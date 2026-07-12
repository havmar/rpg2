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

party[0] is the PLAYER CHARACTER (chosen from three at `new`/`pick`; the
rest are hired companions). PC death ends the game even if a companion
stands. CHA gates how many companions the party can hold; every companion
carries a satisfaction track and quits (with a head-split of the purse) if
it hits bottom -- see rules.md's Party, Charisma & Satisfaction add-on.

The shape of a playthrough:
  new / pick / status / levelup             -- choosing and reading the party
  recruit / hire NAME / dismiss NAME        -- the tavern's hiring layer
  map / travel / explore / hunt / engage    -- the world & the wilds
  board / show QID / take QID / room        -- the LOCAL jobs (the game;
                                               board = the DM inventory,
                                               in play quests come from
                                               their GIVERS -- dm.md)
  chatter                                   -- a party-flavor seed (dm.md)
  hideout ROOM / barrow ROOM / fight N      -- the set sites & off-script
  resume [...] / retreat                    -- settle a paused fight
  rest / camp / tavern / downtime / award / buy / give / train / use / heal
                                            -- the between-fights layer
  forge                                     -- DM-built quest, off the board
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import random
import subprocess
from pathlib import Path

from rpg import (
    Clock, CombatLog, Purse, Entity, Weapon, POTION_KINDS, WEAPONS,
    ENCOUNTER_XP, TRAINING_MAX, PROFICIENCY_MAX,
    STAMINA_DRAUGHT_RESTORE, HEALING_POTION_RESTORE,
    PAUSE_ACTION_DEF_PENALTY,
    KIT_HEALING, KIT_STAMINA,
    TAVERN_COST_PER_HERO, TAVERN_OVERCHARGE,
    BERSERK_HP_COST, BERSERK_STA_GAIN,
    WAR_BREATH_POWER_COST, WAR_BREATH_STA_GAIN,
    standing_order,
    SATISFACTION_START, SAT_DOWNTIME, SAT_DOWNTIME_MATCH,
    MEDS_INTERVAL_DAYS, MEDS_PRICE,
    party_capacity, has_trait, satisfaction_tracked, wants_to_leave,
    adjust_satisfaction, satisfaction_after_fight,
    stat_line, progress_line, fallen_weapons_line,
    xp_to_next, site_encounter_xp, site_clear_xp, site_gold,
    start_fight, group_combat, party_wiped,
    attempt_retreat, refresh_foes_after_retreat,
    award_xp, roll_loot, award_quest,
    short_rest as _short_rest, long_rest as _long_rest,
    tavern_rest as _tavern_rest,
    buy_potion as _buy_potion, use_heal as _use_heal,
    use_potion as _use_potion, buy_weapon as _buy_weapon,
    equip_weapon as _equip_weapon,
    train_combat_once as _train_combat_once,
    train_proficiency as _train_proficiency,
)
import story
from people import (make_character, make_pair, character_sheet, person_line,
                    npc_line, downtime_match, joining_gold, PAIR_CHANCE)
from sites import SITES, FOES, BANDIT_KINDS, WEAPON_INDEX, make_foe, roster_lines
from quests import (generate_world, forge_quest, board_lines,
                    quest_detail_lines, quest_line, roster_kinds_line,
                    lands, roll_wild_level, build_wild_encounter,
                    wild_encounter_xp,
                    TRAVEL_DAYS_IN_LAND, TRAVEL_DAYS_CROSS,
                    TRAVEL_ENCOUNTER_CHANCE, EXPLORE_ENCOUNTER_CHANCE,
                    EXPLORE_XP, SPOTTED_MARGIN, AMBUSH_CHANCE,
                    WILD_SPOTTED_CHANCE, HUNT_AMBUSH_CHANCE,
                    CAMP_ENCOUNTER_CHANCE,
                    HUNT_LEVEL_REACH, WILD_NAME_PARTS)

STATE_PATH = Path(__file__).parent / "save.json"

# Off-script foe kinds (`fight N --type ...`): any catalog kind by name, or
# "bandit" for a random living foe from the bandit pool.
FIGHT_TYPES = ("bandit",) + tuple(sorted(FOES))


def _spawn_foe(kind: str, rng, n: int):
    if kind == "bandit":
        kind = rng.choice(BANDIT_KINDS)
    return make_foe(kind, n, rng)


# --------------------------------------------------------------------------- #
# Location (the navigation layer, 2026-07-09)
# --------------------------------------------------------------------------- #
# The party is always SOMEWHERE: at a settlement (its board is the local
# board; its surrounding sites are in reach) or at a discovered wilderness
# place. A location is {"place": key, "name": display, "land": race,
# "kind": "settlement" | "wild"}. The two hand-built set sites (hideout /
# barrow) lie outside the STARTING settlement (the first one worldgen made).

def _settlement_location(s: dict) -> dict:
    return {"place": s["key"], "name": s["name"], "land": s["race"],
            "kind": "settlement"}


def location_line(state: dict) -> str:
    loc = state["location"]
    return f"{loc['name']} ({loc['land']} lands, {loc['kind']})"


def local_settlement(state: dict) -> dict | None:
    """The settlement the party is AT, or None out in the wilds."""
    loc = state["location"]
    if loc["kind"] != "settlement":
        return None
    for s in state["world"]["settlements"]:
        if s["key"] == loc["place"]:
            return s
    return None


def home_settlement(state: dict) -> dict:
    """The starting settlement -- the two hand-built set sites lie outside it."""
    return state["world"]["settlements"][0]


def clear_sighting(state: dict, quiet: bool = False) -> None:
    """Spotted foes don't wait around: any move (travel, explore, hunt, camp)
    lets them drift on. `engage` is the only way to fight a sighting."""
    if state.get("sighting"):
        if not quiet:
            print("(The foes sighted earlier have moved on.)")
        state["sighting"] = None


def reset_streak(state: dict) -> None:
    """A night's camp breaks the same-site momentum streak (see rpg.py,
    STREAK_STEP): the next encounter pays base rate again."""
    state["streak"] = {"site": None, "count": 0}


def streak_pos_for(state: dict, site_key: str) -> int:
    """The momentum position the NEXT cleared encounter at this site would
    hold: one past the recorded run, or 1 after a camp / at another site."""
    streak = state.get("streak") or {"site": None, "count": 0}
    return streak["count"] + 1 if streak["site"] == site_key else 1


def _settlement_by_key(world: dict, key: str) -> dict | None:
    for s in world["settlements"]:
        if s["key"] == key:
            return s
    return None


def at_quest_settlement(state: dict, quest: dict) -> bool:
    """Quests are LOCAL: taking one and working its sites means being at the
    settlement that posted it (its region holds the sites). Prints the way
    there when the party isn't."""
    key = quest.get("settlement")
    if not key:
        return True     # a placeless forged quest works anywhere
    if state["location"]["place"] == key:
        return True
    s = _settlement_by_key(state["world"], key)
    name = s["name"] if s else key
    print(f"[{quest['id']}] {quest['name']} is {name}'s business -- the "
          f"party is at {location_line(state)}. `travel {key}` first.")
    return False


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
        "streak_pos": pending.get("streak_pos"),
        "dead_before": pending.get("dead_before", []),
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
        "streak_pos": d.get("streak_pos"),
        "dead_before": d.get("dead_before", []),
    }


PARTY_SHEET_PATH = Path(__file__).parent / "party.txt"


