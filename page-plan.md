# Plan: the player's page for rpg2 (a port of dream's Artifact frontend)

The goal is to give rpg2 its own player-facing claude.ai Artifact page, modelled on `dream/web/` and dream's publish / keeper's-turn protocol, and fitted to rpg2's game. All work lands in `/home/user/rpg2`. `/home/user/dream` is reference only and is never changed. The work is split into five serial sessions. Each one ends committed, tested and working, with its paperwork done.

---

## 0. What exists today (checked in the code)

### dream (the reference)

**Python side**
- `dream/publish.py` loads the save and projects it with `dreamgame.player_view`. It writes `web/out/{game,chronicle,fights}/*.json` and `web/out/batch.json`, which is one ArtifactData batch.
  - Every `game/` set is pinned with `if_version`. Versions come from `page.json` beside the save, or from `--state` / `--versions`.
  - Every move it read is deleted, pinned.
  - `--sent` promotes `out/pending` to `out/last`, advances `page.json`, clears the sent fights from the queue, and records `--url` once.
  - Caps: `DOC_MAX = 256 KiB`, `BATCH_MAX = 50`.
- `dream/dreamgame/view.py` holds the projection, `clean_move`, `MoveRefused`, `after_school_args`, `chronicle_entry`, `fight_view` (a big regex parser over the log), `keep_fight` (a manual queue into `saves/queue/`) and `rules_view`.
  - Its principles: the store is readable by the player, so secrets are never written; parse, never cast; a move is data.
- `dream/tests/test_view.py` holds plain-assert tests run as a script. Key checks: secret keys and words never appear, and the publish batch is pinned (`test_publish_writes_the_changed_documents_and_one_pinned_batch`).

**Web side** (`dream/web/`)
- `app/`: Angular 20, standalone, signals, zoneless. `outputHashing: none`. It builds exactly `main.js` and `styles.css`.
- `src/app/store.ts` (`DreamStore`)
  - Subscribes once per document or collection.
  - Keeps a single write queue.
  - `send()` writes `moves/mNNNN` with `seq = max(state.lastSeq, max moves.seq) + 1`.
  - Error codes map to `readOnly` / `link`.
- `model.ts`: defensive readers (`num`, `str`, `arr`, `obj`, `oneOf`), `PATHS`, `readMove`, `moveId`, `paragraphs`.
- `app.ts`: header, three zones (≥1241px), two zones (≤1240px), one zone plus a bottom bar (≤900px).
- `drawer/tabs.ts`: a `bar` flag gives a tab its own bottom-bar slot; the others go under More.
- `ui.ts`, `unread.ts` (localStorage signatures), and panels: `story`, `answer`, `chronicle`, `fight`, `fights`, `fight-chip`, `line`, `member`, `school`, `class`, `realm`, `days`, `rules`, `rich`, `hp-track`.
- `page.html`: content only, with no doctype, `<html>`, `<head>` or `<body>`.
- `build-artifact.mjs`: `page.html` plus the bundles go to `web/dist/`. It fails on stray bundles and on a `<head>`.
- `dev/serve.mjs` (`FakeStore`, SSE, `/__db/list|get|batch|write|dump`, `?readonly`, `?nodb`, `?theme=dark`), `dev/fake-db.js` (a `window.claude.use("db")` shim), and `dev/db.mjs` (the keeper-side CLI).
- `e2e.mjs`: playwright-core against the fake store, with checks and screenshots.

### rpg2 (the target)

**Play**
- Play goes through `session.py`, about 8,500 lines. The state is `save.json` beside it, and it is gitignored (`.gitignore` line 12).
  - `session.load()` / `session.save()` handle it. `save()` rewrites `ui/party.txt`, `ui/map.txt` and `ui/history.txt` through `party_sheet_lines`, `map_sheet_lines` and `history_sheet_lines`, all wrapped at `WRAP_WIDTH = 40` by `_wrap_block`.
- Combat writes `ui/fight-short.txt` (the player log, `CombatLog.player`) and `ui/fight-detailed.txt` (dice; DM post-mortems only) through `new_combat_log()` / `print_combat(log)`.
  - `print_combat` is called at `session.py` lines about 2359 (pause, in `resolve_encounter`), 4267 (mercy), 4385 (end of `finish_encounter`), and 6206 / 6322 / 6341 (resume / retreat).
- `sheet` (`cmd_sheet`) commits `UI_COMMIT_PATHS`: the three pages, the two fight snapshots, and the DM-authored `ui/scene.md` and `ui/transcript.md`.
- **The pause**
  - `state["pending"]` is set by `resolve_encounter`, `cmd_resume` and `cmd_retreat`.
  - `print_pause_menu(state)` prints the options with their eligibility logic inline.
  - `cmd_resume` validates `--drink/--heal/--berserk/--warbreath/--vanish HERO`, allowing one per hero, and refuses them at a Fate pause.
  - `cmd_retreat` takes `--blink HERO` and `--smoke HERO`.
  - Hero lookup is `find_hero`, a case-insensitive substring match.
- **Other readouts**: `tally_lines(state)` is the after-fight block and uses HP *state words*. `print_levelup_menu([pc])` is the spending menu.
- The map is `places.map_lines(world, party, objectives)`: 18 rows by 30 glyphs plus a gutter. `map_glyph` → `gate_glyph` / `settlement_glyph` shows known settlements only (`known_slots`). The legends are `MAP_GLYPH_LEGEND`, `MAP_MARK_LEGEND` and `MAP_GATE_LEGEND`. Coordinates come from `tile_coordinate(row, col)` → `"R17C11"`.
- Quests in hand come from `accepted_quests`, `_quest_site_lines`, `_quest_road_lines`, `quest_objective_tiles` and `deadline_note`.

**Tests and docs**
- Tests are unittest modules at the repo root with `if __name__ == "__main__": unittest.main()`. They run as `python -m unittest -v test_X.py` or `python test_X.py`.
- `test_start.sandbox()` repoints `session.STATE_PATH` and the page paths at a temp dir. Follow that pattern.
- Doc rules:
  - develop.md "Files" must register every new file.
  - "Where a finished feature is written up" requires a designlog entry per shipped session, the `plan.md` entry deleted when shipped, and `rules.md` / `dm.md` for play-facing changes.
  - CLAUDE.md must stay short and register-neutral.
  - writing.md sets the voice: plain, terse, second person, ASCII, displays at 40 columns.
  - develop.md Conventions: stdlib only, ASCII output, and no backwards compatibility.

### Environment

- Node v22.22.2 and npm 10.9.7 are at `/opt/node22/bin`. Python is 3.11.
- `registry.npmjs.org` answers HTTP 200. It is in the agent proxy's `noProxy` list, so the connection is direct.
- `dream/web/app` has no `node_modules`; it has never been installed here.
- Chromium is at `/opt/pw-browsers/chromium-1194/chrome-linux/chrome` and `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers` is set. That matches `playwright-core` 1.56.1, the version in dream's lock.
- **npm handling for implementers:**
  - Copy dream's `package.json` and `package-lock.json`.
  - Rename `"name"` in both files, including `packages[""].name` in the lock.
  - Run `npm ci`. If `npm ci` objects to the lock, run `npm install` once and commit the regenerated lock. Keep the same version ranges; do not upgrade Angular.
  - If the network fails, read `/root/.ccr/README.md` and `curl -sS "$HTTPS_PROXY/__agentproxy/status"`. Never disable TLS or unset `HTTPS_PROXY`.
  - If npm truly cannot install, commit the source anyway. Record in the designlog that build and e2e were **not** run. Never claim they passed.

---

## 1. Architecture decisions (applied throughout)

1. **The page shows what rpg2's player-facing surfaces show, never more.**
   - The projection is built by *calling the same functions* the ui pages use: `hero_block_lines`, `party_sheet_lines`, `map_sheet_lines`, `here_lines`, `history_sheet_lines`, `tally_lines`, the fight log's `CombatLog.player`, and `print_pause_menu` / `print_levelup_menu`. Their output is captured.
   - DM-only surfaces never feed it: `board` (untaken jobs, hidden givers), `show QID` (room rosters), `look --dm`, `tile`, `lore`, `prices`, `armory`, `place_debug_lines`, `ui/fight-detailed.txt`, the `world` dict raw, and the `rng` blob.
   - Where the ui pages show HP as a state word (the tally, the fight) the page does too. Where they show digits (the party sheet, the pause menu) the page does too.
