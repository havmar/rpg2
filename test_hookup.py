"""The hookup's contract suite (2026-08-21, the tile economy arc's session
4 -- round 5's design plus round 4's Miners' League).

Five parts, in the order the session built them.

*The read surface*: the character line's fixed priority on the Tiles that
exercise it, the harvest words and their causes' fiction names, and both
folded into the Tile's public file inside the 40-column wrap with the
route list capped.

*The DM's brief*: one Tile's whole file, the census in full with the unmet
settlements unnamed, the four neighbours, and the DM-only half absent from
what the player reads.

*The tile menu*: the three rows, reaching `local_term` and the price
sheet, multiplying beside the land's own terms under the same clamps.

*The Miners' League*: the deposit slot back with its words and its prices,
the chain run end to end in every land, the caravan admitted on a
neighbour's failed harvest, the scrub, and the calendar rolling one day at
a time across the whole world.

*The scaffolding sweep*: the pre-Europe scaffolding provably gone, and no
constant of places.py copied into the eyeball tool.

`python -m unittest -v test_hookup.py`.
"""

from __future__ import annotations

import copy
import io
import json
import random
import re
import unittest
from contextlib import redirect_stdout
from unittest import mock

import econmap
import places
import quests
import rpg
import session
import worldsim


def _tid(row: int, column: int) -> str:
    return places.tile_id(row, column)


# The Tiles that exercise the character line's priority, by name: a mine,
# a granary, a crossroads, a fen, the two exotic doors and quiet
# wilderness. Every one of them is authored ground, so these hold in every
# world.
GOSLAR = _tid(9, 14)            # a mine (silver, copper)
NILE = _tid(18, 26)             # the Nile granary
PARIS = _tid(9, 10)             # the crossroads all the roads meet at
FENS = _tid(6, 6)               # the Fens: quiet marsh, no goods
EASTERN_GATE = _tid(11, 30)
DELTA_PORT = _tid(18, 24)
WILDWOOD = _tid(7, 24)          # the eastern wildwood: fur country


