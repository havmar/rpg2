"""The CRIME contract suite (2026-08-04, THE DARK REWORK session B).

What is pinned here: the catalogue's shape and the fodder it recycles;
the mark bands and their place gating; the casing guarantee (a seeded
mark is stable per settlement/day/category and a new day rolls a new
one); the take formulas including the fence rate and petty's flatness;
monotony's temporary window and the first-time bonus; the unlock ledger
(grants come from assignments and lifetime sin, by-deed unlocks never
eat a grant); the news cycle's heat floor; and the 40-column fit of
every authored string the player reads.

    python -m unittest -v test_crime.py
"""

from __future__ import annotations

import random
import unittest

import crime
import karma
import quests
import rpg


WIDTH = 40      # session.WRAP_WIDTH -- the designer's phone


class Catalogue(unittest.TestCase):
    def test_every_category_is_well_formed(self):
        for c in crime.CATEGORIES:
            with self.subTest(c["key"]):
                self.assertIn(c["shape"], crime.SHAPES)
                self.assertTrue(c["bands"])
                for b in c["bands"]:
                    self.assertIn(b, crime.BANDS_BY_KEY)
                self.assertIn(c["pay"], ("coin", "goods", None))
                self.assertTrue(c["line"] and c["hint"])
                for kind in crime.where_of(c):
                    self.assertIn(kind, crime.SETTLEMENT_KINDS + ("wilds",))

    def test_keys_and_names_are_unique(self):
        keys = [c["key"] for c in crime.CATEGORIES]
        names = [c["name"] for c in crime.CATEGORIES]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(len(names), len(set(names)))

    def test_all_three_shapes_are_populated(self):
        for shape in crime.SHAPES:
            self.assertTrue([c for c in crime.CATEGORIES
                             if c["shape"] == shape], shape)

    def test_only_petty_and_deeds_carry_a_check(self):
        # Force is the shape that never rolls: it goes through the
        # protection to get at the take, and that is the whole of it.
        for c in crime.CATEGORIES:
            if c["shape"] == "force":
                self.assertIsNone(c["stat"], c["key"])
                self.assertIsNone(c["dc"], c["key"])
            elif c["shape"] == "deed":
                self.assertIsNotNone(c["stat"], c["key"])
                self.assertIn(c["dc"], (9, 10, 11), c["key"])

    def test_every_named_fodder_template_exists(self):
        # The retired fifteen are the scene material: a category that
        # names one must actually find it, or its protection quietly
        # falls back to the generic watch.
        titles = {t["title"] for t in karma.CRIME_FODDER}
        for c in crime.CATEGORIES:
            if c.get("fodder"):
                self.assertIn(c["fodder"], titles, c["key"])

    def test_the_fodder_is_still_rolled_by_nothing(self):
        # Session A's contract, restated from this side: crime dresses
        # itself in the retired templates, it does not post them.
        occult = {t["title"] for t in karma.OCCULT_TEMPLATES}
        fodder = {t["title"] for t in karma.CRIME_FODDER}
        self.assertFalse(occult & fodder)

    def test_lookup_by_key_and_by_name(self):
        self.assertIs(crime.category("burglary"), crime.BY_KEY["burglary"])
        self.assertIs(crime.category("Vault Heist"), crime.BY_KEY["heist"])
        self.assertIsNone(crime.category("embezzlement"))

    def test_protection_dress_falls_back_to_the_watch(self):
        pool, skins = crime.protection_dress({"fodder": None})
        self.assertEqual(pool, crime.GUARD_POOL)
        self.assertEqual(skins, crime.GUARD_SKINS)


