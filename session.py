"""DM session driver -- runs the game turn-by-turn from the terminal.

rpg.py's primitives (open_fight, group_combat, long_rest, ...)
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
  map / travel / look / go / back           -- world and local navigation
  explore / hunt / engage                   -- the wilds
  board / show QID / take QID / room        -- the LOCAL jobs (the game;
                                               board = the DM inventory,
                                               in play quests come from
                                               their GIVERS -- dm.md)
  chatter                                   -- a party-flavor seed (dm.md)
  task / bribe / settle                     -- the hell pact (2026-07-19):
                                               the assignment ledger,
                                               greasing hell's hand, and
                                               taking a caper twist's terms
  case [KEY] / crime KEY / crimes            -- the crime layer (2026-08-04):
                                               free honest casing of the
                                               local mark, then the deed
                                               itself (no giver, no board);
                                               `crimes` is the price sheet
  sin [dark|penance N ...]                  -- the sin & heat meter
  conquer / garrison N / holdings           -- the domain layer (2026-07-27):
                                               take a settlement by its
                                               garrison, hold it with paid
                                               levies, collect tribute
  fight N                                   -- off-script encounters
  hideout ROOM / barrow ROOM                -- the two set sites (DEV/TEST
                                               only since 2026-07-13; not
                                               part of a played campaign)
  resume [...] / retreat [--blink]          -- settle a paused fight
  camp / tavern / downtime / award / buy / give / train / use / heal
  prices                                    -- the shop price sheet (DM ref)
  cast HERO scry|teleport                   -- the between-fights layer
                                               (cast = wizard utility magic)
  forge                                     -- DM-built quest, off the board
  sheet                                     -- commit every ui/ page
                                               (run at the END of every DM
                                               message, after writing
                                               ui/scene.md -- dm.md)

All output is wrapped at WRAP_WIDTH columns (the designer plays on a phone
whose code blocks show ~41 characters and never soft-wrap).
"""
from __future__ import annotations

import argparse
import builtins
import dataclasses
import json
import random
import re
import subprocess
import textwrap
from pathlib import Path

from rpg import (
    Clock, CombatLog, Purse, Entity, Weapon, POTION_KINDS, WEAPONS,
    Condition, condition_tags,
    Wound, wound_tags, wound_morale, healer_service as _healer_service,
    DISEASE_KINDS, DISEASE_FEE, DISEASE_REACH, CONDITION_TAG, treat_disease,
    marked_up,
    HEALER_FEE, HEALER_TIER_CAP, HEALER_DAYS, SALVE_PRICE,
    SHOP_POTION_KINDS, BED_SEVERITY_PER_NIGHT,
    POTION_PRICE,
    ENCOUNTER_XP, TRAINING_MAX, PROFICIENCY_MAX, LEVEL_CAP,
    STAMINA_DRAUGHT_RESTORE, HEALING_POTION_RESTORE,
    PAUSE_ACTION_DEF_PENALTY,
    KIT_HEALING, KIT_STAMINA,
    TAVERN_COST_PER_HERO, TAVERN_OVERCHARGE,
    BERSERK_HP_COST, BERSERK_STA_GAIN,
    WAR_BREATH_POWER_COST, WAR_BREATH_STA_GAIN,
    standing_order,
    SATISFACTION_START, SATISFACTION_MAX, SAT_DOWNTIME, SAT_DOWNTIME_MATCH,
    SAT_TAVERN_COOLDOWN_DAYS,
    MEDS_INTERVAL_DAYS, MEDS_PRICE,
    party_capacity, has_trait, satisfaction_tracked, wants_to_leave,
    adjust_satisfaction, satisfaction_after_fight,
    stat_line, fallen_weapons_line, weapon_tag, prof_name,
    random_trash_weapon, MASTERWORK_PRICE_MULT,
    xp_to_next, quest_encounter_xp, quest_clear_xp, quest_turnin_xp,
    quest_gold,
    track_contest,
    open_fight, group_combat, party_wiped, party_defeated,
    apply_defeat_mercy, mercy_available, FEROCITY_RELENTLESS,
    FEROCITY_BREAKS,
    attempt_retreat, refresh_foes_after_retreat,
    award_xp, roll_loot, award_quest,
    long_rest as _long_rest,
    tavern_rest as _tavern_rest,
    buy_potion as _buy_potion, cast_healing as _cast_healing,
    use_potion as _use_potion, buy_weapon as _buy_weapon,
    auto_potions,
    equip_weapon as _equip_weapon,
    train_combat_once as _train_combat_once,
    train_proficiency as _train_proficiency,
    train_spell as _train_spell,
    learn_spell as _learn_spell,
    buy_spellbook as _buy_spellbook,
    buy_pool as _buy_pool, learn_ability as _learn_ability,
    learn_move as _learn_move, MOVES, move_weapon_ok,
    train_alchemy as _train_alchemy, brew as _brew, auto_brew,
    alchemy_recipes, brew_stock_cap, alchemy_cost,
    ALCHEMY_MAX, ALCHEMY_BATCH, ALCHEMY_RECIPE_RANK, POTION_DISPLAY,
    DRINKABLE_KINDS,
    ABILITIES, ability_tags, training_cost,
    POOL_KINDS, POOL_BUY_CAP, SKILL_POINTS_PER_LEVEL,
    storyteller_tale, survivalist_ground, survivalist_comfort,
    blink_escape, casting_check,
    SPELLS, SPELL_RANK_MAX, SPELLBOOK_PRICE, VANISH_POWER_COST,
    SCRY_POWER_COST, TELEPORT_TRAVEL_COST_PER_DAY, TELEPORT_ESCAPE_COST,
    autospend_points,
    ROOM_FIELD, WILD_FIELD, AMMO_LOTS, AMMO_CAPS, RANGED_WEAPONS,
    buy_ammo as _buy_ammo, grant_starter_ammo,
    WINDED_PENALTY, SPENT_PENALTY, fit_lines,
)
import story
import karma
import crime
import conquest
import worldsim                 # the world layer (2026-08-07, the frame)
import weapons as weaponlib     # the weapon generation system (2026-07-28)
from people import (make_character, make_pair, character_sheet, person_line,
                    npc_line, downtime_match, joining_gold, PAIR_CHANCE)
from sites import SITES, FOES, BANDIT_KINDS, WEAPON_INDEX, make_foe, roster_lines
from quests import (generate_world, forge_quest, board_lines,
                    quest_gold_posted,
                    quest_detail_lines, quest_line, roster_kinds_line,
                    level_grade,
                    all_areas, settlements, settlements_by_land,
                    area_sites, quest_sites, site_rooms,
                    complete_quest_place_state,
                    roll_wild_level, build_wild_encounter,
                    wild_encounter_xp,
                    TRAVEL_ENCOUNTER_CHANCE, EXPLORE_ENCOUNTER_CHANCE,
                    EXPLORE_XP, SPOTTED_MARGIN, AMBUSH_CHANCE,
                    HUNT_AMBUSH_CHANCE,
                    CAMP_ENCOUNTER_CHANCE,
                    HUNT_LEVEL_REACH,
                    notice_contest, foes_preferred_field,
                    expire_settlement_board, refresh_settlement_board,
                    refresh_deliveries, next_quest_id, release_quest_places,
                    quest_band, quest_expired, deadline_note, failure_line,
                    open_quests, board_forecast,
                    cast_service_providers,
                    nearby_settlements, rumor_lines,
                    QUEST_GRACE_DAYS, QUEST_PAY_BANDS, QUEST_RUMOR_DAYS)
from places import (
    materialize_natural_site, materialize_house,
    active_known_facts, place_debug_lines, find_place,
    add_state as add_place_state, replace_state as replace_place_state,
    clear_state as clear_place_state, land_homeland, reveal_tile,
    settlement_tier,
    direction_word, edge_days, edge_direction, map_legend_lines, map_lines,
    neighbor_id, parse_coordinate, path_days, shortest_path, tile_coordinate,
    tile_detail_lines as places_tile_detail, tile_id as tile_id_of, tile_label,
    MAP_GLYPH_LEGEND, MAP_MARK_LEGEND,
)

STATE_PATH = Path(__file__).parent / "save.json"

# --------------------------------------------------------------------------- #
# Output wrapping (2026-07-13) -- the designer plays through a coding-agent CLI on
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
# Position (the navigation layer, 2026-07-09; hierarchy 2026-07-22)
# --------------------------------------------------------------------------- #
# The party's position is a breadcrumb through Country -> Tile -> Area ->
# Site -> Room. Day-scale movement is a walk along cardinal TILE edges
# (2026-08-15); Areas inside one Tile, Sites and Rooms are local and free.

def _area_position(area: dict) -> dict:
    return {"land": area["land"], "tile": area["tile"], "area": area["key"],
            "site": None, "room": None}


def move_party(state: dict, area: dict) -> None:
    """Stand the party in `area` -- the one way position moves once a game
    is running (a travel arrival, a free step to a sibling Area, a
    teleport)."""
    state["position"] = _area_position(area)


def location_line(state: dict) -> str:
    world, pos = state["world"], state["position"]
    area = world["areas"][pos["area"]]
    tile = world["tiles"][pos["tile"]]
    names = [world["lands"][pos["land"]]["name"], tile["name"], area["name"]]
    if pos.get("site"):
        names.append(world["sites"][pos["site"]]["name"])
    if pos.get("room"):
        names.append(world["rooms"][pos["room"]]["name"])
    return " > ".join(names)


def current_area(state: dict) -> dict:
    return state["world"]["areas"][state["position"]["area"]]


def local_settlement(state: dict) -> dict | None:
    """The settlement the party is AT, or None out in the wilds."""
    area = current_area(state)
    return area if area["kind"] == "settlement" else None


def home_settlement(state: dict) -> dict:
    """The capital (settlements[0]) -- the two hand-built DEV/TEST set
    sites lie outside it. (Since 2026-07-13 a new game starts at the
    settlement with the lowest-level job, which may be elsewhere.)"""
    return settlements(state["world"])[0]


def party_wiped_out(state: dict) -> bool:
    """Nobody left standing. A route that ends this way is over: the fight's
    own machinery has saved, and there is no arrival to narrate."""
    return all(h.dead for h in state["party"])


def clear_sighting(state: dict, quiet: bool = False) -> None:
    """Spotted foes don't wait around: any move (travel, explore, hunt, camp)
    lets them drift on. `engage` is the only way to fight a sighting."""
    if state.get("sighting"):
        if not quiet:
            print("(The foes sighted earlier have moved on.)")
        state["sighting"] = None


def _settlement_by_key(world: dict, key: str) -> dict | None:
    area = world["areas"].get(key)
    return area if area and area["kind"] == "settlement" else None


def at_quest_origin(state: dict, quest: dict) -> bool:
    """Taking a quest requires standing in the area where it was offered."""
    key = quest.get("origin")
    if not key:
        return True     # a placeless forged quest works anywhere
    if state["position"]["area"] == key:
        return True
    area = state["world"]["areas"].get(key)
    name = area["name"] if area else key
    print(f"[{quest['id']}] {quest['name']} is {name}'s business -- the "
          f"party is at {location_line(state)}. `travel {key}` first.")
    return False


def at_quest_site(state: dict, quest: dict) -> bool:
    """Working a quest requires reaching its current world-owned site."""
    cur = quest["next"]
    site = quest_sites(state["world"], quest)[cur["site"]]
    if state["position"]["area"] != site["area"]:
        area = state["world"]["areas"][site["area"]]
        print(f"The next site is {site['name']} in {area['name']}. "
              f"`travel {area['key']}` first.")
        return False
    if state["position"].get("site") != site["id"]:
        print(f"The next site is {site['name']}. `go {site['name']}` first.")
        return False
    return True


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
    ref["move_tags"] = tuple(ref.get("move_tags", ()))
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
    # Conditions (slice 3a) DO travel: an untimed one outlives the fight, so
    # it has to outlive the save too. dataclasses.asdict already flattened
    # them into plain dicts -- and so are the WOUND records (slice 3b), which
    # outlive rather more than a fight. `wound_stat_pen` travels with them:
    # the raw stats are saved ALREADY docked, so the reload has to know how
    # much is folded away or _sync_wound_stats would charge for it twice.
    return d


def _entity_from_dict(d: dict) -> Entity:
    d = dict(d)
    d["weapon"] = _weapon_from(d["weapon"])
    d["abilities"] = set(d.get("abilities", ()))
    d["moves"] = set(d.get("moves", ()))
    d["moves_spent"] = set(d.get("moves_spent", ()))
    d["feint_target"] = None
    # Conditions come back as dicts (and are simply absent in a pre-slice-3a
    # save, which is the same thing as carrying none).
    d["conditions"] = [Condition(**c) for c in d.get("conditions", ())]
    # Wounds (slice 3b). Absent in a pre-slice save, which is the same thing
    # as an unwounded party -- and since such a save's stats were never
    # docked, its (missing) wound_stat_pen is correctly empty too.
    d["wounds"] = [Wound(**w) for w in d.get("wounds", ())]
    d["wound_stat_pen"] = dict(d.get("wound_stat_pen", {}))
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
        "crime": pending.get("crime"),
        "pursuit": pending.get("pursuit"),
        "dead_before": pending.get("dead_before", []),
        "field": pending.get("field", 0),
        "weather": pending.get("weather", ""),
        "align": pending.get("align", "neutral"),
        "mercy": pending.get("mercy"),
        "pause_kind": pending.get("pause_kind", "normal"),
        "normal_pause_used": pending.get("normal_pause_used", True),
    }


def _pending_from_dict(d: dict | None, party: list) -> dict | None:
    if d is None:
        return None
    by_name = {h.name: h for h in party}
    crossings = [tuple(c) for c in d["crossings"]]
    pause_kind = d.get(
        "pause_kind",
        "fate" if any(kind == "fate" for kind, _ in crossings) else "normal",
    )
    return {
        "foes": [_entity_from_dict(f) for f in d["foes"]],
        "fired": {(kind, by_name[name]) for kind, name in d["fired"]},
        "round": d["round"],
        "crossings": crossings,
        "xp": d["xp"],
        "site": d["site"],
        "room": d["room"],
        "quest": d.get("quest"),
        "crime": d.get("crime"),
        "pursuit": d.get("pursuit"),
        "dead_before": d.get("dead_before", []),
        "field": d.get("field", 0),
        "weather": d.get("weather", ""),
        "align": d.get("align", "neutral"),
        "mercy": d.get("mercy"),
        "pause_kind": pause_kind,
        # Fate now consumes the one ordinary pause. A pre-slice pending save
        # was necessarily the old ordinary pause, so True is the safe default
        # for either shape.
        "normal_pause_used": d.get("normal_pause_used", True),
    }


# The player-facing display files: the game's GitHub UI. The party/map/
# history pages are rewritten on every save; the two fight pages are
# last-fight snapshots; the scene page and the transcript are DM-AUTHORED
# (dm.md, The scene page: the DM message itself is a file) -- the engine
# never writes those two, it only commits them. `sheet` commits every page
# that exists so the player and DM can read them as blob pages on the
# branch. See dm.md.
UI_DIR = Path(__file__).parent / "ui"
PARTY_SHEET_PATH = UI_DIR / "party.txt"
MAP_SHEET_PATH = UI_DIR / "map.txt"
HISTORY_SHEET_PATH = UI_DIR / "history.txt"
FIGHT_DETAILED_PATH = UI_DIR / "fight-detailed.txt"
FIGHT_SHORT_PATH = UI_DIR / "fight-short.txt"
UI_COMMIT_PATHS = (
    "ui/party.txt",
    "ui/map.txt",
    "ui/history.txt",
    "ui/fight-short.txt",
    "ui/fight-detailed.txt",
    "ui/scene.md",
    "ui/transcript.md",
)


def hero_block_lines(party: list, h) -> list[str]:
    """One hero as a tidy 40-column block: a header naming who they are,
    then short labeled rows all hanging exactly two spaces. Shared by the
    party sheet and `status` so the two readouts never drift (2026-07-28
    display pass: the old layout indented every row 12-14 spaces to sit
    under the role tag -- a third of the phone's width spent on air, and
    every wrapped row turned to confetti)."""
    tag = " [DEAD]" if h.dead else " [DOWN]" if h.down else ""
    if wants_to_leave(h):
        tag += " [QUITTING at the next settlement]"
    head = f"{role_tag(party, h)} {h.name}"
    if h.nickname:
        head += f' "{h.nickname}"'
    if h.homeland:
        head += f" -- {h.homeland} {h.sex}, age {h.age}"
    lines = [head + tag]
    lines.append(f"  L{h.level}  training {h.training}  "
                 f"XP {h.xp}/{xp_to_next(h.level)}  points {h.skill_points}")
    stats = f"  DEX {h.dex}  STR {h.str_}"
    if h.mind:
        stats += f"  MIND {h.mind}"
    if h.cha:
        stats += f"  CHA {h.cha}"
    lines.append(stats)
    # A wounded body shows its CEILING beside the pool (slice 3b's doctrine,
    # same as stat_line): "HP 6/9 of 11" is the whole slow channel at once.
    hp = (f"HP {h.hp}/{h.hp_ceiling} of {h.max_hp}" if h.wounds
          else f"HP {h.hp}/{h.max_hp}")
    lines.append(f"  {hp}  STA {h.cur_sta}/{h.sta}  "
                 f"Power {h.cur_power}/{h.power}")
    kit = ", ".join(f"{k}x{v}" for k, v in h.items.items() if v) or "no kit"
    lines.append(f"  {weapon_tag(h)} | {kit}")
    if h.spells:
        lines.append("  spells: " + ", ".join(
            f"{n} {r}" for n, r in sorted(h.spells.items())))
    if h.abilities:
        lines.append("  abilities: " + ", ".join(ability_tags(h)))
    if h.moves:
        lines.append("  moves: " + ", ".join(sorted(h.moves)))
    if h.alchemy:
        lines.append(f"  alchemy {h.alchemy}")
    pools = ", ".join(f"{k} +{v}"
                      for k, v in sorted(h.pool_bought.items()) if v)
    if pools:
        lines.append(f"  pools bought: {pools}")
    dormant = ", ".join(f"{n} {r}" for n, r in sorted(h.proficiency.items())
                        if r and (h.weapon is None or n != h.weapon.name))
    if dormant:
        lines.append(f"  drilled, not in hand: {dormant}")
    if h.satisfaction is not None:
        lines.append(f"  satisfaction {h.satisfaction}/{SATISFACTION_MAX}")
    if h.homeland:
        # person_line's trait sketch, minus the name and homeland/age already
        # in the header (one source for the category order: people.py).
        traits = person_line(h).split(" -- ", 1)[1].partition("; ")[2]
        if traits:
            lines.append(f"  {traits}")
    for ctag in condition_tags(h):
        lines.append(f"  [{ctag}]")
    for wtag in wound_tags(h):
        lines.append(f"  - {wtag}")
    if h.wounds:
        lines.append(f"  wound load {h.wound_load} -> "
                     f"HP ceiling {h.hp_ceiling}/{h.max_hp}")
    return lines


def party_sheet_lines(state: dict) -> list[str]:
    """The full-party info sheet written to party.txt on every save: the
    whole between-fights board in one plain file (the designer reads it in
    the coding agent on the web via the auto-commit; the DM never has to
    reassemble it from logs)."""
    party, clock, purse = state["party"], state["clock"], state["purse"]
    loc = location_line(state) if state.get("position") else "nowhere yet"
    lines = [f"RPG2 PARTY SHEET -- day {clock.day}, at {loc}",
             f"purse: {purse.gold}g"]
    if not party:
        lines.append("(no party yet -- `pick` a character)")
        return lines
    pc = party[0]
    if pc.cha:
        companions = sum(1 for h in party[1:] if not h.dead)
        lines.append(f"party: {companions}/{party_capacity(pc.cha)} "
                     f"companion slot(s) filled (CHA {pc.cha})")
    for h in party:
        lines.append("")
        lines.extend(hero_block_lines(party, h))
    lines.append("")
    world = state.get("world")
    qid = state.get("active_quest")
    if world and qid and qid in world["quests"]:
        q = world["quests"][qid]
        if q["status"] in ("failed", "expired"):
            lines.append(f"active quest [{qid}] {q['name']} is LOST "
                         f"(the window closed)")
        elif q["status"] == "lost":
            lines.append(f"active quest [{qid}] {q['name']} is DONE, "
                         f"NEVER PAID (the window closed on the road home)")
        elif q["status"] == "done":
            lines.append(f"active quest [{qid}] {q['name']} is COMPLETE")
        elif q["status"] == "work_done":
            g = q.get("giver")
            origin = world["areas"].get(q.get("origin"), {})
            lines.append(f"active quest [{qid}] {q['name']}: THE WORK IS "
                         f"DONE -- return to "
                         f"{g['name'] if g else 'the giver'} at "
                         f"{origin.get('name', q.get('origin'))} "
                         f"(`turnin {qid}`)")
        elif q.get("kind") == "delivery":
            lines.append(f"active quest: [{qid}] DELIVERY {q['name']} -- "
                         f"carry {q['cargo']} to {q['dest_name']} "
                         f"(travel {q['dest']})")
        elif q.get("proof_pending"):
            lines.append(f"active quest [{qid}] {q['name']}: the field is "
                         f"cleared but THE TARGET ESCAPED -- the job still "
                         f"wants {q['proof']}. `pursue` while the trail is "
                         f"warm")
        else:
            cur = q["next"]
            s = quest_sites(world, q)[cur["site"]]
            rooms = site_rooms(world, s)
            lines.append(f"active quest: [{qid}] L{q['level']} {q['name']} "
                         f"-- next: {s['name']} (L{s['level']}), room "
                         f"{cur['room'] + 1}/{len(rooms)}")
        note = (deadline_note(q, clock.day)
                if q["status"] in ("open", "work_done") else "")
        if note:
            lines.append(f"  due day {q['deadline_day']} -- {note}")
    k = state.get("karma")
    if k and k.get("sin_total"):
        meter = karma.karma_line(k, party_level(state), state["clock"].day)
        lines.append(f"sin: {meter}")
    lines.extend(pact_lines(state))
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


def accepted_quests(state: dict) -> list[dict]:
    """The quests the party has TAKEN and not yet finished -- what the map
    shows sites for. `cmd_take` records each in state["accepted"]; the active
    quest and any quest whose cursor has moved off {0,0} also count (so a
    pre-2026-07-22 save, or a save whose accepted list got out of step, still
    maps what's in hand). Offered-but-untaken jobs never appear: the map is
    where the party has been or is bound, not the whole board (a design ask
    of the 2026-07-22 map display)."""
    world = state.get("world")
    if not world:
        return []
    taken = set(state.get("accepted") or [])
    if state.get("active_quest"):
        taken.add(state["active_quest"])
    out = []
    for qid, q in world["quests"].items():
        if q.get("status") in ("done", "failed", "expired", "lost"):
            continue
        progressed = q.get("next", {"site": 0, "room": 0}) != {"site": 0,
                                                                "room": 0}
        if qid in taken or progressed:
            out.append(q)
    return out


def _quest_site_lines(world: dict, q: dict) -> list[str]:
    """One line per site of a taken quest, tagged by the progress cursor:
    cleared / here (with the room) / not yet. These ARE the 'sites the player
    has quests to visit' -- the door banner reveals a site's true level on
    entry, and a taken quest is committed, so levels print plain here."""
    cur = q.get("next", {"site": 0, "room": 0})
    lines = []
    for j, s in enumerate(quest_sites(world, q)):
        n = len(site_rooms(world, s))
        if j < cur["site"]:
            mark = "cleared"
        elif j == cur["site"]:
            mark = (f"here, room {cur['room'] + 1}/{n}"
                    if cur["room"] < n else "cleared")
        else:
            mark = f"not yet ({n} room(s))"
        lines.append(f"  - {s['name']} (L{s['level']}): {mark}")
    return lines


def _quest_road_lines(state: dict, quest: dict) -> list[str]:
    """How far the job's next mark is, in shortest-path days from where the
    party stands. The clock is priced in road days, so the map says them."""
    world, pos = state["world"], state["position"]
    if quest.get("kind") == "delivery":
        area = world["areas"].get(quest.get("dest"))
    else:
        sites = quest_sites(world, quest)
        index = min(quest["next"]["site"], len(sites) - 1) if sites else -1
        area = world["areas"][sites[index]["area"]] if index >= 0 else None
    if area is None:
        return []
    tile = world["tiles"][area["tile"]]
    days = path_days(pos["tile"], tile["id"])
    where = tile_coordinate(tile["row"], tile["column"])
    return [f"{where}: {'here' if not days else f'{days} road day(s)'}"]


def quest_objective_tiles(state: dict) -> list[str]:
    """The Tiles the party's TAKEN work points at -- a delivery's
    destination, or the next unfinished Site of every other job. What the
    map marks `!`."""
    world = state["world"]
    tiles: list[str] = []
    for quest in accepted_quests(state):
        if quest.get("kind") == "delivery":
            area = world["areas"].get(quest.get("dest"))
            if area is not None:
                tiles.append(area["tile"])
            continue
        sites = quest_sites(world, quest)
        index = min(quest["next"]["site"], len(sites) - 1) if sites else -1
        if index >= 0:
            tiles.append(world["areas"][sites[index]["area"]]["tile"])
    return list(dict.fromkeys(tiles))


def here_lines(state: dict) -> list[str]:
    """The detail block under the grid: which Tile the party stands on,
    whose it is, what it is made of, and which of its Areas it knows --
    everything the one-character glyph had to drop."""
    world, pos = state["world"], state["position"]
    tile = world["tiles"][pos["tile"]]
    lines = places_tile_detail(world, tile, areas=False)
    for aid in tile["areas"]:
        area = world["areas"][aid]
        if not area.get("known"):
            continue
        marks = []
        if aid == pos["area"]:
            marks.append("<- the party")
        if area["kind"] == "settlement":
            marks.append(f"{board_forecast(world, area, state['clock'].day)}"
                         f" job(s)")
            if aid in (state.get("holdings") or {}):
                marks.append("YOURS")
        facts = active_known_facts(area)
        if facts:
            marks.append(facts[0]["id"])
        kind = area.get("subtype", area["kind"])
        note = ("  " + ", ".join(marks)) if marks else ""
        lines.append(f"  {area['name']} ({kind}){note}")
    if len(tile["areas"]) > len([a for a in tile["areas"]
                                 if world["areas"][a].get("known")]):
        lines.append("  (more here is unknown)")
    return lines


def map_sheet_lines(state: dict) -> list[str]:
    """The world map written to map.txt on every save (2026-07-22; the GRID
    since 2026-08-15): the game's second GitHub-UI page. The whole fixed
    30x18 Europe under a numeric axis, the party and its taken work marked
    on it, the current Tile in detail below, a compact known-settlement
    legend by country, and the sites of every TAKEN quest with its progress.
    Player-facing, so it never prints the DM-only board (untaken postings,
    hidden givers): terrain is common knowledge, but settlements appear only
    once the party knows them."""
    world = state.get("world")
    if not world:
        return ["RPG2 MAP", "(no world yet -- start one with `new`)"]
    pos = state["position"]
    st = state.get("story")
    objectives = quest_objective_tiles(state)
    lines = [f"RPG2 MAP -- day {state['clock'].day}",
             f"the party is at {location_line(state)}", ""]
    lines.extend(map_lines(world, party=pos["tile"], objectives=objectives))
    lines.append("")
    lines.append(MAP_GLYPH_LEGEND)
    lines.append(MAP_MARK_LEGEND)
    lines.append("")
    lines.extend(here_lines(state))
    # The STATE DIFF (2026-08-07, the world layer): the country's wealth
    # band and whatever it is living through -- its own states and the ones
    # its trade edges derive. The country the party is STANDING in: word
    # travels where the party is, and this is what shows the world moved
    # while it was on the road.
    lines.append("")
    yoke = "  [UNDER THE YOKE]" if st and st.get("fallen") == pos["land"] else ""
    lines.append(f"-- {world['lands'][pos['land']]['name']} --{yoke}")
    lines.extend(worldsim.land_lines(world, pos["land"]))
    legend = map_legend_lines(world)
    if legend:
        lines.append("")
        lines.append("-- known settlements --")
        lines.extend(legend)
    taken = accepted_quests(state)
    if taken:
        lines.append("")
        lines.append("-- quests in hand (where they lead) --")
        for q in taken:
            origin = world["areas"].get(q.get("origin"))
            posted = f" @ {origin['name']}" if origin else ""
            lines.append("")
            if q.get("kind") == "delivery":
                lines.append(f"[{q['id']}] DELIVERY {q['name']}{posted}")
                lines.append(f"  - carry {q['cargo']} to {q['dest_name']} "
                             f"(travel {q['dest']})")
            else:
                lines.append(f"[{q['id']}] {q['name']} (L{q['level']}){posted}")
                lines.extend(_quest_site_lines(world, q))
            lines.extend(f"  - {line}" for line in _quest_road_lines(state, q))
    hold = conquest.holdings_lines(world, state.get("holdings") or {},
                                   state["clock"].day)
    if hold:
        lines.append("")
        lines.extend(hold)
    war = story.war_status_lines(world, st)
    if war:
        lines.append("")
        lines.append("-- the war --")
        lines.extend(war)
    return lines


# --------------------------------------------------------------------------- #
# The history page (2026-08-04, THE DARK REWORK's session C)
# --------------------------------------------------------------------------- #
# The fourth committed UI page: what this campaign has DONE. The party
# sheet is the present and the map is the world; this is the memory --
# the jobs finished, the things that will be remembered, and the tally of
# sin the crime layer keeps. It is also the DM's continuity crib: a
# playthrough spans days of real time and the record has to outlive the
# chat scrollback.
#
# `history` is the save key: a list of day-stamped records, oldest first.
# Two kinds, because the page has two narrative sections -- "quest" (the
# job record, done and lost alike) and "remarkable" (everything else
# worth a line). Nothing writes here automatically except what the code
# below names on purpose; the DM's own entries come through `sin dark N
# REASON` and hand-editing the save.

HISTORY_CAP = 60        # records kept PER KIND -- the page is a phone
                        # page, and a career runs hundreds of jobs. The
                        # oldest fall off the top; the tally never does.


def history_log(state: dict) -> list[dict]:
    return state.setdefault("history", [])


def remember(state: dict, line: str, kind: str = "remarkable",
             note: str = "", day: int | None = None) -> None:
    """Write one day-stamped record into the campaign history. Silently
    ignores an exact duplicate of the most recent record of its kind, so
    a command run twice (or a re-scan like `_note_maimings`) never
    doubles the page."""
    log = history_log(state)
    rec = {"day": state["clock"].day if day is None else day,
           "kind": kind, "line": line}
    if note:
        rec["note"] = note
    for old in reversed(log):
        if old.get("kind") != kind:
            continue
        if old.get("line") == line and old.get("day") == rec["day"]:
            return
        break
    log.append(rec)
    # Trim per kind, oldest first: a career of quests must never push the
    # write-offs and the maimings off the page.
    kept = [r for r in log if r.get("kind") == kind]
    for dead in kept[:-HISTORY_CAP]:
        log.remove(dead)


def _note_maimings(state: dict) -> None:
    """A maiming is permanent, so it is history the moment it lands.
    Scanned rather than hooked: maimings accrue deep inside `_attack`,
    and `remember`'s duplicate guard makes the scan idempotent."""
    for h in state.get("party") or []:
        for w in getattr(h, "wounds", ()) or ():
            if w.permanent:
                remember(state, f"{h.name} is MAIMED -- {w.name}.")


def _named_dead(foes: list) -> list[str]:
    """The named foes that fell: quest bosses, conquest defenders, posse
    leaders, the war's lieutenants. Ordinary rows are numbered off the
    catalog ('Cutthroat 2'); a name without its number is somebody the
    fiction bothered to cast."""
    return [f.name for f in foes
            if f.dead and not re.search(r" \d+$", f.name)]


def history_sheet_lines(state: dict) -> list[str]:
    """ui/history.txt: the campaign's record in four sections -- the jobs,
    the remarkable, the tally of sin, and what hell is currently
    advertising. Player-facing and 40-column, like every UI page."""
    day = state["clock"].day
    lines = [f"RPG2 HISTORY -- day {day}",
             "(what this campaign has done)"]

    def section(title: str, body: list[str], empty: str) -> None:
        lines.append("")
        lines.append(f"-- {title} --")
        lines.extend(body or [f"  ({empty})"])

    def entries(kind: str) -> list[str]:
        out = []
        for rec in history_log(state):
            if rec.get("kind") != kind:
                continue
            out.append(f"day {rec['day']}: {rec['line']}")
            if rec.get("note"):
                out.append(f"  {rec['note']}")
        return out

    section("QUESTS DONE", entries("quest"), "no job finished yet")
    section("REMARKABLE", entries("remarkable"), "nothing yet")

    crimes = state.get("crimes") or crime.new_crimes()
    rows = crime.tally_rows(crimes)
    tally = []
    for name, count, last in rows:
        when = f", last day {last}" if last >= 0 else ""
        tally.append(f"  {name}: {count}{when}")
    if rows:
        kinds = "category" if len(rows) == 1 else "categories"
        tally.append(f"  ({crime.total_crimes(crimes)} crime(s) in "
                     f"{len(rows)} {kinds})")
    else:
        tally.append("  (no crime committed yet)")
    k = state.get("karma")
    if k:
        tally.append(f"  {karma.karma_line(k, party_level(state), day)}")
        tally.append(f"  lifetime sin {k.get('sin_total', 0)} / penance "
                     f"{k.get('penance_total', 0)}")
    section("THE TALLY OF SIN", tally, "no sin on the books")

    # Seeded off the world and the day: the same page rewritten twice in
    # one day shows the same three, and tomorrow advertises differently
    # (catalogue order would sell the same two petty crimes forever).
    feed = crime.suggestions(
        crimes, rng=crime.mark_rng(world_seed(state), "history", day,
                                   "suggestions"))
    section("SUGGESTIONS", [f"  {c['key']} -- {c['name']}: {c['line']}"
                            for c in feed],
            "hell is not advertising -- `case` lists everything anyway")
    return lines


