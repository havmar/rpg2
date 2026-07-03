# Combat Sim — Minimal Ruleset

A combat simulator for a fantasy RPG. Fights resolve on their own; the player's
decisions happen *between* fights. Three stats, one wound track, one loop.

---

## Design goals (the "why", independent of any implementation)

**1. Autobattler, not a combat minigame.** A fight takes no input once it starts.
The simulation produces an outcome (who won, in what shape) and a narrative log.
All player agency lives *between* fights.

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
log narrates well.

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
| **STA** | A pool that drains each round. When low, you're **Winded**. The clock. |
| **HP**  | Wound pool. Damage is taken *as* HP loss, and lost HP is a penalty to your rolls (see Wounds). |

---

## The round loop

Each round, both fighters resolve one exchange:

1. **Tempo roll.** Each rolls `2d6 + DEX − (HP lost so far) − (2 if Winded)`.
2. **Who lands.** Higher total connects this round. `margin` = the difference.
   (A tie is a clash — no one lands.)
3. **Severity.** `severity = margin + attacker STR − defender STR`.
4. **Wound.** Map severity to a tier; the defender loses that much HP.
5. **Drain.** Both fighters lose STA (more for higher-STR fighters — big frames
   burn fuel faster). At **STA ≤ 3**, a fighter is **Winded**.
6. Repeat until someone reaches **0 HP** (dead/defeated) or yields.

### Wound tiers

| Severity | Tier | HP lost |
|----------|------|---------|
| ≤ 0 | Deflected | 0 |
| 1–2 | Graze | 1 |
| 3–4 | Wound | 2 |
| 5–6 | Grievous | 4 |
| 7+  | Killing blow | 6 |

**The death spiral is the whole point.** Your roll penalty equals the HP you've
lost, so the first solid hit tilts every later round against you and the fight
accelerates to a conclusion. There is no slow attrition to zero — one grievous
hit can decide it.

---

## Why three stats produce the loop (no range needed)

- A **Power** build lands rarely (low DEX) but devastatingly, and is durable —
  but burns STA fast, so it must win early.
- A **Precision** build lands often but softly, and is fragile — it wins by
  chipping and evading over time.
- An **Endurance** build is middling but stays sharp longest — it survives the
  Power build's burst and outlasts it, but can't catch or out-chip the Precision
  build.

