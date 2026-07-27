"""Conquest -- the player's own domain layer, slice 1 (2026-07-27).

Plan.md's "conquest ticking" made real: the player can TAKE a settlement,
hold it, and bleed it for tribute. The design calls settled in the
2026-07-27 session (designlog):

- **The settlement is the unit of ownership.** No provinces, no tiles: the
  map stays a list, ownership is a tag on the settlement (`[YOURS]`), the
  same shape the war's occupation layer already prints.
- **The garrison fight is the conquest.** `conquer` builds a garrison job
  at the settlement's GARRISON LEVEL -- rolled once per settlement, stable
  across the save (village 3-5, town 6-10, capital 11-15), so the geography
  of difficulty is fixed terrain the player reads and routes around, like
  the board's straight levels. Win the last room and the tag flips. The
  defender is a named face over a budget-honest roster (the story layer's
  boss doctrine -- stats never fork on a skin).
- **Conquest is dark work.** Every XP a garrison job pays is bad karma, and
  each holding RAISES THE HEAT FLOOR by one step: holding land is standing
  wickedness, and the law comes collecting whether or not the party sins
  again. The strategy layer is the heat machinery the game already has.
- **Holding costs levies, not heroes.** Party members are freely rehired,
  so a garrison is an ARMY resource: one number per holding, bought with
  gold (`garrison N`), never entering the combat engine. Raids strike
  while the party is elsewhere; the garrison absorbs them or the holding
  falls back to the crown. Numbers against numbers -- the engine only ever
  sees the party's own fights.
- **Tribute is the income.** Accrues per held day, collected when the party
  stands in any of its holdings. A holding that falls loses its uncollected
  chest.
- **The aggressor's yoke outranks the party's flag.** A story-fallen land
  seizes the party's holdings there; retaking them is a fresh conquest.

The sims never import this file (karma.py's pattern): state is one plain
dict in the save (`holdings`) plus an `owner` tag on held settlement
records; no bench number can move from it. All knobs are hand-set and
sim-unverified -- tune at the table.

Run:  python conquest.py [--seed N]   # eyeball dump: every settlement's
                                      # garrison level and one built job
"""
from __future__ import annotations

import argparse
import random

from rpg import quest_xp_total
from quests import (LADDER_POOL, GOBLIN_LADDER_POOL, DWARF_LADDER_POOL,
                    ELF_LADDER_POOL, ROOM_SHARES, build_site_rooms,
                    split_encounters, threat_value, new_site, new_room,
                    next_quest_id, settlements)
from places import land_race, stable_seed, slug

# --------------------------------------------------------------------------- #
# The knobs (all hand-set, sim-unverified -- the karma layer's doctrine)
# --------------------------------------------------------------------------- #

GARRISON_BANDS = {          # the garrison level rolled ONCE per settlement,
    "village": (3, 5),      # stable across the save: a contiguous ladder --
    "town": (6, 10),        # villages takeable around L4-5, towns 6-10,
    "capital": (11, 15),    # capitals 13-15 ("conquer a country by 15")
}
CONQUEST_ENCOUNTERS = {     # the job shape scales with the prize: a village
    "village": 1,           # is one hard fight, a capital is the biggest
    "town": 2,              # job shape the game has (the war waves' 3)
    "capital": 3,
}
TRIBUTE_PER_DAY = {         # gold per held day, collected at the party's
    "village": 3,           # holdings; deliberately small next to quest
    "town": 8,              # pay -- tribute is a trickle, not a wage
    "capital": 20,
}
PLUNDER_MULT = 10           # the keep's strongbox on the day it falls:
                            # this many days of tribute, paid as the
                            # conquest job's gold (the dark premium rides
                            # on top like any dark work)