2. **Module layout mirrors rpg2's flat root.** `page.py` is the projection plus moves plus the fight queue (dream's `view.py`). `publish.py` is the keeper's CLI (dream's `publish.py`). `test_page.py` is the suite. `web/` is the page.
3. **One base directory: `RPG2_HOME`.** A new env var, defaulting to the repo root, roots `save.json` and `ui/`.
   - `ui/page.json` is the page's record: the url and the version of each written doc. It is committed by `sheet` and added to `UI_COMMIT_PATHS`.
   - `ui/queue/qNNN.json` holds fights kept for the next publish. It is gitignored, with the same lifetime as `save.json`.
   - `web/out/` holds publish output and is gitignored, as in dream.
   - The e2e and `publish.py` tests set `RPG2_HOME` to a temp dir.
4. **Fights are kept automatically.** `session.print_combat(log, state)` calls `page.keep_fight(state, log)`, so there is no DM call to forget (dream's `keep_fight` was manual).
   - The fight doc is **the player log, exactly**, split into blocks at markers the engine records. It is not regex-parsed.
   - A paused fight's second half is **its own write-once doc** with `continues: "<id>"`. This matches rpg2's "a fight spans at most two messages".
5. **Move kinds are `say`, `ooc` and `pause`.** `pause` is the one mid-fight decision, which CLAUDE.md names as the player's real decision point.
   - Everything else (travel, take a job, train/learn, camp, tavern, buy) is said in words, as today.
   - The DM's `options:` display block becomes tappable chips that **prefill** the answer box. They never send on their own.
6. **The prose file is `ui/scene.md`.** In page play, `ui/scene.md` holds just the turn's DM text: paragraphs plus fenced displays, with no `## turn` heading, no `>` quote and no footer links.
   - A paragraph that is exactly `[fight]` is replaced by the turn's next fight card. Fights not placed follow the prose.
   - `publish.py --sent` appends the sent turn to `ui/transcript.md` in the existing shape, so the transcript stays the record of what the player actually received.
   - The draft-reread-before-publish discipline of dm.md's scene page carries over unchanged.
7. **Dropped from dream:**
   - realities and school dressing;
   - the Class, Realm, School, Days and Rules tabs;
   - `hp-track`, `member.css`, `rich.ts`;
   - `after_school_args`, `reorder`, `tell` / `hear` / `find_lair` / `meet`;
   - `rules_view`;
   - the `fight_view` regex parser and the manual `keep_fight`;
   - web fonts. Use system stacks: mono `ui-monospace, "Roboto Mono", "Droid Sans Mono", monospace`, and prose `Georgia, "Noto Serif", serif`. This removes an external host and the e2e font waits.
8. **Phone first.** The target is Android at about 412px, with 360px as the floor. The bottom bar is five buttons: **Story, Party, Map, Fight, More**. More holds **Fights, Quests, Record**. Touch targets are at least 48px. 40-column displays render as `white-space: pre` in mono at a size where 40 characters fit 360px (about 13px). There is no horizontal page scroll.
9. **Page chrome copy is ASCII, in writing.md's display register**: terse labels, no exclamation marks except engine lines, "--" not em-dashes, and separators drawn with CSS or SVG. See the copy table in Session 3.

---

## 2. The data contract

Every document carries `v: 1`. Keys are camelCase. Every document stays under 256 KiB. Paths:

```
game/state  game/party  game/map  game/quests  game/record      (singletons: publish.py, pinned)
chronicle/tNNNN   one DM turn, written once
fights/fNNNN      one fight (or the continuation of a paused one), written once
moves/mNNNN       one player move, written by the page, deleted by the keeper
```

### `game/state`

```json
{
  "v": 1,
  "status": "awaiting_player",
  "lastSeq": 4,
  "day": 3,
  "where": "Umaia > R17C11 > Dar Aziza",
  "coord": "R17C11",
  "land": "Umaia",
  "latest": "t0005",
  "lastFight": "f0002",
  "checkIn": "when you call from Claude Code",
  "over": null,
  "pause": null,
  "levelUp": null
}
```

- `status` is one of `"awaiting_player"`, `"dm_thinking"`, `"ended"`.
- `over` is `null`, `"wiped"` or `"pc_dead"`. The rules follow `report_game_over`. `status` is forced to `ended` when `over` is set.
- `pause` is `null` or:

```json
{
  "fight": "f0003",
  "round": 3,
  "kind": "normal",
  "trips": "Amina is badly cut up",
  "facing": [{ "name": "Wolf 2", "hp": 3, "maxHp": 6 }],
  "party": [{ "name": "Amina", "down": false, "hpState": "Hurt", "hp": 4, "hpCeiling": 9, "maxHp": 9,
              "sta": 2, "staMax": 6, "power": 3, "powerMax": 3, "penalties": "hurt -1, Winded -2",
              "conditions": ["bleeding"], "wounds": ["a deep cut in the forearm (sev 3)"],
              "healing": 1, "stamina": 0 }],
  "options": [
    { "choice": "fight_on", "label": "fight on", "cost": "fight on" },
    { "choice": "drink",     "heroes": ["Nasir"], "cost": "stamina draught, +3 STA now" },
    { "choice": "heal",      "heroes": ["Amina", "Nasir"], "cost": "healing potion, +5 HP now ..." },
    { "choice": "berserk" }, { "choice": "warbreath" }, { "choice": "vanish" },
    { "choice": "retreat",   "cost": "parting blows ..., then one group chase roll" },
    { "choice": "blink",     "hero": "Nasir", "cost": "..." },
    { "choice": "smoke",     "hero": "Amina", "cost": "..." }
  ],
  "text": ["*** FIGHT PAUSED (after round 3): ...", "..."]
}
```

- `kind` is `"normal"` or `"fate"` (the engine's `pause_kind`; corrected in Session 1 -- what tripped the pause is in `trips`).
- The `berserk`, `warbreath` and `vanish` options appear only when someone qualifies.
- A `"fate"` pause offers `fight_on` and `retreat`, and keeps `blink` / `smoke` when someone qualifies: they are retreats, and rules.md lets a clean escape pay Fate at the door (corrected in Session 1).
- `text` is the exact `print_pause_menu` output, 40-column wrapped, for fidelity.
- `fight` is set by publish to the id of the published fight that paused.
- `levelUp` is `null` or `{ "hero": "Nasir", "points": 3, "text": [ ...print_levelup_menu([pc]) lines... ] }`. It is present when the PC has `skill_points > 0`.

### `game/party`

```json
{
  "v": 1,
  "day": 3,
  "purse": 20,
  "slots": { "filled": 1, "cap": 2, "cha": 5 },
  "members": [{
    "name": "Nasir", "nickname": "", "isPc": true, "homeland": "umaia", "sex": "m", "age": 21,
    "level": 1, "training": 0, "xp": 35, "xpNext": 100, "points": 0,
    "dex": 3, "str": 5, "mind": 6, "cha": 5,
    "hp": 9, "hpCeiling": 9, "maxHp": 9, "hpState": "Unhurt",
    "sta": 5, "staMax": 5, "power": 7, "powerMax": 7,
    "weapon": "wooden staff", "kit": { "healing": 1, "stamina": 1 },
    "spells": { "ice": 1 }, "abilities": [], "moves": [], "alchemy": 0,
    "satisfaction": null, "traits": [], "blood": "", "tongues": "",
    "conditions": [], "wounds": [], "woundLoad": 0,
    "dead": false, "down": false, "quitting": false,
    "text": ["(YOU) Nasir -- umaia m, age 21", "  L1  training 0 ..."]
  }],
  "status": ["active quest: [q3] L1 The Thing in the Well -- next: ...", "sin: ...", "THE PACT: ..."],
  "text": ["RPG2 PARTY SHEET -- day 3, ...", "..."]
}
```

- A member's `text` is `hero_block_lines`, wrapped.
- `status` is the non-hero tail of the party sheet.
- The top-level `text` is `party_sheet_lines`, wrapped: the whole `ui/party.txt`.

### `game/map`

```json
{
  "v": 1,
  "day": 3,
  "coord": "R17C11",
  "rows": ["..............................", "..."],
  "objectives": ["R16C12"],
  "legend": [[".", "sea"], ["#", "land"], ["^", "mtns"], ["~", "river"], ["C", "city"], ["T", "town"],
             ["v", "village"], ["R", "gate ruin"], ["G", "gate city"], ["@", "party"], ["!", "job"]],
  "places": [{ "coord": "R17C11", "name": "Dar Aziza", "kind": "village", "land": "Umaia", "capital": false }],
  "here": ["HERE: R17C11 -- Umaia, plains", "..."],
  "land": { "name": "Umaia", "lines": ["[NORMAL]", "MINISTERIAL RULE", "WEATHER: steady rain."] },
  "known": ["GATES: ...", "Phyrascia cities: ..."],
  "holdings": [],
  "text": ["RPG2 MAP -- day 3", "..."]
}
```

- `rows` are the 18 rows of base glyphs from `map_glyph(world, tile)` called with no party and no objectives, so terrain shows under the markers.
- `places` lists **known** settlement slots and gates only, built from the same `known_slots` / gate records the legend uses.
- `here` is `here_lines`, wrapped. `known` is `map_legend_lines`. `text` is `map_sheet_lines`, wrapped.

### `game/quests`

```json
{
  "v": 1,
  "active": "q3",
  "quests": [{
    "id": "q3", "name": "The Thing in the Well", "level": 1, "kind": "", "origin": "Dar Aziza",
    "status": "open",
    "sites": [{ "name": "the old cellar", "level": 1, "mark": "here, room 1/1" }],
    "road": "R17C11: here", "due": 6, "note": "on time", "cargo": null, "dest": null,
    "lines": ["[q3] The Thing in the Well (L1) @ Dar Aziza", "  - ..."]
  }]
}
```

- `kind` is `"delivery"` or `""`.
- `status` is `open`, `work_done` or `proof_pending`.
- Only `accepted_quests(state)` appear, plus the active one.

### `game/record`

```json
{
  "v": 1,
  "day": 3,
  "quests": [{ "day": 2, "line": "...", "note": "..." }],
  "remarkable": [{ "day": 2, "line": "KILLED: ..." }],
  "tally": ["  (no crime committed yet)", "  clean; heat 0", "..."],
  "suggestions": [{ "key": "pickpocket", "name": "...", "line": "..." }],
  "text": ["RPG2 HISTORY -- day 3", "..."]
}
```

`text` is `history_sheet_lines`, wrapped.

### `chronicle/tNNNN`

```json
{
  "v": 1, "id": "t0005", "turn": 5, "day": 3,
  "where": "Umaia > R17C11 > Dar Aziza", "coord": "R17C11",
  "prose": "The winch lowers you ...\n\n```\n  options: camp, tavern\n```\n\n[fight]\n\n...",
  "answered": [{ "seq": 4, "kind": "say", "text": "go down after it" }],
  "fights": ["f0002"],
  "levels": { "Nasir": 1, "Amina": 1 },
  "over": false
}
```

### `fights/fNNNN`

```json
{
  "v": 1, "id": "f0003", "day": 3, "where": "...", "title": "The Thing in the Well",
  "outcome": "paused", "continues": null, "rounds": 3,
  "blocks": [
    { "kind": "opening", "lines": ["=== The Thing in the Well ===", "..."] },
    { "kind": "rounds",  "lines": ["Round 1:", "...", "Round 2-3: nothing lands."] },
    { "kind": "between", "lines": ["..."] },
    { "kind": "closing", "lines": ["The party catches its breath (+1 STA)", "...", "-- the party --", "..."] }
  ]
}
```

- `outcome` is one of `"won"`, `"lost"`, `"unresolved"`, `"retreated"`, `"paused"`.
- `continues` names the paused fight this one finishes, or is `null`.
- `rounds` is the highest round number named.
- **Invariant:** the concatenation of all `blocks[].lines` equals `CombatLog.player` for that process, which is exactly what that process appended to `ui/fight-short.txt`.

### `moves/mNNNN` (written by the page)

```json
{ "seq": 7, "at": 1790000000000, "kind": "say", "text": "..." }
{ "seq": 8, "at": 1790000000000, "kind": "pause", "fight": "f0003", "choice": "fight_on",
  "actions": [{ "hero": "Amina", "action": "heal" }] }
{ "seq": 9, "at": 1790000000000, "kind": "pause", "fight": "f0003", "choice": "retreat", "escape": "blink", "hero": "Nasir" }
```

- `kind` is `say` or `ooc` for text moves.
- For `pause`: `choice` is `fight_on` or `retreat`. `actions[].action` is one of `drink`, `heal`, `berserk`, `warbreath`, `vanish`. `escape` is `"blink"` or `"smoke"`.

### Validation (Python, `page.py`); a move is data, never obeyed

- **`clean_move(move) -> dict | None`**
  - Returns `None` unless `kind` is in `MOVE_KINDS = ("say", "ooc", "pause")` and `seq` is a whole number of at least 1.
  - Unknown fields are dropped.
  - `text` is stripped and capped at 2000. Hero names are capped at 40. `actions` holds at most 8 entries, and only known actions survive. `choice`, `escape` and `action` must come from the fixed sets.
- **`pause_args(move, state, *, paused_fight) -> list[str]`** returns the `session.py` argv, e.g. `["resume", "--heal", "Amina"]` or `["retreat", "--blink", "Nasir"]`. Otherwise it raises `MoveRefused(reason)`, which is a `ValueError`. It refuses when:
  - no fight is paused;
  - `move.fight` is not the fight that paused (the pause is already over);
  - it is a Fate pause and the move carries actions (an escape is allowed: see Session 1's notes);
  - a hero is not in the party, not alive, or named twice;
  - a hero fails an item, ability or Power gate. This must use the **same** checker as `cmd_resume` / `cmd_retreat`; see the refactor in Session 1;
  - `blink` is asked without teleport rank 2, or `smoke` without a vial;
  - a name `find_hero` would resolve to a different hero (the substring trap).
  
  Names in the argv are the hero's full `name`. Only the newest valid pause move in a turn is played; earlier ones are reported as superseded.
- **The page mirrors `clean_move`** in `cleanBody` (`store.ts`) and `readMove` (`model.ts`).

---

## SESSION 1 — The projection (`page.py`) and the session refactors

**Goal:** a pure, tested Python projection of any `session.load()` state into the five singletons, plus the move contract, with no web and no publish yet.

### Files

- **Create `page.py`**
  - Docstring in dream `view.py`'s style: what crosses, what never crosses, and the decisions made.
  - `VIEW_VERSION`, `STATUSES`, `MOVE_KINDS`, `MOVE_TEXT_MAX`, `SINGLETONS = ("game/state", "game/party", "game/map", "game/quests", "game/record")`.
  - `player_view(state, *, status, last_seq, latest, check_in, last_fight, pause_fight)`, `state_view`, `party_view`, `map_view`, `quests_view`, `record_view`.
  - `chronicle_id`, `chronicle_entry(turn, prose, answered, *, state)`, `clean_move`, `MoveRefused`, `pause_args`.
  - `wrapped(lines)`: `session._wrap_block(...).splitlines()`.
  - Menu capture with `contextlib.redirect_stdout` around `session.print_pause_menu` / `print_levelup_menu`.
  - `import session` at the top. **session must not import page at module level**; Session 2 adds a lazy import inside `print_combat` to avoid the cycle.
- **Modify `session.py`**
  - `RPG2_HOME = Path(os.environ.get("RPG2_HOME") or Path(__file__).parent)`. Then `STATE_PATH = RPG2_HOME / "save.json"` and `UI_DIR = RPG2_HOME / "ui"`, with the other `*_PATH` derived as now.
  - `cmd_sheet`: when `RPG2_HOME` is not the repo directory, write the pages and print that nothing was committed.
  - Split `print_pause_menu` into `pause_menu_data(state) -> dict` (trips, facing, party rows, options with eligible heroes) plus the printer that renders it. The printed text must stay byte-identical; test it.
  - Extract `check_pause_actions(state, requests) -> dict[Entity, str]` from `cmd_resume`'s loop, raising `ValueError(reason)`. `cmd_resume` prints the reason and returns, so behaviour is unchanged.
  - Add the same kind of checker for retreat escapes (`check_escape(state, how, name)`).
  - Extract `party_status_lines(state)` (the tail of `party_sheet_lines` after the hero blocks). `party_sheet_lines` calls it.
- **Create `test_page.py`** (unittest; `python -m unittest -v test_page.py` or `python test_page.py`). Sandbox pattern: extend `test_start.sandbox` or copy it, repointing `STATE_PATH`, `UI_DIR` and all `*_PATH`.
- **Modify `.gitignore`**: add `ui/queue/`, `web/out/`, `web/dist/`, `web/app/dist/`, `web/app/.angular/`, `node_modules/`.

### Copy, adapt, drop

- **Adapt from dream `view.py`**: the module docstring's shape; `clean_move`; `MoveRefused`; `chronicle_id` / `chronicle_entry` (swap `phase`, `subject` and `defeat` for `coord` and `over`); the `SINGLETONS` idea.
- **Drop**: everything school, realm, class and rules, and the fight parser.

### Tests (`test_page.py`, part 1)

1. A fresh `new --seed S --level 1` projects. Every doc is JSON, under 256 KiB, with the fields above. `game/state.coord` equals the party's tile coordinate.
2. The text fields equal the ui pages: `game/party.text == _wrap_block(party_sheet_lines).splitlines()`, and the same for map and record.
3. **Secrets never cross.**
   - Walk every string and key. No `rng` or `world` key. No name of an untaken, open quest on the world's boards appears (collect names not in `accepted_quests` and not active). No name of an unknown settlement slot appears. No foe name from a taken quest's *unentered* rooms appears.
   - The map `places` holds known slots only, and `rows` equals the gutter-stripped `map_lines(world)` with no marks.
4. `pause_menu_data` plus the printer reproduce the old menu text exactly, for both a wounds pause and a Fate pause. Reuse fixtures from `test_mercy.py` / `test_turnin.py` that reach `pending`, or loop seeds with `fight N --type troll`.
5. `pause_args`: fight on; heal a hero with a potion gives the argv; heal a hero with no potion raises `MoveRefused`; a Fate pause with an action raises; a duplicate hero raises; an unknown hero raises; a stale `fight` id raises; no pause raises; blink without teleport 2 raises. The argv resolves through `find_hero` to the same hero.
6. `clean_move` drops unknown kinds, fields and seq below 1, and caps text.
7. `chronicle_entry` keeps the answered moves cleaned and in seq order, and stamps levels.
8. `levelUp` appears when the PC has banked points (set `skill_points` in a sandboxed state).

Also run `test_ui_logs.py`, `test_history.py`, `test_start.py`, `test_mercy.py`, `test_turnin.py` and `test_navigation.py`, because `session.py` was touched. Once per session, run the whole suite with `python -m unittest discover -p "test_*.py"` and record the count.

### Docs

- develop.md **Files**: entries for `page.py` and `test_page.py`. **Running**: `python -m unittest -v test_page.py`.
- `plan.md`: add a short entry, "THE PLAYER'S PAGE ARC", pointing at the saved plan file. Each session removes its part when it ships.
- designlog.md: `## <date> — The player's page, session 1: the projection`, with the calls the build settled.

### Acceptance

- The suites pass.
- `python -c "import session, page, json; print(json.dumps(page.player_view(session.load())))"` works on a fresh `new` inside a temp `RPG2_HOME`.
- `print_pause_menu` output is unchanged.

### Session 1 notes / deviations (2026-09-25, as built)

Read these before Session 2; designlog 2026-09-25 has the full record.

- **Signatures as built.** `player_view(state, *, status="awaiting_player", last_seq=0, latest=None, check_in=None, last_fight=None, pause_fight=None)`; `state_view` takes the same. `check_in=None` becomes `page.CHECK_IN` ("when you call from Claude Code"), so `publish.py` need not default it. `chronicle_entry(turn, prose, answered=(), *, state, fights=())`. `pause_args(move, state, *, paused_fight)` -- the paused fight's id is **handed in** (the save does not know published ids): Session 2's `page.py moves` passes `game/state.pause.fight` from `--state`. `None` refuses every pause move as stale.
- **`pause.kind` is `"normal"` or `"fate"`**, not `"wounds"` (section 2 corrected). Each option carries `choice`, `label`, `cost`; action options carry `heroes` (the names that pass the checker right now, possibly empty); `blink` / `smoke` carry `hero` (the menu's one named hero). The session-side dict (`session.pause_menu_data`) is snake_case and also keeps `cmd` (the printed command line) and `crossings`; `page.pause_view` drops `cmd`.
- **A Fate pause keeps blink and smoke** (section 2 corrected): the old menu printed them at a Fate pause, `retreat` took them, and rules.md (the Fate section: "A CLEAN RETREAT pays it too ... a smoke-vial break, and a rank-2 blink-out alike") says so. `pause_args` refuses only *actions* at Fate.
- **`clean_move` is whole-or-nothing for `pause`**: a `choice`, `escape` or `action` outside the fixed sets, an action or escape without a hero, `actions` not a list or longer than 8 makes the move `None` ("not a move") rather than dropping the bad part and playing the rest. A `fight_on` move keeps only `actions`; a `retreat` keeps only `escape` + `hero`. `at` is kept when numeric. `seq` must be an int (or an integral float) of at least 1 -- a string seq is not a move. The page's `cleanBody` / `readMove` (Session 3) should mirror this.
- **The checkers.** `session.check_pause_actions(state, [(flag, name), ...]) -> {Entity: engine action}` (flag words `drink heal berserk warbreath vanish` = `session.PAUSE_ACTIONS`; `warbreath` maps to the engine's `war-breath`) and `session.check_escape(state, how, name) -> Entity` (`session.ESCAPES`), both raising `ValueError(the line resume/retreat prints)`. Per-hero reasons are `pause_action_refusal` / `escape_refusal`; `pause_menu_data`'s `heroes` lists use the same. **One behaviour change**: `retreat --blink HERO` without teleport rank 2 is now refused before anything rolls (it used to log "rank 2 needed" and run the honest retreat, parting blows and all); and both escapes are checked up front. A blink with too little Power is still not refused (the door fails and the honest retreat runs, as the menu prices it).
- **`pause_args` names heroes by their whole name** (case-insensitive exact match), refuses a name `find_hero`'s substring match would send to another hero, and emits the full `name` in the argv. Session 2's printout must shell-quote names (`shlex.quote`): names can hold spaces.
- **Extra session refactors** the projection needed, all byte-identical to the pages (tested): `quest_site_marks` + `quest_in_hand_lines` (the map's quests in hand), `sin_tally_lines` + `hell_suggestions` (the history page's last two sections), and `find_hero` now goes through the silent `_hero_named`.
- **`RPG2_HOME`**: `session.REPO_DIR` is the repo, `session.RPG2_HOME` the base. `sheet` compares the two and, when they differ, prints "UI pages written under ... nothing was committed." Paths stay module constants computed at import; the suites still repoint them (`test_page.sandbox` repoints `STATE_PATH`, `UI_DIR` and all five page paths -- reuse it for Session 2, and compute queue paths from `session.UI_DIR` at call time as planned).
- **`game/state.over`** is computed from the save (`page.game_over`: all dead -> `wiped`, else the PC dead -> `pc_dead`); `pause` and `levelUp` are `None` once over. `levelUp` is the PC's only (companions autolevel).
- **Map `places`** are the four gates first (kind `gate ruin` / `gate city`, `capital: false`), then the known slots in `tile_order`, kind = the slot's tier (`hamlet`...`metropolis`); `land` is the tile's country's name. `legend` is parsed from places' three legend strings. `holdings` is `conquest.holdings_lines` wrapped (`[]` with none).
- **`game/quests`**: `road` is the first `_quest_road_lines` line or `""`; `due` is `deadline_day` (may be `None`); `note` is `deadline_note` for open/work-done jobs. `game/record.quests[].note` is `""` when the record has none; `record` lists stay oldest first (the page reverses).
- Test count: `test_page.py` 37 tests; the full discover run is in the designlog entry.

---

## SESSION 2 — Fights kept, `publish.py`, the page record, the move checker

**Goal:** the whole keeper's turn works from the terminal, with no page yet.

### Files

- **Modify `rpg.py` (`CombatLog`)**
  - Add `self.round_spans: list[list[int]]`. `round_start` opens a span at `len(self.player)` when none is open; `finish_rounds` closes it at `len(self.player)`.
  - Add `self.outcome: str | None = None`.
  - This is engine-generic and pure bookkeeping. Plain-list benches are untouched.
- **Modify `session.py`**
  - `print_combat(log, state=None)`: pass `state` at every call site. After flushing, when `log.player_path` is set and `state` is given, do a lazy `import page` and call `page.keep_fight(state, log)`. Render outside and I/O inside a try, the `_write_party_sheet` contract, so it never breaks the game.
  - Set `log.outcome`:
    - `"paused"` in the pause branches (`resolve_encounter`, `cmd_resume`, `cmd_retreat` run-down);
    - `"lost"` on a wipe or mercy in `finish_encounter`;
    - `"unresolved"` on the not-cleared branch;
    - `"won"` otherwise;
    - `"retreated"` on a clean escape in `cmd_retreat`.
  - Confirm `state["pending"]` is cleared before `print_combat` on escape.
  - `cmd_new` removes `UI_DIR/page.json` and `UI_DIR/queue/`: one page is one game.
  - Add `"ui/page.json"` to `UI_COMMIT_PATHS`, and update `test_ui_logs`'s commit-set test.
- **Extend `page.py`**
  - `keep_fight(state, log)` writes `UI_DIR/queue/qNNN.json` = `{day, where, coord, title, outcome, continuing: log.continuing, blocks}`. Blocks come from `round_spans`: opening, rounds, between, closing. `rounds` is the maximum `^Round (\d+)(?:-(\d+))?:`.
  - `queued_fights()`. Paths are computed from `session.UI_DIR` **at call time**, so the sandboxes work.
  - `fight_id(n)`.
  - A CLI, `python page.py moves MOVES.json [--state STATE.json]`. For every move with `seq > lastSeq` it prints one line:
    - `m0004 say: <text>`;
    - `m0005 pause -> python session.py resume --heal Amina`;
    - `m0006 pause REFUSED: Amina carries no healing potion (answer it in the fiction)`;
    - `m0007 superseded by m0008`;
    - `m0009 not a move; deleted unanswered`.
  - It reads `save.json` through `session.load()`. It prints, and **never runs** a command.
- **Create `publish.py`**
  - Adapt dream's `publish.py` almost line for line. Keep `read_json`, `write_json` (with `DOC_MAX`), `set_write`, `read_page`, `read_moves`, `sent`, `BATCH_MAX`, the pinning logic, the `--versions` / `--state` / `--state-version` handling, `--status`, `--check-in`, `--all`, `--out` and `--url`.
  - The save is read with `session.load()`. There is no positional SAVE argument; use `RPG2_HOME`.
  - `page.json` lives at `session.UI_DIR / "page.json"`. It is renamed "the page's record" and holds `{"url": ..., "versions": {"game/state": 3, "fights/f0003": 1}}`.
  - Fights: number the queue after `lastFight`, only with `--prose`. A queue entry with `continuing: true` gets `continues` = the previous fight id: the previous queued entry this run, else `lastFight` read from `--state`. Paused fights get `outcome: "paused"`.
  - `game/state.pause.fight` is the id of the newest fight when `state["pending"]` is set.
  - The chronicle entry's prose is the file's text, stripped. Count the `[fight]` paragraphs; warn on stderr when there are more markers than fights.
  - `--sent` also appends the sent entry to `UI_DIR/transcript.md` as `## turn N (day D)`, then `> ` plus each answered move's words, then the prose. It removes the sent queue files. It advances the versions of every `game/` doc it set.
  - The dream mechanism for "a numbered fight is already on the page" carries over: a queue file keeps its id once numbered, and is dropped when `lastFight >= id`.
  - Summary line: `Published day D at WHERE: lastSeq N, tNNNN answering K moves with F fights.` followed by the url instruction.

### Copy, adapt, drop

- **Verbatim**: `publish.py`'s batch, pin, `sent` and `read_moves` machinery.
- **Adapt**: the projection calls and the queue location.
- **Drop**: `party.calendar`, `D.chronicle_entry`'s school fields, and `saves/queue`.

### Tests (`test_page.py`, part 2)

1. **Queue fidelity.** In the sandbox, run `fight 2 --type wolf` through `session.build_parser()`. The queue holds one entry, and its concatenated blocks equal `ui/fight-short.txt`'s lines. There is an opening block, at least one round header, and the closing block ends with the tally.
2. **A paused fight.** Find a seed or foe that pauses. The entry has `outcome: "paused"`. `resume` makes a second entry with `continuing: true`. Its blocks concatenated equal the lines appended to `fight-short.txt` by the resume.
3. **Walkover.** Two fights in one process sequence give two queue entries.
4. **`publish.py` by subprocess** with env `RPG2_HOME=tmp` and `--out tmp/out`, mirroring dream's publish test:
   - the first publish sets every singleton; `--state` pins `game/state`; moves are deleted and pinned; the chronicle and fights come out; `lastSeq`, `latest` and `lastFight` are advanced;
   - `--sent` writes `page.json` versions, appends the transcript, and clears the queue;
   - a second publish sends only what changed;
   - `--sent --url` records the url;
   - `--all` with no reads pins from the record;
   - `checkIn` defaults to `"when you call from Claude Code"`;
   - a paused fight's continuation gets `continues`;
   - no batch exceeds 50 writes.
5. **`page.py moves`** prints the argv, a refusal and a superseded line on crafted inputs.
6. **`new`** removes `page.json` and the queue.

### Docs

- develop.md Files: `publish.py`, `page.py`'s CLI, and the `CombatLog.round_spans` / `outcome` note on the `rpg.py` entry. Dev map entry "The player's page". Running lines.
- Start `web/README.md` with the Python half: publish, the keeper's turn, pins, queue, record.
- designlog entry.

### Acceptance

A complete terminal keeper's turn in a temp `RPG2_HOME`: `new`, write a prose file, `publish.py --all --prose`, `--sent`, a fight, publish again. The output batch files validate.

### Session 2 notes / deviations (2026-09-25, as built)

Read these before Session 3; designlog 2026-09-25 (B) has the full record.

- **The fight document** is `{v, id, day, where, coord, title, outcome, continues, rounds, blocks}` -- `coord` added beside `where` (the party's Tile coordinate, as in `game/state`). Block kinds are `opening`, `rounds`, `between`, `closing`; empty blocks are left out. A second half (`continues` set) has **no `opening`**: it starts with `rounds` (resume, a run-down retreat) or is one `closing` block (a clean escape, a mercy). A log with no rounds at all is one `opening` block. `between` needs two stretches of rounds in one process, which the engine does not produce today; the page should still render it.
- **`title`** is the fight's `===` banner without its rules (joined when fitted over two lines); a fight with no banner (the bare `fight N --type X` command) is named by its first log line, the roster's ("2x Wolf -- fangs"). A second half takes its first half's title (read off `ui/fight-short.txt`, which holds the whole fight by then).
- **`[fight]` markers** (`page.fight_markers`): a line that is exactly `[fight]` after trimming, outside a ``` fence, with a blank line (or the start/end of the prose) on both sides. The Story renderer must use the same rule. Spare markers are left as written (publish warns on stderr); fights the prose did not place follow it.
- **`game/state.pause.fight` can be null while a pause stands**: when fights wait in the queue unpublished (a publish without `--prose`), the page does not hold the paused fight, so there is nothing to point at. The picker should not offer a send with a null fight (the keeper would refuse it as stale).
- **Move words** (`page.move_words`, used for the transcript's `>` lines) -- Session 3's `moveWords` should say the same: say = the text; ooc = `(to the DM) TEXT`; pause fight on = `At the pause: Amina drinks a healing potion; Nasir goes berserk; fight on` (drink = "drinks a stamina draught", heal = "drinks a healing potion", berserk = "goes berserk", warbreath = "draws the war-breath", vanish = "vanishes"); retreat = `At the pause: retreat`, or `At the pause: retreat -- Nasir blinks the party out` / `-- Amina breaks a smoke vial`.
- **Only the newest pause move of a turn is weighed** (`page.moves_report`): it is played as printed or REFUSED; every earlier pause move of the turn is "superseded by" it, even when the newest is refused -- the player's latest word governs, and an older choice is never played in its place. Moves at or under `lastSeq` print "answered by an earlier turn; deleted". `page.py moves` without `--state` reads the last publish's `game/state`.
- **`read_moves` lives in `page.py`** (both `publish.py` and `page.py moves` read moves); `publish.py` keeps the batch, pin, `sent` and file machinery verbatim. **`--queue` is dropped**: the queue is always `ui/queue/` under `RPG2_HOME`.
- **`web/out/` defaults to `RPG2_HOME/web/out`** (the repo's own in play, gitignored): one home is one game, so a temp home keeps its publish output beside its save. The batch's `file_path`s are absolute. **Note for the e2e**: `RPG2_HOME` must exist before `session.py new` (the save's directory is not created -- older behaviour, untouched).
- **The page's record holds `game/` versions only** (the plan's example listed a `fights/` version; fights are write-once and never pinned, as in dream).
- **No record, no last**: a publish with no `ui/page.json` (a new game: `new` drops it) neither compares with nor reads the handshake from `web/out/last/`, so a new game's first publish writes every singleton, unpinned, and starts at `t0001` / `f0001`.
- **`--sent` appends the turn to `ui/transcript.md`**: `## turn N (day D)`, a blank line, one `> ` line per answered move (`move_words`, superseded pause moves included -- they are what the player sent), a blank line, the prose with each placed `[fight]` paragraph written `[fight f0003: TITLE, OUTCOME]` and unplaced fights after it.
- **Every session fight is kept**, chat play included (the queue is gitignored; `new` empties it). A game moved from chat to the page mid-way would publish the whole backlog on its first `--prose` publish: Session 5's protocol should say to empty `ui/queue/` before the first publish of a game already under way.
- **`test_gates._run` now sandboxes the fight pages** (`UI_DIR` and both snapshot paths patched to a temp dir): its retreat test used to append to the repo's `ui/fight-short.txt`, which is how Session 1's `sheet` came to commit stray `ui/fight-*.txt` (removed this session).
- Test count: `test_page.py` 52 tests (37 + 15); `test_ui_logs.py` +1; the full discover run 1350 OK.

---

## SESSION 3 — The Angular page: scaffold, store, Story, Answer, Chronicle, Party, Fight, Fights

**Goal:** a buildable page that plays the basic loop against the fake store, plus the first e2e.

### Files, with the dream → rpg2 mapping

| rpg2 file | from dream | action |
|---|---|---|
| `web/app/package.json`, `package-lock.json` | same | copy; rename `dream-page` → `rpg2-page` in both |
| `web/app/angular.json` | same | copy; project `rpg2`, prefix `rpg`; same budgets and `outputHashing: none` |
| `web/app/tsconfig.json`, `tsconfig.app.json` | same | verbatim |
| `web/app/src/main.ts`, `app/app.config.ts` | same | verbatim (zoneless) |
| `web/app/src/index.html` | same | adapt: title RPG2, `<rpg-root>`, no font link |
| `web/page.html` | same | adapt: `<title>RPG2</title>`, `styles.css`, `<rpg-root><p class="boot">Loading the game.</p></rpg-root>`, `main.js` module; no fonts |
| `web/build-artifact.mjs` | same | copy; `built = app/dist/rpg2/browser` |
| `web/dev/serve.mjs`, `dev/fake-db.js` | same | verbatim, bar the comments |
| `web/dev/db.mjs` | same | copy; env `RPG2_TABLE` instead of `DREAM_TABLE` |
| `src/app/store.ts` | same | copy the plumbing (`connect`, `doc`, `collection`, `register`, `send`, `nextSeq`, `onDbError`, `cleanBody`) verbatim; rename `DreamStore` → `TableStore`; documents: `state`, `party`, `map`, `quests`, `record`, `chronicle`, `fights`, `moves`; computeds `fightById`, `pending`, `awaitingDm`, `latest`, `pc` |
| `src/app/model.ts` | same | copy helpers `num`/`str`/`arr`/`obj`/`strs`/`oneOf`, `moveId`, `paragraphs`; rewrite readers for the contract in section 2; `MoveBody` for say/ooc/pause; `moveWords` (pause in words: "At the pause: Amina drinks a healing potion; fight on") |
| `src/app/ui.ts` | same | adapt: views `story` / `party` / `drawer`; `openFight`; no `dayTarget`, school default or `fightsFace`; key `rpg2.tab`; add a `prefill` signal for option chips |
| `src/app/unread.ts` | same | copy; key `rpg2.seen`; signatures for party, map, fight, fights, quests, record |
| `src/app/drawer/drawer.ts` | same | copy; the Party tab component becomes `Party` |
| `src/app/drawer/tabs.ts` | same | new list: Map (bar), Fight (bar), Fights, Quests, Record. Session 3 ships Fight and Fights; Session 4 adds Map, Quests and Record |
| `src/app/app.ts` | same | adapt: header "RPG2 · Day N · where" in ASCII (no "·": use CSS separators), no realities or defeat; `data-paused` and `data-over` on `:root`; bottom bar Story / Party / tabs / More |
| `src/app/panels/story.ts` | same | rewrite the body: render prose as blocks (paragraphs; fenced ``` blocks as `<pre class="display">`; a `[fight]` paragraph as a `<rpg-fight-card>` for the next fight id; leftover fights after) |
| `panels/answer.ts` | same | copy the logic; copy table below; draft key `rpg2.draft` |
| `panels/chronicle.ts` | same | adapt: group by day only (no halves); use the same block renderer for prose; level-up lines from `levels`; search |
| `panels/fight-chip.ts` | same | adapt the words ("a fight: TITLE, won"); `continues` shows "the fight goes on: ..." |
| `panels/fight.ts` | same | rewrite: header (day, where, outcome, rounds), prev/next stepping (keep dream's), blocks as `<pre>`; rounds block split into rounds, each collapsible with the newest open; line classes by regex (`SLAIN`, `DOWN`, `^!! `, `dmg!+`) for colour only; a continuation shows its paused first half above, collapsed; paused fight: "PAUSED after round N" and a button to the Story's pause picker (the picker itself is Session 4) |
| `panels/fights.ts` | same | adapt: list newest first (day, where, title, outcome, rounds); no face filter |
| `panels/party.ts` (new, replaces `line.ts` / `member.ts`) | line/member | cards: name, (YOU) / companion, L, XP bar, HP / STA / Power meters, kit, weapon, spells / abilities / moves, satisfaction, conditions and wounds as tags; "the sheet as printed" `<details>` with `text`; party `status` lines; purse |
| `src/styles.css` | same | copy the base, layout and bottom bar; one palette, light and dark (tokens only, no realities); `.display` (mono, `white-space: pre`, font-size so 40ch fits 360px); outcome colours |
| `web/e2e.mjs` | same | adapt the plumbing (`check`, `launch` with the `/opt/pw-browsers/.../chrome` fallback, `open`, `phoneTab`, `noSideScroll`, `shoot` without font waits); a Python helper runs `session.py` with env `RPG2_HOME=<out>`; `PHONE = 412x915` mobile, `SMALL = 360x740`, `MID = 1100`, `WIDE = 1440` |
| `.gitignore` | same | already covered in Session 1 |

**Drop**: `history.ts` (keep only a tiny level-up derivation inside the chronicle), `school.ts`, `class.ts`, `realm.ts`, `days.ts`, `rules.ts`, `rich.ts`, `hp-track.ts`, `member.css`, `line.ts`.

### Copy table (page chrome, ASCII, writing.md's register)

| Where | Text |
|---|---|
| Boot | "Loading the game." |
| Connecting notice | "Connecting." |
| No game yet | "No game yet. Ask the DM in Claude Code to start one. The first scene appears here." |
| Connection lost | "The connection dropped. Reload the page." |
| No db | "This page has no line to the game. Open it on claude.ai, signed in." |
| Status line | "Your move" / "1 move waiting on the DM" / "N moves waiting on the DM" / "The DM is writing" / "GAME OVER" / "the DM looks when you call from Claude Code" |
| Answer | heading "Your move, as NAME"; toggle "In the game" / "To the DM"; placeholders "What do you do?" / "Ask the DM, out of the game" |
| Read-only | "You can read this game but not write to it." |

### Tests

- `cd web/app && npm ci && npx ng build && node ../build-artifact.mjs` must be green, with no stray bundle and within budget.
- **`node web/e2e.mjs` v1:**
  1. **Opening.** `new --seed S --level 1`. Write an opening in the rpg2 voice with an options fence to `ui/scene.md` under `RPG2_HOME`. Run `publish.py --all --prose`. Start the server with the batch, then `--sent`. The phone shows the prose, the fenced display in mono, the header day and place, "Your move", and "as NAME".
  2. **Two moves.** A say and an ooc. Both are pending in the chronicle; the store holds `m0001` and `m0002`.
  3. **Keeper's turn.** List and get into files, publish, post the batch, `--sent`. The page shows the new turn with the player's words under it and the queue cleared. Replaying the same batch gets 409. The transcript file gained the turn.
  4. **A fight.** Run `session.py fight 2 --type wolf`, then publish prose that contains `[fight]` between two fences. The card sits in place in the story. Tapping it opens the Fight tab. The lines equal `ui/fight-short.txt`. The Fights list has it.
  5. **Party tab.** Cards for the PC and the companion; the printed sheet in `<details>` matches `ui/party.txt`.
  6. **Layout.** No side scroll at 412 and 360. The bottom bar is five buttons that fit. Screenshots at phone light/dark and wide.
  7. **Fallbacks.** `?readonly` and `?nodb`.

### Docs

- `web/README.md`: layout, build, run locally, test.
- develop.md Files: the `web/` entry, sub-bullets for `web/README.md`, `web/e2e.mjs`, `web/dev/`, `web/build-artifact.mjs`. Running: the build and e2e commands.
- designlog entry. Mark the session's part of the plan.md entry as shipped by deleting it.

### Acceptance

The build is green and e2e v1 is all ok. Screenshots are reviewed at 412px: readable displays, no clipped 40-column lines, thumb targets at least 48px.


### Session 3 notes / deviations (2026-09-25, as built)

Read these before Session 4; designlog 2026-09-25 (C) has the full record.

- **The bottom bar is four buttons today**: Story, Party, Fight, More (More holds Fights). The plan's five need the Map; Session 4 gives the Map tab `bar: true` in `drawer/tabs.ts` (order Map before Fight) and changes the e2e's bar check (`bar.length === 4`, `'Story Party Fight More'`) to five / `'Story Party Map Fight More'`.
- **Unread marks are live already** (dream's machinery whole, key `rpg2.seen`) with signatures for `party`, `fight`, `fights`; Session 4 adds `map`, `quests`, `record` and the e2e checks.
- **The pause, until the picker**: the Story shows a stand-in `<section id="pause">` while `state.pause` is set and the game is not over -- "PAUSED after round N", the trips, "Fight on or retreat: say it in the box below.", an "Open the fight" link and "The menu, as printed" (`pause.text`) in a fold. Session 4 replaces its body with the picker and keeps `id="pause"`: `ui.openPause()` (the Fight tab's "To the pause" button, shown on the fight the game stands paused on while no continuation is published) scrolls to it.
- **The option chips' plumbing is in**: `ui.fill(text)` sets `ui.prefill`, and the Answer box takes the words (say mode), focuses and never sends. Session 4 only parses an `options:` display into chips that call `ui.fill`.
- **`data-paused` and `data-over` are set on `:root`** (`data-over` holds the `over` word, or `true` for a plain `--status ended`) with no styling yet; the answer box already closes with "GAME OVER" when `status` is `ended`.
- **The store never sends a pause** unless `state.pause.fight` is set, equals the move's `fight`, and the game is not over (`TableStore.send`). `model.cleanBody` mirrors `clean_move` whole or nothing; `readMove` is as strict as `clean_move` (a kind is required, `seq` a whole number of at least 1; dream defaulted the kind and read the seq off the id). `nextSeq` still counts a malformed move document's seq (its body's, or its id's digits), so the page never writes over one.
- **One prose renderer**, `panels/prose.ts` (a file the plan's table did not name), sets a turn for the Story and the Chronicle alike through `model.proseBlocks` (paragraphs; fences as `<pre class="display">`; `[fight]` by `page.fight_markers`' rule, a spare marker left as text; unplaced fights after). The in-place card is `rpg-fight-chip` (the plan's `rpg-fight-card` name was not used): "a fight: TITLE, won" / "the fight goes on: TITLE, PAUSED after round N". Session 4's options chips hook into `proseBlocks`' `display` block (a display whose first line starts `options:`).
- **The chronicle** says every move with `moveWords` (answered and waiting alike, so an ooc reads "(to the DM) ..."), labels DM / You / Sent / Level, and a level line reads "NAME reaches level N." (derived from `levels`, no feature text).
- **The Fight tab**: the rounds fold with the newest open and an "Open every round" toggle; each printed line is a `.ln` span, so `rpg-fight .main .ln` textContent is the log line for line (the e2e compares it with `ui/fight-short.txt`); a second half shows its first half folded above; a first half links "The fight goes on >" once its continuation is published. Stepping is "< Earlier" / "Later >".
- **Layout numbers**: three zones at >= 1241px (party 400px, drawer 440px), two below (drawer 420px), one with the bar at <= 900px. `--mono-size` is 13px, 12.5px at <= 380px; a display inside a party card drops its box so 40 columns fit 360px. The e2e's `displaysFit` asserts no display is clipped or scrolled at every width it shoots.
- **The e2e** plays seed 5 (Mansur and his companion Yusuf at Sidi Farhan) under `DIR/home`; the prose goes through `DIR/home/ui/scene.md`. Session 4 extends `web/e2e.mjs` in place (its `publish`, `phoneTab`, `displaysFit`, `smallTargets` helpers).
- `web/app/.gitignore` came along from dream (node_modules, dist, .angular, out-tsc); `npm ci` worked against dream's lock with only the name changed.

---

## SESSION 4 — The pause picker, Map, Quests, Record, level-up, option chips, marks

**Goal:** everything rpg2-specific on the page, and the full e2e.

### Files

- **`panels/pause.ts`** (new). It is shown in the Story above the answer box when `state.pause` is set, `status` is not `ended`, and no pending pause move exists.
  - It shows the fight's "PAUSED after round N", the trips, a facing list, and each hero's row (`hpState`, HP digits, STA, Power, penalties, tags, potions): the pause menu, structured.
  - Choice 1 is **Fight on** or **Retreat**.
  - Under Fight on, per-hero action chips come from `options`. One action per hero is enforced in the UI; the chips are disabled at a Fate pause.
  - Under Retreat, the optional Blink (hero) or Smoke (hero) comes from `options`.
  - A summary line gives the resulting words. Send is `store.send({kind: 'pause', fight, choice, actions, escape, hero})`.
  - "The exact menu" sits in `<details>` with `pause.text`.
  - After sending, it shows "Sent. Waiting on the DM." The answer box stays available for words.
- **`panels/map.ts`** (new).
  - An SVG of 30×18 cells built from `rows`, with glyph classes for sea, land, mountains and river. Markers: the settlement letter (C/T/v/R/G), `@` over the party cell, `!` over objectives. Axis labels every 5.
  - Tapping a cell shows "R12C14 -- land. Venice (city, Byzantium)" using `places` and the legend words.
  - Below it: the `here` block, the `land` block, `known` and `holdings` as `<pre class="display">`.
  - A "text map" toggle shows the exact `text`.
  - Width: `viewBox`, 100% width, so cells are about 12–13px on a 412px phone.
- **`panels/quests.ts`** (new): a card per quest in hand (name, level, origin, sites with their marks, road days, due day and note, delivery cargo and destination). An empty state reads "No job in hand."
- **`panels/record.ts`** (new): QUESTS DONE, REMARKABLE, THE TALLY OF SIN and SUGGESTIONS, as in `history.txt`, in sections, newest first.
- **Party tab**: a `levelUp` block with the points and the menu `text` in `<pre>`, plus the note "Say what to spend them on." The PC card gets a "points to spend" mark.
- **Story, option chips**: a fenced block whose first line starts with `options:` (after trimming) is parsed. Wrapped continuation lines are joined, the prefix is cut, and the rest is split on `", "`. It is rendered as the display plus a row of chips. A tap sets `ui.prefill`; `Answer` puts the words in the box and focuses it. **It never sends.**
- **`app.ts` and `styles.css`**: `data-paused` gives an accent border on the Story; `data-over` greys the page and closes the answer box with "GAME OVER".
- **`unread.ts`**: signatures for map, quests and record.
- **`tabs.ts`**: final list and bottom bar Story, Party, Map, Fight, More, with More holding Fights, Quests and Record.

### E2E, extended (`node web/e2e.mjs`)

Everything from v1, plus:

1. **A paused fight.** The Python helper finds a foe or count that pauses from the save's state: copy the save, try, keep the first that pauses. Publish with `[fight]`.
   - The picker offers only eligible actions, e.g. heal for heroes carrying a healing potion.
   - The player picks heal on a hero plus Fight on. The move lands in `moves/` with `fight` equal to the paused id.
   - The keeper runs `python page.py moves ...`, which prints `python session.py resume --heal NAME`. The keeper runs that and publishes.
   - A continuation fight with `continues` appears, the picker is gone, and the chronicle has both chips.
2. **A refused move.** Write a tampered pause move directly through `/__db/write` for a hero with no potion. `page.py moves` prints REFUSED with the reason. The publish deletes the move and the turn's prose answers it.
3. **Map tab.** 540 cells. The `@` cell's coordinate equals `game/state.coord`. Tapping the party cell names the local settlement. **No unknown settlement name is anywhere in the store**: a Python helper lists unknown slot names and the check scans `/__db/dump`.
4. **Quests tab** after `session.py take QID` (a job at the start settlement; `opening_hook` names it), with its sites and due day. **Record tab** sections.
5. **Level-up.** `session.py award 0 <XP> <PC>` to cross a level. The Party tab shows the menu. The chronicle shows "NAME reaches level 2".
6. **Option chips.** Tapping one fills the box and does not send (the moves count is unchanged).
7. **Unread marks.** A new fight marks Fight and Fights. Looking clears the mark. A reload remembers it. Blocked storage breaks nothing (`context.addInitScript` makes localStorage throw).
8. **Game over dressing.** Force it by editing a copy of the save to kill the PC, then publish with `--status ended`: `data-over` is set and the answer box is closed.
9. Screenshots at phone 412 (light and dark), small 360, mid 1100 and wide 1440. No side scroll at any of them.

### Tests (Python)

Add to `test_page.py`:
- `map_view.places` equals the known slots.
- `quests_view` holds accepted quests only.
- The `options` of `pause` match `pause_menu_data` eligibility, e.g. no `berserk` unless a hero knows it.
- `record_view` equals the history sheet.

### Docs

- `web/README.md`: tabs, the pause picker, "Adding to the page" (adapted from dream's: a tab, a document, a move kind — with the Python side in `page.py`'s `MOVE_KINDS` / `clean_move` and a checker like `pause_args`).
- develop.md dev map.
- designlog entry.

### Acceptance

The full e2e is all ok and the screenshots are reviewed at 412 and 360. All touched Python suites pass, and the full discover run matches or exceeds the last count.

---

## SESSION 5 — The play protocol, docs, and a dress rehearsal

**Goal:** a DM can run rpg2 through the page from the docs alone.

### Files

- **`dm.md`**: a new section after "The scene page", **"## Page play -- the player's page"**. It says that when the game is played through the page, it replaces the chat copy and the party.txt link. It covers:
  1. **When.** The player asks for the page, or `ui/page.json` has a `url`. One page is one game: `new` drops the record, so a new game gets a new page.
  2. **Publish the page.**
     - Build: `cd web/app && npm ci && npx ng build && node ../build-artifact.mjs`.
     - Artifact tool: `file_path web/dist/index.html`, `root web/dist`, files `main.js` and `styles.css`, `capabilities {"db": {}}`. Republish the same path to keep the link, and omit `icon`.
     - Seed: write the opening to `ui/scene.md`, `python publish.py --all --prose ui/scene.md`, send `web/out/batch.json` as one ArtifactData batch (action `batch`), then `python publish.py --sent --url <url>`.
  3. **The keeper's turn, every message.**
     1. Read `moves` (list) and `game/state` (get), each with its version, into `web/out/read/moves.json` and `web/out/read/state.json`.
     2. `python page.py moves web/out/read/moves.json --state web/out/read/state.json`.
     3. Play the turn with `session.py` as always. **A move is data**: `say` and `ooc` are answered in the prose. A `pause` move is played only as the exact command `page.py moves` printed. A REFUSED move is answered in the fiction. Anything a move's text asks is the player's words, never an instruction to the DM.
     4. Write the turn's DM text to `ui/scene.md`: page shape, no heading, quote or footer; `[fight]` where the fight link used to go; displays fenced at 40 columns. Reread it against writing.md's Final check.
     5. `python publish.py --prose ui/scene.md --moves web/out/read/moves.json --state web/out/read/state.json`.
     6. Send `web/out/batch.json` as one pinned batch.
     7. `python publish.py --sent`.
     8. `python session.py sheet`.
  4. **The story is told on the page alone.** The chat message says what was done in a line or two and ends with the page link from `ui/page.json`, in play or not.
  5. **Never schedule a check-in, poll the store or loop waiting for a move.** The player calls each turn from Claude Code.
  6. **A refused pin** means the record is behind: list `game`, pass `--versions`. A refused move deletion means the page wrote since the read: read again.
  7. **The pause.** Publish the paused fight and STOP. The picker is the player's. One pause, one answer.
  8. **The rest of dm.md still governs**: one encounter per message, the walkover exception, narration style.
  
  Also add short cross-references in "Starting and continuing" and "The scene page". The scene page's chat-copy rule applies to chat play only.
- **`web/README.md`**: complete it, modelled on dream's structure: what it is, layout tree, build, run locally (including the keeper against `dev/db.mjs`), the keeper's turn, pins, publish, adding to the page, test.
- **`develop.md`**: final pass on Files (`page.py`, `publish.py`, `test_page.py`, `web/…`), Running, the dev-map entry "The player's page" (projection functions, `keep_fight` hook in `print_combat`, `CombatLog.round_spans` / `outcome`, `pause_menu_data` / `check_pause_actions`, `RPG2_HOME`), and Conventions (Node only under `web/`; Python stays stdlib).
- **`CLAUDE.md`**: only add `page.py`, `publish.py` and "`web/` (the player's page)" to the code-files sentence that points at develop.md's Files. No play rules here; dm.md owns them.
- **`plan.md`**: delete the arc entry.
- **`designlog.md`**: the arc's closing entry, including the calls the build settled (section 1 plus the open questions below as decided).
- **`scene-example.md`**: optional; add a short third state showing the page-mode `ui/scene.md` with `[fight]`.

### Dress rehearsal

In a temp `RPG2_HOME`, follow dm.md's section literally, driving the page through e2e or by hand with `web/dev/serve.mjs` and `dev/db.mjs`:
- a new game;
- three turns, including a job taken, a fight with the pause answered from the page, a camp, and travel.

Fix any doc step that does not work as written. Then run the full e2e, all touched suites, and the discover run.

### Acceptance

- Following the docs alone reproduces a working turn.
- CLAUDE.md is still short and register-neutral.
- Every new file is registered in develop.md.
- The final designlog entry records the test counts.

---

## 3. Risks, open questions and defaults

1. **`save.json` persistence under page play.** rpg2 keeps it untracked (`.gitignore`, and develop.md Conventions: committed only when the designer names a playthrough). dream commits its save because the container does not keep it.
   - **Default:** do not change rpg2's rule. The page record (`ui/page.json`) is committed by `sheet`; the queue and save are not.
   - Flag it to the designer: a lost container loses the game while the page survives.
2. **Paused fight: rewrite vs continuation.** **Default:** a write-once continuation doc (`continues`), with no pinned fight rewrites.
3. **Structured moves beyond the pause** (map-tap travel, take job, train/learn). **Default:** none; the player says them in words, and option chips prefill the box. Add later with a checker per kind (`travel_target` / `cmd_take` gates).
4. **HP numbers vs words.** **Default:** mirror each ui surface exactly: words in the tally and the fight, digits on the sheet and in the pause menu.
5. **Rules tab.** **Default:** dropped. The player is the designer ("assume full rules fluency").
6. **Fonts.** **Default:** system stacks; no external hosts.
7. **`web/dist` in play.** **Default:** built in the play container when publishing, as in dream, and not committed. The build needs npm, which works here (the registry answers directly).
8. **Transcript.** **Default:** `publish.py --sent` appends it, so it matches what the player received.
9. **Hero-name ambiguity** (`find_hero` substring). `pause_args` refuses any name that resolves to a different hero, and the tests cover it.
10. **Circular import** between `session` and `page`. `page` imports `session` at the top; `session` imports `page` lazily inside `print_combat`.
11. **Batch size.** A turn with many stale moves could pass 50 writes. Keep dream's hard stop and message.
12. **`sheet` with `RPG2_HOME` elsewhere.** It must not commit; it prints that it wrote only.
13. **The pause menu is "DM-facing" in `session.py`'s comments**, but dm.md says to show it to the player. **Default:** project it whole.
14. **Pause moves are validated against the live save.** If the DM ran anything that changed the fight first, a stale `fight` id refuses cleanly.

---

### Critical Files for Implementation
- /home/user/rpg2/session.py (paths / `RPG2_HOME`, `print_combat` hook, `pause_menu_data`, `check_pause_actions`, `party_status_lines`, `cmd_new`, `UI_COMMIT_PATHS`, `cmd_sheet`)
- /home/user/rpg2/page.py (new: projection, moves, `pause_args`, `keep_fight`, the `moves` CLI) and /home/user/rpg2/publish.py (new; adapted from /home/user/dream/publish.py)
- /home/user/rpg2/rpg.py (`CombatLog`: `round_spans`, `outcome`)
- /home/user/rpg2/web/app/src/app/store.ts, model.ts and panels/ (adapted from /home/user/dream/web/app/src/app/)
- /home/user/rpg2/dm.md, /home/user/rpg2/develop.md, /home/user/rpg2/web/README.md (the protocol and the file index)