def party_sheet_lines(state: dict) -> list[str]:
    """The full-party info sheet written to party.txt on every save: the
    whole between-fights board in one plain file (the designer reads it in
    Claude Code on the web via the auto-commit; the DM never has to
    reassemble it from logs)."""
    party, clock, purse = state["party"], state["clock"], state["purse"]
    loc = location_line(state) if state.get("location") else "nowhere yet"
    lines = [f"RPG2 PARTY SHEET -- day {clock.day}, at {loc}",
             f"purse: {purse.gold}g | short rests left today: "
             f"{clock.short_rests_left}"]
    if not party:
        lines.append("(no party yet -- `pick` a character)")
        return lines
    pc = party[0]
    if pc.cha:
        companions = sum(1 for h in party[1:] if not h.dead)
        lines.append(f"party: {companions}/{party_capacity(pc.cha)} "
                     f"companion slot(s) filled (CHA {pc.cha})")
    for h in party:
        tag = " [DEAD]" if h.dead else " [DOWN]" if h.down else ""
        if wants_to_leave(h):
            tag += " [QUITTING at the next settlement]"
        lines.append("")
        lines.append(f"{role_tag(party, h)} {stat_line(h)}{tag}")
        if h.race:
            lines.append(" " * 12 + person_line(h))
        lines.append(" " * 12 + progress_line(h))
    lines.append("")
    world = state.get("world")
    qid = state.get("active_quest")
    if world and qid:
        q = world["quests"][qid]
        if q["status"] == "done":
            lines.append(f"active quest [{qid}] {q['name']} is COMPLETE")
        else:
            cur = q["next"]
            s = q["sites"][cur["site"]]
            lines.append(f"active quest: [{qid}] L{q['level']} {q['name']} "
                         f"-- next: {s['name']} (L{s['level']}), room "
                         f"{cur['room'] + 1}/{len(s['rooms'])}")
    streak = state.get("streak") or {"site": None, "count": 0}
    if streak["count"]:
        lines.append(f"momentum: {streak['count']} encounter(s) at "
                     f"{streak['site']} since the last camp")
    if state.get("sighting"):
        lines.append(f"sighted: {state['sighting']['line']}")
    for (site, room), rec in sorted(state.get("rooms", {}).items()):
        standing = sum(1 for f in rec["foes"] if not f.dead)
        lines.append(f"unfinished: {site} room {room} -- {standing} foe(s) "
                     f"still hold it (fled day {rec['day']})")
    if world:
        lines.extend(story.war_status_lines(world, state.get("story")))
    if state.get("pending"):
        lines.append("*** A FIGHT IS PAUSED -- resume or retreat ***")
    return lines


def _write_party_sheet(state: dict) -> None:
    """Write party.txt and best-effort commit it (that one file only; the
    designer follows the playthrough from the repo). NEVER raises: a broken
    git state must not take the game loop down with it."""
    try:
        PARTY_SHEET_PATH.write_text(
            "\n".join(party_sheet_lines(state)) + "\n", encoding="utf-8")
    except Exception:
        return
    try:
        root = Path(__file__).parent
        day = state["clock"].day
        where = (state["location"]["name"]
                 if state.get("location") else "nowhere")
        subprocess.run(["git", "add", "party.txt"], cwd=root, check=False,
                       capture_output=True, timeout=15)
        subprocess.run(["git", "commit", "--quiet",
                        "-m", f"party sheet: day {day} at {where}",
                        "--", "party.txt"],
                       cwd=root, check=False, capture_output=True, timeout=15)
    except Exception:
        pass


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
        "story": state.get("story"),
        "location": state.get("location"),
        "places": state.get("places", []),
        "sighting": state.get("sighting"),
        "streak": state.get("streak", {"site": None, "count": 0}),
        "site_clears": state.get("site_clears", {}),
        "pc_candidates": state.get("pc_candidates"),
        "recruits": state.get("recruits"),
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
    _write_party_sheet(state)


