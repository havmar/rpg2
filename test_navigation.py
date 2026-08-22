"""GRID NAVIGATION AND MAP UI -- the contract suite (2026-08-15).

What this pins, in the order the build was specified:

*The edge*: every case of the symmetric cost rule (east/west one day,
north/south two, +1 for a mountain at EITHER end, nothing extra for river,
sea or a border crossing), reciprocity, the frame's hard limits and the
rejection of diagonals.

*The path*: deterministic shortest routes -- symmetric both ways, stable
across processes, reachable to every landmass because sea is navigable, and
never leaving the 18x30 frame. Representative distances are PINNED so a
change to the cost model cannot pass silently.

*The walk*: `travel DIRECTION` as the primitive, coordinates and known names
as convenience routes, the free step between Areas of one Tile, the
interrupted route that stays at the Tile it reached, and the sea passage
that spends days, weather and recovery but rolls no encounter.

*The surfaces*: teleport priced in real road days, and the map page --
overlay priority, the numeric axes, ASCII, and the 40-column rule.

`python -m unittest -v test_navigation.py`
"""

from __future__ import annotations

import argparse
import io
import random
import tempfile
import unittest
import unittest.mock
from contextlib import contextmanager, redirect_stdout
from pathlib import Path

import crime
import karma
import people
import places
import quests
import rpg
import session


DUBLIN = places.tile_id(5, 2)           # a two-Tile island off the west
PARIS = places.tile_id(9, 10)
ROME = places.tile_id(14, 14)
KYIV = places.tile_id(10, 27)
AMSTERDAM = places.tile_id(8, 11)       # river
PRAGUE = places.tile_id(9, 18)
ISLAND_11 = places.tile_id(3, 4)        # the eleven-Tile northern island
ISLET = places.tile_id(14, 10)          # the one-Tile island


def _world(seed: int = 4471) -> dict:
    return quests.generate_world(seed)


def _party(n: int = 2, level: int = 3) -> list:
    party = []
    for i in range(n):
        hero = people.make_character(random.Random(400 + i), level=level)
        hero.name = f"Hero{i}"
        hero.conditions = []
        party.append(hero)
    return party


def _state(world: dict, area: dict, day: int = 3) -> dict:
    return {"world": world, "party": _party(), "clock": rpg.Clock(day=day),
            "purse": rpg.Purse(silver=500), "rng": random.Random(4),
            "karma": karma.new_karma(), "crimes": crime.new_crimes(),
            "history": [], "position": session._area_position(area),
            "accepted": [], "active_quest": None, "loose_ends": [],
            "foe_count": 0, "pending": None, "rooms": {},
            "site_clears": {}, "holdings": {},
            "pact": None, "services": {}, "visited": [area["key"]]}


@contextmanager
def _save_sandbox():
    """Point session's save and its written pages at a throwaway directory
    -- a suite must never overwrite the playthrough."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "ui").mkdir()
        saved = (session.STATE_PATH, session.PARTY_SHEET_PATH,
                 session.MAP_SHEET_PATH, session.HISTORY_SHEET_PATH)
        session.STATE_PATH = root / "save.json"
        session.PARTY_SHEET_PATH = root / "ui" / "party.txt"
        session.MAP_SHEET_PATH = root / "ui" / "map.txt"
        session.HISTORY_SHEET_PATH = root / "ui" / "history.txt"
        try:
            yield root
        finally:
            (session.STATE_PATH, session.PARTY_SHEET_PATH,
             session.MAP_SHEET_PATH, session.HISTORY_SHEET_PATH) = saved


def _travel(state: dict, *words: str, interrupted: bool = False) -> str:
    """One `travel` command with the road's dice held still."""
    out = io.StringIO()
    with unittest.mock.patch("session.load", return_value=state), \
            unittest.mock.patch("session.wild_event",
                                return_value=interrupted), \
            redirect_stdout(out):
        session.cmd_travel(argparse.Namespace(dest=list(words)))
    return out.getvalue()


# =========================================================================== #
# THE EDGE
# =========================================================================== #

