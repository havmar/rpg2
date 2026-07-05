"""Combat Sim - combat engine, random party, and a skeleton dungeon.

Implements the ruleset in rules.md (core + the Survival & Resources add-on +
the first slice of Progression). A fight takes no input once it starts; it
produces an outcome and a narrative log. Generalized from a 1v1 exchange to a
group melee so a party can be swarmed (numbers are the skeletons' whole threat).

One exception to "no input once it starts": the PAUSE (the interrupt
primitive). With pause_triggers on, group_combat stops at the end of a round
in which a hero crossed STA <= 2 or half HP (each trigger once per fight) and
returns a Pause; the caller -- the DM in session play, sim_pause_policy in the
batch sims -- decides: fight on, a pause action per hero (drink a stamina
draught mid-fight, Berserk HP->STA, War-Breath Power->STA; each costs that
round's attack and defends at -2), or attempt_retreat (parting blows from
every foe fit to swing, then ONE opposed group chase roll -- the barrow's
undead never pursue past the door). A fled room's survivors persist
(refresh_foes_after_retreat): foe STA refills, the living heal over a day,
dead bone stays hacked.

Survival layer: HP carries across the whole run (only a minimal catch-breath
between rooms, never a per-fight reset); 0 HP is Down (out of this fight, stands
back up minimally next room), not Dead; Bulwark buys off killing/grievous blows
in the moment; First Blood opens the fight with a guaranteed graze on the
focused foe (the aggressive third ability -- its value is the death spiral, not
the point of damage); Heal instead mends HP on self or an ally between fights
(all cost Power); STA is the second death-track -- attacks spend it (defense is
free), and an entity that hits 0 STA is SPENT: still swinging, but at a huge
penalty to every roll, with no in-fight recovery. Running dry near a fresh
enemy is how you die (two spent sides cancel out and brawl to a real finish,
so fights resolve). STA only sawtooths back up between fights
(+1 after a fight, +3 per short rest, full overnight) across the run;
healing potions restore HP instantly, drunk between fights. A character only
truly dies when a killing blow lands and the saves have run dry.

The combat log is two-layered (see rules.md "Reading the combat log"): every
exchange gets an interpretive headline (Clash / Lull / edges past /
outmaneuvers / overwhelms ...) with the raw numbers -- dice, every modifier and
its source -- indented beneath it, plus a per-round stamina readout.

Progression & economy: heroes earn XP per encounter won and a lump for clearing
a whole site (the quest); levels grant skill points spent on combat training
(a flat tempo bonus, the veteran-vs-novice axis) or per-weapon proficiency
(+1 attack tempo and +1 severity with that weapon per rank). Gold accrues in a
shared party purse from quest rewards and occasional encounter drops; potions
are bought with gold (buy_potion is a between-adventures call the DM makes),
never auto-refilled. Heroes start with just two random potions. Potions are also
*used* by deliberate DM call (use_potion), between fights -- never automatically;
the one-shot/sim paths model a sensible party via auto_use_potions_*.

Weapons (Phase 4 first slice): every fighter wields one weapon -- an offense
package (attack tempo mod, severity mod, STA per swing) plus flavor (tags,
bulk, value). Commons (crude / soldier's arms / heavy arms) are the mook and
starter table; the quality four (rapier, katana, zweihander, wooden staff)
each suit a build. Weapon-on-weapon contact (a parry or a Clash) can SHATTER
the lower-durability weapon -- rusted mook steel snapping on a hero's quality
blade is the intended, narratable asymmetry.

Run:  python rpg.py            -> generate a party, run the dungeon, print log
      python rpg.py --seed 7   -> reproducible run
"""

from __future__ import annotations

import argparse
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
# and defense alike, with no in-fight recovery. Against fresh enemies that is a
# death sentence (can't land, gets carved, wounds spiral on top); two spent
# sides cancel each other's penalties and brawl it out to a real finish, so
# fights RESOLVE rather than stall. HP is how much you can bleed; STA is how
# long you can fight WELL; whichever empties first in reach of a foe kills you.
# Recovery only happens BETWEEN fights, as a sawtooth that trends down across
# the day: +1 when a fight ends, +3 on a short rest, full only on a long rest
# (overnight). Tireless entities (undead) never spend STA and are never
# Winded/Spent.
STA_ATTACK_COST = 1         # STA per swing (the pool is a swing budget now;
                            # halved from 2 when running dry became lethal, so
                            # a hero gets ~5-8 full-strength swings, not 2-3)
STA_RECOVERY_AFTER_FIGHT = 1  # survivors catch their breath when a fight ends

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
REVIVE_HP = 1                    # HP a Down hero stands back up with (minimal)

# --- Progression (XP, levels, combat training) ------------------------------ #
# Level L -> L+1 costs XP_LEVEL_STEP * L. A starter-site clear (3 encounters +
# quest at the bandit hideout) is exactly one level-1 level-up; the next level
# takes two clears (or one run at the 3x-paying barrow).
XP_LEVEL_STEP = 100
SKILL_POINTS_PER_LEVEL = 1
TRAINING_MAX = 5        # combat training rank cap; each rank = +1 to tempo rolls
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

