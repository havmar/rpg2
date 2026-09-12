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

> **Section 9, section 4's relics and stone, and section 14's "Into the
> ruins" table are CUT** (2026-09-12, session 2 shipped). Where they went:
> the two sentinels, the two bars, the seal's correction, the ruin jobs
> and Tom's stone are **rules.md's `Heaven & Hell - Add-on, part 2`**; the
> table manner is **dm.md's "The gates"**; the code pointers are
> **develop.md's Files and dev map**, the annotation numbers
> **benchlog.md's 2026-09-12 (B) entry**, and the build record (with every
> [build settles] call) **designlog.md's 2026-09-12 (B)**. What remains of
> section 4 is the ONE LINE session 5 still owes: a fact line per culture
> on the lore page, in the culture's own words -- the table of versions
> itself is now rules.md's. What remains below is sessions 4-5.

> **Section 12, the Nephilim, is CUT** (2026-09-12, session 3 shipped).
> Where it went: the three lines, what the blood does, the two rolls and
> the sheet's BLOOD row are **rules.md's `Heaven & Hell - Add-on, part
> 3`**; the table manner is **dm.md's "The gates" and "The player
> character"**; the code pointers are **develop.md's Files and dev map**,
> the two measured distributions **benchlog.md's 2026-09-12 (C) entry**,
> and the build record (with every [build settles] call)
> **designlog.md's 2026-09-12 (C)**.


## 4. Tom -- what is left of it (session 5)

The figure, the versions and the two relics are rules.md's Heaven & Hell
add-on part 2 (2026-09-12, session 2). One thing in this section is not
built: **one fact line per culture on the lore page**, the table of Toms
in the culture's own words, which belongs with session 5's packets and
lore pages (section 11's human side).

> **Section 6's CITY half, section 10 and section 14's two city tables
> are CUT** (2026-09-12, session 4 shipped). Where they went: the tile
> takeover, the one-tile state, its city and its counters, its prices, its
> board, its two crowns and its two name registers are **rules.md's
> `Heaven & Hell - Add-on, part 4`**; the table manner is **dm.md's "The
> gates" and "The nine countries"**; the code pointers are **develop.md's
> Files and dev map**, the numbers **benchlog.md's 2026-09-12 (D) entry**,
> and the build record (with every [build settles] call, every per-reader
> in/out decision for a one-tile state, and exactly what session 5 owes on
> the two packets) **designlog.md's 2026-09-12 (D)**. What remains below
> is session 5: section 11 in full, plus the one line of section 4.

## 11. The world layer: two packets

Everything the validator demands (worldsim.py `_validate_countries`): four
constitutions at 6/2/1/1, at least two rollable tensions with their
factions, faction edges between blocs some tension names, at least one
card per land on each of the three tracks (`crisis`, `weather`,
`season`), at least one standing fact, at least one relation edge, a
capital tile. Both packets are authored under their CULTURE key
(`heaven`, `hell`), the Thule precedent.

> **What session 4 already SHIPPED as a stub** (2026-09-12), authored off
> the rows below so this section extends rather than replaces it: both
> sides' **four constitutions**, all **three tensions** each with the
> inner axis STANDING, all **twelve blocs**, all **twelve faction edges**,
> ONE crisis card each (`heaven/the-register`, `hell/the-feast-spills`),
> the **weather** card each (`heaven/clear-sky`, `hell/feast-fires`, both
> with `sky="clear"` -- the [build settles] call), the **season** card
> each (`heaven/the-choir-season`, `hell/the-wild-season`), the first
> **fact** each (THE GATE, in each city's own words), and three state
> words (`register-read`, `feast-spilled`, plus a placeholder
> `gate-watched`). **What session 5 still owes is everything else on this
> page**: the seven other crisis cards a side, the two OPTIONS a side, the
> five remaining facts a side, the rest of the state words with their
> `STATE_MENU` and `STATE_ENCOUNTERS` rows, the four HOST-resolved
> relations rows (which must REPLACE the two placeholder
> concordia<->saturna edges and retire `gate-watched` with them), and the
> whole human side below.

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

## 13. Sessions

Five build sessions, in an order forced by what boots. Each is one
contract in plan.md pointing here; each ends with the standard paperwork
(rules.md add-on, dm.md, develop.md, benchlog, designlog, the plan entry
deleted, the section here CUT).

**Session 1, the four sites on the map, SHIPPED 2026-09-12** (designlog
2026-09-12 (A)), **session 2, the two sentinels and the ruin jobs,
SHIPPED 2026-09-12** (designlog (B)), **session 3, the Nephilim, SHIPPED
2026-09-12** (designlog (C)) and **session 4, the two city states, SHIPPED
2026-09-12** (designlog (D)); their sections are cut from this file. One
remains.

| # | session | ships | this file's sections |
|---|---|---|---|
| 5 | **The packets and the human side** | the full two packets, the state words, menus and encounters, the HOST-resolved relations, the synod card, the four culture facts, the host facts, the crusade tension and card, the pact pointer line, the lore pages | 11 in full |

Session 1 was the biggest and is what made the arc PLAYABLE: a new world
now has two ruins to walk into at any level, session 2 put something at
the bottom of each, session 3 put the setting in the party itself, and
session 4 made the two live colonies COUNTRIES -- eleven lands, two
boards, two crowns, two priced counters. What session 5 has left is the
CONTENT the frame is now waiting for: the two packets in full (the stubs
mark what stands), the human side's reaction to all of it, and the one
Tom line per culture on the lore page.

## 14. The quest templates

Authored in writing.md's register (a problem already happening, who
wants it changed, a visible objective, at most one complication). `pool`
sets the band; `sites` are the stems the job's places are named by.

> **The two CITY tables are CUT** (2026-09-12, session 4 shipped them as
> `quests.TEMPLATES["heaven"]` and `quests.TEMPLATES["hell"]`, four rows
> each with the failure epilogues the build had to write). Nothing of
> section 14 remains to build.
