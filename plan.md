# The Fixed Europe Map — implementation contract

This is the sole active roadmap. The 2026-08-15 design sessions replace the
former world with a fixed 30x18 Europe-shaped grid inhabited only by humans.
The Human World Contraction is implemented and documented in `rules.md` and
`designlog.md`; the former roadmap is preserved, explicitly
inactive, in `archive/plan-pre-europe-2026-08-15.md`.

Four implementation sessions remain. A future session may be
started simply by asking to implement its exact title:

1. **Fixed Europe Geography**
2. **Grid Navigation and Map UI**
3. **Local Quest Geography**
4. **Europe MVP Closure**

Implement them in order. Each session must leave its own slice coherent and
tested; do not begin a later session as an incidental extension of an earlier
one. No save compatibility is required. Fresh worlds are the only supported
worlds after every slice.

When a session ships, remove its implementation section from this file and
write the result to the normal permanent homes: the played rule and design
spine in `rules.md`, play protocol in `dm.md`, code map in `develop.md`,
measured results in `benchlog.md` where relevant, and the decisions and build
record in `designlog.md`. Keep only the unbuilt contract here. Shared clauses
which later sessions still need may remain until their final consumer ships;
replace already-built detail with a short pointer to its permanent owner.
After verification, always commit the completed session to git before
reporting it done.

---

## Goal and MVP proof

The party should inhabit the ASCII map in `resources/europe_map.txt`, not a
list of disconnected place names. A successful MVP demonstrates this whole
loop in a fresh game:

1. Build the same fixed 30x18 geography for every world seed.
2. Roll population and lazy names deterministically from the world seed.
3. Begin in a uniformly random settlement anywhere in the world.
4. Show the terrain, known settlements, quest target and party position on a
   40-column map.
5. Move orthogonally through basic, river, mountain and sea tiles, including
   travel to every disconnected landmass.
6. Reveal and enter natural and settlement Areas within a tile.
7. Hear about work in known settlements no more than three travel days away.
8. Take an ordinary quest whose target is no more than three travel days from
   its origin, travel there, clear it and return within its path-priced clock.
9. Save, load and revisit without rerolling geography, density, names,
   discovery, paths or place contents.
10. Generate no dwarf, elf, goblin or orc person, country, army, quest giver,
    foe skin or player-facing label.

The MVP does not require roads, seasons, ships as inventory, ports as travel
gates, naval combat, named rural regions, detailed variants of `basic`,
dynamic national borders, tile conquest, or megacities which erase all
nature. Those are refinements after this build has been played.

---

## Settled vocabulary and hierarchy

The canonical spatial hierarchy becomes:

`Country -> Tile -> Area -> Site -> Room`

- **Country** is the political and cultural macro layer. The three countries
  are Firascir, Mortellaria and Tergal. A country owns world-simulation state,
  a culture and name pools. `owner` remains distinct from geographical
  country where conquest needs it.
- **Tile** is one fixed map cell and the day-scale travel node. It owns its
  row, column, biome, country, display name, discovery state, neighboring
  tile IDs, settlement slots and child Area IDs.
- **Area** is a local destination within a tile. Natural and settlement Areas
  are siblings. Every tile has at least one Area. A populated tile may have a
  natural Area, one town Area and two village Areas at once.
- **Site** and **Room** keep their current scale and persistence rules. Local
  movement inside an Area remains free; switching between Areas in one tile
  is also free.

The old statement that a tile is an Area is rejected. The old finite set of
28 authored natural Areas and the list-shaped Land adjacency graph do not
survive as world geography.

### Stable IDs and names

- Coordinates are 1-based in every player-facing surface. Row 1, column 1 is
  the upper-left map cell.
- Tile IDs are `tile/rRR/cCC`, zero-padded to two digits, for example
  `tile/r09/c18`.
- A coordinate tile's display name is `R09C18`.
- A historical-city tile uses the historical city as its display name.
- Names never form Tile IDs. Settlement, Site and Room IDs are scoped under
  the Tile/Area record so exhaustion placeholders and duplicate-looking
  names cannot collide.
- Internal algorithms may use zero-based array indexes, but record fields,
  error messages, commands and displays use the 1-based convention.

### Minimum Tile record

The saved Tile record must carry at least:

- `id`, `row`, `column`, `name`;
- `country`, `biome`;
- `known`, `visited`;
- `neighbors` as cardinal Tile IDs;
- `areas` as child Area IDs;
- `natural_area` as the natural Area ID;
- `settlement_slots`, including unmaterialized slots;
- derived tags needed by placement (`coast`, `riverside`,
  `mountain-foot`, `border`, `island`);
