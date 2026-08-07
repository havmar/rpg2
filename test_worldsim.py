"""Contract suite for the WORLD & NPC SIMULATION build (worldsim.md), the
ladder's own suite -- no sim and no bench imports it. Sessions are named,
not numbered: the ladder renumbers itself every time a rung ships.

THE SETTLEMENT TRIM (2026-08-07). The rules this pins: a land
BEGINS with three settlements (one capital, one town, one village, topped
up from what the catalog holds when a tier is missing); everything else the
catalog holds is the land's RESERVE POOL, unbuilt until something needs it
to exist; the need-to-exist draw builds a whole usable place (Sites, the
guaranteed services, their faces, a board that fills on the first look) and
records WHY it was founded; the draw can be steered by tier and by tags;
a land whose reserve is dry says no rather than inventing geography; and
the whole thing is seeded, stable, and JSON-clean so it rides the save.

THE WORLD FRAME (2026-08-07, `worldsim.py`). The rules this pins: the card
and relation record shapes and their validation; the 2d6 wealth roll at
worldgen and the band it puts every land in; the per-land save layer
(wealth, day-stamped states, the shuffled crisis deck, the drawn record);
the deck draw on need, which skips what a land does not admit and never
contradicts an exclusive slot; what a card's clock takes back and what it
leaves standing; the relations table, whose derived states are computed at
read time and never stored; the lazy roll's identity (catching thirty days
up at an arrival IS rolling them live); and the two surfaces the frame
ships -- the news line, told once, and the state diff.

Run:  python -m unittest -v test_worldsim.py
"""

import io
import json
import random
import unittest
from contextlib import redirect_stdout

import conquest
import places
import quests
import worldsim


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


# =========================================================================== #
# THE WORLD FRAME (2026-08-07) -- worldsim.py
# =========================================================================== #

WIDTH = 40      # the designer's phone: display copy fits, prose wraps


def _layer(world: dict, polity: str) -> dict:
    return worldsim.land_layer(world, polity)


def _fire(world: dict, polity: str, key: str, day: int,
          seed: int = 1) -> dict:
    """Fire one named card by hand -- the tests drive the pulse directly so
    they never have to wait on the deck's own dice."""
    worldsim._fire(world, polity, worldsim.CARDS_BY_KEY[key], day,
                   random.Random(seed))
    return _layer(world, polity)


class TheRecordShapes(unittest.TestCase):
    """The five record kinds, formalized: what the authored data must be."""

    def test_the_authored_content_validates_at_import(self) -> None:
        worldsim.validate_content()     # raises on anything illegal

    def test_a_card_declares_only_real_outlets(self) -> None:
        with self.assertRaises(ValueError):
            worldsim.card("x/y", "X", "firascir", rumor="not an outlet")

    def test_no_card_exceeds_the_five_outlets_or_declares_none(self) -> None:
        for card in worldsim.CARDS:
            self.assertTrue(card["outlets"], card["key"])
            self.assertLessEqual(len(card["outlets"]), 5, card["key"])
            self.assertFalse(set(card["outlets"]) - set(worldsim.OUTLETS),
                             card["key"])

    def test_every_card_admits_over_the_documented_axes(self) -> None:
        for card in worldsim.CARDS:
            self.assertEqual(set(card["admits"]),
                             {"wealth", "states", "without", "weather"},
                             card["key"])

    def test_the_floor_is_two_cards_a_land(self) -> None:
        # The asymmetry doctrine's floor, as far as the frame's seed
        # content goes: every land has something its deck can draw.
        for polity in places.LAND_SPECS:
            own = [c for c in worldsim.CARDS if c["land"] == polity]
            self.assertGreaterEqual(len(own), 2, polity)

    def test_a_slot_member_is_never_set_as_a_free_state(self) -> None:
        for card in worldsim.CARDS:
            state = card["outlets"].get("state") or {}
            for group in ("set", "while", "clear"):
                for sid in state.get(group, ()):
                    self.assertNotIn(sid, worldsim.SLOT_OF, card["key"])

    def test_a_relation_is_a_directed_edge_between_real_lands(self) -> None:
        for edge in worldsim.RELATIONS:
            self.assertIn(edge["from"], places.LAND_SPECS)
            self.assertIn(edge["to"], places.LAND_SPECS)
            self.assertNotEqual(edge["from"], edge["to"])
            self.assertIn(edge["then"], worldsim.STATE_WORDS)
            self.assertTrue(edge["because"])

    def test_every_derived_state_has_a_card_that_can_cause_it(self) -> None:
        # An edge nothing can ever trigger is dead data.
        causable = set()
        for card in worldsim.CARDS:
            state = card["outlets"].get("state") or {}
            causable |= set(state.get("set", ())) | set(state.get("while", ()))
            causable |= set((state.get("slot") or {}).values())
        for edge in worldsim.RELATIONS:
            self.assertTrue(set(edge["when"]) & causable, edge)

    def test_the_authored_labels_fit_the_phone_and_stay_ascii(self) -> None:
        labels = ([c["name"] for c in worldsim.CARDS]
                  + list(worldsim.STATE_WORDS.values())
                  + [e["because"] for e in worldsim.RELATIONS])
        for label in labels:
            self.assertLessEqual(len(label), WIDTH, label)
        prose = labels + [c["outlets"].get("news", "")
                          for c in worldsim.CARDS]
        for line in prose:
            self.assertTrue(line.isascii(), line)


