"""Contract suite for the GAME START and the TRAIT ROLLBACK (2026-08-05 --
plan.md's ready specs A and B, plus the designer's two amendments).

What is pinned here:

- **The start level.** `new` rolls the party's level 1-START_LEVEL_ROLL_MAX
  off the run's own rng (so `--seed` pins it) unless `--level N` fixes the
  band; the range is refused outside 1..LEVEL_CAP.
- **The player character.** Always a MAGIC USER (the gift is rolled at
  creation and nothing can grant it later), never a trait sketch, male, and
  always enough CHA to hold a companion.
- **The career start.** Above level 1 the pair arrives with what those
  levels bought: the doctrine's points spent, a job-reward weapon (a focus
  staff stays a focus), a spellbook per START_SPELL_LEVELS, a purse that is
  a share of the career's earnings, and a hell ledger stamped as though it
  had been collecting all along. Level 1 is the game that always was: trash
  arms, an empty purse, hell's tutorial pin live.
- **The trait rollback.** Traits are the COMPANION layer and only that:
  dict NPCs (givers, recipients, notables, service faces, posse leaders,
  residents) and the PC carry none; recruits and the long-time companion
  still do, mechanics included.

Run:  python -m unittest -v test_start.py
"""

from __future__ import annotations

import contextlib
import io
import random
import tempfile
import unittest
from pathlib import Path

import conquest
import karma
import people
import places
import quests
import rpg
import session
import story
import weapons


# --------------------------------------------------------------------------- #
# Driving `new` without touching the playthrough's save or its ui pages
# --------------------------------------------------------------------------- #

@contextlib.contextmanager
def sandbox():
    """Point the session's save and its three written pages at a throwaway
    directory -- a suite must never overwrite the playthrough."""
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


def run_new(*argv: str) -> tuple[dict | None, str]:
    """`new` with these flags: the loaded state (None when the command
    refused) and everything it printed, unwrapped -- the driver folds every
    line to the designer's 40 columns, so an assertion on a phrase has to
    read it flat."""
    args = session.build_parser().parse_args(["new", *argv])
    out = io.StringIO()
    with sandbox(), contextlib.redirect_stdout(out):
        args.func(args)
        state = session.load() if session.STATE_PATH.exists() else None
    return state, " ".join(out.getvalue().split())


# --------------------------------------------------------------------------- #
# The level: rolled by default, fixed on request
# --------------------------------------------------------------------------- #


class TheStartLevel(unittest.TestCase):
    def test_the_flags_exist_and_default_to_a_roll(self):
        args = session.build_parser().parse_args(["new"])
        self.assertIsNone(args.level)
        self.assertFalse(hasattr(args, "homeland"))

    def test_the_default_rolls_inside_the_band(self):
        for seed in range(40):
            rng = random.Random(seed)
            args = session.build_parser().parse_args(["new"])
            level = session.start_level(args, rng)
            self.assertGreaterEqual(level, 1)
            self.assertLessEqual(level, session.START_LEVEL_ROLL_MAX)

    def test_the_roll_moves(self):
        """A default start is not secretly always level 1."""
        rolled = set()
        for seed in range(40):
            args = session.build_parser().parse_args(["new"])
            rolled.add(session.start_level(args, random.Random(seed)))
        self.assertGreater(len(rolled), 3)

    def test_the_roll_rides_the_run_seed(self):
        args = session.build_parser().parse_args(["new"])
        first = session.start_level(args, random.Random(11))
        again = session.start_level(args, random.Random(11))
        self.assertEqual(first, again)

    def test_a_given_level_is_taken_straight(self):
        args = session.build_parser().parse_args(["new", "--level", "13"])
        self.assertEqual(session.start_level(args, random.Random(1)), 13)

    def test_the_roll_stops_below_the_cap(self):
        """Room to level is the point: a start at the cap is a diorama."""
        self.assertLess(session.START_LEVEL_ROLL_MAX, rpg.LEVEL_CAP)

    def test_the_party_starts_at_the_level_asked_for(self):
        for level in (1, 2, 7, 18, rpg.LEVEL_CAP):
            state, _ = run_new("--seed", "5", "--level", str(level))
            for h in state["party"]:
                self.assertEqual(h.level, level)

    def test_an_impossible_level_is_refused_and_writes_nothing(self):
        for bad in ("0", "-3", str(rpg.LEVEL_CAP + 1)):
            state, out = run_new("--seed", "1", "--level", bad)
            self.assertIsNone(state, bad)
            self.assertIn("--level", out)

    def test_homeland_comes_from_the_starting_settlement(self):
        for seed in range(12):
            state, _ = run_new("--seed", str(seed), "--level", "3")
            here = session.local_settlement(state)
            self.assertEqual(state["party"][0].homeland, here["land"])
            self.assertEqual(state["party"][1].homeland, here["land"])

    def test_the_level_is_printed_and_marked_when_rolled(self):
        _, out = run_new("--seed", "4")
        self.assertIn("-- rolled", out)
        _, out = run_new("--seed", "4", "--level", "6")
        self.assertIn("level 6", out)
        self.assertNotIn("rolled", out)


