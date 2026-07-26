# The Attrition Rework — implementation specification (2026-07-26)

The spec of record for the four-slice rework settled in the 2026-07-26
quest-length design session. It is a **build document, not a rules
document**: nothing in here is shipped. `rules.md` describes the game as it
IS and must not be taught any of this until the slice that implements it
lands; `plan.md` carries the roadmap entries; `designlog.md` carries the
reasoning trail. This file carries the contract each build session works
against.

> **Reading order for an implementation session:** `develop.md` first (the
> dev guide is required reading), then the one slice section below that the
> session is building. Do not start a slice from this file alone, and do not
> build two slices in one session — see *Build order and sessions*.

---

## 1. The problem, and the one-line answer

The generator centres quests on **3.74 encounters** (sites roll 1/2/3 at
45/40/15, then rooms roll 1/2/3 at 20/40/40 *per site*; 47% of quests are 4+
fights and the tail reaches 9). That is too long: the designer wants **1
encounter by default, 2 for a middling job, 3 at most**, with sites used only
when the fiction genuinely moves to a different place.

Cutting encounters exposes the real problem underneath. Attrition currently
lives *inside* a quest — press on through four rooms or camp and lose the XP
streak. With one fight per quest there is nothing left to attrit: the party
wins, camps to full (`camp --heal` runs up to 14 free nights, and `dm.md`
names "camp until whole" as the played default), and HP never mattered. Every
obvious fix is a gold price, and gold is the one quantity that inflates:
quest gold is `15 x L` per site over roughly four days, so income runs about
**4 g/day at level 1 and 75 g/day at level 20** while HP pools barely double
(12-20 base, +10 buyable). Any flat price is brutal at the front door and
rounding error at the back; any scaled price is a curve to re-tune forever.

The answer the session settled on:

> **Do not make rest expensive. Make rest incomplete.**
> Gate recovery on **rate and access**, never on price. Time and geography do
> not inflate; a cap on what a night can restore is worth exactly as much at
> level 20 as at level 1.

Which produces the four slices: cut the encounters, make days cost something
(quest clocks), make damage persist past a night (wounds), and make defeat
survivable enough to carry that weight (mercy).

---

## 2. Settled decisions (do not reopen without a design session)

- **HP stays the scalar.** Wounds are named, located records layered *on top*
  of it, not a replacement for it. Rationale: HP is load-bearing in the
  bestiary's 25 bench-fitted `level`/`ref_pack` annotations, the threat math
  (`THREAT_BASE ** level / ref_pack`), the death spiral
  (`Entity.wound_penalty` = `hp_lost // pain`), the pause layer
  (`PAUSE_HP_FRACTION`, `standing_order`, `fight_winding_down`,
  `sim_pause_policy`), and all five bench harnesses. Removing the scalar is a
  rewrite; removing the *displayed number* is a formatting pass, and the
  formatting pass buys the whole felt effect.
- **Max HP is the constitution stat** the designer asked for. No new stat.
- **Wounds are recorded for the played party only.** Foes keep the scalar.
  They do not persist between fights, so records buy nothing and would cost
  the entire bestiary calibration. Foe wound *narration* is free.
- **Wound stat-penalties do not apply inside the fight that caused them.**
  `Entity.wound_penalty` already models "you are hurt right now"; the wound
  record models "you are carrying this". Double-counting them stacks two
  spirals, and `develop.md` records that enemy DEX is the sharpest lever in
  the game (one point moves clear rates by tens of percent). **Maimings are
  the sole exception** and apply immediately.
- **Conditions are built as a general system, not as a bleed special case.**
  It has been the named blocker behind varied enemies, venom, and varied
  magic for three sessions; build it once, properly.