GARRISON_HIRE_COST = 5      # gold per levy head (`garrison N`)
GARRISON_CAP = {            # how many levies a holding can quarter
    "village": 12,
    "town": 24,
    "capital": 48,
}
RAID_CHANCE_PER_DAY = 0.06  # per holding per elapsed day (lazy roll, at
                            # most one raid per holding per check)
RAID_STRENGTH = {           # heads in a crown raid: bigger prizes draw
    "village": (2, 6),      # bigger columns. A FULL garrison always
    "town": (5, 12),        # repels the worst raid its tier rolls
    "capital": (10, 24),
}
RAID_GARRISON_LOSS = 2      # a repelled raid costs the garrison strength
                            # // this many heads (walls help the defender)
HOLDING_HEAT_STEP = 1       # each holding raises the heat floor this much
                            # (capped by karma.HEAT_CAP at the call site):
                            # holding land is standing wickedness

# The named defender's role, by the land's race (writing.md: role first,
# CRPG vocabulary). A display name over the strongest final-room slot --
# the story layer's boss doctrine, stats never fork.
DEFENDER_ROLES = {
    "human": "castellan",
    "elf": "warden of the walls",
    "dwarf": "gate warden",
    "goblin": "wall-crew boss",
    "orc": "war-chief of the garrison",
}

_ROOM_ROLES = ("the outer wall", "the gatehouse", "the keep")

_LADDERS = {
    "goblin": GOBLIN_LADDER_POOL,
    "dwarf": DWARF_LADDER_POOL,
    "elf": ELF_LADDER_POOL,
}


# --------------------------------------------------------------------------- #
# The garrison (fixed terrain: rolled once, stable across the save)
# --------------------------------------------------------------------------- #

def garrison_level(world: dict, settlement: dict) -> int:
    """The settlement's garrison level -- stable-seeded off the world seed
    and the settlement id, so it never rerolls: difficulty is geography."""
    lo, hi = GARRISON_BANDS[settlement["subtype"]]
    rng = random.Random(stable_seed(world.get("seed"), settlement["id"],
                                    "garrison-level", 0))
    return rng.randint(lo, hi)


def garrison_pool(race: str) -> tuple[str, ...]:
    """A land's garrison fights with its cultural ladder (the same arms
    rule every warband follows)."""
    return _LADDERS.get(race, LADDER_POOL)


# --------------------------------------------------------------------------- #
# The conquest job
# --------------------------------------------------------------------------- #

def build_conquest_quest(world: dict, settlement: dict,
                         rng: random.Random) -> dict:
    """Build the garrison job for `conquer`: an ordinary dark quest
    underneath (same schema, same threat math, no clock -- a keep does not
    lapse), one place at the settlement, capped by the named defender."""
    from people import make_npc     # runtime import (people imports quests)
    level = garrison_level(world, settlement)
    race = land_race(world, settlement["land"])
    encounters = CONQUEST_ENCOUNTERS[settlement["subtype"]]
    pool = garrison_pool(race)
    qid = next_quest_id(world)
    name = settlement["name"]
    quest = {
        "id": qid,
        "name": f"Take {name}",
        "desc": (f"{name} can be taken. Break the garrison at the keep "
                 f"and the {settlement['subtype']} is yours. The crown "
                 f"will not forgive it."),
        "origin": settlement["key"],
        "level": level,
        "skins": {},
        "sites": [], "site_count": 1,
        "encounters": encounters,
        "xp_total": quest_xp_total(level, encounters),
        # The strongbox: the one-day sack, in days of tribute. The dark
        # premium rides on top at the turn-in like any dark work.
        "gold_total": PLUNDER_MULT * TRIBUTE_PER_DAY[settlement["subtype"]],
        "next": {"site": 0, "room": 0},
        "status": "open",
        "align": "dark",
        "epilogue": (f"The garrison is broken. {name} is yours. Tribute "
                     f"flows while you hold it. The crown remembers."),
        "conquest": settlement["key"],
    }
    n_rooms = split_encounters(encounters, 1)[0]
    # A one-fight conquest is the keep itself, not the outer wall: the
    # roles are taken from the END of the ladder.
    roles = _ROOM_ROLES[-n_rooms:]
    rooms = build_site_rooms(level, n_rooms, pool, rng, roles,
                             shares=tuple(ROOM_SHARES[encounters]),
                             final_room=True)
    site_id = (f"site/{settlement['land']}/{slug(settlement['name'])}/"
               f"garrison-{qid}")
    new_site(world, settlement["key"], site_id, "the garrison keep", level,
             quest=qid, template="tower", domain="built")
    for rn, kinds in rooms:
        new_room(world, site_id, f"{site_id}/{slug(rn)}", rn, list(kinds),
                 quest=qid)
    quest["sites"].append(site_id)
    used = {n["name"] for n in world.get("npcs", [])}
    defender = make_npc(rng, race, DEFENDER_ROLES[race], used_names=used)
    strongest = max(rooms[-1][1], key=threat_value)
    world["sites"][site_id]["boss"] = {
        "kind": strongest,
        "display": f"{defender['name']}, the {defender['role']}"}
    world["quests"][qid] = quest
    # NOT appended to the settlement's board: a conquest is not posted
    # work -- it exists because the player declared it (`conquer`), and it
    # is taken like a war wave, at the settlement, by id.
    return quest


