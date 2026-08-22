"""Slice 4 contracts: ferocity, defeat mercy, and Fate's bargain."""

from __future__ import annotations

import random
import unittest
from unittest import mock

import rpg
import session
import sites


def hero(name: str, *, quality: bool = False, level: int = 1) -> rpg.Entity:
    return rpg.Entity(
        name=name,
        dex=5,
        str_=5,
        sta=6,
        max_hp=10,
        power=4,
        pain=rpg.HERO_PAIN,
        records_wounds=True,
        weapon=rpg.WEAPONS["schweizersäbel" if quality else "dagger"],
        level=level,
    )


def defeat(e: rpg.Entity, *, dead: bool = False) -> None:
    e.hp = 0
    e.dead = dead
    e.down = not dead


class FerocityCatalog(unittest.TestCase):
    def test_every_catalog_row_has_the_settled_content_band(self):
        relentless = {"skeleton", "ghoul", "wight"}
        beasts = {
            "wolf", "dire wolf", "boar", "bear", "great spider",
            "ogre", "troll", "giant", "wyvern", "drake", "dragon",
        }
        humanoids = set(sites.FOES) - relentless - beasts
        self.assertTrue(humanoids)
        for kind, spec in sites.FOES.items():
            expected = (
                rpg.FEROCITY_RELENTLESS if kind in relentless
                else rpg.FEROCITY_BREAKS if kind in beasts
                else rpg.FEROCITY_TAKES_SPOILS
            )
            self.assertEqual(spec.ferocity, expected, kind)

    def test_make_foe_copies_and_can_override_ferocity(self):
        rng = random.Random(1)
        self.assertEqual(
            sites.make_foe("wolf", 1, rng).ferocity,
            rpg.FEROCITY_BREAKS,
        )
        wave = sites.make_foe(
            "cutthroat", 2, rng, ferocity=rpg.FEROCITY_RELENTLESS)
        self.assertEqual(wave.ferocity, rpg.FEROCITY_RELENTLESS)

    def test_ferocity_tags_fit_the_player_column(self):
        foes = [
            sites.make_foe("cutthroat", 1, random.Random(1)),
            sites.make_foe("wolf", 2, random.Random(2)),
            sites.make_foe("skeleton", 3, random.Random(3)),
        ]
        lines = sites.roster_lines(foes)
        self.assertTrue(all(len(line) <= rpg.PLAYER_WIDTH for line in lines))


class DefeatMercy(unittest.TestCase):
    def test_humanoids_take_purse_and_quality_steel_but_party_survives(self):
        pc = hero("PC", quality=True)
        companion = hero("Companion")
        pc.weapon = rpg.WEAPONS["wooden staff"]
        pc.power += pc.weapon.power_bonus
        pc.cur_power = pc.power
        power_before = pc.power
        party = [pc, companion]
        for h in party:
            defeat(h)
        foes = [sites.make_foe("cutthroat", 1, random.Random(1))]
        purse = rpg.Purse(73)
        wounds_before = list(pc.wounds)

        kind = rpg.apply_defeat_mercy(
            party, foes, purse, random.Random(2), [], participants=party)

        self.assertEqual(kind, "humanoid")
        self.assertEqual(purse.silver, 0)
        self.assertIsNone(pc.weapon)
        self.assertEqual(pc.power, power_before - 1)
        self.assertLessEqual(pc.cur_power, pc.power)
        self.assertEqual(companion.weapon.name, "dagger")
        self.assertTrue(all(h.alive and h.hp == 1 for h in party))
        self.assertEqual(pc.wounds, wounds_before)
        self.assertEqual(pc.mercy_level, pc.level)

    def test_monsters_take_nothing_and_leave_one_permanent_maiming(self):
        pc = hero("PC", quality=True)
        companion = hero("Companion", quality=True)
        party = [pc, companion]
        for h in party:
            defeat(h)
        foes = [sites.make_foe("bear", 1, random.Random(1))]
        purse = rpg.Purse(73)

        kind = rpg.apply_defeat_mercy(
            party, foes, purse, random.Random(4), [], participants=party)

        self.assertEqual(kind, "monster")
        self.assertEqual(purse.silver, 73)
        self.assertTrue(all(h.weapon is not None for h in party))
        self.assertTrue(all(h.alive and h.hp == 1 for h in party))
        permanents = [w for h in party for w in h.wounds if w.permanent]
        self.assertEqual(len(permanents), 1)

    def test_one_mercy_per_level_non_cumulative(self):
        pc, companion = hero("PC"), hero("Companion")
        party = [pc, companion]
        foes = [sites.make_foe("cutthroat", 1, random.Random(1))]
        purse = rpg.Purse()
        for h in party:
            defeat(h)
        self.assertEqual(
            rpg.apply_defeat_mercy(
                party, foes, purse, random.Random(1), [], participants=party),
            "humanoid",
        )

        for h in party:
            defeat(h)
        self.assertIsNone(rpg.apply_defeat_mercy(
            party, foes, purse, random.Random(1), [], participants=party))

        pc.level += 1
        self.assertEqual(
            rpg.apply_defeat_mercy(
                party, foes, purse, random.Random(1), [], participants=party),
            "humanoid",
        )

    def test_relentless_roster_is_a_real_wipe(self):
        pc, companion = hero("PC"), hero("Companion")
        party = [pc, companion]
        for h in party:
            defeat(h)
        foes = [sites.make_foe("skeleton", 1, random.Random(1))]
        self.assertIsNone(rpg.apply_defeat_mercy(
            party, foes, rpg.Purse(), random.Random(1), [],
            participants=party,
        ))
        self.assertTrue(rpg.party_wiped(party, []))

    def test_posse_mercy_spends_the_same_level_allowance(self):
        pc, companion = hero("PC"), hero("Companion")
        party = [pc, companion]
        for h in party:
            defeat(h)
        state = {
            "party": party,
            "purse": rpg.Purse(12),
            "rng": random.Random(1),
            "clock": rpg.Clock(),
            "karma": {"sin": 25},
            "pending": {},
        }
        foes = [sites.make_foe("cutthroat", 1, random.Random(1))]

        self.assertTrue(session.apply_mercy(
            state, foes, "law", [], participants=party))
        self.assertEqual(state["party"], [pc])
        self.assertEqual(state["purse"].silver, 0)
        self.assertEqual(state["karma"]["sin"], 0)
        defeat(pc)
        self.assertFalse(session.apply_mercy(
            state, foes, "law", [], participants=[pc]))


