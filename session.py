"""DM session driver -- runs the game turn-by-turn from the terminal.

rpg.py's primitives (start_fight, group_combat, short_rest, long_rest, ...)
are meant to be called on purpose, in whatever order the story wants (see
develop.md, "The feel we're going for"). But each terminal call is a fresh
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

party[0] is the PLAYER CHARACTER (GENERATED at `new` since 2026-07-13 --
no candidate pick; his CHA always holds at least one companion, and a
long-time companion starts at his side). PC death ends the game even if a
companion stands. CHA gates how many companions the party can hold; every
companion carries a satisfaction track and quits (with a head-split of the
purse) if it hits bottom -- see rules.md's Party, Charisma & Satisfaction
add-on. Companions AUTOLEVEL (rpg.autospend_points); only the PC banks
skill points for the player to spend.

The shape of a playthrough:
  new / status / levelup                    -- starting and reading the party
  recruit / hire NAME / dismiss NAME        -- the hiring layer (recruit
                                               rolls the day's faces ON
                                               REQUEST, settlements only)
  map / travel / explore / hunt / engage    -- the world & the wilds
  board / show QID / take QID / room        -- the LOCAL jobs (the game;
                                               board = the DM inventory,
                                               in play quests come from
                                               their GIVERS -- dm.md)
  chatter                                   -- a party-flavor seed (dm.md)
  fight N                                   -- off-script encounters
  hideout ROOM / barrow ROOM                -- the two set sites (DEV/TEST
                                               only since 2026-07-13; not
                                               part of a played campaign)
  resume [...] / retreat [--blink]          -- settle a paused fight
  rest / camp / tavern / downtime / award / buy / give / train / use / heal
  prices                                    -- the shop price sheet (DM ref)
  cast HERO scry|teleport                   -- the between-fights layer
                                               (cast = wizard utility magic)
  forge                                     -- DM-built quest, off the board
  sheet                                     -- commit party.txt (run at the
                                               END of every DM message)

All output is wrapped at WRAP_WIDTH columns (the designer plays on a phone
whose code blocks show ~41 characters and never soft-wrap).
"""
from __future__ import annotations

import argparse
import builtins
import dataclasses
import json
import random
import subprocess
import textwrap
from pathlib import Path

from rpg import (
    Clock, CombatLog, Purse, Entity, Weapon, POTION_KINDS, WEAPONS,
    POTION_PRICE,
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
    streak_multiplier,
    start_fight, group_combat, party_wiped,
    attempt_retreat, refresh_foes_after_retreat,
    award_xp, roll_loot, award_quest,
    short_rest as _short_rest, long_rest as _long_rest,
    tavern_rest as _tavern_rest,
    buy_potion as _buy_potion, cast_healing as _cast_healing,
    use_potion as _use_potion, buy_weapon as _buy_weapon,
    equip_weapon as _equip_weapon,
    train_combat_once as _train_combat_once,
    train_proficiency as _train_proficiency,
    train_spell as _train_spell,
    buy_spellbook as _buy_spellbook,
    buy_pool as _buy_pool, learn_ability as _learn_ability,
    learn_move as _learn_move, MOVES, move_weapon_ok,
    train_alchemy as _train_alchemy, brew as _brew, auto_brew,
    alchemy_recipes, brew_stock_cap, alchemy_cost,
    ALCHEMY_MAX, ALCHEMY_BATCH, ALCHEMY_RECIPE_RANK, POTION_DISPLAY,
    DRINKABLE_KINDS,
    ABILITIES, ability_tags, training_cost,
    POOL_KINDS, POOL_BUY_CAP, SKILL_POINTS_PER_LEVEL,
    storyteller_tale, survivalist_camp,
    blink_escape, casting_check,
    SPELLS, SPELL_RANK_MAX, SPELLBOOK_PRICE, VANISH_POWER_COST,
    SCRY_POWER_COST, TELEPORT_TRAVEL_COST_PER_DAY, TELEPORT_ESCAPE_COST,
    autospend_points,
    ROOM_FIELD, WILD_FIELD, AMMO_LOTS, AMMO_CAPS, RANGED_WEAPONS,
    buy_ammo as _buy_ammo, grant_starter_ammo,
)
import story
import karma
from people import (make_character, make_pair, character_sheet, person_line,
                    npc_line, downtime_match, joining_gold, PAIR_CHANCE)
from sites import SITES, FOES, BANDIT_KINDS, WEAPON_INDEX, make_foe, roster_lines
from quests import (generate_world, forge_quest, board_lines, site_gold_for,
                    quest_detail_lines, quest_line, roster_kinds_line,
                    level_grade, seen_level, mind_precision,
                    lands, roll_wild_level, build_wild_encounter,
                    wild_encounter_xp,
                    TRAVEL_DAYS_IN_LAND, TRAVEL_DAYS_CROSS,
                    TRAVEL_ENCOUNTER_CHANCE, EXPLORE_ENCOUNTER_CHANCE,
                    EXPLORE_XP, SPOTTED_MARGIN, AMBUSH_CHANCE,
                    HUNT_AMBUSH_CHANCE,
                    CAMP_ENCOUNTER_CHANCE,
                    HUNT_LEVEL_REACH, WILD_NAME_PARTS,
                    notice_contest, foes_preferred_field)

STATE_PATH = Path(__file__).parent / "save.json"

# --------------------------------------------------------------------------- #
# Output wrapping (2026-07-13) -- the designer plays through Claude Code on
# the web, on a phone whose code blocks show ~41 characters and never
# soft-wrap. EVERYTHING this driver prints (and party.txt) is therefore
# hard-wrapped at WRAP_WIDTH, continuation lines hanging two spaces past the
# original indent. Short lines pass through untouched.
# --------------------------------------------------------------------------- #

WRAP_WIDTH = 40


