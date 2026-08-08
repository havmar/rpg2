# World Simulation — content resource & framework

The working doc of THE WORLD & NPC SIMULATION thread. plan.md owns the
build order — since 2026-08-07 the worldsim-build ladder, the
monolithic design session dissolved and everything settleable settled
in plan.md's rulings block; designlog's 2026-08-05..11 entries own
the reasoning; THIS file holds what is still UNBUILT.

Since 2026-08-11 that is a SHORT list. Every land packet this file ever
carried has shipped — economy, politics, religion and magic — and what is
left here is only the residue no session was asked to build: the standing
FACTS of the economy and politics packets (religion's and magic's became
`worldsim.FACTS` and are cut), the OPTIONS that want a counter the game does
not have yet or a crime-layer category that is not written, the ruler
sheet's per-land and per-race MODIFIER COLUMNS, and the PC's own blank
sheet. None of it blocks anything; all of it is a design round away.

When a piece ships, its rules move to rules.md and its entry here is cut
(the plan.md convention) — the record framework went that way on
2026-08-07, the weather on 2026-08-08, the six ECONOMY land packets on
2026-08-09, THE RULER CHARACTER with the six POLITICS packets on
2026-08-10, and the six RELIGION and six MAGIC packets on 2026-08-11. The
summary of what they became now heads this file so the residue below can be
read against it.

Register note: entries are IDEA-LEVEL, in the dev register. Final
player-facing strings are written at implementation time under
writing.md, and reviewed on the `placegen_review.txt` worksheet
pattern where wording matters.

Provenance: the packets are the designer's 2026-08-05 brainstorm,
rewritten and classified. Assistant additions are marked **[PROPOSED]**;
on 2026-08-07 the designer adopted the [PROPOSED] set WHOLESALE —
implement it like everything else — so the marks (here and in every
later section) are provenance only now, not a cut list.

## What SHIPPED — what anything written here is written against

The five record kinds, the wealth roll, the crisis deck, the relations
table and the lazy day-stamped rolls are BUILT (2026-08-07); so is the
whole WEATHER system this file used to sketch (2026-08-08); so, since
2026-08-09, is the ECONOMY FLOOR — the three outlets the frame carried
but did not apply, the six econ packets' cards and edges, and the card
CHAINS; so, since 2026-08-10, is POLITICS — the constitution slot,
the tension roll and its deck gate, the faction edges, the whole RULER
CHARACTER sheet, and the war layer's feed; and so, since 2026-08-11, are
RELIGION and MAGIC — the last two record kinds (FACT and OPTION), the six
worship packets and the six arcane ones, the Sun communion's two-way
schism edge, the talent-and-hunt chain that runs in every land, and the
crime layer's mark table. It is all `worldsim.py` and `rulers.py`, with the
played rules in rules.md's *The World Layer*, *Weather*, *The Economy
Floor*, *Politics & the Ruler* and *Religion & Magic*, and the code index
in develop.md. What was cut from here is there; what remains below is the
residue still to design.

The API facts an entry in this file needs to know:

- **A card is `worldsim.card(key, name, land, ...)`** — admitting
  conditions (`wealth`, `states`, `without`, `weather`, `wet`/`dry`,
  and the politics rung's five ANY-OF slots: `tension`,
  `constitution`, `traits`, `succession`, `faction_edge`), up
  to five outlet effects (`quest` / `menu` / `encounter` / `news` /
  `state`), and an optional day-stamp clock (`days`). ALL FIVE are
  applied now. A state effect is
  `{"set", "while", "clear", "slot", "wealth", "wealth_while",
  "constitution", "succession"}` — what
  a card SETS outlives it, what it sets WHILE it stands comes off with
  it, and slot members are exclusive.
- **A card's `tension` is also its GATE**: a card that names one only
  enters the deck of a land whose worldgen roll produced it. A card that
  names none is land-wide. This is what lets a packet stay a wide POOL
  without drowning a land's deck.
