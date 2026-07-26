"""Contract suite for the QUARTERMASTER PASS (rpg.auto_potions, 2026-07-26):
the out-of-combat potion deal and auto-drink. Pure policy, so it is worth
pinning exactly -- the deal order, the round-robin, the companion tiebreak,
the PC's spell/ability gate, and the thresholds.

`python -m unittest -v test_potions.py`
"""
import unittest

import rpg


def hero(name, *, max_hp=12, hp=None, sta=6, cur_sta=None, pc=False,
         healing=0, stamina=0, spells=None, abilities=()):
    """A bare Entity with only what the pass reads -- no generation rolls, so
    the fixtures stay readable and the assertions stay exact."""
    # __post_init__ fills hp/cur_sta from the maxima, so the current values
    # are set after construction.
    h = rpg.Entity(name=name, dex=5, str_=5, max_hp=max_hp, sta=sta)
    h.hp = max_hp if hp is None else hp
    h.cur_sta = sta if cur_sta is None else cur_sta
    h.protagonist = pc
    h.items = {"healing": healing, "stamina": stamina}
    h.spells = dict(spells or {})
    h.abilities = set(abilities)
    return h


def kit(party, kind):
    return [h.items.get(kind, 0) for h in party]


class DealTests(unittest.TestCase):
    def test_worst_off_first_then_round_robin(self):
        # 5 potions, 3 heroes: the deal laps the party in need order, so the
        # neediest gets 2, the next 2, the healthiest 1.
        party = [hero("Full", hp=12, healing=5),
                 hero("Hurt", hp=2),
                 hero("Scratched", hp=9)]
        moved = rpg.deal_potions(party)
        self.assertEqual(kit(party, "healing"), [1, 2, 2])
        self.assertEqual(moved, 4)          # Full kept 1 and handed over 4

    def test_stamina_deals_on_stamina_not_hp(self):
        party = [hero("Winded", hp=12, cur_sta=1),
                 hero("Bleeding", hp=1, cur_sta=6, stamina=2)]
        rpg.deal_potions(party)
        self.assertEqual(kit(party, "stamina"), [1, 1])

    def test_ties_favor_the_companions(self):
        # Equal need, one potion: the companion is served before the PC.
        party = [hero("PC", hp=5, pc=True, healing=1),
                 hero("Ally", hp=5)]
        rpg.deal_potions(party)
        self.assertEqual(kit(party, "healing"), [0, 1])

    def test_idempotent_and_silent(self):
        party = [hero("PC", hp=4, pc=True, healing=1, stamina=1),
                 hero("Ally", hp=9, healing=1)]
        rpg.deal_potions(party)
        self.assertEqual(rpg.deal_potions(party), 0)

    def test_the_dead_are_dealt_nothing(self):
        party = [hero("Alive", hp=3), hero("Fallen", hp=0, healing=2)]
        party[1].dead = True
        rpg.deal_potions(party)
        self.assertEqual(kit(party, "healing"), [0, 2])   # the deal skips them

    def test_a_lone_hero_keeps_their_own_pack(self):
        party = [hero("Solo", hp=12, healing=3)]
        self.assertEqual(rpg.deal_potions(party), 0)


class TheFallenTests(unittest.TestCase):
    """A dead companion's kit comes back to the party -- the same doctrine
    as the quality steel they leave behind."""

    def test_potions_are_taken_up_and_shared_out(self):
        party = [hero("PC", hp=12, pc=True),
                 hero("Fallen", hp=0, healing=2, stamina=1)]
        party[1].dead = True
        log = []
        rpg.auto_potions(party, log)
        self.assertEqual(party[1].items, {"healing": 0, "stamina": 0})
        self.assertEqual(party[0].items, {"healing": 2, "stamina": 1})
        self.assertTrue([ln for ln in log if "taken up from where they fell"
                         in ln])

    def test_an_empty_pack_is_not_reported(self):
        party = [hero("PC", pc=True, healing=1), hero("Fallen", hp=0)]
        party[1].dead = True
        log = []
        rpg.auto_potions(party, log)
        self.assertEqual(log, [])

    def test_a_wiped_party_recovers_nothing(self):
        party = [hero("PC", hp=0, pc=True, healing=1), hero("Ally", hp=0)]
        for h in party:
            h.dead = True
        self.assertFalse(rpg.auto_potions(party, []))
        self.assertEqual(party[0].items["healing"], 1)


