# RPG2 — Place Generation Design and Content Draft

Status: **planned, not implemented**. This is the reviewable design and first
content inventory for procedural place generation. `rules.md` continues to
describe the shipped game; `plan.md` points here while the system is pending.

The generator extends the persistent **Land -> Area -> Site -> Room** world
tree already used by quests and navigation. It is meant to give the DM compact,
permanent facts to present and act on. It does not generate paragraphs of
atmosphere.

All strings intended to become game output are ASCII and follow `writing.md`:
plain fantasy nouns, concrete details, one useful fact first.

## Goals

- Give every playthrough a world which is different but stable.
- Keep the world's large-scale identity deliberate and memorable.
- Let local exploration continue producing Sites and Rooms as needed.
- Make ordinary places common. A forest should usually be a forest, not a
  stack of curses and novelties.
- Support features which are public, locally known, discoverable, or hidden.
- Support mutable conditions such as blight, occupation, fire, or recovery.
- Give quests persistent places to reveal, reuse, and change.
- Keep generated content as labels, facts, and small persistent Room-content
  lists. Ordinary furnishings and objects should make an interior concrete
  without requiring prose.

## Non-goals for the first implementation

- Generating the continental ASCII map.
- Simulating weather, ecology, trade, or settlement populations realistically.
- Making every feature mechanical.
- Generating unlimited unique prose.
- Building a general inventory, ownership, or object-physics system. The MVP
  may list and inspect lightweight Room contents; only objects which already
  map to a mechanical item need inventory behavior.
- Automatically turning every interesting feature into a quest.
- Preserving old save formats. Development saves remain disposable.

## The central division: authored silhouette, generated local detail

| Scope | Authored | Generated |
|---|---|---|
| World | Continental shape, adjacency, major factions | Nothing initially |
| Land | Identity, culture, default environment, major wonder | Lesser names where desired |
| Area | Three or four major natural themes per Land; unique cities | Names, ordinary settlement details |
| Site | Unique landmarks and story-critical places | Most ordinary natural and built places |
| Room | Important set-piece spaces | Most layouts, contents, and local details |
| Feature | World wonders and culture-defining facts | Ordinary traits, conditions, and curiosities |

An authored place may still use generated facets. A handcrafted forest theme
can receive a generated name, and a handcrafted capital can roll ordinary
street and resource details without surrendering its identity.

Unique facts are never taken from ordinary random pools. Caelum, a world-tree,
or the only bridge between two realms is authored. Random tables produce local
variation, not replacement wonders.

## Scale and materialization

### Lands and Areas are finite

Each Land has a small authored inventory of important Area roles:

- normally three or four natural Areas;
- settlement Areas appropriate to the Land;
- optional unique Areas such as Caelum or a fortress-city.

Some Areas are public from the beginning and some start unknown. `explore`
reveals this finite inventory. It does not create a new forest, moor, or cave
country forever.

After a Land's major Areas have been found, exploration works inside the
current Area and reveals or creates Sites.

### Sites and Rooms are lazy and persistent

Sites are materialized when:

- an Area is explored;
- a quest needs a suitable destination;
- the DM asks for an ordinary local place;
- a world event creates one;
- a required settlement service becomes navigable.

A generated Site may create its whole small Room layout immediately so its
shape is coherent, while keeping individual Rooms and features unknown until
found. Once materialized, the complete result is saved and never rerolled on
return.

The system is unbounded over a campaign, not infinitely novel. Repetition is
controlled by used-entry sets, scope limits, and template variety.

### Gameplay scale decides the tier

- A normal castle is a Site.
- A fortress-city with independent districts is an Area.
- A small village may be a Site in a rural Area if it does not need its own
  travel hub and quest board.
- A huntsman's cabin may be a Site when it has rooms of its own, or a Room
  when it is one immediate scene.
- A Site may have no Rooms. The Site itself is the default scene.

No dummy `forest site`, `forest room`, or `altar room` repeats its parent.

## Land identity is separate from race

The current placeholder world keys Lands by race. The planned world needs
independent Land records because:

- two human realms have different climates;
- several Lands may share a culture or faction;
- a Land may be mixed, wild, disputed, or conquered;
- a pirate faction may hold more than one archipelago;
- ownership may change.

Conceptual Land record:

```text
Land
  id
  name
  owner or faction
  cultures
  default environment profile
  encounter profile
  Area IDs
  neighboring Land IDs
  famous features
```

Race continues to drive people, cultural names, arms, and some encounter
content. It does not identify geography.

The future grid is a projection, not a fifth place tier. A map cell may
reference a Land and a terrain symbol. A Land may occupy several cells.

## Planned culture and environment distribution

| Planned Land | Culture | Environment |
|---|---|---|
| Icy dwarf mountains | Dwarf | Alpine tundra |
| Temperate human country | Human, temperate | Temperate |
| Mediterranean human country | Human, mediterranean | Mediterranean |
| Elven forest | Elf | Temperate forest |
| Wild forest | None fixed | Temperate forest |
| Goblin mediterranean country | Goblin | Mediterranean |
| Orc prairie | Orc | Prairie |
| Northern pirate islands | Pirate | Cold archipelago |
| Tropical pirate islands | Pirate | Tropical archipelago |
| Jungle | None fixed | Jungle |
| Desert | None fixed | Desert |
| Caelum | Angel/devil, mixed | Authored urban; undecided |

Dwarf, elf, goblin, and orc culture each have one primary environment. Human
and pirate culture each span two. Mediterranean is shared by human and goblin
Lands; temperate forest is shared by the elven and wild forests. Jungle,
desert, and the wild forest do not yet require a governing culture. Caelum is
an authored exception.

`Temperate forest` is the elven forest's practical temperate-oceanic analogue:
mild or cool, damp, frequently overcast, and heavily wooded. Environment
profiles are game-content bundles, not scientific climate classes.

## Environment inheritance

A Land's environment profile supplies:

- a climate label;
- a weighted weather table;
- a vegetation palette;
- common terrain tags;
- common natural Site and feature pools;
- optionally a wilderness encounter profile.

An Area inherits the profile and adds or overrides local facts. Children read
their ancestors' tags when choosing content; inherited facts are not copied
onto every child.

Climate is not current weather. `temperate` makes rain likely; it does not
make a permanent `rainy` feature. Current weather can later be rolled by day.
Persistent fog, magical snowfall, or a wind that never stops are place
features.

Recommended development labels:

- alpine tundra
- temperate
- temperate forest
- mediterranean
- prairie
- cold archipelago
- tropical archipelago
- jungle
- desert

`Woody` becomes `temperate forest`; `grasslands` becomes `prairie`; `nordic`
is reserved for culture while `subarctic`, `alpine tundra`, or `cold maritime`
describe environment.

## Place records

The exact Python representation can change during implementation. The
conceptual separation should not.

```text
Place
  identity
    id
    name
    parent
    template
    source: authored | worldgen | lazy | dm
    generation seed

  facets
    required or exclusive structural choices

  features
    optional persistent descriptive facts

  states
    mutable conditions and occupants

  services and resources
    mechanically or socially useful facts

  children
    child IDs in stable order

  links
    borders, roads, exits, and shortcuts

  knowledge
    known, visited, and feature discoveries
```

Connections are not features. An exit to another Land is a link. An important
marketplace is a Site. A famous smith modifies a service, person, or smithy.

### Natural and built classification

Natural and constructed places use the same hierarchy rather than parallel
trees.

- Area `kind` remains broadly `natural` or `settlement`.
- Sites and Rooms may carry `domain: natural | built | mixed` for template
  routing.
- A cave is natural.
- A cathedral is built.
- A forest altar or garden inside a ruin is mixed.
- A ruin remains built even when plants have reclaimed it.

`Domain` selects materials, features, and child templates. It does not decide
whether a place may stand inside a natural or settlement Area: a hunter's hut
belongs in a forest, and a riverbank may be a natural Site inside a city.

