"""Contract suite for the WORLD & NPC SIMULATION build (worldsim.md), the
ladder's own suite -- no sim and no bench imports it.

Session 1, THE SETTLEMENT TRIM (2026-08-07). The rules this pins: a land
BEGINS with three settlements (one capital, one town, one village, topped
up from what the catalog holds when a tier is missing); everything else the
catalog holds is the land's RESERVE POOL, unbuilt until something needs it
to exist; the need-to-exist draw builds a whole usable place (Sites, the
guaranteed services, their faces, a board that fills on the first look) and
records WHY it was founded; the draw can be steered by tier and by tags;
a land whose reserve is dry says no rather than inventing geography; and
the whole thing is seeded, stable, and JSON-clean so it rides the save.

Run:  python -m unittest -v test_worldsim.py
"""

import json
import random
import unittest

import conquest
import places
import quests


def _world(seed: int = 4471) -> dict:
    return quests.generate_world(seed)


def _settlements(world: dict, polity: str) -> list[dict]:
    return [world["areas"][aid] for aid in world["lands"][polity]["areas"]
            if world["areas"][aid]["kind"] == "settlement"]


class OpeningCensus(unittest.TestCase):
    """What a fresh world holds: three settlements a land, not a catalog."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.world = _world()

    def test_every_land_opens_with_three_settlements(self) -> None:
        for polity in self.world["lands"]:
            self.assertEqual(len(_settlements(self.world, polity)),
                             places.SETTLEMENTS_AT_WORLDGEN, polity)

    def test_one_capital_a_land_and_it_stays_first(self) -> None:
        # story.py raises its waves from settlements_by_land[land][0] and
        # casts the land's notables onto it: the capital is that seat.
        for polity, setts in quests.settlements_by_land(self.world).items():
            capitals = [s for s in setts if s["subtype"] == "capital"]
            self.assertEqual(len(capitals), 1, polity)
            self.assertIs(setts[0], capitals[0], polity)

    def test_the_opening_tiers_are_capital_town_village(self) -> None:
        for polity in self.world["lands"]:
            tiers = [s["subtype"] for s in _settlements(self.world, polity)]
            if polity == "dvarvengrond":
                # The dwarves author no village; the land tops up with the
                # second town rather than opening one settlement short.
                self.assertEqual(sorted(tiers), ["capital", "town", "town"])
            else:
                self.assertEqual(sorted(tiers), ["capital", "town", "village"])

    def test_the_world_is_28_natural_areas_and_18_settlements(self) -> None:
        areas = self.world["areas"].values()
        self.assertEqual(sum(a["kind"] == "natural" for a in areas), 28)
        self.assertEqual(sum(a["kind"] == "settlement" for a in areas), 18)

    def test_every_opening_settlement_is_usable(self) -> None:
        # A settlement the party can stand in: known from day one, its
        # required Sites built, its services attached and faced.
        for settlement in quests.settlements(self.world):
            self.assertTrue(settlement["known"], settlement["name"])
            self.assertTrue(settlement["sites"], settlement["name"])
            kinds = {s["kind"] for s in settlement["services"]}
            self.assertTrue({"lodging", "smith", "general_goods", "healer"}
                            <= kinds, settlement["name"])
            for service in settlement["services"]:
                self.assertIsNotNone(service["provider"], settlement["name"])


class TheReservePool(unittest.TestCase):
    """The catalog's remainder: names and skeletons, not places."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.world = _world()

    def test_unbuilt_catalog_settlements_wait_in_the_reserve(self) -> None:
        # Nothing authored is lost by the trim: every catalog settlement is
        # either one of the opening three or waiting in the reserve.
        for polity, spec in places.LAND_SPECS.items():
            built = {s["name"] for s in _settlements(self.world, polity)}
            waiting = {e["name"]
                       for e in places.reserve_settlements(self.world, polity)}
            authored = {name for name, _tier, _role, _tags
                        in spec["settlements"]}
            self.assertEqual(authored, authored & (built | waiting), polity)
            self.assertFalse(built & waiting, polity)

    def test_reserve_entries_are_unbuilt(self) -> None:
        for polity in self.world["lands"]:
            for entry in places.reserve_settlements(self.world, polity):
                aid = places.area_id(polity, entry["name"])
                self.assertNotIn(aid, self.world["areas"])

    def test_generated_villages_pair_the_name_pool_with_the_roles(self) -> None:
        for polity, spec in places.LAND_SPECS.items():
            entries = [e for e in places.reserve_settlements(self.world, polity)
                       if e["source"] == "worldgen"]
            roles = {role_id for role_id, _heading, _tags in spec["villages"]}
            if not roles:
                self.assertEqual(entries, [], polity)
                continue
            names = [e["name"] for e in entries]
            self.assertEqual(len(names), len(set(names)), polity)
            self.assertTrue(set(names) <= set(spec["village_names"]), polity)
            self.assertTrue({e["role"] for e in entries} <= roles, polity)

    def test_the_dwarves_hold_nothing_in_reserve(self) -> None:
        # Dvarvengrond's whole catalog is its opening three: a land can be
        # finished, and the draw has to survive that.
        self.assertEqual(places.reserve_settlements(self.world,
                                                    "dvarvengrond"), [])

    def test_the_reserve_rides_the_save(self) -> None:
        clone = json.loads(json.dumps(self.world))
        self.assertEqual(clone["lands"], self.world["lands"])