class TheEdgeCost(unittest.TestCase):
    """A tile is 30 km east-west and 60 north-south, so the compass costs
    what the ground does -- and a mountain at either end is symmetric, which
    is what makes the whole distance model symmetric."""

    def test_east_west_is_one_day_and_north_south_is_two(self) -> None:
        self.assertEqual(places.edge_days(places.tile_id(9, 10),
                                          places.tile_id(9, 11)), 1)
        self.assertEqual(places.edge_days(places.tile_id(9, 10),
                                          places.tile_id(10, 10)), 2)

    def test_a_mountain_at_either_end_adds_a_day_symmetrically(self) -> None:
        mountain = next(places.tile_id(row, column)
                        for row in range(1, places.MAP_ROWS + 1)
                        for column in range(1, places.MAP_COLUMNS + 1)
                        if places.biome_at(row, column) == "mountain"
                        and places.neighbor_id(places.tile_id(row, column),
                                               "east") is not None)
        east = places.neighbor_id(mountain, "east")
        base = (places.EDGE_DAYS_EAST_WEST
                + places.MOUNTAIN_EDGE_SURCHARGE)
        self.assertEqual(places.edge_days(mountain, east), base)
        self.assertEqual(places.edge_days(east, mountain), base)

    def test_two_mountains_still_add_only_one_day(self) -> None:
        pair = next(((places.tile_id(row, column),
                      places.tile_id(row, column + 1))
                     for row in range(1, places.MAP_ROWS + 1)
                     for column in range(1, places.MAP_COLUMNS)
                     if places.biome_at(row, column) == "mountain"
                     and places.biome_at(row, column + 1) == "mountain"))
        self.assertEqual(places.edge_days(*pair),
                         places.EDGE_DAYS_EAST_WEST
                         + places.MOUNTAIN_EDGE_SURCHARGE)

    def test_river_sea_and_borders_carry_no_surcharge(self) -> None:
        """River is ordinary inhabited land at this scale, sea is navigable
        water, and a border is a line on a map -- none of the three is a
        cost."""
        river = AMSTERDAM
        self.assertEqual(places.biome_at(*places.tile_row_column(river)),
                         "river")
        for direction in ("east", "west"):
            other = places.neighbor_id(river, direction)
            if other and places.biome_at(
                    *places.tile_row_column(other)) != "mountain":
                self.assertEqual(places.edge_days(river, other), 1)
        sea = next(places.tile_id(row, column)
                   for row in range(1, places.MAP_ROWS + 1)
                   for column in range(1, places.MAP_COLUMNS)
                   if places.biome_at(row, column) == "sea"
                   and places.biome_at(row, column + 1) == "sea")
        self.assertEqual(places.edge_days(
            sea, places.neighbor_id(sea, "east")), 1)
        # A country SEAM is wherever the authored overlay changes letter
        # (2026-08-21: not a column test any more -- there are nine of
        # them and the borders are drawn, not computed).
        border = places.tile_id(9, 11)      # Seraptania's eastern edge...
        beyond = places.tile_id(9, 12)      # ...and Teutonia's first tile
        self.assertNotEqual(places.country_at(9, 11),
                            places.country_at(9, 12))
        self.assertEqual(places.edge_days(border, beyond),
                         places.edge_days(beyond, border))

    def test_only_cardinal_neighbors_are_edges(self) -> None:
        with self.assertRaises(ValueError):     # diagonal
            places.edge_days(places.tile_id(9, 10), places.tile_id(10, 11))
        with self.assertRaises(ValueError):     # two steps
            places.edge_days(places.tile_id(9, 10), places.tile_id(9, 12))
        with self.assertRaises(ValueError):     # itself
            places.edge_days(PARIS, PARIS)

    def test_the_frame_is_the_end_of_the_world(self) -> None:
        self.assertIsNone(places.neighbor_id(places.tile_id(1, 1), "north"))
        self.assertIsNone(places.neighbor_id(places.tile_id(1, 1), "west"))
        self.assertIsNone(places.neighbor_id(
            places.tile_id(places.MAP_ROWS, places.MAP_COLUMNS), "south"))
        self.assertIsNone(places.neighbor_id(
            places.tile_id(places.MAP_ROWS, places.MAP_COLUMNS), "east"))
        with self.assertRaises(ValueError):
            places.tile_row_column("tile/r19/c01")
        with self.assertRaises(ValueError):
            places.tile_row_column("not a tile")

    def test_every_cardinal_link_is_reciprocal_and_none_is_diagonal(self
                                                                    ) -> None:
        world = _world()
        for tile in world["tiles"].values():
            for nid in tile["neighbors"]:
                other = world["tiles"][nid]
                step = (abs(other["row"] - tile["row"])
                        + abs(other["column"] - tile["column"]))
                self.assertEqual(step, 1, f"{tile['id']} -> {nid}")
                self.assertIn(tile["id"], other["neighbors"])


