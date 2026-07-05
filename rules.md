# Combat Sim — Minimal Ruleset

A combat simulator for a fantasy RPG. Fights resolve on their own; the player's
decisions happen *between* fights. Three stats, one wound track, one loop.

---

## Design goals (the "why", independent of any implementation)

**1. Autobattler, not a combat minigame.** A fight takes no input once it starts.
The simulation produces an outcome (who won, in what shape) and a narrative log.
All player agency lives *between* fights — with one deliberate exception: the
**pause** (see the Survival add-on). At most twice a fight, the simulation
stops at a trigger and asks one player-shaped question ("fight on, buy breath,
or run?"), then resumes to conclusion. That is an interrupt, not a combat
minigame: the fight still plays itself; the player only chooses *whether* it
continues.

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
backpedals, a desperate close, the brute heaving for breath. Things like "range"
exist only as prose color; they are never tracked variables.

**7. Three entity tiers with distinct identities.** Humans face real tradeoffs.
Heroes *break* the tradeoff (that's what superhuman means). Monsters are defined
by lopsidedness — each one a different tactical puzzle.

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

1. **Pay for the swing.** Attacking costs STA (`swing_cost`, set by the
   wielded weapon — currently 1 for everything living; the pool is a swing
   budget). Defending is free — guarding is reflexive, swinging is the
   exertion. **Tireless** entities (the undead) never spend STA at all. At
   **STA ≤ 3** a fighter is **Winded** (−2 to all rolls) — the warning zone.
2. **Spent.** At **0 STA** a fighter is **Spent**: still swinging every round
   (desperation is free), but at **−6 to all rolls**, attack and defense alike
   (replacing the Winded −2; wound penalties still stack on top). There is
   **no in-fight recovery** short of a stamina draught drunk at a pause (see
   the add-on — bought at the price of a round's attack and a −2 guard, and
   the pause usually fires *before* Spent) — otherwise Spent lasts until the
   fight ends. Against fresh
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
7. Repeat until one side has no one standing (**0 HP** = Down/dead).

### Wound tiers

| Severity | Tier | HP lost |
|----------|------|---------|
| ≤ 0 | Deflected | 0 |
| 1–2 | Graze | 1 |
| 3–4 | Wound | 2 |
| 5–6 | Grievous | 4 |
| 7+  | Killing blow | 6 |

**The death spiral is the whole point.** Your **wound penalty** equals the HP
you've lost, so the first solid hit tilts every later round against you and the
fight accelerates to a conclusion. There is no slow attrition to zero — one
grievous hit can decide it.

**Undead are the exception enemies** (deliberately — living foes teach the
system, undead break its rules):
- **They feel no pain:** their wound penalty is *halved* (integer —
  `HP lost // 2`, so a graze costs them nothing on the roll). Chip damage and
  spiral-based tricks (First Blood) bite less against them; you have to
  actually break the bones.
- **They are tireless:** they never spend STA, never go Winded, never go
  Spent. Against the undead the stamina war is entirely one-sided — they
  don't have to beat you, just outlast you. That is their whole threat.

---

## Weapons (Phase 4 first slice)

Every fighter wields **one weapon** — no inventory (heroic tone: swaps are
narrative, DM-arbitrated). A weapon is an **offense package**: it never makes
you harder to hit (that's DEX and training), it changes what your attacks are.

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
| **Wooden staff** | 0 | −1 | **+1** | **+1 HP per Heal** through it | The healer's weapon — deliberately poor steel, priced in support. |

Benchmark (`bench_weapons.py`, duel vs swarm win rates per stat frame):
**suited, not ranked** — the rapier is the best duelist on nearly every frame
(by a hair over the katana), the zweihander sweeps every swarm column, the
katana is the reliable second everywhere, and the staff trails everywhere on
purpose. No weapon tops every cell.

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
heal-ability hero has a 50% chance to carry the wooden staff instead.
Skeletons swing **rusted blades** (0/0, durability 1 — grave-steel that snaps
on honest metal).

### Craftsmanship tiers

`plain` / `masterwork` / `legendary` — and **plain is never spoken**: a weapon
is just "a rapier"; special ones are "a masterwork rapier" or a named
legendary blade. Masterwork (+1 on the weapon's signature axis, durability 5)
and legendary (hand-authored, stat-transcending, durability 6) are
**found or quested, never shopped**; only plain weapons are for sale. No
level requirements — authored placement is the gate.

### Durability & breakage

When steel meets steel — a **parry** or a **Clash** (high-dice tie) — the
**lower-durability** weapon risks shattering:
`P(break) = 0.25% × (durability gap)²` per contact; equal durability never
breaks. Ladder: crude/rusted 1, military steel 2, wooden staff 3 (quality,
but wood), quality steel 4, masterwork 5, legendary 6.

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
so every exchange prints **two layers**:

**1. An interpretive headline** — a catchy label a spectator would use:

| Situation | Label |
|-----------|-------|
| Pressure tie, high dice (either 2d6 ≥ 8) | **Clash** — steel rings, neither yields |
| Pressure tie, low dice | **Lull** — they circle, probing for an opening |
| Attacker loses the exchange | *parried* |
| A fighter hits 0 STA | `!! X is SPENT — running on empty (-6 to all rolls until the fight ends)` |
| Hit by margin 1–2 / 3–4 / 5+ | *edges past* / *outmaneuvers* / *overwhelms* |
| Hit lands but soak zeroes the severity | *deflected* — the blow glances off |
| Wound tiers | *a graze / a solid wound / a grievous injury / a killing blow*, with the target's HP and current roll penalty (`-n to rolls`) in brackets |

Notable events get their own lines: `!! X is Winded` when the STA threshold is
crossed, `First Blood!` on the opening strike, a Bulwark *flare* on a saved
blow (raw tier stated first — narrate the averted death),
`*** CRACK -- X's club shatters on Y's blade ***` when a weapon breaks, and
the `***` lines for falls, slayings, and level-ups.

**2. The raw mechanics**, indented under each headline: the actual `2d6`
result, every modifier with its source (`+DEX`, `+training`, `+rapier`,
`+proficiency`, `-wounds`, `-winded`), both totals (formatted
`Name: total (parts)`), then the full severity arithmetic
(`severity = margin + STR + weapon mods - soak -> tier`).

A `stamina:` readout prints every round — the clock is visible ticking — with
`*` marking the Winded and `!!` the Spent; tireless entities are
summarized (`3 tireless`) since their clock never moves. This is deliberately
the *complete* version; a terser mode can come later once the numbers have
earned trust.

---

## Why three stats produce the loop (no range needed)

- A **Power** build lands rarely (low DEX) but devastatingly, and is durable —
  but wants to win early, before the flat swing cost empties its pool. (The
  "big frames burn fuel faster" idea now lives in the per-swing STA cost knob:
  today it's flat per entity type; Phase 4 makes heavy weapons cost more per
  swing, which is what makes a STR build a burst build mechanically.)
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

**Rolled party heroes** span this band and nudge past it: DEX/STR `randint(3, 6)`,
STA `randint(5, 8)` (its own, higher range: STA is the second death-track —
the swing budget — so its floor matters like HP's floor; a 4-STA hero is a
4-swing hero, and the batch sims showed those parties are the wipes), HP
`randint(8, 12)`, Power `randint(3, 6)`, a random ability (Heal, Bulwark, or
First Blood), and two random potions. A hero's epithet ("the precise" / "the
powerful" / "the steady") is derived from their highest stat, with STA
normalized back to the DEX/STR scale for the comparison.

### Heroes — stats 6–10, HP 12–20
Superhuman because they **break the mortal tradeoff**: a hero can be high in
*two or three* stats at once, which no human can. That impossible combination is
the heroic feeling.

| Type | DEX | STR | STA | HP |
|------|-----|-----|-----|----|
| Duelist | 9 | 5 | 7 | 14 |
| Champion | 7 | 8 | 8 | 18 |
| Legend | 8 | 8 | 8 | 20 |

### Monsters — flavor comes from lopsidedness, not big numbers everywhere
Each monster is a puzzle defined by its hole (or, for bosses, its lack of one).
HP is scaled to threat — a big monster needs a deep pool or it spirals as fast
as anyone.

| Monster | DEX | STR | STA | HP | The puzzle |
|---------|-----|-----|-----|----|-----------|
| Goblin | 2 | 2 | 3 | 4 | Trivial alone; dangerous in numbers. |
| Dire wolf | 8 | 4 | 9 | 12 | Fast and tireless — it dictates the pace; you can't out-chip it. |
| Giant | 1 | 12 | 9 | 35 | One landed blow is grievous+. Survive its swings and let it tire. |
| Dragon | 9 | 10 | 9 | 60 | A boss precisely because it has no exploitable hole. |

**Two scaling notes.** Pool depth tunes the spiral: a human at 8 HP collapses
after one grievous; a giant at 35 fights clean until very deep, then folds fast —
a free narrative arc. And a monster's STR difference makes it terrifying through
the severity formula even before its HP matters.

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
  and avoid your counters. *(Live now: farm the skeleton barrow to afford the
  bandit hideout.)*
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
  first (which may be a killing blow), then let resources buy it off. The log
  always states the death that *would* have happened.
- **Single fights are survivable; the campaign is the challenge.** A well-stocked
  party should win a given encounter; the fail state is attrition — running the
  buffers dry across a run of fights.
- **Two buffer layers, cleanly split.** *Between fights* (items, drunk in the
  lull — too slow to use mid-fight) and *in the moment* (Bulwark, paid in
  Power — fast enough to fire during an exchange). Flavor-true rule: **trained
  skill is reflexive; rummaging in a pouch is not.** Heal sits with the items —
  a Power-cost ability, but a *between-fights* one (see below), since restoring
  a wound isn't something you can do in the half-second of an exchange either.

---

## Resources at a glance

| Resource | Scope | Refillable? | Role |
|----------|-------|-------------|------|
| **HP** | Carries across the run (never a per-fight reset) | Trickle via short rest / a healing potion drunk between fights; the real heal is a **long rest** — HP returns over **~a week** | Lethal death-spiral inside a fight; a lasting wound between them. |
| **STA** | Per day | A **sawtooth trending down**: +1 when a fight ends, +3 per short rest (from empty, fight-end +1 plus a short rest only *just* clears Winded); rare/costly potions; **fully recharges on a long rest (overnight)**. **Never recovers mid-fight** — except bought at a pause (a draught, Berserk, or War-Breath; each costs the round's attack and a −2 guard). | The **second death-track**. Attacks spend it; at 0 you're **Spent** (still swinging, −6 to everything, until the fight ends) and fresh enemies usually finish you. Drives the matchup loop. Stays expensive to buy back mid-day on purpose. |
| **Power** | Per day | Rest, gold, world drops | The **spendable budget** for abilities: Bulwark's mid-fight absorb, and Heal's between-fights HP restore. |
| **Items** | Carried stock | Bought with gold, found in world | The *between-fights* buffer: drunk in the lull for an instant top-up. |

Give each character their **own** Power and item stock, not a shared pool — it
keeps build identity alive and makes "who am I about to lose" specific.

---

## The two-buffer split

**Between fights (items — slow to reach for, instant once drunk):**
- **Healing potion** — drunk in the lull between fights, restores HP instantly
  (`HEALING_POTION_RESTORE`, currently 5). **Cannot** be used mid-fight — no time
  in an exchange this fast; you top up in the breather, then wade back in.
- **Stamina draught** — restores STA. Deliberately **rare and expensive**,
  because STA is the un-buyable clock; cheap refills would collapse the matchup
  loop. STA otherwise recovers only slowly across a day. *The one item with a
  mid-fight mode:* at a **pause** (see "The pause" below) a hero can drink one
  in the teeth of the melee — at the cost of that round's attack and a −2
  guard while drinking. Between-fights drinking stays available; it just isn't
  the only mode anymore.
- **Power potion** — *retired from circulation (2026-07)*: Power was never
  the bottleneck in play, so the slot was dead weight in every kit. The kind
  still exists in the schema (an old save can drink one), but creation rolls,
  drops, and shops only circulate healing and stamina. War-Breath (the
  Power-to-STA conversion, see "The pause") now gives Power a live mid-fight
  drain; if it makes Power genuinely scarce in play, re-stock the kind.

**In the moment (abilities — fast, cost Power):**
- **Warrior's Bulwark (grievous-absorb)** — *active*: when a Grievous or Killing
  blow lands, spend Power to reduce it one tier (Killing -> Grievous, Grievous ->
  Wound). Fires mid-fight, on the blow that just landed — and it can run out,
  which is the point.
- **Rogue's First Blood (opening strike)** — *the aggressive counterpart*: as
  the fight begins, before the first exchange, spend Power to land a
  guaranteed graze on the focused foe. Deliberately light — 1 HP, never a free
  kill — because its real value is the death spiral: that foe fights the whole
  battle at −1 to its rolls. Priced like a Bulwark save (2 Power); where
  Bulwark buys off ~2 HP of incoming harm reactively, First Blood buys roughly
  the same swing proactively (a point of damage plus every roll the spiral now
  costs the foe).
- Other class skills are likewise paid in Power.

**Between fights (ability — still costs Power, but not reflexive):**
- **Heal** — spend Power to mend a random amount of HP on yourself or an ally,
  called deliberately between fights (never mid-exchange; there's no time in an
  attack this fast to rummage for a spell any more than a potion). Distinct
  from Bulwark: it's proactive upkeep on the wound pool rather than a reactive
  save against a specific blow, and it can target a teammate.

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

**Triggers** (party side only; each fires at most **once per fight** — no
pause spam; checked at the end of a round, and only while both sides still
stand):
- a hero at **STA ≤ 2** — about to run dry;
- a hero at **HP ≤ half** — being cut apart.

**At the pause, the options** (pause *actions* are per-hero, at most one each;
every action costs that round's attack and the hero defends at **−2** while
occupied — vulnerable, not helpless):

| Option | Cost | Effect |
|--------|------|--------|
| **Fight on** | — | Resume; that trigger won't pause again. |
| **Drink** | a carried stamina draught; the round's attack; −2 guard | +4 STA now, mid-fight. The one exception to "no in-fight STA recovery" — it even un-Spends a fighter at 0. (Healing potions stay between-fights until HP pressure proves otherwise.) |
| **Berserk** | 2 HP; the round's attack; −2 guard | +4 STA. Bleed for breath — and the HP loss deepens the wound spiral immediately, which is the real price. |
| **War-Breath** | 2 Power; the round's attack; −2 guard | +3 STA. A fighter's breath discipline (battle trance), explicitly not wizardry. |
| **Retreat** | see below | Break away from the fight. |

Berserk and War-Breath are the **resource conversions**: STA is the scarce,
dynamic track, while HP and Power mostly sit idle — these give both a live
mid-fight role (a better fix for Power feeling inert than any potion). Both
are open to any hero for now; tying Berserk to the zweihander (the
weapon-granted-ability hook) is a parked idea.

### Retreat & chase

Deliberately **one roll** — no multi-message chase sequences.

1. **Breaking contact:** every foe fit to swing (alive, not Winded, not
   Spent) gets one **free parting blow** (free like the dying swing — no STA
   cost) at a random fleeing hero, who defends at −2. This has teeth: heroes
   can go Down or die at the door.
2. **The chase:** ONE opposed group contest —
   `2d6 + side-average DEX weighted by current STA` (fresher legs count for
   more), the fleeing side at **+2** (the runner picks the moment and the
   ground). Only foes that *pursue* roll: **the barrow's undead are bound to
   the grave** — they swing at the door but never follow past it, so retreat
   from the barrow always succeeds once past the door. Fiction and mechanics
   agree, and "come back tomorrow and finish it" is a real plan instead of a
   death sentence from tireless pursuers.
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
- **Death happens only when the saves run dry** — a killing blow lands with no
  Power for Bulwark/Heal and no buffer left. Loss is rare, earned, and specific
  to whoever was over-extended.

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
  resource — a handful of slots per day. It gives a real breather (+3 STA, a
  sliver of HP) but never a reset: with the +1 a fight's end already gives,
  a rest from empty lands you *just* past the Winded line. The day's shape is
  a sawtooth trending down — the fights exhaust the characters faster than the
  breaks give back. Drinking potions is a *separate* deliberate act
  (see "In advance" above / `use_potion`), not folded into the rest. When the
  slots run out there is no more mid-day recovery: the party pushes on depleted
  or makes camp.
- A **long rest** (overnight, making camp) is the real recovery: **STA recharges
  fully** and **HP knits back at a weekly rate** (a character's nightly heal is
  scaled to their HP pool, so a full bar returns over roughly a week regardless of
  size — a big pool doesn't take proportionally longer). A long rest advances the
  day and refills the short-rest slots.

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
  slots, `SHORT_RESTS_PER_DAY`). A dungeon run is a slice of a day. **HP and STA
  both carry across rooms** (never a per-fight reset). STA moves as a sawtooth:
  attacks spend it (`sta_cost`, 1 per swing), the end of a fight gives
  `STA_RECOVERY_AFTER_FIGHT` (1) back, a `short_rest` spends a slot for
  `STA_RECOVERY_BETWEEN_ROOMS` (3) + a sliver of HP, and `long_rest` makes camp
  for the full STA recharge + the weekly HP tick (`hp_regen_per_night =
  max(1, round(max_hp / 7))`). **There is no mid-fight STA recovery** except
  what a pause action buys (`_do_pause_action`: a drunk draught, Berserk, or
  War-Breath): an entity at 0 is otherwise Spent (`SPENT_PENALTY` = 6 to all
  rolls; it still attacks) until the fight ends, so fights always resolve;
  only the round-cap safety valve (`max_rounds`) can leave a fight
  unresolved, in which case the scenario treats the room as not cleared.
  Power and items are per-day stocks that deplete across the run.
- **The pause is engine-level.** `group_combat(pause_triggers=True, ...)`
  returns a `Pause` (round + what tripped it) instead of finishing; the caller
  resumes with the same `fired` set, `first_round=round+1`, and optional
  per-hero `actions`. `attempt_retreat` runs the parting blows + the one
  chase contest (`FLEE_BONUS`, STA-weighted DEX; `pursues=False` foes never
  chase); `refresh_foes_after_retreat` readies a fled room's survivors.
  Session play persists a paused fight in the save (`session.py resume` /
  `retreat`) and keeps per-room survivor records; the batch sims answer the
  same pauses with `sim_pause_policy` (drink / convert / retreat, one return
  trip per fled room) so tune/bench numbers describe the same game.
- **No auto-night.** `long_rest` is called deliberately (by the DM), never by the
  dungeon loop — the day ends when the player chooses to camp, not on a timer.
- **Saves are automatic and conservative.** A Bulwark-ability character spends
  Power to buy off a *killing* blow whenever it can (Killing -> Grievous), and
  to buy off a *grievous* that would put it Down only when it can keep a
  reserve. Both the raw and the bought-down result are logged. **First Blood is
  likewise automatic** — it fires at the start of every fight while the Power
  lasts (`FIRST_BLOOD_COST` = 2 for a guaranteed 1-HP graze on the focused
  foe); trained aggression is as reflexive as a trained guard. **Heal is not
  automatic** — it has no in-fight role at all; `use_heal(healer, target, ...)`
  is a DM-called, between-fights action (same shape as `buy_potion`) that
  spends `HEAL_COST` (3) Power for a random `HEAL_RESTORE_RANGE` (1-3) HP on
  self or an ally.
- **Potions are not automatic either.** Drinking a carried potion is a DM call,
  `use_potion(hero, kind, ...)`, between fights only (same shape as `buy_potion`
  / `use_heal`): every potion takes effect **instantly on drink** -- *healing*
  restores HP (`HEALING_POTION_RESTORE`), *stamina* restores STA. Only those
  two kinds circulate (`STOCKED_POTION_KINDS`; the power potion is retired --
  see the two-buffer split above). Nothing in the engine drinks on its own.
  The one-shot / sim paths (`run_dungeon`, `scratch_bandits`) model a sensible
  party via `auto_use_potions_on_rest` (heal when badly hurt, drink stamina
  when winded), so `tune.py` / `bench_training.py` still reflect a party that
  drinks when it should.
- **Outcome semantics changed.** "Died" now means *truly slain* (an unsaved
  killing blow), which is rare. The everyday cost is **Down** counts and the
  drawdown of Power / STA / potions — that's the attrition `tune.py` now reports.

---

# Progression & Economy — Add-on

The first slice of the between-fights layer: XP and levels buying **combat
training** (the only skill so far), and a gold economy that keeps the potion
stock a real decision. Follows the design spine: **XP buys permanent ability,
gold buys staying power** — never the reverse.

## XP and levels

- **Earning.** Every hero who is not truly dead earns the *full* award (no
  splitting; the party levels together): a small amount per **encounter won**
  and a lump for **completing a quest** (clearing a whole site).
- **The curve.** Level L → L+1 costs `100 × L` XP. Anchors:
  - Bandit hideout (the **starter** site — living foes who play by the
    party's rules): **15 XP** per encounter, **55 XP** for the quest — a full
    clear (3 rooms) is exactly 100 XP, so the *first clear is a level-up*; the
    second level takes two clears.
  - The skeleton barrow (the **tough** site — tireless undead in numbers)
    pays **3×** (45 / 165) — brutal fights, real wages.
- **Level-ups grant skill points** (1 per level), spent on skills — free
  allocation, never use-based (the Fallout principle from the design record).

## Combat training — the general fighting skill

The veteran-vs-novice axis: *"you know how to fight."*

- **Effect:** +1 to **all pressure rolls** per rank. Because severity = margin +
  STR difference, training quietly improves *everything*: you land more, get
  hit less, and the hits you land cut deeper. One number, three effects — which
  is why it stays cheap-per-rank but caps hard.
- **Cost:** rank *n* costs *n* skill points; **cap: rank 5**. With 1 point per
  level: rank 1 at level 2, rank 2 at level 4, rank 3 at level 7, rank 4 at
  level 11, rank 5 at level 16. Cheap to start, expensive to max.
- **Benchmarked** (`bench_training.py`, 5k trials/rank, post-pause/retreat
  2026-07): the skeleton barrow (tough site) clears
  **22% → 51% → 79% → 95%** across ranks 0–3 (a rank-0 party wipes ~75% of
  the time); the bandit hideout (starter) clears **89% → 98% → 100% → 100%**
  (rank-0 wipe ~10%). Each rank is a *felt* jump — Phase 3's test criterion.
  (The pause/retreat layer lifted every cell ~5–8 points over the
  graze-floor-era numbers; accepted under "the sims understate the player.")

## Weapon proficiency — the second skill

Per **weapon type** (the rapier, not this rapier): each rank gives **+1 attack
pressure AND +1 severity with that weapon**. Rank *n* costs *n* points; **cap:
rank 3**. Deliberately stronger per rank than combat training because it's
narrower — offense only, one weapon — while training helps attack, defense,
and any weapon you pick up. Switching weapons keeps your training but drops
the proficiency layer until you drill the new type: that loss is the
commitment cost that makes a build a build. A broken weapon grants no
proficiency (you're swinging a stump).

**With two sinks, skill points are a real choice now**: nothing auto-spends in
session play (`session.py train HERO combat|weapon` — points bank until the
player spends them). Only the batch sims (`run_dungeon` / `run_hideout`)
auto-spend on combat training, so tune/bench numbers stay comparable.

## Gold and the potion economy

- **The purse is shared** (party-level); potions are per-hero.
- **Income:**
  - **Quests:** bandit hideout (starter) **15 g**, skeleton barrow (tough) **45 g**.
  - **Drops**, per encounter won: **20%** chance of loose coin (**5 g**, half a
    potion) and **10%** chance of a stray potion (random kind, to a random
    hero). Trash-tier on purpose — drops season the run, quests fund it.
- **Sink:** any potion costs **10 g**. `buy_potion` is a deliberate,
  DM-called, between-adventures purchase — nothing in the engine buys or
  refills automatically. A quest reward is worth 1–2 potions (the hideout, 4+).
- **Weapons are the second sink** (`buy_weapon`, same DM-called shape): plain
  quality weapons cost **60 g** — a real saving goal (roughly four hideout
  clears of quest gold + drops); commons are shop-trivial (1–15 g).
  Masterwork/legendary are **never** for sale. This deliberately softens the
  old "gold never buys power" rule (see plan.md): a plain rapier is modest
  permanent power, and worth it — sim-measured (post-pause/retreat), a katana
  + zweihander loadout lifts a fresh party's barrow clear rate from ~22% to
  ~49%, about the value of one training rank. The intended arc: clear the
  hideout fresh, level up *and shop*, then take the barrow.
- **Starting stock:** two *random* potions at creation (healing or stamina —
  the two circulating kinds), plus the rolled starting weapon. That's the
  whole kit; from then on the stock only moves through drops, purchases,
  and use.
