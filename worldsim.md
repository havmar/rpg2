# World Simulation — content resource & framework

The working doc of THE WORLD & NPC SIMULATION thread. plan.md owns the
build order and the design-session agenda; designlog's 2026-08-05
entries own the reasoning; THIS file holds the pre-implementation
material — the record framework the design session will formalize, the
weather system sketch, the curated land economy packets, and the ruler
character schema (the politics dump's person half, 2026-08-06). Nothing
here is shipped. When a piece ships, its rules move to rules.md and
its entry here is cut (the plan.md convention).

Register note: entries are IDEA-LEVEL, in the dev register. Final
player-facing strings are written at implementation time under
writing.md, and reviewed on the `placegen_review.txt` worksheet
pattern where wording matters.

Provenance: the packets are the designer's 2026-08-05 brainstorm,
rewritten and classified. Assistant additions are marked **[PROPOSED]**
and are cut-on-sight material — the designer curates, and fewer
hand-picked elements beat coverage.

## The record kinds

Every entry in a packet is one of five kinds — the designer's own
classification (some things always true, some always options, some
wealth-dependent, some mutually exclusive, some relations between
lands), formalized:

- **fact** — always true of the land; costs nothing at runtime. Feeds
  writing.md/dm.md color and the occasional standing modifier (elven
  murder weighs heavier; orc law is thin).
- **option** — always available: a priced-menu entry or standing scene
  material (the drug market, mercenary hiring). Its terms may read
  states.
- **state** — visible, day-stamped, changeable: the land wealth band,
  a drought, grain-scarce, strike-on, a settlement's deposit stage.
  States are what the STATE DIFF outlet shows, and what cards read
  and flip.
- **card** — the event pulse: admitting conditions (land, wealth,
  states, weather), up to five outlet effects (quest / priced menu /
  encounter / news / state flip), an optional clock. Cards live in a
  land's shuffled CRISIS DECK (drawn on need — the pact-deck pattern)
  or fire off a trigger (a state crossing, a weather roll).
- **relation** — an authored directed edge between lands (or
  settlements): who imports grain, who rents land, who pays tribute.
  Static data read at roll time; derived states fall out of it (a
  drought in Firascir sets grain-scarce in the lands its edge feeds).
  Never a traded quantity — lookups, not flows.

Mutual exclusion is handled the placegen way: exclusive slots (a land
holds ONE wealth band; a settlement ONE deposit stage), and a deck
draw never contradicts a held slot.

## The rolls

- **Land wealth** — rolled per land at worldgen on a weighted middle
  (e.g. 2d6: 2-4 CRISIS ~17%, 5-9 NORMAL ~67%, 10-12 PROSPEROUS ~17%;
  the exact die is the design session's call). Wealth is a STATE, not
  a constant — cards and seasons can move it.
- **Crisis content** — a land in CRISIS (rolled or pushed there)
  draws from its own deck. NORMAL and PROSPEROUS stay mostly
  invisible — the designer's call, and the right one: prosperity
  shows through prices, full boards, and the absence of trouble, plus
  the rare positive card (the fair, the herd drive). Crisis is where
  content lives.
- **Weather** — a day-scale roll against the current land's climate
  distribution. placegen's environment profiles already author
  climate AS a distribution ("climate is a distribution, not current
  weather") — the hook exists and has been unread until now.

## Lazy generation — what the save needs

Everything materializes on first read and persists; nothing ticks in
the background. The save grows, per land: `wealth`, `states`
(day-stamped), the shuffled crisis `deck`, and a drawn-cards record.
Rolls happen at the existing news points — settlement arrivals,
nights, travel legs — where raids, the refill, and `conquest_news`
already fire. Derived states are computed at read time off the
relations table. The one rule that keeps lazy viable: NO quantity
that needs per-day updating — states are words, clocks are day
stamps compared against the calendar (the quest-clock pattern).

**Need-to-exist settlements (the trim, settled 2026-08-05).** A land
begins with THREE settlements — one capital, one town, one village.
Further settlements exist only when something needs them to (a
relation names a rival center of power; a card needs a counterparty
port), and arrive generic, with few unique features. The authored
catalog stops being the world's initial census and becomes the
RESERVE POOL such materializations draw names and skeletons from —
places.py's lazy Site/house materialization lifted one tier.

## Asymmetry doctrine

Lands do NOT need similar amounts of material. The floor every land
needs: the wealth roll, three-plus crisis cards, one or two
relations, one flavor anchor. Above the floor, depth follows the
designer's interest — a plainer generic-fantasy land beside a
detailed one is contrast, not neglect. The overlap guard for the four
modern-flavored societies (Ensimaa, Dvarvengrond, Gibili,
Mortellaria) is the PROBLEM AXIS named at the head of each packet:
a land's troubles must come from its own axis.

---

## WEATHER (land-agnostic system; a strong first-slice candidate)

Weather is a day-scale state with outlet effects — self-contained,
cheap, and it touches every outlet at least once. Season-scale
weather (drought) is an economy state, not a day roll; it bridges
into the land packets.

- **card BIG RAIN** (temperate lands, travel/wilds days): party
  satisfaction dips (a `SAT_*` delta); a shelter roll — the party
  finds a small cabin, and the CABIN TABLE decides its owner: very
  good and helpful / offers a quest / owns something obviously
  valuable (or has just lost it to robbers) / has sinister designs
  (poison, the pot) / wants serious coin for a dry night. The table
  is the replayability; encounter + sight outlets.
- **card CAUGHT COLD** (rides BIG RAIN): a failed STR check gives a
  COLD, run as a condition — this cashes the attrition rework's
  parked DISEASE family (the conditions framework's third family). A
  second cold caught while one runs deepens to PNEUMONIA (the
  bounded-deepening rule). Small, slow, treatable: an illness-shaped
  wound.
- **fact STORM PENALTIES**: in a big storm, ranged attacks take a
  penalty and moving risks a DEX slip — one field knob and one save.
  The SNOWSTORM is the same card in Dvarvengrond's climate, outdoors.
- **card THE FOG RAISES BONES** (supernatural, rare): skeletons walk
  in fog weather. The cause is a NECROMANCER of random level
  somewhere in the land; rumor lines lead to him. Weather as a quest
  hook — encounter + news + recurrence, a landmark-lite problem with
  an address.
- **card THE FORD IS OUT** (human lands, after sustained rain): fords
  uncrossable, bridges and ferries heavily tolled — travel routing
  plus the priced menu, and the toll racket invites the vigilante
  option.
- **state DROUGHT** (season-scale): hits Firascir's and Mortellaria's
  agriculture hard, and the relations table carries it into every
  land that imports their food. Tergal's version threatens PASTURE —
  see its packet's herd spiral.
- **[PROPOSED] card WILDFIRE** (Ensimaa, only under drought): the
  forest burns — an evacuation scene, a blame question, and scarred
  Areas that show on return.
- **[PROPOSED] card DUST STORM** (Tergal, under drought): travel
  halts, herds scatter — escort and recovery work.
- **[PROPOSED] card SMOG SETTLES** (Gibili): the mills' smoke pins
  under the sky for days — satisfaction drain in town, sickness
  checks, and the mill owners' line is that the weather is at fault.

---

## THE LAND PACKETS — ECONOMY (2026-08-05)

### Ensimaa — elves. Axis: MANPOWER & DECADENCE

21st-century vibes and first-world problems, worn by an ancient race.

- **fact** The economy is rare artisanal and artistic output — small,
  precious, irreplaceable.
- **fact** Values with teeth: murder weighs even graver than among
  humans; property crime weighs lighter — the enlightened and
  long-lived can replace things. (Mechanically: the land's
  sin/heat modifiers per crime family — the jerkify machinery read
  at LAND level.)
- **fact** Dwelling anchors: hellenic white marble; giant-treehouse
  architecture; the impossibly tall and thin tower.
- **option** The art market attracts thieves and robbers — standing
  high-value marks for the crime layer, and standing guard/recovery
  work for the honest board.
- **option** The drug problem: smoking and Powder use — a standing
  market for the smuggling category.
- **state** Foreigner communities (service providers past or
  present): welcome, tolerated, or no longer welcome.
- **state** If poor: indebted to other lands for food.
- **card** An old master artisan dies; an export a town relied on can
  no longer be made — the town's income state drops, recovery hooks
  (the apprentice, the last commission, the secret).
- **card** Rented-land tensions: goblins run logging, dwarves mine
  magical crystals on elven ground. The foreigners are out of line —
  or they aren't, and the elves want them gone anyway. Two-sided
  jerkify: work exists on both sides of the eviction.
- **card** The dark clan that steals children — manpower's ugliest
  answer; a standing dark problem with an address.
- **card** Robot servants, built by elves or with goblin science —
  the manpower fix that walks; construct encounters and who-answers-
  for-it questions. *(Flagged: designer's call on tone/tech level.)*
- **relation** Food imports from Firascir and Mortellaria (drought
  there = crisis here). Land rented to Gibili (logging) and
  Dvarvengrond (crystals). Human trader enclaves. Powder inflow.

### Tergal — orcs. Axis: PASTURE & OBLIGATION

Nomadic-herding analogues: Mongolian, native American, Roman-era
Germanic, the D&D barbarian.

- **fact** Herding economy — horses, buffalo, goats; wealth moves on
  the hoof and cannot be accumulated, so gifts and obligations do the
  work of savings. Demands of favors and accusations of ingratitude
  are standing hooks. *(Flagged: designer unsure whether orcs on
  horses clash aesthetically.)*
- **fact** Law is thin: less organized action against crime — lower
  protection and heat, rougher self-help.
- **fact** Imports metal, textiles, grain; exports animals, herd
  products, and MERCENARIES.
- **option** Mercenary hiring — the export is a priced-menu entry.
- **option** Prestige smoking: unaffordable for most; chieftains
  smoke as a question of status — an expensive, severe drug market.
- **state** PASTURE and THE HERD: drought or lost grazing puts the
  tribe's herd in danger; a tribe that loses its herd turns
  desperate and very aggressive — the raiding state that reaches the
  neighboring lands.
- **card** The returned mercenary: back from abroad a level of badass
  richer — dwarven guns and steel, elven magic, goblin gadgets, human
  religion — and disrupting the order. A bully/rival seed with a
  name.
- **card** Tribute politics: another land bribes a chieftain not to
  attack; the chieftain uses the money to oppress the other clans —
  jerkify at the top, and a bridge to the politics layer.
- **card** Trading-outpost tensions: another land's post grows
  significant — protection, resentment, seizure.
- **[PROPOSED] card** The great herd drive (a positive/normal card):
  the seasonal movement of the herds — escort work, ford crossings,
  rustlers.
- **relation** Grain/metal/textile imports from the settled lands;
  raiding targets when desperate; tribute edges from frightened
  neighbors to chieftains.

### Dvarvengrond — dwarves. Axis: EXTRACTION & CLAN CLAIMS

Everything follows from mining.

- **fact** Mining economy; needs food and timber imports to live.
- **state** Per-settlement DEPOSIT STAGE (exclusive slot): normal /
  freshly found (tensions) / drying up (panic) / long dead — the
  ghost city of the poor and the scavengers, or a still-ceremonial
  seat of power.
- **card** A new deposit is found: claims collide — the discoverer,
  the clan whose territory it is, the clan strong enough to actually
  mine it. Clan conflict with work on every side.
- **card** The food caravan: incoming grain is treasure on wheels —
  rival clans, bandits, and political opponents all reach for it.
- **card** Famine by relation: the human harvest fails and the
  mountain starves — or the inversion: the mountain HAS deep
  reserves while the humans who grew the food go hungry. Price and
  conscience play.
- **card** Social justice: exploited workers, a scrip economy, the
  company shop. Strikes — rumor of a big new find, the workers want
  their share before the clan books it.
- **card** Gold rush: a flashy strike that dries up quick; the poor
  flock in, the drugs follow.
- **card** Toxic runoff crosses the border — environmental damage as
  an international incident.
- **card** Fuel crisis: is there coal under the mountain? Are the
  forests above already stripped? Incursions into elven woods; timber
  deals with the humans.
- **card** Digging too deep: the lucrative vein next to the thing
  best left sleeping — the land's landmark problem.
- **card** The half-feral goblin tribe in the deep tunnels —
  coexistence, incidents, go-betweens.
- **card** Air and water: ventilation shafts controlled by one
  powerful clan — plots and blackmail over who breathes.
- **card** The vein that sustains a whole city is running out —
  panic, denial, exodus. Its mirror: a dwarf discovers a method that
  could reopen dead veins — disruption in the other direction.
- **card** Evacuation: a community sits in the way of new deposits,
  or the underground lake is about to cave in on them.
- **card** Sulfur mined and sold to Hell. *(Flagged: designer marked
  it "controversial?" — note the pact frame already makes Hell an
  economic actor, so it is coherent; his call.)*
- **relation** Food from Firascir; timber from Firascir and Ensimaa;
  the crystal claim in Ensimaa; sulfur to Hell.

### Firascir — humans. Axis: MANORIAL OPPRESSION & THE CROWN'S DEBTS

Typical middle-ages agricultural feudal economics, played straight.

- **fact** Manorial agriculture under lords; guilds in the towns.
- **card** The lord's monopoly infrastructure: the mill, the oven,
  the wine press — use them and pay, or grind at home and answer for
  it. Jerkify's quintessence: oppression with an address.
- **card** The plague chain: plague → labor shortage → wage demands →
  wage freeze → peasant revolt. (Cards can CHAIN by setting the
  states the next card admits on.)
- **card** The famine chain: bad harvest → price gouging → bread
  revolt.
- **card** The king's war debts: orcish skirmishes → overtaxation;
  orcish mercenaries hired (the Tergal edge); the indebted crown
  turns on the merchant-paladin order (the templar move); or on a
  merchant city (the hansa-against-the-crown shape).
- **card** The annual fair: chaos, enforcers, the pie-powder court —
  a positive/normal card with crime and comedy in it.
- **card** Small frauds in hard times: counterfeit coin, watered ale,
  sawdust bread — petty-crime color and market events.
- **card** Robber barons and excessive tolls — the toll-reeve worked
  example (plan.md) lives here.
- **option** Smuggling against guild monopolies.
- **relation** THE GRANARY: grain exports to Ensimaa, Dvarvengrond,
  and Gibili — a Firascir drought is everyone's problem. Timber to
  Dvarvengrond. Hires Tergal mercenaries when the crown fights.

### Mortellaria — humans. Axis: FINANCE & THE ABSOLUTIST STATE

Baroque analogue; mediterranean agriculture; gold at the center.

- **fact** Finance exists here and nowhere else: corporate shares,
  banks, paper money, credit. One abstract tropical COLONY offstage.
- **fact** Enticing villas and palaces — the crime layer's richest
  marks live here.
- **option** Banking: paper-to-gold conversion, credit — priced-menu
  entries.
- **option** Smuggling against the centralized state's high tariffs.
- **card** Paid in paper: the PC receives double payment in paper
  money — worth face value only at a bank at the end of a dangerous
  road. A quest shape no other land can offer.
- **card** The tax farmer: the state needs an army and sells the
  right to squeeze a province — jerkify with a ledger.
- **card** Counterfeiting of paper money — crime category and market
  event both.
- **card** Occupation of Gibili for resources — the big card; ties
  into the war layer's machinery.
- **[PROPOSED] card** The bank fails: a run, frozen deposits, paper
  suddenly worth its weight — and the party's savings are wherever
  they left them.
- **relation** The colony (abstract); firearms imports from Gibili;
  food exports north; covetous eyes on Gibili.

### Gibili — goblins. Axis: LABOR vs CAPITAL, NO STATE

Sillon industriel analogue: crowded, industrial, chaotic.

- **fact** Smoke, steel mills, glassworks, textile mills. No state
  power to speak of — corporate power only; law is company
  enforcers.
- **fact** Firearms production, largely for Mortellaria.
- **option** The gadget market; the arms trade.
- **state** STRIKE / UPRISING; under-occupation.
- **card** Worker uprising — the town stops, both sides hire.
- **card** Unions against factory owners, with pistolerismo-style
  company police — jerkify two-sided: pick whose thug you are, or
  whose thug you break.
- **card** The firearms contract: a convoy for Mortellaria worth
  guarding, robbing, or sabotaging.
- **card** Foreign occupation by Mortellaria for resources — the
  other end of Mortellaria's big card.
- **relation** Arms to Mortellaria; the logging concession in
  Ensimaa; science lent to elven robot-making; food imports.

---

## THE RULER CHARACTER — the politics dump, part 1: the person (2026-08-06)

The politics layer's first half: WHO holds power, as a rollable
character schema. The other half — authority KIND, standing tension,
and the wiring of a person's traits into cards — stays with the
design session's identity-schema agenda. Provenance: the designer's
historical-monarch trait catalog (~130 raw entries across ten
headings), merged and classified this session; a parallel session is
coding a dataset of real European monarchs against this sheet to
produce the probability column. This section fixes only the SHAPE —
no probabilities, by directive.

What a ruler's traits are FOR — the merge criterion used throughout:
political land identity, possible PC interaction, and rumor fuel. A
trait that cannot show up through one of the six outlets was cut or
merged (the characteristic criterion applied to people).

### The shape

- **Axes and flags.** An AXIS is two named poles around an unnamed
  neutral middle (doting — silence — harsh at home); a FLAG is one
  named pole and silence (an art patron exists; a hater-of-arts does
  not). Neutral is NEVER mentioned in play — neutral is silence.
- **The trait list is words.** A rolled character stores its named
  poles and flags in one flat `traits` list — pole names are unique
  across the whole vocabulary, so a card or rumor line can admit on
  a bare word (`"cruel" in ruler["traits"]`). Only two companion
  keys exist: derived `heart` (below) and `puppeteer` (only beside
  `puppet`).
- **Count.** Rulers carry 3-5 named traits, center-weighted on 4;
  lesser named authorities (a lord, a sheriff, a guild master) carry
  1-3, center 2. The roll is per-axis independent against the
  probability sheet, then CLAMPED to the window: short characters
  top up with weighted draws from the unrolled axes, long ones drop
  overflow at random. Because the dataset's marginals describe real
  monarchs — who each support far more than four adjectives — the
  sheet's percentages pass through one global scale knob, tuned so
  the expected named count lands near the window's center. The
  dataset supplies RELATIVE frequency; the knob supplies volume.
- **Scope.** Nearly the whole vocabulary applies to ANY authority —
  deliberate, so one sheet rolls a king, a border lord, and a
  toll-sheriff (the settlement authority the identity schema needs).
  The `crown` scope marks the exceptions; the finding is that there
  is almost none (itinerant alone).
- **Extreme steps.** A pole may carry one rarer EXTREME variant that
  occupies the same axis slot (a zealot IS devout, further out). The
  sheet demonstrates the mechanism once — faith's zealot row — and
  extremity is otherwise priced by the probability column alone:
  the dramatic words stay in the vocabulary, their cells just stay
  small.
- **Tribes later.** Orcish (and any tribal) societies will reword or
  zero some axes; per-race probability columns are the intended
  mechanism, deferred by directive. The dataset's European monarchs
  fill the HUMAN-CROWN baseline column.

### Range doctrine (2026-08-06, designer directive)

The game has left generic heroic fantasy — named wounds, crime that
pays, realistic economic trouble — and the sheet follows: its job is
MEMORABLE, VIVID rulers, so the vocabulary keeps the widest range
the catalog allows, the scandalous and the clinical included. A king
who starves himself, or who tried to die by his own hand, is exactly
the rumor that is remembered. Rarity is the probability column's
whole job — a rare entry gets a small cell (the designer plans a ~1%
floor for rare things), never deletion — and no register or writing
pass may collapse specific vivid entries into a safer generic word.
This is range, not grimdark: writing.md's restraint governs how a
line is DELIVERED, never which facts may exist (its Tone section
says the same since this directive).

### Consistency — three rules, no engine

1. **One pole per axis** — structural; the roll picks at most one.
2. **Moral tags.** Nine poles are tagged `good` or `dark` (marked in
   the sheet). A character never holds both a good-tagged and a
   dark-tagged trait: honorable and harsh-at-home do not meet in one
   person, however historical the combination — a four-word
   character must read as ONE person. Untagged traits mix freely
   with either side (grasping + honorable is a real king; lecherous
   + merciful is fine). `heart` is DERIVED, never rolled: any
   dark-tagged trait makes it `dark`, any good-tagged `good`,
   neither `mixed`. Heart stays hidden in play, and it is the crime
   layer's desert anchor (jerkify: sin books lighter against the
   dark-hearted crown, heavier against the good one).
3. **Row exclusions.** A handful of `never with` notes on the flag
   sheet (gifted x spell-fearing), plus one cap: at most THREE of
   the affliction family on one character. Within the cap, combos
   are content, not noise — melancholy + sleepless + drunkard reads
   as one story.

Implementation note for the roll: evaluate axes in a per-character
shuffled order, so skip-on-conflict does not systematically starve
the sheet's later rows.

### The fill sheet — axes

One row per axis; each named pole gets a probability cell; neutral is
the unwritten remainder (100 - %A - %B). The dataset session codes
each monarch per axis as A / neutral / B and each flag as yes/no; the
cell is the share of monarchs. Tags ride the pole word.

| axis      | pole A            | %A | pole B               | %B | scope |
|-----------|-------------------|----|----------------------|----|-------|
| ambition  | ambitious         |    | content              |    | any   |
| industry  | tireless          |    | idle                 |    | any   |
| nerve     | bold              |    | craven               |    | any   |
| trust     | trusting          |    | suspicious           |    | any   |
| mercy     | merciful (good)   |    | cruel (dark)         |    | any   |
| honor     | honorable (good)  |    | faithless (dark)     |    | any   |
| purse     | austere           |    | lavish               |    | any   |
| greed     | openhanded (good) |    | grasping             |    | any   |
| faith     | devout            |    | godless              |    | any   |
| faith+    | zealot (extreme step: counts as devout) | | |    | any   |
| rule      | lawful (good)     |    | arbitrary (dark)     |    | any   |
| custom    | traditionalist    |    | reformer             |    | any   |
| door      | accessible        |    | walled               |    | any   |
| appetites | chaste            |    | lecherous            |    | any   |
| table     | glutton           |    | eats nothing         |    | any   |
| hearth    | doting (good)     |    | harsh at home (dark) |    | any   |
| strangers | welcoming         |    | race-proud           |    | any   |
| sorcery   | spell-friendly    |    | spell-fearing        |    | any   |
| war       | martial           |    | unblooded            |    | any   |
| wits      | brilliant         |    | dull                 |    | any   |
| looks [PROPOSED] | striking   |    | ill-favored          |    | any   |

### The fill sheet — flags

| flag         | % | scope | never with    |
|--------------|---|-------|---------------|
| charismatic  |   | any   |               |
| witty        |   | any   |               |
| cultivated   |   | any   |               |
| tinkerer     |   | any   |               |
| populist     |   | any   |               |
| nepotist     |   | any   |               |
| puppet       |   | any   |               |
| itinerant    |   | crown |               |
| trade-minded |   | any   |               |
| gifted           |   | any   | spell-fearing |
| sickly           |   | any   |               |
| crippled         |   | any   |               |
| falling-sickness |   | any   |               |
| drunkard         |   | any   |               |
| melancholy       |   | any   |               |
| manic            |   | any   |               |
| sees visions     |   | any   |               |
| delusions        |   | any   |               |
| death-wish       |   | any   |               |
| failing mind     |   | any   |               |
| sleepless        |   | any   |               |

Affliction cap: at most three of the affliction family (sickly,
crippled, falling-sickness, drunkard, glutton, eats nothing,
melancholy, manic, sees visions, delusions, death-wish, failing
mind, sleepless) on one character.

### The vocabulary, annotated (the merge ledger)

The dataset session codes monarchs against THIS list; each entry
names what it absorbed from the raw catalog and what it feeds. Pole
words are idea-level — the writing.md pass happens at implementation.

- **ambition** (ambitious / content): absorbs expansionist,
  persistent claimant, warlike-as-policy; defensive-minded and
  peace-seeking fold into content. Feeds the war layer's aggressor
  logic, border cards, usurpation rumor.
- **industry** (tireless / idle): absorbs diligent, disciplined,
  hands-on, micromanaging; indolent, neglectful. Whether the realm
  is actually governed; idle beside any strong minister is a
  who-rules story without needing the puppet flag.
- **nerve** (bold / craven): absorbs courageous, personally
  valorous; timid. Reckless/cautious commander are combo readings
  with martial, not entries. How the ruler answers a threat —
  including one the PC delivers.
- **trust** (trusting / suspicious): absorbs extreme suspiciousness
  (the far end of the same pole); naive folds into trusting, with
  dull nearby when rolled. Purge and spy rumor, betrayal cards,
  whether the PC's word is taken.
- **mercy** (merciful / cruel): absorbs vindictive, ruthless,
  tolerates-suffering. Jerkify desert, punishments as sights,
  revolt cards.
- **honor** (honorable / faithless): absorbs oath-breaking,
  deceitful, scapegoating on the faithless side; loyal-to-servants
  on the honorable side. Whether a promised reward is real — the
  most directly PC-facing axis on the sheet.
- **purse** (austere / lavish): absorbs extravagant, profligate,
  propagandistic display; fiscally prudent. Treasury cards (debt,
  the tax turn), what the court LOOKS like on arrival.
- **greed** (openhanded / grasping): absorbs generous patron;
  corrupt/venal, taxing aggressively. Deliberately separate from
  purse: purse is what he spends on himself, greed is what he takes
  from others — the miser-taker and the spendthrift-giver are both
  real. Bribery terms on the priced menu, reward flavor. Grasping
  is left untagged on purpose: the honest miser king exists.
- **faith** (devout / godless; extreme step: zealot): absorbs
  personally devout, publicly pious, providential; religiously
  indifferent. Zealot absorbs zealous and religious dogmatism.
  Clerical deference/assertion is cut as derived (faith x industry
  covers the readable cases). Temple authority relations, the
  templar move, persecution cards — and hell-pact resonance.
- **rule** (lawful / arbitrary): absorbs legalistic; autocratic,
  tyrannical (tyranny = arbitrary + cruel, a combo reading). What
  justice the PC faces; seizure and rights cards.
- **custom** (traditionalist / reformer): absorbs culturally
  conservative/innovative, centralizing/decentralizing,
  institution-building, reforming. Strike, revolt, and new-court
  cards; which faction hates him.
- **door** (accessible / walled): absorbs accessible; secretive.
  The most mechanical axis here: an accessible ruler is an audience
  the PC can simply GET; a walled one makes the audience itself a
  quest.
- **appetites** (chaste / lecherous): absorbs sexually restrained;
  licentious. Scandal rumor, bastard claimants, the succession
  mess; chaste is notable in the other direction (no heir coming).
- **table** (glutton / eats nothing): absorbs disordered eating,
  widened to both extremes — the gorging court and the fasting
  crown are equally strong rumor. Feasts as sights, the taster's
  job, the physician's despair.
- **hearth** (doting / harsh at home): absorbs devoted spouse,
  affectionate parent; abusive spouse, sexual/emotional jealousy,
  neglectful parent. The catalog's whole home-life cluster in one
  axis — rumor fuel both ways, the estranged-queen card.
- **strangers** (welcoming / race-proud) **[PROPOSED]**: new,
  world-specific. Ensimaa's foreigner-community state already needs
  it, and a mixed party stands before every throne — this axis
  decides how court receives them.
- **sorcery** (spell-friendly / spell-fearing): the requested magic
  entry, shaped as a stance axis because the PC IS always a caster —
  a spell-fearing court is a direct PC problem, a spell-friendly one
  a door. Absorbs heterodox (its occult reading). Witch-trial
  cards, the court wizard's standing.
- **war** (martial / unblooded): absorbs martial interest, military
  strategy, battlefield command; chivalric is a combo reading
  (martial + honorable). Who leads the waves in the field, duel
  challenges, how conquest reads.
- **wits** (brilliant / dull): the requested dumb/smart entry.
  Absorbs the whole Competence heading (administrative, political,
  diplomatic, fiscal, military-strategic, judicial, crisis,
  personnel, public performance as ability), politically astute,
  shrewd, strategically minded, patronage-skilled. Brilliant + idle
  and dull + tireless are the delicious combos.
- **looks** (striking / ill-favored) **[PROPOSED]**: the catalog
  has no appearance entry at all, yet epithet history runs on it
  (the Fair, the Hunchback). Pure rumor and epithet fuel; cheap.

Flags:

- **charismatic**: absorbs charismatic, communication and public
  performance as presence. Loyalty that survives crisis; crowds and
  armies love him.
- **witty**: absorbs humorous. Cheap court color; the one flag kept
  purely for voice.
- **cultivated**: absorbs intellectual, well-educated, curious,
  art patron, learning patron, linguistically gifted. One flag —
  the game does not need to distinguish the reader from the builder
  of libraries. Commissions, elven regard.
- **tinkerer**: absorbs technically minded. Kept apart from
  cultivated because engines and guns are their own flavor in this
  world (Gibili, the dwarves). Gadget and works cards.
- **populist**: absorbs populist, hostile to entrenched elites. The
  commons shield him; the lords plot.
- **nepotist**: absorbs nepotistic, factional, favorite-prone. The
  hated kinsman in office — standing rumor with an address.
- **puppet** (+ `puppeteer`): absorbs favorite-dependent,
  minister-dependent, elite-captured, easily influenced, dominated
  by mother. The puppeteer field carries the color (the queen
  mother, the chancellor, the favorite, the high priest) and is the
  REAL door for PC dealings; who-rules rumor.
- **itinerant** [crown]: governs from the saddle — the one
  crown-scope entry. The king can be MET (or robbed) on the road;
  his arrival is a settlement event.
- **trade-minded**: absorbs commercially minded. Charters, ports,
  tariffs, banks — this world runs on its economy packets, so the
  stance earns a flag.
- **gifted** (never with spell-fearing): the crowned caster — rare
  and world-bending by design; a small cell.
- **sickly**: absorbs chronic physical illness, frail health,
  chronic pain, recurrent incapacitation. The game does not
  distinguish illness from frailty — the rumor is the same: the
  succession clock is ticking. Robust health is the neutral, cut.
- **crippled**: absorbs physical disability, split out of sickly by
  directive — a lame leg is not a sick body, and the epithet is
  different. The withered arm, the lame king; what he cannot do and
  what the court pretends not to see.
- **falling-sickness**: absorbs neurological episodes and seizures,
  under the historical name. A fit before the full court is a
  scene; "God touches him" and "he is cursed" are both live rumors.
- **drunkard**: absorbs alcohol misuse, drug or medication
  dependence. Court sights, indiscretion, a lever for others.
- **melancholy**: absorbs depressive symptoms, pathological
  anxiety, severe grief reaction, trauma symptoms. The shut-away
  crown, the black months, audiences refused.
- **manic**: absorbs manic or unusually elevated episodes. Grand
  schemes, sudden works, spending fevers; rolled beside melancholy
  it is the unstable crown (severe mood instability lives in that
  pair, not in an entry of its own).
- **sees visions**: absorbs hallucination-like experiences. In this
  world the best kind of ambiguous — madness, or a true seeing?
  Cards can play it either way; the fog necromancer pattern has a
  royal cousin here.
- **delusions**: absorbs delusional or psychotic symptoms — the
  fixed false belief: the king who is made of glass, the chosen of
  God, the poisoned bloodline. (Persecutory shades border
  suspicious's far end; both may roll.)
- **death-wish**: absorbs self-harming or suicidal behavior. "The
  priests hushed what happened in the tower" — grave, rare, and
  exactly the rumor that is remembered.
- **failing mind**: absorbs cognitive decline, memory impairment.
  Forgets faces, repeats yesterday's audience; the court governs
  around him — and someone answers in his name.
- **sleepless**: absorbs sleep disturbance. Lamps burn in the
  king's window all night; audiences at dawn or not at all.

Two notes on the affliction family. Any affliction may be stamped
with a dated origin at generation time ("since the fever", "since
the queen died") — this absorbs illness-associated personality
change and gives the rumor its story for free. And MAD is a
READING, not a rolled word: the fiction may crown anyone "the Mad
King" over sees visions, delusions, or the melancholy-manic pair,
but the specific word is what rolls and what cards admit on —
uncollapsed by directive; a card that wants the whole family admits
on any-of.

### Cut from the catalog

- **As derived combos, not entries:** tyrannical (arbitrary +
  cruel), chivalric (martial + honorable), reckless and cautious
  commander (nerve x martial), clerical deference/assertion (faith
  x industry), naive (trusting + dull).
- **As too managerial to show through any outlet:** consultative /
  autocratic (the readable ends live in rule and puppet),
  court-focused, centralizing / decentralizing, patronage-skilled,
  institution-building (folded into reformer), fortification-minded.
- **As neutral defaults:** robust health, providential (devout
  color), propagandistic (lavish color).
- **Moved to circumstances:** fratricidal — history, not
  disposition; see below.

### Circumstances, not traits

The catalog's footer list stands as the non-trait record: age at
accession, mode of accession, strength of initial legitimacy,
minority or regency, religious division, quality of ministers,
captivity or exile. Two additions:

- **succession state** (secure / disputed / heirless) **[PROPOSED]**
  — the most card-rich single fact about any crown, and it reads
  appetites, hearth, and sickly for free.
- **kin-blood accession** — absorbs fratricidal: "took the throne
  over his brother's body" is a mode of accession, and better rumor
  than any disposition word.

### What this does NOT decide

- Probabilities — the parallel monarch-dataset session fills the
  sheet; this section only fixed the rows.
- The wiring — which cards admit on which words, the authority
  kind/tension schema, and whether the land RULER notable (the
  first intended consumer, doing nothing since 2026-07-12) rolls
  this at worldgen: the design session's business.
- Ordinary dict NPCs stay BLANK — givers and service faces carry no
  traits (spec B's rollback stands; the characteristic criterion:
  rulers are card-backed, givers are not). The schema serves the
  authority tier and named actors that cards create. The PC's own
  blank sheet remains an open question.

---

## The layers still to dump (designer's list, recommended order)

**politics → religion → monsters & fauna → magic, science &
technology.** Politics first: the design session's authority /
disposition / tension schema (jerkify, bullies) already needs it, and
half the economy cards above lean on a political actor. (2026-08-06:
politics' PERSON half is dumped — THE RULER CHARACTER above; the
authority-kind/tension half and the trait-to-card wiring remain.) Religion can
fold into politics where it overlaps (the templar move, the temple as
authority) and keep only what stands alone. Monsters & fauna is
mostly ASSIGNMENT — the per-land encounter pools already exist; the
dump picks distinctive regional creatures and ties cards to them
(the fog necromancer pattern). Magic and science/technology should
ride the land packets as flavor anchors first (elven robots, dwarven
methods, goblin gadgets are already in them) and get mechanics only
where a card demands one.
