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
stamped. Part 2 is the draft roadmap beyond the arc — main points only,
each a future design conversation, none scheduled.

The cut is by implementation seam, not one-round-one-session (the
designlog's round names stay the design authority): session 1 is rounds
1+2's deterministic authored ground and the sky; session 2 concentrates
every derived-seed roll and every acknowledged fixture re-pin in one
sitting (round 1's harvest + round 3's census); session 3 is round 4's
trade network over that census; session 4 is round 5 — everything that
READS — plus round 4's Miners' League recovery, which is old-system
integration and belongs with the hookup.

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

# Part 1 — THE TILE ECONOMY ARC: the four implementation sessions

## Session 1 — The ground & the sky (climate + terrain)

The design is designlog 2026-08-21 (the round-1 entry) and 2026-08-21 (B)
(the round-2 entry), including the two reversals they record: climate is
HAND-PAINTED, not computed — the law is demoted to a lint — and **forest
is NOT authored** — the overlay is relief and drainage only, the wildwood
comes from climate and the deforestation law decides what survives, so
deep forest appears exactly where people are few. The authored overlays
and the eyeball tool are already in the tree
(`resources/europe_climate.txt`, `resources/europe_terrain.txt`,
`econmap.py` / `econmap.py terrain` / `potential`); **econmap.py's
constants ARE this contract's numbers** (the climate tables, and
`CLIMATE_ARABLE`, `TERRAIN_ARABLE`, `ALLUVIAL_BONUS`, `HAND_ALLUVIAL`,
`FFD`, `CLEARANCE_K`, `FOREST_CAP`, `MARSH_WOOD`, `GRAZE_CLIMATE`,
`GRAZE_TERRAIN`, the word thresholds, `HAND_MARKS`, `HAND_FOREST` /
`HAND_FOREST_CLEARANCE` — the eastern wildwood: four continental-plains
tiles east of Warsaw where clearance is capped at 0.25 because history
left the great forest standing where the law would clear it) — restated
below only where the build needs more than the tool carries. Both layers
are authored-plus-law with no rng — identical in every campaign like the
map itself — so derived seeds are moot and every existing bench is
unmoved by construction (the sky's day roll is lazy and day-seeded; no
bench reads it). The last-harvest roll is SESSION 2's; no reader surface
beyond the sky and the tile tags ships here (session 4 owns the read
surface, the snapshot arc owns cards and states). The northern-Scotland
flip (R03C04 basic→mountain) shipped with the design rounds as ordinary
dev work.

**1. The ground.** `create_geography` loads
`resources/europe_climate.txt` and `resources/europe_terrain.txt` beside
the base map and stamps `tile["climate"]` and `tile["terrain"]` with the
full words (the letters are file format only): climates tundra, taiga,
continental, oceanic, mediterranean, wet_mediterranean, steppe, desert,
nile, alpine; terrains plains, hills, marsh, mountains. `validate_world`
grows the lints' clauses — every land tile painted, sea unpainted,
alpine and mountains exactly the mountain tiles, only the legal words —
and pins the climate census (u8 t42 c83 o28 m46 w32 s24 d18 n4 a29) and
the terrain census (plains 213, hills 67, marsh 5, mountains 29) plus
the marsh five by name: the Fens R06C06, the Low Countries delta R08C11,
the Pripet pair R09C23 + R09C24, the Danube delta R11C24.

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
desert 17, nile 18, alpine none. The sky and the terrain laws below are
this session's readers of the table; the winter and harvest-day columns
are the snapshot arc's inputs, shipped now as data so that arc starts
from authority.

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
tundra rain reads "cold rain". One terrain flavor joins the re-key
(settled in round 5's design, discharging round 2's parked fen line):
on a MARSH tile, fog reads as fen fog — `WEATHER_LOCAL`'s one
terrain-keyed line; the weather LAW stays climate-only. `drought_days`
moves onto the climate profile.

