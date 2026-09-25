# The player's page

rpg2's own claude.ai Artifact page for the player: the story, the party, the
map, the fights and the one mid-fight decision, read from a shared document
store and answered through it. It is a port of dream's `web/` page and its
keeper's-turn protocol (THE PLAYER'S PAGE ARC, 2026-09-25: designlog
2026-09-25 through (E); `page-plan.md` is the arc's historical note).
**dm.md's "Page play" is how the DM runs a game on it** -- a new game on
the page, the keeper's turn, the pause; this file is the manual behind
it. Section 1 is the Python half, which works from the terminal; section
2 is the page itself (`web/app/`, its tabs, the pause picker, the build,
publishing, the local table, the e2e).

## 1. The Python half

The store is readable by anyone who can open the page, so the DM's secrets
never go there: `page.py` is the only road from the save to the store, and
`publish.py` the only writer. The page writes `moves/` and nothing else.

```
page.py        the projection (player_view, chronicle_entry), the moves
               (clean_move, pause_args, move_words, read_moves), the fight
               queue (keep_fight, queued_fights, fight_doc) and the keeper's
               check: python page.py moves MOVES.json [--state STATE.json]
publish.py     the keeper's publish: the save projected, web/out/batch.json
               written; --sent once the batch has landed
ui/page.json   the page's record: {"url", "versions": {"game/state": 3, ...}}
               (committed by sheet)
ui/queue/      qNNN.json, the fights kept since the last publish
               (gitignored; new empties it)
web/out/       what publish.py wrote: game/, chronicle/, fights/, batch.json,
               pending/ (this publish) and last/ (the last one sent)
               (gitignored)
```

Everything lives under `RPG2_HOME` (the repo by default): the save, `ui/`,
and `web/out/`. A game played elsewhere (the tests, the e2e, a rehearsal)
sets `RPG2_HOME` to a directory and keeps all of it there.

### The documents

