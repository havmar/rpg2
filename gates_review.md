# THE GATES ARC — post-build review (2026-09-13)

A read-only review of the five gates sessions (commits `5e91be1`..`195aeae`,
merged as #105) against the design as it stood at `32cdb60` (`gates.md`
before its sections were cut). Nothing here changes code; every item is a
finding for a follow-up sitting. The whole suite passes (1234 tests, `python
-m unittest discover`), `bench_bestiary --bosses` reproduces benchlog (B),
and a smoke playthrough (new game, map, lore, tile, ruin, delve, city board,
recruit, services) runs clean on seed 7.

Each finding says CONFIRMED (reproduced with a script or a playthrough) or
PLAUSIBLE (read off the code, not reproduced). File:line references are
against `195aeae`.

## Verdict in one paragraph

The plan is implemented: every session's contract shipped, every section of
the design is in code or docs, the paperwork rule was followed (plan entry
deleted, gates.md a map, five designlog and benchlog entries, rules.md parts
1–5, dm.md, writing.md, develop.md). What is wrong is at the seams — the
places where the new content meets the older quest, encounter, room and
recruit machinery — plus two card-layer clauses that never fire and three
deviations from the design that were decided in build sessions and written
up as such (listed last so the next design sitting can accept or reverse
them).

## A. Bugs (fix these)

1. **The boss's body is lost if the party breaks off after killing it.**
   CONFIRMED. Kill Zohariel or Saar, then retreat (or let the fight stagger
   apart) with any other foe standing. `refresh_foes_after_retreat`
   (rpg.py:6503) drops the dead from the remembered room; on the return
   trip `mark_boss_dead` (session.py:5015) sees no dead boss and
   `record_drops` (session.py:4997) never ran on the first fight, so: no
   bar drop, `boss_dead` stays False, the depth is "cleared" and refills
   30 days later with a second Sentinel and a second bar. Fix: mark
   `boss_dead` (and record the bar drop) in the unresolved/retreat branch
   too, or keep dead bosses in the remembered roster.

2. **Card-posted gate jobs spawn with the wrong mercy class.** CONFIRMED
   (two reviewers, independently). `worldsim.job()` (worldsim.py:919) has
   no `ferocity` field and `JOB_KEYS` forbids one, so the nine jobs the
   packets post (Bring the Child Home, The Hermit's Escort, The Lamp
   Thieves, The Servant That Walks, The Year Owed, The Lord's Men, Hounds
   off the Road, The Old Feast, Open the Cages) field Wardens and Sword
   Angels at the row default (takes spoils), not RELENTLESS as section 8
   and rules.md:5982 say. The same titles on `quests.TEMPLATES["heaven"]`
   carry `GATE_FEROCITY` correctly. Fix: add `ferocity` to `job()` /
   `JOB_KEYS`, pass `GATE_FEROCITY[side]` on the gate cards.

3. **Every land's wilderness got wider, and identical.** CONFIRMED.
   quests.py:727 appends the eight ruin templates to EVERY culture's
   table, and `wild_pool` (quests.py:2278) is the union of a culture's
   template pools. Before the arc Phyrascia's roads rolled 15 kinds with
   no ogre, troll, giant, wyvern, drake or dragon; now all nine lands roll
   the same 23-kind pool. A dragon can appear on a Phyrascian road far from
   any ruin. Nothing in benchlog re-measures the wild tables; designlog (E)
   noticed the effect for the two cities only. Fix: keep `RUIN_TEMPLATES`
   out of `TEMPLATES[...]` and add them in the posting pass when a ruin is
   reachable, or exclude strict-placement templates from `wild_pool`.

4. **The eight ruin jobs are dead on most boards.** CONFIRMED by sampling
   40 seeds: a settlement within `ORDINARY_TARGET_DAYS` (3 road-days,
   quests.py:166) of Candor exists in 17/40 worlds, of Libera in 11/40
   (the ruins prefer slow ground and are barred from capitals and their
   ring). `_ruin_place` is strict (quests.py:789), so in the majority of
   worlds no board ever posts a ruin job and the "increased activity
   around" of section 7 does not happen. Fix: give the ruin family its own
   radius (5–6 days), or post ruin jobs at the keeper's capital regardless.

