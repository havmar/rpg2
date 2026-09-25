"""Contract suite for THE PLAYER'S PAGE (2026-09-25, page-plan.md): part 1
(session 1) the projection (`page.py`) and the session refactors under it;
part 2 (session 2) the fights kept, `publish.py`, the page's record and
the keeper's move check.

What is pinned here:

- **The projection.** A fresh `new` projects into the five singletons,
  each JSON, under the store's 256 KiB, with the contract's fields; the
  state's coord is the party's Tile; each `text` is its ui page exactly.
- **Secrets never cross.** No `rng` or `world` key; no untaken posting, no
  unknown settlement, no roster of a room the party has not entered; the
  map's places are the known slots and the gates, its rows the bare grid.
- **The pause menu.** `pause_menu_data` plus its printer print the old menu
  byte for byte (a copy of the old printer is kept below as the witness),
  for a wounds pause, a Fate pause, and a real paused fight.
- **The move contract.** `clean_move` reads data only; `pause_args` gives
  the argv `resume`/`retreat` would take and refuses what they refuse,
  plus a stale fight, a Fate pause with an action, and the substring trap.
- **The chronicle entry** and **the level-up** block.
- **RPG2_HOME**: the game runs under another base directory, and `sheet`
  there commits nothing.
- **Part 2.** A fight's queue entry is its player log exactly, cut at the
  round spans, with its outcome; a paused fight's second half is its own
  entry; two fights are two entries. `publish.py` (by subprocess, under a
  temp RPG2_HOME) pins every `game/` write, deletes every move read,
  numbers the fights after `lastFight` with `continues` on a second half,
  keeps the page's record and the transcript on `--sent`, and stops at 50
  writes. `page.py moves` prints the argv, a refusal, a superseded move,
  a non-move. `new` drops the record and the queue.

Run:  python -m unittest -v test_page.py
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import random
import re
import subprocess
import sys
import shlex
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import page
import places
import rpg
import session
import sites

DOC_MAX = 256 * 1024
REPO = Path(__file__).resolve().parent

# --------------------------------------------------------------------------- #
# The sandbox: every path the session writes, pointed at a throwaway dir
# --------------------------------------------------------------------------- #

_PATHS = {
    "STATE_PATH": "save.json",
    "UI_DIR": "ui",
    "PARTY_SHEET_PATH": "ui/party.txt",
    "MAP_SHEET_PATH": "ui/map.txt",
    "HISTORY_SHEET_PATH": "ui/history.txt",
    "FIGHT_SHORT_PATH": "ui/fight-short.txt",
    "FIGHT_DETAILED_PATH": "ui/fight-detailed.txt",
}


@contextlib.contextmanager
def sandbox():
    """Point the session's save and every ui page at a throwaway directory
    -- a suite must never overwrite the playthrough."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "ui").mkdir()
        saved = {name: getattr(session, name) for name in _PATHS}
        for name, rel in _PATHS.items():
            setattr(session, name, root / rel)
        try:
            yield root
        finally:
            for name, value in saved.items():
                setattr(session, name, value)


def run(*argv: str) -> str:
    """One session command in the current sandbox; what it printed."""
    args = session.build_parser().parse_args(list(argv))
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        args.func(args)
    return out.getvalue()


def strings(doc, keys: bool = True):
    """Every string in a document, keys included."""
    if isinstance(doc, dict):
        for k, v in doc.items():
            if keys:
                yield k
            yield from strings(v, keys)
    elif isinstance(doc, list):
        for v in doc:
            yield from strings(v, keys)
    elif isinstance(doc, str):
        yield doc


def all_keys(doc):
    if isinstance(doc, dict):
        for k, v in doc.items():
            yield k
            yield from all_keys(v)
    elif isinstance(doc, list):
        for v in doc:
            yield from all_keys(v)


def ui_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


# --------------------------------------------------------------------------- #
# The old printer, kept verbatim as the witness for the byte-identical test
# --------------------------------------------------------------------------- #

def old_print_pause_menu(state: dict) -> None:
    """session.print_pause_menu as it stood before pause_menu_data (the
    2026-09-25 split), names qualified, otherwise untouched."""
    print = session.print                      # noqa: A001 -- as session's
    s = session
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
        print(f"  {h.name.split()[0]}{tag}: {h.hp_state} "
              f"HP {h.hp}/{h.hp_ceiling}"
              + (f" (max {h.max_hp})" if h.wounds else "")
              + f" STA {h.cur_sta}/{h.sta} Power {h.cur_power}/{h.power}")
        pens = []
        if h.wound_penalty:
            pens.append(f"hurt -{h.wound_penalty}")
        if h.spent:
            pens.append(f"Spent -{s.SPENT_PENALTY}")
        elif h.winded:
            pens.append(f"Winded -{s.WINDED_PENALTY}")
        if pens:
            print(f"    ({', '.join(pens)} to rolls)")
        for ctag in s.condition_tags(h):
            print(f"    [{ctag}]")
        for wtag in s.wound_tags(h):
            print(f"    - {wtag}")
        print(f"    healing x{h.items.get('healing', 0)}, "
              f"stamina x{h.items.get('stamina', 0)}")
    if fate_pause:
        print("  The player's call:")
    else:
        print("  The player's call (a pause action "
              f"costs the round: defend at -{s.PAUSE_ACTION_DEF_PENALTY}):")

    def option(cmd: str, desc: str) -> None:
        print(f"    {cmd}")
        print(f"      {desc}")

    option("resume", "fight on")
    if not fate_pause:
        option("resume --drink HERO",
               f"stamina draught, +{s.STAMINA_DRAUGHT_RESTORE} STA now")
        option("resume --heal HERO",
               f"healing potion, +{s.HEALING_POTION_RESTORE} HP now "
               f"(the wound penalty lightens)")
        if any(not h.dead and "berserk" in h.abilities for h in party):
            option("resume --berserk HERO",
                   f"{s.BERSERK_HP_COST} HP -> +{s.BERSERK_STA_GAIN} STA "
                   f"(the wound penalty deepens; knowers only)")
        if any(not h.dead and "war_breath" in h.abilities for h in party):
            option("resume --warbreath HERO",
                   f"{s.WAR_BREATH_POWER_COST} Power -> "
                   f"+{s.WAR_BREATH_STA_GAIN} STA (knowers only)")
        if any(not h.dead and h.spell_rank("invisibility") >= 2
               for h in party):
            option("resume --vanish HERO",
                   f"{s.VANISH_POWER_COST} Power: fade from the melee "
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
               f"({s.TELEPORT_ESCAPE_COST} Power; a fizzled door falls "
               f"back to the honest retreat)")
    smoker = next((h for h in party
                   if not h.dead and h.items.get("smoke", 0) > 0), None)
    if smoker is not None:
        option(f"retreat --smoke {smoker.name.split()[0]}",
               f"smoke vial: NO parting blows, but the chase still rolls "
               f"({smoker.items['smoke']} left)")