def _write_party_sheet(state: dict) -> None:
    """Write party.txt (phone-wrapped, like all output) on every save.
    NEVER raises on I/O: a broken disk must not take the game loop down
    with it. Rendering runs OUTSIDE the guard on purpose -- a bug in the
    sheet code must crash loudly, not freeze the page silently (the map
    sheet spent days stuck on day 1 that way, 2026-08-03).
    COMMITTING the sheet is `sheet`'s job (2026-07-13): one commit at the
    end of every DM message, not one per command -- the designer reads the
    playthrough as message-sized diffs."""
    text = _wrap_block("\n".join(party_sheet_lines(state))) + "\n"
    try:
        UI_DIR.mkdir(parents=True, exist_ok=True)
        PARTY_SHEET_PATH.write_text(text, encoding="utf-8")
    except Exception:
        return


def _write_map_sheet(state: dict) -> None:
    """Write map.txt (the world-map UI page) on every save, beside party.txt.
    NEVER raises on I/O, for the same reason `_write_party_sheet` doesn't --
    a disk hiccup must not sink the game loop. Rendering runs OUTSIDE the
    guard: swallowing a render bug here is what froze map.txt at day 1 for
    days after the first wilderness area was revealed (2026-08-03).
    `sheet` commits it alongside the party sheet."""
    text = _wrap_block("\n".join(map_sheet_lines(state))) + "\n"
    try:
        UI_DIR.mkdir(parents=True, exist_ok=True)
        MAP_SHEET_PATH.write_text(text, encoding="utf-8")
    except Exception:
        return


def _write_history_sheet(state: dict) -> None:
    """Write history.txt (the campaign record) on every save, beside the
    party and map pages. Same contract as those two: rendering runs
    OUTSIDE the I/O guard so a render bug crashes loudly instead of
    freezing the page."""
    text = _wrap_block("\n".join(history_sheet_lines(state))) + "\n"
    try:
        UI_DIR.mkdir(parents=True, exist_ok=True)
        HISTORY_SHEET_PATH.write_text(text, encoding="utf-8")
    except Exception:
        return


def cmd_sheet(args: argparse.Namespace) -> None:
    """Rewrite party/map/history and commit every existing ui/ page.

    Fight pages do not exist until the first encounter. Once written, they
    join the same end-of-message commit as the three rewritten pages.
    """
    state = load()
    _write_party_sheet(state)
    _write_map_sheet(state)
    _write_history_sheet(state)
    day = state["clock"].day
    where = (current_area(state)["name"]
             if state.get("position") else "nowhere")
    paths = list(UI_COMMIT_PATHS)
    try:
        root = Path(__file__).parent
        paths = [path for path in paths if (root / path).exists()]
        subprocess.run(["git", "add", *paths], cwd=root, check=False,
                       capture_output=True, timeout=15)
        done = subprocess.run(
            ["git", "commit", "--quiet",
             "-m", f"ui: day {day} at {where}", "--", *paths],
            cwd=root, check=False, capture_output=True, timeout=15)
    except Exception as exc:
        print(f"UI sheets written; commit failed ({exc}) -- the game is "
              f"unaffected.")
        return
    if done.returncode == 0:
        print(f"UI pages committed (day {day} at {where}).")
    else:
        print("UI pages unchanged -- nothing to commit.")


