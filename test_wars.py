"""THE ROLLED WARS & THE CAMPAIGN SIM -- the contract suite (2026-08-22,
the medieval world arc's session 5, and the arc's last).

Four parts, in build order:

  the six templates   the authored half: belligerents, postures and the
                      theater tuples drawn against the real map grids.
  the roll            three distinct wars and Andalusia's vassalage, on
                      their own stream, at every worldgen.
  the campaign sim    the day-stepped front: cadence, caps, expiries, the
                      garrison authority deciding a siege, determinism per
                      seed and across the save, and the non-goals.
  the surfaces        the Tile's page, the DM's brief, `world`, the new
                      game's print -- and the map page left alone.

python -m unittest -v test_wars.py
"""
from __future__ import annotations

import copy
import json
import unittest

import conquest
import places
import quests
import worldsim
from sites import FOES

CONTRACT_KEYS = {"crusade", "hundred-years", "horde", "vikings",
                 "reconquista", "eastern-war"}

# Every land a template can ever put in the field, attacker or defender.
# The theater is checked against THIS rather than against one roll's lists:
# the Reconquista's ground is south Iberia and the Maghreb whichever way
# Andalusia's vassalage falls.
BELLIGERENT_UNIVERSE = {
    "crusade": {"byzantium", "seraptania", "teutonia", "phyrascia", "umaia"},
    "hundred-years": {"phyrascia", "seraptania"},
    "horde": {"tergal", "vellisclavia"},
    "vikings": {"thule", "phyrascia", "seraptania"},
    "reconquista": {"andalusia", "byzantium", "umaia"},
    "eastern-war": {"umaia", "byzantium"},
}

_CACHE: dict[int, dict] = {}


def world(seed: int) -> dict:
    """A built world with its layer opened -- which is where the wars are
    rolled. `quests.generate_world` calls exactly this and then posts work;
    nothing about the wars reads the board, so the cheaper build is the
    honest one for this suite."""
    if seed not in _CACHE:
        built = places.create_geography(seed)
        worldsim.open_world(built)
        _CACHE[seed] = built
    return copy.deepcopy(_CACHE[seed])


def rolled(seed: int, day: int) -> dict:
    built = world(seed)
    conquest.roll_campaigns(built, day)
    return built


def war_states(built: dict) -> list[tuple[str, dict]]:
    """Every active state the campaign sim has written, place id and all."""
    out = []
    for store in (built["tiles"], built["settlement_slots"]):
        for key, place in store.items():
            for state in place["states"]:
                if state.get("active"):
                    out.append((key, state))
    return out


# --------------------------------------------------------------------------- #
# 1. The six templates
# --------------------------------------------------------------------------- #

