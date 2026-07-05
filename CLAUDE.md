# RPG2 — Combat Sim Prototype

A combat simulator for a fantasy RPG, intended to be played through Claude Code
with Claude as DM. Fights resolve on their own (no input once a fight starts,
except the at-most-twice-a-fight **pause**: a trigger stops the melee for one
"fight on / drink / convert / retreat?" question, then it runs to conclusion)
and produce an outcome plus a narrative log; the DM narrates *over* that log.
The player's real decisions happen *between* fights — and at the pause.

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

- `dm.md` — **the DM playbook: read it before playing or testing a game.** The
  play protocol (PC/companion split, one-encounter-per-message, player-owned
  decisions), narration style, and a quick mechanics reference. Keep it in
  sync when play-facing rules change.
- `rules.md` — the ruleset. The source of truth for *mechanics intent* (the
  "why" behind the numbers). Read this before changing mechanics.
- `plan.md` — **the roadmap: planned features only**, in build order (next up:
  the encounter & quest system), plus the parked-ideas list. Broad design
  principles live in `rules.md` (the design spine) and this file; anything
  already implemented is documented in `rules.md`/code, not here. Read this
  for what to build next.
- `rpg.py` — the implementation: combat engine, random party generation, and the
  skeleton dungeon. Self-contained, stdlib only.
- `tune.py` — Monte Carlo sweep over room layouts; prints the none/one/both
  death distribution plus attrition, clear%, flee% (runs with a retreat),
  early% (rooms 1-2 forced a pause/Down/potion — the per-encounter threat
  criterion), and avg days, then the **resource-pressure check**: both sites
  with the usual sim policy vs "reckless" (no pauses, no potions — the
  no-resource baseline, whose wipe rate is what ignoring your resources
  costs). Use it to re-check balance after any mechanics change.
- `scratch_bandits.py` — scenario: a *bandit hideout* (living fighters who play
  by exactly the party's rules: real DEX/STR, they spend STA, go Winded, and
  are Spent at 0). Imports the engine from `rpg.py` and mirrors the survival
  flow (`start_fight` -> `group_combat` -> `short_rest`), exposing
  `run_hideout()` for batch use. **This is the STARTER site**: base pay (a
  full clear = exactly the L1->2 XP cost), ~57% clear / ~41% wipe at rank 0
  (the 2026-07 lethality retune — a real fight now, not a tutorial), and its
  logs teach the system with no special-case enemies. The skeleton
  barrow (in `rpg.py`) is the TOUGH site you train up for. `--seed N` for
  repro, `--training N` to start the party pre-trained. Keep it in sync with
  the `rpg.py` API.
