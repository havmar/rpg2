# RPG2 — Development Guide

The dev guide for the combat-sim prototype: workflow, the file index, the
dev map, conventions, tuning levers, and the current measured balance
numbers. `AGENTS.md` is only the auto-loaded dispatcher (Claude Code imports
it through `CLAUDE.md`); THIS file is the real development entry point —
read it before changing the game.

> **PLAYING, NOT DEVELOPING? Read `dm.md` and `writing.md` instead** — they
> are the entire instruction set for running a game. Nothing in this file
> (especially the be-thorough dev-communication register) applies at the
> table.

## The feel we're going for

A **mechanics-centered RPG** with the freedom of a tabletop game. Combat is
*autocombat* — it runs to completion in one call so play stays fast in chat
instead of grinding through every roll by hand — but the world around it stays
open-ended and player-driven. The engine owns the numbers; the DM owns the
fiction.

**The retro pivot (2026-07-21, designlog):** the game is presented as a
minimalist retro text adventure, no longer as a narrated ttrpg. The AI's
advantage is reframed: not that it narrates, but that it is the coding
agent RUNNING the game — subsystems it calls on purpose, content
generated where needed, coherence kept by the agent, no central game
loop required (which the "How play is driven" model below already
embodies). Script-generated logs and menus become the primary chat
display; plan.md's THE RETRO PIVOT section is the roadmap, `writing.md`
owns the fiction register, and dm.md applies it at the table.

**How play is driven:** the game is *two halves working together*.
- **The scripts (`rpg.py`, `sites.py`, `quests.py`, `people.py`)** are a
  library of mechanics primitives and content — `start_fight`,
  `group_combat`, `short_rest`, `long_rest`, `party_wiped`, the foe
  catalog, the set sites, the quest generator and its world, the
  character generator and its races/traits.
- **The agent (as DM)** calls those primitives *on purpose*, in whatever order the
  story wants, and narrates over the result. There is deliberately **no
  autopilot** for pacing: e.g. nothing forces the day to end — the agent decides
  when the party makes camp and calls `long_rest`. This preserves TTRPG-style
  freedom. Some of these calls can be automated more later; for now they're
  manual on purpose.
- **Part of the game lives in instructions to the agent**, not in code. The engine
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
- **Fiction written during development uses `writing.md`.** Quest templates,
  places, NPC hooks, items, epilogues, and script-authored event lines use
  the same retro text-RPG voice as the DM. This does not make dev reports
  terse: the shared guide governs words *inside the game*, not explanations
  about the game.

## Files

**Mechanics detail lives in `rules.md`, not in this list.** Each entry here is
a pointer: what the file is, how it's run, where its docs are.

- `dm.md` — **the DM playbook: read it before playing or testing a game.**
  Play protocol, application of the shared fiction style at the table, quick
  mechanics reference. Keep it in sync when play-facing rules change.
- `writing.md` — **the shared fiction and content style guide.** Read it
  before running a game or writing/generating quests, places, NPC hooks,
  items, epilogues, or event copy. It owns the retro text-RPG register across
  play and development; `dm.md` owns play protocol and this file owns dev
  communication.
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
- `designlog.md` — **the dated design-session history** (2026-07-19):
  what was discussed, the road the discussion took, what was decided —
  the reasoning trail behind plan.md's decisions, so settled questions
  stay settled. Append an entry after every major design session.
- `placegen.md` — **the planned place-generation design and content draft**
  (2026-07-23): the authored-vs-generated boundary, persistent feature
  schema, weighting/reveal/mutation/seed rules, implementation order, and
  the first reviewable environment, Area, Site, Room, settlement, cathedral,
  curiosity, and name pools. It is a design source while the feature remains
  unimplemented; shipped behavior belongs in `rules.md`.
- `AGENTS.md` — **the auto-loaded dispatcher**: the play/dev mode fork and
  the doc pointers, nothing else. It is injected into EVERY agent session,
  including play (Claude Code imports it through `CLAUDE.md`; Codex CLI and
  other AGENTS.md-aware agents read it directly) — keep it short and
  register-neutral; shared fiction style belongs in writing.md, dev content
  in this file, and play protocol in dm.md.
- `CLAUDE.md` — **a thin shim** that imports `AGENTS.md` so Claude Code
  loads the same dispatcher; put no content of its own here.