def _wrap_block(text: str) -> str:
    out: list[str] = []
    for line in text.split("\n"):
        if len(line) <= WRAP_WIDTH:
            out.append(line)
            continue
        indent = len(line) - len(line.lstrip(" "))
        cont = " " * min(indent + 2, WRAP_WIDTH // 2)
        out.extend(textwrap.wrap(line, WRAP_WIDTH, subsequent_indent=cont,
                                 break_long_words=False,
                                 break_on_hyphens=False) or [""])
    return "\n".join(out)


def print(*args, sep=" ", end="\n", **kwargs):  # noqa: A001 -- shadowing on
    """purpose: every print in this module goes out phone-wrapped."""
    builtins.print(_wrap_block(sep.join(str(a) for a in args)),
                   end=end, **kwargs)


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
# "kind": "settlement" | "wild"}. The two hand-built DEV/TEST set sites
# (hideout / barrow) lie outside the capital (the first settlement worldgen
# made); a new game starts wherever the lowest-level job is posted.

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
    """The capital (settlements[0]) -- the two hand-built DEV/TEST set
    sites lie outside it. (Since 2026-07-13 a new game starts at the
    settlement with the lowest-level job, which may be elsewhere.)"""
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
    # JSON has no sets: abilities, moves, and the per-fight moves_spent travel
    # as sorted lists.
    d["abilities"] = sorted(e.abilities)
    d["moves"] = sorted(e.moves)
    d["moves_spent"] = sorted(e.moves_spent)
    # feint_target is a live Entity reference (a per-fight state); it can't be
    # serialized by identity, so a feint set up the instant a fight pauses
    # simply doesn't carry across the save -- a negligible edge.
    d["feint_target"] = None
    return d


def _entity_from_dict(d: dict) -> Entity:
    d = dict(d)
    d["weapon"] = _weapon_from(d["weapon"])
    d["abilities"] = set(d.get("abilities", ()))
    d["moves"] = set(d.get("moves", ()))
    d["moves_spent"] = set(d.get("moves_spent", ()))
    d["feint_target"] = None
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
        "field": pending.get("field", 0),
        "align": pending.get("align", "neutral"),
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
        "field": d.get("field", 0),
        "align": d.get("align", "neutral"),
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
        elif q.get("kind") == "delivery":
            lines.append(f"active quest: [{qid}] DELIVERY {q['name']} -- "
                         f"carry {q['cargo']} to {q['dest_name']} "
                         f"(travel {q['dest']})")
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
    """Write party.txt (phone-wrapped, like all output) on every save.
    NEVER raises: a broken disk must not take the game loop down with it.
    COMMITTING the sheet is `sheet`'s job (2026-07-13): one commit at the
    end of every DM message, not one per command -- the designer reads the
    playthrough as message-sized diffs."""
    try:
        PARTY_SHEET_PATH.write_text(
            _wrap_block("\n".join(party_sheet_lines(state))) + "\n",
            encoding="utf-8")
    except Exception:
        return


def cmd_sheet(args: argparse.Namespace) -> None:
    """Rewrite party.txt from the save and commit it (that one file only).
    The DM runs this at the END of every message (dm.md) so the sheet's
    history reads one commit per message. Committing nothing (the sheet
    didn't change) is fine and says so."""
    state = load()
    _write_party_sheet(state)
    day = state["clock"].day
    where = (state["location"]["name"]
             if state.get("location") else "nowhere")
    try:
        root = Path(__file__).parent
        subprocess.run(["git", "add", "party.txt"], cwd=root, check=False,
                       capture_output=True, timeout=15)
        done = subprocess.run(
            ["git", "commit", "--quiet",
             "-m", f"party sheet: day {day} at {where}", "--", "party.txt"],
            cwd=root, check=False, capture_output=True, timeout=15)
    except Exception as exc:
        print(f"party.txt written; commit failed ({exc}) -- the game is "
              f"unaffected.")
        return
    if done.returncode == 0:
        print(f"party.txt committed (day {day} at {where}).")
    else:
        print("party.txt unchanged -- nothing to commit.")


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
        "recruits": state.get("recruits"),
        "visited": state.get("visited", []),
        "karma": state.get("karma") or karma.new_karma(),
        "dark_board": state.get("dark_board"),
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
        "recruits": doc.get("recruits"),
        "visited": doc.get("visited")
        or ([location["place"]]
            if location and location.get("kind") != "wild" else []),
        "karma": doc.get("karma") or karma.new_karma(),
        "dark_board": doc.get("dark_board"),
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


def party_mind(state: dict) -> int:
    """The party's best living MIND -- the reader of quest levels (quest
    sight, Magic & Mind): 6 reads exact, 4-5 within one level, 3 and under
    within two. Hiring the bookish companion sharpens the whole board."""
    return max((h.mind for h in state["party"] if not h.dead), default=0)


def print_combat(log: CombatLog) -> None:
    """Print the full (DM/debug) log, then the simplified player-facing block
    -- the piece meant to be pasted into the chat as-is (see rules.md,
    "Reading the combat log")."""
    print("\n".join(log))
    if log.player:
        print()
        print("--- PLAYER LOG (paste into chat as-is) ---")
        print("\n".join(log.player))


def tally_lines(state: dict) -> list[str]:
    """The standard after-the-fight DISPLAY block, appended to every
    encounter's player log: the party's tracks and kit, the purse, the
    day's rests, and -- for an active site -- how many rooms are LEFT
    plus the streak's next multiplier. The numbers are SHOWN here so the
    DM's prose never has to carry them (dm.md, narration style); ahead of
    the party it gives a count only, never a roster -- upcoming room
    contents are DM eyes only."""
    party, clock, purse = state["party"], state["clock"], state["purse"]
    lines = ["", "-- the party --"]
    for h in party:
        if h.dead:
            continue
        tag = " [DOWN]" if h.down else ""
        kit = ", ".join(f"{k} x{v}" for k, v in h.items.items() if v)
        lines.append(f"{h.name.split()[0]}: HP {h.hp}/{h.max_hp}  "
                     f"STA {h.cur_sta}/{h.sta}  "
                     f"Power {h.cur_power}/{h.power}{tag}")
        lines.append(f"  ({kit or 'no kit'})")
    lines.append(f"Purse {purse.gold}g; {clock.short_rests_left} short "
                 f"rest(s) left today.")
    k = state.get("karma")
    if k and k.get("bad_total"):
        lines.append(f"Karma: {karma.karma_line(k, party_level(state))}.")
    qid = state.get("active_quest")
    world = state.get("world")
    if qid and world:
        q = world["quests"][qid]
        if q["status"] == "open" and q.get("kind") != "delivery":
            cur = q["next"]
            s = q["sites"][cur["site"]]
            left = len(s["rooms"]) - cur["room"]
            sites_after = len(q["sites"]) - cur["site"] - 1
            ahead = f"Ahead: {left} room(s) in {s['name']}"
            if sites_after:
                ahead += f", then {sites_after} more site(s)"
            site_key = f"{qid}/s{cur['site'] + 1}"
            mult = streak_multiplier(streak_pos_for(state, site_key))
            lines.append(f"{ahead}; the next pays x{mult:g}.")
    return lines


def append_tally(state: dict, log: CombatLog) -> None:
    """Close a survived encounter's player log with the tally block."""
    party = state["party"]
    if party and not party[0].dead:
        for line in tally_lines(state):
            log.append(line)


def require_no_pending(state: dict) -> bool:
    """Most commands are between-fights actions; refuse them mid-melee."""
    if not state["party"]:
        print("No party in this save -- `new` starts a game.")
        return False
    if state.get("pending"):
        print("A fight is PAUSED -- the party is mid-melee. Resolve it "
              "first: resume [--drink HERO] [--heal HERO] [--berserk HERO] "
              "[--warbreath HERO], or retreat.")
        return False
    return True


def _starting_settlement(world: dict) -> dict:
    """Where a new game begins (2026-07-13): the settlement posting the
    world's LOWEST-level open COMBAT quest, so the opening hook is a job a
    fresh party can actually take. Deliveries are excluded (2026-07-19 fix:
    they carry level 0, so a settlement with a delivery and only high-level
    combat work used to win this contest -- and the hook, which is always
    a combat job, then opened the game on a level-5 door). (The capital --
    settlements[0] -- keeps its story-layer role regardless of where the
    party starts.)"""
    def lowest(s: dict) -> int:
        levels = [world["quests"][qid]["level"] for qid in s["quests"]
                  if world["quests"][qid]["status"] == "open"
                  and world["quests"][qid].get("kind") != "delivery"]
        return min(levels) if levels else 99
    return min(world["settlements"], key=lowest)


def opening_hook(state: dict) -> list[str]:
    """The job the game opens on (2026-07-13, designer call: the game
    starts at the doorstep of a combat quest, not in a tavern): the most
    level-appropriate open quest where the party stands. The DM frames
    the first scene in front of its giver, mid-pitch; taking it stays the
    player's call."""
    world = state["world"]
    here = local_settlement(state)
    if here is None:
        return []
    open_q = [world["quests"][qid] for qid in here["quests"]
              if world["quests"][qid]["status"] == "open"
              and world["quests"][qid].get("kind") != "delivery"]
    if not open_q:      # (a delivery never opens the game -- combat does)
        return []
    q = min(open_q, key=lambda q: (q["level"], q["id"]))
    lines = [f"OPENING HOOK -- frame the first scene at this job's "
             f"doorstep (dm.md); taking it is the player's call:",
             f"  [{q['id']}] L{q['level']} {q['name']}"]
    g = q.get("giver")
    if g:
        lines.append(f"  giver: {npc_line(g)}")
    return lines


def cmd_new(args: argparse.Namespace) -> None:
    rng = random.Random(args.seed)
    # The PC is GENERATED, not chosen (2026-07-13, designer call -- the old
    # three-candidate pick is gone): male by designer fiat, never with a
    # family quirk, rerolled until his CHA holds at least one companion --
    # a capacity-0 solo game was a trap dressed as a choice.
    while True:
        pc = make_character(rng, level=1, sex="m", no_family=True)
        if party_capacity(pc.cha) >= 1:
            break
    pc.protagonist = True   # fate's bargain guards the PC (rpg.Entity)
    used = {pc.name}
    # The long-time companion: generated with the PC and presented as
    # having been at his side for years (2026-07-13 reframe -- nobody
    # "joins" in the first scene), on a hire's terms otherwise.
    ally = make_character(rng, level=1, used_names=used)
    ally.satisfaction = SATISFACTION_START
    ally.bond, ally.bond_kind = pc.name, "old companion"
    world_seed = rng.randrange(1 << 30)     # derived, so --seed pins the
                                            # whole playthrough, world and all
    world = generate_world(world_seed)
    state = {"party": [pc, ally], "clock": Clock(), "purse": Purse(),
             "rng": rng, "foe_count": 0, "pending": None, "rooms": {},
             "world": world, "active_quest": None,
             "story": story.init_story(world, rng, pc_race=pc.race),
             "location": _settlement_location(_starting_settlement(world)),
             "places": [], "sighting": None,
             "streak": {"site": None, "count": 0}, "site_clears": {},
             "recruits": None,
             "karma": karma.new_karma(), "dark_board": None,
             # Settlements the party has stood in -- teleport (rank 3)
             # reaches only KNOWN ground (Magic & Mind).
             "visited": [_starting_settlement(world)["key"]]}
    if has_trait(ally, "needs meds"):
        ally.last_dose_day = state["clock"].day
    state["purse"].gold += joining_gold(pc) + joining_gold(ally)
    save(state)
    print(f"New game (seed={args.seed}).")
    print(f"You are {pc.name}.")
    for line in character_sheet(pc, for_pc=True):
        print("  " + line)
    cap = party_capacity(pc.cha)
    print(f"  presence: CHA {pc.cha} -- the party can hold {cap} "
          f"companion(s).")
    print(f"{ally.name} has walked at {pc.name}'s side for years:")
    for line in character_sheet(ally):
        print("  " + line)
    if state["purse"].gold:
        print(f"The party purse holds {state['purse'].gold}g.")
    print(f"The party stands at {location_line(state)} -- the local jobs "
          f"are `board`; the wider world is `map` and `travel`.")
    for line in opening_hook(state):
        print(line)
    print("(The story layer is armed: a war is seeded in this world and "
          "its first word finds a level-2 party in a settlement. DM: see "
          "dm.md, The war.)")


# --------------------------------------------------------------------------- #
# Recruiting, departures, and the nightly upkeep (the companion layer)
# --------------------------------------------------------------------------- #

def roll_recruits(state: dict) -> None:
    """Roll a settlement day's recruit candidates: as many OPTIONS as
    the PC's CHA capacity (three choices even if only one slot is free --
    seeing the market is part of the pitch), each leveled to the PC +-1,
    a quarter of them bonded pairs (one option, two heads). Rolled ON
    REQUEST by `recruit` (2026-07-13 -- the tavern stopped popping
    candidates unasked), once per settlement per day: the day is the
    reroll gate."""
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


def local_recruits(state: dict) -> dict | None:
    """The candidate pool waiting where the party stands, if any -- rolled
    TODAY (a stale pool has drifted back into the crowd; `recruit` rolls a
    fresh one on request)."""
    rec = state.get("recruits")
    here = local_settlement(state)
    if (not rec or here is None or rec["place"] != here["key"]
            or rec["day"] != state["clock"].day):
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
        here = local_settlement(state)
        if here is None:
            print(f"No one to recruit out here -- the party is at "
                  f"{location_line(state)}. Hiring happens in settlements.")
            return
        if occupied_here(state):
            print(occupation_line(state, here))
            return
        # Rolled on request (2026-07-13): asking around the taproom
        # gathers today's faces -- once per settlement per day.
        roll_recruits(state)
        rec = local_recruits(state)
        if rec is None:
            print(f"Nobody in {here['name']} is looking for this kind of "
                  f"work today.")
            save(state)
            return
        print(f"Asking around {here['name']} turns up today's faces:")
        save(state)
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
        # Companions manage their own points (2026-07-13): any banked
        # arrival points go on the doctrine right away.
        autospend_points(m, log)
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


def companions_brew(state: dict, log: list[str]) -> None:
    """After a long rest, an alchemist COMPANION brews on the sim policy
    (auto_brew: firebombs for a damage build, else strength, else healing) --
    like the autolevel, the companions' brew is automatic while the PC's
    (party[0]) is the player's own `brew` call. Once per night."""
    rng = state["rng"]
    clock = state["clock"]
    for h in state["party"][1:]:
        if h.dead or h.alchemy <= 0 or h.last_brew_day == clock.day:
            continue
        if auto_brew(h, rng, log):
            h.last_brew_day = clock.day


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
        elif q.get("kind") == "delivery":
            print(f"  Active quest: [{qid}] DELIVERY {q['name']} -- carry "
                  f"{q['cargo']} to {q['dest_name']} "
                  f"(`travel {q['dest']}`; arriving is the turn-in).")
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
    k = state.get("karma")
    if k and (k.get("bad_total") or k.get("good_total")):
        print(f"  Karma: {karma.karma_line(k, party_level(state))} "
              f"(lifetime {k['bad_total']} wickedness / "
              f"{k['good_total']} penance; see `karma`).")
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
    if any(not h.dead and "berserk" in h.abilities for h in party):
        print(f"    resume --berserk HERO     -- {BERSERK_HP_COST} HP -> "
              f"+{BERSERK_STA_GAIN} STA (the wound penalty deepens; "
              f"knowers only)")
    if any(not h.dead and "war_breath" in h.abilities for h in party):
        print(f"    resume --warbreath HERO   -- {WAR_BREATH_POWER_COST} "
              f"Power -> +{WAR_BREATH_STA_GAIN} STA (knowers only)")
    if any(not h.dead and h.spell_rank("invisibility") >= 2 for h in party):
        print(f"    resume --vanish HERO      -- {VANISH_POWER_COST} Power: "
              f"fade from the melee (untargetable; the next strike lands "
              f"as an ambush)")
    blinker = next((h for h in party
                    if not h.dead and h.spell_rank("teleport") >= 2), None)
    print("    retreat                   -- parting blows from foes still "
          "fit to swing, then one group chase roll"
          + (" (the dead do not pursue past their ground)"
             if any(f.alive and not f.pursues for f in pending["foes"])
             else ""))
    if blinker is not None:
        print(f"    retreat --blink {blinker.name.split()[0]:<10}-- "
              f"teleport out: NO parting blows, no chase "
              f"({TELEPORT_ESCAPE_COST} Power; a fizzled door falls "
              f"back to the honest retreat)")
    smoker = next((h for h in party
                   if not h.dead and h.items.get("smoke", 0) > 0), None)
    if smoker is not None:
        print(f"    retreat --smoke {smoker.name.split()[0]:<10}-- "
              f"smoke vial: NO parting blows, but the chase still rolls "
              f"({smoker.items['smoke']} left)")


def print_levelup_menu(heroes: list) -> None:
    """The spending menu: what each hero's banked skill points can buy right
    now, with costs and effects -- printed automatically for the PC on every
    level-up (finish_encounter), instead of the DM paraphrasing the rules
    from memory."""
    for h in heroes:
        if h.dead:
            continue
        first = h.name.split()[0]
        print(f"{h.name} -- L{h.level}, {h.skill_points} skill point(s) banked "
              f"(XP {h.xp}/{xp_to_next(h.level)} to L{h.level + 1})")
        # Sink 1: the pools (the old automatic growth, on the menu now).
        pool_bits = []
        for kind in POOL_KINDS:
            bought = h.pool_bought.get(kind, 0)
            pool_bits.append(f"{kind.upper()} +{bought}"
                             + ("(CAP)" if bought >= POOL_BUY_CAP else ""))
        print(f"  pools  +1 max HP/STA/Power  costs 1 each  "
              f"(bought: {', '.join(pool_bits)}; cap +{POOL_BUY_CAP} per "
              f"pool)  -> train {first} hp|sta|power")
        # Sink 2: combat training (+1 to ALL pressure rolls per rank).
        if h.training >= TRAINING_MAX:
            print(f"  combat training      rank {h.training} -- CAPPED")
        else:
            cost = training_cost(h.training)
            mark = "CAN BUY" if h.skill_points >= cost else "can't afford yet"
            print(f"  combat training      rank {h.training} -> "
                  f"{h.training + 1}  costs {cost}  [{mark}]  "
                  f"(+1 to ALL pressure rolls per rank, cap {TRAINING_MAX})"
                  f"  -> train {first} combat")
        # Sink 2 (wizards): SPELL ranks -- the caster's real offense and
        # tricks (the weapon below is their out-of-Power fallback).
        if h.spells:
            for name, rank in sorted(h.spells.items()):
                spell = SPELLS[name]
                if rank >= spell.max_rank:
                    print(f"  {name}  rank {rank} -- CAPPED")
                else:
                    cost = rank + 1
                    mark = ("CAN BUY" if h.skill_points >= cost
                            else "can't afford yet")
                    print(f"  {name}  rank {rank} -> {rank + 1}  costs "
                          f"{cost}  [{mark}]  (next: {spell.ranks[rank]})"
                          f"  -> train {first} {name}")
            print(f"  (NEW spells come from spellbooks -- {SPELLBOOK_PRICE}g "
                  f"in a capital: buy {first} book SPELL; spells: "
                  f"{', '.join(sorted(SPELLS))})")
        # Sink 3: proficiency with the WIELDED weapon.
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
        # Sink 5: the ability catalog (single buys -- learn HERO NAME).
        known = ability_tags(h)
        if known:
            print(f"  abilities known: {', '.join(known)}")
        buyable = []
        for a in ABILITIES.values():
            if (a.name in h.abilities
                    or (a.requires and a.requires not in h.abilities)):
                continue
            mark = "*" if h.skill_points >= a.cost else ""
            buyable.append(f"{a.name} {a.cost}{mark}")
        if buyable:
            print(f"  abilities to learn (cost, * = affordable; "
                  f"learn {first} NAME): {', '.join(buyable)}")
        # Sink 7: alchemy (session C -- the brew skill; brew at camp, once
        # per long rest, off MIND). Open to all.
        if h.alchemy >= ALCHEMY_MAX:
            print(f"  alchemy              rank {h.alchemy} -- CAPPED "
                  f"(batch {ALCHEMY_BATCH[h.alchemy]}, stock cap "
                  f"{brew_stock_cap(h)})")
        else:
            cost = alchemy_cost(h.alchemy)
            mark = "CAN BUY" if h.skill_points >= cost else "can't afford yet"
            nxt = h.alchemy + 1
            unlocks = [POTION_DISPLAY[r] for r, need in
                       ALCHEMY_RECIPE_RANK.items() if need == nxt]
            gain = (f"; unlocks {', '.join(unlocks)}" if unlocks
                    else "")
            print(f"  alchemy              rank {h.alchemy} -> {nxt}  costs "
                  f"{cost}  [{mark}]  (brew {ALCHEMY_BATCH.get(nxt)} a night, "
                  f"stock cap {nxt + 2}{gain}; brew HERO RECIPE at camp)"
                  f"  -> train {first} alchemy")
        # Sink 6: the warrior moves (session B -- riders on the exchange, the
        # engine fires them; repertoire capped at combat training + 1, gated
        # by the wielded weapon's move tags). Shown to EVERYONE (2026-07-19
        # fix: the menu used to hide it from wizards, which read as a class
        # gate -- the free-allocation doctrine has none; the only gates are
        # the weapon's tags and the training cap).
        cap = h.training + 1
        if h.moves:
            print(f"  moves known ({len(h.moves)}/{cap}): "
                  f"{', '.join(sorted(h.moves))}")
        if len(h.moves) >= cap:
            print(f"  moves: repertoire full ({len(h.moves)}/{cap}) -- "
                  f"raise combat training for room")
        else:
            learnable = []
            for name, m in MOVES.items():
                if name in h.moves or not move_weapon_ok(name, h.weapon):
                    continue
                mark = "*" if h.skill_points >= m.cost else ""
                learnable.append(f"{name} {m.cost}{mark}")
            if learnable:
                print(f"  moves to learn (cost, * = affordable; "
                      f"train {first} move NAME): {', '.join(learnable)}")
            elif h.weapon is not None:
                print(f"  moves: none fit the {h.weapon.name}")


def cmd_levelup(args: argparse.Namespace) -> None:
    """The manual menu call: the PC's banked points (companions autolevel
    since 2026-07-13, so theirs is a readout, not a decision)."""
    state = load()
    print_levelup_menu(state["party"])


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
                      streak_pos: int | None = None,
                      field: int = 0, align: str = "neutral") -> None:
    """Shared tail of every encounter command: run the melee -- which may
    PAUSE once, at the fight's first wounds crossing (see play_orders) --
    then award and
    persist. On a pause the fight is saved as `pending` and the turn goes
    back to the player (resume / retreat next message). `quest` ties the
    encounter to a board quest: clearing the room advances its cursor.
    `streak_pos` is the momentum position this encounter's XP was quoted at
    (site encounters only) -- recorded on victory so the NEXT one pays more.
    `field` is the fight's opening gap (ranged combat: ROOM_FIELD indoors,
    the engagement's outcome in the wilds) -- persisted with a paused
    fight so the resume stands on the same ground."""
    party, rng = state["party"], state["rng"]
    living = [h for h in party if not h.dead]
    dead_before = [h.name for h in party if h.dead]    # so the post-fight
                                                       # morale pass knows
                                                       # who died in THIS one
    fired: set[str] = set()
    pause = group_combat(living, foes, rng, log, pause_triggers=True,
                         fired=fired, standing_orders=play_orders(False),
                         field=field)
    if pause is not None:
        state["pending"] = {
            "foes": foes, "xp": encounter_xp, "site": site, "room": room,
            "quest": quest, "fired": fired, "round": pause.round,
            "crossings": [(k, h.name) for k, h in pause.crossings],
            "streak_pos": streak_pos,
            "dead_before": dead_before,
            "field": field,
            "align": align,
        }
        print_combat(log)
        print()
        print_pause_menu(state)
        save(state)
        return
    finish_encounter(state, log, foes, encounter_xp, site=site, room=room,
                     quest=quest, streak_pos=streak_pos,
                     dead_before=dead_before, align=align)


