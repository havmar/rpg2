# RPG2 — Combat Sim Prototype

A combat simulator for a fantasy RPG, intended to be played through Claude Code
with Claude as DM. Fights resolve on their own (no input once a fight starts,
except the **pause**: at most ONCE per encounter, the first wounds crossing
stops the melee for one "fight on / drink / heal / convert / retreat?"
question, then it runs to conclusion on the party's standing orders) and
produce an
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
  up: major questlines & the story layer), plus parked ideas and open
  questions.
- `rpg.py` — **the engine.** Combat (`group_combat` + the pause/retreat
  layer), weapons and breakage, the survival tracks and rests, progression,
  economy, random party generation, and the batch-sim policies
  (`sim_fight` / `sim_pause_policy`). Stdlib-only and self-contained;
  everything else imports it. All tunable constants sit at the top.
- `sites.py` — **the catalog & the set sites.** The foe catalog (`FOES`,
  `make_foe` — six monster families plus the humanoid ladder, every row
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
  `WILDCARD_ROLES`, `world["npcs"]`). `python quests.py [--seed N]
  [--demo]` prints a generated world's board and cast.
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
  `--- PLAYER LOG ---` block the DM pastes into chat.
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
> dev workflow, the file index, tuning levers, and measured balance numbers** —
> don't re-explain a mechanic here that rules.md already covers.

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
  not independent rolls) and the hero spiral gear (`HERO_PAIN`
  — trained fighters, both sides, take `hp_lost // 2` as the wound
  penalty since 2026-07-09), the momentum streak (`STREAK_STEP` +
  `streak_multiplier` — consecutive same-site encounters without a camp
  pay rising XP; a full one-go run collects exactly the encounter share;
  2.0 since 2026-07-10: x1/x3/x5 across three rooms), the tavern night
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
- **Content** — `sites.py`: `FOES` (the bestiary: 22 stat blocks — six
  monster families + the humanoid ladder — each row with a bench-calibrated
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

**Measured numbers (2026-07-07, after the party-size counterweights + the
bestiary).** The press (`CROWD_CAP`), the pain divisor, sweeps, regen, and
XP-per-head landed; both existing sites re-measured essentially UNCHANGED
(the press only binds at 3+ attackers on one target, which the duo-tuned
rooms rarely produce): hideout rank 0 clear ~64.5 / wipe ~33 (reckless wipe
~68), barrow ~3.6 / ~95 (reckless ~99); training ladder barrow 4 -> 17 ->
44 -> 75, hideout 64 -> 86 -> 96 -> 99. Details worth knowing:

- **Party size** (rank 0, 5k/size; the reason "Balanced for two" exists):
  hideout clears **15% / 64% / 93% / 99%** for sizes 1-4, barrow **0.1% /
  3.6% / 25% / 59%** — in-fight, numbers still dominate every other
  progression axis. The press barely moves these on current duo-scale
  rosters; the drag that bites is **XP x 2/N** (a four-party levels at half
  speed, i.e. runs 1-2 training ranks behind — worth ~20-30 clear points
  against a fixed site) plus flat gold, and it compounds instead of showing
  up in a single-run sweep. Expect the press + sweeps to matter more once
  the encounter generator builds bigger rosters.
- **Weapons matrix**: the story holds (rapier best duelist on three of four
  frames, coin flip with the zweihander on precise; zweihander sweeps every
  swarm column; staff trails on purpose). Swarm survival is a few points
  HIGHER across the board — the press shields a lone fighter from 3
  skeletons (only 2 swing per round): e.g. zweihander swarm on the balanced
  frame ~27% (was ~20).
- **Bestiary at-level win rates** (`bench_bestiary.py`, 2k/row, reference
  duo at the annotated level vs `ref_pack`): wolf 61, cutthroat 75,
  archer 88, boar 89, bruiser 84, skeleton 74, dire wolf 85, spider 82,
  bear 82, ghoul 85, ogre 88, troll 87, wight 76, wyvern 81, giant 85,
  drake 86, dragon 73 — packs (site components, meant to chain with
  attrition) sit high-70s-to-high-80s, solo bosses (the whole outing)
  mid-70s-to-high-80s, and every row's -2 column is a real wall (dragon at
  L16: 48%). Provisional by design: final assembly tuning belongs to the
  encounter generator.

