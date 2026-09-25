"""The projection: the save, cut down to what the player may see.

The player's page (page-plan.md) reads a shared document store that anyone
who can open the page can read, with the developer tools if not with the
page. So the DM's secrets are never written to it at all: this module is the
only road from the save to the store, and it copies across only what the
player-facing surfaces already show -- the three ui/ pages, the tally, the
fight's player log, and the pause and level-up menus. Section 2 of the plan
is the contract.

``player_view`` returns the five singleton documents the keeper writes
(``game/state``, ``game/party``, ``game/map``, ``game/quests``,
``game/record``), keyed by path; ``chronicle_entry`` makes one
``chronicle/tNNNN`` document, one DM turn. ``clean_move`` reads a move from
the page as data, and ``pause_args`` turns a ``pause`` move into the
``session.py`` argv that plays it -- or refuses it. Nothing here rolls a die
or changes the save.

What crosses: exactly what the ui pages print, built by CALLING the same
functions they are built from (``hero_block_lines``, ``party_sheet_lines``,
``party_status_lines``, ``map_sheet_lines``, ``here_lines``,
``map_legend_lines``, ``quest_in_hand_lines``, ``history_sheet_lines``,
``sin_tally_lines``, ``hell_suggestions``, ``pause_menu_data`` and the
printed pause and level-up menus), plus structured copies of the numbers
those pages print, so the page can draw them.

What never crosses: the ``world`` dict and the ``rng`` blob raw; the board
(untaken jobs, hidden givers); a settlement slot the party does not know; a
room's roster; the DM's pages (``show``, ``look --dm``, ``tile``, ``lore``,
``prices``, ``armory``, ``place_debug_lines``); and ui/fight-detailed.txt.

Decisions this module makes that the plan left open:

* **Every document carries ``v``**, and keys are camelCase, as in dream.
* **HP is a word where the page it mirrors says a word** (the tally, the
  fight) and digits where it says digits (the party sheet, the pause menu).
* **Each ``text`` field is the ui page's lines exactly**, 40-column wrapped
  (``wrapped``), so the page can always show "the sheet as printed".
* **The map's ``rows`` are the base glyphs**: ``map_lines`` with no party
  and no objectives, gutter and axis cut. The party's coord and the
  objectives travel beside them, so the page draws the marks itself.
* **The pause is the menu's data** (``session.pause_menu_data``) and the
  menu's exact text. A Fate pause keeps its blink and smoke rows: they are
  retreats, and rules.md lets a clean escape pay Fate at the door.
* **A pause move is checked, not obeyed**: ``pause_args`` runs the same
  per-hero checks as ``resume`` and ``retreat`` (``check_pause_actions``,
  ``check_escape``) and returns the argv, or raises ``MoveRefused`` with a
  reason the DM answers in the fiction.
* **A malformed pause move is not a move**: a choice, escape or action
  outside the fixed sets makes ``clean_move`` return None rather than
  playing half of what the page sent.
"""
from __future__ import annotations

import contextlib
import io
from typing import Any, Iterable

import places
import session

__all__ = ["VIEW_VERSION", "STATUSES", "MOVE_KINDS", "MOVE_TEXT_MAX",
           "HERO_NAME_MAX", "ACTIONS_MAX", "SINGLETONS", "PAUSE_CHOICES",
           "OVER_KINDS", "CHECK_IN",
           "player_view", "state_view", "party_view", "map_view",
           "quests_view", "record_view", "member_sheet", "pause_view",
           "level_up_view", "game_over", "wrapped", "chronicle_id",
           "chronicle_entry", "clean_move", "MoveRefused", "pause_args"]

VIEW_VERSION = 1

#: What ``game/state`` says the DM is doing.
STATUSES = ("awaiting_player", "dm_thinking", "ended")

#: How a game ends (session.report_game_over's two states).
OVER_KINDS = ("wiped", "pc_dead")

