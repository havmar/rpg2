# Roadmap

What is left to build, in order. This file is **planned features only**:
design principles (the design spine, the three currencies, tone, legibility)
live in `rules.md`; the play protocol in `dm.md`; dev conventions and current
balance numbers in `develop.md`. Anything already implemented is documented in
`rules.md` and the code, not here — when a feature ships, delete it from this
file rather than marking it done.

---

*(2026-07-09: the world map & navigation layer SHIPPED — location state,
local boards, list-shaped lands, travel/explore/hunt/engage, the road's
party-independent encounter table with the spotted/ambush valve, and with
it the momentum-streak XP and the pain-2 spiral regear. Mechanics in
rules.md — the World & Navigation add-on and the updated wound-tier /
XP sections; measured numbers in benchlog.md. What remains from that design
session lives in the open questions and parked ideas below.)*

## Next up — the banded quest inventory (worldgen reframed)

*(2026-07-12b: batches 1-2 of the story layer SHIPPED — quest givers and
the ask-around funnel (no board in the fiction), quest epilogues with day
stamps, the targeted NPC generator (`people.make_npc`), the per-land
central cast, the surfaced in-game day, the `chatter` flavor seed, and
the whole conquest questline (`story.py`): four aggressor variants, waves
at L2/5/8/10 with the named lieutenants/conqueror as budget-honest
reskins, level-plus-completion wave gating, the scripted wave-3 fall with
occupation, wave-4 liberation. Mechanics in rules.md's Story Layer &
Conquest add-on; play protocol in dm.md (the funnel, the war, the flavor
beats). The career bench was re-run after the worldgen RNG shift: within
noise. NOT built from that round, still good and cheap once wanted in
play: **war-flavored reskins on local quests in threatened lands** ("the
local effect of the main quest" tags) and a **rescued recruit** as an
extra wave-3 tangible.)*

*(Pacing anchors, measured 2026-07-12 by an instrumented career probe —
80 careers, the cautious camps-between-rooms policy: median **L5 at day
~25, L8 at ~47, L10 at ~64, L20 at ~148**; ~61 fights / 17 quests to
L10, ~131 fights / 38 quests to L20. A streak-playing party collects
~100% of site XP instead of the policy's ~70%, so played campaigns run
~25-30% faster: **L10 around in-game day 45-65, L20 around day 110-150**.
In real chat time at ~5 min/turn, L10 is a **~10-12 hour** campaign and
L20 **~25-30 hours**. The conquest arc (L2-10) spans about two in-game
months — one fast campaign season.)*

Story items that survive on the shelf (after the inventory rework):

- **The apocalypse questline — the L12-20 second spine** (replacing the
  old single 3/6/9/12/15/18 conqueror plan: conquest carries the first
  half of the game, the apocalypse the second). Parked until the magic
  tier exists (its payoff enemies are demons above the dragon row);
  early cells (cults = humanoids, summoned beasts) can ship sooner as
  flavor.
- **Progression frames** (guild advancement, the legendary-smith arc) —
  narrative wrappers around the same combat quests; a line of
  world-building each, no mechanics. Cheap now that questlines exist.

### The rework itself

- The designer's vision made concrete: **a land always has work at every
  band, plus objective high-level problems that exist independent of the
  player** (the player is the region's general problem-solver; the world's
  great evils are just *there*, whoever comes for them). Two pieces:
  1. **Landmark problems**, generated at worldgen: 3-5 famous, fixed,
     high-level problems per land (the dragon that has ALWAYS been in
     those mountains), known by rumor from level 1 — the board's rumor
     section already points at this shape.
  2. **Banded refill**: each settlement keeps a few live problems per
     level band, lazily generated and refilled as they're consumed, so
     "asking around" always finds level-appropriate work — WITHOUT
     literally posting 20 quests x 20 levels x N lands into the save.
- This replaces the up-front ~26k-XP world posting and its coverage
  assert (refill guarantees coverage by construction). It's a real rework
  of `generate_world` + the board/`_pick_quest` surface — schedule it as
  its own session, after the questline has proven the story layer.
- Later sim hook (see parked): other heroes occasionally solve, or die
  to, a landmark problem while the player is elsewhere.

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

1. ~~Placeholder magic~~ / ~~Cross-land quests~~ **SHIPPED (2026-07-14)**
   — wizards from level 1 (POWER strictly highest = a school instead of an
   ability; bolts at swing STA + 1 Power, pressure off POWER; fire the
   STR-analogue, ice the stacking DEX rime; school proficiency as the
   levellable axis; hexer/pyromancer/magus enemy rows riding the ladder
   pool), and cross-land deliveries (site-less quests paid at another
   land's settlement, one guaranteed interception, pay by travel days).
   Mechanics in rules.md's Placeholder Magic add-on and the Quest System
   add-on's Cross-land deliveries section. What remains for later passes:
   **escort/caravan variants** of the travel quest (a fragile charge in
   the party is real design work), and the full magic layer below.
2. ~~Magic & MIND, the full layer~~ **SHIPPED (2026-07-15)** — the MIND
   stat (the planned "INT"; a seventh budget line), MIND-highest wizards,
   nine spells at ranks 1-3 (points buy depth, spellbooks buy breadth,
   Power prices the burst), aimed casts on the exchange (AIM =
   ceil((MIND+DEX)/2)), the casting check with the five degrees, the
   assassin openers (invisibility / stop time / teleport), telekinesis,
   possession, flight (burst), scry, teleport travel/escape, the
   spell_ward knob, and quest sight. Mechanics in rules.md's Magic & Mind
   add-on; measured numbers in benchlog.md (2026-07-15). **What remains
   of the old item, still scheduled here:**
   - **Stat transcendence + magic items** (the membrane: +stats up to
     ~double the natural cap 6; +DEX an order of magnitude rarer than
     +STR/+pool) — now the natural payload of the masterwork/legendary
     content pass, item 5's sibling.
   - **The wraith** — the immaterial undead ("mundane steel barely
     bites"): buildable NOW that attack spells exist to be the answer;
     the magic phase's signature enemy.
   - **Rank-4 capstones** — authored tomes/mentors permitting a fourth
     rank (flight-for-good, the firestorm); the 14-20 band's player
     power, gated like masterwork steel.
   - **Enemy spell use** — the magus and future authored casters using
     openers/techniques, not just bolts.
   - **Flight ranks 3-4** (all day / for good) — UNBLOCKED by the ranged
     combat model (2026-07-16: the bestiary can shoot back now); ships
     with the magic content pass.
3. **Armor** — provisional design: armor **shifts the incoming wound tier
   down** (Grievous → Wound, ...) at the cost of a DEX penalty and higher STA
   drain — protection traded for speed and clock. Optional anti-armor weapons
   ignore the tier-shift (gear-counters-gear). *Status: adopt, simplify, or
   defer.* Test: heavy armor changes a fight's *character* (pushes it toward
   attrition/contact), not just its numbers.
4. ~~The ranged combat model / Guns + ammo~~ **SHIPPED (2026-07-16)** —
   the field model (per-entity advances, movement-as-action, the switch
   at contact and the arrival volley), shots on the exchange chassis,
   reload cadence, ammo with field scavenging, seven ranged cards
   (longbow/blunderbuss/revolver quality; shortbow/crossbow/knives/sling
   common), four shooter foe rows, cultural arms (elf bows / goblin
   slings / dwarf powder), and the notice contest replacing the flat
   spotted roll. Mechanics in rules.md's Ranged Combat & the Field
   add-on; measured numbers in benchlog.md (2026-07-16). What remains
   for later passes: the three ranged/anti-ranged ABILITIES (arrow-parry,
   point-blank mastery, rapid reload — parked below on the levelling
   framework), kiting/fall-back AI, cover as terrain, friendly fire,
   ranged pursuit.
5. **Named & masterwork weapon instances** — the tiers exist in the schema;
   no actual masterwork/legendary items are placed in the world yet. Named
   weapons carry authored provenance (a famous smith, a famous wielder, a
   mythic dungeon) and are story beats, never drops. Test: a named weapon
   reads as an event; no power inflation from common loot. (The DM-side
   *reskin* shipped 2026-07-13: `give --as` grants catalog stats under a
   display name.)
6. ~~Party composition & the CHA layer~~ **SHIPPED (2026-07-11)** — CHA as
   the fourth stat (capacity hard cap 0–3, the gold-only negotiation
   bonus), tavern recruitment (leveled candidates,
   bonded pairs), companion satisfaction with departures and the purse
   head-split, races/sex/age/traits generation (`people.py`), and
   `downtime`. Mechanics in rules.md's Party, Charisma & Satisfaction
   add-on (reworked 2026-07-13: generated PC, recruit-on-request,
   companion autolevel, the fixed stat budget). What remains for later
   passes: **companion CHA gameplay** (the
   stat is rolled and shown, mechanically inert), a **nickname system**
   (schema slot exists), and "builds cover each other's weak matchups" as
   a deliberate recruit-pool shaping idea.

---

## The major-feature shortlist (2026-07-14) — ordering notes

A high-level planning pass over the designer's major-feature wishlist:
ordering and dependencies only, nothing below is designed. Items the
roadmap above already schedules (full magic = 2, guns = 4,
named/masterwork weapons = 5, quest variety = the banded inventory
rework) keep their entries; this section places the rest. The short
answer to "can these be done in any order?": mostly yes — but four of
them are foundations that make everything after them cheaper, and one
belongs at the end.

**Foundations — do early, other items ride on them:**

- ~~Full magic (item 2 above)~~ **shipped 2026-07-15** — the keystone is
  in: magic ITEMS, the wraith, and the demon tier (and with them the
  apocalypse spine) are now unblocked content passes, and the MIND build
  exists.
- ~~The ranged combat model~~ **shipped 2026-07-16** (with guns, item 4)
  — the field model is in: every later enemy, weapon, and flight rank
  now has distance to ride on.
- **The levelling framework (skills / abilities / moves / perks)** —
  decides what "player power" means, which is exactly the known 14-20
  gap; enemy and item authoring want to know its shape first.
  Berserk/War-Breath and school proficiency are the seeds it grows from.
- **Conditions** (poison, bleed, disease — the parked venom note) — the
  missing enabler behind "more varied enemies": without conditions, enemy
  variety is mostly stat rearrangement, and varied magic wants them too.
  Flagged as the big gap in the shortlist itself.

**Order-free — can slot in anywhere:**

- **Free-play facilitation / overriding the mechanics** — mostly dm.md
  doctrine plus session override surfaces (`forge`, `give --as`, the
  hand-editable save exist already). Cheap, and worth doing EARLY anyway:
  a good override story de-risks every missing system, because the DM can
  improvise what isn't built yet.
- **Professions** — a between-fights layer hanging off downtime and the
  economy; independent of everything, and the natural feeder for domain
  play.
- **Intraparty mechanics & prominent main NPCs** — deepens shipped layers
  (satisfaction, the central cast); mostly content. Its big multiplier is
  the parked off-screen event simulation — that is what makes NPCs feel
  alive between meetings.
- **Region detail & exploration depth** — navigation shipped 2026-07-09;
  what remains is content (settlement flavor, landmark problems) plus the
  same off-screen tick.

**Late by nature:**

- **Domain play** — the endgame layer (holdings, followers, rulership).
  Wants region detail, professions/economy at scale, and the off-screen
  simulation before it can feel alive — and it is the natural answer to
  "what is gold FOR at L15+", so don't solve that question separately.
- **The content passes** (more quests, more weapons & magic items, more
  varied enemies) — deliberately last within their threads: content is
  cheapest once the systems it varies exist (quests after the banded
  inventory rework; magic items after the magic layer; enemies after
  conditions / magic / the ranged model).

---

## Parked ideas (agreed to exist, not scheduled)

- **Summoning** (2026-07-15, cut from the magic layer by designer call)
  — a conjured body is worth more than any severity number (action
  economy is the game's strongest measured force), so it needs its own
  design round. Sketches from the session: the party cap of 4 counts the
  summon, CHA could be ignored for it, it's expendable, and catalog rows
  as the summons mean the benches already price it.
- **Antimagic** (2026-07-15) — trivial to build, nothing to counter yet
  (three bolt rows); becomes the wizard-duel tech once enemy magic has
  breadth (dispel the flier, ground the unseen, mute the magus).
- **Ward, the tier-shift shield spell** (2026-07-15) — designer pass
  ("finicky unless very strong and general"); note it doubled as the
  provisional armor design, so revisiting armor revisits this.
- **Opener economy in play** (2026-07-15) — openers auto-fire while the
  Power lasts (First Blood's doctrine). If played wizards resent the
  pool burning on trash fights, the fix is a session-side hold toggle
  (`orders HERO opener off`), not engine smarts.
- **Opt-out tutorial register** (2026-07-14) — a new-player mode where
  the DM teaches mechanics as they first come up, off by default. dm.md
  now assumes full rules fluency (the designer is the only player);
  this becomes relevant only if the game ever gets a second player.

- **Off-screen event simulation** (designer, 2026-07-12: plan only for
  now) — methods to simulate events for entities the player isn't
  interacting with: named NPCs, the lands, and main-quest story progress
  independent of the quests. Natural shape: a world tick rolled at
  settlement arrivals from small event tables, day-stamped. Wants batch
  1's named NPCs and day stamps first; the landmark-problem simulation
  ("did some other hero clear it?") is its first concrete customer.
- **Faction reputation** — a parallel progression track earned from local
  quests. Designer has more to spec; do nothing until then.
- **Settlement flavor lines** — a generated line or two per settlement
  for the DM to riff on. Designer's call (2026-07-12): valuable but easy
  to design, deliberately not yet.
- **The rival** — a competing adventuring party as a recurring cast
  entry: they take quests off the same problems, claim a landmark kill,
  maybe die trying. The natural face for the other-heroes simulation,
  and the "rival" NPC role the central-cast table doesn't cover.
- **The traitor twist** — one authored questgiver per conquest variant
  who turns out to be collaborating with the aggressor; a cheap authored
  beat that makes the questgiver layer itself story-bearing.
- **Morale & surrender** — enemies breaking, yielding, bargaining; natural
  attachment point: the retreat/pursuit logic. (Distinct from companion
  satisfaction, which shipped 2026-07-11 — this is the ENEMY side.)
- **Story recruitment** — defeated or met NPCs joining the party outside
  the tavern surface (the tavern layer shipped 2026-07-11; this is the
  "the ogre yields and joins you" version, DM-driven).
- **Weapon reach** — a small first-exchange modifier (spear vs dagger at
  the moment the lines meet); unbuilt, and distinct from the ranged
  model's field (which is between-lines ground, not in-exchange reach).
- **The ranged abilities** (2026-07-16, from the ranged design round;
  wait on the levelling framework): melee masters **parry arrows**
  (high-level: a chance to negate incoming missiles, later bullets);
  **point-blank mastery** (~L10: the ranged card shoots at gap 0, no
  switch round); **rapid reload** (cadence 0 on a card that has one).
- **Kiting / the fall-back step** (2026-07-16) — shooters hold ground in
  v1; a deliberate backward step wants ability framing ("skirmisher's
  step") or it becomes the default degenerate dance.
- **Cover & terrain on the field** (2026-07-16) — a defense bonus for
  shooting at a dug-in target, per-encounter field flavor beyond the one
  size number; prose until the wilderness gets a terrain pass.
- **Friendly fire into the press** (2026-07-16) — shooters currently pick
  freely into a melee; add the miss-hits-a-friend rider only if play
  shows free focus-fire reading wrong.
- **The 2-STA heavy swing** — sim-rejected while Spent is lethal (halving the
  swing budget loses more than severity buys back — `bench_weapons.py` is the
  doc of record); the `sta_cost` knob stays in the schema for deeper STA
  pools.
- **d12 variance experiment** — more upsets both ways, weaker modifiers;
  don't fork the variance dial while lethality changes are still settling.
- **Asymmetric Spent** — keep −6 on defense, soften attack to −3
  ("desperation swings") if spent-vs-fresh grinds ever feel wrong in play.
- **A PC happiness stat** — discussed and kept OFF (2026-07-11): the PC's
  satisfaction is untracked by design (the player embodies the PC's
  morale), and a mood-to-rolls coupling would build a second death spiral
  on top of the wound spiral the pain-2 regear just softened. Revisit only
  when there is a system to hang it on (the story layer); the zero-effect
  display-only version is the most it should ever be without one.
- **Prey depletion (the hunt-spam lever)** — hunting as a farm loop is
  deliberately viable and currently fenced by pay rates, the 10% ambush
  tax, satisfaction bleed, and recovery time; a solo PC is the one party
  shape those fences don't fully govern. If play shows hunt-spam
  degenerate, deplete a land's prey per day before restricting anything.
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
  current numbers live in `develop.md` ("Balance / tuning").
