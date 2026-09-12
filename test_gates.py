"""THE GATES -- the contract suite (2026-09-12, the gates arc's session 1).

Six parts, in the order the session built them:

*The placement*: every clause of the eligibility rule over a sweep of
worlds -- the sets, the authored tiles, the capitals and their ring, the
mines, the four-tile separation, the live city's land neighbour -- plus the
weighted preference actually showing and an empty candidate set raising.

*The record and the ring*: `world["gates"]` in exactly the spec's shape,
the four tile tags, and the permanent ring of `gate-ruin` / `gate-city`
states with their side in `by`.

*The ruins*: two Areas of the third kind with their tags, their six
authored Sites at the authored levels, rosters built at worldgen off the
side's pool, determinism per seed, and Candor's stranded angel.

*The foes*: the two skin tables against the catalog, the disposition beside
the names, the warden blade, and the four pools.

*The ring's encounters*: the tile encounter table against the pools, a tile
entry outranking a land entry in `wild_event`, and the danger ring
multiplying the road, the day afield and the night camped.

*The delve*: forging over authored rooms, the field tranche and no
turn-in, the thirty-day refill, and the deepest Site sealing the ruin.

`python -m unittest -v test_gates.py`
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import random
import unittest
import unittest.mock
from contextlib import redirect_stdout

import crime
import karma
import people
import places
import quests
import rpg
import session
import sites
import worldsim

SWEEP = 40              # worlds the placement clauses sweep (60ms each);
                        # bench_worldgen.py --only gates runs 200.

_CACHE: dict[int, dict] = {}


def world(seed: int) -> dict:
    """The built ground. Cheap: nothing in this suite but the explore roll
    needs a world LAYER under it, and that one asks `played` instead."""
    if seed not in _CACHE:
        _CACHE[seed] = places.create_geography(seed)
    return copy.deepcopy(_CACHE[seed])


_PLAYED: dict[int, dict] = {}


def played(seed: int) -> dict:
    """A world with its layer opened and its boards posted -- what a command
    that reads the sky (weather, the day roll) needs under it."""
    if seed not in _PLAYED:
        _PLAYED[seed] = quests.generate_world(seed)
    return copy.deepcopy(_PLAYED[seed])


def _party(n: int = 2, level: int = 3) -> list:
    party = []
    for i in range(n):
        hero = people.make_character(random.Random(900 + i), level=level)
        hero.name = f"Hero{i}"
        hero.conditions = []
        party.append(hero)
    return party


def _state(built: dict, area: dict, day: int = 3, level: int = 3) -> dict:
    return {"world": built, "party": _party(level=level),
            "clock": rpg.Clock(day=day),
            "purse": rpg.Purse(silver=500), "rng": random.Random(11),
            "karma": karma.new_karma(), "crimes": crime.new_crimes(),
            "history": [], "position": session._area_position(area),
            "accepted": [], "active_quest": None, "loose_ends": [],
            "foe_count": 0, "pending": None, "rooms": {},
            "site_clears": {}, "holdings": {},
            "pact": None, "services": {}, "visited": [area["key"]]}


def _run(state: dict, func, args: argparse.Namespace) -> str:
    out = io.StringIO()
    with unittest.mock.patch("session.load", return_value=state), \
            unittest.mock.patch("session.save"), redirect_stdout(out):
        func(args)
    return out.getvalue()


# =========================================================================== #
# THE PLACEMENT
# =========================================================================== #

class ThePlacementRule(unittest.TestCase):
    """gates.md section 5, clause by clause. The rule is enforced inside
    `create_geography` (`places._validate_gates` raises), so what these add
    is the sweep: it held in every world, not only in the one built here."""

    def test_the_four_are_the_four_in_roll_order(self):
        self.assertEqual(places.GATE_KEYS,
                         ("candor", "libera", "concordia", "saturna"))
        for key, side, kind in (("candor", "heaven", "ruin"),
                                ("libera", "hell", "ruin"),
                                ("concordia", "heaven", "city"),
                                ("saturna", "hell", "city")):
            spec = places.GATE_BY_KEY[key]
            self.assertEqual((spec["side"], spec["kind"]), (side, kind))

    def test_the_sets_are_north_and_south(self):
        """Hell is north and pagan-coded; Heaven is south and church-coded.
        The two sets are disjoint and between them are the nine."""
        self.assertEqual(set(places.HEAVEN_LANDS) | set(places.HELL_LANDS),
                         set(places.COUNTRIES))
        self.assertFalse(set(places.HEAVEN_LANDS) & set(places.HELL_LANDS))

    def test_every_site_lands_in_its_own_set(self):
        for seed in range(SWEEP):
            built = world(seed)
            for key in places.GATE_KEYS:
                tile = built["tiles"][built["gates"][key]["tile"]]
                self.assertIn(tile["country"],
                              places.GATE_BY_KEY[key]["lands"],
                              f"{seed}: {key}")

    def test_no_site_stands_on_an_authored_tile_or_a_mine(self):
        for seed in range(SWEEP):
            built = world(seed)
            for key in places.GATE_KEYS:
                tile = built["tiles"][built["gates"][key]["tile"]]
                here = (tile["row"], tile["column"])
                self.assertNotEqual(tile["biome"], "sea", key)
                self.assertNotIn(here, places.HISTORICAL_BY_TILE, key)
                self.assertNotIn(here, places.MINES, key)

    def test_no_site_stands_on_or_beside_a_capital(self):
        capitals = [places.tile_row_column(tid)
                    for tid in places.CAPITAL_TILES.values()]
        for seed in range(SWEEP):
            built = world(seed)
            for key in places.GATE_KEYS:
                tile = built["tiles"][built["gates"][key]["tile"]]
                gap = min(max(abs(tile["row"] - row),
                              abs(tile["column"] - column))
                          for row, column in capitals)
                self.assertGreaterEqual(gap, 2, f"{seed}: {key}")

    def test_the_four_stand_four_tiles_apart(self):
        """At least three clear tiles between any two, so no two sites ever
        share a neighbour ring."""
        self.assertEqual(places.GATE_SEPARATION, 4)
        for seed in range(SWEEP):
            built = world(seed)
            tiles = [built["tiles"][built["gates"][key]["tile"]]
                     for key in places.GATE_KEYS]
            for i, first in enumerate(tiles):
                for second in tiles[i + 1:]:
                    self.assertGreaterEqual(
                        max(abs(first["row"] - second["row"]),
                            abs(first["column"] - second["column"])),
                        places.GATE_SEPARATION, seed)

    def test_a_live_city_keeps_a_land_neighbour_in_its_own_country(self):
        """The enclave is cut OUT of a country, and that country has to stay
        its neighbour or session 4's relations row means nothing."""
        for seed in range(SWEEP):
            built = world(seed)
            for key in ("concordia", "saturna"):
                tile = built["tiles"][built["gates"][key]["tile"]]
                self.assertTrue(
                    any(built["tiles"][nid]["biome"] != "sea"
                        and built["tiles"][nid]["country"] == tile["country"]
                        for nid in tile["neighbors"]), f"{seed}: {key}")

    def test_the_terrain_preference_is_a_weight_and_not_a_filter(self):
        """Candor wants high ground and Libera wants the wild: most worlds,
        never all of them. A hard filter over a small set would make the
        placement predictable, which is the thing the weight exists to
        avoid."""
        preferred = {key: 0 for key in places.GATE_KEYS}
        for seed in range(SWEEP):
            built = world(seed)
            for key in places.GATE_KEYS:
                spec = places.GATE_BY_KEY[key]
                tile = built["tiles"][built["gates"][key]["tile"]]
                if spec["weight"](built, tile) > 1.0:
                    preferred[key] += 1
        for key, hits in preferred.items():
            self.assertGreater(hits, SWEEP * 0.5, key)
            self.assertLess(hits, SWEEP, key)

    def test_the_placement_moves_with_the_seed(self):
        seen = {key: set() for key in places.GATE_KEYS}
        for seed in range(SWEEP):
            built = world(seed)
            for key in places.GATE_KEYS:
                seen[key].add(built["gates"][key]["tile"])
        for key, tiles in seen.items():
            self.assertGreater(len(tiles), SWEEP // 4, key)

    def test_an_empty_candidate_set_raises(self):
        """Never soften a reader: a set with no eligible tile in it is a
        map edit somebody has to look at, not a site to invent."""
        built = world(3)
        spec = dict(places.GATE_BY_KEY["candor"], lands=("phyrascia",))
        taken = [built["tiles"][tid] for tid in built["tile_order"]
                 if built["tiles"][tid]["biome"] != "sea"]
        self.assertEqual(places.gate_candidates(built, spec, taken), [])
        with unittest.mock.patch.object(
                places, "GATE_SPECS",
                (dict(places.GATE_BY_KEY["candor"], lands=()),)):
            with self.assertRaises(ValueError):
                places.roll_gates(copy.deepcopy(built))


# =========================================================================== #
# THE RECORD, THE TAGS AND THE RING
# =========================================================================== #

class TheRecordAndTheRing(unittest.TestCase):

    def setUp(self):
        self.built = world(1)

    def test_the_record_is_exactly_the_specs_shape(self):
        gates = self.built["gates"]
        self.assertEqual(list(gates), list(places.GATE_KEYS))
        for key, record in gates.items():
            spec = places.GATE_BY_KEY[key]
            owner = "keeper" if spec["kind"] == "ruin" else "cut_from"
            self.assertEqual(set(record), {"side", "kind", "tile", owner})
            self.assertEqual(record["side"], spec["side"])
            self.assertEqual(record["kind"], spec["kind"])
            self.assertEqual(record[owner],
                             self.built["tiles"][record["tile"]]["country"])

    def test_the_record_rides_the_save(self):
        self.assertEqual(json.loads(json.dumps(self.built["gates"])),
                         self.built["gates"])

    def test_the_tile_wears_both_tags(self):
        for key, record in self.built["gates"].items():
            tile = self.built["tiles"][record["tile"]]
            self.assertIn(f"gate-{record['kind']}", tile["tags"])
            self.assertIn(f"{record['side']}-{record['kind']}", tile["tags"])
            self.assertTrue(places.GATE_TAGS.issuperset(
                {f"gate-{record['kind']}",
                 f"{record['side']}-{record['kind']}"}))

    def test_the_ring_is_the_tile_and_its_land_neighbours(self):
        for key, record in self.built["gates"].items():
            tile = self.built["tiles"][record["tile"]]
            ring = {t["id"] for t in places.gate_ring(self.built, tile)}
            self.assertIn(tile["id"], ring)
            for other in ring:
                self.assertNotEqual(self.built["tiles"][other]["biome"],
                                    "sea")
            expected = set()
            for row in range(tile["row"] - 1, tile["row"] + 2):
                for column in range(tile["column"] - 1, tile["column"] + 2):
                    if not (1 <= row <= places.MAP_ROWS
                            and 1 <= column <= places.MAP_COLUMNS):
                        continue
                    tid = places.tile_id(row, column)
                    if self.built["tiles"][tid]["biome"] != "sea":
                        expected.add(tid)
            self.assertEqual(ring, expected, key)

    def test_the_ring_is_a_permanent_dated_state_naming_its_side(self):
        for key, record in self.built["gates"].items():
            for tile in places.gate_ring(self.built,
                                         self.built["tiles"][record["tile"]]):
                state = next(s for s in tile["states"]
                             if s["id"] == f"gate-{record['kind']}")
                self.assertTrue(state["active"])
                self.assertTrue(state["known"])
                self.assertEqual(state["since"], 0)
                self.assertEqual(state["by"], record["side"])

    def test_the_ring_reads_as_words_on_both_pages(self):
        record = self.built["gates"]["candor"]
        tile = self.built["tiles"][record["tile"]]
        state = next(s for s in tile["states"] if s["id"] == "gate-ruin")
        word = places.place_state_line(state)
        self.assertIn("Heaven", word)
        self.assertIn("(day 0)", word)
        brief = places.tile_brief_lines(self.built, tile)
        self.assertTrue(any("CANDOR" in line for line in brief))
        self.assertTrue(any(word.split(" (day")[0] in line
                            for line in places.tile_detail_lines(self.built,
                                                                 tile)))

    def test_the_map_marks_and_the_legend_name_all_four(self):
        rows = places.map_lines(self.built)
        for key, record in self.built["gates"].items():
            tile = self.built["tiles"][record["tile"]]
            glyph = rows[tile["row"] + 1][3 + tile["column"] - 1]
            self.assertEqual(glyph, "R" if record["kind"] == "ruin" else "G",
                             key)
        legend = "\n".join(places.gate_legend_lines(self.built))
        for key in places.GATE_KEYS:
            record = self.built["gates"][key]
            tile = self.built["tiles"][record["tile"]]
            self.assertIn(places.GATE_BY_KEY[key]["name"], legend)
            self.assertIn(places.tile_coordinate(tile["row"], tile["column"]),
                          legend)
            self.assertIn(places.SIDE_WORDS[record["side"]], legend)
        self.assertIn("R gate ruin", places.MAP_GATE_LEGEND)
        self.assertIn("G gate city", places.MAP_GATE_LEGEND)

    def test_the_city_tiles_are_still_ordinary_tiles_of_their_country(self):
        """Session 1 stamps the ring and stops: the takeover is session
        4's, and until then Concordia's ground is Umaia's (or whoever's)."""
        for key in ("concordia", "saturna"):
            record = self.built["gates"][key]
            tile = self.built["tiles"][record["tile"]]
            self.assertEqual(tile["country"], record["cut_from"])
            self.assertIn(tile["id"],
                          self.built["lands"][record["cut_from"]]["tiles"])
            self.assertIsNone(places.ruin_area(self.built, tile))
            names = {self.built["settlement_slots"][sid]["name"]
                     for sid in tile["settlement_slots"]}
            self.assertNotIn(places.GATE_BY_KEY[key]["name"], names)


# =========================================================================== #
# THE RUINS
# =========================================================================== #

class TheRuins(unittest.TestCase):

    def setUp(self):
        self.built = world(1)

    def _ruin(self, key: str) -> dict:
        return places.ruin_area(self.built,
                                self.built["gates"][key]["tile"])

    def test_the_ruin_is_a_third_kind_of_area_beside_its_countryside(self):
        for key in ("candor", "libera"):
            area = self._ruin(key)
            tile = self.built["tiles"][self.built["gates"][key]["tile"]]
            self.assertEqual(area["kind"], "ruin")
            self.assertEqual(area["subtype"], "ruined city")
            self.assertTrue(area["known"])
            self.assertEqual(area["name"],
                             f"{places.GATE_BY_KEY[key]['name']} (ruin)")
            self.assertIn(area["id"], tile["areas"])
            self.assertIsNotNone(tile["natural_area"])
            self.assertNotEqual(area["id"], tile["natural_area"])

    def test_the_ruin_wears_the_authored_tags(self):
        for key in ("candor", "libera"):
            area = self._ruin(key)
            tile = self.built["tiles"][area["tile"]]
            side = self.built["gates"][key]["side"]
            self.assertEqual(
                set(area["tags"]),
                {"ruin", "ruined city", "gate-ruin", f"{side}-ruin",
                 tile["terrain"], tile["country"]})

    def test_each_ruin_has_its_six_authored_sites(self):
        for key in ("candor", "libera"):
            built_sites = places.ruin_sites(self.built, self._ruin(key))
            authored = places.RUIN_SITES[key]
            self.assertEqual(len(built_sites), 6)
            self.assertEqual([s["level"] for s in built_sites],
                             [2, 5, 8, 11, 14, 17])
            for site, spec in zip(built_sites, authored):
                self.assertEqual(site["name"], spec["name"])
                self.assertTrue(site["known"])
                rooms = [self.built["rooms"][rid] for rid in site["rooms"]]
                self.assertEqual([r["name"] for r in rooms],
                                 list(spec["rooms"]))
                self.assertTrue(all(r["kinds"] for r in rooms))

    def test_the_deepest_site_walks_four_rooms(self):
        for key in ("candor", "libera"):
            deepest = places.ruin_sites(self.built, self._ruin(key))[-1]
            self.assertEqual(len(deepest["rooms"]), 4)
            self.assertTrue(deepest["ruin"]["deepest"])

    def test_the_rosters_come_off_the_sides_own_pool(self):
        pools = {"candor": set(quests.HEAVEN_RUIN_POOL) | {"champion"},
                 "libera": set(quests.HELL_RUIN_POOL)}
        for key, allowed in pools.items():
            for site in places.ruin_sites(self.built, self._ruin(key)):
                for rid in site["rooms"]:
                    for kind in self.built["rooms"][rid]["kinds"]:
                        self.assertIn(kind, allowed, site["name"])

    def test_a_stranded_angel_keeps_the_cells_of_the_prefecture(self):
        """The one authored body in either ruin: a champion placed by the
        site's own roster, never out of the pool of made things."""
        site = next(s for s in places.ruin_sites(self.built,
                                                 self._ruin("candor"))
                    if s["name"] == "THE PREFECTURE")
        cells = self.built["rooms"][site["rooms"][1]]
        self.assertEqual(cells["name"], "the cells")
        self.assertIn("champion", cells["kinds"])

    def test_the_deepest_sites_boss_slot_is_empty_and_nameable(self):
        """Session 2 names a `sites.BOSSES` key here and the roster takes
        it; today there is nothing alive of the kind, which is what makes a
        cleared depth stay cleared."""
        for key in ("candor", "libera"):
            self.assertIsNone(places.RUIN_SITES[key][-1]["boss"])
            deepest = places.ruin_sites(self.built, self._ruin(key))[-1]
            self.assertIsNone(deepest["ruin"]["boss"])

    def test_the_rosters_are_deterministic_per_seed(self):
        again = places.create_geography(1)
        for key in ("candor", "libera"):
            mine = places.ruin_sites(self.built, self._ruin(key))
            theirs = places.ruin_sites(
                again, places.ruin_area(again, again["gates"][key]["tile"]))
            self.assertEqual(
                [[self.built["rooms"][r]["kinds"] for r in s["rooms"]]
                 for s in mine],
                [[again["rooms"][r]["kinds"] for r in s["rooms"]]
                 for s in theirs], key)

    def test_the_ruin_rides_the_save(self):
        self.assertEqual(
            json.loads(json.dumps(self._ruin("candor"))),
            self._ruin("candor"))

    def test_the_ruin_is_a_free_step_from_the_countryside(self):
        """`look` lists it under Also on this Tile and `go` walks to it."""
        area = self._ruin("candor")
        tile = self.built["tiles"][area["tile"]]
        natural = self.built["areas"][tile["natural_area"]]
        natural["known"] = True
        state = _state(self.built, natural)
        text = _run(state, session.cmd_look, argparse.Namespace(dm=False))
        self.assertIn("CANDOR", text)
        self.assertIn("Also on this Tile", text)
        self.assertIn("Candor (ruin)", text)
        _run(state, session.cmd_go, argparse.Namespace(dest=["Candor"]))
        self.assertEqual(state["position"]["area"], area["key"])
        text = _run(state, session.cmd_look, argparse.Namespace(dm=False))
        self.assertIn("THE OUTER TERRACES (L2)", text)
        self.assertIn("delve", text)


# =========================================================================== #
# THE FOES
# =========================================================================== #

class TheGateSkins(unittest.TestCase):

    def test_both_tables_name_real_catalog_rows(self):
        for side, table in sites.GATE_SKINS.items():
            self.assertTrue(table, side)
            for kind, display in table.items():
                self.assertIn(kind, sites.FOES, f"{side}/{kind}")
                self.assertTrue(display.isascii(), display)

    def test_heaven_makes_and_hell_breeds(self):
        """The asymmetry: Heaven reskins the undead and the giant-kin as
        constructs and has no animals at all; Hell has the beasts and no
        undead."""
        heaven, hell = sites.GATE_SKINS["heaven"], sites.GATE_SKINS["hell"]
        for kind in quests.UNDEAD_POOL:
            self.assertIn(kind, heaven)
            self.assertNotIn(kind, hell)
        for kind in quests.WOLF_POOL + quests.BEAST_POOL + quests.DRAKE_POOL:
            self.assertIn(kind, hell)
            self.assertNotIn(kind, heaven)
        for kind in quests.GIANTKIN_POOL:
            self.assertIn(kind, heaven)
            self.assertIn(kind, hell)
        for kind in quests.LADDER_POOL + quests.MAGUS_POOL:
            self.assertIn(kind, heaven)
            self.assertIn(kind, hell)

    def test_the_disposition_rides_beside_the_names(self):
        for kind in sites.GATE_SKINS["heaven"]:
            self.assertEqual(sites.GATE_FEROCITY["heaven"][kind],
                             rpg.FEROCITY_RELENTLESS)
        for kind in sites.GATE_SKINS["hell"]:
            if kind in sites.GATE_BRED:
                self.assertNotIn(kind, sites.GATE_FEROCITY["hell"])
            else:
                self.assertEqual(sites.GATE_FEROCITY["hell"][kind],
                                 rpg.FEROCITY_TAKES_SPOILS)

    def test_a_gate_spawn_wears_the_name_and_the_disposition(self):
        rng = random.Random(2)
        foe = sites.make_foe("skeleton", 1, rng,
                             display=sites.GATE_SKINS["heaven"]["skeleton"],
                             ferocity=sites.GATE_FEROCITY["heaven"]
                             ["skeleton"])
        self.assertEqual(foe.name, "Broken Servant 1")
        self.assertEqual(foe.ferocity, rpg.FEROCITY_RELENTLESS)
        wolf = sites.make_foe("wolf", 1, rng,
                              display=sites.GATE_SKINS["hell"]["wolf"])
        self.assertEqual(wolf.name, "Hell Hound 1")
        self.assertEqual(wolf.ferocity, sites.FOES["wolf"].ferocity)

    def test_the_marble_warden_carries_the_warden_blade(self):
        """Same numbers as the wight's barrow blade, its own name."""
        blade, barrow = sites.WARDEN_BLADE, sites.BARROW_BLADE
        self.assertEqual(sites.WEAPON_INDEX["warden blade"], blade)
        import dataclasses
        numbers = [f.name for f in dataclasses.fields(blade)
                   if f.name not in ("name", "description")]
        self.assertEqual([getattr(blade, f) for f in numbers],
                         [getattr(barrow, f) for f in numbers])
        warden = sites.make_foe("wight", 1, random.Random(3),
                                display="Marble Warden")
        self.assertIs(warden.weapon, blade)
        plain = sites.make_foe("wight", 1, random.Random(3))
        self.assertIs(plain.weapon, barrow)

    def test_the_four_pools_are_the_specs_four(self):
        self.assertEqual(quests.HEAVEN_RUIN_POOL,
                         quests.UNDEAD_POOL + quests.GIANTKIN_POOL)
        self.assertEqual(quests.HELL_RUIN_POOL,
                         quests.WOLF_POOL + quests.BEAST_POOL
                         + quests.GIANTKIN_POOL + quests.DRAKE_POOL)
        for pool in (quests.HEAVEN_CITY_POOL, quests.HELL_CITY_POOL):
            self.assertEqual(pool, quests.BANDIT_POOL
                             + quests.LADDER_POOL[3:] + quests.MAGUS_POOL)
        for pool in (quests.HEAVEN_RUIN_POOL, quests.HELL_RUIN_POOL,
                     quests.HEAVEN_CITY_POOL, quests.HELL_CITY_POOL):
            for kind in pool:
                self.assertIn(kind, sites.FOES)


# =========================================================================== #
# THE RING'S ENCOUNTERS
# =========================================================================== #

class TheTileEncounterTable(unittest.TestCase):

    def setUp(self):
        self.built = world(1)

    def test_the_table_mirrors_the_four_pools(self):
        """worldsim cannot import quests, so the entries write their kinds
        out; this is the pin that keeps the two copies the same list."""
        table = worldsim.TILE_STATE_ENCOUNTERS
        self.assertEqual(tuple(table["gate-ruin"]["heaven"]["kinds"]),
                         quests.HEAVEN_RUIN_POOL)
        self.assertEqual(tuple(table["gate-ruin"]["hell"]["kinds"]),
                         quests.HELL_RUIN_POOL)
        self.assertEqual(tuple(table["gate-city"]["heaven"]["kinds"]),
                         quests.HEAVEN_CITY_POOL)
        self.assertEqual(tuple(table["gate-city"]["hell"]["kinds"]),
                         quests.HELL_CITY_POOL)

    def test_the_entries_carry_the_designs_grounds_and_chances(self):
        table = worldsim.TILE_STATE_ENCOUNTERS
        for side in ("heaven", "hell"):
            ruin = table["gate-ruin"][side]
            self.assertEqual(ruin["where"], "any")
            self.assertEqual(ruin["chance"], 0.6)
            self.assertEqual(ruin["as"], "something out of the ruin")
            self.assertIs(ruin["skins"], sites.GATE_SKINS[side])
            city = table["gate-city"][side]
            self.assertEqual(city["where"], "road")
            self.assertEqual(city["chance"], 0.35)
        self.assertEqual(table["gate-city"]["heaven"]["as"],
                         "a patrol out of Concordia")
        self.assertEqual(table["gate-city"]["hell"]["as"],
                         "revelers out of Saturna")

    def test_a_ruin_tile_answers_on_both_grounds_and_a_city_tile_on_roads(self):
        ruin = self.built["tiles"][self.built["gates"]["candor"]["tile"]]
        city = self.built["tiles"][self.built["gates"]["saturna"]["tile"]]
        self.assertTrue(worldsim.tile_encounter_entries(ruin, "road"))
        self.assertTrue(worldsim.tile_encounter_entries(ruin, "wilds"))
        self.assertTrue(worldsim.tile_encounter_entries(city, "road"))
        self.assertFalse(worldsim.tile_encounter_entries(city, "wilds"))
        plain = next(t for t in self.built["tiles"].values()
                     if t["biome"] != "sea" and not t["states"])
        self.assertFalse(worldsim.tile_encounter_entries(plain, "road"))

    def test_a_tile_entry_outranks_a_land_entry(self):
        """The ground is more local than the country, so `wild_event` asks
        the tile first and never falls through when it answers."""
        area = places.ruin_area(self.built,
                                self.built["gates"]["candor"]["tile"])
        state = _state(self.built, area)
        seen = {}

        def spy(st, kinds, level, banner, field=0, skins=None,
                ferocity=None):
            seen.update(kinds=list(kinds), banner=banner, skins=skins or {},
                        ferocity=ferocity or {})

        entry = worldsim.TILE_STATE_ENCOUNTERS["gate-ruin"]["heaven"]
        with unittest.mock.patch.object(
                worldsim, "tile_encounter", return_value=dict(entry)), \
                unittest.mock.patch.object(
                    worldsim, "local_encounter",
                    side_effect=AssertionError("the land was asked")), \
                unittest.mock.patch.object(
                    session, "fight_wild_encounter", spy), \
                unittest.mock.patch.object(
                    session, "notice_contest", return_value=(False, False)), \
                redirect_stdout(io.StringIO()):
            self.assertTrue(session.wild_event(state, 1.0, "On the road",
                                               where="road"))
        self.assertIn("something out of the ruin", seen["banner"])
        for kind in seen["kinds"]:
            self.assertIn(kind, quests.HEAVEN_RUIN_POOL)
        self.assertEqual(seen["skins"], sites.GATE_SKINS["heaven"])
        self.assertEqual(seen["ferocity"], sites.GATE_FEROCITY["heaven"])

    def test_the_land_is_asked_when_the_tile_says_nothing(self):
        """An ordinary Tile never shadows the country's own table."""
        far = next(t for t in self.built["tiles"].values()
                   if t["biome"] != "sea" and not t["states"])
        state = _state(self.built, self.built["areas"][far["natural_area"]])
        asked = []
        with unittest.mock.patch.object(
                worldsim, "local_encounter",
                side_effect=lambda *a, **k: asked.append(a) or None), \
                unittest.mock.patch.object(
                    session, "fight_wild_encounter", lambda *a, **k: None), \
                unittest.mock.patch.object(
                    session, "notice_contest", return_value=(False, False)), \
                redirect_stdout(io.StringIO()):
            session.wild_event(state, 1.0, "On the road", where="road")
        self.assertTrue(asked)

    def test_the_danger_ring_doubles_the_ruins_odds_and_nothing_elses(self):
        self.assertEqual(worldsim.STATE_DANGER, {"gate-ruin": 2.0})
        ruin = self.built["tiles"][self.built["gates"]["candor"]["tile"]]
        city = self.built["tiles"][self.built["gates"]["saturna"]["tile"]]
        plain = next(t for t in self.built["tiles"].values()
                     if t["biome"] != "sea" and not t["states"])
        self.assertEqual(worldsim.tile_danger(ruin), 2.0)
        self.assertEqual(worldsim.tile_danger(city), 1.0)
        self.assertEqual(worldsim.tile_danger(plain), 1.0)

    def test_the_ring_changes_how_often_and_never_how_hard(self):
        """The contract: the wild LEVEL roll is untouched -- the ring makes
        fights more frequent, not harder."""
        built = played(1)
        area = places.ruin_area(built, built["gates"]["candor"]["tile"])
        state = _state(built, area)
        chances = []
        with unittest.mock.patch.object(
                session, "wild_event",
                lambda st, chance, banner, where="wilds": chances.append(
                    chance) or False), \
                unittest.mock.patch.object(session, "save"), \
                unittest.mock.patch("session.load", return_value=state), \
                redirect_stdout(io.StringIO()):
            session.cmd_explore(argparse.Namespace())
        self.assertEqual(chances,
                         [session.EXPLORE_ENCOUNTER_CHANCE * 2.0])

    def test_the_road_roll_reads_the_arrival_tiles_ring(self):
        area = places.ruin_area(self.built,
                                self.built["gates"]["candor"]["tile"])
        state = _state(self.built, area)
        chances = []
        with unittest.mock.patch.object(
                session, "wild_event",
                lambda st, chance, banner, where="wilds": chances.append(
                    chance) or False):
            session._road_roll(state, area, 1)
        self.assertAlmostEqual(chances[0],
                               session.TRAVEL_ENCOUNTER_CHANCE * 2.0)


# =========================================================================== #
# THE DELVE
# =========================================================================== #

class TheDelve(unittest.TestCase):

    def setUp(self):
        self.built = world(1)
        self.area = places.ruin_area(self.built,
                                     self.built["gates"]["candor"]["tile"])
        self.state = _state(self.built, self.area, day=10, level=2)

    def _delve(self, *words: str) -> str:
        return _run(self.state, session.cmd_delve,
                    argparse.Namespace(site=list(words)))

    def _site(self, name: str) -> dict:
        return next(s for s in places.ruin_sites(self.built, self.area)
                    if name in s["name"])

    def test_delve_without_an_argument_lists_the_six(self):
        text = self._delve()
        for spec in places.RUIN_SITES["candor"]:
            self.assertIn(spec["name"], text)
        self.assertIn("(L17)", text)

    def test_delve_outside_a_ruin_says_where_the_ruin_is(self):
        tile = self.built["tiles"][self.area["tile"]]
        natural = self.built["areas"][tile["natural_area"]]
        state = _state(self.built, natural)
        text = _run(state, session.cmd_delve,
                    argparse.Namespace(site=["outer"]))
        self.assertIn("Candor (ruin)", text)
        self.assertIn("go", text)
        far = next(t for t in self.built["tiles"].values()
                   if t["biome"] != "sea" and not t["states"])
        elsewhere = _state(self.built,
                           self.built["areas"][far["natural_area"]])
        text = _run(elsewhere, session.cmd_delve,
                    argparse.Namespace(site=["outer"]))
        self.assertIn("no ruin here", text.lower())

    def test_a_delve_forges_over_the_sites_authored_rooms(self):
        site = self._site("OUTER TERRACES")
        rooms_before = list(site["rooms"])
        self._delve("OUTER TERRACES")
        qid = self.state["active_quest"]
        quest = self.built["quests"][qid]
        self.assertEqual(quest["sites"], [site["id"]])
        self.assertEqual(site["rooms"], rooms_before)
        self.assertEqual(quest["level"], 2)
        self.assertEqual(quest["encounters"], len(rooms_before))
        self.assertTrue(quest["forced"])
        self.assertEqual(quest["align"], "neutral")
        self.assertEqual(quest["silver_total"], 0)
        self.assertIsNone(quest.get("giver"))
        self.assertEqual(quest["delve"], site["id"])
        self.assertIs(quest["skins"] and quest["skins"]["skeleton"],
                      sites.GATE_SKINS["heaven"]["skeleton"])
        self.assertEqual(self.state["position"]["site"], site["id"])

    def test_a_delve_takes_no_board_slot_and_no_radius(self):
        self._delve("OUTER TERRACES")
        quest = self.built["quests"][self.state["active_quest"]]
        self.assertFalse(quests.is_ordinary_posting(quest))
        for area in self.built["areas"].values():
            self.assertNotIn(quest["id"], area["quests"])
        self.assertIsNone(quest.get("deadline_day"))

    def test_delving_the_same_site_twice_reopens_the_same_job(self):
        self._delve("OUTER TERRACES")
        first = self.state["active_quest"]
        self.state["active_quest"] = None
        self._delve("OUTER TERRACES")
        self.assertEqual(self.state["active_quest"], first)

    def test_clearing_pays_the_field_tranche_and_asks_for_no_turn_in(self):
        site = self._site("OUTER TERRACES")
        self._delve("OUTER TERRACES")
        qid = self.state["active_quest"]
        quest = self.built["quests"][qid]
        quest["next"]["room"] = len(site["rooms"])
        before = self.state["party"][0].xp
        log: list[str] = []
        with redirect_stdout(io.StringIO()):
            session._close_site(self.state, log, qid)
        text = "\n".join(log)
        self.assertIn("THE SITE IS CLEARED", text)
        self.assertNotIn("turnin", text)
        self.assertEqual(quest["status"], "done")
        self.assertGreater(self.state["party"][0].xp, before)
        self.assertEqual(self.state["purse"].silver, 500)
        self.assertEqual(site["ruin"]["cleared_day"], 10)

    def test_a_cleared_site_refills_after_thirty_days(self):
        self.assertEqual(places.RUIN_REFILL_DAYS, 30)
        site = self._site("OUTER TERRACES")
        before = [list(self.built["rooms"][r]["kinds"]) for r in site["rooms"]]
        places.close_ruin_site(self.built, site, 10)
        self.assertEqual(places.ruin_site_state(site, 10), "cleared")
        self.assertEqual(places.ruin_site_state(site, 39), "cleared")
        self.assertEqual(places.ruin_site_state(site, 40), "open")
        self.state["clock"].day = 20
        text = self._delve("OUTER TERRACES")
        self.assertIn("cleared", text)
        self.assertIsNone(self.state["active_quest"])
        self.state["clock"].day = 41
        self._delve("OUTER TERRACES")
        self.assertIsNotNone(self.state["active_quest"])
        self.assertEqual(site["ruin"]["refills"], 1)
        after = [list(self.built["rooms"][r]["kinds"]) for r in site["rooms"]]
        self.assertNotEqual(before, after)
        for kinds in after:
            for kind in kinds:
                self.assertIn(kind, quests.HEAVEN_RUIN_POOL)

    def test_the_deepest_site_seals_and_clears_the_ring(self):
        """A cleared depth with no boss alive: no refill, and the ruin's
        ring goes quiet the same day."""
        deepest = places.ruin_sites(self.built, self.area)[-1]
        tile = self.built["tiles"][self.area["tile"]]
        ring = places.gate_ring(self.built, tile)
        self.assertTrue(all(any(s["id"] == "gate-ruin" and s["active"]
                                for s in t["states"]) for t in ring))
        lines = places.close_ruin_site(self.built, deepest, 30)
        self.assertTrue(lines)
        self.assertIn("Candor", lines[0])
        self.assertFalse(any(any(s["id"] == "gate-ruin" and s["active"]
                                 for s in t["states"]) for t in ring))
        self.assertEqual(worldsim.tile_danger(tile), 1.0)
        self.assertFalse(worldsim.tile_encounter_entries(tile, "road"))
        for day in (30, 400):
            self.assertEqual(places.ruin_site_state(deepest, day), "sealed")
        text = self._delve("GATE PLAZA")
        self.assertIn("stays empty", text)

    def test_a_shallow_site_never_touches_the_ring(self):
        site = self._site("OUTER TERRACES")
        tile = self.built["tiles"][self.area["tile"]]
        self.assertEqual(places.close_ruin_site(self.built, site, 10), [])
        self.assertEqual(worldsim.tile_danger(tile), 2.0)

    def test_every_line_the_delve_prints_is_ascii(self):
        for words in ((), ("OUTER TERRACES",), ("nowhere",)):
            for line in self._delve(*words).split("\n"):
                self.assertTrue(line.isascii(), line)


if __name__ == "__main__":
    unittest.main()