#: What ``checkIn`` says when publish is not told otherwise.
CHECK_IN = "when you call from Claude Code"

#: What a move from the page can be (plan section 2).
MOVE_KINDS = ("say", "ooc", "pause")
MOVE_TEXT_MAX = 2000        # the page caps a move there too
HERO_NAME_MAX = 40
ACTIONS_MAX = 8

#: A pause move's first choice, and what each variant may carry.
PAUSE_CHOICES = ("fight_on", "retreat")

#: The documents ``player_view`` returns, in the order a batch writes them.
SINGLETONS = ("game/state", "game/party", "game/map", "game/quests",
              "game/record")

#: The pause options' words on the page.
_OPTION_LABELS = {"fight_on": "fight on", "drink": "drink",
                  "heal": "heal", "berserk": "berserk",
                  "warbreath": "war-breath", "vanish": "vanish",
                  "retreat": "retreat", "blink": "blink out",
                  "smoke": "smoke vial"}


# ---------------------------------------------------------------- helpers
def wrapped(lines: Iterable[str]) -> list[str]:
    """Lines as a ui page prints them: 40-column wrapped, one per row."""
    return session._wrap_block("\n".join(lines)).splitlines()


def _printed(fn, *args) -> list[str]:
    """What a session printer prints, captured (it wraps as it prints)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        fn(*args)
    return out.getvalue().splitlines()


def _coord(tile: dict) -> str:
    return session.tile_coordinate(tile["row"], tile["column"])


def _party_tile(state: dict) -> dict:
    return state["world"]["tiles"][state["position"]["tile"]]


def game_over(state: dict) -> str | None:
    """``"wiped"``, ``"pc_dead"`` or None -- report_game_over's rule: the
    whole party dead, or the player character (party[0]) dead."""
    party = state["party"]
    if party and all(h.dead for h in party):
        return "wiped"
    if party and party[0].dead:
        return "pc_dead"
    return None


# ---------------------------------------------------------------- the whole view
def player_view(state: dict, *, status: str = "awaiting_player",
                last_seq: int = 0, latest: str | None = None,
                check_in: str | None = None, last_fight: str | None = None,
                pause_fight: str | None = None) -> dict[str, dict[str, Any]]:
    """Every singleton document the keeper writes, keyed by path.

    The save does not know the handshake, so ``game/state``'s ``status``,
    ``lastSeq``, ``latest`` chronicle entry, ``lastFight``, ``checkIn`` and
    the id of the fight that paused are handed in."""
    return {
        "game/state": state_view(state, status=status, last_seq=last_seq,
                                 latest=latest, check_in=check_in,
                                 last_fight=last_fight,
                                 pause_fight=pause_fight),
        "game/party": party_view(state),
        "game/map": map_view(state),
        "game/quests": quests_view(state),
        "game/record": record_view(state),
    }


# ---------------------------------------------------------------- game/state
def state_view(state: dict, *, status: str = "awaiting_player",
               last_seq: int = 0, latest: str | None = None,
               check_in: str | None = None, last_fight: str | None = None,
               pause_fight: str | None = None) -> dict[str, Any]:
    """Where the game stands: the day, the place, what the game waits on."""
    if status not in STATUSES:
        raise ValueError(f"{status!r} is not one of {', '.join(STATUSES)}")
    over = game_over(state)
    if over:
        status = "ended"
    world, pos = state["world"], state["position"]
    return {
        "v": VIEW_VERSION,
        "status": status,
        "lastSeq": int(last_seq),
        "day": state["clock"].day,
        "where": session.location_line(state),
        "coord": _coord(_party_tile(state)),
        "land": world["lands"][pos["land"]]["name"],
        "latest": latest,
        "lastFight": last_fight,
        "checkIn": check_in if check_in is not None else CHECK_IN,
        "over": over,
        "pause": (pause_view(state, pause_fight)
                  if state.get("pending") and not over else None),
        "levelUp": None if over else level_up_view(state),
    }


def pause_view(state: dict, fight: str | None = None) -> dict[str, Any]:
    """The paused fight's menu as data (session.pause_menu_data) and as
    printed. ``fight`` is the published id of the fight that paused."""
    data = session.pause_menu_data(state)
    options = []
    for opt in data["options"]:
        out: dict[str, Any] = {"choice": opt["choice"],
                               "label": _OPTION_LABELS[opt["choice"]],
                               "cost": opt["cost"]}
        if "heroes" in opt:
            out["heroes"] = list(opt["heroes"])
        if "hero" in opt:
            out["hero"] = opt["hero"]
        options.append(out)
    return {
        "fight": fight,
        "round": data["round"],
        "kind": data["kind"],
        "trips": data["trips"],
        "facing": [{"name": f["name"], "hp": f["hp"], "maxHp": f["max_hp"]}
                   for f in data["facing"]],
        "party": [{"name": r["name"], "down": r["down"],
                   "hpState": r["hp_state"], "hp": r["hp"],
                   "hpCeiling": r["hp_ceiling"], "maxHp": r["max_hp"],
                   "sta": r["sta"], "staMax": r["sta_max"],
                   "power": r["power"], "powerMax": r["power_max"],
                   "penalties": ", ".join(r["penalties"]),
                   "conditions": list(r["conditions"]),
                   "wounds": list(r["wounds"]),
                   "healing": r["healing"], "stamina": r["stamina"]}
                  for r in data["party"]],
        "options": options,
        "text": _printed(session.print_pause_menu, state),
    }


def level_up_view(state: dict) -> dict[str, Any] | None:
    """The PC's spending menu while he has points banked, else None.
    Companions autolevel; only the PC banks points for the player."""
    party = state["party"]
    if not party or party[0].dead or party[0].skill_points <= 0:
        return None
    pc = party[0]
    return {"hero": pc.name, "points": pc.skill_points,
            "text": _printed(session.print_levelup_menu, [pc])}


# ---------------------------------------------------------------- game/party
def party_view(state: dict) -> dict[str, Any]:
    """The party sheet: every hero's block, the purse, the slots, and the
    sheet's tail (the active quest, sin, the pact, a paused fight)."""
    party = state["party"]
    pc = party[0]
    return {
        "v": VIEW_VERSION,
        "day": state["clock"].day,
        "purse": state["purse"].silver,
        "slots": {"filled": sum(1 for h in party[1:] if not h.dead),
                  "cap": session.party_capacity(pc.cha), "cha": pc.cha},
        "members": [member_sheet(party, h) for h in party],
        "status": wrapped(session.party_status_lines(state)),
        "text": wrapped(session.party_sheet_lines(state)),
    }


