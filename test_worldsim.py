"""Contract suite for the WORLD & NPC SIMULATION build (worldsim.md), the
ladder's own suite -- no sim and no bench imports it. Sessions are named,
not numbered: the ladder renumbers itself every time a rung ships.

FIXED EUROPE GEOGRAPHY (2026-08-15). The rules this pins: the authored
30x18 map and country census; one natural Area per Tile; fixed, seeded
settlement slots; historical towns and explicit capitals; lazy settlement
materialization with stable name reserves; and JSON-clean persistence.

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

THE WEATHER (2026-08-08, the ladder's first content rung). The rules this
pins: the day roll against the environment profile's own climate weights
(and the spells running behind it, which cloud and frost break neither of);
the drought bending the roll that made it; the THREE TRACKS, so a storm
never blocks a harvest failing and a season of drought never blocks a
storm; the weather deck's admits (the sky, the spell, the card's own
`chance` keeping the supernatural rare and leaving it in the deck when it
misses); the authored cards -- the ford's spell, the fire wanting the
drought and the burn scar outliving it, the fog naming ONE necromancer and
keeping him; the DISEASE family (a cold, bounded deepening to pneumonia and
no rung past it, the HP ceiling instead of a per-round tick, the night's
shake on a stat that does not inflate, the roof, the smog that gets in
under it, the healer's tier gate); the storm's one field knob and one save;
and the surfaces -- the sky on the state diff, the cabin table whose
sinister row never announces itself, and the road that costs a day.

THE ECONOMY FLOOR (2026-08-09, the second content rung). The rules this
pins: the wealth band moving how much work a settlement posts and what it
quotes; the three quest verbs (post, cancel, reprice); the priced menu's
three multiplying sources and its clamps, including the only road a DERIVED
state has to a price; the local encounter table changing WHO and never how
hard; the five chains and the one that crosses a relation; and the second
invariant measured -- the board, the prices and the road have all moved by
the time the party walks back in.

POLITICS (2026-08-10, the third content rung). The rules this pins: the
ruler sheet -- one weighted pool of 357, three draws for a crown and two
off the crown-less 355 for anyone else, the shrinking pool that makes three
draws land three compatible words, the affliction cap, the derived heart,
and the two circumstances that read the sheet they were rolled beside; the
constitution slot off each land's own default-heavy die; the tension roll
(one, two in crisis, standing ones held on top) and its DECK GATE, which is
what keeps a packet a wide pool instead of a content budget; the faction
edges that need both ends in the rolled cast; the five ANY-OF admits and
the two new state effects; the lesser authority a card names and the land
keeps; the war layer's feed (the derived-seed casus belli said once at the
first herald, the four instruments as edges with cards in them, the
succession cluster); and the surfaces -- the constitution on the map page,
the whole polity on `world`, and the ruler's PUBLIC reputation under his
face on the board, with his heart never leaving the DM's readout.

Run:  python -m unittest -v test_worldsim.py
"""

import io
import json
import random
import tempfile
import unittest
import unittest.mock
from contextlib import contextmanager, redirect_stdout
from pathlib import Path

import argparse

import conquest
import crime
import places
import quests
import rpg
import rulers
import session
import story
import worldsim


def _world(seed: int = 4471) -> dict:
    return quests.generate_world(seed)


def _flat_world(seed: int = 4471) -> dict:
    """A world whose layer is rolled and then QUIETED at worldgen: every
    land normal, no card standing, no state held, no news. It is the world
    the game shows on a boring day, built LEGALLY -- the layer is present
    and complete, it simply has nothing to say.

    This is the control the derived-seed contract measures against. It is
    deliberately not "a world with no layer": worldgen opens the layer
    before it posts anything, so a land without one is a state the game
    cannot produce, and `worldsim`'s readers are strict about it rather
    than answering neutrally and hiding a bug (develop.md, "No backwards
    compatibility -- ever")."""
    opened = worldsim.open_world

    def quiet(world: dict) -> dict:
        opened(world)
        for polity, land in world["lands"].items():
            land["states"] = []         # assigned, never cleared: a
            layer = land["world"]       # `clear_state` would log an event
            layer["wealth"] = "normal"  # the comparison would then see
            layer["drawn"] = []
            layer["news"] = []
            for track in worldsim.TRACKS:
                layer[worldsim.LIVE_KEY[track]] = None
        return world

    worldsim.open_world = quiet
    try:
        return quests.generate_world(seed)
    finally:
        worldsim.open_world = opened


def _settlements(world: dict, polity: str) -> list[dict]:
    return [world["areas"][aid] for aid in world["lands"][polity]["areas"]
            if world["areas"][aid]["kind"] == "settlement"]


class OpeningCensus(unittest.TestCase):
    """What a fresh fixed-Europe world holds before travel."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.world = _world()

    def test_historical_towns_plus_the_start_tile_are_materialized(self) -> None:
        historical = {name for _r, _c, name, _p, _b, _cap
                      in places.HISTORICAL_CITIES}
        built = {s["name"] for s in quests.settlements(self.world)}
        self.assertTrue(historical <= built)
        start_slot = self.world["settlement_slots"][self.world["start_slot"]]
        self.assertIn(start_slot["area"], self.world["areas"])

    def test_one_capital_a_land_and_it_stays_first(self) -> None:
        # story.py raises its waves from settlements_by_land[land][0] and
        # casts the land's notables onto it: the capital is that seat.
        for polity, setts in quests.settlements_by_land(self.world).items():
            capitals = [s for s in setts if s["capital"]]
            self.assertEqual(len(capitals), 1, polity)
            self.assertIs(setts[0], capitals[0], polity)

    def test_the_world_is_540_natural_areas(self) -> None:
        areas = self.world["areas"].values()
        self.assertEqual(sum(a["kind"] == "natural" for a in areas), 540)

    def test_every_opening_settlement_is_usable(self) -> None:
        # A settlement the party can stand in: known from day one, its
        # required Sites built, its services attached and faced. What it
        # OWES is its tier's row (2026-08-21): a bed, a counter and someone
        # who sets bones everywhere, plus a smith at every tier above the
        # hamlet.
        for settlement in quests.settlements(self.world):
            self.assertTrue(settlement["known"], settlement["name"])
            self.assertTrue(settlement["sites"], settlement["name"])
            kinds = {s["kind"] for s in settlement["services"]}
            owed = set(places.REQUIRED_SERVICES[settlement["subtype"]])
            self.assertTrue(owed <= kinds, settlement["name"])
            self.assertTrue({"lodging", "general_goods", "healer"} <= kinds,
                            settlement["name"])
            self.assertEqual("smith" in kinds,
                             settlement["subtype"] != "hamlet",
                             settlement["name"])
            for service in settlement["services"]:
                self.assertIsNotNone(service["provider"], settlement["name"])


class TheReservePool(unittest.TestCase):
    """Rolled settlement slots are the finite unbuilt census."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.world = _world()

    def test_unmaterialized_slots_wait_in_the_fixed_census(self) -> None:
        for polity in self.world["lands"]:
            waiting = places.reserve_settlements(self.world, polity)
            self.assertTrue(waiting, polity)
            self.assertTrue(all(slot["area"] is None for slot in waiting))

    def test_reserve_entries_are_unbuilt(self) -> None:
        for polity in self.world["lands"]:
            for slot in places.reserve_settlements(self.world, polity):
                self.assertIsNone(slot["area"])
                self.assertIn(slot["id"], self.world["settlement_slots"])

    def test_name_reserves_are_shuffled_without_loss(self) -> None:
        for polity, tiers in places.SETTLEMENT_NAMES.items():
            for tier, names in tiers.items():
                remaining = self.world["name_reserves"][polity][tier]
                used = [slot["name"] for slot in
                        self.world["settlement_slots"].values()
                        if slot["tier"] == tier and not slot["authored"]
                        and slot["name"] in names]
                self.assertEqual(set(remaining) | set(used), set(names))

    def test_the_reserve_rides_the_save(self) -> None:
        clone = json.loads(json.dumps(self.world))
        self.assertEqual(clone["settlement_slots"],
                         self.world["settlement_slots"])
        self.assertEqual(clone["name_reserves"], self.world["name_reserves"])


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
        self.assertTrue(set(places.REQUIRED_SERVICES[area["subtype"]])
                        <= kinds)
        for service in area["services"]:
            self.assertIsNotNone(service["provider"])
            self.assertIn(service["provider"],
                          {npc["id"] for npc in world["npcs"]})

    def test_tier_narrows_the_draw(self) -> None:
        world = _world()
        expected = len(places.reserve_settlements(world, "mortellaria", "town"))
        for _ in range(expected):
            area = places.materialize_settlement(
                world, "mortellaria", need="a rival", tier="town")
            self.assertEqual(area["subtype"], "town")
        self.assertIsNone(places.materialize_settlement(
            world, "mortellaria", need="a rival", tier="town"))

    def test_tags_prefer_a_fitting_skeleton(self) -> None:
        world = _world()
        area = places.materialize_settlement(world, "mortellaria",
                                             need="a counterparty port",
                                             tags=("harbor", "coast"))
        self.assertTrue({"harbor", "coast"}.intersection(area["tags"]),
                        area["tags"])

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

