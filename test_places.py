"""Verification for fixed Europe geography and procedural places."""

from __future__ import annotations

import copy
import json
import random
import re
import unittest

import karma
import people
import places
import quests
import rpg
import session
import story
import worldsim


EXPECTED_COUNTRY_BIOMES = places.PINNED_COUNTRY_BIOMES
EXPECTED_HISTORICAL_CITIES = (
    (5, 2, "Dublin", "firascir", "basic", False),
    (6, 5, "London", "firascir", "basic", False),
    (8, 12, "Amsterdam", "firascir", "river", False),
    (9, 10, "Paris", "firascir", "basic", True),
    (9, 18, "Prague", "firascir", "basic", False),
    (3, 23, "Stockholm", "tergal", "basic", False),
    (7, 28, "Moscow", "tergal", "basic", False),
    (8, 22, "Warsaw", "tergal", "basic", False),
    (10, 27, "Kyiv", "tergal", "river", True),
    (13, 3, "Lisbon", "mortellaria", "river", False),
    (13, 7, "Madrid", "mortellaria", "basic", False),
    (12, 14, "Venice", "mortellaria", "river", False),
    (14, 14, "Rome", "mortellaria", "basic", True),
    (14, 19, "Athens", "mortellaria", "basic", False),
    (14, 27, "Constantinople", "mortellaria", "basic", False),
    (17, 12, "Carthage", "mortellaria", "basic", False),
)


class PlaceGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.world = quests.generate_world(73025)

    def test_fixed_map_census_and_country_partition(self) -> None:
        rows = places.load_europe_map()
        self.assertEqual((len(rows), {len(row) for row in rows}), (18, {30}))
        counts = {biome: 0 for biome in places.PINNED_BIOME_COUNTS}
        country_counts = {
            country: {biome: 0 for biome in ("basic", "mountain", "river")}
            for country in EXPECTED_COUNTRY_BIOMES}
        for tile in self.world["tiles"].values():
            counts[tile["biome"]] += 1
            if tile["biome"] != "sea":
                country_counts[tile["country"]][tile["biome"]] += 1
        self.assertEqual(counts, places.PINNED_BIOME_COUNTS)
        self.assertEqual(country_counts, EXPECTED_COUNTRY_BIOMES)
        self.assertEqual(
            tuple(len(c) for c in places._land_components(rows)),
            places.PINNED_LAND_COMPONENTS)

    def test_map_validation_identifies_bad_row_and_column(self) -> None:
        class Source:
            def __init__(self, text: str):
                self.text = text

            def read_text(self, **_kwargs) -> str:
                return self.text

            def __str__(self) -> str:
                return "test-map"

        rows = list(places.load_europe_map())
        rows[6] = rows[6][:10] + "?" + rows[6][11:]
        with self.assertRaisesRegex(ValueError, r"row 7, column 11"):
            places.load_europe_map(Source("\n".join(rows)))
        rows[6] = rows[6][:-1]
        with self.assertRaisesRegex(ValueError, r"row 7 .*29 columns"):
            places.load_europe_map(Source("\n".join(rows)))

    def test_every_tile_has_one_natural_area_and_cardinal_neighbors(self) -> None:
        self.assertEqual(len(self.world["tiles"]), 540)
        naturals = [a for a in self.world["areas"].values()
                    if a["kind"] == "natural"]
        self.assertEqual(len(naturals), 540)
        for tid in self.world["tile_order"]:
            tile = self.world["tiles"][tid]
            self.assertEqual(tile["areas"][0], tile["natural_area"])
            natural = self.world["areas"][tile["natural_area"]]
            self.assertEqual(natural["tile"], tid)
            for neighbor_id in tile["neighbors"]:
                neighbor = self.world["tiles"][neighbor_id]
                self.assertIn(tid, neighbor["neighbors"])
                self.assertEqual(
                    abs(tile["row"] - neighbor["row"])
                    + abs(tile["column"] - neighbor["column"]), 1)

    def test_historical_city_overlay_and_capitals(self) -> None:
        self.assertEqual(places.HISTORICAL_CITIES,
                         EXPECTED_HISTORICAL_CITIES)
        actual = []
        for row, column, name, country, biome, capital in places.HISTORICAL_CITIES:
            tile = self.world["tiles"][places.tile_id(row, column)]
            self.assertEqual((tile["name"], tile["country"], tile["biome"]),
                             (name, country, biome))
            slots = [self.world["settlement_slots"][sid]
                     for sid in tile["settlement_slots"]]
            self.assertEqual([slot["tier"] for slot in slots],
                             ["town", "village", "village"])
            if not tile["visited"]:
                self.assertEqual([slot["area"] is not None for slot in slots],
                                 [True, False, False])
            town = next(self.world["areas"][self.world["settlement_slots"][sid]["area"]]
                        for sid in tile["settlement_slots"]
                        if self.world["settlement_slots"][sid]["authored"])
            self.assertEqual((town["name"], town["subtype"], town["capital"]),
                             (name, "town", capital))
            self.assertTrue(town["known"])
            actual.append(town)
        self.assertEqual({a["name"] for a in actual if a["capital"]},
                         {"Paris", "Rome", "Kyiv"})

    def test_population_constraints(self) -> None:
        self.assertEqual(places.SETTLEMENT_DENSITY, {
            "mortellaria": (0.10, 0.35),
            "firascir": (0.06, 0.24),
            "tergal": (0.03, 0.17),
        })
        for tile in self.world["tiles"].values():
            slots = [self.world["settlement_slots"][sid]
                     for sid in tile["settlement_slots"]]
            if tile["biome"] == "sea":
                self.assertEqual(slots, [])
            if (tile["biome"] == "mountain"
                    and (tile["row"], tile["column"])
                    not in places.HISTORICAL_BY_TILE):
                self.assertNotIn("town", {slot["tier"] for slot in slots})

    def test_ids_and_generated_village_names_are_unique(self) -> None:
        ids = []
        for store in ("lands", "areas", "sites", "rooms"):
            ids.extend(record["id"] for record in self.world[store].values())
        self.assertEqual(len(ids), len(set(ids)))
        for area in self.world["areas"].values():
            self.assertTrue(area["id"].startswith(f"{area['tile']}/area/"))
        for site in self.world["sites"].values():
            self.assertTrue(site["id"].startswith(f"{site['area']}/"))
        for room in self.world["rooms"].values():
            self.assertTrue(room["id"].startswith(f"{room['site']}/"))
        names = [a["name"] for a in self.world["areas"].values()
                 if a["source"] == "worldgen"]
        self.assertEqual(len(names), len(set(names)))

    def test_seed_is_stable_and_changes_only_variable_structure(self) -> None:
        again = quests.generate_world(73025)
        other = quests.generate_world(73026)
        self.assertEqual(self.world, again)
        terrain = lambda w: [(t["id"], t["biome"], t["country"], t["name"])
                             for t in w["tiles"].values()]
        population = lambda w: [(t["id"], tuple(
            w["settlement_slots"][sid]["tier"]
            for sid in t["settlement_slots"])) for t in w["tiles"].values()]
        self.assertEqual(terrain(self.world), terrain(other))
        self.assertNotEqual((population(self.world), self.world["start_slot"]),
                            (population(other), other["start_slot"]))

    def test_discovery_reveals_existing_area(self) -> None:
        world = places.create_geography(11)
        before = set(world["areas"])
        found = places.discover_area(world, "firascir", day=2)
        self.assertIsNotNone(found)
        self.assertEqual(before, set(world["areas"]))
        self.assertTrue(found["known"])
        self.assertEqual(found["discovered_day"], 2)

    def test_natural_area_yields_three_distinct_persistent_sites(self) -> None:
        world = places.create_geography(12)
        area = world["areas"]["tile/r05/c02/area/natural"]
        area["known"] = True
        sites = [places.materialize_natural_site(world, area, day=i)
                 for i in range(1, 4)]
        self.assertEqual(len({s["template"] for s in sites}), 3)
        self.assertIsNone(places.materialize_natural_site(world, area, day=4))
        snapshot = json.loads(json.dumps(world))
        self.assertEqual(snapshot, world)
        self.assertEqual(
            [world["rooms"][rid]["contents"]
             for site in sites for rid in site["rooms"]],
            [snapshot["rooms"][rid]["contents"]
             for site in sites for rid in site["rooms"]])

    def test_required_services_and_room_definitions(self) -> None:
        world = places.create_geography(13)
        for area in quests.settlements(world):
            kinds = {service["kind"] for service in area["services"]}
            self.assertTrue({"lodging", "smith", "general_goods"} <= kinds,
                            area["name"])
            if area["capital"]:
                self.assertTrue(
                    {"alchemist", "market", "government"} <= kinds,
                    area["name"])
        self.assertTrue(world["rooms"])
        for room in world["rooms"].values():
            self.assertTrue(room["contents"], room["id"])

    def test_catalog_no_longer_owns_world_adjacency(self) -> None:
        self.assertFalse({"land_order", "adjacency", "travel_links",
                          "water_links"}.intersection(places._CATALOG))
        self.assertFalse({"links", "water_links"}.intersection(self.world))
        for country in self.world["lands"].values():
            self.assertFalse({"neighbors", "links"}.intersection(country))

    def test_name_exhaustion_is_persisted_per_country_and_tier(self) -> None:
        world = places.create_geography(131)
        for country in places.COUNTRIES:
            for tier in ("town", "village"):
                world["name_reserves"][country][tier].clear()
                first = places._next_settlement_name(world, country, tier)
                second = places._next_settlement_name(world, country, tier)
                label = world["lands"][country]["name"]
                self.assertEqual(first, f"{label} {tier.title()} 1")
                self.assertEqual(second, f"{label} {tier.title()} 2")

    def test_start_is_a_slot_and_seed_sweep_reaches_countries_and_tiers(self) -> None:
        countries, tiers = set(), set()
        for seed in range(90):
            world = places.create_geography(seed)
            slot = world["settlement_slots"][world["start_slot"]]
            self.assertEqual(slot["area"], world["start_area"])
            countries.add(world["tiles"][slot["tile"]]["country"])
            tiers.add(slot["tier"])
        self.assertEqual(countries, set(places.COUNTRIES))
        self.assertEqual(tiers, {"town", "village"})

    def test_materialization_and_revisit_do_not_change_census_or_names(self) -> None:
        world = places.create_geography(132)
        target = next(t for t in world["tiles"].values()
                      if t["settlement_slots"] and not t["visited"])
        census = {tid: tuple(tile["settlement_slots"])
                  for tid, tile in world["tiles"].items()}
        first = places.reveal_tile(world, target, day=3)
        names = [area["name"] for area in first]
        snapshot = json.loads(json.dumps(world))
        second = places.reveal_tile(snapshot, target["id"], day=9)
        self.assertEqual(census, {tid: tuple(tile["settlement_slots"])
                                  for tid, tile in snapshot["tiles"].items()})
        self.assertEqual(names, [area["name"] for area in second])

    def test_house_contents_and_culture_restrictions(self) -> None:
        world = quests.generate_world(14)
        for area in quests.settlements(world):
            site, resident = places.materialize_house(world, area)
            self.assertEqual(resident["homeland"], area["homeland"])
            self.assertGreaterEqual(len(site["rooms"]), 1)
            self.assertLessEqual(len(site["rooms"]), 3)
            main = world["rooms"][site["rooms"][0]]
            visible = [item for item in main["contents"]
                       if item["reveal"] == "visible"]
            self.assertGreaterEqual(len(visible), 2)
            self.assertLessEqual(len(visible), 5)
            labels = [item["label"] for item in main["contents"]]
            self.assertEqual(len(labels), len(set(labels)))
            hidden = [item for rid in site["rooms"]
                      for item in world["rooms"][rid]["contents"]
                      if item["reveal"] != "visible"]
            self.assertLessEqual(len(hidden), 1)

    def test_every_quest_family_routes_to_compatible_geography(self) -> None:
        world = places.create_geography(15)
        n = 0
        for homeland, templates in quests.TEMPLATES.items():
            origin = next(s for s in quests.settlements(world)
                          if s["homeland"] == homeland)
            for template in templates:
                n += 1
                level = quests.template_band(template)[0]
                quest = quests.build_quest(
                    world, f"verify-{n}", template, origin["id"], level,
                    random.Random(n))
                target = world["areas"][quest["target_area"]]
                self.assertTrue(
                    set(quest["place"]["area_any"]).intersection(
                        target["tags"]),
                    template["title"])
                self.assertTrue(quest["sites"])

    def test_completed_public_site_can_be_reused(self) -> None:
        world = places.create_geography(17)
        origin = next(s for s in quests.settlements(world)
                      if s["homeland"] == "firascir")
        template = next(t for t in quests.TEMPLATES["firascir"]
                        if t["title"] == "The Restless Crypt")
        first = quests.build_quest(
            world, "reuse-1", template, origin["id"], 3, random.Random(1))
        world["quests"][first["id"]] = first
        first["status"] = "done"
        second = quests.build_quest(
            world, "reuse-2", template, origin["id"], 3, random.Random(1))
        if first["target_area"] == second["target_area"]:
            self.assertTrue(set(first["sites"]).intersection(second["sites"]))

    def test_pruned_assignment_does_not_overwrite_its_place(self) -> None:
        world = places.create_geography(18)
        origin = quests.settlements(world)[0]
        first = karma.roll_dark_quest(
            world, origin, 3, random.Random(1), spread=(0, 0))
        first_sites = list(first["sites"])
        del world["quests"][first["id"]]
        second = karma.roll_dark_quest(
            world, origin, 3, random.Random(2), spread=(0, 0))
        self.assertNotEqual(first["id"], second["id"])
        self.assertTrue(all(sid in world["sites"] for sid in first_sites))

    def test_every_occult_template_routes_to_compatible_geography(self) -> None:
        """The occult ten are the ONLY templates a pact assignment draws
        from (2026-08-04), so each one has to find geography it fits at
        the bottom of its own band -- the honest tables' contract, applied
        to hell's deck."""
        world = places.create_geography(19)
        origin = quests.settlements(world)[0]
        for n, template in enumerate(karma.OCCULT_TEMPLATES):
            level = quests.template_band(template)[0]
            quest = quests.build_quest(
                world, f"occult-{n}", template, origin["id"], level,
                random.Random(n))
            target = world["areas"][quest["target_area"]]
            self.assertTrue(
                set(quest["place"]["area_any"]).intersection(target["tags"]),
                template["title"])
            self.assertTrue(quest["sites"], template["title"])

    def test_hidden_facts_stay_out_of_player_fact_selection(self) -> None:
        place = copy.deepcopy(
            next(a for a in self.world["areas"].values()
                 if a["kind"] == "natural"))
        place["features"].append({
            "id": "sealed_crypt", "reveal": "hidden",
            "known": False, "active": True,
        })
        self.assertNotIn("sealed_crypt",
                         [f["id"] for f in places.active_known_facts(place)])

    def test_generated_display_text_is_ascii_and_wraps(self) -> None:
        strings = []
        for store in ("lands", "areas", "sites", "rooms"):
            for record in self.world[store].values():
                strings.extend(value for value in (
                    record.get("name"), record.get("description"))
                               if value)
                strings.extend(item["label"]
                               for item in record.get("contents", ()))
        for value in strings:
            value.encode("ascii")
            wrapped = session._wrap_block(value)
            self.assertTrue(all(len(line) <= session.WRAP_WIDTH
                                for line in wrapped.splitlines()))


