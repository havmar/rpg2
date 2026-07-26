"""Contract suite for the WOUND system (2026-07-26, the attrition rework's
slice 3b -- rules.md's Wounds & Recovery add-on).

What this pins is the load-bearing half: the accrual table (what each tier
leaves and what a graze deliberately does not), the maiming rule and its one
condition, the HP ceiling and the half-pool floor that keeps it from being a
death spiral, the stat fold and its idempotence, the asymmetry (heroes record,
foes never do), every rung of the treatment ladder and what each one can and
cannot reach, the bleed re-derivation, the morale drain, and the save
round-trip -- including a pre-slice save with no `wounds` key.

Run:  python -m unittest -v test_wounds.py
"""

import random
import unittest

import rpg
import sites
import session


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

    def test_every_location_has_a_name_at_every_severity(self):
        for loc in list(rpg.WOUND_LOCATION_WEIGHTS) + [""]:
            for sev in range(1, rpg.WOUND_SEVERITY_MAX + 1):
                self.assertTrue(rpg.wound_name(loc, sev), (loc, sev))


class TheAccrualTable(unittest.TestCase):
    """graze nothing / wound 1 / grievous 2 / crippling 3."""

    def test_a_graze_records_nothing(self):
        h = _hero()
        rpg.record_hit_wound(h, "graze", random.Random(1))
        self.assertEqual(h.wounds, [])

    def test_the_tiers_record_their_severities(self):
        for tier, sev in (("wound", 1), ("grievous", 2),
                          ("crippling blow", 3)):
            h = _hero()
            rpg.record_hit_wound(h, tier, random.Random(4))
            self.assertEqual(h.wound_load, sev, tier)

    def test_a_deflection_records_nothing(self):
        h = _hero()
        rpg.record_hit_wound(h, "deflected", random.Random(1))
        self.assertEqual(h.wounds, [])

    def test_a_second_hit_to_the_same_place_deepens_it(self):
        # Bounded exactly as conditions are: never a second record.
        h = _hero()
        rpg.add_wound(h, "arm", 1)
        rpg.add_wound(h, "arm", 1)
        self.assertEqual(len(h.wounds), 1)
        self.assertEqual(h.wounds[0].severity, 2)

    def test_deepening_stops_at_the_severity_cap(self):
        h = _hero()
        for _ in range(6):
            rpg.add_wound(h, "arm", 2)
        self.assertEqual(h.wounds[0].severity, rpg.WOUND_SEVERITY_MAX)

    def test_going_down_records_an_unlocated_beating(self):
        h = _hero()
        rpg.go_down(h)
        self.assertTrue(h.down)
        self.assertEqual([w.location for w in h.wounds], [""])
        self.assertEqual(h.wounds[0].name, "badly beaten")


class TheAsymmetry(unittest.TestCase):
    """Heroes record wounds; foes keep the scalar and nothing else. Records on
    foes would buy nothing (they do not persist) and would cost the bestiary's
    25 bench-fitted annotations."""

    def test_a_foe_records_nothing(self):
        f = _foe()
        rpg.record_hit_wound(f, "crippling blow", random.Random(1))
        rpg.add_wound(f, "arm", 3)
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
        h = _hero(hp=10)
        h.hp = 0
        h.dead = True
        rpg.record_hit_wound(h, "crippling blow", random.Random(1),
                             log=[])
        limb = [w for w in h.wounds if w.location in rpg.WOUND_LIMBS]
        if limb:       # the seed rolled a limb
            self.assertFalse(h.dead)
            self.assertTrue(h.down)
            self.assertTrue(limb[0].permanent)

    def test_a_vital_hit_leaves_the_death_path_alone(self):
        # Forced: the location is the only thing that decides this.
        for loc in rpg.WOUND_VITALS:
            h = _hero(hp=10)
            h.hp, h.dead = 0, True
            rpg.add_wound(h, loc, 3, permanent=False)
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
        rpg.add_wound(h, "leg", 3, permanent=True)
        self.assertEqual(rpg.heal_wounds(h, 3), [])          # a bed/healer
        self.assertTrue(h.maimed)
        self.assertTrue(rpg.heal_wounds(h, 3, permanents=True))
        self.assertFalse(h.maimed)