- `bench_training.py` — Phase 3 benchmark: runs the barrow and the hideout at
  combat-training ranks 0-3 and prints wipe/clear rates per rank ("does a
  level-up feel noticeable against a fixed enemy"). Run:
  `python bench_training.py`.
- `bench_weapons.py` — Phase 4 benchmark: the "suited, not ranked" test. Each
  stat frame (precise/powerful/steady/balanced) wielding each quality weapon,
  in two situations (1v1 duel vs a shortsword reference; 1v3 skeleton swarm);
  prints win% per cell. Also the doc of record for WHY the zweihander does
  not cost 2 STA per swing (sim-rejected: with Spent lethal, half the swing
  budget loses more than severity buys back). Run: `python bench_weapons.py`.
- `session.py` — **the DM driver used to actually play the game.** A thin CLI
  over `rpg.py`'s primitives that persists party/clock/purse state to
  `.session_state.pkl` (gitignored -- a save file, not source) between
  invocations, since each terminal call is a fresh process. Adds no game logic
  of its own; every subcommand is a direct call into `rpg.py`. Claude (as DM)
  drives a playthrough with this rather than one-shot `rpg.py` runs, so pacing
  decisions (when to rest, when to camp, when to press on) stay real choices
  made turn-by-turn. Subcommands: `new [--seed N]`, `status` (every track
  cur/max plus an XP/skill-point line per hero -- current STA is THE number
  the play protocol turns on, so status must show it), `levelup` (the
  skill-point spending menu: banked points, both sinks, costs, effects --
  the DM presents this on any level-up instead of paraphrasing the training
  rules), `hideout ROOM`
  (1-3, resolves one bandit-hideout room -- the STARTER site -- using that
  room's **set** roster from `scratch_bandits.HIDEOUT_ROOMS`), `barrow ROOM`
  (1-3, resolves one skeleton-barrow room -- the TOUGH site, 3x pay -- using
  that room's **set** skeleton count from `rpg.BARROW_ROOMS`, the same
  `[3, 3, 4]` layout that `run_dungeon`/`tune.py`/`bench_training.py` balance,
  so the site played is the site tuned).
  **Both sites are set encounters -- the DM never invents their foe counts.**
  `fight N [--type skeleton|bandit]` is the *off-script* escape hatch (spawns
  N foes) for improvised scenes only -- a road ambush, a one-off scrap --
  never a substitute for running a site's rooms. **A fight can PAUSE**
  (a hero crosses STA <= 2 or half HP; once each per fight, and crossing-only
  -- a condition already true at fight start never fires, so entering wounded
  or winded doesn't re-ask the question): the paused melee
  is saved, every between-fights command refuses until it's settled, and the
  player answers with `resume [--drink HERO] [--berserk HERO] [--warbreath
  HERO]` (pause actions: skip that round's attack, defend at -2; drink =
  stamina draught mid-fight, berserk = 2 HP -> +4 STA, warbreath = 2 Power ->
  +3 STA) or `retreat` (parting blows + ONE group chase roll; the barrow's
  undead never pursue past the door). A fled site room keeps its survivors
  (day-stamped record, shown in `status`): re-running the room faces them
  again -- STA refreshed, living foes healed after a day, bones still hacked.
  Then `rest`, `camp`,
  `quest GOLD XP NAME`, `buy HERO THING` (a potion OR a weapon -- weapons are
  equipped on the spot; plain tier only, quality 60g / commons 1-15g),
  `give HERO WEAPON` (DM-granted loot: wield a weapon for free -- quest
  rewards, a blade looted off a bandit), `train HERO combat|weapon` (spend a
  banked skill point on combat training or on proficiency with the wielded
  weapon -- **nothing auto-spends in session play**; that choice is the
  player's now),
  `use HERO KIND` (drink a *carried* potion between fights -- DM-called, never
  automatic; instant top-up -- healing restores HP, stamina restores STA),
  `heal HEALER TARGET` (Heal ability, between fights only -- see below).
  After a cleared encounter it prints a `Left among the dead:` loot line
  (fallen foes' weapons with stats) for the DM to offer. Every encounter
  command prints the full (debug) log and then a `--- PLAYER LOG ---` block
  -- the simplified version the DM pastes into chat as-is (see rules.md,
  "Reading the combat log"). Keep it in sync
  with the `rpg.py` API whenever primitives change shape.
- `.notes.txt` — raw brainstorming notes (unstructured, historical).

> **Registering files:** whenever you add a new file to this project (a new
> scenario, tool, or module), add it to this **Files** list with a one-line note
> on what it is and how it's run. Keep this list the index of what exists.

> **Keeping the docs current:** `rules.md` (mechanics + design spine) and
> `plan.md` (the roadmap) are living documents — keep them in sync with the
> code automatically,
> as part of the same change, not as a follow-up. When you change a mechanic,
> update `rules.md` to match; when a roadmap feature ships, **delete it from
> `plan.md`** (implemented things are documented in rules.md, not the
> roadmap); when one is deferred or re-scoped, move/update its entry. If a
> code change contradicts either
> doc, the doc is stale — fix it in the same commit. Flag any conflict you notice
> between them rather than leaving it.

## Running

```
python rpg.py            # random party + dungeon, full narrative log (one-shot)
python rpg.py --seed 7   # reproducible run
python session.py new    # start an actual DM-driven playthrough (see session.py)
python scratch_bandits.py --seed 3   # the starter site, one-shot
python tune.py           # outcome-distribution sweep over layouts
python bench_training.py # wipe/clear rates per combat-training rank
python bench_weapons.py  # weapons "suited, not ranked" matrix (duel + swarm)
```

Use `PYTHONIOENCODING=utf-8` when piping output (Windows cp1250 default). Output
is intentionally ASCII-only, so plain runs are usually fine.

## Core mechanics (see `rules.md` for the full spec)

- Three stats — **DEX** (who lands), **STR** (wound severity + soak), **STA**
  (the swing budget and second death-track; **Winded** at STA ≤ 3,
  **Spent** at 0) — plus an **HP** wound pool. The identity split:
  *DEX = swings that connect, STR = swings that count, STA = how many good
  swings you get.*
- Each round is an opposed `2d6 + DEX + training + weapon − (wound penalty)
  − (fatigue)` exchange (fatigue: 2 Winded / 6 Spent, never stacked; the
  weapon term is attack-side only — atk bonus + proficiency — except the
  staff's +1 / zweihander's −1 defense mod). Higher roll lands;
  `severity = margin + atkSTR + weapon severity mods − defSTR` maps to a
  wound tier (deflected/graze/wound/grievous/killing blow), subject to the
  **graze floors**: a win by margin ≥ `GRAZE_FLOOR_MARGIN` (3) always at
  least grazes regardless of soak (the universal floor — added 2026-07 so
  fresh high-soak heroes can bleed at all before their stamina collapses),
  and the rapier's stricter floor makes *any* landed thrust draw blood.
  **The wound penalty (= HP lost; halved, integer, for the undead — they feel
  no pain) is the death spiral, which is the whole point.**
- **Attacking costs STA** (`Entity.swing_cost`, set by the wielded weapon —
  currently 1 for everything living; the undead are **tireless** and never
  spend any); defending is free. **At 0 STA an entity
  is SPENT**: it still swings (desperation is free) but takes −6 to *all*
  rolls until the fight ends (only a pause action, below, buys STA back
  mid-fight) —
  against fresh foes that's a death
  sentence; two spent sides cancel each other's penalties and the wound
  spiral still ends the fight, so melees always resolve (draws exist only via
  the `max_rounds` safety valve). STA otherwise recovers only between fights.
  People die of exhaustion now; that is the point. (The planned 2-STA heavy
  swing was sim-rejected — see `bench_weapons.py` / rules.md "Weapons".)
- **The pause (interrupt primitive)** — with `pause_triggers=True`,
  `group_combat` stops at the end of a round in which a hero crossed
  **STA ≤ 2** or **half HP** (each trigger once per fight, and
  **crossing-only**: a condition already true at fight start is gated off
  silently — entering low was the player's informed choice at the door) and
  returns a
  `Pause`; re-call with the same `fired` set / `first_round=round+1` to
  resume. Options at the pause: fight on; per-hero **pause actions** (cost
  that round's attack, defend at −2): drink a stamina draught mid-fight
  (+4 STA — even un-Spends a fighter at 0), **Berserk**
  (2 HP → +4 STA, the spiral deepens), **War-Breath** (2 Power → +3 STA); or
  `attempt_retreat` — parting blows from every foe fit to swing, then ONE
  group chase contest (2d6 + STA-weighted avg DEX, fleeing side
  +`FLEE_BONUS`; `pursues=False` foes — the barrow's skeletons — never
  chase). Fled rooms persist via `refresh_foes_after_retreat` (STA refills,
  living heal over a day, bones stay hacked). The batch sims answer pauses
  with `sim_pause_policy` (one return trip per fled room), so tune/bench
  describe the same game; see rules.md "The pause".
- **Weapons (Phase 4 first slice)** — one wielded weapon per fighter, no
  inventory. Quality four: rapier (+2 atk, −1 sev, graze floor), katana
  (+1/+1), zweihander (+1/+3, −1 defense), wooden staff (+1 parry, +1 Heal,
  −1 sev). Commons in three lines: crude 0/−1 (durability 1), soldier's arms
  0/0 (the old implicit baseline), heavy arms 0/+1. **Breakage:** on a parry
  or Clash the lower-durability weapon can shatter (0.25% × gap² per contact;
  broken = −2 atk/−2 sev until re-armed). Tiers plain/masterwork/legendary —
  only plain is shoppable (quality 60 g). Starting roll (heroes & bandits):
  50% crude / 45% soldier / 5% heavy; healers 50% wooden staff. Skeletons
  swing durability-1 rusted blades that snap on good steel.
- `group_combat` resolves a melee **sequentially with a round-start snapshot**
  — party in list order first (PC acts first), then foes. Everyone alive at
  round start gets their one swing, even if felled before their turn comes
  (**the dying swing**: the blows cross in the air; it rolls with its
  round-start wound penalty and costs no STA). Targeting stays live — every
  attacker picks a target *living at the moment it acts*, so no swing is
  wasted on a corpse. A foe dropped by First Blood (pre-round) gets no dying
  swing. Heroes focus-fire the weakest foe; foes target at random.
- **The combat log has two simultaneous levels** (`CombatLog`; see `rules.md`,
  "Reading the combat log"). The **full log** (the list itself — DM/debug):
  every exchange prints an interpretive headline (Clash / Lull / parried /
  edges past / outmaneuvers / overwhelms, wound phrases with the target's
  `-n to rolls` spiral penalty) with the raw numbers indented beneath it (the
  actual 2d6, every modifier and its source, the full severity arithmetic;
  pressure lines read `Name: total (parts)`), plus `!!` Winded/Spent crossing
  lines and a per-round `stamina:` readout (`*` Winded, `!!` Spent, tireless
  summarized). The **player log** (`CombatLog.player`, printed by session.py
  as a `--- PLAYER LOG ---` block): headlines only, HP loss folded in
  (`a solid wound (-2 HP)! [Skeleton 1: 3/5 HP]`), simplified `!!` lines, no
  dice math, no stamina readout — built to be pasted into chat as-is.
  Combat lines use short names ("Inga", never "Inga the precise" — the
  epithet is stat-sheet flavor only). Engine code emits via the
  `_debug`/`_play` helpers so plain `list[str]` logs still work (they get
  the full level).

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
- **STA is the second death-track**: attacks spend it, it carries across rooms,
  and hitting 0 mid-fight leaves you Spent (see Core mechanics), which against
  fresh enemies usually kills. It recovers **between fights** (mid-fight, only
  a pause action buys any back — see Core mechanics), a
  **sawtooth trending down**:
  `STA_RECOVERY_AFTER_FIGHT` (1) when a fight ends, `STA_RECOVERY_BETWEEN_ROOMS`
  (3) per short rest (from 0, fight-end +1 plus a short rest = 4 — *just* clears
  Winded), and only a **long rest recharges STA fully** (overnight). Most
  deaths trace to a fight costing more STA than it looked like it would —
  a player rarely *chooses* to enter a room low; the danger is misjudging
  what the room will cost.
- **Time economy (`Clock`):** a `day` counter plus a per-day budget of
  `SHORT_RESTS_PER_DAY` (**1** — cut from 2 in the 2026-07 lethality retune)
  short-rest slots. `short_rest(party, clock, log)` (~an
  hour or two of narrative time) spends the slot for a small catch-breath
  (+3 STA, +1 HP, +1 Power — `POWER_RECOVERY_BETWEEN_ROOMS`)
  and refuses once it's gone. `long_rest(party, clock, log)` makes
  camp: full STA **and Power**, the weekly HP tick, Down heroes back up,
  `day += 1`, the slot
  refills. **There is no auto-night** — `long_rest` is a function Claude calls on
  purpose; nothing forces the day to end (see "The feel we're going for").
- **Items** are a carried stock that **never auto-refills**: heroes start with
  **two random potions** (`random_kit`) and restock only via drops or
  `buy_potion`. Only **healing and stamina** circulate
  (`STOCKED_POTION_KINDS`); the **power potion is retired** from creation,
  drops, and shops (2026-07: Power is never the bottleneck — the schema keeps
  the kind so old saves can still drink one). **Using** a potion is a
  DM-called, between-fights action too -- `use_potion(hero, kind, log)`, same
  shape as `buy_potion` / `use_heal`, never automatic. Every potion takes
  effect **instantly on drink**: *healing* restores `HEALING_POTION_RESTORE`
  (5) HP (and stands a Down hero back up), *stamina* restores STA.
  `start_fight` is revive-only and `short_rest` is a plain catch-breath --
  neither drinks anything. The one-shot / sim paths (`run_dungeon`,
  `scratch_bandits`) model a sensible party via `auto_use_potions_on_rest`
  (heal when badly hurt, stamina when winded), so `tune.py` /
  `bench_training.py` still model a party that uses its consumables.
- A character only truly **dies** on an unsaved killing blow; `outcome()` counts
  only the slain.
- **Total party knockout = defeat.** `party_wiped()` (in `rpg.py`, shared by both
  scenarios) checks after every fight: if no hero is left standing, the Down are
  finished off (marked Dead) and the run stops — a game over. So a double-Down is
  no longer a recoverable state; it ends the run.

## Progression & economy (Phases 3 + 4 — see `rules.md` add-on)

- **XP:** every not-dead hero earns the full award — 15/encounter + 55/quest at
  the bandit hideout (the starter site), 3x at the skeleton barrow (45/165, the
  tough site). Level `L -> L+1` costs `100 * L` (`xp_to_next`), so the *first
  hideout clear is exactly a level-up*.
  `award_xp` handles level-ups and banks skill points (1/level).
- **Two skill sinks now — points are a real choice.** Combat training: +1 to
  all pressure rolls per rank, rank *n* costs *n* points, cap 5. Weapon
  proficiency (`train_proficiency`): +1 attack pressure AND +1 severity with the
  wielded weapon type per rank, rank *n* costs *n*, cap 3 — narrower, so
  stronger per rank; switching weapons drops the layer (the commitment cost).
  **Session play banks points** (`train HERO combat|weapon`); only the batch
  sims auto-spend on training (`train_combat`, greedy) so tune/bench stay
  comparable.
- **Gold** lives in a shared `Purse`. Income: quest rewards (15 g hideout / 45 g
  barrow) + per-encounter drops (20% -> 5 g, 10% -> a random potion to a random
  hero, `roll_loot`). Sinks: `buy_potion(hero, purse, kind, log)` at
  `POTION_PRICE = 10`, and `buy_weapon(hero, purse, name, log)` — plain
  quality steel at 60 g is the first real saving goal (sim-measured after the
  2026-07 retune: katana + zweihander lift a fresh party's barrow clear
  ~2% -> ~11% — a 5x jump but still suicide alone; it's the *combination*
  that unlocks the barrow: training 2 + steel clears ~66%, training 3 + steel
  ~89%). Both are **DM-called between-adventures purchases**. Nothing
  refills automatically.

## The current prototype scenario

> This layout is played the same everywhere: session play (`session.py barrow
> ROOM`) and the one-shot `rpg.py`/`tune.py` run both draw from
> `rpg.BARROW_ROOMS` / `DUNGEON_ROOMS` -- **the sites are set encounters,
> balanced during development, never improvised at the table** (see the
> `session.py` bullet above; `fight N` exists only for off-script scenes).

- **Party:** two randomly generated humans (`make_human`): DEX/STR
  `randint(3, 6)`, STA `randint(5, 8)` (its own higher range — STA is the swing
  budget / second death-track, so its floor matters like HP's floor), HP
  `randint(8, 12)`, Power `randint(3, 6)`, a random ability (`heal` / `bulwark`
  / `first_blood`), two random potions, a rolled starting weapon (50% crude /
  45% soldier's arms / 5% heavy; heal-ability heroes 50% wooden staff), and an
  epithet from the highest stat (precise/powerful/steady; STA normalized down
  2 for the comparison).
- **The starter site:** the bandit hideout (`scratch_bandits.py`,
  `HIDEOUT_ROOMS`: 1/2/2 living bandits). Same rules as the party — its logs
  teach the system; bandits arm from the same common-weapon table but run a
  point of DEX hot (cutthroat/archer DEX 5, bruiser 4 — the retune's "who
  hits is DEX" lever). Base pay; first clear = level 2, and a real fight now
  (~57% clear / ~41% wipe fresh at rank 0).
- **The tough site:** rooms of skeletons, `BARROW_ROOMS` (named rooms, counts
  `DUNGEON_ROOMS = [3, 3, 4]`; one "day"; 3x pay). HP,
  STA, and the resource stock all carry across rooms (only minimal catch-breaths);
  wounds persist for the run. Clearing all rooms completes the quest
  (gold + XP lump).
- **Skeletons:** brittle, weak individual hitters (DEX 4 / STR 2 / HP 5), no
  Power/kit, but **undead**: half wound penalty (`hp_lost // 2` — no pain, so
  chip damage and First Blood's spiral bite less here) and **tireless** (never
  spend STA, never Winded/Spent) — the threat is *numbers* pressing a party
  whose stamina is a death-track: they don't have to beat you, just outlast
  you. They swing durability-1 **rusted blades** that occasionally snap on
  good steel (~10% of rooms vs a quality-armed party — the barrow visibly
  eases as gear improves). The exception enemies, met second on purpose
  (living foes first).

## Balance / tuning

`tune.py` reports attrition alongside the death split, plus clear rate, gold,
early pressure (rooms 1-2 forcing a pause/Down/potion), and the
resource-pressure check (sim policy vs the reckless no-resource baseline).

**A tuning principle (2026-07): the sims understate the player.** The batch
policies rest on a fixed schedule, drink potions on crude thresholds, and
answer pauses with one-number rules (`sim_pause_policy`); a real player paces
rests, reads the STA math before every door, and times retreats. So sim clear
rates run *below* played clear rates, and
harsher sim numbers than "feels fair" are acceptable — tune for the felt
game, and let rooms 1-2 of a site threaten in the sims, not just the last one.

**The lethality retune (2026-07, second pass): danger lives in the encounter,
not the grind.** The felt game had gone easy — the player can camp after any
encounter, so a site that only threatens via attrition doesn't threaten at
all. Targets set by the designer: the starter hideout at rank 0 clears ~55%
with someone hitting the floor in about half the runs, and **not using
resources should mostly mean death**. The levers pulled: enemy DEX +1 across
the board (skeletons 3 -> 4, cutthroat/archer 4 -> 5, bruiser 3 -> 4 — who
hits is DEX's job), and `SHORT_RESTS_PER_DAY` 2 -> 1. Measured after (10-20k
runs, rank 0): **hideout** clear ~57% / wipe ~41% / Down in ~39% of runs with
the full sim policy, vs **68% wipe reckless** (no pauses, no potions) — the
resources are worth ~28 points of survival; **barrow** `[3, 3, 4]` clear
~2% / wipe ~96%, early pressure ~94% (rooms 1-2 force a resource) — a fresh
party simply should not be there. Per `bench_training.py` (5k/rank): barrow
clears **2% -> 12% -> 37% -> 65%** over ranks 0-3, hideout
**57% -> 81% -> 95% -> 99%**. Gear is the other axis: katana + zweihander
alone lift the fresh barrow to only ~**11%**; the arc is the *combination* —
**training 2 + quality steel clears ~66%** (Down ~32%), training 3 + steel
~89%. The intended arc sharpened: fight the hideout at rank 0 (and expect
retreats and downs), level up *and* buy steel over ~2-3 clears, take the
barrow at rank 2+ armed. Most deaths still trace to STA misjudgment;
skeleton DEX 4 means the bones also cut you while they outlast you.
If the opening needs softening, `HIDEOUT_ROOMS` is the first lever; for the
barrow, `DUNGEON_ROOMS`; enemy DEX is the sharpest knife — a single point
moves clear rates by tens of percent.
(Side effect worth knowing: `bench_weapons.py`'s 1v3-skeleton swarm column
collapsed to low single digits for every weapon — a lone fighter vs three
DEX-4 tireless skeletons is near-hopeless. The column still ranks the
zweihander first, but its discriminating power is thin; the duel column
does the work now.)

Difficulty levers, easiest first: edit `DUNGEON_ROOMS` / `HIDEOUT_ROOMS`, then
survival tunables (`SAVE_COST`, `HEALING_POTION_RESTORE`, `STA_ATTACK_COST`,
`SPENT_PENALTY`, `STA_RECOVERY_AFTER_FIGHT`, `STA_RECOVERY_BETWEEN_ROOMS`,
`SHORT_RESTS_PER_DAY`, `STARTING_POTIONS`), then the pause/retreat layer
(`PAUSE_STA_TRIGGER`, `PAUSE_HP_FRACTION`, `PAUSE_ACTION_DEF_PENALTY`,
`FLEE_BONUS`, `BERSERK_HP_COST`/`BERSERK_STA_GAIN`,
`WAR_BREATH_POWER_COST`/`WAR_BREATH_STA_GAIN`), then weapons (the `WEAPONS`
catalog profiles, `BREAK_CHANCE_PER_GAP_SQ`, the starting-weapon chances,
`PROFICIENCY_MAX`), then economy/progression (`POTION_PRICE`, weapon values,
drop chances, quest rewards, `XP_LEVEL_STEP`, training cap), then
skeleton/bandit stats, then the hero roll ranges (`HERO_STAT_RANGE`,
`HERO_STA_RANGE`, `HERO_HP_RANGE`, `HERO_POWER_RANGE`).
**Always re-run `tune.py`, `bench_training.py`, and `bench_weapons.py` after
touching any of these** — small changes swing lethality, the attrition curve,
and the weapon matchup matrix.

## Conventions

- Stdlib only; keep `rpg.py` self-contained and importable (`tune.py` imports it).
- Keep narrative/log output ASCII (no em-dashes or special glyphs) for Windows.
- `Entity` is `@dataclass(eq=False)` so instances are identity-hashable (used in
  combat sets) — don't switch it back to value equality.
- Two layers, kept separate: thin mechanics in code, rich flavor added by the DM
  over the log. Don't bake prose into the engine beyond terse event lines.
- **Zero backwards compatibility.** This is an early prototype: never spend
  effort keeping saves or schemas loadable across changes. Rename and
  restructure freely; any `.session_state.pkl` is disposable — when a change
  breaks it, delete it and start a fresh game rather than writing migrations
  or compat shims.

## Not yet built (the point of the design)

The between-fights layer is now substantially player choice: gold/XP flow,
skill points are a real allocation (combat training vs weapon proficiency —
nothing auto-spends in session play), `buy_potion` and `buy_weapon` make
shopping real decisions, and which site to run (starter hideout vs 3x-paying
barrow) is the first "pick your fights" choice. The mid-fight layer exists
too now: the pause (drink / Berserk / War-Breath / retreat & chase, with
fled rooms persisting). **The next big feature is the encounter & quest
system** (see `plan.md`): player and encounter levels, the whole power
curve, a monster/opponent catalog spanning it, and DM tools to build foes,
encounters, and dungeons from a level number plus the narrative — the two
hand-built sites become instances of a general system. After that: magic/
INT, armor, guns + ammo, named weapon instances, party composition. See
plan.md for the full roadmap and the parked-ideas list.
