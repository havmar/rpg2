"""Contract suite for the HELL PACT's assignment ladder (2026-08-04 --
the dark rework, session A; rules.md's Karma & Heat add-on, karma.py +
session.py).

The rules this pins: the template SORT (the occult ten are what
assignments draw from; the crime fifteen are inert fodder), the per-save
DECK (shuffled once, one card per pin, band-fitting, skipped cards kept),
the PIN schedule (the odd levels, never stacked, one assignment at the
highest crossed pin), the deadline clocks, the ONE-visit Past Due shape
and its punishment budget, and the WRITE-OFF that closes an account
however the visit ends.

Run:  python -m unittest -v test_pact.py
"""

from __future__ import annotations

import random
import unittest

import karma
import quests
import rpg
import session


def _pact(seed: int = 3) -> dict:
    return karma.new_pact(random.Random(seed))


class TheTemplateSort(unittest.TestCase):
    """The 2026-08-04 sort: occult work stays a quest, crime stops being
    one. Nothing rolls from the fodder."""

    def test_ten_occult_and_fifteen_fodder(self):
        self.assertEqual(len(karma.OCCULT_TEMPLATES), 10)
        self.assertEqual(len(karma.CRIME_FODDER), 15)

    def test_the_two_lists_are_disjoint(self):
        occult = {t["title"] for t in karma.OCCULT_TEMPLATES}
        crime = {t["title"] for t in karma.CRIME_FODDER}
        self.assertFalse(occult & crime)
        self.assertEqual(len(occult), 10)

    def test_the_desecration_slot_is_filled(self):
        titles = {t["title"] for t in karma.OCCULT_TEMPLATES}
        self.assertIn("Desecrate the Shrine", titles)

    def test_every_occult_template_is_dark_and_fights_back(self):
        for t in karma.OCCULT_TEMPLATES:
            self.assertEqual(t["align"], "dark", t["title"])
            self.assertTrue(t["pool"], t["title"])
            self.assertTrue(t["sites"], t["title"])
            self.assertTrue(t["epilogue"], t["title"])

    def test_no_fodder_template_can_be_rolled(self):
        """`roll_dark_quest` draws from the occult ten only -- the crime
        fifteen are scene material for the crime actions (session B), not
        postings."""
        world = quests.generate_world(21)
        origin = quests.settlements(world)[0]
        rng = random.Random(5)
        fodder = {t["title"] for t in karma.CRIME_FODDER}
        for _ in range(60):
            q = karma.roll_dark_quest(world, origin, 3, rng, spread=(0, 0))
            self.assertNotIn(q["name"], fodder)