def printed(fn, *args) -> str:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        fn(*args)
    return out.getvalue()


# --------------------------------------------------------------------------- #
# Fixtures: a fresh game, a crafted pause on it, and a real paused fight
# --------------------------------------------------------------------------- #

def fresh(seed: int = 3) -> dict:
    """`new --seed S --level 1` in the current sandbox, loaded."""
    run("new", "--seed", str(seed), "--level", "1")
    return session.load()


def crafted_pause(state: dict, kind: str = "normal", *,
                  foes: tuple = ("skeleton", "wolf")) -> dict:
    """A paused fight laid on a loaded state by hand: every branch of the
    menu has something to print (a wounded, winded PC with a condition, a
    companion down, a skeleton that does not pursue)."""
    rng = random.Random(7)
    pc, companion = state["party"][0], state["party"][1]
    rpg.add_wound(pc, "arm", 3, 2)
    pc.hp = max(1, pc.hp_ceiling - 3)
    pc.cur_sta = 1
    rpg.apply_condition(pc, "poison", power=1, rounds=None)
    companion.hp = 0
    companion.down = True
    state["pending"] = {
        "foes": [sites.make_foe(k, i + 1, rng) for i, k in enumerate(foes)],
        "fired": set(),
        "round": 3,
        "crossings": ([("fate", pc.name)] if kind == "fate"
                      else [("wounds", pc.name), ("stamina", pc.name)]),
        "xp": 0, "site": None, "room": None, "pause_kind": kind,
        "normal_pause_used": kind == "normal",
    }
    return state


def real_pause() -> dict:
    """A fight that really paused, in the current sandbox: the first seed
    whose party a troll drives to the pause."""
    for seed in range(1, 12):
        fresh(seed)
        run("fight", "1", "--type", "troll")
        state = session.load()
        if state["pending"]:
            return state
    raise AssertionError("no seed in 1..11 paused against one troll")


# --------------------------------------------------------------------------- #
# 1-3. The projection, its fidelity, and its secrets
# --------------------------------------------------------------------------- #

