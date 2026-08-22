# The roadmap

This is the sole active roadmap. **Nothing implemented lives here** — when
a session ships, its contract is deleted and the result is written to the
permanent docs (`rules.md`, `dm.md`, `develop.md`, `benchlog.md`) and the
build record to `designlog.md`. See develop.md's "Where a finished feature
is written up".

Three whole arcs have shipped out of this file, and as of 2026-08-22 it
carries **no build contract at all**. The fixed Europe map was **BUILT**
across five sessions ending 2026-08-15 (designlog 2026-08-15 and develop.md
hold the pointers). **THE TILE ECONOMY ARC** was designed in five rounds
(2026-08-20 through 2026-08-21 (E)) and **BUILT WHOLE on 2026-08-21** across
four numbered implementation sessions — the ground and the sky, the rolled
world, the trade network, and the hookup — whose build records are
designlog's (F), (G), (H) and (I) entries; what it built lives in rules.md's
World & Navigation and Miners' League add-ons, dm.md's "The ground under
the party", develop.md's Files and dev map, and benchlog's 2026-08-21
entries. **THE MEDIEVAL WORLD ARC, Part 1** was designed on 2026-08-21
(designlog (J)) and **BUILT WHOLE across five sessions on 2026-08-21 and
2026-08-22** — the fallen banner (K), the map of nine (L), the towns & the
tongues (M), the norse packet & the nine-land relations (N), and the rolled
wars & the campaign sim (O). It left the world as NINE COUNTRIES over four
cultures, with real town names, tongues on the sheet, a full norse packet,
twenty land-to-land relations, and three standing wars smouldering over
authored theaters; what it built lives in rules.md's World & Navigation and
The Rolled Wars add-ons, dm.md's "The nine countries", "The tongues at the
table" and "The wars", writing.md's "The nine name sounds", develop.md's
Files and dev map, and benchlog's 2026-08-21 (E) and 2026-08-22 entries.

What remains below is the roadmap BEYOND all three: main points only, each
a future design conversation, none scheduled. Two habits from the earlier
arcs continue to apply everywhere — **hidden numbers, visible words** (a
per-tile quantity is a worldgen intermediate; what the game stores and
speaks are words), and **author the physical, derive the human**.

---

## The spring snapshot & trouble arc

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
  on them, so a new seam is found *somewhere in Teutonia* rather than at
  Goslar. Giving it the address is this arc's cheapest visible win. The
  medieval world arc's campaign sim SHIPPED half the plumbing on
  2026-08-22: a Tile and a census slot now carry a `states` list and two
  pages print it (`places.WAR_STATE_WORDS` / `war_state_lines`), so what
  a card still needs is the ADDRESS -- a way to say which tile it fires
  on -- and not a place to write.
- **The past-epidemic population scar** — the plague chain's mark on the
  census, parked out of the census session (2026-08-21) and waiting for
  this arc's own trouble model.

## Politics & war (what the medieval world arc left here)

The nine countries, the raider culture, the era anchor and the standing
wars all SHIPPED with that arc (rules.md's World & Navigation and The
Rolled Wars add-ons). Three things it deliberately declined are still
parked here:

- **Dynamic borders and tile conquest** — real ones, where a front
  advances and a border redraws — once tiles are worth taking. The
  arc's campaign sim deliberately stops short of this; its war records
  and occupation states are the ground it would build on, and nothing
  it shipped needs unbuilding first.
- **Languages with mechanics.** Session 3 SHIPPED who speaks what (the
  SPEAKS line) and dm.md's table rule; an engine reader — a rumor radius
  that stops at a language border, a quest gated on a tongue, an
  interpreter hired for a fee — is a later sitting. Nothing in the
  engine checks a tongue today.
- **Vassalage with teeth.** Andalusia's liege is rolled (a d2 since the
  2026-08-22 Iberia split: Byzantium's vassal or its free ally) and
  printed on `world` and on the map legend — which is the whole of it.
  Tribute, a pulled-in war and a court above the court are undesigned.
- **The era anchor against the colony cards.** `southern/colony-fleet`,
  `southern/monopoly-bubble` and `southern/the-crash` are about colonial
  trade in a world anchored at "about 1500 WITHOUT the age of
  exploration" (found by session 4's card audit, designlog (N)). Three
  cards' fiction to re-write; a content sitting, not a design one.

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