- **Defeat's permanent setback is a maiming, not a stat point.** `rules.md`
  fixes STR and DEX as immovable, and an unrecoverable stat point in a 1-20
  ladder is a death spiral wearing a different hat. A maiming is the same
  mechanical hit, lives inside the wound system, narrates far better, and is
  **curable** later by high-tier magic or a prosthetic — which converts a
  punishment into a story hook and a gold sink.
- **Encounter count stays a weighted roll for now.** Letting the narrative
  content decide a job's length is its own queued design pass (`plan.md`).
- **Site count becomes a template-declared place count.** A job spans two
  sites only when the fiction moves between two places.

Rejected in session, with reasons, so they stay rejected: **scaling tavern
prices** (fiction says a bed is a bed; arithmetic says it inflates);
**food/upkeep as a gold sink** (same inflation, and it taxes a resource with
no other pressure on it); **changing potion prices** (potions are the
overextension warning light; they gain value for free once camping stops
substituting for them); **retribution/patrol attacks as healing pressure**
(re-adds the contentless combat this whole rework removes).

---

## 3. Slice 1 — Quest shape, the pay rebase, and three small fixes

The mechanical change the session started from. Self-contained; ships first.

### 3.1 Quest shape (`quests.py`)

- Templates gain **`places: int`** (default 1) in `TEMPLATES`,
  `EPIC_TEMPLATES`, and `karma.py`'s DARK templates. Set 2 only where the
  fiction genuinely moves: `("the high pasture", "the den in the hills")` is
  two places; `("the village graveyard", "the crypt below")` is one. The
  existing `sites` stem tuples stay as the naming pool.
- **`build_quest`** (`quests.py:912`): replace the site roll
  `rng.choices((1, 2, 3), weights=(45, 40, 15))` with
  `n_places = min(tpl.get("places", 1), len(tpl["sites"]))`. The caper
  branch (`tpl["deed"] or tpl["twist"]`) still forces `len(tpl["sites"])`.
- New quest-level encounter roll:
  `QUEST_ENCOUNTERS = ((1, 2, 3), (55, 30, 15))`, floored at `n_places`
  (a two-place job cannot be one fight). Mean 1.6, hard max 3.
- Encounters distribute across places **front-light** (a 3-encounter,
  2-place job is 1 then 2 — the escalation ends at the destination).
- **`ROOM_SHARES` re-keys to the QUEST's encounter count**, values unchanged
  because they are already bench-calibrated: `1: (1.25,)`,
  `2: (0.85, 1.10)`, `3: (0.55, 0.70, 0.85)`. Shares are assigned in quest
  order across places, not restarted per place.
- **Drop the per-site level decrement**
  (`site_level = max(1, level - (n_sites - 1 - j))`). One quest, one level.
  The rising shares already escalate, and the board stops showing a quest
  whose sites disagree about their own level.
- `_reusable_site`'s room-count gate (`1 <= len(site["rooms"]) <= 3`) must
  match the encounters allotted to *that place*, not 1-3 generally.
- `forge_quest`'s signature changes from `(…, n_sites, n_rooms, …)` to
  `(…, places, encounters, …)`; `session.cmd_forge` follows.
- Quest dict: keep `site_count`, replace `room_count` with `encounters`.

### 3.2 The pay rebase (`rpg.py`)

Pay is per **site** today, so cutting to ~1.15 sites/quest without touching
it drops quest pay ~40% and pushes the career from ~38 quests to ~60 — fewer
fights per quest but *more quests*, which is the wrong direction. Pay moves
to the **quest**, scaled sub-linearly by encounter count because the fixed
overhead (the trip, the giver, the turn-in) is per quest, not per fight.

