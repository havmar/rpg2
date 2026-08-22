"""The HISTORY PAGE contract suite (2026-08-04, THE DARK REWORK session C).

What is pinned here: the campaign record (`session.remember` -- the day
stamp, the two kinds, the duplicate guard, the per-kind trim), the four
sections of `ui/history.txt` and their 40-column fit, the named-kill and
maiming scanners that feed REMARKABLE, the TALLY's honesty about a
category's last day (the monotony window forgets on purpose; the tally
never does), the seeded SUGGESTIONS order, and the SIN rename -- the
karma keys, the display words, and the `sin` command replacing `karma`
with no alias.

    python -m unittest -v test_history.py
"""

from __future__ import annotations

import inspect
import random
import unittest

import crime
import karma
import rpg
import session
import sites


WIDTH = 40      # session.WRAP_WIDTH -- the designer's phone


def _state(day: int = 5, party=None, **extra) -> dict:
    """The minimum a history call needs: a clock, a party, the ledgers."""
    state = {"clock": rpg.Clock(day=day),
             "party": party if party is not None else [],
             "purse": rpg.Purse(silver=0),
             "rng": random.Random(1),
             "karma": karma.new_karma(),
             "crimes": crime.new_crimes(),
             "history": []}
    state.update(extra)
    return state


# --------------------------------------------------------------------------- #
# The record itself
# --------------------------------------------------------------------------- #


class TheRecord(unittest.TestCase):
    def test_a_line_is_day_stamped_and_kinded(self):
        state = _state(day=12)
        session.remember(state, "something happened")
        rec = state["history"][0]
        self.assertEqual(rec["day"], 12)
        self.assertEqual(rec["kind"], "remarkable")
        self.assertEqual(rec["line"], "something happened")

    def test_the_two_kinds_are_kept_apart(self):
        state = _state()
        session.remember(state, "a job", kind="quest", note="the epilogue")
        session.remember(state, "a deed")
        kinds = [r["kind"] for r in state["history"]]
        self.assertEqual(kinds, ["quest", "remarkable"])
        self.assertEqual(state["history"][0]["note"], "the epilogue")

    def test_an_explicit_day_overrides_the_clock(self):
        state = _state(day=3)
        session.remember(state, "earlier", day=1)
        self.assertEqual(state["history"][0]["day"], 1)

    def test_the_same_line_twice_in_a_day_is_written_once(self):
        state = _state(day=4)
        session.remember(state, "MAIMED")
        session.remember(state, "MAIMED")
        self.assertEqual(len(state["history"]), 1)

    def test_the_same_line_on_a_later_day_is_a_new_record(self):
        state = _state(day=4)
        session.remember(state, "a raid")
        state["clock"].day = 5
        session.remember(state, "a raid")
        self.assertEqual(len(state["history"]), 2)

    def test_the_guard_only_looks_at_the_last_of_its_kind(self):
        """A line repeated after something else intervened is real news,
        not a double-write."""
        state = _state(day=4)
        session.remember(state, "a raid")
        session.remember(state, "a fire")
        session.remember(state, "a raid")
        self.assertEqual(len(state["history"]), 3)

    def test_the_trim_is_per_kind(self):
        """A career of jobs must never push the write-offs and maimings
        off the page."""
        state = _state()
        session.remember(state, "the one maiming")
        for i in range(session.HISTORY_CAP + 20):
            session.remember(state, f"job {i}", kind="quest")
        quests_kept = [r for r in state["history"] if r["kind"] == "quest"]
        self.assertEqual(len(quests_kept), session.HISTORY_CAP)
        self.assertEqual(quests_kept[-1]["line"],
                         f"job {session.HISTORY_CAP + 19}")
        self.assertIn("the one maiming",
                      [r["line"] for r in state["history"]
                       if r["kind"] == "remarkable"])


# --------------------------------------------------------------------------- #
# The scanners that feed REMARKABLE
# --------------------------------------------------------------------------- #