class TheReadSurface(unittest.TestCase):
    """ONE phrase and ONE word: the arc's hidden-numbers rule arriving at
    the page it was always for."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.world = places.create_geography(1)

    def test_the_character_line_follows_its_fixed_priority(self) -> None:
        world = self.world
        # the mine leads, by its FIRST metal
        self.assertEqual(places.tile_character(world, GOSLAR),
                         "silver country")
        self.assertEqual(places.tile_character(world, _tid(8, 16)),
                         "salt country")         # Luneburg
        self.assertEqual(places.tile_character(world, _tid(11, 14)),
                         "iron country")         # Erzberg
        # ...then the goods origin
        self.assertEqual(places.tile_character(world, NILE), "grain country")
        self.assertEqual(places.tile_character(world, WILDWOOD),
                         "fur country")
        # ...and the two exotic doors are PLACES, not products
        self.assertEqual(places.tile_character(world, EASTERN_GATE),
                         "the eastern gate")
        self.assertEqual(places.tile_character(world, DELTA_PORT),
                         "the delta port")
        # ...then the land itself
        self.assertEqual(places.tile_character(world, FENS), "fenland")
        self.assertEqual(places.tile_character(world, PARIS),
                         "rich farmland")
        self.assertEqual(places.tile_character(world, _tid(1, 1)),
                         "open sea")

    def test_the_mine_outranks_the_goods_the_tile_also_grows(self) -> None:
        """Falun is a copper mine AND fur country. The mine wins, which is
        the whole reason the priority is fixed."""
        falun = self.world["tiles"][_tid(3, 22)]
        self.assertEqual(falun["mine"], "Falun")
        self.assertIn("furs", falun["goods"])
        self.assertEqual(places.tile_character(self.world, falun),
                         "copper country")

    def test_every_character_phrase_is_a_legal_word(self) -> None:
        legal = set(places.TILE_CHARACTER.values())
        legal.update(phrase for _f, _v, phrase in places.LAND_CHARACTER)
        legal.update(places.TERRAINS)
        legal.add("open sea")
        for tid in self.world["tile_order"]:
            phrase = places.tile_character(self.world, tid)
            self.assertIn(phrase, legal, tid)
            self.assertTrue(phrase.isascii() and phrase == phrase.strip())

    def test_every_good_and_every_land_word_has_a_phrase(self) -> None:
        """No good can reach the reader without one, and the land table
        covers the whole authored vocabulary."""
        self.assertEqual(set(places.TILE_CHARACTER), set(places.GOODS))
        fields = {"cover", "terrain", "climate", "tag"}
        for field, value, phrase in places.LAND_CHARACTER:
            self.assertIn(field, fields)
            self.assertTrue(phrase)
            if field == "terrain":
                self.assertIn(value, places.TERRAINS)
            elif field == "climate":
                self.assertIn(value, places.CLIMATES)
            elif field == "cover":
                self.assertIn(value, places.PINNED_COVER_COUNTS)

    def test_the_harvest_speaks_a_word_and_never_the_percent(self) -> None:
        self.assertEqual(places.harvest_word(115), "legendary")
        self.assertEqual(places.harvest_word(100), "excellent")
        self.assertEqual(places.harvest_word(95), "excellent")
        self.assertEqual(places.harvest_word(94), "ordinary")
        self.assertEqual(places.harvest_word(74), "poor")
        self.assertEqual(places.harvest_word(54), "failed")
        self.assertEqual(places.harvest_word(34), "apocalyptic")
        self.assertIsNone(places.harvest_word(None))
        for tid in self.world["tile_order"]:
            tile = self.world["tiles"][tid]
            line = places.harvest_line(self.world, tile)
            if tile["biome"] == "sea":
                self.assertIsNone(line, tid)
                continue
            self.assertTrue(line.startswith("last harvest: "), tid)
            self.assertNotRegex(line, r"\d")

    def test_the_causes_read_by_their_fiction_names(self) -> None:
        self.assertEqual(set(places.HARVEST_CAUSE_LINES),
                         set(places.SUSCEPTIBILITY))
        self.assertEqual(places.HARVEST_CAUSE_LINES["drought"],
                         "the drought")
        self.assertEqual(places.HARVEST_CAUSE_LINES["rains"],
                         "the great rains")
        self.assertEqual(places.HARVEST_CAUSE_LINES["frost"],
                         "the black frost")

    def test_the_nile_calls_the_failed_rains_a_low_flood(self) -> None:
        """On the Nile the failure of the rains is the failure of the
        FLOOD, and the delta says so in its own words."""
        world = places.create_geography(2)
        nile = dict(world["tiles"][NILE])
        self.assertEqual(nile["climate"], "nile")
        nile.update(harvest=48, harvest_cause="rains")
        self.assertEqual(places.harvest_line(world, nile),
                         "last harvest: failed -- the low Nile")
        elsewhere = dict(world["tiles"][PARIS])
        elsewhere.update(harvest=48, harvest_cause="rains")
        self.assertEqual(places.harvest_line(world, elsewhere),
                         "last harvest: failed -- the great rains")

    def test_the_tiles_public_file_carries_both_new_lines(self) -> None:
        lines = places.tile_detail_lines(self.world, GOSLAR)
        self.assertEqual(lines[1], "  silver country")
        self.assertTrue(any(line.startswith("  last harvest: ")
                            for line in lines))
        self.assertIn("  mine: Goslar", lines)

    def test_a_quiet_tile_still_says_what_it_is_and_what_it_ate(self
                                                                ) -> None:
        lines = places.tile_detail_lines(self.world, FENS, areas=False)
        self.assertEqual(lines[0].split(" -- ")[1], "Phyrascia, marsh")
        self.assertEqual(lines[1], "  fenland")
        self.assertTrue(any("last harvest" in line for line in lines))
        self.assertFalse(any("mine:" in line or "goods:" in line
                             for line in lines))

    def test_the_sea_says_nothing_it_has_no_business_saying(self) -> None:
        lines = places.tile_detail_lines(self.world, _tid(1, 1))
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].endswith("sea"))

    def test_the_character_line_never_repeats_the_ground_word(self
                                                              ) -> None:
        """A bare terrain word falls through to itself and the header has
        already said it. Read unwrapped, so a continuation line cannot be
        mistaken for the character line."""
        repeats = spoken = 0
        for tid in self.world["tile_order"]:
            tile = self.world["tiles"][tid]
            ground = places.tile_ground(tile)
            character = places.tile_character(self.world, tile)
            lines = places.tile_detail_lines(self.world, tid, areas=False,
                                             width=200)
            self.assertNotIn(f"  {ground}", lines, tid)
            if character == ground or tile["biome"] == "sea":
                repeats += 1
            else:
                self.assertEqual(lines[1], f"  {character}", tid)
                spoken += 1
        self.assertTrue(repeats and spoken)

    def test_the_route_list_is_capped_and_the_named_roads_lead(self
                                                               ) -> None:
        """Paris carries a dozen roads and a phone page carries four."""
        routes = places.tile_routes(self.world, PARIS)
        self.assertGreater(len(routes), places.ROUTE_LINES)
        lines = places.route_lines(self.world, PARIS,
                                   limit=places.ROUTE_LINES)
        self.assertEqual(len(lines), places.ROUTE_LINES + 1)
        self.assertEqual(lines[-1],
                         f"+{len(routes) - places.ROUTE_LINES} more")
        named = [route["name"] for route in routes if route["name"]]
        self.assertTrue(named)
        self.assertTrue(lines[0].startswith(named[0]))
        # and uncapped it is the whole list in the world's own order
        whole = places.route_lines(self.world, PARIS)
        self.assertEqual(len(whole), len(routes))
        self.assertEqual(whole[0], places.route_line(self.world, routes[0]))

    def test_a_short_route_list_is_never_capped(self) -> None:
        for tid in self.world["tile_order"]:
            routes = places.tile_routes(self.world, tid)
            if len(routes) <= places.ROUTE_LINES:
                lines = places.route_lines(self.world, tid,
                                           limit=places.ROUTE_LINES)
                self.assertEqual(len(lines), len(routes), tid)
                self.assertFalse(any("more" == line[-4:] for line in lines))

    def test_an_unspeakable_tile_raises_where_it_is_made(self) -> None:
        """One broken world per clause the session added to
        `validate_world`. The failure this catches is a KeyError inside a
        display, mid-play, so it has to raise at creation instead."""
        def broken(mutate):
            world = copy.deepcopy(self.world)
            mutate(world)
            with self.assertRaises(ValueError):
                places.validate_world(world)

        def a_good_with_no_phrase(world):
            _land(world)["goods"] = ["moonstone"]
            places.GOODS = places.GOODS + ("moonstone",)

        def a_harvest_off_the_scale(world):
            _land(world)["harvest"] = None

        def a_cause_with_no_name(world):
            _land(world)["harvest_cause"] = "locusts"

        for mutate in (a_good_with_no_phrase, a_harvest_off_the_scale,
                       a_cause_with_no_name):
            with self.subTest(mutate.__name__):
                goods = places.GOODS
                try:
                    broken(mutate)
                finally:
                    places.GOODS = goods

    def test_the_whole_public_file_fits_the_forty_column_page(self) -> None:
        for tid in self.world["tile_order"]:
            for line in places.tile_detail_lines(self.world, tid):
                self.assertLessEqual(len(line), 40, (tid, line))
                self.assertTrue(line.isascii(), (tid, line))


class TheDMsBrief(unittest.TestCase):
    """What `lore` is to a land, `tile` is to a Tile."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.world = quests.generate_world(19)

    def _brief(self, tid: str) -> list[str]:
        return places.tile_brief_lines(self.world, tid)

    def test_the_brief_is_the_whole_file(self) -> None:
        lines = self._brief(GOSLAR)
        tile = self.world["tiles"][GOSLAR]
        self.assertTrue(lines[0].startswith("TILE "))
        self.assertIn("Teutonia", lines[0])
        # the header: terrain / climate / cover
        self.assertEqual(lines[1], f"  {tile['terrain']} / {tile['climate']}"
                                   f" / {tile['cover']}")
        self.assertEqual(lines[2], "  silver country")
        body = "\n".join(lines)
        for wanted in ("last harvest: ", "mine: Goslar (silver, copper)",
                       "goods: silver, copper", "roads:", "census:",
                       "neighbours:"):
            self.assertIn(wanted, body, wanted)

    def test_the_brief_prints_every_road_uncapped(self) -> None:
        lines = self._brief(PARIS)
        roads = places.tile_routes(self.world, PARIS)
        self.assertGreater(len(roads), places.ROUTE_LINES)
        start = lines.index("  roads:")
        drawn = [line for line in lines[start + 1:] if line.startswith("    ")]
        self.assertNotIn("    +", "".join(drawn))
        # the wrap can split a long road line, so count the ROADS by name
        for route in roads:
            head = places.route_line(self.world, route).split(":")[0]
            self.assertIn(head, "\n".join(drawn), head)

    def test_an_unmet_settlement_is_named_by_its_tier_and_never_by_name(
            self) -> None:
        world = self.world
        tile = next(world["tiles"][tid] for tid in world["tile_order"]
                    if len(world["tiles"][tid]["settlement_slots"]) >= 2
                    and not world["tiles"][tid]["visited"])
        lines = places.tile_brief_lines(world, tile)
        slots = [world["settlement_slots"][sid]
                 for sid in tile["settlement_slots"]]
        body = "\n".join(lines)
        for slot in slots:
            self.assertIsNone(slot["area"])
            self.assertIn(f"a {slot['tier']} (unmet)", body)
        # ...and once it IS met, it is named
        places.reveal_tile(world, tile, day=1)
        lines = places.tile_brief_lines(world, tile, width=200)
        census = lines[lines.index("  census:") + 1:
                       lines.index("  neighbours:")]
        for sid in tile["settlement_slots"]:
            area = world["areas"][world["settlement_slots"][sid]["area"]]
            self.assertTrue(any(area["name"] in line for line in census),
                            area["name"])
        self.assertNotIn("(unmet)", "\n".join(census))

    def test_the_census_marks_the_charter_the_manor_and_a_quiet_board(
            self) -> None:
        world = self.world
        paris = world["settlement_slots"][
            world["tiles"][PARIS]["settlement_slots"][0]]
        self.assertEqual((paris["capital"], paris["charter"]),
                         (True, "free"))
        self.assertIn("    metropolis Paris -- CAPITAL, free",
                      places.tile_brief_lines(world, PARIS))
        manor = next(world["tiles"][tid] for tid in world["tile_order"]
                     if world["tiles"][tid]["settlement_slots"]
                     and world["settlement_slots"][
                         world["tiles"][tid]["settlement_slots"][0]]["manor"])
        self.assertIn("manor", "\n".join(places.tile_brief_lines(world,
                                                                 manor)))
        quiet = next(area for area in world["areas"].values()
                     if area["kind"] == "settlement"
                     and not area.get("board_active"))
        self.assertIn("board quiet",
                      "\n".join(places.tile_brief_lines(world,
                                                        quiet["tile"])))

    def test_an_empty_tile_says_so(self) -> None:
        world = self.world
        empty = next(tid for tid in world["tile_order"]
                     if world["tiles"][tid]["biome"] != "sea"
                     and not world["tiles"][tid]["settlement_slots"])
        self.assertIn("  census: empty", places.tile_brief_lines(world,
                                                                empty))

    def test_the_neighbour_line_marks_unmet_with_the_article(self) -> None:
        """`a village` against `village Erkhet`. The census block says
        `(unmet)` in full; the neighbour line cannot afford the eight
        characters -- with them, seven of these lines in ten wrapped."""
        world = self.world
        unmet = next(world["tiles"][tid] for tid in world["tile_order"]
                     if world["tiles"][tid]["settlement_slots"]
                     and not world["tiles"][tid]["visited"])
        line = places._neighbour_line(world, unmet)
        tier = world["settlement_slots"][
            unmet["settlement_slots"][0]]["tier"]
        self.assertIn(f", a {tier}", line)
        self.assertNotIn("(unmet)", line)
        paris = world["tiles"][PARIS]
        self.assertIn(", metropolis Paris",
                      places._neighbour_line(world, paris))
        # ...and the whole neighbours block stays one line per neighbour
        # on the great majority of Tiles
        wrapped = total = 0
        for tid in world["tile_order"]:
            tile = world["tiles"][tid]
            if tile["biome"] == "sea":
                continue
            for direction in places.DIRECTIONS:
                nid = places.neighbor_id(tile, direction)
                if nid is None:
                    continue
                total += 1
                head = f"    {direction[0].upper()} "
                wrapped += len(head + places._neighbour_line(
                    world, world["tiles"][nid])) > 40
        self.assertLess(wrapped / total, 0.30, f"{wrapped}/{total} wrap")

    def test_the_four_neighbours_each_get_a_line(self) -> None:
        world = self.world
        lines = places.tile_brief_lines(world, PARIS)
        start = lines.index("  neighbours:")
        heads = [line for line in lines[start + 1:]
                 if re.match(r"^    [NWES] ", line)]
        self.assertEqual(len(heads), 4)
        for direction in places.DIRECTIONS:
            nid = places.neighbor_id(PARIS, direction)
            neighbour = world["tiles"][nid]
            head = f"    {direction[0].upper()} {places.tile_label(neighbour)}"
            self.assertTrue(any(line.startswith(head) for line in heads),
                            direction)
            self.assertIn(places.tile_character(world, neighbour),
                          "\n".join(lines))

    def test_the_frames_edge_has_fewer_than_four_neighbours(self) -> None:
        lines = places.tile_brief_lines(self.world, _tid(1, 1))
        self.assertEqual(lines, ["TILE R01C01 -- Phyrascia", "  open sea"])
        corner = places.tile_brief_lines(self.world, _tid(18, 30))
        heads = [line for line in corner if re.match(r"^    [NWES] ", line)]
        self.assertEqual(len(heads), 2)

    def test_a_neighbours_harvest_shows_only_where_it_is_a_problem(self
                                                                   ) -> None:
        """The DM is narrating TOWARD the next Tile, not running a scene on
        it: a fine year there is not news."""
        world = self.world
        shown = hidden = 0
        for tid in world["tile_order"]:
            neighbour = world["tiles"][tid]
            if neighbour["harvest"] is None:
                continue
            line = places._neighbour_line(world, neighbour)
            word = places.harvest_word(neighbour["harvest"])
            if neighbour["harvest"] < places.HARVEST_PROBLEM:
                self.assertIn(f"harvest {word}", line)
                shown += 1
            else:
                self.assertNotIn("harvest", line)
                hidden += 1
        self.assertTrue(shown and hidden)
        # ...and the line the brief prints IS that line
        lines = places.tile_brief_lines(world, PARIS, width=200)
        for direction in places.DIRECTIONS:
            nid = places.neighbor_id(PARIS, direction)
            self.assertIn(f"    {direction[0].upper()} "
                          f"{places._neighbour_line(world, world['tiles'][nid])}",
                          lines)

    def test_the_dm_only_half_never_reaches_the_players_page(self) -> None:
        """The brief carries the unmet census, the cover word and the
        neighbours. The player's detail block carries none of them."""
        world = self.world
        tile = next(world["tiles"][tid] for tid in world["tile_order"]
                    if world["tiles"][tid]["settlement_slots"]
                    and not world["tiles"][tid]["visited"])
        page = "\n".join(places.tile_detail_lines(world, tile))
        self.assertNotIn("(unmet)", page)
        self.assertNotIn("neighbours", page)
        self.assertNotIn("census", page)
        brief = "\n".join(places.tile_brief_lines(world, tile))
        self.assertIn("(unmet)", brief)
        self.assertIn("neighbours:", brief)

    def test_the_brief_fits_the_page_and_is_ascii(self) -> None:
        for tid in self.world["tile_order"]:
            for line in places.tile_brief_lines(self.world, tid):
                self.assertLessEqual(len(line), 40, (tid, line))
                self.assertTrue(line.isascii(), (tid, line))

    def test_the_verb_is_registered_beside_world_and_lore(self) -> None:
        parser = session.build_parser()
        names = set(parser._subparsers._group_actions[0].choices)
        self.assertTrue({"tile", "world", "lore"} <= names)
        args = parser.parse_args(["tile", "R09C10"])
        self.assertEqual((args.func, args.coordinate),
                         (session.cmd_tile, ["R09C10"]))
        self.assertEqual(parser.parse_args(["tile"]).coordinate, [])

    def test_the_verb_defaults_to_here_and_takes_any_coordinate(self
                                                                ) -> None:
        world = self.world
        state = _standing_in(world, _settlement(world, "Paris"))
        here, _saved = _run(session.cmd_tile, state, coordinate=[])
        self.assertIn("TILE Paris (R09C10)", here)
        state = _standing_in(world, _settlement(world, "Rome"))
        there, _saved = _run(session.cmd_tile, state, coordinate=["R09C14"])
        self.assertIn("TILE R09C14", there)
        self.assertIn("mine: Goslar", there)
        refused, _saved = _run(session.cmd_tile, state, coordinate=["Goslar"])
        self.assertIn("not a coordinate", refused)
        beyond, _saved = _run(session.cmd_tile, state, coordinate=["R25C31"])
        self.assertIn("off the map", beyond)

    def test_the_verb_costs_no_day_and_writes_nothing(self) -> None:
        world = self.world
        state = _standing_in(world, _settlement(world, "Paris"))
        before = json.dumps(world, sort_keys=True)
        _output, saved = _run(session.cmd_tile, state, coordinate=["R09C14"])
        self.assertEqual(saved, [])
        self.assertEqual(state["clock"].day, 3)
        self.assertEqual(json.dumps(world, sort_keys=True), before)


