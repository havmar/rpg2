# The Gates — Heaven & Hell design reference (2026-09-12)

This is the spec companion for THE GATES ARC: the setting, the content
tables and the mechanical decisions the arc's build sessions draw from.
It is written like `worldsim.md` was: a section is CUT when the session
that builds it lands, its played rules go to `rules.md`, its table manner
to `dm.md`, its code pointers to `develop.md`, and what remains here is
what remains to build. `plan.md` carries the session contracts and points
here; this file carries the content.

Everything in this file is decided. Where the designer delegated a call,
the call is made and marked **[decided]** so the build session does not
reopen it. Where a build session must settle something the design cannot
(a number that wants a bench, a name that wants the map), it is marked
**[build settles]**.

The standing habits of the earlier arcs apply throughout: **hidden
numbers, visible words**; **author the physical, derive the human**;
**keep lore local and actionable** (writing.md — a proper noun earns its
place by changing what is here or what can be done now).

---

## 0. Directives recorded in this design (2026-09-11/12)

Written down so they stay settled:

- **The pact is a gimmick and this arc ignores it.** The Hell contract,
  the pinned assignments, the collections enforcement and the WORD FROM
  BELOW machinery were built as an excuse to carry the crime content.
  They stay in the game for now, they are not removed, and **nothing in
  this arc has to fit them**. The pact's text in rules.md ("an evil god",
  "the gods of Light") is the old frame; this file's setting is the new
  one and wins wherever they disagree. A later sitting decides whether
  the pact is rewritten onto this setting or cut.
- **Sulfur is one idea, not a pillar.** The parked sulfur-to-Hell card
  may ride Hell's packet as one import line; it carries nothing.
- **The low-band-only principle is set aside for this arc.** `new` rolls
  the start level 1–18, so high-level characters exist and the world has
  to hold content for them. Ruin outer sites are low, ruin depths and
  city politics are high, and every table below spans the ladder.
- **Four one-tile city states, semi-random placement, conquest later.**
  The two live gate cities are countries of exactly one tile. They may
  take land in a later arc (the conquest system is the ground for it);
  nothing here builds that.
- **Hell is north and pagan-coded; Heaven is south and church-coded.**
  Hell's ruin and Hell's city both roll in the northern set of countries;
  Heaven's both in the southern set. The pagan coding is taken all the
  way (section 3).
- **One tongue, two registers.** No Norse or Tergal sound anywhere near
  Hell. Both powers' names come from one language family: Hebrew-shaped
  person names, Latin-shaped places for Heaven, older Italic-shaped
  places for Hell.

---

> **Sections 1-3, 5, the ruin half of 6, 7 and 8 are CUT** (2026-09-12,
> session 1 shipped). Where they went: the setting (the timeline, the two
> powers and their axes, the pagan coding, the stranded, the tongue) and
> the sites, the rings, the ruins-as-dungeons, `delve` and the foe tables
> are **rules.md's `Heaven & Hell - Add-on, part 1`**; the table manner is
> **dm.md's "The gates"**; the two name-sound rows and the
> one-tongue-two-registers note are **writing.md's "The nine name sounds"**;
> the code pointers are **develop.md's dev map**, the placement numbers
> **benchlog.md's 2026-09-12 entry**, and the build record (with every
> [build settles] call) **designlog.md's 2026-09-12 (A)**. Section 4 (Tom)
> is kept whole because session 2 builds the two bars and Tom's stone out
> of it. What remains below is sessions 2-5.


## 4. Tom

The mythical figure who closed both gates. The name stays **Tom**: one
plain syllable, and the writing guide's whole argument.

What is known, which is the only thing the game asserts: 1027 years ago a
person called Tom barred both gates in the same season, and both cities
died. Everything past that is a version:

| who | their Tom |
|---|---|
| the Sun communion | Saint Tom, who shut out the enemy and founded the Church's year |
| Thule's grove | Tom the Smith, who forged the bar |
| Tergal's shamans | Tom who sewed the sky shut |
| Heaven (the Pruners) | a criminal who cut the world off from the Law |
| Heaven (the Gardeners) | a mistake, best not repeated |
| Hell (the Feast) | a hero: he freed both worlds of each other |
| Hell (the Hunger) | a thief who stole a thousand years of feasting |

**Deliberately open**: whether Tom was human, half-blood, angel or demon;
whether Tom is alive. The design keeps one hook only: **only a
half-blood could have touched both gates**, so both powers believe the
old-blood lines are Tom's people, and act on it.

