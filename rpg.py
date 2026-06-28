"""Combat Sim - combat engine, random party, and a skeleton dungeon.

Implements the ruleset in rpg2-rules.md (core + the Survival & Resources add-on).
A fight takes no input once it starts; it produces an outcome and a narrative log.
Generalized from a 1v1 exchange to a group melee so a party can be swarmed
(numbers are the skeletons' whole threat).

Survival layer: HP carries across the whole run (only a minimal catch-breath
between rooms, never a per-fight reset); 0 HP is Down (out of this fight, stands
back up minimally next room), not Dead; Power buys off killing/grievous blows in
the moment; STA is a per-day clock that drains across the whole run; prepped
healing potions regen HP each round. A character only truly dies when a killing
blow lands and the saves have run dry.

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

WINDED_STA = 3          # STA <= this -> Winded
WINDED_PENALTY = 2      # roll penalty while Winded

# Survival add-on tunables.
SAVE_COST = 2           # Power spent to reduce one wound tier (Heal / Bulwark)
HEAL_REGEN = 1          # HP/round granted by a healing potion prepped before a fight
POWER_POTION_RESTORE = 5
STAMINA_DRAUGHT_RESTORE = 4
STA_RECOVERY_BETWEEN_ROOMS = 1   # brief catch-breath; STA is per-day, not reset
HP_RECOVERY_BETWEEN_ROOMS = 1    # minimal HP catch-breath; wounds carry, not reset
REVIVE_HP = 1                    # HP a Down hero stands back up with (minimal)

# Wound tiers as an ordered ladder, so a save can step a blow down one notch.
TIER_ORDER = ["deflected", "graze", "wound", "grievous", "killing blow"]
TIER_HP = {"deflected": 0, "graze": 1, "wound": 2, "grievous": 4, "killing blow": 6}

ABILITY_VERB = {"bulwark": "Bulwark", "heal": "Heal"}


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


@dataclass(eq=False)
class Entity:
    name: str
    dex: int
    str_: int
    sta: int
    max_hp: int
    power: int = 0
    ability: str | None = None          # "heal" or "bulwark"; None = no in-fight save
    hp: int = field(default=0)
    cur_sta: int = field(default=0)
    cur_power: int = field(default=0)
    regen: int = field(default=0)       # HP/round this fight (prepped healing potion)
    down: bool = field(default=False)   # at 0 HP, out of this fight (recoverable)
    dead: bool = field(default=False)   # truly slain (unsaved killing blow)
    items: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.hp = self.max_hp
        self.cur_sta = self.sta
        self.cur_power = self.power

    # --- derived state -------------------------------------------------- #
    @property
    def alive(self) -> bool:
        # "Still in the fight." Down and Dead both sit at 0 HP.
        return self.hp > 0

    @property
    def hp_lost(self) -> int:
        return self.max_hp - self.hp

    @property
    def winded(self) -> bool:
        return self.cur_sta <= WINDED_STA

    @property
    def drain(self) -> int:
        # Bigger frames burn fuel faster.
        return 1 + self.str_ // 4

    def tempo(self, rng: random.Random) -> int:
        roll = rng.randint(1, 6) + rng.randint(1, 6)
        penalty = self.hp_lost + (WINDED_PENALTY if self.winded else 0)
        return roll + self.dex - penalty


# --------------------------------------------------------------------------- #
# Combat: a group melee
# --------------------------------------------------------------------------- #

def _try_save(defender: Entity, tier: str, dmg: int) -> bool:
    """Decide whether the defender spends Power to step an incoming blow down.

    Policy (conservative, death-first): always buy off a *killing* blow if Power
    allows; buy off a *grievous* that would put us Down only when a reserve is
    left for a later death-save. Mutates Power. Returns True if a save fired.
    """
    if not defender.ability or defender.cur_power < SAVE_COST:
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
    """
    atk = attacker.tempo(rng)
    dfn = defender.tempo(rng)
    if atk <= dfn:
        return  # parried / evaded / clash
    severity = (atk - dfn) + attacker.str_ - defender.str_
    raw_tier, dmg = wound_tier(severity)
    if dmg == 0:
        return

    tier = raw_tier
    saved = _try_save(defender, tier, dmg)
    if saved:
        tier, dmg = reduce_tier(tier)

    defender.hp = max(0, defender.hp - dmg)

    if saved:
        verb = ABILITY_VERB.get(defender.ability, "Save")
        log.append(
            f"    {attacker.name}'s {raw_tier} on {defender.name} -- {verb} "
            f"flares; reduced to {tier} (-{dmg} HP -> {defender.hp}) "
            f"[{defender.cur_power} Power left]")
    else:
        log.append(f"    {attacker.name} lands a {tier} on {defender.name} "
                   f"(-{dmg} HP -> {defender.hp})")

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


