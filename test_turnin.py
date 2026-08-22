"""THE TURN-IN, THE ROUT & THE HUNT contract suite (2026-08-08).

What is pinned here, in the cluster's build order:

  A. **The rout** -- its own stricter trigger (`rout_ready`, a THIRD, while
     `fight_winding_down` stays at half for potion thrift), no FLEE_BONUS
     for a collapsing foe line, and the runners' chase DEX weighted by HP
     as well as STA (floored, so a graze-rich pack is not free meat).
  B. **The loose-ends record** -- what a rout writes on the save, and the
     `driven off, not slain` tag on the banner of the field it cleared.
  C. **`pursue`** -- the warm-trail gate (same day, same area, one attempt),
     the tracking contest, and both outcomes.
  D. **Proof of the kill** -- the authored flag, its gate on the FINAL
     site's roster being dead, and the gate lifting when it finally is.
  E. **The turn-in stage** -- the three-way XP split, `taken -> work_done
     -> turned_in | lost`, banding by the TURN-IN day, the return leg
     inside the window, lost-after-done keeping the banked 80% and firing
     no failure rumor, and the exemption set (deliveries, conquest,
     hell, dark).

    python -m unittest -v test_turnin.py
"""

from __future__ import annotations

import io
import random
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest import mock

import karma
import crime
import places
import quests
import rpg
import session
import sites


# --------------------------------------------------------------------------- #
# Harness
# --------------------------------------------------------------------------- #

def hero(name: str, *, level: int = 3, mind: int = 5) -> rpg.Entity:
    return rpg.Entity(
        name=name,
        dex=5,
        str_=5,
        sta=6,
        mind=mind,
        max_hp=12,
        power=4,
        pain=rpg.HERO_PAIN,
        records_wounds=True,
        weapon=rpg.WEAPONS["katana"],
        level=level,
    )


def foe(kind: str = "wolf", n: int = 1, *, hp: int | None = None):
    f = sites.make_foe(kind, n, random.Random(n))
    if hp is not None:
        f.hp = hp
    return f


def _world():
    """One generated world, shared by the lifecycle tests that only read
    its geography. Cheap enough to build per test class, not per test."""
    return quests.generate_world(seed=27)


def _state(world: dict, *, day: int = 5, party=None, at=None) -> dict:
    """A session state standing somewhere real, with the ledgers a quest
    path touches. `at` is the area dict the party stands in (default: the
    world's first settlement)."""
    here = at or quests.settlements(world)[0]
    party = party if party is not None else [hero("PC"), hero("Ally")]
    party[0].protagonist = True
    return {
        "world": world,
        "party": party,
        "clock": rpg.Clock(day=day),
        "purse": rpg.Purse(gold=0),
        "rng": random.Random(4),
        "karma": karma.new_karma(),
        "crimes": crime.new_crimes(),
        "history": [],
        "position": session._area_position(here),
        "accepted": [],
        "active_quest": None,
        "loose_ends": [],
        "foe_count": 0,
        "pending": None,
        "rooms": {},
        "site_clears": {},
        "holdings": {},
        "pact": None,
        "services": {},
        "visited": [here["key"]],
    }


def _quest_in(world: dict, state: dict, **fields) -> dict:
    """A board-shaped quest whose single site stands in the party's area,
    its cursor parked on the LAST site's last room -- the position
    `advance_quest` fires work-done from."""
    here = world["areas"][state["position"]["area"]]
    qid = quests.next_quest_id(world)
    site_id = f"site/test/{qid}"
    quests.new_site(world, here["key"], site_id, "the test tunnel", 3,
                    quest=qid, template="mine", domain="mixed")
    quests.new_room(world, site_id, f"{site_id}/room-1", "the deep end",
                    ["wolf"], quest=qid)
    quest = {
        "id": qid, "name": "A Test Job", "desc": "test work",
        "origin": here["key"], "level": 3, "skins": {},
        "sites": [site_id], "site_count": 1, "encounters": 1,
        "xp_total": rpg.quest_xp_total(3, 1),
        "gold_total": rpg.quest_gold(3, 1),
        "next": {"site": 0, "room": 0},
        "status": "open", "align": "good",
        "epilogue": "The tunnel is clear.",
        "giver": {"name": "Kristryd", "role": "the guild agent",
                  "homeland": "tergal", "sex": "f", "age": 35},
    }
    quest.update(fields)
    quests.stamp_quest_clock(quest, state["clock"].day - 1, state["rng"])
    world["quests"][qid] = quest
    here["quests"].append(qid)
    state["active_quest"] = qid
    state["accepted"].append(qid)
    return quest


def _run(fn, state, **args):
    """Call a session command against an in-memory state (load/save stubbed)
    and return everything it printed."""
    out = io.StringIO()
    with (
        mock.patch("session.load", return_value=state),
        mock.patch("session.save"),
        redirect_stdout(out),
    ):
        fn(SimpleNamespace(**args))
    return out.getvalue()


# --------------------------------------------------------------------------- #
# A. The rout
# --------------------------------------------------------------------------- #