def party_level(state: dict) -> int:
    """The party's best living level -- the karma layer's yardstick (heat
    steps scale with it, posses arrive relative to it)."""
    return max((h.level for h in state["party"] if not h.dead), default=1)


def record_karma(state: dict, xp: int, align: str, log: list) -> None:
    """The session shim over karma.record_karma: a QUOTED award in,
    bucketed by the work's alignment (dark accrues, good burns, neutral
    passes through), the meter line appended to the log."""
    if align in ("dark", "good"):
        karma.record_karma(state["karma"], xp, align, log,
                           party_level(state))


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
    n_sites = len(quest["sites"])
    last_site = cur["site"] == n_sites - 1
    banner = "QUEST COMPLETE" if last_site else "SITE CLEARED"
    # A multi-site quest names its position (site 1/2) in the banner so a
    # SITE CLEARED never reads as the whole job done (2026-07-19).
    pos = f" (site {cur['site'] + 1}/{n_sites})" if n_sites > 1 else ""
    clear_xp = site_clear_xp(site["level"], n_rooms)
    award_quest(party, purse, site_gold_for(quest, site),
                clear_xp, log,
                f"{quest['name']} -- {site['name']}{pos}", banner=banner)
    record_karma(state, clear_xp, quest.get("align", "good"), log)
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


