"""LOCAL QUEST GEOGRAPHY contract suite (2026-08-15).

The session that made work a LOCAL fact. What is pinned here, in build
order:

  A. **Sparse ordinary boards** -- the stable capital/town/village activity
     roll and its measured rates, the starting settlement's override, the
     flag surviving materialization and the save, and what an inactive
     board actually does: no ordinary capacity, no ordinary refill, nothing
     posted at worldgen.
  B. **The forced families** -- a world card's job, a courier run, a story
     wave, hell's assignment and the DM's forged work all reach an inactive
     settlement, none of them consumes ordinary capacity, and none of them
     turns the board active.
  C. **The three-day rumor radius** -- who is in earshot (known,
     materialized, within QUEST_RUMOR_DAYS of the party's Tile), the
     grouped readout, and the refresh scope: a board four days off is
     neither shown nor moved, and `board all` observes without widening it.
  D. **The ordinary target radius** -- every generated target within three
     path days across a seed sweep, tag compatibility never traded for the
     radius, the origin Tile's countryside as the declared fallback, the
     stable candidate order, and `radius=None` reaching past all of it.
  E. **The path-priced clock** -- the ordered route out and home, over
     local, multi-Tile, mountain, sea and multi-Site work, plus the
     deliveries' cross-country pay and window.
  F. **The opening** -- always posted, always at an active board, always
     geographically legal.

    python -m unittest -v test_quest_geography.py
"""

from __future__ import annotations

import io
import json
import random
import unittest
from contextlib import redirect_stdout
from unittest import mock

import argparse
import karma
import places
import quests
import rpg
import session
import story
import worldsim


# --------------------------------------------------------------------------- #
# Harness
# --------------------------------------------------------------------------- #

def _world(seed: int = 27) -> dict:
    return quests.generate_world(seed=seed)


def _hero(name: str = "PC", level: int = 3) -> rpg.Entity:
    return rpg.Entity(name=name, dex=5, str_=5, sta=6, mind=5, max_hp=12,
                      power=4, pain=rpg.HERO_PAIN, records_wounds=True,
                      weapon=rpg.WEAPONS["katana"], level=level)


def _state(world: dict, at: dict, *, day: int = 5) -> dict:
    party = [_hero("PC"), _hero("Ally")]
    party[0].protagonist = True
    return {
        "world": world, "party": party, "clock": rpg.Clock(day=day),
        "purse": rpg.Purse(gold=0), "rng": random.Random(4),
        "karma": karma.new_karma(), "history": [],
        "position": session._area_position(at),
        "accepted": [], "active_quest": None, "loose_ends": [],
        "foe_count": 0, "pending": None, "rooms": {}, "site_clears": {},
        "holdings": {}, "story": None, "pact": None, "services": {},
        "visited": [at["key"]],
    }


def _board_output(state: dict, settlement: str | None = None) -> str:
    args = argparse.Namespace(settlement=settlement, dm=False)
    out = io.StringIO()
    with mock.patch.object(session, "load", lambda: state), \
            mock.patch.object(session, "save", lambda s: None), \
            redirect_stdout(out):
        session.cmd_board(args)
    return out.getvalue()


def _inactive(world: dict) -> dict:
    """A materialized settlement whose ordinary board is shut."""
    return next(s for s in quests.settlements(world)
                if not s["board_active"])


# --------------------------------------------------------------------------- #
# A. Sparse ordinary boards
# --------------------------------------------------------------------------- #