class TheCeiling(unittest.TestCase):
    """hp_ceiling = max(max_hp // 2, max_hp - wound_load). The floor is the
    anti-death-spiral guarantee and it is not optional."""

    def test_the_ceiling_drops_by_the_wound_load(self):
        h = _hero(hp=20)
        rpg.add_wound(h, "arm", 2)
        self.assertEqual(h.hp_ceiling, 18)

    def test_the_ceiling_never_falls_below_half_the_pool(self):
        h = _hero(hp=20)
        for loc in rpg.WOUND_LOCATION_WEIGHTS:
            rpg.add_wound(h, loc, 3)
        self.assertGreater(h.wound_load, 10)
        self.assertEqual(h.hp_ceiling, 10)

    def test_an_unwounded_body_has_no_ceiling_at_all(self):
        h = _hero(hp=13)
        self.assertEqual(h.hp_ceiling, 13)

    def test_the_night_stops_at_the_ceiling(self):
        h = _hero(hp=20)
        rpg.add_wound(h, "flesh", 3)
        h.hp = 1
        for _ in range(20):
            rpg.long_rest([h], rpg.Clock(), [])
        self.assertEqual(h.hp, h.hp_ceiling)
        self.assertLess(h.hp, h.max_hp)

    def test_a_healing_potion_stops_there_too(self):
        h = _hero(hp=20)
        rpg.add_wound(h, "flesh", 3)
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
        rpg.add_wound(h, "arm", 1)
        self.assertEqual(h.str_, base - 1)

    def test_closing_it_gives_the_stat_back(self):
        h = _hero()
        base_str, base_dex = h.str_, h.dex
        rpg.add_wound(h, "arm", 1)
        rpg.add_wound(h, "hand", 1)
        rpg.heal_wounds(h, 99)
        self.assertEqual((h.str_, h.dex), (base_str, base_dex))
        self.assertEqual(h.wound_stat_pen, {})

    def test_the_fold_is_idempotent(self):
        h = _hero()
        rpg.add_wound(h, "head", 2)
        snapshot = (h.dex, h.mind)
        for _ in range(5):
            rpg._sync_wound_stats(h)
        self.assertEqual((h.dex, h.mind), snapshot)

    def test_a_severity_three_arm_adds_its_extra(self):
        h = _hero()
        base = h.dex
        rpg.add_wound(h, "arm", 2)
        self.assertEqual(h.dex, base)
        rpg.add_wound(h, "arm", 1)      # now severity 3
        self.assertEqual(h.dex, base - 1)

    def test_no_stat_is_ever_pushed_below_the_floor(self):
        h = rpg.Entity(name="Frail", dex=1, str_=1, sta=1, max_hp=20,
                       mind=1, records_wounds=True)
        for loc in rpg.WOUND_LOCATION_WEIGHTS:
            rpg.add_wound(h, loc, 3)
        for attr in ("dex", "str_", "mind", "sta"):
            self.assertGreaterEqual(getattr(h, attr), rpg.WOUND_STAT_FLOOR,
                                    attr)

    def test_a_crushed_chest_shrinks_the_pool_you_stand_in(self):
        h = _hero()
        h.cur_sta = h.sta
        rpg.add_wound(h, "chest", 1)
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
            rpg.add_wound(h, "flesh", 2)
        rpg.long_rest([bedded], rpg.Clock(), [], bed=True)
        rpg.long_rest([camped], rpg.Clock(), [], bed=False)
        self.assertEqual(bedded.wound_load, 1)
        self.assertEqual(camped.wound_load, 2)

    def test_a_bed_never_touches_a_maiming(self):
        h = _hero()
        rpg.add_wound(h, "eye", 3, permanent=True)
        for _ in range(10):
            rpg.long_rest([h], rpg.Clock(), [], bed=True)
        self.assertTrue(h.maimed)

    def test_the_healer_is_capped_by_the_settlement_tier(self):
        for subtype, cap in rpg.HEALER_TIER_CAP.items():
            h = _hero(hp=30)
            for loc in ("flesh", "arm", "leg", "hand"):
                rpg.add_wound(h, loc, 3)
            load = h.wound_load
            purse = rpg.Purse(gold=10_000)
            closed, _ = rpg.healer_service([h], purse, subtype, [])
            if cap is None:
                self.assertEqual(h.wound_load, 0, subtype)
            else:
                self.assertEqual(closed, cap, subtype)
                self.assertEqual(h.wound_load, load - cap, subtype)

    def test_the_healer_charges_a_flat_fee_per_severity(self):
        h = _hero()
        rpg.add_wound(h, "flesh", 2)
        purse = rpg.Purse(gold=1000)
        closed, spent = rpg.healer_service([h], purse, "town", [])
        self.assertEqual(spent, rpg.HEALER_FEE * closed)

    def test_an_empty_purse_buys_no_treatment(self):
        h = _hero()
        rpg.add_wound(h, "flesh", 2)
        purse = rpg.Purse(gold=rpg.HEALER_FEE - 1)
        closed, spent = rpg.healer_service([h], purse, "capital", [])
        self.assertEqual((closed, spent), (0, 0))
        self.assertEqual(h.wound_load, 2)

    def test_the_healer_never_reaches_a_maiming(self):
        h = _hero()
        rpg.add_wound(h, "hand", 3, permanent=True)
        purse = rpg.Purse(gold=1000)
        closed, spent = rpg.healer_service([h], purse, "capital", [])
        self.assertEqual((closed, spent), (0, 0))
        self.assertEqual(purse.gold, 1000)

    def test_treatment_dresses_what_it_cannot_close(self):
        h = _hero(hp=30)
        rpg.add_wound(h, "gut", 3)
        rpg.healer_service([h], rpg.Purse(gold=1000), "village", [])
        self.assertTrue(h.wounds[0].treated)
        self.assertEqual(rpg.untreated_wounds(h), 0)

    def test_a_salve_closes_one_wound_and_cannot_reach_a_maiming(self):
        h = _hero()
        rpg.add_wound(h, "flesh", 1)
        h.items["salve"] = 2
        self.assertTrue(rpg.use_potion(h, "salve", []))
        self.assertEqual(h.wounds, [])
        rpg.add_wound(h, "leg", 3, permanent=True)
        self.assertFalse(rpg.use_potion(h, "salve", []))
        self.assertEqual(h.items["salve"], 1)       # nothing was spent

    def test_an_elixir_reaches_a_maiming(self):
        h = _hero()
        rpg.add_wound(h, "leg", 3, permanent=True)
        h.items["elixir"] = 1
        self.assertTrue(rpg.use_potion(h, "elixir", []))
        self.assertFalse(h.maimed)

    def test_the_top_rank_healing_spell_clears_a_maiming(self):
        healer = _hero("Mage", hp=20)
        healer.school, healer.mind = "fire", 8
        healer.spells["healing"] = rpg.SPELL_RANK_MAX
        healer.power = healer.cur_power = 30
        target = _hero("Hurt", hp=20)
        rpg.add_wound(target, "arm", 3, permanent=True)
        target.hp = target.hp_ceiling
        rpg.cast_healing(healer, target, random.Random(3), [])
        self.assertFalse(target.maimed)

    def test_a_lower_rank_healing_spell_does_not(self):
        healer = _hero("Mage", hp=20)
        healer.school, healer.mind = "fire", 8
        healer.spells["healing"] = 2
        healer.power = healer.cur_power = 30
        target = _hero("Hurt", hp=20)
        rpg.add_wound(target, "arm", 3, permanent=True)
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
        rpg.add_wound(h, "gut", 2)
        rpg.refresh_wound_bleed([h])
        self.assertIsNotNone(rpg.condition_of(h, "bleed"))
        rpg._stabilize([h], [])
        self.assertIsNone(rpg.condition_of(h, "bleed"))
        rpg.refresh_wound_bleed([h])
        self.assertIsNotNone(rpg.condition_of(h, "bleed"))

    def test_a_dressed_wound_does_not(self):
        h = _hero()
        rpg.add_wound(h, "gut", 2)
        h.wounds[0].treated = True
        rpg.refresh_wound_bleed([h])
        self.assertIsNone(rpg.condition_of(h, "bleed"))

    def test_only_the_bleeding_locations_bleed(self):
        h = _hero()
        rpg.add_wound(h, "hand", 2)
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
        rpg.add_wound(h, "flesh", 1)
        before = h.satisfaction
        rpg.wound_morale([h], [])
        self.assertEqual(h.satisfaction, before + rpg.SAT_WOUNDED_DAY)

    def test_a_dressed_wound_costs_nothing(self):
        h = self._companion()
        rpg.add_wound(h, "flesh", 1)
        h.wounds[0].treated = True
        before = h.satisfaction
        rpg.wound_morale([h], [])
        self.assertEqual(h.satisfaction, before)

    def test_a_maiming_is_mourned_once_and_not_nightly(self):
        h = self._companion()
        rpg.add_wound(h, "eye", 3, permanent=True)
        rpg.wound_morale([h], [])
        after_first = h.satisfaction
        rpg.wound_morale([h], [])
        self.assertEqual(h.satisfaction, after_first)

    def test_the_pc_is_untracked_and_unaffected(self):
        h = _hero("PC")            # satisfaction None: the PC has no track
        rpg.add_wound(h, "flesh", 2)
        rpg.wound_morale([h], [])
        self.assertIsNone(h.satisfaction)


