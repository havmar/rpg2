# Design Record & Implementation Plan

Working design doc for the combat RPG (no name yet — formerly "duel sim," which
no longer fits now that it's party + campaign). The companion documents are the
**core combat ruleset** and the **survival & resources add-on**; this file is the
high-concept record and the build roadmap that sits above them.

---

## Part 1 — Design spine

### The one principle

**Simulate inside the fight; go gamey between fights.** Magic is the membrane
that lets gamey effects reach into the simulated body.

Decision rule for any future "realistic or gamey?" question: *does it happen
during the fight or around it?* During → lean simulation. Around → lean game.

### The three currencies (non-overlapping on purpose)

| Currency | Source | Buys | Never buys |
|----------|--------|------|------------|
| **XP / Levels** | Winning encounters | Permanent ability: skills, weapon proficiencies (free allocation) | Stats |
| **Gold** | Loot, quests, selling trash | Staying power: consumables, ammo, trash gear, rest/services | Permanent combat ability; Named weapons |
| **Loot & Quests** | Authored rewards | Power spikes: the cool/Named weapons, stat-transcending items | (n/a) |

The rule that keeps the economy from going flat: **gold buys staying power, not
power.** Permanent ability is XP-only; meaningful weapons and stat boosts are
found/quested, not shopped. *Softened by decision (2026-07): this is a
guideline, not a law — the real intent is just that XP and gold shouldn't feel
like the same currency. Plain-tier quality weapons may be shopped for gold;
masterwork/legendary stay found/quested.*

### Stats — five, all fixed at creation

Stats are the *simulated body* (and mind): set at character creation, **not**
raised by levelling. A genetic cap defines each stat's ceiling; this is also
where the human / hero / monster ranges live. Only **magic and rare items** can
push a stat past its natural value — the membrane in action.

| Stat | Layer | Role |
|------|-------|------|
| **STR** | Combat | Wound severity; soaks incoming wounds; scales heavy weapons. |
| **DEX** | Combat | Lands/avoids hits; the tempo roll; scales light weapons. |
| **STA** | Combat | The involuntary clock; drives the burst/sustain matchup loop. |
| **INT** | Magic | Scales/gates magic, the way STR scales weapons. |
| **CHA** | Meta/party | Companions, recruitment, the disengage/rest/quest layer. Never acts inside a fight. |

### Tone — heroic, not gritty (for now)

The current vision is **heroic adventure**, not survival realism: like Lord of
the Rings, you travel with a backpack and no bookkeeping. Concretely ruled out
for now: inventory management, hunger, disease, lifestyle upkeep costs, weapon
maintenance meters. (This may change later — survival/adventure simulation
could suit the format — but it is a deliberate future pivot, not drift.)
Weapons carry a combined weight/bulk property that is *stored but inert*; if
carrying ever matters, it becomes a natural secondary role for STR.

The same tone permits **wacky, non-serious mechanics** once the basics are
solid (e.g. a magic sword that generates gold by killing). The mechanics
should be sturdy first, but the game is not oh-so-serious about its own
economy rules — see the note under the currency table.

### Legibility — a core design challenge

Most of the mechanics are invisible at the table: the player experiences the
game through chat narration, not character sheets. This cuts two ways:

- **Prefer mechanics whose fiction is self-explaining.** A weapon snapping
  mid-fight is instantly understood and narratable; an invisible +1 is not.
  When choosing between two designs of equal depth, take the one a spectator
  could follow. (This is what motivates weapon durability/breakage.)
- **Logging and DM display rules help but don't solve it.** Later: explicit
  instructions for the DM on which stats/log excerpts to copy directly into
  chat so the player can see the state that matters.
- **Future mechanics chosen for legibility:** enemy morale and surrender;
  recruiting defeated/met NPCs into the party; characters with flaws, needs,
  and personalities rolled from spark tables. All parked, not designed.

### Progression — free allocation, never use-based

Levels grant points to spend on **skills** and **weapon proficiencies**, à la
Fallout — *what you are*, not *what you've done*. No Elder-Scrolls use-based
grinding. A character can be the explosives specialist whose skill rarely comes
up; that's identity, and it's valued for flavour, not frequency.

---

## Part 2 — Systems

### Skills & proficiencies

Two stacked layers (the "trained combatant vs trained in a weapon" split from the
opening of the brainstorm):

- **General competence** — broad fighting/magic skills; a flat bonus that says
  "you know how to do this at all." The veteran-vs-conscript axis.
- **Weapon proficiency** *(built)* — per weapon **type** (rapier ranks apply to
  any rapier; no weapon classes needed). Stacks on top of general competence.
  Switching to an unfamiliar weapon keeps your general skill but drops the
  proficiency layer — that loss is the commitment cost that makes a build a
  build.
- Skills may include niche/non-combat ones (e.g. explosives, lore) for character
  identity.

### Weapons — build expression, not a power ladder *(first slice built)*

Each weapon weights the three combat stats *differently*, so a weapon is *suited
or unsuited to a build*, never simply better. The shipped knobs (see rules.md
"Weapons" for the full spec): **attack tempo** (the rapier), **flat severity**
(the zweihander), **defense tempo** (staff +1, zweihander −1), **durability**
(breakage — see below), plus flavor fields (`bulk` inert, `tags`, `value`,
`description`).

Two planned knobs changed on contact with the sims:

- **STA cost per swing** — the intended heavy-weapon burst mechanic — is
  **sim-rejected for now**: with Spent lethal, halving the swing budget loses
  more than any severity bonus buys back (every 2-STA zweihander variant was
  strictly worst-in-class, `bench_weapons.py`). The schema keeps the knob at 1
  for a future with deeper STA pools; the zweihander's burst identity ships as
  the guard penalty instead.
- **Reach** (a small first-exchange modifier) — still unbuilt, parked.

**The quality four (taste-curated; no spears/shields/axes):** rapier (+2 atk,
−1 sev, graze floor — a landed thrust always draws blood), katana (+1/+1, the
all-rounder), zweihander (+1/+3, −1 defense, the crowd-breaker), wooden staff
(healer's weapon: +1 parry, +1 HP per Heal, poor steel on purpose). Commons
(the "uncool" list) collapse to three lines: crude 0/−1 (durability 1),
soldier's arms 0/0, heavy arms 0/+1. **Durability & breakage** shipped: on a
parry or Clash the lower-durability weapon can shatter (0.25% × gap² per
contact — a club vs legendary steel snaps in ~24% of fights, quality vs better
~1%); broken = −2 atk/−2 sev until re-armed. Craftsmanship tiers:
plain (unlabeled in play) / masterwork / legendary — only plain is shoppable.

**Dungeonpunk guns** (ranged; consume **ammo** as a gold sink) — deliberately
excluded from the first slice; a later phase.

### Loot — weapons as narrative elements, not realistic drops

Reject both realistic loot (looting a pile of orcish axes) and Diablo-style
independent drops. Two tiers instead:

- **Trash / starter** — trivial to acquire; includes any "uncool" or realistic
  looted weapon (the guard's halberd *is* lootable — it just has poor stats).
  Functional, forgettable.
- **Named** — a big deal. Better stats, often stat-transcending, and carrying
  authored provenance: made by a famous smith, wielded by a famous foe, lost in a
  mythic dungeon. These are characters/story beats, not drops.

### Armor — provisional (least-developed system)

Standing proposal: armor **shifts the incoming wound tier down** (Grievous→Wound,
etc.) at the cost of a **DEX penalty** and **higher STA drain** — speed and clock
traded for protection. Heavy armor pushing most hits to Graze/Deflected is what
turns a fight toward the attrition/contact game. Optional anti-armor weapons could
ignore the tier-shift (gear-counters-gear on top of build-counters-build).
*Status: adopt, simplify, or defer.*

### Survival & resources (already built — see add-on)

HP **carries across the whole run** (drains like STA, only a minimal catch-breath
between rooms — never a per-fight reset), with the death spiral intact; STA as the
un-buyable clock **and second death-track** (0 STA mid-fight = Spent: still
swinging but −6 to every roll, no recovery until the fight ends — running dry
near a fresh enemy is usually fatal, while two spent sides brawl to a real
finish so fights resolve); **Power** as the spendable mid-fight budget (heals,
the warrior's Bulwark); potions as the in-advance buffer; **Down-not-dead** (0 HP is out of the
fight, revived minimally next room); death only when a killing blow lands and the
saves have run dry. **A total party knockout — no hero left standing — is a
defeat: the fallen are finished off (game over).** Narrate the averted death. This
is the layer that converts the lethal core into a gradual, legible "you're losing"
signal.

### Encounter & meta layer

- Party of **2–4**, shared stat framework.
- An encounter = the party vs a **group**. After a fight, a choice to
  **disengage / rest / retreat** before the next, arbitrated by the **AI DM**
  (is there time to rest, room to retreat?).
- Usually a choice of **easier vs harder** quests.
- **Difficulty is level-based.** Humanoids span any level; monsters and animals
  get **level ranges** that make each kind distinct.
- Design goal: the player should develop a *feel* for how dangerous N enemies of
  level L are, and advancement against that benchmark should feel **noticeable**.

### Architecture: two layers

- **Deterministic combat engine** (the script): resolves fights, tracks HP/STA/
  Power/wounds, emits a mechanical log.
- **AI DM orchestration**: encounter framing, quest/rest/retreat choices,
  narration over the log, the CHA/party layer.

---

## Part 3 — Implementation roadmap (features to add & test)

Each phase names what to build and what to *observe in batch sims*, since the
autobattler is the test harness.

**Phase 0 — Core combat** *(built — `rpg.py`)*
Build: STR/DEX/STA, tempo roll, wound tiers, death spiral, STA clock.
Test: a fight resolves to win/lose; the burst/sustain/control loop is visible
when archetypes meet (run the rock-paper-scissors matrix).

**Phase 1 — Survival layer** *(built — `rpg.py`)*
Build: HP carries across the run (death spiral, not a per-fight reset);
Down-not-dead; total-party-knockout = defeat; Power + abilities (Heal, Bulwark,
First Blood); potions (instant HP/STA/Power top-ups, rare stamina draught);
averted-death log.
Test: a well-stocked party reliably *survives a single fight*; deaths require the
saves to be dry.

**Phase 2 — Day / run economy** *(built — `rpg.py`)*
Build: STA + Power + item carryover across encounters; rest events; a **time
`Clock`** (day counter + short-rest slots). Two rest tiers: `short_rest` (a
limited within-day slot, small catch-breath) and `long_rest` (overnight — full
STA, HP knit back over ~a week at a per-character rate, day advances). **No
auto-night: `long_rest` is a deliberate call, never fired by the loop** — the
timing choice is the player's, preserving TTRPG freedom. The disengage/retreat
hook: *built 2026-07 as Part 3b's Arc B* (the pause primitive + retreat &
chase + encounter persistence).
Test: a run of fights produces a visible grind-down; the stockpile depletion is
felt; wounds linger across days until a week of rest clears them; a too-hard run
forces retreat.

**Phase 3 — Progression** *(first slice built — `rpg.py`)*
Build: XP (per encounter + quest lump), levels (`100 × L` to next), skill
points, and **general combat training** (+1 tempo/rank, rank *n* costs *n*
points, cap 5) — the one skill so far; stats stay fixed. Weapon proficiencies
remain Phase 4; with a single skill the allocation is auto-spent for now.
Test: *passed* — against the skeleton-barrow benchmark (`bench_training.py`;
the barrow is the tough site since the Spent rework swapped the two),
clear rate climbs 15% → 42% → 71% → 90% across training ranks 0–3 (numbers
as of the 2026-07 graze-floor/dying-swing round). Each rank is a felt jump:
training ends fights in fewer swings, which is what stretches the (now
lethal) STA budget.

**Phase 4 — Weapons & proficiency** *(first slice built — `rpg.py`; guns deferred)*
Build: the quality four with distinct tempo/severity/defense profiles + the
common-weapon table (14 named commons in three stat lines) + durability/
breakage + per-weapon-type proficiency (+1 atk tempo & +1 severity per rank,
rank *n* costs *n*, cap 3 — making skill points a real choice vs combat
training; nothing auto-spends in session play anymore). Guns + ammo: deferred
to a later phase.
Test: *passed* (`bench_weapons.py`) — suited, not ranked: the rapier is the
best duelist on nearly every frame, the zweihander sweeps every swarm cell,
the katana is the reliable second everywhere, the staff trails on purpose; no
weapon tops every cell. Gear is a felt jump (`tune`-style check, post-2026-07
numbers: katana + zweihander lift a fresh party's barrow clear from ~15% to
~45%, worth ~1 training rank). The proficiency switching cost is structural
(per weapon type). Note: the planned 2-STA heavy swing was sim-rejected — see
the weapons section above.

**Phase 5 — Loot & items** *(trash-tier slice built: gold/potion encounter
drops + a quest-gold + potion-shop economy, and potion *use* is now a
between-fights player choice (`use_potion`), not auto-fired — see rules.md
"Progression & Economy")*
Build: Trash vs Named items; provenance metadata; stat-transcendence on rare
items.
Test: Named weapons read as events; trash is appropriately trivial; no power
inflation from common drops.

**Phase 6 — Magic & INT**
Build: magic skills, INT scaling, the stat-transcendence path.
Test: an INT build is viable; magic feels like the sanctioned rule-breaker.

**Phase 7 — Armor** *(provisional)*
Build: tier-shift + DEX/STA cost; optional anti-armor weapons.
Test: heavy armor changes a fight's *character* (pushes to attrition/contact);
the speed-vs-protection trade is a real choice, not a strict upgrade.

**Phase 8 — Encounter & difficulty model**
Build: enemy level ranges per creature type; an encounter power curve (party
level/comp vs enemy level/count); easier/harder quest framing.
Test: "N enemies of level L" maps to a predictable difficulty; the curve is
legible enough to *learn*.

**Phase 9 — AI DM integration**
Build: narration over the deterministic log; encounter framing; choice prompts;
the CHA/party layer.
Test: the prose layer is flavour-only and never alters mechanical outcomes.

---

## Part 3b — Next design arcs (agreed 2026-07, from the first playtest)

The first full playthrough (hideout clear, then a rank-1 barrow wipe) produced
a batch of decisions. What shipped immediately: the **universal graze floor**
(win an exchange by margin 3+ and the hit always at least grazes — before
this, a fresh high-soak hero literally could not be injured until his stamina
collapsed, so HP was dead weight), the **dying swing** (everyone alive at
round start gets their attack, even if felled before their turn — killing a
foe no longer cancels the blow it was already delivering), the **power potion
retired** from circulation (Power is never the bottleneck), and the session
UX round (status shows every track cur/max + XP/points, a `levelup` spending
menu, a `Left among the dead:` loot line after each clear).

The arcs below are agreed direction, in order — **B and C are now built**
(2026-07). A standing tuning principle came out of the same session: **the
sims understate the player** — batch policies rest on schedule and drink on
crude thresholds, while a real player paces rests and reads the STA math
before every door — so harsher sim numbers than "feels fair" are acceptable,
and the early rooms of a site should threaten in the sims too, not just the
last one.

### Arc A — Lethality & feel (in progress; test in play before more knobs)

- **Graze floor: shipped** (above). Effect on the numbers: barrow rank-0
  clear 21% → 15%, hideout rank-0 wipe 14% → 18%, quality-steel gear check
  62% → 45%. The party now bleeds *before* the stamina track collapses.
- **d12 experiment: postponed** until the graze floor has been felt in play.
  The flat die is the bigger hammer (more upsets both ways) but weakens every
  modifier relative to noise — don't fork the variance dial while another
  lethality change is still settling.
- **Asymmetric Spent: waiting, same reason.** The candidate design if
  spent-vs-fresh grinds still feel wrong after A+B land: keep the full −6 on
  defense but soften the attack penalty (−3, "desperation swings") — a spent
  fighter gets carved faster *and* stays dangerous, so those fights end
  sooner from both directions. Note the current system already resolves
  spent-vs-spent (the −6s cancel in the opposed roll); the pathology is
  specifically spent-vs-fresh-tireless, and Arc B's retreat dissolves most
  of it (the player exits at 2 STA instead of ever going Spent).
- **Encounter retune** afterward, with the harsher-sims principle applied.

### Arc B — The interrupt primitive: mid-fight potions, retreat, chase *(built 2026-07)*

One engine change carries the whole arc: `group_combat` **pauses at a trigger
and resumes** (`pause_triggers=True` returns a `Pause`; re-call with the same
`fired` set to continue), with the paused fight serialized into the session
save. In chat it is exactly two messages: message 1 = the fight up to the
pause + the DM's question; message 2 = `resume ...` (or `retreat`) to
conclusion. As-built decisions:

- **Triggers as designed:** a hero at STA ≤ 2 or HP ≤ 50%, checked at round
  end, each at most once per fight. A hero *entering* a fight already low
  trips it at the end of round 1 — the drink decision is real there too.
- **Drink shipped as a pause action** (stamina draught only; healing waits
  for proven HP pressure): costs that round's attack, defends at −2 while
  drinking. One pause action per hero per pause. It even un-Spends a fighter
  at 0 — the deliberate exception to "no in-fight STA recovery."
- **Retreat as designed:** parting blows from every foe fit to swing (free,
  like the dying swing), fled at −2; then ONE group contest, 2d6 +
  STA-weighted side-average DEX, the fleeing side at +`FLEE_BONUS` (2). A
  summed threat score / multi-round chase can still layer on later if the
  single contest feels thin.
- **The undead don't pursue** (`pursues=False` on the skeletons): they swing
  at the door, then stop. Retreat from the barrow always succeeds once past
  it — "come back tomorrow and finish it" is a real plan.
- **Encounter persistence shipped:** per-room survivor records (day-stamped)
  in the session save; foe STA refills on the party leaving, living foes
  heal over a day, skeletons stay hacked. `session.py` grew `resume`
  (`--drink/--berserk/--warbreath HERO`) and `retreat`, blocks between-fights
  commands mid-pause, and shows unfinished rooms in `status`.
- **The honest cost, measured:** the sims got a matching pause policy
  (`sim_pause_policy`: drink/convert/retreat on crude thresholds, one return
  trip per fled room) so tune/bench keep describing play. Effect at rank 0:
  barrow clear 15% → ~22% (wipes 85% → ~75%, ~14% of runs retreat at least
  once), hideout wipe ~18% → ~10%. Softer, as predicted — and within the
  "sims understate the player" allowance; watch it in play before touching
  the encounter levers.

### Arc C — Resource-conversion abilities *(built 2026-07; numbers provisional)*

Stamina is the scarce, dynamic track; HP and Power mostly sit idle. Both
conversions shipped as pause-menu actions with the drink's exact shape (the
round's attack + −2 guard), open to every hero for now:

- **Berserk** — 2 HP -> +4 STA. The HP loss deepens the wound spiral on the
  spot, which is the real price. Warrior-flavored; tying it to the
  zweihander (the weapon-granted-ability hook) stays a parked idea.
- **War-Breath** — 2 Power -> +3 STA. A fighter's/monk's breath discipline,
  explicitly *not* wizardry; the staff-fighting monk archetype is the
  natural carrier when abilities get assigned.

Both give Power/HP live mid-fight roles — the better fix for Power feeling
inert than any potion. If War-Breath makes Power genuinely scarce, the
retired power potion can circulate again (rules.md, two-buffer split).

### Parked from the same session

- **Auto-drink thresholds for healing potions** (e.g. at 30–50% HP) — blocked
  on HP pressure actually existing in play (Arc A first), and it must be
  statistically worth it before it's a default.
- **Morale / surrender** interacting with retreat and chase — the existing
  parked idea, now with a concrete attachment point (Arc B's pursuit logic).

---

## Part 4 — Open / deferred

- **Decisions to confirm** (this plan assumes the recommended answer; flip freely):
  currency split as above; INT/CHA fixed at creation; per-weapon proficiency;
  guns use ammo; armor = tier-shift.
- **Charisma / party mechanics** — underdefined; detail deferred until the
  combat + progression spine runs.
- **Untested numbers** — every constant (Power totals, potion restore, STA threshold,
  severity breakpoints, level curve) is provisional and tuned via batch sims, not
  hand-designed.
- **Weapon ideas deferred from the Phase 4 design round (2026-07):**
  - *Level requirements on masterwork/legendary weapons* — rejected for now:
    authored placement by the DM already gates when they appear; a hard level
    lock is redundant bookkeeping. Revisit only if strong gear leaks to
    low-level parties in practice.
  - *Per-weapon tempo dice* (e.g. a weapon rolling 1d12 instead of 2d6 for a
    swingier profile) — fun, but 2d6 is deliberately the single global
    variance dial; don't fork it before the numbers earn trust.
  - *Rapier anti-soak floor* — **shipped** in the first slice (the
    `graze_floor` flag): it turned out to be exactly what the rapier needed
    to reward the low-STR precise frame instead of merely patching clumsy ones.
  - *Guns + ammo* — explicitly out of the first weapons slice; moved to a
    later phase.
  - *Weapon reach* (a small first-exchange modifier) — parked, unbuilt.
  - *The 2-STA heavy swing* — sim-rejected while Spent is lethal; revisit if
    STA pools ever deepen (the `sta_cost` knob remains in the Weapon schema).
- **Legibility-driven mechanics parked** (see the design-spine section):
  enemy morale/surrender, recruitment, spark-table personalities/flaws/needs,
  DM display rules for surfacing stats in chat.