- **The land ruler is `worldsim.ruler_sheet(world, land)`** — the flat
  `traits` word list a card admits on, plus `heart`, `succession`,
  `accession` and the two companion fields. `rulers.roll_ruler(rng,
  crown=False)` is what a card's `hook` rolls for a lesser named
  authority (`worldsim._authority_hook` keeps him on the land).
- **The three wired outlets.** `quest=` takes `post` (a job template
  built by `worldsim.job(...)`), `slots` (negative cancels work) and
  `reprice`; `menu=` takes `MENU_TERMS` (goods / steel / lodging /
  healer / toll / ferry) as multipliers; `encounter=` takes `kinds`,
  `where` ("road" / "wilds"), `skins` and `as`. A state can carry the
  last two by itself through `STATE_MENU` / `STATE_ENCOUNTERS`, which is
  how a DERIVED state reaches a price or a road.
- **A CHAIN is a card SETTING a state the next card ADMITS on** and
  clears as it fires — no extra machinery. One shipped chain crosses a
  relation.
- **`land` takes one land, several, or `worldsim.ANY_LAND`**, and
  `track=` picks which of a land's three decks the card sits in:
  `crisis` (drawn off the wealth band), `weather` (drawn off the day's
  sky, gated by the card's own `chance`), `season` (drawn off a long wet
  or dry spell). One live card per track, so a storm never blocks a
  harvest failing.
- **A relation is `worldsim.relation(from, to, kind, when=, then=,
  because=)`** — a directed edge whose `then` state the target land
  DERIVES at read time for as long as the source holds one of `when`.
- **A fact is `worldsim.fact(land, key, TITLE, line)`** — DM-only standing
  colour the engine never reads, surfaced on `lore` and nowhere else.
- **An option is `worldsim.option(key, name, land, does=, gold=, term=,
  ...)`** — a STANDING priced service at a counter, gated like a card,
  doing exactly one of `bless` / `book` / `sky`. Anything that wants a
  fourth verb is a feature request, not content.
- **A state can also reach the CRIME tables**: `STATE_MARKS` puts extra
  mark faces in a category's roll (the reagent consignment, the opened
  tomb, carnival's masks).

The need-to-exist settlement trim shipped the same day as the frame: the
census, the reserve pool and the draw are rules.md's *The map*;
`places.materialize_settlement` / `quests.found_settlement` are what a
card or relation calls when it needs a place to exist.

## Asymmetry doctrine

Lands do NOT need similar amounts of material. The floor every land
needs: the wealth roll, three-plus crisis cards, one or two
relations, one flavor anchor. (The economy floor session reached it:
five or six crisis cards a land, an anchor each, 17 edges.) Above the
floor, depth follows the
designer's interest — a plainer generic-fantasy land beside a
detailed one is contrast, not neglect. The overlap guard for the four
modern-flavored societies (Ensimaa, Dvarvengrond, Gibili,
Mortellaria) is the PROBLEM AXIS named at the head of each packet:
a land's troubles must come from its own axis.

## THE LAND PACKETS — ECONOMY: what did NOT ship (2026-08-05, trimmed 2026-08-09)

The economy floor session (designlog, 2026-08-09) built the six econ
packets' CARDS, their relation edges and the chains between them; those
entries are cut, and the played rules are rules.md's *The Economy Floor*.
What is left here is the part of the packets no session has consumed
yet — the standing FACTS a DM reads (they cost nothing at runtime and the
engine never sees them), the OPTIONS that want a priced-menu entry of
their own rather than a multiplier on an existing one, and the two cards
plan.md's rulings park.