- a stable derived seed or enough stable parent identity to derive one.

The world record gains a `tiles` store and a row-major `tile_order`. Country
records gain their Tile IDs. Area records gain `tile`; position gains `tile`
while retaining `area`, `site` and `room` breadcrumbs.

---

## Fixed map loading and political division

`resources/europe_map.txt` is authored source data. World generation loads
and validates it; it never edits or procedurally replaces it.

Hard validation:

- exactly 18 rows;
- exactly 30 characters per row;
- only `.`, `#`, `^` and `~`;
- no blank lines inside the grid;
- the checked-in file is read as ASCII/UTF-8 text;
- validation errors identify the row and column.

Biome mapping:

| Glyph | Biome | Meaning in the MVP |
|---|---|---|
| `.` | `sea` | Navigable open water; never populated |
| `#` | `basic` | Generic inhabitable land; detail postponed |
| `^` | `mountain` | Inhabitable only by villages unless authored |
| `~` | `river` | Ordinary inhabitable land containing a major river |

Country assignment applies to sea and land alike, with row precedence:

1. Rows 11 through 18 belong to Mortellaria.
2. Otherwise, columns 1 through 21 belong to Firascir.
3. Otherwise, columns 22 through 30 belong to Tergal.

The resulting non-sea census is a pinned fixture:

| Country | Basic | Mountain | River | Non-sea total |
|---|---:|---:|---:|---:|
| Firascir | 81 | 11 | 5 | 97 |
| Mortellaria | 117 | 15 | 12 | 144 |
| Tergal | 68 | 3 | 4 | 75 |

The complete grid has 266 basic, 29 mountain, 21 river and 224 sea tiles.
Tests must pin these counts so an accidental map edit cannot silently move
the generated world.

### Derived Tile tags

- A river tile receives `river` and `riverside`.
- A tile merely adjacent to a river does not receive `riverside`; a tile is
  30x60 km and adjacency is too far away for that identity.
- A non-sea tile adjacent orthogonally to sea receives `coast`.
- A non-sea tile adjacent orthogonally to mountain receives
  `mountain-foot`.
- A tile adjacent orthogonally to another country receives `border`.
- Every non-sea component other than the 302-tile mainland receives
  `island`. The checked-in map has land-component sizes 302, 11, 2 and 1.
- Every tile receives its biome and country as tags.

---

## Areas inside Tiles

Every Tile receives exactly one natural Area at world creation in the MVP.
This includes sea and historical-city Tiles. A 30x60 km city Tile still has
substantial surrounding country.

Natural Area subtype follows the Tile biome. Its initial plain display name
is derived from the Tile:

- `R09C10 Countryside` / `Paris Countryside` for `basic`;
- `R03C17 Mountains` for `mountain`;
- `R08C12 Riverlands` / `Amsterdam Riverlands` for `river`;
- `R01C01 Sea` for `sea`.

These names are functional first-pass labels, not new proper-name pools.
`basic` receives no forest/plain/farmland roll yet. Natural Site selection
may read the derived Tile tags, but it must not pretend an adjacent river is
locally present.

The record shape permits zero natural Areas for a future authored megacity,
but no MVP definition uses that exception.

Switching between known Areas in the current Tile costs no day. The existing
`go`/`back` Site and Room behavior remains below the Area floor; add the
smallest explicit command or `go` extension needed to choose a sibling Area.

---

## Population, historical cities and lazy settlement materialization

Population is a stable world-seed result over fixed Tiles. It is not rerolled
on discovery, visit, board read, or save load.

### Ordinary density table

Historical-city Tiles are excluded from the ordinary roll. Sea always has no
settlement. Other non-sea Tiles roll:

| Country | Town + 2 villages | 1 village | No settlement |
|---|---:|---:|---:|
| Mortellaria | 10% | 35% | 55% |
| Firascir | 6% | 24% | 70% |
| Tergal | 3% | 17% | 80% |

On a mountain Tile, a rolled `town + 2 villages` result is downgraded to one
village. Authored historical settlements may override this rule.

The roll creates lightweight `settlement_slots`, not full Areas. A dense
Tile has one `town` slot and two `village` slots; a village Tile has one
`village` slot. Each slot stores its tier, authored name if any, capital
flag, materialized Area ID if any, and stable seed identity.