Because you must *land* to deal damage, DEX gates STR for free (the old "range/
bind" mechanic, removed). Because STA degrades fighters over time, *when* you're
dangerous matters. Those two facts alone make the matchups rock-paper-scissors.

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
STA `randint(4, 7)` (floor raised a step above the two so no hero starts the
day already Winded at STA <= 3), HP `randint(8, 12)`, Power `randint(3, 6)`, a
random ability (Heal or Bulwark), and two random potions. A hero's epithet
("the precise" / "the powerful" / "the steady") is derived from their highest
stat.

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
- **Equip gear** that shifts stats, soaks severity, or adds STA.
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
- **New round step — Regen.** After the drain step, if a healing potion was
  prepped, the drinker regains its per-round HP.
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
- **Two buffer layers, cleanly split.** *In advance* (items, prepped before a
  fight — too slow to use mid-fight) and *in the moment* (abilities paid in
  Power — fast enough to fire during an exchange). Flavor-true rule: **magic and
  trained skill are reflexive; rummaging in a pouch is not.**

---

## Resources at a glance

| Resource | Scope | Refillable? | Role |
|----------|-------|-------------|------|
| **HP** | Carries across the run (never a per-fight reset) | Trickle via short rest / prepped potion; the real heal is a **long rest** — HP returns over **~a week** | Lethal death-spiral inside a fight; a lasting wound between them. |
| **STA** | Per day | Small catch-breath per short rest; rare/costly potions; **fully recharges on a long rest (overnight)** | The **involuntary clock**. Drives the matchup loop. Stays expensive to buy back mid-day on purpose. |
| **Power** | Per day | Rest, gold, world drops | The **spendable budget** for abilities, heals, and the warrior's absorb. Fast — usable mid-fight. |
| **Items** | Carried stock | Bought with gold, found in world | The *in-advance* buffer: prepped before a fight, or used after. |

Give each character their **own** Power and item stock, not a shared pool — it
keeps build identity alive and makes "who am I about to lose" specific.

---

## The two-buffer split

**In advance (items — slow, prepped):**
- **Healing potion** — drunk *before* a fight grants HP regen each round (e.g.
  +1 HP/round, capped) for that fight; or drunk *after* to restore HP directly.
  **Cannot** be used mid-fight — no time in an exchange this fast.
- **Stamina draught** — restores STA. Deliberately **rare and expensive**,
  because STA is the un-buyable clock; cheap refills would collapse the matchup
  loop. STA otherwise recovers only slowly across a day.
- **Power potion** — restores Power. More freely available than stamina.

**In the moment (abilities — fast, cost Power):**
- **Heal** — spend Power to restore HP or reduce an incoming wound one tier on
  the round it lands. Common among adventurers.
- **Warrior's Bulwark (grievous-absorb)** — *active*: when a Grievous or Killing
  blow lands, spend Power to reduce it one tier (Killing -> Grievous, Grievous ->
  Wound). The martial mirror of a heal, so non-casters also get an in-the-moment
  save — and it can run out, which is the point.
- Other class skills are likewise paid in Power.

---

## STA vs Power — keep them distinct

STA is your **condition** — it drains whether you want it to or not, and it
creates the fade that powers the matchup triangle. Power is your **budget** — you
*choose* to spend it. Keeping them separate makes the warrior's Bulwark a real
trade (skill budget spent to live) and keeps a stamina potion a rare cheat rather
than a routine top-up.

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
  resource — a handful of slots per day. It gives only a small catch-breath (a
  little STA, a sliver of HP) plus deliberate potion use. When the slots run out
  there is no more mid-day recovery: the party pushes on depleted or makes camp.
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

- **Buy and prep consumables** — pre-load a healing potion for regen, carry a
  rare stamina draught for the long fight, keep Power potions in reserve.
- **Spend Power deliberately** — it's offense-or-survival; every save is a skill
  not used.
- **Manage the run** — conserve resources against matchups you counter; expect to
  hemorrhage them against your counters; rest when the stockpile is dry.

---

## Implementation notes (how `rpg.py` realizes this)

- **Time is a `Clock`** (a `day` counter plus a per-day budget of short-rest
  slots, `SHORT_RESTS_PER_DAY`). A dungeon run is a slice of a day. **HP and STA
  both carry across rooms** (drain, never a per-fight reset); a `short_rest`
  spends a slot for a small catch-breath, and `long_rest` makes camp for the full
  STA recharge + the weekly HP tick (`hp_regen_per_night = max(1, round(max_hp /
  7))`). Power and items are per-day stocks that deplete across the run.
- **No auto-night.** `long_rest` is called deliberately (by the DM), never by the
  dungeon loop — the day ends when the player chooses to camp, not on a timer.
- **Saves are automatic and conservative.** A character spends Power to buy off a
  *killing* blow whenever it can (Killing -> Grievous), and to buy off a
  *grievous* that would put it Down only when it can keep a reserve. Both the raw
  and the bought-down result are logged.
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
  - Skeleton site: **15 XP** per encounter, **55 XP** for the quest — a full
    clear (3 rooms) is exactly 100 XP, so the *first clear is a level-up*; the
    second level takes two clears, the third takes three.
  - The bandit hideout pays **3×** (45 / 165) — tough fights, better wages.
- **Level-ups grant skill points** (1 per level), spent on skills — free
  allocation, never use-based (the Fallout principle from the design record).

## Combat training — the general fighting skill

The veteran-vs-novice axis: *"you know how to fight."*

- **Effect:** +1 to **all tempo rolls** per rank. Because severity = margin +
  STR difference, training quietly improves *everything*: you land more, get
  hit less, and the hits you land cut deeper. One number, three effects — which
  is why it stays cheap-per-rank but caps hard.
- **Cost:** rank *n* costs *n* skill points; **cap: rank 5**. With 1 point per
  level: rank 1 at level 2, rank 2 at level 4, rank 3 at level 7, rank 4 at
  level 11, rank 5 at level 16. Cheap to start, expensive to max.
- It is the **only skill for now**, so the scenarios auto-spend points on it;
  once more skills exist, spending becomes a real between-fights choice.
- **Benchmarked** (`bench_training.py`, 5k trials/rank): the bandit hideout
  wipes a rank-0 party ~78% of the time, rank 1 → ~50%, rank 2 → ~23%,
  rank 3 → ~6%. Each rank is a *felt* jump — Phase 3's test criterion.

## Gold and the potion economy

- **The purse is shared** (party-level); potions are per-hero.
- **Income:**
  - **Quests:** skeleton site **15 g**, bandit hideout **45 g**.
  - **Drops**, per encounter won: **20%** chance of loose coin (**5 g**, half a
    potion) and **10%** chance of a stray potion (random kind, to a random
    hero). Trash-tier on purpose — drops season the run, quests fund it.
- **Sink:** any potion costs **10 g**. `buy_potion` is a deliberate,
  DM-called, between-adventures purchase — nothing in the engine buys or
  refills automatically. A quest reward is worth 1–2 potions (the hideout, 4+).
- **Starting stock:** two *random* potions at creation. That's the whole kit;
  from then on the stock only moves through drops, purchases, and use.