class TheProjection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with sandbox() as root:
            cls.state = fresh(3)
            cls.opening = cls.state["world"]["opening_quest"]
            cls.took = run("take", cls.opening)
            run("sheet")
            cls.state = session.load()
            cls.view = page.player_view(cls.state)
            cls.party_txt = ui_lines(root / "ui" / "party.txt")
            cls.map_txt = ui_lines(root / "ui" / "map.txt")
            cls.history_txt = ui_lines(root / "ui" / "history.txt")

    def test_the_five_singletons_are_json_and_small(self):
        self.assertEqual(tuple(self.view), page.SINGLETONS)
        for path, doc in self.view.items():
            text = json.dumps(doc)
            self.assertLess(len(text.encode()), DOC_MAX, path)
            self.assertEqual(json.loads(text), doc, path)
            self.assertEqual(doc["v"], page.VIEW_VERSION, path)
            text.encode("ascii")            # the page's copy is ASCII

    def test_the_state_says_where_the_party_stands(self):
        st = self.view["game/state"]
        tile = self.state["world"]["tiles"][self.state["position"]["tile"]]
        self.assertEqual(st["coord"],
                         places.tile_coordinate(tile["row"], tile["column"]))
        self.assertEqual(st["where"], session.location_line(self.state))
        self.assertEqual(st["day"], self.state["clock"].day)
        self.assertEqual(st["status"], "awaiting_player")
        self.assertEqual(st["checkIn"], "when you call from Claude Code")
        for key in ("lastSeq", "land", "latest", "lastFight", "over",
                    "pause", "levelUp"):
            self.assertIn(key, st)
        self.assertIsNone(st["pause"])
        self.assertIsNone(st["over"])
        self.assertIsNone(st["levelUp"])
        with self.assertRaises(ValueError):
            page.state_view(self.state, status="asleep")

    def test_each_text_is_its_ui_page(self):
        self.assertEqual(self.view["game/party"]["text"], self.party_txt)
        self.assertEqual(self.view["game/map"]["text"], self.map_txt)
        self.assertEqual(self.view["game/record"]["text"], self.history_txt)
        for member, h in zip(self.view["game/party"]["members"],
                             self.state["party"]):
            self.assertEqual(member["text"], page.wrapped(
                session.hero_block_lines(self.state["party"], h)))
            self.assertEqual(member["name"], h.name)
        self.assertTrue(self.view["game/party"]["members"][0]["isPc"])
        self.assertFalse(self.view["game/party"]["members"][1]["isPc"])
        # the status tail is the sheet's own tail
        status = self.view["game/party"]["status"]
        self.assertTrue(status)
        self.assertEqual(self.party_txt[-len(status):], status)
        for line in (self.party_txt + self.map_txt + self.history_txt):
            self.assertLessEqual(len(line), session.WRAP_WIDTH, line)

    def test_the_taken_quest_is_in_hand(self):
        quests = self.view["game/quests"]
        self.assertEqual([q["id"] for q in quests["quests"]], [self.opening])
        q = quests["quests"][0]
        self.assertEqual(quests["active"], self.state.get("active_quest"))
        self.assertEqual(q["status"], "open")
        self.assertTrue(q["sites"])
        self.assertTrue(q["sites"][0]["mark"].startswith("here, room 1/"))
        for line in q["lines"]:
            self.assertIn(line, self.map_txt)
        self.assertIn(q["due"], (None, self.state["world"]["quests"]
                                 [self.opening]["deadline_day"]))

    def test_the_map_is_the_bare_grid_and_the_known_places(self):
        m = self.view["game/map"]
        world = self.state["world"]
        grid = [row[len(places.MAP_GUTTER):]
                for row in places.map_lines(world)[2:]]
        self.assertEqual(m["rows"], grid)
        self.assertEqual(len(m["rows"]), places.MAP_ROWS)
        self.assertTrue(all(len(r) == places.MAP_COLUMNS for r in m["rows"]))
        self.assertNotIn("@", "".join(m["rows"]))
        self.assertNotIn("!", "".join(m["rows"]))
        # The places are exactly the known slots and the four gates.
        known = []
        for tid in world["tile_order"]:
            tile = world["tiles"][tid]
            for slot in places.known_slots(world, tile):
                known.append((places.tile_coordinate(tile["row"],
                                                     tile["column"]),
                              slot["name"]))
        gates = [(places.tile_coordinate(world["tiles"][g["tile"]]["row"],
                                         world["tiles"][g["tile"]]["column"]),
                  places.GATE_BY_KEY[k]["name"])
                 for k, g in world["gates"].items()]
        self.assertEqual(sorted((p["coord"], p["name"]) for p in m["places"]),
                         sorted(known + gates))
        self.assertIn(m["coord"], [p["coord"] for p in m["places"]])
        # The legend is map.txt's, glyph by glyph.
        flat = " ".join(" ".join(self.map_txt).split())
        for glyph, word in m["legend"]:
            self.assertIn(f"{glyph} {word}", flat)
        self.assertEqual(m["here"], page.wrapped(
            session.here_lines(self.state)))

    def test_the_record_is_the_history_page(self):
        rec = self.view["game/record"]
        for line in rec["tally"]:
            self.assertIn(line, self.history_txt)
        for s in rec["suggestions"]:
            for line in page.wrapped(
                    [f"  {s['key']} -- {s['name']}: {s['line']}"]):
                self.assertIn(line, self.history_txt)
        self.assertEqual(rec["quests"], [])

    def test_no_world_and_no_rng_cross(self):
        keys = set(all_keys(self.view))
        self.assertNotIn("rng", keys)
        self.assertNotIn("world", keys)
        self.assertNotIn("seed", keys)

    def test_no_untaken_posting_crosses(self):
        world = self.state["world"]
        taken = {q["id"] for q in session.accepted_quests(self.state)}
        taken_names = {world["quests"][q]["name"] for q in taken}
        secret = {q["name"] for qid, q in world["quests"].items()
                  if qid not in taken and q["status"] == "open"}
        secret -= taken_names
        self.assertTrue(secret)
        blob = json.dumps(self.view)
        for name in secret:
            self.assertNotIn(name, blob)
        # ...nor their givers
        for qid, q in world["quests"].items():
            giver = q.get("giver")
            if qid in taken or not giver:
                continue
            self.assertNotIn(f"{giver['name']} ({giver['role']})", blob)

    def test_no_unknown_settlement_crosses(self):
        world = self.state["world"]
        known = {s["name"] for s in world["settlement_slots"].values()
                 if s["known"]}
        public = known | {land["name"] for land in world["lands"].values()}
        public |= {h.name for h in self.state["party"]}
        secret = {s["name"] for s in world["settlement_slots"].values()
                  if not s["known"] and s["name"]} - public
        self.assertTrue(secret)
        text = "\n".join(strings(self.view, keys=False))
        for name in secret:
            self.assertIsNone(re.search(rf"\b{re.escape(name)}\b", text),
                              name)

    def test_no_unentered_room_crosses(self):
        world = self.state["world"]
        q = world["quests"][self.opening]
        rooms = [r for s in session.quest_sites(world, q)
                 for r in session.site_rooms(world, s) if not r["visited"]]
        self.assertTrue(rooms)
        text = json.dumps(self.view["game/quests"])
        for room in rooms:
            self.assertNotIn(room["name"], text)
            for kind in room["kinds"]:
                self.assertIsNone(re.search(rf"\b{re.escape(kind)}", text),
                                  kind)


# --------------------------------------------------------------------------- #
# 4. The pause menu: data plus printer is the old menu, byte for byte
# --------------------------------------------------------------------------- #

class ThePauseMenu(unittest.TestCase):
    def assert_same_menu(self, state):
        self.assertEqual(printed(session.print_pause_menu, state),
                         printed(old_print_pause_menu, state))

    def test_a_wounds_pause_prints_as_it_always_did(self):
        with sandbox():
            state = crafted_pause(fresh(3), "normal")
            self.assert_same_menu(state)
            text = printed(session.print_pause_menu, state)
            self.assertIn("(the dead do not pursue past their ground)",
                          " ".join(text.split()))

    def test_a_fate_pause_prints_as_it_always_did(self):
        with sandbox():
            state = crafted_pause(fresh(3), "fate")
            self.assert_same_menu(state)
            data = session.pause_menu_data(state)
            self.assertEqual(data["kind"], "fate")
            self.assertEqual([o["choice"] for o in data["options"]],
                             ["fight_on", "retreat"])

    def test_every_option_prints_as_it_always_did(self):
        with sandbox():
            state = crafted_pause(fresh(3), "normal")
            pc, companion = state["party"]
            pc.abilities.update({"berserk", "war_breath"})
            pc.spells["invisibility"] = 2
            pc.spells["teleport"] = 2
            companion.items["smoke"] = 2
            self.assert_same_menu(state)
            choices = [o["choice"]
                       for o in session.pause_menu_data(state)["options"]]
            self.assertEqual(choices, ["fight_on", "drink", "heal", "berserk",
                                       "warbreath", "vanish", "retreat",
                                       "blink", "smoke"])

    def test_a_real_paused_fight_prints_as_it_always_did(self):
        with sandbox():
            state = real_pause()
            self.assert_same_menu(state)
            view = page.player_view(state, pause_fight="f0001")
            pause = view["game/state"]["pause"]
            self.assertEqual(pause["fight"], "f0001")
            self.assertEqual(pause["text"],
                             printed(session.print_pause_menu,
                                     state).splitlines())
            self.assertEqual(pause["round"], state["pending"]["round"])
            self.assertEqual(pause["kind"], "normal")
            self.assertTrue(pause["facing"])
            row = pause["party"][0]
            for key in ("name", "down", "hpState", "hp", "hpCeiling", "maxHp",
                        "sta", "staMax", "power", "powerMax", "penalties",
                        "conditions", "wounds", "healing", "stamina"):
                self.assertIn(key, row)
            # the heal option's heroes are exactly the potion carriers
            heal = next(o for o in pause["options"] if o["choice"] == "heal")
            self.assertEqual(heal["heroes"],
                             [h.name for h in state["party"]
                              if h.alive and h.items.get("healing", 0) > 0])
            self.assertIn("*** A FIGHT IS PAUSED -- resume or retreat ***",
                          " ".join(" ".join(
                              view["game/party"]["status"]).split()))


