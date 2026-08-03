import tempfile
import unittest
from pathlib import Path

from quests import (board_lines, generate_world, level_grade, new_area,
                    settlements)
from rpg import CombatLog
from session import UI_COMMIT_PATHS, Clock, _area_position, map_sheet_lines


class CombatSnapshotTests(unittest.TestCase):
    def test_new_fight_replaces_and_continuation_appends_both_levels(self):
        with tempfile.TemporaryDirectory() as tmp:
            detailed = Path(tmp) / "fight-detailed.txt"
            short = Path(tmp) / "fight-short.txt"

            first = CombatLog(debug_path=detailed, player_path=short)
            first.play("detail: opening", "short: opening")
            self.assertTrue(first.flush_debug())
            self.assertTrue(first.flush_player())
            first.play("detail: tail", "short: tail")
            self.assertTrue(first.flush_debug())
            self.assertTrue(first.flush_player())

            resumed = CombatLog(debug_path=detailed, player_path=short,
                                continuing=True)
            resumed.play("detail: resumed", "short: resumed")
            resumed.flush_debug()
            resumed.flush_player()

            self.assertEqual(
                detailed.read_text(encoding="utf-8"),
                "detail: opening\ndetail: tail\ndetail: resumed\n")
            self.assertEqual(
                short.read_text(encoding="utf-8"),
                "short: opening\nshort: tail\nshort: resumed\n")

            next_fight = CombatLog(debug_path=detailed, player_path=short)
            next_fight.play("detail: next", "short: next")
            next_fight.flush_debug()
            next_fight.flush_player()

            self.assertEqual(detailed.read_text(encoding="utf-8"),
                             "detail: next\n")
            self.assertEqual(short.read_text(encoding="utf-8"),
                             "short: next\n")

    def test_sheet_commit_set_contains_both_fight_snapshots(self):
        self.assertIn("ui/fight-short.txt", UI_COMMIT_PATHS)
        self.assertIn("ui/fight-detailed.txt", UI_COMMIT_PATHS)


class ExactQuestLevelTests(unittest.TestCase):
    def test_generated_quests_have_no_blur_and_boards_show_exact_levels(self):
        world = generate_world(seed=27)

        for quest in world["quests"].values():
            self.assertNotIn("fuzz", quest)
            grade = level_grade(quest)
            self.assertNotIn("~", grade)
            if quest.get("kind") != "delivery":
                self.assertEqual(grade.strip(), f"L{quest['level']}")

        for line in board_lines(world):
            self.assertNotIn("L~", line)


class MapSheetTests(unittest.TestCase):
    def test_known_wilderness_renders_without_a_board(self):
        # Regression (2026-08-03): board_forecast ran on EVERY known area,
        # so a revealed forest/river (no SETTLEMENT_KINDS row) raised
        # KeyError and the swallowed crash froze map.txt at day 1.
        world = generate_world(seed=27)
        land = next(iter(world["lands"]))
        start = next(s for s in settlements(world) if s["land"] == land)
        new_area(world, "whitweld-forest", "Whitweld Forest", land,
                 "forest", known=True, discovered_day=3)
        new_area(world, "test-river", "the Test River", land,
                 "river", known=True, discovered_day=5)
        state = {"world": world, "clock": Clock(),
                 "position": _area_position(start),
                 "visited": [start["key"]], "accepted": []}
        state["clock"].day = 9

        lines = map_sheet_lines(state)

        self.assertIn("day 9", lines[0])
        forest = next(l for l in lines if "Whitweld Forest" in l)
        river = next(l for l in lines if "the Test River" in l)
        self.assertNotIn("job(s)", forest)   # wilderness has no board
        self.assertNotIn("job(s)", river)
        settle = next(l for l in lines
                      if start["name"] in l and l.startswith("  "))
        self.assertIn("job(s)", settle)      # settlements still forecast


if __name__ == "__main__":
    unittest.main()
