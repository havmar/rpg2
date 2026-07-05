"""DM session driver -- runs the game turn-by-turn from the terminal.

rpg.py's primitives (start_fight, group_combat, short_rest, long_rest, ...)
are meant to be called on purpose, in whatever order the story wants (see
CLAUDE.md, "The feel we're going for"). But each terminal call is a fresh
Python process, so something has to hold party/clock/purse state *between*
calls. That's all this file does: a thin CLI over rpg.py's functions, with
state pickled to .session_state.pkl (gitignored -- it's a save file, not
source) between invocations. It adds no game logic of its own.

The first hero rolled (party[0]) is the PLAYER CHARACTER; the rest are
companions. PC death ends the game even if a companion stands (see dm.md --
the DM protocol for actually playing lives there).

Run:  python session.py new [--seed N]              # new party, resets state
      python session.py status                       # show party/clock/purse
      python session.py hideout ROOM                  # resolve one hideout room (1-3,
                                                        # SET roster per room -- the STARTER
                                                        # site: living foes, base pay)
      python session.py barrow ROOM                   # resolve one barrow room (1-3,
                                                        # SET skeleton count per room from
                                                        # rpg.BARROW_ROOMS -- the TOUGH site:
                                                        # tireless undead, 3x pay)
      python session.py fight N [--type skeleton|bandit]  # OFF-SCRIPT encounter: spawn N foes
                                                        # (road ambushes and other improvised
                                                        # scenes only -- the two sites are set
                                                        # encounters, use barrow/hideout)
      python session.py rest                          # short rest (spends a slot)
      python session.py camp                          # long rest (advance a day)
      python session.py quest GOLD XP NAME             # award a site-clear quest
      python session.py buy HERO THING                  # buy a potion OR a weapon from
                                                        # the purse (weapons are equipped
                                                        # on the spot; plain tier only)
      python session.py give HERO WEAPON                # DM-granted loot: wield a weapon
                                                        # for free (quest rewards, a sword
                                                        # looted off a bandit, ...)
      python session.py train HERO combat|weapon        # spend a banked skill point:
                                                        # combat training (+1 all tempo)
                                                        # or proficiency with the WIELDED
                                                        # weapon (+1 atk tempo & +1 severity
                                                        # with it). Player choice -- nothing
                                                        # auto-spends in session play.
      python session.py use HERO KIND                  # drink a carried potion (instant, between fights)
      python session.py heal HEALER TARGET              # Heal ability, between fights
"""
from __future__ import annotations

import argparse
import pickle
import random
from pathlib import Path

from rpg import (
    Clock, Purse, POTION_KINDS, WEAPONS, ENCOUNTER_XP, BARROW_ENCOUNTER_XP,
    BARROW_ROOMS,
    make_party, make_skeleton, stat_line,
    start_fight, group_combat, party_wiped,
    award_xp, roll_loot, award_quest,
    short_rest as _short_rest, long_rest as _long_rest,
    buy_potion as _buy_potion, use_heal as _use_heal,
    use_potion as _use_potion, buy_weapon as _buy_weapon,
    equip_weapon as _equip_weapon,
    train_combat_once as _train_combat_once,
    train_proficiency as _train_proficiency,
)
from scratch_bandits import (make_bandit, bandit_line, HIDEOUT_ROOMS,
                             BANDIT_TYPES, BANDIT_ENCOUNTER_XP)

STATE_PATH = Path(__file__).parent / ".session_state.pkl"


def _make_random_bandit(rng, n):
    return make_bandit(rng.choice(sorted(BANDIT_TYPES)), n, rng)


FOE_MAKERS = {"skeleton": make_skeleton, "bandit": _make_random_bandit}


def save(state: dict) -> None:
    with open(STATE_PATH, "wb") as f:
        pickle.dump(state, f)


def load() -> dict:
    with open(STATE_PATH, "rb") as f:
        return pickle.load(f)


def role_tag(party: list, h) -> str:
    """party[0] is the player character; the rest are companions (see dm.md)."""
    return "(YOU)      " if h is party[0] else "(companion)"


def cmd_new(args: argparse.Namespace) -> None:
    rng = random.Random(args.seed)
    party = make_party(rng)
    state = {"party": party, "clock": Clock(), "purse": Purse(), "rng": rng,
              "foe_count": 0}
    save(state)
    print(f"New party rolled (seed={args.seed}):")
    for h in party:
        print(f"  {role_tag(party, h)} " + stat_line(h))
    print(f"The player character is {party[0].name} -- if they die, game over.")