def member_sheet(party: list, h) -> dict[str, Any]:
    """One hero, every number hero_block_lines prints and nothing more."""
    return {
        "name": h.name,
        "nickname": h.nickname or "",
        "isPc": h is party[0],
        "homeland": h.homeland or "",
        "sex": h.sex or "",
        "age": h.age,
        "level": h.level,
        "training": h.training,
        "xp": h.xp,
        "xpNext": session.xp_to_next(h.level),
        "points": h.skill_points,
        "dex": h.dex, "str": h.str_, "mind": h.mind, "cha": h.cha,
        "hp": h.hp, "hpCeiling": h.hp_ceiling, "maxHp": h.max_hp,
        "hpState": h.hp_state,
        "sta": h.cur_sta, "staMax": h.sta,
        "power": h.cur_power, "powerMax": h.power,
        "weapon": session.weapon_tag(h),
        "kit": {k: v for k, v in h.items.items() if v},
        "spells": dict(sorted(h.spells.items())),
        "abilities": session.ability_tags(h),
        "moves": sorted(h.moves),
        "alchemy": h.alchemy,
        "satisfaction": h.satisfaction,
        "traits": list(session.trait_bits(h)),
        "blood": session.blood_line(h) if h.blood else "",
        "tongues": session.tongue_line(h) if h.tongues else "",
        "conditions": list(session.condition_tags(h)),
        "wounds": list(session.wound_tags(h)),
        "woundLoad": h.wound_load,
        "dead": h.dead,
        "down": h.down,
        "quitting": session.wants_to_leave(h),
        "text": wrapped(session.hero_block_lines(party, h)),
    }


