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
weapons may be shopped for gold; since 2026-07-28 masterwork is shoppable
too (capitals, 5× price) and a legendary smith sells *commissions* at the
superlinear gold curve — the L15+ "what is gold for" answer. The line that
never softens: **the famous named weapons are not for sale at any price** —
gold can commission new steel, it can never buy a story.

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
death sentence you watch. The spiral is also **visible to the player** —
but at the decision surfaces, not on every wound line (the 2026-07-21 log
rework): the pause menu and the post-fight tally print each hero's standing
`-n to rolls`, where the budgeting actually happens; the fight lines
themselves stay number-light (see "Reading the combat log").

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
instead. **The chargen deal is trashier on purpose (2026-07-28):** in a
played game the level-1 PC and his long-time companion start with TRASH
arms — club, knife, sling (`rpg.TRASH_WEAPONS`) — so the first looted
soldier's blade is a felt upgrade; casters keep the staff (deliberately
poor steel, priced in support). Session-only: recruits rolled later and
every sim keep the table above.
Skeletons swing **rusted blades** (0/0, durability 1 — grave-steel that snaps
on honest metal).

### Craftsmanship tiers (reworked 2026-07-28 — the weapon ladder)

`plain` / `masterwork` / `magic` / `legendary` / `mythic` — and **plain is
never spoken**: a weapon is just "a rapier"; special ones are "a masterwork
rapier" or a named blade. The full ladder, its severity-point currency, the
generator, the famous armory, and the legendary smiths live in **The Weapon
Ladder & Generation add-on** below. The short version:

- **Masterwork** (+1 attack pressure on a quality chassis, durability 5) is
  the master smiths' nonmagical best — **shoppable in capitals** since
  2026-07-28 at five times the plain price (the deliberate second softening
  of "gold never buys power"; the first was plain quality steel).
- **The magic tiers** (magic / legendary / mythic) are generated on a
  budget, carry the stat-transcending bonuses, and are **never on a
  shelf** — found, quested, robbed from their famous owners, or
  commissioned new from a legendary smith. No level requirements —
  placement (the reward ladder, the armory, the smiths' prices) is the
  gate.

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
but wood), quality steel 4, masterwork and magic 5, legendary and mythic 6.
**Natural weapons**
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

**One displayed log (the 2026-07-21 rework).** Combat produces a single
displayed log — `CombatLog.player` — that both readers share: the DM
narrates over it, the player reads it as the fight's mechanical account.
The **detailed log** (dice, every modifier with its source, severity
arithmetic, per-round stamina readouts) still exists — the `CombatLog`
list itself — but it is never printed in play. Session combat logs write
two last-fight snapshots beside the other GitHub UI pages:
**`ui/fight-short.txt`** is the exact displayed log and
**`ui/fight-detailed.txt`** is the detailed record. A new encounter replaces
both files; resume or retreat appends to the paused encounter, so a fight
that spans two commands remains one complete record. `group_combat` flushes
the detailed mechanics block when it pauses or resolves, and
`session.print_combat` flushes both levels' session tail (awards, loot,
tally) afterward without duplicating lines. `sheet` commits both snapshots
with party.txt and map.txt. The bench harnesses pass plain lists and receive
the detailed wording without doing file I/O.

The displayed log is built for a 40-column phone screen (`PLAYER_WIDTH`
in rpg.py): **every line starts in column 1**, and every event is
pre-fitted into lines that break only on semantic seams (`fit_lines` —
fragments like `Gardain (10/12)` / `overwhelms Scrap-Hound 1,` /
`deals 6 dmg!!!` are never split mid-thought). Combat lines use **short
names** ("Inga", nothing appended — a character's race, age, and traits
are sheet flavor, shown at creation and in `status`, never in the
exchanges).

**The exchange line.** The pressure margin is narrated as the verb, the
severity is a bare number, and the wound tier is punctuation:

| Situation | Line |
|-----------|------|
| Hit by margin 1–2 / 3–4 / 5+ | *edges past* / *outmaneuvers* / *overwhelms* |
| Wound tiers (graze/wound/grievous/crippling) | `deals 1 dmg.` / `deals 2 dmg!` / `deals 4 dmg!!` / `deals 6 dmg!!!` |
| Attacker loses the exchange | `X attacks Y, parried.` |
| Hit lands but soak zeroes it | `X attacks Y, deflected.` |
| Pressure tie | `X and Y: Clash!` (high dice) / `X and Y: they circle.` |
| A kill / a fall | `SLAIN.` / `It falls.` glued onto the wound line when it fits, else its own line |
| A hero drops | `X goes DOWN.` |

**The rolling HP readout.** Wound lines no longer print the target's
resulting HP; instead every attack line carries the ATTACKER's own HP
right after their name — `Wolf 2 (1/4) attacks Fizzle, parried.` — and
**no tag means unhurt**. Since everyone acts every round, the reader sees
each fighter's state refreshed once a round, on the line where they act.
A dying attacker announces itself instead: `X strikes as they fall:`.