**4. The laws** ship into `places.py` beside `CLIMATE_PROFILES`, computed
at worldgen per tile: arable potential = climate × terrain (+ the
alluvial bonus on river tiles and the `HAND_ALLUVIAL` Po plain; marsh
takes no bonus — marsh IS the undrained floodplain); potential wheat =
arable × the climate yield column × the ffd gradient (ffd/base);
clearance = wheat / (wheat + 0.2) — the two-pass deforestation proposal
collapsed to its closed form — capped by `HAND_FOREST_CLEARANCE` on the
`HAND_FOREST` tiles; realized arable = arable × clearance; surviving
forest = wildwood × (1 − clearance); pastoral index = climate graze ×
terrain graze. **Stored words, hidden numbers**: the tile keeps
`tile["terrain"]` (authored) and `tile["cover"]` (deep forest ≥ 0.55 /
wooded ≥ 0.25 / open); the numbers are pipeline intermediates session 2
recomputes from the same authorities, never saved.

**5. The tags — the quest-vocabulary reconciliation.** Tile and natural
Area tags become: the terrain word, the country, the positional set
(`river` + `riverside`, `coast`, `mountain-foot`, `border`, `island`),
then the derived words — `forest` (cover wooded or deeper), `farmland`
(realized ≥ 0.30), `pasture` (pastoral ≥ 0.20 and > realized), the
character climates (`steppe`, `desert`, `tundra`), plus `HAND_MARKS`
(the middle Danube's horse country). The bare biome words `basic` and
`mountain` leave the tag lists; **`mountains` is the one word for high
ground** everywhere outside `BIOME_GLYPHS` and the edge-cost rule — the
mountain-vs-mountains near-miss retires, and the quest tables' words
finally match real natural Areas (today `forest` / `hills` / `prairie` /
`pasture` / `farmland` match NO natural Area — every such job falls back
to the origin tile's countryside). Pinned tag census: farmland 128,
pasture 116, forest 101, steppe 24, desert 18, tundra 8; cover open 213,
wooded 55, deep forest 46. `prairie` is renamed `steppe` everywhere
(quests.py tables, the Tergal catalog content, the sky section above
already re-keys `WEATHER_LOCAL`); `marsh` joins the den-family quest
tables.

**6. Area naming and the natural templates.** The natural Area suffix
reads character instead of biome: sea / mountain / river keep Sea /
Mountains / Riverlands; then marsh → Marshes, deep forest → Forest,
hills → Hills, else Countryside. Natural template selection goes by
terrain + cover instead of one-template-per-biome (which currently
leaves Firascir's whole `fields` inventory dead — every basic tile draws
`old_forest`): forest tiles take the forest inventory, cleared plains
the fields, hills the hill one, marsh the fen one. New natural site
inventories owed: firascir hills (moor and glen), firascir marsh (the
fen), tergal marsh (the Pripet); Tergal's `open_prairie` becomes
`open_steppe`. The catalog natural entries' own tag lists are dead data
— drop them (writing.md register for all new content).

**7. Settlement fits.** `TILE_FIT_TAGS` grows the terrain and derived
words (`hills`, `marsh`, `forest`, `farmland`, `pasture`, `steppe`,
`plains`) and drops `basic` / `mountain` / `sea` — position stops being
the only fit vocabulary. Re-fit the templates where character now says
it better: hill_town and ridge_town fit `hills`, forest_village fits
`forest`, herd_village fits `steppe`, plus one new firascir fen village
fitting `marsh`. Template picks may shift on some tiles (the same
`slot["seed"] % n` over a better candidate list) — no compatibility, per
doctrine.

**8. Tests.** The pinned climate, terrain and tag censuses; determinism
(two worlds off different seeds carry identical climate, terrain, cover
and tags); the marsh five by name; one broken world per new
`validate_world` clause; the weight rows summing to 100 at import and
the season calendar's boundaries; the day roll reading the party tile's
climate (a med party can roll summer heat on a day the taiga could
not); the `WEATHER_LOCAL` re-key including the fen fog; the drought
counter reading the profile's `drought_days`; and the reconciliation
observable end to end — a den job landing in a genuinely wooded natural
Area, a steppe job in Tergal's grass, a marsh tag reachable — plus
every existing bench unmoved.

**Explicit non-changes** (settled, not deferred): hills cost no travel
day — the edge model stays biome-only and symmetric, every pinned
distance survives; terrain stays out of the weather LAW (climate owns
the sky; the fen-fog line above is display flavor only) and out of the
harvest contagion model.

## Session 2 — The rolled world: the last harvest & the census

The design is designlog 2026-08-21 (the round-1 entry's second sitting)
and 2026-08-21 (C) (the round-3 entry), including the direction change
it records: **real, historical and downscaled densities are abandoned**
— the tile is the unit, the rolled census IS the population, and the
tier words carry the scale. The layers and the eyeball tool are in the
tree (`econmap.py harvest [SEED]` / `harvest --sweep`, `econmap.py
population [SEED]` / `population --sweep`); **econmap.py's constants
ARE this contract's numbers**. Both layers roll at worldgen off derived
seeds, differing per playthrough on purpose (the bands and laws are
fixed, so France always feels like France; which tiles carry the towns,
and where last year failed, are each world's own). This is the arc's
one fixture-churn session: both rolls and the acknowledged re-pins land
in the same sitting.

**1. The last harvest**, rolled at worldgen off derived seeds. Stored:
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
fiction names come with session 4's read surface (settled there —
`HARVEST_CAUSE_LINES`); this session stores the cause words only.

**2. The scale doctrine** (recorded prominently — it will be asked
about). A tile is SPOKEN OF as 30 km east–west by 60 km north–south (one
travel day east–west, two north–south; 1800 km²). The drawn map
corresponds to real Europe at ~160 km per column × ~220 km per row
(~35,000 km² per tile): the height is **1.4× the width, not the 2× the
travel costs suggest** — the map is a deliberately squashed Europe, and
north–south travel is priced by the fictional 60 km, not the real 220.
By AREA the game world is ~20× smaller than the real one (5.3×
east–west, 3.7× north–south linear). Slots: **at most 4 per tile**,
thought of as a 2×2 lattice 15 km apart east–west and 30 km north–south
(twice as dense horizontally, mirroring the travel anisotropy) — a
settlement every 15–30 km is the medieval market-day spacing, and about
four is what a head can hold. Slots carry no coordinates; the lattice is
doctrine for fiction and scale statements, not a stored position.

**3. The score**, deterministic and never saved (recomputable by any
later arc, like session 1's numbers): food = realized arable +
`PASTORAL_PEOPLE` × pastoral + `FISH_COAST` on sea-adjacent tiles (else
`FISH_RIVER` on river tiles; nile counts as river); × `TRANSPORT_FACTOR`
on coast or river (a town exceeds its land's carrying capacity only with
transport); × the penalties — `MARSH_MALUS`, `HIGHLAND_MALUS`, and the
eastern-frontier malus (`EAST_MALUS_*`, columns past 22 on rows 1–13
only: the frontier is the steppe's reach, and the southern sea-lane
stripe with the Nile granary is not raider country). `HAND_DENSE` names
the authored exceptions with their reasons (the drained Low Countries
delta; the Lombardy–Veneto city belt). The score buckets into six
`BANDS`: wilderness / thin / low / mid / high / dense.

**4. The census roll**, at worldgen off derived seeds, replacing
`_population_slots` and `SETTLEMENT_DENSITY` whole (the rolled slot
census is acknowledged scaffolding; no compatibility). Per tile the band
picks a weighted ARRANGEMENT — a string over the five tiers — from
`ARRANGEMENTS`; **the variance is in the tables** (every settled band
keeps a village-only or emptier roll — ~39% of high+dense tiles roll no
town, which is what keeps rich country from reading as a town grid — and
only the dense band ever rolls a generated city). **Zero is a real
tier**: ~50 tiles of 314 roll empty. A historical tile takes its
authored tier (`HISTORICAL_TIERS`: Paris, Venice and Constantinople are
the three metropolises; the rest city or town) in slot 1 — capital flags
unchanged on Paris, Rome, Kyiv — plus companions from ITS OWN BAND's
table truncated to three, so Paris gathers towns while Stockholm stands
alone. A MINE tile seats its authored mine town the same way — tier
town, named by the mine, always free (its mining law IS its charter) —
so Falun stands alone in the wilderness band while Luneburg gathers
villages. The `MINES` table (nine authored mines with their towns and
goods) lands in `places.py` THIS session as data for the seating;
session 3 gives it its whole trade reading. Slots sort chief-first
(`TIER_ORDER`). Measured over 500 seeds: ~615 settlements (3 metropolis,
~18 city, ~101 town, ~402 village, ~92 hamlet), ~1.96 slots per land
tile, world ~1.3M souls.

**5. The tier vocabulary** grows to five words: **hamlet** (under a
hundred souls), **village** (hundreds), **town** (thousands), **city**
(tens of thousands), **metropolis** (a hundred thousand and more —
"supercity" is dev slang only). The headcounts are fiction anchors for
the DM, never stored numbers. Mechanical mapping: **every
`settlement_tier`-keyed table grows the five words** — city and
metropolis take the capital-grade rows (`quests.SETTLEMENT_KINDS`,
conquest's `TRIBUTE_PER_DAY` / `GARRISON_CAP` / `GARRISON_BANDS` /
`RAID_STRENGTH`), hamlet takes the village's rows and service gates
except tribute halved (6 g/day — a hamlet is barely worth holding);
`BOARD_ACTIVE_CHANCE` extends to metropolis/city 1.0, town 0.6, village
0.25, hamlet 0.05. The map glyph ladder stays ASCII — `C` for
city-grade (metropolis, city, capital — the legend distinguishes), `T`
town, `v` village, hamlets NOT drawn on the map (tile detail lines
only); the uniform start draw excludes hamlets. **The recruit pool
reads the tier** (settled in round 5's design): `roll_recruits` caps
the day's candidate OPTIONS by the settlement — hamlet 1, village 2,
town and above the full CHA capacity — a hamlet is not a hiring market.

**6. Content owed** (writing.md register): a `hamlet` role and a `city`
role per country in the catalog (`TILE_FIT_TAGS` fits per session 1's
vocabulary; the hamlet minimal — a well, a shrine, no board sites);
metropolises cut from the city role until the Settlements-revisited
round gives them their own; hamlet naming (own small pools with a
humbler sound, or the village reserve) and a modest village-pool
growth — naming is lazy at materialization, so pools need to cover play,
not the census.

**7. The charter and the manor**, one stored word each, rolled with the
census and read by nothing yet (the politics arc owns the read surface):
cities and metropolises always hold a **charter** (`free`), a generated
town does at `CHARTER_CHANCE` (1 in 3; an unchartered town is a lord's
town), and a village-led tile of two or more settlements seats a
resident lord at `MANOR_CHANCE` (1 in 2) — the manor mark on its chief
village.

**8. Tests.** The harvest: regions contiguous, the sweep distribution
pinned (~17% mean problem coverage, never zero), the drought always,
the save round-trip. The census: the sweep distribution pinned
(settlement counts per tier, slots per tile, empty-tile count, the
quiet-rich-country share never zero); slot cap 4 and legal tier words
as `validate_world` clauses; the historical tiles carrying their
authored tiers and the capital set unchanged; the mine towns seated by
name; derived seeds (each roll identical when unrelated layers roll);
the keyed tables covering all five words; the recruit cap; and the
acknowledged fixture re-pins — the quest-geography and places fixtures
that pinned the old slot rolls find new seeds, per the no-compatibility
doctrine. Every existing bench unmoved (derived seeds).

**Parked here, still**: the past-epidemic population scar (the snapshot
arc's plague chain); named natural regions (take if cheap, later); the
charter/manor readers and what freedom is worth (the politics arc);
hamlet/metropolis detail (Settlements revisited).

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

- **The last-harvest roll ships with session 2** (settled early,
  designlog 2026-08-21: contiguous cause-carrying problem regions, the
  contagion model). This arc KEEPS: the **last-winter roll** for pastoral
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
  continuations of the routes session, none scheduled.
- Fogging the base terrain map. Diagonal movement.
- Watch in play: a companion quitting mid-career is much harsher on the
  fixed map (closure note, unchanged — the wound and satisfaction tracks
  are behaving as designed; the road is just genuinely long now).
- `archive/plan-pre-europe-2026-08-15.md` remains historical; nothing in
  it is scheduled unless a later design session deliberately returns an
  item to this file.