Ordinary settlement Areas, required Sites, Rooms, services, providers,
boards and garrisons materialize only when something needs that settlement:

- it is selected as the starting settlement;
- the party enters and reveals its Tile;
- a specific quest or world event needs the slot;
- the DM explicitly invokes the existing found/materialize tool.

Materialization consumes an existing slot. It never turns a no-settlement
Tile into a populated Tile and never exceeds the Tile's rolled density.
`found_settlement` therefore changes from drawing an unbounded Land reserve
to selecting an unused fitting slot. If no fitting slot remains, it returns
no settlement and the requesting content does not fire, preserving the
current finite-world discipline.

### Settlement kinds and capitals

- Settlement subtype remains `town` or `village`.
- There is no `city` subtype.
- A national capital is a town with `capital: true`.
- Capital-specific services, board band, conquest band and ruler placement
  read the flag rather than a `capital` subtype.
- A historical non-capital city is mechanically an ordinary town.

### Authored historical city overlay

The first historical overlay is fixed data:

| Tile | Settlement | Country | Biome | Capital |
|---|---|---|---|---|
| R05C02 | Dublin | Firascir | basic | no |
| R06C05 | London | Firascir | basic | no |
| R08C12 | Amsterdam | Firascir | river | no |
| R09C10 | Paris | Firascir | basic | yes |
| R09C18 | Prague | Firascir | basic | no |
| R03C23 | Stockholm | Tergal | basic | no |
| R07C28 | Moscow | Tergal | basic | no |
| R08C22 | Warsaw | Tergal | basic | no |
| R10C27 | Kyiv | Tergal | river | yes |
| R13C03 | Lisbon | Mortellaria | river | no |
| R13C07 | Madrid | Mortellaria | basic | no |
| R12C14 | Venice | Mortellaria | river | no |
| R14C14 | Rome | Mortellaria | basic | yes |
| R14C19 | Athens | Mortellaria | basic | no |
| R14C27 | Constantinople | Mortellaria | basic | no |
| R17C12 | Carthage | Mortellaria | basic | no |

Each historical Tile has the dense three-slot shape. Its named town exists
and is known at world creation. Its two villages remain unnamed,
unmaterialized and unknown until needed. The Tile and its named town use the
same historical name.

### Ordinary settlement naming

Coordinate Tiles never rename themselves after settlement materialization.
A generated Belafonte within `R11C20` leaves the Tile named `R11C20`.

Each country has separate town and village reserves. Reserves are shuffled
once with a stable derived seed, consumed lazily without replacement and
saved. Historical names do not consume them. When a pool is exhausted, use
separate persisted counters:

- `Firascir Town 1`, `Firascir Village 1`;
- `Mortellaria Town 1`, `Mortellaria Village 1`;
- `Tergal Town 1`, `Tergal Village 1`.

Initial town pools:

- Firascir: Tomburgh, Leehaven, Walhaven, Bradwhitchip, Redflurton.
- Mortellaria: Castavera, Portomera, Belafonte, Montaro.
- Tergal: Ulus-Gal, Kharuk, Temenur, Ordubal.

Initial village pools:

- Firascir: Sturford, Ackham, Flurham, Sturham, Sturworth, Newton, Midton,
  Aston, Tomton, Walham, Coldcot, Thornley, Blackton, Astmoor, Ackbridge,
  Ackton, Mickleham, Shepham. The last fifteen are the older design pool in
  `placegen.md`; they were omitted from the shipped catalog only because the
  implementation fixed Firascir to three village records.
- Mortellaria: Alavera, Beloro, Calavento, Doramonte, Fontela, Lunaro,
  Maravento, Oliveta, Rosavera, Sanoro, Solavela, Toralba, Valesero, Ventoro,
  Vilaro.
- Tergal: Aradun, Balurun, Borkal, Enkhar, Eshkar, Guratai, Kharnam,
  Kurugan, Namuruk, Ordaki, Sargul, Teguren, Tumengal, Urkhal, Zamutar.

Reuse the surviving country settlement skeletons and livelihood overlays as
templates, not as fixed geography. A generated settlement chooses a fitting
country/tier role deterministically. Tergal's templates are humanized but
retain steppe, herd, river, basin and clan material.

---

## Discovery, knowledge and the random opening

Terrain and country partition are common knowledge from the start. The base
map is never fogged.

- Historical towns are known from day 0.
- An ordinary Tile's settlement result is hidden until the party enters it,
  a quest explicitly reveals it, or a specific rumor reveals it.