# Site rewards. The bandit hideout (scratch_bandits.py) is the STARTER site
# and pays the base rate -- a full clear (3 encounters + quest) is exactly the
# level-1 -> 2 XP cost, so the first clear is a level-up. The skeleton barrow
# is the TOUGH site (tireless undead in numbers) and pays 3x: farm the bandits
# for training first, then take the barrow for real wages.
ENCOUNTER_XP = 15       # base per-encounter award (starter-site scale)
QUEST_XP = 55
QUEST_GOLD = 15
BARROW_REWARD_MULT = 3  # the barrow is the tough site
BARROW_ENCOUNTER_XP = ENCOUNTER_XP * BARROW_REWARD_MULT
BARROW_QUEST_XP = QUEST_XP * BARROW_REWARD_MULT
BARROW_QUEST_GOLD = QUEST_GOLD * BARROW_REWARD_MULT

# --- Weapons (Phase 4 first slice) ------------------------------------------ #
# A weapon is an OFFENSE package: it modifies the attack tempo roll, the
# severity of hits that land, and the STA cost per swing. Defense stays the
# body's job (DEX + training) except one deliberate knob (def_tempo: the
# staff's parry, the zweihander's unwieldiness). The design constraint: tempo
# already double-dips (margin feeds severity), so flat attack tempo is the
# rapier's axis and flat severity the zweihander's. NOTE on the sta_cost
# knob: a 2-STA heavy swing was the planned burst mechanic, but the sims
# rejected it -- with Spent lethal, halving the swing budget loses more than
# any severity buys back (see bench_weapons.py / rules.md). It stays in the
# schema at 1 for everything living, for a future with deeper STA pools.
PROFICIENCY_MAX = 3     # per-weapon-type proficiency cap (rank n costs n skill
                        # points): +1 attack tempo AND +1 severity with that
                        # weapon per rank -- narrower than combat training
                        # (offense only, one weapon), so stronger per rank