class TheNeedToExistDraw(unittest.TestCase):
    """Settlements exist because something needed them to."""

    def test_a_drawn_settlement_is_a_whole_place(self) -> None:
        world = _world()
        rng = random.Random(3)
        before = len(quests.settlements(world))
        area = quests.found_settlement(world, "tergal", rng,
                                       need="a rival center of power", day=12)
        self.assertIsNotNone(area)
        self.assertEqual(len(quests.settlements(world)), before + 1)
        self.assertIn(area["id"], world["areas"])
        self.assertIn(area["id"], world["lands"]["tergal"]["areas"])
        self.assertTrue(area["known"])
        self.assertFalse(area["visited"])
        self.assertTrue(area["sites"])
        kinds = {s["kind"] for s in area["services"]}
        self.assertTrue({"lodging", "smith", "general_goods", "healer"}
                        <= kinds)
        for service in area["services"]:
            self.assertIsNotNone(service["provider"])
            self.assertIn(service["provider"],
                          {npc["id"] for npc in world["npcs"]})

    def test_the_draw_records_why_and_when(self) -> None:
        world = _world()
        area = places.materialize_settlement(
            world, "gibili", need="the smelter's counterparty port", day=31)
        self.assertEqual(area["founded_for"], "the smelter's counterparty port")
        self.assertEqual(area["founded_day"], 31)
        self.assertIn({"day": 31, "target": area["id"], "action": "materialize"},
                      world["events"])

    def test_the_entry_leaves_the_reserve(self) -> None:
        world = _world()
        before = [e["name"]
                  for e in places.reserve_settlements(world, "ensimaa")]
        area = places.materialize_settlement(world, "ensimaa", need="a rival")
        after = [e["name"]
                 for e in places.reserve_settlements(world, "ensimaa")]
        self.assertEqual(before[1:], after)
        self.assertEqual(before[0], area["name"])

    def test_tier_narrows_the_draw(self) -> None:
        world = _world()
        for _ in range(2):
            area = places.materialize_settlement(world, "mortellaria",
                                                 need="a rival", tier="town")
            self.assertEqual(area["subtype"], "town")
        # Mortellaria authored three towns; two were left after the opening
        # draw, so the third ask finds no town at all.
        self.assertIsNone(places.materialize_settlement(
            world, "mortellaria", need="a rival", tier="town"))

    def test_tags_prefer_a_fitting_skeleton(self) -> None:
        world = _world()
        area = places.materialize_settlement(world, "mortellaria",
                                             need="a counterparty port",
                                             tags=("harbor", "coast"))
        self.assertTrue({"harbor", "coast"}.intersection(area["tags"]),
                        area["tags"])

    def test_a_dry_land_says_no(self) -> None:
        world = _world()
        self.assertIsNone(places.materialize_settlement(
            world, "dvarvengrond", need="a rival center of power"))
        drawn = []
        while True:
            area = places.materialize_settlement(world, "firascir",
                                                 need="a rival")
            if area is None:
                break
            drawn.append(area)
        self.assertTrue(drawn)
        self.assertIsNone(places.materialize_settlement(world, "firascir",
                                                        need="one more"))
        self.assertEqual(places.reserve_settlements(world, "firascir"), [])

    def test_names_and_ids_stay_unique_as_the_world_grows(self) -> None:
        world = _world()
        for polity in list(world["lands"]):
            while places.materialize_settlement(world, polity,
                                                need="stress") is not None:
                pass
        ids = [record["id"] for store in ("areas", "sites", "rooms")
               for record in world[store].values()]
        self.assertEqual(len(ids), len(set(ids)))
        # (Area NAMES are unique among settlements, not world-wide: the two
        # authored rivers deliberately carry one name across two lands.)
        names = [a["name"] for a in world["areas"].values()
                 if a["kind"] == "settlement"]
        self.assertEqual(len(names), len(set(names)))

    def test_a_drawn_settlement_is_ordinary_world_furniture(self) -> None:
        # Whatever reads the world reads it too: its board fills on the
        # first look, and conquest sees a legal holding in its own band.
        world = _world()
        rng = random.Random(9)
        area = quests.found_settlement(world, "gibili", rng,
                                       need="a rival center of power", day=6)
        posted = quests.refresh_settlement_board(world, area, 6, rng)
        self.assertTrue(posted)
        self.assertEqual(len(area["quests"]), quests.board_slots(area))
        lo, hi = conquest.GARRISON_BANDS[area["subtype"]]
        self.assertTrue(lo <= conquest.garrison_level(world, area) <= hi)
        clone = json.loads(json.dumps(world))
        self.assertEqual(clone["areas"][area["id"]], area)


class SeededAndStable(unittest.TestCase):
    """The trim keeps places.py's seed policy: same seed, same world."""

    def test_the_same_seed_opens_the_same_three(self) -> None:
        first, second = _world(881), _world(881)
        self.assertEqual(
            [a["name"] for a in first["areas"].values()],
            [a["name"] for a in second["areas"].values()])
        self.assertEqual(first["lands"], second["lands"])

    def test_another_seed_opens_another_three(self) -> None:
        # The opening draw is the variety: the town and village a land
        # begins with move between playthroughs.
        opening = lambda w: {s["name"] for s in quests.settlements(w)}
        self.assertNotEqual(opening(_world(881)), opening(_world(882)))

    def test_the_draw_is_seeded_not_ordered_by_chance(self) -> None:
        first, second = _world(881), _world(881)
        for polity in first["lands"]:
            a = places.materialize_settlement(first, polity, need="a rival")
            b = places.materialize_settlement(second, polity, need="a rival")
            if a is None:
                self.assertIsNone(b, polity)
                continue
            self.assertEqual(a["name"], b["name"], polity)
            self.assertEqual(a["seed"], b["seed"], polity)


if __name__ == "__main__":
    unittest.main()
