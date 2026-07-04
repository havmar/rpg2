# RPG2 — Combat Sim Prototype

A combat simulator for a fantasy RPG, intended to be played through Claude Code
with Claude as DM. Fights resolve on their own (no input once a fight starts) and
produce an outcome plus a narrative log; the DM narrates *over* that log. The
player's real decisions happen *between* fights.

## The feel we're going for

A **mechanics-centered RPG** with the freedom of a tabletop game. Combat is
*autocombat* — it runs to completion in one call so play stays fast in chat
instead of grinding through every roll by hand — but the world around it stays
open-ended and player-driven. The engine owns the numbers; the DM owns the
fiction.

**How play is driven:** the game is *two halves working together*.
- **The scripts (`rpg.py`)** are a library of mechanics primitives — `start_fight`,
  `group_combat`, `short_rest`, `long_rest`, `party_wiped`, etc.
- **Claude (as DM)** calls those primitives *on purpose*, in whatever order the
  story wants, and narrates over the result. There is deliberately **no
  autopilot** for pacing: e.g. nothing forces the day to end — Claude decides
  when the party makes camp and calls `long_rest`. This preserves TTRPG-style
  freedom. Some of these calls can be automated more later; for now they're
  manual on purpose.
- **Part of the game lives in instructions to Claude**, not in code. The engine
  won't ever encode every situation; judgement calls, improvised scenes, and
  when-to-call-which-function all live in this file and the DM's reasoning. When
  we settle a rule of play that isn't a pure number, write it here rather than
  forcing it into the engine.

> Project-level environment (Python path, encoding, etc.) lives in the parent
> `C:\minden\projects\CLAUDE.md`. Don't duplicate it here.

## Files

- `rules.md` — the ruleset. The source of truth for *mechanics intent* (the
  "why" behind the numbers). Read this before changing mechanics.
- `plan.md` — the high-concept design record and phased build roadmap that sits
  *above* `rules.md` (design spine, currencies, systems, the phase-by-phase
  feature plan). Read this for direction / what to build next.
- `rpg.py` — the implementation: combat engine, random party generation, and the
  skeleton dungeon. Self-contained, stdlib only.
- `tune.py` — Monte Carlo sweep over room layouts; prints the none/one/both death
  distribution. Use it to re-check balance after any mechanics change.
- `scratch_bandits.py` — scenario: a *bandit hideout* (living fighters with real
  DEX/STR who tire, unlike the brittle skeletons). Imports the engine from
  `rpg.py` and mirrors the survival flow (`start_fight` -> `group_combat` ->
  `short_rest`), exposing `run_hideout()` for batch use. **This is the intended
  TOUGH site**: it pays 3x the skeleton barrow (XP and gold) and wipes a fresh
  rank-0 party ~73% of the time — the designed play is to farm skeletons for
  combat training first (rank 2 brings the wipe rate to ~19%). `--seed N` for
  repro, `--training N` to start the party pre-trained. Keep it in sync with
  the `rpg.py` API.