class TheSixTemplates(unittest.TestCase):
    """The authored half. A theater is drawn by hand against the four
    overlays, so the only thing that can go wrong with it is that the hand
    slipped -- these are the clauses that catch a slip."""

    def test_the_six_are_the_contracts_six(self):
        self.assertEqual({s["key"] for s in worldsim.WAR_TEMPLATES},
                         CONTRACT_KEYS)
        self.assertEqual(len(worldsim.WAR_TEMPLATES), len(CONTRACT_KEYS))

    def test_every_theater_tile_is_land_inside_the_frame(self):
        for spec in worldsim.WAR_TEMPLATES:
            self.assertTrue(spec["theater"], spec["key"])
            self.assertEqual(len(set(spec["theater"])),
                             len(spec["theater"]), spec["key"])
            for row, column in spec["theater"]:
                self.assertTrue(1 <= row <= places.MAP_ROWS)
                self.assertTrue(1 <= column <= places.MAP_COLUMNS)
                self.assertNotEqual(places.biome_at(row, column), "sea",
                                    f"{spec['key']} fights at sea")

    def test_every_theater_tile_belongs_to_a_belligerent(self):
        for spec in worldsim.WAR_TEMPLATES:
            for row, column in spec["theater"]:
                self.assertIn(places.country_at(row, column),
                              BELLIGERENT_UNIVERSE[spec["key"]],
                              f"{spec['key']} at R{row:02d}C{column:02d}")

    def test_no_theater_stands_on_a_capital(self):
        """A settled call: a war marks the country, never the crown's own
        seat. Nine capitals, none of them in a theater."""
        capitals = {(row, column) for (row, column), (_n, _c, _b, cap)
                    in places.HISTORICAL_BY_TILE.items() if cap}
        for spec in worldsim.WAR_TEMPLATES:
            self.assertFalse(capitals & set(spec["theater"]), spec["key"])

    def test_every_theater_can_be_besieged(self):
        """A siege needs a settlement to lay itself before. Every theater
        holds several in a real world -- the fallback (burn the country
        instead) exists for a theater the census emptied, not for one the
        author left empty."""
        built = world(11)
        for spec in worldsim.WAR_TEMPLATES:
            slots = [sid for row, column in spec["theater"]
                     for sid in built["tiles"][places.tile_id(row, column)]
                     ["settlement_slots"]]
            self.assertGreaterEqual(len(slots), 5, spec["key"])

    def test_the_postures_are_the_two_the_sim_knows(self):
        for spec in worldsim.WAR_TEMPLATES:
            self.assertIn(spec["posture"], conquest.EVENT_WEIGHTS)

    def test_every_posture_table_is_a_hundred_and_names_real_events(self):
        known = {"lull", "siege", *conquest.EVENT_STATES}
        for posture, table in conquest.EVENT_WEIGHTS.items():
            self.assertEqual(sum(weight for _e, weight in table), 100,
                             posture)
            for event, _weight in table:
                self.assertIn(event, known, posture)

    def test_every_state_the_sim_writes_has_a_word(self):
        for state_id in list(conquest.EVENT_STATES.values()) + [
                "under-siege", "sacked", "occupied"]:
            self.assertIn(state_id, places.WAR_STATE_WORDS)

    def test_the_authored_copy_is_ascii_and_says_something(self):
        for spec in worldsim.WAR_TEMPLATES:
            for text in (spec["name"], spec["herald"],
                         spec.get("vassal_herald", spec["herald"])):
                self.assertTrue(text.isascii(), spec["key"])
                self.assertGreater(len(text), 10, spec["key"])
            self.assertEqual(spec["name"], spec["name"].upper())

    def test_the_crusade_draws_one_to_three_of_the_four_crowns(self):
        spec = worldsim.WAR_TEMPLATES_BY_KEY["crusade"]
        self.assertEqual(set(spec["attackers"]),
                         {"byzantium", "seraptania", "teutonia", "phyrascia"})
        self.assertEqual(spec["attacker_draw"], (1, 3))
        self.assertEqual(spec["defenders"], ("umaia",))

    def test_the_raiding_season_falls_on_both_coasts(self):
        spec = worldsim.WAR_TEMPLATES_BY_KEY["vikings"]
        self.assertEqual(spec["attackers"], ("thule",))
        self.assertEqual(set(spec["defenders"]), {"phyrascia", "seraptania"})
        owners = {places.country_at(row, column)
                  for row, column in spec["theater"]}
        self.assertEqual(owners, {"phyrascia", "seraptania"})

    def test_the_at_war_state_is_external_and_reaches_a_road(self):
        self.assertIn("at-war", worldsim.EXTERNAL_STATES)
        self.assertIn("at-war", worldsim.STATE_WORDS)
        entry = worldsim.STATE_ENCOUNTERS["at-war"]
        for kind in entry["kinds"]:
            self.assertIn(kind, FOES)


# --------------------------------------------------------------------------- #
# 2. The roll
# --------------------------------------------------------------------------- #