### Template definitions

A place template provides:

```text
id and scope
required facet slots
optional exclusive slots
additive feature pools
mutable state pools
child Site or Room roles
required content anchors and optional content pools
naming rules
applicability tags
generation limits
```

### Feature definitions

A feature definition provides:

```text
id
label or DM fact
category
allowed scopes and templates
weight or rarity
requirements
exclusions
default reveal rule
per-Place, per-Area, or per-Land limit
mutable or permanent
optional hook tags
```

The catalog owns constraints. A saved instance primarily needs the selected
feature ID, whether it is known, whether it is active, and any local state.

## Kinds of place fact

### Core identity

Always present and not counted as a feature: forest, cathedral, path, town,
bandit camp. A normal forest is already complete.

### Required facets

One value from a template-specific slot:

- cathedral material;
- cathedral form;
- path surface;
- settlement wealth;
- room furnishing, when furnishing matters.

Required facets do not count against the optional feature budget.

### Optional exclusive slots

Zero or one value from a category:

- forest condition;
- construction state;
- route quality;
- room furnishing beyond the implicit ordinary result.

Absence is the ordinary result. `None` is not a content entry.

### Optional additive features

Compatible persistent details such as flowering, mossy, fruit-bearing,
tree-filled, or foggy.

### Mutable states

Current conditions and uses such as diseased, occupied, unfinished, flooded,
patrolled, or recovering. A quest or world event may add, replace, or resolve
them without replacing the place's identity.

### Notables and curiosities

Rare, concrete, authored facts intended to carry memory. They should be whole
details rather than adjective fragments:

- an oak has grown around a bronze bell;
- a dry well rings when a stone is dropped into it;
- every statue faces the cellar door.

Unique world wonders remain authored.

### Room contents and lightweight objects

A generated Room may carry a small ordered `contents` list. These records make
ordinary interiors concrete: a house can contain a hearth, table, stools,
tools, food, and one personal object without requiring a general item engine.

Conceptual content record:

```text
content ID
label
category: fixture | furniture | tool | food | container | personal | valuable
reveal: visible | search | hidden
state, optional
mechanical item reference, optional
```

Room templates provide one or two required anchors and an optional content
pool. An inhabited ordinary Room should normally resolve to two to five
visible objects or compact object groups. It may also hold one searched or
hidden object. Contents are generated once from the Room seed, saved, and do
not reroll on return.

Object labels are facts, not automatic loot. A table, fishing net, locked
chest, or loaf of bread may be listed and inspected without becoming a
portable inventory item. A potion, weapon, key, or other existing mechanical
item may carry a reference into the relevant game catalog. Residents attach
to the house or Room as NPC IDs; this does not require universal ownership
rules for every object.

## Feature count and rarity

The optional feature-count distribution is:

| Optional features | Chance |
|---|---:|
| 0 | 50% |
| 1 | 30% |
| 2 | 15% |
| 3 | 5% |

This gives a 50% chance of at least one feature, a 20% chance of at least two,
and a 5% chance of three. Required facets and mandatory children do not count.

Within a selected pool, the first-pass rarity target is:

| Rarity | Approximate share |
|---|---:|
| common | 75% |
| uncommon | 20% |
| rare | 5% |
| unique | never randomly rolled |

These are content-balancing targets, not necessarily a second literal roll.
Entry weights may implement the same result directly.

Rules:

- at most one rare optional feature per place;
- no duplicate feature on one place;
- respect exclusive slots before pairwise exclusions;
- respect `requires` and `excludes`;
- a rare entry may be limited to once per Area or Land;
- do not repeat the parent's defining feature as child filler;
- avoid repeating the same Site template in an Area until its ordinary pool
  has been used;
- the DM-facing summary leads with one defining detail and does not enumerate
  every stored fact.

Category design should prevent contradictions before pairwise rules are added.
For example, `earth` and `stone` compete in the path-surface slot, while
`muddy` is a separate condition and may apply to earth but not fitted stone.

## Knowledge and reveal rules

`Renown` is reserved for the reputation of people and deeds. Place facts use
the following reveal levels:

| Reveal | When it becomes known |
|---|---|
| public | whenever the parent place is known |
| local | on arrival or after asking around |
| explore | on entering, searching, or exploring |
| hidden | only through a named interaction, quest, or DM reveal |

A feature exists before it is known. Discovery changes player knowledge, not
the generated world.

Examples:

- the White Forest's pale trees: public;
- a huntsman's cabin near the edge: local;
- the charred oak in the deep wood: explore;
- the crypt beneath the forest altar: hidden.

## Salience and DM output

Scope, rarity, reveal, and salience are separate:

- **scope** says which place owns the fact;
- **rarity** says how often it is generated;
- **reveal** says when the player learns it;
- **salience** says whether it leads the description.

The generator may store several facts, but the normal place display uses:

1. place identity;
2. one defining or currently actionable fact;
3. one obstacle, inhabitant, or exit if relevant.

Secondary traits are available to `look`, exploration, and the DM's state
readout. This protects the fiction register from feature dumping.

## Mutation

Stable identity and active state remain separate:

```text
White Forest
  identity: temperate forest
  stable feature: pale-barked trees
  active state: diseased
```

A curing quest may replace `diseased` with `recovering`, then later with no
adverse state. If history becomes valuable, the event log records that the
blight was cured; the active place record need not retain dead state forever.

State transitions may define:

```text
active state
allowed resolutions
replacement state
features suppressed while active
optional quest or event tags
```

`Scorched` suppresses flowering and fruit-bearing while active. `Recovering`
may allow moss and new growth.

## Seed policy

- World creation chooses the authored variants and generated high-level facts
  from the world seed.
- Every lazy place receives a stable child seed derived from the world seed,
  parent ID, generation purpose, and child sequence.
- Do not use Python's process-randomized `hash()` for derivation.
- The full materialized result is saved. Re-entering never regenerates it.
- A DM-authored place is canonical because it is saved, even if it has no
  random provenance.
- A DM-requested generated place consumes or derives a stable world seed and
  is saved like any other.
- Player and quest mutations are events, not seed results.
- Daily weather and off-screen events use campaign state and day rather than a
  place's generation seed.

## Quest integration

Quests retain premise, giver, progress, alignment, and rewards. They point at
persistent world Sites.

When a quest needs a target:

1. determine the required Area tags from the quest template;
2. prefer a suitable existing Area;
3. prefer a compatible unused Site when reuse makes sense;
4. otherwise materialize a new Site in that Area;
5. reveal only the target and facts the quest should expose;
6. apply quest results as state changes to the Site, Area, or settlement.

A wolf hunt should choose pasture, hills, or forest. A mine quest should
choose highlands, badlands, or a mining settlement. It should not place
`the mountain slopes` inside the giver's settlement merely because that is
where the quest was posted.

Features may carry hook tags such as `blight`, `missing_person`, `resource`,
`monster_threat`, or `hidden_entrance`, but automatic quest creation is not
required in the first implementation.

## Current placeholder audit

The existing records and tables are useful scaffolding, not content to discard
wholesale.

### Keep

- The persistent Land -> Area -> Site -> Room ownership model.
- Stable IDs and ordered child ID lists.
- `known` and `visited` place state.
- The seeded world stored in the save.
- Quest records pointing at world-owned Site IDs.
- Cultural settlement-name fragments as the seed of culture profiles.
- Natural subtype vocabulary such as forest, woodland, wetland, highlands,
  caverns, riverland, badlands, lake, and hills.
- Quest template Site stems as hints about suitable Site roles.
- The encounter builder and foe pools; descriptive generation should not
  disturb their calibrated threat math.

### Replace

- Race-keyed Lands with independent Land records carrying culture and owner.
- The random `one capital + three towns + two villages` world outline with an
  authored realm and Area inventory.
- Unlimited `explore` creation of Areas with finite Area discovery followed by
  Site-level exploration.
- The one global natural-name prefix/suffix table with environment- and
  subtype-specific pools.