`game/state`, `game/party`, `game/map`, `game/quests`, `game/record` (the
singletons, written by `publish.py` only, pinned); `chronicle/tNNNN` (one DM
turn, written once); `fights/fNNNN` (one fight, or the second half of a
paused one, written once); `moves/mNNNN` (one player move, written by the
page, deleted by the keeper). Every document carries `v: 1`, keys are
camelCase, and none passes 256 KiB. Wherever a ui page exists, the
document's `text` is that page line for line (`session._wrap_block` of
the same function), and the structured fields are cut from the same
calls (`page.py`'s builders name them).

- **`game/state`**: `status` (`awaiting_player`, `dm_thinking`, `ended`
  -- forced to `ended` when `over` is set), `lastSeq` (the highest move
  answered), `day`, `where` (the breadcrumb), `coord` (`R09C10`), `land`,
  `latest` (the newest chronicle id), `lastFight`, `checkIn` (default
  "when you call from Claude Code"), `over` (`null`, `wiped`,
  `pc_dead`), `pause` and `levelUp`.
  - `pause` is `null` or the pause menu as data: `fight` (the published
    id of the fight that paused; `null` while that fight waits
    unpublished), `round`, `kind` (`normal` or `fate`), `trips`,
    `facing` (`name`, `hp`, `maxHp`), `party` (per hero: `hpState`, HP /
    STA / Power, `penalties`, `conditions`, `wounds`, `healing` and
    `stamina` potions), `options`
    (each `choice`, `label`, `cost`; `drink` / `heal` / `berserk` /
    `warbreath` / `vanish` carry `heroes`, the names that pass resume's
    checker now; `blink` / `smoke` carry the one `hero`), and `text`
    (`print_pause_menu` exactly). A Fate pause offers no action.
  - `levelUp` is `null` or `{hero, points, text}` (the PC's
    `print_levelup_menu`) while the PC has points banked.
- **`game/party`**: `day`, `purse`, `slots`, `members` (per hero the
  sheet's numbers, kit, spells, abilities, moves, conditions, wounds,
  flags, and `text` = `hero_block_lines`), `status` (the sheet's tail),
  `text` (`ui/party.txt`).
- **`game/map`**: `rows` (the 18 bare rows of 30 glyphs, no marks),
  `coord`, `objectives` (the jobs' squares), `legend` (`[glyph, word]`),
  `places` (the four gates, then the KNOWN settlements only: `coord`,
  `name`, `kind`, `land`, `capital`), `here`, `land` (`name`, `lines`),
  `known`, `holdings`, `text` (`ui/map.txt`).
- **`game/quests`**: `active`, `quests` (the jobs in hand only: `id`,
  `name`, `level`, `kind`, `origin`, `status`, `sites` with their
  `mark`, `road`, `due`, `note`, `cargo`, `dest`, `lines`).
- **`game/record`**: `quests`, `remarkable` (oldest first), `tally`,
  `suggestions`, `text` (`ui/history.txt`).
- **`chronicle/tNNNN`**: `id`, `turn`, `day`, `where`, `coord`, `prose`
  (`ui/scene.md` as published), `answered` (the moves it answers,
  cleaned, in seq order), `fights` (their ids), `levels` (each hero's
  level), `over`.
- **`fights/fNNNN`**: `id`, `day`, `where`, `coord`, `title` (the
  `===` banner, or the roster's first line), `outcome` (`won`, `lost`,
  `unresolved`, `retreated`, `paused`), `continues` (the paused fight a
  second half finishes, else `null`), `rounds`, `blocks` (`opening`,
  `rounds`, `between`, `closing`; a second half has no opening). Its
  lines joined are exactly what the process appended to
  `ui/fight-short.txt`.
- **`moves/mNNNN`** (the page's): `{seq, at, kind: "say" | "ooc", text}`
  or `{seq, at, kind: "pause", fight, choice: "fight_on", actions:
  [{hero, action}]}` / `{..., choice: "retreat", escape?, hero?}`.
  `page.clean_move` reads it whole or not at all.

### Fights are kept on their own

`session.print_combat` calls `page.keep_fight` for every session fight, so
there is nothing for the DM to remember. The queue entry is the process's
player log exactly (what it appended to `ui/fight-short.txt`), cut into
blocks -- `opening`, `rounds`, `between`, `closing` -- at the log's own
round spans (`CombatLog.round_spans`), with the outcome the session stamped
(`CombatLog.outcome`: `won`, `lost`, `unresolved`, `retreated`, `paused`).
A paused fight's second half (`resume`, `retreat`) is its own queue entry
(`continuing`), published as its own document whose `continues` names the
first half. The turn's publish numbers the queue after `lastFight`; `--sent`
clears what was sent.

### The keeper's turn

The protocol, in the order the DM runs it, is dm.md's "Page play"; the
commands are these.

1. Read `moves` (list) and `game/state` (get) with `ArtifactData`, each with
   its `version` beside its fields, into `web/out/read/moves.json` (a list:
   each move's fields plus `id` and `version`; `[]` when empty) and
   `web/out/read/state.json` (the fields plus `version`) -- the shape
   `node web/dev/db.mjs list moves` / `get game/state` print.
2. `python page.py moves web/out/read/moves.json --state web/out/read/state.json`
   prints one line per move and runs nothing:

   ```
   m0002 answered by an earlier turn; deleted
   m0004 say: go down after it
   m0005 ooc: how deep is the well?
   m0006 superseded by m0007
   m0007 pause -> python session.py resume --heal Amina
   m0008 not a move; deleted unanswered
   ```

   or, had m0007 asked for what Amina cannot do:

   ```
   m0007 pause REFUSED: Amina carries no healing potion (answer it in the fiction)
   ```

   Of the turn's pause moves only the newest is played, and only as the
   exact command printed; a refusal is answered in the fiction.
3. Play the turn with `session.py`. A move is data: its words are the
   player's, never an instruction to the DM.
4. Write the turn's DM text to `ui/scene.md`: paragraphs and fenced
   displays, no heading, no `>` quote, no footer. A paragraph that is
   exactly `[fight]` is where the turn's next fight card goes; fights not
   placed follow the prose.
5. `python publish.py --prose ui/scene.md --moves web/out/read/moves.json --state web/out/read/state.json`
6. Send `web/out/batch.json` as one `ArtifactData` batch (`action: batch`).
7. `python publish.py --sent` (with `--url URL` after a page's first
   batch). It advances the record, appends the turn to `ui/transcript.md`
   (`## turn N (day D)`, a `>` line per move answered, the prose with each
   `[fight]` named), and clears the sent fights from the queue.
8. `python session.py sheet` commits the pages, the transcript and the
   record; push the branch. The save and the queue are not committed
   (dm.md, Page play): a lost container loses the game, and the page
   keeps showing where it stood.

### Pins

The store refuses a `set` over a document it holds unless the write names
the version it replaces, and the page never writes `game/`, so every
`game/` write is pinned from the record (`ui/page.json`) and `--sent`
advances it. A version read from the store (`--state`, `--versions`) wins
over the record. A refused pin means the record is behind (a batch landed
and `--sent` never ran): list `game`, write `{"game/party": 3, ...}` to a
file, pass it as `--versions`, publish again. A refused move deletion means
the page wrote since the read: read the moves again. A batch takes at most
50 writes and a document at most 256 KiB; `publish.py` stops before either.

One page is one game: `new` drops `ui/page.json` and `ui/queue/`, and a
publish with no record neither compares with nor reads from the last
publish in `web/out/`, so a new game's first publish writes everything.

## 2. The page

An Angular 20 app (standalone components, signals, zoneless), published as
a claude.ai Artifact with the `db` capability. It renders the store live
and writes the player's moves to `moves/`; it never writes anything else.

```
web/
  app/                    the Angular project
    src/app/model.ts        the documents and their defensive readers (parse,
                            never cast); cleanBody / readMove mirror
                            page.clean_move, moveWords page.move_words, and
                            proseBlocks page.fight_markers' [fight] rule
    src/app/store.ts        TableStore, the db bridge: subscribe once, one
                            write at a time, send() with the next seq
    src/app/app.ts          the shell: header, three zones (>= 1241px), two
                            (<= 1240px), one and a bottom bar (<= 900px);
                            data-paused / data-over on :root
    src/app/ui.ts           page-local state: the tab, the phone's view, the
                            fight on show, words for the answer box (prefill)
    src/app/unread.ts       the unread marks, per viewer in localStorage
    src/app/panels/         story, prose (the turn's blocks: paragraphs,
                            displays, option chips, fight cards in place),
                            pause (the picker), answer, chronicle, party,
                            map, fight, fights, fight-chip, quests, record
    src/app/drawer/         the drawer; tabs.ts lists its tabs
    src/styles.css          the tokens (one palette, light and dark), the
                            layout, the .display class (40 columns, mono)
  page.html               the published page: content only, no doctype,
                          <html>, <head> or <body>
  build-artifact.mjs      page.html + the bundles -> web/dist/
  dev/                    the local page: serve.mjs (a fake store over
                          server-sent events), fake-db.js (the
                          window.claude.use("db") shim), db.mjs (the
                          keeper's side); never published
  e2e.mjs                 the page played end to end against the fake store
```

The page shows what the ui pages show, never more: the DM's turn as
written (a fenced display in mono at its printed 40-column shape, a
paragraph that is exactly `[fight]` as the card of the turn's next fight,
the fights no marker placed after the prose); the party as cards with
each hero's block and the whole `ui/party.txt` as printed; each fight as
the player log exactly (`ui/fight-short.txt`), block by block, the rounds
folded with the newest open, lines coloured by what they say and never
reworded. A second half shows its paused first half above it, folded.

On a phone (the target: Android at about 412px, 360px the floor) the
bottom bar is Story, Party, Map, Fight and More, and More opens Fights,
Quests and Record with a row of chips. A tab's `bar` flag in
`src/app/drawer/tabs.ts` gives it a button of its own; five is the most
the bar holds. Chrome copy is ASCII, in writing.md's display register;
separators are drawn with CSS. Fonts are system stacks, with no external
host.

### The tabs

- **Story** (the page's middle zone): the DM's last turn, the player's
  words it answered, the pause picker while a fight stands paused, the
  answer box, the chronicle. An `options:` display (a fenced block whose
  first line starts `options:`; wrapped lines are joined and the rest
  split on ", ") carries a chip per option: a tap puts the words in the
  answer box and focuses it, and never sends. Chips show only on the
  latest turn and only while the player can answer.
- **Party**: a card per hero (the sheet's numbers drawn, the block as
  printed), the whole `ui/party.txt`; while the PC has points banked, the
  level-up menu as printed on top ("Say what to spend them on." -- the
  player says it in words, the DM plays `levelup` / `train` / `learn`).
- **Map**: the 30 x 18 grid drawn from `game/map.rows` (sea, land,
  mountains, river; the settlement letters), the party's `@` and the
  jobs' `!` laid over it, the axes every 5. A tap names the square in the
  legend's words and the known places ("R06C05 -- land. London (city,
  Phyrascia, capital)."); the arrow keys move the pick. Below it the HERE
  block, the land, the known places and the holdings as printed; "Text
  map" shows `ui/map.txt` exactly. Wide screens open the drawer on it.
- **Fight**: the fight as the player log, block by block, the rounds
  folded with the newest open; a line the engine printed past 40 columns
  wraps in place, hanging, and is never reworded. A new fight turns the
  tab to it. **Fights**: every fight, newest first.
- **Quests**: a card per job in hand (sites with how far the party got,
  the road, the due day and its note, a delivery's cargo and
  destination, the job as `ui/map.txt` prints it); "No job in hand."
- **Record**: QUESTS DONE and REMARKABLE (newest first), THE TALLY OF
  SIN and SUGGESTIONS as `ui/history.txt` has them, the whole page in a
  fold.

Each tab carries an unread mark when its document changed since this
viewer last had it in front of them (`unread.ts`, a signature per tab,
kept per viewer in localStorage; without storage the marks last for the
visit). `data-paused` on `:root` puts the accent on the Story while a
fight stands paused; `data-over` greys the page, and the answer box says
GAME OVER.

### The pause picker

`panels/pause.ts`, in the Story above the answer box while
`game/state.pause` is set and the game goes on (`id="pause"`; the Fight
tab's "To the pause" scrolls there). It is the pause menu as data: what
tripped it, who the party faces, each hero's HP / STA / Power,
penalties, conditions, wounds and potions. The player picks **Fight on**
or **Retreat**. Under Fight on, one action chip per hero at most, and only
the actions `pause.options` names that hero for (the heroes the session's
own checker passes); none at a Fate pause. Under Retreat, an optional
blink or smoke for the one hero the menu names. The summary line is the
move in the player's words (`moveWords`, as `page.move_words` says it),
and Send writes `moves/mNNNN` = `{kind: "pause", fight, choice, actions |
escape + hero}` with the paused fight's published id -- the store sends
none without one. Sent, it says "Sent. Waiting on the DM." with the
words; "Change it" sends a newer choice, which supersedes the first
(`page.py moves` plays only the newest). With `pause.fight` null (the
paused fight not published) Send stays off and the player says it in
words. The exact menu as printed sits in a fold. The keeper never obeys
the move: `page.py moves` prints the command (`python session.py resume
--heal Mansur`) or the refusal, and the DM runs only what it printed.

### Build

```sh
cd web/app && npm ci && npx ng build && node ../build-artifact.mjs
```

`web/dist/` then holds `index.html`, `main.js` and `styles.css`.
`outputHashing` is `none`, so the bundle names are stable, and `page.html`
has no `<head>` because the Artifact host supplies the skeleton. The build
is zoneless, so there is no `polyfills.js`; `build-artifact.mjs` fails if
any other bundle appears (a lazy chunk would be missing from the publish).
`node_modules/`, `dist/` and `.angular/` are not committed;
`package-lock.json` is.

### Publish

With the `Artifact` tool: `file_path` `web/dist/index.html`, `root`
`web/dist`, `files` `main.js` and `styles.css`, `capabilities` `{"db":
{}}`, and an `icon` on the first publish only. Republish the same path in
the same conversation, or pass the page's `url` (from `ui/page.json`)
from another, to keep the link; the store keeps the game across
republishes, so a republish is needed only when `web/` changed.

Then seed the store, once: write the opening to `ui/scene.md`, run
`python publish.py --all --prose ui/scene.md`, send `web/out/batch.json`
as one `ArtifactData` batch to the new `url`, and run `python publish.py
--sent --url <the url>`, which records it in `ui/page.json`. After that a
publish sends only what changed.

One page is one game: `new` drops `ui/page.json` and `ui/queue/`, so a
new game is published as a new page, seeded and recorded the same way,
and the old page stays as the last game left it. A game that began in
chat play has every fight since `new` in `ui/queue/`: empty it before the
first publish, or the backlog goes to the page with the first turn.

### Run it locally

```sh
export RPG2_HOME=/tmp/g && mkdir -p $RPG2_HOME
python session.py new --seed 5 --level 1
python publish.py --all --prose $RPG2_HOME/ui/scene.md   # a scene you wrote
node web/dev/serve.mjs --batch $RPG2_HOME/web/out/batch.json   # http://127.0.0.1:4321/
python publish.py --sent
```

`serve.mjs` serves `web/dist` in a host-like skeleton with `dev/fake-db.js`
loaded first: an in-memory store behind the same calls the page makes on
claude.ai, live over server-sent events, refusing an unpinned write over a
document it holds as ArtifactData does. Add `?readonly` to refuse writes
as for a view-only viewer, `?nodb` to see the page with no capability,
`?theme=dark` to stamp the viewer's theme. Then play the keeper against
it (`RPG2_TABLE` or `--url` picks another server):

```sh
mkdir -p $RPG2_HOME/web/out/read
node web/dev/db.mjs list moves > $RPG2_HOME/web/out/read/moves.json
node web/dev/db.mjs get game/state > $RPG2_HOME/web/out/read/state.json
python page.py moves $RPG2_HOME/web/out/read/moves.json --state $RPG2_HOME/web/out/read/state.json
python publish.py --prose $RPG2_HOME/ui/scene.md --moves $RPG2_HOME/web/out/read/moves.json --state $RPG2_HOME/web/out/read/state.json
node web/dev/db.mjs batch $RPG2_HOME/web/out/batch.json && python publish.py --sent
```

### Test

```sh
node web/e2e.mjs [--out DIR] [--headed]
```

It needs `web/dist` and a Chromium for `playwright-core`
(`PLAYWRIGHT_BROWSERS_PATH`, or `CHROMIUM=/path/to/chrome`; it falls back
to `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`). It rolls its own
game (`session.py new --seed 5 --level 1`) into `DIR/home` as
`RPG2_HOME`, never the repo's, and plays it with the real `session.py`,
`publish.py` and `page.py`: the opening with its displays, a move and a
question to the DM waiting in the chronicle, the keeper's turn (`page.py
moves`, a pinned batch, `--sent`, the same batch refused twice, the
transcript gaining the turn), a fight placed by `[fight]` between two
displays whose Fight tab is `ui/fight-short.txt` line for line, the party
cards and the whole sheet as `ui/party.txt`; the options chips filling the
box and sending nothing; a job taken (`take`): the Map's 540 squares, the
`@` on `game/state.coord`, a tap naming the square, the `!`, the text map
as `ui/map.txt`, no unknown settlement anywhere in the store, the Quests
card and the Record as `ui/history.txt`; a level crossed (`award`): the
level-up menu and "NAME reaches level N." in the chronicle; a real paused
fight (a foe the save's own dice pause against, found on copies of the
home): the Fight and More marks, cleared by looking and remembered over a
reload, the picker offering only what the menu does, a tampered pause
move REFUSED and answered in the fiction, the player's heal and fight on
printed by `page.py moves` as the resume command, played, and its second
half published with both halves equal to `ui/fight-short.txt`; no side
scroll and every display unclipped at 412 and 360 on every tab, the five
thumb-sized bar buttons, mid and wide widths, light and dark, the marks
with storage blocked, the read-only and no-db fallbacks; and game over
(`--status ended` over a dead PC): `data-over`, the box closed.
Screenshots go to `DIR/shots`.

### Adding to the page

- **A drawer tab**: one standalone component in `src/app/panels/`, reading
  `TableStore`, and its entry in `src/app/drawer/tabs.ts`; give it a
  signature in `unread.ts` for its mark. The phone's bar is five buttons at
  most, and it is full (Story, Party, Map, Fight, More): a new tab goes
  under More. Name the component class so it does not shadow a global
  (`MapTab`, `RecordTab`: `tabs.ts` uses `Record<...>`).
- **A document or collection**: a reader in `model.ts` (fall back, never
  cast), then one line in `store.ts`: `readonly x = this.doc('game/x',
  readX)`. It is subscribed once, at connect.
- **A move of a new kind** (the pause is the worked example): `MoveBody`,
  `cleanBody` and `moveWords` in `model.ts`; `MOVE_KINDS`, `clean_move`
  and `move_words` in `page.py`, whole or nothing alike; a checker like
  `pause_args` that goes through the session's own gate (as
  `check_pause_actions` / `check_escape` are `resume`'s and `retreat`'s)
  and raises `MoveRefused`; its line in `moves_report`; the data the page
  needs to build only valid moves, projected from the same gate (as
  `pause_menu_data`'s `heroes`); and a guard in `TableStore.send` if the
  move answers one standing thing. Test the page's move through the
  Python in the e2e, not only each side alone.