- Entering a Tile reveals its natural Area and materializes/reveals all
  settlement slots in that Tile. This is a bounded maximum of three
  settlements and prevents a later revisit from changing the local census.
- Natural Sites remain lazy under their natural Area.
- Quest-specific Sites remain lazy and persistent as now.

### Uniform random starting settlement

The start is uniform over settlement slots, not over countries or populated
Tiles:

1. Roll and store the whole world's lightweight settlement slots.
2. Include every historical town and every ordinary town/village slot.
3. Choose one slot uniformly with the worldgen RNG/derived start stream.
4. Materialize it and reveal its Tile.
5. Make that settlement ordinary-board-active regardless of its prior board
   roll.
6. Force one suitable combat opening quest there.
7. Set the PC's homeland to that settlement's country.

Starting in a capital, historical town, generated town or remote village is
legal. The settlement must have the minimum services the current opening can
depend on. Starting level selection remains unchanged.

---

## All-human world and cultural identity

All people are human. Dwarves, elves, goblins and orcs are removed as playable
characters, companions, NPCs, countries, armies and foe presentations.
There is no retained `race: human` compatibility field.

The surviving countries are:

- **Firascir** — human temperate culture;
- **Mortellaria** — human Mediterranean culture;
- **Tergal** — human steppe/clan culture.

Tergal keeps its current identity except for species claims. Its clans,
horses, herding, confederacy, chiefs, clan mothers, outlaws, shamans, Sky
religion, weather work, warbands, names and settlement material remain.
Replace `orc` according to context with `Tergal`, `clan`, `warband`,
`warrior`, or no modifier. Do not flatten Tergal into the Firascir human
baseline.

### Character and NPC contract

- Replace `race` on characters with `homeland` where cultural identity is
  needed.
- Remove racial floor/ceiling stat modifiers and race-specific trait
  substitutions.
- Remove `--race`; do not replace it with a required chargen choice.
- The PC's homeland is the starting settlement country.
- Recruits use the country of the settlement where they are generated in the
  first pass. Bonded pairs share a homeland where the relationship currently
  requires a shared race.
- `patriotic` compares homeland to current country.
- Side-person and enemy names use homeland/culture, never species.
- Firascir and Mortellaria initially share the existing human personal-name
  pool. Tergal reclassifies the present orc personal-name pool as Tergal
  human names.
- NPC records carry `homeland`, `sex`, `age`, `role` and optional level.
  Player-facing lines may say `Tergal man` or `woman from Tergal`; they never
  say `human` as though it distinguished a species.

### Quest, encounter and conquest content

- Quest tables route by country/culture rather than race.
- Firascir and Mortellaria may share the calibrated human chassis while
  retaining different names, settlement templates and world packets.
- Tergal adapts the current orc quest material into human clan/warband
  material. Enemy stat rows stay calibrated; only invalid species skins and
  text change.
- Delete elf, goblin and dwarf quest-table branches and cultural ladder
  variants. Species-neutral monsters such as wolves, undead, ogres and trolls
  remain unless a string explicitly presents one of the removed peoples.
- Conquest uses one human garrison pool. Defender roles vary by country or
  settlement tier, not race.
- Karma/law/Hell posses use the current country for names and presentation,
  not `land_race`.
- The gunner mechanics, hand bombard and weapon generation remain.
  References to dwarf invention, dwarf-only shelves or dwarf smiths are
  replaced with ordinary gunsmith/master-smith content.

### Country-based conquest story

The war story chooses an aggressor country other than the PC's starting
country. It has three variants:

- **Firascir: the Golden Empire.** Adapt the current elf Golden Empire into
  a human imperial project using soldiers, engineers, industry and war
  machines. Remove every elven biological or racial claim.
- **Mortellaria: the Undead Kingdom.** Keep the existing human dark-kingdom
  variant, routed specifically through Mortellaria.
- **Tergal: the Iron Horde.** Adapt the current orc variant into human Tergal
  clans united by a war leader. Preserve horses, warbands and clan politics;
  remove orc species language.

The goblin Thousand Workshops variant is removed. Story faces draw names from
the aggressor country's human pool. Victim selection, occupation and wave
levels remain, but settlement and quest placement must ultimately use Tiles
and path distance.

### Three-country world simulation

Delete Ensimaa, Dvarvengrond and Gibili constitutions, tensions, factions,
cards, facts, options and relations. Keep Firascir and Mortellaria packets.
Humanize Tergal's packet without removing its clan and shaman content.

