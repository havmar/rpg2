"""Contract suite for the WOUND system (2026-07-26, the attrition rework's
slice 3b -- rules.md's Wounds & Recovery add-on; reworked 2026-09-03 into
ONE wound, not a catalogue).

What this pins is the load-bearing half: the accrual table (what each tier
leaves and what the graze and the wound tiers deliberately do not), the
one-record rule (a second blow deepens, the deeper blow names), the maiming
rule and its one condition, the HP ceiling and the half-pool floor that keeps
it from being a death spiral, the stat fold and its idempotence, the
asymmetry (heroes record, foes never do), every rung of the treatment ladder
and what each one can and cannot reach, the bleed re-derivation, the morale
drain, and the save round-trip.

Run:  python -m unittest -v test_wounds.py
"""

import random
import unittest

import rpg
import sites
import session

GRIEVOUS = rpg.WOUND_TIER_SEVERITY["grievous"]
CRIPPLING = rpg.WOUND_TIER_SEVERITY["crippling blow"]
G_GRIEVOUS = rpg.WOUND_TIER_GRADE["grievous"]
G_CRIPPLING = rpg.WOUND_TIER_GRADE["crippling blow"]


def _hero(name: str = "Test", hp: int = 20, **kw) -> rpg.Entity:
    """A plain body that KEEPS records -- the played-party side."""
    kw.setdefault("records_wounds", True)
    return rpg.Entity(name=name, dex=4, str_=4, sta=8, max_hp=hp, **kw)


def _foe(name: str = "Foe", hp: int = 20, **kw) -> rpg.Entity:
    """...and one that does not, which is every foe in the catalog."""
    return rpg.Entity(name=name, dex=4, str_=4, sta=8, max_hp=hp, **kw)


class TheLocationTable(unittest.TestCase):
    """The vital fraction is a PRIMARY LETHALITY LEVER -- it decides how often
    a crippling blow reads as death rather than as a maiming, so it is pinned
    here and benched, never eyeballed."""

    def test_weights_are_a_closed_table(self):
        self.assertEqual(set(rpg.WOUND_LOCATION_WEIGHTS),
                         set(rpg.WOUND_VITALS) | set(rpg.WOUND_LIMBS))

    def test_vitals_are_about_fifteen_percent_of_located_hits(self):
        total = sum(rpg.WOUND_LOCATION_WEIGHTS.values())
        vital = sum(rpg.WOUND_LOCATION_WEIGHTS[k] for k in rpg.WOUND_VITALS)
        self.assertEqual(total, 100)
        self.assertEqual(vital, 15)

    def test_the_roll_only_ever_returns_a_table_key(self):
        rng = random.Random(1)
        for _ in range(400):
            self.assertIn(rpg.roll_wound_location(rng),
                          rpg.WOUND_LOCATION_WEIGHTS)

    def test_every_location_has_a_name_at_every_recording_grade(self):
        for loc in rpg.WOUND_LOCATION_WEIGHTS:
            for grade in rpg.WOUND_TIER_GRADE.values():
                self.assertTrue(rpg.wound_name(loc, grade), (loc, grade))
        self.assertEqual(rpg.wound_name("", rpg.WOUND_DOWN_GRADE),
                         "badly beaten")

    def test_every_limb_has_a_maiming_name(self):
        for loc in rpg.WOUND_LIMBS:
            self.assertTrue(rpg.wound_name(loc, G_CRIPPLING, permanent=True))

    def test_no_wound_lands_on_the_back(self):
        # The designer's 2026-09-03 note: a fighter faces the foe.
        for table in rpg.WOUND_NAMES.values():
            for name in table.values():
                self.assertNotIn("back", name.split())


