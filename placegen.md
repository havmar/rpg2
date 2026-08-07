# RPG2 — Place Generation MVP Specification

Status: **MVP implemented 2026-07-25**. This document preserves the complete
content catalog and implementation contract behind the shipped pass.
`places.py` and `place_catalog.json` are the runtime catalog/materializer;
`rules.md` describes player-facing behavior. The optional special-feature,
pirate, wilderness, and Caelum material below remains post-MVP.

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

## MVP boundary and completion contract

The first implementation covers the six settled core Lands:

- Dvarvengrond;
- Firascir;
- Mortellaria;
- Ensimaa;
- Gibili;
- Tergal.

For those Lands the MVP includes:

- independent Land, culture, owner, and environment records;
- the finite natural and settlement Area inventories specified below;
- every authored settlement's required Site and Room skeleton;
- the generated village roles and name pools per non-dwarf Land (one village
  a land is built at world creation since the 2026-08-07 trim; the rest are
  the land's reserve);
- lazy ordinary natural Sites, ordinary houses, and their persistent Rooms and
  visible contents;
- coarse environment and purpose tags for quest placement;
- stable seeds, reveal state, navigation, save/load persistence, and simple
  place-state mutation;
- player-facing `look` output and a fuller DM-facing fact readout.

The following are post-MVP content, even though this document keeps their
direction:

- the northern and tropical pirate islands;
- the wild forest, jungle, desert, and Caelum;
- rare curiosities, magical materials, and other Phase-2 special features;
- daily weather and off-screen place simulation;
- unlimited cultural proper-name generation beyond the fixed pools.

The optional-feature machinery may be implemented in the MVP, but missing
special pools do not block the first release. Ordinary identity, structure,
contents, persistence, and quest reuse are the acceptance path.

### Required world-generation counts

> **Superseded for settlements by the settlement trim (2026-08-07).** The
> settlement columns below are the CATALOG, not the world's census: a land
> now BEGINS with three settlements — one capital, one town, one village —
> and everything else here waits in the land's reserve pool until something
> needs it to exist. rules.md's *The map* owns the shipped rule. The natural
> Area counts are unchanged, and every authored settlement listed in this
> document is still authored: what moved is WHEN it is built.

| Land | Natural Areas | Authored settlements | Generated villages |
|---|---:|---:|---:|
| Dvarvengrond | 3 | 3 | 0 |
| Firascir | 4 | 5 | 3 |
| Mortellaria | 5 | 4 | 3 |
| Ensimaa | 5 | 4 | 3 |
| Gibili | 5 | 4 | 3 |
| Tergal | 6 | 4 | 3 |

Initial identity fields:

| Land | Owner ID | Culture profile | People race | Environment |
|---|---|---|---|---|
| Dvarvengrond | dvarvengrond | dwarf | dwarf | alpine_tundra |
| Firascir | firascir | firascir_human | human | temperate |
| Mortellaria | mortellaria | mortellarian_human | human | mediterranean |
| Ensimaa | ensimaa | elf | elf | temperate_forest |
| Gibili | gibili | goblin | goblin | mediterranean |
| Tergal | tergal | orc | orc | prairie |

The initial owner ID deliberately equals the Land polity ID. Ownership remains
a separate field so conquest can change it without changing geography.
`People race` is the adapter into the current NPC, quest, and encounter
tables; culture selects place names and material content.

All finite NATURAL Area records are created at world generation; settlements
are created three to a land and drawn from the reserve thereafter (the trim).
Settlement Areas begin known. Natural Areas begin unknown unless the opening
position, a public route, or a quest reveals them. Discovery changes `known`;
it does not create the Area or reroll any of its facts.

Required settlement Sites and their Room skeletons materialize with the
settlement. Ordinary optional Sites and Room contents materialize on first
request or entry. A natural Area owns the three ordinary Site templates listed
in its concrete catalog. Area exploration draws each once in a stable shuffled
order before any template repeats. Quest-specific Sites may be added at any
time when their tags fit the Area.

Mortellaria, Ensimaa, Gibili, and Tergal draw generated village names without
replacement from their fixed pools and pair each with one of the three roles
defined in their Land catalog, in rotation; Firascir's villages are the fixed
Sturford, Ackham, and Flurham records. Since the trim (2026-08-07) that
pairing produces the land's village RESERVE — one is built at world creation
and the rest wait to be needed. Names do not decide geography; the role
supplies the description, Sites, and livelihood overlay.

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
| Dvarvengrond | Dwarf | Alpine tundra |
| Firascir | Human, temperate | Temperate |
| Mortellaria | Human, mediterranean | Mediterranean |
| Ensimaa | Elf | Temperate forest |
| Wild forest | None fixed | Temperate forest |
| Gibili | Goblin | Mediterranean |
| Tergal | Orc | Prairie |
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

- Whitweld Forest's pale trees: public;
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
Whitweld Forest
  identity: temperate
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

Five to ten settlements per country is the ordinary range, but they need not
all be equal macro destinations. Capitals, cities, towns, and independent
villages are Areas. Minor hamlets which do not need their own travel hub,
shops, and board are Sites in rural Areas.

MVP settlement inventory for an ordinary culturally settled Land — the
CATALOG, which the 2026-08-07 trim turned from a census into a reserve:

- one authored capital Area;
- two or three authored town Areas;
- procedurally generated village Areas (the role/name pairing).

A land is BUILT three settlements deep at world creation — the capital, one
town, one village — and grows by one whenever something needs a place to
exist. The dwarf Land is deliberately smaller: one capital and two towns,
with no village in the catalog at all, so it opens with all three of them and
holds nothing in reserve. Wilderness Lands and unique Caelum do not inherit
this count automatically.

Firascir's catalog is deliberately denser than the ordinary range: one
capital, two harbor towns, two inland towns, and three fixed villages. Five
further village names are reserved for post-MVP expansion. These are all
finite Land slots with stable seeds, not unlimited `explore` results — the
reserve is exhaustible on purpose.

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

# MVP CONTENT CATALOG AND LATER DRAFTS

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

The Alpine Tundra base content is concrete in the accepted Dvarvengrond
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

The Temperate base content is concrete in the accepted Firascir catalog
below. The Land owns its finite named Areas and their accepted Site pools.

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

## First concrete Land structure: Dvarvengrond

This is the non-wording structure behind the completed dwarf string pass.

- Culture: dwarf.
- Default environment: alpine tundra.
- Natural Areas: Drunurnar Mountains, Krokskogur Forest, and Lake Hornindal.
- Settlement Areas: Bjorgheim, the central capital; Roros, the remote northern
  town; and Svalaver, the southern fishing and trade town.
- No village in the catalog at all: the dwarf Land opens with all three of
  its settlements and holds nothing in reserve.
- The southern town connects directly to Firascir and is the
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
                            Firascir
```

The lake and southern town are sibling Areas. The lake owns the open water and
unsettled shore; the town owns the built southern shore. The northern town and
mountains follow the same rule: wilderness stays in the natural Area, while
walls, streets, services, and houses belong to the settlement Area.

Natural Sites, starting settlement Sites, their Room roles, and ordinary
content pools were reviewed in the first worksheet pass. Its accepted names
and wording are preserved in the concrete content catalog below.

### Accepted Land and Area strings

**Dvarvengrond** — Land.

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

This completes Dvarvengrond's **basic string pass**. It does not accept or
reject the special, nonessential feature pools below. Those pools remain draft
material until the later global special-feature review phase.

## Second concrete Land structure: Firascir

This is the accepted base structure behind the temperate human string
worksheet.

- Culture: human, temperate.
- Default environment: temperate.
- Natural Areas: Whitweld Forest, Grendon Fields, Stura River, and Flumenpur
  River.
- Settlement Areas in the catalog: Tomburgh, the capital; Leehaven and
  Walhaven, the two western harbor towns; Bradwhitchip and Redflurton, the
  two inland towns; and the villages of Sturford, Ackham, and Flurham.
  Tomburgh plus one town and one village are built at world creation; the
  other five wait in the land's reserve (the 2026-08-07 trim).
- Five further village names remain reserved for post-MVP expansion.
- Stura River rises in the northern mountains, runs south through
  Mortellaria, and reaches the sea.
- Flumenpur River rises in the northern mountains, crosses Tomburgh, runs
  east-southeast through Caelum, and continues toward Tergal.
- Leehaven and Walhaven stand on Firascir's western sea coast.

Working arrangement:

```text
                   Dvarvengrond / northern mountains
                         /                 \
                    Stura River       Flumenpur River
                         |                  |
                    Grendon Fields      Tomburgh ---- Caelum ---- Tergal
                    /      |      \         |
             Leehaven  Bradwhitchip  Whitweld Forest
                    \      |      /         |
                     Walhaven          Redflurton
                         |
                     Mortellaria
```

The diagram records the main routes, not exact cartographic positions.
Sturford belongs beside Stura River, Ackham at Whitweld Forest's western
edge, and Flurham beside a pond fed by Flumenpur River.

Natural Sites, starting settlement Sites, their Room roles, and ordinary
content pools are reviewed as strings in `placegen_review.txt`. Accepted
names and wording are consolidated below.

### Accepted Land and Area strings

**Firascir** — Land.

> A broad human kingdom lies between the northern mountains and the western
> sea. Two great rivers cross its fields.

**Whitweld Forest** — natural Area, forest.

> Pale beech trunks fill the old wood east of the fields.

**Grendon Fields** — natural Area, farmland and pasture.

> Farms, hedged roads, and sheep pastures cover the rising ground below the
> northern mountains.

**Stura River** — natural Area, southbound river.

> A great river runs from the northern mountains through Grendon Fields. It
> continues south through Mortellaria and reaches the sea.

**Flumenpur River** — natural Area, eastbound river.

> A great river runs from the northern mountains through Tomburgh. It
> continues east-southeast through Caelum toward Tergal.

**Tomburgh** — settlement Area, capital.

> The walled capital stands on both banks of the Flumenpur River. The great
> east road crosses the river here.

**Leehaven** — settlement Area, northern harbor city.

> A harbor city stands around a sheltered bay on the northwestern coast.
> Fishing boats crowd its inner quay.

**Walhaven** — settlement Area, southern harbor city.

> A walled harbor city guards the southwestern coast road. Human and foreign
> merchants unload beside its stone docks.

**Bradwhitchip** — settlement Area, western inland town.

> A market town stands among the farms of Grendon Fields. Grain carts fill its
> square after harvest.

**Redflurton** — settlement Area, eastern inland town.

> A riverside town stands where the old road meets the lower Flumenpur River.
> Reed beds line the water below its bridge.

**Sturford** — generated settlement Area, starting village.

> A farming village stands beside a shallow crossing of the Stura River.

**Ackham** — generated settlement Area, starting village.

> A village of small farms stands at the western edge of Whitweld Forest.

**Flurham** — generated settlement Area, starting village.

> A fishing village stands beside a broad pond fed by the Flumenpur River.

Post-MVP village name pool; use at most five:

- Sturham;
- Sturworth;
- Newton;
- Midton;
- Aston;
- Tomton;
- Walham;
- Coldcot;
- Thornley;
- Blackton;
- Astmoor;
- Ackbridge;
- Ackton;
- Mickleham;
- Shepham.

### Accepted natural Site, Room, and content strings

**Whitweld Forest**

```text
OLD FOREST ROAD — Site
  BEECH GATE — Room
    pale beech trunks
    road marker
    wagon ruts
  STREAM BRIDGE — Room
    plank bridge
    clear stream
    mossy stones

WOODCUTTER'S CAMP — Site
  FIREPIT — Room
    stone fire ring
    log benches
    black cooking pot
  TIMBER YARD — Room
    cut logs
    splitting block
    drag sled
  STORE HUT — Room
    axes
    rope coils
    iron wedges

RUINED WATCHTOWER — Site
  TOWER FOOT — Room
    broken doorway
    fallen stones
    old firepit
  UPPER PLATFORM — Room
    cracked stair
    low parapet
    view over the treetops
```

**Grendon Fields**

```text
HEDGED ROAD — Site
  CART TRACK — Room
    packed earth
    wheel ruts
    milestone
  STONE CROSSING — Room
    narrow stream
    flat stepping stones
    gap in the hedge

SHEPHERD'S HUT — Site
  MAIN ROOM — Room
    stone hearth
    rough table
    wool blankets
  SHEEPFOLD — Room
    low stone wall
    wooden gate
    water trough

OLD WINDMILL — Site
  MILL FLOOR — Room
    millstones
    flour bins
    wooden gears
  GRAIN STORE — Room
    grain sacks
    hand scales
    mouse traps
  UPPER LOFT — Room
    wind shaft
    spare sailcloth
    ladder
```

**Stura River**

```text
SOUTH ROAD BRIDGE — Site
  NORTH BANK — Room
    gravel bank
    road marker
    willow tree
  BRIDGE DECK — Room
    timber rails
    stone piers
    cart ruts
  SOUTH BANK — Room
    muddy landing
    mooring post
    path downstream

RIVERSIDE MILL — Site
  MILL YARD — Room
    mill stream
    stacked grain sacks
    handcart
  MILL ROOM — Room
    waterwheel shaft
    millstones
    flour bins
  STORE ROOM — Room
    grain sacks
    spare belts
    oil jar

FERRY POINT — Site
  LANDING — Room
    timber platform
    mooring posts
    ferry rope
  FERRY HOUSE — Room
    small hearth
    table and stools
    toll box
```

**Flumenpur River**

```text
WEST BANK ROAD — Site
  TOWPATH — Room
    packed earth
    mooring rings
    cart tracks
  WILLOW BEND — Room
    willow trees
    gravel bank
    fishing stakes

EAST FERRY — Site
  WEST LANDING — Room
    timber steps
    bell post
    rope coil
  FERRYBOAT — Room
    flat deck
    guide rope
    boat hook
  EAST LANDING — Room
    stone ramp
    road marker
    waiting bench

RIVER ISLAND — Site
  SHINGLE BANK — Room
    smooth stones
    driftwood
    tied skiff
  FISHER'S CAMP — Room
    canvas shelter
    fish basket
    cold firepit
```

### Accepted settlement Site and Room strings

Required Sites materialize with their settlement. Further ordinary Sites
materialize lazily when requested or explored and then persist.

**Tomburgh**

```text
ROYAL HALL
  THRONE HALL
  COUNCIL ROOM
  RECORDS ROOM
MAIN MARKET
  FOOD ROW
  CLOTH ROW
  FOREIGN YARD
FLUMENPUR BRIDGE
  WEST GATEHOUSE
  BRIDGE DECK
  EAST GATEHOUSE
CROWN AND BELL INN
  COMMON ROOM
  KITCHEN
  CELLAR
  GUEST ROOM
  STABLE
TOMBURGH SMITHY
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
EAST GATE
  GATE PASSAGE
  GUARD ROOM
  WALL WALK
```

Further ordinary Sites:

- ordinary house;
- cathedral;
- barracks;
- guildhall;
- warehouse;
- brewery.

**Leehaven**

```text
HARBOR HALL
  PUBLIC COUNTER
  COUNCIL ROOM
  RECORDS ROOM
INNER QUAY
  FISH LANDING
  NET YARD
  HARBOR STEPS
FISH MARKET
  FISH STALLS
  SALT ROW
  BASKET YARD
GULL AND NET INN
  COMMON ROOM
  KITCHEN
  CELLAR
  GUEST ROOM
LEEHAVEN SMITHY
  FORGE
  YARD
  STORE ROOM
GENERAL SHOP
  SALES ROOM
  STORE ROOM
NORTH WATCH
  GUARD ROOM
  SIGNAL PLATFORM
  HARBOR WALL
```

Further ordinary Sites:

- ordinary house;
- warehouse;
- boat shed;
- shipwright;
- small temple;
- brewery;
- smokehouse.

**Walhaven**

```text
CITY HALL
  PUBLIC HALL
  COUNCIL ROOM
  RECORDS ROOM
STONE DOCKS
  MAIN QUAY
  CARGO YARD
  HARBOR STAIRS
HARBOR MARKET
  FOOD ROW
  CLOTH ROW
  FOREIGN YARD
ANCHOR INN
  COMMON ROOM
  KITCHEN
  CELLAR
  GUEST ROOM
  STABLE
WALHAVEN SMITHY
  FORGE
  YARD
  STORE ROOM
GENERAL SHOP
  SALES ROOM
  STORE ROOM
SEA GATE
  GATE PASSAGE
  GUARD ROOM
  WALL WALK
```

Further ordinary Sites:

- ordinary house;
- merchant warehouse;
- customs house;
- shipwright;
- temple;
- brewery.

**Bradwhitchip**

```text
TOWN HALL
  PUBLIC HALL
  COUNCIL ROOM
  RECORDS ROOM
MARKET SQUARE
  GRAIN ROW
  LIVESTOCK YARD
  CART STAND
HARVEST INN
  COMMON ROOM
  KITCHEN
  CELLAR
  GUEST ROOM
  STABLE
BRADWHITCHIP SMITHY
  FORGE
  YARD
  STORE ROOM
GENERAL SHOP
  SALES ROOM
  STORE ROOM
GRAIN HOUSE
  WEIGHING ROOM
  GRAIN STORE
  LOADING YARD
```

Further ordinary Sites:

- ordinary house;
- barn;
- windmill;
- small temple;
- brewery;
- manor.

**Redflurton**

```text
TOWN HALL
  PUBLIC HALL
  COUNCIL ROOM
  RECORDS ROOM
MERE BRIDGE
  WEST GATE
  BRIDGE DECK
  EAST GATE
REED AND PIKE INN
  COMMON ROOM
  KITCHEN
  CELLAR
  GUEST ROOM
REDFLURTON SMITHY
  FORGE
  YARD
  STORE ROOM
GENERAL SHOP
  SALES ROOM
  STORE ROOM
RIVERSIDE MARKET
  FISH STALLS
  REED ROW
  BOAT LANDING
```

Further ordinary Sites:

- ordinary house;
- ferry house;
- reed warehouse;
- watermill;
- small shrine;
- brewery.

**Sturford**

```text
FORD HOUSE
  TOLL ROOM
  STORE ROOM
SHALLOW FORD
  WEST BANK
  RIVER CROSSING
  EAST BANK
PLOUGH INN
  COMMON ROOM
  KITCHEN
  GUEST ROOM
  STABLE
VILLAGE SMITHY
  FORGE
  YARD
GENERAL STORE
  SALES ROOM
  STORE ROOM
```

Further ordinary Sites:

- ordinary house;
- farm;
- barn;
- roadside shrine;
- mill.

**Ackham**

```text
VILLAGE GREEN
  OLD OAK
  WELL
  NOTICE POST
OAK AND AXE INN
  COMMON ROOM
  KITCHEN
  GUEST ROOM
VILLAGE SMITHY
  FORGE
  YARD
GENERAL STORE
  SALES ROOM
  STORE ROOM
WOOD YARD
  TIMBER YARD
  TOOL SHED
```

Further ordinary Sites:

- ordinary house;
- farm;
- woodcutter's hut;
- charcoal camp;
- small shrine.

**Flurham**

```text
MERE LANDING
  TIMBER JETTY
  BOAT YARD
HERON INN
  COMMON ROOM
  KITCHEN
  GUEST ROOM
SMITH'S SHED
  FORGE
  YARD
GENERAL STORE
  SALES ROOM
  STORE ROOM
FISH SHED
  CUTTING ROOM
  SALT STORE
```

Further ordinary Sites:

- ordinary house;
- fisher's hut;
- boat shed;
- reed store;
- small shrine.

This completes Firascir's **basic string pass**. It does not accept or reject
the special, nonessential feature pools below. Those pools remain draft
material until the later global special-feature review phase.

## Third concrete Land structure: Mortellaria

- Culture: human, mediterranean.
- Default environment: mediterranean.
- Natural Areas: Valdoro Hills, Orivela Coast, Pinavera Valley, Riomara Plain,
  and Stura River.
- Authored settlement Areas: Castavera, the capital; Portomera, the western
  harbor city; Belafonte, the inland market town; and Montaro, the hill town.
- Three village Areas are drawn from the fixed Mortellarian pool and assigned
  to the vineyard, river-plain, and coast-road roles.
- Stura River enters from Firascir, crosses Riomara Plain, and reaches the sea
  south of Portomera.

Working arrangement:

```text
                         Firascir
                            |
                       Stura River
                            |
         Orivela Coast -- Castavera -- Riomara Plain
              |              |              |
          Portomera      Valdoro Hills   river village
              |          /          \
      coast-road village  Belafonte  Montaro
                              |
                       Pinavera Valley
                              |
                      vineyard village
```

### Accepted Land and Area strings

**Mortellaria** — Land.

> A warm human kingdom lies between dry hills and the western sea. Vineyards,
> olive groves, and old stone roads cover the settled country.

**Valdoro Hills** — natural Area, vineyard and olive hills.

> Terraced vineyards and olive groves cover the hills south of Castavera.
> Stone walls divide the slopes.

**Orivela Coast** — natural Area, rocky coast.

> A rocky coast runs west of the capital. Pines grow above its coves and sea
> caves.

**Pinavera Valley** — natural Area, pine valley and dry uplands.

> A dry pine valley cuts through the southern uplands. Goat tracks cross its
> stony slopes.

**Riomara Plain** — natural Area, lower river plain.

> Farms and irrigation channels cover the low plain east of the hills. The
> Stura River bends through its fields.

**Stura River** — natural Area, southbound river.

> The great river continues south from Firascir. It crosses Riomara Plain and
> reaches the western sea.

**Castavera** — settlement Area, capital.

> The walled capital stands above the Stura River road. White stone halls and
> tiled roofs surround its market.

**Portomera** — settlement Area, harbor city.

> A harbor city fills a deep cove on the Orivela Coast. Stone quays shelter
> fishing boats and merchant ships.

**Belafonte** — settlement Area, inland town.

> A market town stands among the lower Valdoro Hills. A public fountain fills
> the square below its olive presses.

**Montaro** — settlement Area, hill town.

> A stone town climbs a steep vineyard hill. Its upper gate overlooks the
> road through Pinavera Valley.

Generated village roles; draw one unused name for each:

**Vineyard village**

> A small village stands among vineyards and olive terraces. Wine carts wait
> beside its press house.

**River-plain village**

> A farming village stands beside an irrigation channel on Riomara Plain.
> Reeds grow along its low walls.

**Coast-road village**

> A fishing village stands where the coast road descends to a sheltered cove.

### Accepted natural Site, Room, and content strings

**Valdoro Hills**

```text
TERRACED ROAD — Site
  LOWER TURN — Room
    fitted stones
    low terrace wall
    cart ruts
  HILL CROSSING — Room
    stone marker
    dry streambed
    two road branches

VINEYARD — Site
  VINE ROWS — Room
    wooden stakes
    grape baskets
    pruning knife
  PRESS HOUSE — Room
    wine press
    clay jars
    drain channel

OLIVE GROVE — Site
  GROVE PATH — Room
    old olive trees
    stone boundary wall
    picking nets
  OIL SHED — Room
    stone press
    oil jars
    wooden measures
```

**Orivela Coast**

```text
CLIFF ROAD — Site
  HIGH TURN — Room
    low stone wall
    road shrine
    view of the cove
  COVE STEPS — Room
    rock-cut steps
    mooring ring
    driftwood

SEA CAVE — Site
  TIDAL MOUTH — Room
    wet stones
    tide line
    shell bank
  DRY CHAMBER — Room
    sand floor
    old firepit
    rope peg

COAST WATCHTOWER — Site
  TOWER FOOT — Room
    stone doorway
    signal wood
    rain barrel
  LOOKOUT — Room
    low parapet
    signal brazier
    coast map
```

**Pinavera Valley**

```text
PINE ROAD — Site
  VALLEY TRACK — Room
    pine needles
    cart ruts
    road marker
  STONE CUT — Room
    cut rock walls
    drainage ditch
    fallen pine

SHEPHERD'S FOLD — Site
  GOAT YARD — Room
    low stone wall
    wooden gate
    water trough
  SHELTER — Room
    small hearth
    wool blankets
    cheese basket

HILL SHRINE — Site
  stone altar
  clay lamps
  water jar
```

**Riomara Plain**

```text
IRRIGATION ROAD — Site
  CHANNEL BANK — Room
    packed earth
    stone-lined channel
    sluice gate
  FIELD CROSSING — Room
    plank bridge
    boundary stones
    willow tree

FARMSTEAD — Site
  FARM YARD — Room
    handcart
    water trough
    grain baskets
  STORE HOUSE — Room
    grain sacks
    olive jars
    tool rack

REED MARSH — Site
  RAISED PATH — Room
    plank walkway
    reed beds
    marker posts
  CLEAR POOL — Room
    open water
    fishing basket
    tied skiff
```

**Stura River**

```text
STONE ROAD BRIDGE — Site
  NORTH BANK — Room
    gravel landing
    willow tree
    road marker
  BRIDGE DECK — Room
    fitted stones
    low parapets
    cart ruts
  SOUTH BANK — Room
    mooring posts
    reed bank
    path downstream

RIVERSIDE MILL — Site
  MILL YARD — Room
    mill stream
    grain sacks
    handcart
  MILL ROOM — Room
    waterwheel shaft
    millstones
    flour bins
  STORE ROOM — Room
    grain sacks
    spare belts
    oil jar

REED LANDING — Site
  RIVER STEPS — Room
    stone steps
    mooring rings
    rope coil
  BOAT SHED — Room
    flat-bottomed boat
    oars
    fish baskets
```

### Accepted settlement Site and Room strings

**Castavera**

```text
ROYAL PALACE
  PUBLIC HALL
  COUNCIL ROOM
  RECORDS ROOM
MAIN MARKET
  FOOD ROW
  CLOTH ROW
  OIL AND WINE ROW
THREE FOUNTAINS INN
  COURTYARD
  COMMON ROOM
  KITCHEN
  CELLAR
  GUEST ROOM
CASTAVERA SMITHY
  FORGE
  COURTYARD
  STORE ROOM
GENERAL SHOP
  SALES ROOM
  STORE ROOM
ALCHEMIST'S SHOP
  SHOP
  WORK ROOM
  LOCKED STORE
RIVER GATE
  GATE PASSAGE
  GUARD ROOM
  WALL WALK
```

Further ordinary Sites:

- ordinary house;
- temple;
- barracks;
- guildhall;
- wine warehouse;
- bathhouse.

**Portomera**

```text
HARBOR HALL
  PUBLIC COUNTER
  COUNCIL ROOM
  RECORDS ROOM
STONE QUAYS
  FISH LANDING
  CARGO YARD
  HARBOR STEPS
HARBOR MARKET
  FISH STALLS
  SALT ROW
  FOREIGN YARD
BLUE SAIL INN
  COURTYARD
  COMMON ROOM
  KITCHEN
  CELLAR
  GUEST ROOM
PORTOMERA SMITHY
  FORGE
  YARD
  STORE ROOM
GENERAL SHOP
  SALES ROOM
  STORE ROOM
SEA WATCH
  GUARD ROOM
  SIGNAL PLATFORM
  HARBOR WALL
```

Further ordinary Sites:

- ordinary house;
- merchant warehouse;
- shipwright;
- smokehouse;
- small temple;
- wine shop.

**Belafonte**

```text
TOWN HALL
  PUBLIC HALL
  COUNCIL ROOM
  RECORDS ROOM
FOUNTAIN MARKET
  STONE FOUNTAIN
  PRODUCE ROW
  CART STAND
OLIVE BRANCH INN
  COURTYARD
  COMMON ROOM
  KITCHEN
  CELLAR
  GUEST ROOM
BELAFONTE SMITHY
  FORGE
  YARD
  STORE ROOM
GENERAL SHOP
  SALES ROOM
  STORE ROOM
PRESS HOUSE
  OLIVE PRESS
  OIL STORE
  LOADING YARD
```

Further ordinary Sites:

- ordinary house;
- vineyard;
- olive warehouse;
- roadside shrine;
- pottery;
- manor.

**Montaro**

```text
HILL HALL
  PUBLIC HALL
  COUNCIL ROOM
  RECORDS ROOM
UPPER GATE
  GATE PASSAGE
  GUARD ROOM
  LOOKOUT
GOAT AND VINE INN
  COMMON ROOM
  KITCHEN
  CELLAR
  GUEST ROOM
MONTARO SMITHY
  FORGE
  YARD
  STORE ROOM
GENERAL SHOP
  SALES ROOM
  STORE ROOM
WINE HOUSE
  PRESS ROOM
  BARREL STORE
  LOADING YARD
```

Further ordinary Sites:

- ordinary house;
- vineyard;
- shepherd's house;
- hill shrine;
- watch post;
- cistern.

**Generated vineyard village**

```text
VILLAGE SQUARE
  STONE WELL
  NOTICE POST
  CART STAND
VINE INN
  COMMON ROOM
  KITCHEN
  CELLAR
  GUEST ROOM
SMITH'S SHED
  FORGE
  YARD
GENERAL STORE
  SALES ROOM
  STORE ROOM
PRESS HOUSE
  WINE PRESS
  JAR STORE
```

**Generated river-plain village**

```text
CHANNEL SQUARE
  STONE WELL
  SLUICE POST
  NOTICE POST
RIVER INN
  COMMON ROOM
  KITCHEN
  GUEST ROOM
SMITH'S SHED
  FORGE
  YARD
GENERAL STORE
  SALES ROOM
  STORE ROOM
GRAIN HOUSE
  GRAIN STORE
  LOADING YARD
```

**Generated coast-road village**

```text
COVE LANDING
  TIMBER JETTY
  BOAT YARD
ROAD INN
  COMMON ROOM
  KITCHEN
  GUEST ROOM
SMITH'S SHED
  FORGE
  YARD
GENERAL STORE
  SALES ROOM
  STORE ROOM
FISH SHED
  CUTTING ROOM
  SALT STORE
```

Every generated village may additionally materialize an ordinary house, farm
or fisher's hut, small shrine, and livelihood store appropriate to its role.

This completes Mortellaria's **MVP basic string pass**.

## Fourth concrete Land structure: Ensimaa

- Culture: elf.
- Default environment: temperate forest.
- Natural Areas: Tiravaine Forest, Koivelle Wood, Maelmor Hills, Avelune
  River, and Saimere Hollow.
- Authored settlement Areas: Taivelle, the capital; Dunmaelle, the western
  town; Kervaine, the river town; and Ruunamont, the hill town.
- Three village Areas are drawn from the fixed elven pool and assigned to the
  deep-forest, river, and woodland-edge roles.
- Buildings use timber, pale plaster, fitted stone, and living trees without
  turning every Room into a magical wonder.

Working arrangement:

```text
                         Maelmor Hills
                               |
                           Ruunamont
                               |
       Dunmaelle -- Koivelle Wood -- Taivelle -- Tiravaine Forest
                         \            |               |
                     edge village  Avelune River  forest village
                                      |
                                  Kervaine
                                      |
                                river village
                                      |
                                Saimere Hollow
```

### Accepted Land and Area strings

**Ensimaa** — Land.

> An elven realm fills the great eastern forest. Rivers, old roads, and small
> settlements run beneath its canopy.

**Tiravaine Forest** — natural Area, deep forest.

> Great oaks and beeches fill the center of Ensimaa. Raised paths cross the
> roots beneath the oldest trees.

**Koivelle Wood** — natural Area, old western woodland.

> Birch and pale beech cover the western wood. Old boundary stones stand
> beside its roads.

**Maelmor Hills** — natural Area, forested hills.

> Wooded hills rise along the northern border. Bare ridges break through the
> trees above the high pastures.

**Avelune River** — natural Area, forest river.

> A clear river runs south through the forest. Root bridges and ferry paths
> join its banks.

**Saimere Hollow** — natural Area, low misty woodland.

> Low woodland surrounds a chain of clear pools. Mist remains between the
> trees until midday.

**Taivelle** — settlement Area, capital.

> The elven capital stands among great living trees beside the Avelune River.
> Timber halls and stone walks circle an open market.

**Dunmaelle** — settlement Area, western town.

> A timber town guards the western forest road. Its gate stands between two
> old beeches.

**Kervaine** — settlement Area, river town.

> A river town stands on both banks of the Avelune. Boats tie beneath its
> broad wooden bridge.

**Ruunamont** — settlement Area, hill town.

> A hill town stands above the northern forest. Stone terraces climb from the
> lower road to its watch hall.

Generated village roles; draw one unused name for each:

**Deep-forest village**

> A small village stands in a wide clearing beneath old trees. Raised paths
> join its timber houses.

**River village**

> A fishing village stands beside a quiet bend of the Avelune River.

**Woodland-edge village**

> A village of foresters and small farms stands at the western edge of
> Koivelle Wood.

### Accepted natural Site, Room, and content strings

**Tiravaine Forest**

```text
ROOT ROAD — Site
  RAISED WALK — Room
    timber walkway
    great roots
    mossy rail
  STREAM GATE — Room
    clear stream
    low bridge
    carved marker

GREAT GROVE — Site
  OUTER RING — Room
    old oaks
    stone seats
    open grass
  INNER TREE — Room
    broad trunk
    root hollow
    offering shelf

WARDEN LODGE — Site
  PORCH — Room
    boot rack
    rain barrel
    warning bell
  MAIN ROOM — Room
    stone hearth
    wall map
    bow rack
  STORE ROOM — Room
    rope coils
    lanterns
    trail markers
```

**Koivelle Wood**

```text
OLD BOUNDARY PATH — Site
  BIRCH TURN — Room
    pale birch trunks
    packed earth
    boundary stone
  BROKEN WALL — Room
    mossy stones
    narrow gap
    old road marker

BIRCH CLEARING — Site
  CLEARING EDGE — Room
    fern beds
    fallen birch
    wood pile
  CHARCOAL HEARTH — Room
    earth mound
    blackened tools
    water bucket

RUINED GATE — Site
  GATE ROAD — Room
    two stone posts
    fallen lintel
    wagon ruts
  GUARD SHELTER — Room
    low wall
    dead firepit
    broken bench
```

**Maelmor Hills**

```text
RIDGE PATH — Site
  WOODED SLOPE — Room
    stone steps
    wind-bent trees
    path marker
  BARE RIDGE — Room
    exposed rock
    low cairn
    view south

HIGH GROVE — Site
  HILLSIDE TREES — Room
    old pines
    spring channel
    stone bench
  OPEN PASTURE — Room
    short grass
    sheep fold
    water trough

STONE LOOKOUT — Site
  LOWER STAIR — Room
    rock-cut steps
    iron handrail
    warning post
  WATCH PLATFORM — Room
    stone parapet
    signal brazier
    hill map
```

**Avelune River**

```text
ROOT BRIDGE — Site
  WEST BANK — Room
    willow roots
    gravel landing
    path marker
  BRIDGE WALK — Room
    living roots
    timber rails
    lantern hooks
  EAST BANK — Room
    stone steps
    mooring post
    path downstream

RIVER ISLAND — Site
  SHINGLE POINT — Room
    smooth stones
    tied skiff
    driftwood
  WILLOW GROVE — Room
    willow trees
    reed mats
    cold firepit

FERRY LANDING — Site
  WEST LANDING — Room
    timber steps
    bell post
    rope coil
  FERRYBOAT — Room
    flat deck
    guide rope
    boat hook
  EAST LANDING — Room
    gravel ramp
    waiting bench
    road marker
```

**Saimere Hollow**

```text
MIST PATH — Site
  FERN WALK — Room
    flat stones
    wet ferns
    white trail marks
  LOW CROSSING — Room
    shallow water
    plank bridge
    willow roots

CLEAR POOL — Site
  POOL BANK — Room
    clear water
    smooth stones
    wooden steps
  SPRING HEAD — Room
    rock basin
    cup on a chain
    herb basket

HEALER'S HUT — Site
  HERB GARDEN — Room
    raised beds
    drying frame
    water barrel
  MAIN ROOM — Room
    tiled hearth
    worktable
    herb shelves
  STORE ROOM — Room
    labeled jars
    folded cloth
    locked cabinet
```

### Accepted settlement Site and Room strings

**Taivelle**

```text
CROWN HALL
  PUBLIC HALL
  COUNCIL ROOM
  RECORDS ROOM
CANOPY MARKET
  FOOD WALK
  CRAFT ROW
  RIVER YARD
ROOT AND RIVER INN
  COMMON ROOM
  KITCHEN
  CELLAR
  GUEST ROOM
TAIVELLE SMITHY
  FORGE
  YARD
  STORE ROOM
GENERAL SHOP
  SALES ROOM
  STORE ROOM
ALCHEMIST'S HOUSE
  SHOP
  WORK ROOM
  LOCKED STORE
WESTERN GATE
  GATE WALK
  GUARD ROOM
  WATCH PLATFORM
```

Further ordinary Sites:

- ordinary house;
- great temple;
- archive;
- warden barracks;
- bowyer;
- garden.

**Dunmaelle**

```text
TOWN HALL
  PUBLIC HALL
  COUNCIL ROOM
  RECORDS ROOM
WESTERN GATE
  GATE WALK
  GUARD ROOM
  WATCH PLATFORM
BEECH AND LANTERN INN
  COMMON ROOM
  KITCHEN
  CELLAR
  GUEST ROOM
DUNMAELLE SMITHY
  FORGE
  YARD
  STORE ROOM
GENERAL SHOP
  SALES ROOM
  STORE ROOM
FORESTER'S YARD
  TIMBER YARD
  TOOL SHED
  MAP ROOM
```

Further ordinary Sites:

- ordinary house;
- bowyer;
- wood store;
- small temple;
- warden lodge;
- healer's house.

**Kervaine**

```text
RIVER HALL
  PUBLIC HALL
  COUNCIL ROOM
  RECORDS ROOM
AVELUNE BRIDGE
  WEST GATE
  BRIDGE WALK
  EAST GATE
RIVER MARKET
  FISH ROW
  BOAT YARD
  PRODUCE WALK
WILLOW INN
  COMMON ROOM
  KITCHEN
  CELLAR
  GUEST ROOM
KERVAINE SMITHY
  FORGE
  YARD
  STORE ROOM
GENERAL SHOP
  SALES ROOM
  STORE ROOM
```

Further ordinary Sites:

- ordinary house;
- ferry house;
- boat shed;
- fish store;
- river shrine;
- herb shop.

**Ruunamont**

```text
HILL COUNCIL
  PUBLIC HALL
  COUNCIL ROOM
  RECORDS ROOM
HIGH WATCH
  LOWER STAIR
  GUARD ROOM
  SIGNAL PLATFORM
PINE AND STONE INN
  COMMON ROOM
  KITCHEN
  CELLAR
  GUEST ROOM
RUUNAMONT SMITHY
  FORGE
  YARD
  STORE ROOM
GENERAL SHOP
  SALES ROOM
  STORE ROOM
PASTURE YARD
  SHEEP PENS
  WOOL STORE
  LOADING YARD
```

Further ordinary Sites:

- ordinary house;
- shepherd's house;
- bowyer;
- hill temple;
- watch post;
- quarry office.

**Generated deep-forest village**

```text
VILLAGE CIRCLE
  OLD TREE
  STONE WELL
  NOTICE POST
FERN INN
  COMMON ROOM
  KITCHEN
  GUEST ROOM
SMITH'S SHELTER
  FORGE
  YARD
GENERAL STORE
  SALES ROOM
  STORE ROOM
WARDEN POST
  DUTY ROOM
  EQUIPMENT STORE
```

**Generated river village**

```text
RIVER LANDING
  TIMBER JETTY
  BOAT YARD
WILLOW INN
  COMMON ROOM
  KITCHEN
  GUEST ROOM
SMITH'S SHELTER
  FORGE
  YARD
GENERAL STORE
  SALES ROOM
  STORE ROOM
FISH HOUSE
  CUTTING ROOM
  NET STORE
```

**Generated woodland-edge village**

```text
VILLAGE GREEN
  OLD BEECH
  STONE WELL
  NOTICE POST
ROAD INN
  COMMON ROOM
  KITCHEN
  GUEST ROOM
SMITH'S SHELTER
  FORGE
  YARD
GENERAL STORE
  SALES ROOM
  STORE ROOM
TIMBER YARD
  LOG YARD
  TOOL SHED
```

Every generated village may additionally materialize an ordinary house,
forester's hut, small shrine, healer's room, and livelihood store appropriate
to its role.

This completes Ensimaa's **MVP basic string pass**.

## Fifth concrete Land structure: Gibili

- Culture: goblin.
- Default environment: mediterranean.
- Natural Areas: Kapaliki Coast, Barasa Hills, Paina Valley, Wela River, and
  Satakalu Plain.
- Authored settlement Areas: Maketawa, the capital; Potalu, the harbor town;
  Birikava, the inland town; and Boilaki, the hill town.
- Three village Areas are drawn from the fixed goblin pool and assigned to
  the coast, river, and brick-country roles.
- Goblin construction reuses stone, brick, timber, sheet metal, rope, and
  repaired machinery. A place may look patched without being ruined.

Working arrangement:

```text
                         Barasa Hills
                              |
                          Boilaki
                              |
      Kapaliki Coast -- Maketawa -- Satakalu Plain
            |             |              |
         Potalu       Wela River     brick village
            |             |
      coast village    river village
                          |
                      Birikava
                          |
                     Paina Valley
```

### Accepted Land and Area strings

**Gibili** — Land.

> A goblin country spreads across a hot coast and dry inland hills. Brick
> roads, patched towers, and crowded yards join its settlements.

**Kapaliki Coast** — natural Area, rocky coast.

> A broken coast of low cliffs and narrow coves runs along western Gibili.
> Sea caves open below the road.

**Barasa Hills** — natural Area, olive scrub and dry hills.

> Dry hills rise north of Maketawa. Olive scrub and abandoned quarries cover
> their lower slopes.

**Paina Valley** — natural Area, pine valley.

> A pine valley runs south from Birikava. Charcoal tracks cross the dry
> forest floor.

**Wela River** — natural Area, river plain.

> A brown river crosses the settled center of Gibili. Rope ferries and reed
> yards line its banks.

**Satakalu Plain** — natural Area, hot inland plain.

> Dry grass and clay flats stretch east of the capital. Brick pits mark the
> old road.

**Maketawa** — settlement Area, capital.

> The goblin capital crowds both sides of the Wela River. Brick halls, metal
> roofs, and market awnings fill the inner wall.

**Potalu** — settlement Area, harbor town.

> A harbor town stands around a narrow cove on the Kapaliki Coast. Piled
> timber jetties reach between the rocks.

**Birikava** — settlement Area, inland town.

> A busy town stands where the river road meets the road to Paina Valley.
> Carts and repair yards fill its outer streets.

**Boilaki** — settlement Area, hill town.

> A brick town stands below an old quarry in the Barasa Hills. Smoke rises
> from lime kilns outside its wall.

Generated village roles; draw one unused name for each:

**Coast village**

> A fishing village fills a small cove below the Kapaliki road. Nets hang
> from every rail.

**River village**

> A reed-cutting village stands beside a rope ferry on the Wela River.

**Brick-country village**

> A small village stands beside clay pits on Satakalu Plain. Brick clamps
> smoke beyond its yards.

### Accepted natural Site, Room, and content strings

**Kapaliki Coast**

```text
CLIFF TRACK — Site
  ROCKY TURN — Room
    gravel path
    rope rail
    road marker
  COVE DROP — Room
    timber steps
    mooring ring
    driftwood

SEA CAVE — Site
  CAVE MOUTH — Room
    tide pools
    wet stones
    rope posts
  UPPER SHELF — Room
    dry ledge
    old firepit
    broken crate

WRECK YARD — Site
  BEACH — Room
    broken hull
    driftwood piles
    iron nails
  SORTING SHED — Room
    workbench
    rope coils
    scrap baskets
```

**Barasa Hills**

```text
QUARRY ROAD — Site
  LOWER TRACK — Room
    cart ruts
    cut stone blocks
    warning post
  HIGH TURN — Room
    low wall
    broken handcart
    view of the plain

ABANDONED QUARRY — Site
  QUARRY FLOOR — Room
    stone chips
    lifting frame
    rusted tools
  CUT FACE — Room
    drill holes
    loose blocks
    shallow cave

OLIVE CAMP — Site
  GROVE YARD — Room
    scrubby olive trees
    picking nets
    water barrel
  PRESS SHED — Room
    small press
    clay jars
    tool rack
```

**Paina Valley**

```text
PINE TRACK — Site
  DRY FORD — Room
    stone bed
    timber marker
    cart tracks
  FOREST TURN — Room
    pine needles
    charcoal sacks
    cut stump

CHARCOAL CAMP — Site
  BURNING GROUND — Room
    earth mounds
    long rakes
    water barrels
  STORE SHELTER — Room
    charcoal sacks
    rope coils
    handcart

SPRING WORKS — Site
  SPRING HEAD — Room
    stone basin
    iron pipe
    cup on a chain
  TANK YARD — Room
    wooden tank
    repair tools
    drainage ditch
```

**Wela River**

```text
RIVER ROAD — Site
  MUD BANK — Room
    packed earth
    reed fence
    cart tracks
  RAISED WALK — Room
    plank walkway
    mooring posts
    warning bell

ROPE FERRY — Site
  WEST LANDING — Room
    timber ramp
    bell post
    rope drum
  FERRY DECK — Room
    flat deck
    guide rope
    boat hook
  EAST LANDING — Room
    muddy steps
    waiting shelter
    road marker

REED WORKS — Site
  CUTTING BANK — Room
    reed bundles
    narrow skiff
    cutting knives
  DRYING YARD — Room
    drying racks
    woven mats
    cord bundles
```

**Satakalu Plain**

```text
DUST ROAD — Site
  CART TRACK — Room
    hard clay
    wheel ruts
    stone marker
  SHADE SHELTER — Room
    patched roof
    water jar
    hitching rail

WATERING YARD — Site
  CISTERN — Room
    brick tank
    hand pump
    water trough
  CORRAL — Room
    timber fence
    feed baskets
    shade cloth

BRICK PIT — Site
  CLAY CUT — Room
    clay bank
    digging tools
    plank ramp
  FIRING GROUND — Room
    brick clamps
    wood piles
    stacked bricks
```

### Accepted settlement Site and Room strings

**Maketawa**

```text
HIGH OFFICE
  PUBLIC HALL
  COUNCIL ROOM
  RECORDS ROOM
MAKETAWA MARKET
  FOOD ROW
  PARTS ROW
  RIVER YARD
BRASS POT INN
  COMMON ROOM
  KITCHEN
  CELLAR
  GUEST ROOM
MAKETAWA METAL SHOP
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
RIVET GATE
  GATE PASSAGE
  GUARD ROOM
  WALL WALK
```

Further ordinary Sites:

- ordinary house;
- watch barracks;
- brick temple;
- guild yard;
- repair shed;
- warehouse.

**Potalu**

```text
HARBOR OFFICE
  PUBLIC COUNTER
  COUNCIL ROOM
  RECORDS ROOM
PILE JETTIES
  FISH LANDING
  NET YARD
  CARGO WALK
FISH MARKET
  FISH STALLS
  SALT ROW
  BASKET YARD
NET AND KETTLE INN
  COMMON ROOM
  KITCHEN
  CELLAR
  GUEST ROOM
POTALU METAL SHOP
  FORGE
  YARD
  STORE ROOM
GENERAL SHOP
  SALES ROOM
  STORE ROOM
COAST WATCH
  GUARD ROOM
  SIGNAL PLATFORM
  ROOF WALK
```

Further ordinary Sites:

- ordinary house;
- wreck yard;
- boat shed;
- smokehouse;
- rope shop;
- small temple.

**Birikava**

```text
TOWN OFFICE
  PUBLIC HALL
  COUNCIL ROOM
  RECORDS ROOM
PARTS MARKET
  TOOL ROW
  CART YARD
  CLOTH ROW
BRICK AND BOTTLE INN
  COMMON ROOM
  KITCHEN
  CELLAR
  GUEST ROOM
  STABLE
BIRIKAVA METAL SHOP
  FORGE
  YARD
  STORE ROOM
GENERAL SHOP
  SALES ROOM
  STORE ROOM
CART WORKS
  REPAIR FLOOR
  PARTS STORE
  OUTER YARD
```

Further ordinary Sites:

- ordinary house;
- warehouse;
- wheelwright;
- reed store;
- small shrine;
- repair yard.

**Boilaki**

```text
HILL OFFICE
  PUBLIC HALL
  COUNCIL ROOM
  RECORDS ROOM
QUARRY GATE
  GATE PASSAGE
  GUARD ROOM
  LOADING WALK
LIME AND LADLE INN
  COMMON ROOM
  KITCHEN
  CELLAR
  GUEST ROOM
BOILAKI METAL SHOP
  FORGE
  YARD
  STORE ROOM
GENERAL SHOP
  SALES ROOM
  STORE ROOM
LIME KILN
  KILN YARD
  FUEL STORE
  BRICK SHED
```

Further ordinary Sites:

- ordinary house;
- quarry office;
- brick yard;
- water store;
- hill shrine;
- watch post.

**Generated coast village**

```text
COVE YARD
  TIMBER JETTY
  NET RACK
KETTLE INN
  COMMON ROOM
  KITCHEN
  GUEST ROOM
METAL SHED
  FORGE
  YARD
GENERAL STORE
  SALES ROOM
  STORE ROOM
FISH SHED
  CUTTING ROOM
  SALT STORE
```

**Generated river village**

```text
FERRY YARD
  WEST LANDING
  ROPE DRUM
  WAITING SHED
FERRY INN
  COMMON ROOM
  KITCHEN
  GUEST ROOM
METAL SHED
  FORGE
  YARD
GENERAL STORE
  SALES ROOM
  STORE ROOM
REED WORKS
  CUTTING YARD
  DRY STORE
```

**Generated brick-country village**

```text
VILLAGE YARD
  WATER TANK
  NOTICE POST
  CART STAND
BRICK INN
  COMMON ROOM
  KITCHEN
  GUEST ROOM
METAL SHED
  FORGE
  YARD
GENERAL STORE
  SALES ROOM
  STORE ROOM
BRICK WORKS
  CLAY YARD
  FIRING GROUND
  BRICK SHED
```

Every generated village may additionally materialize an ordinary house,
worker's shed, small shrine, store yard, and livelihood Site appropriate to
its role.

This completes Gibili's **MVP basic string pass**.

## Sixth concrete Land structure: Tergal

- Culture: orc.
- Default environment: prairie.
- Natural Areas: Khuratal Steppe, Borugal Hills, Temur Ridge, Namak Basin,
  Kharun River, and Flumenpur River.
- Authored settlement Areas: Ulus-Gal, the capital; Kharuk, the western town;
  Temenur, the northern town; and Ordubal, the southern town.
- Three village Areas are drawn from the fixed orc pool and assigned to the
  herd-road, river, and basin roles.
- Flumenpur River enters western Tergal from Caelum. Kharun River drains the
  eastern plain.

Working arrangement:

```text
                         Borugal Hills
                              |
                          Temenur
                              |
         Flumenpur River -- Kharuk -- Temur Ridge
                  |             \          |
               Caelum        Ulus-Gal -- Khuratal Steppe
                                |              |
                           herd village    Kharun River
                                |              |
                          Namak Basin -- river village
                                |
                             Ordubal
                                |
                          basin village
```

### Accepted Land and Area strings

**Tergal** — Land.

> An orc realm covers the eastern prairie. Herd roads cross its grasslands
> between rivers, dry basins, and broken hills.

**Khuratal Steppe** — natural Area, open prairie.

> Open grassland stretches east of Ulus-Gal. Herd trails and wagon roads run
> beneath the constant wind.

**Borugal Hills** — natural Area, broken hills.

> Broken stone hills rise along the northern border. Narrow passes cut
> between their bare slopes.

**Temur Ridge** — natural Area, high grazing range.

> A long ridge overlooks the central prairie. Horses and sheep graze on its
> high slopes.

**Namak Basin** — natural Area, dry southern basin.

> A dry basin lies south of the capital. Salt grass grows around its wells and
> seasonal pools.

**Kharun River** — natural Area, eastern river plain.

> A broad river crosses the eastern prairie. Willow groves mark its bends.

**Flumenpur River** — natural Area, western river.

> The great river enters Tergal from Caelum. The western road follows its
> north bank toward Kharuk.

**Ulus-Gal** — settlement Area, capital.

> The walled capital stands on a low rise above the prairie. Broad roads lead
> from its great hall to the horse market and eastern gate.

**Kharuk** — settlement Area, western town.

> A road town guards the Flumenpur crossing. Traders from Caelum camp outside
> its western wall.

**Temenur** — settlement Area, northern town.

> A stone town stands below Temur Ridge. Herd pens and wool stores fill its
> lower quarter.

**Ordubal** — settlement Area, southern town.

> A low-walled town stands beside the main well of Namak Basin. Salt and
> livestock caravans meet in its yard.

Generated village roles; draw one unused name for each:

**Herd-road village**

> A herding village stands beside a well on Khuratal Steppe. Corrals surround
> its low houses.

**River village**

> A fishing and ferry village stands in a willow bend of the Kharun River.

**Basin village**

> A small village stands beside a deep well in Namak Basin. Salt grass and
> goat pens surround it.

### Accepted natural Site, Room, and content strings

**Khuratal Steppe**

```text
HERD ROAD — Site
  WAGON TRACK — Room
    twin ruts
    stone marker
    old dung fires
  GRASS CROSSING — Room
    herd trail
    low rise
    direction post

WATERING PLACE — Site
  WELL YARD — Room
    stone well
    water trough
    hitching posts
  REST SHELTER — Room
    felt awning
    fire ring
    feed baskets

HUNTER'S CAMP — Site
  FIREPIT — Room
    stone fire ring
    hide screens
    cooking pot
  GEAR SHELTER — Room
    bow rack
    rope coils
    skinning frame
```

**Borugal Hills**

```text
BROKEN PASS — Site
  LOWER ROAD — Room
    loose stones
    cart ruts
    warning marker
  NARROW CUT — Room
    high rock walls
    fallen boulder
    old firepit

STONE QUARRY — Site
  QUARRY FLOOR — Room
    cut blocks
    lifting frame
    stone sled
  TOOL SHELTER — Room
    hammers
    iron wedges
    water barrel

BURIAL MOUND — Site
  MOUND FOOT — Room
    standing stones
    worn path
    offering bowl
  STONE DOOR — Room
    fitted slabs
    carved lintel
    sealed entrance
```

**Temur Ridge**

```text
RIDGE ROAD — Site
  GRASS SLOPE — Room
    switchback track
    low cairn
    wind-bent shrubs
  HIGH SADDLE — Room
    flat stones
    road marker
    view of the steppe

HIGH PASTURE — Site
  GRAZING GROUND — Room
    short grass
    horse lines
    salt blocks
  HERDER'S SHELTER — Room
    stone hearth
    felt rolls
    water skins

WATCH POST — Site
  LOWER YARD — Room
    hitching rail
    firepit
    wood stack
  LOOKOUT — Room
    stone platform
    signal brazier
    ridge map
```

**Namak Basin**

```text
DRY TRACK — Site
  SALT-GRASS ROAD — Room
    hard earth
    wagon ruts
    bone marker
  BASIN TURN — Room
    dry channel
    low cairn
    forked road

SALT SPRING — Site
  SPRING YARD — Room
    mineral pool
    stone trough
    salt crust
  DRYING RACKS — Room
    clay pans
    reed mats
    storage jars

ABANDONED CORRAL — Site
  OUTER FENCE — Room
    broken posts
    open gate
    old tracks
  HERDER'S HUT — Room
    cold hearth
    low table
    empty water skins
```

**Kharun River**

```text
RIVER FORD — Site
  WEST BANK — Room
    willow trees
    gravel track
    marker post
  FORD — Room
    shallow water
    guide stakes
    firm stone bed
  EAST BANK — Room
    muddy landing
    hitching rail
    road east

WILLOW CAMP — Site
  RIVER CLEARING — Room
    willow shade
    fire ring
    fish rack
  BOAT SHELTER — Room
    narrow boat
    oars
    net basket

FERRY POINT — Site
  WEST LANDING — Room
    timber ramp
    bell post
    rope drum
  FERRYBOAT — Room
    broad deck
    guide rope
    boat hook
  EAST LANDING — Room
    stone steps
    waiting bench
    direction post
```

**Flumenpur River**

```text
WESTERN CROSSING — Site
  CAELUM ROAD — Room
    packed earth
    border marker
    willow tree
  BRIDGE DECK — Room
    timber roadway
    stone piers
    low rails
  TERGAL ROAD — Room
    wagon yard
    hitching posts
    guard shelter

NORTH BANK ROAD — Site
  RIVER TRACK — Room
    gravel road
    mooring rings
    cart tracks
  BLUFF TURN — Room
    low stone wall
    signal post
    view west

TRADER'S LANDING — Site
  RIVER STEPS — Room
    fitted stones
    mooring posts
    cargo hook
  STORE SHELTER — Room
    stacked crates
    rope coils
    tally board
```

### Accepted settlement Site and Room strings

**Ulus-Gal**

```text
GREAT HALL
  PUBLIC HALL
  COUNCIL ROOM
  RECORDS ROOM
HORSE MARKET
  HORSE YARD
  TACK ROW
  TRADER'S CAMP
OPEN HEARTH INN
  COMMON ROOM
  KITCHEN
  STORE ROOM
  GUEST ROOM
  STABLE
ULUS-GAL FORGE
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
EAST GATE
  GATE PASSAGE
  GUARD ROOM
  WALL WALK
```

Further ordinary Sites:

- ordinary house;
- barracks;
- ancestor temple;
- wool hall;
- caravan yard;
- bowyer.

**Kharuk**

```text
ROAD HALL
  PUBLIC HALL
  COUNCIL ROOM
  RECORDS ROOM
FLUMENPUR BRIDGE
  WEST GATE
  BRIDGE DECK
  EAST GATE
WEST ROAD INN
  COMMON ROOM
  KITCHEN
  STORE ROOM
  GUEST ROOM
  STABLE
KHARUK FORGE
  FORGE
  YARD
  STORE ROOM
GENERAL SHOP
  SALES ROOM
  STORE ROOM
CARAVAN YARD
  WAGON YARD
  CARGO STORE
  ANIMAL PENS
```

Further ordinary Sites:

- ordinary house;
- foreign warehouse;
- ferry house;
- small temple;
- leather shop;
- guard post.

**Temenur**

```text
RIDGE HALL
  PUBLIC HALL
  COUNCIL ROOM
  RECORDS ROOM
HERD MARKET
  SHEEP PENS
  WOOL ROW
  HORSE YARD
LONG FIRE INN
  COMMON ROOM
  KITCHEN
  STORE ROOM
  GUEST ROOM
  STABLE
TEMENUR FORGE
  FORGE
  YARD
  STORE ROOM
GENERAL SHOP
  SALES ROOM
  STORE ROOM
RIDGE WATCH
  GUARD ROOM
  SIGNAL PLATFORM
  UPPER YARD
```

Further ordinary Sites:

- ordinary house;
- wool store;
- bowyer;
- hill temple;
- tannery;
- shepherd's house.

**Ordubal**

```text
TOWN HALL
  PUBLIC HALL
  COUNCIL ROOM
  RECORDS ROOM
GREAT CISTERN
  WELL YARD
  PUMP HOUSE
  WATER STORE
SALT ROAD INN
  COMMON ROOM
  KITCHEN
  STORE ROOM
  GUEST ROOM
  STABLE
ORDUBAL FORGE
  FORGE
  YARD
  STORE ROOM
GENERAL SHOP
  SALES ROOM
  STORE ROOM
SALT MARKET
  SALT ROW
  GOAT YARD
  CART STAND
```

Further ordinary Sites:

- ordinary house;
- salt store;
- goat yard;
- basin shrine;
- caravan shed;
- healer's house.

**Generated herd-road village**

```text
VILLAGE WELL
  STONE WELL
  WATER TROUGHS
  NOTICE POST
HERD INN
  COMMON ROOM
  KITCHEN
  STORE ROOM
  GUEST ROOM
SMITH'S FORGE
  FORGE
  YARD
GENERAL STORE
  SALES ROOM
  STORE ROOM
HERD YARD
  ANIMAL PENS
  TACK SHED
```

**Generated river village**

```text
RIVER LANDING
  TIMBER JETTY
  FERRY YARD
WILLOW INN
  COMMON ROOM
  KITCHEN
  GUEST ROOM
SMITH'S FORGE
  FORGE
  YARD
GENERAL STORE
  SALES ROOM
  STORE ROOM
FISH HOUSE
  CUTTING ROOM
  NET STORE
```

**Generated basin village**

```text
DEEP WELL
  STONE WELL
  WATER TROUGHS
  SHADE SHELTER
BASIN INN
  COMMON ROOM
  KITCHEN
  STORE ROOM
  GUEST ROOM
SMITH'S FORGE
  FORGE
  YARD
GENERAL STORE
  SALES ROOM
  STORE ROOM
GOAT YARD
  GOAT PENS
  FEED STORE
```

Every generated village may additionally materialize an ordinary house,
herder's house, small temple, healer's room, and livelihood Site appropriate
to its role.

This completes Tergal's **MVP basic string pass**.

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

Accepted Site-name models:

- Borin's House — dwarf;
- Sela's House — human;
- Aurenne's House — elf;
- Kikawa's House — goblin;
- Sargul's House — orc.

`Main Room` heating, choose one:

- stone hearth;
- iron stove.

Culture additions:

- tiled hearth — Mortellarian or elf;
- clay stove — goblin or orc;
- iron brazier — goblin;

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

- black bread — dwarf;
- brown bread — human;
- flatbread — Mortellarian, goblin, or orc;
- oat bread — elf;
- onions;
- hard cheese;
- dried mushrooms — dwarf;
- dried mushrooms — elf;
- dried apples — human;
- olives — Mortellarian;
- dried peppers — goblin;
- dried curds — orc;
- berry preserves — elf;
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
- goat pen — dwarf;
- chicken coop — human;
- herb bed — Mortellarian or elf;
- scrap basket — goblin;
- hitching rail — orc;
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

Firascir human livelihood overlays:

Tomburgh:

- account book;
- sealing wax;
- guard belt;
- folded cloth;
- writing case.

Leehaven:

- fishing net;
- iron hooks;
- cork floats;
- sailcloth;
- fish basket.

Walhaven:

- cargo tally;
- rope coil;
- tar pot;
- crate bar;
- merchant scales.

Bradwhitchip:

- sickle;
- grain sack;
- seed basket;
- harness;
- wooden measure.

Redflurton:

- reed knife;
- eel basket;
- ferry rope;
- waterproof boots;
- fish trap.

Sturford:

- plough blade;
- grain sack;
- ferry pole;
- horse tack;
- seed basket.

Ackham:

- hand saw;
- splitting axe;
- timber wedges;
- charcoal basket;
- leather apron.

Flurham:

- fishing line;
- reed basket;
- cork floats;
- boat hook;
- salt sack.

Mortellarian livelihood overlays:

Castavera:

- account book;
- sealing wax;
- folded cloth;
- oil jar;
- writing case.

Portomera:

- fishing net;
- sailcloth;
- cargo tally;
- tar pot;
- fish basket.

Belafonte:

- pruning knife;
- olive basket;
- oil measure;
- pottery tools;
- market scales.

Montaro:

- grape basket;
- barrel hoops;
- goat bell;
- pruning hook;
- wine tally.

Vineyard village:

- pruning knife;
- grape basket;
- picking net;
- clay wine jug;
- olive rake.

River-plain village:

- sickle;
- grain sack;
- sluice key;
- reed basket;
- wooden measure.

Coast-road village:

- fishing line;
- cork floats;
- salt sack;
- boat hook;
- net needle.

Elven livelihood overlays:

Taivelle:

- account book;
- map case;
- folded cloth;
- carving knife;
- herb basket.

Dunmaelle:

- hand saw;
- timber wedges;
- bow stave;
- trail markers;
- leather apron.

Kervaine:

- fishing line;
- oar blade;
- reed basket;
- ferry rope;
- fish trap.

Ruunamont:

- wool bundle;
- shepherd's crook;
- quarry hammer;
- signal cord;
- horse tack.

Deep-forest village:

- bow stave;
- herb basket;
- trail markers;
- pruning knife;
- hide scraper.

River village:

- fishing net;
- cork floats;
- boat hook;
- reed basket;
- net needle.

Woodland-edge village:

- hand saw;
- splitting axe;
- seed basket;
- charcoal basket;
- leather apron.

Goblin livelihood overlays:

Maketawa:

- tally slate;
- rivet box;
- folded awning cloth;
- repair tools;
- labeled parts tin.

Potalu:

- fishing net;
- rope coil;
- scrap hook;
- tar pot;
- cork floats.

Birikava:

- wheel pin;
- tool roll;
- cargo tally;
- crate bar;
- spare harness.

Boilaki:

- quarry hammer;
- lime scoop;
- brick mold;
- dust mask;
- iron wedges.

Coast village:

- net needle;
- fish basket;
- rope coil;
- hull scraper;
- salt sack.

River village:

- reed knife;
- ferry rope;
- matting needle;
- boat hook;
- cord bundle.

Brick-country village:

- brick mold;
- clay spade;
- firing tongs;
- handcart pin;
- charcoal basket.

Orc livelihood overlays:

Ulus-Gal:

- tack repair kit;
- market tally;
- wool bundle;
- bow case;
- seal box.

Kharuk:

- cargo tally;
- harness;
- ferry rope;
- foreign coin weights;
- crate bar.

Temenur:

- wool shears;
- saddle blanket;
- shepherd's crook;
- bow stave;
- salt blocks.

Ordubal:

- salt scoop;
- water tally;
- goat bell;
- clay jar;
- caravan rope.

Herd-road village:

- horse brush;
- rope halter;
- feed basket;
- leather needle;
- wool shears.

River village:

- fishing net;
- ferry pole;
- fish basket;
- boat hook;
- reed mat.

Basin village:

- water skin;
- salt scoop;
- goat tack;
- reed mat;
- well rope.

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

These ordinary pools are accepted in the Dvarvengrond and Firascir base
passes and may be reused by later cultures where their wording and material
fit.

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

`Jetty`, `Quay`, or `Landing`:

- stone quay;
- timber platform;
- mooring posts;
- rope coils;
- cargo hook;
- handcart;
- fish baskets;
- small crane.

`Smokehouse` or `Fish Shed`:

- smoking racks;
- fire trench;
- fish hooks;
- salt barrel;
- cutting table;
- knives;
- wood pile.

Firascir adds these accepted basic pools:

`Throne Hall` or `Public Hall`:

- long table;
- raised seat;
- benches;
- wall banners;
- public notice board;
- petition rail;
- iron braziers.

Human `Council Room`:

- table;
- chairs;
- wall map;
- account books;
- contract box;
- seal press;
- locked chest.

`Harbor Hall Public Counter`:

- long counter;
- harbor ledger;
- ship list;
- wall map;
- weighing scales;
- seal box;
- bell.

`Stable`:

- stalls;
- hay rack;
- water trough;
- tack pegs;
- feed bin;
- pitchfork;
- stable lantern.

`Gate Passage` or `Gatehouse`:

- timber gates;
- portcullis;
- guard bench;
- weapon rack;
- bell rope;
- key board.

`Wall Walk` or `Signal Platform`:

- stone parapet;
- signal brazier;
- warning bell;
- arrow chest;
- watch shelter.

`Bridge Deck`:

- stone roadway;
- low parapets;
- lamp posts;
- drainage gaps;
- cart ruts.

`Cargo Yard`:

- stacked crates;
- barrels;
- handcarts;
- cargo net;
- weighing scales;
- tally board.

`Fish Market`:

- fish stalls;
- cutting tables;
- baskets;
- weighing scales;
- salt barrels;
- water buckets;
- canvas awnings.

`Grain Row` or `Grain Store`:

- grain sacks;
- flour bins;
- weighing scales;
- tally board;
- handcart;
- grain scoops;
- mouse traps.

`Livestock Yard`:

- timber pens;
- hitching rails;
- water trough;
- feed baskets;
- weighing gate;
- straw.

`Village Green`:

- old tree;
- stone well;
- notice post;
- benches;
- hitching rail;
- water trough.

`Ford` or `River Crossing`:

- shallow water;
- gravel bed;
- marker posts;
- guide rope;
- muddy banks;
- cart tracks.

`Timber Yard`:

- cut logs;
- timber stacks;
- splitting block;
- handcart;
- saw frame;
- wood chips.

`Boat Yard`:

- pulled-up skiffs;
- trestles;
- rope coils;
- tar pot;
- spare planks;
- oars.

Mortellaria adds:

`Courtyard`:

- stone paving;
- covered tables;
- water basin;
- clay planters;
- hitching rings;
- canvas shade.

`Oil and Wine Row`, `Press Room`, or `Press House`:

- olive baskets;
- grape baskets;
- stone press;
- wooden press;
- clay jars;
- barrel racks;
- wooden measures;
- drain channel.

`Stone Fountain` or `Well`:

- carved basin;
- iron spout;
- water jars;
- stone bench;
- drainage channel.

`Pottery` or `Jar Store`:

- clay jars;
- stacked tiles;
- potter's wheel;
- drying shelves;
- clay bins;
- packing straw.

Ensimaa adds:

`Gate Walk` or `Raised Walk`:

- timber walkway;
- carved rails;
- lantern hooks;
- warning bell;
- root steps;
- watch bench.

`Warden Post` or `Forester's Yard`:

- wall map;
- duty board;
- bow rack;
- lantern shelf;
- rope coils;
- trail markers;
- tool shed.

`Craft Row`:

- carving tables;
- bow staves;
- folded cloth;
- herb baskets;
- small awnings;
- handcarts.

`Herb Room`, `Healer's Room`, or `Herb Shop`:

- worktable;
- drying rack;
- labeled jars;
- folded cloth;
- water basin;
- mortar;
- locked cabinet.

Gibili adds:

`Parts Row`, `Parts Store`, or `Repair Floor`:

- parts bins;
- rivet boxes;
- gear wheels;
- tool rack;
- oil cans;
- repair bench;
- scrap baskets.

`Metal Shop` or `Metal Shed`:

- forge;
- anvil;
- quench barrel;
- hand drill;
- rivet tray;
- scrap pile;
- tool rack.

`Brick Works`, `Brick Shed`, or `Firing Ground`:

- brick molds;
- clay barrows;
- stacked bricks;
- charcoal baskets;
- firing tongs;
- water barrel.

`Reed Works`:

- reed bundles;
- cutting knives;
- drying racks;
- woven mats;
- cord bundles;
- handcart.

Tergal adds:

`Horse Market`, `Herd Market`, or `Herd Yard`:

- timber pens;
- hitching rails;
- water troughs;
- feed baskets;
- tack racks;
- tally board;
- judging ring.

`Tack Row`, `Tack Shed`, or `Stable Store`:

- saddles;
- rope halters;
- folded blankets;
- harness;
- leather tools;
- feed sacks.

`Wool Row` or `Wool Store`:

- wool bales;
- shears;
- weighing scales;
- tally board;
- packing cloth;
- handcart.

`Cistern`, `Pump House`, or `Water Store`:

- stone tank;
- hand pump;
- well rope;
- water jars;
- repair tools;
- locked grate.

`Caravan Yard` or `Trader's Camp`:

- wagons;
- cargo stacks;
- animal pens;
- hitching rails;
- cook fire;
- tally board;
- canvas shelters.

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
- hidden or mutable states normally do not;
- a river which crosses several Lands keeps one canonical name for its whole
  course; culture profiles do not translate or regenerate it at a border.

The cultural profiles below govern proper nouns for Lands, natural Areas, and
settlements. Ordinary functional Site and Room labels remain plain English so
the map is immediately legible. An exceptional Site which needs a proper
label reuses its parent name with an English function, such as `Taivelle Gate`
or `Maketawa Market`; it does not open another generated proper-name pool. The
six settled MVP cultures now have complete proper-name rosters and concrete
basic catalogs. Later revisions to descriptions, Site layouts, Room labels,
or contents do not reopen the proper names unless the designer explicitly
does so.

Canonical cross-Land rivers:

- **Stura River** — Firascir and Mortellaria;
- **Flumenpur River** — Firascir, Caelum, and Tergal.

### Natural Area patterns

```text
The + Modifier + Place Noun
Modifier + Place Noun
Creature or Plant + Place Noun
Person's Name + Place Noun
Place Noun + geographic qualifier
```

Use `Whitweld Forest` in prose but store the canonical name consistently;
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

- Firascir uses loose invented English-sounding names;
- authored models: Tomburgh, Leehaven, Walhaven, Bradwhitchip, Redflurton,
  Sturford, Ackham, and Flurham;
- generated village models: Sturham, Sturworth, Newton, Midton, Aston,
  Tomton, Walham, Coldcot, Thornley, Blackton, Astmoor, Ackbridge, Ackton,
  Mickleham, and Shepham.

Human mediterranean:

- use an Italian-Spanish pastiche written as an English speaker might spell it
  by ear;
- keep spelling simple and ASCII: clear vowels, few silent letters, no
  accents, and no claim of correct real-world language;
- prefer names which sound Romance without becoming transparent English
  compounds such as `Goldport` or `Olive Hill`;
- the Land is **Mortellaria**;
- finite natural Areas:
  - **Valdoro Hills** — vineyard and olive hills;
  - **Orivela Coast** — rocky western coast;
  - **Pinavera Valley** — pine valley and dry uplands;
  - **Riomara Plain** — lower river plain;
  - **Stura River** — the same river named in Firascir, continuing south to
    the sea;
- authored settlements:
  - **Castavera** — capital;
  - **Portomera** — harbor city;
  - **Belafonte** — inland town;
  - **Montaro** — hill town;
- generated village name pool (one is built at world creation; the rest are
  the land's reserve):
  - Alavera;
  - Beloro;
  - Calavento;
  - Doramonte;
  - Fontela;
  - Lunaro;
  - Maravento;
  - Oliveta;
  - Rosavera;
  - Sanoro;
  - Solavela;
  - Toralba;
  - Valesero;
  - Ventoro;
  - Vilaro.

Elf:

- use a loose Finnish-Gaelic-French sound blend: open vowels and doubled
  vowels beside soft consonants, `ae`/`ai`/`ui` clusters, and occasional
  `dun`, `mael`, `-elle`, `-enne`, `-aine`, or `-maa` shapes;
- treat those languages as sound palettes, not translation sources, and use
  ASCII only;
- avoid the stock English elf compounds `Silverglade`, `Moonspire`, and their
  near equivalents;
- the Land is **Ensimaa**;
- finite natural Areas:
  - **Tiravaine Forest** — deep central forest;
  - **Koivelle Wood** — old western woodland;
  - **Maelmor Hills** — forested northern hills;
  - **Avelune River** — river wood and crossings;
  - **Saimere Hollow** — low misty woodland;
- authored settlements:
  - **Taivelle** — capital;
  - **Dunmaelle** — western town;
  - **Kervaine** — river town;
  - **Ruunamont** — hill town;
- generated village name pool (one is built at world creation; the rest are
  the land's reserve):
  - Ailava;
  - Aurenne;
  - Briomaa;
  - Eilamere;
  - Fionava;
  - Halivain;
  - Kaelinne;
  - Liorenne;
  - Muirala;
  - Oirava;
  - Rosmaine;
  - Suvamere;
  - Tervaine;
  - Vaelora;
  - Yllenne.

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

- use short, open Polynesian-like syllables disturbed by worn-down simple
  English work words; this is an invented goblin sound, not a representation
  of Hawaiian or a claim of correct Pidgin;
- a source such as `market`, `port`, `boiler`, `brick`, `brass`, `stack`,
  `rivet`, or `yard` may survive faintly inside a name, but do not emit plain
  compounds such as `Irontown`, `Scrap Yard`, or `Boiler Works`;
- keep spelling direct, rhythmic, and ASCII;
- the Land is **Gibili**;
- finite natural Areas:
  - **Kapaliki Coast** — rocky coast and sea caves;
  - **Barasa Hills** — olive scrub and dry hills;
  - **Paina Valley** — pine valley;
  - **Wela River** — river plain;
  - **Satakalu Plain** — hot inland country;
- authored settlements:
  - **Maketawa** — capital;
  - **Potalu** — harbor town;
  - **Birikava** — inland town;
  - **Boilaki** — hill town;
- generated village name pool (one is built at world creation; the rest are
  the land's reserve):
  - Barasalo;
  - Bokapali;
  - Brikiki;
  - Kapalota;
  - Kikawa;
  - Kopaka;
  - Makelu;
  - Napaliki;
  - Pakapota;
  - Pikitawa;
  - Riveta;
  - Satakiki;
  - Tinkalo;
  - Wekapali;
  - Yadaka.

Orc:

- use a loose Mongol-Sumerian sound blend: hard `k`/`kh`/`g`, broad back
  vowels, compact roots, and occasional monumental compounds;
- treat both language families as sound palettes, not translation sources,
  and use ASCII only;
- avoid transparent warlike English compounds such as `Ironhold`,
  `Bone Camp`, and `Stormfang`;
- the Land is **Tergal**;
- finite natural Areas:
  - **Khuratal Steppe** — open central prairie;
  - **Borugal Hills** — broken northern hills;
  - **Temur Ridge** — high grazing range;
  - **Namak Basin** — dry southern basin;
  - **Kharun River** — eastern river plain;
  - **Flumenpur River** — the same river named in Firascir, crossing Caelum
    before entering western Tergal;
- authored settlements:
  - **Ulus-Gal** — capital;
  - **Kharuk** — western town;
  - **Temenur** — northern town;
  - **Ordubal** — southern town;
- generated village name pool (one is built at world creation; the rest are
  the land's reserve):
  - Aradun;
  - Balurun;
  - Borkal;
  - Enkhar;
  - Eshkar;
  - Guratai;
  - Kharnam;
  - Kurugan;
  - Namuruk;
  - Ordaki;
  - Sargul;
  - Teguren;
  - Tumengal;
  - Urkhal;
  - Zamutar.

Pirate:

- Black, Free, Storm, Knife, Gull, Rum, Red, Broken;
- harbor, key, cove, haven, hook, reef, port, rest.

Caelum should remain authored. The name strongly supports the city of angels
and devils; ordinary name generation should not produce near-copies.

## Worked forest chain

```text
WHITWELD FOREST — Area
  kind: natural
  subtype: forest
  environment: temperate
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

- none: ordinary Whitweld Forest;
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

## MVP implementation contract

This section resolves the choices a first code pass should not have to make.
Field names may be improved during implementation, but all information and
behavior below must survive any rename.

### Catalog split

Keep authored definitions separate from saved instances:

```text
ENVIRONMENT_PROFILES
LAND_SPECS
AREA_SPECS
SETTLEMENT_SITE_SPECS
NATURAL_SITE_SPECS
SITE_TEMPLATES
ROOM_CONTENT_POOLS
CULTURE_PROFILES
QUEST_PLACE_REQUIREMENTS
```

Definitions are immutable module data. The save contains only materialized
instances, selected definition IDs, local generated values, and mutable state.
Do not copy whole template definitions into every save record.

The concrete Land sections in this document are canonical input, not examples:
every named Area, required settlement Site, Room label, and ordinary natural
Site listed for the six MVP Lands must have a catalog entry.

Every Room definition carries either fixed `anchors` or a `content_pool` ID.
Resolve repeated role labels through aliases rather than copying pools:

- `PUBLIC HALL`, `THRONE HALL`, `GREAT HALL`, and `HILL COUNCIL` use the
  public-hall family;
- `COUNCIL ROOM` and `CONTRACT ROOM` use the council-room family;
- `RECORDS ROOM` and `MAP ROOM` use the records-room family;
- every tavern `COMMON ROOM`, `KITCHEN`, `CELLAR`, `GUEST ROOM`, and `STABLE`
  uses its shared pool;
- every `FORGE`, shop `SALES ROOM`, ordinary `STORE ROOM`, guard Room, gate,
  bridge, market row, landing, yard, and watch platform uses its shared or
  culture-specific family;
- a unique Room whose concrete catalog lists contents uses those lines as
  fixed anchors.

Add three generic fallback pools so no authored Room is empty:

`generic store`:

- shelves;
- crates;
- barrels;
- sacks;
- lamp;

`generic work room`:

- workbench;
- tool rack;
- water bucket;
- shelves;
- waste basket;

`generic yard`:

- packed ground;
- handcart;
- water barrel;
- stacked materials;
- covered shelter.

The catalog loader should fail loudly when a Room has neither anchors, an
explicit pool, a recognized alias, nor one of these intentional generic
fallbacks.

### Saved record minimums

`Land`:

```text
id
name
owner
culture
environment
seed
area IDs in stable authored order
neighbor Land IDs
```

`Area`:

```text
id
name
land ID
kind: natural | settlement
subtype
role
description
source
template ID
seed
known
visited
Site IDs in stable materialization order
quest IDs
tags
features
states
used natural-Site template IDs
```

`Site`:

```text
id
name
Area ID
domain: natural | built | mixed
template ID
description, optional
source
seed
known
visited
Room IDs in stable order
quest IDs
level, optional
tags
features
states
services
occupant NPC IDs
```

`Room`:

```text
id
name
Site ID
template or role ID
source
seed
known
visited
content records in stable order
features
states
occupant NPC IDs
encounter foe-kind list, when used by combat
```

Lightweight `content`:

```text
id
label
category
reveal: visible | search | hidden
known
state, optional
mechanical item reference, optional
```

A feature or state instance minimally stores its definition ID, reveal rule,
known flag, active flag, and any local value. If the first slice does not yet
use optional features, keep empty lists on the records so mutation and save
shape do not require another schema rewrite.

IDs use ASCII slugs and parent ownership:

```text
land/mortellaria
area/mortellaria/valdoro-hills
site/mortellaria/valdoro-hills/terraced-road/1
room/mortellaria/valdoro-hills/terraced-road/1/lower-turn
```

The exact prefix is not important; uniqueness, stable derivation, and readable
debug output are. Display names are never used as dictionary keys.

### Stable seed derivation

Use a deterministic digest such as SHA-256 or BLAKE2 over an ASCII payload:

```text
world seed | parent ID | purpose | sequence
```

Convert a fixed first portion of the digest to an integer for
`random.Random`. Never use Python `hash()`, call order in the campaign-wide
RNG, or the display name as the only seed input.

Every lazy operation first reserves a child sequence on its parent, derives a
seed, materializes the complete result, and saves it. A failed compatibility
roll does not consume an externally visible child: filter candidates first,
then choose.

### World creation

First-pass order:

1. Create the six `Land` records in authored order.
2. Create every finite natural and authored settlement `Area`.
3. Create Firascir's three fixed starting villages; for the other four
   village-bearing Lands, draw generated names without replacement and attach
   them to the Land's three village roles.
4. Add explicit Land adjacency and cross-Land river links.
5. Materialize required settlement Sites and Room skeletons.
6. Cast settlement NPCs and attach required services.
7. Post quests only after geography exists, so their targets can select it.
8. Save the resulting world. Reprinting it performs no generation.

MVP adjacency:

- Dvarvengrond <-> Firascir;
- Firascir <-> Mortellaria;
- Firascir <-> Ensimaa;
- Firascir <-> Tergal, through Caelum as a two-day route until Caelum exists;
- Gibili is reached by a sea route from Mortellaria;
- Mortellaria <-> Gibili is therefore a travel link, not a shared border.

Cross-Land water links:

- Stura River: Firascir -> Mortellaria -> sea;
- Flumenpur River: Firascir -> future Caelum -> Tergal.

Until Caelum is implemented, the Flumenpur travel route may be represented by
one named transit link with no visitable intermediate Area. Do not create a
placeholder Caelum settlement.

### Natural exploration

Discovering a natural Area:

- changes its existing record to `known`;
- records `discovered_day`;
- places it on the macro map;
- does not automatically reveal all Sites within it.

Exploring inside a known natural Area:

1. take the next unused ordinary Site template from that Area's seeded,
   shuffled three-template inventory;
2. materialize its full Room skeleton;
3. reveal the Site and its entrance/default Room;
4. mark the selected template used;
5. award exploration XP only for the new Site or Area, never for revisiting.

After all three ordinary templates are used, ordinary exploration may return
`nothing new` in the MVP. Quest and DM requests may still create compatible
Sites. Unlimited blind Site repetition is not required for the first pass.

### Settlement and house materialization

All required settlement Site and Room names in the concrete catalogs exist
from world creation. They begin known when the settlement is known, but Rooms
begin unvisited. Contents may be rolled at world creation or on first entry;
either path must use the Room seed and save the same result.

An ordinary house request:

1. generates or selects a resident of the settlement culture;
2. names the Site `<resident>'s House`;
3. creates `Main Room`;
4. selects zero to two distinct optional Rooms;
5. selects heating and furniture compatible with culture;
6. adds one to three ordinary contents, zero or one food, zero or one
   livelihood object, and zero or one personal object;
7. adds at most one non-visible object for the whole Site;
8. saves resident, Site, Rooms, and contents together.

An inhabited `Main Room` must end with two to five visible content records
after anchors are combined. Do not emit duplicate labels in one Room.

### MVP Area tags

Use these controlled tags for natural-Site selection and quest placement.
Settlement Areas also carry `settlement`, their tier, culture, and livelihood
role.

| Land | Area | Tags |
|---|---|---|
| Dvarvengrond | Drunurnar Mountains | mountains, hills, pass, mine, road |
| Dvarvengrond | Krokskogur Forest | forest, road, timber |
| Dvarvengrond | Lake Hornindal | lake, shore, ice, fishing |
| Firascir | Whitweld Forest | forest, road, timber, ruin |
| Firascir | Grendon Fields | farmland, pasture, hills, road |
| Firascir | Stura River | river, road, crossing, mill |
| Firascir | Flumenpur River | river, road, crossing, island |
| Mortellaria | Valdoro Hills | hills, vineyard, olive, road, pasture |
| Mortellaria | Orivela Coast | coast, road, cave, fishing |
| Mortellaria | Pinavera Valley | forest, hills, road, pasture |
| Mortellaria | Riomara Plain | farmland, river, wetland, road |
| Mortellaria | Stura River | river, road, crossing, mill |
| Ensimaa | Tiravaine Forest | forest, road, grove, warden |
| Ensimaa | Koivelle Wood | forest, road, timber, ruin |
| Ensimaa | Maelmor Hills | forest, hills, pasture, road, lookout |
| Ensimaa | Avelune River | forest, river, crossing, island |
| Ensimaa | Saimere Hollow | forest, wetland, mist, healer |
| Gibili | Kapaliki Coast | coast, road, cave, fishing, wreck |
| Gibili | Barasa Hills | hills, quarry, olive, road |
| Gibili | Paina Valley | forest, road, timber, spring |
| Gibili | Wela River | river, wetland, crossing, reed |
| Gibili | Satakalu Plain | prairie, road, clay, livestock |
| Tergal | Khuratal Steppe | prairie, road, pasture, hunt |
| Tergal | Borugal Hills | hills, pass, quarry, tomb |
| Tergal | Temur Ridge | hills, pasture, road, lookout |
| Tergal | Namak Basin | prairie, basin, road, salt, livestock |
| Tergal | Kharun River | river, crossing, fishing, willow |
| Tergal | Flumenpur River | river, road, crossing, trade |

Generated village roles add:

- Sturford: settlement, village, river, crossing, farmland;
- Ackham: settlement, village, forest, farmland, timber;
- Flurham: settlement, village, river, pond, fishing;
- vineyard village: settlement, village, vineyard, olive;
- river-plain village: settlement, village, river, farmland;
- coast-road village: settlement, village, coast, road, fishing;
- deep-forest village: settlement, village, forest, warden;
- elven river village: settlement, village, river, fishing, crossing;
- woodland-edge village: settlement, village, forest, farmland, timber;
- goblin coast village: settlement, village, coast, fishing, repair;
- goblin river village: settlement, village, river, reed, crossing;
- brick-country village: settlement, village, clay, industry, prairie;
- herd-road village: settlement, village, prairie, pasture, livestock;
- orc river village: settlement, village, river, fishing, crossing;
- orc basin village: settlement, village, basin, salt, livestock.

Authored settlement tags follow their stated functions: harbor, market,
industrial, mining, river, hill, or pasture. Store them explicitly in
`AREA_SPECS`; do not recover tags later by parsing descriptions or names.

### Quest placement requirements

Add a `place` requirement to quest templates. It contains:

```text
area_any: acceptable Area tags
site_template: preferred ordinary or quest-specific Site template
domain
reuse: prefer | allow | never
state_on_post, optional
state_on_complete, optional
```

MVP routing by existing quest family:

| Quest family | Acceptable target |
|---|---|
| Human bandits/deserters | road, farmland, pasture, coast-road, or rural settlement fringe |
| Human wolves | forest, hills, pasture, pine valley, or prairie edge |
| Human crypt | cemetery or temple Site in or beside a settlement |
| Human renegade wizards | ruined built Site on a road or settlement fringe |
| Elf grove/beasts/spiders | forest, woodland, hollow, or forested hills |
| Elf wardens | forest road or warden Site |
| Elf mist coven | hollow, forest river, or forested hills |
| Dwarf deep road/mine | mountains or a mining settlement |
| Dwarf lost hold/clan war | mountains, abandoned mine, gate, or settlement fringe |
| Goblin factory/machine/boiler | industrial Site in Maketawa, Birikava, Boilaki, or a brick-country village |
| Goblin night market/gang | settlement market, warehouse, tower, or yard |
| Goblin spiders below | cistern, cellar, quarry, or underground works |
| Orc hunt/warband/shamans | prairie, ridge, basin, herd road, or broken hills |
| Orc giants/dragon | Borugal Hills or Temur Ridge |
| Epic dragon | mountains, hills, or ridge |
| Epic giant | border road, ruined fort, hills, or pass |
| Epic wizard | ruined built Site or isolated tower |

The current Site stems remain valid player-facing names for quest-specific
Sites. Replace generic Room-stage names with concrete roles selected from the
Site template, but leave encounter budgets and foe pools unchanged.

Reuse rules:

- never attach two active quests to one Site unless a template explicitly
  allows it;
- prefer an existing compatible unused Site for roads, bridges, cemeteries,
  markets, mines, towers, and other public structures;
- create a fresh den, camp, hidden shrine, or temporary war camp when reuse
  would reveal it before the quest;
- quest completion changes state and knowledge; it does not delete the Site;
- a cleared quest Site remains available for later travel, inspection, DM use,
  or a compatible new state.

### Minimum mutation API

The first pass needs only small explicit operations:

```text
add_state(place, state_id)
replace_state(place, old_state_id, new_state_id)
clear_state(place, state_id)
reveal(place_or_fact)
```

Operations append a short world event with day, target ID, action, and state
IDs. The active record is the source for current display. The event list is a
history/debug surface, not a second state engine.

Required vertical-slice transition:

```text
Whitweld Forest: blighted -> recovering -> no adverse state
```

The quest may target a grove Site, but the state belongs to the Area when the
whole forest is described as blighted.

### Readouts

Player `map`:

- known Lands;
- known Areas beneath each Land;
- settlement job counts and current position;
- no hidden Sites or feature facts.

Player `look`:

- breadcrumb;
- place name and stored description;
- one salient active state or feature;
- known child Sites or Rooms;
- usable links and services;
- visible Room contents when at Room scope.

DM place readout:

- IDs and template/source;
- seed;
- all facets, features, states, and reveal flags;
- all children and links;
- occupant IDs;
- quest attachments;
- used Site-template inventory.

Display helpers wrap at 40 columns. Catalog strings remain ASCII. Stored
descriptions are sentence text; headings and tree indentation are composed by
the display layer.

### Minimum verification

Automated or reproducible checks must cover:

- exact natural-Area counts, and the opening settlement census (three a
  land) with the remainder waiting in the land's reserve;
- unique stable IDs and unique generated village names;
- same seed produces structurally identical world data;
- a different seed changes the opening draw, village assignment, and lazy
  Site order;
- save/load/re-entry does not change Sites, Rooms, contents, or fact reveal;
- discovering an Area reveals an existing record rather than adding one;
- each natural Area yields its three ordinary Sites without repetition;
- every required settlement service resolves to a Site or service record;
- house generation respects content counts and culture restrictions;
- every quest family finds at least one compatible target in a fresh world;
- quest posting and completion preserve the target Site and persist its state;
- no hidden fact appears in player readouts;
- every generated output string is ASCII and wraps to 40 columns;
- existing encounter-budget and career benches remain mechanically unchanged.

## Review-to-implementation workflow

The ordinary procedural-place MVP is implemented and verified. This workflow
now applies to later content expansion.

The six settled MVP Lands now have complete basic catalogs in this file.
Implementation can begin without producing four more translation worksheets.
`placegen_review.txt` remains useful as the historical Firascir wording sheet
and as a format for focused rewrites, but it is no longer a gate.

Further content work uses this loop:

1. Review a narrow environment, culture, or template pool when play exposes a
   wording or repetition problem.
2. Use `placegen_review.txt` only when a translation-style sheet makes that
   review easier.
3. Consolidate accepted changes into this canonical catalog.
4. Add the same catalog change to code once implementation exists.
5. Review Phase-2 special features after the ordinary vertical slice works;
   they do not block the MVP.

## Implementation handoff

Shipped on 2026-07-25:

- The six-settled-Land MVP content specification is complete.
- Dvarvengrond, Firascir, Mortellaria, Ensimaa, Gibili, and Tergal each have
  Land and Area descriptions, ordinary natural Site/Room layouts, settlement
  Site/Room skeletons, generated-village roles, and house livelihood content.
- The shared and culture-specific Room-content pools cover every required MVP
  Room role; specialized optional Sites may continue using the generic
  template drafts.
- `placegen_review.txt` remains the completed Firascir string sheet as the
  last dedicated review record. It need not be replaced before coding.
- The **MVP implementation contract** is realized by the checked-in catalog,
  materializer, quest routing, navigation commands, mutation API, and
  `test_places.py`.
- No special/nonessential feature pool has been accepted yet. Existing
  optional-feature and curiosity lists remain post-MVP candidates.

The shipped feature provides:

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

Shipped mechanics and behavior now live in `rules.md`; the completed track was
removed from `plan.md`. Further work here is a content expansion, beginning
with review of special features only when play exposes a need.

## Implemented order (historical)

1. Add catalog data structures and stable seed derivation.
2. Split Land identity from race/culture; load environment profiles and the
   finite six-Land Area inventory.
3. Materialize settlement Site/Room skeletons and required services.
4. Replace unlimited natural-Area creation with discovery of existing Areas
   followed by the three-entry lazy natural-Site inventory.
5. Add lightweight Room contents and the ordinary-house generator.
6. Add player `look` and DM fact readouts; update the macro/local map surface.
7. Route quests through `QUEST_PLACE_REQUIREMENTS`, replacing generic Room
   stages without changing encounter budgets.
8. Add reveal and minimum state-mutation operations.
9. Verify the Firascir vertical slice, then load all remaining MVP catalogs.
10. Add the optional weighted-feature selector and 50/30/15/5 distribution
    when the first special-feature pool is accepted.
11. Add cathedral and other optional specialized templates after the ordinary
    path is stable.

The verified Firascir vertical slice contains:

- one capital;
- one town;
- one village or hamlet;
- farmland;
- pasture or hills;
- Whitweld Forest;
- generated ordinary Sites in the forest;
- one generated ordinary house with persistent Rooms and visible contents;
- one quest which discovers and changes a forest state.

This is enough to test inheritance, names, reveal levels, quest placement,
mutation, persistence, and DM output before loading the other five settled
catalogs. The forest state may be assigned directly by the test quest; the
optional-feature weighting pass is not required.

## Post-MVP content review questions

During later content expansion, review the draft for:

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