class HumanWorldContractionTests(unittest.TestCase):
    HOMELANDS = {"firascir", "mortellaria", "tergal"}
    REMOVED = re.compile(
        r"\b(?:elf|elves|elven|dwarf|dwarves|dwarven|goblin|goblins|"
        r"orc|orcs|orcen|ensimaa|dvarvengrond|gibili|middenland)\b",
        re.IGNORECASE)

    @staticmethod
    def _walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                yield key
                yield from HumanWorldContractionTests._walk(item)
        elif isinstance(value, (list, tuple, set)):
            for item in value:
                yield from HumanWorldContractionTests._walk(item)
        elif isinstance(value, str):
            yield value

    def test_only_three_human_homelands_exist(self) -> None:
        self.assertEqual(set(places.LAND_SPECS), self.HOMELANDS)
        self.assertEqual(set(quests.HOMELANDS), self.HOMELANDS)
        self.assertEqual(set(people.NAMES), self.HOMELANDS)
        self.assertEqual(set(story.CONQUESTS), self.HOMELANDS)
        self.assertEqual(set(story.AGGRESSORS), self.HOMELANDS)

    def test_runtime_records_use_homeland_and_never_race(self) -> None:
        for seed in range(8):
            world = quests.generate_world(seed)
            for value in self._walk(world):
                self.assertNotEqual(value, "race")
            for store in (world["lands"], world["areas"]):
                for record in store.values():
                    self.assertIn(record["homeland"], self.HOMELANDS)
            for settlement in quests.settlements(world):
                for service in settlement["services"]:
                    provider = next(npc for npc in world["npcs"]
                                    if npc["id"] == service["provider"])
                    self.assertIn(provider["homeland"],
                                  self.HOMELANDS)
            for quest in world["quests"].values():
                self.assertIn(quest["giver"]["homeland"], self.HOMELANDS)

    def test_active_catalogs_name_no_removed_people_or_realms(self) -> None:
        active = (
            places._CATALOG,
            quests.TEMPLATES,
            story.CONQUESTS,
            worldsim.CARDS,
            worldsim.RELATIONS,
            worldsim.FACTS,
            worldsim.OPTIONS,
            worldsim.CONSTITUTIONS,
            worldsim.TENSIONS,
            worldsim.STATE_MENU,
            worldsim.STATE_ENCOUNTERS,
            worldsim.STATE_MARKS,
            [weapon.description for weapon in rpg.WEAPONS.values()],
        )
        offenders = sorted({text for text in self._walk(active)
                            if self.REMOVED.search(text)})
        self.assertEqual(offenders, [])

    def test_every_story_variant_builds_all_four_waves(self) -> None:
        for n, aggressor in enumerate(story.AGGRESSORS):
            rng = random.Random(9000 + n)
            world = quests.generate_world(9100 + n)
            campaign = story.init_story(world, rng, aggressor=aggressor)
            self.assertEqual(campaign["aggressor"], aggressor)
            self.assertEqual(campaign["conqueror"]["homeland"], aggressor)
            for _ in story.WAVE_LEVELS:
                quest, lines = story.post_wave(world, campaign, rng, day=1)
                self.assertTrue(lines)
                self.assertFalse(self.REMOVED.search(" ".join(
                    self._walk(quest))))
            self.assertEqual(campaign["wave_posted"], 4)


if __name__ == "__main__":
    unittest.main()
