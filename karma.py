"""Karma & heat -- the villain layer's first slice (2026-07-19).

The design (rules.md, the Karma & Heat add-on, has the full spine): the
game learns to be PLAYED WICKEDLY without forking into a second ruleset.
XP is bucketed by the ALIGNMENT of the work that paid it -- dark work
accrues BAD KARMA, honest work burns it 1:1 (penance) -- and the party's
current bad karma sets its HEAT: how many levels above the party the
world's retribution arrives. Zero heat is the old game exactly; the whole
layer is inert until the player takes dark work.

- **Heat is the throttle.** One at-level dark quest is ~one heat step
  (KARMA_HEAT_STEP * level bad karma per step; a level-L quest quotes
  ~100L XP). The player pumps difficulty by sinning and bleeds it off by
  honest work -- difficulty selection by consequence, not by board-reading.
- **Punishment is people, not weather.** At heat >= 1, time-spaced posses
  (cooldown + a chance roll at arrivals and nights) hunt the party at
  party level + heat: the Watch first, then bounty hunters, the crown's
  huntsmen, finally heroes of the realm -- all budget-honest ladder
  rosters wearing lawful display names, led by a generated face. Cutting
  them down pays XP like any road fight, and ALL of it is bad karma: the
  ratchet is the point.
- **Dark quests are the same machinery flagged.** Templates below ride
  build_quest/attach_giver unchanged; they are rolled LAZILY per
  settlement day (`board --dark`, the recruits-on-request pattern), so
  worldgen, the coverage assert, and every bench never see them. Crime
  pays a gold premium (quests.DARK_GOLD_MULT); its XP is the liability.
- **The fights stay honest.** A dark quest's foes are always people/things
  that fight back (guards, militia, an aggrieved parent dire wolf); the
  wickedness itself -- the theft, the arson, the kicked puppy -- is
  narration (dm.md owns the register: cartoonish, never grim).

The sims never import this file. State is one plain dict in the save
(`karma`): current bad karma, the lifetime ledgers, the punishment day
stamp, and the last posse leader's name (the future nemesis seed).

Run:  python karma.py [--seed N]   # sample dark boards and posses
"""

from __future__ import annotations

import argparse
import random

from rpg import LEVEL_CAP
from quests import (LADDER_POOL, WOLF_POOL, UNDEAD_POOL, CASTER_POOL,
                    build_quest, attach_giver, template_band, build_room,
                    room_budget)

# --------------------------------------------------------------------------- #
# Constants (the villain layer's knobs)
# --------------------------------------------------------------------------- #

KARMA_HEAT_STEP = 100   # bad karma per heat step is this * the PC's level:
                        # a level-L quest quotes ~100L XP (site_xp_total),
                        # so ONE at-level dark quest ~ one heat step, and
                        # one honest at-level quest ~ one step of penance
HEAT_CAP = 3            # posses arrive at party level + heat, capped: +3
                        # is already a truly dangerous fight (the punching-
                        # up measurements); past it the number is noise
PUNISH_COOLDOWN_DAYS = 2   # the law is never instantaneous: at least this
                           # many days between posses ("a bit time spaced")
PUNISH_CHANCE = 0.6     # per eligible stop (arrival / settlement night /
                        # wilds camp) once the cooldown has passed
DARK_JOBS_PER_DAY = 3   # the shadow board's size, rolled per settlement day

# --------------------------------------------------------------------------- #
# Karma state (one plain dict in the save)
# --------------------------------------------------------------------------- #


def new_karma() -> dict:
    return {"bad": 0,           # current, burnable -- drives heat
            "bad_total": 0,     # lifetime wickedness (never decreases --
                                # the player's badness level, for titles
                                # and the DM's memory)
            "good_total": 0,    # lifetime penance (record only)
            "last_punish_day": -99,
            "last_leader": None}   # the last posse's named leader -- the
                                   # nemesis seed (persistence is plan.md)


