"""DM session driver -- runs the game turn-by-turn from the terminal.

rpg.py's primitives (start_fight, group_combat, short_rest, long_rest, ...)
are meant to be called on purpose, in whatever order the story wants (see
CLAUDE.md, "The feel we're going for"). But each terminal call is a fresh
Python process, so something has to hold party/clock/purse state *between*
calls. That's all this file does: a thin CLI over rpg.py's functions,
sites.py's content, and quests.py's generated world, with state written to
save.json between invocations. It adds no game logic of its own;
`python session.py --help` lists every subcommand, and each subcommand's
--help carries its full rules. The play protocol (who decides what, one
encounter per message, narration style) lives in dm.md.

THE SAVE IS A PLAIN JSON FILE (save.json, beside this script) on purpose:
  - it survives sessions and machines -- commit it and the playthrough
    travels with the repo;
  - it is the DM's OVERRIDE SURFACE: when the story needs what no command
    provides (grant gold, mend a wound, invent a foe's aftermath), edit the
    file directly between commands -- every command reloads it fresh.
    Weapons are stored by catalog name ("weapon": "katana"); everything
    else is the literal field. The "rng" blob is the one part not meant
    for hands.

The first hero rolled (party[0]) is the PLAYER CHARACTER; the rest are
companions. PC death ends the game even if a companion stands.

The shape of a playthrough:
  new / status / levelup                    -- rolling and reading the party
  board / show QID / take QID / room        -- the quest board (the game)
  hideout ROOM / barrow ROOM / fight N      -- the set sites & off-script
  resume [...] / retreat                    -- settle a paused fight
  rest / camp / award / buy / give / train / use / heal
                                            -- the between-fights layer
  forge                                     -- DM-built quest, off the board
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import random
from pathlib import Path

from rpg import (
    Clock, CombatLog, Purse, Entity, Weapon, POTION_KINDS, WEAPONS,
    ENCOUNTER_XP, TRAINING_MAX, PROFICIENCY_MAX,
    STAMINA_DRAUGHT_RESTORE, PAUSE_ACTION_DEF_PENALTY,
    BERSERK_HP_COST, BERSERK_STA_GAIN,
    WAR_BREATH_POWER_COST, WAR_BREATH_STA_GAIN,
    make_party, stat_line, progress_line, fallen_weapons_line,
    xp_to_next, site_encounter_xp, site_clear_xp, site_gold,
    start_fight, group_combat, party_wiped,
    attempt_retreat, refresh_foes_after_retreat,
    award_xp, roll_loot, award_quest,
    short_rest as _short_rest, long_rest as _long_rest,
    buy_potion as _buy_potion, use_heal as _use_heal,
    use_potion as _use_potion, buy_weapon as _buy_weapon,
    equip_weapon as _equip_weapon,
    train_combat_once as _train_combat_once,
    train_proficiency as _train_proficiency,
)
from sites import SITES, FOES, BANDIT_KINDS, WEAPON_INDEX, make_foe, roster_lines
from quests import (generate_world, forge_quest, board_lines,
                    quest_detail_lines, quest_line)

STATE_PATH = Path(__file__).parent / "save.json"

# Off-script foe kinds (`fight N --type ...`): any catalog kind by name, or
# "bandit" for a random living foe from the bandit pool.
FIGHT_TYPES = ("bandit",) + tuple(sorted(FOES))


def _spawn_foe(kind: str, rng, n: int):
    if kind == "bandit":
        kind = rng.choice(BANDIT_KINDS)
    return make_foe(kind, n, rng)


# --------------------------------------------------------------------------- #
# The save file (JSON in, JSON out; see the module docstring)
# --------------------------------------------------------------------------- #

def _weapon_ref(w: Weapon | None):
    """A weapon serializes as its catalog name when it IS the catalog entry
    (the hand-editable normal case); a one-off instance serializes whole."""
    if w is None:
        return None
    if WEAPON_INDEX.get(w.name) == w:
        return w.name
    return dataclasses.asdict(w)


def _weapon_from(ref) -> Weapon | None:
    if ref is None:
        return None
    if isinstance(ref, str):
        return WEAPON_INDEX[ref]
    ref = dict(ref)
    ref["tags"] = tuple(ref.get("tags", ()))
    return Weapon(**ref)


def _entity_to_dict(e: Entity) -> dict:
    d = dataclasses.asdict(e)
    d["weapon"] = _weapon_ref(e.weapon)
    return d


def _entity_from_dict(d: dict) -> Entity:
    d = dict(d)
    d["weapon"] = _weapon_from(d["weapon"])
    e = Entity(**d)
    # __post_init__ resets the live tracks to full; restore the saved state.
    e.hp = d["hp"]
    e.cur_sta = d["cur_sta"]
    e.cur_power = d["cur_power"]
    return e


def _pending_to_dict(pending: dict | None, party: list) -> dict | None:
    if pending is None:
        return None
    return {
        "foes": [_entity_to_dict(f) for f in pending["foes"]],
        "fired": [[kind, h.name] for kind, h in pending["fired"]],
        "round": pending["round"],
        "crossings": [list(c) for c in pending["crossings"]],
        "xp": pending["xp"],
        "site": pending["site"],
        "room": pending["room"],
        "quest": pending.get("quest"),
    }


def _pending_from_dict(d: dict | None, party: list) -> dict | None:
    if d is None:
        return None
    by_name = {h.name: h for h in party}
    return {
        "foes": [_entity_from_dict(f) for f in d["foes"]],
        "fired": {(kind, by_name[name]) for kind, name in d["fired"]},
        "round": d["round"],
        "crossings": [tuple(c) for c in d["crossings"]],
        "xp": d["xp"],
        "site": d["site"],
        "room": d["room"],
        "quest": d.get("quest"),
    }


def save(state: dict) -> None:
    party = state["party"]
    rng_version, rng_internal, rng_gauss = state["rng"].getstate()
    doc = {
        "party": [_entity_to_dict(h) for h in party],
        "clock": {"day": state["clock"].day,
                  "short_rests_used": state["clock"].short_rests_used},
        "purse": {"gold": state["purse"].gold},
        "foe_count": state["foe_count"],
        "active_quest": state.get("active_quest"),
        "world": state.get("world"),
        "pending": _pending_to_dict(state.get("pending"), party),
        "rooms": {f"{site}#{room}": {"foes": [_entity_to_dict(f)
                                              for f in rec["foes"]],
                                     "day": rec["day"]}
                  for (site, room), rec in state.get("rooms", {}).items()},
        "rng": [rng_version, list(rng_internal), rng_gauss],
    }
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)
        f.write("\n")


def load() -> dict:
    with open(STATE_PATH, encoding="utf-8") as f:
        doc = json.load(f)
    party = [_entity_from_dict(d) for d in doc["party"]]
    rng = random.Random()
    v, internal, gauss = doc["rng"]
    rng.setstate((v, tuple(internal), gauss))
    rooms = {}
    for key, rec in doc.get("rooms", {}).items():
        site, room = key.rsplit("#", 1)
        rooms[(site, int(room))] = {
            "foes": [_entity_from_dict(f) for f in rec["foes"]],
            "day": rec["day"]}
    return {
        "party": party,
        "clock": Clock(**doc["clock"]),
        "purse": Purse(**doc["purse"]),
        "rng": rng,
        "foe_count": doc["foe_count"],
        "active_quest": doc.get("active_quest"),
        "world": doc.get("world"),
        "pending": _pending_from_dict(doc.get("pending"), party),
        "rooms": rooms,
    }


def role_tag(party: list, h) -> str:
    """party[0] is the player character; the rest are companions (see dm.md)."""
    return "(YOU)      " if h is party[0] else "(companion)"


def find_hero(party: list, name: str):
    """Substring hero lookup, None (with a message) instead of a crash."""
    for h in party:
        if name.lower() in h.name.lower():
            return h
    print(f"No hero matches {name!r}. Party: "
          + ", ".join(h.name for h in party))
    return None


def print_combat(log: CombatLog) -> None:
    """Print the full (DM/debug) log, then the simplified player-facing block
    -- the piece meant to be pasted into the chat as-is (see rules.md,
    "Reading the combat log")."""
    print("\n".join(log))
    if log.player:
        print()
        print("--- PLAYER LOG (paste into chat as-is) ---")
        print("\n".join(log.player))


def require_no_pending(state: dict) -> bool:
    """Most commands are between-fights actions; refuse them mid-melee."""
    if state.get("pending"):
        print("A fight is PAUSED -- the party is mid-melee. Resolve it "
              "first: resume [--drink HERO] [--berserk HERO] "
              "[--warbreath HERO], or retreat.")
        return False
    return True


def cmd_new(args: argparse.Namespace) -> None:
    rng = random.Random(args.seed)
    party = make_party(rng)
    world_seed = rng.randrange(1 << 30)     # derived, so --seed pins the
                                            # whole playthrough, world and all
    world = generate_world(world_seed)
    state = {"party": party, "clock": Clock(), "purse": Purse(), "rng": rng,
             "foe_count": 0, "pending": None, "rooms": {},
             "world": world, "active_quest": None}
    save(state)
    print(f"New party rolled (seed={args.seed}):")
    for h in party:
        print(f"  {role_tag(party, h)} " + stat_line(h))
    print(f"The player character is {party[0].name} -- if they die, game over.")
    names = ", ".join(f"{s['name']} ({s['race']} {s['kind']})"
                      for s in world["settlements"])
    print(f"The world holds {len(world['quests'])} posted quests across: "
          f"{names}. See them with `board`.")


def cmd_status(args: argparse.Namespace) -> None:
    state = load()
    party, clock, purse = state["party"], state["clock"], state["purse"]
    print(f"Day {clock.day}, {clock.short_rests_left} short rest(s) left today. "
          f"Purse: {purse.gold}g.")
    for h in party:
        tag = " [DEAD]" if h.dead else " [DOWN]" if h.down else ""
        print(f"  {role_tag(party, h)} " + stat_line(h) + tag)
        print(" " * 14 + progress_line(h))
    world = state.get("world")
    if world:
        open_q = sum(1 for q in world["quests"].values()
                     if q["status"] == "open")
        print(f"  Board: {open_q} open quest(s) across "
              f"{len(world['settlements'])} settlement(s) -- see `board`.")
    qid = state.get("active_quest")
    if qid:
        q = world["quests"][qid]
        if q["status"] == "done":
            print(f"  Active quest [{qid}] {q['name']} is COMPLETE -- "
                  f"take a new one.")
        else:
            cur = q["next"]
            s = q["sites"][cur["site"]]
            print(f"  Active quest: [{qid}] L{q['level']} {q['name']} -- "
                  f"next: {s['name']} (L{s['level']}), room "
                  f"{cur['room'] + 1}/{len(s['rooms'])}. Fight it with `room`.")
    for (site, room), rec in sorted(state.get("rooms", {}).items()):
        standing = sum(1 for f in rec["foes"] if not f.dead)
        print(f"  Unfinished: {site} room {room} -- {standing} foe(s) still "
              f"hold it (fled day {rec['day']})")
    if state.get("pending"):
        print()
        print_pause_menu(state)


def print_pause_menu(state: dict) -> None:
    """The DM-facing pause menu: who tripped it, the board, and every option
    with its real cost -- presented, like `levelup`, instead of paraphrased."""
    pending = state["pending"]
    party = state["party"]
    what = {"stamina": "is nearly out of breath",
            "wounds": "is badly cut up"}
    trips = "; ".join(f"{name} {what[kind]}"
                      for kind, name in pending["crossings"])
    print(f"*** FIGHT PAUSED (after round {pending['round']}): {trips}. ***")
    standing = [f for f in pending["foes"] if f.alive]
    print("  Facing: " + ", ".join(
        f"{f.name} {f.hp}/{f.max_hp} HP" for f in standing))
    for h in party:
        if h.dead:
            continue
        tag = " [DOWN]" if h.down else ""
        print(f"  {h.name}{tag}: STA {h.cur_sta}/{h.sta}  HP {h.hp}/{h.max_hp}"
              f"  Power {h.cur_power}/{h.power}  "
              f"stamina draughts x{h.items.get('stamina', 0)}")
    print("  The player's call (pause actions cost that round's attack and "
          f"defend at -{PAUSE_ACTION_DEF_PENALTY}):")
    print("    resume                    -- fight on")
    print(f"    resume --drink HERO       -- stamina draught, "
          f"+{STAMINA_DRAUGHT_RESTORE} STA now")
    print(f"    resume --berserk HERO     -- {BERSERK_HP_COST} HP -> "
          f"+{BERSERK_STA_GAIN} STA (the wound penalty deepens)")
    print(f"    resume --warbreath HERO   -- {WAR_BREATH_POWER_COST} Power -> "
          f"+{WAR_BREATH_STA_GAIN} STA")
    print("    retreat                   -- parting blows from foes still "
          "fit to swing, then one group chase roll"
          + (" (the dead do not pursue past their ground)"
             if any(f.alive and not f.pursues for f in pending["foes"])
             else ""))


def cmd_levelup(args: argparse.Namespace) -> None:
    """The spending menu: what each hero's banked skill points can buy right
    now, with costs and effects -- the DM presents this to the player whenever
    points are unspent (dm.md), instead of paraphrasing the rules from memory."""
    state = load()
    party = state["party"]
    for h in party:
        if h.dead:
            continue
        first = h.name.split()[0]
        print(f"{h.name} -- L{h.level}, {h.skill_points} skill point(s) banked "
              f"(XP {h.xp}/{xp_to_next(h.level)} to L{h.level + 1})")
        # Sink 1: combat training (+1 to ALL pressure rolls per rank).
        if h.training >= TRAINING_MAX:
            print(f"  combat training      rank {h.training} -- CAPPED")
        else:
            cost = h.training + 1
            mark = "CAN BUY" if h.skill_points >= cost else "can't afford yet"
            print(f"  combat training      rank {h.training} -> "
                  f"{h.training + 1}  costs {cost}  [{mark}]  "
                  f"(+1 to ALL pressure rolls per rank, cap {TRAINING_MAX})"
                  f"  -> train {first} combat")
        # Sink 2: proficiency with the WIELDED weapon.
        if h.weapon is None or h.weapon_broken:
            print("  weapon proficiency   (no whole weapon in hand to drill)")
        else:
            rank = h.proficiency.get(h.weapon.name, 0)
            if rank >= PROFICIENCY_MAX:
                print(f"  {h.weapon.name} proficiency  rank {rank} -- CAPPED")
            else:
                cost = rank + 1
                mark = ("CAN BUY" if h.skill_points >= cost
                        else "can't afford yet")
                print(f"  {h.weapon.name} proficiency  rank {rank} -> "
                      f"{rank + 1}  costs {cost}  [{mark}]  "
                      f"(+1 atk pressure & +1 severity with it, cap "
                      f"{PROFICIENCY_MAX}; lost on weapon switch)"
                      f"  -> train {first} weapon")
        other = {n: r for n, r in h.proficiency.items()
                 if r and (h.weapon is None or n != h.weapon.name)}
        if other:
            dormant = ", ".join(f"{n} {r}" for n, r in sorted(other.items()))
            print(f"  (drilled but not in hand: {dormant})")


def resolve_encounter(state: dict, log: list[str], foes: list,
                      encounter_xp: int, site: str | None = None,
                      room: int | None = None,
                      quest: str | None = None) -> None:
    """Shared tail of every encounter command: run the melee -- which may
    PAUSE at a trigger (STA <= 2 / half HP, once each) -- then award and
    persist. On a pause the fight is saved as `pending` and the turn goes
    back to the player (resume / retreat next message). `quest` ties the
    encounter to a board quest: clearing the room advances its cursor."""
    party, rng = state["party"], state["rng"]
    living = [h for h in party if not h.dead]
    fired: set[str] = set()
    pause = group_combat(living, foes, rng, log, pause_triggers=True,
                         fired=fired)
    if pause is not None:
        state["pending"] = {
            "foes": foes, "xp": encounter_xp, "site": site, "room": room,
            "quest": quest, "fired": fired, "round": pause.round,
            "crossings": [(k, h.name) for k, h in pause.crossings],
        }
        print_combat(log)
        print()
        print_pause_menu(state)
        save(state)
        return
    finish_encounter(state, log, foes, encounter_xp, site=site, room=room,
                     quest=quest)


def advance_quest(state: dict, log: list[str], qid: str) -> None:
    """The active quest's cleared room: move the cursor. Finishing a site
    pays its clear lump + gold (each site pays its own way -- the level IS
    the pay grade); finishing the last site closes the quest."""
    quest = state["world"]["quests"][qid]
    party, purse = state["party"], state["purse"]
    cur = quest["next"]
    site = quest["sites"][cur["site"]]
    cur["room"] += 1
    if cur["room"] < len(site["rooms"]):
        return
    n_rooms = len(site["rooms"])
    last_site = cur["site"] == len(quest["sites"]) - 1
    banner = "QUEST COMPLETE" if last_site else "SITE CLEARED"
    award_quest(party, purse, site_gold(site["level"]),
                site_clear_xp(site["level"], n_rooms), log,
                f"{quest['name']} -- {site['name']}", banner=banner)
    cur["site"] += 1
    cur["room"] = 0
    if last_site:
        quest["status"] = "done"
    else:
        nxt = quest["sites"][cur["site"]]
        log.append(f"  (next: {nxt['name']}, L{nxt['level']}, "
                   f"{len(nxt['rooms'])} encounter(s))")


def finish_encounter(state: dict, log: list[str], foes: list,
                     encounter_xp: int, site: str | None = None,
                     room: int | None = None,
                     quest: str | None = None) -> None:
    """The melee actually ended: wipe check, awards, loot, persist."""
    party, purse, rng = state["party"], state["purse"], state["rng"]
    state["pending"] = None
    wiped = party_wiped(party, log)
    if not wiped and any(f.alive for f in foes):
        # Unresolved (the fight staggered apart, both sides spent): no award.
        log.append("  The encounter is not cleared -- the foes still stand.")
        if site is not None:
            # A site room keeps its survivors (same rule as a retreat) --
            # re-running the room faces them again, not a fresh spawn.
            state.setdefault("rooms", {})[(site, room)] = {
                "foes": foes, "day": state["clock"].day}
            standing = sum(1 for f in foes if f.alive)
            log.append(f"  ({site} room {room} is left to its {standing} "
                       f"standing foe(s) -- it will remember)")
    elif not wiped:
        award_xp(party, encounter_xp, log, "encounter")
        roll_loot(party, purse, rng, log)
        weapons_left = fallen_weapons_line(foes)
        if weapons_left:
            log.append(weapons_left)
        if quest is not None:
            advance_quest(state, log, quest)

    print_combat(log)
    save(state)
    report_game_over(party, wiped)


def cmd_fight(args: argparse.Namespace) -> None:
    state = load()
    if not require_no_pending(state):
        return
    party, rng = state["party"], state["rng"]
    log = CombatLog()
    for h in [h for h in party if not h.dead]:
        start_fight(h, log)

    foes = []
    for _ in range(args.n):
        state["foe_count"] += 1
        foes.append(_spawn_foe(args.type, rng, state["foe_count"]))
    for line in roster_lines(foes):
        log.append("  " + line)

    # Off-script fights pay the base (starter-site) rate regardless of foe --
    # the DM adjusts via `quest` if a scene deserves more.
    resolve_encounter(state, log, foes, ENCOUNTER_XP)


def reclaim_room(state: dict, site: str, room: int) -> tuple[list, str] | None:
    """If the party once fled this room, its survivors are still there:
    STA refreshed the moment the party left; living foes healed if a day has
    passed; the undead still hacked (dead bone doesn't knit). Returns the
    readied foes and a log note, or None if the room has no record."""
    rec = state.setdefault("rooms", {}).pop((site, room), None)
    if rec is None:
        return None
    days = state["clock"].day - rec["day"]
    foes = refresh_foes_after_retreat(rec["foes"], days)
    standing = sum(1 for f in foes if f.alive)
    healed = days > 0 and any(not f.undead for f in foes)
    note = (f"  (the survivors of the earlier fight still hold it: "
            f"{standing} standing{' -- rested and healed' if healed else ''})")
    return foes, note


def cmd_site(args: argparse.Namespace) -> None:
    """Resolve one room of a SET site (hideout/barrow -- args.site carries
    the key). Fresh rooms spawn the authored roster; a room the party fled
    (or left standing) is re-fought against its recorded survivors."""
    state = load()
    if not require_no_pending(state):
        return
    party, rng = state["party"], state["rng"]
    site = SITES[args.site]
    log = CombatLog()
    for h in [h for h in party if not h.dead]:
        start_fight(h, log)

    room_name, roster = site.rooms[args.room - 1]
    held = reclaim_room(state, site.key, args.room)
    banner = f"=== {site.key.capitalize()} room {args.room}: {room_name}"
    if held is None:
        spawn = site.spawn_phrase.format(n=len(roster))
        log.append(f"{banner} ({spawn}) ===")
        foes = []
        for kind in roster:
            state["foe_count"] += 1
            foes.append(make_foe(kind, state["foe_count"], rng))
        for line in roster_lines(foes):
            log.append("  " + line)
    else:
        foes, note = held
        log.append(f"{banner}, again ===")
        log.append(note)
        for line in roster_lines([f for f in foes if f.alive]):
            log.append("  " + line)

    resolve_encounter(state, log, foes, site.encounter_xp,
                      site=site.key, room=args.room)


def _get_quest(world: dict, ref: str) -> dict | None:
    """Quest lookup by id, forgiving about the exact spelling (q7 / q07 / 7)."""
    ref = ref.lower().lstrip("q")
    for qid, quest in world["quests"].items():
        if qid.lstrip("q").lstrip("0") == ref.lstrip("0"):
            return quest
    print(f"No quest {ref!r} on the board. See `board`.")
    return None


def cmd_board(args: argparse.Namespace) -> None:
    state = load()
    world = state.get("world")
    if not world:
        print("No world in this save -- start one with `new`.")
        return
    key = None
    if args.settlement:
        want = args.settlement.lower()
        match = [s for s in world["settlements"] if want in s["key"]]
        if not match:
            print(f"No settlement matches {args.settlement!r}. Settlements: "
                  + ", ".join(s["name"] for s in world["settlements"]))
            return
        key = match[0]["key"]
    for line in board_lines(world, key):
        print(line)
    if state.get("active_quest"):
        print(f"(active quest: {state['active_quest']})")


def cmd_show(args: argparse.Namespace) -> None:
    state = load()
    quest = _get_quest(state["world"], args.quest)
    if quest is None:
        return
    for line in quest_detail_lines(quest):
        print(line)


def cmd_take(args: argparse.Namespace) -> None:
    state = load()
    if not require_no_pending(state):
        return
    quest = _get_quest(state["world"], args.quest)
    if quest is None:
        return
    if quest["status"] == "done":
        print(f"[{quest['id']}] {quest['name']} is already complete.")
        return
    state["active_quest"] = quest["id"]
    save(state)
    print(f"The party takes the job: {quest_line(quest)}")
    for line in quest_detail_lines(quest)[1:]:
        print(line)
    print("Fight the next room with `room`. Switching quests later keeps "
          "this one's progress.")


def cmd_room(args: argparse.Namespace) -> None:
    """Resolve the active quest's next encounter (the board-quest sibling of
    `hideout ROOM` / `barrow ROOM`). Rooms come in order -- the cursor is the
    quest's memory; a room the party fled is re-fought against its recorded
    survivors, same rule as the set sites."""
    state = load()
    if not require_no_pending(state):
        return
    qid = state.get("active_quest")
    if not qid:
        print("No active quest. Pick one: `board`, then `take QID`.")
        return
    quest = state["world"]["quests"][qid]
    if quest["status"] == "done":
        print(f"[{qid}] {quest['name']} is complete -- take a new quest.")
        return
    party, rng = state["party"], state["rng"]
    cur = quest["next"]
    site = quest["sites"][cur["site"]]
    room_i = cur["room"]
    room_name, kinds = site["rooms"][room_i]
    site_key = f"{qid}/s{cur['site'] + 1}"

    log = CombatLog()
    for h in [h for h in party if not h.dead]:
        start_fight(h, log)

    held = reclaim_room(state, site_key, room_i + 1)
    banner = (f"=== {quest['name']} -- {site['name']} (L{site['level']}), "
              f"room {room_i + 1}/{len(site['rooms'])}: {room_name}")
    if held is None:
        log.append(banner + " ===")
        foes = []
        for kind in kinds:
            state["foe_count"] += 1
            foes.append(make_foe(kind, state["foe_count"], rng,
                                 display=quest["skins"].get(kind)))
        for line in roster_lines(foes):
            log.append("  " + line)
    else:
        foes, note = held
        log.append(banner + ", again ===")
        log.append(note)
        for line in roster_lines([f for f in foes if f.alive]):
            log.append("  " + line)

    resolve_encounter(state, log, foes,
                      site_encounter_xp(site["level"], len(site["rooms"])),
                      site=site_key, room=room_i + 1, quest=qid)


def cmd_forge(args: argparse.Namespace) -> None:
    """The DM's quest creator: build a quest by the generator's own rules
    (level in, rosters out) for scenes the board doesn't cover, and post it
    to a settlement's board like any other quest."""
    state = load()
    if not require_no_pending(state):
        return
    world = state.get("world")
    if not world:
        print("No world in this save -- start one with `new`.")
        return
    kinds = tuple(k.strip() for k in args.kinds.split(","))
    unknown = [k for k in kinds if k not in FOES]
    if unknown:
        print(f"Unknown foe kind(s): {', '.join(unknown)}. "
              f"Catalog: {', '.join(sorted(FOES))}.")
        return
    settlement = world["settlements"][0]
    if args.settlement:
        want = args.settlement.lower()
        match = [s for s in world["settlements"] if want in s["key"]]
        if not match:
            print(f"No settlement matches {args.settlement!r}.")
            return
        settlement = match[0]
    qid = f"q{len(world['quests']) + 1:02d}"
    quest = forge_quest(qid, args.level, args.sites, args.rooms, kinds,
                        args.name, state["rng"],
                        settlement_key=settlement["key"])
    world["quests"][qid] = quest
    settlement["quests"].append(qid)
    save(state)
    print(f"Forged and posted at {settlement['name']}:")
    for line in quest_detail_lines(quest):
        print(line)