**Facts — the standing colour of each land's economy.** Ensimaa: the
economy is rare artisanal and artistic output, small and irreplaceable;
values with teeth (murder graver than among humans, property crime
lighter — the jerkify machinery read at LAND level); dwelling anchors of
hellenic white marble, giant treehouses, the impossibly tall thin tower.
Tergal: wealth moves on the hoof and cannot be accumulated, so gifts and
obligations do the work of savings, and demands of favours and
accusations of ingratitude are standing hooks; law is thin (lower
protection and heat, rougher self-help); imports metal, textiles and
grain, exports animals, herd products and MERCENARIES. Dvarvengrond: a
mining economy that needs food and timber imports to live. Firascir:
manorial agriculture under lords, guilds in the towns. Mortellaria:
finance exists here and nowhere else — shares, banks, paper money,
credit, one abstract tropical colony offstage — and its villas and
palaces are the crime layer's richest marks. Gibili: smoke, steel mills,
glassworks, textile mills, firearms largely for Mortellaria, and no state
power to speak of — law is company enforcers.

**Options still wanting their own priced-menu entries.** The economy
floor wired the six TERMS that move prices the game already charges; each
of these is a NEW thing to buy, and wants either the crime layer's
categories or a counter of its own:

- **Mercenary hiring in Tergal** — the land's own export, sold across the
  border. The nearest shipped machinery is `recruit`/`hire`, which is
  free and CHA-capped; a paid mercenary is a different transaction.
- **Banking in Mortellaria** — paper-to-gold conversion and credit. The
  bank-run card already knows what worthless paper is; nobody sells the
  service yet.
- **The drug markets** — Ensimaa's smoking and Powder problem (a standing
  smuggling market) and Tergal's prestige smoking (expensive, severe,
  chieftains only, a question of status).
- **Smuggling** against Firascir's guild monopolies and Mortellaria's
  tariffs; **the gadget market and the arms trade** in Gibili. All four
  belong with the crime layer's smuggling category rather than a shop.

**The two parked cards.** *Robot servants* built by elves or with goblin
science — the manpower fix that walks; construct encounters and
who-answers-for-it questions. WAITS for the science & technology layer:
its tone/tech question is that layer's magical-vs-mundane boundary call.
*Sulfur mined and sold to Hell* out of Dvarvengrond — coherent with the
pact frame, which already makes Hell an economic actor. WAITS with hell's
own parked treatment.

## THE RULER CHARACTER & THE POLITICS PACKETS: what did NOT ship (2026-08-10)

The politics session (designlog, 2026-08-10) built the whole ruler sheet,
the constitution slot, the tension roll and its deck gate, the faction
edges, every **card** entry in the six political packets, and the war
feed. Those entries are cut; the played rules are rules.md's *Politics &
the Ruler*, the code is `rulers.py` and `worldsim.py`, and develop.md
indexes both.

What is left here is the part of the packets no session has consumed —
the standing **facts** a DM reads (they cost nothing at runtime and the
engine never sees them) and the **options** that want a priced-menu entry
or a crime-layer category rather than a card — plus the two pieces of the
ruler sheet the build could not settle.

**The ruler sheet's own leftovers.** The weights shipped are the
HUMAN-CROWN / FIRASCIR BASELINE and nothing else: **per-land and
per-race modifier columns are still to author**, and with them the
tribal rewording (an orcish society will zero or reword some axes —
`itinerant` means nothing on a plain where the whole court moves). The
magic cells (spell-friendly 2, spell-fearing 3, gifted 1) are hand-set
and are the first modifier targets. **The PC's own blank sheet remains
an open question** — the schema serves the authority tier and the named
actors cards create; givers and service faces stay blank by the
characteristic criterion.