class TheAccrualTable(unittest.TestCase):
    """graze nothing / wound nothing / grievous 3 at grade 2 / crippling 4 at
    grade 3 (2026-09-03: the slow channel starts at grievous)."""

    def test_a_graze_records_nothing(self):
        h = _hero()
        rpg.record_hit_wound(h, "graze", random.Random(1))
        self.assertEqual(h.wounds, [])

    def test_a_solid_wound_records_nothing_either(self):
        # The 2-HP tier is blood loss. Recording it was what filed two or
        # three cuts a fight.
        h = _hero()
        for _ in range(10):
            rpg.record_hit_wound(h, "wound", random.Random(1))
        self.assertEqual(h.wounds, [])

    def test_the_tiers_record_their_severities_and_grades(self):
        for tier, sev, grade in (("grievous", GRIEVOUS, G_GRIEVOUS),
                                 ("crippling blow", CRIPPLING, G_CRIPPLING)):
            h = _hero()
            rpg.record_hit_wound(h, tier, random.Random(4))
            self.assertEqual(h.wound_load, sev, tier)
            self.assertEqual(h.wounds[0].grade, grade, tier)

    def test_a_deflection_records_nothing(self):
        h = _hero()
        rpg.record_hit_wound(h, "deflected", random.Random(1))
        self.assertEqual(h.wounds, [])

    def test_going_down_records_an_unlocated_beating(self):
        h = _hero()
        rpg.go_down(h)
        self.assertTrue(h.down)
        self.assertEqual([w.location for w in h.wounds], [""])
        self.assertEqual(h.wounds[0].name, "badly beaten")
        self.assertEqual(h.wound_load, rpg.WOUND_DOWN_SEVERITY)


class TheOneRecord(unittest.TestCase):
    """A body carries ONE wound. Further blows deepen it; the worst blow names
    it; the name never steps down as the load knits."""

    def test_a_second_blow_deepens_the_one_record(self):
        h = _hero()
        rpg.add_wound(h, "arm", GRIEVOUS, G_GRIEVOUS)
        rpg.add_wound(h, "leg", GRIEVOUS, G_GRIEVOUS)
        self.assertEqual(len(h.wounds), 1)
        self.assertEqual(h.wounds[0].severity, 2 * GRIEVOUS)

    def test_an_equal_blow_leaves_the_name_where_it_was(self):
        h = _hero()
        rpg.add_wound(h, "arm", GRIEVOUS, G_GRIEVOUS)
        rpg.add_wound(h, "leg", GRIEVOUS, G_GRIEVOUS)
        self.assertEqual(h.wounds[0].location, "arm")
        self.assertEqual(h.wounds[0].name, rpg.WOUND_NAMES["arm"][G_GRIEVOUS])
        self.assertEqual(h.wounds[0].penalty, {"str": -1})

    def test_the_deeper_blow_takes_the_record_over(self):
        h = _hero()
        base_str, base_dex = h.str_, h.dex
        rpg.add_wound(h, "arm", GRIEVOUS, G_GRIEVOUS)
        rpg.add_wound(h, "leg", CRIPPLING, G_CRIPPLING)
        w, = h.wounds
        self.assertEqual((w.location, w.grade), ("leg", G_CRIPPLING))
        self.assertEqual(w.name, "a broken leg")
        self.assertEqual(w.severity, min(GRIEVOUS + CRIPPLING,
                                         rpg.WOUND_SEVERITY_MAX))
        # ...and the penalty moved with it: the arm's STR came back.
        self.assertEqual((h.str_, h.dex), (base_str, base_dex - 1))

    def test_a_lighter_blow_only_adds_its_load(self):
        h = _hero()
        rpg.add_wound(h, "leg", CRIPPLING, G_CRIPPLING)
        rpg.add_wound(h, "arm", GRIEVOUS, G_GRIEVOUS)
        w, = h.wounds
        self.assertEqual((w.location, w.name), ("leg", "a broken leg"))
        self.assertEqual(w.severity, min(CRIPPLING + GRIEVOUS,
                                         rpg.WOUND_SEVERITY_MAX))

    def test_going_down_deepens_the_wound_without_renaming_it(self):
        h = _hero()
        rpg.add_wound(h, "leg", CRIPPLING, G_CRIPPLING)
        rpg.go_down(h)
        w, = h.wounds
        self.assertEqual(w.name, "a broken leg")
        self.assertEqual(w.severity, CRIPPLING + rpg.WOUND_DOWN_SEVERITY)

    def test_a_blow_after_a_beating_names_the_record(self):
        h = _hero()
        rpg.go_down(h)
        rpg.add_wound(h, "gut", GRIEVOUS, G_GRIEVOUS)
        w, = h.wounds
        self.assertEqual((w.location, w.grade), ("gut", G_GRIEVOUS))
        self.assertEqual(w.severity, rpg.WOUND_DOWN_SEVERITY + GRIEVOUS)

    def test_deepening_stops_at_the_load_cap(self):
        h = _hero()
        for _ in range(6):
            rpg.add_wound(h, "arm", CRIPPLING, G_CRIPPLING)
        self.assertEqual(len(h.wounds), 1)
        self.assertEqual(h.wounds[0].severity, rpg.WOUND_SEVERITY_MAX)

    def test_a_worse_blow_still_renames_a_record_at_the_cap(self):
        h = _hero()
        for _ in range(3):
            rpg.add_wound(h, "arm", GRIEVOUS, G_GRIEVOUS)
        self.assertEqual(h.wounds[0].severity, rpg.WOUND_SEVERITY_MAX)
        rpg.add_wound(h, "hand", CRIPPLING, G_CRIPPLING)
        self.assertEqual(h.wounds[0].name, "a broken hand")

    def test_a_new_blow_reopens_a_dressed_wound(self):
        h = _hero()
        rpg.add_wound(h, "gut", GRIEVOUS, G_GRIEVOUS)
        h.wounds[0].treated = True
        rpg.add_wound(h, "arm", GRIEVOUS, G_GRIEVOUS)
        self.assertFalse(h.wounds[0].treated)

    def test_the_name_does_not_step_down_as_it_knits(self):
        h = _hero()
        rpg.add_wound(h, "leg", CRIPPLING, G_CRIPPLING)
        rpg.heal_wounds(h, CRIPPLING - 1)
        w, = h.wounds
        self.assertEqual((w.name, w.severity), ("a broken leg", 1))
        self.assertEqual(w.penalty, {"dex": -1})

    def test_a_maiming_sits_beside_the_wound(self):
        h = _hero()
        rpg.add_wound(h, "leg", GRIEVOUS, G_GRIEVOUS)
        rpg.maim(h, "eye")
        self.assertEqual(len(h.wounds), 2)
        self.assertEqual(sorted(w.permanent for w in h.wounds),
                         [False, True])
        # The wound goes on deepening on its own record.
        rpg.add_wound(h, "arm", GRIEVOUS, G_GRIEVOUS)
        self.assertEqual(len(h.wounds), 2)
        self.assertEqual(next(w for w in h.wounds if not w.permanent).severity,
                         2 * GRIEVOUS)

    def test_the_played_log_says_wound_then_hurt_worse(self):
        h = _hero()
        log: list[str] = []
        rpg.add_wound(h, "arm", GRIEVOUS, G_GRIEVOUS, log=log)
        rpg.add_wound(h, "leg", GRIEVOUS, G_GRIEVOUS, log=log)
        text = "\n".join(log)
        self.assertIn("takes a wound", text)
        self.assertIn("is hurt worse", text)