def report_game_over(party: list, wiped: bool) -> None:
    """The two run-ending states: a total wipe, or the player character slain
    (party[0] is the PC -- see dm.md; the companion surviving doesn't save the
    game)."""
    if wiped:
        print("\n*** RUN OVER: total party wipe. GAME OVER. ***")
    elif party[0].dead:
        print(f"\n*** {party[0].name} -- the player character -- is slain. "
              f"GAME OVER. ***")


def cmd_resume(args: argparse.Namespace) -> None:
    """Continue the paused fight, with optional pause actions (one per hero:
    drink / berserk / warbreath -- each costs that round's attack and defends
    at -2). Invalid requests abort BEFORE the fight moves, so the DM can
    correct the call; a valid resume runs to the next pause or the end."""
    state = load()
    pending = state.get("pending")
    if not pending:
        print("No paused fight to resume.")
        return
    party, rng = state["party"], state["rng"]
    living = [h for h in party if not h.dead]

    actions: dict = {}
    for flag, action in (("drink", "drink"), ("berserk", "berserk"),
                         ("warbreath", "war-breath")):
        for name in getattr(args, flag) or []:
            hero = find_hero(party, name)
            if hero is None:
                return
            if not hero.alive:
                print(f"{hero.name} is not on their feet -- no pause action.")
                return
            if hero in actions:
                print(f"{hero.name} can only take ONE pause action.")
                return
            if action == "drink" and hero.items.get("stamina", 0) <= 0:
                print(f"{hero.name} carries no stamina draught.")
                return
            if action == "berserk" and hero.hp <= BERSERK_HP_COST:
                print(f"{hero.name} is too torn up to Berserk "
                      f"(HP {hero.hp}, must survive the {BERSERK_HP_COST}).")
                return
            if action == "war-breath" and hero.cur_power < WAR_BREATH_POWER_COST:
                print(f"{hero.name} lacks the Power for War-Breath "
                      f"({hero.cur_power}/{WAR_BREATH_POWER_COST}).")
                return
            actions[hero] = action

    log = CombatLog()
    pause = group_combat(living, pending["foes"], rng, log,
                         pause_triggers=True, fired=pending["fired"],
                         first_round=pending["round"] + 1,
                         actions=actions or None)
    if pause is not None:
        pending["round"] = pause.round
        pending["crossings"] = [(k, h.name) for k, h in pause.crossings]
        print_combat(log)
        print()
        print_pause_menu(state)
        save(state)
        return
    finish_encounter(state, log, pending["foes"], pending["xp"],
                     site=pending["site"], room=pending["room"],
                     quest=pending.get("quest"))