class Bands(unittest.TestCase):
    def test_bands_climb_without_gaps(self):
        levels = [b["levels"] for b in crime.MARK_BANDS]
        self.assertEqual(levels[0][0], 1)
        self.assertEqual(levels[-1][1], rpg.LEVEL_CAP)
        for (lo, hi), (nlo, _) in zip(levels, levels[1:]):
            self.assertLess(lo, hi)
            # Contiguous or overlapping: no level between 1 and the cap
            # falls into no band at all.
            self.assertLessEqual(nlo, hi + 1)

    def test_a_village_holds_nobody_worth_a_heist(self):
        heist = crime.BY_KEY["heist"]
        self.assertEqual(crime.bands_here(heist, "village"), [])
        self.assertTrue(crime.bands_here(heist, "capital"))

    def test_road_work_stays_on_the_road(self):
        for key in ("highway", "caravan", "taxcart"):
            cat = crime.BY_KEY[key]
            self.assertEqual(crime.where_of(cat), ("wilds",), key)
            for kind in crime.SETTLEMENT_KINDS:
                self.assertEqual(crime.bands_here(cat, kind), [], key)

    def test_the_default_is_settlements_only(self):
        self.assertEqual(crime.where_of(crime.BY_KEY["mugging"]),
                         crime.SETTLEMENT_KINDS)

    def test_something_is_available_everywhere(self):
        for kind in crime.SETTLEMENT_KINDS + ("wilds",):
            self.assertTrue(crime.available(kind), kind)

    def test_a_category_can_name_its_own_faces(self):
        puppy = crime.BY_KEY["puppy"]
        self.assertNotIn("a farmhand", crime.roles_of(puppy, "commoner"))
        # ...and a category with no override takes the band's list.
        self.assertEqual(crime.roles_of(crime.BY_KEY["vandalism"],
                                        "commoner"),
                         tuple(crime.band_of("commoner")["roles"]))


class TheMark(unittest.TestCase):
    def test_casing_is_honest_same_day_and_stale_tomorrow(self):
        cat = crime.BY_KEY["burglary"]
        a = crime.roll_mark(cat, 11, "town-a", "town", 5)
        b = crime.roll_mark(cat, 11, "town-a", "town", 5)
        self.assertEqual(a, b)          # `case` then `crime` -- same mark
        # ...and sleeping on it rolls a new one: over a fortnight the
        # town does not keep offering one identical mark.
        week = {(crime.roll_mark(cat, 11, "town-a", "town", d)["role"],
                 crime.roll_mark(cat, 11, "town-a", "town", d)["level"])
                for d in range(1, 15)}
        self.assertGreater(len(week), 1)

    def test_the_mark_differs_between_settlements(self):
        cat = crime.BY_KEY["mugging"]
        seen = {(crime.roll_mark(cat, 3, f"town-{i}", "town", 2)["role"],
                 crime.roll_mark(cat, 3, f"town-{i}", "town", 2)["level"])
                for i in range(12)}
        self.assertGreater(len(seen), 1)

    def test_no_mark_where_the_crime_does_not_belong(self):
        self.assertIsNone(crime.roll_mark(crime.BY_KEY["caravan"],
                                          1, "v", "village", 1))

    def test_the_level_stays_inside_its_band(self):
        for cat in crime.CATEGORIES:
            for kind in crime.SETTLEMENT_KINDS + ("wilds",):
                for day in range(1, 8):
                    mark = crime.roll_mark(cat, 9, "x", kind, day)
                    if mark is None:
                        continue
                    lo, hi = crime.band_of(mark["band"])["levels"]
                    self.assertTrue(lo <= mark["level"] <= hi,
                                    (cat["key"], kind, mark))

    def test_petty_never_has_a_roster_and_everything_else_does(self):
        for cat in crime.CATEGORIES:
            for kind in crime.SETTLEMENT_KINDS + ("wilds",):
                mark = crime.roll_mark(cat, 4, "y", kind, 3)
                if mark is None:
                    continue
                if cat["shape"] == "petty":
                    self.assertEqual(mark["kinds"], [], cat["key"])
                else:
                    self.assertTrue(mark["kinds"], cat["key"])

    def test_an_npc_mark_takes_the_dm_s_level_and_is_stable(self):
        cat = crime.BY_KEY["blackmail"]
        a = crime.npc_mark(cat, 2, "Petra", 6, 4)
        b = crime.npc_mark(cat, 2, "Petra", 6, 4)
        self.assertEqual(a, b)
        self.assertEqual(a["level"], 6)
        self.assertEqual(a["role"], "Petra")
        self.assertIsNone(a["band"])
        # A different victim is a different mark: same level and band,
        # its own roll.
        other = crime.npc_mark(cat, 2, "Otho", 6, 4)
        self.assertEqual(other["role"], "Otho")
        self.assertEqual(other["level"], 6)