- `rpg.py` — **the engine.** Combat (`group_combat` + the pause/retreat
  layer), weapons and breakage, the survival tracks and rests, progression,
  economy, random party generation, the Magic & Mind layer
  (2026-07-15: the MIND stat, the nine-spell catalog with ranks, the
  casting check, the openers, spellbooks — rules.md's
  Magic & Mind add-on), ranged combat & the field (2026-07-16: per-entity
  advances, the movement phase, shots on the exchange, reload cadence,
  ammo & scavenging, the seven ranged cards, conspicuousness — rules.md's
  Ranged Combat add-on), the levelling framework (2026-07-17: the point
  economy, the ability catalog, the warrior moves, and — session C —
  ALCHEMY & the potion rework: `train_alchemy`/`brew`, the kit shrink +
  forage in `long_rest`, `use_potion`'s overcharge and stat-brew branches,
  the firebomb in `group_combat`, the smoke vial in `attempt_retreat` —
  rules.md's Alchemy & the Potion Rework add-on), and the batch-sim
  policies (`sim_fight` / `sim_pause_policy`). Stdlib-only and
  self-contained; everything else imports it. All tunable constants sit at
  the top.
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
- `quests.py` — **the world, quest & encounter generator** (rules.md, the
  Quest System and World & Navigation add-ons): the persistent Land -> Area
  -> Site -> Room schema and its accessors, the threat math (all constants at
  the top, calibrated by `bench_quests.py`), the room/site/quest builders,
  per-race quest
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
- `karma.py` — **the villain layer** (2026-07-19, rules.md's Karma &
  Heat add-on; the direction it serves is plan.md's VILLAIN PIVOT):
  the karma state dict + heat math (`new_karma` / `heat` /
  `record_karma` / `karma_line`), the DARK quest templates
  + `roll_dark_quest` (lazy per-settlement-day shadow jobs — worldgen
  never sees them; the `spread` param leans hell's assignments upward),
  and the punishment posses (`POSSE_BANDS` /
  `build_posse`: ladder rosters wearing lawful display names, a
  generated leader face). **The hell pact (same day, second slice —
  rules.md's "The Hell Pact"):** `new_pact` + the assignment/
  enforcement knobs (`TASK_INTERVAL_DAYS`, `TASK_GRACE_DAYS`,
  `ENFORCE_*`, `BRIBE_*`, `DEED_FAIL_KARMA`, `HELL_MAIL`), the hell
  enforcers (`HELL_SKINS` / `build_hell_posse` — Chickening Out), and
  the CAPER schema on templates (`deed` = 2d6+stat vs DC gate, `twist`
  = priced terms; 24 dark templates total after the content pass). All
  other knobs at the top (`KARMA_HEAT_STEP`,
  `HEAT_CAP`, `PUNISH_*`, `DARK_JOBS_PER_DAY`; the dark gold premium
  `DARK_GOLD_MULT` sits in quests.py with the pay knobs). The sims
  never import it. `python karma.py [--seed N]` prints sample shadow
  boards and posses (the eyeball check).
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
  World play (2026-07-09; hierarchy 2026-07-22): `map` / `travel` / `look` /
  `go` / `back` / `explore` / `hunt` / `engage` — breadcrumb position,
  macro and local navigation, local boards, road encounters, the momentum
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
  (and the UI pages) is hard-wrapped at `WRAP_WIDTH` = 40 for the
  designer's phone, and the two **UI pages in `ui/`** are rewritten on
  every save but committed only by **`sheet`** — the end-of-every-DM-message
  command (one commit per message; best-effort git, never fatal). The pages
  are **`ui/party.txt`** (`party_sheet_lines` — the full party board) and,
  since 2026-07-22, **`ui/map.txt`** (`map_sheet_lines` — lands, known areas
  with settlement open-job counts + a visited/here marker, and, until the
  planned `ui/minimap.txt` takes over local detail, the sites of every TAKEN
  quest with
  its progress cursor; `accepted_quests` gates it on the new `accepted`
  save key — offered-but-untaken jobs never appear). Both are **committed
  to the branch, not gitignored: they are the player's GitHub UI** (blob
  links, dm.md); only `save.json` and `ui/fight.log` stay untracked.
  Encounter commands print ONE log since 2026-07-21 (the log rework):
  the player-facing display the DM pastes into chat as-is, while the
  full debug log goes to the untracked **`ui/fight.log`** workfile
  (`group_combat` flushes the configured log at pause/resolution and
  `print_combat` flushes its session tail; gitignored with save.json -- the
  post-mortem surface, e.g. on a player death). The block ends with the
  party tally (`tally_lines`: tracks, standing roll penalties -- shown
  HERE and in the pause menu since the fight lines dropped the numbers
  -- kit/purse, rooms-left count, next streak multiplier), the standard
  between-encounters numbers display so the DM's prose never has to
  carry the numbers (dm.md, Narration style). Since 2026-07-17 (session C)
  also the alchemy surface: `brew HERO RECIPE` (once/day), `train HERO
  alchemy`, `use HERO strength|dexterity` (the stat brews / overcharge),
  `retreat --smoke HERO`, companion auto-brew at the night paths, and the
  levelup-menu alchemy sink. Since 2026-07-19: `prices` (the DM price
  sheet, read from the live constants -- dm.md points at it), the
  starting settlement excludes deliveries (their level 0 used to win
  the lowest-job contest and open the game on a high-level hook,
  ~59% of seeds), multi-site SITE CLEARED banners carry their position
  (site 1/2), and the levelup menu shows the moves section to wizards
  too (the free-allocation doctrine: no class gate).
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
  reference party is built on progression doctrine v2 (2026-07-17: the
  old default build priced in the point economy — pools to the old curve,
  training at 2n, proficiency, monotone).
  `python bench_bestiary.py [--trials N] [--kind wolf]`.
- `bench_abilities.py` — the equal-cost matrix (2026-07-17, levelling
  session A; grown in B): frames at L4/L8/L14, each column one
  whole-budget way to spend the same points (reference doctrine /
  training-heavy / pools-heavy / proficiency-heavy / the saves package /
  the strikes package), rows = at-level generated room, generated site,
  soldiery-ladder duel; acceptance band +-10 of the row median, flags
  printed. Utility abilities get an exact-odds table on their own axis.
  **Session B added** the warrior-moves matchup block (a doctrine duo with
  a GRANTED katana repertoire vs one without, on the room/duel rows — what
  the repertoire buys) and the disarm-move-vs-telekinesis-rank-1 price
  check. **Session C added** the alchemist career column
  (`alchemist_matchup`: the L15 alchemist read three ways — the mixed
  alchemist+fighter duo, the two-fighter reference, and the pure-bomber
  trap-control — on the room/site/duel rows).
  `python bench_abilities.py [--trials N] [--frame 8]`.
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
  (`SAVE_COST`, `FIRST_BLOOD_*`, potion restores, the
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
  (`XP_LEVEL_STEP`, `LEVEL_CAP`, `SKILL_POINTS_PER_LEVEL` — 3 since
  2026-07-17, `TRAINING_MAX`, `TRAINING_COST_MULT` — rank n costs 2n,
  `POOL_BUY_CAP` / `POOL_KINDS` — pools are bought now, `buy_pool`;
  `POOL_GROWTH_LEVELS` survives as the doctrine curve only,
  `PROFICIENCY_MAX`), the ability catalog (2026-07-17: the `ABILITIES`
  dict + `learn_ability`; the per-ability knobs `RAGE_ATK_BONUS`,
  `FIELD_MEDIC_DC`, `STORYTELLER_DC` / `STORYTELLER_POWER_BONUS`,
  `SURVIVALIST_DC`, `ARROW_PARRY_DEF` / `_2`; the healing spell's
  `HEALING_CAST_COST` / `HEALING_MEND` / `HEALING_REVIVE_HP` sit in the
  magic block), the warrior moves (2026-07-17, session B: the `MOVES`
  catalog + `learn_move` + `_WEAPON_MOVE_TAGS`; the knobs `MOVE_PROC_BASE`
  / `MOVE_PROC_PER_TRAINING`, `MOVE_STA_REFUND` / `MOVE_REFUND_CAP`, the
  rider magnitudes `THRUST_ATK` / `FEINT_ATK` / `RIPOSTE_ATK` / `IAIDO_*`
  / `FINISHER_SEV` / `POMMEL_SEV` / `OFF_GUARD_PENALTY`, and
  `MOVE_LAND_MARGIN`), economy (`POTION_PRICE`, drop chances, and the
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
- **Between fights** — `short_rest` / `long_rest` (the `Clock`; long_rest
  also re-arms the field medic's day), `use_potion`, `cast_healing` (the
  healing spell, 2026-07-17 — `use_heal` is gone), `buy_potion` /
  `buy_weapon` (the `Purse`), `equip_weapon` (keeps the staff's
  `power_bonus` books), `award_xp` / `award_quest` / `roll_loot`
  (`award_quest` also applies the PC's `cha_gold_bonus` and the +1
  satisfaction lump), `train_combat_once` / `train_proficiency` /
  `train_spell` / `buy_pool` / `learn_ability` (session play banks
  points; the sims and companions auto-spend via `autospend_points`,
  doctrine v2 — `train_combat` the greedy trainer is gone),
  `storyteller_tale` / `survivalist_camp` (the night abilities; session's
  night paths call them), `party_wiped`, `start_fight` (revive-only).
- **Alchemy & the potion rework** (2026-07-17, levelling session C —
  rules.md's Alchemy & the Potion Rework add-on) — `rpg.py`: the alchemy
  constants block (`ALCHEMY_*`, `BREWED_KINDS`, `POTION_DISPLAY`,
  `POTION_OVERCHARGE`, `STRENGTH/DEXTERITY_POTION_*`, `BOMB_*`), the
  `Entity` fields (`alchemy`, `brewed`, `str_buff`, `dex_buff`,
  `last_brew_day`), `train_alchemy` / `brew` / `auto_brew` /
  `alchemy_cost` / `brew_stock_cap` / `alchemy_recipes`, the overcharge
  and stat-brew branches in `use_potion` (`DRINKABLE_KINDS`), the buff
  peel + the per-party kit floor with the forage roll in `long_rest`
  (`KIT_HEALING`/`KIT_STAMINA`/`KIT_FORAGE_CHANCE`, `rng` param; mirrored
  in `tavern_rest`), the FIREBOMB branch in `group_combat` (the fireball
  sweep chassis, `cast="bomb"` -> `cast_severity_mods`/`pressure`
  reading `alchemy` for prof + a flat that grows at rank 5), and the
  SMOKE-vial path in `attempt_retreat` (`smoke=` suppresses parting blows,
  the chase still rolls). `session.py`: `brew HERO RECIPE` (cmd_brew,
  once/day via `last_brew_day`), `train HERO alchemy`, `use HERO
  strength|dexterity`, `retreat --smoke HERO`, `companions_brew` in the
  night paths (auto-brew for party[1:]), the levelup-menu alchemy sink,
  the pause-menu smoke hint. `sites.py`/benches: `auto_brew` at run_site's
  long rests, the `bench_abilities` alchemist career column.
- **The ability catalog in the engine** (2026-07-17) — `Entity.abilities`
  (a set); Bulwark in `_try_save`, First Blood in `_first_blood`,
  the conversions
  gated in `standing_order` / `sim_pause_policy` / `_do_pause_action`,
  Rage in `pressure` (the +2) + group_combat's kill bookkeeping and the
  exhausted-round skip, Field Medic in `_try_field_medic` (called from
  group_combat's death branch; fate's price is never medic'd),
  Arrow-Parry in `_arrow_parry_bonus` (applied in `_attack`'s shot
  defense), Point-Blank Mastery in group_combat's contact/shooting
  branches, Rapid Reload in `Entity.effective_reload`, the night pair in
  `storyteller_tale` / `survivalist_camp`. The archetype seed table lives
  in `make_human` (`_starter_move` picks the drilled seed's move by the
  weapon's tags).
- **Warrior moves** (2026-07-17, levelling session B — rules.md's Warrior
  Moves add-on) — `rpg.py`: the moves constants block + the `Move`/`MOVES`
  catalog + `MOVE_PRIORITY` + `MoveRider`/`build_move_rider` +
  `move_weapon_ok`/`_finisher_ok`/`finisher_name` (just after the WEAPONS
  catalog, which now carries `Weapon.move_tags` via `_WEAPON_MOVE_TAGS`;
  `_MOVE_WEAPON_OK` holds the special gates -- iaido, the finisher, and
  since 2026-07-19 the staff's riposte/disarm quarterstaff pair);
  `Entity`'s per-fight move state (`moves_spent`, `moves_refunded`,
  `feint_target`, `off_guard`, `stanced`, `just_parried`/`parried_last`,
  cleared in `_clear_fight_states`); the selection hook `_fire_move` +
  `_spend_move` + `_move_fire_text`, called from `group_combat`'s bare-
  melee-strike branch (sweep reshapes the swing there; the skirmisher's
  step lives in the arrival-volley branch); the riders inside `_attack`
  (the atk/sev folds + the disarm/trip/kick/pommel-stun outcome block;
  `just_parried` set on a melee parry) and the `off_guard` defense penalty
  in `pressure`; the round-end tick (off_guard/parried_last/feint cleanup)
  and the `stanced` skip in group_combat. Learned via `learn_move`
  (repertoire ≤ training + 1, weapon-gated); `autolearn_moves` spends
  LEFTOVER points on a suited repertoire (called last in `autospend_points`
  and `develop_hero`). `session.py`: `train HERO move NAME` (cmd_train),
  the levelup menu's moves section, `MOVES`/`move_weapon_ok`/`learn_move`
  imports, and the `moves_spent`/`feint_target` serializer handling.
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
- **The log** — `CombatLog` (reworked 2026-07-21, the one-log display;
  persistence fixed 2026-07-23): the list itself is the full debug log
  (never printed in play -- session-created logs target the untracked
  **`ui/fight.log`** workfile; `group_combat` flushes at pause/resolution,
  then `session.print_combat` flushes any appended session tail and prints
  only `.player`); `.player` is THE display --
  col-1, pre-fitted to `PLAYER_WIDTH` = 40 via `fit_lines` (fragments
  never split), damage as `deals N dmg` + tier punctuation (`TIER_EMPH`),
  attacker-HP tags when hurt, quiet-round collapse
  (`round_start`/`finish_rounds`; parries/deflects marked `quiet=`,
  Winded/Spent crossings `defer=` so collapsed rounds still surface
  them), `play_tail` gluing SLAIN/falls onto the wound line, movement
  lines player-only in ranged fights. Emit helpers `_debug` / `_play` /
  `_play_tail` / `_quiet` / `_round_start` keep plain lists working (the
  benches' path -- they get the full wording; full-log line WORDING is
  unchanged on purpose: tune.py/bench greps key on it). The roster
  blocks live in `sites.roster_lines`; the banners in session's
  `log_banner`; the penalties display in `tally_lines` + the pause menu.
- **Content** — all fictional wording follows `writing.md`. `sites.py`:
  `FOES` (the bestiary: 25 stat blocks — six
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
- **The world & navigation** (2026-07-09; hierarchy 2026-07-22) —
  `quests.py`: the world-owned `lands` / `areas` / `sites` / `rooms` stores;
  `new_area` / `new_site` / `new_room` and the tree accessors; settlements
  as areas (`kind=settlement`, capital/town/village `subtype`), discovered
  geography as areas (`kind=natural`, a geographic `subtype`); quest `sites`
  as persistent world IDs; `wild_pool`
  (what roams a land = the union of its race's template pools),
  `roll_wild_level` (the road's party-independent geometric level table),
  `build_wild_encounter`, `wild_encounter_xp`. `session.py`: breadcrumb
  `position` (`land`, `area`, optional `site`/`room`), `current_area` /
  `local_settlement` / `at_quest_origin` / `at_quest_site`; `cmd_map` and
  `ui/map.txt` as the macro Land/Area view; `cmd_look` / `cmd_go` / `cmd_back`
  as the local view and movement precursor to the planned `ui/minimap.txt`;
  `wild_event` (the one roll: nothing / fight / sighting), `cmd_travel` /
  `cmd_explore` / `cmd_hunt` / `cmd_engage`.
- **Karma & heat** (2026-07-19, the villain layer — rules.md's Karma &
  Heat add-on) — `karma.py`: everything (see Files). `quests.py`: the
  `align` field on quest dicts (build_quest/forge_quest/deliveries),
  `DARK_GOLD_MULT` + the dark branch in `quest_gold_total` /
  `site_gold_for`, the DARK tag in `quest_line`. `session.py`:
  `party_level` / `record_karma` (the bucketing shim, called in
  `finish_encounter`, `advance_quest`, `deliver_if_arrived`, `cmd_award`),
  the `align` thread through `resolve_encounter`/`pending`/resume/retreat
  serializers, `maybe_punish` (called at travel arrivals and
  tavern/downtime/camp nights), `roll_dark_board` + `board --dark`,
  `forge --dark`, `award --dark/--good`, `cmd_karma`, the karma lines in
  `tally_lines`/`cmd_status`, the `karma`/`dark_board` save keys.
- **The hell pact & the capers** (2026-07-19, second slice — rules.md's
  "The Hell Pact") — `karma.py`: the pact constants, `new_pact`,
  `HELL_MAIL`, `HELL_SKINS` / `build_hell_posse`, the `deed`/`twist`
  template fields (see Files). `quests.py`: `build_quest` pins a caper's
  site count and copies `deed` → first site / `twist` → last site; the
  deed/twist lines in `quest_detail_lines` (twist is DM-eyes-only).
  `session.py`: the `pact` save key (None = pactless; `new --no-pact`),
  `pact_task` / `pact_lines`, `maybe_assign_task` (arrivals, `board`,
  settlement nights) + `maybe_enforce` (the posse stops, after
  `maybe_punish`), `cmd_task` / `cmd_bribe`, THE DEED + THE TWIST
  branches in `cmd_room`, `cmd_settle`, `_close_site` (advance_quest's
  tail split out: deed-skips and settles close sites through it;
  also the hell-task completion ledger), and the MERCY thread —
  `mercy` through `resolve_encounter`/`pending`/resume/retreat,
  `apply_mercy` (left for dead / the lesson) in place of
  `report_game_over` on posse losses.
- **Session state** — `session.py`: one JSON document in `save.json`
  (party, clock, purse, rng, world, `active_quest`, `accepted` (the TAKEN-
  quest ids, since 2026-07-22 — `cmd_take` appends, `ui/map.txt` reads),
  `pending` paused-fight record, `rooms` fled-encounter records, breadcrumb
  `position`, persistent geography under `world` (`lands` / `areas` / `sites`
  / `rooms`),
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

**Current state (2026-07-17, after the levelling framework session C —
alchemy & the potion rework: the alchemy skill + the long-rest brew, the
kit SHRINK (1 healing + 1 stamina per PARTY, was per hero, + a stamina
forage roll), the overcharge doctrine, the strength/dexterity stat brews,
the firebomb and the smoke vial. Sessions A/B — the point economy and the
warrior moves — still underlie doctrine v2). The full dated report of every
measured re-tuning lives in `benchlog.md`; this is only the standing
summary — refresh it whenever a new entry lands there.**

- **The kit shrink is a FRESH-DUO lever, not a campaign one.** The old
  per-hero kit floored a duo to 2 healing + 2 stamina every camp; the
  `tune.py`/`run_site` sim flees ~72% of rooms (a fixed baseline) and
  grinds them out on free camp-refilled stamina. Cut that faucet and the
  rank-0 sim starves — but a leveled CAREER party camps to full STA for
  free and buys potions, so careers barely feel it. The lever lands
  exactly where the standing flag lived (the fresh hideout duo) and leaves
  the campaign arc alone.
- **Hideout** (rank 0, 6k runs): clear **57.2** / wipe **12.5**; reckless
  wipe **75.9** — IN the 55-65 retune band (was 84.7), and "not using
  resources mostly means death" holds. **Barrow** `[3, 3, 4]`: clear
  **38.1** / wipe **40.6**; reckless **98.3** (was 46.5 / 45.2 — the tough
  site felt the shrink too, still suicide-until-trained).
- **The stamina cliff + the forage roll.** The shrink's effect is almost
  purely a function of the STAMINA floor (a duo needs 2 draughts per
  retry): stamina-2 clears ~76, stamina-1 ~40 — a hard integer cliff. The
  floor gained a **forage roll** (`KIT_FORAGE_CHANCE` = 0.5, one extra
  draught on a good night) to thread the ~0.5-draught-a-night average that
  lands the band. Healing floor barely moves the number.
- **Training ladder** (3k/rank): hideout **57.5 -> 74.4 -> 87.2 -> 94.2**,
  barrow **38.3 -> 71.3 -> 90.2 -> 97.4** — dropped at ranks 0-1 (the
  shrink bites the fresh party), converges by 2-3 (a trained party doesn't
  live on the free kit). A rank still reads as a rank; the fresh-vs-drilled
  gap widened, which is the intent.
- **Weapons (melee) and ranged**: **unchanged to the cell** — both build
  bare stat frames and resolve SINGLE fights (no `long_rest`), so neither
  the kit shrink nor the alchemy layer reaches them. Zweihander/katana/
  staff and the ranged cards order exactly as before.
- **The equal-cost matrix** (`bench_abilities.py`, 250/cell, L8): the six
  columns tell the same story — **all-in pools a trap** (site 4.8 vs
  median 45), **training/weapon top the site row** (58/62.8), saves fine
  from L8. The warrior-moves matchup block is unchanged (room 76->90, duel
  77->90 at L8).
- **The alchemist career** (`bench_abilities`, NEW; L15, 250/cell): the
  MIXED duo (alchemist + reference fighter) clears **room 48.8 / site 24.0
  / duel 32.8** vs the two-fighter reference **67.2 / 53.2 / 63.2**; the
  PURE-alchemist duo is a trap at **6.4 / 2.8 / 4.0**. The alchemist is a
  SUPPORT/ECONOMY career, not combat-parity: the firebomb stays a scarce
  burst (stock cap rank+2) because alchemy is open to ALL — the payoff is
  the kit it brews (which the shrink makes matter), overcharge, and stat
  brews, none of which the one-go site row (the FLOOR) captures.
- **Bestiary at-level**: within noise of session B (the reference duo
  camps to full STA + buys potions — kit-insensitive; no non-alchemist
  combat path changed). The catalog still orders correctly.
- **Generated content** (200/cell): at-level rooms win **67-95** (single
  fights, untouched); at-level sites the familiar 93-at-L1 -> ~45 shape.
- **Careers** (150): reach **L5 83% / L8 60% / L11 36% / L14 12% /
  L20 4%**, median death **L8**, capped median 158 days / 38 quests —
  **within noise of session B** (86/62/32/16/7). The most important
  negative result: the kit shrink leaves the beatability curve intact.
- **Open flags for the designer**: the standing hideout flag is **CLOSED**
  (57.2, in band, from 84.7); if play feels grim, `KIT_STAMINA` 1->2 or
  `KIT_FORAGE_CHANCE` up is the gentler dial (open question #3). The
  alchemist is a support career by the numbers, NOT a bomber-carry — the
  DEX-potion warning (#5) stands but the pure alchemist never out-fences
  anyone, so it did not need cutting. The barrow slid to 38 clear
  (acceptable for the tough site, worth a glance if the 15-20 band ever
  reads punishing). All-in pools remains a trap the levelup menu steers
  past.
- **Pacing anchors** (2026-07-12 probe): played campaigns reach L10
  around in-game day 45-65 (~10-12 chat hours) and L20 around day
  110-150 (~25-30 hours).
- **The karma layer is bench-invisible (2026-07-19).** It lives entirely
  in the play surface: worldgen posts no dark quests (the shadow board
  rolls them lazily per settlement day), the engine is untouched, and no
  sim imports karma.py — verified by a sanity `bench_quests` run (within
  noise) after the slice landed. Its knobs (`KARMA_HEAT_STEP` 100,
  `HEAT_CAP` 3, cooldown 2d / chance 0.6, `DARK_GOLD_MULT` 1.5) are
  hand-set and SIM-UNVERIFIED — tune them at the table; a karma-playing
  career sim is parked in plan.md.
- **The one-log rework's dying-swing reorder is within noise
  (2026-07-21).** The only engine-mechanical piece of the log rework
  (the felled fighter's dying swing resolving immediately after the
  felling blow instead of at its original turn slot) was sanity-checked:
  tune.simulate at 4k trials reads hideout 57.6 clear / 12.2 wipe /
  75.8 reckless-wipe (standing: 57.2 / 12.5 / 75.9) and barrow 37.0 /
  41.4 / 98.5 (38.1 / 40.6 / 98.3); bench_party at 1.5k reads the duo
  58.1 / 38.3 clear (58/38 shape intact). No retune needed; benchlog
  entry 2026-07-21.
- **The dark layer's balance is deliberately unmanaged (designer
  directive, 2026-07-19, the dark-quests session).** "Game balance of
  xp gold and similar should be abandoned for now — a good variety of
  quests will do more good for the game": the hell pact, the capers,
  the mercy, and the 17-template content pass ship with hand-set
  numbers (`TASK_*`, `ENFORCE_*`, `BRIBE_*`, `DEED_FAIL_KARMA`, deed
  DCs 10-11, twist pay 0.5) and NO bench coverage — all play-surface,
  engine untouched, worldgen untouched (`build_quest`'s caper attach is
  a no-op for every worldgen template). Don't spend bench rounds here
  until the dark path has actually been played.

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
spotted/ambushed mix on the road). The point economy adds two more
(2026-07-17): `SKILL_POINTS_PER_LEVEL` and `TRAINING_COST_MULT` — the
two knobs the levelling design explicitly reserved for the bench rounds.
And session C's **kit floor is now a real difficulty lever**
(`KIT_HEALING` / `KIT_STAMINA` — per PARTY now — and `KIT_FORAGE_CHANCE`,
the stamina forage that threads the integer stamina cliff): it swings the
FRESH-DUO sim by tens of points (careers barely move — a leveled party
buys potions and camps to full STA), so it is the sharpest knife for the
rank-0 starter-site clear rate. The alchemy layer's own knobs
(`ALCHEMY_*`, `BOMB_*`, `POTION_OVERCHARGE`, the stat-brew magnitudes)
sit with it at the top of `rpg.py`. The karma layer's knobs
(`karma.KARMA_HEAT_STEP` / `HEAT_CAP` / `PUNISH_COOLDOWN_DAYS` /
`PUNISH_CHANCE`, `quests.DARK_GOLD_MULT`) are PLAY-ONLY dials — no
bench measures them; the felt game is their only meter for now.
**Always re-run `tune.py`, `bench_training.py`, `bench_weapons.py`,
`bench_ranged.py`, `bench_bestiary.py`, `bench_abilities.py`, and
`bench_quests.py` after touching any of these** — small changes swing
lethality, the attrition curve, the weapon matchup matrix, the level
annotations, the equal-cost matrix, and the career curve.


## Conventions

- Stdlib only; keep `rpg.py` self-contained and importable (everything else
  imports it; `sites.py` holds the content so the engine stays generic).
- Keep narrative/log output ASCII (no em-dashes or special glyphs) for Windows.
- `Entity` is `@dataclass(eq=False)` so instances are identity-hashable (used in
  combat sets and the pause's `fired` pairs) — don't switch it back to value
  equality.
- Two layers, kept separate: thin mechanics in code, fiction supplied by
  authored/generated content and the DM in the register `writing.md` defines.
  Don't bake prose into the engine beyond terse event lines.
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
skill points are a real allocation across the WHOLE menu (2026-07-17:
pools vs training vs proficiency vs spell ranks vs the ability catalog —
nothing auto-spends in session play and nothing grows automatically),
`buy_potion` and `buy_weapon` make
shopping real decisions, **the quest board is the "pick your fights"
layer at full size** — a generated world of leveled quests, levels shown
straight, pay scaling with them — and **the party itself is player choice
now** (2026-07-11): who to pick, who to hire, whose patience to spend, when
to buy it back with a tavern night or a downtime day. The mid-fight layer
exists too: the pause (drink / Berserk / War-Breath — for those who know
them — / vanish / retreat &
chase — or a blink out — with fled rooms persisting). **The Magic & Mind
layer is in (2026-07-15)** — MIND-highest wizards from level 1, ten
spells at ranks 1-3 (skill points buy depth, spellbooks buy breadth,
Power prices the burst), the casting check with degrees of success, the
assassin openers, telekinesis, possession, scry, teleport travel, and
quest sight (the board blurs to the party's best MIND). **Cross-land
deliveries** (2026-07-14) send the party travelling. **Ranged combat &
guns are in (2026-07-16)** — the field model, seven ranged cards, ammo,
shooter foe rows, cultural arms, and the notice contest (rules.md's
Ranged Combat & the Field add-on). **The levelling framework is COMPLETE
(sessions A, B, and C, 2026-07-17)** — session A: the point economy (3
points/level, pools on the menu, training at 2n), the eleven-entry ability
catalog, healing as the tenth spell, the archetype seed table; session B:
the warrior moves system (rules.md's Warrior Moves add-on) — `move_tags`,
the eleven-move repertoire, the engine's once-per-fight selection rider
with the flow refund, `learn_move` / `train HERO move NAME`; session C:
alchemy & the potion rework (rules.md's Alchemy & the Potion Rework
add-on) — the alchemy skill + the long-rest brew, the kit shrink (per
party + a forage roll, which CLOSED the standing hideout flag to the
55-65 band), the overcharge doctrine, the strength/dexterity stat brews,
the firebomb and the smoke vial, plus the `bench_abilities` alchemist
column. **The villain layer's first slices are in (2026-07-19)** — karma & heat,
the shadow board, the punishment posses, the hell pact and its capers.
Next per plan.md's villain roadmap (reordered 2026-07-19): play the dark
path first (the no-code tone probe), then **nemesis persistence** (the
cheap, high-leverage slice — a surviving posse leader who returns with a
face and a grudge), then conquest ticking. The old magic-phase remainder
(stat transcendence + the wraith, armor — designer lean: probably never
important — named weapon instances) still stands behind that, along with
the career sim's finding that the 14-20 band lacks its player power until
masterwork/magic-item content lands. See plan.md for the full roadmap and
the parked-ideas list.