# --------------------------------------------------------------------------- #
# 5. pause_args: the argv, or a refusal
# --------------------------------------------------------------------------- #

def pause_move(**fields) -> dict:
    move = {"seq": 5, "at": 1, "kind": "pause", "fight": "f0003",
            "choice": "fight_on"}
    move.update(fields)
    return move


class PauseArgs(unittest.TestCase):
    def setUp(self):
        self._sandbox = sandbox()
        self._sandbox.__enter__()
        self.state = crafted_pause(fresh(3), "normal")
        self.pc, self.companion = self.state["party"]
        self.companion.hp, self.companion.down = 5, False

    def tearDown(self):
        self._sandbox.__exit__(None, None, None)

    def args(self, move, fight="f0003"):
        return page.pause_args(move, self.state, paused_fight=fight)

    def refused(self, move, fight="f0003", why=""):
        with self.assertRaises(page.MoveRefused) as caught:
            self.args(move, fight)
        self.assertIn(why, str(caught.exception))
        return str(caught.exception)

    def test_fight_on(self):
        self.assertEqual(self.args(pause_move()), ["resume"])

    def test_heal_with_a_potion_gives_the_argv(self):
        self.pc.items["healing"] = 1
        argv = self.args(pause_move(actions=[{"hero": self.pc.name,
                                              "action": "heal"}]))
        self.assertEqual(argv, ["resume", "--heal", self.pc.name])
        # ...which the command line resolves to the same hero
        self.assertIs(session.find_hero(self.state["party"], argv[2]),
                      self.pc)
        # and resume's own parser takes it
        parsed = session.build_parser().parse_args(argv)
        self.assertEqual(parsed.heal, [self.pc.name])

    def test_two_heroes_two_actions(self):
        self.pc.items["healing"] = 1
        self.companion.items["stamina"] = 1
        argv = self.args(pause_move(actions=[
            {"hero": self.pc.name, "action": "heal"},
            {"hero": self.companion.name, "action": "drink"}]))
        self.assertEqual(argv, ["resume", "--heal", self.pc.name,
                                "--drink", self.companion.name])

    def test_heal_without_a_potion_is_refused(self):
        self.pc.items["healing"] = 0
        self.refused(pause_move(actions=[{"hero": self.pc.name,
                                          "action": "heal"}]),
                     why="carries no healing potion")

    def test_an_action_at_fate_is_refused(self):
        self.state["pending"]["pause_kind"] = "fate"
        self.pc.items["healing"] = 1
        self.refused(pause_move(actions=[{"hero": self.pc.name,
                                          "action": "heal"}]),
                     why="Fate")
        self.assertEqual(self.args(pause_move()), ["resume"])

    def test_a_duplicate_hero_is_refused(self):
        self.pc.items["healing"] = 1
        self.pc.items["stamina"] = 1
        self.refused(pause_move(actions=[
            {"hero": self.pc.name, "action": "heal"},
            {"hero": self.pc.name, "action": "drink"}]), why="ONE")

    def test_an_unknown_hero_is_refused(self):
        self.refused(pause_move(actions=[{"hero": "Nobody",
                                          "action": "heal"}]),
                     why="no Nobody")

    def test_a_down_hero_is_refused(self):
        self.companion.hp, self.companion.down = 0, True
        self.companion.items["healing"] = 1
        self.refused(pause_move(actions=[{"hero": self.companion.name,
                                          "action": "heal"}]),
                     why="not on their feet")

    def test_a_stale_fight_is_refused(self):
        self.refused(pause_move(fight="f0002"), why="over")
        self.refused(pause_move(), fight=None, why="over")

    def test_no_pause_is_refused(self):
        self.state["pending"] = None
        self.refused(pause_move(), why="no fight is paused")

    def test_not_a_pause_move_is_refused(self):
        self.refused({"seq": 1, "kind": "say", "text": "resume"},
                     why="not a pause")
        self.refused(pause_move(choice="surrender"), why="not a pause")

    def test_retreat_and_its_escapes(self):
        self.assertEqual(self.args(pause_move(choice="retreat")),
                         ["retreat"])
        self.refused(pause_move(choice="retreat", escape="blink",
                                hero=self.pc.name), why="rank 2")
        self.pc.spells["teleport"] = 2
        self.assertEqual(self.args(pause_move(choice="retreat",
                                              escape="blink",
                                              hero=self.pc.name)),
                         ["retreat", "--blink", self.pc.name])
        self.refused(pause_move(choice="retreat", escape="smoke",
                                hero=self.companion.name), why="smoke vial")
        self.companion.items["smoke"] = 1
        self.assertEqual(self.args(pause_move(choice="retreat",
                                              escape="smoke",
                                              hero=self.companion.name)),
                         ["retreat", "--smoke", self.companion.name])
        # A clean escape is a retreat, and Fate lets a retreat pay at the
        # door (rules.md): the escapes stay open at a Fate pause.
        self.state["pending"]["pause_kind"] = "fate"
        self.assertEqual(self.args(pause_move(choice="retreat",
                                              escape="smoke",
                                              hero=self.companion.name)),
                         ["retreat", "--smoke", self.companion.name])

    def test_the_substring_trap_is_refused(self):
        # A companion whose whole name is inside the PC's: the command line
        # would hand the companion's action to the PC.
        self.companion.name = self.pc.name[:3]
        self.companion.items["healing"] = 1
        self.refused(pause_move(actions=[{"hero": self.companion.name,
                                          "action": "heal"}]),
                     why="another hero")

    def test_the_checker_is_resumes_own(self):
        # check_pause_actions is what cmd_resume runs: its refusal is the
        # line `resume` prints, unchanged.
        self.pc.items["healing"] = 0
        with self.assertRaises(ValueError) as caught:
            session.check_pause_actions(self.state,
                                        [("heal", self.pc.name)])
        self.assertEqual(str(caught.exception),
                         f"{self.pc.name} carries no healing potion.")
        self.pc.items["healing"] = 1
        self.companion.abilities.add("war_breath")
        self.companion.cur_power = session.WAR_BREATH_POWER_COST
        actions = session.check_pause_actions(
            self.state, [("heal", self.pc.name),
                         ("warbreath", self.companion.name)])
        self.assertEqual(actions, {self.pc: "heal",
                                   self.companion: "war-breath"})


