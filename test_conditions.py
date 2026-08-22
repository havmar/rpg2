"""Contract suite for the CONDITIONS framework (2026-07-26, the attrition
rework's slice 3a -- rules.md's Conditions add-on).

The rules this pins are the ones that are easy to break later and expensive
to notice: the bounded stacking rule, the tick's position and its
never-kills guarantee, what survives the end of a fight, what first aid
reaches and what it deliberately does not, and the night's price. Plus the
two shipped customers and the save round-trip.

Run:  python -m unittest -v test_conditions.py
"""

import random
import unittest

import rpg
import sites
import session


def _dummy(name: str = "Test", hp: int = 20, **kw) -> rpg.Entity:
    """A plain body with no build attached -- enough to carry conditions."""
    return rpg.Entity(name=name, dex=4, str_=4, sta=8, max_hp=hp, **kw)


class StackingRule(unittest.TestCase):
    """CONDITION_STACK_RULE = refresh: never a second copy, never a sum."""

    def test_second_dose_does_not_add_a_copy(self):
        e = _dummy()
        rpg.apply_condition(e, "poison")
        rpg.apply_condition(e, "poison")
        self.assertEqual(len(e.conditions), 1)

    def test_power_takes_the_max_never_the_sum(self):
        e = _dummy()
        rpg.apply_condition(e, "poison", power=1)
        rpg.apply_condition(e, "poison", power=3)
        self.assertEqual(rpg.condition_of(e, "poison").power, 3)
        rpg.apply_condition(e, "poison", power=1)
        self.assertEqual(rpg.condition_of(e, "poison").power, 3)

    def test_duration_takes_the_longer_of_the_two(self):
        e = _dummy()
        rpg.apply_condition(e, "burn", rounds=2)
        rpg.apply_condition(e, "burn", rounds=5)
        self.assertEqual(rpg.condition_of(e, "burn").rounds, 5)
        rpg.apply_condition(e, "burn", rounds=1)
        self.assertEqual(rpg.condition_of(e, "burn").rounds, 5)

    def test_an_untimed_dose_wins_over_a_timed_one_both_ways(self):
        # Once something is bleeding freely, a timed dose must not hand it
        # an expiry -- and an untimed dose must remove an existing one.
        e = _dummy()
        rpg.apply_condition(e, "bleed", rounds=3)
        rpg.apply_condition(e, "bleed", rounds=None)
        self.assertIsNone(rpg.condition_of(e, "bleed").rounds)
        rpg.apply_condition(e, "bleed", rounds=3)
        self.assertIsNone(rpg.condition_of(e, "bleed").rounds)

    def test_different_kinds_coexist(self):
        e = _dummy()
        rpg.apply_condition(e, "poison")
        rpg.apply_condition(e, "burn")
        self.assertEqual({c.kind for c in e.conditions}, {"poison", "burn"})