class TheAsymmetry(unittest.TestCase):
    """Heroes record wounds; foes keep the scalar and nothing else. Records on
    foes would buy nothing (they do not persist) and would cost the bestiary's
    25 bench-fitted annotations."""

    def test_a_foe_records_nothing(self):
        f = _foe()
        rpg.record_hit_wound(f, "crippling blow", random.Random(1))
        rpg.add_wound(f, "arm", CRIPPLING, G_CRIPPLING)
        rpg.go_down(f)
        self.assertEqual(f.wounds, [])
        self.assertEqual(f.hp_ceiling, f.max_hp)

    def test_the_catalog_never_records(self):
        rng = random.Random(2)
        for kind in sites.FOES:
            self.assertFalse(sites.make_foe(kind, 1, rng).records_wounds,
                             kind)

    def test_heroes_do(self):
        rng = random.Random(2)
        self.assertTrue(rpg.make_human(rng, "Hero").records_wounds)

    def test_a_foe_costs_no_rng_call(self):
        # The stream a foe-only exchange rolls must not move: the whole
        # bestiary calibration is keyed to it.
        a, b = random.Random(5), random.Random(5)
        rpg.record_hit_wound(_foe(), "crippling blow", a)
        self.assertEqual(a.random(), b.random())


class TheMaiming(unittest.TestCase):
    """A crippling blow to a LIMB that would kill maims instead; the same blow
    to a vital is still the killing one."""

    def test_a_crippling_limb_blow_that_drops_you_maims(self):
        maimed = 0
        for seed in range(40):
            h = _hero(hp=10)
            h.hp = 0
            h.dead = True
            rpg.record_hit_wound(h, "crippling blow", random.Random(seed),
                                 log=[])
            limb = [w for w in h.wounds if w.location in rpg.WOUND_LIMBS]
            if limb:       # the seed rolled a limb
                maimed += 1
                self.assertFalse(h.dead)
                self.assertTrue(h.down)
                self.assertTrue(limb[0].permanent)
                self.assertEqual(limb[0].severity, CRIPPLING)
        self.assertGreater(maimed, 0)

    def test_a_vital_hit_leaves_the_death_path_alone(self):
        # Forced: the location is the only thing that decides this.
        for loc in rpg.WOUND_VITALS:
            h = _hero(hp=10)
            h.hp, h.dead = 0, True
            rpg.add_wound(h, loc, CRIPPLING, G_CRIPPLING, permanent=False)
            self.assertTrue(h.dead, loc)

    def test_a_crippling_blow_that_does_not_drop_you_never_maims(self):
        # The rare-and-meaningful rule: maimings are what would have been
        # deaths, not every deep cut.
        rng = random.Random(9)
        for _ in range(50):
            h = _hero(hp=20)
            h.hp = 12
            rpg.record_hit_wound(h, "crippling blow", rng)
            self.assertFalse(h.maimed)

    def test_only_the_epic_tier_reaches_a_maiming(self):
        h = _hero()
        rpg.maim(h, "leg")
        self.assertEqual(rpg.heal_wounds(h, rpg.ELIXIR_SEVERITY), [])
        self.assertTrue(h.maimed)                              # a bed/healer
        self.assertTrue(rpg.heal_wounds(h, rpg.ELIXIR_SEVERITY,
                                        permanents=True))
        self.assertFalse(h.maimed)

    def test_the_elixir_reaches_the_whole_of_any_one_record(self):
        # "Clears one wound of any kind outright" has to stay literally true
        # at the load cap, or the epic tier is a bed-night with a name.
        self.assertGreaterEqual(rpg.ELIXIR_SEVERITY, rpg.WOUND_SEVERITY_MAX)


