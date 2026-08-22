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

This file now carries one ACTIVE build contract again: **THE MEDIEVAL
WORLD ARC, Part 1** (designed 2026-08-21, designlog (J)) — nine countries,
names and tongues, the Thule packet, and the rolled wars. Its sessions 1
(the fallen banner, designlog (K)) and 2 (the map of nine, designlog (L))
shipped on 2026-08-21, and sessions 3 (the towns & the tongues, designlog
(M)) and 4 (the norse packet & the nine-land relations, designlog (N)) on
2026-08-22; session 5 is the last build. Below the
contract is the roadmap BEYOND
it: main points only, each a future design conversation, none scheduled.
Two habits from the earlier arcs continue to apply everywhere — **hidden
numbers, visible words** (a per-tile quantity is a worldgen intermediate;
what the game stores and speaks are words), and **author the physical,
derive the human**.

---

# THE MEDIEVAL WORLD ARC — Part 1: nine countries & the rolled wars

Designed 2026-08-21 (designlog (J) is the session record). This is the
build contract: five sessions, in order, each leaving the game true and
green. When a session ships, delete its contract here and write it up per
develop.md's "Where a finished feature is written up". **Session 1 — the
fallen banner** shipped on 2026-08-21 and is gone from this file: the
scripted conquest questline (`story.py`), the war feed and every
touchpoint were deleted whole, and the game runs warless (designlog (K);
rules.md's Story Layer add-on carries the note). **Session 2 — the map of
nine** shipped the same day and is gone too: the country overlay, the
catalog's culture/land split, the name pools, the norse culture and the
mechanically re-keyed worldsim (designlog (L); rules.md's World &
Navigation add-on, "Nine countries over four cultures"). **Session 3 —
the towns & the tongues** shipped on 2026-08-22 and is gone as well: the
164 authored town names and the chief-slot naming rule, and the nine
tongues on the sheet (designlog (M); rules.md's "The towns have REAL
names" and "Tongues", dm.md's "The tongues at the table", writing.md's
"The nine name sounds"). **Session 4 — the norse packet & the
nine-land relations** shipped on 2026-08-22 and is gone as well: Thule's
full card packet, the audit that read every re-keyed western and southern
card against its new scope, the twenty authored land-to-land relation
edges that replaced the culture cross product, and a signature fact for
every country (designlog (N); rules.md's "Relations" and "Thule keeps the
old gods", dm.md's Thule row). Session 5 follows.

## The frame

- **A country is cheap now**: a bundle of tiles on the authored map, a
  culture's shared card packet, a capital, a name style and a tongue.
  This arc spends that cheapness: the census of three was a contraction
  artifact, and the map reads wrong with one crown over all of France,
  Britain and Germany.
- **COUNTRY vs CULTURE.** Nine countries own identity: tiles, capital,
  tongue, name pools, standing facts, wars. Four CULTURES own the
  reusable content: the card decks, tensions, constitutions, faction
  edges, options, settlement templates, natural inventories and quest
  tables. `western` (from the Firascir packet), `southern` (from the
  Mortellaria packet), `steppe` (Tergal's own), `norse` (new, this arc).
  Only Tergal keeps its name; Firascir and Mortellaria disappear as
  countries and survive as the western and southern cultures.
- **The era anchor: about 1500, without the age of exploration** (moved
  here from the roadmap). Pre-Columbus trade frames the edges: silk in
  from the east, spice through the southern entrepot, gold caravans from
  beyond the fertile stripe, the wool-cloth axis in the west. Any higher
  technology is heaven, hell and magic, never a gunpowder tech line.
- **The game is static in time, so wars are static too.** Wars are
  rolled once at worldgen like the last harvest, stand for the whole
  campaign, and smoulder rather than resolve. The campaign sim makes the
  front LOOK alive (raids, camps, battles, a siege that sacks a town);
  it never redraws a border and never ends a war. Real dynamic conquest
  stays parked in the roadmap until tiles are worth taking.

## The nine countries

| key | name | seat of | tongue | culture | capital |
|---|---|---|---|---|---|
| `phyrascia` | Phyrascia | Britannia | Phyrascian (English sounds) | western | London (6,5) |
| `seraptania` | Seraptania | France | Seraptanian (French sounds) | western | Paris (9,10) |
| `teutonia` | Teutonia | Germany | Teutonic (German sounds) | western | Prague (9,18) |
| `vellisclavia` | Vellisclavia | Poland & Rus | Vellisclav (old Slavic sounds) | western | Moscow (7,28) |
| `thule` | Thule | Scandinavia | Norse (old Norse mashup) | norse | Stockholm (3,23) |
| `byzantium` | Byzantium | Italy, Balkans, Anatolia | Latin | southern | Constantinople (14,27) |
| `andalusia` | Andalusia | Iberia | Andalusian (Spanish sounds) | southern | Cordoba (14,4) |
| `umaia` | Umaia | Africa & the Levant | Umaian (Arabic sounds) | southern | Cairo (18,24) |
| `tergal` | Tergal | the Pontic steppe | the Tergal tongue (as today) | steppe | Kyiv (10,27) |

Settled calls, so they stay settled:

- **Byzantium is the southern heir**: Rome, Venice, Athens and
  Constantinople are its cities, its tongue is Latin, and the
  Mortellarian identity that is land-specific (the death rite, the
  carnival, the academy necromancers, the schism material) re-homes to
  Byzantium alone rather than to the whole southern culture.
- **Seraptania has no southern coastline.** The Mediterranean coast
  tiles at (11,10) and (11,11) are Byzantium's — the empire holds the
  middle sea's north shore to the Rhone.
- **Tergal keeps Kyiv as its capital.** The horde seated in a taken
  river city is genre-correct (the Golden Horde pattern), it is already
  the game's capital there, and it puts the aggressor's seat on the
  frontier it attacks from. Vellisclavia's Rus identity hangs on Moscow,
  Warsaw and (at build) Novgorod. The alternative — Kyiv to Vellisclavia
  and an authored Sarai in the east — was considered and declined.
- **Amsterdam and the Low Countries are Teutonia's** (the imperial
  pattern); the wool-cloth axis becomes Phyrascia-to-Teutonia trade.
  The Alpine tiles (10,18)-(10,19) and (11,12)-(11,14) with Erzberg are
  Teutonia's (the Austrian pattern); everything south of the Alps is
  Byzantium's; the Carpathian mine tiles (10,20) and (10,21) are
  Vellisclavia's.
- **Andalusia might be a vassal.** At worldgen roll d3: 1 Byzantium's
  vassal, 2 Umaia's, 3 independent. Stored as
  `world["lands"]["andalusia"]["liege"]` (a polity key or None), read
  by `politics_lines`, the map legend and the Reconquista template. No
  other mechanical effect in this arc.

## Session 5 — the rolled wars & the campaign sim

**The roll.** At worldgen, in `worldsim.open_world`'s world-level pass
(after every land's layer exists), on derived rng `f"wars:{seed}"`:
first Andalusia's vassalage d3, then THREE distinct wars drawn from the
six templates. No exclusion rules — any three coexist (the age was like
that). Each war stamps `at-war` on every belligerent land (a new
external state: news line, one `STATE_ENCOUNTERS` row of soldiery,
deserters and refugees), posts its herald line through `post_news`, and
is stored on `world["wars"]`: `{key, name, attackers, defenders,
theater, posture, herald, rolled_day, occupied: []}`. The new-game
print names the three wars where the story-layer line used to be.

**The six templates** (theater = an authored tile tuple, drawn at build
from the descriptions here; posture picks the event weights):

| key | name | belligerents | theater | posture |
|---|---|---|---|---|
| `crusade` | THE CRUSADE | 1-3 rolled of {byzantium, seraptania, teutonia, phyrascia} -> Umaia's east | the Levant around Jerusalem, (15,28)-(17,30) | invasion |
| `hundred-years` | THE LONG WAR | phyrascia -> seraptania | Seraptania's north and west coast and Aquitaine | invasion |
| `horde` | THE HORDE RIDES WEST | tergal -> vellisclavia | the steppe frontier, row 8 south edge and (9,20)-(10,21) | invasion |
| `vikings` | THE RAIDING SEASON | thule -> phyrascia AND seraptania | both coasts, channel and west | raiding |
| `reconquista` | THE RECONQUISTA | andalusia (backed by byzantium) -> Umaia's west; if Andalusia is Umaia's vassal, byzantium alone | south Iberia and the west Maghreb coast | invasion |
| `eastern-war` | THE EASTERN WAR | umaia -> byzantium | east Anatolia and the Levant border strip | invasion |

**The campaign sim** lives in `conquest.py` (the war machinery the game
already trusts: numbers against numbers, the garrison authority,
nothing the combat engine sees). `roll_campaigns(world, day)` — lazy,
day-stepped, seeded per war per day
(`stable_seed(seed, war_key, "campaign", day)`), watermarked on the war
record so catching up is living through it. Every `WAR_PULSE` (3) days
each war rolls ONE event on its posture's weights:

- invasion: lull 45, raid 25, army 10, battle 10, siege 10.
- raiding: lull 55, raid 40, siege 5.

Events write ordinary tile/settlement STATES (the record shape places
and lands already share, `since`-stamped; the sim clears its own
expired states when it rolls): `war-raided` (a theater tile, 30 days),
`war-camp` (an army sits, 10 days), `battlefield` (60 days),
`under-siege` (a theater settlement, 12 days) — resolved by a strength
roll of the attacker's tier band against `conquest.garrison_level`:
the town falls (`sacked`, 90 days, and — while the war holds fewer
than `OCCUPIED_CAP` 2 — `occupied`, permanent, occupier named) or the
siege lifts. Each event posts one news line to both belligerents. At
most 6 standing scar states per war; oldest cleared first. Surfaces:
the tile detail and DM brief print the states through the existing
state readout, `world` gains a wars block (belligerents, herald,
vassalage), and the map page is deliberately untouched. Driven from
the same day-settling seam as `conquest_news`.

**Non-goals, stated so they stay stated**: the sim never changes a
tile's country, never touches boards, quests, party holdings or
recruit pools, never ends a war, and occupation gates nothing — it is
a banner on the record and a line on the page. When dynamic borders
arrive (roadmap), they build on these records; nothing here needs
unbuilding.

**Tests and benches**: template well-formedness (theaters inside the
belligerents' tiles, every roll of three distinct and legal, vassalage
read where the Reconquista needs it), determinism per seed and across
the save, the state caps and expiries, siege resolution honoring the
garrison authority, a world left alone for 200 days staying bounded,
and `bench_worldgen` growing a wars sweep line.

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
  Goslar. Giving it the address is this arc's cheapest visible win. (The
  medieval world arc's campaign sim writes tile-level states directly and
  is a second customer for the same read surface.)
- **The past-epidemic population scar** — the plague chain's mark on the
  census, parked out of the census session (2026-08-21) and waiting for
  this arc's own trouble model.

## Politics & war (what the medieval world arc leaves here)

The nine countries, the raider culture, the era anchor and the standing
wars moved up into the arc contract above. Still parked here:

- **Dynamic borders and tile conquest** — real ones, where a front
  advances and a border redraws — once tiles are worth taking. The
  arc's campaign sim deliberately stops short of this; its war records
  and occupation states are the ground it would build on.
- **Languages with mechanics.** Session 3 SHIPPED who speaks what (the
  SPEAKS line) and dm.md's table rule; an engine reader — a rumor radius
  that stops at a language border, a quest gated on a tongue, an
  interpreter hired for a fee — is a later sitting. Nothing in the
  engine checks a tongue today.
- **Vassalage with teeth.** Andalusia's liege is rolled and printed;
  tribute, a pulled-in war, a court above the court are undesigned.

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
