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

## Next up — the story layer, in implementable shape (2026-07-12)

*(Design round 2026-07-12: the designer's story/world/NPC notes brought to
build order. The conquest questline is the authored spine; the scaffolding
batch ships first because every questline beat stands on it. **Pacing
anchors for all story writing**, measured by an instrumented career probe
(80 careers, the cautious camps-between-rooms policy): median **L5 at day
~25, L8 at ~47, L10 at ~64, L20 at ~148**; ~61 fights / 17 quests to L10,
~131 fights / 38 quests to L20. A streak-playing party collects ~100% of
site XP instead of the policy's ~70%, so played campaigns run ~25-30%
faster: call it **L10 around in-game day 45-65, L20 around day 110-150**.
In real chat time at ~5 min/turn, L10 is a **~10-12 hour** campaign and
L20 **~25-30 hours**. Story consequence: the conquest arc (L2-10) spans
about **two in-game months** — write it as one fast campaign season, not a
decade of war.)*

### Batch 1 — story scaffolding (cheap, ships first)

- **Quest givers & the diegetic funnel — the quest board presentation goes
  away.** Every quest gets a `giver` at worldgen: name from people.py's
  pools, role implied by the template (reeve, constable, elder, guild
  clerk...), personality from the targeted generator below. In play there
  is no board: the party asks around (the tavern keeper knows, any local
  points the way) and ONE message funnels to the giver — "the mayor sends
  you to the chief constable, who lays out the job." Taking the quest is
  talking to the giver; the giver stays talkable while it runs and
  receives the turn-in. Engine side: a `giver` field on quests; `board`
  survives as a DM-facing inventory readout only. The funnel itself is
  dm.md protocol.
- **Quest epilogues.** One authored aftermath line per template (reskin
  slots allowed), delivered at turn-in and day-stamped into the quest
  record — which also gives the parked history readout its content.
  Designer's call: small change, high impact.
- **Targeted NPC generation** (`people.make_npc`): the caller fixes race,
  role, sex, and age band (the DM already knows the constable is a
  middle-aged local; no twelve-year-olds in random clothes), the
  generator rolls personality from the existing trait tables, a name, and
  a sheet line. Clothes/presentation stay rollable for any role (gaudy or
  tasteful constables both exist). Stats only for NPCs who might fight
  (develop_hero). Party generation stays fully random; NPCs are *cast* to
  fit. Personality categories can grow richer later (manner of speech,
  motivation, a want and a fear).
- **The central cast (recurring NPCs).** Per land, generated at worldgen,
  persisted in the save: a **ruler** (the war-wave questgiver), a
  **knowledge figure** (scholar or wizard — exposition, foreshadowing,
  "find the enemy's weakness" hooks), and one **wildcard** from a small
  role table (spymaster, mercenary captain, master smith, priest, war
  profiteer, refugee leader). The trick for roles beyond questgiver:
  attach each NPC to a system that already exists — recruiting (the
  captain brings hires), training (a retired blademaster as mentor),
  shopping (the smith), rumor (the spymaster) — instead of inventing new
  mechanics per NPC. The enemy side gets faces too: the conqueror plus
  1-2 lieutenants who recur across waves (a lieutenant killed in wave 2
  is mourned by the conqueror in wave 4 — recurring villains are the
  cheapest continuity device in the game).
- **The in-game day, surfaced.** The Clock already counts days; print
  "Day N" on board/map/party.txt headers and stamp quest completions and
  story beats with it. Trivial, and the epilogue/history layer wants it.
- **The flavor protocol (dm.md), alongside this batch:** two beats the DM
  provides regularly, always brief — a 2-3 line atmospheric visual on
  every scene change (what's seen, what stands out), and party chatter
  (what companions are preoccupied with, seeded from their traits and
  current satisfaction). A tiny `chatter` seed helper — pick a companion,
  pick a topic from their trait sheet — lets the DM riff instead of
  inventing from nothing.

### Batch 2 — the conquest questline (the L2-10 spine)

- **One aggressor per playthrough**, chosen at worldgen or by the DM at
  `new` — four variants for replayability: **elves** (fascist perfection —
  so cultured they should rule everyone; beautiful, efficient,
  magic-fuelled steampunk industry), **goblins** (chaotic evil tech —
  robots, bombs, bioweapons, zany genetic experiments), **humans** (the
  deathless kingdom — a crown corrupted by an evil god; necromancy as
  conscription that does not end at death), **orcs** (a khan unites the
  clans — might is right, war is glorious). Dwarves are never the
  aggressor (no theme found; they are the stalwart victim/ally land).
- **Four waves pinned at levels 2 / 5 / 8 / 10**, each one multi-site
  quest (2-3 sites) — `build_quest`'s existing shape already runs earlier
  sites at lower levels, so "first sites easier" is free. The beats:
  first skirmishes before open war (L2); a land attacked and successfully
  defended (L5); a land defended *and lost anyway* (L8 — the fall is
  scripted; quest success buys the epilogue, not the outcome, and must
  pay something real so it doesn't read as a cheat: the evacuation, a
  rescued recruit, a lieutenant's head); the conqueror defeated for good
  (L10).
- **Rosters**: the humanoid ladder + existing pools reskinned per
  aggressor via `make_foe(display=...)` — zero new stat blocks in v1
  (elf: gilded automata, aether-riflemen; goblin: scrap-golems,
  bomb-lobbers, vat-beasts on the beast rows; human: the undead pool plus
  living cultist soldiery; orc: the ladder worn straight). Wave 4's boss
  is the warlord row reskinned as the conqueror.
- **Story state in the save** (`story`: aggressor, wave cursor, day
  stamps). The next wave POSTS when the party reaches its level — a
  messenger or rumor scene, day-stamped (level-gating, not day-gating, so
  the party can't outlevel or underlevel the war). Local quests in
  threatened lands pick up war-flavored reskins ("local effect of the
  main quest" tags).
- **The hellish-forces / apocalypse questline becomes the SECOND spine
  (L12-20)** — this replaces the old single 3/6/9/12/15/18 conqueror
  plan: conquest carries the first half of the game, the apocalypse the
  second. Still parked until the magic tier exists (its payoff enemies
  are demons above the dragon row); early cells (cults = humanoids,
  summoned beasts) can ship sooner as flavor.
- **Progression frames** (guild advancement, the legendary-smith arc) —
  narrative wrappers around the same combat quests; a line of
  world-building each, no mechanics. Cheap once questlines exist.

### Batch 3 — the banded quest inventory (worldgen reframed)

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
- **Weapon reach** — a small first-exchange modifier; unbuilt.
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
  current numbers live in `CLAUDE.md` ("Balance / tuning").