class NamedKills(unittest.TestCase):
    """Ordinary rows are numbered off the catalog ('Cutthroat 2'); a name
    without its number is somebody the fiction cast."""

    def foe(self, name: str, dead: bool = True):
        e = sites.make_foe("cutthroat", 1, random.Random(1))
        e.name = name
        e.dead = dead
        return e

    def test_a_numbered_row_is_not_a_named_kill(self):
        self.assertEqual(session._named_dead([self.foe("Cutthroat 2")]), [])

    def test_a_bare_name_is(self):
        self.assertEqual(session._named_dead([self.foe("Vashka the Knife")]),
                         ["Vashka the Knife"])

    def test_a_survivor_is_never_a_kill(self):
        self.assertEqual(session._named_dead([self.foe("Vashka", dead=False)]),
                         [])

    def test_a_generated_roster_names_nobody(self):
        foes = [sites.make_foe(k, i, random.Random(i))
                for i, k in enumerate(("wolf", "soldier", "skeleton"), 1)]
        for f in foes:
            f.dead = True
        self.assertEqual(session._named_dead(foes), [])


class Maimings(unittest.TestCase):
    """A maiming lands deep inside `_attack`, so the record scans for it.
    The scan has to be idempotent -- it runs on every save."""

    def hero(self):
        h = rpg.Entity(name="Maud", dex=4, str_=4, sta=8, max_hp=10)
        h.wounds.append(rpg.Wound(location="arm", severity=3,
                                  name="a withered arm", permanent=True))
        return h

    def test_a_maiming_is_recorded(self):
        state = _state(day=7, party=[self.hero()])
        session._note_maimings(state)
        self.assertEqual(len(state["history"]), 1)
        self.assertIn("MAIMED", state["history"][0]["line"])
        self.assertIn("a withered arm", state["history"][0]["line"])

    def test_the_scan_is_idempotent(self):
        state = _state(day=7, party=[self.hero()])
        for _ in range(5):
            session._note_maimings(state)
        self.assertEqual(len(state["history"]), 1)

    def test_an_ordinary_wound_is_not_history(self):
        h = rpg.Entity(name="Maud", dex=4, str_=4, sta=8, max_hp=10)
        h.wounds.append(rpg.Wound(location="arm", severity=2,
                                  name="a gashed arm"))
        state = _state(party=[h])
        session._note_maimings(state)
        self.assertEqual(state["history"], [])


# --------------------------------------------------------------------------- #
# The page
# --------------------------------------------------------------------------- #