def load() -> dict:
    with open(STATE_PATH, encoding="utf-8") as f:
        doc = json.load(f)
    party = [_entity_from_dict(d) for d in doc["party"]]
    if party:
        # party[0] IS the PC by definition (dm.md) -- assert it positionally
        # on every load so fate's bargain also covers pre-flag saves.
        party[0].protagonist = True
    rng = random.Random()
    v, internal, gauss = doc["rng"]
    rng.setstate((v, tuple(internal), gauss))
    rooms = {}
    for key, rec in doc.get("rooms", {}).items():
        site, room = key.rsplit("#", 1)
        rooms[(site, int(room))] = {
            "foes": [_entity_from_dict(f) for f in rec["foes"]],
            "day": rec["day"]}
    world = doc.get("world")
    location = doc.get("location")
    if location is None and world:
        # A save from before the navigation layer: the party is at home.
        location = _settlement_location(world["settlements"][0])
    return {
        "party": party,
        "clock": Clock(**doc["clock"]),
        "purse": Purse(**doc["purse"]),
        "rng": rng,
        "foe_count": doc["foe_count"],
        "active_quest": doc.get("active_quest"),
        "world": world,
        "story": doc.get("story"),
        "location": location,
        "places": doc.get("places", []),
        "sighting": doc.get("sighting"),
        "streak": doc.get("streak", {"site": None, "count": 0}),
        "site_clears": doc.get("site_clears", {}),
        "pc_candidates": doc.get("pc_candidates"),
        "recruits": doc.get("recruits"),
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
    """Most commands are between-fights actions; refuse them mid-melee --
    and refuse them before the game has a party at all (a fresh `new` waits
    on `pick`)."""
    if not state["party"]:
        print("No party yet -- choose your character first (`pick N`; "
              "`status` shows the candidates), then hire companions "
              "(`recruit` / `hire NAME`).")
        return False
    if state.get("pending"):
        print("A fight is PAUSED -- the party is mid-melee. Resolve it "
              "first: resume [--drink HERO] [--heal HERO] [--berserk HERO] "
              "[--warbreath HERO], or retreat.")
        return False
    return True


def print_pc_candidates(state: dict) -> None:
    cands = [_entity_from_dict(d) for d in state["pc_candidates"]]
    print("Three men stand ready -- choose your character "
          "(`pick N` or `pick NAME`):")
    for i, c in enumerate(cands, 1):
        print(f"[{i}]")
        for line in character_sheet(c):
            print("  " + line)
        cap = party_capacity(c.cha)
        crowd = (f"could lead {cap} companion(s)" if cap
                 else "would travel ALONE -- no one follows a leader this "
                      "charmless (a near-hopeless game)")
        print(f"    presence: CHA {c.cha} -- {crowd}")


def cmd_new(args: argparse.Namespace) -> None:
    rng = random.Random(args.seed)
    used: set[str] = set()
    # The PC is chosen from THREE rolled men (male by designer fiat for now;
    # picking from candidates mirrors the tavern's hiring surface and keeps
    # a capacity-0 CHA roll a rare, semi-chosen fate instead of a 1-in-4
    # ambush -- see rules.md, the Party & Charisma add-on).
    candidates = [make_character(rng, level=1, sex="m", used_names=used)
                  for _ in range(3)]
    world_seed = rng.randrange(1 << 30)     # derived, so --seed pins the
                                            # whole playthrough, world and all
    world = generate_world(world_seed)
    state = {"party": [], "clock": Clock(), "purse": Purse(), "rng": rng,
             "foe_count": 0, "pending": None, "rooms": {},
             "world": world, "active_quest": None,
             "story": story.init_story(world, rng),
             "location": _settlement_location(world["settlements"][0]),
             "places": [], "sighting": None,
             "streak": {"site": None, "count": 0}, "site_clears": {},
             "pc_candidates": [_entity_to_dict(c) for c in candidates],
             "recruits": None}
    save(state)
    print(f"New game (seed={args.seed}).")
    print("(The story layer is armed: a war is seeded in this world and "
          "its first word finds a level-2 party. DM: see dm.md, The war.)")
    print_pc_candidates(state)
    names = ", ".join(f"{s['name']} ({s['race']} {s['kind']})"
                      for s in world["settlements"])
    print(f"The world holds {len(world['quests'])} posted quests across: "
          f"{names}.")


def cmd_pick(args: argparse.Namespace) -> None:
    state = load()
    cands = state.get("pc_candidates")
    if not cands:
        print("No character choice pending -- `new` starts a game.")
        return
    want = " ".join(args.who).lower()
    chosen = None
    if want.isdigit() and 1 <= int(want) <= len(cands):
        chosen = cands[int(want) - 1]
    else:
        for d in cands:
            if want in d["name"].lower():
                chosen = d
                break
    if chosen is None:
        print(f"No candidate matches {want!r}. Candidates: "
              + ", ".join(d["name"] for d in cands))
        return
    pc = _entity_from_dict(chosen)
    pc.protagonist = True   # fate's bargain guards the PC (rpg.Entity)
    state["party"] = [pc]
    state["pc_candidates"] = None
    print(f"You are {pc.name}.")
    print("  " + person_line(pc))
    print("  " + stat_line(pc))
    gold = joining_gold(pc)
    if gold:
        state["purse"].gold += gold
        print(f"  {pc.name} starts with {gold}g of his own -- the purse "
              f"holds {state['purse'].gold}g.")
    cap = party_capacity(pc.cha)
    if cap == 0:
        print(f"  CHA {pc.cha}: no one will follow {pc.name}. This game is "
              f"played ALONE -- if he dies, it ends, and no fate's bargain "
              f"softens it.")
    else:
        print(f"  CHA {pc.cha}: the party can hold {cap} companion(s).")
        # The starter companion (2026-07-11, designer call: the game should
        # start PLAYABLE): one random companion joins for free at pick --
        # an old ALLY of the PC's, never family or a mentor (that read too
        # restrictive), leveled with him, arriving on the same terms as a
        # hire (satisfaction 7, joining gold to the purse). Any remaining
        # capacity is still the tavern's to fill -- choosing the rest of
        # the party stays a real decision.
        rng = state["rng"]
        used = {h.name for h in state["party"]}
        ally = make_character(rng, level=1, used_names=used)
        ally.satisfaction = SATISFACTION_START
        ally.bond, ally.bond_kind = pc.name, "old ally"
        if has_trait(ally, "needs meds"):
            ally.last_dose_day = state["clock"].day
        state["party"].append(ally)
        print(f"An old ally answers {pc.name}'s call and joins for the road:")
        for line in character_sheet(ally):
            print("  " + line)
        gold = joining_gold(ally)
        if gold:
            state["purse"].gold += gold
            print(f"  {ally.name} adds {gold}g to the party purse "
                  f"({state['purse'].gold}g).")
        roll_recruits(state)
        print(f"The common room at {state['location']['name']} holds "
              f"tonight's introductions (free, this once):")
        for line in recruit_summary_lines(state):
            print(line)
        if cap > 1:
            print("See them in full with `recruit`; sign one with "
                  "`hire NAME`. A later `tavern` night gathers new faces.")
        else:
            print(f"(With {ally.name} along the party is at its CHA "
                  f"capacity -- these faces just drink here. `dismiss` "
                  f"frees a slot; a later `tavern` night gathers new ones.)")
    print(f"The party stands at {location_line(state)} -- the local board "
          f"is `board`; the wider world is `map` and `travel`. The old "
          f"hideout and barrow lie outside "
          f"{state['world']['settlements'][0]['name']}.")
    save(state)


# --------------------------------------------------------------------------- #
# Recruiting, departures, and the nightly upkeep (the companion layer)
# --------------------------------------------------------------------------- #

def roll_recruits(state: dict) -> None:
    """Roll a settlement evening's recruit candidates: as many OPTIONS as
    the PC's CHA capacity (three choices even if only one slot is free --
    seeing the market is part of the pitch), each leveled to the PC +-1,
    a quarter of them bonded pairs (one option, two heads). Rolled once per
    paid tavern night (plus the free game-start evening) -- the night's cost
    and day are the reroll gate."""
    party, rng, clock = state["party"], state["rng"], state["clock"]
    here = local_settlement(state)
    pc = party[0]
    cap = party_capacity(pc.cha)
    if here is None or cap == 0:
        state["recruits"] = None
        return
    used = {h.name for h in party}
    options = []
    for _ in range(cap):
        level = max(1, pc.level + rng.randint(-1, 1))
        if rng.random() < PAIR_CHANCE:
            kind, members = make_pair(rng, level, used_names=used)
        else:
            kind, members = None, [make_character(rng, level,
                                                  used_names=used)]
        options.append({"kind": kind,
                        "members": [_entity_to_dict(m) for m in members]})
    state["recruits"] = {"place": here["key"], "day": clock.day,
                         "options": options}


def recruit_summary_lines(state: dict) -> list[str]:
    """The compact one-line-per-option readout (tavern nights); `recruit`
    prints the full sheets."""
    rec = state.get("recruits")
    if not rec or not rec["options"]:
        return []
    lines = []
    for i, opt in enumerate(rec["options"], 1):
        names = " & ".join(f"{m['name']} ({m['race']} {m['sex']}, "
                           f"L{m['level']})" for m in opt["members"])
        pair = f" -- {opt['kind']} (one option, two heads)" if opt["kind"] else ""
        lines.append(f"  [{i}] {names}{pair}")
    return lines


def local_recruits(state: dict) -> dict | None:
    """The candidate pool waiting where the party stands, if any."""
    rec = state.get("recruits")
    here = local_settlement(state)
    if not rec or here is None or rec["place"] != here["key"]:
        return None
    return rec if rec["options"] else None


def cmd_recruit(args: argparse.Namespace) -> None:
    state = load()
    party = state["party"]
    if not party:
        print("No party yet -- `pick` your character first.")
        return
    pc = party[0]
    cap = party_capacity(pc.cha)
    companions = [h for h in party[1:] if not h.dead]
    print(f"{pc.name}'s presence (CHA {pc.cha}) can hold {cap} "
          f"companion(s); the party has {len(companions)}.")
    if cap == 0:
        print("No one would sign on -- this party is a party of one.")
        return
    rec = local_recruits(state)
    if rec is None:
        print("No candidates gathered here -- a `tavern` night draws them "
              "(the evening's company is part of what the coin buys).")
        return
    for i, opt in enumerate(rec["options"], 1):
        header = f"[{i}]"
        if opt["kind"]:
            header += (f" {opt['kind']} -- one option, two heads against "
                       f"the capacity, joining and leaving together")
        print(header)
        for m in opt["members"]:
            for line in character_sheet(_entity_from_dict(m)):
                print("  " + line)
    print("`hire NAME` signs them on (a pair signs together).")


def cmd_hire(args: argparse.Namespace) -> None:
    state = load()
    if not require_no_pending(state):
        return
    party, purse, clock = state["party"], state["purse"], state["clock"]
    rec = local_recruits(state)
    if rec is None:
        print("No candidates here to hire -- see `recruit`.")
        return
    want = " ".join(args.name).lower()
    match = None
    for opt in rec["options"]:
        if any(want in m["name"].lower() for m in opt["members"]):
            match = opt
            break
    if match is None:
        names = ", ".join(m["name"] for opt in rec["options"]
                          for m in opt["members"])
        print(f"No candidate matches {want!r}. Candidates: {names}.")
        return
    pc = party[0]
    cap = party_capacity(pc.cha)
    companions = [h for h in party[1:] if not h.dead]
    heads = len(match["members"])
    if len(companions) + heads > cap:
        pair = " (a pair signs together -- two heads)" if heads > 1 else ""
        print(f"The party is full: CHA {pc.cha} holds {cap} companion(s) "
              f"and it has {len(companions)}{pair}. No one leaves a leader "
              f"they still follow -- capacity is a hard cap.")
        return
    log: list[str] = []
    for d in match["members"]:
        m = _entity_from_dict(d)
        m.satisfaction = SATISFACTION_START
        if has_trait(m, "needs meds"):
            m.last_dose_day = clock.day
        gold = joining_gold(m)
        if gold:
            purse.gold += gold
            log.append(f"    {m.name} adds {gold}g to the party purse "
                       f"({purse.gold}g).")
        party.append(m)
        bond = f" -- with {m.bond} ({m.bond_kind})" if m.bond else ""
        log.append(f"  {m.name} joins the party{bond}.")
        log.append("    " + stat_line(m))
    rec["options"].remove(match)
    print("\n".join(log))
    save(state)


def cmd_dismiss(args: argparse.Namespace) -> None:
    """Let a companion go (2026-07-11): the player's side of the departure
    coin. Settlement-gated like every parting of ways, and the severance is
    the QUITTER'S deal on purpose -- an equal head-split of the purse plus
    their carried gear -- so swapping the party out isn't free (hire, use,
    dump before payday would otherwise be the optimal churn). Bond partners
    walk together, same as a quit."""
    state = load()
    if not require_no_pending(state):
        return
    if local_settlement(state) is None:
        print(f"Partings happen at a settlement -- the party is at "
              f"{location_line(state)}. No one walks into the wilds alone.")
        return
    party, purse = state["party"], state["purse"]
    hero = find_hero(party, " ".join(args.name))
    if hero is None:
        return
    if hero is party[0]:
        print(f"{hero.name} IS the party -- the player character can't be "
              f"dismissed.")
        return
    if hero.dead:
        print(f"{hero.name} is dead -- the dead are laid to rest on "
              f"arrival, not dismissed.")
        return
    leavers = [hero]
    partner = next((p for p in party[1:]
                    if hero.bond and p.name == hero.bond and not p.dead),
                   None)
    if partner is not None:
        leavers.append(partner)
    place = state["location"]["name"]
    living = [h for h in party if not h.dead]
    share = purse.gold // len(living) if living else 0
    log: list[str] = []
    for h in leavers:
        purse.gold -= share
        party.remove(h)
        why = (f"leaves with {h.name if h is hero else hero.name}"
               f" ({h.bond_kind})" if h is not hero else "is let go")
        log.append(f"  {h.name} {why} at {place} -- taking their share "
                   f"of the purse ({share}g) and their gear.")
    log.append(f"    The purse holds {purse.gold}g.")
    print("\n".join(log))
    save(state)


def night_upkeep(state: dict, log: list[str]) -> None:
    """Once per night slept, wherever it was: the 'needs meds' drain -- a
    companion whose last dose is older than MEDS_INTERVAL_DAYS loses 1
    satisfaction per night until a dose is bought (`buy HERO meds`, capitals
    only)."""
    clock = state["clock"]
    for h in state["party"][1:]:
        if h.dead or not satisfaction_tracked(h):
            continue
        if (has_trait(h, "needs meds")
                and clock.day - h.last_dose_day > MEDS_INTERVAL_DAYS):
            adjust_satisfaction(h, -1, log, "out of their medicine")


def process_departures(state: dict, log: list[str]) -> None:
    """Settle the party's books at a settlement: dead companions are laid to
    rest (the party as constituted shrinks -- XP shares reflect it from here
    on), and anyone at/below their leave threshold quits, taking an equal
    head-split of the purse (and their carried weapon and potions) with
    them. Bond partners leave together. Called on settlement arrival and at
    the end of tavern/downtime nights."""
    if local_settlement(state) is None:
        return
    party, purse = state["party"], state["purse"]
    place = state["location"]["name"]
    for h in [h for h in party[1:] if h.dead]:
        party.remove(h)
        log.append(f"  {h.name} is laid to rest at {place}.")
    leavers = [h for h in party[1:] if wants_to_leave(h)]
    pulled: list = []
    for h in list(leavers):
        if h.bond:
            partner = next((p for p in party[1:]
                            if p.name == h.bond and not p.dead
                            and p not in leavers and p not in pulled), None)
            if partner is not None:
                pulled.append(partner)
    if not leavers:
        return
    living = [h for h in party if not h.dead]
    share = purse.gold // len(living) if living else 0
    for h in leavers + pulled:
        purse.gold -= share
        party.remove(h)
        why = (f"leaves with {h.bond} ({h.bond_kind})" if h in pulled
               else "has had enough and quits the party")
        log.append(f"  *** {h.name} {why} at {place} -- taking their share "
                   f"of the purse ({share}g) and their gear. ***")
    log.append(f"    The purse holds {purse.gold}g.")


def cmd_status(args: argparse.Namespace) -> None:
    state = load()
    party, clock, purse = state["party"], state["clock"], state["purse"]
    if not party and state.get("pc_candidates"):
        print_pc_candidates(state)
        return
    print(f"Day {clock.day}, {clock.short_rests_left} short rest(s) left today. "
          f"Purse: {purse.gold}g. At: {location_line(state)}.")
    pc = party[0] if party else None
    if pc is not None and pc.cha:
        companions = sum(1 for h in party[1:] if not h.dead)
        print(f"  Party: {companions}/{party_capacity(pc.cha)} companion "
              f"slot(s) filled (CHA {pc.cha}).")
    for h in party:
        tag = " [DEAD]" if h.dead else " [DOWN]" if h.down else ""
        if wants_to_leave(h):
            tag += " [QUITTING at the next settlement]"
        print(f"  {role_tag(party, h)} " + stat_line(h) + tag)
        if h.race:
            print(" " * 14 + person_line(h))
        print(" " * 14 + progress_line(h))
    if local_recruits(state):
        print("  Candidates wait at the tavern -- `recruit` shows them.")
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
    streak = state.get("streak") or {"site": None, "count": 0}
    if streak["count"]:
        print(f"  Momentum: {streak['count']} encounter(s) cleared at "
              f"{streak['site']} since the last camp -- the next pays more "
              f"(a camp resets it).")
    if state.get("sighting"):
        s = state["sighting"]
        print(f"  Sighted (day {s['day']}): {s['line']} -- `engage` to fight "
              f"it; any move lets it drift on.")
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
    print("  (the encounter's ONE pause -- after this it runs to its end, "
          "the party acting on its standing orders)")
    standing = [f for f in pending["foes"] if f.alive]
    print("  Facing: " + ", ".join(
        f"{f.name} {f.hp}/{f.max_hp} HP" for f in standing))
    for h in party:
        if h.dead:
            continue
        tag = " [DOWN]" if h.down else ""
        print(f"  {h.name}{tag}: STA {h.cur_sta}/{h.sta}  HP {h.hp}/{h.max_hp}"
              f"  Power {h.cur_power}/{h.power}  "
              f"healing x{h.items.get('healing', 0)}  "
              f"stamina x{h.items.get('stamina', 0)}")
    print("  The player's call (pause actions cost that round's attack and "
          f"defend at -{PAUSE_ACTION_DEF_PENALTY}):")
    print("    resume                    -- fight on")
    print(f"    resume --drink HERO       -- stamina draught, "
          f"+{STAMINA_DRAUGHT_RESTORE} STA now")
    print(f"    resume --heal HERO        -- healing potion, "
          f"+{HEALING_POTION_RESTORE} HP now (the wound penalty lightens)")
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


def play_orders(already_paused: bool):
    """Session play's crossing dispatch (rpg.group_combat's standing_orders):
    the FIRST wounds crossing of the fight interrupts -- the one "someone is
    being cut apart, do we retreat?" pause, the player's -- and every other
    crossing runs the default standing order (rpg.standing_order: drink /
    heal / convert on their own, skipped when the fight is winding down).
    At most ONE pause per encounter (designer call, 2026-07-11): a fight
    with a `pending` record has had its pause, so resumes pass
    already_paused=True and never stop again."""
    def orders(kind, hero, party, foes):
        if kind == "wounds" and not already_paused:
            return "pause"
        return standing_order(kind, hero, foes)
    return orders


def resolve_encounter(state: dict, log: list[str], foes: list,
                      encounter_xp: int, site: str | None = None,
                      room: int | None = None,
                      quest: str | None = None,
                      streak_pos: int | None = None) -> None:
    """Shared tail of every encounter command: run the melee -- which may
    PAUSE once, at the fight's first wounds crossing (see play_orders) --
    then award and
    persist. On a pause the fight is saved as `pending` and the turn goes
    back to the player (resume / retreat next message). `quest` ties the
    encounter to a board quest: clearing the room advances its cursor.
    `streak_pos` is the momentum position this encounter's XP was quoted at
    (site encounters only) -- recorded on victory so the NEXT one pays more."""
    party, rng = state["party"], state["rng"]
    living = [h for h in party if not h.dead]
    dead_before = [h.name for h in party if h.dead]    # so the post-fight
                                                       # morale pass knows
                                                       # who died in THIS one
    fired: set[str] = set()
    pause = group_combat(living, foes, rng, log, pause_triggers=True,
                         fired=fired, standing_orders=play_orders(False))
    if pause is not None:
        state["pending"] = {
            "foes": foes, "xp": encounter_xp, "site": site, "room": room,
            "quest": quest, "fired": fired, "round": pause.round,
            "crossings": [(k, h.name) for k, h in pause.crossings],
            "streak_pos": streak_pos,
            "dead_before": dead_before,
        }
        print_combat(log)
        print()
        print_pause_menu(state)
        save(state)
        return
    finish_encounter(state, log, foes, encounter_xp, site=site, room=room,
                     quest=quest, streak_pos=streak_pos,
                     dead_before=dead_before)


def advance_quest(state: dict, log: list[str], qid: str) -> None:
    """The active quest's cleared room: move the cursor. Finishing a site
    pays its clear lump + gold (each site pays its own way -- the level IS
    the pay grade); finishing the last site closes the quest, day-stamps
    it, and delivers the EPILOGUE (2026-07-12: the authored aftermath line
    the giver's turn-in scene is narrated over -- dm.md)."""
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
        quest["done_day"] = state["clock"].day
        g = quest.get("giver")
        if g:
            log.append(f"  (turn in to {g['name']}, {g['role']} -- "
                       f"narrate the scene)")
        if quest.get("epilogue"):
            log.append(f"  EPILOGUE (day {state['clock'].day}): "
                       f"{quest['epilogue']}")
        if quest.get("story_wave") is not None and state.get("story"):
            for line in story.on_wave_done(state["story"], quest,
                                           state["clock"].day):
                log.append("  " + line)
    else:
        nxt = quest["sites"][cur["site"]]
        log.append(f"  (next: {nxt['name']}, L{nxt['level']}, "
                   f"{len(nxt['rooms'])} encounter(s))")


def maybe_post_wave(state: dict, log: list | None = None) -> bool:
    """The war's clock (story.py): post the next wave when it is due --
    the previous wave DONE and the party at the wave's level (2/5/8/10).
    Checked at the natural news-reaches-you points: the board, arrivals,
    settlement nights, and right after a quest pays out. Prints (or
    appends) the messenger scene; every call site saves afterward."""
    st = state.get("story")
    living = [h for h in state["party"] if not h.dead]
    if not st or not living:
        return False
    if story.next_wave_due(st, max(h.level for h in living)) is None:
        return False
    quest, lines = story.post_wave(state["world"], st, state["rng"],
                                   state["clock"].day)
    lines.append(f"(details: `show {quest['id']}`; it is taken AT its "
                 f"settlement, like any quest)")
    if log is None:
        print("\n".join(lines))
    else:
        log.extend(lines)
    return True


def occupied_here(state: dict) -> dict | None:
    """The local settlement when it lies in the war's fallen land (the
    post-wave-3 occupation), else None."""
    here = local_settlement(state)
    if here is not None and story.occupied(state.get("story"), here):
        return here
    return None


def occupation_line(state: dict, settlement: dict) -> str:
    return (f"{settlement['name']} lies under the "
            f"{state['story']['aggressor']} yoke -- no board, no tavern, "
            f"no hiring, no idle days in an occupied town. The roads "
            f"still pass through, and the war can still turn.")


def pay_set_site_clear(state: dict, log: list[str], site_key: str,
                       room: int) -> None:
    """A SET site (hideout/barrow) has no quest cursor, so track its cleared
    rooms here and pay the site-clear lump the first time every room is down --
    the same gold + XP lump board quests pay via advance_quest, and the sims
    pay via sites.run_site (dm.md: 'both set sites pay themselves now'). The
    play driver was the one path that skipped it. Order-independent (rooms may
    be run in any order) and paid once per site."""
    site = SITES.get(site_key)
    if site is None:
        return
    rec = state.setdefault("site_clears", {}).setdefault(
        site_key, {"rooms": [], "paid": False})
    if room not in rec["rooms"]:
        rec["rooms"].append(room)
    if rec["paid"] or len(rec["rooms"]) < len(site.rooms):
        return
    rec["paid"] = True
    award_quest(state["party"], state["purse"], site.quest_gold,
                site.quest_xp, log, site.quest_line, banner="SITE CLEARED")


def finish_encounter(state: dict, log: list[str], foes: list,
                     encounter_xp: int, site: str | None = None,
                     room: int | None = None,
                     quest: str | None = None,
                     streak_pos: int | None = None,
                     dead_before: list[str] | None = None) -> None:
    """The melee actually ended: wipe check, awards, loot, the companion
    morale pass, persist."""
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
        reason = "encounter"
        if streak_pos is not None and streak_pos > 1:
            reason = f"encounter, streak {streak_pos}"
        award_xp(party, encounter_xp, log, reason)
        if site is not None and streak_pos is not None:
            # Momentum recorded: the next same-site encounter without a camp
            # between pays the next multiplier up.
            state["streak"] = {"site": site, "count": streak_pos}
        roll_loot(party, purse, rng, log)
        weapons_left = fallen_weapons_line(foes)
        if weapons_left:
            log.append(weapons_left)
        if quest is not None:
            advance_quest(state, log, quest)
        elif site is not None:
            pay_set_site_clear(state, log, site, room)

    if not wiped:
        # The companion morale pass: blood and fear, whatever the outcome
        # (a game over needs no bookkeeping).
        satisfaction_after_fight(party, dead_before or [], log)
        # The war's clock: a fight that leveled the party (or closed a
        # wave) can bring the next messenger on the spot.
        maybe_post_wave(state, log)
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
    if state.get("world"):
        home = home_settlement(state)
        if state["location"]["place"] != home["key"]:
            print(f"The {site.key} lies outside {home['name']} -- the party "
                  f"is at {location_line(state)}. `travel {home['key']}` "
                  f"first.")
            return
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

    k = streak_pos_for(state, site.key)
    resolve_encounter(state, log, foes, site.encounter_xp(k),
                      site=site.key, room=args.room, streak_pos=k)


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
    if state["party"] and maybe_post_wave(state):
        save(state)     # persist the posting BEFORE the readout: a broken
                        # pipe mid-print must not lose the wave
    key = None
    if args.settlement:
        # An explicit settlement (or 'all') is the DM's overview; what the
        # PLAYER gets is the ask-around funnel over the local list (dm.md).
        if args.settlement.lower() != "all":
            want = args.settlement.lower()
            match = [s for s in world["settlements"] if want in s["key"]]
            if not match:
                print(f"No settlement matches {args.settlement!r}. "
                      "Settlements: "
                      + ", ".join(s["name"] for s in world["settlements"]))
                return
            key = match[0]["key"]
    else:
        here = local_settlement(state)
        if here is None:
            print(f"No jobs to ask after out here -- the party is at "
                  f"{location_line(state)}. Work is found in settlements "
                  f"(`map` lists them; `board all` is the DM overview).")
            return
        if occupied_here(state):
            print(occupation_line(state, here))
            return
        key = here["key"]
        print(f"Day {state['clock'].day}. Asking around {here['name']} "
              f"(the DM's inventory -- in play, each job is its GIVER's; "
              f"funnel to them in one message, dm.md):")
    for line in board_lines(world, key):
        print(line)
    if not args.settlement:
        cast = [n for n in world.get("npcs", []) if n["seat"] == key]
        if cast:
            print("Notables in town (the recurring cast -- see dm.md):")
            for n in cast:
                print("  " + npc_line(n))
    if not args.settlement:
        # Word travels within a land (2026-07-11, designer call): the
        # player KNOWS every open quest in the current land -- name, level,
        # where -- so travel is an informed choice, not a blind hop. Levels
        # shown straight, like the local board; details and `take` still
        # want the party AT the posting settlement.
        land = state["location"]["land"]
        rumors = []
        for s in lands(world).get(land, []):
            if s["key"] == key:
                continue
            for qid in s["quests"]:
                q = world["quests"][qid]
                if q["status"] == "open":
                    rumors.append(f"  [{q['id']}] L{q['level']:<2} "
                                  f"{q['name']} -- at {s['name']}")
        if rumors:
            print(f"Word from around the {land} lands (travel there to "
                  f"take one; `show QID` for what's known):")
            for line in rumors:
                print(line)
    for line in story.war_status_lines(world, state.get("story")):
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
    if not at_quest_settlement(state, quest):
        return
    here = occupied_here(state)
    if here is not None:
        print(occupation_line(state, here))
        return
    state["active_quest"] = quest["id"]
    save(state)
    g = quest.get("giver")
    if g:
        print(f"The job is taken from its giver -- narrate the scene "
              f"(dm.md): {npc_line(g)}")
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
    if not at_quest_settlement(state, quest):
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
        # A named villain (the conquest's lieutenants/conqueror) caps the
        # site's last room: the strongest roster slot wears the name --
        # display only, the stat row never forks (story.py).
        boss = site.get("boss")
        boss_at = None
        if boss and room_i == len(site["rooms"]) - 1:
            hits = [i for i, k in enumerate(kinds) if k == boss["kind"]]
            boss_at = hits[-1] if hits else None
        foes = []
        for i, kind in enumerate(kinds):
            state["foe_count"] += 1
            foe = make_foe(kind, state["foe_count"], rng,
                           display=quest["skins"].get(kind))
            if i == boss_at:
                foe.name = boss["display"]
            foes.append(foe)
        for line in roster_lines(foes):
            log.append("  " + line)
    else:
        foes, note = held
        log.append(banner + ", again ===")
        log.append(note)
        for line in roster_lines([f for f in foes if f.alive]):
            log.append("  " + line)

    k = streak_pos_for(state, site_key)
    resolve_encounter(state, log, foes,
                      site_encounter_xp(site["level"], len(site["rooms"]), k),
                      site=site_key, room=room_i + 1, quest=qid,
                      streak_pos=k)


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


# --------------------------------------------------------------------------- #
# The wilds: travel / explore / hunt / engage (the navigation layer)
# --------------------------------------------------------------------------- #

def _spawn_wild_foes(state: dict, kinds: list[str]) -> list:
    rng = state["rng"]
    foes = []
    for kind in kinds:
        state["foe_count"] += 1
        foes.append(make_foe(kind, state["foe_count"], rng))
    return foes


def fight_wild_encounter(state: dict, kinds: list[str], level: int,
                         banner: str) -> None:
    """Run a wilderness encounter through the same machinery as any other
    (it can pause; retreat scatters it -- the road is not a room)."""
    party = state["party"]
    log = CombatLog()
    for h in [h for h in party if not h.dead]:
        start_fight(h, log)
    log.append(f"=== {banner} (a level-{level} encounter) ===")
    foes = _spawn_wild_foes(state, kinds)
    for line in roster_lines(foes):
        log.append("  " + line)
    resolve_encounter(state, log, foes, wild_encounter_xp(level))


def wild_event(state: dict, chance: float, banner: str) -> bool:
    """Roll the wilds once: nothing, a FIGHT (returns True; the encounter
    machinery has taken over and saved), or a SIGHTING. Foes well above the
    party are usually spotted at range (unless they ambush first), and even
    ordinary trouble is spotted first WILD_SPOTTED_CHANCE of the time
    (2026-07-10) -- either way avoid or `engage` is the player's call."""
    rng = state["rng"]
    if rng.random() >= chance:
        return False
    level = roll_wild_level(rng)
    land = state["location"]["land"]
    kinds = build_wild_encounter(level, land, rng)
    party_level = max(h.level for h in state["party"] if not h.dead)
    towering = level >= party_level + SPOTTED_MARGIN
    spotted = (rng.random() >= AMBUSH_CHANCE if towering
               else rng.random() < WILD_SPOTTED_CHANCE)
    if spotted:
        line = f"L{level}: {roster_kinds_line(kinds, {})}"
        state["sighting"] = {"kinds": list(kinds), "level": level,
                             "day": state["clock"].day, "line": line}
        if towering:
            print(f"  Sighted at a distance -- {line}. Well above the "
                  f"party's weight; they haven't noticed you. `engage` to "
                  f"close with them; any other move slips away.")
        else:
            print(f"  Spotted first -- {line}. They haven't noticed the "
                  f"party. `engage` to attack; any other move slips past.")
        return False
    if towering:
        print(f"  AMBUSH -- they found the party first, and they are far "
              f"beyond it. Running away is a pause action (retreat).")
    fight_wild_encounter(state, kinds, level, banner)
    return True


def cmd_travel(args: argparse.Namespace) -> None:
    state = load()
    if not require_no_pending(state):
        return
    world = state.get("world")
    if not world:
        print("No world in this save -- start one with `new`.")
        return
    want = " ".join(args.dest).lower()
    target = None
    for s in world["settlements"]:
        if want in s["key"]:
            target = _settlement_location(s)
            break
    if target is None:
        for p in state.get("places", []):
            if want in p["name"].lower():
                target = {"place": p["name"].lower(), "name": p["name"],
                          "land": p["land"], "kind": "wild"}
                break
    if target is None:
        known = [s["name"] for s in world["settlements"]]
        known += [p["name"] for p in state.get("places", [])]
        print(f"No known place matches {want!r}. Known: {', '.join(known)}.")
        return
    if target["place"] == state["location"]["place"]:
        print(f"The party is already at {target['name']}.")
        return
    days = (TRAVEL_DAYS_IN_LAND
            if target["land"] == state["location"]["land"]
            else TRAVEL_DAYS_CROSS)
    clear_sighting(state)
    print(f"The party sets out for {target['name']} -- {days} day(s) on "
          f"the road, camping as they go.")
    log: list[str] = []
    for _ in range(days):
        _long_rest(state["party"], state["clock"], log)
        night_upkeep(state, log)
    reset_streak(state)
    print("\n".join(log))
    state["location"] = target
    print(f"The party arrives at {location_line(state)} (day "
          f"{state['clock'].day}).")
    here = occupied_here(state)
    if here is not None:
        print(occupation_line(state, here))
    # Settling the books at the walls: the dead are buried, anyone done with
    # this party walks (with their head-split of the purse).
    log = []
    process_departures(state, log)
    if log:
        print("\n".join(log))
    maybe_post_wave(state)      # news travels; arrivals are where it lands
    chance = 1 - (1 - TRAVEL_ENCOUNTER_CHANCE) ** days
    if not wild_event(state, chance, f"On the road to {target['name']}"):
        save(state)


def cmd_explore(args: argparse.Namespace) -> None:
    state = load()
    if not require_no_pending(state):
        return
    world = state.get("world")
    if not world:
        print("No world in this save -- start one with `new`.")
        return
    clear_sighting(state)
    party, clock, rng = state["party"], state["clock"], state["rng"]
    land = state["location"]["land"]
    print(f"The party ranges out into the {land} wilds -- a day afield, "
          f"camping rough.")
    log: list[str] = []
    _long_rest(party, clock, log)
    night_upkeep(state, log)
    reset_streak(state)
    print("\n".join(log))
    used = {p["name"] for p in state.get("places", [])}
    pre, suf = WILD_NAME_PARTS
    name = None
    for _ in range(60):
        name = rng.choice(pre) + rng.choice(suf)
        if name not in used:
            break
    state.setdefault("places", []).append(
        {"name": name, "land": land, "day": clock.day})
    state["location"] = {"place": name.lower(), "name": name, "land": land,
                         "kind": "wild"}
    log = []
    award_xp(party, EXPLORE_XP, log, "discovery")
    print(f"They find a place no map of theirs holds: {name}.")
    print("\n".join(log))
    if not wild_event(state, EXPLORE_ENCOUNTER_CHANCE,
                      f"In the wilds at {name}"):
        save(state)


def cmd_hunt(args: argparse.Namespace) -> None:
    """The farm loop: stalk prey in the current land's wilds. The party
    CHOOSES this fight, so unlike the road table it rolls at-or-below the
    party's level -- grinding XP and loot is always available, at wild
    (below-board) rates."""
    state = load()
    if not require_no_pending(state):
        return
    world = state.get("world")
    if not world:
        print("No world in this save -- start one with `new`.")
        return
    clear_sighting(state)
    party, rng = state["party"], state["rng"]
    land = state["location"]["land"]
    if rng.random() < HUNT_AMBUSH_CHANCE:
        # The hunter is the hunted (2026-07-10): stalking means going where
        # the predators are, and this often something off the ROAD's table
        # (any level, the higher the rarer) finds the party first. Met
        # blade-first -- an ambush never grants the sighting choice.
        level = roll_wild_level(rng)
        kinds = build_wild_encounter(level, land, rng)
        print(f"  The hunter is the hunted -- something found the party "
              f"first. AMBUSH!")
        fight_wild_encounter(state, kinds, level,
                             f"Ambushed on the hunt in the {land} wilds")
        return
    party_level = max(h.level for h in party if not h.dead)
    level = rng.randint(max(1, party_level - HUNT_LEVEL_REACH),
                        max(1, party_level))
    kinds = build_wild_encounter(level, land, rng)
    fight_wild_encounter(state, kinds, level,
                         f"The hunt in the {land} wilds")


def cmd_engage(args: argparse.Namespace) -> None:
    state = load()
    if not require_no_pending(state):
        return
    sighting = state.get("sighting")
    if not sighting:
        print("Nothing sighted to engage. (Sightings appear on the road and "
              "afield; see `status`.)")
        return
    state["sighting"] = None
    print(f"The party closes with the sighted foes -- {sighting['line']}.")
    fight_wild_encounter(state, sighting["kinds"], sighting["level"],
                         "The party picks this fight")


def cmd_map(args: argparse.Namespace) -> None:
    state = load()
    world = state.get("world")
    if not world:
        print("No world in this save -- start one with `new`.")
        return
    loc = state["location"]
    st = state.get("story")
    print(f"Day {state['clock'].day}. The party stands at "
          f"{location_line(state)}.")
    print(f"(travel: {TRAVEL_DAYS_IN_LAND} day within a land, "
          f"{TRAVEL_DAYS_CROSS} days to another land; every travel day "
          f"risks a road encounter)")
    for race, settlements in lands(world).items():
        mark = "  <- here" if race == loc["land"] else ""
        if st and st.get("fallen") == race:
            mark += "  [UNDER THE YOKE]"
        print(f"the {race} lands:{mark}")
        for s in settlements:
            open_q = sum(1 for qid in s["quests"]
                         if world["quests"][qid]["status"] == "open")
            here = "  <- the party" if s["key"] == loc["place"] else ""
            print(f"  {s['name']} ({s['kind']}) -- {open_q} open "
                  f"quest(s){here}")
        cast = [n for n in world.get("npcs", []) if n["land"] == race]
        if cast:
            print("  notables: " + "; ".join(f"{n['name']} ({n['role']}, "
                                             f"at {n['seat']})"
                                             for n in cast))
        for p in state.get("places", []):
            if p["land"] == race:
                here = ("  <- the party"
                        if p["name"].lower() == loc["place"] else "")
                print(f"  {p['name']} (wilds, found day {p['day']}){here}")
    for line in story.war_status_lines(world, st):
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
    for flag, action in (("drink", "drink"), ("heal", "heal"),
                         ("berserk", "berserk"),
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
            if action == "heal" and hero.items.get("healing", 0) <= 0:
                print(f"{hero.name} carries no healing potion.")
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
                         actions=actions or None,
                         standing_orders=play_orders(True))
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
                     quest=pending.get("quest"),
                     streak_pos=pending.get("streak_pos"),
                     dead_before=pending.get("dead_before"))


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
        if not wiped:
            satisfaction_after_fight(party, pending.get("dead_before") or [],
                                     log, fled=True)
        print_combat(log)
        save(state)
        report_game_over(party, wiped)
        return

    # Run down: the fight resumes at once, the parting damage already taken.
    pause = group_combat(living, pending["foes"], rng, log,
                         pause_triggers=True, fired=pending["fired"],
                         first_round=pending["round"] + 1,
                         standing_orders=play_orders(True))
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
                     quest=pending.get("quest"),
                     streak_pos=pending.get("streak_pos"),
                     dead_before=pending.get("dead_before"))