class TheTileMenu(unittest.TestCase):
    """The integration minimum: the ground under the party on the shelf,
    beside what the land's world layer is doing."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.world = quests.generate_world(1)

    def test_the_three_rows_and_nothing_else(self) -> None:
        self.assertEqual(set(places.TILE_MENU),
                         {"grain", "mine", "crossroads"})
        self.assertEqual(places.TILE_MENU["grain"], {"lodging": 0.90})
        self.assertEqual(places.TILE_MENU["mine"], {"steel": 0.90})
        self.assertEqual(places.TILE_MENU["crossroads"],
                         {"goods": 0.95, "lodging": 1.10})
        for row in places.TILE_MENU.values():
            for name in row:
                self.assertIn(name, worldsim.MENU_TERMS)
            # the road's own charges stay the snapshot arc's business
            self.assertNotIn("toll", row)
            self.assertNotIn("ferry", row)

    def test_the_granary_the_pithead_and_the_crossroads(self) -> None:
        world = self.world
        self.assertEqual(places.tile_terms(world, NILE), {"lodging": 0.90})
        crossroads = places.tile_terms(world, PARIS)
        self.assertEqual(crossroads, {"goods": 0.95, "lodging": 1.10})
        mine = places.tile_terms(world, GOSLAR)
        self.assertEqual(mine["steel"], 0.90)
        self.assertEqual(places.tile_terms(world, FENS), {})

    def test_the_rows_multiply_where_a_tile_earns_two(self) -> None:
        world = self.world
        wanted = [tid for tid in world["tile_order"]
                  if "grain" in world["tiles"][tid]["goods"]
                  and len(places.tile_routes(world, tid))
                  >= places.CROSSROADS_ROUTES]
        self.assertTrue(wanted)
        terms = places.tile_terms(world, wanted[0])
        self.assertAlmostEqual(terms["lodging"], 0.90 * 1.10)

    def test_a_crossroads_is_two_roads_meeting(self) -> None:
        world = self.world
        for tid in world["tile_order"]:
            crossing = len(places.tile_routes(world, tid))
            terms = places.tile_terms(world, tid)
            self.assertEqual(crossing >= places.CROSSROADS_ROUTES,
                             terms.get("goods") == 0.95, tid)

    def test_the_shop_multiplies_the_land_by_the_ground(self) -> None:
        world = quests.generate_world(1)
        paris = _settlement(world, "Paris")
        state = _standing_in(world, paris)
        land = worldsim.term(world, paris["land"], "lodging")
        self.assertAlmostEqual(session.local_term(state, "lodging"),
                               land * 1.10)
        self.assertAlmostEqual(session.local_prices(state)["goods"],
                               worldsim.term(world, paris["land"], "goods")
                               * 0.95)

    def test_the_product_is_clamped_like_every_other_term(self) -> None:
        world = quests.generate_world(1)
        paris = _settlement(world, "Paris")
        state = _standing_in(world, paris)
        # four bad states stacking on lodging, then the crossroads on top
        for state_id in ("harvest-failed", "grain-scarce", "royal-progress",
                         "drought"):
            worldsim.set_state(world, paris["land"], state_id, 1)
        self.assertEqual(session.local_term(state, "lodging"),
                         worldsim.MENU_CEILING)
        self.assertLessEqual(session.local_prices(state)["lodging"],
                             worldsim.MENU_CEILING)

    def test_the_price_sheet_says_what_the_ground_is_doing(self) -> None:
        world = quests.generate_world(1)
        paris = _settlement(world, "Paris")
        state = _standing_in(world, paris)
        lines = session.tile_price_lines(state)
        self.assertIn("-- and what this ground charges --", lines[0])
        self.assertTrue(any("the shop shelf: down x0.95" in line
                            for line in lines))
        quiet = next(tid for tid in world["tile_order"]
                     if not places.tile_terms(world, tid))
        state["position"] = dict(state["position"], tile=quiet)
        self.assertEqual(session.tile_price_lines(state), [])

    def test_nothing_about_the_tile_menu_is_stored(self) -> None:
        """Static and derived: the granary and the pithead are facts of the
        map, so a save carries no trace of them."""
        world = self.world
        before = json.dumps(world, sort_keys=True)
        for tid in world["tile_order"][:80]:
            places.tile_terms(world, tid)
        self.assertEqual(json.dumps(world, sort_keys=True), before)


class TheMinersLeague(unittest.TestCase):
    """The old world's extraction chain, re-homed onto a map that finally
    has mines on it."""

    KEYS = ("mining/new-seam", "mining/gold-rush", "mining/vein-dries",
            "mining/veins-reopened", "mining/strike",
            "mining/food-caravan")

    @staticmethod
    def _card(key: str) -> dict:
        return next(c for c in worldsim.CARDS if c["key"] == key)

    def test_the_deposit_slot_is_back_with_its_words_and_its_prices(self
                                                                    ) -> None:
        self.assertEqual(worldsim.STATE_SLOTS["deposit"],
                         ("deposit-normal", "deposit-found",
                          "deposit-drying"))
        for member in worldsim.STATE_SLOTS["deposit"]:
            self.assertIn(member, worldsim.STATE_WORDS)
            self.assertEqual(worldsim.SLOT_OF[member], "deposit")
        self.assertEqual(worldsim.STATE_MENU["deposit-drying"],
                         {"steel": 1.20})
        self.assertEqual(worldsim.STATE_MENU["deposit-found"],
                         {"steel": 0.85})

    def test_six_cards_reach_every_land(self) -> None:
        for key in self.KEYS:
            card = self._card(key)
            self.assertEqual(card["land"], (worldsim.ANY_LAND,))
            for polity in places.COUNTRIES:
                self.assertTrue(worldsim.in_land(card, polity),
                                (key, polity))

    def test_the_scrub_left_no_dwarf_behind(self) -> None:
        gone = re.compile(r"\b(dwarf|dwarves|dwarven|clan|clans|thane|"
                          r"under-thane|dvarvengrond)\b", re.I)
        for key in self.KEYS:
            card = self._card(key)
            for text in _strings(card):
                self.assertIsNone(gone.search(text), (key, text))
        for entry in worldsim.FACTS:
            if entry["key"].startswith("league") or entry["key"] == "knockers":
                self.assertIsNone(gone.search(entry["line"]), entry["key"])

    def test_the_kept_mining_language_is_still_there(self) -> None:
        """The claim-keeper, the company shop, the winding gear and the pit
        bosses were period human mining words all along."""
        body = "\n".join(text for key in self.KEYS
                         for text in _strings(self._card(key)))
        for kept in ("claim-keeper", "company shop", "winding gear",
                     "Pit Boss", "Claim-Jumper", "jumped", "caravan master"):
            self.assertIn(kept, body, kept)
        self.assertIn("MINERS' LEAGUE", "\n".join(
            entry["title"] for entry in worldsim.FACTS))

    def test_the_toughs_are_the_standard_human_pool(self) -> None:
        for key in self.KEYS:
            posted = (self._card(key)["outlets"].get("quest") or {}).get("post")
            if posted:
                self.assertEqual(posted["pool"], worldsim._TOUGHS, key)

    def test_the_knockers_came_back_word_for_word(self) -> None:
        knockers = next(f for f in worldsim.FACTS if f["key"] == "knockers")
        self.assertEqual(knockers["land"], (worldsim.ANY_LAND,))
        self.assertEqual(
            knockers["line"],
            "The mine-spirits knock before a collapse and are paid for it: "
            "the last bite of every meal, left at the working face. "
            "Whistling underground is forbidden. Skeptics exist; they are "
            "assigned the unluckiest shifts.")
        for polity in places.COUNTRIES:
            self.assertIn(knockers, worldsim.FACTS_BY_LAND[polity])

    def test_every_land_has_a_league_fact_naming_its_own_mines(self
                                                               ) -> None:
        """Five of the nine hold pits, and each of those has a League
        chapter fact naming ITS OWN mines and no others. A land with no
        pits keeps no chapter."""
        mines: dict[str, list[str]] = {}
        world = places.create_geography(1)
        for (row, column), (name, _goods) in places.MINES.items():
            tile = world["tiles"][places.tile_id(row, column)]
            mines.setdefault(tile["country"], []).append(name)
        self.assertEqual(len(mines), 5)
        for polity in places.COUNTRIES:
            entry = next((f for f in worldsim.FACTS_BY_LAND[polity]
                          if f["key"] == f"league-{polity}"), None)
            if polity not in mines:
                self.assertIsNone(entry, polity)
                continue
            self.assertIsNotNone(entry, polity)
            for name in mines[polity]:
                self.assertIn(name, entry["line"], (polity, name))
            for other, names in mines.items():
                if other == polity:
                    continue
                for name in names:
                    self.assertNotIn(name, entry["line"], (polity, name))

    def test_the_rush_chain_runs_and_closes(self) -> None:
        """seam -> rush: the find sets the slot AND the argument, and the
        bust puts the slot back and settles the argument, so the chain can
        run again next year."""
        for polity in places.COUNTRIES:
            world = quests.generate_world(5)
            rng = random.Random(4)
            worldsim.set_wealth(world, polity, "normal", 1)
            _all_quiet(world, polity)
            seam = self._card("mining/new-seam")
            self.assertTrue(worldsim.admits(world, polity, seam["admits"]))
            worldsim._fire(world, polity, seam, 2, rng)
            held = worldsim.state_ids(world, polity)
            self.assertIn("deposit-found", held)
            self.assertIn("claims-collide", held)
            self.assertFalse(worldsim.admits(world, polity, seam["admits"]))
            rush = self._card("mining/gold-rush")
            self.assertTrue(worldsim.admits(world, polity, rush["admits"]))
            worldsim._fire(world, polity, rush, 5, rng)
            held = worldsim.state_ids(world, polity)
            self.assertIn("deposit-normal", held)
            self.assertNotIn("claims-collide", held)
            self.assertNotIn("deposit-found", held)
            worldsim.roll_land(world, polity, 40)   # the rush's clock runs out
            self.assertNotIn("rush-on", worldsim.state_ids(world, polity))
            self.assertNotIn("claims-collide",
                             worldsim.state_ids(world, polity))
            # ...and the seam can be found again. Whatever else the land's
            # own deck drew in those forty days is not this chain's
            # business, so it is put back to quiet first.
            _all_quiet(world, polity)
            worldsim.set_wealth(world, polity, "normal", 41)
            self.assertTrue(worldsim.admits(world, polity, seam["admits"]))

    def test_the_bust_chain_runs_both_ways(self) -> None:
        for polity in places.COUNTRIES:
            world = quests.generate_world(6)
            rng = random.Random(4)
            _all_quiet(world, polity)
            worldsim.set_wealth(world, polity, "normal", 1)
            dries = self._card("mining/vein-dries")
            self.assertTrue(worldsim.admits(world, polity, dries["admits"]))
            worldsim._fire(world, polity, dries, 2, rng)
            self.assertEqual(worldsim.wealth_of(world, polity), "crisis")
            self.assertIn("deposit-drying",
                          worldsim.state_ids(world, polity))
            self.assertGreater(worldsim.term(world, polity, "steel"), 1.0)
            reopened = self._card("mining/veins-reopened")
            self.assertTrue(worldsim.admits(world, polity,
                                            reopened["admits"]))
            worldsim._fire(world, polity, reopened, 9, rng)
            self.assertEqual(worldsim.wealth_of(world, polity), "normal")
            self.assertIn("deposit-normal",
                          worldsim.state_ids(world, polity))

    def test_the_strike_wants_a_crisis_and_makes_steel_dear(self) -> None:
        world = quests.generate_world(8)
        polity = "phyrascia"
        _all_quiet(world, polity)
        strike = self._card("mining/strike")
        worldsim.set_wealth(world, polity, "normal", 1)
        self.assertFalse(worldsim.admits(world, polity, strike["admits"]))
        worldsim.set_wealth(world, polity, "crisis", 1)
        self.assertTrue(worldsim.admits(world, polity, strike["admits"]))
        worldsim._fire(world, polity, strike, 2, random.Random(1))
        self.assertIn("strike", worldsim.state_ids(world, polity))
        self.assertGreater(worldsim.term(world, polity, "steel"), 1.30)

    def test_the_caravan_is_admitted_on_a_neighbours_failed_harvest(self
                                                                    ) -> None:
        """The one card in the family that cannot fire on its own: it takes
        somebody ELSE's grain failing, and the relation is the road."""
        world = quests.generate_world(9)
        caravan = self._card("mining/food-caravan")
        source, target = next((edge["from"], edge["to"])
                              for edge in worldsim.RELATIONS
                              if edge["then"] == "grain-scarce")
        _all_quiet(world, target)
        self.assertFalse(worldsim.admits(world, target, caravan["admits"]))
        worldsim.set_state(world, source, "harvest-failed", 2)
        self.assertIn("grain-scarce", worldsim.state_ids(world, target))
        self.assertTrue(worldsim.admits(world, target, caravan["admits"]))

    def test_the_league_actually_fires_in_a_world_left_alone(self) -> None:
        seen = set()
        for seed in range(6):
            world = quests.generate_world(400 + seed)
            worldsim.roll_world(world, 400)
            for polity in world["lands"]:
                for record in worldsim.land_layer(world, polity)["drawn"]:
                    if record["key"].startswith("mining/"):
                        seen.add(record["key"])
        self.assertTrue(seen, "no League card fired in six long worlds")

    def test_the_calendar_moves_the_whole_world_one_day_at_a_time(self
                                                                  ) -> None:
        """A card that admits on a DERIVED state reads another land, so a
        world caught up in one jump has to be the world that was watched.
        Before 2026-08-21 `roll_world` ran each land to the target day in
        turn and the two histories parted."""
        watched, ignored = quests.generate_world(4471), \
            quests.generate_world(4471)
        for day in range(1, 121):
            worldsim.roll_world(watched, day)
        worldsim.roll_world(ignored, 120)
        for polity in watched["lands"]:
            self.assertEqual(worldsim.land_layer(ignored, polity),
                             worldsim.land_layer(watched, polity), polity)
            self.assertEqual(ignored["lands"][polity]["states"],
                             watched["lands"][polity]["states"], polity)