class TheCeiling(unittest.TestCase):
    """hp_ceiling = max(max_hp // 2, max_hp - wound_load). The floor is the
    anti-death-spiral guarantee and it is not optional."""

    def test_the_ceiling_drops_by_the_wound_load(self):
        h = _hero(hp=20)
        rpg.add_wound(h, "arm", GRIEVOUS, G_GRIEVOUS)
        self.assertEqual(h.hp_ceiling, 20 - GRIEVOUS)

    def test_the_ceiling_never_falls_below_half_the_pool(self):
        h = _hero(hp=10)
        rpg.add_wound(h, "leg", rpg.WOUND_SEVERITY_MAX, G_CRIPPLING)
        rpg.maim(h, "arm")
        self.assertGreater(h.wound_load, 5)
        self.assertEqual(h.hp_ceiling, 5)

    def test_an_unwounded_body_has_no_ceiling_at_all(self):
        h = _hero(hp=13)
        self.assertEqual(h.hp_ceiling, 13)

    def test_the_night_stops_at_the_ceiling(self):
        h = _hero(hp=20)
        rpg.add_wound(h, "flesh", GRIEVOUS, G_GRIEVOUS)
        h.hp = 1
        for _ in range(20):
            rpg.long_rest([h], rpg.Clock(), [])
        self.assertEqual(h.hp, h.hp_ceiling)
        self.assertLess(h.hp, h.max_hp)

    def test_a_healing_potion_stops_there_too(self):
        h = _hero(hp=20)
        rpg.add_wound(h, "flesh", GRIEVOUS, G_GRIEVOUS)
        h.hp = h.hp_ceiling - 1
        h.items["healing"] = 1
        rpg.use_potion(h, "healing", [])
        self.assertEqual(h.hp, h.hp_ceiling)