**Facts — the standing colour of each land's politics.** Ensimaa: THE
FROZEN LADDER (the elite hoard life-extending magic, seats and
precedence — nothing opens because nobody dies and nobody yields, and
the "young" of a mere century own nothing); FACE IS THE CURRENCY (purity
certificates renewed by interview gate office, contract and polite
existence; the neighbourhood association watches and reports as a civic
duty — ruin is reputational, not judicial); SHUNNING IS THE CAPITAL
PUNISHMENT (the erased elf is looked through, unnamed, contract-void —
an elven heat that posses never enforce); THE MALAISE (the automation
meets every need and asks nothing back; the commons are safe, idle and
meaning-starved). Tergal: TANISTRY (the ablest kinsman inherits — strong
chiefs by design and a scramble every time); THE SKY'S MANDATE (the
neighbours are rebels who have not yet submitted, and an omen read in
bones can halt a campaign the council already voted); WERGILD (every
life and limb has a price in livestock, payable to the wronged kin — in
Tergal sin can be SETTLED, and unpaid it reads as the feud); GUEST RIGHT
(whoever eats at the fire is safe, blood enemies included; the one sin
no wergild covers); THE CLAN MOTHERS (lineage and herds run through the
women, who seat chiefs and unseat them); THE DOG SOLDIERS (a warrior
society polices the camps with absolute authority over any rank — law
enforcement with a face, and not the chief's); PRESTIGE IS GIVEN AWAY
(authority is earned by open hands and lost overnight when the giving
stops; rivals are buried under gifts they cannot repay); VOTING WITH THE
FEET (a failing chief wakes to empty grass); OUTLAWRY (the cast-out is
stripped of law entirely — Tergal's crime layer runs on the declaration,
not on posses); THE COMPANIONS (free warriors who abandon clan to swear
to a charismatic nobody — which is exactly what the land reads a PC
party as). Dvarvengrond: GEOLOGICAL LAW (all law is extraction law —
murder is a crime, collapsing a rival's gallery is high treason); CLAIMS
ARE ETERNAL (a claim binds to blood and to the dead who cut it; rezoning
one tunnel needs the living AND rites to release the founders);
HOARDING IS STATESMANSHIP (the mightiest thanes hold court inside their
own unmined veins — power displayed by NOT extracting); BLOOD AND QUOTAS
(a missed tonnage is a spiritual failing before the ancestors, not
merely a debt); THE WILDCATTERS (claim-jumpers in the condemned upper
galleries, persecuted as structural traitors rather than thieves); THE
SHORN (the unclanned: name stripped, no legal person, killable without
price — a protection-zero band for the crime layer's mark tables); THE
SURFACE ENVOYS (the despised caste that handles everything above ground
— nearly every dwarf the party meets abroad is one). Mortellaria: THE
GILDED CAGE (the high nobility must attend the palace — precedence wars,
ruinous wardrobe, bedchamber offices, the salons as unofficial
ministries — kept beautifully broke and far from their power bases);
EVERYTHING IS FOR SALE (offices, titles, judgeships and colonelcies
minted to cover debts; the absurd office is real power); THE BLACK
CHAMBER (every sealed letter through the capital is opened, copied and
resealed — the game's delivery quests pass through this fact); THE OARS
(the state's galleys are rowed by the sentenced, and the port's press
gangs take the rest on a bad night); THE SMUGGLER STATE (internal
tariffs and the salt price built a parallel nation better funded than
the coast guard). Gibili: THE PARLIAMENT OF CHAOS (deadlocked and OWNED
— rotten districts where one landlord commands all three voters); THE
BUFFER DOCTRINE (the whole foreign policy is "give the empire no
excuse", and the empire quietly funds rival radicals to keep the state
weak); THE SPLIT ARMY (aristocrat generals who despise the mill barons
commanding slum-drafted ranks who sympathise with the strikers they are
ordered to shoot — every crowd order is a coin flip); THE SYNDICATES AS
SHADOW STATE (unions running schools, clinics, courts and dues in the
districts the state forgot).

**Options still wanting an entry of their own.** THE FLOATING QUARTER
(Ensimaa: one walled district where face is suspended — pleasure,
Powder, debt, unmentionable outside its gate; the econ packet's drug
market has its address here). THE SINGERS (Tergal: wandering skalds own
the oral record, and praise and mockery ARE the propaganda layer — a
rumor outlet with a face, and a singer hired against a chief is a card
in waiting). SANCTUARY (Firascir: a fugitive who reaches the altar
cannot be taken for forty days, then walks barefoot into exile — a
priced, timed heat valve the crime layer can quote, and a card when the
posse decides not to wait out the clock). LETTERS OF MARQUE
(Mortellaria: state piracy with paperwork, one revoked commission away
from the ordinary kind). THE EMIGRE CAFES and THE BASEMENT PRESSES
(Gibili: every neighbour's exiles end up here and half of them are
somebody's informant; seditious print for every appetite, smuggled south
against the censors — standing employer fauna, and the crime layer's
smuggling category).

## THE RELIGION & MAGIC PACKETS: what did NOT ship (2026-08-11)

The religion and magic rung (designlog, 2026-08-11) built BOTH packets
whole — every fact, every option, every card and every edge in them, plus
the two record kinds they needed. The sections are cut; the played rules
are rules.md's *Religion & Magic*, the facts are `worldsim.FACTS` (read at
the table with `lore`), and the options are `worldsim.OPTIONS`.

Four things in them were parked by name and are parked still:

- **THE DRAUGR, THE KNOCKERS as a creature, and Tergal's GRAVE-MADE
  GHOSTS** wait for the monsters & fauna dump — each names a creature row
  the catalog does not have (see the last section of this file).
- **CURSED WORK** — the cursed ring that grants +3 DEX and takes 1 point of
  natural DEX; the affliction doctrine sized to an item, power with a
  receipt. It belongs with plan.md's parked non-weapon magic items row
  (rings and amulets reusing the weapon `sp` table) and is priced there,
  not here.
- **SULFUR MINED AND SOLD TO HELL** waits with hell's own treatment, as it
  did before; **the ROBOT SERVANTS** wait for science & technology.
- **THE RULER SHEET'S MAGIC CELLS** (spell-friendly 2, spell-fearing 3,
  gifted 1) are still hand-set and still the first per-land modifier
  targets. The packets now supply each land's direction — Ensimaa and
  Gibili friendly, Firascir indifferent, Mortellaria patron-and-leash,
  Tergal reads it as armament, Dvarvengrond as a trade — but the columns
  themselves are deferred with the rest of the modifier work above.

The **temple/penance wiring** is NOT on this list because it was never
this rung's: whether and how temples interact with the shipped sin/penance
economy is deliberately undesigned at the designer's 2026-08-06 direction,
and the rung shipped temples as plain priced services exactly as ruled.

---

## The layers still to dump (designer's list, recommended order)

**politics → religion → monsters & fauna → magic, science &
technology.** Four of the five are done and SHIPPED: politics and the
ruler character (dumped 2026-08-06, built 2026-08-10), religion (dumped
2026-08-06, built 2026-08-11) and magic (dumped 2026-08-07 ahead of
monsters & fauna on the designer's initiative, built the same day as
religion — the two rode one rung). What each of them left behind is the
"what did NOT ship" section above it, and nothing else.

**Monsters & fauna** is POSTPONED (2026-08-07, with science &
technology — the build implements what is dumped); when it comes it is
mostly ASSIGNMENT: the per-land encounter pools already exist, and the
dump picks distinctive regional creatures and ties cards to them (the
fog necromancer pattern). The religion packets PRE-ORDERED three of
them and their cards wait with the dump: THE DRAUGR (a dead founder
who will not stay down, in his own gallery, on his own hoard, and by
claim-law still its holder — the priestly answer, the practical answer
and the legal question of whose vein it is, all three for hire), THE
KNOCKERS as a creature rather than the shipped fact, and Tergal's
GRAVE-MADE GHOSTS (the religion rung shipped the foreign-graveyard card
over the catalog's skeletons and ghouls; the grave-made ghost is still
its own row to write).

**Science & technology** is the layer's remaining half. It should still
ride the land packets as flavor anchors first (elven robots, dwarven
methods, goblin gadgets are already in them) and get mechanics only
where a card demands one — and it owes the magic packets one boundary
when it lands: which technology is magical at the core (the embedded
tier) and which is mundane (the robot question, the guns). The two
parked cards above wait on exactly that call.