class TheTake(unittest.TestCase):
    rng = random.Random(0)

    def test_a_coin_crime_pays_the_formula(self):
        cat = crime.BY_KEY["heist"]        # coin, mult 1.25
        gold, xp = crime.take_of(cat, 8, random.Random(1))
        self.assertEqual(gold, round(crime.CRIME_GOLD_PER_LEVEL * 8 * 1.25))
        self.assertEqual(xp, round(crime.CRIME_XP_PER_LEVEL * 8 * 1.25))

    def test_goods_are_fenced(self):
        goods = crime.BY_KEY["burglary"]     # goods, mult 1.0
        self.assertEqual(goods["pay"], "goods")
        g_gold, g_xp = crime.take_of(goods, 6, random.Random(1))
        self.assertEqual(
            g_gold,
            round(crime.CRIME_GOLD_PER_LEVEL * 6 * goods["mult"]
                  * crime.FENCE_RATE))
        # The FENCE takes its half out of the coin only -- the sin is
        # what the deed was, not what the fence paid for it.
        self.assertEqual(g_xp,
                         round(crime.CRIME_XP_PER_LEVEL * 6
                               * goods["mult"]))

    def test_the_lump_is_half_an_at_level_quest(self):
        # The design sentence: a crime is ONE SCENE, so it pays half a job.
        for level in (1, 5, 10, 20):
            _, xp = crime.take_of(crime.BY_KEY["mugging"], level,
                                  random.Random(2))
            quoted = rpg.quest_xp_total(level, 2)
            self.assertLess(xp, quoted)
            self.assertGreater(xp * 4, quoted)

    def test_petty_is_flat_and_never_scales_with_the_mark(self):
        cat = crime.BY_KEY["pickpocket"]
        for level in (1, 2, 4):
            gold, xp = crime.take_of(cat, level, random.Random(3))
            self.assertTrue(crime.PETTY_SIN[0] <= xp <= crime.PETTY_SIN[1])
            self.assertTrue(crime.PETTY_GOLD[0] <= gold
                            <= crime.PETTY_GOLD[1])

    def test_a_no_pay_crime_pays_no_coin(self):
        for key in ("puppy", "vandalism"):
            gold, xp = crime.take_of(crime.BY_KEY[key], 2, random.Random(4))
            self.assertEqual(gold, 0, key)
            self.assertGreater(xp, 0, key)      # ...but it is still sin

    def test_farming_down_is_self_defeating(self):
        # The doctrine in one assertion: the reward scales off the mark,
        # so robbing commoners forever pays commoner money forever.
        cat = crime.BY_KEY["mugging"]
        low, _ = crime.take_of(cat, 1, random.Random(5))
        high, _ = crime.take_of(cat, 7, random.Random(5))
        self.assertLess(low, high)


class Monotony(unittest.TestCase):
    def ledger(self):
        return crime.new_crimes()

    def test_the_first_ever_commission_pays_the_creativity_bonus(self):
        c = self.ledger()
        rec = crime.record_for(c, "arson")
        self.assertEqual(crime.sin_mult(rec, 1), crime.FIRST_TIME_MULT)

    def test_the_window_bites_then_ages_out(self):
        c = self.ledger()
        crime.stamp(c, "arson", 1)      # the first-time one
        rec = crime.record_for(c, "arson")
        self.assertEqual(crime.sin_mult(rec, 1), crime.MONOTONY_MULTS[1])
        crime.stamp(c, "arson", 1)
        self.assertEqual(crime.sin_mult(rec, 1), crime.MONOTONY_MULTS[2])
        crime.stamp(c, "arson", 1)
        self.assertEqual(crime.sin_mult(rec, 1), crime.MONOTONY_MULTS[3])
        # ...and the stamps age out: hell gets bored, it does not hold a
        # grudge.
        self.assertEqual(crime.sin_mult(rec, 1 + crime.MONOTONY_WINDOW),
                         crime.MONOTONY_MULTS[0])

    def test_the_floor_holds(self):
        c = self.ledger()
        for _ in range(20):
            crime.stamp(c, "arson", 2)
        self.assertEqual(crime.sin_mult(crime.record_for(c, "arson"), 2),
                         crime.MONOTONY_FLOOR)

    def test_alternating_two_crimes_does_not_reset_either(self):
        # Decision 7, stated as a test: each category owns its own window,
        # so a two-crime loop stales and a portfolio does not.
        c = self.ledger()
        for _ in range(3):
            crime.stamp(c, "arson", 1)
            crime.stamp(c, "mugging", 1)
        self.assertEqual(crime.sin_mult(crime.record_for(c, "arson"), 1),
                         crime.MONOTONY_MULTS[3])
        self.assertEqual(crime.sin_mult(crime.record_for(c, "raid"), 1),
                         crime.FIRST_TIME_MULT)

    def test_stamping_unlocks_by_deed(self):
        c = self.ledger()
        crime.stamp(c, "kidnap", 4)
        self.assertTrue(crime.peek(c, "kidnap")["unlocked"])
        self.assertEqual(c["grants"], 0)     # ...and eats no grant