class RoutTrigger(unittest.TestCase):
    def test_the_rout_wants_a_third_where_winding_down_wants_a_half(self):
        # The two predicates are deliberately different bands: winding-down
        # also gates potion thrift and must not move.
        f = foe("bear")
        f.hp = int(f.max_hp * 0.45)
        self.assertTrue(rpg.fight_winding_down([f]))
        self.assertFalse(rpg.rout_ready([f]))
        f.hp = int(f.max_hp * 0.30)
        self.assertTrue(rpg.rout_ready([f]))

    def test_a_spent_foe_is_rout_ready_at_any_hp(self):
        f = foe("bear")
        f.hp = f.max_hp
        f.cur_sta = 0
        self.assertTrue(f.spent)
        self.assertTrue(rpg.rout_ready([f]))

    def test_one_healthy_body_holds_the_whole_line(self):
        hurt, fresh = foe("wolf", 1, hp=1), foe("wolf", 2)
        self.assertFalse(rpg.rout_ready([hurt, fresh]))

    def test_the_dead_do_not_vote(self):
        hurt, dead = foe("wolf", 1, hp=1), foe("wolf", 2, hp=0)
        dead.dead = True
        self.assertTrue(rpg.rout_ready([hurt, dead]))

    def test_group_combat_breaks_a_line_at_a_third_not_at_a_half(self):
        # A big pool, so the two bands are genuinely separate integers --
        # this IS the case the rebalance was for (the troll hovering under
        # the half band for rounds).
        h = hero("Hunter")
        half = foe("bear")
        half.hp = int(half.max_hp * 0.45)
        with (
            mock.patch("rpg._attack", return_value=False),
            mock.patch("rpg._chase_contest", return_value=True),
        ):
            rpg.group_combat([h], [half], random.Random(2), [], max_rounds=1)
        self.assertFalse(half.withdrew)      # above the rout band: it stays

        third = foe("bear", 2)
        third.hp = max(1, int(third.max_hp * 0.30))
        with (
            mock.patch("rpg._attack", return_value=False),
            mock.patch("rpg._chase_contest", return_value=True),
        ):
            rpg.group_combat([h], [third], random.Random(2), [], max_rounds=1)
        self.assertTrue(third.withdrew)