- Generic Room names (`the approach`, `the way in`, `the outer chamber`, `the
  inner chamber`, `the heart of it`) with template Room roles and concrete
  place names.
- Quest target placement in the giver's settlement with selection of a
  context-appropriate Area and Site.
- `Site.kind = quest` as the place's identity. A quest is a relationship to a
  Site, not a geographic kind; the Site retains its own template and domain.

### Reuse after sorting

- `Black`, `Red`, `Mist`, `Thorn`, `Crow`, `Elk`, `Adder`, `Howling`,
  `Broken`, and `Old` remain useful name modifiers, but not for every biome.
- `fen`, `ridge`, `wood`, `moor`, `caves`, `falls`, and `barrens` remain
  usable after scale and environment filtering. `Hollow` usually belongs to
  a small Area or Site. `Cairn` is normally a landmark or Site. Cut `tarn`
  from the general pool in favor of the immediately readable `lake`.
- Existing human, elf, orc, dwarf, and goblin settlement fragments move from
  race-owned Lands to culture profiles. Add mediterranean human and pirate
  profiles.
- Quest Site stems such as `the roadside camp`, `the high pasture`, `the
  crypt below`, and `the forest road` become template requests. Some should
  reuse existing geography instead of always creating another Site.

### Add

- Land environment and encounter profiles.
- Finite authored Area roles and discovery order.
- Facets, optional features, mutable states, per-feature reveal state, source,
  salience, and stable generation seed.
- Natural/built/mixed domain tags.
- Services, resource facts, and structural links.
- Compatibility constraints and scope limits.
- Used-entry tracking for repetition control.
- Context requirements on quest templates.
- A DM-facing fact summary separate from the player-facing place description.

## Settlement model

A settlement is generated from:

```text
tier
culture and owner
geographic setting
wealth
resource facts
required services
optional Sites
civic states
named specialties and notables
```

Recommended tiers:

- capital;
- city;
- town;
- village;
- hamlet, normally a Site rather than an Area.

Five to ten settlements per country may exist in fiction, but they need not
all be equal macro destinations. Capitals, cities, towns, and independent
villages are Areas. Minor hamlets which do not need their own travel hub,
shops, and board are Sites in rural Areas.

MVP settlement inventory for an ordinary culturally settled Land:

- one authored capital Area;
- two or three authored town Areas;
- three procedurally generated village Areas at world creation.

The initial dwarf Land is deliberately smaller: one capital and two towns,
with no additional generated villages. Wilderness Lands and unique Caelum do
not inherit this count automatically.

Ordinary houses materialize lazily as Sites when explored or requested. The
generator does not instantiate a realistic census, but any settlement can
produce a persistent resident, house, Rooms, and Room contents when play needs
one.

### Services are not automatically Sites

Every ordinary settlement guarantees:

- lodging or tavern;
- smith service;
- general goods.

Every capital additionally guarantees:

- alchemist;
- major market;
- government seat.

Other settlements may roll an alchemist. A service materializes as a Site
when entering it creates a scene or decision. Until then it remains a useful
settlement fact.

An important marketplace is a Site. A famous smith attaches to the smith
service, its NPC, and eventually its smithy Site. Oppressive leadership is a
mutable civic state.

# CONTENT DRAFT

The lists below are deliberately broader than the first implementation needs.
Review should cut weak or redundant entries before they become data.

Weights are shown as rarity labels rather than final numeric constants.
`Normal` is usually implicit absence, not a selectable string.

## Environment profiles

### Alpine tundra

Climate summary:

- Cold, windy highlands with long winters and short summers.

Weather:

- clear cold;
- hard wind;
- light snow;
- heavy snow;
- mountain fog.

Vegetation:

- dwarf pine;
- juniper;
- lichen;
- moss;
- alpine grass;
- mountain flowers.

The Alpine Tundra base content is concrete in the accepted icy dwarf Land
catalog below. Generic natural-Area and Site suggestions were removed after
review; the Land owns its finite named Areas and their accepted Site pools.

### Temperate

Climate:

- mild rain;
- cloud;
- clear weather;
- wind;
- autumn fog;
- winter frost.

Vegetation:

- oak;
- beech;
- ash;
- elm;
- hedges;
- meadow grass;
- reeds along water.

Natural Areas:

- farmland;
- pasture;
- broadleaf forest;
- grassy hills;
- river valley;
- wetland.

Common Sites:

- field road;
- hedged lane;
- copse;
- mill stream;
- old bridge;
- shepherd's hut;
- ruined farm;
- roadside shrine.

### Temperate forest

Climate:

- frequent shade and damp;
- light rain;
- morning mist;
- summer storms;
- winter frost.

Vegetation:

- oak;
- beech;
- birch;
- fern;
- bramble;
- moss;
- mushrooms.

Natural Areas:

- deep forest;
- old woodland;
- forested hills;
- river wood;
- misty hollow.

Common Sites:

- forest edge;
- old path;
- deep wood;
- grove;
- stream crossing;
- clearing;
- den;
- hunter's camp;
- altar;
- boundary path.

### Mediterranean

Climate:

- hot dry summer;
- mild wet winter;
- sea wind;
- brief hard rain;
- dusty inland heat.

Vegetation:

- olive;
- cypress;
- pine;
- scrub oak;
- grapevine;
- rosemary;
- dry grass.

Natural Areas:

- olive country;
- vineyard hills;
- rocky coast;
- dry uplands;
- pine valley;
- river plain.

Common Sites:

- terrace;
- vineyard road;
- spring;
- ruined villa;
- hill shrine;
- sea cave;
- watchtower;
- shepherd's fold.

### Prairie

Climate:

- strong wind;
- hot summer;
- cold winter;
- sudden storm;
- long dry spell.

Vegetation:

- tall grass;
- short grass;
- sage;
- wildflowers;
- reeds near rivers;
- scattered cottonwood or willow.

Natural Areas:

- open prairie;
- rolling grassland;
- river plain;
- broken hills;
- dry basin;
- grazing range.

Common Sites:

- herd trail;
- watering place;
- lone tree;
- grass fire scar;
- burial mound;
- hunter's camp;
- ravine;
- standing stones.

### Cold archipelago

Climate:

- cold rain;
- sea fog;
- hard wind;
- sleet;
- short bright summer.

Vegetation:

- heather;
- coarse grass;
- low pine;
- rowan;
- kelp;
- cliff flowers.

Natural Areas:

- rocky island;
- sheltered sound;
- sea cliffs;
- peat upland;
- pine island;
- storm coast.

Common Sites:

- fishing cove;
- sea cave;
- cliff path;
- beacon;
- wreck;
- turf hut;
- stone jetty;
- seal beach.

### Tropical archipelago

Climate:

- heat;
- warm rain;
- sea breeze;
- sudden storm;
- humid calm.

Vegetation:

- palm;
- mangrove;
- breadfruit;
- flowering vine;
- bamboo;
- dense coastal scrub.

Natural Areas:

- palm island;
- mangrove lagoon;
- coral coast;
- volcanic ridge;
- jungle interior;
- river mouth.

Common Sites:

- hidden cove;
- reef passage;
- wreck;
- beach camp;
- freshwater pool;
- sea cave;
- abandoned fort;
- rope bridge.

### Jungle

Climate:

- heavy rain;
- humid heat;
- afternoon storm;
- river mist;
- short dry spell.

Vegetation:

- tall broadleaf trees;
- palm;
- bamboo;
- fern;
- thick vine;
- orchids;
- giant leaves.

Natural Areas:

- deep jungle;
- flooded forest;
- river basin;
- high jungle;
- vine-choked ruins;
- mangrove edge.

Common Sites:

- game trail;
- river crossing;
- ruined stair;
- sinkhole;
- giant tree;
- vine bridge;
- hunter's shelter;
- overgrown shrine.

### Desert

Climate:

- dry heat;
- cold night;
- dust wind;
- rare hard rain;
- morning haze.

