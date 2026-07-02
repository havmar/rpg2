"""One-off scenario: a bandit hideout. Imports the engine from rpg.py.

Bandits are competent living fighters (real DEX/STR, and they tire), unlike the
brittle tireless skeletons. Mirrors the dungeon's survival flow: start_fight prep
(revive Down, prep a potion) -> group_combat -> rest. Prints both sides' stats.

This is the TOUGH site: rewards pay 3x the skeleton barrow (XP and gold), and a
fresh level-1 party will usually wipe here -- the intended play is to farm the
skeletons for a level or two of combat training first (see bench_training.py
for the numbers). `--training N` starts the party pre-trained to see that jump.
"""

import argparse
import random

from rpg import (Entity, Clock, Purse, make_party, group_combat, stat_line,
                 outcome, start_fight, short_rest, party_wiped, award_xp,
                 award_quest, roll_loot, SKELETON_ENCOUNTER_XP,
                 SKELETON_QUEST_XP, SKELETON_QUEST_GOLD)

# The hideout pays 3x the skeleton site -- tough fights, better wages.
BANDIT_ENCOUNTER_XP = 3 * SKELETON_ENCOUNTER_XP
BANDIT_QUEST_XP = 3 * SKELETON_QUEST_XP
BANDIT_QUEST_GOLD = 3 * SKELETON_QUEST_GOLD

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


def run_hideout(party: list[Entity], clock: Clock, purse: Purse,
                rng: random.Random, log: list[str],
                verbose_rosters: bool = True) -> None:
    """The hideout run, mirroring rpg.run_dungeon (kept in sync with its flow).
    Importable so bench_training.py can batch it."""
    count = 0
    cleared_all = True
    for i, (room_name, roster) in enumerate(HIDEOUT_ROOMS, start=1):
        living = [h for h in party if not h.dead]
        if not living:
            cleared_all = False
            break

        log.append("")
        log.append(f"=== Room {i}: {room_name} ({len(roster)} bandits) ===")
        for h in living:
            start_fight(h, log)

        bandits = []
        for kind in roster:
            count += 1
            bandits.append(make_bandit(kind, count))
        if verbose_rosters:
            for b in bandits:
                log.append("  " + bandit_line(b))

        group_combat(living, bandits, rng, log)

        if party_wiped(party, log):
            cleared_all = False
            break

        award_xp(party, BANDIT_ENCOUNTER_XP, log, "encounter")
        roll_loot(party, purse, rng, log)

        survivors = [h for h in party if h.alive]
        if survivors:
            log.append(f"  Room cleared. {len(survivors)} still standing.")
            short_rest(survivors, clock, log)

    if cleared_all and any(not h.dead for h in party):
        award_quest(party, purse, BANDIT_QUEST_GOLD, BANDIT_QUEST_XP,
                    log, "the hideout is broken")


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