class TheCommandsStillRefuse(unittest.TestCase):
    """resume and retreat print the checker's reason and leave the fight
    where it was."""

    def test_resume_and_retreat_refuse_before_the_fight_moves(self):
        with sandbox() as root:
            state = real_pause()
            pc = state["party"][0]
            pc.items["healing"] = 0
            session.save(state)
            before = (root / "save.json").read_text(encoding="utf-8")
            out = run("resume", "--heal", pc.name)
            self.assertIn("carries no healing potion", out)
            self.assertEqual((root / "save.json").read_text(
                encoding="utf-8"), before)
            out = run("resume", "--heal", "Nobody")
            self.assertIn("No hero matches 'Nobody'", out)
            out = run("retreat", "--smoke", pc.name)
            self.assertIn("has no smoke vial", out)
            out = run("retreat", "--blink", pc.name)
            self.assertIn("rank 2 needed", out)
            self.assertEqual((root / "save.json").read_text(
                encoding="utf-8"), before)


# --------------------------------------------------------------------------- #
# 6-8. clean_move, the chronicle entry, the level-up block
# --------------------------------------------------------------------------- #

class CleanMove(unittest.TestCase):
    def test_kinds_and_seq(self):
        self.assertIsNone(page.clean_move({"seq": 1, "kind": "shout",
                                           "text": "hi"}))
        self.assertIsNone(page.clean_move({"seq": 0, "kind": "say",
                                           "text": "hi"}))
        self.assertIsNone(page.clean_move({"seq": -3, "kind": "say",
                                           "text": "hi"}))
        self.assertIsNone(page.clean_move({"seq": True, "kind": "say",
                                           "text": "hi"}))
        self.assertIsNone(page.clean_move({"seq": "x", "kind": "say",
                                           "text": "hi"}))
        self.assertIsNone(page.clean_move({"kind": "say", "text": "hi"}))
        self.assertIsNone(page.clean_move({"seq": 1, "kind": "say",
                                           "text": "   "}))
        self.assertIsNone(page.clean_move("say hi"))
        self.assertEqual(page.clean_move({"seq": 2.0, "kind": "ooc",
                                          "text": " hi "})["seq"], 2)

    def test_unknown_fields_drop_and_text_is_capped(self):
        move = page.clean_move({"seq": 4, "at": 99, "kind": "say",
                                "text": "x" * 5000, "admin": True,
                                "fight": "f0001"})
        self.assertEqual(set(move), {"seq", "at", "kind", "text"})
        self.assertEqual(len(move["text"]), page.MOVE_TEXT_MAX)

    def test_a_pause_move_is_whole_or_nothing(self):
        good = pause_move(actions=[{"hero": "A" * 90, "action": "heal",
                                    "extra": 1}], hero="ignored")
        move = page.clean_move(good)
        self.assertEqual(move["actions"], [{"hero": "A" * page.HERO_NAME_MAX,
                                            "action": "heal"}])
        self.assertNotIn("hero", move)          # fight on carries no escape
        for bad in (pause_move(choice="flee"),
                    pause_move(actions=[{"hero": "A", "action": "pray"}]),
                    pause_move(actions=[{"action": "heal"}]),
                    pause_move(actions="heal"),
                    pause_move(actions=[{"hero": "A", "action": "heal"}] * 9),
                    pause_move(choice="retreat", escape="teleport",
                               hero="A"),
                    pause_move(choice="retreat", escape="blink")):
            self.assertIsNone(page.clean_move(bad), bad)
        retreat = page.clean_move(pause_move(choice="retreat",
                                             escape="smoke", hero=" Ali ",
                                             actions=[{"hero": "A",
                                                       "action": "heal"}]))
        self.assertEqual(retreat, {"seq": 5, "at": 1, "kind": "pause",
                                   "fight": "f0003", "choice": "retreat",
                                   "escape": "smoke", "hero": "Ali"})


class TheChronicleAndTheLevelUp(unittest.TestCase):
    def test_a_chronicle_entry(self):
        with sandbox():
            state = fresh(3)
            entry = page.chronicle_entry(
                5, "\n  The road.  \n",
                [{"seq": 9, "kind": "ooc", "text": "b"},
                 {"seq": 4, "kind": "say", "text": " a ", "x": 1},
                 {"seq": 7, "kind": "nonsense"}],
                state=state, fights=["f0002"])
            self.assertEqual(entry["id"], "t0005")
            self.assertEqual(entry["turn"], 5)
            self.assertEqual(entry["prose"], "The road.")
            self.assertEqual(entry["answered"],
                             [{"seq": 4, "kind": "say", "text": "a"},
                              {"seq": 9, "kind": "ooc", "text": "b"}])
            self.assertEqual(entry["fights"], ["f0002"])
            self.assertEqual(entry["levels"],
                             {h.name: 1 for h in state["party"]})
            self.assertIs(entry["over"], False)
            self.assertEqual(entry["coord"],
                             page.state_view(state)["coord"])
            self.assertEqual(entry["day"], state["clock"].day)
            json.dumps(entry)

    def test_banked_points_show_the_level_up_menu(self):
        with sandbox():
            state = fresh(3)
            state["party"][0].skill_points = 3
            up = page.state_view(state)["levelUp"]
            self.assertEqual(up["hero"], state["party"][0].name)
            self.assertEqual(up["points"], 3)
            self.assertEqual(up["text"], printed(
                session.print_levelup_menu,
                [state["party"][0]]).splitlines())
            state["party"][1].skill_points = 3      # companions autolevel
            state["party"][0].skill_points = 0
            self.assertIsNone(page.state_view(state)["levelUp"])

    def test_game_over_ends_the_status(self):
        with sandbox():
            state = fresh(3)
            state["party"][0].dead = True
            st = page.state_view(state, status="awaiting_player")
            self.assertEqual(st["over"], "pc_dead")
            self.assertEqual(st["status"], "ended")
            for h in state["party"]:
                h.dead = True
            self.assertEqual(page.state_view(state)["over"], "wiped")
            self.assertTrue(page.chronicle_entry(
                1, "", state=state)["over"])


