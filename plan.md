# The roadmap

This is the sole active roadmap and build contract. **Nothing implemented
lives here** — when a session ships, its contract is deleted and the result
is written to the permanent docs (`rules.md`, `dm.md`, `develop.md`,
`benchlog.md`) and the build record to `designlog.md`. See develop.md's
"Where a finished feature is written up".

The fixed Europe map is **BUILT** (2026-08-15, five sessions; designlog
2026-08-15 and develop.md hold the pointers). What is queued now is **THE
TILE ECONOMY ARC** (Part 1) — a chain of **design rounds, not
implementation sessions** (2026-08-20, designlog): each round settles its
spec in full — vocabularies, laws, tables, numbers — so that the
implementation afterward is trivial. When a round's design settles, its
entry here is REPLACED by the implementation contract it produced; when
that ships, the contract is deleted as usual. Part 2 is the draft roadmap
beyond the arc — main points only, each a future design conversation, none
scheduled.

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

---

# Part 1 — THE TILE ECONOMY ARC (climate, terrain, economy, population)

## Round 1 — Climate: the implementation contract (design settled 2026-08-21)

The design is designlog 2026-08-21 (including the reversal it records:
climate is HAND-PAINTED, not computed — the law is demoted to a lint).
The authored overlay and the eyeball tool are already in the tree
(`resources/europe_climate.txt`, `econmap.py`); **econmap.py's constants
ARE this contract's numbers** — the tables live there and ship from
there, restated below only where the build needs more than the tool
carries. Derived seeds throughout; no reader surface beyond the sky
(round 5 owns the read surface, the snapshot arc owns cards and states).

**1. The ground.** `create_geography` loads
`resources/europe_climate.txt` beside the base map and stamps
`tile["climate"]` with the full word (the letters are file format only):
tundra, taiga, continental, oceanic, mediterranean, wet_mediterranean,
steppe, desert, nile, alpine. `validate_world` grows the lint's clauses —
every land tile painted, sea unpainted, alpine exactly the mountain
tiles, only the ten words — and pins the climate census (u8 t42 c83 o29
m46 w32 s24 d18 n4 a28).