def group_combat(party: list[Entity], foes: list[Entity],
                 rng: random.Random, log: list[str],
                 max_rounds: int = 40) -> None:
    """Resolve a melee in place. Survivors keep their HP/STA/Power as-is."""
    party_set = set(party)
    rnd = 0
    while any(e.alive for e in party) and any(e.alive for e in foes):
        rnd += 1
        if rnd > max_rounds:
            log.append("    (the fight grinds to a standstill)")
            break
        log.append(f"  Round {rnd}:")

        # Snapshot attacks against start-of-round state (simultaneous swings),
        # so a foe felled this round still gets its swing in.
        actions: list[tuple[Entity, Entity]] = []
        for hero in party:
            if hero.alive:
                actions.append((hero, _pick_target(foes, rng, focus=True)))
        for foe in foes:
            if foe.alive:
                actions.append((foe, _pick_target(party, rng, focus=False)))

        standing = {e for e in party + foes if e.alive}
        for attacker, defender in actions:
            _attack(attacker, defender, rng, log)  # planned swing always lands its attempt

        for e in foes + party:  # report exits once, foes first
            if e in standing and not e.alive:
                if e.dead:
                    log.append(f"    *** {e.name} is SLAIN. ***")
                elif e in party_set:
                    log.append(f"    {e.name} goes down, out of the fight.")
                else:
                    log.append(f"    *** {e.name} falls. ***")

        # Drain hits everyone still standing.
        for e in party + foes:
            if e.alive:
                e.cur_sta = max(0, e.cur_sta - e.drain)

        # Regen step: prepped healing potions tick after the drain.
        for e in party + foes:
            if e.alive and e.regen:
                before = e.hp
                e.hp = min(e.max_hp, e.hp + e.regen)
                if e.hp != before:
                    log.append(f"    {e.name} steadies (potion regen "
                               f"+{e.hp - before} HP -> {e.hp})")


# --------------------------------------------------------------------------- #
# Character generation
# --------------------------------------------------------------------------- #

ARCHETYPES = {
    # Elite-veteran band (rules: 4-5 / HP 8-10, Power 4-5). Adventurers good
    # enough to beat a lone skeleton, but who can be overwhelmed by a swarm.
    # Each has one in-the-moment save paid in Power.
    "precise": {  # lands often, fragile; heals the worst of it
        "dex": (5, 5), "str": (3, 3), "sta": (4, 5), "hp": (8, 8),
        "power": (4, 5), "ability": "heal",
    },
    "powerful": {  # heavy, durable, tires; a warrior's bulwark
        "dex": (4, 4), "str": (5, 5), "sta": (4, 4), "hp": (10, 10),
        "power": (4, 5), "ability": "bulwark",
    },
    "steady": {  # endurance, stays sharp; bulwark
        "dex": (4, 4), "str": (4, 4), "sta": (5, 5), "hp": (9, 9),
        "power": (5, 5), "ability": "bulwark",
    },
}

NAMES = ["Brand", "Sela", "Corvin", "Mira", "Doran", "Yssa", "Kael", "Rhea",
         "Tomas", "Inga", "Veld", "Nessa"]


def default_kit() -> dict[str, int]:
    """A veteran's starting consumables (the in-advance buffer)."""
    return {"healing": 2, "power": 1, "stamina": 1}


def make_human(rng: random.Random, name: str,
               archetype: str | None = None) -> Entity:
    archetype = archetype or rng.choice(list(ARCHETYPES))
    a = ARCHETYPES[archetype]
    return Entity(
        name=f"{name} the {archetype}",
        dex=rng.randint(*a["dex"]),
        str_=rng.randint(*a["str"]),
        sta=rng.randint(*a["sta"]),
        max_hp=rng.randint(*a["hp"]),
        power=rng.randint(*a["power"]),
        ability=a["ability"],
        items=default_kit(),
    )


def make_party(rng: random.Random) -> list[Entity]:
    names = rng.sample(NAMES, 2)
    return [make_human(rng, names[0]), make_human(rng, names[1])]


def make_skeleton(rng: random.Random, n: int) -> Entity:
    # Tireless but brittle, and a weak individual hitter (low STR -> low
    # severity). No Power, no saves, no kit. The threat is numbers.
    return Entity(name=f"Skeleton {n}", dex=3, str_=2, sta=8, max_hp=5)