Rebuild the minimum directed relation set among the survivors:

- Firascir exports grain and timber;
- Mortellaria exports coin, luxury goods and southern trade;
- Tergal exports horses, livestock and military service.

Use existing states and card chains where they still tell the truth. Every
derived state must still have an authored cause, every relation must point to
real countries, and every country must retain valid economy, weather,
politics, religion/magic and ruler layers. Country climates remain the MVP
weather source even while the party is on sea or mountain Tiles; Tile-level
climate overrides are postponed.

Runtime content, active docs and tests must stop describing Tergal as orc or
the removed countries as present. Historical records in `designlog.md`,
`placegen.md`, `worldsim.md` and `archive/` may retain old language when
clearly historical; do not rewrite project history as part of this build.

---

## Grid movement, path cost and position

Travel uses orthogonal Tile edges. There are no diagonals.

### Symmetric edge cost

- East/west edge base: 1 day.
- North/south edge base: 2 days.
- Add 1 day if either endpoint is a mountain Tile.
- River has no surcharge. It is ordinary inhabited land at this scale.
- Sea has no surcharge beyond directional base.
- Crossing a country border has no intrinsic surcharge.

The mountain surcharge is symmetric: descending the same edge costs what
ascending it cost. Path cost must therefore be symmetric between two Tiles.

Use deterministic Dijkstra (or an equivalent weighted shortest-path
algorithm) with a stable row/column tie-break. The pathfinder may cross known
sea and terrain because the whole base map is known. It may not leave the
18x30 frame.

### Travel commands

- `travel north|south|east|west` moves one cardinal edge and is the canonical
  primitive.
- `travel R09C18` and `travel NAME` may follow the cheapest route to a known
  Tile or settlement as a convenience. Execute it edge by edge and stop after
  a fight, sighting requiring input, party wipe, or other interruption.
- Traveling to a Tile coordinate arrives in its natural Area.
- Traveling to a settlement name arrives in that settlement Area.
- An unknown ordinary settlement cannot be a named destination.

An edge is atomic. Spend its days, apply recovery/world clocks, place the
party in the destination Tile/Area, then resolve its arrival-road encounter.
There is no half-edge save position. A fight stops a multi-edge route at the
Tile just reached; the party never bounces back to the journey's origin.

Each land/mountain/river edge keeps the current compounded per-day road
encounter chance and the avoidability valves, using the destination country's
human/cultural pool. Sea edges roll weather/exposure and time but no random
combat encounter in the MVP. Sea nights grant ordinary travel recovery: the
passage is abstracted and no ship inventory is created.

Teleport travel remains settlement-to-settlement and visited-only. Its Power
cost uses shortest-path days rather than the old same-Land/cross-Land
constant.

---

## Map and local displays

`map` and `ui/map.txt` become the 30x18 terrain display with numeric axes,
fitting within 40 columns. Do not draw border characters through the grid;
the fixed partition rule and grouped city legend carry political geography,
and the current-Tile detail always names its country.

Base glyphs remain `. # ^ ~`. Known overlays have this priority:

1. `@` party;
2. `!` active quest objective;
3. `C` capital;
4. `T` any known town in the Tile;
5. `v` known village(s) with no known town;
6. biome glyph.

One cell never attempts to show all settlements. A detail block below the map
lists the current Tile's name, coordinates, country, biome, known Areas and
active quest markers. A second compact legend groups known historical cities
and other known settlements by country as space permits. All generated map
lines and legends must use the existing 40-column fitting utilities and ASCII
output.

Terrain is visible from world creation. Discovery governs ordinary
settlements, Areas and Sites, not the continental outline.

`look` at Tile/Area level must distinguish the Tile from the current Area and
list known sibling Areas. `ui/minimap.txt` remains out of this MVP; the macro
map plus existing local breadcrumb is enough.

---

## Local quest geography — approved quick patch

The old rule that news exposes every open quest in the current Land is
replaced by path-local knowledge. It is valid and expected for a settlement
to have no ordinary quests.

Constants:

- `QUEST_RUMOR_DAYS = 3`
- `ORDINARY_TARGET_DAYS = 3`

### Sparse ordinary boards

At materialization, a stable derived roll decides whether the settlement
normally posts ordinary generated work:

| Settlement | Ordinary board active |
|---|---:|
| Capital | 100% |
| Other town | 60% |
| Village | 25% |

