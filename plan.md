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
stamped, and **Sessions 1 (the ground & the sky) and 2 (the rolled world:
the last harvest & the census) both shipped 2026-08-21** (designlog's (F)
and (G) entries; the built layers are documented in rules.md, dm.md and
develop.md, and their measured numbers in benchlog). The numbers are kept
as they were cut, so 3 and 4 still mean what the designlog says they
mean. Part 2 is the draft roadmap
beyond the arc — main points only, each a future design conversation,
none scheduled.

The cut is by implementation seam, not one-round-one-session (the
designlog's round names stay the design authority): session 3 is round 4's
trade network over the census session 2 rolled; session 4 is round 5 —
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

# Part 1 — THE TILE ECONOMY ARC: the remaining implementation sessions

## Session 3 — The trade network: mines, goods & routes

The design is designlog 2026-08-21 (D) (the round-4 entry), including
the reversal it records: **exotics are goods like any other** — the old
keep-them-off-the-map remark is dead; an exotic's origin tile is simply
the frame's door (the eastern gate, the delta port), and the legendary
roads stay worth taxing and robbing because that is where their whole
cargo walks. The layer and the eyeball tool are in the tree
(`econmap.py routes [SEED]` / `routes --sweep`); **econmap.py's
constants ARE this contract's numbers** (`MINES`, `GOODS_AUTHORED`,
`ENDPOINT_NAMES`, the derived-origin thresholds, `GOOD_ROUTES`,
`MINE_FOOD_DAYS`, `MIN_PRODUCE_REGION`, `LEGENDARY`). The mines, the
authored colour, the derived origins and the legendary roads are
deterministic like the map; the ordinary network is rolled WITH the
census it reads (derived seeds, after the census roll), so the trade
skeleton is fixed in character and each world's own in detail. Measured
over 100 seeds: ~59 routes a world (58–59), ~114 of 314 land tiles on a
route, ~27 ports. The Miners' League recovery is SESSION 4's; this
session builds the ground it will speak of.

