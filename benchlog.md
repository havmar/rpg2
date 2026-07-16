# RPG2 — Tuning History (the bench log)

The dated ledger of every measured re-tuning, oldest first. Each entry is
the full report of one bench-suite run: what changed, what was re-run,
the numbers before and after, and the flags raised for the designer.

Protocol: after any mechanics or balance change, re-run the suite (see
`develop.md` "Balance / tuning" for which benches and the difficulty
levers), APPEND a dated entry here, and refresh the "Current state"
summary in develop.md. History is never rewritten — supersede an entry
with a newer one.

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

**Measured numbers (2026-07-14, placeholder magic + cross-land
deliveries).** `make_human` now rolls a WIZARD on 24% of characters
(POWER strictly highest; measured over 20k rolls), so every seeded stream
shifted AND a genuinely new hero shape entered every sim. The suite was
re-run THREE times this session, and the middle runs did real work:

- **Run 1 caught a scaling break.** With the growing Power pool doubling
  as the bolt's attack stat, high-level reference wizards cast at +17-up
  and every top-band row drifted 5-9 points easier (dragon 89 -> 94.6,
  troll 94 -> 98). Fixed the same day: `Entity.power_stat` pins a
  wizard's aim at creation POWER — pool growth deepens the AMMO, never
  the aim (the 1-20 doctrine holds for wizards too).
- **Run 2 caught a content break.** The first caster rows measured
  toothless (97-100% duo win two levels UNDER their annotations); after
  re-statting them into the catalog band, sitting in `LADDER_POOL` they
  appeared in 46-77% of ALL warband rooms and the career curve COLLAPSED
  (reach-L11 47% -> 16%, capped 7.5% -> 3%). Attribution probes (200
  careers each): wizard HEROES alone ≈ baseline (L11 45%) — the collapse
  was caster foes saturating the most common content. Rooms measured
  fine at level; SITES dropped 15-25 points mid-band — ranged chip
  bleeds a duo across chained rooms even when each room is fair.
- **The shipped shape: casters are contained content.** One caster quest
  per race + the Renegade Magus capital epic, out of the warband pool
  entirely (rules.md, Enemy casters). Final numbers below.

The tuned game, final (run 3 where worldgen matters, run 2 elsewhere):

- **Hideout** (rank 0, 10k): clear **77.7** / wipe **19.7** (was
  74.1/22.8); reckless wipe **84.5** (was 86.9). **Barrow** `[3,3,4]`:
  clear **20.3** / wipe **76.0** (was 17.0/79.6), reckless 99.5.
  Cleared-run HP-lost spread 17/58/22/3 and 23/58/17/3 — the middle
  holds. A wizard in the party is a mild net buff at the low band.
- **Training ladder** (5k/rank): barrow **20 -> 52 -> 80 -> 96**, hideout
  **78 -> 95 -> 99 -> 99.9** (was 17/45/76/94 and 74/93/99/99.9) — a rank
  still reads as a rank.
- **Party size** (5k/size): hideout **17 / 78 / 98 / 99.8**, barrow
  **0.8 / 20 / 67 / 94** (was 17/74/97/99.5 and 0.8/17/58/88) — numbers
  still dominate, and the 3-4-size columns rose a few points (more
  bodies = more wizard rolls).
