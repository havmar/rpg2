# World Simulation — content resource & framework

The working doc of THE WORLD & NPC SIMULATION thread. plan.md owns the
build order — since 2026-08-07 the worldsim-build ladder, the
monolithic design session dissolved and everything settleable settled
in plan.md's rulings block; designlog's 2026-08-05..10 entries own
the reasoning; THIS file holds what is still UNBUILT — the religion
land packets (the worship dump, 2026-08-06) and the magic land packets
(the arcane dump, 2026-08-07), plus the leftovers of the economy and
politics packets that no session has consumed (the standing facts, the
options wanting a priced entry of their own, and the ruler sheet's
per-land modifier columns). When a piece ships, its rules move to
rules.md and its entry here is cut (the plan.md convention) — the
record framework went that way on 2026-08-07, the weather on
2026-08-08, the six ECONOMY land packets on 2026-08-09, and THE RULER
CHARACTER with the six POLITICS packets on 2026-08-10. The summary of
what they became now heads this file so the packets below can be read
against it.

Register note: entries are IDEA-LEVEL, in the dev register. Final
player-facing strings are written at implementation time under
writing.md, and reviewed on the `placegen_review.txt` worksheet
pattern where wording matters.

Provenance: the packets are the designer's 2026-08-05 brainstorm,
rewritten and classified. Assistant additions are marked **[PROPOSED]**;
on 2026-08-07 the designer adopted the [PROPOSED] set WHOLESALE —
implement it like everything else — so the marks (here and in every
later section) are provenance only now, not a cut list.

## The frame, the weather, the economy floor and the politics SHIPPED — what the packets are written against

The five record kinds, the wealth roll, the crisis deck, the relations
table and the lazy day-stamped rolls are BUILT (2026-08-07); so is the
whole WEATHER system this file used to sketch (2026-08-08); so, since
2026-08-09, is the ECONOMY FLOOR — the three outlets the frame carried
but did not apply, the six econ packets' cards and edges, and the card
CHAINS; and so, since 2026-08-10, is POLITICS — the constitution slot,
the tension roll and its deck gate, the faction edges, the whole RULER
CHARACTER sheet, and the war layer's feed. It is all `worldsim.py` and
`rulers.py`, with the played rules in rules.md's *The World Layer*,
*Weather*, *The Economy Floor* and *Politics & the Ruler*, and the code
index in develop.md. What was cut from here is there; what remains below
is the content still to author against it.

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

---


## THE LAND PACKETS — RELIGION (2026-08-06)

