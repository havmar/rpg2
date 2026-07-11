"""Combat Sim - the mechanics engine.

Implements the ruleset in rules.md (the source of truth for mechanics intent):
the group melee (group_combat), the pause/retreat interrupt layer, weapons and
breakage, the survival tracks (HP/STA/Power, rests, the clock), progression
(XP, training, proficiency), the economy (purse, potions, weapons), random
party generation, and the batch-sim policies (sim_fight, sim_pause_policy).

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
]}

CRUDE_WEAPONS = ("club", "dagger", "whip", "light hammer")
SOLDIER_WEAPONS = ("shortsword", "scimitar", "spear", "mace", "flail", "morningstar")
HEAVY_WEAPONS = ("longsword", "battleaxe", "warhammer", "halberd")
QUALITY_WEAPONS = ("rapier", "katana", "zweihander", "wooden staff")

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
# function Claude calls on purpose (see the module docstring / CLAUDE.md), never
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
# per fight (no pause spam; per hero, so one hero's crisis never consumes the
# other's warning). CROSSING-ONLY (2026-07): a trigger whose condition already
# holds when the fight starts is marked spent silently -- entering low was the
# player's informed choice at the door, so only an IN-FIGHT crossing
# interrupts (a wounded day no longer re-asks the same question every fight).
# At the pause the choices are: fight on (resume), a pause ACTION per hero --
# drink a stamina draught mid-fight, or one of the resource conversions below
# -- or retreat. Every pause action costs that round's attack and the hero
# defends at a penalty while occupied: vulnerable, not helpless. Mid-fight
# drinking un-Spends a fighter at 0 STA -- bought at a real price.
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
PAUSE_ACTIONS = ("drink", "berserk", "war-breath")

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
    dex: int
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
                            # -2 fleeing under a parting blow)
    misc_label: str = ""

    def breakdown(self, name: str) -> str:
        parts = [f"2d6={self.dice}", f"+{self.dex} DEX"]
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
    ability: str | None = None          # "bulwark" (mid-fight save) or "heal" (between-
                                         # fights HP restore, see use_heal); None = neither
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
        # you're swinging a stump, not the weapon you drilled with).
        if self.weapon is None or self.weapon_broken:
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

    def severity_mods(self) -> list[tuple[int, str]]:
        """The wielded weapon's severity terms as (value, label) pairs, kept
        separate so the log can show every source (weapon vs proficiency)."""
        if self.weapon is None:
            return []
        if self.weapon_broken:
            return [(BROKEN_SEVERITY, f"broken {self.weapon.name}")]
        mods = []
        if self.weapon.severity:
            mods.append((self.weapon.severity, self.weapon.name))
        if self.prof_rank:
            mods.append((self.prof_rank, "proficiency"))
        return mods

    def pressure(self, rng: random.Random, attacking: bool = False,
              wound_pen: int | None = None, misc: int = 0,
              misc_label: str = "") -> PressureRoll:
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
        if self.weapon is not None:
            if attacking:
                if self.weapon_broken:
                    weapon_mod = BROKEN_ATK_PRESSURE
                    weapon_label = f"broken {self.weapon.name}"
                else:
                    weapon_mod = self.weapon.atk_pressure
                    weapon_label = self.weapon.name
                    prof = self.prof_rank
            elif not self.weapon_broken and self.weapon.def_pressure:
                weapon_mod = self.weapon.def_pressure
                weapon_label = self.weapon.name
        # def_bonus is a body knob (the "armored" trait): defense only, like
        # the staff's parry but worn instead of wielded.
        armor = 0 if attacking else self.def_bonus
        total = (dice + self.dex + self.training + weapon_mod + prof + armor
                 + misc - pen - fatigue_pen)
        return PressureRoll(total=total, dice=dice, dex=self.dex,
                         training=self.training, wound_pen=pen,
                         fatigue_pen=fatigue_pen, fatigue_label=fatigue_label,
                         weapon_mod=weapon_mod, weapon_label=weapon_label,
                         prof=prof, armor=armor, misc=misc,
                         misc_label=misc_label)


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
            soften: bool = False) -> None:
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

    Every exchange logs two layers: an interpretive headline first (both log
    levels; the player version folds the HP loss in and drops the roll
    penalty), then the raw numbers (dice, each modifier and its source)
    indented beneath it -- full log only.
    """
    atk = (attacker.pressure(rng, attacking=True, wound_pen=atk_wound_pen)
           if atk_roll is None else atk_roll)
    dfn = defender.pressure(rng, misc=def_mod, misc_label=def_label)
    pressure_line = (f"        pressure: {atk.breakdown(attacker.name)} vs "
                  f"{dfn.breakdown(defender.name)}")

    if atk.total == dfn.total:
        # A tie: no one lands. High dice = furious contact, low = circling.
        if max(atk.dice, dfn.dice) >= TIE_HIGH_DICE:
            label = "Clash! Steel rings; neither yields"
            contact = True      # steel met steel -- durability is tested
        else:
            label = "Lull. They circle, probing for an opening"
            contact = False     # no contact, nothing to break
        log.append(f"    {attacker.name} and {defender.name} -- {label}.")
        _debug(log, pressure_line)
        if contact:
            _check_weapon_break(attacker, defender, rng, log)
        return

    if atk.total < dfn.total:
        log.append(f"    {attacker.name} attacks {defender.name} -- parried.")
        _debug(log, pressure_line)
        _check_weapon_break(attacker, defender, rng, log)
        return

    margin = atk.total - dfn.total
    sev_mods = attacker.severity_mods()
    severity = (margin + attacker.str_ + sum(v for v, _ in sev_mods)
                - defender.str_)
    raw_tier, dmg = wound_tier(severity)
    sev_line = f"        severity: {severity} = margin {margin} +{attacker.str_} STR"
    for v, label in sev_mods:
        sev_line += f" {v:+d} {label}"
    sev_line += f" -{defender.str_} soak -> {raw_tier}"

    if dmg == 0:
        # Anti-soak floors -- chip damage soak can't zero, feeding the spiral.
        if (attacker.weapon is not None and not attacker.weapon_broken
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
            log.append(f"    {attacker.name} {margin_verb(margin)} "
                       f"{defender.name}, but the blow glances off -- deflected.")
            _debug(log, pressure_line)
            _debug(log, sev_line)
            return

    if soften and dmg > 0:
        # The parting blow at a fleeing back lands one tier lighter (see the
        # docstring) -- softened BEFORE the save, so its raw tier can never
        # be crippling and a retreat is never an outright death at the door.
        raw_tier, dmg = reduce_tier(raw_tier)
        sev_line += f" -> a hurried blow at a fleeing back: {raw_tier}"
        if dmg == 0:
            log.append(f"    {attacker.name} {margin_verb(margin)} "
                       f"{defender.name}, but the hurried blow at a fleeing "
                       f"back glances off -- deflected.")
            _debug(log, pressure_line)
            _debug(log, sev_line)
            return

    tier = raw_tier
    saved = _try_save(defender, tier, dmg)
    if saved:
        tier, dmg = reduce_tier(tier)
        sev_line += f", Bulwark save -> {tier} (-{dmg} HP)"
    else:
        sev_line += f" (-{dmg} HP)"

    defender.hp = max(0, defender.hp - dmg)
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
              f"    {attacker.name} {margin_verb(margin)} {defender.name}"
              f" -- {TIER_PHRASE[raw_tier]}... {defender.name}'s Bulwark "
              f"flares! Reduced to {tier}. [{state}; "
              f"{defender.cur_power} Power left]",
              f"    {attacker.name} {margin_verb(margin)} {defender.name}"
              f" -- {TIER_PHRASE[raw_tier]}... {defender.name}'s Bulwark "
              f"flares! Reduced to {tier} (-{dmg} HP). [{player_state}; "
              f"{defender.cur_power} Power left]")
    else:
        _play(log,
              f"    {attacker.name} {margin_verb(margin)} {defender.name}"
              f" -- {TIER_PHRASE[tier]}! [{state}]",
              f"    {attacker.name} {margin_verb(margin)} {defender.name}"
              f" -- {TIER_PHRASE[tier]} (-{dmg} HP)! [{player_state}]")
    _debug(log, pressure_line)
    _debug(log, sev_line)

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
                 engaged: dict[Entity, int] | None = None) -> Entity | None:
    """Pick a living target. With `engaged` (this round's single-attack counts
    per defender), only targets with press room (fewer than their crowd_cap
    attackers so far) are eligible -- returns None when every living target is
    already crowded, and the attacker circles the round away instead."""
    living = [e for e in targets if e.alive]
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