```
QUEST_XP_PER_LEVEL   = 60      # fit by bench_quests, see acceptance
QUEST_GOLD_PER_LEVEL = 18      # fit by bench_quests
ENCOUNTER_MULT       = {1: 1.0, 2: 1.6, 3: 2.2}
ENCOUNTER_XP_SHARE   = 0.40    # paid as encounters fall; 0.60 on turn-in

quest_xp_total(level, encounters)  = QUEST_XP_PER_LEVEL * (level + 1) * ENCOUNTER_MULT[encounters]
quest_encounter_xp(level, enc)     = quest_xp_total(...) * ENCOUNTER_XP_SHARE / enc   # flat, no streak
quest_clear_xp(level, enc)         = quest_xp_total(...) - enc * quest_encounter_xp(...)
quest_gold(level, encounters)      = QUEST_GOLD_PER_LEVEL * level * ENCOUNTER_MULT[encounters]
```

The `site_*` family **stays** for `sites.py`'s two hand-built anchors — they
are dev/test calibration fixtures that `tune.py`, `bench_training.py`, and
`run_site` are fitted to, and they are not part of a played campaign. Only
the streak argument drops from `site_encounter_xp`. Two deliberate ladders:
the anchors are the fixtures, the quest formulas are the game. Comment them
as such so nobody "unifies" them later.

### 3.3 Deletions

**The XP streak.** `STREAK_STEP`, `streak_multiplier` (`rpg.py:560-563`), the
streak argument on `site_encounter_xp`, `session.reset_streak`
(`session.py:244`), the `streak` save key, the streak line in `tally_lines`
(`session.py:793`), and the streak notices in `cmd_camp`/`cmd_travel`. Its
job — make pressing on beat camping — transfers to the wound track in slice
3, where camping restores stamina but never HP.

**The short rest.** `SHORT_RESTS_PER_DAY` (`rpg.py:1179`), `short_rest`
(`rpg.py:6135`), `Clock.short_rests_used` / `Clock.short_rests_left`
(`rpg.py:1725`), `STA_RECOVERY_BETWEEN_ROOMS`, `HP_RECOVERY_BETWEEN_ROOMS`,
`POWER_RECOVERY_BETWEEN_ROOMS` (`rpg.py:373-377`), the slot reset in
`long_rest`, the `short_rest` calls in `sites.run_site` and the benches, and
the `rest` subcommand in `session.py`. The day's shape becomes one thing: the
night.

### 3.4 Three small fixes that belong in this slice

1. **Camp rolls the visitor BEFORE the night's recovery.** `cmd_camp`
   (`session.py:3484-3505`) currently runs `_long_rest` -> storyteller ->
   brew -> `night_upkeep` and only then `wild_event`, so every night's
   healing is banked before the fight is rolled. Invert it: roll the visitor
   first; if a fight fires, the night is spent on it and `cmd_camp` returns
   without the recovery. This changes the feel of `camp N` completely — you
   fight at whatever you went to sleep with.
2. **Travel encounters fire on the road, not at the destination gates.**
   `cmd_travel` (`session.py:2936`) rolls the encounter *after* the position
   is updated, the arrival is printed, departures are processed, and war news
   is posted — so a road fight is narrated at the destination and draws from
   the **destination** land's pool. Move the roll ahead of the arrival and
   read the **origin** land's pool. v1 behaviour on a fight: the trip is
   interrupted, the days are spent, the party stays at the origin and the
   player re-issues `travel`. (A true en-route position is parked, §7.)
   The rates themselves are correct and were measured this session — see
   §8.3; do not "fix" them without a decision.
3. **Cap the satisfaction ratchet.** Gains (+1 quest clear, +1 tavern night,
   +1/+2 downtime) beat losses (-1 fled, -1 bloodied, -2 Down, -2 death
   witness) on a normal cycle, so morale climbs to 10 and stays. This slice
   reduces fights per quest and increases town nights, making it worse. Add
   `SAT_TAVERN_COOLDOWN_DAYS` (3) so the bed bonus cannot be farmed nightly;
   the injury-side drain lands in slice 3.

### 3.5 Acceptance

- Measured encounters per quest: mean 1.55-1.70, **max 3**, no tail.
- `bench_quests --part career`: quests to cap within ~10% of the current 38,
  median death level not worse than 7 (currently 8). Fit
  `QUEST_XP_PER_LEVEL` / `QUEST_GOLD_PER_LEVEL` to hit it; the values above
  are the starting estimate, not the answer.