class TheScaffoldingSweep(unittest.TestCase):
    """The pre-Europe scaffolding is GONE -- not filtered, not unused:
    absent. In the removed-peoples sweep's manner."""

    DEAD_NAMES = ("ENVIRONMENT_PROFILES", "SETTLEMENT_DENSITY",
                  "_population_slots")

    def test_no_runtime_module_defines_the_dead_names(self) -> None:
        for module in (places, quests, session, worldsim, econmap, rpg):
            for name in self.DEAD_NAMES:
                self.assertFalse(hasattr(module, name),
                                 (module.__name__, name))

    def test_the_catalog_has_no_environment_key_and_no_old_census(self
                                                                  ) -> None:
        for polity, land in places.LAND_SPECS.items():
            self.assertNotIn("environment", land, polity)
            for dead in places.OBSOLETE_LAND_KEYS:
                self.assertNotIn(dead, land, (polity, dead))
        for dead in places.OBSOLETE_CATALOG_KEYS:
            self.assertNotIn(dead, places._CATALOG, dead)

    def test_prairie_is_gone_from_every_runtime_table(self) -> None:
        prairie = re.compile(r"\bprairie\b", re.I)
        for table in (places._CATALOG, places.AREA_SPECS,
                      places.NATURAL_SITE_SPECS,
                      places.SETTLEMENT_SITE_SPECS,
                      places.ROOM_CONTENT_POOLS, quests.TEMPLATES,
                      worldsim.CARDS, worldsim.FACTS):
            for text in _strings(table):
                self.assertIsNone(prairie.search(text), text)
        for name in ("dm.md", "writing.md", "scene-example.md", "rules.md"):
            with open(name, encoding="utf-8") as handle:
                self.assertIsNone(prairie.search(handle.read()), name)

    def test_no_area_wears_a_bare_biome_tag(self) -> None:
        """`basic` and `mountain` are DRAWING words for the base map. What
        ground a place stands on is its terrain word."""
        world = quests.generate_world(31)
        for tid in [t for t in world["tile_order"]
                    if world["tiles"][t]["settlement_slots"]][:60]:
            places.reveal_tile(world, tid, day=1)
        for area in world["areas"].values():
            self.assertNotIn("basic", area["tags"], area["id"])
            self.assertNotIn("mountain", area["tags"], area["id"])
        for tile in world["tiles"].values():
            self.assertNotIn("basic", tile["tags"], tile["id"])
            self.assertNotIn("mountain", tile["tags"], tile["id"])

    def test_the_eyeball_tool_keeps_no_copy_of_a_shipped_constant(self
                                                                  ) -> None:
        """One authority per constant, at the end of the arc: econmap draws
        a built world and authors nothing."""
        with open("econmap.py", encoding="utf-8") as handle:
            source = handle.read()
        for name in ("CLIMATE_ARABLE", "TERRAIN_ARABLE", "FOREST_CAP",
                     "GRAZE_CLIMATE", "CLEARANCE_K", "HARVEST_SPREAD",
                     "SUSCEPTIBILITY", "ARRANGEMENTS", "GOOD_ROUTES",
                     "LEGENDARY", "MINES", "BANDS", "TIERS"):
            self.assertNotRegex(source, rf"(?m)^{name} = (?!places\.)",
                                name)
        self.assertNotIn("def _single_source", source)
        self.assertNotIn("def roll_harvest", source)
        self.assertNotIn("def roll_census", source)
        self.assertNotIn("def roll_routes", source)
        self.assertNotIn("def sweep_", source)

    def test_the_tool_renders_a_built_world_in_every_mode(self) -> None:
        world = places.create_geography(3)
        renders = dict(econmap.MODES, climate=econmap.render_climate)
        for name, render in renders.items():
            out = io.StringIO()
            with redirect_stdout(out):
                if render in (econmap.render_terrain,
                              econmap.render_potential,
                              econmap.render_climate):
                    render(world)
                else:
                    render(world, 3)
            self.assertTrue(out.getvalue().strip(), name)
            self.assertTrue(out.getvalue().isascii(), name)
        # ...and the lint still reads the FILES, because a half-drawn
        # overlay is the one case no world can be built from
        econmap.run_lint()


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def _land(world: dict) -> dict:
    return next(tile for tile in world["tiles"].values()
                if tile["biome"] != "sea")


