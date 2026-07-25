import tempfile
import unittest
from pathlib import Path

from quests import board_lines, generate_world, level_grade
from rpg import CombatLog
from session import UI_COMMIT_PATHS


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


if __name__ == "__main__":
    unittest.main()