class ThePage(unittest.TestCase):
    SECTIONS = ("QUESTS DONE", "REMARKABLE", "THE TALLY OF SIN",
                "SUGGESTIONS")

    def test_every_section_is_present_on_an_empty_campaign(self):
        text = "\n".join(session.history_sheet_lines(_state()))
        for title in self.SECTIONS:
            self.assertIn(f"-- {title} --", text)

    def test_every_section_is_present_on_a_full_one(self):
        state = _state(day=9)
        session.remember(state, "[q1] The Miller's Debt (L2) -- done.",
                         kind="quest", note="the wheel turns again")
        session.remember(state, "KILLED: Vashka the Knife.")
        crime.stamp(state["crimes"], "arson", 4)
        crime.record_for(state["crimes"], "mugging")["unlocked"] = True
        text = "\n".join(session.history_sheet_lines(state))
        for title in self.SECTIONS:
            self.assertIn(f"-- {title} --", text)
        self.assertIn("day 9: KILLED: Vashka the Knife.", text)
        self.assertIn("the wheel turns again", text)
        self.assertIn("Arson: 1, last day 4", text)
        self.assertIn("Mugging", text)          # the suggestion feed

    def test_the_header_carries_the_day(self):
        lines = session.history_sheet_lines(_state(day=41))
        self.assertIn("day 41", lines[0])

    def test_an_empty_section_says_so_rather_than_vanishing(self):
        lines = session.history_sheet_lines(_state())
        body = "\n".join(lines)
        self.assertIn("no job finished yet", body)
        self.assertIn("nothing yet", body)
        self.assertIn("no crime committed yet", body)
        self.assertIn("clean; heat 0", body)

    def test_the_whole_page_fits_forty_columns(self):
        state = _state(day=9)
        session.remember(state, "[q1] The Miller's Debt (L2) -- done.",
                         kind="quest", note="the mill wheel turns again, "
                                            "and nobody asks whose coin "
                                            "oils it")
        session.remember(state, "CONQUEST: Sturford falls under the "
                                "party's flag.")
        for key in ("arson", "mugging", "burglary"):
            crime.stamp(state["crimes"], key, 4)
        for c in crime.CATEGORIES:
            crime.record_for(state["crimes"], c["key"])["unlocked"] = True
        text = session._wrap_block("\n".join(
            session.history_sheet_lines(state)))
        for line in text.splitlines():
            self.assertLessEqual(len(line), WIDTH, line)

    def test_the_page_is_ascii(self):
        state = _state()
        session.remember(state, "a deed")
        for line in session.history_sheet_lines(state):
            line.encode("ascii")

    def test_the_tally_carries_the_meter_and_the_lifetime_ledger(self):
        state = _state()
        state["karma"]["sin"] = 40
        state["karma"]["sin_total"] = 240
        state["karma"]["penance_total"] = 200
        text = "\n".join(session.history_sheet_lines(state))
        self.assertIn("lifetime sin 240 / penance 200", text)
        self.assertIn("sin 40", text)

    def test_the_suggestion_order_is_seeded_and_stable_within_a_day(self):
        state = _state(day=6, world={"seed": 3})
        for c in crime.CATEGORIES:
            crime.record_for(state["crimes"], c["key"])["unlocked"] = True
        once = session.history_sheet_lines(state)
        twice = session.history_sheet_lines(state)
        self.assertEqual(once, twice)

    def test_a_new_day_advertises_differently(self):
        """Catalogue order would sell the same two petty crimes forever."""
        seen = set()
        for day in range(1, 12):
            state = _state(day=day, world={"seed": 3})
            for c in crime.CATEGORIES:
                crime.record_for(state["crimes"], c["key"])["unlocked"] = True
            lines = session.history_sheet_lines(state)
            tail = lines[lines.index("-- SUGGESTIONS --") + 1:]
            seen.add(tuple(tail))
        self.assertGreater(len(seen), 1)

    def test_at_most_three_suggestions_are_shown(self):
        state = _state(world={"seed": 3})
        for c in crime.CATEGORIES:
            crime.record_for(state["crimes"], c["key"])["unlocked"] = True
        lines = session.history_sheet_lines(state)
        tail = lines[lines.index("-- SUGGESTIONS --") + 1:]
        self.assertLessEqual(len(tail), crime.SUGGESTIONS_SHOWN)


class ThePageLifecycle(unittest.TestCase):
    """history.txt joins party.txt and map.txt: rewritten on every save,
    committed by `sheet`."""

    def test_it_is_a_committed_ui_path(self):
        self.assertIn("ui/history.txt", session.UI_COMMIT_PATHS)
        self.assertEqual(session.HISTORY_SHEET_PATH.name, "history.txt")

    def test_the_save_rewrites_it(self):
        src = inspect.getsource(session.save)
        self.assertIn("_write_history_sheet", src)
        self.assertIn('"history"', src)

    def test_the_sheet_command_rewrites_it(self):
        self.assertIn("_write_history_sheet",
                      inspect.getsource(session.cmd_sheet))

    def test_the_load_reads_the_key(self):
        self.assertIn('"history"', inspect.getsource(session.load))

    def test_the_maiming_scan_runs_before_the_write(self):
        src = inspect.getsource(session.save)
        self.assertLess(src.index("_note_maimings"), src.index("json.dump"))


# --------------------------------------------------------------------------- #
# The tally's honesty
# --------------------------------------------------------------------------- #