- **Weapons matrix**: the story is intact — zweihander best duel on
  precise/steady, katana on powerful/balanced, zweihander owns every
  swarm column, staff trails, no weapon tops every cell (the frames are
  fixed non-casters, so magic can't touch this bench by construction).
- **Bestiary**: the monster families drifted UP +1-6 even after the pin
  (skeleton 95 was 89, wolf 91, troll 97, dragon 91) — a wizard in the
  reference duo is a real buff against low-soak and undead rows (fire
  bolts ignore the caster's STR, never test steel, and never tire the
  arm the way the swing budget bites vs tireless bones). The elite
  ladder held (champion 72, blademaster 64.5, warlord 59). **New rows,
  bench-annotated:** hexer **81** at L3 (its -2 column 28 — a real
  wall), pyromancer **89** at L6 (-2: 75), magus **91** solo at L10
  (-2: 75) — calibrated by an 800-trial probe sweep (dex/power/
  school_prof), landed inside the band on the 2k-trial bench.
- **Generated content** (300/cell): at-level rooms win **69-99** across
  1-20; at-level sites **~90-92 at L1-3** sliding to **~37-54 at
  15-20**. The caster quests are the new hard -2s at the LOW band
  (site clear-2 41-49 at L3-5): grinding two-below into a coven is the
  one below-level pick that still bites.
- **Careers** (200): reach **L5 80% / L8 54% / L11 30% / L14 14% /
  L20 4.5%**, median death **L8**, capped median 168 days / 38 quests —
  **HARDER than 2026-07-13's 80/74/47/22/7.5, median L10. This is the
  flag for the designer.** Attribution is clean: pinned wizard heroes
  cost ~nothing (the no-caster probe reads L11 45%); the residual is
  the caster quests themselves (~1 in 5 board quests), which the career
  sim walks into blind at its grind-2-below policy. A PLAYER reads "2x
  Mist-Singer" on the quest detail and preps, skips, or punches at
  level — exactly the sims-understate-the-player gap, but it is wide
  here. Levers if play agrees it's too hot, in ascending disruption: a
  posting-weight knob for caster templates, `school_prof` 2 -> 1 on the
  hexer/pyromancer rows (drops them a band), floor caster templates at
  L4+ so the fresh-party band never meets them. Levers untouched this
  session — feel it in play first.
- **What the batch changes in PLAYED games beyond the sims**: a quarter
  of rolled characters (PC included) are wizards whose skill points want
  the school lane; enemy casters are board-legible set pieces; and
  deliveries add a no-combat income lane (2/world, 40g + 50 XP the
  standard cross-land run) whose guaranteed interception rolls the road
  table. The career sim skips deliveries (no travel layer), so career
  numbers carry no delivery income.


**Measured numbers (2026-07-15, the Magic & Mind layer: MIND stat +
budget 11, the spell system with ranks/openers/casting check, quest
sight, caster rows re-statted).** Full suite re-run; one mid-session
recalibration (the caster rows' aim, below).

The change under measurement: MIND joined the creation budget as a
seventh line (surplus 9 -> 11 to keep the per-stat spread), wizard =
MIND-highest (was POWER-highest, ~unchanged 23% of rolls), bolt aim
moved from the flat POWER stat to ceil((MIND+DEX)/2) + spell rank, the
school proficiency ranks became SPELL ranks (rank 1 free at creation --
a small early wizard buff), and rank-3 techniques/openers exist (the
sims' rolled heroes only ever know their school spell, so no opener
fires in any bench -- openers are book-taught, and books are play-only).

- **The headline: heroes drifted ~4-8 points stronger across every
  bench** -- the budget bump plus the free rank-1 school. Direction is
  uniform; no interaction looks broken.
- **Hideout** (rank 0, 10k): clear **81.5** / wipe **16.5** (was
  77.7/19.7); reckless wipe **79.4** (was 84.5) -- "not using resources
  mostly means death" still holds, but the gap narrowed. **Barrow**
  `[3,3,4]`: clear **24.8** / wipe **71.6** (was 20.3/76.0).
- **Training ladder** (5k/rank): barrow **24 -> 56 -> 84 -> 97**,
  hideout **82 -> 96 -> 99.6 -> 100** (was 20/52/80/96 and
  78/95/99/99.9) -- a rank still reads as a rank.
- **Party size** (5k/size): hideout **19 / 82 / 98.6 / 99.9**, barrow
  **1.5 / 24 / 73 / 95** (was 17/78/98/99.8 and 0.8/20/67/94).
- **Weapons matrix**: unchanged story (fixed non-caster frames by
  construction) -- zweihander/katana split the duel columns, zweihander
  owns every swarm, staff trails, no weapon tops every cell.
- **Bestiary**: the monster families sat still (skeleton 95.8, wolf
  91.8, troll 97.2, dragon 89.9); the elite ladder rose a touch
  (champion 73.8, blademaster 66.7, warlord 65 -- was 72/64.5/59).
  **The caster rows initially COLLAPSED** (hexer 81 -> 93 at level):
  their aim had ridden the flat power stat 8/8/11, and mind=8 under the
  new mean-with-DEX formula cost them 2 pressure. Recalibrated the same
  session: mind 11/11/14 (savant values -- monster rows break the human
  cap by doctrine, like the dragon's DEX 8) reproduces the old bolt
  pressure exactly. After the fix: **hexer 81.8 (L3), pyromancer 90.4
  (L6), magus 92.2 (L10)** -- all within a point of 2026-07-14, the -2
  columns real walls again (35/79/77). The magus also gained
  spell_ward 2 (assassin-opener protection; sims never cast openers,
  so this moved nothing).
- **New knob, unmeasured by design: spell_ward** (dragon 3, drake 2,
  magus 2, wight 2, giant 1) -- it only acts against openers and stun
  riders, which no bench path uses; it exists for played wizards.
- **Generated content** (300/cell): at-level rooms win **75-99**, sites
  **~94 at L1-3** sliding to **~36-56 at 15-20** -- same shape, a few
  points up with the stronger duo.
- **Careers** (200, after the caster fix): reach **L5 88% / L8 72% /
  L11 38% / L14 20% / L20 8%**, median death **L9**, capped median 166
  days / 39 quests. Before the caster fix the curve had rebounded to
  92/81/52/26/8 (median L9) -- the fix restored roughly half the
  2026-07-14 hardening; the rest of the ease (vs 80/54/30/14/4.5,
  median L8) is the hero-side buff itself.
- **The flag for the designer:** the whole game moved a few points
  easier, and the hideout now sits ~25 points above the 2026-07
  retune's ~55% clear target (the 2026-07-11b flag, wider). The
  cheapest single counter-lever if play agrees: HERO_STAT_BUDGET
  11 -> 10 (pulls every hero half a stat point); enemy DEX stays the
  sharper knife if only the low band needs teeth. Levers untouched
  this session -- feel the wizard game in play first.
- **What the batch changes in PLAYED games beyond the sims**: openers,
  techniques, vanish/blink, spellbooks, teleport travel, scry, and
  quest sight (the board blurs to L~N under a best MIND of 5 or less;
  pay stays honest) exist only at the table -- no bench models a
  book-taught wizard. The career sim's board picks still read TRUE
  levels (the sims pass no mind), so quest sight moved no number.

**Measured numbers (2026-07-16, Ranged Combat & the Field -- the distance
model, seven ranged cards, the archer rearm + slinger/hunter/gunner rows,
cultural ladder pools, the notice contest; rooms open at ROOM_FIELD 2, the
wilds at WILD_FIELD 3, field 0 = the old engine to the digit).** Full
suite re-run plus the new `bench_ranged.py`. The melee game is
UNDISTURBED within noise; the one real drift is the mid-band career.

- **Hideout** (rank 0, 10k): clear **80.6** / wipe **16.7** (was
  81.5/16.5); reckless wipe **79.2** (79.4). The archer rearm was a
  wash: one shortbow shot at field 2 buys about what its old random
  melee weapon bought. **Barrow** `[3,3,4]`: clear **26.1** / wipe
  **71.0** (was 24.8/71.6); early pressure 88.6, walk-away wounds still
  populate the middle (58% of cleared runs leave 10-40% HP behind).
- **Training ladder** (5k/rank): barrow **26.7 -> 57.9 -> 83.9 -> 97.4**,
  hideout **81.1 -> 95.9 -> 99.4 -> 100** (was 24/56/84/97 and
  82/96/99.6/100).
- **Party size** (5k/size): hideout **22.2 / 81.1 / 98.8 / 100**, barrow
  **1.1 / 26.7 / 72.6 / 95.1** (was 19/82/98.6/99.9 and 1.5/24/73/95).
- **Melee weapons matrix**: unchanged story (field 0 by construction) --
  zweihander best duel precise/steady, katana powerful/balanced,
  zweihander every swarm column, staff trails.
- **Ranged matrix** (`bench_ranged.py`, 4k/cell, the new doc of record):
  suited-frame duels vs the melee reference at fields 0/2/3 -- longbow
  **46/49/67**, shortbow 40/31/42, crossbow 8/17/34, blunderbuss
  13/24/27, revolver 26/45/50, knives 63/40/52, sling 3/3/6; katana 97
  flat. Escort shape (card + katana partner vs 3 wolves at field 3):
  91-99 across every card. The criterion holds: reach is an EDGE that
  grows with the field and dies at the door, no shooter out-duels steel
  at contact, and the played shape is where shooters earn their keep.
  TWO MEASUREMENT-DRIVEN ENGINE CALLS made this true and are now
  doctrine: (1) chargers commit before skirmishers in the movement
  phase (a shooter no longer walks into a charge and loses its only
  shot); (2) the ARRIVAL VOLLEY (a loaded shooter looses point-blank
  the round contact first arrives -- without it the blunderbuss
  literally never fired beyond field 1). Severity flats were also bumped
  one step across the board mid-calibration (a shot's flat replaces STR,
  so the first-draft numbers under-hit by exactly a soak).
  FLAGGED WART: cadence-1 range-2 cards (shortbow, knives) read a few
  points worse at field 2 than at field 0 in a pure 1v1 -- one
  graze-grade shot under-buys its STA and tempo. Party play doesn't
  show it; levers if it nags: their flats, or a free switch for cards
  whose melee grip is their own steel (the knives).
- **Bestiary**: melee rows benched at field 0 -- unchanged by
  construction. Shooter rows bench at field 3 (a shooter benched at the
  door never shoots): archer **97.2** (L1), slinger **98.7** (L1),
  hunter **94.8** (L3; 69.8 at -2), gunner **97.5** (L4; 82.8 at -2).
  Hunter was authored at L4 and measured down to 3; gunner at L6,
  measured down through 5 to 4 -- the hand bombard's one flat-4 blast
  lands too rarely on trained duos to carry a higher band. Soft
  at-level with real -2 walls is the L1-band norm these join.
- **Generated content** (300/cell): at-level rooms win **75-97**;
  at-level sites **96 at L1** sliding to **43-51 at 19-20** -- the
  pre-ranged shape.
- **Careers** (200): reach **L5 86 / L8 66 / L11 38 / L14 19 /
  L20 6.5**, median death **L9**, capped median 175 days / 40 quests
  (was 88/72/38/20/8, median L9, 166d/39q). The L8 band is ~6 points
  harder: enemy shooters and casters now collect approach-round shots
  in rooms and on the road -- the intended price of distance being
  real, and it partially offsets the Magic & Mind ease.
- **What no bench models**: hero shooters (the reference duo stays
  melee -- a played bow party runs EASIER than these numbers,
  especially outdoors where it opens at its own range), the notice
  contest (session-side; towering encounters kept the old flat valve as
  a contract), ammo economy across a day, and the dwarf-shop revolver.
- **Levers untouched** (feel bows in play first). Standing flag
  unchanged: the hideout sits ~25 points above the 2026-07 retune's
  ~55% clear target.
