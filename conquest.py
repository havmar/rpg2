"""Conquest -- the player's own domain layer, slice 1 (2026-07-27).

Plan.md's "conquest ticking" made real: the player can TAKE a settlement,
hold it, and bleed it for tribute. The design calls settled in the
2026-07-27 session (designlog):

- **The settlement is the unit of ownership.** No provinces, no tiles: the
  map stays a list, ownership is a tag on the settlement (`[YOURS]`).
- **The garrison fight is the conquest.** `conquer` builds a garrison job
  at the settlement's GARRISON LEVEL -- rolled once per settlement, stable
  across the save (village 3-5, town 6-10, capital 11-15), so the geography
  of difficulty is fixed terrain the player reads and routes around, like
  the board's straight levels. Win the last room and the tag flips. The
  defender is a named face over a budget-honest roster -- a display name
  over the strongest slot, stats never fork on a skin.
- **Conquest is dark work.** Every XP a garrison job pays is sin, and
  each holding RAISES THE HEAT FLOOR by one step: holding land is standing
  wickedness, and the law comes collecting whether or not the party sins
  again. The strategy layer is the heat machinery the game already has.
- **Holding costs levies, not heroes.** Party members are freely rehired,
  so a garrison is an ARMY resource: one number per holding, bought with
  silver (`garrison N`), never entering the combat engine. Raids strike
  while the party is elsewhere; the garrison absorbs them or the holding
  falls back to the crown. Numbers against numbers -- the engine only ever
  sees the party's own fights.
- **Tribute is the income.** Accrues per held day, collected when the party
  stands in any of its holdings. A holding that falls loses its uncollected
  chest.
The sims never import this file (karma.py's pattern): state is one plain
dict in the save (`holdings`) plus an `owner` tag on held settlement
records; no bench number can move from it. All knobs are hand-set and
sim-unverified -- tune at the table.

**THE CAMPAIGN SIM (2026-08-22, the medieval world arc's session 5)** lives
here for the same reasons: `roll_campaigns` runs the crown's OWN wars --
the three `worldsim.roll_wars` rolls at worldgen -- on exactly this file's
terms. Numbers against numbers, the garrison authority deciding a siege,
the combat engine never seeing it, ordinary since-stamped states on Tiles
and census slots as the whole output. It never redraws a border and never
ends a war (rules.md's The Rolled Wars add-on).

Run:  python conquest.py [--seed N]   # eyeball dump: every settlement's
                                      # garrison level and one built job
"""
from __future__ import annotations

import argparse
import random

import places
import worldsim
from rpg import quest_xp_total
from quests import (LADDER_POOL, ROOM_SHARES, build_site_rooms,
                    split_encounters, threat_value, new_site, new_room,
                    next_quest_id, settlements)
from places import land_homeland, settlement_tier, stable_seed, slug

# --------------------------------------------------------------------------- #
# The knobs (all hand-set, sim-unverified -- the karma layer's doctrine)
# --------------------------------------------------------------------------- #

# The five census tiers (2026-08-21, the tile economy arc's session 2).
# CITY-GRADE -- metropolis and city -- takes the capital's rows: a great
# city is a crown-scale prize whoever wears the crown. The HAMLET takes the
# village's rows everywhere except TRIBUTE, which halves: a hundred souls
# are barely worth holding, and the ledger should say so.
GARRISON_BANDS = {          # the garrison level rolled ONCE per settlement,
    "hamlet": (3, 5),       # stable across the save: a contiguous ladder --
    "village": (3, 5),      # villages takeable around L4-5, towns 6-10,
    "town": (6, 10),        # capitals 13-15 ("conquer a country by 15")
    "city": (11, 15),
    "metropolis": (11, 15),
    "capital": (11, 15),
}
CONQUEST_ENCOUNTERS = {     # the job shape scales with the prize: a village
    "hamlet": 1,            # is one hard fight, a capital is the biggest
    "village": 1,           # job shape the game has (the war waves' 3)
    "town": 2,
    "city": 3,
    "metropolis": 3,
    "capital": 3,
}
TRIBUTE_PER_DAY = {         # silver per held day, collected at the party's
    "hamlet": 1,            # holdings; deliberately small next to quest
    "village": 3,           # pay -- tribute is a trickle, not a wage
    "town": 8,
    "city": 20,
    "metropolis": 20,
    "capital": 20,
}
PLUNDER_MULT = 10           # the keep's strongbox on the day it falls:
                            # this many days of tribute, paid as the
                            # conquest job's silver (the dark premium rides
                            # on top like any dark work)