# ---------------------------------------------------------------- game/map
def _legend() -> list[list[str]]:
    """The map legend as [glyph, word] pairs, read off places' own three
    legend lines so the page cannot drift from map.txt."""
    pairs = []
    for line in (session.MAP_GLYPH_LEGEND, session.MAP_MARK_LEGEND,
                 session.MAP_GATE_LEGEND):
        for item in line.split("  "):
            glyph, word = item.strip().split(" ", 1)
            pairs.append([glyph, word])
    return pairs


def _places(world: dict) -> list[dict[str, Any]]:
    """The settlements the party KNOWS and the four gates (common knowledge
    from day one): exactly what the map legend names."""
    out = []
    for key in places.GATE_KEYS:
        gate = world["gates"][key]
        tile = world["tiles"][gate["tile"]]
        out.append({"coord": _coord(tile),
                    "name": places.GATE_BY_KEY[key]["name"],
                    "kind": "gate ruin" if gate["kind"] == "ruin"
                    else "gate city",
                    "land": world["lands"][tile["country"]]["name"],
                    "capital": False})
    for tid in world["tile_order"]:
        tile = world["tiles"][tid]
        for slot in places.known_slots(world, tile):
            out.append({"coord": _coord(tile), "name": slot["name"],
                        "kind": slot["tier"],
                        "land": world["lands"][tile["country"]]["name"],
                        "capital": bool(slot["capital"])})
    return out


def map_view(state: dict) -> dict[str, Any]:
    """The map page: the grid's base glyphs, the party's coord and the
    objectives, the known places, and the blocks map.txt prints below."""
    world, pos = state["world"], state["position"]
    grid = session.map_lines(world)[2:]         # cut the two axis rows
    gutter = len(places.MAP_GUTTER)
    objectives = [_coord(world["tiles"][t])
                  for t in session.quest_objective_tiles(state)]
    day = state["clock"].day
    return {
        "v": VIEW_VERSION,
        "day": day,
        "coord": _coord(_party_tile(state)),
        "rows": [row[gutter:] for row in grid],
        "objectives": objectives,
        "legend": _legend(),
        "places": _places(world),
        "here": wrapped(session.here_lines(state)),
        "land": {"name": world["lands"][pos["land"]]["name"],
                 "lines": wrapped(session.worldsim.land_lines(
                     world, pos["land"]))},
        "known": wrapped(session.map_legend_lines(world)),
        "holdings": wrapped(session.conquest.holdings_lines(
            world, state.get("holdings") or {}, day)),
        "text": wrapped(session.map_sheet_lines(state)),
    }


# ---------------------------------------------------------------- game/quests
def _quest_status(q: dict) -> str:
    if q.get("proof_pending"):
        return "proof_pending"
    return "work_done" if q["status"] == "work_done" else "open"


def quests_view(state: dict) -> dict[str, Any]:
    """The quests in hand -- taken, not finished -- as the map page lists
    them. An untaken posting never appears."""
    world, day = state["world"], state["clock"].day
    quests = []
    for q in session.accepted_quests(state):
        delivery = q.get("kind") == "delivery"
        origin = world["areas"].get(q.get("origin"))
        road = session._quest_road_lines(state, q)
        quests.append({
            "id": q["id"],
            "name": q["name"],
            "level": q.get("level"),
            "kind": "delivery" if delivery else "",
            "origin": origin["name"] if origin else "",
            "status": _quest_status(q),
            "sites": [] if delivery else [
                {"name": s["name"], "level": s["level"], "mark": mark}
                for s, mark in session.quest_site_marks(world, q)],
            "road": road[0] if road else "",
            "due": q.get("deadline_day"),
            "note": (session.deadline_note(q, day)
                     if q["status"] in ("open", "work_done") else ""),
            "cargo": q["cargo"] if delivery else None,
            "dest": q["dest_name"] if delivery else None,
            "lines": wrapped(session.quest_in_hand_lines(state, q)),
        })
    return {"v": VIEW_VERSION, "active": state.get("active_quest"),
            "quests": quests}