# --------------------------------------------------------------------------- #
# RPG2_HOME: the game under another base directory
# --------------------------------------------------------------------------- #

class TheBaseDirectory(unittest.TestCase):
    def test_a_game_runs_under_rpg2_home_and_projects(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, RPG2_HOME=tmp, PYTHONIOENCODING="utf-8")

            def py(*argv):
                return subprocess.run([sys.executable, *argv], cwd=REPO,
                                      env=env, capture_output=True,
                                      text=True, check=True).stdout

            py("session.py", "new", "--seed", "3", "--level", "1")
            self.assertTrue((Path(tmp) / "save.json").exists())
            self.assertTrue((Path(tmp) / "ui" / "party.txt").exists())
            out = py("-c", "import session, page, json; print(json.dumps("
                           "page.player_view(session.load())))")
            view = json.loads(out)
            self.assertEqual(tuple(view), page.SINGLETONS)
            out = py("session.py", "sheet")
            self.assertIn("nothing was committed", " ".join(out.split()))

    def test_the_default_home_is_the_repo(self):
        if os.environ.get("RPG2_HOME"):
            self.skipTest("RPG2_HOME is set for this run")
        self.assertEqual(session.RPG2_HOME, REPO)
        self.assertEqual(session.REPO_DIR, REPO)


# =========================================================================== #
# PART 2 (session 2): the fights kept, publish.py, the record, the moves
# =========================================================================== #

def queue() -> list[tuple[Path, dict]]:
    return page.queued_fights()


def joined(doc: dict) -> list[str]:
    """A fight's blocks, joined back into its lines."""
    return [line for block in doc["blocks"] for line in block["lines"]]


def calm_fight(kind: str = "wolf", count: int = 1) -> dict:
    """A fight that runs to its end without pausing, in the current
    sandbox: the first seed whose party does not stop against it."""
    for seed in range(1, 20):
        fresh(seed)
        run("fight", str(count), "--type", kind)
        state = session.load()
        if not state["pending"]:
            return state
    raise AssertionError(f"every seed paused against {count} {kind}")


class TheRoundSpans(unittest.TestCase):
    def test_spans_mark_the_rounds_in_the_player_log(self):
        log = rpg.CombatLog()
        log.play("opening", "=== A Fight ===")
        log.round_start(1)
        log.play("hit", "Amina hits.")
        log.round_start(2)
        log.play("parry", "A parry.", quiet=True)
        log.round_start(3)
        log.play("hit", "Nasir hits.")
        log.finish_rounds()
        log.finish_rounds()                     # a second close is a no-op
        log.play("tally", "Purse 3s; day 1.")
        self.assertEqual(log.round_spans, [[1, 6]])
        self.assertEqual(log.player[1:6], ["Round 1:", "Amina hits.",
                                           "Round 2: nothing lands.",
                                           "Round 3:", "Nasir hits."])
        self.assertIsNone(log.outcome)
        blocks = page.fight_blocks(log.player, log.round_spans)
        self.assertEqual([b["kind"] for b in blocks],
                         ["opening", "rounds", "closing"])
        self.assertEqual(joined({"blocks": blocks}), log.player)

    def test_blocks_between_two_stretches_and_without_rounds(self):
        lines = ["a", "R1", "b", "R2", "c"]
        blocks = page.fight_blocks(lines, [[1, 2], [3, 4]])
        self.assertEqual([b["kind"] for b in blocks],
                         ["opening", "rounds", "between", "rounds",
                          "closing"])
        self.assertEqual(joined({"blocks": blocks}), lines)
        self.assertEqual([b["kind"] for b in page.fight_blocks(["x"], [])],
                         ["opening"])
        self.assertEqual([b["kind"] for b in
                          page.fight_blocks(["x"], [], continuing=True)],
                         ["closing"])

    def test_the_title_is_the_banner(self):
        self.assertEqual(page.fight_title(
            ["=== The reckoning:", "the Watch ===", "Guard 1"]),
            "The reckoning: the Watch")
        self.assertEqual(page.fight_title(
            ["=== The Thing in the Well ===", "(a level-1 fight)"]),
            "The Thing in the Well")
        self.assertEqual(page.fight_title(["2x Wolf -- fangs", "DEX 4"]),
                         "2x Wolf -- fangs")
        self.assertEqual(page.fight_title([]), "")