class SeededAndStable(unittest.TestCase):
    """The trim keeps places.py's seed policy: same seed, same world."""

    def test_the_same_seed_opens_the_same_three(self) -> None:
        first, second = _world(881), _world(881)
        self.assertEqual(
            [a["name"] for a in first["areas"].values()],
            [a["name"] for a in second["areas"].values()])
        self.assertEqual(first["lands"], second["lands"])

    def test_another_seed_opens_another_three(self) -> None:
        # The opening draw is the variety: the settlements a land begins
        # with move between playthroughs.
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

    def test_a_clockless_card_cannot_carry_a_while_payload(self) -> None:
        # A card with no clock never ends, so nothing would ever take its
        # `while` states or its `wealth_while` band back off (the shipped
        # example was mortellaria/revocation, which held a land in CRISIS
        # forever).
        with self.assertRaises(ValueError):
            worldsim.card("x/y", "X", "firascir", days=None,
                          state={"while": ("harvest-failed",)})
        with self.assertRaises(ValueError):
            worldsim.card("x/y", "X", "firascir", days=None,
                          state={"set": ("harvest-failed",),
                                 "wealth_while": "crisis"})

    def test_a_same_track_while_admit_is_rejected(self) -> None:
        # The chain trap (the 2026-08-12 repair's cause): a track's draw
        # only runs while its live slot is free, and expiry drops the live
        # card's `while` states first -- so a card admitting on a state
        # only its OWN track holds as `while` can never fire. Cross-track
        # `while` admits (a crisis card riding a season card's drought)
        # stay legal.
        setter = worldsim.card("x/setter", "X", "firascir", days=(5, 10),
                               news="x",
                               state={"while": ("harvest-failed",)})
        waiter = worldsim.card("x/waiter", "X", "firascir",
                               states=("harvest-failed",), news="x")
        with self.assertRaises(ValueError):
            worldsim._validate_reachability((setter, waiter))
        season = worldsim.card("x/season", "X", "firascir", days=(5, 10),
                               track="season", news="x",
                               state={"while": ("harvest-failed",)})
        worldsim._validate_reachability((season, waiter))   # cross-track
        keeper = worldsim.card("x/keeper", "X", "firascir", days=(5, 10),
                               news="x",
                               state={"set": ("harvest-failed",)})
        worldsim._validate_reachability((keeper, waiter))   # outlives it

    def test_no_card_exceeds_the_five_outlets_or_declares_none(self) -> None:
        for card in worldsim.CARDS:
            self.assertTrue(card["outlets"], card["key"])
            self.assertLessEqual(len(card["outlets"]), 5, card["key"])
            self.assertFalse(set(card["outlets"]) - set(worldsim.OUTLETS),
                             card["key"])

    def test_every_card_admits_over_the_documented_axes(self) -> None:
        for card in worldsim.CARDS:
            self.assertEqual(set(card["admits"]),
                             {"wealth", "states", "without", "weather",
                              "wet", "dry", "tension", "constitution",
                              "traits", "succession", "edge"},
                             card["key"])

    def test_the_floor_is_two_cards_a_land(self) -> None:
        # The asymmetry doctrine's floor, as far as the shipped content
        # goes: every land has something each of its three decks can draw.
        for polity in places.LAND_SPECS:
            own = [c for c in worldsim.CARDS
                   if c["track"] == "crisis" and worldsim.in_land(c, polity)]
            self.assertGreaterEqual(len(own), 2, polity)
            for track in ("weather", "season"):
                deck = [c for c in worldsim.CARDS if c["track"] == track
                        and worldsim.in_land(c, polity)]
                self.assertTrue(deck, (polity, track))

    def test_a_slot_member_is_never_set_as_a_free_state(self) -> None:
        """The exclusive-slot discipline. STATE_SLOTS is EMPTY since the
        human contraction -- both authored slots belonged wholly to deleted
        countries -- so this guard is currently watching nothing, which is
        the state the assertion below pins. The frame stays because the next
        country packet plugs a slot in with one row, and on that day this
        test is what stops it being set as a free state."""
        self.assertEqual(worldsim.SLOT_OF, {})
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
        armory -- is identical when the layer has nothing to say.

        Since the economy floor (2026-08-09) there is exactly ONE exception,
        and it is the point of that session: what a posting QUOTES reads the
        land's wealth band. The stream is still untouched -- same
        geography, same cast, same templates, same levels, same clocks --
        so `gold_total` is what this comparison lifts out, and the test
        below is what pins it instead.

        The control is a world whose layer is rolled and then QUIETED, not
        one built without a layer: every land normal, no card standing, no
        state held. That is a state the game produces all the time, and the
        readers are strict about the one it never produces."""
        def stripped(world: dict) -> str:
            world = json.loads(json.dumps(world))
            for land in world["lands"].values():
                land.pop("world", None)
                land["states"] = []
            for quest in world["quests"].values():
                quest.pop("gold_total", None)
            world["events"] = [e for e in world["events"]
                               if e["action"] != "add_state"]
            return json.dumps(world, sort_keys=True)

        self.assertEqual(stripped(_flat_world(2026)),
                         stripped(_world(2026)))

    def test_the_quoted_gold_is_the_one_thing_the_layer_moves(self) -> None:
        """...and it moves it by exactly `board_pay` -- the band's own
        multiplier times whatever card was standing over the land when the
        posting went up. A land that opened in crisis is already living
        through its first card at worldgen, so the band alone is the right
        answer only where nothing stands (asserted separately below)."""
        quiet = {q["id"]: q["gold_total"]
                 for q in _flat_world(2026)["quests"].values()
                 if q.get("kind") != "delivery"}
        world = _world(2026)
        seen_bare = False
        for quest in world["quests"].values():
            if quest.get("kind") == "delivery":
                continue        # the road pays by the day, not by the land
            if quest.get("reward_weapon"):
                continue        # ...and a job paying in steel quotes no gold
            polity = world["areas"][quest["origin"]]["land"]
            self.assertEqual(quest["gold_total"],
                             max(1, round(quiet[quest["id"]]
                                          * worldsim.board_pay(world,
                                                               polity))),
                             quest["id"])
            if not worldsim.live_cards(world, polity):
                seen_bare = True
                self.assertEqual(
                    quest["gold_total"],
                    max(1, round(quiet[quest["id"]] * worldsim.BAND_PAY[
                        worldsim.wealth_of(world, polity)])), quest["id"])
        self.assertTrue(seen_bare, "no quiet land in this world")

    def test_a_band_a_card_moved_for_its_clock_comes_back(self) -> None:
        world = _world(3)
        worldsim.set_wealth(world, "firascir", "normal", 0)
        live = _fire(world, "firascir", "firascir/bad-harvest", 5)["live"]
        self.assertEqual(worldsim.wealth_of(world, "firascir"), "crisis")
        _layer(world, "firascir")["rolled_day"] = live["until"] - 1
        worldsim.roll_land(world, "firascir", live["until"])
        self.assertEqual(worldsim.wealth_of(world, "firascir"), "normal")

    def test_the_band_has_a_temporary_way_down(self) -> None:
        """A surviving card can push a land into crisis temporarily; its
        clock restores the prior band, as the preceding behavior test pins."""
        down = {c["key"] for c in worldsim.CARDS
                if (c["outlets"].get("state") or {}).get("wealth") == "crisis"
                or (c["outlets"].get("state") or {}).get("wealth_while")
                == "crisis"}
        self.assertTrue(down)


class ThePerLandSaveState(unittest.TestCase):
    """What the save grows: one plain dict per land, JSON all the way."""

    def test_every_land_carries_the_documented_layer(self) -> None:
        world = _world()
        for polity in world["lands"]:
            layer = _layer(world, polity)
            self.assertEqual(set(layer),
                             {"wealth", "wealth_day", "deck", "drawn",
                              "live", "news", "news_seq", "told_seq",
                              "rolled_day",
                              "weather_deck", "season_deck", "weather_live",
                              "season_live", "weather", "weather_day",
                              "wet", "dry",
                              # the politics rung (2026-08-10)
                              "constitution", "tensions", "ruler",
                              "authorities",
                              # ...and the religion & magic rung (2026-08-11):
                              # the one thing an OPTION can buy that outlives
                              # the transaction
                              "bought_sky"})

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
        """...its own cards, minus the ones its rolled tensions shut out.
        The tension gate is the politics rung's whole economy: a Firascir
        where the crown is fighting its lords never holds the temple's
        cards at all (2026-08-10)."""
        world = _world()
        for polity in world["lands"]:
            held_tensions = worldsim.tensions_of(world, polity)
            own = {c["key"] for c in worldsim.CARDS
                   if worldsim.in_land(c, polity)
                   and worldsim._tension_gate(c, held_tensions)}
            shut = {c["key"] for c in worldsim.CARDS
                    if worldsim.in_land(c, polity)} - own
            layer = _layer(world, polity)
            held = {d["key"] for d in layer["drawn"]}
            for track in worldsim.TRACKS:
                held |= set(layer[worldsim.DECK_KEY[track]])
            self.assertEqual(held, own, polity)
            self.assertFalse(held & shut, polity)

    def test_the_deck_order_is_seeded_and_stable(self) -> None:
        self.assertEqual(_layer(_world(881), "firascir")["deck"],
                         _layer(_world(881), "firascir")["deck"])

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

    def test_a_card_blocked_by_a_state_it_forbids(self) -> None:
        world = _world()
        worldsim.set_wealth(world, "firascir", "crisis", 0)
        spec = worldsim.CARDS_BY_KEY["firascir/war-debts"]["admits"]
        self.assertTrue(worldsim.admits(world, "firascir", spec))
        worldsim.set_state(world, "firascir", "harvest-failed", 2)
        self.assertFalse(worldsim.admits(world, "firascir", spec))

    def test_an_exhausted_deck_reshuffles(self) -> None:
        world = _world()
        polity = "tergal"
        worldsim.set_wealth(world, polity, "crisis", 0)
        _layer(world, polity)["deck"] = []
        drawn = worldsim._draw(world, polity, random.Random(5))
        self.assertIsNotNone(drawn)
        self.assertEqual(drawn["land"], (polity,))


class TheCardsClock(unittest.TestCase):
    """What a pulse leaves behind when its day-stamp runs out."""

    def test_a_while_state_comes_off_and_the_mark_it_left_stands(self
                                                                 ) -> None:
        world = _world()
        layer = _fire(world, "tergal", "tergal/herd-fails", 10)
        held = lambda: [s["id"] for s in worldsim.held_states(world,
                                                             "tergal")]
        self.assertIn("herd-loss", held())
        self.assertIn("grass-gone", held())
        layer["rolled_day"] = layer["live"]["until"] - 1
        worldsim.roll_land(world, "tergal", layer["live"]["until"])
        self.assertNotIn("herd-loss", held())           # the card's own
        self.assertIn("grass-gone", held())             # the mark it left

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

    def test_it_reaches_every_land_down_the_edge(self) -> None:
        world = _world()
        worldsim.set_state(world, "firascir", "harvest-failed", 5)
        fed = {e["to"] for e in worldsim.RELATIONS
               if e["from"] == "firascir" and e["then"] == "grain-scarce"}
        for polity in fed:
            self.assertIn("grain-scarce",
                          worldsim.state_ids(world, polity), polity)

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
                "position": session._area_position(
                    quests.settlements_by_land(world)["firascir"][0])}

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


# =========================================================================== #
# THE WEATHER (2026-08-08) -- the ladder's first content rung
# =========================================================================== #

def _sky(world: dict, polity: str, word: str) -> None:
    """Put a sky over a land by hand. The tests drive the weather directly
    so they never have to wait on a 5%-a-day storm to turn up."""
    _layer(world, polity)["weather"] = word


def _party(n: int = 2, level: int = 3) -> list:
    import people
    party = []
    for i in range(n):
        h = people.make_character(random.Random(400 + i), level=level)
        h.name = f"Hero{i}"
        h.conditions = []
        party.append(h)
    return party


class TheDayRoll(unittest.TestCase):
    """The sky: one word a land a day, off the climate of the ground the
    party is standing on and the season of the year."""

    def test_every_land_holds_a_legal_sky_once_it_has_been_rolled(self
                                                                  ) -> None:
        world = _world()
        worldsim.roll_world(world, 20)
        for polity in world["lands"]:
            self.assertIn(_layer(world, polity)["weather"],
                          worldsim.WEATHER_WORDS, polity)
            self.assertEqual(_layer(world, polity)["weather_day"], 20)

    def test_a_fresh_world_has_no_sky_yet(self) -> None:
        # Day 0 is worldgen's bookkeeping: a sky is a thing that happens on
        # a day somebody played.
        world = _world()
        for polity in world["lands"]:
            self.assertEqual(_layer(world, polity)["weather"], "")

    def test_the_spells_count_and_break(self) -> None:
        world = _world()
        polity, layer = "firascir", _layer(world, "firascir")
        rng = random.Random(0)
        # DRY is days since the last rain, so an overcast day extends it;
        # WET is a run of wet days that a DRY day breaks and an overcast
        # one does not. Two counters, two meanings, on purpose.
        for word, wet, dry in (("rain", 1, 0), ("rain", 2, 0),
                               ("cloud", 2, 1),      # no rain, but no break
                               ("fog", 2, 2),
                               ("clear", 0, 3),      # a dry day breaks it
                               ("heat", 0, 4),
                               ("frost", 0, 5),
                               ("storm", 1, 0)):
            layer["weather_live"] = None
            with unittest.mock.patch.object(worldsim, "roll_weather",
                                            return_value=word):
                worldsim._roll_sky(world, polity, 1, rng)
            self.assertEqual((layer["wet"], layer["dry"]), (wet, dry), word)

    def test_a_drought_makes_its_own_weather(self) -> None:
        """The season state bending the roll that produced it -- which is
        why a drought lasts past the day that started it."""
        world = _world()
        base = worldsim.weather_weights(world, "firascir", 1)
        worldsim.set_state(world, "firascir", "drought", day=1)
        dry = worldsim.weather_weights(world, "firascir", 1)
        self.assertLess(dry["rain"], base["rain"])
        self.assertGreater(dry["clear"], base["clear"])

    def test_a_card_that_is_the_weather_holds_the_sky(self) -> None:
        """A storm declared to last three days is a storm on all three: the
        alternative is a state readout saying "the storm has closed the roads"
        under clear skies, which the player would see immediately."""
        world = _world()
        worldsim.roll_world(world, 3)
        _sky(world, "firascir", "storm")
        worldsim._fire(world, "firascir", worldsim.CARDS_BY_KEY["weather/storm"],
                       4, random.Random(1))
        layer = _layer(world, "firascir")
        self.assertGreater(layer["weather_live"]["until"], 4)
        layer["rolled_day"] = 4
        worldsim.roll_land(world, "firascir", layer["weather_live"]["until"] - 1)
        self.assertEqual(layer["weather"], "storm")

    def test_the_sky_rides_the_lazy_roll_like_everything_else(self) -> None:
        watched, ignored = _world(77), _world(77)
        for day in range(1, 41):
            worldsim.roll_world(watched, day)
        worldsim.roll_world(ignored, 40)
        for polity in watched["lands"]:
            self.assertEqual(_layer(ignored, polity)["weather"],
                             _layer(watched, polity)["weather"], polity)


class TheThreeTracks(unittest.TestCase):
    """One live card per track, because one slot could not hold them: a
    season of drought would have blocked every storm under it."""

    def test_each_track_has_its_own_deck_and_its_own_live_slot(self) -> None:
        world = _world()
        layer = _layer(world, "firascir")
        for track in worldsim.TRACKS:
            self.assertIn(worldsim.DECK_KEY[track], layer)
            self.assertIn(worldsim.LIVE_KEY[track], layer)
        self.assertEqual(len(set(worldsim.LIVE_KEY.values())), 3)

    def test_a_storm_does_not_block_the_harvest_failing(self) -> None:
        world = _world()
        worldsim.roll_world(world, 2)
        _sky(world, "firascir", "storm")
        worldsim._fire(world, "firascir",
                       worldsim.CARDS_BY_KEY["weather/storm"], 3,
                       random.Random(1))
        worldsim._fire(world, "firascir",
                       worldsim.CARDS_BY_KEY["firascir/bad-harvest"], 3,
                       random.Random(1))
        layer = _layer(world, "firascir")
        self.assertIsNotNone(layer["weather_live"])
        self.assertIsNotNone(layer["live"])
        held = set(worldsim.state_ids(world, "firascir"))
        self.assertIn("storm-bound", held)
        self.assertIn("harvest-failed", held)

    def test_a_weather_card_carries_no_wealth_condition(self) -> None:
        # A prosperous land gets the same storms as a starving one: that is
        # what makes weather the outlet that reaches a quiet world.
        for card in worldsim.CARDS:
            if card["track"] == "crisis":
                continue
            self.assertEqual(card["admits"]["wealth"], worldsim.BANDS,
                             card["key"])

    def test_a_land_agnostic_card_sits_in_every_land_s_deck(self) -> None:
        world = _world()
        for polity in world["lands"]:
            self.assertIn("weather/storm",
                          _layer(world, polity)["weather_deck"], polity)

class TheWeatherCards(unittest.TestCase):
    """What the authored deck does when it fires."""

    def test_the_ford_needs_a_spell_not_a_shower(self) -> None:
        world = _world()
        worldsim.roll_world(world, 1)
        spec = worldsim.CARDS_BY_KEY["weather/fords-out"]["admits"]
        layer = _layer(world, "firascir")
        layer["wet"] = 1
        self.assertFalse(worldsim.admits(world, "firascir", spec))
        layer["wet"] = 3
        self.assertTrue(worldsim.admits(world, "firascir", spec))

    def test_the_ford_is_a_human_lands_card(self) -> None:
        card = worldsim.CARDS_BY_KEY["weather/fords-out"]
        self.assertEqual(set(card["land"]), {"firascir", "mortellaria"})
        self.assertFalse(worldsim.in_land(card, "tergal"))

    def test_the_fog_names_its_cause_and_keeps_him(self) -> None:
        """The rumor address, kept cheap: a name and a level on the land
        record and nothing else -- and the SAME man next fog, which is what
        makes him a face instead of a pulse."""
        world = _world()
        worldsim.roll_world(world, 1)
        _fire(world, "tergal", "weather/fog-bones", 5)
        who = worldsim.named_necromancer(world, "tergal")
        self.assertIsNotNone(who)
        self.assertTrue(who["name"])
        self.assertTrue(3 <= who["level"] <= 14)
        self.assertEqual(who["since"], 5)
        news = _layer(world, "tergal")["news"][-1]["line"]
        self.assertIn(who["name"], news)
        self.assertNotIn("{", news)
        worldsim._end(world, "tergal", 25, "weather")
        _fire(world, "tergal", "weather/fog-bones", 40)
        self.assertEqual(worldsim.named_necromancer(world, "tergal")["name"],
                         who["name"])

class TheDiseaseFamily(unittest.TestCase):
    """The conditions framework's third family, cashed by the weather:
    small, slow, treatable -- an illness-shaped wound."""

    def test_a_chill_is_a_cold_and_a_second_deepens_it(self) -> None:
        import rpg
        h = _party(1)[0]
        self.assertEqual(rpg.catch_chill(h), "cold")
        self.assertEqual(rpg.catch_chill(h), "pneumonia")
        self.assertIsNone(rpg.catch_chill(h))       # bounded: no third rung
        self.assertEqual([c.kind for c in h.conditions], ["pneumonia"])

    def test_an_illness_costs_the_ceiling_and_never_ticks(self) -> None:
        import rpg
        h = _party(1)[0]
        whole = h.hp_ceiling
        rpg.catch_chill(h)
        self.assertEqual(h.hp_ceiling, whole - rpg.DISEASE_LOAD["cold"])
        self.assertTrue(h.sick)
        before, log = h.hp, []
        rpg._tick_conditions([h], {h}, log)
        self.assertEqual(h.hp, before)              # no per-round arithmetic
        self.assertEqual(log, [])

    def test_the_ceiling_never_falls_past_the_floor(self) -> None:
        import rpg
        h = _party(1)[0]
        rpg.catch_chill(h)
        rpg.catch_chill(h)
        self.assertGreaterEqual(h.hp_ceiling,
                                h.max_hp // rpg.WOUND_HP_FLOOR_DIV)

    def test_the_night_does_not_sweat_it_out_but_rolls_against_it(self
                                                                  ) -> None:
        import rpg
        h = _party(1)[0]
        rpg.catch_chill(h)
        # A night whose roll misses leaves it exactly where it was.
        with unittest.mock.patch.object(random.Random, "randint",
                                        return_value=1):
            rpg.long_rest([h], rpg.Clock(), [], rng=random.Random(1))
        self.assertTrue(h.sick)

    def test_a_made_shake_eases_one_rung(self) -> None:
        import rpg
        h = _party(1)[0]
        rpg.catch_chill(h)
        rpg.catch_chill(h)
        with unittest.mock.patch.object(random.Random, "randint",
                                        return_value=6):
            rpg.shake_disease(h, random.Random(1), [], bed=True)
        self.assertEqual([c.kind for c in h.conditions], ["cold"])
        with unittest.mock.patch.object(random.Random, "randint",
                                        return_value=6):
            rpg.shake_disease(h, random.Random(1), [], bed=True)
        self.assertFalse(h.sick)

    def test_a_roof_is_the_answer_to_the_weather(self) -> None:
        import rpg
        for sheltered in (False, True):
            party = _party(3)
            with unittest.mock.patch.object(random.Random, "randint",
                                            return_value=1):
                rpg.long_rest(party, rpg.Clock(), [], rng=random.Random(1),
                              sky="storm", sheltered=sheltered)
            caught = sum(h.sick for h in party)
            self.assertEqual(caught, 0 if sheltered else 3)

    def test_the_smog_gets_in_under_the_roof(self) -> None:
        import rpg
        self.assertIn("smog", rpg.INDOOR_SKY)
        party = _party(2)
        with unittest.mock.patch.object(random.Random, "randint",
                                        return_value=1):
            rpg.long_rest(party, rpg.Clock(), [], rng=random.Random(1),
                          sky="smog", bed=True)
        self.assertTrue(all(h.sick for h in party))

    def test_the_healer_s_cap_gates_the_illness_too(self) -> None:
        import rpg
        h = _party(1)[0]
        rpg.catch_chill(h)
        rpg.catch_chill(h)                          # pneumonia
        self.assertIsNone(rpg.treat_disease(h, "village"))
        self.assertEqual(rpg.treat_disease(h, "town"), "pneumonia")
        rpg.catch_chill(h)
        self.assertEqual(rpg.treat_disease(h, "village"), "cold")

    def test_the_shake_rides_a_stat_that_does_not_inflate(self) -> None:
        """STR, not STA: STA is a POOL that doubles over twenty levels, and
        an illness that got easier to shake as you levelled would inflate
        exactly the way this game's costs never do."""
        import rpg
        rolls = []
        for level in (1, 20):
            h = _party(1, level=level)[0]
            rpg.catch_chill(h)
            log = []
            rpg.shake_disease(h, random.Random(4), log, bed=False)
            rolls.append(next(l for l in log if "disease:" in l))
        self.assertTrue(all("STR" in line for line in rolls))
        self.assertNotIn("STA", " ".join(rolls))