class InTheFight(unittest.TestCase):
    """Both channels are live in the fight the wound is taken in -- there is
    no seam and no `fresh` flag."""

    def test_a_played_fight_leaves_records_on_the_party_only(self):
        wounded = 0
        for seed in range(20):
            rng = random.Random(seed)
            party = rpg.make_party(rng)
            foes = [sites.make_foe("cutthroat", 1, rng),
                    sites.make_foe("bruiser", 2, rng)]
            rpg.group_combat(party, foes, rng, [])
            wounded += sum(1 for h in party if h.wounds)
            self.assertFalse(any(f.wounds for f in foes), seed)
        self.assertGreater(wounded, 0)

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
        rpg.add_wound(h, "arm", 2)
        rpg.add_wound(h, "eye", 3, permanent=True)
        back = session._entity_from_dict(session._entity_to_dict(h))
        self.assertEqual(len(back.wounds), 2)
        self.assertEqual(back.wound_load, h.wound_load)
        self.assertTrue(back.maimed)
        self.assertEqual(back.hp_ceiling, h.hp_ceiling)

    def test_the_stat_fold_is_not_charged_twice(self):
        h = _hero()
        rpg.add_wound(h, "arm", 3)
        back = session._entity_from_dict(session._entity_to_dict(h))
        self.assertEqual((back.str_, back.dex), (h.str_, h.dex))
        rpg._sync_wound_stats(back)
        self.assertEqual((back.str_, back.dex), (h.str_, h.dex))

    def test_a_pre_slice_save_loads_as_an_unwounded_party(self):
        h = _hero()
        d = session._entity_to_dict(h)
        d.pop("wounds")
        d.pop("wound_stat_pen")
        back = session._entity_from_dict(d)
        self.assertEqual(back.wounds, [])
        self.assertEqual(back.hp_ceiling, back.max_hp)