class TheBoardActivityRoll(unittest.TestCase):
    def test_the_rates_are_the_authored_hundred_sixty_twentyfive(self) -> None:
        """Measured over a large deterministic sample of slot identities.
        A capital always posts work; most towns do; most villages do not --
        and a village with nothing to offer is a correct village."""
        counted = {band: [0, 0] for band in places.BOARD_ACTIVE_CHANCE}
        for n in range(3000):
            for tier, capital in (("town", True), ("town", False),
                                  ("village", False)):
                band = "capital" if capital else tier
                slot = {"id": f"tile/r{n % 18 + 1:02d}/c{n % 30 + 1:02d}"
                              f"/settlement/{tier}",
                        "tier": tier, "capital": capital}
                counted[band][1] += 1
                counted[band][0] += places.board_active_roll(n, slot)
        for band, (active, total) in counted.items():
            self.assertAlmostEqual(active / total,
                                   places.BOARD_ACTIVE_CHANCE[band],
                                   delta=0.03, msg=band)

    def test_the_roll_is_stable_for_one_slot(self) -> None:
        slot = {"id": "tile/r09/c10/settlement/02", "tier": "village",
                "capital": False}
        first = places.board_active_roll(11, slot)
        self.assertEqual(first, places.board_active_roll(11, slot))
        self.assertEqual(first, places.board_active_roll(11, dict(slot)))

    def test_every_capital_posts_ordinary_work(self) -> None:
        for seed in (3, 8, 21):
            world = _world(seed)
            capitals = [s for s in quests.settlements(world) if s["capital"]]
            self.assertEqual(len(capitals), 3, seed)
            for capital in capitals:
                self.assertTrue(capital["board_active"], capital["name"])

    def test_the_starting_settlement_is_forced_active(self) -> None:
        """Whatever its own roll said. The game has to start at a board."""
        forced = 0
        for seed in range(40):
            world = places.create_geography(seed)
            start = world["areas"][world["start_area"]]
            self.assertTrue(start["board_active"], seed)
            slot = world["settlement_slots"][start["settlement_slot"]]
            if not places.board_active_roll(seed, slot):
                forced += 1
        self.assertGreater(forced, 0)   # the override is doing real work

    def test_the_flag_survives_the_save(self) -> None:
        world = _world(5)
        before = {s["key"]: s["board_active"]
                  for s in quests.settlements(world)}
        reloaded = json.loads(json.dumps(world))
        after = {s["key"]: s["board_active"]
                 for s in quests.settlements(reloaded)}
        self.assertEqual(before, after)

    def test_the_flag_does_not_move_when_a_slot_materializes_late(self) -> None:
        world = _world(9)
        slot = next(s for s in world["settlement_slots"].values()
                    if s["area"] is None)
        want = places.board_active_roll(world["seed"], slot)
        area = places.materialize_slot(world, slot)
        self.assertEqual(area["board_active"], want)


class TheInactiveBoard(unittest.TestCase):
    def setUp(self) -> None:
        self.world = _world(27)
        self.shut = _inactive(self.world)

    def test_a_shut_board_has_no_ordinary_capacity(self) -> None:
        self.assertEqual(quests.board_slots(self.world, self.shut), 0)

    def test_the_floor_does_not_reach_a_shut_board(self) -> None:
        """`BOARD_SLOTS_FLOOR` keeps an ACTIVE board a place with work in
        it; it is not a guarantee that every settlement has any."""
        self.assertGreaterEqual(worldsim.BOARD_SLOTS_FLOOR, 1)
        self.assertEqual(quests.board_slots(self.world, self.shut), 0)

    def test_a_shut_board_refills_to_nothing(self) -> None:
        posted = quests.refresh_settlement_board(
            self.world, self.shut, 4, random.Random(3))
        self.assertEqual([q for q in posted
                          if quests.is_ordinary_posting(q)], [])
        self.assertEqual([q for q in quests.open_quests(self.world, self.shut)
                          if quests.is_ordinary_posting(q)], [])

    def test_worldgen_posts_nothing_at_a_shut_board(self) -> None:
        for seed in (3, 27, 44):
            world = _world(seed)
            for settlement in quests.settlements(world):
                if settlement["board_active"]:
                    continue
                self.assertEqual(
                    [q for q in quests.open_quests(world, settlement)
                     if quests.is_ordinary_posting(q)], [],
                    f"{seed}/{settlement['name']}")

    def test_a_shut_board_forecasts_nothing(self) -> None:
        self.assertEqual(
            quests.board_forecast(self.world, self.shut, 9), 0)

    def test_settlements_with_no_work_are_the_common_case(self) -> None:
        """It is valid and EXPECTED for a settlement to have no ordinary
        quests -- roughly a third of a fresh world's materialized places."""
        shut = 0
        total = 0
        for seed in range(20):
            world = _world(seed)
            setts = quests.settlements(world)
            total += len(setts)
            shut += sum(1 for s in setts if not s["board_active"])
        self.assertGreater(shut, 0)
        self.assertLess(shut, total)


