# Roadmap

What is left to build, in order. This file is **planned features only**:
design principles (the design spine, the three currencies, tone, legibility)
live in `rules.md`; the play protocol in `dm.md`; dev conventions and current
balance numbers in `CLAUDE.md`. Anything already implemented is documented in
`rules.md` and the code, not here — when a feature ships, delete it from this
file rather than marking it done.

---

*(2026-07-09: the world map & navigation layer SHIPPED — location state,
local boards, list-shaped lands, travel/explore/hunt/engage, the road's
party-independent encounter table with the spotted/ambush valve, and with
it the momentum-streak XP and the pain-2 spiral regear. Mechanics in
rules.md — the World & Navigation add-on and the updated wound-tier /
XP sections; measured numbers in CLAUDE.md. What remains from that design
session lives in the open questions and parked ideas below.)*

## Next up — major questlines & the world's story layer

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

**A career finding to design against** (updated 2026-07-09): the pain-2
regear answered most of 2026-07-08's roguelike-lethality — careers now
reach L5 68% / L11 38% / L20 6% (median death L8, was L3-4). What remains
of the finding: the top band (15-20) is still the hard edge (per-quest
wipe 40-65% at level) and still waits on masterwork gear, armor, and magic
for its missing player power. The "is a playthrough a roguelike run?"
question is softened but not closed — fate's bargain (shipped 2026-07-10:
the PC's death trades for a random companion's, rules.md) answers the
in-fight half; the wipe version stays parked below.

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
5. ~~Party composition & the CHA layer~~ **SHIPPED (2026-07-11)** — CHA as
   the fourth stat (capacity hard cap 0–3, the gold-only negotiation
   bonus), tavern recruitment (pick-of-3 PC creation, leveled candidates,
   bonded pairs), companion satisfaction with departures and the purse
   head-split, races/sex/age/traits generation (`people.py`), and
   `downtime`. Mechanics in rules.md's Party, Charisma & Satisfaction
   add-on. What remains for later passes: **companion CHA gameplay** (the
   stat is rolled and shown, mechanically inert), a **nickname system**
   (schema slot exists), and "builds cover each other's weak matchups" as
   a deliberate recruit-pool shaping idea.

---

## Parked ideas (agreed to exist, not scheduled)

- **Morale & surrender** — enemies breaking, yielding, bargaining; natural
  attachment point: the retreat/pursuit logic. (Distinct from companion
  satisfaction, which shipped 2026-07-11 — this is the ENEMY side.)
- **Story recruitment** — defeated or met NPCs joining the party outside
  the tavern surface (the tavern layer shipped 2026-07-11; this is the
  "the ogre yields and joins you" version, DM-driven).
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
- **The "obliterating" wound tier** — one tier above the crippling blow
  (severity 10+, ~9 HP, maybe pierces one Bulwark step) so landed blows
  differentiate again in the 14-20 band; parked because monster STR past
  `soak + 7` buys nothing under the current table (rules.md, the severity
  design note) and the crippling-blow cap is scary enough until the top
  band is authored.
- **Venom / conditions** — the great spider's poison (and disease, bleeds…)
  is a whole system; the bite carries the row until conditions exist.
- **Survival/adventure-sim pivot** (hunger, upkeep, inventory) — a deliberate
  possible future pivot away from the heroic tone, not drift.
- **Power potion re-stock** — retired 2026-07; re-circulate the kind if
  War-Breath ever makes Power genuinely scarce in play.
- **Crit/fumble on the 2d6** (snake-eyes auto-fail, boxcars auto-success or
  a guaranteed graze) — un-deadens hopeless exchanges: a DEX-4 attacker at
  -4 wounds and Spent currently rolls pressure that mathematically cannot
  win. ~2.8% per tail, but it fattens BOTH tails of EVERY exchange, not
  just the hopeless corner — the whole bench suite must be re-run before
  judging it. Note the counter-position first: a spent, near-dead fighter
  *being* helpless is partly the design working (that is what the pause,
  potions, and retreat are for).
- **Party members as lives, the wipe version** — the in-fight half shipped
  2026-07-10 as **fate's bargain** (rules.md: the PC's death commutes to a
  Down; winning the fight then costs a random companion's life). What
  remains parked is the WIPE version: on a total party knockout the PC
  alone crawls away (at 1 HP), losing a level and possibly possessions.
  Revisit once fate's bargain has been felt in play. The recruitment layer
  (shipped 2026-07-11) makes the life-resource RENEWABLE — replacements
  cost gold, capacity, and a tavern trip — and gives the spent companion a
  face (traits, maybe a grieving bond partner who walks); watch in play
  whether that renewal softens the death rule too much.