BROKEN_ATK_TEMPO = -2   # fighting with the stump of a shattered weapon
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
    (heroic tone, no encumbrance -- see plan.md; if carrying ever matters it
    becomes STR's secondary role). `tags` drive generation flavor."""
    name: str
    atk_tempo: int          # attack tempo roll modifier (attack only, never defense)
    severity: int           # flat severity modifier on hits that land
    sta_cost: int           # STA per swing (the burst/sustain knob)
    durability: int         # 1 crude .. 6 legendary; the lower may shatter on contact
    quality: bool = False
    tier: str = "plain"     # plain | masterwork | legendary (plain is unlabeled in play)
    def_tempo: int = 0      # defense tempo modifier (the staff's parry niche;
                            # negative for the zweihander -- no parrying a girder)
    graze_floor: bool = False   # the rapier: a landed hit is never fully
                                # deflected -- the point finds a seam (min. a
                                # graze), so soak can't zero the chip damage
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
    Weapon("zweihander", 1, 3, 1, durability=4, quality=True, def_tempo=-1,
           bulk=4, value=60,
           description="Two-handed war steel: every hit lands a tier harder "
                       "and mooks die in one blow, but there is no parrying "
                       "with a girder (-1 on defense). Wants STR and soak "
                       "behind it; the crowd-breaker."),
    Weapon("wooden staff", 0, -1, 1, durability=3, quality=True, def_tempo=1,
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
# automatic. A long rest recharges STA fully and knits HP back at a per-character
# weekly rate (~max_hp / 7 per night -> roughly a week to fully heal).
SHORT_RESTS_PER_DAY = 2          # short-rest slots available each day

# --- The mid-fight pause (the interrupt primitive) --------------------------- #
# group_combat can PAUSE at a trigger and resume: the "do I fight on?" decision
# surfaced BEFORE Spent, where play never had it. Triggers watch the party side
# only, at the end of a round, and each kind fires at most once per fight (no
# pause spam). At the pause the choices are: fight on (resume), a pause ACTION
# per hero -- drink a stamina draught mid-fight, or one of the resource
# conversions below -- or retreat. Every pause action costs that round's
# attack and the hero defends at a penalty while occupied: vulnerable, not
# helpless. Mid-fight drinking un-Spends at 0 STA -- the one exception to
# "no in-fight STA recovery", bought at a real price.
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
# high-STR frame is unwoundable by weak foes until fatigue collapses its tempo
# -- the party literally could not be injured before its stamina broke, which
# made HP dead weight (design note, 2026-07). Soak still gates the REAL wound
# tiers; this only stops chip damage from being zeroed on a clean win. The
# rapier's own graze_floor is stricter still (any landed hit).
GRAZE_FLOOR_MARGIN = 3

# Wound tiers as an ordered ladder, so a save can step a blow down one notch.
TIER_ORDER = ["deflected", "graze", "wound", "grievous", "killing blow"]
TIER_HP = {"deflected": 0, "graze": 1, "wound": 2, "grievous": 4, "killing blow": 6}

# --- Log vocabulary (the interpretive layer) -------------------------------- #
# Every exchange logs two layers: a catchy headline (what a watcher would say)
# and the raw numbers beneath it (every die, modifier, and source). See
# rules.md "Reading the combat log".
TIER_PHRASE = {"graze": "a graze", "wound": "a solid wound",
               "grievous": "a grievous injury", "killing blow": "a killing blow"}

# Tie on the tempo roll: high dice = furious contact, low dice = cagey circling.
TIE_HIGH_DICE = 8       # either side's raw 2d6 at/above this -> "Clash", else "Lull"


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
    return ("killing blow", TIER_HP["killing blow"])


def reduce_tier(tier: str) -> tuple[str, int]:
    """Step a wound down one tier (a Heal/Bulwark save). Floors at deflected."""
    i = TIER_ORDER.index(tier)
    new = TIER_ORDER[max(0, i - 1)]
    return new, TIER_HP[new]


@dataclass
class TempoRoll:
    """One tempo roll with its full breakdown, so the log can expose every
    modifier and its source (the mechanics layer of the two-layer log)."""
    total: int
    dice: int           # the raw 2d6 sum
    dex: int
    training: int
    wound_pen: int      # HP lost so far (the death spiral)
    fatigue_pen: int    # SPENT_PENALTY at 0 STA, else WINDED_PENALTY if
                        # Winded, else 0 (the two never stack)
    fatigue_label: str  # "spent" / "winded" / ""
    weapon_mod: int = 0     # the weapon's tempo term (attack bonus, the staff's
                            # parry bonus on defense, or the broken-weapon malus)
    weapon_label: str = ""  # e.g. "rapier" / "broken club"
    prof: int = 0           # proficiency rank with the wielded weapon (attack only)
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
    name: str
    dex: int
    str_: int
    sta: int
    max_hp: int
    power: int = 0
    ability: str | None = None          # "bulwark" (mid-fight save) or "heal" (between-
                                         # fights HP restore, see use_heal); None = neither
    sta_cost: int = STA_ATTACK_COST     # STA spent per attack (defense is free);
                                         # Phase 4 hangs weapon weight on this knob
    undead: bool = False                # no pain: wound roll penalty halved (see
                                         # wound_penalty)
    tireless: bool = False              # never spends STA, never Winded/Spent
                                         # (the undead don't tire; you do)
    pursues: bool = True                # gives chase when the party retreats;
                                         # False for the barrow's undead (bound
                                         # to the grave -- they swing at the
                                         # door but never follow past it)
    hp: int = field(default=0)
    cur_sta: int = field(default=0)
    cur_power: int = field(default=0)
    down: bool = field(default=False)   # at 0 HP, out of this fight (recoverable)
    dead: bool = field(default=False)   # truly slain (unsaved killing blow)
    items: dict[str, int] = field(default_factory=dict)
    hp_regen_per_night: int = field(default=0)  # HP knit back per long rest (derived)
    # Progression. Training is the veteran-vs-novice axis: a flat tempo bonus,
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
        # -SPENT_PENALTY to all rolls, and there is NO in-fight recovery --
        # spent lasts until the fight ends. (Derived from cur_sta, so a
        # fighter entering a fight at 0 is spent from round 1: you don't
        # start a fight with nothing left.)
        return not self.tireless and self.cur_sta <= 0

    @property
    def winded(self) -> bool:
        return (not self.tireless and not self.spent
                and self.cur_sta <= WINDED_STA)

    @property
    def wound_penalty(self) -> int:
        # The death spiral. Undead feel no pain: it bites at half strength
        # (integer halves -- a graze costs them nothing).
        return self.hp_lost // 2 if self.undead else self.hp_lost

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

    def tempo(self, rng: random.Random, attacking: bool = False,
              wound_pen: int | None = None, misc: int = 0,
              misc_label: str = "") -> TempoRoll:
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
        # The weapon is an offense package: its tempo bonus (and proficiency)
        # apply to the ATTACK roll only. Defense is the body -- DEX and
        # training -- except the staff's deliberate parry knob (def_tempo).
        # A broken weapon drags the attack down instead.
        weapon_mod, weapon_label, prof = 0, "", 0
        if self.weapon is not None:
            if attacking:
                if self.weapon_broken:
                    weapon_mod = BROKEN_ATK_TEMPO
                    weapon_label = f"broken {self.weapon.name}"
                else:
                    weapon_mod = self.weapon.atk_tempo
                    weapon_label = self.weapon.name
                    prof = self.prof_rank
            elif not self.weapon_broken and self.weapon.def_tempo:
                weapon_mod = self.weapon.def_tempo
                weapon_label = self.weapon.name
        total = (dice + self.dex + self.training + weapon_mod + prof + misc
                 - pen - fatigue_pen)
        return TempoRoll(total=total, dice=dice, dex=self.dex,
                         training=self.training, wound_pen=pen,
                         fatigue_pen=fatigue_pen, fatigue_label=fatigue_label,
                         weapon_mod=weapon_mod, weapon_label=weapon_label,
                         prof=prof, misc=misc, misc_label=misc_label)


# --------------------------------------------------------------------------- #
# Combat: a group melee
# --------------------------------------------------------------------------- #

def _try_save(defender: Entity, tier: str, dmg: int) -> bool:
    """Decide whether the defender spends Power to step an incoming blow down.

    Bulwark only -- Heal has no in-fight role; it mends HP between fights
    instead (see use_heal).

    Policy (conservative, death-first): always buy off a *killing* blow if Power
    allows; buy off a *grievous* that would put us Down only when a reserve is
    left for a later death-save. Mutates Power. Returns True if a save fired.
    """
    if defender.ability != "bulwark" or defender.cur_power < SAVE_COST:
        return False
    if tier not in ("grievous", "killing blow"):
        return False
    lethal = tier == "killing blow"
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
    loser, stronger = (a, wb) if wa.durability < wb.durability else (b, wa)
    other = b if loser is a else a
    gap = abs(wa.durability - wb.durability)
    if rng.random() >= BREAK_CHANCE_PER_GAP_SQ * gap * gap:
        return
    loser.weapon_broken = True
    log.append(f"    *** CRACK -- {loser.name}'s {loser.weapon.name} shatters "
               f"on {other.name}'s {stronger.name}! They fight on with what's "
               f"left ({BROKEN_ATK_TEMPO} attack tempo, "
               f"{BROKEN_SEVERITY} severity). ***")


def _attack(attacker: Entity, defender: Entity, rng: random.Random,
            log: list[str], atk_wound_pen: int | None = None,
            def_mod: int = 0, def_label: str = "") -> None:
    """One opposed exchange. Higher roll lands; severity sets the wound.

    The *raw* result is computed first (it may be a killing blow); a Power save
    can then step it down one tier. The log states the blow that would have
    landed. Death only happens when a raw killing blow is not saved.

    `atk_wound_pen` overrides the attacker's wound penalty (the dying swing --
    see group_combat's round-start snapshot). `def_mod`/`def_label` is a
    circumstance penalty on the defense roll (a hero drinking at the pause, or
    fleeing under a parting blow, defends at -PAUSE_ACTION_DEF_PENALTY).

    Every exchange logs two layers: an interpretive headline first, then the
    raw numbers (dice, each modifier and its source) indented beneath it.
    """
    atk = attacker.tempo(rng, attacking=True, wound_pen=atk_wound_pen)
    dfn = defender.tempo(rng, misc=def_mod, misc_label=def_label)
    tempo_line = (f"        tempo: {atk.breakdown(attacker.name)} vs "
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
        log.append(tempo_line)
        if contact:
            _check_weapon_break(attacker, defender, rng, log)
        return

    if atk.total < dfn.total:
        log.append(f"    {attacker.name} attacks {defender.name} -- parried.")
        log.append(tempo_line)
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
            log.append(tempo_line)
            log.append(sev_line)
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

    if saved:
        log.append(f"    {attacker.name} {margin_verb(margin)} {defender.name}"
                   f" -- {TIER_PHRASE[raw_tier]}... {defender.name}'s Bulwark "
                   f"flares! Reduced to {tier}. [{state}; "
                   f"{defender.cur_power} Power left]")
    else:
        log.append(f"    {attacker.name} {margin_verb(margin)} {defender.name}"
                   f" -- {TIER_PHRASE[tier]}! [{state}]")
    log.append(tempo_line)
    log.append(sev_line)

    if raw_tier == "killing blow" and not saved:
        defender.dead = True
    elif defender.hp <= 0:
        defender.down = True


def _pick_target(targets: list[Entity], rng: random.Random,
                 focus: bool) -> Entity:
    living = [e for e in targets if e.alive]
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
            log.append(f"    {hero.name} strikes before the lines meet -- "
                       f"First Blood! {target.name} is grazed "
                       f"(-{FIRST_BLOOD_HP} HP -> {target.hp}/{target.max_hp},"
                       f" -{target.wound_penalty} to rolls) "
                       f"[{FIRST_BLOOD_COST} Power spent, "
                       f"{hero.cur_power} left]")
            if not target.alive:
                target.down = True
                log.append(f"    *** {target.name} falls. ***")


def _stamina_line(party: list[Entity], foes: list[Entity]) -> str:
    """One compact stamina readout per round (attacks spend the clock -- the
    log shows it ticking every round). A * marks the Winded, !! the Spent;
    tireless entities are summarized (their clock never moves)."""
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
                          fired: set[str]) -> list[tuple[str, Entity]]:
    """The pause triggers, checked at the end of a round: a hero at STA <=
    PAUSE_STA_TRIGGER, or at HP <= half. Party side only (the pause is the
    player's), each kind at most once per fight (`fired` is mutated), and only
    while both sides still stand -- a decided fight has nothing to decide."""
    if not (any(e.alive for e in party) and any(e.alive for e in foes)):
        return []
    crossings = []
    if "stamina" not in fired:
        for h in party:
            if (h.alive and not h.tireless
                    and h.cur_sta <= PAUSE_STA_TRIGGER):
                fired.add("stamina")
                crossings.append(("stamina", h))
                break
    if "wounds" not in fired:
        for h in party:
            if h.alive and h.hp <= h.max_hp * PAUSE_HP_FRACTION:
                fired.add("wounds")
                crossings.append(("wounds", h))
                break
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
        h.cur_sta = min(h.sta, h.cur_sta + STAMINA_DRAUGHT_RESTORE)
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
        h.cur_sta = min(h.sta, h.cur_sta + BERSERK_STA_GAIN)
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
        h.cur_sta = min(h.sta, h.cur_sta + WAR_BREATH_STA_GAIN)
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
        h.cur_sta = min(h.sta, h.cur_sta + STA_RECOVERY_AFTER_FIGHT)
    log.append(f"    The party catches its breath "
               f"(+{STA_RECOVERY_AFTER_FIGHT} STA)")


def group_combat(party: list[Entity], foes: list[Entity],
                 rng: random.Random, log: list[str],
                 max_rounds: int = 40,
                 pause_triggers: bool = False, fired: set[str] | None = None,
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

    Stamina: an attack costs the attacker `swing_cost` STA -- set by the
    wielded weapon (defense is free); tireless entities pay nothing. An entity
    that hits 0 STA is SPENT: it still swings (desperation is free) but takes
    -SPENT_PENALTY to all rolls, attack and defense alike, with no in-fight
    recovery (short of a stamina draught drunk at a pause). Against fresh foes
    that is a death sentence; two spent sides cancel each other's penalties
    and the wound spiral still finishes the fight -- so melees resolve instead
    of stalling (max_rounds is only a safety valve). When the fight ends the
    survivors catch their breath (+STA_RECOVERY_AFTER_FIGHT).

    The pause (the interrupt primitive): with pause_triggers=True the fight
    PAUSES at the end of a round in which a hero crossed STA <=
    PAUSE_STA_TRIGGER or HP <= half (each trigger once per fight -- `fired`
    carries the used ones across a resume). Returns a Pause instead of
    finishing; the caller decides (fight on / pause actions / retreat) and
    calls again with fired, first_round=pause.round+1, and `actions`
    ({hero: "drink" | "berserk" | "war-breath"}, executed at the top of the
    resumed round: the hero skips that attack and defends at
    -PAUSE_ACTION_DEF_PENALTY). Returns None when the melee actually ended.
    """
    party_set = set(party)
    if fired is None:
        fired = set()
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

        # Round-start snapshot: everyone alive NOW acts this round, even if
        # felled before their turn comes -- the dying swing (see docstring).
        actors = [e for e in party + foes if e.alive]
        start_pens = {e: e.wound_penalty for e in actors}
        for attacker in actors:
            if attacker in busy:
                continue    # occupied with their draught/conversion this round
            dying = not attacker.alive      # felled earlier this round
            targets = foes if attacker in party_set else party
            if not any(t.alive for t in targets):
                continue        # nobody left on the other side for THIS
                                # attacker; a dying foe later in the order
                                # may still owe the party its last blow
            if not attacker.tireless and not dying:
                # The dying swing is free -- desperation costs nothing.
                was_winded = attacker.winded
                # The weapon sets the swing price (zweihander 2, most else 1).
                attacker.cur_sta = max(0, attacker.cur_sta - attacker.swing_cost)
                if attacker.winded and not was_winded:
                    log.append(f"    !! {attacker.name} is Winded "
                               f"(STA {attacker.cur_sta} -- -{WINDED_PENALTY} "
                               f"to all rolls until they catch their breath)")
                if attacker.spent and attacker not in spent_logged:
                    # Covers both the swing that emptied the tank and walking
                    # into the fight already at 0.
                    spent_logged.add(attacker)
                    log.append(f"    !! {attacker.name} is SPENT -- running "
                               f"on empty (-{SPENT_PENALTY} to all rolls "
                               f"until the fight ends)")
            defender = _pick_target(targets, rng,
                                    focus=attacker in party_set)
            if dying:
                log.append(f"    ({attacker.name} strikes even as they fall)")
            was_alive = defender.alive
            _attack(attacker, defender, rng, log,
                    atk_wound_pen=start_pens[attacker] if dying else None,
                    def_mod=(-PAUSE_ACTION_DEF_PENALTY
                             if defender in busy else 0),
                    def_label=busy_label.get(busy.get(defender, ""), ""))
            if was_alive and not defender.alive:
                if defender.dead:
                    log.append(f"    *** {defender.name} is SLAIN. ***")
                elif defender in party_set:
                    log.append(f"    {defender.name} goes down, "
                               f"out of the fight.")
                else:
                    log.append(f"    *** {defender.name} falls. ***")
        busy.clear()
        log.append(_stamina_line(party, foes))

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

    # The dust settles: whoever is still standing catches their breath.
    survivors = [h for h in party if h.alive]
    if survivors:
        _catch_breath(survivors, log)
    return None


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
    at a random fleeing hero, who defends at -PAUSE_ACTION_DEF_PENALTY. Then
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
        _attack(f, h, rng, log, def_mod=-PAUSE_ACTION_DEF_PENALTY,
                def_label="fleeing")
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
        _catch_breath(runners, log)
        return True

    flee_dex = _chase_dex(runners)
    hunt_dex = _chase_dex(pursuers)
    flee_dice = rng.randint(1, 6) + rng.randint(1, 6)
    hunt_dice = rng.randint(1, 6) + rng.randint(1, 6)
    flee_total = flee_dice + flee_dex + FLEE_BONUS
    hunt_total = hunt_dice + hunt_dex
    log.append(f"    the chase: flight {flee_total:.1f} (2d6={flee_dice}, "
               f"+{flee_dex:.1f} DEX STA-weighted, +{FLEE_BONUS} head start) "
               f"vs pursuit {hunt_total:.1f} (2d6={hunt_dice}, "
               f"+{hunt_dex:.1f} DEX STA-weighted)")
    if flee_total >= hunt_total:
        log.append("    They break away -- clean escape.")
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
        if days_passed > 0 and not f.undead:
            f.hp = f.max_hp
            f.down = False
    return survivors


# --------------------------------------------------------------------------- #
# Character generation
# --------------------------------------------------------------------------- #

# Rolled ranges for a starting hero. 3-6 straddles the human bands in rules.md:
# a 3 is trained-soldier grade, a 6 nudges past elite-veteran. HP 8-12 likewise.
HERO_STAT_RANGE = (3, 6)      # DEX / STR
# STA gets its own, higher range: it is the second death-track (the swing
# budget; running dry mid-fight is usually fatal), so its floor matters like
# HP's floor -- a 4-STA hero is a 4-swing hero, and the batch sims show those
# parties are the wipes. Floor 5 also keeps a fresh hero two swings clear of
# the Winded line (WINDED_STA = 3).
HERO_STA_RANGE = (5, 8)
HERO_HP_RANGE = (8, 12)
HERO_POWER_RANGE = (3, 6)

# Flavor epithet from the highest stat (ties resolve in this order).
EPITHETS = {"dex": "precise", "str": "powerful", "sta": "steady"}

NAMES = ["Brand", "Sela", "Corvin", "Mira", "Doran", "Yssa", "Kael", "Rhea",
         "Tomas", "Inga", "Veld", "Nessa"]


def random_kit(rng: random.Random) -> dict[str, int]:
    """Two random potions at creation -- the whole starting stock. Nothing
    refills for free; further potions are bought with gold or dropped."""
    kit = {k: 0 for k in STOCKED_POTION_KINDS}
    for _ in range(STARTING_POTIONS):
        kit[rng.choice(STOCKED_POTION_KINDS)] += 1
    return kit


def make_human(rng: random.Random, name: str) -> Entity:
    """Fully random generation: DEX/STR 3-6, STA 5-8, HP 8-12, Power 3-6, a random
    ability (heal / bulwark / first_blood -- mend, mitigate, or open aggressively),
    two random potions, and a starting weapon (the common table: 50% crude /
    45% soldier's arms / 5% heavy; healers often carry the wooden staff)."""
    stats = {k: rng.randint(*HERO_STAT_RANGE) for k in ("dex", "str")}
    stats["sta"] = rng.randint(*HERO_STA_RANGE)
    # Epithet from the highest stat, with STA normalized back to the DEX/STR
    # scale (its rolled range sits 2 higher) so "steady" doesn't win every tie.
    ranked = dict(stats, sta=stats["sta"] - (HERO_STA_RANGE[0] - HERO_STAT_RANGE[0]))
    epithet = EPITHETS[max(ranked, key=ranked.get)]
    ability = rng.choice(["heal", "bulwark", "first_blood"])
    if ability == "heal" and rng.random() < HEALER_STAFF_CHANCE:
        weapon = WEAPONS["wooden staff"]    # the caster-bridge weapon at home
                                            # in a healer's hands (+1 to Heal)
    else:
        weapon = random_common_weapon(rng)
    return Entity(
        name=f"{name} the {epithet}",
        dex=stats["dex"],
        str_=stats["str"],
        sta=stats["sta"],
        max_hp=rng.randint(*HERO_HP_RANGE),
        power=rng.randint(*HERO_POWER_RANGE),
        ability=ability,
        weapon=weapon,
        items=random_kit(rng),
    )


def make_party(rng: random.Random) -> list[Entity]:
    names = rng.sample(NAMES, 2)
    return [make_human(rng, names[0]), make_human(rng, names[1])]


def make_skeleton(rng: random.Random, n: int) -> Entity:
    # Brittle and a weak individual hitter (low STR -> low severity), but
    # undead: no pain (wound roll penalty halved -- a graze costs it nothing,
    # which also blunts First Blood's spiral here) and TIRELESS (never spends
    # STA, never Winded or Spent -- they don't tire; you do). No Power, no
    # saves, no kit. The threat is numbers pressing a party whose stamina is a
    # death-track: the bones don't have to beat you, just outlast you.
    # They swing corroded grave-steel (durability 1): against a party carrying
    # quality weapons the rusted blades start snapping -- the barrow gets
    # *visibly* easier with better gear, not just numerically.
    # pursues=False: bound to the grave -- they swing at a fleeing party's
    # backs but never follow past the door, which is what makes "come back
    # tomorrow and finish it" a real plan instead of a death sentence.
    return Entity(name=f"Skeleton {n}", dex=3, str_=2, sta=8, max_hp=5,
                  sta_cost=0, undead=True, tireless=True, pursues=False,
                  weapon=RUSTED_BLADE)


# --------------------------------------------------------------------------- #
# The dungeon (one "day")
# --------------------------------------------------------------------------- #

# Rooms of skeletons -- the TOUGH site (pays 3x; train up at the bandit hideout
# first). HP and STA both carry across the whole run with only a brief
# catch-breath between rooms (no per-fight reset); HP wounds and the STA
# death-track both bind, and the skeletons are tireless -- numbers grinding a
# party dry is the whole threat. Power and items deplete.
# BARROW_ROOMS is the SET encounter list for the site (name, skeleton count) --
# session play (`session.py barrow ROOM`) and the one-shot run both use it, so
# the layout tune.py/bench_training.py balance is the layout actually played.
BARROW_ROOMS = [
    ("the collapsed entry", 3),
    ("the ossuary", 3),
    ("the burial vault", 4),
]
DUNGEON_ROOMS = [n for _, n in BARROW_ROOMS]  # counts only (tune.py sweeps this)


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
    every fight), so it must never have to be scraped off a combat log."""
    kit = ", ".join(f"{k}x{v}" for k, v in e.items.items() if v) or "no kit"
    return (f"{e.name} (L{e.level}, training {e.training}): "
            f"DEX {e.dex}  STR {e.str_}  STA {e.cur_sta}/{e.sta}  "
            f"HP {e.hp}/{e.max_hp}  Power {e.cur_power}/{e.power}  "
            f"({e.ability or 'no save'}; {weapon_tag(e)}; {kit})")


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
        bits.append(f"{n}{name} ({w.atk_tempo:+d} atk/{w.severity:+d} sev, "
                    f"{w.value}g)")
    return "  Left among the dead: " + ", ".join(bits) + "."


# --------------------------------------------------------------------------- #
# Progression & economy
# --------------------------------------------------------------------------- #

def xp_to_next(level: int) -> int:
    return XP_LEVEL_STEP * level


def award_xp(party: list[Entity], amount: int, log: list[str],
             reason: str = "") -> None:
    """Every hero who is not truly dead earns the full amount (no splitting --
    the party levels together). Handles level-ups and banks skill points."""
    note = f" ({reason})" if reason else ""
    for h in party:
        if h.dead:
            continue
        h.xp += amount
        log.append(f"    {h.name} gains {amount} XP{note} "
                   f"[{h.xp}/{xp_to_next(h.level)}]")
        while h.xp >= xp_to_next(h.level):
            h.xp -= xp_to_next(h.level)
            h.level += 1
            h.skill_points += SKILL_POINTS_PER_LEVEL
            log.append(f"    *** {h.name} reaches level {h.level}! "
                       f"(+{SKILL_POINTS_PER_LEVEL} skill point, "
                       f"{h.skill_points} unspent) ***")


def train_combat_once(h: Entity, log: list[str]) -> bool:
    """Spend skill points on ONE rank of combat training (rank n costs n,
    +1 to ALL tempo rolls per rank, cap TRAINING_MAX). The session-play shape:
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
               f"(+{h.training} to all tempo rolls) "
               f"[{h.skill_points} point(s) left]")
    return True


def train_proficiency(h: Entity, log: list[str]) -> bool:
    """Spend skill points on ONE rank of proficiency with the WIELDED weapon
    (+1 attack tempo AND +1 severity with that weapon per rank; rank n costs
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
               f"{rank + 1} (+{rank + 1} attack tempo and +{rank + 1} "
               f"severity with it) [{h.skill_points} point(s) left]")
    return True


def train_combat(h: Entity, log: list[str]) -> bool:
    """Greedy auto-spend on combat training -- the SIM policy only (run_dungeon
    / run_hideout call it after quest awards so tune.py / bench_training.py
    model a party that spends its points). Real play never auto-spends:
    session.py banks the points and the player chooses via `train`."""
    trained = False
    while h.training < TRAINING_MAX and h.skill_points > h.training:
        h.skill_points -= h.training + 1
        h.training += 1
        trained = True
        log.append(f"    {h.name} trains: combat training rank {h.training} "
                   f"(+{h.training} to all tempo rolls)")
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


def award_quest(party: list[Entity], purse: Purse, gold: int, xp: int,
                log: list[str], name: str) -> None:
    """Clearing a whole site completes its quest: gold to the purse and an XP
    lump to everyone still alive. Skill points are BANKED, not auto-spent --
    with two sinks now (combat training vs weapon proficiency) spending is a
    real player choice (session.py `train`); only the sim paths auto-train."""
    log.append("")
    log.append(f"  *** QUEST COMPLETE: {name}. Reward: {gold} gold. ***")
    purse.gold += gold
    log.append(f"    The party purse holds {purse.gold} gold.")
    award_xp(party, xp, log, "quest")


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
        h.hp = min(h.max_hp, max(h.hp, 0) + HEALING_POTION_RESTORE)
        if h.hp > 0:
            h.down = False
        log.append(f"    {h.name} drinks a healing potion "
                   f"(HP {before} -> {h.hp}/{h.max_hp}; {h.items['healing']} left)")
    elif kind == "stamina":
        before = h.cur_sta
        h.cur_sta = min(h.sta, h.cur_sta + STAMINA_DRAUGHT_RESTORE)
        log.append(f"    {h.name} downs a stamina draught "
                   f"(STA {before} -> {h.cur_sta}; {h.items['stamina']} left)")
    else:  # power
        before = h.cur_power
        h.cur_power = min(h.power, h.cur_power + POWER_POTION_RESTORE)
        log.append(f"    {h.name} drinks a power potion "
                   f"(Power {before} -> {h.cur_power}; {h.items['power']} left)")
    return True


def auto_use_potions_on_rest(survivors: list[Entity], log: list[str]) -> None:
    """The 'sensible party' rest-time policy for the sim / one-shot paths only
    (run_dungeon, scratch_bandits) -- NOT for real play, which leaves every
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
    """A short rest (~an hour or two): a little STA and HP back. Costs one of the
    day's short-rest slots. Returns False (no effect) once the day's slots are
    spent -- there is no more mid-day recovery then; the party pushes on depleted
    or Claude calls long_rest() to make camp. Potions are NOT drunk here: that is
    a deliberate DM call (use_potion), never automatic."""
    if clock.short_rests_left <= 0:
        log.append("    (no short rest left today -- the party must push on "
                   "or make camp)")
        return False
    clock.short_rests_used += 1
    log.append(f"  The party takes a short rest "
               f"({clock.short_rests_left} left today).")
    for h in survivors:
        # STA is the per-day clock: only a slow catch-breath, never a full reset.
        h.cur_sta = min(h.sta, h.cur_sta + STA_RECOVERY_BETWEEN_ROOMS)
        # HP carries across rooms too: only a minimal catch-breath, not a reset.
        h.hp = min(h.max_hp, h.hp + HP_RECOVERY_BETWEEN_ROOMS)
    return True


def long_rest(party: list[Entity], clock: Clock, log: list[str]) -> None:
    """Make camp for the night. A deliberate, Claude-invoked step -- never
    automatic. STA recharges fully overnight; HP knits back at each character's
    weekly rate; Down heroes get back on their feet; the day advances and the
    short-rest slots refill. Only the truly Dead stay down."""
    clock.day += 1
    clock.short_rests_used = 0
    log.append(f"  --- The party makes camp. Night passes; day {clock.day} dawns. ---")
    for h in party:
        if h.dead:
            continue
        h.cur_sta = h.sta                       # STA fully recharges overnight
        h.down = False
        before = h.hp
        h.hp = min(h.max_hp, max(h.hp, 0) + h.hp_regen_per_night)
        note = f"STA full ({h.cur_sta}/{h.sta})"
        if h.hp != before:
            note += f", +{h.hp - before} HP -> {h.hp}/{h.max_hp}"
        else:
            note += ", HP full"
        log.append(f"    {h.name}: {note}")


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
              log: list[str]) -> str:
    """One encounter under the batch-sim pause policy (drink / convert /
    retreat -- sim_pause_policy). Returns "resolved" (the melee ended; read
    the outcome off the entities) or "fled" (a clean escape; foes survive).
    The scenario loops (run_dungeon / run_hideout) and session play share the
    same engine; only WHO answers the pause differs -- here a policy, there
    the player."""
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


def run_dungeon(party: list[Entity], clock: Clock, purse: Purse,
                rng: random.Random, log: list[str]) -> None:
    skel_count = 0
    cleared_all = True
    room_i = 0
    attempts = 0
    held_over: list[Entity] | None = None   # survivors of a room the party fled
    while room_i < len(DUNGEON_ROOMS):
        n_skel = DUNGEON_ROOMS[room_i]
        living = [h for h in party if not h.dead]
        if not living:
            cleared_all = False
            break

        log.append("")
        if held_over is None:
            attempts = 1
            log.append(f"=== Room {room_i + 1}: {n_skel} skeletons rise "
                       f"from the bones ===")
            skeletons = []
            for _ in range(n_skel):
                skel_count += 1
                skeletons.append(make_skeleton(rng, skel_count))
            s = skeletons[0]
            log.append(f"  {len(skeletons)} skeletons: DEX {s.dex}  "
                       f"STR {s.str_}  HP {s.max_hp} each "
                       f"(undead: no pain, tireless; rusted blades)")
        else:
            attempts += 1
            skeletons = held_over
            held_over = None
            standing = sum(1 for s in skeletons if s.alive)
            log.append(f"=== Room {room_i + 1}, again: "
                       f"{standing} skeleton(s) still stand among "
                       f"the hacked bones ===")
        for h in living:
            start_fight(h, log)

        result = sim_fight(living, skeletons, rng, log)

        if party_wiped(party, log):
            cleared_all = False
            break
        if result == "fled":
            if attempts >= SIM_MAX_ROOM_ATTEMPTS:
                log.append("  The party has had enough -- "
                           "the barrow is abandoned.")
                cleared_all = False
                break
            # Rest up and go back in (the sims' determined-player policy):
            # a short rest if a slot is left today, else camp overnight.
            day_before = clock.day
            survivors = [h for h in party if h.alive]
            if not short_rest(survivors, clock, log):
                long_rest(party, clock, log)
            auto_use_potions_on_rest([h for h in party if h.alive], log)
            held_over = refresh_foes_after_retreat(
                skeletons, clock.day - day_before)
            continue    # the same room, again
        if any(s.alive for s in skeletons):
            # Unresolved (the fight staggered apart): no award, no clear.
            log.append("  The room is not cleared -- the party pulls back.")
            cleared_all = False
            break

        award_xp(party, BARROW_ENCOUNTER_XP, log, "encounter")
        roll_loot(party, purse, rng, log)

        survivors = [h for h in party if h.alive]
        if survivors:
            log.append(f"  Room cleared. {len(survivors)} still standing.")
            short_rest(survivors, clock, log)
            auto_use_potions_on_rest(survivors, log)  # one-shot sim: sensible party
        room_i += 1

    if cleared_all and any(not h.dead for h in party):
        award_quest(party, purse, BARROW_QUEST_GOLD, BARROW_QUEST_XP,
                    log, "the barrow is cleansed")
        for h in party:
            if not h.dead:
                train_combat(h, log)    # sim policy: auto-spend on training


def outcome(party: list[Entity]) -> str:
    """How many were truly slain (Down does not count -- it recovers)."""
    dead = sum(1 for h in party if h.dead)
    return {0: "none", 1: "one", 2: "both"}[dead]


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    party = make_party(rng)
    clock = Clock()
    purse = Purse()
    log: list[str] = []
    log.append(f"Day {clock.day}. The party descends into the barrow:")
    for h in party:
        log.append("  " + stat_line(h))

    run_dungeon(party, clock, purse, rng, log)
    # No auto-night: making camp (long_rest) is a deliberate call Claude makes
    # between adventuring days, not something the dungeon does on its own.

    log.append("")
    dead = [h for h in party if h.dead]
    alive = [h for h in party if not h.dead]
    log.append(f"OUTCOME: {outcome(party)} of the party died. "
               f"Purse: {purse.gold} gold.")
    if dead:
        log.append("  Fallen:   " + ", ".join(h.name for h in dead))
    if alive:
        log.append("  Survived: " + ", ".join(
            f"{h.name} (L{h.level}, Power {h.cur_power}/{h.power}, "
            f"STA {h.cur_sta}/{h.sta})" for h in alive))

    print("\n".join(log))


if __name__ == "__main__":
    main()