- The starting settlement is forced active.
- An inactive board has ordinary capacity zero.
- An active board retains the current tier capacity, refill-per-day rule,
  economy/world-state modifiers and a minimum capacity of one.
- Story, world-card, delivery, pact, punishment and explicit DM-forged quests
  may post at an inactive settlement. They do not convert it permanently into
  an ordinary board.
- Historical fame does not itself guarantee ordinary work; only capitals and
  the starting override do.
- No quest is posted merely to satisfy a global world count.

### Three-day rumor radius

When the player reads a board:

1. Find known, materialized settlements whose shortest path from the current
   Tile costs at most three days, including the current settlement.
2. Refresh only their active boards to the current day. Reading local rumors
   is an intentional lazy roll point; it does not materialize unknown
   settlements.
3. Expire their stale postings normally.
4. Show open quests grouped as `HERE`, `1 DAY AWAY`, `2 DAYS AWAY`, and
   `3 DAYS AWAY`; omit empty groups.
5. Include origin settlement, Tile name/coordinate and path days on each
   remote listing.

`board all` remains a DM/debug inventory and may show every materialized
posting without changing which boards refresh.

### Ordinary target radius

- An ordinary generated quest selects compatible natural/settlement Areas
  whose Tile is at most three one-way shortest-path days from its origin.
- The origin Tile is legal and guarantees at least its natural Area as a
  fallback candidate.
- Tag compatibility still applies; do not route a coast quest to generic
  inland ground merely to satisfy the radius.
- Selection is deterministic from the quest's existing RNG stream after the
  candidate set is assembled in stable Tile/Area order.
- Story waves, deliveries, pact assignments, punishment, DM-forged quests
  and specifically authored world events may override the radius.

### Path-priced clocks and deliveries

- Ordinary quest base windows keep the current 3-7 day roll.
- Add twice the shortest path from origin to the quest's final target Tile:
  one outward leg and one return leg.
- If a multi-Site quest crosses Tiles, price the actual required route through
  its ordered Sites plus the return to origin rather than multiplying only
  the final distance.
- Delivery destinations remain in another country and are not radius-limited.
- Delivery gold and XP use actual one-way shortest-path days.
- Delivery clock allowance adds twice that one-way cost, retaining the
  present round-trip doctrine.
- Teleport skips travel days but does not retroactively shorten a posted
  quest's window or reward.

---

## Source-data boundary

`place_catalog.json` stops owning world geography. It remains the content
catalog for surviving country cultures, settlement skeletons, natural Site
templates, Room layouts and livelihood overlays.

Remove or replace its obsolete geography fields:

- six-Land order and adjacency;
- authored natural-Area census;
- fixed settlement census as map positions;
- cross-Land travel links and water links;
- deleted-country content.

The fixed map owns Tile adjacency. Historical city positions and density/name
tables may live in the catalog or in one small validated constant module, but
there must be one source of truth and import-time validation. Prefer catalog
data when it is content and Python when it is a mechanical rule.

The archived map generators remain archived. Do not revive them or add a seed
choice between generated and fixed geography.

---

## Cross-cutting invariants and verification

Every session must preserve these invariants relevant to its slice:

- Same seed produces structurally identical country, Tile, density, name,
  discovery and quest-placement data.
- Different seeds change density, name order, start and lazy content without
  moving the fixed terrain or historical cities.
- Every one of 540 Tiles has a natural Area and a valid country.
- Sea has no settlement slots.
- Mountains have no ordinary town slots.
- Exactly Paris, Rome and Kyiv carry `capital: true`.
- Historical city coordinates contain the declared biome and country.
- Every cardinal link is reciprocal; no diagonal link exists.
- Shortest-path cost is symmetric and uses 1/2 directional base plus the
  symmetric mountain surcharge.
- Every landmass is reachable because sea is navigable.
- No reader silently supplies a missing Tile, Area, country or world-layer
  record; illegal world state raises.
- Lazy settlement materialization never changes the rolled census.
- Name exhaustion is stable and collision-free.
- Starting selection is over settlement slots, not countries or Tiles.
- Ordinary rumor and target distance never exceed three path days.
- Forced quest families may bypass sparse-board and target-radius rules only
  through explicit code paths.
- Player-facing output and runtime catalogs contain no removed race/country
  presentation. Historical documents are excluded from this assertion.
- Map and board displays stay ASCII and at most 40 columns.
- Existing combat, wound, crime, karma, weapon and world-layer mechanics do
  not change except where cultural routing or path days explicitly require it.