class TheWarRoll(unittest.TestCase):
    SEEDS = tuple(range(24))

    @classmethod
    def setUpClass(cls):
        cls.worlds = {seed: world(seed) for seed in cls.SEEDS}

    def test_three_distinct_legal_wars_in_every_world(self):
        for seed, built in self.worlds.items():
            keys = [war["key"] for war in built["wars"]]
            self.assertEqual(len(keys), worldsim.WARS_ROLLED, seed)
            self.assertEqual(len(set(keys)), len(keys), seed)
            self.assertLessEqual(set(keys), CONTRACT_KEYS, seed)

    def test_the_sweep_reaches_every_template(self):
        seen = {war["key"] for built in self.worlds.values()
                for war in built["wars"]}
        self.assertEqual(seen, CONTRACT_KEYS)

    def test_the_record_carries_exactly_the_contracted_shape(self):
        built = self.worlds[0]
        for war in built["wars"]:
            self.assertEqual(set(war), {"key", "name", "attackers",
                                        "defenders", "theater", "posture",
                                        "herald", "rolled_day", "occupied",
                                        "scars"})
            self.assertEqual(war["rolled_day"], 0)
            self.assertEqual(war["occupied"], [])
            self.assertTrue(json.dumps(war))    # the record rides the save

    def test_every_belligerent_holds_at_war_and_nobody_else_does(self):
        for seed, built in self.worlds.items():
            fighting = {polity for war in built["wars"]
                        for polity in war["attackers"] + war["defenders"]}
            for polity in built["lands"]:
                held = worldsim.state_ids(built, polity)
                self.assertEqual("at-war" in held, polity in fighting,
                                 f"{seed}/{polity}")

    def test_every_herald_is_posted_to_every_belligerent(self):
        for built in self.worlds.values():
            for war in built["wars"]:
                for polity in war["attackers"] + war["defenders"]:
                    news = [n["line"] for n
                            in worldsim.land_layer(built, polity)["news"]]
                    self.assertTrue(
                        any(war["herald"] in line and war["name"] in line
                            for line in news),
                        f"{war['key']} unheard in {polity}")
                    self.assertTrue(all(n["day"] == 0 for n
                                        in worldsim.land_layer(
                                            built, polity)["news"]
                                        if war["herald"] in n["line"]))

    def test_every_rolled_theater_is_its_own_belligerents_ground(self):
        for seed, built in self.worlds.items():
            for war in built["wars"]:
                fighting = set(war["attackers"]) | set(war["defenders"])
                for tid in war["theater"]:
                    self.assertIn(built["tiles"][tid]["country"], fighting,
                                  f"{seed}/{war['key']}/{tid}")

    def test_the_same_seed_rolls_the_same_wars(self):
        for seed in (3, 17):
            first, second = world(seed), world(seed)
            self.assertEqual(first["wars"], second["wars"])
            self.assertEqual(first["lands"]["andalusia"]["liege"],
                             second["lands"]["andalusia"]["liege"])

    def test_the_wars_are_each_worlds_own(self):
        rolls = {tuple(war["key"] for war in built["wars"])
                 for built in self.worlds.values()}
        self.assertGreater(len(rolls), 4)

    def test_the_crusade_fields_one_to_three_crowns(self):
        sizes = set()
        for built in self.worlds.values():
            for war in built["wars"]:
                if war["key"] != "crusade":
                    continue
                self.assertLessEqual(
                    set(war["attackers"]),
                    set(worldsim.WAR_TEMPLATES_BY_KEY["crusade"]["attackers"]))
                sizes.add(len(war["attackers"]))
        self.assertTrue(sizes <= {1, 2, 3} and sizes)

    def test_the_vassalage_is_a_d3_and_only_andalusia_has_a_liege(self):
        seen = set()
        for built in self.worlds.values():
            liege = built["lands"]["andalusia"]["liege"]
            self.assertIn(liege, worldsim.VASSALAGE)
            seen.add(liege)
            for polity, land in built["lands"].items():
                if polity != "andalusia":
                    self.assertIsNone(land["liege"], polity)
        self.assertEqual(seen, set(worldsim.VASSALAGE))

    def test_the_reconquista_reads_the_vassalage(self):
        """The one place the liege has mechanical teeth in this arc: a
        vassal fights for its liege, so Umaia's vassal makes Byzantium come
        alone and stands with Umaia itself."""
        seen = set()
        for built in self.worlds.values():
            war = next((w for w in built["wars"]
                        if w["key"] == "reconquista"), None)
            if war is None:
                continue
            liege = built["lands"]["andalusia"]["liege"]
            seen.add(liege)
            spec = worldsim.WAR_TEMPLATES_BY_KEY["reconquista"]
            if liege == "umaia":
                self.assertEqual(war["attackers"], ["byzantium"])
                self.assertIn("andalusia", war["defenders"])
                self.assertEqual(war["herald"], spec["vassal_herald"])
            else:
                self.assertEqual(war["attackers"], ["andalusia", "byzantium"])
                self.assertEqual(war["defenders"], ["umaia"])
                self.assertEqual(war["herald"], spec["herald"])
        self.assertIn("umaia", seen)        # both branches reached over
        self.assertTrue(seen - {"umaia"})   # the sweep

    def test_the_roll_moves_no_other_layer(self):
        """The wars run on their own derived stream (`wars:{seed}`), so a
        world built without them is identical everywhere else."""
        plain = places.create_geography(6)
        armed = world(6)
        for key in ("harvest_regions", "routes", "start_slot", "party_tile"):
            self.assertEqual(json.dumps(plain[key], sort_keys=True),
                             json.dumps(armed[key], sort_keys=True), key)
        self.assertEqual(
            [(sid, slot["tier"], slot["name"])
             for sid, slot in plain["settlement_slots"].items()],
            [(sid, slot["tier"], slot["name"])
             for sid, slot in armed["settlement_slots"].items()])


