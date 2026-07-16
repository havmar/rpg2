"""Combat Sim - the mechanics engine.

Implements the ruleset in rules.md (the source of truth for mechanics intent):
the group melee (group_combat), the pause/retreat interrupt layer, weapons and
breakage, ranged combat & the field (distance, shots, cadence, ammo --
rules.md's Ranged Combat add-on), the survival tracks (HP/STA/Power, rests,
the clock), progression
(XP, training, proficiency), the economy (purse, potions, weapons,
spellbooks), random party generation, the Magic & Mind layer (wizards, the
MIND stat, the spell catalog with ranks, the casting check, the openers),
and the batch-sim policies (sim_fight, sim_pause_policy).

What you FIGHT and WHERE lives in sites.py (the foe catalog and the two
hand-built sites); how a playthrough is DRIVEN lives in session.py. This file
stays stdlib-only and self-contained -- everything else imports it.

Run:  python rpg.py [--site hideout] [--seed N]   -> one-shot site run
      (delegates to sites.py, which owns the content; `python sites.py`
      is the same thing)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field


# --------------------------------------------------------------------------- #
# Mechanics
# --------------------------------------------------------------------------- #

WINDED_STA = 3          # STA <= this -> Winded (the warning zone)
WINDED_PENALTY = 2      # roll penalty while Winded
SPENT_PENALTY = 6       # roll penalty at 0 STA (replaces the Winded penalty)

# Stamina economy: ATTACKING is what tires you; defending is reflexive and free.
# STA is the SECOND DEATH-TRACK. An entity that hits 0 STA is SPENT: still
# swinging -- desperation is free -- but at -SPENT_PENALTY to ALL rolls, attack
# and defense alike, until the fight ends (only a pause action -- a draught,
# Berserk, or War-Breath -- can buy STA back mid-fight). Against fresh enemies
# that is a death sentence (can't land, gets carved, wounds spiral on top); two
# spent sides cancel each other's penalties and brawl it out to a real finish,
# so fights RESOLVE rather than stall. HP is how much you can bleed; STA is how
# long you can fight WELL; whichever empties first in reach of a foe kills you.
# Recovery otherwise happens BETWEEN fights, as a sawtooth that trends down
# across the day: +1 when a fight ends, +3 on a short rest, full only on a long
# rest (overnight). Tireless entities (undead) never spend STA and are never
# Winded/Spent.
STA_ATTACK_COST = 1         # STA per swing (the pool is a swing budget now;
                            # halved from 2 when running dry became lethal, so
                            # a hero gets ~5-8 full-strength swings, not 2-3)
STA_RECOVERY_AFTER_FIGHT = 1  # survivors catch their breath when a fight ends

# --- The press (the crowding cap; 2026-07 party-size counterweight) --------- #
# At most this many attackers can press one man-sized target in a round;
# anyone crowded out CIRCLES instead (no swing, no STA -- circling is free,
# like defending). You cannot get four swords around one man. This is the
# in-fight party-size counterweight (the game is balanced for a party of TWO;
# see rules.md "Balanced for two"): it trims the mob-the-mook action economy
# of a big party AND shields a lone hero from being swarmed -- both ends of
# the 1-4 party range move toward the middle with one symmetric rule. Big
# monsters override it per-entity (Entity.crowd_cap: a giant can be pressed
# from all sides), so boss fights stay full-party.
CROWD_CAP = 2

# Survival add-on tunables.
SAVE_COST = 2           # Power spent to reduce one wound tier (Bulwark's mid-fight save)
HEAL_COST = 3           # Power spent on the Heal ability (between fights, see use_heal)
FIRST_BLOOD_COST = 2    # Power spent on First Blood (the rogue's opening strike)
FIRST_BLOOD_HP = 1      # First Blood inflicts a guaranteed graze -- light on purpose
                        # (its real value is the death spiral: -1 to the foe's rolls
                        # all fight), never a free kill
HEAL_RESTORE_RANGE = (1, 3)     # random HP restored per Heal use

# --- Magic & Mind (2026-07-15; grew out of the 2026-07-14 placeholder) ------- #
# Wizards exist from level 1. A character whose MIND is STRICTLY the highest
# of the three creation stats MIND/DEX/STR is a WIZARD (CHA stays social and
# doesn't compete); a wizard rolls a SCHOOL (fire/ice) instead of an ability
# and starts knowing that one spell at rank 1. MIND is the casting stat --
# "the mind", fixed at creation like every stat (the 1-20 doctrine); the
# POWER pool is the FUEL and stays its own rolled thing (qi, not iq --
# designer call 2026-07-15: Power never derives from MIND).
#
# THE SPELL SYSTEM:
# - A wizard knows SPELLS at RANKS 1..3 (SPELL_RANK_MAX). Rank n costs n
#   skill points (train_spell) -- the proficiency chassis wholesale. The
#   first spell is rolled at creation; every further spell needs a
#   SPELLBOOK (learn_spell; bought in a capital, SPELLBOOK_PRICE).
# - AIMED casts (bolts, fireballs, hurled debris) ride the normal exchange:
#   attack pressure = 2d6 + AIM + training + spell rank, where AIM =
#   ceil((MIND + DEX) / 2) -- the mind shapes it, the hand throws it. The
#   defender defends with the body as ever. Severity = margin + the cast's
#   flat (CAST_SEVERITY) - soak; STR and the weapon stay out of it.
# - UNAIMED casts (the openers, the utility spells) roll the CASTING CHECK:
#   2d6 + MIND + rank vs DC = CAST_DC_BASE + CAST_DC_PER_RANK * rank cast.
#   Degrees by margin: miss by 5+ (or snake-eyes) = MISFIRE (Power lost,
#   the action lost, MISFIRE_BACKLASH_HP to the caster); miss = FIZZLE
#   (Power lost, action lost); make it by 0-1 = DOWNGRADE (resolves one
#   rank lower where the spell has one); make it by 2+ = success; by 7+
#   (or boxcars) = CRITICAL (the Power is refunded). MASTERY: casting a
#   technique BELOW your trained rank never rolls -- reliability is what
#   study buys; risk lives at the edge of your art. Snake-eyes on an aimed
#   cast's attack dice is likewise a misfire (magic is the volatile art;
#   steel stays reliable -- the fumble is scoped to casting only).
# - Casting tires like fighting: a cast costs the normal swing STA, and the
#   Power is ammo ON TOP -- never a second endurance pool. A parried or
#   warded cast still burns its Power. Out of Power the wizard swings the
#   weapon in hand and defends normally all along.
# - CONTROL effects (possession; the freeze/knockdown riders) respect
#   SPELL_WARD, the apex monsters' per-row knob (like pain/crowd_cap):
#   ward raises a possession's DC by 2/point, ward >= 2 is immune to
#   stun riders, and ANY ward turns an ambush strike into a normal
#   exchange. The undead/tireless have no living mind: possession-immune.
# - No magic-resistance stat exists: aimed spells are dodged by the body,
#   control is resisted through the DC (training + ward), and the rest is
#   priced in Power. (Design discussion, 2026-07-15.)
BOLT_POWER_COST = 1
SCHOOLS = ("fire", "ice")   # the creation roll (books teach the rest)
SPELL_RANK_MAX = 3
SPELLBOOK_PRICE = 120       # gold; capitals only (session) -- a real saving
                            # goal (two quality weapons)
CAST_DC_BASE = 7
CAST_DC_PER_RANK = 2
MISFIRE_BACKLASH_HP = 1
AMBUSH_MARGIN = 6           # an ambush strike (unseen / a blink at the back /
                            # a stolen moment) auto-wins the exchange at this
                            # margin -- the severity TABLE is the cap: mooks
                            # take a crippling blow, bosses soak and survive.
                            # Any spell_ward turns the ambush into a normal
                            # exchange instead.
# Severity flats per aimed cast kind (replacing STR + weapon severity; the
# spell's rank adds +1 pressure and +1 severity on top, like proficiency).
# fire ~ a solid fighter with military steel; ice is weak on purpose (the
# rime is the point); tk hurls debris; freeze/hurl_foe trade damage for the
# stun rider.
CAST_SEVERITY = {"fire": 5, "ice": 2, "freeze": 2, "tk": 4, "hurl_foe": 3}
CAST_POWER_COST = {"fire": BOLT_POWER_COST, "ice": BOLT_POWER_COST,
                   "freeze": 4, "tk": 2, "hurl_foe": 4, "disarm": 2}
CAST_SPELL = {"fire": "fire", "ice": "ice", "freeze": "ice",
              "tk": "telekinesis", "hurl_foe": "telekinesis",
              "disarm": "telekinesis"}   # cast kind -> the spell whose rank
                                         # applies
ICE_DEX_DEBUFF = 1          # stacking DEX loss per landed ice bolt (per fight)
FREEZE_DEX_DEBUFF = 2       # flash-freeze rimes deeper
FIREBALL_POWER_COST = 4     # fire rank 3's signature: a hero-side sweep
FIREBALL_TARGETS = 3        # ...of up to this many foes (cast vs 3+ foes)
# The openers -- cast at fight start, before the lines meet (First Blood's
# doctrine: automatic while the Power lasts, skipped when the fight is
# already winding down). Cost scales with the rank cast.
OPENER_SPELLS = ("possession", "stop time", "invisibility", "teleport",
                 "flight")      # auto-cast priority order
POSSESSION_POWER_COST = 3       # + rank (4/5/6); puppet fights for you
                                # `rank` rounds. DC + target training
                                # + 2 x ward; the dead have no mind to seize.
STOP_TIME_POWER_COST = 3        # + rank (4/5/6); `rank` stolen strikes
TELEPORT_STRIKE_COST = 3        # the blink at the back (rank 1 technique)
TELEPORT_ESCAPE_COST = 5        # rank 2: the whole party steps through --
                                # no parting blows, no chase
TELEPORT_TRAVEL_COST_PER_DAY = 3  # rank 3: instant travel to a KNOWN
                                  # settlement (session `cast`)
INVISIBILITY_POWER_COST = 3     # rank 1: enter unseen; the first attack is
                                # an ambush and breaks it
VANISH_POWER_COST = 4           # rank 2: the mid-fight re-vanish (a pause
                                # action / standing order)
FLIGHT_POWER_COST = 2           # + rank (3/5): aloft `rank` rounds -- melee
                                # can't reach; bolts and BREATH still can
                                # (fueled sweeps); +1 attack pressure aloft
FLIGHT_ALOFT_ATK = 1
SCRY_POWER_COST = {1: 2, 2: 3, 3: 4}    # utility (session `cast`): next
                                        # room's roster / the whole site /
                                        # the far-seeing (DM-adjudicated)
WIZARD_STAFF_CHANCE = 0.50  # wizards often start with the wooden staff


@dataclass(frozen=True)
class Spell:
    """One spell in the catalog: what each rank does (menu/doc text; the
    behavior itself is engine code keyed by name). `combat` spells act on
    their own inside the autobattle -- a spell is an OPENER, an attack-
    school behavior, or a pause/standing-order action, NEVER a new mid-
    fight decision layer (design rule, 2026-07-15). Utility spells are
    session/DM calls between fights; rank 3 of several spells is the
    roleplay tier the DM adjudicates (dm.md)."""
    name: str
    kind: str               # "attack" | "opener" | "utility"
    blurb: str
    ranks: tuple[str, ...]  # per-rank effect, human-readable
    max_rank: int = SPELL_RANK_MAX


SPELLS = {s.name: s for s in [
    Spell("fire", "attack",
          "The damage school: bolts that hit like heavy steel.",
          (f"firebolt ({CAST_POWER_COST['fire']} Power, severity flat "
           f"+{CAST_SEVERITY['fire']})",
           "+1 bolt pressure & severity (the rank bonus)",
           f"FIREBALL: vs 3+ foes, one roll strikes up to "
           f"{FIREBALL_TARGETS} of them ({FIREBALL_POWER_COST} Power)")),
    Spell("ice", "attack",
          "The control school: weak bolts that RIME (-1 DEX, stacking).",
          (f"icebolt ({CAST_POWER_COST['ice']} Power, flat "
           f"+{CAST_SEVERITY['ice']}, rime -{ICE_DEX_DEBUFF} DEX)",
           "+1 bolt pressure & severity (the rank bonus)",
           f"FLASH-FREEZE: a wounding bolt also freezes the target out of "
           f"its next action (rime -{FREEZE_DEX_DEBUFF}; "
           f"{CAST_POWER_COST['freeze']} Power; ward 2+ is immune)")),
    Spell("telekinesis", "attack",
          "Force at a distance: disarm, hurl debris, hurl people.",
          (f"DISARM: tear an armed foe's weapon away (opposed; "
           f"{CAST_POWER_COST['disarm']} Power; once per foe)",
           f"HURL: fling debris as an aimed strike (flat "
           f"+{CAST_SEVERITY['tk']}, {CAST_POWER_COST['tk']} Power)",
           f"HURL FOE: slam a body off its feet -- a wounding hit also "
           f"costs its next action ({CAST_POWER_COST['hurl_foe']} Power; "
           f"ward 2+ is immune)")),
    Spell("teleport", "opener",
          "Step through space: the blink at the back, the way out, the road "
          "not walked.",
          (f"BLINK STRIKE: open the fight at a foe's back -- an ambush "
           f"strike ({TELEPORT_STRIKE_COST} Power)",
           f"BLINK OUT: retreat with NO parting blows and NO chase "
           f"(`retreat --blink`; {TELEPORT_ESCAPE_COST} Power)",
           f"TRAVEL: step to any settlement the party has visited "
           f"({TELEPORT_TRAVEL_COST_PER_DAY} Power per travel day skipped; "
           f"no road, no interception)")),
    Spell("invisibility", "opener",
          "Unseen until the knife falls. Out of a fight it is the DM's to "
          "adjudicate (sneak, slip past, vanish from a scene).",
          (f"UNSEEN ENTRY: start the fight untargetable; the first attack "
           f"is an ambush strike and breaks it "
           f"({INVISIBILITY_POWER_COST} Power)",
           f"VANISH: re-fade mid-fight (a pause action / standing order; "
           f"{VANISH_POWER_COST} Power)",
           "GHOST-WALK: unseen for a whole scene out of combat "
           "(DM-adjudicated roleplay tier)")),
    Spell("stop time", "opener",
          "The stolen moment: the world hangs while the wizard works.",
          (f"one stolen strike -- an ambush before the lines meet "
           f"({STOP_TIME_POWER_COST + 1} Power)",
           f"two stolen strikes ({STOP_TIME_POWER_COST + 2} Power)",
           f"three stolen strikes ({STOP_TIME_POWER_COST + 3} Power)")),
    Spell("possession", "opener",
          "Seize a living mind: the puppet fights for the party. The dead "
          "and the warded resist (DC + training + 2 x ward).",
          (f"1 round ({POSSESSION_POWER_COST + 1} Power)",
           f"2 rounds ({POSSESSION_POWER_COST + 2} Power)",
           f"3 rounds ({POSSESSION_POWER_COST + 3} Power)")),
    Spell("flight", "opener",
          "The sky is a place to fight from. The full spell (all day, for "
          "good) waits on the ranged-combat model -- rank 3 is not yet "
          "written.",
          (f"SKY-STEP: aloft round 1 -- melee can't reach; bolts and "
           f"breath can; +{FLIGHT_ALOFT_ATK} attack pressure aloft "
           f"({FLIGHT_POWER_COST + 1} Power)",
           f"aloft rounds 1-2 ({FLIGHT_POWER_COST + 2} Power)"),
          max_rank=2),
    Spell("scry", "utility",
          "Sight beyond walls (session `cast HERO scry`).",
          (f"the next room's roster ({SCRY_POWER_COST[1]} Power)",
           f"every room of the active site ({SCRY_POWER_COST[2]} Power)",
           f"the far-seeing: the active quest whole, and DM-adjudicated "
           f"divination ({SCRY_POWER_COST[3]} Power)")),
]}
HEALING_POTION_RESTORE = 5      # HP restored instantly by a healing potion (between fights)
POWER_POTION_RESTORE = 5
STAMINA_DRAUGHT_RESTORE = 4
STA_RECOVERY_BETWEEN_ROOMS = 3   # STA regained per SHORT rest (a real breather, but
                                 # from 0 it only *just* clears Winded with the
                                 # fight-end +1 -- the day still grinds down)
HP_RECOVERY_BETWEEN_ROOMS = 1    # HP regained per SHORT rest (minimal; wounds carry)
POWER_RECOVERY_BETWEEN_ROOMS = 1  # Power regained per SHORT rest (a long rest
                                  # refills it fully -- Power recharges with
                                  # rest, like STA, just never mid-fight)
REVIVE_HP = 1                    # HP a Down hero stands back up with (minimal)

# --- Progression (XP, levels, combat training) ------------------------------ #
# Level L -> L+1 costs XP_LEVEL_STEP * L. A starter-site clear (3 encounters +
# quest at the bandit hideout) is exactly one level-1 level-up; the next level
# takes two clears (or one run at the 3x-paying barrow).
XP_LEVEL_STEP = 100
LEVEL_CAP = 20          # the game runs levels 1-20 (rules.md, the doctrine);
                        # XP past the cap accumulates to no effect
# XP pays the JOB, not the head (2026-07 party-size counterweight): awards are
# quoted at the two-hero baseline and each member earns amount * BASELINE /
# party size. A duo gets the listed numbers unchanged; four swords split the
# wages (level at half speed); a solo who overcomes the same work earns
# double. The economic drag on big parties -- invisible in any one fight,
# compounding across a campaign. Gold already works this way for free (the
# purse is shared, quests pay flat).
XP_PARTY_BASELINE = 2
SKILL_POINTS_PER_LEVEL = 1
# Levels pour into the POOLS (the 1-20 doctrine, rules.md): DEX/STR stay
# fixed at creation forever; each POOL_GROWTH_LEVELS levels add +1 HP, +1 STA,
# +1 Power. Total growth at level L is (L-1) // 2 -- the odd levels (3, 5,
# 7...) each add one -- which is exactly the curve bench_bestiary.py's
# reference parties were calibrated with when it was still applied by hand.
POOL_GROWTH_LEVELS = 2
TRAINING_MAX = 5        # combat training rank cap; each rank = +1 to pressure rolls
                        # (rank n costs n skill points: cheap to start, dear to max)

# --- Gold & the potion economy ---------------------------------------------- #
POTION_KINDS = ("healing", "power", "stamina")  # the full schema use_potion accepts
STOCKED_POTION_KINDS = ("healing", "stamina")   # what creation, drops, and shops
                        # actually circulate: the POWER POTION IS RETIRED from
                        # circulation (design call, 2026-07) -- Power is never
                        # the bottleneck in play, so the slot was dead weight.
                        # Old saves may still carry and drink one; re-add the
                        # kind here if Power ever becomes scarce.
POTION_PRICE = 10       # gold per potion, any kind
STARTING_POTIONS = 2    # random potions rolled at character creation
# The traveling kit (2026-07-11): basic potions replenish THEMSELVES -- every
# long rest tops each living hero back up to the kit line (herbs brewed at the
# camp fire; a vial scrounged or bought with pocket change in town). Design
# call: shopping for the baseline potion was friction, not a choice -- the
# felt game skipped it. `buy` still stocks ABOVE the kit line for a planned
# push; drops still add on top. The kit is deliberately thin (one of each):
# a second draught for the same fight is still something you paid or bled for.
KIT_HEALING = 1         # healing potions each hero wakes with, minimum
KIT_STAMINA = 1         # stamina draughts each hero wakes with, minimum
DROP_POTION_CHANCE = 0.10   # per encounter won: a random potion drops
DROP_GOLD_CHANCE = 0.20     # per encounter won: loose coin drops
DROP_GOLD_AMOUNT = POTION_PRICE // 2

# Site rewards scale with the SITE'S LEVEL, not with which site it happens to
# be (2026-07, the quest system): the level on the board IS the pay grade, so
# beating work above your level pays above your weight class by construction,
# and easy work pays less -- no separate under/over-level bonus needed. The
# anchor: a level-1 site (the bandit hideout: 3 encounters + quest) pays
# exactly the level-1 -> 2 XP cost, so a fresh duo's first clear is a
# level-up. From there pay grows by HALF the anchor per level --
# site_xp_total(L) = SITE_XP_PER_LEVEL * (L + 1) -- while the level cost
# grows by the full step, so leveling SLOWS with rank: one at-level site per
# level at the start, settling toward two. (~35 at-level site clears from 1
# to 20; see bench_quests.py for the measured career pace.)
# Inside a site the hideout's split is kept: ~ENCOUNTER_XP_SHARE of the XP is
# paid room by room as encounters fall, the rest as the site-clear lump.
# THE MOMENTUM STREAK (2026-07-09): the per-encounter share is paid on a
# rising multiplier -- the k-th consecutive encounter cleared IN THE SAME
# SITE without a night's camp between pays (1 + STREAK_STEP*(k-1)) x the
# base. A full one-go run collects exactly ENCOUNTER_XP_SHARE of the site
# total (the anchor is preserved); camping mid-site resets the streak to
# base, so a piecemeal clear pays noticeably less. This is the carrot that
# makes "do the site in one go and budget HP across it" the paying line
# without forbidding the camp -- the site-clear lump (the majority share)
# still requires beating the site either way.
SITE_XP_PER_LEVEL = 50
ENCOUNTER_XP_SHARE = 0.45   # fraction of a site's XP paid per-encounter
STREAK_STEP = 2.0           # per-consecutive-encounter multiplier growth
                            # (x1, x3, x5 across a 3-room site in one go;
                            # raised from 1.0 on 2026-07-10 -- the designer
                            # wanted one-go clears to FEEL like the paying
                            # line: piecemeal now collects ~70% of a site's
                            # total instead of ~78%, and the middle room's
                            # rate -- the wild/off-script anchor, 15 at L1 --
                            # is unchanged by construction)
GOLD_PER_SITE_LEVEL = 15    # a level-L site pays this * L gold on completion
ENCOUNTER_XP = 15       # the flat off-script rate (session `fight N`) -- equals
                        # a level-1 three-room site's MIDDLE (streak-2) award
QUEST_XP = 55           # the level-1 site-clear lump (the hideout's quest pay)
QUEST_GOLD = 15         # the level-1 site's gold (the hideout's quest pay)


def site_xp_total(level: int) -> int:
    """Total XP a level-L site pays (encounters + site-clear lump), quoted at
    the duo baseline like every award."""
    return SITE_XP_PER_LEVEL * (level + 1)


def streak_multiplier(streak: int) -> float:
    """The momentum multiplier for the k-th consecutive encounter cleared in
    the same site without a camp between (k >= 1)."""
    return 1.0 + STREAK_STEP * (max(1, streak) - 1)


def site_encounter_xp(level: int, rooms: int, streak: int = 1) -> int:
    """The per-encounter pay of a level-L site at streak position k: the
    base is sized so a FULL streak (1..rooms in one go) collects exactly
    ENCOUNTER_XP_SHARE of the site total. L1 x 3 rooms pays 5/15/25 in one
    go (sum 45, the hideout's historic share) and 5 per room piecemeal."""
    weights = sum(streak_multiplier(k) for k in range(1, rooms + 1))
    base = site_xp_total(level) * ENCOUNTER_XP_SHARE / weights
    return max(1, round(base * streak_multiplier(streak)))


def site_clear_xp(level: int, rooms: int) -> int:
    """The site-clear (quest) XP lump: whatever a full-streak run's encounter
    awards leave of the site total. L1 x 3 rooms = 55, the hideout's
    historic rate."""
    return site_xp_total(level) - sum(site_encounter_xp(level, rooms, k)
                                      for k in range(1, rooms + 1))


def site_gold(level: int) -> int:
    """Gold a level-L site pays on completion (flat to the party purse).
    L1 = 15 and L3 = 45: both hand-built sites' historic rates."""
    return GOLD_PER_SITE_LEVEL * level

# --- Weapons (Phase 4 first slice) ------------------------------------------ #
# A weapon is an OFFENSE package: it modifies the attack pressure roll, the
# severity of hits that land, and the STA cost per swing. Defense stays the
# body's job (DEX + training) except one deliberate knob (def_pressure: the
# staff's parry, the zweihander's unwieldiness). The design constraint: pressure
# already double-dips (margin feeds severity), so flat attack pressure is the
# rapier's axis and flat severity the zweihander's. NOTE on the sta_cost
# knob: a 2-STA heavy swing was the planned burst mechanic, but the sims
# rejected it -- with Spent lethal, halving the swing budget loses more than
# any severity buys back (see bench_weapons.py / rules.md). It stays in the
# schema at 1 for everything living, for a future with deeper STA pools.
PROFICIENCY_MAX = 3     # per-weapon-type proficiency cap (rank n costs n skill
                        # points): +1 attack pressure AND +1 severity with that
                        # weapon per rank -- narrower than combat training
                        # (offense only, one weapon), so stronger per rank
BROKEN_ATK_PRESSURE = -2   # fighting with the stump of a shattered weapon
BROKEN_SEVERITY = -2
BREAK_CHANCE_PER_GAP_SQ = 0.0025    # per weapon contact (a parry or a Clash):
                                    # P(break) = this * (durability gap)^2 for
                                    # the LOWER-durability weapon only; equal
                                    # durability never breaks. Calibrated so a
                                    # club facing legendary steel snaps in
                                    # roughly a fight in four, and quality
                                    # steel facing better in ~1-2% of fights.
# Starting-weapon table, heroes and bandits alike: mostly crude or soldier's
# steel, the odd heavy piece. Crude starts leave room to feel the upgrade.
CRUDE_WEAPON_CHANCE = 0.50
HEAVY_WEAPON_CHANCE = 0.05
HEALER_STAFF_CHANCE = 0.50  # heal-ability heroes often carry the wooden staff

# --- Ranged combat (2026-07-16) ---------------------------------------------- #
# The distance model: every fight opens across a FIELD (an abstract gap in
# "bounds" -- one round's movement each). Each entity carries an `adv`
# counter, steps taken from its own line; the gap between two OPPOSING
# entities is max(0, field - a.adv - b.adv) -- one small int per body, no
# coordinates, no pairs. Field 0 (the default everywhere the caller doesn't
# say otherwise) is today's fight to the digit: the lines meet at the door.
#
# The rules, all riding that one number:
# - MOVING IS YOUR ACTION. An entity with no enemy inside its reach advances
#   one step instead of attacking (free, like circling -- no STA). Both
#   sides advancing close the gap by 2 a round. Nobody falls back (v1: no
#   kiting -- shooters hold their ground; leaving is the retreat layer).
# - Melee weapons reach gap 0 only. RANGED weapons reach their card's range
#   but are USELESS at gap 0: a foe at arm's length forces the shooter to
#   spend a round switching to the card's melee grip (melee_atk/melee_sev --
#   one weapon, two lines, no inventory). Aimed CASTS reach CAST_RANGE at
#   ANY gap including 0 -- magic doesn't jam at contact (this keeps every
#   caster bench meaningful and pre-ranged fights identical).
# - A shot rides the normal exchange: 2d6 + AIM + training + weapon atk +
#   proficiency vs the body's defense WITHOUT the weapon's parry knob (you
#   don't parry an arrow with a stick; the armored trait still counts).
#   Severity = margin + the card's flat - soak, STR out (like a cast) --
#   the bow's STR share lives in its AIM instead. Shots cost the normal
#   swing STA (a war draw is work); no steel-on-steel breakage, no rapier
#   floors, and the universal margin-3 graze floor applies.
# - CADENCE: after each shot the card's `reload` rounds must pass (nocking,
#   cranking, recharging) before the next -- reload ticks on any round the
#   shooter doesn't fire, movement included. The revolver's whole identity
#   is reload 0.
# - AMMO is a carried count in Entity.items ("arrows"/"bolts"/"shells"/
#   "knives"); the sling scrounges stones (free) and the revolver fires
#   Power itself (REVOLVER_POWER_COST a shot -- the spell-bolt economy).
#   Ammo is spent hit or miss; a WON field is scavenged (recover the spent
#   missiles at RECOVER_HIT/RECOVER_MISS rates -- a stuck arrow is easier
#   to find than a lost one); a fled field is left, arrows and all.
# - The press is melee geometry: shooters at range neither consume nor
#   respect crowd room -- and a melee attacker crowded out of the press
#   with the field still open ADVANCES instead of circling, slipping
#   toward the backline (the archer's escort problem, emergent).
ROOM_FIELD = 2      # site/quest rooms: close quarters -- a hall's width, one
                    # approach round, at most one shot loosed indoors
WILD_FIELD = 3      # the open road: the widest common engagement -- a
                    # longbow's whole reach, ~2 shots before contact
CAST_RANGE = 2      # how far every aimed cast carries (bolts, fireballs,
                    # hurled debris) -- and casts alone also work at gap 0
REVOLVER_POWER_COST = 1     # the magic gun fires the wielder's own Power
FOE_AMMO = 8        # what a spawned shooter carries (plenty for one fight)
AMMO_CAPS = {"arrows": 20, "bolts": 20, "shells": 10, "knives": 6}
# `buy HERO arrows|bolts|shells|knives`: (lot size, lot price in gold).
# Arrows are deliberately trivial next to the 60g bow -- the recurring sink
# with real teeth is the blunderbuss shell (the design's own compensation:
# the weapon needs no stats, so the ammo carries the price).
AMMO_LOTS = {"arrows": (10, 5), "bolts": (10, 5),
             "shells": (2, 10), "knives": (2, 4)}
RECOVER_HIT = {"arrows": 0.70, "bolts": 0.70, "knives": 0.90}
RECOVER_MISS = {"arrows": 0.40, "bolts": 0.40, "knives": 0.60}
# Starter load included with a bought/granted ranged weapon (nobody sells a
# bow without a quiver); tops UP to this, never past the cap.
STARTER_AMMO = {"arrows": 10, "bolts": 10, "shells": 2, "knives": 4}

# --- Engagement: who notices whom (2026-07-16) -------------------------------- #
# The road's spotted/ambush valve (quests.py) decides WHO saw WHOM first;
# these are its new inputs. A side's CONSPICUOUSNESS is what there is to
# notice: bodies, glint, noise -- group size, plus a point per showy trait,
# plus a clumsy-stealth point when its WORST DEX drags (stealth is a
# weakest-link property). NOTICING is the other side's roll against it:
# 2d6 + notice stat vs NOTICE_BASE + conspicuousness. The party watches
# with its best MIND (the watchful mind reads the land -- MIND's third
# everyday job, after casting and quest sight); beasts and foes sense with
# the sharper of MIND and DEX. Whoever notices first picks the engagement:
# shooters open at their range, an unseen melee side closes to contact.
NOTICE_BASE = 8
STEALTH_DEX_BASE = 4        # a group's worst DEX below this adds the gap
                            # to its conspicuousness (someone keeps snapping
                            # twigs)
CONSPICUOUS_TRAITS = ("armored", "loud", "colorful", "flamboyant",
                      "luxurious")   # presentation traits that catch the eye
                                     # (people.py's dress/voice tables)


def conspicuousness(group) -> int:
    """How much there is to notice about a group: size + showy traits +
    the clumsy-stealth term off its worst DEX. Duck-typed (needs .dex and
    .traits or neither) so it prices hero parties and FoeSpec rows alike."""
    living = [e for e in group if getattr(e, "hp", 1) > 0]
    if not living:
        return 0
    score = len(living)
    score += max(0, STEALTH_DEX_BASE - min(e.dex for e in living))
    for e in living:
        traits = getattr(e, "traits", None) or {}
        score += sum(1 for t in traits.values()
                     if t.split(" (")[0] in CONSPICUOUS_TRAITS)
    return score


@dataclass(frozen=True)
class Weapon:
    """An offense package plus flavor. `tier` is craftsmanship: "plain" is
    never shown to the player (a rapier is just 'a rapier'); masterwork and
    legendary are found/quested, never shopped. `quality` marks the cool,
    culturally-significant weapons vs common arms. `bulk` is stored but inert
    (heroic tone, no encumbrance -- see rules.md's design spine; if carrying ever matters it
    becomes STR's secondary role). `tags` drive generation flavor."""
    name: str
    atk_pressure: int          # attack pressure roll modifier (attack only, never defense)
    severity: int           # flat severity modifier on hits that land
    sta_cost: int           # STA per swing (the burst/sustain knob)
    durability: int         # 1 crude .. 6 legendary; the lower may shatter on contact
    quality: bool = False
    tier: str = "plain"     # plain | masterwork | legendary (plain is unlabeled in play)
    def_pressure: int = 0      # defense pressure modifier (the staff's parry niche;
                            # negative for the zweihander -- no parrying a girder)
    graze_floor: bool = False   # the rapier: a landed hit is never fully
                                # deflected -- the point finds a seam (min. a
                                # graze), so soak can't zero the chip damage
    natural: bool = False   # fangs, claws, tusks -- part of the body: never
                            # breaks, never breaks steel (breakage is a
                            # steel-on-steel event; see _check_weapon_break),
                            # never left as loot
    heal_bonus: int = 0     # extra HP per Heal ability use (the staff)
    # Ranged cards (2026-07-16; see the ranged-combat constants block).
    # range 0 = a melee weapon (everything above); range N = shoots targets
    # at gap 1..N and is USELESS at gap 0 (the melee grip below takes over
    # after a switch round).
    range: int = 0          # how far the card shoots (in field steps)
    reload: int = 0         # rounds between shots (0 = every round; 1 = the
                            # bow's every-2nd-round nock; ticks whenever the
                            # shooter doesn't fire)
    aim: str = "dex"        # the shot's attack stat: "dex" (guns, thrown),
                            # "dex_str" (bows: ceil((DEX+STR)/2) -- the draw
                            # is strength, the loose is aim), or "flat"
                            # (the blunderbuss: the spread does the aiming)
    aim_flat: int = 0       # the "flat" aim's fixed stat term
    heavy_draw: int = 0     # STR below this cranks slowly: +1 reload (the
                            # crossbow's strength gate lives in cadence, not
                            # accuracy)
    ammo: str = ""          # carried-count key in Entity.items ("arrows" /
                            # "bolts" / "shells" / "knives"), "power" (the
                            # revolver fires the wielder's own Power), or
                            # "" (the sling scrounges stones -- free)
    missile: str = ""       # what the log says flew ("arrow", "bolt", ...)
    melee_atk: int = BROKEN_ATK_PRESSURE    # the card's own melee line, used
    melee_sev: int = BROKEN_SEVERITY        # after the switch at contact --
                            # a bow swung as a stave is a broken-weapon
                            # stump; a blunderbuss stock clubs honestly.
                            # No proficiency applies (you drilled the shot,
                            # not the club).
    bulk: int = 1           # carry weight/bulk -- stored, unused for now
    tags: tuple[str, ...] = ()
    value: int = 0          # gold
    description: str = ""   # the mechanical role in plain words (DM/player-facing)


WEAPONS = {w.name: w for w in [
    # Crude commons -- cheap, everywhere, and a liability against real steel.
    Weapon("club", 0, -1, 1, durability=1, bulk=2, tags=("cheap",), value=1,
           description="A length of hard wood. Hits soft and snaps on real steel."),
    Weapon("dagger", 0, -1, 1, durability=1, bulk=1, tags=("cheap",), value=2,
           description="A knife for close, mean work. Easy to carry, shallow wounds."),
    Weapon("whip", 0, -1, 1, durability=1, bulk=1, tags=("cheap",), value=2,
           description="Stings and startles; opens nothing that bone or mail resists."),
    Weapon("light hammer", 0, -1, 1, durability=1, bulk=2, tags=("cheap",), value=2,
           description="A workman's tool pressed into service."),
    # Soldier's arms -- proper military steel; the baseline weapons.
    Weapon("shortsword", 0, 0, 1, durability=2, bulk=1, tags=("military",), value=8,
           description="The soldier's standard sidearm. No strengths, no flaws."),
    Weapon("scimitar", 0, 0, 1, durability=2, bulk=1, tags=("military",), value=8,
           description="A curved cutting sword. Honest cavalry steel."),
    Weapon("spear", 0, 0, 1, durability=2, bulk=2, tags=("military",), value=5,
           description="The oldest soldier's weapon there is. Plain and serviceable."),
    Weapon("mace", 0, 0, 1, durability=2, bulk=2, tags=("military",), value=8,
           description="A flanged iron head on a haft. Simple, brutal, dependable."),
    Weapon("flail", 0, 0, 1, durability=2, bulk=2, tags=("military",), value=8,
           description="A swung head on a chain. Loud, showy, workmanlike."),
    Weapon("morningstar", 0, 0, 1, durability=2, bulk=2, tags=("military",), value=8,
           description="A spiked head that punishes whatever it touches."),
    # Heavy arms -- military steel with real weight behind the blow.
    Weapon("longsword", 0, 1, 1, durability=2, bulk=2, tags=("military",), value=15,
           description="A knight's cruciform sword. Heavier steel, deeper wounds."),
    Weapon("battleaxe", 0, 1, 1, durability=2, bulk=2, tags=("military",), value=15,
           description="A bearded axe that bites deep when it lands."),
    Weapon("warhammer", 0, 1, 1, durability=2, bulk=3, tags=("military",), value=15,
           description="Armor-cracking weight on a short haft."),
    Weapon("halberd", 0, 1, 1, durability=2, bulk=3, tags=("military",), value=15,
           description="The guard's pole-arm: axe, hook, and spike on six feet of ash."),
    # The quality four -- culturally significant weapons; each suits a build.
    # (Profiles are sim-tuned: see bench_weapons.py. The zweihander's burst
    # identity lives in the guard penalty, NOT a 2-STA swing cost -- that was
    # tried and is a death trap while Spent is lethal; the sta_cost knob
    # stays in the schema for a future with deeper STA pools.)
    Weapon("rapier", 2, -1, 1, durability=4, quality=True, bulk=1, value=60,
           graze_floor=True,
           description="A duelist's blade: lands constantly, cuts shallow, and "
                       "ALWAYS draws blood -- a landed thrust is never fully "
                       "deflected. Wins through the wound spiral; laughs at "
                       "heavy soak."),
    Weapon("katana", 1, 1, 1, durability=4, quality=True, bulk=2, value=60,
           description="The balanced blade: lands a little more, cuts a little "
                       "deeper. At home in any strong hand."),
    Weapon("zweihander", 1, 3, 1, durability=4, quality=True, def_pressure=-1,
           bulk=4, value=60,
           description="Two-handed war steel: every hit lands a tier harder "
                       "and mooks die in one blow, but there is no parrying "
                       "with a girder (-1 on defense). Wants STR and soak "
                       "behind it; the crowd-breaker."),
    Weapon("wooden staff", 0, -1, 1, durability=3, quality=True, def_pressure=1,
           heal_bonus=1, bulk=2, value=60,
           description="A healer's iron-shod staff: poor on the attack, +1 to "
                       "the parry, and Heals through it restore +1 HP."),
    # Ranged commons -- cheap missiles for whoever can't afford real reach.
    # (Severity flats run higher than melee cards because a shot's severity
    # replaces STR entirely, like a cast: a card's flat IS the whole punch.)
    Weapon("sling", -1, 3, 1, durability=1, bulk=1, tags=("cheap", "ranged"),
           value=2, range=2, reload=1, aim="dex", missile="sling stone",
           description="A strap and a stone. Weak, slow, free to feed -- "
                       "stones are everywhere -- and it still outranges a "
                       "knife."),
    Weapon("throwing knives", 0, 2, 1, durability=2, bulk=1,
           tags=("military", "ranged"), value=8, range=1, reload=0,
           aim="dex", ammo="knives", missile="thrown knife",
           melee_atk=0, melee_sev=-1,
           description="A brace of balanced knives: one every round, short "
                       "reach, shallow cuts -- and most are picked back up "
                       "after. In a closed fist it is still a knife."),
    Weapon("shortbow", 0, 4, 1, durability=2, bulk=2,
           tags=("military", "ranged", "bow"), value=8, range=2, reload=1,
           aim="dex_str", ammo="arrows", missile="arrow",
           description="A hunter's bow: honest reach, honest wounds. Draw "
                       "and aim both count -- AIM is the mean of DEX and "
                       "STR."),
    Weapon("crossbow", -1, 6, 1, durability=2, bulk=3,
           tags=("military", "ranged"), value=15, range=2, reload=1,
           heavy_draw=4, aim="dex", ammo="bolts", missile="bolt",
           description="A heavy bolt that punches like a lance when it "
                       "lands -- and it is easy to miss with. Weak arms "
                       "(STR under 4) crank it a round slower."),
    # The quality ranged three -- reach as a build, not a sidearm.
    Weapon("longbow", 1, 5, 1, durability=4, quality=True, bulk=3,
           tags=("ranged", "bow"), value=60, range=3, reload=1,
           aim="dex_str", ammo="arrows", missile="arrow",
           description="A war bow with the whole field for a killing "
                       "ground: the longest reach there is (range 3). AIM "
                       "is the mean of DEX and STR -- the draw is strength, "
                       "the loose is aim."),
    Weapon("blunderbuss", 0, 7, 1, durability=4, quality=True, bulk=3,
           tags=("ranged", "gun"), value=90, range=1, reload=1,
           aim="flat", aim_flat=4, ammo="shells",
           missile="thundering blast", melee_atk=0, melee_sev=0,
           description="Dwarven thunder in a brass throat: the spread does "
                       "the aiming (a flat 4 -- no stats needed) and what "
                       "it hits it ruins, one bound away at most. The "
                       "shells cost real gold, and the stock clubs "
                       "honestly when they close."),
    Weapon("revolver", -1, 5, 1, durability=4, quality=True, bulk=1,
           tags=("ranged", "gun", "dwarven"), value=250, range=2, reload=0,
           aim="dex", ammo="power", missile="shot",
           description="A dwarven magic gun: no powder, no reloading -- "
                       "every round, while the wielder's own Power lasts "
                       "(1 a shot). Hard to aim (-1) and unforgiving of "
                       "clumsy hands; wants high DEX. Sold only where "
                       "dwarves sell."),
]}

CRUDE_WEAPONS = ("club", "dagger", "whip", "light hammer")
SOLDIER_WEAPONS = ("shortsword", "scimitar", "spear", "mace", "flail", "morningstar")
HEAVY_WEAPONS = ("longsword", "battleaxe", "warhammer", "halberd")
QUALITY_WEAPONS = ("rapier", "katana", "zweihander", "wooden staff",
                   "longbow", "blunderbuss", "revolver")
RANGED_WEAPONS = ("sling", "throwing knives", "shortbow", "crossbow",
                  "longbow", "blunderbuss", "revolver")

# The skeletons' grave-goods: corroded, durability 1 -- they snap on good steel,
# which is the intended player-favoring asymmetry once the party earns quality.
RUSTED_BLADE = Weapon("rusted blade", 0, 0, 1, durability=1, tags=("ancient",),
                      value=0,
                      description="Grave-steel eaten by centuries. Snaps on honest metal.")


def random_common_weapon(rng: random.Random) -> Weapon:
    """The starting/mook weapon roll: 50% crude, 45% soldier's arms, 5% heavy.
    Always a specific named weapon, never a generic 'crude weapon'."""
    r = rng.random()
    if r < CRUDE_WEAPON_CHANCE:
        pool = CRUDE_WEAPONS
    elif r < CRUDE_WEAPON_CHANCE + HEAVY_WEAPON_CHANCE:
        pool = HEAVY_WEAPONS
    else:
        pool = SOLDIER_WEAPONS
    return WEAPONS[rng.choice(pool)]


# --- Time economy (the clock) ---------------------------------------------- #
# A "day" is a slot budget, not a wall clock. The party gets a limited number of
# SHORT rests -- each ~ an hour or two of narrative time -- between fights; when
# those run out there is no more mid-day recovery and the party must make camp
# for a LONG rest (overnight). Nothing forces the day's end: long_rest() is a
# function Claude calls on purpose (see the module docstring / develop.md), never
# automatic. A long rest recharges STA and Power fully and knits HP back at a
# per-character weekly rate (~max_hp / 7 per night -> roughly a week to heal).
SHORT_RESTS_PER_DAY = 1          # short-rest slots available each day (cut from
                                 # 2 in the 2026-07 lethality retune: one
                                 # breather a day, then you press on or camp)

# --- The tavern night (2026-07-10) ------------------------------------------ #
# A settlement's paid alternative to the free camp: a long rest plus a hot
# meal and a real bed. The party wakes OVERCHARGED -- current HP and STA a
# fraction ABOVE their maxima ("13/12 HP") -- a one-day edge for the door
# they walk through tomorrow. The excess is spent normally and can never be
# recovered (every recovery path tops up TOWARD max, never past it -- see
# recover()); whatever is left is clamped away by the next long rest. Session
# play gates it to settlements (`tavern`); camping in the wilds is free but
# risks a night encounter (quests.CAMP_ENCOUNTER_CHANCE).
TAVERN_COST_PER_HERO = 1    # gold per living member, per night
TAVERN_OVERCHARGE = 0.10    # overcharge fraction of each maximum (min +1)

# --- Charisma & the party cap (2026-07-11) ----------------------------------- #
# CHA is the fourth hero stat, rolled on the DEX/STR band. Its two jobs:
# it gates how many companions the party can HOLD (capacity = CHA - 3,
# clamped 0..3: a minimum roll travels alone -- a hard cap, not a price),
# and the PC's CHA talks quest pay up (gold only, never XP -- a compounding
# XP bonus would make CHA the best stat in the game, and levels already
# dominate everything). Sims never roll heroes through the people layer and
# never set `protagonist`, so neither knob moves a single bench number.
HERO_CHA_RANGE = (3, 6)         # rolled like DEX/STR; racial mods raise the
                                # FLOOR of this range, never the ceiling
                                # (people.py -- the natural cap 6 holds)
PARTY_CAPACITY_BASE_CHA = 3     # capacity = CHA - this, clamped to 0..3
PARTY_CAPACITY_MAX = 3          # the party tops out at 4 swords (PC + 3)
CHA_GOLD_BONUS_PER_POINT = 0.10  # +10% quest gold per PC CHA point above the
CHA_GOLD_BONUS_CAP = 0.30        # capacity base, capped at +30% (CHA 6)


def party_capacity(cha: int) -> int:
    """How many companions a leader with this CHA can hold (and how many
    candidates a tavern evening turns up)."""
    return max(0, min(PARTY_CAPACITY_MAX, cha - PARTY_CAPACITY_BASE_CHA))


# --- Companion satisfaction (2026-07-11) -------------------------------------- #
# Every hired companion carries a satisfaction track (0..10, PC excluded --
# Entity.satisfaction stays None for the PC, foes, and every sim entity, so
# the engine benches never see it). It rises with success and comfort, falls
# with blood and fear, and at 0 the companion quits at the next settlement,
# walking off with an equal head-split of the purse. This is the
# counter-pressure to the momentum streak: the streak pays the party to push
# on; satisfaction pays it to stop, sleep warm, and spend days off. There is
# deliberately NO pay-to-raise knob (designer call, 2026-07-11: logical but
# unfun) -- success, tavern nights, and downtime to a companion's liking are
# the levers.
SATISFACTION_MAX = 10
SATISFACTION_START = 7          # a fresh hire: content, not devoted
SATISFACTION_WARN = 3           # at/below: the "gone quiet" warning fires
SATISFACTION_FLOOR = -3         # the track's hard floor; also where a LOYAL
                                # companion finally leaves (others leave at 0)
SAT_SITE_CLEAR = 1              # a site/quest lump paid out (award_quest)
SAT_TAVERN = 1                  # a warm bed and a hot meal (tavern night)
SAT_DOWNTIME = 1                # a day off in a settlement...
SAT_DOWNTIME_MATCH = 2          # ...doubled-ish when it suits their traits
                                # (interest/patriotic/religious -- people.py)
SAT_FLED = -1                   # the party ran (injury-scaled: see below)
SAT_BLOODIED = -1               # ended a fight below half HP
SAT_DOWN = -2                   # hit the floor
SAT_DEATH_WITNESS = -2          # watched a party member die this fight
# The injury-side events scale with temperament: COWARDLY doubles them,
# BRAVE halves them (rounding toward zero -- a brave companion shrugs off
# a -1 entirely). Applied in adjust_satisfaction(injury=True).

# The "needs meds" weakness (people.py rolls it): a dose must be bought in a
# CAPITAL every MEDS_INTERVAL_DAYS days (session `buy HERO meds`, tracked on
# Entity.last_dose_day) or the companion's satisfaction drains 1 per night.
MEDS_INTERVAL_DAYS = 10
MEDS_PRICE = 20                 # deliberately dear (two potions a dose)

# --- The mid-fight pause (the interrupt primitive) --------------------------- #
# group_combat can PAUSE at a trigger and resume: the "do I fight on?" decision
# surfaced BEFORE Spent, where play never had it. Triggers watch the party side
# only, at the end of a round, and each (kind, hero) pair fires at most once
# per fight (per hero, so one hero's crisis never consumes the other's
# warning). CROSSING-ONLY (2026-07): a trigger whose condition already
# holds when the fight starts is marked spent silently -- entering low was the
# player's informed choice at the door, so only an IN-FIGHT crossing
# interrupts (a wounded day no longer re-asks the same question every fight).
# At the pause the choices are: fight on (resume), a pause ACTION per hero --
# drink a stamina draught or healing potion mid-fight, or one of the resource
# conversions below -- or retreat. Every pause action costs that round's
# attack and the hero defends at a penalty while occupied: vulnerable, not
# helpless. Mid-fight drinking un-Spends a fighter at 0 STA -- bought at a
# real price.
#
# STANDING ORDERS (2026-07-11): with 3-4 party members the per-hero triggers
# made a long fight stop up to 2N times, each a full chat round-trip -- the
# designer wants AT MOST ONE pause per encounter. The engine now takes a
# `standing_orders` callback deciding each crossing: interrupt ("pause"),
# auto-act (a pause-action string, executed at the top of the next round at
# the usual price), or fight on (None). Session play interrupts only on the
# FIRST wounds crossing of the fight -- the "someone is being cut apart, do
# we retreat?" question, which belongs to the player -- and answers every
# other crossing with the standing order (drink / convert, skipped when the
# fight is already winding down -- see fight_winding_down). The sims pass no
# callback and keep the old every-crossing pause, so sim_pause_policy answers
# exactly what it always answered.
PAUSE_STA_TRIGGER = 2       # a hero at/below this STA at round end -> pause
PAUSE_HP_FRACTION = 0.5     # a hero at/below this fraction of max HP -> pause
PAUSE_ACTION_DEF_PENALTY = 2    # the busy hero's defense penalty that round

# Retreat & chase. Deliberately ONE roll -- no multi-message chase scenes.
# Breaking contact: every foe fit to swing (alive, not Winded, not Spent) gets
# one free parting blow at the fleeing party (defended at
# -PAUSE_ACTION_DEF_PENALTY; free like the dying swing -- no STA cost). Then
# ONE opposed group contest -- 2d6 + side-average DEX weighted by current STA
# -- decides the break; the fleeing side adds FLEE_BONUS (the runner picks the
# moment and the ground). Success = clean escape; failure = rare and
# catastrophic (the fight resumes with the parting-blow damage already taken).
# Entities with pursues=False (the barrow's undead -- bound to the grave)
# still swing at the door but never give chase: retreat from the barrow
# always succeeds once past it.
FLEE_BONUS = 2

# --- Resource conversions (they ride the same pause) ------------------------- #
# STA is the scarce, dynamic track; HP and Power mostly sit idle. Both
# conversions are pause-menu actions with the drink's exact shape (skip the
# attack, defend at -PAUSE_ACTION_DEF_PENALTY that round). Numbers are
# provisional, sim-tuned like every other constant.
BERSERK_HP_COST = 2         # Berserk: bleed HP for STA. The HP loss also
BERSERK_STA_GAIN = 4        # deepens the wound spiral -- the real price.
WAR_BREATH_POWER_COST = 2   # War-Breath: spend Power for STA -- a fighter's
WAR_BREATH_STA_GAIN = 3     # breath discipline, not wizardry.
PAUSE_ACTIONS = ("drink", "heal", "berserk", "war-breath", "vanish")
# "vanish" is invisibility rank 2's mid-fight re-fade (VANISH_POWER_COST
# Power at the same pause-action price): the wizard drops out of every
# foe's reach until their next attack, which strikes as an ambush.

# The universal graze floor: win the exchange by at least this margin and the
# hit always draws blood (min. a graze), no matter the soak. Without it a
# high-STR frame is unwoundable by weak foes until fatigue collapses its pressure
# -- the party literally could not be injured before its stamina broke, which
# made HP dead weight (design note, 2026-07). Soak still gates the REAL wound
# tiers; this only stops chip damage from being zeroed on a clean win. The
# rapier's own graze_floor is stricter still (any landed hit).
GRAZE_FLOOR_MARGIN = 3

# Wound tiers as an ordered ladder, so a save can step a blow down one notch.
# The top tier was renamed "killing blow" -> "crippling blow" (2026-07-10):
# it is 6 flat HP and only kills when it drops you to 0 unsaved, but the old
# name read as an instant kill at the table. Same mechanic, honest name.
TIER_ORDER = ["deflected", "graze", "wound", "grievous", "crippling blow"]
TIER_HP = {"deflected": 0, "graze": 1, "wound": 2, "grievous": 4, "crippling blow": 6}

# --- Log vocabulary (the interpretive layer) -------------------------------- #
# Every exchange logs two layers: a catchy headline (what a watcher would say)
# and the raw numbers beneath it (every die, modifier, and source). See
# rules.md "Reading the combat log".
TIER_PHRASE = {"graze": "a graze", "wound": "a solid wound",
               "grievous": "a grievous injury", "crippling blow": "a crippling blow"}

# Tie on the pressure roll: high dice = furious contact, low dice = cagey circling.
TIE_HIGH_DICE = 8       # either side's raw 2d6 at/above this -> "Clash", else "Lull"


class CombatLog(list):
    """The two-level combat log (2026-07). The list itself IS the full log --
    every headline plus the raw numbers, the debug/DM layer, unchanged in
    format -- while `.player` collects a parallel simplified version meant to
    be pasted into the chat as-is (headlines with the HP loss folded in, no
    pressure/severity arithmetic, no per-round stamina readout).

    Emitters:
      log.append(line)      -> both levels (headlines, falls, banners, ...)
      log.debug(line)       -> full log only (dice math, stamina readouts)
      log.play(full, plyr)  -> divergent wording per level

    Engine code emits through the _debug/_play helpers below so a plain
    list[str] still works everywhere (it then just receives the full log --
    the bench harnesses pass throwaway lists)."""

    def __init__(self, lines=()):
        super().__init__(lines)
        self.player: list[str] = []

    def append(self, line: str) -> None:
        super().append(line)
        self.player.append(line)

    def debug(self, line: str) -> None:
        super().append(line)

    def play(self, full_line: str, player_line: str) -> None:
        super().append(full_line)
        self.player.append(player_line)


def _debug(log: list[str], line: str) -> None:
    """Full-log-only line (raw numbers). No-op difference on a plain list."""
    (log.debug if isinstance(log, CombatLog) else log.append)(line)


def _play(log: list[str], full_line: str, player_line: str) -> None:
    """Two wordings, one event. A plain list gets the full wording."""
    if isinstance(log, CombatLog):
        log.play(full_line, player_line)
    else:
        log.append(full_line)


CAST_LABEL = {"fire": "fire bolt", "ice": "ice bolt",
              "freeze": "flash-freeze", "tk": "hurled debris",
              "hurl_foe": "telekinetic slam", "disarm": "telekinetic grip"}


def kind_label(kind: str) -> str:
    """Log/menu name for an aimed cast kind."""
    return CAST_LABEL[kind]


def _an(noun: str) -> str:
    """'an arrow', 'a bolt' -- the log's article helper."""
    return ("an " if noun[:1].lower() in "aeiou" else "a ") + noun


def margin_verb(margin: int) -> str:
    """How decisively the exchange was won, as a verb for the headline."""
    if margin >= 5:
        return "overwhelms"
    if margin >= 3:
        return "outmaneuvers"
    return "edges past"


def wound_tier(severity: int) -> tuple[str, int]:
    """Map a severity score to (tier name, HP lost)."""
    if severity <= 0:
        return ("deflected", TIER_HP["deflected"])
    if severity <= 2:
        return ("graze", TIER_HP["graze"])
    if severity <= 4:
        return ("wound", TIER_HP["wound"])
    if severity <= 6:
        return ("grievous", TIER_HP["grievous"])
    return ("crippling blow", TIER_HP["crippling blow"])


def reduce_tier(tier: str) -> tuple[str, int]:
    """Step a wound down one tier (a Heal/Bulwark save). Floors at deflected."""
    i = TIER_ORDER.index(tier)
    new = TIER_ORDER[max(0, i - 1)]
    return new, TIER_HP[new]


def recover(cur: int, gain: int, cap: int) -> int:
    """The one recovery clamp: gain toward cap, never DOWN to it. A pool
    already at/over its max (the tavern's overcharge) keeps its excess --
    recovery just can't add to it. Every top-up path (rests, potions, pause
    drinks, conversions) goes through this so overcharge is spent-only."""
    if cur >= cap:
        return cur
    return min(cap, cur + gain)


@dataclass
class PressureRoll:
    """One pressure roll with its full breakdown, so the log can expose every
    modifier and its source (the mechanics layer of the two-layer log)."""
    total: int
    dice: int           # the raw 2d6 sum
    dex: int            # the stat term: DEX normally, AIM (the MIND/DEX
                        # mean) on a cast (stat_label says which)
    training: int
    wound_pen: int      # HP lost so far (the death spiral)
    fatigue_pen: int    # SPENT_PENALTY at 0 STA, else WINDED_PENALTY if
                        # Winded, else 0 (the two never stack)
    fatigue_label: str  # "spent" / "winded" / ""
    weapon_mod: int = 0     # the weapon's pressure term (attack bonus, the staff's
                            # parry bonus on defense, or the broken-weapon malus)
    weapon_label: str = ""  # e.g. "rapier" / "broken club"
    prof: int = 0           # proficiency rank with the wielded weapon (attack only)
    armor: int = 0          # the entity's def_bonus (defense only -- the
                            # "armored" dress trait; a body knob, not a weapon)
    misc: int = 0           # circumstance term (e.g. -2 drinking mid-fight,
                            # -2 fleeing under a parting blow, +1 aloft)
    misc_label: str = ""
    stat_label: str = "DEX"  # "AIM" on a cast (the Magic & Mind add-on)
    chill: int = 0          # DEX lost to landed ice bolts this fight

    def breakdown(self, name: str) -> str:
        parts = [f"2d6={self.dice}", f"+{self.dex} {self.stat_label}"]
        if self.chill:
            parts.append(f"-{self.chill} chilled")
        if self.training:
            parts.append(f"+{self.training} training")
        if self.weapon_mod:
            parts.append(f"{self.weapon_mod:+d} {self.weapon_label}")
        if self.prof:
            parts.append(f"+{self.prof} proficiency")
        if self.armor:
            parts.append(f"+{self.armor} armor")
        if self.wound_pen:
            parts.append(f"-{self.wound_pen} wounds")
        if self.fatigue_pen:
            parts.append(f"-{self.fatigue_pen} {self.fatigue_label}")
        if self.misc:
            parts.append(f"{self.misc:+d} {self.misc_label}")
        return f"{name}: {self.total} ({', '.join(parts)})"


@dataclass
class Clock:
    """Campaign time. Coarse on purpose: a `day` counter for the weekly HP math
    plus the short-rest slots spent so far today. This is the seed of the
    between-fights layer -- later it can grow finer (hours) without changing how
    the rest functions are called."""
    day: int = 1
    short_rests_used: int = 0

    @property
    def short_rests_left(self) -> int:
        return max(0, SHORT_RESTS_PER_DAY - self.short_rests_used)


@dataclass
class Purse:
    """The party's shared gold. Potions are per-hero; coin is communal because
    buying happens between adventures, where the party acts as one."""
    gold: int = 0


@dataclass(eq=False)
class Entity:
    name: str               # short (combat-log) name -- "Inga", nothing
                            # appended: sheet flavor (race, traits) stays out
                            # of the per-exchange lines so both log levels
                            # stay terse
    dex: int
    str_: int
    sta: int
    max_hp: int
    power: int = 0
    mind: int = 0           # MIND, the casting stat (the 1-20 doctrine:
                            # fixed at creation, natural human cap 6; only
                            # monsters and future transcendence break it).
                            # Aim for a thrown cast is ceil((MIND+DEX)/2);
                            # the casting check rolls off MIND alone. Also
                            # the party's QUEST SIGHT (quests.py: the best
                            # MIND reads a job's level precisely). 0 = never
                            # rolled (pre-magic foes).
    ability: str | None = None          # "bulwark" (mid-fight save) or "heal" (between-
                                         # fights HP restore, see use_heal); None = neither
    school: str = ""                    # the wizard marker: the school rolled
                                         # at creation ("fire"/"ice"; "" = not
                                         # a wizard). The identity gate for
                                         # learning spells; the spells dict
                                         # below carries what they know.
    spells: dict[str, int] = field(default_factory=dict)   # spell -> rank
                                         # (1..SPELL_RANK_MAX; rank n costs n
                                         # points via train_spell; new spells
                                         # come from spellbooks, learn_spell)
    spell_ward: int = 0                 # the apex monsters' resistance knob
                                         # (a per-row puzzle piece like pain,
                                         # never a universal stat): +2 x ward
                                         # to a possession's DC, ward >= 2
                                         # immune to stun riders, any ward
                                         # defends normally against ambush
                                         # strikes
    sta_cost: int = STA_ATTACK_COST     # STA spent per attack (defense is free);
                                         # Phase 4 hangs weapon weight on this knob
    undead: bool = False                # dead flesh: wounds never knit back on
                                         # their own (refresh_foes_after_retreat)
    pain: int = 1                       # the pain divisor: wound roll penalty =
                                         # HP lost // pain. 1 = feels everything
                                         # (small beasts, untrained flesh);
                                         # 2 = the trained-fighter norm, HEROES
                                         # AND humanoid foes alike (the 2026-07-09
                                         # spiral regear -- see HERO_PAIN) plus
                                         # undead/brutes; 3-4 = the apex
                                         # monsters, whose deep HP pools would
                                         # otherwise be nullified by the spiral
                                         # (a 60-HP dragon at -20 to rolls is a
                                         # grind, not a boss)
    tireless: bool = False              # never spends STA, never Winded/Spent
                                         # (the undead don't tire; you do)
    pursues: bool = True                # gives chase when the party retreats;
                                         # False for the barrow's undead (bound
                                         # to the grave -- they swing at the
                                         # door but never follow past it)
    crowd_cap: int = CROWD_CAP          # how many attackers can press THIS
                                         # target at once (the press, see
                                         # CROWD_CAP); big monsters take 3-4 --
                                         # a giant can be attacked from all
                                         # sides, so boss fights stay full-party
    regen: int = 0                      # HP knit back at the end of each round
                                         # while up (trolls) -- the anti-attrition
                                         # puzzle: out-damage it or lose to it.
                                         # A fled regenerator is a healed one
                                         # (refresh_foes_after_retreat).
    sweep: int = 1                      # max targets per attack (one attacker
                                         # roll, each defender rolls separately
                                         # -- the giant's sweeping blow, the
                                         # dragon's breath). 1 = normal.
    sweep_cost_power: int = 0           # Power per multi-target use (dragonfire
                                         # is fueled); 0 = free (a club sweep).
                                         # Out of Power -> single attacks.
    sweep_label: str = ""               # log flavor for the multi-target blow
                                         # ("a great sweeping blow", "a gout of
                                         # dragonfire")
    protagonist: bool = False           # the PLAYER CHARACTER (session play
                                         # marks party[0]; the sims never set
                                         # it). Fate's bargain applies: a blow
                                         # that would kill them is commuted to
                                         # a Down while a companion still
                                         # draws breath -- and if the fight is
                                         # then WON, the last foe's dying blow
                                         # kills one random companion. The
                                         # party is a life-resource, spent one
                                         # member at a time; a party that
                                         # cannot win anyway still wipes.
    hp: int = field(default=0)
    cur_sta: int = field(default=0)
    cur_power: int = field(default=0)
    dex_debuff: int = field(default=0)  # DEX lost to landed ice bolts; lasts
                                         # the fight (cleared when the melee
                                         # ends or the party breaks away)
    # Per-fight spell states (all cleared by _clear_fight_states at fight
    # end / on a break-away -- nothing here crosses fights):
    unseen: bool = field(default=False)     # invisibility: untargetable; the
                                            # next attack is an ambush strike
                                            # and breaks it
    aloft: int = field(default=0)           # flight: rounds left in the air
                                            # (melee can't reach; bolts and
                                            # fueled sweeps -- breath -- can;
                                            # +FLIGHT_ALOFT_ATK attacking)
    stunned: int = field(default=0)         # frozen solid / slammed sprawling:
                                            # loses that many actions (defense
                                            # is unaffected -- the body still
                                            # flinches)
    possessed: int = field(default=0)       # rounds left fighting for the
                                            # OTHER side (a foe field; the
                                            # party never gets possessed --
                                            # enemy wizards cast only bolts
                                            # for now)
    disarm_tried: bool = field(default=False)   # telekinetic disarm attempted
                                                # on this target (once per foe
                                                # per fight, hit or miss)
    # Ranged-combat per-fight state (2026-07-16; cleared with the rest):
    adv: int = field(default=0)         # steps advanced from this side's
                                        # line; the gap to an opposing
                                        # entity is field - adv - their adv
    reload_left: int = field(default=0)     # rounds until the next shot is
                                            # ready (ticks on non-firing
                                            # rounds)
    switched: bool = field(default=False)   # forced to the ranged card's
                                            # melee grip by contact (the
                                            # switch round was paid)
    shots_hit: int = field(default=0)       # missiles spent this fight, by
    shots_missed: int = field(default=0)    # outcome -- the scavenge roll's
                                            # inputs (hits recover better)
    down: bool = field(default=False)   # at 0 HP, out of this fight (recoverable)
    dead: bool = field(default=False)   # truly slain (unsaved crippling blow)
    fate_debt: bool = field(default=False)  # spared by fate THIS fight; the
                                             # price (a companion's life) is
                                             # collected at victory, waived on
                                             # a fled or lost fight
    items: dict[str, int] = field(default_factory=dict)
    hp_regen_per_night: int = field(default=0)  # HP knit back per long rest (derived)
    # Progression. Training is the veteran-vs-novice axis: a flat pressure bonus,
    # so it improves landing, avoiding, AND severity (margin feeds severity).
    level: int = field(default=1)
    xp: int = field(default=0)          # progress toward the NEXT level only
    skill_points: int = field(default=0)
    training: int = field(default=0)    # combat training rank (0..TRAINING_MAX)
    # Weapons. One wielded weapon, no inventory (heroic tone -- swaps are
    # narrative, DM-arbitrated). Proficiency is per weapon TYPE (name), so a
    # replacement rapier keeps your rapier ranks.
    weapon: Weapon | None = field(default=None)
    weapon_broken: bool = field(default=False)  # shattered in combat; fights
                                                # on as a stump until re-armed
    proficiency: dict[str, int] = field(default_factory=dict)  # name -> rank
    # The person behind the numbers (2026-07-11, the character layer --
    # people.py rolls these; foes and sim entities keep the defaults, so
    # nothing here moves a bench number).
    cha: int = 0                        # the fourth hero stat: party capacity
                                        # (party_capacity) and the PC's quest-
                                        # gold negotiation (award_quest).
                                        # 0 = never rolled (foes, old paths)
    def_bonus: int = 0                  # flat DEFENSE pressure (the "armored"
                                        # dress trait; armor-the-system is a
                                        # separate roadmap item)
    race: str = ""                      # human / elf / orc / dwarf / goblin
    sex: str = ""                       # "m" / "f" (flavor)
    age: int = 0                        # 2d20+10 at creation (flavor)
    nickname: str = ""                  # schema slot only -- no nickname
                                        # system yet (designer note 2026-07-11)
    traits: dict[str, str] = field(default_factory=dict)   # category -> trait
                                        # ("temperament": "loyal", ...); the
                                        # few mechanical ones are checked by
                                        # NAME via has_trait -- everything
                                        # else is DM-performed fiction
    satisfaction: int | None = field(default=None)  # the companion morale
                                        # track (0..10; see the SAT_*
                                        # constants). None = not tracked:
                                        # the PC, foes, candidates not yet
                                        # hired, and every sim entity
    bond: str = ""                      # pair recruits: the partner's name --
                                        # they join and leave TOGETHER, and a
                                        # partner's death breaks the survivor
    bond_kind: str = ""                 # "a married couple" / "parent and
                                        # child" / "mentor and mentee" / ...
    last_dose_day: int = 0              # "needs meds" bookkeeping: the clock
                                        # day of the last dose bought

    def __post_init__(self) -> None:
        self.hp = self.max_hp
        self.cur_sta = self.sta
        self.cur_power = self.power
        # HP returns over ~a week. Derived from max_hp so a big pool doesn't take
        # forever (a flat 1/night would leave a 20-HP tank down for 20 nights).
        self.hp_regen_per_night = max(1, round(self.max_hp / 7))

    # --- derived state -------------------------------------------------- #
    @property
    def alive(self) -> bool:
        # "Still in the fight." Down and Dead both sit at 0 HP.
        return self.hp > 0

    @property
    def hp_lost(self) -> int:
        return self.max_hp - self.hp

    @property
    def spent(self) -> bool:
        # 0 STA = Spent: still swings (desperation is free) but takes
        # -SPENT_PENALTY to all rolls until the fight ends -- only a pause
        # action (a draught, Berserk, War-Breath) buys STA back mid-fight.
        # (Derived from cur_sta, so a
        # fighter entering a fight at 0 is spent from round 1: you don't
        # start a fight with nothing left.)
        return not self.tireless and self.cur_sta <= 0

    @property
    def winded(self) -> bool:
        return (not self.tireless and not self.spent
                and self.cur_sta <= WINDED_STA)

    @property
    def wound_penalty(self) -> int:
        # The death spiral, geared down by the pain divisor (integer floor --
        # at pain 2 a graze costs nothing on the roll). pain 1 feels
        # everything; undead and brutes take 2; the apex monsters 3-4, which
        # is what makes their deep HP pools survivable to CARRY (a big pool
        # with human pain collapses into a helpless grind long before zero).
        # Floored at 0: tavern-overcharged HP (hp > max_hp) is a buffer, not
        # a bonus to rolls.
        return max(0, self.hp_lost) // self.pain

    @property
    def prof_rank(self) -> int:
        # Rank with the WIELDED weapon (a broken weapon grants nothing --
        # you're swinging a stump, not the weapon you drilled with; a
        # ranged card in the switched melee grip likewise: you drilled the
        # shot, not the club).
        if self.weapon is None or self.weapon_broken:
            return 0
        if self.switched and self.weapon.range:
            return 0
        return self.proficiency.get(self.weapon.name, 0)

    @property
    def swing_cost(self) -> int:
        # STA per attack. The weapon sets it (the burst/sustain knob: a
        # zweihander burns 2 a swing); tireless entities pay nothing; a
        # broken weapon falls back to the entity's base cost.
        if self.tireless:
            return 0
        if self.weapon is not None and not self.weapon_broken:
            return self.weapon.sta_cost
        return self.sta_cost

    # --- ranged combat (2026-07-16) --------------------------------------- #
    @property
    def ranged(self) -> Weapon | None:
        """The wielded RANGED card while it can still shoot: not broken,
        not switched to the melee grip. None for every melee weapon."""
        w = self.weapon
        if (w is None or self.weapon_broken or w.range <= 0
                or self.switched):
            return None
        return w

    def has_ammo(self) -> bool:
        """Something left to shoot: a carried count, the revolver's Power,
        or the sling's anywhere-stones (no ammo key = free)."""
        w = self.weapon
        if w is None or not w.range:
            return False
        if not w.ammo:
            return True
        if w.ammo == "power":
            return self.cur_power >= REVOLVER_POWER_COST
        return self.items.get(w.ammo, 0) > 0

    @property
    def shot_ready(self) -> bool:
        """Loaded, drawn, and in the shooting grip -- fires this round if a
        target stands in range."""
        return (self.ranged is not None and self.reload_left <= 0
                and self.has_ammo())

    @property
    def effective_reload(self) -> int:
        """The card's cadence for THIS wielder: heavy_draw punishes weak
        arms with an extra cranking round (the crossbow's strength gate)."""
        w = self.weapon
        if w is None:
            return 0
        extra = 1 if w.heavy_draw and self.str_ < w.heavy_draw else 0
        return w.reload + extra

    @property
    def shot_aim(self) -> int:
        """The shot's attack stat per the card: DEX, the bow's
        ceil((DEX+STR)/2), or the blunderbuss's flat."""
        w = self.weapon
        if w is None:
            return self.dex
        if w.aim == "dex_str":
            return (self.dex + self.str_ + 1) // 2
        if w.aim == "flat":
            return w.aim_flat
        return self.dex

    @property
    def threat_reach(self) -> int:
        """How far this entity threatens RIGHT NOW -- what the movement
        phase holds ground for: the ranged card's range while ammo lasts
        (mid-reload still counts: they shoot from here), CAST_RANGE for a
        caster with a bolt to throw, 0 for steel."""
        r = 0
        if self.ranged is not None and self.has_ammo():
            r = self.ranged.range
        if self.default_cast() is not None:
            r = max(r, CAST_RANGE)
        return r

    def shot_severity_mods(self) -> list[tuple[int, str]]:
        """A shot's severity terms: the card's flat replaces STR entirely
        (like a cast -- the bow's STR share lives in its AIM), plus
        proficiency with the card."""
        w = self.weapon
        mods = [(w.severity, w.name)]
        if self.prof_rank:
            mods.append((self.prof_rank, "proficiency"))
        return mods

    def spend_shot(self) -> None:
        """Charge one missile (hit or miss) and start the reload clock."""
        w = self.weapon
        if w.ammo == "power":
            self.cur_power -= REVOLVER_POWER_COST
        elif w.ammo:
            self.items[w.ammo] = max(0, self.items.get(w.ammo, 0) - 1)
        self.reload_left = self.effective_reload

    # --- magic (the Magic & Mind add-on) ---------------------------------- #
    @property
    def is_wizard(self) -> bool:
        return bool(self.school)

    @property
    def aim(self) -> int:
        """The thrown-cast attack stat: ceil((MIND + DEX) / 2) -- the mind
        shapes it, the hand throws it (designer call, 2026-07-15). Fixed by
        construction: both parents are creation stats."""
        return (self.mind + self.dex + 1) // 2

    def spell_rank(self, name: str) -> int:
        return self.spells.get(name, 0)

    @property
    def attack_school(self) -> str | None:
        """The wizard's attack lane this fight: the best-drilled attack
        spell they know (ties prefer the innate school, then fire -- the
        damage default)."""
        known = [(self.spells[s], s == self.school, s)
                 for s in ("fire", "ice", "telekinesis") if s in self.spells]
        if not known:
            return None
        rank, _, best = max(known, key=lambda t: (t[0], t[1], t[2] == "fire"))
        return best

    def default_cast(self) -> str | None:
        """The basic attack cast this entity throws when nothing smarter
        applies (parting blows use exactly this): the attack school's bolt
        while the Power lasts, else None (swing the weapon)."""
        school = self.attack_school
        if school is None:
            return None
        kind = {"fire": "fire", "ice": "ice", "telekinesis": "tk"}[school]
        if kind == "tk" and self.spell_rank("telekinesis") < 2:
            return None     # rank 1 is only the disarm; nothing to hurl yet
        return kind if self.cur_power >= CAST_POWER_COST[kind] else None

    def choose_cast(self, defender: "Entity") -> str | None:
        """The wizard's per-exchange plan (a standing behavior, never a
        mid-fight decision): telekinetically DISARM an armed foe first
        (once per foe, hit or miss), spend a rank-3 technique (freeze /
        hurl_foe) on a still-healthy body, else throw the school's bolt,
        else swing steel (None)."""
        if not self.is_wizard:
            return None
        if (self.spell_rank("telekinesis") >= 1
                and self.cur_power >= CAST_POWER_COST["disarm"]
                and not defender.disarm_tried
                and defender.weapon is not None
                and not defender.weapon.natural
                and not defender.weapon_broken):
            return "disarm"
        school = self.attack_school
        healthy = defender.hp * 2 >= defender.max_hp
        control_ok = (healthy and not defender.stunned
                      and defender.spell_ward < 2)
        if school == "ice":
            if (self.spell_rank("ice") >= SPELL_RANK_MAX and control_ok
                    and self.cur_power >= CAST_POWER_COST["freeze"]):
                return "freeze"
            if self.cur_power >= CAST_POWER_COST["ice"]:
                return "ice"
        elif school == "fire":
            if self.cur_power >= CAST_POWER_COST["fire"]:
                return "fire"
        elif school == "telekinesis":
            if (self.spell_rank("telekinesis") >= SPELL_RANK_MAX
                    and control_ok
                    and self.cur_power >= CAST_POWER_COST["hurl_foe"]):
                return "hurl_foe"
            if (self.spell_rank("telekinesis") >= 2
                    and self.cur_power >= CAST_POWER_COST["tk"]):
                return "tk"
        return None

    def cast_severity_mods(self, kind: str) -> list[tuple[int, str]]:
        """An aimed cast's severity terms: the kind's flat replaces STR AND
        the weapon; the spell's rank adds like weapon proficiency does."""
        mods = [(CAST_SEVERITY[kind], f"{kind_label(kind)}")]
        rank = self.spell_rank(CAST_SPELL[kind])
        if rank:
            mods.append((rank, "spell rank"))
        return mods

    def severity_mods(self) -> list[tuple[int, str]]:
        """The wielded weapon's severity terms as (value, label) pairs, kept
        separate so the log can show every source (weapon vs proficiency)."""
        if self.weapon is None:
            return []
        if self.weapon_broken:
            return [(BROKEN_SEVERITY, f"broken {self.weapon.name}")]
        if self.switched and self.weapon.range:
            # The ranged card's melee grip: its own line, no proficiency.
            return [(self.weapon.melee_sev, f"{self.weapon.name} (in hand)")]
        mods = []
        if self.weapon.severity:
            mods.append((self.weapon.severity, self.weapon.name))
        if self.prof_rank:
            mods.append((self.prof_rank, "proficiency"))
        return mods

    def pressure(self, rng: random.Random, attacking: bool = False,
              wound_pen: int | None = None, misc: int = 0,
              misc_label: str = "", cast: str | None = None,
              shot: bool = False, vs_shot: bool = False) -> PressureRoll:
        # wound_pen overrides the live wound penalty -- used for the dying
        # swing (group_combat): a fighter felled mid-round still gets their
        # blow in, rolled with the wounds they had at ROUND START, not the
        # ones that just killed them (the blows cross in the air).
        dice = rng.randint(1, 6) + rng.randint(1, 6)
        pen = self.wound_penalty if wound_pen is None else wound_pen
        if self.spent:
            fatigue_pen, fatigue_label = SPENT_PENALTY, "spent"
        elif self.winded:
            fatigue_pen, fatigue_label = WINDED_PENALTY, "winded"
        else:
            fatigue_pen, fatigue_label = 0, ""
        # The weapon is an offense package: its pressure bonus (and proficiency)
        # apply to the ATTACK roll only. Defense is the body -- DEX and
        # training -- except the staff's deliberate parry knob (def_pressure).
        # A broken weapon drags the attack down instead.
        weapon_mod, weapon_label, prof = 0, "", 0
        if cast:
            # An aimed cast: the weapon stays out of it -- the "proficiency"
            # is the spell's rank instead.
            prof = self.spell_rank(CAST_SPELL[cast])
        elif shot:
            # A shot: the card's attack bonus and the drilled proficiency,
            # like any weapon attack.
            weapon_mod = self.weapon.atk_pressure
            weapon_label = self.weapon.name
            prof = self.prof_rank
        elif self.weapon is not None:
            if attacking:
                if self.weapon_broken:
                    weapon_mod = BROKEN_ATK_PRESSURE
                    weapon_label = f"broken {self.weapon.name}"
                elif self.switched and self.weapon.range:
                    # The ranged card's melee grip (post-switch): its own
                    # melee line, no proficiency (prof_rank knows).
                    weapon_mod = self.weapon.melee_atk
                    weapon_label = f"{self.weapon.name} (in hand)"
                else:
                    weapon_mod = self.weapon.atk_pressure
                    weapon_label = self.weapon.name
                    prof = self.prof_rank
            elif (not self.weapon_broken and self.weapon.def_pressure
                    and not vs_shot):
                # No parrying an arrow with a stick: the weapon's guard knob
                # (the staff's +1, the zweihander's -1) is steel-on-steel
                # geometry and sits out of a defense against missiles.
                weapon_mod = self.weapon.def_pressure
                weapon_label = self.weapon.name
        # def_bonus is a body knob (the "armored" trait): defense only, like
        # the staff's parry but worn instead of wielded -- and worn armor
        # DOES count against arrows (vs_shot keeps it).
        armor = 0 if attacking else self.def_bonus
        # The stat term: DEX for everything bodily, AIM (the MIND/DEX mean)
        # for a cast, the card's aim stat for a shot. Frost (landed ice)
        # slows the BODY: it drags DEX-based rolls, never a cast's aim or
        # the blunderbuss's flat spread, and can't push the term below 0.
        if cast:
            stat, stat_label = self.aim, "AIM"
            chill = 0
        elif shot:
            stat, stat_label = self.shot_aim, "AIM"
            chill = (0 if self.weapon.aim == "flat"
                     else min(stat, self.dex_debuff))
        else:
            stat, stat_label = self.dex, "DEX"
            chill = min(self.dex, self.dex_debuff)
        # Height is an attacker's edge (flight): hard to reach, easy to rain
        # blows down from.
        if attacking and self.aloft > 0 and not misc:
            misc, misc_label = FLIGHT_ALOFT_ATK, "aloft"
        total = (dice + stat - chill + self.training + weapon_mod + prof
                 + armor + misc - pen - fatigue_pen)
        return PressureRoll(total=total, dice=dice, dex=stat,
                         training=self.training, wound_pen=pen,
                         fatigue_pen=fatigue_pen, fatigue_label=fatigue_label,
                         weapon_mod=weapon_mod, weapon_label=weapon_label,
                         prof=prof, armor=armor, misc=misc,
                         misc_label=misc_label, stat_label=stat_label,
                         chill=chill)


# --------------------------------------------------------------------------- #
# Combat: a group melee
# --------------------------------------------------------------------------- #

def _try_save(defender: Entity, tier: str, dmg: int) -> bool:
    """Decide whether the defender spends Power to step an incoming blow down.

    Bulwark only -- Heal has no in-fight role; it mends HP between fights
    instead (see use_heal).

    Policy (conservative, death-first): always buy off a *crippling* blow if
    Power allows; buy off a *grievous* that would put us Down only when a
    reserve is left for a later death-save. Mutates Power. Returns True if a
    save fired.
    """
    if defender.ability != "bulwark" or defender.cur_power < SAVE_COST:
        return False
    if tier not in ("grievous", "crippling blow"):
        return False
    lethal = tier == "crippling blow"
    would_down = (defender.hp - dmg) <= 0
    if lethal or (would_down and defender.cur_power >= SAVE_COST * 2):
        defender.cur_power -= SAVE_COST
        return True
    return False


def _check_weapon_break(a: Entity, b: Entity, rng: random.Random,
                        log: list[str]) -> None:
    """Weapon-on-weapon contact (a parry or a Clash): the LOWER-durability
    weapon risks shattering -- P = BREAK_CHANCE_PER_GAP_SQ * gap^2. Equal
    durability never breaks, and a broken weapon can't break again. Crude mook
    steel snapping on a hero's quality blade is the intended player-favoring
    asymmetry: visible power without inflating any number."""
    wa = a.weapon if a.weapon is not None and not a.weapon_broken else None
    wb = b.weapon if b.weapon is not None and not b.weapon_broken else None
    if wa is None or wb is None or wa.durability == wb.durability:
        return
    if wa.natural or wb.natural:
        return      # breakage is a steel-on-steel event: a claw neither
                    # shatters nor shatters the blade that parries it
    loser, stronger = (a, wb) if wa.durability < wb.durability else (b, wa)
    other = b if loser is a else a
    gap = abs(wa.durability - wb.durability)
    if rng.random() >= BREAK_CHANCE_PER_GAP_SQ * gap * gap:
        return
    loser.weapon_broken = True
    log.append(f"    *** CRACK -- {loser.name}'s {loser.weapon.name} shatters "
               f"on {other.name}'s {stronger.name}! They fight on with what's "
               f"left ({BROKEN_ATK_PRESSURE} attack pressure, "
               f"{BROKEN_SEVERITY} severity). ***")


def _attack(attacker: Entity, defender: Entity, rng: random.Random,
            log: list[str], atk_wound_pen: int | None = None,
            def_mod: int = 0, def_label: str = "",
            atk_roll: PressureRoll | None = None,
            soften: bool = False, cast: str | None = "auto",
            ambush: bool = False, shot: bool = False) -> None:
    """One opposed exchange. Higher roll lands; severity sets the wound.

    The *raw* result is computed first (it may be a crippling blow); a Power
    save can then step it down one tier. The log states the blow that would
    have landed. Death only happens when a raw crippling blow is not saved.

    `atk_wound_pen` overrides the attacker's wound penalty (the dying swing --
    see group_combat's round-start snapshot). `def_mod`/`def_label` is a
    circumstance penalty on the defense roll (a hero drinking at the pause, or
    fleeing under a parting blow, defends at -PAUSE_ACTION_DEF_PENALTY).
    `atk_roll` reuses a pre-rolled attack (a SWEEP: one great blow, one
    attacker roll, resolved against each caught defender's own defense).
    `soften=True` steps the landed wound down ONE tier (after the graze
    floors, before any save): the parting blow at a fleeing back (2026-07-10)
    -- a hasty swing at a moving target, not a set-piece kill. A retreating
    party stacks -2 fleeing on top of its wounds and fatigue, so at low HP
    every parting blow was landing grievous-or-worse and retreat-when-low
    (exactly when you retreat) was a guaranteed mauling; softened, a parting
    blow can still Down a hero but never lands the crippling tier, so the
    door can maim but not kill outright.

    Magic (the Magic & Mind add-on): `cast` names the aimed cast kind
    ("fire"/"ice"/"freeze"/"tk"/"hurl_foe"/"disarm"; see CAST_SEVERITY).
    The default sentinel "auto" lets the attacker decide by its own rule
    (default_cast: the attack school's bolt while the Power lasts), so every
    attack path -- the melee loop, parting blows -- casts consistently;
    group_combat passes an explicit kind when it planned something smarter
    (a freeze, a disarm, a fireball's reused sweep roll). The cast's Power
    is charged HERE (a parried cast still burns it) except on a reused
    sweep roll, which the caller fueled. Snake-eyes on a cast's attack dice
    is a MISFIRE (the fumble is scoped to casting -- steel stays reliable):
    the Power and the action are lost and the backlash grazes the caster.

    `ambush=True` (or an unseen attacker) is the assassin strike -- unseen,
    a blink at the back, a stolen moment: the defender never rolls and the
    exchange is won at margin AMBUSH_MARGIN. The severity TABLE is the cap
    (a crippling blow at worst), so mooks drop and bosses soak -- never a
    literal auto-kill. Any spell_ward turns the ambush into a normal
    exchange (the moment is not wholly the caster's).

    `shot=True` (ranged combat, 2026-07-16) is a missile: pressure off the
    card's AIM, the defense WITHOUT the weapon's parry knob (vs_shot), the
    severity off the card's flat with STR out (like a cast). The missile is
    charged here hit or miss (spend_shot: ammo/Power + the reload clock),
    and the outcome is tallied on shots_hit/shots_missed for the after-
    battle scavenge. No steel-on-steel breakage, no misfires -- the fumble
    stays scoped to casting; powder and gut-strings are reliable arts.

    Every exchange logs two layers: an interpretive headline first (both log
    levels; the player version folds the HP loss in and drops the roll
    penalty), then the raw numbers (dice, each modifier and its source)
    indented beneath it -- full log only.
    """
    if attacker.unseen and atk_roll is None:
        ambush = True
        attacker.unseen = False     # the strike breaks the veil, hit or miss
    if shot:
        cast = None                 # a missile is a missile, never a cast
    elif atk_roll is None and cast == "auto":
        cast = attacker.default_cast()
    elif cast == "auto":
        cast = None                 # a reused sweep roll: physical unless the
                                    # caller said otherwise (a fireball does)
    if ambush and cast == "disarm":
        # Nobody breaks an ambush to fumble at a scabbard: the strike from
        # nowhere is a strike -- fall back to the default attack cast.
        cast = attacker.default_cast()
    if cast and atk_roll is None:
        # The cast happens whatever the exchange then does -- parried and
        # warded casts burn Power too. (The swing's STA was already paid.)
        attacker.cur_power -= CAST_POWER_COST[cast]
    if shot:
        # The missile flies whatever the exchange then does: ammo (or the
        # revolver's Power) is spent hit or miss, and the reload clock
        # starts now.
        attacker.spend_shot()
    if ambush and defender.spell_ward > 0:
        ambush = False
        log.append(f"    {defender.name}'s ward flares -- the ambush is met "
                   f"as an honest exchange!")

    label = (kind_label(cast) if cast
             else attacker.weapon.missile if shot else None)
    subject = f"{attacker.name}'s {label}" if label else attacker.name

    if ambush:
        atk, dfn = None, None
        margin = AMBUSH_MARGIN
        pressure_line = (f"        pressure: ambush -- no defense, "
                         f"margin {AMBUSH_MARGIN}")
        log.append(f"    {attacker.name} strikes out of nowhere -- "
                   f"{defender.name} never sees it coming!")
    else:
        atk = (attacker.pressure(rng, attacking=True, wound_pen=atk_wound_pen,
                                 cast=cast, shot=shot)
               if atk_roll is None else atk_roll)
        dfn = defender.pressure(rng, misc=def_mod, misc_label=def_label,
                                vs_shot=shot)
        pressure_line = (f"        pressure: {atk.breakdown(attacker.name)} vs "
                      f"{dfn.breakdown(defender.name)}")
        if cast and atk_roll is None:
            pressure_line += (f" [{label}: -{CAST_POWER_COST[cast]} "
                              f"Power, {attacker.cur_power} left]")
        elif shot:
            w = attacker.weapon
            if w.ammo == "power":
                pressure_line += (f" [{w.name}: -{REVOLVER_POWER_COST} "
                                  f"Power, {attacker.cur_power} left]")
            elif w.ammo:
                pressure_line += (f" [{w.ammo}: "
                                  f"{attacker.items.get(w.ammo, 0)} left]")

        if cast and atk_roll is None and atk.dice == 2:
            # Snake-eyes on a cast: MISFIRE. Magic is the volatile art --
            # the spell collapses in the hand; the backlash grazes the
            # caster (the Power is already gone).
            attacker.hp = max(0, attacker.hp - MISFIRE_BACKLASH_HP)
            _play(log,
                  f"    !! {attacker.name}'s {label} MISFIRES -- the spell "
                  f"collapses in their hands (-{MISFIRE_BACKLASH_HP} HP -> "
                  f"{attacker.hp}/{attacker.max_hp}; the Power is wasted)",
                  f"    !! {attacker.name}'s {label} MISFIRES "
                  f"(-{MISFIRE_BACKLASH_HP} HP to the caster)")
            _debug(log, pressure_line)
            if attacker.hp <= 0:
                attacker.down = True
                log.append(f"    {attacker.name} goes down, "
                           f"out of the fight.")
            return

        if cast == "disarm":
            # Telekinesis rank 1: no wound -- the grip tears the weapon
            # away. Opposed like any exchange; once per foe per fight,
            # tried is tried.
            defender.disarm_tried = True
            _debug(log, pressure_line)
            if (atk.total > dfn.total and defender.weapon is not None
                    and not defender.weapon.natural
                    and not defender.weapon_broken):
                defender.weapon_broken = True
                _play(log,
                      f"    *** {attacker.name}'s telekinetic grip tears the "
                      f"{defender.weapon.name} from {defender.name}'s hands "
                      f"-- it clatters away ({BROKEN_ATK_PRESSURE} attack "
                      f"pressure, {BROKEN_SEVERITY} severity bare-handed). ***",
                      f"    *** {defender.name} is DISARMED -- the "
                      f"{defender.weapon.name} is torn away! ***")
            else:
                log.append(f"    {attacker.name}'s telekinetic grip closes on "
                           f"{defender.name}'s weapon -- and is shaken off.")
            return

        if atk.total == dfn.total:
            # A tie: no one lands. High dice = furious contact, low = circling.
            if cast:
                tie = f"the {label} splashes wide; neither yields"
                contact = False     # magic on steel tests nothing
            elif shot:
                tie = f"the {label} hisses past; neither yields"
                contact = False     # a missile tests no steel
            elif max(atk.dice, dfn.dice) >= TIE_HIGH_DICE:
                tie = "Clash! Steel rings; neither yields"
                contact = True      # steel met steel -- durability is tested
            else:
                tie = "Lull. They circle, probing for an opening"
                contact = False     # no contact, nothing to break
            log.append(f"    {attacker.name} and {defender.name} -- {tie}.")
            _debug(log, pressure_line)
            if shot:
                attacker.shots_missed += 1
            if contact:
                _check_weapon_break(attacker, defender, rng, log)
            return

        if atk.total < dfn.total:
            if cast:
                log.append(f"    {attacker.name} sends {label} "
                           f"at {defender.name} -- warded off.")
            elif shot:
                log.append(f"    {attacker.name} sends {_an(label)} "
                           f"at {defender.name} -- who twists away.")
                attacker.shots_missed += 1
            else:
                log.append(f"    {attacker.name} attacks {defender.name} "
                           f"-- parried.")
            _debug(log, pressure_line)
            if not cast and not shot:
                _check_weapon_break(attacker, defender, rng, log)
            return

        margin = atk.total - dfn.total
    # A cast's severity is the kind's flat (fire hits hard, ice barely) in
    # place of BOTH the caster's STR and the weapon; a shot's is the CARD's
    # flat likewise (the bow's STR share lives in its AIM); the defender
    # soaks as ever.
    if cast:
        sev_mods = attacker.cast_severity_mods(cast)
    elif shot:
        sev_mods = attacker.shot_severity_mods()
    else:
        sev_mods = attacker.severity_mods()
    atk_str = 0 if (cast or shot) else attacker.str_
    severity = (margin + atk_str + sum(v for v, _ in sev_mods)
                - defender.str_)
    raw_tier, dmg = wound_tier(severity)
    sev_line = f"        severity: {severity} = margin {margin}"
    if not cast and not shot:
        sev_line += f" +{attacker.str_} STR"
    for v, mod_label in sev_mods:
        sev_line += f" {v:+d} {mod_label}"
    sev_line += f" -{defender.str_} soak -> {raw_tier}"

    if dmg == 0:
        # Anti-soak floors -- chip damage soak can't zero, feeding the spiral.
        if (not cast and not shot and attacker.weapon is not None
                and not attacker.weapon_broken
                and attacker.weapon.graze_floor):
            # The rapier's own floor: ANY landed thrust draws blood.
            raw_tier, dmg = "graze", TIER_HP["graze"]
            sev_line += f" -> the {attacker.weapon.name}'s point finds a seam: graze"
        elif margin >= GRAZE_FLOOR_MARGIN:
            # The universal floor: a decisively won exchange always cuts at
            # least a little, no matter the soak (see GRAZE_FLOOR_MARGIN).
            raw_tier, dmg = "graze", TIER_HP["graze"]
            sev_line += " -> a clean hit still cuts: graze"
        else:
            what = "the " + label if (cast or shot) else "the blow"
            log.append(f"    {subject} {margin_verb(margin)} "
                       f"{defender.name}, but {what} glances off -- deflected.")
            _debug(log, pressure_line)
            _debug(log, sev_line)
            if shot:
                attacker.shots_missed += 1
            return

    if soften and dmg > 0:
        # The parting blow at a fleeing back lands one tier lighter (see the
        # docstring) -- softened BEFORE the save, so its raw tier can never
        # be crippling and a retreat is never an outright death at the door.
        raw_tier, dmg = reduce_tier(raw_tier)
        sev_line += f" -> a hurried blow at a fleeing back: {raw_tier}"
        if dmg == 0:
            log.append(f"    {subject} {margin_verb(margin)} "
                       f"{defender.name}, but the hurried blow at a fleeing "
                       f"back glances off -- deflected.")
            _debug(log, pressure_line)
            _debug(log, sev_line)
            if shot:
                attacker.shots_missed += 1
            return

    tier = raw_tier
    saved = _try_save(defender, tier, dmg)
    if saved:
        tier, dmg = reduce_tier(tier)
        sev_line += f", Bulwark save -> {tier} (-{dmg} HP)"
    else:
        sev_line += f" (-{dmg} HP)"

    defender.hp = max(0, defender.hp - dmg)
    if shot:
        attacker.shots_hit += 1     # a missile in a body is found again
                                    # more often than one in the grass
    state = (f"{defender.name}: {defender.hp}/{defender.max_hp} HP, "
             f"-{defender.wound_penalty} to rolls")
    # The death spiral is a real number the player budgets around, so the
    # player log shows it too (2026-07-09: it used to be full-log-only, which
    # made wounded fights read as inexplicable losing).
    player_state = f"{defender.name}: {defender.hp}/{defender.max_hp} HP"
    if defender.wound_penalty:
        player_state += f", -{defender.wound_penalty} to rolls"

    if saved:
        _play(log,
              f"    {subject} {margin_verb(margin)} {defender.name}"
              f" -- {TIER_PHRASE[raw_tier]}... {defender.name}'s Bulwark "
              f"flares! Reduced to {tier}. [{state}; "
              f"{defender.cur_power} Power left]",
              f"    {subject} {margin_verb(margin)} {defender.name}"
              f" -- {TIER_PHRASE[raw_tier]}... {defender.name}'s Bulwark "
              f"flares! Reduced to {tier} (-{dmg} HP). [{player_state}; "
              f"{defender.cur_power} Power left]")
    else:
        _play(log,
              f"    {subject} {margin_verb(margin)} {defender.name}"
              f" -- {TIER_PHRASE[tier]}! [{state}]",
              f"    {subject} {margin_verb(margin)} {defender.name}"
              f" -- {TIER_PHRASE[tier]} (-{dmg} HP)! [{player_state}]")
    _debug(log, pressure_line)
    _debug(log, sev_line)
    if cast in ("ice", "freeze"):
        # The ice school's whole point: every landed bolt rimes the target --
        # a stacking DEX loss for the rest of the fight (attack and defense;
        # the term floors at 0 in `pressure`). A flash-freeze rimes deeper.
        defender.dex_debuff += (FREEZE_DEX_DEBUFF if cast == "freeze"
                                else ICE_DEX_DEBUFF)
        _play(log,
              f"    {defender.name} is rimed with frost "
              f"(-{defender.dex_debuff} DEX for this fight)",
              f"    {defender.name} is rimed with frost "
              f"(-{defender.dex_debuff} DEX for this fight)")
    if (cast in ("freeze", "hurl_foe") and dmg > 0 and defender.alive
            and defender.spell_ward < 2):
        # The control riders: a wounding flash-freeze locks the body, a
        # wounding slam sprawls it -- either way the target loses its next
        # action (defense unaffected: the body still flinches). Ward 2+ is
        # immune; the damage landed regardless.
        defender.stunned = max(defender.stunned, 1)
        what = ("frozen fast" if cast == "freeze"
                else "slammed sprawling")
        log.append(f"    {defender.name} is {what} -- they lose their "
                   f"next action!")

    # Death is a 0-HP state (see the `alive` property): a blow only kills if
    # it actually drops you. At 0 HP an unsaved crippling blow is a death; any
    # other tier that took you there is a Down. A crippling blow that doesn't
    # reach 0 is just its damage -- you can't die at 4 HP.
    if defender.hp <= 0:
        if raw_tier == "crippling blow" and not saved:
            defender.dead = True
        else:
            defender.down = True


def _pick_target(targets: list[Entity], rng: random.Random, focus: bool,
                 engaged: dict[Entity, int] | None = None,
                 attacker: Entity | None = None,
                 reachable=None) -> Entity | None:
    """Pick a living target. With `engaged` (this round's single-attack counts
    per defender), only targets with press room (fewer than their crowd_cap
    attackers so far) are eligible -- returns None when every living target is
    already crowded, and the attacker circles the round away instead.

    Spell states (with `attacker` given): an UNSEEN target can't be picked
    at all; an ALOFT target only by an attacker who can cast OR SHOOT at it
    (bolts and arrows reach the sky, steel doesn't). A POSSESSED foe is off
    the party's list -- nobody cuts down their own puppet.

    `reachable` (ranged combat): a predicate narrowing eligibility to the
    attacker's reach on the field (gap 0 for steel, the card's range for a
    shot, CAST_RANGE for a caster) -- group_combat builds it per attack."""
    living = [e for e in targets if e.alive]
    if attacker is not None:
        living = [e for e in living if not e.unseen and not e.possessed]
        if not (attacker.default_cast() or attacker.sweep_cost_power
                or attacker.shot_ready):
            living = [e for e in living if e.aloft <= 0]
    if reachable is not None:
        living = [e for e in living if reachable(e)]
    if engaged is not None:
        living = [e for e in living if engaged.get(e, 0) < e.crowd_cap]
    if not living:
        return None
    if focus:
        # Focus fire the weakest target to thin the enemy line fastest.
        return min(living, key=lambda e: e.hp)
    return rng.choice(living)


def _first_blood(party: list[Entity], foes: list[Entity],
                 rng: random.Random, log: list[str]) -> None:
    """The rogue's opening strike, fired once as the fight begins (before the
    first exchange). Spends Power for a guaranteed graze on the focused target;
    the graze's real value is the death spiral (-1 to that foe's rolls all
    fight). Automatic, like Bulwark: trained aggression is reflexive."""
    for hero in party:
        if (hero.alive and hero.ability == "first_blood"
                and hero.cur_power >= FIRST_BLOOD_COST
                and any(f.alive for f in foes)):
            target = _pick_target(foes, rng, focus=True)
            hero.cur_power -= FIRST_BLOOD_COST
            target.hp = max(0, target.hp - FIRST_BLOOD_HP)
            _play(log,
                  f"    {hero.name} strikes before the lines meet -- "
                  f"First Blood! {target.name} is grazed "
                  f"(-{FIRST_BLOOD_HP} HP -> {target.hp}/{target.max_hp},"
                  f" -{target.wound_penalty} to rolls) "
                  f"[{FIRST_BLOOD_COST} Power spent, "
                  f"{hero.cur_power} left]",
                  f"    {hero.name} strikes before the lines meet -- "
                  f"First Blood! {target.name} is grazed "
                  f"(-{FIRST_BLOOD_HP} HP) "
                  f"[{target.name}: {target.hp}/{target.max_hp} HP]")
            if not target.alive:
                target.down = True
                log.append(f"    *** {target.name} falls. ***")


def casting_check(caster: Entity, spell: str, rank_cast: int,
                  rng: random.Random, log: list[str],
                  dc_extra: int = 0, dc_label: str = "") -> str:
    """The unaimed-cast roll (openers and utility spells; aimed casts ride
    the exchange instead): 2d6 + MIND + trained rank vs DC = CAST_DC_BASE +
    CAST_DC_PER_RANK x the rank being cast (+ dc_extra: a possession
    target's training and ward). Returns the degree of success:
      "misfire"   -- miss by 5+, or snake-eyes: Power lost, action lost,
                     the backlash grazes the caster (the caller applies it
                     via _misfire)
      "fizzle"    -- miss: Power lost, action lost, nothing happens
      "downgrade" -- make it by 0-1: resolves one rank lower (where the
                     spell has one; rank 1 has nothing to fall to)
      "success"
      "crit"      -- beat it by 7+, or boxcars: the Power is refunded
    MASTERY: casting a technique BELOW the caster's trained rank never
    rolls (auto-success, no log) -- reliability is what study buys; the
    risk lives at the edge of the art."""
    trained = caster.spell_rank(spell)
    if rank_cast < trained:
        return "success"
    dice = rng.randint(1, 6) + rng.randint(1, 6)
    dc = CAST_DC_BASE + CAST_DC_PER_RANK * rank_cast + dc_extra
    total = dice + caster.mind + trained
    margin = total - dc
    if dice == 2 or margin <= -5:
        result = "misfire"
    elif margin < 0:
        result = "fizzle"
    elif margin <= 1:
        result = "downgrade"
    elif dice == 12 or margin >= 7:
        result = "crit"
    else:
        result = "success"
    extra = f" +{dc_extra} {dc_label}" if dc_extra else ""
    _debug(log, f"        casting: {total} (2d6={dice}, +{caster.mind} MIND, "
                f"+{trained} rank) vs DC {dc} "
                f"({CAST_DC_BASE} +{CAST_DC_PER_RANK}x rank {rank_cast}"
                f"{extra}) -> {result}")
    return result


def _misfire(caster: Entity, spell: str, log: list[str]) -> None:
    """A misfired unaimed cast: the spell collapses in the hand -- the Power
    is already gone (the caller charged it), and the backlash grazes the
    caster."""
    caster.hp = max(0, caster.hp - MISFIRE_BACKLASH_HP)
    _play(log,
          f"    !! {caster.name}'s {spell} MISFIRES -- the spell collapses "
          f"in their hands (-{MISFIRE_BACKLASH_HP} HP -> "
          f"{caster.hp}/{caster.max_hp}; the Power is wasted)",
          f"    !! {caster.name}'s {spell} MISFIRES "
          f"(-{MISFIRE_BACKLASH_HP} HP to the caster)")
    if caster.hp <= 0:
        caster.down = True
        log.append(f"    {caster.name} goes down, out of the fight.")


def _log_foe_fall(defender: Entity, log: list[str]) -> None:
    if defender.alive:
        return
    if defender.dead:
        log.append(f"    *** {defender.name} is SLAIN. ***")
    else:
        log.append(f"    *** {defender.name} falls. ***")


def _cast_openers(party: list[Entity], foes: list[Entity],
                  rng: random.Random, log: list[str]) -> None:
    """The wizard openers, fired once as the fight begins (First Blood's
    doctrine: automatic while the Power lasts -- trained art is reflexive --
    and skipped when the fight is already winding down, so nobody burns the
    pool on a beaten foe). Each wizard casts at most ONE opener, the first
    it can afford down the OPENER_SPELLS priority ladder, at its full
    trained rank; the casting check gates it (at-rank casts roll -- see
    casting_check)."""
    if fight_winding_down(foes):
        return
    for hero in party:
        if not hero.alive or not hero.is_wizard or not hero.spells:
            continue
        _cast_opener(hero, foes, rng, log)


def _cast_opener(hero: Entity, foes: list[Entity], rng: random.Random,
                 log: list[str]) -> None:
    for spell in OPENER_SPELLS:
        rank = hero.spell_rank(spell)
        if rank <= 0:
            continue
        if spell == "possession":
            cost = POSSESSION_POWER_COST + rank
            prey = [f for f in foes if f.alive and not f.undead
                    and not f.tireless]
            if hero.cur_power < cost or not prey:
                continue
            target = max(prey, key=lambda f: f.max_hp)
            hero.cur_power -= cost
            result = casting_check(
                hero, spell, rank, rng, log,
                dc_extra=target.training + 2 * target.spell_ward,
                dc_label="the target resists")
            rounds = rank - 1 if result == "downgrade" else rank
            if result == "misfire":
                _misfire(hero, spell, log)
            elif result == "fizzle" or rounds <= 0:
                log.append(f"    {hero.name} reaches for {target.name}'s "
                           f"mind -- and is shut out. The spell fizzles "
                           f"({cost} Power wasted).")
            else:
                if result == "crit":
                    hero.cur_power += cost
                target.possessed = rounds
                left = (f"{hero.cur_power} Power left" if result != "crit"
                        else "a flawless seizure -- no Power spent")
                _play(log,
                      f"    *** {target.name}'s eyes go glassy -- "
                      f"{hero.name} seizes their mind! The puppet fights "
                      f"for the party ({rounds} round(s); {left}). ***",
                      f"    *** {target.name}'s eyes go glassy -- "
                      f"{hero.name} seizes their mind ({rounds} "
                      f"round(s))! ***")
            return
        if spell == "stop time":
            cost = STOP_TIME_POWER_COST + rank
            if hero.cur_power < cost:
                continue
            hero.cur_power -= cost
            result = casting_check(hero, spell, rank, rng, log)
            strikes = rank - 1 if result == "downgrade" else rank
            if result == "misfire":
                _misfire(hero, spell, log)
            elif result == "fizzle" or strikes <= 0:
                log.append(f"    {hero.name} reaches for the moment between "
                           f"moments -- and it slips away ({cost} Power "
                           f"wasted).")
            else:
                if result == "crit":
                    hero.cur_power += cost
                log.append(f"    *** Time stutters and HANGS -- {hero.name} "
                           f"moves alone through the frozen moment "
                           f"({strikes} stolen strike(s))! ***")
                for _ in range(strikes):
                    target = _pick_target(foes, rng, focus=True,
                                          attacker=hero)
                    if target is None:
                        break
                    was_alive = target.alive
                    _attack(hero, target, rng, log, ambush=True)
                    if was_alive and not target.alive:
                        _log_foe_fall(target, log)
            return
        if spell == "teleport":
            cost = TELEPORT_STRIKE_COST
            if hero.cur_power < cost:
                continue
            target = _pick_target(foes, rng, focus=True, attacker=hero)
            if target is None:
                continue
            hero.cur_power -= cost
            result = casting_check(hero, spell, 1, rng, log)
            if result == "misfire":
                _misfire(hero, spell, log)
            elif result == "fizzle":
                log.append(f"    {hero.name} folds space -- and arrives a "
                           f"step wide of it. The blink fizzles "
                           f"({cost} Power wasted).")
            else:
                if result == "crit":
                    hero.cur_power += cost
                log.append(f"    *** {hero.name} BLINKS -- and is behind "
                           f"{target.name}. ***")
                was_alive = target.alive
                _attack(hero, target, rng, log, ambush=True)
                if was_alive and not target.alive:
                    _log_foe_fall(target, log)
            return
        if spell == "invisibility":
            cost = INVISIBILITY_POWER_COST
            if hero.cur_power < cost:
                continue
            hero.cur_power -= cost
            result = casting_check(hero, spell, 1, rng, log)
            if result == "misfire":
                _misfire(hero, spell, log)
            elif result == "fizzle":
                log.append(f"    {hero.name} gathers the light around "
                           f"themselves -- and it slides off. The spell "
                           f"fizzles ({cost} Power wasted).")
            else:
                if result == "crit":
                    hero.cur_power += cost
                hero.unseen = True
                log.append(f"    *** {hero.name} is simply NOT THERE -- "
                           f"unseen until their strike lands. ***")
            return
        if spell == "flight":
            rank = min(rank, SPELLS["flight"].max_rank)
            cost = FLIGHT_POWER_COST + rank
            if hero.cur_power < cost:
                continue
            hero.cur_power -= cost
            result = casting_check(hero, spell, rank, rng, log)
            rounds = rank - 1 if result == "downgrade" else rank
            if result == "misfire":
                _misfire(hero, spell, log)
            elif result == "fizzle" or rounds <= 0:
                log.append(f"    {hero.name} kicks off the earth -- and "
                           f"comes right back down. The spell fizzles "
                           f"({cost} Power wasted).")
            else:
                if result == "crit":
                    hero.cur_power += cost
                hero.aloft = rounds
                log.append(f"    *** {hero.name} steps onto the AIR -- "
                           f"aloft for {rounds} round(s), out of steel's "
                           f"reach (+{FLIGHT_ALOFT_ATK} attacking; bolts "
                           f"and breath can still find them). ***")
            return


def _stamina_line(party: list[Entity], foes: list[Entity]) -> str:
    """One compact stamina readout per round (attacks spend the clock -- the
    log shows it ticking every round). A * marks the Winded, !! the Spent;
    tireless entities are summarized (their clock never moves). Full log
    only -- the player log tracks the clock via the !! crossing lines."""
    def side(group: list[Entity]) -> str:
        living = [e for e in group if e.alive]
        tireless = [e for e in living if e.tireless]
        parts = [f"{e.name} {e.cur_sta}/{e.sta}"
                 + ("!!" if e.spent else "*" if e.winded else "")
                 for e in living if not e.tireless]
        if tireless:
            parts.append(f"{len(tireless)} tireless")
        return ", ".join(parts)
    sides = " | ".join(s for s in (side(party), side(foes)) if s)
    line = f"    stamina: {sides}"
    legend = []
    if any(e.alive and e.winded for e in party + foes):
        legend.append("* = Winded")
    if any(e.alive and e.spent for e in party + foes):
        legend.append("!! = Spent")
    if legend:
        line += f"   ({', '.join(legend)})"
    return line


@dataclass
class Pause:
    """group_combat stopped at a trigger mid-fight (the interrupt primitive).
    The fight is NOT over: call group_combat again with the same `fired` set,
    first_round=round+1, and any pause actions to resume -- or attempt_retreat
    to break away. `crossings` is what tripped the pause: (kind, hero) pairs,
    kind in ("stamina", "wounds")."""
    round: int
    crossings: list[tuple[str, Entity]]


def _check_pause_triggers(party: list[Entity], foes: list[Entity],
                          fired: set[tuple[str, Entity]]
                          ) -> list[tuple[str, Entity]]:
    """The pause triggers, checked at the end of a round: a hero at STA <=
    PAUSE_STA_TRIGGER, or at HP <= half. Party side only (the pause is the
    player's), each (kind, hero) pair at most once per fight (`fired` is
    mutated) -- PER HERO, so one hero's crisis never silences the other's
    (2026-07: `fired` used to be keyed by kind alone, and a hero entering
    wounded gated the wounds trigger for the whole party) -- and only while
    both sides still stand: a decided fight has nothing to decide.
    group_combat also calls this once at fight start with the crossings
    discarded: the crossing-only gate (a condition already true at the door
    never fires -- see the pause comment block)."""
    if not (any(e.alive for e in party) and any(e.alive for e in foes)):
        return []
    crossings = []
    for h in party:
        if not h.alive:
            continue
        if (("stamina", h) not in fired and not h.tireless
                and h.cur_sta <= PAUSE_STA_TRIGGER):
            fired.add(("stamina", h))
            crossings.append(("stamina", h))
        if (("wounds", h) not in fired
                and h.hp <= h.max_hp * PAUSE_HP_FRACTION):
            fired.add(("wounds", h))
            crossings.append(("wounds", h))
    return crossings


def fight_winding_down(foes: list[Entity]) -> bool:
    """Is this fight already decided in the party's favor? True when every
    living foe is below half HP or Spent -- low, spiralling, losing force.
    The standing orders check this before spending a potion or a conversion
    on a fight that no longer needs one (designer call, 2026-07-11)."""
    return all(f.hp * 2 < f.max_hp or f.spent for f in foes if f.alive)


def standing_order(kind: str, hero: Entity, foes: list[Entity]) -> str | None:
    """The default mid-fight standing order for a hero whose crossing does
    NOT interrupt (see the pause comment block): what they do on their own,
    at the pause-action price, when they run low. Mirrors sim_pause_policy's
    conversion ladder minus the retreat vote (retreating is the player's,
    at the one wounds pause):
      stamina -> nothing if the fight is winding down; else drink a carried
                 draught, else War-Breath (a Bulwark hero keeps one save in
                 reserve), else Berserk on a still-healthy body.
      wounds  -> VANISH (invisibility rank 2 -- a cut-up wizard fades out
                 of reach) if they know it and the Power is there; else a
                 carried healing potion; unless the fight is winding down.
    Returns a pause-action string or None (fight on)."""
    if fight_winding_down(foes):
        return None
    if kind == "wounds":
        if (hero.spell_rank("invisibility") >= 2
                and hero.cur_power >= VANISH_POWER_COST):
            return "vanish"
        return "heal" if hero.items.get("healing", 0) > 0 else None
    if hero.items.get("stamina", 0) > 0:
        return "drink"
    if hero.cur_power >= WAR_BREATH_POWER_COST + (
            SAVE_COST if hero.ability == "bulwark" else 0):
        return "war-breath"
    if hero.hp > BERSERK_HP_COST * 3:
        return "berserk"
    return None


def _do_pause_action(h: Entity, action: str, log: list[str],
                     rng: random.Random) -> bool:
    """Execute one pause-menu action at the top of the resumed round: drink a
    stamina draught or healing potion, a resource conversion (Berserk /
    War-Breath), or a wizard's VANISH (invisibility rank 2). Returns
    True if it took effect -- the hero is then BUSY this round: no attack, and
    -PAUSE_ACTION_DEF_PENALTY on defense (vulnerable, not helpless). A failed
    action (nothing to drink, not enough Power) logs and the hero just fights."""
    if not h.alive:
        return False
    if action == "vanish":
        if h.spell_rank("invisibility") < 2:
            log.append(f"    {h.name} knows no vanishing art deep enough "
                       f"to cast in a melee. They fight on.")
            return False
        if h.cur_power < VANISH_POWER_COST:
            log.append(f"    {h.name} lacks the Power to vanish "
                       f"({h.cur_power}/{VANISH_POWER_COST}). "
                       f"They fight on.")
            return False
        h.cur_power -= VANISH_POWER_COST
        result = casting_check(h, "invisibility", 2, rng, log)
        if result == "misfire":
            _misfire(h, "invisibility", log)
        elif result == "fizzle":
            log.append(f"    {h.name} gathers the light -- and it slides "
                       f"off ({VANISH_POWER_COST} Power wasted). No attack "
                       f"this round, -{PAUSE_ACTION_DEF_PENALTY} defending.")
        else:
            if result == "crit":
                h.cur_power += VANISH_POWER_COST
            h.unseen = True
            log.append(f"    {h.name} VANISHES from the melee "
                       f"(-{VANISH_POWER_COST} Power -> {h.cur_power}) -- "
                       f"out of every foe's reach until their next strike, "
                       f"which lands as an ambush.")
        return True
    if action == "drink":
        if h.items.get("stamina", 0) <= 0:
            log.append(f"    {h.name} gropes for a stamina draught -- "
                       f"none left! They fight on.")
            return False
        h.items["stamina"] -= 1
        before = h.cur_sta
        h.cur_sta = recover(h.cur_sta, STAMINA_DRAUGHT_RESTORE, h.sta)
        log.append(f"    {h.name} downs a stamina draught mid-fight "
                   f"(STA {before} -> {h.cur_sta}/{h.sta}; "
                   f"{h.items['stamina']} left) -- no attack this round, "
                   f"-{PAUSE_ACTION_DEF_PENALTY} defending while they drink")
        return True
    if action == "heal":
        # The wounds trigger's own answer (2026-07-11; rules.md's "until HP
        # pressure proves otherwise" clause resolved in play): a healing
        # potion at the drink's exact price. It lightens the wound penalty
        # immediately -- fighting the spiral is the point.
        if h.items.get("healing", 0) <= 0:
            log.append(f"    {h.name} gropes for a healing potion -- "
                       f"none left! They fight on.")
            return False
        h.items["healing"] -= 1
        before = h.hp
        h.hp = recover(h.hp, HEALING_POTION_RESTORE, h.max_hp)
        log.append(f"    {h.name} downs a healing potion mid-fight "
                   f"(HP {before} -> {h.hp}/{h.max_hp}, now "
                   f"-{h.wound_penalty} to rolls; "
                   f"{h.items['healing']} left) -- no attack this round, "
                   f"-{PAUSE_ACTION_DEF_PENALTY} defending while they drink")
        return True
    if action == "berserk":
        if h.hp <= BERSERK_HP_COST:
            log.append(f"    {h.name} is too torn up to go Berserk "
                       f"(HP {h.hp}/{h.max_hp}). They fight on.")
            return False
        before = h.cur_sta
        h.hp -= BERSERK_HP_COST
        h.cur_sta = recover(h.cur_sta, BERSERK_STA_GAIN, h.sta)
        log.append(f"    {h.name} goes BERSERK -- strength torn from their "
                   f"own flesh (-{BERSERK_HP_COST} HP -> {h.hp}/{h.max_hp}, "
                   f"now -{h.wound_penalty} to rolls; STA {before} -> "
                   f"{h.cur_sta}/{h.sta}) -- no attack this round, "
                   f"-{PAUSE_ACTION_DEF_PENALTY} defending")
        return True
    if action == "war-breath":
        if h.cur_power < WAR_BREATH_POWER_COST:
            log.append(f"    {h.name} lacks the Power for War-Breath "
                       f"({h.cur_power}/{WAR_BREATH_POWER_COST}). "
                       f"They fight on.")
            return False
        before = h.cur_sta
        h.cur_power -= WAR_BREATH_POWER_COST
        h.cur_sta = recover(h.cur_sta, WAR_BREATH_STA_GAIN, h.sta)
        log.append(f"    {h.name} centers their breath -- War-Breath! "
                   f"(-{WAR_BREATH_POWER_COST} Power -> {h.cur_power}; "
                   f"STA {before} -> {h.cur_sta}/{h.sta}) -- no attack this "
                   f"round, -{PAUSE_ACTION_DEF_PENALTY} defending")
        return True
    raise ValueError(f"unknown pause action: {action}")


def _catch_breath(survivors: list[Entity], log: list[str]) -> None:
    """The fight is over for these heroes (won it or fled it clean): they
    catch their breath (+STA_RECOVERY_AFTER_FIGHT)."""
    for h in survivors:
        h.cur_sta = recover(h.cur_sta, STA_RECOVERY_AFTER_FIGHT, h.sta)
    log.append(f"    The party catches its breath "
               f"(+{STA_RECOVERY_AFTER_FIGHT} STA)")


def group_combat(party: list[Entity], foes: list[Entity],
                 rng: random.Random, log: list[str],
                 max_rounds: int = 40,
                 pause_triggers: bool = False,
                 fired: set[tuple[str, Entity]] | None = None,
                 first_round: int = 1,
                 actions: dict[Entity, str] | None = None,
                 standing_orders=None,
                 field: int = 0) -> Pause | None:
    """Resolve a melee in place. Survivors keep their HP/STA/Power as-is.

    THE FIELD (ranged combat, 2026-07-16): `field` is the opening gap
    between the two lines (0 = today's fight at the door -- every legacy
    caller unchanged; ROOM_FIELD indoors, WILD_FIELD on the road; a resume
    must pass the same value). Each entity's `adv` counts its steps from
    its own line; the pairwise gap is max(0, field - a.adv - b.adv). Each
    round opens with a movement phase: an entity with no living enemy
    inside its threat_reach ADVANCES one step instead of attacking (free,
    like circling; decided on round-start positions, applied together, so
    two closing lines meet in the middle). Steel reaches gap 0; shots reach
    the card's range but never gap 0 (contact forces the switch round to
    the card's melee grip); casts reach CAST_RANGE at any gap including 0.
    Shooters follow the card's reload cadence and ignore the press both
    ways; a melee attacker crowded out of an open field slips deeper
    toward the backline instead of circling. See the ranged-combat
    constants block for the whole doctrine.

    Exchanges resolve *sequentially* -- party in list order first, then foes --
    but the ROSTER of who acts is snapshotted at round start: everyone alive
    when the round opens gets their one swing, even if felled before their
    turn comes (the blows cross in the air -- the dying swing). A dying
    attacker rolls with the wounds it had at round start, not the ones that
    just dropped it, and its swing is free (desperation costs nothing).
    Targeting stays live: every attacker picks a target *living at the moment
    it acts*, so nobody wastes a swing on a corpse.

    The press (CROWD_CAP): at most crowd_cap attackers can press one target
    in a round (2 for anything man-sized; big monsters take more); an
    attacker with no open target circles instead -- free, no STA. Sweeps
    (Entity.sweep > 1) hit several defenders with ONE attacker roll, each
    defender rolling its own defense, and ignore the press both ways;
    a fueled sweep (sweep_cost_power) falls back to single attacks when the
    Power runs out. Regenerators knit `regen` HP at the end of every round
    they are still up.

    Stamina: an attack costs the attacker `swing_cost` STA -- set by the
    wielded weapon (defense is free); tireless entities pay nothing. An entity
    that hits 0 STA is SPENT: it still swings (desperation is free) but takes
    -SPENT_PENALTY to all rolls, attack and defense alike, until the fight
    ends (only a pause action buys STA back mid-fight). Against fresh foes
    that is a death sentence; two spent sides cancel each other's penalties
    and the wound spiral still finishes the fight -- so melees resolve instead
    of stalling (max_rounds is only a safety valve). When the fight ends the
    survivors catch their breath (+STA_RECOVERY_AFTER_FIGHT).

    The pause (the interrupt primitive): with pause_triggers=True the fight
    PAUSES at the end of a round in which a hero CROSSED STA <=
    PAUSE_STA_TRIGGER or HP <= half (each trigger once per hero per fight --
    `fired` carries the used (kind, hero) pairs across a resume; a condition
    already true at fight start is gated off, crossing-only). Returns a Pause
    instead of
    finishing; the caller decides (fight on / pause actions / retreat) and
    calls again with fired, first_round=pause.round+1, and `actions`
    ({hero: "drink" | "heal" | "berserk" | "war-breath"}, executed at the top
    of the resumed round: the hero skips that attack and defends at
    -PAUSE_ACTION_DEF_PENALTY). Returns None when the melee actually ended.

    Standing orders (2026-07-11): `standing_orders(kind, hero, party, foes)`
    decides each crossing instead of the every-crossing pause -- return
    "pause" to interrupt, a pause-action string to have the hero act on
    their own at the top of the next round (the usual price), or None to
    fight on. With standing_orders=None (the sims' default) every crossing
    pauses, exactly the pre-2026-07-11 behavior. When a round yields both an
    interrupt and auto-orders, the auto crossings are RE-ARMED (removed from
    `fired`) instead of acted on, so the order isn't lost across the
    save/resume boundary -- they re-trip after the resume.
    """
    party_set = set(party)

    def _gap(a: Entity, b: Entity) -> int:
        """The ground between two entities. Same-side pairs (and the
        possessed puppet in its own line) stand together; anyone aloft is
        'everywhere' -- steel still can't reach them, but that is
        _pick_target's aloft rule, not distance."""
        if field <= 0:
            return 0
        if (a in party_set) == (b in party_set):
            return 0
        if a.aloft > 0 or b.aloft > 0:
            return 0
        return max(0, field - a.adv - b.adv)

    def _min_gap() -> int:
        pairs = [_gap(h, f) for h in party for f in foes
                 if h.alive and f.alive]
        return min(pairs) if pairs else 0

    if fired is None:
        fired = set()
    if pause_triggers and first_round == 1:
        # Crossing-only gating: a trigger whose condition already holds as
        # the fight opens is marked fired silently -- entering low was the
        # player's informed choice at the door, so only an IN-FIGHT crossing
        # interrupts. (Reuses the trigger check; crossings are discarded.)
        _check_pause_triggers(party, foes, fired)
    # On a resume, entities already Spent have had their !! line; don't repeat.
    spent_logged: set[Entity] = (
        {e for e in party + foes if e.alive and e.spent}
        if first_round > 1 else set())
    busy_label = {"drink": "drinking", "heal": "drinking",
                  "berserk": "berserk", "war-breath": "war-breath",
                  "vanish": "casting"}
    busy: dict[Entity, str] = {}
    # Actions waiting to execute at the top of the next round: the caller's
    # pause answers on a resume, plus any standing orders issued at a
    # crossing (both pay the same price when they fire).
    queued: dict[Entity, str] = dict(actions) if actions else {}
    rnd = first_round - 1
    while any(e.alive for e in party) and any(e.alive for e in foes):
        rnd += 1
        if rnd > max_rounds:
            log.append("    (the fight grinds to a standstill)")
            break
        log.append(f"  Round {rnd}:")
        if rnd == 1:
            # The wizard openers fire before the lines meet (First Blood's
            # slot; a resume never re-fires them -- rnd starts past 1).
            _cast_openers(party, foes, rng, log)
            _first_blood(party, foes, rng, log)
            if not (any(e.alive for e in party)
                    and any(e.alive for e in foes)):
                break   # the openers alone can end a small fight
        if queued:
            # The pause actions happen now, in the teeth of the melee.
            for h, act in queued.items():
                if _do_pause_action(h, act, log, rng):
                    busy[h] = act
            queued = {}
            # A drink can un-Spend a fighter at 0: drop them from the
            # already-logged set so running dry AGAIN earns a fresh !! line.
            spent_logged = {e for e in spent_logged if e.spent}

        # Round-start snapshot: everyone alive NOW acts this round, even if
        # felled before their turn comes -- the dying swing (see docstring).
        actors = [e for e in party + foes if e.alive]
        start_pens = {e: e.wound_penalty for e in actors}
        engaged: dict[Entity, int] = {}     # the press: single-attack counts
                                            # per defender this round
        fired_shots: set[Entity] = set()    # who shot this round (their
                                            # reload clock starts fresh, it
                                            # doesn't also tick)

        # The movement phase (field > 0 only): whoever has nobody inside
        # their reach closes one step instead of attacking. Two sub-phases
        # (2026-07-16, bench-driven): CHARGERS COMMIT FIRST -- everyone
        # with reach 0 decides on round-start positions, applied together,
        # so two closing lines meet in the middle -- and SKIRMISHERS REACT
        # to the new ground (a shooter who'd have stepped toward a charger
        # sees the charge coming and holds instead of walking into it).
        moved: set[Entity] = set()
        arrived: set[Entity] = set()    # movers whose step created contact
                                        # -- the arrival volley's targets
        if field > 0:
            gap_before = _min_gap()
            advancing: list[Entity] = []

            def _may_move(e: Entity) -> bool:
                return not (e in busy or e in queued or e.stunned > 0
                            or e.aloft > 0 or e.unseen or e.possessed > 0
                            or e.adv >= field)

            def _wants_move(e: Entity) -> bool:
                enemies = foes if e in party_set else party
                live = [t for t in enemies if t.alive and not t.unseen]
                return bool(live) and all(_gap(e, t) > e.threat_reach
                                          for t in live)

            for skirmish_phase in (False, True):
                deciders = [e for e in actors if _may_move(e)
                            and (e.threat_reach > 0) == skirmish_phase
                            and e not in moved]
                step = [e for e in deciders if _wants_move(e)]
                for e in step:      # decided together, applied together
                    e.adv = min(field, e.adv + 1)
                    moved.add(e)
                advancing.extend(step)
            for e in moved:
                enemies = foes if e in party_set else party
                if any(_gap(e, t) == 0 for t in enemies if t.alive):
                    arrived.add(e)
            if advancing:
                gap_now = _min_gap()
                names = ", ".join(e.name for e in advancing)
                if gap_before > 0 and gap_now == 0:
                    _play(log,
                          f"    {names} close the distance -- the lines "
                          f"meet!",
                          f"    The lines meet -- steel range.")
                else:
                    _play(log,
                          f"    {names} close the distance "
                          f"(the gap narrows to {gap_now}).",
                          f"    The lines close.")
        for attacker in actors:
            if attacker in busy:
                continue    # occupied with their draught/conversion this round
            if attacker.stunned > 0:
                # Frozen fast / slammed sprawling (the control riders): the
                # action is lost -- no swing, no STA; the body still defends.
                attacker.stunned -= 1
                log.append(f"    {attacker.name} struggles back to their "
                           f"footing -- no action this round.")
                continue
            dying = not attacker.alive      # felled earlier this round
            if attacker in party_set:
                targets = foes
            elif attacker.possessed > 0:
                # The puppet turns on its own line (possession): it fights
                # for the party as long as the seizure holds.
                targets = [f for f in foes if f is not attacker]
            else:
                targets = party
            living_targets = [t for t in targets if t.alive]
            if not living_targets:
                continue        # nobody left on the other side for THIS
                                # attacker; a dying foe later in the order
                                # may still owe the party its last blow
            if attacker in moved:
                continue        # closing the distance was the action
            friendly = attacker in party_set or attacker.possessed > 0

            # A multi-target blow (the giant's sweep, the dragon's breath):
            # one attacker roll, resolved against each caught defender's own
            # defense. Sweeps don't queue for press room -- a wall of fire
            # doesn't care how crowded the line is -- and a fueled one
            # (sweep_cost_power) needs the Power, else it falls back to
            # single attacks. A wizard at fire rank 3 sweeps too: the
            # FIREBALL, one roll against up to FIREBALL_TARGETS foes,
            # thrown whenever 3+ stand (Power-priced, so it self-limits).
            # On an open field an arm's arc reaches gap 0 only; breath and
            # fireballs carry CAST_RANGE (the dragon breathes on a party
            # still crossing the ground).
            pool = [t for t in living_targets if not t.unseen]
            near = [t for t in pool if _gap(attacker, t) <= 0]
            thrown = [t for t in pool if _gap(attacker, t) <= CAST_RANGE]
            sweep_pool = thrown if attacker.sweep_cost_power else near
            sweeping = (attacker.sweep > 1 and len(sweep_pool) > 1
                        and (attacker.sweep_cost_power == 0
                             or attacker.cur_power
                             >= attacker.sweep_cost_power))
            if sweeping and attacker.sweep_cost_power == 0:
                # An arm's arc can't reach the sky; breath (fueled) can.
                sweep_pool = [t for t in sweep_pool if t.aloft <= 0]
                sweeping = len(sweep_pool) > 1
            fireball = (not sweeping
                        and attacker.spell_rank("fire") >= SPELL_RANK_MAX
                        and attacker.cur_power >= FIREBALL_POWER_COST
                        and len(thrown) >= FIREBALL_TARGETS)
            shooting = False
            if sweeping or fireball:
                n = attacker.sweep if sweeping else FIREBALL_TARGETS
                pick_from = sweep_pool if sweeping else thrown
                victims = rng.sample(pick_from, min(n, len(pick_from)))
            else:
                # Ranged combat: the wielder of a ranged card fights by its
                # rules -- shoot while the ground is open, switch to the
                # melee grip when contact forces it (the switch round is
                # the action), switch back when room opens again.
                w = attacker.weapon
                ranged_card = (w is not None and w.range > 0
                               and not attacker.weapon_broken)
                contact = any(_gap(attacker, t) == 0 for t in pool
                              if t.aloft <= 0)
                if ranged_card and contact and not attacker.switched:
                    # THE ARRIVAL VOLLEY: the round contact first arrives,
                    # a still-loaded shooter looses point-blank into
                    # whoever just charged in -- THEN the grip must change.
                    volley = None
                    if attacker.shot_ready:
                        volley = _pick_target(
                            targets, rng, focus=friendly, attacker=attacker,
                            reachable=lambda t: (t in arrived
                                                 and _gap(attacker, t) == 0))
                    if volley is not None:
                        _play(log,
                              f"    {attacker.name} looses point-blank "
                              f"into {volley.name}'s charge!",
                              f"    {attacker.name} looses point-blank "
                              f"into the charge!")
                        victims = [volley]
                        shooting = True
                        fired_shots.add(attacker)
                    else:
                        attacker.switched = True
                        _play(log,
                              f"    {attacker.name} is caught at arm's "
                              f"length -- they drop the {w.name} to a "
                              f"fighting grip ({w.melee_atk:+d} atk/"
                              f"{w.melee_sev:+d} sev, no shooting until "
                              f"there's room)!",
                              f"    {attacker.name} is caught at arm's "
                              f"length -- the {w.name} becomes a poor "
                              f"melee weapon!")
                        continue    # the switch is the round (free, like
                                    # circling -- no STA)
                if ranged_card and not contact and attacker.switched:
                    attacker.switched = False
                    log.append(f"    {attacker.name} finds room to breathe "
                               f"and brings the {w.name} back up.")
                    continue
                if attacker.ranged is not None and not contact:
                    # The shooting grip with open ground: loose, or work
                    # the reload. Shooters ignore the press both ways.
                    if attacker.shot_ready:
                        defender = _pick_target(
                            targets, rng, focus=friendly, attacker=attacker,
                            reachable=lambda t: 1 <= _gap(attacker, t)
                            <= w.range)
                        if defender is None:
                            _debug(log, f"    {attacker.name} holds -- "
                                        f"no target in range.")
                            continue
                        victims = [defender]
                        shooting = True
                        fired_shots.add(attacker)
                    elif attacker.reload_left > 0:
                        _debug(log, f"    {attacker.name} works the "
                                    f"{w.name}'s reload.")
                        continue
                    else:
                        _debug(log, f"    {attacker.name} is out of "
                                    f"{w.ammo or 'shots'} -- nothing to "
                                    f"shoot with.")
                        continue    # the movement phase will close them in
                if not shooting:
                    # Steel reaches gap 0; a caster's bolts reach
                    # CAST_RANGE at any gap (magic doesn't jam at contact).
                    can_cast = (attacker.default_cast() is not None
                                or (attacker.is_wizard
                                    and attacker.cur_power > 0))
                    max_reach = CAST_RANGE if can_cast else 0
                    defender = _pick_target(
                        targets, rng, focus=friendly,
                        engaged=engaged, attacker=attacker,
                        reachable=(None if field <= 0 else
                                   lambda t: _gap(attacker, t) <= max_reach))
                    if defender is None:
                        # Crowded out of the press (or nothing in reach):
                        # on an open field, slip DEEPER instead -- toward
                        # whoever is hanging back (the backline's escort
                        # problem); on a closed one, circle the round away
                        # (free, like defending).
                        if (field > 0 and attacker.adv < field
                                and any(_gap(attacker, t) > 0
                                        for t in living_targets)):
                            attacker.adv += 1
                            _play(log,
                                  f"    {attacker.name} slips through the "
                                  f"press, pushing deeper "
                                  f"(advance {attacker.adv}/{field}).",
                                  f"    {attacker.name} slips through the "
                                  f"press, pushing deeper!")
                        else:
                            log.append(f"    {attacker.name} circles, "
                                       f"crowded out of the press.")
                        continue
                    if _gap(attacker, defender) == 0:
                        engaged[defender] = engaged.get(defender, 0) + 1
                    victims = [defender]

            if not attacker.tireless and not dying:
                # The dying swing is free -- desperation costs nothing.
                was_winded = attacker.winded
                # The weapon sets the swing price (zweihander 2, most else 1);
                # a cast tires at the base rate -- the arm isn't swinging steel.
                cost = (STA_ATTACK_COST if attacker.default_cast()
                        else attacker.swing_cost)
                attacker.cur_sta = max(0, attacker.cur_sta - cost)
                if attacker.winded and not was_winded:
                    _play(log,
                          f"    !! {attacker.name} is Winded "
                          f"(STA {attacker.cur_sta} -- -{WINDED_PENALTY} "
                          f"to all rolls until they catch their breath)",
                          f"    !! {attacker.name} is Winded -- "
                          f"-{WINDED_PENALTY} to all rolls")
                if attacker.spent and attacker not in spent_logged:
                    # Covers both the swing that emptied the tank and walking
                    # into the fight already at 0.
                    spent_logged.add(attacker)
                    _play(log,
                          f"    !! {attacker.name} is SPENT -- running "
                          f"on empty (-{SPENT_PENALTY} to all rolls "
                          f"until the fight ends)",
                          f"    !! {attacker.name} is SPENT -- "
                          f"-{SPENT_PENALTY} to all rolls")
            if dying:
                log.append(f"    ({attacker.name} strikes even as they fall)")

            atk_roll = None
            sweep_cast = None
            if sweeping or fireball:
                if fireball:
                    attacker.cur_power -= FIREBALL_POWER_COST
                    sweep_cast = "fire"
                    label = "a roaring FIREBALL"
                    fuel_cost = FIREBALL_POWER_COST
                else:
                    if attacker.sweep_cost_power:
                        attacker.cur_power -= attacker.sweep_cost_power
                    label = attacker.sweep_label or "a great sweeping blow"
                    fuel_cost = attacker.sweep_cost_power
                names = ", ".join(v.name for v in victims)
                fuel = (f" [{fuel_cost} Power spent, "
                        f"{attacker.cur_power} left]" if fuel_cost else "")
                _play(log,
                      f"    {attacker.name} unleashes {label} -- "
                      f"{names} are caught in it!{fuel}",
                      f"    {attacker.name} unleashes {label} -- "
                      f"{names} are caught in it!")
                atk_roll = attacker.pressure(
                    rng, attacking=True, cast=sweep_cast,
                    wound_pen=start_pens[attacker] if dying else None)
            for defender in victims:
                was_alive = defender.alive
                # A single attack lets the wizard plan the exchange (disarm /
                # freeze / hurl / bolt -- choose_cast); a reused sweep roll
                # already knows what it is; a shot is a shot.
                if atk_roll is not None:
                    cast_kind = sweep_cast
                elif shooting:
                    cast_kind = None
                elif attacker.is_wizard:
                    cast_kind = attacker.choose_cast(defender)
                else:
                    cast_kind = "auto"
                if (not shooting and atk_roll is None
                        and _gap(attacker, defender) > 0):
                    # Only magic carries across open ground on this path:
                    # force a cast, never a steel swing at ten paces.
                    if cast_kind == "auto":
                        cast_kind = attacker.default_cast()
                    if cast_kind is None:
                        continue    # nothing that reaches -- hold
                _attack(attacker, defender, rng, log,
                        atk_wound_pen=start_pens[attacker] if dying else None,
                        def_mod=(-PAUSE_ACTION_DEF_PENALTY
                                 if defender in busy else 0),
                        def_label=busy_label.get(busy.get(defender, ""), ""),
                        atk_roll=atk_roll, cast=cast_kind, shot=shooting)
                if was_alive and not defender.alive:
                    if (defender.dead and defender.protagonist
                            and not defender.fate_debt
                            and any(h is not defender and not h.dead
                                    for h in party)):
                        # Fate's bargain (2026-07-10): the protagonist's
                        # death is commuted to a Down while a companion
                        # still draws breath. The price is collected at
                        # victory (_settle_fate_debt) -- one random
                        # companion for the protagonist's life. A fight the
                        # rest can't win is still a wipe.
                        defender.dead = False
                        defender.down = True
                        defender.fate_debt = True
                        log.append(f"    *** The blow should be "
                                   f"{defender.name}'s death -- and is not. "
                                   f"Fate has spared them; its price comes "
                                   f"due if this fight is won. ***")
                        log.append(f"    {defender.name} goes down, "
                                   f"out of the fight.")
                    elif defender.dead:
                        log.append(f"    *** {defender.name} is SLAIN. ***")
                    elif defender in party_set:
                        log.append(f"    {defender.name} goes down, "
                                   f"out of the fight.")
                    else:
                        log.append(f"    *** {defender.name} falls. ***")
        busy.clear()
        # Regeneration (the troll's puzzle): wounds knit at the end of every
        # round the regenerator is still up -- out-damage it or lose to it.
        # At 0 HP it stays down: dead-or-down flesh doesn't knit mid-fight.
        for e in actors:
            if e.alive and e.regen and e.hp < e.max_hp:
                before = e.hp
                e.hp = min(e.max_hp, e.hp + e.regen)
                _play(log,
                      f"    {e.name}'s wounds knit closed before their eyes "
                      f"(+{e.hp - before} HP -> {e.hp}/{e.max_hp}, "
                      f"-{e.wound_penalty} to rolls)",
                      f"    {e.name}'s wounds knit closed "
                      f"(+{e.hp - before} HP) [{e.name}: "
                      f"{e.hp}/{e.max_hp} HP]")
        # The reload clock ticks on any round the shooter didn't fire --
        # walking, circling, even switching grips works the nock/crank.
        for e in actors:
            if e.reload_left > 0 and e not in fired_shots:
                e.reload_left -= 1
        # Spell durations tick at round end: flight sets down, a seized
        # mind shakes free.
        for e in actors:
            if e.aloft > 0:
                e.aloft -= 1
                if e.aloft == 0 and e.alive:
                    log.append(f"    {e.name} alights -- back in "
                               f"steel's reach.")
            if e.possessed > 0:
                e.possessed -= 1
                if e.possessed == 0 and e.alive:
                    log.append(f"    *** The light returns to {e.name}'s "
                               f"eyes -- the puppet is free, and FURIOUS. "
                               f"***")
        _debug(log, _stamina_line(party, foes))

        if pause_triggers:
            crossings = _check_pause_triggers(party, foes, fired)
            if crossings:
                interrupts: list[tuple[str, Entity]] = []
                autos: list[tuple[str, Entity, str]] = []
                for kind, h in crossings:
                    order = ("pause" if standing_orders is None
                             else standing_orders(kind, h, party, foes))
                    if order == "pause":
                        interrupts.append((kind, h))
                    elif order is not None:
                        autos.append((kind, h, order))
                if interrupts:
                    for kind, h in interrupts:
                        if kind == "stamina":
                            log.append(f"    == {h.name} is nearly out of "
                                       f"breath (STA {h.cur_sta}/{h.sta}) -- "
                                       f"the fight hangs for a heartbeat. ==")
                        else:
                            log.append(f"    == {h.name} is badly cut up "
                                       f"(HP {h.hp}/{h.max_hp}) -- "
                                       f"the fight hangs for a heartbeat. ==")
                    # Re-arm the auto crossings instead of acting: an order
                    # queued now would be lost across the caller's
                    # save/resume boundary. Their condition still holds, so
                    # they re-trip at the end of the first resumed round.
                    for kind, h, _ in autos:
                        fired.discard((kind, h))
                    return Pause(round=rnd, crossings=interrupts)
                for kind, h, order in autos:
                    # One action per hero per round: a hero crossing both
                    # tracks at once acts on the later (wounds) order.
                    queued[h] = order

    # The dust settles: fate collects first, then whoever is still standing
    # catches their breath. A WON field is scavenged for spent missiles
    # before the per-fight states clear (a fled field is left, arrows and
    # all -- attempt_retreat clears without recovering). No spell state
    # outlasts the melee: the rime melts, fliers land, the unseen resolve,
    # puppets are released (a retreat clears the same states in
    # attempt_retreat / refresh_foes_after_retreat instead).
    if any(h.alive for h in party) and not any(f.alive for f in foes):
        _recover_missiles(party, rng, log)
    _clear_fight_states(party + foes)
    _settle_fate_debt(party, foes, rng, log)
    survivors = [h for h in party if h.alive]
    if survivors:
        _catch_breath(survivors, log)
    return None


def _recover_missiles(party: list[Entity], rng: random.Random,
                      log: list[str]) -> None:
    """Walk a WON field for the missiles spent on it: each arrow/bolt/knife
    recovers at RECOVER_HIT (stuck in a body) or RECOVER_MISS (lost in the
    grass) odds. Shells burn and stones aren't counted; the counters clear
    with the other per-fight states either way."""
    for h in party:
        w = h.weapon
        if w is None or w.ammo not in RECOVER_HIT:
            continue
        spent = h.shots_hit + h.shots_missed
        if spent == 0:
            continue
        got = sum(1 for _ in range(h.shots_hit)
                  if rng.random() < RECOVER_HIT[w.ammo])
        got += sum(1 for _ in range(h.shots_missed)
                   if rng.random() < RECOVER_MISS[w.ammo])
        if got:
            h.items[w.ammo] = min(AMMO_CAPS.get(w.ammo, got),
                                  h.items.get(w.ammo, 0) + got)
        log.append(f"    {h.name} walks the field and recovers {got} of "
                   f"the {spent} {w.ammo} spent "
                   f"({h.items.get(w.ammo, 0)} carried).")


def _clear_fight_states(entities: list[Entity]) -> None:
    """End-of-fight cleanup for every per-fight state: the ice rime,
    invisibility, flight, stuns, possession, the per-foe disarm-attempt
    marker -- and the field state (advances, the reload clock, the melee
    grip, the shot tallies). Nothing per-fight crosses fights."""
    for e in entities:
        e.dex_debuff = 0
        e.unseen = False
        e.aloft = 0
        e.stunned = 0
        e.possessed = 0
        e.disarm_tried = False
        e.adv = 0
        e.reload_left = 0
        e.switched = False
        e.shots_hit = 0
        e.shots_missed = 0


def _settle_fate_debt(party: list[Entity], foes: list[Entity],
                      rng: random.Random, log: list[str]) -> None:
    """Collect fate's price at the end of a melee (the protagonist bargain --
    see Entity.protagonist). Debts are cleared whatever happened; the price is
    only PAID on a victory: the last foe's dying strength kills one random
    companion (Down or standing -- fate is not particular). A lost or
    staggered-apart fight collects nothing (the wipe or the foes still
    standing are punishment enough), and a clean retreat waives the debt in
    attempt_retreat."""
    debtors = [h for h in party if h.fate_debt]
    if not debtors:
        return
    for h in debtors:
        h.fate_debt = False
    if any(f.alive for f in foes):
        return
    victims = [h for h in party if not h.dead and not h.protagonist]
    if not victims:
        return
    victim = rng.choice(victims)
    victim.hp = 0
    victim.down = False
    victim.dead = True
    log.append(f"    *** The last foe spends its dying strength on one final "
               f"blow -- fate's price for {debtors[0].name}'s life. It finds "
               f"{victim.name}. ***")
    log.append(f"    *** {victim.name} is SLAIN. ***")


# --------------------------------------------------------------------------- #
# Retreat & chase (the other exit from a paused fight)
# --------------------------------------------------------------------------- #

def _chase_dex(group: list[Entity]) -> float:
    """A side's speed in the break contest: average DEX weighted by current
    STA -- fresher legs count for more (tireless entities always weigh in at
    full). A side entirely out of breath falls back to a plain average.
    Frost-rimed legs (the ice school's debuff) run slower here too."""
    def dex(e: Entity) -> int:
        return max(0, e.dex - e.dex_debuff)
    total_weight = sum(max(0, e.cur_sta) for e in group)
    if total_weight == 0:
        return sum(dex(e) for e in group) / len(group)
    return sum(dex(e) * max(0, e.cur_sta) for e in group) / total_weight


def attempt_retreat(party: list[Entity], foes: list[Entity],
                    rng: random.Random, log: list[str],
                    field: int = 0) -> bool:
    """Break away from a paused fight. The procedure (deliberately ONE roll,
    no chase scenes): every foe fit to swing (alive, not Winded, not Spent)
    gets one free parting blow -- free like the dying swing, no STA cost --
    at a random fleeing hero, who defends at -PAUSE_ACTION_DEF_PENALTY.
    Parting blows ignore the press (CROWD_CAP is melee geometry; strikes at
    backs running past the line are not a press). Then
    one opposed group contest (2d6 + STA-weighted side-average DEX, the
    fleeing side at +FLEE_BONUS) decides the break -- but only foes that
    `pursues` give chase: the barrow's undead swing at the door and stop
    (bound to the grave), so retreat from the barrow always succeeds once
    past it.

    Returns True on a clean escape (the runners catch their breath -- the
    fight is over for them); False means the party is run down and the caller
    must resume the fight, the parting-blow damage already taken. Either way
    heroes can go Down or die here: check party_wiped afterward.
    """
    log.append("  The party breaks for safety!")
    swingers = [f for f in foes if f.alive and not f.winded and not f.spent]
    for f in swingers:
        targets = [h for h in party if h.alive]
        if not targets:
            break               # everyone is down mid-flight; nothing to chase
        h = rng.choice(targets)
        # Parting blows are softened one tier (see _attack): a swing at a
        # fleeing back can maim, never land the crippling tier. On an open
        # field (ranged combat) reach gates who gets one at all: steel
        # needs contact, a ready shooter looses a parting SHOT across the
        # ground (fleeing crosses the open -- exactly a bow's moment), a
        # caster bolts within CAST_RANGE, and everyone else watches them go.
        gap = (max(0, field - f.adv - h.adv) if field > 0 else 0)
        if gap == 0:
            _attack(f, h, rng, log, def_mod=-PAUSE_ACTION_DEF_PENALTY,
                    def_label="fleeing", soften=True)
        elif f.shot_ready and gap <= f.ranged.range:
            _attack(f, h, rng, log, def_mod=-PAUSE_ACTION_DEF_PENALTY,
                    def_label="fleeing", soften=True, shot=True)
        elif f.default_cast() is not None and gap <= CAST_RANGE:
            _attack(f, h, rng, log, def_mod=-PAUSE_ACTION_DEF_PENALTY,
                    def_label="fleeing", soften=True)
        else:
            continue    # out of reach: no blow at this back
        if not h.alive:
            if h.dead:
                log.append(f"    *** {h.name} is SLAIN. ***")
            else:
                log.append(f"    {h.name} goes down, out of the fight.")

    runners = [h for h in party if h.alive]
    if not runners:
        return False    # cut down at the door -- the caller sees the wipe

    pursuers = [f for f in swingers if f.alive and f.pursues]
    if not pursuers:
        if any(f.alive and not f.pursues for f in foes):
            log.append("    The dead do not follow beyond their ground -- "
                       "clean escape.")
        else:
            log.append("    No one is fit to give chase -- clean escape.")
        for h in party:
            h.fate_debt = False     # a fled fight is not a won one: waived
        _clear_fight_states(party)  # the spell states drop on the run
        _catch_breath(runners, log)
        return True

    flee_dex = _chase_dex(runners)
    hunt_dex = _chase_dex(pursuers)
    flee_dice = rng.randint(1, 6) + rng.randint(1, 6)
    hunt_dice = rng.randint(1, 6) + rng.randint(1, 6)
    flee_total = flee_dice + flee_dex + FLEE_BONUS
    hunt_total = hunt_dice + hunt_dex
    _debug(log, f"    the chase: flight {flee_total:.1f} (2d6={flee_dice}, "
                f"+{flee_dex:.1f} DEX STA-weighted, +{FLEE_BONUS} head start) "
                f"vs pursuit {hunt_total:.1f} (2d6={hunt_dice}, "
                f"+{hunt_dex:.1f} DEX STA-weighted)")
    if flee_total >= hunt_total:
        log.append("    They break away -- clean escape.")
        for h in party:
            h.fate_debt = False     # a fled fight is not a won one: waived
        _clear_fight_states(party)  # the spell states drop on the run
        _catch_breath(runners, log)
        return True
    log.append("    *** RUN DOWN -- the pursuers catch them, and the fight "
               "resumes with their backs to it. ***")
    return False


def blink_escape(party: list[Entity], foes: list[Entity], wizard: Entity,
                 rng: random.Random, log: list[str]) -> bool:
    """Teleport rank 2, BLINK OUT: the wizard tears a door in the air and
    the whole party steps through -- NO parting blows, NO chase roll (the
    two costs the ordinary retreat is priced in). Charges
    TELEPORT_ESCAPE_COST Power and rolls the casting check at rank 2; a
    fizzled door leaves the party standing at it -- the caller falls back
    to an honest retreat (attempt_retreat), blows and all. A clean blink
    waives any fate debt like any clean escape."""
    if wizard.spell_rank("teleport") < 2:
        log.append(f"    {wizard.name}'s teleport art can't carry a party "
                   f"out of a melee (rank 2 needed).")
        return False
    if wizard.cur_power < TELEPORT_ESCAPE_COST:
        log.append(f"    {wizard.name} lacks the Power to tear the door "
                   f"open ({wizard.cur_power}/{TELEPORT_ESCAPE_COST}).")
        return False
    wizard.cur_power -= TELEPORT_ESCAPE_COST
    result = casting_check(wizard, "teleport", 2, rng, log)
    if result == "misfire":
        _misfire(wizard, "teleport", log)
        return False
    if result == "fizzle":
        log.append(f"    {wizard.name} tears at the air -- and it holds. "
                   f"The door won't open ({TELEPORT_ESCAPE_COST} Power "
                   f"wasted); the party must run for it.")
        return False
    if result == "crit":
        wizard.cur_power += TELEPORT_ESCAPE_COST
    log.append(f"  *** {wizard.name} tears a door in the air -- the party "
               f"steps through and is GONE. No blade falls, nothing gives "
               f"chase. ***")
    for h in party:
        h.fate_debt = False     # a fled fight is not a won one: waived
    _clear_fight_states(party)
    runners = [h for h in party if h.alive]
    if runners:
        _catch_breath(runners, log)
    return True


def refresh_foes_after_retreat(foes: list[Entity],
                               days_passed: int) -> list[Entity]:
    """The room the party fled from, readied for a return trip (encounter
    persistence). The dead stay dead. Foe STA refills the moment the party
    leaves (they rest too). LIVING foes heal their wounds once a day has
    passed; the undead stay hacked -- dead bone doesn't knit, which is exactly
    the asymmetry that rewards a return trip to the barrow."""
    survivors = [f for f in foes if not f.dead]
    _clear_fight_states(survivors)  # no spell state survives to a return trip
    for f in survivors:
        f.cur_sta = f.sta
        if f.regen or (days_passed > 0 and not f.undead):
            # A fled regenerator is a healed one, same day or not -- the
            # camp-and-return loop does not work on a troll.
            f.hp = f.max_hp
            f.down = False
        if f.weapon is not None and f.weapon.ammo in AMMO_CAPS:
            # The field is theirs: its shooters gather their own missiles
            # back to a full quiver while the party is gone.
            f.items[f.weapon.ammo] = max(f.items.get(f.weapon.ammo, 0),
                                         FOE_AMMO)
    return survivors


# --------------------------------------------------------------------------- #
# Character generation
# --------------------------------------------------------------------------- #

# Rolled ranges for a starting hero. 3-6 straddles the human bands in rules.md:
# a 3 is trained-soldier grade, a 6 nudges past elite-veteran. HP 8-12 likewise.
HERO_STAT_RANGE = (3, 6)      # DEX / STR
# The hero death spiral, geared down (2026-07-09, the "less binary outcomes"
# retune): trained fighters are pain 2 -- wound penalty = HP lost // 2 -- and
# so are the humanoid FOES (sites.py rows), symmetrically. At pain 1 the
# first decisive exchange decided everything: whoever bled first spiraled
# into helplessness, so encounters split into "took 0 damage" and "died"
# with nothing in between. Halving the spiral (both sides) keeps wounded
# fighters dangerous, which is what populates the 25-75%-HP-lost middle.
# pain 1 is now the SOFT tier (small critters that feel everything).
HERO_PAIN = 2
# STA gets its own, higher range: it is the second death-track (the swing
# budget; running dry mid-fight is usually fatal), so its floor matters like
# HP's floor -- a 4-STA hero is a 4-swing hero, and the batch sims show those
# parties are the wipes. Floor 5 also keeps a fresh hero two swings clear of
# the Winded line (WINDED_STA = 3).
HERO_STA_RANGE = (5, 8)
HERO_HP_RANGE = (8, 12)
HERO_POWER_RANGE = (3, 6)
# Fixed-budget generation (2026-07-13, designer call): every character gets
# the same number of surplus points above the range floors, dealt out by a
# randomly-ordered stat PRIORITY (weighted toward the front of the order), so
# builds differ in SHAPE, never in total -- recruiting compares tradeoffs
# instead of point sums. Racial floor mods (people.RACE_MODS) raise a stat's
# floor UNDER the budget, so they stay a genuine net extra: races remain
# unequal on purpose. 9 was the old independent rolls' mean surplus over six
# stats; MIND (2026-07-15, the Magic & Mind add-on) is a seventh budget
# line, so the budget rose to 11 to keep the per-stat surplus ~unchanged.
HERO_STAT_BUDGET = 11

# The sims' throwaway name pool (the played game draws from people.py's
# per-race pools instead). The old stat epithet ("the precise") is GONE
# (2026-07-11): it was a stat-tell in costume, and the trait system does its
# one job -- flavor at introduction -- better.
NAMES = ["Brand", "Sela", "Corvin", "Mira", "Doran", "Yssa", "Kael", "Rhea",
         "Tomas", "Inga", "Veld", "Nessa"]


def random_kit(rng: random.Random) -> dict[str, int]:
    """Two random potions at creation -- the whole starting stock. Nothing
    refills for free; further potions are bought with gold or dropped."""
    kit = {k: 0 for k in STOCKED_POTION_KINDS}
    for _ in range(STARTING_POTIONS):
        kit[rng.choice(STOCKED_POTION_KINDS)] += 1
    return kit


def _adjusted_range(base: tuple[int, int], floor_up: int = 0,
                    ceiling_down: int = 0) -> tuple[int, int]:
    """Racial/trait stat modifiers move a roll's FLOOR up (never the ceiling
    -- the natural cap 6 holds, see rules.md's 1-20 doctrine) or its CEILING
    down; stacked adjustments can never invert the range."""
    lo, hi = base[0] + floor_up, base[1] - ceiling_down
    return (min(lo, hi), hi) if lo > hi else (lo, hi)


def make_human(rng: random.Random, name: str,
               floors: dict[str, int] | None = None,
               ceilings: dict[str, int] | None = None) -> Entity:
    """Fixed-budget generation (2026-07-13): ranges DEX/STR/MIND/POWER/CHA
    3-6, STA 5-8, HP 8-12; every character starts at the floors and receives
    exactly HERO_STAT_BUDGET surplus points, dealt by a randomly-shuffled
    stat priority (linear weights down the order, each stat capped at its
    ceiling) -- equal totals, different shapes. Plus a random ability
    (heal / bulwark / first_blood), two random potions, and a starting
    weapon (the common table: 50% crude / 45% soldier's arms / 5% heavy;
    healers often carry the wooden staff). `floors`/`ceilings` shift the
    ranges per key ("dex", "str", "cha", "hp") -- the racial/trait hook
    (people.py: an orc's STR floor is 4 and the point is a NET extra under
    the budget; the "short" trait caps STR at 5).

    Magic & Mind (2026-07-15): MIND strictly above BOTH other combat stats
    makes a WIZARD -- a rolled school (fire/ice) known at rank 1 instead of
    an ability. POWER stays its own rolled pool: the fuel is qi, not iq --
    it never derives from MIND (designer call)."""
    floors = floors or {}
    ceilings = ceilings or {}
    ranges = {"dex": HERO_STAT_RANGE, "str": HERO_STAT_RANGE,
              "mind": HERO_STAT_RANGE,
              "sta": HERO_STA_RANGE, "hp": HERO_HP_RANGE,
              "power": HERO_POWER_RANGE, "cha": HERO_CHA_RANGE}
    lo, hi, stats = {}, {}, {}
    for key, base in ranges.items():
        lo[key], hi[key] = _adjusted_range(base, floors.get(key, 0),
                                           ceilings.get(key, 0))
        stats[key] = lo[key]
    order = list(ranges)
    rng.shuffle(order)                      # the build's priority spine
    weight = {key: len(order) - i for i, key in enumerate(order)}
    for _ in range(HERO_STAT_BUDGET):
        open_keys = [k for k in order if stats[k] < hi[k]]
        if not open_keys:
            break
        k = rng.choices(open_keys, [weight[k] for k in open_keys])[0]
        stats[k] += 1

    # MIND strictly above BOTH other combat stats makes a WIZARD -- a
    # school spell at rank 1 instead of an ability (CHA and POWER stay out
    # of the comparison: one is social, the other is fuel).
    ability, school = None, ""
    if stats["mind"] > stats["dex"] and stats["mind"] > stats["str"]:
        school = rng.choice(list(SCHOOLS))
    else:
        ability = rng.choice(["heal", "bulwark", "first_blood"])
    if ((ability == "heal" and rng.random() < HEALER_STAFF_CHANCE)
            or (school and rng.random() < WIZARD_STAFF_CHANCE)):
        weapon = WEAPONS["wooden staff"]    # the caster-bridge weapon at home
                                            # in a healer's (or wizard's) hands
    else:
        weapon = random_common_weapon(rng)
    return Entity(
        name=name,
        dex=stats["dex"],
        str_=stats["str"],
        mind=stats["mind"],
        sta=stats["sta"],
        max_hp=stats["hp"],
        power=stats["power"],
        cha=stats["cha"],
        ability=ability,
        school=school,
        spells={school: 1} if school else {},
        pain=HERO_PAIN,
        weapon=weapon,
        items=random_kit(rng),
    )


def make_party(rng: random.Random) -> list[Entity]:
    names = rng.sample(NAMES, 2)
    return [make_human(rng, names[0]), make_human(rng, names[1])]


def weapon_tag(e: Entity) -> str:
    """Short wielded-weapon readout for stat lines: name, BROKEN flag, and the
    proficiency rank with it (if any)."""
    if e.weapon is None:
        return "unarmed"
    tag = e.weapon.name + (" (BROKEN)" if e.weapon_broken else "")
    rank = e.proficiency.get(e.weapon.name, 0)
    if rank:
        tag += f", prof {rank}"
    return tag


def stat_line(e: Entity) -> str:
    """One-line body readout. Every drainable track shows cur/max -- current
    STA is THE number the play protocol turns on (dm.md: check it before
    every fight), so it must never have to be scraped off a combat log.
    CHA appears only where it was rolled (heroes); satisfaction only where
    it is tracked (hired companions) -- both are play-critical numbers
    (capacity / who is about to quit), never combat-log noise."""
    kit = ", ".join(f"{k}x{v}" for k, v in e.items.items() if v) or "no kit"
    cha = f"CHA {e.cha}  " if e.cha else ""
    mind = f"MIND {e.mind}  " if e.mind else ""
    if e.spells:
        gift = "spells: " + ", ".join(f"{n} {r}"
                                      for n, r in sorted(e.spells.items()))
    else:
        gift = e.ability or "no save"
    line = (f"{e.name} (L{e.level}, training {e.training}): "
            f"DEX {e.dex}  STR {e.str_}  {mind}STA {e.cur_sta}/{e.sta}  "
            f"HP {e.hp}/{e.max_hp}  Power {e.cur_power}/{e.power}  {cha}"
            f"({gift}; {weapon_tag(e)}; {kit})")
    if e.satisfaction is not None:
        line += f"  [satisfaction {e.satisfaction}/{SATISFACTION_MAX}]"
    return line


def progress_line(e: Entity) -> str:
    """The allocation sheet to pair with stat_line: XP toward the next level,
    banked skill points, drilled proficiencies. Everything the player SPENDS
    lives here; stat_line above is the body."""
    parts = [f"XP {e.xp}/{xp_to_next(e.level)} to L{e.level + 1}",
             f"skill points: {e.skill_points}"]
    profs = ", ".join(f"{n} {r}" for n, r in sorted(e.proficiency.items()) if r)
    if profs:
        parts.append(f"proficiency: {profs}")
    if e.spells:
        parts.append("spells: " + ", ".join(
            f"{n} {r}" for n, r in sorted(e.spells.items())))
    return " | ".join(parts)


def fallen_weapons_line(foes: list[Entity]) -> str | None:
    """The loot gesture after a cleared fight: what steel the fallen leave
    behind, with just enough stats to decide on (the DM offers, the player
    takes via `give`). Shattered weapons and worthless grave-steel (value 0,
    e.g. the skeletons' rusted blades) aren't worth a line. Returns None if
    there is nothing to mention."""
    drops: dict[str, tuple[Weapon, int]] = {}
    for f in foes:
        w = f.weapon
        if f.alive or w is None or f.weapon_broken or w.value <= 0:
            continue
        drops[w.name] = (w, drops.get(w.name, (w, 0))[1] + 1)
    if not drops:
        return None
    bits = []
    for name, (w, count) in drops.items():
        n = f"{count}x " if count > 1 else "a "
        bits.append(f"{n}{name} ({w.atk_pressure:+d} atk/{w.severity:+d} sev, "
                    f"{w.value}g)")
    return "  Left among the dead: " + ", ".join(bits) + "."


# --------------------------------------------------------------------------- #
# Progression & economy
# --------------------------------------------------------------------------- #

def xp_to_next(level: int) -> int:
    return XP_LEVEL_STEP * level


def pool_growth_due(level: int) -> bool:
    """Does REACHING `level` grant the pool growth? +1 HP/STA/Power per
    POOL_GROWTH_LEVELS levels: the odd levels (3, 5, 7...) each add one,
    so total growth at level L is (L-1) // 2."""
    return level > 1 and (level - 1) % POOL_GROWTH_LEVELS == 0


def grow_pools(h: Entity) -> None:
    """One step of the level pool growth: +1 max HP, STA, and Power, the
    current pools rising with their maxima (training hardens the living body,
    it doesn't heal wounds -- a Down hero's HP stays where it fell)."""
    h.max_hp += 1
    if h.hp > 0:
        h.hp += 1
    h.sta += 1
    h.cur_sta += 1
    h.power += 1
    h.cur_power += 1
    h.hp_regen_per_night = max(1, round(h.max_hp / 7))


HERO_QUALITY_LEVEL = 4      # levels from which a generated character carries
                            # quality steel (the reference-progression
                            # doctrine -- see bench_bestiary.py's duo)


def develop_hero(h: Entity, level: int, rng: random.Random) -> Entity:
    """Grow a fresh level-1 roll into a level-`level` character in place --
    the generator for recruits and leveled NPCs (people.make_character calls
    it). Follows the reference-progression doctrine bench_bestiary.py's duo
    was calibrated with: monotone spend (training to 3, then proficiency,
    then training to the cap -- a build must never get WEAKER with levels),
    quality steel from HERO_QUALITY_LEVEL, the engine pool curve. Points the
    monotone spend can't afford stay banked (a hired recruit arrives with
    their history mostly spent -- choosing between candidates IS the
    customization -- but may carry a point or two to allocate).

    The one divergence from the bench reference: the quality weapon SUITS
    the frame instead of always being the katana -- a healer keeps the
    staff, a STR frame takes the zweihander, a DEX frame the rapier."""
    h.level = level
    points = level - 1

    def buy_training(cap: int) -> None:
        nonlocal points
        while h.training < cap and points >= h.training + 1:
            points -= h.training + 1
            h.training += 1

    buy_training(3)
    if level >= HERO_QUALITY_LEVEL:
        if ((h.ability == "heal" or h.school) and h.weapon is not None
                and h.weapon.name == "wooden staff"):
            pass                                    # the staff IS quality
        elif h.str_ > h.dex:
            h.weapon = WEAPONS["zweihander"]
        elif h.dex > h.str_:
            h.weapon = WEAPONS["rapier"]
        else:
            h.weapon = WEAPONS["katana"]
    # The proficiency sink: a wizard drills the SCHOOL SPELL (their real
    # offense); everyone else drills the wielded weapon.
    if h.school:
        rank = h.spells.get(h.school, 1)
        cap = SPELLS[h.school].max_rank
        while rank < cap and points >= rank + 1:
            points -= rank + 1
            rank += 1
        h.spells[h.school] = rank
    elif h.weapon is not None:
        rank = h.proficiency.get(h.weapon.name, 0)
        while rank < PROFICIENCY_MAX and points >= rank + 1:
            points -= rank + 1
            rank += 1
        if rank:
            h.proficiency[h.weapon.name] = rank
    buy_training(TRAINING_MAX)
    h.skill_points = points
    for lvl in range(2, level + 1):
        if pool_growth_due(lvl):
            grow_pools(h)
    return h


# --------------------------------------------------------------------------- #
# Companion satisfaction (the retention layer -- session play only)
# --------------------------------------------------------------------------- #

def has_trait(e: Entity, name: str) -> bool:
    """Trait check by canonical name; detail in parentheses is ignored
    ("has a child (Timo, age 9)" carries the trait "has a child")."""
    return any(v.split(" (")[0] == name for v in e.traits.values())


def satisfaction_tracked(e: Entity) -> bool:
    return e.satisfaction is not None and not e.protagonist


def leave_threshold(e: Entity) -> int:
    """Where this companion quits: 0 for most, the hard floor for the LOYAL
    (they stay past the breaking point -- to a point)."""
    return SATISFACTION_FLOOR if has_trait(e, "loyal") else 0


def wants_to_leave(e: Entity) -> bool:
    return (satisfaction_tracked(e) and not e.dead
            and e.satisfaction <= leave_threshold(e))


def adjust_satisfaction(e: Entity, delta: int, log: list[str], reason: str,
                        injury: bool = False) -> None:
    """Move a companion's satisfaction, with the temperament scaling on
    injury-side losses (COWARDLY doubles, BRAVE halves toward zero) and the
    two legibility crossings logged: the warning at SATISFACTION_WARN and
    the notice at the leave threshold. No-op for untracked entities."""
    if not satisfaction_tracked(e) or delta == 0:
        return
    if injury and delta < 0:
        if has_trait(e, "cowardly"):
            delta *= 2
        elif has_trait(e, "brave"):
            delta = -(-delta // 2)      # halved, rounded toward zero: a
                                        # brave companion shrugs off a -1
    if delta == 0:
        return
    old = e.satisfaction
    e.satisfaction = max(SATISFACTION_FLOOR,
                         min(SATISFACTION_MAX, old + delta))
    if e.satisfaction == old:
        return
    log.append(f"    {e.name}: satisfaction {old} -> "
               f"{e.satisfaction}/{SATISFACTION_MAX} ({reason})")
    threshold = leave_threshold(e)
    if old > threshold >= e.satisfaction:
        log.append(f"    *** {e.name} has had enough -- they will leave the "
                   f"party at the next settlement (unless something lifts "
                   f"their spirits first). ***")
    elif (threshold < 0 and old > 0 >= e.satisfaction):
        log.append(f"    {e.name} is past caring, but loyalty holds them -- "
                   f"for now.")
    elif old > SATISFACTION_WARN >= e.satisfaction:
        log.append(f"    ({e.name} has gone quiet -- their patience is "
                   f"wearing thin.)")


def satisfaction_after_fight(party: list[Entity], dead_before: list[str],
                             log: list[str], fled: bool = False) -> None:
    """The post-fight morale pass (session play calls it after every settled
    encounter; the sims never do -- no sim entity is tracked). Blood and
    fear, per surviving tracked companion: fled, Down, bloodied (below half
    HP -- Down supersedes it), and having watched a party member die this
    fight (`dead_before` names who was already dead when it started). A dead
    companion's bond partner takes it hardest: whatever their satisfaction
    was, the heart goes out of them."""
    new_dead = [h for h in party if h.dead and h.name not in dead_before]
    dead_names = ", ".join(h.name for h in new_dead)
    for h in party:
        if not satisfaction_tracked(h) or h.dead:
            continue
        if fled:
            adjust_satisfaction(h, SAT_FLED, log, "the party fled",
                                injury=True)
        if h.down:
            adjust_satisfaction(h, SAT_DOWN, log, "beaten to the floor",
                                injury=True)
        elif h.hp * 2 <= h.max_hp:
            adjust_satisfaction(h, SAT_BLOODIED, log, "badly bloodied",
                                injury=True)
        if new_dead:
            adjust_satisfaction(h, SAT_DEATH_WITNESS, log,
                                f"watched {dead_names} die", injury=True)
    for d in new_dead:
        if not d.bond:
            continue
        partner = next((h for h in party if h.name == d.bond
                        and not h.dead), None)
        if partner is None or not satisfaction_tracked(partner):
            continue
        if partner.satisfaction > 0:
            adjust_satisfaction(partner, -partner.satisfaction, log,
                                f"{d.name} is dead -- the heart goes out "
                                f"of them")


def award_xp(party: list[Entity], amount: int, log: list[str],
             reason: str = "") -> None:
    """XP pays the JOB, not the head (the party-size counterweight): awards
    are quoted at the two-hero baseline and every hero who is not truly dead
    earns amount * XP_PARTY_BASELINE / party size -- the same number to each,
    so the party still levels together. A duo gets the listed award unchanged;
    four swords split the wages; a solo who overcame the same work earns
    double. The divisor is the party as constituted (the dead still count --
    no XP windfall for losing a companion mid-run). Handles level-ups and
    banks skill points."""
    share = max(1, round(amount * XP_PARTY_BASELINE / len(party)))
    note = f" ({reason})" if reason else ""
    for h in party:
        if h.dead:
            continue
        h.xp += share
        log.append(f"    {h.name} gains {share} XP{note} "
                   f"[{h.xp}/{xp_to_next(h.level)}]")
        while h.level < LEVEL_CAP and h.xp >= xp_to_next(h.level):
            h.xp -= xp_to_next(h.level)
            h.level += 1
            h.skill_points += SKILL_POINTS_PER_LEVEL
            grown = ""
            if pool_growth_due(h.level):
                grow_pools(h)
                grown = (f" Pools grow: HP {h.hp}/{h.max_hp}, "
                         f"STA {h.cur_sta}/{h.sta}, "
                         f"Power {h.cur_power}/{h.power}.")
            log.append(f"    *** {h.name} reaches level {h.level}! "
                       f"(+{SKILL_POINTS_PER_LEVEL} skill point, "
                       f"{h.skill_points} unspent){grown} ***")


def train_combat_once(h: Entity, log: list[str]) -> bool:
    """Spend skill points on ONE rank of combat training (rank n costs n,
    +1 to ALL pressure rolls per rank, cap TRAINING_MAX). The session-play shape:
    with proficiency as a second sink, each point is a real player choice now
    (session.py `train`), so nothing auto-spends in real play."""
    if h.training >= TRAINING_MAX:
        log.append(f"    {h.name} is already at the combat training cap "
                   f"({TRAINING_MAX}).")
        return False
    cost = h.training + 1
    if h.skill_points < cost:
        log.append(f"    {h.name} needs {cost} skill point(s) for combat "
                   f"training rank {h.training + 1} (has {h.skill_points}).")
        return False
    h.skill_points -= cost
    h.training += 1
    log.append(f"    {h.name} trains: combat training rank {h.training} "
               f"(+{h.training} to all pressure rolls) "
               f"[{h.skill_points} point(s) left]")
    return True


def train_proficiency(h: Entity, log: list[str]) -> bool:
    """Spend skill points on ONE rank of proficiency with the WIELDED weapon
    (+1 attack pressure AND +1 severity with that weapon per rank; rank n costs
    n; cap PROFICIENCY_MAX). Narrower than combat training -- offense only,
    one weapon type -- so it's stronger per rank. Per weapon TYPE: a
    replacement rapier keeps your rapier ranks; switching weapons drops the
    layer until you drill the new one (the commitment cost). A player choice
    (session.py `train`); the sims never buy it."""
    if h.weapon is None:
        log.append(f"    {h.name} has no weapon to drill with.")
        return False
    if h.weapon_broken:
        log.append(f"    {h.name}'s {h.weapon.name} is broken -- "
                   f"nothing to drill with.")
        return False
    name = h.weapon.name
    rank = h.proficiency.get(name, 0)
    if rank >= PROFICIENCY_MAX:
        log.append(f"    {h.name} has mastered the {name} "
                   f"(cap {PROFICIENCY_MAX}).")
        return False
    cost = rank + 1
    if h.skill_points < cost:
        log.append(f"    {h.name} needs {cost} skill point(s) for {name} "
                   f"proficiency rank {rank + 1} (has {h.skill_points}).")
        return False
    h.skill_points -= cost
    h.proficiency[name] = rank + 1
    log.append(f"    {h.name} drills with the {name}: proficiency rank "
               f"{rank + 1} (+{rank + 1} attack pressure and +{rank + 1} "
               f"severity with it) [{h.skill_points} point(s) left]")
    return True


def train_spell(h: Entity, name: str, log: list[str]) -> bool:
    """Spend skill points on ONE rank of a KNOWN spell (the Magic & Mind
    add-on) -- the weapon-proficiency chassis wholesale: rank n costs n,
    cap the spell's max_rank (usually SPELL_RANK_MAX). What a rank buys is
    the spell's own ladder (SPELLS[name].ranks): attack spells gain +1
    pressure AND +1 severity per rank like a drilled weapon, and rank 3 is
    the signature technique; openers/utility spells deepen in effect.
    Wizards only, and the spell must already be KNOWN (rolled at creation,
    or learned from a spellbook -- learn_spell)."""
    if not h.is_wizard:
        log.append(f"    {h.name} has no gift for magic to train.")
        return False
    spell = SPELLS.get(name)
    if spell is None:
        log.append(f"    No such spell: {name!r}. "
                   f"Spells: {', '.join(sorted(SPELLS))}.")
        return False
    rank = h.spells.get(name)
    if rank is None:
        log.append(f"    {h.name} has not learned {name} -- a spellbook "
                   f"teaches it ({SPELLBOOK_PRICE}g, capitals).")
        return False
    if rank >= spell.max_rank:
        log.append(f"    {h.name} has mastered {name} "
                   f"(cap {spell.max_rank}).")
        return False
    cost = rank + 1
    if h.skill_points < cost:
        log.append(f"    {h.name} needs {cost} skill point(s) for {name} "
                   f"rank {rank + 1} (has {h.skill_points}).")
        return False
    h.skill_points -= cost
    h.spells[name] = rank + 1
    log.append(f"    {h.name} deepens their {name}: rank {rank + 1} -- "
               f"{spell.ranks[rank]} [{h.skill_points} point(s) left]")
    return True


def learn_spell(h: Entity, name: str, log: list[str]) -> bool:
    """Learn a NEW spell at rank 1 (the spellbook's teaching -- the gold
    gate on breadth; ranks past 1 are skill points, train_spell). Wizards
    only: the gift is rolled at creation, a book can't grant it."""
    if not h.is_wizard:
        log.append(f"    {h.name} has no gift for magic -- the book is "
                   f"just diagrams to them.")
        return False
    spell = SPELLS.get(name)
    if spell is None:
        log.append(f"    No such spell: {name!r}. "
                   f"Spells: {', '.join(sorted(SPELLS))}.")
        return False
    if name in h.spells:
        log.append(f"    {h.name} already knows {name} "
                   f"(rank {h.spells[name]}).")
        return False
    h.spells[name] = 1
    log.append(f"    {h.name} studies the book and learns {name} (rank 1: "
               f"{spell.ranks[0]}).")
    return True


def buy_spellbook(h: Entity, purse: Purse, name: str, log: list[str]) -> bool:
    """Buy the spellbook that teaches `name` and learn it on the spot -- a
    between-adventures DM call (same shape as buy_weapon; session gates it
    to capitals). SPELLBOOK_PRICE gold from the party purse."""
    spell = SPELLS.get(name)
    if spell is None:
        log.append(f"    No such spell: {name!r}. "
                   f"Spells: {', '.join(sorted(SPELLS))}.")
        return False
    if not h.is_wizard or name in h.spells:
        return learn_spell(h, name, log)    # emits the right refusal
    if purse.gold < SPELLBOOK_PRICE:
        log.append(f"    Not enough gold for the {name} spellbook "
                   f"({purse.gold}g / {SPELLBOOK_PRICE}g).")
        return False
    purse.gold -= SPELLBOOK_PRICE
    log.append(f"    {h.name} buys the {name} spellbook for "
               f"{SPELLBOOK_PRICE}g (purse: {purse.gold}g).")
    return learn_spell(h, name, log)


def autospend_points(h: Entity, log: list[str]) -> bool:
    """COMPANION self-improvement (2026-07-13): spend a companion's banked
    points on the reference doctrine develop_hero uses -- combat training to
    rank 3, then proficiency IF the carried weapon is quality steel (nobody
    drills a club) -- a wizard companion drills the SCHOOL instead, always
    (the gift is always worth drilling) -- then training to the cap.
    session.py runs this for
    party[1:] after every fight's awards (and at hire); the PC's points are
    never touched -- spending them stays the player's decision. Returns
    whether anything was bought (the train_* calls log each purchase)."""
    bought = False

    def training_to(cap: int) -> None:
        nonlocal bought
        while (h.training < cap
               and h.skill_points >= h.training + 1
               and train_combat_once(h, log)):
            bought = True

    training_to(3)
    if h.school:
        while (h.skill_points >= h.spells.get(h.school, 1) + 1
               and h.spells.get(h.school, 1) < SPELLS[h.school].max_rank
               and train_spell(h, h.school, log)):
            bought = True
    elif (h.weapon is not None and h.weapon.quality
            and not h.weapon_broken):
        while (h.skill_points >= h.proficiency.get(h.weapon.name, 0) + 1
               and h.proficiency.get(h.weapon.name, 0) < PROFICIENCY_MAX
               and train_proficiency(h, log)):
            bought = True
    training_to(TRAINING_MAX)
    return bought


def train_combat(h: Entity, log: list[str]) -> bool:
    """Greedy auto-spend on combat training -- the SIM policy only
    (sites.run_site calls it after quest awards so tune.py / bench_training.py
    model a party that spends its points). Real play never auto-spends:
    session.py banks the points and the player chooses via `train`."""
    trained = False
    while h.training < TRAINING_MAX and h.skill_points > h.training:
        h.skill_points -= h.training + 1
        h.training += 1
        trained = True
        log.append(f"    {h.name} trains: combat training rank {h.training} "
                   f"(+{h.training} to all pressure rolls)")
    return trained


def roll_loot(party: list[Entity], purse: Purse, rng: random.Random,
              log: list[str]) -> None:
    """Per encounter won: a small chance of loose coin and of a stray potion.
    Trash-tier drops on purpose -- the real income is quest rewards."""
    living = [h for h in party if not h.dead]
    if not living:
        return
    if rng.random() < DROP_GOLD_CHANCE:
        purse.gold += DROP_GOLD_AMOUNT
        log.append(f"    Loot: {DROP_GOLD_AMOUNT} gold scavenged "
                   f"(purse: {purse.gold}g).")
    if rng.random() < DROP_POTION_CHANCE:
        kind = rng.choice(STOCKED_POTION_KINDS)
        h = rng.choice(living)
        h.items[kind] = h.items.get(kind, 0) + 1
        log.append(f"    Loot: a {kind} potion -- {h.name} pockets it "
                   f"({kind} x{h.items[kind]}).")


def cha_gold_bonus(party: list[Entity], gold: int) -> int:
    """The PC's negotiation edge: +CHA_GOLD_BONUS_PER_POINT of the quoted
    gold per CHA point above the capacity base, capped at CHA_GOLD_BONUS_CAP.
    GOLD ONLY, never XP (an XP bonus would compound into CHA being the best
    stat in the game). Zero when no protagonist is flagged -- i.e. in every
    sim path -- so the benches never see it."""
    pc = next((h for h in party if h.protagonist and not h.dead), None)
    if pc is None or pc.cha <= PARTY_CAPACITY_BASE_CHA:
        return 0
    frac = min(CHA_GOLD_BONUS_CAP,
               CHA_GOLD_BONUS_PER_POINT * (pc.cha - PARTY_CAPACITY_BASE_CHA))
    return round(gold * frac)


def award_quest(party: list[Entity], purse: Purse, gold: int, xp: int,
                log: list[str], name: str,
                banner: str = "QUEST COMPLETE") -> None:
    """Clearing a whole site pays its lump: gold to the purse and an XP lump
    to everyone still alive (`banner` reads SITE CLEARED for the non-final
    sites of a multi-site quest). Skill points are BANKED, not auto-spent --
    with two sinks now (combat training vs weapon proficiency) spending is a
    real player choice (session.py `train`); only the sim paths auto-train.
    A charismatic PC talks the gold up (cha_gold_bonus), and a paid-out job
    is the one thing that RAISES companion satisfaction on the road."""
    log.append("")
    log.append(f"  *** {banner}: {name}. Reward: {gold} gold. ***")
    bonus = cha_gold_bonus(party, gold)
    if bonus:
        pc = next(h for h in party if h.protagonist and not h.dead)
        gold += bonus
        log.append(f"    {pc.name} talks the pay up: +{bonus}g "
                   f"(CHA {pc.cha} -- {gold}g in all).")
    purse.gold += gold
    log.append(f"    The party purse holds {purse.gold} gold.")
    award_xp(party, xp, log, "quest")
    for h in party:
        if not h.dead:
            adjust_satisfaction(h, SAT_SITE_CLEAR, log, "a job paid out")


def buy_potion(h: Entity, purse: Purse, kind: str, log: list[str]) -> bool:
    """Buy one potion from the party purse. A between-adventures call the DM
    makes on the player's decision -- nothing in the engine buys automatically."""
    if kind not in POTION_KINDS:
        raise ValueError(f"unknown potion kind: {kind}")
    if kind not in STOCKED_POTION_KINDS:
        log.append(f"    No shop stocks a {kind} potion.")
        return False
    if purse.gold < POTION_PRICE:
        log.append(f"    Not enough gold for a {kind} potion "
                   f"({purse.gold}g / {POTION_PRICE}g).")
        return False
    purse.gold -= POTION_PRICE
    h.items[kind] = h.items.get(kind, 0) + 1
    log.append(f"    {h.name} buys a {kind} potion for {POTION_PRICE}g "
               f"({kind} x{h.items[kind]}; purse: {purse.gold}g).")
    return True


def equip_weapon(h: Entity, weapon: Weapon, log: list[str]) -> None:
    """Wield a weapon (found, bought, or DM-granted loot). There is no
    inventory -- the old weapon is set aside as narrative (heroic tone,
    no bookkeeping). A fresh weapon is whole (clears the broken flag).
    Proficiency is per weapon TYPE, so ranks with this type apply at once."""
    old = h.weapon
    h.weapon = weapon
    h.weapon_broken = False
    h.switched = False
    was = (f" (setting aside the {old.name})"
           if old is not None and old.name != weapon.name else "")
    rank = h.proficiency.get(weapon.name, 0)
    drilled = f" -- already drilled with it (prof {rank})" if rank else ""
    log.append(f"    {h.name} takes up the {weapon.name}{was}{drilled}.")
    if weapon.ammo in AMMO_CAPS and h.items.get(weapon.ammo, 0) <= 0:
        log.append(f"    (it shoots {weapon.ammo} -- `buy` some, or there "
                   f"is nothing to loose)")


def grant_starter_ammo(h: Entity, log: list[str]) -> None:
    """A bought or DM-granted ranged weapon comes with a starter load
    (nobody sells a bow without a quiver): tops the matching ammo count UP
    to STARTER_AMMO, never past, never down."""
    w = h.weapon
    if w is None or w.ammo not in STARTER_AMMO:
        return
    have = h.items.get(w.ammo, 0)
    want = STARTER_AMMO[w.ammo]
    if have < want:
        h.items[w.ammo] = want
        log.append(f"    (it comes with {want - have} {w.ammo} -- "
                   f"{want} carried)")


def buy_weapon(h: Entity, purse: Purse, name: str, log: list[str]) -> bool:
    """Buy a weapon from the party purse and wield it -- a between-adventures
    DM call, same shape as buy_potion. Only plain-tier weapons are ever for
    sale (masterwork/legendary are found or quested, never shopped)."""
    w = WEAPONS.get(name)
    if w is None:
        raise ValueError(f"unknown weapon: {name}")
    if w.tier != "plain":
        log.append(f"    No shop sells a {w.tier} weapon.")
        return False
    if purse.gold < w.value:
        log.append(f"    Not enough gold for a {name} "
                   f"({purse.gold}g / {w.value}g).")
        return False
    purse.gold -= w.value
    log.append(f"    {h.name} buys a {name} for {w.value}g "
               f"(purse: {purse.gold}g).")
    equip_weapon(h, w, log)
    grant_starter_ammo(h, log)
    return True


def buy_ammo(h: Entity, purse: Purse, kind: str, log: list[str]) -> bool:
    """Buy one LOT of ammo (AMMO_LOTS: arrows/bolts by the sheaf, shells
    and knives by the pair) from the party purse, up to the carry cap.
    Sling stones are never bought -- the ground is full of them."""
    if kind not in AMMO_LOTS:
        log.append(f"    No shop sells {kind!r}.")
        return False
    lot, price = AMMO_LOTS[kind]
    cap = AMMO_CAPS[kind]
    have = h.items.get(kind, 0)
    if have >= cap:
        log.append(f"    {h.name} already carries a full load of {kind} "
                   f"({have}/{cap}).")
        return False
    if purse.gold < price:
        log.append(f"    Not enough gold for {lot} {kind} "
                   f"({purse.gold}g / {price}g).")
        return False
    purse.gold -= price
    h.items[kind] = min(cap, have + lot)
    log.append(f"    {h.name} buys {h.items[kind] - have} {kind} for "
               f"{price}g ({h.items[kind]}/{cap} carried; "
               f"purse: {purse.gold}g).")
    return True


def use_heal(healer: Entity, target: Entity, rng: random.Random,
             log: list[str]) -> bool:
    """Spend Power on the Heal ability: mends a random 1-3 HP on self or an
    ally. Unlike Bulwark's mid-fight save, Heal has no in-fight role -- it's a
    between-fights, DM-called action (same shape as buy_potion), so it never
    fires automatically."""
    if healer.ability != "heal":
        log.append(f"    {healer.name} has no Heal ability.")
        return False
    if healer.cur_power < HEAL_COST:
        log.append(f"    {healer.name} doesn't have enough Power to Heal "
                   f"({healer.cur_power}/{HEAL_COST}).")
        return False
    if target.dead:
        log.append(f"    {target.name} is beyond Heal.")
        return False
    healer.cur_power -= HEAL_COST
    amount = rng.randint(*HEAL_RESTORE_RANGE)
    # The wooden staff is the healer's weapon: +1 HP per Heal through it.
    staff_note = ""
    if (healer.weapon is not None and not healer.weapon_broken
            and healer.weapon.heal_bonus):
        amount += healer.weapon.heal_bonus
        staff_note = f" ({healer.weapon.name} +{healer.weapon.heal_bonus})"
    before = target.hp
    target.hp = min(target.max_hp, target.hp + amount)
    if target.hp > 0:
        target.down = False
    log.append(f"    {healer.name} spends {HEAL_COST} Power to Heal "
               f"{target.name}{staff_note} (+{target.hp - before} HP -> "
               f"{target.hp}/{target.max_hp}) [{healer.cur_power} Power left]")
    return True


def use_potion(h: Entity, kind: str, log: list[str]) -> bool:
    """Consume one carried potion by player choice, between fights. A DM-called
    action (same shape as buy_potion / use_heal) -- nothing in the engine drinks
    automatically. Every potion takes effect instantly on drink (you're between
    fights; there's time to let it work). Returns True if a potion was spent.
      healing -> restore HP now
      stamina -> restore STA now
      power   -> restore Power now"""
    if kind not in POTION_KINDS:
        raise ValueError(f"unknown potion kind: {kind}")
    if h.items.get(kind, 0) <= 0:
        log.append(f"    {h.name} has no {kind} potion to use.")
        return False
    h.items[kind] -= 1
    if kind == "healing":
        before = h.hp
        h.hp = recover(max(h.hp, 0), HEALING_POTION_RESTORE, h.max_hp)
        if h.hp > 0:
            h.down = False
        log.append(f"    {h.name} drinks a healing potion "
                   f"(HP {before} -> {h.hp}/{h.max_hp}; {h.items['healing']} left)")
    elif kind == "stamina":
        before = h.cur_sta
        h.cur_sta = recover(h.cur_sta, STAMINA_DRAUGHT_RESTORE, h.sta)
        log.append(f"    {h.name} downs a stamina draught "
                   f"(STA {before} -> {h.cur_sta}; {h.items['stamina']} left)")
    else:  # power
        before = h.cur_power
        h.cur_power = recover(h.cur_power, POWER_POTION_RESTORE, h.power)
        log.append(f"    {h.name} drinks a power potion "
                   f"(Power {before} -> {h.cur_power}; {h.items['power']} left)")
    return True


def auto_use_potions_on_rest(survivors: list[Entity], log: list[str]) -> None:
    """The 'sensible party' rest-time policy for the sim / one-shot paths only
    (sites.run_site) -- NOT for real play, which leaves every
    potion to the DM via use_potion(). Drinks a healing potion when badly hurt,
    a stamina draught when winded, and a power potion when the save budget is
    nearly gone -- so tune.py / bench_training.py still model a party that uses
    its consumables."""
    for h in survivors:
        if h.hp <= h.max_hp // 2 and h.items.get("healing", 0) > 0:
            use_potion(h, "healing", log)
        if h.cur_sta <= WINDED_STA and h.items.get("stamina", 0) > 0:
            use_potion(h, "stamina", log)
        if h.cur_power <= SAVE_COST and h.items.get("power", 0) > 0:
            use_potion(h, "power", log)


def start_fight(h: Entity, log: list[str]) -> None:
    """Per-fight prep: bring a Down hero back to their feet (minimally). HP is NOT
    reset -- wounds carry across rooms; healing comes from potions, spells, and
    resting between adventures, never a free per-fight top-up."""
    if h.down or h.hp <= 0:
        h.hp = REVIVE_HP
        h.down = False
        log.append(f"    {h.name} is helped back to their feet ({REVIVE_HP} HP).")


def short_rest(survivors: list[Entity], clock: Clock, log: list[str]) -> bool:
    """A short rest (~an hour or two): a little STA, HP, and Power back. Costs
    one of the day's short-rest slots. Returns False (no effect) once the day's
    slots are spent -- there is no more mid-day recovery then; the party pushes
    on depleted or Claude calls long_rest() to make camp. Potions are NOT drunk
    here: that is a deliberate DM call (use_potion), never automatic."""
    if clock.short_rests_left <= 0:
        log.append("    (no short rest left today -- the party must push on "
                   "or make camp)")
        return False
    clock.short_rests_used += 1
    log.append(f"  The party takes a short rest "
               f"({clock.short_rests_left} left today).")
    for h in survivors:
        # STA is the per-day clock: only a slow catch-breath, never a full reset.
        h.cur_sta = recover(h.cur_sta, STA_RECOVERY_BETWEEN_ROOMS, h.sta)
        # HP carries across rooms too: only a minimal catch-breath, not a reset.
        h.hp = recover(h.hp, HP_RECOVERY_BETWEEN_ROOMS, h.max_hp)
        # Power trickles back with rest too (2026-07): the budget refills like
        # the condition does, slowly by day and fully overnight.
        h.cur_power = recover(h.cur_power, POWER_RECOVERY_BETWEEN_ROOMS, h.power)
    return True


def long_rest(party: list[Entity], clock: Clock, log: list[str],
              banner: str = "The party makes camp.") -> None:
    """Make camp for the night. A deliberate, Claude-invoked step -- never
    automatic. STA and Power recharge fully overnight; HP knits back at each
    character's weekly rate; Down heroes get back on their feet; the day
    advances and the short-rest slots refill. Only the truly Dead stay down.
    `banner` reflavors the night line (the tavern sleeps under a roof)."""
    clock.day += 1
    clock.short_rests_used = 0
    log.append(f"  --- {banner} Night passes; day {clock.day} dawns. ---")
    for h in party:
        if h.dead:
            continue
        h.cur_sta = h.sta                       # STA fully recharges overnight
        h.cur_power = h.power                   # so does the Power budget
        h.down = False
        before = h.hp
        h.hp = min(h.max_hp, max(h.hp, 0) + h.hp_regen_per_night)
        note = f"STA and Power full ({h.cur_sta}/{h.sta}, "
        note += f"{h.cur_power}/{h.power})"
        if h.hp > before:
            note += f", +{h.hp - before} HP -> {h.hp}/{h.max_hp}"
        elif h.hp < before:
            # The tavern's overcharge expiring: the night clamps the excess.
            note += f", the overcharge fades -> {h.hp}/{h.max_hp} HP"
        else:
            note += ", HP full"
        log.append(f"    {h.name}: {note}")
    # The traveling kit replenishes itself (2026-07-11, see KIT_*): herbs
    # brewed at the camp fire, a vial scrounged in town -- nobody shops for
    # the baseline potion. `buy` still stocks above the kit line.
    restocked = 0
    for h in party:
        if h.dead:
            continue
        for kind, floor_n in (("healing", KIT_HEALING),
                              ("stamina", KIT_STAMINA)):
            have = h.items.get(kind, 0)
            if have < floor_n:
                h.items[kind] = floor_n
                restocked += floor_n - have
    if restocked:
        log.append(f"    The kit is restocked overnight (+{restocked} "
                   f"potion(s) brewed or scrounged -- everyone carries at "
                   f"least {KIT_HEALING} healing, {KIT_STAMINA} stamina)")


def tavern_rest(party: list[Entity], clock: Clock, purse: Purse,
                log: list[str]) -> bool:
    """A night at the inn (session play gates it to settlements): a long rest
    plus a hot meal and a real bed, TAVERN_COST_PER_HERO gold per living
    member from the purse. The party wakes OVERCHARGED: current HP and STA
    gain TAVERN_OVERCHARGE of their maximum (min 1) ON TOP of the overnight
    recovery, and may sit above max ("13/12 HP"). The excess is a one-day
    edge: recovery never adds past max (see recover()), so it is spent-only,
    and whatever survives the day is clamped away by the next long rest.
    Returns False (nothing happens, no rest) when the purse can't pay --
    camping is always free."""
    boarders = [h for h in party if not h.dead]
    cost = TAVERN_COST_PER_HERO * len(boarders)
    if purse.gold < cost:
        log.append(f"    Not enough gold for beds ({purse.gold}g / {cost}g "
                   f"at {TAVERN_COST_PER_HERO}g a head) -- the party can "
                   f"still camp for free.")
        return False
    purse.gold -= cost
    log.append(f"  The party takes beds at the tavern ({cost}g -- purse: "
               f"{purse.gold}g).")
    long_rest(party, clock, log,
              banner="The party sleeps warm under a roof.")
    for h in boarders:
        hp_bonus = max(1, round(h.max_hp * TAVERN_OVERCHARGE))
        sta_bonus = max(1, round(h.sta * TAVERN_OVERCHARGE))
        h.hp += hp_bonus
        h.cur_sta += sta_bonus
        log.append(f"    {h.name} wakes overcharged: +{hp_bonus} HP -> "
                   f"{h.hp}/{h.max_hp}, +{sta_bonus} STA -> "
                   f"{h.cur_sta}/{h.sta} (a one-day edge -- it fades at the "
                   f"next night's rest)")
    for h in boarders:
        adjust_satisfaction(h, SAT_TAVERN, log, "a warm bed and a hot meal")
    return True


def party_wiped(party: list[Entity], log: list[str]) -> bool:
    """A total party knockout is a defeat. If no hero is left standing after a
    fight, there's no one to drag the fallen clear -- every Down hero is finished
    off (marked Dead). Returns True on a wipe (the run should stop). Kept here so
    every scenario shares one game-over rule."""
    if any(h.alive for h in party):
        return False
    for h in party:
        if not h.dead:
            h.dead = True
            h.down = False
    log.append("  *** The party is overwhelmed -- none left standing. "
               "The fallen do not rise. TOTAL DEFEAT. ***")
    return True


# The batch sims' pause policy. Crude thresholds on purpose -- the sims
# UNDERSTATE the player (see develop.md "Balance / tuning"): a real player
# reads the whole board at a pause; this reads one number per crossing.
SIM_MAX_ROOM_ATTEMPTS = 2   # a fled room gets ONE return trip in the sims,
                            # then the run is abandoned (a determined but
                            # finite party; real play has no such cap)


def sim_pause_policy(crossings: list[tuple[str, Entity]]
                     ) -> str | dict[Entity, str]:
    """Decide a paused fight for the batch sims: "retreat", or {hero: action}
    (empty dict = fight on). Per crossing:
      stamina -> drink a carried draught; else War-Breath if the Power is
                 there (a Bulwark hero keeps one save in reserve); else
                 Berserk on a still-healthy body; else vote retreat.
      wounds  -> drink a carried healing potion mid-fight (2026-07-11, the
                 pause's "heal" action); a deep cut with no potion votes
                 retreat; a shallow one with no potion fights on.
    Any retreat vote carries -- the party leaves together."""
    actions: dict[Entity, str] = {}
    for kind, hero in crossings:
        if kind == "stamina":
            if hero.items.get("stamina", 0) > 0:
                actions[hero] = "drink"
            elif hero.cur_power >= WAR_BREATH_POWER_COST + (
                    SAVE_COST if hero.ability == "bulwark" else 0):
                actions[hero] = "war-breath"
            elif hero.hp > BERSERK_HP_COST * 3:
                actions[hero] = "berserk"
            else:
                return "retreat"
        else:   # wounds
            if hero.items.get("healing", 0) > 0:
                actions[hero] = "heal"
            elif hero.hp * 3 <= hero.max_hp:
                return "retreat"
    return actions


def sim_fight(living: list[Entity], foes: list[Entity], rng: random.Random,
              log: list[str], reckless: bool = False,
              field: int = 0) -> str:
    """One encounter under the batch-sim pause policy (drink / convert /
    retreat -- sim_pause_policy). Returns "resolved" (the melee ended; read
    the outcome off the entities) or "fled" (a clean escape; foes survive).
    The site loop (sites.run_site) and session play share the
    same engine; only WHO answers the pause differs -- here a policy, there
    the player.

    reckless=True is the NO-RESOURCE baseline (tune.py's honesty check): the
    fight runs with no pauses at all -- never drinks, converts, or retreats.
    Its wipe rate is what "not using your resources" costs, which the retune
    wants to be most of a party's life expectancy."""
    if reckless:
        group_combat(living, foes, rng, log, field=field)
        return "resolved"
    fired: set[str] = set()
    actions: dict[Entity, str] | None = None
    first_round = 1
    while True:
        pause = group_combat(living, foes, rng, log, pause_triggers=True,
                             fired=fired, first_round=first_round,
                             actions=actions, field=field)
        actions = None
        if pause is None:
            return "resolved"
        first_round = pause.round + 1
        decision = sim_pause_policy(pause.crossings)
        if decision == "retreat":
            if attempt_retreat(living, foes, rng, log, field=field):
                return "fled"
            if not any(h.alive for h in living):
                return "resolved"   # cut down at the door
            continue                # run down: the fight resumes
        actions = decision or None


def outcome(party: list[Entity]) -> str:
    """How many were truly slain (Down does not count -- it recovers).
    Works for any party size 1-4; the classic duo keeps its "both"."""
    dead = sum(1 for h in party if h.dead)
    if dead == 0:
        return "none"
    if dead == len(party):
        return "both" if len(party) == 2 else "all"
    return "one" if dead == 1 else str(dead)


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    # The one-shot runner lives with the content now (sites.py); this stub
    # keeps `python rpg.py [--site ...] [--seed N]` working as documented.
    from sites import main as run_sites
    run_sites()


if __name__ == "__main__":
    main()