- `bench_training.py` — Phase 3 benchmark: runs the barrow and the hideout at
  combat-training ranks 0-3 and prints wipe/clear rates per rank ("does a
  level-up feel noticeable against a fixed enemy"). Run:
  `python bench_training.py`.
- `session.py` — **the DM driver used to actually play the game.** A thin CLI
  over `rpg.py`'s primitives that persists party/clock/purse state to
  `.session_state.pkl` (gitignored -- a save file, not source) between
  invocations, since each terminal call is a fresh process. Adds no game logic
  of its own; every subcommand is a direct call into `rpg.py`. Claude (as DM)
  drives a playthrough with this rather than one-shot `rpg.py` runs, so pacing
  decisions (when to rest, when to camp, when to press on) stay real choices
  made turn-by-turn. Subcommands: `new [--seed N]`, `status`, `fight N
  [--type skeleton]` (spawns N foes and resolves one encounter -- **N is
  chosen by the DM each call, freely; it is *not* read from `rpg.py`'s
  `DUNGEON_ROOMS`**, which only sizes the one-shot `run_dungeon`/`tune.py`
  path. When narrating a "barrow room," pick a foe count that fits the scene
  -- `DUNGEON_ROOMS = [3, 3, 4]` is a reasonable reference for what a
  farmable barrow room looks like, but session play isn't bound to it),
  `hideout ROOM` (1-3, resolves one bandit-hideout room against the persisted
  party using that room's **fixed** roster, mirroring
  `scratch_bandits.run_hideout` -- unlike `fight`, the roster size isn't a
  free choice here), `rest`, `camp`, `quest GOLD XP NAME`, `buy HERO KIND`,
  `heal HEALER TARGET` (Heal ability, between fights only -- see below).
  Keep it in sync with the `rpg.py` API whenever primitives change shape.
- `.notes.txt` — raw brainstorming notes (unstructured, historical).

> **Registering files:** whenever you add a new file to this project (a new
> scenario, tool, or module), add it to this **Files** list with a one-line note
> on what it is and how it's run. Keep this list the index of what exists.

> **Keeping the docs current:** `rules.md` (mechanics) and `plan.md` (design +
> roadmap) are living documents — keep them in sync with the code automatically,
> as part of the same change, not as a follow-up. When you change a mechanic,
> update `rules.md` to match; when you finish, defer, or re-scope a roadmap
> feature, update `plan.md`'s phase status. If a code change contradicts either
> doc, the doc is stale — fix it in the same commit. Flag any conflict you notice
> between them rather than leaving it.

## Running

```
python rpg.py            # random party + dungeon, full narrative log (one-shot)
python rpg.py --seed 7   # reproducible run
python session.py new    # start an actual DM-driven playthrough (see session.py)
python scratch_bandits.py --seed 3 --training 2   # the tough site, pre-trained
python tune.py           # outcome-distribution sweep over layouts
python bench_training.py # wipe/clear rates per combat-training rank
```

Use `PYTHONIOENCODING=utf-8` when piping output (Windows cp1250 default). Output
is intentionally ASCII-only, so plain runs are usually fine.

## Core mechanics (see `rules.md` for the full spec)

- Three stats — **DEX** (who lands), **STR** (wound severity + soak), **STA**
  (a draining clock; **Winded** at STA ≤ 3) — plus an **HP** wound pool.
- Each round is an opposed `2d6 + DEX + training − (HP lost) − (2 if Winded)`
  exchange. Higher roll lands; `severity = margin + atkSTR − defSTR` maps to a
  wound tier (deflected/graze/wound/grievous/killing blow). **HP lost is itself
  a roll penalty — the death spiral is the whole point.**
- `group_combat` generalizes the 1v1 exchange to a melee so a party can be
  swarmed. Heroes focus-fire the weakest foe; foes target party members at random.
- **The combat log is two-layered** (see `rules.md`, "Reading the combat log"):
  every exchange prints an interpretive headline (Clash / Lull / turned aside /
  edges past / outmaneuvers / overwhelms, wound phrases with the target's
  `-n to rolls` spiral penalty) with the raw numbers indented beneath it (the
  actual 2d6, every modifier and its source, the full severity arithmetic).
  Winded crossings get a `!!` line and a `stamina:` readout prints every round.
  Deliberately verbose for now — simplify only once the numbers have earned trust.

## Survival & Resources add-on (now implemented)

See the add-on section in `rules.md` for intent. In `rpg.py`:
- **HP carries across the whole run** (drains like STA, never a per-fight reset),
  with only a minimal `HP_RECOVERY_BETWEEN_ROOMS` catch-breath per short rest;
  the real recovery is a **long rest**, which knits HP back at each character's
  `hp_regen_per_night` (= `max(1, round(max_hp / 7))`, so **HP returns over ~a
  week** — a 20-HP tank heals in ~7 nights, not 20). **0 HP = Down** (out of this
  fight; stands back up at `REVIVE_HP` next room), **not Dead**.
- **Power** + an **ability** (`bulwark` / `heal` / `first_blood`) per entity,
  with distinct roles. `bulwark` is the mid-fight save: `_try_save` spends Power
  to step a blow down one tier — always buying off a *killing* blow, and a
  *would-Down grievous* only when a reserve remains; `_attack` logs the raw blow
  and the bought-down result. `first_blood` is the aggressive counterpart
  (rogue/glass-cannon): automatic at fight start, `_first_blood` spends
  `FIRST_BLOOD_COST` (2) Power for a guaranteed `FIRST_BLOOD_HP` (1) graze on
  the focused foe — light on purpose (never a free kill); its real value is the
  death spiral (that foe rolls at -1 all fight). `heal` has no in-fight role at
  all — it's a **between-fights** action, `use_heal(healer, target, rng, log)`,
  spending `HEAL_COST` (3) Power to restore a random `HEAL_RESTORE_RANGE` (1-3)
  HP on self or an ally. Same shape as `buy_potion`: DM-called, never automatic.
- **STA is the binding clock**: it drains in combat and carries across rooms with
  only a small `STA_RECOVERY_BETWEEN_ROOMS` catch-breath per short rest. A **long
  rest recharges STA fully** (overnight).
- **Time economy (`Clock`):** a `day` counter plus a per-day budget of
  `SHORT_RESTS_PER_DAY` (2) short-rest slots. `short_rest(party, clock, log)` (~an
  hour or two of narrative time) spends a slot for a small catch-breath + potion
  use, and refuses once the slots are gone. `long_rest(party, clock, log)` makes
  camp: full STA, the weekly HP tick, Down heroes back up, `day += 1`, slots
  refill. **There is no auto-night** — `long_rest` is a function Claude calls on
  purpose; nothing forces the day to end (see "The feel we're going for").
- **Items** (`healing` / `power` / `stamina`) are a carried stock that **never
  auto-refills**: heroes start with **two random potions** (`random_kit`) and
  restock only via drops or `buy_potion`. A healing potion is *prepped* before a
  room (`start_fight`) for HP regen; `short_rest` spends power/stamina potions
  deliberately when low.
- A character only truly **dies** on an unsaved killing blow; `outcome()` counts
  only the slain.
- **Total party knockout = defeat.** `party_wiped()` (in `rpg.py`, shared by both
  scenarios) checks after every fight: if no hero is left standing, the Down are
  finished off (marked Dead) and the run stops — a game over. So a double-Down is
  no longer a recoverable state; it ends the run.

## Progression & economy (Phase 3 first slice — see `rules.md` add-on)

- **XP:** every not-dead hero earns the full award — 15/encounter + 55/quest at
  the skeleton site, 3x at the bandit hideout (45/165). Level `L -> L+1` costs
  `100 * L` (`xp_to_next`), so the *first barrow clear is exactly a level-up*.
  `award_xp` handles level-ups and banks skill points (1/level).
- **Combat training** (`train_combat`) — the only skill so far: +1 to all tempo
  rolls per rank, rank *n* costs *n* points, cap 5. Since it's the only sink,
  scenarios auto-spend after quest awards; when more skills exist this becomes
  a real player choice.
- **Gold** lives in a shared `Purse`. Income: quest rewards (15 g barrow / 45 g
  hideout) + per-encounter drops (20% -> 5 g, 10% -> a random potion to a random
  hero, `roll_loot`). Sink: `buy_potion(hero, purse, kind, log)` at
  `POTION_PRICE = 10` — a **DM-called between-adventures purchase**, the first
  real player shopping decision. Nothing refills automatically.

## The current prototype scenario

> This section describes the one-shot `rpg.py`/`tune.py` run. **Session play
> (`session.py fight N`) is not bound to `DUNGEON_ROOMS`** -- the DM picks a
> foe count per encounter (see the `session.py` bullet above), using this
> layout only as a reference for what a room "should" feel like.

- **Party:** two randomly generated humans (`make_human`): DEX/STR
  `randint(3, 6)`, STA `randint(4, 7)` (floor raised a step above DEX/STR so no
  hero starts a day already Winded), HP `randint(8, 12)`, Power `randint(3, 6)`,
  a random ability (`heal` / `bulwark` / `first_blood`), two random potions, and
  an epithet from the highest stat (precise/powerful/steady).
- **Dungeon:** rooms of skeletons, `DUNGEON_ROOMS = [3, 3, 4]` (one "day"). HP,
  STA, and the resource stock all carry across rooms (only minimal catch-breaths);
  wounds persist for the run. Clearing all rooms completes the quest
  (gold + XP lump).
- **Skeletons:** brittle, weak individual hitters (DEX 3 / STR 2 / HP 5), no
  Power/kit but tireless — the threat is *numbers*, matching the goblin/swarm
  puzzle in the rules, not raw power. **The farmable site**; the bandit hideout
  (`scratch_bandits.py`) is the tough one you train up for.

## Balance / tuning

`tune.py` reports attrition alongside the death split, plus clear rate and gold.
With random chargen + the 2-random-potion kit, at `[3, 3, 4]` over 20k runs:
~**35% / 12% / 53%** (none / one / both slain), **clear ~47%**, a Down in ~46% of
runs, ~64% Power / ~5% STA left, healing potions spent, ~9 g earned. The wipe
tail is now the *designed* pressure to level — and it is steep at rank 0: per
`bench_training.py`, the barrow goes **48% -> 76% -> 93% -> 99%** clear across
training ranks 0-3, and the bandit hideout **27% -> 56% -> 81% -> 96%**. A
fresh party's first barrow run is now a genuine coin flip (the old `[2, 2, 3]`
layout cleared ~77% at rank 0); trained parties farm. If the rank-0 opening
feels too brutal in play, `DUNGEON_ROOMS` is the first lever to pull back.

Difficulty levers, easiest first: edit `DUNGEON_ROOMS`, then survival tunables
(`SAVE_COST`, `HEAL_REGEN`, `STA_RECOVERY_BETWEEN_ROOMS`, `SHORT_RESTS_PER_DAY`,
`STARTING_POTIONS`), then economy/progression (`POTION_PRICE`, drop chances,
quest rewards, `XP_LEVEL_STEP`, training cap), then skeleton stats, then the
hero roll ranges (`HERO_STAT_RANGE`, `HERO_HP_RANGE`, `HERO_POWER_RANGE`).
**Always re-run `tune.py` and `bench_training.py` after touching any of
these** — small changes swing both lethality and the attrition curve.

## Conventions

- Stdlib only; keep `rpg.py` self-contained and importable (`tune.py` imports it).
- Keep narrative/log output ASCII (no em-dashes or special glyphs) for Windows.
- `Entity` is `@dataclass(eq=False)` so instances are identity-hashable (used in
  combat sets) — don't switch it back to value equality.
- Two layers, kept separate: thin mechanics in code, rich flavor added by the DM
  over the log. Don't bake prose into the engine beyond terse event lines.

## Not yet built (the point of the design)

The between-fights layer is now *partly* player choice: gold/XP flow, combat
training is bought with levels, and `buy_potion` makes stocking up a real
decision (which site to run — farmable barrow vs 3x-paying hideout — is the
first "pick your fights" choice). Still missing: more skills + weapon
proficiencies (so skill points become an allocation, not an auto-spend), gear
that shifts stats / soaks severity / adds STA, raising stats toward an
archetype, and composing the party so builds cover each other. See the
"Between-fights layer" and the add-on sections in `rules.md`.