class TheStormInTheFight(unittest.TestCase):
    """One field knob and one save, as worldsim.md asks for."""

    def _fight(self, weather: str):
        import rpg, sites
        rng = random.Random(11)
        party = _party(2, level=5)
        rpg.equip_weapon(party[0], rpg.WEAPONS["shortbow"], [])
        party[0].items["arrows"] = 40
        foes = [sites.make_foe("cutthroat", i, rng) for i in range(3)]
        log = rpg.CombatLog()
        rpg.group_combat(party, foes, rng, log, field=rpg.WILD_FIELD,
                         weather=weather)
        return log

    def test_the_storm_drags_a_shot_and_nothing_else(self) -> None:
        import rpg
        log = self._fight("storm")
        shots = [l for l in log if "pressure" in l and "arrows:" in l]
        self.assertTrue(shots)
        self.assertTrue(all("-2 storm" in l for l in shots), shots[:2])
        # ...and nothing else: a bolt does not care about the wind, and
        # neither does an axe.
        others = [l for l in log if "pressure" in l and "arrows:" not in l]
        self.assertTrue(others)
        self.assertTrue(all("storm" not in l for l in others), others[:2])

    def test_a_clear_day_costs_nobody_anything(self) -> None:
        log = self._fight("clear")
        self.assertFalse([l for l in log if "storm" in l])

    def test_the_slip_costs_the_step_not_the_round(self) -> None:
        import rpg
        log = self._fight("storm")
        slips = [l for l in log if "storm slip" in l]
        self.assertTrue(slips)
        # A body that slipped still acted: the fight resolved either way.
        self.assertTrue([l for l in log if "pressure" in l])

    def test_the_sky_is_put_on_both_sides_and_comes_off_after(self) -> None:
        import rpg, sites
        rng = random.Random(2)
        party = _party(2, level=4)
        foes = [sites.make_foe("cutthroat", i, rng) for i in range(2)]
        rpg.group_combat(party, foes, rng, rpg.CombatLog(),
                         field=rpg.WILD_FIELD, weather="storm")
        rpg._clear_fight_states(party + foes)
        self.assertTrue(all(e.storm_pen == 0 for e in party + foes))

    def test_a_room_has_no_sky_in_it(self) -> None:
        import session
        state = {"world": None, "position": {"land": "firascir",
                                             "site": "site/x"},
                 "clock": None}
        self.assertEqual(session.fight_sky(state), "")


class TheWeatherSurfaces(unittest.TestCase):
    """What the player and the DM actually see."""

    def test_the_state_diff_carries_the_sky(self) -> None:
        world = _world()
        worldsim.roll_world(world, 9)
        lines = worldsim.land_lines(world, "firascir")
        self.assertTrue(any("WEATHER:" in line for line in lines))
        for line in lines:
            self.assertTrue(line.isascii(), line)

    def test_a_long_spell_says_so(self) -> None:
        world = _world()
        worldsim.roll_world(world, 5)
        layer = _layer(world, "firascir")
        layer["weather"], layer["wet"], layer["dry"] = "rain", 4, 0
        self.assertIn("4th wet day", worldsim.weather_line(world, "firascir"))
        layer["weather"], layer["wet"], layer["dry"] = "clear", 0, 12
        self.assertIn("12 days without rain",
                      worldsim.weather_line(world, "firascir"))

    def test_the_dm_inventory_shows_the_sky_and_all_three_decks(self
                                                                ) -> None:
        world = _world()
        worldsim.roll_world(world, 30)
        text = "\n".join(worldsim.world_lines(world))
        self.assertIn("sky:", text)
        for track in worldsim.TRACKS:
            self.assertIn(f"{track} ", text)

    def test_the_cabin_table_is_a_sight_and_a_dm_note(self) -> None:
        kinds = set()
        for seed in range(200):
            found = worldsim.cabin(random.Random(seed))
            kinds.add(found["kind"])
            self.assertIn(found["host"], found["sight"])
            self.assertNotIn(found["dm"], found["sight"])
            self.assertTrue(found["sight"].isascii())
            self.assertTrue(found["dm"].isascii())
        self.assertEqual(kinds, {"helpful", "job", "valuable", "sinister",
                                 "priced"})

    def test_the_sinister_row_never_announces_itself(self) -> None:
        """The quest twist's rule, applied to a camp: a display that gave
        the host away would be no scene at all."""
        for seed in range(200):
            found = worldsim.cabin(random.Random(seed))
            if found["kind"] != "sinister":
                continue
            for tell in ("sinister", "harm", "axe", "under the floor"):
                self.assertNotIn(tell, found["sight"].lower())
            self.assertIn("DM EYES ONLY", found["dm"])

    def test_the_weather_costs_the_road_a_day(self) -> None:
        world = _world()
        worldsim.roll_world(world, 4)
        self.assertEqual(worldsim.travel_delay(world,
                                               ["firascir", "tergal"])[0], 0)
        worldsim.set_state(world, "firascir", "fords-out", day=4)
        days, why = worldsim.travel_delay(world, ["firascir", "tergal"])
        self.assertEqual(days, 1)
        self.assertIn("fords", why[0])

    def test_the_weather_labels_fit_the_phone_and_stay_ascii(self) -> None:
        labels = (list(worldsim.WEATHER_WORDS.values())
                  + [w for local in worldsim.WEATHER_LOCAL.values()
                     for w in local.values()])
        for label in labels:
            self.assertLessEqual(len(label), WIDTH, label)
            self.assertTrue(label.isascii(), label)
        for line in worldsim.TRAVEL_SLOW.values():      # prose, not a label
            self.assertTrue(line.isascii(), line)


class TheWeatherSessionWiring(unittest.TestCase):
    """The rung is only real if play reads it."""

    @staticmethod
    def _state(world: dict, day: int) -> dict:
        import rpg
        return {"world": world, "clock": rpg.Clock(day=day),
                "rng": random.Random(3), "party": [], "accepted": [],
                "active_quest": None, "purse": rpg.Purse(gold=0),
                "position": session._area_position(
                    quests.settlements_by_land(world)["firascir"][0])}

    def test_the_road_tells_the_party_the_sky(self) -> None:
        import session
        world = _world(4471)
        state = self._state(world, 12)
        out = io.StringIO()
        with redirect_stdout(out):
            session.weather_note(state)
        self.assertIn("WEATHER:", out.getvalue())

    def test_the_smog_is_what_a_town_night_is_paid_for(self) -> None:
        import session
        world = _world(4471)
        state = self._state(world, 6)
        session.sky_here(state)
        worldsim.set_state(world, "firascir", "smog", day=6)
        self.assertEqual(session.exposure_sky(state), "smog")

    def test_a_storm_night_rolls_the_cabin_table(self) -> None:
        import rpg, session
        world = _world(4471)
        state = self._state(world, 6)
        state["rng"] = random.Random(2)
        log = rpg.CombatLog()
        found = None
        for _ in range(20):             # SHELTER_CHANCE is not 1.0
            found = session.shelter_here(state, log)
            if found is not None:
                break
        self.assertIsNotNone(found)
        text = "\n".join(log.player)
        self.assertIn("SHELTER:", text)
        self.assertIn("DM eyes only", text)
        for line in log.player:
            self.assertLessEqual(len(line), WIDTH, line)

    def test_a_road_fight_is_fought_in_the_weather(self) -> None:
        import session
        world = _world(4471)
        state = self._state(world, 15)
        session.sky_here(state)         # roll first, then put a sky on it
        _sky(world, "firascir", "storm")
        self.assertEqual(session.fight_sky(state), "storm")

    def test_every_night_of_a_leg_is_paid_at_its_own_sky(self) -> None:
        """`travel`'s night loop asks for the sky once a night and
        `long_rest` advances the day between asks -- so `exposure_sky`
        rolls the world up to TODAY like every other reader. Without it a
        four-day leg charged the departure day's weather four times: four
        exposure checks in one storm, four cabin rolls, four morale hits."""
        import session
        world = _world(4471)
        state = self._state(world, 1)
        twin = _world(4471)             # the same world, rolled by hand
        seen = []
        for day in range(1, 13):
            state["clock"].day = day    # what a night on the road does
            got = session.exposure_sky(state)
            worldsim.roll_world(twin, day)
            want = ("smog" if "smog" in worldsim.state_ids(twin, "firascir")
                    else worldsim.weather_of(twin, "firascir"))
            self.assertEqual(got, want, day)
            self.assertEqual(_layer(world, "firascir")["rolled_day"], day)
            seen.append(got)
        self.assertGreater(len(set(seen)), 1)   # and it is not one frozen sky

    def test_the_storm_rides_a_paused_fight_to_its_resume(self) -> None:
        import session
        pending = {"foes": [], "fired": set(), "round": 2, "crossings": [],
                   "xp": 10, "site": None, "room": None, "field": 2,
                   "weather": "storm"}
        wire = session._pending_to_dict(pending, [])
        self.assertEqual(wire["weather"], "storm")
        self.assertEqual(session._pending_from_dict(
            json.loads(json.dumps(wire)), [])["weather"], "storm")


# =========================================================================== #
# THE ECONOMY FLOOR (2026-08-09) -- the three outlets the frame carried
# =========================================================================== #

def _quiet(world: dict, polity: str, band: str = "normal") -> None:
    """Take everything off a land: no band effect, no card, no state. The
    outlet tests need a zero to measure from, and a generated world hands
    out crises it did not ask for."""
    layer = _layer(world, polity)
    for track in worldsim.TRACKS:
        layer[worldsim.LIVE_KEY[track]] = None
    for entry in list(worldsim.held_states(world, polity)):
        worldsim.drop_state(world, polity, entry["id"], 0)
    layer["wealth"] = band


def _all_quiet(world: dict) -> None:
    for polity in world["lands"]:
        _quiet(world, polity)


