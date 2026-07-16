"""Ranged-weapons benchmark: is reach an EDGE rather than a win button?

The ranged test criterion (rules.md, the Ranged Combat add-on): distance is
free damage BEFORE a normal melee -- ceil(field/2) shots at most -- so a
ranged card should win its fights by a real but bounded margin on open
ground, and that margin should COLLAPSE with the field (cramped rooms are
where you counter shooters). Two readouts:

- duel-by-field: each ranged card (on the frame that suits it) vs the
  bench_weapons melee reference (a balanced frame with a shortsword), at
  field 0 / ROOM_FIELD / WILD_FIELD. Field 0 forces the card's melee grip
  from round 1 -- the floor every shooter pays for carrying reach; the
  katana row prints alongside as the melee baseline.
- escort: the played shape -- an archer + a katana partner vs a wolf pack
  at WILD_FIELD (does the line protect the bow; does the pack's spare wolf
  slip the press and walk it down).

Pure weapon test: no abilities, no potions, no training, full quivers,
same HP both sides.

Run:  python bench_ranged.py [--trials N]
"""

import argparse
import random

from rpg import (Entity, WEAPONS, HERO_PAIN, group_combat, STARTER_AMMO,
                 AMMO_CAPS, ROOM_FIELD, WILD_FIELD)
from sites import make_foe

HP = 10

# Each card on the frame its aim stat wants (the blunderbuss's whole point
# is needing neither stat, so it gets the leftover frame).
RANGED_FRAMES = {
    "longbow":         dict(dex=5, str_=5, sta=6),   # dex_str aim
    "shortbow":        dict(dex=5, str_=5, sta=6),
    "crossbow":        dict(dex=5, str_=4, sta=6),   # str 4 clears heavy_draw
    "blunderbuss":     dict(dex=3, str_=4, sta=6),   # the low-stat equalizer
    "revolver":        dict(dex=6, str_=3, sta=6),   # wants high DEX
    "throwing knives": dict(dex=6, str_=3, sta=6),
    "sling":           dict(dex=5, str_=3, sta=6),
}
MELEE_BASELINE = ("katana", dict(dex=5, str_=5, sta=6))

REFERENCE = dict(dex=4, str_=4, sta=7)      # bench_weapons' sparring partner
REFERENCE_WEAPON = "shortsword"

FIELDS = (0, ROOM_FIELD, WILD_FIELD)


def full_quiver(weapon_name: str) -> dict[str, int]:
    w = WEAPONS[weapon_name]
    if w.ammo and w.ammo != "power":
        return {w.ammo: AMMO_CAPS[w.ammo]}
    return {}


def shooter(name: str, weapon_name: str, frame: dict,
            power: int = 6) -> Entity:
    return Entity(name=name, max_hp=HP, pain=HERO_PAIN, power=power,
                  weapon=WEAPONS[weapon_name],
                  items=full_quiver(weapon_name), **frame)


def duel(weapon_name: str, frame: dict, field: int,
         rng: random.Random) -> bool:
    a = shooter("A", weapon_name, frame)
    b = Entity(name="B", max_hp=HP, pain=HERO_PAIN,
               weapon=WEAPONS[REFERENCE_WEAPON], **REFERENCE)
    group_combat([a], [b], rng, log=[], field=field)
    return a.alive and not b.alive


def escort(weapon_name: str, frame: dict, rng: random.Random) -> bool:
    """The played shape: archer + katana line vs 3 wolves at WILD_FIELD."""
    a = shooter("A", weapon_name, frame)
    b = Entity(name="B", max_hp=HP, pain=HERO_PAIN,
               weapon=WEAPONS["katana"], **MELEE_BASELINE[1])
    foes = [make_foe("wolf", i + 1, rng) for i in range(3)]
    group_combat([a, b], foes, rng, log=[], field=WILD_FIELD)
    return (a.alive or b.alive) and not any(f.alive for f in foes)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=4000)
    args = ap.parse_args()

    print(f"duel = 1v1 vs reference (DEX {REFERENCE['dex']}/"
          f"STR {REFERENCE['str_']}/STA {REFERENCE['sta']}, "
          f"{REFERENCE_WEAPON}) by opening field; "
          f"escort = +katana partner vs 3 wolves at field {WILD_FIELD}.")
    print(f"{args.trials} trials per cell; win%.\n")
    header = (f"{'card (suited frame)':<28}"
              + "".join(f"{'field ' + str(f):>10}" for f in FIELDS)
              + f"{'escort':>10}")
    print(header)
    rows = list(RANGED_FRAMES.items()) + [
        (MELEE_BASELINE[0], MELEE_BASELINE[1])]
    for weapon_name, frame in rows:
        row = f"{weapon_name:<28}"
        for field in FIELDS:
            rng = random.Random(4242)
            wins = sum(duel(weapon_name, frame, field, rng)
                       for _ in range(args.trials))
            row += f"{100 * wins / args.trials:>10.1f}"
        rng = random.Random(4243)
        wins = sum(escort(weapon_name, frame, rng)
                   for _ in range(args.trials))
        row += f"{100 * wins / args.trials:>10.1f}"
        print(row)
    print("\nReach should read as an EDGE that grows with the field and "
          "dies at the door\n(field 0 is the switched melee grip -- the "
          "price of carrying a shooter's card).")


if __name__ == "__main__":
    main()
