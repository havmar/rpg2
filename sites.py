"""The game's content: the foe catalog and the two hand-built sites.

The engine lives in rpg.py; this file holds what you FIGHT and WHERE. It is
the seed of the encounter & quest system (plan.md): foe stat blocks (FOES),
the two set sites (SITES -- the bandit hideout and the skeleton barrow), and
ONE generic site runner (run_site) shared by the one-shot entry point and the
batch sims (tune.py, bench_training.py), so the layout that gets tuned is the
layout that gets played. Session play (session.py) draws rooms and foes from
the same tables.

The two sites, by design:
- The bandit HIDEOUT is the STARTER site. Bandits are living fighters who
  play by exactly the party's rules: real DEX/STR, they spend STA to swing,
  go Winded, and are SPENT at 0 like anyone alive -- its logs teach the
  system with no special cases. Base pay: a full clear (3 encounters + quest)
  is exactly the level-1 -> 2 XP cost.
- The skeleton BARROW is the TOUGH site (3x pay). Skeletons are the exception
  enemies: undead (half wound penalty -- no pain) and tireless (never spend
  STA, never Winded/Spent), so the threat is numbers outlasting a party whose
  stamina is a death-track. Met second on purpose: living foes first.

Run:  python sites.py                        # one-shot barrow run, full log
      python sites.py --site hideout         # one-shot starter-site run
      python sites.py --seed 7               # reproducible
      python sites.py --training 2           # start the party pre-trained
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass

from rpg import (Entity, Weapon, Clock, Purse, RUSTED_BLADE,
                 make_party, stat_line, outcome, start_fight,
                 short_rest, long_rest, party_wiped,
                 award_xp, award_quest, roll_loot, auto_use_potions_on_rest,
                 train_combat, random_common_weapon,
                 sim_fight, refresh_foes_after_retreat,
                 ENCOUNTER_XP, QUEST_XP, QUEST_GOLD,
                 BARROW_ENCOUNTER_XP, BARROW_QUEST_XP, BARROW_QUEST_GOLD,
                 SIM_MAX_ROOM_ATTEMPTS)


# --------------------------------------------------------------------------- #
# The foe catalog
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class FoeSpec:
    """One foe stat block. The seed of the monster/opponent catalog (plan.md):
    every foe in the game is a row here, and make_foe() is the one place a
    stat block becomes a fighting Entity."""
    display: str            # log name stem ("Skeleton" -> "Skeleton 3")
    dex: int
    str_: int
    sta: int
    hp: int
    undead: bool = False    # no pain: wound roll penalty halved
    tireless: bool = False  # never spends STA, never Winded/Spent
    pursues: bool = True    # gives chase when the party retreats
    weapon: Weapon | None = None    # fixed armament (the skeletons' rusted
                                    # blades); None = roll the common table
                                    # like a starting hero


# Enemy DEX runs hot across the board (2026-07 lethality retune): who hits is
# DEX's job, and danger has to live in each encounter itself -- the party can
# always camp after it. A single point of foe DEX moves clear rates by tens
# of percent; it is the sharpest tuning knife in this table.
FOES = {
    # The bandits: raw living fighters, no Power/ability/kit. They arm from
    # the same common-weapon table as starting heroes (50% crude / 45%
    # soldier's arms / 5% heavy) -- always a specific named weapon, so the
    # logs read "Cutthroat 2's dagger", never "a crude weapon".
    "cutthroat": FoeSpec("Cutthroat", dex=5, str_=3, sta=5, hp=7),  # nimble knife-work
    "bruiser":   FoeSpec("Bruiser",   dex=4, str_=5, sta=5, hp=9),  # heavy and durable, quicker than he looks
    "archer":    FoeSpec("Archer",    dex=5, str_=2, sta=5, hp=6),  # lands often, soft
    # The skeleton: brittle and a weak individual hitter (low STR -> low
    # severity), but undead and TIRELESS -- the stamina war is one-sided; the
    # bones don't have to beat you, just outlast you. pursues=False: bound to
    # the grave -- they swing at a fleeing party's backs but never follow
    # past the door, which is what makes "come back tomorrow and finish it" a
    # real plan instead of a death sentence. Their corroded grave-steel
    # (durability 1) snaps on good steel -- the barrow visibly eases as the
    # party's gear improves.
    "skeleton":  FoeSpec("Skeleton",  dex=4, str_=2, sta=8, hp=5,
                         undead=True, tireless=True, pursues=False,
                         weapon=RUSTED_BLADE),
}

BANDIT_KINDS = ("archer", "bruiser", "cutthroat")   # the living-foe pool


def make_foe(kind: str, n: int, rng: random.Random) -> Entity:
    """Stat block -> fighting Entity, numbered for the log ("Cutthroat 2")."""
    spec = FOES[kind]
    weapon = spec.weapon if spec.weapon is not None else random_common_weapon(rng)
    return Entity(name=f"{spec.display} {n}", dex=spec.dex, str_=spec.str_,
                  sta=spec.sta, max_hp=spec.hp, undead=spec.undead,
                  tireless=spec.tireless, pursues=spec.pursues, weapon=weapon)


def roster_lines(foes: list[Entity]) -> list[str]:
    """The room's roster for the log. Identical foes collapse into one
    counted line ("3x Skeleton: ..."); foes that differ (a bandit's rolled
    weapon, a survivor's wounds) each get their own."""
    def body(e: Entity) -> str:
        wpn = e.weapon.name if e.weapon else "unarmed"
        tags = []
        if e.undead:
            tags.append("undead: no pain")
        if e.tireless:
            tags.append("tireless")
        tag = f"; {', '.join(tags)}" if tags else ""
        sta = "" if e.tireless else f"STA {e.sta}  "
        return (f"DEX {e.dex}  STR {e.str_}  {sta}HP {e.hp}/{e.max_hp}  "
                f"({wpn}{tag})")

    groups: list[tuple[str, list[Entity]]] = []
    for f in foes:
        b = body(f)
        for gb, members in groups:
            if gb == b:
                members.append(f)
                break
        else:
            groups.append((b, [f]))
    lines = []
    for b, members in groups:
        if len(members) == 1:
            lines.append(f"{members[0].name}: {b}")
        else:
            stem = members[0].name.rsplit(" ", 1)[0]
            lines.append(f"{len(members)}x {stem}: {b}")
    return lines


# --------------------------------------------------------------------------- #
# The sites
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Site:
    """One authored site: set rooms, set rosters, set pay. The sites are
    balanced during development and never improvised at the table -- the DM
    runs them room-by-room (session.py `hideout ROOM` / `barrow ROOM`);
    `fight N` is the off-script escape hatch for improvised scenes only."""
    key: str                # save-file / CLI identity ("hideout", "barrow")
    rooms: tuple[tuple[str, tuple[str, ...]], ...]  # (room name, foe kinds)
    encounter_xp: int
    quest_xp: int
    quest_gold: int
    quest_line: str         # the QUEST COMPLETE banner
    spawn_phrase: str       # room banner flavor; {n} = foe count
    abandon_line: str       # the sims' walk-away line
    intro: str              # the one-shot opening line


# The set room layouts -- the first difficulty lever (CLAUDE.md "Balance /
# tuning"). Edit these here; every consumer (one-shot, session, tune, bench)
# reads the same tables.
HIDEOUT_ROOMS = (
    ("the lookout post", ("cutthroat",)),
    ("the common room", ("cutthroat", "archer")),
    ("the boss's den", ("bruiser", "cutthroat")),
)
BARROW_ROOMS = (
    ("the collapsed entry", ("skeleton",) * 3),
    ("the ossuary", ("skeleton",) * 3),
    ("the burial vault", ("skeleton",) * 4),
)

SITES = {
    "hideout": Site(
        key="hideout",
        rooms=HIDEOUT_ROOMS,
        encounter_xp=ENCOUNTER_XP,
        quest_xp=QUEST_XP,
        quest_gold=QUEST_GOLD,
        quest_line="the hideout is broken",
        spawn_phrase="{n} bandits",
        abandon_line="the hideout is left be.",
        intro="The party slips into the bandit hideout:",
    ),
    "barrow": Site(
        key="barrow",
        rooms=BARROW_ROOMS,
        encounter_xp=BARROW_ENCOUNTER_XP,
        quest_xp=BARROW_QUEST_XP,
        quest_gold=BARROW_QUEST_GOLD,
        quest_line="the barrow is cleansed",
        spawn_phrase="{n} skeletons rise from the bones",
        abandon_line="the barrow is abandoned.",
        intro="The party descends into the barrow:",
    ),
}


# --------------------------------------------------------------------------- #
# The generic site runner (one-shot + batch sims)
# --------------------------------------------------------------------------- #

def run_site(site: Site, party: list[Entity], clock: Clock, purse: Purse,
             rng: random.Random, log: list[str], *,
             verbose_rosters: bool = True, reckless: bool = False,
             rooms=None) -> None:
    """Run a site start to finish under the batch-sim policies (sim_fight
    answers pauses via sim_pause_policy; a fled room gets one return trip).
    Session play shares the same engine and tables but the PLAYER answers the
    pauses -- see session.py.

    `rooms` overrides the site's layout (tune.py's sweep knob).
    reckless=True is the no-resource baseline: no pauses (so no drinks,
    conversions, or retreats) and no potions drunk at rests -- short rests
    still happen (pacing, not a consumable)."""
    rooms = site.rooms if rooms is None else rooms
    count = 0
    cleared_all = True
    room_i = 0
    attempts = 0
    held_over: list[Entity] | None = None   # survivors of a room the party fled
    while room_i < len(rooms):
        room_name, roster = rooms[room_i]
        living = [h for h in party if not h.dead]
        if not living:
            cleared_all = False
            break

        log.append("")
        if held_over is None:
            attempts = 1
            spawn = site.spawn_phrase.format(n=len(roster))
            log.append(f"=== Room {room_i + 1}: {room_name} ({spawn}) ===")
            foes = []
            for kind in roster:
                count += 1
                foes.append(make_foe(kind, count, rng))
            if verbose_rosters:
                for line in roster_lines(foes):
                    log.append("  " + line)
        else:
            attempts += 1
            foes = held_over
            held_over = None
            standing = sum(1 for f in foes if f.alive)
            log.append(f"=== Room {room_i + 1}: {room_name}, again -- "
                       f"{standing} foe(s) still hold it ===")
        for h in living:
            start_fight(h, log)

        result = sim_fight(living, foes, rng, log, reckless=reckless)

        if party_wiped(party, log):
            cleared_all = False
            break
        if result == "fled":
            if attempts >= SIM_MAX_ROOM_ATTEMPTS:
                log.append(f"  The party has had enough -- {site.abandon_line}")
                cleared_all = False
                break
            # Rest up and go back in (the sims' determined-player policy):
            # a short rest if a slot is left today, else camp overnight.
            day_before = clock.day
            survivors = [h for h in party if h.alive]
            if not short_rest(survivors, clock, log):
                long_rest(party, clock, log)
            auto_use_potions_on_rest([h for h in party if h.alive], log)
            held_over = refresh_foes_after_retreat(foes,
                                                   clock.day - day_before)
            continue    # the same room, again
        if any(f.alive for f in foes):
            # Unresolved (the fight staggered apart): no award, no clear.
            log.append("  The room is not cleared -- the party pulls back.")
            cleared_all = False
            break

        award_xp(party, site.encounter_xp, log, "encounter")
        roll_loot(party, purse, rng, log)

        survivors = [h for h in party if h.alive]
        if survivors:
            log.append(f"  Room cleared. {len(survivors)} still standing.")
            short_rest(survivors, clock, log)
            if not reckless:
                auto_use_potions_on_rest(survivors, log)  # sim: sensible party
        room_i += 1

    if cleared_all and any(not h.dead for h in party):
        award_quest(party, purse, site.quest_gold, site.quest_xp,
                    log, site.quest_line)
        for h in party:
            if not h.dead:
                train_combat(h, log)    # sim policy: auto-spend on training


# --------------------------------------------------------------------------- #
# One-shot entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", choices=sorted(SITES), default="barrow")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--training", type=int, default=0,
                    help="start the party at this combat-training rank")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    site = SITES[args.site]

    party = make_party(rng)
    for h in party:
        h.training = args.training
    clock = Clock()
    purse = Purse()
    log = [f"Day {clock.day}. {site.intro}"]
    for h in party:
        log.append("  " + stat_line(h))

    run_site(site, party, clock, purse, rng, log)
    # No auto-night: making camp (long_rest) is a deliberate call Claude makes
    # between adventuring days, not something the site loop does on its own.

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