Vegetation:

- thorn scrub;
- salt grass;
- hardy flowers after rain;
- date palm at water;
- dry reeds;
- succulents.

Natural Areas:

- dune sea;
- stony desert;
- salt flat;
- canyon country;
- dry river basin;
- oasis belt.

Common Sites:

- well;
- caravan track;
- rock shelter;
- ruined watchtower;
- dry cistern;
- oasis;
- tomb entrance;
- wind-carved arch.

## First concrete Land structure: icy dwarf mountains

This is the non-wording structure behind the current string worksheet.

- Culture: dwarf.
- Default environment: alpine tundra.
- Natural Areas: Drunurnar Mountains, Krokskogur Forest, and Lake Hornindal.
- Settlement Areas: Bjorgheim, the central capital; Roros, the remote northern
  town; and Svalaver, the southern fishing and trade town.
- No additional generated villages at world creation.
- The southern town connects directly to the temperate human Land and is the
  dwarf-human trading hub.

Working arrangement:

```text
                            northern town
                                 |
                           mountain range
                                 |
                           central capital
                              /       \
                         pine forest  cold lake
                              \       /
                           southern town
                                 |
                       temperate human Land
```

The lake and southern town are sibling Areas. The lake owns the open water and
unsettled shore; the town owns the built southern shore. The northern town and
mountains follow the same rule: wilderness stays in the natural Area, while
walls, streets, services, and houses belong to the settlement Area.

Natural Sites, starting settlement Sites, their Room roles, and ordinary
content pools are reviewed as strings in `placegen_review.txt`. Accepted names
and wording return to the concrete content catalog in this file.

### Accepted Area strings

**Drunurnar Mountains** — natural Area, mountains.

> An ice-capped range fills the western Land.

**Krokskogur Forest** — natural Area, forest.

> Dwarf pine covers the valley below the mountains.

**Lake Hornindal** — natural Area, lake.

> A great cold lake fills the basin. Ice remains in its coves and along its
> northern shore through the short summer.

**Bjorgheim** — settlement Area, capital.

> A walled stone city stands where the mountain roads meet.

**Roros** — settlement Area, northern town.

> A remote stone town guards the northern pass. Snow lies against its walls
> through most of the year.

**Svalaver** — settlement Area, southern fishing and trade town.

> A stone fishing town stands on the southern shore. Dwarf and human merchants
> meet beside its jetty.

### Accepted natural Site, Room, and content strings

**Drunurnar Mountains**

```text
HIGH PASS — Site
  PASS ROAD — Room
    stone markers
    ice-crusted cart ruts
    warning post
  WIND SHELTER — Room
    low stone wall
    dead firepit
    stack of split wood

ABANDONED MINE — Site
  MINE ENTRANCE — Room
    broken ore cart
    timber props
    rusted chain
  WINCH ROOM — Room
    hand winch
    frayed rope
    empty ore baskets
  LOWER TUNNEL — Room
    old rail
    standing water
    collapsed side passage

WATCH POST — Site
  LOOKOUT — Room
    signal brazier
    iron bell
    mountain map
  GUARD ROOM — Room
    bench
    weapon rack
    coal box
```

**Krokskogur Forest**

```text
OLD FOREST ROAD — Site
  FROZEN STREAM CROSSING — Room
    plank bridge
    ice-covered ford
    road marker
  LOGGER'S TURN — Room
    stacked timber
    drag sled
    wood chips

LOGGING CAMP — Site
  FIREPIT — Room
    stone fire ring
    log benches
    black cooking pot
  STORE HUT — Room
    axes
    rope coils
    timber wedges

STONE SHRINE — Site
  carved stone
  offering bowl
  iron candle stand
```

**Lake Hornindal**

```text
NORTH SHORE — Site
  SHINGLE BANK — Room
    flat stones
    driftwood
    overturned skiff
  ICE COVE — Room
    shore ice
    mooring ring
    abandoned fish basket

ICE-FISHING GROUND — Site
  FISHING HOLES — Room
    cut ice holes
    low windbreak
    bait box

FROZEN INLET — Site
  REED BANK — Room
    dry reeds
    narrow footbridge
    animal tracks
```

### Accepted settlement Site and Room strings

Required Sites materialize with their settlement. Optional ordinary Sites
materialize lazily when requested or explored and then persist.

**Bjorgheim**

```text
CLAN HALL
  GREAT HALL
  COUNCIL ROOM
  RECORDS ROOM
MAIN MARKET
  FOOD ROW
  SMITHS' ROW
  HUMAN YARD
WARM HEARTH INN
  COMMON ROOM
  KITCHEN
  CELLAR
  GUEST ROOM
BJORGHEIM SMITHY
  FORGE
  YARD
  STORE ROOM
GENERAL SHOP
  SALES ROOM
  STORE ROOM
ALCHEMIST'S SHOP
  SHOP
  WORK ROOM
  LOCKED STORE
SOUTH GATE
  GATE PASSAGE
  GUARD ROOM
```

Optional ordinary Sites:

- ordinary house;
- brewery;
- temple;
- warehouse;
- barracks;
- guildhall.

**Roros**

```text
NORTH WATCH
  GATE PASSAGE
  GUARD ROOM
  SIGNAL PLATFORM
LAST FIRE INN
  COMMON ROOM
  KITCHEN
  GUEST ROOM
  GOAT SHED
ROROS SMITHY
  FORGE
  STORE ROOM
GENERAL SHOP
  SALES ROOM
  STORE ROOM
MINE OFFICE
  CONTRACT ROOM
  EQUIPMENT STORE
```

Optional ordinary Sites:

- ordinary house;
- ore warehouse;
- mountain shrine;
- brewery.

**Svalaver**

```text
TRADE HALL
  PUBLIC COUNTER
  RECORDS ROOM
  MERCHANT ROOM
STONE JETTY
  LANDING
  NET YARD
FISH MARKET
  FISH STALLS
  HUMAN YARD
LAKESIDE INN
  COMMON ROOM
  KITCHEN
  CELLAR
  GUEST ROOM
SVALAVER SMITHY
  FORGE
  STORE ROOM
GENERAL SHOP
  SALES ROOM
  STORE ROOM
SMOKEHOUSE
  CUTTING ROOM
  SMOKE ROOM
  SALT STORE
```

Optional ordinary Sites:

- ordinary house;
- human warehouse;
- boat shed;
- small temple;
- brewery.

This completes the icy dwarf Land's **basic string pass**. It does not accept
or reject the special, nonessential feature pools below. Those pools remain
draft material until the later global special-feature review phase.

## Natural Area feature pools

### Forest: optional additive features

Common:

- flowering undergrowth;
- heavy moss;
- fruit-bearing trees;
- frequent mushrooms;
- thorny undergrowth;
- giant boulders;
- many fallen trees;
- shallow streams;

Uncommon:

- persistent fog;
- unusually pale bark;
- trees grown over old walls;
- a great number of birds;
- no birds at all;
- unusually large mushrooms;
- dense hanging vines;

Rare:

- faintly glowing plants;
- trees which bleed clear sap;
- a bell heard with no visible source;
- stone faces grown into the roots;

Constraints:

- `fruit-bearing` excludes `scorched`;
- `flowering` excludes `scorched`;
- `heavy moss` requires damp or shade and excludes active fire;
- `persistent fog` is a microclimate, not daily weather;
- `glowing plants` is rare and once per Area.

### Forest: mutable condition slot

Common or uncommon:

- diseased;
- dying;
- scorched;
- polluted;
- flooded;
- storm-damaged;
- overhunted;
- occupied by loggers;
- frequented by a monster family;

Resolution or replacement:

- recovering;
- new growth;
- abandoned by the occupants;
- water cleared;

Recommended consolidation before implementation:

- use `blighted` when disease and magical decay do not need separate behavior;
- keep `dying` only for drought, age, or deliberate destruction;
- keep monster presence as an occupant/threat state rather than vegetation.

