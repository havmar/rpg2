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
names and tongues, the Thule packet, and the rolled wars. Its five
sessions are the next builds. Below the contract is the roadmap BEYOND
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
develop.md's "Where a finished feature is written up".

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

## Session 1 — the fallen banner (the old conquest questline goes)

The scripted main quest (`story.py`: one aggressor country, war waves at
levels 2/5/8/10, the Golden Empire / Undead Kingdom / Iron Horde) is
REMOVED, whole. It is three-country content at its core, the rolled wars
of session 5 replace its job, and deleting it first means no later
session renames a line of it.

- **Delete `story.py`** and every touchpoint: `session.py`'s
  `init_story` at `new`, save/load of `"story"`, `war_status_lines` in
  status and board, the map page's yoke tag and `-- the war --` block,
  `maybe_post_wave`, the wave-completion hook, all `occupied_here` /
  `occupation_line` gates, the `story_wave` pay routing, the new-game
  "story layer is armed" print, and the help copy naming war waves.
  Also `quests.is_ordinary_posting`'s `story_wave` clause and the
  `karma.py` comment.
- **The war feed goes with its one customer**: `worldsim.CASUS_BELLI`,
  `STANDING_CASUS_BELLI`, `roll_casus_belli`, `casus_belli_line` and
  their validation. Session 5's war templates carry authored herald
  lines instead. **`post_news` stays** — the campaign sim is its next
  customer.
- **`conquest.py` (the player's own holdings layer) STAYS** — conquer /
  garrison / holdings, tribute, raids, the heat floor. Only
  `seize_by_occupation` (which reads `story["fallen"]`) is deleted; the
  campaign sim of this arc never touches party holdings.
- **Docs and tests**: rules.md's Story Layer & Conquest add-on loses its
  questline half (the player-conquest half stays), dm.md's "The war"
  section goes, `test_worldsim.TheWarFeed` and every `story` assertion
  in `test_places` / `test_start` / `test_conquest` /
  `test_quest_geography` go, and state stubs drop `"story"`.
- **Interim contract**: the game runs warless and green; a new game
  prints no war line at all.

## Session 2 — the map of nine

The world builds and plays as nine countries. Everything worldgen needs
on day one lands in this session: the overlay, the catalog, the names,
the homeland plumbing, and a mechanically re-keyed worldsim.

**The country overlay.** A fourth authored grid,
`resources/europe_countries.txt`, letters on exactly the 314 land tiles
(`.` on sea). `country_at(row, column)` reads it instead of the
geometric split. The draft (this is the authored artifact; the build may
adjust single tiles but the pinned census then moves with it):

```
..............................
...............hhhhhhhhhh.....
...p.........hhhhhh.hhhhhh.vvv
...pp......hhhhhh...vvvvvvvvvv
.p.pp.....hhhhhh...vvvvvvvvvvv
.p..pp.......hh......vvvvvvvvv
...pppp....h......vvvvvvvvvvvv
........sstttttttttvvvvvvvvvvv
...ssssssssttttttttvvggggggggg
....sssssssttttttttvvggggggggg
.....ssssbbtttbbbbbbbbbb.g.ggg
.....ssaabbbbb.bbbbbbb......gg
.aaaaaaa....bb...bbb.........g
.aaaaa...b..bb...bb..bbbbbbbbb
..aaa......bbb........bbbbbuuu
......uuu.................uuuu
.uuuuuuuuuuuuuu...uu......uuuu
uuuuuuuuuuuuuuuuuuuuuuuuuuuuuu
```

(`p` Phyrascia, `s` Seraptania, `t` Teutonia, `h` Thule,
`v` Vellisclavia, `b` Byzantium, `a` Andalusia, `u` Umaia, `g` Tergal.)
A sea tile's country is DERIVED: the country of the nearest land tile by
tile distance, ties settled north-then-west like the pathfinder — no
hand-painted sea, no ambiguity. The `border` tag stays derived as today.
Pinned: the per-country biome census off this grid replaces
`PINNED_COUNTRY_BIOMES`, and the per-country BAND census (the bands are
campaign-invariant) is pinned beside it:

| country | land | wild | thin | low | mid | high | dense |
|---|---|---|---|---|---|---|---|
| phyrascia | 13 | 0 | 2 | 0 | 5 | 6 | 0 |
| seraptania | 23 | 0 | 0 | 2 | 3 | 16 | 2 |
| teutonia | 28 | 5 | 0 | 7 | 0 | 13 | 3 |
| thule | 37 | 9 | 24 | 0 | 1 | 3 | 0 |
| vellisclavia | 60 | 15 | 11 | 5 | 14 | 15 | 0 |
| byzantium | 51 | 1 | 5 | 3 | 22 | 10 | 10 |
| andalusia | 17 | 1 | 2 | 4 | 6 | 4 | 0 |
| umaia | 60 | 4 | 16 | 0 | 8 | 28 | 4 |
| tergal | 25 | 1 | 5 | 7 | 10 | 2 | 0 |

The census machinery itself (score, bands, arrangements, mines, harvest,
routes) does not change at all in this arc.

**Historical cities.** The sixteen keep their tiles and tiers and take
their new owners (Dublin and London Phyrascia; Paris Seraptania;
Amsterdam and Prague Teutonia; Stockholm Thule; Moscow and Warsaw
Vellisclavia; Kyiv Tergal; Venice, Rome, Athens and Constantinople
Byzantium; Lisbon and Madrid Andalusia; Carthage Umaia). THREE are
added: **Cordoba** (14,4), city, Andalusia's capital; **Cairo** (18,24),
METROPOLIS on the Nile, Umaia's capital — the fourth metropolis, the
biggest city of the age; **Jerusalem** (16,27), town, Umaia — the
crusade's prize. `CAPITAL_TILES` grows to nine (the capitals column of
the table above); each land's sky is read off its own capital as today.