class TheTick(unittest.TestCase):

    def test_tick_costs_the_summed_power_and_counts_down(self):
        e = _dummy(hp=20)
        rpg.apply_condition(e, "poison", power=1)      # untimed
        rpg.apply_condition(e, "burn", power=2, rounds=2)
        rpg._tick_conditions([e], set(), [])
        self.assertEqual(e.hp, 17)
        self.assertEqual(rpg.condition_of(e, "burn").rounds, 1)
        self.assertIsNone(rpg.condition_of(e, "poison").rounds)

    def test_timed_conditions_expire_untimed_ones_do_not(self):
        e = _dummy(hp=20)
        rpg.apply_condition(e, "burn", power=1, rounds=1)
        rpg.apply_condition(e, "poison", power=1)
        rpg._tick_conditions([e], set(), [])
        self.assertIsNone(rpg.condition_of(e, "burn"))
        self.assertIsNotNone(rpg.condition_of(e, "poison"))

    def test_a_tick_can_never_kill_only_Down(self):
        e = _dummy(hp=2)
        rpg.apply_condition(e, "bleed", power=99)
        rpg._tick_conditions([e], set(), [])
        self.assertEqual(e.hp, 0)
        self.assertTrue(e.down)
        self.assertFalse(e.dead)

    def test_a_fallen_body_keeps_only_untimed_conditions(self):
        # A corpse stops burning; the venom is still in it when it is
        # helped back up.
        e = _dummy(hp=1)
        e.hp = 0
        rpg.apply_condition(e, "burn", rounds=3)
        rpg.apply_condition(e, "poison")
        rpg._tick_conditions([e], set(), [])
        self.assertEqual([c.kind for c in e.conditions], ["poison"])

    def test_falls_are_worded_by_side(self):
        # bench_bestiary/tune grep on "goes down" to count HERO falls; foes
        # fall with "*** X falls. ***". The tick must follow the melee's own
        # wording or the harnesses silently mis-count.
        hero, foe = _dummy("Inga", hp=1), _dummy("Wolf 1", hp=1)
        for e in (hero, foe):
            rpg.apply_condition(e, "bleed", power=5)
        log: list[str] = []
        rpg._tick_conditions([hero, foe], {hero}, log)
        text = "\n".join(log)
        self.assertIn("Inga goes down, out of the fight.", text)
        self.assertIn("*** Wolf 1 falls. ***", text)
        self.assertNotIn("Wolf 1 goes down", text)

    def test_the_player_log_gets_one_collapsed_quiet_line_a_round(self):
        a, b, c = _dummy("A"), _dummy("B"), _dummy("C")
        for e in (a, b, c):
            rpg.apply_condition(e, "poison")
        log = rpg.CombatLog()
        log.round_start(1)
        rpg._tick_conditions([a, b, c], {a}, log)
        log.finish_rounds()
        # All three ticked, but the round was otherwise quiet: it collapses.
        self.assertEqual(log.player, ["Round 1: nothing lands."])

    def test_the_tick_runs_after_regen_inside_a_round(self):
        # regen -> conditions, in that order. Discriminating case: a
        # regenerator two HP down whose knitting is capped at max. Regen
        # first ends the round at max-1; conditions first would end it at
        # max. (The opponent is built to never land, so only the round-end
        # bookkeeping moves the troll's HP.)
        troll = _dummy("Troll 1", hp=20, regen=3)
        troll.hp = 18
        rpg.apply_condition(troll, "burn", power=1, rounds=3)
        harmless = _dummy("Straw", hp=500)
        harmless.dex, harmless.str_ = -50, 0
        rpg.group_combat([harmless], [troll], random.Random(1), [],
                         max_rounds=1)
        self.assertEqual(troll.hp, 19)


class FightEndAndTreatment(unittest.TestCase):

    def test_clear_fight_states_drops_timed_keeps_untimed(self):
        e = _dummy()
        rpg.apply_condition(e, "burn", rounds=5)
        rpg.apply_condition(e, "poison")
        rpg._clear_fight_states([e])
        self.assertEqual([c.kind for c in e.conditions], ["poison"])

    def test_stabilize_stops_bleeding_and_leaves_venom(self):
        up, felled = _dummy("Up"), _dummy("Felled")
        felled.hp = 0
        for e in (up, felled):
            rpg.apply_condition(e, "bleed")
            rpg.apply_condition(e, "poison")
        rpg._stabilize([up, felled], [])
        self.assertEqual([c.kind for c in up.conditions], ["poison"])
        # Nobody binds the wounds of someone who is not standing.
        self.assertEqual({c.kind for c in felled.conditions},
                         {"bleed", "poison"})

    def test_a_won_fight_stabilizes_the_survivors(self):
        hero = _dummy("Inga", hp=60)
        hero.dex, hero.str_ = 20, 20
        hero.weapon = rpg.WEAPONS["schweizersäbel"]
        foe = _dummy("Mook 1", hp=1)
        foe.dex, foe.str_ = 0, 0
        rpg.apply_condition(hero, "bleed")
        rpg.apply_condition(hero, "poison")
        rpg.group_combat([hero], [foe], random.Random(3), [])
        self.assertFalse(foe.alive)
        self.assertTrue(hero.alive)
        self.assertIsNone(rpg.condition_of(hero, "bleed"))
        self.assertIsNotNone(rpg.condition_of(hero, "poison"))

    def test_a_healing_potion_closes_bleeding_but_is_no_antidote(self):
        h = _dummy(hp=20)
        h.hp = 5
        h.items["healing"] = 1
        rpg.apply_condition(h, "bleed")
        rpg.apply_condition(h, "poison")
        rpg.use_potion(h, "healing", [])
        self.assertIsNone(rpg.condition_of(h, "bleed"))
        self.assertIsNotNone(rpg.condition_of(h, "poison"))

    def test_the_night_sweats_everything_out_at_a_price(self):
        # The price comes off BEFORE the night's own recovery, so the net
        # effect is that a poisoned night heals less (and can lose ground).
        clean, sick = _dummy("Clean", hp=20), _dummy("Sick", hp=20)
        clean.hp = sick.hp = 20
        rpg.apply_condition(sick, "poison")
        rpg.apply_condition(sick, "bleed")
        rpg.long_rest([clean, sick], rpg.Clock(), [])
        self.assertEqual(sick.conditions, [])
        self.assertEqual(clean.hp, 20)
        self.assertEqual(sick.hp,
                         20 - 2 * rpg.POISON_NIGHT_HP
                         + sick.hp_regen_per_night)

    def test_the_night_never_kills(self):
        h = _dummy(hp=20)
        h.hp = 1
        rpg.apply_condition(h, "poison")
        rpg.long_rest([h], rpg.Clock(), [])
        self.assertGreaterEqual(h.hp, 1)
        self.assertFalse(h.dead)

    def test_a_fled_room_binds_its_own_wounds(self):
        foe = _dummy("Mook 1")
        rpg.apply_condition(foe, "poison")
        survivors = rpg.refresh_foes_after_retreat([foe], days_passed=0)
        self.assertEqual(survivors[0].conditions, [])