class Unlocks(unittest.TestCase):
    def state(self, done=0, sin=0):
        k = karma.new_karma()
        k["bad_total"] = sin
        return crime.new_crimes(), k, {"done": done}

    def test_nothing_is_advertised_before_the_first_assignment(self):
        c, k, pact = self.state(done=0, sin=5000)
        self.assertEqual(crime.unlocks_due(k, pact), 0)
        self.assertEqual(crime.refresh_unlocks(c, k, pact, random.Random(1)),
                         [])

    def test_a_pactless_save_is_never_advertised_to(self):
        c, k, _ = self.state(sin=5000)
        self.assertEqual(crime.unlocks_due(k, None), 0)

    def test_the_first_completed_assignment_buys_one(self):
        c, k, pact = self.state(done=1, sin=0)
        fresh = crime.refresh_unlocks(c, k, pact, random.Random(1))
        self.assertEqual(len(fresh), 1)
        self.assertEqual(c["grants"], 1)

    def test_then_one_per_step_of_lifetime_sin(self):
        c, k, pact = self.state(done=1, sin=crime.CRIME_UNLOCK_STEP * 3)
        self.assertEqual(crime.unlocks_due(k, pact), 4)
        crime.refresh_unlocks(c, k, pact, random.Random(2))
        self.assertEqual(c["grants"], 4)

    def test_refreshing_is_idempotent(self):
        c, k, pact = self.state(done=1, sin=crime.CRIME_UNLOCK_STEP * 2)
        crime.refresh_unlocks(c, k, pact, random.Random(3))
        self.assertEqual(crime.refresh_unlocks(c, k, pact,
                                               random.Random(3)), [])

    def test_the_full_catalogue_lands_near_the_designer_s_target(self):
        # The derivation in plan.md: ~4,750 lifetime sin for all of them.
        need = (len(crime.CATEGORIES) - 1) * crime.CRIME_UNLOCK_STEP
        self.assertTrue(4000 <= need <= 5500, need)

    def test_a_by_deed_unlock_does_not_consume_a_grant(self):
        c, k, pact = self.state(done=1, sin=0)
        crime.stamp(c, "puppy", 1)      # committed while "locked"
        fresh = crime.refresh_unlocks(c, k, pact, random.Random(4))
        self.assertEqual(len(fresh), 1)
        self.assertNotEqual(fresh[0]["key"], "puppy")

    def test_the_feed_shows_only_unlocked_uncommitted_work(self):
        c, k, pact = self.state(done=1, sin=crime.CRIME_UNLOCK_STEP * 5)
        crime.refresh_unlocks(c, k, pact, random.Random(5))
        feed = crime.suggestions(c)
        self.assertEqual(len(feed), crime.SUGGESTIONS_SHOWN)
        for cat in feed:
            rec = crime.peek(c, cat["key"])
            self.assertTrue(rec["unlocked"])
            self.assertEqual(rec["count"], 0)
        # A committed category leaves the feed.
        crime.stamp(c, feed[0]["key"], 1)
        self.assertNotIn(feed[0]["key"],
                         [x["key"] for x in crime.suggestions(c)])

    def test_peek_never_writes(self):
        c = crime.new_crimes()
        crime.peek(c, "arson")
        self.assertEqual(c["ledger"], {})

    def test_the_tally_reads_busiest_first(self):
        c = crime.new_crimes()
        crime.stamp(c, "arson", 1)
        crime.stamp(c, "arson", 2)
        crime.stamp(c, "mugging", 3)
        rows = crime.tally_rows(c)
        self.assertEqual([r[0] for r in rows],
                         [crime.BY_KEY["arson"]["name"],
                          crime.BY_KEY["mugging"]["name"]])
        self.assertEqual(rows[0][1:], (2, 2))