# --------------------------------------------------------------------------- #
# The player character
# --------------------------------------------------------------------------- #


class ThePlayerCharacter(unittest.TestCase):
    def test_the_pc_is_always_a_magic_user(self):
        for seed in range(8):
            state, _ = run_new("--seed", str(seed))
            pc = state["party"][0]
            self.assertTrue(pc.is_wizard, seed)
            self.assertIn(pc.school, rpg.SCHOOLS)
            self.assertGreaterEqual(pc.spells.get(pc.school, 0), 1)

    def test_the_gift_survives_every_homeland_the_flag_can_fix(self):
        for homeland in quests.HOMELANDS:
            e = people.make_character(random.Random(7), 4,
                                      homeland=homeland,
                                      with_traits=False, wizard=True)
            self.assertTrue(e.is_wizard, homeland)
            self.assertEqual(e.homeland, homeland)

    def test_the_gift_is_the_natural_roll_not_a_nudge(self):
        """MIND strictly above both other combat stats -- rpg.make_human's
        own test, never patched after the fact."""
        for seed in range(30):
            e = people.make_character(random.Random(seed), 1,
                                      with_traits=False, wizard=True)
            self.assertGreater(e.mind, e.dex)
            self.assertGreater(e.mind, e.str_)

    def test_a_wizard_levels_as_a_warrior_but_never_the_reverse(self):
        """The reason the PC starts with the gift: it is the only thing a
        character can never acquire. Steel is open to everyone."""
        log: list[str] = []
        wiz = people.make_character(random.Random(3), 6, with_traits=False,
                                    wizard=True)
        wiz.skill_points = 20
        wiz.weapon = rpg.WEAPONS["katana"]
        self.assertTrue(rpg.train_combat_once(wiz, log))
        self.assertTrue(rpg.train_proficiency(wiz, log))
        self.assertTrue(rpg.learn_move(wiz, "thrust", log))
        fighter = people.make_character(random.Random(3), 6)
        while fighter.is_wizard:            # a rolled companion may have it
            fighter = people.make_character(random.Random(), 6)
        fighter.skill_points = 20
        self.assertFalse(rpg.learn_spell(fighter, "fire", log))
        self.assertNotIn("fire", fighter.spells)

    def test_the_pc_carries_no_trait_sketch(self):
        for seed in range(8):
            state, _ = run_new("--seed", str(seed))
            self.assertEqual(state["party"][0].traits, {})

    def test_the_pc_is_male_flagged_and_holds_a_companion(self):
        for seed in range(6):
            state, _ = run_new("--seed", str(seed))
            pc = state["party"][0]
            self.assertEqual(pc.sex, "m")
            self.assertTrue(pc.protagonist)
            self.assertGreaterEqual(rpg.party_capacity(pc.cha), 1)


# --------------------------------------------------------------------------- #
# The companion at his side
# --------------------------------------------------------------------------- #


