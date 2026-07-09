# Roadmap

What is left to build, in order. This file is **planned features only**:
design principles (the design spine, the three currencies, tone, legibility)
live in `rules.md`; the play protocol in `dm.md`; dev conventions and current
balance numbers in `CLAUDE.md`. Anything already implemented is documented in
`rules.md` and the code, not here — when a feature ships, delete it from this
file rather than marking it done.

---

## Next up — the world map & navigation layer

*(2026-07-09 design session: quests are currently global — `board` lists the
whole world and nothing anchors the party anywhere. The fix is a light
navigation layer over the existing worldgen, list-shaped, not spatial. All
numbers below are provisional until simmed/played.)*

- **Location state & local boards.** The save gains a current-location; the
  party is always *somewhere* (a settlement, or traveling/afield). `board`
  shows only the local settlement's quests, and taking a quest means being
  there. The world stops being globally available.
- **The map is a list, not a grid.** ~5 lands (one per race), each holding
  its settlements and wilderness — no coordinates. Travel inside a land
  takes 1 day, to another land 2 days; the world can grow later if that
  feels small. Travel days are camp nights, so healing en route falls out
  of the existing recovery ticks — no new mechanic.
- **Travel encounters.** Each travel day risks a combat encounter
  (~10-20%). Any level can appear, weighted strongly toward low — the rare
  high tail is how the world above the party's level stays real. Needs an
  **avoidability valve**: an encounter well above the party should usually
  be spotted first (avoid, or attempt to slip past) so the tail signals
  danger instead of executing the party on a die roll.
- **The explore move.** Spend a day to discover a place in the current land
  you haven't seen; pays XP for the discovery, at a higher encounter chance
  (~30%). Discovered places persist in the save.
- **A farm loop that never runs dry.** Wilderness hunting/patrol: generated
  encounters at the local band paying the flat encounter rate, so grinding
  gold/XP is always possible even with the board's finite XP.
- **Difficulty geography.** Lands/areas carry level *bands* — ranges, 3-5
  across the world, never 20 micro-tiers — posted independent of the party
  (the OSR stance; the settlement bands already work this way, this gives
  them geography). The open question below on the viable level band decides
  how the bands are spaced.

---

## Then — major questlines & the world's story layer

*(2026-07-08: the encounter & quest system SHIPPED — pool growth in the
engine, the humanoid ladder (soldier→warlord), the generation layer
(`quests.py`: threat math, room/site/quest builders, seeded worldgen with
asserted XP coverage, race reskinning), the quest board in session play
(`board`/`take`/`room`/`forge`), the JSON save, and `bench_quests.py` with
the career sim. Mechanics now documented in rules.md's Quest System add-on;
measured numbers in CLAUDE.md. What remains of the original vision is the
STORY layer:)*

- **The mundane-conqueror questline** (deferred from the first quest slice
  by design call): the first major questline — ~6 authored quests pinned at
  fixed levels (roughly 3/6/9/12/15/18) forming the game's difficulty
  spine, running on the humanoid ladder (reskinned soldiery = the
  conqueror's armies). Local quests then pick up "local effect of the main
  quest" template tags.
- **The hellish-forces questline** — parked until the tier above the dragon
  exists: its payoff enemies (demons) are authored one-offs on the Heroes
  table, which wants the magic phase. Early cells (cults = humanoids,
  summoned beasts) could ship sooner as flavor.
- **Progression frames** (guild advancement, the legendary-smith arc) —
  narrative wrappers around the same combat quests; a line of world-building
  each, no mechanics. Cheap once questlines exist as a concept.
- **Leveled quest boards** — the long-term shape: ~5 level-banded quest sets
  per settlement so every party level finds work; today's boards roll levels
  randomly in one band per settlement kind (that randomness is v1's
  placeholder, kept on purpose).

**A career finding to design against** (bench_quests, 2026-07-08): under sim
policy a full 1-20 career is roguelike-lethal — L5 46% / L11 14% / L20 ~0%,
half the deaths at the rank-0 front door, and past ~L13 outleveling content
stops working because the party saturates (skills capped, pools only) while
the bestiary keeps climbing. The top band's missing player power is exactly
the next systems below: masterwork gear, armor, magic. Decide eventually:
is a playthrough a roguelike run (death = new party, the world persists) or
should the curve soften?

---

## After that (in rough order)

1. **Magic & INT** — magic skills, INT scaling/gating (the way STR scales
   weapons), the stat-transcendence path (magic is the membrane that lets
   gamey effects into the simulated body; ceiling: up to ~double the natural
   DEX/STR cap of 6, and +DEX items an order of magnitude rarer than
   +STR/+pool — see rules.md, the 1-20 doctrine). Test: an INT build is
   viable; magic feels like the sanctioned rule-breaker. **The wraith
   belongs here**: the immaterial undead ("mundane steel barely bites") only
   works once magic exists to be the answer — it's the magic phase's
   signature enemy, deliberately left out of the bestiary until then.
2. **Armor** — provisional design: armor **shifts the incoming wound tier
   down** (Grievous → Wound, ...) at the cost of a DEX penalty and higher STA
   drain — protection traded for speed and clock. Optional anti-armor weapons
   ignore the tier-shift (gear-counters-gear). *Status: adopt, simplify, or
   defer.* Test: heavy armor changes a fight's *character* (pushes it toward
   attrition/contact), not just its numbers.