class TheTally(unittest.TestCase):
    def test_a_row_per_committed_category_busiest_first(self):
        c = crime.new_crimes()
        crime.stamp(c, "arson", 1)
        for _ in range(3):
            crime.stamp(c, "mugging", 1)
        rows = crime.tally_rows(c)
        self.assertEqual([r[0] for r in rows], ["Mugging", "Arson"])
        self.assertEqual(rows[0][1], 3)

    def test_an_uncommitted_category_has_no_row(self):
        c = crime.new_crimes()
        crime.record_for(c, "arson")["unlocked"] = True
        self.assertEqual(crime.tally_rows(c), [])

    def test_the_last_day_outlives_the_monotony_window(self):
        """The day stamps age out by design (that is what makes monotony
        temporary); the tally's memory must not."""
        c = crime.new_crimes()
        crime.stamp(c, "arson", 1)
        late = 1 + crime.MONOTONY_WINDOW * 3
        # Reading the record prunes it -- the window is empty by now.
        self.assertEqual(crime.monotony_mult(crime.record_for(c, "arson"),
                                             late),
                         crime.MONOTONY_MULTS[0])
        self.assertEqual(crime.recent_days(crime.record_for(c, "arson"),
                                           late), [])
        self.assertEqual(crime.tally_rows(c)[0], ("Arson", 1, 1))

    def test_the_total_counts_every_commission(self):
        c = crime.new_crimes()
        crime.stamp(c, "arson", 1)
        crime.stamp(c, "arson", 2)
        crime.stamp(c, "mugging", 2)
        self.assertEqual(crime.total_crimes(c), 3)
        self.assertEqual(crime.total_crimes(crime.new_crimes()), 0)

    def test_the_total_and_the_rows_can_never_disagree(self):
        """A key the catalogue no longer carries is not a crime -- the
        page prints the two side by side, so they read off one source."""
        c = crime.new_crimes()
        crime.stamp(c, "arson", 1)
        crime.stamp(c, "a_retired_key", 1)
        self.assertEqual(crime.total_crimes(c),
                         sum(r[1] for r in crime.tally_rows(c)))
        self.assertEqual(crime.total_crimes(c), 1)

    def test_peek_never_writes_a_row(self):
        c = crime.new_crimes()
        for cat in crime.CATEGORIES:
            crime.peek(c, cat["key"])
        self.assertEqual(c["ledger"], {})

    def test_the_empty_record_is_never_shared(self):
        c = crime.new_crimes()
        crime.peek(c, "arson")["count"] = 99
        self.assertEqual(crime.peek(c, "mugging")["count"], 0)


class TheSuggestionFeed(unittest.TestCase):
    def test_it_lists_unlocked_and_uncommitted_only(self):
        c = crime.new_crimes()
        crime.record_for(c, "arson")["unlocked"] = True
        crime.stamp(c, "mugging", 1)        # unlocked by deed, but done
        keys = [x["key"] for x in crime.suggestions(c)]
        self.assertEqual(keys, ["arson"])

    def test_a_seeded_feed_is_reproducible(self):
        c = crime.new_crimes()
        for cat in crime.CATEGORIES:
            crime.record_for(c, cat["key"])["unlocked"] = True
        a = crime.suggestions(c, rng=random.Random(4))
        b = crime.suggestions(c, rng=random.Random(4))
        self.assertEqual([x["key"] for x in a], [x["key"] for x in b])

    def test_the_shuffle_reaches_past_the_catalogue_head(self):
        c = crime.new_crimes()
        for cat in crime.CATEGORIES:
            crime.record_for(c, cat["key"])["unlocked"] = True
        head = {cat["key"] for cat in crime.CATEGORIES[:3]}
        reached = set()
        for seed in range(20):
            reached |= {x["key"]
                        for x in crime.suggestions(c, rng=random.Random(seed))}
        self.assertTrue(reached - head)


# --------------------------------------------------------------------------- #
# The rename
# --------------------------------------------------------------------------- #


