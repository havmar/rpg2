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
import unittest
import unittest.mock
from contextlib import redirect_stdout

import argparse

import conquest
import places
import quests
import rpg
import rulers
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
        self.assertEqual(len(area["quests"]),
                         quests.board_slots(world, area))
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
                              "live", "news", "told_day", "rolled_day",
                              "weather_deck", "season_deck", "weather_live",
                              "season_live", "weather", "weather_day",
                              "wet", "dry",
                              # the politics rung (2026-08-10)
                              "constitution", "tensions", "ruler",
                              "authorities"})

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
        self.assertEqual(drawn["land"], (polity,))


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
        derived = next(s for s in worldsim.derived_states(world, "mortellaria")
                       if s["id"] == "arms-scarce")
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
    """The sky: one word a land a day, off the environment's own climate."""

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

    def test_the_profile_is_the_distribution(self) -> None:
        """Every environment authors its own climate, and the roll obeys it:
        the damp forest rains more than the dry south, and only the cold
        highlands ever see snow."""
        seen = {polity: [] for polity in _world()["lands"]}
        for seed in range(6):
            world = _world(seed)
            for day in range(1, 121):
                worldsim.roll_world(world, day)
                for polity in world["lands"]:
                    seen[polity].append(_layer(world, polity)["weather"])
        wet = {p: sum(w in ("rain", "storm") for w in words) / len(words)
               for p, words in seen.items()}
        self.assertGreater(wet["ensimaa"], wet["mortellaria"])
        self.assertGreater(wet["firascir"], wet["mortellaria"])
        self.assertNotIn("snow", seen["ensimaa"])
        self.assertIn("snow", seen["dvarvengrond"])
        self.assertNotIn("heat", seen["dvarvengrond"])

    def test_the_same_word_reads_differently_on_different_ground(self
                                                                 ) -> None:
        # The dwarves' storm IS the snowstorm -- one card underneath, one
        # phrase on top (worldsim.md's own note).
        self.assertEqual(worldsim.weather_phrase("alpine_tundra", "storm"),
                         "a snowstorm")
        self.assertEqual(worldsim.weather_phrase("temperate", "storm"),
                         "a storm")

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
        base = worldsim.weather_weights(world, "firascir")
        worldsim.set_state(world, "firascir", "drought", day=1)
        dry = worldsim.weather_weights(world, "firascir")
        self.assertLess(dry["rain"], base["rain"])
        self.assertGreater(dry["clear"], base["clear"])

    def test_a_card_that_is_the_weather_holds_the_sky(self) -> None:
        """A storm declared to last three days is a storm on all three: the
        alternative is a state readout saying "the storm has the roads"
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

    def test_the_rare_card_stays_in_the_deck_when_it_loses_its_roll(self
                                                                   ) -> None:
        world = _world()
        worldsim.roll_world(world, 1)
        _sky(world, "ensimaa", "fog")
        _layer(world, "ensimaa")["weather_deck"] = ["weather/fog-bones"]
        misses = 0
        for seed in range(40):
            drawn = worldsim._draw(world, "ensimaa", random.Random(seed),
                                   "fog", "weather")
            if drawn is None:
                misses += 1
            else:                       # put it back for the next try
                _layer(world, "ensimaa")["weather_deck"] = \
                    ["weather/fog-bones"]
        self.assertGreater(misses, 25)      # chance 0.05: rare, not never
        self.assertIn("weather/fog-bones",
                      _layer(world, "ensimaa")["weather_deck"])


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

    def test_the_drought_is_season_scale_and_wants_a_dry_spell(self) -> None:
        card = worldsim.CARDS_BY_KEY["weather/drought"]
        self.assertEqual(card["track"], "season")
        self.assertGreaterEqual(card["days"][0], 45)
        # ...and the spell is the LAND's own: a drought is relative, so the
        # threshold comes off the environment profile rather than a single
        # number that the wet lands could never reach.
        self.assertEqual(card["admits"]["dry"], worldsim.PROFILE_SPELL)
        world = _world()
        worldsim.roll_world(world, 1)
        for polity, need in (("mortellaria", 25), ("ensimaa", 12)):
            layer = _layer(world, polity)
            layer["dry"] = need - 1
            self.assertFalse(worldsim.admits(world, polity, card["admits"]),
                             polity)
            layer["dry"] = need
            self.assertTrue(worldsim.admits(world, polity, card["admits"]),
                            polity)
        self.assertLess(
            places.ENVIRONMENT_PROFILES["temperate_forest"]["drought_days"],
            places.ENVIRONMENT_PROFILES["mediterranean"]["drought_days"])

    def test_the_fire_wants_the_drought_and_the_green_wants_the_burn(self
                                                                    ) -> None:
        world = _world()
        worldsim.roll_world(world, 1)
        _sky(world, "ensimaa", "heat")
        fire = worldsim.CARDS_BY_KEY["weather/wildfire"]
        self.assertFalse(worldsim.admits(world, "ensimaa", fire["admits"],
                                         "heat"))
        worldsim.set_state(world, "ensimaa", "drought", day=1)
        self.assertTrue(worldsim.admits(world, "ensimaa", fire["admits"],
                                        "heat"))
        _fire(world, "ensimaa", "weather/wildfire", 2)
        held = set(worldsim.state_ids(world, "ensimaa"))
        self.assertIn("wildfire", held)
        self.assertIn("burned-over", held)
        # The scar OUTLIVES the fire, and one card is the way back
        worldsim._end(world, "ensimaa", 12, "weather")
        held = set(worldsim.state_ids(world, "ensimaa"))
        self.assertNotIn("wildfire", held)
        self.assertIn("burned-over", held)
        worldsim.drop_state(world, "ensimaa", "drought", 12)
        _fire(world, "ensimaa", "weather/green-again", 90)
        self.assertNotIn("burned-over",
                         set(worldsim.state_ids(world, "ensimaa")))

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

    def test_the_smog_is_gibili_s_and_the_owners_blame_the_weather(self
                                                                   ) -> None:
        card = worldsim.CARDS_BY_KEY["weather/smog"]
        self.assertEqual(card["land"], ("gibili",))
        self.assertIn("weather", card["outlets"]["news"])


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
                "position": {"land": "firascir",
                             "area": quests.settlements_by_land(
                                 world)["firascir"][0]["key"]}}

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
        town = quests.settlements_by_land(world)["firascir"][0]
        base = quests.SETTLEMENT_KINDS[town["subtype"]][0]
        for band, want in worldsim.BAND_SLOTS.items():
            _quiet(world, "firascir", band)
            self.assertEqual(quests.board_slots(world, town), base + want,
                             band)

    def test_a_settlement_is_never_a_place_with_no_work(self) -> None:
        world = _world()
        _all_quiet(world)
        village = next(s for s in quests.settlements_by_land(world)["gibili"]
                       if s["subtype"] == "village")
        _quiet(world, "gibili", "crisis")
        _fire(world, "gibili", "gibili/timber-short", 4)    # slots -2 on top
        self.assertLess(worldsim.board_shift(world, "gibili"), 0)
        self.assertGreaterEqual(quests.board_slots(world, village),
                                worldsim.BOARD_SLOTS_FLOOR)

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

    def test_a_card_job_pays_its_premium_over_the_going_rate(self) -> None:
        world = _world()
        _all_quiet(world)
        _fire(world, "dvarvengrond", "dvarvengrond/food-caravan", 4)
        town = quests.settlements_by_land(world)["dvarvengrond"][0]
        posted = quests.refresh_settlement_board(world, town, 4,
                                                 random.Random(6))
        job = next(q for q in posted
                   if q.get("world_card") == "dvarvengrond/food-caravan")
        plain = rpg.quest_gold(job["level"], job["encounters"])
        pay = worldsim.CARDS_BY_KEY[
            "dvarvengrond/food-caravan"]["outlets"]["quest"]["pay"]
        self.assertEqual(job["gold_total"], max(1, round(plain * pay)))
        self.assertGreater(job["gold_total"], plain)

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

    def test_the_band_is_on_the_shelf(self) -> None:
        world = _world()
        _quiet(world, "gibili", "prosperous")
        rich = worldsim.menu_terms(world, "gibili")
        _quiet(world, "gibili", "crisis")
        poor = worldsim.menu_terms(world, "gibili")
        self.assertLess(rich["goods"], poor["goods"])
        self.assertGreater(rich["lodging"], poor["lodging"])

    def test_a_card_prices_what_it_is_about(self) -> None:
        world = _world()
        _all_quiet(world)
        _fire(world, "firascir", "firascir/tolls", 3)
        self.assertEqual(worldsim.term(world, "firascir", "toll"), 2.0)
        _all_quiet(world)
        _fire(world, "gibili", "gibili/gadget-fair", 3)
        self.assertLess(worldsim.term(world, "gibili", "steel"), 1.0)

    def test_a_relation_reaches_a_price_three_lands_away(self) -> None:
        """The whole reason the menu reads STATES and not just cards: the
        elves throw the loggers out, and a dwarven smith puts his prices
        up because the mountain's own timber road runs through it."""
        world = _world()
        _all_quiet(world)
        base = worldsim.term(world, "dvarvengrond", "steel")
        worldsim.set_state(world, "ensimaa", "foreigners-unwelcome", 5)
        self.assertIn("claims-revoked",
                      worldsim.state_ids(world, "dvarvengrond"))
        self.assertGreater(worldsim.term(world, "dvarvengrond", "steel"),
                           base)

    def test_the_terms_are_clamped_at_both_ends(self) -> None:
        world = _world()
        _quiet(world, "dvarvengrond", "crisis")
        for state_id in ("strike", "deposit-dead", "grain-scarce"):
            worldsim.set_state(world, "dvarvengrond", state_id, 5)
        for mult in worldsim.menu_terms(world, "dvarvengrond").values():
            self.assertGreaterEqual(mult, worldsim.MENU_FLOOR)
            self.assertLessEqual(mult, worldsim.MENU_CEILING)

    def test_a_price_never_goes_to_nothing(self) -> None:
        world = _world()
        _all_quiet(world)
        _fire(world, "gibili", "gibili/gadget-fair", 3)
        self.assertGreaterEqual(worldsim.priced(world, "gibili", "goods", 1),
                                1)

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
        ("ensimaa", "ensimaa/rented-land", "foreigners-unwelcome",
         "ensimaa/eviction"),
        ("dvarvengrond", "dvarvengrond/new-seam", "deposit-found",
         "dvarvengrond/gold-rush"),
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

    def test_one_chain_crosses_a_relation(self) -> None:
        """The Gibili mills run cold because the ELVES threw the loggers
        out: the link is a derived state, and the card reads it like any
        other."""
        world = _world()
        _all_quiet(world)
        spec = worldsim.CARDS_BY_KEY["gibili/timber-short"]["admits"]
        self.assertFalse(worldsim.admits(world, "gibili", spec))
        _fire(world, "ensimaa", "ensimaa/rented-land", 3)
        self.assertIn("concession-lost", worldsim.state_ids(world, "gibili"))
        self.assertTrue(worldsim.admits(world, "gibili", spec))


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

    def test_the_relations_table_grew_past_the_frame(self) -> None:
        self.assertGreater(len(worldsim.RELATIONS), 9)
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

    def test_the_posted_jobs_honor_the_cultural_arms_rule(self) -> None:
        """Elves shoot bows, goblins sling, dwarves shoot powder
        (rules.md's Ranged Combat). The rule is about WHOSE the roster is,
        not whose ground it stands on -- the goblin loggers holding a camp
        in the elven forest still sling -- so the contract is that the
        authored pools are culturally clean and every card draws from one
        of them, never from an ad-hoc mix."""
        pools = {"_TOUGHS": worldsim._TOUGHS,
                 "_ELF_TOUGHS": worldsim._ELF_TOUGHS,
                 "_GOBLIN_TOUGHS": worldsim._GOBLIN_TOUGHS,
                 "_DWARF_TOUGHS": worldsim._DWARF_TOUGHS,
                 "_BEASTS": worldsim._BEASTS}
        for row in ("slinger", "gunner"):
            self.assertNotIn(row, pools["_ELF_TOUGHS"])
        for row in ("archer", "hunter", "gunner"):
            self.assertNotIn(row, pools["_GOBLIN_TOUGHS"])
        for row in ("archer", "hunter", "slinger"):
            self.assertNotIn(row, pools["_DWARF_TOUGHS"])
        known = {tuple(p) for p in pools.values()}
        for spec in worldsim.CARDS:
            posted = (spec["outlets"].get("quest") or {}).get("post")
            if posted:
                self.assertIn(tuple(posted["pool"]), known, spec["key"])

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
                "position": {"land": polity,
                             "area": quests.settlements_by_land(
                                 world)[polity][0]["key"]}}

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

    def test_a_card_admits_on_the_constitution(self) -> None:
        world = _world()
        spec = worldsim.CARDS_BY_KEY["ensimaa/hunters-sent"]["admits"]
        _layer(world, "ensimaa")["constitution"] = "constitutional"
        self.assertFalse(worldsim.admits(world, "ensimaa", spec))
        _layer(world, "ensimaa")["constitution"] = "sealed"
        self.assertTrue(worldsim.admits(world, "ensimaa", spec))

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

    def test_a_card_admits_on_a_live_faction_edge(self) -> None:
        world = _world()
        spec = worldsim.CARDS_BY_KEY["gibili/provocateur"]["admits"]
        layer = _layer(world, "gibili")
        layer["tensions"] = ["parliament-deadlock"]
        self.assertFalse(worldsim.admits(world, "gibili", spec))
        layer["tensions"] = ["parliament-deadlock", "syndicate-vs-syndicate"]
        self.assertTrue(worldsim.admits(world, "gibili", spec))

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

    def test_the_constitution_slot_moves_only_where_a_card_says_so(self
                                                                  ) -> None:
        flips = {c["key"]: (c["outlets"]["state"]["constitution"],
                            c["land"])
                 for c in worldsim.CARDS
                 if (c["outlets"].get("state") or {}).get("constitution")}
        self.assertTrue(flips)
        for key, (value, lands) in flips.items():
            self.assertEqual(len(lands), 1, key)
            self.assertIn(value, {c["key"]
                                  for c in worldsim.CONSTITUTIONS[lands[0]]})
        world = _world()
        _layer(world, "gibili")["tensions"] = ["army-vs-ranks"]
        _layer(world, "gibili")["constitution"] = "paper-state"
        _fire(world, "gibili", "gibili/junta", 20)
        self.assertEqual(worldsim.constitution_of(world, "gibili"), "junta")
        self.assertEqual(_layer(world, "gibili")["constitution_day"], 20)

    def test_a_constitution_a_land_already_holds_says_nothing_new(self
                                                                 ) -> None:
        world = _world()
        _layer(world, "gibili")["constitution"] = "junta"
        self.assertTrue(worldsim._says_nothing_new(
            world, "gibili", worldsim.CARDS_BY_KEY["gibili/junta"]))

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
    return list(worldsim.POLITICS_CARDS)


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

    def test_the_succession_cluster_skips_the_land_with_no_crown(self
                                                                ) -> None:
        cluster = [c for c in _politics_cards() if c["admits"]["succession"]]
        self.assertGreaterEqual(len(cluster), 4)
        for spec in cluster:
            self.assertNotIn("gibili", spec["land"], spec["key"])

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

    def test_the_exile_edge_fires_in_other_lands(self) -> None:
        """A card about LEAVING a country can only reach the party
        somewhere else, which is what the edge is for."""
        world = _world()
        worldsim.set_state(world, "ensimaa", "hunters-out", 4)
        reached = [p for p in world["lands"]
                   if "elf-hunters" in worldsim.state_ids(world, p)]
        self.assertGreaterEqual(len(reached), 3)
        self.assertNotIn("ensimaa", reached)
        self.assertIn("elf-hunters", worldsim.STATE_ENCOUNTERS)

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

    def test_one_race_needs_no_roll(self) -> None:
        for seed in range(40):
            entry = worldsim.roll_casus_belli(random.Random(seed), "orc")
            self.assertEqual(entry["key"], "mandate")
        rolled = {worldsim.roll_casus_belli(random.Random(s), "human")["key"]
                  for s in range(60)}
        self.assertGreater(len(rolled), 3)
        self.assertNotIn("mandate", rolled)

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
                 "position": {"land": "firascir",
                              "area": npc["seat"], "site": None},
                 "visited": [], "purse": 10}
        args = argparse.Namespace(settlement=None, dm=False)
        out = io.StringIO()
        with unittest.mock.patch.object(session, "load", lambda: state), \
                unittest.mock.patch.object(session, "save", lambda s: None), \
                redirect_stdout(out):
            session.cmd_board(args)
        self.assertIn("lecherous", out.getvalue())


if __name__ == "__main__":
    unittest.main()