class TheWealthRoll(unittest.TestCase):
    """2d6 at worldgen: 2-4 CRISIS, 5-9 NORMAL, 10-12 PROSPEROUS."""

    def test_every_land_holds_exactly_one_legal_band(self) -> None:
        world = _world()
        for polity in world["lands"]:
            self.assertIn(worldsim.wealth_of(world, polity), worldsim.BANDS)

    def test_the_die_is_the_weighted_middle(self) -> None:
        rng = random.Random(11)
        rolled = [worldsim.roll_wealth(rng) for _ in range(6000)]
        share = {b: rolled.count(b) / len(rolled) for b in worldsim.BANDS}
        self.assertAlmostEqual(share["crisis"], 1 / 6, delta=0.03)
        self.assertAlmostEqual(share["normal"], 2 / 3, delta=0.03)
        self.assertAlmostEqual(share["prosperous"], 1 / 6, delta=0.03)

    def test_the_band_is_stable_for_a_seed_and_moves_between_seeds(self
                                                                  ) -> None:
        first, second = _world(881), _world(881)
        bands = lambda w: {p: worldsim.wealth_of(w, p) for p in w["lands"]}
        self.assertEqual(bands(first), bands(second))
        self.assertNotEqual(
            {bands(_world(s))["firascir"] for s in range(30)}, {"normal"})

    def test_the_world_layer_moves_no_worldgen_stream(self) -> None:
        """The armory's rule: the layer rolls off DERIVED seeds, so the
        WHOLE world every career bench rides -- board, cast, geography,
        armory -- is identical with the layer taken away."""
        def stripped(world: dict) -> str:
            world = json.loads(json.dumps(world))
            for land in world["lands"].values():
                land.pop("world", None)
                land["states"] = []
            world["events"] = [e for e in world["events"]
                               if e["action"] != "add_state"]
            return json.dumps(world, sort_keys=True)

        opened = worldsim.open_world
        with_layer = stripped(_world(2026))
        try:
            worldsim.open_world = lambda world: world
            self.assertEqual(stripped(_world(2026)), with_layer)
        finally:
            worldsim.open_world = opened

    def test_a_band_a_card_moved_for_its_clock_comes_back(self) -> None:
        world = _world(3)
        worldsim.set_wealth(world, "firascir", "normal", 0)
        live = _fire(world, "firascir", "firascir/bad-harvest", 5)["live"]
        self.assertEqual(worldsim.wealth_of(world, "firascir"), "crisis")
        _layer(world, "firascir")["rolled_day"] = live["until"] - 1
        worldsim.roll_land(world, "firascir", live["until"])
        self.assertEqual(worldsim.wealth_of(world, "firascir"), "normal")

    def test_a_clockless_card_moves_the_band_for_good(self) -> None:
        """A vein running out is not a season: nothing gives the band back
        on a clock, and the only way up is another card."""
        world = _world(3)
        worldsim.set_wealth(world, "dvarvengrond", "normal", 0)
        layer = _fire(world, "dvarvengrond", "dvarvengrond/vein-dries", 4)
        self.assertEqual(worldsim.wealth_of(world, "dvarvengrond"), "crisis")
        self.assertIsNone(layer["live"])    # it stands over nothing
        layer["rolled_day"] = 4
        worldsim.roll_land(world, "dvarvengrond", 120)
        drawn = {d["key"] for d in layer["drawn"]}
        if worldsim.wealth_of(world, "dvarvengrond") != "crisis":
            self.assertIn("dvarvengrond/veins-reopened", drawn)

    def test_the_band_has_a_way_down_and_a_way_back_up(self) -> None:
        """The loop closes: a land can be pushed into crisis and pulled out
        of it. A frame where the opening roll is destiny is not a sim."""
        down = {c["key"] for c in worldsim.CARDS
                if (c["outlets"].get("state") or {}).get("wealth") == "crisis"
                or (c["outlets"].get("state") or {}).get("wealth_while")
                == "crisis"}
        up = {c["key"] for c in worldsim.CARDS
              if (c["outlets"].get("state") or {}).get("wealth")
              in ("normal", "prosperous")}
        self.assertTrue(down)
        self.assertTrue(up)