class TheBoardOutlet(unittest.TestCase):
    """THE FIRST INVARIANT: the board reacts to world state."""

    def test_the_band_moves_the_slot_count(self) -> None:
        world = _world()
        _all_quiet(world)
        town = next(s for s in quests.settlements_by_land(world)["firascir"]
                    if not s["capital"] and s["subtype"] == "town")
        town["board_active"] = True     # this is the BAND's test; whether
                                        # the town posts ordinary work at
                                        # all is the sparse-board roll's
                                        # (2026-08-15, test_quest_geography)
        base = quests.SETTLEMENT_KINDS[places.settlement_tier(town)][0]
        for band, want in worldsim.BAND_SLOTS.items():
            _quiet(world, "firascir", band)
            self.assertEqual(quests.board_slots(world, town), base + want,
                             band)

    def test_the_band_moves_what_a_posting_quotes(self) -> None:
        world = _world()
        _all_quiet(world)
        for band, want in worldsim.BAND_PAY.items():
            _quiet(world, "firascir", band)
            self.assertAlmostEqual(worldsim.board_pay(world, "firascir"),
                                   want)

    def test_a_card_reprices_the_whole_board(self) -> None:
        # THE REPRICE VERB. Mortellaria paying its swords in notes quotes
        # half again as much for everything on the board.
        world = _world()
        _all_quiet(world)
        before = worldsim.board_pay(world, "mortellaria")
        _fire(world, "mortellaria", "mortellaria/paid-in-paper", 3)
        self.assertGreater(worldsim.board_pay(world, "mortellaria"), before)
        _all_quiet(world)
        _fire(world, "firascir", "firascir/war-debts", 3)   # ...and down
        self.assertLess(worldsim.board_pay(world, "firascir"), 1.0)

    def test_a_card_puts_its_own_job_up(self) -> None:
        # THE POST VERB, end to end: the card fires, the board refills, and
        # the job is on it with the card's key, its title and its premium.
        world = _world()
        _all_quiet(world)
        _fire(world, "tergal", "tergal/tribute", 4)
        town = quests.settlements_by_land(world)["tergal"][0]
        posted = quests.refresh_settlement_board(world, town, 4,
                                                 random.Random(5))
        mine = [q for q in posted if q.get("world_card") == "tergal/tribute"]
        self.assertEqual(len(mine), 1)
        self.assertEqual(mine[0]["name"], "The Chief's New Men")
        self.assertTrue(mine[0]["giver"])
        self.assertTrue(mine[0]["sites"])
        self.assertIsNotNone(mine[0].get("deadline_day"))

    def test_one_board_never_runs_two_copies_of_one_card_s_job(self) -> None:
        world = _world()
        _all_quiet(world)
        _fire(world, "tergal", "tergal/tribute", 4)
        town = quests.settlements_by_land(world)["tergal"][0]
        for day in range(4, 9):
            quests.refresh_settlement_board(world, town, day,
                                            random.Random(day))
        keys = [world["quests"][qid].get("world_card")
                for qid in town["quests"] if qid in world["quests"]]
        self.assertEqual(keys.count("tergal/tribute"), 1)

    def test_the_card_s_job_lapses_and_the_card_puts_it_back(self) -> None:
        world = _world()
        _all_quiet(world)
        _fire(world, "tergal", "tergal/tribute", 1)
        town = quests.settlements_by_land(world)["tergal"][0]
        quests.refresh_settlement_board(world, town, 1, random.Random(5))
        first = next(qid for qid in town["quests"]
                     if world["quests"][qid].get("world_card"))
        late = world["quests"][first]["deadline_day"] + 2
        quests.expire_settlement_board(world, town, late)
        self.assertNotIn(first, town["quests"])
        quests.refresh_settlement_board(world, town, late, random.Random(5))
        again = [world["quests"][qid].get("world_card")
                 for qid in town["quests"] if qid in world["quests"]]
        self.assertIn("tergal/tribute", again)

    def test_a_finished_card_job_does_not_block_the_repost(self) -> None:
        # The 2026-08-12 repair: a completed posting stays in the
        # settlement's quest list, but only OPEN postings hold the card's
        # place -- the card stands, so its work goes back up. (Before this,
        # finishing a card's job once shut that card off that board for
        # the rest of the campaign.)
        world = _world()
        _all_quiet(world)
        _fire(world, "tergal", "tergal/tribute", 1)
        town = quests.settlements_by_land(world)["tergal"][0]
        quests.refresh_settlement_board(world, town, 1, random.Random(5))
        first = next(qid for qid in town["quests"]
                     if world["quests"][qid].get("world_card"))
        world["quests"][first]["status"] = "done"
        quests.refresh_settlement_board(world, town, 3, random.Random(7))
        open_again = [world["quests"][qid].get("world_card")
                      for qid in town["quests"] if qid in world["quests"]
                      and world["quests"][qid]["status"] == "open"]
        self.assertIn("tergal/tribute", open_again)

    def test_a_taken_card_job_still_holds_the_card_s_place(self) -> None:
        # ...but a job the party is RUNNING is still open, so the card
        # does not double-post under them.
        world = _world()
        _all_quiet(world)
        _fire(world, "tergal", "tergal/tribute", 1)
        town = quests.settlements_by_land(world)["tergal"][0]
        quests.refresh_settlement_board(world, town, 1, random.Random(5))
        quests.refresh_settlement_board(world, town, 3, random.Random(7))
        keys = [world["quests"][qid].get("world_card")
                for qid in town["quests"] if qid in world["quests"]]
        self.assertEqual(keys.count("tergal/tribute"), 1)

    def test_a_card_job_never_pays_in_steel_instead(self) -> None:
        # The weapon-reward mode is a flat share of the ORDINARY board; a
        # card that pays a gold premium must not silently pay it in a blade.
        world = _world()
        _all_quiet(world)
        posted = []
        for polity in world["lands"]:
            for key in [c["key"] for c in worldsim.CARDS
                        if worldsim.in_land(c, polity)
                        and (c["outlets"].get("quest") or {}).get("post")
                        and c["track"] == "crisis"]:
                _quiet(world, polity)
                _fire(world, polity, key, 3)
                town = quests.settlements_by_land(world)[polity][0]
                posted += [q for q in quests.refresh_settlement_board(
                    world, town, 3, random.Random(7))
                    if q.get("world_card")]
        self.assertTrue(posted)
        for quest in posted:
            self.assertIsNone(quest.get("reward_weapon"), quest["name"])


class TheMenuOutlet(unittest.TestCase):
    """THE PRICED MENU: standing actions whose terms local state sets."""

    def test_a_quiet_land_charges_the_catalog(self) -> None:
        world = _world()
        _all_quiet(world)
        self.assertEqual(worldsim.menu_terms(world, "firascir"), {})
        self.assertEqual(worldsim.term(world, "firascir", "goods"), 1.0)
        self.assertEqual(worldsim.priced(world, "firascir", "goods", 40), 40)

    def test_the_engine_takes_the_number_and_asks_nothing(self) -> None:
        # rpg.py never imports worldsim: the markup arrives as a float and
        # the default is the catalog price the benches have always paid.
        purse = rpg.Purse(gold=500)
        hero = _party(1)[0]
        log: list[str] = []
        rpg.buy_potion(hero, purse, "healing", log)
        plain = 500 - purse.gold
        rpg.buy_potion(hero, purse, "healing", log, markup=2.0)
        self.assertEqual(500 - purse.gold, plain + plain * 2)

    def test_the_road_takes_its_toll(self) -> None:
        world = _world()
        _all_quiet(world)
        self.assertEqual(worldsim.road_charges(world, ["firascir"])[0], 0)
        _fire(world, "firascir", "firascir/tolls", 3)
        gold, lines = worldsim.road_charges(world,
                                            ["firascir", "mortellaria"])
        self.assertGreater(gold, 0)
        self.assertTrue(any("toll" in line for line in lines))
        # ...and a land is charged once however often the leg names it.
        twice = worldsim.road_charges(world, ["firascir", "firascir"])[0]
        self.assertEqual(twice, gold)

    def test_the_price_sheet_says_what_the_world_did(self) -> None:
        world = _world()
        _all_quiet(world)
        self.assertEqual(worldsim.menu_lines(world, "firascir"), [])
        _fire(world, "firascir", "firascir/tolls", 3)
        lines = worldsim.menu_lines(world, "firascir")
        self.assertTrue(lines)
        for line in lines:
            self.assertLessEqual(len(line), WIDTH, line)
            self.assertTrue(line.isascii(), line)


class TheEncounterOutlet(unittest.TestCase):
    """The local encounter table: what the world puts on the road."""

    def test_a_quiet_land_has_the_road_s_own_wildlife(self) -> None:
        world = _world()
        _all_quiet(world)
        self.assertEqual(worldsim.encounter_entries(world, "firascir"), [])
        self.assertIsNone(worldsim.local_encounter(world, "firascir", "road",
                                                   random.Random(1)))

    def test_a_card_puts_its_own_people_on_the_ground(self) -> None:
        world = _world()
        _all_quiet(world)
        _fire(world, "firascir", "firascir/tolls", 3)
        road = worldsim.encounter_entries(world, "firascir", "road")
        self.assertEqual(len(road), 1)
        self.assertIn("toll-men", road[0]["as"])
        # ...and only on the ground it named.
        self.assertEqual(worldsim.encounter_entries(world, "firascir",
                                                    "wilds"), [])

    def test_a_derived_state_gets_onto_a_road_too(self) -> None:
        world = _world()
        _all_quiet(world)
        worldsim.set_state(world, "tergal", "raiding", 5)
        self.assertIn("raiders-out", worldsim.state_ids(world, "firascir"))
        road = worldsim.encounter_entries(world, "firascir", "road")
        self.assertEqual([e["as"] for e in road],
                         [worldsim.STATE_ENCOUNTERS["raiders-out"]["as"]])

    def test_the_entry_is_rolled_at_its_own_chance(self) -> None:
        world = _world()
        _all_quiet(world)
        _fire(world, "firascir", "firascir/tolls", 3)
        rng = random.Random(11)
        hits = sum(1 for _ in range(2000)
                   if worldsim.local_encounter(world, "firascir", "road", rng))
        want = worldsim.CARDS_BY_KEY[
            "firascir/tolls"]["outlets"]["encounter"]["chance"]
        self.assertAlmostEqual(hits / 2000, want, delta=0.05)

    def test_it_changes_who_and_never_how_hard(self) -> None:
        """The party-independent danger curve is a contract: a world card
        picks the faces, the road still rolls the level."""
        world = _world()
        _all_quiet(world)
        _fire(world, "firascir", "firascir/tolls", 3)
        entry = worldsim.encounter_entries(world, "firascir", "road")[0]
        for level in (1, 4, 9):
            kinds = quests.build_wild_encounter(level, "firascir",
                                                random.Random(level),
                                                pool=tuple(entry["kinds"]))
            self.assertTrue(kinds)
            for kind in kinds:
                self.assertIn(kind, entry["kinds"])

    def test_the_skin_is_fiction_and_the_row_is_mechanics(self) -> None:
        import sites
        entry = worldsim.CARDS_BY_KEY[
            "firascir/tolls"]["outlets"]["encounter"]
        plain = sites.make_foe("cutthroat", 1, random.Random(3))
        dressed = sites.make_foe("cutthroat", 1, random.Random(3),
                                 display=entry["skins"]["cutthroat"])
        self.assertIn("Toll-Man", dressed.name)
        self.assertEqual((dressed.dex, dressed.str_, dressed.max_hp),
                         (plain.dex, plain.str_, plain.max_hp))


class TheChains(unittest.TestCase):
    """A card sets the state the next card admits on -- and no new
    machinery under it."""

    CHAINS = (
        ("firascir", "firascir/bad-harvest", "bread-dear",
         "firascir/bread-revolt"),
        ("mortellaria", "mortellaria/bank-run", "bad-paper",
         "mortellaria/counterfeit"),
        ("tergal", "tergal/herd-fails", "grass-gone", "tergal/raid"),
    )

    def test_the_link_outlives_the_card_that_set_it(self) -> None:
        for polity, first, link, _second in self.CHAINS:
            world = _world()
            _all_quiet(world)
            _fire(world, polity, first, 3)
            worldsim._end(world, polity, 60,
                          worldsim.CARDS_BY_KEY[first]["track"])
            self.assertIn(link, worldsim.state_ids(world, polity),
                          (polity, first))

    def test_the_next_card_admits_on_it_and_could_not_before(self) -> None:
        for polity, first, _link, second in self.CHAINS:
            world = _world()
            _all_quiet(world)
            spec = worldsim.CARDS_BY_KEY[second]["admits"]
            self.assertFalse(worldsim.admits(world, polity, spec),
                             (polity, second))
            _fire(world, polity, first, 3)
            worldsim._end(world, polity, 60,
                          worldsim.CARDS_BY_KEY[first]["track"])
            self.assertTrue(worldsim.admits(world, polity, spec),
                            (polity, second))

    def test_the_second_card_consumes_the_link(self) -> None:
        for polity, first, link, second in self.CHAINS:
            world = _world()
            _all_quiet(world)
            _fire(world, polity, first, 3)
            worldsim._end(world, polity, 60,
                          worldsim.CARDS_BY_KEY[first]["track"])
            _fire(world, polity, second, 61)
            self.assertNotIn(link, worldsim.state_ids(world, polity),
                             (polity, second))

    def test_the_first_card_does_not_stack_its_own_link(self) -> None:
        for polity, first, link, _second in self.CHAINS:
            spec = worldsim.CARDS_BY_KEY[first]
            state = spec["outlets"]["state"]
            if link in (state.get("slot") or {}).values():
                continue        # an exclusive slot cannot stack by
                                # construction (`_says_nothing_new`)
            self.assertIn(link, spec["admits"]["without"], first)

