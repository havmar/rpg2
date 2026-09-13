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

import dataclasses

import conquest
import crime
import karma
import people
import places
import quests
import rpg
import rulers
import session
import sites
import weapons
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
        The two sets are disjoint and between them are the nine -- the
        HUMAN nine: a gate never rolls into the other gate's city state."""
        self.assertEqual(set(places.HEAVEN_LANDS) | set(places.HELL_LANDS),
                         set(places.HUMAN_COUNTRIES))
        self.assertFalse(set(places.HEAVEN_LANDS) & set(places.HELL_LANDS))

    def test_every_site_lands_in_its_own_set(self):
        """A ruin's tile still flies its keeper's flag; a live city's flies
        its own after the takeover (2026-09-12, session 4), so the set is
        checked against the country it was cut out of."""
        for seed in range(SWEEP):
            built = world(seed)
            for key in places.GATE_KEYS:
                record = built["gates"][key]
                tile = built["tiles"][record["tile"]]
                home = record.get("cut_from", tile["country"])
                self.assertIn(home, places.GATE_BY_KEY[key]["lands"],
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
        # The NINE painted capitals: a city state's own capital IS the
        # tile being placed (2026-09-12).
        capitals = [places.tile_row_column(tid)
                    for tid in places.HISTORICAL_CAPITAL_TILES.values()]
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
                record = built["gates"][key]
                tile = built["tiles"][record["tile"]]
                self.assertTrue(
                    any(built["tiles"][nid]["biome"] != "sea"
                        and built["tiles"][nid]["country"]
                        == record["cut_from"]
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
            tile = self.built["tiles"][record["tile"]]
            if spec["kind"] == "ruin":
                # A ruin's country KEEPS it.
                self.assertEqual(record["keeper"], tile["country"])
            else:
                # ...and a city's country lost the tile to the takeover
                # (2026-09-12), so `cut_from` is where it came from.
                self.assertEqual(tile["country"], key)
                self.assertNotEqual(record["cut_from"], key)

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

    def test_a_live_city_has_no_ruin_on_its_tile(self):
        for key in ("concordia", "saturna"):
            tile = self.built["tiles"][self.built["gates"][key]["tile"]]
            self.assertIsNone(places.ruin_area(self.built, tile))


# =========================================================================== #
# THE TAKEOVER: the two city states (2026-09-12, session 4)
# =========================================================================== #

class TheTakeover(unittest.TestCase):
    """One tile leaves its country and becomes a country. What moves is the
    FLAG -- the tile, the natural Area standing on it, the land's capital --
    and what does not move is the GROUND: a wall round a plain does not move
    the plain, so climate, terrain, harvest, goods and the countryside's own
    inventory are exactly the donor's still."""

    def setUp(self):
        self.built = world(1)

    def test_the_tile_changes_hands_and_the_land_lists_agree(self):
        for seed in range(6):
            built = world(seed)
            for key in ("concordia", "saturna"):
                record = built["gates"][key]
                tid = record["tile"]
                donor = record["cut_from"]
                tile = built["tiles"][tid]
                self.assertEqual(tile["country"], key)
                self.assertIn(key, tile["tags"])
                self.assertNotIn(donor, tile["tags"])
                self.assertEqual(built["lands"][key]["tiles"], [tid])
                self.assertNotIn(tid, built["lands"][donor]["tiles"])
                self.assertEqual(built["lands"][key]["capital_tile"], tid)

    def test_the_countryside_goes_with_the_tile_and_keeps_its_ground(self):
        """The natural Area changes hands and NOTHING else about it: it was
        cut from the donor culture's inventory before the takeover and it
        keeps it. Concordia's fields are still Seraptanian fields."""
        for key in ("concordia", "saturna"):
            record = self.built["gates"][key]
            tile = self.built["tiles"][record["tile"]]
            area = self.built["areas"][tile["natural_area"]]
            self.assertEqual(area["land"], key)
            self.assertEqual(area["homeland"], key)
            self.assertIn(area["id"], self.built["lands"][key]["areas"])
            self.assertNotIn(area["id"],
                             self.built["lands"][record["cut_from"]]["areas"])
            donor_culture = places.CULTURE_OF[record["cut_from"]]
            self.assertIn(f"/{donor_culture}/", area["template"])
            self.assertIn(area["template"].rsplit("/", 1)[-1],
                          places.CULTURE_SPECS[donor_culture][
                              "natural_sites"])
            self.assertIsNotNone(tile["climate"])
            self.assertIsNotNone(tile["harvest"])

    def test_the_census_seats_the_city_and_nothing_else(self):
        for seed in range(6):
            built = world(seed)
            for key in ("concordia", "saturna"):
                tile = built["tiles"][built["gates"][key]["tile"]]
                slots = [built["settlement_slots"][sid]
                         for sid in tile["settlement_slots"]]
                self.assertEqual(len(slots), 1, key)
                slot = slots[0]
                self.assertEqual(slot["tier"], "city")
                self.assertEqual(slot["name"],
                                 places.GATE_BY_KEY[key]["name"])
                self.assertTrue(slot["capital"])
                self.assertTrue(slot["authored"])
                self.assertTrue(slot["known"])
                self.assertEqual(slot["charter"], "free")
                self.assertIsNone(slot["manor"])

    def test_the_city_is_built_at_worldgen_and_wears_the_gate_template(self):
        for key in ("concordia", "saturna"):
            tile = self.built["tiles"][self.built["gates"][key]["tile"]]
            slot = self.built["settlement_slots"][tile["settlement_slots"][0]]
            area = self.built["areas"][slot["area"]]
            self.assertEqual(area["name"], places.GATE_BY_KEY[key]["name"])
            self.assertEqual(area["subtype"], "city")
            self.assertTrue(area["capital"])
            self.assertTrue(area["known"])
            culture = places.CULTURE_OF[key]
            spec = places.AREA_SPECS[places.template_id(culture,
                                                        "gate_city")]
            self.assertEqual(area["description"], spec["description"])
            for tag in spec["tags"]:
                self.assertIn(tag, area["tags"], (key, tag))
            side = places.LAND_SPECS[key]["side"]
            self.assertIn(f"{side}-city", area["tags"])
            kinds = {service["kind"] for service in area["services"]}
            self.assertTrue({"lodging", "smith", "general_goods", "healer",
                             "alchemist", "market", "government"} <= kinds,
                            (key, sorted(kinds)))

    def test_the_capital_tile_is_a_land_fact_and_the_readers_use_it(self):
        here = self.built["tiles"][self.built["party_tile"]]["country"]
        for country in places.COUNTRIES:
            tid = places.capital_tile(self.built, country)
            self.assertEqual(self.built["lands"][country]["capital_tile"],
                             tid)
            self.assertEqual(self.built["tiles"][tid]["country"], country)
            # ...and worldsim reads the same field for the land's own sky
            # while the party is somewhere else.
            if country != here:
                self.assertEqual(
                    worldsim.sky_tile(self.built, country)["id"], tid)
        self.assertFalse(hasattr(places, "CAPITAL_TILES"))
        self.assertEqual(set(places.HISTORICAL_CAPITAL_TILES),
                         set(places.HUMAN_COUNTRIES))

    def test_the_priced_counter_is_the_catalog_s_and_reaches_the_tile(self):
        want = {"concordia": {"healer": 0.6, "lodging": 0.8, "goods": 1.2},
                "saturna": {"lodging": 0.5, "goods": 0.9, "healer": 1.3}}
        for key, terms in want.items():
            side = places.LAND_SPECS[key]["side"]
            self.assertEqual(places.GATE_CITY_MENU[side], terms)
            tile = self.built["tiles"][self.built["gates"][key]["tile"]]
            here = places.tile_terms(self.built, tile)
            # The city's row MULTIPLIES over whatever else the ground is
            # doing (a granary, a pithead, a crossroads), exactly as the
            # tile menu's own rows multiply over each other.
            bare = copy.deepcopy(tile)
            bare["tags"] = [t for t in tile["tags"]
                            if t != f"{side}-city"]
            base = places.tile_terms(self.built, bare)
            for name, mult in terms.items():
                self.assertAlmostEqual(here[name],
                                       base.get(name, 1.0) * mult, places=6)
        for term in set(places.MENU_TERM_WORDS):
            self.assertIn(term, worldsim.MENU_TERMS)
        self.assertEqual(set(places.MENU_TERM_WORDS),
                         set(worldsim.MENU_TERMS))

    def test_the_world_boots_with_eleven_lands(self):
        built = quests.generate_world(3)
        self.assertEqual(len(built["lands"]), 11)
        for key in places.CITY_STATES:
            land = built["lands"][key]
            self.assertTrue(land["world"]["deck"], key)
            self.assertTrue(worldsim.constitution_of(built, key), key)
            self.assertTrue(worldsim.facts_of(key), key)
            seat = next(s for s in quests.settlements_by_land(built)[key]
                        if s["capital"])
            self.assertEqual(seat["name"], places.GATE_BY_KEY[key]["name"])

    def test_no_campaign_opens_inside_a_gate_city(self):
        for seed in range(30):
            built = world(seed)
            slot = built["settlement_slots"][built["start_slot"]]
            self.assertNotIn(built["tiles"][slot["tile"]]["country"],
                             places.CITY_STATES, seed)

    def test_the_map_legend_calls_them_countries(self):
        legend = "\n".join(places.gate_legend_lines(self.built, width=200))
        for key in ("concordia", "saturna"):
            record = self.built["gates"][key]
            donor = self.built["lands"][record["cut_from"]]["name"]
            self.assertIn(f"city state in {donor}", legend)

    def test_the_two_crowns_and_the_two_defenders(self):
        self.assertEqual(quests.RULER_TITLES["concordia"],
                         {"m": "prefect", "f": "prefect"})
        self.assertEqual(quests.RULER_TITLES["saturna"],
                         {"m": "lord of misrule", "f": "lady of misrule"})
        self.assertEqual(conquest.DEFENDER_ROLES["concordia"],
                         "warden of the gate")
        self.assertEqual(conquest.DEFENDER_ROLES["saturna"],
                         "master of hounds")

    def test_the_two_name_pools_are_one_tongue_in_two_registers(self):
        """Heaven's names are BOUND -- every one of the men's ends in the
        suffix that means "of the Law" -- and Hell's are UNBOUND: never
        -el, and rank is an epithet the table hangs on instead."""
        for sex in ("m", "f"):
            self.assertEqual(len(set(people.NAMES["concordia"][sex])), 25)
            self.assertEqual(len(set(people.NAMES["saturna"][sex])), 25)
        for name in people.NAMES["concordia"]["m"]:
            self.assertTrue(name.endswith(("el", "iel")), name)
        for sex in ("m", "f"):
            for name in people.NAMES["saturna"][sex]:
                self.assertFalse(name.endswith("el"), name)
        for pool in (people.NAMES["concordia"], people.NAMES["saturna"]):
            for names in pool.values():
                for name in names:
                    self.assertTrue(name.isascii(), name)

    def test_the_counters_are_staffed_out_of_the_city_s_own_pool(self):
        built = quests.generate_world(5)
        for key in places.CITY_STATES:
            seat = next(s for s in quests.settlements_by_land(built)[key])
            providers = [npc for npc in built["npcs"]
                         if npc["seat"] == seat["id"]]
            self.assertTrue(providers, key)
            pool = {n for names in people.NAMES[key].values() for n in names}
            for npc in providers:
                self.assertEqual(npc["homeland"], key)
                self.assertIn(npc["name"].split()[0], pool)

    def test_the_two_tables_land_in_the_human_countryside(self):
        """The city is the capital and the only board in its country, so
        its four rows are what it posts -- and every one of them lands on
        ordinary ground within the three-day radius."""
        built = quests.generate_world(7)
        for key, titles in (("concordia", ("Escort the Healers",
                                           "The Lamp Thieves",
                                           "Bring the Child Home",
                                           "The Prefect's Levy")),
                            ("saturna", ("Bring the Wine", "Guard the Feast",
                                         "Break the Debt-House",
                                         "The Hunt of Misrule"))):
            table = [t["title"] for t
                     in quests.TEMPLATES[places.CULTURE_OF[key]]]
            for title in titles:
                self.assertIn(title, table, key)
                place = quests.quest_place_requirement(
                    next(t for t in quests.TEMPLATES[places.CULTURE_OF[key]]
                         if t["title"] == title))
                self.assertFalse(place.get("strict"), title)
            seat = next(s for s in quests.settlements_by_land(built)[key])
            rng = random.Random(9)
            for _ in range(6):
                quest = quests._post_quest(built, seat, rng)
                self.assertIn(quest["name"],
                              table + [t["title"]
                                       for t in quests.EPIC_TEMPLATES])

    def test_the_two_epics_are_the_city_s_own_and_nobody_else_s(self):
        """Capital-only by construction: the two EPIC rows sit on their own
        culture's table, which exactly one land in the world wears."""
        for title in ("The Prefect's Levy", "The Hunt of Misrule"):
            wearing = [c for c, table in quests.TEMPLATES.items()
                       if any(t["title"] == title for t in table)]
            self.assertEqual(len(wearing), 1, title)
            self.assertIn(wearing[0], ("heaven", "hell"))
            self.assertNotIn(title, [t["title"]
                                     for t in quests.EPIC_TEMPLATES])


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
        """...plus the two authored bodies the pool never rolls: the
        stranded angel of the Prefecture and the deepest Site's boss."""
        pools = {"candor": set(quests.HEAVEN_RUIN_POOL) | {"champion"},
                 "libera": set(quests.HELL_RUIN_POOL)}
        for key, allowed in pools.items():
            allowed = allowed | {places.RUIN_SITES[key][-1]["boss"]}
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

    def test_the_deepest_site_names_its_boss_and_stands_it_in_the_bar(self):
        """The `boss` slot session 1 left empty carries a `sites.BOSSES`
        key since session 2, and `ruin_site_rosters` puts it in the LAST
        room -- "the bar", where Tom's bar is."""
        for key, kind in (("candor", "sentinel of candor"),
                          ("libera", "old host of libera")):
            self.assertEqual(places.RUIN_SITES[key][-1]["boss"], kind)
            deepest = places.ruin_sites(self.built, self._ruin(key))[-1]
            self.assertEqual(deepest["ruin"]["boss"], kind)
            self.assertFalse(deepest["ruin"]["boss_dead"])
            rooms = [self.built["rooms"][r] for r in deepest["rooms"]]
            self.assertEqual(rooms[-1]["name"], "the bar")
            self.assertEqual(rooms[-1]["kinds"].count(kind), 1)
            for room in rooms[:-1]:
                self.assertNotIn(kind, room["kinds"])

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
        """A cleared depth with its boss DEAD: no refill, and the ruin's
        ring goes quiet the same day."""
        deepest = places.ruin_sites(self.built, self.area)[-1]
        deepest["ruin"]["boss_dead"] = True
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


# =========================================================================== #
# THE BOSSES AND THE BARS (2026-09-12, session 2)
# =========================================================================== #

class TheBosses(unittest.TestCase):
    """gates.md section 9: the tier above the dragon, as a table of two."""

    def test_a_boss_is_not_in_the_catalog_and_no_pool_can_draw_one(self):
        for kind in sites.BOSSES:
            self.assertNotIn(kind, sites.FOES)
        pools = [tpl["pool"] for table in quests.TEMPLATES.values()
                 for tpl in table]
        pools += [tpl["pool"] for tpl in quests.EPIC_TEMPLATES]
        pools += [quests.HEAVEN_RUIN_POOL, quests.HELL_RUIN_POOL,
                  quests.HEAVEN_CITY_POOL, quests.HELL_CITY_POOL,
                  quests.LADDER_POOL, quests.wild_pool("seraptania")]
        for pool in pools:
            for kind in sites.BOSSES:
                self.assertNotIn(kind, pool)

    def test_the_bench_row_loop_never_sees_one(self):
        """bench_bestiary walks FOES; --bosses is a separate pass."""
        import bench_bestiary
        rows = sorted(sites.FOES, key=lambda k: (sites.FOES[k].level, k))
        for kind in sites.BOSSES:
            self.assertNotIn(kind, rows)
        self.assertEqual(
            sorted(sites.BOSSES,
                   key=lambda k: (sites.BOSSES[k].level, k)),
            ["old host of libera", "sentinel of candor"])
        self.assertEqual(bench_bestiary.BENCH_WORLD_SEED, 1)

    def test_both_bodies_are_the_legend_row_with_no_mortal_tradeoffs(self):
        for kind in sites.BOSSES:
            spec = sites.BOSSES[kind]
            self.assertEqual((spec.dex, spec.str_, spec.sta), (8, 8, 8))
            self.assertEqual(spec.pain, 3)
            self.assertEqual(spec.spell_ward, 2)
            self.assertEqual(spec.crowd_cap, 3)
            self.assertEqual(spec.power, 12)
            self.assertEqual(spec.ref_pack, 1)
            self.assertTrue(spec.tireless)
            self.assertGreaterEqual(spec.training, 2)
            self.assertIsNone(spec.weapon)

    def test_the_sentinel_and_the_old_host_are_the_designs_two(self):
        zoh = sites.BOSSES["sentinel of candor"]
        self.assertEqual(zoh.display, "Zohariel the Sentinel")
        self.assertEqual((zoh.school, zoh.school_rank), ("ice", 2))
        self.assertEqual(zoh.sweep, 1)
        self.assertEqual(zoh.level, 17)
        self.assertEqual(zoh.ferocity, rpg.FEROCITY_RELENTLESS)
        self.assertEqual((zoh.hp, zoh.training), (20, 3))

        saar = sites.BOSSES["old host of libera"]
        self.assertEqual(saar.display, "Saar the Old Host")
        self.assertEqual((saar.school, saar.school_rank), ("fire", 2))
        self.assertEqual(saar.inflicts, "burn")
        self.assertEqual((saar.sweep, saar.sweep_cost_power), (2, 3))
        self.assertEqual(saar.level, 16)
        self.assertEqual(saar.ferocity, rpg.FEROCITY_TAKES_SPOILS)

    def test_foe_spec_reads_the_catalog_and_then_the_bosses(self):
        self.assertIs(sites.foe_spec("wolf"), sites.FOES["wolf"])
        self.assertIs(sites.foe_spec("sentinel of candor"),
                      sites.BOSSES["sentinel of candor"])
        with self.assertRaises(KeyError):
            sites.foe_spec("no such thing")

    def test_make_foe_builds_a_boss_only_with_its_own_steel(self):
        rng = random.Random(3)
        with self.assertRaises(ValueError):
            sites.make_foe("sentinel of candor", 1, rng)
        bar = sites.boss_bar("sentinel of candor", 1)
        foe = sites.make_foe("sentinel of candor", 1, rng, weapon=bar)
        self.assertIs(foe.weapon, bar)
        self.assertEqual(foe.name, "Zohariel the Sentinel 1")
        self.assertEqual(foe.spells, {"ice": 2})
        self.assertTrue(foe.tireless)
        self.assertEqual(foe.crowd_cap, 3)
        self.assertEqual(foe.ferocity, rpg.FEROCITY_RELENTLESS)

    def test_the_roster_block_announces_what_it_is(self):
        bar = sites.boss_bar("old host of libera", 1)
        foe = sites.make_foe("old host of libera", 1, random.Random(4),
                             weapon=bar)
        text = "\n".join(sites.roster_lines([foe]))
        for word in ("Saar the Old Host", "the Libera bar", "drilled +2",
                     "barely feels pain", "tireless", "spell-warded 2",
                     "caster: fire 2"):
            self.assertIn(word, text)
        for line in text.split("\n"):
            self.assertTrue(line.isascii(), line)


class TheTwoBars(unittest.TestCase):
    """gates.md section 4: the relics, as steel and as armory rows."""

    def setUp(self):
        self.built = played(1)

    def _entry(self, gate: str) -> dict:
        return next(e for e in self.built["armory"]
                    if e.get("gate") == gate)

    def test_the_bar_is_a_clean_sp_nine_two_hander(self):
        for gate in ("candor", "libera"):
            bar = weapons.gate_bar(1, gate)
            self.assertEqual(bar.base, "zweihander")
            self.assertEqual(bar.tier, "legendary")
            self.assertEqual(weapons.weapon_sp(bar), weapons.GATE_BAR_SP)
            self.assertEqual(bar.str_bonus, 3)
            self.assertFalse(bar.rider)
            self.assertFalse(bar.lunge)
            self.assertFalse(bar.silver_on_kill or bar.karma_on_kill)
            self.assertTrue(bar.description.isascii())

    def test_the_bar_is_the_same_piece_in_every_world(self):
        """There is exactly one Candor bar: Tom set it, and no seed
        re-forges it."""
        first = weapons.gate_bar(1, "candor")
        for seed in (2, 17, 99):
            self.assertEqual(dataclasses.asdict(weapons.gate_bar(seed,
                                                                 "candor")),
                             dataclasses.asdict(first))
        self.assertNotEqual(weapons.gate_bar(1, "libera").name, first.name)

    def test_both_bars_are_fixed_entries_in_the_world_armory(self):
        names = [e["name"] for e in self.built["armory"]]
        self.assertIn("the Candor bar", names)
        self.assertIn("the Libera bar", names)
        self.assertEqual(len(self.built["armory"]),
                         len(weapons.ARMORY_TIERS) + len(weapons.GATE_BARS))
        for gate, owner in (("candor", "Zohariel the Sentinel"),
                            ("libera", "Saar the Old Host")):
            entry = self._entry(gate)
            self.assertEqual(entry["status"], "known")
            self.assertEqual(entry["owner"]["name"], owner)
            deepest = places.ruin_sites(
                self.built,
                places.ruin_area(self.built,
                                 self.built["gates"][gate]["tile"]))[-1]
            self.assertEqual(entry["owner"]["seat"], deepest["id"])
            self.assertIn(deepest["name"], entry["where"])
            self.assertEqual(entry["boss"],
                             places.RUIN_SITES[gate][-1]["boss"])

    def test_the_armory_page_prints_them_inside_the_screen(self):
        lines = weapons.armory_lines(self.built["armory"])
        text = "\n".join(lines)
        self.assertIn("the Candor bar", text)
        self.assertIn("the Libera bar", text)
        bars = [ln for ln in lines
                if "bar" in ln or "Candor" in ln or "Libera" in ln
                or "Zohariel" in ln or "Saar" in ln or "GATE" in ln]
        self.assertTrue(bars)
        for line in bars:
            self.assertTrue(line.isascii(), line)
        for line in lines:
            self.assertLessEqual(len(line), 40, line)

    def test_the_armory_rides_the_save(self):
        for entry in self.built["armory"][-len(weapons.GATE_BARS):]:
            self.assertEqual(json.loads(json.dumps(entry))["name"],
                             entry["name"])
            self.assertIn(entry["name"],
                          ("the Candor bar", "the Libera bar"))

    def test_only_the_deepest_sites_boss_is_handed_a_bar(self):
        area = places.ruin_area(self.built,
                                self.built["gates"]["candor"]["tile"])
        sites_ = places.ruin_sites(self.built, area)
        deepest = sites_[-1]
        bar = session.ruin_boss_bar(self.built, deepest,
                                    "sentinel of candor")
        self.assertEqual(bar.name, "the Candor bar")
        self.assertIsNone(session.ruin_boss_bar(self.built, deepest,
                                                "skeleton"))
        self.assertIsNone(session.ruin_boss_bar(self.built, sites_[0],
                                                "sentinel of candor"))

    def test_the_boss_stands_in_the_bar_room_holding_its_bar(self):
        area = places.ruin_area(self.built,
                                self.built["gates"]["candor"]["tile"])
        deepest = places.ruin_sites(self.built, area)[-1]
        state = _state(self.built, area, day=10, level=17)
        _run(state, session.cmd_delve,
             argparse.Namespace(site=["GATE PLAZA"]))
        quest = self.built["quests"][state["active_quest"]]
        quest["next"]["room"] = len(deepest["rooms"]) - 1
        text = _run(state, session.cmd_room, argparse.Namespace())
        self.assertIn("Zohariel the Sentinel", text)
        self.assertIn("the Candor bar", text)
        self.assertIn("room 4/4: the bar", text)
        for line in text.split("\n"):
            self.assertTrue(line.isascii(), line)

    def test_the_bar_drops_when_the_boss_dies_and_a_hand_can_take_it(self):
        bar = sites.boss_bar("old host of libera", 1)
        foe = sites.make_foe("old host of libera", 1, random.Random(5),
                             weapon=bar)
        self.assertIsNone(rpg.fallen_weapons_line([foe]))   # still standing
        foe.hp = 0
        foe.dead = True
        line = rpg.fallen_weapons_line([foe])
        self.assertIn("the Libera bar", line)
        self.assertNotIn("a the Libera bar", line)

        area = places.ruin_area(self.built,
                                self.built["gates"]["libera"]["tile"])
        state = _state(self.built, area, day=10, level=17)
        session.record_drops(state, [foe])
        self.assertIn("the Libera bar", state["drops"])
        hero = state["party"][0]
        _run(state, session.cmd_give,
             argparse.Namespace(hero=hero.name,
                                weapon=["the", "Libera", "bar"],
                                as_name=None))
        self.assertEqual(hero.weapon.name, "the Libera bar")
        self.assertEqual(hero.weapon.str_bonus, 3)

    def test_catalog_steel_is_never_kept_as_a_drop(self):
        foe = sites.make_foe("veteran", 1, random.Random(6))
        foe.hp, foe.dead = 0, True
        state = {"drops": {}}
        session.record_drops(state, [foe])
        self.assertEqual(state["drops"], {})


class TheSealNeedsABody(unittest.TestCase):
    """The ruin goes quiet on a corpse, not on an empty room."""

    def setUp(self):
        self.built = world(1)
        self.area = places.ruin_area(self.built,
                                     self.built["gates"]["libera"]["tile"])
        self.deepest = places.ruin_sites(self.built, self.area)[-1]

    def _ring_live(self) -> bool:
        tile = self.built["tiles"][self.area["tile"]]
        return any(any(s["id"] == "gate-ruin" and s["active"]
                       for s in t["states"])
                   for t in places.gate_ring(self.built, tile))

    def test_a_depth_cleared_with_the_boss_alive_refills(self):
        self.assertEqual(places.close_ruin_site(self.built, self.deepest,
                                                10), [])
        self.assertTrue(self._ring_live())
        self.assertEqual(places.ruin_site_state(self.deepest, 10), "cleared")
        self.assertEqual(places.ruin_site_state(self.deepest, 40), "open")
        places.refill_ruin_site(self.built, self.deepest, 40)
        rooms = [self.built["rooms"][r] for r in self.deepest["rooms"]]
        self.assertIn("old host of libera", rooms[-1]["kinds"])

    def test_a_dead_boss_seals_the_depth_and_clears_the_ring(self):
        self.deepest["ruin"]["boss_dead"] = True
        lines = places.close_ruin_site(self.built, self.deepest, 10)
        self.assertTrue(lines)
        self.assertFalse(self._ring_live())
        for day in (10, 400):
            self.assertEqual(places.ruin_site_state(self.deepest, day),
                             "sealed")

    def test_the_won_fight_is_what_marks_the_boss_dead(self):
        state = {"world": self.built}
        bar = sites.boss_bar("old host of libera", 1)
        foe = sites.make_foe("old host of libera", 1, random.Random(7),
                             weapon=bar)
        session.mark_boss_dead(state, self.deepest["id"], [foe])
        self.assertFalse(self.deepest["ruin"]["boss_dead"])
        foe.withdrew = True         # it broke and ran: still not a body
        session.mark_boss_dead(state, self.deepest["id"], [foe])
        self.assertFalse(self.deepest["ruin"]["boss_dead"])
        foe.withdrew, foe.hp, foe.dead = False, 0, True
        session.mark_boss_dead(state, self.deepest["id"], [foe])
        self.assertTrue(self.deepest["ruin"]["boss_dead"])

    def test_a_shallow_sites_dead_roster_never_marks_a_boss(self):
        shallow = places.ruin_sites(self.built, self.area)[0]
        foe = sites.make_foe("wolf", 1, random.Random(8))
        foe.hp, foe.dead = 0, True
        session.mark_boss_dead({"world": self.built}, shallow["id"], [foe])
        self.assertFalse(shallow["ruin"]["boss_dead"])


# =========================================================================== #
# THE RUIN JOBS
# =========================================================================== #

class TheRuinTemplates(unittest.TestCase):
    """gates.md section 14, "Into the ruins": eight jobs on every table."""

    def setUp(self):
        self.built = played(1)

    def test_the_eight_are_on_every_cultures_table(self):
        self.assertEqual(len(quests.RUIN_TEMPLATES), 8)
        titles = [tpl["title"] for tpl in quests.RUIN_TEMPLATES]
        self.assertEqual(len(set(titles)), 8)
        for culture, table in quests.TEMPLATES.items():
            posted = [tpl["title"] for tpl in table]
            for title in titles:
                self.assertIn(title, posted, culture)
        for title in titles:
            self.assertNotIn(title,
                             [t["title"] for t in quests.EPIC_TEMPLATES])

    def test_every_row_is_authored_whole_and_in_the_register(self):
        for tpl in quests.RUIN_TEMPLATES:
            for key in ("desc", "giver", "epilogue", "failure_epilogue"):
                self.assertTrue(tpl[key], (tpl["title"], key))
            self.assertTrue(tpl["sites"])
            self.assertTrue(tpl["pool"])
            for kind in tpl["pool"]:
                self.assertIn(kind, sites.FOES)
            for text in (tpl["title"], tpl["desc"], tpl["giver"],
                         tpl["epilogue"], tpl["failure_epilogue"]):
                self.assertTrue(text.isascii(), text)

    def test_each_row_is_placed_on_its_own_sides_ruin_and_strictly(self):
        for tpl in quests.RUIN_TEMPLATES:
            place = quests.QUEST_PLACE_REQUIREMENTS[tpl["title"]]
            self.assertEqual(len(place["area_any"]), 1)
            side = place["area_any"][0]
            self.assertIn(side, ("heaven-ruin", "hell-ruin"))
            self.assertEqual(place["domain"], "natural")
            self.assertEqual(place["site_template"], "ruin")
            self.assertTrue(place["strict"])
            if tpl["skins"]:
                want = "heaven" if side == "heaven-ruin" else "hell"
                self.assertEqual(tpl["skins"], sites.GATE_SKINS[want])
                self.assertEqual(tpl["ferocity"], sites.GATE_FEROCITY[want])

    def test_only_the_two_ruin_areas_wear_the_side_words(self):
        """The words are on the ruin Area alone: a settlement standing on a
        gate's own tile is in the RING, not in the dead city."""
        for side, gate in (("heaven-ruin", "candor"), ("hell-ruin", "libera")):
            wearing = [a for a in self.built["areas"].values()
                       if side in a.get("tags", ())]
            self.assertEqual(len(wearing), 1, side)
            self.assertEqual(wearing[0]["kind"], "ruin")
            self.assertEqual(
                wearing[0]["id"],
                places.ruin_area(self.built,
                                 self.built["gates"][gate]["tile"])["id"])
        for gate in places.GATE_KEYS:
            tile = self.built["tiles"][self.built["gates"][gate]["tile"]]
            for aid in tile["areas"]:
                area = self.built["areas"][aid]
                if area["kind"] == "ruin":
                    continue
                if area["land"] in places.CITY_STATES:
                    # The CITY words are the gate city's OWN settlement
                    # template's (2026-09-12, session 4; gates.md section
                    # 10): a `gate_city` Area says what it is.
                    self.assertNotIn("gate-ruin", area["tags"], aid)
                    continue
                for tag in places.GATE_TAGS:
                    self.assertNotIn(tag, area["tags"], aid)

    def test_a_heaven_job_lands_in_candor_and_a_hell_job_in_libera(self):
        origin = self.built["start_area"]
        for tpl in quests.RUIN_TEMPLATES:
            place = quests.quest_place_requirement(tpl)
            gate = ("candor" if place["area_any"][0] == "heaven-ruin"
                    else "libera")
            want = places.ruin_area(self.built,
                                    self.built["gates"][gate]["tile"])
            picked = quests._select_quest_area(
                self.built, origin, place, random.Random(2), radius=None)
            self.assertEqual(picked["id"], want["id"], tpl["title"])

    def test_the_natural_domain_admits_a_ruin(self):
        """The widening is what lets a `domain: natural` job stand in a
        dead city; a settlement Area is still refused."""
        place = quests.quest_place_requirement(quests.RUIN_TEMPLATES[0])
        self.assertEqual(place["domain"], "natural")
        picked = quests._select_quest_area(
            self.built, self.built["start_area"], place,
            random.Random(3), radius=None)
        self.assertEqual(picked["kind"], "ruin")

    def test_a_board_out_of_range_never_offers_one(self):
        far = min(
            (s for s in quests.settlements(self.built)),
            key=lambda s: -places.path_days(
                self.built["areas"][s["key"]]["tile"],
                self.built["gates"]["candor"]["tile"]))
        place = quests.quest_place_requirement(quests.RUIN_TEMPLATES[0])
        self.assertFalse(quests.place_reachable(self.built, far["key"],
                                                place))
        with self.assertRaises(ValueError):
            quests._select_quest_area(self.built, far["key"], place,
                                      random.Random(4))
        near_area = places.ruin_area(
            self.built, self.built["gates"]["candor"]["tile"])
        self.assertTrue(quests.place_reachable(self.built, near_area["key"],
                                               place))

    def test_a_posted_ruin_job_builds_its_own_site_in_the_ruin(self):
        """The six authored Sites belong to `delve`: a board job never
        re-rosters one."""
        area = places.ruin_area(self.built,
                                self.built["gates"]["libera"]["tile"])
        before = {s["id"]: (s["level"],
                            [list(self.built["rooms"][r]["kinds"])
                             for r in s["rooms"]])
                  for s in places.ruin_sites(self.built, area)}
        tpl = next(t for t in quests.RUIN_TEMPLATES
                   if t["title"] == "The Vine Pits")
        quest = quests.build_quest(self.built, "qruin", tpl, area["key"], 5,
                                   random.Random(9), radius=None)
        self.assertEqual(self.built["areas"][quest["target_area"]]["id"],
                         area["id"])
        for sid in quest["sites"]:
            self.assertNotIn(sid, before)
            self.assertEqual(self.built["sites"][sid]["name"],
                             "the vine pits")
        after = {s["id"]: (s["level"],
                           [list(self.built["rooms"][r]["kinds"])
                            for r in s["rooms"]])
                 for s in places.ruin_sites(self.built, area)}
        self.assertEqual(before, after)
        self.assertEqual(quest["ferocity"], sites.GATE_FEROCITY["hell"])

    def test_a_board_near_a_ruin_can_post_one(self):
        """The sweep: over forty worlds the eight reach a board, and only
        boards inside the three-day radius carry them."""
        titles = {tpl["title"] for tpl in quests.RUIN_TEMPLATES}
        seen = set()
        for seed in range(1, 25):
            built = played(seed)
            for settlement in quests.settlements(built):
                origin = built["areas"][settlement["key"]]
                for qid in settlement["quests"]:
                    quest = built["quests"][qid]
                    if quest["name"] not in titles:
                        continue
                    seen.add(quest["name"])
                    target = built["areas"][quest["target_area"]]
                    self.assertEqual(target["kind"], "ruin")
                    self.assertLessEqual(
                        places.path_days(origin["tile"], target["tile"]),
                        quests.ORDINARY_TARGET_DAYS)
        self.assertTrue(seen)


class TomsStone(unittest.TestCase):
    """gates.md section 4: the pilgrim's stop, on ordinary ground."""

    def _inventories(self, culture: str) -> dict:
        return places.LAND_SPECS_BY_CULTURE[culture]["natural_sites"] \
            if hasattr(places, "LAND_SPECS_BY_CULTURE") else None

    def test_it_stands_in_every_western_and_southern_inventory(self):
        catalog = json.loads(
            places.CATALOG_PATH.read_text(encoding="utf-8"))
        for culture, wanted in (("western", True), ("southern", True),
                                ("steppe", False), ("norse", False)):
            for key, specs in \
                    catalog["cultures"][culture]["natural_sites"].items():
                ids = [spec["id"] for spec in specs]
                self.assertEqual("toms-stone" in ids, wanted,
                                 f"{culture}/{key}")

    def test_it_is_authored_as_a_shrine(self):
        catalog = json.loads(
            places.CATALOG_PATH.read_text(encoding="utf-8"))
        spec = next(s for s in
                    catalog["cultures"]["western"]["natural_sites"]["fields"]
                    if s["id"] == "toms-stone")
        self.assertEqual(spec["name"], "TOM'S STONE")
        self.assertEqual(spec["template"], "shrine")
        self.assertEqual(len(spec["rooms"]), 2)
        self.assertTrue(json.dumps(spec).isascii())

    def test_it_materializes_as_a_natural_shrine_site(self):
        built = world(5)
        area = next(a for a in built["areas"].values()
                    if a["kind"] == "natural"
                    and "toms-stone" in a["natural_site_order"]
                    and built["lands"][a["land"]]["culture"] == "western")
        site = None
        for _ in range(len(area["natural_site_order"])):
            made = places.materialize_natural_site(built, area, day=0)
            if made is not None and made["name"] == "TOM'S STONE":
                site = made
                break
        self.assertIsNotNone(site)
        self.assertEqual(site["template"], "shrine")
        self.assertEqual(site["domain"], "natural")
        self.assertTrue(site["known"])
        names = [built["rooms"][r]["name"] for r in site["rooms"]]
        self.assertEqual(names, ["PILGRIM PATH", "THE STONE"])

    def test_no_steppe_or_norse_area_offers_it(self):
        built = world(5)
        for area in built["areas"].values():
            if area["kind"] != "natural":
                continue
            if built["lands"][area["land"]]["culture"] in ("steppe", "norse"):
                self.assertNotIn("toms-stone", area["natural_site_order"])


# =========================================================================== #
# THE TWO PACKETS AND THE HUMAN SIDE (2026-09-12, the gates arc's session 5)
# =========================================================================== #
# Everything in the world layer that cannot be authored at import, because
# its ends are ROLLED: the five standing words, the four host facts, the
# four HOST-resolved relation rows, the crusade tension, and the two chains
# the packets are built round.


def _quiet(built: dict, polity: str, band: str = "normal") -> None:
    """Take everything off a land: no live card, no held state, no band
    effect. A generated world hands out crises it did not ask for, and a
    chain test needs a zero to drive from."""
    layer = worldsim.land_layer(built, polity)
    for track in worldsim.TRACKS:
        layer[worldsim.LIVE_KEY[track]] = None
    for entry in list(worldsim.held_states(built, polity)):
        worldsim.drop_state(built, polity, entry["id"], 0)
    layer["wealth"] = band


def _fire(built: dict, polity: str, key: str, day: int = 5) -> None:
    worldsim._fire(built, polity, worldsim.CARDS_BY_KEY[key], day,
                   random.Random(day))


class TheStandingGateStates(unittest.TestCase):
    """The five words worldgen stamps off `world["gates"]`, and the four
    facts that go with them. None of them is authorable at import: which
    land hosts Concordia is a roll."""

    def test_the_four_lands_wear_their_word(self):
        for seed in range(1, 9):
            built = played(seed)
            for key, word in worldsim.GATE_STANDING.items():
                land = worldsim.gate_land(built, key)
                self.assertIn(word, worldsim.state_ids(built, land),
                              (seed, key))

    def test_no_other_land_wears_one(self):
        for seed in range(1, 9):
            built = played(seed)
            for key, word in worldsim.GATE_STANDING.items():
                wearing = [p for p in built["lands"]
                           if word in {s["id"] for s
                                       in worldsim.held_states(built, p)}]
                self.assertEqual(wearing, [worldsim.gate_land(built, key)],
                                 (seed, key))

    def test_the_standing_words_are_worldgens_and_no_cards(self):
        """They are in EXTERNAL_STATES for the same reason `at-war` is: a
        land hosts a gate for the whole campaign and nothing takes it off,
        so no card may set one and none does."""
        for word in worldsim.GATE_STANDING.values():
            self.assertIn(word, worldsim.EXTERNAL_STATES)
            for spec in worldsim.CARDS:
                state = spec["outlets"].get("state") or {}
                for group in ("set", "while", "clear"):
                    self.assertNotIn(word, state.get(group, ()), spec["key"])

    def test_the_two_host_words_reach_a_counter(self):
        """The cheapest thing on the map that says a foreign power is HERE:
        the cure leaks out of Concordia and the feast out of Saturna, every
        day, at the host's own counter."""
        self.assertLess(worldsim.STATE_MENU["hosts-heaven"]["healer"], 1.0)
        self.assertLess(worldsim.STATE_MENU["hosts-hell"]["lodging"], 1.0)
        built = played(3)
        host = worldsim.gate_land(built, "concordia")
        self.assertLess(worldsim.term(built, host, "healer"), 1.0)

    def test_pagan_host_only_where_the_old_gods_are(self):
        """Hell came back into old-god country, or it did not. The word
        goes on BOTH ends when it does -- the card that reads it is
        Saturna's own -- and on neither when Hell landed in a Sun land."""
        seen = set()
        for seed in range(1, 25):
            built = played(seed)
            host = worldsim.gate_land(built, "saturna")
            pagan = host in worldsim.PAGAN_HOSTS
            seen.add(pagan)
            for land in (host, "saturna"):
                self.assertEqual(
                    "pagan-host" in worldsim.state_ids(built, land),
                    pagan, (seed, land, host))
        self.assertEqual(seen, {True, False})   # both worlds exist

    def test_the_four_host_facts_are_on_the_right_pages(self):
        for seed in range(1, 9):
            built = played(seed)
            for key, title in (("concordia", "THE GATE CITY"),
                               ("saturna", "THE GATE CITY"),
                               ("candor", "THE WHITE RUIN"),
                               ("libera", "THE WILD RUIN")):
                land = worldsim.gate_land(built, key)
                titles = [f["title"] for f in built["lands"][land]["facts"]]
                self.assertIn(title, titles, (seed, key))
                page = "\n".join(worldsim.lore_lines(built, land))
                self.assertIn(title, page, (seed, key))
                self.assertIn(built["lands"][land]["name"], page)

    def test_the_year_is_printed_on_a_lore_page_and_nowhere_else(self):
        """gates.md section 1: 1027 is the only date the game ever prints,
        and only here."""
        built = played(1)
        for polity in built["lands"]:
            self.assertIn("1027",
                          "\n".join(worldsim.lore_lines(built, polity)),
                          polity)
        self.assertNotIn("1027", "\n".join(worldsim.world_lines(built)))


class TheResolvedRelations(unittest.TestCase):
    """The four rows whose ends are rolled (`_GATE_RELATIONS`), resolved
    onto the world at `open_world` off `world["gates"]`."""

    def test_the_authored_table_carries_the_placeholder(self):
        self.assertEqual(len(worldsim._GATE_RELATIONS), 4)
        ends = [(e["from"], e["to"]) for e in worldsim._GATE_RELATIONS]
        self.assertEqual(ends, [("concordia", worldsim.HOST),
                                ("saturna", worldsim.HOST),
                                (worldsim.HOST, "concordia"),
                                (worldsim.HOST, "saturna")])
        for edge in worldsim.RELATIONS:      # ...and the module table has
            self.assertNotIn(worldsim.HOST,  # none of it
                             (edge["from"], edge["to"]))

    def test_every_end_resolves_to_a_real_land_in_every_world(self):
        for seed in range(1, 13):
            built = played(seed)
            table = worldsim.relations_of(built)
            self.assertEqual(len(table), len(worldsim.RELATIONS) + 4)
            for edge in table:
                for side in ("from", "to"):
                    self.assertIn(edge[side], built["lands"], (seed, edge))
                self.assertNotEqual(edge["from"], edge["to"])

    def test_the_four_rows_run_between_a_city_and_its_own_host(self):
        for seed in range(1, 13):
            built = played(seed)
            gates = {"concordia": worldsim.gate_land(built, "concordia"),
                     "saturna": worldsim.gate_land(built, "saturna")}
            found = {e["kind"]: e for e in worldsim.relations_of(built)
                     if e["kind"] in ("the cure", "the feast",
                                      "the bishops", "the hunt")}
            self.assertEqual(set(found),
                             {"the cure", "the feast", "the bishops",
                              "the hunt"})
            self.assertEqual(found["the cure"]["to"], gates["concordia"])
            self.assertEqual(found["the feast"]["to"], gates["saturna"])
            self.assertEqual(found["the bishops"]["from"],
                             gates["concordia"])
            self.assertEqual(found["the hunt"]["from"], gates["saturna"])

    def test_every_land_is_reached_and_the_cities_only_this_way(self):
        """The validator's reachability pass runs on the RESOLVED table,
        which is the whole reason the four rows exist: no authored edge
        touches a city state."""
        for seed in range(1, 9):
            built = played(seed)
            reached = {p for e in worldsim.relations_of(built)
                       for p in (e["from"], e["to"])}
            self.assertEqual(reached, set(built["lands"]), seed)

    def test_every_derived_word_reaches_a_price_or_a_road(self):
        for edge in worldsim._GATE_RELATIONS:
            word = edge["then"]
            self.assertIn(word, worldsim.STATE_WORDS)
            self.assertTrue(worldsim.STATE_MENU.get(word)
                            or worldsim.STATE_ENCOUNTERS.get(word), word)

    def test_a_shut_gate_is_felt_at_the_hosts_healer(self):
        built = played(2)
        host = worldsim.gate_land(built, "concordia")
        _quiet(built, "concordia")
        _quiet(built, host)
        before = worldsim.term(built, host, "healer")
        worldsim.set_state(built, "concordia", "gate-shut", 4)
        derived = [s["id"] for s in worldsim.derived_states(built, host)]
        self.assertIn("cure-dear", derived)
        self.assertGreater(worldsim.term(built, host, "healer"), before)

    def test_the_spilled_feast_puts_revelers_on_the_hosts_ground(self):
        built = played(2)
        host = worldsim.gate_land(built, "saturna")
        _quiet(built, "saturna")
        _quiet(built, host)
        worldsim.set_state(built, "saturna", "feast-spilled", 4)
        self.assertIn("feast-abroad",
                      [s["id"] for s in worldsim.derived_states(built, host)])
        entries = worldsim.encounter_entries(built, host, "wilds")
        self.assertTrue([e for e in entries if "feast" in e["as"]])

    def test_the_gate_watched_placeholder_is_retired(self):
        self.assertNotIn("gate-watched", worldsim.STATE_WORDS)
        for edge in worldsim.RELATIONS + worldsim._GATE_RELATIONS:
            self.assertNotEqual(edge["then"], "gate-watched")


class TheHumanSide(unittest.TestCase):
    """What the nine make of two foreign cities on their ground."""

    def test_the_return_question_sits_in_both_rite_decks(self):
        spec = worldsim.CARDS_BY_KEY["communion/the-return-question"]
        self.assertEqual(set(spec["land"]), {"byzantium", "seraptania"})
        self.assertEqual(spec["admits"]["states"], ("schism-near",))
        self.assertEqual(spec["outlets"]["state"]["while"],
                         ("return-argued",))
        self.assertNotIn("set", spec["outlets"]["state"])

    def test_the_return_questions_news_names_both_answers(self):
        """Which rite welcomes the Return is an ADDRESS, not an opinion:
        the one that has Concordia on its own ground. Both rite words open
        a sentence in the line, so the hook hands them over capitalized
        (2026-09-13)."""
        for seed in (1, 2, 3, 4, 5, 6):
            built = played(seed)
            host = worldsim.gate_land(built, "concordia")
            fields = worldsim._return_hook(built, "byzantium", 5,
                                           random.Random(1))
            keeps = ("The old rite"
                     if places.CULTURE_OF[host] == "southern"
                     else "The western church")
            other = ("The western church" if keeps == "The old rite"
                     else "The old rite")
            self.assertEqual(fields["hosting"], keeps, seed)
            self.assertEqual(fields["other"], other, seed)
            self.assertEqual(fields["host"], built["lands"][host]["name"])

    def test_the_synod_line_starts_every_sentence_upper_case(self):
        """The rendered news line, read the way the table reads it: no
        sentence in it opens in lower case (2026-09-13, the post-build
        review's find)."""
        built = played(1)
        _quiet(built, "byzantium")
        worldsim.set_state(built, "byzantium", "schism-near", 3)
        _fire(built, "byzantium", "communion/the-return-question", 4)
        line = worldsim.take_news(built, "byzantium", 4)[0]
        for sentence in [s.strip() for s in line.split(". ") if s.strip()]:
            self.assertTrue(sentence[0].isupper(), sentence)

    def test_the_crusade_tension_is_stamped_only_on_a_sun_host(self):
        seen = set()
        for seed in range(1, 25):
            built = played(seed)
            host = worldsim.gate_land(built, "saturna")
            sun = host in worldsim.SUN_HOSTS
            seen.add(sun)
            for polity in built["lands"]:
                held = "church-vs-saturna" in worldsim.tensions_of(built,
                                                                   polity)
                self.assertEqual(held, sun and polity == host,
                                 (seed, polity, host))
        self.assertEqual(seen, {True, False})

    def test_the_crusade_is_never_rollable(self):
        """It is in EXTERNAL_TENSIONS, so no western land without a feast
        town beside it can ever draw it."""
        self.assertIn("church-vs-saturna", worldsim.EXTERNAL_TENSIONS)
        rng = random.Random(4)
        for _ in range(400):
            for polity in places.CULTURE_LANDS["western"]:
                self.assertNotIn("church-vs-saturna",
                                 worldsim.roll_tensions(rng, polity,
                                                        "crisis"))

    def test_the_crusade_card_enters_the_hosts_deck_and_no_one_elses(self):
        for seed in range(1, 13):
            built = played(seed)
            host = worldsim.gate_land(built, "saturna")
            for polity in places.CULTURE_LANDS["western"]:
                deck = worldsim.land_layer(built, polity)["deck"]
                self.assertEqual("western/the-preaching-crusade" in deck,
                                 polity == host and host
                                 in worldsim.SUN_HOSTS, (seed, polity))

    def test_toms_four_versions_reach_every_land_of_every_culture(self):
        built = played(1)
        want = {"western": "SAINT TOM AND THE RETURN",
                "southern": "SAINT TOM OF THE TWO DOORS",
                "norse": "TOM THE SMITH",
                "steppe": "TOM WHO SEWED THE SKY"}
        for culture, title in want.items():
            for polity in places.CULTURE_LANDS[culture]:
                titles = [f["title"] for f in worldsim.facts_of(polity)]
                self.assertIn(title, titles, polity)
        # ...and no land wears two of them: the versions disagree
        for polity in places.HUMAN_COUNTRIES:
            titles = [f["title"] for f in worldsim.facts_of(polity)]
            self.assertEqual(len([t for t in titles if t in want.values()]),
                             1, polity)


class TheGateCityCounters(unittest.TestCase):
    """The two options a side -- the hole the stubs left, closed."""

    def test_both_cities_are_selling_something(self):
        built = played(1)
        for polity in places.CITY_STATES:
            lines = worldsim.service_lines(built, polity, "capital")
            self.assertTrue(lines, polity)
            self.assertEqual(len(worldsim.options_here(built, polity,
                                                       "capital")), 2)

    def test_the_words_are_the_designs_words(self):
        for word in ("choir", "measures", "feast", "fire"):
            spec = worldsim.option_named(word)
            self.assertIsNotNone(spec, word)
            self.assertEqual(worldsim.option_word(spec), word)

    def test_the_two_schools_undercut_every_human_teaching_door(self):
        human = [o["silver"] for o in worldsim.OPTIONS
                 if o["does"] == "book"
                 and not set(o["land"]) & set(places.CITY_STATES)]
        for word in ("measures", "fire"):
            self.assertLess(worldsim.option_named(word)["silver"],
                            min(human), word)


class TheTwoChains(unittest.TestCase):
    """The two driven chains the packets are built round, end to end."""

    def test_the_register_chain_takes_a_child_and_names_it_once(self):
        built = played(1)
        _quiet(built, "concordia")
        _fire(built, "concordia", "heaven/the-register", 4)
        self.assertIn("register-read",
                      worldsim.state_ids(built, "concordia"))
        spec = worldsim.CARDS_BY_KEY["heaven/the-removal"]
        self.assertTrue(worldsim.admits(built, "concordia", spec["admits"],
                                        weather="clear"))
        worldsim.land_layer(built, "concordia")["live"] = None
        _fire(built, "concordia", "heaven/the-removal", 9)
        self.assertNotIn("register-read",
                         worldsim.state_ids(built, "concordia"))
        self.assertIn("removal", worldsim.state_ids(built, "concordia"))
        who = worldsim.named_authority(built, "concordia", "nephilim-child")
        self.assertIsNotNone(who)
        news = worldsim.take_news(built, "concordia", 9)
        self.assertTrue([line for line in news if who["name"] in line])
        # ...and the name is KEPT: firing again does not re-roll a person
        worldsim.land_layer(built, "concordia")["live"] = None
        _fire(built, "concordia", "heaven/the-removal", 30)
        self.assertEqual(
            worldsim.named_authority(built, "concordia",
                                     "nephilim-child")["name"], who["name"])

    def test_the_removal_posts_the_childs_quest_on_the_hosts_board(self):
        """The work is in the host country, so the job is (2026-09-13):
        a village child taken through a door in the Prefecture is read off
        a board down the road, not off Concordia's own one board."""
        posted = worldsim.CARDS_BY_KEY[
            "heaven/the-removal"]["outlets"]["quest"]["post"]
        self.assertEqual(posted["title"], "Bring the Child Home")
        self.assertEqual(posted["align"], "good")
        self.assertEqual(posted["at"], "host")
        built = played(1)
        host = worldsim.gate_land(built, "concordia")
        _quiet(built, "concordia")
        _fire(built, "concordia", "heaven/the-removal", 9)
        self.assertNotIn("Bring the Child Home",
                         [j["job"]["title"] for j
                          in worldsim.board_postings(built, "concordia")])
        live = [j["job"]["title"] for j
                in worldsim.board_postings(built, host)]
        self.assertIn("Bring the Child Home", live)

    def test_the_hanged_lord_posts_his_mens_job_on_the_hosts_board(self):
        built = played(1)
        host = worldsim.gate_land(built, "saturna")
        _quiet(built, "saturna")
        _fire(built, "saturna", "hell/the-lord-hanged", 9)
        self.assertNotIn("The Lord's Men",
                         [j["job"]["title"] for j
                          in worldsim.board_postings(built, "saturna")])
        self.assertIn("The Lord's Men",
                      [j["job"]["title"] for j
                       in worldsim.board_postings(built, host)])

    def test_the_three_cards_that_offer_two_employers(self):
        """THE DARK OUTLETS (2026-09-13). Three cards put up two jobs at
        once -- the same trouble with a good employer and a dark one -- and
        the player picks whose money he takes. Opposite aligns, distinct
        board keys, and no shared site stem to collide on."""
        pairs = {"heaven/the-removal": ("Bring the Child Home",
                                        "Deliver the Child"),
                 "hell/the-debt-book": ("The Year Owed",
                                        "Collect the Year"),
                 "hell/a-stranded-one": ("The Old Feast", "Bring Her In")}
        for key, (good, dark) in pairs.items():
            outlet = worldsim.CARDS_BY_KEY[key]["outlets"]["quest"]
            self.assertEqual(outlet["post"]["title"], good)
            self.assertEqual(outlet["dark"]["title"], dark)
            self.assertEqual(outlet["post"]["align"], "good")
            self.assertEqual(outlet["dark"]["align"], "dark")
            self.assertEqual(outlet["post"]["pool"], outlet["dark"]["pool"])
            self.assertEqual(outlet["post"]["skins"],
                             outlet["dark"]["skins"])
            self.assertEqual(outlet["post"]["ferocity"],
                             outlet["dark"]["ferocity"])
            self.assertFalse(set(outlet["post"]["sites"])
                             & set(outlet["dark"]["sites"]), key)
        built = played(1)
        host = worldsim.gate_land(built, "concordia")
        _quiet(built, "concordia")
        _fire(built, "concordia", "heaven/the-removal", 9)
        board = worldsim.board_postings(built, host)
        both = {j["key"]: j["job"]["align"] for j in board
                if j["key"].startswith("heaven/the-removal")}
        self.assertEqual(both, {"heaven/the-removal": "good",
                                "heaven/the-removal/dark": "dark"})

    def test_both_employers_reach_one_board_and_pay_the_dark_premium(self):
        """A dark card job is a dark job: it goes up beside its twin, the
        board prints it as one, and the karma machinery reads it off
        `align` exactly as it reads a dark template's."""
        built = played(1)
        settlement = next(s for s in quests.settlements(built)
                          if s["land"] == "saturna")
        _quiet(built, "saturna")
        worldsim.set_state(built, "saturna", "feast-spilled", 3)
        _fire(built, "saturna", "hell/the-debt-book", 4)
        posted = {}
        for posting in worldsim.board_postings(built, "saturna"):
            if not posting["key"].startswith("hell/the-debt-book"):
                continue
            quest = quests._post_card_quest(built, settlement, posting,
                                            random.Random(5), day=4)
            posted[quest["name"]] = quest
        self.assertEqual(set(posted), {"The Year Owed", "Collect the Year"})
        self.assertEqual(posted["The Year Owed"]["align"], "good")
        self.assertEqual(posted["Collect the Year"]["align"], "dark")
        self.assertGreater(
            quests.quest_silver_posted(posted["Collect the Year"]),
            posted["Collect the Year"]["silver_total"])
        self.assertEqual(quests.quest_silver_posted(posted["The Year Owed"]),
                         posted["The Year Owed"]["silver_total"])
        self.assertFalse(
            set(posted["The Year Owed"]["sites"])
            & set(posted["Collect the Year"]["sites"]))

    def test_the_child_is_a_person_of_the_host_country(self):
        """A half-blood on Concordia's list is a VILLAGE child, and the
        name has to say so or the list is not frightening."""
        for seed in (1, 2, 3, 4):
            built = played(seed)
            host = worldsim.gate_land(built, "concordia")
            _quiet(built, "concordia")
            _fire(built, "concordia", "heaven/the-removal", 9)
            name = worldsim.named_authority(built, "concordia",
                                            "nephilim-child")["name"]
            self.assertIn(name, people.NAMES[host]["m"]
                          + people.NAMES[host]["f"], (seed, host))

    def test_the_feast_chain_collects_a_year_and_names_the_debtor(self):
        built = played(1)
        _quiet(built, "saturna")
        _fire(built, "saturna", "hell/the-feast-spills", 4)
        self.assertIn("feast-spilled", worldsim.state_ids(built, "saturna"))
        worldsim.land_layer(built, "saturna")["live"] = None
        spec = worldsim.CARDS_BY_KEY["hell/the-debt-book"]
        self.assertTrue(worldsim.admits(built, "saturna", spec["admits"],
                                        weather="clear"))
        _fire(built, "saturna", "hell/the-debt-book", 9)
        self.assertNotIn("feast-spilled",
                         worldsim.state_ids(built, "saturna"))
        self.assertIn("year-owed", worldsim.state_ids(built, "saturna"))
        who = worldsim.named_authority(built, "saturna", "hell-debtor")
        self.assertIsNotNone(who)
        self.assertTrue([line for line
                         in worldsim.take_news(built, "saturna", 9)
                         if who["name"] in line])
        self.assertIn("The Year Owed",
                      [j["job"]["title"] for j
                       in worldsim.board_postings(built, "saturna")])

    def test_the_spilled_feast_is_cheap_lodging_and_the_owed_year_is_not(
            self):
        built = played(1)
        _quiet(built, "saturna")
        base = worldsim.term(built, "saturna", "lodging")
        worldsim.set_state(built, "saturna", "feast-spilled", 4)
        self.assertLess(worldsim.term(built, "saturna", "lodging"), base)
        worldsim.drop_state(built, "saturna", "feast-spilled", 5)
        worldsim.set_state(built, "saturna", "year-owed", 5)
        self.assertGreater(worldsim.term(built, "saturna", "lodging"), base)

    def test_the_cages_reach_the_crime_layer(self):
        built = played(1)
        _quiet(built, "saturna")
        worldsim.set_state(built, "saturna", "cages-open", 4)
        self.assertTrue(worldsim.mark_roles(built, "saturna", "powder"))
        self.assertTrue(worldsim.mark_roles(built, "saturna", "con"))

    def test_the_lamps_reach_the_crime_layer_wherever_heaven_stands(self):
        built = played(1)
        host = worldsim.gate_land(built, "concordia")
        self.assertTrue(worldsim.mark_roles(built, host, "burglary"))
        self.assertTrue(worldsim.mark_roles(built, host, "con"))


class TheCardPostedJobs(unittest.TestCase):
    """What a card's own job carries (2026-09-13, the post-build review).
    The nine jobs the two packets post field the gates' own people, and
    the mercy class has to travel with the names: a Marble Warden met off
    a board is as relentless as one met in the ruin."""

    def _gate_jobs(self, side: str) -> list[dict]:
        return [posting["job"]
                for spec in worldsim.CARDS if spec["land"] == (
                    places.CITY_STATE_OF_SIDE[side],)
                for posting in worldsim._card_jobs(spec)]

    def test_every_gate_card_job_carries_its_sides_disposition(self):
        wanted = {"heaven": ("Bring the Child Home", "Deliver the Child",
                             "The Hermit's Escort", "The Lamp Thieves",
                             "The Servant That Walks"),
                  "hell": ("The Year Owed", "Collect the Year",
                           "The Lord's Men", "Hounds off the Road",
                           "The Old Feast", "Bring Her In",
                           "Open the Cages")}
        for side, titles in wanted.items():
            jobs = {job["title"]: job for job in self._gate_jobs(side)}
            self.assertEqual(set(jobs), set(titles), side)
            for title, job in jobs.items():
                self.assertEqual(job["ferocity"],
                                 dict(sites.GATE_FEROCITY[side]), title)

    def test_a_warden_off_the_childs_job_is_relentless(self):
        """The bug this pins: `job()` had no `ferocity` field at all, so
        every warden a card posted fought at the catalog row's own mercy
        class and took the party's purse instead of finishing it."""
        built = played(3)
        tpl = worldsim.CARDS_BY_KEY[
            "heaven/the-removal"]["outlets"]["quest"]["post"]
        settlement = next(s for s in quests.settlements(built)
                          if s["land"] == worldsim.gate_land(built,
                                                             "concordia"))
        quest = quests.build_quest(built, "qtest", tpl, settlement["key"],
                                   4, random.Random(7))
        self.assertEqual(quest["ferocity"]["soldier"],
                         rpg.FEROCITY_RELENTLESS)
        warden = sites.make_foe("soldier", 1, random.Random(7),
                                display=quest["skins"]["soldier"],
                                ferocity=quest["ferocity"]["soldier"])
        self.assertIn("Warden", warden.name)
        self.assertEqual(warden.ferocity, rpg.FEROCITY_RELENTLESS)

    def test_the_lamp_job_pays_on_the_lamps(self):
        job = worldsim.CARDS_BY_KEY[
            "heaven/the-lamp-thieves"]["outlets"]["quest"]["post"]
        self.assertEqual(job["proof"], "the lamps")

    def test_the_validator_still_refuses_a_key_it_does_not_know(self):
        """The new fields widened the job schema; they did not open it."""
        good = worldsim.CARDS_BY_KEY[
            "hell/the-kennels-open"]["outlets"]["quest"]
        worldsim._validate_quest("test", dict(good))     # the real one
        with self.assertRaises(ValueError):
            worldsim._validate_quest("test", dict(good, bounty=3))
        with self.assertRaises(ValueError):
            worldsim._validate_quest(
                "test", {"post": dict(good["post"], hazard="fire")})
        with self.assertRaises(ValueError):
            worldsim._validate_quest(
                "test", {"post": dict(good["post"],
                                      ferocity={"no such row": 2})})
        with self.assertRaises(ValueError):
            worldsim.job("Nowhere", "x", pool=("wolf",), sites=("a hill",),
                         giver="a shepherd", epilogue="", failure_epilogue="",
                         at="the moon")


class TheDeckScopes(unittest.TestCase):
    """Which deck a card sits in (2026-09-13, the post-build review). Three
    cards were in the wrong one, and each was invisible rather than loud:
    a state nobody could set, a tension nobody could roll, a witch-hunt at
    the Prefecture."""

    def test_the_sermon_is_the_hosts_card_and_only_the_hosts(self):
        """`pulpit-against` runs off `preached-against` on the HOST, so
        the card that sets it has to be a card the host can draw."""
        spec = worldsim.CARDS_BY_KEY["heaven/the-sermon"]
        self.assertEqual(set(spec["land"]), set(places.HUMAN_COUNTRIES))
        self.assertEqual(spec["admits"]["states"], ("hosts-heaven",))
        self.assertFalse(spec["admits"]["tension"])
        for seed in (1, 2, 3, 4):
            built = played(seed)
            host = worldsim.gate_land(built, "concordia")
            for polity in built["lands"]:
                deck = worldsim._deck(built, polity, "crisis",
                                      worldsim.tensions_of(built, polity))
                drawable = ("heaven/the-sermon" in deck
                            and worldsim.admits(
                                built, polity,
                                spec["admits"], weather="clear"))
                self.assertEqual(drawable, polity == host, (seed, polity))

    def test_the_sermon_turns_the_hosts_pulpit_on_concordia(self):
        built = played(2)
        host = worldsim.gate_land(built, "concordia")
        _quiet(built, host)
        _quiet(built, "concordia")
        before = worldsim.term(built, "concordia", "goods")
        _fire(built, host, "heaven/the-sermon", 6)
        self.assertIn("preached-against", worldsim.state_ids(built, host))
        self.assertIn("pulpit-against",
                      [s["id"] for s
                       in worldsim.derived_states(built, "concordia")])
        self.assertGreater(worldsim.term(built, "concordia", "goods"),
                           before)

    def test_a_war_alone_does_not_put_hounds_on_saturnas_road(self):
        """`at-war` is stamped at worldgen and never cleared, so reading
        it here made the row a standing fact in half of all worlds."""
        self.assertEqual(
            next(e["when"] for e in worldsim._GATE_RELATIONS
                 if e["kind"] == "the hunt"), ("hunt-up",))
        seen_war = False
        for seed in range(1, 13):
            built = played(seed)
            host = worldsim.gate_land(built, "saturna")
            if "at-war" not in worldsim.state_ids(built, host):
                continue
            seen_war = True
            self.assertNotIn("hounds-out",
                             [s["id"] for s
                              in worldsim.derived_states(built, "saturna")],
                             seed)
            worldsim.set_state(built, host, "hunt-up", 5)
            self.assertIn("hounds-out",
                          [s["id"] for s
                           in worldsim.derived_states(built, "saturna")],
                          seed)
        self.assertTrue(seen_war, "no rolled war reached a Hell host")

    def test_the_quarantine_shuts_the_gate_without_the_prefects_quarrel(
            self):
        """`admits` is AND across kinds, so a Concordia that rolled the
        Pruners' government but not the Prefect's quarrel could never see
        the gate shut. A second card, keyed on the constitution."""
        built = played(1)
        layer = worldsim.land_layer(built, "concordia")
        layer["tensions"] = [t for t in layer["tensions"]
                             if t != "prefect-vs-church"]
        worldsim.set_constitution(built, "concordia", "quarantine", 3)
        _quiet(built, "concordia")
        worldsim.set_constitution(built, "concordia", "quarantine", 3)
        deck = worldsim._deck(built, "concordia", "crisis",
                              layer["tensions"])
        shut = [key for key in deck
                if "gate-shut" in ((worldsim.CARDS_BY_KEY[key]["outlets"]
                                    .get("state") or {}).get("while", ()))]
        self.assertEqual(shut, ["heaven/the-gate-guarded-by-law"])
        spec = worldsim.CARDS_BY_KEY["heaven/the-gate-guarded-by-law"]
        self.assertTrue(worldsim.admits(built, "concordia", spec["admits"],
                                        weather="clear"))
        _fire(built, "concordia", "heaven/the-gate-guarded-by-law", 6)
        self.assertIn("gate-shut", worldsim.state_ids(built, "concordia"))

    def test_no_witch_hunt_at_the_prefecture(self):
        """The gift is born in villages; the two city states have none."""
        for polity in places.CITY_STATES:
            for track in worldsim.TRACKS:
                deck = worldsim._deck(world(1), polity, track)
                self.assertFalse([k for k in deck
                                  if k.startswith("magic/")],
                                 (polity, track))
        built = played(1)
        for polity in places.HUMAN_COUNTRIES:
            deck = worldsim._deck(built, polity, "crisis",
                                  worldsim.tensions_of(built, polity))
            self.assertIn("magic/wild-talent", deck, polity)
            self.assertIn("magic/the-hunt", deck, polity)


class TheGateCrowns(unittest.TestCase):
    """The Prefect and the Lord of Misrule read as an angel and a demon."""

    def test_neither_crown_is_a_decaying_mortal_body(self):
        for seed in range(1, 25):
            built = played(seed)
            for polity in places.CITY_STATES:
                sheet = worldsim.ruler_sheet(built, polity)
                self.assertFalse(set(sheet["traits"]) & rulers.BODILESS,
                                 (seed, polity, sheet["traits"]))

    def test_the_accession_is_named_not_rolled(self):
        for seed in range(1, 13):
            built = played(seed)
            self.assertEqual(
                worldsim.ruler_sheet(built, "concordia")["accession"],
                "appointed")
            self.assertEqual(
                worldsim.ruler_sheet(built, "saturna")["accession"],
                "acclaimed")

    def test_a_human_crown_still_draws_the_whole_human_pool(self):
        drawn = set()
        for seed in range(1, 25):
            built = played(seed)
            for polity in places.HUMAN_COUNTRIES:
                drawn |= set(worldsim.ruler_sheet(built, polity)["traits"])
        self.assertTrue(drawn & rulers.BODILESS)

    def test_the_epics_have_no_king_in_a_city_state(self):
        for culture in ("heaven", "hell"):
            givers = [t["giver"] for t in quests.epic_templates(culture)]
            for giver in givers:
                self.assertNotIn("king", giver, culture)
            self.assertEqual(len(givers), len(quests.EPIC_TEMPLATES))
        self.assertEqual(quests.epic_templates("western"),
                         quests.EPIC_TEMPLATES)


class TheGatePacketsAtTheTable(unittest.TestCase):
    """Everything either packet can print, ASCII and inside the column."""

    def test_every_new_line_is_ascii(self):
        built = played(1)
        lines: list[str] = []
        for polity in built["lands"]:
            lines += worldsim.lore_lines(built, polity)
            lines += worldsim.land_lines(built, polity)
            lines += worldsim.politics_lines(built, polity)
        lines += worldsim.world_lines(built)
        for line in lines:
            self.assertTrue(line.isascii(), line)

    def test_every_gate_card_says_something(self):
        for spec in worldsim.CARDS:
            if not spec["key"].startswith(("heaven/", "hell/")):
                continue
            self.assertTrue(spec["outlets"], spec["key"])
            self.assertTrue(spec["outlets"].get("news"), spec["key"])
            self.assertTrue(spec["outlets"]["news"].isascii(), spec["key"])


if __name__ == "__main__":
    unittest.main()