class TheLongTimeCompanion(unittest.TestCase):
    def test_the_ally_keeps_the_sketch_the_pc_lost(self):
        for seed in range(6):
            state, _ = run_new("--seed", str(seed))
            ally = state["party"][1]
            self.assertEqual(len(ally.traits), 3, seed)

    def test_the_ally_is_bound_and_on_a_satisfaction_track(self):
        state, _ = run_new("--seed", "2")
        pc, ally = state["party"]
        self.assertEqual(ally.bond, pc.name)
        self.assertEqual(ally.bond_kind, "old companion")
        self.assertEqual(ally.satisfaction, rpg.SATISFACTION_START)

    def test_a_recruit_still_rolls_the_full_sketch(self):
        rng = random.Random(4)
        for _ in range(10):
            self.assertEqual(len(people.make_character(rng, 3).traits), 3)


# --------------------------------------------------------------------------- #
# The career a level-N start arrives with
# --------------------------------------------------------------------------- #


class TheCareerStart(unittest.TestCase):
    def test_level_one_is_the_game_that_always_was(self):
        state, _ = run_new("--seed", "6", "--level", "1")
        pc, ally = state["party"]
        self.assertEqual(session.career_purse(1), 0)
        self.assertEqual(state["purse"].gold, people.joining_gold(ally))
        for h in (pc, ally):
            self.assertTrue(h.weapon.name in rpg.TRASH_WEAPONS
                            or h.weapon.name == "wooden staff", h.weapon.name)
            self.assertEqual(h.spells and len(h.spells) or 1, 1)

    def test_a_career_start_is_past_the_trash_arms(self):
        for seed in range(6):
            state, _ = run_new("--seed", str(seed), "--level", "9")
            for h in state["party"]:
                self.assertNotIn(h.weapon.name, rpg.TRASH_WEAPONS)

    def test_the_pc_claims_the_reward_weapon_of_his_band(self):
        """Plain chassis low, masterwork mid, generated magic up top --
        weapons.reward_weapon_for_level's own ladder."""
        for level, tier in ((3, "plain"), (7, "masterwork"),
                            (12, "magic"), (18, "legendary")):
            state, _ = run_new("--seed", "8", "--level", str(level))
            self.assertEqual(state["party"][0].weapon.tier, tier, level)

    def test_a_focus_staff_is_never_traded_for_steel_without_one(self):
        for seed in range(12):
            state, _ = run_new("--seed", str(seed), "--level", "11")
            pc = state["party"][0]
            if "staff" in pc.weapon.name:
                self.assertGreaterEqual(pc.weapon.power_bonus, 1, seed)

    def test_the_career_buys_a_spellbook_every_few_levels(self):
        for level in (1, 5, 6, 11, 16):
            state, _ = run_new("--seed", "3", "--level", str(level))
            pc = state["party"][0]
            expected = 1 + (level - 1) // session.START_SPELL_LEVELS
            self.assertEqual(len(pc.spells), expected, level)

    def test_the_books_are_learned_at_rank_one(self):
        state, _ = run_new("--seed", "3", "--level", "16")
        pc = state["party"][0]
        for name, rank in pc.spells.items():
            if name != pc.school:
                self.assertEqual(rank, 1, name)

    def test_the_purse_is_a_share_of_the_career_it_stands_on(self):
        self.assertEqual(session.career_purse(1), 0)
        last = 0
        for level in range(2, rpg.LEVEL_CAP + 1):
            purse = session.career_purse(level)
            self.assertGreater(purse, last, level)
            last = purse
        earned = sum(session.START_QUESTS_PER_LEVEL * rpg.quest_gold(l, 2)
                     for l in range(1, 11))
        self.assertEqual(session.career_purse(11),
                         round(session.START_PURSE_SHARE * earned))

    def test_the_purse_on_the_save_is_that_purse(self):
        state, _ = run_new("--seed", "5", "--level", "8")
        self.assertEqual(state["purse"].gold,
                         session.career_purse(8)
                         + people.joining_gold(state["party"][1]))

    def test_both_heroes_spent_the_doctrine_points(self):
        """develop_hero + autospend: the pools of the level are bought, so
        the player is not handed thirty banked points to page through."""
        level = 12
        state, _ = run_new("--seed", "9", "--level", str(level))
        target = min((level - 1) // rpg.POOL_GROWTH_LEVELS, rpg.POOL_BUY_CAP)
        for h in state["party"]:
            for kind in rpg.POOL_KINDS:
                self.assertEqual(h.pool_bought.get(kind, 0), target, h.name)
            self.assertLess(h.skill_points, rpg.SKILL_POINTS_PER_LEVEL * 2)

    def test_the_opening_kit_is_shared_out_at_any_level(self):
        state, _ = run_new("--seed", "5", "--level", "15")
        for h in state["party"]:
            self.assertGreaterEqual(h.items.get("healing", 0), rpg.KIT_HEALING)
            self.assertGreaterEqual(h.items.get("stamina", 0), rpg.KIT_STAMINA)


# --------------------------------------------------------------------------- #
# Hell's ledger and the world the party opens on
# --------------------------------------------------------------------------- #


class TheStartingPact(unittest.TestCase):
    def test_every_pin_below_the_start_counts_as_served(self):
        for level in range(1, rpg.LEVEL_CAP + 1):
            pact = session._start_pact(random.Random(1), level)
            expected = max((p for p in karma.TASK_PIN_LEVELS if p < level),
                           default=0)
            self.assertEqual(pact["last_pin_served"], expected, level)

    def test_the_level_one_game_still_opens_on_hells_tutorial(self):
        state, out = run_new("--seed", "2", "--level", "1")
        self.assertEqual(session.pending_pin(state["pact"], 1), 1)
        self.assertIn("first assignment finds the party", out)

    def test_a_career_start_opens_with_no_backlog(self):
        for level in (4, 6, 12, 18):
            state, _ = run_new("--seed", "2", "--level", str(level))
            self.assertIsNone(session.pending_pin(state["pact"], level))
            self.assertGreater(session.coming_pin(state["pact"]), level)

    def test_an_odd_career_start_is_pinned_at_once(self):
        for level in (5, 9, 17):
            state, _ = run_new("--seed", "2", "--level", str(level))
            self.assertEqual(session.pending_pin(state["pact"], level), level)

    def test_no_pact_still_starts_the_neutral_game(self):
        state, _ = run_new("--seed", "2", "--level", "7", "--no-pact")
        self.assertIsNone(state["pact"])


class TheOpeningGround(unittest.TestCase):
    def _hook_level(self, state: dict) -> int:
        world, here = state["world"], session.local_settlement(state)
        return min(world["quests"][qid]["level"] for qid in here["quests"]
                   if world["quests"][qid]["status"] == "open"
                   and world["quests"][qid].get("kind") != "delivery")

    def test_start_uses_the_worlds_uniform_slot_selection(self):
        state, _ = run_new("--seed", "3", "--level", "1")
        world = state["world"]
        slot = world["settlement_slots"][world["start_slot"]]
        self.assertEqual(state["position"]["area"], slot["area"])
        self.assertEqual(state["position"]["tile"], slot["tile"])

    def test_every_start_gets_work_at_the_partys_level(self):
        for level in (8, 14):
            state, _ = run_new("--seed", "3", "--level", str(level))
            self.assertEqual(self._hook_level(state), level)

    def test_the_hook_names_a_job_at_the_partys_own_level(self):
        _, out = run_new("--seed", "3", "--level", "10")
        self.assertIn("OPENING HOOK", out)

    def test_the_war_line_stops_promising_level_two_to_a_career_party(self):
        _, low = run_new("--seed", "3", "--level", "1")
        self.assertIn(f"level-{story.WAVE_LEVELS[0]} party", low)
        _, high = run_new("--seed", "3", "--level", "12")
        self.assertIn("already due", high)


# --------------------------------------------------------------------------- #
# Spec B -- the trait rollback
# --------------------------------------------------------------------------- #


class TheTraitRollback(unittest.TestCase):
    def test_a_cast_npc_carries_no_sketch(self):
        rng = random.Random(2)
        npc = people.make_npc(rng, "firascir", "chief constable")
        self.assertNotIn("traits", npc)
        self.assertEqual(set(npc),
                         {"name", "homeland", "sex", "age", "role"})

    def test_a_cast_npc_records_a_level_when_the_caller_knows_one(self):
        rng = random.Random(2)
        self.assertEqual(people.make_npc(rng, "tergal", "boss", level=7)["level"],
                         7)
        self.assertNotIn("level", people.make_npc(rng, "tergal", "boss"))

    def test_the_npc_line_is_name_role_homeland_sex_age(self):
        npc = people.make_npc(random.Random(5), "mortellaria", "sage")
        line = people.npc_line(npc)
        self.assertEqual(line, f"{npc['name']} (sage) -- mortellaria "
                               f"{npc['sex']}, "
                               f"age {npc['age']}")

    def test_no_face_in_a_generated_world_carries_traits(self):
        world = quests.generate_world(12)
        faces = list(world["npcs"])
        for quest in world["quests"].values():
            faces += [f for f in (quest.get("giver"), quest.get("recipient"))
                      if f]
        self.assertGreater(len(faces), 50)
        for face in faces:
            self.assertNotIn("traits", face, face["name"])

    def test_the_quest_readout_dumps_no_traits(self):
        world = quests.generate_world(12)
        for quest in list(world["quests"].values())[:20]:
            text = "\n".join(quests.quest_detail_lines(world, quest, day=0))
            self.assertNotIn("temperament", text)
            self.assertNotIn("dress:", text)

    def test_the_posse_leaders_carry_no_sketch(self):
        """The law's and hell's named faces -- both builders return
        (kinds, skins, leader, label)."""
        rng = random.Random(6)
        for build in (karma.build_posse, karma.build_hell_posse):
            _kinds, _skins, leader, _label = build(5, "firascir", rng)
            self.assertNotIn("traits", leader)
            self.assertEqual(leader["level"], 5)

    def test_the_conquest_defender_carries_no_sketch(self):
        world = quests.generate_world(13)
        settlement = quests.settlements(world)[0]
        quest = conquest.build_conquest_quest(world, settlement,
                                              random.Random(2))
        boss = world["sites"][quest["sites"][0]]["boss"]
        self.assertIn(",", boss["display"])     # "Name, the role"
        for npc in world["npcs"]:
            self.assertNotIn("traits", npc)

    def test_a_house_resident_carries_no_sketch(self):
        world = quests.generate_world(14)
        area = next(a for a in world["areas"].values()
                    if a["kind"] == "settlement")
        site, _room = places.materialize_house(world, area)
        resident = next(n for n in world["npcs"]
                        if n["id"] == site["occupants"][0])
        self.assertEqual(resident["post"], "resident")
        self.assertNotIn("traits", resident)

    def test_the_legendary_smiths_carry_no_sketch(self):
        world = quests.generate_world(15)
        for smith in weapons.roll_smiths(world, random.Random(3)):
            self.assertNotIn("traits", smith)

    def test_traits_stay_mechanical_where_they_are_read(self):
        """The rollback is a SCOPE change, not a deletion: a companion's
        sketch still moves numbers and still prices a hire."""
        rng = random.Random(1)
        for _ in range(200):
            e = people.make_character(rng, 2)
            if rpg.has_trait(e, "armored"):
                self.assertEqual(e.def_bonus, people.ARMORED_DEF_BONUS)
            if rpg.has_trait(e, "wealthy"):
                self.assertEqual(people.joining_gold(e),
                                 people.TRAIT_GOLD["wealthy"])

    def test_a_trait_less_roll_takes_no_trait_shifts(self):
        rng = random.Random(1)
        for _ in range(50):
            e = people.make_character(rng, 1, with_traits=False)
            self.assertEqual(e.traits, {})
            self.assertEqual(e.def_bonus, 0)
            self.assertEqual(people.joining_gold(e), 0)

    def test_the_reward_ladder_can_be_asked_for_one_chassis(self):
        """The career start's hook into weapons.py (a caster's staff)."""
        rng = random.Random(2)
        for level in (2, 7, 12, 19):
            w = weapons.reward_weapon_for_level(level, rng,
                                                chassis="wooden staff")
            self.assertIn("staff", w.name)
            self.assertGreaterEqual(w.power_bonus, 1)


if __name__ == "__main__":
    unittest.main()
