# Roadmap

What is left to build, in order. This file is **planned features only**:
design principles (the design spine, the three currencies, tone, legibility)
live in `rules.md`; the play protocol in `dm.md`; dev conventions and current
balance numbers in `CLAUDE.md`. Anything already implemented is documented in
`rules.md` and the code, not here — when a feature ships, delete it from this
file rather than marking it done.

---

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

**A career finding to design against** (bench_quests, 2026-07-08): under sim
policy a full 1-20 career is roguelike-lethal — L5 46% / L11 14% / L20 ~0%,
half the deaths at the rank-0 front door, and past ~L13 outleveling content
stops working because the party saturates (skills capped, pools only) while
the bestiary keeps climbing. The top band's missing player power is exactly
the next systems below: masterwork gear, armor, magic. Decide eventually:
is a playthrough a roguelike run (death = new party, the world persists) or
should the curve soften?

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
5. **Party composition & the CHA layer** — parties of 1–4 built so builds
   cover each other's weak matchups; recruitment; richer companion mechanics
   (currently the PC/companion split is run by DM protocol alone). The
   engine side shipped 2026-07 (any size 1–4 works; the counterweights —
   flat income, the press, sweeps — are in; see rules.md "Balanced for
   two"); what remains is the CHA/recruitment fiction and pricing a
   companion. CHA itself is underdefined — detail deferred until this
   layer is next up.

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
- **The "obliterating" wound tier** — one tier above killing blow (severity
  10+, ~9 HP, maybe pierces one Bulwark step) so landed blows differentiate
  again in the 14-20 band; parked because monster STR past `soak + 7` buys
  nothing under the current table (rules.md, the severity design note) and
  the killing-blow cap is scary enough until the top band is authored.
- **Venom / conditions** — the great spider's poison (and disease, bleeds…)
  is a whole system; the bite carries the row until conditions exist.
- **Survival/adventure-sim pivot** (hunger, upkeep, inventory) — a deliberate
  possible future pivot away from the heroic tone, not drift.
- **Power potion re-stock** — retired 2026-07; re-circulate the kind if
  War-Breath ever makes Power genuinely scarce in play.

---

## Open questions

- **Armor:** adopt, simplify, or defer (see above) — the least-developed
  system.
- ~~Can stats ever be raised?~~ **Resolved (2026-07):** the frame is talent,
  the engine is training — DEX/STR stay fixed at creation (natural human cap
  6; only magic/items transcend, to ~double); levels grow the POOLS (+1
  HP/STA/Power per two levels — in the engine since 2026-07).
  Doctrine lives in rules.md ("The ceilings, and what levels grow").
- **CHA / party mechanics** — underdefined by design; detail when that layer
  is next up.
- Every constant is provisional and sim-tuned, never hand-designed — the
  current numbers live in `CLAUDE.md` ("Balance / tuning").
