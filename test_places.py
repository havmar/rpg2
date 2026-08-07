"""Verification for the place-generation MVP contract."""

from __future__ import annotations

import copy
import json
import random
import unittest

import karma
import places
import quests
import session


# Natural Areas, then the OPENING settlement census per land: capital plus
# towns, and villages (2026-08-07, the settlement trim -- a land begins with
# three settlements and grows on need; everything else is the reserve pool,
# see test_worldsim.py).
EXPECTED = {
    "dvarvengrond": (3, 3, 0),      # the dwarves author no village at all
    "firascir": (4, 2, 1),
    "mortellaria": (5, 2, 1),
    "ensimaa": (5, 2, 1),
    "gibili": (5, 2, 1),
    "tergal": (6, 2, 1),
}


class PlaceGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.world = quests.generate_world(73025)

    def test_required_land_and_area_counts(self) -> None:
        self.assertEqual(list(self.world["lands"]), list(EXPECTED))
        for polity, (natural, standing, villages) in EXPECTED.items():
            areas = [self.world["areas"][aid]
                     for aid in self.world["lands"][polity]["areas"]]
            self.assertEqual(sum(a["kind"] == "natural" for a in areas),
                             natural)
            settlements = [a for a in areas
                           if a["kind"] == "settlement"]
            self.assertEqual(len(settlements),
                             places.SETTLEMENTS_AT_WORLDGEN, polity)
            self.assertEqual(sum(a["subtype"] != "village"
                                 for a in settlements), standing)
            self.assertEqual(sum(a["subtype"] == "village"
                                 for a in settlements), villages)

    def test_ids_and_generated_village_names_are_unique(self) -> None:
        ids = []
        for store in ("lands", "areas", "sites", "rooms"):
            ids.extend(record["id"] for record in self.world[store].values())
        self.assertEqual(len(ids), len(set(ids)))
        names = [a["name"] for a in self.world["areas"].values()
                 if a["source"] == "worldgen"]
        self.assertEqual(len(names), len(set(names)))

    def test_seed_is_stable_and_changes_variable_structure(self) -> None:
        again = quests.generate_world(73025)
        other = quests.generate_world(73026)
        self.assertEqual(self.world, again)
        villages = lambda w: [a["name"] for a in w["areas"].values()
                              if a["source"] == "worldgen"]
        orders = lambda w: [a["natural_site_order"]
                            for a in w["areas"].values()
                            if a["kind"] == "natural"]
        self.assertTrue(villages(self.world) != villages(other)
                        or orders(self.world) != orders(other))

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
        area = world["areas"]["area/firascir/whitweld-forest"]
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
            if area["subtype"] == "capital":
                self.assertTrue(
                    {"alchemist", "market", "government"} <= kinds,
                    area["name"])
        self.assertTrue(world["rooms"])
        for room in world["rooms"].values():
            self.assertTrue(room["contents"], room["id"])

    def test_transit_and_sea_routes_are_not_land_borders(self) -> None:
        world = places.create_geography(130)
        firascir = world["lands"]["firascir"]["links"]
        mortellaria = world["lands"]["mortellaria"]["links"]
        self.assertIn(("tergal", "transit"),
                      {(link["target"], link["kind"]) for link in firascir})
        self.assertNotIn(("tergal", "border"),
                         {(link["target"], link["kind"]) for link in firascir})
        self.assertIn(("gibili", "sea_route"),
                      {(link["target"], link["kind"])
                       for link in mortellaria})
        self.assertNotIn(("gibili", "border"),
                         {(link["target"], link["kind"])
                          for link in mortellaria})

    def test_house_contents_and_culture_restrictions(self) -> None:
        world = quests.generate_world(14)
        for area in quests.settlements(world):
            site, resident = places.materialize_house(world, area)
            self.assertEqual(resident["race"], area["race"])
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
        for race, templates in quests.TEMPLATES.items():
            origin = next(s for s in quests.settlements(world)
                          if s["race"] == race)
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

    def test_quest_state_transition_preserves_site(self) -> None:
        world = places.create_geography(16)
        origin = next(s for s in quests.settlements(world)
                      if s["race"] == "elf")
        template = next(t for t in quests.TEMPLATES["elf"]
                        if t["title"] == "The Blighted Grove")
        quest = quests.build_quest(
            world, "vertical", template, origin["id"], 3, random.Random(2))
        site_ids = list(quest["sites"])
        target = world["areas"][quest["target_area"]]
        self.assertEqual(
            [s["id"] for s in places.active_known_facts(target)],
            ["blighted"])
        quests.complete_quest_place_state(world, quest, day=7)
        self.assertEqual(
            [s["id"] for s in places.active_known_facts(target)],
            ["recovering"])
        self.assertTrue(all(sid in world["sites"] for sid in site_ids))
        places.clear_state(world, target, "recovering", day=8)
        self.assertFalse(places.active_known_facts(target))

    def test_completed_public_site_can_be_reused(self) -> None:
        world = places.create_geography(17)
        origin = next(s for s in quests.settlements(world)
                      if s["race"] == "human")
        template = next(t for t in quests.TEMPLATES["human"]
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
            self.world["areas"]["area/firascir/whitweld-forest"])
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


if __name__ == "__main__":
    unittest.main()