### Hills and highlands: optional features

Common:

- exposed rock;
- sheep or goat pasture;
- scattered thorn bushes;
- many small streams;
- old field walls;
- wind-bent trees;

Uncommon:

- standing stones;
- abandoned terraces;
- sinkholes;
- hot spring;
- fossil beds;
- frequent landslides;

Rare:

- stones which hum in high wind;
- a stair cut into a cliff with no building above it;
- lightning repeatedly strikes one bare summit.

### Wetlands: optional features

Common:

- reed beds;
- willow islands;
- deep mud;
- clear pools;
- clouds of insects;
- many water birds;

Uncommon:

- drowned road;
- peat fires;
- floating mats of flowers;
- salt water far inland;
- old posts marking a lost boundary;

Rare:

- pale lights move beneath the water;
- a stone doorway stands in the deepest pool;
- the frogs fall silent around one island.

### Prairie: optional features

Common:

- tall grass;
- wildflowers;
- herd trails;
- scattered boulders;
- dry creek beds;
- frequent wind;

Uncommon:

- burned grass;
- abandoned corrals;
- great animal bones;
- prairie-dog mounds;
- a seasonal lake;

Rare:

- one circle of grass always grows green;
- a line of buried bronze markers crosses the plain;
- a lone tree bears fruit from another climate.

### Coast and island: optional features

Common:

- tide pools;
- shell beaches;
- high cliffs;
- strong currents;
- driftwood;
- nesting birds;

Uncommon:

- black sand;
- a wreck visible at low tide;
- caves flooded at high tide;
- a warm spring;
- abandoned fish traps;

Rare:

- a bell rings beneath the water;
- every compass turns toward one reef;
- a stone road appears at the lowest tide.

### Desert: optional features

Common:

- wind-cut stone;
- thorn scrub;
- salt crust;
- old tracks;
- dry wells;
- animal burrows;

Uncommon:

- glassy sand;
- a recently flooded channel;
- buried walls;
- red stone pillars;
- mineral springs;

Rare:

- one dune does not move with the wind;
- a dry well returns thrown stones at dawn;
- black flowers open only under moonlight.

## Natural Site role pools

These roles generate local structure. They are not all features.

### Forest Sites

Ordinary:

- forest edge;
- old path;
- deep wood;
- clearing;
- grove;
- stream crossing;
- rocky rise;
- fallen timber;

Inhabited or used:

- huntsman's camp;
- charcoal burner's camp;
- woodcutter's camp;
- bandit camp;
- warden lodge;
- healer's hut;
- forester's hut;

Dangerous:

- wolves' den;
- spider hollow;
- monster trail;
- blighted grove;
- burned clearing;
- flooded hollow;

Landmarks:

- forest altar;
- old boundary stone;
- charred oak;
- giant boulder;
- ruined tower;
- ancient bridge;

### Hill and mountain Sites

- pass road;
- ledge;
- scree slope;
- cave mouth;
- high pasture;
- spring;
- mine entrance;
- abandoned quarry;
- watchtower;
- mountain shrine;
- collapsed bridge;
- giant's trail;

### Prairie Sites

- herd trail;
- watering place;
- lone tree;
- ravine;
- hunter's camp;
- abandoned corral;
- burial mound;
- standing stones;
- burned camp;
- monster den.

### Wetland Sites

- raised path;
- reed island;
- ferry point;
- deep pool;
- willow grove;
- fisher's hut;
- ruined causeway;
- drowned shrine;
- monster nest;
- peat cutting.

### Coast and island Sites

- cove;
- beach;
- cliff path;
- sea cave;
- jetty;
- lighthouse or beacon;
- wreck;
- fisher's camp;
- ruined fort;
- reef passage.

### Desert Sites

- caravan track;
- well;
- oasis;
- rock shelter;
- canyon path;
- dry cistern;
- buried ruin;
- tomb entrance;
- watchtower;
- bandit camp.

## Path template

Required surface slot:

- earth — common, implicit display unless relevant;
- gravel — common;
- timber — uncommon, requires wetland, jungle, or maintained route;
- fitted stone — uncommon, requires old or wealthy construction;

Optional condition slot:

- muddy — requires earth or gravel and recent wet conditions;
- flooded — requires low ground or water;
- broken — requires constructed surface;
- overgrown — excludes heavily used;
- snow-covered — requires suitable environment or event;

Optional traffic or threat state:

- patrolled by soldiers;
- used by pilgrims;
- used by traders;
- watched by bandits;
- threatened by a monster family;
- abandoned;

Optional navigation slot:

- well-marked;
- confusing;
- treacherous;

Optional lighting:

- regular lanterns — uncommon, near settlement;
- magical lanterns — rare, requires wealthy, magical, or authored context;

`None` gives the normal path appropriate to its environment.

## Settlement tier draft

### Capital Area

Required:

- government seat;
- major market;
- tavern or inn service;
- smith service;
- general goods;
- alchemist;
- guards or army presence;

Likely Sites:

- palace, council hall, or clan hall;
- main market;
- major temple or cathedral;
- barracks;
- city gate;
- important bridge, harbor, or road station when geography requires;

Optional:

- wizard;
- guildhall;
- brewery;
- arena;
- university or archive;
- great park;
- foreign quarter;

### City Area

Required:

- tavern or inn service;
- smith service;
- general goods;
- market;
- local government;
- guards;

Optional:

- alchemist;
- cathedral or major temple;
- guildhall;
- brewery;
- docks;
- fortified gate;
- theater or arena;

### Town Area

Required:

- tavern or inn service;
- smith service;
- general goods;
- local authority;

Optional:

- alchemist, rare;
- marketplace;
- brewery;
- temple;
- mill;
- barracks;
- bridge;
- ferry;

### Village Area

Required:

- lodging or tavern service;
- basic smith service;
- general goods or peddler;

Optional:

- shrine or small temple;
- mill;
- brewer;
- healer;
- bridge;
- ferry;
- manor;

### Hamlet Site

Required:

- a few homes;
- one livelihood;

Optional:

- alehouse;
- shrine;
- smith;
- peddler;
- healer;

Hamlets do not automatically post boards or provide every settlement command.

## Settlement feature pools

### Geographic setting

One or two may apply:

- riverside;
- lakeside;
- seaside;
- hillside;
- valley floor;
- forest edge;
- crossroads;
- mountain pass;
- island;
- built around a spring;

Consequences:

- a riverside settlement generates a bridge, ferry, ford, or explicit reason
  no crossing exists;
- a seaside settlement may generate docks or a beach landing;
- a hillside settlement may generate steep streets or terraces;
- a crossroads settlement is more likely to have a market and lodging.

### Wealth slot

- poor — uncommon;
- ordinary — implicit;
- wealthy — uncommon;

Wealth adjusts materials and optional services but does not overwrite authored
culture.

### Street and built-form traits

Common:

- narrow streets;
- broad main road;
- crowded houses;
- scattered houses;
- many courtyards;
- fortified center;
- timber buildings;
- stone lower floors;

Uncommon:

- canals;
- roofed walkways;
- houses built into a cliff;
- many trees;
- public wells at every square;
- streets raised above floodwater;

Rare:

- bridges join the upper floors;
- every street descends toward one sealed gate;
- old walls divide the settlement into isolated quarters.

### Civic states

- oppressive leaders;
- disputed leadership;
- strict curfew;
- occupied by foreign troops;
- swollen by refugees;
- recovering from fire;
- recovering from flood;
- struck by disease;
- preparing for a fair;
- preparing for war;
- troubled by gangs;
- unusually peaceful;

These are mutable and should be rarer than ordinary stable settlement traits.

### Resource facts

Abundant:

- grain;
- livestock;
- timber;
- fish;
- salt;
- iron;
- copper;
- coal;
- stone;
- clay;
- wine;
- herbs;