def cmd_retreat(args: argparse.Namespace) -> None:
    """Break away from the paused fight: parting blows from every foe still
    fit to swing, then ONE opposed group chase roll (the barrow's undead never
    pursue past the door). A clean escape leaves the room to its survivors --
    recorded, so re-running the room resumes against them (STA refreshed;
    living foes heal over a day; bones stay hacked). A failed break resumes
    the fight on the spot."""
    state = load()
    pending = state.get("pending")
    if not pending:
        print("No paused fight to retreat from.")
        return
    party, rng, clock = state["party"], state["rng"], state["clock"]
    living = [h for h in party if not h.dead]
    log = CombatLog()

    escaped = attempt_retreat(living, pending["foes"], rng, log)
    wiped = party_wiped(party, log)
    if wiped or escaped:
        state["pending"] = None
        if escaped and not wiped:
            site, room = pending["site"], pending["room"]
            if site is not None:
                state.setdefault("rooms", {})[(site, room)] = {
                    "foes": pending["foes"], "day": clock.day}
                standing = sum(1 for f in pending["foes"] if f.alive)
                log.append(f"  ({site} room {room} is left to its "
                           f"{standing} standing foe(s) -- it will remember)")
            else:
                log.append("  (the foes scatter -- an off-script encounter "
                           "is not kept)")
        print_combat(log)
        save(state)
        report_game_over(party, wiped)
        return

    # Run down: the fight resumes at once, the parting damage already taken.
    pause = group_combat(living, pending["foes"], rng, log,
                         pause_triggers=True, fired=pending["fired"],
                         first_round=pending["round"] + 1)
    if pause is not None:
        pending["round"] = pause.round
        pending["crossings"] = [(k, h.name) for k, h in pause.crossings]
        print_combat(log)
        print()
        print_pause_menu(state)
        save(state)
        return
    finish_encounter(state, log, pending["foes"], pending["xp"],
                     site=pending["site"], room=pending["room"],
                     quest=pending.get("quest"))


