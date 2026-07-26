# Roadmap

What is left to build, in order. This file is **planned features only**:
design principles (the design spine, the three currencies, tone, legibility)
live in `rules.md`; shared fiction/content style in `writing.md`; the play
protocol in `dm.md`; dev conventions and current balance numbers in
`develop.md`. Anything already implemented is documented in `rules.md` and the
code, not here — when a feature ships, delete it from this file rather than
marking it done.

---

## THE RETRO PIVOT (2026-07-21) — the direction the roadmap now serves

The 2026-07-21 design session reframed the game again — this time the
presentation and the seat the AI sits in, not the content. The trigger:
strong dissatisfaction with the AI-DM's narration and table manner,
even as the dark quests were judged an improvement over the vanilla
ones. The paradigm so far — a ttrpg with an AI DM — is dropped as the
goal.

**The vision:** a mechanics-centered game in the mold of a **retro
text adventure**. The mechanics are not tactical combat but MACRO
decisions and a SIMULATED WORLD the player watches play out. The LLM's
advantage is reframed: not that it narrates, but that it is a **coding
agent running the game** — the central game function need not exist,
only subsystems; the AI calls them, generates content where needed,
and keeps the whole coherent and open. (This inverts half of
2026-07-19's "the superpower is free narration" diagnosis — designlog
records the reversal.)

Concretely:

- **Style (SHIPPED 2026-07-21):** minimalist retro text adventure —
  present tense, second person, terse, deadpan; not wry Pratchett, not
  generic-fantasy purple prose. Expanded into the shared `writing.md`
  fiction/content guide on 2026-07-22; dm.md applies it at the table.
- **Displays over prose:** a greater role for script-generated logs
  and menus, optimized so the chat can usually display them directly
  (roadmap item 1 below).
- **Dark quests stay the most important pre-authored content** — but
  their wording gets a simple-and-straightforward rewrite (item 2).
- **The villain/karma layer is DEMOTED to one layer among several** we
  may return to — no longer the direction the roadmap serves. Nemesis
  persistence / rival posses: bumped way back (they serve narrative
  strength, not mechanical strength, and narrative is not the focus
  now).

### The retro roadmap (build order)

1. **The log/menu rework.** Script output becomes the primary thing
   the player reads; the chat should usually display it directly. The
   40-column wrap stands. Success test: a typical DM message is mostly
   script output plus a few terse retro-register lines.
   - **The combat log part SHIPPED 2026-07-21** (rules.md "Reading the
     combat log" is the doc of record): ONE displayed log — col-1
     lines pre-fitted to 40 via `fit_lines`, damage as `deals N dmg` +
     tier punctuation, attacker-HP tags when hurt, no penalty numbers
     in fight lines (they moved to the pause menu + tally), quiet
     rounds collapsed, movement lines only in ranged fights, named
     moves/abilities name-only, Power printed only on casts, roster
     stat blocks as the enemy introduction, the dying counterattack
     resolving immediately (bench-checked within noise, benchlog).
     The detailed log stopped printing. Since 2026-07-26 combat writes
     committed last-fight snapshots in `ui/fight-short.txt` (the complete
     displayed log and DM fallback) and `ui/fight-detailed.txt`
     (post-mortems); new encounters replace them and paused fights append
     through resume/retreat. Encounter banners, the
     pause menu, and the award/XP/autospend lines were refit in the
     same pass; dm.md's protocol/narration sections updated.
   - **Still open from item 1:** a player STATUS DISPLAY log (a
     fitted, pasteable `status` in the same register — today's
     `status`/`board`/`map` print DM-shaped, wrap-reliant output);
     the levelup menu refit WITH ability descriptions (it still
     prints the old wide two-column-ish lines that wrap raggedly at
     40); and a fitting pass over the remaining non-combat surfaces
     (rests, travel, recruit sheets) where lines still hang a word
     past the width. The `fit_lines` helper and the tally/pause
     penalty display are the pattern to reuse.
   - **Local map page:** add **`ui/minimap.txt`** beside the shipped
     `ui/map.txt`. `map.txt` is the macro Land/Area view; the minimap is the
     current Area/Site/Room branch, visible exits, and local quest markers.
     It should use the shipped `look`/breadcrumb data and join the same
     rewrite + `sheet` commit lifecycle. This is UI only; the persistent
     Land -> Area -> Site -> Room foundation shipped 2026-07-22.
   - **Parked from the log session (designer skepticism recorded):
     E1/P1 shorthand** for enemy/party names in fight lines — saves
     width on long names but reads cryptic; try only if long-name
     fights prove noisy in play.
2. **The quest wording rework.** The dark templates' words themselves
   (titles, descs, giver lines, epilogues in `karma.py`) rewritten
   simple and straightforward, using `writing.md` — the current
   Pratchett-wry phrasing goes; the comedy that survives is situational
   and deadpan. The good-side templates in `quests.py` get the same
   pass afterward where the clash is felt.
3. **Play the dark path in the new register** (absorbs villain roadmap
   item 1): the probe now tests the retro style AND the dark content at
   once — the first ten messages, the first three levels.
4. **The macro-game design session.** The genuinely new build: define
   what the macro decisions ARE and what the simulated world runs.
   Seeds already on the books: off-screen event simulation (parked),
   standing dark enterprises, conquest ticking / domain play. Schedule
   as its own session; nothing is committed yet beyond the direction.

---

## The villain layer (the 2026-07-19 pivot — DEMOTED 2026-07-21)

*(2026-07-21: the retro pivot above supersedes this section's FRAMING.
The karma/heat/pact mechanics and the dark content stay shipped and
stay important; what is demoted is the villain ARC as the roadmap's
direction. The build order below is kept as the layer's internal order
for when/if it returns; item 1 moved into the retro roadmap; item 2 —
the nemesis — is bumped way back, narrative-serving. Of the rest,
conquest ticking and the greed economy are the most retro-compatible
entries — macro decisions, world state — enter through them if the
layer returns.)*

The 2026-07-19 design session reframed the game. The diagnosis: the game
had become a difficulty curve with a purse — real decisions, but all the
same decision (read the board, pick a level), and nothing the player does
changes what the world *is*. The project's actual superpower (the AI
freely narrating and animating people) had nothing to chew on.

