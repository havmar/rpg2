# Combat Sim — Minimal Ruleset

A combat simulator for a fantasy RPG. Fights resolve on their own; the player's
decisions happen *between* fights. Three stats, one wound track, one loop.

---

## Design goals (the "why", independent of any implementation)

**1. Autobattler, not a combat minigame.** A fight takes no input once it starts.
The simulation produces an outcome (who won, in what shape) and a narrative log.
All player agency lives *between* fights — with one deliberate exception: the
**pause** (see "The pause" below). **At most once per encounter** (2026-07-11),
at the fight's first wounds crossing, the simulation stops and asks one
player-shaped question ("fight on, patch up, or run?"), then resumes to
conclusion — every later crisis is answered by the party's **standing
orders** (they drink and convert on their own, at the same price). That is
an interrupt, not a combat minigame: the fight still plays itself; the
player only chooses *whether* it continues.

**2. The strategy is the build, made in advance.** Between fights the player
allocates stats, picks gear, chooses which opponents to take, and composes the
party (e.g. a PC and a companion). A fight is the test of those choices, not a
place to make new ones.

**3. Builds beat each other in a loop, not "biggest total wins."** The core
promise is non-transitivity: there is no single best build, only builds that
counter other builds. This is what makes the between-fights planning a real
decision instead of arithmetic. The loop is **burst / sustain / control**:

- **Precision (DEX) beats Endurance (STA)** — you can't grind down what you
  can't hit; the precise fighter evades trades and chips the slow one out.
- **Endurance (STA) beats Power (STR)** — survive the heavy hitter's early
  storm and win once it tires.
- **Power (STR) beats Precision (DEX)** — one clean hit cripples a fragile
  precise fighter through the wound spiral before its chip damage adds up.

**4. Stamina is the engine that makes the loop work.** Without a clock, stat
comparison goes transitive and you're just adding totals. Stamina is what makes
a fighter *change* mid-fight — dangerous early, fading late — so matchups become
"*when* am I dangerous", which is what creates the counter-loop and what a text
log narrates well. And the clock has teeth: STA is a **second death-track**.
A fighter who runs it dry mid-fight is **Spent** — still swinging, but ragged,
every roll crippled — and against fresh enemies is usually finished where they
stand. HP is how much you can bleed; STA is how long you can fight *well*;
whichever empties first in reach of an enemy kills you.

**5. Wounds, not a hit-point buffer.** A clean hit can swing or end a fight. The
decisive contact is short and brutal; the depth of a fighter's pool just sets how
long before the spiral bites.

**6. Two layers: thin mechanics, rich flavor.** The mechanical layer is a few
numbers. The narrative layer is interpreted *over* those numbers — lunges,
backpedals, a desperate close, the brute heaving for breath. *(Historical
note: this goal originally read "range exists only as prose color, never a
tracked variable." The Ranged Combat add-on, 2026-07-16, deliberately
overturned that — distance is now ONE tracked number per fighter, the
minimum that makes bows and guns real. The spirit stands: everything finer
than that number — footwork, cover, the shape of the ground — remains prose.)*

