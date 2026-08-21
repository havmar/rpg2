# The roadmap

This is the sole active roadmap and build contract. **Nothing implemented
lives here** — when a session ships, its contract is deleted and the result
is written to the permanent docs (`rules.md`, `dm.md`, `develop.md`,
`benchlog.md`) and the build record to `designlog.md`. See develop.md's
"Where a finished feature is written up".

Two whole arcs have shipped out of this file. The fixed Europe map was
**BUILT** across five sessions ending 2026-08-15 (designlog 2026-08-15 and
develop.md hold the pointers). **THE TILE ECONOMY ARC** was designed in
five rounds (2026-08-20 through 2026-08-21 (E)) and **BUILT WHOLE on
2026-08-21** across four numbered implementation sessions — the ground and
the sky, the rolled world, the trade network, and the hookup — whose build
records are designlog's (F), (G), (H) and (I) entries. Its Part 1 contract
is gone from this file, per the rule above; what it built lives in
rules.md's World & Navigation and Miners' League add-ons, dm.md's "The
ground under the party", develop.md's Files and dev map, and benchlog's
2026-08-21 entries.

What follows is the roadmap BEYOND both arcs: main points only, each a
future design conversation, none scheduled. The arc's own standing rules
were written for its build and are not repeated here; two of them are
worth carrying forward as habits and are stated where they apply below —
**hidden numbers, visible words** (a per-tile quantity is a worldgen
intermediate; what the game stores and speaks are words), and **author the
physical, derive the human**.

---


## The spring snapshot & trouble arc (the natural next)

- **The last-harvest roll SHIPPED with session 2 and is READ since
  session 4** (2026-08-21 — the layer is `places.roll_harvest`, its words
  are `places.harvest_line`, and rules.md's World & Navigation add-on
  documents both). This arc KEEPS: the
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
  geography, so the harvest fails where the grain grows. The Miners'
  League (session 4) is the concrete customer waiting: its six cards fire
  at LAND level over a map that knows exactly which nine tiles have pits
  on them, so a new seam is found *somewhere in Firascir* rather than at
  Goslar. Giving it the address is this arc's cheapest visible win.
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

## Parked from the tile economy arc (2026-08-21, when session 4 shipped)

None of these is blocked; the arc declined them rather than deferring
them, so each is a cheap sitting whenever the map wants it.

- **A Hanse-shaped authored northern circuit.** Round 4 declined it because
  the DERIVED north already draws the circuit organically — Falun's copper,
  the taiga timber, the Sound's herring, Luneburg's salt, the amber shore.
  Authoring it would be for the NAME and the story, not for the roads.
- **An Ardennes-shaped western wildwood mark.** The eastern one shipped as
  `places.HAND_FOREST` (four clearance-capped tiles east of Warsaw); the
  west still has none, so no lowland deep forest survives the deforestation
  law there. One entry in the same table.
- **Two land-character rows the goods layer always outranks**, plus the
  `plains` fall-through. `deep forest` and `the open steppe` never reach a
  page on the shipped overlays, because every deep-forest tile is already
  a fur or timber origin and every non-marsh steppe tile is horse country;
  `plains` never does either, because an earlier rule covers every plains
  tile that lacks the farmland tag. They are law rows over the whole
  authored vocabulary rather than dead fallbacks, and `econmap.py
  character` prints which are unused so the fact stays visible; a later
  overlay change may bring any of them back on its own. Only revisit if
  the priority itself starts reading wrong at the table.

## Small deferred leftovers (from the Europe build, still true)

- **The charter and the manor have no MECHANICAL readers.** Session 2
  stores both words on every settlement slot and session 4's tile brief
  prints them for the DM, but nothing in the engine acts on either; what
  freedom is worth — taxes, revolts, entry at the gate — is the politics
  arc's design (rules.md's World & Navigation add-on describes what is
  stored).
- **Named natural regions** (the Alps, the Pripet, the Danube corridor) —
  take if cheap, still unscheduled.
- Roads and road quality; bridges, mandatory river tolls and ferries;
  ports, owned ships, passage prices and naval encounters — natural
  continuations of the routes session, none scheduled. Session 4 wired
  the priced menu's TILE half (a granary's cheap beds, a pithead's cheap
  steel, a crossroads' full shelves) and deliberately left `toll` and
  `ferry` alone: tolls walking the route network want the snapshot and
  politics arcs first.
- Fogging the base terrain map. Diagonal movement.
- **Two calibration benches are not reproducible run to run**, and
  neither can clear a change. `bench_abilities.py` (found 2026-08-21,
  session 2): its warrior-moves matchup and alchemist career blocks swing
  several points between two runs of identical code. `bench_quests.py`
  (found 2026-08-21, session 3, verified over three runs of an unmodified
  tree): parts 1 and 2 are byte-stable and PART 3, the career sim, is not
  — reached-L20 came back 0.5%, 1.5% and 0.0%. Both develop.md Files
  entries carry the warning. Worth a sitting of its own: a safety net that
  cannot be compared against itself is not one. (`bench_worldgen.py`,
  added by session 4, is NOT one of them — its layers are deterministic
  per seed, so it can clear a change.)
- Watch in play: a companion quitting mid-career is much harsher on the
  fixed map (closure note, unchanged — the wound and satisfaction tracks
  are behaving as designed; the road is just genuinely long now).
- `archive/plan-pre-europe-2026-08-15.md` remains historical; nothing in
  it is scheduled unless a later design session deliberately returns an
  item to this file.