class DrinkTests(unittest.TestCase):
    """`drink=True` is the fight's end and nothing else -- the default pass
    only moves vials around."""

    def test_the_morning_pass_deals_but_never_drinks(self):
        party = [hero("PC", pc=True), hero("Ally", hp=3, cur_sta=1,
                                           healing=2, stamina=2)]
        log = []
        rpg.auto_potions(party, log)        # no drink= : the camp/shop pass
        self.assertEqual(party[1].hp, 3)
        self.assertEqual(party[1].cur_sta, 1)
        self.assertEqual(kit(party, "healing"), [1, 1])
        self.assertFalse([ln for ln in log if "drink" in ln or "downs" in ln])

    def test_companion_drinks_when_badly_hurt_and_when_winded(self):
        party = [hero("PC", pc=True), hero("Ally", hp=3, cur_sta=1,
                                           healing=1, stamina=1)]
        log = []
        self.assertTrue(rpg.auto_potions(party, log, drink=True))
        self.assertEqual(party[1].hp, 3 + rpg.HEALING_POTION_RESTORE)
        self.assertEqual(party[1].cur_sta, 1 + rpg.STAMINA_DRAUGHT_RESTORE)

    def test_nobody_drinks_at_full_the_overcharge_stays_deliberate(self):
        party = [hero("PC", pc=True), hero("Ally", healing=2, stamina=2)]
        log = []
        rpg.auto_potions(party, log, drink=True)    # the kit is shared out...
        self.assertEqual(kit(party, "healing"), [1, 1])
        self.assertEqual(kit(party, "stamina"), [1, 1])
        for h in party:                             # ...and nothing is drunk
            self.assertEqual(h.hp, h.max_hp)
            self.assertEqual(h.cur_sta, h.sta)
        self.assertFalse([ln for ln in log if "drink" in ln or "downs" in ln])

    def test_a_downed_companion_is_stood_up_and_topped_off(self):
        # Deal -> drink -> deal alternates, so one pass can spend several.
        party = [hero("PC", pc=True), hero("Ally", hp=0, healing=3)]
        party[1].down = True
        rpg.auto_potions(party, [], drink=True)
        self.assertFalse(party[1].down)
        self.assertGreater(party[1].hp, party[1].max_hp // 2)

    def test_drinking_stops_at_the_threshold_not_at_the_last_vial(self):
        party = [hero("PC", pc=True), hero("Ally", max_hp=12, hp=6,
                                           healing=4)]
        rpg.auto_potions(party, [], drink=True)
        self.assertEqual(party[1].hp, 11)   # one potion clears half, then stop
        self.assertEqual(sum(kit(party, "healing")), 3)


class PlayerCharacterGateTests(unittest.TestCase):
    """The PC drinks automatically only on a track they have no answer of
    their own for."""

    def test_bare_pc_drinks_both(self):
        party = [hero("PC", hp=3, cur_sta=1, pc=True, healing=1, stamina=1)]
        rpg.auto_potions(party, [], drink=True)
        self.assertEqual(party[0].items, {"healing": 0, "stamina": 0})

    def test_the_healing_spell_holds_the_wound_decision(self):
        party = [hero("PC", hp=3, cur_sta=1, pc=True, healing=1, stamina=1,
                      spells={"healing": 1})]
        rpg.auto_potions(party, [], drink=True)
        self.assertEqual(party[0].items["healing"], 1)   # kept
        self.assertEqual(party[0].items["stamina"], 0)   # drunk

    def test_a_conversion_holds_the_stamina_decision(self):
        for ability in ("war_breath", "berserk"):
            with self.subTest(ability=ability):
                party = [hero("PC", hp=3, cur_sta=1, pc=True, healing=1,
                              stamina=1, abilities=(ability,))]
                rpg.auto_potions(party, [], drink=True)
                self.assertEqual(party[0].items["healing"], 0)   # drunk
                self.assertEqual(party[0].items["stamina"], 1)   # kept

    def test_a_gated_pc_is_still_dealt_potions(self):
        party = [hero("PC", hp=1, pc=True, spells={"healing": 1}),
                 hero("Ally", hp=12, healing=2)]
        rpg.auto_potions(party, [], drink=True)
        self.assertEqual(kit(party, "healing"), [1, 1])

    def test_companions_are_never_gated(self):
        party = [hero("PC", pc=True),
                 hero("Ally", hp=3, cur_sta=1, healing=1, stamina=1,
                      spells={"healing": 3}, abilities=("war_breath",))]
        rpg.auto_potions(party, [], drink=True)
        self.assertEqual(party[1].items, {"healing": 0, "stamina": 0})


class ReportTests(unittest.TestCase):
    def test_a_hand_over_reports_once_and_a_settled_kit_says_nothing(self):
        party = [hero("Brand Ashwood", hp=12, healing=2),
                 hero("Ilse Vahr", hp=4)]
        log = []
        rpg.auto_potions(party, log)
        shares = [ln for ln in log if "shares out its potions" in ln]
        self.assertEqual(len(shares), 1)
        self.assertIn("Ilse Vahr: 1 healing", shares[0])
        log2 = []
        rpg.auto_potions(party, log2)
        self.assertEqual(log2, [])

    def test_the_player_display_stays_inside_the_wrap(self):
        party = [hero("Brand Ashwood", hp=12, healing=3, stamina=3),
                 hero("Ilse Vahr", hp=4),
                 hero("Torbera Hollowmark", hp=6)]
        log = rpg.CombatLog()
        rpg.auto_potions(party, log)
        for line in log.player:
            self.assertLessEqual(len(line), rpg.PLAYER_WIDTH, line)


if __name__ == "__main__":
    unittest.main()