class TheDeck(unittest.TestCase):
    """Ten cards, shuffled once per save, one dealt per pin. Random order
    is wanted (variety over curriculum sense); an unbuildable roster is
    not."""

    def test_a_fresh_deck_holds_every_card_once(self):
        pact = _pact()
        self.assertEqual(sorted(pact["deck"]),
                         list(range(len(karma.OCCULT_TEMPLATES))))

    def test_the_shuffle_is_seeded(self):
        self.assertEqual(karma.new_pact(random.Random(9))["deck"],
                         karma.new_pact(random.Random(9))["deck"])

    def test_dealing_consumes_one_card(self):
        pact = _pact()
        before = len(pact["deck"])
        karma.deal_card(pact, 1, random.Random(1))
        self.assertEqual(len(pact["deck"]), before - 1)

    def test_the_ten_pins_deal_the_ten_cards_without_repeat(self):
        pact = _pact(4)
        rng = random.Random(4)
        dealt = [karma.deal_card(pact, pin, rng)["title"]
                 for pin in karma.TASK_PIN_LEVELS]
        self.assertEqual(len(dealt), 10)
        self.assertEqual(len(set(dealt)), 10)
        self.assertFalse(pact["deck"])

    def test_a_dealt_card_admits_the_level_when_one_can(self):
        for seed in range(12):
            pact = _pact(seed)
            rng = random.Random(seed)
            for pin in (1, 3, 5):
                tpl = karma.deal_card(pact, pin, rng)
                lo, hi = quests.template_band(tpl)
                self.assertTrue(lo <= pin <= hi,
                                f"{tpl['title']} L{lo}-{hi} dealt at {pin}")

    def test_a_skipped_card_stays_in_the_deck(self):
        """A card whose band cannot hold the pin is passed over, not
        burned -- it waits for a pin it fits."""
        pact = _pact(7)
        rng = random.Random(7)
        # Deal at a level only the widest bands admit: exactly one card
        # leaves, and the cards it passed over are still there for a pin
        # they fit.
        before = set(pact["deck"])
        tpl = karma.deal_card(pact, 13, rng)
        idx = karma.OCCULT_TEMPLATES.index(tpl)
        self.assertEqual(before - set(pact["deck"]), {idx})
        passed = [i for i in pact["deck"]
                  if quests.template_band(karma.OCCULT_TEMPLATES[i])[1] < 13]
        self.assertTrue(passed)

    def test_the_high_pins_still_deal_a_card(self):
        """Past the widest band the NEAREST card is dealt: hell always has
        something to ask for, and the assignment levels into the band."""
        pact = _pact(2)
        rng = random.Random(2)
        for pin in karma.TASK_PIN_LEVELS:
            self.assertIsNotNone(karma.deal_card(pact, pin, rng))

    def test_an_empty_deck_reshuffles(self):
        pact = _pact(1)
        rng = random.Random(1)
        for _ in range(len(karma.OCCULT_TEMPLATES)):
            karma.deal_card(pact, 3, rng)
        self.assertFalse(pact["deck"])
        self.assertIsNotNone(karma.deal_card(pact, 3, rng))
        self.assertEqual(len(pact["deck"]), len(karma.OCCULT_TEMPLATES) - 1)


class ThePins(unittest.TestCase):
    """Assignments are pinned to the PC's odd levels -- ten a career.
    Pins never queue."""

    def test_the_pins_are_the_odd_levels_to_the_cap(self):
        self.assertEqual(karma.TASK_PIN_LEVELS,
                         (1, 3, 5, 7, 9, 11, 13, 15, 17, 19))
        self.assertEqual(len(karma.TASK_PIN_LEVELS),
                         len(karma.OCCULT_TEMPLATES))

    def test_pin_one_is_due_at_level_one(self):
        self.assertEqual(session.pending_pin(_pact(), 1), 1)

    def test_nothing_is_due_between_pins(self):
        pact = _pact()
        pact["last_pin_served"] = 3
        self.assertIsNone(session.pending_pin(pact, 4))
        self.assertEqual(session.pending_pin(pact, 5), 5)

    def test_crossed_pins_never_stack(self):
        """Levelling 1 -> 6 with an account open owes ONE assignment, at
        the highest crossed pin -- not four."""
        pact = _pact()
        self.assertEqual(session.pending_pin(pact, 6), 5)
        pact["last_pin_served"] = 5
        self.assertIsNone(session.pending_pin(pact, 6))

    def test_the_ladder_ends_after_the_last_pin(self):
        pact = _pact()
        pact["last_pin_served"] = 19
        self.assertIsNone(session.pending_pin(pact, 20))
        self.assertIsNone(session.coming_pin(pact))

    def test_the_coming_pin_is_the_next_unserved(self):
        pact = _pact()
        self.assertEqual(session.coming_pin(pact), 1)
        pact["last_pin_served"] = 1
        self.assertEqual(session.coming_pin(pact), 3)


class TheClocks(unittest.TestCase):
    """A milestone job must not be missable to a road delay."""

    def test_the_grace_covers_a_pin_crossed_in_the_wilds(self):
        self.assertEqual(karma.TASK_GRACE_DAYS, 10)

    def test_the_completion_window_is_generous(self):
        self.assertEqual(karma.TASK_WINDOW_DAYS, (6, 8))

    def test_the_assignment_spread_runs_upward_only(self):
        lo, hi = karma.TASK_SPREAD
        self.assertEqual(lo, 0)
        self.assertGreater(hi, 0)