class TheStatFold(unittest.TestCase):
    """Penalties are folded into the raw stats (the str_buff pattern in the
    other direction), so every read site needs no wound special case."""

    def test_a_located_wound_docks_its_stat(self):
        h = _hero()
        base = h.str_
        rpg.add_wound(h, "arm", GRIEVOUS, G_GRIEVOUS)
        self.assertEqual(h.str_, base - 1)

    def test_closing_it_gives_the_stat_back(self):
        h = _hero()
        base_str, base_dex = h.str_, h.dex
        rpg.add_wound(h, "arm", CRIPPLING, G_CRIPPLING)   # STR -1, DEX -1
        rpg.heal_wounds(h, 99)
        self.assertEqual((h.str_, h.dex), (base_str, base_dex))
        self.assertEqual(h.wound_stat_pen, {})

    def test_the_fold_is_idempotent(self):
        h = _hero()
        rpg.add_wound(h, "head", GRIEVOUS, G_GRIEVOUS)
        snapshot = (h.dex, h.mind)
        for _ in range(5):
            rpg._sync_wound_stats(h)
        self.assertEqual((h.dex, h.mind), snapshot)

    def test_a_crippling_arm_adds_its_extra_and_a_grievous_one_does_not(self):
        h = _hero()
        base = h.dex
        rpg.add_wound(h, "arm", GRIEVOUS, G_GRIEVOUS)
        self.assertEqual(h.dex, base)
        rpg.add_wound(h, "arm", CRIPPLING, G_CRIPPLING)   # now grade 3
        self.assertEqual(h.dex, base - 1)

    def test_no_stat_is_ever_pushed_below_the_floor(self):
        for loc in rpg.WOUND_LOCATION_WEIGHTS:
            h = rpg.Entity(name="Frail", dex=1, str_=1, sta=1, max_hp=20,
                           mind=1, records_wounds=True)
            rpg.add_wound(h, loc, CRIPPLING, G_CRIPPLING)
            for attr in ("dex", "str_", "mind", "sta"):
                self.assertGreaterEqual(getattr(h, attr),
                                        rpg.WOUND_STAT_FLOOR, (loc, attr))

    def test_a_crushed_chest_shrinks_the_pool_you_stand_in(self):
        h = _hero()
        h.cur_sta = h.sta
        rpg.add_wound(h, "chest", GRIEVOUS, G_GRIEVOUS)
        self.assertEqual(h.sta, 8 - 2)
        self.assertEqual(h.cur_sta, h.sta)


class TheBudgetShift(unittest.TestCase):
    """HERO_PAIN 2 -> 3 is what keeps a single blow from being charged twice:
    the anonymous HP penalty gives up roughly what the named wound takes."""

    def test_heroes_are_pain_three_and_foes_are_not(self):
        self.assertEqual(rpg.HERO_PAIN, 3)
        rng = random.Random(1)
        self.assertEqual(rpg.make_human(rng, "H").pain, rpg.HERO_PAIN)
        self.assertEqual(sites.make_foe("cutthroat", 1, rng).pain, 2)

    def test_six_hp_lost_now_costs_two_not_three(self):
        h = _hero(hp=20, pain=rpg.HERO_PAIN)
        h.hp = 14
        self.assertEqual(h.wound_penalty, 2)