**The vision:** the player becomes the *cause* of the world's state
instead of its janitor. The game facilitates and encourages a **cartoon-
villain campaign** — conquer, extort, steal, flaunt — while remaining
fully playable as the old Good game (dual by construction, never two
rulesets). Tone: Discworld/Conan, pratfall evil, never grimdark (`writing.md`
owns the register; dm.md applies it at the table). ~~The candidate frame for
the PC: an imp sent
topside with a quota~~ — **SETTLED later the same day (the dark-quests
session): the PC is a MORTAL of an ordinary race, a low-ranking
employee of Hell under a pact with an evil god.** Not an imp. The pact
rides every new save (`new --no-pact` opts out); rules.md's Karma &
Heat add-on, "The Hell Pact", has the shipped mechanics (assignments,
Chickening Out enforcement, bribes, the caper structure, the
left-for-dead mercy, seventeen new dark templates).

**The load-bearing mechanism (SHIPPED as the first slice, 2026-07-19 —
rules.md's Karma & Heat add-on):** XP bucketed by the alignment of the
work that paid it; bad karma sets HEAT; heat sends escalating lawful
posses at party level + heat; honest work burns karma 1:1. Difficulty
selection by consequence — the throttle the player pumps — and the
ratchet (killing the law is itself a crime) is the villain campaign's
level curve. Karma rides *beside* levels for now: merging them fully
(karma AS the level track) stays an open question below.

**Decisions settled in the session** (recorded so they stay settled):

- **Karma merged into XP accounting** (bucketed awards) over a separate
  currency — a separate track would re-open "what does karma actually
  get you"; the bucket answer is free.
- **The map stays a LIST.** Conquest will be ownership tags on the
  existing Land/Area readout (`[YOURS]` beside `[UNDER THE
  YOKE]`), like the occupation layer already does. No hexes, no grid —
  everything prints at 40 columns.
- **No big-number rework.** The Diablo feel (whip of bad karma, the
  Midas sword) comes from named/masterwork instances with authored
  riders (the named-weapons item in "After that" below), never from
  renumbering the 2d6 engine the whole bench suite calibrates.
- **No food/hunger meter.** The job food was meant to do (a scaling
  gold sink with flavor) goes to the GREED ECONOMY instead (below):
  luxury display as a voluntary sink with consequences, monster-cooking
  as its flavor. A hunger meter is the upkeep bookkeeping the heroic
  tone bans.
- **Conquest is ticking a list, not a strategy layer.** The player's
  dials stay few and chat-legible: where to strike, how hot to run,
  what to flaunt. Anything that can't be decided in one chat line is
  over the line. (An army mechanic is parked as an open question, not
  promised.)

### The villain roadmap (build order — SHELVED 2026-07-21, see the note above)

1. **Play the dark path** (no code): run the first ten messages of a
   wicked campaign on the shipped slice — the tone probe. Does cartoon
   evil sing at the table? Does heat feel like a throttle? The first
   3 levels are the only part that ever gets tested; make them land.
2. **Nemesis persistence.** Posse leaders who survive (party fled, or
   the leader's row lived) RETURN: same face, +1 level, a grudge line.
   The save already keeps `last_leader`; grow it into a small nemesis
   record. This is the AI-DM superpower feature — recurring named
   enemies the DM can animate. (Absorbs the parked "rival" idea.)
   *Pulled ahead of conquest (2026-07-19, the ordering vibe check):
   it is the cheapest item on the board (a thin save record + one
   posse-spawn hook), it makes the just-shipped heat layer read as
   story instead of a random tax, and it is small enough to slot in
   mid-playtest the moment the first surviving leader is felt to be
   forgotten.*
3. **Conquest ticking** — the `conquer` verb: beat a settlement's
   garrison (a generated site at the settlement's band), flip an owner
   tag on the map, collect a daily tribute trickle; occupied-by-you
   settlements refuse honest boards but keep shadow ones. Reuses the
   occupation machinery. Bad karma prices the deed; holding land should
   probably RAISE the heat floor (standing wickedness). *Deliberately
   after the play probe and the nemesis slice: it is the meatier build,
   and its open calls (the heat-floor question, tribute rates) want a
   played dark run behind them.*
4. **The good-karma mirror — the dual campaign.** *Half-shipped
   2026-07-19*: hell's disciplinary posses exist (Chickening Out — they
   punish DISOBEDIENCE, an ignored assignment), and the PC frame is
   settled (mortal pact-holder, default-on). What remains is the mirror
   proper: hell auditing a too-*virtuous* employee (good karma as the
   liability axis), so the hypocritical middle path (both meters hot)
   becomes the comedy jackpot. One mechanic, two skins.
5. **The greed economy.** Luxury items as gold sinks that generate bad
   karma and heat when FLAUNTED (envious hell officials, heroes coming
   for the holy golden elephant): each displayed trophy is a standing
   quest hook pointed at the party. Feasts (cook the monster) as the
   satisfaction/karma variant. This is also the L15+ "what is gold
   for" answer arriving early — coordinate with domain play.
6. **Dark content pass**: race-flavored dark templates (the generic
   seven ship in the slice), war-integration (side WITH the story
   layer's aggressor?), parley/bribery with posses, karma-flavored
   named weapons riding item 5 below.

---

## The levelling framework — COMPLETE (A/B/C shipped 2026-07-17)

Carry-forwards, parked (not scheduled):

- **Enemy-side moves** (giving the drilled soldiery two moves each) and the
  **second-wave moves** (guard-break, taunt, battle-cry) — a later content
  pass with its own bench round (from session B).
- **The day-stamp spoilage variant** — session C shipped the freshness
  STOCK CAP (rank + 2 brewed items) over per-potion spoil timestamps. If
  spoilage should ever be FELT, the cheap variant is one day-stamp per
  hero's brewed batch — noted, not built.
- **Alchemy conditions** (poisons, oils) — UNBLOCKED 2026-07-26: the
  conditions framework shipped (slice 3a), and alchemy is its first queued
  customer. A poison oil is now a recipe plus one `apply_condition` call.

Open to feel out in PLAY: points-per-level 3 vs 4 and training 2n
(re-open only if the mid-band feels grim); the **kit-shrink dial**
(`KIT_STAMINA` 1->2 or a higher `KIT_FORAGE_CHANCE` if play reads too
grim); the **DEX potion** (rank 4/+1 under the standing +DEX warning).

---

## NEXT BUILD — the attrition rework (2026-07-26)

The full build contract for the four slices settled in the 2026-07-26
quest-length design session. It lives here, in the roadmap, and propagates
outward as each slice ships: mechanics to `rules.md`, play protocol to
`dm.md`, dev map and balance numbers to `develop.md`, measured runs to
`benchlog.md`. **Delete each slice from this section when it lands** — that
is the rule for this file and it is what keeps the spec from rotting.

### Why: the problem and the spine

The generator centred quests on **3.74 encounters** — sites rolled 1/2/3 at
45/40/15, then rooms rolled 1/2/3 at 20/40/40 *per site*, so 47% of quests
were four fights or more and the tail reached nine. The target was **1
encounter by default, 2 for a middling job, 3 at most**, with sites used only
when the fiction genuinely moves to a different place, never as the
difficulty dial. *(Slice 1 shipped this: mean 1.66, hard max 3.)*

Cutting encounters exposes the real problem underneath. Attrition used to
live *inside* a quest — press on through four rooms or camp and lose the XP
streak. With one fight per quest there is nothing left to attrit: the party
wins, camps to full (`camp --heal` runs up to fourteen free nights, and
`dm.md` names "camp until whole" as the played default), and HP never
mattered. Every obvious fix is a gold price, and gold is the one quantity
that inflates: quest gold is `15 x L` per site over roughly four days, so
income runs about **4 g/day at level 1 and 75 g/day at level 20** while HP
pools barely double (12-20 base, +10 buyable). Flat prices are brutal at the
front door and rounding error at the back; scaled prices are a curve to
re-tune forever, and a bed is a bed.

> **The spine: do not make rest expensive. Make rest incomplete.**
> Gate recovery on **rate and access**, never on price. Time and geography do
> not inflate; a cap on what a night can restore is worth exactly as much at
> level 20 as at level 1.

*(Slices 2 and 3a shipped the first two thirds of the answer: a day now
costs a job, and what a fight leaves on you no longer always stops at the
door — venom follows you out of the room and only a night ends it. What is
still missing is a night that restores LESS, which is slice 3b's whole job;
until it lands `camp --heal` is expensive and slightly leaky rather than
incomplete.)*

Hence four slices: cut the encounters, make days cost something (quest
clocks), make damage persist past a night (wounds), and make defeat
survivable enough to carry that weight (mercy).

### Settled decisions (do not reopen without a design session)

- **HP stays the scalar.** Wounds are named located records layered *on top*
  of it, not a replacement. Removing the scalar is a rewrite: it is
  load-bearing in the bestiary's 25 bench-fitted `level`/`ref_pack`
  annotations, the threat math (`THREAT_BASE ** level / ref_pack`), the
  spiral (`Entity.wound_penalty`), the pause layer (`PAUSE_HP_FRACTION`,
  `standing_order`, `fight_winding_down`, `sim_pause_policy`), and all five
  bench harnesses. Removing the *displayed number* is a formatting pass, and
  it buys the whole felt effect.
- **Max HP is the constitution stat.** No new stat.
- **Injury is ONE system with two time constants** — see "One injury system"
  under slice 3b. *(This supersedes an earlier call in the same session that
  wound penalties should wait until the next fight; the designer pushed back
  and was right. There is no in-fight/between-fights seam.)*
- **Wounds are recorded for the played party only.** Foes keep the scalar:
  they do not persist between fights, so records buy nothing and would cost
  the entire bestiary calibration. Foe wound *narration* is free.
- **Conditions are built as a general system, not a bleed special case.** It
  has been the named blocker behind varied enemies, venom, and varied magic
  for three sessions; build it once, properly.
- **Defeat's permanent setback is a maiming, not a stat point.** `rules.md`
  fixes STR and DEX as immovable, and an unrecoverable stat point in a 1-20
  ladder is a death spiral in disguise. A maiming is the same mechanical hit,
  lives inside the wound system, narrates better, and is **curable** by
  high-tier magic or a prosthetic — a story hook and a gold sink instead of a
  punishment.
- **Encounter count stays a weighted roll for now**; site count becomes a
  template-declared place count. Letting narrative content decide a job's
  length is its own queued pass (below). *(Shipped in slice 1.)*

Rejected in session, with reasons, so they stay rejected: **scaling tavern
prices** (a bed is a bed, and it inflates); **food or upkeep as a gold sink**
(same inflation, and it taxes a resource with no other pressure on it);
**changing potion prices** (potions are the overextension warning light, and
they gain value for free once camping stops substituting for them);
**retribution or patrol attacks as healing pressure** (re-adds the
contentless combat this whole rework removes).

### Slice 3b — the wound system

**One injury system, two time constants.** Today there is a single channel:
HP. `Entity.wound_penalty` is a live property, `hp_lost // pain` with
`hp_lost = max_hp - hp`, read on every `pressure()` roll and so applied to
attack and defense alike. Because HP carries across fights, **that penalty
already carries across fights too** — it is not an in-fight-only effect. It
just heals away free over about seven nights of camping.

The rework keeps one system and splits it by **how fast it fades**, not by
where it applies:

- **HP is the fast channel.** Mechanically unchanged: blood and shock,
  `wound_penalty` still derived from it, refills with rest up to the ceiling.
- **Wounds are the slow channel.** Named located records that lower the
  ceiling and carry specific stat penalties.

**Both channels are live in every fight, including the one where the wound is
taken.** There is no seam and no `fresh` flag.

What keeps that from double-charging a single blow is a **budget shift, not a
delay**: move part of the roll-penalty budget out of the anonymous HP channel
and into the named wound channel. Raise `HERO_PAIN` 2 -> 3 (a hero down 6 HP
goes from -3 to -2 on all rolls) and let the located wound's -1 pay the
difference. Total in-fight pressure at a given injury level stays near the
bench baseline; what changes is that part of it is now **specific, located,
and does not heal overnight**. That is the entire point of the system.

State the asymmetry on purpose: heroes record wounds, foes do not, so a
hero's penalty budget moves from fast-healing HP to slow-healing wounds while
a foe's stays entirely fast. Over a career that is a net nerf to the party —
which IS the attrition being added. If it proves too much, the dial is the
treatment ladder's **rate** (bed nights per severity, healer tier caps), not
the penalty magnitudes.

```
@dataclass
class Wound:
    location: str    # "head"|"eye"|"chest"|"gut"|"arm"|"hand"|"leg"|"flesh"
    name: str        # authored display string, writing.md register
    severity: int    # 1-3
    penalty: dict    # stat -> int
    bleed: int       # 0 = none
    permanent: bool  # a maiming; only high-tier magic clears it
    treated: bool
```

`Entity.wounds: list[Wound]`, `Entity.records_wounds: bool` (played party
only). `wound_load` = sum of severities.
**`hp_ceiling` = `max(max_hp // 2, max_hp - wound_load)`** — wounds can never
take a character below half their pool. That floor is the anti-death-spiral
guarantee and it is not optional. `long_rest` heals toward `hp_ceiling`,
never past it; `camp --heal` becomes "camp until as whole as the wilds can
make you".

**Accrual**, in `_attack` where the tier is already computed (`TIER_HP`:
graze 1 / wound 2 / grievous 4 / crippling blow 6):

| tier | result |
|------|--------|
| graze | nothing recorded — blood loss only; grazes are never located |
| wound | severity 1, located |
| grievous | severity 2, located |
| crippling, **vital** (head/chest/gut) | the lethal one — existing death/save path unchanged |
| crippling, **limb/extremity** | **MAIMS**: severity 3, `permanent=True`, Down instead of dead |
| going Down by any route | +1 severity, unlocated ("badly beaten") |

Grazes staying unlocated is what keeps the reworked 40-column log readable,
and it matches the designer's own split: cuts and grazes are blood loss, not
disabling wounds.

**Location table:** weighted — `flesh`/`arm`/`hand`/`leg` common,
`chest`/`gut` uncommon, `head`/`eye` rare. Tune so vitals land ~15% of
located hits. That fraction sets how often "crippling" reads as death rather
than maiming, so it is a **primary lethality lever** — bench it.

**Penalties** (`WOUND_PENALTIES`): arm -> STR -1 (and DEX -1 at severity 3);
hand -> DEX -1; leg -> DEX -1; chest -> max STA -2; gut -> STR -1 + bleed;
head -> DEX -1 and MIND -1; eye -> DEX -1.

**Naming:** `WOUND_NAMES[location][severity]` — "a deep cut across the left
forearm", "a gut wound, still seeping". `writing.md` register. This table is
the narrative payoff of the whole system — it is what lets the agent refer
back to an injury sessions later — so it gets a real content pass, not
placeholders.

**Display:** `tally_lines`, `cmd_status` and `ui/party.txt` carry the wound
list; in play HP shows as a **state word** (`Bloodied`, `Failing`) with the
digits available in `status` and `ui/fight-detailed.txt`. That is the
designer's "no HP as a number" at display level, cheaply reversible.

**Treatment ladder** — the anti-inflation spine. The gate is rate and access;
the fee is a convenience and may stay flat forever.

| source | clears | gate |
|--------|--------|------|
| field stabilize | bleed | free, automatic at fight end |
| a bed in a settlement | 1 severity per night | **time** |
| healer service | several severity, a day + a modest fee | **settlement tier** |
| basic potion | HP / blood loss | gold (price unchanged) |
| medium potion / salve | one non-permanent wound | alchemy rank, stock-capped |
| epic potion / high healing magic | permanents and maimings | scarce, authored |

New `healer` service kind in `places._service_kind` and the required-service
sets in `_attach_services`; tier caps village 2 severity / town 4 / city 6 /
capital all. The **cap** is the gate, which is why the fee never needs to
scale. Potion tiers slot onto `STOCKED_POTION_KINDS`, `POTION_PRICE`, and the
alchemy recipe/rank ladder (`brew_stock_cap` = rank + 2 is the pattern to
copy). The healing spell's top rank clears permanents — the level-point
sink's permanent career job.

**Satisfaction** (the designer's "your party abandons you if it is more than
x weeks"): `SAT_WOUNDED_DAY`, a per-day drain for each companion carrying an
untreated wound, plus a `SAT_MAIMED` lump. With `SAT_TAVERN_COOLDOWN_DAYS`
from slice 1, a long convalescence genuinely costs morale, and the existing
`wants_to_leave` / `leave_threshold` carry it from there. No new departure
machinery.

**Acceptance.** Full rebaseline: `tune.py`, `bench_training.py`,
`bench_bestiary.py`, `bench_quests.py` (all three parts),
`bench_abilities.py`, `bench_party.py`, with `bench_weapons.py` /
`bench_ranged.py` as controls. The career curve will move; the target is that
the **beatability curve stays intact** (the kit-shrink precedent in
`develop.md`) — reach-L8 and median death level must not collapse. The three
dials, in order: `HERO_PAIN`, the vital-location fraction, and the treatment
rate.

### Slice 4 — defeat without death

Small, and it is what makes slice 3b's lethality survivable. Most of it
already exists. **`session.apply_mercy`** already implements exactly this for
posse losses ("left for dead / the lesson", in place of `report_game_over`) —
generalize it from the posse path to **any** defeat. **`FoeSpec.ferocity`**
(0-2) is a content field, not a stat: 0 = takes what it wants and leaves
(bandits, raiders); 1 = fights while it is winning and breaks off when it is
not (most beasts); 2 = never breaks off (undead, demons, the conquest's
waves). `pursues` is its existing bool ancestor. Zero new math, and it makes
the bestiary say something. On a party defeat the roster's ferocity decides
wipe vs **left for dead**. **One mercy per character level**, non-cumulative
(`Entity.mercy_level`). Consequences: humanoid rosters take the purse and
quality weapons; monster rosters take nothing but the party wakes carrying a
**permanent maiming** on a random member — never a stat point. Ferocity-0/1
rosters may also break off when badly beaten, reusing `attempt_retreat`'s
chase machinery in reverse.

**Acceptance.** Wipe rate in `bench_quests --part career` converts largely
into mercy events; a career can absorb a defeat and continue; median death
level rises relative to slice 3b. That is the point.

### Parked out of the rework

Additive to the schemas above — none of them requires redesigning anything.

- **Damage types and weapon profiles** (cut / pierce / blunt / burn / poison
  / magic). `Weapon` already carries `move_tags` and severity flats, so a
  `damage_type` field is cheap now that conditions exist (shipped 3a).
- **Magic energy bypassing protections.** Waits on damage types, and on
  armour existing at all.
- **Armour interacting with wounds** — a tier shift would now also decide
  whether a crippling blow kills, maims, or merely wounds. Decide after 3b.
- **Foe wound records.** Rejected for v1; revisit only if persistent named
  enemies (the nemesis record) ever need scars.
- **Prosthetics** — steampunk and magical limbs and eyes, including ones that
  push a stat **above** the natural cap. Note the synergy: the queued *stat
  transcendence + magic items* item is the membrane they need, and
  prosthetics are its ideal first authored customer — a magic item with a
  scar attached. Design `Wound` so a `prosthetic` field costs nothing later.
- **Disease** as a third condition family beside poison and bleed.
- **Infection / wound complications over time** — an untreated wound
  worsening rather than merely persisting; natural once disease exists.
- **Removing HP from the MODEL.** v1 removes it from the display only.
- **A true en-route travel position.** Slice 1 SHIPPED the two real fixes
  (the roll happens on the road, off the origin land's pool) but still
  bounces an interrupted trip back to the origin, and a road SIGHTING is
  simply slipped past rather than offered as a choice. Proper mid-road
  positioning wants the local navigation layer and `ui/minimap.txt`.
- **Road-encounter rate trim.** `TRAVEL_ENCOUNTER_CHANCE` 0.15/day,
  `EXPLORE_ENCOUNTER_CHANCE` 0.30, `CAMP_ENCOUNTER_CHANCE` 0.10 were sized
  against 3.74-fight quests; now that quests average 1.66 the road is a
  much larger *share* of all combat, and slice 2's clocks price the trips.
  Re-judge from played evidence; the lever is a trim to ~0.10 / ~0.20, not a
  redesign.
- **A travel layer in the career sim.** `bench_quests`' careers still teleport
  between jobs, which is why 51% of its turn-ins land in the QUICK band —
  a played campaign, paying 1-2 days each way, will sit in "on time" and
  drift late. Adding the road would make the sim's calendar honest against
  the clock, at the cost of breaking comparability with every career number
  in benchlog. Do it deliberately, in its own pass, not as a side effect of
  another slice.
- **Wilds camping restoring less than full STA** (`CAMP_STA_FRACTION` ~0.75,
  a bed 1.0). Held at 1.0; pull it only if multi-encounter quests get chunked
  into one-fight days.

### Build order, sessions, and doc propagation

One build session per slice — deliberately. `rpg.py` is 332 KB and
`session.py` 206 KB, and slice 3b ends in a bench rebaseline whose
numbers need reading and judging **before** the next slice lands on top of
it. The precedent is the levelling framework's sessions A/B/C.
**Slices 1, 2 and 3a SHIPPED 2026-07-26** (benchlog has all three
measurement entries).

| # | slice | ends with |
|---|-------|-----------|
| 3b | the wound system | **full** rebaseline; the beatability curve must survive |
| 4 | defeat without death | mercy converts wipes; median death level rises |

Slice 4 can slot in any time after 3b. **3a shipped 2026-07-26** — the
conditions framework is in `rules.md`'s Conditions add-on, and 3b's
`Wound.bleed` is now writing into a channel that already exists (the
untimed-condition branch, the field stabilize, the potion/spell clears are
all built and unused).

**Each session closes by propagating outward and deleting its slice from
here.** What each one owes:

- **Slice 3b** — a new `rules.md` **Wounds & Recovery** add-on, plus rewrites
  of Survival's "Resources at a glance", "The two-buffer split" and "The day
  / run economy". `dm.md`'s "camp until whole" default becomes wrong and must
  be rewritten. `writing.md` gains the wound-naming register note.
  `develop.md`: dev map, difficulty levers, full balance rebaseline.
- **Slice 4** — `rules.md` near "Down, not dead" and "Fate's bargain";
  `dm.md`: what to do when the party loses.

### Measurements taken 2026-07-26 (do not re-derive)

- **Encounters per quest, before slice 1:** mean **3.74**; 1:9.0% 2:19.7%
  3:24.4% 4:13.6% 5:14.9% 6:10.2% 7:4.3% 8:2.9% 9:0.9% — **47% were 4+**.
  *After slice 1 (measured over 4900 generated quests): mean **1.657**;
  1:49.3% 2:35.8% 3:14.9%, hard max 3, no tail. 9.8% of quests span two
  places.*
- **Travel encounters work**; they are rare, and the sighting valve is widest
  exactly where a new campaign is played. Real `notice_contest`, real wild
  pools, 20k rolls per party level:

  | party lvl | sighting (no fight) | ambush | met square | fight given a roll | per 1-day trip | per 2-day trip |
  |---|---|---|---|---|---|---|
  | 1 | 37.7% | 6.2% | 56.1% | 62.3% | **9.4%** | 17.3% |
  | 3 | 24.8% | 4.3% | 70.9% | 75.2% | 11.3% | 20.9% |
  | 5 | 13.1% | 11.3% | 75.5% | 86.9% | 13.0% | 24.1% |
  | 8 | 8.0% | 6.3% | 85.6% | 92.0% | 13.8% | 25.5% |
  | 12 | 4.7% | 13.9% | 81.3% | 95.3% | 14.3% | 26.4% |

  One road fight per ~11 one-day trips at level 1.
- **Total XP to level 20** is 19,000 quoted (`sum(100 * L)`, L = 1..19);
  current mean quest pay is about `85 * L + 42`, giving the ~38 quests the
  career sim reports.

---

## Queued — landmark problems (what the banded refill did NOT ship)

*(2026-07-26: the **banded refill itself SHIPPED** with the attrition
rework's slice 2 — settlement slot counts, lazy per-day refill, expiry, and
the deletion of the up-front coverage assert are all in `quests.py` and
documented in rules.md's Quest System, "The clock". What is left of the
original entry is the authored half.)*

*(Story-layer batches 1-2 shipped 2026-07-12; pacing anchors measured
2026-07-12: played campaigns L10 ~ day 45-65 (~10-12 chat hours), L20 ~
day 110-150 (~25-30 hours). Still good and cheap once wanted in play:
war-flavored reskins on local quests in threatened lands, and a rescued
recruit as an extra wave-3 tangible.)*

- **Objective high-level problems that exist independent of the player**:
  landmark problems known by rumor from level 1, standing on the board
  regardless of the party's level and NOT subject to the refill's churn (a
  dragon does not lapse in seven days). The refill posts ordinary work; this
  is the authored counterweight to it.
- Later sim hook (parked): other heroes occasionally solve, or die to, a
  landmark problem while the player is elsewhere.

---

## Queued — quest shape from narrative content (its own design pass)

*(2026-07-26, the quest-length session. That session cuts encounters per
quest to 1 by default / 2 for a middling job / 3 at most, and moves site
count to a template-declared place count — a job spans two sites only
when the fiction genuinely moves between two places. The encounter count
itself stays a weighted roll for now: a deliberate placeholder.)*

- The designer's intent: **the narrative content should decide how long a
  job is** — a template's premise, its stakes, and its place structure
  imply whether it is one fight, a two-stage hunt, or a three-beat
  escalation, and a rolled 1/2/3 only approximates that. The pass makes
  the encounter count (and the shape of each encounter's role in the
  quest) an authored property of the template, so the board's mix of
  short and long work is designed rather than sampled.
- Wants the same pass over the good templates in `quests.py`, the epics,
  and the dark templates in `karma.py`, and it pairs naturally with the
  quest-wording rework (retro roadmap item 2) — same files, same content
  register (`writing.md`).
- Schedule after the quest-clock and wound slices have been played: what
  a job's *right* length feels like is a play finding, not a desk one.

Story items on the shelf:

- **The apocalypse questline — the L12-20 second spine.** Parked until
  the magic tier exists (its payoff enemies are demons above the dragon
  row). *(Pivot note: under the villain frame this may become the
  RIVAL conquering force — the thing that conquers half the world if
  the player doesn't, or the employer the player answers to. Decide
  when the good-karma mirror lands.)*
- **Progression frames** (guild advancement, the legendary-smith arc) —
  narrative wrappers around the same combat quests; cheap now that
  questlines exist.

**A career finding to design against**: the top band (15-20) is still
the hard edge (per-quest wipe 40-65% at level) and still waits on
masterwork gear, armor, and magic for its missing player power.

---

## After that (in rough order)

*(Shipped and struck from this list: placeholder magic + cross-land
deliveries 2026-07-14; Magic & MIND 2026-07-15; ranged combat & guns
2026-07-16; party/CHA layer 2026-07-11 — mechanics all in rules.md.)*

1. **What remains of the magic item**: stat transcendence + magic items
   (the membrane: +stats to ~double the natural cap; +DEX an order of
   magnitude rarer than +STR/+pool); **the wraith** (buildable now that
   attack spells exist); **rank-4 capstones** (authored tomes/mentors —
   the 14-20 band's player power); **enemy spell use** (openers, not
   just bolts); **flight ranks 3-4**.
2. **Armor** — provisional design: shifts the incoming wound tier down
   at the cost of a DEX penalty and higher STA drain. *Status: adopt,
   simplify, or defer.* (Designer lean: probably never important.)
   *(2026-07-26: if it is ever adopted, the attrition rework gives it a
   far better home — a tier shift now also decides whether a crippling
   blow kills, maims, or merely wounds. Decide after slice 3b.)*
3. **Named & masterwork weapon instances** — the tiers exist in the
   schema; nothing placed yet. Named weapons carry authored provenance
   and are story beats, never drops. **The pivot leans on this item**:
   the over-the-top villain arsenal (leech blades via the regen field,
   the Midas sword's gold rider, the whip of bad karma paying karma on
   kills) are named instances with authored riders — no renumbering.

---

## The major-feature shortlist (2026-07-14) — ordering notes

Foundations all shipped (magic, ranged, levelling); what stands:

- **Conditions** — SHIPPED 2026-07-26 as the attrition rework's slice 3a
  (rules.md's Conditions add-on): bleed, poison and burn as one general
  framework. **Disease stays parked** as the third family, and the queued
  customers the framework now unblocks are cheap: a school-wide cast rider
  (every fire bolt burns — deliberately held back, it moves every bestiary
  row because hero wizards gain it too), the firebomb, poisoned blades and
  the rot spell, and varied-enemy riders generally.
- **Free-play facilitation / overriding the mechanics** — mostly dm.md
  doctrine plus the override surfaces that already exist (`forge`,
  `give --as`, the hand-editable save). Cheap, worth doing early.
- **Professions** — a between-fights layer off downtime and the economy;
  natural feeder for domain play.
- **Intraparty mechanics & prominent main NPCs** — deepens shipped
  layers; its big multiplier is the parked off-screen event simulation.
  *(The nemesis record — villain roadmap item 2 — is this thread's
  first concrete customer.)*
- **Domain play** — the endgame layer (holdings, followers, rulership);
  the natural answer to "what is gold FOR at L15+". *(Pivot note:
  conquest ticking is domain play's thin edge — build item 3 of the
  villain roadmap first and let domain play grow out of whatever
  tribute/holding state it creates.)*
- **The content passes** — deliberately last within their threads.

---

## Parked ideas (agreed to exist, not scheduled)

- **Hell as a place** (2026-07-19, dark-quests session) — walkable any
  time at no cost, dangerous, demons love bullying. Today it is pure
  DM narration (dm.md); the parked content: the gladiator pits of hell
  (with the bribe-to-lose-on-purpose bout), the castle bought in human
  bones, hell's org chart above the collections agent. First customer
  of any hell map.
- **A geographic wanted level** (2026-07-19, dark-quests session) —
  searched-for in one settlement / the whole land / all lands, as the
  designer's brainstorm named it. Heat is the GLOBAL version and
  shipped; the geographic split is a refinement — park until heat has
  been felt at the table.
- **Standing dark enterprises** (2026-07-19, dark-quests session) —
  the powder network (and rackets generally) as HOLDINGS that earn and
  draw rivals over time, not one-shot quests. The Powder Trade
  template ships the seed version; the standing layer feeds domain
  play / conquest ticking.
- **The rot spell & evil magic content** (2026-07-19, dark-quests
  session) — "learn an evil spell that quickly rots the opponent
  alive; use it on an innocent bystander" wants a new spell (and the
  conditions system, which shipped 2026-07-26); park with the magic
  content pass, alongside the school-wide cast rider that pass also owes.
- **War-side-taking** ("a land has attacked a neighbor — help the
  aggressor") — already the dark content pass / war-integration item
  (villain roadmap 6); noted here so the brainstorm line has a home.
- **An army mechanic** (2026-07-19) — "some army mechanic might be
  good" for the conquest game; parked until conquest ticking has been
  felt. The guard rail stands: one chat line per decision, or it's out.
- **Karma-gated powers / hell ranks** (2026-07-19) — bad karma
  currently buys nothing but heat and rich work; whether lifetime
  wickedness should UNLOCK anything (evil abilities, hell hierarchy
  ranks, the imp's promotions) is deliberately open — see Open
  questions.
- **Summoning** (2026-07-15) — needs its own design round (action
  economy is the game's strongest measured force).
- **Antimagic** (2026-07-15) — trivial to build, nothing to counter yet.
- **Ward, the tier-shift shield spell** (2026-07-15) — note it doubled
  as the provisional armor design.
- **Opener economy in play** (2026-07-15) — if played wizards resent
  the pool burning on trash fights, the fix is a session-side hold
  toggle, not engine smarts.
- **Opt-out tutorial register** (2026-07-14) — relevant only if the
  game gets a second player.
- **Off-screen event simulation** (2026-07-12) — a world tick rolled at
  settlement arrivals from small event tables, day-stamped. First
  customers: the landmark problems, the nemesis record, the rival.
  *(2026-07-21: promoted to a SEED of the retro pivot's simulated
  world — feeds the macro-game design session, retro roadmap 4.)*
- **Faction reputation** — designer has more to spec; nothing until
  then. *(Note: karma IS a first faction axis — law vs the party;
  spec the rest against it.)*
- **Settlement flavor lines** — valuable but easy; deliberately not yet.
- **The rival** — ABSORBED into the villain roadmap (nemesis
  persistence, item 2) and the apocalypse-as-rival-conqueror note.
  *(Bumped way back with the nemesis, 2026-07-21.)*
- **The traitor twist** — one authored questgiver per conquest variant
  collaborating with the aggressor; cheap authored beat.
- **Morale & surrender** — enemies breaking, yielding, bargaining.
  *(Pivot note: posse PARLEY — bribing the Watch, demanding surrender
  — wants this; build them together.)* *(2026-07-26: the attrition
  rework's slice 4 ships its first half — `FoeSpec.ferocity` and
  low-ferocity rosters breaking off — so what remains here is the
  party-facing side: yielding, bargaining, parley.)*
- **Story recruitment** — "the ogre yields and joins you", DM-driven.
- **Weapon reach** — a small first-exchange modifier; distinct from the
  field.
- **Cover & terrain on the field** (2026-07-16) — prose until the
  wilderness gets a terrain pass.
- **Friendly fire into the press** (2026-07-16) — only if play shows
  free focus-fire reading wrong.
- **The 2-STA heavy swing** — sim-rejected while Spent is lethal.
- **d12 variance experiment** — don't fork the dial while lethality is
  settling.
- **Asymmetric Spent** — soften attack to −3 if spent-vs-fresh grinds
  ever feel wrong.
- **A PC happiness stat** — kept OFF (2026-07-11).
- **Prey depletion (the hunt-spam lever)** — only if play shows
  hunt-spam degenerate.
- **Per-weapon pressure dice** — rejected; 2d6 stays the one dial.
- **Level requirements on masterwork/legendary weapons** — rejected;
  authored placement gates them.
- **The "obliterating" wound tier** — parked until the top band is
  authored. *(2026-07-26: slice 3b gets most of what it wanted for free
  — a crippling blow to a vital already reads as the killing one, and
  the same blow to a limb maims instead.)*
- ~~**Venom / conditions**~~ — SHIPPED 2026-07-26 (slice 3a). The great
  spider is venomous and the pyromancer's fire clings. The `level`
  annotations were deliberately NOT re-fit: both rows moved toward the
  calibration band and stayed in family with a catalog that is broadly
  annotated easy — see benchlog for the numbers, and "Re-annotate the
  bestiary for the pain-2 party" below for the pass that owns it.
- **Survival/adventure-sim pivot** (hunger, upkeep, inventory) — kept
  on the books as a possible deliberate pivot, but note 2026-07-19
  chose the GREED ECONOMY over food as the villain game's sink; this
  pivot is further away than it was. *(2026-07-21: the retro pivot is
  a sibling — macro decisions over a simulated world — so pieces of
  this may return through the macro-game design session.)*
  *(2026-07-26: PARTLY CASHED. The attrition rework takes this pivot on
  the WOUND axis, not the hunger axis: named located injuries, blood
  loss, convalescence, maiming, prosthetics later. Food and upkeep stay
  rejected as gold sinks for the reason this whole rework turns on —
  flat prices inflate away. If rations ever return it is as carrying
  CAPACITY on long wilderness trips, never as a price.)*
- **Power potion re-stock** — if War-Breath ever makes Power scarce.
- **Crit/fumble on the 2d6** — fattens both tails of every exchange;
  full bench re-run before judging.
- **Party members as lives, the wipe version** — the in-fight half
  shipped as fate's bargain; watch whether recruit renewal softens it.
  *(2026-07-26: the attrition rework's slice 4 answers the wipe half a
  different way — left-for-dead once per character level, with a maiming
  as the price. Re-judge this entry after that ships.)*
- **A PC-centric career sim** — if played campaigns drift from the
  bench's even-duo story. *(Pivot note: a karma-playing career variant
  — dark quests + posses in the policy — is the natural check once the
  villain game has been played; today no sim sees karma at all.)*
- **Quest history readout** — cheap; gives the save a memoir.
- **Site persistence / repopulation** — the stick version of one-go
  sites. *(2026-07-26: its old trigger is gone — the attrition rework
  DELETES the XP streak. The new pressure is the wound track: camping
  restores stamina but never HP, so a multi-encounter quest is a real HP
  budget. Re-judge only if that proves too soft.)*
- **Give the rapier its niche back** — do nothing until felt in play.
- **Re-annotate the bestiary for the pain-2 party** — calibration
  polish, not a fire.

---

## Open questions

- **Karma AS the level track?** (2026-07-19) The shipped slice runs
  karma beside XP (bucketed awards). The radical version — karma IS
  progression, levels EARNED by wickedness under the imp's quota —
  would make the villain frame total. Decide after the dark path has
  been played; the bucket design was chosen precisely so the merge
  stays cheap.
- **What does bad karma BUY?** Heat and gold-rich work only, today.
  Candidates: karma-gated abilities, hell ranks (titles + perks), the
  luxury economy's prices. The other half of the original "good and bad
  karma as xp unlocking abilities" idea — deliberately deferred out of
  the first slice.
- **The heat curve's numbers** — KARMA_HEAT_STEP 100, HEAT_CAP 3,
  cooldown 2 days, chance 0.6, dark gold ×1.5: all provisional,
  hand-set, sim-unverified (no sim plays dark). Tune at the table
  first; a karma career sim is parked above.
- **Armor:** adopt, simplify, or defer (the least-developed system;
  designer lean: never important).
- Every constant is provisional and sim-tuned, never hand-designed — the
  current numbers live in `develop.md` ("Balance / tuning").