class TheNewsCycle(unittest.TestCase):
    def test_a_big_score_floors_heat_through_any_penance(self):
        k = karma.new_karma()
        log: list[str] = []
        step = karma.heat_step(3)
        karma.record_karma(k, step, "dark", log, 3, day=10)
        self.assertEqual(k["hot_until"], 10 + karma.NEWS_DAYS)
        # Buy every point of it off the same day...
        karma.record_karma(k, step, "good", log, 3, day=10)
        self.assertEqual(k["bad"], 0)
        # ...and the town still talks.
        self.assertEqual(karma.heat(k, 3, day=10), 1)
        self.assertEqual(karma.heat(k, 3, day=10 + karma.NEWS_DAYS - 1), 1)
        self.assertEqual(karma.heat(k, 3, day=10 + karma.NEWS_DAYS), 0)

    def test_petty_sin_stays_dodgeable_on_purpose(self):
        k = karma.new_karma()
        log: list[str] = []
        for day in range(6):
            karma.record_karma(k, karma.heat_step(3) - 1, "dark", log, 3,
                               day=day)
            karma.record_karma(k, karma.heat_step(3), "good", log, 3,
                               day=day)
        self.assertEqual(k["hot_until"], 0)
        self.assertEqual(karma.heat(k, 3, day=6), 0)

    def test_the_news_never_lowers_real_heat(self):
        k = karma.new_karma()
        k["bad"] = karma.heat_step(2) * 3
        k["hot_until"] = 99
        self.assertEqual(karma.heat(k, 2, day=1), karma.HEAT_CAP)

    def test_a_dayless_read_is_the_plain_meter(self):
        # Displays with no calendar to hand must not invent a floor.
        k = karma.new_karma()
        k["hot_until"] = 99
        self.assertEqual(karma.heat(k, 3), 0)

    def test_an_undated_award_books_the_sin_without_the_stamp(self):
        k = karma.new_karma()
        log: list[str] = []
        karma.record_karma(k, karma.heat_step(4) * 2, "dark", log, 4)
        self.assertEqual(k["bad_total"], karma.heat_step(4) * 2)
        self.assertEqual(k["hot_until"], 0)

    def test_a_fresh_karma_dict_carries_the_key(self):
        self.assertEqual(karma.new_karma()["hot_until"], 0)


class Display(unittest.TestCase):
    def fits(self, text: str) -> bool:
        # The played surfaces hard-wrap at 40; what is checked here is
        # that no single authored FRAGMENT is unwrappable on its own.
        return all(len(w) <= WIDTH for w in text.split())

    def test_every_authored_string_wraps(self):
        for c in crime.CATEGORIES:
            for field in ("name", "line", "hint"):
                self.assertTrue(self.fits(c[field]), (c["key"], field))

    def test_every_mark_face_wraps(self):
        for b in crime.MARK_BANDS:
            for role in b["roles"]:
                self.assertTrue(self.fits(role), role)
        for c in crime.CATEGORIES:
            for roles in (c.get("roles") or {}).values():
                for role in roles:
                    self.assertTrue(self.fits(role), role)

    def test_the_check_line_says_which_shape_it_is(self):
        self.assertIn("no check", crime.check_line(crime.BY_KEY["mugging"]))
        self.assertIn("DC", crime.check_line(crime.BY_KEY["burglary"]))

    def test_the_roster_hint_reads_the_real_roster(self):
        mark = crime.roll_mark(crime.BY_KEY["racket"], 6, "t", "town", 2)
        hint = crime.roster_hint(mark)
        self.assertTrue(hint)
        self.assertNotEqual(hint, "no protection")
        for kind in set(mark["kinds"]):
            self.assertIn(mark["skins"].get(kind, quests.FOES[kind].display),
                          hint)


class SessionWiring(unittest.TestCase):
    """The driver's side: the commands exist, the encounter machinery
    carries a crime, and the save round-trips the ledger."""

    def test_the_commands_are_registered(self):
        import session
        self.assertTrue(callable(session.cmd_case))
        self.assertTrue(callable(session.cmd_crime))

    def test_the_take_rides_the_pending_fight(self):
        import session
        rec = {"key": "arson", "name": "Arson", "role": "a miller",
               "level": 3, "gold": 60, "xp": 150, "note": ""}
        pending = {"foes": [], "fired": set(), "round": 2, "crossings": [],
                   "xp": 10, "site": None, "room": None, "quest": None,
                   "crime": rec, "dead_before": [], "field": 0,
                   "align": "dark", "mercy": None, "pause_kind": "normal",
                   "normal_pause_used": True}
        doc = session._pending_to_dict(pending, [])
        self.assertEqual(doc["crime"], rec)
        self.assertEqual(session._pending_from_dict(doc, [])["crime"], rec)

    def test_the_ledger_is_a_save_key(self):
        import inspect
        import session
        src = inspect.getsource(session.save)
        self.assertIn('"crimes"', src)


if __name__ == "__main__":
    unittest.main()