def active_delivery(state: dict) -> dict | None:
    """The active quest when it is an OPEN delivery (the cross-land courier
    kind, 2026-07-14), else None."""
    qid = state.get("active_quest")
    world = state.get("world")
    if not qid or not world:
        return None
    q = world["quests"].get(qid)
    if q is not None and q.get("kind") == "delivery" and q["status"] == "open":
        return q
    return None


def deliver_if_arrived(state: dict, log: list[str]) -> bool:
    """The delivery hand-off: fires whenever the active quest is an open
    delivery and the party stands at its destination settlement -- checked
    at travel arrivals and after any fight settles (the guaranteed
    interception may pause, so the pay must be able to land after a resume
    or a retreat too). Idempotent: pays once, flips the quest done. An
    occupied destination cannot pay -- the delivery waits on the war."""
    q = active_delivery(state)
    if q is None:
        return False
    here = local_settlement(state)
    if here is None or here["key"] != q["dest"]:
        return False
    if occupied_here(state) is not None:
        log.append(f"  ({q['name']}: {here['name']} lies under the yoke -- "
                   f"no one here can receive {q['cargo']} or pay for it. "
                   f"The delivery waits on the war.)")
        return False
    award_quest(state["party"], state["purse"], q["gold"], q["xp"], log,
                q["name"], banner="DELIVERY COMPLETE")
    record_karma(state, q["xp"], q.get("align", "good"), log)
    q["status"] = "done"
    q["done_day"] = state["clock"].day
    r = q.get("recipient")
    if r:
        log.append(f"  (hand {q['cargo']} to the recipient -- narrate the "
                   f"scene: {npc_line(r)})")
    if q.get("epilogue"):
        log.append(f"  EPILOGUE (day {state['clock'].day}): {q['epilogue']}")
    return True


def maybe_post_wave(state: dict, log: list | None = None) -> bool:
    """The war's clock (story.py): post the next wave when it is due --
    the previous wave DONE, the party at the wave's level (2/5/8/10), and
    the party IN A SETTLEMENT (2026-07-13, designer call: war news never
    finds them mid-quest in the middle of nowhere -- it waits at the next
    town). Checked at the natural news-reaches-you points: the board,
    arrivals, and settlement nights. Prints (or appends) the messenger
    scene; every call site saves afterward."""
    st = state.get("story")
    living = [h for h in state["party"] if not h.dead]
    if not st or not living or local_settlement(state) is None:
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


# --------------------------------------------------------------------------- #
# Karma & heat (the villain layer, 2026-07-19 -- karma.py, rules.md add-on)
# --------------------------------------------------------------------------- #

def maybe_punish(state: dict) -> bool:
    """Heat's collection call: at heat >= 1, once the cooldown has passed,
    a chance-rolled POSSE finds the party -- checked at travel arrivals,
    settlement nights (tavern/downtime), and camp nights: the law is
    people, and people travel. The posse fights at party level + heat off
    the plain ladder wearing the band's lawful names (the Watch -> bounty
    guild -> crown's huntsmen -> heroes of the realm), led by a generated
    face (the nemesis seed). It pays wild XP like any road fight and ALL
    of it is bad karma -- cutting down the law is itself a crime; that
    ratchet is the design. Returns True when a fight ran (the encounter
    machinery has printed and saved)."""
    k = state.get("karma")
    living = [h for h in state["party"] if not h.dead]
    if not k or not living or state.get("pending"):
        return False
    lvl = party_level(state)
    h = karma.heat(k, lvl)
    if h < 1:
        return False
    day = state["clock"].day
    if day < k.get("last_punish_day", -99) + karma.PUNISH_COOLDOWN_DAYS:
        return False
    rng = state["rng"]
    if rng.random() >= karma.PUNISH_CHANCE:
        return False
    k["last_punish_day"] = day
    posse_level = min(karma.LEVEL_CAP, lvl + h)
    land = state["location"]["land"]
    used = {n["name"] for n in state["world"].get("npcs", [])}
    kinds, skins, leader, label = karma.build_posse(posse_level, land, rng,
                                                    used_names=used)
    k["last_leader"] = f"{leader['name']}, {leader['role']}"
    here = local_settlement(state)
    where = (f"at {here['name']}'s gates" if here is not None
             else "at the party's fire")
    print(f"*** THE RECKONING -- day {day}: word of the party's deeds "
          f"has caught up ({karma.karma_line(k, lvl)}). ***")
    print(f"  {label} find the party {where}, led by {npc_line(leader)}")
    print(f"  (no parley in v1 -- they mean to collect; retreat is the "
          f"peaceful option)")
    log = CombatLog()
    for hero in living:
        start_fight(hero, log)
    log.append(f"=== The reckoning: {label} "
               f"(a level-{posse_level} posse) ===")
    foes = []
    for kind in kinds:
        state["foe_count"] += 1
        foes.append(make_foe(kind, state["foe_count"], rng,
                             display=skins.get(kind)))
    # Biggest last (build_room's order): the leader's face goes on the
    # strongest slot, the conquest-boss doctrine -- a display name over a
    # budget-honest row.
    foes[-1].name = leader["name"]
    for line in roster_lines(foes):
        log.append("  " + line)
    field = 0 if here is not None else WILD_FIELD
    resolve_encounter(state, log, foes, wild_encounter_xp(posse_level),
                      field=field, align="dark")
    return True


def roll_dark_board(state: dict) -> dict | None:
    """The SHADOW board (`board --dark`): rolled lazily, once per
    settlement per day -- the recruits-on-request pattern, so worldgen
    (and every bench) never sees a dark quest. Yesterday's untaken offers
    melt back into the shadows: pruned from world['quests'] unless taken
    (the active quest, or any quest already progressed/done, survives)."""
    here = local_settlement(state)
    if here is None:
        return None
    rec = state.get("dark_board")
    day = state["clock"].day
    if rec and rec["place"] == here["key"] and rec["day"] == day:
        return rec
    world = state["world"]
    if rec:
        for qid in rec["qids"]:
            q = world["quests"].get(qid)
            untouched = (q is not None and q["status"] == "open"
                         and q["next"] == {"site": 0, "room": 0}
                         and state.get("active_quest") != qid)
            if untouched:
                del world["quests"][qid]
    used = {n["name"] for n in world.get("npcs", [])}
    used |= {q["giver"]["name"] for q in world["quests"].values()
             if q.get("giver")}
    qids = []
    for _ in range(karma.DARK_JOBS_PER_DAY):
        q = karma.roll_dark_quest(world, here, party_level(state),
                                  state["rng"], used_names=used)
        qids.append(q["id"])
    rec = {"place": here["key"], "day": day, "qids": qids}
    state["dark_board"] = rec
    return rec


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
                     dead_before: list[str] | None = None,
                     align: str = "neutral") -> None:
    """The melee actually ended: wipe check, awards, companion autolevel,
    loot, the companion morale pass, persist -- and the PC's level-up
    prints the spending menu on the spot (2026-07-13)."""
    party, purse, rng = state["party"], state["purse"], state["rng"]
    pc = party[0] if party else None
    pc_level_before = pc.level if pc else 0
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
        record_karma(state, encounter_xp, align, log)
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
        # Companions manage their own skill points (2026-07-13): any
        # points the awards just banked go on the doctrine now. The PC's
        # stay banked -- spending them is the player's decision.
        for h in party[1:]:
            if not h.dead:
                autospend_points(h, log)
        # Quality steel outlives its bearer (2026-07-13): a companion who
        # died THIS fight leaves their weapon with the party.
        for h in party[1:]:
            if (h.dead and h.name not in (dead_before or [])
                    and h.weapon is not None and h.weapon.quality
                    and not h.weapon_broken):
                log.append(f"  {h.name}'s {h.weapon.name} is taken up from "
                           f"where they fell -- quality steel stays with "
                           f"the party (`give HERO {h.weapon.name}`).")
        # The companion morale pass: blood and fear, whatever the outcome
        # (a game over needs no bookkeeping).
        satisfaction_after_fight(party, dead_before or [], log)
        # A delivery's hand-off can come due here: the guaranteed
        # interception (or any other fight at the destination's gates)
        # settling with the party at the destination IS the arrival.
        deliver_if_arrived(state, log)
        # (War news no longer arrives at fight's end -- it waits for the
        # next settlement scene: board, arrival, tavern, downtime.)
        append_tally(state, log)
    print_combat(log)
    save(state)
    if (not wiped and pc is not None and not pc.dead
            and pc.level > pc_level_before):
        print()
        print(f"*** {pc.name} reached level {pc.level} -- the spending "
              f"menu (show it to the player, dm.md): ***")
        print_levelup_menu([pc])
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
    # the DM adjusts via `quest` if a scene deserves more. `--field N` sets
    # the opening gap for an outdoor scene (default 0: at the door).
    resolve_encounter(state, log, foes, ENCOUNTER_XP,
                      field=max(0, args.field))


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
                      site=site.key, room=args.room, streak_pos=k,
                      field=ROOM_FIELD)


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
    if getattr(args, "dark", False):
        # The SHADOW board (karma & heat): the wrong tavern corner, the
        # back room, the fence's cellar. Rolled on request, once per
        # settlement day; its jobs are leveled AT the party (the fixer
        # offers what the taker can handle -- the OSR straight-board
        # stance is the honest world's).
        here = local_settlement(state)
        if here is None:
            print(f"The shadows do business behind walls -- the party is "
                  f"at {location_line(state)}. Find a settlement first.")
            return
        if occupied_here(state):
            print(occupation_line(state, here))
            return
        rec = roll_dark_board(state)
        save(state)
        mind = party_mind(state)
        print(f"Day {state['clock'].day}. Asking around the wrong corners "
              f"of {here['name']} (dark work: the gold runs half again "
              f"the honest rate, but every XP is BAD KARMA -- heat "
              f"follows, and the law collects):")
        for qid in rec["qids"]:
            q = world["quests"].get(qid)
            if q is None:
                continue
            g = q.get("giver")
            who = f"    ({g['name']}, {g['role']})" if g else ""
            print("  " + quest_line(q, mind) + who)
        print(f"({karma.karma_line(state['karma'], party_level(state))}; "
              f"these offers last today only -- take one like any "
              f"quest: `take QID`)")
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
    # Quest sight: the LOCAL (played) board reads through the party's best
    # MIND -- L~7 is an estimate, not the truth. The explicit-settlement /
    # 'all' call is the DM overview and stays true.
    mind = party_mind(state) if not args.settlement else None
    if mind is not None and mind_precision(mind) > 0:
        print(f"(the party's best MIND is {mind}: quest levels marked ~ "
              f"are read within {mind_precision(mind)} level(s))")
    for line in board_lines(world, key, mind=mind):
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
        # read through the party's MIND like the local board (quest sight);
        # details and `take` still want the party AT the posting settlement.
        land = state["location"]["land"]
        rumors = []
        for s in lands(world).get(land, []):
            if s["key"] == key:
                continue
            for qid in s["quests"]:
                q = world["quests"][qid]
                if q["status"] == "open":
                    rumors.append(f"  [{q['id']}] {level_grade(q, mind)} "
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
    # The player-facing view reads through the party's MIND (quest sight);
    # --dm is the true view for the DM's own planning.
    mind = None if args.dm else party_mind(state)
    for line in quest_detail_lines(quest, mind=mind):
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
    mind = party_mind(state)
    print(f"The party takes the job: {quest_line(quest, mind)}")
    for line in quest_detail_lines(quest, mind=mind)[1:]:
        print(line)
    if quest.get("kind") == "delivery":
        print(f"The road is the job: `travel {quest['dest']}` "
              f"({quest['days']} day(s)) and expect trouble en route -- "
              f"arriving is the turn-in.")
    else:
        print("Fight the next room with `room`. Switching quests later keeps "
              "this one's progress.")
    if quest.get("align") == "dark":
        print("(dark work: every XP it pays is BAD KARMA -- heat rises, "
              "and the law comes collecting. Honest jobs burn bad karma "
              "1:1; `karma` shows the meter.)")


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
    if quest.get("kind") == "delivery":
        print(f"[{qid}] {quest['name']} is a road job -- no rooms to fight. "
              f"`travel {quest['dest']}` to carry it.")
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
                      streak_pos=k, field=ROOM_FIELD,
                      align=quest.get("align", "good"))


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
    n = len(world["quests"]) + 1
    while f"q{n:02d}" in world["quests"]:    # shadow-board pruning can
        n += 1                               # leave id holes
    qid = f"q{n:02d}"
    quest = forge_quest(qid, args.level, args.sites, args.rooms, kinds,
                        args.name, state["rng"],
                        settlement_key=settlement["key"],
                        align="dark" if args.dark else "good")
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