# =========================================================================== #
# THE PATH
# =========================================================================== #

class TheShortestPath(unittest.TestCase):

    def test_distance_is_symmetric_over_a_wide_sample(self) -> None:
        rng = random.Random(9)
        tiles = [places.tile_id(rng.randint(1, places.MAP_ROWS),
                                rng.randint(1, places.MAP_COLUMNS))
                 for _ in range(60)]
        for origin, dest in zip(tiles, tiles[1:]):
            self.assertEqual(places.path_days(origin, dest),
                             places.path_days(dest, origin), (origin, dest))

    def test_a_route_is_a_chain_of_real_edges_summing_to_its_cost(self
                                                                  ) -> None:
        for origin, dest in ((PARIS, KYIV), (ROME, DUBLIN),
                             (PRAGUE, ISLET)):
            route = places.shortest_path(origin, dest)
            self.assertEqual(route[0], origin)
            self.assertEqual(route[-1], dest)
            total = sum(places.edge_days(route[i], route[i + 1])
                        for i in range(len(route) - 1))
            self.assertEqual(total, places.path_days(origin, dest))

    def test_representative_distances_are_pinned(self) -> None:
        """The cost model in numbers. These move only when the rules do."""
        self.assertEqual(places.path_days(PARIS, PRAGUE), 8)     # two crowns
        self.assertEqual(places.path_days(ROME, KYIV), 21)       # two realms
        self.assertEqual(places.path_days(PARIS, ROME), 14)
        self.assertEqual(places.path_days(AMSTERDAM, PARIS), 3)  # river end
        self.assertEqual(places.path_days(PARIS, DUBLIN), 16)    # by sea

    def test_every_landmass_is_reachable_because_the_sea_is(self) -> None:
        """The eleven-tile island, the two-tile island Dublin stands on and
        the lone islet are all in the world, not beside it."""
        world = _world()
        start = world["areas"][world["start_area"]]["tile"]
        for island in (ISLAND_11, DUBLIN, ISLET):
            self.assertGreater(places.path_days(start, island), 0)
            route = places.shortest_path(start, island)
            self.assertTrue(any(world["tiles"][tid]["biome"] == "sea"
                                for tid in route)
                            or world["tiles"][start]["biome"] == "sea")

    def test_no_route_leaves_the_frame(self) -> None:
        for tid in places.shortest_path(places.tile_id(1, 1),
                                        places.tile_id(places.MAP_ROWS,
                                                       places.MAP_COLUMNS)):
            row, column = places.tile_row_column(tid)
            self.assertTrue(1 <= row <= places.MAP_ROWS)
            self.assertTrue(1 <= column <= places.MAP_COLUMNS)

    def test_the_search_is_deterministic_across_a_cold_cache(self) -> None:
        first = places.shortest_path(ROME, KYIV)
        places._PATHS.clear()
        self.assertEqual(places.shortest_path(ROME, KYIV), first)

    def test_a_country_is_crossable_within_itself(self) -> None:
        world = _world()
        for country in places.COUNTRIES:
            tiles = [tid for tid in world["lands"][country]["tiles"]
                     if world["tiles"][tid]["biome"] != "sea"]
            self.assertEqual(places.path_days(tiles[0], tiles[-1]),
                             places.path_days(tiles[-1], tiles[0]))


# =========================================================================== #
# THE WALK
# =========================================================================== #