def heat(karma: dict, pc_level: int) -> int:
    """Current heat: how many levels above the party retribution arrives.
    Derived, never stored -- bad karma over KARMA_HEAT_STEP * level, so
    the same sins cool as the party's legend grows (the Watch that hunts
    a level-2 puppy-kicker has better sense at level 10)."""
    step = KARMA_HEAT_STEP * max(1, pc_level)
    return min(HEAT_CAP, karma["bad"] // step)


def record_karma(karma: dict, xp: int, align: str, log: list,
                 pc_level: int) -> None:
    """Bucket a QUOTED XP award by the work's alignment: dark work accrues
    bad karma, good work burns it 1:1 (penance -- 'the basic quests delete
    the karma'). Neutral work (the wilds, the hunt) touches nothing.
    Appends the bookkeeping line so the player always sees the meter."""
    if align == "dark" and xp > 0:
        karma["bad"] += xp
        karma["bad_total"] += xp
        log.append(f"    (dark work: +{xp} bad karma -- "
                   f"{karma_line(karma, pc_level)})")
    elif align == "good" and xp > 0:
        karma["good_total"] += xp
        if karma["bad"] > 0:
            burned = min(karma["bad"], xp)
            karma["bad"] -= burned
            log.append(f"    (penance: -{burned} bad karma -- "
                       f"{karma_line(karma, pc_level)})")


def karma_line(karma: dict, pc_level: int) -> str:
    """The one-line meter for tallies and status readouts -- always
    self-contained (current bad karma + what it means)."""
    h = heat(karma, pc_level)
    step = KARMA_HEAT_STEP * max(1, pc_level)
    if h >= 1:
        return (f"bad karma {karma['bad']}; HEAT {h} -- retribution "
                f"hunts {h} level(s) above the party")
    if karma["bad"] > 0:
        return (f"bad karma {karma['bad']}/{step}; heat 0 -- lying low")
    return "clean; heat 0"


# --------------------------------------------------------------------------- #
# Dark quest templates
# --------------------------------------------------------------------------- #
# Race-agnostic on purpose (dark work is cosmopolitan; race-flavored dark
# tables are a later content pass -- plan.md). Same schema as
# quests.TEMPLATES plus `align: "dark"`; the foes are always someone who
# FIGHTS BACK -- guards, militia, the relic's keepers, the puppy's parent
# -- so the engine only ever resolves honest fights and the wickedness
# itself stays narration (dm.md, the villain register).

DARK_TEMPLATES: list[dict] = [
    dict(title="The Puppy on the Doorstep", align="dark",
         desc="A widow's guard-pup keeps fouling the fixer's doorstep. "
              "Kick it down the lane, says the fixer. The pup, it turns "
              "out, has family.",
         pool=WOLF_POOL,
         skins={"wolf": "Very Big Dog", "dire wolf": "the Pup's Mother"},
         sites=("the back lane", "the kennel yard"),
         giver="the fixer",
         epilogue="The pup limps home. Somewhere a tavern bard is already "
                  "singing about the brutes who kicked it, with gestures."),
    dict(title="The Protection Round", align="dark",
         desc="Three streets of shopkeepers pooled their coin and hired "
              "steel instead of paying up. The racket wants the lesson "
              "delivered anyway.",
         pool=LADDER_POOL,
         skins={"cutthroat": "Hired Knife", "archer": "Rooftop Lookout",
                "bruiser": "Shop-Door Tough", "soldier": "Hired Guard",
                "veteran": "Guard Sergeant", "champion": "the Streets' "
                "Champion"},
         sites=("the market row", "the counting room"),
         giver="the racket's collector",
         epilogue="The shutters go up meekly on rent day. The shopkeepers "
                  "smile at the party in the street, carefully, with "
                  "every tooth."),
    dict(title="Burn the Granary", align="dark",
         desc="The miller's rival pays for a fire and no witnesses. The "
              "miller, regrettably, pays for guards and dogs.",
         pool=("wolf",) + LADDER_POOL[:4],
         skins={"wolf": "Miller's Mastiff", "cutthroat": "Night Watchman",
                "archer": "Granary Archer", "bruiser": "Miller's Man",
                "soldier": "Hired Guard"},
         sites=("the mill yard", "the granary floor"),
         giver="the rival in silk",
         epilogue="Grain prices double by market day. The rival in silk "
                  "is very sorry to hear it, publicly, at length."),
    dict(title="The Reliquary Job", align="dark",
         desc="A collector wants the temple's golden relic, feels the "
              "temple has had its turn. The keepers keep it with steel "
              "and scripture.",
         pool=LADDER_POOL[:6] + CASTER_POOL,
         skins={"cutthroat": "Temple Novice", "archer": "Roof Warden",
                "bruiser": "Lay Brother", "soldier": "Temple Guard",
                "veteran": "Warden of the Shrine",
                "champion": "the Faith's Sworn Blade",
                "hexer": "Curse-Chanter", "pyromancer": "Censer-Burner"},
         sites=("the temple court", "the reliquary vault"),
         giver="the veiled collector",
         epilogue="The empty plinth draws bigger crowds than the relic "
                  "ever did. The priests declare a miracle of absence "
                  "and double the alms box takings."),
    dict(title="The Debt Collection", align="dark",
         desc="A whole village signed, sealed, and stopped paying. The "
              "moneylender pays a fifth of the book to whoever squeezes "
              "it out of them -- and the village has raised a militia.",
         pool=LADDER_POOL[:5],
         skins={"cutthroat": "Village Rough", "archer": "Poacher-Turned-"
                "Sentry", "bruiser": "the Blacksmith", "soldier":
                "Militiaman", "veteran": "the Old Campaigner"},
         sites=("the barricaded bridge", "the village square"),
         giver="the moneylender's broker",
         epilogue="The village pays to the copper, then names its new "
                  "well after the party. The bucket, specifically."),
    dict(title="Grave Goods", align="dark",
         desc="The old barrow is consecrated ground and the parish is "
              "touchy about it. The broker is not: the dead wear gold "
              "down there, and gold belongs to the living.",
         pool=UNDEAD_POOL,
         skins={},
         sites=("the broken seal", "the gold-hung galleries"),
         giver="the grave-broker",
         epilogue="The parish re-consecrates the barrow at great expense. "
                  "The broker weighs the grave-gold twice and asks, "
                  "brightly, about the OTHER barrow."),
    dict(title="Toll the King's Road", align="dark",
         desc="Why rob a road when you can OWN one? Set up the chain, "
              "post the rates -- and hold the crossing when the garrison "
              "comes to take it down.",
         pool=LADDER_POOL,
         skins={"cutthroat": "Garrison Scout", "archer": "Garrison "
                "Crossbowman", "bruiser": "Garrison Mauler",
                "soldier": "Garrison Regular", "veteran": "Garrison "
                "Sergeant", "champion": "the Garrison Captain",
                "blademaster": "the Crown's Duelist",
                "warlord": "the Lord Marshal"},
         sites=("the toll chain", "the fordside camp", "the held crossing"),
         giver="the ambitious lieutenant",
         epilogue="For one glorious week the road pays the party, not "
                  "the crown. Clerks in three counting-houses develop "
                  "nervous conditions."),
]


def roll_dark_quest(world: dict, settlement: dict, pc_level: int,
                    rng: random.Random,
                    used_names: set[str] | None = None) -> dict:
    """One shadow job: leveled AT the party (-1..+2 -- the fixer offers
    what the taker can handle; the public board's OSR stance is about the
    honest world), built by build_quest unchanged, flagged dark, given a
    shady face. Registered in world['quests'] (so show/take work) but on
    NO settlement board -- the shadow board lists it (session.py)."""
    level = max(1, min(LEVEL_CAP, pc_level + rng.randint(-1, 2)))
    fitting = [t for t in DARK_TEMPLATES
               if template_band(t)[0] <= level <= template_band(t)[1]]
    tpl = rng.choice(fitting or DARK_TEMPLATES)
    lo, hi = template_band(tpl)
    level = max(lo, min(hi, level))
    # First free id: stale shadow jobs are PRUNED from world['quests']
    # (session.py rolls a fresh board per settlement day), so the count
    # alone can collide with a surviving taken job's id.
    n = len(world["quests"]) + 1
    while f"q{n:02d}" in world["quests"]:
        n += 1
    qid = f"q{n:02d}"
    quest = build_quest(qid, tpl, settlement["key"], level, rng)
    attach_giver(quest, settlement["race"], rng, role=tpl.get("giver"),
                 used_names=used_names)
    world["quests"][qid] = quest
    return quest


# --------------------------------------------------------------------------- #
# Punishment (the posses)
# --------------------------------------------------------------------------- #
# Budget-honest ladder rosters (the same threat math as any wild
# encounter) wearing LAWFUL display names by band, led by a generated
# face. The bands escalate with the posse's level, not with time: the
# Watch chases petty villains; heroes of the realm chase warlords.

POSSE_BANDS = (
    # (min posse level, band label, leader role, skins over LADDER_POOL)
    (14, "heroes of the realm", "famous hero",
     {"cutthroat": "Hero's Scout", "archer": "Far-Famed Archer",
      "bruiser": "the Strong Companion", "soldier": "Sworn Companion",
      "veteran": "Errant Hero", "champion": "Famous Hero",
      "blademaster": "Legendary Swordmaster",
      "warlord": "the Realm's Chosen"}),
    (9, "the crown's huntsmen", "knight-captain of the hunt",
     {"cutthroat": "Crown Informer", "archer": "Royal Tracker",
      "bruiser": "the King's Mauler", "soldier": "King's Huntsman",
      "veteran": "Knight-Errant", "champion": "Knight-Captain",
      "blademaster": "the Crown's Blade", "warlord": "the Lord Marshal"}),
    (4, "the bounty guild", "bounty captain",
     {"cutthroat": "Bounty Knife", "archer": "Bounty Archer",
      "bruiser": "Man-Catcher", "soldier": "Bounty Hunter",
      "veteran": "Seasoned Man-Hunter", "champion": "the Guild's Best",
      "blademaster": "the Guild's Legend"}),
    (0, "the Watch", "sergeant of the Watch",
     {"cutthroat": "Watch Runner", "archer": "Watch Bowman",
      "bruiser": "Watch Bruiser", "soldier": "Watchman",
      "veteran": "Watch Sergeant", "champion": "Watch Captain"}),
)


def posse_band(level: int) -> tuple[str, str, dict]:
    for floor, label, role, skins in POSSE_BANDS:
        if level >= floor:
            return label, role, skins
    return POSSE_BANDS[-1][1:]      # unreachable; keeps the checker honest


def build_posse(level: int, race: str, rng: random.Random,
                used_names: set[str] | None = None
                ) -> tuple[list[str], dict, dict, str]:
    """One punishment encounter at `level`: (kinds, skins, leader npc,
    band label). A full reference-encounter budget off the plain ladder
    -- exactly a wild encounter's weight, wearing the law's names. The
    leader is a generated face (people.make_npc) for the strongest slot
    and the DM's scene; their name is the nemesis seed."""
    from people import make_npc     # runtime import (people imports quests)
    label, role, skins = posse_band(level)
    kinds = build_room(room_budget(level, 1.0), LADDER_POOL, rng,
                       final=True)
    leader = make_npc(rng, race, role, level=level, used_names=used_names)
    return kinds, skins, leader, label


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    from quests import generate_world, quest_detail_lines
    world = generate_world(rng.randrange(1 << 30))
    s = world["settlements"][0]
    print(f"Sample shadow board at {s['name']} (PC level 3):")
    for _ in range(DARK_JOBS_PER_DAY):
        q = roll_dark_quest(world, s, 3, rng)
        for line in quest_detail_lines(q):
            print(line)
        print()
    print("Sample posses (one per heat band):")
    for lvl in (3, 6, 11, 16):
        kinds, skins, leader, label = build_posse(lvl, s["race"], rng)
        shown = ", ".join(skins.get(k, k) for k in kinds)
        print(f"  L{lvl} ({label}): {shown}")
        print(f"    led by {leader['name']}, {leader['role']}")


if __name__ == "__main__":
    main()
