"""The trade network's contract suite (2026-08-21, the tile economy arc's
session 3).

Four parts. *The authored half*: the nine mines with their towns, goods and
tags, the authored colour and the exotic doors, the five legendary roads by
name with their endpoints and cargo -- all identical in every campaign.
*The derived half*: the produce origins by law over sessions 1-2's numbers,
the region minimum with grain exempt, and the pinned sweep (~59 routes,
~114 land tiles on a route, 27 ports). *The routes themselves*: well-formed
records end to end, the merge on shared endpoints, the sea rule and its
ports, the grain roads with Falun pinned unfed, and the save round-trip.
*The label*: the mine, goods and route lines on the Tiles that own them,
inside the 40-column wrap, and one broken world per clause the session
added to `validate_world`.

`python -m unittest -v test_trade.py`
"""

from __future__ import annotations

import copy
import json
import unittest
from collections import Counter

import places

SWEEP = 40          # worlds a distribution test builds (~60ms each). The
                    # 100-seed pins live in benchlog.md until session 4's
                    # bench_worldgen.py takes the sweeps over.


def _world(seed: int = 5) -> dict:
    return places.create_geography(seed)


def _land(world: dict) -> list[dict]:
    return [t for t in world["tiles"].values() if t["biome"] != "sea"]


def _tagged(world: dict, tag: str) -> set[str]:
    return {tid for tid, tile in world["tiles"].items()
            if tag in tile["tags"]}


# --------------------------------------------------------------------------- #
# A. The authored half: the mines, the colour and the legendary roads
# --------------------------------------------------------------------------- #