class TheTreatmentLadder(unittest.TestCase):
    """Every rung is the same primitive with a different budget and reach."""

    def test_a_bed_knits_one_severity_a_night_and_the_wilds_knit_none(self):
        bedded, camped = _hero(hp=20), _hero(hp=20)
        for h in (bedded, camped):
            rpg.add_wound(h, "flesh", GRIEVOUS, G_GRIEVOUS)
        rpg.long_rest([bedded], rpg.Clock(), [], bed=True)
        rpg.long_rest([camped], rpg.Clock(), [], bed=False)
        self.assertEqual(bedded.wound_load, GRIEVOUS - 1)
        self.assertEqual(camped.wound_load, GRIEVOUS)

    def test_a_grievous_wound_is_three_bed_nights_and_a_crippling_four(self):
        for sev in (GRIEVOUS, CRIPPLING):
            h = _hero(hp=20)
            grade = G_GRIEVOUS if sev == GRIEVOUS else G_CRIPPLING
            rpg.add_wound(h, "leg", sev, grade)
            nights = 0
            while h.wounds:
                rpg.long_rest([h], rpg.Clock(), [], bed=True)
                nights += 1
            self.assertEqual(nights, sev)

    def test_a_bed_never_touches_a_maiming(self):
        h = _hero()
        rpg.maim(h, "eye")
        for _ in range(10):
            rpg.long_rest([h], rpg.Clock(), [], bed=True)
        self.assertTrue(h.maimed)

    def test_the_healer_is_capped_by_the_settlement_tier(self):
        for subtype, cap in rpg.HEALER_TIER_CAP.items():
            h = _hero(hp=30)
            rpg.add_wound(h, "leg", CRIPPLING, G_CRIPPLING)
            rpg.add_wound(h, "arm", GRIEVOUS, G_GRIEVOUS)
            rpg.add_wound(h, "hand", GRIEVOUS, G_GRIEVOUS)
            load = h.wound_load
            self.assertEqual(load, rpg.WOUND_SEVERITY_MAX)
            purse = rpg.Purse(silver=10_000)
            closed, _ = rpg.healer_service([h], purse, subtype, [])
            if cap is None:
                self.assertEqual(h.wound_load, 0, subtype)
            else:
                self.assertEqual(closed, cap, subtype)
                self.assertEqual(h.wound_load, load - cap, subtype)

    def test_the_healer_charges_a_flat_fee_per_severity(self):
        h = _hero()
        rpg.add_wound(h, "flesh", GRIEVOUS, G_GRIEVOUS)
        purse = rpg.Purse(silver=1000)
        closed, spent = rpg.healer_service([h], purse, "town", [])
        self.assertEqual(spent, rpg.HEALER_FEE * closed)

    def test_an_empty_purse_buys_no_treatment(self):
        h = _hero()
        rpg.add_wound(h, "flesh", GRIEVOUS, G_GRIEVOUS)
        purse = rpg.Purse(silver=rpg.HEALER_FEE - 1)
        closed, spent = rpg.healer_service([h], purse, "capital", [])
        self.assertEqual((closed, spent), (0, 0))
        self.assertEqual(h.wound_load, GRIEVOUS)

    def test_the_healer_never_reaches_a_maiming(self):
        h = _hero()
        rpg.maim(h, "hand")
        purse = rpg.Purse(silver=1000)
        closed, spent = rpg.healer_service([h], purse, "capital", [])
        self.assertEqual((closed, spent), (0, 0))
        self.assertEqual(purse.silver, 1000)

    def test_treatment_dresses_what_it_cannot_close(self):
        h = _hero(hp=30)
        rpg.add_wound(h, "gut", CRIPPLING, G_CRIPPLING)
        rpg.healer_service([h], rpg.Purse(silver=1000), "village", [])
        self.assertEqual(h.wound_load, CRIPPLING - 2)
        self.assertTrue(h.wounds[0].treated)
        self.assertEqual(rpg.untreated_wounds(h), 0)

    def test_a_rung_only_dresses_the_bodies_it_reached(self):
        # The cap has to bite: a healer who spends the village's whole reach
        # on the worst wound in the room leaves the other hero's raw.
        worse, lighter = _hero("Worse", hp=30), _hero("Lighter", hp=30)
        rpg.add_wound(worse, "gut", CRIPPLING, G_CRIPPLING)
        rpg.add_wound(lighter, "hand", GRIEVOUS, G_GRIEVOUS)
        rpg.healer_service([worse, lighter], rpg.Purse(silver=1000),
                           "village", [])
        self.assertTrue(worse.wounds[0].treated)
        self.assertFalse(lighter.wounds[0].treated)

    def test_a_salve_knits_two_and_dresses_the_wound(self):
        h = _hero()
        rpg.add_wound(h, "leg", CRIPPLING, G_CRIPPLING)
        h.items["salve"] = 2
        self.assertTrue(rpg.use_potion(h, "salve", []))
        w, = h.wounds
        self.assertEqual(w.severity, CRIPPLING - rpg.SALVE_SEVERITY)
        self.assertTrue(w.treated)
        self.assertEqual(w.name, "a broken leg")
        self.assertTrue(rpg.use_potion(h, "salve", []))
        self.assertEqual(h.wounds, [])

    def test_a_salve_cannot_reach_a_maiming(self):
        h = _hero()
        rpg.maim(h, "leg")
        h.items["salve"] = 1
        self.assertFalse(rpg.use_potion(h, "salve", []))
        self.assertEqual(h.items["salve"], 1)       # nothing was spent

    def test_the_salve_is_the_healer_in_a_jar(self):
        # Same rate as the healer's fee for the severity it knits -- what the
        # silver buys is carrying it, not a discount.
        self.assertEqual(rpg.SALVE_PRICE,
                         rpg.HEALER_FEE * rpg.SALVE_SEVERITY)

    def test_an_elixir_reaches_a_maiming(self):
        h = _hero()
        rpg.maim(h, "leg")
        h.items["elixir"] = 1
        self.assertTrue(rpg.use_potion(h, "elixir", []))
        self.assertFalse(h.maimed)
        self.assertEqual(h.wounds, [])

    def test_the_top_rank_healing_spell_clears_a_maiming(self):
        healer = _hero("Mage", hp=20)
        healer.school, healer.mind = "fire", 8
        healer.spells["healing"] = rpg.SPELL_RANK_MAX
        healer.power = healer.cur_power = 30
        target = _hero("Hurt", hp=20)
        rpg.maim(target, "arm")
        target.hp = target.hp_ceiling
        rpg.cast_healing(healer, target, random.Random(3), [])
        self.assertFalse(target.maimed)

    def test_a_lower_rank_healing_spell_does_not(self):
        healer = _hero("Mage", hp=20)
        healer.school, healer.mind = "fire", 8
        healer.spells["healing"] = 2
        healer.power = healer.cur_power = 30
        target = _hero("Hurt", hp=20)
        rpg.maim(target, "arm")
        target.hp = 1
        rpg.cast_healing(healer, target, random.Random(3), [])
        self.assertTrue(target.maimed)

    def test_the_salve_is_shop_stocked_and_the_elixir_is_not(self):
        self.assertIn("salve", rpg.SHOP_POTION_KINDS)
        self.assertNotIn("elixir", rpg.SHOP_POTION_KINDS)
        self.assertIn("salve", rpg.ALCHEMY_RECIPE_RANK)
        self.assertNotIn("elixir", rpg.ALCHEMY_RECIPE_RANK)

    def test_the_wound_tiers_stay_out_of_the_scrounged_kit(self):
        # Deliberate: leaving creation/drops/the overnight kit alone is what
        # keeps their RNG streams -- and the calibration behind them -- put.
        for kind in ("salve", "elixir"):
            self.assertNotIn(kind, rpg.STOCKED_POTION_KINDS)
            self.assertNotIn(kind, rpg.AUTO_POTION_KINDS)