# --------------------------------------------------------------------------- #
# B. The forced families
# --------------------------------------------------------------------------- #

class TheForcedFamilies(unittest.TestCase):
    def setUp(self) -> None:
        self.world = _world(27)
        self.shut = _inactive(self.world)

    def test_the_ordinary_reading_of_each_flag(self) -> None:
        self.assertTrue(quests.is_ordinary_posting({"id": "q1"}))
        for forced in ({"kind": "delivery"}, {"world_card": "x/y"},
                       {"story_wave": 0}, {"hell_task": True},
                       {"forced": True}):
            self.assertFalse(quests.is_ordinary_posting(forced), forced)

    def test_a_world_cards_job_reaches_a_shut_board(self) -> None:
        """A world event is news, and news does not wait for a slot that
        will never open."""
        posting = next(p for p in worldsim.board_postings(
            self.world, self.shut["land"])) if worldsim.board_postings(
                self.world, self.shut["land"]) else None
        if posting is None:      # this land's deck is quiet: force one up
            card = next(spec for spec in worldsim.CARDS
                        if (spec.get("outlets") or {}).get("quest"))
            posting = {"key": card["key"],
                       "job": card["outlets"]["quest"]["post"],
                       "pay": 1.0}
        quest = quests._post_card_quest(self.world, self.shut, posting,
                                        random.Random(2), day=3)
        self.assertIn(quest["id"], self.shut["quests"])
        self.assertFalse(quests.is_ordinary_posting(quest))
        self.assertFalse(self.shut["board_active"])
        self.assertEqual(quests.board_slots(self.world, self.shut), 0)

    def test_a_courier_run_reaches_a_shut_board(self) -> None:
        quest = quests._post_delivery(self.world, random.Random(5),
                                      day=2, origins=[self.shut])
        self.assertIn(quest["id"], self.shut["quests"])
        self.assertEqual(quest["origin"], self.shut["key"])
        self.assertFalse(self.shut["board_active"])

    def test_hells_assignment_reaches_a_shut_board(self) -> None:
        quest = karma.roll_dark_quest(self.world, self.shut, 3,
                                      random.Random(6), spread=(0, 0))
        quest["hell_task"] = True
        self.assertEqual(quest["origin"], self.shut["key"])
        self.assertTrue(quest["sites"])
        self.assertFalse(quests.is_ordinary_posting(quest))

    def test_a_forged_job_reaches_a_shut_board(self) -> None:
        quest = quests.forge_quest(self.world, "qF", 3, 1, 1, ("wolf",),
                                   "A Forged Job", random.Random(7),
                                   area_key=self.shut["key"])
        self.assertEqual(quest["origin"], self.shut["key"])
        self.assertTrue(quest["sites"])

    def test_a_story_wave_reaches_its_settlement_whatever_its_board(self) -> None:
        world = _world(27)
        rng = random.Random(3)
        tale = story.init_story(world, rng, pc_homeland="firascir")
        tale["wave_posted"] = 0
        quest, lines = story.post_wave(world, tale, rng, day=4)
        origin = world["areas"][quest["origin"]]
        self.assertIn(quest["id"], origin["quests"])
        self.assertFalse(quests.is_ordinary_posting(quest))
        self.assertTrue(lines)

    def test_forced_work_does_not_eat_the_ordinary_capacity(self) -> None:
        """An active board keeps its own slot count of generated work even
        while a card's job and a courier run sit on it."""
        world = _world(31)
        town = next(s for s in quests.settlements(world)
                    if s["board_active"] and not s["capital"])
        quests._post_delivery(world, random.Random(1), day=1, origins=[town])
        slots = quests.board_slots(world, town)
        quests.refresh_settlement_board(world, town, 1, random.Random(2))
        ordinary = [q for q in quests.open_quests(world, town)
                    if quests.is_ordinary_posting(q)]
        self.assertEqual(len(ordinary), slots)

    def test_forced_work_shows_in_the_forecast(self) -> None:
        world = _world(31)
        shut = _inactive(world)
        self.assertEqual(quests.board_forecast(world, shut, 3), 0)
        quests._post_delivery(world, random.Random(1), day=1, origins=[shut])
        self.assertEqual(quests.board_forecast(world, shut, 3), 1)


