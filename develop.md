# RPG2 — Development Guide

The dev guide for the combat-sim prototype: workflow, the file index, the
dev map, conventions, tuning levers, and the current measured balance
numbers. `CLAUDE.md` is only the auto-loaded dispatcher; THIS file is the
real development entry point — read it before changing the game.

> **PLAYING, NOT DEVELOPING? Read `dm.md` instead** — it is the entire
> instruction set for running a game, narration style included. Nothing in
> this file (especially the be-thorough dev-communication register) applies
> at the table.

## The feel we're going for

A **mechanics-centered RPG** with the freedom of a tabletop game. Combat is
*autocombat* — it runs to completion in one call so play stays fast in chat
instead of grinding through every roll by hand — but the world around it stays
open-ended and player-driven. The engine owns the numbers; the DM owns the
fiction.

**How play is driven:** the game is *two halves working together*.
- **The scripts (`rpg.py`, `sites.py`, `quests.py`, `people.py`)** are a
  library of mechanics primitives and content — `start_fight`,
  `group_combat`, `short_rest`, `long_rest`, `party_wiped`, the foe
  catalog, the set sites, the quest generator and its world, the
  character generator and its races/traits.
- **Claude (as DM)** calls those primitives *on purpose*, in whatever order the
  story wants, and narrates over the result. There is deliberately **no
  autopilot** for pacing: e.g. nothing forces the day to end — Claude decides
  when the party makes camp and calls `long_rest`. This preserves TTRPG-style
  freedom. Some of these calls can be automated more later; for now they're
  manual on purpose.
- **Part of the game lives in instructions to Claude**, not in code. The engine
  won't ever encode every situation; judgement calls, improvised scenes, and
  when-to-call-which-function all live in `dm.md` and the DM's reasoning. When
  we settle a rule of play that isn't a pure number, write it into dm.md
  rather than forcing it into the engine.

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
  up: the levelling framework — points, abilities, moves, alchemy; the
  2026-07-16 spec lives there), plus parked ideas and open questions.
- `benchlog.md` — **the dated tuning history**: the full report of every
  measured bench-suite run, oldest first. Append a dated entry after every
  re-measurement; the "Balance / tuning" section below keeps only the
  current summary.
- `CLAUDE.md` — **the auto-loaded dispatcher**: the play/dev mode fork and
  the doc pointers, nothing else. It is injected into EVERY session,
  including play — keep it short and register-neutral; dev content belongs
  in this file, play content in dm.md.
- `rpg.py` — **the engine.** Combat (`group_combat` + the pause/retreat
  layer), weapons and breakage, the survival tracks and rests, progression,
  economy, random party generation, the Magic & Mind layer
  (2026-07-15: the MIND stat, the nine-spell catalog with ranks, the
  casting check, the openers, spellbooks — rules.md's
  Magic & Mind add-on), ranged combat & the field (2026-07-16: per-entity
  advances, the movement phase, shots on the exchange, reload cadence,
  ammo & scavenging, the seven ranged cards, conspicuousness — rules.md's
  Ranged Combat add-on), and the batch-sim policies
  (`sim_fight` / `sim_pause_policy`). Stdlib-only and self-contained;
  everything else imports it. All tunable constants sit at the top.
- `sites.py` — **the catalog & the set sites.** The foe catalog (`FOES`,
  `make_foe` — six monster families plus the humanoid ladder and, since
  2026-07-14, the three caster rows (hexer/pyromancer/magus), every row
  bench-calibrated; `make_foe(display=...)` is the reskin hook), the two
  set sites (`SITES`: the bandit **hideout** = the starter, level 1; the
  skeleton **barrow** = the tough site, level 3; room layouts in
  `HIDEOUT_ROOMS` / `BARROW_ROOMS`; pay derives from `Site.level` via
  rpg.py's site formulas), and `run_site`, the one site loop the one-shot
  run and the batch sims share. **Both sites are set encounters — the DM
  never invents their rosters — and since 2026-07-13 they are DEV/TEST
  calibration content only, no longer part of a played campaign** (the
  generated board covers the band; the benches still run them).
  One-shot: `python sites.py [--site
  hideout] [--seed N] [--training N]`.
- `quests.py` — **the quest & encounter generator** (rules.md, the Quest
  System add-on): the threat math (all constants at the top, calibrated by
  `bench_quests.py`), the room/site/quest builders, per-race quest
  templates with reskin tables (since 2026-07-12 each also authors a
  `giver` role and an `epilogue` line), and seeded worldgen with asserted
  XP coverage to the level cap — which since 2026-07-12 also attaches a
  generated giver face to every quest (`attach_giver`) and casts each
  land's three persistent notables (`RULER_TITLES` / `SAGE_ROLES` /
  `WILDCARD_ROLES`, `world["npcs"]`). Since 2026-07-14 also the
  cross-land deliveries (`DELIVERY_TEMPLATES`, `build_delivery_quest`,
  `_post_delivery` — the site-less courier kind, two per world; rules.md's
  Quest System add-on, "Cross-land deliveries"). `python quests.py
  [--seed N] [--demo]` prints a generated world's board and cast.
