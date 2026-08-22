"""Contract suite for the CONQUEST domain layer (2026-07-27 -- rules.md's
Conquest & Holdings add-on, conquest.py).

The rules this pins: the garrison level is FIXED TERRAIN (stable across
rerolls, banded by settlement kind), the conquest job is an ordinary dark
quest underneath (schema, threat-honest rooms, the named defender over the
strongest slot, no clock, not on the board), the holding ledger's flips
(take / raid loss), the tribute arithmetic, the raid
resolution (heads against heads, the engine never sees it), the heat
floor, and the save round-trip. Display fit is checked against the
40-column wrap.

Run:  python -m unittest -v test_conquest.py
"""

import random
import unittest

import conquest
import karma
import places
import quests


def _world(seed: int = 11) -> dict:
    return quests.generate_world(seed=seed)


def _first(world: dict, subtype: str) -> dict:
    return next(s for s in quests.settlements(world)
                if places.settlement_tier(s) == subtype)


class GarrisonLevels(unittest.TestCase):
    """The garrison level is geography: banded, rolled once, stable."""

    def test_bands_by_subtype(self):
        world = _world()
        for s in quests.settlements(world):
            tier = places.settlement_tier(s)
            lo, hi = conquest.GARRISON_BANDS[tier]
            level = conquest.garrison_level(world, s)
            self.assertTrue(lo <= level <= hi,
                            f"{s['name']} ({tier}) rolled L{level} "
                            f"outside {lo}-{hi}")

    def test_stable_across_calls(self):
        world = _world()
        for s in quests.settlements(world):
            self.assertEqual(conquest.garrison_level(world, s),
                             conquest.garrison_level(world, s))

    def test_every_census_tier_is_priced(self):
        # 2026-08-21 (the tile economy arc's census session): the accidental
        # "city" merge of 2026-07-27 is undone and the five census words are
        # a design rung each. Every tier a settlement can carry has to reach
        # every conquest table, or a holding falls off the ledger.
        world = _world()
        subtypes = {s["subtype"] for s in quests.settlements(world)}
        self.assertTrue(subtypes <= set(places.TIERS), subtypes)
        self.assertEqual(sum(s["capital"] for s in quests.settlements(world)),
                         len(places.COUNTRIES))
        for table in (conquest.GARRISON_BANDS, conquest.CONQUEST_ENCOUNTERS,
                      conquest.TRIBUTE_PER_DAY, conquest.GARRISON_CAP,
                      conquest.RAID_STRENGTH, quests.SETTLEMENT_KINDS):
            self.assertEqual(set(table),
                             set(places.TIERS) | {"capital"}, table)

    def test_bands_are_a_contiguous_ladder(self):
        self.assertEqual(conquest.GARRISON_BANDS["village"][1] + 1,
                         conquest.GARRISON_BANDS["town"][0])
        self.assertEqual(conquest.GARRISON_BANDS["town"][1] + 1,
                         conquest.GARRISON_BANDS["capital"][0])
        # City-grade takes the capital's rung; the hamlet takes the
        # village's everywhere except tribute, which halves.
        for tier in ("city", "metropolis"):
            self.assertEqual(conquest.GARRISON_BANDS[tier],
                             conquest.GARRISON_BANDS["capital"])
            self.assertEqual(conquest.RAID_STRENGTH[tier],
                             conquest.RAID_STRENGTH["capital"])
        self.assertEqual(conquest.GARRISON_BANDS["hamlet"],
                         conquest.GARRISON_BANDS["village"])
        self.assertLess(conquest.TRIBUTE_PER_DAY["hamlet"],
                        conquest.TRIBUTE_PER_DAY["village"])


