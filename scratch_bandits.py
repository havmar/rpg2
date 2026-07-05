"""Scenario: a bandit hideout -- the STARTER site. Imports the engine from rpg.py.

Bandits are living fighters who play by exactly the party's rules: real
DEX/STR, they spend STA to swing, go Winded, and are SPENT at 0 like anyone
alive. That's deliberate -- this is the first site a new party runs, and its
logs teach the system with no special cases. (The skeleton barrow is the tough
site: tireless undead in numbers, the exception enemies you train up for.)

Rewards pay the base rate (a full clear = exactly the level-1 -> 2 XP cost);
the barrow pays 3x. `--training N` starts the party pre-trained.
"""

import argparse
import random

from rpg import (Entity, Clock, Purse, make_party, stat_line,
                 outcome, start_fight, short_rest, long_rest, party_wiped,
                 award_xp, award_quest, roll_loot, auto_use_potions_on_rest,
                 train_combat, random_common_weapon,
                 sim_fight, refresh_foes_after_retreat,
                 ENCOUNTER_XP, QUEST_XP, QUEST_GOLD, SIM_MAX_ROOM_ATTEMPTS)

# The starter site pays the base rate (the barrow pays 3x -- see rpg.py).
BANDIT_ENCOUNTER_XP = ENCOUNTER_XP
BANDIT_QUEST_XP = QUEST_XP
BANDIT_QUEST_GOLD = QUEST_GOLD

# Bandit roster: name, dex, str, sta, hp. No Power/ability/kit -- raw fighters
# who tire and go Spent exactly like the heroes do.
BANDIT_TYPES = {
    "cutthroat": (4, 3, 5, 7),   # nimble knife-work
    "bruiser":   (3, 5, 5, 9),   # slow, heavy, durable
    "archer":    (4, 2, 5, 6),   # lands often, soft
}

HIDEOUT_ROOMS = [
    ("the lookout post", ["cutthroat"]),
    ("the common room", ["cutthroat", "archer"]),
    ("the boss's den", ["bruiser", "cutthroat"]),
]


def make_bandit(kind: str, n: int, rng: random.Random) -> Entity:
    # Bandits arm from the same common-weapon table as starting heroes
    # (50% crude / 45% soldier's arms / 5% heavy) -- always a specific named
    # weapon, so the logs read "Cutthroat 2's dagger", never "a crude weapon".
    dex, str_, sta, hp = BANDIT_TYPES[kind]
    return Entity(name=f"{kind.capitalize()} {n}", dex=dex, str_=str_,
                  sta=sta, max_hp=hp, weapon=random_common_weapon(rng))


def bandit_line(e: Entity) -> str:
    wpn = e.weapon.name if e.weapon else "unarmed"
    return (f"{e.name}: DEX {e.dex}  STR {e.str_}  STA {e.sta}  "
            f"HP {e.hp}/{e.max_hp}  ({wpn})")


def run_hideout(party: list[Entity], clock: Clock, purse: Purse,
                rng: random.Random, log: list[str],
                verbose_rosters: bool = True) -> None:
    """The hideout run, mirroring rpg.run_dungeon (kept in sync with its flow,
    including the pause/retreat policy -- unlike the barrow's grave-bound
    skeletons, bandits DO give chase, so a hideout retreat can fail).
    Importable so bench_training.py can batch it."""
    count = 0
    cleared_all = True
    room_i = 0
    attempts = 0
    held_over = None    # survivors of a room the party fled
    while room_i < len(HIDEOUT_ROOMS):
        room_name, roster = HIDEOUT_ROOMS[room_i]
        living = [h for h in party if not h.dead]
        if not living:
            cleared_all = False
            break

        log.append("")
        if held_over is None:
            attempts = 1
            log.append(f"=== Room {room_i + 1}: {room_name} "
                       f"({len(roster)} bandits) ===")
            bandits = []
            for kind in roster:
                count += 1
                bandits.append(make_bandit(kind, count, rng))
            if verbose_rosters:
                for b in bandits:
                    log.append("  " + bandit_line(b))
        else:
            attempts += 1
            bandits = held_over
            held_over = None
            standing = sum(1 for b in bandits if b.alive)
            log.append(f"=== Room {room_i + 1}: {room_name}, again -- "
                       f"{standing} bandit(s) still hold it ===")
        for h in living:
            start_fight(h, log)

        result = sim_fight(living, bandits, rng, log)

        if party_wiped(party, log):
            cleared_all = False
            break
        if result == "fled":
            if attempts >= SIM_MAX_ROOM_ATTEMPTS:
                log.append("  The party has had enough -- "
                           "the hideout is left be.")
                cleared_all = False
                break
            day_before = clock.day
            survivors = [h for h in party if h.alive]
            if not short_rest(survivors, clock, log):
                long_rest(party, clock, log)
            auto_use_potions_on_rest([h for h in party if h.alive], log)
            held_over = refresh_foes_after_retreat(
                bandits, clock.day - day_before)
            continue    # the same room, again
        if any(b.alive for b in bandits):
            # Unresolved (the fight staggered apart): no award, no clear.
            log.append("  The room is not cleared -- the party pulls back.")
            cleared_all = False
            break

        award_xp(party, BANDIT_ENCOUNTER_XP, log, "encounter")
        roll_loot(party, purse, rng, log)

        survivors = [h for h in party if h.alive]
        if survivors:
            log.append(f"  Room cleared. {len(survivors)} still standing.")
            short_rest(survivors, clock, log)
            auto_use_potions_on_rest(survivors, log)  # batch sim: sensible party
        room_i += 1

    if cleared_all and any(not h.dead for h in party):
        award_quest(party, purse, BANDIT_QUEST_GOLD, BANDIT_QUEST_XP,
                    log, "the hideout is broken")
        for h in party:
            if not h.dead:
                train_combat(h, log)    # sim policy: auto-spend on training


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--training", type=int, default=0,
                    help="start the party at this combat-training rank")
    args = ap.parse_args()
    rng = random.Random(args.seed)

    party = make_party(rng)
    for h in party:
        h.training = args.training
    clock = Clock()
    purse = Purse()
    log = ["The party slips into the bandit hideout:"]
    for h in party:
        log.append("  " + stat_line(h))

    run_hideout(party, clock, purse, rng, log)

    log.append("")
    dead = [h for h in party if h.dead]
    alive = [h for h in party if not h.dead]
    log.append(f"OUTCOME: {outcome(party)} of the party died. "
               f"Purse: {purse.gold} gold.")
    if dead:
        log.append("  Fallen:   " + ", ".join(h.name for h in dead))
    if alive:
        log.append("  Survived: " + ", ".join(
            f"{h.name} (L{h.level}, HP {h.hp}/{h.max_hp}, "
            f"Power {h.cur_power}/{h.power}, STA {h.cur_sta}/{h.sta})"
            for h in alive))

    print("\n".join(log))


if __name__ == "__main__":
    main()