Scarce uses the same keyed resources. A settlement cannot be both rich and
poor in the same resource. Resource facts should respect environment and
trade:

- fish requires coast, lake, or river;
- wine favors mediterranean or warm temperate country;
- timber requires forest access;
- ores favor mountains, hills, mines, or established trade;
- herbs may support an alchemist but do not guarantee one.

### Specialties and notables

Common or uncommon:

- famous smith;
- skilled brewer;
- large seasonal fair;
- horse market;
- boat builders;
- renowned healer;
- good hunting dogs;
- decorated pottery;
- strong local cheese;
- fine bows;
- reliable guides;

Rare:

- a smith who works meteoric iron;
- a market held only at night;
- a brewery using water from a sacred spring;
- a healer served by tame crows.

The notable should attach to a person, service, or Site rather than float as
an unsupported adjective.

## Constructed Site templates

Initial ordinary settlement pool:

- ordinary house;
- tavern or inn;
- smithy;
- general shop;
- marketplace;
- temple;
- cathedral;
- alchemist's shop;
- town hall or council hall;
- barracks or watch house;
- gate;
- bridge;
- docks;
- mill;
- brewery;
- warehouse;
- manor;
- guildhall;
- cemetery;

Initial rural and frontier pool:

- farm;
- shepherd's hut;
- hunter's cabin;
- mine;
- quarry;
- watchtower;
- tollhouse;
- roadside shrine;
- ruined fort;
- abandoned house;
- bandit camp;

Each template needs:

- required facets only where they add useful distinction;
- ordinary Room roles;
- optional Room roles;
- feature pools;
- environment and settlement-tier constraints.

## Cathedral Site draft

Required form:

- stout — common;
- tall — common;
- sprawling — uncommon;

Required material:

- wood — common in poor, forest, and frontier contexts;
- brick — common where clay and permanent settlement exist;
- stone — common;
- marble — uncommon, requires wealth, quarry, or trade;
- obsidian — rare, requires volcanic, infernal, magical, or authored context;

Optional decoration slot:

- austere;
- gilded;
- crowded with icons;
- painted in bright colors;
- covered in carved saints;
- marked with macabre carvings;

Optional construction state:

- unfinished;
- damaged by fire;
- damaged by war;
- partly abandoned;

Optional exceptional features:

- living trees grow through the nave;
- a spring rises beneath the altar;
- the bells are cast from captured weapons;
- every statue faces the cellar door;
- birds nest inside without being driven out;

Mutable or hidden states:

- heretics held in cages;
- forbidden rites in the crypt;
- refugees sleeping inside;
- soldiers using it as a storehouse;
- the clergy are divided;
- the crypt is sealed;

Constraints:

- `gilded` favors wealthy settlements;
- `living trees` requires an elven, woodland, nature-cult, or authored tag;
- `heretics held in cages` requires an oppressive or extreme authority and is
  hidden or local, not a decorative motif;
- obsidian is not an ordinary material roll.

### Cathedral Room roles

The Site itself represents the nave and public cathedral unless subdivision
matters.

Likely:

- clergy quarters;
- sacristy or storage;

Optional:

- cellar;
- crypt;
- archive;
- treasury;
- guardroom;
- bell tower;
- side chapel;
- kitchen;

Rare or state-driven:

- hidden chapel;
- prison room;
- sealed vault;
- magical workshop.

### Clergy quarters feature pools

Furnishing slot:

- ascetic;
- ordinary, implicit;
- comfortable;
- luxurious;

Documents and work:

- valuable books;
- maps;
- diary;
- administrative papers;
- letters from a noble;
- unfinished sermon;
- records of births and deaths;

Valuables:

- gold or treasure;
- rare weapon;
- silver ritual vessels;
- jeweled vestments;

Hidden or illicit:

- poison;
- signs of indulgence;
- magical experiments;
- forbidden book;
- blackmail letters;
- false accounts;

Constraints:

- do not generate every document as a separate narrated detail;
- one visible work item and at most one hidden item is normally enough;
- a rare weapon or major treasure should be rare and potentially mechanical
  when the object system exists;
- hidden and illicit entries default to `hidden`.

## Other first-pass Site anatomy

### Ordinary house — accepted basic template

An ordinary house is a lazily materialized Site attached to a generated
resident or household. It always has a `Main Room` and rolls zero to two of:

- Sleeping Alcove;
- Store Room;
- Work Room;
- Small Yard.

Accepted Site-name model:

- Borin's House.

`Main Room` heating, choose one:

- stone hearth;
- iron stove.

`Main Room` eating furniture, choose one:

- rough table and stools;
- narrow table and bench.

`Main Room` ordinary contents, choose one to three:

- shelf of crockery;
- water bucket;
- oil lamp;
- wool blankets;
- coat pegs;
- broom;
- kindling basket;
- covered food crock;
- small household shrine.

`Main Room` food, zero or one:

- black bread;
- onions;
- hard cheese;
- dried mushrooms;
- smoked fish;
- pot of stew.

`Main Room` personal object, zero or one:

- carved toy;
- sewing basket;
- smoking pipe;
- whetstone;
- family token;
- bundle of letters.

`Sleeping Alcove`:

- one narrow bed;
- two narrow beds;
- blanket chest;
- wash basin;
- stool;
- wall peg;
- candle;
- spare boots.

`Store Room`:

- shelves;
- sacks;
- barrels;
- rope;
- lamp oil;
- preserved food;
- spare tools;
- empty baskets.

`Work Room`:

- workbench;
- tool rack.

`Small Yard`:

- wood pile;
- water barrel;
- handcart;
- chopping block;
- goat pen;
- drying line;
- tool shed.

Dwarf livelihood overlays:

Bjorgheim:

- hand tools;
- leather apron;
- unfinished ironwork;
- account slate;
- stone dust.

Roros:

- pickaxe;
- rope;
- hooded lamp;
- ore basket;
- fur boots;
- goat tack.

Svalaver:

- fishing net;
- iron hooks;
- cork floats;
- ice chisel;
- fish basket;
- cargo tally.

Generation:

- generate one resident or household role from the settlement culture;
- always generate the `Main Room`;
- roll zero to two optional Rooms;
- give each Room its required anchors;
- add one to three ordinary visible contents;
- add zero or one livelihood object;
- add zero or one personal object;
- add at most one searched or hidden object for the whole house;
- save the resident, Rooms, and contents permanently.

### Accepted shared basic Room-content pools

These ordinary pools are accepted in the dwarf base pass and may be reused by
later cultures where their wording and material fit.

`Great Hall`:

- long table;
- high seat;
- iron braziers;
- clan banners;
- public notice board;
- petition bench;
- feast vessels.

`Council Room` or `Contract Room`:

- table;
- chairs;
- stools;
- wall map;
- account slate;
- contract box;
- seal press;
- locked chest.

`Records Room`:

- shelves;
- document boxes;
- ledgers;
- road maps;
- tax rolls;
- spare ink;
- seal box.

`Market Row` or `Yard`:

- stalls;
- trading tables;
- handcarts;
- baskets;
- awnings;
- scales;
- empty crates;
- public notices.

`Tavern Common Room`:

- hearth;
- tables and benches;
- serving counter;
- ale barrels;
- game board;
- notice board;
- coat pegs;
- stew pot.

`Kitchen`:

- cooking fire;
- stove;
- worktable;
- iron pots;
- knives;
- crockery;
- bread shelf;
- water barrel.

`Cellar` or `Food Store`:

- shelves;
- racks;
- ale barrels;
- salt sacks;
- root baskets;
- smoked meat;
- lamp.

`Guest Room`:

- bed;
- bunks;
- wash basin;
- stool;
- peg rail;
- blanket chest;
- candle;
- shuttered window.

`Forge`:

- forge;
- anvil;
- quench tub;
- tool rack;
- coal bin;
- unfinished tools;
- scrap basket;
- bellows.

`Smithy Store Room`:

- shelves;
- locked tool chest;
- iron bars;
- horseshoes;
- axe heads;
- nails;
- charcoal sacks.