# --------------------------------------------------------------------------- #
# C. The three-day rumor radius
# --------------------------------------------------------------------------- #

class TheRumorRadius(unittest.TestCase):
    """Seed 19 opens at Shepham, with Dublin two days off (one job posted)
    and London three (none): one populated group and one empty one, which
    is the pair the readout has to tell apart."""

    def setUp(self) -> None:
        self.world = _world(19)
        self.here = self.world["areas"][self.world["start_area"]]

    def test_the_seed_stands_where_this_class_thinks_it_does(self) -> None:
        near = {s["name"]: days for s, days
                in quests.nearby_settlements(self.world, self.here["tile"])}
        self.assertEqual(near.get("Dublin"), 2)
        self.assertEqual(near.get("London"), 3)

    def test_nobody_beyond_the_radius_is_in_earshot(self) -> None:
        near = quests.nearby_settlements(self.world, self.here["tile"])
        for settlement, days in near:
            self.assertLessEqual(days, quests.QUEST_RUMOR_DAYS)
            self.assertEqual(days, places.path_days(self.here["tile"],
                                                    settlement["tile"]))

    def test_the_current_settlement_is_in_its_own_radius(self) -> None:
        near = dict((s["key"], d) for s, d in quests.nearby_settlements(
            self.world, self.here["tile"]))
        self.assertEqual(near[self.here["key"]], 0)

    def test_an_unknown_settlement_is_not_in_earshot(self) -> None:
        """Reading local rumors is a lazy roll point, not a discovery
        verb: it never reveals a settlement the party has not found."""
        world, here = self.world, self.here
        dublin = next(s for s in quests.settlements(world)
                      if s["name"] == "Dublin")
        keys = lambda: [s["key"] for s, _d
                        in quests.nearby_settlements(world, here["tile"])]
        self.assertIn(dublin["key"], keys())
        dublin["known"] = False
        self.assertNotIn(dublin["key"], keys())

    def test_nothing_beyond_the_radius_is_in_earshot_however_famous(self) -> None:
        world, here = self.world, self.here
        far = max(quests.settlements(world),
                  key=lambda s: places.path_days(here["tile"], s["tile"]))
        self.assertGreater(places.path_days(here["tile"], far["tile"]),
                           quests.QUEST_RUMOR_DAYS)
        self.assertNotIn(far["key"],
                         [s["key"] for s, _d
                          in quests.nearby_settlements(world, here["tile"])])

    def test_the_radius_is_ordered_nearest_first_and_stably(self) -> None:
        near = quests.nearby_settlements(self.world, self.here["tile"])
        self.assertEqual([d for _s, d in near], sorted(d for _s, d in near))
        keys = [(d, s["tile"], s["key"]) for s, d in near]
        self.assertEqual(keys, sorted(keys))
        again = quests.nearby_settlements(self.world, self.here["tile"])
        self.assertEqual([s["key"] for s, _d in near],
                         [s["key"] for s, _d in again])

    def test_the_readout_groups_by_the_road_and_omits_empty_groups(self) -> None:
        world, here = self.world, self.here
        state = _state(world, here, day=2)
        text = _board_output(state)
        self.assertIn("HERE:", text)
        near = quests.nearby_settlements(world, here["tile"])
        for want in range(1, quests.QUEST_RUMOR_DAYS + 1):
            has_work = any(
                quests.open_quests(world, s, state["clock"].day)
                for s, d in near if d == want)
            label = f"{want} DAY{'S' if want > 1 else ''} AWAY:"
            self.assertEqual(label in text, has_work, label)

    def test_a_remote_row_names_the_settlement_the_tile_and_the_days(self) -> None:
        world, here, day = self.world, self.here, 2
        settlement, days = next(
            (s, d) for s, d in quests.nearby_settlements(world, here["tile"])
            if d > 0 and quests.open_quests(world, s, day))
        lines = quests.rumor_lines(
            world, quests.nearby_settlements(world, here["tile"]), day)
        text = "\n".join(lines)
        self.assertIn(settlement["name"], text)
        self.assertIn(world["tiles"][settlement["tile"]]["name"], text)
        self.assertIn(f"{days} days off", text)
        for quest in quests.open_quests(world, settlement, day):
            self.assertIn(f"[{quest['id']}]", text)

    def test_the_empty_group_is_omitted(self) -> None:
        """London is three days off and has nothing posted; the readout
        does not print an empty heading over it."""
        world, here = self.world, self.here
        lines = quests.rumor_lines(
            world, quests.nearby_settlements(world, here["tile"]), 2)
        text = "\n".join(lines)
        self.assertIn("2 DAYS AWAY:", text)
        self.assertNotIn("3 DAYS AWAY:", text)
        self.assertNotIn("HERE", text)

    def test_the_single_day_group_says_day_not_days(self) -> None:
        world = _world(37)      # Sanoro, with Lisbon one day's road off
        here = world["areas"][world["start_area"]]
        lines = quests.rumor_lines(
            world, quests.nearby_settlements(world, here["tile"]), 2)
        text = "\n".join(lines)
        self.assertIn("1 DAY AWAY:", text)
        self.assertIn("1 day off", text)
        self.assertNotIn("1 days", text)

    def test_the_here_group_is_not_repeated_as_a_rumor(self) -> None:
        world, here = self.world, self.here
        lines = quests.rumor_lines(
            world, quests.nearby_settlements(world, here["tile"]), 2)
        for quest in quests.open_quests(world, here, 2):
            self.assertNotIn(f"[{quest['id']}]", "\n".join(lines))

    def test_only_boards_in_earshot_are_refreshed(self) -> None:
        world, here = self.world, self.here
        state = _state(world, here, day=12)
        near = {s["key"] for s, _d
                in quests.nearby_settlements(world, here["tile"])}
        far = [s for s in quests.settlements(world) if s["key"] not in near]
        self.assertTrue(far)
        before = {s["key"]: (list(s["quests"]), s.get("board_day"))
                  for s in far}
        session.board_clock(state)
        for settlement in far:
            self.assertEqual((list(settlement["quests"]),
                              settlement.get("board_day")),
                             before[settlement["key"]], settlement["name"])

    def test_a_board_in_earshot_is_refreshed(self) -> None:
        world, here = self.world, self.here
        state = _state(world, here, day=12)
        session.board_clock(state)
        for settlement, _days in quests.nearby_settlements(world,
                                                           here["tile"]):
            self.assertEqual(settlement["board_day"], 12, settlement["name"])

    def test_board_all_observes_without_widening_the_refresh(self) -> None:
        """The DM's inventory shows every materialized posting; which boards
        MOVE is still decided by where the party stands."""
        world, here = self.world, self.here
        near = {s["key"] for s, _d
                in quests.nearby_settlements(world, here["tile"])}
        far = [s for s in quests.settlements(world) if s["key"] not in near]
        state = _state(world, here, day=15)
        before = {s["key"]: (list(s["quests"]), s.get("board_day"))
                  for s in far}
        text = _board_output(state, settlement="all")
        for settlement in far:
            self.assertEqual((list(settlement["quests"]),
                              settlement.get("board_day")),
                             before[settlement["key"]], settlement["name"])
        self.assertIn(far[0]["name"], text)

    def test_a_settlement_beyond_the_radius_is_never_shown(self) -> None:
        world, here = self.world, self.here
        state = _state(world, here, day=6)
        near = {s["key"] for s, _d
                in quests.nearby_settlements(world, here["tile"])}
        text = _board_output(state)
        for settlement in quests.settlements(world):
            if settlement["key"] in near:
                continue
            for quest in quests.open_quests(world, settlement):
                self.assertNotIn(f"[{quest['id']}]", text,
                                 f"{settlement['name']} {quest['id']}")