class TheAuthoredHalf(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.world = _world()

    def test_the_nine_mines_carry_their_town_goods_and_tag(self) -> None:
        self.assertEqual(len(places.MINES), 9)
        for (row, column), (name, goods) in places.MINES.items():
            tile = self.world["tiles"][places.tile_id(row, column)]
            self.assertEqual(tile["mine"], name, name)
            self.assertIn("mine", tile["tags"], name)
            for good in goods:
                self.assertIn(good, tile["goods"], name)
            slot = self.world["settlement_slots"][tile["settlement_slots"][0]]
            self.assertEqual((slot["name"], slot["tier"], slot["charter"]),
                             (name, "town", "free"), name)

    def test_the_famous_nine_are_the_ones_the_round_named(self) -> None:
        """The names and their metals, so a re-sited mine is a decision."""
        self.assertEqual(
            {name: goods for name, goods in places.MINES.values()},
            {"Goslar": ("silver", "copper"), "Kutna Hora": ("silver",),
             "Falun": ("copper", "iron"),
             "Banska Stiavnica": ("silver", "copper"),
             "Melle": ("silver",), "Erzberg": ("iron",),
             "Novo Brdo": ("silver",), "Luneburg": ("salt",),
             "Wieliczka": ("salt",)})

    def test_only_a_mine_tile_carries_a_mine(self) -> None:
        for tile in self.world["tiles"].values():
            authored = (tile["row"], tile["column"]) in places.MINES
            self.assertEqual(tile["mine"] is not None, authored, tile["id"])
            self.assertEqual("mine" in tile["tags"], authored, tile["id"])

    def test_the_authored_colour_sits_where_it_was_placed(self) -> None:
        for (row, column), goods in places.GOODS_AUTHORED.items():
            tile = self.world["tiles"][places.tile_id(row, column)]
            self.assertNotEqual(tile["biome"], "sea", tile["id"])
            for good in goods:
                self.assertIn(good, tile["goods"], tile["id"])

    def test_the_exotic_doors_are_ordinary_tiles(self) -> None:
        """The reversal the round recorded: an exotic's origin is the
        frame's DOOR and nothing else about it is special -- an ordinary
        tile with an ordinary goods list, which is why the delta port also
        exports the Nile's grain."""
        for rc, goods in (((11, 30), ("silk", "dyes")),
                          ((18, 24), ("spice", "sugar", "dyes"))):
            tile = self.world["tiles"][places.tile_id(*rc)]
            self.assertEqual(tuple(tile["goods"][:len(goods)]), goods,
                             tile["id"])
            self.assertIsNone(tile["mine"], tile["id"])
            self.assertNotIn("mine", tile["tags"], tile["id"])
        delta = self.world["tiles"][places.tile_id(18, 24)]
        self.assertIn("grain", delta["goods"])

    def test_the_five_legendary_roads_run_where_they_were_authored(self):
        by_name = {route["name"]: route for route in self.world["routes"]
                   if route["name"]}
        self.assertEqual(sorted(by_name),
                         ["the Amber Road", "the Fairs Road",
                          "the Grain Fleet", "the Silk Road",
                          "the Spice Lane"])
        for spec in places.LEGENDARY:
            route = by_name[spec["name"]]
            self.assertEqual(route["path"][0], places.tile_id(*spec["from"]),
                             spec["name"])
            self.assertEqual(route["path"][-1], places.tile_id(*spec["to"]),
                             spec["name"])
            for good in spec["goods"]:
                self.assertIn(good, route["goods"], spec["name"])

    def test_venice_is_the_hub_by_construction(self) -> None:
        """Three of the five legendary roads meet at one tile -- the
        middleman monopoly emerges from the authored endpoint pairs, not
        from a rule that says so."""
        venice = places.tile_id(12, 14)
        named = [route for route in places.tile_routes(self.world, venice)
                 if route["name"]]
        self.assertEqual(len(named), 3)

    def test_the_authored_half_is_the_same_in_every_campaign(self) -> None:
        """The mines, the origins and the legendary roads are the trade
        skeleton: fixed in character however the census rolls."""
        other = _world(999)
        for tid, tile in self.world["tiles"].items():
            self.assertEqual(tile["goods"], other["tiles"][tid]["goods"], tid)
            self.assertEqual(tile["mine"], other["tiles"][tid]["mine"], tid)
        for name in ("the Silk Road", "the Grain Fleet"):
            here = next(r for r in self.world["routes"] if r["name"] == name)
            there = next(r for r in other["routes"] if r["name"] == name)
            self.assertEqual(here["path"], there["path"], name)

    def test_the_ordinary_network_is_each_world_s_own(self) -> None:
        """...and the other half of that claim: the roads follow the rolled
        census, so two worlds do not carry the same traffic."""
        other = _world(999)
        self.assertNotEqual(_tagged(self.world, "trade-route"),
                            _tagged(other, "trade-route"))


# --------------------------------------------------------------------------- #
# B. The derived half: the produce origins and the network's shape
# --------------------------------------------------------------------------- #

class TheDerivedHalf(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.world = _world()

    def test_only_legal_good_words_anywhere(self) -> None:
        self.assertEqual(len(places.GOODS), 19)
        for tile in self.world["tiles"].values():
            for good in tile["goods"]:
                self.assertIn(good, places.GOODS, tile["id"])
        for route in self.world["routes"]:
            self.assertTrue(route["goods"], route["id"])
            for good in route["goods"]:
                self.assertIn(good, places.GOODS, route["id"])

    def test_the_sea_digs_and_grows_nothing(self) -> None:
        for tile in self.world["tiles"].values():
            if tile["biome"] != "sea":
                continue
            self.assertEqual(tile["goods"], [], tile["id"])
            self.assertIsNone(tile["mine"], tile["id"])

    def test_grain_is_the_alluvial_corridors_only(self) -> None:
        """The threshold sits above the ordinary-plains baseline on
        purpose: plain country feeds itself and exports nothing, so the
        goods map stays sparse."""
        grain = [t for t in _land(self.world) if "grain" in t["goods"]]
        self.assertTrue(4 <= len(grain) <= 30, len(grain))
        for tile in grain:
            economy = places.tile_economy(
                tile["climate"], tile["terrain"], tile["biome"] == "river",
                tile["row"], tile["column"])
            self.assertGreaterEqual(economy["realized"],
                                    places.GRAIN_SURPLUS, tile["id"])

    def test_a_produce_region_under_the_minimum_is_local_colour(self) -> None:
        """Every derived origin except grain is a contiguous region of at
        least `MIN_PRODUCE_REGION` tiles; grain is exempt, because one
        alluvial tile IS a granary."""
        origins = places.goods_origins(self.world)
        authored = ({places.tile_id(*rc) for rc in places.MINES}
                    | {places.tile_id(*rc) for rc in places.GOODS_AUTHORED})
        for origin in origins:
            if origin["tiles"] & authored and len(origin["tiles"]) == 1:
                continue                    # an authored single tile
            if origin["goods"][0] == "grain":
                continue
            self.assertGreaterEqual(len(origin["tiles"]),
                                    places.MIN_PRODUCE_REGION,
                                    origin["goods"])
            reached, frontier = set(), [min(origin["tiles"])]
            while frontier:
                tid = frontier.pop()
                if tid in reached:
                    continue
                reached.add(tid)
                frontier += [n for n in self.world["tiles"][tid]["neighbors"]
                             if n in origin["tiles"]]
            self.assertEqual(reached, origin["tiles"], origin["goods"])

    def test_timber_never_rises_in_the_fen(self) -> None:
        for tile in _land(self.world):
            if tile["terrain"] == "marsh":
                self.assertNotIn("timber", tile["goods"], tile["id"])

    def test_furs_and_wax_travel_together(self) -> None:
        for tile in _land(self.world):
            self.assertEqual("furs" in tile["goods"],
                             "wax" in tile["goods"], tile["id"])

    def test_the_networks_pinned_sweep(self) -> None:
        """The measured posture (benchlog 2026-08-21): ~59 routes a world,
        ~114 of 314 land tiles on one, 27 ports. The network is nearly
        deterministic -- it moves only with the rolled cities."""
        routes, on_road, ports = [], [], []
        for seed in range(SWEEP):
            world = _world(seed)
            routes.append(len(world["routes"]))
            on_road.append(len(_tagged(world, "trade-route")))
            ports.append(len(_tagged(world, "port")))
        self.assertTrue(56 <= min(routes) and max(routes) <= 62, routes)
        self.assertTrue(105 <= min(on_road) and max(on_road) <= 125, on_road)
        self.assertTrue(23 <= min(ports) and max(ports) <= 31, ports)


# --------------------------------------------------------------------------- #
# C. The routes themselves
# --------------------------------------------------------------------------- #

class TheRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.world = _world()

    def test_every_route_record_is_well_formed_end_to_end(self) -> None:
        seen = set()
        for index, route in enumerate(self.world["routes"], 1):
            self.assertEqual(route["id"], f"route/{index:02d}")
            self.assertNotIn((route["path"][0], route["path"][-1]), seen,
                             "routes with both endpoints shared merge")
            seen.add((route["path"][0], route["path"][-1]))
            self.assertGreaterEqual(len(route["path"]), 2, route["id"])
            self.assertEqual(len(set(route["path"])), len(route["path"]),
                             route["id"])
            days = sum(places.edge_days(a, b) for a, b
                       in zip(route["path"], route["path"][1:]))
            self.assertEqual(days, route["days"], route["id"])

    def test_a_route_crossing_a_tile_tags_it(self) -> None:
        on_road, at_sea = set(), set()
        for route in self.world["routes"]:
            for tid in route["path"]:
                sea = self.world["tiles"][tid]["biome"] == "sea"
                (at_sea if sea else on_road).add(tid)
        self.assertEqual(on_road, _tagged(self.world, "trade-route"))
        self.assertEqual(at_sea, _tagged(self.world, "sea-lane"))
        self.assertTrue(at_sea, "the sea lanes sail somewhere")

    def test_a_port_is_a_shore_a_route_changes_element_on(self) -> None:
        ports = _tagged(self.world, "port")
        self.assertTrue(ports)
        for tid in ports:
            tile = self.world["tiles"][tid]
            self.assertNotEqual(tile["biome"], "sea", tid)
            self.assertIn("coast", tile["tags"], tid)
            self.assertIn("trade-route", tile["tags"], tid)

    def test_the_sea_sails_at_the_settled_edge_cost(self) -> None:
        """No cheap freight: one distance model for war, trade and play.
        The Spice Lane's days are exactly what walking it would cost."""
        lane = next(r for r in self.world["routes"]
                    if r["name"] == "the Spice Lane")
        self.assertEqual(lane["days"],
                         places.path_days(lane["path"][0], lane["path"][-1]))
        self.assertTrue(any(self.world["tiles"][t]["biome"] == "sea"
                            for t in lane["path"]))

    def test_a_hungry_mine_gets_a_grain_road_and_falun_does_not(self) -> None:
        """Seven of the nine mines cannot feed themselves; six find a
        granary inside `MINE_FOOD_DAYS` and Falun does not. The north's
        grain problem is pinned, not accidental."""
        hungry, fed = [], []
        for (row, column), (name, _goods) in places.MINES.items():
            tid = places.tile_id(row, column)
            tile = self.world["tiles"][tid]
            economy = places.tile_economy(
                tile["climate"], tile["terrain"], tile["biome"] == "river",
                row, column)
            if economy["realized"] >= places.FARMLAND_MIN:
                continue
            hungry.append(name)
            caravan = [r for r in self.world["routes"]
                       if r["path"][-1] == tid and "grain" in r["goods"]]
            if caravan:
                fed.append(name)
                self.assertLessEqual(caravan[0]["days"],
                                     places.MINE_FOOD_DAYS, name)
                origin = caravan[0]["path"][0]
                self.assertIn("grain", self.world["tiles"][origin]["goods"])
        self.assertEqual(len(hungry), 7, hungry)
        self.assertEqual(sorted(set(hungry) - set(fed)), ["Falun"])

    def test_routes_with_shared_endpoints_merge_their_cargo(self) -> None:
        """Falun ships copper and iron down one road, not two."""
        multi = [r for r in self.world["routes"] if len(r["goods"]) > 1]
        self.assertTrue(multi)
        falun = places.tile_id(3, 22)
        out = [r for r in self.world["routes"] if r["path"][0] == falun]
        self.assertEqual(len(out), 1)
        self.assertEqual(sorted(out[0]["goods"]), ["copper", "iron"])

    def test_the_network_rides_the_save(self) -> None:
        clone = json.loads(json.dumps(self.world))
        self.assertEqual(clone["routes"], self.world["routes"])
        for tid, tile in self.world["tiles"].items():
            self.assertEqual((clone["tiles"][tid]["goods"],
                              clone["tiles"][tid]["mine"]),
                             (tile["goods"], tile["mine"]), tid)
        places.validate_world(clone)


# --------------------------------------------------------------------------- #
# D. The label, and the broken worlds
# --------------------------------------------------------------------------- #

class TheLabel(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.world = _world()

    def test_a_mine_tile_speaks_its_mine_and_its_metal(self) -> None:
        lines = places.tile_detail_lines(self.world, places.tile_id(9, 14))
        self.assertIn("  mine: Goslar", lines)
        self.assertIn("  goods: silver, copper", lines)

    def test_an_ordinary_route_names_its_endpoints_and_cargo(self) -> None:
        goslar = places.tile_id(9, 14)
        lines = places.tile_detail_lines(self.world, goslar)
        self.assertIn("  Goslar - Prague: silver", lines)

    def test_a_legendary_road_leads_with_its_own_name(self) -> None:
        gate = places.tile_id(11, 30)
        lines = places.tile_detail_lines(self.world, gate, width=200)
        self.assertIn("  the Silk Road: the eastern gate - "
                      "Constantinople, silk and dyes", lines)

    def test_an_unnamed_endpoint_reads_as_its_coordinate(self) -> None:
        """A rolled market is a place the party has never heard of, so the
        label says where it is rather than inventing what it is called."""
        text = "\n".join(line for tid in self.world["tile_order"]
                         for line in places.tile_detail_lines(
                             self.world, tid, width=200))
        self.assertRegex(text, r"\n  R\d\dC\d\d - ")

    def test_every_label_line_is_inside_the_wrap(self) -> None:
        for tid in self.world["tile_order"]:
            for line in places.tile_detail_lines(self.world, tid):
                self.assertLessEqual(len(line), 40, f"{tid}: {line!r}")

    def test_a_quiet_tile_says_nothing_it_has_no_reason_to(self) -> None:
        quiet = next(t for t in _land(self.world)
                     if not t["goods"] and "trade-route" not in t["tags"])
        lines = places.tile_detail_lines(self.world, quiet)
        self.assertTrue(all(not line.startswith("  mine") for line in lines))
        self.assertTrue(all(not line.startswith("  goods") for line in lines))
        self.assertTrue(all(" - " not in line for line in lines[1:]))

    def test_the_cargo_words_read_as_english(self) -> None:
        self.assertEqual(places._cargo_words(["silver"]), "silver")
        self.assertEqual(places._cargo_words(["copper", "iron"]),
                         "copper and iron")
        self.assertEqual(places._cargo_words(["spice", "sugar", "dyes"]),
                         "spice, sugar and dyes")

    def test_an_illegal_trade_layer_raises_where_it_is_made(self) -> None:
        """One broken world per clause the trade session added."""
        def broken(mutate):
            world = copy.deepcopy(self.world)
            mutate(world)
            with self.assertRaises(ValueError):
                places.validate_world(world)

        def unnumber_the_routes(world):
            world["routes"].reverse()

        def a_route_to_nowhere(world):
            world["routes"][0]["path"] = [world["routes"][0]["path"][0]]

        def an_empty_cart(world):
            world["routes"][0]["goods"] = []

        def invent_a_good(world):
            world["routes"][0]["goods"] = ["moonstone"]

        def invent_a_good_on_a_tile(world):
            _any_land(world)["goods"] = ["moonstone"]

        def a_route_that_leaps(world):
            route = world["routes"][0]
            route["path"] = [route["path"][0], route["path"][-1]]

        def a_walk_costed_wrong(world):
            world["routes"][0]["days"] += 1

        def lose_a_legendary_road(world):
            world["routes"] = [r for r in world["routes"]
                               if r["name"] != "the Amber Road"]
            for index, route in enumerate(world["routes"], 1):
                route["id"] = f"route/{index:02d}"

        def rename_an_ordinary_road(world):
            next(r for r in world["routes"]
                 if not r["name"])["name"] = "the Silk Road"

        def unload_a_legendary_road(world):
            route = next(r for r in world["routes"]
                         if r["name"] == "the Silk Road")
            route["goods"] = ["grain"]

        def reroute_a_legendary_road(world):
            route = next(r for r in world["routes"]
                         if r["name"] == "the Fairs Road")
            route["path"] = list(reversed(route["path"]))

        def move_a_mine(world):
            world["tiles"][places.tile_id(9, 14)]["mine"] = None

        def invent_a_mine(world):
            tile = next(t for t in _land(world) if t["mine"] is None)
            tile["mine"] = "Nowhere Deep"

        def strip_a_mine_s_metal(world):
            tile = world["tiles"][places.tile_id(8, 16)]
            tile["goods"] = [g for g in tile["goods"] if g != "salt"]

        def farm_the_sea(world):
            next(t for t in world["tiles"].values()
                 if t["biome"] == "sea")["goods"] = ["grain"]

        def forget_a_road(world):
            tid = world["routes"][0]["path"][0]
            world["tiles"][tid]["tags"].remove("trade-route")

        def invent_a_port(world):
            tile = next(t for t in _land(world)
                        if "port" not in t["tags"] and "coast" in t["tags"])
            tile["tags"].append("port")

        def invent_a_sea_lane(world):
            tile = next(t for t in world["tiles"].values()
                        if t["biome"] == "sea" and "sea-lane" not in t["tags"])
            tile["tags"].append("sea-lane")

        def untag_a_mine(world):
            world["tiles"][places.tile_id(9, 14)]["tags"].remove("mine")

        def a_port_off_the_coast(world):
            tile = next(t for t in _land(world) if "port" in t["tags"])
            tile["tags"].remove("coast")

        for mutate in (unnumber_the_routes, a_route_to_nowhere, an_empty_cart,
                       invent_a_good, invent_a_good_on_a_tile,
                       a_route_that_leaps, a_walk_costed_wrong,
                       lose_a_legendary_road, rename_an_ordinary_road,
                       unload_a_legendary_road, reroute_a_legendary_road,
                       move_a_mine, invent_a_mine, strip_a_mine_s_metal,
                       farm_the_sea, forget_a_road, invent_a_port,
                       invent_a_sea_lane, untag_a_mine,
                       a_port_off_the_coast):
            with self.subTest(mutate.__name__):
                broken(mutate)


def _any_land(world: dict) -> dict:
    return next(t for t in world["tiles"].values() if t["biome"] != "sea")


if __name__ == "__main__":
    unittest.main()