class TheConquestJob(unittest.TestCase):
    """An ordinary dark quest underneath."""

    def setUp(self):
        self.world = _world()
        self.rng = random.Random(3)
        self.target = _first(self.world, "village")
        self.quest = conquest.build_conquest_quest(self.world, self.target,
                                                   self.rng)

    def test_shape_matches_the_subtype(self):
        self.assertEqual(self.quest["encounters"],
                         conquest.CONQUEST_ENCOUNTERS["village"])
        self.assertEqual(self.quest["site_count"], 1)
        self.assertEqual(len(self.quest["sites"]), 1)
        rooms = quests.site_rooms(self.world,
                                  self.world["sites"][self.quest["sites"][0]])
        self.assertEqual(len(rooms), self.quest["encounters"])

    def test_level_is_the_garrison_level(self):
        self.assertEqual(self.quest["level"],
                         conquest.garrison_level(self.world, self.target))

    def test_dark_no_clock_no_giver(self):
        self.assertEqual(self.quest["align"], "dark")
        self.assertIsNone(self.quest.get("deadline_day"))
        self.assertIsNone(self.quest.get("giver"))
        self.assertEqual(quests.quest_band(self.quest, day=999), "on time")

    def test_not_posted_on_the_board(self):
        self.assertNotIn(self.quest["id"], self.target["quests"])

    def test_named_defender_caps_the_strongest_final_slot(self):
        site = self.world["sites"][self.quest["sites"][0]]
        boss = site.get("boss")
        self.assertIsNotNone(boss)
        final_kinds = quests.site_rooms(self.world, site)[-1]["kinds"]
        self.assertIn(boss["kind"], final_kinds)
        self.assertEqual(boss["kind"],
                         max(final_kinds, key=quests.threat_value))
        homeland = quests.land_homeland(self.world, self.target["land"])
        self.assertIn(conquest.DEFENDER_ROLES[homeland], boss["display"])

    def test_every_homeland_uses_the_shared_ladder(self):
        for homeland in quests.HOMELANDS:
            self.assertEqual(conquest.garrison_pool(homeland),
                             quests.LADDER_POOL)
        with self.assertRaises(KeyError):
            conquest.garrison_pool("nowhere")

    def test_strongbox_pays_in_days_of_tribute(self):
        self.assertEqual(self.quest["silver_total"],
                         conquest.PLUNDER_MULT
                         * conquest.TRIBUTE_PER_DAY["village"])


class TheHoldingLedger(unittest.TestCase):

    def setUp(self):
        self.world = _world()
        self.holdings: dict = {}
        self.village = _first(self.world, "village")
        self.town = _first(self.world, "town")

    def test_take_flips_the_tag(self):
        conquest.take_settlement(self.world, self.holdings, self.village,
                                 day=5)
        self.assertIn(self.village["key"], self.holdings)
        self.assertEqual(self.village.get("owner"), "party")
        rec = self.holdings[self.village["key"]]
        self.assertEqual(rec["garrison"], 0)
        self.assertEqual(rec["last_tribute_day"], 5)

    def test_lose_clears_the_tag(self):
        conquest.take_settlement(self.world, self.holdings, self.village,
                                 day=5)
        conquest.lose_holding(self.world, self.holdings,
                              self.village["key"])
        self.assertNotIn(self.village["key"], self.holdings)
        self.assertNotIn("owner", self.village)

    def test_tribute_accrues_per_day_and_collects_everything(self):
        conquest.take_settlement(self.world, self.holdings, self.village,
                                 day=0)
        conquest.take_settlement(self.world, self.holdings, self.town,
                                 day=4)
        due = (10 * conquest.TRIBUTE_PER_DAY["village"]
               + 6 * conquest.TRIBUTE_PER_DAY["town"])
        self.assertEqual(
            conquest.tribute_pending(self.world, self.holdings, day=10), due)
        self.assertEqual(
            conquest.collect_tribute(self.world, self.holdings, day=10), due)
        # Collected means collected: the meter restarts from the day.
        self.assertEqual(
            conquest.tribute_pending(self.world, self.holdings, day=10), 0)

    def test_heat_floor(self):
        self.assertEqual(conquest.heat_floor(0), 0)
        self.assertEqual(conquest.heat_floor(2),
                         2 * conquest.HOLDING_HEAT_STEP)