class TheGridWalk(unittest.TestCase):

    def setUp(self) -> None:
        self.world = _world()
        self.start = self.world["areas"][self.world["start_area"]]
        self.state = _state(self.world, self.start)

    def test_a_direction_moves_exactly_one_edge_and_spends_its_days(self
                                                                    ) -> None:
        tile = self.world["tiles"][self.state["position"]["tile"]]
        direction = next(d for d in ("east", "west", "north", "south")
                         if places.neighbor_id(tile, d) is not None)
        nid = places.neighbor_id(tile, direction)
        day = self.state["clock"].day
        with _save_sandbox():
            _travel(self.state, direction)
        self.assertEqual(self.state["position"]["tile"], nid)
        self.assertGreaterEqual(self.state["clock"].day,
                                day + places.edge_days(tile, nid))
        # An ordinary leg lands in the Tile's natural Area, never inside a
        # settlement it happened to pass.
        self.assertEqual(self.state["position"]["area"],
                         self.world["tiles"][nid]["natural_area"])

    def test_the_frame_refuses_a_step_off_the_map(self) -> None:
        corner = self.world["areas"][
            self.world["tiles"][places.tile_id(1, 1)]["natural_area"]]
        state = _state(self.world, corner)
        with _save_sandbox():
            out = _travel(state, "north")
        self.assertIn("map ends", out)
        self.assertEqual(state["position"]["tile"], places.tile_id(1, 1))

    def test_a_coordinate_route_walks_every_edge_and_arrives(self) -> None:
        tile = self.state["position"]["tile"]
        dest = min((t for t in self.world["tiles"].values()
                    if places.path_days(tile, t["id"]) >= 4),
                   key=lambda t: places.path_days(tile, t["id"]))
        want = places.tile_coordinate(dest["row"], dest["column"])
        expected = places.path_days(tile, dest["id"])
        day = self.state["clock"].day
        with _save_sandbox():
            _travel(self.state, want)
        self.assertEqual(self.state["position"]["tile"], dest["id"])
        self.assertGreaterEqual(self.state["clock"].day, day + expected)

    def test_a_named_city_is_a_route_and_arrives_in_the_settlement(self
                                                                   ) -> None:
        state = _state(self.world,
                       self.world["areas"][
                           self.world["tiles"][PARIS]["natural_area"]])
        state["position"]["area"] = self.world["areas"][
            self.world["tiles"][PARIS]["natural_area"]]["key"]
        with _save_sandbox():
            _travel(state, "Prague")
        arrived = self.world["areas"][state["position"]["area"]]
        self.assertEqual(state["position"]["tile"], PRAGUE)
        self.assertEqual(arrived["kind"], "settlement")
        self.assertEqual(arrived["name"], "Prague")

    def test_a_whole_name_beats_a_place_that_merely_contains_it(self
                                                                ) -> None:
        """Substring matching is the convenience, not the rule: a Tile
        named for its own coordinate contains every shorter coordinate, so
        `travel R09C1` must not outrank an exact `R09C1x` -- and an exact
        city name must win outright."""
        state = _state(self.world,
                       self.world["areas"][
                           self.world["tiles"][PARIS]["natural_area"]])
        tile, area = session.travel_target(state, "Prague")
        self.assertEqual(tile["id"], PRAGUE)
        self.assertEqual(area["name"], "Prague")
        # the natural Area of R09C1 does not exist; R09C10 and R09C18 both
        # contain "R09C1", and the exact spelling must pick its own Tile.
        for want, expect in (("R09C10", PARIS), ("R09C18", PRAGUE)):
            tile, _ = session.travel_target(state, want)
            self.assertEqual(tile["id"], expect, want)

    def test_an_unknown_ordinary_settlement_is_not_a_destination(self
                                                                 ) -> None:
        hidden = next(slot for slot in self.world["settlement_slots"].values()
                      if not slot["known"] and slot["name"] is None)
        with _save_sandbox():
            out = _travel(self.state, "a place nobody has heard of")
        self.assertIn("No known place matches", out)
        self.assertIsNone(hidden["area"])

    def test_switching_areas_on_one_tile_costs_no_day(self) -> None:
        tile = self.world["tiles"][self.state["position"]["tile"]]
        natural = self.world["areas"][tile["natural_area"]]
        day = self.state["clock"].day
        with _save_sandbox():
            _travel(self.state, natural["name"])
        self.assertEqual(self.state["position"]["area"], natural["key"])
        self.assertEqual(self.state["clock"].day, day)

    def test_an_interrupted_route_keeps_the_ground_it_walked(self) -> None:
        """The contract the paid-crossing marker used to paper over: a
        fight stops the route AT THE TILE REACHED, never back at the
        settlement it set out from."""
        tile = self.state["position"]["tile"]
        far = max(self.world["tiles"].values(),
                  key=lambda t: places.path_days(tile, t["id"]))
        route = places.shortest_path(tile, far["id"])
        # The road roll fires on LAND legs only (a sea passage rolls no
        # encounter), so the fight stops the party at the first tile the
        # route reaches over a land edge.
        stop = next(route[i] for i in range(1, len(route))
                    if not session._sea_leg(self.world, route[i - 1],
                                            route[i]))
        with _save_sandbox():
            _travel(self.state, far["id"].replace("tile/r", "R")
                    .replace("/c", "C"), interrupted=True)
            session.save(self.state)
            reloaded = session.load()
        self.assertEqual(self.state["position"]["tile"], stop)
        self.assertNotEqual(self.state["position"]["area"],
                            self.start["key"])
        self.assertEqual(reloaded["position"]["tile"], stop)