class ThePerLandSaveState(unittest.TestCase):
    """What the save grows: one plain dict per land, JSON all the way."""

    def test_every_land_carries_the_documented_layer(self) -> None:
        world = _world()
        for polity in world["lands"]:
            layer = _layer(world, polity)
            self.assertEqual(set(layer),
                             {"wealth", "wealth_day", "deck", "drawn",
                              "live", "news", "told_day", "rolled_day"})

    def test_the_layer_rides_the_save(self) -> None:
        world = _world()
        worldsim.roll_world(world, 50)
        clone = json.loads(json.dumps(world))
        for polity in world["lands"]:
            self.assertEqual(clone["lands"][polity]["world"],
                             _layer(world, polity))
            self.assertEqual(clone["lands"][polity]["states"],
                             world["lands"][polity]["states"])

    def test_the_deck_is_the_land_s_own_cards_shuffled(self) -> None:
        world = _world()
        for polity in world["lands"]:
            own = {c["key"] for c in worldsim.CARDS if c["land"] == polity}
            layer = _layer(world, polity)
            held = set(layer["deck"]) | {d["key"] for d in layer["drawn"]}
            self.assertEqual(held, own, polity)

    def test_the_deck_order_is_seeded_and_stable(self) -> None:
        self.assertEqual(_layer(_world(881), "firascir")["deck"],
                         _layer(_world(881), "firascir")["deck"])

    def test_the_states_are_day_stamped(self) -> None:
        world = _world()
        worldsim.set_state(world, "gibili", "mills-stopped", day=9)
        held = worldsim.held_states(world, "gibili")
        self.assertEqual([s["id"] for s in held], ["mills-stopped"])
        self.assertEqual(held[0]["since"], 9)