def cmd_rest(args: argparse.Namespace) -> None:
    state = load()
    if not require_no_pending(state):
        return
    party, clock = state["party"], state["clock"]
    log: list[str] = []
    _short_rest([h for h in party if h.alive], clock, log)
    print("\n".join(log) if log else "(nothing happened)")
    save(state)


def cmd_camp(args: argparse.Namespace) -> None:
    state = load()
    if not require_no_pending(state):
        return
    party, clock = state["party"], state["clock"]
    log: list[str] = []
    _long_rest(party, clock, log)
    print("\n".join(log))
    save(state)


def cmd_award(args: argparse.Namespace) -> None:
    state = load()
    if not require_no_pending(state):
        return
    party, purse = state["party"], state["purse"]
    log: list[str] = []
    award_quest(party, purse, args.gold, args.xp, log, args.name)
    print("\n".join(log))
    save(state)


def cmd_buy(args: argparse.Namespace) -> None:
    state = load()
    if not require_no_pending(state):
        return
    party, purse = state["party"], state["purse"]
    log: list[str] = []
    hero = find_hero(party, args.hero)
    if hero is None:
        return
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
    if not require_no_pending(state):
        return
    party = state["party"]
    log: list[str] = []
    hero = find_hero(party, args.hero)
    if hero is None:
        return
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
    if not require_no_pending(state):
        return
    party = state["party"]
    log: list[str] = []
    hero = find_hero(party, args.hero)
    if hero is None:
        return
    if args.what == "combat":
        _train_combat_once(hero, log)
    else:
        _train_proficiency(hero, log)
    print("\n".join(log))
    save(state)


