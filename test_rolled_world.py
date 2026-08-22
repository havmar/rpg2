"""The rolled world's contract suite (2026-08-21, the tile economy arc's
session 2).

Four parts. *The last harvest*: the scale, the contiguous problem regions
and their causes, the two guarantees (a drought somewhere in every world,
trouble near the start in seven worlds out of eight), the pinned sweep, and
the save round-trip. *The census*: the score law's fixed bands, the rolled
arrangement per tile, the authored answer keys (the sixteen historical
tiers, the nine mine towns, the three capitals), the slot cap and the tier
vocabulary, the charter and the manor, and the pinned sweep. *The two rolls
apart*: derived seeds, so moving one layer's tables leaves the other's
numbers untouched, and the layers differ per playthrough while their laws
do not. *The five words in the machinery*: every `settlement_tier`-keyed
table covering the census's vocabulary, the hamlet's shorter service row
and its recruit cap, and one broken world per clause the session added to
`validate_world`.

`python -m unittest -v test_rolled_world.py`
"""

from __future__ import annotations

import copy
import json
import random
import unittest

import conquest
import crime
import places
import quests
import rpg
import session

SWEEP = 60          # worlds a distribution test builds (60ms each). The
                    # 500-seed pins live in benchlog.md until session 4's
                    # bench_worldgen.py takes the sweeps over.
TIER_PEOPLE = {"hamlet": 60, "village": 300, "town": 3000,
               "city": 25000, "metropolis": 150000}


def _world(seed: int = 5) -> dict:
    return places.create_geography(seed)


def _land(world: dict) -> list[dict]:
    return [t for t in world["tiles"].values() if t["biome"] != "sea"]


def _slots(world: dict, tile: dict) -> list[dict]:
    return [world["settlement_slots"][sid] for sid in tile["settlement_slots"]]


# --------------------------------------------------------------------------- #
# A. The last harvest
# --------------------------------------------------------------------------- #