def cmd_rest(args: argparse.Namespace) -> None:
    state = load()
    if not require_no_pending(state):
        return
    party, clock = state["party"], state["clock"]
    log: list[str] = []
    _short_rest([h for h in party if h.alive], clock, log)
    print("\n".join(log) if log else "(nothing happened)")
    save(state)


MAX_HEAL_CAMP_NIGHTS = 14   # `camp --heal` safety valve: HP knits at
                            # ~max_hp/7 a night, so a week-and-change always
                            # reaches full from anywhere


def cmd_camp(args: argparse.Namespace) -> None:
    """One night by default; `camp N` strings several together and `camp
    --heal` camps until every living hero's HP is full (2026-07-11 -- the
    played default is camping until whole, see dm.md). Each WILDS night
    rolls its own visitor and a fight interrupts the stay on the spot --
    a long convalescence in the open is a real gamble, days x risk."""
    state = load()
    if not require_no_pending(state):
        return
    party, clock = state["party"], state["clock"]
    nights = MAX_HEAL_CAMP_NIGHTS if args.heal else max(1, args.nights)
    streak = state.get("streak") or {"site": None, "count": 0}
    if streak["count"]:
        print(f"    (the night breaks the momentum at {streak['site']} "
              f"-- the next encounter pays base XP again)")
    reset_streak(state)
    clear_sighting(state)
    for _ in range(nights):
        log: list[str] = []
        _long_rest(party, clock, log)
        night_upkeep(state, log)
        print("\n".join(log))
        if state.get("world") and state["location"]["kind"] != "settlement":
            # A night in the wilds is not a night behind walls (2026-07-10):
            # the fire can draw a visitor. Rolled after the night's recovery;
            # a fight cuts the stay short -- what remains of it is the
            # player's call again afterward.
            if wild_event(state, CAMP_ENCOUNTER_CHANCE,
                          f"In the night at {state['location']['name']}"):
                return
        if args.heal and all(h.dead or h.hp >= h.max_hp for h in party):
            break
    if args.heal:
        print(f"  The party breaks camp whole on day {clock.day}.")
    save(state)