class TheFightsKept(unittest.TestCase):
    def test_a_fight_is_queued_as_its_player_log(self):
        with sandbox() as root:
            state = calm_fight("wolf", 2)
            kept = queue()
            self.assertEqual(len(kept), 1)
            path, doc = kept[0]
            self.assertEqual(path.name, "q001.json")
            short = ui_lines(root / "ui" / "fight-short.txt")
            self.assertEqual(joined(doc), short)
            kinds = [b["kind"] for b in doc["blocks"]]
            self.assertEqual(kinds[0], "opening")
            self.assertEqual(kinds[-1], "closing")
            self.assertIn("rounds", kinds)
            rounds = [b for b in doc["blocks"] if b["kind"] == "rounds"]
            self.assertTrue(rounds[0]["lines"][0].startswith("Round "))
            self.assertGreaterEqual(doc["rounds"], 1)
            tally = session.tally_lines(state)
            self.assertEqual(doc["blocks"][-1]["lines"][-len(tally):], tally)
            self.assertIn(doc["outcome"], ("won", "unresolved"))
            self.assertFalse(doc["continuing"])
            self.assertEqual(doc["day"], state["clock"].day)
            self.assertEqual(doc["where"], session.location_line(state))
            self.assertEqual(doc["title"], short[0])
            json.dumps(doc).encode("ascii")

    def test_a_paused_fight_and_its_second_half(self):
        with sandbox() as root:
            real_pause()                        # new empties the queue
            short = root / "ui" / "fight-short.txt"
            (_, first), = queue()
            self.assertEqual(first["outcome"], "paused")
            self.assertEqual(joined(first), ui_lines(short))
            self.assertFalse(first["continuing"])
            before = len(ui_lines(short))
            run("resume")
            kept = queue()
            self.assertEqual(len(kept), 2)
            second = kept[1][1]
            self.assertTrue(second["continuing"])
            self.assertEqual(joined(second), ui_lines(short)[before:])
            self.assertIn(second["outcome"],
                          ("won", "lost", "unresolved", "paused"))
            self.assertEqual(second["title"], first["title"])
            self.assertNotEqual(second["blocks"][0]["kind"], "opening")

    def test_a_clean_retreat_is_retreated(self):
        with sandbox():
            real_pause()
            with unittest.mock.patch("session.attempt_retreat",
                                     return_value=True):
                run("retreat")
            doc = queue()[-1][1]
            self.assertEqual(doc["outcome"], "retreated")
            self.assertTrue(doc["continuing"])
            self.assertIsNone(session.load()["pending"])

    def test_two_fights_are_two_entries(self):
        with sandbox() as root:
            calm_fight("wolf", 1)               # new empties the queue
            first = ui_lines(root / "ui" / "fight-short.txt")
            run("fight", "1", "--type", "wolf")
            kept = queue()
            self.assertEqual([p.name for p, _ in kept],
                             ["q001.json", "q002.json"])
            self.assertEqual(joined(kept[0][1]), first)
            self.assertEqual(joined(kept[1][1]),
                             ui_lines(root / "ui" / "fight-short.txt"))

    def test_a_bare_log_is_not_kept(self):
        with sandbox():
            fresh(3)
            state = session.load()
            log = rpg.CombatLog()                   # no ui page: a bench's
            log.play("x", "x")
            with contextlib.redirect_stdout(io.StringIO()):
                session.print_combat(log, state)
            self.assertEqual(queue(), [])

    def test_new_drops_the_record_and_the_queue(self):
        with sandbox() as root:
            calm_fight("wolf", 1)
            (root / "ui" / "page.json").write_text('{"url": "x"}')
            self.assertTrue(queue())
            fresh(4)
            self.assertFalse((root / "ui" / "page.json").exists())
            self.assertFalse((root / "ui" / "queue").exists())

    def test_the_record_is_committed_by_sheet(self):
        self.assertIn("ui/page.json", session.UI_COMMIT_PATHS)


class TheMoveCheck(unittest.TestCase):
    """`page.py moves`: what the DM does with each move read."""

    def setUp(self):
        self._sandbox = sandbox()
        self._sandbox.__enter__()
        self.state = crafted_pause(fresh(3), "normal")
        self.pc, self.companion = self.state["party"]
        self.companion.hp, self.companion.down = 5, False
        self.pc.items["healing"] = 1
        self.companion.items["healing"] = 0

    def tearDown(self):
        self._sandbox.__exit__(None, None, None)

    def report(self, moves, last_seq=3):
        for i, m in enumerate(moves):
            m.setdefault("id", f"m{m.get('seq', 90 + i):04d}")
        return page.moves_report(moves, self.state, last_seq=last_seq,
                                 paused_fight="f0003")

    def test_each_kind_of_line(self):
        pc, companion = self.pc.name, self.companion.name
        lines = self.report([
            {"seq": 2, "kind": "say", "text": "old"},
            {"seq": 4, "kind": "say", "text": "  go on  "},
            {"seq": 5, "kind": "ooc", "text": "why?"},
            pause_move(seq=6, actions=[{"hero": pc, "action": "heal"}]),
            pause_move(seq=7, actions=[{"hero": pc, "action": "heal"}]),
            {"seq": 8, "kind": "order"},
        ])
        self.assertEqual(lines, [
            "m0002 answered by an earlier turn; deleted",
            "m0004 say: go on",
            "m0005 ooc: why?",
            "m0006 superseded by m0007",
            f"m0007 pause -> python session.py resume --heal "
            f"{shlex.quote(pc)}",
            "m0008 not a move; deleted unanswered",
        ])
        refused = self.report([pause_move(
            seq=9, actions=[{"hero": companion, "action": "heal"}])])
        self.assertEqual(refused, [
            f"m0009 pause REFUSED: {companion} carries no healing potion "
            f"(answer it in the fiction)"])
        stale = self.report([pause_move(seq=9, fight="f0002")])
        self.assertIn("REFUSED: that pause is over", stale[0])

    def test_the_command_printed_is_what_resume_reads(self):
        line, = self.report([pause_move(
            seq=6, actions=[{"hero": self.pc.name, "action": "heal"}])])
        argv = shlex.split(line.split(" -> python session.py ", 1)[1])
        args = session.build_parser().parse_args(argv)
        self.assertEqual(args.heal, [self.pc.name])

    def test_move_words(self):
        pc = self.pc.name
        self.assertEqual(page.move_words(page.clean_move(pause_move(
            actions=[{"hero": pc, "action": "heal"}]))),
            f"At the pause: {pc} drinks a healing potion; fight on")
        self.assertEqual(page.move_words(page.clean_move(pause_move(
            choice="retreat", escape="smoke", hero=pc))),
            f"At the pause: retreat -- {pc} breaks a smoke vial")
        self.assertEqual(page.move_words(page.clean_move(
            {"seq": 1, "kind": "ooc", "text": "hi"})), "(to the DM) hi")


# --------------------------------------------------------------------------- #
# publish.py, by subprocess, under a temp RPG2_HOME
# --------------------------------------------------------------------------- #