class TheDeckDraw(unittest.TestCase):
    """The draw on need: the pact deck's pattern, over admitting cards."""

    def test_a_land_in_crisis_opens_with_a_card(self) -> None:
        seen = 0
        for seed in range(25):
            world = _world(seed)
            for polity in world["lands"]:
                layer = _layer(world, polity)
                if layer["wealth"] != "crisis":
                    continue
                seen += 1
                self.assertTrue(layer["drawn"], (seed, polity))
                # Dated the first PLAYED day, not worldgen's day 0.
                self.assertEqual(layer["drawn"][0]["day"],
                                 worldsim.OPENING_DAY)
        self.assertTrue(seen, "no crisis land in 25 worlds")

    def test_a_quiet_land_opens_with_nothing(self) -> None:
        for seed in range(25):
            world = _world(seed)
            for polity in world["lands"]:
                layer = _layer(world, polity)
                if layer["wealth"] != "crisis":
                    self.assertFalse(layer["drawn"], (seed, polity))

    def test_the_draw_skips_what_the_land_does_not_admit(self) -> None:
        world = _world()
        worldsim.set_wealth(world, "mortellaria", "prosperous", 0)
        rng = random.Random(4)
        for _ in range(6):
            drawn = worldsim._draw(world, "mortellaria", rng)
            if drawn is None:
                break
            self.assertIn("prosperous", drawn["admits"]["wealth"])
        # ...and what it skipped is still in the deck for a later day.
        self.assertIn("mortellaria/bank-run", _layer(world, "mortellaria")
                      ["deck"])

    def test_a_card_admitting_on_a_state_waits_for_it(self) -> None:
        world = _world()
        worldsim.set_wealth(world, "dvarvengrond", "crisis", 0)
        spec = worldsim.CARDS_BY_KEY["dvarvengrond/veins-reopened"]["admits"]
        self.assertFalse(worldsim.admits(world, "dvarvengrond", spec))
        worldsim.set_state(world, "dvarvengrond", "deposit-drying", 3)
        self.assertTrue(worldsim.admits(world, "dvarvengrond", spec))

    def test_a_card_blocked_by_a_state_it_forbids(self) -> None:
        world = _world()
        worldsim.set_wealth(world, "firascir", "crisis", 0)
        spec = worldsim.CARDS_BY_KEY["firascir/war-debts"]["admits"]
        self.assertTrue(worldsim.admits(world, "firascir", spec))
        worldsim.set_state(world, "firascir", "harvest-failed", 2)
        self.assertFalse(worldsim.admits(world, "firascir", spec))

    def test_an_exclusive_slot_is_never_contradicted(self) -> None:
        world = _world()
        worldsim.set_state(world, "ensimaa", "foreigners-unwelcome", 2)
        worldsim.set_state(world, "ensimaa", "foreigners-tolerated", 6)
        held = [s["id"] for s in worldsim.held_states(world, "ensimaa")]
        self.assertEqual([s for s in held if s.startswith("foreigners")],
                         ["foreigners-tolerated"])

    def test_a_card_with_nothing_new_to_say_stays_in_the_deck(self) -> None:
        world = _world()
        worldsim.set_wealth(world, "ensimaa", "crisis", 0)
        worldsim.set_state(world, "ensimaa", "foreigners-unwelcome", 1)
        rng = random.Random(2)
        for _ in range(4):
            drawn = worldsim._draw(world, "ensimaa", rng)
            if drawn is None:
                break
            self.assertNotEqual(drawn["key"], "ensimaa/rented-land")
        self.assertIn("ensimaa/rented-land", _layer(world, "ensimaa")["deck"])

    def test_an_exhausted_deck_reshuffles(self) -> None:
        world = _world()
        polity = "tergal"
        worldsim.set_wealth(world, polity, "crisis", 0)
        _layer(world, polity)["deck"] = []
        drawn = worldsim._draw(world, polity, random.Random(5))
        self.assertIsNotNone(drawn)
        self.assertEqual(drawn["land"], polity)


class TheCardsClock(unittest.TestCase):
    """What a pulse leaves behind when its day-stamp runs out."""

    def test_a_while_state_comes_off_and_a_slot_stands(self) -> None:
        world = _world()
        layer = _fire(world, "dvarvengrond", "dvarvengrond/new-seam", 10)
        held = lambda: [s["id"] for s in worldsim.held_states(world,
                                                             "dvarvengrond")]
        self.assertIn("claims-collide", held())
        self.assertIn("deposit-found", held())
        layer["rolled_day"] = layer["live"]["until"] - 1
        worldsim.roll_land(world, "dvarvengrond", layer["live"]["until"])
        self.assertNotIn("claims-collide", held())      # the card's own
        self.assertIn("deposit-found", held())          # the mark it left

    def test_the_clock_is_a_day_stamp_not_a_countdown(self) -> None:
        world = _world()
        layer = _fire(world, "gibili", "gibili/uprising", 30)
        self.assertGreater(layer["live"]["until"], 30)
        self.assertEqual(layer["live"]["day"], 30)

    def test_one_card_stands_over_a_land_at_a_time(self) -> None:
        for seed in range(12):
            world = _world(seed)
            for day in range(1, 80):
                worldsim.roll_world(world, day)
                for polity in world["lands"]:
                    live = _layer(world, polity)["live"]
                    self.assertTrue(live is None or live["key"]
                                    in worldsim.CARDS_BY_KEY)

    def test_every_firing_is_recorded(self) -> None:
        world = _world(7)
        worldsim.roll_world(world, 120)
        for polity in world["lands"]:
            layer = _layer(world, polity)
            for record in layer["drawn"]:
                self.assertIn(record["key"], worldsim.CARDS_BY_KEY)
                self.assertGreaterEqual(record["day"], 0)