class RoutChaseMath(unittest.TestCase):
    def test_a_rout_gets_no_head_start_and_a_retreat_keeps_its_bonus(self):
        runner, chaser = foe("wolf", 1), hero("Chaser")
        rolls = iter([3, 3, 3, 3] * 2)   # both sides roll 6
        with mock.patch("random.Random.randint",
                        side_effect=lambda *_: next(rolls)):
            rng = random.Random(1)
            routed = rpg._chase_contest([runner], [chaser], rng, [],
                                        routed=True)
            deliberate = rpg._chase_contest([runner], [chaser], rng, [])
        # Same dice, same bodies: the only difference is FLEE_BONUS and the
        # HP weighting, and it decides the contest.
        self.assertFalse(routed)
        self.assertTrue(deliberate)

    def test_a_routed_runners_dex_is_weighted_by_hp(self):
        whole, broken = foe("bear", 1), foe("bear", 2)
        broken.hp = max(1, broken.max_hp // 4)
        self.assertGreater(rpg._chase_dex([whole], hp_weighted=True),
                           rpg._chase_dex([broken], hp_weighted=True))

    def test_the_hp_weight_has_a_floor(self):
        f = foe("bear")
        f.hp = 1
        floored = rpg._chase_dex([f], hp_weighted=True)
        self.assertAlmostEqual(floored,
                               rpg._chase_dex([f]) * rpg.CHASE_HP_WEIGHT_FLOOR,
                               places=6)

    def test_the_partys_own_retreat_never_pays_the_rout_handicap(self):
        # attempt_retreat is the deliberate break: it picked the moment.
        pc, f = hero("PC"), foe("cutthroat")
        pc.hp = 1
        seen = {}

        def spy(runners, pursuers, rng, log, routed=False):
            seen["routed"] = routed
            return True

        with (
            mock.patch("rpg._attack", return_value=False),
            mock.patch("rpg._chase_contest", side_effect=spy),
        ):
            rpg.attempt_retreat([pc], [f], random.Random(2), [])
        self.assertFalse(seen["routed"])

    def test_a_breaking_foe_line_is_rolled_as_a_rout(self):
        pc, f = hero("PC"), foe("wolf", hp=1)
        seen = {}

        def spy(runners, pursuers, rng, log, routed=False):
            seen["routed"] = routed
            return True

        with (
            mock.patch("rpg._attack", return_value=False),
            mock.patch("rpg._chase_contest", side_effect=spy),
        ):
            rpg.attempt_foe_retreat([f], [pc], random.Random(2), [])
        self.assertTrue(seen["routed"])


# --------------------------------------------------------------------------- #
# B. The loose-ends record
# --------------------------------------------------------------------------- #

class LooseEnds(unittest.TestCase):
    def setUp(self):
        self.world = _world()
        self.state = _state(self.world, day=6)

    def test_a_rout_writes_who_got_away_and_from_where(self):
        runner = foe("troll")
        runner.hp, runner.withdrew = 4, True
        log: list[str] = []
        rec = session.record_loose_end(self.state, [runner], log)

        self.assertEqual(rec["day"], 6)
        self.assertEqual(rec["area"], self.state["position"]["area"])
        self.assertEqual(len(rec["foes"]), 1)
        saved = rec["foes"][0]
        self.assertEqual(saved["name"], runner.name)
        self.assertEqual(saved["hp"], 4)
        self.assertEqual(saved["level"], runner.level)
        self.assertIs(self.state["loose_ends"][0], rec)
        self.assertTrue(any(rec["id"] in line for line in log))

    def test_records_stack_newest_first(self):
        first = session.record_loose_end(self.state, [foe("wolf", 1)], [])
        second = session.record_loose_end(self.state, [foe("wolf", 2)], [])
        self.assertEqual([r["id"] for r in self.state["loose_ends"]],
                         [second["id"], first["id"]])

    def test_ids_are_unique_across_separate_processes(self):
        # Every command is its own process reading the save back, so the id
        # can only come from the LIST -- a counter in state would reset to
        # zero on the next command and stamp every rout `le1`.
        session.record_loose_end(self.state, [foe("wolf", 1)], [])
        reloaded = _state(self.world, day=self.state["clock"].day)
        reloaded["loose_ends"] = list(self.state["loose_ends"])
        session.record_loose_end(reloaded, [foe("wolf", 2)], [])
        ids = [r["id"] for r in reloaded["loose_ends"]]
        self.assertEqual(len(set(ids)), 2, ids)

    def test_pruning_the_list_never_reissues_a_live_id(self):
        # The record has no expiry: the DM prunes it by save edit, and the
        # next rout must not collide with what is left.
        session.record_loose_end(self.state, [foe("wolf", 1)], [])
        second = session.record_loose_end(self.state, [foe("wolf", 2)], [])
        self.state["loose_ends"] = [second]      # the DM drops the older
        third = session.record_loose_end(self.state, [foe("wolf", 3)], [])
        self.assertNotEqual(third["id"], second["id"])

    def test_a_quest_rout_names_the_job_and_the_place(self):
        quest = _quest_in(self.world, self.state)
        rec = session.record_loose_end(
            self.state, [foe("wolf")], [],
            quest_id=quest["id"], site_key=quest["sites"][0], room=1)
        self.assertIn(quest["name"], rec["where"])
        self.assertIn("the test tunnel", rec["where"])
        self.assertEqual(rec["quest"], quest["id"])

    def test_an_off_script_rout_names_the_open_ground(self):
        rec = session.record_loose_end(self.state, [foe("wolf")], [])
        area = session.current_area(self.state)
        self.assertIn(area["name"], rec["where"])

    def test_a_cleared_field_carries_the_driven_off_tag(self):
        quest = _quest_in(self.world, self.state)
        runner = foe("wolf")
        runner.hp, runner.withdrew = 1, True
        log: list[str] = []
        with mock.patch("session.award_xp"), mock.patch("session.roll_loot"), \
                mock.patch("session.satisfaction_after_fight"), \
                mock.patch("session.auto_potions"), \
                mock.patch("session.append_tally"), \
                mock.patch("session.print_combat"), \
                mock.patch("session.save"), \
                mock.patch("session.report_game_over"):
            session.finish_encounter(
                self.state, log, [runner], 10,
                site=quest["sites"][0], room=1, quest=quest["id"])
        self.assertTrue(self.world["sites"][quest["sites"][0]]["routed"])
        self.assertTrue(any("driven off, not slain" in line for line in log),
                        log)

    def test_the_record_survives_the_save_round_trip(self):
        runner = foe("troll")
        runner.hp = 5
        session.record_loose_end(self.state, [runner], [])
        doc = session._entity_from_dict(
            self.state["loose_ends"][0]["foes"][0])
        self.assertEqual(doc.hp, 5)
        self.assertEqual(doc.name, runner.name)


class TheWarmTrail(unittest.TestCase):
    def setUp(self):
        self.world = _world()
        self.state = _state(self.world, day=6)
        runner = foe("troll")
        runner.hp = 5
        self.rec = session.record_loose_end(self.state, [runner], [])

    def test_same_day_same_area_is_warm(self):
        self.assertTrue(session.trail_warm(self.state, self.rec))

    def test_a_night_slept_cools_it(self):
        self.state["clock"].day += 1
        self.assertFalse(session.trail_warm(self.state, self.rec))

    def test_leaving_the_area_cools_it(self):
        other = [a for a in quests.all_areas(self.world)
                 if a["key"] != self.rec["area"]][0]
        self.state["position"] = session._area_position(other)
        self.assertFalse(session.trail_warm(self.state, self.rec))


# --------------------------------------------------------------------------- #
# C. pursue
# --------------------------------------------------------------------------- #

class Pursue(unittest.TestCase):
    def setUp(self):
        self.world = _world()
        self.state = _state(self.world, day=6)
        runner = foe("troll")
        runner.hp = 5
        self.rec = session.record_loose_end(self.state, [runner], [])

    def test_a_cold_trail_is_refused_and_costs_nothing(self):
        self.state["clock"].day += 1
        with mock.patch("session.resolve_encounter") as fight:
            out = _run(session.cmd_pursue, self.state, id=None, stage=False)
        fight.assert_not_called()
        self.assertIn("cold", out)
        self.assertFalse(self.rec["pursue_tried"])

    def test_one_attempt_per_rout(self):
        self.rec["pursue_tried"] = True
        with mock.patch("session.resolve_encounter") as fight:
            out = _run(session.cmd_pursue, self.state, id=None, stage=False)
        fight.assert_not_called()
        self.assertIn("one attempt per rout", out)

    def test_a_lost_trail_spends_no_day_and_keeps_the_record(self):
        day = self.state["clock"].day
        with (
            mock.patch("session.track_contest", return_value=False),
            mock.patch("session.resolve_encounter") as fight,
        ):
            out = _run(session.cmd_pursue, self.state, id=None, stage=False)
        fight.assert_not_called()
        self.assertIn("trail is lost", out)
        self.assertEqual(self.state["clock"].day, day)
        self.assertTrue(self.rec["pursue_tried"])
        self.assertIsNone(self.rec["resolved_day"])

    def test_a_won_trail_reopens_the_fight_at_the_fled_state(self):
        with (
            mock.patch("session.track_contest", return_value=True),
            mock.patch("session.resolve_encounter") as fight,
        ):
            _run(session.cmd_pursue, self.state, id=None, stage=False)
        fight.assert_called_once()
        foes = fight.call_args.args[2]
        self.assertEqual(len(foes), 1)
        self.assertEqual(foes[0].hp, 5)          # no refresh: they ran hurt
        self.assertFalse(foes[0].withdrew)       # back in a fight
        self.assertEqual(fight.call_args.kwargs["pursuit"], self.rec["id"])

    def test_the_mop_up_pays_wild_rates(self):
        with (
            mock.patch("session.track_contest", return_value=True),
            mock.patch("session.resolve_encounter") as fight,
        ):
            _run(session.cmd_pursue, self.state, id=None, stage=False)
        level = max(f["level"] for f in self.rec["foes"])
        self.assertEqual(fight.call_args.args[3],
                         quests.wild_encounter_xp(level))

    def test_the_party_meets_them_at_its_own_range(self):
        with (
            mock.patch("session.track_contest", return_value=True),
            mock.patch("session.resolve_encounter") as fight,
        ):
            _run(session.cmd_pursue, self.state, id=None, stage=False)
        self.assertEqual(
            fight.call_args.kwargs["field"],
            session.party_preferred_field(self.state["party"]))

    def test_the_contest_reads_mind_against_hp_weighted_dex(self):
        party = [hero("Tracker", mind=6)]
        runner = foe("wolf")
        runner.hp = 1
        rolls = iter([3, 3, 3, 3])
        with mock.patch("random.Random.randint",
                        side_effect=lambda *_: next(rolls)):
            caught = rpg.track_contest(party, [runner], random.Random(1), [])
        # 6 + MIND 6 = 12 against 6 + a floored wolf DEX: the trail holds.
        self.assertTrue(caught)

    def test_blood_on_the_ground_helps_the_trackers(self):
        runner = foe("wolf")
        runner.wounds = [rpg.Wound(location="flank", name="a torn flank",
                                   severity=2)]
        log: list[str] = []
        with mock.patch("random.Random.randint", return_value=1):
            rpg.track_contest([hero("T")], [runner], random.Random(1), log)
        self.assertTrue(any("blood on the ground" in line for line in log),
                        log)

    def test_a_won_pursuit_settles_the_record(self):
        dead = foe("troll")
        dead.hp, dead.dead = 0, True
        log: list[str] = []
        session._resolve_pursuit(self.state, log, self.rec["id"], [dead])
        self.assertEqual(self.rec["resolved_day"], self.state["clock"].day)

    def test_a_second_rout_re_arms_the_record_instead(self):
        again = foe("troll")
        again.hp, again.withdrew = 3, True
        self.rec["pursue_tried"] = True
        self.state["clock"].day += 2
        log: list[str] = []
        session._resolve_pursuit(self.state, log, self.rec["id"], [again])
        self.assertIsNone(self.rec["resolved_day"])
        self.assertFalse(self.rec["pursue_tried"])   # a new rout, a new trail
        self.assertEqual(self.rec["day"], self.state["clock"].day)
        self.assertEqual(self.rec["foes"][0]["hp"], 3)

    def test_the_staged_re_encounter_skips_the_gate_and_heals_the_runners(self):
        self.state["clock"].day += 4
        self.rec["pursue_tried"] = True
        with (
            mock.patch("session.track_contest") as roll,
            mock.patch("session.resolve_encounter") as fight,
        ):
            _run(session.cmd_pursue, self.state, id=self.rec["id"],
                 stage=True)
        roll.assert_not_called()
        fight.assert_called_once()
        healed = fight.call_args.args[2][0]
        self.assertEqual(healed.hp, healed.max_hp)   # a troll knits whole


# --------------------------------------------------------------------------- #
# D. Proof of the kill
# --------------------------------------------------------------------------- #

class ProofTemplates(unittest.TestCase):
    def test_a_modest_fraction_of_kill_work_wants_proof(self):
        tables = [t for ts in quests.TEMPLATES.values() for t in ts]
        tables += quests.EPIC_TEMPLATES
        flagged = [t for t in tables if t.get("proof")]
        share = len(flagged) / len(tables)
        self.assertGreater(share, 0.15)
        self.assertLess(share, 0.5)

    def test_the_token_is_a_concrete_thing_the_giver_can_be_handed(self):
        for ts in list(quests.TEMPLATES.values()) + [quests.EPIC_TEMPLATES]:
            for t in ts:
                if t.get("proof"):
                    self.assertIsInstance(t["proof"], str)
                    self.assertTrue(t["proof"].strip())
                    self.assertEqual(t["proof"], t["proof"].lower())

    def test_a_flagged_template_builds_a_flagged_quest(self):
        world = _world()
        tpl = next(t for ts in quests.TEMPLATES.values() for t in ts
                   if t.get("proof"))
        settlement = quests.settlements(world)[0]
        quest = quests.build_quest(world, "qX", tpl, settlement["key"], 3,
                                   random.Random(2))
        self.assertEqual(quest["proof"], tpl["proof"])

    def test_the_board_row_and_the_detail_view_both_say_so(self):
        world = _world()
        quest = next(q for q in world["quests"].values() if q.get("proof"))
        self.assertIn(quest["proof"], quests.quest_line(quest))
        detail = quests.quest_detail_lines(world, quest)
        self.assertTrue(any("proof wanted" in line for line in detail))

    def test_forge_can_flag_one_and_defaults_the_token(self):
        world = _world()
        state = _state(world)
        out = _run(session.cmd_forge, state, level=2, places=1, encounters=1,
                   kinds="wolf", name="A Bounty", area=None, dark=False,
                   days=0, proof="the wolf's head")
        forged = next(q for q in world["quests"].values()
                      if q["name"] == "A Bounty")
        self.assertEqual(forged["proof"], "the wolf's head")
        self.assertIn("proof", out)


class TheProofGate(unittest.TestCase):
    def setUp(self):
        self.world = _world()
        self.state = _state(self.world, day=6)
        self.quest = _quest_in(self.world, self.state,
                               proof="the troll's ears")

    def _clear_the_last_room(self, escaped=None):
        """Walk the quest's only room to done, optionally by rout."""
        log: list[str] = []
        if escaped is not None:
            session.record_loose_end(
                self.state, escaped, log, quest_id=self.quest["id"],
                site_key=self.quest["sites"][0], room=1)
        session.advance_quest(self.state, log, self.quest["id"])
        return log

    def test_a_rout_at_the_final_site_holds_the_job_open(self):
        runner = foe("troll")
        runner.hp, runner.withdrew = 6, True
        log = self._clear_the_last_room([runner])

        self.assertEqual(self.quest["status"], "open")
        self.assertTrue(self.quest["proof_pending"])
        self.assertTrue(any("THE TARGET ESCAPED" in line for line in log),
                        log)
        self.assertIn("proof wanted", quests.quest_line(self.quest))

    def test_the_field_still_cleared_and_paid_for_that_fight(self):
        # The escape clears the field and pays the encounter share: forcing
        # the escape IS winning the fight. Only the JOB waits.
        runner = foe("troll")
        runner.hp, runner.withdrew = 6, True
        self._clear_the_last_room([runner])
        self.assertEqual(self.quest["next"]["room"], 1)   # the room is done

    def test_room_says_so_instead_of_indexing_past_the_last_room(self):
        # The cursor stands past the final room (they are all fought), so
        # every reader has to know the state -- `room` used to crash here.
        runner = foe("troll")
        runner.hp, runner.withdrew = 6, True
        self._clear_the_last_room([runner])
        out = _run(session.cmd_room, self.state, **{})
        self.assertIn(self.quest["proof"], out)
        self.assertIn("pursue", out)

    def test_the_readouts_never_print_a_room_past_the_last(self):
        runner = foe("troll")
        runner.hp, runner.withdrew = 6, True
        self._clear_the_last_room([runner])
        status = _run(session.cmd_status, self.state, **{})
        sheet = "\n".join(session.party_sheet_lines(self.state))
        tally = "\n".join(session.tally_lines(self.state))
        for text in (status, sheet, tally):
            self.assertNotIn("room 2/1", text)
        self.assertIn("ESCAPED", status)
        self.assertIn("ESCAPED", sheet)
        self.assertIn("got away", tally)

    def test_killing_the_target_later_lifts_the_gate(self):
        runner = foe("troll")
        runner.hp, runner.withdrew = 6, True
        self._clear_the_last_room([runner])
        rec = self.state["loose_ends"][0]

        dead = foe("troll")
        dead.hp, dead.dead = 0, True
        log: list[str] = []
        session._resolve_pursuit(self.state, log, rec["id"], [dead])

        self.assertNotIn("proof_pending", self.quest)
        self.assertEqual(self.quest["status"], "work_done")
        self.assertTrue(any("PROOF TAKEN" in line for line in log), log)

    def test_turnin_is_refused_while_the_proof_is_wanted(self):
        runner = foe("troll")
        runner.hp, runner.withdrew = 6, True
        self._clear_the_last_room([runner])
        out = _run(session.cmd_turnin, self.state, quest=self.quest["id"],
                   here=False)
        self.assertIn("proof wanted", out)
        self.assertEqual(self.state["purse"].gold, 0)

    def test_a_clean_kill_never_trips_the_gate(self):
        self._clear_the_last_room()
        self.assertEqual(self.quest["status"], "work_done")
        self.assertNotIn("proof_pending", self.quest)

    def test_an_unflagged_job_is_driven_off_completable(self):
        # This matters: after the rebalance escapes correlate with a
        # battered party, and the relief-escape is only a relief if it
        # still pays.
        plain = _quest_in(self.world, self.state)
        runner = foe("wolf")
        runner.hp, runner.withdrew = 1, True
        log: list[str] = []
        session.record_loose_end(self.state, [runner], log,
                                 quest_id=plain["id"],
                                 site_key=plain["sites"][0], room=1)
        session.advance_quest(self.state, log, plain["id"])
        self.assertEqual(plain["status"], "work_done")

    def test_a_mook_site_escape_is_exempt(self):
        # Only the FINAL site's roster is the target; an earlier place's
        # runners never hold the job open.
        here = self.world["areas"][self.state["position"]["area"]]
        second = f"site/test/{self.quest['id']}-2"
        quests.new_site(self.world, here["key"], second, "the deeper hall", 3,
                        quest=self.quest["id"], template="mine",
                        domain="mixed")
        quests.new_room(self.world, second, f"{second}/room-1", "the hall",
                        ["wolf"], quest=self.quest["id"])
        self.quest["sites"].append(second)
        self.quest["site_count"] = 2

        runner = foe("wolf")
        runner.hp, runner.withdrew = 1, True
        log: list[str] = []
        session.record_loose_end(self.state, [runner], log,
                                 quest_id=self.quest["id"],
                                 site_key=self.quest["sites"][0], room=1)
        session.advance_quest(self.state, log, self.quest["id"])
        # The first site closed and the job moved on -- no gate.
        self.assertEqual(self.quest["status"], "open")
        self.assertNotIn("proof_pending", self.quest)
        self.assertEqual(self.quest["next"]["site"], 1)


# --------------------------------------------------------------------------- #
# E. The split, the stages, the clock
# --------------------------------------------------------------------------- #

class TheThreeWaySplit(unittest.TestCase):
    def test_the_tranches_sum_to_the_posted_total_exactly(self):
        for level in range(1, 21):
            for enc in (1, 2, 3):
                total = rpg.quest_xp_total(level, enc)
                paid = (enc * rpg.quest_encounter_xp(level, enc)
                        + rpg.quest_clear_xp(level, enc)
                        + rpg.quest_turnin_xp(level, enc))
                self.assertEqual(paid, total, (level, enc))

    def test_the_shares_are_the_settled_forty_forty_twenty(self):
        self.assertAlmostEqual(rpg.QUEST_ENCOUNTER_SHARE, 0.40)
        self.assertAlmostEqual(rpg.QUEST_TURNIN_SHARE, 0.20)
        level, enc = 10, 3
        total = rpg.quest_xp_total(level, enc)
        self.assertAlmostEqual(
            rpg.quest_turnin_xp(level, enc) / total, 0.20, places=2)
        self.assertAlmostEqual(
            rpg.quest_clear_xp(level, enc) / total, 0.40, places=2)

    def test_the_turn_in_tranche_is_the_smaller_half_of_the_lump(self):
        # Reporting back diligently is real XP but smallish -- the gold is
        # the turn-in's real weight.
        for level in (1, 5, 12, 20):
            self.assertLess(rpg.quest_turnin_xp(level, 2),
                            rpg.quest_clear_xp(level, 2))


class TheRoadInsideTheWindow(unittest.TestCase):
    """The clock buys the WHOLE road (2026-08-15, Local Quest Geography):
    out through every Site in cursor order, then home. It used to buy the
    homeward leg only, which posted a job three days out with the same
    window as one in the settlement's own fields."""

    def test_a_job_with_no_sites_buys_no_road_days(self):
        world = _world()
        settlement = quests.settlements(world)[0]
        quest = {"origin": settlement["key"], "sites": []}
        self.assertEqual(quests.route_days(world, quest), 0)

    def test_the_window_widens_by_the_whole_route(self):
        world = _world()
        for quest in world["quests"].values():
            if quest.get("kind") == "delivery" or not quest.get("sites"):
                continue
            road = quests.route_days(world, quest)
            origin = world["areas"][quest["origin"]]
            here, want = origin["tile"], 0
            for site_id in quest["sites"]:
                tile = world["areas"][world["sites"][site_id]["area"]]["tile"]
                want += places.path_days(here, tile)
                here = tile
            want += places.path_days(here, origin["tile"])
            self.assertEqual(road, want)
            lo, hi = quests.QUEST_WINDOW_DAYS
            self.assertGreaterEqual(quest["window"], lo + road)
            self.assertLessEqual(quest["window"], hi + road)

    def test_one_site_costs_the_trip_out_and_the_trip_home(self):
        """A single-Site job buys TWICE its distance -- the doctrine the
        deliveries have carried since they shipped, now applied to ordinary
        work: the party has to get there before it can get back."""
        world = _world()
        settlement = quests.settlements(world)[0]
        far = max((a for a in quests.all_areas(world)
                   if a["land"] != settlement["land"]),
                  key=lambda a: places.path_days(settlement["tile"],
                                                 a["tile"]))
        near = world["areas"][world["tiles"][settlement["tile"]]
                              ["natural_area"]]
        for area, site_id in ((far, "site/test/far"),
                              (near, "site/test/near")):
            quests.new_site(world, area["key"], site_id, "a place", 3)
        far_road = quests.route_days(
            world, {"origin": settlement["key"], "sites": ["site/test/far"]})
        near_road = quests.route_days(
            world, {"origin": settlement["key"], "sites": ["site/test/near"]})
        self.assertEqual(near_road, 0)          # same Tile: no road at all
        self.assertGreater(far_road, near_road)
        self.assertEqual(far_road, 2 * places.path_days(settlement["tile"],
                                                        far["tile"]))

    def test_a_two_site_job_pays_for_the_detour_between_them(self):
        """Two Sites on OPPOSITE sides of the origin cost the walk between
        them, not twice the distance to the last one: the cursor visits them
        in order, and the road it actually walks is what the window buys."""
        world = _world()
        settlement = quests.settlements(world)[0]
        here = settlement["tile"]
        row, column = places.tile_row_column(here)
        west = places.tile_id(row, max(1, column - 2))
        east = places.tile_id(row, min(places.MAP_COLUMNS, column + 2))
        for tile_id, site_id in ((west, "site/test/west"),
                                 (east, "site/test/east")):
            area = world["areas"][world["tiles"][tile_id]["natural_area"]]
            quests.new_site(world, area["key"], site_id, "a place", 3)
        road = quests.route_days(
            world, {"origin": settlement["key"],
                    "sites": ["site/test/west", "site/test/east"]})
        self.assertEqual(road,
                         places.path_days(here, west)
                         + places.path_days(west, east)
                         + places.path_days(east, here))
        self.assertGreater(road, 2 * places.path_days(here, east))


class TheWorkDoneStage(unittest.TestCase):
    def setUp(self):
        self.world = _world()
        self.state = _state(self.world, day=6)
        self.quest = _quest_in(self.world, self.state)

    def _finish_the_work(self):
        log: list[str] = []
        session.advance_quest(self.state, log, self.quest["id"])
        return log

    def test_the_job_goes_to_work_done_not_to_done(self):
        self._finish_the_work()
        self.assertEqual(self.quest["status"], "work_done")
        self.assertEqual(self.quest["work_done_day"], 6)

    def test_the_field_tranche_lands_and_the_gold_does_not(self):
        before = [h.xp for h in self.state["party"]]
        self._finish_the_work()
        field = rpg.quest_clear_xp(self.quest["level"], 1)
        for h, was in zip(self.state["party"], before):
            self.assertEqual(h.xp - was, field)
        self.assertEqual(self.state["purse"].gold, 0)

    def test_the_field_tranche_is_never_banded(self):
        # Only the turn-in tranche and the gold are ever banded or lost.
        self.state["clock"].day = self.quest["deadline_day"] + 1
        self.assertEqual(quests.quest_band(self.quest,
                                           self.state["clock"].day), "late")
        before = self.state["party"][0].xp
        self._finish_the_work()
        self.assertEqual(self.state["party"][0].xp - before,
                         rpg.quest_clear_xp(self.quest["level"], 1))

    def test_the_banner_names_the_giver_the_area_and_the_command(self):
        log = self._finish_the_work()
        text = "\n".join(log)
        self.assertIn("THE JOB IS DONE", text)
        self.assertIn("Kristryd", text)
        self.assertIn(f"turnin {self.quest['id']}", text)

    def test_the_world_changes_at_work_done_not_at_the_turn_in(self):
        # The pass reopens when the deed is done, not when it is paid.
        with mock.patch("session.complete_quest_place_state") as change:
            self._finish_the_work()
        change.assert_called_once()

    def test_no_epilogue_and_no_history_record_until_the_giver_hears_it(self):
        log = self._finish_the_work()
        self.assertFalse(any("EPILOGUE" in line for line in log), log)
        self.assertEqual(self.state["history"], [])

    def test_the_reward_weapon_waits_for_the_giver(self):
        self.quest["reward_weapon"] = {"name": "a bright longsword",
                                       "description": "test steel"}
        self.quest["gold_total"] = 0
        self._finish_the_work()
        self.assertIsNone(self.state.get("pending_reward"))


class TheTurnIn(unittest.TestCase):
    def setUp(self):
        self.world = _world()
        self.state = _state(self.world, day=6)
        self.quest = _quest_in(self.world, self.state)
        session.advance_quest(self.state, [], self.quest["id"])
        self.assertEqual(self.quest["status"], "work_done")

    def _turnin(self, **args):
        args.setdefault("quest", self.quest["id"])
        args.setdefault("here", False)
        return _run(session.cmd_turnin, self.state, **args)

    def test_it_pays_the_gold_and_the_turn_in_tranche(self):
        before = self.state["party"][0].xp
        self._turnin()
        band = quests.quest_band(self.quest, 6)
        mult = quests.QUEST_PAY_BANDS[band]
        want_xp = round(rpg.quest_turnin_xp(self.quest["level"], 1) * mult)
        self.assertEqual(self.state["party"][0].xp - before, want_xp)
        self.assertGreater(self.state["purse"].gold, 0)
        self.assertEqual(self.quest["status"], "done")
        self.assertEqual(self.quest["turned_in_day"], 6)

    def test_it_is_gated_on_standing_where_the_giver_stands(self):
        far = next(a for a in quests.all_areas(self.world)
                   if a["key"] != self.quest["origin"])
        self.state["position"] = session._area_position(far)
        out = self._turnin()
        self.assertEqual(self.quest["status"], "work_done")
        self.assertEqual(self.state["purse"].gold, 0)
        self.assertIn("business", out)

    def test_the_here_override_pays_anywhere(self):
        far = next(a for a in quests.all_areas(self.world)
                   if a["key"] != self.quest["origin"])
        self.state["position"] = session._area_position(far)
        self._turnin(here=True)
        self.assertEqual(self.quest["status"], "done")
        self.assertGreater(self.state["purse"].gold, 0)

    def test_the_band_is_read_off_the_turn_in_day_not_the_work_day(self):
        # The road home is finally inside the clock.
        self.state["clock"].day = self.quest["deadline_day"] + 1
        self._turnin()
        late = quests.QUEST_PAY_BANDS["late"]
        self.assertEqual(
            self.state["purse"].gold,
            round(quests.quest_gold_posted(self.quest) * late)
            + rpg.cha_gold_bonus(
                self.state["party"],
                round(quests.quest_gold_posted(self.quest) * late)))

    def test_the_epilogue_and_the_history_record_land_here(self):
        out = self._turnin()
        self.assertIn("EPILOGUE", out)
        quest_records = [r for r in self.state["history"]
                         if r["kind"] == "quest"]
        self.assertEqual(len(quest_records), 1)
        self.assertIn("done", quest_records[0]["line"])

    def test_the_reward_weapon_is_claimable_at_the_giver(self):
        self.quest["reward_weapon"] = {"name": "a bright longsword",
                                       "description": "test steel"}
        out = self._turnin()
        self.assertEqual(self.state["pending_reward"]["name"],
                         "a bright longsword")
        self.assertIn("claim", out)

    def test_companions_gain_satisfaction_in_town(self):
        ally = self.state["party"][1]
        ally.satisfaction = 5
        self._turnin()
        self.assertEqual(ally.satisfaction, 6)

    def test_the_cha_talk_up_applies_to_the_gold(self):
        pc = self.state["party"][0]
        pc.cha = rpg.PARTY_CAPACITY_BASE_CHA + 2
        self._turnin()
        band = quests.QUEST_PAY_BANDS[quests.quest_band(self.quest, 6)]
        base = round(quests.quest_gold_posted(self.quest) * band)
        self.assertEqual(self.state["purse"].gold,
                         base + rpg.cha_gold_bonus(self.state["party"], base))

    def test_a_job_whose_work_is_not_done_is_refused(self):
        plain = _quest_in(self.world, self.state)
        out = _run(session.cmd_turnin, self.state, quest=plain["id"],
                   here=False)
        self.assertIn("not done", out)
        self.assertEqual(plain["status"], "open")

    def test_paying_twice_is_refused(self):
        self._turnin()
        gold = self.state["purse"].gold
        out = self._turnin()
        self.assertIn("already paid", out)
        self.assertEqual(self.state["purse"].gold, gold)

    def test_a_delivery_is_sent_to_its_destination_instead(self):
        delivery = {"id": "d1", "kind": "delivery", "name": "The Parcel",
                    "dest_name": "Far Town", "status": "open", "level": 0,
                    "next": {"site": 0, "room": 0}, "sites": []}
        self.world["quests"]["d1"] = delivery
        out = _run(session.cmd_turnin, self.state, quest="d1", here=False)
        self.assertIn("arriving at Far Town is the turn-in", out)


class LostAfterTheWorkIsDone(unittest.TestCase):
    def setUp(self):
        self.world = _world()
        self.state = _state(self.world, day=6)
        self.quest = _quest_in(self.world, self.state)
        session.advance_quest(self.state, [], self.quest["id"])
        self.xp_banked = self.state["party"][0].xp
        self.state["clock"].day = (self.quest["deadline_day"]
                                   + quests.QUEST_GRACE_DAYS + 1)

    def test_the_clock_marks_it_done_never_paid(self):
        notices = session.board_clock(self.state)
        self.assertEqual(self.quest["status"], "lost")
        self.assertTrue(any("NEVER PAID" in n for n in notices), notices)

    def test_the_banked_eighty_percent_stays(self):
        session.board_clock(self.state)
        self.assertEqual(self.state["party"][0].xp, self.xp_banked)
        self.assertEqual(self.state["purse"].gold, 0)

    def test_no_failure_rumor_fires(self):
        # The monsters are dead -- the world changed. The giver's grievance
        # is story material, not a penalty.
        origin = self.world["areas"][self.quest["origin"]]
        with mock.patch("session._remember_failure") as rumor:
            session.board_clock(self.state)
        for call in rumor.call_args_list:
            self.assertIsNot(call.args[1], self.quest)
        self.assertFalse(origin.get("rumors"))

    def test_the_place_states_stay_completed(self):
        with mock.patch("session.complete_quest_place_state") as change:
            session.board_clock(self.state)
        change.assert_not_called()      # it already ran at work-done

    def test_the_record_reads_done_never_paid(self):
        session.board_clock(self.state)
        line = [r for r in self.state["history"]
                if r["kind"] == "quest"][0]["line"]
        self.assertIn("never paid", line)

    def test_turning_in_past_the_grace_pays_nothing(self):
        out = _run(session.cmd_turnin, self.state, quest=self.quest["id"],
                   here=False)
        self.assertEqual(self.quest["status"], "lost")
        self.assertEqual(self.state["purse"].gold, 0)
        self.assertIn("NEVER PAID", out)

    def test_an_unfinished_job_still_fails_the_old_way(self):
        plain = _quest_in(self.world, self.state)
        plain["deadline_day"] = self.state["clock"].day - (
            quests.QUEST_GRACE_DAYS + 1)
        notices = session.board_clock(self.state)
        self.assertEqual(plain["status"], "failed")
        self.assertTrue(any("JOB LOST" in n for n in notices), notices)


class TheExemptions(unittest.TestCase):
    """The turn-in stage is for HONEST work with a giver. Everything with
    no giver to return to, or whose giver is unreachable by design, pays
    where the last body falls exactly as before."""

    def setUp(self):
        self.world = _world()
        self.state = _state(self.world, day=6)

    def _close(self, **fields):
        quest = _quest_in(self.world, self.state, **fields)
        log: list[str] = []
        session.advance_quest(self.state, log, quest["id"])
        return quest, log

    def test_a_conquest_garrison_job_pays_at_work_done(self):
        area = quests.settlements(self.world)[1]
        with mock.patch("session.conquest.take_settlement", return_value=[]):
            quest, log = self._close(conquest=area["key"])
        self.assertEqual(quest["status"], "done")
        self.assertGreater(self.state["purse"].gold, 0)

    def test_a_hell_assignment_pays_at_work_done(self):
        quest, log = self._close(hell_task=True, align="dark")
        self.assertEqual(quest["status"], "done")
        self.assertGreater(self.state["purse"].gold, 0)

    def test_dark_work_pays_at_work_done(self):
        quest, log = self._close(align="dark")
        self.assertEqual(quest["status"], "done")
        self.assertGreater(self.state["purse"].gold, 0)

    def test_an_exempt_job_pays_both_lump_tranches_at_once(self):
        quest, log = self._close(align="dark")
        band = quests.QUEST_PAY_BANDS[quests.quest_band(quest, 6)]
        want = round((rpg.quest_clear_xp(3, 1) + rpg.quest_turnin_xp(3, 1))
                     * band)
        self.assertEqual(self.state["party"][0].xp, want)

    def test_honest_board_work_is_not_exempt(self):
        quest, log = self._close()
        self.assertEqual(quest["status"], "work_done")
        self.assertEqual(self.state["purse"].gold, 0)


class TheCareerBenchStillPaysTheWholeJob(unittest.TestCase):
    def test_the_bench_splits_and_sums_to_the_same_total(self):
        # bench_quests' careers turn in instantly at the origin (they
        # teleport): the field tranche and the banded turn-in land
        # together, so career totals stay comparable.
        level, enc = 6, 2
        on_time = (rpg.quest_clear_xp(level, enc)
                   + round(rpg.quest_turnin_xp(level, enc) * 1.0))
        self.assertEqual(on_time, rpg.quest_xp_total(level, enc)
                         - enc * rpg.quest_encounter_xp(level, enc))


if __name__ == "__main__":
    unittest.main()
