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
      python session.py fight N [--type skeleton]     # resolve one room's melee
      python session.py rest                          # short rest (spends a slot)
      python session.py camp                          # long rest (advance a day)
      python session.py quest GOLD XP NAME             # award a site-clear quest
      python session.py buy HERO KIND                  # buy a potion from the purse
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
    buy_potion as _buy_potion,
)

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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new")
    p.add_argument("--seed", type=int, default=None)
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("status")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("fight")
    p.add_argument("n", type=int)
    p.add_argument("--type", default="skeleton", choices=list(FOE_MAKERS))
    p.set_defaults(func=cmd_fight)

    p = sub.add_parser("rest")
    p.set_defaults(func=cmd_rest)

    p = sub.add_parser("camp")
    p.set_defaults(func=cmd_camp)

    p = sub.add_parser("quest")
    p.add_argument("gold", type=int)
    p.add_argument("xp", type=int)
    p.add_argument("name")
    p.set_defaults(func=cmd_quest)

    p = sub.add_parser("buy")
    p.add_argument("hero")
    p.add_argument("kind", choices=list(POTION_KINDS))
    p.set_defaults(func=cmd_buy)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