class TheSinRename(unittest.TestCase):
    """bad karma -> SIN, everywhere, with no alias and no compat branch
    (develop.md's no-backwards-compatibility rule)."""

    def test_the_karma_dict_carries_the_new_keys(self):
        k = karma.new_karma()
        self.assertIn("sin", k)
        self.assertIn("sin_total", k)
        self.assertIn("penance_total", k)

    def test_the_old_keys_are_gone(self):
        k = karma.new_karma()
        for dead in ("bad", "bad_total", "good_total"):
            self.assertNotIn(dead, k)

    def test_the_meter_says_sin(self):
        k = karma.new_karma()
        k["sin"] = 40
        line = karma.karma_line(k, 2)
        self.assertIn("sin 40", line)
        self.assertNotIn("bad karma", line)

    def test_the_award_lines_say_sin(self):
        k = karma.new_karma()
        log: list[str] = []
        karma.record_karma(k, 30, "dark", log, 2)
        self.assertIn("+30 sin", "\n".join(log))
        log = []
        karma.record_karma(k, 10, "good", log, 2)
        self.assertIn("-10 sin", "\n".join(log))

    def test_lifetime_sin_is_what_the_crime_layer_reads(self):
        k = karma.new_karma()
        k["sin_total"] = 350
        self.assertEqual(crime.lifetime_sin(k), 350)

    def test_the_command_is_sin_with_no_karma_alias(self):
        parser = session.build_parser()
        names = set(parser._subparsers._group_actions[0].choices)
        self.assertIn("sin", names)
        self.assertNotIn("karma", names)

    def test_the_command_records_both_directions(self):
        parser = session.build_parser()
        for kind in ("dark", "penance"):
            args = parser.parse_args(["sin", kind, "20", "a", "reason"])
            self.assertEqual(args.kind, kind)
            self.assertEqual(args.amount, 20)
            self.assertEqual(args.func, session.cmd_sin)

    def test_no_module_still_says_bad_karma(self):
        for mod in (karma, crime, session, rpg):
            self.assertNotIn("bad karma", inspect.getsource(mod),
                             mod.__name__)

    def test_the_crimes_sheet_is_registered(self):
        parser = session.build_parser()
        names = set(parser._subparsers._group_actions[0].choices)
        self.assertIn("crimes", names)
        self.assertTrue(callable(session.cmd_crimes))


class TheCrimeSheet(unittest.TestCase):
    """`crimes` is the `prices` pattern for the dark side: the BAND's
    worth, not one rolled mark."""

    def test_petty_quotes_its_flat_constants(self):
        line = session.take_span(crime.BY_KEY["pickpocket"], "town", 1.0)
        self.assertIn("flat", line)
        self.assertIn(f"{crime.PETTY_SIN[0]}-{crime.PETTY_SIN[1]}", line)

    def test_a_paying_crime_quotes_the_band_ends(self):
        cat = crime.BY_KEY["burglary"]
        line = session.take_span(cat, "town", 1.0)
        bands = crime.bands_here(cat, "town")
        lo = min(b["levels"][0] for b in bands)
        hi = max(b["levels"][1] for b in bands)
        self.assertIn(f"L{lo}-{hi}", line)
        g_hi, _ = crime.take_of(cat, hi, random.Random(0))
        self.assertIn(f"{g_hi}s", line)

    def test_a_takeless_crime_says_no_coin(self):
        self.assertIn("no coin",
                      session.take_span(crime.BY_KEY["puppy"], "village", 1.0))

    def test_the_multiplier_rides_the_quote(self):
        line = session.take_span(crime.BY_KEY["burglary"], "town",
                                 crime.FIRST_TIME_MULT)
        self.assertIn(f"x{crime.FIRST_TIME_MULT:g}", line)

    def test_every_row_fits_the_phone(self):
        for kind in crime.SETTLEMENT_KINDS + ("wilds",):
            for cat in crime.available(kind):
                line = session.take_span(cat, kind, 1.0)
                for word in line.split():
                    self.assertLessEqual(len(word), WIDTH, line)


if __name__ == "__main__":
    unittest.main()