class Raids(unittest.TestCase):
    """Heads against heads; the combat engine never sees a raid."""

    def setUp(self):
        self.world = _world()
        self.holdings: dict = {}
        self.village = _first(self.world, "village")
        conquest.take_settlement(self.world, self.holdings, self.village,
                                 day=0)

    def _force_raid(self, garrison: int, days: int = 30) -> list[str]:
        """Roll raids with an rng seeded to fire (searched, not stubbed)."""
        rec = self.holdings[self.village["key"]]
        rec["garrison"] = garrison
        for seed in range(200):
            rec["last_raid_day"] = 0
            rec_before = dict(rec)
            lines = conquest.roll_raids(self.world, self.holdings,
                                        random.Random(seed), day=days)
            if lines:
                return lines
            self.holdings[self.village["key"]] = rec_before
            self.holdings[self.village["key"]]["last_raid_day"] = 0
        self.fail("no raid fired in 200 seeds")

    def test_full_garrison_always_repels_its_tier(self):
        # The design guarantee: a FULL garrison beats the worst raid its
        # tier rolls (cap >= max strength).
        for subtype, (lo, hi) in conquest.RAID_STRENGTH.items():
            self.assertGreaterEqual(conquest.GARRISON_CAP[subtype], hi)
        lines = self._force_raid(conquest.GARRISON_CAP["village"])
        self.assertIn("REPELLED", lines[0])
        self.assertIn(self.village["key"], self.holdings)

    def test_unguarded_holding_falls(self):
        lines = self._force_raid(0)
        self.assertIn("IS LOST", lines[0])
        self.assertNotIn(self.village["key"], self.holdings)
        self.assertNotIn("owner", self.village)

    def test_party_present_means_no_raid(self):
        rec = self.holdings[self.village["key"]]
        rec["garrison"] = 0
        for seed in range(50):
            rec["last_raid_day"] = 0
            lines = conquest.roll_raids(self.world, self.holdings,
                                        random.Random(seed), day=30,
                                        skip_key=self.village["key"])
            self.assertEqual(lines, [])
            self.assertIn(self.village["key"], self.holdings)

    def test_no_elapsed_days_no_raid(self):
        rec = self.holdings[self.village["key"]]
        rec["garrison"] = 0
        rec["last_raid_day"] = 30
        for seed in range(50):
            self.assertEqual(
                conquest.roll_raids(self.world, self.holdings,
                                    random.Random(seed), day=30), [])


class SaveRoundTrip(unittest.TestCase):
    """The ledger is plain JSON -- it must survive the save unchanged."""

    def test_holdings_survive_json(self):
        import json
        world = _world()
        holdings: dict = {}
        village = _first(world, "village")
        conquest.take_settlement(world, holdings, village, day=3)
        holdings[village["key"]]["garrison"] = 7
        back = json.loads(json.dumps(holdings))
        self.assertEqual(back, holdings)


class DisplayFit(unittest.TestCase):
    """Authored display copy stays legible at the 40-column wrap (the
    session driver re-wraps long lines; what must hold is that no single
    WORD outruns the width and the ledger lines read in a glance)."""

    def test_holdings_lines_words_fit(self):
        world = _world()
        holdings: dict = {}
        for s in quests.settlements(world)[:4]:
            conquest.take_settlement(world, holdings, s, day=0)
        for line in conquest.holdings_lines(world, holdings, day=9):
            for word in line.split():
                self.assertLessEqual(len(word), 40, f"word too wide: {word}")

    def test_take_lines_words_fit(self):
        world = _world()
        for s in quests.settlements(world):
            for line in conquest.take_settlement(world, {}, s, day=0):
                for word in line.split():
                    self.assertLessEqual(len(word), 40,
                                         f"word too wide: {word}")


if __name__ == "__main__":
    unittest.main()