class TheLastHarvest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.world = _world()

    def test_every_land_tile_carries_a_percent_and_no_sea_tile_does(self):
        for tile in self.world["tiles"].values():
            if tile["biome"] == "sea":
                self.assertEqual((tile["harvest"], tile["harvest_cause"]),
                                 (None, None), tile["id"])
                continue
            self.assertIsInstance(tile["harvest"], int, tile["id"])
            self.assertGreaterEqual(tile["harvest"],
                                    places.SEVERITY_CLAMP[0], tile["id"])
            self.assertLessEqual(tile["harvest"], places.GOOD_CLAMP[1],
                                 tile["id"])

    def test_a_cause_and_a_problem_are_the_same_fact(self) -> None:
        """Below 75 is a problem tile, and a problem tile is somebody's
        region: there is no unexplained bad year and no cursed fine one."""
        for tile in _land(self.world):
            self.assertEqual(tile["harvest"] < places.HARVEST_PROBLEM,
                             tile["harvest_cause"] is not None, tile["id"])
            if tile["harvest_cause"] is not None:
                self.assertIn(tile["harvest_cause"], places.SUSCEPTIBILITY)

    def test_a_region_is_a_contiguous_piece_of_land(self) -> None:
        for seed in range(8):
            world = _world(seed)
            for region in world["harvest_regions"]:
                pool = set(region["tiles"])
                self.assertIn(region["center"], pool)
                reached, frontier = {region["center"]}, [region["center"]]
                while frontier:
                    tid = frontier.pop()
                    for nid in world["tiles"][tid]["neighbors"]:
                        if nid in pool and nid not in reached:
                            reached.add(nid)
                            frontier.append(nid)
                self.assertEqual(reached, pool, region["id"])
                causes = {r["cause"] for r in world["harvest_regions"]}
                for tid in pool:
                    tile = world["tiles"][tid]
                    self.assertNotEqual(tile["biome"], "sea")
                    # A tile two regions reached takes the WORSE year and
                    # that region's cause, so a member's cause is some
                    # region's, not necessarily this one's.
                    self.assertIn(tile["harvest_cause"], causes, tid)
                    self.assertLess(tile["harvest"], places.HARVEST_PROBLEM)

    def test_no_year_is_a_good_year_everywhere(self) -> None:
        """The drought guarantee: every world has its year of dust
        somewhere, whatever the causes rolled."""
        for seed in range(SWEEP):
            world = _world(seed)
            causes = {r["cause"] for r in world["harvest_regions"]}
            self.assertIn("drought", causes, seed)
            self.assertTrue(any(t["harvest"] < places.HARVEST_PROBLEM
                                for t in _land(world)), seed)

    def test_the_campaign_usually_opens_beside_a_bad_year(self) -> None:
        """The nearby-trouble nudge. Raw rolls put a region center within
        five days of the start in about a third of worlds; the nudge lifts
        it to roughly seven in eight, and the quiet start is the eighth."""
        near = 0
        for seed in range(SWEEP):
            world = _world(seed)
            if any(places.path_days(world["party_tile"], region["center"])
                   <= places.TROUBLE_DAYS
                   for region in world["harvest_regions"]):
                near += 1
        self.assertGreater(near / SWEEP, 0.75)
        self.assertLess(near / SWEEP, 1.0)      # the quiet start survives

    def test_the_sweep_distribution_is_the_pinned_one(self) -> None:
        coverage, sizes = [], []
        for seed in range(SWEEP):
            world = _world(seed)
            land = _land(world)
            bad = [t for t in land if t["harvest"] < places.HARVEST_PROBLEM]
            coverage.append(len(bad) / len(land))
            sizes += [len(r["tiles"]) for r in world["harvest_regions"]]
            self.assertTrue(bad, seed)          # never zero
            self.assertIn(len(world["harvest_regions"]),
                          range(places.HARVEST_REGIONS[0],
                                places.HARVEST_REGIONS[1] + 1))
        mean = sum(coverage) / len(coverage)
        self.assertGreater(mean, 0.13)          # ~18% of the land in trouble
        self.assertLess(mean, 0.23)
        self.assertGreater(sum(sizes) / len(sizes), 7)      # ~11 tiles
        self.assertLess(sum(sizes) / len(sizes), 15)

    def test_the_harvest_rides_the_save(self) -> None:
        clone = json.loads(json.dumps(self.world))
        self.assertEqual(clone["harvest_regions"],
                         self.world["harvest_regions"])
        for tid, tile in self.world["tiles"].items():
            self.assertEqual((clone["tiles"][tid]["harvest"],
                              clone["tiles"][tid]["harvest_cause"]),
                             (tile["harvest"], tile["harvest_cause"]), tid)
        places.validate_world(clone)


# --------------------------------------------------------------------------- #
# B. The settlement census
# --------------------------------------------------------------------------- #