5. **The deepest site's four-room job overpays.** CONFIRMED. `cmd_delve`
   forges with `encounters = len(site["rooms"])` = 4 (session.py:5118) but
   `quest_xp_total` / `quest_encounter_xp` / `quest_clear_xp` clamp at 3
   (rpg.py:632–662), so each of the four rooms pays a three-encounter share:
   at L17 the plaza pays 1626 XP against 1394 for a three-room site, while
   the stored `xp_total` says 1742. `RUIN_SHARES[4]` (places.py:2741) sums
   to 2.50 against `ROOM_SHARES[3]`'s 2.10 (+19% roster budget) despite the
   comment saying "the same total". The design itself contradicted its own
   1–3 rule here ("the deepest site four"); the build should have settled
   it. Fix: an honest 4-encounter multiplier, or pay the delve's per-room
   share as the 3-encounter total split four ways; rescale or bench the
   shares.

6. **A refill does not clear the party-side room records.** CONFIRMED by
   probe. `refill_ruin_site` (places.py:3016) re-rolls the world's rooms
   but `state["rooms"][(site_id, room_index)]` (written at session.py:4262
   and :6224) survives, and `reclaim_room` (session.py:4395) pops it first,
   so the next delve of a refilled site fights the old healed leftovers
   instead of the ring's fresh roster. `site["routed"]` (session.py:4292)
   also survives, so a once-routed site prints "driven off, not slain" on
   every later clear. Fix: drop the site's `state["rooms"]` keys and reset
   `routed` when refilling.

7. **Recruits in Concordia and Saturna are born there.** CONFIRMED in
   play: `recruit` at Concordia yields "Kavodiel -- concordia m, age 33 ...
   speaks: Latin, Phyrascian". `cmd_recruit` passes `homeland=here["land"]`
   (session.py:1689/1692), bypassing `HUMAN_HOMELANDS`; `roll_tongues` then
   treats Concordia's Latin as Byzantine Latin and rolls a random human
   second tongue. The design says nobody is born in the city states
   (section 6). Fix: map a city state to a human homeland for recruits
   (the `cut_from` land is the natural one), or cast them from the pool
   without a homeland and give them the city's tongue.

8. **`go SITE` walks into any ruin Site without a delve.** CONFIRMED. The
   six Sites are `known=True` and `cmd_go` (session.py:5943) matches any
   known site by substring, so `go choir hall` enters THE CHOIR HALL past
   the cleared/sealed checks; `room` then refuses. A dead end, not an
   exploit. Fix: `cmd_go` skips sites carrying `ruin` and points at
   `delve`.

9. **The `border` tag is stale after the city takeover.** CONFIRMED
   (20 worlds: 28/40 city tiles and 84 neighbour tiles lack `border`).
   `border` is computed in the neighbour loop before `roll_gates`
   (places.py:3208 vs :3235) and `_city_takeover` (:2930) never recomputes
   it. `border` is a `TILE_FIT_TAGS` word read by settlement fitting.
   Fix: recompute for the tile and its neighbours inside `_city_takeover`.

10. **Two relation rows read a `when` that never or always holds.**
    CONFIRMED. `pulpit-against` (worldsim.py:5047) reads
    `preached-against` on the HOST, but only `heaven/the-sermon` sets it,
    and that card fires on Concordia — the row runs on `interdict` alone.
    `hounds-out` (5050) reads `at-war`, which is stamped at worldgen and
    never cleared, so in 15/30 worlds Saturna's roads carry a permanent
    0.40 hound row from day 0 as a standing fact, not an event. Fix: make
    the sermon a host-side card; read `hunt-up` only, or a war state that
    ends.