class TheRelations(unittest.TestCase):
    """Authored directed edges, read at roll time. Never a quantity."""

    def test_a_derived_state_is_computed_and_never_stored(self) -> None:
        world = _world()
        worldsim.set_state(world, "firascir", "harvest-failed", 5)
        derived = [s["id"] for s in worldsim.derived_states(world, "ensimaa")]
        self.assertEqual(derived, ["grain-scarce"])
        self.assertNotIn("grain-scarce",
                         [s["id"] for s in worldsim.held_states(world,
                                                                "ensimaa")])
        self.assertNotIn("grain-scarce",
                         json.dumps(world["lands"]["ensimaa"]["states"]))

    def test_it_reaches_every_land_down_the_edge(self) -> None:
        world = _world()
        worldsim.set_state(world, "firascir", "harvest-failed", 5)
        fed = {e["to"] for e in worldsim.RELATIONS
               if e["from"] == "firascir" and e["then"] == "grain-scarce"}
        for polity in fed:
            self.assertIn("grain-scarce",
                          worldsim.state_ids(world, polity), polity)

    def test_it_lifts_when_the_cause_does(self) -> None:
        world = _world()
        worldsim.set_state(world, "firascir", "harvest-failed", 5)
        worldsim.drop_state(world, "firascir", "harvest-failed", 40)
        self.assertEqual(worldsim.derived_states(world, "ensimaa"), [])

    def test_a_card_admits_on_a_derived_state_too(self) -> None:
        world = _world()
        worldsim.set_state(world, "firascir", "harvest-failed", 5)
        self.assertIn("grain-scarce", worldsim.state_ids(world, "gibili"))
        spec = {"wealth": (), "states": ("grain-scarce",), "without": (),
                "weather": ()}
        self.assertTrue(worldsim.admits(world, "gibili", spec))

    def test_the_edge_names_its_cause_for_the_readout(self) -> None:
        world = _world()
        worldsim.set_state(world, "gibili", "mills-stopped", 3)
        derived = worldsim.derived_states(world, "mortellaria")[0]
        self.assertEqual(derived["from"], "gibili")
        self.assertIn(derived["because"], worldsim.state_line(derived))


class TheRollPoints(unittest.TestCase):
    """Lazy, seeded, day-stamped: no background tick, and no difference
    between a world watched and a world left alone."""

    def test_catching_up_is_the_same_as_living_through_it(self) -> None:
        watched, ignored = _world(4471), _world(4471)
        for day in range(1, 61):
            worldsim.roll_world(watched, day)
        worldsim.roll_world(ignored, 60)
        for polity in watched["lands"]:
            self.assertEqual(_layer(ignored, polity),
                             _layer(watched, polity), polity)
            self.assertEqual(ignored["lands"][polity]["states"],
                             watched["lands"][polity]["states"], polity)

    def test_rolling_the_same_day_twice_changes_nothing(self) -> None:
        world = _world(12)
        worldsim.roll_world(world, 40)
        before = json.dumps(world["lands"], sort_keys=True)
        worldsim.roll_world(world, 40)
        worldsim.roll_world(world, 12)      # and the past is not re-run
        self.assertEqual(json.dumps(world["lands"], sort_keys=True), before)

    def test_the_same_seed_lives_the_same_history(self) -> None:
        first, second = _world(99), _world(99)
        worldsim.roll_world(first, 90)
        worldsim.roll_world(second, 90)
        for polity in first["lands"]:
            self.assertEqual(_layer(first, polity)["drawn"],
                             _layer(second, polity)["drawn"], polity)

    def test_another_seed_lives_another_history(self) -> None:
        histories = set()
        for seed in range(8):
            world = _world(seed)
            worldsim.roll_world(world, 90)
            histories.add(tuple(d["key"] for polity in world["lands"]
                                for d in _layer(world, polity)["drawn"]))
        self.assertGreater(len(histories), 1)

    def test_something_moves_without_the_party_doing_anything(self) -> None:
        """The thread's second invariant, at the frame's scale: leave the
        world alone for a season and it is not where you left it."""
        moved = 0
        for seed in range(20):
            world = _world(seed)
            before = json.dumps(world["lands"], sort_keys=True)
            worldsim.roll_world(world, 60)
            moved += json.dumps(world["lands"], sort_keys=True) != before
        self.assertGreaterEqual(moved, 15, f"{moved}/20 worlds moved")