class TheDisplay(unittest.TestCase):
    """The played surfaces band HP into a state word; the digits stay one
    command away. Everything still fits the 40-column wrap."""

    def test_hp_reads_as_a_state_word_against_the_ceiling(self):
        h = _hero(hp=20)
        h.hp = 20
        self.assertEqual(h.hp_state, "Unhurt")
        rpg.add_wound(h, "flesh", 3)
        h.hp = h.hp_ceiling
        self.assertEqual(h.hp_state, "Unhurt")   # as whole as they can be
        h.hp = 2
        self.assertEqual(h.hp_state, "Failing")
        h.down = True
        self.assertEqual(h.hp_state, "Down")

    def test_wound_tags_mark_permanents_and_dressings(self):
        h = _hero()
        rpg.add_wound(h, "eye", 3, permanent=True)
        rpg.add_wound(h, "flesh", 1)
        h.wounds[1].treated = True
        tags = rpg.wound_tags(h)
        self.assertTrue(any("[PERMANENT]" in t for t in tags))
        self.assertTrue(any("(dressed)" in t for t in tags))

    def test_the_authored_names_fit_the_column(self):
        for loc, table in rpg.WOUND_NAMES.items():
            for sev, name in table.items():
                for line in rpg.fit_lines([name]):
                    self.assertLessEqual(len(line), rpg.PLAYER_WIDTH,
                                         (loc, sev, line))


if __name__ == "__main__":
    unittest.main()