class TheSeaPassage(unittest.TestCase):
    """Sea is navigable without ports, ships or inventory -- and the MVP has
    no naval combat, so a passage is weather, time and recovery only."""

    def setUp(self) -> None:
        self.world = _world()
        coast = next(t for t in self.world["tiles"].values()
                     if "coast" in t["tags"]
                     and any(self.world["tiles"][n]["biome"] == "sea"
                             for n in t["neighbors"]))
        self.sea = next(n for n in coast["neighbors"]
                        if self.world["tiles"][n]["biome"] == "sea")
        self.state = _state(self.world,
                            self.world["areas"][coast["natural_area"]])
        self.coast = coast

    def test_a_sea_leg_spends_days_and_rolls_no_encounter(self) -> None:
        day = self.state["clock"].day
        rolled: list = []
        out = io.StringIO()
        with _save_sandbox(), \
                unittest.mock.patch("session.load", return_value=self.state), \
                unittest.mock.patch(
                    "session.wild_event",
                    side_effect=lambda *a, **k: rolled.append(a) or False), \
                redirect_stdout(out):
            session.cmd_travel(argparse.Namespace(dest=[self.sea]))
        self.assertEqual(self.state["position"]["tile"], self.sea)
        self.assertEqual(self.state["clock"].day,
                         day + places.edge_days(self.coast, self.sea))
        self.assertEqual(rolled, [])            # no road table at sea

    def test_a_passage_pays_no_toll_and_waits_on_no_ford(self) -> None:
        """Both halves of the road's price are land. A ship does not queue
        at a bridge, so a sea leg asks `_road_costs` for nothing."""
        day = self.state["clock"].day
        silver = self.state["purse"].silver
        charged: list = []
        out = io.StringIO()
        with _save_sandbox(), \
                unittest.mock.patch("session.load", return_value=self.state), \
                unittest.mock.patch("worldsim.road_charges",
                                    side_effect=lambda *a, **k:
                                    charged.append(a) or (0, [])), \
                unittest.mock.patch("worldsim.travel_delay",
                                    side_effect=lambda *a, **k:
                                    charged.append(a) or (0, [])), \
                redirect_stdout(out):
            session.cmd_travel(argparse.Namespace(dest=[self.sea]))
        self.assertEqual(charged, [])           # neither half was consulted
        self.assertEqual(self.state["purse"].silver, silver)
        self.assertEqual(self.state["clock"].day,
                         day + places.edge_days(self.coast, self.sea))

    def test_the_sea_tile_is_a_real_place_with_a_natural_area(self) -> None:
        tile = self.world["tiles"][self.sea]
        self.assertEqual(tile["biome"], "sea")
        self.assertEqual(tile["settlement_slots"], [])
        self.assertIn(tile["natural_area"], self.world["areas"])

    def test_hunting_open_water_is_refused(self) -> None:
        state = _state(self.world,
                       self.world["areas"][
                           self.world["tiles"][self.sea]["natural_area"]])
        out = io.StringIO()
        with _save_sandbox(), \
                unittest.mock.patch("session.load", return_value=state), \
                redirect_stdout(out):
            session.cmd_hunt(argparse.Namespace())
        self.assertIn("open water", out.getvalue())


# =========================================================================== #
# THE SURFACES
# =========================================================================== #

class TeleportPays(unittest.TestCase):
    """Rank-3 travel skips the road; the Power pool is priced in the road it
    skipped, which since 2026-08-15 is the real shortest path."""

    def test_the_cost_is_the_actual_path_days(self) -> None:
        world = _world()
        here = world["areas"][f"{PARIS}/area/settlement/01"]
        there = world["areas"][f"{PRAGUE}/area/settlement/01"]
        state = _state(world, here)
        state["visited"] = [here["key"], there["key"]]
        hero = state["party"][0]
        hero.spells = {"teleport": 3}
        days = places.path_days(PARIS, PRAGUE)
        hero.cur_power = hero.max_power = (
            session.TELEPORT_TRAVEL_COST_PER_DAY * days) - 1
        log: list[str] = []
        out = io.StringIO()
        with redirect_stdout(out):
            session._cast_teleport(state, hero, "prague", log)
        self.assertIn(f"{days} road day(s)", out.getvalue())
        self.assertEqual(state["position"]["area"], here["key"])


