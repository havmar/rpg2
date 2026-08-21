# The roadmap

This is the sole active roadmap and build contract. **Nothing implemented
lives here** — when a session ships, its contract is deleted and the result
is written to the permanent docs (`rules.md`, `dm.md`, `develop.md`,
`benchlog.md`) and the build record to `designlog.md`. See develop.md's
"Where a finished feature is written up".

The fixed Europe map is **BUILT** (2026-08-15, five sessions; designlog
2026-08-15 and develop.md hold the pointers). **THE TILE ECONOMY ARC**
(Part 1) is now fully **DESIGNED** — five design rounds, settled
2026-08-20 through 2026-08-21 (the designlog entries from "planning the
plan" through round 5's "(E)") — and queued as **four numbered
implementation sessions**. Trigger one by prompting **"implement
session N"**; a session is a full dev sitting (read develop.md first,
ship the contract, run the suites, do the shipping paperwork). The
sessions ship **in order** — each reads the layers the one before it
stamped, and **Sessions 1 (the ground & the sky), 2 (the rolled world:
the last harvest & the census) and 3 (the trade network: mines, goods &
routes) all shipped 2026-08-21** (designlog's (F), (G) and (H) entries;
the built layers are documented in rules.md, dm.md and develop.md, and
their measured numbers in benchlog). **Session 4 is the last, and when
it ships Part 1 is deleted whole.** The numbers are kept as they were
cut, so 4 still means what the designlog says it means. Part 2 is the
draft roadmap
beyond the arc — main points only, each a future design conversation,
none scheduled.

The cut is by implementation seam, not one-round-one-session (the
designlog's round names stay the design authority): session 4 is round 5 —
everything that READS — plus round 4's Miners' League recovery, which is
old-system integration and belongs with the hookup.

**The arc's product is a WORLDGEN PIPELINE, not a running simulation.**
Geography and climate determine agriculture, agriculture determines
population, population determines the settlement census — rolled by law at
worldgen off derived seeds, eyeballed as ASCII overlay maps, then left
alone. The event pulse (cards, weather, the boards) stays the part of the
world that lives forward in time. The spring snapshot, trouble and
politics are the NEXT arcs (Part 2); this arc builds the ground they stand
on.

Standing rules for the arc:

- **Hidden numbers, visible words.** Per-tile quantities (population,
  yield, traffic) are worldgen intermediates the player never sees; what
  the game stores and speaks are words and records the existing machinery
  can read.
- **Author the physical, derive the human.** Nature's layer (terrain,
  climate exceptions, mines, the legendary routes) is hand-authored;
  mankind's layer (farmland, population, the census, the ordinary routes)
  is computed from it. Hand-tuned exceptions to a law are legitimate — the
  map is authored; the law is a helper.
- **Derived seeds throughout**, so every existing bench measures the same
  board it always did; `validate_world` grows a clause per layer.