def party_preferred_field(party: list) -> int:
    """The gap the PARTY opens at when it picks the engagement (a won
    sighting, the hunt): its longest ready reach -- a shooter's range, a
    caster's bolts -- or 0 for an all-steel party that closes to contact
    quietly (today's fight)."""
    return max((h.threat_reach for h in party if h.alive), default=0)


def fight_wild_encounter(state: dict, kinds: list[str], level: int,
                         banner: str, field: int = WILD_FIELD) -> None:
    """Run a wilderness encounter through the same machinery as any other
    (it can pause; retreat scatters it -- the road is not a room). `field`
    is the engagement's opening gap (who noticed whom decides it)."""
    party = state["party"]
    log = CombatLog()
    for h in [h for h in party if not h.dead]:
        start_fight(h, log)
    log.append(f"=== {banner} (a level-{level} encounter) ===")
    foes = _spawn_wild_foes(state, kinds)
    for line in roster_lines(foes):
        log.append("  " + line)
    resolve_encounter(state, log, foes, wild_encounter_xp(level),
                      field=field)


def wild_event(state: dict, chance: float, banner: str) -> bool:
    """Roll the wilds once: nothing, a FIGHT (returns True; the encounter
    machinery has taken over and saved), or a SIGHTING. Foes well above
    the party keep the old contract (usually spotted at range unless they
    ambush first -- deadly-but-avoidable is a promise, not a roll of the
    conspicuousness dice). ORDINARY trouble runs the notice contest
    (quests.notice_contest, 2026-07-16): party MIND vs foe senses over
    each side's conspicuousness -- seen-first alone = the sighting choice;
    seeing the party first alone = an AMBUSH at the foes' preferred range;
    both or neither = met square across the open field (WILD_FIELD)."""
    rng = state["rng"]
    if rng.random() >= chance:
        return False
    level = roll_wild_level(rng)
    land = state["location"]["land"]
    kinds = build_wild_encounter(level, land, rng)
    party_level = max(h.level for h in state["party"] if not h.dead)
    towering = level >= party_level + SPOTTED_MARGIN
    if towering:
        spotted, ambushed = rng.random() >= AMBUSH_CHANCE, False
    else:
        party_sees, foes_see = notice_contest(state["party"], kinds, rng)
        spotted = party_sees and not foes_see
        ambushed = foes_see and not party_sees
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
        field = foes_preferred_field(kinds)
    elif ambushed:
        field = foes_preferred_field(kinds)
        how = ("already shooting" if field else "on the party blade-first")
        print(f"  AMBUSH -- they saw the party first, {how}.")
    else:
        field = WILD_FIELD      # met square: both sides cross the open
    fight_wild_encounter(state, kinds, level, banner, field=field)
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
        _long_rest(state["party"], state["clock"], log, rng=state["rng"])
        storyteller_tale(state["party"], state["rng"], log)
        companions_brew(state, log)
        night_upkeep(state, log)
    reset_streak(state)
    print("\n".join(log))
    state["location"] = target
    if target.get("kind") != "wild":
        visited = state.setdefault("visited", [])
        if target["place"] not in visited:
            visited.append(target["place"])  # known ground for teleport
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
    dq = active_delivery(state)
    if (dq is not None and target["place"] == dq["dest"]
            and not dq.get("intercepted")):
        # The delivery's guaranteed encounter: the leg that reaches the
        # destination is watched. Rolled off the road's own table like any
        # travel event (spotted/ambush valves included), just at chance 1.
        dq["intercepted"] = True
        print(f"  Word of {dq['cargo']} travelled faster than the party -- "
              f"the road is watched.")
        if wild_event(state, 1.0,
                      f"Intercepted on the road to {target['name']}"):
            return      # the fight machinery saved; if it paused, the
                        # hand-off lands when the fight settles
                        # (deliver_if_arrived in finish_encounter/retreat)
    elif wild_event(state, chance, f"On the road to {target['name']}"):
        return
    if maybe_punish(state):     # the law meets the party at the walls
        return                  # (karma & heat; the machinery saved)
    log = []
    if deliver_if_arrived(state, log):
        print("\n".join(log))
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
    _long_rest(party, clock, log, rng=rng)
    storyteller_tale(party, rng, log)
    companions_brew(state, log)
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
        # (any level, the higher the rarer) finds the party first. Met at
        # the AMBUSHER'S preferred range -- never the sighting choice.
        level = roll_wild_level(rng)
        kinds = build_wild_encounter(level, land, rng)
        print(f"  The hunter is the hunted -- something found the party "
              f"first. AMBUSH!")
        fight_wild_encounter(state, kinds, level,
                             f"Ambushed on the hunt in the {land} wilds",
                             field=foes_preferred_field(kinds))
        return
    party_level = max(h.level for h in party if not h.dead)
    level = rng.randint(max(1, party_level - HUNT_LEVEL_REACH),
                        max(1, party_level))
    kinds = build_wild_encounter(level, land, rng)
    # The party stalks and springs this fight: it opens at ITS preferred
    # range (the archer's whole reach, or a quiet close to contact).
    fight_wild_encounter(state, kinds, level,
                         f"The hunt in the {land} wilds",
                         field=party_preferred_field(party))


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
    # Engaging a sighting is the party's spring: it opens at ITS preferred
    # range (shooters at their reach, an all-steel party at contact).
    fight_wild_encounter(state, sighting["kinds"], sighting["level"],
                         "The party picks this fight",
                         field=party_preferred_field(state["party"]))


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
                         ("warbreath", "war-breath"),
                         ("vanish", "vanish")):
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
            if action == "berserk":
                if "berserk" not in hero.abilities:
                    print(f"{hero.name} has not learned Berserk "
                          f"(1 point at the levelup menu).")
                    return
                if hero.hp <= BERSERK_HP_COST:
                    print(f"{hero.name} is too torn up to Berserk "
                          f"(HP {hero.hp}, must survive the "
                          f"{BERSERK_HP_COST}).")
                    return
            if action == "war-breath":
                if "war_breath" not in hero.abilities:
                    print(f"{hero.name} has not learned War-Breath "
                          f"(2 points at the levelup menu).")
                    return
                if hero.cur_power < WAR_BREATH_POWER_COST:
                    print(f"{hero.name} lacks the Power for War-Breath "
                          f"({hero.cur_power}/{WAR_BREATH_POWER_COST}).")
                    return
            if action == "vanish":
                if hero.spell_rank("invisibility") < 2:
                    print(f"{hero.name} doesn't know invisibility at rank 2 "
                          f"(the vanish).")
                    return
                if hero.cur_power < VANISH_POWER_COST:
                    print(f"{hero.name} lacks the Power to vanish "
                          f"({hero.cur_power}/{VANISH_POWER_COST}).")
                    return
            actions[hero] = action

    log = CombatLog()
    pause = group_combat(living, pending["foes"], rng, log,
                         pause_triggers=True, fired=pending["fired"],
                         first_round=pending["round"] + 1,
                         actions=actions or None,
                         standing_orders=play_orders(True),
                         field=pending.get("field", 0))
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
                     dead_before=pending.get("dead_before"),
                     align=pending.get("align", "neutral"))


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

    escaped = False
    if args.blink:
        # Teleport rank 2, BLINK OUT: the whole party steps through -- no
        # parting blows, no chase. A fizzled door falls back to the honest
        # retreat below, blows and all.
        wizard = find_hero(party, args.blink)
        if wizard is None:
            return
        if not wizard.alive:
            print(f"{wizard.name} is not on their feet -- no one to tear "
                  f"the door open.")
            return
        escaped = blink_escape(living, pending["foes"], wizard, rng, log)
    smoker = None
    if not escaped and args.smoke:
        # A smoke vial (session C): no parting blows land, but the chase
        # still rolls -- the haze buys the exit, not the legs.
        smoker = find_hero(party, args.smoke)
        if smoker is None:
            return
        if not smoker.alive:
            print(f"{smoker.name} is not on their feet to throw the vial.")
            return
        if smoker.items.get("smoke", 0) <= 0:
            print(f"{smoker.name} has no smoke vial.")
            return
    if not escaped:
        escaped = attempt_retreat(living, pending["foes"], rng, log,
                                  field=pending.get("field", 0), smoke=smoker)
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
            # Fleeing the delivery's interception doesn't un-deliver: if the
            # party stands at the destination, the hand-off happens.
            deliver_if_arrived(state, log)
            append_tally(state, log)
        print_combat(log)
        save(state)
        report_game_over(party, wiped)
        return

    # Run down: the fight resumes at once, the parting damage already taken.
    pause = group_combat(living, pending["foes"], rng, log,
                         pause_triggers=True, fired=pending["fired"],
                         first_round=pending["round"] + 1,
                         standing_orders=play_orders(True),
                         field=pending.get("field", 0))
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
                     dead_before=pending.get("dead_before"),
                     align=pending.get("align", "neutral"))


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
        _long_rest(party, clock, log, rng=state["rng"])
        storyteller_tale(party, state["rng"], log)
        companions_brew(state, log)
        in_wilds = (state.get("world")
                    and state["location"]["kind"] != "settlement")
        quiet = False
        if in_wilds:
            # Survivalist (the ability): a made MIND check turns the rough
            # camp into a tavern night and halves the visitor chance.
            quiet = survivalist_camp(party, state["rng"], log)
        night_upkeep(state, log)
        print("\n".join(log))
        if in_wilds:
            # A night in the wilds is not a night behind walls (2026-07-10):
            # the fire can draw a visitor. Rolled after the night's recovery;
            # a fight cuts the stay short -- what remains of it is the
            # player's call again afterward.
            chance = CAMP_ENCOUNTER_CHANCE / 2 if quiet else CAMP_ENCOUNTER_CHANCE
            if wild_event(state, chance,
                          f"In the night at {state['location']['name']}"):
                return
        if maybe_punish(state):     # posses track a camp too (karma)
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
    if not _tavern_rest(state["party"], state["clock"], state["purse"], log,
                        rng=state["rng"]):
        print("\n".join(log))
        return
    storyteller_tale(state["party"], state["rng"], log)
    companions_brew(state, log)
    night_upkeep(state, log)
    streak = state.get("streak") or {"site": None, "count": 0}
    if streak["count"]:
        log.append(f"    (the night breaks the momentum at {streak['site']} "
                   f"-- the next encounter pays base XP again)")
    reset_streak(state)
    clear_sighting(state)
    process_departures(state, log)
    # Candidates are no longer popped unasked (2026-07-13): when the
    # player wants to hire, `recruit` gathers the day's faces.
    maybe_post_wave(state, log)     # tavern talk is where war news lands
    print("\n".join(log))
    if maybe_punish(state):     # the Watch knows where the party sleeps
        return
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
    _long_rest(party, clock, log, rng=state["rng"])
    storyteller_tale(party, state["rng"], log)
    companions_brew(state, log)
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
    if maybe_punish(state):     # an idle day is easy to find the party on
        return
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
    pc = party[0]
    pc_level_before = pc.level
    log: list[str] = []
    award_quest(party, purse, args.gold, args.xp, log, args.name)
    if args.dark:
        record_karma(state, args.xp, "dark", log)
    elif args.good:
        record_karma(state, args.xp, "good", log)
    for h in party[1:]:
        if not h.dead:
            autospend_points(h, log)
    print("\n".join(log))
    save(state)
    if not pc.dead and pc.level > pc_level_before:
        print()
        print(f"*** {pc.name} reached level {pc.level} -- the spending "
              f"menu (show it to the player, dm.md): ***")
        print_levelup_menu([pc])