def cmd_tavern(args: argparse.Namespace) -> None:
    """A paid night at the inn (settlements only): long rest plus the one-day
    HP/STA overcharge (rpg.tavern_rest), +1 companion satisfaction, and the
    evening's company -- a fresh set of recruit candidates (the hiring
    surface: rolled once per paid night). Resets the streak like any night;
    anyone at the end of their patience walks at the morning."""
    state = load()
    if not require_no_pending(state):
        return
    if local_settlement(state) is None:
        print(f"No tavern out here -- the party is at {location_line(state)}."
              f" Beds are settlement comfort; in the wilds it's `camp`.")
        return
    here = occupied_here(state)
    if here is not None:
        print(occupation_line(state, here))
        return
    log: list[str] = []
    if not _tavern_rest(state["party"], state["clock"], state["purse"], log):
        print("\n".join(log))
        return
    night_upkeep(state, log)
    streak = state.get("streak") or {"site": None, "count": 0}
    if streak["count"]:
        log.append(f"    (the night breaks the momentum at {streak['site']} "
                   f"-- the next encounter pays base XP again)")
    reset_streak(state)
    clear_sighting(state)
    process_departures(state, log)
    roll_recruits(state)
    summary = recruit_summary_lines(state)
    if summary:
        log.append("  In the common room tonight (see `recruit`, sign with "
                   "`hire NAME`):")
        log.extend(summary)
    maybe_post_wave(state, log)     # tavern talk is where war news lands
    print("\n".join(log))
    save(state)