**2. The label table**, a `CLIMATE_PROFILES` table in `places.py`
replacing `ENVIRONMENT_PROFILES` (the five old profiles and the
catalog's per-country `environment` key retire as scaffolding). Columns
per climate — frost-free days, wheat-yield multiplier, winter severity
0–3, harvest day, `drought_days`:

| climate | ffd | yield | winter | harvest day | drought_days |
|---|---|---|---|---|---|
| tundra | 60 | 0 | 3 | — | 20 |
| taiga | 100 | 0.3 | 3 | 125 | 15 |
| alpine | 90 | 0.15 | 3 | 125 | 15 |
| continental | 170 | 1.0 | 2 | 100 | 18 |
| oceanic | 220 | 1.0 | 1 | 110 | 15 |
| mediterranean | 270 | 0.8 | 0 | 50 | 30 |
| wet_mediterranean | 300 | 1.3 | 0 | 45 | 25 |
| steppe | 160 | 0.5 | 3 | 90 | 25 |
| desert | 330 | 0.05 | 0 | — | 40 |
| nile | 330 | 1.5 | 0 | 40 | 40 |

The latitude gradient: ffd(tile) = base + 8 × (row − reference row),
clamped to base ± 40; reference rows tundra 2, taiga 4, oceanic 8,
continental 8, steppe 10, mediterranean 13, wet_mediterranean 17,
desert 17, nile 18, alpine none. Only the sky columns have a reader this
round — ffd/yield/winter/harvest-day are rounds 2–3 and the snapshot
arc's inputs, shipped now as data so those rounds start from authority.

**3. The sky** (absorbs the deferred "seasonal or Tile-specific weather
profiles" item whole). A season CALENDAR, not a season track: day 1 =
April 1st; spring days 1–60, summer 61–150, autumn 151–210 (autumn
reuses spring's weights), winter 211–360; `season_of(day)` is a lookup
and nothing else reads it. Weather weights become per climate × season —
the settled tables, per hundred days over the nine words in the order
clear / cloud / wind / rain / storm / fog / frost / snow / heat (each
row sums to 100; autumn = spring; nile shares desert's sky):

| climate | spring | summer | winter |
|---|---|---|---|
| oceanic | 20/26/12/26/4/8/4/0/0 | 30/24/10/24/6/4/0/0/2 | 12/30/16/24/6/6/5/1/0 |
| continental | 26/22/12/20/5/5/8/2/0 | 34/16/8/18/10/2/0/0/12 | 16/22/10/4/2/6/22/18/0 |
| taiga | 18/24/10/16/3/10/12/7/0 | 28/22/8/22/5/8/4/0/3 | 14/20/10/0/2/6/26/22/0 |
| tundra | 16/20/22/6/4/8/14/10/0 | 22/22/16/14/4/10/8/4/0 | 12/16/22/0/6/4/20/20/0 |
| alpine | 18/20/18/12/6/8/10/8/0 | 26/18/14/16/10/6/6/4/0 | 14/16/16/0/6/6/20/22/0 |
| mediterranean | 34/14/14/18/4/4/2/0/10 | 48/8/12/4/4/2/0/0/22 | 24/20/14/30/6/4/2/0/0 |
| wet_mediterranean | 32/14/12/24/4/4/0/0/10 | 42/10/10/12/6/2/0/0/18 | 26/18/12/32/6/4/0/0/2 |
| steppe | 28/12/24/14/6/2/10/4/0 | 38/8/20/8/8/0/0/0/18 | 18/14/22/2/4/2/22/16/0 |
| desert, nile | 52/6/18/4/2/2/2/0/14 | 50/2/14/0/2/0/0/0/32 | 50/10/16/6/2/4/8/0/4 |

The day roll takes its weights from the party's
CURRENT TILE's climate and the season instead of the land's environment;
still one sky per land per day, and the wet/dry counters, the drought
bend, cards' own skies and bought skies are untouched. `WEATHER_LOCAL`
re-keys by climate: alpine keeps the snowstorm rows, steppe inherits
prairie's wind line, desert's storm reads "a dust storm", taiga and
tundra rain reads "cold rain". `drought_days` moves onto the climate
profile.

**4. The last harvest**, rolled at worldgen off derived seeds. Stored:
`tile["harvest"]` (an int percent) and `tile["harvest_cause"]`, plus the
region records (cause, center, member tiles) on the world — the
addresses the snapshot arc will wire. The scale: 100 = a full excellent
harvest; 110–120 legendary, 95–109 excellent, 75–94 ordinary, 55–74
poor, 35–54 failed, below 35 apocalyptic; a PROBLEM tile is below 75.
The method and every constant are `econmap.py`'s `roll_harvest`: 4–6
regions, centers seeded by `CENTER_WEIGHT` with 4+ tiles separation,
cause drawn per center climate (`CAUSES`), contagion growth by ring
(`SPREAD` × `SUSCEPTIBILITY`), severity 30–65 at the core softening 6
per ring ± 8 clamped 25–74, a fine year elsewhere (gauss 90/9 clamped
75–120, 3% legendary tail). Two guarantees: at least one DROUGHT region
per world (the most drought-apt center re-causes), and the NEARBY
TROUBLE nudge — if no region center lies within 5 path-days of the start
tile, relocate the last-rolled region to a `CENTER_WEIGHT`-weighted tile
inside that radius with chance 3 in 4, re-drawing its cause from the new
climate before growth (measured on raw rolls: trouble within 6 days of
the start in only ~52% of worlds; the nudge lifts the played posture to
~88% — the campaign usually opens in or beside a bad year, and the
genuinely quiet start survives at about one world in eight). The causes'
fiction names (writing.md register) come with their first read surface,
not now. Tests: regions contiguous, the sweep distribution pinned (~17%
mean problem coverage, never zero), the drought always, the save
round-trip, and every existing bench unmoved (derived seeds).

## Round 2 — Terrain & the land's potential

The hand-authored overlay is what nature put there — forest, hills, marsh
(the vocabulary is the round's first job). **Farmland is not authored**:
it is population's footprint, resolved by the deforestation law below.

- Per tile: **arable potential and potential wheat yield**, by rule from
  climate + terrain + river (alluvial bonus), hand-tuned where the rule
  reads wrong.
- **The deforestation law** (the named gap): how much of its arable
  potential a tile REALIZES. **[remark]** Proposal: realized arable =
  potential × clearance(population pressure), solved in two passes —
  provisional population off raw potential, clearance off that
  population, final forest = authored forest − cleared. Deep forest then
  survives exactly where people are few, which is the wilderness the game
  wants.
- **Herding is the complement, not a second authored layer**: pastoral
  share is what habitable land does where arable potential is low — the
  steppe, the hills, the highland margins, dry country. Tergal reads
  pastoral by climate law with no hand-picking; hand-mark exceptions only
  where character demands one (horse country, a transhumance corridor).
- **Reconcile the quest tables' terrain vocabulary** — `forest` / `hills`
  / `prairie` / `pasture` / `farmland` — absorbing the deferred sub-biomes
  item whole, including the `mountain`-vs-`mountains` near-miss and
  something better than `coast` / `riverside` / `mountain-foot` for the
  settlement templates to fit against.

## Round 3 — Population & the settlement census

Population per tile, a **hidden number**, from the ground up:

- **The law**: base = realized arable × climate factor, plus pasture at a
  lower weight and fishing on coasts; a **transport bonus** on rivers and
  coasts (towns exceed local carrying capacity only with transport); then
  the **penalties** — frontier insecurity, marsh disease, highland.
- **Scale anchoring**: the world is smaller than the real thing — settle
  what a population number means and the village / town / city
  thresholds.
- **Calibration by retrodiction**: the authored historical towns are the
  answer key. Tune the law until the density map lights up where the
  cities already are; where it will not, either fix the law or author an
  exception and write down why.
- **The census table**: population → settlement count and tier per tile.
  Dense urban = several towns and a village; prosperous countryside =
  four villages; remote = one village; **zero is a real tier** (steppe,
  deep forest, high massif — authored wilderness). About four settlements
  is the ceiling a player and DM can hold in the head for one tile.
- This **replaces the rolled slot census**, acknowledged as scaffolding
  (2026-08-20). No compatibility — the doctrine is standing.
- **Parked here**: the past-epidemic population scar (a region's number
  cut by a plague that already happened — colour now, and the plague
  chain's geography later). Named regions may fall out of the density and
  terrain clusters (the deferred "named natural regions" item) — take the
  win if it is cheap, park it if not.

## Round 4 — Resources, trade goods & routes

- **Mines: authored by hand, semi-historically, few and famous** — the
  silver of the eastern hills, mountain iron, salt; the list is the
  round's work. The mining-town rule: a mine town exceeds its land's
  carrying capacity and imports food — which creates a route and a
  vulnerability in one stroke. The empty `worldsim.STATE_SLOTS` deposit
  slot (parked by the Europe closure) returns to service here with the
  extraction chain a real mine re-homes.
- **Trade goods: sparse authored colour**, one good word per notable tile
  or region — furs, timber, honey, wax, amber, herring, wool, wine, oil.
  **[remark]** Keep the exotics — spices, silk, jewels — OFF the map:
  they enter along the legendary routes from the frame edges, which is
  exactly what makes those routes worth taxing, robbing and fighting
  over.
- **Routes: derived plus authored.** The ordinary network is computed —
  the existing pathfinder run between surplus regions and populous or
  deficit ones, `trade-route` stamped on the tiles crossed with a traffic
  weight. The legendary ones are authored: the Tergal silk road entering
  at the eastern frame edge, the southern sea lane to the fertile stripe,
  an amber road (the list to settle). Sea legs need their route rule —
  the pathfinder already sails.
- Route tiles are **addresses for later arcs** — inns, tolls, banditry,
  smuggling, plague walking the network in from a port. This round stamps
  tags and traffic; it wires nothing.

## Round 5 — The hookup (the read surface)

The vaguest round on purpose; its design session settles what the game
READS off the new ground. Candidates, from cheap upward:

- **Tile detail lines and the map page speak the tile's character** —
  grain country, drove road, silver town — the writing.md register laid
  over the tile's facts; the DM gets the tile's facts the way `lore`
  serves the land's.
- **Existing systems reading population**: board activity derived from
  the tile instead of the hand-set `BOARD_ACTIVE_CHANCE` roll; recruit
  pools; price nudges. The round decides the minimum set.
- **Storage and wiring**: where each layer lives (an authored overlay
  resource beside `europe_map.txt`, computed tables in `places.py` — to
  settle), worldgen kept derived-seed clean, `validate_world` clauses per
  layer, a `bench_worldgen`-style suite pinning the distributions the
  rounds tuned, and the render script kept as the standing eyeball.
- **Explicit non-goals, so the arc stays this arc**: no trouble score, no
  forward simulation, no card changes — the cards gain their geography in
  the snapshot arc.

---

# Part 2 — The roadmap draft beyond the arc

Main points only. Each is a future design conversation; nothing here is
scheduled or specified.

## The spring snapshot & trouble arc (the natural next)

- **The last-harvest roll ships with round 1** (settled early, designlog
  2026-08-21: contiguous cause-carrying problem regions, the contagion
  model). This arc KEEPS: the **last-winter roll** for pastoral country
  (fodder, herd losses, animal disease, wolves and monsters at the herd's
  edges — reading the climate table's winter column, and the great-rains
  regions doubling as murrain country, 1315-style); the READING of both
  rolls (states, prices, trouble); and the harvest-day consequences (the
  day the new harvest replaces last year's story — this year's harvest
  stays unwritten until then, the shipped weather tracks its story).
  Spring is the hungry gap: the snapshot the party walks into is the
  year's maximum tension.
- **Organic distribution**: round 1's seeded contagion (centers, causes,
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
makes wantable.

## Small deferred leftovers (from the Europe build, still true)

- Roads and road quality; bridges, mandatory river tolls and ferries;
  ports, owned ships, passage prices and naval encounters — natural
  continuations of the routes round, none scheduled.
- Fogging the base terrain map. Diagonal movement.
- Watch in play: a companion quitting mid-career is much harsher on the
  fixed map (closure note, unchanged — the wound and satisfaction tracks
  are behaving as designed; the road is just genuinely long now).
- `archive/plan-pre-europe-2026-08-15.md` remains historical; nothing in
  it is scheduled unless a later design session deliberately returns an
  item to this file.