class ThePunishmentBudget(unittest.TestCase):
    """~0.5 punishment fights per level per side (plan.md). The
    escalating ladder and the interval clock are gone."""

    def test_the_collections_visit_rolls_zero_to_two_over(self):
        self.assertEqual(karma.ENFORCE_SPREAD, (0, 2))

    def test_the_law_eased_to_the_same_budget(self):
        self.assertEqual(karma.PUNISH_COOLDOWN_DAYS, 6)
        self.assertEqual(karma.PUNISH_CHANCE, 0.6)

    def test_the_dead_knobs_are_gone(self):
        for dead in ("TASK_INTERVAL_DAYS", "FIRST_TASK_LEVEL",
                     "ENFORCE_CAP_OVER", "DARK_JOBS_PER_DAY",
                     "DARK_TEMPLATES"):
            self.assertFalse(hasattr(karma, dead), dead)

    def test_the_shadow_board_is_gone(self):
        self.assertFalse(hasattr(session, "roll_dark_board"))

    def test_a_fresh_pact_carries_no_dead_bookkeeping(self):
        pact = _pact()
        self.assertNotIn("last_task_day", pact)
        self.assertNotIn("beatings", pact)
        self.assertEqual(pact["defied"], 0)
        self.assertEqual(pact["last_pin_served"], 0)


class TheWriteOff(unittest.TestCase):
    """However the one visit resolves, the account closes: the job is
    withdrawn, the ledger ticks, and hell waits for the next pin."""

    def _state(self) -> tuple[dict, dict]:
        world = quests.generate_world(31)
        origin = quests.settlements(world)[0]
        rng = random.Random(6)
        pact = _pact()
        tpl = karma.deal_card(pact, 1, rng)
        q = karma.roll_dark_quest(world, origin, 1, rng,
                                  spread=karma.TASK_SPREAD, template=tpl)
        q["hell_task"] = True
        pact["task"] = q["id"]
        pact["warned"] = True
        # The clock rides along because the write-off writes a day-stamped
        # line into the campaign history (session C's ui/history.txt).
        return {"world": world, "pact": pact, "active_quest": q["id"],
                "accepted": [q["id"]], "clock": rpg.Clock(day=12),
                "history": []}, q

    def test_the_assignment_leaves_the_world(self):
        state, q = self._state()
        label = session.withdraw_assignment(state)
        self.assertIn(q["name"], label)
        self.assertNotIn(q["id"], state["world"]["quests"])
        self.assertIsNone(state["active_quest"])
        self.assertEqual(state["accepted"], [])

    def test_the_ledger_ticks_and_the_slot_clears(self):
        state, _ = self._state()
        session.withdraw_assignment(state)
        pact = state["pact"]
        self.assertIsNone(pact["task"])
        self.assertFalse(pact["warned"])
        self.assertEqual(pact["defied"], 1)

    def test_its_geography_goes_back_to_the_land(self):
        """A withdrawn job's private Sites are released, not left to
        litter the land (the pruning contract)."""
        state, q = self._state()
        private = [sid for sid in q["sites"] if f"quest-{q['id']}-" in sid]
        session.withdraw_assignment(state)
        for sid in private:
            self.assertNotIn(sid, state["world"]["sites"])

    def test_withdrawing_nothing_is_a_no_op(self):
        state, _ = self._state()
        state["pact"]["task"] = None
        self.assertEqual(session.withdraw_assignment(state), "")
        self.assertEqual(state["pact"]["defied"], 0)

    def test_the_write_off_prints_a_scene_that_fits(self):
        state, _ = self._state()
        log: list[str] = []
        session.close_hell_account(state, log)
        self.assertTrue(log)
        for line in log:
            for word in line.split():
                self.assertLessEqual(len(word), 40, word)

    def test_the_write_off_is_a_no_op_on_a_closed_account(self):
        """Won, then fled, then lost cannot each tick the ledger: the
        second call finds nothing to write off."""
        state, _ = self._state()
        session.close_hell_account(state, [])
        session.close_hell_account(state, [])
        self.assertEqual(state["pact"]["defied"], 1)

    def test_a_closed_account_does_not_jam_the_next_pin(self):
        state, _ = self._state()
        state["pact"]["last_pin_served"] = 1
        session.withdraw_assignment(state)
        self.assertEqual(session.coming_pin(state["pact"]), 3)
        self.assertEqual(session.pending_pin(state["pact"], 4), 3)


if __name__ == "__main__":
    unittest.main()