# --------------------------------------------------------------------------- #
# Holdings -- state lives in the save (`holdings`, a plain dict)
# --------------------------------------------------------------------------- #

def new_holding(day: int) -> dict:
    return {"taken_day": day,
            "garrison": 0,          # levy heads (`garrison N` buys more)
            "last_tribute_day": day,
            "last_raid_day": day}


def take_settlement(world: dict, holdings: dict, settlement: dict,
                    day: int) -> list[str]:
    """Flip the tag: the settlement is the party's. Called when the
    conquest quest completes."""
    holdings[settlement["key"]] = new_holding(day)
    settlement["owner"] = "party"
    return [f"*** {settlement['name'].upper()} IS YOURS. ***",
            f"  Tribute: {TRIBUTE_PER_DAY[settlement['subtype']]} g/day, "
            f"collected when the party stands in a holding.",
            f"  It is held by levies, not luck: `garrison N` buys "
            f"{GARRISON_HIRE_COST}g-a-head guards (cap "
            f"{GARRISON_CAP[settlement['subtype']]}). An unguarded "
            f"holding falls to the first raid.",
            f"  Holding land is standing wickedness: the heat floor "
            f"rises while the flag flies."]


def lose_holding(world: dict, holdings: dict, key: str) -> None:
    holdings.pop(key, None)
    area = world["areas"].get(key)
    if area is not None and area.get("owner") == "party":
        area.pop("owner", None)


def tribute_pending(world: dict, holdings: dict, day: int) -> int:
    total = 0
    for key, rec in holdings.items():
        subtype = world["areas"][key]["subtype"]
        total += (day - rec["last_tribute_day"]) * TRIBUTE_PER_DAY[subtype]
    return total


def collect_tribute(world: dict, holdings: dict, day: int) -> int:
    """Sweep every holding's accrued tribute (the party stands in one of
    its holdings -- the stewards bring the chests). Returns the gold."""
    total = tribute_pending(world, holdings, day)
    for rec in holdings.values():
        rec["last_tribute_day"] = day
    return total