def cmd_karma(args: argparse.Namespace) -> None:
    """The karma & heat meter, and the DM's off-script sin/penance entry
    (quest work buckets itself -- this is for improvised wickedness or
    roleplayed virtue: the kicked puppy, the fenced heirloom, the coin
    pressed into the beggar's hand)."""
    state = load()
    k = state["karma"]
    lvl = party_level(state)
    if args.kind:
        if args.amount <= 0:
            print("Usage: karma bad N [reason...] / karma good N "
                  "[reason...] -- N must be positive.")
            return
        log: list[str] = []
        align = "dark" if args.kind == "bad" else "good"
        karma.record_karma(k, args.amount, align, log, lvl)
        why = " ".join(args.why)
        word = "Sin" if align == "dark" else "Penance"
        print(f"{word} recorded" + (f": {why}" if why else "") + ".")
        for line in log:
            print(line)
        save(state)
    print(f"Karma: {karma.karma_line(k, lvl)}")
    print(f"  lifetime: {k['bad_total']} wickedness, {k['good_total']} "
          f"penance.")
    if k.get("last_leader"):
        print(f"  Last posse led by {k['last_leader']} (day "
              f"{k['last_punish_day']}).")
    h = karma.heat(k, lvl)
    if h >= 1:
        print(f"  Posses arrive at party level +{h} -- at arrivals and "
              f"nights, at most one per {karma.PUNISH_COOLDOWN_DAYS} "
              f"days. Honest quests burn bad karma 1:1.")


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
    elif thing in AMMO_LOTS:
        # Ammo by the lot (ranged combat): arrows/bolts by the sheaf,
        # shells and knives by the pair, up to the carry cap.
        _buy_ammo(hero, purse, thing, log)
    elif thing in WEAPONS:
        if thing == "revolver":
            # The magic gun is dwarf craft and dwarf commerce: sold only
            # in dwarven settlements (the L10+ gold sink lives there).
            here = local_settlement(state)
            if here is None or here["race"] != "dwarf":
                print(f"Revolvers are sold only in dwarven settlements -- "
                      f"the party is at {location_line(state)}.")
                return
        _buy_weapon(hero, purse, thing, log)
    elif thing.startswith("book"):
        # `buy HERO book SPELL` -- the spellbook, the gold gate on a
        # wizard's breadth (Magic & Mind). Sold where scholarship lives:
        # capitals only, like meds.
        spell_name = thing[4:].strip()
        if spell_name not in SPELLS:
            print(f"No book teaches {spell_name!r}. Spells: "
                  f"{', '.join(sorted(SPELLS))}.")
            return
        here = local_settlement(state)
        if here is None or here["kind"] != "capital":
            print(f"Spellbooks are sold only in a capital -- the party is "
                  f"at {location_line(state)}.")
            return
        _buy_spellbook(hero, purse, spell_name, log)
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
              f"Weapons: {', '.join(sorted(WEAPONS))}. Ammo: "
              f"{', '.join(sorted(AMMO_LOTS))}. Also: meds, "
              f"book SPELL.")
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
    if args.as_name:
        # The DM's custom-weapon hook (2026-07-13): a display name over an
        # honest catalog profile -- same doctrine as foe reskins, the name
        # is fiction and the stats never change with the costume. The
        # instance serializes whole in the save; note proficiency follows
        # the NAME, so reskin looted flavor, not a drilled blade.
        weapon = dataclasses.replace(weapon, name=args.as_name)
        log.append(f"  ({weapon.name}: a reskinned {name} -- catalog stats)")
    _equip_weapon(hero, weapon, log)
    grant_starter_ammo(hero, log)   # a DM-granted bow comes with a quiver
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
    what = " ".join(args.what).lower()
    if what == "combat":
        _train_combat_once(hero, log)
    elif what == "weapon":
        _train_proficiency(hero, log)
    elif what == "alchemy":
        _train_alchemy(hero, log)
    elif what in POOL_KINDS:
        # The pool buys (the point economy): +1 max HP/STA/Power, 1 point.
        _buy_pool(hero, what, log)
    elif what == "magic":
        # The shorthand: drill the wizard's own school spell.
        if hero.school:
            _train_spell(hero, hero.school, log)
        else:
            log.append(f"    {hero.name} has no school of magic to drill.")
    elif what in SPELLS:
        _train_spell(hero, what, log)
    elif what.startswith("move"):
        # A warrior move (session B): `train HERO move NAME`.
        name = what[len("move"):].strip().replace("-", " ").replace(" ", "_")
        if not name:
            print(f"Which move? Options: {', '.join(sorted(MOVES))}.")
            return
        _learn_move(hero, name, log)
    else:
        print(f"Unknown skill: {what!r}. Options: combat, weapon, alchemy, "
              f"{'|'.join(POOL_KINDS)}, magic, a spell name "
              f"({', '.join(sorted(SPELLS))}), or move NAME "
              f"({', '.join(sorted(MOVES))}).")
        return
    print("\n".join(log))
    save(state)


def cmd_prices(args: argparse.Namespace) -> None:
    """The DM's price sheet (2026-07-19), read from the live constants --
    'what does a katana cost' should never mean searching the code (dm.md
    points here). A pure readout: no save touched, callable any time."""
    print("-- SHOP PRICES (gold) --")
    print(f"potion (healing or stamina): {POTION_PRICE}g")
    print(f"spellbook (capitals only): {SPELLBOOK_PRICE}g")
    print(f"meds dose (capitals only, one per {MEDS_INTERVAL_DAYS} days): "
          f"{MEDS_PRICE}g")
    print(f"tavern night: {TAVERN_COST_PER_HERO}g a head")
    print("ammo, by the lot (to the carry cap):")
    for kind, (lot, price) in AMMO_LOTS.items():
        print(f"  {kind}: {lot} for {price}g (cap {AMMO_CAPS[kind]})")
    print("  sling stones: free (the ground is full of them)")
    common = [(n, w) for n, w in WEAPONS.items()
              if w.tier == "plain" and not w.quality]
    quality = [(n, w) for n, w in WEAPONS.items()
               if w.tier == "plain" and w.quality]
    print("common weapons:")
    for name, w in sorted(common, key=lambda kv: (kv[1].value, kv[0])):
        print(f"  {name}: {w.value}g")
    print("quality weapons:")
    for name, w in sorted(quality, key=lambda kv: (kv[1].value, kv[0])):
        print(f"  {name}: {w.value}g")
    print("(the revolver sells in DWARVEN settlements only; masterwork and "
          "legendary are never for sale; brewed potions can't be sold)")


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