def cmd_use(args: argparse.Namespace) -> None:
    state = load()
    if not require_no_pending(state):
        return
    party = state["party"]
    log: list[str] = []
    hero = find_hero(party, args.hero)
    if hero is None:
        return
    _use_potion(hero, args.kind, log)
    print("\n".join(log))
    save(state)


def cmd_heal(args: argparse.Namespace) -> None:
    state = load()
    if not require_no_pending(state):
        return
    party, rng = state["party"], state["rng"]
    log: list[str] = []
    healer = find_hero(party, args.healer)
    if healer is None:
        return
    target = find_hero(party, args.target)
    if target is None:
        return
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
        "levelup",
        help="the skill-point spending menu: each hero's banked points and "
             "what they can buy (present this to the player whenever points "
             "are unspent)")
    p.set_defaults(func=cmd_levelup)

    p = sub.add_parser(
        "barrow",
        help="resolve one skeleton-barrow room (SET rooms from "
             "sites.BARROW_ROOMS -- the TOUGH site, 3x pay)")
    p.add_argument("room", type=int,
                   choices=range(1, len(SITES["barrow"].rooms) + 1))
    p.set_defaults(func=cmd_site, site="barrow")

    p = sub.add_parser(
        "hideout",
        help="resolve one bandit-hideout room (SET rooms from "
             "sites.HIDEOUT_ROOMS -- the STARTER site)")
    p.add_argument("room", type=int,
                   choices=range(1, len(SITES["hideout"].rooms) + 1))
    p.set_defaults(func=cmd_site, site="hideout")

    p = sub.add_parser(
        "fight",
        help="OFF-SCRIPT encounter: spawn N foes (improvised scenes like road "
             "ambushes only -- the two sites are set encounters, use "
             "barrow/hideout). Pays the base 15 XP regardless of foe; award "
             "extra via `quest` if the scene deserves it.")
    p.add_argument("n", type=int, help="how many foes to spawn for this encounter")
    p.add_argument("--type", default="skeleton", choices=list(FIGHT_TYPES),
                   help="a catalog foe kind, or 'bandit' for a random "
                        "living foe")
    p.set_defaults(func=cmd_fight)

    p = sub.add_parser(
        "resume",
        help="continue a PAUSED fight, optionally with pause actions (one "
             "per hero; each costs that round's attack and defends at -2): "
             "--drink HERO (stamina draught), --berserk HERO (HP -> STA), "
             "--warbreath HERO (Power -> STA). Plain resume = fight on.")
    p.add_argument("--drink", action="append", metavar="HERO")
    p.add_argument("--berserk", action="append", metavar="HERO")
    p.add_argument("--warbreath", action="append", metavar="HERO")
    p.set_defaults(func=cmd_resume)

    p = sub.add_parser(
        "retreat",
        help="break away from a PAUSED fight: parting blows from foes fit "
             "to swing, then ONE group chase roll. A fled site room keeps "
             "its survivors; re-run the room to face them again.")
    p.set_defaults(func=cmd_retreat)

    p = sub.add_parser("rest", help="short rest: spends a daily slot for a small catch-breath")
    p.set_defaults(func=cmd_rest)

    p = sub.add_parser("camp", help="long rest: full STA, weekly HP tick, advances a day")
    p.set_defaults(func=cmd_camp)

    p = sub.add_parser(
        "board",
        help="the quest board: every settlement's posted quests with level "
             "(shown straight -- too easy and too hard both happen), shape, "
             "and pay. Optionally filter to one settlement.")
    p.add_argument("settlement", nargs="?", default=None)
    p.set_defaults(func=cmd_board)

    p = sub.add_parser(
        "show",
        help="one quest in full: description, sites, rooms, and what holds "
             "each room (by skinned display name)")
    p.add_argument("quest", help="quest id (q07, or just 7)")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser(
        "take",
        help="make a board quest the ACTIVE quest; `room` then fights its "
             "encounters in order. Switching quests keeps the old one's "
             "progress -- come back to it whenever.")
    p.add_argument("quest", help="quest id (q07, or just 7)")
    p.set_defaults(func=cmd_take)

    p = sub.add_parser(
        "room",
        help="resolve the ACTIVE quest's next encounter (the board-quest "
             "sibling of `hideout ROOM`). Clearing a site pays its lump; "
             "clearing the last site completes the quest. A fled room is "
             "re-fought against its recorded survivors.")
    p.set_defaults(func=cmd_room)

    p = sub.add_parser(
        "forge",
        help="DM quest creator: generate a quest at a level/shape/foe-mix of "
             "your choosing (same builder as worldgen) and post it to a "
             "settlement's board. For scenes the board doesn't cover.")
    p.add_argument("--level", type=int, required=True)
    p.add_argument("--sites", type=int, default=1, choices=(1, 2, 3))
    p.add_argument("--rooms", type=int, default=2, choices=(1, 2, 3),
                   help="rooms per site")
    p.add_argument("--kinds", required=True,
                   help="comma-separated catalog foe kinds (the quest's pool)")
    p.add_argument("--name", required=True)
    p.add_argument("--settlement", default=None,
                   help="where to post it (default: the capital)")
    p.set_defaults(func=cmd_forge)

    p = sub.add_parser(
        "award",
        help="off-script bonus: award gold + an XP lump by hand (board "
             "quests pay themselves -- this is for improvised scenes)")
    p.add_argument("gold", type=int)
    p.add_argument("xp", type=int)
    p.add_argument("name")
    p.set_defaults(func=cmd_award)

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
        help="spend a banked skill point: 'combat' = +1 to all pressure rolls "
             "per rank (cap 5); 'weapon' = proficiency with the WIELDED "
             "weapon, +1 attack pressure & +1 severity per rank (cap 3). "
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