# ---------------------------------------------------------------- game/record
def record_view(state: dict) -> dict[str, Any]:
    """The history page: the jobs, the remarkable, the tally of sin and
    hell's suggestions, oldest first as history.txt keeps them."""
    log = session.history_log(state)

    def entries(kind: str, note: bool) -> list[dict[str, Any]]:
        out = []
        for rec in log:
            if rec.get("kind") != kind:
                continue
            row: dict[str, Any] = {"day": rec["day"], "line": rec["line"]}
            if note:
                row["note"] = rec.get("note", "")
            out.append(row)
        return out

    return {
        "v": VIEW_VERSION,
        "day": state["clock"].day,
        "quests": entries("quest", True),
        "remarkable": entries("remarkable", False),
        "tally": wrapped(session.sin_tally_lines(state)),
        "suggestions": [{"key": c["key"], "name": c["name"],
                         "line": c["line"]}
                        for c in session.hell_suggestions(state)],
        "text": wrapped(session.history_sheet_lines(state)),
    }


# ---------------------------------------------------------------- the chronicle
def chronicle_id(turn: int) -> str:
    """``chronicle/t0001``'s id: ``t`` and the turn to four digits, so id
    order is turn order."""
    return f"t{int(turn):04d}"


def chronicle_entry(turn: int, prose: str,
                    answered: Iterable[dict[str, Any]] = (), *,
                    state: dict, fights: Iterable[str] = ()
                    ) -> dict[str, Any]:
    """One DM turn, written once: the moves it answered, the prose, the
    fights. ``answered`` are the page's moves as read; each is cleaned
    (``clean_move``) and kept in seq order. What the turn left true is
    stamped on it: each hero's level (a rise between two entries is a
    level-up) and whether the game is over."""
    moves = [m for m in (clean_move(m) for m in answered) if m is not None]
    moves.sort(key=lambda m: m["seq"])
    return {
        "v": VIEW_VERSION,
        "id": chronicle_id(turn),
        "turn": int(turn),
        "day": state["clock"].day,
        "where": session.location_line(state),
        "coord": _coord(_party_tile(state)),
        "prose": str(prose).strip(),
        "answered": moves,
        "fights": [str(f) for f in fights],
        "levels": {h.name: h.level for h in state["party"]},
        "over": game_over(state) is not None,
    }


# ---------------------------------------------------------------- moves
def _text(value: Any, cap: int) -> str:
    return value.strip()[:cap] if isinstance(value, str) else ""