class ThePoliticsChains(unittest.TestCase):
    """The politics rung's own chains, repaired 2026-08-12: they used to
    wait on a same-track `while` state, which a track's own draw can never
    see (`_validate_reachability` now polices the whole class). Every link
    is a `set` state now, alive after its setter's clock runs out."""

    LINKS = (
        ("mortellaria", "mortellaria/tax-farmer", "tax-farmed",
         "mortellaria/salt-revolt", ("court-vs-provinces",)),
        ("tergal", "tergal/herd-fails", "grass-gone",
         "tergal/mourning-war", ("clan-vs-clan",)),
        ("tergal", "tergal/herd-fails", "grass-gone",
         "tergal/ghost-dance", ("council-vs-outlaws",)),
    )

    def test_each_link_reaches_its_successor(self) -> None:
        for polity, first, link, second, tensions in self.LINKS:
            world = _world()
            _all_quiet(world)
            _layer(world, polity)["tensions"] = list(tensions)
            spec = worldsim.CARDS_BY_KEY[second]["admits"]
            self.assertFalse(worldsim.admits(world, polity, spec), second)
            _fire(world, polity, first, 3)
            worldsim._end(world, polity, 60,
                          worldsim.CARDS_BY_KEY[first]["track"])
            self.assertIn(link, worldsim.state_ids(world, polity), first)
            self.assertTrue(worldsim.admits(world, polity, spec), second)

class TheEconomyFloorContent(unittest.TestCase):
    """What the session was asked to author, asserted as data."""

    def test_the_floor_is_five_crisis_cards_a_land(self) -> None:
        for polity in places.LAND_SPECS:
            own = [c for c in worldsim.CARDS
                   if c["track"] == "crisis" and worldsim.in_land(c, polity)]
            self.assertGreaterEqual(len(own), 5, polity)

    def test_every_land_has_one_card_that_is_not_trouble(self) -> None:
        """The flavor anchor: a world where the only thing that ever
        happens is a disaster reads as a disaster, not as a world. The
        test for 'not trouble' is mechanical -- a card that admits in the
        GOOD bands and leaves the land better off in at least one outlet:
        something cheaper (on the card or through the state it sets), more
        work posted, or better pay for it."""
        for polity in places.LAND_SPECS:
            good = []
            for spec in worldsim.CARDS:
                if spec["track"] != "crisis" or not worldsim.in_land(spec,
                                                                     polity):
                    continue
                if "crisis" in spec["admits"]["wealth"]:
                    continue
                state = spec["outlets"].get("state") or {}
                priced = dict(spec["outlets"].get("menu") or {})
                for state_id in (tuple(state.get("while", ()))
                                 + tuple(state.get("set", ()))
                                 + tuple((state.get("slot") or {}).values())):
                    priced.update(worldsim.STATE_MENU.get(state_id, {}))
                quest = spec["outlets"].get("quest") or {}
                if (any(m < 1 for m in priced.values())
                        or quest.get("slots", 0) > 0
                        or quest.get("reprice", 1.0) > 1.0
                        or quest.get("pay", 1.0) > 1.0
                        or state.get("wealth_while") == "prosperous"):
                    good.append(spec["key"])
            self.assertTrue(good, polity)

    def test_the_relations_table_contains_only_surviving_realms(self) -> None:
        for edge in worldsim.RELATIONS:
            self.assertIn(edge["from"], places.LAND_SPECS)
            self.assertIn(edge["to"], places.LAND_SPECS)

    def test_every_land_sells_what_the_rules_say_it_sells(self) -> None:
        """rules.md's three-country economy, edge by edge. A bare COUNT of
        the table said nothing about whether the goods were there -- the
        Europe closure shipped with only the granary built and the count
        green (2026-08-15)."""
        sells = {"firascir": {"grain", "timber"},
                 "mortellaria": {"coin", "trade"},
                 "tergal": {"horses", "livestock", "service"}}
        for polity, goods in sells.items():
            sold = {e["kind"] for e in worldsim.RELATIONS
                    if e["from"] == polity}
            self.assertTrue(goods <= sold, f"{polity} does not sell {goods - sold}")
        # ...and every export is FELT: a derived word with a price on it.
        for edge in worldsim.RELATIONS:
            if edge["kind"] not in {g for gs in sells.values() for g in gs}:
                continue
            self.assertIn(edge["then"], worldsim.STATE_WORDS)
            self.assertTrue(worldsim.STATE_MENU.get(edge["then"]),
                            f"{edge['then']} reaches no shelf")
        # ...and the drought stands beside the failed harvest at the head
        # of the grain edges (plan.md's own instruction to this session).
        grain = [e for e in worldsim.RELATIONS
                 if e["from"] == "firascir" and e["then"] == "grain-scarce"]
        self.assertTrue(grain)
        for edge in grain:
            self.assertIn("drought", edge["when"])
            self.assertIn("harvest-failed", edge["when"])

    def test_every_posted_job_is_a_legal_quest_template(self) -> None:
        for spec in worldsim.CARDS:
            posted = (spec["outlets"].get("quest") or {}).get("post")
            if not posted:
                continue
            lo, hi = quests.template_band(posted)
            self.assertLessEqual(lo, hi, spec["key"])
            self.assertTrue(quests.quest_place_requirement(posted),
                            spec["key"])
            for text in (posted["title"], posted["desc"],
                         posted["epilogue"], posted["failure_epilogue"]):
                self.assertTrue(text.isascii(), spec["key"])
            self.assertLessEqual(len(posted["title"]), WIDTH, spec["key"])

    def test_the_menu_tables_never_double_charge(self) -> None:
        worldsim._validate_menu_tables()     # raises on a clash

    def test_every_authored_string_fits_and_stays_ascii(self) -> None:
        for spec in worldsim.CARDS:
            entry = spec["outlets"].get("encounter")
            if entry:
                self.assertTrue(entry["as"].isascii(), spec["key"])
                for skin in (entry.get("skins") or {}).values():
                    self.assertTrue(skin.isascii(), spec["key"])
                    self.assertLessEqual(len(skin), 20, skin)
        for label in worldsim.MENU_LABEL.values():
            self.assertLessEqual(len(label) + 12, WIDTH, label)


class TheEconomyFloorWiring(unittest.TestCase):
    """THE SECOND INVARIANT: something moves without the player taking a
    job -- and the board, the prices and the road have all moved by the
    time the party walks back in."""

    @staticmethod
    def _state(world: dict, day: int, polity: str = "firascir") -> dict:
        return {"world": world, "clock": rpg.Clock(day=day),
                "rng": random.Random(3), "party": _party(),
                "accepted": [], "active_quest": None,
                "purse": rpg.Purse(gold=200), "foe_count": 0,
                "position": session._area_position(
                    quests.settlements_by_land(world)[polity][0])}

    def test_the_shop_asks_the_land_what_it_charges(self) -> None:
        import session
        world = _world()
        _all_quiet(world)
        state = self._state(world, 3)
        self.assertEqual(session.local_term(state, "goods"), 1.0)
        _fire(world, "firascir", "firascir/monopoly", 3)
        self.assertGreater(session.local_term(state, "goods"), 1.0)

    def test_the_price_sheet_reads_the_world(self) -> None:
        import session
        world = _world()
        _all_quiet(world)
        _fire(world, "firascir", "firascir/tolls", 3)
        state = self._state(world, 3)
        self.assertIn("toll", session.local_prices(state))
        self.assertEqual(session.local_prices(None), {})

    def test_the_arrival_says_what_the_prices_did(self) -> None:
        import session
        world = _world()
        _all_quiet(world)
        state = self._state(world, 3)
        quiet = io.StringIO()
        with redirect_stdout(quiet):
            session.price_note(state)
        self.assertEqual(quiet.getvalue(), "")
        _fire(world, "firascir", "firascir/monopoly", 3)
        loud = io.StringIO()
        with redirect_stdout(loud):
            session.price_note(state)
        self.assertIn("the shop shelf", loud.getvalue())

    def test_the_road_meets_the_card_s_people(self) -> None:
        import session
        world = _world()
        _all_quiet(world)
        _fire(world, "firascir", "firascir/tolls", 3)
        state = self._state(world, 3)
        state["rng"] = random.Random(2)
        out = io.StringIO()
        for _ in range(40):
            with redirect_stdout(out):
                session.wild_event(state, 1.0, "On the road", where="road")
            if "Toll-" in out.getvalue():
                break
        self.assertIn("Toll-", out.getvalue())

    def test_the_dm_inventory_carries_the_three_outlets(self) -> None:
        world = _world()
        _all_quiet(world)
        # One card a track, as the loop itself would stand them up: two
        # crisis cards on one land would only overwrite each other.
        _fire(world, "firascir", "firascir/tolls", 3)
        _fire(world, "tergal", "tergal/tribute", 3)
        text = "\n".join(worldsim.world_lines(world))
        self.assertIn("board:", text)
        self.assertIn("menu:", text)
        self.assertIn("road:", text)
        self.assertIn("The Chief's New Men", text)
        for line in worldsim.world_lines(world):
            self.assertTrue(line.isascii(), line)

    def test_the_world_moves_the_board_while_nobody_is_looking(self) -> None:
        """The session's headline, measured: leave a world alone for two
        months and its boards are not the boards it was left with. Every
        world does it, and the test walks the days rather than sampling
        the last one -- a card that came and went still moved the board
        while it stood, which is the whole claim."""
        def snapshot(world: dict) -> tuple:
            return (tuple(sorted((s["key"], quests.board_slots(world, s))
                                 for s in quests.settlements(world))),
                    tuple(sorted((p, round(worldsim.board_pay(world, p), 3))
                                 for p in world["lands"])))

        for seed in range(6):
            world = _world(seed)
            start = snapshot(world)
            seen = set()
            for day in range(1, 71):
                worldsim.roll_world(world, day)
                seen.add(snapshot(world))
            self.assertTrue(seen - {start}, seed)


@contextmanager
def _save_sandbox():
    """Point session's save and its three written pages at a throwaway
    directory -- a suite must never overwrite the playthrough."""
    import session
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


class TheRoadCharges(unittest.TestCase):
    """What a tolled, washed-out road takes off ONE EDGE, and what an
    interrupted route leaves behind.

    The paid-crossing marker (`road_paid`, 2026-08-08) is GONE with the grid
    (2026-08-15): it existed only because an interrupted trip bounced the
    party back to where it set out from, so the same crossing had to be
    walked twice and could not honestly be charged twice. A route now stops
    at the Tile it reached, so the next `travel` is a different edge from a
    different place -- a fresh road, honestly priced."""

    @staticmethod
    def _priced_road() -> tuple[dict, dict, dict]:
        """A world whose Firascir charges for its roads both ways -- a
        doubled toll (gold) and fords that are out (gold AND a day)."""
        world = _world(27)
        _fire(world, "firascir", "firascir/tolls", 3)
        worldsim.set_state(world, "firascir", "fords-out", day=3)
        here = _settlements(world, "firascir")[0]
        return world, here, world["tiles"][here["tile"]]

    @staticmethod
    def _state(world: dict, here: dict, day: int = 3) -> dict:
        import karma
        import session
        return {"world": world, "party": _party(), "clock": rpg.Clock(day=day),
                "purse": rpg.Purse(gold=500), "rng": random.Random(4),
                "karma": karma.new_karma(), "crimes": crime.new_crimes(),
                "history": [], "position": session._area_position(here),
                "accepted": [], "active_quest": None, "loose_ends": [],
                "foe_count": 0, "pending": None, "rooms": {},
                "site_clears": {}, "holdings": {}, "story": None,
                "pact": None, "services": {}, "visited": [here["key"]]}

    @staticmethod
    def _travel(state: dict, dest: str, interrupted: bool) -> str:
        """One `travel` command. `interrupted` is the road fight the party
        ran into, stubbed at the one valve the command reads it through."""
        import session
        out = io.StringIO()
        with unittest.mock.patch("session.load", return_value=state), \
                unittest.mock.patch("session.wild_event",
                                    return_value=interrupted), \
                redirect_stdout(out):
            session.cmd_travel(argparse.Namespace(dest=[dest]))
        return out.getvalue()

    def _open_road(self, world: dict, tile: dict) -> tuple[str, str]:
        """A direction out of `tile` that stays inside Firascir and off the
        water, so the leg is a road and its charges are the land's own."""
        for direction in ("east", "west", "north", "south"):
            nid = places.neighbor_id(tile, direction)
            if nid is None:
                continue
            other = world["tiles"][nid]
            if other["country"] == "firascir" and other["biome"] != "sea":
                return direction, nid
        raise AssertionError("no land road out of the test tile")

    def test_one_edge_pays_its_toll_and_walks_its_detour(self) -> None:
        world, here, tile = self._priced_road()
        state = self._state(world, here)
        direction, nid = self._open_road(world, tile)
        with _save_sandbox():
            self._travel(state, direction, interrupted=False)
        self.assertGreater(500 - state["purse"].gold, 0)   # the road took it
        self.assertEqual(state["clock"].day,
                         3 + places.edge_days(tile, nid) + 1)  # + detour
        self.assertEqual(state["position"]["tile"], nid)

    def test_an_interrupted_route_stops_at_the_tile_it_reached(self) -> None:
        """The reason `road_paid` is gone: the party keeps the ground it
        walked, so nothing is ever paid for twice."""
        import session
        world, here, tile = self._priced_road()
        state = self._state(world, here)
        far = max(world["tiles"].values(),
                  key=lambda t: places.path_days(tile["id"], t["id"]))
        route = places.shortest_path(tile["id"], far["id"])
        with _save_sandbox():
            self._travel(state, far["id"].replace("tile/r", "R").replace(
                "/c", "C"), interrupted=True)
            session.save(state)             # what the fight machinery does
            again = session.load()          # ...and what the re-issue reads
        self.assertEqual(state["position"]["tile"], route[1])
        self.assertNotEqual(state["position"]["area"], here["key"])
        self.assertEqual(again["position"]["tile"], route[1])
        self.assertIsNone(again.get("road_paid"))

    def test_the_marker_is_gone_from_the_save_entirely(self) -> None:
        import session
        world, here, _tile = self._priced_road()
        state = self._state(world, here)
        with _save_sandbox():
            session.save(state)
            self.assertNotIn("road_paid",
                             json.loads(session.STATE_PATH.read_text()))


# =========================================================================== #
# POLITICS (2026-08-10, the ladder's third content rung)
# =========================================================================== #