class FateBargain(unittest.TestCase):
    def test_paid_duo_victory_is_a_wounded_solo_victory_not_a_wipe(self):
        pc = hero("PC")
        companion = hero("Companion")
        pc.protagonist = True
        rpg.add_wound(pc, "arm", 2)
        wounds_before = [(w.location, w.severity) for w in pc.wounds]
        pc.cur_sta = 1
        pc.cur_power = 2
        rpg.apply_condition(pc, "poison", power=1, rounds=None)
        conditions_before = list(pc.conditions)
        defeat(pc)
        pc.fate_debt = True
        foe = sites.make_foe("skeleton", 1, random.Random(1))
        defeat(foe, dead=True)

        paid = rpg._settle_fate_debt(
            [pc, companion], [foe], random.Random(2), [])

        self.assertTrue(paid)
        self.assertTrue(pc.alive)
        self.assertEqual(pc.hp, 1)
        self.assertFalse(pc.down)
        self.assertTrue(companion.dead)
        self.assertEqual(
            [(w.location, w.severity) for w in pc.wounds], wounds_before)
        self.assertEqual(pc.cur_sta, 1)
        self.assertEqual(pc.cur_power, 2)
        self.assertEqual(pc.conditions, conditions_before)
        self.assertFalse(rpg.party_wiped([pc, companion], []))
        # A Fate-paid victory is not allowed to spend Slice 4's mercy.
        self.assertIsNone(rpg.apply_defeat_mercy(
            [pc, companion], [foe], rpg.Purse(), random.Random(3), [],
            participants=[pc, companion],
        ))
        self.assertEqual(pc.mercy_level, 0)

        state = {
            "party": [pc, companion],
            "purse": rpg.Purse(),
            "rng": random.Random(4),
            "clock": rpg.Clock(),
            "pending": None,
        }
        with (
            mock.patch("session.apply_mercy") as mercy_path,
            mock.patch("session.award_xp"),
            mock.patch("session.record_karma"),
            mock.patch("session.roll_loot"),
            mock.patch("session.satisfaction_after_fight"),
            mock.patch("session.auto_potions"),
            mock.patch("session.deliver_if_arrived"),
            mock.patch("session.append_tally"),
            mock.patch("session.print_combat"),
            mock.patch("session.save"),
            mock.patch("session.report_game_over"),
        ):
            session.finish_encounter(state, [], [foe], encounter_xp=0)
        mercy_path.assert_not_called()
        self.assertFalse(pc.fate_paid)

    def test_a_lost_fight_pays_the_same_price_and_takes_no_mercy(self):
        # 2026-07-29: losing used to waive the debt outright, which made a
        # loss strictly cheaper than a win at the interrupt. Fate is owed.
        pc = hero("PC")
        companion = hero("Companion")
        pc.protagonist = True
        defeat(pc)
        pc.fate_debt = True
        foe = sites.make_foe("skeleton", 1, random.Random(1))
        self.assertTrue(foe.alive)

        paid = rpg._settle_fate_debt(
            [pc, companion], [foe], random.Random(2), [])

        self.assertTrue(paid)
        self.assertTrue(companion.dead)
        self.assertTrue(pc.alive)
        self.assertEqual(pc.hp, 1)
        self.assertFalse(pc.down)
        self.assertTrue(pc.fate_paid)
        # The 1 HP restoration is what bars the level's defeat mercy: the
        # party is no longer defeated by the time mercy is checked.
        self.assertFalse(rpg.party_defeated([pc, companion]))
        self.assertIsNone(rpg.apply_defeat_mercy(
            [pc, companion], [foe], rpg.Purse(), random.Random(3), [],
            participants=[pc, companion],
        ))
        self.assertEqual(pc.mercy_level, 0)
        # ...and it buys nothing: the foe is still standing, so the room is
        # left uncleared rather than banked.
        self.assertFalse(rpg.party_wiped([pc, companion], []))
        self.assertTrue(foe.alive)

    def test_the_session_tail_of_a_paid_loss_banks_nothing(self):
        pc = hero("PC")
        companion = hero("Companion")
        pc.protagonist = True
        defeat(pc)
        pc.fate_debt = True
        foe = sites.make_foe("skeleton", 1, random.Random(1))
        rpg._settle_fate_debt([pc, companion], [foe], random.Random(2), [])

        state = {
            "party": [pc, companion],
            "purse": rpg.Purse(),
            "rng": random.Random(4),
            "pending": None,
            "rooms": {},
            "clock": rpg.Clock(day=1),
        }
        log: list[str] = []
        with (
            mock.patch("session.award_xp") as award,
            mock.patch("session.record_karma"),
            mock.patch("session.roll_loot") as loot,
            mock.patch("session.satisfaction_after_fight"),
            mock.patch("session.auto_potions"),
            mock.patch("session.deliver_if_arrived"),
            mock.patch("session.collect_weapon_quirks"),
            mock.patch("session.append_tally"),
            mock.patch("session.print_combat"),
            mock.patch("session.save"),
            mock.patch("session.report_game_over") as game_over,
        ):
            session.finish_encounter(
                state, log, [foe], encounter_xp=100,
                site="the ritual ground", room=1)

        # No wipe, no game over, and no pay for a fight that was lost.
        # (report_game_over runs on every tail; it no-ops unless the party
        # was wiped or the PC is dead, so assert on what it was told.)
        game_over.assert_called_once()
        self.assertFalse(game_over.call_args.args[1])   # wiped
        self.assertTrue(pc.alive)
        award.assert_not_called()
        loot.assert_not_called()
        self.assertEqual(pc.mercy_level, 0)
        self.assertEqual(state["purse"].silver, 0)
        # The room remembers its survivor, as after any staggered-apart fight.
        self.assertIn(("the ritual ground", 1), state["rooms"])
        self.assertTrue(
            any("not cleared" in line for line in log), log)
        self.assertFalse(pc.fate_paid)   # the transient marker is consumed

    def test_a_clean_retreat_pays_the_debt_too(self):
        # 2026-07-29: running does not buy the protagonist's life back.
        # There is no exit from the bargain, only a choice of what it buys.
        pc = hero("PC")
        companion = hero("Companion")
        pc.protagonist = True
        defeat(pc)
        pc.fate_debt = True
        foe = sites.make_foe("skeleton", 1, random.Random(1))

        with (
            mock.patch("rpg._attack", return_value=False),
            mock.patch("rpg._chase_contest", return_value=True),
        ):
            escaped = rpg.attempt_retreat(
                [pc, companion], [foe], random.Random(2), [])

        self.assertTrue(escaped)
        self.assertFalse(pc.fate_debt)
        self.assertTrue(companion.dead)
        self.assertTrue(pc.alive)
        self.assertEqual(pc.hp, 1)
        self.assertTrue(pc.fate_paid)

    def test_a_blink_out_pays_the_debt_too(self):
        # The Power buys the party out of the room, not out of the bargain.
        pc = hero("PC")
        companion = hero("Companion")
        pc.protagonist = True
        pc.school = "fire"
        pc.spells = {"teleport": 2}
        pc.cur_power = 99
        defeat(pc)
        pc.fate_debt = True
        foe = sites.make_foe("skeleton", 1, random.Random(1))

        with mock.patch("rpg.casting_check", return_value="success"):
            gone = rpg.blink_escape(
                [pc, companion], [foe], pc, random.Random(2), [])

        self.assertTrue(gone)
        self.assertTrue(companion.dead)
        self.assertTrue(pc.alive)
        self.assertEqual(pc.hp, 1)

    def test_a_failed_break_defers_the_debt_to_the_real_end(self):
        # The fight is not over, so nothing is collected at the door.
        # A pursuing roster is required for the chase to roll at all --
        # the barrow's undead never chase, so fleeing them always works.
        pc = hero("PC")
        companion = hero("Companion")
        pc.protagonist = True
        defeat(pc)
        pc.fate_debt = True
        foe = sites.make_foe("cutthroat", 1, random.Random(1))
        self.assertTrue(foe.pursues)

        with (
            mock.patch("rpg._attack", return_value=False),
            mock.patch("rpg._chase_contest", return_value=False),
        ):
            escaped = rpg.attempt_retreat(
                [pc, companion], [foe], random.Random(2), [])

        self.assertFalse(escaped)
        self.assertTrue(pc.fate_debt)      # still owed
        self.assertFalse(companion.dead)
        self.assertFalse(pc.fate_paid)

    def test_depleted_party_restores_pc_after_killing_last_companion(self):
        pc = hero("PC")
        already_dead = hero("Already Dead")
        last_standing = hero("Last Standing")
        pc.protagonist = True
        defeat(pc)
        pc.fate_debt = True
        defeat(already_dead, dead=True)
        foe = sites.make_foe("skeleton", 1, random.Random(1))
        defeat(foe, dead=True)

        rpg._settle_fate_debt(
            [pc, already_dead, last_standing], [foe],
            random.Random(2), [])

        self.assertTrue(already_dead.dead)
        self.assertTrue(last_standing.dead)
        self.assertTrue(pc.alive)
        self.assertEqual(pc.hp, 1)
        self.assertFalse(rpg.party_wiped(
            [pc, already_dead, last_standing], []))

    def test_fate_interrupt_consumes_the_ordinary_pause(self):
        pc = hero("PC")
        companion = hero("Companion")
        pc.protagonist = True
        foe = rpg.Entity(
            name="Executioner",
            dex=5,
            str_=5,
            sta=8,
            max_hp=10,
            sweep=2,
            ferocity=rpg.FEROCITY_RELENTLESS,
        )
        fired: set[tuple[str, rpg.Entity]] = set()

        def first_round(attacker, defender, *_args, **_kwargs):
            if attacker is foe and defender is pc:
                defender.hp = 0
                defender.dead = True
                defender.down = False
            elif attacker is foe and defender is companion:
                defender.hp = 4
            return True

        with mock.patch("rpg._attack", side_effect=first_round):
            pause = rpg.group_combat(
                [pc, companion], [foe], random.Random(5), [],
                max_rounds=2, pause_triggers=True, fired=fired,
                standing_orders=lambda *_: "pause",
            )

        self.assertIsNotNone(pause)
        self.assertEqual(pause.kind, "fate")
        self.assertIn(("pause-spent", pc), fired)

        # The companion crossed half HP in the same round, but Fate spent the
        # encounter's one pause. Even a caller asking to pause again is
        # forced through standing orders.
        with mock.patch("rpg._attack", return_value=True):
            second = rpg.group_combat(
                [pc, companion], [foe], random.Random(6), [],
                max_rounds=pause.round + 1,
                pause_triggers=True,
                fired=fired,
                first_round=pause.round + 1,
                standing_orders=lambda *_: "pause",
            )
        self.assertIsNone(second)

    def test_an_ordinary_pause_already_spent_suppresses_the_fate_interrupt(self):
        pc = hero("PC")
        companion = hero("Companion")
        pc.protagonist = True
        foe = rpg.Entity(
            name="Executioner",
            dex=5,
            str_=5,
            sta=8,
            max_hp=10,
            ferocity=rpg.FEROCITY_RELENTLESS,
        )
        fired: set[tuple[str, rpg.Entity]] = set()

        def wound_companion(attacker, defender, *_args, **_kwargs):
            if attacker is foe and defender is companion:
                defender.hp = 4
            return True

        with mock.patch("rpg._attack", side_effect=wound_companion):
            pause = rpg.group_combat(
                [pc, companion], [foe], random.Random(7), [],
                max_rounds=1, pause_triggers=True, fired=fired,
                standing_orders=lambda *_: "pause",
            )

        self.assertIsNotNone(pause)
        self.assertEqual(pause.kind, "normal")
        self.assertTrue(any(kind == "pause-spent" for kind, _ in fired))

        # Fate intervenes later in the same encounter. The already-spent
        # ordinary pause prevents a second interrupt.
        defeat(pc)
        pc.fate_debt = True
        with mock.patch("rpg._attack", return_value=True):
            second = rpg.group_combat(
                [pc, companion], [foe], random.Random(8), [],
                max_rounds=pause.round + 1,
                pause_triggers=True,
                fired=fired,
                first_round=pause.round + 1,
                standing_orders=lambda *_: "pause",
            )
        self.assertIsNone(second)
        self.assertNotIn(("fate", pc), fired)