def cmd_downtime(args: argparse.Namespace) -> None:
    """A full day off in a settlement (the satisfaction lever the player
    controls): every companion gains SAT_DOWNTIME, or SAT_DOWNTIME_MATCH
    when the place suits a trait (an interest where it thrives, patriotic
    ground, a capital's temples for the religious). Ends in a free
    settlement night (long rest, streak reset, day advances)."""
    state = load()
    if not require_no_pending(state):
        return
    here = local_settlement(state)
    if here is None:
        print(f"A day off wants walls and company -- the party is at "
              f"{location_line(state)}. In the wilds the night is `camp`.")
        return
    if occupied_here(state) is not None:
        print(occupation_line(state, here))
        return
    party, clock = state["party"], state["clock"]
    log: list[str] = [f"  The party takes a day off at {here['name']}."]
    for h in party[1:]:
        if h.dead or not satisfaction_tracked(h):
            continue
        why = downtime_match(h, here)
        if why:
            adjust_satisfaction(h, SAT_DOWNTIME_MATCH, log, why)
        else:
            adjust_satisfaction(h, SAT_DOWNTIME, log, "a day off their feet")
    _long_rest(party, clock, log)
    night_upkeep(state, log)
    streak = state.get("streak") or {"site": None, "count": 0}
    if streak["count"]:
        log.append(f"    (the day breaks the momentum at {streak['site']} "
                   f"-- the next encounter pays base XP again)")
    reset_streak(state)
    clear_sighting(state)
    process_departures(state, log)
    maybe_post_wave(state, log)
    print("\n".join(log))
    save(state)


