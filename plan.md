# Roadmap

What is left to build, in order. This file is **planned features only**:
design principles (the design spine, the three currencies, tone, legibility)
live in `rules.md`; shared fiction/content style in `writing.md`; the play
protocol in `dm.md`; dev conventions and current balance numbers in
`develop.md`. Anything already implemented is documented in `rules.md` and the
code, not here — when a feature ships, delete it from this file rather than
marking it done.

---

## THE RETRO PIVOT (2026-07-21) — the direction the roadmap now serves

The 2026-07-21 design session reframed the game again — this time the
presentation and the seat the AI sits in, not the content. The trigger:
strong dissatisfaction with the AI-DM's narration and table manner,
even as the dark quests were judged an improvement over the vanilla
ones. The paradigm so far — a ttrpg with an AI DM — is dropped as the
goal.

**The vision:** a mechanics-centered game in the mold of a **retro
text adventure**. The mechanics are not tactical combat but MACRO
decisions and a SIMULATED WORLD the player watches play out. The LLM's
advantage is reframed: not that it narrates, but that it is a **coding
agent running the game** — the central game function need not exist,
only subsystems; the AI calls them, generates content where needed,
and keeps the whole coherent and open. (This inverts half of
2026-07-19's "the superpower is free narration" diagnosis — designlog
records the reversal.)

Concretely:

- **Style (SHIPPED 2026-07-21):** minimalist retro text adventure —
  present tense, second person, terse, deadpan; not wry Pratchett, not
  generic-fantasy purple prose. Expanded into the shared `writing.md`
  fiction/content guide on 2026-07-22; dm.md applies it at the table.
- **Displays over prose:** a greater role for script-generated logs
  and menus, optimized so the chat can usually display them directly
  (roadmap item 1 below).
- **Dark quests stay the most important pre-authored content** — but
  their wording gets a simple-and-straightforward rewrite (item 2).
- **The villain/karma layer is DEMOTED to one layer among several** we
  may return to — no longer the direction the roadmap serves. Nemesis
  persistence / rival posses: bumped way back (they serve narrative
  strength, not mechanical strength, and narrative is not the focus
  now).

### The retro roadmap (build order)