Tests should be rewritten to construct legal fresh worlds, not wrapped in
compatibility helpers for the old save or old six-Land schema.

---

# Implementation sessions

## Session 2 — Fixed Europe Geography

**Trigger:** `Implement Fixed Europe Geography from plan.md.`

### Objective

Replace list geography with the fixed Tile hierarchy, natural Areas,
population slots, historical cities, lazy names and uniformly random start.
Travel may still use a temporary direct move until Session 3.

### Required work

1. Load and validate `resources/europe_map.txt`; build 540 Tile records and
   three country Tile inventories.
2. Add Tile IDs/schema, cardinal neighbors, derived tags and one natural Area
   per Tile.
3. Refactor Area IDs/records and position to include Tile without weakening
   required-record reads.
4. Add historical city data exactly as specified; materialize/know their town
   Areas and keep their village slots lazy.
5. Roll ordinary settlement slots with the pinned tables and mountain
   downgrade.
6. Restore all three country name reserves, including Firascir's older pool,
   plus deterministic exhaustion counters.
7. Rework settlement materialization/founding around fixed slots and reuse
   surviving Site/Room/service templates.
8. Select the start uniformly across settlement slots, materialize it, assign
   PC homeland and force a legal opening hook.
9. Remove old authored natural-Area geography, Land adjacency and reserve
   census from runtime source data.

### Primary files

`resources/europe_map.txt` (read-only source), `place_catalog.json`,
`places.py`, `quests.py`, `session.py`, `weapons.py` where smith placement
reads settlements, `test_places.py`, `test_start.py`, affected world tests,
`rules.md`, `dm.md`, `develop.md`.

### Non-goals

No final pathfinder, sea encounter design, map overlay or three-day rumor
patch. Do not re-detail `basic` or name rural Tiles.

### Verification

- Pin dimensions, glyph counts, country/biome counts, component sizes,
  historical city table and three capitals.
- Assert 540 Tiles and 540 natural Areas.
- Assert every sea Tile has zero slots and ordinary mountains have no towns.
- Same-seed full structure equality; different-seed density/name/start
  variation with identical terrain.
- Force name-pool exhaustion for every country/tier.
- Repeated fresh starts reach every country and multiple settlement tiers
  over a seed sweep; selection tests prove the candidate unit is a slot.
- Materialize/reload/revisit tests prove no census or name changes.

## Session 3 — Grid Navigation and Map UI

**Trigger:** `Implement Grid Navigation and Map UI from plan.md.`

### Objective

Make the fixed map navigable and legible: weighted cardinal movement,
sea access, persistent intermediate position, destination pathfinding and the
40-column map.

### Required work

1. Implement reciprocal cardinal edges, symmetric edge cost and deterministic
   shortest paths.
2. Replace 1-day/2-day Land travel with Tile-edge movement while preserving
   recovery, clocks, weather, sightings, fights, news, punishment and arrival
   hooks in correct order.
3. Add directional travel and known destination/settlement convenience paths;
   stop multi-edge travel after interruption at the Tile reached.
4. Make sea navigable without ports/inventory and suppress random sea combat.
5. Adapt wild/hunt/camp context and teleport cost to Tile/country/path data.
6. Render the fixed map with axes and overlay priority; update `ui/map.txt`.
7. Update `look`, location breadcrumbs and sibling-Area movement for the new
   hierarchy.
8. Remove the old list-shaped map display and direct Land-distance logic.

### Primary files

`places.py`, `quests.py`, `session.py`, `worldsim.py`, `dm.md`, `rules.md`,
`develop.md`, `test_places.py`, `test_start.py`, `test_turnin.py`,
`test_worldsim.py`, UI log tests and new focused navigation tests if warranted.

### Non-goals

No roads, ports, ships, naval encounters, diagonal motion, Tile climate
profiles or dynamic borders. Do not implement the quest-radius patch in this
session.

### Verification

- Unit-test every edge-cost case and reciprocal path symmetry.
- Pin representative shortest paths across each country, a mountain edge,
  a river Tile, country borders and sea to all three small landmasses.
- Interrupted route leaves the party at the reached Tile, never the original
  settlement.
- Sea travel spends time/recovery/weather but rolls no combat encounter.
- Teleport charges actual path days.
- Map overlays obey priority and every line fits 40 ASCII columns.
- Manual smoke: start, travel by direction, travel to a named city, cross sea,
  save/load and continue from the same Tile/Area.