def clean_move(move: Any) -> dict[str, Any] | None:
    """A move from the page, as data: the known fields of the known kinds.

    The page is untrusted input. Anything that is not a move of a known
    kind with a whole ``seq`` of at least 1 comes back None; text is capped;
    unknown fields are dropped. A pause move is whole or nothing: a choice,
    escape or action outside the fixed sets, a hero name missing, or more
    than ACTIONS_MAX actions, and it is not a move. Nothing in a move is
    ever followed as an instruction."""
    if not isinstance(move, dict):
        return None
    seq = move.get("seq")
    if isinstance(seq, float) and seq.is_integer():
        seq = int(seq)                  # JSON has one number type
    if isinstance(seq, bool) or not isinstance(seq, int) or seq < 1:
        return None
    kind = move.get("kind")
    if kind not in MOVE_KINDS:
        return None
    out: dict[str, Any] = {"seq": seq, "kind": kind}
    at = move.get("at")
    if isinstance(at, (int, float)) and not isinstance(at, bool):
        out["at"] = int(at)
    if kind in ("say", "ooc"):
        out["text"] = _text(move.get("text"), MOVE_TEXT_MAX)
        return out if out["text"] else None
    # kind == "pause"
    out["fight"] = _text(move.get("fight"), HERO_NAME_MAX)
    choice = move.get("choice")
    if choice not in PAUSE_CHOICES:
        return None
    out["choice"] = choice
    if choice == "fight_on":
        actions = move.get("actions") or []
        if not isinstance(actions, list) or len(actions) > ACTIONS_MAX:
            return None
        clean = []
        for a in actions:
            if not isinstance(a, dict):
                return None
            hero = _text(a.get("hero"), HERO_NAME_MAX)
            action = a.get("action")
            if not hero or action not in session.PAUSE_ACTIONS:
                return None
            clean.append({"hero": hero, "action": action})
        out["actions"] = clean
    else:
        escape = move.get("escape")
        if escape is not None:
            hero = _text(move.get("hero"), HERO_NAME_MAX)
            if escape not in session.ESCAPES or not hero:
                return None
            out["escape"] = escape
            out["hero"] = hero
    return out


class MoveRefused(ValueError):
    """A move the keeper does not play: the reason, for the DM to answer in
    the fiction."""


def _hero(party: list, name: str):
    """The hero a page move names, by his whole name (any case); refused
    when there is none, or when ``session.find_hero``'s substring match
    would land on somebody else (a "Ali" beside an "Alibek")."""
    hero = next((h for h in party if h.name.lower() == name.lower()), None)
    if hero is None:
        raise MoveRefused(f"there is no {name} in the party")
    if session._hero_named(party, hero.name) is not hero:
        raise MoveRefused(f"{hero.name}'s name would reach another hero "
                          f"from the command line")
    return hero


def pause_args(move: dict[str, Any], state: dict, *,
               paused_fight: str | None) -> list[str]:
    """The ``session.py`` argv that plays a ``pause`` move, e.g.
    ``["resume", "--heal", "Amina"]`` or ``["retreat", "--blink", "Nasir"]``.

    ``paused_fight`` is the id of the fight the published page showed as
    paused (``game/state.pause.fight``); a move answering any other fight is
    stale. The per-hero gates are session's own (``check_pause_actions``,
    ``check_escape``), so the page can never ask for what ``resume`` or
    ``retreat`` would refuse. Anything else raises :class:`MoveRefused`
    with the reason; nothing is run here."""
    cleaned = clean_move(move)
    if cleaned is None or cleaned["kind"] != "pause":
        raise MoveRefused("that is not a pause choice")
    pending = state.get("pending")
    if not pending:
        raise MoveRefused("no fight is paused")
    if not paused_fight or cleaned["fight"] != paused_fight:
        raise MoveRefused("that pause is over: the move answers "
                          f"{cleaned['fight'] or 'no fight'}, and the pause "
                          f"on the page is {paused_fight or 'none'}")
    fate = pending.get("pause_kind") == "fate"
    party = state["party"]
    if cleaned["choice"] == "fight_on":
        if fate and cleaned["actions"]:
            raise MoveRefused("Fate's pause is fight on or retreat, "
                              "with no pause action")
        requests = [(a["action"], _hero(party, a["hero"]).name)
                    for a in cleaned["actions"]]
        try:
            session.check_pause_actions(state, requests)
        except ValueError as refused:
            raise MoveRefused(str(refused)) from None
        argv = ["resume"]
        for action, name in requests:
            argv += [f"--{action}", name]
        return argv
    if "escape" not in cleaned:
        return ["retreat"]
    hero = _hero(party, cleaned["hero"])
    try:
        session.check_escape(state, cleaned["escape"], hero.name)
    except ValueError as refused:
        raise MoveRefused(str(refused)) from None
    return ["retreat", f"--{cleaned['escape']}", hero.name]