**Measured numbers (2026-07-08, the quest system: pool growth + humanoid
ladder + level-pay + the generator).** Full suite re-run; the tuned game is
UNDISTURBED — hideout rank 0 clear 64.5 / wipe 32.6 (reckless 67.9), barrow
3.6 / 94.5 (reckless 99.3), training ladder and party sweep identical, the
weapons story holds (rapier/zweihander coin flip on precise, zweihander owns
every swarm column, staff trails). Barrow PAY changed with the level
formulas: 30 XP/encounter + 110 XP & 45 g on the clear (was 45/165/45 under
the old 3x rule) — XP down a third, gold unchanged. New numbers:

- **The humanoid ladder** (`bench_bestiary.py`, at-level win vs reference
  duo): soldier L3 **81**, veteran L6 **63**, champion L10 **66**,
  blademaster L15 **57**, warlord L19 **59** — deliberately the scary end
  of the catalog band (elite duelists), each -2 column a wall until the
  top band, where the +-2 gradient flattens for every row (the party
  saturates: skills capped ~L13, pools only after — the pre-magic,
  pre-masterwork band).
- **Generated encounters** (`bench_quests.py`, at-level room at share 1.0):
  win 55-93% across the whole 1-20 line — inside the calibrated catalog
  band. The three rules that got it there (linear unit pricing measured
  rooms ~15 levels hot): the crowding surcharge, the ~1.4-pack room cap,
  and solo-boss rows fighting alone (all documented in rules.md's Quest
  System add-on; knobs at the top of quests.py).