# --------------------------------------------------------------------------- #
# The dungeon (one "day")
# --------------------------------------------------------------------------- #

# Rooms of skeletons. HP and STA both carry across the whole run with only a brief
# catch-breath between rooms (no per-fight reset); HP wounds and the per-day STA
# clock both bind. Power and items are per-day stocks that deplete.
DUNGEON_ROOMS = [2, 2, 3]


def stat_line(e: Entity) -> str:
    kit = ", ".join(f"{k}x{v}" for k, v in e.items.items() if v) or "no kit"
    return (f"{e.name}: DEX {e.dex}  STR {e.str_}  STA {e.sta}  "
            f"HP {e.hp}/{e.max_hp}  Power {e.power}  ({e.ability or 'no save'}; "
            f"{kit})")


def start_fight(h: Entity, log: list[str]) -> None:
    """Per-fight prep: bring a Down hero back to their feet (minimally) and prep
    a potion. HP is NOT reset -- wounds carry across rooms; healing comes from
    potions, spells, and resting between adventures, never a free per-fight top-up."""
    h.regen = 0
    if h.down or h.hp <= 0:
        h.hp = REVIVE_HP
        h.down = False
        log.append(f"    {h.name} is helped back to their feet ({REVIVE_HP} HP).")
    # Prep a healing potion if any remain: regen each round, this fight only.
    if h.items.get("healing", 0) > 0:
        h.items["healing"] -= 1
        h.regen = HEAL_REGEN
        log.append(f"    {h.name} preps a healing potion "
                   f"(+{HEAL_REGEN} HP/round; {h.items['healing']} left)")


def rest(survivors: list[Entity], log: list[str]) -> None:
    """Between-room rest: a little STA back, plus deliberate potion use."""
    for h in survivors:
        # STA is the per-day clock: only a slow catch-breath, never a full reset.
        h.cur_sta = min(h.sta, h.cur_sta + STA_RECOVERY_BETWEEN_ROOMS)
        # HP carries across rooms too: only a minimal catch-breath, not a reset.
        h.hp = min(h.max_hp, h.hp + HP_RECOVERY_BETWEEN_ROOMS)
        # Stamina draught: rare, saved for when badly winded.
        if h.cur_sta <= WINDED_STA and h.items.get("stamina", 0) > 0:
            h.items["stamina"] -= 1
            h.cur_sta = min(h.sta, h.cur_sta + STAMINA_DRAUGHT_RESTORE)
            log.append(f"    {h.name} downs a stamina draught "
                       f"(STA -> {h.cur_sta}; {h.items['stamina']} left)")
        # Power potion: top up when the save budget is nearly gone.
        if h.cur_power <= SAVE_COST and h.items.get("power", 0) > 0:
            h.items["power"] -= 1
            h.cur_power = min(h.power, h.cur_power + POWER_POTION_RESTORE)
            log.append(f"    {h.name} drinks a power potion "
                       f"(Power -> {h.cur_power}; {h.items['power']} left)")


def run_dungeon(party: list[Entity], rng: random.Random,
                log: list[str]) -> None:
    skel_count = 0
    for i, n_skel in enumerate(DUNGEON_ROOMS, start=1):
        living = [h for h in party if not h.dead]
        if not living:
            break

        log.append("")
        log.append(f"=== Room {i}: {n_skel} skeletons rise from the bones ===")
        for h in living:
            start_fight(h, log)

        skeletons = []
        for _ in range(n_skel):
            skel_count += 1
            skeletons.append(make_skeleton(rng, skel_count))

        group_combat(living, skeletons, rng, log)

        survivors = [h for h in party if h.alive]
        if survivors:
            log.append(f"  Room cleared. {len(survivors)} still standing.")
            rest(survivors, log)


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
    log: list[str] = []
    log.append("The party descends into the barrow:")
    for h in party:
        log.append("  " + stat_line(h))

    run_dungeon(party, rng, log)

    log.append("")
    dead = [h for h in party if h.dead]
    alive = [h for h in party if not h.dead]
    log.append(f"OUTCOME: {outcome(party)} of the party died.")
    if dead:
        log.append("  Fallen:   " + ", ".join(h.name for h in dead))
    if alive:
        log.append("  Survived: " + ", ".join(
            f"{h.name} (Power {h.cur_power}/{h.power}, STA {h.cur_sta}/{h.sta})"
            for h in alive))

    print("\n".join(log))


if __name__ == "__main__":
    main()
