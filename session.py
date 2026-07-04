"""DM session driver -- runs the game turn-by-turn from the terminal.

rpg.py's primitives (start_fight, group_combat, short_rest, long_rest, ...)
are meant to be called on purpose, in whatever order the story wants (see
CLAUDE.md, "The feel we're going for"). But each terminal call is a fresh
Python process, so something has to hold party/clock/purse state *between*
calls. That's all this file does: a thin CLI over rpg.py's functions, with
state pickled to .session_state.pkl (gitignored -- it's a save file, not
source) between invocations. It adds no game logic of its own.

Run:  python session.py new [--seed N]              # new party, resets state
      python session.py status                       # show party/clock/purse
      python session.py fight N [--type skeleton]     # spawn N foes, resolve one melee
                                                        # (N is the DM's call each time --
                                                        # not read from rpg.py's DUNGEON_ROOMS,
                                                        # which only sizes the one-shot/tune.py
                                                        # dungeon run)
      python session.py hideout ROOM                  # resolve one hideout room (1-3)
      python session.py rest                          # short rest (spends a slot)
      python session.py camp                          # long rest (advance a day)
      python session.py quest GOLD XP NAME             # award a site-clear quest
      python session.py buy HERO KIND                  # buy a potion from the purse
      python session.py heal HEALER TARGET              # Heal ability, between fights
"""
from __future__ import annotations

import argparse
import pickle
import random
from pathlib import Path

from rpg import (
    Clock, Purse, POTION_KINDS, SKELETON_ENCOUNTER_XP,
    make_party, make_skeleton, stat_line,
    start_fight, group_combat, party_wiped,
    award_xp, roll_loot, award_quest,
    short_rest as _short_rest, long_rest as _long_rest,
    buy_potion as _buy_potion, use_heal as _use_heal,
)
from scratch_bandits import make_bandit, bandit_line, HIDEOUT_ROOMS

STATE_PATH = Path(__file__).parent / ".session_state.pkl"

FOE_MAKERS = {"skeleton": make_skeleton}


def save(state: dict) -> None:
    with open(STATE_PATH, "wb") as f:
        pickle.dump(state, f)


def load() -> dict:
    with open(STATE_PATH, "rb") as f:
        return pickle.load(f)


def cmd_new(args: argparse.Namespace) -> None:
    rng = random.Random(args.seed)
    party = make_party(rng)
    state = {"party": party, "clock": Clock(), "purse": Purse(), "rng": rng,
              "foe_count": 0}
    save(state)
    print(f"New party rolled (seed={args.seed}):")
    for h in party:
        print("  " + stat_line(h))


def cmd_status(args: argparse.Namespace) -> None:
    state = load()
    party, clock, purse = state["party"], state["clock"], state["purse"]
    print(f"Day {clock.day}, {clock.short_rests_left} short rest(s) left today. "
          f"Purse: {purse.gold}g.")
    for h in party:
        tag = " [DEAD]" if h.dead else " [DOWN]" if h.down else ""
        print("  " + stat_line(h) + tag)


def cmd_fight(args: argparse.Namespace) -> None:
    state = load()
    party, purse, rng = state["party"], state["purse"], state["rng"]
    log: list[str] = []
    living = [h for h in party if not h.dead]
    for h in living:
        start_fight(h, log)

    maker = FOE_MAKERS[args.type]
    foes = []
    for _ in range(args.n):
        state["foe_count"] += 1
        foes.append(maker(rng, state["foe_count"]))

    group_combat(living, foes, rng, log)
    wiped = party_wiped(party, log)
    if not wiped:
        award_xp(party, SKELETON_ENCOUNTER_XP, log, "encounter")
        roll_loot(party, purse, rng, log)

    print("\n".join(log))
    save(state)
    if wiped:
        print("\n*** RUN OVER: total party wipe. ***")


