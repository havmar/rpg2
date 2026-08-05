# World Simulation — content resource & framework

The working doc of THE WORLD & NPC SIMULATION thread. plan.md owns the
build order and the design-session agenda; designlog's 2026-08-05
entries own the reasoning; THIS file holds the pre-implementation
material — the record framework the design session will formalize, the
weather system sketch, and the curated land economy packets. Nothing
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

## The layers still to dump (designer's list, recommended order)

**politics → religion → monsters & fauna → magic, science &
technology.** Politics first: the design session's authority /
disposition / tension schema (jerkify, bullies) already needs it, and
half the economy cards above lean on a political actor. Religion can
fold into politics where it overlaps (the templar move, the temple as
authority) and keep only what stands alone. Monsters & fauna is
mostly ASSIGNMENT — the per-land encounter pools already exist; the
dump picks distinctive regional creatures and ties cards to them
(the fog necromancer pattern). Magic and science/technology should
ride the land packets as flavor anchors first (elven robots, dwarven
methods, goblin gadgets are already in them) and get mechanics only
where a card demands one.