class TheShippedCustomers(unittest.TestCase):

    def test_the_great_spider_is_venomous_and_says_so(self):
        spider = sites.make_foe("great spider", 1, random.Random(1))
        self.assertEqual(spider.inflicts, "poison")
        self.assertEqual(rpg.CONDITION_ROUNDS["poison"], None)
        roster = "\n".join(sites.roster_lines([spider]))
        self.assertIn("venomous", roster)

    def test_the_pyromancers_fire_clings_and_says_so(self):
        pyro = sites.make_foe("pyromancer", 1, random.Random(1))
        self.assertEqual(pyro.inflicts, "burn")
        self.assertEqual(rpg.CONDITION_ROUNDS["burn"], rpg.BURN_ROUNDS)
        self.assertIn("fire clings", "\n".join(sites.roster_lines([pyro])))

    def test_nothing_else_in_the_catalog_inflicts_anything(self):
        # The acceptance criterion for slice 3a, as an assertion: exactly two
        # rows carry a rider. Adding a third is a bench-round decision.
        carriers = {k for k, spec in sites.FOES.items() if spec.inflicts}
        self.assertEqual(carriers, {"great spider", "pyromancer"})

    def test_hero_fire_wizards_do_not_burn(self):
        # Deliberate: a school-wide rider moves every bestiary row, because
        # the bench's reference duo rolls fire wizards. See the conditions
        # constants block.
        wizard = _dummy("Wiz", hp=20, mind=8, power=10)
        wizard.school = "fire"
        wizard.spells = {"fire": 2}
        self.assertEqual(wizard.inflicts, "")
        target = _dummy("Mook 1", hp=40)
        rng = random.Random(0)
        for _ in range(40):
            wizard.cur_power = 10
            rpg._attack(wizard, target, rng, [], cast="fire")
        self.assertIsNone(rpg.condition_of(target, "burn"))

    def test_a_landed_bite_poisons_a_missed_one_does_not(self):
        spider = _dummy("Great Spider 1", inflicts="poison")
        spider.dex, spider.str_ = 20, 20     # this bite lands and hurts
        target = _dummy("Inga", hp=200)
        target.dex, target.str_ = 0, 0
        rpg._attack(spider, target, random.Random(2), [])
        self.assertLess(target.hp, 200)
        self.assertIsNotNone(rpg.condition_of(target, "poison"))

        gnat = _dummy("Gnat 1", inflicts="poison")
        gnat.dex, gnat.str_ = -50, 0        # never wins an exchange
        clean = _dummy("Gard", hp=200)
        clean.dex, clean.str_ = 20, 20
        for _ in range(20):
            rpg._attack(gnat, clean, random.Random(4), [])
        self.assertEqual(clean.hp, 200)
        self.assertIsNone(rpg.condition_of(clean, "poison"))


class SaveRoundTrip(unittest.TestCase):

    def test_conditions_survive_the_save(self):
        h = _dummy("Inga")
        rpg.apply_condition(h, "poison", source="Great Spider 2")
        rpg.apply_condition(h, "burn", power=2, rounds=3)
        back = session._entity_from_dict(session._entity_to_dict(h))
        self.assertEqual(
            sorted((c.kind, c.power, c.rounds, c.source)
                   for c in back.conditions),
            sorted((c.kind, c.power, c.rounds, c.source)
                   for c in h.conditions))


if __name__ == "__main__":
    unittest.main()