def cmd_brew(args: argparse.Namespace) -> None:
    """The alchemist's long-rest brew (session C): pick a recipe their rank
    has unlocked and roll 2d6 + MIND + rank vs DC 9. Once per hero per day
    (the brew is the night's work); the batch is fenced by the freshness
    cap (rank + 2 carried). Brewed potions are unsellable."""
    state = load()
    if not require_no_pending(state):
        return
    party, rng, clock = state["party"], state["rng"], state["clock"]
    log: list[str] = []
    hero = find_hero(party, args.hero)
    if hero is None:
        return
    if hero.alchemy <= 0:
        print(f"{hero.name} knows no alchemy (train {hero.name.split()[0]} "
              f"alchemy).")
        return
    recipe = args.recipe.lower()
    if recipe not in alchemy_recipes(hero.alchemy):
        print(f"{hero.name} can brew: "
              f"{', '.join(alchemy_recipes(hero.alchemy))} "
              f"(rank {hero.alchemy}).")
        return
    if hero.last_brew_day == clock.day:
        print(f"{hero.name} has already brewed today -- the still needs the "
              f"night. (Brewing is one batch per long rest.)")
        return
    _brew(hero, recipe, rng, log)       # a curdled batch still spends the day
    hero.last_brew_day = clock.day
    print("\n".join(log))
    save(state)


def cmd_heal(args: argparse.Namespace) -> None:
    """The healing SPELL, between fights (the old Heal ability became
    magic -- rules.md): cast at the healer's trained rank through the
    casting check."""
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
    _cast_healing(healer, target, rng, log)
    print("\n".join(log))
    save(state)


def cmd_learn(args: argparse.Namespace) -> None:
    """Buy a catalog ability with banked skill points (the levelling
    framework's single buys -- rpg.ABILITIES; the levelup menu lists
    costs). Accepts spaces or dashes for the underscored keys."""
    state = load()
    if not require_no_pending(state):
        return
    party = state["party"]
    log: list[str] = []
    hero = find_hero(party, args.hero)
    if hero is None:
        return
    name = " ".join(args.ability).lower().replace("-", " ").replace(" ", "_")
    _learn_ability(hero, name, log)
    print("\n".join(log))
    save(state)


def _cast_scry(state: dict, hero, log: list[str]) -> None:
    """Scry, between fights: sight beyond walls. Rank 1 reads the ACTIVE
    quest's next room; rank 2 the whole current site; rank 3 the whole
    quest (its TRUE level included -- the far-seeing outranks quest sight)
    plus whatever DM-adjudicated divination the scene wants (dm.md)."""
    rng = state["rng"]
    rank = hero.spell_rank("scry")
    if rank <= 0:
        print(f"{hero.name} has not learned scry (a spellbook teaches it).")
        return
    cost = SCRY_POWER_COST[rank]
    if hero.cur_power < cost:
        print(f"{hero.name} lacks the Power to scry "
              f"({hero.cur_power}/{cost}).")
        return
    qid = state.get("active_quest")
    world = state.get("world")
    quest = world["quests"].get(qid) if (qid and world) else None
    if quest is None or quest["status"] != "open" or not quest.get("sites"):
        print("Nothing taken to scry at -- an active site quest gives the "
              "spell a target. (Freeform divination is the DM's to "
              "adjudicate over a rank-3 casting.)")
        return
    hero.cur_power -= cost
    result = casting_check(hero, "scry", rank, rng, log)
    seen_rank = rank - 1 if result == "downgrade" else rank
    if result == "misfire":
        # rpg's helper handles the backlash bookkeeping consistently.
        from rpg import _misfire
        _misfire(hero, "scry", log)
        return
    if result == "fizzle" or seen_rank <= 0:
        log.append(f"    {hero.name} stares into the beyond -- and sees "
                   f"only fog ({cost} Power wasted).")
        return
    if result == "crit":
        hero.cur_power += cost
    log.append(f"    {hero.name} scries (-{0 if result == 'crit' else cost} "
               f"Power -> {hero.cur_power}):")
    cur = quest["next"]
    site = quest["sites"][cur["site"]]
    if seen_rank >= 3:
        log.append(f"    THE FAR-SEEING -- [{quest['id']}] {quest['name']} "
                   f"is truly level {quest['level']}:")
    sites = (quest["sites"] if seen_rank >= 3
             else [site])
    for i, s in enumerate(sites):
        s_i = i if seen_rank >= 3 else cur["site"]
        rooms = s["rooms"]
        for j, (rname, kinds) in enumerate(rooms):
            if seen_rank == 1 and not (s_i == cur["site"]
                                       and j == cur["room"]):
                continue
            if seen_rank == 2 and j < cur["room"] and s_i == cur["site"]:
                continue
            log.append(f"      {s['name']} room {j + 1}: {rname} -- "
                       f"{roster_kinds_line(kinds, quest['skins'])}")
    if seen_rank >= 3:
        log.append("      (rank 3 also carries DM-adjudicated divination -- "
                   "ask the question in the scene, dm.md)")


def _cast_teleport(state: dict, hero, want: str, log: list[str]) -> None:
    """Teleport rank 3, TRAVEL: step to any settlement the party has
    VISITED -- no days pass, no road, no camp, no interception. The Power
    pool is the leash: TELEPORT_TRAVEL_COST_PER_DAY per travel day the road
    would have taken."""
    rng, world = state["rng"], state["world"]
    if hero.spell_rank("teleport") < 3:
        print(f"{hero.name}'s teleport art can't carry the party across "
              f"the world (rank 3 needed).")
        return
    visited = state.get("visited", [])
    target = None
    for s in world["settlements"]:
        if want in s["key"]:
            target = s
            break
    if target is None:
        print(f"No settlement matches {want!r}. Teleport reaches "
              f"settlements only (the wilds shift too much to fix).")
        return
    if target["key"] not in visited:
        print(f"The party has never stood in {target['name']} -- teleport "
              f"reaches only KNOWN ground (travel there once first).")
        return
    if target["key"] == state["location"]["place"]:
        print(f"The party is already at {target['name']}.")
        return
    days = (TRAVEL_DAYS_IN_LAND
            if target["race"] == state["location"]["land"]
            else TRAVEL_DAYS_CROSS)
    cost = TELEPORT_TRAVEL_COST_PER_DAY * days
    if hero.cur_power < cost:
        print(f"{hero.name} lacks the Power for that distance "
              f"({hero.cur_power}/{cost} -- {days} road day(s) at "
              f"{TELEPORT_TRAVEL_COST_PER_DAY}/day).")
        return
    hero.cur_power -= cost
    result = casting_check(hero, "teleport", 3, rng, log)
    if result == "misfire":
        from rpg import _misfire
        _misfire(hero, "teleport", log)
        print("\n".join(log))
        return
    if result == "fizzle":
        log.append(f"    {hero.name} folds the map -- and it springs back "
                   f"flat ({cost} Power wasted). The party goes nowhere.")
        print("\n".join(log))
        return
    if result == "crit":
        hero.cur_power += cost
    clear_sighting(state, quiet=True)
    state["location"] = _settlement_location(target)
    log.append(f"    *** {hero.name} folds the world -- one step, and the "
               f"party stands in {target['name']} "
               f"(-{0 if result == 'crit' else cost} Power -> "
               f"{hero.cur_power}). No road, no nights, no ambush. ***")
    print("\n".join(log))
    log2: list[str] = []
    process_departures(state, log2)
    if log2:
        print("\n".join(log2))
    here = occupied_here(state)
    if here is not None:
        print(occupation_line(state, here))
    maybe_post_wave(state)
    log3: list[str] = []
    if deliver_if_arrived(state, log3):
        print("\n".join(log3))


