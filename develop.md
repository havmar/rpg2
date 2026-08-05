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
  `group_combat`, `long_rest`, `party_wiped`, the foe
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

## No backwards compatibility — ever (2026-08-04, designer directive)

This project has exactly ONE player: the designer. His loop is to playtest
until something big or breaking surfaces, change the game, and **start a
new game**. The game is in early development; optimizing it around old
saves would be optimizing the wrong thing. Therefore:

- **Save compatibility is never a design input.** Never write migration
  shims, lazy upgrades, or missing-key fallbacks whose only purpose is
  loading an old `save.json`. When a better key name or state shape wins,
  take it and let old saves break.
- **Old-save round-trip tests are historical.** Several suites assert that
  a pre-slice save loads clean (`test_conditions`, `test_wounds`,
  `test_mercy`, `test_weapon_gen`, `test_conquest`) — those assertions
  documented past caution, not a standing requirement. Delete them (and
  any lazy-upgrade branch they cover) whenever you touch their files;
  never add new ones. `ensure_weapon_layer` — the named example — went
  in session C of the dark rework; worldgen has armed every world since
  2026-07-28.
- **Optimize for the good game.** If a change is better for play and
  breaks every existing save, it is simply better. The same spirit applies
  inside the codebase: refactor freely — the test suites and benches are
  the safety net, not frozen interfaces.

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
  up: the world & NPC simulation thread — the 2026-08-05 framing lives
  there; its two ready specs shipped the same day, so what is left is the
  settlement trim and the design session), plus parked ideas and open
  questions.
- `benchlog.md` — **the dated tuning history**: the full report of every
  measured bench-suite run, oldest first. Append a dated entry after every
  re-measurement; the "Balance / tuning" section below keeps only the
  current summary.
- `designlog.md` — **the dated design-session history** (2026-07-19):
  what was discussed, the road the discussion took, what was decided —
  the reasoning trail behind plan.md's decisions, so settled questions
  stay settled. Append an entry after every major design session.
- `placegen.md` — **the implemented place-generation MVP specification**
  (2026-07-23; content specification and implementation completed
  2026-07-25): the
  authored-vs-generated boundary, persistent feature and lightweight
  Room-content schema, weighting/reveal/mutation/seed rules, implementation
  order, and the canonical pre-implementation content catalog. All six
  settled MVP Lands — Dvarvengrond, Firascir, Mortellaria, Ensimaa, Gibili,
  and Tergal — have finite Area inventories, basic natural and settlement
  Site/Room layouts, generated-village roles, house overlays, and ordinary
  content pools. Its historical implementation contract fixes record fields,
  stable materialization, quest routing, readouts, and minimum verification.
  Pirate, wilderness, Caelum, and special-feature content remain post-MVP;
  shipped behavior belongs in `rules.md`.
- `places.py` — **the procedural-place runtime**: loads the immutable catalog,
  derives stable BLAKE2 child seeds, creates the six Lands and finite Areas,
  materializes required settlements/lazy natural Sites/ordinary houses,
  resolves Room contents, tracks knowledge, and applies place-state mutation.
- `place_catalog.json` — **the checked-in ordinary place catalog** extracted
  from the accepted concrete content in `placegen.md`: all six Land/Area
  records, required settlement Site/Room skeletons, natural three-Site
  inventories, generated-village roles/names, adjacency, and river/routes.
- `test_places.py` — **the place-generation MVP contract suite**: counts,
  IDs/names, deterministic seeds, finite discovery, lazy persistence,
  services/content, house constraints, quest routing/state transitions,
  hidden facts, ASCII, and 40-column display wrapping.
  `python -m unittest -v test_places.py`.
- `test_potions.py` — the QUARTERMASTER PASS contract suite (2026-07-26):
  the deal order and round-robin, the companion tiebreak, the lone hero,
  recovering the fallen's kit, the fight-only drink fence (`drink=`), the
  drink thresholds and the deal/drink alternation, the PC's
  healing-spell / War-Breath / Berserk gate, and the one-line hand-over
  report inside the 40-column wrap.
  `python -m unittest -v test_potions.py`.
- `test_conditions.py` — the CONDITIONS framework contract suite (2026-07-26,
  slice 3a): the bounded stacking rule (refresh, never sum, untimed wins),
  the tick's arithmetic and its position after regen, the never-kills-only-
  Downs guarantee, the side-worded fall lines (the bench greps depend on
  them), the one-collapsed-quiet-line-a-round display, what
  `_clear_fight_states` / the field stabilize / a healing potion / the night
  each clear, the two shipped customers (and the assertion that nothing else
  in the catalog carries a rider), and the save round-trip including a
  pre-slice save with no `conditions` key.
  `python -m unittest -v test_conditions.py`.
- `test_wounds.py` — the WOUND system contract suite (2026-07-26, slice 3b):
  the location table and its 15% vital fraction, the accrual table (and the
  graze that deliberately records nothing), the bounded deepening, the
  maiming rule and its one condition, the asymmetry (heroes record, foes
  never do — including the assertion that a foe costs no rng call), the HP
  ceiling and its half-pool floor, the stat fold's idempotence and its
  floor, every rung of the treatment ladder and what each can and cannot
  reach, the bleed re-derivation, the morale drain, the save round-trip
  (including a pre-slice save with no `wounds` key), and the 40-column fit
  of every authored wound name.
  `python -m unittest -v test_wounds.py`.
- `test_mercy.py` — the DEFEAT / FEROCITY / FATE contract suite
  (2026-07-26, slice 4): catalog bands and 40-column tags; humanoid spoils,
  beast maiming, relentless wipes and the non-cumulative one-mercy-per-level
  allowance; LAW using that same allowance; Fate-paid duo and depleted-party
  victories; the special Fate interrupt consuming the ordinary pause in both
  orderings; reverse foe retreat; and old/new save compatibility.
  `python -m unittest -v test_mercy.py`.
- `test_ui_logs.py` — focused contracts for the committed last-fight
  snapshots (new-fight replace, pause/resume append, short/detailed split,
  `sheet` path registration) and exact quest-level readouts.
  `python -m unittest -v test_ui_logs.py`.
- `scene-example.md` — **the worked scene-page model** (2026-08-05): a game
  start and a fight turn in writing.md's voice and dm.md's scene-page format
  (the one-turn page shown in two successive states, fenced displays, the
  start+link+end fight shape).
  Referenced by dm.md and writing.md; it is play-facing copy, so it follows
  the page rules itself (displays fenced at 40 columns, prose unwrapped,
  markdown for structure only, ASCII).
- `placegen_review.txt` — **the current string-review worksheet**: a minimal,
  translation-style view of one Land's player/DM-facing names, descriptions,
  Site and Room labels, and visible content strings. It carries only enough
  context to identify each string; schema, rationale, constraints, and process
  live in `placegen.md`. It currently preserves the completed Firascir /
  temperate human basic pass as the last dedicated review record. No further
  Land worksheet blocks the MVP implementation; reuse the format for focused
  wording or later special-feature review when useful.
- `AGENTS.md` — **the auto-loaded dispatcher**: the play/dev mode fork and
  the doc pointers, nothing else. It is injected into EVERY agent session,
  including play (Claude Code imports it through `CLAUDE.md`; Codex CLI and
  other AGENTS.md-aware agents read it directly) — keep it short and
  register-neutral; shared fiction style belongs in writing.md, dev content
  in this file, and play protocol in dm.md.
- `CLAUDE.md` — **a thin shim** that imports `AGENTS.md` so Claude Code
  loads the same dispatcher; put no content of its own here.
