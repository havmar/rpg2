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

## Round 1 — Climate

Every tile receives a **climate property, computed by law** from position
and terrain — no hand-picking, only a short authored exception list where
the law reads wrong. The inputs the law has: latitude (growing season,
winter severity), distance from the western ocean (continentality — wider
variance, harsher winters), mountains (highland), the southern coast
(mediterranean: winter rain, summer drought — its bad year is a *dry*
year), and the Africa stripe (rows 17–18) as the fertile southern band.

To settle in the round:

- The **climate vocabulary** itself — how many words, their names.
- The **numbers each word carries**: growing season / yield multiplier,
  **variance** (the column the snapshot arc will later roll against),
  winter severity, and a weather profile (per-environment day-roll weights
  plus `drought_days`), so the sky can be rolled off the TILE rather than
  the country. This absorbs the deferred "seasonal or Tile-specific
  weather profiles" item whole.
- The **Africa stripe's treatment**: river-fed granary — high yield and
  LOW variance, because the reliability is its character as much as the
  fertility (the south's grain buffer, a strategic prize, the reason the
  sea lanes matter) — and whether its river is authored into
  `resources/europe_map.txt` itself (row 18 is plain `#` today).
- **[remark]** The arc's tooling: a standalone, stdlib-only pipeline
  script in the `archive/worldmap.py` manner that renders every layer as
  a 30x18 ASCII overlay — climate now; fertility, population, routes as
  later rounds land. Every later round is eyeballed against these maps,
  so the tooling belongs to the first round, not the last.

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

- **Two worldgen rolls: last harvest and last winter.** Arable country
  reads the harvest roll (the grain stores); pastoral country reads the
  winter roll (fodder, herd losses, animal disease, wolves and monsters
  at the herd's edges) — two countries' bad years are different dice by
  construction. Spring is the hungry gap: the snapshot the party walks
  into is the year's maximum tension, and this year's harvest stays
  unwritten — the shipped weather tracks are its story.
- **Organic distribution by multi-scale rolls**: a country/season term, a
  region term, per-tile jitter — never everything-everywhere, never one
  needle. Margins amplify variance: rich cores rarely fail, the edges
  often do.
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