GARRISON_HIRE_COST = 5      # silver per levy head (`garrison N`)
GARRISON_CAP = {            # how many levies a holding can quarter
    "hamlet": 12,
    "village": 12,
    "town": 24,
    "city": 48,
    "metropolis": 48,
    "capital": 48,
}
RAID_CHANCE_PER_DAY = 0.06  # per holding per elapsed day (lazy roll, at
                            # most one raid per holding per check)
RAID_STRENGTH = {           # heads in a crown raid: bigger prizes draw
    "hamlet": (2, 6),       # bigger columns. A FULL garrison always
    "village": (2, 6),      # repels the worst raid its tier rolls
    "town": (5, 12),
    "city": (10, 24),
    "metropolis": (10, 24),
    "capital": (10, 24),
}
RAID_GARRISON_LOSS = 2      # a repelled raid costs the garrison strength
                            # // this many heads (walls help the defender)
HOLDING_HEAT_STEP = 1       # each holding raises the heat floor this much
                            # (capped by karma.HEAT_CAP at the call site):
                            # holding land is standing wickedness

# The named defender's role, by country (writing.md: role first,
# CRPG vocabulary). A display name over the strongest final-room slot --
# stats never fork.
DEFENDER_ROLES = {
    "phyrascia": "castellan",
    "seraptania": "castellan",
    "teutonia": "captain of the town watch",
    "vellisclavia": "voivode of the garrison",
    "thule": "hall-captain",
    "byzantium": "captain of the walls",
    "andalusia": "keeper of the gate",
    "umaia": "captain of the guard",
    "tergal": "war-chief of the garrison",
}

_ROOM_ROLES = ("the outer wall", "the gatehouse", "the keep")

# --------------------------------------------------------------------------- #
# The garrison (fixed terrain: rolled once, stable across the save)
# --------------------------------------------------------------------------- #

def garrison_level(world: dict, settlement: dict) -> int:
    """The settlement's garrison level -- stable-seeded off the world seed
    and the settlement id, so it never rerolls: difficulty is geography."""
    lo, hi = GARRISON_BANDS[settlement_tier(settlement)]
    rng = random.Random(stable_seed(world.get("seed"), settlement["id"],
                                    "garrison-level", 0))
    return rng.randint(lo, hi)


