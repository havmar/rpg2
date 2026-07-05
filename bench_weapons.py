"""Weapons benchmark: are the quality weapons SUITED rather than RANKED?

The weapons test criterion (rules.md, "Weapons"): each weapon should be build-*suited*, never
simply better -- no single weapon may top every build in every situation.
Two situations per frame, because the weapons split along that axis too:

- duel:  1v1 vs a fixed reference (a balanced frame with a shortsword, i.e.
         the engine's old implicit baseline). The rapier's home turf.
- swarm: 1v3 skeletons, fresh. Numbers pressing a lone fighter -- the
         zweihander's home turf (one blow per mook, but no parrying a girder).

Read it row-wise: the best duel weapon should change with the frame, the
swarm column should reorder it again, and the wooden staff should trail
everywhere -- it's a healer's weapon, priced in combat stats on purpose.

Pure weapon test: no abilities, no potions, no training, same HP both sides.
This bench also documents WHY the zweihander does not cost 2 STA per swing:
every 2-STA variant tested was strictly worst-in-class (Spent is lethal, so
half the swing budget loses more than any severity bonus buys back).

Run:  python bench_weapons.py [--trials N]
"""

import argparse
import random

from rpg import Entity, WEAPONS, group_combat
from sites import make_foe

# Stat frames spanning the hero roll ranges (DEX/STR 3-6, STA 5-8; STA's range
# sits 2 higher -- see rules.md). HP fixed so only stats and steel differ.
FRAMES = {
    "precise  (DEX 6/STR 3/STA 6)": dict(dex=6, str_=3, sta=6),
    "powerful (DEX 3/STR 6/STA 6)": dict(dex=3, str_=6, sta=6),
    "steady   (DEX 4/STR 4/STA 8)": dict(dex=4, str_=4, sta=8),
    "balanced (DEX 5/STR 5/STA 6)": dict(dex=5, str_=5, sta=6),
}
HP = 10

WEAPON_LIST = ["shortsword", "rapier", "katana", "zweihander", "wooden staff"]

REFERENCE = dict(dex=4, str_=4, sta=7)      # the sparring partner: middling
REFERENCE_WEAPON = "shortsword"             # everything, baseline steel
SWARM_SIZE = 3


def duel(frame: dict, weapon_name: str, rng: random.Random) -> bool:
    """One 1v1 to the finish. True if the frame's fighter wins (reference
    down or dead; a standstill counts as no win)."""
    a = Entity(name="A", max_hp=HP, weapon=WEAPONS[weapon_name], **frame)
    b = Entity(name="B", max_hp=HP, weapon=WEAPONS[REFERENCE_WEAPON],
               **REFERENCE)
    group_combat([a], [b], rng, log=[])
    return a.alive and not b.alive


def swarm(frame: dict, weapon_name: str, rng: random.Random) -> bool:
    """One fighter vs SWARM_SIZE fresh skeletons. True if all fall."""
    a = Entity(name="A", max_hp=HP, weapon=WEAPONS[weapon_name], **frame)
    foes = [make_foe("skeleton", i + 1, rng) for i in range(SWARM_SIZE)]
    group_combat([a], foes, rng, log=[])
    return a.alive and not any(f.alive for f in foes)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=4000)
    args = ap.parse_args()

    print(f"duel = 1v1 vs reference (DEX {REFERENCE['dex']}/"
          f"STR {REFERENCE['str_']}/STA {REFERENCE['sta']}, "
          f"{REFERENCE_WEAPON}); swarm = 1v{SWARM_SIZE} skeletons.")
    print(f"{args.trials} trials per cell; win%.\n")
    header = f"{'frame':<30}" + "".join(f"{w:>16}" for w in WEAPON_LIST)
    print(header)
    print(f"{'':<30}" + "".join(f"{'duel/swarm':>16}" for _ in WEAPON_LIST))
    for frame_name, frame in FRAMES.items():
        row = f"{frame_name:<30}"
        best_duel, best_d = "", -1.0
        best_swarm, best_s = "", -1.0
        for weapon_name in WEAPON_LIST:
            rng = random.Random(4242)
            d = 100 * sum(duel(frame, weapon_name, rng)
                          for _ in range(args.trials)) / args.trials
            rng = random.Random(4243)
            s = 100 * sum(swarm(frame, weapon_name, rng)
                          for _ in range(args.trials)) / args.trials
            row += f"{d:>8.1f}/{s:>6.1f}"
            if d > best_d:
                best_duel, best_d = weapon_name, d
            if s > best_s:
                best_swarm, best_s = weapon_name, s
        print(row)
        print(f"{'':<30}    -> best duel: {best_duel}; "
              f"best swarm: {best_swarm}")
    print("\nSuited, not ranked: the best weapon should change across "
          "frames and situations,\nand no weapon should top every cell.")


if __name__ == "__main__":
    main()