## Session 4 — Local Quest Geography

**Trigger:** `Implement Local Quest Geography from plan.md.`

### Objective

Make boards, rumors, targets, clocks and deliveries read actual path distance
without requiring every settlement to contain work.

### Required work

1. Add the stable capital/town/village board-activity roll and starting
   override.
2. Separate ordinary board capacity from forced quest posting so an inactive
   board can still receive story/world/delivery/pact work.
3. Replace Land-wide rumor visibility with known materialized settlements in
   the three-day shortest-path radius.
4. Refresh only those nearby active boards at the board roll point and group
   the readout by path days.
5. Restrict ordinary generated targets to compatible Areas within three path
   days, with stable ordering and local fallback.
6. Price ordinary windows by the actual ordered route and return leg.
7. Price delivery pay/window by unrestricted cross-country shortest path.
8. Place story/world-card/forced quest content geographically through explicit
   radius overrides.
9. Update career/test helpers deliberately; do not preserve old benchmark
   comparability through compatibility code.

### Primary files

`quests.py`, `session.py`, `story.py`, `worldsim.py`, `karma.py`,
`test_places.py`, `test_start.py`, `test_turnin.py`, `test_worldsim.py`,
`bench_quests.py`, `rules.md`, `dm.md`, `develop.md`, and `benchlog.md` if the
career sim is remeasured.

### Non-goals

No global quest-density guarantee, background board tick, settlement creation
for rumor purposes, roads, faction reputation or content expansion.

### Verification

- Board-active rates match 100/60/25 over a large deterministic sample.
- Inactive settlements can be empty and can still hold each forced quest
  family.
- Remote board reads never show or refresh a settlement beyond three days.
- `board all` observes without changing remote refresh scope.
- Ordinary target paths never exceed three days across a seed sweep.
- Deadline tests cover local, multi-Tile, mountain, sea and multi-Site routes.
- Delivery tests cover different-country destinations and exact distance pay.
- Opening quest is always present and geographically legal.
- Re-run the career bench if its path/calendar model changes, record results,
  and do not tune unrelated combat numbers in this session.

## Session 5 — Europe MVP Closure

**Trigger:** `Implement Europe MVP Closure from plan.md.`

### Objective

Remove obsolete scaffolding, close documentation and test gaps, and prove the
new world in an end-to-end fresh playthrough.

### Required work

1. Delete dead list-map, race adapter, six-country catalog, old reserve and
   constant-distance branches left behind by the staged build.
2. Audit active runtime strings and content for removed peoples/countries and
   accidental `city` subtype assumptions.
3. Tighten import-time/data validation around Tile, historical city,
   settlement-slot and three-country worldsim contracts.
4. Consolidate or split tests so the permanent suite describes the new model
   rather than the migration sequence.
5. Update `rules.md`, `dm.md`, `develop.md`, relevant spec companions and the
   full designlog build record. Remove all now-shipped Europe planning from
   this file.
6. Run the complete test suite and relevant benches.
7. Run an end-to-end smoke game: random start, inspect map, hear a nearby
   quest, take it, traverse at least two biome types, clear it, return, turn
   it in, save/load, and inspect world/map state.

### Primary files

All files touched by Sessions 1-4, with special attention to active docs,
validation and tests. Archived historical files are not rewritten.

### Non-goals

No balance redesign, new quest content, roads, ships, seasons, detailed basic
biomes, dynamic borders or resurrection of items in the archived roadmap.

### Verification

- Full unit suite green.
- Relevant benchmark/sanity commands complete and are recorded where required.
- No active runtime/catalog output contains a removed people or country.
- The end-to-end smoke loop satisfies every item under **Goal and MVP proof**.
- `plan.md` is empty of the shipped Europe contract except for genuinely
  discovered follow-up work; the completed record lives in permanent docs.

---

## Explicitly deferred until after the MVP is played

- Detailed sub-biomes for `basic`.
- Roads and road quality.
- Bridges, mandatory river tolls and ferry infrastructure.
- Ports, owned ships, passage prices and naval encounters.
- Seasonal or Tile-specific weather profiles.
- Named rural Tiles and natural regions beyond coordinates.
- Megacities with no natural Area.
- Dynamic country borders and Tile-level conquest.
- Fogging the base terrain map.
- Diagonal movement.
- Any feature preserved in `archive/plan-pre-europe-2026-08-15.md` unless a
  later design session deliberately returns it to the active roadmap.
