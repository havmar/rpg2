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

## Next up — the levelling framework (designed 2026-07-16; three implementation sessions)

The shortlist's "levelling framework" foundation, designed in the
2026-07-16 session. **This section is the full spec** — implementation is
deliberately NOT this session's work; it splits into three sessions (A/B/C
below), each ending with a full bench re-run and a benchlog entry.
Terminology settled: **ability** is the umbrella word; ranked multi-buy
tracks are **skills** (combat training, weapon proficiency, spells,
alchemy); the warrior repertoire entries are **moves**. "Perk" is retired.

Comes forward from the parked list (entries deleted there): **overfill
potions** (ships as the overcharge doctrine, session C), **the alchemist**
(the whole session-C tree), **the three ranged abilities** (arrow-parry /
point-blank mastery / rapid reload, session A catalog), **kiting** (ships
as the skirmisher's step move, session B), and **weapon-granted abilities**
(superseded: moves are weapon-gated by tags, which is that idea grown up).

The one-sentence shape: **a level grants several points, and everything a
level can buy — pool growth included — is bought with those points, at
prices scaled to measured value.** No class gates anywhere: the first rank
of anything is buyable by anyone (the game's own free-allocation doctrine);
prerequisites are physical only (a move needs a weapon that can do it,
spellBOOKS stay wizard-gated, alchemy is open to all but rolls off MIND).

### Session A — the point economy & the ability catalog

**The currency.** `SKILL_POINTS_PER_LEVEL` 1 -> **3** (57 points banked by
L20, 42 by L15). The automatic odd-level pool growth is **removed**;
`grow_pools` leaves `award_xp`, and pools join the menu:

| Purchase | Point cost | Cap |
|----------|-----------|-----|
| +1 max HP, +1 max STA, or +1 max Power | 1 each | +10 bought per pool |
| Combat training rank n | **2n** (was n) | 5 (unchanged) |
| Weapon proficiency rank n | n (unchanged) | 3 |
| Spell rank n, for a spell you KNOW | n (unchanged) | 3 |
| Alchemy rank n (session C) | 2n | 5 |
| A move (session B) | 1 (iaido and the finishers 2) | repertoire ≤ training + 1 |
| Single-buy abilities | 1–3 (catalog below) | — |

Training doubles in price because it is the measured strongest buy (a rank
moves site clear rates by tens of points — bench_training), and the
designer's instinct that "the general fighting skill should cost more"
is right: at rank-n-costs-n it would be strictly the best deal in the new
economy and same-cost-same-value would be broken from day one.

**The arithmetic sanity check** (why 3/level and these prices): the old
default build priced in new points is *training-2n + pools-at-1*, and it
maps almost exactly through midgame — L4: old (training 2, pools +1 each)
= 6+3 = 9 = the new budget to the point; L8: 12+9 = 21 = the budget
exactly. At L11 the old default costs 35 vs 30 banked and at L20 63 vs 57
— the new economy runs ~10-15% tighter at the top, WHICH IS THE FLEX
PREMIUM: nobody gets the old everything-for-free build plus new toys; you
fund moves/abilities/alchemy by shaving pools or a training rank. Net
player power at 14-20 still RISES (the band's known gap): moves, rage,
the ranged abilities, and alchemy are all new power the old build never
had. `POINTS_PER_LEVEL` and the training multiplier are THE two knobs the
session-A bench round is allowed to move (3 vs 4, 2n vs n+something).

**Learnable abilities (the catalog).** `Entity.ability` (one string)
becomes a set; the pause layer checks it. Everyone keeps potions and the
pause — what stops being universal is the *trained* answers:

| Ability | Cost | Effect (mechanics unchanged where they exist today) |
|---------|------|------------------------------------------------------|
| **Bulwark** | 3 | as today (the mid-fight tier-shift save, Power-paid) |
| **First Blood** | 2 | as today (auto opener, 2 Power, guaranteed graze) |
| **War-Breath** | 2 | as today (pause/standing-order: 2 Power -> +3 STA) — now known, not universal |
| **Berserk** | 1 | as today (2 HP -> +4 STA) — now known, not universal |
| **Rage** | 2 | after slaying a foe: +2 to the next exchange; if that exchange fails to slay, the hero spends the following round exhausted (no attack). Mork Borg import; swingy on purpose |
| **Field Medic** | 3 | once per day, when a companion would truly DIE near you: DEX check DC 9 — success commutes it to a Down (rapid surgery, takes your next round). Fate's bargain's price can NOT be medic'd (fate is owed, not bleeding) |
| **Storyteller** | 2 | at a long rest: CHA check DC 9 (+1 per listener beyond the second) — success gives every party member +1 Power ABOVE max (overcharge rules). CHA's first in-mechanics job beyond capacity/gold |
| **Survivalist** | 2 | at a wilds camp: MIND check DC 9 — the camp counts as a tavern night (the overcharge) and night-visitor chance is halved |
| **Arrow-Parry** | 2 / +3 for rank 2 | melee grip only: +2 defense pressure against missiles (arrows/bolts/stones); rank 2 extends to bullets and rises to +3. The parked ranged-ability, priced |
| **Point-Blank Mastery** | 3 | the ranged card shoots at gap 0 — no switch round (parked design, unchanged) |
| **Rapid Reload** | 3 | cadence 0 on a card that has 1 (parked design, unchanged) |

Standing orders update: the War-Breath and Berserk rungs check the
ability; a hero with neither answers a stamina crossing with a draught or
fights on. That IS the intended new pressure — the universal safety net
narrows to potions, and "who knows a conversion" becomes a build fact.

**Healing becomes magic.** `Heal` the ability is deleted; **healing** joins
`rpg.SPELLS` as the tenth spell (unaimed utility, between-fights only, no
in-fight role — exactly today's shape under magic rules): rank 1 mends
3 HP, rank 2 5 HP, rank 3 7 HP, 3 Power per cast, casting check per the
magic add-on (mastery: casting below trained rank never rolls, so a
trained healer is reliable at their own tier — the check bites at the
edge). Rank 3 also stands a Downed ally straight to 3 HP after a won
fight, plus the usual roleplay tier (steady the dying, DM-adjudicated).
One gate loosens to make this work: **ranks are trainable in any spell
you KNOW; wizardhood keeps gating spellBOOKS** (`train_spell` drops its
`is_wizard` check, `buy_spellbook` keeps it). The non-wizard path to
healing is the starter table below (the hedge-healer roll) — after that,
parties without one rely on potions and alchemists, which is the intended
ecosystem shift.

**The staff stops paying in healing.** `heal_bonus` is deleted with the
ability; the wooden staff instead grants **+1 max Power while wielded**
(the focus: fuel, not surgery — "power or int" per the designer, and max
Power is the entanglement-free choice; MIND feeds wizardhood/AIM/quest
sight and must stay a birth stat).

**Starting abilities become the archetype seed.** The random
heal/bulwark/first-blood roll widens to a five-entry table (MIND-highest
wizard override unchanged, school spell as today). Each grant is a
~2-3-point head start that HINTS an archetype without gating one:

| Roll | Grant | The hint |
|------|-------|----------|
| the shieldman | Bulwark | the frontline saver |
| the killer | First Blood | the aggressive duelist |
| the hedge-healer | healing spell rank 1 (+ the 50% staff chance, as today's healer) | the support line — and the only non-wizard door into a spell |
| the herbalist | Alchemy rank 1 | the session-C tree's seed |
| the drilled | one move matching the starting weapon (thrust/sweep/feint by tag) | the session-B system's seed |

**Touch list**: constants + price functions (`train_combat_once`,
`train_proficiency`, `train_spell`, new `buy_pool`, new
`learn_ability`), `award_xp` (no growth), the levelup menu and `train`/
`buy` session surface, `develop_hero` + `autospend_points` +
`make_character` doctrine v2 (below), the standing-orders ladder, save
serializers, dm.md's quick reference + levelup guidance, rules.md
Progression add-on rewrite. Zero-backcompat: old saves die, as always.

### Session B — the moves system (the warrior repertoire)

Spells for warriors, under the autocombat doctrine: **a move is a rider
on the normal exchange, chosen by the engine, never a mid-fight decision.**

**Selection.** Each attack, if an owned move is *eligible* (its condition
holds) and unspent, it fires with chance **50% + 10% x training** (rank 5
= always — "higher fighting ability means more moves", literally); ties
broken by a fixed priority (finisher > disarm > sweep > trip > pommel >
kick > riposte > feint > thrust). **Each move fires at most once per
fight** — that single rule kills the repeat-penalty bookkeeping the
brainstorm circled (no combo counters, no same-move fail states) and
makes a deep repertoire the only way to have a rider every round.

**Flow — why learn many moves when fights run 3-6 rounds:** every
DISTINCT move that fires refunds **1 STA** (cap 3 per fight). Variety IS
the stamina engine the brainstorm wanted; a two-move fighter gets two
riders and 2 STA back, a six-move blademaster fights a longer, richer
fight. No Power costs anywhere in the system (the designer's open
question, answered): STA is the warrior's clock and Power stays the
spell/ability budget — the STA-vs-Power split survives intact.

**Weapon gating** by a new `Weapon.move_tags` field (`pierce` / `blade` /
`blunt` / `heavy`; ranged cards get `ranged`). The rapier is `pierce
blade` and simply lacks the tags for the butcher moves — "some moves
don't fit the rapier" falls out of the tags, no per-move exception lists.

| Move | Cost | Tags | Condition | Rider |
|------|------|------|-----------|-------|
| **Thrust** | 1 | pierce | always | +2 attack pressure this exchange |
| **Sweep** | 1 | heavy | 2+ foes engage the hero | this attack strikes 2 targets (the monster-sweep chassis, hero-side) |
| **Feint** | 1 | blade | round 2+ | next round's attack vs the same target at +3 |
| **Pommel strike** | 1 | blade, blunt | target unhurt or lightly hurt | on a wounding hit: severity −2 but the target loses its next attack (the stun-rider chassis) |
| **Disarm** | 1 | blade, pierce | target carries a breakable weapon | if the attack lands with margin ≥ 3: weapon flies (broken-weapon state; once per foe; mirrors telekinesis rank 1 — the bench checks the two price out comparably) |
| **Kick** | 1 | any | target engaged with the hero | on a hit: target defends at −2 next round |
| **Trip** | 1 | any | round 2+ | on margin ≥ 3: target skips its next attack AND defends −2 next round (prone) |
| **Riposte** | 1 | blade, pierce | hero parried last round | +2 attack pressure this exchange |
| **Iaido** | 2 | katana only | round 1 | +2 attack, +3 severity — then the hero stands stanced round 2 (no attack). The katana's signature |
| **Finisher: Decapitate / Split Skull** | 2 | blade / heavy+blunt (not pierce) | target below 1/3 max HP | +3 severity — stretches the almost-kill into the kill; the log names it and the DM gets the best line in the fight |
| **Skirmisher's step** | 1 | ranged | a charger reaches gap 0 | step back to gap 1 once per fight (the parked kiting, ability-framed so it can't become the default dance) |

Most riders are deliberately small (+2-ish) and mechanically near-
equivalent — the brainstorm's own read. The value of the system is
legibility (named lines in both log levels; the DM narrates over "Rhea
feints — the cutthroat bites") plus the flow refund plus the handful of
real state riders (disarm, trip, the finishers).

Candidate second-wave moves, NOT in v1: guard-break (severity ignores 2
soak — the anti-beast tool), taunt (draw one attacker onto self — press
manipulation, the wizard-protector), battle-cry (waits on enemy morale).

Enemy side: hero-only in v1 (like potions and standing orders). Giving
the drilled soldiery rows (blademaster, warlord) two moves each is a
later content pass with its own bench round — noted, not scheduled.

**Touch list**: `Weapon.move_tags`, `Entity.moves` + per-fight spent set,
the selection hook in `group_combat`'s attack step, the riders (mostly
existing chassis: sweep, stun, broken-weapon, pressure mods), log lines
both levels, `train HERO move NAME` + levelup menu, autospend v2 buys
fighter companions thrust-or-sweep then a finisher, bench extension.

### Session C — alchemy & the potion rework

**The kit shrinks** (the "too generous" faucet): the long-rest restock
drops from 1 healing + 1 stamina PER HERO to **1 + 1 PER PARTY**
(scrounged herbs; shops unchanged at 10 g). This is a real difficulty
lever pulled on purpose — it is the natural candidate for finally closing
the standing hideout flag (measured 80.6% clear vs the ~55% retune
target). The session-C bench round tunes toward the **55-65 band** and
says so in benchlog.

**The brew.** Alchemy is a skill (rank n costs 2n, cap 5, open to all —
30 points, so a pure alchemist maxes it around L15 with ~12 points left
for pools, exactly the designer's target career). At each long rest the
alchemist rolls **2d6 + MIND + rank vs DC 9** (the casting-check chassis;
MIND advantage as specified): miss = the batch curdled, success = the
batch, beat by 7+ or boxcars = a double batch. The batch by rank:

| Rank (cost) | Batch | Unlocks |
|-------------|-------|---------|
| 1 (2) | 1 potion (healing or stamina, brewer's choice) | — |
| 2 (4) | 1 | **strength potion** |
| 3 (6) | 2 | **firebomb** |
| 4 (8) | 2 | **dexterity potion**, **smoke vial** |
| 5 (10) | 3 | bombs at +6 / sweep 3 — "mostly rely on potions for damage" |

**Brewed stock cap, not spoilage** (the designer's spoil question,
answered with a recommendation): a hero carries at most **rank + 2**
brewed items — the fiction is freshness ("it keeps a week or two"), the
mechanics are one integer. Per-potion spoil timestamps are exactly the
inventory bookkeeping the heroic tone forbids (rules.md: no upkeep
meters), and the cap fences the same degenerate case (a free faucet
filling a bottomless stockpile). If the designer wants spoilage FELT, the
cheap variant is one day-stamp per hero's brewed batch (all brewed items
expire 10 days after the newest brew) — cuttable without touching the
rest. Brewed potions are also **unsellable** (no guild seal — rotgut to a
shopkeep): alchemy pays in kit, never gold, so the economy faucet stays
closed.

**Drinking in advance — the overcharge doctrine** (ships the parked
overfill idea; the tavern clamp is the chassis): a potion drunk with the
pool at max grants **+2 above max** (HP or STA by kind), spent-only,
clamped away at the next long rest. Flat +2 on purpose — legible, no
half-restore math.

**The stat brews** (the membrane: potions may transcend the fixed body,
temporarily): **strength potion** +1 STR, **dexterity potion** +1 DEX,
each until the next long rest. DEX arrives two ranks later and never
exceeds +1 (the standing warning: a point of DEX is worth several
training ranks; +STR circulates an order of magnitude more freely).

**The bombs** (the damage career): **firebomb** — thrown on the exchange,
attack = 2d6 + AIM + alchemy rank, severity flat +4, strikes 2 adjacent
foes (sweep chassis), consumes the item; at rank 5, +6 and sweep 3 (a
brewed fireball). **Smoke vial** — a retreat with NO parting blows (the
blink-out analogue, item-priced; the chase still rolls). Poisons/oils
deliberately wait for the conditions system (the parked venom note —
alchemy is its first customer).

**Touch list**: kit constants + `long_rest` restock, the alchemy skill +
brew roll + rank table, potion kinds (str/dex + bomb/smoke as items),
`use_potion` overcharge branch + stat-buff fields with long-rest expiry,
the thrown-bomb branch (AIM chassis), retreat's smoke path, session
`brew` + shop surface, autospend v2 for an alchemist companion, dm.md +
rules.md sections, bench + career re-run with the kit-shrink retune.

### Benchmark validation strategy (all three sessions)

- **`bench_abilities.py` (new, session A, grows in B/C)** — the
  equal-cost matrix the designer asked for: reference frames at L4 / L8 /
  L14, each column one way to spend the SAME banked points (training-
  heavy, pools-heavy, a moves package, an ability package, a spell rank,
  alchemy), each row a fixed suite (at-level generated room, a site run,
  a duel vs the soldiery ladder). **Acceptance band: combat options of
  equal point cost land within ~±10 clear-rate points of the column
  median**; utility buys (alchemy, storyteller, survivalist) are measured
  on their own axis (potions produced, Power banked, camp outcomes) plus
  the career column. Perfect balance is explicitly NOT the bar (the
  designer's own stance — equipment and party context may weigh in);
  wildly-different-at-same-price is the failure to catch.
- **Doctrine v2 keeps the suite comparable**: `develop_hero` /
  `autospend_points` / the bench reference duo reproduce the OLD default
  build in the new currency (pools to the old odd-level curve, then
  training, then proficiency/school as today). Session A's full-suite run
  then isolates the economy change itself; drift beyond noise is
  attributable and gets a benchlog entry before any new content lands.
- **Per-session gates**: full suite (`tune`, training, weapons, ranged,
  bestiary, party, quests) re-run at the end of A, B, and C. Careers:
  reach-L8 stays within ~5 points of the current 66% through A and B
  (no intended difficulty change); session C is the exception — the kit
  shrink deliberately moves numbers, targets: hideout to the 55-65 clear
  band, reckless wipe stays ≥ ~75% ("not using resources mostly means
  death" holds), careers re-anchored and written up.
- **Session B adds a moves matchup block** to bench_abilities (each move
  package vs the reference duo; disarm-the-move priced against
  telekinesis-rank-1); **session C adds the alchemist career column**
  (the L15 maxed alchemist vs the L15 fighter reference).

### Settled here vs. designer decision points

Settled by this design (flagged if the designer wants them reopened):
melee/ranged stay under ONE combat training (proficiency + the ranged
abilities carry the split; shooters already pay ammo and cadence), moves
cost no Power, healing goes to magic with the hedge-healer starter as the
non-wizard door, Berserk becomes learnable-at-1 alongside War-Breath (the
designer asked for "other conversions as well"; if standing orders feel
toothless in play the 1-point price makes Berserk near-universal anyway).

Genuinely open — cheap to flip before session A starts, pick defaults
stand otherwise:

1. **Points per level 3 vs 4** (and training 2n) — bench_abilities rules.
2. **Spoilage**: the stock cap (recommended) vs the day-stamp variant.
3. **Kit shrink target**: the 55-65 hideout band, or gentler (per-party
   2+2) if C's career numbers read too grim.
4. **Move proc chance** (50% + 10%/rank) vs always-fire-when-eligible:
   texture vs determinism; the sims can measure both in an afternoon.
5. **DEX potion existence at all** — shipped at rank 4/+1 under the
   standing +DEX warning; delete it if the bench shows a rank-4 alchemist
   outfencing the fencer.

---

## Queued — the banded quest inventory (worldgen reframed)

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
- **The levelling framework (skills / abilities / moves)** — **designed
  2026-07-16, spec above** ("Next up — the levelling framework"): the
  point economy, the ability catalog, the moves system, the alchemy
  tree; three implementation sessions scheduled.
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