def cmd_cast(args: argparse.Namespace) -> None:
    """The between-fights utility casts (combat spells cast themselves in
    the melee -- the autobattler rule): `cast HERO scry`, `cast HERO
    teleport DEST`. Rank-3 roleplay uses (ghost-walk, far-seeing) are the
    DM's to adjudicate in the scene (dm.md); this command covers the
    engine-backed ones."""
    state = load()
    if not require_no_pending(state):
        return
    party = state["party"]
    log: list[str] = []
    hero = find_hero(party, args.hero)
    if hero is None:
        return
    spell = args.spell.lower()
    if spell == "scry":
        _cast_scry(state, hero, log)
        if log:
            print("\n".join(log))
    elif spell == "teleport":
        if not args.dest:
            print("cast HERO teleport DEST -- name a visited settlement.")
            return
        _cast_teleport(state, hero, " ".join(args.dest).lower(), log)
    else:
        print(f"Between fights only scry and teleport are cast by command "
              f"-- combat spells fire on their own in the melee. "
              f"({spell!r} given.)")
        return
    save(state)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser(
        "new",
        help="start a fresh game (overwrites save): rolls the world, "
             "GENERATES the player character (male; CHA always holds at "
             "least one companion; no family quirks) with his long-time "
             "companion at his side, and prints the OPENING HOOK -- the "
             "most level-appropriate local job to frame the first scene "
             "on. No character pick, no tavern opening (2026-07-13).")
    p.add_argument("--seed", type=int, default=None)
    p.set_defaults(func=cmd_new)

    p = sub.add_parser(
        "recruit",
        help="gather and show hiring candidates at this settlement -- "
             "rolled ON REQUEST (once per settlement per day), leveled to "
             "the PC +-1; a quarter are bonded pairs (one option, two "
             "heads). Full sheets: transparency over realism, like the "
             "board's straight levels. Only when the player wants to "
             "hire -- the tavern never pops candidates unasked.")
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
        help="the skill-point spending menu (prints automatically on the "
             "PC's level-up; this is the manual re-read). Only the PC's "
             "points are a decision -- companions autolevel.")
    p.set_defaults(func=cmd_levelup)

    p = sub.add_parser(
        "barrow",
        help="DEV/TEST ONLY (2026-07-13: the set sites are calibration "
             "content, not part of a played campaign -- the board's "
             "generated quests are the game). Resolve one skeleton-barrow "
             "room (sites.BARROW_ROOMS).")
    p.add_argument("room", type=int,
                   choices=range(1, len(SITES["barrow"].rooms) + 1))
    p.set_defaults(func=cmd_site, site="barrow")

    p = sub.add_parser(
        "hideout",
        help="DEV/TEST ONLY (2026-07-13: the set sites are calibration "
             "content, not part of a played campaign -- the board's "
             "generated quests are the game). Resolve one bandit-hideout "
             "room (sites.HIDEOUT_ROOMS).")
    p.add_argument("room", type=int,
                   choices=range(1, len(SITES["hideout"].rooms) + 1))
    p.set_defaults(func=cmd_site, site="hideout")

    p = sub.add_parser(
        "fight",
        help="OFF-SCRIPT encounter: spawn N foes (improvised scenes like road "
             "ambushes only -- board quests are set encounters, use `room`). "
             "Pays the base 15 XP regardless of foe; award "
             "extra via `award` if the scene deserves it.")
    p.add_argument("n", type=int, help="how many foes to spawn for this encounter")
    p.add_argument("--type", default="skeleton", choices=list(FIGHT_TYPES),
                   help="a catalog foe kind, or 'bandit' for a random "
                        "living foe")
    p.add_argument("--field", type=int, default=0,
                   help="opening gap for an open-ground scene (0 = at the "
                        "door, the default; the wilds use 3)")
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
    p.add_argument("--vanish", action="append", metavar="HERO",
                   help=f"invisibility rank 2: fade from the melee "
                        f"({VANISH_POWER_COST} Power; untargetable, the "
                        f"next strike lands as an ambush)")
    p.set_defaults(func=cmd_resume)

    p = sub.add_parser(
        "retreat",
        help="break away from a PAUSED fight: parting blows from foes fit "
             "to swing, then ONE group chase roll. A fled site room keeps "
             "its survivors; re-run the room to face them again. "
             "--blink HERO (teleport rank 2) tears a door instead: no "
             "parting blows, no chase; a fizzled casting falls back to "
             "the honest retreat. --smoke HERO smashes a smoke vial: no "
             "parting blows, but the chase still rolls.")
    p.add_argument("--blink", metavar="HERO", default=None)
    p.add_argument("--smoke", metavar="HERO", default=None)
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
             f"night's rest. Also +1 companion satisfaction. Resets "
             f"the momentum streak like any night. (Hiring candidates "
             f"are `recruit`'s business, on request -- the tavern never "
             f"pops them unasked.)")
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
             "here. `board all` / `board NAME` is the wider DM overview. "
             "`board --dark` asks the WRONG corners instead: the shadow "
             "board (karma & heat) -- 2-3 dark jobs leveled at the "
             "party, rolled fresh per settlement day; a gold premium, "
             "but every XP is BAD KARMA.")
    p.add_argument("settlement", nargs="?", default=None)
    p.add_argument("--dark", action="store_true",
                   help="the shadow board: today's dark jobs here")
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
             f"spotted at range first, but can ambush, and ordinary "
             f"trouble runs the NOTICE CONTEST: party MIND vs their "
             f"senses, over each side's conspicuousness -- spotted, "
             f"ambushed, or met square on the open field)")
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
             "each room (by skinned display name). Levels read through the "
             "party's best MIND (quest sight: L~7 is an estimate); --dm "
             "prints the true levels for the DM's own planning.")
    p.add_argument("quest", help="quest id (q07, or just 7)")
    p.add_argument("--dm", action="store_true",
                   help="true levels (DM view), no quest-sight blur")
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
    p.add_argument("--dark", action="store_true",
                   help="forge a SHADOW job (karma & heat): bad-karma "
                        "XP, the dark gold premium")
    p.set_defaults(func=cmd_forge)

    p = sub.add_parser(
        "award",
        help="off-script bonus: award gold + an XP lump by hand (board "
             "quests pay themselves -- this is for improvised scenes). "
             "--dark buckets the XP as BAD KARMA, --good as penance "
             "(karma & heat); plain awards touch neither.")
    p.add_argument("gold", type=int)
    p.add_argument("xp", type=int)
    p.add_argument("name")
    p.add_argument("--dark", action="store_true",
                   help="the scene was wicked: its XP is bad karma")
    p.add_argument("--good", action="store_true",
                   help="the scene was virtuous: its XP burns bad karma")
    p.set_defaults(func=cmd_award)

    p = sub.add_parser(
        "karma",
        help="the karma & heat meter (the villain layer): current bad "
             "karma, heat, lifetime ledgers, the last posse's leader. "
             "`karma bad N [reason]` / `karma good N [reason]` record an "
             "off-script sin or penance by hand -- quest work buckets "
             "itself; this is for improvised wickedness (the kicked "
             "puppy) or roleplayed virtue. Guideline sizes: petty ~15, "
             "serious ~50, an outrage ~100+ (one heat step is 100 x "
             "party level).")
    p.add_argument("kind", nargs="?", choices=("bad", "good"), default=None)
    p.add_argument("amount", nargs="?", type=int, default=0)
    p.add_argument("why", nargs="*", default=[])
    p.set_defaults(func=cmd_karma)

    p = sub.add_parser(
        "buy",
        help="spend gold on a potion, a weapon, or (in a capital) a dose "
             "of meds or a SPELLBOOK -- `buy HERO book SPELL`, "
             f"{SPELLBOOK_PRICE}g, teaches a wizard a new spell at rank 1 "
             "-- for one hero (weapons are equipped on the spot; plain "
             "tier only -- masterwork/legendary are never shopped). Note "
             f"the kit restocks itself: every long rest tops each hero "
             f"back up to {KIT_HEALING} healing + {KIT_STAMINA} stamina "
             f"free -- buying is for stocking ABOVE that line.")
    p.add_argument("hero")
    p.add_argument("thing", nargs="+",
                   help="a potion kind, a weapon name (e.g. rapier, "
                        "wooden staff), 'meds', or 'book SPELL'")
    p.set_defaults(func=cmd_buy)

    p = sub.add_parser(
        "prices",
        help="the DM's price sheet, read from the live constants: potions, "
             "spellbooks, meds, the tavern, ammo lots, and every shoppable "
             "weapon -- answer 'what does X cost' from this readout, never "
             "by searching the code")
    p.set_defaults(func=cmd_prices)

    p = sub.add_parser(
        "give",
        help="DM-granted loot: a hero wields a weapon for free (quest "
             "rewards, a blade looted off a bandit, ...). `--as NAME` "
             "reskins it for the fiction (a 'shock prod' over the club "
             "row): the display name changes, the catalog stats never do. "
             "Proficiency follows the name -- reskin looted flavor, not "
             "a drilled blade.")
    p.add_argument("hero")
    p.add_argument("weapon", nargs="+", help="weapon name (e.g. wooden staff)")
    p.add_argument("--as", dest="as_name", default=None, metavar="NAME",
                   help="display name over the catalog profile")
    p.set_defaults(func=cmd_give)

    p = sub.add_parser(
        "train",
        help="spend banked skill points: 'combat' = +1 to all pressure "
             "rolls per rank (rank n costs 2n, cap 5); 'weapon' = "
             "proficiency with the WIELDED weapon, +1 attack pressure & "
             "+1 severity per rank (rank n costs n, cap 3); "
             "'hp'/'sta'/'power' = +1 to that maximum (1 point each, "
             "+10 per pool a career); a SPELL NAME = one rank of a KNOWN "
             "spell (rank n costs n, cap 3 -- anyone can deepen a spell "
             "they know; books stay wizard-only); 'magic' = shorthand "
             "for the wizard's own school spell; 'move NAME' = a warrior "
             "move (session B -- the engine fires it as a rider on the "
             "exchange; 1 point, iaido/finisher 2; repertoire capped at "
             "combat training + 1, gated by the wielded weapon). See "
             "`levelup` for the whole menu (abilities are `learn`). The "
             "PC's points are the player's choice (companions autolevel "
             "on the doctrine).")
    p.add_argument("hero")
    p.add_argument("what", nargs="+",
                   help="combat | weapon | alchemy | hp | sta | power | "
                        "magic | a spell name (e.g. 'stop time') | move NAME")
    p.set_defaults(func=cmd_train)

    p = sub.add_parser(
        "learn",
        help="buy a catalog ability with banked skill points (single "
             "buys, no class gates -- Bulwark 3, First Blood 2, "
             "War-Breath 2, Berserk 1, Rage 2, Field Medic 3, "
             "Storyteller 2, Survivalist 2, Arrow-Parry 2 (+3 rank 2), "
             "Point-Blank Mastery 3, Rapid Reload 3; `levelup` lists "
             "them with blurbs)")
    p.add_argument("hero")
    p.add_argument("ability", nargs="+",
                   help="ability name (e.g. war breath, rage, "
                        "arrow parry 2)")
    p.set_defaults(func=cmd_learn)

    p = sub.add_parser(
        "use",
        help="drink a carried potion for one hero, between fights (instant: "
             "healing/stamina restore HP/STA -- drunk AT max they OVERCHARGE "
             "+2 above max, spent-only; strength/dexterity give +1 STR/DEX "
             "until the next long rest)")
    p.add_argument("hero")
    p.add_argument("kind", choices=list(DRINKABLE_KINDS))
    p.set_defaults(func=cmd_use)

    p = sub.add_parser(
        "brew",
        help="an alchemist brews a batch at camp (once per long rest): "
             "2d6 + MIND + rank vs DC 9 -- a make yields the batch, a beat "
             "by 7 doubles it, a miss curdles. Recipes by rank: healing, "
             "stamina (r1); strength (r2); firebomb (r3); dexterity, smoke "
             "(r4). Brewed stock is capped at rank+2 and can't be sold.")
    p.add_argument("hero")
    p.add_argument("recipe", help="healing|stamina|strength|firebomb|"
                                  "dexterity|smoke (what the rank unlocks)")
    p.set_defaults(func=cmd_brew)

    p = sub.add_parser(
        "heal",
        help="cast the healing SPELL, between fights only (rank 1/2/3 "
             "mends 3/5/7 HP, 3 Power, the casting check rolls; rank 3 "
             "stands a Downed ally to 3 HP after a won fight)")
    p.add_argument("healer")
    p.add_argument("target")
    p.set_defaults(func=cmd_heal)

    p = sub.add_parser(
        "cast",
        help="a wizard's between-fights utility cast (combat spells fire "
             "on their own in the melee): `cast HERO scry` reads the "
             "active quest's rooms ahead (rank 1 the next room, 2 the "
             "site, 3 the whole quest + its TRUE level); `cast HERO "
             f"teleport DEST` (rank 3) steps to a VISITED settlement, "
             f"{TELEPORT_TRAVEL_COST_PER_DAY} Power per road day skipped "
             "-- no days pass, no road encounters, no interception. "
             "Rank-3 roleplay uses (ghost-walk, freeform divination) are "
             "DM-adjudicated in the scene (dm.md).")
    p.add_argument("hero")
    p.add_argument("spell", help="scry | teleport")
    p.add_argument("dest", nargs="*",
                   help="teleport only: the destination settlement")
    p.set_defaults(func=cmd_cast)

    p = sub.add_parser(
        "sheet",
        help="rewrite party.txt from the save and COMMIT it (that one "
             "file). Run at the END of every DM message (dm.md) -- the "
             "sheet's git history then reads one commit per message. "
             "Committing an unchanged sheet is a no-op and says so.")
    p.set_defaults(func=cmd_sheet)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