11. **`the-gate-guarded` and `the-sermon` are both absent in about half of
    all worlds.** CONFIRMED (seed 1). Design: "constitution QUARANTINE or
    tension prefect-vs-church"; `admits` is AND across kinds so the build
    took the tension only (designlog E #3). A Concordia that rolled
    `quarantine` without `prefect-vs-church` can never see `gate-shut`,
    `preached-against` or `cure-dear`. Fix: a second card keyed on the
    constitution, or an OR group in `admits`.

12. **The two `magic/*` any-land cards reach both city states.**
    CONFIRMED in seed 1–3 decks. `_HUMAN` scope (worldsim.py:796) is used
    only by the `mining/*` cards; a witch-hunt at the Prefecture is a
    thematic seam. Fix: scope `magic/wild-talent` and `magic/the-hunt`
    `_HUMAN`.

13. **A sealed ruin still posts ruin jobs and still reads as live.**
    PLAUSIBLE. `close_ruin_site` clears only the ring STATES; the tile and
    Area tags stay, so boards keep posting "Looters in the White Ruin" into
    a ruin whose line says nothing comes out of it, and `world["gates"]`
    never learns it was sealed. Fix: a `sealed_day` on the gate record,
    read by `_ruin_place` / `place_reachable`.

14. **Boss respawn with a second bar via a reopened quest.** PLAUSIBLE
    (probe by forcing the quest to `failed`). `ruin_site_rosters`
    (places.py:2882) always appends the boss and `cmd_delve` forges a fresh
    quest whenever the stored one is not `open`. No path today except a
    wipe-and-continue; a trap for any future `abandon`. Fix: omit the boss
    when `boss_dead`.

15. **The synod news line starts sentences in lower case.** CONFIRMED.
    `_RITE_WORDS` (worldsim.py:1798) begin "the …" and
    `communion/the-return-question` (4297) puts them after full stops.

## B. Seams and nits

- **Boss names are numbered.** "Zohariel the Sentinel 10" — `make_foe`
  numbers every body (sites.py:570). A one-off with an authored name should
  not carry an index.
- **`accepted` keeps done delve quests** (q23 stayed in `accepted` after
  the clear); harmless today.
- **Armory never learns the bar moved.** After the bar drops and is given,
  `armory` still says the Sentinel holds it (weapons.py:426 writes
  `status: "known"`; nothing writes anything else). Shared with rolled
  pieces, but the bars are where the player looks.
- **Two Hell skin tables disagree.** karma's `HELL_SKINS` / hellgate card
  (a Duke of Hell, Demon Brute) versus `GATE_SKINS["hell"]` (Prince of
  Hell, Horned Brute). Same rows, different names; no path applies both.
  Design section 0 says the pact is ignored, so a recorded wart.
- **`HEAVEN_CITY_POOL` / `HELL_CITY_POOL`** (quests.py:315) are referenced
  only by tests; `TILE_STATE_ENCOUNTERS` hand-copies the kinds.
- **The two EPIC capital rows are not epic-banded.** The Prefect's Levy
  (LADDER_POOL, 1–20) and The Hunt of Misrule (HELL_RUIN_POOL) post at
  L2–L3 ("a horned giant off Libera" with a wolf roster). Capital-only
  holds by construction; "EPIC" is not delivered. Pool them high or add a
  band floor.
- **`heaven/the-removal` and `hell/the-lord-hanged`** post on the city's
  own board, not "the host's nearest town" / "the host's capital"; no
  relation row reads `lord-hanged`; `the-lamp-thieves` has no `proof`
  (`job()` cannot carry one).
- **Ruin Site tags are `['ruin', 'ruin']`**, the ruin Area and settlement
  slot 01 share an Area seed (nothing reads it), and `look` prints the
  TILE line before the gate line where the design says the gate line
  leads (`tile` does lead with it).
- **`_validate_countries`** checks one tile per city state but not "of the
  right set"; `bench_worldgen.py:269` still reads
  `HISTORICAL_CAPITAL_TILES` rather than the land record.
- **Tile precedence is "asked first", not "outranks"**: when the ring's
  roll fails the land's entry still rolls (session.py:5228). Note only.
- **Site flavour.** All six Sites of a ruin share one description; the
  design's per-site "what is there" column (the hall still hums, lamps
  that still burn) survives only in the room names and dm.md's paragraph.