def cmd_status(args: argparse.Namespace) -> None:
    state = load()
    party, clock, purse = state["party"], state["clock"], state["purse"]
    print(f"Day {clock.day}, {clock.short_rests_left} short rest(s) left today. "
          f"Purse: {purse.gold}g.")
    for h in party:
        tag = " [DEAD]" if h.dead else " [DOWN]" if h.down else ""
        print(f"  {role_tag(party, h)} " + stat_line(h) + tag)


def resolve_encounter(state: dict, log: list[str], foes: list,
                      encounter_xp: int) -> None:
    """Shared tail of every encounter command: run the melee, award, persist."""
    party, purse, rng = state["party"], state["purse"], state["rng"]
    living = [h for h in party if not h.dead]
    group_combat(living, foes, rng, log)
    wiped = party_wiped(party, log)
    if not wiped and any(f.alive for f in foes):
        # Unresolved (the fight staggered apart, both sides spent): no award.
        log.append("  The encounter is not cleared -- the foes still stand.")
    elif not wiped:
        award_xp(party, encounter_xp, log, "encounter")
        roll_loot(party, purse, rng, log)

    print("\n".join(log))
    save(state)
    report_game_over(party, wiped)


def cmd_fight(args: argparse.Namespace) -> None:
    state = load()
    party, rng = state["party"], state["rng"]
    log: list[str] = []
    for h in [h for h in party if not h.dead]:
        start_fight(h, log)

    maker = FOE_MAKERS[args.type]
    foes = []
    for _ in range(args.n):
        state["foe_count"] += 1
        foes.append(maker(rng, state["foe_count"]))

    resolve_encounter(state, log, foes, ENCOUNTER_XP)


def cmd_barrow(args: argparse.Namespace) -> None:
    state = load()
    party, rng = state["party"], state["rng"]
    log: list[str] = []
    for h in [h for h in party if not h.dead]:
        start_fight(h, log)

    room_name, n_skel = BARROW_ROOMS[args.room - 1]
    log.append(f"=== Barrow room {args.room}: {room_name} "
               f"({n_skel} skeletons rise from the bones) ===")
    skeletons = []
    for _ in range(n_skel):
        state["foe_count"] += 1
        skeletons.append(make_skeleton(rng, state["foe_count"]))
    s = skeletons[0]
    log.append(f"  {len(skeletons)} skeletons: DEX {s.dex}  STR {s.str_}  "
               f"HP {s.max_hp} each (undead: no pain, tireless)")

    resolve_encounter(state, log, skeletons, BARROW_ENCOUNTER_XP)


def report_game_over(party: list, wiped: bool) -> None:
    """The two run-ending states: a total wipe, or the player character slain
    (party[0] is the PC -- see dm.md; the companion surviving doesn't save the
    game)."""
    if wiped:
        print("\n*** RUN OVER: total party wipe. GAME OVER. ***")
    elif party[0].dead:
        print(f"\n*** {party[0].name} -- the player character -- is slain. "
              f"GAME OVER. ***")


def cmd_hideout(args: argparse.Namespace) -> None:
    state = load()
    party, rng = state["party"], state["rng"]
    log: list[str] = []
    for h in [h for h in party if not h.dead]:
        start_fight(h, log)

    room_name, roster = HIDEOUT_ROOMS[args.room - 1]
    log.append(f"=== Room {args.room}: {room_name} ({len(roster)} bandits) ===")
    bandits = []
    for kind in roster:
        state["foe_count"] += 1
        bandits.append(make_bandit(kind, state["foe_count"], rng))
    for b in bandits:
        log.append("  " + bandit_line(b))

    resolve_encounter(state, log, bandits, BANDIT_ENCOUNTER_XP)


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
    thing = " ".join(args.thing).lower()
    if thing in POTION_KINDS:
        _buy_potion(hero, purse, thing, log)
    elif thing in WEAPONS:
        _buy_weapon(hero, purse, thing, log)
    else:
        print(f"Unknown purchase: {thing!r}. Potions: {', '.join(POTION_KINDS)}. "
              f"Weapons: {', '.join(sorted(WEAPONS))}.")
        return
    print("\n".join(log))
    save(state)