**No penalty numbers in the fight lines (the 2026-07-21 doctrine turn —
supersedes 2026-07-09's "print `-n to rolls` on every wound line").**
State crossings say only the state — `!! X is Winded.` / `!! X is
SPENT.` — and wound lines carry no roll penalty. The numbers moved to
the two decision surfaces instead: the **pause menu** and the
**post-fight tally** both print each hero's standing penalties
(`(hurt -2, Winded -2 to rolls)`). A number the player budgets around
is a number the player sees — at the moments they actually budget.
(Since 2026-07-26 that first term is labelled **hurt**, not "wounds":
it is the HP-derived spiral — the fast channel — and the named located
WOUNDS now print as their own list beneath it. Two channels, two
displays, never one number wearing both names.)

**Quiet rounds collapse.** A round in which nothing lands (all parries,
deflections, circling) is not printed; consecutive quiet rounds compress
into one line — `Round 4-5: nothing lands.` — with any Winded/Spent
crossings from those rounds surfacing right after it. Movement lines
(`The lines close.` / `The lines meet -- steel range.`) print only in
fights where someone threatens at range (a card or a caster); in an
all-steel fight the approach is silent.

**Named things stay named.** Abilities and warrior moves log by name and
name only — `Morgran uses First Blood!`, `Rhea: Feint -- the cutthroat's
guard opens.`, `Orsik: Iaido -- one flowing cut!`, a Bulwark save as
`but Bulwark blunts it: deals 2 dmg!` — with no cost/bonus arithmetic on
the line. **Power is printed only after casting spells** (`[5 Power
left]` on cast lines, fireballs, openers, vanish); ability fuel and STA
refunds stay off the displayed log. Falls, weapon breaks (`*** CRACK
... ***`), regeneration, XP, and loot appear as their own fitted lines.

**The enemy introduction.** Each encounter opens with the fitted banner
(quest, site, room) and the roster as per-kind stat blocks — the one
place the player reads the numbers they are about to fight:

```
3x Blight-Wolf -- fangs
DEX 4  STR 2  STA 8  HP 4/4
Gloomweaver 5 -- fangs
DEX 6  STR 2  STA 7  HP 6/6
caster: shadow 2; 8 Power
```

Special rules (drilled, undead, tireless, casters, sweeps, regeneration,
ranged reach) ride a tag line under the stats.

**The dying counterattack resolves immediately (2026-07-21).** A fighter
felled before their turn takes the round-start dying swing right after
the blow that felled them — promoted to the front of the turn order, not
at their original slot — so `deals 6 dmg!!! SLAIN.` and `X strikes as
they fall:` read together. Same swing, same round-start wound penalty;
no balance intent (verified within noise on the tune sweep).

Since 2026-07-14 every survived encounter's block closes with the **party
tally** (`session.tally_lines`): each standing member's HP/STA/Power,
their standing roll penalties (see above), kit, the purse, the day, and
-- with an active quest -- the count of fights left and what the turn-in
will pay. It is the standard
between-encounters numbers display: the DM narrates around it instead of
restating it, and it deliberately shows a *count* of what lies ahead,
never the rosters (dm.md, Narration style).

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
*(Implemented 2026-07-28: weapon stat bonuses are that membrane — the
Weapon Ladder add-on prices +DEX at 3 sp and gates it to the legendary
tiers, with the weapon's share of transcendence capped at +3.)*

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
  the **weekly knit-back on long rests** (see
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
| **HP** | Carries across the run (never a per-fight reset) | A healing potion drunk between fights; the real heal is a **long rest** — HP returns over **~a week**, but only ever up to the **wound ceiling** (2026-07-26, slice 3b) | Lethal death-spiral inside a fight; a lasting wound between them. The FAST channel of the injury system. |
| **Wounds** | Carry indefinitely — a night does nothing for them | Only the **treatment ladder**: a settlement bed (1 severity a night), the healer (tier-capped), a salve, or high magic for a maiming | The SLOW channel (2026-07-26, slice 3b): named located records that dock the HP ceiling and carry stat penalties. See the Wounds & Recovery add-on. |
| **STA** | Per day | A **sawtooth trending down**: +1 when a fight ends (the day's only free give-back since the short rest went, 2026-07-26); rare/costly potions; **fully recharges on a long rest (overnight)**. Mid-fight it comes back only through a pause action (a draught, Berserk, or War-Breath; each costs the round's attack and a −2 guard). | The **second death-track**. Attacks spend it; at 0 you're **Spent** (still swinging, −6 to everything, until the fight ends) and fresh enemies usually finish you. Drives the matchup loop. Stays expensive to buy back mid-day on purpose. |
| **Power** | Per day | **Full on a long rest** (it recharges with rest like STA, just never mid-fight); world drops | The **spendable budget** for the learned abilities (Bulwark's mid-fight absorb, First Blood's opener, War-Breath) and for every spell — the healing spell's between-fights mending included. |
| **Items** | Carried stock | The **kit restocks itself, thinly** — every long rest the PARTY scrounges up to 1 healing + 1 stamina (per party since session C, + a forage roll for a 2nd draught); anything above that is bought, found, or **brewed** (the alchemist) | The buffer: drunk in the lull for an instant top-up, or mid-fight at a pause / by standing order (the round's attack, −2 guard). Drunk AT max, a potion **overcharges** (+2 above max, spent-only — session C). Out of combat the lull top-up runs itself since 2026-07-26 — the **quartermaster pass** deals the stock to whoever needs it, and at a fight's OPENING (2026-08-05) drinks for everyone who has no better answer (see "Gold and the potion economy"). |

Give each character their **own** Power and item stock, not a shared pool — it
keeps build identity alive and makes "who am I about to lose" specific. (The
quartermaster pass moves *basic potions* between packs out of combat; the
stocks stay per-character, and nothing else is ever pooled.)

---

## The two-buffer split

*(2026-07-26, slice 3b: every HP mend below — potion, spell, rest — now fills
toward the **wound ceiling** and stops there, and the ladder gained two new
item rungs, the **surgeon's salve** and the authored **elixir of mending**.
See the Wounds & Recovery add-on.)*

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
**first wounds crossing** (any member's), or at Fate's intervention if that
gets there first. The wounds question is "someone is being cut apart, do we
retreat?"; Fate's special version asks only fight on / retreat. Whichever
fires spends the same pause budget. Every other crossing — every stamina
crossing, and wounds crossings after the pause is spent — is answered by the
party's **standing orders** (below) without stopping the fight. The engine
still detects every crossing per hero exactly as before (`standing_orders`
is a session-side dispatch on top; the batch sims run the old every-crossing
pause with their policy, so the benches answer the same questions they
always did).

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

The **+2 and the plain STA weighting belong to the party's deliberate
retreat**, which picks its moment. The reverse case — a beaten foe line
collapsing — is a ROUT and is rolled differently; see below.

### The rout — when the foes break (2026-08-08 rebalance)

The same machinery reflected across the field, with three deliberate
differences. A rout is a **collapse under pursuit**, not a plan:

- **No flee bonus.** The runners picked nothing: no +2.
- **The runners' DEX is weighted by HP as well as STA** — they are below a
  third by construction, and broken bodies run slowly. The weight floors at
  0.3 of the body's DEX, so a graze-rich pack is not automatically caught.
- **Its own trigger, stricter than the standing orders':** every living foe
  **below a third of HP, or Spent** (`rout_ready`). The half-HP
  `fight_winding_down` band stays where it is — it also gates potion thrift
  and must not move.

*Why:* measured before the change, the solo troll escaped **54%** of won
fights and 50% even when the party ended fresh — a big HP pool sits in the
trigger band for rounds while DEX 6-7 plus the bonus beats the party
average. The mechanic fired hardest in the fights the party was flatly
winning, and forced fiction that contradicted the job. After: the troll is
at 18% overall and **14% when the party ends fresh**, against 67% when it
ends spent. That separation *is* the design — the escape is a relief when
the party has nothing left to chase with, not a tax when it is fresh.
`bench_rout.py` measures it, `--legacy` prints the before column.

A field cleared by a rout says so: the site banner reads **(driven off,
not slain)**, so no display ever claims the giants are dead against a log
that says otherwise.

### Loose ends — the escapees the game remembers

A rout writes a record the save keeps (`loose_ends`, newest first): who got
away, at what HP and wounds, from which fight, in which area, on what day.
It persists with no expiry — entries are story, not bookkeeping, and the DM
prunes them by save edit. `status` names the latest; `look --dm` lists the
local ones.

**`pursue` — the warm trail.** One command, one roll, no tracking
subsystem, available only while the trail is **WARM**: same day as the
rout, party still in the area, no night slept. One attempt per rout.

- **The contest:** `2d6 + the party's best MIND` vs `2d6 + the runners'
  chase DEX` (HP- and STA-weighted, as in the rout they escaped by),
  trackers **+2** if any runner carries a wound — blood on the ground.
- **Success:** the fight re-opens against the survivors **at their fled
  state** — their end-of-fight HP, wounds and STA; they have been running,
  and nothing refreshes — met at the party's preferred range, because the
  party are the hunters now. Standard encounter machinery from there:
  pause, retreat, and another rout are all possible (a second rout re-arms
  the record on fresh ground).
- **Failure:** the trail is lost. No day is spent, and the loose end stays
  on the books — the record is the story hook.
- **Pay:** the room already banked its encounter share when the field
  cleared, so the mop-up pays **wild rates** for what it kills. Loot rolls
  as in any fight.
- **Cold trails are not a mechanic.** After a night the wounds have healed
  (living foes heal over a day; the troll fully) and pursuit becomes
  *finding* — rumor, `travel`, `forge`, the DM's territory, fed by the
  record. `pursue --stage` is the DM's valve for the scene that finding
  produces: no gate, no roll, survivors healed by the days passed.

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
- **A killing blow can still kill**, and a relentless roster can still finish
  a defeated party. Slice 4's level-limited mercy below is the campaign
  safety valve: defeat normally leaves damage, loss and a maiming instead of
  demanding a new character.

---

## Fate's bargain — the player character's death trade (2026-07-10)

Session play marks the PC (`party[0]`) as the **protagonist**, and one rule
guards them: **a blow that would kill the PC is commuted to a Down while at
least one companion still draws breath.** The log announces the reprieve and
its terms (*"Fate has spared them; its price comes due if this fight is
won"*).

If the encounter's one pause is still unspent, the bargain creates its
**special fight-on/retreat interrupt** at the end of that round. It offers no
potion or conversion actions. It **consumes the ordinary pause**; every later
crossing runs on standing orders. If the wounds pause already happened, Fate
does not create a second stop. Then:

**The debt is UNCONDITIONAL (2026-07-29).** Fate is owed, not bargained down.
Once the spare has fired, the encounter ends by killing **one random
companion** (Down or standing; fate is not particular) and standing the PC at
**exactly 1 HP** — whether the party won, lost, or walked away clean. Every
wound and all other damage remain. The trade is literal: a companion dies and
the player character lives. In a duo, the result is a badly wounded solo PC,
**not** a fake reprieve followed by a wipe. The outcome decides only what the
party got for the corpse:

- **A WIN** banks the fight: the last foe's dying strength lands the final
  blow, and the room, the pay, and the XP are the party's.
- **A LOSS** pays exactly the same price and buys nothing. The foes are still
  standing, so the encounter resolves UNCLEARED — no pay, no XP, and the room
  keeps its survivors.
- **A CLEAN RETREAT** pays it too, at the door — the ordinary break, a
  smoke-vial break, and a rank-2 **blink-out** alike. The Power and the vial
  buy the party out of the *room*, never out of the bargain. The room is given
  up and remembered, as after any flight.
- **The one deferral is a FAILED break.** Run down at the door, the fight
  resumes and the debt is still owed; it settles at the fight's real end.
- **None of these may also spend defeat mercy.** The spare was the reprieve
  and a companion has already paid for it, so the roster's ferocity
  consequence and the PC's once-per-level allowance below are both skipped.
  Mechanically this falls out of the 1 HP restoration: `party_defeated` is
  false by the time mercy is checked.

So the interrupt is no longer a question about the debt — it is only *is this
room still worth trying?* Press on for the pay, or break off and keep the
damage you have. The companion is buried either way.

The spare only intercepts actual deaths (an unsaved crippling blow at 0 HP);
ordinary Downs are unchanged. A solo PC has nothing to trade and dies like
anyone. If every companion is already dead when the fight ends, the debt has
no victim left to take: the price is treated as settled and the PC still
rises at 1 HP. The sims never set the protagonist flag, so their tuning numbers are
untouched — this is a session-play rule for why a *fragile PC build is viable
at all*: the party is the PC's real HP bar, spent one member at a time.

---

## Defeat without death — ferocity and mercy (2026-07-26, slice 4)

The wound system made losses heavier on purpose. Defeat therefore stops
meaning "roll a new character" by default, without making every enemy
merciful. Each foe carries **`ferocity` (0–2)** as a content fact, never a
combat modifier:

| ferocity | conduct |
|---|---|
| **0 — takes spoils** | Bandits, raiders and ordinary humanoids rob the defeated and leave. |
| **1 — breaks** | Most beasts fight while they are winning and break when badly beaten. |
| **2 — relentless** | Undead, demons and the conquest waves neither break nor grant ordinary roster mercy. |

The roster reads at its **highest** ferocity. One relentless member makes the
whole defeat lethal.

**The allowance is one mercy per PC character level, non-cumulative.** The
first eligible defeat at level N marks `Entity.mercy_level = N`; another loss
at that level is real. Reaching N+1 restores one allowance, never a bank of
unused ones.

On an eligible defeat (nobody left standing, or the PC truly slain):

- everyone who entered that fight wakes at **1 HP**; older dead companions
  stay dead;
- wounds and every other lasting injury remain;
- a **ferocity-0 humanoid roster** takes the entire purse and every quality
  weapon, leaving ordinary steel alone (a quality wielder wakes unarmed);
- a **ferocity-1 monster roster** takes nothing, but one random participant
  wakes with a **permanent maiming**;
- a **ferocity-2 roster**, or a second defeat at the same level, remains a
  wipe / PC death and GAME OVER.

Law and hell posses are the authored exception to the roster consequence —
LAW also clears sin; HELL withdraws the refused task — but they spend
this same once-per-level allowance. Their former unlimited mercy is gone.

Ferocity also speaks before defeat. Once every living foe is **below a third
of HP or Spent** (2026-08-08: its own band, stricter than the standing
orders' half), a ferocity-0/1 roster may make **one break attempt**: the
party gets softened parting blows, then the retreat's chase runs in reverse
— as a ROUT, with no flee bonus and the runners' DEX weighted by HP as well
as STA (see "The rout" under Retreat & chase). Escape means the foes yield
the field alive and leave a **loose end** the save remembers; ferocity 2
never tries.

Fate and mercy do not stack into two reprieves. A lost Fate-bargain fight is
a genuine defeat and can spend mercy. A **paid** Fate victory stands the PC
at 1 HP, so the defeat predicate is false and mercy cannot fire.

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

**One tier of rest: the night** (2026-07-26 — the **short rest is deleted**).
A mid-day breather that handed back +3 STA, a sliver of HP and +1 Power
existed to pace a four-room site; with quests down to one or two encounters
there is no mid-day left to pace, and every free top-up between fights is a
top-up the wound track would have to fight. Recovery is the night's job now,
and only the night's. The day's shape is still a sawtooth trending down —
fights spend STA, and only the +1 at a fight's end gives any of it back
before dark.

- A **long rest** (overnight, making camp) is the recovery: **STA and
  Power recharge
  fully** and **HP knits back at a weekly rate** (a character's nightly heal is
  scaled to their HP pool, so a full bar returns over roughly a week regardless of
  size — a big pool doesn't take proportionally longer). A long rest advances the
  day. Drinking potions is a *separate* deliberate act
  (see "In advance" above / `use_potion`), never folded into a rest.
  **But the night is no longer whole (2026-07-26, slice 3b): HP knits toward
  the WOUND CEILING, never past it.** What a fight left recorded on you is
  still on you in the morning unless something on the treatment ladder
  answered it — and in the wilds nothing does. A **settlement bed** (tavern,
  downtime, a healer's day) additionally knits one severity a night; the
  wilds knit none. That is the geography gate the whole rework turns on.
- **Where the night is spent matters (2026-07-10):**
  - **Camping in the wilds** (anywhere that isn't a settlement) risks a
    **night visitor** (~10%, off the road's party-independent table with the
    same spotted/ambush valves). Since 2026-07-26 the visitor is rolled
    **before the night's recovery**: the camp is pitched, the fire draws
    whatever it draws, and only a night that passes undisturbed heals
    anybody — a fight is met at the HP the day left you with, not at full.
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

**Nothing forces the day to end.** Ending the day is a *choice* — the DM (the agent)
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

- **Time is a `Clock`** (a `day` counter, and since 2026-07-26 nothing
  else). A dungeon run is a slice of a day. **HP
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
- **Potions run themselves out of combat (2026-07-26 — the quartermaster
  pass).** `use_potion(hero, kind, ...)` is still the deliberate call, and every
  potion still takes effect **instantly on drink** — *healing* restores HP
  (`HEALING_POTION_RESTORE`), *stamina* restores STA; only those two kinds
  circulate (`STOCKED_POTION_KINDS`; the power potion is retired — see the
  two-buffer split above). What is no longer a decision is *who carries which
  vial* and *whether to drink one when you walk into a fight already
  bleeding*: see
  **"The quartermaster pass"** below. The one-shot / sim paths
  (`sites.run_site`) keep their own, older policy —
  `auto_use_potions_on_rest` (heal when badly hurt, drink stamina when
  winded, on each hero's own stock, no hand-over) — so `tune.py` /
  `bench_training.py` numbers describe the same party they always did.
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
  plus a lump at the **turn-in** of the whole quest.
- **The curve.** Level L → L+1 costs `100 × L` XP, capped at **level 20**
  (the 1–20 doctrine below).
- **Pay scales with LEVEL, and it is quoted per JOB** (rebased 2026-07-26,
  the attrition rework). There are **two deliberate ladders** in `rpg.py` —
  do not unify them:
  - **The quest ladder — the game.** A generated quest is 1-3 encounters
    (below); its whole pay is
    `quest_xp_total(L, enc) = 44 × (L + 1) × ENCOUNTER_MULT[enc]` XP and
    `quest_gold(L, enc) = 18 × L × ENCOUNTER_MULT[enc]` gold, with
    `ENCOUNTER_MULT = {1: 1.0, 2: 1.6, 3: 2.2}`. The multiplier rises
    **sub-linearly** on purpose: the fixed overhead of a job — the trip out,
    the giver, the turn-in — is paid once whether you fight once or three
    times, so three fights are worth more than one but nothing like three
    times more. The XP splits **three ways** (2026-08-08, the turn-in
    stage): **40%** falls as the encounters do (flat: every fight on the job
    pays the same, wherever it stands), **40%** is the FIELD tranche paid
    unbanded when the last place closes, and **20%** plus **all** of the
    gold is the TURN-IN, paid where the giver stands and banded by the day
    it lands. An intermediate place of a two-place job clears with a banner
    and no purse.
  - **The site ladder — the fixtures.** `site_xp_total(L) = 50 × (L + 1)`,
    45% split flat across the rooms, the rest as the clear lump, plus
    `15 × L` gold. This ladder now serves ONLY the two hand-built sites in
    `sites.py` (the bandit hideout at level 1, the skeleton barrow at level
    3), which are dev/test calibration fixtures that `tune.py`,
    `bench_training.py`, and `run_site` are fitted to — not played content.
    A fixture whose pay moves stops being a control.

  The shape is the same on both: pay grows by *half* the level-1 anchor per
  level while the level cost grows by the full step, so **leveling slows
  with rank** (~38 at-level quests from 1 to 20, measured). And because pay
  follows the JOB'S level, not the party's, punching up pays above your
  weight class and easy work pays less — no separate under/over-level bonus
  exists or is needed.
- **Off-script and road pay.** A won road encounter, hunt, or `fight N` pays
  one encounter's share of a level-L *three-fight* quest — below board work
  on purpose, since a road fight carries no turn-in lump. The wilds are the
  farm; the board is the game.
- **The momentum streak is GONE** (deleted 2026-07-26). It paid a rising
  multiplier for consecutive encounters cleared in one site without a camp,
  to make pressing on beat camping. With quests down to one or two fights
  there is nothing left to press through, and the job it was doing — making
  a night's rest cost something — belongs to the wound track instead
  (camping restores stamina, never lost HP). Every encounter of a quest now
  pays the same flat share.
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

- **The purse is shared** (party-level); potions are per-hero — but since
  2026-07-26 the party *manages* them as a shared stock (the quartermaster
  pass, below).
- **Income:**
  - **Quests:** a level-L quest pays **18 × L × ENCOUNTER_MULT** gold, all
    of it at the turn-in (2026-07-26) — ~25 × L at the measured encounter
    mix, which is what the old per-site ladder paid over its ~1.6 sites.
    Career gold is deliberately unchanged by the rework: gold is the one
    quantity that inflates across a 1–20 career, which is exactly why
    recovery is never priced in it. The two hand-built site fixtures keep
    the old **15 × L** on the clear (the hideout's 15 g and the barrow's
    45 g are the L1 and L3 rates).
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

### The quartermaster pass (2026-07-26; the drink moved to a fight's opening 2026-08-05)

**Carrying and drinking basic potions stopped being decisions.** Who holds
which vial was never a choice with a wrong answer worth making, and a hero
bleeding at 2 HP with a potion in the pack is bookkeeping, not tension. Out
of combat the engine now runs both (`rpg.auto_potions`), and the potion
decisions that *are* real — how deep a stock to buy before a push, when to
spend the alchemist's day, whether to drink at the mid-fight pause — are
untouched.

- **When it runs:** whenever the party's potion stock **changes**, out of
  combat — a purchase, a brewed batch, loot, the overnight kit scrounge, a
  drink, a hire, a quitter walking off with their pack, at every fight's end
  (including a retreat), and at every fight's **opening**. Never mid-fight:
  the pause and the standing orders own that decision, and nobody rummages
  through a comrade's satchel during an exchange.
- **The fallen are emptied first.** A dead companion's healing potions and
  draughts are **taken up from where they fell** and go back into the
  party's stock — the same doctrine as the quality steel a fallen hero
  leaves behind. Burying a full satchel is a loss nobody in the fiction
  would accept; everything else stays with the body.
- **The deal.** Healing potions and stamina draughts (`AUTO_POTION_KINDS`;
  the retired power potion and the alchemist's stat brews, bombs, and smoke
  are left where they lie) are pooled and dealt back out **worst-off
  first, then round-robin** — the neediest for that kind gets the first
  one, the next-neediest the second, and a deep stock keeps spreading so
  the whole party carries some of it. Need is the **raw current pool** (HP
  for healing, STA for draughts), not a fraction of maximum: the restores
  are flat, so the character closest to falling is the one with the fewest
  points left. **Ties go to the companions** — the player can always call
  for a potion, while the engine speaks for everyone else.
- **The drink — at a fight's OPENING, and nowhere else** (2026-08-05;
  it used to be the fight's *end*). Anyone the pass speaks for drinks when
  **badly hurt** (at or below half HP) or **Winded** (STA ≤ `WINDED_STA`) —
  the same lines the sim policy has always used — but only in `open_fight`,
  the step between "there they are" and the first blow. Every other pass
  **deals only**, the fight's end included: once the last foe is down the
  party can camp, and the night knits HP back for free, so a vial poured
  down a hero on the way OUT of a fight is one the morning would have
  saved. Carried INTO the next fight, the same wound is what gets them
  killed — that is where the vial is worth its price. Never at full either
  way: the overcharge (+2 above max) stays a deliberate spend. Prep stands
  the Down back up first, then deal and drink alternate until nothing more
  is wanted, so a hero who went down last room can be stood up and topped
  off in one opening.
- **Who it speaks for.** **Companions always** — nobody is playing them.
  **The player character only when they have no better answer of their
  own:** a PC who knows the **healing spell** owns the wound decision, and
  a PC who knows **War-Breath or Berserk** owns the stamina decision (the
  draught is exactly what those conversions exist to save). Such a PC is
  still *dealt* potions — they simply drink them on the player's `use`
  call, not the engine's.
- **The cost of it.** A small difficulty *give* — the party no longer walks
  into the next door at half HP with an unopened potion — kept small by the
  opening fence: the nightly kit line is banked, not burned, because
  nothing drinks at camp, at a shop, or on the way out of a fight. Moving
  the drink from the fight's end to its opening (2026-08-05) barely moves
  the numbers where two fights run back to back — the same vial is spent,
  minutes later — and *saves* it outright wherever the player camps,
  travels, or visits the healer in between. **A wound is now visible in
  `status` between fights**: heroes carry their HP as it is and crack the
  vial when steel comes out, which is also the honest reading of the
  fiction. Recovering the fallen's kit cuts the other way from where it
  looks: it softens a death, but a death still costs the companion. The
  levers, if it proves too generous, are the drink threshold
  (`wants_potion`) and which call sites pass `drink=True` (exactly one:
  `rpg.open_fight`).

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

Poisons and oils are unblocked as of 2026-07-26 — the conditions framework
shipped (the Conditions add-on) and alchemy is its first queued customer: a
poison oil is a recipe plus one `apply_condition` call. The firebomb likewise
does not set anything alight yet; hooking it to `burn` is a content-pass
decision with its own bench round, not a framework one.

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
  rank 1; wizards often carry the wooden staff (50%). **The PC always has
  it (2026-08-05)**: `new` rerolls the stat budget until the gift lands,
  because the gift is the one thing nothing later can grant, while every
  warrior sink stays open to a wizard — see *The player character* in the
  Party add-on.
- **The casting check's stat** (unaimed spells, below).
- **Half the AIM of a thrown cast** (aimed spells, below).
- **The notice contest's party stat** — a watchful mind sees road trouble
  before it closes.

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
| **scry** | utility | the next room's roster (2 P) / the whole site (3 P) / **the far-seeing**: the whole quest and DM-adjudicated divination (4 P) — `cast HERO scry` |
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
  first mechanics; the PC carries no traits, so what the party is noticed
  for is its companions) + a clumsy-stealth point per point its *worst* DEX
  sits under 4 (stealth is a weakest-link property). The party notices
  with its **best MIND** (the watchful mind); beasts and foes sense with
  the sharper of MIND and DEX.
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

# Conditions — Add-on (2026-07-26, the attrition rework's slice 3a)

Lingering effects that keep costing you after the blow that caused them:
**bleed**, **poison**, **burn**. One schema, one tick point, one stacking
rule. It is built as a general framework rather than a bleed special case
because it has been the named blocker behind varied enemies, venom, varied
magic and fire for three design sessions — so it gets built once, properly,
and the wound system (slice 3b) lands on top of it.

`rpg.Condition` / `rpg.Entity.conditions`; the constants live in the
conditions block at the top of `rpg.py`.

## The schema

| field | meaning |
|-------|---------|
| `kind` | `bleed` / `poison` / `burn` |
| `power` | HP lost per tick |
| `rounds` | how many ticks are left — **`None` = untimed** |
| `source` | who or what put it there (display only, never mechanics) |

**`rounds=None` is the load-bearing distinction.** An untimed condition does
not run out on a clock: it survives the end of the fight, walks out of the
room on its victim, and waits for something to *treat* it. A rounds count is
the ordinary case — fire burns out on its own.

## The tick

At the **end of every round**, in this order: regenerators knit → conditions
tick → Winded/Spent crossings are read. The order is deliberate both ways —
a troll's knitting outruns a burn, and a tick can trip the pause the same
round it lands.

**A tick can never kill.** A body taken to 0 HP by a tick goes **Down**, with
no crippling save involved. Steel kills; the blood loss after it only ever
costs you the fight. A silent scalar killer would undo "lethality is real,
then padded", and bleeding out has to stay treatable.

**Stacking is bounded.** A second condition of the same kind on the same body
*refreshes* — it takes `max(power)` and the longer duration, and an untimed
dose wins outright over a timed one. It never adds a second copy and never
sums the powers. Unbounded stacking is how condition systems become the only
strategy worth playing.

**The log gets one line per round, not one per condition per body.** Every
ticking entity folds into a single collapsed line ("`Poisoned: Gard -1.`"),
emitted quiet so the quiet-round collapse still works; the arithmetic goes to
the detailed log. Going Down from a tick is a real event and gets its own
line, worded by side exactly like the melee's own falls.

## Clearing and treatment

| what | clears | when |
|------|--------|------|
| end of fight | every **timed** condition | automatic (`_clear_fight_states`) |
| **field stabilize** | bleeding, on anyone still standing | free, automatic at fight end, both sides |
| healing potion / healing spell | bleeding | on the drink / the cast |
| **the night** | everything still on you | `long_rest`, at a price |

The field stabilize is the designer's line made mechanical: *after combat,
stabilized, the wounds and the penalties remain and the blood pool stays
lower, but the character is not actively dying.* It costs nothing and is
never a decision — the alternative was a party that quietly bleeds to death
walking to the next room.

What it deliberately does **not** touch is venom. A poisoned hero walks out
of the room still poisoned and ticks again in the next one; only sleeping it
off ends it, and the night charges `POISON_NIGHT_HP` per condition off its
own recovery (floored so a night is never a death sentence). That is the
attrition point of the whole rework in miniature: with one fight per quest,
pressing on has to cost blood, and a day already costs a job (the quest
clock). The fuller treatment ladder — healer services, salves, the potion
tiers — arrives with the wound system.

Conditions do **not** persist for foes across a return trip: a room left
alone binds its own wounds. Foes keep the scalar and nothing else, the same
asymmetry the wound system will run on.

## Who inflicts what

The rider hangs on the **body**, not the delivery (`Entity.inflicts`): it is
what this creature's attacks leave behind, whether that arrives as fangs, a
bolt, or a shot. Two shipped customers:

- **The great spider** — venomous. Untimed poison, so the row's whole shape
  is now "it barely hurts you in the room and then follows you out of it".
  This is what its STR 2 bite needed; the venom no longer has to hide inside
  the raw damage.
- **The pyromancer** — its fire clings. Timed burn, a couple of rounds.

Both announce themselves in the roster's stat block, which is the enemy
introduction: a venomous row that only revealed itself in the log would have
cheated the player out of the decision.

A **school-wide** rider — every fire bolt on the board burns, the ice
school's rime as its precedent — is the obvious generalization and is
deliberately not here. Measured 2026-07-26: hooking burn to the fire *cast*
moved every single bestiary row, because the reference duo rolls fire
wizards, so the hero side gains it too. That is a career-curve change, not a
framework one; it is a one-line addition whenever the magic content pass is
ready to bench it.

## Balance

`bench_bestiary` re-run at 2000 trials a column: exactly two rows moved, to
the cell. Great Spider at level 89.5% → 81.9% win (wipe 0.8% → 5.2%);
Pyromancer at level 92.4% → 87.7% (wipe 3.1% → 7.5%). Both moved *toward*
the 55-75% calibration band and both remain on its easy side, along with
most of the catalog — the standing "re-annotate the bestiary for the pain-2
party" item, not this slice's business. Every other row, `tune.py` and
`bench_training.py` are unchanged.

---

# Wounds & Recovery — Add-on (2026-07-26, the attrition rework's slice 3b)

**One injury system, two time constants.** HP is the **fast** channel: blood
and shock, refilling with rest. **Wounds** are the **slow** one: named located
records that lower the HP ceiling and carry specific stat penalties, and that
a night in the wilds does nothing for.

Both channels are live in **every** fight, including the one where the wound
is taken. There is no in-fight/between-fights seam and no `fresh` flag —
`Entity.wound_penalty` already carried across fights (it is derived from HP,
and HP carries), so a delay would have been a fiction.

`rpg.Wound` / `rpg.Entity.wounds`; the constants live in the wounds block at
the top of `rpg.py`.

## Why: rest had stopped being incomplete

With quests down to one encounter (slice 1) there was nothing left inside a
job to attrit: the party won, camped to full, and HP never mattered. Every
obvious fix is a gold price — and gold is the one quantity that inflates
(income runs ~4 g/day at level 1 and ~75 g/day at level 20 while HP pools
barely double). So:

> **Do not make rest expensive. Make rest incomplete.**
> Gate recovery on **rate** and **access**, never on price. Time and geography
> do not inflate; a cap on what a night can restore is worth exactly as much
> at level 20 as at level 1.

## The budget shift (why a blow is not charged twice)

Part of the roll-penalty budget **moved out of the anonymous HP channel and
into the named wound channel**. `HERO_PAIN` went **2 → 3**: a hero down 6 HP
now takes −2 on all rolls instead of −3, and the located wound's own −1 pays
the difference. Total in-fight pressure at a given injury level therefore
stays near the bench baseline. What changed is that part of it is now
**specific, located, and does not heal overnight**. That is the entire point.

**The asymmetry is deliberate and stated on purpose.** Heroes record wounds;
foes keep the scalar and stay at pain 2. Foes do not persist between fights,
so records would buy nothing and would cost the bestiary's 25 bench-fitted
`level`/`ref_pack` annotations. The consequence is that a hero's penalty
budget moves from fast-healing HP into slow-healing wounds while a foe's stays
entirely fast — over a career, a net nerf to the party, and that net nerf **is
the attrition this rework is adding**. If it proves too much, the dial is the
treatment ladder's **rate**, not the penalty magnitudes.

Foe wound *narration* is free and stays the DM's.

## The schema

| field | meaning |
|-------|---------|
| `location` | `flesh` / `arm` / `hand` / `leg` / `chest` / `gut` / `head` / `eye`, or `""` (unlocated) |
| `name` | the authored display string (`WOUND_NAMES`, writing.md's register) |
| `severity` | 1–3 |
| `penalty` | stat key → int (folded into the raw stats) |
| `bleed` | HP/round it re-opens with; 0 = none |
| `permanent` | a **maiming** — only the epic tier reaches it |
| `treated` | a healer has packed it: it no longer bleeds, no longer drains morale |
| `prosthetic` | schema seed only (plan.md's parked prosthetics) |

## The HP ceiling

**`hp_ceiling = max(max_hp // 2, max_hp − wound_load)`**, where `wound_load`
is the sum of severities. Every mend — the night, a healing potion, the
healing spell — fills *toward* the ceiling and stops there. `camp --heal`
stopped meaning "camp until whole" and now means **"camp until as whole as
the wilds can make you"**.

**Wounds can never take a character below half their pool.** That floor is the
anti-death-spiral guarantee and it is not optional: an injury track without
one is a career that ends by arithmetic rather than by play.

HP is never docked twice for one blow — a tier's damage is always at least its
severity, so the blow that made the record has already taken more than the
record costs.

## What a blow leaves

Rolled in `_attack`, where the tier is already known:

| tier | result |
|------|--------|
| graze | **nothing recorded** — blood loss only; grazes are never located |
| wound | severity 1, located |
| grievous | severity 2, located |
| crippling blow | severity 3, located — and if it also **dropped** the body, see below |
| going Down by any route | **+1 severity, unlocated** ("badly beaten") |

Grazes staying unlocated is what keeps the 40-column log and the sheet
readable, and it matches the fiction: a cut is blood, not a disabling injury.

A second hit to the same place **deepens** the record rather than opening a
second one (bounded exactly as conditions are), capped at severity 3.

**The maiming rule.** A crippling blow that drops the body reads off its
location: a **vital** (head / chest / gut) is the killing one and the ordinary
death path stands; a **limb or extremity** **MAIMS** instead — `permanent`,
and **Down rather than dead**. A crippling blow that does *not* drop you never
maims, which is what keeps maimings rare and meaningful: a maiming is what
would have been a death. This is most of what the parked "obliterating tier"
wanted, bought for free.

**The location table is weighted** — flesh/arm/hand/leg common, chest/gut
uncommon, head/eye rare — and vitals are **15% of located hits**. That
fraction decides how often "crippling" reads as death rather than maiming, so
it is a **primary lethality lever**: bench it, never eyeball it.

## Penalties

| location | penalty |
|----------|---------|
| arm | STR −1 (and DEX −1 at severity 3) |
| hand | DEX −1 |
| leg | DEX −1 |
| chest | max STA −2 |
| gut | STR −1, and it **bleeds** |
| head | DEX −1, MIND −1 |
| eye | DEX −1 |
| flesh / unlocated | none — the ceiling loss is the whole cost |

Penalties are **folded into the raw stats** (the same machinery as the brewed
`str_buff` / `dex_buff`, run in the other direction), so every read site —
the pressure roll, a cast's AIM, the severity soak, the night's STA refill —
needs no wound special case. No stat is ever pushed below 1.

**Bleeding is re-derived, not stored as a condition.** An untreated gut wound
re-opens at the start of every fight; the free field stabilize stops the blood
when the steel stops, and the wound opens it again next time. The *wound*, not
the condition, is the thing that has to be treated.

## The treatment ladder — the anti-inflation spine

The gate is **rate and access**. The fee is a convenience and may stay flat
forever.

| source | clears | gate |
|--------|--------|------|
| field stabilize | bleed | free, automatic at fight end |
| **a bed in a settlement** | 1 severity per night | **time** (the wilds knit none) |
| **the healer** (`healer`) | several severity, a day + a flat fee | **settlement tier** |
| basic potion | HP / blood loss, to the ceiling | gold (price unchanged) |
| **surgeon's salve** | one non-permanent wound outright | gold, or alchemy rank 3 (stock-capped) |
| **elixir of mending / rank-3 healing spell** | permanents and maimings | scarce, authored |

**Healer tier caps: village 2 severity a visit, town 4, capital
everything short of a maiming.** The **cap is the gate**, which is why the fee
never needs to scale — a village that cannot touch your third wound is worth
exactly as much at level 20 as at level 1. Treatment also *dresses* what it
cannot close: a packed wound stops bleeding and stops draining morale while
its severity knits.

Every settlement has a healer service (`places._service_kind`, and
`_attach_services` hangs one on the alchemist, the general shop or the inn
where no building of its own exists) — the game gates on the **service's
tier**, never on which door it is behind.

The salve is shop-stocked and brewable; the elixir is neither, and neither
ever enters creation rolls, drops, or the overnight kit. That was deliberate:
leaving those streams alone is what keeps the bestiary calibration behind them
where it was.

## Morale

`SAT_WOUNDED_DAY` per night for each companion carrying an **untended** wound,
plus a one-off `SAT_MAIMED` the first night after a maiming. With the tavern's
morale cooldown (`SAT_TAVERN_COOLDOWN_DAYS`) a long convalescence genuinely
costs the party, and `wants_to_leave` / `leave_threshold` carry it from there
— no new departure machinery. A wound a healer has dressed costs nothing:
paying for care is exactly what stops the grumbling, which is the point of
having a ladder at all.

## Display

In play HP reads as a **state word** — Unhurt / Scratched / Bloodied /
Reeling / Failing, banded against the **ceiling**, so a wounded hero resting
at their ceiling reads Unhurt rather than permanently Bloodied. The digits
stay one command away in `status`, the pause menu, and
`ui/fight-detailed.txt`. That is the designer's "no HP as a number" at display
level only, and it is cheaply reversible — the model still has the scalar.

The wound list itself appears in the post-fight tally, the pause menu,
`status` and `ui/party.txt`, worst first, with `[PERMANENT]` and `(dressed)`
markers.

---

# The Quest System — Add-on (2026-07)

The generation layer over the bestiary: a generated **world** with persistent
Land -> Area -> Site -> Room geography, and settlements posting combat
**quests** that point into it. Every roster is assembled from the catalog by
its level annotations. `quests.py` owns it; `bench_quests.py` is its
calibration harness. The two hand-built sites stay hand-built — they are the
anchors the formulas were fitted to.

## The shape

- **Geography belongs to the world.** A quest carries its premise, giver,
  ordered objectives, progress, alignment, and rewards; its `sites` are IDs
  pointing to persistent world sites, whose `rooms` are IDs pointing to
  persistent immediate places. A generated quest may create a tower, cave,
  farm, or road site, but the place remains part of the world after the job.
  Ordinary and quest-specific places use the same records, contents,
  knowledge, and state machinery.
- **Quest shape (rebased 2026-07-26, the attrition rework):** a combat quest
  is **1–3 encounters** — 1 by default, 2 for a middling job, 3 at most —
  rolled once at the QUEST level (`QUEST_ENCOUNTERS`, weights 55/30/15, mean
  **1.66** measured). Its **place count is authored, not rolled**: a
  template carries `places` (default 1) and spans two sites only where the
  fiction genuinely moves between two places — the high pasture where the
  wolves killed and the den in the hills you track them to. "The village
  graveyard" and "the crypt below" are one place, and so is a mine and the
  chamber at its end. **Place count is never a difficulty dial.**
  - The generator used to roll sites 1/2/3 and then rooms 1/2/3 *per site*,
    centring quests on **3.74** encounters with a tail to nine (47% were four
    fights or more). Quest length was the difficulty dial, and length is
    exactly what the attrition rework has to stop spending.
  - **One quest, one level.** Every place of a job stands at the quest's own
    level; the old per-site −1/−2 decrement is gone, so the board never shows
    a job whose sites disagree about their own grade. The escalation is
    carried by the rising `ROOM_SHARES` curve instead, now keyed to the
    quest's ENCOUNTER count and consumed **in quest order** — a two-place job
    does not restart the ramp at its second place, and the anchor (and the
    boss allowance) lands at the destination.
  - Encounters spread **front-light** across places, so a three-fight
    two-place job is 1 then 2.
  - **Pay is per QUEST**, not per site (see *XP and levels*): the encounter
    shares fall as the fights do, the FIELD tranche lands when the LAST
    place closes, and the gold plus the turn-in tranche are handed over at
    the giver (2026-08-08). An intermediate place clears with a banner and
    no purse.
  - A **caper** (the dark templates' authored shapes — see the Karma & Heat
    add-on) still pins its place count to every stem it lists, and its
    encounter count follows.
- **Quest placement follows place requirements.** Each family specifies
  acceptable Area tags, a Site template/domain, and a reuse policy. A wolf
  hunt selects forest, hills, pasture, or prairie; a mine job selects
  mountains, mines, or quarries. Public roads, bridges, mines, markets, and
  towers may be reused when free; hidden camps, dens, and shrines are made
  fresh. Two active quests never share one Site.
- **Local content remains deliberately compact:** the system provides a
  direct premise, a persistent destination, concrete Room roles and contents,
  and the fights. Local quests are formulaic pieces (a culture × themed foe
  pool), not miniature stories.
- **The world is generated once per playthrough, seeded** (`session.py new`),
  and lives in the save. It creates the six finite MVP Lands and all their
  settlements, posts **one local job per settlement**, and stops. The board
  is not a census taken at worldgen — it is a **live inventory** that expires
  and refills (see *The clock*, below). Quest
  levels still roll uniformly in their settlement bands (village 1–8, town
  1–14, capital 1–20; the accidental "city" tier was merged into town
  2026-07-27). Too-easy and too-hard work both exists;
  geography selects where it happens without changing its threat budget.

## The clock: windows, bands, and the live board (2026-07-26)

The attrition rework's slice 2. Its spine: **do not make rest expensive —
make rest incomplete.** Recovery is gated on *rate and access*, never on
price, because time and geography do not inflate. A window is worth exactly
as much at level 20 as at level 1; a bed is not.

**Every posting carries a window.** A quest is stamped with `posted_day`, a
`window` rolled at `QUEST_WINDOW_DAYS` = 3–7 days **plus the return leg**
(2026-08-08: 0 days if the work is in the giver's own area, 1 elsewhere in
the land, 2 across a border — the delivery kind's round-trip precedent),
and the `deadline_day` that follows. The clock starts at **posting**, not at
taking: a job already five days old is five days into its window, so reading
the board's clock is part of reading the board. The windows were tuned when
a job completed instantly in the field; the return leg is now inside the
clock, and the widening keeps the bands where they were (measured: 33/53/10/4
against 34/50/12/3 — benchlog 2026-08-08).

**The turn-in is paid in bands**, by the day it is handed over:

| band | when | the turn-in pays |
|---|---|---|
| quick | within the first third of the window | ×1.15 |
| on time | by `deadline_day` | ×1.00 |
| late | within `QUEST_GRACE_DAYS` = 3 days past it | ×0.60 |
| expired | past the grace | nothing — the job is lost |

Only the **turn-in tranche and the gold** are banded. The per-encounter
shares and the field tranche were paid as they were earned and are never
clawed back: a failed job still leaves the party with what the fighting
paid — **80% of the XP**, since the split (above). The premium is small on
purpose — the clock is a pressure, not a second economy.

### The lifecycle: taken → work done → turned in (2026-08-08)

**A quest is paid where the giver stands, not where the last body falls.**
The old banner paid the lump and all the gold the instant the last field
cleared, wherever the party happened to be, and the giver scene the DM
narrated over it was fiction with nothing under it. Now the job has a stage
for it.

**At work-done** — the last place closed, and proof satisfied where the job
wants it:

- the banner says **THE JOB IS DONE**, and names the giver and the area to
  return to, with the deadline;
- **the world changes now** (the quest's place-state transition fires): the
  pass reopens when the deed is done, not when it is paid;
- the **field tranche** of the XP lands, **unbanded**.

**At turn-in** — `turnin QID`, gated on standing in the giver's settlement
area, run by the DM as part of the return scene and narrated as that scene:
**all** the gold and the **turn-in tranche**, both banded by the TURN-IN
day; the CHA negotiation; the reward weapon (`claim` finally waits where the
giver does); **+1 companion satisfaction** — which now lands in town by
construction, exactly where a quitting companion can be talked round; and
the epilogue with the history record. `--here` is the DM's valve for edge
fiction: a dead giver, an occupied town — pay where the story says.

**Lost after work-done** — the deadline and its grace pass before the party
returns: the turn-in tranche and the gold are gone, the banked 80% **stays**,
**no failure rumour fires** (the monsters are dead — the world changed), the
place states stay completed, and the record reads *done, never paid*. The
giver's grievance is story material, not a penalty.

**Exempt, and paid at work-done as before** — the stage is for HONEST work
with a giver to return to:

| kind | why |
|---|---|
| **deliveries** | the hand-off at the destination already IS the turn-in |
| **war waves** | no clock, the giver is a ruler mid-war, and wave 3's scripted fall makes the return scene impossible by design |
| **conquest garrisons** | no giver — the town is the pay |
| **hell assignments, dark work** | hell verifies its own work and the purse arrives by infernal delivery (narrate the receipt); a settled twist is a hand-off on the spot by definition |

### Proof of the kill

About a third of the kill-shaped templates are **bounties**, and say so on
the board row and in the giver's words: *bring back the pelts / the rings /
the head*. The terms are taken knowingly, the same doctrine as levels and
deadlines. `forge --proof TOKEN` makes one by hand.

A `proof` flag gates work-done on the **FINAL site's roster being dead** —
mook sites are exempt; only the target counts. A rout there still clears
the field and pays its encounter share (forcing the escape IS winning the
fight), but the quest sits **UNFINISHED** — *the target escaped, proof
wanted* on `status` and the board row — until the runner is killed: a warm
`pursue`, or a later re-encounter the DM stages off the loose end. The
moment it dies, the gate lifts and work-done fires.

**Ordinary quests stay driven-off-completable**, and that matters: after the
rout rebalance escapes correlate with a battered party, so flagging every
job would punish exactly the party already hurting. *Clear the pass* is done
when the road is open; the bounty is done when the ears are on the table.
The deadline prices the chase for free — the bounty is due day 9, the troll
ran on day 6 and heals whole overnight, so pursue tonight bloodied or eat
the late band.

**Untaken work expires off the board** the day after its deadline, and the
settlement that posted it keeps a day-stamped **failure rumour** — the
template's `failure_epilogue`, told once, the next time the party asks around
there ("The bandits are still on the road. Two carters are dead and the toll
bridge is theirs now."). **Taken work keeps the grace**, then closes as
FAILED wherever the party is standing, with its failure line as the epilogue.
This is what makes a day cost something: a week of camping is a week the job
did not wait through.

**The board refills instead of being pre-posted.** Each settlement keeps its
`SETTLEMENT_KINDS` slot count live — capital 5, town 4, village 2 —
and posts back toward it as days pass: at most `QUEST_REFILL_PER_DAY` = 1 new
job a day, except the first time a board is looked at, which fills it (the
land has always had work; the party has just never asked). Only the current
land's boards run their clock — a board nobody is looking at costs nothing to
leave alone. `karma.roll_dark_quest` is the shape this copies: rolled lazily,
never seen by worldgen.

The old up-front XP-coverage top-up and its assert are **gone**. They
asserted a total the board would carry forever, and expiry makes that total a
lie within a week. What replaces the guarantee is measured, not asserted: the
career sim runs a full 1–20 career with the board never running dry
(benchlog).

One kind of job deliberately carries **no clock**: the war waves (an authored
questline does not lapse). Hell's assignments carry their own pair of clocks
instead — the grace to take one, then the completion window — and never lapse
off the board (the Karma & Heat add-on). The DM's `forge` is timeless unless
given `--days N`.
- **Five races, one catalog: reskinning.** Display name is fiction, the stat
  row is mechanics — a goblin "Scrap-Hound" is the wolf row, a dwarf
  "Hold-Lord" the wight. Balance never forks on a skin.

## The threat math (dumb on purpose, sim-verified)

All of it lives in `quests.py` as tuned constants; `bench_quests.py` is the
proof. One catalog level ≈ **×1.5 threat**; a member of a row is worth
`1.5^level / ref_pack` units; a **quest's whole roster is ~2 at-level
reference encounters' worth**, split over its encounters in rising shares
(the rule the hand-built sites turned out to already follow; keyed to the
quest since 2026-07-26). Three hard lessons
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

The final room of the quest's LAST place may carry an anchor up to ~1.35× its
budget — the boss rule: the ogre quest ends with the ogre. Earlier places of a
multi-place job get no boss allowance; the anchor is still ahead of you.

**Measured honesty** (`bench_quests.py`, 300/cell, after the 2026-07-09
pain regear): generated at-level rooms win 61–93% against the reference duo
across the whole 1–20 line and generated at-level sites clear ~80–87% at
levels 1–5, sliding to ~34–55% at 15–20. The −2 column (fighting two levels
over your head) is now a **coin flip to a hard fight (~30–80%) rather than
a wall** — a deliberate consequence of the regear: the viable level band
widened, so punching up is a real choice and being overleveled for a quest
is comfortable, which is what a leveled open world needs to be playable.
Current numbers live in develop.md ("Balance / tuning").

## What careers measure (updated 2026-07-26)

The career sim (fresh duo, fresh world, grind-below-level policy, camps
between rooms, board clock run between jobs) reaches
**L5 89% / L8 72% / L11 47% / L14 16% / L17 9% / L20 4%**; median death at
level 10, and a capped career takes ~78 days / ~34 quests. The top band is
still the hard edge (per-quest wipe 40–65% at 15–20 at level) and still
waits on masterwork gear, armor, and magic (plan.md) for its missing player
power — but a full 1–20 career is now merely harsh, not a lottery.

The sim runs the board's clock but does **not** play against it: it takes the
freshest of equally good work and otherwise ignores deadlines, so it eats
whatever late turn-ins its rest schedule produces. With no travel layer its
jobs land fast — half in the quick band — which a played campaign will not
match once the road is priced in. That is the usual understatement (the
standing tuning principle), read here on a new axis. The board itself is the
part that matters and it holds: **zero careers in 500 exhausted the board**,
with ~660 postings expiring unfinished per career and ~129 live jobs standing
at the end. Current numbers live in develop.md ("Balance / tuning").

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
- **A couple live at a time** (2): worldgen posts them and the board's
  refill tops them back up as they are run or lapse. On the board a
  delivery shows **DELIVERY** where a level would go: the road's danger
  is the road's table, not a site level.
- **A courier job's window buys its road** (2026-07-26): the standard
  3–7 day window plus twice the trip's travel days, so a cross-land run is
  not late before it starts. Its hand-off is banded like any turn-in.

---

# The World & Navigation — Add-on (2026-07-09; hierarchy 2026-07-22)

The geography under the quest system: the party is always **somewhere**, and
quests refer to places in the same world rather than carrying private maps.
It remains deliberately list-shaped, not coordinate-shaped — no hex grid.
`places.py` and `place_catalog.json` own place definitions, deterministic
materialization, knowledge, contents, and mutation. `quests.py` owns encounter
placement and travel constants/tables; `session.py` owns position, discovery,
movement, and displays.

## The hierarchy

The canonical spatial vocabulary is **Land -> Area -> Site -> Room**:

- **Land** is the macro territory: identity, owner, culture, default
  environment, war state, wilderness encounter profile, and cross-land
  links. Land identity is not race: Firascir and Mortellaria are distinct
  human realms with different cultures and environments, and conquest may
  change `owner` without changing geography. `race` remains an adapter into
  NPC, quest, and encounter content.
- **Area** is a world-map destination. Its broad `kind` is `settlement` or
  `natural`; its subtype says capital/town/village or forest, mountain, plain,
  swamp, and similar. Travel between areas costs days. This handles both kinds
  of destination without making them parallel hierarchies.
- **Site** is a local destination in an area, reached without day-scale
  travel: a castle, street, tavern, cave, tower, grove, bridge, or battlefield.
- **Room** is the smallest persistent navigable place and encounter node. It
  may be a literal room or an outdoor clearing, ledge, stream bank, or stretch
  of path. `room` remains the engine term; player output leads with the
  place's actual name.

Classification follows **gameplay scale**, not physical size. A normal castle
is a site with rooms; a fortress-city whose districts host independent work is
an area with several sites. The tree may be sparse, and the UI may collapse a
single-child step — no dummy “forest site / forest room” is required. Each
deeper level must add a landmark, function, obstacle, or affordance rather
than repeat its parent's kind.

Authored definitions and saved instances are separate. Lazy child seeds use a
stable BLAKE2 digest of `world seed | parent ID | purpose | sequence`; Python's
process-randomized hash and the campaign RNG are never used. The instance
stores its selected definition IDs, seed, mutable facts, knowledge, child IDs,
and lightweight contents. Returning or loading the JSON save reads that
instance rather than calling the generator again.

Room contents are persistent facts, not automatic loot. Fixtures, furniture,
tools, food, containers, and personal objects make ordinary interiors
concrete; only a record with a mechanical item reference enters the existing
inventory systems. Required settlement Sites and Room skeletons exist with
their settlement — at world creation for the opening three, at the draw for
every settlement the world grows later. Natural Sites and ordinary houses
materialize lazily.

## The map

- **The finite world.** The MVP has Dvarvengrond, Firascir, Mortellaria,
  Ensimaa, Gibili, and Tergal: 28 natural Areas, and **three settlements a
  land** at world creation — one capital, one town, one village, drawn on
  the world seed (Dvarvengrond authors no village and opens with its capital
  and both towns). Eighteen settlements stand on day one.
- **The catalog is the reserve, not the census** (2026-08-07, the settlement
  trim). Every other authored settlement, and every generated village name
  paired with its livelihood role, waits UNBUILT in its land's reserve pool.
  One is materialized only when something in the world needs it to exist — a
  relation naming a rival center of power, a card needing a counterparty
  port. It arrives whole: required Sites, the guaranteed services and their
  faces, a board that fills to its band the first time the party looks at
  it, a garrison in its tier's band — and it records the day it was founded
  and the need that founded it. A land whose reserve has run dry says no:
  the world stays finite, and what cannot be built does not happen. This is
  the lazy materialization of Sites and houses, lifted one tier: places
  exist because the world asked for them.
- **Lands and Areas.** Each Land owns IDs in stable authored order.
  Settlement Areas are known as soon as they exist — the opening three from
  day one, a drawn one from the day it is founded; all natural Areas already
  exist but join the player map only when revealed. Discovery changes knowledge,
  never creates or rerolls the Area. `map` and `ui/map.txt` show the known
  macro Land/Area view as a 40-column list.
- **Links.** Land adjacency is explicit. Mortellaria–Gibili is a sea route;
  Firascir–Tergal uses the Flumenpur transit route until Caelum exists. Stura
  River links its Firascir and Mortellaria Areas, and Flumenpur River links
  Firascir and Tergal without creating a placeholder Caelum.
- **Position.** The save carries a breadcrumb with `land`, `area`, and
  optional `site` / `room` IDs. Status and `look` print it as, for example,
  `Elven Lands > Far Forest > Wizard's Tower > Library`. A new game starts
  in the settlement area posting the open quest closest to the party's
  level (2026-07-13 — the opening hook must be takeable; generalized
  2026-08-05 when the start level became a roll, and identical to the old
  lowest-posting rule at level 1). The two hand-built set
  sites (hideout, barrow) lie outside
  the **capital** (the first settlement worldgen made) and are **DEV/TEST
  calibration content only** since 2026-07-13 — presented alongside
  generated quests they confused the board's fiction, and the generator
  covers the level band; the benches still run them.
- **Quest offers are local; targets are tagged places.** `board` shows the current
  settlement area's jobs, and taking one requires standing in its origin
  Area. Taking it reveals its target Area and first Site. Working it then
  requires travelling to that Site's Area and entering it with `go`; `room`
  faces the next encounter there. Completion never deletes the Site. A quest
  may replace an active place state; the vertical slice changes a blighted
  forest to recovering. Word still travels (2026-07-11): the player also
  KNOWS every other open quest **in the current land** — name, level,
  where — as a "word from around the land" rumor list under the local
  board. Same stance as straight-shown levels: travel should be an
  informed routing decision, not a blind hop. Crossing into another land
  still means going to look. (`board all` remains as the DM's overview —
  not what the player reads.)

## Travel

- **`travel AREA`** is the day-scale move: **1 day** between areas of the
  same land, **2 days** crossing into another land. It returns the position
  to area level. Every travel day is a camp night: the ordinary overnight
  recovery applies, so *travel heals*.
- **The road rolls one encounter check per trip** (~15%/day, compounded),
  rolled ON THE ROAD since 2026-07-26 — before the arrival, off the
  **origin** land's pool. A road fight interrupts the trip: the days are
  spent, the party is still where it set out from, and the player re-issues
  `travel`. (A true mid-road position wants the local navigation layer;
  plan.md parks it. A sighting is simply slipped past — the party is
  moving.)
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

## Local movement

- **`look`** prints the breadcrumb, stored description, one salient known
  state or feature, known children, usable links/services, and visible Room
  contents. **`look --dm`** prints the complete current record: ID,
  template/source, seed, all facts/reveal flags, children, links, occupants,
  quest attachments, and used natural-Site inventory.
- **`go NAME`** moves from an area into a known site, or from a site to one of
  its known rooms. Entering a Site reveals its first Room; entering one Room
  reveals the next. It costs no day; local walking is not another survival
  tax.
- **`back`** moves one level outward (room to site, site to area).
- Settlement-wide conveniences (`board`, tavern, recruiting, shops) remain
  area-scoped shortcuts. The hierarchy supports meaningful local choices; it
  does not force repeated walks through streets with no decision.
- `ui/map.txt` is the macro Land/Area page. A companion `ui/minimap.txt` is
  planned for Site/Room detail and local quest markers; it is UI work, not
  built in this hierarchy slice. Until then, `look` is the local display and
  `map.txt` retains the taken-quest site summary it already shipped with.

## The explore move & the hunt

- **`explore`** spends a day ranging the current place and its roads. From a
  settlement it reveals the next existing natural Area in the Land's stable
  shuffled discovery order. Inside a natural Area it materializes the next
  unused one of that Area's three authored ordinary Site templates, including
  its full Room skeleton, then reveals the Site and entrance. Each template
  appears once; after all three, ordinary exploration reports nothing new in
  the MVP. New Areas and Sites pay discovery XP; revisits do not. The day
  still camps rough and checks for a wild encounter.
- **`house`** materializes an ordinary house in the current settlement. It
  casts a culture-compatible resident, creates a Main Room plus zero to two
  optional Rooms, and stores two to five visible Main-Room contents plus at
  most one searched object. Heating, food, livelihood tools, and yard details
  follow culture and settlement role. The complete house is saved at once and
  never rerolls.
- **Place facts and mutation.** Every Area, Site, and Room carries separate
  `features` and active `states`; facts have public/local/explore/hidden
  reveal rules and exist before discovery. The minimal API adds, replaces, or
  clears a state and appends a day-stamped world event. `place-state` is the
  DM override surface. Identity survives every transition:
  `blighted -> recovering -> no adverse state`.
- **`hunt`** is the always-available farm loop: stalk prey in the current
  land NOW (no day cost). The party chooses this fight, so unlike the road
  the level rolls at-or-below the party's (down to −2) — grinding XP, loot
  rolls, and drops is always possible. It pays **wild rates** (one
  encounter's share of a three-fight quest, no turn-in lump), deliberately
  below board work: the
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
party's jobs and hires, not a stat-sheet beauty contest). Three
guarantees replace the pick's safety valves:

- **Minimum capacity 1**: the roll rerolls until the PC's CHA holds at
  least one companion. The capacity-0 solo game was a trap dressed as a
  choice; it no longer occurs.
- **Always a magic user (2026-08-05)**: the roll rerolls until MIND comes
  out strictly above both DEX and STR — the gift's own test (Magic & Mind).
  The reason is asymmetry, not power: **the gift is the one thing a
  character can never acquire** (a spellbook is diagrams to a non-wizard),
  while steel is open to everyone — a wizard trains combat, drills a
  weapon and buys the move repertoire like anybody else. A magic user can
  be levelled as a warrior; a warrior can never be levelled into a magic
  user. Starting the PC with the gift therefore closes no door and opens
  one. The stats are the NATURAL roll, rerolled until it lands — nothing
  is nudged afterwards, so a PC wizard's shape is a wizard's shape.
  *(2026-08-07: the never-acquire asymmetry is now a temporary fact of
  the build, not doctrine — the designer ruled that becoming a caster
  mid-game should open, for gameplay openness; plan.md carries the item.
  The reroll and the wizard gate stand until that ships.)*
- **No trait sketch (2026-08-05)**: the PC rolls no traits at all (see
  *Traits — the companion layer* below), which retired the old
  no-relatives rule with it: there is no quirk to roll away. His sheet is
  his person line, his stats, his kit and his banked points.

**The long-time companion (2026-07-13 reframe of the starter ally).** One
random companion at the PC's own level is generated WITH the PC and
presented as having been **at his side for years** — nobody "joins" in
the first scene. Hire's normal terms otherwise (satisfaction 7, joining
gold to the purse, bond-linked to the PC, **traits included** — his is
the layer traits are for). The game starts PLAYABLE — a duo walks
straight out the gate — while recruiting still fills the remaining slots.

## The starting level — rolled, or asked for (2026-08-05)

A new game no longer always starts at level 1. `new` **rolls the party's
level 1–18** off the run's own rng (so `--seed` still pins the whole
playthrough), and `new --level N` fixes it anywhere in 1–20 when a session
is testing one band. The reason is played reality: no campaign has ever
gone past level 4, and hours of play stand between a fresh save and the
bands the ladder is built for — a start that lands anywhere on it is how
the rest of the game gets seen at all. The roll stops at 18 so there is
always ladder left above the party. `--race R` fixes the PC's race.

**The career a level-N start arrives with.** Everything above level 1 is
autogenerated history, not a bonus:

- **The points** are spent by the reference doctrine (`develop_hero`, then
  `autospend_points` for the leftovers) — for BOTH heroes, PC included.
  The levelup menu is for played progression; nobody wants to page through
  thirty banked points before scene one. What the doctrine bought prints
  as a one-line `career:` summary under each sheet.
- **The arms** are what those levels bought: quality steel from L4, plus
  the PC claiming his band's job-reward weapon
  (`weapons.reward_weapon_for_level` — plain chassis low, masterwork mid,
  generated magic steel at the top). A PC on a **focus staff** claims the
  staff of that band instead of rolling the chassis: his staff is his
  quality weapon, so the upgrade has to keep the focus rather than trade
  it for steel that has none.
- **The books**: one spellbook per 5 levels, each learned at rank 1 (what
  a book teaches; ranks are skill points, and the doctrine already spent
  those on the school). A level-18 wizard who knows exactly one spell is
  not what that band looks like from the inside.
- **The purse**: a fifth of what the jobs on the way up would have paid
  (`quest_gold` at the career pace of ~2 quests a level). A played party
  has spent most of what it earned; this is testing convenience, not
  economy fidelity.
- **Hell's ledger** is stamped as though it had been collecting all
  along: every pin BELOW the starting level counts as served, so a career
  start opens with no backlog. The pin AT the level is live — which is
  why the level-1 game still opens on hell's tutorial job, a level-5 start
  is pinned at once, and a level-4 one waits for 5.
- **Level 1 is the game that always was**: trash arms, an empty purse,
  hell's first pin due, no career line.

**The opening (2026-07-13, generalized 2026-08-05).** A new game starts at
the settlement posting the open combat quest **closest to the party's
level**, and `new` prints that job as the **OPENING HOOK** — the game
opens at a combat quest's doorstep (giver mid-pitch), not in a tavern. At
level 1 closest-to-level IS the world's lowest posting, so the ordinary
opening is unchanged. Taking it stays the player's call; the hook is a
doorstep, not a railroad. The story layer's war waves gate on party level,
so a career start finds the war's first word already due at the next
settlement stop.

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
- **Traits — a sketch, not a census, and the COMPANION layer only**: ONE
  behavior category (temperament / quirk / interest / weakness /
  background) + TWO presentation categories (speech / voice / dress /
  looks), one trait each. What isn't described is typical for the
  archetype; the DM edits any generated contradiction before presenting.
  **Who rolls them (2026-08-05, designer directive):** hireable
  companions — recruits, the pairs, the long-time ally — and nobody else.
  The PC and every dict NPC (givers, recipients, notables, service faces,
  posse leaders, residents, smiths) carry none. The criterion is the
  world thread's characteristic criterion: a companion's traits are
  **chosen against** at hiring and several of them **move numbers**, so
  they earn their keep; on a giver's face the same three lines were
  unbacked flavor the DM had to perform. What a dict NPC carries instead
  (a want, a problem, a disposition with teeth) is plan.md's open
  question. Most traits are DM-performed fiction; the mechanical few:
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

Companions only (never the PC), 0–10, floor −3. It is the layer that
**prices stopping**: a party that never presses on and never takes a risk
still has to keep its people fed, warm, and paid.

| Event | Δ |
|-------|---|
| Site/quest lump paid out (`award_quest`) | +1 |
| Tavern night | +1, at most once every **3 days** per companion (`SAT_TAVERN_COOLDOWN_DAYS`, 2026-07-26) |
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

Every quest carries a **giver**: a generated face (name, race, sex, age)
whose ROLE the template authors (the reeve, the grudge-keeper, the
vent-warden). The board survives only as the **DM's
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
the caller **fixes race, role, and optionally sex/age** (and a level where
the fiction knows one — posse leaders, hell's collectors, the famous
smiths), and the dice roll only the name. **No trait sketch since
2026-08-05**: a giver's temperament, voice and dress were three lines of
flavor per face that no rule read and the DM had to perform on top of the
scene — the rollback stops paying for them (see *Traits* above). NPCs are
plain dicts with **no stat block**: if one must fight, forge the encounter
or borrow a leveled body from `make_character`. `NPC_MIN_AGE` (20) floors
the age roll for anyone with a job title.

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
work never accrues sin, never sees heat, never meets a posse — no
existing mechanic, bench, or sim moves. The whole layer is opt-in at the
moment of taking a job, and it lives entirely in the play surface
(`karma.py` + session wiring; worldgen and the engine are untouched).

**2. Heat is the difficulty throttle the player pumps.** The standing
problem it answers: "part of the game would be trying to gain power to
do quests above your level." Instead of reading a board for a bigger
number, the player *runs hot*: dark work pays a gold premium and bad
karma; sin sets HEAT; heat sends retribution **at party level +
heat**. Difficulty selection by consequence.

**3. The ratchet.** Punishment fights pay XP like any road fight — and
ALL of it is sin (cutting down the Watch is itself a crime). A
villain career escalates on its own: sin → posse → bigger sin → bigger
posse. That self-driving spiral IS the villain campaign's level curve.
The brakes are equally mechanical: **honest work burns sin 1:1**
(penance), and heat is measured against the party's level, so a grown
legend needs proportionally more wickedness to stay hot.

**4. The fights stay honest; the wickedness is prose.** A dark quest's
rosters are always things that fight back — hired guards, an aggrieved
militia, the barrow's own dead, the kicked pup's mother. The engine
never resolves violence against the helpless; the theft, the arson, the
kick are narration, in the cartoon register (pratfall evil, never grimdark).
`writing.md` owns the wording: the material may be comic, but the telling
stays flat and concrete.

## The mechanics

- **Alignment.** Every quest carries `align`: `good` (all worldgen
  quests, deliveries, plain forges) or `dark` (hell's assignments,
  conquest jobs, `forge --dark`). Wild/hunt/explore fights and the set
  sites are neutral — farming wolves is not penance.
- **Bucketing.** Every QUOTED XP award from aligned work is recorded
  (`session.record_karma` → `karma.record_karma`): dark XP adds to
  **current sin** (`sin`) and **lifetime sin** (`sin_total`); good XP
  adds to **lifetime penance** (`penance_total`) and burns current sin
  1:1. Quoted amounts, not per-head shares — the ledger tracks the deed,
  not the head count. The meter line prints with the award, in the
  tally, and in `status`. The words are the save keys: bad karma was
  renamed **SIN** throughout on 2026-08-04 (session C), keys included,
  with no aliases. Heat kept its name — it is the law's meter, not
  hell's.
- **Heat** = `sin // (KARMA_HEAT_STEP × party level)`, capped at
  `HEAT_CAP` (3). KARMA_HEAT_STEP is 100, and a level-L quest quotes
  ~100·L XP — so **one at-level dark quest ≈ one heat step**, and one
  honest at-level quest ≈ one step of penance, at any level. Derived,
  never stored; levelling up cools the party's old sins by itself.
- **Punishment (the reckoning).** At heat ≥ 1, checked at travel
  arrivals, settlement nights (tavern/downtime), and camp nights — at
  most one per `PUNISH_COOLDOWN_DAYS` (**6** since 2026-08-04; 2 before,
  a cadence set before persistent wounds and quest deadlines made it
  much harsher after the fact), at `PUNISH_CHANCE` (0.6) per
  eligible stop, and never stacked on a stop that already fought (the
  law is time-spaced by design). The budget: at sustained max heat this
  is ~0.8 posses per level, where the old cooldown came to ~2 — constant
  invasion, against a levelling budget of 2–3 fights. The posse is a
  full reference-encounter
  budget off the plain humanoid ladder at **party level + heat**,
  wearing the band's lawful display names — **the Watch** (to L3), **the
  bounty guild** (L4-8), **the crown's huntsmen** (L9-13), **heroes of
  the realm** (L14+) — led by a generated face on the strongest slot
  (the conquest-boss doctrine: a name over a budget-honest row). The
  leader's name is kept (`last_leader`) as the nemesis seed. Retreat
  works normally — escaping the law is viable; the karma stays.
- **No shadow board** (retired 2026-08-04). `board --dark` and its
  three-jobs-a-day roll are gone. Dark quests now come from exactly two
  places: hell's pinned **assignments** (below) and the DM's
  `forge --dark`. Freelance wickedness is no longer a posting at all —
  it is a free **crime action** against a leveled mark (plan.md, THE
  DARK REWORK, session B). The fifteen crime templates were retired from
  the quest system with the board; they survive in `karma.CRIME_FODDER`
  as authored scene material for those actions, and nothing rolls from
  them.
- **Crime pays, in gold**: a dark quest's gold is ×`DARK_GOLD_MULT`
  (1.5). This is a **deliberate small breach of the "gold buys staying
  power" spine**: the premium is the temptation, and the XP-as-liability
  is the price tag. (The full greed economy — luxury display as a karma
  engine — is roadmap.)
- **DM surface**: `sin` (the meter + lifetime ledgers), `sin dark N` /
  `sin penance N` (off-script sins/penance — guideline: petty ~15,
  serious ~50, outrage ~100+; a NAMED reason also lands one line in
  `ui/history.txt`), `award --dark/--good`, `forge --dark`.
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
is often not Good, which is the dark path's running joke (`writing.md`
owns the register; dm.md owns its use at the table). The pact rides every
new save; `new --no-pact` is the neutral game, and a pact-holder who quests
honestly and stiff-arms
hell is a fully supported campaign — the mechanics below only price it.

- **Assignments — the pinned ladder (2026-08-04, was an interval
  clock).** Hell's work is **pinned to the PC's odd levels**:
  `TASK_PIN_LEVELS` = 1, 3, 5 … 19, ten milestone jobs across a career,
  on the war waves' proven shape (`story.WAVE_LEVELS`). Crossing an
  unserved pin makes an assignment due; it lands at the next settlement
  stop, printed as a WORD FROM BELOW block (delivery flavor rolled from
  `HELL_MAIL`: unseen job boards — searched for by paladins —
  black-waxed letters, ember-eyed couriers). Pin 1 fires at level 1 and
  **is** the tutorial job.
  - **The deck.** The **occult ten** (`karma.OCCULT_TEMPLATES` — blood
    on the altar, the hellgate, the stolen and corrupted holy things,
    the desecrated shrine) are shuffled once per save into the pact's
    `deck`; each pin deals the next card whose band admits the level,
    skipped cards staying in the deck for a pin they fit (past the
    widest band, the nearest card is dealt and the job levels into its
    band). **Order is random by directive** — variety over curriculum
    sense, because only the low levels ever get played; the hellgate may
    well come at level 3, and that is accepted.
  - **Never stacked, never jammed.** Assignments stay strictly serial:
    no second letter while one is open. Pins crossed while an account
    was open (or while the party was in the wilds) are served as ONE
    fresh assignment at the first settlement stop after it closes,
    stamped at the highest crossed pin (`last_pin_served`).
  - The task is an ordinary dark quest flagged `hell_task`, rolled AT
    the party with the margin of error running UPWARD (`TASK_SPREAD`,
    0..+1). `forge --dark` remains the DM's freeform dark-quest tool.
- **Past Due — one visit, then the write-off (2026-08-04; was the
  collections ladder).** The grace covers *taking* the job: an
  assignment may sit untaken for `TASK_GRACE_DAYS` (**10** — a pin can
  be crossed mid-wilds, and a milestone job must not be missable to a
  road delay). **Taking it stops enforcement** and stamps a
  visible completion window on the quest: `TASK_WINDOW_DAYS` (**6–8**) +
  the road days to its first site, carried by the ordinary deadline
  machinery, so every board and readout prints the clock. Hell work is
  never LOST off that clock: late pays the ordinary bands (×0.6, then
  ×0 past the grace), but the job stands until it is done, written off,
  or bribed quiet — past the window enforcement resumes instead.
  Untaken past grace, or taken and past the window, the job is PAST
  DUE, and hell calls at the posse stops (arrivals, nights; cooldown
  `ENFORCE_COOLDOWN_DAYS` (4), chance 0.6):
  1. **One WARNING** — a clerk from Hell, forms, no fight, fired at the
     first eligible stop with no chance roll, naming the final-notice
     date.
  2. **One collections visit** — a budget-honest ladder roster wearing
     infernal names (`HELL_SKINS`), led by a generated face, at **party
     level + a rolled `ENFORCE_SPREAD` (0..+2)**. The roll is where the
     devastation lives; the roster **breaks when beaten**, so retreat
     stays viable. Its XP is **neutral**: cutting down devils is
     neither crime nor penance (farming them for absolution would be a
     hole).
  3. **The write-off.** However that visit resolves — won, lost, or fled;
     hell's point is made either way — the account CLOSES: the quest is
     withdrawn (its sites released), `defied` ticks on the ledger, and
     hell is quiet until the next pin. LOSING keeps the shipped mercy
     (the purse as the fine) — the same closure, bought with coin.
     `defied` is a ledger for later content (hell's patience, pact
     termination — parked, not built).

  **The punishment budget** (the reasoning, kept): levelling takes ~2–3
  fights. Ten pins × one visit ≈ **0.53 punishment fights per level** —
  the target of ~0.5 per side. The rejected shapes: the old relentless
  rung harassed a refuser forever, and even a finite chain of three came
  to 10 × 3 ≈ 1.6/level, a third of a campaign spent on a layer the
  player opted out of. Hell quests are a HOOK into dark play, not the
  game.
- **Bribes.** `bribe` pays `BRIBE_GOLD_PER_LEVEL` (30) × party level
  for `BRIBE_DAYS` (10) of no new assignments and no enforcement. An
  open assignment survives the bribe; its grace runs fresh from the
  bribe's end, Past Due resets (warning and all), and a taken job's
  window stretches by the bought days.
- **Left for dead (the mercy).** Heroic adventurers and hell's enforcers use
  the authored LAW/HELL form of Slice 4's mercy. On the PC's first eligible
  defeat at each character level, `apply_mercy` replaces GAME OVER: the PC
  alone survives at 1 HP; the party and purse are forfeit. A second loss at
  that level is real.
  Against the **law**, all sin clears too — the heroes think him
  dead (or he ran, in shame; everyone in hell is laughing), and the
  ledger is considered settled: heat 0, a fresh start in one shoe.
  Against **hell**, the purse is the fine, the refused assignment is
  withdrawn, and the karma stays. Ordinary fights now use their roster's
  ferocity and the same level allowance; relentless enemies still kill.
  Related doctrine (dm.md): combat the fiction says isn't lethal reads
  0 HP as knocked out, same numbers.

### The caper structure (deeds & twists)

The formalized "more complex quest structure" for dark work — two
optional authored fields on a template, riding the site dicts through
`build_quest` (a template carrying either pins its site count):

- **Deed** (first site): `{stat, dc, text, fail}`. Before the site's
  first fight, the **PC** rolls 2d6 + stat vs the DC (printed as THE
  DEED block). A make closes the site CLEAN — full lump, no fight, and
  (a happy accident kept on purpose) none of the rooms' encounter XP,
  so stealth runs karma-light. A miss is the complication: the fight
  is on, and witnesses add `DEED_FAIL_KARMA` (15) flat sin. DCs
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
content passes optimize for texture, not for the career curve. Tune at
the table; a karma career sim stays parked.

The one place arithmetic *is* load-bearing is the **punishment budget**
(2026-08-04): both punishment layers are counted against the levelling
budget of 2–3 fights per level, and both are held near **0.5 fights per
level** — hell by the one-visit write-off (10 pins × 1 ≈ 0.53), the law
by `PUNISH_COOLDOWN_DAYS` 6 (~0.8 at sustained max heat). That is a
countable target, not a simulated one; it is what keeps a pure refusal
run and a max-evil run both playable.

## Explicitly not in this slice (roadmap, plan.md)

~~Conquest ticking~~ (SHIPPED 2026-07-27 — the Conquest & Holdings
add-on below), hell as a VISITABLE
place (the gladiator pits, the castle bought in bones, bullying demons
— walkable today as pure narration), a geographic wanted level
(searched-for in one settlement / a land / all lands — heat is the
global version), the good-karma mirror (hell auditing a *virtuous*
employee — the dual campaign), nemesis persistence beyond the
remembered name, race-flavored dark templates, standing dark
enterprises (the powder network earns as a crime category, not as a
holding), the rot-spell and other evil magic content, parley/bribery
with the LAW's posses (hell takes bribes now; the Watch doesn't yet),
and any karma-gated power. Lifetime wickedness got its first job in
the rework's session B (the crime-suggestion unlock feed — the Crime
add-on below) but still buys no powers or ranks.

**Coming in the rework** (plan.md, THE DARK REWORK — session C, not
built yet): the **history page** (`ui/history.txt`) with the tally of
sin and the suggestion feed, the `crimes` readout, and the **rename** of
sin to SIN throughout, save keys included. *(Session B — crime as
free actions — SHIPPED 2026-08-04; the Crime add-on below is its doc of
record.)*

---

# Crime — Add-on (2026-08-04, THE DARK REWORK's session B)

Freelance wickedness stopped being a quest. Until this slice, crime was
fifteen dark TEMPLATES a questgiver handed out and a shadow board posted;
the 2026-08-04 design session sorted the dark content apart and found
that two different things had been conflated. What hell *wants* is the
occult work — hellgates, desecration, blood on the altar — and that stays
a quest (the pinned assignment ladder above). Everything else was crime,
and crime is not work anyone hands out:

> **The PC does the thing because they want to, and keeps whatever
> material gain directly follows.**

So there is no giver, no posting, no turn-in and no board. There is a
CATEGORY, a MARK, and a resolution. `crime.py` holds the bands, the
catalogue and every knob; `session.py` owns the two commands. The sims
never import it (the karma layer's doctrine — no sim plays dark), and
every number here is hand-set and table-tuned.

## The mark is the difficulty dial

The conquest doctrine — **geography, not gates** — applied to people. A
mark's LEVEL fixes both its wealth and its protection; nothing scales to
the party, and nothing is locked.

| mark | level | where |
|---|---|---|
| commoner / stray / unpaid lunch | 1–2 | anywhere |
| tradesman, innkeeper | 2–4 | anywhere |
| merchant, priest | 4–7 | town+ |
| guild master, noble | 8–12 | town / capital |
| magnate, high temple | 12–16 | capital |
| the royal vault | 16–20 | capital |

Availability is by settlement kind — the garrison-band logic applied to
people, so a village holds nobody worth a heist. The **wilds** admit the
bands that TRAVEL (commoner through merchant, and the crown's tax cart),
which is what makes road work a real ladder instead of a village-capped
one; a category also declares WHERE it happens, so a caravan is robbed on
the road and never inside the walls.

**Farming down is self-defeating**, and that is the whole point of
pricing off the mark: robbing commoners forever pays commoner money
forever. Reaching up is the only way the take grows — and reaching up is
how the protection kills you.

A named victim is a first-class mark: `--npc NAME --level N` puts a
giver, a notable, or anyone the fiction has already animated on the
table, with the DM assigning the band by naming the level. NPCs are
freely attackable and robbable through that door.

## Casing is free — and honest

`case` with no argument lists what has a mark where the party stands,
grouped by shape, with hell's current suggestions; `case CATEGORY` prints
that mark's level, the take, the check, and the protection roster.

The mark is **seeded** off (world seed, place, day, category). Nothing is
stored between casing and committing, and nothing needs to be: the same
seed rolls the same mark, the same take and the same roster, so
committing today faces exactly what the casing showed. Sleeping on it
rolls a new mark tomorrow. This is the OSR straight-board stance the
quest board already takes — the numbers are on the table, and the
decision is the game.

## Three shapes

- **Petty** — a trivial check or none at all, and **never a fight**. Flat
  sin (`PETTY_SIN`, 10–15) quoted as XP, coin in pennies (`PETTY_GOLD`);
  the mark's level buys it nothing, which is exactly why petty crime is a
  dead end. A miss is simply a miss: no take, no sin, no ledger stamp.
  The token roster the fiction may want — the pup's mother, the indignant
  innkeeper — is the DM's `forge`, not the engine's.
- **Deed** — 2d6 + stat vs DC, the caper machinery generalized (DCs sit
  9–11 against stats 3–5). A **make** takes it clean: the lump, the sin,
  no blood, the whole crime in one message. A **miss** botches it into
  the mark's protection with witnesses (`WITNESS_SIN`, the caper's own
  `DEED_FAIL_KARMA` 15) — and winning that fight still pays the take,
  because the crime happened, the hard way.
- **Force** — no check at all: straight to the protection, then the take.
  The fight pays its own XP as dark work, and the crime lump lands on
  top.

A commission is booked when the crime is **committed**, not when it
pays: a force job the party is driven off, and a botched deed whose
fight is lost, still stamp the category's monotony window. Hell was
watching the attempt.

The protection is always **people who fight back** — a `build_room`
budget at the MARK's level wearing the retired templates' rosters and
skins (`karma.CRIME_FODDER`, kept for exactly this). The wickedness
itself stays narration; the engine only ever resolves honest fights. A
lost fight pays nothing, and so does a retreat.

## What it pays

- The crime **lump** is `CRIME_XP_PER_LEVEL` (50) × the mark's level ×
  the category's multiplier — about **half an at-level quest**, because a
  crime is one scene and not an expedition. Every point of it is sin.
- **Coin** crimes pay `CRIME_GOLD_PER_LEVEL` (20) × mark level × the same
  multiplier. **Goods** crimes (jewels, relics, cattle, a wagon's
  freight) pay what the FENCE gives, `FENCE_RATE` 0.5 — the gap between
  the two is the reason coin crimes exist. The fence takes its half out
  of the coin only: the sin is what the deed was, not what the fence paid
  for it.

## Monotony, and the creativity carrot

Every commission day-stamps its category. Stamps still inside
`MONOTONY_WINDOW` (10 days) cut the next one's **sin and XP** by
`MONOTONY_MULTS` — (1.0, 1.0, 0.5, 0.25) by how many are already in the
window, floor 0.25.

- **Gold never depreciates.** The loot is the loot; it is hell that gets
  bored.
- **It is temporary by construction.** The stamps age out — nothing has
  to be reset, and nothing is remembered forever.
- **Alternating two categories resets neither.** Each window is its own.
  A two-crime loop is *supposed* to stale; a portfolio, or honest days
  between sprees, stays fresh.
- A category's **first-ever** commission pays `FIRST_TIME_MULT` (1.5) —
  the carrot that points at the suggestion feed.

## The news cycle (`karma.py`)

A **single** sin gain at or above the heat step (100 × level) stamps
`hot_until = day + NEWS_DAYS` (6), and heat cannot fall below 1 until
then however fast the penance is bought. Anti-laundering for big scores:
a vault heist or an occult assignment is a story, and a story cannot be
honest-quested out of the town gossip inside a week. It applies to quest
turn-ins too — the occult assignments are exactly the scores it exists
for. **Petty sin stays dodgeable on purpose**: the tithing puppy-kicker
is a comedy the game wants.

## Unlocks gate suggestions, never permission

Every category is committable from scene one. What the ledger buys is
**advertising**: hell suggests one new category on the first COMPLETED
assignment, and one more per `CRIME_UNLOCK_STEP` (200) of lifetime sin,
in random order. A "locked" category committed anyway unlocks itself by
deed and never consumes a grant.

The full catalogue lands around **4,750 lifetime sin** — the derivation:
the XP budget to level 20 is 19,000 quoted, at most half of it can be sin
if heat is ever to come down (each sin point wants a penance point), and
half of that again is the target.

## The catalogue (27 categories)

Nothing grim: `writing.md`'s cartoon register gates the list. Theft,
arson, extortion, hubris and kicked puppies — indignant victims, never
brutalized ones.

- **Petty (5):** kick the puppy, dine and dash, cheat at dice,
  petty vandalism, pickpocket a commoner.
- **Deeds (10):** burglary, the vault heist, the con, counterfeiting,
  blackmail, impersonate an official, poison the feast, grave-robbing,
  the powder trade, cattle rustling.
- **Force (12):** mugging, the protection racket, strong-arm debt
  collection, highway robbery, rob the tax collector, arson, kidnapping
  for ransom, jailbreak, caravan robbery, the village raid, the land
  grab, betrayal.

## The knobs, and what to watch

All hand-set (`crime.py`): `CRIME_XP_PER_LEVEL` 50, `CRIME_GOLD_PER_LEVEL`
20, `FENCE_RATE` 0.5, `PETTY_SIN` (10, 15), `PETTY_GOLD` (1, 5),
`MONOTONY_WINDOW` 10, `MONOTONY_MULTS` (1.0, 1.0, 0.5, 0.25),
`FIRST_TIME_MULT` 1.5, `CRIME_UNLOCK_STEP` 200, `WITNESS_SIN` 15; plus
`karma.NEWS_DAYS` 6.

Two things to judge from play:

- **The heat pump.** Crime lumps are smaller than quest lumps, so running
  hot now takes big marks or volume. That is coherent — petty crime
  should not summon the crown's huntsmen — but `CRIME_XP_PER_LEVEL` is
  the lever if heat proves too hard to reach.
- **The flat DC.** A deed's check is 9–11 whatever the mark's level, so a
  low-level party can gamble one roll against a very rich mark: a make is
  a clean windfall, a miss is a protection roster far above its weight.
  That gamble is the intended shape of "difficulty comes from the mark",
  but if the make proves too cheap the lever is a DC that climbs with the
  mark's level, or a lump the clean take only partly pays.

## The `crimes` sheet (2026-08-04, session C)

The dark side's `prices` page, and the player's whole crime surface in
one screen. It reads the **band**, not one rolled mark: every category
available where the party stands, grouped by shape, each row quoting
what its mark band is worth (gold, sin/XP with the current multiplier
already applied), the check it asks for, and its authored
what-stands-in-the-way line. Then the party's tally of sin, the meter,
and hell's current suggestions.

`case KEY` stays the exact read (today's rolled mark, its level and its
roster); `crimes` answers "what is worth doing here" without
twenty-seven casings. A pure readout — no save touched, every number off
`crime.py`'s live knobs. Petty rows quote `PETTY_GOLD` / `PETTY_SIN`
straight, because petty is flat by construction; everything else is a
clean function of the mark's level, so the band's ends ARE the span.

## Explicitly not in this layer

Crime buys no powers or ranks; standing dark enterprises are still
parked (the powder network earns as a category, not as a holding); and
no sim or bench sees crime, by the karma layer's doctrine.

---

# The Campaign Record — Add-on (2026-08-04, THE DARK REWORK's session C)

**`ui/history.txt`** — the fourth rewritten UI page, beside `party.txt`
and `map.txt` and committed by `sheet` with them. The party sheet is the
present and the map is the world; this is the MEMORY. It exists because a
playthrough spans days of real time and the chat scrollback is not a
record: what the party did, what it is known for, and what it owes are
continuity the DM has to be able to look up.

## The page

Four sections, always all four (an empty one says so rather than
vanishing), 40-column wrapped like every other page:

- **QUESTS DONE** — one day-stamped line per job, carrying the epilogue
  that closed it. Dark work is tagged `[DARK]`. A job LOST to its window
  is recorded here too, with the giver's failure line: the section is
  the campaign's job record, not a trophy case.
- **REMARKABLE** — the war's waves broken (and the scripted fall, and
  the war's end), conquests taken and holdings lost, hell's assignments
  served and its write-offs, defeats survived (the level's one mercy,
  LEFT FOR DEAD, THE LESSON), maimings, named kills, and the DM's own
  named off-script sins.
- **THE TALLY OF SIN** — per crime category: the count and the last day
  it was done, busiest first; then the total, the meter line, and the
  lifetime sin / penance ledgers.
- **SUGGESTIONS** — up to `SUGGESTIONS_SHOWN` (3) unlocked-but-never-
  committed categories, in an order seeded off the world and the DAY.
  Catalogue order would advertise the same two petty crimes forever;
  seeding it means the feed rotates without storing anything.

## The state

`history` in the save: a list of day-stamped records, oldest first, each
`{day, kind, line}` plus an optional `note` (the epilogue). Two kinds —
`quest` and `remarkable` — because the page has two narrative sections.
`session.remember` is the only writer. It drops an exact duplicate of the
most recent record of its kind on the same day, which is what lets the
maiming SCAN be safe: a maiming lands deep inside `_attack`, so rather
than hooking the melee, `save` re-scans the party's permanent wounds
every time and the guard absorbs the repeats. Records are trimmed **per
kind** at `HISTORY_CAP` (60): a career of jobs must never push the
write-offs and the maimings off the page.

**Named kills** are detected by shape, not by a flag: ordinary rows are
numbered off the catalog ("Cutthroat 2"), so a dead foe whose name has no
trailing number is somebody the fiction cast — a quest boss, a conquest
defender, a posse leader, one of the war's lieutenants.

The **tally's `last` day** is stored separately from the monotony
window's day stamps (`crime.stamp`). The window prunes itself as it is
read — that is what makes monotony temporary — so reading the last day
off it would forget a career-defining crime ten days after it happened.

---

# Conquest & Holdings — Add-on (2026-07-27, the domain layer's first slice)

Plan.md's "conquest ticking" shipped. The player can TAKE a settlement,
hold it with paid levies, and bleed it for tribute — the domain game
opening at the level the game is actually played at (a village falls to a
level 4-5 party), not parked at the endgame. Mechanics in `conquest.py`;
the play surface in `session.py` (`conquer` / `garrison` / `holdings`).
The sims never import it: like karma, the layer is play-surface only, its
knobs hand-set and table-tuned.

## Design spine

- **The settlement is the unit of ownership.** No provinces, no tiles: the
  map stays a list and ownership is a tag (`[YOURS]`), exactly the shape
  the war's occupation layer prints. One object to point a quest at.
- **Garrison levels are geography, not gates.** Each settlement rolls its
  garrison level ONCE (stable-seeded): village 3–5, town 6–10, capital
  11–15 — a contiguous ladder, so one land is a whole campaign: first
  village around L4, towns through the mid band, the capital around
  L13-15. Nothing forbids attacking early; the fight is the gate, the
  board's straight-levels doctrine applied to conquest.
- **The duel is the battle.** Conquest is won by the party breaking the
  garrison in person; armies are NUMBERS around that fight, never rosters
  in it. The engine only ever simulates the party's own melee.
- **Holding costs levies, not heroes.** Recruits are freely rehired, so a
  garrison is an army resource: one integer per holding, bought with gold.
  This is gold's first standing job before L15.
- **Conquest is dark work, priced by the machinery that exists.** Its XP
  is sin, and the flag itself keeps a HEAT FLOOR up — holding land
  is standing wickedness. The strategy opponent is the heat layer the
  game already tuned, not a new AI.

## Taking a settlement

`conquer`, standing in the target settlement, builds the garrison job:
an ordinary dark quest underneath (same schema, threat math and pay
ladder), one place — "the garrison keep" — at the settlement's garrison
level, with the land's cultural ladder pool. Village 1 encounter, town 2,
capital 3 (the war waves' maximum). The last room is capped by a **named
defender** (a generated face, per-race role: castellan, warden of the
walls, gate warden, wall-crew boss, war-chief of the garrison) worn as a
display name over the budget-honest strongest slot. The job has **no
clock** (a keep does not lapse), **no giver**, and is **not posted on the
board** — it exists because the player declared it, and is taken like a
war wave (`take QID`, at the settlement).

Winning the last room flips the tag: `*** NAME IS YOURS ***`. The quest's
gold is the keep's strongbox (10 days of the settlement's tribute, with
the dark premium on the turn-in); its XP is all sin. An
aggressor-occupied settlement cannot be conquered — the yoke holds it,
and the war decides.

## Holding

Each holding is a record in the save (`holdings`): garrison heads, the
tribute meter, the raid clock.

- **Tribute** accrues per held day (village 3g / town 8g / capital 20g)
  and is collected automatically when the party stands in ANY holding —
  the stewards bring every chest to the flag. A holding that falls loses
  its uncollected tribute.
- **Levies**: `garrison N`, at the holding, buys N heads at 5g each,
  capped by the settlement (village 12 / town 24 / capital 48). A FULL
  garrison always repels the worst raid its tier rolls.
- **Raids**: the crown's counterstroke, rolled lazily over elapsed days at
  the news points (arrivals, settlement nights, the board), ~6%/day per
  holding, only where the party is NOT standing. Heads against heads: a
  raid of strength S against garrison G is repelled when G >= S (costing
  S/2 levies) and takes the holding when G < S. The party's own fights
  remain the posse machinery's job.
- **The heat floor**: each holding raises effective heat by 1 (capped at
  HEAT_CAP). Zero sin with one holding still means the law calls at
  party level +1 — and killing the posse is itself sin, so the flag
  feeds the ratchet.
- **The board goes dark.** A held settlement posts no honest work for
  its conqueror; crime and the pact serve instead. The tavern, the shops,
  recruiting and downtime keep the party's custom — it is their town now.
- **The yoke outranks the flag.** When the war's wave 3 fells a land, the
  aggressor seizes the party's holdings there; retaking one after the war
  turns is a fresh conquest.

## Display

`holdings` is the ledger (garrison, tribute rates, waiting chests, the
heat floor); `status` carries a one-line summary; `map`/`ui/map.txt` tag
held settlements `[YOURS]` and list the holdings under their own section.

## The knobs (`conquest.py`, all hand-set)

`GARRISON_BANDS` (3-5 / 6-10 / 11-15), `CONQUEST_ENCOUNTERS` (1/2/3),
`TRIBUTE_PER_DAY` (3/8/20), `PLUNDER_MULT` 10, `GARRISON_HIRE_COST` 5,
`GARRISON_CAP` (12/24/48), `RAID_CHANCE_PER_DAY` 0.06, `RAID_STRENGTH`
(2-6 / 5-12 / 10-24), `RAID_GARRISON_LOSS` 2 (divisor),
`HOLDING_HEAT_STEP` 1. `test_conquest.py` is the contract suite.

## Explicitly not in this slice

Armies that MOVE (rival powers taking provinces from each other — the
macro-game session's question), army-vs-army battles beyond the raid
roll, the good mirror (liberating occupied settlements for their own
crown — the dual campaign's other skin), garrison QUALITY (veteran
levies, a companion as castellan), vassal income buildings and the
greed economy hookup, conquest-flavored quest content beyond the built
job, and any narrative framing pass (chosen one / dark lord / prophet —
the 2026-07-27 brainstorm's list waits on the new-setting session).

---

# The Weapon Ladder & Generation — Add-on (2026-07-28)

The full assortment of weapons, trash to mythic: one design currency, one
budgeted generator, a famous pregenerated armory, and the legendary smiths.
`weapons.py` owns the generator and the world layer; the engine hooks
(schema fields, equip bookkeeping, the rider and quirk hooks, the lunge)
live in `rpg.py`. The sims never import `weapons.py`, and every generation
rng is DERIVED (worldgen streams and the bench suite are byte-identical to
the pre-weapons-layer world).

## The severity-point (sp) — the design currency

The shipped quality four already encoded the exchange rate: they are
bench-verified equal ("suited, not ranked"), and setting rapier = katana =
zweihander solves to **+1 attack pressure = 2 sp, +1 defense pressure =
2 sp, +1 severity = 1 sp** — all four chassis land at exactly **3 sp** (the
staff closes with its focus at 2 sp per +1 max Power). The full table
(`weapons.py`):

| Advantage | sp | Note |
|-----------|----|------|
| +1 severity | 1 | the base unit |
| +1 attack pressure | 2 | proven by rapier = katana |
| +1 defense pressure | 2 | proven by katana = zweihander |
| +1 max Power | 2 | the staff's focus rate |
| +1 max STA | 1 | the cheap pool axis |
| +2 max HP | 1 | bought in pairs |
| **+1 true STR** | 2 | severity AND soak; magic tiers up |
| **+1 true DEX** | 3 | lands, defends, and feeds severity through the margin — **legendary tiers only** (the standing +DEX warning made law) |
| rider: burn / bleed | 1 | priced off the pyromancer's measured shift |
| rider: poison / rime | 2 | untimed venom follows you out; enemy-DEX is dear |
| the lunge quirk | 1 | once per fight |
| gold / karma on kill | 0 | economy and story, never combat power |

Melee steel only: a ranged card's severity flat replaces STR entirely
(the Ranged Combat add-on), so the cards sit off this scale on purpose.

## The ladder (about ten rungs, not twenty)

| Rung | Tier | sp | Acquired | Gold |
|------|------|----|----------|------|
| 1 | Trash (club, knife, sling) | −1 | **chargen** (the 2026-07-28 deal) | 1–2 g |
| 2 | Soldier's arms | 0 | looted from humanoids | 5–8 g |
| 3 | Heavy arms | +1 | looted, cheap shop | 15 g |
| 4 | Quality four | 3 | shopped | 60 g |
| 5 | Masterwork | 5 | **shopped, capitals** (+1 atk, dur 5) | 300 g |
| 6–7 | Magic | 6–7 | quested, robbed, commissioned | ~480–960 g |
| 8–9 | Legendary | 8–9 | the armory, the top smiths | ~1,900–3,800 g |
| 10 | Mythic | 10 | one resting-place find per world | beyond price |

**The mythic cap is the transcendence doctrine's half:** the player can by
design double a stat (natural 6 → heroic 12), and HALF of that may come
from the weapon — +3 effective points on its signature axis, never more.
The gold curve is **superlinear** (roughly doubling per sp above quality,
`value_for_sp`): career gold is ~thousands, and a linear price would sell
mythic steel for lunch money — and let gold buy DEX-axis power at HP-axis
rates. **There is no all-stats artifact** (designer call, 2026-07-28): the
maximal weapon exists only as the yardstick that defines the budget.

## The profile rule (how generated weapons stay legible)

A generated weapon is a quality CHASSIS plus a budget: **at least
two-thirds of the budget on the chassis's signature axis** (rapier/katana →
the DEX axis, zweihander → the STR axis, staff → the Power axis), **at most
one condition rider, at most one quirk**, per-axis caps (+3 DEX/STR at the
very top). It reads as "a rapier, but more so, with one twist" — never a
stat soup. Budget honesty is a test contract (`test_weapon_gen.py`): a
generated weapon re-prices to exactly its tier's sp.

## Riders and quirks (the engine hooks)

- **Riders** are the wielder-side mirror of `Entity.inflicts`: a landed
  weapon-delivered blow (never a cast, never the broken stump) applies the
  condition with the weapon's own power/rounds. **Rime** rides the ice
  school's rail instead — a stacking fight-only DEX debuff.
- **The lunge** (`Weapon.lunge`): the wielder's first attack of the fight
  reaches gap 1 — the flying lunge closes the distance and strikes in one
  motion (it also holds ground in the movement phase, like any threat).
  Once per fight; cleared with the per-fight states.
- **On-kill quirks** (`gold_on_kill` / `karma_on_kill`): the engine only
  counts (capped at `MIDAS_FIGHT_CAP` kills a fight — a swarm room is not
  a mint); the session drains the counters at the fight's end into the
  purse and the karma ledger.
- **Stat bonuses** (`dex/str/sta/hp/power_bonus`) are the membrane made
  steel: applied and removed by `equip_weapon`, symmetric by contract, and
  an unequip never kills (the HP floor is 1).
- **Proficiency follows the chassis** (`prof_name`: `Weapon.base`): a
  masterwork or named magic katana counts as a katana in a drilled hand —
  the reward never costs the ranks — and draws the chassis's special moves
  (iaido). A bare `give --as` reskin has no base: the old
  proficiency-follows-the-name doctrine still holds for costumes.

## The world layer

- **The famous armory** (`world["armory"]`, ten per world: six magic,
  three legendary, one mythic): named pieces (Frostfang, Kingsbane...),
  rolled at worldgen on a derived rng and **known from day one** — rumor
  is free. Owners are drawn from the world's notables and **wield their
  weapon in any fight over it** (the weapon guards itself); the rest lie
  in named resting places, and the mythic piece is ALWAYS a resting-place
  find — the endgame is going and getting it. Never for sale. Acquiring
  an owned one is theft, robbery, or a questline — the karma layer prices
  the dark routes. `armory` is the DM inventory; `python weapons.py` the
  eyeball check.
- **The legendary smiths** (`world["smiths"]`, three per world, seated in
  distinct capitals): each has a style (blades only / war steel / any), a
  CAP (sp 7 / 8 / 9) and **the pride floor — cap − 1 — below which they
  refuse to work**. A commission (`commission SMITH HERO [CHASSIS]`) costs
  the open value plus a pride premium (`COMMISSION_MULT` 1.5) and takes
  sp − 3 forging days (narrated; the profile that comes off the anvil is
  the smith's art, not a menu). This is the one way gold buys magic steel.
- **Weapon-reward quests** (`quests.WEAPON_REWARD_CHANCE`, 15% of
  postings): the job's turn-in **gold lump is replaced by a weapon** of
  the level's grade (quality ≤L4, masterwork L5–9, magic L10–16, legendary
  L17+) — XP and the per-encounter shares untouched, the board row says
  `pays a masterwork rapier`, and the turn-in banks it for `claim HERO`.
  Rolled on a per-quest derived rng: the posting stream never moves.

## Serialization

Catalog weapons serialize by name, generated instances whole. There is no
old-save path and no lazy backfill: worldgen rolls the armory and the
smiths for every world (develop.md, "No backwards compatibility").

---

# The World Layer — Add-on (2026-08-07, the worldsim build's frame)

The world stopped being scenery. Every land now carries a **wealth band**,
a set of day-stamped **states**, and a shuffled **crisis deck** it draws
from when it needs something to be happening; **relations** between lands
carry one land's trouble into the ones it feeds. Nothing ticks in the
background — the world's day is rolled where the game's day already
advances, off a stable seed, so a land the party has not visited in a
month is exactly where its own dice put it.

`worldsim.py` owns it; the design spine and the content it is drawn from
are `worldsim.md`'s.

## The wealth band (the roll every land opens with)

- **2d6 at worldgen, per land**: 2–4 **CRISIS** (~17%), 5–9 **NORMAL**
  (~67%), 10–12 **PROSPEROUS** (~17%). It is a **state in an exclusive
  slot**, not a constant — cards move it.
- **Crisis is where content lives.** A land in crisis draws a card on
  need and is living through one most days; normal and prosperous lands
  stay mostly invisible and turn up about one card in a fifty-day
  stretch. Prosperity shows as full boards, prices, and the absence of
  trouble.
- **A land in crisis is in crisis from scene one**: it draws its first
  card at worldgen, dated day 1.
- The roll is on a **derived seed**: the world layer moves no worldgen
  stream, so every career bench measures the same board it always did.

## States, and the exclusive slots

- A state is a **word the land holds**, day-stamped, visible, and
  changeable — `harvest-failed`, `strike`, `toll-squeeze`. They ride the
  same machinery as a place's states, so the world and the map speak one
  vocabulary.
- Some belong to an **exclusive slot** (the land's `deposit` stage, the
  standing of its `foreigners`): setting one clears whatever the slot
  held, and a card that would only re-assert a slot the land already
  holds does not fire at all.
- **What a card sets outlives it; what it sets *while* it stands comes
  off with it.** That holds for the wealth band too: a failed harvest is
  a season of crisis and then it is over, while a vein running out is
  simply what the mountain is now — and only another card (a dwarf who
  can work a written-off seam) puts it back.

## The card (the event pulse)

- **Admitting conditions** over land, wealth band, states held (its own
  or derived), states forbidden, and weather (the sky and the wet/dry
  spell behind it — the Weather add-on below).
- **Up to five outlet effects**: post/cancel/reprice a quest, adjust the
  priced menu, add a local encounter-table entry, emit a **news line**,
  flip a **state**. The frame applied the last two; all five apply since
  the economy floor (its add-on below owns the first three).
- **An optional day-stamp clock.** One card stands over a land *per
  track* at a time, so the news stays legible and the states stay
  coherent; a card with no clock leaves its mark and stands over nothing.
- The deck is **drawn on need, not shuffled through**: the first card the
  land admits, with skipped cards left in the deck for a later day (the
  hell pact's deck pattern). An exhausted deck reshuffles.

## Relations (what one land's trouble does to another)

Authored **directed edges** — who eats whose grain, who logs whose
forest, whose mercenaries come when called. They are lookups, never
traded quantities, and the states they cause are **derived at read time
and never stored**: a failed harvest in Firascir is `grain scarce` in
Ensimaa, Dvarvengrond and Gibili for exactly as long as it lasts, and
gone the day it lifts. Cards admit on derived states like any other.

## Where the world is rolled, and where the player meets it

- **Rolled** wherever the calendar advances (travel, explore, camp,
  tavern, downtime, the board) — the same points the quest board's refill
  and the crown's raids already fire. Every land is brought up to today
  together, so no relation ever reads a land that is behind the calendar.
- **Heard** where news lands — arrivals, settlement nights, the board:
  `WORD FROM <LAND>`, day-stamped, told once. Word travels **within a
  land** (the board's own rumor rule); another land's cards are heard by
  going there, or through the states its edges derive here. A long
  absence is summarized, not scrolled.
- **Seen** on `map` / `ui/map.txt`: under each land the party has visited,
  its band and what it is living through, the derived states naming their
  cause. This is the STATE DIFF — the readout that shows the world moved
  while the party was elsewhere.
- **`world`** is the DM's inventory of the whole layer: every land's band,
  states, derived states, the card standing over it, and how deep its deck
  still is. `place-state` remains the override.

---

# Weather — Add-on (2026-08-08, the worldsim build's first content rung)

Every land rolls a **sky** every day, off its own climate. It is the
cheapest world content there is — land-agnostic, and the only layer that
touches the party on every day it is out of doors. `worldsim.py` owns the
roll, the states and the cards; `places.py`'s environment profiles author
the distribution; `rpg.py` owns the two things the sky does to a body (the
DISEASE family, the storm's field penalties).

## The day roll

- **Nine words**, shared by every land: clear, cloud, wind, rain, storm,
  fog, frost, snow, heat. What differs is the **weights**, which each
  environment profile authors as the numbers behind its climate sentence.
  The game has no season track, so a profile's winters and summers are
  averaged into one year-round distribution rather than modelled.
- The same word **reads differently on different ground**: a storm in the
  dwarves' highlands is a *snowstorm*, and it is the same card underneath.
- Two counters run behind the roll. **DRY is days since the last rain**, so
  an overcast day extends it — a grey sky is not a drought ending. **WET is
  a run of wet days** that a dry day breaks and an overcast one does not:
  three days of rain with a grey one in the middle still puts the fords
  out.
- A held **drought bends the roll that made it** — rain and storm weights
  cut hard, clear and heat lifted — which is why droughts last past the day
  that started them.

## The three tracks

A land carries **one live card per track**, each with its own deck, draw
rule and timescale, because one slot could not hold them: a season of
drought would have blocked every storm under it, and a storm would have
blocked the harvest failing.

| track | drawn by | timescale |
|-------|----------|-----------|
| **crisis** | the wealth band (the frame's own rule) | days to weeks |
| **weather** | today's sky, times the card's own `chance` | hours to days |
| **season** | a long wet or dry spell | a season |

No weather card carries a wealth condition: **a prosperous land gets the
same storms as a starving one**, which is what makes weather the outlet
that reaches a quiet world. A card that *is* the weather (the storm, the
dust storm) **holds the sky while it stands**, so a storm that sets in for
two days is a storm on both of them.

## What the deck holds

- **THE STORM SETS IN** — any land, on a storm day, 1–3 days. Its state is
  `the storm has closed the roads`, and it is what the field penalties and the
  cabin table hang on.
- **THE FORD IS OUT** — the two human lands, after three wet days. Fords
  uncrossable, bridges and ferries tolled by men who know it: the road
  costs **a day** while it stands, and the toll racket is the vigilante
  invitation. (The ferrymen's own rates are authored on the card and wait
  for the economy floor with the rest of the priced menu.)
- **THE FOG RAISES BONES** — any land, on a fog day, rare. Skeletons walk,
  and the country people **have a name for the man who calls them up**: a
  necromancer of rolled level 3–14, named once and kept on the land record.
  A second fog raises the *same* man's dead. The rumor address is
  deliberately cheap — a name and a level, no landmark machinery — and the
  party goes looking or it does not.
- **THE FOREST BURNS** — Ensimaa, only under drought. An evacuation, a
  blame question, and a `burn is still black` scar that **outlives the
  fire**; one card (the burn going green, a season later) is the way back.
- **THE DUST STORM** — Tergal, under drought. The roads stop and the herds
  scatter: **a day** on the road, and recovery work after.
- **THE SMOG SETTLES** — Gibili. The mill smoke has nowhere to go; it is
  the one sky **a roof does not keep out**, and the owners say it is the
  weather.
- **THE RAINS DO NOT COME** — the season card, any land. A drought is a
  **relative** thing, so the spell that triggers it is the land's own (a
  fortnight without rain is a disaster in the shaded forest and an ordinary
  Tuesday in the dry south). It is the state the wildfire and the dust
  storm admit on, and the one the economy floor's relations will read.

## The night in the open — the DISEASE family

The conditions framework's **third family**, parked since the attrition
rework and cashed here. What makes it a family rather than a fourth kind of
poison is its **clock**: rounds are the wrong unit for an illness.

- **Catching one.** A night in the open under rain, frost, snow or storm is
  **2d6 + STR** against the sky (rain is easy, a storm is not), once per
  hero. A miss is a **COLD**. A roof of any kind — walls, or the storm
  night's cabin — skips the check entirely: *shelter is the answer to
  weather, and always was.*
- **Bounded deepening.** A chill caught while a cold is running deepens it
  to **PNEUMONIA**; a chill caught on pneumonia does nothing. There is no
  third rung, and disease never kills.
- **What it costs.** Not a per-round tick — the **HP ceiling**, like a
  wound: sick, you cannot get back to full, and you walk into every fight
  carrying it. (Under the same floor as a wound, so it is never a spiral.)
- **Shaking it.** One roll a night, **2d6 + STR**, harder by a rung for
  pneumonia and easier under a roof. A made roll eases it **one rung** —
  pneumonia to a cold, a cold to nothing — so the way down is the way up
  walked backwards. STR and not STA deliberately: STA is a pool that
  doubles over twenty levels, and an illness that got easier to shake as
  you levelled would inflate exactly the way this game's costs never do.
  A cold is ~3 nights in the wilds and ~2 in a bed; pneumonia is a
  fortnight out there and under a week in a town.
- **The healer's rung.** A visit **breaks one illness outright** for a
  flat fee, gated by the same tier cap that gates wounds: a village
  herb-wife can break a cold and can do nothing for a pneumonia.

## The storm in a fight

One field knob and one save, and both ride an **outdoor** fight only — a
room, a cellar or a barrow has no sky in it.

- **A shot drags** (−2 to its attack pressure). A cast does not care about
  the wind and neither does an axe.
- **Every step is a save** (2d6 + DEX): a miss costs the **step**, never
  the round's attack. Weather slows a fight down; it never decides one.
- Both sides carry it, symmetric by contract like the ground itself — the
  storm is not a party debuff, it is what the fight is being fought in. It
  rides a paused fight to its resume: a storm the fight opened in is still
  blowing when the player comes back to it.

## The cabin table (what the storm drives you into)

The storm's real content is not the penalty, it is **where the penalty
drives you**. A wilds night under a storm rolls for shelter, and what the
shelter holds is a five-row table: a host who is **helpful** and glad of
faces / one with a **job** they have been waiting to tell somebody / one
who owns something **valuable** (or has just lost it to robbers) / one with
**sinister** designs (the pot, then the axe) / one who wants **serious
coin** for a dry night. A dry night skips the exposure check and the
storm's morale grumble.

The display prints what the party **sees** plus a `(DM eyes only: ...)`
line — the sinister row would be no scene at all if the display gave it
away. That line is never read aloud (dm.md).

## Where the player meets it

- **Seen** on the road: one `WEATHER:` line where the sky matters — setting
  out, a day afield, a night in the open, and on arrival. It says the spell
  when the spell has become the story ("the 4th wet day running", "12 days
  without rain").
- **Seen** on `map` / `ui/map.txt`, under the land's band and states.
- **Felt** as a day added to a leg, a chill in the night, a dragged shot, a
  companion's grumble after a night out in a storm.
- **`world`** carries the sky, the spell, all three tracks' live cards, and
  the fog's named necromancer if the land has one.

---

# The Economy Floor — Add-on (2026-08-09, the worldsim build's second content rung)

The world layer stops being a readout. The three outlets the frame carried
but did not apply — the **quest board**, the **priced menu** and the
**local encounter table** — are wired, and the thread's two invariants
land with them:

- **The board reacts to world state.** How much work a settlement posts,
  what it pays, and what work is even *there* now depend on the land's
  wealth band and the cards standing over it.
- **Something moves without the player taking a job, and it is visible on
  return.** The news and the state diff shipped with the frame; now the
  board is a different board, the prices are different prices, and the
  road has different people on it.

`worldsim.py` owns the readers; `quests.py` owns the board, `rpg.py` the
prices, `session.py` the road. The content it is drawn from is
`worldsim.md`'s six economy packets.

## The board (the quest outlet)

Three verbs, all authored on a card and all read at the moment the board
refills:

| verb | what it is | example |
|---|---|---|
| **post** | the card puts its OWN job up | the failed harvest posts *The Grain Road* |
| **cancel** | a negative `slots`: the town stops hiring | cold mills take two postings off |
| **reprice** | a multiplier on every posting's quoted lump | the crown's war debts pay 0.85 |

- **The band is the baseline.** A **prosperous** land posts one more job a
  settlement and pays **1.15**; a land in **crisis** posts one fewer and
  pays **0.85** — its crises post their own work back on top, so a crisis
  board is short of *ordinary* work, not of work. A settlement never drops
  below **one** posting however bad it gets.
- **A card's job is an ordinary job**: a real template, real geography, a
  real giver's face, a real epilogue, a real window. It carries the card's
  key so one board never runs two copies of it, it pays the card's own
  premium (1.10–1.35), it lapses on its own clock like anything else — and
  the card puts it back up for as long as the card stands. A card job
  never pays in **steel**: the weapon-reward mode is a flat share of the
  ordinary board.
- **The pay is stamped in at posting time**, not read out at turn-in: a job
  taken keeps the terms it was posted at, which is what makes a good week
  on somebody else's board worth walking to.

## The priced menu (the menu outlet)

Six **terms**, each a multiplier on a price the game already charges:
`goods` (potions, salve, ammo, doses), `steel` (weapons, masterwork, a
commission), `lodging`, `healer`, `toll`, `ferry`. Three sources multiply
into each, and the result is clamped to **0.5–4.0** — a bad month is
expensive, never absurd, and a price never goes to nothing:

1. **the wealth band** — crisis puts the shelf up and the beds down,
   prosperity does the reverse;
2. **the states the land holds or derives** — this is the only road a
   RELATION has to a price, and it is the point: the elves throw the
   loggers out, and a dwarven smith three lands away puts his prices up;
3. **the live cards' own terms** — the doubled toll, the ferryman's price,
   the fair's cheap week.

**The road takes its own.** A leg through a land whose terms put the toll
UP — whatever raised it: the toll squeeze, the tax farmer, a free company
on the bridges — or through a washed-out ford is charged in gold before it
is walked (small on purpose — the fords cost a *day*, and days are the
expensive currency). A purse that cannot pay walks anyway and owes
nothing: the bridge is not a wall.

## The local encounter table (the encounter outlet)

A live card, or a state the relations table derived, can put **its own
people** on the land's ground: the baron's toll-men on the bridges, loggers
holding their camp, claim-jumpers off the new workings, riders off the
border, what the fog put on its feet.

- An entry is filtered by **ground** — `road` (a travel leg) or `wilds` (a
  day afield, a night camped) — and rolled at its own chance when an
  encounter is about to happen.
- **It changes WHO, never how hard.** The level is still the road's
  party-independent roll; the deadly-but-avoidable contract and the
  notice/ambush valves are untouched.
- The roster is **reskinned, not reforged**: a Toll-Man is a cutthroat in
  the baron's livery. Display name is fiction, the stat row is mechanics.

## Chains

**A card sets a state that outlives it; the next card admits on that state
and clears it as it fires.** No new machinery — the frame's admitting
conditions already read what the last card left behind. Five ship:

| land | first card | the link it leaves | second card |
|---|---|---|---|
| Firascir | the harvest fails | bread is expensive | the bread riot |
| Mortellaria | the bank fails | forged notes are about | the note-hunters |
| Ensimaa | the rented land turns | foreigners unwelcome | the evictions |
| Dvarvengrond | a new seam is found | the seam (a slot) | the rush and the bust |
| Tergal | the herds die | the grass has not come back | the clans ride |

One more crosses a **relation**: the Gibili mills run cold because the
*elves* threw the loggers out, and `concession lost` is a derived state
like any other.

## Where the player meets it

- **On the board** — fewer or more rows, better or worse pay, and the
  land's own trouble posted as work with a name.
- **At the counter** — `prices` is the priced menu now: it prints what the
  land is charging today over the catalog sheet, and every `buy`, bed,
  healer's day and commission pays it.
- **On arrival** — one short block naming what the world did to the prices,
  printed only when it did something.
- **On the road** — the toll line before the trip, and whoever the world has
  put on that ground when the trip rolls an encounter.
- **`world`** carries all three outlets per land for the DM: the board's
  shift and pay, what each live card is posting, the priced terms, and who
  is out there.

---

# Politics & the Ruler — Add-on (2026-08-10, the worldsim build's third content rung)

The land stopped being an economy with a sky over it and became a **polity**:
who holds it, what it is fighting about, who is pulling at whom, and what
kind of person sits at the top of it. `worldsim.py` owns the frame and the
cards; `rulers.py` owns the person; `story.py` gained the war's reason.

Everything here is a **gate on content**, not a system of its own. Nothing
ticks, nothing accumulates, and no political value is ever a quantity.

## The constitution (one exclusive slot per land)

- **Rolled once at worldgen on a default-heavy die** — the wealth-band
  pattern. The stereotype is the constant (feudal humans, herding orcs,
  mining dwarves) and the variants are the colour, so the same land comes up
  a different flavour of itself across playthroughs.
- Firascir opens DECENTRALIZED FEUDALISM, Mortellaria ABSOLUTISM, Ensimaa
  CONSTITUTIONAL MONARCHY, Tergal THE CLAN CONFEDERACY, Dvarvengrond THE
  ARBITER CROWN, Gibili THE PAPER STATE. Each carries two or three variants
  — the centralizing crown, the princes in arms, the sealed realm, the great
  chief, the empty throne, the junta, the commune.
- **Cards never flip it.** The two that do say so on their face (the junta
  takes the parliament; the commune keeps the barricade), and a card that
  would only re-assert the constitution a land already holds never fires.
- It shows on `map` under the land, by name; `world` carries its sentence.

## The tensions (the deck's gate)

- Each land's packet lists **standing tensions — two named blocs and what
  they fight over**. A land **rolls ONE at worldgen, and TWO if it opened in
  CRISIS**; a tension marked STANDING is held on top of the roll and never
  rolled (Firascir's manor against its village is the econ packet's
  oppression axis, so it is simply what the land is).
- **Only cards whose tension holds enter the land's crisis deck** — the same
  deck as the econ cards, no second pile. This is the whole economy of the
  rung: a Firascir where the crown is fighting its lords never draws the
  temple's cards at all, so the packet stays a wide pool and each rolled
  world stays specific.
- A card that names no tension is land-wide and always passes: every economy
  and weather card does.

## Factions and edges (the in-land relation)

- The rolled tensions imply a small **faction cast**, and **authored
  directed verb edges** carry the wiring: the crown leans on the great
  lords, the mill barons fund the secret police, the secret police
  infiltrate the anarchist cells, the clan mothers seat the chiefs.
- **An edge is live when both its ends are in the cast** — an edge with one
  end missing is not a half-edge, it simply is not there this playthrough —
  and cards admit on it.
- A faction gets its face for free from the notables cast (`ruler` / `sage`
  / `wildcard`) where its packet names one; nothing here asks for a new NPC.

## The ruler character

Rolled at worldgen onto the land's RULER notable, in **one copy on the land
layer**; the notable carries the name and the sheet carries the words.

- **One weighted pool of 357 words** — twenty axes (two named poles around
  an unnamed neutral), one extreme step, twenty flags. A crown **draws
  THREE**; a lesser named authority a card creates draws **TWO** off the
  crown-less 355.
- **The pool shrinks between draws.** The drawn word, its axis opposite (an
  extreme takes the whole axis: a zealot *is* devout) and its never-with
  partners leave the pool, and the die shrinks by their weights — so three
  draws always land three distinct compatible words. It is exactly
  equivalent to rerolling invalid draws, and it keeps every remaining weight
  in its measured proportion.
- **The weights are measured.** 443 traited rulers out of 734 coded, average
  3 traits each — which is why three draws reproduce the per-trait marginals
  (ambitious lands on about a quarter of rolled crowns). Vivid entries the
  data zeroed sit at the **floor of 1**: rarity is priced by the weight
  column, never by deletion.
- **Neutral is silence** — an unrolled axis is never mentioned in play.
- **At most three afflictions** on one character (a combo is a story; a
  fourth is noise), and any affliction may carry a **dated origin** — "since
  the fever", "since the siege year".
- **`heart` is derived and hidden**: dark-tagged traits and no good ones →
  `dark`; good and no dark → `good`; both or neither → `mixed`. It is the
  crime layer's desert anchor and it never appears where the player can see
  it. What the town says of its king is the trait words themselves, which is
  exactly the reputation everyone in the land already has of him.
- **Two circumstances are rolled beside the words**: the mode of accession
  (inherited, elected, minority, usurped, **kin-blood** — took the throne
  over a brother's body — conquest, restored) and the **succession state**
  (secure / disputed / heirless), which reads the traits and the accession
  for free: a chaste or sickly crown trends heirless, a lecherous one
  disputed. The rest of the non-trait record (age at accession, legitimacy,
  quality of ministers, captivity) stays the DM's.
- **Ordinary NPCs stay blank.** Givers and service faces carry no sheet — the
  characteristic criterion: rulers are card-backed, givers are not.

## What a political card can do that an economic one cannot

The five outlets are unchanged. What the rung adds is four more **admitting
conditions**, each ANY-OF because each reads a slot holding one or two
values — `tension`, `constitution`, `traits` (the land ruler's rolled words),
`succession`, `edge` — and two more **state effects**: moving the
constitution slot, and moving the succession state.

A card that has to **name somebody** names him once and the land keeps him
(the fog necromancer's pattern, generalized): the banned lord, the
witch-finder, the bandit king, the pretender each roll a two-word crown-less
sheet, and the same man is still there the next time the card comes round.

## The war layer's feed

- **The casus belli.** The war had waves and no reason; now it has one,
  rolled beside story.py's aggressor off a **derived seed** (so every
  existing world's aggressor, faces and targets are untouched). It is said
  ONCE, at the first herald, and left on the land's news for whoever arrives
  later. One race needs no roll: the Sky's mandate says the neighbours are
  rebels who have not yet submitted.
- **The diplomatic instruments** — how wars end and stay ended — are
  **authored relation edges with cards standing in them**: the courtly
  hostage (a child of one hall grows up in the other), the yearly tribute,
  the marriage pact whose breaking is its own casus belli, and the personal
  union that puts two crowns on one head and both realms' quarrels at one
  table.
- **The succession cluster** admits on the crown's circumstance and moves
  it: the infant heir and its regency council, three branches and three
  readings of the law, the dead king who comes back (or the man wearing his
  face), and the bought recognition that is void the day the king dies.
  Per-land shapes ride the packets — Tergal's tanistry makes every
  succession a scramble, Dvarvengrond's electors deadlock, Ensimaa's search
  happens once an age, and Gibili has no crown to pass, so its version is
  the junta.

## Where the player meets it

- **On the map** — the land's constitution by name, under its band and its
  states.
- **In town** — what is said of the ruler, printed under his face in the
  notables block: the trait words, the succession when it is not settled,
  and the hand behind the throne when there is one.
- **On the board** — most political cards move slots or pay, because a land's
  politics is not a readout: a regency posts less ordinary work, a disputed
  succession pays over the odds for blades, a general strike takes two rows
  off the board.
- **On the news, the shelf and the road** — the same five outlets as
  everything else.
- **`world`** carries the whole polity for the DM: the constitution and its
  sentence, the tensions (standing ones marked), the live faction edges, the
  ruler's sheet including `heart`, and the faces the cards have named.

---

# Religion & Magic — Add-on (2026-08-11, the worldsim build's fourth content rung)

The last rung of the WORLD & NPC SIMULATION build. Everything here is
content over the frame the three rungs before it left: cards, relation
edges, tensions and two record kinds that had not been built yet. No new
outlet, no new tick, and no political or economic value anywhere.

`worldsim.py` owns all of it. `crime.py` gained one optional argument;
`session.py` gained two commands.

## The two record kinds that were still prose

worldsim.md opened with five. The frame and the two content rungs built the
card, the relation and the state; these are the other two, and they are the
cheap ones on purpose.

- **A FACT is the standing colour of a land**, for the DM and nobody else.
  The engine never reads one, it rides no save, and its whole surface is the
  `lore` page. The characteristic criterion applies to it exactly as it does
  to a card: every fact shipped stands behind a card, prices an option, or
  names something the player can already do.
- **An OPTION is a standing priced service** — the sixth outlet's other
  half: *player-initiated actions whose terms local state sets*. It never
  fires; it sits at a counter waiting to be bought. It carries a catalog
  price, the priced-menu **term** that moves it, and the same gates a card
  admits on (states held or derived, a rolled tension, a settlement tier).

An option does one of **three** things and there is no fourth: a
**blessing** (a paid rite: one point of satisfaction to every companion —
two for a religious one — on its own cooldown), a **book** (a wizard
teaches: the spellbook gate, opened by a land's own organization at that
land's price), or a **sky** (Tergal's rain stone). An option that needed new
machinery would be a feature request wearing a content hat.

## Temple services

Priced, not penitential — the deliberate limit of this rung:

- **Healing is the `healer` term itself.** In the two human lands the temple
  *is* the healer, so no new counter exists: the interdict already puts the
  fee up 30%, the unlicensed holy well already undercuts it by a quarter.
- **Burial and blessing are options**, sold in both Sun-communion lands off
  the same term. Beside them: Firascir's pilgrim badge, Mortellaria's
  hooded burial brotherhood, Gibili's burial club and charm trade,
  Dvarvengrond's hall blessing.
- **The sin/penance wiring is not designed and is not here.** No option
  touches sin, heat or the karma layer at all.

Ensimaa sells nothing of the kind, and that is the content: its only
religious architecture is an open-roofed marble court with no clergy, no
services and no images.

## What the packets became

- **The Sun communion is one church and two rites.** Firascir and
  Mortellaria worship the same god; each land **derives `schism-near` off
  the other's rites** through a relation edge that runs both ways, and the
  joint synod is one card sitting in *both* their decks. Every synod ends
  one insult short of the split.
- **Each land got a religion axis and a tension to hang it on**: two shrines
  and one saint, and the abbey against the families (Firascir); which face
  of the god rules the year (Mortellaria); one word in one old text
  (Ensimaa); the tomb priests against the quota (Dvarvengrond); the white
  shamans against the dark one (Tergal); the chapels against the ladder
  faiths (Gibili). The tension is the deck gate, exactly as in politics — a
  land whose shrines are at war never draws the abbey's cards at all.
- **Four more relation edges cross the border**: the southern death feast
  pulling the young elves out of Ensimaa, Gibili franchising a ladder faith
  into a Firascir market town, the old spirit-practice recognized across the
  Tergal border, and the academy's purged necromancers arriving as goblin
  street mediums.
- **Two named pools were added and no creature row**: the undead
  (skeleton/ghoul/wight) and the casters (hexer/pyromancer/magus), both off
  the catalog the game already had. The draugr and Tergal's grave-made
  ghosts still wait for the monsters & fauna dump.

## Magic: the doctrines, as data

- **THE MARGIN.** Magic is real, known and small — a gamble, not a pillar.
  Mechanically: **not one magic card moves a wealth band or a constitution**,
  and every one of them is rare or hard-gated. No throne, market or war is
  decided by it.
- **CONDUCT, NOT CREED.** There is no inquisition against casting as such
  and a caster playthrough is never dominated by automatic hostility from
  civilization. **The hunt admits only on `talent-loose`** — on what
  somebody *did* — never on a land, a ruler or a faith.
- **THE PRICE RULE.** It can't, or it costs double the mundane fix. Healing
  is retail and so is weather: the rain stone buys **two days** of rain over
  one land, never a harvest. Every epidemic, famine and drought card is safe
  from the question.
- **The gift is BORN**, and the world's answer to that is a chain that runs
  in every land: the wild talent goes off and runs (`talent-loose`), and the
  hunt that answers is the next card. The talent is **named once and kept**,
  like the fog's necromancer — recurrence is what makes an NPC exist.
- **The theory is hoarded**, and the four organizations are four prices on
  one action: the goblin master undercuts the academy, the Firascir tower
  wants a volunteer, and the elven school is the dearest teaching in the
  world and charges in standing as well as gold.

## The mark table (the reagent trade's wiring)

A third table in the shape of the priced menu and the encounter table: **a
state can put its own marks in a crime category's roll.** The reagent
consignment reaches the vault heist, the burglary, the caravan and the
smuggling deed; the opened tomb reaches grave-robbing; the stolen relic
reaches burglary and the con; carnival's masks reach the pickpocket, the
burglary and the con.

The extra faces are **dealt in beside the band's own** — a state that makes a
new kind of mark exist here does not replace the ordinary ones, it competes
with them — and the casing prints whichever came up like any other face.

## Where the player meets it

- **`service`** — the counter: what this land sells that no other does, at
  today's prices. `prices` prints the same block under the catalog sheet.
- **`lore`** — the DM's page behind a land: what is worshipped here, how
  magic works here, and what the counters are selling. Free, costs no day,
  and the engine never reads a word of it.
- **On the board, the news, the shelf and the road** — the same five outlets
  as everything else.
- **On a casing report** — a mark that is only there because of what the
  world is doing this week.
- **`world`** carries the counter and the live mark categories for the DM.