class TheMapPage(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.world = _world()
        cls.state = _state(cls.world,
                           cls.world["areas"][cls.world["start_area"]])

    def test_the_grid_is_eighteen_rows_under_a_numeric_axis(self) -> None:
        lines = places.map_lines(self.world)
        self.assertEqual(len(lines), places.MAP_ROWS + 2)
        self.assertEqual(lines[1], "   " + "1234567890" * 3)
        for row, line in enumerate(lines[2:], 1):
            self.assertTrue(line.startswith(f"{row:02d} "))
            self.assertEqual(len(line) - 3, places.MAP_COLUMNS)

    def test_the_overlay_obeys_its_priority(self) -> None:
        world = self.world
        capital = world["tiles"][PARIS]
        city = world["tiles"][PRAGUE]        # authored CITY since 2026-08-21
        town = world["tiles"][DUBLIN]        # ...and Dublin an authored town
        empty = next(t for t in world["tiles"].values()
                     if t["biome"] == "sea")
        # 3/4: a known city-grade place beats a known town beats terrain.
        # `C` is the whole city grade -- capital, metropolis and city --
        # which is why Prague and Paris draw the same glyph.
        self.assertEqual(places.map_glyph(world, capital), "C")
        self.assertEqual(places.map_glyph(world, city), "C")
        self.assertEqual(places.map_glyph(world, town), "T")
        self.assertEqual(places.map_glyph(world, empty), ".")
        # 5: villages only where no town is known.
        village_tile = next(
            (t for t in world["tiles"].values()
             if places.known_slots(world, t)
             and all(slot["tier"] == "village"
                     for slot in places.known_slots(world, t))), None)
        if village_tile is not None:
            self.assertEqual(places.map_glyph(world, village_tile), "v")
        # ...and a Tile of nothing but HAMLETS is not drawn at all: the
        # 30x18 map is a country-scale picture.
        hamlets = next(
            (t for t in world["tiles"].values()
             if places.known_slots(world, t)
             and all(slot["tier"] == "hamlet"
                     for slot in places.known_slots(world, t))), None)
        if hamlets is not None:
            self.assertEqual(places.map_glyph(world, hamlets),
                             places.BIOME_LETTERS[hamlets["biome"]])
        # 2 then 1: the objective outranks the capital, the party outranks
        # everything.
        self.assertEqual(places.map_glyph(world, capital,
                                          objectives=[PARIS]), "!")
        self.assertEqual(places.map_glyph(world, capital, party=PARIS,
                                          objectives=[PARIS]), "@")

    def test_an_unknown_ordinary_settlement_never_shows(self) -> None:
        hidden = next(slot for slot in self.world["settlement_slots"].values()
                      if not slot["known"])
        tile = self.world["tiles"][hidden["tile"]]
        if not places.known_slots(self.world, tile):
            self.assertEqual(places.map_glyph(self.world, tile),
                             places.BIOME_LETTERS[tile["biome"]])

    def test_terrain_is_never_fogged(self) -> None:
        """Discovery governs settlements, not the continental outline."""
        rows = places.europe_grid()
        drawn = [line[3:] for line in places.map_lines(self.world)[2:]]
        for authored, shown in zip(rows, drawn):
            for glyph, cell in zip(authored, shown):
                self.assertIn(cell, (glyph, "C", "T", "v", "@", "!"))

    def test_every_page_line_is_ascii_and_fits_forty_columns(self) -> None:
        text = session._wrap_block("\n".join(
            session.map_sheet_lines(self.state)))
        for line in text.split("\n"):
            self.assertLessEqual(len(line), session.WRAP_WIDTH, line)
            self.assertTrue(line.isascii(), line)

    def test_the_page_names_the_tile_the_party_stands_on(self) -> None:
        lines = session.map_sheet_lines(self.state)
        tile = self.world["tiles"][self.state["position"]["tile"]]
        coordinate = places.tile_coordinate(tile["row"], tile["column"])
        self.assertTrue(any(coordinate in line for line in lines))


if __name__ == "__main__":
    unittest.main()