def cmd_give(args: argparse.Namespace) -> None:
    state = load()
    party = state["party"]
    log: list[str] = []
    hero = next(h for h in party if args.hero.lower() in h.name.lower())
    name = " ".join(args.weapon).lower()
    weapon = WEAPONS.get(name)
    if weapon is None:
        print(f"Unknown weapon: {name!r}. Weapons: {', '.join(sorted(WEAPONS))}.")
        return
    _equip_weapon(hero, weapon, log)
    print("\n".join(log))
    save(state)


def cmd_train(args: argparse.Namespace) -> None:
    state = load()
    party = state["party"]
    log: list[str] = []
    hero = next(h for h in party if args.hero.lower() in h.name.lower())
    if args.what == "combat":
        _train_combat_once(hero, log)
    else:
        _train_proficiency(hero, log)
    print("\n".join(log))
    save(state)


def cmd_use(args: argparse.Namespace) -> None:
    state = load()
    party = state["party"]
    log: list[str] = []
    hero = next(h for h in party if args.hero.lower() in h.name.lower())
    _use_potion(hero, args.kind, log)
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
        "barrow",
        help="resolve one skeleton-barrow room (SET skeleton count per room, "
             "from rpg.BARROW_ROOMS -- the TOUGH site, 3x pay)")
    p.add_argument("room", type=int, choices=range(1, len(BARROW_ROOMS) + 1))
    p.set_defaults(func=cmd_barrow)

    p = sub.add_parser(
        "hideout",
        help="resolve one bandit-hideout room (SET roster per room -- "
             "the STARTER site)")
    p.add_argument("room", type=int, choices=range(1, len(HIDEOUT_ROOMS) + 1))
    p.set_defaults(func=cmd_hideout)

    p = sub.add_parser(
        "fight",
        help="OFF-SCRIPT encounter: spawn N foes (improvised scenes like road "
             "ambushes only -- the two sites are set encounters, use barrow/hideout)")
    p.add_argument("n", type=int, help="how many foes to spawn for this encounter")
    p.add_argument("--type", default="skeleton", choices=list(FOE_MAKERS))
    p.set_defaults(func=cmd_fight)

    p = sub.add_parser("rest", help="short rest: spends a daily slot for a small catch-breath")
    p.set_defaults(func=cmd_rest)

    p = sub.add_parser("camp", help="long rest: full STA, weekly HP tick, advances a day")
    p.set_defaults(func=cmd_camp)

    p = sub.add_parser("quest", help="award a site-clear quest bonus (gold + XP lump)")
    p.add_argument("gold", type=int)
    p.add_argument("xp", type=int)
    p.add_argument("name")
    p.set_defaults(func=cmd_quest)

    p = sub.add_parser(
        "buy",
        help="spend gold on a potion or a weapon for one hero (weapons are "
             "equipped on the spot; plain tier only -- masterwork/legendary "
             "are never shopped)")
    p.add_argument("hero")
    p.add_argument("thing", nargs="+",
                   help="a potion kind or a weapon name (e.g. rapier, "
                        "wooden staff)")
    p.set_defaults(func=cmd_buy)

    p = sub.add_parser(
        "give",
        help="DM-granted loot: a hero wields a weapon for free (quest "
             "rewards, a blade looted off a bandit, ...)")
    p.add_argument("hero")
    p.add_argument("weapon", nargs="+", help="weapon name (e.g. wooden staff)")
    p.set_defaults(func=cmd_give)

    p = sub.add_parser(
        "train",
        help="spend a banked skill point: 'combat' = +1 to all tempo rolls "
             "per rank (cap 5); 'weapon' = proficiency with the WIELDED "
             "weapon, +1 attack tempo & +1 severity per rank (cap 3). "
             "Rank n costs n points. A player choice -- nothing auto-spends.")
    p.add_argument("hero")
    p.add_argument("what", choices=["combat", "weapon"])
    p.set_defaults(func=cmd_train)

    p = sub.add_parser(
        "use",
        help="drink a carried potion for one hero, between fights "
             "(instant top-up: healing restores HP, stamina/power restore now)")
    p.add_argument("hero")
    p.add_argument("kind", choices=list(POTION_KINDS))
    p.set_defaults(func=cmd_use)

    p = sub.add_parser("heal", help="Heal ability, between fights only")
    p.add_argument("healer")
    p.add_argument("target")
    p.set_defaults(func=cmd_heal)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