1. **The log/menu rework.** Script output becomes the primary thing
   the player reads; the chat should usually display it directly. The
   40-column wrap stands. Success test: a typical DM message is mostly
   script output plus a few terse retro-register lines.
   - **The combat log part SHIPPED 2026-07-21** (rules.md "Reading the
     combat log" is the doc of record): ONE displayed log — col-1
     lines pre-fitted to 40 via `fit_lines`, damage as `deals N dmg` +
     tier punctuation, attacker-HP tags when hurt, no penalty numbers
     in fight lines (they moved to the pause menu + tally), quiet
     rounds collapsed, movement lines only in ranged fights, named
     moves/abilities name-only, Power printed only on casts, roster
     stat blocks as the enemy introduction, the dying counterattack
     resolving immediately (bench-checked within noise, benchlog).
     The detailed log stopped printing. Since 2026-07-26 combat writes
     committed last-fight snapshots in `ui/fight-short.txt` (the complete
     displayed log and DM fallback) and `ui/fight-detailed.txt`
     (post-mortems); new encounters replace them and paused fights append
     through resume/retreat. Encounter banners, the
     pause menu, and the award/XP/autospend lines were refit in the
     same pass; dm.md's protocol/narration sections updated.
   - **Still open from item 1:** a player STATUS DISPLAY log (a
     fitted, pasteable `status` in the same register — today's
     `status`/`board`/`map` print DM-shaped, wrap-reliant output);
     the levelup menu refit WITH ability descriptions (it still
     prints the old wide two-column-ish lines that wrap raggedly at
     40); and a fitting pass over the remaining non-combat surfaces
     (rests, travel, recruit sheets) where lines still hang a word
     past the width. The `fit_lines` helper and the tally/pause
     penalty display are the pattern to reuse.
   - **Local map page:** add **`ui/minimap.txt`** beside the shipped
     `ui/map.txt`. `map.txt` is the macro Land/Area view; the minimap is the
     current Area/Site/Room branch, visible exits, and local quest markers.
     It should use the shipped `look`/breadcrumb data and join the same
     rewrite + `sheet` commit lifecycle. This is UI only; the persistent
     Land -> Area -> Site -> Room foundation shipped 2026-07-22.
   - **Parked from the log session (designer skepticism recorded):
     E1/P1 shorthand** for enemy/party names in fight lines — saves
     width on long names but reads cryptic; try only if long-name
     fights prove noisy in play.
2. **The quest wording rework.** The dark templates' words themselves
   (titles, descs, giver lines, epilogues in `karma.py`) rewritten
   simple and straightforward, using `writing.md` — the current
   Pratchett-wry phrasing goes; the comedy that survives is situational
   and deadpan. The good-side templates in `quests.py` get the same
   pass afterward where the clash is felt. *(2026-08-04: for karma.py
   this is absorbed by THE DARK REWORK above — the occult ten get their
   pass in its Session A, the crime scene copy in Session B; what
   remains of this item is the quests.py good-template half.)*
3. **Play the dark path in the new register** (absorbs villain roadmap
   item 1): the probe now tests the retro style AND the dark content at
   once — the first ten messages, the first three levels.
4. **The macro-game design session.** The genuinely new build: define
   what the macro decisions ARE and what the simulated world runs.
   Seeds already on the books: off-screen event simulation (parked),
   standing dark enterprises, conquest ticking / domain play. Schedule
   as its own session; nothing is committed yet beyond the direction.

---

## THE DARK REWORK (2026-08-04) — next up: assignments from Hell, crime as actions

The 2026-08-04 design session (designlog has the reasoning trail). This
section is the complete implementation spec: a fresh session should be
able to build any slice from it without the conversation that produced
it. Three sessions, in order — each leaves the game playable.

**The resort.** The 24 dark templates conflate two different things, and
they get sorted apart:

- **Assignments from Hell** — the OCCULT work (hellgate, desecration,
  blood sacrifice): few, level-pinned, longer-deadlined quests on the
  war-wave model (`story.WAVE_LEVELS` is the proven shape). The pact's
  spine.
- **Crime** — everything else: no longer quests at all, but free ACTIONS
  against a leveled world, resolved by a parametrized pipeline the DM can
  adjust, gamified by a tally/history page instead of a board. The
  questgiver frame GOES: the PC does the thing because they want to and
  keeps whatever material gain directly follows. The shadow board
  (`board --dark`) dies with it.

**Rename:** bad karma → **SIN** (current sin / lifetime sin / penance),
including the save keys. **develop.md's "No backwards compatibility"
rule (2026-08-04) governs this whole rework**: rename keys freely, and
delete old-save assertions and lazy-upgrade branches wherever a touched
file carries them. No shims.

### Settled decisions (2026-08-04 — reopen only with the designer)

1. **Assignments pin at odd PC levels** — `TASK_PIN_LEVELS = (1, 3, 5,
   7, 9, 11, 13, 15, 17, 19)`, ten per career ("more frequent" was the
   designer's call over a sparser 1/3/5/8/13/18). The interval clock
   (`TASK_INTERVAL_DAYS`) dies.
2. **The occult templates form a ten-card DECK**, shuffled once per save;
   each pin deals the next card. Order is RANDOM by directive — variety
   over curriculum sense, because only the low levels ever get played
   (the hellgate may well come at level 3; that is accepted).
3. **The retribution chain is FINITE**: one warning, then three
   collection fights (party +0, +1, +2 — only the third relentless), then
   hell WRITES THE JOB OFF and waits for the next pin. A good-alignment
   refuser is priced, not permanently besieged (the old ladder repeated
   the capped rung forever — see "The refuser's arc" below).
4. **Crime difficulty comes from the MARK's level** — the conquest
   doctrine (geography, not gates) applied to people: a mark's level
   fixes both wealth and protection, availability is gated by settlement
   kind, casing is free, and nothing auto-levels to the party. Farming
   down is self-defeating because rewards scale off the mark.
5. **Petty crime pays XP** (small, and all of it sin) — designer call.
6. **The news cycle**: any single sin gain ≥ the heat step floors heat
   at 1 for `NEWS_DAYS` regardless of penance. Anti-laundering for big
   scores; petty sin stays dodgeable on purpose (the tithing
   puppy-kicker is a comedy the game wants).
7. **Monotony is per-category and TEMPORARY** (a day-stamp window), with
   a first-time creativity bonus; gold never depreciates — the loot is
   the loot, it is hell that gets bored.
8. **Unlocks gate SUGGESTIONS, never permission** — crime is free; a
   "locked" category committed anyway unlocks itself by deed. The
   suggestion feed is advertising.

### The template sort

**Occult ten** (assignments — stay quests): Blood on the Altar,
Sacrifice the Puppy, Steal the Temple Relic, Kill the Priest, Corrupt
the Holy Sword, Find the Evil Sword, Guard the Cultists, Open the
Hellgate, Capture the Beast (hell is the customer — occult by giver),
plus ONE NEW template to author: **Desecrate the Shrine** (writing.md
register; the desecration slot the list lacks).

**Crime fifteen** (retire from the quest system; their skins, rosters
and situations become Session B's scene fodder): Kick the Puppy, Collect
Protection Money, Burn the Granary, Steal the Jewel, Collect the Debt,
Rob the Tomb, Take Over the Road, Dine and Dash, Loot the Village, Rob
the Vault, Poison the Feast, Take the Mansion, Betray an Old Friend,
Sell the Powder, Take the Neighbor's Land.

### The refuser's arc (why decision 3 — the analysis, kept)

Under the old shape, a player who ignores an assignment reaches the
capped relentless rung and is then harassed forever (cooldown 4, chance
0.6) until they do the job, bribe, or lose. Under pins that is worse:
the serial rule would block every later pin behind the refused job, so a
good-alignment campaign would spend its whole life fighting hell's
capped posse. The finite chain fixes it: per refused assignment the
price is one warning scene plus at most three hell fights (party +0,
+1, +2 relentless; neutral XP — no absolution farming), spread over
~8–16 days, then the write-off and quiet until the next odd level.
Chains never stack and never reset mid-account: pins crossed while an
account is open are noted, and ONE fresh assignment lands at the first
settlement stop after the account closes (see `last_pin_served` below).
Losing any visit keeps the shipped mercy: purse as the fine, job
withdrawn, account closed.

### Session A — the assignment ladder (karma.py, session.py + docs)

- **Sort the templates.** `DARK_TEMPLATES` splits: `OCCULT_TEMPLATES`
  (the ten above, incl. the new Desecrate the Shrine) is what
  `roll_dark_quest` draws from; the crime fifteen move to a clearly
  marked fodder block (unused by any roll — Session B consumes them).
- **The deck.** `new_pact()` gains `deck` (a seeded shuffle of the ten
  template indexes), `last_pin_served: 0`, `defied: 0`; drop `task`
  bookkeeping that dies with the interval clock (`last_task_day`).
  Dealing: take the next card in the deck whose `template_band` admits
  the assignment level; if none fits, the nearest-band card. Skipped
  cards stay in the deck. (Random order is wanted; a mechanically
  unbuildable roster is not.)
- **`maybe_assign_task`** (session.py): fires at settlement stops when
  no task is open, no bribe holds, and some pin ≤ PC level is
  > `last_pin_served`. Serves ONE assignment (never stacks skipped
  pins), stamps `last_pin_served` to the highest crossed pin, levels the
  quest at party level + `TASK_SPREAD` (0..+1, unchanged). `HELL_MAIL`
  delivery flavor unchanged. `FIRST_TASK_LEVEL` dies — pin 1 fires at
  level 1, which IS the tutorial job.
- **Deadlines**: `TASK_GRACE_DAYS` 4 → **10** (a pin can be crossed
  mid-wilds; a milestone quest must not be missable to a road delay);
  `TASK_WINDOW_DAYS` (4, 6) → **(6, 8)** + road days, mechanism
  unchanged (the honest deadline machinery; hell work never lapses off
  the clock).
- **`maybe_enforce`** (session.py): warning rung unchanged. Fights at
  party +0/+1/+2 as shipped (`ENFORCE_CAP_OVER` 2, third fight
  relentless). NEW: when the party survives the third fight (it
  resolved without `apply_mercy`), hell WRITES OFF the job — quest
  withdrawn (release its places), `pact["task"] = None`,
  `defied += 1`, a short authored scene ("the account is written off;
  hell's ledger remembers"). `defied` is a ledger for later content
  (hell's patience / pact termination — parked, not built).
- **Kill the shadow board**: `roll_dark_board`, the `dark_board` save
  key, `board --dark`, `DARK_JOBS_PER_DAY`. `roll_dark_quest` survives
  (assignments + the `test_places` routing test). `forge --dark` stays
  as the DM's freeform dark-quest tool; `DARK_GOLD_MULT` stays for
  quests that remain dark (assignments, forges, conquest jobs).
- **Conquest doctrine touch-up**: a held settlement's board line
  ("`board --dark` serves") becomes "posts no honest work; crime and
  the pact serve" — session.py's occupied-board text + rules.md's
  Conquest add-on.
- **Docs**: rules.md Karma & Heat add-on (Assignments / Past Due /
  shadow-board bullets rewritten), dm.md quick reference, develop.md's
  karma.py file entry. New template wording per writing.md.
- **Tests**: update the `test_places` dark-quest routing test; delete
  old-save compat assertions in any touched suite (the no-compat rule).

### Session B — crime actions (new `crime.py`, session.py + docs)

- **New module `crime.py`** (register in develop.md's Files): the mark
  bands, the crime catalog, and the resolution helpers. session.py owns
  the commands. No sim or bench imports it (the karma doctrine).
- **Mark bands** (level fixes wealth AND protection; availability by
  settlement kind, the garrison-band logic — village caps ~7, town ~12,
  capital 20):

  | mark | level | where |
  |---|---|---|
  | commoner / stray / unpaid lunch | 1–2 | anywhere |
  | tradesman, innkeeper | 2–4 | anywhere |
  | merchant, priest | 4–7 | town+ |
  | guild master, noble | 8–12 | town / capital |
  | magnate, high temple | 12–16 | capital |
  | the royal vault | 16–20 | capital |

- **Casing is free** (the OSR straight-board stance): `case CATEGORY`
  rolls the local mark (seeded per settlement/day/category) and prints
  level, expected take, the check, and a protection hint. `crime
  CATEGORY` commits against the cased mark (rolls fresh if uncased).
  `--npc NAME --level N` targets a named victim (giver, notable) — the
  DM assigns the band; NPCs are freely attackable/robbable through this.
- **Three shapes**, per category:
  1. **petty** — trivial or no check, no roster (or a token one), flat
     `PETTY_SIN` (10–15) quoted as XP (all sin), coin in pennies.
  2. **deed** — 2d6 + stat vs DC (the caper machinery generalized).
     Make: clean take, sin, no fight. Miss: the mark's protection
     fights (a `build_room` budget at mark level wearing the recycled
     skins) + `WITNESS_SIN` (reuse `DEED_FAIL_KARMA` 15).
  3. **force** — no check; straight to the protection roster, then the
     take. Fight XP is dark as usual, plus the crime lump.
- **Formulas** (initial knobs, hand-set per the standing balance
  directive): crime lump ≈ `CRIME_XP_PER_LEVEL` (50) × mark level ×
  category mult (half an at-level quest — a crime is one scene); coin
  crimes pay ≈ `CRIME_GOLD_PER_LEVEL` (20) × mark level; goods crimes
  (jewels, relics, cattle) pay in goods fenced at `FENCE_RATE` (0.5).
- **Monotony**: per category, day stamps within `MONOTONY_WINDOW` (10);
  the sin/XP mult by count already in the window is `(1.0, 1.0, 0.5,
  0.25)`, floor 0.25 — temporary by construction, stamps age out. Gold
  never depreciates. Alternating two categories does NOT reset either —
  each has its own window; that is intended (a two-crime loop should
  stale; a portfolio, or honest days between sprees, stays fresh).
- **First-time bonus**: a category's first-ever commission pays
  `FIRST_TIME_MULT` (1.5) on sin/XP — the creativity carrot, pointing
  at the suggestion feed.
- **The news cycle** (karma.py): a single sin gain ≥ the heat step
  (100 × level) stamps `hot_until = day + NEWS_DAYS` (6); `heat()`
  floors at 1 until then, penance or no. Applies to quest turn-ins too
  — occult assignments are exactly the big scores it exists for.
- **Unlocks**: the `crimes` save ledger (per category: count, day
  stamps, unlocked flag). The first COMPLETED hell assignment unlocks
  one random suggestion; thereafter one per `CRIME_UNLOCK_STEP` (200)
  lifetime sin, random order. Full list lands around 4,750 lifetime sin
  — the derivation: the XP budget to L20 is 19,000 quoted; keeping heat
  down means at most half can be sin (each point needs a penance
  point), so 9,500; half of that again = the designer's target.
- **The catalogue** (~24 categories; shape and check noted — DCs sit
  10–11 against stats 3–5, the caper doctrine):
  - *petty*: kick the puppy; dine and dash; cheat at dice (CHA);
    petty vandalism; pickpocket a commoner (DEX, tiny take).
  - *deed*: burglary (DEX); the vault heist (MIND); the con / false
    relics (CHA); counterfeiting (MIND); blackmail (CHA); impersonate
    an official (CHA); poison the feast (MIND); grave-robbing (DEX);
    smuggling / the powder trade (MIND); cattle rustling (DEX).
  - *force*: mugging; extortion / protection racket; strong-arm debt
    collection; highway robbery; rob the tax collector (the crown's
    own coin — posse magnet); arson; kidnapping for ransom; jailbreak
    (frees a future recruit — hook); caravan robbery; the village
    raid; the land grab (conquest-adjacent); betrayal (sell out an
    ally's crew).
  - Nothing grim (writing.md's cartoon register gates the list).
- **Heat-pump note to watch at the table**: crime lumps are smaller
  than quest lumps, so running hot now takes big marks or volume —
  coherent (petty crime should not summon the crown's huntsmen), but
  `CRIME_XP_PER_LEVEL` is the lever if heat gets too hard to reach.
- **Docs**: rules.md gets a Crime section (in or beside Karma & Heat);
  dm.md (crime at the table: the wickedness stays narration, the
  engine only ever fights the protection); develop.md Files + dev map.

### Session C — the surface: history page, tally, the sin rename

- **`ui/history.txt`** — the fourth committed UI page (cashes the
  parked "quest history readout"), rewritten on every save, committed
  by `sheet` like party/map/fight. Sections: QUESTS DONE (day-stamped
  one-liners with the epilogue), REMARKABLE (waves, conquests, mercies,
  maimings, write-offs, named kills), THE TALLY OF SIN (category:
  count, last day), SUGGESTIONS (2–3 unlocked-but-uncommitted
  categories, seeded random order). Save keys: `history` (list of
  day-stamped lines), plus Session B's `crimes` ledger. 40-column wrap.
- **The rename**: karma save keys `bad` → `sin`, `bad_total` →
  `sin_total`, `good_total` → `penance_total`; every display string
  ("dark work: +N sin", "sin N; HEAT h", "lifetime sin"); the `karma`
  command becomes `sin` (no alias — no compat); rules.md / dm.md sweep.
  Heat stays heat (it is the law's meter, not hell's).
- **`crimes` command** — the `prices` pattern: the catalog with
  expected take / check / protection for the LOCAL marks, the tally,
  and the suggestions. This is the player's crime surface; the DM's
  numbers all live in `crime.py`'s knobs.
- **Tests**: contracts for the history page (sections present, 40-col
  fit), the unlock ledger, and the monotony math; finish deleting
  old-save assertions in every suite this rework touched.

### What dies (the full list)

`TASK_INTERVAL_DAYS`, `FIRST_TASK_LEVEL`, `last_task_day`,
`DARK_JOBS_PER_DAY`, `roll_dark_board` / the `dark_board` save key /
`board --dark`, the fifteen crime templates as QUESTS (content
recycled), the endless top-rung enforcement (replaced by the write-off),
the `karma` command name, the old karma save keys.

### Explicitly not in this rework (still parked / open)

Hell ranks and karma-gated powers (lifetime sin now has its first job —
the unlock feed — but buys no powers yet); the geographic wanted level;
standing dark enterprises (the powder network earns as a crime category,
not as a holding); nemesis persistence; race-flavored occult tables; a
crime/karma career sim (the balance stance stays variety-first,
table-tuned); parley with the law's posses.

---

## The villain layer (the 2026-07-19 pivot — DEMOTED 2026-07-21)

*(2026-07-21: the retro pivot above supersedes this section's FRAMING.
The karma/heat/pact mechanics and the dark content stay shipped and
stay important; what is demoted is the villain ARC as the roadmap's
direction. The build order below is kept as the layer's internal order
for when/if it returns; item 1 moved into the retro roadmap; item 2 —
the nemesis — is bumped way back, narrative-serving. Of the rest,
conquest ticking and the greed economy are the most retro-compatible
entries — macro decisions, world state — enter through them if the
layer returns. 2026-08-04: THE DARK REWORK above supersedes this
layer's dark-quest SHAPE — the shadow board and the crime templates go,
the occult assignments and free crime actions replace them; karma/heat/
pact/posses stay the shipped spine.)*

The 2026-07-19 design session reframed the game. The diagnosis: the game
had become a difficulty curve with a purse — real decisions, but all the
same decision (read the board, pick a level), and nothing the player does
changes what the world *is*. The project's actual superpower (the AI
freely narrating and animating people) had nothing to chew on.

**The vision:** the player becomes the *cause* of the world's state
instead of its janitor. The game facilitates and encourages a **cartoon-
villain campaign** — conquer, extort, steal, flaunt — while remaining
fully playable as the old Good game (dual by construction, never two
rulesets). Tone: Discworld/Conan, pratfall evil, never grimdark (`writing.md`
owns the register; dm.md applies it at the table). ~~The candidate frame for
the PC: an imp sent
topside with a quota~~ — **SETTLED later the same day (the dark-quests
session): the PC is a MORTAL of an ordinary race, a low-ranking
employee of Hell under a pact with an evil god.** Not an imp. The pact
rides every new save (`new --no-pact` opts out); rules.md's Karma &
Heat add-on, "The Hell Pact", has the shipped mechanics (assignments,
Past Due collections enforcement (reshaped 2026-08-03, was Chickening
Out), bribes, the caper structure, the left-for-dead mercy, seventeen
new dark templates).

**The load-bearing mechanism (SHIPPED as the first slice, 2026-07-19 —
rules.md's Karma & Heat add-on):** XP bucketed by the alignment of the
work that paid it; bad karma sets HEAT; heat sends escalating lawful
posses at party level + heat; honest work burns karma 1:1. Difficulty
selection by consequence — the throttle the player pumps — and the
ratchet (killing the law is itself a crime) is the villain campaign's
level curve. Karma rides *beside* levels for now: merging them fully
(karma AS the level track) stays an open question below.

**Decisions settled in the session** (recorded so they stay settled):

- **Karma merged into XP accounting** (bucketed awards) over a separate
  currency — a separate track would re-open "what does karma actually
  get you"; the bucket answer is free.
- **The map stays a LIST.** Conquest will be ownership tags on the
  existing Land/Area readout (`[YOURS]` beside `[UNDER THE
  YOKE]`), like the occupation layer already does. No hexes, no grid —
  everything prints at 40 columns.
- **No big-number rework.** The Diablo feel (whip of bad karma, the
  Midas sword) comes from named/masterwork instances with authored
  riders (the named-weapons item in "After that" below), never from
  renumbering the 2d6 engine the whole bench suite calibrates.
- **No food/hunger meter.** The job food was meant to do (a scaling
  gold sink with flavor) goes to the GREED ECONOMY instead (below):
  luxury display as a voluntary sink with consequences, monster-cooking
  as its flavor. A hunger meter is the upkeep bookkeeping the heroic
  tone bans.
- **Conquest is ticking a list, not a strategy layer.** The player's
  dials stay few and chat-legible: where to strike, how hot to run,
  what to flaunt. Anything that can't be decided in one chat line is
  over the line. (An army mechanic is parked as an open question, not
  promised.)

### The villain roadmap (build order — SHELVED 2026-07-21, see the note above)

1. **Play the dark path** (no code): run the first ten messages of a
   wicked campaign on the shipped slice — the tone probe. Does cartoon
   evil sing at the table? Does heat feel like a throttle? The first
   3 levels are the only part that ever gets tested; make them land.
2. **Nemesis persistence.** Posse leaders who survive (party fled, or
   the leader's row lived) RETURN: same face, +1 level, a grudge line.
   The save already keeps `last_leader`; grow it into a small nemesis
   record. This is the AI-DM superpower feature — recurring named
   enemies the DM can animate. (Absorbs the parked "rival" idea.)
   *Pulled ahead of conquest (2026-07-19, the ordering vibe check):
   it is the cheapest item on the board (a thin save record + one
   posse-spawn hook), it makes the just-shipped heat layer read as
   story instead of a random tax, and it is small enough to slot in
   mid-playtest the moment the first surviving leader is felt to be
   forgotten.*
3. ~~**Conquest ticking**~~ — **SHIPPED 2026-07-27** (rules.md's
   Conquest & Holdings add-on; designlog has the session): the `conquer`
   verb over fixed garrison levels (village 3-5 / town 6-10 / capital
   11-15), the owner tag, tribute, paid levy garrisons absorbing crown
   raids, the heat floor per holding, shadow-only boards in held
   settlements, and the yoke override. The 2026-07-19 open calls landed
   as guessed: bad karma prices the deed and holding land raises the
   heat floor. All knobs hand-set -- tune at the table.
4. **The good-karma mirror — the dual campaign.** *Half-shipped
   2026-07-19*: hell's disciplinary posses exist (Past Due collections
   — they punish DISOBEDIENCE, an ignored assignment), and the PC
   frame is
   settled (mortal pact-holder, default-on). What remains is the mirror
   proper: hell auditing a too-*virtuous* employee (good karma as the
   liability axis), so the hypocritical middle path (both meters hot)
   becomes the comedy jackpot. One mechanic, two skins.
5. **The greed economy.** Luxury items as gold sinks that generate bad
   karma and heat when FLAUNTED (envious hell officials, heroes coming
   for the holy golden elephant): each displayed trophy is a standing
   quest hook pointed at the party. Feasts (cook the monster) as the
   satisfaction/karma variant. This is also the L15+ "what is gold
   for" answer arriving early — coordinate with domain play.
6. **Dark content pass**: race-flavored dark templates (the generic
   seven ship in the slice), war-integration (side WITH the story
   layer's aggressor?), parley/bribery with posses. *(Karma-flavored
   weapons shipped 2026-07-28: the karma-on-kill quirk is a live
   generator roll — what remains here is authoring SPECIFIC villain
   pieces onto it.)*

---

## The levelling framework — COMPLETE (A/B/C shipped 2026-07-17)

Carry-forwards, parked (not scheduled):

- **Enemy-side moves** (giving the drilled soldiery two moves each) and the
  **second-wave moves** (guard-break, taunt, battle-cry) — a later content
  pass with its own bench round (from session B).
- **The day-stamp spoilage variant** — session C shipped the freshness
  STOCK CAP (rank + 2 brewed items) over per-potion spoil timestamps. If
  spoilage should ever be FELT, the cheap variant is one day-stamp per
  hero's brewed batch — noted, not built.
- **Alchemy conditions** (poisons, oils) — UNBLOCKED 2026-07-26: the
  conditions framework shipped (slice 3a), and alchemy is its first queued
  customer. A poison oil is now a recipe plus one `apply_condition` call.

Open to feel out in PLAY: points-per-level 3 vs 4 and training 2n
(re-open only if the mid-band feels grim); the **kit-shrink dial**
(`KIT_STAMINA` 1->2 or a higher `KIT_FORAGE_CHANCE` if play reads too
grim); the **DEX potion** (rank 4/+1 under the standing +DEX warning).

---

## CLOSED DESIGN — the attrition rework (2026-07-26)

All four slices from the 2026-07-26 quest-length design session have shipped.
The settled constraints remain here because they govern the parked follow-ons
below; live mechanics are in `rules.md`.

### Why: the problem and the spine

The generator centred quests on **3.74 encounters** — sites rolled 1/2/3 at
45/40/15, then rooms rolled 1/2/3 at 20/40/40 *per site*, so 47% of quests
were four fights or more and the tail reached nine. The target was **1
encounter by default, 2 for a middling job, 3 at most**, with sites used only
when the fiction genuinely moves to a different place, never as the
difficulty dial. *(Slice 1 shipped this: mean 1.66, hard max 3.)*

Cutting encounters exposes the real problem underneath. Attrition used to
live *inside* a quest — press on through four rooms or camp and lose the XP
streak. With one fight per quest there is nothing left to attrit: the party
wins, camps to full (`camp --heal` runs up to fourteen free nights, and
`dm.md` names "camp until whole" as the played default), and HP never
mattered. Every obvious fix is a gold price, and gold is the one quantity
that inflates: quest gold is `15 x L` per site over roughly four days, so
income runs about **4 g/day at level 1 and 75 g/day at level 20** while HP
pools barely double (12-20 base, +10 buyable). Flat prices are brutal at the
front door and rounding error at the back; scaled prices are a curve to
re-tune forever, and a bed is a bed.

> **The spine: do not make rest expensive. Make rest incomplete.**
> Gate recovery on **rate and access**, never on price. Time and geography do
> not inflate; a cap on what a night can restore is worth exactly as much at
> level 20 as at level 1.

*(Slices 2, 3a, 3b and 4 shipped the answer: a day costs a job, what a fight
leaves on you no longer stops at the door, and the night no longer makes
anyone whole — HP knits only to the **wound ceiling**, and the wounds
themselves come off only through the treatment ladder. `camp --heal` now
means "camp until as whole as the wilds can make you", while ferocity and
one mercy per character level make that added lethality survivable.)*

Hence four slices: cut the encounters, make days cost something (quest
clocks), make damage persist past a night (wounds), and make defeat
survivable enough to carry that weight (mercy).

### Settled decisions (do not reopen without a design session)

- **HP stays the scalar.** Wounds are named located records layered *on top*
  of it, not a replacement. Removing the scalar is a rewrite: it is
  load-bearing in the bestiary's 25 bench-fitted `level`/`ref_pack`
  annotations, the threat math (`THREAT_BASE ** level / ref_pack`), the
  spiral (`Entity.wound_penalty`), the pause layer (`PAUSE_HP_FRACTION`,
  `standing_order`, `fight_winding_down`, `sim_pause_policy`), and all five
  bench harnesses. Removing the *displayed number* is a formatting pass, and
  it buys the whole felt effect.
- **Max HP is the constitution stat.** No new stat.
- **Injury is ONE system with two time constants**, no in-fight/between-fights
  seam. *(Shipped in slice 3b; rules.md's Wounds & Recovery add-on is the doc
  of record. This superseded an earlier call in the same session that wound
  penalties should wait until the next fight; the designer pushed back and
  was right.)*
- **Wounds are recorded for the played party only.** Foes keep the scalar:
  they do not persist between fights, so records buy nothing and would cost
  the entire bestiary calibration. Foe wound *narration* is free. *(Shipped
  in slice 3b.)*
- **Conditions are built as a general system, not a bleed special case.** It
  has been the named blocker behind varied enemies, venom, and varied magic
  for three sessions; build it once, properly. *(Shipped in slice 3a.)*
- **Defeat's permanent setback is a maiming, not a stat point.** `rules.md`
  fixes STR and DEX as immovable, and an unrecoverable stat point in a 1-20
  ladder is a death spiral in disguise. A maiming is the same mechanical hit,
  lives inside the wound system, narrates better, and is **curable** by
  high-tier magic or a prosthetic — a story hook and a gold sink instead of a
  punishment. *(The maiming itself shipped in slice 3b — a crippling blow to
  a limb that would have killed. Slice 4 shipped its second use: beast
  mercy.)*
- **Encounter count stays a weighted roll for now**; site count becomes a
  template-declared place count. Letting narrative content decide a job's
  length is its own queued pass (below). *(Shipped in slice 1.)*

Rejected in session, with reasons, so they stay rejected: **scaling tavern
prices** (a bed is a bed, and it inflates); **food or upkeep as a gold sink**
(same inflation, and it taxes a resource with no other pressure on it);
**changing potion prices** (potions are the overextension warning light, and
they gain value for free once camping stops substituting for them);
**retribution or patrol attacks as healing pressure** (re-adds the
contentless combat this whole rework removes).

### Parked out of the rework

Additive to the schemas above — none of them requires redesigning anything.

- **Damage types and weapon profiles** (cut / pierce / blunt / burn / poison
  / magic). `Weapon` already carries `move_tags` and severity flats, so a
  `damage_type` field is cheap now that conditions exist (shipped 3a).
- **Magic energy bypassing protections.** Waits on damage types, and on
  armour existing at all.
- **Armour interacting with wounds** — UNBLOCKED 2026-07-26: with slice 3b
  shipped, a tier shift also decides whether a crippling blow kills, maims,
  or merely wounds, and whether the record is severity 1, 2 or 3. That is a
  far better job than "+DEF", and it is the strongest argument armour has
  ever had. Still the designer's call to adopt, simplify, or defer.
- **Foe wound records.** Rejected for v1; revisit only if persistent named
  enemies (the nemesis record) ever need scars.
- **Prosthetics** — steampunk and magical limbs and eyes, including ones that
  push a stat **above** the natural cap. Note the synergy: the queued *stat
  transcendence + magic items* item is the membrane they need, and
  prosthetics are its ideal first authored customer — a magic item with a
  scar attached. `Wound.prosthetic` shipped as a seed field in slice 3b, so
  the schema cost is already paid: what remains is the item content and the
  above-cap rule.
- **Disease** as a third condition family beside poison and bleed.
- **Infection / wound complications over time** — an untreated wound
  worsening rather than merely persisting; natural once disease exists.
- **Removing HP from the MODEL.** Slice 3b removed it from the DISPLAY only
  (the played surfaces band it into a state word; `status`, the pause menu
  and the detailed log keep the digits). The model keeps the scalar, and the
  settled decision above says why.
- **A true en-route travel position.** Slice 1 SHIPPED the two real fixes
  (the roll happens on the road, off the origin land's pool) but still
  bounces an interrupted trip back to the origin, and a road SIGHTING is
  simply slipped past rather than offered as a choice. Proper mid-road
  positioning wants the local navigation layer and `ui/minimap.txt`.
- **Road-encounter rate trim.** `TRAVEL_ENCOUNTER_CHANCE` 0.15/day,
  `EXPLORE_ENCOUNTER_CHANCE` 0.30, `CAMP_ENCOUNTER_CHANCE` 0.10 were sized
  against 3.74-fight quests; now that quests average 1.66 the road is a
  much larger *share* of all combat, and slice 2's clocks price the trips.
  Re-judge from played evidence; the lever is a trim to ~0.10 / ~0.20, not a
  redesign.
- **A travel layer in the career sim.** `bench_quests`' careers still teleport
  between jobs, which is why 51% of its turn-ins land in the QUICK band —
  a played campaign, paying 1-2 days each way, will sit in "on time" and
  drift late. Adding the road would make the sim's calendar honest against
  the clock, at the cost of breaking comparability with every career number
  in benchlog. Do it deliberately, in its own pass, not as a side effect of
  another slice.
- **Wilds camping restoring less than full STA** (`CAMP_STA_FRACTION` ~0.75,
  a bed 1.0). Held at 1.0; pull it only if multi-encounter quests get chunked
  into one-fight days.

### Measurements taken 2026-07-26 (do not re-derive)

- **Encounters per quest, before slice 1:** mean **3.74**; 1:9.0% 2:19.7%
  3:24.4% 4:13.6% 5:14.9% 6:10.2% 7:4.3% 8:2.9% 9:0.9% — **47% were 4+**.
  *After slice 1 (measured over 4900 generated quests): mean **1.657**;
  1:49.3% 2:35.8% 3:14.9%, hard max 3, no tail. 9.8% of quests span two
  places.*
- **Travel encounters work**; they are rare, and the sighting valve is widest
  exactly where a new campaign is played. Real `notice_contest`, real wild
  pools, 20k rolls per party level:

  | party lvl | sighting (no fight) | ambush | met square | fight given a roll | per 1-day trip | per 2-day trip |
  |---|---|---|---|---|---|---|
  | 1 | 37.7% | 6.2% | 56.1% | 62.3% | **9.4%** | 17.3% |
  | 3 | 24.8% | 4.3% | 70.9% | 75.2% | 11.3% | 20.9% |
  | 5 | 13.1% | 11.3% | 75.5% | 86.9% | 13.0% | 24.1% |
  | 8 | 8.0% | 6.3% | 85.6% | 92.0% | 13.8% | 25.5% |
  | 12 | 4.7% | 13.9% | 81.3% | 95.3% | 14.3% | 26.4% |

  One road fight per ~11 one-day trips at level 1.
- **Total XP to level 20** is 19,000 quoted (`sum(100 * L)`, L = 1..19);
  current mean quest pay is about `85 * L + 42`, giving the ~38 quests the
  career sim reports.

---

## Queued — landmark problems (what the banded refill did NOT ship)

*(2026-07-26: the **banded refill itself SHIPPED** with the attrition
rework's slice 2 — settlement slot counts, lazy per-day refill, expiry, and
the deletion of the up-front coverage assert are all in `quests.py` and
documented in rules.md's Quest System, "The clock". What is left of the
original entry is the authored half.)*

*(Story-layer batches 1-2 shipped 2026-07-12; pacing anchors measured
2026-07-12: played campaigns L10 ~ day 45-65 (~10-12 chat hours), L20 ~
day 110-150 (~25-30 hours). Still good and cheap once wanted in play:
war-flavored reskins on local quests in threatened lands, and a rescued
recruit as an extra wave-3 tangible.)*

- **Objective high-level problems that exist independent of the player**:
  landmark problems known by rumor from level 1, standing on the board
  regardless of the party's level and NOT subject to the refill's churn (a
  dragon does not lapse in seven days). The refill posts ordinary work; this
  is the authored counterweight to it.
- Later sim hook (parked): other heroes occasionally solve, or die to, a
  landmark problem while the player is elsewhere.

---

## Queued — quest shape from narrative content (its own design pass)

*(2026-07-26, the quest-length session. That session cuts encounters per
quest to 1 by default / 2 for a middling job / 3 at most, and moves site
count to a template-declared place count — a job spans two sites only
when the fiction genuinely moves between two places. The encounter count
itself stays a weighted roll for now: a deliberate placeholder.)*

- The designer's intent: **the narrative content should decide how long a
  job is** — a template's premise, its stakes, and its place structure
  imply whether it is one fight, a two-stage hunt, or a three-beat
  escalation, and a rolled 1/2/3 only approximates that. The pass makes
  the encounter count (and the shape of each encounter's role in the
  quest) an authored property of the template, so the board's mix of
  short and long work is designed rather than sampled.
- Wants the same pass over the good templates in `quests.py`, the epics,
  and the dark templates in `karma.py`, and it pairs naturally with the
  quest-wording rework (retro roadmap item 2) — same files, same content
  register (`writing.md`).
- Schedule after the quest-clock and wound slices have been played: what
  a job's *right* length feels like is a play finding, not a desk one.

Story items on the shelf:

- **The apocalypse questline — the L12-20 second spine.** Parked until
  the magic tier exists (its payoff enemies are demons above the dragon
  row). *(Pivot note: under the villain frame this may become the
  RIVAL conquering force — the thing that conquers half the world if
  the player doesn't, or the employer the player answers to. Decide
  when the good-karma mirror lands.)*
- **Progression frames** (guild advancement, the legendary-smith arc) —
  narrative wrappers around the same combat quests; cheap now that
  questlines exist. *(2026-07-28: the legendary smiths themselves shipped
  as commission vendors — the weapon layer; what stays parked here is the
  narrative ARC around one: winning a smith's respect, fetching the ore,
  the rival buyer.)*

**A career finding to design against**: the top band (15-20) is still
the hard edge (per-quest wipe 40-65% at level) and still waits on
armor and the rank-4 capstones for part of its missing player power —
the gear half shipped 2026-07-28 (masterwork in shops, magic weapons on
the reward ladder and the smiths' anvils); a top-band career re-bench
with the new gear actually reaching sim hands is still owed.

---

## After that (in rough order)

*(Shipped and struck from this list: placeholder magic + cross-land
deliveries 2026-07-14; Magic & MIND 2026-07-15; ranged combat & guns
2026-07-16; party/CHA layer 2026-07-11 — mechanics all in rules.md.)*

1. **What remains of the magic item**: **the wraith** (buildable now that
   attack spells exist); **rank-4 capstones** (authored tomes/mentors —
   the 14-20 band's player power); **enemy spell use** (openers, not
   just bolts); **flight ranks 3-4**. *(The stat-transcendence half —
   +stats to ~double the natural cap through gear, +DEX an order of
   magnitude dearer than +STR/+pool — SHIPPED 2026-07-28 as the weapon
   generation system: rules.md's Weapon Ladder & Generation add-on.
   Non-weapon magic items — rings, amulets — would reuse its sp table
   if ever wanted.)*
2. **Armor** — provisional design: shifts the incoming wound tier down
   at the cost of a DEX penalty and higher STA drain. *Status: adopt,
   simplify, or defer.* (Designer lean: probably never important.)
   *(2026-07-26, after slice 3b: the wound system gives armour a far better
   home than "+DEF" — a tier shift now also decides whether a crippling blow
   kills, maims, or merely wounds, and how deep a record it leaves. See the
   attrition rework's parked list.)*
3. ~~**Named & masterwork weapon instances**~~ — **SHIPPED 2026-07-28**
   (rules.md's Weapon Ladder & Generation add-on; designlog has the
   session): the sp currency, the budgeted generator, masterwork
   shoppable in capitals, the famous armory (owners wield their pieces),
   the legendary smiths with the pride floor, weapon-reward quests, and
   the villain arsenal's mechanics (the Midas gold quirk and the
   karma-on-kill quirk are live generator rolls; a leech blade waits on
   an authored regen rider). Remaining content work, not framework:
   hand-authoring signature pieces where the fiction wants a SPECIFIC
   blade rather than a rolled one.

---

## The major-feature shortlist (2026-07-14) — ordering notes

Foundations all shipped (magic, ranged, levelling); what stands:

- **Conditions** — SHIPPED 2026-07-26 as the attrition rework's slice 3a
  (rules.md's Conditions add-on): bleed, poison and burn as one general
  framework. **Disease stays parked** as the third family, and the queued
  customers the framework now unblocks are cheap: a school-wide cast rider
  (every fire bolt burns — deliberately held back, it moves every bestiary
  row because hero wizards gain it too), the firebomb, poisoned blades and
  the rot spell, and varied-enemy riders generally.
- **Free-play facilitation / overriding the mechanics** — mostly dm.md
  doctrine plus the override surfaces that already exist (`forge`,
  `give --as`, the hand-editable save). Cheap, worth doing early.
- **Professions** — a between-fights layer off downtime and the economy;
  natural feeder for domain play.
- **Intraparty mechanics & prominent main NPCs** — deepens shipped
  layers; its big multiplier is the parked off-screen event simulation.
  *(The nemesis record — villain roadmap item 2 — is this thread's
  first concrete customer.)*
- **Domain play** — the fuller layer (followers, rulership, buildings);
  the natural answer to "what is gold FOR at L15+". *(2026-07-27: its
  thin edge SHIPPED as the conquest slice — holdings, tribute, and levy
  garrisons already give gold a standing job. Grow the rest out of that
  state; the greed economy is the natural next hookup.)*
- **The content passes** — deliberately last within their threads.

---

## Parked ideas (agreed to exist, not scheduled)

- **The posting-band trim** (2026-07-27, the conquest session) — the
  designer floated lowering `SETTLEMENT_KINDS` posting caps (capital 15,
  town ~9, village ~6). The conquest ladder that motivated it shipped as
  the separate GARRISON bands instead, leaving the calibrated quest
  economy untouched; the trim stands on its own merits only. Note the
  cost before pulling it: capital 20 -> 15 means no L16-20 board work
  ever posts, and it needs a bench re-run.
- **The conquest mirror for the good campaign** (2026-07-27) —
  liberating a war-occupied settlement for its own crown (or a
  protectorate flavor of holding). One mechanic, two skins, like the
  karma mirror; park until the dark conquest has been played.

- **Hell as a place** (2026-07-19, dark-quests session) — walkable any
  time at no cost, dangerous, demons love bullying. Today it is pure
  DM narration (dm.md); the parked content: the gladiator pits of hell
  (with the bribe-to-lose-on-purpose bout), the castle bought in human
  bones, hell's org chart above the collections agent. First customer
  of any hell map.
- **A geographic wanted level** (2026-07-19, dark-quests session) —
  searched-for in one settlement / the whole land / all lands, as the
  designer's brainstorm named it. Heat is the GLOBAL version and
  shipped; the geographic split is a refinement — park until heat has
  been felt at the table.
- **Standing dark enterprises** (2026-07-19, dark-quests session) —
  the powder network (and rackets generally) as HOLDINGS that earn and
  draw rivals over time, not one-shot quests. *(2026-08-04: the Powder
  Trade template retires with THE DARK REWORK; the smuggling/powder
  crime category carries the seed.)* The standing layer feeds domain
  play / conquest ticking.
- **The rot spell & evil magic content** (2026-07-19, dark-quests
  session) — "learn an evil spell that quickly rots the opponent
  alive; use it on an innocent bystander" wants a new spell (and the
  conditions system, which shipped 2026-07-26); park with the magic
  content pass, alongside the school-wide cast rider that pass also owes.
- **War-side-taking** ("a land has attacked a neighbor — help the
  aggressor") — already the dark content pass / war-integration item
  (villain roadmap 6); noted here so the brainstorm line has a home.
- **An army mechanic** (2026-07-19) — "some army mechanic might be
  good" for the conquest game. *2026-07-27: its SEED shipped with the
  conquest slice — the garrison levy number, resolved heads-against-heads
  off-screen. What stays parked is armies that MOVE (rival powers, fronts,
  army-vs-army campaigns); feel out the shipped raids first.* The guard
  rail stands: one chat line per decision, or it's out.
- **Karma-gated powers / hell ranks** (2026-07-19) — bad karma
  currently buys nothing but heat and rich work; whether lifetime
  wickedness should UNLOCK anything (evil abilities, hell hierarchy
  ranks, the imp's promotions) is deliberately open — see Open
  questions.
- **Summoning** (2026-07-15) — needs its own design round (action
  economy is the game's strongest measured force).
- **Antimagic** (2026-07-15) — trivial to build, nothing to counter yet.
- **Ward, the tier-shift shield spell** (2026-07-15) — note it doubled
  as the provisional armor design.
- **Opener economy in play** (2026-07-15) — if played wizards resent
  the pool burning on trash fights, the fix is a session-side hold
  toggle, not engine smarts.
- **Opt-out tutorial register** (2026-07-14) — relevant only if the
  game gets a second player.
- **Off-screen event simulation** (2026-07-12) — a world tick rolled at
  settlement arrivals from small event tables, day-stamped. First
  customers: the landmark problems, the nemesis record, the rival.
  *(2026-07-21: promoted to a SEED of the retro pivot's simulated
  world — feeds the macro-game design session, retro roadmap 4.)*
- **Faction reputation** — designer has more to spec; nothing until
  then. *(Note: karma IS a first faction axis — law vs the party;
  spec the rest against it.)*
- **Settlement flavor lines** — valuable but easy; deliberately not yet.
- **The rival** — ABSORBED into the villain roadmap (nemesis
  persistence, item 2) and the apocalypse-as-rival-conqueror note.
  *(Bumped way back with the nemesis, 2026-07-21.)*
- **The traitor twist** — one authored questgiver per conquest variant
  collaborating with the aggressor; cheap authored beat.
- **Morale & surrender** — enemies breaking, yielding, bargaining.
  *(Pivot note: posse PARLEY — bribing the Watch, demanding surrender
  — wants this; build them together.)* *(2026-07-26: the attrition
  rework's slice 4 shipped its first half — `FoeSpec.ferocity` and
  low-ferocity rosters breaking off — so what remains here is the
  party-facing side: yielding, bargaining, parley.)*
- **Story recruitment** — "the ogre yields and joins you", DM-driven.
- **Weapon reach** — a small first-exchange modifier; distinct from the
  field.
- **Cover & terrain on the field** (2026-07-16) — prose until the
  wilderness gets a terrain pass.
- **Friendly fire into the press** (2026-07-16) — only if play shows
  free focus-fire reading wrong.
- **The 2-STA heavy swing** — sim-rejected while Spent is lethal.
- **d12 variance experiment** — don't fork the dial while lethality is
  settling.
- **Asymmetric Spent** — soften attack to −3 if spent-vs-fresh grinds
  ever feel wrong.
- **A PC happiness stat** — kept OFF (2026-07-11).
- **Prey depletion (the hunt-spam lever)** — only if play shows
  hunt-spam degenerate.
- **Per-weapon pressure dice** — rejected; 2d6 stays the one dial.
- **Level requirements on masterwork/legendary weapons** — rejected;
  authored placement gates them.
- ~~**The "obliterating" wound tier**~~ — effectively ANSWERED by slice 3b
  (2026-07-26): a crippling blow to a vital already reads as the killing
  one, and the same blow to a limb maims instead. Re-open only if the top
  band, once authored, still wants a fifth tier of its own.
- ~~**Venom / conditions**~~ — SHIPPED 2026-07-26 (slice 3a). The great
  spider is venomous and the pyromancer's fire clings. The `level`
  annotations were deliberately NOT re-fit: both rows moved toward the
  calibration band and stayed in family with a catalog that is broadly
  annotated easy — see benchlog for the numbers, and "Re-annotate the
  bestiary for the pain-2 party" below for the pass that owns it.
- **Survival/adventure-sim pivot** (hunger, upkeep, inventory) — kept
  on the books as a possible deliberate pivot, but note 2026-07-19
  chose the GREED ECONOMY over food as the villain game's sink; this
  pivot is further away than it was. *(2026-07-21: the retro pivot is
  a sibling — macro decisions over a simulated world — so pieces of
  this may return through the macro-game design session.)*
  *(2026-07-26: PARTLY CASHED. The attrition rework takes this pivot on
  the WOUND axis, not the hunger axis: named located injuries, blood
  loss, convalescence, maiming, prosthetics later. Food and upkeep stay
  rejected as gold sinks for the reason this whole rework turns on —
  flat prices inflate away. If rations ever return it is as carrying
  CAPACITY on long wilderness trips, never as a price.)*
- **Power potion re-stock** — if War-Breath ever makes Power scarce.
- **Crit/fumble on the 2d6** — fattens both tails of every exchange;
  full bench re-run before judging.
- **Party members as lives, the wipe version** — the in-fight half
  shipped as fate's bargain; watch whether recruit renewal softens it.
  *(2026-07-26: the attrition rework's slice 4 answers the wipe half a
  different way — left-for-dead once per character level, with a maiming
  as the price. Re-judge this entry from play.)*
- **A PC-centric career sim** — if played campaigns drift from the
  bench's even-duo story. *(Pivot note: a karma-playing career variant
  — dark quests + posses in the policy — is the natural check once the
  villain game has been played; today no sim sees karma at all.)*
- **Quest history readout** — cheap; gives the save a memoir.
- **Site persistence / repopulation** — the stick version of one-go
  sites. *(2026-07-26: its old trigger is gone — the attrition rework
  DELETES the XP streak. The new pressure is the wound track: camping
  restores stamina but never HP, so a multi-encounter quest is a real HP
  budget. Re-judge only if that proves too soft.)*
- **Give the rapier its niche back** — do nothing until felt in play.
- **Re-annotate the bestiary for the pain-2 party** — calibration
  polish, not a fire.

---

## Open questions

- **Karma AS the level track?** (2026-07-19) The shipped slice runs
  karma beside XP (bucketed awards). The radical version — karma IS
  progression, levels EARNED by wickedness under the imp's quota —
  would make the villain frame total. Decide after the dark path has
  been played; the bucket design was chosen precisely so the merge
  stays cheap.
- **What does bad karma BUY?** Heat and gold-rich work only, today.
  Candidates: karma-gated abilities, hell ranks (titles + perks), the
  luxury economy's prices. The other half of the original "good and bad
  karma as xp unlocking abilities" idea — deliberately deferred out of
  the first slice. *(2026-08-04: first customer planned — lifetime sin
  drives THE DARK REWORK's crime-suggestion unlocks; powers/ranks still
  open.)*
- **The heat curve's numbers** — KARMA_HEAT_STEP 100, HEAT_CAP 3,
  cooldown 2 days, chance 0.6, dark gold ×1.5: all provisional,
  hand-set, sim-unverified (no sim plays dark). Tune at the table
  first; a karma career sim is parked above.
- **Armor:** adopt, simplify, or defer (the least-developed system;
  designer lean: never important).
- Every constant is provisional and sim-tuned, never hand-designed — the
  current numbers live in `develop.md` ("Balance / tuning").