def garrison_pool(homeland: str) -> tuple[str, ...]:
    """The shared calibrated garrison ladder for a known homeland."""
    if homeland not in DEFENDER_ROLES:
        raise KeyError(f"unknown homeland: {homeland}")
    return LADDER_POOL


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
    homeland = land_homeland(world, settlement["land"])
    tier = settlement_tier(settlement)
    encounters = CONQUEST_ENCOUNTERS[tier]
    pool = garrison_pool(homeland)
    qid = next_quest_id(world)
    name = settlement["name"]
    quest = {
        "id": qid,
        "name": f"Take {name}",
        "desc": (f"{name} can be taken. Break the garrison at the keep "
                 f"and the {tier} is yours. The crown "
                 f"will not forgive it."),
        "origin": settlement["key"],
        "level": level,
        "skins": {},
        "sites": [], "site_count": 1,
        "encounters": encounters,
        "xp_total": quest_xp_total(level, encounters),
        # The strongbox: the one-day sack, in days of tribute. The dark
        # premium rides on top at the turn-in like any dark work.
        "silver_total": PLUNDER_MULT * TRIBUTE_PER_DAY[tier],
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
    site_id = f"{settlement['id']}/site/garrison-{qid}"
    new_site(world, settlement["key"], site_id, "the garrison keep", level,
             quest=qid, template="tower", domain="built")
    for rn, kinds in rooms:
        new_room(world, site_id, f"{site_id}/{slug(rn)}", rn, list(kinds),
                 quest=qid)
    quest["sites"].append(site_id)
    used = {n["name"] for n in world.get("npcs", [])}
    defender = make_npc(rng, homeland, DEFENDER_ROLES[homeland],
                        used_names=used)
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
            f"  Tribute: {TRIBUTE_PER_DAY[settlement_tier(settlement)]} g/day, "
            f"collected when the party stands in a holding.",
            f"  It is held by levies, not luck: `garrison N` buys "
            f"{GARRISON_HIRE_COST}s-a-head guards (cap "
            f"{GARRISON_CAP[settlement_tier(settlement)]}). An unguarded "
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
        subtype = settlement_tier(world["areas"][key])
        total += (day - rec["last_tribute_day"]) * TRIBUTE_PER_DAY[subtype]
    return total


def collect_tribute(world: dict, holdings: dict, day: int) -> int:
    """Sweep every holding's accrued tribute (the party stands in one of
    its holdings -- the stewards bring the chests). Returns the silver."""
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
        strength = rng.randint(*RAID_STRENGTH[settlement_tier(area)])
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


def heat_floor(n_holdings: int) -> int:
    """What the flag alone keeps hot (capped by karma.HEAT_CAP at the call
    site). Zero holdings = the old game exactly."""
    return HOLDING_HEAT_STEP * n_holdings


# --------------------------------------------------------------------------- #
# THE CAMPAIGN SIM (2026-08-22, the medieval world arc's session 5)
# --------------------------------------------------------------------------- #
# The crown's wars, on the same terms as the crown's raids above: numbers
# against numbers, the garrison authority doing the deciding, and the combat
# engine never seeing any of it. `worldsim.roll_wars` rolls the three wars at
# worldgen; this is what makes their fronts LOOK alive between them.
#
# What it does: every WAR_PULSE days each standing war rolls ONE event on its
# posture's weights and writes an ordinary since-stamped STATE onto a theater
# Tile or one of the census slots standing on it. What it never does
# (rules.md's The Rolled Wars add-on states these as law): change a Tile's
# country, touch a board, a quest, the party's holdings or a recruit pool, or
# END a war. Occupation gates nothing -- it is a banner on the war record and
# a line on the Tile's page.

WAR_PULSE = 3               # days between one war's event rolls
OCCUPIED_CAP = 2            # settlements one war may hold at a time
SCAR_CAP = 6                # standing temporary states one war may have on
                            # the map; the oldest is cleared to make room

EVENT_WEIGHTS = {           # what a war of each posture does with a pulse
    "invasion": (("lull", 45), ("raid", 25), ("army", 10),
                 ("battle", 10), ("siege", 10)),
    "raiding": (("lull", 55), ("raid", 40), ("siege", 5)),
}
EVENT_STATES = {"raid": "war-raided", "army": "war-camp",
                "battle": "battlefield"}
SCAR_DAYS = {               # how long each mark stands. `occupied` is not
    "war-raided": 30,       # here: it is permanent, and capped by count
    "war-camp": 10,
    "battlefield": 60,
    "under-siege": 12,
    "sacked": 90,
}
SIEGE_STRENGTH = {          # the besieging column's heads, by the prize's
    "hamlet": (1, 6),       # tier, rolled against `garrison_level`. Each
    "village": (1, 6),      # band straddles its garrison band, so a town
    "town": (3, 12),        # falls about half the time and a great city
    "city": (7, 17),        # rather less
    "metropolis": (7, 17),
    "capital": (7, 17),
}


def slot_garrison_level(world: dict, slot: dict) -> int:
    """The garrison a census SLOT fields -- the same number
    `garrison_level` gives its Area once anybody materializes it, because
    it is asked under the Area id the slot will wear
    (`places.slot_area_id`). The campaign sim besieges towns nobody has
    walked into, so it cannot wait for the Area to exist."""
    return garrison_level(world, {"id": places.slot_area_id(slot),
                                  "subtype": slot["tier"],
                                  "capital": slot["capital"]})


def _scar_place(world: dict, scar: dict) -> dict:
    return (world["tiles"][scar["place"]] if scar["kind"] == "tile"
            else world["settlement_slots"][scar["place"]])


def _drop_scar(world: dict, war: dict, scar: dict, day: int) -> None:
    """Take one mark out of a war's ledger, and off the map ONLY once no
    war's ledger books it any more. Theaters overlap (the Long War and the
    raiding season share four coast tiles) and both wars pulse on the same
    three-day grid, while the map keeps ONE state record per place and
    word: as long as any war still books the mark -- laid earlier, later,
    or on the very same day -- clearing the shared record would cut that
    war's mark short."""
    war["scars"].remove(scar)
    if any(s["place"] == scar["place"] and s["state"] == scar["state"]
           for w in world["wars"] for s in w["scars"]):
        return
    places.clear_state(world, _scar_place(world, scar), scar["state"],
                       day=day)


def _clear_expired(world: dict, war: dict, day: int) -> None:
    """The sim cleans up after itself: every mark whose days are spent goes
    off the map when the war next rolls."""
    for scar in list(war["scars"]):
        if day >= scar["until"]:
            _drop_scar(world, war, scar, day)


def _stamp(world: dict, war: dict, kind: str, place: dict, state_id: str,
           day: int, who: str | None = None) -> dict:
    """Write one war mark onto a Tile or a slot, day-stamped, and book it in
    the war's own scar ledger so it can expire and be counted. A mark laid
    twice on one place is RE-DATED rather than doubled."""
    state = places.replace_state(world, place, state_id, state_id, day=day)
    if who is not None:
        state["who"] = who
    if state_id not in SCAR_DAYS:       # `occupied`: permanent, capped by
        return state                    # OCCUPIED_CAP instead
    for scar in list(war["scars"]):
        if scar["place"] == place["id"] and scar["state"] == state_id:
            war["scars"].remove(scar)
    war["scars"].append({"kind": kind, "place": place["id"],
                         "state": state_id, "until": day + SCAR_DAYS[state_id]})
    while len(war["scars"]) > SCAR_CAP:
        _drop_scar(world, war, war["scars"][0], day)
    return state


def _event(rng: random.Random, posture: str) -> str:
    table = EVENT_WEIGHTS[posture]
    return rng.choices([row[0] for row in table],
                       [row[1] for row in table])[0]


def _news(world: dict, war: dict, day: int, line: str) -> None:
    """One line, to both sides. A war is heard about in every country
    fighting it, and nowhere else -- word travels within a land."""
    for polity in war["attackers"] + war["defenders"]:
        worldsim.post_news(world, polity, day, f"{war['name']}: {line}")


def _attacker_name(world: dict, war: dict) -> str:
    return world["lands"][war["attackers"][0]]["name"]


def _theater_slots(world: dict, war: dict) -> list[dict]:
    return [world["settlement_slots"][sid] for tid in war["theater"]
            for sid in world["tiles"][tid]["settlement_slots"]]


def _siege(world: dict, war: dict, day: int, rng: random.Random) -> None:
    """A column sits down in front of a theater town, and the garrison
    authority decides what happens: `garrison_level` against a strength
    roll on the prize's own band. The town falls and is sacked -- and, while
    the war holds fewer than OCCUPIED_CAP, occupied with the occupier named
    -- or the siege stands its twelve days and lifts."""
    slots = _theater_slots(world, war)
    if not slots:                       # a theater of empty country: the
        _mark(world, war, day, rng, "raid")          # column burns it instead
        return
    slot = rng.choice(slots)
    tile = world["tiles"][slot["tile"]]
    area = world["areas"].get(slot["area"]) if slot["area"] else None
    who = area["name"] if area is not None and area.get("known") else None
    # A settlement the party has met is named; one it has not is its tier
    # standing on a Tile the DM can find. Never both -- a town on its own
    # named Tile would otherwise read "Jerusalem (Jerusalem (R16C27))".
    where = (f"{who} ({places.tile_coordinate(tile['row'], tile['column'])})"
             if who else f"a {slot['tier']} at {places.tile_label(tile)}")
    garrison = slot_garrison_level(world, slot)
    strength = rng.randint(*SIEGE_STRENGTH[places.slot_tier(slot)])
    if strength < garrison:
        _stamp(world, war, "slot", slot, "under-siege", day)
        _news(world, war, day,
              f"{_attacker_name(world, war)}'s army sits before {where}.")
        return
    _stamp(world, war, "slot", slot, "sacked", day)
    line = f"The walls are broken. {where} is taken and sacked."
    if (slot["id"] not in war["occupied"]
            and len(war["occupied"]) < OCCUPIED_CAP):
        _stamp(world, war, "slot", slot, "occupied", day,
               who=_attacker_name(world, war))
        war["occupied"].append(slot["id"])
        line += f" {_attacker_name(world, war)} holds it."
    _news(world, war, day, line)


def _mark(world: dict, war: dict, day: int, rng: random.Random,
          event: str) -> None:
    """The three marks a war leaves on open ground: a burned countryside, an
    army sitting on it, and the field a battle was fought over."""
    tile = world["tiles"][rng.choice(war["theater"])]
    state_id = EVENT_STATES[event]
    _stamp(world, war, "tile", tile, state_id, day)
    where = places.tile_label(tile)
    who = _attacker_name(world, war)
    line = {"raid": f"{who}'s riders have burned the country at {where}.",
            "army": f"An army of {who} is camped at {where}.",
            "battle": f"A battle was fought at {where}. Both sides claim "
                      f"it."}[event]
    _news(world, war, day, line)


def _pulse(world: dict, war: dict, day: int) -> None:
    rng = random.Random(stable_seed(world.get("seed"), war["key"],
                                    "campaign", day))
    _clear_expired(world, war, day)
    event = _event(rng, war["posture"])
    if event == "lull":
        return              # a quiet three days says nothing and marks
                            # nothing: it is what a smouldering front does
    if event == "siege":
        _siege(world, war, day, rng)
    else:
        _mark(world, war, day, rng, event)


def roll_campaigns(world: dict, day: int) -> None:
    """Bring every standing war up to `day`. Lazy, day-stepped and seeded
    per war per day, so catching up thirty days at an arrival gives exactly
    the front that rolling them live would have -- the world layer's own
    contract, applied to the war.

    Driven from the same day-settling seam as `conquest_news`. The wars
    advance TOGETHER, one day at a time -- never one war across the whole
    span while the others stand still -- because theaters overlap and the
    map keeps one state record per place and word: a war catching up
    against another war's finished ledger would lay and clear shared marks
    out of time order, and catching up would stop equalling living
    through it exactly where the fronts touch."""
    wars = world["wars"]
    while any(war["rolled_day"] < day for war in wars):
        for war in wars:
            if war["rolled_day"] < day:
                today = war["rolled_day"] + 1
                if today % WAR_PULSE == 0:
                    _pulse(world, war, today)
                war["rolled_day"] = today


# --------------------------------------------------------------------------- #
# Readouts
# --------------------------------------------------------------------------- #

def holdings_lines(world: dict, holdings: dict, day: int) -> list[str]:
    if not holdings:
        return []
    lines = ["-- your holdings --"]
    for key, rec in sorted(holdings.items()):
        area = world["areas"][key]
        subtype = settlement_tier(area)
        due = (day - rec["last_tribute_day"]) * TRIBUTE_PER_DAY[subtype]
        lines.append(f"  {area['name']} ({subtype}) -- garrison "
                     f"{rec['garrison']}/{GARRISON_CAP[subtype]}, "
                     f"tribute {TRIBUTE_PER_DAY[subtype]} g/day"
                     + (f" ({due}s waiting)" if due else ""))
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
        tier = settlement_tier(s)
        print(f"  {s['name']:14} {tier:8} "
              f"L{garrison_level(world, s):>2}  "
              f"({CONQUEST_ENCOUNTERS[tier]} fight(s), "
              f"tribute {TRIBUTE_PER_DAY[tier]} g/day)")
    target = next(s for s in settlements(world)
                  if s["subtype"] == "village")
    quest = build_conquest_quest(world, target, rng)
    print(f"\nSample conquest job at {target['name']}:")
    print(f"  [{quest['id']}] L{quest['level']} {quest['name']} -- "
          f"{quest['desc']}")
    site = world["sites"][quest["sites"][0]]
    print(f"  boss: {site['boss']['display']} "
          f"(over the {site['boss']['kind']} row)")
    print(f"  pay: {quest['xp_total']} xp (all sin), "
          f"{quest['silver_total']}s strongbox")


if __name__ == "__main__":
    main()