- `rpg.py` — **the engine.** Combat (`group_combat` + the pause/retreat
  layer), weapons and breakage, the survival tracks and the NIGHT (the short
  rest is gone since 2026-07-26), progression,
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
  rules.md's Alchemy & the Potion Rework add-on), the QUARTERMASTER PASS
  (2026-07-26: `auto_potions` and its helpers — the out-of-combat potion
  deal and auto-drink, played sessions only), the CONDITIONS framework
  (2026-07-26, the attrition rework's slice 3a: `Condition`,
  `Entity.conditions` / `Entity.inflicts`, `apply_condition` /
  `clear_conditions` / `_tick_conditions` / `_stabilize` — rules.md's
  Conditions add-on), the WOUND SYSTEM (2026-07-26, slice 3b: `Wound`,
  `Entity.wounds` / `records_wounds` / `hp_ceiling`, the accrual in
  `_attack` and the maiming rule, the treatment ladder's `heal_wounds` /
  `healer_service` / the salve and elixir tiers, `wound_morale`, and
  **`HERO_PAIN` 2 -> 3, the budget shift** — rules.md's Wounds & Recovery
  add-on), DEFEAT WITHOUT DEATH (2026-07-26, slice 4:
  `Entity.mercy_level` / `ferocity` / `withdrew` / `fate_paid`,
  `party_defeated`,
  `apply_defeat_mercy`, reverse retreat through `attempt_foe_retreat`, and
  Fate's paid-victory restoration), and the batch-sim
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
  rpg.py's site formulas), the Slice 4 `FoeSpec.ferocity` content bands and
  their roster tags, and `run_site`, the one site loop the one-shot
  run and the batch sims share. **Both sites are set encounters — the DM
  never invents their rosters — and since 2026-07-13 they are DEV/TEST
  calibration content only, no longer part of a played campaign** (the
  generated board covers the band; the benches still run them).
  One-shot: `python sites.py [--site
  hideout] [--seed N] [--training N]`.
- `quests.py` — **the quest & encounter generator over persistent places**
  (rules.md, the Quest System and World & Navigation add-ons): tree
  accessors, the threat math (all constants at the top, calibrated by
  `bench_quests.py`), concrete quest Room builders, the
  `QUEST_PLACE_REQUIREMENTS` tag/template routing layer,
  and per-race quest
  templates with reskin tables (since 2026-07-12 each also authors a
  `giver` role and an `epilogue` line; since 2026-07-26 a
  `failure_epilogue` too), the QUEST CLOCK and the banded lazy refill
  (2026-07-26, slice 2: `stamp_quest_clock` / `quest_band` /
  `quest_expired` / `expire_settlement_board` / `refresh_settlement_board`
  / `release_quest_places` / `next_quest_id` — rules.md's Quest System,
  "The clock"), and seeded worldgen, which now posts ONE job per
  settlement and stops (the asserted XP coverage to the level cap is
  DELETED — expiry made the assert a lie) — and which since 2026-07-12 also
  attaches a generated giver face to every quest (`attach_giver`) and casts each
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
  `record_karma` / `karma_line`), the quest templates + `roll_dark_quest`
  (lazy — worldgen never sees a dark quest; `spread` leans hell's
  assignments upward, `template` pins the deck's card),
  and the punishment posses (`POSSE_BANDS` /
  `build_posse`: ladder rosters wearing lawful display names, a
  generated leader face). **The hell pact (same day, second slice —
  rules.md's "The Hell Pact"):** `new_pact` (which shuffles the pact's
  DECK off the run's rng) + `deal_card`, the assignment/enforcement
  knobs (`TASK_PIN_LEVELS`, `TASK_GRACE_DAYS`, `TASK_SPREAD`,
  `TASK_WINDOW_DAYS`, `ENFORCE_*` incl. `ENFORCE_SPREAD`, `BRIBE_*`,
  `DEED_FAIL_KARMA`, `HELL_MAIL`), the hell collections posse
  (`HELL_SKINS` / `build_hell_posse` — Past Due; ONE visit since
  2026-08-04, was an escalating ladder), and
  the CAPER schema on templates (`deed` = 2d6+stat vs DC gate, `twist`
  = priced terms).
  **The 2026-08-04 template sort** (THE DARK REWORK, session A):
  `OCCULT_TEMPLATES` is the pact's ten-card deck and the ONLY list any
  roll draws from; `CRIME_FODDER` is the fifteen retired crime
  templates, rolled by nothing and kept as authored scene material --
  since 2026-08-04 they are what `crime.py` dresses a mark's protection
  in. Also the NEWS CYCLE (same day, session B): `NEWS_DAYS`, the
  `hot_until` karma key, `heat_step` / `in_the_news`, and the optional
  `day` on `heat` / `record_karma` / `karma_line` that a big single sin
  stamps and a heat floor of 1 reads. All
  other knobs at the top (`KARMA_HEAT_STEP`,
  `HEAT_CAP`, `PUNISH_*`; the dark gold premium
  `DARK_GOLD_MULT` sits in quests.py with the pay knobs). The sims
  never import it. `python karma.py [--seed N]` prints a shuffled deck,
  sample assignments and posses (the eyeball check).
- `conquest.py` — **the domain layer: player conquest** (2026-07-27,
  rules.md's Conquest & Holdings add-on): fixed stable-seeded garrison
  levels (village 3-5 / town 6-10 / capital 11-15), the garrison-job
  builder (`build_conquest_quest` -- an ordinary dark quest with a named
  defender over the strongest slot, no clock, never on the board), the
  holdings ledger (`take_settlement` / `lose_holding`), tribute accrual
  and collection, the lazy crown raids (`roll_raids` -- heads against
  heads, the engine never sees them), the story-occupation seizure, and
  `heat_floor`. The sims never import it; every knob is hand-set (the
  karma layer's doctrine). `python conquest.py [--seed N]` dumps every
  settlement's garrison level and one built job.
- `test_conquest.py` — the CONQUEST contract suite (2026-07-27): garrison
  bands and stability, the merged city tier, the job's shape/pricing/boss,
  the holding ledger flips, tribute arithmetic, raid resolution (full
  garrison always repels; unguarded always falls; present party is never
  raided), the yoke's seizure, the save round-trip, display fit.
  `python -m unittest -v test_conquest.py`.
- `test_pact.py` — the HELL PACT assignment-ladder contract suite
  (2026-08-04, THE DARK REWORK session A): the template sort (occult ten
  vs. inert crime fodder — nothing rolls from the fodder), the per-save
  deck (shuffle, one card per pin, band-fitting, skipped cards kept,
  the nearest-band fallback), the pin schedule (odd levels, never
  stacked, the highest crossed pin served once), the deadline clocks,
  the punishment-budget knobs, and the write-off (`withdraw_assignment`:
  the job leaves the world, its sites are released, `defied` ticks, the
  next pin is not jammed). `python -m unittest -v test_pact.py`.
- `crime.py` — **the crime layer: free ACTIONS against a leveled world**
  (2026-08-04, THE DARK REWORK's session B; rules.md's Crime add-on is
  the doc of record, dm.md the table manner). Crime stopped being a quest
  in session A; this is what replaced it. The MARK BANDS (`MARK_BANDS` —
  level fixes wealth AND protection, availability by place kind, the
  wilds admitting the bands that travel), the 27-category CATALOGUE
  (`CATEGORIES` / `BY_KEY` — 5 petty, 10 deeds, 12 force, each declaring
  its shape, check, bands, pay kind, multiplier and the retired
  `karma.CRIME_FODDER` template whose roster and skins dress its
  protection), the seeded mark roll (`roll_mark` / `npc_mark` /
  `build_mark` off `places.stable_seed` — casing is free AND honest
  because `case` and `crime` share the stream), the take formulas
  (`take_of` — `CRIME_XP_PER_LEVEL` 50, `CRIME_GOLD_PER_LEVEL` 20,
  `FENCE_RATE` 0.5, flat `PETTY_SIN`/`PETTY_GOLD`), the monotony window
  and first-time bonus (`sin_mult` / `monotony_mult` / `stamp` /
  `recent_days` — temporary by construction, sin and XP only, never
  gold), and the unlock ledger (`new_crimes` / `record_for` / `peek` /
  `refresh_unlocks` / `suggestions` — optionally SHUFFLED off a passed
  rng since session C — / `tally_rows` / `total_crimes` — suggestions,
  never permission; the tally reads the record's own `last` day, never
  the monotony window's self-pruning day stamps). All knobs hand-set;
  the sims and benches never import it.
  `python crime.py [--seed N]` prints the catalogue and one day's local
  marks at each place kind (the eyeball check).
- `test_crime.py` — the CRIME contract suite (2026-08-04, session B): the
  catalogue's shape and the fodder it recycles, the mark bands and their
  place gating, the casing guarantee (stable per settlement/day/category,
  fresh tomorrow), the take formulas including the fence rate and petty's
  flatness, monotony's temporary window / floor / per-category
  independence and the first-time bonus, the unlock ledger (grants from
  assignments and lifetime sin; a by-deed unlock eats no grant; `peek`
  never writes), the news cycle's heat floor and petty's exemption from
  it, the 40-column fit of every authored string, and the session wiring
  (the take rides `pending`, the ledger is a save key).
  `python -m unittest -v test_crime.py`.
- `test_history.py` — the CAMPAIGN RECORD contract suite (2026-08-04,
  THE DARK REWORK's session C): `session.remember` (the day stamp, the
  two kinds, the duplicate guard, the per-kind trim), the named-kill and
  maiming scanners, the four sections of `ui/history.txt` and their
  40-column/ASCII fit, the page's place in the save/`sheet` lifecycle,
  the tally's honesty about a category's last day, the seeded
  suggestion order, the `crimes` sheet's band quotes, and the SIN
  RENAME (the karma keys, the display words, the `sin` command with no
  `karma` alias — read off `session.build_parser`).
  `python -m unittest -v test_history.py`.
- `test_start.py` — the GAME START contract suite (2026-08-05, plan.md's
  specs A and B): the level roll (`1..START_LEVEL_ROLL_MAX`, seeded, and
  `--level` / `--race` with their refusals), the PC's two guarantees (the
  gift always, the sketch never — plus the asymmetry that motivates them:
  a wizard trains steel, a warrior can never learn a spell), the career a
  level-N start arrives with (doctrine points, the reward weapon and the
  focus-staff rule, the spellbooks, the purse, the opening kit), hell's
  stamped ledger, the opening ground, and the trait rollback across every
  casting path (givers, recipients, notables, service faces, posse
  leaders, residents, smiths). It drives `cmd_new` end to end against a
  temp save — never the playthrough's.
  `python -m unittest -v test_start.py`.
- `weapons.py` — **the weapon generation system** (2026-07-28, rules.md's
  Weapon Ladder & Generation add-on): the severity-point price table and
  `weapon_sp`, the budgeted generator (`generate_weapon` — profile rule,
  riders, quirks, the +DEX legendary gate), the quest reward ladder
  (`reward_weapon_for_level`), the famous armory (`roll_armory`), the
  legendary smiths (`roll_smiths` / `commission_weapon` — the pride
  floor), and the 40-column readouts. The sims never import it; worldgen
  calls it on DERIVED rngs so no bench stream moves. `python weapons.py
  [--seed N]` prints one world's armory, smiths, and sample commissions
  (the eyeball check).
- `test_weapon_gen.py` — the WEAPON GENERATION contract suite
  (2026-07-28): the sp identities (the quality four price at exactly
  3 sp), generator budget honesty and the profile rule, the +DEX gate,
  masterwork shape/price/shop doctrine, equip/unequip symmetry over every
  bonus, the rider and rime hooks, the on-kill quirk counters and their
  per-fight cap, proficiency-follows-the-chassis (and the reskin
  exception), old/new save round-trips, armory determinism and 40-column
  fit, the smiths' pride floor, the reward ladder, the trash chargen
  pool. `python -m unittest -v test_weapon_gen.py`.
- `people.py` — **the character layer** (2026-07-11, rules.md's Party,
  Charisma & Satisfaction add-on): the five races' stat modifiers
  (floor-raise `RACE_MODS`; since 2026-07-13 also the goblin STR ceiling
  drop `RACE_MODS_CEIL` and the race trait substitutions
  `RACE_TRAIT_SUBS`), the 25+25 per-race name pools, the trait
  tables (1 behavior + 2 presentation categories per character; the
  mechanical few annotated in `TRAIT_NOTES`; looks pool widened
  2026-07-13) — **COMPANIONS only since 2026-08-05**: `with_traits=False`
  is the PC's setting and dict NPCs never roll one (the rollback; it
  retired the old `no_family` switch, which existed to keep a child out
  of the PC's opening scene), `make_character` (any
  level, via rpg.develop_hero; `wizard=True` rerolls the stat budget
  until the gift lands — the PC is always a magic user),
  `make_pair` (bonded recruit pairs), the
  candidate sheets, and the downtime-matching rules; since 2026-07-12
  also `make_npc` / `npc_line` (the TARGETED generator: the caller fixes
  race/role/sex/age and optionally a level, the dice roll the name —
  dict NPCs, no stat blocks, no sketch, `NPC_MIN_AGE` floors anyone with
  a job title). Content
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
  `go` / `back` / `explore` / `house` / `place-state` / `hunt` / `engage` —
  breadcrumb position, finite Area/Site discovery, persistent ordinary
  houses, DM mutation,
  macro and local navigation, local boards, road encounters;
  since 2026-07-10 also `tavern` (the paid settlement night with
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
  GENERATES the PC (no `pick`; min capacity 1, the long-time companion,
  the OPENING HOOK at the closest-level-quest settlement, aggressor
  excludes the PC race — and since 2026-08-05 a rolled start level, an
  always-wizard PC and no trait sketch on him), `recruit` rolls candidates
  ON REQUEST (once per settlement/day; the tavern stopped popping them),
  companions AUTOLEVEL after fights/hire (`rpg.autospend_points`) while
  the PC's level-up auto-prints the `levelup` menu, `maybe_post_wave` is
  settlement-gated (no war news mid-wilds), a dead companion's quality
  weapon stays with the party, `give --as` reskins weapons, ALL output
  (and the UI pages) is hard-wrapped at `WRAP_WIDTH` = 40 for the
  designer's phone, and the **UI pages in `ui/`** are committed only by
  **`sheet`** — the end-of-every-DM-message command (one commit per message;
  best-effort git, never fatal). **`ui/party.txt`** (`party_sheet_lines` —
  the full party board) and,
  since 2026-07-22, **`ui/map.txt`** (`map_sheet_lines` — lands, known areas
  with settlement open-job counts + a visited/here marker, and, until the
  planned `ui/minimap.txt` takes over local detail, the sites of every TAKEN
  quest with
  its progress cursor; `accepted_quests` gates it on the new `accepted`
  save key — offered-but-untaken jobs never appear) and, since
  2026-08-04 (session C), **`ui/history.txt`** (`history_sheet_lines` —
  QUESTS DONE / REMARKABLE / THE TALLY OF SIN / SUGGESTIONS, over the
  `history` save key that `remember` writes and `_note_maimings`
  re-scans into) are rewritten on every
  save. Combat writes two last-fight snapshots:
  **`ui/fight-short.txt`** (the exact displayed log and DM fallback) and
  **`ui/fight-detailed.txt`** (every roll and modifier). A new encounter
  replaces them; resume/retreat appends to the paused encounter. Since
  2026-08-05 the DM's message itself is a page too: **`ui/scene.md`**
  (the current turn, rewritten whole) and **`ui/transcript.md`**
  (the append-only play log) are DM-AUTHORED — the engine never writes
  them, `sheet` just commits them (`UI_COMMIT_PATHS`; dm.md, The scene
  page; the worked model is `scene-example.md`). Rendered markdown, not
  txt — the app character-wraps raw text blobs — with every display in
  a code fence. The page is the DRAFTING surface, not a substitute for
  the chat: the reviewed turn is copied back into the chat message
  verbatim, with the page link under it, and the page keeps that one
  turn only — the chat scrollback is the lookback, the transcript is
  the record. All seven
  are **committed to the branch, not gitignored: they are the GitHub UI**
  (blob links, dm.md); only `save.json` stays untracked.
  Encounter commands print ONE log since 2026-07-21 (the log rework):
  the player-facing display whose opening and closing blocks the DM
  copies onto the scene page — the round-by-round middle stays behind
  the `ui/fight-short.txt` blob link (dm.md, 2026-08-05) — while the
  detailed version goes to **`ui/fight-detailed.txt`**
  (`group_combat` flushes the configured log at pause/resolution and
  `print_combat` flushes both snapshots' session tail). The block ends with the
  party tally (`tally_lines`: tracks, standing roll penalties -- shown
  HERE and in the pause menu since the fight lines dropped the numbers
  -- kit/purse, fights-left count and the turn-in quote), the standard
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
  too (the free-allocation doctrine: no class gate). Since 2026-07-26 the
  QUARTERMASTER PASS is dispatched from here: `rpg.auto_potions` is called
  at every out-of-combat point where the potion stock changes (see the dev
  map), so `use` became an override rather than the routine step. Also
  since 2026-07-26 (slice 3b) the WOUND surface: **`healer`** (the day
  with the settlement's healer — the treatment ladder's access rung),
  `bed=True` on the settlement night paths (`downtime`, `camp` behind
  walls; `tavern_rest` passes it in the engine), `camp --heal` stopping at
  the wound CEILING instead of at full, the `wound_tags` readouts and the
  banded `hp_state` word across `tally_lines` / `cmd_status` /
  `party_sheet_lines` / the pause menu, and the salve/healer rows in
  `prices`. The 2026-07-28 display pass rebuilt the two hero readouts
  for the 40-column phone: `hero_block_lines` (shared by
  `party_sheet_lines` and `status` — a header plus short labeled rows
  hanging two spaces, replacing the old 12-space alignment column) and
  the standardized `print_levelup_menu` (fixed command-headed sections,
  a right-hand cost column with the `*` affordability mark, and a
  one-line brief under every buy — rpg.py's `Ability.brief` /
  `Move.brief`; the full blurbs stay the learn-time text). Since
  2026-07-28 also the WEAPON-LAYER surface: the trash chargen deal in
  `cmd_new`, `buy HERO masterwork WEAPON` (capitals), `claim HERO` (the
  weapon-reward turn-in, `pending_reward` in the save), `armory` (the DM
  inventory of famous weapons + smiths), `commission SMITH HERO
  [CHASSIS] [--sp N]`,
  and `collect_weapon_quirks` (fight-end and retreat paths: Midas gold
  to the purse, dark kills to the karma ledger). Since 2026-08-04 the
  CRIME surface (THE DARK REWORK's session B): `case [KEY]` (the free,
  honest casing report and the local catalogue) and `crime KEY` (the
  commission -- petty / deed / force), both taking
  `--npc NAME --level N` to put a named victim on the table, plus the
  `crimes` save ledger and the suggestion feed that rides the settlement
  scenes beside `conquest_news`. Session C (same day) added the SURFACE:
  **`crimes`** (`cmd_crimes` / `take_span` — the `prices` pattern for
  the dark side: the local catalogue quoted at the mark BAND, then the
  tally and the feed), the **`sin`** command (`cmd_sin`, replacing
  `karma` with no alias — the bad-karma-to-SIN rename runs through the
  save keys and every display string), the campaign record
  (`remember` / `history_sheet_lines` / `_write_history_sheet` /
  `_named_dead` / `_note_maimings`), and `build_parser`, split out of
  `main` so the command surface is testable.
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
python weapons.py --seed 1            # one world's armory + smiths (eyeball)
python -m unittest -v test_weapon_gen.py  # the weapon generation contract
python -m unittest -v test_places.py  # procedural-place MVP contract
python -m unittest -v test_potions.py # the quartermaster pass contract
python -m unittest -v test_conditions.py  # the conditions framework contract
python -m unittest -v test_wounds.py  # the wound system contract
python -m unittest -v test_mercy.py   # defeat, ferocity, and Fate contracts
python -m unittest -v test_ui_logs.py # fight snapshots + exact quest levels
python -m unittest -v test_conquest.py # the conquest domain layer contract
python -m unittest -v test_pact.py    # hell's assignment ladder contract
python crime.py --seed 1              # the crime catalogue + local marks
python -m unittest -v test_crime.py   # the crime layer contract
python -m unittest -v test_history.py # the campaign record + the sin rename
python -m unittest -v test_start.py   # the start level, the wizard PC, traits
```

Use `PYTHONIOENCODING=utf-8` when piping output (Windows cp1250 default). Output
is intentionally ASCII-only, so plain runs are usually fine.

## The dev map (where mechanics live in the code)

The one-screen index for finding the thing you need to change. What each
mechanic *does* and *why* is rules.md's job.

- **Tunable constants** — all at the top of `rpg.py`, grouped and commented:
  fatigue (`WINDED_STA`, `SPENT_PENALTY`, `STA_ATTACK_COST`), survival
  (`SAVE_COST`, `FIRST_BLOOD_*`, potion restores, `REVIVE_HP`, and the
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
  TWO level-pay ladders, deliberately separate since 2026-07-26 and
  commented so nobody unifies them: the QUEST ladder `quest_xp_total` /
  `quest_encounter_xp` / `quest_clear_xp` / `quest_gold` with
  `QUEST_XP_PER_LEVEL` / `QUEST_GOLD_PER_LEVEL` / `ENCOUNTER_MULT` /
  `QUEST_ENCOUNTER_SHARE` — this is the GAME's pay — and the site-FIXTURE
  ladder `site_xp_total` / `site_encounter_xp` /
  `site_clear_xp` / `site_gold` with their `SITE_XP_PER_LEVEL` /
  `ENCOUNTER_XP_SHARE` / `GOLD_PER_SITE_LEVEL` knobs, which now serves only
  sites.py's two hand-built calibration fixtures), weapons (the
  `WEAPONS` catalog, `BREAK_CHANCE_PER_GAP_SQ`, starting-weapon chances;
  since 2026-07-28 also the weapon-ladder block — `MASTERWORK_*`,
  `TRASH_WEAPONS`, `MIDAS_FIGHT_CAP` — plus `prof_name` /
  `masterwork_of` / `random_trash_weapon` beside the catalog, the
  `Weapon` magic knobs (stat bonuses, `rider`, `lunge`, the on-kill
  quirks), the full equip bookkeeping in `equip_weapon`, the wielder
  rider hook in `_attack`, and the lunge branch in `group_combat`; the
  sp PRICES live at the top of `weapons.py`),
  hero stat generation (`HERO_*_RANGE` + `HERO_STAT_BUDGET` — since
  2026-07-13 a fixed surplus budget dealt by a shuffled priority order,
  not independent rolls; 11 since 2026-07-15, when MIND joined the
  budget) and the hero spiral gear (`HERO_PAIN`
  — trained fighters, both sides, take `hp_lost // 2` as the wound
  penalty since 2026-07-09), the magic layer
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
  `PACK_CAP`, `BOSS_ALLOWANCE`, the quest-clock block `QUEST_WINDOW_DAYS` /
  `QUEST_QUICK_SHARE` / `QUEST_GRACE_DAYS` / `QUEST_PAY_BANDS` /
  `QUEST_REFILL_PER_DAY`, settlement bands), and
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
  are re-armed, not silently spent). Fate's bargain (revised 2026-07-26)
  lives here too: the fall
  handler commutes a protagonist's death to a Down (`Entity.protagonist` /
  `fate_debt`; session marks `party[0]`). If the encounter pause is unused,
  Fate returns `Pause(kind="fate")` and spends it; an earlier ordinary pause
  suppresses that interrupt, and a Fate pause suppresses every later ordinary
  one. `_settle_fate_debt(..., fled=False|True)` collects one companion's life
  on EVERY ending — won, lost, staggered apart, or fled (2026-07-29: the debt
  is unconditional; nothing waives it) — and restores the PC to exactly 1 HP
  without touching wounds or other damage. Four call sites: the melee tail in
  `group_combat`, both clean-escape branches of `attempt_retreat`, and
  `blink_escape`. A FAILED break is the only deferral (the fight is not over).
  The restoration is also what bars the level's defeat mercy:
  `party_defeated` is false by the time `apply_mercy` is reached.
- **Retreat** — `attempt_retreat` (parting blows — softened one wound tier
  since 2026-07-10 (`_attack(soften=True)`): the door maims, never kills
  outright — + ONE group chase roll; `pursues=False` foes never chase; a
  clean escape SETTLES any fate debt), `attempt_foe_retreat` (the same chase
  contest reflected across the field for ferocity-0/1 rosters; survivors are
  `withdrew`, not dead), and `refresh_foes_after_retreat` (fled-room
  persistence).
- **The quartermaster pass** (2026-07-26 — rules.md's Gold and the potion
  economy, "The quartermaster pass") — `rpg.py`: `AUTO_POTION_KINDS` (in
  the potion-economy constants block), `wants_potion` (the badly-hurt /
  Winded lines, now shared with `auto_use_potions_on_rest` — the sim
  policy's numbers are unchanged), `drinks_own_potions` (companions always;
  the PC only without the healing spell / War-Breath / Berserk on that
  track), `_potion_need`, `deal_potions` (pool → worst-off-first
  round-robin, ties to companions, silent and idempotent),
  `recover_potions_from_the_fallen` (a dead companion's vials go back to
  the party — the quality-steel doctrine), `_kit_line`, and
  `auto_potions` — the recover/deal/drink/deal loop and the ONE entry
  point. **`drink=` is the fight-only fence** (designer call, 2026-07-26):
  it defaults to False, so every call DEALS and only the encounter paths
  pass `drink=True`. A camp/shop/morning drink was the wrong trade — the
  night heals free, so the vial is worth more unopened.
  `session.py` calls it wherever the stock changes out of combat, and those
  call sites are the trigger list: `finish_encounter` and `cmd_retreat`'s
  escape branch (**the two `drink=True` sites**), plus deal-only at
  `cmd_new` (the opening kit),
  `night_upkeep` (every night path, after the rest and the brew),
  `cmd_buy` / `cmd_use` / `cmd_brew` (all gated on the primitive actually
  succeeding), `cmd_hire`, `cmd_dismiss`, `process_departures`. The sims
  and one-shots do NOT run it (`sites.run_site` keeps
  `auto_use_potions_on_rest`) — a deliberate divergence, so tune/bench
  numbers keep describing the party they were calibrated against;
  `sites.py --seed 3` and `bench_training.py` were diffed byte-identical
  across the change.
- **Between fights** — `long_rest` (the `Clock`; long_rest
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
  last-fight snapshots added 2026-07-26): the list itself is the detailed
  log (never printed in play; session-created logs target
  **`ui/fight-detailed.txt`**); `.player` is THE display and targets
  **`ui/fight-short.txt`**. New fights overwrite both, while
  resume/retreat logs append; `group_combat` flushes detailed mechanics at
  pause/resolution, then `session.print_combat` flushes both appended
  session tails and prints only `.player`. The player level is
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
  `level` annotation, `ref_pack`, for the drilled soldiery a `training`
  rank, and since 2026-07-26 an `inflicts` condition rider on exactly two
  rows — the great spider's venom and the pyromancer's clinging fire),
  `NATURAL_WEAPONS` (fangs/claws — never break, never loot),
  `make_foe` (+ the `display` reskin hook), `SITES`, `HIDEOUT_ROOMS` /
  `BARROW_ROOMS`, `run_site` (the sim loop), `roster_lines`,
  `WEAPON_INDEX` (name -> Weapon, the save file's reference table).
- **Generation** — `quests.py`: `threat_value` / `build_room` /
  `build_site_rooms` (the threat math), `TEMPLATES` / `EPIC_TEMPLATES`
  (the per-race quest tables + reskins), `build_quest` / `forge_quest`,
  `generate_world` (the one-job-per-settlement SEED since 2026-07-26),
  `quest_to_sites` (generated
  quest -> `Site` instances for the sims), the board readout helpers.
- **The quest clock & the live board** (2026-07-26, the attrition rework's
  slice 2 — rules.md's Quest System, "The clock") — `quests.py`: the
  constants block, `stamp_quest_clock` / `quest_days_left` / `quest_band` /
  `quest_pay_mult` / `quest_expired` / `deadline_note` / `failure_line`,
  `next_quest_id` (the world's monotonic id counter, `world["quest_seq"]`),
  `release_quest_places` (a dead posting gives its Sites back),
  `board_slots` / `open_quests` / `expire_settlement_board` /
  `refresh_settlement_board` / `refresh_deliveries`, the `day` parameter on
  `quest_line` / `board_lines` / `quest_detail_lines`, and the
  `failure_epilogue` field on every good/epic/delivery template.
  `session.py`: `board_clock` / `print_board_clock` (called at EVERY day
  advance — travel out and travel in, explore, each camp night, tavern,
  downtime — and on `board`), `_remember_failure` / `take_failure_rumors`
  (the settlement's `rumors` list, told once), the band multiplier in
  `_close_site` and `deliver_if_arrived`, the clock lines in `tally_lines` /
  `cmd_status` / `cmd_take` / `party_sheet_lines`, `open_quests` in
  `map_sheet_lines`, and `forge --days N`. `karma.py` and `story.py` post
  jobs with NO clock on purpose (day-scoped shadow offers; an authored
  questline does not lapse). `bench_quests.py`: `run_board_clock` and the
  banded turn-in in `run_career`. `people.py`: `pick_name` numbers its
  overflow (`Brand II`, `Brand 3`) instead of choosing from an empty pool —
  a churning board asks for far more faces than the 25-a-race/sex pools
  hold, and the giver namespace is now the names IN USE (recomputed in
  `board_clock`), never a persisted ledger.
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
  decided it) plus the "Renegade Magus" epic. `session.py`:
  `train HERO SPELL`, `buy HERO book SPELL` (capitals),
  `cast HERO scry|teleport`, `resume --vanish`,
  `retreat --blink`, exact board/show/take levels (`show --dm` adds
  surprise complications), the `visited` save key
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
- **The world, places & navigation** (2026-07-09; hierarchy 2026-07-22;
  procedural-place MVP 2026-07-25) — `places.py` +
  `place_catalog.json`: independent Land/culture/owner/environment records,
  the finite 67-Area six-Land inventory, stable BLAKE2 child seeds, required
  settlement skeletons/services/providers, three-entry natural Site
  inventories, Room contents, ordinary houses, knowledge, links, and the
  explicit state mutation/event API. `quests.py`: the world-owned
  `lands` / `areas` / `sites` / `rooms` stores and tree accessors; quest
  Sites as persistent world IDs, `QUEST_PLACE_REQUIREMENTS` routing;
  `wild_pool`
  (what roams a land = the union of its race's template pools),
  `roll_wild_level` (the road's party-independent geometric level table),
  `build_wild_encounter`, `wild_encounter_xp`. `session.py`: breadcrumb
  `position` (`land`, `area`, optional `site`/`room`), `current_area` /
  `local_settlement` / `at_quest_origin` / `at_quest_site`; `cmd_map` and
  `ui/map.txt` as the macro Land/Area view; `cmd_look` / `cmd_go` / `cmd_back`
  as the local view and movement precursor to the planned `ui/minimap.txt`;
  `wild_event` (the one roll: nothing / fight / sighting), `cmd_travel` /
  finite `cmd_explore`, `cmd_house`, `cmd_place_state`, `cmd_hunt` /
  `cmd_engage`; `look --dm` is the complete place-fact readout.
- **Karma & heat** (2026-07-19, the villain layer — rules.md's Karma &
  Heat add-on) — `karma.py`: everything (see Files). `quests.py`: the
  `align` field on quest dicts (build_quest/forge_quest/deliveries),
  `DARK_GOLD_MULT` + the dark branch in `quest_gold_total` /
  `site_gold_for`, the DARK tag in `quest_line`. `session.py`:
  `party_level` / `record_karma` (the bucketing shim, called in
  `finish_encounter`, `advance_quest`, `deliver_if_arrived`, `cmd_award`),
  the `align` thread through `resolve_encounter`/`pending`/resume/retreat
  serializers, `maybe_punish` (called at travel arrivals and
  tavern/downtime/camp nights),
  `forge --dark`, `award --dark/--good`, `cmd_sin` (the `sin` command --
  was `cmd_karma`/`karma` before session C's rename), the sin lines in
  `tally_lines`/`cmd_status`, the `karma` save key (whose sub-keys are
  `sin` / `sin_total` / `penance_total` since 2026-08-04).
  (`roll_dark_board`, `board --dark` and the `dark_board` save key died
  2026-08-04 with the shadow board.)
- **The hell pact & the capers** (2026-07-19, second slice — rules.md's
  "The Hell Pact") — `karma.py`: the pact constants, `new_pact`,
  `HELL_MAIL`, `HELL_SKINS` / `build_hell_posse`, the `deed`/`twist`
  template fields (see Files). `quests.py`: `build_quest` pins a caper's
  site count and copies `deed` → first site / `twist` → last site; the
  deed/twist lines in `quest_detail_lines` (twist is DM-eyes-only).
  `session.py`: the `pact` save key (None = pactless; `new --no-pact`),
  `pact_task` / `pact_lines`, `pc_level` / `pending_pin` / `coming_pin`
  (the pin schedule), `maybe_assign_task` (arrivals, `board`,
  settlement nights) + `maybe_enforce` (the posse stops, after
  `maybe_punish`), `withdraw_assignment` / `close_hell_account` (the
  write-off, called from `finish_encounter` and the retreat path on any
  `mercy="hell"` fight), `cmd_task` / `cmd_bribe`, THE DEED + THE TWIST
  branches in `cmd_room`, `cmd_settle`, `_close_site` (advance_quest's
  tail split out: deed-skips and settles close sites through it;
  also the hell-task completion ledger), and the MERCY thread —
  `mercy` through `resolve_encounter`/`pending`/resume/retreat,
  `apply_mercy` (left for dead / the lesson), now spending the same
  one-per-level allowance as every ordinary mercy.
- **Crime — the free actions** (2026-08-04, THE DARK REWORK's session B
  — rules.md's Crime add-on) — `crime.py`: everything (the bands, the
  27-category catalogue, the seeded mark roll, the take formulas, the
  monotony window, the unlock ledger — see Files). `karma.py`: the NEWS
  CYCLE (`NEWS_DAYS`, the `hot_until` key on `new_karma`, `heat_step` /
  `in_the_news`, the stamp in `record_karma` and the floor in `heat` —
  all three now take an optional `day`, and the karma displays thread it
  through), and `CRIME_FODDER`, which crime dresses its protection in.
  `session.py`: `cmd_case` / `cmd_crime` (the whole play surface),
  `crimes_state` / `place_kind` / `place_id` / `world_seed`,
  `crime_news` (the suggestion feed — called wherever `conquest_news`
  is: travel arrivals, `board`, tavern and downtime nights),
  `local_mark` / `no_mark_line` / `case_lines` / `mult_note`,
  `crime_record` (books the commission and freezes the payoff numbers),
  `pay_crime` (the take, and every point of its XP as sin),
  `crime_fight` (the protection roster through `resolve_encounter`),
  `pc_levelup_prompt`, the `crime_take` thread through
  `resolve_encounter`/`pending`/`finish_encounter` and both resume
  serializers, and the `crimes` save key. `rpg.py`: `award_quest` grew a
  `reason` argument so the take's XP line reads "crime" instead of
  "quest" — the only engine-side change, and behaviourally a no-op
  (`sites.py --seed 3` and `bench_quests --part enc` were diffed
  byte-identical across the slice).
- **The campaign record & the sin rename** (2026-08-04, THE DARK
  REWORK's session C — rules.md's The Campaign Record add-on) —
  `session.py`: `remember` (the ONLY writer; the day stamp, the
  quest/remarkable kinds, the same-day duplicate guard, the per-kind
  `HISTORY_CAP` trim), `history_sheet_lines` /
  `_write_history_sheet` / `HISTORY_SHEET_PATH` (in `UI_COMMIT_PATHS`,
  written by `save` and `cmd_sheet` beside party/map), `_named_dead`
  (the by-shape named-kill detector, read in `finish_encounter`),
  `_note_maimings` (the scan, called at the top of `save` so it lands
  BEFORE the JSON dump), the `history` save key, and the `remember`
  call sites — `_close_site` (jobs done, waves, conquests, hell's
  assignments), `board_clock` (jobs lost), `deliver_if_arrived`,
  `withdraw_assignment` (write-offs), `apply_mercy` (all three defeat
  paths), `conquest_news` (holdings lost), `cmd_sin` (a NAMED
  off-script sin only). Also `cmd_crimes` / `take_span` (the crime
  price sheet) and `build_parser`, split out of `main`. `crime.py`:
  `stamp`'s `last` field (the tally outlives the monotony window),
  `total_crimes`, and `suggestions`' optional rng. The RENAME touched
  `karma.new_karma`'s keys and every display string across
  `karma.py` / `crime.py` / `quests.py` / `rpg.py` / `conquest.py` /
  `weapons.py` / `session.py`.
- **The game start at any level & the trait rollback** (2026-08-05,
  plan.md's ready specs A and B plus the designer's two amendments —
  rules.md's Party add-on, *The starting level* and *The player
  character*) — `session.py`: the start block
  (`START_LEVEL_ROLL_MAX` = 18, `START_QUESTS_PER_LEVEL`,
  `START_PURSE_SHARE`, `START_SPELL_LEVELS`, `start_level`,
  `career_purse`, `career_kit`, `_start_pact`, `career_line`),
  `cmd_new` rebuilt around them (the `--level` / `--race` flags and
  their refusals, the always-wizard trait-less PC, the trash arms now
  level-1 only, the war and pact lines that no longer promise level 2),
  `_starting_settlement(world, level)` and `opening_hook` picking the
  posting CLOSEST to the party's level (identical to the old
  lowest-posting rule at level 1), and `cmd_chatter` skipping heroes
  with no sketch. `people.py`: `make_character`'s `with_traits` /
  `wizard` switches (`WIZARD_ROLL_TRIES`), `roll_traits` minus
  `no_family`, `make_npc` minus the sketch (plus the optional `level`
  key), `npc_line`, `character_sheet` minus the dead `for_pc` switch and
  `SATISFACTION_NOTE_TRAITS`. `weapons.py`: `reward_weapon_for_level`'s
  optional `chassis` (the caster's staff). `quests.py`: the giver and
  recipient trait dumps deleted from `quest_detail_lines`.
  `test_start.py` is the contract suite. Nothing here touches the
  engine or the sims — bench numbers are untouched by construction.
- **The conquest domain layer** (2026-07-27 — rules.md's Conquest &
  Holdings add-on) — `conquest.py`: everything (see Files). `session.py`:
  `cmd_conquer` / `cmd_garrison` / `cmd_holdings`, `held_here` /
  `holding_board_line` (the honest board refuses in a held settlement;
  taverns/shops/hiring keep working), `effective_heat` (karma's meter
  floored by holdings — `maybe_punish` reads it, and prints the flag
  note when the floor drives the posse), `conquest_news` (seizures,
  raids, tribute — called at travel arrivals, tavern and downtime
  nights, and `board`), the flip hook in `_close_site` (a done quest
  with a `conquest` key), the `[YOURS]` tag + holdings section in
  `map_sheet_lines`, the summary line in `cmd_status`, and the
  `holdings` save key. `quests.py`: the "city" settlement tier was
  merged into "town" the same day (SETTLEMENT_KINDS; the catalog
  retiered Leehaven, Walhaven and Portomera) — `rpg.HEALER_TIER_CAP`
  lost its city row with it.
- **Defeat without death** (2026-07-26, attrition slice 4 — rules.md's
  Ferocity and Mercy section) — `rpg.py`: the ferocity constants,
  `Entity.ferocity` / `withdrew` / `break_tried` / `mercy_level` /
  `fate_paid`,
  `party_defeated`, `roster_ferocity`, `defeat_mercy_kind`,
  `mercy_available`, `apply_defeat_mercy`, `_chase_contest` and
  `attempt_foe_retreat`. `sites.py`: every `FoeSpec` carries a content band;
  humanoids are 0, most beasts 1, undead 2; hell enforcers and conquest waves
  override authored humanoids to 2. `session.py`: mercy runs before
  `party_wiped`, including a failed retreat, and LAW/HELL keep their special
  save reshaping while sharing the level allowance. `bench_quests.py` counts
  mercies and continues the career after one. `test_mercy.py` is the contract.
- **Conditions** (2026-07-26, the attrition rework's slice 3a — rules.md's
  Conditions add-on) — `rpg.py`: the conditions constants block just under
  `TIER_HP` (`CONDITION_STACK_RULE`, `CONDITION_KINDS`, `BLEED_POWER`,
  `POISON_POWER` / `POISON_ROUNDS` / `POISON_NIGHT_HP`, `BURN_POWER` /
  `BURN_ROUNDS`, the `CONDITION_POWER` / `CONDITION_ROUNDS` tables,
  `STABILIZE_CLEARS`, and the `CONDITION_TAG` / `CONDITION_ON_HIT_TAG`
  vocabulary); the `Condition` dataclass beside `Purse`; `Entity.conditions`
  and `Entity.inflicts`; the API block ahead of the melee (`condition_of` /
  `condition_tags` / `apply_condition` / `clear_conditions` /
  `_tick_conditions` / `_stabilize`). The TICK is called from
  `group_combat`'s round end, between the regen loop and the reload clock —
  that position is the spec, not an accident. `_clear_fight_states` drops
  TIMED conditions only; `_stabilize` runs at every fight exit (resolution,
  both clean-escape branches in `attempt_retreat`, `blink_escape`);
  `refresh_foes_after_retreat` wipes a fled room's conditions outright.
  Between fights: the sweat-it-out block in `long_rest` (which `tavern_rest`
  inherits), the bleed clear in `use_potion`'s healing branch, and
  `_mend_bleeding` off `cast_healing`. `sites.py`: `FoeSpec.inflicts` +
  its `make_foe` pass-through, the great spider's `inflicts="poison"` and
  the pyromancer's `inflicts="burn"`, the on-hit and live-condition tags in
  `roster_lines`. `session.py`: the `Condition` round-trip in
  `_entity_to_dict` / `_entity_from_dict` (an untimed condition outlives the
  fight, so it has to outlive the save), and the `condition_tags` readouts in
  `tally_lines` / `cmd_status` / `party_sheet_lines` / the pause menu.
  **The one thing deliberately NOT here** is a school-wide cast rider
  (`{"fire": "burn"}` on every bolt): measured, it moves every bestiary row
  because the bench's reference duo rolls fire wizards. It is a one-line
  addition for the magic content pass, with its own bench round.
- **Wounds & recovery** (2026-07-26, the attrition rework's slice 3b —
  rules.md's Wounds & Recovery add-on) — `rpg.py`: the wounds constants
  block just under the conditions one (`WOUND_LOCATION_WEIGHTS` /
  `WOUND_VITALS` / `WOUND_LIMBS`, `WOUND_TIER_SEVERITY` /
  `WOUND_DOWN_SEVERITY` / `WOUND_SEVERITY_MAX`, `WOUND_PENALTIES` /
  `WOUND_SEVERE_EXTRA` / `WOUND_BLEED`, `WOUND_STAT_FLOOR` /
  `WOUND_HP_FLOOR_DIV`, the authored `WOUND_NAMES` / `WOUND_MAIM_NAMES`,
  the treatment ladder's `BED_SEVERITY_PER_NIGHT` / `HEALER_*` / `SALVE_*` /
  `ELIXIR_SEVERITY`, `SAT_WOUNDED_DAY` / `SAT_MAIMED`, and
  `HP_STATE_BANDS`); **`HERO_PAIN` 2 -> 3 is the budget shift** and sits
  where it always did, in the hero-generation block. The `Wound` dataclass
  beside `Condition`; `Entity.wounds` / `records_wounds` /
  `wound_stat_pen` and the properties `wound_load` / `hp_ceiling` /
  `maimed` / `hp_state`. The API block between the conditions helpers and
  the melee: `_sync_wound_stats` (the stat fold — the `str_buff` pattern
  run backwards, which is why no read site needs a wound special case),
  `roll_wound_location`, `wound_name` / `wound_penalty_for`, `add_wound`,
  `record_hit_wound` (the accrual hook and the MAIMING rule),
  `note_beaten` / `go_down`, `refresh_wound_bleed`, `heal_wounds` (the ONE
  treatment primitive every rung calls), `wound_tags` / `untreated_wounds`.
  Accrual is called from the END of `_attack`, deliberately after the
  death branch — that is where a crippling limb blow commutes a kill into
  a maiming. **`go_down` replaced every bare `down = True`** so no future
  caller can miss the fall's own record. `refresh_wound_bleed` runs at
  `group_combat`'s round-1 setup; `long_rest` gained `bed=` (the
  settlement rung) and the ceiling clamp; `use_potion` gained the
  salve/elixir branches; `cast_healing`/`_mend_bleeding` gained the
  rank-3 permanent clear; `healer_service` is the access rung;
  `wound_morale` is the nightly convalescence drain. `places.py`: the
  `healer` service kind and `_HEALER_HOSTS` (every settlement gets one —
  the tier cap is the gate, not the building). `quests.py`: the healer's
  role in `_cast_service_providers`. `session.py`: the `Wound` round-trip
  in the serializers, `cmd_healer`, `bed=True` from `cmd_downtime`
  (`tavern_rest` passes it in the engine), `wound_morale` in
  `night_upkeep`, the `wound_tags` readouts and the `hp_state` word in
  `tally_lines` / `cmd_status` / `party_sheet_lines` / the pause menu,
  and the salve/healer rows in `prices`. `test_wounds.py` is the contract.
- **Session state** — `session.py`: one JSON document in `save.json`
  (party, clock, purse, rng, world, `active_quest`, `accepted` (the TAKEN-
  quest ids, since 2026-07-22 — `cmd_take` appends, `ui/map.txt` reads),
  `pending` paused-fight record, `rooms` fled-encounter records, breadcrumb
  `position`, persistent geography under `world` (`lands` / `areas` / `sites`
  / `rooms`),
  `sighting`, `site_clears` set-site pay
  tracking, `holdings` (the conquest ledger, 2026-07-27 — plain dict,
  garrison heads + tribute/raid day stamps per held settlement), and
  `recruits` (the on-request candidate pool, keyed to its
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

**Current state (2026-07-26, after the complete attrition rework: slices 1,
2, 3a, 3b and 4 — quest shape, clocks, conditions, wounds, ferocity and
defeat mercy. Session C's alchemy layer and
sessions A/B's point economy still underlie doctrine v2.) The full dated
report of every measured re-tuning lives in `benchlog.md`; this is only the
standing summary — refresh it whenever a new entry lands there.**

**The weapon generation system (2026-07-28) is bench-neutral by
construction, with one honest economy shave.** Every engine hook is inert
without a magic weapon in hand (the sims never hold one), both site
fixtures were diffed byte-identical across the change, and worldgen's
armory/smith/reward rolls ride DERIVED rngs so the posting streams the
career sim consumes are unchanged. The one real effect: ~15% of postings
now pay their turn-in lump as a weapon (`WEAPON_REWARD_CHANCE`), which the
sim party cannot claim — career gold runs a shade leaner. A 30-career
sanity run matched the slice-4 acceptance shape (L5 93% / L8 80% / L11
33%; median death L9; capped 93 days / 38 quests — small-sample noise
around the 500-career baseline). Owed before trusting the sp prices for
tuning: a bench_weapons budget-honesty matrix (equal-sp columns, the
bench_abilities pattern) and a top-band career re-bench with generated
steel actually reaching sim hands.

**Slice 4 (2026-07-26) is a selective content rebaseline plus the career
acceptance pass.** Ferocity-0/1 enemies may now escape a fight they are
losing, while ferocity-2 rows run the old combat unchanged; defeat mercy
belongs to the played/career layer and does not falsify the raw wipe columns.

- **Relentless controls are unchanged:** skeleton **93.2%** and ghoul
  **91.5%** annotated-level wins; the barrow rank-0 fixture remains
  **27.4 clear / 50.8 wipe** (rounding-only against 27.4 / 50.7).
- **Breaking content resolves sooner in the party's favor:** the hideout
  rank-0 fixture is **54.3 clear / 18.6 wipe**, from slice 3b's 45.3 / 22.7.
  Its training ladder is **54.3 → 75.2 → 86.4 → 93.9** and its party-size
  sweep **22.1 / 54.3 / 64.1 / 76.3**. No stat or resource dial moved.
- **Generated content** (300/cell): at-level encounters win **77.3-95.7%**;
  at-level whole jobs clear **61.0-92.3%**. The rise is the visible effect
  of non-relentless rosters breaking, not a pressure-math change.
- **CAREERS — Slice 4's acceptance measurement.** 500 careers reach
  **L5 86% / L8 70% / L11 35% / L14 10% / L17 3% / L20 1%**; median death
  rises **L8 → L9**; capped median is **92 days / 36 quests**. There were
  **500 defeat mercies (1.00/career)** and **86.2%** of careers survived at
  least one. Turn-in bands are **42 / 49 / 7 / 2**. The acceptance criterion
  — wipes largely become survivable events and median death level rises —
  is met.

**Slice 3b (2026-07-26) is the full rebaseline. The one-line reading: the
SINGLE-FIGHT game barely moved and the CAREER moved a lot** — which is the
budget shift (`HERO_PAIN` 2 → 3) working exactly as specified. In-fight
pressure at a given injury level is unchanged; what changed is that part of
it is now located, named, and does not heal overnight.

- **Bestiary: within noise, row for row** (2000 trials a column, at the
  annotated level): archer 80.9 → **81.3**, skeleton 93.0 → **93.2**, dire
  wolf 93.5 → **94.2**, great spider 81.9 → **85.1**, ghoul 92.0 → **91.5**,
  pyromancer 87.7 → **85.0**, giant 98.8 → **98.9**. Nothing moved more than
  ~3 points and the moves go both ways. No annotation touched.
- **Controls: also within noise** — `bench_weapons` keeps its column order
  exactly (zweihander tops every swarm, katana/zweihander split the duels);
  `bench_ranged` longbow **46.9 / 47.2 / 67.8** by field against 46.4 / 48.8 /
  66.7. Both harnesses now build wound-recording fighters (they are heroes),
  so these are live numbers, not frozen ones.
- **The multi-encounter FIXTURES got harsher, as designed** — they are the
  content the wound track exists to tax: hideout rank 0 clear/wipe **45.3 /
  22.7** (was 50.8 / 15.6), barrow `[3,3,4]` **27.4 / 50.7** (was 30.2 /
  48.3). Training ladder hideout **44.5 → 68.3 → 83.5 → 92.4**, barrow
  **27.4 → 59.8 → 86.1 → 96.1**: a rank still reads as a rank. Party sweep
  hideout **15.4 / 44.5 / 51.2 / 66.0**, barrow **2.2 / 27.4 / 67.4 / 87.3**:
  the solo-death-trap / 3-4-cruise shape holds.
- **Generated content** (300/cell): at-level encounters win **71.7-93.3%**;
  at-level whole jobs clear **55-85%**, deepest in the L8-9 pocket (59.0 /
  55.0), top band **61.0 / 66.7** at L19-20.
- **The equal-cost matrix**: column order unchanged on a floor a few points
  lower — L8 site row pools **5.2** vs median **34.9**, training **47.8**,
  weapon **54.5** (was 7.5 / 38.8 / 53.0 / 56.5). Moves, disarm-vs-
  telekinesis and the alchemist career all keep their verdicts.
- **CAREERS — the acceptance measurement.** 500 careers: reach **L5 76% / L8 62% / L11 32% / L14 10% / L17 5% / L20 1.2%**, median death **L8**, capped median **96 days / 35 quests** (p10-p90 84-132). Against slice 2's 89/72/47/16/9/4.2, death L10, 78 days — and against the PRE-REWORK 83/60/36/12/-/4, death L8, 158 days / 38 quests. Read against the pre-rework curve the career is essentially where it started: **median death level returns to 8**, the number the whole rework was pointed at, and **days to cap recover to 96** from the 78 slice 1's flag was raised about — through convalescence rather than a longer grind, which is the inflation answer the rework exists for. Turn-in bands **quick 41 / on time 49 / late 8 / expired 2** (was 51/43/4/1): the quick premium stopped being nearly free. **No dial was pulled** — the acceptance criterion (reach-L8 and median death level must not collapse) is met.
- **A harness trap worth remembering:** the first full run read reach-L8 5%
  and median death L3. That was `bench_quests` camping until
  `hp >= 0.8 * max_hp`, which a wounded hero can never reach, so both rest
  loops burned their whole 14-night cap before every door. **Any harness that
  reads a rest target off `max_hp` is now wrong** — use `hp_ceiling`.

**Slice 3a (2026-07-26) moved exactly two bestiary rows and nothing else.**
The conditions framework is inert wherever nothing inflicts a condition, and
only two rows do:

- **Great Spider** (annotated L3, 3x, 2000 trials a column): at level
  **89.5% → 81.9%** win, wipe 0.8% → 5.2%, down 2.5% → 14.4%. The full
  ladder now reads L1 34.6 / **L2 71.6** / L3 81.9 / L4 94.8.
- **Pyromancer** (annotated L6, 2x): at level **92.4% → 87.7%** win, wipe
  3.1% → 7.5%, down 10.2% → 25.6%. Ladder: L4 65.0 / **L5 74.0** / L6 87.7 /
  L7 90.2.
- **Both `level` annotations were left alone, deliberately.** The measured
  best fit to the 55-75% band is L2 for the spider and L5 for the
  pyromancer — but *most* of the catalog sits above that band at its
  annotated level (archer 80.9, skeleton 93.0, dire wolf 93.5, ghoul 92.0,
  giant 98.8...). Re-fitting two rows in isolation would make them outliers
  the other way and would ripple into `quests.py`'s threat math without a
  matching pass over the other 26. Both rows moved *toward* the target and
  stayed in family; the catalog-wide re-annotation stays the parked item it
  already was (plan.md, "Re-annotate the bestiary for the pain-2 party").
- Every other row is identical **to the cell**, as are `tune.py`,
  `bench_training.py`, and `python sites.py --seed 3` byte-for-byte.
- **The dials**, if venom or fire needs to bite harder or softer:
  `POISON_POWER` / `BURN_POWER` first (HP per tick), then `BURN_ROUNDS`,
  then `POISON_NIGHT_HP` (what sleeping it off costs). `STABILIZE_CLEARS` is
  not a dial — it is the anti-bleed-out guarantee.

**Slice 2 (2026-07-26) changed no combat math and nothing in the fixtures
moved** — `tune.py`, `bench_training.py`, `bench_party.py`,
`bench_weapons.py`, `bench_ranged.py` and `bench_quests`' encounter/site rows
all read exactly as the slice-1 block below. What moved is the CAREER:

- **The clock:** `QUEST_WINDOW_DAYS` = (3, 7) rolled per posting,
  `QUEST_QUICK_SHARE` = 1/3, `QUEST_GRACE_DAYS` = 3, pay bands
  **quick 1.15 / on time 1.00 / late 0.60 / expired 0**.
  `QUEST_REFILL_PER_DAY` = 1 per settlement (a board's first look fills it to
  its `SETTLEMENT_KINDS` slot count).
- **Careers** (500): reach **L5 89% / L8 72% / L11 47% / L14 16% / L17 9% /
  L20 4.2%**, median death **L10**, capped median **78 days / 34 quests**
  (p10-p90 60-94 days). Against slice 1's 85/70/40/17/8/6.4, death L9, 81
  days / 37 quests: the beatability curve survived, the mid band drifted
  slightly survival-ward again, and **days to cap held at ~78** (the
  designer's call: the 158-day calendar is not coming back, and 80 is fine).
- **The board never runs dry:** 0/500 careers exhausted it, ~660 postings
  expire unfinished per career, ~129 live jobs standing at the end. The
  up-front XP-coverage assert is deleted and nothing replaced it but the
  measurement.
- **Turn-in bands in the sim: quick 51% / on time 43% / late 4% / expired
  1%.** That quick share is a sim artifact, not a play prediction — the
  career sim has no travel layer, so its jobs land 2-3 days faster than a
  played one ever will. Do not read it as "the premium is too easy to get";
  re-read it after the road is priced in.
- **The open dial** if the clock ever needs to bite harder or softer, in
  order: `QUEST_WINDOW_DAYS`, then `QUEST_PAY_BANDS["late"]`, then
  `QUEST_GRACE_DAYS`. Never the refill rate — an empty board is not
  difficulty, it is a dead world.

**The slice-1 rebaseline (2026-07-26).** Every fixture number below moved
because `run_site` lost a whole recovery step (the short rest is deleted), and
the whole generated-content picture moved because a quest went from 3.74
encounters to 1.66. Read the fixtures as CONTROLS that were re-zeroed, not as
the game getting harder:

- **Quest shape:** encounters per quest **mean 1.657** (1: 49.3% / 2: 35.8% /
  3: 14.9%), hard max 3, no tail (was 3.74 with 47% at 4+ and a tail to
  nine). **9.8%** of quests span two places; place count is authored on the
  template now, never rolled.
- **Pay:** per QUEST, not per site. `QUEST_XP_PER_LEVEL` = **44** (fitted:
  60/48/44/40 gave 28/34/38/42 quests to the cap; 38 was the target),
  `QUEST_GOLD_PER_LEVEL` = **18** (career gold deliberately unchanged).
- **Hideout** (rank 0): clear **50.8** / wipe **15.6**; reckless wipe
  **86.5** (was 57.2 / 12.5 / 75.9). **Barrow** `[3,3,4]`: clear **30.2** /
  wipe **48.3**; reckless **99.8** (was 38.1 / 40.6 / 98.3).
- **Training ladder:** hideout **51.2 -> 71.0 -> 83.8 -> 92.4**, barrow
  **31.0 -> 63.1 -> 87.4 -> 96.8**. A rank still reads as a rank.
- **Party-size sweep:** hideout 1/2/3/4 clear **23.3 / 51.2 / 54.5 / 67.0**;
  barrow **2.2 / 31.0 / 70.1 / 89.4**. Solo death-trap, 3-4 cruise — shape
  intact.
- **Controls unchanged to the cell:** `bench_weapons.py`, `bench_ranged.py`,
  and `bench_bestiary.py` (the last builds parties directly and resolves ONE
  fight, so neither the rest nor the pay change can reach it).
- **Generated content** (300/cell): at-level encounters win **71-94%**
  (untouched builder); at-level whole JOBS clear **85% at L1**, **60-80%
  mid**, **~63% at 19-20** — flatter than the old site row's 93 -> ~45,
  because a job is no longer four fights deep.
- **Careers** (500): reach **L5 85% / L8 70% / L11 40% / L14 17% / L20
  6.4%**, median death **L9**, capped median **81 days / 37 quests**.
- **The flag that was: days to cap fell 158 -> 81** (gold per quest
  unchanged, so gold per DAY roughly doubled). **Settled 2026-07-26 by the
  designer: the shorter calendar stands.** Slice 2 was therefore built to
  HOLD ~80 days, not to restore 158, and it does (78). The hideout fixture
  also fell out of its 55-65 band (50.8) — the
  standing flag is reopened at fixture level, but no lever was pulled: doing
  so now would confound slice 3b's full rebaseline.

**Pre-rework state (2026-07-17, the levelling framework session C — the
alchemy layer: the alchemy skill + the long-rest brew, the kit SHRINK, the
overcharge doctrine, the stat brews, the firebomb and the smoke vial). Kept
for comparison; every fixture number in it is superseded by the block
above.**

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
- **The conquest layer is bench-invisible too (2026-07-27).** Same
  construction as karma: play-surface only, no sim imports it, worldgen
  posts nothing for it. Its knobs (garrison bands, tribute, raid
  chance/strength, levy price, the heat floor) are hand-set and
  SIM-UNVERIFIED — tune at the table. The same session merged the
  accidental "city" settlement tier into "town" (three settlements:
  Leehaven, Walhaven, Portomera): their posting band narrowed 1-16 ->
  1-14 and their board slots held at 4, a change too small to move the
  career curve (sanity-checked; benchlog 2026-07-27).
- **The one-log rework's dying-swing reorder is within noise
  (2026-07-21).** The only engine-mechanical piece of the log rework
  (the felled fighter's dying swing resolving immediately after the
  felling blow instead of at its original turn slot) was sanity-checked:
  tune.simulate at 4k trials reads hideout 57.6 clear / 12.2 wipe /
  75.8 reckless-wipe (standing: 57.2 / 12.5 / 75.9) and barrow 37.0 /
  41.4 / 98.5 (38.1 / 40.6 / 98.3); bench_party at 1.5k reads the duo
  58.1 / 38.3 clear (58/38 shape intact). No retune needed; benchlog
  entry 2026-07-21.
- **The procedural-place MVP is routing-only for balance (2026-07-25).**
  A small `bench_quests` integration run confirmed the generated Room/Site
  and career shapes remain plausible after quests began selecting tagged
  persistent geography. Encounter budgets, foe pools, XP, and gold formulas
  are unchanged; this was not a rebaseline. See the 2026-07-25 benchlog entry.
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
**The punishment budget is the exception** (2026-08-04): both
punishment layers are counted, not felt, against the levelling budget of
2–3 fights per level, and both are held near 0.5 fights per level — hell
by the one-visit write-off (`TASK_PIN_LEVELS` × one visit ≈ 0.53/level),
the law by `PUNISH_COOLDOWN_DAYS` (6 → ~0.8/level at sustained max heat;
2 came to ~2/level, which made normal questing impossible once
persistent wounds and quest deadlines shipped). Change either knob and
redo that arithmetic — it is what keeps a pure-refusal run and a
max-evil run both playable.
**The wound system (2026-07-26, slice 3b) adds three, and they have a
declared order** — use them in it: (1) **`HERO_PAIN`** (the budget shift;
3 now — dropping it back toward 2 hands the party its in-fight pressure
back without touching the wound track), (2) **the vital fraction in
`WOUND_LOCATION_WEIGHTS`** (15% of located hits today; it decides how often
a crippling blow reads as death rather than as a maiming, so it is a
*primary lethality lever* and moves the death/mercy mix directly), and
(3) **the treatment RATE** (`BED_SEVERITY_PER_NIGHT`, `HEALER_TIER_CAP`,
`SALVE_SEVERITY`). Reach for the rate before the penalty magnitudes: the
whole design gates recovery on rate and access precisely so that the
magnitudes never have to be re-tuned against an inflating economy.
`WOUND_HP_FLOOR_DIV` is **not** a dial — the half-pool floor is the
anti-death-spiral guarantee.
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
assassin openers, telekinesis, possession, scry, and teleport travel.
**Cross-land
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
masterwork/magic-item content lands. **The attrition rework shipped in full
on 2026-07-26.** Quests are 1-3 encounters (mean 1.66, from 3.74), the live
board and its clocks make days matter, conditions and named wounds make
damage persist, and ferocity plus one mercy per character level lets a
career carry one defeat without making relentless enemies harmless. Its
design spine remains: *do not make rest expensive, make rest incomplete* —
gate recovery on rate and access, never on price, because price is the only
thing that inflates across a 1-20 career. See plan.md for the parked
follow-ons.