- `tune.py`, `bench_training.py`, `bench_party.py` re-measured and
  benchlogged. Expect the hideout/barrow numbers to move: removing the short
  rest makes `run_site` strictly harsher. This is a **rebaseline**, not a
  regression.
- `bench_weapons.py` / `bench_ranged.py` unchanged to the cell (controls —
  they build bare frames and resolve single fights).
- `test_places.py` quest-routing contracts still pass.

---

## 4. Slice 2 — Quest clocks and the banded refill

The piece that makes days cost something without a gold price: healing takes
days, and days cost you the job.

### 4.1 Clocks (`quests.py`, `session.py`)

- `QUEST_WINDOW_DAYS = (3, 7)`, rolled per quest at posting. Quest dict gains
  `posted_day` and `deadline_day`.
- Outcome bands on turn-in:

  | band | condition | pay |
  |------|-----------|-----|
  | quick | done within the first third of the window | x1.15 |
  | on time | done by `deadline_day` | x1.00 |
  | late | done within a grace of +3 days | x0.60, late epilogue |
  | expired | past the grace, or never taken | removed, failure epilogue |

- Templates gain **`failure_epilogue`** beside the existing `epilogue` ("the
  wolves moved on; two more shepherds are dead"). `writing.md` register.
- Untaken quests expire off the board at `deadline_day`; the failure epilogue
  surfaces as a day-stamped rumour next time the party is in that settlement.
- A taken quest that expires mid-run closes as failed; encounter pay already
  earned stands, the turn-in lump does not.
- `session.expire_quests(state)` runs at every day advance (`_long_rest`,
  travel, camp) and on `board`. `board` shows days left per quest.

### 4.2 The hard dependency: banded lazy refill

Worldgen posts the whole board up front against an asserted XP-coverage
target (`WORLD_XP_MARGIN` 1.35, ~26k XP, `xp_to_cap`). **Once quests expire,
that assert is meaningless and the world can run dry.** So this slice must
also land the queued *banded quest inventory* item from `plan.md`:

- Each settlement keeps a few live jobs **per level band**, rolled lazily per
  settlement-day and pruned as they expire or are completed.
- `karma.roll_dark_quest` is the working precedent — lazily rolled per
  settlement-day, never seen by worldgen, bench-invisible. Copy its shape.
- Bands come from `SETTLEMENT_KINDS` (`quests.py:680`: capital 5 slots /
  1-20, city 4 / 1-16, town 4 / 1-14, village 2 / 1-8).
- The up-front coverage top-up and its assert are deleted.

Delete the banded-inventory entry from `plan.md` when this ships.

### 4.3 Acceptance

- A world runs a full 1-20 career without exhausting posted work
  (`bench_quests --part career`).
- Quests visibly expire and refill across a simulated 150-day career.
- Pace: days to cap within ~15% of the current ~158.

---

## 5. Slice 3 — Conditions, then wounds

The centrepiece, and the one to split across two sessions: the conditions
framework is independently useful and independently testable, and the wound
system is its first serious customer.

### 5.1 Session 3a — the conditions framework (`rpg.py`)

Built as a general system because it has been the standing blocker behind
varied enemies, venom (the spider row is currently carrying poison in its
raw damage), varied magic, and burn.

```
@dataclass
class Condition:
    kind: str        # "bleed" | "poison" | "burn" | ...
    power: int       # magnitude per tick
    rounds: int|None # None = persists past the fight until treated
    source: str      # display/attribution
```

- `Entity.conditions: list[Condition]`.
- **Tick point:** end of round in `group_combat`, beside `Entity.regen`.
  Order: regen -> conditions -> Winded/Spent crossings, so a condition tick
  can trip a pause the same round it lands.
- **Stacking is bounded:** a second condition of the same kind refreshes
  `rounds` and takes `max(power)` — it never adds. Unbounded stacking is how
  condition systems become the only strategy.
- **A condition tick can never kill outright.** Taking an entity to 0 puts it
  **Down**, with no crippling save involved. Bleeding out is treatable; a
  silent scalar killer would undo the whole "lethality is real, then padded"
  design intent in `rules.md`.
- **Log:** one collapsed line per round in the player log, emitted `quiet=`
  so the quiet-round collapse still works. The detailed log gets the full
  arithmetic. The 40-column display must not grow a line per condition per
  entity per round.
- **Clearing:** `_clear_fight_states` (`rpg.py:4469`) clears every
  `rounds`-limited condition. `rounds=None` conditions survive to the
  between-fights layer.
- **Stabilize:** a free automatic pass at fight end clears combat bleed on
  survivors. Wound-driven bleed and poison persist until treated — this is
  the designer's "after combat, stabilized, the wounds and penalties remain,
  blood pool remains lower, but the char wouldn't be actively dying".
- New knobs in their own constants block: `BLEED_POWER`, `POISON_*`,
  `BURN_*`, `CONDITION_STACK_RULE`.
- **First customers in this session:** the spider row's venom, the
  pyromancer's fire. Wound-driven bleed arrives in 3b.

Acceptance: `bench_bestiary.py` re-run — the spider and pyromancer rows may
need their `level` annotations re-fitted; every other row unchanged to the
cell.

### 5.2 Session 3b — the wound system

```
@dataclass
class Wound:
    location: str    # "head"|"eye"|"chest"|"gut"|"arm"|"hand"|"leg"|"flesh"
    name: str        # authored display string, writing.md register
    severity: int    # 1-3
    penalty: dict    # stat -> int, applied BETWEEN fights
    bleed: int       # 0 = none
    permanent: bool  # a maiming; only high-tier magic clears it
    treated: bool
    fresh: bool      # taken this fight; penalties inert until cleared
```

- `Entity.wounds: list[Wound]`, `Entity.records_wounds: bool` (played party
  only — foes never record).
- `wound_load` = sum of severities.
  **`hp_ceiling` = `max(max_hp // 2, max_hp - wound_load)`** — wounds can
  never take a character below half their pool. This is the anti-death-spiral
  floor and it is not optional.
- `long_rest` heals toward `hp_ceiling`, never past it. `camp --heal` becomes
  "camp until as whole as the wilds can make you".

**Accrual**, in `_attack` where the tier is already computed
(`TIER_HP`: graze 1 / wound 2 / grievous 4 / crippling blow 6):

| tier | result |
|------|--------|
| graze | nothing recorded — blood loss only (grazes are never located) |
| wound | severity 1, located |
| grievous | severity 2, located |
| crippling, **vital** location (head/chest/gut) | the lethal one — existing death/save path unchanged |
| crippling, **limb/extremity** | **MAIMS**: severity 3, `permanent=True`, entity goes Down instead of dying |
| going Down by any route | +1 severity, unlocated ("badly beaten") |

Grazes staying unlocated is what keeps the reworked 40-column log readable,
and it matches the designer's own split (cuts and grazes are blood loss, not
disabling wounds).