# --------------------------------------------------------------------------- #
# D. The ordinary target radius
# --------------------------------------------------------------------------- #

class TheTargetRadius(unittest.TestCase):
    def test_no_generated_target_is_more_than_three_days_out(self) -> None:
        for seed in range(12):
            world = _world(seed)
            for quest in world["quests"].values():
                if quest.get("kind") == "delivery" or "target_area" not in quest:
                    continue
                origin = world["areas"][quest["origin"]]
                target = world["areas"][quest["target_area"]]
                self.assertLessEqual(
                    places.path_days(origin["tile"], target["tile"]),
                    quests.ORDINARY_TARGET_DAYS,
                    f"{seed}/{quest['id']} {quest['name']}")

    def test_the_refilled_board_keeps_the_radius(self) -> None:
        world = _world(4)
        rng = random.Random(2)
        for settlement in quests.settlements(world):
            quests.refresh_settlement_board(world, settlement, 6, rng)
        for quest in world["quests"].values():
            if quest.get("kind") == "delivery" or "target_area" not in quest:
                continue
            origin = world["areas"][quest["origin"]]
            target = world["areas"][quest["target_area"]]
            self.assertLessEqual(
                places.path_days(origin["tile"], target["tile"]),
                quests.ORDINARY_TARGET_DAYS, quest["id"])

    def test_compatibility_is_not_traded_for_the_radius(self) -> None:
        """When nothing compatible stands within reach the job falls back
        to the ORIGIN Tile's own countryside -- never to incompatible
        ground that merely happens to be close."""
        world = _world(6)
        origin = world["areas"][world["start_area"]]
        requirement = {"area_any": ("nowhere-at-all",),
                       "site_template": "camp", "domain": "mixed",
                       "reuse": "never"}
        target = quests._select_quest_area(world, origin["key"], requirement,
                                           random.Random(1))
        self.assertEqual(
            target["id"], world["tiles"][origin["tile"]]["natural_area"])

    def test_the_origin_tile_is_always_a_legal_fallback(self) -> None:
        for seed in (2, 6, 19):
            world = _world(seed)
            for settlement in quests.settlements(world):
                requirement = {"area_any": (), "site_template": "camp",
                               "domain": "mixed", "reuse": "never"}
                target = quests._select_quest_area(
                    world, settlement["key"], requirement, random.Random(seed))
                self.assertEqual(target["tile"], settlement["tile"])

    def test_the_choice_is_stable_off_the_seed(self) -> None:
        """The candidate set is assembled in Tile/Area order before the
        quest's own rng picks from it: no dict or hash order anywhere."""
        world = _world(8)
        origin = world["areas"][world["start_area"]]
        template = quests.TEMPLATES[origin["homeland"]][0]
        requirement = quests.quest_place_requirement(template)
        first = quests._select_quest_area(world, origin["key"], requirement,
                                          random.Random(5))
        for _ in range(5):
            again = quests._select_quest_area(world, origin["key"],
                                              requirement, random.Random(5))
            self.assertEqual(first["id"], again["id"])

    def test_lifting_the_radius_reaches_past_it(self) -> None:
        world = _world(6)
        origin = world["areas"][world["start_area"]]
        far = max(quests.settlements(world),
                  key=lambda s: places.path_days(origin["tile"], s["tile"]))
        self.assertGreater(places.path_days(origin["tile"], far["tile"]),
                           quests.ORDINARY_TARGET_DAYS)
        requirement = {"area_any": tuple(far["tags"]),
                       "site_template": "camp", "domain": "built",
                       "reuse": "never"}
        reached = {quests._select_quest_area(world, origin["key"], requirement,
                                             random.Random(n), None)["id"]
                   for n in range(40)}
        self.assertIn(far["id"], reached)
        bounded = {quests._select_quest_area(world, origin["key"], requirement,
                                             random.Random(n))["id"]
                   for n in range(40)}
        self.assertNotIn(far["id"], bounded)

    def test_a_dark_job_keeps_the_ordinary_radius_by_default(self) -> None:
        world = _world(10)
        here = quests.settlements(world)[0]
        for n in range(6):
            quest = karma.roll_dark_quest(world, here, 3, random.Random(n),
                                          spread=(0, 0))
            target = world["areas"][quest["target_area"]]
            self.assertLessEqual(
                places.path_days(here["tile"], target["tile"]),
                quests.ORDINARY_TARGET_DAYS, quest["name"])


