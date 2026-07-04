"""Combat Sim - combat engine, random party, and a skeleton dungeon.

Implements the ruleset in rules.md (core + the Survival & Resources add-on +
the first slice of Progression). A fight takes no input once it starts; it
produces an outcome and a narrative log. Generalized from a 1v1 exchange to a
group melee so a party can be swarmed (numbers are the skeletons' whole threat).

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
(a flat tempo bonus, the veteran-vs-novice axis). Gold accrues in a shared
party purse from quest rewards and occasional encounter drops; potions are
bought with gold (buy_potion is a between-adventures call the DM makes), never
auto-refilled. Heroes start with just two random potions. Potions are also
*used* by deliberate DM call (use_potion), between fights -- never automatically;
the one-shot/sim paths model a sensible party via auto_use_potions_*.

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
POTION_KINDS = ("healing", "power", "stamina")
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

# --- Time economy (the clock) ---------------------------------------------- #
# A "day" is a slot budget, not a wall clock. The party gets a limited number of
# SHORT rests -- each ~ an hour or two of narrative time -- between fights; when
# those run out there is no more mid-day recovery and the party must make camp
# for a LONG rest (overnight). Nothing forces the day's end: long_rest() is a
# function Claude calls on purpose (see the module docstring / CLAUDE.md), never
# automatic. A long rest recharges STA fully and knits HP back at a per-character
# weekly rate (~max_hp / 7 per night -> roughly a week to fully heal).
SHORT_RESTS_PER_DAY = 2          # short-rest slots available each day

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

    def breakdown(self, name: str) -> str:
        parts = [f"2d6={self.dice}", f"+{self.dex} DEX"]
        if self.training:
            parts.append(f"+{self.training} training")
        if self.wound_pen:
            parts.append(f"-{self.wound_pen} wounds")
        if self.fatigue_pen:
            parts.append(f"-{self.fatigue_pen} {self.fatigue_label}")
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

    def tempo(self, rng: random.Random) -> TempoRoll:
        dice = rng.randint(1, 6) + rng.randint(1, 6)
        if self.spent:
            fatigue_pen, fatigue_label = SPENT_PENALTY, "spent"
        elif self.winded:
            fatigue_pen, fatigue_label = WINDED_PENALTY, "winded"
        else:
            fatigue_pen, fatigue_label = 0, ""
        total = (dice + self.dex + self.training
                 - self.wound_penalty - fatigue_pen)
        return TempoRoll(total=total, dice=dice, dex=self.dex,
                         training=self.training, wound_pen=self.wound_penalty,
                         fatigue_pen=fatigue_pen, fatigue_label=fatigue_label)


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


def _attack(attacker: Entity, defender: Entity, rng: random.Random,
            log: list[str]) -> None:
    """One opposed exchange. Higher roll lands; severity sets the wound.

    The *raw* result is computed first (it may be a killing blow); a Power save
    can then step it down one tier. The log states the blow that would have
    landed. Death only happens when a raw killing blow is not saved.

    Every exchange logs two layers: an interpretive headline first, then the
    raw numbers (dice, each modifier and its source) indented beneath it.
    """
    atk = attacker.tempo(rng)
    dfn = defender.tempo(rng)
    tempo_line = (f"        tempo: {atk.breakdown(attacker.name)} vs "
                  f"{dfn.breakdown(defender.name)}")

    if atk.total == dfn.total:
        # A tie: no one lands. High dice = furious contact, low = circling.
        if max(atk.dice, dfn.dice) >= TIE_HIGH_DICE:
            label = "Clash! Steel rings; neither yields"
        else:
            label = "Lull. They circle, probing for an opening"
        log.append(f"    {attacker.name} and {defender.name} -- {label}.")
        log.append(tempo_line)
        return

    if atk.total < dfn.total:
        log.append(f"    {attacker.name} attacks {defender.name} -- parried.")
        log.append(tempo_line)
        return

    margin = atk.total - dfn.total
    severity = margin + attacker.str_ - defender.str_
    raw_tier, dmg = wound_tier(severity)
    sev_line = (f"        severity: {severity} = margin {margin} "
                f"+{attacker.str_} STR -{defender.str_} soak -> {raw_tier}")

    if dmg == 0:
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


def group_combat(party: list[Entity], foes: list[Entity],
                 rng: random.Random, log: list[str],
                 max_rounds: int = 40) -> None:
    """Resolve a melee in place. Survivors keep their HP/STA/Power as-is.

    Exchanges resolve *sequentially* -- party in list order first, then foes --
    and every attacker picks a living target at the moment it acts, so a foe
    slain mid-round is neither attacked again nor gets a posthumous swing.

    Stamina: an attack costs the attacker `sta_cost` STA (defense is free);
    tireless entities pay nothing. An entity that hits 0 STA is SPENT: it
    still swings (desperation is free) but takes -SPENT_PENALTY to all rolls,
    attack and defense alike, with no in-fight recovery. Against fresh foes
    that is a death sentence; two spent sides cancel each other's penalties
    and the wound spiral still finishes the fight -- so melees resolve instead
    of stalling (max_rounds is only a safety valve). When the fight ends the
    survivors catch their breath (+STA_RECOVERY_AFTER_FIGHT).
    """
    party_set = set(party)
    spent_logged: set[Entity] = set()
    rnd = 0
    while any(e.alive for e in party) and any(e.alive for e in foes):
        rnd += 1
        if rnd > max_rounds:
            log.append("    (the fight grinds to a standstill)")
            break
        log.append(f"  Round {rnd}:")
        if rnd == 1:
            _first_blood(party, foes, rng, log)

        for attacker in party + foes:
            if not attacker.alive:
                continue        # felled before its turn came: no swing
            targets = foes if attacker in party_set else party
            if not any(t.alive for t in targets):
                break           # no one left to fight this round
            if not attacker.tireless:
                was_winded = attacker.winded
                attacker.cur_sta = max(0, attacker.cur_sta - attacker.sta_cost)
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
            was_alive = defender.alive
            _attack(attacker, defender, rng, log)
            if was_alive and not defender.alive:
                if defender.dead:
                    log.append(f"    *** {defender.name} is SLAIN. ***")
                elif defender in party_set:
                    log.append(f"    {defender.name} goes down, "
                               f"out of the fight.")
                else:
                    log.append(f"    *** {defender.name} falls. ***")
        log.append(_stamina_line(party, foes))

    # The dust settles: whoever is still standing catches their breath.
    survivors = [h for h in party if h.alive]
    if survivors:
        for h in survivors:
            h.cur_sta = min(h.sta, h.cur_sta + STA_RECOVERY_AFTER_FIGHT)
        log.append(f"    The party catches its breath "
                   f"(+{STA_RECOVERY_AFTER_FIGHT} STA)")


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
    kit = {k: 0 for k in POTION_KINDS}
    for _ in range(STARTING_POTIONS):
        kit[rng.choice(POTION_KINDS)] += 1
    return kit


def make_human(rng: random.Random, name: str) -> Entity:
    """Fully random generation: DEX/STR 3-6, STA 4-7, HP 8-12, Power 3-6, a random
    ability (heal / bulwark / first_blood -- mend, mitigate, or open aggressively),
    and two random potions."""
    stats = {k: rng.randint(*HERO_STAT_RANGE) for k in ("dex", "str")}
    stats["sta"] = rng.randint(*HERO_STA_RANGE)
    # Epithet from the highest stat, with STA normalized back to the DEX/STR
    # scale (its rolled range sits 2 higher) so "steady" doesn't win every tie.
    ranked = dict(stats, sta=stats["sta"] - (HERO_STA_RANGE[0] - HERO_STAT_RANGE[0]))
    epithet = EPITHETS[max(ranked, key=ranked.get)]
    return Entity(
        name=f"{name} the {epithet}",
        dex=stats["dex"],
        str_=stats["str"],
        sta=stats["sta"],
        max_hp=rng.randint(*HERO_HP_RANGE),
        power=rng.randint(*HERO_POWER_RANGE),
        ability=rng.choice(["heal", "bulwark", "first_blood"]),
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
    return Entity(name=f"Skeleton {n}", dex=3, str_=2, sta=8, max_hp=5,
                  sta_cost=0, undead=True, tireless=True)


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


def stat_line(e: Entity) -> str:
    kit = ", ".join(f"{k}x{v}" for k, v in e.items.items() if v) or "no kit"
    return (f"{e.name} (L{e.level}, training {e.training}): "
            f"DEX {e.dex}  STR {e.str_}  STA {e.sta}  "
            f"HP {e.hp}/{e.max_hp}  Power {e.power}  ({e.ability or 'no save'}; "
            f"{kit})")


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


def train_combat(h: Entity, log: list[str]) -> bool:
    """Spend banked skill points on combat training (rank n costs n points,
    +1 tempo per rank). The only skill for now, so the scenarios call this
    right after XP awards; once more skills exist, spending becomes a real
    player choice made between fights."""
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
        kind = rng.choice(POTION_KINDS)
        h = rng.choice(living)
        h.items[kind] = h.items.get(kind, 0) + 1
        log.append(f"    Loot: a {kind} potion -- {h.name} pockets it "
                   f"({kind} x{h.items[kind]}).")


def award_quest(party: list[Entity], purse: Purse, gold: int, xp: int,
                log: list[str], name: str) -> None:
    """Clearing a whole site completes its quest: gold to the purse, an XP lump
    to everyone still alive, and any earned training is applied."""
    log.append("")
    log.append(f"  *** QUEST COMPLETE: {name}. Reward: {gold} gold. ***")
    purse.gold += gold
    log.append(f"    The party purse holds {purse.gold} gold.")
    award_xp(party, xp, log, "quest")
    for h in party:
        if not h.dead:
            train_combat(h, log)


def buy_potion(h: Entity, purse: Purse, kind: str, log: list[str]) -> bool:
    """Buy one potion from the party purse. A between-adventures call the DM
    makes on the player's decision -- nothing in the engine buys automatically."""
    if kind not in POTION_KINDS:
        raise ValueError(f"unknown potion kind: {kind}")
    if purse.gold < POTION_PRICE:
        log.append(f"    Not enough gold for a {kind} potion "
                   f"({purse.gold}g / {POTION_PRICE}g).")
        return False
    purse.gold -= POTION_PRICE
    h.items[kind] = h.items.get(kind, 0) + 1
    log.append(f"    {h.name} buys a {kind} potion for {POTION_PRICE}g "
               f"({kind} x{h.items[kind]}; purse: {purse.gold}g).")
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
    before = target.hp
    target.hp = min(target.max_hp, target.hp + amount)
    if target.hp > 0:
        target.down = False
    log.append(f"    {healer.name} spends {HEAL_COST} Power to Heal "
               f"{target.name} (+{target.hp - before} HP -> "
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


def run_dungeon(party: list[Entity], clock: Clock, purse: Purse,
                rng: random.Random, log: list[str]) -> None:
    skel_count = 0
    cleared_all = True
    for i, n_skel in enumerate(DUNGEON_ROOMS, start=1):
        living = [h for h in party if not h.dead]
        if not living:
            cleared_all = False
            break

        log.append("")
        log.append(f"=== Room {i}: {n_skel} skeletons rise from the bones ===")
        for h in living:
            start_fight(h, log)

        skeletons = []
        for _ in range(n_skel):
            skel_count += 1
            skeletons.append(make_skeleton(rng, skel_count))
        s = skeletons[0]
        log.append(f"  {len(skeletons)} skeletons: DEX {s.dex}  STR {s.str_}  "
                   f"HP {s.max_hp} each (undead: no pain, tireless)")

        group_combat(living, skeletons, rng, log)

        if party_wiped(party, log):
            cleared_all = False
            break
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

    if cleared_all and any(not h.dead for h in party):
        award_quest(party, purse, BARROW_QUEST_GOLD, BARROW_QUEST_XP,
                    log, "the barrow is cleansed")


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