class ThePublish(unittest.TestCase):
    """dream's publish test, rpg2's way: the game is played in the sandbox
    (whose root is laid out as an RPG2_HOME), publish.py runs over it."""

    def py(self, *argv, check=True):
        env = dict(os.environ, RPG2_HOME=str(self.root),
                   PYTHONIOENCODING="utf-8")
        return subprocess.run([sys.executable, *argv], cwd=REPO, env=env,
                              capture_output=True, text=True, check=check)

    def publish(self, *extra):
        self.py("publish.py", "--out", str(self.out), *extra)
        return json.loads((self.out / "batch.json").read_text())

    def sent(self, *extra):
        self.py("publish.py", "--sent", "--out", str(self.out), *extra)

    def doc(self, path):
        return json.loads((self.out / f"{path}.json").read_text())

    @staticmethod
    def targets(batch):
        return [(w["op"], f"{w['collection']}/{w['doc_id']}",
                 w.get("if_version")) for w in batch]

    def write(self, name, doc):
        path = self.root / name
        path.write_text(json.dumps(doc) if not isinstance(doc, str) else doc)
        return str(path)

    def test_the_keepers_turn(self):
        with sandbox() as root:
            self.root, self.out = root, root / "out"
            state = real_pause()
            self.assertEqual(len(queue()), 1)
            pc = state["party"][0]
            pc.items["healing"] = 1
            session.save(state)
            prose = self.write("prose.md", "The troll comes.\n\n[fight]\n\n"
                               "It stands over you.\n")
            moves = self.write("moves.json", [
                {"id": "m0003", "version": 1, "seq": 3, "kind": "say",
                 "text": "I walk."},
                {"id": "m0002", "version": 2, "seq": 2, "kind": "say",
                 "text": "answered already"}])
            read = self.write("state.json", {"v": 1, "lastSeq": 2,
                                             "latest": "t0004",
                                             "version": 9})

            # the first publish: every singleton, pinned where known
            batch = self.publish("--prose", prose, "--moves", moves,
                                 "--state", read)
            targets = self.targets(batch)
            self.assertIn(("set", "game/state", 9), targets)
            self.assertIn(("set", "chronicle/t0005", None), targets)
            self.assertIn(("set", "fights/f0001", None), targets)
            self.assertIn(("delete", "moves/m0002", 2), targets)
            self.assertIn(("delete", "moves/m0003", 1), targets)
            self.assertGreaterEqual({p for _, p, _ in targets},
                                    set(page.SINGLETONS))
            for write in batch:
                if write["op"] == "set":
                    self.assertTrue(Path(write["file_path"]).is_file())
                    self.assertIn(write["collection"],
                                  ("game", "chronicle", "fights"))
            game = self.doc("game/state")
            self.assertEqual((game["lastSeq"], game["latest"],
                              game["lastFight"]), (3, "t0005", "f0001"))
            self.assertEqual(game["pause"]["fight"], "f0001")
            self.assertEqual(game["checkIn"], "when you call from Claude Code")
            entry = self.doc("chronicle/t0005")
            self.assertEqual([m["seq"] for m in entry["answered"]], [3])
            self.assertEqual(entry["fights"], ["f0001"])
            fight = self.doc("fights/f0001")
            self.assertEqual((fight["v"], fight["id"], fight["outcome"],
                              fight["continues"]), (1, "f0001", "paused",
                                                    None))
            self.assertNotIn("continuing", fight)

            # the keeper's check reads the published pause
            pause = pause_move(seq=4, fight="f0001", actions=[
                {"hero": pc.name, "action": "heal"}])
            pause["id"] = "m0004"
            checked = self.py("page.py", "moves",
                              self.write("moves2.json", [pause]),
                              "--state", str(self.out / "game" /
                                             "state.json")).stdout
            self.assertIn("m0004 pause -> python session.py resume --heal",
                          checked)

            # --sent: the record, the transcript, the queue
            self.sent()
            record = json.loads((root / "ui" / "page.json").read_text())
            self.assertIsNone(record["url"])
            self.assertEqual(record["versions"],
                             dict({p: 1 for p in page.SINGLETONS},
                                  **{"game/state": 10}))
            transcript = (root / "ui" / "transcript.md").read_text()
            self.assertTrue(transcript.startswith(
                f"## turn 5 (day {state['clock'].day})\n\n> I walk.\n\n"
                f"The troll comes.\n\n[fight f0001: "))
            self.assertEqual(queue(), [])

            # the second half: its own document, continuing the first
            run("resume", "--heal", pc.name)
            read = self.write("state.json", dict(game, version=10))
            prose = self.write("prose.md", "You drink and go on.\n")
            batch = self.publish("--prose", prose, "--state", read)
            second = self.doc("fights/f0002")
            self.assertEqual(second["continues"], "f0001")
            self.assertEqual(self.doc("game/state")["lastFight"], "f0002")
            self.assertIsNone(self.doc("game/state")["pause"])
            self.assertIn(("set", "game/state", 10), self.targets(batch))
            self.sent()
            self.assertIn("[fight f0002: ",
                          (root / "ui" / "transcript.md").read_text())

            # a second publish sends only what changed
            batch = self.publish("--status", "dm_thinking")
            self.assertEqual([(w["doc_id"], w.get("if_version"))
                              for w in batch], [("state", 11)])
            self.sent("--url", "https://claude.ai/artifact/x")
            record = json.loads((root / "ui" / "page.json").read_text())
            self.assertEqual(record["url"], "https://claude.ai/artifact/x")
            self.assertEqual(record["versions"]["game/state"], 12)

            # --all with nothing read: the record pins every one
            batch = self.publish("--all")
            self.assertEqual({(w["doc_id"], w.get("if_version"))
                              for w in batch},
                             {(p.split("/")[1], record["versions"][p])
                              for p in page.SINGLETONS})

            # a batch never passes 50 writes
            many = self.write("many.json", [
                {"id": f"m{n:04d}", "seq": n, "kind": "say", "text": "x"}
                for n in range(20, 80)])
            done = self.py("publish.py", "--out", str(self.out),
                           "--moves", many, check=False)
            self.assertNotEqual(done.returncode, 0)
            self.assertIn("more than one batch takes (50)", done.stderr)

    def test_a_new_game_writes_everything(self):
        """No record (new dropped it): the last publish is another page's,
        so nothing is compared with it or read from it."""
        with sandbox() as root:
            self.root, self.out = root, root / "out"
            fresh(3)
            prose = self.write("prose.md", "You wake.\n")
            self.publish("--prose", prose)
            self.sent()
            fresh(3)                              # the same world, anew
            batch = self.publish("--prose", prose)
            self.assertEqual({p for _, p, _ in self.targets(batch)},
                             set(page.SINGLETONS) | {"chronicle/t0001"})
            self.assertTrue(all(v is None for _, _, v in
                                self.targets(batch)))


if __name__ == "__main__":
    unittest.main()