# --------------------------------------------------------------------------- #
# E. The path-priced clock
# --------------------------------------------------------------------------- #

class ThePathPricedClock(unittest.TestCase):
    def setUp(self) -> None:
        self.world = _world(27)
        self.origin = quests.settlements(self.world)[0]

    def _site_at(self, tile_id: str, site_id: str) -> str:
        area = self.world["areas"][self.world["tiles"][tile_id]
                                   ["natural_area"]]
        quests.new_site(self.world, area["key"], site_id, "a place", 3)
        return site_id

    def _road(self, *site_ids: str) -> int:
        return quests.route_days(self.world, {"origin": self.origin["key"],
                                              "sites": list(site_ids)})

    def test_work_in_the_origin_tile_buys_no_road(self) -> None:
        here = self.origin["tile"]
        self._site_at(here, "site/test/home")
        self.assertEqual(self._road("site/test/home"), 0)

    def test_a_job_one_tile_over_buys_the_trip_both_ways(self) -> None:
        row, column = places.tile_row_column(self.origin["tile"])
        neighbour = places.neighbor_id(self.origin["tile"],
                                       "east" if column < places.MAP_COLUMNS
                                       else "west")
        self._site_at(neighbour, "site/test/next-door")
        self.assertEqual(self._road("site/test/next-door"),
                         2 * places.path_days(self.origin["tile"], neighbour))

    def test_a_mountain_job_pays_the_surcharge_at_both_ends(self) -> None:
        mountain = next(t for t in self.world["tile_order"]
                        if self.world["tiles"][t]["biome"] == "mountain")
        self._site_at(mountain, "site/test/peak")
        want = 2 * places.path_days(self.origin["tile"], mountain)
        self.assertEqual(self._road("site/test/peak"), want)
        self.assertGreater(want, 0)

    def test_a_job_across_water_pays_for_the_crossing(self) -> None:
        sea = next(t for t in self.world["tile_order"]
                   if self.world["tiles"][t]["biome"] == "sea")
        self._site_at(sea, "site/test/reef")
        self.assertEqual(self._road("site/test/reef"),
                         2 * places.path_days(self.origin["tile"], sea))

    def test_a_multi_site_job_pays_the_route_it_actually_walks(self) -> None:
        row, column = places.tile_row_column(self.origin["tile"])
        west = places.tile_id(row, max(1, column - 2))
        east = places.tile_id(row, min(places.MAP_COLUMNS, column + 2))
        self._site_at(west, "site/test/west")
        self._site_at(east, "site/test/east")
        here = self.origin["tile"]
        self.assertEqual(
            self._road("site/test/west", "site/test/east"),
            places.path_days(here, west) + places.path_days(west, east)
            + places.path_days(east, here))

    def test_the_posted_window_carries_the_road(self) -> None:
        lo, hi = quests.QUEST_WINDOW_DAYS
        for seed in (3, 27):
            world = _world(seed)
            for quest in world["quests"].values():
                if quest.get("kind") == "delivery" or not quest.get("sites"):
                    continue
                road = quests.route_days(world, quest)
                self.assertGreaterEqual(quest["window"], lo + road)
                self.assertLessEqual(quest["window"], hi + road)

    def test_the_window_is_walkable_at_the_radius_ceiling(self) -> None:
        """The doctrine the clock rests on: a job at the far edge of the
        ordinary radius can be walked to, cleared and reported back inside
        the window it was posted with."""
        world = _world(27)
        origin = quests.settlements(world)[0]
        quest = {"origin": origin["key"], "sites": []}
        far = max(world["tile_order"],
                  key=lambda t: -abs(places.path_days(origin["tile"], t)
                                     - quests.ORDINARY_TARGET_DAYS))
        area = world["areas"][world["tiles"][far]["natural_area"]]
        quests.new_site(world, area["key"], "site/test/edge", "a place", 3)
        quest["sites"] = ["site/test/edge"]
        quests.stamp_quest_clock(quest, 0, random.Random(1),
                                 extra_days=quests.route_days(world, quest))
        self.assertGreaterEqual(
            quest["window"],
            2 * places.path_days(origin["tile"], far) + quests.QUEST_WINDOW_DAYS[0])