**1. The ground.** Rolled at worldgen after the census. Stored:
`tile["goods"]` (the origin's good words — sparse, most tiles carry
none), `tile["mine"]` (the mine town's name), and the world's route
records — id, name (legendary only), the ordered tile path, the goods
carried, the length in days. Tags grow: `mine` on mine tiles,
`trade-route` on land tiles a route crosses, `port` where a route steps
between land and sea, `sea-lane` on the sea tiles it sails.
`validate_world` grows the clauses: every mine tile carries its town,
its goods and its tags; only legal good words anywhere; every legendary
road present with its authored endpoints and cargo; every route path a
chain of real edges whose days sum to the record's; ports on coast.

**2. The mines**, authored, few and famous (`MINES` — nine, each also
an authored mine TOWN in the census, seated in session 2): Goslar
R09C14 (silver, copper — the Rammelsberg), Kutna Hora R09C19 (silver),
Falun R03C22 (copper, iron), Banska Stiavnica R10C20 (silver, copper),
Melle R10C08 (silver), Erzberg R11C14 (iron), Novo Brdo R13C18
(silver), Luneburg R08C16 (salt), Wieliczka R10C21 (salt). **The
mining-town rule is two laws**: the town law (slot 1, tier town, named
by the mine, always free — shipped in session 2) and the hunger law — a
mine tile whose own realized arable is under 0.30 gets a GRAIN ROAD
from the nearest grain origin within `MINE_FOOD_DAYS` (6): the food
caravan, a route and a vulnerability in one stroke. Falun finds no
grain in reach and stays UNFED by design (pinned): the north's grain
problem is real, and the DM has a standing story.

**3. The goods**, nineteen words. Derived origins, by law over the
prior sessions' numbers (regions of at least `MIN_PRODUCE_REGION` = 2
contiguous tiles, except grain — one alluvial tile IS a granary):
**grain** (realized ≥ 0.55: the river corridors and the Nile), **wine**
(med and wet-med farmland), **wool** (oceanic and med hill country,
pastoral ≥ 0.40), **horses** (the steppe's herds, pastoral ≥ 0.40),
**timber** (wooded + river or coast, never marsh), **furs + wax** (deep
forest in taiga, tundra or continental — the north and the eastern
wildwood). Authored colour (`GOODS_AUTHORED`): the bay salt pans
R10C05, the wine coast R11C06, the Sound's herring R06C15, the amber
shore R06C22, the cloth looms R08C11 and R13C14, the Lombard armouries
R12C13, the middle Danube horse fairs R11C19. The exotic doors: the
eastern gate R11C30 (silk, dyes), the delta port R18C24 (spice, sugar,
dyes). Mines carry silver, copper, iron, salt.

**4. The routes.** The ordinary network is computed: per origin and
good, `GOOD_ROUTES` names the destination kind (markets = city-grade
chiefs + historical + mine towns; cities; the three metropolises; the
smiths; the cloth looms; the origin's own capital or all three), how
many destinations, and the bulk range in days (rich goods travel any
distance — silver to the crown's mint, wool to the looms, cloth and
wine to the metropolises, arms to the capitals). The pathfinder is
places.py's own (`_single_source` — this session retires econmap's
restated copy); ties settle deterministically. The LEGENDARY five are
authored endpoints whose line the same pathfinder draws: the Silk Road
(the eastern gate → Constantinople; silk, dyes), the Spice Lane (the
delta port → Venice by sea; spice, sugar, dyes), the Amber Road (the
amber shore → Venice), the Fairs Road (Venice → Paris; silk, spice,
sugar) and the Grain Fleet (the Nile granary → Constantinople). **The
sea rule**: sea sails at the settled edge cost (no cheap freight — one
distance model for war, trade and play); a route's sea tiles are its
sea lane, and the two shores where it changes element are ports. Routes
with shared endpoints merge their cargo.

**5. The label** — the one read surface this session ships (designer
directive): `tile_detail_lines` grows the mine line, the goods line and
one line per route crossing the tile — endpoints by name and the cargo,
`Goslar – Paris: silver`, `the Silk Road: the eastern gate –
Constantinople, silk and dyes` — inside the 40-column wrap. Everything
else that READS the trade layer (the DM tile brief, the map page,
prices, boards, encounters) is session 4's.

**6. Tests.** Origins, mines and legendary roads identical across
seeds; the network's pinned sweep (~59 routes, ~114 land tiles on a
route, ~27 ports); the mines by name with their towns and tags; a grain
road for every hungry mine and Falun pinned unfed; route records
well-formed end to end; the label lines wrapped; one broken world per
new `validate_world` clause; every existing bench unmoved (derived
seeds).

**Explicit non-changes** (settled, not deferred): the edge model is
untouched — no cheap sea freight; no re-export chains — a route is one
origin to one destination, and the entrepôt story is told by routes
MEETING at Venice, not by cargo transshipping; the exotic doors are
ordinary tiles with no special rule; nothing reads routes yet beyond
the label (inns, tolls, banditry, plague walking in from a port stay
later arcs' work, with their addresses now on the map).

**Parked here**: a Hanse-shaped authored northern circuit (the derived
north draws its own for now); the Ardennes-shaped western wildwood mark
(the eastern one shipped; the west still has none).

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
- **`bench_abilities.py` is not reproducible run to run** (found
  2026-08-21 and verified against an unmodified tree): its warrior-moves
  matchup and alchemist career blocks swing several points between two
  runs of identical code, so a diff of that file proves nothing. Worth a
  sitting when somebody next touches it; develop.md's Files entry carries
  the warning.
- Watch in play: a companion quitting mid-career is much harsher on the
  fixed map (closure note, unchanged — the wound and satisfaction tracks
  are behaving as designed; the road is just genuinely long now).
- `archive/plan-pre-europe-2026-08-15.md` remains historical; nothing in
  it is scheduled unless a later design session deliberately returns an
  item to this file.