class TheBleedRederivation(unittest.TestCase):
    """First aid stops the blood; the WOUND is what has to be treated, so an
    untended gut wound opens again the next time the body fights."""

    def test_an_open_gut_wound_bleeds_at_every_fight_start(self):
        h = _hero()
        rpg.add_wound(h, "gut", GRIEVOUS, G_GRIEVOUS)
        rpg.refresh_wound_bleed([h])
        self.assertIsNotNone(rpg.condition_of(h, "bleed"))
        rpg._stabilize([h], [])
        self.assertIsNone(rpg.condition_of(h, "bleed"))
        rpg.refresh_wound_bleed([h])
        self.assertIsNotNone(rpg.condition_of(h, "bleed"))

    def test_a_dressed_wound_does_not(self):
        h = _hero()
        rpg.add_wound(h, "gut", GRIEVOUS, G_GRIEVOUS)
        h.wounds[0].treated = True
        rpg.refresh_wound_bleed([h])
        self.assertIsNone(rpg.condition_of(h, "bleed"))

    def test_only_the_bleeding_locations_bleed(self):
        h = _hero()
        rpg.add_wound(h, "hand", GRIEVOUS, G_GRIEVOUS)
        rpg.refresh_wound_bleed([h])
        self.assertIsNone(rpg.condition_of(h, "bleed"))

    def test_the_bleed_follows_the_record_when_a_worse_blow_moves_it(self):
        h = _hero()
        rpg.add_wound(h, "gut", GRIEVOUS, G_GRIEVOUS)
        rpg.add_wound(h, "leg", CRIPPLING, G_CRIPPLING)
        self.assertEqual(h.wounds[0].bleed, 0)
        rpg.refresh_wound_bleed([h])
        self.assertIsNone(rpg.condition_of(h, "bleed"))


class TheMoraleDrain(unittest.TestCase):
    """A long convalescence costs the party, and needs no new departure
    machinery to do it."""

    def _companion(self) -> rpg.Entity:
        h = _hero("Comp")
        h.satisfaction = rpg.SATISFACTION_START
        return h

    def test_an_untended_wound_costs_morale_every_night(self):
        h = self._companion()
        rpg.add_wound(h, "flesh", GRIEVOUS, G_GRIEVOUS)
        before = h.satisfaction
        rpg.wound_morale([h], [])
        self.assertEqual(h.satisfaction, before + rpg.SAT_WOUNDED_DAY)

    def test_a_dressed_wound_costs_nothing(self):
        h = self._companion()
        rpg.add_wound(h, "flesh", GRIEVOUS, G_GRIEVOUS)
        h.wounds[0].treated = True
        before = h.satisfaction
        rpg.wound_morale([h], [])
        self.assertEqual(h.satisfaction, before)

    def test_a_maiming_is_mourned_once_and_not_nightly(self):
        h = self._companion()
        rpg.maim(h, "eye")
        rpg.wound_morale([h], [])
        after_first = h.satisfaction
        rpg.wound_morale([h], [])
        self.assertEqual(h.satisfaction, after_first)

    def test_the_pc_is_untracked_and_unaffected(self):
        h = _hero("PC")            # satisfaction None: the PC has no track
        rpg.add_wound(h, "flesh", GRIEVOUS, G_GRIEVOUS)
        rpg.wound_morale([h], [])
        self.assertIsNone(h.satisfaction)


