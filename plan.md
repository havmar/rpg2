# The roadmap

This is the sole active roadmap and build contract. **Nothing implemented
lives here** — when a session ships, its contract is deleted and the result
is written to the permanent docs (`rules.md`, `dm.md`, `develop.md`,
`benchlog.md`) and the build record to `designlog.md`. See develop.md's
"Where a finished feature is written up".

The fixed Europe map is **BUILT**. Five sessions shipped it between
2026-08-15's design reset and the same day's closure — Human World
Contraction, Fixed Europe Geography, Grid Navigation and Map UI, Local
Quest Geography, Europe MVP Closure — and their contracts are gone from
this file. Where the world is now written down:

- **the played rules** — `rules.md`'s World & Navigation add-on (the
  hierarchy, the map, travel and its costs, local movement, the settlement
  census, the templates, the world's own validation) and its Quest System
  add-on (sparse boards, the radii, the path-priced clock);
- **the table manner** — `dm.md` (the map page, `travel`, `explore`, the
  war);
- **the code map** — `develop.md`'s entries for `places.py`,
  `place_catalog.json`, `quests.py`, `session.py`, `worldsim.py` and the
  four contract suites;
- **the build record and every call the specs left open** —
  `designlog.md`, 2026-08-15;
- **the numbers** — `benchlog.md`, 2026-08-15.

`archive/plan-pre-europe-2026-08-15.md` holds the complete roadmap the
Europe reset displaced, including its unfinished and parked ideas. It is
historical and is not implementation authority; nothing in it is scheduled
unless a later design session deliberately moves an item back here.

There is no session queued. The next one is a design conversation, not an
implementation trigger — the MVP is built and the honest next input is
play.

---

## Deferred until after the MVP is played

These were deliberately left out of the Europe build. None of them blocks
anything; each is a design round away.

- **Detailed sub-biomes for `basic`.** Local Quest Geography found the cost
  of deferring this (2026-08-15, designlog): the quest tables ask for
  `forest` / `hills` / `prairie` / `pasture` / `farmland` / `road` terrain,
  and a natural Area's tags are its Tile's — `basic`, `river`, `mountain`,
  `sea` plus `coast` / `riverside` / `mountain-foot` / `border` / `island`.
  Only `coast` and the settlement Areas' own template tags intersect the
  tables, so most ordinary jobs land on the origin Tile's own countryside
  through the declared fallback rather than being routed by terrain.
  Nothing is broken — every job is legal, close and playable — but the
  radius rule is doing less work than it could. Whoever gives `basic` its
  sub-biomes should reconcile the two vocabularies in the same pass
  (including the near-miss between the `mountain` biome tag and the tables'
  `mountains`), and should also give the settlement templates something
  better than `coast` / `river` / `mountain-foot` to fit against.
- Roads and road quality.
- Bridges, mandatory river tolls and ferry infrastructure.
- Ports, owned ships, passage prices and naval encounters.
- Seasonal or Tile-specific weather profiles. Country climates remain the
  MVP weather source even while the party is on a sea or mountain Tile.
- Named rural Tiles and natural regions beyond coordinates.
- Megacities with no natural Area. The Tile record already permits zero
  natural Areas; no definition uses the exception.
- Dynamic country borders and Tile-level conquest.
- Fogging the base terrain map.
- Diagonal movement.
- Any feature preserved in `archive/plan-pre-europe-2026-08-15.md` unless a
  later design session deliberately returns it to this file.

---

## Parked by the closure (2026-08-15)

Discovered while closing the Europe build, and left alone on purpose.

- **The exclusive-state-slot frame has no authored users.** Both
  `worldsim.STATE_SLOTS` entries — the standing of a land's foreigners, the
  stage of its ore deposits — belonged wholly to countries the contraction
  deleted. The table is empty; the machinery, its import-time validation
  and `set_state`'s slot discipline all stand, and `test_worldsim` pins the
  emptiness so it cannot rot into a silently vacuous guard. The next
  country packet, or a re-homed extraction chain with a gate a surviving
  country actually has, plugs a slot back in with one row. Nothing is
  broken meanwhile: wealth and the constitution are exclusive slots with
  setters of their own and never went through this table.
- **Settlement templates repeat across a world.** Four town roles and five
  village roles a country means any world with twenty settlements has two
  places reading the same sentence (the smoke game's Leehaven and Prague
  were both `market_town`). The DM narrating over it is the intended
  answer. If it grates in play the fix is more authored roles per country,
  not a generator — and the sub-biome round above is the natural place to
  write them.
- **A companion quitting mid-career is much harsher on the fixed map.**
  Watch it in play before touching a number. The wound track and the
  satisfaction track are both behaving as designed; what changed is that
  the road is now genuinely long, so walking somewhere to recruit costs a
  wounded PC days it may not have. The smoke game (designlog 2026-08-15)
  lost its run exactly this way.