class TheCensus(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.world = _world()

    def test_the_score_is_law_and_the_band_is_the_same_in_every_world(self):
        """The census is rolled per playthrough; what it is rolled AGAINST
        is not. France always feels like France."""
        other = _world(77)
        for tile in _land(self.world):
            self.assertEqual(places.population_band(self.world, tile),
                             places.population_band(other, tile["id"]),
                             tile["id"])
        with self.assertRaises(ValueError):
            sea = next(t for t in self.world["tiles"].values()
                       if t["biome"] == "sea")
            places.population_band(self.world, sea)

    def test_the_bands_are_the_authored_six_and_cover_the_map(self) -> None:
        seen = {places.population_band(self.world, t) for t in
                _land(self.world)}
        self.assertEqual(seen, set(places.BAND_WORDS))

    def test_a_tile_seats_at_most_the_lattice(self) -> None:
        for tile in _land(self.world):
            slots = _slots(self.world, tile)
            self.assertLessEqual(len(slots), places.SLOT_CAP, tile["id"])
            for slot in slots:
                self.assertIn(slot["tier"], places.TIERS, slot["id"])

    def test_the_slots_are_sorted_chief_first(self) -> None:
        rank = {tier: places.TIER_ORDER.index(letter)
                for letter, tier in places.TIER_LETTERS.items()}
        for tile in _land(self.world):
            ranks = [rank[slot["tier"]] for slot in _slots(self.world, tile)]
            self.assertEqual(ranks, sorted(ranks), tile["id"])

    def test_zero_is_a_real_tier(self) -> None:
        empty = [t for t in _land(self.world)
                 if not t["settlement_slots"]]
        self.assertGreater(len(empty), 20)
        self.assertLess(len(empty), 90)

    def test_the_historical_tiles_carry_their_authored_tiers(self) -> None:
        for seed in range(6):
            world = _world(seed)
            for row, column, name, _c, _b, capital in \
                    places.HISTORICAL_CITIES:
                tile = world["tiles"][places.tile_id(row, column)]
                slots = _slots(world, tile)
                self.assertEqual(slots[0]["name"], name)
                self.assertEqual(slots[0]["tier"],
                                 places.HISTORICAL_TIERS[name])
                self.assertEqual(slots[0]["capital"], capital)
                self.assertEqual(slots[0]["charter"], "free")
                self.assertTrue(slots[0]["authored"])

    def test_the_four_metropolises_and_the_nine_capitals(self) -> None:
        metros = {n for n, t in places.HISTORICAL_TIERS.items()
                  if t == "metropolis"}
        self.assertEqual(metros,
                         {"Paris", "Venice", "Constantinople", "Cairo"})
        capitals = {slot["name"] for slot
                    in self.world["settlement_slots"].values()
                    if slot["capital"]}
        self.assertEqual(capitals,
                         {"London", "Paris", "Prague", "Stockholm",
                          "Moscow", "Constantinople", "Cordoba", "Cairo",
                          "Kyiv"})

    def test_the_mine_towns_are_seated_by_name(self) -> None:
        self.assertEqual(len(places.MINES), 9)
        for seed in range(6):
            world = _world(seed)
            for (row, column), (town, goods) in places.MINES.items():
                tile = world["tiles"][places.tile_id(row, column)]
                slots = _slots(world, tile)
                self.assertEqual(slots[0]["name"], town)
                self.assertEqual(slots[0]["tier"], "town")
                self.assertEqual(slots[0]["charter"], "free")
                self.assertFalse(slots[0]["authored"])  # famous, not known
                self.assertTrue(goods)

    def test_falun_stands_alone_in_the_wilderness(self) -> None:
        """The mine town's law is what puts a town where no band would:
        Falun's own ground is wilderness and it seats a town anyway."""
        tile = self.world["tiles"][places.tile_id(3, 22)]
        self.assertEqual(places.population_band(self.world, tile),
                         "wilderness")
        self.assertEqual(_slots(self.world, tile)[0]["name"], "Falun")

    def test_only_the_dense_band_rolls_a_generated_city(self) -> None:
        for seed in range(10):
            world = _world(seed)
            for tile in _land(world):
                for slot in _slots(world, tile):
                    if slot["tier"] in places.CITY_GRADE \
                            and slot["name"] not in places.HISTORICAL_TIERS:
                        self.assertEqual(
                            places.population_band(world, tile), "dense",
                            tile["id"])

    def test_rich_country_keeps_its_quiet_tiles(self) -> None:
        """The variance is IN the tables: a high or dense tile rolling no
        town at all is what keeps France from reading as a town grid."""
        shares = []
        for seed in range(SWEEP):
            world = _world(seed)
            rich = [t for t in _land(world)
                    if places.population_band(world, t) in ("high", "dense")
                    and (t["row"], t["column"]) not in
                    places.HISTORICAL_BY_TILE]
            quiet = [t for t in rich
                     if not any(s["tier"] in ("town", "city", "metropolis")
                                for s in _slots(world, t))]
            self.assertTrue(quiet, seed)        # never zero
            shares.append(len(quiet) / len(rich))
        mean = sum(shares) / len(shares)
        self.assertGreater(mean, 0.30)          # ~37%
        self.assertLess(mean, 0.45)

    def test_the_sweep_distribution_is_the_pinned_one(self) -> None:
        totals = {tier: 0 for tier in places.TIERS}
        filled, souls = [], []
        for seed in range(SWEEP):
            world = _world(seed)
            counts = []
            for tile in _land(world):
                slots = _slots(world, tile)
                counts.append(len(slots))
                for slot in slots:
                    totals[slot["tier"]] += 1
            filled.append(sum(counts) / len(counts))
            souls.append(sum(TIER_PEOPLE[s["tier"]]
                             for s in world["settlement_slots"].values()))
        per = {tier: total / SWEEP for tier, total in totals.items()}
        self.assertEqual(per["metropolis"], 4.0)        # always the four
        self.assertAlmostEqual(per["city"], 18, delta=3)
        self.assertAlmostEqual(per["town"], 101, delta=8)
        self.assertAlmostEqual(per["village"], 402, delta=20)
        self.assertAlmostEqual(per["hamlet"], 92, delta=12)
        self.assertAlmostEqual(sum(per.values()), 615, delta=25)
        self.assertAlmostEqual(sum(filled) / SWEEP, 1.96, delta=0.10)
        self.assertAlmostEqual(sum(souls) / SWEEP, 1_500_000, delta=150_000)

    def test_the_charter_is_law_and_not_size(self) -> None:
        towns = free = 0
        for seed in range(12):
            world = _world(seed)
            for slot in world["settlement_slots"].values():
                if slot["tier"] in places.CITY_GRADE:
                    self.assertEqual(slot["charter"], "free", slot["id"])
                if slot["tier"] == "town" and not slot["authored"] \
                        and slot["name"] is None:
                    towns += 1
                    free += slot["charter"] == "free"
                if slot["tier"] in ("village", "hamlet"):
                    self.assertIsNone(slot["charter"], slot["id"])
        self.assertTrue(towns)
        self.assertAlmostEqual(free / towns, places.CHARTER_CHANCE,
                               delta=0.08)

    def test_the_manor_rides_a_village_led_tile_of_two_or_more(self) -> None:
        marked = tiles = 0
        for seed in range(12):
            world = _world(seed)
            for tile in _land(world):
                slots = _slots(world, tile)
                for slot in slots[1:]:
                    self.assertIsNone(slot["manor"], slot["id"])
                if len(slots) >= 2 and slots[0]["tier"] == "village":
                    tiles += 1
                    marked += slots[0]["manor"] == "manor"
                elif slots:
                    self.assertIsNone(slots[0]["manor"], slots[0]["id"])
        self.assertTrue(tiles)
        self.assertAlmostEqual(marked / tiles, places.MANOR_CHANCE,
                               delta=0.08)

    def test_the_census_rides_the_save(self) -> None:
        clone = json.loads(json.dumps(self.world))
        self.assertEqual(clone["settlement_slots"],
                         self.world["settlement_slots"])
        places.validate_world(clone)

    def test_the_census_is_this_world_s_own(self) -> None:
        """Rolled per playthrough on purpose: which tiles carry the towns
        is each world's business, even though the bands are not."""
        first = {tid: [s["tier"] for s in _slots(_world(1), t)]
                 for tid, t in _world(1)["tiles"].items()}
        other = _world(2)
        second = {tid: [s["tier"] for s in _slots(other, t)]
                  for tid in other["tiles"]
                  for t in (other["tiles"][tid],)}
        self.assertNotEqual(first, second)


# --------------------------------------------------------------------------- #
# C. The two rolls, apart
# --------------------------------------------------------------------------- #

class DerivedSeeds(unittest.TestCase):
    """Every roll takes its own derived stream, so a change in one layer's
    tables cannot move another layer's numbers -- which is what lets the
    existing benches measure the same board they always did."""

    def test_the_harvest_reads_the_start_tile_and_nothing_else(self) -> None:
        """The one thing the harvest takes from the census is WHERE THE
        CAMPAIGN OPENS, which the nearby-trouble nudge needs. Take the
        whole census away and re-roll: the same year comes back."""
        world = _world(4)
        before = [t["harvest"] for t in _land(world)]
        clone = copy.deepcopy(world)
        for tile in clone["tiles"].values():
            tile["settlement_slots"] = []
        clone["settlement_slots"] = {}
        places.roll_harvest(clone)
        self.assertEqual([t["harvest"] for t in _land(clone)], before)
        self.assertEqual(clone["harvest_regions"], world["harvest_regions"])

    def test_a_different_start_moves_the_nudge_and_only_the_nudge(self):
        world = _world(4)
        moved = copy.deepcopy(world)
        moved["party_tile"] = places.tile_id(3, 22)     # Falun, far north
        places.roll_harvest(moved)
        self.assertNotEqual([t["harvest"] for t in _land(moved)],
                            [t["harvest"] for t in _land(world)])
        self.assertEqual(moved["settlement_slots"],
                         world["settlement_slots"])

    def test_moving_the_harvest_tables_leaves_the_census_alone(self) -> None:
        before = _world(4)
        original = places.HARVEST_REGIONS
        places.HARVEST_REGIONS = (6, 6)
        try:
            after = _world(4)
        finally:
            places.HARVEST_REGIONS = original
        self.assertNotEqual([t["harvest"] for t in _land(before)],
                            [t["harvest"] for t in _land(after)])
        self.assertEqual(before["settlement_slots"],
                         after["settlement_slots"])

    def test_the_rolls_are_stable_for_one_seed(self) -> None:
        first, second = _world(9), _world(9)
        self.assertEqual(first["settlement_slots"],
                         second["settlement_slots"])
        self.assertEqual(first["harvest_regions"], second["harvest_regions"])
        self.assertEqual([t["harvest"] for t in _land(first)],
                         [t["harvest"] for t in _land(second)])


# --------------------------------------------------------------------------- #
# D. The five words in the machinery
# --------------------------------------------------------------------------- #

class TheFiveWords(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.world = _world()

    def test_every_tier_keyed_table_covers_the_census(self) -> None:
        """The rule the round named: every `settlement_tier`-keyed table
        grows the five words. A table that misses one answers wrongly about
        a settlement the census can produce."""
        full = set(places.TIERS) | {"capital"}
        # REQUIRED_SERVICES is keyed by the Area's SUBTYPE -- the five
        # census words -- and a capital adds its three counters on top.
        self.assertEqual(set(places.REQUIRED_SERVICES), set(places.TIERS))
        for table in (places.BOARD_ACTIVE_CHANCE,
                      quests.SETTLEMENT_KINDS, conquest.GARRISON_BANDS,
                      conquest.CONQUEST_ENCOUNTERS,
                      conquest.TRIBUTE_PER_DAY, conquest.GARRISON_CAP,
                      conquest.RAID_STRENGTH, rpg.HEALER_TIER_CAP):
            missing = full - set(table)
            self.assertFalse(missing, f"{sorted(missing)} missing")
        self.assertEqual(set(crime.TIER_ROW), full | {"wilds"})
        for tier in places.TIERS:
            self.assertIn(tier, str(rpg.DISEASE_REACH["cold"]))

    def test_the_board_ladder_reaches_the_new_words(self) -> None:
        chance = places.BOARD_ACTIVE_CHANCE
        self.assertEqual(chance["metropolis"], 1.0)
        self.assertEqual(chance["city"], 1.0)
        self.assertEqual(chance["hamlet"], 0.05)
        self.assertLess(chance["hamlet"], chance["village"])

    def test_a_hamlet_is_a_settlement_without_a_smith(self) -> None:
        world, found = None, None
        for seed in range(40):
            world = _world(seed)
            found = next((world["areas"][slot["area"]] for slot
                          in world["settlement_slots"].values()
                          if slot["tier"] == "hamlet" and slot["area"]), None)
            if found is not None:
                break
        self.assertIsNotNone(found, "no hamlet materialized in 40 worlds")
        kinds = {service["kind"] for service in found["services"]}
        self.assertTrue({"lodging", "general_goods", "healer"} <= kinds)
        self.assertNotIn("smith", kinds)
        self.assertTrue(places.has_service(found, "lodging"))
        self.assertFalse(places.has_service(found, "smith"))
        self.assertEqual(len(found["sites"]), 4)

    def test_the_hiring_market_reads_the_settlement(self) -> None:
        """A hamlet is not a hiring market: it turns up one face a day
        however much presence the PC has. The CAPACITY is untouched."""
        for tier, expected in (("hamlet", 1), ("village", 2), ("town", 3),
                               ("city", 3), ("metropolis", 3),
                               ("capital", 3)):
            here = {"subtype": tier, "capital": tier == "capital"}
            self.assertEqual(session.recruit_options(3, here), expected,
                             tier)
        self.assertEqual(session.recruit_options(1, {"subtype": "town",
                                                     "capital": False}), 1)

    def test_a_metropolis_wears_the_city_role(self) -> None:
        venice = next(area for area in self.world["areas"].values()
                      if area.get("name") == "Venice")
        self.assertEqual(venice["subtype"], "metropolis")
        self.assertEqual(places.settlement_tier(venice), "metropolis")
        self.assertEqual(
            places.CULTURE_SPECS["southern"]["settlement_templates"][
                venice["role"]]["tier"], "city")
        self.assertIn("city", venice["tags"])

    def test_an_illegal_rolled_world_raises_where_it_is_made(self) -> None:
        """One broken world per clause the census session added."""
        def broken(mutate):
            world = copy.deepcopy(self.world)
            mutate(world)
            with self.assertRaises(ValueError):
                places.validate_world(world)

        def a_fifth_settlement(world):
            tile = next(t for t in _land(world) if t["settlement_slots"])
            for index in range(len(tile["settlement_slots"]),
                               places.SLOT_CAP + 1):
                sid = f"{tile['id']}/settlement/{index + 1:02d}"
                slot = places._slot(sid, "hamlet", 1)
                slot.update(tile=tile["id"], index=index + 1)
                world["settlement_slots"][sid] = slot
                tile["settlement_slots"].append(sid)
                world["lands"][tile["country"]][
                    "settlement_slots"].append(sid)

        def invent_a_tier(world):
            _any_slot(world)["tier"] = "conurbation"

        def invent_a_charter(world):
            _any_slot(world)["charter"] = "imperial"

        def invent_a_manor(world):
            _any_slot(world)["manor"] = "duchy"

        def unfree_a_city(world):
            slot = next(s for s in world["settlement_slots"].values()
                        if s["tier"] in places.CITY_GRADE)
            slot["charter"] = None

        def demote_a_historical_city(world):
            world["settlement_slots"]["tile/r09/c10/settlement/01"][
                "tier"] = "village"

        def rename_a_mine_town(world):
            world["settlement_slots"]["tile/r09/c14/settlement/01"][
                "name"] = "Somewhere Else"

        def unfree_a_mine_town(world):
            world["settlement_slots"]["tile/r09/c14/settlement/01"][
                "charter"] = None

        def build_a_town_on_a_mountain(world):
            tile = next(t for t in world["tiles"].values()
                        if t["biome"] == "mountain"
                        and t["settlement_slots"]
                        and (t["row"], t["column"]) not in places.MINES)
            world["settlement_slots"][tile["settlement_slots"][0]][
                "tier"] = "town"

        def unsort_the_slots(world):
            tile = next(t for t in _land(world)
                        if len({world["settlement_slots"][s]["tier"]
                                for s in t["settlement_slots"]}) > 1)
            tile["settlement_slots"].reverse()

        def move_the_manor(world):
            tile = next(t for t in _land(world)
                        if len(t["settlement_slots"]) >= 2)
            for index, sid in enumerate(tile["settlement_slots"]):
                world["settlement_slots"][sid]["manor"] = \
                    "manor" if index else None

        def open_in_a_hamlet(world):
            world["settlement_slots"][world["start_slot"]]["tier"] = "hamlet"

        def harvest_at_sea(world):
            sea = next(t for t in world["tiles"].values()
                       if t["biome"] == "sea")
            sea["harvest"] = 90

        def a_percent_off_the_scale(world):
            _any_land(world)["harvest"] = 500

        def invent_a_cause(world):
            tile = next(t for t in _land(world)
                        if t["harvest_cause"] is not None)
            tile["harvest_cause"] = "locusts"

        def a_bad_year_with_no_cause(world):
            tile = next(t for t in _land(world)
                        if t["harvest_cause"] is not None)
            tile["harvest_cause"] = None

        def a_good_year_with_a_cause(world):
            tile = next(t for t in _land(world)
                        if t["harvest_cause"] is None)
            tile["harvest_cause"] = "drought"

        def a_year_with_no_trouble(world):
            world["harvest_regions"] = []

        def a_year_with_no_drought(world):
            for region in world["harvest_regions"]:
                region["cause"] = "frost"

        def a_region_without_its_center(world):
            region = world["harvest_regions"][0]
            region["tiles"] = [t for t in region["tiles"]
                               if t != region["center"]]

        def a_region_in_two_pieces(world):
            region = next(r for r in world["harvest_regions"]
                          if len(r["tiles"]) > 3)
            far = next(t for t in world["tile_order"]
                       if world["tiles"][t]["biome"] != "sea"
                       and t not in region["tiles"]
                       and not set(world["tiles"][t]["neighbors"])
                       & set(region["tiles"]))
            region["tiles"].append(far)
            world["tiles"][far]["harvest"] = 50
            world["tiles"][far]["harvest_cause"] = region["cause"]

        def trouble_at_sea(world):
            region = world["harvest_regions"][0]
            sea = next(nid for tid in region["tiles"]
                       for nid in world["tiles"][tid]["neighbors"]
                       if world["tiles"][nid]["biome"] == "sea")
            region["tiles"].append(sea)
            world["tiles"][sea]["harvest"] = 50
            world["tiles"][sea]["harvest_cause"] = region["cause"]

        for mutate in (a_fifth_settlement, invent_a_tier, invent_a_charter,
                       invent_a_manor, unfree_a_city,
                       demote_a_historical_city, rename_a_mine_town,
                       unfree_a_mine_town, build_a_town_on_a_mountain,
                       unsort_the_slots, move_the_manor, open_in_a_hamlet,
                       harvest_at_sea, a_percent_off_the_scale,
                       invent_a_cause, a_bad_year_with_no_cause,
                       a_good_year_with_a_cause, a_year_with_no_trouble,
                       a_year_with_no_drought, a_region_without_its_center,
                       a_region_in_two_pieces, trouble_at_sea):
            with self.subTest(mutate.__name__):
                broken(mutate)


def _any_slot(world: dict) -> dict:
    return world["settlement_slots"][
        next(iter(world["settlement_slots"]))]


def _any_land(world: dict) -> dict:
    return next(t for t in world["tiles"].values() if t["biome"] != "sea")


if __name__ == "__main__":
    unittest.main()
