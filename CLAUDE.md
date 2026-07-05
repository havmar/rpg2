# RPG2 — Combat Sim Prototype

A combat simulator for a fantasy RPG, intended to be played through Claude Code
with Claude as DM. Fights resolve on their own (no input once a fight starts,
except the **pause**: a trigger stops the melee for one "fight on / drink /
convert / retreat?" question, then it runs to conclusion) and produce an
outcome plus a narrative log; the DM narrates *over* that log. The player's
real decisions happen *between* fights — and at the pause.

> **PLAYING, NOT DEVELOPING? Read `dm.md` first.** Whenever the task is to
> start, continue, or test a playthrough as DM (rather than change the game),
> `dm.md` is the required reading: the play protocol (one encounter per
> message, PC-vs-companion, which decisions are the player's), narration
> style, and a quick mechanics reference. This file (CLAUDE.md) is the
> development guide; you don't need most of it just to run a game.

## The feel we're going for

A **mechanics-centered RPG** with the freedom of a tabletop game. Combat is
*autocombat* — it runs to completion in one call so play stays fast in chat
instead of grinding through every roll by hand — but the world around it stays
open-ended and player-driven. The engine owns the numbers; the DM owns the
fiction.

**How play is driven:** the game is *two halves working together*.
- **The scripts (`rpg.py`, `sites.py`)** are a library of mechanics primitives
  and content — `start_fight`, `group_combat`, `short_rest`, `long_rest`,
  `party_wiped`, the foe catalog, the set sites.
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

## Working with the designer

The user is this game's designer and only audience. He built these systems and
knows them; what he doesn't hold in his head is the fine mechanical detail
(exact modifiers, formulas, tuned constants) — supply *that*, don't re-explain
his own design back to him.

- **No reflexive commentary.** Cut filler observations like "that's the
  stamina system working as designed" or "this is the intended difficulty" —
  in dev and test sessions they're noise. When something happens that the
  design intends, just show it happening.
- **Real feedback is wanted — actively.** Say when something feels weird,
  non-optimal, or frictful from the DM/co-designer chair: a fight that played
  as a foregone grind, a log that buried the decisive number, a choice that
  wasn't really a choice. General impressions and opinions are welcome;
  point out obvious problems and low-hanging fruit proactively instead of
  waiting to be asked.
- **When transcribing his chat notes into docs, rewrite them.** Present the
  intent in clean prose; don't paste raw brainstorm wording into rules.md /
  plan.md / this file.
- **Dev communication is the place to be thorough.** Post-implementation
  summaries, tuning reports, and design discussions should be genuinely
  verbose: what changed, where, why, what the measured numbers were before
  and after, what was tried and rejected. Conciseness is a virtue of DM
  *narration*, not of dev reports — an over-terse summary that forces the
  designer to ask follow-ups costs more than a long one.

## Files

**Mechanics detail lives in `rules.md`, not in this list.** Each entry here is
a pointer: what the file is, how it's run, where its docs are.

- `dm.md` — **the DM playbook: read it before playing or testing a game.**
  Play protocol, narration style, quick mechanics reference. Keep it in sync
  when play-facing rules change.
- `rules.md` — **the ruleset: the source of truth for mechanics and the
  design spine** (the "why" behind every number, the log format, the pause,
  weapons, survival, progression). Read it before changing mechanics.
- `plan.md` — **the roadmap: planned features only**, in build order (next
  up: the encounter & quest system), plus parked ideas and open questions.
- `rpg.py` — **the engine.** Combat (`group_combat` + the pause/retreat
  layer), weapons and breakage, the survival tracks and rests, progression,
  economy, random party generation, and the batch-sim policies
  (`sim_fight` / `sim_pause_policy`). Stdlib-only and self-contained;
  everything else imports it. All tunable constants sit at the top.
- `sites.py` — **the content.** The foe catalog (`FOES`, `make_foe`), the two
  set sites (`SITES`: the bandit **hideout** = the starter, base pay; the
  skeleton **barrow** = the tough site, 3x pay; room layouts in
  `HIDEOUT_ROOMS` / `BARROW_ROOMS`), and `run_site`, the one site loop the
  one-shot run and the batch sims share. **Both sites are set encounters —
  the DM never invents their rosters.** The seed of the encounter & quest
  system. One-shot: `python sites.py [--site hideout] [--seed N]
  [--training N]`.
- `session.py` — **the DM driver used to actually play.** A thin CLI over
  rpg.py/sites.py that pickles party/clock/purse state to
  `.session_state.pkl` (gitignored — a save file) between invocations, so
  pacing decisions stay real turn-by-turn choices. Adds no game logic of its
  own. `python session.py --help` lists every subcommand with its rules;
  dm.md says which decisions belong to the player. Encounter commands print
  the full log then the `--- PLAYER LOG ---` block the DM pastes into chat.
- `tune.py` — Monte Carlo sweep over barrow layouts plus the
  resource-pressure check (the usual sim policy vs "reckless": no pauses, no
  potions — the no-resource baseline, whose wipe rate is what ignoring your
  resources costs). Reports the death split, attrition, clear%, flee%, and
  early% (rooms 1-2 forced a pause/Down/potion — the per-encounter threat
  criterion). **Re-run after any mechanics change.**
- `bench_training.py` — wipe/clear rates per combat-training rank 0-3 at both
  sites ("does a level-up feel noticeable against a fixed enemy").
- `bench_weapons.py` — the "suited, not ranked" weapons matrix: each stat
  frame x each quality weapon, duel and swarm. Also the doc of record for WHY
  the zweihander does not cost 2 STA per swing (sim-rejected while Spent is
  lethal).
- `.notes.txt` — raw brainstorming notes (unstructured, historical).

> **Registering files:** whenever you add a new file to this project (a new
> scenario, tool, or module), add it to this **Files** list with a one-line note
> on what it is and how it's run. Keep this list the index of what exists.

> **Keeping the docs current:** `rules.md` (mechanics + design spine) and
> `plan.md` (the roadmap) are living documents — keep them in sync with the
> code automatically, as part of the same change, not as a follow-up. When you
> change a mechanic, update `rules.md` to match; when a roadmap feature ships,
> **delete it from `plan.md`** (implemented things are documented in rules.md,
> not the roadmap); when one is deferred or re-scoped, move/update its entry.
> If a code change contradicts either doc, the doc is stale — fix it in the
> same commit. Flag any conflict you notice between them rather than leaving
> it. Division of labor: **rules.md owns mechanics description; this file owns
> dev workflow, the file index, tuning levers, and measured balance numbers** —
> don't re-explain a mechanic here that rules.md already covers.

## Running

```
python session.py new    # start an actual DM-driven playthrough (see dm.md)
python sites.py          # one-shot barrow run, full narrative log
python sites.py --site hideout --seed 3   # one-shot starter site, reproducible
python rpg.py            # same one-shot (delegates to sites.py)
python tune.py           # outcome-distribution sweep + resource-pressure check
python bench_training.py # wipe/clear rates per combat-training rank
python bench_weapons.py  # weapons "suited, not ranked" matrix (duel + swarm)
```

Use `PYTHONIOENCODING=utf-8` when piping output (Windows cp1250 default). Output
is intentionally ASCII-only, so plain runs are usually fine.

## The dev map (where mechanics live in the code)

The one-screen index for finding the thing you need to change. What each
mechanic *does* and *why* is rules.md's job.

- **Tunable constants** — all at the top of `rpg.py`, grouped and commented:
  fatigue (`WINDED_STA`, `SPENT_PENALTY`, `STA_ATTACK_COST`), survival
  (`SAVE_COST`, `HEAL_COST`, `FIRST_BLOOD_*`, potion restores, the
  `*_RECOVERY_*` family, `REVIVE_HP`, `SHORT_RESTS_PER_DAY`), the pause layer
  (`PAUSE_STA_TRIGGER`, `PAUSE_HP_FRACTION`, `PAUSE_ACTION_DEF_PENALTY`,
  `FLEE_BONUS`, `BERSERK_*`, `WAR_BREATH_*`), the graze floor
  (`GRAZE_FLOOR_MARGIN`), wound tiers (`TIER_HP`), progression
  (`XP_LEVEL_STEP`, `TRAINING_MAX`, `PROFICIENCY_MAX`), economy
  (`POTION_PRICE`, drop chances, quest rewards), weapons (the `WEAPONS`
  catalog, `BREAK_CHANCE_PER_GAP_SQ`, starting-weapon chances), and hero roll
  ranges (`HERO_*_RANGE`).
- **The exchange** — `Entity.pressure` (the opposed roll with its full
  breakdown) and `_attack` (severity, graze floors, saves, the two-level log
  lines). `_check_weapon_break` on parries and Clashes.
- **The melee** — `group_combat`: round-start actor snapshot (the dying
  swing), live targeting, STA spend, Winded/Spent crossings, pause triggers.
  Returns a `Pause` mid-fight when `pause_triggers=True`; resume by calling
  again with the same `fired` set (keyed by `(kind, hero)` — each trigger
  once per hero per fight, crossing-only), `first_round=round+1`, and
  per-hero `actions`.
- **Retreat** — `attempt_retreat` (parting blows + ONE group chase roll;
  `pursues=False` foes never chase), `refresh_foes_after_retreat` (fled-room
  persistence).
- **Between fights** — `short_rest` / `long_rest` (the `Clock`), `use_potion`,
  `use_heal`, `buy_potion` / `buy_weapon` (the `Purse`), `equip_weapon`,
  `award_xp` / `award_quest` / `roll_loot`, `train_combat_once` /
  `train_proficiency` (session play banks points; only the sims auto-spend
  via `train_combat`), `party_wiped`, `start_fight` (revive-only).
- **The log** — `CombatLog` (full + `.player` levels; `_debug` / `_play`
  emit helpers so plain lists still work).
- **Content** — `sites.py`: `FOES` (stat blocks), `make_foe`, `SITES`,
  `HIDEOUT_ROOMS` / `BARROW_ROOMS`, `run_site` (the sim loop), `roster_lines`.
- **Session state** — `session.py`: one pickled dict (party, clock, purse,
  rng, `pending` paused-fight record, `rooms` fled-room records). A paused
  fight blocks every between-fights command until settled.

## Balance / tuning

**A tuning principle (2026-07): the sims understate the player.** The batch
policies rest on a fixed schedule, drink potions on crude thresholds, and
answer pauses with one-number rules (`sim_pause_policy`); a real player paces
rests, reads the STA math before every door, and times retreats. So sim clear
rates run *below* played clear rates, and harsher sim numbers than "feels
fair" are acceptable — tune for the felt game, and let rooms 1-2 of a site
threaten in the sims, not just the last one.

**The lethality retune (2026-07): danger lives in the encounter, not the
grind.** The player can camp after any encounter, so a site that only
threatens via attrition doesn't threaten at all. Targets set by the designer:
the starter hideout at rank 0 clears ~55% with someone hitting the floor in
about half the runs, and **not using resources should mostly mean death**.
Levers pulled then: enemy DEX +1 across the board (who hits is DEX's job) and
`SHORT_RESTS_PER_DAY` 2 -> 1.

**Current measured numbers (2026-07-06, after the per-hero pause fix).**
Making pause triggers fire per hero (instead of once per fight for the whole
party) gave the sim policy more intervention points and moved the numbers a
few points toward survival — **the hideout now sits above the retune's ~55%
clear target**; flagged for the designer, levers untouched:

- **Hideout** (rank 0, 10-20k runs): clear **~64%** (was ~57-59), wipe
  **~33%** (was ~39-41), Down in ~33% of runs, vs **~68% wipe reckless** —
  the resources are still worth ~35 points of survival.
- **Barrow** `[3, 3, 4]` (rank 0): clear **~3.5%** / wipe **~95%**, early
  pressure ~94% (rooms 1-2 force a resource), reckless wipe ~99% — a fresh
  party still simply should not be there.
- **Per training rank** (`bench_training.py`, 5k/rank, ranks 0-3): barrow
  clears **3% -> 17% -> 44% -> 74%**; hideout **64% -> 86% -> 96% -> 99%**.
- **Gear** (katana + zweihander loadout, 5k runs): fresh + steel takes the
  barrow to only **~13%**; the arc is the *combination* — **training 2 +
  steel clears ~70%** (Down ~30%), training 3 + steel **~90%**.
- **Weapons** (`bench_weapons.py`): rapier is the best duelist on three of
  four frames (on the precise frame it's a coin flip with the zweihander);
  the zweihander sweeps every swarm column (~17-22% on high-DEX frames,
  single digits elsewhere — a lone fighter vs 3 tireless DEX-4 skeletons is
  still near-hopeless); the katana is the reliable second everywhere; the
  staff trails everywhere on purpose. No weapon tops every cell.

The intended arc is unchanged: fight the hideout at rank 0 (expect retreats
and downs), level up *and* buy steel over ~2-3 clears, take the barrow at
rank 2+ armed. Most deaths still trace to STA misjudgment.

**Difficulty levers, easiest first:** the room layouts
(`sites.HIDEOUT_ROOMS` / `sites.BARROW_ROOMS`), then survival tunables, then
the pause/retreat layer, then weapons, then economy/progression, then the foe
stat blocks (`sites.FOES` — **enemy DEX is the sharpest knife**: a single
point moves clear rates by tens of percent), then the hero roll ranges
(all constants: see the dev map above). **Always re-run `tune.py`,
`bench_training.py`, and `bench_weapons.py` after touching any of these** —
small changes swing lethality, the attrition curve, and the weapon matchup
matrix.

## Conventions

- Stdlib only; keep `rpg.py` self-contained and importable (everything else
  imports it; `sites.py` holds the content so the engine stays generic).
- Keep narrative/log output ASCII (no em-dashes or special glyphs) for Windows.
- `Entity` is `@dataclass(eq=False)` so instances are identity-hashable (used in
  combat sets and the pause's `fired` pairs) — don't switch it back to value
  equality.
- Two layers, kept separate: thin mechanics in code, rich flavor added by the DM
  over the log. Don't bake prose into the engine beyond terse event lines.
- **Zero backwards compatibility.** This is an early prototype: never spend
  effort keeping saves or schemas loadable across changes. Rename and
  restructure freely; any `.session_state.pkl` is disposable — when a change
  breaks it, delete it and start a fresh game rather than writing migrations
  or compat shims.
- **Saves are disposable during development too.** Don't spend effort
  preserving, backing up, or restoring `.session_state.pkl` while developing
  or tuning: run `session.py new`, wreck the state with test games, move on.
  A playthrough worth keeping is the exception the designer will name
  explicitly, not the default to protect.

## Not yet built (the point of the design)

The between-fights layer is now substantially player choice: gold/XP flow,
skill points are a real allocation (combat training vs weapon proficiency —
nothing auto-spends in session play), `buy_potion` and `buy_weapon` make
shopping real decisions, and which site to run (starter hideout vs 3x-paying
barrow) is the first "pick your fights" choice. The mid-fight layer exists
too: the pause (drink / Berserk / War-Breath / retreat & chase, with fled
rooms persisting). **The next big feature is the encounter & quest system**
(see `plan.md`): player and encounter levels, the whole power curve, a
monster/opponent catalog spanning it, and DM tools to build foes, encounters,
and dungeons from a level number plus the narrative — the two hand-built
sites become instances of a general system (`sites.py` is its seed). After
that: magic/INT, armor, guns + ammo, named weapon instances, party
composition. See plan.md for the full roadmap and the parked-ideas list.
