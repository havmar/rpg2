"""The towns & the tongues contract suite (2026-08-22, the medieval world
arc's session 3).

Four parts. *The town-name table*: 183 tiles can ever seat a town, 19 of
them are already named by a historical city or a mine, and the authored
table names the other 164 -- every one of them on a mid/high/dense tile of
the country whose name it wears, no name used twice anywhere in the three
authored tables, ASCII and inside the page's width, and three broken worlds,
one per clause the session added to `validate_world`. *The naming rule*: a
tile's town name goes to the CHIEF slot and only when the census gave it
town tier or better -- a second town on the tile and everything from village
down draws the generic pool, an authored slot keeps its own name, and no
name is spent twice in a whole revealed world. *The tongues*: the nine
languages off the catalog, Latin as Byzantium's own and the west's second,
the roll (everyone Latin plus their homeland's, a Byzantine Latin plus one
other), and the NPC who carries no list at all. *The SPEAKS line*: on the
candidate sheet and on the party board, across the save, and at 40 columns
in a real new game.

`python -m unittest -v test_towns.py`
"""

from __future__ import annotations

import contextlib
import copy
import io
import json
import random
import tempfile
import unittest
from pathlib import Path

import people
import places
import quests
import rpg
import session

TOWN_CAPABLE = 183          # mid/high/dense land tiles -- the tiles a town or
                            # a city can ever be rolled on. Campaign-invariant:
                            # the band reads only the ground and the shoreline.
AUTHORED_ALREADY = 19       # ...of which a historical city or a mine names
AUTHORED_TOWNS = 164        # ...leaving this many for TILE_TOWN_NAMES
TOWNS_PER_COUNTRY = {"phyrascia": 9, "seraptania": 20, "teutonia": 13,
                     "thule": 4, "vellisclavia": 27, "byzantium": 36,
                     "andalusia": 8, "umaia": 37, "tergal": 10}


def _world(seed: int = 5) -> dict:
    return places.create_geography(seed)


def _town_tiles(world: dict) -> set[tuple[int, int]]:
    """Every land Tile whose band admits a town or a city."""
    return {(t["row"], t["column"]) for t in world["tiles"].values()
            if t["biome"] != "sea"
            and places.population_band(world, t) in places.TOWN_BANDS}


def _slots(world: dict, tile: dict) -> list[dict]:
    return [world["settlement_slots"][sid] for sid in tile["settlement_slots"]]


# --------------------------------------------------------------------------- #
# A. The town-name table
# --------------------------------------------------------------------------- #