def cmd_hideout(args: argparse.Namespace) -> None:
    state = load()
    party, purse, rng = state["party"], state["purse"], state["rng"]
    log: list[str] = []
    living = [h for h in party if not h.dead]
    for h in living:
        start_fight(h, log)

    room_name, roster = HIDEOUT_ROOMS[args.room - 1]
    log.append(f"=== Room {args.room}: {room_name} ({len(roster)} bandits) ===")
    bandits = []
    for kind in roster:
        state["foe_count"] += 1
        bandits.append(make_bandit(kind, state["foe_count"]))
    for b in bandits:
        log.append("  " + bandit_line(b))

    group_combat(living, bandits, rng, log)
    wiped = party_wiped(party, log)
    if not wiped:
        award_xp(party, 3 * SKELETON_ENCOUNTER_XP, log, "encounter")
        roll_loot(party, purse, rng, log)

    print("\n".join(log))
    save(state)
    if wiped:
        print("\n*** RUN OVER: total party wipe. ***")


def cmd_rest(args: argparse.Namespace) -> None:
    state = load()
    party, clock = state["party"], state["clock"]
    log: list[str] = []
    _short_rest([h for h in party if h.alive], clock, log)
    print("\n".join(log) if log else "(nothing happened)")
    save(state)


def cmd_camp(args: argparse.Namespace) -> None:
    state = load()
    party, clock = state["party"], state["clock"]
    log: list[str] = []
    _long_rest(party, clock, log)
    print("\n".join(log))
    save(state)


def cmd_quest(args: argparse.Namespace) -> None:
    state = load()
    party, purse = state["party"], state["purse"]
    log: list[str] = []
    award_quest(party, purse, args.gold, args.xp, log, args.name)
    print("\n".join(log))
    save(state)


def cmd_buy(args: argparse.Namespace) -> None:
    state = load()
    party, purse = state["party"], state["purse"]
    log: list[str] = []
    hero = next(h for h in party if args.hero.lower() in h.name.lower())
    _buy_potion(hero, purse, args.kind, log)
    print("\n".join(log))
    save(state)


def cmd_heal(args: argparse.Namespace) -> None:
    state = load()
    party, rng = state["party"], state["rng"]
    log: list[str] = []
    healer = next(h for h in party if args.healer.lower() in h.name.lower())
    target = next(h for h in party if args.target.lower() in h.name.lower())
    _use_heal(healer, target, rng, log)
    print("\n".join(log))
    save(state)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new", help="start a fresh party/clock/purse (overwrites save)")
    p.add_argument("--seed", type=int, default=None)
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("status", help="show the persisted party/clock/purse")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser(
        "fight",
        help="spawn N foes and resolve one encounter against the party "
             "(N is a free choice each call, not tied to any fixed room list)")
    p.add_argument("n", type=int, help="how many foes to spawn for this encounter")
    p.add_argument("--type", default="skeleton", choices=list(FOE_MAKERS))
    p.set_defaults(func=cmd_fight)

    p = sub.add_parser(
        "hideout",
        help="resolve one bandit-hideout room (fixed roster per room, unlike `fight`)")
    p.add_argument("room", type=int, choices=[1, 2, 3])
    p.set_defaults(func=cmd_hideout)

    p = sub.add_parser("rest", help="short rest: spends a daily slot for a small catch-breath")
    p.set_defaults(func=cmd_rest)

    p = sub.add_parser("camp", help="long rest: full STA, weekly HP tick, advances a day")
    p.set_defaults(func=cmd_camp)

    p = sub.add_parser("quest", help="award a site-clear quest bonus (gold + XP lump)")
    p.add_argument("gold", type=int)
    p.add_argument("xp", type=int)
    p.add_argument("name")
    p.set_defaults(func=cmd_quest)

    p = sub.add_parser("buy", help="spend gold on a potion for one hero")
    p.add_argument("hero")
    p.add_argument("kind", choices=list(POTION_KINDS))
    p.set_defaults(func=cmd_buy)

    p = sub.add_parser("heal", help="Heal ability, between fights only")
    p.add_argument("healer")
    p.add_argument("target")
    p.set_defaults(func=cmd_heal)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