class TheDeliveryPrice(unittest.TestCase):
    def test_a_courier_run_crosses_a_border_and_is_not_radius_bound(self) -> None:
        world = _world(27)
        couriers = [q for q in world["quests"].values()
                    if q.get("kind") == "delivery"]
        self.assertTrue(couriers)
        for quest in couriers:
            origin = world["areas"][quest["origin"]]
            dest = world["areas"][quest["dest"]]
            self.assertNotEqual(origin["land"], dest["land"])
            self.assertEqual(quest["days"],
                             places.path_days(origin["tile"], dest["tile"]))

    def test_the_pay_is_the_exact_one_way_distance(self) -> None:
        world = _world(27)
        for quest in world["quests"].values():
            if quest.get("kind") != "delivery":
                continue
            self.assertEqual(quest["gold"],
                             quests.DELIVERY_GOLD_PER_DAY * quest["days"])
            self.assertEqual(quest["xp"],
                             quests.DELIVERY_XP_PER_DAY * quest["days"])

    def test_the_window_buys_the_round_trip(self) -> None:
        world = _world(27)
        lo, hi = quests.QUEST_WINDOW_DAYS
        for quest in world["quests"].values():
            if quest.get("kind") != "delivery":
                continue
            self.assertGreaterEqual(quest["window"], lo + 2 * quest["days"])
            self.assertLessEqual(quest["window"], hi + 2 * quest["days"])

    def test_the_distance_is_symmetric(self) -> None:
        world = _world(27)
        for quest in world["quests"].values():
            if quest.get("kind") != "delivery":
                continue
            origin = world["areas"][quest["origin"]]
            dest = world["areas"][quest["dest"]]
            self.assertEqual(places.path_days(dest["tile"], origin["tile"]),
                             quest["days"])


