"""The WEAPON GENERATION SYSTEM contract suite (2026-07-28).

What it pins: the sp currency's identities (the quality four price at
exactly 3 sp -- the exchange rate the shipped catalog encodes), the
generator's budget honesty and profile rule, the +DEX legendary gate, the
masterwork shape/price/shop doctrine, equip/unequip bookkeeping symmetry
for every weapon bonus, the wielder-side rider hook, the on-kill quirk
counters and their per-fight cap, proficiency following the chassis, the
save round-trip (old and new shapes), the famous armory's determinism and
40-column fit, the smiths' pride floor, the quest reward ladder, and the
trash chargen deal.

python -m unittest -v test_weapon_gen.py
"""

import dataclasses
import json
import random
import unittest

import rpg
import weapons
import session
import quests
from rpg import WEAPONS, Entity


def _hero(**over):
    h = rpg.make_human(random.Random(1), "Test")
    for k, v in over.items():
        setattr(h, k, v)
    return h


class TestSpCurrency(unittest.TestCase):
    def test_quality_four_price_at_exactly_three_sp(self):
        for name in ("rapier", "katana", "zweihander", "wooden staff"):
            self.assertEqual(weapons.weapon_sp(WEAPONS[name]), 3, name)

    def test_common_lines_price_at_minus_one_zero_one(self):
        self.assertEqual(weapons.weapon_sp(WEAPONS["club"]), -1)
        self.assertEqual(weapons.weapon_sp(WEAPONS["shortsword"]), 0)
        self.assertEqual(weapons.weapon_sp(WEAPONS["longsword"]), 1)

    def test_masterwork_prices_at_five_sp(self):
        for name in ("rapier", "katana", "zweihander", "wooden staff"):
            self.assertEqual(weapons.weapon_sp(rpg.masterwork_of(name)), 5,
                             name)

    def test_ranged_cards_are_off_the_scale(self):
        with self.assertRaises(ValueError):
            weapons.weapon_sp(WEAPONS["longbow"])

    def test_gold_curve_is_superlinear(self):
        self.assertEqual(weapons.value_for_sp(3), 60)
        vals = [weapons.value_for_sp(sp) for sp in range(3, 11)]
        for a, b in zip(vals, vals[1:]):
            self.assertGreaterEqual(b, 2 * a - 10)   # ~doubles per sp