# --------------------------------------------------------------------------- #
# 3. The campaign sim
# --------------------------------------------------------------------------- #

class TheCampaignSim(unittest.TestCase):
    DAYS = 200

    @classmethod
    def setUpClass(cls):
        cls.built = rolled(3, cls.DAYS)

    def test_catching_up_is_living_through_it(self):
        step = world(3)
        for day in range(1, self.DAYS + 1):
            conquest.roll_campaigns(step, day)
        jump = rolled(3, self.DAYS)
        self.assertEqual(json.dumps(step["wars"], sort_keys=True),
                         json.dumps(jump["wars"], sort_keys=True))
        self.assertEqual(war_states(step), war_states(jump))

    def test_rolling_the_same_day_twice_changes_nothing(self):
        again = copy.deepcopy(self.built)
        conquest.roll_campaigns(again, self.DAYS)
        self.assertEqual(json.dumps(again["wars"], sort_keys=True),
                         json.dumps(self.built["wars"], sort_keys=True))
        self.assertEqual(war_states(again), war_states(self.built))

    def test_the_same_seed_gives_the_same_front(self):
        self.assertEqual(json.dumps(rolled(3, self.DAYS)["wars"],
                                    sort_keys=True),
                         json.dumps(self.built["wars"], sort_keys=True))

    def test_the_front_survives_the_save(self):
        saved = json.loads(json.dumps(self.built))
        conquest.roll_campaigns(saved, self.DAYS + 90)
        live = copy.deepcopy(self.built)
        conquest.roll_campaigns(live, self.DAYS + 90)
        self.assertEqual(json.dumps(saved["wars"], sort_keys=True),
                         json.dumps(live["wars"], sort_keys=True))
        self.assertEqual(war_states(saved), war_states(live))

    def test_the_watermark_is_the_day_it_was_rolled_to(self):
        for war in self.built["wars"]:
            self.assertEqual(war["rolled_day"], self.DAYS)

    def test_every_mark_lands_on_a_pulse_day(self):
        for _key, state in war_states(self.built):
            self.assertEqual(state["since"] % conquest.WAR_PULSE, 0,
                             state)

    def test_the_scars_are_capped_and_the_occupation_is_capped(self):
        for days in (200, 800, 2000):
            built = rolled(5, days)
            for war in built["wars"]:
                self.assertLessEqual(len(war["scars"]), conquest.SCAR_CAP,
                                     war["key"])
                self.assertLessEqual(len(war["occupied"]),
                                     conquest.OCCUPIED_CAP, war["key"])
                self.assertEqual(len(set(war["occupied"])),
                                 len(war["occupied"]))

    def test_a_world_left_alone_stays_bounded(self):
        ceiling = worldsim.WARS_ROLLED * (conquest.SCAR_CAP
                                          + conquest.OCCUPIED_CAP)
        for seed in (1, 5, 11, 42):
            built = rolled(seed, 2000)
            self.assertLessEqual(len(war_states(built)), ceiling, seed)

    def test_nothing_outlives_its_own_days(self):
        """The sim clears what it wrote when the days are spent; only the
        occupation is permanent."""
        built = rolled(11, 600)
        for _key, state in war_states(built):
            if state["id"] == "occupied":
                continue
            age = 600 - state["since"]
            self.assertLessEqual(age,
                                 conquest.SCAR_DAYS[state["id"]]
                                 + conquest.WAR_PULSE, state)

    def test_only_the_wars_own_words_are_written(self):
        for _key, state in war_states(self.built):
            self.assertIn(state["id"], places.WAR_STATE_WORDS)

    def test_every_mark_stands_in_its_own_theater(self):
        for seed in (1, 3, 5):
            built = rolled(seed, 400)
            ground = {tid for war in built["wars"] for tid in war["theater"]}
            for key, _state in war_states(built):
                tile = (key if key in built["tiles"]
                        else built["settlement_slots"][key]["tile"])
                self.assertIn(tile, ground, key)

    def test_a_besieged_town_is_asked_of_the_garrison_authority(self):
        """The siege is decided by `garrison_level`, the same authority the
        player's own conquest asks -- forcing the strength roll to the floor
        never takes a town, and to the ceiling always does."""
        table = dict.fromkeys(conquest.SIEGE_STRENGTH, (0, 0))
        with _patched(conquest, SIEGE_STRENGTH=table):
            weak = rolled(3, 400)
        self.assertFalse([s for _k, s in war_states(weak)
                          if s["id"] in ("sacked", "occupied")])
        self.assertTrue([s for _k, s in war_states(weak)
                         if s["id"] == "under-siege"])
        table = dict.fromkeys(conquest.SIEGE_STRENGTH, (99, 99))
        with _patched(conquest, SIEGE_STRENGTH=table):
            strong = rolled(3, 400)
        self.assertFalse([s for _k, s in war_states(strong)
                          if s["id"] == "under-siege"])
        self.assertTrue([s for _k, s in war_states(strong)
                         if s["id"] == "sacked"])

    def test_a_slots_garrison_is_the_areas_garrison(self):
        """The number does not move when the town finally materializes:
        the slot is asked under the Area id it will wear."""
        built = world(7)
        slots = [slot for slot in built["settlement_slots"].values()
                 if slot["area"] is None][:20]
        for slot in slots:
            before = conquest.slot_garrison_level(built, slot)
            area = places.materialize_slot(built, slot)
            self.assertEqual(before, conquest.garrison_level(built, area))

    def test_each_event_is_heard_by_both_sides_and_by_nobody_else(self):
        """Counted at the DOOR rather than on the feed: a land in two wars
        trims its news list to NEWS_KEPT like any other, so what the feed
        still holds is not what the sim posted."""
        built = world(3)
        posted: list[tuple[str, str]] = []
        real = worldsim.post_news

        def spy(w, polity, day, line):
            posted.append((polity, line))
            real(w, polity, day, line)

        with _patched(worldsim, post_news=spy):
            conquest.roll_campaigns(built, 300)
        self.assertTrue(posted)
        for war in built["wars"]:
            mine = [entry for entry in posted
                    if entry[1].startswith(war["name"])]
            heard: dict[str, int] = {}
            for polity, _line in mine:
                heard[polity] = heard.get(polity, 0) + 1
            self.assertEqual(set(heard),
                             set(war["attackers"] + war["defenders"]),
                             war["key"])
            self.assertEqual(len(set(heard.values())), 1, heard)

    def test_a_lull_says_nothing(self):
        """The one event that writes nothing and posts nothing -- with
        every pulse a lull, the world is exactly the world at day zero."""
        table = {posture: (("lull", 100),)
                 for posture in conquest.EVENT_WEIGHTS}
        with _patched(conquest, EVENT_WEIGHTS=table):
            quiet = rolled(3, 400)
        self.assertEqual(war_states(quiet), [])
        for polity in quiet["lands"]:
            self.assertEqual(len(worldsim.land_layer(quiet, polity)["news"]),
                             len(worldsim.land_layer(world(3),
                                                     polity)["news"]))

    # --- the non-goals, stated so they stay stated ------------------------- #

    def test_the_sim_never_redraws_a_border(self):
        plain = world(3)
        for tid, tile in self.built["tiles"].items():
            self.assertEqual(tile["country"], plain["tiles"][tid]["country"])

    def test_the_sim_never_touches_the_board_or_the_quests(self):
        built = quests.generate_world(3)
        before = json.dumps({"quests": built["quests"],
                             "boards": {aid: area.get("quests")
                                        for aid, area in
                                        built["areas"].items()}},
                            sort_keys=True)
        conquest.roll_campaigns(built, 400)
        after = json.dumps({"quests": built["quests"],
                            "boards": {aid: area.get("quests")
                                       for aid, area in
                                       built["areas"].items()}},
                           sort_keys=True)
        self.assertEqual(before, after)

    def test_the_sim_never_materializes_a_settlement(self):
        built = world(3)
        before = sorted(built["areas"])
        conquest.roll_campaigns(built, 400)
        self.assertEqual(sorted(built["areas"]), before)

    def test_the_sim_never_ends_a_war(self):
        built = rolled(3, 4000)
        self.assertEqual(len(built["wars"]), worldsim.WARS_ROLLED)
        for war in built["wars"]:
            self.assertTrue(war["attackers"] and war["defenders"])
            fighting = set(war["attackers"]) | set(war["defenders"])
            for polity in fighting:
                self.assertIn("at-war", worldsim.state_ids(built, polity))

    def test_occupation_gates_nothing(self):
        """A banner on the record and a line on the page. The occupied
        settlement keeps its owner, its board and its services."""
        built = rolled(5, 600)
        held = [sid for war in built["wars"] for sid in war["occupied"]]
        self.assertTrue(held)
        for sid in held:
            slot = built["settlement_slots"][sid]
            area = places.materialize_slot(built, slot)
            self.assertNotIn("owner", area)
            self.assertEqual(area["homeland"],
                             built["tiles"][slot["tile"]]["country"])
            self.assertTrue(area["services"])