class TheSurfaces(unittest.TestCase):
    """The two the frame ships: the news line, and the state diff."""

    def test_the_news_is_day_stamped_and_told_once(self) -> None:
        world = _world()
        _fire(world, "gibili", "gibili/uprising", 12)
        first = worldsim.take_news(world, "gibili", 12)
        self.assertTrue(any("(day 12)" in line for line in first))
        self.assertEqual(worldsim.take_news(world, "gibili", 12), [])

    def test_a_long_absence_is_a_summary_not_a_scroll(self) -> None:
        world = _world()
        for day in range(1, 12):
            _fire(world, "tergal", "tergal/herd-drive", day)
        told = worldsim.take_news(world, "tergal", 12)
        self.assertLessEqual(len(told), worldsim.NEWS_TOLD + 1)  # + the head

    def test_the_news_keeps_only_so_much(self) -> None:
        world = _world()
        for day in range(1, worldsim.NEWS_KEPT + 12):
            _fire(world, "tergal", "tergal/herd-drive", day)
        self.assertEqual(len(_layer(world, "tergal")["news"]),
                         worldsim.NEWS_KEPT)

    def test_the_state_diff_shows_the_band_and_what_it_holds(self) -> None:
        world = _world()
        worldsim.set_wealth(world, "firascir", "crisis", 0)
        worldsim.set_state(world, "firascir", "harvest-failed", 7)
        line = worldsim.land_lines(world, "firascir")[0]
        self.assertIn("[CRISIS]", line)
        self.assertIn("the harvest has failed", line)
        self.assertIn("day 7", line)
        # ...and down the edge, with the cause named.
        fed = worldsim.land_lines(world, "gibili")[0]
        self.assertIn("grain is scarce", fed)
        self.assertIn("the Firascir grain", fed)

    def test_the_dm_inventory_covers_every_land(self) -> None:
        world = _world()
        worldsim.roll_world(world, 40)
        text = "\n".join(worldsim.world_lines(world))
        for polity, land in world["lands"].items():
            self.assertIn(land["name"], text)
            self.assertIn(worldsim.wealth_of(world, polity).upper(), text)

    def test_the_readouts_stay_ascii(self) -> None:
        world = _world()
        worldsim.roll_world(world, 60)
        for line in worldsim.world_lines(world):
            self.assertTrue(line.isascii(), line)


class TheSessionWiring(unittest.TestCase):
    """The frame is only real if the driver rolls it and tells it."""

    @staticmethod
    def _state(world: dict, day: int) -> dict:
        import rpg
        return {"world": world, "clock": rpg.Clock(day=day),
                "rng": random.Random(3), "party": [], "accepted": [],
                "active_quest": None, "purse": rpg.Purse(gold=0),
                "position": {"land": "firascir",
                             "area": quests.settlements_by_land(
                                 world)["firascir"][0]["key"]}}

    def test_the_board_s_clock_rolls_the_world(self) -> None:
        import session
        world = _world(4471)
        state = self._state(world, 25)
        with redirect_stdout(io.StringIO()):
            session.board_clock(state)
        for polity in world["lands"]:
            self.assertEqual(_layer(world, polity)["rolled_day"], 25, polity)

    def test_the_news_reaches_the_party_where_it_stands(self) -> None:
        import session
        world = _world(4471)
        state = self._state(world, 30)
        _fire(world, "firascir", "firascir/tolls", 9)
        out = io.StringIO()
        with redirect_stdout(out):
            session.world_news(state)
        self.assertIn("doubled the road tolls", " ".join(out.getvalue()
                                                         .split()))
        again = io.StringIO()
        with redirect_stdout(again):
            session.world_news(state)       # told once
        self.assertNotIn("doubled the road tolls", again.getvalue())

    def test_the_dm_has_a_command_for_it(self) -> None:
        import session
        args = session.build_parser().parse_args(["world"])
        self.assertIs(args.func, session.cmd_world)


if __name__ == "__main__":
    unittest.main()