- **Balance note, not a bug.** A two-person party wiped in THE CHOIR HALL
  (L5 at L5) and a two-person L20 party lost to the colossus-plus-Sentinel
  room. The bench targets are duo-baseline, so this is the intended edge;
  worth a line in dm.md that the ruins are a full party's work.

## C. Deviations from the design that were decided in the build

Each is written up in designlog/rules/develop as a call; the design doc is
what is stale. Listed so the next sitting confirms or reverses them.

1. **Ruin jobs do not reuse the six authored Sites.** Design 7/14: `reuse:
   "prefer"` on the Site stems. Code: `_reusable_site` (quests.py:1352)
   skips any `ruin` Site, so a posted job builds a new site named by stem
   beside the authored one ("the measuring house" L3 beside THE MEASURING
   HOUSE L11; "The Register of Candor" at L3 against porters who kept it a
   thousand years). rules.md:6128 and develop.md:2939 record it.
2. **The dark outlets were not built.** "Deliver the Child", the debt-book's
   "collect it", the stranded demon's "bring her in" — each card posts one
   `good` job; `job()` has no dual-align shape. "The Year Owed"'s desc still
   offers the collection.
3. **Placement tag is `<side>-ruin`, not `gate-ruin`** (a tightening, and
   correct); natural Areas do NOT inherit the gate tags (built before
   `roll_gates`) — the mechanism the design named is not the real one.
4. **`the-cure-line` prices Concordia, not the host** (designlog #11).
5. **Fire blood's "max Power +2"** is implemented as the whole range moving
   (floor +2 and ceiling +2, rpg.py:6582); rules.md part 3 says so.
6. **Old Host body** is hp 16 / drilled +2, not 20 / +3, inside the
   design's tuning allowance and in benchlog (B).

## D. Docs

- develop.md:177–179 still says plan.md "carries one build contract, THE
  GATES ARC ... ONE session now". It carries none.
- The four dev-map entries (develop.md:2872, 2922, 2957, 3004) still point
  at "`gates.md` for what is left to build" / "what session 5 still owes".
- worldsim.py:1105–1109 still calls both packets "STUBS on purpose ... so
  session 5 extends them".
- The design's section 7/14 `reuse: "prefer"` clause and section 11's dark
  outlets should be marked as build-changed wherever rules.md restates
  them, so the next reader does not take the old text as the rule.

## What was checked and holds

Placement rule 1–6, the sets, the roll order and child seed, the empty-set
raise, the weighted terrain draw, the `world["gates"]` record, the rings as
dated states with `by`, the tile tags, the ruin Area shape and tags, the
six Sites at 2/5/8/11/14/17 with rosters off the pool and the champion in
the cells, the map marks and GATES legend, `delve` (forced, no slot, no
radius, no giver, neutral, field tranche only, 30-day refill, deepest
seals and clears the ring), all 23 skin rows both sides, the four pools,
`GATE_FEROCITY` on delves and templates, `warden blade`, `BOSSES` and both
bodies, `make_foe` refusing a boss without steel, the bars generated off
the world seed and entered in the armory, `bench_bestiary --bosses`, the
twelve section-14 templates' fields, the nine card jobs existing, the
catalog v4 lands and cultures, the `gate_city` templates and menus, the
one-slot city census, `capital_tile` as a land fact, the ceded-tile
validator arithmetic, `HUMAN_HOMELANDS` for the PC and companions, the
start slot never a city state, `RULER_TITLES`/`DEFENDER_ROLES`, the
appointed/acclaimed crowns with `BODILESS` barred, the full packets
(constitutions, tensions, edges, facts, options, 8+8 cards, weather and
season), `STATE_WORDS`/`STATE_MENU`/`STATE_ENCOUNTERS`, `stamp_gates`
(hosts-*, keeps-*, host facts, `pagan-host`, the crusade tension only on
the three Sun-communion northern hosts), the synod card, HOST resolution
with no placeholder leak, `TILE_STATE_ENCOUNTERS` and `STATE_DANGER`
applied once each in road/explore/camp, the city states never in a war,
`Entity.blood` round-trip, the d6 and `--blood`, the companion odds, the
floors/ceiling/ward/Old Tongue, the BLOOD row and `TRAIT_NOTES`.