class _patched:
    """Swap module attributes for the length of a block (and clear the
    world cache, since a patched table changes what a seed produces)."""

    def __init__(self, module, **values):
        self.module, self.values, self.old = module, values, {}

    def __enter__(self):
        for name, value in self.values.items():
            self.old[name] = getattr(self.module, name)
            setattr(self.module, name, value)
        return self

    def __exit__(self, *exc):
        for name, value in self.old.items():
            setattr(self.module, name, value)
        return False


# --------------------------------------------------------------------------- #
# 4. The surfaces
# --------------------------------------------------------------------------- #

class TheSurfaces(unittest.TestCase):
    WIDTH = 40

    @classmethod
    def setUpClass(cls):
        cls.built = rolled(3, 300)

    def _marked_tile(self, state_id: str | None = None) -> dict:
        for key, state in war_states(self.built):
            if state_id is not None and state["id"] != state_id:
                continue
            tid = (key if key in self.built["tiles"]
                   else self.built["settlement_slots"][key]["tile"])
            return self.built["tiles"][tid]
        raise AssertionError(f"no tile marked {state_id}")

    def test_the_tile_page_prints_the_states(self):
        tile = self._marked_tile()
        lines = places.tile_detail_lines(self.built, tile)
        words = [places.place_state_line(s)
                 for s in tile["states"] if s.get("active")]
        for word in words:
            self.assertTrue(any(word.split(" (day")[0] in line
                                for line in lines), word)

    def test_the_dm_brief_prints_the_states(self):
        tile = self._marked_tile()
        lines = places.tile_brief_lines(self.built, tile)
        for state in tile["states"]:
            if state.get("active"):
                self.assertTrue(
                    any(places.WAR_STATE_WORDS[state["id"]] in line
                        for line in lines), state)

    def test_a_besieged_settlement_reaches_both_pages(self):
        siege = next((key for key, state in war_states(self.built)
                      if state["id"] in ("under-siege", "sacked", "occupied")),
                     None)
        self.assertIsNotNone(siege)
        slot = self.built["settlement_slots"][siege]
        detail = places.tile_detail_lines(self.built, slot["tile"])
        brief = places.tile_brief_lines(self.built, slot["tile"])
        word = places.WAR_STATE_WORDS[
            next(s["id"] for s in slot["states"] if s.get("active"))]
        self.assertTrue(any(word.split(" ")[0] in line for line in detail))
        self.assertTrue(any(word.split(" ")[0] in line for line in brief))

    def test_an_unmet_settlement_is_named_by_its_tier(self):
        siege = next(key for key, state in war_states(self.built)
                     if key in self.built["settlement_slots"])
        slot = self.built["settlement_slots"][siege]
        slot["area"] = None
        lines = places.war_state_lines(
            self.built, self.built["tiles"][slot["tile"]])
        self.assertTrue(any(line.startswith(f"a {slot['tier']}:")
                            for line in lines), lines)

    def test_every_page_line_fits_the_phone(self):
        for key, _state in war_states(self.built):
            tid = (key if key in self.built["tiles"]
                   else self.built["settlement_slots"][key]["tile"])
            for lines in (places.tile_detail_lines(self.built, tid),
                          places.tile_brief_lines(self.built, tid)):
                for line in lines:
                    self.assertLessEqual(len(line), self.WIDTH, line)
                    self.assertTrue(line.isascii(), line)
        for line in worldsim.war_lines(self.built):
            self.assertLessEqual(len(line), self.WIDTH, line)
            self.assertTrue(line.isascii(), line)

    def test_the_map_page_is_untouched(self):
        plain = world(3)
        self.assertEqual(places.map_lines(self.built),
                         places.map_lines(plain))

    def test_the_map_legend_says_who_is_whose_vassal(self):
        built = next(world(seed) for seed in range(24)
                     if world(seed)["lands"]["andalusia"]["liege"])
        liege = built["lands"]["andalusia"]["liege"]
        self.assertEqual(
            places.land_label(built, "andalusia"),
            f"Andalusia ({built['lands'][liege]['name']}'s vassal)")
        self.assertEqual(places.land_label(built, "umaia"), "Umaia")
        legend = " ".join(places.map_legend_lines(built))
        self.assertIn("vassal", legend)

    def test_world_carries_the_wars_block(self):
        lines = worldsim.world_lines(self.built)
        text = "\n".join(lines)
        self.assertIn("-- the wars --", text)
        for war in self.built["wars"]:
            self.assertIn(war["name"], text)
            self.assertIn(war["herald"][:30], text)
            for polity in war["attackers"] + war["defenders"]:
                self.assertIn(self.built["lands"][polity]["name"], text)

    def test_the_polity_page_says_which_wars_it_is_in(self):
        war = self.built["wars"][0]
        polity = war["attackers"][0]
        lines = "\n".join(worldsim.politics_lines(self.built, polity))
        self.assertIn(f"{war['name']}: attacking", lines)
        defender = war["defenders"][0]
        self.assertIn(f"{war['name']}: defending",
                      "\n".join(worldsim.politics_lines(self.built,
                                                        defender)))

    def test_a_land_at_war_says_so_on_the_map_page(self):
        war = self.built["wars"][0]
        polity = war["defenders"][0]
        lines = " ".join(worldsim.land_lines(self.built, polity))
        self.assertIn(worldsim.STATE_WORDS["at-war"], lines)


class TheNewGamePrint(unittest.TestCase):
    """The three wars land where the scripted questline's armed-layer line
    used to (session 1 removed it). Driven through the real command."""

    def test_a_new_game_names_the_three_wars(self):
        import test_start
        state, out = test_start.run_new("--seed", "5", "--level", "1")
        self.assertIn("Three wars are standing", out)
        for war in state["world"]["wars"]:
            self.assertIn(war["name"], out)
        self.assertEqual(len(state["world"]["wars"]), worldsim.WARS_ROLLED)


if __name__ == "__main__":
    unittest.main()