CHATTER_PROMPTS = {
    "temperament": "their {v} streak colors the evening",
    "quirk": "the old preoccupation surfaces: {v}",
    "interest": "talk drifts to {v} -- their favorite subject",
    "weakness": "the {v} itch is acting up",
    "background": "a story from their {v} days comes out",
    "speech": "holding forth, {v} as ever",
    "voice": "that {v} voice carries over the fire",
    "dress": "fussing over their {v} clothes",
    "looks": "someone needles them about their looks ({v}); they answer",
}


def cmd_chatter(args: argparse.Namespace) -> None:
    """A chatter seed for the DM's party-flavor beat (dm.md): who is
    preoccupied with what, drawn from traits + current satisfaction. Uses
    an UNSEEDED rng on purpose -- flavor must never perturb the game's
    dice -- and changes no state (nothing is saved)."""
    state = load()
    party = state["party"]
    companions = [h for h in party[1:] if not h.dead]
    if not companions:
        print("No companions along -- the road is quiet.")
        return
    rng = random.Random()
    print("CHATTER SEED (riff briefly -- a line or three of party talk):")
    for h in rng.sample(companions, min(2, len(companions))):
        mood = ""
        if satisfaction_tracked(h):
            if wants_to_leave(h):
                mood = "; one boot already out the door"
            elif h.satisfaction <= 3:
                mood = f"; sullen and gone quiet (satisfaction "\
                       f"{h.satisfaction})"
            elif h.satisfaction >= 9:
                mood = "; in high spirits"
        cat, val = rng.choice(sorted(h.traits.items()))
        prompt = CHATTER_PROMPTS[cat].format(v=val)
        print(f"  {h.name} ({h.race} {h.sex}, {cat}: {val}{mood}) -- "
              f"{prompt}.")


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
    elif thing == "meds":
        # The "needs meds" weakness: a dose every MEDS_INTERVAL_DAYS days,
        # compounded only in a capital, or the nightly drain sets in.
        if not has_trait(hero, "needs meds"):
            print(f"{hero.name} has no need of medicine.")
            return
        here = local_settlement(state)
        if here is None or here["kind"] != "capital":
            print(f"Doses are compounded only in a capital -- the party is "
                  f"at {location_line(state)}.")
            return
        if purse.gold < MEDS_PRICE:
            print(f"Not enough gold for a dose ({purse.gold}g / "
                  f"{MEDS_PRICE}g).")
            return
        purse.gold -= MEDS_PRICE
        hero.last_dose_day = state["clock"].day
        log.append(f"    {hero.name} buys a dose of their medicine for "
                   f"{MEDS_PRICE}g (good for {MEDS_INTERVAL_DAYS} days; "
                   f"purse: {purse.gold}g).")
        adjust_satisfaction(hero, 1, log, "the shakes ease")
    else:
        print(f"Unknown purchase: {thing!r}. Potions: {', '.join(POTION_KINDS)}. "
              f"Weapons: {', '.join(sorted(WEAPONS))}. Also: meds.")
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

    p = sub.add_parser(
        "new",
        help="start a fresh game (overwrites save): rolls the world and "
             "THREE player-character candidates -- choose with `pick`")
    p.add_argument("--seed", type=int, default=None)
    p.set_defaults(func=cmd_new)

    p = sub.add_parser(
        "pick",
        help="choose the player character from `new`'s three candidates "
             "(by number or name). His CHA sets the party's companion "
             "capacity for the whole game; if it holds anyone at all, an "
             "old ally joins on the spot (a random level-1 companion, free) "
             "and the first evening's recruit introductions follow.")
    p.add_argument("who", nargs="+", help="candidate number (1-3) or name")
    p.set_defaults(func=cmd_pick)

    p = sub.add_parser(
        "recruit",
        help="the full sheets of the candidates gathered at this "
             "settlement's tavern (rolled at each paid `tavern` night, "
             "leveled to the PC +-1; a quarter are bonded pairs -- one "
             "option, two heads). Everything is shown: transparency over "
             "realism, like the board's straight levels.")
    p.set_defaults(func=cmd_recruit)

    p = sub.add_parser(
        "hire",
        help="sign a candidate on (a pair signs together). Hard-capped by "
             "the PC's CHA (capacity = CHA - 3, up to 3); a fresh hire "
             "starts at satisfaction 7/10 and any joining gold (wealthy/"
             "luxurious) goes to the purse.")
    p.add_argument("name", nargs="+", help="candidate name (substring)")
    p.set_defaults(func=cmd_hire)

    p = sub.add_parser(
        "dismiss",
        help="let a companion go (settlements only): they take the same "
             "equal head-split of the purse a quitter takes, plus their "
             "carried gear; a bond partner walks with them. Swapping the "
             "party out is deliberately not free.")
    p.add_argument("name", nargs="+", help="companion name (substring)")
    p.set_defaults(func=cmd_dismiss)

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
             "--drink HERO (stamina draught), --heal HERO (healing potion), "
             "--berserk HERO (HP -> STA), "
             "--warbreath HERO (Power -> STA). Plain resume = fight on. "
             "The fight then runs to its END -- an encounter pauses at most "
             "once (its first wounds crossing); every later crossing is "
             "answered by the party's standing orders (drink/heal/convert "
             "on their own, skipped when the fight is already winding down).")
    p.add_argument("--drink", action="append", metavar="HERO")
    p.add_argument("--heal", action="append", metavar="HERO")
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

    p = sub.add_parser(
        "camp",
        help="long rest: full STA, weekly HP tick, advances a day -- and "
             "RESETS the same-site momentum streak (consecutive same-site "
             "encounters without a camp pay rising XP; camping mid-site "
             "trades that pay for safety). `camp N` strings N nights "
             "together; `camp --heal` camps until every living hero's HP "
             "is full (the played default -- see dm.md). A night camped in "
             "the WILDS (not at a settlement) risks a visitor "
             f"(~{int(CAMP_ENCOUNTER_CHANCE * 100)}%% PER NIGHT, the "
             f"road's table) and a fight cuts the stay short.")
    p.add_argument("nights", type=int, nargs="?", default=1,
                   help="how many nights (default 1)")
    p.add_argument("--heal", action="store_true",
                   help="camp until every living hero's HP is full")
    p.set_defaults(func=cmd_camp)

    p = sub.add_parser(
        "tavern",
        help=f"a paid night at the inn (settlements only, "
             f"{TAVERN_COST_PER_HERO}g per living member): a full long rest "
             f"plus a ONE-DAY OVERCHARGE -- everyone wakes with HP and STA "
             f"+{int(TAVERN_OVERCHARGE * 100)}%% of max (min 1) ABOVE their "
             f"caps; the excess can't be healed back and fades at the next "
             f"night's rest. Also +1 companion satisfaction, and the "
             f"evening gathers a fresh set of recruit candidates. Resets "
             f"the momentum streak like any night.")
    p.set_defaults(func=cmd_tavern)

    p = sub.add_parser(
        "downtime",
        help="a full day off in a settlement: +1 satisfaction to every "
             "companion (+2 where the place suits a trait -- an interest "
             "where it thrives, patriotic ground, a capital's temples), "
             "then a free night (long rest, day advances, streak resets). "
             "The deliberate morale lever -- it costs a day the streak "
             "economy would rather spend fighting.")
    p.set_defaults(func=cmd_downtime)

    p = sub.add_parser(
        "board",
        help="the DM's LOCAL quest inventory (2026-07-12: in play there is "
             "no board -- each job belongs to its GIVER, and asking around "
             "funnels to that person in one message, see dm.md). Rows show "
             "level (straight), shape, pay, and the giver; plus notables "
             "in town, WORD FROM AROUND THE LAND (other open jobs in this "
             "land), and the war's status. Only local jobs can be taken "
             "here. `board all` / `board NAME` is the wider DM overview.")
    p.add_argument("settlement", nargs="?", default=None)
    p.set_defaults(func=cmd_board)

    p = sub.add_parser(
        "chatter",
        help="a party-chatter seed for the DM's flavor beat: 1-2 "
             "companions, what they're preoccupied with (traits + "
             "satisfaction). Unseeded rng, no state change -- pure "
             "flavor, safe to call any time.")
    p.set_defaults(func=cmd_chatter)

    p = sub.add_parser(
        "map",
        help="the known world: the race lands, their settlements (with open "
             "quest counts), discovered wild places, and where the party "
             "stands")
    p.set_defaults(func=cmd_map)

    p = sub.add_parser(
        "travel",
        help=f"move to a settlement or discovered place: "
             f"{TRAVEL_DAYS_IN_LAND} day within a land, {TRAVEL_DAYS_CROSS} "
             f"days to another land. Every travel day is a camp night "
             f"(overnight recovery -- travel heals; it also resets the "
             f"momentum streak) and risks a road encounter "
             f"(~{int(TRAVEL_ENCOUNTER_CHANCE * 100)}%%/day, ANY level -- "
             f"the higher the rarer; foes far above the party are usually "
             f"spotted at range first, but can ambush, and even ordinary "
             f"trouble is spotted first ~{int(WILD_SPOTTED_CHANCE * 100)}%% "
             f"of the time)")
    p.add_argument("dest", nargs="+", help="settlement or place (substring)")
    p.set_defaults(func=cmd_travel)

    p = sub.add_parser(
        "explore",
        help=f"a day ranging the current land's wilds: discovers a new "
             f"place (pays {EXPLORE_XP} XP, persists on the map), camps "
             f"rough (overnight recovery, streak reset), and beats more "
             f"bushes than the road "
             f"({int(EXPLORE_ENCOUNTER_CHANCE * 100)}%% encounter chance)")
    p.set_defaults(func=cmd_explore)

    p = sub.add_parser(
        "hunt",
        help="stalk prey in the current land's wilds NOW (no day cost): a "
             "guaranteed encounter at-or-below the party's level -- the "
             "always-available farm loop, paying wild (below-board) XP "
             "rates plus normal loot rolls. But "
             f"~{int(HUNT_AMBUSH_CHANCE * 100)}%% of hunts the hunter is "
             f"the hunted: an AMBUSH off the road's any-level table")
    p.set_defaults(func=cmd_hunt)

    p = sub.add_parser(
        "engage",
        help="close with the foes SIGHTED on the road or afield (see "
             "status) -- the player picking the over-their-weight fight on "
             "purpose. Any other move lets the sighting drift on.")
    p.set_defaults(func=cmd_engage)

    p = sub.add_parser(
        "show",
        help="one quest in full: description, sites, rooms, and what holds "
             "each room (by skinned display name)")
    p.add_argument("quest", help="quest id (q07, or just 7)")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser(
        "take",
        help="make a board quest the ACTIVE quest (the party must be AT the "
             "settlement that posted it); `room` then fights its encounters "
             "in order. Switching quests keeps the old one's progress -- "
             "come back to it whenever.")
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
        help="spend gold on a potion, a weapon, or (in a capital) a dose of "
             "meds for one hero (weapons are equipped on the spot; plain "
             "tier only -- masterwork/legendary are never shopped). Note "
             f"the kit restocks itself: every long rest tops each hero "
             f"back up to {KIT_HEALING} healing + {KIT_STAMINA} stamina "
             f"free -- buying is for stocking ABOVE that line.")
    p.add_argument("hero")
    p.add_argument("thing", nargs="+",
                   help="a potion kind, a weapon name (e.g. rapier, "
                        "wooden staff), or 'meds'")
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