3. **Guns + ammo** — dungeonpunk ranged weapons; ammo as the recurring gold
   sink. Deliberately excluded from the first weapons slice.
4. **Named & masterwork weapon instances** — the tiers exist in the schema;
   no actual masterwork/legendary items are placed in the world yet. Named
   weapons carry authored provenance (a famous smith, a famous wielder, a
   mythic dungeon) and are story beats, never drops. Test: a named weapon
   reads as an event; no power inflation from common loot.
5. **Party composition & the CHA layer** — parties of 1–4 built so builds
   cover each other's weak matchups; recruitment; richer companion mechanics
   (currently the PC/companion split is run by DM protocol alone). The
   engine side shipped 2026-07 (any size 1–4 works; the counterweights —
   flat income, the press, sweeps — are in; see rules.md "Balanced for
   two"); what remains is the CHA/recruitment fiction and pricing a
   companion. CHA itself is underdefined — detail deferred until this
   layer is next up.

---

## Parked ideas (agreed to exist, not scheduled)

- **Morale & surrender** — enemies breaking, yielding, bargaining; natural
  attachment point: the retreat/pursuit logic.
- **Recruitment** — defeated or met NPCs joining the party (legibility pick).
- **Spark-table personalities** — flaws/needs/quirks rolled at creation
  (legibility pick).
- **Weapon reach** — a small first-exchange modifier; unbuilt.
- **The 2-STA heavy swing** — sim-rejected while Spent is lethal (halving the
  swing budget loses more than severity buys back — `bench_weapons.py` is the
  doc of record); the `sta_cost` knob stays in the schema for deeper STA
  pools.
- **d12 variance experiment** — more upsets both ways, weaker modifiers;
  don't fork the variance dial while lethality changes are still settling.
- **Asymmetric Spent** — keep −6 on defense, soften attack to −3
  ("desperation swings") if spent-vs-fresh grinds ever feel wrong in play.
- **Auto-drink thresholds for healing potions** — only if statistically
  worth it; drinking stays a deliberate act until then.
- **Per-weapon pressure dice** (a d12 weapon) — rejected: 2d6 stays the
  single global variance dial.
- **Level requirements on masterwork/legendary weapons** — rejected: authored
  placement already gates them; revisit only if strong gear leaks downward.
- **Weapon-granted abilities** — e.g. Berserk tied to the zweihander.
- **The "obliterating" wound tier** — one tier above killing blow (severity
  10+, ~9 HP, maybe pierces one Bulwark step) so landed blows differentiate
  again in the 14-20 band; parked because monster STR past `soak + 7` buys
  nothing under the current table (rules.md, the severity design note) and
  the killing-blow cap is scary enough until the top band is authored.
- **Venom / conditions** — the great spider's poison (and disease, bleeds…)
  is a whole system; the bite carries the row until conditions exist.
- **Survival/adventure-sim pivot** (hunger, upkeep, inventory) — a deliberate
  possible future pivot away from the heroic tone, not drift.
- **Power potion re-stock** — retired 2026-07; re-circulate the kind if
  War-Breath ever makes Power genuinely scarce in play.
- **Show the wound penalty in the player log** — the full log prints
  `-n to rolls` on every wound line; the player log prints HP only, so the
  death spiral is invisible to the player. Low-hanging legibility fix; do
  it before touching spiral *mechanics*, so any tuning reacts to a spiral
  the player can actually see.
- **Rename the "killing blow" tier** — it is 6 flat HP and only kills at
  0 HP unsaved, but the name reads as an instant kill in play (a testing
  session tripped on it). Pure renaming ("mortal strike", "crippling
  blow"...); the mechanic is fine.
- **Crit/fumble on the 2d6** (snake-eyes auto-fail, boxcars auto-success or
  a guaranteed graze) — un-deadens hopeless exchanges: a DEX-4 attacker at
  -4 wounds and Spent currently rolls pressure that mathematically cannot
  win. ~2.8% per tail, but it fattens BOTH tails of EVERY exchange, not
  just the hopeless corner — the whole bench suite must be re-run before
  judging it. Note the counter-position first: a spent, near-dead fighter
  *being* helpless is partly the design working (that is what the pause,
  potions, and retreat are for).
- **Party members as lives** — on a wipe the PC alone survives (at 1 HP),
  companions die, and the PC loses a level and possibly possessions. Turns
  companions into a graded life-resource and softens the career sim's
  roguelike lethality (see the career finding above) without making death
  free. Interacts with the recruitment/CHA layer.
- **Overfill potions** — drinking in advance tops HP/STA above max
  temporarily (pre-battle preparation as a real decision, and a use for
  potions at full health).
- **Alchemist ability** — a hero who periodically produces potions for
  free; an economy faucet, so priced carefully.
- **Quest history readout** — completed quests already persist in the world
  with their status; a `history` subcommand listing what the party has done
  (and when) is cheap and gives the save a memoir.
- **Site persistence / repopulation** — cleared-so-far rooms refill after a
  day or two, so a site cannot be done piecemeal with a camp between every
  door. The enforcement half of the resource-horizon question below; only
  worth building if that question resolves toward budgeting HP across a
  site.

---

## Open questions

- **The resource horizon** (2026-07-09, the current big question). Camping
  after any encounter makes HP cheap — healing, potions, and defense only
  become valuable if resources are budgeted over a *site*, not one fight.
  The candidate package (its pieces reinforce each other and should be
  judged together): sites done in one go (via repopulation and/or travel
  friction), **larger HP pools**, and a **geared-down hero death spiral**
  (a hero pain divisor, or a cap on the wound penalty) so "low on HP" is
  tension rather than helplessness. This *conflicts* with the 2026-07
  lethality retune, which put the danger in the single encounter precisely
  because camping was free — pick one horizon and retune; don't run both
  screws tight at once. The far end of this dial — flat combat, no STA, no
  wound penalty — is recorded as considered and resisted: the pause,
  retreat, potion, and Bulwark decisions all hang off fatigue and the
  spiral, and removing them removes most of the game's decisions. First
  step either way: make the spiral visible in the player log (parked idea
  above) before tuning it.
- **How wide is the viable level band?** The goal of all difficulties
  existing on the map at once pushes against deadly at-level combat: the
  benches say -2 levels is a real wall, so the felt band today is roughly
  [-something small, +2]. If leveled areas should be *choices* (farm low,
  challenge high, Shamus Young's self-regulating difficulty), the band may
  need widening — which is the same lever as the resource-horizon question
  (bigger pools, gentler spiral). If instead the band stays narrow, the
  map's high bands are honest signage ("come back at 14"), which is the
  OSR answer and already how the barrow works. Decide which game it is
  before tuning the navigation layer's bands.
- **Armor:** adopt, simplify, or defer (see above) — the least-developed
  system.
- ~~Can stats ever be raised?~~ **Resolved (2026-07):** the frame is talent,
  the engine is training — DEX/STR stay fixed at creation (natural human cap
  6; only magic/items transcend, to ~double); levels grow the POOLS (+1
  HP/STA/Power per two levels — in the engine since 2026-07).
  Doctrine lives in rules.md ("The ceilings, and what levels grow").
- **CHA / party mechanics** — underdefined by design; detail when that layer
  is next up.
- Every constant is provisional and sim-tuned, never hand-designed — the
  current numbers live in `CLAUDE.md` ("Balance / tuning").