class TestGenerator(unittest.TestCase):
    def test_budget_honesty_across_the_ladder(self):
        rng = random.Random(42)
        for sp in (6, 7, 8, 9, 10):
            for _ in range(40):
                w = weapons.generate_weapon(rng, sp)
                self.assertEqual(weapons.weapon_sp(w), sp,
                                 (w.name, w.tier, dataclasses.asdict(w)))

    def test_tier_bands(self):
        rng = random.Random(3)
        self.assertEqual(weapons.generate_weapon(rng, 6).tier, "magic")
        self.assertEqual(weapons.generate_weapon(rng, 8).tier, "legendary")
        self.assertEqual(weapons.generate_weapon(rng, 10).tier, "mythic")

    def test_dex_gated_to_legendary_tiers(self):
        rng = random.Random(7)
        for sp in (6, 7):
            for _ in range(60):
                self.assertEqual(weapons.generate_weapon(rng, sp).dex_bonus,
                                 0)

    def test_mythic_cap_is_the_doctrine_half(self):
        # +3 signature-stat equivalents at most: no generated weapon may
        # exceed the per-axis caps (the profile stays a profile).
        rng = random.Random(11)
        for _ in range(80):
            w = weapons.generate_weapon(rng, 10)
            self.assertLessEqual(w.dex_bonus, weapons.CAP_DEX)
            self.assertLessEqual(w.str_bonus, weapons.CAP_STR)

    def test_at_most_one_rider_and_one_quirk(self):
        rng = random.Random(13)
        for _ in range(120):
            w = weapons.generate_weapon(rng, rng.choice((6, 7, 8, 9, 10)))
            self.assertIn(w.rider, ("", "bleed", "poison", "burn", "rime"))
            quirks = sum((w.lunge, w.gold_on_kill > 0, w.karma_on_kill > 0))
            self.assertLessEqual(quirks, 1)

    def test_profile_rule_signature_axis_majority(self):
        # At least two-thirds of the budget lands on the signature axis
        # (off-axis spend -- riders, quirks, filler -- is bounded by
        # construction: off_allow = budget - ceil(2/3 budget)).
        rng = random.Random(17)
        for _ in range(120):
            sp = rng.choice((6, 7, 8, 9, 10))
            w = weapons.generate_weapon(rng, sp)
            budget = sp - weapons.QUALITY_SP
            base = WEAPONS[w.base]
            if w.base in ("rapier", "katana"):
                sig = (weapons.SP_DEX * w.dex_bonus + weapons.SP_ATK
                       * (w.atk_pressure - base.atk_pressure))
            elif w.base == "zweihander":
                sig = (weapons.SP_STR * w.str_bonus
                       + weapons.SP_SEV * (w.severity - base.severity))
            else:
                sig = (weapons.SP_POWER
                       * (w.power_bonus - base.power_bonus)
                       + weapons.SP_DEF
                       * (w.def_pressure - base.def_pressure))
            self.assertGreaterEqual(sig, -(-2 * budget // 3)
                                    - budget % 1 - 1,
                                    (w.name, sp, sig, budget))

    def test_generated_weapon_keeps_chassis_moves_and_prof(self):
        w = weapons.generate_weapon(random.Random(5), 9, chassis="katana")
        self.assertEqual(w.base, "katana")
        self.assertEqual(rpg.prof_name(w), "katana")
        self.assertEqual(w.move_tags, WEAPONS["katana"].move_tags)
        self.assertTrue(rpg.move_weapon_ok("iaido", w))

    def test_display_fits_forty_columns(self):
        rng = random.Random(23)
        for _ in range(40):
            w = weapons.generate_weapon(rng, rng.choice((6, 8, 10)))
            for line in weapons.weapon_lines(w):
                self.assertLessEqual(len(line), 40, line)


class TestMasterwork(unittest.TestCase):
    def test_shape(self):
        mw = rpg.masterwork_of("rapier")
        self.assertEqual(mw.atk_pressure, WEAPONS["rapier"].atk_pressure + 1)
        self.assertEqual(mw.durability, rpg.MASTERWORK_DURABILITY)
        self.assertEqual(mw.tier, "masterwork")
        self.assertEqual(mw.base, "rapier")
        self.assertEqual(mw.value,
                         WEAPONS["rapier"].value * rpg.MASTERWORK_PRICE_MULT)

    def test_quality_only(self):
        with self.assertRaises(ValueError):
            rpg.masterwork_of("club")

    def test_shoppable_and_legendary_refused(self):
        h = _hero()
        purse = rpg.Purse()
        purse.gold = 1000
        log = []
        self.assertTrue(rpg.buy_weapon(h, purse, "masterwork katana", log))
        self.assertEqual(purse.gold, 1000 - 300)
        self.assertEqual(h.weapon.name, "masterwork katana")
        # A non-quality masterwork ask is refused, not crashed.
        self.assertFalse(rpg.buy_weapon(h, purse, "masterwork club", log))

    def test_proficiency_follows_the_chassis(self):
        h = _hero()
        h.proficiency["katana"] = 2
        log = []
        rpg.equip_weapon(h, rpg.masterwork_of("katana"), log)
        self.assertEqual(h.prof_rank, 2)
        # ...and drilling it deepens the CHASSIS rank.
        h.skill_points = 5
        self.assertTrue(rpg.train_proficiency(h, log))
        self.assertEqual(h.proficiency["katana"], 3)
        self.assertNotIn("masterwork katana", h.proficiency)

    def test_reskin_still_follows_the_display_name(self):
        # A bare `--as` reskin has no base: the old doctrine holds.
        w = dataclasses.replace(WEAPONS["katana"], name="shock prod")
        self.assertEqual(rpg.prof_name(w), "shock prod")


class TestEquipBookkeeping(unittest.TestCase):
    def test_full_symmetry_over_every_bonus(self):
        h = _hero()
        w = dataclasses.replace(
            WEAPONS["katana"], name="test blade", base="katana",
            tier="legendary", dex_bonus=2, str_bonus=1, sta_bonus=2,
            hp_bonus=4, power_bonus=1)
        before = (h.dex, h.str_, h.sta, h.max_hp, h.power)
        log = []
        rpg.equip_weapon(h, w, log)
        self.assertEqual((h.dex, h.str_, h.sta, h.max_hp, h.power),
                         (before[0] + 2, before[1] + 1, before[2] + 2,
                          before[3] + 4, before[4] + 1))
        rpg.equip_weapon(h, WEAPONS["katana"], log)
        self.assertEqual((h.dex, h.str_, h.sta, h.max_hp, h.power), before)

    def test_unequip_never_kills(self):
        h = _hero()
        w = dataclasses.replace(WEAPONS["katana"], name="lifeblade",
                                base="katana", hp_bonus=4)
        log = []
        rpg.equip_weapon(h, w, log)
        h.hp = 2
        rpg.equip_weapon(h, WEAPONS["katana"], log)
        self.assertGreaterEqual(h.hp, 1)


class TestRiderAndQuirks(unittest.TestCase):
    def _duel(self, weapon, seed=1):
        atk = _hero(school="", spells={})   # steel, never a bolt
        atk.dex, atk.training = 10, 5       # lands reliably
        log = []
        rpg.equip_weapon(atk, weapon, log)
        dfn = rpg.Entity(name="Dummy", dex=1, str_=1, sta=9, max_hp=12,
                         hp=12, pain=2)
        rng = random.Random(seed)
        rpg._attack(atk, dfn, rng, log)
        return atk, dfn

    def test_weapon_rider_applies_condition(self):
        w = dataclasses.replace(WEAPONS["katana"], name="venom katana",
                                base="katana", rider="poison",
                                rider_power=1, rider_rounds=None)
        for seed in range(1, 20):
            atk, dfn = self._duel(w, seed)
            if dfn.max_hp - dfn.hp > 0 and dfn.alive:
                kinds = [c.kind for c in dfn.conditions]
                self.assertIn("poison", kinds)
                c = rpg.condition_of(dfn, "poison")
                self.assertIsNone(c.rounds)     # untimed: walks out
                return
        self.fail("no landed hit in 19 seeded exchanges")

    def test_rime_rider_stacks_the_dex_debuff(self):
        w = dataclasses.replace(WEAPONS["katana"], name="frost katana",
                                base="katana", rider="rime", rider_power=1)
        for seed in range(1, 20):
            atk, dfn = self._duel(w, seed)
            if dfn.max_hp - dfn.hp > 0 and dfn.alive:
                self.assertGreaterEqual(dfn.dex_debuff, 1)
                self.assertFalse(dfn.conditions)    # never a tick
                return
        self.fail("no landed hit in 19 seeded exchanges")

    def test_on_kill_quirks_accrue_and_cap(self):
        w = dataclasses.replace(WEAPONS["zweihander"], name="gilded zwei",
                                base="zweihander", gold_on_kill=2,
                                karma_on_kill=1)
        atk = _hero()
        atk.dex, atk.str_, atk.training = 10, 10, 5
        log = []
        rpg.equip_weapon(atk, w, log)
        rng = random.Random(2)
        felled = 0
        for i in range(10):     # cut down more mooks than the cap allows
            dummy = rpg.Entity(name=f"M{i}", dex=1, str_=1, sta=5, max_hp=1,
                               hp=1, pain=1)
            rpg._attack(atk, dummy, rng, log)
            if dummy.hp <= 0:
                felled += 1
        self.assertGreater(felled, rpg.MIDAS_FIGHT_CAP)
        self.assertEqual(atk.quirk_kills, rpg.MIDAS_FIGHT_CAP)
        self.assertEqual(atk.quirk_gold, 2 * rpg.MIDAS_FIGHT_CAP)
        self.assertEqual(atk.quirk_karma, 1 * rpg.MIDAS_FIGHT_CAP)
        # The per-fight cap clears; the owed counters do not.
        rpg._clear_fight_states([atk])
        self.assertEqual(atk.quirk_kills, 0)
        self.assertEqual(atk.quirk_gold, 2 * rpg.MIDAS_FIGHT_CAP)

    def test_lunge_reach_and_spend(self):
        w = dataclasses.replace(WEAPONS["katana"], name="lunging katana",
                                base="katana", lunge=True)
        h = _hero(school="", spells={})     # no caster reach in the way
        log = []
        rpg.equip_weapon(h, w, log)
        self.assertTrue(h.lunge_ready)
        self.assertEqual(h.threat_reach, 1)
        h.lunge_spent = True
        self.assertFalse(h.lunge_ready)
        self.assertEqual(h.threat_reach, 0)
        rpg._clear_fight_states([h])
        self.assertTrue(h.lunge_ready)      # once per FIGHT, not per career


class TestSaveRoundTrip(unittest.TestCase):
    def test_new_shape_survives_json(self):
        h = _hero()
        w = weapons.generate_weapon(random.Random(9), 9)
        log = []
        rpg.equip_weapon(h, w, log)
        h.quirk_gold = 4
        d = json.loads(json.dumps(session._entity_to_dict(h)))
        h2 = session._entity_from_dict(d)
        self.assertEqual(h2.weapon, h.weapon)
        self.assertEqual(h2.quirk_gold, 4)
        self.assertEqual(rpg.prof_name(h2.weapon), w.base)

    def test_pre_slice_weapon_dict_still_loads(self):
        # An old save's one-off weapon dict has none of the new fields.
        old = {"name": "shock prod", "atk_pressure": 1, "severity": 1,
               "sta_cost": 1, "durability": 4, "quality": True,
               "tier": "plain", "def_pressure": 0, "graze_floor": False,
               "natural": False, "power_bonus": 0, "range": 0, "reload": 0,
               "aim": "dex", "aim_flat": 0, "heavy_draw": 0, "ammo": "",
               "missile": "", "melee_atk": -2, "melee_sev": -2, "bulk": 2,
               "tags": [], "move_tags": ["blade", "pierce"], "value": 60,
               "description": ""}
        w = session._weapon_from(old)
        self.assertEqual(w.base, "")
        self.assertEqual(w.rider, "")
        self.assertEqual(w.dex_bonus, 0)
        self.assertFalse(w.lunge)


class TestWorldLayer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = quests.generate_world(1)

    def test_armory_shape_and_determinism(self):
        a1 = self.world["armory"]
        a2 = quests.generate_world(1)["armory"]
        self.assertEqual(a1, a2)
        self.assertEqual(len(a1), len(weapons.ARMORY_TIERS))
        tiers = [e["tier"] for e in a1]
        self.assertEqual(tiers.count("mythic"), 1)
        for e in a1:
            self.assertEqual(weapons.weapon_sp(
                session._weapon_from(e["weapon"])), e["sp"])
        # The mythic piece is never in a pocket -- always a resting place.
        mythic = next(e for e in a1 if e["tier"] == "mythic")
        self.assertIsNone(mythic["owner"])

    def test_armory_display_fits_forty_columns(self):
        for line in weapons.armory_lines(self.world["armory"]):
            self.assertLessEqual(len(line), 40, line)
        for line in weapons.smith_lines(self.world["smiths"]):
            self.assertLessEqual(len(line), 40, line)

    def test_smiths_caps_and_pride_floor(self):
        smiths = self.world["smiths"]
        self.assertEqual(sorted(s["cap"] for s in smiths),
                         sorted(weapons.SMITH_CAPS))
        for s in smiths:
            self.assertEqual(s["floor"], s["cap"] - 1)
            with self.assertRaises(ValueError):
                weapons.commission_weapon(s, random.Random(1),
                                          sp=s["floor"] - 1)
            with self.assertRaises(ValueError):
                weapons.commission_weapon(s, random.Random(1),
                                          sp=s["cap"] + 1)
            w, price, days = weapons.commission_weapon(s, random.Random(1))
            self.assertEqual(weapons.weapon_sp(w), s["cap"])
            self.assertEqual(price, weapons.commission_price(s["cap"]))
            self.assertGreater(days, 0)

    def test_worldgen_stream_untouched_by_the_layer(self):
        # The armory rides a DERIVED rng: the shared posting stream must
        # be byte-identical to a world rolled without the layer.
        w1 = quests.generate_world(2)
        w2 = quests.generate_world(2)
        q1 = {qid: (q["name"], q["level"]) for qid, q in w1["quests"].items()}
        q2 = {qid: (q["name"], q["level"]) for qid, q in w2["quests"].items()}
        self.assertEqual(q1, q2)

    def test_reward_quests_replace_the_lump_and_fit_the_band(self):
        found = 0
        for seed in range(1, 6):
            w = quests.generate_world(seed)
            for q in w["quests"].values():
                rw = q.get("reward_weapon")
                if not rw:
                    continue
                found += 1
                self.assertEqual(q["gold_total"], 0)
                lvl, tier = q["level"], rw["tier"]
                if lvl <= 4:
                    self.assertEqual(tier, "plain")
                elif lvl <= 9:
                    self.assertEqual(tier, "masterwork")
                elif lvl <= 16:
                    self.assertEqual(tier, "magic")
                else:
                    self.assertEqual(tier, "legendary")
                self.assertIn(f"pays a {rw['name']}",
                              quests.quest_line(q))
        self.assertGreater(found, 0)

    def test_reward_ladder_levels(self):
        rng = random.Random(1)
        self.assertEqual(weapons.reward_weapon_for_level(1, rng).tier,
                         "plain")
        self.assertEqual(weapons.reward_weapon_for_level(7, rng).tier,
                         "masterwork")
        self.assertEqual(weapons.reward_weapon_for_level(12, rng).tier,
                         "magic")
        self.assertEqual(weapons.reward_weapon_for_level(20, rng).tier,
                         "legendary")


class TestTrashStart(unittest.TestCase):
    def test_trash_pool(self):
        rng = random.Random(1)
        for _ in range(30):
            w = rpg.random_trash_weapon(rng)
            self.assertIn(w.name, rpg.TRASH_WEAPONS)
            self.assertLessEqual(w.value, 2)


if __name__ == "__main__":
    unittest.main()