def _strings(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _strings(key)
            yield from _strings(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, str):
        yield value


def _all_quiet(world: dict, polity: str) -> None:
    """A land with nothing standing over it: the League's admits are what
    is being read, not whatever the deck happened to draw."""
    layer = worldsim.land_layer(world, polity)
    world["lands"][polity]["states"] = []
    for track in worldsim.TRACKS:
        layer[worldsim.LIVE_KEY[track]] = None


def _standing_in(world: dict, area: dict) -> dict:
    """The party stood in one Area, without a save on disk. Everything the
    price readers ask for and nothing else -- `save.json` belongs to
    whatever playthrough the designer has running."""
    return {"world": world, "position": session._area_position(area),
            "clock": rpg.Clock(day=3)}


def _settlement(world: dict, name: str) -> dict:
    return next(area for area in world["areas"].values()
                if area["kind"] == "settlement" and area.get("name") == name)


def _run(command, state: dict, **kwargs) -> str:
    """One session verb, driven against `state` instead of the save."""
    out = io.StringIO()
    saves = []
    with mock.patch.object(session, "load", lambda: state), \
            mock.patch.object(session, "save", saves.append), \
            redirect_stdout(out):
        command(_Args(**kwargs))
    return out.getvalue(), saves


class _Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


if __name__ == "__main__":
    unittest.main()