Where Tom exists in the game (keep lore local and actionable):

- **Tom's stone**: a shrine site type in the western and southern
  natural inventories (the pilgrim's stop, a burial and blessing sold at
  it like at any shrine).
- **The two bars**: one relic per ruin, at the bottom of each — the
  bar Tom set across that gate, still there, still holding the OLD gate
  shut. The relic is a heavy-arms weapon with an authored name (`the
  Candor bar`, `the Libera bar`), the two most notable pieces of loot in
  the game, and nothing else: no quest hangs on them yet, and the design
  does NOT say what one would do to a live gate. That is the arc's
  endgame question and stays open on purpose.
- **One fact line per culture** on the lore page (the table above, in
  the culture's own words).

## 6. The gate layer: the CITY half (session 4)

Session 1 shipped `places.roll_gates(world)` -- the roll, `world["gates"]`,
all four rings, the tile tags and the two ruins (see rules.md's Heaven &
Hell add-on and develop.md's dev map for what exists). What it
deliberately did NOT do is the city tiles' TAKEOVER. The city tiles today
are ordinary tiles of their countries wearing a ring, two tags, a record
entry and the map glyph `G`. This is what session 4 adds on top.

**The takeover.** For each **city** in `world["gates"]`: `tile["country"]`
re-homed to the city state; the tile moved from the donor land's `tiles`
list to the city state's; the land record's `capital_tile` set (see the
validator note); the census then seats the city (below). `cut_from` on the
record already names the donor.

**The census and the city.** `roll_census` treats a gate-city tile like
an authored historical tile: ONE slot, tier `city`, `name` the authored
city name, `capital=True`, `authored=True`, `charter="free"`, no
companions (`SLOT_CAP` does not apply: a one-tile state is its city and
nothing else). The city's settlement template is the culture's
`gate_city` template (section 10). The city is `known=True` from day one,
like every authored city: everyone has heard of Concordia.

**The validators.** Three of today's checks assume the nine and must be
taught the gates, and the fix is one shape:

- `_validate_fixed_data` keeps checking the AUTHORED overlay against the
  pinned nine-country censuses exactly as now (it runs before the gate
  layer; the map file has not changed).
- `_validate_countries` (world level) compares each of the nine against
  its pinned biome and band counts **minus the tile it ceded**, read off
  `world["gates"]`, and checks the two city states hold exactly one tile
  each, of the right set.
- **The capital tile becomes a per-world land fact.** `CAPITAL_TILES` is
  a module constant today, consumed by `worldsim.capital_tile` for the
  sky read AND by `places.gate_candidates` for the no-capital clause. It
  becomes `land["capital_tile"]`, set for the nine from
  `HISTORICAL_CITIES` and for the two from the roll; `worldsim.capital_tile`
  reads the land record. The "nine capitals named explicitly" check in
  `_validate_fixed_data` stays about the nine.
- `quests.generate_world`'s `capital = next(s for s in setts if
  s.get("capital"))` works unchanged once the city slot is `capital`.
- `places._validate_gates` (session 1's clause) will need its city half
  widened the same way: it checks the placement rule, and after the
  takeover a city tile's `country` is no longer its `cut_from`.

**Homelands.** `people.HOMELANDS` (the birth roll for the PC, companions
and recruits) becomes `HUMAN_HOMELANDS`: the nine. Nobody is *born* in
Concordia or Saturna in the roll; the city states' name pools serve the
NPCs cast at their counters (the smith in Concordia is an angel, and
`cast_service_providers` casts from the country's pool as it does
everywhere). `RULER_TITLES` gains `concordia: prefect/prefect` and
`saturna: lord of misrule/lady of misrule`; `conquest.DEFENDER_ROLES`
gains `warden of the gate` and `master of hounds`.

**Name reserves.** `SETTLEMENT_NAMES` requires four non-empty tiers per
country; a city state seats exactly one settlement, so its validator
clause relaxes to "every tier the country can seat", and each city state
authors one `city` name and nothing else. [decided: relax the clause,
don't author districts nobody will see.]


## 9. The two sentinels (the bosses)

rules.md's doctrine says the tier above the dragon is authored one-offs
on the Heroes table, never catalog rows. Nothing implements it. This arc
builds the factory, small:

- `sites.BOSSES` — a second table beside `FOES`, same `FoeSpec` shape,
  read by `make_foe` when the kind is not in `FOES`. Never in any pool,
  never in the bench's row loop; spawned only where a Site's authored
  roster names the key.
- Both bodies are the Legend row (DEX 8, STR 8, STA 8, HP 20) with the
  "no mortal tradeoffs" reading: `pain=3`, `spell_ward=2`, `crowd_cap=3`,
  `training=3` (`drilled +3`), `power=12`, `tireless=True`, `ref_pack=1`.
  Heaven's is `FEROCITY_RELENTLESS`; Hell's is `FEROCITY_TAKES_SPOILS`
  (even at the bottom of Libera, the Old Host lets you crawl out).
- **The Sentinel of Candor** (`sentinel of candor`, display "Zohariel the
  Sentinel"): a stranded angel who never left its post. School `ice`,
  rank 2 (the Voice of Measure), sweep 1. Level annotation target **17**.
- **The Old Host of Libera** (`old host of libera`, display "Saar the Old
  Host"): a stranded demon who kept the feast going alone. School
  `fire`, rank 2, `inflicts="burn"`, sweep 2 with `sweep_cost_power=3`
  (the fueled sweep, as the drake). Level annotation target **16**.
- **Each wields its bar.** `the Candor bar` and `the Libera bar` are
  legendary heavy-arms weapons (chassis a two-hander; sp 9 [build
  settles the exact spend with `generate_weapon(rng, 9, chassis, name)`
  off the world seed]), and both are entered in the world's armory
  (`weapons.roll_armory`) as fixed entries with the boss as owner and
  the deepest site as `where`. The armory is the game's existing "famous
  weapons with owners and resting places" record; the bars are its two
  most famous pieces and the arc's endgame loot.
- **Bench.** `bench_bestiary.py` gains a `--bosses` pass that annotates
  the two at the duo baseline like any row; the targets are 17 and 16,
  and the bodies are tuned to land there (`hp`, `training`, `pain` in
  that order). Numbers to benchlog.

## 10. The two city states (the catalog)

`place_catalog.json` goes to version 4. Two new `lands` and two new
`cultures`:

```
"lands": {
  "concordia": {"name": "Concordia", "culture": "heaven", "tongue": "Latin",
                "rolled": true, "side": "heaven",
                "description": "Heaven's gate city, 27 years old: white walls on a plain, a gate in the middle of it, a Prefect over it."},
  "saturna":   {"name": "Saturna", "culture": "hell", "tongue": "Old Tongue",
                "rolled": true, "side": "hell",
                "description": "Hell's gate city, 27 years old: a wooden town round a hollow, a feast every week, a Lord of Misrule for a year and a day."}}
```

`rolled` is the flag the map layer reads (no overlay letter, tile from
the roll); `side` is what the skins, pools and rings read.

Each culture record carries `natural` (unused: a one-tile state's natural
Area is the tile's own ground and keeps the DONOR culture's inventory —
Concordia's countryside is still Seraptanian fields), `natural_sites`
(empty), and ONE settlement template, `gate_city`:

- **Concordia's**: tier `city`, tags `(capital, city, market, walls, road,
  gate-city, heaven-city)`, sites: THE GATE (the standing crossing;
  rooms: the approach, the ring, the gate), THE PREFECTURE (court, cells,
  archive), THE INFIRMARY (the ward, the dispensary), THE SCHOOL OF
  MEASURES (the hall, the library), THE MARKET OF LAMPS, THE CHOIR.
- **Saturna's**: tier `city`, tags `(capital, city, market, gate-city,
  hell-city)`, sites: THE GATE (the descent, the ring, the gate), THE
  FEAST-HALL (the long table, the kitchens, the cellar), THE KENNELS
  (the runs, the master's house), THE FIRE SCHOOL (the forge hall, the
  still-room), THE WILD MARKET (the stalls, the cages, the counting
  house), THE DEBT-HOUSE (where oaths are written and the year is owed).

Both cities post work: the city is `capital`, so its board draws its
culture's quest table plus `EPIC_TEMPLATES`, five ordinary slots, the
whole ladder. Its jobs land within three days' road — in the human
countryside around it. That is how a city state is FELT before the
player ever walks in.

**Prices.** The `gate_city` template's priced menu: Concordia `healer`
×0.6 and `lodging` ×0.8 (clean beds, the cure), `goods` ×1.2; Saturna
`lodging` ×0.5 (a bed is a place at the feast), `goods` ×0.9, `healer`
×1.3 (nobody in Saturna is in a hurry to heal you). Ordinary menu terms;
the band and states multiply over them as everywhere.

## 11. The world layer: two packets

Everything the validator demands (worldsim.py `_validate_countries`): four
constitutions at 6/2/1/1, at least two rollable tensions with their
factions, faction edges between blocs some tension names, at least one
card per land on each of the three tracks (`crisis`, `weather`,
`season`), at least one standing fact, at least one relation edge, a
capital tile. Both packets are authored under their CULTURE key
(`heaven`, `hell`), the Thule precedent.

### Heaven (`heaven`, worn by `concordia`)

**Constitutions:** THE HIERARCHY (6, "ranks all the way up; the Prefect
answers to the gate"), THE MISSION (2, "the Gardeners hold the city; the
school and the infirmary come first"), THE QUARANTINE (1, "the Pruners
hold the city; the gate is guarded from both sides"), THE COUNCIL OF
CHOIRS (1, "the choirs vote; the Prefect counts").

**Tensions (factions):** `gardeners-vs-pruners` (gardeners, pruners) —
the inner axis, standing; `prefect-vs-church` (prefect, bishops) — the
host's church against the Prefect; `angels-vs-converts` (angels,
converts) — the humans of the city against the people of the gate.

**Faction edges (six):** pruners `list` converts ("the register names
every half-blood in the city"); gardeners `heal` converts; bishops
`preach-against` angels; prefect `tax` converts; angels `judge`
converts; converts `petition` prefect.

**Facts (six, ASCII-uppercase titles):** THE GATE ("it stands in the
middle of the city and it is open; things come through it that nobody
here made"); THE LAMPS ("the lamps of Concordia burn without oil; one is
worth a horse outside the walls"); THE REGISTER ("the Pruners keep a list
of every half-blood born in the last 27 years; nobody outside the city
has seen it"); THE CURE ("the infirmary heals what the temples cannot,
and charges for it"); THE MARBLE SERVANTS ("stone that walks and carries;
the city's labour, made not born"); SAINT TOM ("the Church's saint closed
this gate's elder a thousand years ago; the city does not say the name").

**Options (two):** `heaven/choir-blessing` — does `bless`, term `healer`,
silver 40, word `choir`, line "a choir sings the rite of order over the
party; every companion is steadier for it"; `heaven/school-of-measures`
— does `book`, term `goods`, silver 120, word `measures`, line "the
school teaches the ice school's first diagrams to anyone with the gift".

**Cards (crisis track, eight):**

| key | name | admits | outlets, in one line |
|---|---|---|---|
| heaven/the-register | The register is read | tension gardeners-vs-pruners | state set `register-read`; news: the Pruners post a list of half-bloods in the host country; encounter road: wardens asking questions |
| heaven/the-removal | A child is taken | states register-read | clear `register-read`, while `removal`; quest "Bring the Child Home" (good) or "Deliver the Child" (dark), posted at the host's nearest town; the child is named once and kept (an authority hook, `nephilim-child`) |
| heaven/the-cure-line | The infirmary opens to all | tension gardeners-vs-pruners | menu healer ×0.5 in the host land while it stands; news |
| heaven/the-gate-guarded | The gate is guarded from both sides | constitution QUARANTINE or tension prefect-vs-church | while `gate-shut`; menu healer ×1.5, goods ×1.3; encounter road: wardens turning travellers back |
| heaven/a-stranded-one | A stranded angel is found | any | news: a hermit in the host's hills is an angel a thousand years native; authority hook `stranded-angel`; quest "The Hermit's Escort" (good) — the Pruners want the hermit brought in, the Gardeners want the hermit left alone |
| heaven/the-lamp-thieves | Lamps are stolen | wealth normal or better | quest "The Lamp Thieves" over the ladder pool; state marks: the stolen relic reaches burglary and the con |
| heaven/the-sermon | The bishop preaches against the gate | tension prefect-vs-church | while `preached-against`; encounter wilds: pilgrims with staves; the synod question is asked (a link for the church card below) |
| heaven/the-servant-loose | A marble servant walks off | any | quest "The Servant That Walks" (constructs pool, one place); news |

**Weather track (one):** `heaven/clear-sky` — "The sky over Concordia is
clear" — the Prefect's own sky, `sky=` the weather layer's clear word
[build settles], chance 0.4, days 3–6; it
is the one thing Heaven does to the weather and it is small.

**Season track (one):** `heaven/the-choir-season` — the choir sings the
year in; a blessing is cheaper (menu healer ×0.8) for the season.

### Hell (`hell`, worn by `saturna`)

**Constitutions:** THE FEAST (6, "a Lord of Misrule for a year and a
day, elected at the long table"), THE FREE COMPANIES (2, "no lord; the
captains hold the city between them"), THE LONG FEAST (1, "the Lord of
Misrule did not step down; the Hunger holds the city"), THE KENNEL (1,
"the Master of Hounds rules; the feast is for the hounds").

**Tensions (factions):** `feast-vs-hunger` (feast, hunger) — the inner
axis, standing; `lord-vs-captains` (lord, captains); `demons-vs-debtors`
(demons, debtors) — the humans who owe a year against the people they
owe it to.

**Faction edges (six):** hunger `own` debtors ("a year of a man's life,
written in the debt-house"); feast `free` debtors; captains `raid`
debtors; lord `pardon` debtors; demons `bargain` debtors; debtors
`petition` lord.

**Facts (six):** THE GATE ("it is a hollow in the middle of the town, and
the town sits round it like a feast round a fire"); THE YEAR ("every
bargain in Saturna is paid in time: a year of your life, owed, written
and collected"); THE FEAST ("once a week the town eats and drinks
everything it has; strangers eat free"); THE HOUNDS ("hell hounds are
bred here and sold; the kennels are the richest house in the town");
THE WILD MARKET ("cages and stalls; things for sale that are alive");
TOM THE THIEF ("the Hunger says Tom stole a thousand years of feasting;
the Feast drinks to him").

**Options (two):** `hell/the-feast` — does `bless`, term `lodging`,
silver 25, word `feast`, line "a place at the long table; the party eats,
drinks and sings until morning; every companion is the better for it";
`hell/the-fire-school` — does `book`, term `goods`, silver 120, word
`fire`, line "the forge hall teaches the fire school's first diagrams to
anyone with the gift".

**Cards (crisis track, eight):**

| key | name | admits | outlets, in one line |
|---|---|---|---|
| hell/the-feast-spills | The feast spills over the wall | tension feast-vs-hunger | state set `feast-spilled`; news: the host's nearest villages are drunk and unfenced; menu lodging ×0.6 in the host land; encounter wilds: revelers |
| hell/the-debt-book | The debt-house collects | states feast-spilled | clear `feast-spilled`, while `year-owed`; quest "The Year Owed" — a village has sold a year and wants it back (good: burn the book; dark: collect it); the debtor named once and kept (`hell-debtor`) |
| hell/the-lord-hanged | The free company hangs a lord | tension lord-vs-captains | while `lord-hanged`; quest "The Lord's Men" (ladder) posted at the host's capital; the host's relation edge reads it |
| hell/the-kennels-open | Hounds get loose | any | quest "Hounds off the Road" (wolves pool, skins hounds); encounter road: hounds |
| hell/a-stranded-one | A stranded demon is found | any | news: an old woman in a fen village has run the same feast for forty generations; authority hook `stranded-demon`; quest "The Old Feast" (good: leave her be, dark: bring her in for the Hunger) |
| hell/the-cages | The wild market sells people | tension feast-vs-hunger, constitution LONG FEAST or KENNEL | while `cages-open`; state marks: reaches the smuggling and the con; quest "Open the Cages" (good) |
| hell/the-election | The feast elects a Lord of Misrule | any, days 3–5 | news; succession `disputed` cleared; encounter road: the new lord's revelers |
| hell/the-horned-ones | The grove knows its own | states hosts-hell AND the host is Thule or Tergal (a `pagan-host` standing state stamped at worldgen) | news: the host's old-god people walk to Saturna; menu goods ×0.9; encounter wilds: pilgrims of the grove |

**Weather track (one):** `hell/feast-fires` — "The feast-fires are lit;
the sky is red over Saturna" — `sky=` the same clear word [build settles], chance 0.4, days
1–2; smoke that is no weather at all, the sky's one Hell line.

**Season track (one):** `hell/the-wild-season` — the hunt is on; hounds
are cheap and the road is loud (menu goods ×0.9; encounter road: hunters
and hounds).

### The states, and their prices

New state words in `STATE_WORDS` (id → readout phrase): `register-read`
("the Pruners' list is out"), `removal` ("a child was taken"),
`gate-shut` ("the gate is guarded from both sides"), `preached-against`
("the pulpit is against the gate"), `feast-spilled` ("the feast has
spilled over the wall"), `year-owed` ("a village owes a year"),
`lord-hanged` ("the free company hanged a lord"), `cages-open` ("the wild
market is selling people"), and the four standing ones stamped at
worldgen: `hosts-heaven`, `hosts-hell` (on the two donor/host lands),
`keeps-candor`, `keeps-libera` (on the two ruins' keeper lands), and
`pagan-host` (on Hell's host when it is Thule or Tergal).

`STATE_MENU` rows: `gate-shut` healer ×1.5 goods ×1.3; `feast-spilled`
lodging ×0.6; `year-owed` lodging ×1.2; `hosts-heaven` healer ×0.9
(the cure leaks out); `hosts-hell` lodging ×0.9 (so does the feast).
`STATE_ENCOUNTERS` rows for `gate-shut`, `feast-spilled`, `lord-hanged`.

### The relations rows (four, one per site)

| from | link | to | when | then | because |
|---|---|---|---|---|---|
| concordia | the cure | its host (`cut_from`) | gate-shut, removal | `cure-dear` (healer ×1.3) | "the infirmary's doors" |
| saturna | the feast | its host | feast-spilled, cages-open | `feast-abroad` (lodging ×0.7; encounter wilds: revelers) | "what spills over Saturna's wall" |
| the host of Heaven | the bishops | concordia | interdict, preached-against | `pulpit-against` | "the host's pulpit" |
| the host of Hell | the hunt | saturna | hunt-up, at-war | `hounds-out` (encounter road: hounds) | "the host's men on the road" |

The relation ends are world-specific (`cut_from` is rolled), so the
table is authored with a `HOST` placeholder that `open_world` resolves
off `world["gates"]` when it builds `RELATIONS` for the world. [decided:
resolve at open_world, not at import; the validator's reachability pass
runs on the resolved table.] Every derived word reaches a price.

### The human side

- **The synod question**: one card in both Byzantium's and Seraptania's
  decks, `southern/the-return-question` — "The synod asks what came back"
  — admits `schism-near`; news names the two answers (the hosting rite's
  "the god's own country has come back" against the other's "an invasion
  wearing the god's face"); `while: return-argued`; it is the one insult
  that does not split the church either, by the standing rule.
- **Per-culture fact lines** (four, on every land of the culture): the
  western church's Saint Tom and the Return; the southern rite's; Thule's
  Tom the Smith and the horned ones; Tergal's Tom who sewed the sky.
- **Host-specific facts** (stamped at worldgen from `world["gates"]`,
  four lines): "THE GATE CITY: Concordia stands on land that was ours 27
  years ago" on Heaven's host; the same for Hell's host; "THE WHITE RUIN"
  on Candor's keeper; "THE WILD RUIN" on Libera's keeper.
- **The crusade tension**: where Hell's host is a Sun-communion land
  (Phyrascia, Teutonia, Vellisclavia), the host gains the standing
  tension `church-vs-saturna` (bishops, saturna) and one card,
  `western/the-preaching-crusade` — "The bishop preaches a crusade
  against the feast" — while `crusade-preached`; encounter road:
  pilgrims with staves. The standing wars are NOT rolled over the city
  states (section 0): the crusade is a card, not a war, until conquest
  comes.
- **The pact text.** rules.md's Hell Pact section gains one line at its
  head pointing at the Heaven & Hell add-on as the setting authority and
  noting the pact is kept as-is; no other line of it changes.

## 12. The Nephilim

A per-character fact, not a sketch trait: `Entity.blood: str = ""`,
values `""`, `old`, `sky`, `fire`. It rides the save for free (the Entity
dataclass round-trips), prints on the sheet, and is read by
`rpg.make_human` through floors and ceilings.

**Who has it [decided]:**

- **The PC** rolls it in `cmd_new` on a d6: 1–3 none, 4 `old`, 5 `sky`,
  6 `fire`. `new --blood none|old|sky|fire` fixes it, beside `--level`.
  Half of all PCs are Nephilim; that is what "an important part of the
  setting" means at the table.
- **Companions and recruits**: `old` 1 in 12, `sky` and `fire` 1 in 24
  each, rolled in `make_character`.
- **NPC dicts** carry none. The named Nephilim of the world (the child,
  the debtor) are the packets' authority hooks.

**What it does [decided], one line each, all through `make_human`'s
floors and ceilings and two Entity fields:**

| blood | body | the other thing | the marker (sheet line) |
|---|---|---|---|
| old | `mind` floor +1 (the gift is BORN — the wild talents of the world are old blood without the word) | — | "eyes that catch the light" / "taller than the door" |
| sky | `dex` floor +1 | `spell_ward` 1 (the Law in the blood: +2 to any possession DC) | "gold in the eyes; the hair does not grey" |
| fire | `str` floor +1 | max `power` +2; `Old Tongue` added to `tongues` | "small horns under the hair; warm to the touch" |

Sheet line: `BLOOD: fire-born (small horns under the hair)`; nothing when
none. `people.person_line` and `character_sheet` print it; `TRAIT_NOTES`
gets the three mechanics notes.

**How the world reacts** is table protocol plus the packets, not an
engine gate (cards and prices cannot read the party): dm.md's Nephilim
paragraph says that a warden asks a sky-born for the register, a demon
greets a fire-born as kin and charges double, a bishop looks twice at
either, and the Pruners' and the Hunger's cards are ABOUT people like the
PC. The named-child and named-debtor hooks are the same three-employers
shape as the wild talent.

## 13. Sessions

Five build sessions, in an order forced by what boots. Each is one
contract in plan.md pointing here; each ends with the standard paperwork
(rules.md add-on, dm.md, develop.md, benchlog, designlog, the plan entry
deleted, the section here CUT).

**Session 1, the four sites on the map, SHIPPED 2026-09-12** (designlog
2026-09-12 (A)); its sections are cut from this file. Four remain.

| # | session | ships | this file's sections |
|---|---|---|---|
| 2 | **The two sentinels and the ruin jobs** | `sites.BOSSES`, `make_foe` reading it, the two bosses, the two bars in the armory, bench_bestiary's `--bosses` pass, the ruin quest templates on every culture's table (section 9's templates, `QUEST_PLACE_REQUIREMENTS` rows on `gate-ruin`), Tom's stone site | 4 (the relics), 9, the templates of section 14 |
| 3 | **The Nephilim** | `Entity.blood`, the rolls, `--blood`, the floors and the two fields, the sheet line, `TRAIT_NOTES`, dm.md's Nephilim paragraph, `test_start` coverage | 12 |
| 4 | **The two city states** | catalog v4, the city half of `roll_gates` (tile takeover, census, capital_tile as a land fact, the validators), name pools, `RULER_TITLES`/`DEFENDER_ROLES`, `HUMAN_HOMELANDS`, the `gate_city` templates and their menus, the two culture quest tables (section 14), a STUB packet each (the validator's minimum: four constitutions, two tensions, one card a track, one fact, one relation) | 6 (the city half), 10, the minimum of 11 |
| 5 | **The packets and the human side** | the full two packets, the state words, menus and encounters, the HOST-resolved relations, the synod card, the four culture facts, the host facts, the crusade tension and card, the pact pointer line, the lore pages | 11 in full |

Session 1 was the biggest and is what made the arc PLAYABLE: a new world
now has two ruins to walk into at any level. Sessions
2 and 3 are additive and small. Session 4 is the one that touches
validators and the country machinery and must leave the world booting
with eleven lands; its packet stubs exist only so the validator passes,
and session 5 replaces them.

## 14. The quest templates

Authored in writing.md's register (a problem already happening, who
wants it changed, a visible objective, at most one complication). `pool`
sets the band; `sites` name the ruin Sites by stem so `reuse: "prefer"`
lands the job in the authored place.

**Into the ruins (every culture's table; placement `area_any:
("gate-ruin",)`, `domain: "natural"` widened to admit kind `ruin`):**

- **Looters in the White Ruin** — pool LADDER_POOL[:5], skins {}, sites
  ("the outer terraces",), giver "the sheriff", desc "Looters are
  stripping the white stone off Candor's terraces and selling it. Clear
  them out.", epilogue "The terraces are quiet. The stone stays where
  Tom left it."
- **The Servant That Walks** — pool HEAVEN_RUIN_POOL[:3] (the small
  constructs), skins heaven, sites ("the choir hall",), giver "the
  village priest", desc "A marble servant has walked out of Candor and is
  standing in the churchyard. It does not answer. Break it or lead it
  home.", epilogue "The servant is broken. The priest keeps a hand of it
  on the altar."
- **The Lamp in the Glass Garden** — pool HEAVEN_RUIN_POOL, skins heaven,
  sites ("the glass garden",), giver "a lamp merchant", proof "the lamp",
  desc "A lamp still burns in Candor's glass garden. The merchant pays
  for it. The wardens of the garden are still there too.", epilogue "The
  lamp burns on the merchant's counter. He is not selling."
- **The Register of Candor** — pool HEAVEN_RUIN_POOL + ("champion",),
  skins heaven, sites ("the measuring house",), giver "an archivist from
  Concordia", align good, desc "Concordia wants the old register out of
  Candor's measuring house. The porters in there have kept it for a
  thousand years.", epilogue "The register goes to Concordia. Somebody
  there is reading the names."
- **Hounds off the Wild Ruin** — pool WOLF_POOL, skins hell, sites ("the
  fallen feast-hall",), giver "the head shepherd", proof "the collars",
  desc "Hell hounds are coming out of Libera's feast-hall and taking
  sheep. Kill the pack and bring back the collars.", epilogue "The
  collars hang on the shepherd's door. The sheep are back on the hill."
- **The Vine Pits** — pool BEAST_POOL + ("dire wolf",), skins hell, sites
  ("the vine pits",), giver "the vintner", desc "The old vine pits at
  Libera are still bearing. The vintner wants the vintage. The boars
  want it too.", epilogue "Twelve barrels of a thousand-year vintage. The
  vintner will not say what it tastes like."
- **The Kennel Master's House** — pool HELL_RUIN_POOL, skins hell, sites
  ("the kennels",), giver "the Master of Hounds of Saturna", align dark,
  desc "Saturna wants the old kennel book out of Libera. The black hounds
  and the ember troll in the kennels are not selling.", epilogue "The
  kennel book goes to Saturna. The hounds there are bred from it now."
- **The Debt of a Thousand Years** — pool HELL_RUIN_POOL + ("champion",),
  skins hell, sites ("the wild market",), giver "a debtor from Saturna",
  desc "A man from Saturna says his year is written in Libera's old
  counting house and can be burned there. The horned brutes keep the
  house.", epilogue "The book is burned. The man walks out a year
  younger, or says he does."

**Concordia's table (culture `heaven`):**

- **Escort the Healers** — LADDER_POOL[:4], skins {}, sites ("the
  road",), giver "the infirmary's warden", desc "Two healers walk to the
  villages every week. Raiders have taken to walking with them. Walk
  with them instead.", epilogue "The healers make their rounds. The
  raiders do not."
- **The Lamp Thieves** — LADDER_POOL[:5], sites ("the thieves' camp",),
  giver "the Market of Lamps", proof "the lamps", desc "Six lamps of
  Concordia were stolen off a cart. Bring them back. The thieves are
  camped in the hills and the lamps show at night.", epilogue "Six lamps
  back on the counter. The hills are dark again."
- **Bring the Child Home** — LADDER_POOL[:5] + ("soldier",), skins
  heaven, sites ("the warden's post",), giver "a mother from the host
  village", align good, desc "The Pruners took a child off the register
  to Concordia. The mother wants the child back. The wardens at the post
  will not hand it over.", epilogue "The child is home. The register has
  one name crossed out and nobody in Concordia says by whom."
- **The Prefect's Levy** (EPIC, capital only) — LADDER_POOL, skins heaven,
  sites ("the muster field", "the raiders' hold"), places 2, giver "the
  Prefect", desc "The Prefect wants the raiders who burned a lamp-cart
  made an example of. Muster with the wardens and take the hold.",
  epilogue "The hold is taken. The wardens hang nobody; the Prefect's law
  does not hang. It registers."

**Saturna's table (culture `hell`):**

- **Bring the Wine** — BANDIT_POOL, skins {}, sites ("the cart road",),
  giver "the Feast-hall", desc "The feast is in four days and the wine
  cart is stuck at a bridge held by toll-men. Bring the wine.", epilogue
  "The wine arrives. The toll-men are invited."
- **Guard the Feast** — LADDER_POOL[:5] + ("dire wolf",), skins hell,
  sites ("the long table",), giver "the Lord of Misrule", desc "Every
  feast somebody starts a fight and every fight somebody dies. This
  week, stop it.", epilogue "Nobody dies. It is the quietest feast in
  Saturna's memory and the Lord of Misrule is not pleased."
- **Break the Debt-House** — LADDER_POOL[:6], skins hell, sites ("the
  debt-house",), giver "a village elder from the host land", align good,
  desc "Half the village owes a year to Saturna's debt-house. The elder
  wants the books burned. The demons of bargains keep the books.",
  epilogue "The books burn. Half the village is a year richer and
  Saturna's demons of bargains write it down as a lesson."
- **The Hunt of Misrule** (EPIC, capital only) — HELL_RUIN_POOL, skins
  hell, sites ("the hunt's yard", "the quarry's ground"), places 2, giver
  "the Master of Hounds", desc "Once a year the feast hunts something
  that hunts back. This year it is a horned giant off Libera. Ride with
  the hounds.", epilogue "The giant's horns hang in the feast-hall. The
  hounds ate well."