def _politics(spec: dict) -> dict:
    """The politics half of a card's admitting conditions."""
    return {k: spec["admits"].get(k) or ()
            for k in ("tension", "constitution", "traits", "succession",
                      "edge")}


POLITICS_KEYS = ("tension", "constitution", "traits", "succession", "edge")


class TheRulerSheet(unittest.TestCase):
    """`rulers.py`: three weighted draws off 357 words, and the removals
    that make three draws land three compatible ones."""

    def test_the_pool_is_the_documented_size(self) -> None:
        self.assertEqual(rulers.POOL_TOTAL, 357)
        self.assertEqual(rulers.CROWNLESS_TOTAL, 355)
        self.assertEqual(sum(rulers.pool(True).values()), 357)
        self.assertEqual(sum(rulers.pool(False).values()), 355)

    def test_a_crown_draws_three_distinct_words(self) -> None:
        for seed in range(200):
            sheet = rulers.roll_ruler(random.Random(seed))
            self.assertEqual(len(sheet["traits"]), rulers.CROWN_DRAWS, seed)
            self.assertEqual(len(set(sheet["traits"])),
                             len(sheet["traits"]), seed)
            for word in sheet["traits"]:
                self.assertIn(word, rulers.VOCABULARY, word)

    def test_one_pole_per_axis_and_the_extreme_takes_the_whole_axis(self
                                                                   ) -> None:
        for seed in range(400):
            traits = rulers.roll_ruler(random.Random(seed))["traits"]
            axes = [rulers.VOCABULARY[w]["axis"] for w in traits
                    if rulers.VOCABULARY[w]["axis"]]
            self.assertEqual(len(axes), len(set(axes)), traits)
            # ...and the demonstration case: a zealot IS devout, so the
            # faith axis cannot also produce devout or godless.
            if "zealot" in traits:
                self.assertNotIn("devout", traits)
                self.assertNotIn("godless", traits)

    def test_a_never_with_pair_never_rolls_together(self) -> None:
        for seed in range(600):
            traits = set(rulers.roll_ruler(random.Random(seed))["traits"])
            self.assertFalse({"gifted", "spell-fearing"} <= traits, seed)

    def test_the_crown_scope_entry_stays_off_a_lesser_sheet(self) -> None:
        self.assertIn("itinerant", rulers.pool(True))
        self.assertNotIn("itinerant", rulers.pool(False))
        for seed in range(400):
            sheet = rulers.roll_ruler(random.Random(seed), crown=False)
            self.assertEqual(len(sheet["traits"]), rulers.LESSER_DRAWS)
            self.assertNotIn("itinerant", sheet["traits"])

    def test_the_affliction_cap_holds(self) -> None:
        for seed in range(400):
            traits = rulers.roll_ruler(random.Random(seed),
                                       draws=6)["traits"]
            afflicted = [w for w in traits if w in rulers.AFFLICTIONS]
            self.assertLessEqual(len(afflicted), rulers.AFFLICTION_CAP,
                                 traits)

    def test_heart_reads_the_moral_tags_and_nothing_else(self) -> None:
        self.assertEqual(rulers.heart_of(["cruel", "arbitrary"]), "dark")
        self.assertEqual(rulers.heart_of(["merciful", "lawful"]), "good")
        self.assertEqual(rulers.heart_of(["cruel", "lawful"]), "mixed")
        self.assertEqual(rulers.heart_of(["brilliant", "sickly"]), "mixed")
        for seed in range(200):
            sheet = rulers.roll_ruler(random.Random(seed))
            self.assertIn(sheet["heart"], ("good", "dark", "mixed"))

    def test_the_companion_fields_exist_only_beside_their_trait(self
                                                               ) -> None:
        seen_puppet = seen_origin = False
        for seed in range(400):
            sheet = rulers.roll_ruler(random.Random(seed))
            if "puppet" in sheet["traits"]:
                seen_puppet = True
                self.assertIn(sheet["puppeteer"], rulers.PUPPETEERS)
            else:
                self.assertNotIn("puppeteer", sheet)
            for word in sheet.get("origins", {}):
                seen_origin = True
                self.assertIn(word, rulers.AFFLICTIONS)
                self.assertIn(word, sheet["traits"])
        self.assertTrue(seen_puppet)
        self.assertTrue(seen_origin)

    def test_the_circumstances_are_rolled_and_read_the_sheet(self) -> None:
        for seed in range(200):
            sheet = rulers.roll_ruler(random.Random(seed))
            self.assertIn(sheet["succession"], rulers.SUCCESSIONS)
            self.assertIn(sheet["accession"],
                          {m for m, _w, _l in rulers.ACCESSIONS})
        # A chaste crown has no heir coming: the succession table reads the
        # traits rather than rolling blind.
        chaste = [rulers.roll_succession(random.Random(s), ["chaste"],
                                         "inherited") for s in range(300)]
        plain = [rulers.roll_succession(random.Random(s), [], "inherited")
                 for s in range(300)]
        self.assertGreater(chaste.count("heirless"), plain.count("heirless"))

    def test_the_weights_reproduce_the_measured_marginals(self) -> None:
        """The identity the three-draw design rests on: three weighted
        draws off 357 put the dataset's per-trait shares back on roughly
        the measured proportion. Ambitious was 32/443 in the data and lands
        on about a quarter of rolled crowns."""
        rng = random.Random(11)
        rolls = [rulers.roll_ruler(rng)["traits"] for _ in range(4000)]
        share = sum("ambitious" in t for t in rolls) / len(rolls)
        self.assertAlmostEqual(share, 0.27, delta=0.05)

    def test_a_sheet_is_json_clean_and_seeded(self) -> None:
        sheet = rulers.roll_ruler(random.Random(4))
        self.assertEqual(json.loads(json.dumps(sheet)), sheet)
        self.assertEqual(rulers.roll_ruler(random.Random(4)), sheet)


class ThePoliticsFrame(unittest.TestCase):
    """Three rolls and one authored table: what a land IS before anything
    happens to it."""

    def test_every_land_rolls_a_constitution_from_its_own_slot(self
                                                              ) -> None:
        for seed in range(12):
            world = _world(seed)
            for polity in world["lands"]:
                key = worldsim.constitution_of(world, polity)
                self.assertIn(key, {c["key"]
                                    for c in worldsim.CONSTITUTIONS[polity]})

    def test_the_constitution_die_is_default_heavy(self) -> None:
        """The stereotype is the constant and the variants are the colour:
        the default carries most of the die in every land."""
        for polity, entries in worldsim.CONSTITUTIONS.items():
            total = sum(c["weight"] for c in entries)
            self.assertGreater(entries[0]["weight"] / total, 0.5, polity)
        rolled = [worldsim.roll_constitution(random.Random(s), "firascir")
                  for s in range(600)]
        self.assertGreater(rolled.count("feudal") / len(rolled), 0.5)
        self.assertTrue(set(rolled) - {"feudal"})       # ...and not only it

    def test_a_land_rolls_one_tension_and_a_crisis_land_two(self) -> None:
        standing = worldsim.STANDING_TENSIONS
        for band, want in (("normal", worldsim.TENSION_ROLLS),
                           ("crisis", worldsim.CRISIS_TENSION_ROLLS)):
            for polity in places.LAND_SPECS:
                held = worldsim.roll_tensions(random.Random(5), polity, band)
                own = standing.get(polity, ())
                self.assertEqual(len(held), want + len(own), (polity, band))
                self.assertEqual(len(set(held)), len(held))
                for key in own:
                    self.assertIn(key, held)

    def test_a_standing_tension_is_never_rolled_twice(self) -> None:
        for seed in range(40):
            held = worldsim.roll_tensions(random.Random(seed), "firascir",
                                          "crisis")
            self.assertEqual(held.count("manor-vs-village"), 1)

    def test_the_faction_cast_is_what_the_tensions_name(self) -> None:
        world = _world(7)
        for polity in world["lands"]:
            want = {name for key in worldsim.tensions_of(world, polity)
                    for name in worldsim.tension_spec(polity,
                                                      key)["factions"]}
            self.assertEqual(set(worldsim.factions_of(world, polity)), want)

    def test_an_edge_needs_both_its_ends_in_the_cast(self) -> None:
        world = _world(7)
        for polity in world["lands"]:
            cast = set(worldsim.factions_of(world, polity))
            live = worldsim.live_edges(world, polity)
            for entry in live:
                self.assertEqual(entry["land"], polity)
                self.assertIn(entry["from"], cast)
                self.assertIn(entry["to"], cast)
            dark = [e for e in worldsim.FACTION_EDGES
                    if e["land"] == polity and e not in live]
            for entry in dark:
                self.assertFalse({entry["from"], entry["to"]} <= cast)

    def test_the_ruler_sheet_lives_on_the_layer_and_wears_a_face(self
                                                                ) -> None:
        world = _world(21)
        for polity in world["lands"]:
            sheet = worldsim.ruler_sheet(world, polity)
            self.assertEqual(len(sheet["traits"]), rulers.CROWN_DRAWS)
            npc = next(n for n in world["npcs"]
                       if n.get("post") == "ruler" and n["land"] == polity)
            self.assertEqual(sheet["npc"], npc["id"])
            # ONE copy: the face carries no traits of its own.
            self.assertNotIn("traits", npc)
            self.assertNotIn("heart", npc)

    def test_the_politics_rolls_move_no_wealth_band(self) -> None:
        """They come after the wealth roll on the same stream, so every
        world's bands are what they were before politics existed."""
        for seed in range(30):
            world = _world(seed)
            for polity in world["lands"]:
                rng = random.Random(
                    worldsim._land_seed(world, polity, "worldsim-open", 0))
                self.assertEqual(worldsim.roll_wealth(rng),
                                 worldsim.wealth_of(world, polity))

    def test_the_politics_layer_rides_the_save(self) -> None:
        world = _world(13)
        worldsim.roll_world(world, 90)
        clone = json.loads(json.dumps(world))
        for polity in world["lands"]:
            self.assertEqual(clone["lands"][polity]["world"],
                             _layer(world, polity))


class ThePoliticsGate(unittest.TestCase):
    """The tension is the deck's gate; the other four slots are admits."""

    def test_a_card_whose_tension_is_not_held_never_enters_the_deck(self
                                                                   ) -> None:
        world = _world(4471)
        held = worldsim.tensions_of(world, "firascir")
        shut = [c for c in worldsim.CARDS
                if worldsim.in_land(c, "firascir")
                and c["admits"]["tension"]
                and not any(t in held for t in c["admits"]["tension"])]
        self.assertTrue(shut, "no politics card is shut out in this world")
        deck = set(_layer(world, "firascir")["deck"])
        for spec in shut:
            self.assertNotIn(spec["key"], deck)
            self.assertFalse(worldsim.admits(world, "firascir",
                                             spec["admits"]), spec["key"])

    def test_a_card_naming_no_tension_always_passes_the_gate(self) -> None:
        for spec in worldsim.CARDS:
            if spec["admits"]["tension"]:
                continue
            self.assertTrue(worldsim._tension_gate(spec, ()), spec["key"])

    def test_a_reshuffled_deck_is_still_gated(self) -> None:
        world = _world(4471)
        layer = _layer(world, "firascir")
        layer["deck"] = []
        worldsim._draw(world, "firascir", random.Random(2))
        held = worldsim.tensions_of(world, "firascir")
        for key in layer["deck"]:
            self.assertTrue(
                worldsim._tension_gate(worldsim.CARDS_BY_KEY[key], held), key)

    def test_a_card_admits_on_the_ruler_s_own_words(self) -> None:
        world = _world()
        spec = worldsim.CARDS_BY_KEY["firascir/royal-progress"]["admits"]
        sheet = worldsim.ruler_sheet(world, "firascir")
        sheet["traits"] = ["cruel", "brilliant", "devout"]
        self.assertFalse(worldsim.admits(world, "firascir", spec))
        sheet["traits"] = ["cruel", "itinerant", "devout"]
        self.assertTrue(worldsim.admits(world, "firascir", spec))

    def test_a_card_admits_on_the_succession(self) -> None:
        world = _world()
        spec = worldsim.CARDS_BY_KEY["crown/infant-heir"]["admits"]
        worldsim.set_succession(world, "firascir", "secure", 0)
        self.assertFalse(worldsim.admits(world, "firascir", spec))
        worldsim.set_succession(world, "firascir", "disputed", 0)
        self.assertTrue(worldsim.admits(world, "firascir", spec))

    def test_the_politics_admits_are_any_of(self) -> None:
        """Each reads a slot that holds one or two values, so a card names
        every value it will take and one of them is enough."""
        world = _world()
        spec = worldsim.CARDS_BY_KEY["crown/dead-king-returns"]["admits"]
        self.assertEqual(set(spec["succession"]), {"heirless", "disputed"})
        for state in ("heirless", "disputed"):
            worldsim.set_succession(world, "tergal", state, 0)
            self.assertTrue(worldsim.admits(world, "tergal", spec), state)
        worldsim.set_succession(world, "tergal", "secure", 0)
        self.assertFalse(worldsim.admits(world, "tergal", spec))