# --------------------------------------------------------------------------- #
# F. The opening
# --------------------------------------------------------------------------- #

class TheOpeningQuest(unittest.TestCase):
    def test_the_opening_is_always_posted_at_an_active_board(self) -> None:
        for seed in range(15):
            world = _world(seed)
            qid = world["opening_quest"]
            self.assertIn(qid, world["quests"], seed)
            quest = world["quests"][qid]
            start = world["areas"][world["start_area"]]
            self.assertEqual(quest["origin"], start["key"], seed)
            self.assertTrue(start["board_active"], seed)
            self.assertIn(qid, start["quests"], seed)

    def test_the_opening_is_geographically_legal(self) -> None:
        for seed in range(15):
            world = _world(seed)
            quest = world["quests"][world["opening_quest"]]
            start = world["areas"][world["start_area"]]
            target = world["areas"][quest["target_area"]]
            self.assertLessEqual(
                places.path_days(start["tile"], target["tile"]),
                quests.ORDINARY_TARGET_DAYS, seed)
            self.assertTrue(quest["sites"], seed)
            for site_id in quest["sites"]:
                self.assertIn(site_id, world["sites"], seed)

    def test_the_opening_is_walkable_inside_its_window(self) -> None:
        for seed in range(15):
            world = _world(seed)
            quest = world["quests"][world["opening_quest"]]
            self.assertGreaterEqual(
                quest["window"],
                quests.route_days(world, quest) + quests.QUEST_WINDOW_DAYS[0])


if __name__ == "__main__":
    unittest.main()