Provenance: the designer's 2026-08-06 religion notes — a register per
race (shamanic orcs; pagan-Germanic, stereotypical-fantasy dwarves;
folksy, superstitious, cult-like goblin business religions — showy,
busy, loud, self-help and multi-level-marketing shaped; secular /
philosophical / nondual elves whose religion stays personal and
fragmented even under a totalitarian state; a Christian-coded Sun
religion of the One God for both human lands, Mortellaria's version
obsessed with death imagery and Dionysian hedonism as two aspects of
the one, carnival and day-of-the-dead vibes) — expanded by the
assistant on the approved mapping method: find the real-world
version and carry its realistic or quirky detail, never the
generic-fantasy filler. Written in two rounds (outline, feedback,
writeup — all 2026-08-06); the feedback is folded in below. Entries
beyond the approved outline are marked **[PROPOSED]** (adopted
wholesale 2026-08-07 — the intro's ruling). All of it is a first
version, to be playtested before it
hardens.

Three directives from the feedback round govern the whole section:

- **The pact stays out.** The player's hell pact is a gameplay
  frame that predates the detailed worldbuilding, and it is NOT
  lore: nobody in the world knows of it, nothing can sense it, and
  no religion entry reacts to it — dark play is an option offered,
  never a mark that makes the party conspicuous. Hell as a place,
  actor, or church waits for its own later treatment (the
  Caelum/pirates pattern — parked, deliberately unharmonized).
- **Temple services are deferred.** Temples are option material
  (healing, burial, blessing as priced-menu entries where a packet
  says so), but the sin/penance wiring is deliberately NOT designed
  here — the karma layer's mechanics are their own open question,
  and the worldbuilding leans on none of them for now.
- **No theology ruling.** The game never decides which land's
  religion is true. Each is written from inside, on its own terms;
  they contradict each other exactly the way real religions do, and
  the contradictions are content (the disputation, the schism, the
  mission), never errors to reconcile.

**What politics already ate** (reference, don't duplicate — the
dedupe doctrine): the interdict, the investiture tension and the
militant order, the witch-finder, the dancing plague, sanctuary, the
scandalous priest, and the tithe war (Firascir); the auto-da-fé and
the Revocation (Mortellaria); the Sky's mandate, the bone-readers'
veto, and the ghost dance (Tergal); the founders' dead and their
release rites (Dvarvengrond); the purity writs, shunning, and the
hermits (Ensimaa). Religion owns worship, rite, and the parish's
daily texture; politics keeps church POWER.

### The Sun communion (the two human lands, one church)

One church, two rites — the outline round's lean, adopted: Firascir
and Mortellaria worship the same One God of the Sun in one nominal
communion, because the standing argument between two rites is better
content than two sealed religions (the Latin/Greek shape: one
communion in name, two liturgical worlds, the schism always one
insult away).

- **fact** The shared spine: one God, whose visible face is the
  sun; dawn services; the solar year as the liturgical calendar.
  Everything else the rites contest.
- **relation** THE SCHISM CLOCK: the northern rite calls
  Mortellaria's death-face devotion creeping heresy — an accusation
  with teeth in a world where a king corrupted by a hungry god is a
  thing that happens (the war layer's Deathless Crown variant is
  the nightmare version, and both rites know it). Mortellaria
  answers that a faith that refuses death its face is what MAKES
  death monstrous. Both are right, neither yields, and every joint
  synod ends one insult short of the split (the Photian shape).
  Cards on this edge fire in both lands.

### Ensimaa — elves. Religion axis: REVERENCE WITHOUT WORSHIP

Reworked on the feedback round's directive: recognizable high
fantasy elves — grace, refinement, gravity; the superhuman race
whose one big flaw keeps the short-lived races on the board — with
the notes' secular/nondual spine worn as ancient contemplative
dignity, not modern satire. (The same directive flags the rest of
the elven material for a later coherence-and-subtlety pass.)

- **fact** THE UNPETITIONED HEAVEN: elves acknowledge the powers
  humans call gods — they are old enough to have met a few — and do
  not worship them. Their reverence goes to the whole of things,
  never to a person in it (the nondual reading); asking a power for
  favors strikes them as a category error, and watching humans pray
  embarrasses them faintly, the way watching someone beg does.
- **fact** THE STAR-COURTS: the land's only religious architecture
  — open-roofed white marble courts, silent by custom, no clergy,
  no services, no images. An elf sits with the night sky; that is
  the whole liturgy. Visitors are admitted, and the silence is kept
  without one posted rule.
- **fact** THE SCHOOLS: a handful of contemplative disciplines
  older than human civilization — teacher lineages, essays
  exchanged a decade apart, membership as personal as a human's
  parish. From outside the schools are indistinguishable; inside, a
  one-word difference in one old text is a gulf. This is why even
  the sealed-realm state never seized a church: there has never
  been one to seize (the designer's note, kept as the axis's
  political face).
- **fact** MEMORY IS THE AFTERLIFE: the dead are not prayed to but
  remembered EXACTLY — recited, name by name, deed by deed, for
  millennia. WIRING: the politics packet's unearthed-record scandal
  cuts as deep as it does because curated memory is sacrilege in
  the one place elves keep something sacred.
- **card** THE FUNERAL: an elf actually dies — once a century,
  and murder's graver weight (econ) means it is usually a crime
  too. The land stops. The rite is long, closed to outsiders, and
  the grief is not graceful: an ageless people has no practice at
  endings, and the composure the whole culture stands on fails in
  public. The big flaw, worn liturgically.
- **card [PROPOSED]** THE MISSION: a Sun-church mission has stood
  in the capital for four hundred years and converted no one. The
  elves send polite questions the missionaries cannot answer, and
  fix the mission's roof when it leaks. Both sides consider the
  arrangement a success.
- **relation** THE ONES WHO GO TO LEARN ENDINGS: young elves — the
  Mortality Club's quieter cousins — travel to Mortellaria's death
  feast to stand where death has a face. The elders call it a
  sickness; a few are old enough to remember going.

### Tergal — orcs. Religion axis: THE PRACTICE, NOT THE CREED

Shamanism as technique (Tengrist, Siberian, and plains-nations
mechanisms, near verbatim). Politics owns the Sky's mandate, the
bone-readers, and the ghost dance; religion keeps the daily
practice a camp actually lives by.

- **fact** THE CALL: shamans do not choose — a sickness or madness
  takes the marked one, and initiation under a living shaman is the
  only cure; refusal ends in death or a broken mind (the Siberian
  shaman-sickness, verbatim).
- **card** THE CALLED CHILD: a chief's child has the call; the
  family hires escort to a distant teacher — or hires hands to hide
  the child from the spirits, which every shaman says cannot be
  done.
- **fact** TABOO LAW: running water is never fouled (wash in a
  river and answer for it — the Mongol water taboos), a tent's
  threshold is never stepped on, the dead's names go unspoken. The
  party WILL trip one — a standing scene machine, guest right's
  ritual sibling, and the fine is paid in livestock like everything
  else (wergild's little cousin).
- **fact** THE SKY BURIAL: the dead go to the birds on exposure
  platforms; burying a body in earth MAKES a ghost. A foreign
  graveyard is an abomination the camps detour around — and a
  native haunting means someone skipped the rites, with an address
  at the end of the rumor line (the fog-necromancer pattern).
- **option** THE WEATHER-WORKER: rain stones (the jada): a shaman
  who moves weather can be HIRED — drought relief, or a storm
  dropped on an enemy's grazing. The weather system's day roll
  gains a priced thumb on the scale.
- **fact** WHITE AND BLACK: the healer-shaman everyone loves, and
  the one who deals with the dark spirits — needed, paid double,
  and made to camp outside the ring of tents. The useful pariah:
  when the herds sicken or the dead walk, everyone knows whose
  tent to visit, after dark.
- **fact** OWNER-SPIRITS: every spring, pass, and mountain has one
  (the land-wights); travelers add a stone to the cairn at every
  pass (the ovoo) — cheap travel-leg color, and an offended owner
  starts the misfortune chain the shaman is paid to end.

### Dvarvengrond — dwarves. Religion axis: THE DEAD ARE THE CHURCH

Norse pagan practice over an ancestor cult, with the mining
folklore worn as liturgy — the stereotypical fantasy dwarf, built
from the real superstition catalog.

- **fact** The gods are far away and the ancestors are RIGHT HERE:
  formal worship is thin — a hall blessing, a seasonal sacrifice
  (the blót) — and the working faith is the dead in the stone,
  consulted, fed, and still holding claims (politics' founders'
  veto is this fact's legal face). The deepest galleries are tombs,
  and the tombs are the holiest ground in the mountain.
- **fact** THE KNOCKERS: the mine-spirits knock before a collapse,
  and are paid for it — the last bite of every meal left at the
  working face — and WHISTLING UNDERGROUND IS FORBIDDEN (the
  Cornish tommyknockers' superstition catalog, verbatim). Skeptics
  exist; they are assigned the unluckiest shifts.
- **fact** THE OATH RING: an oath sworn on the shrine's iron ring
  binds in LAW (the hof ring) — the Grand Ledger's sacred sibling,
  and oath-breaking the one crime the priests own outright.
- **card** THE SEERESS: a traveling prophetess (the völva) whose
  visit even thanes prepare for — the high seat built, the
  questions submitted in order, no second answers. Her word on a
  vein or a succession moves markets, and someone always wants the
  question asked again.
- **card** THE DRAUGR: a dead founder who will not stay down — in
  his own gallery, on his own hoard, and by claim-law still its
  HOLDER. The priestly answer, the practical answer, and the legal
  question of whose vein it is now: all three for hire (WAITS for
  the postponed monsters & fauna dump to assign its creature row —
  the card names it).
- **fact** GRAVE GOODS: wealth is buried with the dead — hoarding
  as statesmanship continued past death (the politics fact's
  liturgical face). The mountain's richest rooms are its tombs,
  tomb-robbing is the deepest sacrilege on the books, and the
  crime layer's most lucrative marks are its worst ideas.

### Firascir — humans. Religion axis: THE PARISH IS THE SECOND STATE

Medieval Latin Christianity played straight, as the land plays its
economics — the baseline church the other five lands deviate from.

- **fact** THE PARISH GRID: every village its priest, every life
  its rites, baptism to burial; the church is the one institution
  that reaches every hearth in the land (the manor reaches the
  body; the parish reaches everything else).
- **fact** THE CALENDAR RULES WORK: feast days claim a third of
  the year, and working them is an offense — the harvest standing
  ripe under a week of obligatory feasts is a card in waiting (the
  real medieval count, kept because it is barely believable).
- **option** THE PILGRIM ROADS: shrine circuits, pilgrim badges,
  the inns that live on them — standing escort work, and a coin
  inflow the econ packet never counted.
- **card** FURTA SACRA: a town steals a rival shrine's relic to
  capture its pilgrim trade — and doctrine holds the SAINT
  CONSENTED, or the theft could not have succeeded (the
  translation of St Nicholas, near verbatim). Work on every side,
  theology included.
- **card** THE THIRD SKULL: three shrines own the same saint's
  skull; a synod orders authentication by miracle — and two of the
  three abbots already know what the test will find.
- **card** THE UNLICENSED MIRACLE: a well starts healing before
  the church has ruled on it — license it, suppress it, or quietly
  improve it; the innkeepers have opinions, and so does the parish
  priest whose font sits empty.
- **card** THE ANCHORITE: a hermit walled into the church wall
  with one street-facing window (the anchoress, verbatim) — the
  village's live-in saint, its advice window, and the one witness
  who has watched the whole street every day for thirty years.
- **card** THE OBLATE: a child given to the abbey at seven wants
  out at fifteen; the abbey holds his labor, his inheritance, and
  the law. A YEAR AND A DAY's church-side cousin, and both sides
  will hire.

### Mortellaria — humans. Religion axis: WHICH FACE RULES

The same One God, the southern rite: the sun DIES every evening
and is born every dawn — Death and the Feast are the god's two
faces, and every argument in the land is over their proper share.
The extremes — debauchery and self-flagellation — are BOTH
arguably orthodox (the designer's note, kept as the axis): this is
a religion whose internal argument its own scripture cannot
settle. Tension candidate for the politics frame's roll: the
penitent wing vs the carnival wing.

- **fact** THE PENDULUM CALENDAR: the year swings between the
  penitential season — hooded processions, flagellant columns, the
  veiled statues (Semana Santa) — and CARNIVAL: masks, license,
  the world upside down. Each wing calls the other the corruption;
  attendance at both is near universal.
- **fact** BONE ARCHITECTURE: ossuary chapels walled in skulls
  (the Capela dos Ossos), catacomb saints dressed in jewels and
  gold wire (the katakombenheilige) — memento mori as the national
  art style, and the crime layer's strangest marks.
- **card** THE DAY OF THE DEAD: one night a year the dead are
  GUESTS — tombs picnicked in, plates set at family tables, the
  graveyard lit like a fair. (2026-08-07: deliberately UNRULED
  whether the dead ever actually attend — the rite works either way,
  the family that swears grandmother came is content in both, and
  the ambiguity is itself content.)
- **card** THE CARNIVAL AMNESTY: sins confessed masked, during
  carnival, are absolved wholesale — the custom old, the theology
  contested, and the season's last night the year's best time to
  be forgiven or to disappear. (Mechanical reading deferred with
  the rest of the temple-services wiring.)
- **fact/option** THE BURIAL BROTHERHOODS: hooded lay
  confraternities (the Misericordia) bury the poor and the plague
  dead on dues and donations — anonymous by rule, ubiquitous by
  custom, and the hood is perfect cover. Card: two brotherhoods
  claim one notable corpse, and the standoff is conducted in full
  regalia.
- **card** THE DISPUTATION RIOT: a public theology debate on the
  two faces — staged as entertainment, wagered on like a duel —
  ends in faction fighting in the square: the argument the axis
  names, with clubs.

### Gibili — goblins. Religion axis: SALVATION AS BUSINESS

No church — a MARKET (prosperity gospel, the multi-level marketing
shape, the tiered-enlightenment ladder, spiritualist parlors,
Victorian burial societies, street millenarians). Showy, busy,
loud — the designer's three words, constitutional.

- **fact** THE RELIGION MARKET: storefront temples, revival tents,
  rival processions with brass bands, jingles, handbills (the
  basement presses print scripture too, and tract-against-tract
  wars sell papers). Congregations are founded, merge, split, and
  fail like firms — weekly.
- **fact** THE LADDER FAITHS: enlightenment sold in ranked tiers,
  each rank's secrets priced above the last, the top tiers' price
  never printed (the Scientology shape); recruiting five converts
  is itself a sacrament, and the downline IS the congregation (the
  MLM worn as church order).
- **fact/option** THE BURIAL CLUBS: weekly dues, a grand funeral
  guaranteed — plumes, band, the good hearse (the Victorian burial
  societies, verbatim; a goblin funeral is the one show everyone
  gets). Cards: the embezzled fund; two clubs claim one corpse.
- **card** THE SEANCE PARLOR: mediumship as parlor business — most
  are knee-under-the-table frauds, a few are real necromancers
  moonlighting (the fog-necromancer pattern), and telling which is
  which is the job (session D's flagged rescue candidate, landed).
- **card** THE PROSPERITY PYRAMID: "the One God wants YOU rich" —
  tithes promised back tenfold, early tithers paid from late
  tithers' offerings, until the collapse (econ's bank-run card's
  ugly street cousin).
- **card** THE GREAT DISAPPOINTMENT: a street prophet dates the
  End; believers quit the mills, sell everything, and climb the
  slag hill in white robes. The card is the DAY AFTER (the
  Millerites, verbatim): the debts, the emptied houses, the
  prophet's recalculation — and the fringe insisting it worked,
  invisibly.
- **option [PROPOSED]** THE CHARM TRADE: amulets, blessed
  machine-oil, curse insurance with printed policies — folk
  superstition as light industry, sold door to door (the patent
  medicine show's spiritual arm).
- **relation [PROPOSED]** THE FRANCHISE MISSION: a ladder faith
  opens a branch in a Firascir market town; the parish priest's
  reaction writes itself (the reverse of Ensimaa's Sun-church
  mission — Gibili exports religion the way it exports guns).

---

## THE LAND PACKETS — MAGIC (2026-08-07)

Provenance: the designer's 2026-08-07 magic brainstorm — the healing
question and its supernatural-affliction answer, the five scarcity
limits, the margin stance, the no-persecution requirement, the
organization sketches per land, and the discipline analogy —
rewritten and classified. Dumped ahead of monsters & fauna (the
recommended order) on the designer's initiative; the layer's other
half — science & technology — is NOT here and keeps its slot in the
order. Assistant additions are marked **[PROPOSED]** (adopted
wholesale 2026-08-07 — the intro's ruling).

**Two development demotions** (recorded so nothing downstream
mistakes them for lore):

- **The conquest questlines are not lore.** They predate the
  detailed worldbuilding; their narrative beats were throwaway
  main-conflict scaffolding for the early game. The human kingdoms'
  undead army can stay for now, but it is not valuable lore — no
  packet owes it consistency. (Mortellaria's necromantic strand,
  the fog necromancer, and the Deathless Crown stand on their own.)
- **The magic-user start is a development matter, and casterhood
  opens mid-game (ruled 2026-08-07).** The current start generates
  a caster for magic-content testing; that carries no worldbuilding
  significance. Cannot-become-a-caster-later is unintentional, and
  the flagged collision with the recorded 2026-08-05 always-caster
  rationale is settled the designer's way: becoming a caster
  halfway into the game is no big design challenge — it is simply
  to keep the game open and fun. Realism makes the world
  interesting but does not restrict the player to that extent:
  GAMEPLAY OPENNESS OUTRANKS M1 at the character sheet. plan.md
  carries the roadmap line; rules.md's never-acquire rationale
  carries the dated softening; the mechanism (and its in-fiction
  reading — a latent gift waking is the cheapest) is the build's
  call when it ships.

### The five limits — what keeps magic scarce

- **M1 THE GIFT IS BORN.** Real magic needs rare inborn ability; no
  diligence substitutes. The gift ignores rank — it lands on
  peasants and princes alike, which is most of the trouble below.
  (A worldbuilding fact, not a player gate — the 2026-08-07 ruling
  in the demotions above.)
- **M2 THE THEORY.** The gift untrained is a hazard, not a career:
  a proper wizard takes years of practice and access to good
  theory, and good theory is hoarded — every organization below is,
  among other things, a gate around it.
- **M3 THE COSTS.** Great workings want rare and expensive
  reagents, and personal Power is limited — as in gameplay: the
  pool is real, the burst is budgeted, and nobody casts all day.
- **M4 THE DANGER.** Magic worked untrained, or with too much
  ambition and too little caution, exacts its own price: madness,
  incurable magical sickness, physical ruin (the affliction
  doctrine below). The orcish reading is already canon — religion's
  THE CALL, the shaman-sickness that kills or breaks the
  uninitiated, is M4 in camp clothes.
- **M5 THE DARK SHORTCUT.** Loss as the price, not the accident:
  blood, body parts, and family members can be traded for Power —
  hell usually involved (hell's own treatment stays parked; at this
  layer that is what practitioners believe, not a mapped place).
  The shortcut works, which is exactly the problem: it is the fast
  road the gifted-and-poor are offered first, and the conduct that
  gets a caster hunted (below).

### The stance doctrines

- **THE MARGIN.** Magic is real, known, and SMALL — a gamble, not a
  pillar. Everyone is secondhand familiar with its minor forms (the
  healer's mending, a charm that works) and almost no one has seen
  a great working; it is not wonder to people, and it is not
  dominion either. M1–M3 keep it from being a definitive
  world-forming force over politics or economics, and its
  reputation — useful and powerful; unpredictable and dangerous —
  balances out to wary respect. No throne, market, or war is
  decided by magic alone.
- **CONDUCT, NOT CREED.** This world has NO analogue of the
  christian stance that magic is from the devil, and no inquisition
  against casting as such — a deliberate design requirement: a
  caster playthrough must never be dominated by automatic hostility
  from civilization. What gets a caster hunted is what they DID:
  dark workings draw witchhunters (a paid trade, not a holy
  office), hired adventurers, or plain soldiers — a murderer's
  treatment with a specialist's surcharge. THE DOCTRINE OUTRANKS
  THE CARDS (ruled 2026-08-07): the two inquisition-adjacent
  politics cards are assistant-written, lower-priority material —
  where they conflict with this requirement they bend or go at
  implementation. The readings that keep them: the WITCH-FINDER is
  a con man whose "witch" is almost never a real caster — real ones
  are rare, the friendless are not; the AUTO-DA-FE prosecutes
  heresy — "witchcraft" on its charge sheet means harm by hidden
  means, and the academy teaching openly in the same capital is the
  doctrine made visible. The ruler sheet's spell-fearing cell stays
  a PERSONAL stance some authorities roll, never a civilization's.
- **PERSONAL AND EMBEDDED.** Personal casting is rare; embedded
  magic is common wherever money is: a large portion of the world's
  functional technology is magical at the core — devices, potions,
  charms (elven automation, dwarven artifice, goblin gadgets: the
  econ packets already carry them). This is how the margin survives
  the technology: a device amortizes one wizard's rare work across
  decades of use.
- **THE DISCIPLINE.** Wizard magic is maths, physics, programming:
  an interface exists for changing the world with thought, but
  building the access, directing the process, and fueling it takes
  complex abstract law learnt deeply and used in long connected
  chains. Some of the difficulty can be outsourced to physical
  substrates — a device or a potion carries a pre-solved working in
  matter. The analogy completes the margin: everyone uses the
  products, few can do the work, and the ones who can are well-paid
  professionals, not kings. And the PC's gift reads in-world as
  PRODIGY: very strong inborn talent that turns a little theory
  into new and stronger practice fast — the in-world reading of the
  spellbook economy, where a 120g book makes the PC dangerous and
  makes an academy student a sophomore.
- **CAN'T, OR COSTS DOUBLE (the price rule — designer's answer,
  2026-08-07).** Why doesn't every problem get fixed by magic?
  Simply: it can't, or it would be twice as expensive as any
  mundane solution. There is no spell to create lots of food for
  free, or to fix the harvest — and where a working does exist, the
  mundane fix underbids it, so nobody sane buys the spell. The
  corollary at body scale: healing is retail — it mends the person
  in front of the caster at standard-service prices, and nothing
  scales to a plague, a famine, or a season (the weather-worker's
  rain stone buys a day of rain, not a harvest; religion's Tergal
  option already prices exactly that). Every epidemic, famine, and
  drought card is safe from the question the ruler sheet asked.
  Companion line [PROPOSED]: NOBODY COMES BACK — necromancy
  animates bodies and interrogates echoes; it never returns the
  person (the draugr is the founder's corpse and the founder's
  temper, not the founder). Death keeps its full weight: the
  succession cluster, the elven funeral, and murder's gravity all
  stand on it.
- **THE SUPERNATURAL AFFLICTION** (the ruler sheet's healing
  question, answered the designer's way). Ordinary hurts yield to
  ordinary healing — that is why the healer is a standard service
  and no king is one bad fall from a crippled reign. But sickness
  and disability can THEMSELVES be supernatural, and the ordinary
  healing arts do not touch those. The origin list, each a rumor
  and sometimes an address: exposure to a working or a place of
  power; gifted blood's inheritance (lines that bred for the gift —
  an advantage on the road to a throne — bred its twists in with
  it); the ruler's own magical experiment gone wrong; magical
  poisoning by an enemy; a bargain's price, health traded away; a
  saint's curse (the vedic shape — the holy man's anger lands and
  stays); a witch's curse; divine punishment. Magic itself comes
  out dark and potentially costly — the intended note, and later
  gameplay (CURSED WORK below). WIRING — the residue rule
  [PROPOSED]: wealth cures the curable, so among the great the
  afflictions that PERSIST are precisely the supernatural, the
  bargained, and the divine. The ruler sheet's affliction family
  keeps its measured weights (what history counted is what magic
  could not cure), the origin stamp extends to the new origins
  ("since the working"; "cursed by the hermit he evicted"), and
  every afflicted ruler upgrades to a standing rumor: why can the
  king not be healed? Among the poor the read stays mundane —
  sickness is sickness where nobody can pay — and the two-tier read
  is itself color.

### Land-agnostic material

- **fact THE RECRUITERS.** M1 + M2 make gifted children a resource:
  talent born poor stays untrained, so wizard organizations look
  for gifted children to raise into proper wizards. The scout at
  the fair, the family paid off, the tested orphan — standing hook
  fauna in every settled land; Mortellaria's academy runs the
  formal version (its packet).
- **card THE WILD TALENT.** Great M1 and no M2: a poor peasant in a
  traumatic moment explodes a harasser with magic — and runs. A
  dangerous, half-mad fugitive with an uncontrollable power: posse,
  recruiters, witchhunters, and pity all converge, and the party
  fits on every side — hunt, rescue, or deliver to a teacher: three
  employers, one target. **[PROPOSED]** the true-positive variant
  of the WITCH-FINDER card: sometimes there IS one behind the
  burned barn, and the fraud has accidentally found a real fire.
  Orcish cousin, already canon: THE CALLED CHILD (religion) — the
  call is the wild talent in a culture with a working cure.
- **fact THE REAGENT TRADE (M3).** Rare magical resources exist and
  move: crystals, plants, specific animal parts, the wool of golden
  sheep. Compact, high-value, provenance-sensitive — natural heist
  marks and the smuggling category's luxury end (crime-layer
  wiring); the dwarven crystal concession in Ensimaa (econ) is the
  trade's visible end, the alchemists' wing (politics) a
  state-scale buyer.
- **option THE HUNT.** Witchhunting is a trade: posted work against
  a named dark caster, taken by specialists, hired adventurers, or
  soldiers when the target is loud enough. The party is the natural
  contractor — and on a dark path, in time, the natural quarry.
- **wiring CURSED WORK [PROPOSED].** The designer's gameplay
  integration — the cursed ring that grants +3 DEX and takes 1
  point of natural DEX — is the affliction doctrine sized to an
  item: power with a receipt. It slots into plan.md's parked
  non-weapon magic items row (rings/amulets reusing the weapon sp
  table); idea-level here, priced there.
- **wiring THE RULER CELLS.** The sheet's hand-set magic cells
  (spell-friendly / spell-fearing / gifted) were flagged as prime
  per-land modifier targets; these packets now supply each land's
  direction (deferred with the modifier columns, as ever).

### The organizations — the guild frame

**fact** Where wizards organize — the human and goblin lands — the
organization is GUILD-SHAPED: charters, dues, masters and
journeymen, jealously held privileges; a powerful guild among
guilds, never a fifth estate. Three local flavors below; the elves
and dwarves organize otherwise (their entries).

### Ensimaa — elves. Magic: THE INTEGRATED ART

- **fact** Much more magic, and no profession fencing it in: the
  automation, the wards, the life-extending and aesthetic magic the
  frozen ladder hoards are one continuous fabric with everyday life
  (econ and politics already carry all three). A visitor sees more
  working magic in a market morning here than in a Firascir year.
- **fact** The frozen ladder applies to the art itself: the best
  magic sits where every other advantage sits — at the top, hoarded
  by the ageless.
- **option** TEACHING THE OUTSIDER: possible, and priced twice —
  high fees AND standing in their society: a ladder of quests,
  sponsors, and interviews first (face is the currency; the
  purity-writ machinery is the natural gate). What is taught is
  real; how long the ladder runs depends on who is asking.

### Tergal — orcs. Magic: THE PRACTICE (reference)

Religion owns orcish magic whole — shamanic, intuitive, elemental:
the call, the white and black shamans, the weather-worker, taboo
law (the dedupe doctrine). This packet adds two facts and an edge:

- **fact** MAGIC IS A WEAPON: a warband counts its shaman in its
  strength, and chiefs court spirit-workers the way settled lands
  court engineers — in war the shaman is armament, and valued
  exactly so.
- **fact** MAGIC IS PERFORMED: where there is a ritual there is an
  art — the fire dance; the flicker dance, a dancer blinking in and
  out of sight or across the circle (invisibility and teleportation
  as performance). Display magic is prestige, and prestige is power
  here.
- **relation** THE OLD PRACTICE: the voodoo strand — spirits, minor
  gods, and demons dealt with by name — is shared inheritance with
  the goblins' preindustrial past. Tergal runs it at full strength,
  Gibili's margins keep its residue (its packet), and practitioners
  recognize each other across the border.

### Dvarvengrond — dwarves. Magic: THE PRACTICAL ARTS

- **fact** Primarily artificing, alchemy, and healing — pragmatic
  to the bone: magic is a trade skill inside the clan and guild
  structures, worked in workshops rather than towers, priced like
  smithing and inspected like it too. The embedded tier's center of
  mass: runes in the work, not fire from the hand. (Religion keeps
  the knockers, the dead, and the seeress.)

### Firascir — humans. Magic: THE TOWERS

- **fact** Barely an organization: grumpy old wizards in scattered
  towers, experimenting and hoarding books and knowledge, meeting
  rarely and mostly to feud. No formal teaching track exists.
- **option** THE TOWER DOOR: an offer of gold might open it;
  volunteering as the subject of a dangerous experiment opens it
  faster. An apprenticeship is personal, rare, and ends at the
  master's whim. The land with talent and no ladder — the wild
  talent's natural home ground, and the witch-finder's natural
  market (where real magic is rarest, the fraud sells best).

### Mortellaria — humans. Magic: THE ACADEMY

- **fact** The archetypical wizarding academy: a university —
  faculties, examinations, robes — with the bureaucracy and class
  discrimination of the land it serves. The gifted commoner is
  admitted (talent is talent) and made to feel the admission daily.
  The crown is patron and leash at once (the alchemists' wing reads
  naturally as an academy contract).
- **card** THE BASEMENT CHILDREN: the academy's scouts run the
  recruiter fact at scale, and the designer's hook lands here —
  neglected adopted children in the basement of the wizarding
  academy, taken young for the gift and raised by an institution
  that wanted the talent, not the child. Ward, witness, and time
  bomb in one; the wild-talent card's indoor variant.
- **fact** THE NECROMANTIC AFFINITY: necromancy keeps surfacing
  here — a cultural affinity, very controversial, and periodically
  winning some degree of acceptance before the next scandal buries
  it again. WIRING: the death-face rite makes it locally thinkable
  (religion's axis); the northern rite cites it as proof of the
  creeping heresy (the schism clock's best fuel); and the seance
  parlors' moonlighting necromancers (Gibili) trained somewhere —
  usually here.

### Gibili — goblins. Magic: THE MASTERS FOR HIRE

- **fact** Open and transactional: any master teaches — for a
  price, or for quests run on the master's errands. Buyer beware,
  constitutionally: the useless book sold dear, the master who
  vanishes with the fee, the master who delegated his dirty work
  and now prefers the errand-runner disappeared. (Dedupe: religion
  owns salvation-shaped commerce — the charm trade, the ladder
  faiths; magic owns capability-shaped commerce — teaching,
  devices, and the real necromancers behind the parlor fronts.)
- **fact** THE OLD PRACTICE'S RESIDUE: the preindustrial goblin
  past's spirit-practice — voodoo dealing with spirits, minor gods,
  demons — survives at the margins, the residue end of Tergal's OLD
  PRACTICE relation (its packet).

---

## The layers still to dump (designer's list, recommended order)

**politics → religion → monsters & fauna → magic, science &
technology.** Politics first: the authority / disposition / tension
schema (jerkify, bullies) already needs it, and half the economy
cards above lean on a political actor. (2026-08-06: BOTH halves are
dumped — THE RULER CHARACTER and THE LAND PACKETS — POLITICS above;
2026-08-07: the constitution/tension/faction records ship as drafted
at the ladder's politics session, the trait-to-card wiring is
written per card at implementation, and the per-land ruler modifier
columns stay to author.) Religion is dumped too
(2026-08-06, THE LAND PACKETS — RELIGION above): worship and rite
only, the political overlap having gone to politics; the
temple-service/penance wiring and anything hell-shaped are
deliberately deferred, per the session's directives. Monsters &
fauna is POSTPONED (2026-08-07, with science & technology — the
build implements what is dumped); when it comes it is mostly
ASSIGNMENT — the per-land encounter pools already exist; the dump
picks distinctive regional creatures and ties cards to them (the fog
necromancer pattern) — and the religion packets pre-order three (the
draugr, the knockers, Tergal's grave-made ghosts), whose cards wait
with it.
Magic is dumped too (2026-08-07, THE LAND PACKETS — MAGIC above,
taken ahead of monsters & fauna on the designer's initiative: the
scarcity limits, the stance doctrines — the supernatural-affliction
answer to the ruler sheet's healing question among them — and the
per-land organization packets). Science/technology is the layer's
remaining half; it should still
ride the land packets as flavor anchors first (elven robots, dwarven
methods, goblin gadgets are already in them) and get mechanics only
where a card demands one — and it now owes the magic packets one
boundary when it lands: which technology is magical at the core (the
embedded tier) and which is mundane (the robot question, the guns).