**The catalog** (`place_catalog.json`, version 3). Top level:
`cultures` (settlement templates + natural inventories + natural
character map, keyed western/southern/steppe/norse — the existing
Firascir, Mortellaria and Tergal sets move under their culture names
unchanged) and `lands` (nine records: `name`, `culture`, `tongue`,
`description`; per-land template overrides possible later, none now).
The NORSE culture is authored new, Tergal-scoped: templates `capital`
(king's harbor), `walled_city`, `harbor_town` (fits coast),
`market_town`, `shore_village` (fits coast), `wood_village` (fits
forest), `field_village`, `cot_hamlet`; natural inventories
`taiga_wood`, `fells`, `skerry_coast`, `river_north` (three sites each),
mapped over the seven characters. `validate_catalog` learns the shape:
every culture covers every tier with a no-fits role, every land names a
real culture.

**The names.** Reuse before authoring: Phyrascia inherits Firascir's
settlement pools and person names whole; Byzantium inherits
Mortellaria's settlement pools; Tergal keeps both of its own. Authored
new: settlement pools for the six other countries and person-name lists
(25 male + 25 female, `people.NAMES` shape) for the seven countries that
lack one. Pool sizes per country — city 4, town 6, village 24
(Vellisclavia, Byzantium, Umaia) or 16 (the rest), hamlet 10; the
numbered-name fallback stays as the safety net. The sound briefs (per
writing.md: invented sounds, not real-language claims, ASCII only):

- Seraptania, French-flavored: Charmont, Vaudrienne, Roquefaille;
  people Thierry, Gaspard, Alienor, Margot.
- Teutonia, German-flavored: Falkenau, Steinbruck, Eberfeld; people
  Konrad, Dietrich, Adelheid, Greta.
- Thule, old-Norse mashup: Seljavik, Hrafnstad, Ulfsness; people Orm,
  Ketil, Astrid, Sigrun.
- Vellisclavia, old-Slavic-flavored: Dubrov, Zalesk, Mirogrod; people
  Bogdan, Vsevolod, Ludmila, Milena.
- Byzantium, Latin people (the places stay Mortellarian): Cassius,
  Petronius, Livia, Marcella.
- Andalusia, Spanish-flavored: Torrelava, Fuentebra, Almazora; people
  Alvaro, Rodrigo, Beatriz, Ines.
- Umaia, Arabic-flavored: Al-Qasrin, Bir Hakla, Wadi Sef; people Harun,
  Yusuf, Zaynab, Layla.

**The plumbing sweep.** `HOMELANDS` is nine. Every homeland-keyed
catalog either re-keys by culture (`quests.TEMPLATES`, `wild_pool`,
delivery skins — the norse culture gets five authored quest templates
of its own here, longship- and grove-flavored) or grows to nine rows
(`conquest.DEFENDER_ROLES`; `garrison_pool` stays `LADDER_POOL` for
all). `worldsim` is re-keyed MECHANICALLY in this session so the game
runs: card ids `firascir/*` -> `western/*` and `mortellaria/*` ->
`southern/*`, `land=` fields name cultures (resolved through a
`CULTURES` map to land tuples) or single lands where content is
land-specific, `_validate_three_countries` becomes
`_validate_countries` over nine, and Thule gets the MINIMUM the
validator demands as real content: one standing fact (THE GROVE) and
one relation edge. The full Thule packet and the per-card audit are
session 4's. The Miners' League land facts re-home to the actual mine
owners under the overlay: Teutonia (Goslar, Kutna Hora, Luneburg,
Erzberg), Vellisclavia (Banska Stiavnica, Wieliczka), Seraptania
(Melle), Thule (Falun), Byzantium (Novo Brdo).

**Tests**: the nine-country sweep replaces `TheThreeHumanCountries`
(closed homeland set over nine, records carry a homeland and never a
race, every country owed a deck, lore, a relation and a capital), the
overlay censuses pin, the border seam tests move off column 21, and the
name-pool validation covers nine.

## Session 3 — the towns & the tongues

**The town-name table.** The check the design asked for, run against
the overlay: a world seats ~615 settlements (~18 cities, ~101 towns,
~402 villages, ~92 hamlets, plus the four authored metropolises), and
the tiles that can EVER roll a town or city are exactly the mid, high
and dense band tiles — **185 of 314**, campaign-invariant. Per country:
Phyrascia 11, Seraptania 21, Teutonia 16, Thule 4, Vellisclavia 29,
Byzantium 42, Andalusia 10, Umaia 40, Tergal 12. So: one authored table,
`TILE_TOWN_NAMES: {(row, column): name}`, covering every mid/high/dense
tile not already named by `HISTORICAL_CITIES` or `MINES` (~160 new
names), each a REAL historical town placed on its plausible tile —
York, Bristol, Rouen, Bordeaux, Cologne, Nuremberg, Bruges, Uppsala,
Krakow, Novgorod, Milan, Naples, Thessalonica, Trebizond, Granada,
Sevilla, Toledo, Alexandria, Damascus, Fez, Tunis, Sarai, Kaffa and
their kin. The rule: when a tile's CHIEF slot materializes at town tier
or better and carries no authored name, it takes the tile's town name;
second towns on the same tile and everything village-down draw from the
generic pools. A tile's town name is used at most once. (Villages never
take real names — the real map at village grain would be a research
project, and the generic pools are the texture anyway.)