def roll_raids(world: dict, holdings: dict, rng: random.Random, day: int,
               skip_key: str | None = None) -> list[str]:
    """The crown's counterstroke, rolled lazily over the elapsed days (at
    most one raid per holding per check). Numbers against numbers: the
    raid's heads against the garrison's -- the combat engine never sees
    it. The holding where the party stands is skipped: the law prefers to
    retake a keep while the warlord is away (and the party's own fights
    are the posse machinery's job)."""
    lines: list[str] = []
    for key in list(holdings):
        rec = holdings[key]
        days = day - rec.get("last_raid_day", day)
        rec["last_raid_day"] = day
        if key == skip_key or days <= 0:
            continue
        if rng.random() >= 1 - (1 - RAID_CHANCE_PER_DAY) ** days:
            continue
        area = world["areas"][key]
        strength = rng.randint(*RAID_STRENGTH[area["subtype"]])
        g = rec["garrison"]
        if g >= strength:
            loss = strength // RAID_GARRISON_LOSS
            rec["garrison"] = g - loss
            lines.append(f"*** RAID at {area['name']}: the crown sends "
                         f"{strength} heads against your {g} levies -- "
                         f"REPELLED. {loss} levies lost; "
                         f"{rec['garrison']} stand. ***")
        else:
            lose_holding(world, holdings, key)
            lines.append(f"*** RAID at {area['name']}: the crown sends "
                         f"{strength} heads against your {g} levies -- "
                         f"{area['name'].upper()} IS LOST. The uncollected "
                         f"tribute goes with it. ***")
    return lines


def seize_by_occupation(world: dict, holdings: dict,
                        story: dict | None) -> list[str]:
    """The aggressor's yoke outranks the party's flag: a story-fallen land
    takes the party's holdings with it. Retaking one is a fresh
    conquest."""
    fallen = story.get("fallen") if story else None
    if not fallen:
        return []
    lines = []
    for key in list(holdings):
        area = world["areas"][key]
        if area["land"] == fallen:
            lose_holding(world, holdings, key)
            lines.append(f"*** The yoke takes {area['name']} -- your "
                         f"garrison is scattered with the rest. ***")
    return lines


def heat_floor(n_holdings: int) -> int:
    """What the flag alone keeps hot (capped by karma.HEAT_CAP at the call
    site). Zero holdings = the old game exactly."""
    return HOLDING_HEAT_STEP * n_holdings


# --------------------------------------------------------------------------- #
# Readouts
# --------------------------------------------------------------------------- #

def holdings_lines(world: dict, holdings: dict, day: int) -> list[str]:
    if not holdings:
        return []
    lines = ["-- your holdings --"]
    for key, rec in sorted(holdings.items()):
        area = world["areas"][key]
        subtype = area["subtype"]
        due = (day - rec["last_tribute_day"]) * TRIBUTE_PER_DAY[subtype]
        lines.append(f"  {area['name']} ({subtype}) -- garrison "
                     f"{rec['garrison']}/{GARRISON_CAP[subtype]}, "
                     f"tribute {TRIBUTE_PER_DAY[subtype]} g/day"
                     + (f" ({due}g waiting)" if due else ""))
    return lines


# --------------------------------------------------------------------------- #
# Demo (the designer's eyeball check)
# --------------------------------------------------------------------------- #

def main() -> None:
    from quests import generate_world
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    world = generate_world(seed=args.seed)
    print("Garrison levels (stable per settlement):")
    for s in settlements(world):
        print(f"  {s['name']:14} {s['subtype']:8} "
              f"L{garrison_level(world, s):>2}  "
              f"({CONQUEST_ENCOUNTERS[s['subtype']]} fight(s), "
              f"tribute {TRIBUTE_PER_DAY[s['subtype']]} g/day)")
    target = next(s for s in settlements(world)
                  if s["subtype"] == "village")
    quest = build_conquest_quest(world, target, rng)
    print(f"\nSample conquest job at {target['name']}:")
    print(f"  [{quest['id']}] L{quest['level']} {quest['name']} -- "
          f"{quest['desc']}")
    site = world["sites"][quest["sites"][0]]
    print(f"  boss: {site['boss']['display']} "
          f"(over the {site['boss']['kind']} row)")
    print(f"  pay: {quest['xp_total']} xp (all bad karma), "
          f"{quest['gold_total']}g strongbox")


if __name__ == "__main__":
    main()