- **The campaign year is spring to autumn.** No season track; winter is
  out of scope as played time and exists only as a worldgen roll (the
  snapshot arc's).
- **One authority per constant.** econmap.py's constants ARE each
  contract's numbers until its session ships; the session then moves them
  into `places.py` and re-points econmap.py to import them back — the
  tool keeps the rendering and never a second copy.

---

# Part 1 — THE TILE ECONOMY ARC: the last implementation session

## Session 4 — The hookup: the read surface & the League

The design is designlog 2026-08-21 (E) (round 5 — the read surface, the
integration minimum, the storage settlements); the Miners' League's
design is designlog 2026-08-21 (D)'s own scrub, moved here because the
old-world cards returning IS the hookup's business. This is the arc's
last session: when it ships, Part 1 is deleted whole and any parked
item still standing folds into Part 2.

**1. The tile character line.** A `TILE_CHARACTER` table in `places.py`
and `tile_character(world, tile)` — ONE short phrase in the writing.md
register, composed from the tile's facts by fixed priority: the mine
first (by its first good — "silver country", "salt country", "iron
country"), then the goods-origin words ("grain country", "wine
country", "wool country", "horse country", "timber country", "fur
country", and the authored colours' own), then land character off cover
+ terrain + climate ("deep forest", "hill country", "fenland", "the
open steppe", "bare tundra", "open desert", "rich farmland" where the
farmland tag, else the terrain's plain word). One phrase, never a list
— composition into fuller sentences is the DM's, not the code's. The
exact word table is settled at build under writing.md; the examples
here are canon.

**2. The harvest words** (discharging round 1's parked fiction names —
this is the harvest's first read surface). The spoken scale words are
the settled ones — legendary / excellent / ordinary / poor / failed /
apocalyptic — and NEVER the stored percent (hidden numbers, visible
words: the DM speaks the word too). The causes read through
`HARVEST_CAUSE_LINES`: `drought` → "the drought", `rains` → "the great
rains" (on nile tiles "the low Nile" — the failed flood), `frost` →
"the black frost". The line: `last harvest: failed -- the great rains`.

**3. The tile detail fold-in.** `tile_detail_lines` grows the character
line and the last-harvest line (both common knowledge — the player sees
them on map.txt's here-block; inside the 40-column wrap). With session
3's mine, goods and route lines this completes the tile's public file.

**4. The DM tile brief** (designer directive, the round-4 sitting).
`places.tile_brief_lines(world, tile)` — one tile's WHOLE file for DM
eyes, the way `lore` serves the land's: the header (label, country,
biome, terrain, climate, cover), the character line, the last harvest
with its cause, the goods, the mine, the routes with endpoints and
cargo, the census (every slot: tier, the name where materialized —
"a village (unmet)" otherwise — the charter/manor words, the quiet
board marked), then the four NEIGHBOURS in a line each — label,
character phrase, chief settlement tier and name if any, the harvest
word where it is a problem — so the DM narrates toward the next tile
knowingly. A new verb `tile [COORD]` beside `world` and `lore` — DM
eyes, free, costs no day; defaults to the party's tile, takes any
coordinate. The land layer stays `world` / `lore`'s business — the
brief is the TILE's file only. dm.md gains the protocol (consult the
brief on arrival and before narrating travel; it is narration material,
never a dump to the player) and the quick reference gains the five
tiers, the season calendar and the climate words.

**5. The tile menu** — the settled minimum of existing systems reading
the new ground (the priced menu grows a STATIC tile factor beside the
land's dynamic terms; round 4's parked route-aware-prices item resolves
to exactly this). A `TILE_MENU` table, three rows: a grain-origin tile
prices `lodging` 0.90 (bread is cheap at the granary — the mirror of
grain-scarce's 1.50), a mine tile prices `steel` 0.90 (stacking under
deposit-found is right — a strike at the pithead is the cheapest steel
in the world), a crossroads tile (2+ routes crossing) prices `goods`
0.95 and `lodging` 1.10 (full shelves, full beds). Read by
`session.local_term` and the `prices` sheet as a multiplier beside
`worldsim.term`, clamped by the same `MENU_FLOOR` / `MENU_CEILING`;
static, derived, never stored. `toll` and `ferry` stay untouched —
tolls walking the route network is the snapshot and politics arcs'
work.

**6. The Miners' League** — the recovery (designer directive; the
worked scrub is designlog 2026-08-21 (D)). The `deposit` slot returns
to `worldsim.STATE_SLOTS` with its three stages and words, and
`STATE_MENU` prices them again (deposit-drying: steel 1.20;
deposit-found: steel 0.85). The six-card extraction chain is recovered
from the pre-cut catalog (`git show 4d9155b^:worldsim.py`) and re-keyed
`mining/*` for all three lands (each now holds mines): new-seam,
gold-rush, vein-dries, veins-reopened, strike, food-caravan — the chain
discipline unchanged. The scrub: clans → the MINERS' LEAGUE and its
chapter masters; "A dwarf has found a way" → an old engineer; the
under-thane → the League steward; the clan books → the League's books;
`_DWARF_TOUGHS` → the standard human tough pool. The claim-keeper, the
company shop, the winding gear and the pit bosses stay — they were
always human mining language. THE KNOCKERS fact returns verbatim (it
was always human mining folklore), plus a League fact per land naming
its chapter and its mines. The cards fire at land level like every
card; their tile address (the mine) arrives with the snapshot arc.

**7. The standing eyeball and the bench.** Sessions 1–3 each moved
their constants into `places.py` and re-pointed econmap.py (the
standing-rules bullet); this session finishes the tool's turn: its
render commands draw FROM a built world (`places.create_geography`)
rather than a private simulation, and its `--sweep` commands retire in
favor of **`bench_worldgen.py`** — the arc's measured suite over real
worldgen: the harvest sweep (coverage, region sizes, cause mix, the
drought guarantee), the census sweep (per tier, slots per tile, empty
tiles, souls, the quiet-rich share), the trade sweep (routes, ports,
crossroads), default 100 seeds with the census and harvest pins
measured at 500. Register it in develop.md's Files and append a dated
benchlog entry per run, per doctrine.

**8. The scaffolding sweep.** One test in the removed-peoples-sweep
manner: the pre-Europe scaffolding is GONE — no `ENVIRONMENT_PROFILES`,
no `SETTLEMENT_DENSITY` / `_population_slots`, no catalog `environment`
key, no `prairie` in any runtime table or play-facing doc, no bare
`basic` / `mountain` tag on any Area, and econmap.py holds no private
copy of a constant `places.py` owns.

**9. Tests.** The character line and the harvest line on representative
tiles (a mine, a granary, a crossroads, a quiet wilderness tile), inside
the wrap; the brief complete for a start tile and its neighbours, the
unmet settlements unnamed, the DM-only fields absent from the player's
detail lines; the tile menu's three rows reaching `local_term` and
`prices`, stacking with the land's terms under the clamps; the League
chain run in a mining land (seam → rush, dries → reopened, and the
caravan admitted on grain-scarce); the sweep test; one broken world per
new `validate_world` clause if any; every existing bench unmoved.

**What session 3 left on session 4's desk** (2026-08-21, designlog (H)):

- **The label is crowded where the trade is.** Paris carries fourteen
  route lines and the busiest tile in an average world is crossed by
  twelve or thirteen routes, which on a 40-column page is twenty-odd lines
  under the grid. The contract asked for one line per route and got it;
  this session owns the whole read surface, so it is the place to decide
  whether a `+N more` cap (the `map_legend_lines` pattern) belongs there.
- **The trade tags are deliberately kept off an Area's tag list.**
  `materialize_slot` merges the tile's GROUND tags only, because an Area's
  tags are quest vocabulary and `quests._fallback_place_requirement`
  already asks for a `mine` tag. Wiring them back on PURPOSE — a mine job
  landing at a real mine rather than on any mountain — is a one-line
  change with the reason written beside it in `places.py`.

**Parked from round 4** (moved here when session 3 shipped): a
Hanse-shaped authored northern circuit (the derived north draws its own
for now); the Ardennes-shaped western wildwood mark (the eastern one
shipped; the west still has none). Both fold into Part 2 if this session
does not take them.

**Settled non-changes** (round 5's design, so the arc stays this arc):
board activity stays the tier table — deriving it from the band would
count the census twice (the tier IS the band's expression); no trouble
score, no forward simulation, no card changes and no card addresses
(the snapshot arc); creature and encounter geography stays the fauna
dump's — `hunt` and the road keep the land pools; the wealth band stays
the land's 2d6 (the snapshot arc argues the aggregate); the charter and
the manor stay write-only (the politics arc); no new map overlay page —
the 33-column map is settled, and the tile's character lives in the
detail lines and the brief.

---

# Part 2 — The roadmap draft beyond the arc

Main points only. Each is a future design conversation; nothing here is
scheduled or specified.

## The spring snapshot & trouble arc (the natural next)

- **The last-harvest roll SHIPPED with session 2** (2026-08-21 — the
  layer is in `places.roll_harvest` and documented in rules.md's World &
  Navigation add-on; nothing reads it yet). This arc KEEPS: the
  **last-winter roll** for pastoral
  country (fodder, herd losses, animal disease, wolves and monsters at
  the herd's edges — reading the climate table's winter column, and the
  great-rains regions doubling as murrain country, 1315-style); the
  READING of both rolls (states, prices, trouble); and the harvest-day
  consequences (the day the new harvest replaces last year's story — this
  year's harvest stays unwritten until then, the shipped weather tracks
  its story). Spring is the hungry gap: the snapshot the party walks into
  is the year's maximum tension.
- **Organic distribution**: the seeded contagion (centers, causes,
  susceptibility) is the worked model — never everything-everywhere,
  never one needle; margins amplify variance because the centers seed
  where the climate is failure-prone. The winter roll wants the same
  shape over pastoral ground.
- **Trouble siting laws**: trouble = shortfall × population pressure ÷
  trade access; **state reach** (path distance from the capital along
  routes) sites the tax squeeze near and banditry and outlawry far;
  monsters at the thin-population frontier. Benched targets: a few spots
  per country, never zero, never everywhere.
- **The wealth band question**: keep the land's independent 2d6, or
  derive the band from its tiles' aggregate spring. **[remark]** Argue
  the aggregate — the macro story and the map then agree by construction.
- **Cards gain addresses**: a firing card stamps tile-level states (place
  and land states already share one record shape), and admits read
  geography, so the harvest fails where the grain grows.
- **The past-epidemic population scar** — the plague chain's mark on the
  census, parked out of the census session (2026-08-21) and waiting for
  this arc's own trouble model.

## Politics, war & more countries

- **More countries for the medieval feel** — the census of three is a
  contraction artifact, not a doctrine. New countries get cheaper once a
  country is a bundle of tiles plus a card packet.
- **A viking/pirate-analogue raider culture**, mostly threats and
  antagonists rather than a played symmetric neighbour; **Tergal as an
  aggressor** by disposition.
- **The era anchor: about 1500, without the age of exploration.** The
  Europe frame argues against colonial dynamics; Mortellaria's baroque
  surface and any higher technology are the result of heaven, hell and
  magic, not a gunpowder-age tech line. **Pre-Columbus trade is the model
  for the frame edges**: the silk roads in via the eastern edge, the
  spice route through a southern entrepôt to the sea lane (a
  Venice-shaped middleman monopoly is a Mortellaria hook), gold caravans
  from beyond the fertile stripe, a Hanse-shaped northern network (furs,
  wax, timber, herring, grain), the wool–cloth axis in the west.
- **Dynamic borders and tile conquest** (deferred by the Europe build)
  land here, once tiles are worth taking.

## Fantasy & magic elements

- **The monsters & fauna dump** (postponed 2026-08-07; worldsim.md
  carries the three pre-ordered creatures). With the tile ground built,
  the assignment gains geography: creatures OF the marsh, the deep
  forest, the high passes, the empty steppe.
- **Heaven and hell as the technology source** — the parked
  sulfur-to-Hell and robot-servants items wait here as before, and the
  magical-vs-mundane boundary call is still this layer's to make.
- `worldsim.md` remains the reference for what the old world-layer
  packets left undesigned.

## Settlements revisited (later)

For now **the tile is the defining element** and settlements stay thin. A
later round returns to give them detail: more authored template roles per
country (the closure's parked repeat problem), megacities with no natural
Area (the Tile record already permits it), and whatever the census rework
makes wantable. The census session (2026-08-21) left two specific debts
here: a **metropolis** wears the city role and owes one of its own, and
the **hamlet** is deliberately one minimal role a country — a well, a
shrine, a cot and a store — that a detail round would widen. Both live in
`place_catalog.json` and are described in develop.md's Files entry for it.

## Small deferred leftovers (from the Europe build, still true)

- **The charter and the manor have no readers.** Session 2 stores both
  words on every settlement slot and nothing looks at them; what freedom
  is worth — taxes, revolts, entry at the gate — is the politics arc's
  design (rules.md's World & Navigation add-on describes what is stored).
- **Named natural regions** (the Alps, the Pripet, the Danube corridor) —
  take if cheap, still unscheduled.
- Roads and road quality; bridges, mandatory river tolls and ferries;
  ports, owned ships, passage prices and naval encounters — natural
  continuations of the routes session, none scheduled.
- Fogging the base terrain map. Diagonal movement.
- **Two calibration benches are not reproducible run to run**, and
  neither can clear a change. `bench_abilities.py` (found 2026-08-21,
  session 2): its warrior-moves matchup and alchemist career blocks swing
  several points between two runs of identical code. `bench_quests.py`
  (found 2026-08-21, session 3, verified over three runs of an unmodified
  tree): parts 1 and 2 are byte-stable and PART 3, the career sim, is not
  — reached-L20 came back 0.5%, 1.5% and 0.0%. Both develop.md Files
  entries carry the warning. Worth a sitting of its own: a safety net that
  cannot be compared against itself is not one.
- Watch in play: a companion quitting mid-career is much harsher on the
  fixed map (closure note, unchanged — the wound and satisfaction tracks
  are behaving as designed; the road is just genuinely long now).
- `archive/plan-pre-europe-2026-08-15.md` remains historical; nothing in
  it is scheduled unless a later design session deliberately returns an
  item to this file.