**The tongues.** The first mechanic on `homeland`. Nine languages, named
in fiction by their country ("the Seraptanian tongue"), except
Byzantium's, which is Latin — also the church-and-scholars tongue of
the whole west. `people.py` owns `LANGUAGES` (country -> tongue) and
rolls a character's tongues at creation: **everyone speaks Latin plus
their homeland's tongue; a Byzantine speaks Latin plus one random other
tongue.** The sheet gains a SPEAKS line; companions and the PC both.
NPCs carry no list — a local speaks the local tongue, and clergy,
scholars and officials speak Latin too, everywhere. No engine gate in
this arc: dm.md gets the table rule (if nobody in the party shares a
tongue with the speaker, the scene is gestures, coins and an
interpreter if one can be found; in Umaia, Latin reaches port traders
and officials, not villagers), and writing.md gets the name-sound table
of session 2 written down as the standing brief.

## Session 4 — the norse packet & the nine-land relations

**The Thule deck**, scoped like Tergal's (Tergal: 18 own crisis cards +
1 weather + the shared crown cluster, 4 tensions, 6 faction edges, 8
facts, 1 option, 4 constitutions). Pagan vikings; the sea is the
economy and the law is the thing. Authored (final copy per writing.md
at build):

- Crisis cards (~16-18): `norse/raid-season` (the ships go out; sets
  `raiding`), `norse/kings-share` (the sea-king claims a share of every
  catch), `norse/blood-feud`, `norse/weregild` (a man's price, haggled),
  `norse/the-thing` (the assembly at the stone), `norse/outlawed`
  (three years an outlaw; he takes to the hills), `norse/berserk-oath`,
  `norse/ring-giver-poor` (the chief's silver runs out; his men look
  elsewhere), `norse/land-taking` (a younger son stakes ground with
  hazel poles), `norse/grove-sacrifice` (nine of every kind hang at the
  grove), `norse/seer-speaks` (the seer names next winter's dead),
  `norse/curse-pole` (a carved pole with a neighbor's name on it),
  `norse/drowned-crew` (a ship did not come home), `norse/whale-ashore`
  (meat, and a brawl over shares), `norse/herring-run` (every boat
  out), `norse/ice-locked` (the harbors freeze shut), `norse/wolf-winter`
  (fodder gone, wolves at the byres), `norse/danegeld` (a foreign crown
  pays the fleet to stay home; sets `tribute-taken`). Plus the crown
  cluster where it fits and one weather card, `norse/white-storm`.
- Tensions (4): `jarls-vs-thing` (jarls / freeholders), `old-vs-new-gods`
  (grove priests / missionaries), `sea-vs-land` (sea-kings /
  land-chiefs), `feud` (two feuding houses). Faction edges: 6 over
  those blocs.
- Facts (7): THE GROVE (from session 2), ship-burial, the seer and the
  thread of fates, the land-spirits, the drowned belong to the sea, the
  thing's law and outlawry, and Thule's League fact naming Falun.
- Option (1): `norse/weather-witch` — bought wind (`does="sky"`), the
  rain stone's northern cousin.
- Constitutions (4, default-heavy): THE SEA-KINGS, THE ALLTHING, THE
  HIGH KING, THE SCATTERED JARLS.

**The card audit.** Every re-keyed western and southern card is read
once against its new scope: culture-wide by default; land-specific
content narrows to one land (the necromancy/death-rite/carnival cluster
and the schism material to Byzantium; `weather/smog` to Teutonia, the
close-built northern towns' own; anything naming a river, coast or city
to the land that holds it now). The calls the audit settles go in the
designlog, per the standing rule.

**The relations table**, re-authored whole for nine lands (~20 edges,
every land reached; same record, same one-hop derivation): Baltic grain
vellisclavia->thule and Nile grain umaia->byzantium (`grain-scarce`);
steppe raids tergal->vellisclavia and sea raids thule->phyrascia,
thule->seraptania (`raiders-out`); timber thule->seraptania
(`timber-dear`); Lombard coin byzantium->seraptania (`credit-dry`); the
southern road byzantium->teutonia (`southern-goods-short`); horses
tergal->vellisclavia and andalusia->seraptania (`horses-dear`);
livestock tergal->byzantium (`hides-dear`); hired swords
tergal->byzantium (`swords-gone`); wool phyrascia->teutonia (new word
`wool-short`, one `STATE_MENU` row); gold caravans umaia->andalusia
(`southern-goods-short`); the diplomatic instruments re-homed — hostage
tergal->vellisclavia, danegeld thule->phyrascia, marriage
seraptania->phyrascia, union phyrascia->seraptania (the claim to the
French crown); and the schism clock byzantium<->seraptania (the old
rite and the western church, both directions). Each land also owes at
least one standing fact of its own by the end of this session
(Seraptania, Teutonia, Vellisclavia, Andalusia, Umaia and Phyrascia
each get one signature fact beside their culture's shared lore).

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
- **Languages with mechanics.** The arc records who speaks what and
  gives dm.md the table rule; an engine reader (rumor radius, quest
  gating, an interpreter hire) is a later sitting.
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