class ThePoliticsEffects(unittest.TestCase):
    """What a political card does that an economic one cannot."""

    def test_a_card_can_move_the_succession(self) -> None:
        world = _world()
        worldsim.set_succession(world, "tergal", "secure", 0)
        _layer(world, "tergal")["tensions"] = ["clan-vs-clan"]
        _fire(world, "tergal", "tergal/tanist-scramble", 12)
        self.assertEqual(worldsim.succession_of(world, "tergal"), "disputed")

    def test_a_card_that_names_somebody_keeps_him(self) -> None:
        world = _world()
        _layer(world, "firascir")["tensions"] = ["crown-vs-lords"]
        _fire(world, "firascir", "firascir/the-ban", 10)
        who = worldsim.named_authority(world, "firascir", "banned-lord")
        self.assertIsNotNone(who)
        self.assertEqual(len(who["traits"]), rulers.LESSER_DRAWS)
        self.assertNotIn("itinerant", who["traits"])
        self.assertIn(who["name"],
                      _layer(world, "firascir")["news"][-1]["line"])
        # ...and the same man is still there the next time it comes round.
        _fire(world, "firascir", "firascir/the-ban", 60)
        self.assertEqual(
            worldsim.named_authority(world, "firascir", "banned-lord"), who)

    def test_the_politics_cards_move_the_board_too(self) -> None:
        """The first invariant, applied to the new rung: a land's politics
        is not a readout -- it is how much work is posted and what it
        pays."""
        moved = [c for c in _politics_cards()
                 if (c["outlets"].get("quest") or {}).get("slots")
                 or (c["outlets"].get("quest") or {}).get("reprice")]
        self.assertGreater(len(moved), len(_politics_cards()) // 2)


def _politics_cards() -> list[dict]:
    return [worldsim.CARDS_BY_KEY[card["key"]]
            for card in worldsim.POLITICS_CARDS
            if card["key"] in worldsim.CARDS_BY_KEY]


class ThePoliticsContent(unittest.TestCase):
    """What the session was asked to author, asserted as data."""

    def test_every_politics_card_is_gated_on_something_political(self
                                                                ) -> None:
        """Nothing in this rung is ungated noise: each card either names a
        politics slot -- a tension, a constitution, a ruler trait, a
        succession state, a faction edge -- or admits on a STATE some other
        card left behind or some relation derives, which is the chain
        pattern the economy floor shipped."""
        settable = {s for c in worldsim.CARDS
                    for group in ("set", "while")
                    for s in (c["outlets"].get("state") or {}).get(group, ())}
        settable |= {e["then"] for e in worldsim.RELATIONS}
        for spec in _politics_cards():
            gated = any(spec["admits"].get(k) for k in POLITICS_KEYS)
            chained = set(spec["admits"]["states"])
            self.assertTrue(gated or chained, spec["key"])
            self.assertFalse(chained - settable, spec["key"])

    def test_every_land_has_politics_of_its_own(self) -> None:
        for polity in places.LAND_SPECS:
            own = [c for c in _politics_cards()
                   if worldsim.in_land(c, polity)]
            self.assertGreaterEqual(len(own), 3, polity)

    def test_the_baseline_land_takes_the_deepest_packet(self) -> None:
        """The asymmetry doctrine, as a number: Firascir carries more
        politics than any other land, because the ruler sheet's weights are
        already its."""
        depth = {p: len([c for c in _politics_cards()
                         if worldsim.in_land(c, p)])
                 for p in places.LAND_SPECS}
        self.assertEqual(max(depth, key=depth.get), "firascir")

    def test_each_land_s_troubles_come_from_its_own_axis(self) -> None:
        """The overlap guard: a card belongs to at most one land unless it
        is a crown-wide succession card, which every crowned land shares by
        construction."""
        for spec in _politics_cards():
            if spec["admits"]["succession"]:
                continue
            self.assertEqual(len(spec["land"]), 1, spec["key"])

    def test_every_instrument_is_an_edge_with_a_card_in_it(self) -> None:
        """The four diplomatic instruments: each is a state one land holds,
        an authored relation edge the other derives off it, and a card
        standing in that edge (worldsim.md's war feed)."""
        instruments = {"hostage", "tribute", "marriage", "union"}
        edges = {e["kind"]: e for e in worldsim.RELATIONS
                 if e["kind"] in instruments}
        self.assertEqual(set(edges), instruments)
        settable = {s for c in worldsim.CARDS
                    for group in ("set", "while")
                    for s in (c["outlets"].get("state") or {}).get(group, ())}
        for kind, entry in edges.items():
            self.assertTrue(set(entry["when"]) & settable, kind)
            readers = [c for c in worldsim.CARDS
                       if entry["then"] in c["admits"]["states"]]
            self.assertTrue(readers, kind)
            for spec in readers:
                self.assertIn(entry["to"], spec["land"], spec["key"])

    def test_no_politics_card_is_dead_data(self) -> None:
        """Every card in the rung is REACHABLE: force each gate it names
        and it admits. A card whose conditions can never all hold at once
        is the failure mode a five-slot admit invites, and it is silent --
        the deck simply skips it forever."""
        world = _world(4471)
        for spec in _politics_cards():
            polity = spec["land"][0]
            layer = _layer(world, polity)
            admits_ = spec["admits"]
            if admits_["edge"]:
                entry = next(e for e in worldsim.FACTION_EDGES
                             if e["key"] == admits_["edge"][0])
                layer["tensions"] = [
                    t["key"] for t in worldsim.TENSIONS[polity]
                    if {entry["from"], entry["to"]} <= set(t["factions"])
                    or entry["from"] in t["factions"]
                    or entry["to"] in t["factions"]]
            elif admits_["tension"]:
                layer["tensions"] = list(admits_["tension"][:1])
            if admits_["constitution"]:
                layer["constitution"] = admits_["constitution"][0]
            if admits_["traits"]:
                layer["ruler"]["traits"] = list(admits_["traits"])
            if admits_["succession"]:
                layer["ruler"]["succession"] = admits_["succession"][0]
            for state_id in admits_["states"]:
                # a DERIVED state is set on its source land, not this one
                edge = next((e for e in worldsim.RELATIONS
                             if e["to"] == polity
                             and e["then"] == state_id), None)
                if edge is None:
                    worldsim.set_state(world, polity, state_id, 1)
                else:
                    worldsim.set_state(world, edge["from"],
                                       edge["when"][0], 1)
            if worldsim.wealth_of(world, polity) not in admits_["wealth"]:
                worldsim.set_wealth(world, polity, admits_["wealth"][0], 1)
            self.assertTrue(worldsim.admits(world, polity, admits_),
                            spec["key"])
            for state_id in admits_["states"]:
                worldsim.drop_state(world, polity, state_id, 2)

    def test_the_authored_politics_fits_and_stays_ascii(self) -> None:
        labels = ([c["name"] for c in worldsim.CONSTITUTIONS["firascir"]]
                  + [t["line"] for ts in worldsim.TENSIONS.values()
                     for t in ts]
                  + [f["name"] for f in worldsim.FACTIONS.values()])
        for label in labels:
            self.assertLessEqual(len(label), WIDTH, label)
            self.assertTrue(label.isascii(), label)
        for polity, entries in worldsim.CONSTITUTIONS.items():
            for spec in entries:
                self.assertLessEqual(len(spec["name"]), WIDTH,
                                     (polity, spec["key"]))
                self.assertTrue(spec["line"].isascii(), spec["key"])
        for entry in worldsim.FACTION_EDGES:
            self.assertTrue(entry["line"].isascii(), entry["key"])


class TheWarFeed(unittest.TestCase):
    """The war had waves and no reason. Now it has one."""

    def test_the_casus_belli_is_rolled_off_a_derived_seed(self) -> None:
        world = _world(90)
        tale = story.init_story(world, random.Random(3))
        want = worldsim.roll_casus_belli(
            random.Random(f"casus:{world['seed']}:{tale['aggressor_land']}"),
            tale["aggressor"])
        self.assertEqual(tale["casus_belli"], want)

    def test_the_line_names_both_realms(self) -> None:
        longest = max((land["name"] for land in places.LAND_SPECS.values()),
                      key=len)
        for _key, line in (worldsim.CASUS_BELLI
                           + tuple(worldsim.STANDING_CASUS_BELLI.values())):
            text = worldsim.casus_belli_line({"line": line}, longest, longest)
            self.assertNotIn("{", text)
            self.assertTrue(text.isascii(), text)
            self.assertLessEqual(len(text), 72, text)

    def test_the_herald_says_it_once_and_leaves_it_on_the_news(self
                                                              ) -> None:
        world = _world(90)
        tale = story.init_story(world, random.Random(3))
        _, lines = story.post_wave(world, tale, random.Random(1), day=6)
        why = story.casus_belli_line(world, tale)
        self.assertTrue(why)
        self.assertTrue(any(why in line for line in lines))
        heard = "\n".join(worldsim.take_news(
            world, world["areas"][world["quests"]["w1"]["origin"]]["land"],
            6))
        self.assertIn(why, heard)
        # ...once: wave 2's herald does not repeat it.
        world["quests"]["w1"]["status"] = "done"
        tale["wave_done"] = 1
        _, again = story.post_wave(world, tale, random.Random(1), day=20)
        self.assertFalse(any(why in line for line in again))

    def test_every_rolled_war_carries_a_reason(self) -> None:
        """...and the reader is STRICT about it: a story without one is a
        bug, not a save to be humoured (develop.md's no-compat rule)."""
        for seed in range(12):
            world = _world(seed)
            tale = story.init_story(world, random.Random(seed))
            self.assertIn(tale["casus_belli"]["key"],
                          {k for k, _line in worldsim.CASUS_BELLI}
                          | {k for k, _line
                             in worldsim.STANDING_CASUS_BELLI.values()})
            self.assertTrue(story.casus_belli_line(world, tale))
        with self.assertRaises(KeyError):
            story.casus_belli_line(_world(1), {})


class ThePoliticsSurfaces(unittest.TestCase):
    """Where the player and the DM meet the polity."""

    def test_the_map_page_says_what_kind_of_place_it_is(self) -> None:
        world = _world(31)
        lines = worldsim.land_lines(world, "firascir")
        name = worldsim.constitution_spec(world, "firascir")["name"]
        self.assertIn(f"  {name}", lines)
        self.assertLessEqual(len(lines), 3)
        for line in lines:
            self.assertLessEqual(len(line), WIDTH, line)

    def test_the_dm_inventory_carries_the_whole_polity(self) -> None:
        world = _world(31)
        text = "\n".join(worldsim.world_lines(world))
        for polity in world["lands"]:
            self.assertIn(worldsim.constitution_spec(world,
                                                     polity)["name"], text)
            for key in worldsim.tensions_of(world, polity):
                self.assertIn(worldsim.tension_spec(polity, key)["line"],
                              text)
        self.assertIn("heart ", text)
        for line in worldsim.world_lines(world):
            self.assertTrue(line.isascii(), line)

    def test_the_town_says_the_ruler_s_reputation_and_not_his_heart(self
                                                                   ) -> None:
        world = _world(31)
        npc = next(n for n in world["npcs"]
                   if n.get("post") == "ruler" and n["land"] == "firascir")
        sheet = worldsim.ruler_sheet(world, "firascir")
        sheet["traits"] = ["cruel", "brilliant", "sickly"]
        sheet["heart"] = "dark"
        sheet["succession"] = "heirless"
        lines = worldsim.notable_lines(world, npc)
        text = "\n".join(lines)
        self.assertIn("cruel", text)
        self.assertNotIn("heart", text)
        self.assertNotIn("dark", text)
        self.assertIn("no heir", text)
        # Nobody else in the cast carries a sheet.
        sage = next(n for n in world["npcs"] if n.get("post") == "sage")
        self.assertEqual(worldsim.notable_lines(world, sage), [])

    def test_the_board_prints_the_reputation_under_the_face(self) -> None:
        import session
        world = _world(31)
        npc = next(n for n in world["npcs"]
                   if n.get("post") == "ruler" and n["land"] == "firascir")
        worldsim.ruler_sheet(world, "firascir")["traits"] = ["lecherous"]
        state = {"world": world, "clock": rpg.Clock(day=2),
                 "rng": random.Random(1), "party": _party(),
                 "position": session._area_position(
                     world["areas"][npc["seat"]]),
                 "visited": [], "purse": 10}
        args = argparse.Namespace(settlement=None, dm=False)
        out = io.StringIO()
        with unittest.mock.patch.object(session, "load", lambda: state), \
                unittest.mock.patch.object(session, "save", lambda s: None), \
                redirect_stdout(out):
            session.cmd_board(args)
        self.assertIn("lecherous", out.getvalue())


def _lore_cards() -> list[dict]:
    return [worldsim.CARDS_BY_KEY[card["key"]]
            for card in worldsim.RELIGION_CARDS + worldsim.MAGIC_CARDS
            if card["key"] in worldsim.CARDS_BY_KEY]


class TheLastTwoRecordKinds(unittest.TestCase):
    """FACT and OPTION: what the rung had to build before it could author."""

    def test_a_fact_costs_nothing_at_runtime(self) -> None:
        """The engine never reads one. The contract is mechanical: no fact
        key is a state, a card key, an option key or a tension -- there is
        nothing for anything but the DM's page to look it up by."""
        machinery = (set(worldsim.STATE_WORDS) | set(worldsim.CARDS_BY_KEY)
                     | set(worldsim.OPTIONS_BY_KEY)
                     | {t["key"] for ts in worldsim.TENSIONS.values()
                        for t in ts})
        for entry in worldsim.FACTS:
            self.assertNotIn(entry["key"], machinery, entry["key"])

    def test_every_land_carries_facts_of_its_own(self) -> None:
        for polity in places.LAND_SPECS:
            self.assertGreaterEqual(len(worldsim.facts_of(polity)), 5,
                                    polity)

    def test_an_option_only_does_what_the_engine_already_does(self) -> None:
        """The closed verb set. An option that needed new machinery would
        be a feature request wearing a content hat."""
        for spec in worldsim.OPTIONS:
            self.assertIn(spec["does"], worldsim.SERVICES, spec["key"])

    def test_the_word_the_player_types_is_unique(self) -> None:
        words = [worldsim.option_word(o) for o in worldsim.OPTIONS]
        self.assertEqual(len(words), len(set(words)))
        for word in words:
            self.assertIs(worldsim.option_named(word),
                          worldsim.OPTIONS_BY_KEY[
                              next(o["key"] for o in worldsim.OPTIONS
                                   if worldsim.option_word(o) == word)])

    def test_an_option_is_gated_and_reachable(self) -> None:
        """Every gated option's state is something a card in this game
        actually sets -- an option nobody can ever reach is dead data, and
        it is silent, which is exactly what import-time validation is
        for."""
        settable = {s for c in worldsim.CARDS for group in ("set", "while")
                    for s in (c["outlets"].get("state") or {}).get(group, ())}
        gated = 0
        for spec in worldsim.OPTIONS:
            for state_id in spec["states"]:
                self.assertIn(state_id, settable, spec["key"])
                gated += 1
        self.assertGreaterEqual(gated, 1)

    def test_the_authored_lore_fits_and_stays_ascii(self) -> None:
        for entry in worldsim.FACTS:
            self.assertLessEqual(len(entry["title"]), WIDTH, entry["key"])
            self.assertTrue(entry["title"].isascii(), entry["key"])
            self.assertTrue(entry["line"].isascii(), entry["key"])
        for spec in worldsim.OPTIONS:
            self.assertLessEqual(len(spec["name"]), WIDTH, spec["key"])
            self.assertTrue(spec["line"].isascii(), spec["key"])


class TheServicesCounter(unittest.TestCase):
    """The sixth outlet's standing half, at the counter."""

    @staticmethod
    def _state(world: dict, polity: str, day: int = 5) -> dict:
        here = quests.settlements_by_land(world)[polity][0]
        return {"world": world, "clock": rpg.Clock(day=day),
                "rng": random.Random(9), "party": _party(),
                "purse": rpg.Purse(gold=900), "services": {},
                "accepted": [], "active_quest": None, "visited": [],
                "position": session._area_position(here)}

    def _run(self, state: dict, *words: str) -> str:
        import session
        out = io.StringIO()
        args = argparse.Namespace(what=list(words))
        with unittest.mock.patch.object(session, "load", lambda: state), \
                unittest.mock.patch.object(session, "save", lambda s: None), \
                redirect_stdout(out):
            session.cmd_service(args)
        return out.getvalue()

    def test_the_counter_lists_what_this_land_sells(self) -> None:
        world = _world()
        text = self._run(self._state(world, "firascir"))
        self.assertIn("burial", text)
        self.assertNotIn("rain stone", text)      # that is Tergal's counter

    def test_a_blessing_is_paid_for_and_lands_on_the_party(self) -> None:
        world = _world()
        state = self._state(world, "firascir")
        for h in state["party"][1:]:     # a recruited companion tracks
            h.satisfaction = 5           # satisfaction; the fixture's do
            h.protagonist = False        # not until they are told to
        tracked = [h for h in state["party"][1:]
                   if rpg.satisfaction_tracked(h)]
        self.assertTrue(tracked, "the fixture party tracks satisfaction")
        before = [h.satisfaction for h in tracked]
        gold = state["purse"].gold
        self._run(state, "blessing")
        self.assertLess(state["purse"].gold, gold)
        self.assertTrue(all(h.satisfaction > b
                            for h, b in zip(tracked, before)))

    def test_a_blessing_has_a_cooldown_and_the_purse_is_not_charged(self
                                                                   ) -> None:
        world = _world()
        state = self._state(world, "firascir")
        self._run(state, "blessing")
        gold = state["purse"].gold
        text = self._run(state, "blessing")
        self.assertEqual(state["purse"].gold, gold)
        self.assertIn("twice", text)

    def test_a_shut_option_is_refused_and_never_charged(self) -> None:
        world = _world()
        state = self._state(world, "firascir")
        gold = state["purse"].gold
        text = self._run(state, "tower-fee")   # wants tower-open
        self.assertEqual(state["purse"].gold, gold)
        self.assertIn("not on offer", text)
        worldsim.set_state(world, "firascir", "tower-open", 4)
        self.assertIn("tower", self._run(state))

    def test_another_land_s_counter_is_not_this_one(self) -> None:
        world = _world()
        state = self._state(world, "firascir")
        self.assertIn("not sold", self._run(state, "rain-stone"))

    def test_the_rain_stone_buys_the_sky_and_gives_it_back(self) -> None:
        """The weather-worker's priced thumb on the day roll: a day or two
        of rain, never a season -- the price rule says healing is retail
        and so is weather."""
        world = _world()
        state = self._state(world, "tergal", day=5)
        self._run(state, "rain-stone")
        spec = worldsim.OPTIONS_BY_KEY["tergal/rain-stone"]
        # The purchase day's sky is already rolled, so the paid window is
        # the NEXT `holds` days -- every one of them, or the player paid
        # for a day the stone never delivered (the 2026-08-12 repair).
        for day in range(6, 6 + spec["holds"]):
            worldsim.roll_world(world, day)
            self.assertEqual(worldsim.weather_of(world, "tergal"), "rain",
                             f"day {day} was paid for")
        self.assertIn("rain-bought", worldsim.state_ids(world, "tergal"))
        worldsim.roll_world(world, 6 + spec["holds"])
        self.assertNotIn("rain-bought", worldsim.state_ids(world, "tergal"))
        self.assertIsNone(_layer(world, "tergal")["bought_sky"])

    def test_a_bought_sky_still_runs_the_spells(self) -> None:
        world = _world()
        worldsim.roll_world(world, 4)
        worldsim.hire_weather(world, "tergal", 4, "rain", 3)
        worldsim.roll_world(world, 6)
        self.assertGreaterEqual(_layer(world, "tergal")["wet"], 2)
        self.assertEqual(_layer(world, "tergal")["dry"], 0)

    def test_the_price_sheet_carries_the_counter(self) -> None:
        import session
        world = _world()
        state = self._state(world, "tergal")
        out = io.StringIO()
        with unittest.mock.patch.object(session, "load", lambda: state), \
                redirect_stdout(out):
            session.cmd_prices(argparse.Namespace())
        self.assertIn("rain stone", out.getvalue())

class TheCrimeMarkWiring(unittest.TestCase):
    """The reagent trade, wired where worldsim.md put it."""

    def test_a_quiet_land_puts_nothing_in_the_mark_table(self) -> None:
        world = _flat_world()
        for polity in world["lands"]:
            for cat in crime.CATEGORIES:
                self.assertEqual(
                    worldsim.mark_roles(world, polity, cat["key"]), (),
                    (polity, cat["key"]))

    def test_every_state_mark_names_a_real_category(self) -> None:
        for state_id, table in worldsim.STATE_MARKS.items():
            self.assertIn(state_id, worldsim.STATE_WORDS)
            for key in table:
                self.assertIn(key, crime.BY_KEY, (state_id, key))

    def test_the_extra_faces_are_dealt_in_beside_the_band_s_own(self
                                                               ) -> None:
        """A state that makes a new kind of mark exist does not replace the
        ordinary ones -- it competes with them, and the casing prints
        whichever came up like any other face."""
        cat = crime.BY_KEY["heist"]
        extra = ("the reagent vault under the academy",)
        seen = set()
        for day in range(1, 60):
            mark = crime.roll_mark(cat, 11, "area/x/y", "capital", day,
                                   extra)
            seen.add(mark["role"])
        self.assertIn(extra[0], seen)
        self.assertTrue(seen - set(extra))

class TheReligionAndMagicContent(unittest.TestCase):
    """What the session was asked to author, asserted as data."""

    def test_the_magic_packets_reach_every_land_too(self) -> None:
        for polity in places.LAND_SPECS:
            own = [c for c in worldsim.MAGIC_CARDS
                   if worldsim.in_land(c, polity)]
            self.assertGreaterEqual(len(own), 3, polity)

    def test_almost_nothing_in_the_rung_is_ungated(self) -> None:
        """The gate is what keeps a packet a wide POOL instead of a content
        budget. What is left ungated is at most two cards in a surviving
        land, and each pays for the privilege with its own low `chance`."""
        loose = [c for c in _lore_cards()
                 if not any(c["admits"].get(k) for k in POLITICS_KEYS)
                 and not c["admits"]["states"]
                 and not c["admits"]["weather"]]
        for spec in loose:
            self.assertLess(spec["chance"], 1.0, spec["key"])
        by_land: dict[str, int] = {}
        for spec in loose:
            if len(spec["land"]) > 1:   # a land-agnostic card is the
                continue                # packet's own, not this land's
            by_land[spec["land"][0]] = by_land.get(spec["land"][0], 0) + 1
        for polity, count in by_land.items():
            self.assertLessEqual(count, 2, polity)

    def test_the_margin_doctrine_holds_in_the_data(self) -> None:
        """Magic is real, known and SMALL: no throne, market or war is
        decided by it. Mechanically -- not one magic card moves a wealth
        band, and every one of them is rare or hard-gated."""
        for spec in worldsim.MAGIC_CARDS:
            state = spec["outlets"].get("state") or {}
            self.assertFalse(state.get("wealth"), spec["key"])
            self.assertFalse(state.get("wealth_while"), spec["key"])
            self.assertFalse(state.get("constitution"), spec["key"])

    def test_conduct_not_creed(self) -> None:
        """The design requirement: no inquisition against casting as such.
        The hunt exists, and it admits only on what somebody DID -- the
        talent that went off -- never on a land, a ruler or a faith."""
        hunt = worldsim.CARDS_BY_KEY["magic/the-hunt"]
        self.assertEqual(hunt["admits"]["states"], ("talent-loose",))
        self.assertFalse(hunt["admits"]["constitution"])
        self.assertFalse(hunt["admits"]["traits"])
        self.assertEqual(hunt["land"], (worldsim.ANY_LAND,))

    def test_the_wild_talent_and_the_seeress_are_kept(self) -> None:
        """RECURRENCE is the property that makes an NPC exist at all: the
        card names somebody once and the land keeps him."""
        world = _flat_world()
        _fire(world, "firascir", "magic/wild-talent", 3)
        who = worldsim.named_authority(world, "firascir", "wild-talent")
        self.assertIsNotNone(who)
        _fire(world, "firascir", "magic/wild-talent", 40, seed=7)
        self.assertEqual(
            worldsim.named_authority(world, "firascir",
                                     "wild-talent")["name"], who["name"])

    def test_the_schism_clock_runs_both_ways(self) -> None:
        """One church, two rites, and cards on the edge fire in BOTH
        lands (worldsim.md's Sun communion)."""
        world = _flat_world()
        synod = worldsim.CARDS_BY_KEY["communion/the-synod"]
        self.assertEqual(set(synod["land"]), {"firascir", "mortellaria"})
        worldsim.set_state(world, "mortellaria", "dead-abroad", 3)
        self.assertIn("schism-near", worldsim.state_ids(world, "firascir"))
        self.assertTrue(worldsim.admits(world, "firascir", synod["admits"]))
        worldsim.drop_state(world, "mortellaria", "dead-abroad", 4)
        worldsim.set_state(world, "firascir", "interdict", 5)
        self.assertIn("schism-near",
                      worldsim.state_ids(world, "mortellaria"))
        self.assertTrue(worldsim.admits(world, "mortellaria",
                                        synod["admits"]))

    def test_the_temple_sells_a_burial_and_a_blessing_and_no_penance(self
                                                                    ) -> None:
        """plan.md's ruling, as data: healing, burial and blessing as plain
        priced entries, and the sin/penance wiring deliberately absent.
        HEALING is the `healer` term itself -- the temple IS the healer in
        the Sun lands, which is why the interdict puts the fee up and the
        unlicensed well puts it down."""
        temple = [o for o in worldsim.OPTIONS
                  if o["key"].startswith("sun/")]
        self.assertEqual({worldsim.option_word(o) for o in temple},
                         {"burial", "blessing"})
        for spec in temple:
            self.assertEqual(set(spec["land"]), {"firascir", "mortellaria"})
            self.assertEqual(spec["term"], "healer")
        self.assertGreater(worldsim.STATE_MENU["interdict"]["healer"], 1.0)
        self.assertLess(worldsim.STATE_MENU["holy-well"]["healer"], 1.0)
        for spec in worldsim.OPTIONS:
            self.assertNotIn("sin", spec["line"].lower().split())
            self.assertNotIn("penance", spec["line"].lower())

    def test_the_pact_stays_out_of_the_lore(self) -> None:
        """The design round's first directive: nobody in the world knows of
        the player's hell pact, nothing senses it, and no entry in these
        packets reacts to it."""
        text = " ".join(
            [e["line"] for e in worldsim.FACTS]
            + [o["line"] for o in worldsim.OPTIONS]
            + [c["outlets"].get("news", "") for c in _lore_cards()]).lower()
        for word in ("the pact", "hell", "infernal", "damned"):
            self.assertNotIn(word, text)

    def test_no_card_in_the_rung_is_dead_data(self) -> None:
        """Force each gate a card names and it admits. A card whose
        conditions can never all hold at once is silent -- the deck simply
        skips it forever."""
        world = _world(4471)
        for spec in _lore_cards():
            polity = spec["land"][0]
            if polity == worldsim.ANY_LAND:
                polity = "firascir"
            layer = _layer(world, polity)
            admits_ = spec["admits"]
            if admits_["edge"]:
                entry = next(e for e in worldsim.FACTION_EDGES
                             if e["key"] == admits_["edge"][0])
                layer["tensions"] = [
                    t["key"] for t in worldsim.TENSIONS[polity]
                    if entry["from"] in t["factions"]
                    or entry["to"] in t["factions"]]
            elif admits_["tension"]:
                layer["tensions"] = list(admits_["tension"][:1])
            if admits_["traits"]:
                layer["ruler"]["traits"] = list(admits_["traits"])
            for state_id in admits_["states"]:
                edge = next((e for e in worldsim.RELATIONS
                             if e["to"] == polity
                             and e["then"] == state_id), None)
                if edge is None:
                    worldsim.set_state(world, polity, state_id, 1)
                else:
                    worldsim.set_state(world, edge["from"],
                                       edge["when"][0], 1)
            for state_id in admits_["without"]:
                worldsim.drop_state(world, polity, state_id, 1)
            if worldsim.wealth_of(world, polity) not in admits_["wealth"]:
                worldsim.set_wealth(world, polity, admits_["wealth"][0], 1)
            self.assertTrue(worldsim.admits(world, polity, admits_),
                            spec["key"])
            for state_id in admits_["states"]:
                worldsim.drop_state(world, polity, state_id, 2)

    def test_the_authored_rung_fits_and_stays_ascii(self) -> None:
        for spec in _lore_cards():
            self.assertTrue(spec["name"].isascii(), spec["key"])
            self.assertLessEqual(len(spec["name"]), WIDTH, spec["key"])
            for line in spec["outlets"].values():
                if isinstance(line, str):
                    self.assertTrue(line.isascii(), spec["key"])


if __name__ == "__main__":
    unittest.main()
