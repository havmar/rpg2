"""One-off scenario: a bandit hideout. Imports the engine from rpg.py.

Bandits are competent living fighters (real DEX/STR, and they tire), unlike the
brittle tireless skeletons. Mirrors the dungeon's survival flow: start_fight prep
(revive Down, prep a potion) -> group_combat -> rest. Prints both sides' stats.
"""

import argparse
import random

from rpg import (Entity, make_party, group_combat, stat_line, outcome,
                 start_fight, rest, party_wiped)

# Bandit roster: name, dex, str, sta, hp. No Power/ability/kit -- raw fighters.
BANDIT_TYPES = {
    "cutthroat": (4, 3, 5, 7),   # nimble knife-work
    "bruiser":   (3, 5, 5, 9),   # slow, heavy, durable
    "archer":    (4, 2, 5, 6),   # lands often, soft
}

HIDEOUT_ROOMS = [
    ("the lookout post", ["cutthroat", "cutthroat"]),
    ("the common room", ["bruiser", "cutthroat", "archer"]),
    ("the boss's den", ["bruiser", "bruiser", "cutthroat"]),
]


def make_bandit(kind: str, n: int) -> Entity:
    dex, str_, sta, hp = BANDIT_TYPES[kind]
    return Entity(name=f"{kind.capitalize()} {n}", dex=dex, str_=str_,
                  sta=sta, max_hp=hp)


def bandit_line(e: Entity) -> str:
    return (f"{e.name}: DEX {e.dex}  STR {e.str_}  STA {e.sta}  "
            f"HP {e.hp}/{e.max_hp}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    party = make_party(rng)
    log = ["The party slips into the bandit hideout:"]
    for h in party:
        log.append("  " + stat_line(h))

    count = 0
    for i, (room_name, roster) in enumerate(HIDEOUT_ROOMS, start=1):
        living = [h for h in party if not h.dead]
        if not living:
            break

        log.append("")
        log.append(f"=== Room {i}: {room_name} ({len(roster)} bandits) ===")
        for h in living:
            start_fight(h, log)

        bandits = []
        for kind in roster:
            count += 1
            bandits.append(make_bandit(kind, count))
        for b in bandits:
            log.append("  " + bandit_line(b))

        group_combat(living, bandits, rng, log)

        if party_wiped(party, log):
            break

        survivors = [h for h in party if h.alive]
        if survivors:
            log.append(f"  Room cleared. {len(survivors)} still standing.")
            rest(survivors, log)

    log.append("")
    dead = [h for h in party if h.dead]
    alive = [h for h in party if not h.dead]
    log.append(f"OUTCOME: {outcome(party)} of the party died.")
    if dead:
        log.append("  Fallen:   " + ", ".join(h.name for h in dead))
    if alive:
        log.append("  Survived: " + ", ".join(
            f"{h.name} (HP {h.hp}/{h.max_hp}, Power {h.cur_power}/{h.power}, "
            f"STA {h.cur_sta}/{h.sta})" for h in alive))

    print("\n".join(log))


if __name__ == "__main__":
    main()