- **A PC-centric career sim** — the career bench plays an even duo with no
  protagonist, so neither fate's bargain nor the CHA/satisfaction layer is
  modeled in any career number. If played campaigns start feeling easier
  (or churn-ier) than the bench says, a career variant with a protagonist,
  hired companions, and satisfaction-driven turnover is the natural check.
- **Overfill potions** — drinking in advance tops HP/STA above max
  temporarily (pre-battle preparation as a real decision, and a use for
  potions at full health).
- **Alchemist ability** — a hero who periodically produces potions for
  free; an economy faucet, so priced carefully.
- **Quest history readout** — completed quests already persist in the world
  with their status; a `history` subcommand listing what the party has done
  (and when) is cheap and gives the save a memoir.
- **Site persistence / repopulation** — cleared-so-far rooms refill after a
  day or two, the STICK version of one-go sites. The carrot version (the
  momentum streak) shipped 2026-07-09; revisit the stick only if play shows
  the streak isn't pressure enough.
- **Give the rapier its niche back** — the 2026-07-09 pain regear halved
  the value of chip grazes, which was the rapier's whole edge (graze-floor
  thrusts feeding the spiral): it now duels a close second everywhere
  instead of best-on-three-frames (bench_weapons). Candidate fixes if the
  designer wants the old story back: rapier ignores the pain divisor
  (precision finds the nerve), or +1 atk. Do nothing until it's felt in
  play.
- **Re-annotate the bestiary for the pain-2 party** — at-level win rates
  drifted up ~5-10 points for the monster families (heroes toughened,
  monsters kept their pain; the humanoid ladder got the same buff and
  stayed put). The catalog still orders correctly and the generator's
  at-level band is honest, so this is calibration polish, not a fire —
  a dedicated bench session when the numbers start feeling mushy.

---

## Open questions

- ~~The resource horizon~~ **Resolved (2026-07-09):** the carrot was chosen
  over the stick — the momentum streak backloads per-encounter XP into
  one-go site runs (camping stays available, at a pay cost), and the
  spiral was geared down via the pain divisor (trained fighters at pain 2,
  both sides) instead of a penalty cap or flat combat. Measured: cleared
  runs now spread ~20/50/25/3 across the <10 / 10-40 / 40-70 / 70%+
  HP-lost buckets (the middle exists), reckless play still wipes ~70%.
  The flat-combat temptation stays recorded-and-resisted. Re-open only if
  play shows camping still trivializes HP despite the streak.
- ~~How wide is the viable level band?~~ **Resolved by the same regear
  (2026-07-09):** punching up 2 levels went from "a real wall" to a
  30-80% fight depending on band — leveled areas are now real choices
  (farm low / challenge high), while the road's party-independent table
  and straight-shown board levels keep the OSR stance. The felt width in
  actual play is still to be confirmed at the table.
- **Armor:** adopt, simplify, or defer (see above) — the least-developed
  system. Note the designer's lean (2026-07-11, from the trait discussion):
  armor should probably NOT be an important system, so that looks/dress
  stay varied — the "armored" trait's +1 defense may be most of what armor
  ever is.
- ~~Can stats ever be raised?~~ **Resolved (2026-07):** the frame is talent,
  the engine is training — DEX/STR stay fixed at creation (natural human cap
  6; only magic/items transcend, to ~double); levels grow the POOLS (+1
  HP/STA/Power per two levels — in the engine since 2026-07).
  Doctrine lives in rules.md ("The ceilings, and what levels grow").
- ~~CHA / party mechanics~~ **Resolved (2026-07-11):** shipped as the
  Party, Charisma & Satisfaction add-on (rules.md) — capacity hard cap,
  gold-only negotiation, tavern recruiting with pairs, satisfaction with
  departures, races/traits generation. Deliberately cut in the design
  round: paying companions to stay (logical but complicated and unfun) and
  luxurious-dress-attracts-bandits. Open to feel out in play: whether
  satisfaction events are tuned right, and whether recruit renewal softens
  fate's bargain (see the parked wipe-version note).
- Every constant is provisional and sim-tuned, never hand-designed — the
  current numbers live in `CLAUDE.md` ("Balance / tuning").