def save(state: dict) -> None:
    party = state["party"]
    # A maiming is permanent and lands deep inside the melee: catch it
    # here, where every path that could have caused one passes through.
    _note_maimings(state)
    rng_version, rng_internal, rng_gauss = state["rng"].getstate()
    doc = {
        "party": [_entity_to_dict(h) for h in party],
        "clock": {"day": state["clock"].day},
        "purse": {"gold": state["purse"].gold},
        "foe_count": state["foe_count"],
        "active_quest": state.get("active_quest"),
        "accepted": state.get("accepted", []),
        "world": state.get("world"),
        "story": state.get("story"),
        "position": state.get("position"),
        "sighting": state.get("sighting"),
        "site_clears": state.get("site_clears", {}),
        "recruits": state.get("recruits"),
        "visited": state.get("visited", []),
        "karma": state.get("karma") or karma.new_karma(),
        "pact": state.get("pact"),
        "crimes": state.get("crimes") or crime.new_crimes(),
        # The services counter's cooldowns (2026-08-11): option key -> the
        # day it was last bought. A blessing is not buyable twice a week.
        "services": state.get("services", {}),
        "history": state.get("history", []),
        "holdings": state.get("holdings", {}),
        # The loose ends (2026-08-08): who got away from a rout, newest
        # first -- what `pursue` reads and a proof quest checks. The fled
        # foes ride each record as entity dicts, so a won trail re-opens
        # the fight at their exact fled state. No expiry: entries persist
        # until the DM prunes them by save edit -- they are story, not
        # bookkeeping.
        "loose_ends": state.get("loose_ends", []),
        "pending_reward": state.get("pending_reward"),
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
    _write_map_sheet(state)
    _write_history_sheet(state)


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
    position = doc.get("position")
    return {
        "party": party,
        "clock": Clock(**doc["clock"]),
        "purse": Purse(**doc["purse"]),
        "rng": rng,
        "foe_count": doc["foe_count"],
        "active_quest": doc.get("active_quest"),
        # Quests the party has TAKEN (map.txt shows their sites; offered-but-
        # -untaken jobs never appear).
        "accepted": doc.get("accepted", []),
        "world": world,
        "story": doc.get("story"),
        "position": position,
        "sighting": doc.get("sighting"),
        "site_clears": doc.get("site_clears", {}),
        "recruits": doc.get("recruits"),
        "visited": doc.get("visited", []),
        "karma": doc.get("karma") or karma.new_karma(),
        # None = a pactless save (new --no-pact): the hell layer stays
        # inert -- no default resurrect.
        "pact": doc.get("pact"),
        # The crime ledger (2026-08-04): counts, day stamps and the
        # suggestion feed's unlocked flags. crime.py owns its shape.
        "crimes": doc.get("crimes") or crime.new_crimes(),
        # The services counter's cooldowns (2026-08-11, religion & magic).
        "services": doc.get("services") or {},
        # The campaign record (2026-08-04, session C): day-stamped
        # "quest" and "remarkable" lines behind ui/history.txt.
        "history": doc.get("history") or [],
        "holdings": doc.get("holdings", {}),
        # The loose-ends record (2026-08-08): rout escapees, newest first.
        "loose_ends": doc.get("loose_ends") or [],
        "pending_reward": doc.get("pending_reward"),
        "pending": _pending_from_dict(doc.get("pending"), party),
        "rooms": rooms,
    }


def role_tag(party: list, h) -> str:
    """party[0] is the player character; the rest are companions (see dm.md).
    Unpadded since 2026-07-28 -- nothing aligns under it anymore (the hero
    blocks hang everything two spaces, see hero_block_lines)."""
    return "(YOU)" if h is party[0] else "(companion)"


def find_hero(party: list, name: str):
    """Substring hero lookup, None (with a message) instead of a crash."""
    for h in party:
        if name.lower() in h.name.lower():
            return h
    print(f"No hero matches {name!r}. Party: "
          + ", ".join(h.name for h in party))
    return None


def new_combat_log(continuing: bool = False) -> CombatLog:
    """A two-level log configured for the UI's last-fight snapshots.

    New encounters replace both files. Resume/retreat calls continue the
    paused fight already in them, so one fight remains intact even though it
    spans two session.py processes.
    """
    return CombatLog(debug_path=FIGHT_DETAILED_PATH,
                     player_path=FIGHT_SHORT_PATH,
                     continuing=continuing)


def print_combat(log: CombatLog) -> None:
    """Print THE combat log (2026-07-21: the player-facing level is the only
    combat display -- the DM narrates over it and pastes it as-is; see
    rules.md, "Reading the combat log"). Both levels are also written as
    last-fight snapshots: ui/fight-short.txt is the paste/narration backup;
    ui/fight-detailed.txt carries dice math, modifiers, and stamina readouts
    for post-mortems. group_combat already flushes detailed mechanics at
    resolution/pause; these cursor-safe flushes capture the session tail
    without duplicating lines."""
    if isinstance(log, CombatLog) and log.player:
        log.flush_debug()
        log.flush_player()
        print("\n".join(log.player))
    else:
        print("\n".join(log))


def print_play(log) -> None:
    """Print a between-fights command's log at the PLAYER level (dice and
    debug lines stay off the played surface -- the 2026-07-21 one-log rule
    applies to camps and potions as much as to melees). Plain lists print
    as-is."""
    lines = log.player if isinstance(log, CombatLog) else log
    print("\n".join(lines) if lines else "(nothing happened)")


def log_banner(log, full: str, parts: list[str]) -> None:
    """An encounter banner in two shapes: the one-line full-log form and the
    fitted col-1 player lines (fit_lines packs `parts`)."""
    if isinstance(log, CombatLog):
        log.play(full, fit_lines(parts))
    else:
        log.append(full)


def tally_lines(state: dict) -> list[str]:
    """The standard after-the-fight DISPLAY block, appended to every
    encounter's player log: the party's tracks and kit, the purse, the
    and -- for an active quest -- how many encounters are LEFT.
    The numbers are SHOWN here so the
    DM's prose never has to carry them (dm.md, narration style); ahead of
    the party it gives a count only, never a roster -- upcoming room
    contents are DM eyes only."""
    party, clock, purse = state["party"], state["clock"], state["purse"]
    lines = ["", "-- the party --"]
    for h in party:
        if h.dead:
            continue
        kit = ", ".join(f"{k} x{v}" for k, v in h.items.items() if v)
        # HP reads as a STATE WORD in play (slice 3b, the designer's "no HP
        # as a number"): the digits stay one command away in `status` and in
        # ui/fight-detailed.txt. Purely a display call, cheaply reversible.
        lines.append(f"{h.name.split()[0]}: {h.hp_state} "
                     f"STA {h.cur_sta}/{h.sta} "
                     f"Power {h.cur_power}/{h.power}")
        if h.down:
            lines.append("  [DOWN]")
        # The standing roll penalties, shown HERE (2026-07-21): the fight
        # lines stopped carrying the numbers -- the between-fights display
        # is where the player budgets around them.
        pens = []
        if h.wound_penalty:
            # "hurt", not "wounds" (slice 3b): this is the HP-derived spiral,
            # the FAST channel. The named located records print below it, and
            # the two must not read as the same number.
            pens.append(f"hurt -{h.wound_penalty}")
        if h.spent:
            pens.append(f"Spent -{SPENT_PENALTY}")
        elif h.winded:
            pens.append(f"Winded -{WINDED_PENALTY}")
        if pens:
            lines.append(f"  ({', '.join(pens)} to rolls)")
        # What is still ON them after the fight (slice 3a): first aid stopped
        # the bleeding, so anything listed here is what a night (or, later, a
        # healer) has to answer -- and it ticks again in the next room.
        for tag in condition_tags(h):
            lines.append(f"  [{tag}]")
        # The SLOW channel (slice 3b): what a night in the wilds will NOT
        # answer. This is the list the player budgets a bed, a salve or a
        # healer's day against.
        for tag in wound_tags(h):
            lines.append(f"  - {tag}")
        if h.wounds:
            lines.append(f"  (HP ceiling {h.hp_ceiling}/{h.max_hp} "
                         f"until they mend)")
        lines.append(f"  ({kit or 'no kit'})")
    lines.append(f"Purse {purse.gold}g; day {clock.day}.")
    k = state.get("karma")
    if k and k.get("sin_total"):
        meter = karma.karma_line(k, party_level(state), state["clock"].day)
        lines.append(f"Sin: {meter}.")
    qid = state.get("active_quest")
    world = state.get("world")
    if qid and world:
        q = world["quests"].get(qid)
        # The pay ahead is quoted AT TODAY'S BAND (2026-07-26): the number
        # the player budgets against is what the job pays if it is handed
        # over now, not what the board advertised on the day it posted.
        # Since the turn-in stage (2026-08-08) only the TURN-IN tranche and
        # the gold band -- the field lump at work-done is quoted straight.
        band = quest_band(q, clock.day) if q else "on time"
        mult = QUEST_PAY_BANDS[band]
        if q and q.get("proof_pending"):
            lines.append(f"The field is cleared, but the target got away. "
                         f"The job still wants {q['proof']}: `pursue` while "
                         f"the trail is warm -- nothing is paid until the "
                         f"target is dead.")
        elif q and q["status"] == "open" and q.get("kind") != "delivery":
            cur = q["next"]
            s = quest_sites(world, q)[cur["site"]]
            left = len(site_rooms(world, s)) - cur["room"]
            sites_after = len(q["sites"]) - cur["site"] - 1
            ahead = f"Ahead: {left} fight(s) at {s['name']}"
            if sites_after:
                ahead += f", then {sites_after} more place(s)"
            enc = q.get("encounters", 1)
            field_xp = quest_clear_xp(q["level"], enc)
            lump = round(quest_turnin_xp(q["level"], enc) * mult)
            gold = round(quest_gold_posted(q) * mult)
            lines.append(f"{ahead}; the work done pays {field_xp} XP in "
                         f"the field, and the turn-in pays {gold}g, "
                         f"{lump} XP at the giver.")
            note = deadline_note(q, clock.day)
            if note:
                lines.append(f"  (due day {q['deadline_day']} -- {note}; "
                             f"{band} pay, x{mult:g})")
        elif q and q["status"] == "work_done":
            g = q.get("giver")
            origin = world["areas"].get(q.get("origin"), {})
            enc = q.get("encounters", 1)
            lump = round(quest_turnin_xp(q["level"], enc) * mult)
            gold = round(quest_gold_posted(q) * mult)
            lines.append(f"The work is done: return to "
                         f"{g['name'] if g else 'the giver'} at "
                         f"{origin.get('name', q.get('origin'))} -- the "
                         f"turn-in pays {gold}g, {lump} XP "
                         f"(`turnin {qid}`).")
            note = deadline_note(q, clock.day)
            if note:
                lines.append(f"  (due day {q['deadline_day']} -- {note}; "
                             f"{band} pay, x{mult:g})")
    return lines


def append_tally(state: dict, log: CombatLog) -> None:
    """Close a survived encounter's log with the tally block (emitted via
    play so the block's own two-space indents survive -- plain append
    unindents its player copy)."""
    party = state["party"]
    if party and not party[0].dead:
        for line in tally_lines(state):
            if isinstance(log, CombatLog):
                log.play(line, line)
            else:
                log.append(line)


def require_no_pending(state: dict) -> bool:
    """Most commands are between-fights actions; refuse them mid-melee."""
    if not state["party"]:
        print("No party in this save -- `new` starts a game.")
        return False
    if state.get("pending"):
        if state["pending"].get("pause_kind") == "fate":
            print("A fight is PAUSED at Fate's bargain. Resolve it first: "
                  "resume (fight on), or retreat.")
        else:
            print("A fight is PAUSED -- the party is mid-melee. Resolve it "
                  "first: resume [--drink HERO] [--heal HERO] "
                  "[--berserk HERO] [--warbreath HERO], or retreat.")
        return False
    return True


# --------------------------------------------------------------------------- #
# Starting the game -- the level roll and the career kit (2026-08-05)
# --------------------------------------------------------------------------- #
# A new game starts at ANY level (designer call). The DEFAULT is a ROLL:
# nothing above level 4 has ever been played (CLAUDE.md's played-reality
# note), and a start that lands anywhere on the ladder is how the rest of
# the game gets seen at all. `new --level N` fixes the band when a session
# is testing one. Everything above level 1 is autogenerated career: the
# levels' points are spent by doctrine (rpg.develop_hero + autospend_points
# -- the levelup menu is for PLAYED progression, not for paging through
# thirty banked points by hand), the arms are what those levels bought, and
# the purse holds what the jobs behind them left over.

START_LEVEL_ROLL_MAX = 18   # the default roll is 1..this. LEVEL_CAP is 20;
                            # a start with no ladder left above it is a
                            # diorama, not a playthrough.
START_QUESTS_PER_LEVEL = 2  # the career sim's measured pace (develop.md) --
                            # what the purse below is reckoned against
START_PURSE_SHARE = 0.20    # of the gold those jobs paid on the way up. A
                            # played party has SPENT most of what it earned
                            # (potions, beds, books, the healer), so this is
                            # deliberately a fifth: testing convenience, not
                            # economy fidelity.
START_SPELL_LEVELS = 5      # one career SPELLBOOK per this many levels. The
                            # PC is always a magic user, and a level-18
                            # wizard who knows exactly one spell is not what
                            # that band looks like from the inside -- by 18
                            # he has bought three books (SPELLBOOK_PRICE is
                            # 120g against thousands earned).


def start_level(args: argparse.Namespace, rng: random.Random) -> int:
    """The level a fresh game starts at: `--level N` when given, else a
    roll in 1..START_LEVEL_ROLL_MAX off the run's own rng, so `--seed`
    pins the level with everything else."""
    if getattr(args, "level", None) is not None:
        return args.level
    return rng.randint(1, START_LEVEL_ROLL_MAX)


def career_purse(level: int) -> int:
    """What a party STARTING at `level` carries: a share of what the jobs
    on the way up would have paid (rpg.quest_gold at the career pace), most
    of it already spent. 0 at level 1 -- the ordinary game starts broke."""
    earned = sum(START_QUESTS_PER_LEVEL * quest_gold(l, 2)
                 for l in range(1, level))
    return round(START_PURSE_SHARE * earned)


def career_kit(pc: Entity, ally: Entity, level: int, rng: random.Random,
               log: list[str]) -> None:
    """Everything a level-N start owes the pair beyond their stat blocks.

    The arms: develop_hero already put quality steel in a level-4+ hand,
    and on top of that the PC claims the best job reward of his band
    (weapons.reward_weapon_for_level) -- the piece a career of turn-ins
    would have landed. A PC on a FOCUS staff claims the STAFF of that band
    instead of rolling the chassis: his staff is his quality weapon (the
    same rule develop_hero follows), so the upgrade has to keep the focus
    rather than trade it for steel that has none.

    The books: a spellbook per START_SPELL_LEVELS, each learned at rank 1
    (what a book teaches; ranks are skill points, and the doctrine already
    spent those on the school).

    The points: both autospend the doctrine's leftovers. The PC's banked
    points are normally the player's to spend and stay his after this --
    this is only the history he arrives with."""
    focus = (pc.weapon.name
             if pc.weapon is not None and pc.weapon.power_bonus else None)
    reward = weaponlib.reward_weapon_for_level(level, rng, chassis=focus)
    if reward.name != (pc.weapon.name if pc.weapon else None):
        _equip_weapon(pc, reward, log)
    for _ in range((level - 1) // START_SPELL_LEVELS):
        unknown = [s for s in sorted(SPELLS) if s not in pc.spells]
        if not unknown:
            break
        _learn_spell(pc, rng.choice(unknown), log)
    for h in (pc, ally):
        autospend_points(h, log)


def _start_pact(rng: random.Random, level: int) -> dict:
    """The pact a level-N game opens with: hell's ledger stamped as though
    it had been collecting all along, so a career start does not open with
    a backlog of assignments it never refused. Every pin BELOW the starting
    level counts as served; the pin AT it is live, which is why the level-1
    game still opens on hell's tutorial job and a level-4 one waits for
    level 5."""
    pact = karma.new_pact(rng)
    pact["last_pin_served"] = max(
        (p for p in karma.TASK_PIN_LEVELS if p < level), default=0)
    return pact


def career_line(h: Entity) -> str | None:
    """The one-line summary of what a career start BOUGHT that the stat
    line doesn't already show (rpg.stat_line carries training, spells,
    abilities, moves, the weapon and the kit): the pools and the drills."""
    bits = []
    pools = ", ".join(f"{k} +{v}"
                      for k, v in sorted(h.pool_bought.items()) if v)
    if pools:
        bits.append(f"pools {pools}")
    drilled = ", ".join(f"{n} {r}" for n, r in sorted(h.proficiency.items())
                        if r)
    if drilled:
        bits.append(f"drilled {drilled}")
    return "career: " + "; ".join(bits) if bits else None


def _starting_settlement(world: dict) -> dict:
    """The settlement slot selected uniformly by fixed-Europe worldgen."""
    return world["areas"][world["start_area"]]


def opening_hook(state: dict) -> list[str]:
    """The job the game opens on (2026-07-13, designer call: the game
    starts at the doorstep of a combat quest, not in a tavern): the most
    level-appropriate open quest where the party stands -- the posting
    closest to the PC's level (at level 1, the lowest one: the ordinary
    game's hook is unchanged). The DM frames the first scene in front of
    its giver, mid-pitch; taking it stays the player's call."""
    world = state["world"]
    here = local_settlement(state)
    if here is None:
        return []
    open_q = [world["quests"][qid] for qid in here["quests"]
              if world["quests"][qid]["status"] == "open"
              and world["quests"][qid].get("kind") != "delivery"]
    if not open_q:      # (a delivery never opens the game -- combat does)
        return []
    level = state["party"][0].level
    q = min(open_q, key=lambda q: (abs(q["level"] - level), q["level"],
                                   q["id"]))
    lines = [f"OPENING HOOK -- frame the first scene at this job's "
             f"doorstep (dm.md); taking it is the player's call:",
             f"  [{q['id']}] L{q['level']} {q['name']}"]
    g = q.get("giver")
    if g:
        lines.append(f"  giver: {npc_line(g)}")
    return lines


def cmd_new(args: argparse.Namespace) -> None:
    if args.level is not None and not 1 <= args.level <= LEVEL_CAP:
        print(f"--level takes a level of 1-{LEVEL_CAP}.")
        return
    rng = random.Random(args.seed)
    level = start_level(args, rng)
    world_seed = rng.randrange(1 << 30)
    world = generate_world(world_seed, start_level=level)
    start = _starting_settlement(world)
    homeland = start["land"]
    # The PC is GENERATED, not chosen (2026-07-13, designer call -- the old
    # three-candidate pick is gone): male by designer fiat, no trait sketch
    # (2026-08-05: traits are the companion layer -- they are chosen against
    # at hiring, and the PC is nobody's hire), and rerolled until his CHA
    # holds at least one companion -- a capacity-0 solo game was a trap
    # dressed as a choice.
    #
    # He is ALWAYS A MAGIC USER (2026-08-05, designer call). The gift is
    # rolled at creation and NOTHING can grant it later -- a book is just
    # diagrams to a non-wizard (rpg.learn_spell) -- so a warrior PC is a PC
    # with a door permanently shut. The reverse never binds: a wizard levels
    # as a warrior any day he likes (combat training, weapon proficiency and
    # the move repertoire are all on his menu), so starting him with the
    # gift takes nothing away and opens everything.
    while True:
        pc = make_character(rng, level=level, sex="m",
                            homeland=homeland,
                            with_traits=False, wizard=True)
        if party_capacity(pc.cha) >= 1:
            break
    pc.protagonist = True   # fate's bargain guards the PC (rpg.Entity)
    used = {pc.name}
    # The long-time companion: generated with the PC and presented as
    # having been at his side for years (2026-07-13 reframe -- nobody
    # "joins" in the first scene), on a hire's terms otherwise -- the trait
    # sketch included, because his is the layer traits are FOR.
    ally = make_character(rng, level=level, homeland=homeland,
                          used_names=used)
    ally.satisfaction = SATISFACTION_START
    ally.bond, ally.bond_kind = pc.name, "old companion"
    career_log: list[str] = []
    if level == 1:
        # The trash start (2026-07-28, the weapon generation system): at
        # chargen the pair carries TRASH arms -- club, knife, sling -- so the
        # first looted soldier's blade is a felt upgrade. Casters keep the
        # staff (deliberately poor steel, priced in support). Chargen only:
        # recruits rolled later keep the ordinary table -- and so does a
        # CAREER start, which is past the scene the trash arms are for.
        for h in (pc, ally):
            if h.weapon is None or h.weapon.name != "wooden staff":
                h.weapon = random_trash_weapon(rng)
    else:
        career_kit(pc, ally, level, rng, career_log)
    start["visited"] = True
    state = {"party": [pc, ally], "clock": Clock(), "purse": Purse(),
             "rng": rng, "foe_count": 0, "pending": None, "rooms": {},
             "world": world, "active_quest": None, "accepted": [],
             "story": story.init_story(world, rng,
                                       pc_homeland=pc.homeland),
             "position": _area_position(start),
             "sighting": None,
             "site_clears": {},
             "recruits": None,
             "karma": karma.new_karma(),
             # THE HELL PACT (2026-07-19): the PC is a low-ranking
             # employee of Hell by default -- `--no-pact` is the
             # neutral-adventurer switch (and what the old game was).
             # The pact's DECK is shuffled here, off the run's rng, so
             # `--seed` pins the assignment order with everything else.
             "pact": None if args.no_pact else _start_pact(rng, level),
             # The crime ledger (2026-08-04): counts, day stamps and the
             # suggestion feed. Empty is a clean record, not an inert
             # layer -- every category is committable from scene one.
             "crimes": crime.new_crimes(),
             # Nothing bought at a counter yet (2026-08-11).
             "services": {},
             # Settlements the party has stood in -- teleport (rank 3)
             # reaches only KNOWN ground (Magic & Mind).
             "visited": [start["key"]]}
    if has_trait(ally, "needs meds"):
        ally.last_dose_day = state["clock"].day
    state["purse"].gold += career_purse(level) + joining_gold(ally)
    kit_log: list[str] = []
    auto_potions(state["party"], kit_log)    # the opening kit, shared out
    save(state)
    print(f"New game (seed={args.seed}, level {level}"
          f"{'' if args.level is not None else ' -- rolled'}).")
    print(f"You are {pc.name}, a magic user.")
    for line in character_sheet(pc):
        print("  " + line)
    pc_career = career_line(pc)
    if pc_career:
        print("  " + pc_career)
    cap = party_capacity(pc.cha)
    print(f"  presence: CHA {pc.cha} -- the party can hold {cap} "
          f"companion(s).")
    print(f"{ally.name} has walked at {pc.name}'s side for years:")
    for line in character_sheet(ally):
        print("  " + line)
    ally_career = career_line(ally)
    if ally_career:
        print("  " + ally_career)
    for line in career_log:
        print(line.strip())
    if state["purse"].gold:
        print(f"The party purse holds {state['purse'].gold}g.")
    for line in kit_log:
        print(line.strip())
    print(f"The party stands at {location_line(state)} -- the local jobs "
          f"are `board`; the wider world is `map` and `travel`.")
    for line in opening_hook(state):
        print(line)
    # The waves gate on PARTY LEVEL, so a career start is already past
    # wave 1's rung and the war's first word is due at the next settlement
    # stop -- worth saying plainly, since the line used to promise level 2.
    war = (f"its first word finds a level-{story.WAVE_LEVELS[0]} party in "
           f"a settlement" if level < story.WAVE_LEVELS[0] else
           "its first word is already due -- it finds the party at the "
           "next settlement stop")
    print(f"(The story layer is armed: a war is seeded in this world and "
          f"{war}. DM: see dm.md, The war.)")
    if state.get("pact"):
        due = pending_pin(state["pact"], level)
        when = ("the first assignment finds the party at a settlement now"
                if due else
                f"the next assignment lands at level "
                f"{coming_pin(state['pact'])}")
        print(f"(THE PACT rides this save: {pc.name} is a low-ranking "
              f"employee of Hell -- dm.md, The dark path. Hell's work is "
              f"pinned to the odd levels, so {when}; `task` shows the "
              f"ledger. `new --no-pact` is the neutral game.)")


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
            kind, members = make_pair(rng, level, used_names=used,
                                      homeland=here["land"])
        else:
            kind, members = None, [make_character(rng, level,
                                                  homeland=here["land"],
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
    auto_potions(party, log)    # a new hand brings their own vials in
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
    place = current_area(state)["name"]
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
    auto_potions(party, log)    # their potions walked out with them
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
    """Once per night slept, wherever it was -- the morning's bookkeeping.
    (1) The 'needs meds' drain: a
    companion whose last dose is older than MEDS_INTERVAL_DAYS loses 1
    satisfaction per night until a dose is bought (`buy HERO meds`, capitals
    only). (2) The QUARTERMASTER PASS, DEAL ONLY: the night just changed the
    stock (the kit scrounge, the alchemist's batch), so the party shares its
    potions out before the day starts -- but nobody DRINKS at the morning
    fire. The night heals for free and the vial is worth more unopened; the
    fight's end is where the pass drinks (rpg.auto_potions). Called last in
    every night path, after the rest and the brew."""
    clock = state["clock"]
    for h in state["party"][1:]:
        if h.dead or not satisfaction_tracked(h):
            continue
        if (has_trait(h, "needs meds")
                and clock.day - h.last_dose_day > MEDS_INTERVAL_DAYS):
            adjust_satisfaction(h, -1, log, "out of their medicine")
    # (3) The CONVALESCENCE drain (slice 3b): an untended wound costs morale
    # every day it goes untended, and a maiming costs a lump once. A long
    # recovery is meant to be felt in the party, not only on the sheet.
    wound_morale(state["party"], log)
    auto_potions(state["party"], log)


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
    place = current_area(state)["name"]
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
    # A quitter walks off with the potions in their pack: what is left is
    # shared out among the ones who stayed (the quartermaster pass).
    auto_potions(party, log)


def cmd_status(args: argparse.Namespace) -> None:
    state = load()
    party, clock, purse = state["party"], state["clock"], state["purse"]
    print(f"Day {clock.day}. Purse: {purse.gold}g. "
          f"At: {location_line(state)}.")
    pc = party[0] if party else None
    if pc is not None and pc.cha:
        companions = sum(1 for h in party[1:] if not h.dead)
        print(f"  Party: {companions}/{party_capacity(pc.cha)} companion "
              f"slot(s) filled (CHA {pc.cha}).")
    # `status` is where the DIGITS live (slice 3b keeps them here on
    # purpose: the played displays band HP into a state word, the hero
    # block spells out the ceiling the wounds have set).
    for h in party:
        for line in hero_block_lines(party, h):
            print(line)
    if local_recruits(state):
        print("  Candidates wait at the tavern -- `recruit` shows them.")
    world = state.get("world")
    if world:
        day = state["clock"].day
        open_q = sum(board_forecast(world, s, day)
                     for s in settlements(world))
        print(f"  Board: {open_q} open quest(s) across "
              f"{len(settlements(world))} settlement(s) -- see `board`.")
    qid = state.get("active_quest")
    if qid and world and qid in world["quests"]:
        q = world["quests"][qid]
        if q["status"] in ("failed", "expired"):
            print(f"  Active quest [{qid}] {q['name']} is LOST -- its "
                  f"window closed. Take a new one.")
        elif q["status"] == "lost":
            print(f"  Active quest [{qid}] {q['name']} is DONE, NEVER "
                  f"PAID -- the window closed on the road home. The "
                  f"banked pay stands; take a new one.")
        elif q["status"] == "done":
            print(f"  Active quest [{qid}] {q['name']} is COMPLETE -- "
                  f"take a new one.")
        elif q["status"] == "work_done":
            g = q.get("giver")
            origin = world["areas"].get(q.get("origin"), {})
            print(f"  Active quest [{qid}] {q['name']}: THE WORK IS DONE "
                  f"-- return to {g['name'] if g else 'the giver'} at "
                  f"{origin.get('name', q.get('origin'))} and "
                  f"`turnin {qid}` for the gold and the lump.")
        elif q.get("kind") == "delivery":
            print(f"  Active quest: [{qid}] DELIVERY {q['name']} -- carry "
                  f"{q['cargo']} to {q['dest_name']} "
                  f"(`travel {q['dest']}`; arriving is the turn-in).")
        elif q.get("proof_pending"):
            print(f"  Active quest [{qid}] {q['name']}: the field is "
                  f"cleared, but THE TARGET ESCAPED and the job still "
                  f"wants {q['proof']}. No rooms are left to fight -- "
                  f"`pursue` while the trail is warm, or find them again "
                  f"later.")
        else:
            cur = q["next"]
            s = quest_sites(world, q)[cur["site"]]
            rooms = site_rooms(world, s)
            print(f"  Active quest: [{qid}] L{q['level']} {q['name']} -- "
                  f"next: {s['name']} (L{s['level']}), room "
                  f"{cur['room'] + 1}/{len(rooms)}. Fight it with `room`.")
        note = deadline_note(q, state["clock"].day)
        if note and q["status"] in ("open", "work_done"):
            print(f"    (due day {q['deadline_day']} -- {note}; "
                  f"{quest_band(q, state['clock'].day)} pay)")
    k = state.get("karma")
    if k and (k.get("sin_total") or k.get("penance_total")):
        print(f"  Sin: "
              f"{karma.karma_line(k, party_level(state), clock.day)} "
              f"(lifetime sin {k['sin_total']} / penance "
              f"{k['penance_total']}; see `sin`).")
    holdings = state.get("holdings") or {}
    if holdings and world:
        due = conquest.tribute_pending(world, holdings, clock.day)
        floor = min(karma.HEAT_CAP, conquest.heat_floor(len(holdings)))
        print(f"  Holdings: {len(holdings)} under the flag -- heat floor "
              f"{floor}" + (f", {due}g tribute waiting" if due else "")
              + " (see `holdings`).")
    for line in pact_lines(state):
        print("  " + line)
    if state.get("sighting"):
        s = state["sighting"]
        print(f"  Sighted (day {s['day']}): {s['line']} -- `engage` to fight "
              f"it; any move lets it drift on.")
    for (site, room), rec in sorted(state.get("rooms", {}).items()):
        standing = sum(1 for f in rec["foes"] if not f.dead)
        print(f"  Unfinished: {site} room {room} -- {standing} foe(s) still "
              f"hold it (fled day {rec['day']})")
    ends = [r for r in state.get("loose_ends") or []
            if r.get("resolved_day") is None and loose_end_survivors(r)]
    if ends:
        more = (f" (+{len(ends) - 1} more on the books)"
                if len(ends) > 1 else "")
        print(f"  Loose end {loose_end_line(ends[0], clock.day)}{more}")
    if state.get("pending"):
        print()
        print_pause_menu(state)


def print_pause_menu(state: dict) -> None:
    """The DM-facing pause menu: who tripped it, the board, and every option
    with its real cost -- presented, like `levelup`, instead of paraphrased."""
    pending = state["pending"]
    party = state["party"]
    fate_pause = pending.get("pause_kind") == "fate"
    what = {"stamina": "is nearly out of breath",
            "wounds": "is badly cut up",
            "fate": "was spared by Fate"}
    trips = "; ".join(f"{name} {what[kind]}"
                      for kind, name in pending["crossings"])
    print(f"*** FIGHT PAUSED (after round {pending['round']}): {trips}. ***")
    if fate_pause:
        print("  (Fate's bargain spends the encounter's ONE pause; "
              "only fight on or retreat)")
        print("  (the price -- one companion -- is owed either way; "
              "breaking off pays it at the door)")
    else:
        print("  (the encounter's ONE pause -- after this it runs to its end, "
              "the party acting on its standing orders)")
    standing = [f for f in pending["foes"] if f.alive]
    print("  Facing: " + ", ".join(
        f"{f.name} ({f.hp}/{f.max_hp} HP)" for f in standing))
    for h in party:
        if h.dead:
            continue
        tag = " [DOWN]" if h.down else ""
        # The pause is a DM-facing menu, so it keeps the digits AND adds the
        # state word: the retreat decision is priced on both.
        print(f"  {h.name.split()[0]}{tag}: {h.hp_state} "
              f"HP {h.hp}/{h.hp_ceiling}"
              + (f" (max {h.max_hp})" if h.wounds else "")
              + f" STA {h.cur_sta}/{h.sta} Power {h.cur_power}/{h.power}")
        pens = []
        if h.wound_penalty:
            # "hurt", not "wounds" (slice 3b): this is the HP-derived spiral,
            # the FAST channel. The named located records print below it, and
            # the two must not read as the same number.
            pens.append(f"hurt -{h.wound_penalty}")
        if h.spent:
            pens.append(f"Spent -{SPENT_PENALTY}")
        elif h.winded:
            pens.append(f"Winded -{WINDED_PENALTY}")
        if pens:
            print(f"    ({', '.join(pens)} to rolls)")
        # The tick is priced into the retreat decision: a bleeding hero
        # loses HP every round the fight goes on, whatever else happens.
        for ctag in condition_tags(h):
            print(f"    [{ctag}]")
        # ...and so are the wounds already recorded: they are what the party
        # walks out of this room carrying whatever it decides now.
        for wtag in wound_tags(h):
            print(f"    - {wtag}")
        print(f"    healing x{h.items.get('healing', 0)}, "
              f"stamina x{h.items.get('stamina', 0)}")
    if fate_pause:
        print("  The player's call:")
    else:
        print("  The player's call (a pause action "
              f"costs the round: defend at -{PAUSE_ACTION_DEF_PENALTY}):")

    def option(cmd: str, desc: str) -> None:
        # One option per block: the command on its own line, its cost on
        # an indented one -- nothing wraps mid-flag at 40 columns.
        print(f"    {cmd}")
        print(f"      {desc}")

    option("resume", "fight on")
    if not fate_pause:
        option("resume --drink HERO",
               f"stamina draught, +{STAMINA_DRAUGHT_RESTORE} STA now")
        option("resume --heal HERO",
               f"healing potion, +{HEALING_POTION_RESTORE} HP now "
               f"(the wound penalty lightens)")
        if any(not h.dead and "berserk" in h.abilities for h in party):
            option("resume --berserk HERO",
                   f"{BERSERK_HP_COST} HP -> +{BERSERK_STA_GAIN} STA "
                   f"(the wound penalty deepens; knowers only)")
        if any(not h.dead and "war_breath" in h.abilities for h in party):
            option("resume --warbreath HERO",
                   f"{WAR_BREATH_POWER_COST} Power -> "
                   f"+{WAR_BREATH_STA_GAIN} STA (knowers only)")
        if any(not h.dead and h.spell_rank("invisibility") >= 2
               for h in party):
            option("resume --vanish HERO",
                   f"{VANISH_POWER_COST} Power: fade from the melee "
                   f"(untargetable; the next strike lands as an ambush)")
    blinker = next((h for h in party
                    if not h.dead and h.spell_rank("teleport") >= 2), None)
    option("retreat",
           "parting blows from foes still fit to swing, then one group "
           "chase roll"
           + (" (the dead do not pursue past their ground)"
              if any(f.alive and not f.pursues for f in pending["foes"])
              else ""))
    if blinker is not None:
        option(f"retreat --blink {blinker.name.split()[0]}",
               f"teleport out: NO parting blows, no chase "
               f"({TELEPORT_ESCAPE_COST} Power; a fizzled door falls "
               f"back to the honest retreat)")
    smoker = next((h for h in party
                   if not h.dead and h.items.get("smoke", 0) > 0), None)
    if smoker is not None:
        option(f"retreat --smoke {smoker.name.split()[0]}",
               f"smoke vial: NO parting blows, but the chase still rolls "
               f"({smoker.items['smoke']} left)")


def print_levelup_menu(heroes: list) -> None:
    """The spending menu: what each hero's banked skill points can buy right
    now, with costs and effects -- printed automatically for the PC on every
    level-up (finish_encounter), instead of the DM paraphrasing the rules
    from memory.

    2026-07-28 display pass: one standardized row shape per buy --
    `* item                cost` with the cost in a right-hand column and a
    one-line brief under it (Ability.brief / Move.brief) -- in fixed
    sections each headed by its command. Every item is at most two
    40-column lines, so the whole menu scans on the phone."""
    shown_one = False
    for h in heroes:
        if h.dead:
            continue
        first = h.name.split()[0]

        def row(label: str, cost, brief: str = "",
                afford: bool | None = None) -> None:
            if afford is None:
                afford = isinstance(cost, int) and h.skill_points >= cost
            print(f"{'*' if afford else ' '} {label:<33}{str(cost):>4}")
            if brief:
                print(f"    {brief}")

        if shown_one:
            print("")
        shown_one = True
        print(f"{h.name} -- L{h.level}, {h.skill_points} point(s) banked, "
              f"XP {h.xp}/{xp_to_next(h.level)} to L{h.level + 1}")
        print("(* = buyable now; costs in points)")
        # Sink 1: the pools (the old automatic growth, on the menu now).
        print(f"POOLS -- train {first} hp|sta|power")
        bought = ", ".join(f"{k} +{h.pool_bought.get(k, 0)}"
                           for k in POOL_KINDS)
        row(f"+1 max HP/STA/Power (cap +{POOL_BUY_CAP})", "1 ea",
            f"bought {bought}", afford=h.skill_points >= 1)
        # Sink 2: combat training (+1 to ALL pressure rolls per rank).
        print(f"TRAINING -- train {first} combat")
        if h.training >= TRAINING_MAX:
            row(f"combat rank {h.training}", "CAP")
        else:
            row(f"combat rank {h.training} -> {h.training + 1}",
                training_cost(h.training),
                f"+1 to every pressure roll (cap {TRAINING_MAX})")
        # Sink 2 (casters): SPELL ranks -- the real offense and tricks of
        # anyone who knows one (the weapon is the out-of-Power fallback).
        if h.spells:
            print(f"SPELLS -- train {first} SPELL")
            for name, rank in sorted(h.spells.items()):
                spell = SPELLS[name]
                if rank >= spell.max_rank:
                    row(f"{name} rank {rank}", "CAP")
                else:
                    row(f"{name} rank {rank} -> {rank + 1}", rank + 1,
                        f"next: {spell.ranks[rank]}")
            if h.is_wizard:
                print(f"  (new spells: a spellbook teaches one --"
                      f" {SPELLBOOK_PRICE}g in a capital, buy {first} "
                      f"book SPELL)")
        # Sink 3: proficiency with the WIELDED weapon.
        print(f"WEAPON -- train {first} weapon")
        if h.weapon is None or h.weapon_broken:
            print("  (no whole weapon in hand to drill)")
        else:
            rank = h.proficiency.get(prof_name(h.weapon), 0)
            if rank >= PROFICIENCY_MAX:
                row(f"{prof_name(h.weapon)} rank {rank}", "CAP")
            else:
                row(f"{prof_name(h.weapon)} rank {rank} -> {rank + 1}",
                    rank + 1, "+1 atk & sev; drops on switch")
        dormant = ", ".join(f"{n} {r}" for n, r in sorted(h.proficiency.items())
                            if r and (h.weapon is None
                                      or n != prof_name(h.weapon)))
        if dormant:
            print(f"  (drilled, not in hand: {dormant})")
        # Sink 7: alchemy (session C -- the brew skill; brew at camp, once
        # per long rest, off MIND). Open to all.
        print(f"ALCHEMY -- train {first} alchemy")
        if h.alchemy >= ALCHEMY_MAX:
            row(f"alchemy rank {h.alchemy}", "CAP",
                f"batch {ALCHEMY_BATCH[h.alchemy]}, stock cap "
                f"{brew_stock_cap(h)}")
        else:
            nxt = h.alchemy + 1
            unlocks = [POTION_DISPLAY[r] for r, need in
                       ALCHEMY_RECIPE_RANK.items() if need == nxt]
            brief = f"brew {ALCHEMY_BATCH[nxt]}/night, stock {nxt + 2}"
            if unlocks:
                brief += f"; +{', '.join(unlocks)}"
            row(f"alchemy rank {h.alchemy} -> {nxt}", alchemy_cost(h.alchemy),
                brief)
        # Sink 6: the warrior moves (session B -- riders on the exchange, the
        # engine fires them; repertoire capped at combat training + 1, gated
        # by the wielded weapon's move tags). Shown to EVERYONE (2026-07-19
        # fix: the menu used to hide it from wizards, which read as a class
        # gate -- the free-allocation doctrine has none; the only gates are
        # the weapon's tags and the training cap).
        cap = h.training + 1
        print(f"MOVES -- train {first} move NAME "
              f"({len(h.moves)}/{cap} known)")
        if h.moves:
            print(f"  known: {', '.join(sorted(h.moves))}")
        if len(h.moves) >= cap:
            print("  (repertoire full -- raise combat training for room)")
        else:
            learnable = [m for name, m in MOVES.items()
                         if name not in h.moves
                         and move_weapon_ok(name, h.weapon)]
            for m in learnable:
                row(m.name, m.cost, m.brief or m.blurb)
            if not learnable and h.weapon is not None:
                print(f"  (none fit the {h.weapon.name})")
        # Sink 5: the ability catalog (single buys -- learn HERO NAME).
        print(f"ABILITIES -- learn {first} NAME")
        known = ability_tags(h)
        if known:
            print(f"  known: {', '.join(known)}")
        for a in ABILITIES.values():
            if (a.name in h.abilities
                    or (a.requires and a.requires not in h.abilities)):
                continue
            row(a.name, a.cost, a.brief or a.blurb)


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
    At most ONE pause per encounter (designer call, 2026-07-11): an ordinary
    wounds pause or slice 4's special Fate pause spends it, so resumes pass
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
                      crime_take: dict | None = None,
                      field: int = 0, align: str = "neutral",
                      mercy: str | None = None,
                      weather: str = "",
                      pursuit: str | None = None) -> None:
    """Shared tail of every encounter command: run the melee -- which may
    PAUSE once, at the fight's first wounds crossing or at Fate's bargain
    (see play_orders) -- then award and
    persist. On a pause the fight is saved as `pending` and the turn goes
    back to the player (resume / retreat next message). `quest` ties the
    encounter to a board quest: clearing the room advances its cursor.
    `field` is the fight's opening gap (ranged combat: ROOM_FIELD indoors,
    the engagement's outcome in the wilds) -- persisted with a paused
    fight so the resume stands on the same ground, and `weather` rides
    beside it for the same reason (a storm the fight opened in is still
    blowing when the player resumes it). `mercy` ("law"/"hell")
    marks a POSSE fight: an eligible loss uses its authored mercy.
    `pursuit` names the loose-end record this fight re-opened (`pursue`,
    2026-08-08): the fight's end settles the record either way."""
    party, rng = state["party"], state["rng"]
    living = [h for h in party if not h.dead]
    dead_before = [h.name for h in party if h.dead]    # so the post-fight
                                                       # morale pass knows
                                                       # who died in THIS one
    fired: set[tuple[str, Entity]] = set()
    pause = group_combat(living, foes, rng, log, pause_triggers=True,
                         fired=fired, standing_orders=play_orders(False),
                         field=field, weather=weather)
    if pause is not None:
        state["pending"] = {
            "foes": foes, "xp": encounter_xp, "site": site, "room": room,
            "quest": quest, "crime": crime_take, "pursuit": pursuit,
            "fired": fired, "round": pause.round,
            "crossings": [(k, h.name) for k, h in pause.crossings],
            "dead_before": dead_before,
            "field": field,
            "weather": weather,
            "align": align,
            "mercy": mercy,
            "pause_kind": pause.kind,
            # Fate's special interrupt consumes the same one-pause budget.
            "normal_pause_used": True,
        }
        print_combat(log)
        print()
        print_pause_menu(state)
        save(state)
        return
    finish_encounter(state, log, foes, encounter_xp, site=site, room=room,
                     quest=quest, crime_take=crime_take,
                     dead_before=dead_before, align=align, mercy=mercy,
                     pursuit=pursuit)


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
                           party_level(state), state["clock"].day)


def collect_weapon_quirks(state: dict, log: list[str]) -> None:
    """Drain what the on-kill weapon quirks accrued this fight (the engine
    only counts -- rpg.py's quirk_gold/quirk_karma): Midas gold lands in
    the purse, dark-pact kills land on the karma ledger. Idempotent (the
    counters zero on collection), so the fight-end and retreat paths can
    both call it."""
    purse = state["purse"]
    day = state["clock"].day
    for h in state["party"]:
        wname = h.weapon.name if h.weapon is not None else "weapon"
        if h.quirk_gold:
            purse.gold += h.quirk_gold
            log.append(f"    The {wname} pays out its kills: "
                       f"+{h.quirk_gold}g (purse {purse.gold}g).")
            h.quirk_gold = 0
        if h.quirk_karma:
            k = state["karma"]
            k["sin"] += h.quirk_karma
            k["sin_total"] += h.quirk_karma
            log.append(f"    (the {wname} drinks its kills: "
                       f"+{h.quirk_karma} sin -- "
                       f"{karma.karma_line(k, party_level(state), day)})")
            h.quirk_karma = 0


SETTLEMENT_RUMOR_CAP = 4    # failure rumors a settlement remembers


def _remember_failure(settlement: dict, quest: dict, day: int) -> None:
    """Leave a day-stamped rumor behind: what happened because nobody took
    the job. The party hears it next time it asks around here."""
    rumors = settlement.setdefault("rumors", [])
    rumors.append({"day": day, "name": quest["name"],
                   "text": failure_line(quest)})
    del rumors[:-SETTLEMENT_RUMOR_CAP]


def take_failure_rumors(settlement: dict) -> list[dict]:
    """Read and clear a settlement's failure rumors (they are news once)."""
    rumors = settlement.get("rumors") or []
    settlement["rumors"] = []
    return rumors


def _lose_paid_window(state: dict, quest: dict) -> list[str]:
    """The lost-after-work-done path (2026-08-08, the turn-in stage): the
    window closed before the party returned. The turn-in tranche and the
    gold are gone, the banked 80% stays, NO failure rumor fires (the
    monsters are dead -- the world changed), place states stay completed,
    and the record reads done, never paid. The giver's grievance is story
    material, not a penalty."""
    day = state["clock"].day
    qid = quest["id"]
    quest["status"] = "lost"
    quest["lost_day"] = day
    accepted = state.get("accepted") or []
    if qid in accepted:
        accepted.remove(qid)
    if state.get("active_quest") == qid:
        state["active_quest"] = None
    origin = state["world"]["areas"].get(quest.get("origin"))
    if origin is not None and qid in origin.get("quests", ()):
        origin["quests"].remove(qid)
    remember(state,
             f"[{qid}] {quest['name']} (L{quest['level']}) -- done, "
             f"never paid: the window closed before the party returned.",
             kind="quest", note=quest.get("epilogue", ""))
    return [
        f"  *** JOB DONE, NEVER PAID: {quest['name']} ***",
        f"  The window closed on day "
        f"{quest['deadline_day'] + QUEST_GRACE_DAYS} with the work done "
        f"and the pay uncollected. What the fighting and the field "
        f"already paid is kept; the gold and the turn-in lump are gone.",
    ]


def board_clock(state: dict) -> list[str]:
    """Run the quest board's clock (2026-07-26, the attrition rework's slice
    2). Two jobs, in order:

    1. **The taken job's window closes wherever the party is standing.** Past
       the deadline plus QUEST_GRACE_DAYS the quest is FAILED: the encounter
       pay already banked stands, the turn-in lump does not, and the giver's
       failure line lands as the epilogue. This is what makes a day cost
       something -- a week of camping is a week the job did not wait through.
       A job whose WORK is done but whose pay was never collected goes to
       LOST instead (2026-08-08, `_lose_paid_window`): done, never paid.
    2. **The boards WITHIN EARSHOT expire and refill.** Untaken work comes
       off at its deadline (leaving a failure rumor at the settlement that
       posted it), and each settlement posts back toward its ordinary slot
       count. Only the settlements inside `QUEST_RUMOR_DAYS` of where the
       party stands are run (2026-08-15, Local Quest Geography -- it used to
       be the whole current LAND, which is now a whole country): a board
       nobody can hear costs nothing to leave alone, and its first look
       fills it up (quests.py). An INACTIVE board refills to nothing and
       still receives whatever the world forces onto it.

    Called at every day advance (travel, explore, camp, tavern, downtime) and
    on `board`. Returns the notices the caller prints."""
    world = state.get("world")
    if not world:
        return []
    day, rng = state["clock"].day, state["rng"]
    # The world's own day, rolled here because this is where the calendar
    # advances (2026-08-07, the world layer): every land's clock catches up
    # to today -- cards expire, decks are drawn on need, states flip. Silent
    # by design; what the party HEARS is `world_news`, at the points news
    # lands. The whole world moves together so a relation never reads a
    # land that is behind the calendar.
    worldsim.roll_world(world, day)
    notices: list[str] = []
    accepted = state.setdefault("accepted", [])
    taken = set(accepted)
    active = state.get("active_quest")
    if active:
        taken.add(active)
    for qid in sorted(taken):
        quest = world["quests"].get(qid)
        if quest is None or quest["status"] not in ("open", "work_done"):
            continue
        if quest.get("hell_task"):
            # Hell work is never LOST off the clock: a blown window
            # resumes the collections ladder instead (maybe_enforce),
            # and a very late turn-in still resolves the pact -- it
            # just pays the expired band (2026-08-03).
            continue
        if not quest_expired(quest, day, taken=True):
            continue
        if quest["status"] == "work_done":
            notices.extend(_lose_paid_window(state, quest))
            continue
        quest["status"] = "failed"
        quest["failed_day"] = day
        if qid in accepted:
            accepted.remove(qid)
        if state.get("active_quest") == qid:
            state["active_quest"] = None
        # The giver's row comes off the board, but no RUMOR is left: the
        # party was the one carrying this job and hears its epilogue here
        # and now, not as gossip on the next visit.
        origin = world["areas"].get(quest.get("origin"))
        if origin is not None and qid in origin.get("quests", ()):
            origin["quests"].remove(qid)
        notices.append(f"  *** JOB LOST: {quest['name']} ***")
        notices.append(f"  The window closed on day "
                       f"{quest['deadline_day'] + QUEST_GRACE_DAYS}. "
                       f"No turn-in, no lump -- what the fighting already "
                       f"paid is kept.")
        notices.append(f"  EPILOGUE (day {day}): {failure_line(quest)}")
        remember(state, f"[{qid}] {quest['name']} (L{quest['level']}) "
                        f"-- LOST, the window closed.",
                 kind="quest", note=failure_line(quest))
    # The party is always SOMEWHERE once a world exists (`_area_position`
    # is the only writer), so this reads the Tile straight rather than
    # tolerating a position that worldgen cannot produce.
    local = [s for s, _days
             in nearby_settlements(world, state["position"]["tile"])]
    if not local:
        return notices
    # The name namespace is the names IN USE, recomputed -- not a ledger of
    # every giver the world ever had. With the board churning (~660 postings
    # a career) a persisted list would outgrow the homeland name pools inside a
    # single playthrough; a giver whose job lapsed forty days ago is free to
    # be reused.
    used = {n["name"] for n in world.get("npcs", ())}
    used |= {q["giver"]["name"] for q in world["quests"].values()
             if q.get("giver")}
    used |= {h.name for h in state["party"]}
    for settlement in local:
        for gone in expire_settlement_board(world, settlement, day, taken):
            _remember_failure(settlement, gone, day)
        refresh_settlement_board(world, settlement, day, rng, used)
    refresh_deliveries(world, day, rng, used, origins=local)
    return notices


def print_board_clock(state: dict) -> None:
    """The day-advance path: run the clock and print whatever it cost."""
    notices = board_clock(state)
    if notices:
        print("\n".join(notices))


def advance_quest(state: dict, log: list[str], qid: str) -> None:
    """The active quest's cleared room: move the cursor. Finishing the last
    room of a place moves on to the next place; finishing the LAST place
    fires the work-done stage (_close_site) -- unless the job wants PROOF
    and somebody from the final site is still breathing (2026-08-08): the
    field is cleared and paid, but the quest sits UNFINISHED until the
    target is killed -- a warm `pursue`, or a re-encounter the DM stages
    off the loose end (_maybe_finish_proof lifts the gate)."""
    quest = state["world"]["quests"][qid]
    cur = quest["next"]
    site = quest_sites(state["world"], quest)[cur["site"]]
    cur["room"] += 1
    if cur["room"] < len(site_rooms(state["world"], site)):
        return
    if (quest.get("proof") and cur["site"] == len(quest["sites"]) - 1
            and _final_site_loose_ends(state, qid)):
        quest["proof_pending"] = True
        log_banner(log,
                   f"  *** THE TARGET ESCAPED -- proof wanted: "
                   f"{quest['proof']}. The job is not done until they "
                   f"are dead. ***",
                   ["*** THE TARGET ESCAPED --",
                    f"proof wanted: {quest['proof']}.",
                    "The job is not done until",
                    "they are dead. ***"])
        return
    _close_site(state, log, qid)


def _close_site(state: dict, log: list[str], qid: str,
                pay_mult: float = 1.0, note: str = "") -> None:
    """Close the active quest's CURRENT place: move the cursor on, and if it
    was the LAST place, fire the WORK-DONE stage (2026-08-08, the turn-in
    rework): the banner says the job is done and names the giver, the world
    changes now (complete_quest_place_state -- the pass reopens when the
    deed is done, not when it is paid), and the FIELD tranche of the XP
    lands, unbanded. The gold, the turn-in tranche, the CHA negotiation,
    the reward weapon and the epilogue wait where the giver stands
    (`turnin QID`). advance_quest's tail, split out (2026-07-19) so a deed
    done clean and a settled twist can close a place without walking its
    rooms.

    The EXEMPT kinds still pay whole here -- the turn-in stage is for
    HONEST work with a giver (board quests and forged good quests): WAR
    WAVES have no clock, the giver is a ruler mid-war, and wave 3's
    scripted fall makes the return scene impossible by design; CONQUEST
    garrison jobs have no giver -- the town is the pay; HELL assignments
    and dark quests pay at work-done (hell verifies its own work and the
    purse arrives by infernal delivery -- narrate the receipt; a settled
    twist is a hand-off on the spot by definition). DELIVERIES never come
    this way at all: the hand-off at the destination is their turn-in
    (deliver_if_arrived).

    `pay_mult` is the caper paths' fraction (a settled twist), and rides
    under the band as before. A place cleared by rout carries its tag on
    the banner: driven off, not slain."""
    quest = state["world"]["quests"][qid]
    party, purse = state["party"], state["purse"]
    cur = quest["next"]
    sites = quest_sites(state["world"], quest)
    site = sites[cur["site"]]
    n_sites = len(quest["sites"])
    last_site = cur["site"] == n_sites - 1
    pays_here = (quest.get("story_wave") is not None
                 or quest.get("conquest")
                 or quest.get("hell_task")
                 or quest.get("align") == "dark")
    if site.get("routed"):
        # The display never prints "the giants are dead" against a log
        # that says otherwise.
        note = f"{note}; driven off, not slain" if note \
            else "driven off, not slain"
    day = state["clock"].day
    enc = quest.get("encounters", 1)
    # A multi-site quest names its position (site 1/2) in the banner so a
    # SITE CLEARED never reads as the whole job done (2026-07-19).
    pos = f" (site {cur['site'] + 1}/{n_sites})" if n_sites > 1 else ""
    tag = f" ({note})" if note else ""
    if last_site and pays_here:
        banner = "QUEST COMPLETE" + tag
        # The clock's band rides ON TOP of the caper fraction (2026-07-26):
        # what the job is worth is what it is worth ON THE DAY it is handed
        # over. The per-encounter shares were paid as they were earned and
        # are never clawed back.
        band = quest_band(quest, day)
        pay_mult *= QUEST_PAY_BANDS[band]
        clear_xp = round((quest_clear_xp(quest["level"], enc)
                          + quest_turnin_xp(quest["level"], enc))
                         * pay_mult)
        gold = round(quest_gold_posted(quest) * pay_mult)
        award_quest(party, purse, gold, clear_xp, log,
                    f"{quest['name']} -- {site['name']}{pos}", banner=banner)
        record_karma(state, clear_xp, quest.get("align", "good"), log)
        rw = quest.get("reward_weapon")
        if rw:
            # The weapon-reward mode (2026-07-28): the turn-in lump IS the
            # weapon (the posting carried gold_total 0). It waits with the
            # giver until a hand takes it up.
            state["pending_reward"] = dict(rw)
            log_banner(log,
                       f"  The pay is the {rw['name']} itself -- "
                       f"`claim HERO` takes it up.",
                       [f"The pay is the {rw['name']} --",
                        "`claim HERO` takes it up."])
        if quest.get("deadline_day") is not None and band != "on time":
            log_banner(log,
                       f"  (turned in {band.upper()} -- day {day} against a "
                       f"deadline of day {quest['deadline_day']}: "
                       f"x{QUEST_PAY_BANDS[band]:g} on the turn-in)",
                       [f"({band.upper()} turn-in: day {day},",
                        f"due day {quest['deadline_day']} --",
                        f"x{QUEST_PAY_BANDS[band]:g} on the lump)"])
    elif last_site:
        # The work-done stage: the deed is done in the field; the pay
        # waits with the giver. The FIELD tranche lands now, unbanded --
        # only the turn-in tranche and the gold are ever banded or lost.
        banner = "THE JOB IS DONE" + tag
        origin = state["world"]["areas"].get(quest["origin"])
        g = quest.get("giver")
        who = f"{g['name']}" if g else "the giver"
        where = origin["name"] if origin else quest["origin"]
        due = (f" -- due day {quest['deadline_day']}"
               if quest.get("deadline_day") is not None else "")
        log.append("")
        log_banner(log,
                   f"  *** {banner}: {quest['name']} -- "
                   f"{site['name']}{pos}. Return to {who} at "
                   f"{where}{due}: `turnin {qid}`. ***",
                   [f"*** {banner}:", f"{quest['name']} --",
                    f"{site['name']}{pos}.",
                    f"Return to {who}",
                    f"at {where}{due}:",
                    f"`turnin {qid}`. ***"])
        field_xp = round(quest_clear_xp(quest["level"], enc) * pay_mult)
        award_xp(party, field_xp, log, "the work done")
        record_karma(state, field_xp, quest.get("align", "good"), log)
    else:
        banner = "SITE CLEARED" + tag
        log_banner(log,
                   f"  *** {banner}: {site['name']}{pos} -- "
                   f"the job goes on. ***",
                   [f"*** {banner} ***", f"{site['name']}{pos} --",
                    "the job goes on."])
    cur["site"] += 1
    cur["room"] = 0
    if last_site and not pays_here:
        # The world changes NOW -- the pass reopens when the deed is done,
        # not when it is paid. The epilogue and the history record wait
        # for the giver's scene (cmd_turnin).
        quest["status"] = "work_done"
        quest["work_done_day"] = day
        complete_quest_place_state(state["world"], quest, day=day)
        return
    if last_site:
        quest["status"] = "done"
        quest["done_day"] = state["clock"].day
        complete_quest_place_state(state["world"], quest,
                                   day=state["clock"].day)
        g = quest.get("giver")
        if g:
            log_banner(log,
                       f"  (turn in to {g['name']}, {g['role']} -- "
                       f"narrate the scene)",
                       ["(turn in to", f"{g['name']}, {g['role']} --",
                        "narrate the scene)"])
        if quest.get("epilogue"):
            log.append(f"  EPILOGUE (day {state['clock'].day}): "
                       f"{quest['epilogue']}")
        # The campaign record (session C): one day-stamped line per job,
        # carrying the epilogue that closed it.
        dark = " [DARK]" if quest.get("align") == "dark" else ""
        remember(state,
                 f"[{qid}] {quest['name']} (L{quest['level']}){dark} "
                 f"-- done.",
                 kind="quest", note=quest.get("epilogue", ""))
        if quest.get("story_wave") is not None and state.get("story"):
            remember(state, f"THE WAR: wave {quest['story_wave'] + 1} "
                            f"broken -- {quest['name']}.")
            for line in story.on_wave_done(state["story"], quest,
                                           state["clock"].day):
                log.append("  " + line)
                # The scripted fall and the war's end are the two lines
                # the record must carry (story.py authors both).
                remember(state, line.strip("* ").rstrip())
        ckey = quest.get("conquest")
        if ckey:
            # The garrison is broken: the tag flips (conquest.py). The
            # strongbox was the quest's gold; tribute starts today.
            holdings = state.setdefault("holdings", {})
            remember(state, f"CONQUEST: "
                            f"{state['world']['areas'][ckey]['name']} "
                            f"falls under the party's flag.")
            for line in conquest.take_settlement(
                    state["world"], holdings, state["world"]["areas"][ckey],
                    state["clock"].day):
                log.append("  " + line)
        pact = state.get("pact")
        if pact and quest.get("hell_task") and pact.get("task") == qid:
            # The assignment is done: the account closes clean and the
            # curriculum ledger ticks. Hell's next job waits for the next
            # PIN (2026-08-04) -- unless one was crossed while this was
            # open, in which case it lands at the next settlement stop.
            pact["task"] = None
            pact["warned"] = False
            pact["done"] = pact.get("done", 0) + 1
            remember(state, f"HELL'S ASSIGNMENT {pact['done']} served: "
                            f"{quest['name']}.")
            pin = coming_pin(pact)
            when = (f"The next is pinned to PC level {pin}."
                    if pin is not None else "Hell has no more work pinned.")
            log.append(f"  (THE ASSIGNMENT IS DONE -- hell is pleased; "
                       f"the ledger reads {pact['done']} completed. "
                       f"{when})")
    else:
        nxt = sites[cur["site"]]
        nxt["known"] = True
        state["position"]["site"] = None
        state["position"]["room"] = None
        log.append(f"  (next: {nxt['name']}, L{nxt['level']}, "
                   f"{len(site_rooms(state['world'], nxt))} encounter(s))")


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
    day = state["clock"].day
    band = quest_band(q, day)
    mult = QUEST_PAY_BANDS[band]
    award_quest(state["party"], state["purse"], round(q["gold"] * mult),
                round(q["xp"] * mult), log,
                q["name"], banner="DELIVERY COMPLETE")
    record_karma(state, round(q["xp"] * mult), q.get("align", "good"), log)
    if q.get("deadline_day") is not None and band != "on time":
        log.append(f"  (delivered {band.upper()} -- day {day} against a "
                   f"deadline of day {q['deadline_day']}: x{mult:g})")
    q["status"] = "done"
    q["done_day"] = state["clock"].day
    r = q.get("recipient")
    if r:
        log.append(f"  (hand {q['cargo']} to the recipient -- narrate the "
                   f"scene: {npc_line(r)})")
    if q.get("epilogue"):
        log.append(f"  EPILOGUE (day {state['clock'].day}): {q['epilogue']}")
    remember(state, f"[{q['id']}] DELIVERY {q['name']} -- {q['cargo']} "
                    f"carried to {q['dest_name']}.",
             kind="quest", note=q.get("epilogue", ""))
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
# Conquest -- the player's domain layer (2026-07-27, conquest.py)
# --------------------------------------------------------------------------- #

def held_here(state: dict) -> dict | None:
    """The local settlement when it flies the party's flag, else None."""
    here = local_settlement(state)
    if here is not None and here["key"] in (state.get("holdings") or {}):
        return here
    return None


def holding_board_line(settlement: dict) -> str:
    return (f"{settlement['name']} flies the party's flag -- the guilds "
            f"post no honest work for their conqueror. Crime and the "
            f"pact serve instead; the tavern, the shops, and the hiring "
            f"keep your custom.")


def effective_heat(state: dict) -> int:
    """Heat with the domain layer's floor folded in: holding land is
    standing wickedness, so the flag alone keeps the law coming (one step
    per holding, the same HEAT_CAP). Zero holdings = karma.heat exactly."""
    k = state.get("karma") or karma.new_karma()
    derived = karma.heat(k, party_level(state), state["clock"].day)
    floor = conquest.heat_floor(len(state.get("holdings") or {}))
    return min(karma.HEAT_CAP, max(derived, floor))


def conquest_news(state: dict) -> None:
    """The domain layer's day-settling, run where news lands (arrivals,
    settlement nights, the board): the yoke's seizures, the crown's raids
    on holdings the party is away from, and the tribute chests when the
    party stands in a holding. Prints directly; every call site saves
    afterward (or hands off to machinery that does)."""
    holdings = state.get("holdings")
    if not holdings:
        return
    world = state["world"]
    day = state["clock"].day
    held_before = set(holdings)
    lines = conquest.seize_by_occupation(world, holdings,
                                         state.get("story"))
    here = local_settlement(state)
    here_key = here["key"] if here is not None else None
    lines += conquest.roll_raids(world, holdings, state["rng"], day,
                                 skip_key=here_key)
    # A holding lost is history whichever way it went (the crown's raid
    # or the aggressor's yoke) -- the flag came down, that is the record.
    for key in sorted(held_before - set(holdings)):
        area = world["areas"].get(key) or {}
        remember(state, f"HOLDING LOST: {area.get('name', key)} is out "
                        f"of the party's hands.")
    if here_key is not None and here_key in holdings:
        gold = conquest.collect_tribute(world, holdings, day)
        if gold:
            state["purse"].gold += gold
            lines.append(f"TRIBUTE: {gold}g collected -- the stewards "
                         f"bring every holding's chest to the flag.")
    if lines:
        print("\n".join(lines))


# --------------------------------------------------------------------------- #
# The world layer (2026-08-07 -- worldsim.py, the worldsim build's frame)
# --------------------------------------------------------------------------- #

def sky_here(state: dict) -> str:
    """Today's weather word over the land the party stands in, with the world
    brought up to today first so it is TODAY's sky and not the one it had
    when the party last looked. "" when there is no world yet."""
    world = state.get("world")
    if not world or not state.get("position"):
        return ""
    worldsim.roll_world(world, state["clock"].day)
    return worldsim.weather_of(world, state["position"]["land"])


def exposure_sky(state: dict) -> str:
    """The sky a night is PAID for, which is not always the sky overhead: a
    mill town under SMOG charges the same lungs a rainy hillside does, and a
    roof is no answer to it (rpg.INDOOR_SKY).

    Rolled up to today first, like `sky_here` -- and it is `travel`'s night
    loop that makes it matter, since `long_rest` advances the day inside the
    loop. Without the roll every night of a four-day leg was charged the
    DEPARTURE day's weather: one storm at the gate meant four exposure
    checks in it, four cabin rolls and four nights of storm morale."""
    world = state.get("world")
    if not world or not state.get("position"):
        return ""
    worldsim.roll_world(world, state["clock"].day)
    polity = state["position"]["land"]
    if "smog" in worldsim.state_ids(world, polity):
        return "smog"
    return worldsim.weather_of(world, polity)


def fight_sky(state: dict) -> str:
    """The weather THIS fight is fought in -- the storm's field penalties
    (rpg.group_combat's `weather`). Outdoors only: a room, a cellar or a
    barrow has no sky in it, and the party is under one exactly when it is
    not standing inside a site."""
    if (state.get("position") or {}).get("site"):
        return ""
    return sky_here(state)


def weather_note(state: dict) -> None:
    """The one line the party reads about the sky, where the sky matters --
    setting out, a day afield, a night in the open. `map` and `world` carry
    it as state; this is the SIGHT."""
    world = state.get("world")
    if not world or not state.get("position"):
        return
    worldsim.roll_world(world, state["clock"].day)
    line = worldsim.weather_line(world, state["position"]["land"])
    if line:
        print(f"  {line}")


def shelter_here(state: dict, log) -> dict | None:
    """A storm night in the wilds rolls for a roof, and what the roof HOLDS
    is worldsim's cabin table -- the storm's real content, since the penalty
    is only ever the thing that drives you to the door.

    Logs what the party SEES plus the DM's own line: the sinister row would
    be no scene at all if the display gave it away, so the player-facing
    half never does (the quest twist's rule, applied to a camp)."""
    found = worldsim.shelter_roll(state["rng"])
    if found is None:
        return None
    log_banner(log, f"  SHELTER: {found['sight']}",
               ["SHELTER:"] + found["sight"].split())
    log_banner(log, f"  (DM eyes only: {found['dm']})",
               f"(DM eyes only: {found['dm']})".split())
    return found


def local_term(state: dict, name: str) -> float:
    """What the land the party stands in is doing to one priced term today
    (2026-08-09, the economy floor's PRICED MENU). 1.0 -- the catalog price,
    untouched -- when there is no world, no position, or nothing happening,
    so every shop call can ask without checking first.

    The world is rolled up to today first: a price is a thing you are quoted
    now, not a thing that was true when the party last looked."""
    world = state.get("world")
    if not world or not state.get("position"):
        return 1.0
    worldsim.roll_world(world, state["clock"].day)
    return worldsim.term(world, state["position"]["land"], name)


def price_note(state: dict) -> None:
    """The one line a shop prints when the world has moved its prices --
    silence when it has not. The SIGHT half of the priced menu; `prices`
    carries the whole sheet."""
    world = state.get("world")
    if not world or not state.get("position"):
        return
    lines = worldsim.menu_lines(world, state["position"]["land"])
    if lines:
        print("\n".join(lines))


def world_news(state: dict) -> None:
    """What the land the party stands in has heard since it last listened.
    Runs where news lands -- arrivals, settlement nights, the board, beside
    conquest's own word from the holdings -- and tells each line ONCE.

    Word travels within a land (the board's rumor rule): another land's
    cards are heard by going there, or through the states its edges derive
    here (`map`, `world`). A long absence is summarized, not scrolled."""
    world = state.get("world")
    if not world or not state.get("position"):
        return
    worldsim.roll_world(world, state["clock"].day)
    lines = worldsim.take_news(world, state["position"]["land"],
                               state["clock"].day)
    if lines:
        print("\n".join(lines))


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
    of it is sin -- cutting down the law is itself a crime; that
    ratchet is the design. Returns True when a fight ran (the encounter
    machinery has printed and saved)."""
    k = state.get("karma")
    living = [h for h in state["party"] if not h.dead]
    if not k or not living or state.get("pending"):
        return False
    lvl = party_level(state)
    h = effective_heat(state)   # karma's meter, floored by holdings (the
                                # flag is standing wickedness -- conquest.py)
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
    land = state["position"]["land"]
    used = {n["name"] for n in state["world"].get("npcs", [])}
    kinds, skins, leader, label = karma.build_posse(
        posse_level, land_homeland(state["world"], land), rng,
                                                    used_names=used)
    k["last_leader"] = f"{leader['name']}, {leader['role']}"
    here = local_settlement(state)
    where = (f"at {here['name']}'s gates" if here is not None
             else "at the party's fire")
    print(f"*** THE RECKONING -- day {day}: word of the party's deeds "
          f"has caught up ({karma.karma_line(k, lvl, day)}). ***")
    if karma.heat(k, lvl, day) < h:
        print(f"  (the flag draws them: {len(state.get('holdings') or {})} "
              f"holding(s) keep the heat floor at {h})")
    print(f"  {label} find the party {where}, led by {npc_line(leader)}")
    print(f"  (no parley in v1 -- they mean to collect; retreat is the "
          f"peaceful option. Losing is not death: the law leaves the "
          f"PC for dead -- party, purse, and sin all forfeit)")
    log = new_combat_log()
    open_fight(state["party"], log)
    log_banner(log,
               f"=== The reckoning: {label} "
               f"(a level-{posse_level} posse) ===",
               ["=== The reckoning:", f"{label} ===",
                f"(a level-{posse_level} posse)"])
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
                      field=field, align="dark", mercy="law",
                      weather=fight_sky(state))
    return True


# --------------------------------------------------------------------------- #
# The hell pact (2026-07-19, the dark-quests session; the PINNED ladder
# 2026-08-04 -- karma.py, rules.md)
# --------------------------------------------------------------------------- #

def pc_level(state: dict) -> int:
    """The PROTAGONIST's level -- what hell's pins are read against
    (party_level is the party's best living level, the yardstick for
    threat; the curriculum is the PC's own)."""
    party = state.get("party") or []
    return party[0].level if party else 1


def pending_pin(pact: dict, level: int) -> int | None:
    """The highest TASK_PIN_LEVELS pin the PC has reached that hell has
    not served, or None. Pins NEVER stack into a queue: several crossed
    while an account was open (or while the party was in the wilds) are
    served as ONE assignment, at the highest of them."""
    served = pact.get("last_pin_served", 0)
    crossed = [p for p in karma.TASK_PIN_LEVELS if served < p <= level]
    return crossed[-1] if crossed else None


def coming_pin(pact: dict) -> int | None:
    """The next pin hell is waiting on (readouts), or None once the ten
    are all served."""
    served = pact.get("last_pin_served", 0)
    return next((p for p in karma.TASK_PIN_LEVELS if p > served), None)


def pact_task(state: dict) -> dict | None:
    """The current assignment's quest, or None (also self-heals a stale
    pointer: a done/withdrawn task clears the slot)."""
    pact = state.get("pact")
    if not pact or not pact.get("task"):
        return None
    q = state["world"]["quests"].get(pact["task"]) if state.get("world") \
        else None
    if q is None or q["status"] == "done":
        pact["task"] = None
        return None
    return q


def pact_lines(state: dict) -> list[str]:
    """The pact's readout lines (status and `task` share them)."""
    pact = state.get("pact")
    if not pact:
        return []
    day = state["clock"].day
    lines = []
    q = pact_task(state)
    if q is not None:
        s = _settlement_by_key(state["world"], q["origin"])
        where = s["name"] if s else q["origin"]
        taken = (q["id"] in (state.get("accepted") or [])
                 or state.get("active_quest") == q["id"])
        bribed = day < pact.get("bribed_until", 0)
        if taken:
            deadline = q.get("deadline_day")
            if deadline is not None and day > deadline and not bribed:
                state_word = "PAST DUE -- collections are coming"
            elif deadline is not None:
                state_word = f"taken; hell wants it by day {deadline}"
            else:
                state_word = "taken"
        else:
            due = pact["assigned_day"] + karma.TASK_GRACE_DAYS
            state_word = ("PAST DUE -- collections are coming"
                          if day > due and not bribed
                          else f"grace to take it runs to day {due}")
        if pact.get("warned") and "PAST DUE" in state_word:
            state_word += " (the warning was given)"
        lines.append(f"THE PACT: assignment [{q['id']}] {q['name']} at "
                     f"{where} ({state_word}).")
    elif day < pact.get("bribed_until", 0):
        lines.append(f"THE PACT: hell eased off until day "
                     f"{pact['bribed_until']} (bribed).")
    else:
        due = pending_pin(pact, pc_level(state))
        nxt = coming_pin(pact)
        if due is not None:
            when = (f"the level-{due} pin is due -- it lands at the next "
                    f"settlement")
        elif nxt is not None:
            when = f"the next is pinned to PC level {nxt}"
        else:
            when = "hell's ten pinned jobs are all served"
        lines.append(f"THE PACT: no current assignment ({when}).")
    if pact.get("done"):
        lines.append(f"  ({pact['done']} assignment(s) completed -- "
                     f"the curriculum ledger; see `task`)")
    return lines


def maybe_assign_task(state: dict) -> bool:
    """Hell's PINNED ladder (2026-08-04): an ASSIGNMENT finds the party at
    a settlement whenever the PC has crossed a `TASK_PIN_LEVELS` pin hell
    has not served -- the odd levels, ten a career, the war waves' shape.
    Never while one is open, never while a bribe holds, never in an
    occupied town. Assignments stay strictly SERIAL and never stack: pins
    crossed while an account was open are served as ONE fresh job at the
    first settlement stop after it closes, stamped at the highest crossed
    pin (`last_pin_served`). The template comes off the pact's shuffled
    DECK (karma.deal_card); the quest is levelled at the PARTY with the
    margin of error running upward (TASK_SPREAD), flagged `hell_task`,
    and delivered by unseen job board / black-waxed letter / ember-eyed
    courier (karma.HELL_MAIL). Prints the WORD FROM BELOW block; the
    caller saves. Returns True when one landed."""
    pact = state.get("pact")
    living = [h for h in state["party"] if not h.dead]
    if not pact or not living or state.get("pending"):
        return False
    if pact.get("task"):
        return False
    day = state["clock"].day
    if day < pact.get("bribed_until", 0):
        return False
    pin = pending_pin(pact, pc_level(state))
    if pin is None:
        return False
    here = local_settlement(state)
    if here is None or occupied_here(state) is not None:
        return False
    world, rng = state["world"], state["rng"]
    used = {n["name"] for n in world.get("npcs", [])}
    used |= {q["giver"]["name"] for q in world["quests"].values()
             if q.get("giver")}
    lvl = party_level(state)
    tpl = karma.deal_card(pact, lvl, rng)
    q = karma.roll_dark_quest(world, here, lvl, rng, used_names=used,
                              spread=karma.TASK_SPREAD, template=tpl)
    q["hell_task"] = True
    pact["task"] = q["id"]
    pact["assigned_day"] = day
    pact["last_pin_served"] = pin
    pact["warned"] = False
    how = rng.choice(karma.HELL_MAIL)
    print(f"*** WORD FROM BELOW -- day {day}: {how}. ***")
    print(f"  Hell assigns: {quest_line(q)}")
    g = q.get("giver")
    if g:
        print(f"  (the local hand on the job: {npc_line(g)})")
    print(f"  (the level-{pin} pin -- hell's work comes at the odd "
          f"levels, ten in a career)")
    print(f"  `take {q['id']}` within ~{karma.TASK_GRACE_DAYS} days works "
          f"it -- taking it sets the completion clock and hell waits on "
          f"the road. Left untaken past the grace it goes PAST DUE: one "
          f"warning, then one collections visit, and then hell writes the "
          f"job off. `bribe` (~{karma.BRIBE_GOLD_PER_LEVEL} g x level) "
          f"buys {karma.BRIBE_DAYS} days of quiet; `task` shows the "
          f"ledger.")
    return True


def maybe_enforce(state: dict) -> bool:
    """Past Due -- ONE collections visit (reshaped 2026-08-04, was the
    escalating ladder). Checked at the same stops as the law's posses
    (arrivals and nights), never stacked on a stop that already fought.
    When enforcement fires at all:

    - An UNTAKEN assignment is eligible past its grace
      (TASK_GRACE_DAYS from the day it landed).
    - A TAKEN one is eligible only past its stamped completion window
      (`deadline_day`, set by `take`) -- a party working the job in its
      window is left alone; that is the whole point of taking it.

    The shape: the FIRST visit of a refusal is a WARNING -- a clerk, a
    letter, no fight -- fired at the first eligible stop (no chance
    roll: informing is the point). Then ONE armed visit on the usual
    cooldown + chance, at PARTY LEVEL + a rolled ENFORCE_SPREAD (0..+2):
    potentially devastating, never dominating, and it breaks when beaten
    (retreat stays viable -- the roll is the danger, not
    relentlessness). However that visit RESOLVES -- won, lost, or fled;
    hell's point is made either way -- the account CLOSES
    (`close_hell_account`): the job is written off, `defied` ticks, and
    nothing more comes until the next pin. LOSING keeps hell's shipped
    lesson (apply_mercy: the purse taken as a fine, the job withdrawn) --
    the same closure. Their XP is NEUTRAL -- cutting down devils is
    neither crime nor penance, and farming them for absolution would be
    a hole.

    The budget behind the shape (plan.md, THE DARK REWORK): ten pins x
    one visit is ~0.5 punishment fights per level, against a levelling
    budget of 2-3 fights per level. A chain of three came to 1.6/level
    -- a third of a campaign spent on a layer the player opted out of."""
    pact = state.get("pact")
    living = [h for h in state["party"] if not h.dead]
    if not pact or not living or state.get("pending"):
        return False
    q = pact_task(state)
    if q is None:
        return False
    day = state["clock"].day
    taken = (q["id"] in (state.get("accepted") or [])
             or state.get("active_quest") == q["id"])
    if taken:
        deadline = q.get("deadline_day")
        if deadline is None or day <= deadline:
            return False
    elif day <= pact["assigned_day"] + karma.TASK_GRACE_DAYS:
        return False
    if day < pact.get("bribed_until", 0):
        return False
    if day < pact.get("last_enforce_day", -99) + karma.ENFORCE_COOLDOWN_DAYS:
        return False
    rng = state["rng"]
    if not pact.get("warned"):
        # The warning rung: one scene, no fight, no chance roll. The
        # final-notice date is the cooldown's end -- after it, steel.
        pact["warned"] = True
        pact["last_enforce_day"] = day
        print(f"*** PAST DUE -- day {day}: [{q['id']}] {q['name']} is "
              f"owed and hell has noticed. ***")
        print(f"  A clerk from Hell finds the party. He has three forms "
              f"and no weapon. The forms name the job, the day it was "
              f"due, and the word COLLECTIONS.")
        print(f"  (final notice: from day "
              f"{day + karma.ENFORCE_COOLDOWN_DAYS} collections come "
              f"armed, ONCE -- and whatever that visit costs, hell then "
              f"writes the job off. `take {q['id']}` / finishing the job "
              f"or `bribe` (~{karma.BRIBE_GOLD_PER_LEVEL} g x level) are "
              f"the ways out)")
        save(state)     # the fight branches persist via resolve_encounter;
        return True     # the warning must persist itself
    if rng.random() >= karma.ENFORCE_CHANCE:
        return False
    pact["last_enforce_day"] = day
    lvl = party_level(state)
    # ONE visit, its level rolled: party +0..+2. The roll is where the
    # devastation lives -- a +2 collections posse on a party that just
    # levelled is a real fight -- and it never comes back.
    posse_level = min(karma.LEVEL_CAP,
                      lvl + rng.randint(*karma.ENFORCE_SPREAD))
    ferocity = FEROCITY_BREAKS
    land = state["position"]["land"]
    used = {n["name"] for n in state["world"].get("npcs", [])}
    kinds, skins, leader, label = karma.build_hell_posse(
        posse_level, land_homeland(state["world"], land), rng,
        used_names=used)
    here = local_settlement(state)
    where = (f"at {here['name']}" if here is not None
             else "at the party's fire")
    print(f"*** PAST DUE -- day {day}: collections on "
          f"[{q['id']}] {q['name']}. ***")
    print(f"  {label} find the party {where}, led by {npc_line(leader)}")
    print(f"  (this is the ONE visit: however it ends -- won, lost, or "
          f"run from -- hell writes the job off afterwards. Lose and it "
          f"collects its fine first.)")
    log = new_combat_log()
    open_fight(state["party"], log)
    log_banner(log,
               f"=== Past Due: {label} "
               f"(a level-{posse_level} posse) ===",
               ["=== Past Due:", f"{label} ===",
                f"(a level-{posse_level} posse)"])
    foes = []
    for kind in kinds:
        state["foe_count"] += 1
        foes.append(make_foe(kind, state["foe_count"], rng,
                             display=skins.get(kind),
                             ferocity=ferocity))
    foes[-1].name = leader["name"]
    for line in roster_lines(foes):
        log.append("  " + line)
    field = 0 if here is not None else WILD_FIELD
    resolve_encounter(state, log, foes, wild_encounter_xp(posse_level),
                      field=field, align="neutral", mercy="hell",
                      weather=fight_sky(state))
    return True


def withdraw_assignment(state: dict) -> str:
    """Pull the current assignment out of the world: the quest is
    withdrawn (its Sites released back to the land), the pointer and the
    warning cleared, and hell's WRITE-OFF ledger (`defied`) ticks.
    Returns '[qid] Name' for the scene, or '' when no assignment stood.
    Shared by the two ways an account closes -- the write-off after the
    collections visit and hell's mercy on a lost one."""
    pact = state.get("pact")
    if not pact or not pact.get("task"):
        return ""
    qid = pact["task"]
    world = state["world"]
    q = world["quests"].get(qid)
    label = ""
    if q is not None:
        label = f"[{qid}] {q['name']}"
        release_quest_places(world, q)
        del world["quests"][qid]
    if state.get("active_quest") == qid:
        state["active_quest"] = None
    accepted = state.get("accepted") or []
    if qid in accepted:
        accepted.remove(qid)
    pact["task"] = None
    pact["warned"] = False
    pact["defied"] = pact.get("defied", 0) + 1
    remember(state, f"WRITTEN OFF: {label} -- hell closed the account "
                    f"(write-off {pact['defied']}).")
    return label


def close_hell_account(state: dict, log: list) -> None:
    """The collections visit RESOLVED (2026-08-04) -- won, lost, or fled;
    hell's point is made either way. The account closes here: the
    assignment is written off, the ledger remembers, and hell is quiet
    until the next pin. Accounts never stack and never jam a later pin
    behind a refused job."""
    label = withdraw_assignment(state)
    if not label:
        return
    pact = state["pact"]
    pin = coming_pin(pact)
    nxt = (f"The next comes at PC level {pin}." if pin is not None
           else "Hell has no more work pinned.")
    log_banner(log,
               f"  *** WRITTEN OFF: {label}. The account is closed; "
               f"hell's ledger remembers. {nxt} ***",
               ["*** WRITTEN OFF ***", f"{label}",
                "The account is closed; hell's",
                "ledger remembers.", nxt])


def apply_mercy(state: dict, foes: list, mercy: str | None, log: list,
                participants: list | None = None) -> bool:
    """Apply Slice 4's one-mercy-per-character-level rule before
    `party_wiped` finishes the Down.

    Ordinary rosters derive their consequence from ferocity through
    `rpg.apply_defeat_mercy`. Posse fights keep their authored LAW/HELL
    reshaping, but now spend the same level mercy: a second genuine loss at
    that level is GAME OVER. The encounter tail skips this function entirely
    for any fight that paid Fate's bargain -- won or lost."""
    party = state["party"]
    pc = party[0] if party else None
    if pc is None or not party_defeated(party):
        return False

    if mercy not in ("law", "hell"):
        fired = apply_defeat_mercy(
            party, foes, state["purse"], state["rng"], log,
            participants=participants,
        )
        if fired:
            state["pending"] = None
            remember(state, f"DEFEAT at L{pc.level}: the party went down "
                            f"and lived -- a {fired} roster took its "
                            f"price. The level's one mercy is spent.")
        return fired is not None

    if not mercy_available(pc):
        return False
    day = state["clock"].day
    pc.mercy_level = pc.level
    pc.dead = False
    pc.down = False
    pc.withdrew = False
    pc.hp = min(1, pc.hp_ceiling)
    lost = [h.name for h in party[1:]]
    state["party"] = [pc]
    fine = state["purse"].gold
    state["purse"].gold = 0
    state["pending"] = None

    def emit(parts: list[str]) -> None:
        for line in fit_lines(parts):
            log.append(line)

    if mercy == "law":
        k = state["karma"]
        burned = k["sin"]
        k["sin"] = 0
        emit(["*** LEFT FOR DEAD --", f"day {day}.",
              "The heroes think the PC dead. ***"])
        if lost:
            emit(["The party is lost:"])
            emit([name + "." for name in lost])
        emit([f"The purse is forfeit: {fine} g gone."])
        if burned:
            emit([f"The ledger is settled: {burned}",
                  "sin cleared. Heat 0."])
        emit([f"{pc.name} wakes in a ditch at 1 HP.",
              "Everyone in hell is laughing."])
        remember(state, f"LEFT FOR DEAD by the law at L{pc.level}: "
                        f"{fine}g and {len(lost)} companion(s) gone, "
                        f"{burned} sin cleared.")
    else:
        # Hell's mercy IS the account closing (2026-08-04): the fine, the
        # withdrawal, the write-off -- the same closure the visit gets
        # when it is won or run from, bought with the purse instead.
        label = withdraw_assignment(state)
        emit(["*** THE LESSON --", f"day {day}.",
              "Hell's enforcers leave the PC alive. ***"])
        if lost:
            emit(["The party is lost:"])
            emit([name + "." for name in lost])
        emit([f"The purse is collected: {fine} g."])
        if label:
            emit([f"{label} is WITHDRAWN --",
                  "the account is written off."])
        emit([f"{pc.name} wakes at 1 HP.",
              "The sin remains."])
        remember(state, f"THE LESSON at L{pc.level}: hell's collectors "
                        f"took {fine}g and {len(lost)} companion(s). "
                        f"The sin remains.")
    return True


def cmd_task(args: argparse.Namespace) -> None:
    """The pact's ledger: the current assignment (and its grace clock),
    the bribe window, the pin schedule, the lifetime counts."""
    state = load()
    pact = state.get("pact")
    if not pact:
        print("No pact rides this save (a `new --no-pact` game) -- the "
              "party answers to nobody below.")
        return
    for line in pact_lines(state):
        print(line)
    q = pact_task(state)
    if q is not None:
        for line in quest_detail_lines(state["world"], q, dm=False):
            print(line)
        print(f"(left untaken past its grace -- or taken and past its "
              f"window -- it goes PAST DUE: one warning, then ONE armed "
              f"collections visit at a road or a night (cooldown "
              f"{karma.ENFORCE_COOLDOWN_DAYS} d, level party +0..+2). "
              f"However that visit ends, hell then writes the job off "
              f"and waits for the next pin. Taking it and working the "
              f"window keeps hell off the road; `bribe` buys "
              f"{karma.BRIBE_DAYS} days of quiet.)")
    pins = ", ".join(str(p) for p in karma.TASK_PIN_LEVELS)
    print(f"The pins (PC levels): {pins} -- ten jobs a career, dealt off "
          f"a shuffled deck of the occult ten.")
    print(f"Lifetime: {pact.get('done', 0)} assignment(s) completed; "
          f"{pact.get('defied', 0)} written off after collections.")


def cmd_bribe(args: argparse.Namespace) -> None:
    """Grease hell's local hand: BRIBE_GOLD_PER_LEVEL x party level buys
    BRIBE_DAYS of no new assignments and no enforcement. An open
    assignment isn't cancelled -- its clock restarts when the coin runs
    out (the grace runs fresh from the bribe's end)."""
    state = load()
    if not require_no_pending(state):
        return
    pact = state.get("pact")
    if not pact:
        print("No pact rides this save -- nobody below to bribe.")
        return
    purse, day = state["purse"], state["clock"].day
    cost = karma.BRIBE_GOLD_PER_LEVEL * party_level(state)
    if purse.gold < cost:
        print(f"Hell's ease costs {cost} g (30 x party level); the purse "
              f"holds {purse.gold} g. No discount. There is never a "
              f"discount.")
        return
    purse.gold -= cost
    until = max(day, pact.get("bribed_until", day)) + karma.BRIBE_DAYS
    pact["bribed_until"] = until
    if pact.get("task"):
        # The clock restarts when the coin runs out: the grace window
        # reopens at the bribe's end, so the ease is real -- and Past Due
        # resets with it (the coin buys fresh patience, warning and all;
        # 2026-08-03).
        pact["assigned_day"] = until
        pact["warned"] = False
        q = pact_task(state)
        if q is not None and q.get("deadline_day") is not None \
                and q["id"] in (state.get("accepted") or []):
            # A TAKEN job's window restarts fresh from the bribe's end
            # (mirroring the untaken grace) -- ease that leaves the
            # deadline already blown would be no ease.
            window = q.get("window",
                           q["deadline_day"] - q.get("posted_day", day))
            q["posted_day"] = until
            q["deadline_day"] = until + window
    save(state)
    print(f"{cost} g changes hands in the wrong tavern corner. Hell is "
          f"EASED until day {until}: no new assignments, no enforcers."
          + (f" The open assignment waits -- its grace runs fresh from "
             f"day {until}." if pact.get("task") else ""))
    print(f"The party purse holds {purse.gold} g.")


# --------------------------------------------------------------------------- #
# Crime -- free actions against a leveled world (2026-08-04, THE DARK
# REWORK's session B; crime.py holds the bands, the catalogue and every
# knob, rules.md's Crime add-on the played rules, dm.md the table manner)
# --------------------------------------------------------------------------- #
# Crime is not a job anyone hands out and not a posting anyone reads: the
# PC does the thing because they want to and keeps what follows. Two
# commands carry the whole layer -- `case` reads the local mark for free,
# `crime` commits against it -- and everything difficult about a crime is
# the MARK's level, never a gate.


def crimes_state(state: dict) -> dict:
    """The `crimes` save ledger, made on demand (a save that never
    committed a crime carries an empty one)."""
    rec = state.get("crimes")
    if not rec:
        rec = crime.new_crimes()
        state["crimes"] = rec
    return rec


def place_kind(state: dict) -> str:
    """Which crime market the party stands in: a settlement's subtype, or
    the wilds (where the road work lives)."""
    here = local_settlement(state)
    return settlement_tier(here) if here is not None else "wilds"


def place_id(state: dict) -> str:
    """The mark seed's place component -- the settlement key, or the area
    the party is crossing. Stable, so casing and committing agree."""
    here = local_settlement(state)
    if here is not None:
        return here["key"]
    return str(_area_position(current_area(state)).get("area")
               or state["position"].get("area") or "the road")


def world_seed(state: dict) -> int | None:
    return (state.get("world") or {}).get("seed")


def crime_news(state: dict) -> None:
    """Hand out whatever suggestions hell owes and announce them. Unlocks
    gate SUGGESTIONS, never permission (decision 8): this is advertising,
    and every category is committable from day one whether or not it has
    ever been advertised."""
    if not state.get("pact"):
        return
    fresh = crime.refresh_unlocks(crimes_state(state), state["karma"],
                                  state["pact"], state["rng"])
    if not fresh:
        return
    print("*** A SUGGESTION FROM BELOW ***")
    for c in fresh:
        print(f"  {c['name']} -- {c['line']} (`case {c['key']}`)")


def local_mark(state: dict, cat: dict, npc: str | None,
               level: int | None) -> dict | None:
    """The mark this category has where the party stands -- or the NAMED
    victim the DM assigned. None means the crime has no mark here."""
    day = state["clock"].day
    if npc:
        return crime.npc_mark(cat, world_seed(state), npc,
                              level or party_level(state), day)
    # The world layer's own corner of the mark table (2026-08-11): a state
    # that makes a NEW kind of mark exist here deals its faces in beside the
    # band's -- the reagent consignment, the opened tomb, the masked house.
    world, roles = state.get("world"), ()
    if world and state.get("position"):
        worldsim.roll_world(world, day)
        roles = worldsim.mark_roles(world, state["position"]["land"],
                                    cat["key"])
    return crime.roll_mark(cat, world_seed(state), place_id(state),
                           place_kind(state), day, roles)


def no_mark_line(state: dict, cat: dict) -> str:
    """Why this crime has nobody to do it to here -- the two reasons read
    differently, and the player should not have to guess which it is."""
    kind = place_kind(state)
    tail = " (`--npc NAME --level N` names a victim anywhere.)"
    if kind not in crime.where_of(cat):
        return (f"{cat['name']} does not happen at a {kind} -- it wants "
                f"{', '.join(crime.where_of(cat))}." + tail)
    bands = ", ".join(crime.band_of(k)["label"] for k in cat["bands"])
    return (f"{cat['name']} finds no mark at a {kind}: it wants a "
            f"{bands}, and none of those live here." + tail)


def case_lines(state: dict, cat: dict, mark: dict) -> list[str]:
    """The casing report -- free, and honest: the same seed rolls the
    mark, the take and the roster that committing will face."""
    rec = crime.peek(crimes_state(state), cat["key"])
    day = state["clock"].day
    mult = crime.sin_mult(rec, day)
    lines = [f"-- CASING: {cat['name']} --",
             f"  the shape: {cat['shape']}",
             f"  {cat['line']}",
             f"  the mark: {mark['role']} (L{mark['level']})",
             f"  the take: {mark['gold']}g, "
             f"{round(mark['xp'] * mult)} XP (all of it sin)",
             f"  the check: {crime.check_line(cat)}",
             f"  protection: {crime.roster_hint(mark)}",
             f"  ({cat['hint']})"]
    if mult != 1.0:
        lines.append(f"  {mult_note(rec, mult, day)}")
    return lines


def mult_note(rec: dict, mult: float, day: int) -> str:
    """Why the sin is not face value. Gold NEVER carries these -- the loot
    is the loot; it is hell that gets bored."""
    if rec.get("count", 0) == 0:
        return (f"first time: x{mult:g} on the sin and XP (the coin is "
                f"unchanged)")
    n = len(crime.recent_days(rec, day))
    return (f"hell is bored: x{mult:g} on the sin and XP -- {n} of these "
            f"in the last {crime.MONOTONY_WINDOW} days (the coin is "
            f"unchanged)")


def cmd_crimes(args: argparse.Namespace) -> None:
    """The crime PRICE SHEET (2026-08-04, session C -- the `prices`
    pattern): the whole catalogue with what each category is worth
    against the LOCAL marks, then the tally of what the party has already
    done and what hell is currently advertising.

    `case KEY` reads one mark exactly (the rolled level, the rolled
    roster); this reads the BAND, so it answers 'what is worth doing
    here' without twenty-seven casings. A pure readout: no save touched,
    and every number comes off crime.py's live knobs."""
    state = load()
    kind, day = place_kind(state), state["clock"].day
    crimes = crimes_state(state)
    print(f"-- THE CRIME SHEET, day {day}, at a {kind} --")
    print(f"  (the take is quoted at the MARK's level -- difficulty is "
          f"who you rob, never a gate; petty crime is flat and pays in "
          f"pennies. All the XP is sin.)")
    for shape in crime.SHAPES:
        here = [c for c in crime.available(kind) if c["shape"] == shape]
        if not here:
            continue
        print(f"  {shape}:")
        for c in here:
            rec = crime.peek(crimes, c["key"])
            mult = crime.sin_mult(rec, day)
            done = f" [x{rec['count']}]" if rec["count"] else ""
            tag = "" if rec["count"] or not rec["unlocked"] else " (suggested)"
            print(f"    {c['key']} -- {c['name']}{done}{tag}")
            print(f"      {take_span(c, kind, mult)}")
            print(f"      {crime.check_line(c)}")
            # `hint` IS the authored what-stands-in-the-way line; a pool
            # dump would print eight guard skins and say nothing about
            # the roster, which is built at the MARK's level anyway.
            print(f"      {c['hint']}")
    rows = crime.tally_rows(crimes)
    if rows:
        print("  -- the tally --")
        for name, count, last in rows:
            when = f", last day {last}" if last >= 0 else ""
            print(f"    {name}: {count}{when}")
    k = state.get("karma")
    if k:
        print(f"  {karma.karma_line(k, party_level(state), day)}; "
              f"lifetime sin {k.get('sin_total', 0)}")
    feed = crime.suggestions(crimes)
    if feed:
        print("  hell suggests: " + ", ".join(c["key"] for c in feed))
    print("  (`case KEY` reads today's actual mark; `crime KEY` commits. "
          "Nothing is locked -- a suggestion is advertising. The full "
          "record is ui/history.txt.)")


def take_span(cat: dict, place_kind: str, mult: float) -> str:
    """What a category is worth against the mark BAND it draws here --
    the range, not one rolled mark (`case` is the exact read). Petty is
    flat by construction, so it quotes its own constants; everything else
    is a clean function of the mark's level, so the band's ends ARE the
    span."""
    if cat["shape"] == "petty":
        coin = ("no coin" if cat["pay"] is None
                else f"{crime.PETTY_GOLD[0]}-{crime.PETTY_GOLD[1]}g")
        lo, hi = crime.PETTY_SIN
        return (f"flat: {coin}, {round(lo * mult)}-{round(hi * mult)} "
                f"sin/XP" + (f" (x{mult:g})" if mult != 1.0 else ""))
    bands = crime.bands_here(cat, place_kind)
    lo = min(b["levels"][0] for b in bands)
    hi = max(b["levels"][1] for b in bands)
    g_lo, x_lo = crime.take_of(cat, lo, random.Random(0))
    g_hi, x_hi = crime.take_of(cat, hi, random.Random(0))
    span = f"L{lo}" if lo == hi else f"L{lo}-{hi}"
    coin = "no coin" if not g_hi else (f"{g_lo}g" if g_lo == g_hi
                                       else f"{g_lo}-{g_hi}g")
    xp = (f"{round(x_lo * mult)}" if x_lo == x_hi
          else f"{round(x_lo * mult)}-{round(x_hi * mult)}")
    return (f"marks {span}: {coin}, {xp} sin/XP"
            + (f" (x{mult:g})" if mult != 1.0 else ""))


def cmd_case(args: argparse.Namespace) -> None:
    """Case a crime -- free, always. With no category it lists what has a
    mark where the party stands; with one it prints that mark's level,
    take, check and protection. Casing costs nothing and hides nothing
    (the straight-board stance): the mark is seeded per settlement, day
    and category, so committing today faces exactly what the casing
    showed, and sleeping on it rolls a new one tomorrow."""
    state = load()
    crime_news(state)
    kind, day = place_kind(state), state["clock"].day
    if not args.category:
        crimes = crimes_state(state)
        print(f"-- CRIME, day {day}, at a {kind} --")
        for shape in crime.SHAPES:
            here = [c for c in crime.available(kind) if c["shape"] == shape]
            if not here:
                continue
            print(f"  {shape}:")
            for c in here:
                rec = crime.peek(crimes, c["key"])
                if rec["count"]:
                    tag = f" (x{rec['count']})"
                elif rec["unlocked"]:
                    tag = " (suggested)"
                else:
                    tag = ""
                print(f"    {c['key']} -- {c['name']}{tag}")
        feed = crime.suggestions(crimes)
        if feed:
            print("  hell suggests: "
                  + ", ".join(c["key"] for c in feed))
        print("  (`case KEY` reads the local mark; `crime KEY` commits. "
              "Nothing is locked -- a suggestion is advertising.)")
        save(state)
        return
    cat = crime.category(args.category)
    if cat is None:
        print(f"No such crime: {args.category}. `case` lists them.")
        return
    mark = local_mark(state, cat, args.npc, args.level)
    if mark is None:
        print(no_mark_line(state, cat))
        return
    for line in case_lines(state, cat, mark):
        print(line)
    save(state)


def crime_record(state: dict, cat: dict, mark: dict) -> dict:
    """Book the commission and return the payoff record: what the take
    is worth AFTER the sin multipliers, and the note explaining it. The
    ledger is stamped HERE, when the crime is committed -- a fight that
    goes badly does not un-commit it."""
    day = state["clock"].day
    crimes = crimes_state(state)
    rec = crime.record_for(crimes, cat["key"])
    mult = crime.sin_mult(rec, day)
    note = mult_note(rec, mult, day) if mult != 1.0 else ""
    crime.stamp(crimes, cat["key"], day)
    return {"key": cat["key"], "name": cat["name"], "role": mark["role"],
            "level": mark["level"], "gold": mark["gold"],
            "xp": round(mark["xp"] * mult), "note": note}


def pay_crime(state: dict, log: list, rec: dict) -> None:
    """The take lands: gold to the purse, the lump as XP -- and every
    point of it sin, because a crime is dark work by construction."""
    if rec.get("note"):
        log.append(f"    ({rec['note']})")
    award_quest(state["party"], state["purse"], rec["gold"], rec["xp"],
                log, f"{rec['name']} -- {rec['role']}", banner="THE TAKE",
                reason="crime")
    record_karma(state, rec["xp"], "dark", log)


def crime_fight(state: dict, cat: dict, mark: dict, rec: dict,
                banner: str) -> None:
    """Send the party through the mark's protection. Ordinary people who
    object, at the MARK's level -- the engine only ever fights things that
    fight back, and the wickedness itself stays narration (dm.md). The
    crime record rides the encounter, so the take pays out when the fight
    is won (and pays nothing when it is not)."""
    party, rng = state["party"], state["rng"]
    log = new_combat_log()
    open_fight(party, log)
    log_banner(log,
               f"=== {banner}: {mark['role']} (L{mark['level']}) ===",
               [f"=== {banner}:", f"{mark['role']} (L{mark['level']}) ==="])
    foes = []
    for kind in mark["kinds"]:
        state["foe_count"] += 1
        foes.append(make_foe(kind, state["foe_count"], rng,
                             display=mark["skins"].get(kind)))
    for line in roster_lines(foes):
        log.append("  " + line)
    field = 0 if local_settlement(state) is not None else WILD_FIELD
    resolve_encounter(state, log, foes, wild_encounter_xp(mark["level"]),
                      field=field, align="dark", crime_take=rec,
                      weather=fight_sky(state))


def cmd_crime(args: argparse.Namespace) -> None:
    """Commit a crime against the local mark (or a named victim). Three
    shapes: PETTY does it or fumbles it and never fights; a DEED rolls
    2d6+stat vs its DC -- a make takes it clean, a miss botches it into
    the protection with witnesses; FORCE skips the check and goes through
    the protection to get at the take."""
    state = load()
    if not require_no_pending(state):
        return
    crime_news(state)
    cat = crime.category(args.category)
    if cat is None:
        print(f"No such crime: {args.category}. `case` lists them.")
        return
    mark = local_mark(state, cat, args.npc, args.level)
    if mark is None:
        print(no_mark_line(state, cat))
        return
    party, rng = state["party"], state["rng"]
    pc = party[0]
    pc_level_before = pc.level
    print(f"*** {cat['name'].upper()} -- {mark['role']} "
          f"(L{mark['level']}) ***")
    print(f"  {cat['line']}")

    # --- the check (petty may carry a trivial one; a deed always does) --- #
    made = True
    if cat["stat"]:
        stat = {"str": pc.str_, "dex": pc.dex, "mind": pc.mind,
                "cha": pc.cha}[cat["stat"]]
        roll = rng.randint(1, 6) + rng.randint(1, 6)
        total = roll + stat
        made = total >= cat["dc"]
        print(f"  {pc.name} rolls 2d6+{cat['stat'].upper()}: {roll}+"
              f"{stat} = {total} vs DC {cat['dc']} -- "
              f"{'CLEAN' if made else 'BOTCHED'}.")

    if cat["shape"] == "petty":
        # Petty crime never fights. A miss is simply a miss: no take, no
        # sin, no stamp -- the scene (the indignant innkeeper, the pup's
        # mother) is the DM's to narrate and `forge` if it wants dice.
        if not made:
            print("  It does not come off. Nothing taken, nothing "
                  "gained -- the scene is yours (dm.md).")
            save(state)
            return
        rec = crime_record(state, cat, mark)
        log: list[str] = []
        pay_crime(state, log, rec)
        print("\n".join(log))
        save(state)
        pc_levelup_prompt(pc, pc_level_before)
        return

    rec = crime_record(state, cat, mark)

    if cat["shape"] == "deed" and made:
        # The clean take: the whole crime in one message, no blood.
        log = ["  No alarm, no blood, no witnesses -- it is done and the "
               "party is three streets away."]
        pay_crime(state, log, rec)
        for h in party[1:]:
            if not h.dead:
                autospend_points(h, log)
        print("\n".join(log))
        save(state)
        pc_levelup_prompt(pc, pc_level_before)
        return

    if cat["shape"] == "deed":
        klog: list[str] = []
        karma.record_karma(state["karma"], crime.WITNESS_SIN, "dark",
                           klog, party_level(state), state["clock"].day)
        print(f"  {cat['hint']} -- and now they have seen the party's "
              f"faces (+{crime.WITNESS_SIN} sin). The take is "
              f"still there for whoever is standing at the end.")
        for line in klog:
            print(line)
        banner = f"{cat['name']} botched"
    else:
        print(f"  No plan, no patience: {cat['hint'].lower()}")
        banner = cat["name"]
    crime_fight(state, cat, mark, rec, banner)


def pc_levelup_prompt(pc, level_before: int) -> None:
    """Print the spending menu if the PC just crossed a level -- the same
    prompt the quest and encounter award paths end with."""
    if pc.dead or pc.level <= level_before:
        return
    print()
    print(f"*** {pc.name} reached level {pc.level} -- the spending "
          f"menu (show it to the player, dm.md): ***")
    print_levelup_menu([pc])


def cmd_settle(args: argparse.Namespace) -> None:
    """Take a TWIST's terms (the caper structure): the current site
    closes without a fight at the twist's pay fraction of its lump.
    Fighting on (`room`) is the refusal."""
    state = load()
    if not require_no_pending(state):
        return
    qid = state.get("active_quest")
    if not qid:
        print("No active quest -- nothing on the table to settle.")
        return
    quest = state["world"]["quests"][qid]
    if quest["status"] != "open" or quest.get("kind") == "delivery":
        print(f"[{qid}] {quest['name']} has no terms on the table.")
        return
    if not at_quest_site(state, quest):
        return
    cur = quest["next"]
    site = quest_sites(state["world"], quest)[cur["site"]]
    twist = site.get("twist")
    if not twist or twist.get("resolved") or cur["room"] != 0:
        print(f"[{qid}] {quest['name']}: no terms on the table at "
              f"{site['name']} -- `room` fights on.")
        return
    twist["resolved"] = True
    party = state["party"]
    pc = party[0]
    pc_level_before = pc.level
    log: list[str] = [f"THE TERMS ARE TAKEN: {twist['accept']}"]
    _close_site(state, log, qid, pay_mult=twist.get("pay", 0.5),
                note="settled")
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


# --------------------------------------------------------------------------- #
# Loose ends (2026-08-08): a rout writes a record the save keeps
# --------------------------------------------------------------------------- #

def record_loose_end(state: dict, escaped: list, log: list[str],
                     quest_id: str | None = None,
                     site_key: str | None = None,
                     room: int | None = None) -> dict:
    """Who got away, at what HP and wounds, from which fight, in which
    area, on what day -- exactly as fled party rooms keep their survivors.
    One list on the save (`loose_ends`), newest first. It is what `pursue`
    reads, what a proof quest checks, and the honest substrate for "the
    same troll, healed, back in the pass". No expiry: entries persist until
    the DM prunes them by save edit -- they are story, not bookkeeping."""
    # The id is DERIVED from the list, never counted alongside it: every
    # command is its own process, so a counter would have to ride the save
    # to mean anything, and one the DM's pruning could desynchronize. The
    # highest suffix in hand plus one is correct after any edit.
    used = [int(m.group(1)) for r in state.get("loose_ends") or []
            if (m := re.fullmatch(r"le(\d+)", r.get("id", "")))]
    n = max(used, default=0) + 1
    area = current_area(state)
    world = state.get("world") or {}
    if quest_id:
        q = world.get("quests", {}).get(quest_id)
        s = world.get("sites", {}).get(site_key)
        where = (f"{q['name']} -- {s['name']}" if q and s
                 else quest_id)
    elif site_key:
        where = site_key
    else:
        where = f"the open ground of {area['name']}"
    rec = {
        "id": f"le{n}",
        "day": state["clock"].day,
        "area": area["key"],
        "area_name": area["name"],
        "where": where,
        "quest": quest_id,
        "site": site_key,
        "room": room,
        "foes": [_entity_to_dict(f) for f in escaped],
        "pursue_tried": False,
        "resolved_day": None,
    }
    state.setdefault("loose_ends", []).insert(0, rec)
    names = ", ".join(f.name for f in escaped)
    log.append(f"  (LOOSE END {rec['id']}: {names} got away -- "
               f"`pursue` while the trail is warm: today, here, "
               f"before a night's sleep)")
    return rec


def loose_end_by_id(state: dict, rec_id: str) -> dict | None:
    for rec in state.get("loose_ends") or []:
        if rec["id"] == rec_id:
            return rec
    return None


def loose_end_survivors(rec: dict) -> list[dict]:
    return [f for f in rec["foes"] if not f.get("dead")]


def loose_end_line(rec: dict, day: int) -> str:
    """One 40-column-wrappable readout row for a loose end."""
    names = ", ".join(f"{f['name']} (L{f['level']}, "
                      f"{f['hp']}/{f['max_hp']} HP"
                      + (", wounded" if f.get("wounds") else "") + ")"
                      for f in loose_end_survivors(rec))
    if rec.get("resolved_day") is not None:
        tail = f"settled day {rec['resolved_day']}"
    elif rec.get("pursue_tried"):
        tail = "the trail is walked out"
    elif rec["day"] == day:
        tail = "the trail is WARM"
    else:
        tail = "the trail is cold"
    return (f"{rec['id']}: {names or 'nobody left'} -- fled {rec['where']} "
            f"(day {rec['day']}, {rec['area_name']}); {tail}")


def trail_warm(state: dict, rec: dict) -> bool:
    """The warm-trail gate (2026-08-08): same day as the rout, party still
    in the area. A slept night advances the day, so 'no night slept' rides
    in the same check."""
    return (rec["day"] == state["clock"].day
            and rec["area"] == (state.get("position") or {}).get("area"))


def _final_site_loose_ends(state: dict, qid: str) -> list[dict]:
    """The unresolved loose ends holding a proof quest open: escapes from
    its FINAL site with somebody still breathing. Mook sites -- every site
    before the last -- are exempt by construction."""
    quest = state["world"]["quests"][qid]
    if not quest.get("sites"):
        return []
    final = quest["sites"][-1]
    return [rec for rec in state.get("loose_ends") or []
            if rec.get("quest") == qid and rec.get("site") == final
            and rec.get("resolved_day") is None
            and loose_end_survivors(rec)]


def _maybe_finish_proof(state: dict, log: list[str], qid: str) -> None:
    """A proof quest held open by an escape completes the moment its final
    site's roster is finally dead: the gate lifts and the work-done stage
    fires (the cursor never moved past the final site)."""
    quest = state["world"]["quests"].get(qid)
    if (quest is None or not quest.get("proof_pending")
            or quest["status"] != "open"
            or _final_site_loose_ends(state, qid)):
        return
    quest.pop("proof_pending", None)
    log_banner(log,
               f"  *** PROOF TAKEN: {quest['proof']} -- the target is "
               f"dead. ***",
               ["*** PROOF TAKEN:", f"{quest['proof']} --",
                "the target is dead. ***"])
    _close_site(state, log, qid)


def _resolve_pursuit(state: dict, log: list[str], rec_id: str,
                     foes: list) -> None:
    """A won pursuit fight settles its loose end. Everyone dead: the record
    resolves, and a proof quest it was holding open completes. A SECOND
    rout: the record re-arms in place -- fresh day, fresh ground, a fresh
    warm trail (a new rout is a new attempt)."""
    rec = loose_end_by_id(state, rec_id)
    if rec is None:
        return
    day = state["clock"].day
    escaped = [f for f in foes if f.withdrew]
    if escaped:
        area = current_area(state)
        rec["day"] = day
        rec["area"] = area["key"]
        rec["area_name"] = area["name"]
        rec["foes"] = [_entity_to_dict(f) for f in escaped]
        rec["pursue_tried"] = False
        names = ", ".join(f.name for f in escaped)
        log.append(f"  (LOOSE END {rec['id']}: {names} got away AGAIN -- "
                   f"the trail is warm while the day holds)")
        return
    rec["resolved_day"] = day
    log.append(f"  (loose end {rec['id']} is settled -- nobody got away "
               f"this time)")
    if rec.get("quest"):
        _maybe_finish_proof(state, log, rec["quest"])


def finish_encounter(state: dict, log: list[str], foes: list,
                     encounter_xp: int, site: str | None = None,
                     room: int | None = None,
                     quest: str | None = None,
                     crime_take: dict | None = None,
                     dead_before: list[str] | None = None,
                     align: str = "neutral",
                     mercy: str | None = None,
                     pursuit: str | None = None) -> None:
    """The melee actually ended: defeat mercy/wipe check, awards,
    companion autolevel,
    loot, the companion morale pass, persist -- and the PC's level-up
    prints the spending menu on the spot (2026-07-13). Any genuine loss
    gets the roster's level-limited Slice 4 mercy when eligible; LAW/HELL
    posse fights keep their special consequences."""
    party, purse, rng = state["party"], state["purse"], state["rng"]
    pc = party[0] if party else None
    pc_level_before = pc.level if pc else 0
    state["pending"] = None
    participants = [h for h in party if h.name not in (dead_before or [])]
    # A fight that paid Fate never also spends slice 4's mercy: the spare WAS
    # the reprieve, and a companion already paid for it. True on a paid loss
    # as well as a paid victory. The marker is consumed before saving.
    fate_paid = any(h.fate_paid for h in party)
    for h in party:
        h.fate_paid = False
    mercy_fired = (
        False if fate_paid
        else apply_mercy(state, foes, mercy, log, participants=participants)
    )
    if mercy_fired:
        append_tally(state, log)
        print_combat(log)
        save(state)
        return

    wiped = party_wiped(party, log)
    if not wiped and any(f.alive for f in foes):
        # Unresolved (the fight staggered apart, both sides spent): no award.
        log_banner(log,
                   "  The encounter is not cleared -- the foes still stand.",
                   ["The encounter is not cleared --",
                    "the foes still stand."])
        if site is not None:
            # A site room keeps its survivors (same rule as a retreat) --
            # re-running the room faces them again, not a fresh spawn.
            state.setdefault("rooms", {})[(site, room)] = {
                "foes": foes, "day": state["clock"].day}
            standing = sum(1 for f in foes if f.alive)
            log_banner(log,
                       f"  ({site} room {room} is left to its {standing} "
                       f"standing foe(s) -- it will remember)",
                       [f"({site} room {room} is left to its",
                        f"{standing} standing foe(s) --",
                        "it will remember)"])
    elif not wiped:
        award_xp(party, encounter_xp, log, "encounter")
        record_karma(state, encounter_xp, align, log)
        roll_loot(party, purse, rng, log)
        weapons_left = fallen_weapons_line(foes)
        if weapons_left:
            log.append(weapons_left)
        # A field cleared by rout leaves its record (2026-08-08): the loose
        # end, and a `routed` mark on the site so its banner says driven
        # off, not slain. A won PURSUIT settles its record instead --
        # `pursue`'s own catch never writes a second entry.
        escaped = [f for f in foes if f.withdrew]
        if pursuit is not None:
            _resolve_pursuit(state, log, pursuit, foes)
        elif escaped:
            world = state.get("world")
            wsite = (world["sites"].get(site)
                     if world and site is not None else None)
            if wsite is not None:
                wsite["routed"] = True
            record_loose_end(state, escaped, log, quest_id=quest,
                             site_key=site, room=room)
        if quest is not None:
            advance_quest(state, log, quest)
        elif site is not None:
            pay_set_site_clear(state, log, site, room)
        elif crime_take is not None:
            # The protection is down, so the take is the party's (the
            # crime layer, 2026-08-04). A LOST fight pays nothing, and
            # neither does a retreat: this branch only runs on a clean
            # win.
            pay_crime(state, log, crime_take)

    if not wiped:
        # Named kills (session C): the roster's cast members -- quest
        # bosses, conquest defenders, posse leaders, the war's
        # lieutenants -- are the ones the record keeps.
        for name in _named_dead(foes):
            remember(state, f"KILLED: {name}.")
        if mercy == "hell":
            # The Past Due visit resolved (won, or fought to a
            # standstill): hell's ONE visit is spent, so the job is
            # written off. A LOST one closed the same account through
            # apply_mercy above (that path returns early).
            close_hell_account(state, log)
        # The on-kill weapon quirks pay out (2026-07-28): Midas gold,
        # dark karma -- whatever the engine counted during the melee.
        collect_weapon_quirks(state, log)
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
                log_banner(log,
                           f"  {h.name}'s {h.weapon.name} is taken up from "
                           f"where they fell -- quality steel stays with "
                           f"the party (`give HERO {h.weapon.name}`).",
                           [f"{h.name}'s {h.weapon.name}",
                            "is taken up from where they fell",
                            f"(`give HERO {h.weapon.name}`)."])
        # The companion morale pass: blood and fear, whatever the outcome
        # (a game over needs no bookkeeping).
        satisfaction_after_fight(party, dead_before or [], log)
        # The quartermaster pass (2026-07-26): the fight just changed the
        # stock (potions drunk at the pause, a potion looted, a fallen
        # companion's satchel) and who needs it. It DEALS only -- nobody
        # drinks on the way out of a fight (2026-08-05): the party can camp
        # from here and the night knits HP back for free, so the vial keeps.
        # The drink waits for the next fight's opening (rpg.open_fight).
        auto_potions(party, log)
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
    log = new_combat_log()
    open_fight(party, log)

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
    tail = ", rested and healed" if healed else ""
    note = fit_lines(["(the earlier fight's survivors",
                      f"still hold it: {standing} standing{tail})"])
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
        if state["position"]["area"] != home["key"]:
            print(f"The {site.key} lies outside {home['name']} -- the party "
                  f"is at {location_line(state)}. `travel {home['key']}` "
                  f"first.")
            return
    log = new_combat_log()
    open_fight(party, log)

    room_name, roster = site.rooms[args.room - 1]
    held = reclaim_room(state, site.key, args.room)
    banner = f"=== {site.key.capitalize()} room {args.room}: {room_name}"
    if held is None:
        spawn = site.spawn_phrase.format(n=len(roster))
        log_banner(log, f"{banner} ({spawn}) ===",
                   [f"=== {site.key.capitalize()}",
                    f"room {args.room}: {room_name} ===",
                    f"({spawn})"])
        foes = []
        for kind in roster:
            state["foe_count"] += 1
            foes.append(make_foe(kind, state["foe_count"], rng))
        for line in roster_lines(foes):
            log.append("  " + line)
    else:
        foes, note = held
        log_banner(log, f"{banner}, again ===",
                   [f"=== {site.key.capitalize()}",
                    f"room {args.room}: {room_name},", "again ==="])
        for line in note:
            log.append("  " + line)
        for line in roster_lines([f for f in foes if f.alive]):
            log.append("  " + line)

    resolve_encounter(state, log, foes, site.encounter_xp,
                      site=site.key, room=args.room,
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
    if state["party"] and maybe_post_wave(state):
        save(state)     # persist the posting BEFORE the readout: a broken
                        # pipe mid-print must not lose the wave
    if state["party"] and maybe_assign_task(state):
        save(state)     # hell's mail lands where the party asks around
    conquest_news(state)    # and so does word from the holdings
    world_news(state)       # ...and what the land itself is living through
    crime_news(state)       # ...and hell's crime suggestions
    clock_notices = board_clock(state)   # asking around IS reading the board:
    save(state)                          # closed windows, fresh postings
    key = None
    if args.settlement:
        # An explicit settlement (or 'all') is the DM's overview; what the
        # PLAYER gets is the ask-around funnel over the local list (dm.md).
        if args.settlement.lower() != "all":
            want = args.settlement.lower()
            match = [s for s in settlements(world) if want in s["key"]]
            if not match:
                print(f"No settlement matches {args.settlement!r}. "
                      "Settlements: "
                      + ", ".join(s["name"] for s in settlements(world)))
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
        if held_here(state):
            print(holding_board_line(here))
            return
        key = here["key"]
        if clock_notices:
            print("\n".join(clock_notices))
        print(f"Day {state['clock'].day}. Asking around {here['name']} "
              f"(the DM's inventory -- in play, each job is its GIVER's; "
              f"funnel to them in one message, dm.md):")
    day = state["clock"].day
    if args.settlement:
        for line in board_lines(world, key, day=day):
            print(line)
    else:
        # HERE is the whole TILE, not just the Area the party stands in:
        # stepping between the Areas of one Tile is free (2026-08-15), so a
        # sibling village's work is as available as the local board's.
        near = nearby_settlements(world, state["position"]["tile"])
        print("HERE:")
        for settlement, days in [(world["areas"][key], 0)] + [
                pair for pair in near
                if pair[1] == 0 and pair[0]["key"] != key]:
            for line in board_lines(world, settlement["key"], day=day):
                print(line)
    if not args.settlement:
        # What came of the jobs nobody took (2026-07-26): the settlement's
        # failure rumors, day-stamped, told once.
        here = local_settlement(state)
        told = take_failure_rumors(here) if here is not None else []
        if told:
            print("What came of the work nobody took:")
            for r in told:
                print(f"  (day {r['day']}) {r['name']}: {r['text']}")
            save(state)
    if not args.settlement:
        cast = [n for n in world.get("npcs", [])
                if n["seat"] == key
                and n.get("post") in ("ruler", "sage", "wildcard")]
        if cast:
            print("Notables in town (the recurring cast -- see dm.md):")
            for n in cast:
                print("  " + npc_line(n))
                # The land RULER carries a rolled character since the
                # politics rung (2026-08-10): what is said of him here is
                # public reputation, which is what makes him rumor fuel.
                for extra in worldsim.notable_lines(world, n):
                    print(extra)
    if not args.settlement:
        # THE THREE-DAY RUMOR RADIUS (2026-08-15, Local Quest Geography;
        # it used to be every open job in the current LAND, a rule written
        # when a land was six Areas wide rather than a country). The player
        # knows the open work at every KNOWN settlement within
        # QUEST_RUMOR_DAYS of here -- name, exact level, whose board, which
        # Tile, how far -- so travel is an informed choice and the choice is
        # a real one. Details and `take` still want the party AT the posting
        # settlement.
        lines = rumor_lines(
            world, nearby_settlements(world, state["position"]["tile"]), day)
        if lines:
            print(f"Word from up to {QUEST_RUMOR_DAYS} days' road away "
                  f"(travel there to take one; `show QID` for what's "
                  f"known):")
            for line in lines:
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
    for line in quest_detail_lines(state["world"], quest, dm=args.dm,
                                   day=state["clock"].day):
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
    if quest["status"] == "work_done":
        print(f"[{quest['id']}] {quest['name']}: the work is done -- "
              f"`turnin {quest['id']}` at the giver pays it.")
        return
    if quest["status"] == "lost":
        print(f"[{quest['id']}] {quest['name']} is over -- done, never "
              f"paid: the window closed before the party returned.")
        return
    if quest["status"] in ("failed", "expired"):
        print(f"[{quest['id']}] {quest['name']} is over -- the window "
              f"closed on day {quest.get('deadline_day')}. "
              f"{failure_line(quest)}")
        return
    day = state["clock"].day
    already = quest["id"] in (state.get("accepted") or [])
    if not already and quest_expired(quest, day):
        # A job the party ALREADY took keeps its grace (switching back to a
        # late job is the player's call); an untaken one is simply gone.
        print(f"[{quest['id']}] {quest['name']} is stale -- it was due on "
              f"day {quest['deadline_day']} and nobody is paying for it "
              f"now. `board` for what still stands.")
        return
    if not at_quest_origin(state, quest):
        return
    here = occupied_here(state)
    if here is not None:
        print(occupation_line(state, here))
        return
    state["active_quest"] = quest["id"]
    accepted = state.setdefault("accepted", [])
    if quest["id"] not in accepted:
        accepted.append(quest["id"])   # the map tracks TAKEN jobs (map.txt)
    if quest.get("hell_task") and quest.get("deadline_day") is None:
        # Taking the assignment stops the collections ladder and stamps
        # the visible completion window: TASK_WINDOW_DAYS + the road
        # days to the job (2026-08-03 -- hell waits on a party that is
        # working). The window uses the honest deadline machinery, but
        # hell work is never LOST off the clock: past the window the
        # ladder resumes instead (maybe_enforce; board_clock skips it).
        if quest.get("kind") == "delivery":
            road = quest.get("days", 0)
        else:
            first = quest_sites(state["world"], quest)[quest["next"]["site"]]
            target_area = state["world"]["areas"][first["area"]]
            road = path_days(state["position"]["tile"], target_area["tile"])
        window = state["rng"].randint(*karma.TASK_WINDOW_DAYS) + road
        quest["posted_day"] = day
        quest["window"] = window
        quest["deadline_day"] = day + window
    g = quest.get("giver")
    if g:
        print(f"The job is taken from its giver -- narrate the scene "
              f"(dm.md): {npc_line(g)}")
    print(f"The party takes the job: {quest_line(quest, day)}")
    for line in quest_detail_lines(state["world"], quest, dm=False,
                                   day=day)[1:]:
        print(line)
    if quest.get("hell_task"):
        print(f"Hell wants it done by day {quest['deadline_day']} "
              f"({deadline_note(quest, day)}). Late still pays "
              f"x{QUEST_PAY_BANDS['late']:g} for "
              f"{QUEST_GRACE_DAYS} more days, then nothing -- but the "
              f"job never lapses: past the window, collections resume "
              f"until it is done, withdrawn, or bribed quiet.")
    elif quest.get("deadline_day") is not None:
        print(f"The job is wanted by day {quest['deadline_day']} "
              f"({deadline_note(quest, day)}). Late still pays "
              f"x{QUEST_PAY_BANDS['late']:g} for "
              f"{QUEST_GRACE_DAYS} more days; after that the job is lost "
              f"and the turn-in with it.")
    if quest.get("kind") == "delivery":
        print(f"The road is the job: `travel {quest['dest']}` "
              f"({quest['days']} day(s)) and expect trouble en route -- "
              f"arriving is the turn-in.")
    else:
        first = quest_sites(state["world"], quest)[quest["next"]["site"]]
        target_area = state["world"]["areas"][first["area"]]
        if not target_area.get("known"):
            target_area["known"] = True
            target_area["discovered_day"] = state["clock"].day
        first["known"] = True
        rooms = site_rooms(state["world"], first)
        if rooms:
            rooms[0]["known"] = True
        print(f"The first site is {first['name']}. `look`, then "
              f"`travel {target_area['name']}`, `go {first['name']}`, then "
              f"`room` faces its next encounter.")
    if quest.get("align") == "dark":
        print("(dark work: every XP it pays is SIN -- heat rises, "
              "and the law comes collecting. Honest jobs burn sin "
              "1:1; `sin` shows the meter.)")
    save(state)


def cmd_turnin(args: argparse.Namespace) -> None:
    """Hand the finished job back to its giver (2026-08-08, the turn-in
    stage): gated on the party standing in the giver's settlement area, run
    by the DM as part of the return scene and narrated as that scene
    (dm.md). ALL the gold and the TURN-IN tranche of the XP land here,
    banded by the turn-in day -- the road home is finally inside the
    clock -- plus the CHA negotiation, the reward weapon, the companion
    morale bump, and the epilogue. `--here` is the DM's valve for edge
    fiction (a dead giver, an occupied town): pay where the story says."""
    state = load()
    if not require_no_pending(state):
        return
    world = state["world"]
    quest = _get_quest(world, args.quest)
    if quest is None:
        return
    qid = quest["id"]
    if quest.get("kind") == "delivery":
        print(f"[{qid}] {quest['name']} is a delivery -- arriving at "
              f"{quest['dest_name']} is the turn-in.")
        return
    if quest["status"] == "open":
        if quest.get("proof_pending"):
            print(f"[{qid}] {quest['name']}: the target escaped -- proof "
                  f"wanted ({quest.get('proof')}). The job is not done "
                  f"until they are dead.")
        else:
            print(f"[{qid}] {quest['name']}: the work is not done yet.")
        return
    if quest["status"] == "done":
        print(f"[{qid}] {quest['name']} is already paid.")
        return
    if quest["status"] in ("failed", "expired", "lost"):
        print(f"[{qid}] {quest['name']} is over -- the window closed on "
              f"day {quest.get('deadline_day')}.")
        return
    day = state["clock"].day
    if quest_expired(quest, day, taken=True):
        # The window closed on the road home; the next day tick would say
        # the same (board_clock). Say it now instead of paying.
        for line in _lose_paid_window(state, quest):
            print(line)
        save(state)
        return
    if not args.here and not at_quest_origin(state, quest):
        return
    party, purse = state["party"], state["purse"]
    pc = party[0]
    pc_level_before = pc.level
    band = quest_band(quest, day)
    mult = QUEST_PAY_BANDS[band]
    enc = quest.get("encounters", 1)
    xp = round(quest_turnin_xp(quest["level"], enc) * mult)
    gold = round(quest_gold_posted(quest) * mult)
    g = quest.get("giver")
    log: list[str] = []
    if g:
        log.append(f"The job is handed back to its giver -- narrate the "
                   f"scene (dm.md): {npc_line(g)}")
    award_quest(party, purse, gold, xp, log,
                f"{quest['name']} -- paid in full",
                banner="QUEST COMPLETE")
    record_karma(state, xp, quest.get("align", "good"), log)
    rw = quest.get("reward_weapon")
    if rw:
        # The reward weapon finally stands where the giver does: `claim`
        # already waits at the turn-in.
        state["pending_reward"] = dict(rw)
        log_banner(log,
                   f"  The pay is the {rw['name']} itself -- "
                   f"`claim HERO` takes it up.",
                   [f"The pay is the {rw['name']} --",
                    "`claim HERO` takes it up."])
    if quest.get("deadline_day") is not None and band != "on time":
        log_banner(log,
                   f"  (turned in {band.upper()} -- day {day} against a "
                   f"deadline of day {quest['deadline_day']}: "
                   f"x{mult:g} on the turn-in)",
                   [f"({band.upper()} turn-in: day {day},",
                    f"due day {quest['deadline_day']} --",
                    f"x{mult:g} on the lump)"])
    quest["status"] = "done"
    quest["turned_in_day"] = day
    if quest.get("epilogue"):
        log.append(f"  EPILOGUE (day {day}): {quest['epilogue']}")
    remember(state,
             f"[{qid}] {quest['name']} (L{quest['level']}) -- done.",
             kind="quest", note=quest.get("epilogue", ""))
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
    if quest["status"] == "work_done":
        print(f"[{qid}] {quest['name']}: the work is done -- no rooms "
              f"left. Return to the giver and `turnin {qid}`.")
        return
    if quest["status"] == "lost":
        print(f"[{qid}] {quest['name']} is over -- done, never paid. "
              f"Take a new quest.")
        return
    if quest.get("proof_pending"):
        # Every room is fought; the cursor stands past the last one and
        # there is nothing here to index. What the job still wants is a
        # corpse, and that is `pursue`'s business, not this command's.
        print(f"[{qid}] {quest['name']}: every room is cleared, but the "
              f"target got away. The job still wants {quest['proof']} "
              f"(proof of the kill). `pursue` while the trail is warm "
              f"(same day, same area); after that, finding them again is "
              f"the DM's scene.")
        return
    if quest.get("kind") == "delivery":
        print(f"[{qid}] {quest['name']} is a road job -- no rooms to fight. "
              f"`travel {quest['dest']}` to carry it.")
        return
    if not at_quest_site(state, quest):
        return
    party, rng = state["party"], state["rng"]
    cur = quest["next"]
    site = quest_sites(state["world"], quest)[cur["site"]]
    rooms = site_rooms(state["world"], site)
    room_i = cur["room"]
    room = rooms[room_i]
    room_name, kinds = room["name"], room["kinds"]
    site_key = site["id"]
    state["position"]["room"] = room["id"]
    site["visited"] = True
    room["known"] = room["visited"] = True

    # The caper structure (2026-07-19, dark quests -- karma.py's schema):
    # a TWIST site opens with its authored terms (one message: take them
    # with `settle`, or `room` again to fight through them)...
    twist = site.get("twist")
    if (twist and not twist.get("resolved") and room_i == 0
            and not twist.get("offered")):
        twist["offered"] = True
        save(state)
        print(f"*** THE TWIST -- {quest['name']}, {site['name']}: ***")
        print(f"  {twist['text']}")
        print(f"  The player's call: `settle` takes the terms (this "
              f"site closes at x{twist.get('pay', 0.5):g} of its lump, "
              f"no fight); `room` refuses them and fights it out for "
              f"the full pay.")
        return
    # ...and a DEED site opens with the attempt itself: the PC rolls
    # 2d6 + stat vs the DC. A make does the site CLEAN (full lump, no
    # fight); a miss botches it into the fight, with witnesses.
    deed = site.get("deed")
    if deed and not deed.get("done") and room_i == 0:
        deed["done"] = True
        pc = party[0]
        stat_of = {"str": pc.str_, "dex": pc.dex, "mind": pc.mind,
                   "cha": pc.cha}
        stat = stat_of.get(deed["stat"], pc.dex)
        roll = rng.randint(1, 6) + rng.randint(1, 6)
        total = roll + stat
        made = total >= deed["dc"]
        print(f"*** THE DEED -- {quest['name']}, {site['name']}: "
              f"{deed['text']}. ***")
        print(f"  {pc.name} rolls 2d6+{deed['stat'].upper()}: {roll}+"
              f"{stat} = {total} vs DC {deed['dc']} -- "
              f"{'CLEAN' if made else 'BOTCHED'}.")
        if made:
            pc_level_before = pc.level
            log2: list[str] = ["  No alarm, no blood, no witnesses -- "
                              "the job is done quietly."]
            _close_site(state, log2, qid, note="clean work")
            for h in party[1:]:
                if not h.dead:
                    autospend_points(h, log2)
            print("\n".join(log2))
            save(state)
            if not pc.dead and pc.level > pc_level_before:
                print()
                print(f"*** {pc.name} reached level {pc.level} -- the "
                      f"spending menu (show it to the player, dm.md): ***")
                print_levelup_menu([pc])
            return
        klog: list[str] = []
        karma.record_karma(state["karma"], karma.DEED_FAIL_KARMA, "dark",
                           klog, party_level(state), state["clock"].day)
        print(f"  {deed['fail']} -- witnesses are hard to avoid "
              f"(+{karma.DEED_FAIL_KARMA} sin), and the fight is "
              f"on.")
        for line in klog:
            print(line)

    log = new_combat_log()
    open_fight(party, log)

    held = reclaim_room(state, site_key, room_i + 1)
    banner = (f"=== {quest['name']} -- {site['name']} (L{site['level']}), "
              f"room {room_i + 1}/{len(site['rooms'])}: {room_name}")
    n_rooms = len(rooms)
    banner_parts = [f"=== {quest['name']} ===",
                    f"{site['name']} (L{site['level']}),",
                    f"room {room_i + 1}/{n_rooms}: {room_name}"]
    if held is None:
        log_banner(log, banner + " ===", banner_parts)
        # A named villain (the conquest's lieutenants/conqueror) caps the
        # site's last room: the strongest roster slot wears the name --
        # display only, the stat row never forks (story.py).
        boss = site.get("boss")
        boss_at = None
        if boss and room_i == len(rooms) - 1:
            hits = [i for i, k in enumerate(kinds) if k == boss["kind"]]
            boss_at = hits[-1] if hits else None
        foes = []
        for i, kind in enumerate(kinds):
            state["foe_count"] += 1
            foe = make_foe(kind, state["foe_count"], rng,
                           display=quest["skins"].get(kind),
                           ferocity=(FEROCITY_RELENTLESS
                                     if quest.get("story_wave") is not None
                                     else None))
            if i == boss_at:
                foe.name = boss["display"]
            foes.append(foe)
        for line in roster_lines(foes):
            log.append("  " + line)
    else:
        foes, note = held
        log_banner(log, banner + ", again ===",
                   banner_parts[:-1] + [banner_parts[-1] + ", again"])
        for line in note:
            log.append("  " + line)
        for line in roster_lines([f for f in foes if f.alive]):
            log.append("  " + line)

    resolve_encounter(state, log, foes,
                      quest_encounter_xp(quest["level"],
                                         quest.get("encounters", 1)),
                      site=site_key, room=room_i + 1, quest=qid,
                      field=ROOM_FIELD,
                      align=quest.get("align", "good"))


def cmd_forge(args: argparse.Namespace) -> None:
    """The DM's quest creator: build a quest by the generator's own rules
    (level in, rosters out) for scenes the generated offers don't cover,
    placing its persistent sites in an area."""
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
    area = current_area(state)
    if args.area:
        want = args.area.lower()
        match = [a for a in all_areas(world) if want in a["key"]]
        if not match:
            print(f"No area matches {args.area!r}.")
            return
        area = match[0]
    qid = next_quest_id(world)   # the world's monotonic counter: pruned
                                 # shadow jobs and expired postings leave
                                 # persistent geography behind
    quest = forge_quest(world, qid, args.level, args.places, args.encounters,
                        kinds, args.name, state["rng"],
                        area_key=area["key"],
                        align="dark" if args.dark else "good",
                        proof=args.proof or "")
    if args.days:
        # A forged job carries a window only when the DM gives it one
        # (`forge --days N`); without one it is timeless, like a war wave.
        quest["posted_day"] = state["clock"].day
        quest["window"] = args.days
        quest["deadline_day"] = state["clock"].day + args.days
    world["quests"][qid] = quest
    area["quests"].append(qid)
    save(state)
    print(f"Forged at {area['name']}:")
    for line in quest_detail_lines(world, quest, day=state["clock"].day):
        print(line)


# --------------------------------------------------------------------------- #
# The wilds: travel / explore / hunt / engage (the navigation layer)
# --------------------------------------------------------------------------- #

def _spawn_wild_foes(state: dict, kinds: list[str],
                     skins: dict | None = None) -> list:
    rng = state["rng"]
    foes = []
    for kind in kinds:
        state["foe_count"] += 1
        foes.append(make_foe(kind, state["foe_count"], rng,
                             display=(skins or {}).get(kind)))
    return foes


def party_preferred_field(party: list) -> int:
    """The gap the PARTY opens at when it picks the engagement (a won
    sighting, the hunt): its longest ready reach -- a shooter's range, a
    caster's bolts -- or 0 for an all-steel party that closes to contact
    quietly (today's fight)."""
    return max((h.threat_reach for h in party if h.alive), default=0)


def fight_wild_encounter(state: dict, kinds: list[str], level: int,
                         banner: str, field: int = WILD_FIELD,
                         skins: dict | None = None) -> None:
    """Run a wilderness encounter through the same machinery as any other
    (it can pause; retreat scatters it -- the road is not a room). `field`
    is the engagement's opening gap (who noticed whom decides it), and the
    SKY comes with it: a road fight is fought in whatever the world layer
    rolled for the day (2026-08-08), which a fight inside a site is not.

    `skins` reskins the roster for a world card's local encounter entry
    (2026-08-09): a Toll-Man is a cutthroat in the baron's livery, and the
    stat row never changes with the costume."""
    party = state["party"]
    log = new_combat_log()
    open_fight(party, log)
    log_banner(log, f"=== {banner} (a level-{level} encounter) ===",
               [f"=== {banner} ===", f"(a level-{level} encounter)"])
    foes = _spawn_wild_foes(state, kinds, skins)
    for line in roster_lines(foes):
        log.append("  " + line)
    resolve_encounter(state, log, foes, wild_encounter_xp(level),
                      field=field, weather=fight_sky(state))


def wild_event(state: dict, chance: float, banner: str,
               where: str = "wilds") -> bool:
    """Roll the wilds once: nothing, a FIGHT (returns True; the encounter
    machinery has taken over and saved), or a SIGHTING. Foes well above
    the party keep the old contract (usually spotted at range unless they
    ambush first -- deadly-but-avoidable is a promise, not a roll of the
    conspicuousness dice). ORDINARY trouble runs the notice contest
    (quests.notice_contest, 2026-07-16): party MIND vs foe senses over
    each side's conspicuousness -- seen-first alone = the sighting choice;
    seeing the party first alone = an AMBUSH at the foes' preferred range;
    both or neither = met square across the open field (WILD_FIELD).

    THE LOCAL ENCOUNTER TABLE (2026-08-09, the economy floor). Before the
    land's own wildlife is rolled, the world layer gets a look: a live card
    or a derived state may have put somebody on this ground -- toll-men on
    the bridges, loggers holding a camp, riders off the border. It replaces
    WHO the party meets and never how hard they are: the level is still the
    road's party-independent roll, which is a contract. `where` is the
    ground ("road" for a travel leg, "wilds" for a day afield or a night
    camped)."""
    rng = state["rng"]
    if rng.random() >= chance:
        return False
    level = roll_wild_level(rng)
    land = state["position"]["land"]
    entry = worldsim.local_encounter(state["world"], land, where, rng)
    skins = dict(entry.get("skins") or {}) if entry else {}
    kinds = build_wild_encounter(level, land, rng,
                                 pool=tuple(entry["kinds"]) if entry else None)
    if entry:
        banner = f"{banner} -- {entry['as']}"
    party_level = max(h.level for h in state["party"] if not h.dead)
    towering = level >= party_level + SPOTTED_MARGIN
    if towering:
        spotted, ambushed = rng.random() >= AMBUSH_CHANCE, False
    else:
        party_sees, foes_see = notice_contest(state["party"], kinds, rng)
        spotted = party_sees and not foes_see
        ambushed = foes_see and not party_sees
    if spotted:
        line = f"L{level}: {roster_kinds_line(kinds, skins)}"
        state["sighting"] = {"kinds": list(kinds), "level": level,
                             "day": state["clock"].day, "line": line,
                             "skins": skins}
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
    fight_wild_encounter(state, kinds, level, banner, field=field,
                         skins=skins)
    return True


# --------------------------------------------------------------------------- #
# Travel: the grid walk (2026-08-15, Grid Navigation and Map UI)
# --------------------------------------------------------------------------- #
# `travel` walks CARDINAL TILE EDGES. One edge is the atomic unit: its days
# are spent as camp nights, the party is PLACED in the Tile it reached, and
# only then does the road roll its encounter. That order is the whole point
# of the rework -- an interrupted trip now leaves the party where it got to,
# never back where it set out from, so there is no half-edge position to save
# and no paid-crossing marker to carry across one (both are gone with it).
#
# A named or coordinate destination is a CONVENIENCE over that primitive: the
# cheapest route is walked edge by edge and stops the moment something wants
# the player's attention. Weather detours and tolls are priced PER EDGE, not
# per command -- otherwise ten `travel north`s would cost ten tolls where one
# `travel Rome` across the same ground cost one.

SEA_ARRIVALS = ("The party takes ship and stands out into open water.",
                "Sail and oar carry the party across the water.",
                "The party crosses by water, sighting no other sail.")


def at_sea(state: dict) -> bool:
    """Is the party on a water Tile? The sea has no road table, no game to
    hunt and no ground to walk -- it has weather and time."""
    return state["world"]["tiles"][state["position"]["tile"]]["biome"] == "sea"


def _sea_leg(world: dict, origin: str, dest: str) -> bool:
    """A passage rather than a road: either end is water. Nothing rolls off
    the land's encounter table on one (the MVP has no naval combat), and
    stepping ashore from a boat is not a road arrival either -- the rule is
    symmetric because the edge is."""
    return "sea" in (world["tiles"][origin]["biome"],
                     world["tiles"][dest]["biome"])


def _natural_area(world: dict, tile: dict) -> dict:
    """Where an ordinary leg puts the party down: the Tile's natural Area.
    A named settlement destination overrides this on the FINAL leg only."""
    return world["areas"][tile["natural_area"]]


def travel_target(state: dict, want: str) -> tuple[dict, dict] | None:
    """Resolve `travel`'s argument to (destination Tile, arrival Area).

    Four spellings, in priority order: a cardinal direction (the primitive),
    a coordinate, a known Area, and a Tile by name -- which in practice
    means a historical city, since every other Tile is named after its own
    coordinate. An ordinary settlement nobody has found yet is not a
    destination: the party cannot walk to a rumour."""
    world, pos = state["world"], state["position"]
    here = world["tiles"][pos["tile"]]
    direction = direction_word(want)
    if direction is not None:
        nid = neighbor_id(here, direction)
        if nid is None:
            print(f"The map ends {direction} of "
                  f"{tile_coordinate(here['row'], here['column'])} -- "
                  f"nothing lies that way.")
            return None
        tile = world["tiles"][nid]
        return tile, _natural_area(world, tile)
    try:
        coordinate = parse_coordinate(want)
    except ValueError as exc:
        print(str(exc))
        return None
    if coordinate is not None:
        tile = world["tiles"][tile_id_of(*coordinate)]
        return tile, _natural_area(world, tile)
    if want.strip().lower() in world["tiles"]:      # a raw Tile ID (DM/debug)
        tile = world["tiles"][want.strip().lower()]
        return tile, _natural_area(world, tile)
    low = want.lower()
    want_slug = re.sub(r"[^a-z0-9]+", "-", low).strip("-")
    area = next((a for a in all_areas(world)
                 if a.get("known")
                 and (low in a["key"].lower()
                      or low in a["name"].lower()
                      or (want_slug and want_slug in a["key"].lower()))), None)
    if area is not None:
        return world["tiles"][area["tile"]], area
    tile = next((world["tiles"][tid] for tid in world["tile_order"]
                 if low in world["tiles"][tid]["name"].lower()), None)
    if tile is not None:
        return tile, _natural_area(world, tile)
    known = sorted({a["name"] for a in all_areas(world)
                    if a.get("known") and a["kind"] == "settlement"})
    print(f"No known place matches {want!r}. Name a direction (north / "
          f"south / east / west), a coordinate (R09C18), or a known "
          f"settlement: {', '.join(known)}.")
    return None


def _road_costs(state: dict, origin: dict, dest: dict) -> int:
    """What the weather and the toll-men take off ONE edge, before it is
    walked. Returns the extra days; the gold is charged here. A purse that
    cannot cover a toll crosses anyway -- the bridge is not a wall."""
    world = state["world"]
    legs = [origin["country"], dest["country"]]
    slow, why = worldsim.travel_delay(world, legs)
    for line in why:
        print(line)
    take, tolls = worldsim.road_charges(world, legs)
    if take:
        paid = min(take, state["purse"].gold)
        state["purse"].gold -= paid
        for line in tolls:
            print(line)
        if paid == take:
            print(f"  The road takes {paid}g (purse: "
                  f"{state['purse'].gold}g).")
        elif paid:
            print(f"  The road takes what the purse has -- {paid}g of "
                  f"{take}g, and the rest is argued down.")
        else:
            print(f"  The purse is empty and the toll-men can see it. "
                  f"The party is waved through, owing nothing but the "
                  f"look of it.")
    return slow


def _road_roll(state: dict, arrival: dict, days: int) -> bool:
    """The leg's own encounter check (the per-day chance compounded over the
    days it took), plus the delivery's one guaranteed interception when this
    is the leg that reaches the cargo's destination."""
    chance = 1 - (1 - TRAVEL_ENCOUNTER_CHANCE) ** days
    banner = f"On the road at {arrival['name']}"
    delivery = active_delivery(state)
    if (delivery is not None and arrival["key"] == delivery["dest"]
            and not delivery.get("intercepted")):
        # The leg that reaches the destination is watched. Rolled off the
        # road's own table like any travel event (spotted/ambush valves
        # included), just at chance 1.
        delivery["intercepted"] = True
        print(f"  Word of {delivery['cargo']} travelled faster than the "
              f"party -- the road is watched.")
        return wild_event(state, 1.0, banner, where="road")
    return wild_event(state, chance, banner, where="road")


def _walk_edge(state: dict, dest: dict, arrival: dict) -> str:
    """One cardinal edge, whole: cost, nights, arrival, road roll.

    Returns `"on"` (the route may walk another edge) or `"stop"` (something
    wants the player -- a fight, a sighting, a wipe)."""
    world = state["world"]
    origin = world["tiles"][state["position"]["tile"]]
    direction = edge_direction(origin, dest)
    days = edge_days(origin, dest)
    clear_sighting(state)
    worldsim.roll_world(world, state["clock"].day)   # quote TODAY's fords
    days += _road_costs(state, origin, dest)
    where = tile_coordinate(dest["row"], dest["column"])
    label = arrival["name"] if arrival["kind"] == "settlement" else where
    print(f"The party goes {direction} to {label} -- {days} day(s).")
    weather_note(state)
    log = CombatLog()
    for _ in range(days):
        # Each night on the road (or at sea) is a night in the open: the sky
        # it is spent under decides whether anyone catches a chill, and a
        # storm night rolls the cabin table for a roof first.
        sky = exposure_sky(state)
        roof = (shelter_here(state, log)
                if worldsim.storming(world, state["position"]["land"])
                else None)
        _long_rest(state["party"], state["clock"], log, rng=state["rng"],
                   sky=sky, sheltered=roof is not None)
        storyteller_tale(state["party"], state["rng"], log)
        companions_brew(state, log)
        night_upkeep(state, log)
    print_play(log)
    print_board_clock(state)    # the road costs days, and days cost jobs
    sea = _sea_leg(world, origin["id"], dest["id"])
    existing = {area["id"] for area in settlements(world)}
    for settlement in reveal_tile(world, dest, day=state["clock"].day):
        if settlement["id"] not in existing:
            cast_service_providers(world, settlement, state["rng"])
    arrival = world["areas"][arrival["key"]]
    move_party(state, arrival)
    arrival["visited"] = True
    if arrival["kind"] == "settlement":
        visited = state.setdefault("visited", [])
        if arrival["key"] not in visited:
            visited.append(arrival["key"])   # known ground for teleport
    if sea:
        print(state["rng"].choice(SEA_ARRIVALS))
    print(f"The party reaches {location_line(state)} (day "
          f"{state['clock'].day}).")
    # THE ROAD, at the gates it reached (2026-08-15). The encounter is rolled
    # with the party STANDING IN the Tile it walked to, off that country's
    # own pool -- what roams the ground you arrived on. A fight stops the
    # route here, and here is where the party stays. A SEA leg rolls nothing:
    # the MVP has no naval combat, only weather and time.
    if not sea and _road_roll(state, arrival, days):
        return "stop"
    if state.get("sighting"):
        return "stop"           # spotted something: the player decides
    return "on"


def arrive(state: dict) -> bool:
    """The ceremony where the party STOPS -- run once, at journey's end or
    wherever the road broke off, never at every Tile a route passes through.
    Returns True when something took over (the law, hell): that machinery
    has already saved."""
    here = occupied_here(state)
    if here is not None:
        print(occupation_line(state, here))
    # Settling the books at the walls: the dead are buried, anyone done with
    # this party walks (with their head-split of the purse).
    log: list[str] = []
    process_departures(state, log)
    if log:
        print("\n".join(log))
    print_board_clock(state)    # a board's first look fills it
    maybe_post_wave(state)      # news travels; arrivals are where it lands
    conquest_news(state)        # word from the holdings travels with it
    world_news(state)           # and the country tells the party what moved
                                # while it was on the road (the state diff)
    weather_note(state)         # ...under whatever sky it is standing under
    price_note(state)           # ...and what that has done to the prices
    crime_news(state)           # hell suggests work on arrival too
    if maybe_punish(state):     # the law meets the party at the walls
        return True             # (karma & heat; the machinery saved)
    if maybe_enforce(state):    # hell's collections travel the same roads
        return True             # (the pact; the machinery saved)
    maybe_assign_task(state)    # and hell's mail finds arrivals
    log = []
    if deliver_if_arrived(state, log):
        print("\n".join(log))
    return False


def cmd_travel(args: argparse.Namespace) -> None:
    state = load()
    if not require_no_pending(state):
        return
    world = state.get("world")
    if not world:
        print("No world in this save -- start one with `new`.")
        return
    resolved = travel_target(state, " ".join(args.dest))
    if resolved is None:
        return
    target_tile, target_area = resolved
    pos = state["position"]
    if target_tile["id"] == pos["tile"]:
        # Same Tile: switching Areas is free. A Tile is 30x60 km and its
        # Areas are a walk across local ground, not a journey.
        if target_area["key"] == pos["area"]:
            print(f"The party is already at {target_area['name']}.")
            return
        move_party(state, target_area)
        target_area["visited"] = True
        print(f"The party crosses to {location_line(state)} -- no day "
              f"passes; it is the same Tile.")
        save(state)
        return
    route = shortest_path(pos["tile"], target_tile["id"])
    if len(route) > 2:
        total = sum(edge_days(route[i], route[i + 1])
                    for i in range(len(route) - 1))
        print(f"The road to {target_area['name']}: {len(route) - 1} legs, "
              f"{total} day(s) at the least.")
    for step, nid in enumerate(route[1:], 1):
        final = step == len(route) - 1
        dest = world["tiles"][nid]
        arrival = target_area if final else _natural_area(world, dest)
        if _walk_edge(state, dest, arrival) == "stop":
            if state.get("pending") or party_wiped_out(state):
                return          # a paused fight or a wipe owns the turn,
                                # and its machinery has already saved
            if not final:
                print(f"  The road stops here -- the party is at "
                      f"{location_line(state)}. `travel "
                      f"{target_area['name']}` again when it is clear.")
            if not arrive(state):
                save(state)
            return
    if not arrive(state):
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
    polity = state["position"]["land"]
    here = current_area(state)
    if here["kind"] != "natural":
        # Exploring is going AFIELD: from a settlement the party walks out
        # into its own Tile's countryside, which costs no day of its own
        # (2026-08-15 -- the old country-wide "next undiscovered Area"
        # sweep went with the list-shaped world).
        here = world["areas"][world["tiles"][state["position"]["tile"]]
                              ["natural_area"]]
        here["known"] = here["visited"] = True
        move_party(state, here)
    print(f"The party explores {here['name']} -- a day afield, camping "
          f"rough.")
    weather_note(state)
    log = CombatLog()
    sky = exposure_sky(state)
    roof = (shelter_here(state, log)
            if worldsim.storming(world, polity) else None)
    _long_rest(party, clock, log, rng=rng, sky=sky,
               sheltered=roof is not None)
    storyteller_tale(party, rng, log)
    companions_brew(state, log)
    night_upkeep(state, log)
    print_play(log)
    print_board_clock(state)    # a day afield is a day off the board's clock
    found_site = materialize_natural_site(world, here, day=clock.day)
    log = []
    if found_site is not None:
        award_xp(party, EXPLORE_XP, log, "discovery")
        print(f"A local place is found: {found_site['name']}.")
        found_name = found_site["name"]
    else:
        found_name = here["name"]
        print(f"Nothing new is found in {here['name']}. Its three "
              f"ordinary sites are already mapped -- `travel` to another "
              f"Tile for fresh ground.")
    print("\n".join(log))
    # Open water has no wilds table (the sea rolls weather, not foes).
    if at_sea(state) or not wild_event(state, EXPLORE_ENCOUNTER_CHANCE,
                                       f"In the wilds at {found_name}"):
        save(state)


def cmd_house(args: argparse.Namespace) -> None:
    """Materialize one persistent ordinary house in the current settlement."""
    state = load()
    if not require_no_pending(state):
        return
    settlement = local_settlement(state)
    if settlement is None:
        print("Ordinary houses are requested in a settlement.")
        return
    site, resident = materialize_house(state["world"], settlement)
    state["position"]["site"] = site["id"]
    state["position"]["room"] = site["rooms"][0]
    site["visited"] = True
    state["world"]["rooms"][site["rooms"][0]]["visited"] = True
    print(f"{site['name']} is now part of {settlement['name']}.")
    print(f"{resident['name']} is here, {resident['role']}.")
    save(state)


def cmd_hunt(args: argparse.Namespace) -> None:
    """The farm loop: stalk prey in the Tile's wilds, off the country's own
    pool. The party CHOOSES this fight, so unlike the road table it rolls
    at-or-below the party's level -- grinding XP and loot is always
    available, at wild (below-board) rates."""
    state = load()
    if not require_no_pending(state):
        return
    world = state.get("world")
    if not world:
        print("No world in this save -- start one with `new`.")
        return
    if at_sea(state):
        print("There is nothing to stalk on open water. `travel` to land "
              "to hunt.")
        return
    clear_sighting(state)
    party, rng = state["party"], state["rng"]
    land = state["position"]["land"]
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
                         field=party_preferred_field(state["party"]),
                         skins=sighting["skins"])


def cmd_pursue(args: argparse.Namespace) -> None:
    """Run down a rout's survivors (2026-08-08): one command, one roll, no
    tracking subsystem. Available only while the trail is WARM -- same day
    as the rout, party still in the area, no night slept. The player says
    "I want them dead"; the DM runs it. One attempt per rout. Success
    re-opens the fight at the runners' fled state -- their end-of-fight HP,
    wounds and STA (they have been running; no refresh) -- met at the
    party's preferred range: they are the hunters. Failure loses the
    trail, no day spent; the loose end stays. The mop-up pays WILD rates
    (the room already banked its encounter share when the field cleared).

    `--stage` is the DM's valve for the cold trail's END: a re-encounter
    staged off the loose end (rumor, travel, the story's territory) -- no
    gate, no roll, and the survivors healed by the days passed (living
    foes heal after a day; the troll fully)."""
    state = load()
    if not require_no_pending(state):
        return
    ends = [r for r in state.get("loose_ends") or []
            if r.get("resolved_day") is None and loose_end_survivors(r)]
    if args.id:
        rec = loose_end_by_id(state, args.id)
        if rec is None:
            print(f"No loose end {args.id!r}. On the books: "
                  + (", ".join(r["id"] for r in state.get("loose_ends")
                               or []) or "none") + ".")
            return
    else:
        rec = next((r for r in ends
                    if trail_warm(state, r) and not r["pursue_tried"]),
                   None) or (ends[0] if ends else None)
        if rec is None:
            print("No loose end to pursue -- nobody has gotten away.")
            return
    day = state["clock"].day
    survivors = loose_end_survivors(rec)
    if rec.get("resolved_day") is not None or not survivors:
        print(f"Loose end {rec['id']} is settled -- nobody left to chase.")
        return
    if not args.stage:
        if rec.get("pursue_tried"):
            print(f"Loose end {rec['id']}: the trail was walked out "
                  f"already -- one attempt per rout. Finding them again "
                  f"is rumor, travel, and the DM's territory (`pursue "
                  f"{rec['id']} --stage` when the story stages it).")
            return
        if not trail_warm(state, rec):
            print(f"Loose end {rec['id']}: the trail is cold -- it was "
                  f"day {rec['day']} at {rec['area_name']}, and a night "
                  f"heals a runner's wounds. Pursuit is finding now: "
                  f"rumor, travel, forge -- the record keeps the story "
                  f"(`pursue {rec['id']} --stage` when it lands).")
            return
    party, rng = state["party"], state["rng"]
    runners = [_entity_from_dict(d) for d in rec["foes"]
               if not d.get("dead")]
    for f in runners:
        f.withdrew = False      # they are back in a fight
    if args.stage:
        days = day - rec["day"]
        runners = refresh_foes_after_retreat(runners, days)
        banner = f"THE RE-ENCOUNTER: {rec['where']} -- day {rec['day']}"
    else:
        rec["pursue_tried"] = True
        contest_log: list[str] = []
        caught = track_contest(party, runners, rng, contest_log)
        for line in contest_log:
            print(line)
        if not caught:
            print(f"The trail is lost. No day is spent; the loose end "
                  f"stays on the books ({rec['id']} -- the record is "
                  f"the story hook).")
            save(state)
            return
        banner = f"RUN DOWN: {rec['where']}"
    log = new_combat_log()
    open_fight(party, log)
    level = max(f.level for f in runners)
    log_banner(log, f"=== {banner} (a level-{level} fight) ===",
               [f"=== {banner} ===", f"(a level-{level} fight)"])
    for line in roster_lines(runners):
        log.append("  " + line)
    quest = state["world"]["quests"].get(rec["quest"]) \
        if rec.get("quest") and state.get("world") else None
    resolve_encounter(state, log, runners, wild_encounter_xp(level),
                      field=party_preferred_field(party),
                      align=(quest or {}).get("align", "neutral"),
                      weather=fight_sky(state) if not rec.get("site")
                      else "",
                      pursuit=rec["id"])


def cmd_look(args: argparse.Namespace) -> None:
    """Show the stored local place and only player-known facts/children."""
    state = load()
    world, pos = state["world"], state["position"]
    area = current_area(state)
    if args.dm:
        place = (world["rooms"][pos["room"]] if pos.get("room") else
                 world["sites"][pos["site"]] if pos.get("site") else area)
        print("DM PLACE FACTS")
        for line in place_debug_lines(world, place):
            print(line)
        local_ends = [r for r in state.get("loose_ends") or []
                      if r.get("area") == area["key"]]
        if local_ends:
            print("LOOSE ENDS HERE (newest first):")
            for rec in local_ends:
                print(f"  {loose_end_line(rec, state['clock'].day)}")
        return
    print(f"WHERE: {location_line(state)}")
    if pos.get("room"):
        room = world["rooms"][pos["room"]]
        print(f"You are at {room['name']}.")
        facts = active_known_facts(room)
        if facts:
            print(f"It is {facts[0]['id'].replace('_', ' ')}.")
        visible = [c["label"] for c in room.get("contents", ())
                   if c.get("known") and c.get("reveal") == "visible"]
        if visible:
            print("You see: " + ", ".join(visible) + ".")
        print(f"`back` returns to {world['sites'][room['site']]['name']}.")
        return
    if pos.get("site"):
        site = world["sites"][pos["site"]]
        if site.get("description"):
            print(site["description"])
        facts = active_known_facts(site)
        if facts:
            print(f"Current state: {facts[0]['id'].replace('_', ' ')}.")
        contents = [c["label"] for c in site.get("contents", ())
                    if c.get("known")]
        if contents:
            print("You see: " + ", ".join(contents) + ".")
        rooms = [room for room in site_rooms(world, site)
                 if room.get("known")]
        print(f"{site['name']} has {len(rooms)} known immediate place(s):")
        for room in rooms:
            mark = "  <- here" if room["id"] == pos.get("room") else ""
            print(f"  {room['name']}{mark}")
        print(f"`back` returns to {area['name']}.")
        return
    visible = [s for s in area_sites(world, area) if s.get("known")]
    kind = area.get("subtype", area["kind"])
    tile = world["tiles"][pos["tile"]]
    # The TILE first, then the Area standing on it (2026-08-15): they are
    # different places now, and a breadcrumb that only named the Area left
    # the player with no idea which map cell they were on.
    print(f"TILE {tile_label(tile)} -- "
          f"{world['lands'][tile['country']]['name']}, {tile['biome']}")
    print(area.get("description") or f"{area['name']} is a {kind} Area.")
    facts = active_known_facts(area)
    if facts:
        print(f"Current state: {facts[0]['id'].replace('_', ' ')}.")
    if visible:
        print("Sites in reach:")
        for site in visible:
            print(f"  {site['name']}")
        print("Use `go SITE` to enter.")
    else:
        print("No local sites are known here.")
    services = area.get("services", ())
    if services:
        print("Services: " + ", ".join(s["label"] for s in services) + ".")
    siblings = [world["areas"][aid] for aid in tile["areas"]
                if aid != area["key"] and world["areas"][aid].get("known")]
    if siblings:
        print("Also on this Tile (a free `go`, no day):")
        for other in siblings:
            print(f"  {other['name']} "
                  f"({other.get('subtype', other['kind'])})")
    ways = []
    for direction in ("north", "south", "east", "west"):
        nid = neighbor_id(tile, direction)
        if nid is None:
            continue
        other = world["tiles"][nid]
        ways.append(f"{direction} {tile_label(other)} {other['biome']} "
                    f"({edge_days(tile, other)}d)")
    print("Roads out (`travel DIRECTION`):")
    for way in ways:
        print(f"  {way}")
def cmd_go(args: argparse.Namespace) -> None:
    """Move locally: a Room, a Site, or a SIBLING AREA on the same Tile
    (2026-08-15 -- the town and the countryside around it are one map cell,
    so crossing between them costs no day either). `travel` remains the
    day-scale move, and it is what leaves the Tile."""
    state = load()
    if not require_no_pending(state):
        return
    world, pos = state["world"], state["position"]
    want = " ".join(args.dest).lower()
    if pos.get("site"):
        site = world["sites"][pos["site"]]
        matches = [r for r in site_rooms(world, site)
                   if r.get("known") and want in r["name"].lower()]
        if matches:
            room = matches[0]
            room["known"] = room["visited"] = True
            pos["room"] = room["id"]
            rooms = site_rooms(world, site)
            index = rooms.index(room)
            if index + 1 < len(rooms):
                rooms[index + 1]["known"] = True
            print(f"You go to {location_line(state)}.")
            save(state)
            return
    area = current_area(state)
    matches = [s for s in area_sites(world, area)
               if s.get("known") and want in s["name"].lower()]
    if matches:
        site = matches[0]
        site["visited"] = True
        pos["site"], pos["room"] = site["id"], None
        rooms = site_rooms(world, site)
        if rooms:
            rooms[0]["known"] = True
        print(f"You enter {location_line(state)}.")
        save(state)
        return
    tile = world["tiles"][pos["tile"]]
    siblings = [world["areas"][aid] for aid in tile["areas"]
                if aid != area["key"] and world["areas"][aid].get("known")
                and want in world["areas"][aid]["name"].lower()]
    if siblings:
        other = siblings[0]
        move_party(state, other)
        other["visited"] = True
        print(f"You cross to {location_line(state)} -- the same Tile, so "
              f"no day passes.")
        save(state)
        return
    print(f"No local destination matches {want!r}. `look` shows what is "
          "in reach on this Tile; `travel` leaves it.")


def cmd_back(args: argparse.Namespace) -> None:
    state = load()
    if not require_no_pending(state):
        return
    pos = state["position"]
    if pos.get("room"):
        pos["room"] = None
    elif pos.get("site"):
        pos["site"] = None
    else:
        print("Already at area level. Use `travel AREA` to leave.")
        return
    print(f"You return to {location_line(state)}.")
    save(state)


def cmd_map(args: argparse.Namespace) -> None:
    state = load()
    world = state.get("world")
    if not world:
        print("No world in this save -- start one with `new`.")
        return
    for line in map_sheet_lines(state):
        print(line)


def cmd_world(args: argparse.Namespace) -> None:
    """The DM's inventory of the world layer (2026-08-07): what every land
    is living through, and what its deck still holds. Rolls the world up to
    today first -- reading it is a roll point like any other."""
    state = load()
    world = state.get("world")
    if not world:
        print("No world in this save -- start one with `new`.")
        return
    worldsim.roll_world(world, state["clock"].day)
    save(state)
    for line in worldsim.world_lines(world):
        print(line)
    print("")
    print("(the player's half: the state line on `map`, and the news at "
          "arrivals and settlement nights. `place-state` is the override.)")


def cmd_place_state(args: argparse.Namespace) -> None:
    """DM override for the minimum persistent place-state mutation API."""
    state = load()
    world = state.get("world")
    if not world:
        print("No world in this save -- start one with `new`.")
        return
    target = find_place(world, args.place)
    if target is None or "states" not in target:
        print(f"No mutable place matches {args.place!r}.")
        return
    day = state["clock"].day
    if args.action == "add":
        add_place_state(world, target, args.state, day=day)
        print(f"{target['name']}: {args.state} added.")
    elif args.action == "clear":
        if clear_place_state(world, target, args.state, day=day):
            print(f"{target['name']}: {args.state} cleared.")
        else:
            print(f"{target['name']} has no active {args.state} state.")
            return
    else:
        if not args.new_state:
            print("`place-state replace` needs NEW_STATE.")
            return
        replace_place_state(world, target, args.state, args.new_state,
                            day=day)
        print(f"{target['name']}: {args.state} -> {args.new_state}.")
    save(state)


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

    if (pending.get("pause_kind") == "fate"
            and any(getattr(args, flag) for flag in
                    ("drink", "heal", "berserk", "warbreath", "vanish"))):
        print("Fate's bargain allows only `resume` (fight on) or `retreat`.")
        return

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

    log = new_combat_log(continuing=True)
    pause = group_combat(living, pending["foes"], rng, log,
                         pause_triggers=True, fired=pending["fired"],
                         first_round=pending["round"] + 1,
                         actions=actions or None,
                         standing_orders=play_orders(
                             pending.get("normal_pause_used", True)),
                         field=pending.get("field", 0),
                         weather=pending.get("weather", ""))
    if pause is not None:
        pending["round"] = pause.round
        pending["crossings"] = [(k, h.name) for k, h in pause.crossings]
        pending["pause_kind"] = pause.kind
        pending["normal_pause_used"] = True
        print_combat(log)
        print()
        print_pause_menu(state)
        save(state)
        return
    finish_encounter(state, log, pending["foes"], pending["xp"],
                     site=pending["site"], room=pending["room"],
                     quest=pending.get("quest"),
                     crime_take=pending.get("crime"),
                     dead_before=pending.get("dead_before"),
                     align=pending.get("align", "neutral"),
                     mercy=pending.get("mercy"),
                     pursuit=pending.get("pursuit"))


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
    log = new_combat_log(continuing=True)

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
    participants = [h for h in party
                    if h.name not in (pending.get("dead_before") or [])]
    mercy_fired = apply_mercy(
        state, pending["foes"], pending.get("mercy"), log,
        participants=participants,
    )
    wiped = False if mercy_fired else party_wiped(party, log)
    if mercy_fired or wiped or escaped:
        state["pending"] = None
        if escaped and not wiped and not mercy_fired:
            site, room = pending["site"], pending["room"]
            if pending.get("pursuit"):
                # The party broke off its own pursuit: the loose end stays
                # on the books at the runners' current tracks -- the one
                # warm attempt is spent, and the rest is the DM's story.
                rec = loose_end_by_id(state, pending["pursuit"])
                if rec is not None:
                    rec["foes"] = [_entity_to_dict(f)
                                   for f in pending["foes"] if not f.dead]
                    log.append(f"  (loose end {rec['id']} stays on the "
                               f"books -- the party broke off the chase)")
            elif site is not None:
                state.setdefault("rooms", {})[(site, room)] = {
                    "foes": pending["foes"], "day": clock.day}
                standing = sum(1 for f in pending["foes"] if f.alive)
                log.append(f"  ({site} room {room} is left to its "
                           f"{standing} standing foe(s) -- it will remember)")
            else:
                log.append("  (the foes scatter -- an off-script encounter "
                           "is not kept)")
        if not wiped and not mercy_fired:
            if pending.get("mercy") == "hell":
                # Running from the collections visit still RESOLVES it --
                # hell's point is made either way (2026-08-04). The
                # account closes and the job is written off.
                close_hell_account(state, log)
            collect_weapon_quirks(state, log)   # kills before the break-away
            satisfaction_after_fight(party, pending.get("dead_before") or [],
                                     log, fled=True)
            # Out of the fight, wounds and all -- and the pass deals only
            # here too: a hero who broke away can camp, and the vial is
            # worth more unopened than the HP it would buy right now.
            auto_potions(party, log)
            # Fleeing the delivery's interception doesn't un-deliver: if the
            # party stands at the destination, the hand-off happens.
            deliver_if_arrived(state, log)
            append_tally(state, log)
        elif mercy_fired:
            append_tally(state, log)
        print_combat(log)
        save(state)
        if not mercy_fired:
            report_game_over(party, wiped)
        return

    # Run down: the fight resumes at once, the parting damage already taken.
    pause = group_combat(living, pending["foes"], rng, log,
                         pause_triggers=True, fired=pending["fired"],
                         first_round=pending["round"] + 1,
                         standing_orders=play_orders(
                             pending.get("normal_pause_used", True)),
                         field=pending.get("field", 0),
                         weather=pending.get("weather", ""))
    if pause is not None:
        pending["round"] = pause.round
        pending["crossings"] = [(k, h.name) for k, h in pause.crossings]
        pending["pause_kind"] = pause.kind
        pending["normal_pause_used"] = True
        print_combat(log)
        print()
        print_pause_menu(state)
        save(state)
        return
    finish_encounter(state, log, pending["foes"], pending["xp"],
                     site=pending["site"], room=pending["room"],
                     quest=pending.get("quest"),
                     crime_take=pending.get("crime"),
                     dead_before=pending.get("dead_before"),
                     align=pending.get("align", "neutral"),
                     mercy=pending.get("mercy"),
                     pursuit=pending.get("pursuit"))


MAX_HEAL_CAMP_NIGHTS = 14   # `camp --heal` safety valve: HP knits at
                            # ~max_hp/7 a night, so a week-and-change always
                            # reaches full from anywhere


def cmd_camp(args: argparse.Namespace) -> None:
    """One night by default; `camp N` strings several together and `camp
    --heal` camps until every living hero is at their WOUND CEILING
    (2026-07-11; the ceiling since 2026-07-26 -- out here nothing knits a
    wound, so "until whole" stopped being reachable, see dm.md). Each WILDS
    night
    rolls its own visitor and a fight interrupts the stay on the spot --
    a long convalescence in the open is a real gamble, days x risk.

    The visitor is rolled BEFORE the night's recovery (2026-07-26): the
    camp is pitched, the fire draws whatever it draws, and only a night that
    passes undisturbed heals anybody. It used to run the other way round, so
    every night's healing was banked before the fight was rolled and the
    party met its visitor at full HP -- which is exactly the free recovery
    the attrition rework exists to stop handing out."""
    state = load()
    if not require_no_pending(state):
        return
    party, clock = state["party"], state["clock"]
    nights = MAX_HEAL_CAMP_NIGHTS if args.heal else max(1, args.nights)
    clear_sighting(state)
    for _ in range(nights):
        log = CombatLog()
        in_wilds = (state.get("world")
                    and current_area(state)["kind"] != "settlement")
        # A night on the water is a night in the open, but no visitor can
        # walk up to it: the sea has weather and time and nothing else.
        afloat = bool(state.get("world")) and at_sea(state)
        scout = None
        if in_wilds:
            # Survivalist (the ability): a made MIND check picks ground that
            # halves the visitor chance -- and, if the night holds, sleeps
            # the party as warm as a tavern.
            scout = survivalist_ground(party, state["rng"], log)
            weather_note(state)
        print_play(log)
        if in_wilds and not afloat:
            # A night in the wilds is not a night behind walls (2026-07-10):
            # the fire can draw a visitor. A fight cuts the stay short before
            # anyone has slept -- the party fights it as tired as the day
            # left them, and what remains of the night is the player's call
            # again afterward.
            chance = (CAMP_ENCOUNTER_CHANCE / 2 if scout
                      else CAMP_ENCOUNTER_CHANCE)
            if wild_event(state, chance,
                          f"In the night at {current_area(state)['name']}"):
                return
        log = CombatLog()
        # A night behind walls is a BED on the treatment ladder (slice 3b) --
        # it knits a severity. A night in the wilds knits none, which is why
        # `camp --heal` can no longer make anyone whole out there.
        sky = exposure_sky(state)
        roof = (shelter_here(state, log)
                if in_wilds and worldsim.storming(
                    state["world"], state["position"]["land"]) else None)
        _long_rest(party, clock, log, rng=state["rng"], bed=not in_wilds,
                   sky=sky, sheltered=roof is not None)
        if scout is not None:
            survivalist_comfort(party, scout, log)
        storyteller_tale(party, state["rng"], log)
        companions_brew(state, log)
        night_upkeep(state, log)
        print_play(log)
        print_board_clock(state)    # every night camped is a night the job
                                    # was not being done
        if maybe_punish(state):     # posses track a camp too (karma)
            return
        if maybe_enforce(state):    # so do hell's collections (the pact)
            return
        # "Whole" is the CEILING now (slice 3b): out here nothing knits a
        # wound, so once everyone is at their ceiling further nights are
        # pure calendar and the loop stops.
        if args.heal and all(h.dead or h.hp >= h.hp_ceiling for h in party):
            break
    if args.heal:
        hurt = [h for h in party if not h.dead and h.wounds]
        if hurt:
            print(f"  The party breaks camp on day {clock.day} -- as whole "
                  f"as the wilds can make them. Still carrying wounds: "
                  f"{', '.join(h.name.split()[0] for h in hurt)}. A bed, a "
                  f"`healer`, or a salve is what answers those.")
        else:
            print(f"  The party breaks camp whole on day {clock.day}.")
    save(state)


def cmd_tavern(args: argparse.Namespace) -> None:
    """A paid night at the inn (settlements only): long rest plus the one-day
    HP/STA overcharge (rpg.tavern_rest), +1 companion satisfaction, and the
    evening's company -- a fresh set of recruit candidates (the hiring
    surface: rolled once per paid night). The bed's +1 satisfaction is on
    a per-companion cooldown (rpg.SAT_TAVERN_COOLDOWN_DAYS); anyone at the
    end of their patience walks at the morning."""
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
    log = CombatLog()
    if not _tavern_rest(state["party"], state["clock"], state["purse"], log,
                        rng=state["rng"], sky=exposure_sky(state),
                        markup=local_term(state, "lodging")):
        print_play(log)
        return
    storyteller_tale(state["party"], state["rng"], log)
    companions_brew(state, log)
    night_upkeep(state, log)
    clear_sighting(state)
    process_departures(state, log)
    # Candidates are no longer popped unasked (2026-07-13): when the
    # player wants to hire, `recruit` gathers the day's faces.
    maybe_post_wave(state, log)     # tavern talk is where war news lands
    print_play(log)
    print_board_clock(state)    # a bed costs a day like any other
    conquest_news(state)        # tavern talk carries holding news too
    world_news(state)           # and the land's own news with it
    crime_news(state)           # and what hell would like tried
    if maybe_punish(state):     # the Watch knows where the party sleeps
        return
    if maybe_enforce(state):    # and hell holds the mortgage on it
        return
    maybe_assign_task(state)    # hell's mail finds the tavern too
    save(state)


def cmd_downtime(args: argparse.Namespace) -> None:
    """A full day off in a settlement (the satisfaction lever the player
    controls): every companion gains SAT_DOWNTIME, or SAT_DOWNTIME_MATCH
    when the place suits a trait (an interest where it thrives, patriotic
    ground, a capital's temples for the religious). Ends in a free
    settlement night (long rest, the day advances)."""
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
    log = CombatLog()
    log.append(f"  The party takes a day off at {here['name']}.")
    for h in party[1:]:
        if h.dead or not satisfaction_tracked(h):
            continue
        why = downtime_match(h, here)
        if why:
            adjust_satisfaction(h, SAT_DOWNTIME_MATCH, log, why)
        else:
            adjust_satisfaction(h, SAT_DOWNTIME, log, "a day off their feet")
    # A downtime day is spent inside walls, so it counts as a BED night on the
    # treatment ladder (slice 3b): the free settlement rung, one severity a
    # night, and the reason convalescence is a place you stay rather than a
    # number that ticks down anywhere.
    _long_rest(party, clock, log, rng=state["rng"], bed=True,
               sky=exposure_sky(state))
    storyteller_tale(party, state["rng"], log)
    companions_brew(state, log)
    night_upkeep(state, log)
    clear_sighting(state)
    process_departures(state, log)
    maybe_post_wave(state, log)
    print_play(log)
    print_board_clock(state)    # so does an idle one
    conquest_news(state)        # an idle day hears from the holdings
    world_news(state)           # and from the land around them
    crime_news(state)           # and hell fills the idle hands
    if maybe_punish(state):     # an idle day is easy to find the party on
        return
    if maybe_enforce(state):    # for the law and for hell alike
        return
    maybe_assign_task(state)
    save(state)


def heal_the_sick(party, purse, subtype: str, log,
                  markup: float = 1.0) -> int:
    """The healer's day, applied to the ILLNESS half (2026-08-08): the visit
    breaks one disease outright per hero at DISEASE_FEE, and the same tier
    cap that gates wounds gates it -- a village herb-wife can break a cold
    and cannot touch a pneumonia (rpg.DISEASE_REACH). Returns how many
    illnesses were broken. `markup` is the land's `healer` term -- a mill
    town under smog charges what a town full of coughing people will pay."""
    broken = 0
    fee = marked_up(DISEASE_FEE, markup)
    for h in party:
        if h.dead or not h.sick:
            continue
        if purse.gold < fee:
            break
        carrying = next(c.kind for c in h.conditions
                        if c.kind in DISEASE_KINDS)
        got = treat_disease(h, subtype)
        if got is None:
            log.append(f"    The healer can do nothing for {h.name}'s "
                       f"{CONDITION_TAG[carrying]} -- that wants a bigger "
                       f"town.")
            continue
        purse.gold -= fee
        broken += 1
        log.append(f"    {h.name} is treated for {CONDITION_TAG[got]} "
                   f"({fee}g -- HP ceiling {h.hp_ceiling}/"
                   f"{h.max_hp}).")
    return broken


def cmd_healer(args: argparse.Namespace) -> None:
    """A day with the settlement's healer (slice 3b, the treatment ladder's
    ACCESS rung). Costs the day and HEALER_FEE per severity closed, and the
    settlement's TIER decides how far the art reaches -- a village herb-wife
    stops where a capital's surgeons do not. The cap is the gate, so the fee
    never has to scale: what the player is buying is reach, not HP."""
    state = load()
    if not require_no_pending(state):
        return
    here = local_settlement(state)
    if here is None:
        print(f"No healer out here -- the party is at "
              f"{location_line(state)}. In the wilds a wound waits.")
        return
    if occupied_here(state) is not None:
        print(occupation_line(state, here))
        return
    if not any(h.wounds or h.sick for h in state["party"] if not h.dead):
        print("Nobody is carrying a wound or an illness. Save the fee.")
        return
    party, clock, purse = state["party"], state["clock"], state["purse"]
    subtype = settlement_tier(here)
    log = CombatLog()
    log.append(f"  The party spends the day with {here['name']}'s healer.")
    fee_mult = local_term(state, "healer")
    closed, spent = _healer_service(party, purse, subtype, log,
                                    markup=fee_mult)
    broken = heal_the_sick(party, purse, subtype, log, markup=fee_mult)
    if not closed and not broken:
        print("\n".join(log))
        return
    # The visit is a DAY, and a day is what a quest clock spends: it runs
    # the whole night path so the calendar, the board and the morale
    # bookkeeping all see it (a bed under a roof, on top of the treatment).
    _long_rest(party, clock, log, banner="The party sleeps in the healer's "
                                         "care.", rng=state["rng"], bed=True,
               sky=exposure_sky(state))
    storyteller_tale(party, state["rng"], log)
    companions_brew(state, log)
    night_upkeep(state, log)
    clear_sighting(state)
    process_departures(state, log)
    maybe_post_wave(state, log)
    print_play(log)
    print_board_clock(state)
    if maybe_punish(state):
        return
    if maybe_enforce(state):
        return
    maybe_assign_task(state)
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
    dice -- and changes no state (nothing is saved). COMPANIONS only: the
    PC carries no trait sketch (people.py, 2026-08-05), and the beat is
    the party talking around him anyway."""
    state = load()
    party = state["party"]
    companions = [h for h in party[1:] if not h.dead and h.traits]
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
        print(f"  {h.name} ({h.homeland} {h.sex}, {cat}: {val}{mood}) -- "
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


def cmd_sin(args: argparse.Namespace) -> None:
    """The SIN & heat meter, and the DM's off-script sin/penance entry
    (quest work and crime bucket themselves -- this is for improvised
    wickedness or roleplayed virtue: the kicked puppy, the fenced
    heirloom, the coin pressed into the beggar's hand)."""
    state = load()
    k = state["karma"]
    lvl = party_level(state)
    day = state["clock"].day
    if args.kind:
        if args.amount <= 0:
            print("Usage: sin dark N [reason...] / sin penance N "
                  "[reason...] -- N must be positive.")
            return
        log: list[str] = []
        align = "dark" if args.kind == "dark" else "good"
        karma.record_karma(k, args.amount, align, log, lvl, day)
        why = " ".join(args.why)
        word = "Sin" if align == "dark" else "Penance"
        if why:
            # An off-script scene the DM bothered to name is worth
            # remembering; a bare number is bookkeeping, not history.
            remember(state, f"{word} ({args.amount}): {why}")
        print(f"{word} recorded" + (f": {why}" if why else "") + ".")
        for line in log:
            print(line)
        save(state)
    print(f"Sin: {karma.karma_line(k, lvl, day)}")
    print(f"  lifetime: {k['sin_total']} sin, {k['penance_total']} "
          f"penance.")
    if k.get("last_leader"):
        print(f"  Last posse led by {k['last_leader']} (day "
              f"{k['last_punish_day']}).")
    h = effective_heat(state)
    if h > karma.heat(k, lvl, day):
        print(f"  The flag is standing wickedness: "
              f"{len(state.get('holdings') or {})} holding(s) keep the "
              f"heat floor at {h} (see `holdings`).")
    if h >= 1:
        print(f"  Posses arrive at party level +{h} -- at arrivals and "
              f"nights, at most one per {karma.PUNISH_COOLDOWN_DAYS} "
              f"days. Honest quests burn sin 1:1.")


def cmd_conquer(args: argparse.Namespace) -> None:
    """Declare the assault on the settlement the party stands in: builds
    the garrison job at the settlement's fixed garrison level
    (conquest.py). The job is taken like a war wave -- at the settlement,
    by id -- and its last room wears the named defender's face."""
    state = load()
    if not require_no_pending(state):
        return
    world = state.get("world")
    if not world:
        print("No world in this save -- start one with `new`.")
        return
    here = local_settlement(state)
    if here is None:
        print(f"Conquest starts at the walls -- the party is at "
              f"{location_line(state)}. Stand in the settlement you mean "
              f"to take.")
        return
    if occupied_here(state) is not None:
        print(f"{here['name']} lies under the "
              f"{state['story']['aggressor']} yoke -- the war holds it, "
              f"and the war decides. Break the occupation first.")
        return
    if here["key"] in (state.get("holdings") or {}):
        print(f"{here['name']} already flies the party's flag. `holdings` "
              f"reads the ledger; `garrison N` strengthens it.")
        return
    open_q = next((q for q in world["quests"].values()
                   if q.get("conquest") == here["key"]
                   and q["status"] == "open"), None)
    if open_q is not None:
        print(f"The assault is already declared: [{open_q['id']}] "
              f"{open_q['name']} -- `take {open_q['id']}`, then `room`.")
        return
    quest = conquest.build_conquest_quest(world, here, state["rng"])
    save(state)
    role = conquest.DEFENDER_ROLES[land_homeland(world, here["land"])]
    print(f"The party sizes up {here['name']}: the garrison holds the "
          f"keep at L{quest['level']} -- {quest['encounters']} fight(s), "
          f"and the last room is the {role}'s.")
    for line in quest_detail_lines(world, quest, day=state["clock"].day):
        print(line)
    print(f"(`take {quest['id']}` opens the assault. Dark work: every XP "
          f"it pays is sin, and a holding keeps the heat floor up. "
          f"The keep's strongbox pays on the day it falls.)")


def cmd_garrison(args: argparse.Namespace) -> None:
    """Raise levies at the holding the party stands in: gold in, garrison
    heads out. The garrison is an ARMY number, never party members -- it
    absorbs the crown's raids while the party is elsewhere (conquest.py);
    an unguarded holding falls to the first raid."""
    state = load()
    if not require_no_pending(state):
        return
    here = held_here(state)
    if here is None:
        print("Levies are raised at a holding -- stand in a settlement "
              "that flies the party's flag (`holdings` lists them; "
              "`conquer` wins new ones).")
        return
    rec = state["holdings"][here["key"]]
    cap = conquest.GARRISON_CAP[settlement_tier(here)]
    if not args.heads:
        print(f"{here['name']}: garrison {rec['garrison']}/{cap} "
              f"({conquest.GARRISON_HIRE_COST}g a head -- `garrison N` "
              f"hires).")
        return
    n = min(args.heads, cap - rec["garrison"])
    if n <= 0:
        print(f"{here['name']} quarters no more: garrison "
              f"{rec['garrison']}/{cap}.")
        return
    cost = n * conquest.GARRISON_HIRE_COST
    purse = state["purse"]
    if purse.gold < cost:
        print(f"{n} head(s) cost {cost}g -- the purse holds "
              f"{purse.gold}g.")
        return
    purse.gold -= cost
    rec["garrison"] += n
    save(state)
    print(f"{n} levies take the wall at {here['name']} (-{cost}g): "
          f"garrison {rec['garrison']}/{cap}.")


def cmd_holdings(args: argparse.Namespace) -> None:
    """The domain ledger: every settlement under the party's flag, its
    garrison, and the tribute waiting."""
    state = load()
    holdings = state.get("holdings") or {}
    if not holdings:
        print("The party holds nothing yet. `conquer` at a settlement "
              "starts the domain game -- dark work, and the crown "
              "answers.")
        return
    for line in conquest.holdings_lines(state["world"], holdings,
                                        state["clock"].day):
        print(line)
    floor = min(karma.HEAT_CAP, conquest.heat_floor(len(holdings)))
    print(f"(heat floor {floor} while the flag flies. Tribute is "
          f"collected standing in any holding; raids strike where the "
          f"party is not -- the garrison absorbs them or the holding "
          f"falls.)")


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
        # A bought potion belongs to the party, not to the buyer: the
        # quartermaster pass puts it in the right hand (and drinks it if
        # that hand needed it now). A purchase the purse couldn't cover
        # changed nothing, so it wakes nothing.
        if _buy_potion(hero, purse, thing, log,
                       markup=local_term(state, "goods")):
            auto_potions(party, log)
    elif thing in AMMO_LOTS:
        # Ammo by the lot (ranged combat): arrows/bolts by the sheaf,
        # shells and knives by the pair, up to the carry cap.
        _buy_ammo(hero, purse, thing, log,
                  markup=local_term(state, "goods"))
    elif thing.startswith("masterwork "):
        # The master smiths' nonmagical best (2026-07-28): shoppable, but
        # only where master smiths work -- capitals, like spellbooks.
        here = local_settlement(state)
        if here is None or not here.get("capital"):
            print(f"Masterwork steel is sold only in a capital -- the "
                  f"party is at {location_line(state)}.")
            return
        _buy_weapon(hero, purse, thing, log,
                    markup=local_term(state, "steel"))
    elif thing in WEAPONS:
        _buy_weapon(hero, purse, thing, log,
                    markup=local_term(state, "steel"))
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
        if here is None or not here.get("capital"):
            print(f"Spellbooks are sold only in a capital -- the party is "
                  f"at {location_line(state)}.")
            return
        _buy_spellbook(hero, purse, spell_name, log,
                       markup=local_term(state, "goods"))
    elif thing == "meds":
        # The "needs meds" weakness: a dose every MEDS_INTERVAL_DAYS days,
        # compounded only in a capital, or the nightly drain sets in.
        if not has_trait(hero, "needs meds"):
            print(f"{hero.name} has no need of medicine.")
            return
        here = local_settlement(state)
        if here is None or not here.get("capital"):
            print(f"Doses are compounded only in a capital -- the party is "
                  f"at {location_line(state)}.")
            return
        dose = marked_up(MEDS_PRICE, local_term(state, "goods"))
        if purse.gold < dose:
            print(f"Not enough gold for a dose ({purse.gold}g / "
                  f"{dose}g).")
            return
        purse.gold -= dose
        hero.last_dose_day = state["clock"].day
        log.append(f"    {hero.name} buys a dose of their medicine for "
                   f"{dose}g (good for {MEDS_INTERVAL_DAYS} days; "
                   f"purse: {purse.gold}g).")
        adjust_satisfaction(hero, 1, log, "the shakes ease")
    else:
        print(f"Unknown purchase: {thing!r}. Potions: {', '.join(POTION_KINDS)}. "
              f"Weapons: {', '.join(sorted(WEAPONS))}. Ammo: "
              f"{', '.join(sorted(AMMO_LOTS))}. Also: meds, "
              f"book SPELL, masterwork WEAPON (capitals).")
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


def cmd_claim(args: argparse.Namespace) -> None:
    """Take up a quest's weapon reward (the pay-band mode, 2026-07-28):
    the turn-in banked it as pending_reward; this puts it in a hand."""
    state = load()
    if not require_no_pending(state):
        return
    rw = state.get("pending_reward")
    if not rw:
        print("No weapon reward waits to be claimed.")
        return
    hero = find_hero(state["party"], args.hero)
    if hero is None:
        return
    log: list[str] = []
    _equip_weapon(hero, _weapon_from(rw), log)
    grant_starter_ammo(hero, log)
    state["pending_reward"] = None
    print("\n".join(log))
    save(state)


def cmd_armory(args: argparse.Namespace) -> None:
    """The DM's weapon-world inventory (2026-07-28): the famous armory
    (all KNOWN -- rumor is free) and the legendary smiths. In play the
    player hears of these through taverns and notables, not a list."""
    state = load()
    world = state["world"]
    print("\n".join(weaponlib.armory_lines(world["armory"])))
    print()
    print("\n".join(weaponlib.smith_lines(world["smiths"])))
    print("(a commission: `commission SMITH HERO [CHASSIS]` at the "
          "smith's seat. The famous blades are never for sale -- steal, "
          "rob, or quest for them, and their owners wield them.)")
    save(state)


def cmd_commission(args: argparse.Namespace) -> None:
    """Commission a legendary smith (2026-07-28): magic steel at the
    smith's own tier -- never below the pride floor (cap - 1). The one
    way gold buys magic; the profile is the smith's art, not a menu."""
    state = load()
    if not require_no_pending(state):
        return
    party, purse = state["party"], state["purse"]
    world = state["world"]
    hero = find_hero(party, args.hero)
    if hero is None:
        return
    want = args.smith.lower()
    smith = next((s for s in world["smiths"]
                  if want in s["name"].lower()), None)
    if smith is None:
        names = ", ".join(s["name"] for s in world["smiths"])
        print(f"No legendary smith called {args.smith!r}. Smiths: {names}.")
        return
    here = local_settlement(state)
    if here is None or here["key"] != smith["seat"]:
        print(f"{smith['name']} works at {smith['seat_name']} -- the "
              f"party is at {location_line(state)}.")
        return
    chassis = " ".join(args.chassis).lower() if args.chassis else None
    try:
        w, price, days = weaponlib.commission_weapon(
            smith, state["rng"], sp=args.sp, chassis=chassis)
    except ValueError as e:
        print(str(e))
        return
    price = marked_up(price, local_term(state, "steel"))
    if purse.gold < price:
        print(f"Not enough gold for the commission ({purse.gold}g / "
              f"{price}g).")
        return
    purse.gold -= price
    log: list[str] = []
    log.append(f"  {smith['name']} takes the commission: {price}g "
               f"(purse {purse.gold}g), {days} day(s) at the forge.")
    log.append("  (narrate the wait -- camp or downtime advance the "
               "clock; the piece below is what comes off the anvil)")
    for ln in weaponlib.weapon_lines(w):
        log.append("  " + ln)
    _equip_weapon(hero, w, log)
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


def local_prices(state: dict | None) -> dict[str, float]:
    """The priced terms over wherever the party is standing, or an empty
    sheet when there is nowhere and nothing (`prices` is callable with no
    save at all -- it is the DM's reference as well as the player's shop)."""
    if not state or not state.get("world") or not state.get("position"):
        return {}
    worldsim.roll_world(state["world"], state["clock"].day)
    return worldsim.menu_terms(state["world"], state["position"]["land"])


def cmd_prices(args: argparse.Namespace) -> None:
    """The DM's price sheet (2026-07-19), read from the live constants --
    'what does a katana cost' should never mean searching the code (dm.md
    points here). A pure readout: no save is written, and it is callable
    before there is one.

    Since the economy floor (2026-08-09) it is also THE PRICED MENU: every
    number below is what the land the party is standing in charges TODAY,
    with the world's hand on it named at the top. A sheet with no world
    under it prints the catalog, which is what it always printed."""
    try:
        state = load()
    except (OSError, ValueError, KeyError):
        state = None
    terms = local_prices(state)
    goods = terms.get("goods", 1.0)
    steel = terms.get("steel", 1.0)
    fee = terms.get("healer", 1.0)
    bed = terms.get("lodging", 1.0)
    if terms:
        for line in worldsim.menu_lines(state["world"],
                                        state["position"]["land"]):
            print(line)
        print("  (the sheet below is what that comes to at the counter)")
    print("-- SHOP PRICES (gold) --")
    print(f"potion (healing or stamina): {marked_up(POTION_PRICE, goods)}g")
    print(f"surgeon's salve (closes one wound): "
          f"{marked_up(SALVE_PRICE, goods)}g")
    print(f"healer's day: {marked_up(HEALER_FEE, fee)}g per severity, "
          f"{HEALER_DAYS} day -- reach by settlement:")
    for sub, cap in HEALER_TIER_CAP.items():
        reach = ("everything short of a maiming" if cap is None
                 else f"{cap} severity a visit")
        print(f"  {sub}: {reach}")
    print("  (a maiming wants the rank-3 healing spell or an authored "
          "elixir; a bed knits "
          f"{BED_SEVERITY_PER_NIGHT} severity a night for free)")
    print(f"spellbook (capitals only): {marked_up(SPELLBOOK_PRICE, goods)}g")
    print(f"meds dose (capitals only, one per {MEDS_INTERVAL_DAYS} days): "
          f"{marked_up(MEDS_PRICE, goods)}g")
    print(f"tavern night: {marked_up(TAVERN_COST_PER_HERO, bed)}g a head")
    print("ammo, by the lot (to the carry cap):")
    for kind, (lot, price) in AMMO_LOTS.items():
        print(f"  {kind}: {lot} for {marked_up(price, goods)}g "
              f"(cap {AMMO_CAPS[kind]})")
    print("  sling stones: free (the ground is full of them)")
    common = [(n, w) for n, w in WEAPONS.items()
              if w.tier == "plain" and not w.quality]
    quality = [(n, w) for n, w in WEAPONS.items()
               if w.tier == "plain" and w.quality]
    print("common weapons:")
    for name, w in sorted(common, key=lambda kv: (kv[1].value, kv[0])):
        print(f"  {name}: {marked_up(w.value, steel)}g")
    print("quality weapons:")
    for name, w in sorted(quality, key=lambda kv: (kv[1].value, kv[0])):
        print(f"  {name}: {marked_up(w.value, steel)}g")
    print("masterwork weapons (capitals only; +1 attack, durability 5):")
    for name, w in sorted(quality, key=lambda kv: (kv[1].value, kv[0])):
        if not w.range or name == "longbow":
            print(f"  masterwork {name}: "
                  f"{marked_up(w.value * MASTERWORK_PRICE_MULT, steel)}g")
    print("(MAGIC steel is never on a shelf -- quested, robbed, or "
          "COMMISSIONED from a "
          "legendary smith (`armory` lists them; the famous named blades "
          "are never for sale at any price); brewed potions can't be sold)")
    # The sixth outlet's standing half (2026-08-11): the things ONE land
    # sells that nothing else does -- the temple counter, the rain stone, the
    # charm trade, the three lands where a wizard teaches.
    if state and state.get("world") and state.get("position"):
        lines = worldsim.service_lines(state["world"],
                                       state["position"]["land"],
                                       place_kind(state))
        if lines:
            print("")
            print("\n".join(lines))
            print("  (`service` on its own lists these; `lore` is the DM's "
                  "page behind them)")


# --------------------------------------------------------------------------- #
# The services counter and the lore page (2026-08-11, religion & magic)
# --------------------------------------------------------------------------- #

def cmd_service(args: argparse.Namespace) -> None:
    """The priced menu's STANDING half: what this land sells that no other
    does (worldsim.OPTIONS). Bare `service` lists what is on sale here and
    what it costs today; `service WORD` buys it.

    Three things an option can do, and no fourth: a BLESSING (a paid rite,
    worth a point of satisfaction to every companion, on its own cooldown),
    a BOOK (a wizard teaches -- the spellbook gate, opened by a land's own
    organization at that land's price), and a SKY (Tergal's rain stone: the
    weather-worker's priced thumb on the day roll)."""
    state = load()
    if not require_no_pending(state):
        return
    world = state.get("world")
    here = local_settlement(state)
    if not world or here is None:
        print(f"Nobody keeps a counter out here -- the party is at "
              f"{location_line(state)}.")
        return
    polity, day = state["position"]["land"], state["clock"].day
    worldsim.roll_world(world, day)
    kind = place_kind(state)
    if not args.what:
        lines = worldsim.service_lines(world, polity, kind)
        print("\n".join(lines) if lines
              else f"{world['lands'][polity]['name']} is selling nothing "
                   f"out of the ordinary this week.")
        return
    spec = worldsim.option_named(args.what[0])
    if spec is None:
        print(f"No such service: {args.what[0]!r}. `service` lists what is "
              f"on sale here.")
        return
    if polity not in spec["land"]:
        print(f"{spec['name'].capitalize()} is not sold in "
              f"{world['lands'][polity]['name']}.")
        return
    if not worldsim.option_open(world, polity, spec, kind):
        print(f"{spec['name'].capitalize()} is not on offer here today.")
        return
    price = worldsim.option_price(world, polity, spec)
    purse = state["purse"]
    if purse.gold < price:
        print(f"That costs {price}g and the purse holds {purse.gold}g.")
        return
    log: list[str] = []
    if not _pay_service(state, spec, price, args.what[1:], log):
        if log:
            print("\n".join(log))
        return
    print("\n".join(log))
    save(state)


def _pay_service(state: dict, spec: dict, price: int, rest: list,
                 log: list[str]) -> bool:
    """Run one bought option. Returns False (having said why) when the
    transaction cannot happen -- the purse is charged only on the way
    through, so a refused service is never a paid one."""
    world, day = state["world"], state["clock"].day
    polity, purse = state["position"]["land"], state["purse"]
    if spec["does"] == "bless":
        seen = state.setdefault("services", {})
        last = seen.get(spec["key"], -999)
        if day - last < spec["days"]:
            log.append(f"{spec['name'].capitalize()} was bought on day "
                       f"{last} -- it is good for {spec['days']} days, and "
                       f"buying it twice is not how it works.")
            return False
        purse.gold -= price
        seen[spec["key"]] = day
        log.append(f"    The party pays {price}g: {spec['line']}.")
        blessed = 0
        for h in state["party"][1:]:
            if h.dead or not satisfaction_tracked(h):
                continue
            # A religious companion gets what a capital's temples give them
            # on a day off: the rite is the point, not the errand.
            gain = spec["gives"] + (1 if has_trait(h, "religious") else 0)
            adjust_satisfaction(h, gain, log, spec["name"])
            blessed += 1
        if not blessed:
            log.append("    Nobody in the party is here to be comforted by "
                       "it. The rite is performed anyway.")
        log.append(f"    The purse holds {purse.gold}g.")
        return True
    if spec["does"] == "book":
        if len(rest) < 2:
            log.append(f"{spec['name'].capitalize()} teaches a named "
                       f"spell to a named caster: `service "
                       f"{worldsim.option_word(spec)} HERO SPELL` "
                       f"({price}g). Spells: {', '.join(sorted(SPELLS))}.")
            return False
        hero = find_hero(state["party"], rest[0])
        if hero is None:
            return False
        spell = " ".join(rest[1:]).lower()
        if spell not in SPELLS:
            log.append(f"Nobody here teaches {spell!r}. Spells: "
                       f"{', '.join(sorted(SPELLS))}.")
            return False
        # The option owns the price, so the markup is already in it: the
        # book gate is charged at the land's own rate rather than the
        # capital's flat one, which is the whole point of the three
        # organizations being different.
        return _buy_spellbook(hero, purse, spell, log,
                              markup=price / SPELLBOOK_PRICE)
    # "sky": the weather-worker, paid.
    purse.gold -= price
    worldsim.hire_weather(world, polity, day, spec["word"], spec["holds"])
    log.append(f"    The party pays {price}g: {spec['line']}.")
    log.append(f"    The sky over {world['lands'][polity]['name']} is "
               f"bought for {spec['holds']} day(s). The purse holds "
               f"{purse.gold}g.")
    return True


def cmd_lore(args: argparse.Namespace) -> None:
    """The DM's page behind a land (2026-08-11): the standing facts about
    what is believed here and how magic works here, and whatever its
    counters are selling today. Free, costs no day, and the engine never
    reads a word of it -- this is the one surface a FACT has."""
    state = load()
    world = state.get("world")
    if not world:
        print("No world in this save -- start one with `new`.")
        return
    wanted = " ".join(args.land).lower().strip()
    polity = state["position"]["land"] if not wanted else None
    if polity is None:
        hits = [p for p, land in world["lands"].items()
                if p.startswith(wanted) or land["name"].lower().startswith(
                    wanted)]
        if len(hits) != 1:
            print(f"Which land? {', '.join(world['lands'])}")
            return
        polity = hits[0]
    worldsim.roll_world(world, state["clock"].day)
    print("\n".join(worldsim.lore_lines(world, polity)))


def cmd_use(args: argparse.Namespace) -> None:
    state = load()
    if not require_no_pending(state):
        return
    party = state["party"]
    log = CombatLog()
    hero = find_hero(party, args.hero)
    if hero is None:
        return
    if _use_potion(hero, args.kind, log):
        auto_potions(party, log)  # one fewer in the bag: re-share the rest
    print_play(log)
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
    log = CombatLog()
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
    made = _brew(hero, recipe, rng, log)  # a curdled batch still spends the day
    hero.last_brew_day = clock.day
    if made:
        auto_potions(party, log)  # a made batch is the party's, not the still's
    print_play(log)
    save(state)


def cmd_heal(args: argparse.Namespace) -> None:
    """The healing SPELL, between fights (the old Heal ability became
    magic -- rules.md): cast at the healer's trained rank through the
    casting check."""
    state = load()
    if not require_no_pending(state):
        return
    party, rng = state["party"], state["rng"]
    log = CombatLog()
    healer = find_hero(party, args.healer)
    if healer is None:
        return
    target = find_hero(party, args.target)
    if target is None:
        return
    _cast_healing(healer, target, rng, log)
    print_play(log)
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
    quest plus whatever DM-adjudicated divination the scene wants (dm.md)."""
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
    qsites = quest_sites(world, quest)
    site = qsites[cur["site"]]
    if seen_rank >= 3:
        log.append(f"    THE FAR-SEEING -- [{quest['id']}] {quest['name']} "
                   f"is truly level {quest['level']}:")
    sites = (qsites if seen_rank >= 3
             else [site])
    for i, s in enumerate(sites):
        s_i = i if seen_rank >= 3 else cur["site"]
        rooms = site_rooms(world, s)
        for j, room in enumerate(rooms):
            rname, kinds = room["name"], room["kinds"]
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
    for s in settlements(world):
        # By NAME as well as by key since the Areas moved under their Tiles
        # (2026-08-15): a settlement key is now `tile/rNN/cNN/area/...`, so
        # the old key-substring match could never find "prague" again.
        if want in s["key"].lower() or want in s["name"].lower():
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
    if target["key"] == state["position"]["area"]:
        print(f"The party is already at {target['name']}.")
        return
    days = path_days(state["position"]["tile"], target["tile"])
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
    move_party(state, target)
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
    maybe_post_wave(state)      # an arrival is an arrival, however made:
    conquest_news(state)        # the door opens on the same news, sky and
    world_news(state)           # prices a road arrival hears (2026-08-12
    weather_note(state)         # -- the spell used to land in silence)
    price_note(state)
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


def build_parser() -> argparse.ArgumentParser:
    """Every subcommand and its rules. Split out from `main` (2026-08-04,
    session C) so the command SURFACE is testable without running a
    command -- `test_history` reads it to pin the karma -> sin rename."""
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser(
        "new",
        help="start a fresh game (overwrites save): rolls the world, "
             "GENERATES the player character -- male, no trait sketch, "
             "ALWAYS A MAGIC USER, CHA always holds at least one "
             "companion -- in a uniformly selected settlement slot, with "
             "his homeland set from that country and his long-time "
             "companion at his side. It prints a level-fit OPENING HOOK "
             "there to frame the first scene on. No character "
             "pick, no tavern opening (2026-07-13). The party's LEVEL is "
             f"rolled 1-{START_LEVEL_ROLL_MAX} unless `--level N` fixes "
             "it (2026-08-05): above level 1 the pair arrives with the "
             "career those levels bought -- points spent by doctrine, "
             "quality steel, a job-reward weapon, spellbooks and a purse. "
             "THE HELL PACT rides every new save by default "
             "(2026-07-19): the PC is a low-ranking employee of Hell "
             "-- assignments, enforcement, `task`/`bribe`; dm.md, The "
             "dark path. `--no-pact` starts the old neutral game.")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--level", type=int, default=None,
                   help=f"start the party at this level (1-{LEVEL_CAP}); "
                        f"omitted, the level is ROLLED 1-"
                        f"{START_LEVEL_ROLL_MAX}")
    p.add_argument("--no-pact", action="store_true",
                   help="a neutral adventurer: no pact, no assignments "
                        "(the pre-2026-07-19 game)")
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
             "once (its first wounds crossing, or Fate's bargain with only "
             "fight on/retreat); every later crossing is "
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

    p = sub.add_parser(
        "camp",
        help="long rest: full STA, weekly HP tick UP TO THE WOUND CEILING, "
             "advances a day -- the "
             "day's ONLY recovery step (the short rest is gone). `camp N` "
             "strings N nights together; `camp --heal` camps until every "
             "living hero is at their ceiling. A night behind SETTLEMENT "
             "walls also knits one wound severity; a night in the wilds "
             "knits none. A night camped in "
             "the WILDS (not at a settlement) rolls its visitor BEFORE the "
             "night's recovery "
             f"(~{int(CAMP_ENCOUNTER_CHANCE * 100)}%% PER NIGHT, the "
             f"road's table): a fight cuts the stay short and nobody heals "
             f"that night.")
    p.add_argument("nights", type=int, nargs="?", default=1,
                   help="how many nights (default 1)")
    p.add_argument("--heal", action="store_true",
                   help="camp until every living hero is at their wound "
                        "ceiling (out in the wilds that is as whole as they "
                        "get -- wounds want a bed, a healer, or a salve)")
    p.set_defaults(func=cmd_camp)

    p = sub.add_parser(
        "tavern",
        help=f"a paid night at the inn (settlements only, "
             f"{TAVERN_COST_PER_HERO}g per living member): a full long rest "
             f"plus a ONE-DAY OVERCHARGE -- everyone wakes with HP and STA "
             f"+{int(TAVERN_OVERCHARGE * 100)}%% of max (min 1) ABOVE their "
             f"caps; the excess can't be healed back and fades at the next "
             f"night's rest. Also +1 companion satisfaction, at most once "
             f"every {SAT_TAVERN_COOLDOWN_DAYS} days per companion. "
             f"(Hiring candidates "
             f"are `recruit`'s business, on request -- the tavern never "
             f"pops them unasked.)")
    p.set_defaults(func=cmd_tavern)

    p = sub.add_parser(
        "downtime",
        help="a full day off in a settlement: +1 satisfaction to every "
             "companion (+2 where the place suits a trait -- an interest "
             "where it thrives, patriotic ground, a capital's temples), "
             "then a free night (long rest, the day advances). "
             "The deliberate morale lever -- it costs a day, and days are "
             "what a quest clock spends.")
    p.set_defaults(func=cmd_downtime)

    p = sub.add_parser(
        "healer",
        help=f"a day with the settlement's healer (the wound system's "
             f"ACCESS rung): {HEALER_FEE}g per severity closed, worst wound "
             f"first across the whole party, and it costs the day like any "
             f"other night. How far the art reaches is set by the "
             f"SETTLEMENT, not the purse -- village "
             f"{HEALER_TIER_CAP['village']} severity a visit, town "
             f"{HEALER_TIER_CAP['town']}, "
             f"a capital everything short of a maiming. A maiming wants the "
             f"rank-3 healing spell or an authored elixir; a free bed knits "
             f"{BED_SEVERITY_PER_NIGHT} severity a night on its own.")
    p.set_defaults(func=cmd_healer)

    p = sub.add_parser(
        "board",
        help="the DM's LOCAL quest inventory (2026-07-12: in play there is "
             "no board -- each job belongs to its GIVER, and asking around "
             "funnels to that person in one message, see dm.md). Rows show "
             "level (straight), shape, pay, and the giver; plus notables "
             "in town, WORD FROM AROUND THE LAND (other open jobs in this "
             "land), and the war's status. Only local jobs can be taken "
             "here. `board all` / `board NAME` is the wider DM overview. "
             "(There is no dark board since 2026-08-04: hell's own work "
             "arrives as pinned ASSIGNMENTS -- `task` -- and freelance "
             "crime is not a posting at all.)")
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
        help="the known world: lands and known areas, with settlement job "
             "counts and the party's position")
    p.set_defaults(func=cmd_map)

    p = sub.add_parser(
        "world",
        help="the DM inventory of the world layer (worldsim.py): every "
             "land's wealth band, the states it holds, the states its "
             "trade edges derive, the card standing over it and how deep "
             "its crisis deck still is. The player's half of this is the "
             "state line on `map` and the news at arrivals.")
    p.set_defaults(func=cmd_world)

    p = sub.add_parser(
        "look",
        help="the local view: stored description, known state, child places, "
             "services, and visible Room contents. --dm prints the complete "
             "place record including hidden facts and generation data")
    p.add_argument("--dm", action="store_true",
                   help="full current-place fact record for DM eyes")
    p.set_defaults(func=cmd_look)

    p = sub.add_parser(
        "go",
        help="move locally to a known site or room; costs no day (`travel` "
             "is the day-scale move between areas)")
    p.add_argument("dest", nargs="+", help="local site or room (substring)")
    p.set_defaults(func=cmd_go)

    p = sub.add_parser(
        "back",
        help="move one local level outward: room to site, or site to area")
    p.set_defaults(func=cmd_back)

    p = sub.add_parser(
        "travel",
        help=f"walk the map grid. `travel north|south|east|west` is the "
             f"primitive: one cardinal Tile edge, 1 day east/west, 2 days "
             f"north/south, +1 if either end is mountain (sea costs the "
             f"base and nothing more). `travel R09C18` or `travel NAME` "
             f"follows the cheapest route to a coordinate, a known "
             f"settlement or a historical city, edge by edge. Every travel "
             f"day is a camp night (overnight recovery -- travel heals); "
             f"each LAND edge risks a road encounter rolled at the Tile "
             f"just reached, off THAT country's table "
             f"(~{int(TRAVEL_ENCOUNTER_CHANCE * 100)}%%/day, ANY level -- "
             f"the higher the rarer; foes far above the party are usually "
             f"spotted at range first, but can ambush, and ordinary "
             f"trouble runs the NOTICE CONTEST: party MIND vs their "
             f"senses, over each side's conspicuousness -- spotted, "
             f"ambushed, or met square on the open field). A fight or a "
             f"sighting stops a route AT THE TILE REACHED, never back at "
             f"its origin. SEA edges spend time, weather and recovery and "
             f"roll no encounter at all.")
    p.add_argument("dest", nargs="+",
                   help="direction, coordinate, or known place (substring)")
    p.set_defaults(func=cmd_travel)

    p = sub.add_parser(
        "explore",
        help=f"a day afield in THIS Tile's countryside (from a settlement "
             f"the party walks out into it first): reveals the natural "
             f"Area's next ordinary Site, three to a Tile. A new place "
             f"pays {EXPLORE_XP} XP and persists; revisits do not. Camps "
             f"rough (overnight recovery), and beats more "
             f"bushes than the road "
             f"({int(EXPLORE_ENCOUNTER_CHANCE * 100)}%% encounter chance; "
             f"open water rolls none)")
    p.set_defaults(func=cmd_explore)

    p = sub.add_parser(
        "house",
        help="materialize one ordinary house in the current settlement: a "
             "persistent resident, Main Room, zero to two optional Rooms, "
             "and culture-compatible visible contents")
    p.set_defaults(func=cmd_house)

    p = sub.add_parser(
        "place-state",
        help="DM place mutation: add, replace, or clear a persistent state "
             "on a Land, Area, Site, or Room; records a day-stamped world "
             "event")
    p.add_argument("action", choices=("add", "replace", "clear"))
    p.add_argument("place", help="place name or ID substring")
    p.add_argument("state", help="state to add/clear, or old state")
    p.add_argument("new_state", nargs="?", default=None,
                   help="replacement state (replace only)")
    p.set_defaults(func=cmd_place_state)

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
        "pursue",
        help="run down a rout's survivors (the loose-ends record, "
             "2026-08-08) while the trail is WARM: same day, same area, "
             "no night slept; ONE attempt per rout. 2d6 + best MIND vs "
             "the runners' chase DEX (+2 trackers if any runner is "
             "wounded). Success re-opens the fight at their fled state, "
             "at the party's preferred range; failure loses the trail "
             "(no day spent -- the record stays). Pays WILD rates: the "
             "field already banked its share. `--stage` is the DM's "
             "cold-trail valve: re-open a fight off any loose end, no "
             "gate, no roll, the survivors healed by the days passed.")
    p.add_argument("id", nargs="?", default=None,
                   help="loose-end id (default: the newest warm one here; "
                        "`status` names the latest, `look --dm` lists "
                        "local ones)")
    p.add_argument("--stage", action="store_true",
                   help="DM: stage the re-encounter the story found -- "
                        "skips the warm gate and the tracking roll")
    p.set_defaults(func=cmd_pursue)

    p = sub.add_parser(
        "show",
        help="one quest in full: description, sites, rooms, and what holds "
             "each room (by skinned display name). Levels are exact; --dm "
             "also reveals surprise complications for planning.")
    p.add_argument("quest", help="quest id (q07, or just 7)")
    p.add_argument("--dm", action="store_true",
                   help="include DM-only surprise complications")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser(
        "take",
        help="make a quest ACTIVE (the party must be at its origin area) and "
             "reveal its first site. `go SITE`, then `room`, works its "
             "encounters in order. Switching quests preserves progress.")
    p.add_argument("quest", help="quest id (q07, or just 7)")
    p.set_defaults(func=cmd_take)

    p = sub.add_parser(
        "turnin",
        help="hand a WORK-DONE job back to its giver (2026-08-08: a quest "
             "is paid where the giver stands, not where the last body "
             "falls). Gated on standing in the giver's settlement area; "
             "run it as the return scene (dm.md). Pays ALL the gold and "
             "the turn-in XP tranche, banded by TODAY -- the road home is "
             "inside the clock -- plus the CHA talk-up, the reward "
             "weapon, +1 companion satisfaction, and the epilogue. "
             "(Deliveries pay at the destination; war waves, conquest, "
             "hell and dark work pay at work-done.)")
    p.add_argument("quest", help="quest id (q07, or just 7)")
    p.add_argument("--here", action="store_true",
                   help="DM valve for edge fiction (a dead giver, an "
                        "occupied town): pay where the story says")
    p.set_defaults(func=cmd_turnin)

    p = sub.add_parser(
        "room",
        help="resolve the ACTIVE quest's next encounter at its current site "
             "(enter it with `go SITE` first). Clearing the last site is "
             "WORK DONE: the field XP lands and the gold waits at the "
             "giver (`turnin`). A fled room is "
             "re-fought against its recorded survivors. CAPER quests "
             "(dark work, 2026-07-19): a DEED site first rolls the PC's "
             "2d6+stat vs its DC -- a make does the site clean (full "
             "lump, no fight), a miss botches it into the fight with "
             "witnesses; a TWIST site first prints its terms -- `room` "
             "again refuses and fights, `settle` accepts.")
    p.set_defaults(func=cmd_room)

    p = sub.add_parser(
        "settle",
        help="take a TWIST's terms (the caper structure, dark quests): "
             "the current site closes WITHOUT a fight at the twist's "
             "pay fraction of its lump (usually half). Fighting on "
             "(`room`) refuses the terms and keeps the full pay on the "
             "table.")
    p.set_defaults(func=cmd_settle)

    p = sub.add_parser(
        "task",
        help="the hell pact's ledger: the current ASSIGNMENT (with its "
             "grace clock and full detail), the bribe window, the next "
             "pin, assignments completed and written off. Assignments "
             "are occult quests hell PINS to the PC's odd levels (1, 3, "
             "5 ... 19 -- ten a career, dealt off a shuffled deck), "
             "leveled at the party with the margin of error upward and "
             "delivered at settlements. Taking one stamps a visible "
             "completion window and stops enforcement; untaken past "
             "grace or taken past window it goes PAST DUE -- one "
             "warning, then ONE collections visit, then hell writes the "
             "job off and waits for the next pin.")
    p.set_defaults(func=cmd_task)

    p = sub.add_parser(
        "bribe",
        help=f"grease hell's local hand: {karma.BRIBE_GOLD_PER_LEVEL} g "
             f"x party level buys {karma.BRIBE_DAYS} days of NO new "
             f"assignments and NO enforcement. An open assignment isn't "
             f"cancelled -- its grace runs fresh from the bribe's end.")
    p.set_defaults(func=cmd_bribe)

    p = sub.add_parser(
        "forge",
        help="DM quest creator: generate a quest at a level/shape/foe-mix of "
             "your choosing (same builder as worldgen) and place its sites "
             "in an area. Defaults to the current area.")
    p.add_argument("--level", type=int, required=True)
    p.add_argument("--places", type=int, default=1, choices=(1, 2, 3),
                   help="how many sites the job spans (default 1 -- only "
                        "where the fiction genuinely moves)")
    p.add_argument("--encounters", type=int, default=1, choices=(1, 2, 3),
                   help="fights in the whole job (default 1; floored at "
                        "--places)")
    p.add_argument("--kinds", required=True,
                   help="comma-separated catalog foe kinds (the quest's pool)")
    p.add_argument("--name", required=True)
    p.add_argument("--area", default=None,
                   help="where its sites belong (default: current area)")
    p.add_argument("--dark", action="store_true",
                   help="forge a SHADOW job (karma & heat): bad-karma "
                        "XP, the dark gold premium")
    p.add_argument("--days", type=int, default=0,
                   help="give the job a WINDOW this many days out (the "
                        "board's clock, quests.py). Omit for a timeless "
                        "job -- the DM's improvised work has no deadline "
                        "unless the fiction gives it one.")
    p.add_argument("--proof", nargs="?", const="proof of the kill",
                   default=None, metavar="TOKEN",
                   help="forge a BOUNTY: the giver pays on this token "
                        "(default 'proof of the kill') -- the final "
                        "site's roster must be DEAD before the job is "
                        "done; driven off is not done")
    p.set_defaults(func=cmd_forge)

    p = sub.add_parser(
        "award",
        help="off-script bonus: award gold + an XP lump by hand (board "
             "quests pay themselves -- this is for improvised scenes). "
             "--dark buckets the XP as SIN, --good as penance "
             "(karma & heat); plain awards touch neither.")
    p.add_argument("gold", type=int)
    p.add_argument("xp", type=int)
    p.add_argument("name")
    p.add_argument("--dark", action="store_true",
                   help="the scene was wicked: its XP is sin")
    p.add_argument("--good", action="store_true",
                   help="the scene was virtuous: its XP burns sin")
    p.set_defaults(func=cmd_award)

    p = sub.add_parser(
        "sin",
        help="the SIN & heat meter (the villain layer): current sin, "
             "heat, the lifetime ledgers, the last posse's leader. "
             "`sin dark N [reason]` / `sin penance N [reason]` record an "
             "off-script sin or penance by hand -- quest work and crime "
             "bucket themselves; this is for improvised wickedness (the "
             "kicked puppy) or roleplayed virtue. Guideline sizes: petty "
             "~15, serious ~50, an outrage ~100+ (one heat step is 100 x "
             "party level). A named reason lands in ui/history.txt.")
    p.add_argument("kind", nargs="?", choices=("dark", "penance"),
                   default=None)
    p.add_argument("amount", nargs="?", type=int, default=0)
    p.add_argument("why", nargs="*", default=[])
    p.set_defaults(func=cmd_sin)

    p = sub.add_parser(
        "case",
        help="CASE a crime, free and honest (the crime layer, "
             "2026-08-04). No argument lists what has a mark where the "
             "party stands, grouped by shape (petty / deed / force), "
             "with hell's current suggestions. `case KEY` prints that "
             "category's local MARK: who, at what level, what the take "
             "is worth, the check, and the protection that will have to "
             "be fought. The mark is seeded per settlement, day and "
             "category -- committing today faces exactly what the "
             "casing showed, and tomorrow rolls a new one. Casing costs "
             "nothing and is never wrong.")
    p.add_argument("category", nargs="?",
                   help="a category key or name (`case` lists them)")
    p.add_argument("--npc", default=None,
                   help="case a NAMED victim instead of the local slot "
                        "(a giver, a notable, anyone the fiction put on "
                        "the table)")
    p.add_argument("--level", type=int, default=None,
                   help="--npc's level: the DM assigns the band, and it "
                        "fixes both the take and the protection")
    p.set_defaults(func=cmd_case)

    p = sub.add_parser(
        "crime",
        help="COMMIT a crime against the local mark (the crime layer, "
             "2026-08-04): no giver, no posting, no turn-in -- the PC "
             "does the thing and keeps what follows. PETTY does it or "
             "fumbles it and never fights (flat small sin, coin in "
             "pennies). A DEED rolls 2d6+stat vs its DC: a make takes it "
             "clean, a miss botches it into the protection with "
             f"witnesses (+{crime.WITNESS_SIN} sin). FORCE skips "
             "the check and goes through the protection to the take. "
             "Difficulty is the MARK's level, never a gate: nothing is "
             "locked, and nothing scales to the party. All the XP is "
             "sin; a category repeated inside "
             f"{crime.MONOTONY_WINDOW} days pays less of it (the coin "
             "never depreciates), and a first-ever category pays "
             f"x{crime.FIRST_TIME_MULT:g}.")
    p.add_argument("category", help="a category key or name (`case` lists "
                                    "them)")
    p.add_argument("--npc", default=None,
                   help="rob/attack a NAMED victim instead of the local "
                        "slot")
    p.add_argument("--level", type=int, default=None,
                   help="--npc's level (the DM assigns the band)")
    p.set_defaults(func=cmd_crime)

    p = sub.add_parser(
        "crimes",
        help="the CRIME SHEET (2026-08-04, session C -- the `prices` "
             "pattern for the dark side): the whole catalogue available "
             "where the party stands, each row quoting what its mark "
             "BAND is worth (gold, sin/XP with the current multiplier), "
             "the check it asks for and the protection it wears -- then "
             "the party's tally of sin and hell's current suggestions. "
             "`case KEY` reads TODAY'S rolled mark exactly; this reads "
             "the band, so it answers 'what is worth doing here' in one "
             "screen. A pure readout: no save touched.")
    p.set_defaults(func=cmd_crimes)

    p = sub.add_parser(
        "conquer",
        help="declare the assault on the settlement the party stands in "
             "(the domain layer, 2026-07-27): builds the garrison job at "
             "the settlement's FIXED garrison level (village 3-5, town "
             "6-10, capital 11-15 -- rolled once, stable, geography not "
             "gate), capped by a named defender. Take it like a war wave "
             "(`take QID`), fight it with `room`; the last room's fall "
             "flips the tag. Dark work: all its XP is sin, and "
             "every holding keeps the heat floor up.")
    p.set_defaults(func=cmd_conquer)

    p = sub.add_parser(
        "garrison",
        help=f"raise levies at the holding the party stands in: "
             f"{conquest.GARRISON_HIRE_COST}g a head, capped by the "
             f"settlement (village {conquest.GARRISON_CAP['village']} / "
             f"town {conquest.GARRISON_CAP['town']} / capital "
             f"{conquest.GARRISON_CAP['capital']}). The garrison is an "
             f"ARMY number, never party members: raids resolve heads "
             f"against heads while the party is elsewhere -- an unguarded "
             f"holding falls to the first raid. No argument shows the "
             f"local count.")
    p.add_argument("heads", nargs="?", type=int, default=0)
    p.set_defaults(func=cmd_garrison)

    p = sub.add_parser(
        "holdings",
        help="the domain ledger: every settlement under the party's flag, "
             "garrison strength, tribute rates and what waits in the "
             "chests. Tribute is collected standing in any holding; the "
             "heat floor rises one step per holding.")
    p.set_defaults(func=cmd_holdings)

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
        "service",
        help="the priced menu's STANDING half (2026-08-11): what THIS land "
             "sells that no other does -- a burial or a blessing at the "
             "temple, a pilgrim badge, a burial club's dues, a charm and "
             "its printed policy, a hall blessing, Tergal's rain stone, "
             "and the three lands where a wizard will teach. Bare "
             "`service` lists what is on sale here at today's prices; "
             "`service WORD` buys it (a teaching wants `service WORD HERO "
             "SPELL`)")
    p.add_argument("what", nargs="*",
                   help="the service, and whatever it needs (a teaching "
                        "takes a hero and a spell)")
    p.set_defaults(func=cmd_service)

    p = sub.add_parser(
        "lore",
        help="the DM's page behind a land (2026-08-11): the standing facts "
             "about what is worshipped here and how magic works here, plus "
             "whatever its counters are selling. Free, costs no day, and "
             "the engine never reads a word of it. Defaults to the land "
             "the party is standing in")
    p.add_argument("land", nargs="*", help="a land, by name or key")
    p.set_defaults(func=cmd_lore)

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
        "claim",
        help="take up a quest's WEAPON reward (the pay-band mode: some "
             "jobs pay their turn-in lump as steel instead of gold -- the "
             "board row says so). The piece waits with the giver until "
             "claimed; claiming equips it on the spot.")
    p.add_argument("hero")
    p.set_defaults(func=cmd_claim)

    p = sub.add_parser(
        "armory",
        help="the DM's weapon-world inventory: the world's famous magic "
             "weapons (all KNOWN -- who carries each, where the rest "
             "lie; steal, rob, or quest for them, never buy) and the "
             "three legendary smiths with their tiers and prices. In "
             "play this reaches the player as rumor, not a list.")
    p.set_defaults(func=cmd_armory)

    p = sub.add_parser(
        "commission",
        help="commission a legendary smith for a MAGIC weapon -- the one "
             "way gold buys magic steel. Party must stand at the smith's "
             "seat; the smith works only at their own tier (the pride "
             "floor: nothing below cap-1). The profile that comes off "
             "the anvil is the smith's art, not a menu.")
    p.add_argument("smith", help="the smith's name (see `armory`)")
    p.add_argument("hero", help="who the piece is fitted for (equips on "
                                "the spot; narrate the forging days)")
    p.add_argument("chassis", nargs="*",
                   help="optional chassis (e.g. katana) -- must fit the "
                        "smith's style")
    p.add_argument("--sp", type=int, default=None,
                   help="commission tier in severity-points (default: the "
                        "smith's cap; the floor is cap-1)")
    p.set_defaults(func=cmd_commission)

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
        help="rewrite party/map/history and COMMIT every existing "
             "ui/ page, including the last-fight logs and the "
             "DM-written scene/transcript pages. Run at the END of every "
             "DM message, after writing ui/scene.md (dm.md, The scene "
             "page); committing unchanged pages is a harmless no-op.")
    p.set_defaults(func=cmd_sheet)

    return ap


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
