"""The ground and the sky's contract suite (2026-08-21, the tile economy
arc's session 1).

Four parts. *The two overlays*: that they load onto every land Tile and no
sea Tile, that the words nature fixes sit on the high ground, the pinned
climate and terrain censuses, and the marsh five by name. *The law over
them*: the derived cover and tag censuses, the hand-authored exceptions
(the Po plain's alluvium, the eastern wildwood, the Danube's horse
country), one broken world per new `validate_world` clause, and the whole
layer's determinism -- it is authored, so two worlds off different seeds
carry the same ground. *The reconciliation*: the words a quest may ask for
are words a natural Area actually carries, natural Areas are named and
stocked by character, and settlements are fitted by it. *The sky*: the
season calendar, the weight rows, the day roll reading the ground the
party is standing on, the display re-key including the fen's fog, and the
drought threshold coming off the climate profile.
"""

from __future__ import annotations

import copy
import random
import unittest

import places
import quests
import worldsim


def _world(seed: int = 5) -> dict:
    return places.create_geography(seed)


def _land_tiles(world: dict) -> list[dict]:
    return [t for t in world["tiles"].values() if t["biome"] != "sea"]


# --------------------------------------------------------------------------- #
# A. The two authored overlays
# --------------------------------------------------------------------------- #

class TheOverlays(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.world = _world()

    def test_every_land_tile_is_painted_and_no_sea_tile_is(self) -> None:
        for tile in self.world["tiles"].values():
            if tile["biome"] == "sea":
                self.assertEqual(
                    (tile["climate"], tile["terrain"], tile["cover"]),
                    (None, None, None), tile["id"])
            else:
                self.assertIn(tile["climate"], places.CLIMATE_PROFILES,
                              tile["id"])
                self.assertIn(tile["terrain"], places.TERRAINS, tile["id"])
                self.assertIn(tile["cover"],
                              ("open", "wooded", "deep forest"), tile["id"])

    def test_alpine_and_mountains_are_exactly_the_high_ground(self) -> None:
        for tile in self.world["tiles"].values():
            high = tile["biome"] == "mountain"
            self.assertEqual(tile["climate"] == "alpine", high, tile["id"])
            self.assertEqual(tile["terrain"] == "mountains", high,
                             tile["id"])

    def test_the_pinned_climate_and_terrain_censuses(self) -> None:
        """The overlays are AUTHORED: a number that moves is a repaint
        somebody decided on, not drift."""
        climates, terrains = {}, {}
        for tile in _land_tiles(self.world):
            climates[tile["climate"]] = climates.get(tile["climate"], 0) + 1
            terrains[tile["terrain"]] = terrains.get(tile["terrain"], 0) + 1
        self.assertEqual(climates, places.PINNED_CLIMATE_COUNTS)
        self.assertEqual(terrains, places.PINNED_TERRAIN_COUNTS)
        self.assertEqual(sum(climates.values()), 314)

    def test_the_marsh_five_by_name(self) -> None:
        """Five hand-placed Tiles are content, not statistics."""
        marshes = {(t["row"], t["column"]): t["id"]
                   for t in _land_tiles(self.world)
                   if t["terrain"] == "marsh"}
        self.assertEqual(set(marshes), {(6, 6),      # the Fens
                                        (8, 11),     # the Low Countries
                                        (9, 23),     # the Pripet pair
                                        (9, 24),
                                        (11, 24)})   # the Danube delta
        self.assertEqual(set(marshes), set(places.PINNED_MARSHES))
        # Holland IS the marsh: the one marsh over a drawn river.
        self.assertEqual(
            self.world["tiles"]["tile/r08/c11"]["biome"], "river")

    def test_the_overlays_reject_a_bad_grid(self) -> None:
        for path in (places.CLIMATE_PATH, places.TERRAIN_PATH):
            self.assertEqual(
                len(places.load_overlay(path, places.CLIMATE_LETTERS
                                        if "climate" in path.name
                                        else places.TERRAIN_LETTERS)),
                places.MAP_ROWS)
        with self.assertRaises(ValueError):
            places.load_overlay(places.EUROPE_MAP_PATH,
                                places.CLIMATE_LETTERS)


# --------------------------------------------------------------------------- #
# B. The law over them
# --------------------------------------------------------------------------- #

class TheLandsPotential(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.world = _world()

    def test_the_pinned_cover_and_derived_tag_censuses(self) -> None:
        covers, tags = {}, {}
        for tile in _land_tiles(self.world):
            covers[tile["cover"]] = covers.get(tile["cover"], 0) + 1
            for tag in tile["tags"]:
                if tag in places.PINNED_TAG_COUNTS:
                    tags[tag] = tags.get(tag, 0) + 1
        self.assertEqual(covers, places.PINNED_COVER_COUNTS)
        self.assertEqual(tags, places.PINNED_TAG_COUNTS)

    def test_the_bare_biome_words_left_the_tag_vocabulary(self) -> None:
        """`basic` and `mountain` are map glyphs, not ground. What a land
        Tile now leads with is its terrain word."""
        for tile in _land_tiles(self.world):
            self.assertNotIn("basic", tile["tags"], tile["id"])
            self.assertNotIn("mountain", tile["tags"], tile["id"])
            self.assertEqual(tile["tags"][0], tile["terrain"], tile["id"])
            self.assertIn(tile["country"], tile["tags"], tile["id"])

    def test_deep_forest_stands_where_people_are_few(self) -> None:
        """Forest is DERIVED, not authored: the wildwood minus what the
        plough cleared. So the taiga north is deep forest and the Paris
        basin is not, without a line of authored woodland anywhere."""
        cover = {t["id"]: t["cover"] for t in _land_tiles(self.world)}
        self.assertEqual(cover["tile/r09/c10"], "open")        # Paris
        self.assertEqual(cover["tile/r03/c23"], "deep forest")  # Stockholm
        deep = [t for t in _land_tiles(self.world)
                if t["cover"] == "deep forest"]
        self.assertTrue(all("forest" in t["tags"] for t in deep))

    def test_the_hand_authored_exceptions_do_their_work(self) -> None:
        tiles = self.world["tiles"]
        # The Po plain: floodplain soils whose river the map redraw cut.
        po = places.tile_economy("wet_mediterranean", "plains", False, 12, 13)
        dry = places.tile_economy("wet_mediterranean", "plains", False, 12, 4)
        self.assertGreater(po["arable"], dry["arable"])
        # The eastern wildwood: cleared by the law, standing by hand.
        for row, column in places.HAND_FOREST:
            tile = tiles[places.tile_id(row, column)]
            self.assertEqual(tile["cover"], "deep forest", tile["id"])
        # The middle Danube's horse country.
        self.assertIn("pasture", tiles["tile/r11/c19"]["tags"])

    def test_the_latitude_gradient_is_clamped(self) -> None:
        base = places.CLIMATE_PROFILES["continental"]["ffd"]
        self.assertEqual(places.frost_free_days("continental", 8), base)
        self.assertEqual(places.frost_free_days("continental", 9), base + 8)
        self.assertEqual(places.frost_free_days("continental", 1),
                         base - places.FFD_SPREAD)
        # Alpine is altitude, not latitude, so it has no reference row.
        self.assertEqual(places.frost_free_days("alpine", 1),
                         places.frost_free_days("alpine", 18))

    def test_the_ground_is_the_same_in_every_campaign(self) -> None:
        """Two authored overlays and a law with no rng in it: the seed
        moves the people, never the land."""
        first, second = _world(1), _world(999)
        for tid, tile in first["tiles"].items():
            other = second["tiles"][tid]
            self.assertEqual(
                (tile["climate"], tile["terrain"], tile["cover"],
                 tile["tags"]),
                (other["climate"], other["terrain"], other["cover"],
                 other["tags"]), tid)

    def test_an_illegal_ground_raises_where_it_is_made(self) -> None:
        """One broken world per clause the ground session added."""
        def broken(mutate):
            world = copy.deepcopy(self.world)
            mutate(world)
            with self.assertRaises(ValueError):
                places.validate_world(world)

        def paint_the_sea(world):
            sea = next(t for t in world["tiles"].values()
                       if t["biome"] == "sea")
            sea["climate"] = "oceanic"

        def unpaint_the_land(world):
            world["tiles"]["tile/r09/c10"]["climate"] = None

        def invent_a_climate(world):
            world["tiles"]["tile/r09/c10"]["climate"] = "monsoon"

        def invent_a_terrain(world):
            world["tiles"]["tile/r09/c10"]["terrain"] = "badlands"

        def invent_a_cover(world):
            world["tiles"]["tile/r09/c10"]["cover"] = "jungle"

        def alpine_off_the_mountain(world):
            world["tiles"]["tile/r09/c10"]["climate"] = "alpine"

        def mountains_off_the_mountain(world):
            world["tiles"]["tile/r09/c10"]["terrain"] = "mountains"

        def move_the_census(world):
            tile = next(t for t in world["tiles"].values()
                        if t["climate"] == "oceanic")
            tile["climate"] = "continental"

        def drain_a_marsh(world):
            world["tiles"]["tile/r06/c06"]["terrain"] = "plains"

        def revive_the_bare_biome_word(world):
            world["tiles"]["tile/r09/c10"]["tags"].append("basic")

        def move_the_tag_census(world):
            tile = next(t for t in world["tiles"].values()
                        if "farmland" in t["tags"])
            tile["tags"].remove("farmland")

        def strand_the_party(world):
            world["party_tile"] = "tile/r99/c99"

        for mutate in (paint_the_sea, unpaint_the_land, invent_a_climate,
                       invent_a_terrain, invent_a_cover,
                       alpine_off_the_mountain, mountains_off_the_mountain,
                       move_the_census, drain_a_marsh,
                       revive_the_bare_biome_word, move_the_tag_census,
                       strand_the_party):
            with self.subTest(mutate.__name__):
                broken(mutate)


# --------------------------------------------------------------------------- #
# C. The quest-vocabulary reconciliation
# --------------------------------------------------------------------------- #

class TheReconciliation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.world = _world(3)

    def test_the_words_a_job_asks_for_are_words_the_ground_answers(self
                                                                   ) -> None:
        """Before the ground session `forest` / `hills` / `pasture` /
        `farmland` matched NO natural Area, so every such job fell back to
        the origin Tile's countryside. Each of them is now real ground."""
        carried = set()
        for tile in _land_tiles(self.world):
            carried.update(self.world["areas"][tile["natural_area"]]["tags"])
        for word in ("forest", "hills", "pasture", "farmland", "steppe",
                     "marsh", "mountains", "plains", "desert", "tundra"):
            self.assertIn(word, carried, word)
        self.assertNotIn("prairie", carried)

    def test_prairie_is_gone_from_the_quest_tables(self) -> None:
        asked = set()
        for requirement in quests.QUEST_PLACE_REQUIREMENTS.values():
            asked.update(requirement["area_any"])
        self.assertNotIn("prairie", asked)
        self.assertIn("steppe", asked)
        self.assertIn("marsh", asked)

    def test_a_den_job_lands_in_genuinely_wooded_ground(self) -> None:
        """The end-to-end read: the beast tables ask for woods, and the
        Area they route to is one the deforestation law left standing."""
        wanted = set(quests.QUEST_PLACE_REQUIREMENTS["Wolves Attack"]
                     ["area_any"])
        matches = [t for t in _land_tiles(self.world)
                   if wanted & set(t["tags"])]
        self.assertGreater(len(matches), 100)
        wooded = [t for t in matches if "forest" in t["tags"]]
        self.assertTrue(all(t["cover"] != "open" for t in wooded))
        self.assertGreaterEqual(len(wooded), 90)

    def test_a_steppe_job_lands_in_tergals_grass(self) -> None:
        steppe = [t for t in _land_tiles(self.world) if "steppe" in t["tags"]]
        self.assertEqual(len(steppe), 24)
        self.assertTrue(all(t["climate"] == "steppe" for t in steppe))

    def test_natural_areas_are_named_and_stocked_by_character(self) -> None:
        names, templates = {}, {}
        for tile in _land_tiles(self.world):
            area = self.world["areas"][tile["natural_area"]]
            character = places.natural_character(tile)
            self.assertTrue(
                area["name"].endswith(places.AREA_SUFFIXES[character]),
                f"{area['name']} / {character}")
            names.setdefault(character, area["name"])
            templates.setdefault(character, set()).add(area["template"])
            self.assertIn(area["template"], places.NATURAL_SITE_SPECS)
        # Every ground a Tile can be is actually on the map...
        self.assertEqual(set(names),
                         {"mountains", "river", "marsh", "forest", "hills",
                          "coast", "fields"})
        # ...and the fen is stocked out of the fen inventory, not the
        # country's default, which is the dead-inventory bug this fixed.
        fen = self.world["tiles"]["tile/r06/c06"]
        self.assertEqual(places.natural_character(fen), "marsh")
        self.assertEqual(
            self.world["areas"][fen["natural_area"]]["template"],
            "natural/firascir/fen")

    def test_every_authored_natural_inventory_is_drawn_from(self) -> None:
        """Dead authored content is the disease this session cut out."""
        drawn = {self.world["areas"][t["natural_area"]]["template"]
                 for t in self.world["tiles"].values()}
        for polity, land in places.LAND_SPECS.items():
            for key in land["natural_sites"]:
                self.assertIn(f"natural/{polity}/{key}", drawn,
                              f"{polity}/{key}")

    def test_a_settlement_can_be_fitted_by_character(self) -> None:
        """Position stopped being the only fit vocabulary: a hill town
        wants hills and a fen village wants the fen."""
        self.assertLessEqual(
            {"hills", "marsh", "forest", "farmland", "pasture", "steppe",
             "plains"}, set(places.TILE_FIT_TAGS))
        for retired in ("basic", "mountain", "sea"):
            self.assertNotIn(retired, places.TILE_FIT_TAGS)
        fits = places.LAND_SPECS["mortellaria"]["settlement_templates"]
        self.assertEqual(fits["hill_town"]["fits"], ["hills"])
        fen = places.LAND_SPECS["firascir"]["settlement_templates"][
            "fen_village"]
        self.assertEqual(fen["fits"], ["marsh"])
        # The fen village is reachable: the Fens carry `marsh`, so the
        # template is in the draw there and nowhere else.
        village = {role: set(spec["fits"])
                   for role, spec in places.LAND_SPECS["firascir"][
                       "settlement_templates"].items()
                   if spec["tier"] == "village"}
        fens = set(self.world["tiles"]["tile/r06/c06"]["tags"])
        paris = set(self.world["tiles"]["tile/r09/c10"]["tags"])
        self.assertIn("fen_village",
                      [r for r, f in village.items() if f <= fens])
        self.assertNotIn("fen_village",
                         [r for r, f in village.items() if f <= paris])
        # ...and a plain inland Tile still draws something: every tier
        # keeps a template that asks for nothing.
        slot = {"seed": 0, "capital": False}
        template, _sites = places._settlement_template(
            "firascir", "village", slot, paris)
        self.assertLessEqual(set(template["fits"]), paris)


# --------------------------------------------------------------------------- #
# D. The sky
# --------------------------------------------------------------------------- #

class TheSeasonCalendar(unittest.TestCase):
    def test_the_boundaries(self) -> None:
        """Day 1 is April 1st. A calendar, not a track: `season_of` is a
        lookup and nothing stores a season."""
        for day, season in ((1, "spring"), (60, "spring"), (61, "summer"),
                            (150, "summer"), (151, "autumn"),
                            (210, "autumn"), (211, "winter"),
                            (360, "winter"), (361, "spring"),
                            (420, "spring"), (421, "summer")):
            self.assertEqual(worldsim.season_of(day), season, day)

    def test_autumn_reuses_springs_weights(self) -> None:
        self.assertEqual(worldsim.SEASON_COLUMN["autumn"], "spring")
        self.assertEqual(sum(length for _n, length in worldsim.SEASONS),
                         worldsim.YEAR_DAYS)

    def test_every_weight_row_is_per_hundred_days(self) -> None:
        for climate, seasons in worldsim.CLIMATE_WEATHER.items():
            self.assertIn(climate, places.CLIMATE_PROFILES, climate)
            for column, weights in seasons.items():
                self.assertEqual(set(weights), set(worldsim.WEATHER_WORDS),
                                 f"{climate}/{column}")
                self.assertEqual(sum(weights.values()), 100,
                                 f"{climate}/{column}")
        for climate in places.CLIMATE_PROFILES:
            self.assertIn(climate, worldsim.CLIMATE_WEATHER, climate)


class TheDayRollReadsTheGround(unittest.TestCase):
    def setUp(self) -> None:
        self.world = quests.generate_world(11)

    def _stand(self, tid: str) -> dict:
        self.world["party_tile"] = tid
        return self.world["tiles"][tid]

    def test_the_weights_come_from_the_tile_underfoot(self) -> None:
        """A party in the south can roll a summer heat the taiga could not
        have given it that same day."""
        south = self._stand("tile/r14/c14")             # Rome
        self.assertEqual(south["country"], "mortellaria")
        hot = worldsim.weather_weights(self.world, "mortellaria", 100)
        north = self._stand("tile/r03/c23")             # Stockholm
        self.assertEqual(north["country"], "tergal")
        cold = worldsim.weather_weights(self.world, "tergal", 100)
        self.assertGreater(hot["heat"], cold.get("heat", 0))
        self.assertGreater(cold["rain"], hot["rain"])

    def test_the_season_moves_the_same_ground(self) -> None:
        self._stand("tile/r09/c18")                     # Prague
        spring = worldsim.weather_weights(self.world, "firascir", 10)
        winter = worldsim.weather_weights(self.world, "firascir", 300)
        self.assertGreater(winter.get("snow", 0), spring.get("snow", 0))
        self.assertGreater(spring["rain"], winter["rain"])

    def test_a_land_the_party_is_not_in_reads_its_capital(self) -> None:
        self._stand("tile/r14/c14")                     # Rome
        self.assertEqual(worldsim.sky_tile(self.world, "firascir")["id"],
                         places.CAPITAL_TILES["firascir"])
        self.assertEqual(worldsim.sky_tile(self.world, "mortellaria")["id"],
                         "tile/r14/c14")

    def test_the_open_sea_reads_the_capital_too(self) -> None:
        sea = next(t for t in self.world["tiles"].values()
                   if t["biome"] == "sea"
                   and t["country"] == "mortellaria")
        self._stand(sea["id"])
        self.assertEqual(worldsim.sky_tile(self.world, "mortellaria")["id"],
                         places.CAPITAL_TILES["mortellaria"])

    def test_the_roll_only_ever_says_a_legal_word(self) -> None:
        self._stand("tile/r17/c14")
        rng = random.Random(4)
        words = {worldsim.roll_weather(self.world, "mortellaria", day, rng)
                 for day in range(1, 400)}
        self.assertTrue(words <= set(worldsim.WEATHER_WORDS))

    def test_the_drought_threshold_comes_off_the_climate_profile(self
                                                                 ) -> None:
        """A fortnight without rain is a disaster in the wet north and an
        ordinary Tuesday in the dry south."""
        self._stand("tile/r17/c14")                     # the southern shore
        south = worldsim.drought_days(self.world, "mortellaria")
        self._stand("tile/r06/c05")                     # London
        north = worldsim.drought_days(self.world, "firascir")
        self.assertGreater(south, north)
        self.assertEqual(north, places.CLIMATE_PROFILES[
            self.world["tiles"]["tile/r06/c05"]["climate"]]["drought_days"])


class TheLocalWords(unittest.TestCase):
    def test_the_re_key_reads_climate_and_the_one_terrain_line(self
                                                               ) -> None:
        phrase = worldsim.weather_phrase
        self.assertEqual(phrase("alpine", "storm"), "a snowstorm")
        self.assertEqual(phrase("desert", "storm"), "a dust storm")
        self.assertEqual(phrase("nile", "storm"), "a dust storm")
        self.assertEqual(phrase("taiga", "rain"), "cold rain")
        self.assertEqual(phrase("tundra", "rain"), "cold rain")
        self.assertEqual(phrase("steppe", "wind"),
                         "a wind with no cover from it")
        self.assertEqual(phrase("mediterranean", "cloud"), "haze")
        # ...and the one line relief and not the sky picks: the fen's fog
        # beats whatever the climate would have called it.
        self.assertEqual(phrase("oceanic", "fog"), "fog on the ground")
        self.assertEqual(phrase("oceanic", "fog", "marsh"), "fen fog")
        self.assertEqual(phrase("oceanic", "rain", "marsh"), "steady rain")

    def test_the_line_the_party_reads_is_its_own_grounds(self) -> None:
        world = quests.generate_world(12)
        world["party_tile"] = "tile/r08/c11"            # the Low Countries
        worldsim.roll_world(world, 4)
        worldsim.land_layer(world, "firascir")["weather"] = "fog"
        self.assertIn("fen fog", worldsim.weather_line(world, "firascir"))
        world["party_tile"] = "tile/r06/c05"            # London
        self.assertIn("fog on the ground",
                      worldsim.weather_line(world, "firascir"))


if __name__ == "__main__":
    unittest.main()
