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


if __name__ == "__main__":
    unittest.main()