class TheTownNameTable(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.world = _world()
        cls.town_tiles = _town_tiles(cls.world)

    def test_the_tiles_that_can_seat_a_town_are_the_measured_183(self):
        self.assertEqual(len(self.town_tiles), TOWN_CAPABLE)
        named = {t for t in self.town_tiles
                 if t in places.HISTORICAL_BY_TILE or t in places.MINES}
        self.assertEqual(len(named), AUTHORED_ALREADY)
        self.assertEqual(len(places.TILE_TOWN_NAMES), AUTHORED_TOWNS)

    def test_the_table_covers_exactly_the_tiles_left_over(self):
        owed = {t for t in self.town_tiles
                if t not in places.HISTORICAL_BY_TILE and t not in places.MINES}
        self.assertEqual(set(places.TILE_TOWN_NAMES), owed)

    def test_every_named_tile_is_land_inside_the_frame(self):
        for row, column in places.TILE_TOWN_NAMES:
            self.assertTrue(1 <= row <= places.MAP_ROWS)
            self.assertTrue(1 <= column <= places.MAP_COLUMNS)
            tile = self.world["tiles"][places.tile_id(row, column)]
            self.assertNotEqual(tile["biome"], "sea",
                                places.tile_coordinate(row, column))

    def test_each_country_carries_its_own_share(self):
        """A name is the most country-shaped thing in the game: the table is
        pinned per country, so a repaint of the overlay has to be a decision
        rather than a drift."""
        census: dict[str, int] = {c: 0 for c in places.COUNTRIES}
        for row, column in places.TILE_TOWN_NAMES:
            census[places.country_at(row, column)] += 1
        self.assertEqual(census, TOWNS_PER_COUNTRY)
        self.assertEqual(sum(census.values()), AUTHORED_TOWNS)

    def test_no_name_is_authored_twice(self):
        names = list(places.TILE_TOWN_NAMES.values())
        names += [n for _r, _c, n, *_rest in places.HISTORICAL_CITIES]
        names += [n for n, _goods in places.MINES.values()]
        self.assertEqual(len(names), len(set(names)))

    def test_no_town_name_collides_with_a_generic_pool(self):
        """The pools are invented sounds and these are real towns: an
        overlap would put one name in two naming systems."""
        pooled = {name for pools in places.SETTLEMENT_NAMES.values()
                  for names in pools.values() for name in names}
        self.assertFalse(pooled & set(places.TILE_TOWN_NAMES.values()))

    def test_the_names_are_ascii_and_fit_the_page(self):
        for name in places.TILE_TOWN_NAMES.values():
            self.assertTrue(name.isascii(), name)
            self.assertTrue(name.strip(), name)
            self.assertLessEqual(len(name), 20, name)

    def test_the_town_capable_set_is_campaign_invariant(self):
        """The band is a fact about the ground, so the table is authored
        against every world at once."""
        for seed in (1, 2, 17):
            self.assertEqual(_town_tiles(_world(seed)), self.town_tiles)

    def test_an_illegal_town_table_raises_where_the_world_is_made(self):
        """One broken world per clause the towns session added."""
        table = places.TILE_TOWN_NAMES

        def broken(replacement):
            places.TILE_TOWN_NAMES = replacement
            try:
                with self.assertRaises(ValueError):
                    places.validate_world(self.world)
            finally:
                places.TILE_TOWN_NAMES = table

        missing = dict(table)
        missing.pop(next(iter(missing)))
        broken(missing)

        stray = dict(table)
        stray[(1, 1)] = "Nowhere"       # (1,1) is open sea
        broken(stray)

        twice = dict(table)
        keys = list(twice)
        twice[keys[0]] = twice[keys[1]]
        broken(twice)

        collides = dict(table)
        collides[keys[0]] = "London"    # a historical city's own name
        broken(collides)


# --------------------------------------------------------------------------- #
# B. The naming rule
# --------------------------------------------------------------------------- #

class TheChiefSlotTakesTheTownName(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.world = _world(5)

    def _chief(self, tier: str, **want) -> tuple[dict, dict]:
        """A tile whose chief slot has this tier, plus whatever else the
        test asks of the slot."""
        for tile in self.world["tiles"].values():
            if tile["biome"] == "sea" or not tile["settlement_slots"]:
                continue
            if (tile["row"], tile["column"]) not in places.TILE_TOWN_NAMES:
                continue
            slot = _slots(self.world, tile)[0]
            if slot["tier"] != tier:
                continue
            if all(slot[key] == value for key, value in want.items()):
                return tile, slot
        self.fail(f"no chief {tier} in this world")

    def test_a_chief_town_wears_the_tile_s_real_name(self):
        world = copy.deepcopy(self.world)
        found = 0
        for tile in world["tiles"].values():
            where = (tile["row"], tile["column"])
            if where not in places.TILE_TOWN_NAMES:
                continue
            slots = _slots(world, tile)
            if not slots or slots[0]["tier"] not in places.TOWN_GRADE:
                continue
            area = places.materialize_slot(world, slots[0])
            self.assertEqual(area["name"], places.TILE_TOWN_NAMES[where])
            self.assertEqual(slots[0]["name"], places.TILE_TOWN_NAMES[where])
            found += 1
        self.assertGreater(found, 30)

    def test_a_chief_village_leaves_the_town_name_unspent(self):
        world = copy.deepcopy(self.world)
        tile, slot = self._chief("village")
        area = places.materialize_slot(world, world["settlement_slots"][
            slot["id"]])
        self.assertNotEqual(area["name"],
                            places.TILE_TOWN_NAMES[(tile["row"],
                                                    tile["column"])])
        self.assertIn(area["name"],
                      [n for pool in places.SETTLEMENT_NAMES[
                          tile["country"]].values() for n in pool])

    def test_a_second_town_on_the_tile_draws_the_generic_pool(self):
        world = copy.deepcopy(self.world)
        tile = next(t for t in world["tiles"].values()
                    if (t["row"], t["column"]) in places.TILE_TOWN_NAMES
                    and len(t["settlement_slots"]) > 1
                    and [s["tier"] for s in _slots(world, t)][:2]
                    == ["town", "town"])
        names = [places.materialize_slot(world, s)["name"]
                 for s in _slots(world, tile)]
        real = places.TILE_TOWN_NAMES[(tile["row"], tile["column"])]
        self.assertEqual(names[0], real)
        self.assertNotIn(real, names[1:])

    def test_an_authored_slot_keeps_its_own_name(self):
        """A historical city and a mine town are already named; the rule
        never reaches them."""
        world = copy.deepcopy(self.world)
        for (row, column), (name, *_rest) in places.HISTORICAL_BY_TILE.items():
            tile = world["tiles"][places.tile_id(row, column)]
            area = places.materialize_slot(world, _slots(world, tile)[0])
            self.assertEqual(area["name"], name)
        for (row, column), (name, _goods) in places.MINES.items():
            tile = world["tiles"][places.tile_id(row, column)]
            area = places.materialize_slot(world, _slots(world, tile)[0])
            self.assertEqual(area["name"], name)

    def test_no_settlement_name_is_spent_twice_in_a_whole_world(self):
        world = _world(9)
        names = [places.materialize_slot(world, sid)["name"]
                 for sid in world["settlement_slots"]]
        self.assertEqual(len(names), len(set(names)))
        real = set(places.TILE_TOWN_NAMES.values())
        taken = [n for n in names if n in real]
        self.assertTrue(taken)
        self.assertEqual(len(taken), len(set(taken)))

    def test_a_village_never_wears_a_real_town_name(self):
        world = _world(9)
        real = set(places.TILE_TOWN_NAMES.values())
        for sid, slot in world["settlement_slots"].items():
            places.materialize_slot(world, sid)
            if slot["tier"] in places.TOWN_GRADE:
                continue
            self.assertNotIn(slot["name"], real, sid)

    def test_the_reader_answers_the_same_question_twice(self):
        tile, slot = self._chief("town")
        first = places.tile_town_name(tile, dict(slot, name=None))
        again = places.tile_town_name(tile, dict(slot, name=None))
        self.assertEqual(first, again)
        self.assertEqual(first,
                         places.TILE_TOWN_NAMES[(tile["row"],
                                                 tile["column"])])
        # ...and never for a named slot or a second seat
        self.assertIsNone(places.tile_town_name(tile, dict(slot, name="X")))
        self.assertIsNone(places.tile_town_name(
            tile, dict(slot, name=None, index=2)))

    def test_the_names_ride_the_save(self):
        world = _world(7)
        for tile in list(world["tiles"].values())[:120]:
            for sid in tile["settlement_slots"]:
                places.materialize_slot(world, sid)
        clone = json.loads(json.dumps(world))
        self.assertEqual(clone["settlement_slots"], world["settlement_slots"])
        self.assertEqual(clone["areas"], world["areas"])
        places.validate_world(clone)

    def test_the_same_seed_seats_the_same_towns(self):
        def towns(seed):
            world = _world(seed)
            return {sid: places.materialize_slot(world, sid)["name"]
                    for sid in world["settlement_slots"]}
        self.assertEqual(towns(4), towns(4))


# --------------------------------------------------------------------------- #
# C. The tongues
# --------------------------------------------------------------------------- #

class TheTongues(unittest.TestCase):
    def test_nine_tongues_named_by_their_country(self):
        self.assertEqual(set(people.LANGUAGES), set(quests.HOMELANDS))
        self.assertEqual(len(set(people.LANGUAGES.values())), 9)
        for country, tongue in people.LANGUAGES.items():
            self.assertEqual(tongue, places.LAND_SPECS[country]["tongue"])
            self.assertTrue(tongue.isascii(), tongue)

    def test_latin_is_byzantium_s_and_the_west_s_second(self):
        self.assertEqual(people.LATIN, "Latin")
        self.assertEqual(people.LANGUAGES["byzantium"], people.LATIN)

    def test_everyone_speaks_latin_plus_their_homeland(self):
        rng = random.Random(3)
        for country in quests.HOMELANDS:
            if country == "byzantium":
                continue
            for _ in range(5):
                spoken = people.roll_tongues(rng, country)
                self.assertEqual(spoken,
                                 [people.LATIN, people.LANGUAGES[country]])

    def test_a_byzantine_speaks_latin_plus_one_other(self):
        rng = random.Random(3)
        second = set()
        for _ in range(120):
            spoken = people.roll_tongues(rng, "byzantium")
            self.assertEqual(len(spoken), 2)
            self.assertEqual(spoken[0], people.LATIN)
            self.assertNotEqual(spoken[1], people.LATIN)
            self.assertIn(spoken[1], set(people.LANGUAGES.values()))
            second.add(spoken[1])
        self.assertEqual(second,
                         {t for t in people.LANGUAGES.values()
                          if t != people.LATIN})

    def test_the_roll_is_seeded(self):
        self.assertEqual(people.roll_tongues(random.Random(11), "byzantium"),
                         people.roll_tongues(random.Random(11), "byzantium"))

    def test_a_generated_character_carries_the_list(self):
        rng = random.Random(21)
        for _ in range(30):
            hero = people.make_character(rng, 1)
            self.assertEqual(len(hero.tongues), 2)
            self.assertEqual(hero.tongues[0], people.LATIN)
            if hero.homeland != "byzantium":
                self.assertEqual(hero.tongues[1],
                                 people.LANGUAGES[hero.homeland])

    def test_the_pc_and_a_pair_carry_it_too(self):
        rng = random.Random(4)
        pc = people.make_character(rng, 1, with_traits=False, wizard=True)
        self.assertTrue(pc.tongues)
        _kind, pair = people.make_pair(rng, 1)
        for hero in pair:
            self.assertTrue(hero.tongues)

    def test_an_npc_carries_no_list(self):
        """A local speaks the local tongue, and clergy, scholars and
        officials speak Latin everywhere: an NPC needs no record."""
        npc = people.make_npc(random.Random(2), "umaia", "harbour master")
        self.assertNotIn("tongues", npc)

    def test_a_sim_body_carries_no_list(self):
        """The benches' throwaway duos come from rpg.make_party and have no
        homeland, so nothing rolls them a tongue."""
        for body in rpg.make_party(random.Random(2)):
            self.assertEqual(body.tongues, [])


# --------------------------------------------------------------------------- #
# D. The SPEAKS line
# --------------------------------------------------------------------------- #

@contextlib.contextmanager
def sandbox():
    """Point the session's save and its pages at a throwaway directory --
    a suite must never overwrite the playthrough."""
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


class TheSpeaksLine(unittest.TestCase):
    def test_the_candidate_sheet_shows_it(self):
        hero = people.make_character(random.Random(6), 2)
        line = next(ln for ln in people.character_sheet(hero)
                    if ln.strip().startswith("speaks:"))
        self.assertEqual(line.strip(),
                         "speaks: " + ", ".join(hero.tongues))

    def test_the_party_board_shows_it(self):
        hero = people.make_character(random.Random(6), 2)
        lines = session.hero_block_lines([hero], hero)
        self.assertTrue(any(ln.strip().startswith("speaks:") for ln in lines))

    def test_a_body_with_no_list_prints_no_row(self):
        body = people.make_character(random.Random(6), 1)
        body.tongues = []
        self.assertFalse(any("speaks:" in ln
                             for ln in people.character_sheet(body)))
        self.assertFalse(any("speaks:" in ln
                             for ln in session.hero_block_lines([body],
                                                                body)))

    def test_the_list_rides_the_save(self):
        hero = people.make_character(random.Random(8), 3)
        back = session._entity_from_dict(
            json.loads(json.dumps(session._entity_to_dict(hero))))
        self.assertEqual(back.tongues, hero.tongues)

    def test_a_new_game_speaks(self):
        args = session.build_parser().parse_args(
            ["new", "--seed", "5", "--level", "1"])
        out = io.StringIO()
        with sandbox(), contextlib.redirect_stdout(out):
            args.func(args)
            state = session.load()
            board = session.party_sheet_lines(state)
        for hero in state["party"]:
            self.assertEqual(len(hero.tongues), 2)
        spoken = [ln for ln in board if ln.strip().startswith("speaks:")]
        self.assertEqual(len(spoken), len(state["party"]))
        for line in spoken:
            self.assertLessEqual(len(line), session.WRAP_WIDTH, line)
            self.assertTrue(line.isascii(), line)


if __name__ == "__main__":
    unittest.main()