class FoeBreak(unittest.TestCase):
    """The ROUT. Its trigger band and chase math were rebalanced on
    2026-08-08 and are pinned in test_turnin.py (RoutTrigger,
    RoutChaseMath); what stays here is what the break itself does to the
    encounter -- the withdrew marker, the ferocity gate, the one attempt."""

    def test_a_badly_beaten_beast_can_escape_in_reverse(self):
        h = hero("Hunter")
        foe = sites.make_foe("wolf", 1, random.Random(1))
        foe.hp = 1
        with (
            mock.patch("rpg._attack", return_value=True),
            mock.patch("rpg._chase_contest", return_value=True),
        ):
            rpg.group_combat([h], [foe], random.Random(2), [],
                             max_rounds=1)
        self.assertTrue(foe.withdrew)
        self.assertFalse(foe.alive)
        self.assertFalse(foe.dead)
        self.assertIsNone(rpg.fallen_weapons_line([foe]))

    def test_relentless_foes_never_break(self):
        h = hero("Hunter")
        foe = sites.make_foe("skeleton", 1, random.Random(1))
        foe.hp = 1
        with mock.patch("rpg._attack", return_value=True):
            rpg.group_combat([h], [foe], random.Random(2), [],
                             max_rounds=1)
        self.assertFalse(foe.withdrew)
        self.assertTrue(foe.alive)

    def test_a_run_down_line_never_gets_a_second_try(self):
        # break_tried is stamped on the whole standing line at the attempt,
        # so a caught roster fights it out (one attempt per fight).
        h = hero("Hunter")
        foe = sites.make_foe("bear", 1, random.Random(1))
        foe.hp = 1
        with (
            mock.patch("rpg._attack", return_value=False),
            mock.patch("rpg._chase_contest", return_value=False) as chase,
        ):
            rpg.group_combat([h], [foe], random.Random(2), [],
                             max_rounds=4)
        self.assertEqual(chase.call_count, 1)
        self.assertFalse(foe.withdrew)
        # ...and the marker is per-fight: it clears with the rest of the
        # fight states, so the next encounter starts with its own attempt.
        self.assertFalse(foe.break_tried)

    def test_a_rout_is_rolled_without_the_runners_head_start(self):
        # The party's deliberate retreat keeps FLEE_BONUS; a collapse under
        # pursuit picks nothing (2026-08-08). Full math: test_turnin.py.
        h = hero("Hunter")
        foe = sites.make_foe("bear", 1, random.Random(1))
        foe.hp = 1
        with (
            mock.patch("rpg._attack", return_value=False),
            mock.patch("rpg._chase_contest", return_value=True) as chase,
        ):
            rpg.group_combat([h], [foe], random.Random(2), [],
                             max_rounds=1)
        self.assertTrue(chase.call_args.kwargs.get("routed"))


class SaveRoundTrip(unittest.TestCase):
    def test_new_fields_survive_the_round_trip(self):
        e = hero("PC", level=4)
        e.mercy_level = 3
        e.ferocity = rpg.FEROCITY_RELENTLESS
        e.break_tried = True
        e.fate_paid = True
        doc = session._entity_to_dict(e)
        loaded = session._entity_from_dict(doc)
        self.assertEqual(loaded.mercy_level, 3)
        self.assertEqual(loaded.ferocity, rpg.FEROCITY_RELENTLESS)
        self.assertTrue(loaded.break_tried)
        self.assertTrue(loaded.fate_paid)


if __name__ == "__main__":
    unittest.main()