- `story.py` — **the authored story layer: the conquest questline**
  (2026-07-12, rules.md's Story Layer & Conquest add-on). Four aggressor
  variants (elf/goblin/human/orc — content dicts at the top: creeds,
  reskins, waves, heralds, epilogues), the named faces (conqueror + two
  lieutenants as display names over budget-honest rosters), waves pinned
  at L2/5/8/10 built by quests.py's own threat math, wave gating
  (previous wave done + party at level + party at a settlement since
  2026-07-13; the aggressor roll excludes the PC's race), the
  wave-3 scripted fall with
  occupation, and the war readouts. State lives in the session save
  (`story` key); the sims never import it. `python story.py [--seed N]
  [--aggressor R]` dumps one rolled conquest, all waves force-posted.
- `people.py` — **the character layer** (2026-07-11, rules.md's Party,
  Charisma & Satisfaction add-on): the five races' stat modifiers
  (floor-raise `RACE_MODS`; since 2026-07-13 also the goblin STR ceiling
  drop `RACE_MODS_CEIL` and the race trait substitutions
  `RACE_TRAIT_SUBS`), the 25+25 per-race name pools, the trait
  tables (1 behavior + 2 presentation categories per character; the
  mechanical few annotated in `TRAIT_NOTES`; looks pool widened
  2026-07-13), `make_character` (any
  level, via rpg.develop_hero; `no_family=True` is the PC switch),
  `make_pair` (bonded recruit pairs), the
  candidate sheets, and the downtime-matching rules; since 2026-07-12
  also `make_npc` / `npc_line` (the TARGETED generator: the caller fixes
  race/role/sex/age, the dice roll name + personality — dict NPCs, no
  stat blocks, `NPC_MIN_AGE` floors anyone with a job title). Content
  only — the satisfaction/CHA mechanics it hangs on live in rpg.py; the
  sims import it only through worldgen's giver/cast generation.
  `python people.py [--seed N] [--level L]` prints a sample
  (the DM's eyeball check).
- `session.py` — **the DM driver used to actually play.** A thin CLI over
  rpg.py/sites.py/quests.py that keeps party/clock/purse/world state in
  **`save.json`** (plain JSON: committable, so a playthrough can travel
  with the repo, and hand-editable — the DM's override surface, see dm.md)
  between invocations, so pacing decisions stay real turn-by-turn choices.
  Adds no game logic of its own. `python session.py --help` lists every
  subcommand with its rules; dm.md says which decisions belong to the
  player. Quest play: `board` (LOCAL by default since 2026-07-09) /
  `show QID` / `take QID` / `room`, plus `forge` (the DM quest creator).
  World play (2026-07-09): `map` / `travel` / `explore` / `hunt` /
  `engage` — location state, local boards, road encounters, the momentum
  streak; since 2026-07-10 also `tavern` (the paid settlement night with
  the one-day HP/STA overcharge), wilderness `camp` night encounters, the
  ordinary-encounter spotted valve, and the hunt ambush. Since 2026-07-11
  also the party layer: `recruit` /
  `hire` (candidates, CHA-capped), `dismiss` (voluntary departure,
  the quitter's head-split terms), `downtime` (the morale day),
  `buy HERO meds`, and the satisfaction bookkeeping (post-fight morale
  pass, nightly meds drain, settlement departures with the purse
  head-split) — plus the same day's play-feedback batch: `play_orders`
  (the one-pause-per-encounter dispatch over the engine's standing-orders
  hook), `camp N` / `camp --heal` (multi-night camping, cut short by a
  wilds visitor), and the board's land-wide rumor section.
  Since 2026-07-12 also the story layer's play surface: `board` is
  the DM inventory (rows carry givers; in play quests come from their
  GIVERS via the one-message ask-around funnel, dm.md), quest turn-ins
  print the day-stamped EPILOGUE + giver prompt, `chatter` (the party-
  flavor seed: unseeded rng, no state change), day headers on board/map,
  local notables on the board, and the war plumbing (`maybe_post_wave`,
  `occupied_here` gates on
  board/take/tavern/downtime, the boss-name spawn in `room`, `story` in
  the save). Reworked 2026-07-13 (the streamlining batch): `new`
  GENERATES the PC (no `pick`; min capacity 1, no family quirks, the
  long-time companion, the OPENING HOOK at the lowest-level-quest
  settlement, aggressor excludes the PC race), `recruit` rolls candidates
  ON REQUEST (once per settlement/day; the tavern stopped popping them),
  companions AUTOLEVEL after fights/hire (`rpg.autospend_points`) while
  the PC's level-up auto-prints the `levelup` menu, `maybe_post_wave` is
  settlement-gated (no war news mid-wilds), a dead companion's quality
  weapon stays with the party, `give --as` reskins weapons, ALL output
  (and `party.txt`) is hard-wrapped at `WRAP_WIDTH` = 40 for the
  designer's phone, and **`party.txt`** is rewritten on every save but
  committed only by **`sheet`** — the end-of-every-DM-message command
  (one commit per message; best-effort git, never fatal).
  Encounter commands print the full log then the
  `--- PLAYER LOG ---` block the DM pastes into chat -- which since
  2026-07-14 ends with the party tally (`tally_lines`: tracks/kit/purse,
  rooms-left count, next streak multiplier), the standard
  between-encounters numbers display so the DM's prose never has to
  carry the numbers (dm.md, Narration style).
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
- `bench_ranged.py` — the ranged matchup matrix (2026-07-16): each ranged
  card on its suited frame vs the melee reference at fields 0/2/3, plus
  the played escort shape (shooter + katana line vs a wolf pack). The doc
  of record for reach-is-an-edge-not-a-win-button, and for WHY the
  severity flats run higher than melee mods (a shot's flat replaces STR)
  and why chargers commit before skirmishers in the movement phase.
  `python bench_ranged.py [--trials N]`.
- `bench_bestiary.py` — the bestiary calibration: each catalog row's
  reference encounter (`ref_pack` of it) vs reference duos at the annotated
  level and two levels either side; win/fled/wipe/stall/down rates. The
  reference party grows its pools through the engine curve
  (`rpg.grow_pools`) and buys training/proficiency monotonically.
  `python bench_bestiary.py [--trials N] [--kind wolf]`.
- `bench_party.py` — the party-size sweep behind rules.md's "Balanced for
  two": both sites at rank 0 for party sizes 1-4, wipe/down/clear per size.
  Re-run after touching the press or the melee loop.
  `python bench_party.py [--trials N]`.
- `bench_quests.py` — the quest-generator calibration AND the career sim:
  (1) generated at-level rooms vs the reference duo across levels 1-20,
  (2) generated whole sites likewise, (3) full careers — fresh duo, fresh
  world, play the board to the level cap or the grave; reports the
  reached-level distribution, pace (days/quests), and board coverage.
  **Re-run after touching quests.py's threat math, the bestiary, or the
  reward formulas.** `python bench_quests.py [--trials N] [--careers N]
  [--part enc|site|career]`.
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
> dev workflow, the file index, tuning levers, and the current balance
> summary (the dated measurement history goes to `benchlog.md`)** — don't
> re-explain a mechanic here that rules.md already covers.

## Running

```
python session.py new    # start an actual DM-driven playthrough (see dm.md)
python quests.py --seed 1 --demo   # print a generated world's quest board
python sites.py          # one-shot barrow run, full narrative log
python sites.py --site hideout --seed 3   # one-shot starter site, reproducible
python rpg.py            # same one-shot (delegates to sites.py)
python tune.py           # outcome-distribution sweep + resource-pressure check
python bench_training.py # wipe/clear rates per combat-training rank
python bench_weapons.py  # weapons "suited, not ranked" matrix (duel + swarm)
python bench_ranged.py   # ranged cards by opening field + the escort shape
python bench_bestiary.py # bestiary level-annotation calibration (per row +-2)
python bench_party.py    # party-size sweep (the "Balanced for two" check)
python bench_quests.py   # generated rooms/sites honesty + the career sim
```

Use `PYTHONIOENCODING=utf-8` when piping output (Windows cp1250 default). Output
is intentionally ASCII-only, so plain runs are usually fine.

## The dev map (where mechanics live in the code)

The one-screen index for finding the thing you need to change. What each
mechanic *does* and *why* is rules.md's job.

- **Tunable constants** — all at the top of `rpg.py`, grouped and commented:
  fatigue (`WINDED_STA`, `SPENT_PENALTY`, `STA_ATTACK_COST`), survival
  (`SAVE_COST`, `HEAL_COST`, `FIRST_BLOOD_*`, potion restores, the
  `*_RECOVERY_*` family, `REVIVE_HP`, `SHORT_RESTS_PER_DAY`, and the
  self-restocking kit `KIT_HEALING` / `KIT_STAMINA` — 2026-07-11, every
  long rest tops each hero back up to the kit line), the pause layer
  (`PAUSE_STA_TRIGGER`, `PAUSE_HP_FRACTION`, `PAUSE_ACTION_DEF_PENALTY`,
  `FLEE_BONUS`, `BERSERK_*`, `WAR_BREATH_*`; since 2026-07-11 the
  standing-orders hook — `group_combat(standing_orders=...)`,
  `rpg.standing_order` the default ladder, `fight_winding_down` the
  don't-waste-a-potion check, "heal" the fourth pause action), the graze
  floor
  (`GRAZE_FLOOR_MARGIN`), wound tiers (`TIER_HP`), progression
  (`XP_LEVEL_STEP`, `LEVEL_CAP`, `POOL_GROWTH_LEVELS`, `TRAINING_MAX`,
  `PROFICIENCY_MAX`), economy (`POTION_PRICE`, drop chances, and the
  level-pay formulas `site_xp_total` / `site_encounter_xp` /
  `site_clear_xp` / `site_gold` with their `SITE_XP_PER_LEVEL` /
  `ENCOUNTER_XP_SHARE` / `GOLD_PER_SITE_LEVEL` knobs), weapons (the
  `WEAPONS` catalog, `BREAK_CHANCE_PER_GAP_SQ`, starting-weapon chances),
  hero stat generation (`HERO_*_RANGE` + `HERO_STAT_BUDGET` — since
  2026-07-13 a fixed surplus budget dealt by a shuffled priority order,
  not independent rolls; 11 since 2026-07-15, when MIND joined the
  budget) and the hero spiral gear (`HERO_PAIN`
  — trained fighters, both sides, take `hp_lost // 2` as the wound
  penalty since 2026-07-09), the momentum streak (`STREAK_STEP` +
  `streak_multiplier` — consecutive same-site encounters without a camp
  pay rising XP; a full one-go run collects exactly the encounter share;
  2.0 since 2026-07-10: x1/x3/x5 across three rooms), the magic layer
  (2026-07-15: the `SPELLS` catalog, `CAST_SEVERITY` / `CAST_POWER_COST`,
  the casting-check knobs `CAST_DC_BASE` / `CAST_DC_PER_RANK`,
  `AMBUSH_MARGIN`, the opener costs, `SPELLBOOK_PRICE`,
  `ICE_DEX_DEBUFF` / `FREEZE_DEX_DEBUFF`, `WIZARD_STAFF_CHANCE`; the
  delivery pay knobs
  `DELIVERY_GOLD_PER_DAY` / `DELIVERY_XP_PER_DAY` /
  `DELIVERIES_PER_WORLD` sit at the top of quests.py), the tavern night
  (`TAVERN_COST_PER_HERO`, `TAVERN_OVERCHARGE` — the one-day above-max
  HP/STA edge; `recover()` is the clamp that makes the excess spent-only),
  and the party-size counterweights
  (`CROWD_CAP` — the press; `XP_PARTY_BASELINE` — awards quoted at the
  duo, paid `x 2 / party size`), the CHA layer (`HERO_CHA_RANGE`,
  `party_capacity` = CHA−3 clamped 0..3, `CHA_GOLD_BONUS_PER_POINT` /
  `_CAP` — gold only, never XP), and companion satisfaction (the
  `SATISFACTION_*` bounds and `SAT_*` event deltas, plus
  `MEDS_INTERVAL_DAYS` / `MEDS_PRICE`). The character layer's content
  knobs (racial `RACE_MODS`, `PAIR_CHANCE`, `ARMORED_DEF_BONUS`,
  `TRAIT_GOLD`, `INTEREST_PLACES`) sit at the top of `people.py`. The
  quest generator's own knobs sit at the top of `quests.py` (`THREAT_BASE`, `ROOM_SHARES`, `DUP_COST`,
  `PACK_CAP`, `BOSS_ALLOWANCE`, `WORLD_XP_MARGIN`, settlement bands), and
  so do the navigation layer's (`TRAVEL_DAYS_*`, `TRAVEL_ENCOUNTER_CHANCE`,
  `EXPLORE_*`, `WILD_LEVEL_DECAY`, `SPOTTED_MARGIN`, `AMBUSH_CHANCE`,
  `WILD_SPOTTED_CHANCE`, `HUNT_LEVEL_REACH`, `HUNT_AMBUSH_CHANCE`,
  `CAMP_ENCOUNTER_CHANCE`).
- **The exchange** — `Entity.pressure` (the opposed roll with its full
  breakdown) and `_attack` (severity, graze floors, saves, the two-level log
  lines). `_check_weapon_break` on parries and Clashes.
- **The melee** — `group_combat`: round-start actor snapshot (the dying
  swing), live targeting under the press (`_pick_target` + per-round
  `engaged` counts vs each defender's `crowd_cap`; a crowded-out attacker
  circles free), sweeps (`Entity.sweep` targets off ONE attacker roll,
  optional `sweep_cost_power` fuel), end-of-round regeneration
  (`Entity.regen`), STA spend, Winded/Spent crossings, pause triggers.
  Returns a `Pause` mid-fight when `pause_triggers=True`; resume by calling
  again with the same `fired` set (keyed by `(kind, hero)` — each trigger
  once per hero per fight, crossing-only), `first_round=round+1`, and
  per-hero `actions`. Since 2026-07-11 the `standing_orders` callback
  decides each crossing (interrupt / auto-act next round / fight on;
  None = every crossing pauses, the sims' path — `session.play_orders` is
  the played dispatch: first wounds crossing pauses, everything else runs
  `rpg.standing_order`; auto crossings sharing a round with an interrupt
  are re-armed, not silently spent). Fate's bargain (2026-07-10) lives
  here too: the fall
  handler commutes a protagonist's death to a Down (`Entity.protagonist` /
  `fate_debt`; session marks `party[0]`), `_settle_fate_debt` collects the
  companion's life at victory.
- **Retreat** — `attempt_retreat` (parting blows — softened one wound tier
  since 2026-07-10 (`_attack(soften=True)`): the door maims, never kills
  outright — + ONE group chase roll; `pursues=False` foes never chase; a
  clean escape waives any fate debt), `refresh_foes_after_retreat`
  (fled-room persistence).
- **Between fights** — `short_rest` / `long_rest` (the `Clock`), `use_potion`,
  `use_heal`, `buy_potion` / `buy_weapon` (the `Purse`), `equip_weapon`,
  `award_xp` / `award_quest` / `roll_loot` (`award_quest` also applies the
  PC's `cha_gold_bonus` and the +1 satisfaction lump), `train_combat_once` /
  `train_proficiency` (session play banks points; only the sims auto-spend
  via `train_combat`), `party_wiped`, `start_fight` (revive-only).
- **The party layer** (2026-07-11) — `rpg.py`: the satisfaction helpers
  (`adjust_satisfaction` with the cowardly/brave injury scaling,
  `satisfaction_after_fight`, `wants_to_leave` / `leave_threshold`,
  `has_trait`), `party_capacity`, `develop_hero` (the leveled-character
  factory, mirroring bench_bestiary's reference doctrine), `Entity`'s
  person fields (`cha`, `race`, `sex`, `age`, `traits`, `satisfaction`,
  `bond`/`bond_kind`, `last_dose_day`, `def_bonus`, `nickname`; the
  `epithet` field is GONE). `people.py`: generation + sheets (see Files).
  `session.py`: `roll_recruits` / `cmd_hire` (per-head capacity check;
  candidates rolled on request in `cmd_recruit` since 2026-07-13),
  `cmd_dismiss` (voluntary departure, the quitter's head-split terms, bond
  partner walks), the generated PC + long-time companion in `cmd_new`,
  `process_departures` (burials + the purse head-split, run at settlement
  arrivals and tavern/downtime nights), `night_upkeep` (meds drain),
  `cmd_downtime`, and the `dead_before` plumbing through `pending` so the
  post-fight morale pass knows who died in *this* fight.
- **The log** — `CombatLog` (full + `.player` levels; `_debug` / `_play`
  emit helpers so plain lists still work).
- **Content** — `sites.py`: `FOES` (the bestiary: 25 stat blocks — six
  monster families + the humanoid ladder + the three casters — each row
  with a bench-calibrated
  `level` annotation, `ref_pack`, and for the drilled soldiery a `training`
  rank), `NATURAL_WEAPONS` (fangs/claws — never break, never loot),
  `make_foe` (+ the `display` reskin hook), `SITES`, `HIDEOUT_ROOMS` /
  `BARROW_ROOMS`, `run_site` (the sim loop), `roster_lines`,
  `WEAPON_INDEX` (name -> Weapon, the save file's reference table).
- **Generation** — `quests.py`: `threat_value` / `build_room` /
  `build_site_rooms` (the threat math), `TEMPLATES` / `EPIC_TEMPLATES`
  (the per-race quest tables + reskins), `build_quest` / `forge_quest`,
  `generate_world` (+ the coverage top-up), `quest_to_sites` (generated
  quest -> `Site` instances for the sims), the board readout helpers.
- **The story layer** (2026-07-12) — `quests.py`: template `giver`/
  `epilogue` fields, `attach_giver`, the central cast
  (`_cast_the_land` + the role tables, `world["npcs"]`). `people.py`:
  `make_npc` / `npc_line` / `NPC_MIN_AGE` (the targeted generator).
  `story.py`: `CONQUESTS` (the four variants' content), `WAVE_LEVELS` /
  `WAVE_ROOMS`, `init_story` / `next_wave_due` / `post_wave` /
  `on_wave_done` / `occupied` / `war_status_lines`. `session.py`:
  `maybe_post_wave`, `occupied_here` / `occupation_line`, the epilogue +
  `done_day` stamp in `advance_quest`, the boss-name spawn in `cmd_room`,
  `cmd_chatter` + `CHATTER_PROMPTS`.
- **Magic & Mind** (2026-07-15, replacing the 2026-07-14 placeholder) —
  `rpg.py`: the constants block (the `SPELLS` catalog, cast costs/
  severities, the DC knobs, opener costs, `SPELLBOOK_PRICE`),
  `Entity.mind` / `spells` / `spell_ward` and the per-fight states
  (`unseen`, `aloft`, `stunned`, `possessed`, `disarm_tried`,
  `dex_debuff`), the magic API (`is_wizard`, `aim`, `spell_rank`,
  `attack_school`, `default_cast`, `choose_cast`, `cast_severity_mods`),
  the cast branch in `_attack` + `pressure(cast=...)` (AIM stat swap,
  ambush strikes, the disarm exchange, the misfire fumble, the stun
  riders), `casting_check` + `_misfire`, the openers (`_cast_openers` /
  `_cast_opener`), the hero fireball sweep + stun/possession/aloft
  handling in `group_combat`, `_clear_fight_states` (fight end / clean
  escape / `refresh_foes_after_retreat`), `blink_escape`, the "vanish"
  pause action (`_do_pause_action`, `standing_order`), the wizard roll in
  `make_human` (MIND-highest), `train_spell` / `learn_spell` /
  `buy_spellbook`, and the spell branches in `develop_hero` /
  `autospend_points`. `sites.py`: `FoeSpec.mind` / `school_rank` /
  `spell_ward` + the hexer/pyromancer/magus rows and the roster tags.
  `quests.py`: `CASTER_POOL` — one contained caster template per race
  (NOT the warband ladder; see rules.md on the career collapse that
  decided it) plus the "Renegade Magus" epic; **quest sight** —
  `quest["fuzz"]`, `mind_precision` / `seen_level` / `level_grade`, the
  `mind` param through `quest_line` / `board_lines` /
  `quest_detail_lines`. `session.py`: `train HERO SPELL`, `buy HERO book
  SPELL` (capitals), `cast HERO scry|teleport`, `resume --vanish`,
  `retreat --blink`, `party_mind` + the blurred board/show/take
  readouts (`show --dm` = the true view), the `visited` save key
  (teleport's known ground), the levelup menu's spell section.
- **Ranged combat & the field** (2026-07-16) — `rpg.py`: the constants
  block (`ROOM_FIELD` / `WILD_FIELD` / `CAST_RANGE`, ammo caps/lots/
  recovery rates, `NOTICE_BASE` / `CONSPICUOUS_TRAITS` /
  `conspicuousness`), the Weapon card's ranged fields (`range`, `reload`,
  `aim`/`aim_flat`, `heavy_draw`, `ammo`, `missile`, the melee-grip
  line), the seven ranged cards in `WEAPONS`, `Entity`'s field state
  (`adv`, `reload_left`, `switched`, the shot tallies) and helpers
  (`ranged`, `shot_ready`, `threat_reach`, `shot_aim`, `spend_shot`),
  the shot branch in `_attack` + `pressure(shot=/vs_shot=)`, the
  movement phase and mode logic in `group_combat` (`field` param, the
  `_gap` closure, chargers-then-skirmishers, the arrival volley, the
  slip-past-the-press advance), `_recover_missiles`, reach-gated parting
  blows in `attempt_retreat(field=)`, foe requiver in
  `refresh_foes_after_retreat`, `buy_ammo` / `grant_starter_ammo`.
  `sites.py`: `HAND_BOMBARD`, the archer rearm + the slinger/hunter/
  gunner rows, foe ammo in `make_foe`, the `shoots to range N` roster
  tag, `run_site` at `ROOM_FIELD`. `quests.py`: the cultural ladder
  pools (`GOBLIN_LADDER_POOL` / `DWARF_LADDER_POOL` /
  `ELF_LADDER_POOL`), `notice_contest`, `foes_preferred_field`.
  `session.py`: the engagement rework in `wild_event`,
  `party_preferred_field`, field plumbing through
  `resolve_encounter`/`pending`/resume/retreat, `fight --field`,
  `buy HERO arrows|bolts|shells|knives`, the dwarf-settlement revolver
  gate, starter ammo on `give`.
- **Cross-land deliveries** (2026-07-14) — `quests.py`:
  `DELIVERY_TEMPLATES` / `build_delivery_quest` / `_post_delivery` and
  the kind-aware readout helpers. `session.py`: `active_delivery` /
  `deliver_if_arrived` (called at travel arrivals, in `finish_encounter`,
  and after a retreat's clean escape), the forced interception in
  `cmd_travel`, and the delivery guards in take/room/status/sheet/
  opening-hook/board-rumors.
- **The world & navigation** (2026-07-09) — `quests.py`: `lands` (race ->
  settlements; the map IS this grouping, no coordinates), `wild_pool`
  (what roams a land = the union of its race's template pools),
  `roll_wild_level` (the road's party-independent geometric level table),
  `build_wild_encounter`, `wild_encounter_xp`. `session.py`: the location
  helpers (`_settlement_location` / `local_settlement` /
  `at_quest_settlement` — board/take/room/hideout/barrow are gated on
  being there), `wild_event` (the one roll: nothing / fight / sighting,
  with the spotted-vs-ambush valve), and `cmd_travel` / `cmd_explore` /
  `cmd_hunt` / `cmd_engage` / `cmd_map`.
- **Session state** — `session.py`: one JSON document in `save.json`
  (party, clock, purse, rng, world, `active_quest`, `pending` paused-fight
  record, `rooms` fled-room records, `location`, `places` discovered wilds,
  `sighting`, `streak` momentum record, `site_clears` set-site pay
  tracking, and `recruits` (the on-request candidate pool, keyed to its
  settlement and day); entities/
  weapons via the `_entity_*`/`_weapon_*` serializers).
  A paused fight blocks every between-fights command until settled. Quest
  progress lives on each quest (`next` cursor, `status`); `advance_quest`
  pays site lumps and closes quests.

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

**Current state (2026-07-16, after Ranged Combat & the Field — the
distance model, seven ranged cards, four shooter foe rows, the notice
contest; rooms now open at field 2, the wilds at field 3). The full dated
report of every measured re-tuning lives in `benchlog.md`; this is only
the standing summary — refresh it whenever a new entry lands there.**

- **The batch's headline: the melee game is UNDISTURBED within noise.**
  Field 0 fights are the old engine to the digit by construction, and
  the room/road fields moved the tuned sites almost nothing (the
  hideout's archer traded a random melee weapon for one shortbow shot —
  a wash). The one real drift is the mid-band career (below).
- **Hideout** (rank 0, 10k runs): clear **80.6** / wipe **16.7**;
  reckless (no-resource) wipe **79.2**. **Barrow** `[3, 3, 4]`: clear
  **26.1** / wipe **71.0**. "Not using resources mostly means death"
  holds.
- **Training ladder** (5k/rank): barrow **27 -> 58 -> 84 -> 97**, hideout
  **81 -> 96 -> 99.4 -> 100** — a rank still reads as a rank.
- **Party size** (5k/size, sizes 1-4): hideout **22 / 81 / 98.8 / 100**,
  barrow **1.1 / 27 / 73 / 95** — numbers still dominate; XP x 2/N is
  the counterweight.
- **Weapons (melee)**: zweihander best duel on precise/steady, katana on
  powerful/balanced, zweihander owns every swarm column, staff trails on
  purpose — no weapon tops every cell.
- **Ranged cards** (`bench_ranged.py`, 4k/cell, suited frames vs the
  melee reference): reach is an edge that grows with the field and dies
  at the door — longbow **46 / 49 / 67** win% at fields 0/2/3, revolver
  26/45/50, crossbow 8/17/34, blunderbuss 13/24/27, sling trails
  everywhere on purpose; the katana wins **97** flat, so no shooter
  out-duels steel at contact, and every card holds its own in the played
  escort shape (91-99% with a katana partner vs a wolf pack). Flagged
  wart: cadence-1 range-2 cards read a few points WORSE at field 2 than
  at 0 in a pure 1v1 (one graze-grade shot under-buys its STA + tempo) —
  party play doesn't show it; candidate levers if it nags: severity
  flats, or a free switch for melee-grip-strong cards.
- **Bestiary at-level win rates**: melee rows benched at field 0 —
  unchanged by construction (skeleton 95.8, troll 97.2, dragon 89.9,
  hexer 81.8...). The shooter rows bench at field 3: archer **97.2**
  (L1), slinger **98.7** (L1), hunter **94.8** (L3; 69.8 at -2), gunner
  **97.5** (L4; 82.8 at -2) — soft at level with real -2 walls, the
  L1-band norm; annotations set this session (hunter 4 -> 3,
  gunner 6 -> 4 measured down).
- **Generated content** (300/cell): at-level rooms win **75-97** across
  levels 1-20; at-level sites **~96 at L1** sliding to **~43-51 at
  19-20** — the pre-ranged shape.
- **Careers** (200): reach **L5 86% / L8 66% / L11 38% / L14 19% /
  L20 6.5%**, median death **L9**, capped median 175 days / 40 quests.
  The L8 band is ~6 points harder than 2026-07-15 (72 -> 66): enemy
  shooters and casters now collect approach-round shots in rooms and on
  the road — the intended price of distance being real. Everything else
  within noise.
- **Open flags for the designer** (levers untouched — feel bows in play
  first): the hideout still sits ~25 points above the 2026-07 retune's
  ~55% clear target (the standing flag); the career mid-band hardening
  partially offsets the Magic & Mind ease. NOTE the benches model NO
  hero shooters (the reference duo stays melee) — a played bow party
  runs easier than these numbers, especially outdoors.
- **Pacing anchors** (2026-07-12 probe): played campaigns reach L10
  around in-game day 45-65 (~10-12 chat hours) and L20 around day
  110-150 (~25-30 hours).

**Difficulty levers, easiest first:** the room layouts
(`sites.HIDEOUT_ROOMS` / `sites.BARROW_ROOMS`) and the quest generator's
budget knobs (`quests.ROOM_SHARES`, `PACK_CAP`, `DUP_COST` — these move
every generated site at once), then survival tunables, then the
pause/retreat layer, then weapons, then economy/progression (the level-pay
formulas set the whole game's pace now), then the foe stat blocks
(`sites.FOES` — **enemy DEX is the sharpest knife**: a single point moves
clear rates by tens of percent; the soldiery's `training` is the same knife
for the ladder), then the hero roll ranges (all constants: see the dev map
above). The ranged layer adds its own levers: the field sizes
(`ROOM_FIELD` / `WILD_FIELD` — one point of field is roughly half a shot
per fight), the cards' severity flats (they replace STR, so they move in
bigger steps than melee mods), reload cadence, and `NOTICE_BASE` (the
spotted/ambushed mix on the road). **Always re-run `tune.py`,
`bench_training.py`, `bench_weapons.py`, `bench_ranged.py`,
`bench_bestiary.py`, and `bench_quests.py` after
touching any of these** — small changes swing lethality, the attrition
curve, the weapon matchup matrix, the level annotations, and the career
curve.


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
  restructure freely; any `save.json` is disposable — when a change breaks
  it, delete it and start a fresh game rather than writing migrations or
  compat shims.
- **Saves are disposable during development too.** Don't spend effort
  preserving, backing up, or restoring `save.json` while developing or
  tuning: run `session.py new`, wreck the state with test games, move on.
  A playthrough worth keeping is the exception the designer will name
  explicitly (commit its `save.json` — the format is plain JSON precisely
  so a kept playthrough can travel with the repo), not the default to
  protect.

## Not yet built (the point of the design)

The between-fights layer is now substantially player choice: gold/XP flow,
skill points are a real allocation (combat training vs weapon proficiency —
nothing auto-spends in session play), `buy_potion` and `buy_weapon` make
shopping real decisions, **the quest board is the "pick your fights"
layer at full size** — a generated world of leveled quests, levels shown
straight, pay scaling with them — and **the party itself is player choice
now** (2026-07-11): who to pick, who to hire, whose patience to spend, when
to buy it back with a tavern night or a downtime day. The mid-fight layer
exists too: the pause (drink / Berserk / War-Breath / vanish / retreat &
chase — or a blink out — with fled rooms persisting). **The Magic & Mind
layer is in (2026-07-15)** — MIND-highest wizards from level 1, nine
spells at ranks 1-3 (skill points buy depth, spellbooks buy breadth,
Power prices the burst), the casting check with degrees of success, the
assassin openers, telekinesis, possession, scry, teleport travel, and
quest sight (the board blurs to the party's best MIND). **Cross-land
deliveries** (2026-07-14) send the party travelling. **Ranged combat &
guns are in (2026-07-16)** — the field model, seven ranged cards, ammo,
shooter foe rows, cultural arms, and the notice contest (rules.md's
Ranged Combat & the Field add-on). Next: **the levelling framework**
(designed 2026-07-16, full spec in plan.md — the point economy,
learnable abilities, the warrior moves system, the alchemy tree; three
implementation sessions A/B/C), then stat
transcendence + the wraith (the rest of the old magic phase), armor
(note the designer's lean: probably never important), named
weapon instances — and the career sim's finding that the 14-20 band lacks
its player power until masterwork/magic-item content lands. See plan.md
for the full roadmap and the parked-ideas list.