**7. Three entity tiers with distinct identities.** Humans face real tradeoffs.
Heroes *break* the tradeoff (that's what superhuman means). Monsters are defined
by lopsidedness — each one a different tactical puzzle.

---

## Design spine (the principles above the mechanics)

*(Moved here from plan.md, 2026-07 — plan.md is now roadmap-only.)*

**The one principle: simulate inside the fight; go gamey between fights.**
Magic is the membrane that lets gamey effects reach into the simulated body.
Decision rule for any "realistic or gamey?" question: *does it happen during
the fight or around it?* During → lean simulation. Around → lean game.

**The three currencies (non-overlapping on purpose):**

| Currency | Source | Buys | Never buys |
|----------|--------|------|------------|
| **XP / Levels** | Winning encounters | Permanent ability: skills, weapon proficiencies (free allocation) | Stats |
| **Gold** | Loot, quests, selling trash | Staying power: consumables, ammo, trash gear, rest/services | Named weapons |
| **Loot & Quests** | Authored rewards | Power spikes: the cool/Named weapons, stat-transcending items | (n/a) |

The rule that keeps the economy from going flat: **gold buys staying power,
not power** — softened by decision (2026-07) to a guideline: the real intent
is that XP and gold shouldn't feel like the same currency. Plain-tier quality
weapons may be shopped for gold; masterwork/legendary stay found/quested.

**Stats are the simulated body, fixed at creation** — never raised by
levelling. A genetic cap defines each stat's ceiling; only magic and rare
items can push a stat past its natural value (the membrane in action). The
full set is five, all shipped: DEX/STR/STA (combat, built), **MIND**
(magic — the planned "INT", renamed: it scales/gates spells the way STR
scales weapons, and reads quest levels — the Magic & Mind add-on,
2026-07-15), **CHA** (the meta/party layer — companions, recruitment;
never acts inside a fight).

**Progression is free allocation, never use-based.** Levels grant points
spent on skills and proficiencies, a la Fallout — *what you are*, not *what
you've done*. A character can be the explosives specialist whose skill never
comes up; that's identity, valued for flavor.

**Tone: heroic, not gritty (for now).** Travel with a backpack and no
bookkeeping — no inventory management, hunger, disease, upkeep, or
maintenance meters. Weapons carry an inert `bulk` field; if carrying ever
matters it becomes STR's secondary role. The same tone permits wacky
mechanics once the basics are solid; the game is not oh-so-serious about its
own economy rules.

**Legibility is a core design constraint.** The player experiences the game
through chat narration, not character sheets — so prefer mechanics whose
fiction is self-explaining (a weapon snapping mid-fight over an invisible
+1), and lean on the log/DM display rules for the rest. Future mechanics
chosen for legibility: enemy morale and surrender, recruiting defeated NPCs,
spark-table personalities (all parked, see plan.md).

---

## Balanced for two (party size 1-4)

The game is playable by a party of **one to four** heroes, and every award,
site, and catalog level annotation is quoted at the **two-hero baseline** --
encounters are **never** rebalanced to the head count. Numbers are a real
advantage (they should be: recruiting a companion must be worth something),
but a raw one is enormous -- action economy compounds (N heroes deal N times
the damage *and* spread the incoming across N pools), so an untreated
four-hero party trivializes duo content (measured 2026-07-13: the rank-0
hideout clears
~17% solo, ~74% duo, ~97% trio, ~99% four-up). Three quiet counterweights
drag on numbers instead of any per-size tuning:

1. **Income is flat.** The purse is shared and quests pay fixed gold (four
   heroes buy four swords from the same reward), and **XP pays the job, not
   the head**: each member earns `award x 2 / party size`. A duo gets the
   listed numbers; four swords split the wages and level at half speed; a
   solo earns double. Invisible in any one fight, compounding across a
   campaign -- a big party is always a training rank or two behind where a
   duo would be.
2. **The press.** At most **2 attackers** can press one man-sized target in
   a round (`CROWD_CAP`); anyone crowded out *circles* -- no swing, no STA
   spent. You cannot get four swords around one man. Symmetric on purpose:
   it trims a big party's mob-the-mook economy *and* shields a lone hero
   from being swarmed -- both ends of the party-size range move toward the
   middle. Big monsters take more attackers (`crowd_cap` 3-4: a giant can be
   pressed from all sides), so boss fights stay full-party.
3. **Sweeps at the top.** The big monsters' multi-target attacks (below) hit
   several heroes per swing -- four heroes standing in the dragonfire take
   four times the total damage a solo would. The apex tier is naturally
   party-size-neutral.

The residual is accepted: 4 > 2 > 1 in raw power, and a solo player's real
lever is the oldest one in the game -- pick your fights (roughly two
encounter levels below a duo of the same level; a four-party can reach two
above).

---

## Stats

Every entity has three stats and a wound pool.

| Stat | What it does |
|------|--------------|
| **DEX** | Landing hits and avoiding them. Decides who connects each round. |
| **STR** | Force behind a blow (how bad the wound) and soaking incoming wounds. |
| **STA** | The attack budget: every swing spends it (defense is free). When low, you're **Winded**; at zero you're **Spent** — still swinging, but every roll crippled. The second death-track. |
| **HP**  | Wound pool. Damage is taken *as* HP loss, and lost HP is a penalty to your rolls (see Wounds). |

---

## The round loop

Each round, every combatant takes one attack in turn (party first, then foes).
**Who acts is fixed at round start; who is targeted stays live.** Everyone
alive when the round opens gets their one swing, even if felled before their
turn comes — the blows cross in the air, so killing a foe mid-round does not
cancel the blow it was already delivering (**the dying swing**: rolled with
the wounds it had at round start, and free — desperation costs no STA). But
every attacker picks a target *living at the moment it acts*, so no one wastes
a swing on a corpse. A foe dropped by First Blood (before the lines meet)
gets no dying swing.

0. **Find room to swing — the press.** At most `crowd_cap` attackers (2 for
   anything man-sized; 3-4 for the big monsters) can press one target in a
   round. An attacker with no open target **circles** instead: no swing, no
   STA — circling is free, like defending. (The party-size counterweight;
   see *Balanced for two*.) Sweeps ignore the press both ways.
1. **Pay for the swing.** Attacking costs STA (`swing_cost`, set by the
   wielded weapon — currently 1 for everything living; the pool is a swing
   budget). Defending is free — guarding is reflexive, swinging is the
   exertion. **Tireless** entities (the undead) never spend STA at all. At
   **STA ≤ 3** a fighter is **Winded** (−2 to all rolls) — the warning zone.
   A **sweep** (a monster with `sweep` > 1: the giant's arc, the bear's
   swipe, dragonfire) still costs one swing — one great blow, several
   defenders: ONE attacker roll, each caught defender rolling its own
   defense, severity resolved per target. A *fueled* sweep
   (`sweep_cost_power` — dragonfire) burns Power per use and falls back to
   single attacks when the fuel is dry.
2. **Spent.** At **0 STA** a fighter is **Spent**: still swinging every round
   (desperation is free), but at **−6 to all rolls**, attack and defense alike
   (replacing the Winded −2; wound penalties still stack on top), until the
   fight ends. Mid-fight, only a pause action buys STA back (see the add-on —
   a draught, Berserk, or War-Breath, each at the price of a round's attack
   and a −2 guard; the pause usually fires *before* Spent). Against fresh
   enemies it is a death sentence: you can't land and you get carved. But two
   spent sides *cancel each other's penalties* in the opposed roll and brawl
   on at even odds — the wound spiral still finishes the fight, so melees
   **resolve** instead of stalling. People absolutely die of tiredness now:
   that is the point. (A drawn standstill survives only as a rare safety-valve
   outcome via the round cap — no award, no clear.)
3. **Pressure roll.** Attacker and defender each roll
   `2d6 + DEX + training − (wound penalty) − (2 if Winded / 6 if Spent)`,
   **plus the weapon's pressure term**: the attacker adds their weapon's attack
   bonus and proficiency rank; the defender adds the weapon's defense mod
   (usually 0 — the staff parries at +1, the zweihander guards at −1, a
   broken weapon attacks at −2).
4. **Who lands.** Higher total connects this round. `margin` = the difference.
   (A tie is a clash — no one lands; if the defender wins, the attack is
   *parried*. Both are weapon contact: see *Durability* under Weapons.)
5. **Severity.** `severity = margin + attacker STR + weapon severity mods
   (weapon + proficiency) − defender STR`.
6. **Wound.** Map severity to a tier; the defender loses that much HP —
   subject to the **graze floors**: an exchange won by **margin ≥ 3** always
   at least grazes, no matter the soak (the universal floor,
   `GRAZE_FLOOR_MARGIN` — without it a high-STR frame literally could not be
   injured before its stamina collapsed, which made HP dead weight), and the
   rapier's own stricter floor makes *any* landed thrust draw blood. Soak
   still gates the real wound tiers; the floors only stop chip damage from
   being zeroed on a cleanly won exchange.
7. **End of round: regeneration.** A regenerator still on its feet (the
   troll: `regen`) knits that many HP back — and its wound penalty falls
   with the healing. Chip damage loses to it; you out-cut the knitting or
   you lose. At 0 HP it stays down: dead-or-down flesh doesn't knit
   mid-fight. (And a *fled* troll is a *healed* troll — the camp-and-return
   loop does not work on one.)
8. Repeat until one side has no one standing (**0 HP** = Down/dead).

### Wound tiers

| Severity | Tier | HP lost |
|----------|------|---------|
| ≤ 0 | Deflected | 0 |
| 1–2 | Graze | 1 |
| 3–4 | Wound | 2 |
| 5–6 | Grievous | 4 |
| 7+  | Crippling blow | 6 |

*(The top tier was renamed from "killing blow" on 2026-07-10: it is 6 flat HP
and only kills when it drops you to 0 unsaved, but the old name read as an
instant kill at the table. Same mechanic, honest name.)*

**The death spiral drives fights to a conclusion — geared down (2026-07-09).**
Your **wound penalty** is the HP you've lost divided by your pain divisor, so
a solid hit tilts every later round against you and the fight accelerates
instead of grinding. At the original full force (penalty = every HP lost)
the spiral overshot: the first decisive exchange decided the whole fight, so
encounters split into "took no damage" and "died" with almost nothing
between — wounded fighters (both sides) were helpless, and a bandit room
either blanked the party or killed it. The regear puts trained fighters at
**pain 2** (below), halving the spiral: wounds still bend a fight, but a
hero at half HP is *in trouble*, not already dead. Measured effect: the
share of cleared starter-site runs ending in the 10–70% HP-lost middle went
from thin to ~4 in 5 — "I'm low on HP" is now a state you play in, not a
death sentence you watch. The spiral is also **visible to the player** now:
the player log prints `-n to rolls` on every wound line, same as the full
log — a number the player budgets around must be a number the player sees.

**The pain divisor** (2026-07; generalizes the old undead-only halving):
every entity has a `pain` value and its wound penalty is `HP lost // pain`.
The ladder (rebased 2026-07-09: **2 is the trained-fighter norm**):

| Pain | Who | What it means |
|------|-----|---------------|
| 1 | Small beasts, untrained flesh (wolf, spider) | Feels everything — the spiral at full force. They fold fast once cut; that's their nature. |
| 2 | **Heroes and humanoid foes** (the trained norm), undead, brutes (boar, bear, ogre, troll) | Penalty halved (integer — a graze costs nothing on the roll). A drilled fighter grits through wounds; fights between them last long enough for both sides to bleed. |
| 3–4 | The apex monsters (giant, drake; dragon 4) | *Barely feels pain.* **This is what makes a deep HP pool carryable at all**: at pain 1 a 50-HP dragon would be rolling at −20 while still half alive — a helpless grind, not a boss. The divisor keeps it dangerous deep into its pool, then it folds fast. |

**Undead are still the exception enemies** (deliberately — living foes teach
the system, undead break its rules): since the pain rebase their divisor (2)
matches the trained norm, so their rule-break is now purely that they are
**tireless** — they never spend STA, never go Winded, never go Spent. Against the undead the stamina
war is entirely one-sided; they don't have to beat you, just outlast you.
That is their whole threat. (Undead flesh also never heals on its own — a
hacked skeleton stays hacked across days, which is what rewards the return
trip to the barrow.)

**A severity design note (the cap on monster STR).** Severity 7+ is a
crippling blow — 6 HP, flat — so monster STR past `hero soak + ~7` buys
nothing: a giant at STR 9 already caps every landed blow. Monster threat
scales past that point through DEX (landing at all), sweeps, and pool depth,
never through more STR. If the 14-20 band ever needs landed blows to
differentiate again, the parked fix is one tier above crippling blow
("obliterating", see plan.md) — not bigger STR numbers.

---

## Weapons (Phase 4 first slice)

Every fighter wields **one weapon** — no inventory (heroic tone: swaps are
narrative, DM-arbitrated). A weapon is an **offense package**: it never makes
you harder to hit (that's DEX and training), it changes what your attacks are.

*(This section is the MELEE catalog. Ranged weapons — bows, guns, slings,
their distance model, cadence, and ammo — live in the **Ranged Combat &
the Field add-on** below, 2026-07-16. The one-weapon rule holds there too:
a ranged card carries its own melee grip line instead of a sidearm slot.)*

**The knobs** (chosen so no weapon double-dips — pressure already feeds severity
through the margin):

| Knob | What it does | Who uses it |
|------|--------------|-------------|
| Attack pressure | Added to the attack roll only | The rapier's axis |
| Severity | Flat bonus to hits that land | The zweihander's axis |
| Defense pressure | Guard mod (usually 0) | Staff +1, zweihander −1 |
| STA per swing | The burst/sustain clock | 1 for everything, for now (see note) |
| Durability | Breakage ladder, 1–6 | See *Durability* below |

> **The 2-STA heavy swing was tried and rejected (for now).** The plan was for
> heavy weapons to burn the clock faster. The sims veto it: with Spent lethal,
> halving the swing budget loses far more than any severity bonus buys back —
> every 2-STA zweihander variant was strictly worst-in-class
> (`bench_weapons.py`). The knob stays in the schema for a future with deeper
> STA pools; the zweihander's burst identity lives in the guard penalty
> instead.

### The quality four (the cool weapons)

Culturally significant, high status, and actual quality steel. Never dropped
by low common enemies; plain ones are shoppable at 60 g.

| Weapon | Atk | Sev | Def | Special | Identity |
|--------|-----|-----|-----|---------|----------|
| **Rapier** | +2 | −1 | — | **Graze floor**: a landed thrust is never fully deflected (min. 1 HP) — stricter than the universal margin-3 floor: *any* hit counts | The duelist. Lands constantly, always draws blood, wins by the spiral. Laughs at heavy soak. |
| **Katana** | +1 | +1 | — | — | The all-rounder: consistently near-best everywhere, best almost nowhere. |
| **Zweihander** | +1 | +3 | **−1** | — | The crowd-breaker: mooks die in one blow, but there's no parrying a girder. Wants STR/soak behind it. |
| **Wooden staff** | 0 | −1 | **+1** | **+1 max Power while wielded** (2026-07-17: the focus — fuel, not surgery) | The caster's weapon — deliberately poor steel, priced in support. |

Benchmark (`bench_weapons.py`, duel vs swarm win rates per stat frame):
**suited, not ranked** — the rapier is the best duelist on three of four
frames (on the precise frame it's a coin flip with the zweihander), the
zweihander sweeps every swarm column, the katana is the reliable second
everywhere, and the staff trails everywhere on purpose. No weapon tops every
cell.

### Common weapons

Trash-to-functional arms — always a *specific named weapon* in play, never "a
crude weapon". Three stat lines, many names:

| Line | Atk/Sev/STA | Durability | Weapons | Value |
|------|-------------|-----------|---------|-------|
| Crude (`cheap`) | 0 / −1 / 1 | 1 | club, dagger, whip, light hammer | 1–2 g |
| Soldier's arms (`military`) | 0 / 0 / 1 | 2 | shortsword, scimitar, spear, mace, flail, morningstar | 5–8 g |
| Heavy arms (`military`) | 0 / +1 / 1 | 2 | longsword, battleaxe, warhammer, halberd | 15 g |

Soldier's arms are the engine's old implicit baseline (0/0/1), so the
pre-weapons balance is the soldier's-arms balance. **Starting weapons**
(heroes and bandits alike): 50% crude / 45% soldier's arms / 5% heavy; a
hedge-healer (and a wizard) has a 50% chance to carry the wooden staff
instead.
Skeletons swing **rusted blades** (0/0, durability 1 — grave-steel that snaps
on honest metal).

### Craftsmanship tiers

`plain` / `masterwork` / `legendary` — and **plain is never spoken**: a weapon
is just "a rapier"; special ones are "a masterwork rapier" or a named
legendary blade. Masterwork (+1 on the weapon's signature axis, durability 5)
and legendary (hand-authored, stat-transcending, durability 6) are
**found or quested, never shopped**; only plain weapons are for sale. No
level requirements — authored placement is the gate.

**Weapon reskins (2026-07-13).** The DM can grant any catalog profile
under a display name (`give HERO club --as "shock prod"`) — the same
doctrine as foe reskins: the name is fiction, the stats never change with
the costume. For when a reskinned foe's drop would break the fiction (gun
robots leaving "a whip"). The instance serializes whole in the save;
proficiency follows the *name*, so reskin looted flavor, not a drilled
blade.

### Durability & breakage

When steel meets steel — a **parry** or a **Clash** (high-dice tie) — the
**lower-durability** weapon risks shattering:
`P(break) = 0.25% × (durability gap)²` per contact; equal durability never
breaks. Ladder: crude/rusted 1, military steel 2, wooden staff 3 (quality,
but wood), quality steel 4, masterwork 5, legendary 6. **Natural weapons**
(fangs, claws — the monsters' armament) sit outside the ladder entirely:
breakage is a steel-on-steel event, so a claw neither shatters nor shatters
the blade that parries it.

Calibrated per-fight rates (measured): a club against legendary steel snaps
in ~24% of fights; against a quality katana ~10%; quality steel against one
step better ~1%. Against a quality-armed party, a skeleton's rusted blade
snaps in ~10% of rooms — the barrow *visibly* easing as the party's gear
improves, which is the point: the asymmetry favors the player without
inflating a single number, and a `*** CRACK ***` line is the most narratable
event in the system.

A fighter whose weapon breaks fights on with what's left: **−2 attack pressure,
−2 severity**, no proficiency, no weapon specials, and nothing left to break.
Re-arming (loot a fallen foe's blade, buy a new one) is a between-fights DM
beat.

### Flavor properties (stored, mechanically inert)

`bulk` (carry weight — no encumbrance in the heroic tone; STR's future
secondary role if that changes), `tags` (`cheap` / `military` / `ancient`,
later `orcish`... — generation flavor), `value` (gold), and `description`
(the mechanical role in plain words, so nobody has to math out what a weapon
is for).

---

## Reading the combat log

The log is written for two readers at once — the human player and the AI DM —
and since 2026-07 it comes in **two simultaneous levels** (`CombatLog` in
`rpg.py`): the **full log** (the DM/debug layer — everything below) and a
parallel **player log** (`CombatLog.player`) built at the same time, designed
to be pasted into the chat as-is. Combat lines in both levels use **short
names** ("Inga", nothing appended — a character's race, age, and traits are
sheet flavor, shown at creation and in `status`, never in the exchanges;
the old highest-stat epithet, "the precise", was removed 2026-07-11 — it
was a stat-tell in costume, and the trait system does its job better).

Within the full log, every exchange prints **two layers**:

**1. An interpretive headline** — a catchy label a spectator would use:

| Situation | Label |
|-----------|-------|
| Pressure tie, high dice (either 2d6 ≥ 8) | **Clash** — steel rings, neither yields |
| Pressure tie, low dice | **Lull** — they circle, probing for an opening |
| Attacker loses the exchange | *parried* |
| A fighter hits 0 STA | `!! X is SPENT — running on empty (-6 to all rolls until the fight ends)` |
| Hit by margin 1–2 / 3–4 / 5+ | *edges past* / *outmaneuvers* / *overwhelms* |
| Hit lands but soak zeroes the severity | *deflected* — the blow glances off |
| Wound tiers | *a graze / a solid wound / a grievous injury / a crippling blow*, with the target's HP and current roll penalty (`-n to rolls`) in brackets |

Notable events get their own lines: `!! X is Winded` when the STA threshold is
crossed, `First Blood!` on the opening strike, a Bulwark *flare* on a saved
blow (raw tier stated first — narrate the averted death),
`*** CRACK -- X's club shatters on Y's blade ***` when a weapon breaks,
`X circles, crowded out of the press` when the crowding cap bites,
`X unleashes a great sweeping blow -- Y, Z are caught in it!` announcing a
multi-target attack (then each defender's exchange resolves under it),
`X's wounds knit closed` on a regenerator's end-of-round heal, and
the `***` lines for falls, slayings, and level-ups.

**2. The raw mechanics**, indented under each headline: the actual `2d6`
result, every modifier with its source (`+DEX`, `+training`, `+rapier`,
`+proficiency`, `-wounds`, `-winded`), both totals (formatted
`Name: total (parts)`), then the full severity arithmetic
(`severity = margin + STR + weapon mods - soak -> tier`).

A `stamina:` readout prints every round — the clock is visible ticking — with
`*` marking the Winded and `!!` the Spent; tireless entities are
summarized (`3 tireless`) since their clock never moves. This full version is
deliberately complete: it is how the numbers earn trust, and the DM reads it.

**The player log** is the terser mode, kept in lockstep: headlines only, with
the HP loss folded into the wound phrase and the roll-penalty bookkeeping
dropped —

```
Round 2:
  Rhea outmaneuvers Cutthroat 2 -- a grievous injury (-4 HP)! [Cutthroat 2: 3/7 HP]
  Tomas edges past Cutthroat 2 -- a graze (-1 HP)! [Cutthroat 2: 2/7 HP]
  !! Cutthroat 2 is Winded -- -2 to all rolls
```

No pressure/severity arithmetic, no per-round stamina readout (the `!!`
Winded/Spent crossings and the pause menu carry the clock), no chase math.
Falls, slayings, weapon breaks, First Blood, Bulwark flares, XP, and loot
lines all appear in both levels. `session.py` prints the player log as a
`--- PLAYER LOG ---` block after the full log; the DM pastes it into chat
so the player gets the mechanical shape of the fight without the dice.

Since 2026-07-14 every survived encounter's block closes with the **party
tally** (`session.tally_lines`): each standing member's HP/STA/Power and
kit, the purse, the day's remaining short rests, and -- with an active
site -- the count of rooms left plus the streak's next multiplier. It is
the standard between-encounters numbers display: the DM narrates around
it instead of restating it, and it deliberately shows a *count* of what
lies ahead, never the rosters (dm.md, Narration style).

---

## Why three stats produce the loop (no range needed in the melee)

*(Written before the Ranged Combat add-on; "range" here means the old
weapon-reach/bind mechanic inside an exchange, which stays removed. The
add-on's FIELD is between-lines distance, a different thing.)*

- A **Power** build lands rarely (low DEX) but devastatingly, and is durable —
  but wants to win early, before the flat swing cost empties its pool. (The
  "big frames burn fuel faster" idea — heavy weapons costing more STA per
  swing — was sim-rejected while Spent is lethal; see the Weapons note. The
  STR build's burst identity lives in the zweihander's flat severity and
  guard penalty instead, and the `sta_cost` knob waits in the schema for
  deeper STA pools.)
- A **Precision** build lands often but softly, and is fragile — it wins by
  chipping and evading over time.
- An **Endurance** build is middling but stays sharp longest — it survives the
  Power build's burst and outlasts it, but can't catch or out-chip the Precision
  build.

Because you must *land* to deal damage, DEX gates STR for free (the old "range/
bind" mechanic, removed). Because STA degrades fighters over time, *when* you're
dangerous matters. Those two facts alone make the matchups rock-paper-scissors.

### On DEX vs STR (a design note, post-Spent)

Point for point, **DEX double-dips**: it decides who lands *and* (because
margin feeds severity) adds to the wound when you do — everything +1 STR
gives, plus the landing/avoidance. Under the original rules that made DEX
strictly dominant, and worse: since 0 STA was a *safe* guard-loop, a high-DEX
fighter could parry forever and win any fight given enough rounds. Time was
free, so the chip strategy was unbeatable.

**The Spent state is the price tag on time.** Every fighter has a budget of
full-strength swings, so the axes read: **DEX = swings that connect, STR =
swings that count, STA = how many good swings you get.** In a clean
equal-stamina 1v1 the DEX build still dominates (~75/25 at equal budget over
20k duels) — precision *is* the duelist stat, and that is accepted for now.
The working counterweights live elsewhere: STR carries hidden defense (a
spent fighter's DEX is swamped by the −6, while STR soak keeps working — the
brute survives going ragged, the fencer gets carved), a *stamina* edge now
converts directly into wins (the fresher fighter mauls the spent one — 
Endurance beats Power measurably, ~52/48 at equal points), and in the swarm
fights that fill actual play, per-swing damage decides whether you clear the
room before you run dry.

Phase 4 weapons now carry part of that counterweight: the zweihander hangs
flat severity on a STR frame (and its guard penalty leans on STR's soak), so
a brute with war steel one-shots what a fencer has to carve at. The original
plan — heavy weapons costing more STA per swing — was sim-rejected (see the
Weapons section note). If the gap still feels wrong, the next lever is
weighting STR heavier in the severity formula (a `margin + 2×(STR−soak)`
variant) — rejected for now because it soak-locks low-STR swarm enemies out
of the game.

---

## Tuning knob: luck

The `2d6` is the variance dial. Flatten it (`3d6`) and skill almost always wins —
a grim, predictable world. Widen it (`1d12`) and upsets happen — the lucky
peasant occasionally kills the knight. Set rolls to a fixed value and the sim is
fully deterministic (pure stat math), if that's the auto-battler feel you want.

---

## Entities and stat ranges

Anchor everything to humans, then let heroes and monsters break the anchor in
opposite ways.

### Humans — stats 1–5, HP 5–10
The band where tradeoffs are real: you cannot be good at everything.

| Type | DEX | STR | STA | HP |
|------|-----|-----|-----|----|
| Untrained | 1–2 | 1–2 | 1–2 | 5 |
| Trained soldier | 3 | 3 | 3 | 7 |
| Elite veteran | 4–5 | 4–5 | 4–5 | 8–10 |

**Rolled party heroes** span this band and nudge past it, on the **fixed
budget** (2026-07-13, replacing independent rolls): ranges DEX/STR/POWER/
CHA 3–6 (CHA is the fourth hero stat — see the Party, Charisma &
Satisfaction add-on), STA 5–8 (its own, higher range: STA is the second
death-track — the swing budget — so its floor matters like HP's floor; a
4-STA hero is a 4-swing hero, and the batch sims showed those parties are
the wipes), HP 8–12 — every character starts at the floors and receives
exactly **9 surplus points** dealt by a randomly-shuffled stat priority
(see the Party add-on's Character generation: equal totals, different
shapes). Plus a random ability (Heal, Bulwark, or First Blood) and two
random potions.
Racial modifiers and a couple of physical traits shift a range's **floor up
or ceiling down, never the ceiling up** (an orc's STR spans 4–6), so the
natural cap 6 below holds for every race.

### The ceilings, and what levels grow (the 1–20 doctrine)

The game runs **levels 1–20** (`100 × L` XP per level, **3 skill points
each** since 2026-07-17 — level 20 banks 57 points against an
everything-the-old-build-had cost of 63: the ~10% shortfall is the point
economy's flex premium, see the Progression add-on).

**The frame is talent; the engine is training.** DEX and STR are the body
you were born with — **fixed at creation, never raised by levels**. The
natural human cap is **6**: 5 is the career elite (the veteran row above),
6 the generational talent (the top of the hero roll). What a career grows
is everything trainable: **levels buy the pools** — +1 max HP, STA, or
Power per point, capped at +10 bought per pool (the old automatic
+1-per-two-levels curve is now the doctrine build's habit, not a law) —
plus the capped skills (training +5, proficiency +3), spells, and the
ability catalog. This split is also the balance-safe one: DEX double-dips
(landing *and* severity through the margin), so per-exchange dominance
stays behind the capped skills while levels buy staying power.

Note the spiral caps useful HP depth for anything at pain 1: penalty equals
HP lost, so a human past ~22 HP is buying corpse-phase, not survival — the
pool curve is deliberately shallow.

**Only magic and legendary gear transcend the caps** — up to roughly
*double* (DEX/STR 10–12), which is exactly the monster-apex band (dragon
DEX 8, giant STR 9): transcendence is what lets a mortal step into the
monster band, and the Heroes table below IS that band. One warning stands
for the magic phase: a +DEX item is worth several training ranks in one
slot (enemy DEX moves clear rates by tens of percent per point) — +STR and
+pool items can circulate an order of magnitude more freely than +DEX ones.

### Heroes — stats 6–10, HP 12–20 (the max-level destination)
Superhuman because they **break the mortal tradeoff**: a hero can be high in
*two or three* stats at once, which no human can. That impossible combination is
the heroic feeling. Read this table as **where the 1–20 ladder ends**: a
level-20 human with maxed training, a mastered masterwork blade, and grown
pools has exactly this table's effective numbers — the Legend row is the
character sheet of the endgame.

| Type | DEX | STR | STA | HP |
|------|-----|-----|-----|----|
| Duelist | 9 | 5 | 7 | 14 |
| Champion | 7 | 8 | 8 | 18 |
| Legend | 8 | 8 | 8 | 20 |

### The bestiary — flavor comes from lopsidedness, not big numbers everywhere
Each monster is a puzzle defined by its hole (or, for bosses, its lack of
one). The catalog lives in `sites.py` (`FOES`, with per-row **level
annotations** at the duo baseline, bench-calibrated by `bench_bestiary.py`);
**six families** span levels 1–20, each family introducing at most one
mechanic. Humanoids (bandits, soldiers, champions…) run parallel across
every level and fill the gaps between bands, and the tier ABOVE the dragon
is humanoid on purpose: demons, demigods, liches are **authored one-offs
built on the Heroes table** — heroes on the wrong side, no mortal tradeoffs,
Power fueling authored abilities — never catalog rows. The dragon is the
mightiest *beast*; the mightiest *enemies* are persons.

| Family | Rows (level) | The puzzle | Mechanic introduced |
|--------|--------------|------------|---------------------|
| **Wolves** | wolf (1), dire wolf (3) | The pack: fast, fragile, sets the pace — and PURSUES; retreating from wolves is how heroes die tired | — |
| **Beasts** | boar (2), bear (4) | The soak wall: low DEX, heavy STR both ways, slow to pain — chip damage struggles | (bear: a mauling swipe, sweep 2) |
| **Vermin** | great spider (3) | The ambusher: lands often, folds fast (venom parked with conditions, plan.md) | — |
| **Restless dead** | skeleton (2), ghoul (4), wight (8) | Tireless + slow to pain; the ghoul HUNGERS (it pursues, unlike the grave-bound); the wight is the tireless *duelist* with real DEX and lootable grave-steel | — (the exception rules) |
| **Giant-kin** | ogre (5), troll (8), giant (12) | The severity cliff — every landed blow caps; the hole is a DEX low *for its band*. The troll REGENERATES (out-damage it or lose; fleeing it resets it); the giant SWEEPS | regeneration; the sweep |
| **Drakes** | wyvern (10), drake (14), dragon (18) | Real DEX on a monster frame. The drake adds fire (fueled sweep); the dragon is a boss precisely because it has no hole at all | the fueled sweep (Power-paid breath) |
| **The soldiery** | soldier (3), veteran (6), champion (10), blademaster (15), warlord (19) | The humanoid LADDER (2026-07): living fighters under exactly the party's rules at every band — no mechanic, no hole but their humanity. Fixed military steel rising to lootable quality blades; the top ranks are *drilled* (real combat training, the `drilled +N` roster tag — how a champion outfences you without a monster's DEX). The warlord is roughly the Legend row on the wrong side | — (training, the party's own bonus) |

Natural weapons (fangs, claws, tusks, dragonfire — `NATURAL_WEAPONS` in
`sites.py`) are part of the body: they never break, never break steel
(breakage is a steel-on-steel event), and are never left as loot. The one
exception is the wight's **barrow blade** — real, lootable heavy-arms steel
with a dead man's name.

**Two scaling notes.** Pool depth *with a pain divisor* tunes the spiral: a
human at 8 HP collapses after one grievous; a dragon at 50 HP and pain 4
fights nearly clean until very deep, then folds fast — a free narrative arc
(without the divisor the deep pool would be a helpless grind instead; see
the pain ladder above). And a monster's STR difference makes it terrifying
through the severity formula even before its HP matters — up to the killing
blow cap (the severity design note above).

---

## Between-fights layer (where the player actually plays)

Partially implemented (XP/training and the potion shop exist — see the
*Progression & Economy* add-on below); the rest is what the design exists to
serve:

- **Allocate / raise stats** toward an archetype, or toward countering what's
  ahead.
- **Equip gear** that shifts stats, soaks severity, or adds STA. *(Live now:
  weapons — buy plain quality steel, loot commons, drill proficiency.)*
- **Pick your fights** — knowing the loop, choose opponents your build counters
  and avoid your counters. *(Live now: the whole quest board — levels shown
  straight, pay scaling with them; see the Quest System add-on.)*
- **Compose the party** — a PC plus a companion (same stat framework) whose
  builds cover each other's weak matchup.

The fight is deterministic-to-watch; the *interesting* decision already happened
before it started.

---

# Survival & Resources — Add-on

An add-on to the core combat ruleset above. It does **not** restate the core
(stats, round loop, wound tiers, entity tables) — it only adds the survival layer
and the few hooks the core needs to support it.

The combat core stays lethal — characters *can* die. This layer sits on top so
that, in practice, they usually don't: each averted death is narrated as a
near-thing, and the buffers that bought it visibly run out across a day.

---

## Hooks into the core (the small changes)

These are the only edits to the existing rules:

- **HP carries across the run (a lasting wound).** *(This supersedes the original
  "HP resets each fight" idea.)* HP still drives the in-fight death spiral, but it
  no longer refills between encounters: a wound persists until healed. Recovery is
  a slow catch-breath on a short rest and a **weekly knit-back on long rests** (see
  *The day / run economy*); potions/spells can top it up in a pinch.
- **0 HP = Down, not Dead.** A character at 0 is out of *this* fight only (see
  *Down, not dead* below).
- **New resource — Power.** Fuel for abilities and saves (mana, but it also
  powers martial skills). See the table below for ranges to add to each tier.

---

## Design intent

- **Lethality is real, then padded — not removed.** Compute the *raw* result
  first (which may be a crippling blow), then let resources buy it off. The
  log always states the death that *would* have happened.
- **Single fights are survivable; the campaign is the challenge.** A well-stocked
  party should win a given encounter; the fail state is attrition — running the
  buffers dry across a run of fights.
- **Two buffer layers, cleanly split.** *Between fights* (items, drunk in the
  lull — too slow to use mid-fight) and *in the moment* (Bulwark, paid in
  Power — fast enough to fire during an exchange). Flavor-true rule: **trained
  skill is reflexive; rummaging in a pouch is not.** Healing sits with the
  items — since 2026-07-17 it is a SPELL (the tenth; Magic & Mind add-on), and
  still a *between-fights* one: restoring a wound isn't something you can do
  in the half-second of an exchange either.
- **The trained answers are LEARNED (2026-07-17, the levelling framework).**
  Everyone keeps potions and the pause; Bulwark, First Blood, War-Breath,
  Berserk and the rest are catalog **abilities** bought with skill points
  (Progression add-on). The universal safety net narrows to potions on
  purpose — "who knows a conversion" is a build fact now.

---

## Resources at a glance

| Resource | Scope | Refillable? | Role |
|----------|-------|-------------|------|
| **HP** | Carries across the run (never a per-fight reset) | Trickle via short rest / a healing potion drunk between fights; the real heal is a **long rest** — HP returns over **~a week** | Lethal death-spiral inside a fight; a lasting wound between them. |
| **STA** | Per day | A **sawtooth trending down**: +1 when a fight ends, +3 per short rest (from empty, fight-end +1 plus a short rest only *just* clears Winded); rare/costly potions; **fully recharges on a long rest (overnight)**. Mid-fight it comes back only through a pause action (a draught, Berserk, or War-Breath; each costs the round's attack and a −2 guard). | The **second death-track**. Attacks spend it; at 0 you're **Spent** (still swinging, −6 to everything, until the fight ends) and fresh enemies usually finish you. Drives the matchup loop. Stays expensive to buy back mid-day on purpose. |
| **Power** | Per day | +1 per short rest, **full on a long rest** (it recharges with rest like STA, just never mid-fight); world drops | The **spendable budget** for the learned abilities (Bulwark's mid-fight absorb, First Blood's opener, War-Breath) and for every spell — the healing spell's between-fights mending included. |
| **Items** | Carried stock | The **kit restocks itself, thinly** — every long rest the PARTY scrounges up to 1 healing + 1 stamina (per party since session C, + a forage roll for a 2nd draught); anything above that is bought, found, or **brewed** (the alchemist) | The buffer: drunk in the lull for an instant top-up, or mid-fight at a pause / by standing order (the round's attack, −2 guard). Drunk AT max, a potion **overcharges** (+2 above max, spent-only — session C). |

Give each character their **own** Power and item stock, not a shared pool — it
keeps build identity alive and makes "who am I about to lose" specific.

---

## The two-buffer split

**Between fights (items — slow to reach for, instant once drunk):**
- **Healing potion** — drunk in the lull between fights, restores HP instantly
  (`HEALING_POTION_RESTORE`, currently 5). Since 2026-07-11 it also has *a
  mid-fight mode*: at a **pause** (or by standing order — see "The pause"
  below) a hero can down one in the teeth of the melee, at the cost of that
  round's attack and a −2 guard. The wound penalty lightens immediately —
  fighting the death spiral is the point, and it was the wounds trigger's
  only missing answer (its menu used to be "ignore it, bleed MORE for
  stamina, or run"). The old "between fights only" rule carried an explicit
  sunset clause — "until HP pressure proves otherwise" — and play proved
  otherwise.
- **Stamina draught** — restores STA. Deliberately **thin on the ground**,
  because STA is the un-buyable clock; cheap refills would collapse the matchup
  loop. STA otherwise recovers only slowly across a day. *Mid-fight mode:* at
  a pause or by standing order, at the same price as the healing potion
  (the round's attack, −2 guard). Between-fights drinking stays available.
- **The traveling kit (2026-07-11; SHRUNK 2026-07-17, session C)** — basic
  potions replenish themselves at camp, but thinly: **every long rest the
  PARTY scrounges up to 1 healing + 1 stamina** (a floor on the party
  *total*, not per hero — herbs at the camp fire, a vial in town), **plus a
  good-forage night** (`KIT_FORAGE_CHANCE`) that yields one extra stamina
  draught. The old per-hero floor made a bottomless free supply the sim's
  determined-camper lived on (flee, camp, retry on free draughts); the
  shrink is a real difficulty lever pulled on purpose — it closed the
  standing hideout flag to the 55-65 clear band (benchlog 2026-07-17) while
  leaving the campaign arc alone (a leveled party buys potions and camps to
  full STA regardless). Anything above the scrounge is bought (`buy`,
  `POTION_PRICE`), looted, saved, or **BREWED** (the alchemist — see the
  Alchemy add-on). Drops, purchases, and brew stack above the kit.
- **Power potion** — *retired from circulation (2026-07)*: Power was never
  the bottleneck in play, so the slot was dead weight in every kit. The kind
  still exists in the schema (an old save can drink one), but creation rolls,
  drops, and shops only circulate healing and stamina. War-Breath (the
  Power-to-STA conversion, see "The pause") now gives Power a live mid-fight
  drain; if it makes Power genuinely scarce in play, re-stock the kind.

**In the moment (learned abilities — fast, cost Power; bought from the
catalog with skill points since 2026-07-17, see the Progression add-on):**
- **Bulwark (grievous-absorb)** — *active*: when a Grievous or Killing
  blow lands, spend Power to reduce it one tier (Killing -> Grievous, Grievous ->
  Wound). Fires mid-fight, on the blow that just landed — and it can run out,
  which is the point.
- **First Blood (opening strike)** — *the aggressive counterpart*: as
  the fight begins, before the first exchange, spend Power to land a
  guaranteed graze on the focused foe. Deliberately light — 1 HP, never a free
  kill — because its real value is the death spiral: that foe fights the whole
  battle at −1 to its rolls. Priced like a Bulwark save (2 Power); where
  Bulwark buys off ~2 HP of incoming harm reactively, First Blood buys roughly
  the same swing proactively (a point of damage plus every roll the spiral now
  costs the foe).
- The rest of the catalog (Rage, Field Medic, the ranged arts...) lives in
  the Progression add-on's ability table.

**Between fights (magic — still costs Power, but not reflexive):**
- **The healing spell** — 3 Power to mend HP on yourself or an ally (3/5/7
  by rank; the casting check rolls at the caster's edge), called
  deliberately between fights (never mid-exchange; there's no time in an
  attack this fast to shape a working any more than to rummage for a
  potion). Distinct from Bulwark: proactive upkeep on the wound pool rather
  than a reactive save, and it can target a teammate. Rank 3 stands a
  Downed ally straight to 3 HP after a won fight. (2026-07-17: this
  replaces the old Heal ability — healing became magic; the hedge-healer
  starting roll is the non-wizard door into it.)

---

## STA vs Power — keep them distinct

STA is your **condition** — it drains whether you want it to or not, and it
creates the fade that powers the matchup triangle; run it dry mid-fight and
you're Spent and likely dead. Power is your **budget** — you *choose* to spend it.
Keeping them separate makes the warrior's Bulwark a real trade (skill budget
spent to live) and keeps a stamina potion a rare cheat rather than a routine
top-up — with the Spent state waiting at 0, the draught is now genuinely a
life-saver, not a convenience. (War-Breath — below — deliberately bridges the
two: Power *bought as* STA, at a poor exchange rate and the cost of a round's
attack. The budget can subsidize the condition; it can never replace it.)

---

## The pause — the interrupt primitive

One engine change carries the whole mid-fight decision layer: a fight can
**pause at a trigger and resume**. This is where the "do I fight on?" decision
finally lives — *before* Spent, which is where play never had it. In chat it
fits exactly two messages: message 1 = the fight up to the pause plus the DM's
question; message 2 = `resume ...` (or `retreat`) to conclusion.

**One pause per encounter (2026-07-11).** The party layer broke the old
per-hero interrupt: with 3–4 members each carrying two triggers, a long
fight stopped up to 2N times, each stop a full chat round-trip. The
designer's call: **an encounter pauses at most ONCE** — at the fight's
**first wounds crossing** (any member's), because "someone is being cut
apart, do we retreat?" is the one question that genuinely belongs to the
player. Every other crossing — every stamina crossing, and wounds crossings
after the pause is spent — is answered by the party's **standing orders**
(below) without stopping the fight. The engine still detects every crossing
per hero exactly as before (`standing_orders` is a session-side dispatch on
top; the batch sims run the old every-crossing pause with their policy, so
the benches answer the same questions they always did).

**Triggers** (party side only; each fires at most **once per hero per
fight**, so one hero's crisis never uses up the other's warning; checked at
the end of a round, and only while both sides still stand):
- a hero **crossing STA ≤ 2** — about to run dry;
- a hero **crossing HP ≤ half** — being cut apart.

**Crossing-only (2026-07):** a trigger whose condition already holds when the
fight starts is marked spent silently — for that hero only. Entering a fight
wounded past half or nearly out of breath was the player's informed choice at
the door — the pause exists to surface *new* information (the fight going
worse than it looked), not to re-ask a question the player just answered.
Before this gate, a wounded party re-tripped the wounds pause at round 1 of
every fight all day. (And before the per-hero keying, a hero entering wounded
silently consumed the whole party's wounds trigger — the other hero could be
cut to ribbons mid-fight without a pause.)

**Standing orders (2026-07-11).** A crossing that doesn't interrupt is
handled by the hero, on their own, at the top of the next round — at the
full pause-action price (the round's attack, −2 guard). The default order
mirrors the sims' conversion ladder, minus the retreat vote (retreat is the
player's, at the pause):
- *first, the read:* if the fight is already **winding down** — every living
  foe below half HP or Spent — do nothing; nobody burns a potion on a won
  fight (designer call: "if the enemy is low and spiralling, no potion is
  needed");
- *stamina crossing:* drink a carried stamina draught; else War-Breath —
  **if they know it** (a Bulwark hero keeps one save in reserve); else
  Berserk — **if they know it** — on a still-healthy body; else fight on.
  (2026-07-17: the conversions are learned abilities now; a hero with
  neither answers a stamina crossing with a draught or fights on. That is
  the intended new pressure — the universal safety net narrows to potions,
  and "who knows a conversion" becomes a build fact.)
- *wounds crossing (the pause already spent):* drink a carried healing
  potion.

**At the pause, the options** (pause *actions* are per-hero, at most one each;
every action costs that round's attack and the hero defends at **−2** while
occupied — vulnerable, not helpless):

| Option | Cost | Effect |
|--------|------|--------|
| **Fight on** | — | Resume; the fight then runs to its end on standing orders. |
| **Drink** | a carried stamina draught; the round's attack; −2 guard | +4 STA now, mid-fight — it even un-Spends a fighter at 0. |
| **Heal** | a carried healing potion; the round's attack; −2 guard | +5 HP now, mid-fight — the wound penalty lightens immediately (2026-07-11: the wounds trigger finally has an answer that addresses wounds; the old "between-fights until HP pressure proves otherwise" clause resolved in play). |
| **Berserk** | 2 HP; the round's attack; −2 guard; **the ability (1 point)** | +4 STA. Bleed for breath — and the HP loss deepens the wound spiral immediately, which is the real price. |
| **War-Breath** | 2 Power; the round's attack; −2 guard; **the ability (2 points)** | +3 STA. A fighter's breath discipline (battle trance), explicitly not wizardry. |
| **Retreat** | see below | Break away from the fight. |

Berserk and War-Breath are the **resource conversions**: STA is the scarce,
dynamic track, while HP and Power mostly sit idle — these give both a live
mid-fight role (a better fix for Power feeling inert than any potion).
Since 2026-07-17 both are **learned abilities** (the catalog, Progression
add-on) — Berserk's 1-point price keeps it near-universal for anyone who
wants it, which answered the old weapon-granted-Berserk parked idea.

### Retreat & chase

Deliberately **one roll** — no multi-message chase sequences.

1. **Breaking contact:** every foe fit to swing (alive, not Winded, not
   Spent) gets one **free parting blow** (free like the dying swing — no STA
   cost) at a random fleeing hero, who defends at −2 — but the blow lands
   **one wound tier lighter** than the exchange says (2026-07-10): a hasty
   swing at a moving back, not a set-piece kill. This still has teeth —
   heroes go Down at the door — but a parting blow can never land the
   crippling tier, so retreat is never an *outright death* at the door.
   *Why:* you retreat exactly when you're low, and a low hero's defense
   stacks wounds + Winded + the −2 flee penalty — before the softening,
   every parting blow against the hero who most needed to leave was a
   guaranteed grievous-or-worse, which punished the retreat call the game
   wants to be real. (Deaths in a failed retreat still happen — the chase
   failure resumes the full fight.)
2. **The chase:** ONE opposed group contest —
   `2d6 + side-average DEX weighted by current STA` (fresher legs count for
   more), the fleeing side at **+2** (the runner picks the moment and the
   ground). Only foes *fit to swing* give chase — a Winded or Spent foe
   watches you go — and only foes that *pursue* roll: **the barrow's undead
   are bound to the grave** — they swing at the door but never follow past
   it, so retreat from the barrow always succeeds once past the door. Fiction
   and mechanics agree, and "come back tomorrow and finish it" is a real plan
   instead of a death sentence from tireless pursuers.
3. **Success** = clean escape (the runners catch their fight-end breath).
   **Failure** = rare and catastrophic: the fight resumes on the spot, the
   parting-blow damage already taken.

### Encounter persistence

A fled room is not a reset room. Its survivors are recorded (per room, with a
day stamp) and wait:

- **Foe STA refills the moment the party leaves** — they rest too; a
  re-entered room is a re-fought room against breath-fresh foes.
- **Living foes heal their wounds over a day**; same-day re-entry catches
  them still hurt.
- **Skeletons stay hacked** — dead bone doesn't knit. This is exactly the
  asymmetry that rewards the return trip to the barrow.
- **A fled regenerator is a healed one** — the troll is whole again the
  moment you're out the door, same day or not. The camp-and-return loop
  does not work on it; that is its puzzle.

**The honest cost of this whole layer:** it softens "running dry is how
parties die," which the balance leans on. The counterweights: the parting
blow has teeth, a failed break is fatal-adjacent, a re-entered room is a
re-fought room against STA-refreshed foes, and the return trip burns rest
slots or a whole day. The batch sims model all of it (a crude pause policy +
one return trip per fled room — `sim_pause_policy` / `sim_fight`), so
`tune.py` keeps describing play.

---

## Down, not dead

- A character at **0 HP** is **Down** — out of this fight, not killed. The party
  fights shorthanded from that point (a real, graded cost).
- **No mid-fight revival.** Recovery is a rest event: between fights the Down get
  back on their feet, but only *minimally* (a sliver of HP) — the wound itself
  heals slowly, over days of long rest, not instantly for the next encounter.
- **Death happens only when the saves run dry** — a crippling blow lands with
  no Power for Bulwark/Heal and no buffer left. Loss is rare, earned, and
  specific to whoever was over-extended.

---

## Fate's bargain — the player character's death trade (2026-07-10)

Session play marks the PC (`party[0]`) as the **protagonist**, and one rule
guards them: **a blow that would kill the PC is commuted to a Down while at
least one companion still draws breath.** The log announces the reprieve and
its terms (*"Fate has spared them; its price comes due if this fight is
won"*). Then:

- **If the party goes on to WIN that fight**, the last foe's dying strength
  lands one final blow — and it kills **one random companion** (Down or
  standing; fate is not particular). The trade is explicit: a companion's
  life for the player's.
- **If the party loses anyway** (everyone Down/dead), it is still a wipe and
  still GAME OVER — fate spares no party that cannot win.
- **If the party retreats instead**, a clean escape **waives the debt**: no
  one died, nothing is owed — but the fight was given up, not won. (This is
  a real post-spare decision: press on and pay a companion, or flee with the
  downed PC and pay in progress.)

The spare only intercepts actual deaths (an unsaved crippling blow at 0 HP);
ordinary Downs are unchanged. A solo PC has nothing to trade and dies like
anyone. The sims never set the flag, so tuning numbers are untouched — this
is a session-play rule for why a *fragile PC build is viable at all*: the
party is the PC's real HP bar, spent one member at a time. (It also
implements the spirit of the parked "party members as lives" idea, without
the level loss.)

---

## Narrate the averted death

Compute the **raw** result before applying a save, and state both in the log:

> *The giant's club falls in a killing arc — Kestrel's ward flares and he
> staggers back merely Grievous instead of broken.* `(Bulwark: 12 Power left.)`

The player feels the lethality every time it's bought off and watches the number
buying it tick down. "Running out" becomes dread, not bookkeeping.

---

## The day / run economy

Power, potions, and stamina are the spendable survival layer; gold buys potions
and the world drops them, so exploration feeds survivability. A hard run of
fights *visibly* draws the stockpile down. The **day** is the natural unit of
attrition: the grind-down expressed as depletion of *kit and Power* rather than
HP.

**Two tiers of rest, keyed to time:**

- A **short rest** (~an hour or two of narrative time) is a limited within-day
  resource — **one slot per day** (cut from two in the 2026-07 lethality
  retune: one breather, then you press on depleted or pay the day). It gives
  a real breather (+3 STA, a sliver of HP, +1 Power) but never a reset: with
  the +1 a fight's end already gives,
  a rest from empty lands you *just* past the Winded line. The day's shape is
  a sawtooth trending down — the fights exhaust the characters faster than the
  breaks give back. Drinking potions is a *separate* deliberate act
  (see "In advance" above / `use_potion`), not folded into the rest. When the
  slot is spent there is no more mid-day recovery: the party pushes on depleted
  or makes camp.
- A **long rest** (overnight, making camp) is the real recovery: **STA and
  Power recharge
  fully** and **HP knits back at a weekly rate** (a character's nightly heal is
  scaled to their HP pool, so a full bar returns over roughly a week regardless of
  size — a big pool doesn't take proportionally longer). A long rest advances the
  day and refills the short-rest slot.
- **Where the night is spent matters (2026-07-10):**
  - **Camping in the wilds** (anywhere that isn't a settlement) risks a
    **night visitor** (~10%, rolled after the night's recovery, off the
    road's party-independent table with the same spotted/ambush valves).
    Behind settlement walls the night is safe and free. (Only the
    deliberate `camp` rolls this; travel and explore nights already price
    their own encounter risk — no double-dipping.)
  - **The tavern** (settlements only, `tavern`) is the paid upgrade: **1 g
    per living member** for the same long rest plus a **one-day
    overcharge** — everyone wakes with current HP *and* STA at +10% of
    their maximum (min +1), sitting *above* the cap (`13/12 HP`). The
    excess is spent-only: no rest, potion, or Heal tops a pool past its
    max (they only fill *toward* it), and whatever excess survives the day
    is clamped away by the next long rest. Mechanically it is a small
    pre-bought buffer for tomorrow's door — and it gives gold a drip-feed
    survival use and settlements a comfort identity. (Overcharged HP never
    grants a *negative* wound penalty; the spiral floors at 0.)

**Nothing forces the day to end.** Ending the day is a *choice* — the DM (Claude)
decides when the party camps and takes the long rest; the mechanics never
auto-camp. This keeps the tabletop freedom: you can press on wounded and Winded
into one more fight, or pull back and pay the day. The tension is *when* to spend
the day, not a timer running out on you.

---

## Power ranges to add to the entity tiers

Append to the existing stat blocks (combat stats and HP unchanged):

| Tier | Power | Notes |
|------|-------|-------|
| Human — untrained | 0 | No skills to fuel. |
| Human — soldier | 2–3 | A trick or two. |
| Human — veteran | 4–5 | Reliable saves. |
| Hero | 10–20 | Deep enough to buy off death repeatedly — until it runs out. |
| Monster | 0 | Unless it has special abilities to fuel… |
| Monster — caster/boss | up to ~20 | …e.g. a dragon spending Power on breath and skills. |

---

## Between-fights additions

On top of the existing build/allocation choices:

- **Buy and carry consumables** — stock healing potions for the wounded lulls,
  carry a rare stamina draught for the long fight, keep Power potions in reserve.
- **Spend Power deliberately** — it's offense-or-survival; every save is a skill
  not used.
- **Manage the run** — conserve resources against matchups you counter; expect to
  hemorrhage them against your counters; rest when the stockpile is dry.

---

## Implementation notes (how `rpg.py` realizes this)

- **Time is a `Clock`** (a `day` counter plus a per-day budget of short-rest
  slots, `SHORT_RESTS_PER_DAY` = 1). A dungeon run is a slice of a day. **HP
  and STA
  both carry across rooms** (never a per-fight reset). STA moves as a sawtooth:
  attacks spend it (`sta_cost`, 1 per swing), the end of a fight gives
  `STA_RECOVERY_AFTER_FIGHT` (1) back, a `short_rest` spends the slot for
  `STA_RECOVERY_BETWEEN_ROOMS` (3) + a sliver of HP + 1 Power, and `long_rest`
  makes camp
  for the full STA + Power recharge + the weekly HP tick (`hp_regen_per_night
  = max(1, round(max_hp / 7))`). Mid-fight, STA comes back only through a
  pause action (`_do_pause_action`: a drunk draught, Berserk, or
  War-Breath): an entity at 0 is otherwise Spent (`SPENT_PENALTY` = 6 to all
  rolls; it still attacks) until the fight ends, so fights always resolve;
  only the round-cap safety valve (`max_rounds`) can leave a fight
  unresolved, in which case the scenario treats the room as not cleared.
  Items are a carried stock that depletes across the run.
- **The pause is engine-level.** `group_combat(pause_triggers=True, ...)`
  returns a `Pause` (round + what tripped it) instead of finishing; the caller
  resumes with the same `fired` set, `first_round=round+1`, and optional
  per-hero `actions`. At fight start, triggers whose condition already holds
  are pre-marked fired (the crossing-only gate). `attempt_retreat` runs the
  parting blows + the one
  chase contest (`FLEE_BONUS`, STA-weighted DEX; `pursues=False` foes never
  chase); `refresh_foes_after_retreat` readies a fled room's survivors.
  Session play persists a paused fight in the save (`session.py resume` /
  `retreat`) and keeps per-room survivor records; the batch sims answer the
  same pauses with `sim_pause_policy` (drink / convert / retreat, one return
  trip per fled room) so tune/bench numbers describe the same game.
- **No auto-night.** `long_rest` is called deliberately (by the DM), never by the
  dungeon loop — the day ends when the player chooses to camp, not on a timer.
- **Saves are automatic and conservative.** A Bulwark-knowing character spends
  Power to buy off a *crippling* blow whenever it can (Crippling -> Grievous),
  and to buy off a *grievous* that would put it Down only when it can keep a
  reserve. Both the raw and the bought-down result are logged. **First Blood is
  likewise automatic** — it fires at the start of every fight while the Power
  lasts (`FIRST_BLOOD_COST` = 2 for a guaranteed 1-HP graze on the focused
  foe); trained aggression is as reflexive as a trained guard. **Healing is
  not automatic** — it has no in-fight role at all;
  `cast_healing(healer, target, ...)` is a DM-called, between-fights cast
  (same shape as `buy_potion`) that spends `HEALING_CAST_COST` (3) Power
  through the casting check for the rank's mending (`HEALING_MEND`) on
  self or an ally.
- **Potions are not automatic either.** Drinking a carried potion is a DM call,
  `use_potion(hero, kind, ...)`, between fights only (same shape as `buy_potion`
  / `cast_healing`): every potion takes effect **instantly on drink** -- *healing*
  restores HP (`HEALING_POTION_RESTORE`), *stamina* restores STA. Only those
  two kinds circulate (`STOCKED_POTION_KINDS`; the power potion is retired --
  see the two-buffer split above). Nothing in the engine drinks on its own.
  The one-shot / sim paths (`sites.run_site`) model a sensible
  party via `auto_use_potions_on_rest` (heal when badly hurt, drink stamina
  when winded), so `tune.py` / `bench_training.py` still reflect a party that
  drinks when it should.
- **Outcome semantics changed.** "Died" now means *truly slain* (an unsaved
  crippling blow), which is rare. The everyday cost is **Down** counts and the
  drawdown of Power / STA / potions — that's the attrition `tune.py` now reports.

---

# Progression & Economy — Add-on

The between-fights progression layer: XP and levels feeding the **point
economy** (2026-07-17 — pools, skills, spells, and the ability catalog all
bought from the same banked points), and a gold economy that keeps the
potion stock a real decision. Follows the design spine: **XP buys
permanent ability, gold buys staying power** — never the reverse.

## XP and levels

- **Earning.** XP pays the **job, not the head** (the party-size
  counterweight — see *Balanced for two*): awards are quoted at the two-hero
  baseline and every hero who is not truly dead earns
  `award × 2 / party size` — the same number to each, so the party still
  levels together (the divisor counts the dead too: no XP windfall for
  losing a companion mid-run). A duo gets the listed numbers unchanged; a
  solo earns double; four split the wages. Awarded per **encounter won**
  plus a lump for **completing a quest** (clearing a whole site).
- **The curve.** Level L → L+1 costs `100 × L` XP, capped at **level 20**
  (the 1–20 doctrine below).
- **Pay scales with the site's level** (2026-07, the quest system): a
  level-L site pays `site_xp_total(L) = 50 × (L + 1)` XP — ~45% paid per
  encounter as rooms fall (on the momentum streak below), the rest as the
  site-clear lump — and `15 × L` gold. The two rates this generalizes from:
  - Bandit hideout (the **starter**, a level-1 site — living foes who play
    by the party's rules): 5/15/25 XP across its three rooms in one go,
    55 XP + 15 g for the clear — a full one-go clear is exactly 100 XP, so
    the *first clear is a level-up*.
  - The skeleton barrow (the **tough** site, level 3): 10/30/50 per room in
    one go, 110 + 45 g for the clear.

  The shape is deliberate: pay grows by *half* the level-1 anchor per level
  while the level cost grows by the full step, so **leveling slows with
  rank** — one at-level site per level at the start, settling toward two
  (~35 at-level site clears from 1 to 20). And because pay follows the
  SITE'S level, not the party's, punching up pays above your weight class
  and easy work pays less — no separate under/over-level bonus exists or is
  needed.
- **The momentum streak** (2026-07-09; steepened 2026-07-10). The
  per-encounter share is paid on a rising multiplier: the k-th consecutive
  encounter cleared **in the same site without a night's camp between**
  pays `(1 + 2(k−1)) ×` the base (STREAK_STEP = 2: ×1 / ×3 / ×5 across a
  three-room site). The base is sized so a full one-go run collects exactly
  the ~45% encounter share; **camping mid-site resets the streak to base**,
  so a camp-after-every-door clear collects **~70%** of the site's total
  pay (it was ~78% at the original step of 1 — the designer wanted one-go
  clears to *feel* like the paying line). *Why:* the party can always
  retreat to camp, and a full night heals — so HP was cheap and healing,
  potions, and defense had little to buy. The streak makes pressing on the
  paying line — budgeting HP and STA across a whole site — while leaving
  the camp available at a price, and with the clear lump (55%) gated behind
  the site actually falling plus the top multiplier landing on the last
  room, **the final encounter of a one-go run carries ~80% of the site's
  total pay**. Off-script fights, road encounters, and hunts never streak
  (they pay a site's *middle* room rate, which the step change deliberately
  leaves unmoved); a retreat or an unresolved room doesn't reset the
  streak (only the night does). **Multi-site quests streak per site**: each
  site ramps ×1/×3/×5 on its own and pays its own lump — the streak never
  carries across sites, so "one site per day" is the natural paying rhythm
  and nothing forces marathoning a whole quest.
- **Level-ups grant skill points** (**3 per level** since 2026-07-17; 57
  banked by L20), spent on the menu below — free allocation, never
  use-based (the Fallout principle from the design record).
- **Nothing else is automatic.** The old odd-level pool growth is gone:
  pools joined the menu (the point economy below). DEX and STR still never
  move (see *The ceilings*).

## The point economy (2026-07-17, the levelling framework session A)

The one-sentence shape: **a level grants several points, and everything a
level can buy — pool growth included — is bought with those points, at
prices scaled to measured value.** No class gates anywhere: the first rank
of anything is buyable by anyone (the free-allocation doctrine);
prerequisites are physical only (spellBOOKS stay wizard-gated, a deep
ability rank needs its base).

| Purchase | Point cost | Cap |
|----------|-----------|-----|
| +1 max HP, +1 max STA, or +1 max Power | 1 each | +10 bought per pool |
| Combat training rank n | **2n** (was n) | 5 (unchanged) |
| Weapon proficiency rank n | n (unchanged) | 3 |
| Spell rank n, for a spell you KNOW | n (unchanged) | 3 |
| Alchemy rank n (2026-07-17, session C) | 2n | 5 |
| A warrior move (the repertoire) | 1 (iaido and the finisher 2) | repertoire ≤ training + 1 |
| Single-buy abilities | 1–3 (the catalog below) | — |

Training doubled in price because it is the measured strongest buy (a rank
moves site clear rates by tens of points — bench_training): at
rank-n-costs-n it would be strictly the best deal in the new economy, and
same-cost-same-value would be broken from day one.

**The arithmetic anchor** (why 3/level and these prices): the old default
build priced in new points is *training-at-2n + pools-at-1-each*, and it
maps almost exactly through midgame — L4: old (training 2, pools +1 each)
= 6+3 = 9 = the new budget to the point; L8: 12+9 = 21 = the budget
exactly. At L11 the old default costs 35 vs 30 banked and at L20 63 vs 57
— the new economy runs ~10-15% tighter at the top, WHICH IS THE FLEX
PREMIUM: nobody gets the old everything-for-free build plus new toys; you
fund abilities (and later moves and alchemy) by shaving pools or a
training rank. In the sims this reads as the doctrine build lagging the
old one by about a training rank through the midgame (benchlog,
2026-07-17).

## The ability catalog (single buys)

`Entity.abilities` is a set of learned tricks (`learn HERO NAME`;
`rpg.ABILITIES` is the engine reference). Everyone keeps potions and the
pause — what stopped being universal is the *trained* answers:

| Ability | Cost | Effect |
|---------|------|--------|
| **Bulwark** | 3 | the mid-fight tier-shift save, Power-paid (as ever) |
| **First Blood** | 2 | the auto opener: 2 Power, guaranteed graze (as ever) |
| **War-Breath** | 2 | the pause/standing-order conversion, 2 Power -> +3 STA — now known, not universal |
| **Berserk** | 1 | 2 HP -> +4 STA — now known, not universal |
| **Rage** | 2 | after slaying a foe: +2 to the next exchange; if that exchange fails to slay, the hero spends the following round exhausted (no attack). Mork Borg import; swingy on purpose |
| **Field Medic** | 3 | once per day, when a companion would truly DIE nearby: DEX check DC 9 — success commutes it to a Down (rapid surgery, takes the medic's next round). Fate's bargain's price can NOT be medic'd (fate is owed, not bleeding) |
| **Storyteller** | 2 | at a long rest: CHA check DC 9 (+1 per listener beyond the second) — success gives every party member +1 Power ABOVE max (overcharge rules). CHA's first in-mechanics job beyond capacity/gold |
| **Survivalist** | 2 | at a wilds camp: MIND check DC 9 — the camp counts as a tavern night (the overcharge) and the night-visitor chance is halved |
| **Arrow-Parry** | 2 / +3 for rank 2 | melee grip only: +2 defense pressure against missiles (arrows/bolts/stones/knives); rank 2 extends to bullets and rises to +3 |
| **Point-Blank Mastery** | 3 | the ranged card shoots at gap 0 — contact never forces the switch round |
| **Rapid Reload** | 3 | cadence 0 on a card that has 1 (the crossbow's heavy draw still applies) |

**The starting roll is an archetype seed** (make_human; the MIND-highest
wizard override is unchanged): the old heal/bulwark/first-blood roll
widened to a five-entry table, each grant a ~2-3-point head start that
HINTS a build without gating one — the **shieldman** (Bulwark), the
**killer** (First Blood), the **hedge-healer** (healing spell rank 1, plus
the old staff chance — the only non-wizard door into a spell), the
**herbalist** (alchemy rank 1, session C's seed), and the **drilled** (one
warrior move the starting weapon can perform — see the Warrior Moves
add-on).

**Healing became magic** (the same session): the Heal ability is deleted;
**healing** is the tenth spell (Magic & Mind add-on — unaimed utility,
between fights only, no in-fight role). Rank 1 mends 3 HP, rank 2 mends 5,
rank 3 mends 7 and stands a Downed ally straight to 3 HP after a won
fight; 3 Power per cast, the casting check per the magic add-on. One gate
loosened to make this work: **ranks are trainable in any spell you KNOW;
wizardhood keeps gating spellBOOKS** (`train_spell` dropped its wizard
check, `buy_spellbook` keeps it). And **the staff stopped paying in
healing**: the wooden staff now grants **+1 max Power while wielded** (the
focus: fuel, not surgery).

## Combat training — the general fighting skill

The veteran-vs-novice axis: *"you know how to fight."*

- **Effect:** +1 to **all pressure rolls** per rank. Because severity = margin +
  STR difference, training quietly improves *everything*: you land more, get
  hit less, and the hits you land cut deeper. One number, three effects — which
  is why it stays cheap-per-rank but caps hard.
- **Cost:** rank *n* costs **2n** skill points (2026-07-17, the point
  economy: the measured strongest buy must not also be the cheapest);
  **cap: rank 5**. On the doctrine build (pools first), rank 3 lands at
  L8 and rank 4 around L12-13 — about a rank later than the old economy,
  which is the flex premium made visible.
- **Benchmarked** (`bench_training.py`, 5k trials/rank, 2026-07-13 after
  the fixed stat budget): the skeleton barrow (tough site) clears
  **17% → 45% → 76% → 94%** across ranks 0–3 (a rank-0 duo still wipes ~4
  times in 5 — a fresh party should not be there); the bandit hideout
  (starter) clears **74% → 93% → 99% → 99.9%**
  (rank-0 wipe ~23%). Each rank is a *felt* jump — the progression test
  criterion —
  and gear stacks on top. (History: 3/17/44/74 and 64/86/96/99 at the
  2026-07-06 measure; the 2026-07-09 pain regear and the 2026-07-11 heal
  batch each lifted the whole ladder — benchlog.md holds the ledger.)

## Weapon proficiency — the second skill

Per **weapon type** (the rapier, not this rapier): each rank gives **+1 attack
pressure AND +1 severity with that weapon**. Rank *n* costs *n* points; **cap:
rank 3**. Deliberately stronger per rank than combat training because it's
narrower — offense only, one weapon — while training helps attack, defense,
and any weapon you pick up. Switching weapons keeps your training but drops
the proficiency layer until you drill the new type: that loss is the
commitment cost that makes a build a build. A broken weapon grants no
proficiency (you're swinging a stump).

**With the full menu, the PC's skill points are a real build**: points
bank on level-up (`session.py train` / `learn`) and the level-up **prints
the spending menu automatically** (2026-07-13) so the choice is always put
in front of the player. **Companions autolevel** (2026-07-13,
`rpg.autospend_points`, run after every fight's awards and at hire) on the
reference **doctrine v2** (2026-07-17: the old default build priced in the
new currency) — pools to the old odd-level curve first, then combat
training to rank 3, then proficiency once they carry a **quality** weapon
(nobody drills a club) — a wizard companion drills their **school**
instead — then training to the cap. Managing three companions' menus was
bookkeeping, not choice; the player's build decisions are the PC's. The
batch sims auto-spend on the SAME doctrine (`sites.run_site`,
bench_bestiary's reference duo), so tune/bench numbers stay comparable
across the economy change; `bench_abilities.py` is where the OTHER ways
of spending get measured.

## Gold and the potion economy

- **The purse is shared** (party-level); potions are per-hero.
- **Income:**
  - **Quests:** a level-L site pays **15 × L gold** on the clear (the
    hideout's 15 g and the barrow's 45 g are the L1 and L3 rates).
  - **Drops**, per encounter won: **20%** chance of loose coin (**5 g**, half a
    potion) and **10%** chance of a stray potion (random kind, to a random
    hero). Trash-tier on purpose — drops season the run, quests fund it.
- **Sink:** any potion costs **10 g** — but since 2026-07-11 gold only buys
  potions **above the self-restocking kit line** (every long rest tops each
  hero back up to 1 healing + 1 stamina free — see "The two-buffer split").
  `buy_potion` remains the deliberate, DM-called purchase for stocking a
  planned push; the routine baseline restock is no longer a gold sink (the
  designer's call: it was friction, not a choice). Weapons and meds carry
  the economy's sink weight now.
- **Weapons are the second sink** (`buy_weapon`, same DM-called shape): plain
  quality weapons cost **60 g** — a real saving goal (roughly four hideout
  clears of quest gold + drops); commons are shop-trivial (1–15 g).
  Masterwork/legendary are **never** for sale. This deliberately softens the
  old "gold never buys power" rule (see the design spine): a plain rapier is
  modest
  permanent power, and worth it — sim-measured (2026-07-06), a katana
  + zweihander loadout lifts a fresh party's barrow clear rate from ~3.5% to
  ~13% (though the barrow stays suicide until trained: the real
  unlock is the combination — training 2 + steel ~70%). The intended arc:
  fight the hideout at rank 0, level up *and shop* over a few clears, then
  take the barrow trained and armed.
- **Starting stock:** two *random* potions at creation (healing or stamina —
  the two circulating kinds), plus the rolled starting weapon. From then on
  the stock moves through drops, purchases, use — and the kit's nightly
  top-up to 1+1 (2026-07-11).

---

# Warrior Moves — Add-on (2026-07-17, the levelling framework session B)

**Spells for warriors, under the autocombat doctrine.** A *move* is a rider
on the normal exchange, **chosen by the engine, never a mid-fight decision**
— the same design rule that shaped magic (the autocombat doctrine in the
Magic & Mind add-on below). `Entity.moves` is a set of catalog keys, bought
with skill points
(`learn_move`; `train HERO move NAME`). The "drilled" archetype seeds one
matching the starting weapon.

## Selection & the once-per-fight rule

Each **melee attack**, every owned move whose **condition** holds and that
**hasn't fired yet this fight** rolls to fire at **50% + 10% × combat
training** (training 5 = *always* — "a better fighter has more moves,"
literally). Among the moves that pass in one exchange, the
highest-**priority** one rides it:

> finisher > iaido > disarm > sweep > trip > pommel > kick > riposte > feint
> > thrust

**Each move fires at most once per fight.** That one rule kills the
repeat-penalty bookkeeping the design circled (no combo counters, no
same-move fail states) and makes a **deep repertoire the only way to have a
rider most rounds**. Because each eligible move rolls independently, a wider
repertoire fires *more often* as well as *more variously* — the reward for
learning many.

## The flow refund (why depth pays)

Every **distinct move that fires refunds 1 STA** (toward the maximum, cap
**3 a fight**). Variety *is* the stamina engine: a two-move fighter gets two
riders and 2 STA back; a six-move blademaster fights a longer, richer fight.
**No Power costs anywhere in the system** — STA is the warrior's clock,
Power stays the spell/ability budget, and the STA-vs-Power split survives
intact.

## Weapon gating (by tags, not exception lists)

Each weapon carries `move_tags` (**pierce / blade / blunt / heavy** for
steel, **ranged** for the missile cards). A move is eligible only if the
wielded weapon carries one of its tags — so "some moves don't fit the
rapier" (pierce+blade, no butcher's heft) falls out of the tags, no per-move
exception lists. Three special gates: **iaido** is the katana's alone; the
**finisher** needs a killing arc (a blade, or a heavy blunt — a pure spear
has none); and the **wooden staff** joins **riposte** and **disarm** past
its blunt tag (2026-07-19, quarterstaff play: the +1-parry weapon answers
after a parry, and the bind-and-lever disarm is the staff's classic trick)
— with its tag's pommel/kick/trip, the caster's focus performs a real small
repertoire (5 of 11) without ever gaining a killing arc. Learning a move
requires a weapon that can perform it, and the
repertoire is capped at **combat training + 1**.

**No class gate** (the free-allocation doctrine, restated because the
levelup menu once implied otherwise): *anyone* with the points — wizards
included — learns any move their weapon performs. The wizard/warrior split
is fiction. Wizard **companions** simply don't buy moves on their own
(`autolearn_moves` skips them: their autolevel points go to the school
spell — a spending default, not a prohibition); the player can `train`
a move onto any hero with the points banked.

## The repertoire (v1)

| Move | Cost | Tags | Condition | Rider |
|------|------|------|-----------|-------|
| **Thrust** | 1 | pierce | always | +2 attack pressure this exchange |
| **Sweep** | 1 | heavy | 2+ foes at contact | the swing catches a second foe (the hero-side sweep, one roll each defends) |
| **Feint** | 1 | blade | round 2+ | the next attack on the same foe rides at +3 |
| **Pommel Strike** | 1 | blade/blunt | foe unhurt (≥ 2/3 HP) | on a wounding hit: severity −2 but the foe loses its next attack |
| **Disarm** | 1 | blade/pierce (+ the staff) | foe armed | on a decisive hit (margin ≥ 3): the weapon flies (broken-weapon state; mirrors telekinesis rank 1) |
| **Kick** | 1 | any melee | foe at contact | on a hit: the foe defends at −2 next round |
| **Trip** | 1 | any melee | round 2+ | on a decisive hit (margin ≥ 3): the foe skips its next attack AND defends −2 (prone) |
| **Riposte** | 1 | blade/pierce (+ the staff) | parried a blow last round | +2 attack pressure this exchange |
| **Iaido** | 2 | katana only | round 1 | +2 attack, +3 severity — then a round stanced (no attack). The katana's signature |
| **Finisher** (Decapitate / Split Skull) | 2 | blade / heavy+blunt | foe below 1/3 max HP | +3 severity — stretches the almost-kill into the kill; the log names it |
| **Skirmisher's Step** | 1 | ranged | a charger reaches contact | give ground to reopen the gap by a step (once per fight — kiting, ability-framed so it can't become the default dance) |

Most riders are deliberately small (~+2) and near-equivalent — the value is
**legibility** (named lines in both log levels; the DM narrates over "Rhea
feints — the cutthroat bites"), the **flow refund**, and the handful of real
**state riders** (disarm, trip, the finisher). The stun/prone riders respect
`spell_ward ≥ 2` like the magic control riders (a warded apex monster is not
pommel-stunned or tripped).

**Candidate second-wave moves, NOT in v1:** guard-break (severity ignores 2
soak — the anti-beast tool), taunt (draw one attacker onto self), battle-cry
(waits on enemy morale). **Enemy side:** hero-only in v1 (like potions and
standing orders); giving the drilled soldiery two moves each is a later
content pass with its own bench round.

---

# Alchemy & the Potion Rework — Add-on (2026-07-17, levelling framework session C)

The third and last slice of the levelling framework. Two threads: a
**difficulty lever** (the kit shrinks — the free potion faucet closes) and a
**new career** (the alchemist brews the kit the party now has to work for,
plus bombs, stat brews, and the overcharge). The design spine holds: alchemy
pays in **kit**, never gold (brewed potions are unsellable), so the economy
faucet stays shut; and the whole layer follows the autocombat doctrine —
the firebomb fires on its own like a spell, never a new mid-fight decision.

## The kit shrink (the faucet closes)

The self-restocking kit (Survival add-on) drops from **1 healing + 1 stamina
per HERO** to **1 + 1 per PARTY** — a floor on the party *total* (scrounge
only what the party lacks), plus a **forage roll** (`KIT_FORAGE_CHANCE`, one
extra stamina draught on a good night). Shops are unchanged (`POTION_PRICE`
10 g). This is a real difficulty lever pulled on purpose: the old per-hero
floor was a bottomless free supply the sims' determined-camper lived on
(flee, camp, retry on free draughts), and it was the natural closer for the
standing hideout-too-easy flag. Measured (benchlog 2026-07-17): the rank-0
hideout falls from 84.7% to the **55-65 retune band**, while careers stay
within noise (a leveled party buys potions and camps to full STA — the
shrink is a *fresh-duo* lever, exactly where the flag lived). The effect is
almost purely a function of the STAMINA floor (a duo needs two draughts per
retry — a hard integer cliff); the forage roll threads it into band.

## Alchemy — the skill

Alchemy is a **skill** (`Entity.alchemy`, rank 0-5), **open to all** (the
free-allocation doctrine — no class gate) and rolled off **MIND** (its first
non-magic customer). Rank *n* costs **2n** points (`train_alchemy`, the
training chassis — a faucet must not be the cheapest buy): 30 points to max,
so a pure alchemist maxes it around **L15** with ~12 points left for pools —
the designer's target career. The **herbalist** archetype seed grants rank 1.

**The brew.** At each long rest the alchemist rolls **2d6 + MIND + rank vs
DC 9** (the casting-check chassis, MIND-advantaged): a miss curdles the
batch, a make yields it, a beat by **7+ (or boxcars)** doubles it. The batch
and its unlocks by rank:

| Rank (cost) | Batch | Unlocks |
|-------------|-------|---------|
| 1 (2) | 1 potion (healing or stamina, brewer's choice) | — |
| 2 (4) | 1 | **strength potion** |
| 3 (6) | 2 | **firebomb** |
| 4 (8) | 2 | **dexterity potion**, **smoke vial** |
| 5 (10) | 3 | bombs at +6 / sweep 3 — "mostly rely on potions for damage" |

Brewing is **one batch per long rest** (`brew HERO RECIPE`; companions
auto-brew like they autolevel). Healing/stamina brew into the universal
stock; the rest are alchemy-only items.

**The freshness cap, not spoilage.** A hero carries at most **rank + 2**
brewed items (`Entity.brewed`, ONE integer — the fiction is freshness, "it
keeps a week or two"; per-potion spoil timestamps are exactly the inventory
bookkeeping the heroic tone forbids, and the cap fences the same degenerate
case). The brew clamps to the cap; using a brewed item reopens the room.
Brewed potions are **unsellable** (no guild seal — rotgut to a shopkeep):
alchemy pays in kit, never gold.

## The overcharge doctrine (drinking in advance)

A potion drunk with the pool **already at max** grants a flat **+2 above
max** (HP or STA by kind) instead of being wasted — spent-only, clamped away
at the next long rest (the tavern-overcharge chassis; `recover()` never
fills past max). Flat on purpose: legible, no half-restore math. (Below max,
a potion fills toward max as ever — the overcharge is only the at-full
case.)

## The stat brews (the membrane, briefly)

Potions may transcend the fixed body, temporarily: a **strength potion**
gives **+1 STR**, a **dexterity potion** **+1 DEX**, each until the next long
rest. DEX arrives two ranks later and **never exceeds +1** (the standing
warning: a point of DEX is worth several training ranks, so +DEX stays an
order of magnitude scarcer than +STR — which may stack). The buff folds into
the raw stat (so it helps everything DEX/STR touch, aim included) and the
night peels it back.

## The bombs & the smoke vial (the damage/escape career)

- **Firebomb** — an item-fueled **hero-side sweep** (the fireball chassis,
  paid in stock not Power). Thrown when **2+ foes** stand in reach and the
  fight isn't already winding down (nobody wastes a scarce bomb on a beaten
  room): attack = **2d6 + AIM + alchemy rank**, severity a **flat +4** (STR
  and the weapon out, like a cast), strikes **2 adjacent foes**, consumes
  the item. At rank 5, **+6 and 3 targets** — a brewed fireball. No misfire
  (alchemy is reliable; the fumble is scoped to casting). Fires on its own
  under the autocombat doctrine, like a spell.
- **Smoke vial** — a retreat with **NO parting blows** (the blink-out's
  first half, item-priced) — but the **chase still rolls** (unlike the
  blink, which skips both): the haze buys the exit, not the legs.
  `retreat --smoke HERO`.

Poisons and oils deliberately wait for the conditions system (the parked
venom note — alchemy is its first customer).

## Balance notes (benchlog 2026-07-17)

The alchemist is a **support/economy career, not combat parity**: the mixed
duo (alchemist + fighter) trails two fighters (L15 room 49 vs 67, site 24 vs
53), and a PURE-alchemist duo is a trap (6/3/4) like all-in pools. The
firebomb MUST stay a scarce burst (the rank+2 stock cap) precisely because
alchemy is open to all — a bomb big enough to carry a pure bomber would make
a *fighter with bombs* oppressive. The alchemist's real value is the kit it
brews for the party (which the shrink makes matter), the overcharge, and the
stat brews — none of which a one-go site run (no camp to rebrew) shows.

---

# Magic & Mind — Add-on (2026-07-15)

The full wizard layer (designed in the 2026-07-15 session; it grew out of
and REPLACES the 2026-07-14 placeholder slice — the bolts and the two
schools survive inside it as the attack spells' bottom rungs). Magic
exists **from level 1**; the inspiration is Dishonored and
Morrowind/Oblivion, not the D&D spell list — few spells, each deep.

## MIND — the casting stat

**MIND is a full creation stat** (the design spine's planned INT; "the
mind, not the IQ"): rolled 3–6 in the fixed budget beside DEX/STR/CHA
(the surplus budget rose 9 → 11 to keep the per-stat spread when the
seventh line joined), **fixed at creation, natural cap 6** — the 1-20
doctrine holds for wizards too. Its jobs:

- **The gift: MIND strictly highest of MIND/DEX/STR at creation =
  wizard** (CHA and POWER stay out of the comparison — one is social,
  the other is fuel). ~23% of rolls. A wizard rolls a **school** (fire or
  ice, 50/50) instead of an ability and starts knowing that one spell at
  rank 1; wizards often carry the wooden staff (50%).
- **The casting check's stat** (unaimed spells, below).
- **Half the AIM of a thrown cast** (aimed spells, below).
- **Quest sight** (its everyday second job, below) — MIND matters to
  parties with no wizard at all.

**POWER is fuel, never intellect** (designer call, 2026-07-15: "qi, not
iq"). It stays its own rolled pool (3–6 + the level growth), spends on
spells exactly as it spends on Bulwark or War-Breath, and never derives
from MIND. A deep-pooled dullard and a sharp-minded wisp of a caster are
both real rolls.

## Spells, ranks, and what gates them

A wizard knows **spells at ranks 1–3** (`Entity.spells`; the catalog is
`rpg.SPELLS` — ten spells since 2026-07-17, healing included; listed
below).

- **Skill points gate DEPTH**: rank n costs n points (`train HERO
  SPELLNAME`; `train HERO magic` is shorthand for the innate school) —
  the weapon-proficiency chassis wholesale, cap 3. Rank 3 of an attack
  spell is its **signature technique** (fireball, flash-freeze, hurl
  foe); rank 3 of a utility spell is usually the **roleplay tier** the
  DM adjudicates in the scene. Since 2026-07-17 depth is open to ANYONE
  who knows the spell (`train_spell` dropped its wizard gate — the
  hedge-healer's rolled healing rank is the customer); wizardhood keeps
  gating the books.
- **Spellbooks gate BREADTH**: the first spell is rolled at creation;
  every further spell needs its book — **`SPELLBOOK_PRICE` (120 g),
  capitals only** (`buy HERO book SPELL`), teaching the spell at rank 1.
  Books are shoppable by designer call (the "gold never buys power" rule
  was already softened to a guideline); masterwork-style *found* tomes
  can gate a future rank 4 when the 14-20 band gets its content pass.
- **Power costs gate the BURST** — the designer's core intent: a low-level
  wizard's big spell eats most of their pool (a rank-1 opener costs 3–4
  Power against a starting pool of 3–6), one great effect per fight; the
  pool's level growth (+1 per two levels) slowly turns the same spell
  routine. No level gates exist anywhere — point scarcity and Power do
  the pacing (the game's own doctrine: free allocation, authored
  placement, never level requirements).
- **Character math**: 19 points by L20 buy two rank-3 spells (12) plus
  combat training 3 (6) — the balanced wizard — or a third spell for the
  glass cannon who never learned to parry. "A wizard masters 2-3 spells
  in a career" falls out of the arithmetic, unlegislated.

Wizard companions autolevel into their school spell (the doctrine:
training to 3, school to cap, training on — `rpg.develop_hero`,
`autospend_points`, and the bench reference duo all follow it).

## How casting works (two shapes, mirroring the game's own split)

**1. AIMED casts** (bolts, the fireball, hurled debris) ride the normal
exchange — one opposed roll, severity, wound tiers:

- **Attack pressure = 2d6 + AIM + training + spell rank**, where **AIM =
  ceil((MIND + DEX) / 2)** — the mind shapes it, the hand throws it
  (designer call: aimed magic uses DEX too; this forks wizard builds
  into pure-MIND controllers and DEX-touched battle-mages). The weapon
  stays out of it.
- **Severity = margin + the cast's flat − soak** (STR and weapon out):
  fire +5 (the STR analogue), ice +2 (weak on purpose — every landed
  bolt **rimes**: stacking −1 DEX for the fight, and the chase's legs),
  hurled debris +4, the control techniques +2/+3. The spell's rank adds
  +1 pressure AND +1 severity, like weapon proficiency.
- **Cost: the normal swing STA + the cast's Power** (bolts 1, techniques
  2–4). Casting tires like fighting — Power is ammo ON TOP of stamina,
  never a second endurance pool. A parried or warded cast still burns
  its Power. Out of Power the wizard swings the weapon in hand.
- **Defense is unchanged**: the body (DEX + training + parry knob) —
  squishiness comes from the statline, not a rule. Bolts neither test
  durability nor risk the caster's weapon.

**2. UNAIMED casts** (the openers, the utility spells) roll the
**casting check**: `2d6 + MIND + trained rank` vs `DC = 7 + 2 × rank
cast` (+ the target's resistance for control spells, below). Degrees by
margin — the designer's five:

| Margin vs DC | Result |
|---|---|
| miss by 5+, or snake-eyes | **MISFIRE** — Power lost, action lost, the backlash grazes the caster (1 HP) |
| miss | **fizzle** — Power lost, action lost |
| make it by 0–1 | **downgrade** — resolves one rank lower (where one exists) |
| make it by 2+ | **success** |
| beat it by 7+, or boxcars | **critical** — the Power is refunded |

**Mastery: casting a technique BELOW your trained rank never rolls** —
reliability is what study buys; risk lives at the edge of the art (so a
rank-3 fire wizard's rank-1 bolts stay exactly as reliable as the
placeholder's were). **The fumble is scoped to casting**: snake-eyes on
an aimed cast's attack dice is likewise a misfire, while steel stays
reliable — the parked crit/fumble idea shipped magic-only, on purpose,
touching no melee bench.

## The spell list (ten since 2026-07-17; `rpg.SPELLS` is the reference)

| Spell | Kind | r1 / r2 / r3 |
|-------|------|--------------|
| **fire** | attack | firebolt (1 P) / rank bonus / **FIREBALL**: one roll sweeps up to 3 foes (4 P, thrown when 3+ stand) |
| **ice** | attack | rime bolt (1 P, −1 DEX stacking) / rank bonus / **FLASH-FREEZE**: a wounding bolt also costs the target its next action (4 P; rime −2) |
| **telekinesis** | attack | **DISARM**: tear a weapon away — the broken-weapon state, once per foe (2 P) / **HURL** debris (2 P, +4 flat) / **HURL FOE**: a wounding slam costs its next action (4 P) |
| **teleport** | opener | **BLINK STRIKE**: open at a foe's back — an ambush strike (3 P) / **BLINK OUT**: retreat with NO parting blows and NO chase (`retreat --blink`, 5 P; a fizzled door falls back to the honest retreat) / **TRAVEL**: step to any VISITED settlement, 3 P per road day skipped — no days, no road, no interception (`cast`) |
| **invisibility** | opener | **UNSEEN ENTRY**: untargetable until the first strike, which lands as an ambush (3 P) / **VANISH**: re-fade mid-fight — a pause action / standing order (4 P) / **GHOST-WALK**: a scene unseen, out of combat (roleplay tier) |
| **stop time** | opener | 1 / 2 / 3 **stolen strikes** — ambushes before the lines meet (4/5/6 P) |
| **possession** | opener | seize a living mind: the puppet fights for the party 1 / 2 / 3 rounds (4/5/6 P; DC + target training + 2 × ward; the dead have no mind) |
| **flight** | opener | **SKY-STEP**: aloft round 1 — melee can't reach, bolts and breath can, +1 attacking (3 P) / aloft rounds 1–2 (5 P) / *not yet written* (see below) |
| **scry** | utility | the next room's roster (2 P) / the whole site (3 P) / **the far-seeing**: the quest whole, its TRUE level, and DM-adjudicated divination (4 P) — `cast HERO scry` |
| **healing** | utility | mend 3 HP / 5 HP / 7 HP — **and rank 3 stands a Downed ally straight to 3 HP** after a won fight (3 P a cast; between fights ONLY, no in-fight role; `heal HEALER TARGET`; steadying the truly dying is the roleplay tier). The tenth spell (2026-07-17): the old Heal ability, become magic — and the hedge-healer's starting rank is the one non-wizard door into a spell |

**The assassin openers overlap on purpose** (invisibility, stop time,
teleport all open with a guaranteed strike at rank 1 — the designer's
almost-lethal-once intent): they diverge with rank (defense / multi-kill /
mobility), and all three carry roleplay value outside combat, which is
why all three stayed (designer call, 2026-07-15).

**An ambush strike is never a literal kill**: it auto-wins the exchange
at margin 6 and the **severity table is the cap** — a 7-HP bandit takes
a crippling blow and fights on at 1 HP in a deep spiral (functionally
dead), a boss soaks it and turns around. Any `spell_ward` (below) meets
an ambush as an honest exchange instead.

## The autocombat doctrine (the design rule that shaped everything)

**A spell is an opener, a sustained state, a pause/retreat option, or a
standing-order behavior — NEVER a new mid-fight decision layer.** The
one-pause promise survives untouched; the wizard's play is deciding what
to walk in under. Concretely:

- **Openers fire automatically** at fight start (First Blood's doctrine:
  trained art is reflexive, while the Power lasts), one per wizard per
  fight, best affordable first (possession > stop time > invisibility >
  teleport > flight), skipped when the fight is already winding down.
- **Attack spells are standing behavior** (`Entity.choose_cast`): disarm
  an armed foe once, spend the rank-3 technique on a healthy body, else
  bolt, else steel.
- **The pause gains two wizard actions**: `--vanish` (invisibility 2)
  and `retreat --blink` (teleport 2). The standing orders prefer a
  vanish over a healing potion on a cut-up wizard who knows it.

## Magic resistance — no new stat (settled 2026-07-15)

Three existing surfaces carry it instead:

1. **Aimed spells are dodged by the body** — DEX + training + soak
   already resist a fireball for the same reason they resist a spear.
2. **Control resists through the DC**: a possession adds the target's
   `training` and `2 × spell_ward` to the casting DC — one roll, no
   second save. The undead/tireless have no living mind: immune.
3. **`spell_ward` is a per-row monster knob** (like `pain` and
   `crowd_cap`, a puzzle piece, never a universal stat): +DC as above,
   ward ≥ 2 immune to the stun riders, ANY ward meets ambush strikes as
   honest exchanges. Current wards: dragon 3, drake 2, magus 2, wight 2,
   giant 1 — the apex keeps its bosshood through the wizard tier.

## Quest sight — MIND's second job

**The party's best living MIND reads quest levels**: 6 reads the board
exact; 4–5 within one level; 3 and under within two. A blurred read
shows as `L~7` (board, rumors, `show`, `take`), the error is rolled once
per quest at worldgen (re-asking never re-rolls), and the site sub-lines
shift consistently — the truth never leaks through a detail row. **Pay
always follows the TRUE level** — a canny player can smell a mispriced
job, which is intended flavor. Scry rank 3 outranks the blur. This
deliberately spends part of the old levels-shown-straight stance to make
MIND matter to every party (hiring the bookish companion sharpens the
whole board); `show --dm` keeps the DM's true view, and the sims read
true levels, so no bench number moves.

## Enemy casters

The three rows (hexer ice-2, pyromancer fire-2, magus fire-3) carry a
savant `mind` stat (8/8/11 — monster rows may break the human cap, same
doctrine as the dragon's DEX 8) and aim like hero wizards; their `power`
is the ammo pool, so the family's shape is unchanged: dangerous at range
until it runs dry, then a robed conscript with a knife. The magus adds
`spell_ward` 2 (no assassinating the tower's master). They keep only
bolts — enemy openers/techniques are a future pass. **Casters stay
contained content** (one caster quest per race + the Renegade Magus
epic; the 2026-07-14 career-collapse lesson stands: reach-L11 47% → 18%
when they rode the warband pool).

## Deferred with reasons (the design session's cut list)

- **Flight ranks 3–4 (all day / for good)** — blocked on the ranged
  combat model (plan.md's foundation): sustained untargetability against
  a melee-only bestiary is a win button, not a spell. Burst flight ships.
- **Summoning** — cut for now (designer call): action economy is the
  measured strongest force in the game (hideout 17/78/98% by party
  size), so a conjured body needs its own design round. Sketches kept:
  party cap 4 would count the summon, CHA could be ignored for it,
  expendable; catalog rows as the summons so the benches already know
  their worth.
- **Antimagic** — nothing to counter yet (three bolt rows); it becomes
  the wizard-duel tech when enemy magic has breadth.
- **Ward (the tier-shift shield)** — designer pass ("finicky unless very
  strong"); note it was also the provisional armor design.
- **Possession shipped instead** (mind control made the designer's cut).

---

# Ranged Combat & the Field — Add-on (2026-07-16)

Bows, guns, and distance (the roadmap's "ranged combat model" foundation +
"guns & ammo" content, shipped together). The design bar: the minimum
simulation that makes "the ranged fighter gets free attacks on the melee
one" true, mixed lines coherent (the archer stays back while the fighters
close), and cramped ground a real counter — without a battle map and
without breaking autocombat. Fights with no shooters and no open ground
play exactly as before.

## The field (the distance model)

- Every fight opens across a **field**: an abstract gap in *bounds* (one
  round's movement each). **Field 0 = the lines meet at the door** — every
  pre-ranged fight, unchanged to the digit. Rooms (site and quest
  encounters) open at **field 2** (a hall's width — one approach round, at
  most one shot loosed indoors); the road and the wilds at **field 3** (a
  longbow's whole reach).
- Each fighter carries one number: **`adv`, steps advanced from its own
  line**; the gap between two opposing fighters is
  `field − adv(a) − adv(b)`, floored at 0. One small int per body — no
  coordinates, no pair matrix — yet mixed lines just work: the fighters
  advance, the archer holds, and the gap to *each* enemy is its own.
  *(The single fight-wide counter was rejected in design: the moment one
  hero carries a bow — the whole point — it either drags the archer into
  the melee or holds the swords back. Per-pair tracking was rejected as
  illegible overkill. This is the sweet spot.)*
- **Moving is your action.** A fighter with no enemy inside its reach
  advances one bound instead of attacking (free, like circling — no STA).
  Two closing lines meet in the middle. **Chargers commit first,
  skirmishers react**: melee movement resolves before shooters decide, so
  a shooter never blunders into a charge it can see coming. Nobody moves
  backward — no kiting in v1; leaving the fight is the retreat layer.
- **Reach:** steel reaches gap 0 only. A ranged card reaches its listed
  range **but is useless at gap 0**. Aimed casts reach **range 2 at any
  gap, including 0** — magic doesn't jam at contact (so caster fights that
  used to trade bolts point-blank still do, and every caster bench stays
  meaningful).
- **Contact forces the switch:** an enemy at arm's length makes the shooter
  spend a round changing to the card's **melee grip** — every ranged card
  carries its own melee line (a bow swung as a stave is −2/−2, a
  blunderbuss stock clubs at 0/0), one weapon, two lines, no inventory,
  no proficiency (you drilled the shot, not the club). **The arrival
  volley:** the round contact *first* arrives, a still-loaded shooter
  looses point-blank into the charge before the grip must change — the
  doorway blast is the blunderbuss's whole life.
- **The press is melee geometry:** shooters at range neither consume nor
  respect crowd room. And a melee attacker crowded out of the press on an
  open field **slips deeper** instead of circling — toward whoever hangs
  back. The backline is a real position with a real escort problem, found
  by the engine, not scripted.
- Round shape stays the round shape: openers and First Blood still fire as
  the fight begins (a blink strike doesn't care about ground), the pause
  and standing orders are untouched, and autocombat resolves movement on
  its own — the one-pause promise survives.

## The shot (how shooting resolves)

A shot rides the normal exchange, the way aimed casts do:

- **Pressure: 2d6 + AIM + training + card attack bonus + proficiency**,
  where AIM is per card — pure DEX (guns, thrown), **ceil((DEX+STR)/2)**
  for bows (the draw is strength, the loose is aim — and a deliberate
  brake on DEX's double-dip), or a **flat number** (the blunderbuss: the
  spread does the aiming; the low-stat equalizer).
- **Defense: the body without the weapon** — 2d6 + DEX + training + the
  armored trait, but no parry knob (you don't parry an arrow with a
  stick; the staff's +1 and the zweihander's −1 sit out).
- **Severity = margin + the card's flat − soak, STR out** (the cast rule:
  the card's flat is the *whole* punch, which is why ranged flats run
  higher than melee weapon mods — a longbow's 5 next to a fire bolt's 5).
  The universal margin-3 graze floor applies; no rapier floors, no
  steel-on-steel breakage, no misfires (the fumble stays scoped to
  casting — powder and gut-strings are reliable arts).
- A shot costs the normal **swing STA** (a war draw is work): Winded and
  Spent drag aim like everything else.
- **Cadence:** after each shot the card's `reload` rounds must pass —
  reload ticks on any round the shooter doesn't fire, movement included.
  Reload 1 = the bow's every-2nd-round nock; the revolver's identity is
  reload 0. The crossbow's STR gate lives here: STR under 4 cranks a
  round slower — never in the aim.

## Ammo (the recurring sink, kept heroic-light)

One carried count per kind in the hero's kit line (`arrows` / `bolts` /
`shells` / `knives`); spent hit or miss. The sling scrounges stones
(free, always); the **revolver fires the wielder's own Power** (1 a
shot — the spell-bolt economy in a brass frame). `buy HERO arrows` etc.
buys by the lot; a bought or granted ranged weapon comes with a starter
load.

- Caps: 20 arrows / 20 bolts / 10 shells / 6 knives. Lots: 10 arrows or
  bolts for 5g; 2 shells for 10g; 2 knives for 4g.
- **A won field is scavenged**: each spent missile recovers at 70% if it
  hit (stuck in a body) or 40% if it missed (lost in the grass) — knives
  90/60. A *fled* field is left, arrows and all. Shells burn. Net effect:
  arrow upkeep is deliberately trivial (the bow's costs are the 60g and
  the stat demands) while **the blunderbuss shell is the ammo sink with
  teeth** — the weapon needs no stats, so the ammo carries the price, by
  design.
- Foe shooters spawn with 8 rounds and regather them if the party flees
  the room (encounter persistence: the field is theirs).

## The cards

Quality three (shoppable at plain tier like the melee four; the revolver
only where dwarves sell):

| Card | Range | Cadence | AIM | Atk | Sev flat | Melee grip | Ammo | Value |
|------|-------|---------|-----|-----|----------|------------|------|-------|
| **Longbow** | 3 | every 2nd | (DEX+STR)/2 | +1 | +5 | −2/−2 | arrows | 60g |
| **Blunderbuss** | 1 | every 2nd | flat 4 | 0 | +7 | 0/0 | shells (5g a shot) | 90g |
| **Revolver** | 2 | **every round** | DEX | −1 | +5 | −2/−2 | **1 Power/shot** | 250g, dwarven settlements only |

Commons:

| Card | Range | Cadence | AIM | Atk | Sev flat | Melee grip | Ammo | Value |
|------|-------|---------|-----|-----|----------|------------|------|-------|
| **Shortbow** | 2 | every 2nd | (DEX+STR)/2 | 0 | +4 | −2/−2 | arrows | 8g |
| **Crossbow** | 2 | every 2nd (3rd if STR<4) | DEX | −1 | +6 | −2/−2 | bolts | 15g |
| **Throwing knives** | 1 | every round | DEX | 0 | +3 | **0/−1** (it's a knife) | themselves (90/60 recovery) | 8g |
| **Sling** | 2 | every 2nd | DEX | −1 | +3 | −2/−2 | stones, free | 2g |

*(The hand bombard — range 1, flat aim, +6, 15g — is the gunner row's
common gun, so mid-band dwarf foes shoot powder without dropping 90g of
quality brass into every fight: the same economy rule that keeps quality
blades off low mooks.)*

The identities: the **longbow** owns the open field (2 shots before any
contact); the **blunderbuss** is the doorway weapon and the low-stat
equalizer (its flat 4 aim needs nobody's talent, and is outgrown by real
archers — correct); the **revolver** is magic-tech sustained fire priced
in the wielder's own Power and wants high DEX; the **crossbow** punches
like a lance and forgives nothing; **knives** are a melee-adjacent trick
(every round, short reach, mostly recovered, still a knife in the fist);
the **sling** is the peasant's reach — weak, slow, free to feed.

Sim-measured shape (`bench_ranged.py`, the doc of record): reach is an
EDGE that grows with the field and dies at the door — no ranged card
approaches the katana in a 1v1 at contact, all of them hold their own in
the played party shape (shooter + line), and a solo shooter who lets the
enemy walk in has already made a build mistake. Melee beats ranged at
contact; ranged beats the slow approach; cramped ground and ambush beat
ranged. The stat triangle is untouched: AIM reuses DEX/STR, distance is a
positional axis on top.

## Who notices whom (engagement)

The road's spotted/ambush valve decides *who saw whom first*; ranged
combat gives its words mechanical teeth (the starting field) and new
inputs (the notice contest):

- **Towering encounters (3+ levels up) keep the old contract untouched**:
  usually spotted at range, AMBUSH_CHANCE of the time they find you.
  Deadly-but-avoidable is a promise, not a roll of the conspicuousness
  dice.
- **Ordinary encounters run the notice contest**: each side rolls
  `2d6 + notice stat` against `8 + the other side's conspicuousness`.
  **Conspicuousness** = group size + a point per showy trait (armored,
  loud, colorful, flamboyant, luxurious — the presentation tables'
  first mechanics) + a clumsy-stealth point per point its *worst* DEX
  sits under 4 (stealth is a weakest-link property). The party notices
  with its **best MIND** (the watchful mind — MIND's third everyday job,
  after casting and quest sight); beasts and foes sense with the sharper
  of MIND and DEX.
- Outcomes: seen-first alone = **spotted** (the sighting persists;
  `engage` or slip past — the player's call, as ever); seeing the party
  first alone = **AMBUSH at the foes' preferred range** (their shooters
  open already shooting; an all-steel ambush is simply on you — the old
  met-blade-first); both or neither = met square across the open field.
- **Whoever picks the fight picks the ground**: `engage` and the hunt
  open at the party's preferred range — a shooter's whole reach, or a
  quiet close to contact for an all-steel party.

## Cultural arms (NPC-side, by designer fiat)

**Elves always shoot bows** (the ladder's archer, plus their own hunter
row); **goblins never do** (slings — the slinger row); **dwarves shoot
powder** (the gunner's hand bombard; the blunderbuss and revolver are
their craft). Enforced where rosters are drawn: each race's warband
templates use its own ladder variant, and a land's wild pool inherits its
templates, so the roads shoot culturally too. Humans and orcs field the
plain ladder. (The war machine's reskins — aether-rifles, rivet-guns —
stay display names over calibrated rows, doctrine unchanged.) Four
shooter rows joined the catalog: the **archer** (L1, rearmed with a real
shortbow), the **slinger** (L1), the **hunter** (L3, drilled), the
**gunner** (L4) — annotations bench-measured like every row.

## Deferred with reasons (the design round's cut list)

- **Kiting / falling back** — v1 shooters hold ground; a fall-back AI
  wants the levelling framework's movement abilities to hang on.
- **Cover as a terrain bonus** — cover is prose for now; the defense roll
  already carries DEX + armor.
- **Friendly fire into a melee** — shooters pick freely into the press;
  parked until it reads wrong in play.
- **Parting shots at a fleeing party get reach-gated instead of a new
  system**: steel needs contact, ready shooters loose across the ground,
  casters bolt within reach, everyone else watches them go. Ranged
  PURSUIT (shooting during the chase) is out of scope.
- **The three abilities** (arrow-parry for melee masters, point-blank
  mastery ~L10, rapid reload) — designed in outline, parked on the
  levelling framework (plan.md).
- **Flight ranks 3–4 unblock**: sustained flight vs a bestiary that can
  now shoot back is designable — scheduled with the magic content pass,
  not here.

---

# The Quest System — Add-on (2026-07)

The generation layer over the bestiary: a generated **world** of settlements
posting combat **quests** (1–3 sites of 1–3 encounters), every roster
assembled from the catalog by its level annotations. `quests.py` owns it;
`bench_quests.py` is its calibration harness. The two hand-built sites stay
hand-built — they are the anchors the formulas were fitted to.

## The shape

- **Quest = description + encounters, nothing more.** Deliberately dreamlike:
  the system provides the fights and one line of premise; the DM invents the
  telling. Local quests are formulaic placeholders (a race stereotype × a
  themed foe pool), not authored content.
- **Hierarchy:** a quest has 1–3 **sites** (weighted toward fewer); a site
  has 1–3 **rooms** (encounters). Multi-site quests escalate: earlier sites
  run at level −1, −2 from the quest's level. A site pays its own lump (XP +
  gold, the level formulas) when cleared; the last site completes the quest.
- **The world is generated once per playthrough, seeded** (`session.py new`),
  and lives in the save: one capital, three towns (distinct races), villages
  — quest levels rolled uniformly in a settlement band (village 1–8, town
  1–14, capital 1–20) and **displayed straight**: too easy and too hard both
  appear, reading the board is the decision. Worldgen tops the board up
  until it posts **1.35× the XP a duo needs to reach level 20** — coverage
  is asserted at generation, and the surplus is grind room (a party that
  only took at-level work would die compounding the risk).
- **Five races, one catalog: reskinning.** Display name is fiction, the stat
  row is mechanics — a goblin "Scrap-Hound" is the wolf row, a dwarf
  "Hold-Lord" the wight. Balance never forks on a skin.

## The threat math (dumb on purpose, sim-verified)

All of it lives in `quests.py` as tuned constants; `bench_quests.py` is the
proof. One catalog level ≈ **×1.5 threat**; a member of a row is worth
`1.5^level / ref_pack` units; a **site's whole roster is ~2 at-level
reference encounters' worth**, split over its rooms in rising shares (the
rule the hand-built sites turned out to already follow). Three hard lessons
the bench taught, now rules:

- **Crowding surcharge:** room members are priced by pack-equivalents — a
  body bought while N whole packs already stand costs `2^N` its base value
  (a 4th skeleton is cheap; anything joining a dragon is not). Action
  economy against a duo scales super-linearly; linear pricing measured
  rooms ~15 levels hot.
- **A room never exceeds ~1.4 pack-equivalents**, whatever the pricing — a
  reference pack plus a shade is all the bestiary bench ever validated.
- **Solo-boss rows (ref_pack 1) fight alone.** Their fairness against a duo
  IS the party's action-economy advantage; a second apex body deletes it.

The final room of a site may carry an anchor up to ~1.35× its budget — the
boss rule: the ogre quest ends with the ogre.

**Measured honesty** (`bench_quests.py`, 300/cell, after the 2026-07-09
pain regear): generated at-level rooms win 61–93% against the reference duo
across the whole 1–20 line and generated at-level sites clear ~80–87% at
levels 1–5, sliding to ~34–55% at 15–20. The −2 column (fighting two levels
over your head) is now a **coin flip to a hard fight (~30–80%) rather than
a wall** — a deliberate consequence of the regear: the viable level band
widened, so punching up is a real choice and being overleveled for a quest
is comfortable, which is what a leveled open world needs to be playable.
Current numbers live in develop.md ("Balance / tuning").

## What careers measure (updated 2026-07-09)

The career sim (fresh duo, fresh world, grind-below-level policy, camps
between rooms — so it mostly earns the piecemeal streak rate) reaches
**L5 68% / L8 56% / L11 38% / L14 20% / L20 6%**; median death at level 8.
The pain regear moved every number sharply survival-ward from 2026-07-08's
roguelike curve (L5 46 / L11 14 / L20 ~0, median death L3-4): the rank-0
front door now claims far fewer careers, and a capped career takes ~148
days / ~37 quests. The top band is still the hard edge (per-quest wipe
40–65% at 15–20 at level) and still waits on masterwork gear, armor, and
magic (plan.md) for its missing player power — but a full 1–20 career is
now merely harsh, not a lottery.

## Cross-land deliveries (2026-07-14)

The quest kind that sends the party **travelling**: taken at its origin
settlement, paid at a named settlement in another land. No sites — the
road is the content:

- **Pay scales with the trip**: 20 g + 25 XP per one-way travel day (the
  standard cross-land run is 2 days: 40 g + 50 XP). Gold-rich for the
  effort — the courier premium — and XP-light next to site work: walking
  isn't fighting. The CHA negotiation bonus applies like any quest gold.
- **One guaranteed interception** on the travel leg that reaches the
  destination: a road-table event at chance 1 — the road's own
  party-independent level table, spotted/ambush valves included, paying
  its own wild XP. It cannot un-deliver: winning it, fleeing it, or
  slipping past a sighting all still end at the gates.
- **Arriving IS the turn-in** (the site-less quest's cursor is "arrive"):
  the hand-off fires whenever the party stands at the destination with
  the quest active — at travel arrivals, or when a fight there settles.
  Every delivery carries a giver face at the origin AND a **recipient**
  face at the destination (the turn-in scene), plus an epilogue. An
  occupied destination cannot pay — the delivery waits on the war.
- **A couple per world** at worldgen (2), posted ON TOP of the XP coverage
  target (courier work is travel pay, not the climb). On the board a
  delivery shows **DELIVERY** where a level would go: the road's danger
  is the road's table, not a site level.

---

# The World & Navigation — Add-on (2026-07-09)

The geography over the quest system: the party is always **somewhere**, and
where they are decides what work they can see and take. Deliberately
list-shaped, not spatial — no coordinates, no hex map. `quests.py` owns the
constants and tables (top of file); `session.py` owns the state and moves.

## The map

- **Lands.** Each race's land holds its settlements and its wilderness; a
  land exists exactly when its race has at least one settlement. `map`
  lists them all — the world is known in outline from day one; what's *in*
  the wilds is not.
- **Location.** The save carries where the party stands: a settlement, or a
  discovered wilderness place. A new game starts at the settlement posting
  the world's lowest-level open quest (2026-07-13 — the opening hook must
  be takeable). The two hand-built set sites (hideout, barrow) lie outside
  the **capital** (the first settlement worldgen made) and are **DEV/TEST
  calibration content only** since 2026-07-13 — presented alongside
  generated quests they confused the board's fiction, and the generator
  covers the level band; the benches still run them.
- **Quests are local — but word travels (2026-07-11).** `board` shows the
  CURRENT settlement's full board, and taking or working a quest still
  means being at the settlement that posted it. But the player now also
  KNOWS every other open quest **in the current land** — name, level,
  where — as a "word from around the land" rumor list under the local
  board. Same stance as straight-shown levels: travel should be an
  informed routing decision, not a blind hop. Crossing into another land
  still means going to look. (`board all` remains as the DM's overview —
  not what the player reads.)

## Travel

- **1 day** between settlements of the same land, **2 days** crossing into
  another land. Every travel day is a camp night: the ordinary overnight
  recovery applies, so *travel heals* — and every night on the road resets
  the momentum streak, so leaving a half-cleared site costs its pay
  escalation.
- **The road rolls one encounter check per trip** (~15%/day, compounded).
  The road's level table is **party-independent** (the OSR stance): any
  level can appear, geometrically weighted toward the low end — the rare
  high tail is how the world above the party's level stays real, met on the
  road rather than read about.
- **The avoidability valve.** Anything **3+ levels above the party is
  usually spotted at range** — the sighting persists until the party moves
  on (it drifts away) or chooses `engage`: climbing into an
  over-their-weight fight is always the player's own act, never the dice's.
  **A quarter of the time the tall thing finds them first** (ambush) — then
  the fight is on, the pause is the exit, and running away is the correct
  and intended answer. Deadly-but-avoidable is the contract: death by
  random table is not. And since 2026-07-10 even **ordinary encounters
  (below that margin) are spotted first ~25% of the time** — the party
  sees the wolves before the wolves see them, and attacking (`engage`) or
  slipping past is the player's call. A quarter of the road's trouble is
  now optional trouble; the rest is simply met.

## The explore move & the hunt

- **`explore`** spends a day ranging the current land's wilds: discovers a
  new named place (persists on the map, travelable later, XP for the
  discovery), camps rough (overnight recovery, streak reset), and beats
  more bushes than the road (~30% encounter chance, same table and valve).
  Discovered places are hooks — the DM can `forge` content onto them.
- **`hunt`** is the always-available farm loop: stalk prey in the current
  land NOW (no day cost). The party chooses this fight, so unlike the road
  the level rolls at-or-below the party's (down to −2) — grinding XP, loot
  rolls, and drops is always possible. It pays **wild rates** (a site's
  mid-streak room rate, no clear lump), deliberately below board work: the
  wilds are the farm, the board is the game. What actually roams a land is
  the union of its race's template pools — a land whose cheapest fauna is
  a dire wolf has rough hunting, and that is flavor, not a bug.
  **The farm has a tax (2026-07-10): ~10% of hunts, the hunter is the
  hunted** — an AMBUSH off the road's party-independent table (any level,
  geometrically rare at the top), met blade-first with no sighting choice.
  Stalking means going where the predators are; the grind loop stays
  available but is never entirely safe, and the road's "world above your
  level" can find you on a hunt too.

## Why this shape

Everything-everywhere made the board a menu, not a world. This layer prices
distance in days (the one currency the survival game already respects),
lets difficulty live in *places* without scaling anything to the party, and
gives the "world above your level" a face the party can walk away from.
The bands stay honest: settlement kinds set quest levels exactly as before;
the road table ignores the party entirely.

---

# Party, Charisma & Satisfaction — Add-on (2026-07-11)

The character layer: who the heroes *are* (race, sex, age, traits), what
holds a party together (the PC's CHA), and what pulls it apart (companion
satisfaction). Engine constants and helpers live in `rpg.py`; the content
(races, names, trait tables, the generator) in `people.py`; the play
surface (`new`/`pick`, `recruit`/`hire`, `downtime`, departures) in
`session.py`. **None of it touches the melee or the sims**: `group_combat`
never reads a trait or a satisfaction number, sim entities never set
`cha`/`protagonist`/`satisfaction`, so every bench number is untouched by
construction (re-measured 2026-07-11 — see benchlog.md).

## CHA — the fourth stat

Set at creation like DEX/STR (range 3–6, filled from the fixed stat
budget since 2026-07-13; elves' floor is 4) and
**fixed forever**, like the other frame stats. Its two jobs:

- **Party capacity** (the PC's CHA only): `capacity = CHA − 3`, clamped
  0–3. A hard cap, not a price — no one follows a leader they don't
  believe in. CHA 3 travels **alone** (fate's bargain never fires solo;
  the game says so at creation), CHA 6 can lead a full party of four.
  Capacity is checked **per head**: a bonded pair needs two free slots.
  The counterweight is already in the engine: more companions = XP ×2/N —
  capacity buys safety at leveling speed.
- **Negotiation** (the PC's CHA only): quest/site gold lumps pay
  **+10% per CHA point above 3, capped at +30%** (`cha_gold_bonus`, applied
  in `award_quest`). **Gold only, never XP** — a compounding XP bonus would
  make CHA the best stat in the game; as gold it's an economy stat.

Companions roll CHA too (it shows on their sheet) but it does nothing yet
— hooks for later.

## The player character — generated, not chosen (2026-07-13)

`new` **generates ONE PC** (male, by designer fiat for now) — the old
three-candidate pick is gone (streamlining: the real choices are the
party's jobs and hires, not a stat-sheet beauty contest). Two guarantees
replace the pick's safety valves:

- **Minimum capacity 1**: the roll rerolls until the PC's CHA holds at
  least one companion. The capacity-0 solo game was a trap dressed as a
  choice; it no longer occurs.
- **No relatives**: the PC never rolls the family-generating quirks
  ("has a child"); a lone sword with a kid in tow was the wrong opening
  premise. "Has an enemy" stays — an enemy is story fuel, not luggage.

His sheet prints **without the satisfaction-mechanics annotations** (he
has no satisfaction track; the notes baited mechanics talk into his
introduction). A wealthy/luxurious PC starts with his trait gold in the
purse.

**The long-time companion (2026-07-13 reframe of the starter ally).** One
random level-1 companion is generated WITH the PC and presented as having
been **at his side for years** — nobody "joins" in the first scene. Hire's
normal terms otherwise (satisfaction 7, joining gold to the purse,
bond-linked to the PC). The game starts PLAYABLE — a duo walks straight
out the gate — while recruiting still fills the remaining slots.

**The opening (2026-07-13).** A new game starts at the settlement posting
the world's **lowest-level open quest**, and `new` prints that job as the
**OPENING HOOK** — the game opens at a combat quest's doorstep (giver
mid-pitch), not in a tavern. Taking it stays the player's call; the hook
is a doorstep, not a railroad.

## Character generation (recruits, and NPCs with DM edits)

`people.make_character(rng, level, ...)` builds a person at **any level**:

- **Stats — the fixed budget (2026-07-13)**: every character starts at
  the range floors (DEX/STR/POWER/CHA 3, STA 5, HP 8) and receives exactly
  **`HERO_STAT_BUDGET` = 9 surplus points**, dealt by a randomly-shuffled
  stat **priority order** (linear weights down the order, each stat capped
  at its ceiling). Equal totals, different shapes: recruiting compares
  builds — the tank, the duelist, the leader — instead of point sums,
  which under independent rolls made "highest total wins" the only hiring
  logic. 9 is the old independent rolls' mean surplus (9.5) rounded down.
- **Race**: one of the world's five (`quests.RACES`). Racial stat modifiers
  raise a roll's **floor** (orc STR 4–6, goblin DEX 4–6, elf CHA 4–6,
  dwarf HP 9–13, human plain) — and under the fixed budget a floor raise
  stays a genuine **net extra**: races remain unequal on purpose (goblin
  is the combat pick, elf the economy pick). Goblins also carry the one
  **ceiling drop**: STR 3–5 (wiry, not strong — a goblin frame lands on
  the rapier, never naturally on the zweihander), and their trait rolls
  substitute race flavor ("beautiful" → "sharp-toothed", "melodious" →
  "high, cackling").
- **Sex**: random m/f (names come from 25+25 per-race pools, `people.NAMES`
  — no epithets anywhere). A `nickname` schema slot exists, empty — no
  nickname system yet.
- **Age**: 2d20+10 (the Cairn roll, 12–50). Twelve-year-old sellswords
  happen; anime logic, designer-blessed.
- **Traits — a sketch, not a census**: ONE behavior category (temperament /
  quirk / interest / weakness / background) + TWO presentation categories
  (speech / voice / dress / looks), one trait each. What isn't described is
  typical for the archetype; the DM edits any generated contradiction
  before presenting. Most traits are DM-performed fiction; the mechanical
  few:
  - **loyal** — leaves at −3 instead of 0; **cowardly** — injury-side
    satisfaction losses ×2; **brave** — halved (toward zero).
  - **armored** (dress) — +1 defense pressure (`Entity.def_bonus`).
    Deliberately minor: armor-the-system stays a roadmap item, and the
    designer wants armor unimportant enough that looks stay varied.
  - **wealthy** (+25g) / **luxurious** (+10g) — joining gift to the purse.
  - **big** / **short** — +1 STR floor / −1 STR ceiling at creation.
  - **needs meds** — a dose every 10 days (20g, **capitals only**, `buy
    HERO meds`) or satisfaction drains 1/night until dosed.
  - **patriotic / religious / interests** — downtime targeting (below).
  - **has a child / has an enemy** (quirks) — generated inline as a name
    and a line (the enemy at level+2, for the DM to `forge` when the story
    wants it). **No recursion**: side-people never get traits of their own.
- **Level**: grown by the reference progression doctrine v2
  (`rpg.develop_hero`, the same curve `bench_bestiary`'s duo calibrates
  with): points spent monotonically (pools to the old curve → training 3
  → proficiency → training cap), quality steel from L4 **suited to the
  frame** (STR→zweihander, DEX→rapier, balanced→katana, casters keep the
  staff). Points arrive mostly **pre-spent** — choosing between candidates
  IS the customization — with a few banked for the player to allocate.

## Recruiting — on request (2026-07-13)

Candidates are gathered **when the player asks** (`recruit`, settlements
only, once per settlement per day — the day is the reroll gate): as many
**options** as the PC's capacity, each leveled to the PC ±1, full sheets
shown — transparency over realism, the same stance as straight-shown board
levels. The tavern **never pops candidates unasked** (it used to; the
pregens-every-night surface read as noise): a paid night is a bed and a
meal, and hiring is its own deliberate move. **A quarter of options are
bonded pairs** (parent and child, a married couple, mentor and mentee, two
old friends — ages fixed up so the relationship reads): one option slot,
**two heads against capacity**, joining and leaving together — better
value per slot, correlated risk. `hire NAME` signs them on at
**satisfaction 7/10**; any banked arrival points are spent on the spot
(companions manage their own points — see the Progression add-on).

## Satisfaction — the retention track

Companions only (never the PC), 0–10, floor −3. **The counter-pressure to
the momentum streak**: the streak pays you to push on; satisfaction pays
you to stop, sleep warm, and take days off.

| Event | Δ |
|-------|---|
| Site/quest lump paid out (`award_quest`) | +1 |
| Tavern night | +1 |
| Downtime day (`downtime`, settlements only) | +1 |
| Downtime day matching a trait (interest where it thrives — villages for plants/animals/hunting, capitals for art/history/fashion, towns+capitals for food/music; patriotic in their race's land; religious at a capital's temples) | +2 |
| Fled a fight * | −1 |
| Ended a fight below half HP * | −1 |
| Went Down * | −2 |
| Watched a party member die this fight * | −2 |
| "Needs meds", overdue, per night | −1 |
| A bond partner's death | → 0, wherever it was |

\* = injury-side: cowardly ×2, brave ×½ (toward zero). Down supersedes
bloodied. Plain camps and long rests are **0** — recovery is comfort, not
routine. There is deliberately **no pay-to-raise mechanic** (vetted and
cut: logical but complicated and unfun).

**Legibility**: satisfaction shows in `stat_line`/`status`; crossing 3
prints a "gone quiet" warning; crossing the leave threshold prints the
notice. At **0** (loyal: **−3**) the companion **quits at the next
settlement** — the check runs on settlement arrival and at tavern/downtime
nights, so anything that lifts them above the line before then (a paid-out
job, a warm bed) genuinely saves them.

## Departures — the purse split

The purse stays communal in play (unchanged); personal shares exist only
at the moment of leaving: a departing companion takes **an equal head-split
of the current purse** (`purse // living members`) plus their carried
weapon and potions. Bond partners walk together, whatever the partner's own
number. Dead companions are **laid to rest at the next settlement** — from
then on the party as constituted is smaller (XP shares included; between
the death and the walls the dead still count, so there is no mid-run XP
windfall). **Quality steel outlives its bearer (2026-07-13)**: a dead
companion's quality weapon stays with the party (the fight's log prints
the recovery; `give` re-arms a living hand) — commons are buried with
them, and a QUITTER still takes all their gear (that's the severance).
Fate's bargain thus has a face and a second-order cost now: the
companion it kills was hired, has traits, and may leave a grieving partner
who walks.

**Dismissal (2026-07-11).** The player can also end it: `dismiss NAME`
(settlements only) lets a companion go on **the quitter's exact terms** —
the equal head-split of the purse, their carried gear, the bond partner
walking with them. Symmetric on purpose: severance priced at zero would
make hire-use-dump-before-payday the optimal churn, and the retention
economy a revolving door. Swapping the party out at the tavern is thus a
real move (dismiss, then hire into the freed capacity) with a real price.

---

# The Story Layer & the Conquest — Add-on (2026-07-12)

The quest system gave the game its work; this layer gives the work faces,
aftermath, and a spine. Design stance: **story is people and consequences,
not new combat mechanics** — everything here rides the existing quest
schema, threat math, and pay formulas. The engine (`rpg.py`) is untouched;
the sims never see any of it.

## Quest givers & the funnel (there is no board)

Every quest carries a **giver**: a generated face (name, race, sex, age,
personality traits) whose ROLE the template authors (the reeve, the
grudge-keeper, the vent-warden). The board survives only as the **DM's
inventory readout** (`board` — each row shows whose job it is); in the
fiction there is no board at all. The protocol is the **one-message
funnel**: the party asks around — the tavern keeper knows, any local
points the way — and a single message lands them in front of the giver,
who lays out the job ("the mayor sends you to the chief constable...").
Taking the quest IS talking to the giver; the giver remains talkable while
it runs; the turn-in goes back to them. Faces come from the targeted
generator (below); worldgen attaches them, so a playthrough's givers are
permanent and learnable like everything else in its world.

## Epilogues & the day stamp

Every template authors one **epilogue** line — what happened after the
job was done — delivered at the QUEST COMPLETE banner along with a
turn-in prompt naming the giver. Completions are **day-stamped**
(`done_day`), and the in-game day now prints on the board, the map, and
the party sheet: the campaign has an official calendar, and the record of
what the party did (and when) accretes in the save — the future `history`
readout's raw material. Small mechanism, large effect: quests end as
events in a world instead of pay lines.

## The targeted NPC generator (`people.make_npc`)

Party members are rolled whole — race, background, everything — because
the dice casting the person IS the recruiting game. NPCs are the
opposite: the DM already knows the constable is a middle-aged local, so
the caller **fixes race, role, and optionally sex/age**, and the dice
roll only the name and the personality (the same 1-behavior +
2-presentation trait sketch companions get; presentation deliberately
stays fully random — a flamboyantly dressed constable is a feature).
NPCs are plain dicts with **no stat block**: if one must fight, forge the
encounter or borrow a leveled body from `make_character`. `NPC_MIN_AGE`
(20) floors the age roll for anyone with a job title.

## The central cast

Each land gets three persistent figures at worldgen, in the save for the
whole playthrough: a **ruler** (race-titled: king/queen, high thane,
speaker of the high council, great chief, chief overboss — the war-wave
questgiver), a **sage** (loremaster, court wizard... — the exposition and
foreshadowing voice), and a **wildcard** from a small role table
(spymaster, mercenary captain, master smith, high priest, war profiteer,
guild factor). The design rule for giving them life: **attach each to a
system that already exists** — the captain to recruiting, the smith to
shopping, the spymaster to rumor — rather than inventing mechanics per
NPC. They print with the board (local notables) and the map.

## Party chatter (`chatter`)

The DM's second flavor beat (dm.md owns the protocol): a seed generator
that picks 1-2 living companions and surfaces what they're preoccupied
with — a trait, plus their satisfaction state when it's loud (sullen at
<= 3, one boot out the door when quitting). Deliberately **unseeded and
stateless**: flavor must never perturb the game's dice, so `chatter`
draws from a throwaway rng and saves nothing.

## The conquest — the first questline (levels 2-10)

One aggressor race per playthrough rolls at worldgen and starts a war —
**never the PC's own race** (2026-07-13: the player fighting his own
people's war of conquest read wrong; the roll excludes it). Four
**waves**, each an ordinary multi-site quest pinned at levels
**2 / 5 / 8 / 10** (sites escalate within each wave, so the first doors
are always the easier ones). The variants:

- **Elves — the Radiant Ascendancy.** Fascist perfection: so cultured
  they should rule everyone. Magic-fuelled steampunk — everything they
  field is beautiful, efficient, well designed (automata, aether-rifles,
  colossus engines).
- **Goblins — the Thousand Workshops.** Chaotic evil tech: robots,
  bombs, bioweapons, vat-grown zany experiments.
- **Humans — the Deathless Crown.** A king corrupted by a hungry god;
  necromancy as conscription that does not end at death (the undead pool
  plus living cultist soldiery).
- **Orcs — the Iron Sky Horde.** A khagan unites the clans: might is
  right, war is glorious, everything under the iron sky is theirs.
- **Dwarves are never the aggressor** — the stalwart victim/ally land.

The mechanics, all of them reuses:

- **Rosters are reskins.** Every war body is an existing bench-calibrated
  row wearing a themed display name (`make_foe(display=...)`); v1 adds
  zero stat blocks. The **named villains** — the conqueror and two
  lieutenants, generated faces with titles — cap waves 2/3/4 as a display
  name on the strongest slot the threat math put in the final room:
  the boss fight is exactly as hard as an honest room of that level.
- **Wave gating**: wave N+1 posts when wave N's quest is DONE, the
  party has reached the wave's level, **and the party is at a
  settlement** (2026-07-13: the messenger no longer finds them mid-quest
  in the middle of nowhere — a level-up in the field keeps until the next
  town) — checked at boards, arrivals, and settlement nights, delivered
  as a day-stamped messenger scene (herald line + the ruler raising the
  call). The war can neither outrun the party nor lag it; a fresh party
  hears nothing until its first level-up.
- **Targets**: waves 1-2 press one victim land (skirmishes, then an
  invasion beaten back); wave 3 takes a second land — chosen never to be
  the capital's; wave 4 is raised from the capital against the
  conqueror's own seat.
- **Wave 3 is scripted loss.** The land falls regardless of the quest's
  outcome — success buys the evacuation (the epilogue), full quest pay,
  and the lieutenant's head, never the walls. The design point: the
  player must get something REAL out of a won quest inside a lost battle,
  or the script reads as a cheat.
- **Occupation** is light but mechanical: the fallen land's settlements
  refuse `board`/`take`/`tavern`/`downtime` (and with the tavern, all
  hiring) with one line; travel through is allowed; the map marks the
  land `[UNDER THE YOKE]`. Wave 4's victory lifts it.
- **Pay is the standard formulas** at the pinned levels — war work is
  rich because punching at your own level in 2-3-site quests is rich
  (~250/750/1200/1500 quoted XP across the four waves; the whole war
  roughly levels a party from 2 to ~10-11 on its own if pressed).

Story state (aggressor, faces, targets, wave cursors, day-stamped event
log, occupation) lives in the save under `story`. The **apocalypse
questline** — the L12-20 second spine — stays parked on the magic tier
(plan.md).

---

# Karma & Heat — Add-on (2026-07-19, the villain layer's first slice)

The 2026-07-19 design session (the villain pivot — plan.md carries the
full direction and the roadmap) turned on one idea: **the game should be
playable wickedly**, and the mechanization that makes it cheap is
**bucketing XP by the alignment of the work that paid it**. This add-on
is the pivot's first slice: dark quests, karma, heat, and the
punishment posses. Everything else about the villain direction (conquest
ticking, the greed economy, nemesis persistence, the hell frame) is
roadmap, not rules.

## Design goals

**1. Zero heat is the old game, exactly.** A party that never takes dark
work never accrues bad karma, never sees heat, never meets a posse — no
existing mechanic, bench, or sim moves. The whole layer is opt-in at the
moment of taking a job, and it lives entirely in the play surface
(`karma.py` + session wiring; worldgen and the engine are untouched).

**2. Heat is the difficulty throttle the player pumps.** The standing
problem it answers: "part of the game would be trying to gain power to
do quests above your level." Instead of reading a board for a bigger
number, the player *runs hot*: dark work pays a gold premium and bad
karma; bad karma sets HEAT; heat sends retribution **at party level +
heat**. Difficulty selection by consequence.

**3. The ratchet.** Punishment fights pay XP like any road fight — and
ALL of it is bad karma (cutting down the Watch is itself a crime). A
villain career escalates on its own: sin → posse → bigger sin → bigger
posse. That self-driving spiral IS the villain campaign's level curve.
The brakes are equally mechanical: **honest work burns bad karma 1:1**
(penance), and heat is measured against the party's level, so a grown
legend needs proportionally more wickedness to stay hot.

**4. The fights stay honest; the wickedness is prose.** A dark quest's
rosters are always things that fight back — hired guards, an aggrieved
militia, the barrow's own dead, the kicked pup's mother. The engine
never resolves violence against the helpless; the theft, the arson, the
kick are narration, in the cartoon register dm.md mandates (Discworld/
Conan, pratfall evil, never grimdark).

## The mechanics

- **Alignment.** Every quest carries `align`: `good` (all worldgen
  quests, deliveries, plain forges) or `dark` (shadow-board jobs,
  `forge --dark`). Wild/hunt/explore fights and the set sites are
  neutral — farming wolves is not penance.
- **Bucketing.** Every QUOTED XP award from aligned work is recorded
  (`session.record_karma` → `karma.record_karma`): dark XP adds to
  **bad karma** (current) and **lifetime wickedness**; good XP adds to
  **lifetime penance** and burns current bad karma 1:1. Quoted amounts,
  not per-head shares — karma tracks the deed, not the head count. The
  meter line prints with the award, in the tally, and in `status`.
- **Heat** = `bad_karma // (KARMA_HEAT_STEP × party level)`, capped at
  `HEAT_CAP` (3). KARMA_HEAT_STEP is 100, and a level-L quest quotes
  ~100·L XP — so **one at-level dark quest ≈ one heat step**, and one
  honest at-level quest ≈ one step of penance, at any level. Derived,
  never stored; levelling up cools the party's old sins by itself.
- **Punishment (the reckoning).** At heat ≥ 1, checked at travel
  arrivals, settlement nights (tavern/downtime), and camp nights — at
  most one per `PUNISH_COOLDOWN_DAYS` (2), at `PUNISH_CHANCE` (0.6) per
  eligible stop, and never stacked on a stop that already fought (the
  law is time-spaced by design). The posse is a full reference-encounter
  budget off the plain humanoid ladder at **party level + heat**,
  wearing the band's lawful display names — **the Watch** (to L3), **the
  bounty guild** (L4-8), **the crown's huntsmen** (L9-13), **heroes of
  the realm** (L14+) — led by a generated face on the strongest slot
  (the conquest-boss doctrine: a name over a budget-honest row). The
  leader's name is kept (`last_leader`) as the nemesis seed. Retreat
  works normally — escaping the law is viable; the karma stays.
- **The shadow board.** `board --dark` rolls `DARK_JOBS_PER_DAY` (3)
  dark quests for the local settlement, once per settlement day, leveled
  at the party (−1..+2) — the fixer offers what the taker can handle;
  the OSR straight-board stance belongs to the honest world. Untaken
  offers are pruned at the next roll (they melt back into the shadows);
  taken ones are ordinary quests in every way (`show`/`take`/`room`,
  progress cursor, giver turn-in, epilogue).
- **Crime pays, in gold**: a dark quest's gold is ×`DARK_GOLD_MULT`
  (1.5). This is a **deliberate small breach of the "gold buys staying
  power" spine**: the premium is the temptation, and the XP-as-liability
  is the price tag. (The full greed economy — luxury display as a karma
  engine — is roadmap.)
- **DM surface**: `karma` (the meter + lifetime ledgers), `karma bad N` /
  `karma good N` (off-script sins/penance — guideline: petty ~15,
  serious ~50, outrage ~100+), `award --dark/--good`, `forge --dark`.
  State is one plain dict in the save (`karma`).

## The Hell Pact (2026-07-19, second slice — the dark-quests session)

The frame, settled by the designer the same day the first slice shipped:
**the PC is not a neutral adventurer but a low-ranking employee of
Hell** — a mortal of an ordinary game race (not an imp; this settles
plan.md's open frame question) bound by a pact with an evil god. Wealth
and power are promised in exchange for obedience in tasks that weaken
the fabric of the orderly universe — hell's aim being exactly that
fraying (hellgates, summonings). Order is maintained by the gods of
Light and their religions (paladins, hunters, monks, priests, hired
heroes) and by worldly power (armies, watchmen, mobs) — and that order
is often not Good, which is the dark path's running joke (dm.md owns
the register). The pact rides every new save; `new --no-pact` is the
neutral game, and a pact-holder who quests honestly and stiff-arms
hell is a fully supported campaign — the mechanics below only price it.

- **Assignments.** Hell assigns Dark Tasks on its own clock: a fresh
  one lands at a settlement `TASK_INTERVAL_DAYS` (4) after the last
  resolved, printed as a WORD FROM BELOW block (delivery flavor rolled
  from `HELL_MAIL`: unseen job boards — searched for by paladins —
  black-waxed letters, ember-eyed couriers). The task is an ordinary
  dark quest flagged `hell_task`, rolled AT the party with the margin
  of error running UPWARD (spread 0..+2 — the fixer's −1..+2 belongs
  to chosen shadow work). The curriculum doctrine: each task teaches a
  type of destructive act; the shadow board and `forge --dark` are the
  self-assigned version the player graduates into.
- **Chickening Out.** An assignment may be ignored for
  `TASK_GRACE_DAYS` (4). Past that, infernal colleagues are dispatched
  at the posse stops (arrivals, nights; cooldown 2 d, chance 0.6):
  budget-honest ladder rosters wearing infernal names (`HELL_SKINS`),
  led by a generated face, at **party level + 1, +1 per beating
  already survived (capped +3 over)**. Beating them changes nothing —
  the job stands and the next visit is worse. Their XP is **neutral**:
  cutting down devils is neither crime nor penance (farming them for
  absolution would be a hole).
- **Bribes.** `bribe` pays `BRIBE_GOLD_PER_LEVEL` (30) × party level
  for `BRIBE_DAYS` (10) of no new assignments and no enforcement. An
  open assignment survives the bribe; its grace runs fresh from the
  bribe's end.
- **Left for dead (the mercy).** The PC is never killed by heroic
  adventurers — or by hell's enforcers. A posse fight lost (wipe, or
  the PC down for good) fires `apply_mercy` instead of GAME OVER: the
  PC alone survives at 1 HP; the party and the purse are forfeit.
  Against the **law**, all bad karma clears too — the heroes think him
  dead (or he ran, in shame; everyone in hell is laughing), and the
  ledger is considered settled: heat 0, a fresh start in one shoe.
  Against **hell**, the purse is the fine, the refused assignment is
  withdrawn, and the karma stays. Ordinary fights (roads, quests,
  hunts) still kill exactly as before — the mercy is the posses' rule,
  not the world's. Related doctrine (dm.md): combat the fiction says
  isn't lethal reads 0 HP as knocked out, same numbers.

### The caper structure (deeds & twists)

The formalized "more complex quest structure" for dark work — two
optional authored fields on a template, riding the site dicts through
`build_quest` (a template carrying either pins its site count):

- **Deed** (first site): `{stat, dc, text, fail}`. Before the site's
  first fight, the **PC** rolls 2d6 + stat vs the DC (printed as THE
  DEED block). A make closes the site CLEAN — full lump, no fight, and
  (a happy accident kept on purpose) none of the rooms' encounter XP,
  so stealth runs karma-light. A miss is the complication: the fight
  is on, and witnesses add `DEED_FAIL_KARMA` (15) flat bad karma. DCs
  sit at 10-11 against typical stats 3-5: *the dex check will probably
  fail, and lead to a fight* is the design sentence.
- **Twist** (last site): `{text, accept, pay}`. Arriving prints THE
  TWIST block — an authored complication with priced terms (the
  fence's half-price offer, the rival's partnership). `settle` takes
  the terms: the site closes without a fight at `pay` (0.5) × its
  lump. `room` refuses them and fights for the full pay.

Both paths close sites through `_close_site` (advance_quest's tail,
split out), so lumps, epilogues, the war hook, and the pact ledger all
fire identically however a site ends.

### Balance stance (designer directive, 2026-07-19)

**XP/gold balance is deliberately abandoned for the dark layer for
now** — a good variety of quests does the game more good than tuned
numbers. Every pact constant is hand-set and sim-unverified (no sim
sees the pact, the capers, or the mercy — all play-surface); the
seventeen-template content pass optimizes for texture, not for the
career curve. Tune at the table; a karma career sim stays parked.

## Explicitly not in this slice (roadmap, plan.md)

Conquest ticking (settlement ownership + tribute), hell as a VISITABLE
place (the gladiator pits, the castle bought in bones, bullying demons
— walkable today as pure narration), a geographic wanted level
(searched-for in one settlement / a land / all lands — heat is the
global version), the good-karma mirror (hell auditing a *virtuous*
employee — the dual campaign), nemesis persistence beyond the
remembered name, race-flavored dark templates, standing dark
enterprises (the powder network as a holding), the rot-spell and other
evil magic content, parley/bribery with the LAW's posses (hell takes
bribes now; the Watch doesn't yet), and any karma-gated power. Bad
karma currently buys nothing but heat and gold-rich work — whether it
should *unlock* anything (hell ranks, evil powers) is the next design
decision.