- **Generated sites**: at-level clear ~66-78% at L1-5 (bracketing the
  hideout's 64), ~42-62% mid-band, ~32-48% at 15-20; -2 a real wall.
- **Careers** (fresh duo, fresh world, grind-below-level policy, camps
  between rooms): reach **L5 46% / L8 29% / L11 14% / L14 5% / L20 ~0.3%**;
  median death at L3-4 (the rank-0 front door claims ~a third of careers);
  a capped career took ~167 days / ~31 quests. Per-quest death at the top
  band stays 15-25% however you pick — the missing player power up there
  is masterwork/armor/magic (see plan.md, "a career finding to design
  against").
- **A world posts ~26k XP** (1.35x the 19,000 a duo needs to reach L20),
  asserted at generation; ~35-45 quests across ~6 settlements.

**Measured numbers (2026-07-09, the pain-2 regear + momentum streak +
navigation).** The spiral was geared down for ALL trained fighters (heroes
via `HERO_PAIN = 2`; the bandit rows and the soldiery got `pain=2` in
sites.FOES — symmetric on purpose), the hideout's den gained an archer
(5 -> 6 bandits) to hold the starter on target, per-encounter XP moved onto
the momentum streak, and `tune.py` gained the outcome-shape check (HP lost
on cleared runs). The full suite, re-run:

- **The regear's target — less binary outcomes — landed:** cleared hideout
  runs now spread **22% / 50% / 25% / 3%** across the <10 / 10-40 / 40-70 /
  70%+ HP-lost buckets (barrow clears: 19/52/26/3). Losing a quarter or
  three-quarters of the party's blood and *walking out* is now the common
  texture of a win; before the regear the middle barely existed (whoever
  bled first spiraled into helplessness — also why bandit rooms used to
  deal 0 damage or kill).
- **Hideout** (rank 0, new 6-bandit layout, 10k runs): clear **~58%** /
  wipe **~37%** / Down in **~49%** of runs — back on the designer's ~55%
  target — vs **~70% wipe reckless**: ignoring resources still costs most
  of a party's life expectancy.
- **Barrow** `[3, 3, 4]` (rank 0): clear **~13%** / wipe **~85%** (was
  3.6/95): still a death trap fresh, no longer a near-certainty. Training
  ladder (5k/rank): barrow **13 -> 37 -> 67 -> 89**; hideout
  **58 -> 83 -> 95 -> 99** — a rank still feels like a rank.
- **Party size** (rank 0, 5k/size): hideout **14 / 58 / 89 / 97**, barrow
  **0.5 / 13 / 49 / 82** for sizes 1-4 — numbers still dominate; the free
  3rd/4th member remains the intended crutch, paid for by XP x 2/N.
- **Weapons: the rapier lost its duelist crown** (bench_weapons, now run
  at hero pain): its edge was graze-chip feeding the full-force spiral, so
  halving the spiral halved the niche. Best duel is now zweihander on
  precise/steady and katana on powerful/balanced, rapier a close second
  everywhere, zweihander still owns every swarm column (up to 44% on
  balanced), staff still trails. "No weapon tops every cell" still holds;
  a rapier re-niche idea is parked in plan.md.
- **Bestiary at-level win rates drifted up ~5-10 points** for the monster
  families (archer 94, cutthroat 84, wolf 81, skeleton 86, dire wolf 94,
  ghoul 94, ogre 94, troll 92, wight 87, wyvern 91, giant 92, drake 95,
  dragon 85); the elite-humanoid ladder — which got the same pain buff the
  heroes did — stayed put or hardened (soldier 89, veteran 72, champion
  63, blademaster 54, warlord 54). Ordering intact; re-annotation parked
  in plan.md as calibration polish.
- **Generated content** (bench_quests, 300/cell): at-level rooms win
  61-93% across 1-20; at-level sites clear ~80-87% at L1-5 sliding to
  ~34-55% at 15-20. **The -2 column stopped being a wall** (30-80%
  depending on band) — punching up two levels is now a real, paying
  choice, which is what the leveled-world direction wanted.
- **Careers softened sharply** (200 careers, camps-between-rooms policy —
  which under the streak earns mostly base-rate encounter XP): reach
  **L5 68% / L8 56% / L11 38% / L14 20% / L20 6%**, median death **L8**
  (was L5 46 / L11 14 / L20 ~0.3, median death L3-4). A capped career:
  ~148 days / ~37 quests. The top band (15-20) is still the hard edge
  (per-quest wipe 40-65% at level) and still waits on masterwork/armor/
  magic for its player power.
- **Streak anchors** (exact by construction): a level-L 3-room site pays
  its rooms `base x 1/2/3` in one go — hideout 8/15/22 + 55 lump = 100,
  barrow 15/30/45 + 110 lump = 200 — and `base x 1/1/1` camped-between
  (~78% of total collected). Wild/road/hunt fights pay the site's
  mid-streak rate at their level (15 at L1) and never streak.
- Also fixed in passing: `site_clears` (the set sites' clear-lump tracking,
  added 2026-07-08) was never persisted to save.json, so the hideout/barrow
  lump could never actually pay across separate CLI invocations. It
  persists now.

**Measured numbers (2026-07-10, the play-feedback batch: crippling-blow
rename + softened parting blows + fate's bargain + the wilds valves +
tavern/camp nights + streak x1/x3/x5).** Mechanics in rules.md (fate's
bargain, the tavern, the retreat softening) and dm.md. The full suite
re-run; **the tuned game is UNDISTURBED** — by design, most of the batch is
session-layer (fate's bargain needs `Entity.protagonist`, which only
session play sets; the wilds valves live in `session.py`; the tavern is a
command) and the one engine change the sims do see (parting blows softened
one tier) barely moves site outcomes, because deaths AT the door were
already rare — the lethal retreat failure is the chase, and that is
untouched:

- **Hideout** (rank 0, 10k): clear **58.6** / wipe **36.5** / Down ~49 —
  same as 2026-07-09. **Barrow** `[3,3,4]`: clear **13.2** / wipe **83.5**
  (was 13/85). Cleared-run HP-lost spread 17/48/31/3 (hideout) and
  19/52/25/4 (barrow) — the middle is still where wins live.
- **Correction while re-measuring:** reckless (no-resource) hideout wipe
  measures **80%** on BOTH the previous commit and this one — the ~70% in
  the 2026-07-09 entry was stale (quoted from a pre-6-bandit-layout run).
  The resource gap is even wider than documented: 36.5% wipe with
  resources vs 80% without. Barrow reckless 98.7%.
- **Training ladder** (5k/rank): barrow **14 -> 38 -> 69 -> 89**, hideout
  **58 -> 83 -> 95 -> 99**. **Party size** (5k/size): hideout
  **13 / 58 / 89 / 96**, barrow **0.6 / 14 / 51 / 82** — all within a
  point or two of 2026-07-09.
- **Weapons matrix**: unchanged story (zweihander best duel on
  precise/steady, katana on powerful/balanced, zweihander owns every swarm
  column, staff trails). **Bestiary**: every row within noise of the
  2026-07-09 numbers (archer 94, wolf 81, skeleton 86 ... dragon 84.5,
  warlord 55.5); ordering intact.
- **Careers** (200, camps-between-rooms policy): reach **L5 67% / L8 54% /
  L11 37% / L14 19% / L20 4.5%**, median death L8, capped career ~141
  days / ~38 quests — statistically the same curve as 2026-07-09. The
  steeper streak doesn't slow the career sim because its policy camps
  between rooms and always earned base rate; what it changes is the
  PLAYED game's incentive: piecemeal now collects ~70% of a site's total
  (was ~78%), and the last room of a one-go run plus the lump carries
  ~80% of the site's pay.
- **New streak anchors** (exact by construction): a 3-room site pays
  `base x 1/3/5` in one go — hideout 5/15/25 + 55 lump = 100, barrow
  10/30/50 + 110 lump = 200 — and `base x 1/1/1` camped-between. The
  MIDDLE rate is invariant under the step change, so wild/road/hunt pay
  (that mid rate; 15 at L1) and the off-script `ENCOUNTER_XP = 15` are
  untouched.
- **Fate's bargain measured at the engine level** (rigged 400-fight probe,
  not the tuned sims): the spare converts a PC death into a Down and, on
  victory, one random companion's death; a clean retreat after the spare
  waives it. In the sims (`protagonist` never set) nothing fires — bench
  numbers can't drift from it. Expect PLAYED campaigns to lose fewer PCs
  and more companions; no sim models that yet (the career sim has no
  protagonist either — a future "PC-centric career" variant is the
  natural check if this needs numbers).

**Measured numbers (2026-07-11, the character & party layer: CHA capacity +
satisfaction + recruiting + races/traits).** The layer is session-side by
construction — `group_combat` never reads a trait or a satisfaction number,
and the sims never set `cha`/`protagonist`/`satisfaction`, so no bench CAN
move from the mechanics; the full suite was re-run anyway because
`make_human` now rolls CHA (every seeded RNG stream shifted, so every
number re-measured through fresh randomness — a distribution-level
no-change check). It held, everything within noise of 2026-07-10:

- **Hideout** (rank 0, 10k): clear **58.0** / wipe **37.2** / Down ~50
  (was 58.6/36.5); reckless wipe **81.2** (was 80). **Barrow** `[3,3,4]`:
  clear **13.5** / wipe **83.3** (was 13.2/83.5), reckless 98.6.
  Cleared-run HP-lost spread 16/49/31/4 and 18/52/27/3 — the middle holds.
- **Training ladder** (5k/rank): barrow **14 -> 38 -> 68 -> 90**, hideout
  **58 -> 82 -> 95 -> 99**. **Party size** (5k/size): hideout
  **13 / 58 / 89 / 97**, barrow **0.6 / 14 / 51 / 83** — identical story.
- **Weapons matrix**: unchanged (zweihander best duel on precise/steady,
  katana on powerful/balanced, zweihander owns every swarm column, staff
  trails). **Bestiary**: every row within a point or three (archer 92,
  wolf 80, skeleton 87 ... dragon 86, warlord 54); ordering intact.
  **Generated content**: at-level rooms win 61-96 across 1-20, sites
  ~81-88 at L1-5 sliding to ~37-57 at 15-20. **Careers** (200): reach
  L5 63% / L8 53% / L11 34% / L14 20% / L20 5.5%, median death L8.
- **What the layer changes in PLAYED games, not sims**: the party starts
  as PC + hires instead of a hardcoded duo (the "Balanced for two" baseline
  is now the typical capacity-1-or-2 outcome, not a constant); quest gold
  runs up to +30% at CHA 6; and satisfaction is a new upkeep economy
  (tavern nights and downtime days vs the streak's push-on pay). No sim
  models satisfaction churn or the CHA gold — the career sim plays an even
  duo with no protagonist (parked note in plan.md: a PC-centric career
  variant is the natural check if played campaigns drift from the bench).

**Measured numbers (2026-07-11b, the pause & potion batch: one pause per
encounter + standing orders + the mid-fight healing potion + the
self-restocking kit; also the starter ally, `dismiss`, land-wide board
rumors, `camp N`/`--heal`, and party.txt).** Two of the changes are
sim-visible and the full suite was re-run: `sim_pause_policy` now answers a
wounds crossing by DRINKING a carried healing potion mid-fight (the new
"heal" action), and `long_rest` restocks the kit. The standing-orders
engine hook itself moves nothing (the sims pass no callback and keep the
old every-crossing pause). **The game got a full notch easier — the
designer's ~55% hideout target is now overshot by ~19 points — flagged
below, levers deliberately untouched this session:**

- **Hideout** (rank 0, 10k): clear **73.6** / wipe **23.2** / Down ~35
  (was 58.0/37.2/~50). **Barrow** `[3,3,4]`: clear **19.2** / wipe **77.3**
  (was 13.5/83.3). Attribution probe (tune re-run with the sim heal
  reverted, kit kept): the KIT alone is hideout 62.2/34.8 — so ~+4 points
  come from the kit and ~+11 from the mid-fight heal. **Reckless wipe is
  UNCHANGED (81.2 hideout / 98.6 barrow)** — "not using resources mostly
  means death" still holds in full; what changed is how much using them
  now buys (a 58-point survival gap, was ~44). Cleared-run HP-lost spread
  20/54/24/3 and 23/54/20/3 — the middle holds.
- **Training ladder** (5k/rank): barrow **19 -> 47 -> 74 -> 93**, hideout
  **72 -> 91 -> 98 -> 99.8** (was 14/38/68/90 and 58/82/95/99) — a rank
  still reads as a rank, shifted up.
- **Party size** (5k/size): hideout **20 / 72 / 96 / 99**, barrow
  **1.5 / 19 / 60 / 88** (was 13/58/89/97 and 0.6/14/51/83). Note the
  full party of four now clears the starter at 99% — in-fight safety by
  headcount is stronger than ever; XP x 2/N remains the counterweight.
- **Weapons matrix**: the story is intact (zweihander best duel on
  precise/steady, katana on powerful/balanced, zweihander owns every swarm
  column, staff trails; no weapon tops every cell).
- **Bestiary**: monster families drifted up a few points (wolf 87, skeleton
  87, dire wolf 97, dragon 90); the elite-humanoid ladder softened MOST
  (veteran 80 was 72, champion 76 was 63, blademaster 67 was 54, warlord
  63 was 54) — long duels against wound-spiral fighters are exactly where
  a mid-fight heal shines. Ordering intact; the parked re-annotation pass
  is now genuinely due when the numbers next feel mushy.
- **Generated content**: at-level rooms win 70-97 across 1-20; at-level
  sites ~86-92 at L1-5 sliding to ~38-58 at 15-20; -2 columns 35-86.
  **Careers** (200): reach **L5 80% / L8 68% / L11 49% / L14 26% /
  L20 9.5%**, median death **L9** (was 63/53/34/20/5.5, median L8) — the
  career curve softened sharply; the kit compounds across a career's many
  nights (a career sim party never buys potions and now never runs out of
  the baseline).
- **The flag for the designer:** the hideout at rank 0 now sits ~19 points
  above the 2026-07 retune target (~55 clear), and the floor-hit rate
  dropped below it too (Down ~35%, target ~half of runs) — the mid-fight
  heal prevents exactly the falls the target counted. Both moves were
  explicit design calls made knowing the direction (the wounds pause
  finally has an answer that addresses wounds; nobody shops for the
  baseline potion), and the felt game had been running harsh. If the new
  level is too soft, the counter-levers in ascending disruption: gulp-size
  mid-fight heal (restore 3, not the full 5), a thinner kit (healing only,
  or top-up every OTHER night), enemy DEX (the usual knife, but it moves
  every annotation). Recommend feeling it in play before pulling any.

**Measured numbers (2026-07-12, the story layer: givers + central cast +
epilogues + the conquest questline).** The layer is content and session
plumbing — the engine is untouched and the sims pass no story state — but
worldgen now draws giver faces and the cast from its seeded rng, so every
generated world differs from 2026-07-11b's at equal seeds. The one bench
that consumes worldgen (`bench_quests --part career`, 200 careers) was
re-run as the distribution-level no-change check, and held: reach
**L5 77% / L8 68% / L11 50% / L14 26% / L20 12.5%**, median death L9,
capped career median 161 days / 39 quests (was 80/68/49/26/9.5, median
L9 — all within noise at n=200). Nothing else re-run on purpose:
tune/bench_training/bench_weapons/bench_bestiary/bench_party import
neither quests.py nor the new files. Pacing anchors measured this session
(the instrumented career probe) live in plan.md's Next-up note: played
campaigns reach L10 around in-game day 45-65 (~10-12 chat hours) and L20
around day 110-150 (~25-30 hours). **The war adds ~3,700 quoted XP at
pinned levels 2/5/8/10** on top of the world's ~27k — rich by design
(punching at level in multi-site quests); watch in play whether pressing
the war front-loads leveling too hard.

**Measured numbers (2026-07-13, the streamlining & QoL batch: fixed-budget
stats + generated PC start + recruit-on-request + companion autolevel +
wave gating + phone wrapping).** The one sim-visible change is
`make_human`: independent stat rolls became a FIXED 9-point surplus budget
dealt by a shuffled priority order (equal totals, different shapes — the
recruiting-comparison fix; racial floors stay net extras). Every seeded
stream shifted AND the hero distribution genuinely changed (no more
god-rolls or gutter-rolls), so the full suite was re-run. **The tuned game
is essentially UNDISTURBED** — variance narrowed exactly where the old
tails lived:

- **Hideout** (rank 0, 10k): clear **74.1** / wipe **22.8** / Down ~33
  (was 73.6/23.2/~35). **Barrow** `[3,3,4]`: clear **17.0** / wipe
  **79.6** (was 19.2/77.3). Cleared-run HP-lost spread 16/57/24/3 and
  22/55/20/2 — the middle holds. **Reckless wipe rose to 86.9 hideout /
  99.6 barrow** (was 81.2/98.6): with god-rolled parties gone, ignoring
  resources has even fewer lucky escapes — "not using resources mostly
  means death" is at its strongest measure yet (a 64-point survival gap).
- **Training ladder** (5k/rank): barrow **17 -> 45 -> 76 -> 94**, hideout
  **74 -> 93 -> 99 -> 99.9** (was 19/47/74/93 and 72/91/98/99.8) — a rank
  still reads as a rank.
- **Party size** (5k/size): hideout **17 / 74 / 97 / 99.5**, barrow
  **0.8 / 17 / 58 / 88** (was 20/72/96/99 and 1.5/19/60/88) — numbers
  still dominate; note the SOLO columns dropped a few points (the budget
  means no solo hero rolls hot everywhere, which is fine: the generated PC
  now always has a companion).
- **Weapons matrix**: the story is intact — zweihander best duel on
  precise/steady, katana on powerful/balanced, zweihander owns every
  swarm column, staff trails, no weapon tops every cell.
- **Bestiary**: low-band packs drifted up a few points (archer 97,
  cutthroat 90, wolf 88, skeleton 89, dire wolf 97.5, soldier 94, ghoul
  96, troll 94, wight 91), the top band held (champion 73, blademaster
  66, dragon 89, warlord 61); ordering intact. The parked re-annotation
  pass remains due when the numbers next feel mushy in play.
- **Generated content** (300/cell): at-level rooms win **68-99** across
  1-20; at-level sites clear **~93 at L1-5** sliding to **~38-52 at
  15-20**; the -2 columns 35-85 — same shape as 2026-07-11b.
- **Careers** (200): reach **L5 80% / L8 74% / L11 47% / L14 22% /
  L20 7.5%**, median death **L10**, capped career median 160 days / 39
  quests (was 77/68/50/26/12.5, median L9 — within noise at n=200).
- **What the batch changes in PLAYED games, not sims**: the sims pass no
  standing-orders callback, never set `protagonist`, and use `rpg.
  make_party` (no races/traits), so recruit-on-request, autolevel (the
  sims' own `train_combat` policy is unchanged), the wave gate, and the
  start refactor cannot move a bench by construction — only the
  `make_human` budget could, and the numbers above say it barely did.

**Difficulty levers, easiest first:** the room layouts
(`sites.HIDEOUT_ROOMS` / `sites.BARROW_ROOMS`) and the quest generator's
budget knobs (`quests.ROOM_SHARES`, `PACK_CAP`, `DUP_COST` — these move
every generated site at once), then survival tunables, then the
pause/retreat layer, then weapons, then economy/progression (the level-pay
formulas set the whole game's pace now), then the foe stat blocks
(`sites.FOES` — **enemy DEX is the sharpest knife**: a single point moves
clear rates by tens of percent; the soldiery's `training` is the same knife
for the ladder), then the hero roll ranges (all constants: see the dev map
above). **Always re-run `tune.py`, `bench_training.py`,
`bench_weapons.py`, `bench_bestiary.py`, and `bench_quests.py` after
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
exists too: the pause (drink / Berserk / War-Breath / retreat & chase, with
fled rooms persisting). **Next up: the story layer over the board** (see
`plan.md`) — the mundane-conqueror questline as the authored difficulty
spine, then progression frames (guilds, the legendary smith). After that:
magic/INT, armor (note the designer's lean: probably never important),
guns + ammo, named weapon instances — and the career sim's finding that
the 14-20 band lacks its player power until masterwork/magic land. See
plan.md for the full roadmap and the parked-ideas list.