`General Shop Sales Room`:

- counter;
- goods shelves;
- baskets;
- rope;
- lamps;
- crockery;
- blankets;
- tools;
- food jars.

`General Store Room`:

- crates;
- barrels;
- flour sacks;
- lamp oil;
- spare rope;
- folded cloth;
- empty bottles.

`Alchemist's Shop`:

- counter;
- bottle shelves;
- mortar;
- scales;
- dried herbs;
- labeled jars;
- locked cabinet.

`Alchemist's Work Room`:

- workbench;
- small furnace;
- glass tubes;
- herb rack;
- water basin;
- charcoal box;
- notes.

`Guard Room`:

- bench;
- weapon rack;
- duty board;
- bell rope;
- lanterns;
- shield rack;
- key board.

`Jetty` or `Landing`:

- stone quay;
- timber platform;
- mooring posts;
- rope coils;
- cargo hook;
- handcart;
- fish baskets;
- small crane.

`Smokehouse`:

- smoking racks;
- fire trench;
- fish hooks;
- salt barrel;
- cutting table;
- knives;
- wood pile.

### Tavern or inn

Required:

- common room;
- lodging service;

Optional Rooms:

- private room;
- kitchen;
- cellar;
- stable;
- owner's room;

Optional features:

- crowded;
- quiet;
- cheap;
- expensive;
- many travelers;
- soldiers drink here;
- gamblers meet here;
- famous stew;
- poor ale;
- large fireplace;
- tree grows through the common room;

### Smithy

Required:

- forge;
- smith service level: basic, skilled, master;

Optional Rooms:

- yard;
- store room;
- living room;
- locked workshop;

Optional features:

- works mainly in tools;
- works mainly in weapons;
- repairs armor;
- uses water power;
- crowded with apprentices;
- short of fuel;
- famous smith;
- unusual material under lock.

### General shop

Required:

- ordinary goods;

Optional features:

- cramped;
- orderly;
- badly stocked;
- buys curiosities;
- also serves as post office;
- guarded store room;
- family lives above;
- one unusual item, rare.

### Marketplace

The market is a Site when it is important enough to visit independently.

Optional Rooms or local nodes:

- food stalls;
- livestock yard;
- cloth row;
- smiths' row;
- foreign merchants;
- auction platform;
- guard post;

Optional states:

- fair day;
- closed;
- under guard;
- flooded;
- controlled by a guild;
- troubled by thieves.

### Bandit camp

Likely Rooms:

- outer watch;
- campfire;
- prisoners or stores;
- leader's tent;

Optional features:

- hidden among rocks;
- concealed by trees;
- abandoned wagons;
- stolen livestock;
- signal fire;
- muddy ground;
- disciplined sentries;
- quarrelling factions.

### Monster den

Likely Rooms:

- approach or tracks;
- den;

Optional:

- feeding ground;
- egg chamber;
- hidden exit;
- remains of prey;
- stolen object;
- trapped entrance.

## General Room content categories

Room facts should normally come from no more than one entry in each useful
category:

- spatial form: narrow, open, divided, raised, sunken;
- surface or material;
- furnishing;
- current use;
- occupant or threat;
- useful object or resource;
- evidence or document;
- exit, obstacle, or affordance;
- hidden content.

These categories are prompts, not a requirement to fill every Room. A bridge
Room may need only the bridge, the stream, and who controls the crossing.

## Curiosity draft

These entries are deliberately concrete and context-bound.

Natural:

- An oak has grown around a bronze bell.
- A dry well rings when a stone is dropped into it.
- Every bird nest in the grove contains blue thread.
- A boundary stone is warm even under snow.
- Fish gather beneath a bridge where no one feeds them.
- One tree has iron nails driven into every branch.
- A spring leaves red mineral lines on everything it touches.
- A line of footprints crosses bare rock and stops at the cliff.

Constructed:

- Every statue faces the cellar door.
- A clock strikes thirteen at noon.
- One chimney smokes although its hearth is cold.
- A sealed window has fresh flowers on its sill.
- The floor has been repaired around a perfect circle.
- The gate key is too large for any visible lock.
- All the chairs have one leg shortened.
- A bell rope descends into a locked room.

Settlement:

- The public well is covered by an iron cage at night.
- Every shop uses the same painted sign.
- The bridge bears the names of people who drowned there.
- No door on one street opens toward the road.
- A market stall sells only keys.
- A tree in the main square holds hundreds of written promises.

Reject or constrain any curiosity which suggests a larger mystery the game
cannot support. A detail may remain unexplained, but it should still be
inspectable, usable, or tied to a clear local fact.

## Name generation

Names are generated independently of hidden features. A hidden blight should
not accidentally name its Area `Blighted Wood` before discovery.

Generation rules:

- names are unique within the world;
- prefer one strong modifier and one familiar place noun;
- no `Forest Forest`, `Hill Ridge Hills`, or repeated parent noun;
- numbered depths and generic `site 2` are development fallbacks only;
- cultural settlement pools remain separate from environmental Area pools;
- a public defining feature may influence the name;
- hidden or mutable states normally do not.

### Natural Area patterns

```text
The + Modifier + Place Noun
Modifier + Place Noun
Creature or Plant + Place Noun
Person's Name + Place Noun
Place Noun + geographic qualifier
```

Use `The White Forest` in prose but store the canonical name consistently;
the display layer should not double the article.

### Forest modifiers

- White;
- Black;
- Red;
- Silver;
- Ash;
- Birch;
- Crow;
- Thorn;
- Mist;
- Elder;
- Green;
- High;
- Far;
- Old;

Forest nouns:

- Forest;
- Wood;
- Grove, for a smaller Area or major Site;
- Hollow, when the Area is valley-shaped;
- Reach;

### Hill and mountain modifiers

- High;
- Broken;
- Red;
- Black;
- Wind;
- Stone;
- Ash;
- Goat;
- Eagle;
- Crown;
- Long;
- Frost;

Nouns:

- Hills;
- Ridge;
- Heights;
- Peaks;
- Pass;
- Uplands;

### Wetland modifiers

- Black;
- Reed;
- Willow;
- Mist;
- Crow;
- Salt;
- Long;
- Drowned;
- Green;
- Cold;

Nouns:

- Fen;
- Marsh;
- Wetlands;
- Mere;
- Pools;
- Reedlands;

### Prairie modifiers

- Long;
- Red;
- Golden;
- Wind;
- Horse;
- Bison;
- Broken;
- High;
- Open;
- Sun;

Nouns:

- Prairie;
- Plains;
- Grasslands;
- Range;
- Downs;

### Coast and archipelago modifiers

- Storm;
- Black;
- White;
- Gull;
- Seal;
- Crown;
- Broken;
- Outer;
- Green;
- Red;

Nouns:

- Isles;
- Islands;
- Coast;
- Sound;
- Reaches;
- Cliffs;

### Desert modifiers

- Red;
- White;
- Black;
- Glass;
- Salt;
- Long;
- Burning;
- Silent;
- Scorpion;
- Moon;

Nouns:

- Desert;
- Wastes;
- Dunes;
- Flats;
- Barrens;
- Basin;

### Settlement name direction

Retain culture-specific construction, but broaden it beyond a race-to-Land
mapping. A culture profile supplies fragments and whole-name patterns.

Human temperate:

- Alder, Oak, Stone, Fair, King's, Marsh, Green, High;
- ford, bridge, field, haven, market, mere, wall, gate.

Human mediterranean:

- Bell, Rose, Sun, Gold, White, High, Saint, Olive;
- coast, hill, port, vale, bridge, market, spring, tower.

Elf:

- Silver, Moon, Green, Dawn, Star, Willow, Mist, Bright;
- glade, hollow, reach, veil, song, grove, spire, bough.

Dwarf:

- use an invented Germanic/Norse-sounding creole, drawing loosely from
  Icelandic, Swedish, Norwegian, and related languages without claiming
  linguistic accuracy;
