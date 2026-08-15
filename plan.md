# The Fixed Europe Map — implementation contract

This is the sole active roadmap. The 2026-08-15 design sessions replace the
former world with a fixed 30x18 Europe-shaped grid inhabited only by humans.
The Human World Contraction, the Fixed Europe Geography, Grid Navigation
and Map UI and Local Quest Geography are implemented and documented in
`rules.md`, `dm.md`, `develop.md` and `designlog.md`; the former roadmap is
preserved, explicitly inactive, in
`archive/plan-pre-europe-2026-08-15.md`.

One implementation session remains. It may be
started simply by asking to implement its exact title:

1. **Europe MVP Closure**

The session must leave its slice coherent and tested. No save compatibility
is required. Fresh worlds are the only supported worlds.

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

## Grid movement, path cost and position — BUILT

Shipped 2026-08-15 (Grid Navigation and Map UI). The played rule lives in
`rules.md`'s World & Navigation add-on ("Travel" and "Local movement"); the
code map is in `develop.md` under `places.py` and `session.py`; the build
record and the calls this contract left open are in `designlog.md`.

What later sessions need to know: distance is `places.path_days(a, b)`
between two Tile IDs — symmetric, deterministic, finite between any two
Tiles because sea is navigable — and `places.shortest_path` returns the
route. Nothing asks "same land or another?" any more.

## Map and local displays — BUILT

Shipped 2026-08-15 with the above. `rules.md`'s World & Navigation add-on
owns the rule ("The map" and "Local movement"), `develop.md` the code.

## Local quest geography — BUILT

Shipped 2026-08-15 (Local Quest Geography). The played rules live in
`rules.md`'s Quest System add-on ("Sparse boards", the target radius under
quest placement, the three-day rumor radius under quest offers, and the
whole road inside the window under "The clock"); the table manner is in
`dm.md`; the code map is in `develop.md` under `places.py`, `quests.py`
and `session.py`; the build record and the calls the spec left open are in
`designlog.md`, the re-measured career column in `benchlog.md`.

What the closure session needs to know: `QUEST_RUMOR_DAYS` and
`ORDINARY_TARGET_DAYS` are both 3 and both live in `quests.py`;
`quests.is_ordinary_posting` is the single reader that separates ordinary
work from the forced families; `places.board_active_roll` decides whether a
settlement posts ordinary work at all.

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

## The remaining session — Europe MVP Closure

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

All files touched by the four shipped Europe sessions, with special
attention to active docs, validation and tests. Archived historical files
are not rewritten.

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

- Detailed sub-biomes for `basic`. **Local Quest Geography found the cost of
  deferring this** (2026-08-15, designlog): the quest tables ask for
  `forest` / `hills` / `prairie` / `pasture` / `farmland` / `road`
  terrain, and a natural Area's tags are its Tile's — `basic`, `river`,
  `mountain`, `sea` plus `coast` / `riverside` / `mountain-foot` / `border`
  / `island`. Only `coast` and the settlement Areas' own template tags
  intersect the tables, so most ordinary jobs land on the origin Tile's own
  countryside through the declared fallback rather than being routed by
  terrain. Nothing is broken — every job is legal, close and playable — but
  the radius rule is doing less work than it could. Whoever gives `basic`
  its sub-biomes should reconcile the two vocabularies in the same pass
  (including the near-miss between the `mountain` biome tag and the tables'
  `mountains`).
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
