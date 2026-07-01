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
found/quested, not shopped.

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
- **Weapon proficiency** — per-individual-weapon (only five exist, so no need for
  classes). Stacks on top of general competence. Switching to an unfamiliar
  weapon keeps your general skill but drops the proficiency layer — that loss is
  the commitment cost that makes a build a build.
- Skills may include niche/non-combat ones (e.g. explosives, lore) for character
  identity.

### Weapons — build expression, not a power ladder

Each weapon weights the three combat stats *differently*, so a weapon is *suited
or unsuited to a build*, never simply better. Knobs (all from the existing
system):

- **Tempo weighting** — DEX-favouring (rapier) vs STR-contributing (greatsword).
- **Severity profile** — flat bonus vs STR-scaling.
- **STA cost per swing** — heavy weapons burn the clock faster (a burst weapon
  *mechanically*, wanting a high-STA frame behind it).
- **Reach** — survives as a small first-exchange modifier even though range isn't
  tracked.

**Shortlist (taste-curated; no spears/shields/axes):**

| Weapon | Likely identity |
|--------|-----------------|
| Wooden staff | INT/caster weapon — bridges martial and magic. |
| Greatsword | STR burst — high severity, high STA cost. |
| Rapier | DEX precision — tempo-favouring, low severity. |
| Katana | Balanced/finesse — the all-rounder. |
| Dungeonpunk guns | Ranged; consumes **ammo** (gold sink, balancing lever). |

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
un-buyable clock; **Power** as the spendable mid-fight budget (heals, the warrior's
Bulwark); potions as the in-advance buffer; **Down-not-dead** (0 HP is out of the
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
Down-not-dead; total-party-knockout = defeat; Power + abilities (Heal, Bulwark);
potions (prepped regen, rare stamina draught); averted-death log.
Test: a well-stocked party reliably *survives a single fight*; deaths require the
saves to be dry.

**Phase 2 — Day / run economy** *(built — `rpg.py`; disengage/retreat still open)*
Build: STA + Power + item carryover across encounters; rest events; the
disengage/retreat hook *(not yet — belongs to the AI DM layer)*.
Test: a run of fights produces a visible grind-down; the stockpile depletion is
felt; a too-hard run forces retreat.

**Phase 3 — Progression**
Build: XP, levels, free skill + proficiency allocation; stats stay fixed.
Test: against a fixed enemy benchmark, a level-up makes the outcome *noticeably*
better — quantify the jump.

**Phase 4 — Weapons & proficiency**
Build: the five weapons with distinct tempo/severity/STA profiles; per-weapon
proficiency; guns + ammo.
Test: each weapon is build-*suited* rather than ranked (no single best); the
proficiency switching cost is real.

**Phase 5 — Loot & items**
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

## Part 4 — Open / deferred

- **Decisions to confirm** (this plan assumes the recommended answer; flip freely):
  currency split as above; INT/CHA fixed at creation; per-weapon proficiency;
  guns use ammo; armor = tier-shift.
- **Charisma / party mechanics** — underdefined; detail deferred until the
  combat + progression spine runs.
- **Untested numbers** — every constant (Power totals, regen rate, STA threshold,
  severity breakpoints, level curve) is provisional and tuned via batch sims, not
  hand-designed.
