# Roadmap

What is left to build, in order. This file is **planned features only**:
design principles (the design spine, the three currencies, tone, legibility)
live in `rules.md`; the play protocol in `dm.md`; dev conventions and current
balance numbers in `CLAUDE.md`. Anything already implemented is documented in
`rules.md` and the code, not here — when a feature ships, delete it from this
file rather than marking it done.

---

## Next up — the encounter & quest system

The game currently has exactly two hand-built sites (the bandit hideout and
the skeleton barrow), balanced by hand against a level-1-ish party. The next
big feature turns that pair into *instances of a general system* that covers
the whole game:

- **Levels as the shared difficulty language.** Player levels exist (XP,
  `100 × L` to next); give encounters and opponents levels in the same
  currency, so "a level-3 encounter" and "a level-3 party" are commensurable.
  Rough out the **whole power curve** end to end — what changes per level for
  the party (training ranks, proficiency, gear tiers) and for the opposition
  (stats, numbers, abilities) — even if most of it ships as tables and
  guidance before it ships as code.
- **A monster/opponent catalog spanning the full range.** Humanoids span any
  level; monsters and animals get **level ranges** that make each kind
  distinct (the lopsidedness principle from `rules.md`: each monster is a
  puzzle defined by its hole; bosses by the lack of one). The catalog should
  cover the curve from a goblin to a dragon with no dead zones — every band
  of levels has things to fight that feel different from the last band.
- **DM tools for authoring opponents and dungeons.** Given a target level and
  a narrative brief ("a wolf-den for a level-2 party", "a cursed chapel,
  tough side of fair"), the DM should be able to generate or assemble foes,
  rooms, and rewards *without hand-tuning against the sims each time* —
  the system encodes what the two hand-built sites taught us about pacing
  (set encounters, room counts, attrition budget, reward scale).
- **Quests as the frame.** The player picks work at a level and risk of their
  choosing — usually a choice of easier vs harder quests — with gold/XP
  rewards scaled by the encounter system, so "which fight do I take" stays
  the core between-fights decision as the game grows past two sites.

**Test criteria:** "N foes of level L" maps to a predictable difficulty the
player can learn to *feel*; a DM-assembled dungeon at level L lands in the
intended clear-rate band without bespoke tuning; advancement against a fixed
benchmark stays a noticeable jump (the `bench_training.py` criterion,
generalized).

Everything below waits until this exists — magic, armor, and guns all need
the level/power curve to hang their numbers on.

---

## After that (in rough order)

1. **Magic & INT** — magic skills, INT scaling/gating (the way STR scales
   weapons), the stat-transcendence path (magic is the membrane that lets
   gamey effects into the simulated body). Test: an INT build is viable;
   magic feels like the sanctioned rule-breaker.
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
5. **Party composition & the CHA layer** — parties of 2–4 built so builds
   cover each other's weak matchups; recruitment; richer companion mechanics
   (currently the PC/companion split is run by DM protocol alone). CHA
   itself is underdefined — detail deferred until this layer is next up.

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
- **Survival/adventure-sim pivot** (hunger, upkeep, inventory) — a deliberate
  possible future pivot away from the heroic tone, not drift.
- **Power potion re-stock** — retired 2026-07; re-circulate the kind if
  War-Breath ever makes Power genuinely scarce in play.

---

## Open questions

- **Armor:** adopt, simplify, or defer (see above) — the least-developed
  system.
- **Can stats ever be raised?** The design spine (`rules.md`) says stats are
  fixed at creation and only magic/items transcend them; older notes also
  mention "raising stats toward an archetype" as a between-fights choice.
  Unresolved — decide when the encounter system makes the power curve
  concrete.
- **CHA / party mechanics** — underdefined by design; detail when that layer
  is next up.
- Every constant is provisional and sim-tuned, never hand-designed — the
  current numbers live in `CLAUDE.md` ("Balance / tuning").