def _do_pause_action(h: Entity, action: str, log: list[str]) -> bool:
    """Execute one pause-menu action at the top of the resumed round: drink a
    stamina draught, or a resource conversion (Berserk / War-Breath). Returns
    True if it took effect -- the hero is then BUSY this round: no attack, and
    -PAUSE_ACTION_DEF_PENALTY on defense (vulnerable, not helpless). A failed
    action (nothing to drink, not enough Power) logs and the hero just fights."""
    if not h.alive:
        return False
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
                 actions: dict[Entity, str] | None = None) -> Pause | None:
    """Resolve a melee in place. Survivors keep their HP/STA/Power as-is.

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
    ({hero: "drink" | "berserk" | "war-breath"}, executed at the top of the
    resumed round: the hero skips that attack and defends at
    -PAUSE_ACTION_DEF_PENALTY). Returns None when the melee actually ended.
    """
    party_set = set(party)
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
    busy_label = {"drink": "drinking", "berserk": "berserk",
                  "war-breath": "war-breath"}
    busy: dict[Entity, str] = {}
    rnd = first_round - 1
    while any(e.alive for e in party) and any(e.alive for e in foes):
        rnd += 1
        if rnd > max_rounds:
            log.append("    (the fight grinds to a standstill)")
            break
        log.append(f"  Round {rnd}:")
        if rnd == 1:
            _first_blood(party, foes, rng, log)
        if actions and rnd == first_round:
            # The pause actions happen now, in the teeth of the melee.
            for h, act in actions.items():
                if _do_pause_action(h, act, log):
                    busy[h] = act
            # A drink can un-Spend a fighter at 0: drop them from the
            # already-logged set so running dry AGAIN earns a fresh !! line.
            spent_logged = {e for e in spent_logged if e.spent}

        # Round-start snapshot: everyone alive NOW acts this round, even if
        # felled before their turn comes -- the dying swing (see docstring).
        actors = [e for e in party + foes if e.alive]
        start_pens = {e: e.wound_penalty for e in actors}
        engaged: dict[Entity, int] = {}     # the press: single-attack counts
                                            # per defender this round
        for attacker in actors:
            if attacker in busy:
                continue    # occupied with their draught/conversion this round
            dying = not attacker.alive      # felled earlier this round
            targets = foes if attacker in party_set else party
            living_targets = [t for t in targets if t.alive]
            if not living_targets:
                continue        # nobody left on the other side for THIS
                                # attacker; a dying foe later in the order
                                # may still owe the party its last blow

            # A multi-target blow (the giant's sweep, the dragon's breath):
            # one attacker roll, resolved against each caught defender's own
            # defense. Sweeps don't queue for press room -- a wall of fire
            # doesn't care how crowded the line is -- and a fueled one
            # (sweep_cost_power) needs the Power, else it falls back to
            # single attacks.
            sweeping = (attacker.sweep > 1 and len(living_targets) > 1
                        and (attacker.sweep_cost_power == 0
                             or attacker.cur_power
                             >= attacker.sweep_cost_power))
            if sweeping:
                victims = rng.sample(living_targets,
                                     min(attacker.sweep, len(living_targets)))
            else:
                defender = _pick_target(targets, rng,
                                        focus=attacker in party_set,
                                        engaged=engaged)
                if defender is None:
                    # Crowded out of the press: circle the round away instead
                    # (free, like defending -- no swing, no STA).
                    log.append(f"    {attacker.name} circles, crowded out "
                               f"of the press.")
                    continue
                engaged[defender] = engaged.get(defender, 0) + 1
                victims = [defender]

            if not attacker.tireless and not dying:
                # The dying swing is free -- desperation costs nothing.
                was_winded = attacker.winded
                # The weapon sets the swing price (zweihander 2, most else 1).
                attacker.cur_sta = max(0, attacker.cur_sta - attacker.swing_cost)
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
            if sweeping:
                if attacker.sweep_cost_power:
                    attacker.cur_power -= attacker.sweep_cost_power
                label = attacker.sweep_label or "a great sweeping blow"
                names = ", ".join(v.name for v in victims)
                fuel = (f" [{attacker.sweep_cost_power} Power spent, "
                        f"{attacker.cur_power} left]"
                        if attacker.sweep_cost_power else "")
                _play(log,
                      f"    {attacker.name} unleashes {label} -- "
                      f"{names} are caught in it!{fuel}",
                      f"    {attacker.name} unleashes {label} -- "
                      f"{names} are caught in it!")
                atk_roll = attacker.pressure(
                    rng, attacking=True,
                    wound_pen=start_pens[attacker] if dying else None)
            for defender in victims:
                was_alive = defender.alive
                _attack(attacker, defender, rng, log,
                        atk_wound_pen=start_pens[attacker] if dying else None,
                        def_mod=(-PAUSE_ACTION_DEF_PENALTY
                                 if defender in busy else 0),
                        def_label=busy_label.get(busy.get(defender, ""), ""),
                        atk_roll=atk_roll)
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
        _debug(log, _stamina_line(party, foes))

        if pause_triggers:
            crossings = _check_pause_triggers(party, foes, fired)
            if crossings:
                for kind, h in crossings:
                    if kind == "stamina":
                        log.append(f"    == {h.name} is nearly out of breath "
                                   f"(STA {h.cur_sta}/{h.sta}) -- "
                                   f"the fight hangs for a heartbeat. ==")
                    else:
                        log.append(f"    == {h.name} is badly cut up "
                                   f"(HP {h.hp}/{h.max_hp}) -- "
                                   f"the fight hangs for a heartbeat. ==")
                return Pause(round=rnd, crossings=crossings)

    # The dust settles: fate collects first, then whoever is still standing
    # catches their breath.
    _settle_fate_debt(party, foes, rng, log)
    survivors = [h for h in party if h.alive]
    if survivors:
        _catch_breath(survivors, log)
    return None


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
    full). A side entirely out of breath falls back to a plain average."""
    total_weight = sum(max(0, e.cur_sta) for e in group)
    if total_weight == 0:
        return sum(e.dex for e in group) / len(group)
    return sum(e.dex * max(0, e.cur_sta) for e in group) / total_weight


def attempt_retreat(party: list[Entity], foes: list[Entity],
                    rng: random.Random, log: list[str]) -> bool:
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
        # fleeing back can maim, never land the crippling tier.
        _attack(f, h, rng, log, def_mod=-PAUSE_ACTION_DEF_PENALTY,
                def_label="fleeing", soften=True)
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
        _catch_breath(runners, log)
        return True
    log.append("    *** RUN DOWN -- the pursuers catch them, and the fight "
               "resumes with their backs to it. ***")
    return False


def refresh_foes_after_retreat(foes: list[Entity],
                               days_passed: int) -> list[Entity]:
    """The room the party fled from, readied for a return trip (encounter
    persistence). The dead stay dead. Foe STA refills the moment the party
    leaves (they rest too). LIVING foes heal their wounds once a day has
    passed; the undead stay hacked -- dead bone doesn't knit, which is exactly
    the asymmetry that rewards a return trip to the barrow."""
    survivors = [f for f in foes if not f.dead]
    for f in survivors:
        f.cur_sta = f.sta
        if f.regen or (days_passed > 0 and not f.undead):
            # A fled regenerator is a healed one, same day or not -- the
            # camp-and-return loop does not work on a troll.
            f.hp = f.max_hp
            f.down = False
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
    """Fully random generation: DEX/STR/CHA 3-6, STA 5-8, HP 8-12, Power 3-6,
    a random ability (heal / bulwark / first_blood -- mend, mitigate, or open
    aggressively), two random potions, and a starting weapon (the common
    table: 50% crude / 45% soldier's arms / 5% heavy; healers often carry the
    wooden staff). `floors`/`ceilings` shift the roll ranges per key ("dex",
    "str", "cha", "hp") -- the racial-modifier hook (people.py: an orc's STR
    rolls 4-6; the "short" trait caps STR at 5)."""
    floors = floors or {}
    ceilings = ceilings or {}

    def roll(key: str, base: tuple[int, int]) -> int:
        return rng.randint(*_adjusted_range(base, floors.get(key, 0),
                                            ceilings.get(key, 0)))

    ability = rng.choice(["heal", "bulwark", "first_blood"])
    if ability == "heal" and rng.random() < HEALER_STAFF_CHANCE:
        weapon = WEAPONS["wooden staff"]    # the caster-bridge weapon at home
                                            # in a healer's hands (+1 to Heal)
    else:
        weapon = random_common_weapon(rng)
    return Entity(
        name=name,
        dex=roll("dex", HERO_STAT_RANGE),
        str_=roll("str", HERO_STAT_RANGE),
        sta=rng.randint(*HERO_STA_RANGE),
        max_hp=roll("hp", HERO_HP_RANGE),
        power=rng.randint(*HERO_POWER_RANGE),
        cha=roll("cha", HERO_CHA_RANGE),
        ability=ability,
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
    line = (f"{e.name} (L{e.level}, training {e.training}): "
            f"DEX {e.dex}  STR {e.str_}  STA {e.cur_sta}/{e.sta}  "
            f"HP {e.hp}/{e.max_hp}  Power {e.cur_power}/{e.power}  {cha}"
            f"({e.ability or 'no save'}; {weapon_tag(e)}; {kit})")
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
        if (h.ability == "heal" and h.weapon is not None
                and h.weapon.name == "wooden staff"):
            pass                                    # the staff IS quality
        elif h.str_ > h.dex:
            h.weapon = WEAPONS["zweihander"]
        elif h.dex > h.str_:
            h.weapon = WEAPONS["rapier"]
        else:
            h.weapon = WEAPONS["katana"]
    if h.weapon is not None:
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
    was = (f" (setting aside the {old.name})"
           if old is not None and old.name != weapon.name else "")
    rank = h.proficiency.get(weapon.name, 0)
    drilled = f" -- already drilled with it (prof {rank})" if rank else ""
    log.append(f"    {h.name} takes up the {weapon.name}{was}{drilled}.")


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
# UNDERSTATE the player (see CLAUDE.md "Balance / tuning"): a real player
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
      wounds  -> fight on while a healing potion is carried for afterward or
                 the wound is shallow; a deep cut with no buffer votes retreat.
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
            if (hero.items.get("healing", 0) == 0
                    and hero.hp * 3 <= hero.max_hp):
                return "retreat"
    return actions


def sim_fight(living: list[Entity], foes: list[Entity], rng: random.Random,
              log: list[str], reckless: bool = False) -> str:
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
        group_combat(living, foes, rng, log)
        return "resolved"
    fired: set[str] = set()
    actions: dict[Entity, str] | None = None
    first_round = 1
    while True:
        pause = group_combat(living, foes, rng, log, pause_triggers=True,
                             fired=fired, first_round=first_round,
                             actions=actions)
        actions = None
        if pause is None:
            return "resolved"
        first_round = pause.round + 1
        decision = sim_pause_policy(pause.crossings)
        if decision == "retreat":
            if attempt_retreat(living, foes, rng, log):
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