**Location table:** weighted roll — `flesh`/`arm`/`hand`/`leg` common,
`chest`/`gut` uncommon, `head`/`eye` rare. Tune so vitals land ~15% of
located hits; that fraction is what sets how often "crippling" reads as death
rather than maiming, so it is a **primary lethality lever** — bench it.

**Penalties** (`WOUND_PENALTIES`), applied **from the next fight**:
arm -> STR -1 (and DEX -1 at severity 3); hand -> DEX -1; leg -> DEX -1;
chest -> max STA -2; gut -> STR -1 + bleed; head -> DEX -1 and MIND -1;
eye -> DEX -1. `Entity.pressure` reads only wounds with `fresh=False`;
`fresh` clears at fight end. **Maimings (`permanent=True`) ignore `fresh` and
apply immediately** — that is the dramatic beat, and it is rare enough not to
move the curve.

**Do not touch `Entity.wound_penalty`** (`rpg.py:2010`, `hp_lost // pain`,
`HERO_PAIN` = 2). It is the in-fight spiral and it stays exactly as it is.
The wound record is the between-fights layer. Double-counting them is the
single biggest balance risk in this rework.

**Naming:** `WOUND_NAMES[location][severity]` content table ("a deep cut
across the left forearm", "a gut wound, still seeping"). `writing.md`
register. This table is the whole narrative payoff of the system — it is what
lets the agent refer back to an injury three sessions later — so it gets a
real content pass, not placeholders.

**Display:** `tally_lines`, `cmd_status`, and `ui/party.txt` carry the wound
list. In play, HP shows as a **state word** (`Bloodied`, `Failing`) with the
digits available in `status` and `ui/fight-detailed.txt`. This is the
designer's "no HP as a number" at display level, and it is cheaply
reversible.

**Treatment ladder** — the anti-inflation spine. The gate is rate and
access; the fee is a convenience and may stay flat forever.

| source | clears | gate |
|--------|--------|------|
| field stabilize | bleed | free, automatic at fight end |
| a bed in a settlement | 1 severity per night | **time** |
| healer service | several severity, costs a day + a modest fee | **settlement tier** |
| basic potion | HP / blood loss | gold (unchanged price) |
| medium potion / salve | one non-permanent wound | alchemy rank, stock-capped |
| epic potion / high healing magic | permanents and maimings | scarce, authored |

- New `healer` service kind in `places._service_kind` (`places.py:525`) and
  the required-service sets in `_attach_services` (`places.py:543`). Tier
  caps: village 2 severity, town 4, city 6, capital all. The **cap** is the
  gate, which is why the fee never needs to scale.
- Potion tiers slot onto `STOCKED_POTION_KINDS`, `POTION_PRICE`, and the
  alchemy recipe/rank ladder (`brew_stock_cap` = rank + 2 is the existing
  pattern to copy).
- The healing spell's top rank clears permanents; that is the level-point
  sink's permanent career job.

**Satisfaction** (the designer's "your party abandons you if it is more than
x weeks"): `SAT_WOUNDED_DAY`, a per-day drain for each companion carrying an
untreated wound, plus a `SAT_MAIMED` lump. With `SAT_TAVERN_COOLDOWN_DAYS`
from slice 1, a long convalescence now genuinely costs morale, and the
existing `wants_to_leave` / `leave_threshold` (`rpg.py:5142-5148`) already
carry it from there. No new departure machinery.

### 5.3 Acceptance

Full rebaseline: `tune.py`, `bench_training.py`, `bench_bestiary.py`,
`bench_quests.py` (all three parts), `bench_abilities.py`,
`bench_party.py`; `bench_weapons.py` / `bench_ranged.py` as controls.
Expect the career curve to move; the target is that the **beatability curve
stays intact** (the kit-shrink precedent, `develop.md`) — reach-L8 and
median-death-level should not collapse. The vital-location fraction and the
`hp_ceiling` floor are the two dials to move if it does.

---

## 6. Slice 4 — Defeat without death

Small, and it is what makes slice 3's lethality survivable. Most of it
already exists.

- **`session.apply_mercy`** (`session.py:2045`) already implements exactly
  this for posse losses ("left for dead / the lesson", in place of
  `report_game_over`). Generalize it from the posse path to **any** defeat.
- **`FoeSpec.ferocity`** (0-2), a content field, not a stat: 0 = takes what
  it wants and leaves (bandits, raiders); 1 = fights while it is winning and
  breaks off when it is not (most beasts); 2 = never breaks off (undead,
  demons, the conquest's waves). `pursues` already exists as the bool
  ancestor of this. Zero new math, and it makes the bestiary say something.
- On a party defeat, the roster's ferocity decides wipe vs **left for dead**.
- **One mercy per character level, non-cumulative** (`Entity.mercy_level`):
  the mercy fires once per level, not once per career and not stacking.
- Consequences: humanoid rosters take the purse and quality weapons; monster
  rosters take nothing but the party wakes carrying a **permanent maiming**
  on a random member. Never a stat point (§2).
- Enemy retreat: ferocity-0/1 rosters may break off when badly beaten, reusing
  `attempt_retreat`'s chase machinery in reverse.

Acceptance: wipe rate in `bench_quests --part career` converts largely into
mercy events; a career can absorb a defeat and continue. Median death level
should rise relative to slice 3's measurement — that is the point.

---

## 7. The park list

Everything raised in the design session and deliberately **not** in v1.
Each is additive to the schemas above; none requires redesigning them.

**Parked from the wound brainstorm**

- **Damage types and weapon profiles** (cut / pierce / blunt / burn / poison
  / magic). `Weapon` already carries `move_tags` and severity flats, so a
  `damage_type` field is cheap later. Wants the conditions system first —
  which slice 3a delivers.
- **Magic energy bypassing protections.** Waits on damage types and on
  armour existing at all.
- **Armour interacting with wounds** (tier-shift on the incoming wound).
  `plan.md`'s armour item is still "adopt, simplify, or defer"; the wound
  system gives it a much better home if it is ever adopted.
- **Foe wound records.** Explicitly rejected for v1 (§2); revisit only if
  persistent named enemies (the nemesis record) ever need scars.
- **Prosthetics** — steampunk and magical limbs and eyes, including ones that
  push a stat **above** the natural cap. Note the synergy: `plan.md` item 1
  already queues *stat transcendence + magic items (the membrane: +stats to
  ~double the natural cap)*. Prosthetics are that membrane's ideal first
  authored customer — a magic item with a scar attached. Design the `Wound`
  record so a `prosthetic` field costs nothing to add.
- **Disease** as a third condition family beside poison and bleed.
- **Removing HP from the MODEL.** v1 removes it from the *display* only. The
  model-level removal is a rewrite of the bestiary calibration and every
  bench harness (§2).
- **Infection / wound complications over time** (an untreated wound worsening
  rather than merely persisting) — a natural extension once disease exists.

**Parked from the quest and travel discussion**

- **A true en-route travel position.** Slice 1 fixes the two real problems
  (fires after arrival, uses the wrong land's pool) but still interrupts the
  trip back to the origin. Proper mid-road positioning wants the local
  navigation layer and `ui/minimap.txt`.
- **Road-encounter rate trim.** `TRAVEL_ENCOUNTER_CHANCE` 0.15/day,
  `EXPLORE_ENCOUNTER_CHANCE` 0.30, `CAMP_ENCOUNTER_CHANCE` 0.10 were sized
  against 3.74-fight quests. After slice 1 the road is a larger *share* of
  all combat, and slice 2 adds town trips. Re-judge with measured play; the
  lever is a trim to ~0.10 / ~0.20, not a redesign.
- **Wilds camping restoring less than full STA** (`CAMP_STA_FRACTION` ~0.75,
  a bed restoring 1.0). Held at 1.0. Pull it only if play shows multi-
  encounter quests being chunked into one-fight days.
- **Narrative-informed encounter counts** — already queued in `plan.md` as
  its own design pass.

**Rejected outright (reasons in §2)**

Scaling tavern prices; food or upkeep as a gold sink (a later *carry
capacity* version on long wilderness trips remains possible, but never as a
price); changing potion prices; retribution or patrol attacks as healing
pressure; permanent random stat loss on defeat.

---

## 8. Build order, sessions, and verification

### 8.1 One session per slice — yes, deliberately

`rpg.py` alone is 332 KB and `session.py` 206 KB; a slice that ends in a full
bench rebaseline needs its numbers **read and judged** before the next slice
lands on top of them. The repo's own precedent is the levelling framework
(sessions A, B, C, 2026-07-17). Five sessions:

| # | slice | ends with |
|---|-------|-----------|
| 1 | Quest shape + pay rebase + the two deletions + the three small fixes (§3) | fit the two pay constants; rebaseline `tune` / `bench_training` / `bench_party` / `bench_quests` |
| 2 | Quest clocks + banded lazy refill (§4) | career sim proves the board never runs dry |
| 3a | The conditions framework (§5.1) | `bench_bestiary` re-fit for spider/pyromancer only |
| 3b | The wound system (§5.2) | **full** rebaseline; the beatability curve must survive |
| 4 | Defeat without death (§6) | mercy converts wipes; median death level rises |

Each session opens by reading `develop.md` and this file's slice section, and
closes by: syncing `rules.md` and `dm.md` to what actually shipped, appending
a `benchlog.md` entry, deleting the shipped entry from `plan.md`, and
striking the slice from this file's status header.

Slices 1 and 2 are order-dependent (2 needs 1's quest dict). 3a precedes 3b.
4 can slot in any time after 3b.

### 8.2 Docs each slice must touch

- **Slice 1:** `rules.md` Quest System ("Quest shape", the threat math note),
  Progression & Economy (XP earning, the momentum streak paragraph goes, the
  gold section), Survival (the short-rest bullet in "The day / run economy",
  "Resources at a glance", "Implementation notes"); `dm.md` (the `rest`
  command, the streak advice); `develop.md` (dev map + balance summary).
- **Slice 2:** `rules.md` Quest System (clocks, expiry, worldgen reframed);
  `dm.md` (board reading, deadlines); `plan.md` (delete the banded item).
- **Slice 3a:** a new `rules.md` **Conditions** add-on.
- **Slice 3b:** a new `rules.md` **Wounds & Recovery** add-on, plus rewrites
  of Survival's "Resources at a glance", "The two-buffer split", and "The day
  / run economy"; `dm.md`'s "camp until whole" default becomes wrong and must
  be rewritten; `writing.md` gains the wound-naming register note.
- **Slice 4:** `rules.md` (defeat, mercy, ferocity — near "Down, not dead"
  and "Fate's bargain"); `dm.md` (what to do when the party loses).

### 8.3 Measurements taken this session (do not re-derive)

- **Encounters per quest today:** mean **3.74**; 1:9.0% 2:19.7% 3:24.4%
  4:13.6% 5:14.9% 6:10.2% 7:4.3% 8:2.9% 9:0.9%; **47% are 4+**.
- **Travel encounters work.** Measured with the real `notice_contest` and
  real wild pools, 20k rolls per party level:

  | party lvl | sighting (no fight) | ambush | met square | fight given a roll | per 1-day trip | per 2-day trip |
  |---|---|---|---|---|---|---|
  | 1 | 37.7% | 6.2% | 56.1% | 62.3% | **9.4%** | 17.3% |
  | 3 | 24.8% | 4.3% | 70.9% | 75.2% | 11.3% | 20.9% |
  | 5 | 13.1% | 11.3% | 75.5% | 86.9% | 13.0% | 24.1% |
  | 8 | 8.0% | 6.3% | 85.6% | 92.0% | 13.8% | 25.5% |
  | 12 | 4.7% | 13.9% | 81.3% | 95.3% | 14.3% | 26.4% |

  One road fight per ~11 one-day trips at level 1, and the sighting valve is
  widest exactly where a new campaign is played. Rare by design, not broken.
- **Total XP to level 20** is 19,000 quoted (`sum(100 * L)`, L = 1..19);
  current mean quest pay is about `85 * L + 42` XP, giving the ~38 quests
  the career sim reports.