class InTheFight(unittest.TestCase):
    """Both channels are live in the fight the wound is taken in -- there is
    no seam and no `fresh` flag."""

    def test_a_played_fight_leaves_records_on_the_party_only(self):
        wounded = 0
        for seed in range(40):
            rng = random.Random(seed)
            party = rpg.make_party(rng)
            foes = [sites.make_foe("cutthroat", 1, rng),
                    sites.make_foe("bruiser", 2, rng)]
            rpg.group_combat(party, foes, rng, [])
            wounded += sum(1 for h in party if h.wounds)
            self.assertFalse(any(f.wounds for f in foes), seed)
        self.assertGreater(wounded, 0)

    def test_a_hero_never_carries_two_wounds(self):
        for seed in range(60):
            rng = random.Random(seed)
            party = rpg.make_party(rng)
            foes = [sites.make_foe("cutthroat", 1, rng),
                    sites.make_foe("bruiser", 2, rng),
                    sites.make_foe("bruiser", 3, rng)]
            rpg.group_combat(party, foes, rng, [])
            for h in party:
                self.assertLessEqual(
                    sum(1 for w in h.wounds if not w.permanent), 1, seed)

    def test_records_survive_the_end_of_the_fight(self):
        for seed in range(20):
            rng = random.Random(seed)
            party = rpg.make_party(rng)
            foes = [sites.make_foe("bruiser", 1, rng)]
            rpg.group_combat(party, foes, rng, [])
            loads = [h.wound_load for h in party]
            rpg._clear_fight_states(party)
            self.assertEqual([h.wound_load for h in party], loads, seed)


class TheSaveRoundTrip(unittest.TestCase):
    """A wound outlives rather more than a fight, so it has to outlive the
    save -- and the docked stats must not be docked a second time."""

    def test_wounds_survive_the_round_trip(self):
        h = _hero()
        rpg.add_wound(h, "arm", GRIEVOUS, G_GRIEVOUS)
        rpg.maim(h, "eye")
        back = session._entity_from_dict(session._entity_to_dict(h))
        self.assertEqual(len(back.wounds), 2)
        self.assertEqual(back.wound_load, h.wound_load)
        self.assertEqual([w.grade for w in back.wounds],
                         [w.grade for w in h.wounds])
        self.assertTrue(back.maimed)
        self.assertEqual(back.hp_ceiling, h.hp_ceiling)

    def test_the_stat_fold_is_not_charged_twice(self):
        h = _hero()
        rpg.add_wound(h, "arm", CRIPPLING, G_CRIPPLING)
        back = session._entity_from_dict(session._entity_to_dict(h))
        self.assertEqual((back.str_, back.dex), (h.str_, h.dex))
        rpg._sync_wound_stats(back)
        self.assertEqual((back.str_, back.dex), (h.str_, h.dex))


class TheDisplay(unittest.TestCase):
    """The played surfaces band HP into a state word; the digits stay one
    command away. Everything still fits the 40-column wrap."""

    def test_hp_reads_as_a_state_word_against_the_ceiling(self):
        h = _hero(hp=20)
        h.hp = 20
        self.assertEqual(h.hp_state, "Unhurt")
        rpg.add_wound(h, "flesh", GRIEVOUS, G_GRIEVOUS)
        h.hp = h.hp_ceiling
        self.assertEqual(h.hp_state, "Unhurt")   # as whole as they can be
        h.hp = 2
        self.assertEqual(h.hp_state, "Failing")
        h.down = True
        self.assertEqual(h.hp_state, "Down")

    def test_wound_tags_mark_permanents_and_dressings(self):
        h = _hero()
        rpg.maim(h, "eye")
        rpg.add_wound(h, "flesh", GRIEVOUS, G_GRIEVOUS)
        next(w for w in h.wounds if not w.permanent).treated = True
        tags = rpg.wound_tags(h)
        self.assertTrue(any("[PERMANENT]" in t for t in tags))
        self.assertTrue(any("(dressed)" in t for t in tags))

    def test_the_authored_names_fit_the_column(self):
        for loc, table in rpg.WOUND_NAMES.items():
            for grade, name in table.items():
                for line in rpg.fit_lines([name]):
                    self.assertLessEqual(len(line), rpg.PLAYER_WIDTH,
                                         (loc, grade, line))
        for loc, name in rpg.WOUND_MAIM_NAMES.items():
            for line in rpg.fit_lines([name]):
                self.assertLessEqual(len(line), rpg.PLAYER_WIDTH, (loc, line))


if __name__ == "__main__":
    unittest.main()