- use ASCII transliteration only;
- model names: Drunurnar, Krokskogur, Hornindal, Bjorgheim, Roros, Svalaver;
- a plain English type noun may remain for immediate readability:
  `Drunurnar Mountains`, `Krokskogur Forest`, `Lake Hornindal`;
- DM-created dwarf place names follow the same sound and hybrid construction.

Goblin:

- Gear, Sprocket, Grease, Boiler, Scrap, Smog, Brass, Rivet;
- town, works, burrow, pit, sprawl, market, stack, yard.

Orc:

- Iron, Red, Ash, Bone, Storm, Black, Horse, Flint;
- hold, camp, ridge, spear, fang, range, ford, crown.

Pirate:

- Black, Free, Storm, Knife, Gull, Rum, Red, Broken;
- harbor, key, cove, haven, hook, reef, port, rest.

Caelum should remain authored. The name strongly supports the city of angels
and devils; ordinary name generation should not produce near-copies.

## Worked forest chain

```text
THE WHITE FOREST — Area
  kind: natural
  subtype: forest
  environment: temperate forest
  public signature: pale-barked trees

  HUNTER'S EDGE — Site
    reveal: local
    HUNTSMAN'S CABIN — Room

  OLD FOREST ROAD — Site
    reveal: public
    surface: earth
    SMALL BRIDGE — Room

  DEEP WOOD — Site
    reveal: explore
    CHARRED OAK — Room
    WOLVES' DEN — Room

  BANDIT CAMP — Site
    reveal: quest or explore
    CAMPFIRE — Room
    LEADER'S TENT — Room

  FOREST ALTAR — Site
    reveal: local
    no Room required

  eastern link:
    ELVEN BORDER — Area
    HEALER'S HUT may be a Site beside the crossing
```

Possible generated Area states:

- none: the ordinary White Forest;
- diseased;
- scorched;
- frequented by dire wolves.

Possible generated additive features:

- flowering undergrowth;
- giant boulders;
- fruit-bearing trees;
- persistent fog.

`Scorched + flowering + fruit-bearing` is rejected. `Foggy + mossy + giant
boulders` is valid but uncommon because it requires three optional features.

## Worked cathedral chain

```text
CATHEDRAL OF THE DAWN — Site
  form: tall
  material: brick
  decoration: gilded
  state: unfinished
  public fact: the west tower has no roof

  CLERGY QUARTERS — Room
    furnishing: ascetic
    visible: administrative papers
    hidden: blackmail letters

  STORAGE — Room
    visible: lamp oil and folded cloth

  CRYPT — Room
    reveal: hidden
    state: sealed

  BELL TOWER — Room
    obstacle: unfinished stair
```

This Site has several structural facts, but its ordinary description leads
with the unfinished west tower. The DM does not recite every feature at the
door.

## Review-to-implementation workflow

Procedural place generation remains the active development track until it is
implemented and verified. Content work uses this repeatable loop:

1. This file holds the schema, distributions, counts, links, constraints,
   generation rules, rationale, and completion requirements.
2. **Phase 1 — basic content:** `placegen_review.txt` presents one Land's
   essential player/DM-facing strings, grouped under minimal labels for its
   environment, Areas, Sites, Rooms, and ordinary contents.
3. Review the sheet like a translation: keep, cut, rename, or supply
   alternative wording without working through the surrounding design again.
4. Transfer the accepted basic strings into this canonical catalog. Move
   reusable Room/content pools into shared templates; keep culture- and
   geography-specific strings under their concrete Land.
5. Replace the worksheet with the next Land's basic sheet in a new review
   session. Repeat until every planned Land, culture, and environment has
   completed Phase 1.
6. **Phase 2 — special content:** only after every basic Land pass is complete,
   review the optional Area traits, mutable states, rare curiosities,
   exceptional settlement features, and hidden or unusual Room contents.
   These may be grouped by environment or shared template instead of repeated
   Land by Land.
7. Transfer the accepted special strings into this canonical catalog.
8. Implement the accepted schemas and catalogs in code. A vertical slice may
   ship internally before every pool is coded, but no accepted MVP content may
   remain documentation-only when the feature is declared complete.

Review and implementation therefore form one track, not two unrelated
projects. The worksheets settle the concrete content; this file consolidates
it; the code generates and persists it.

The worksheet deliberately contains no introduction, schema explanation,
rationale, coverage requirements, completion checklist, or open-question
essay. Keep only enough non-output labeling for the reviewer to know what each
string names. All general information belongs here.

## Current review handoff

Status on 2026-07-24:

- Phase 1 is active.
- Alpine Tundra and the icy dwarf Land basic pass are complete.
- The accepted dwarf content has been consolidated into the Alpine Tundra
  profile, the concrete dwarf Land catalog, the ordinary-house template, and
  the shared basic Room-content pools in this file.
- `placegen_review.txt` remains the completed dwarf string sheet as the review
  record.
- No special/nonessential feature pool has been accepted yet. Existing
  optional-feature and curiosity lists in this draft remain Phase-2
  candidates.

Next session:

1. Replace `placegen_review.txt` with the **temperate human country basic
   strings**.
2. Use the same minimal translation-sheet format.
3. Review only essential environment, Area, settlement, Site, Room, and
   ordinary-content strings.
4. Consolidate accepted strings here before starting the following Land.

Do not begin the special-feature review until every planned basic Land/climate
sheet has been completed and consolidated.

The feature is done when:

- the reviewed Land/culture/environment distribution is represented in
  worldgen;
- the generator creates each Land's finite Area and initial settlement
  inventory;
- lazy Sites, Rooms, residents, place facts, and Room contents use stable
  child seeds and survive save/load without rerolling;
- ordinary settlement interiors, including generated houses, are navigable
  and display their persistent contents;
- quest placement selects suitable persistent geography and quest or world
  changes mutate that geography without replacing its identity;
- macro and local readouts expose known places, exits, contents, and relevant
  state;
- deterministic generation, constraints, persistence, and a fresh-world
  vertical play path have automated or reproducible verification.

After those conditions hold, move the shipped mechanics and behavior to
`rules.md`, update the development map and file index, and remove the feature
from `plan.md`.

## Initial implementation order

1. Split Land identity from race/culture and add environment profiles.
2. Replace unlimited natural-Area creation with finite authored Area roles.
3. Add place facets, features, states, reveal state, source, generation seed,
   and lightweight Room contents to the persistent schema.
4. Build the generic weighted selector with slots, requirements, exclusions,
   scope limits, and the 50/30/15/5 feature-count distribution.
5. Add natural Area and forest/path Site content first.
6. Make quest placement select suitable Areas and persistent Sites.
7. Add settlement tiers, services, and settlement Site templates.
8. Add the ordinary-house template and its Room-content pools.
9. Add cathedral and other specialized Room-content templates.
10. Add DM readouts and the local minimap surface.
11. Add mutation hooks for quests and later off-screen events.

The first vertical slice should be one temperate human Land containing:

- one capital;
- one town;
- one village or hamlet;
- farmland;
- pasture or hills;
- the White Forest;
- generated ordinary Sites in the forest;
- one generated ordinary house with persistent Rooms and visible contents;
- one quest which discovers and changes a forest state.

This is enough to test inheritance, names, feature weighting, reveal levels,
quest placement, mutation, persistence, and DM output before filling every
biome.

## Content review questions

Before implementation, review the draft for:

- environment entries which are redundant or use the wrong scale;
- feature entries which are merely atmosphere and give the DM no usable fact;
- curiosities which imply unsupported mysteries;
- conditions which should be states rather than permanent features;
- pairs better represented as one exclusive slot;
- constraints missing from rare materials or magical entries;
- settlement services which should not be universal;
- natural Site roles which should be Rooms, and the reverse;
- terms which are too historical, ornamental, or obscure for `writing.md`;
- pools too small to resist repetition.
