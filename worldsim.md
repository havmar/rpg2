# World Simulation — content resource & framework

The working doc of THE WORLD & NPC SIMULATION thread. plan.md owns the
build order — since 2026-08-07 the worldsim-build ladder, the
monolithic design session dissolved and everything settleable settled
in plan.md's rulings block; designlog's 2026-08-05..09 entries own
the reasoning; THIS file holds what is still UNBUILT — the ruler
character schema (the politics dump's person half, 2026-08-06), and
the politics land packets with the constitution/tension/faction frame
(the dump's power half, same day), and the religion land packets (the
worship dump, same day), and the magic land packets (the arcane dump,
2026-08-07). When a piece ships, its rules move to rules.md and
its entry here is cut (the plan.md convention) — the record framework
went that way on 2026-08-07 and the six ECONOMY land packets on
2026-08-09, and the summary of what they became now heads this file so
the packets below can be read against it.

Register note: entries are IDEA-LEVEL, in the dev register. Final
player-facing strings are written at implementation time under
writing.md, and reviewed on the `placegen_review.txt` worksheet
pattern where wording matters.

Provenance: the packets are the designer's 2026-08-05 brainstorm,
rewritten and classified. Assistant additions are marked **[PROPOSED]**;
on 2026-08-07 the designer adopted the [PROPOSED] set WHOLESALE —
implement it like everything else — so the marks (here and in every
later section) are provenance only now, not a cut list.

## The frame, the weather and the economy floor SHIPPED — what the packets are written against

The five record kinds, the wealth roll, the crisis deck, the relations
table and the lazy day-stamped rolls are BUILT (2026-08-07); so is the
whole WEATHER system this file used to sketch (2026-08-08); and so, since
2026-08-09, is the ECONOMY FLOOR — the three outlets the frame carried
but did not apply, the six econ packets' cards and edges, and the card
CHAINS. It is all `worldsim.py`, with the played rules in rules.md's
*The World Layer*, *Weather* and *The Economy Floor* and the code index
in develop.md. What was cut from here is there; what remains below is the
content still to author against it.

The API facts an entry in this file needs to know:

- **A card is `worldsim.card(key, name, land, ...)`** — admitting
  conditions (`wealth`, `states`, `without`, `weather`, `wet`/`dry`), up
  to five outlet effects (`quest` / `menu` / `encounter` / `news` /
  `state`), and an optional day-stamp clock (`days`). ALL FIVE are
  applied now. A state effect is
  `{"set", "while", "clear", "slot", "wealth", "wealth_while"}` — what
  a card SETS outlives it, what it sets WHILE it stands comes off with
  it, and slot members are exclusive.
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

## THE RULER CHARACTER — the politics dump, part 1: the person (2026-08-06)

The politics layer's first half: WHO holds power, as a rollable
character schema. The other half splits (2026-08-07): authority KIND
and standing tension at the settlement tier are JERKIFY — postponed
past the worldsim build for their own design session (plan.md) — and
a person's traits wire into cards at implementation, card by card,
where the packet text names them. Provenance: the designer's
historical-monarch trait catalog (~130 raw entries across ten
headings), merged and classified 2026-08-06; the probability column
landed the same day from the parallel dataset session — 734 European
rulers coded, 443 carrying at least one trait at the kept resolution
(the traitless discarded as minor), max 14 traits per ruler, average
3, percentages rounded up. Those numbers are the weights in the
sheets below: the HUMAN-CROWN / FIRASCIR BASELINE. Other lands and
races get modifier columns later.

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
- **The pool roll (2026-08-06, dataset in hand — supersedes the
  per-axis roll and its scale knob).** All named entries form ONE
  weighted pool; the weight is the sheet number, the pool totals
  357 (the magic cells included). A ruler DRAWS THREE: d357 against
  the cumulative list, and between draws the drawn word, its axis
  opposite, and its never-with partners leave the pool while the
  die shrinks by their weights (Consistency below) — so three draws
  always land three distinct compatible words. Lesser named
  authorities (a lord, a sheriff, a guild master) draw TWO from the
  crown-less pool (355). The identity that makes this faithful: the dataset's average
  trait count was 3, so three weighted draws reproduce the measured
  per-trait marginals almost exactly (ambitious lands on ~27% of
  rolled rulers; the dataset said 32%). If rulers feel thin in
  play, a fourth draw is the one knob — it scales every marginal by
  4/3.
- **The floor.** Vivid entries the dataset zeroed — godless, eats
  nothing, sees visions — enter the pool at weight 1: the range
  doctrine's ~1% floor made real. To fatten the rare tail later,
  RAISE the floor at full resolution (+2, +3); never compress the
  pool to a d100 — re-rounding either deletes the tail or triples
  it, and code reads a 357-list as easily as a 100-list.
- **The magic cells are hand-set** — history offers no data:
  spell-friendly 2, spell-fearing 3, gifted 1 **[PROPOSED]**.
  Witch-fear slightly ahead of patronage in a plain human land, the
  crowned caster at the floor; all three are prime per-land
  modifier targets.
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

### Consistency — two rules, a shrinking pool, no engine

1. **One pole per axis.** Enforced by the draw itself: a drawn
   trait AND its axis opposite leave the pool, and their weights
   leave the die — draw ambitious on the d357 and ambitious 32 +
   content 1 are gone; the next roll is a d324. Zealot occupies the
   whole faith axis: drawing it removes devout and godless;
   drawing devout removes godless and zealot.
2. **Row exclusions, the same way.** A drawn trait also removes
   whatever its `never with` column names (gifted removes
   spell-fearing and vice versa); a character holding three of the
   affliction family removes the rest of that family; and
   out-of-scope entries never enter the die at all — a village
   sheriff rolls the crown-less pool (355). Within the cap,
   affliction combos are content, not noise — melancholy +
   sleepless + drunkard reads as one story.

**Moral tags are bookkeeping now, not law (2026-08-06, designer
call).** Nine poles still carry `good` or `dark` in the sheet, but
they forbid NOTHING — an honorable cruel king is a contradiction,
and contradictions can work; the range doctrine would rather have
him than not. The tags exist only to derive `heart`: dark-tagged
traits present and no good ones → `dark`; good and no dark →
`good`; both or neither → `mixed` (the contradictory ruler reads
as complicated, which is what mixed means). Heart stays hidden in
play, and it is the crime layer's desert anchor (jerkify: sin
books lighter against the dark-hearted crown, heavier against the
good one).

The shrinking pool is exactly equivalent to rerolling invalid
draws against the full die; implement whichever is cleaner. The
removals terminate by construction and keep every remaining weight
in its measured proportion.

### The fill sheet — axes

One row per axis; the number beside each pole is its measured share
of the 443 traited rulers (rounded up), serving directly as its pool
weight. Neutral is the unwritten remainder. Tags ride the pole word;
`fl` marks a dataset zero entered at the floor, `hs` a hand-set
magic cell. All weights across both sheets sum to 357 — the pool.

| axis      | pole A            | w  | pole B               | w  | scope |
|-----------|-------------------|----|----------------------|----|-------|
| ambition  | ambitious         | 32 | content              | 1  | any   |
| industry  | tireless          | 15 | idle                 | 2  | any   |
| nerve     | bold              | 15 | craven               | 1  | any   |
| trust     | trusting          | 2  | suspicious           | 7  | any   |
| mercy     | merciful (good)   | 3  | cruel (dark)         | 10 | any   |
| honor     | honorable (good)  | 2  | faithless (dark)     | 2  | any   |
| purse     | austere           | 5  | lavish               | 5  | any   |
| greed     | openhanded (good) | 2  | grasping             | 2  | any   |
| faith     | devout            | 31 | godless              | 1 fl | any |
| faith+    | zealot (extreme step: counts as devout) | 17 | | | any |
| rule      | lawful (good)     | 12 | arbitrary (dark)     | 14 | any   |
| custom    | traditionalist    | 7  | reformer             | 25 | any   |
| door      | accessible        | 2  | walled               | 3  | any   |
| appetites | chaste            | 2  | lecherous            | 3  | any   |
| table     | glutton           | 2  | eats nothing         | 1 fl | any |
| hearth    | doting (good)     | 3  | harsh at home (dark) | 1  | any   |
| strangers | welcoming         | 4  | race-proud           | 3  | any   |
| sorcery   | spell-friendly    | 2 hs | spell-fearing      | 3 hs | any |
| war       | martial           | 28 | unblooded            | 1  | any   |
| wits      | brilliant         | 18 | dull                 | 1  | any   |
| looks     | striking          | 3  | ill-favored          | 1  | any   |

### The fill sheet — flags

| flag             | w    | scope | never with    |
|------------------|------|-------|---------------|
| charismatic      | 7    | any   |               |
| witty            | 2    | any   |               |
| cultivated       | 14   | any   |               |
| tinkerer         | 1    | any   |               |
| nepotist         | 1    | any   |               |
| puppet           | 4    | any   |               |
| itinerant        | 2    | crown |               |
| trade-minded     | 3    | any   |               |
| gifted           | 1 hs | any   | spell-fearing |
| sickly           | 7    | any   |               |
| crippled         | 4    | any   |               |
| falling-sickness | 3    | any   |               |
| drunkard         | 2    | any   |               |
| melancholy       | 3    | any   |               |
| manic            | 1    | any   |               |
| sees visions     | 1 fl | any   |               |
| delusions        | 3    | any   |               |
| death-wish       | 1    | any   |               |
| failing mind     | 2    | any   |               |
| sleepless        | 1    | any   |               |

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
  is left untagged on purpose: taking hard is not dark-hearted by
  itself.
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
  institution-building, reforming — and, since the dataset pass,
  populist's one usable idea: a reformer's natural enemies are the
  entrenched elites, and charisma decides whether the commons
  shield him. Strike, revolt, and new-court cards; which faction
  hates him.
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
- **strangers** (welcoming / race-proud): world-specific, adopted
  with the dataset (the dataset's column name for race-proud is
  `exclusive` — same slot). Ensimaa's foreigner-community state
  already needs it, and a mixed party stands before every throne —
  this axis decides how court receives them.
- **sorcery** (spell-friendly / spell-fearing): the requested magic
  entry, shaped as a stance axis because the PC plays a caster —
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
- **looks** (striking / ill-favored): adopted with the dataset —
  the catalog had no appearance entry, yet epithet history runs on
  it (the Fair, the Hunchback). Pure rumor and epithet fuel; cheap.

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
- **As blander than its neighbors (2026-08-06, dataset in hand):**
  populist — zero hits in 443 rulers, and on inspection everything
  it would do in play is reformer + charismatic wearing different
  clothes; its one usable idea moved into custom's annotation. The
  designer's suspicion, confirmed.
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

- Per-land and per-race probabilities — the sheet carries the
  human-crown / Firascir baseline only; the other lands' modifier
  columns and the tribal rewording are still to author.
- ~~The wiring~~ — settled 2026-08-07 (plan.md's rulings): the land
  RULER notable (the first intended consumer, doing nothing since
  2026-07-12) DOES roll this at worldgen, at the ladder's politics
  session; card admits are written per card at implementation; the
  settlement authority kind/tension schema is jerkify's, postponed
  past the build.
- Ordinary dict NPCs stay BLANK — givers and service faces carry no
  traits (spec B's rollback stands; the characteristic criterion:
  rulers are card-backed, givers are not). The schema serves the
  authority tier and named actors that cards create. The PC's own
  blank sheet remains an open question.

---

## THE LAND PACKETS — POLITICS — the politics dump, part 2: the power (2026-08-06)

THE RULER CHARACTER above is WHO holds power; this is what he sits
on and who is pulling at it — authority kind, standing tension, and
the political event material: the second half of the design
session's identity-schema agenda (plan.md). Provenance: the
designer's 2026-08-06 politics brainstorm — the per-land dump, the
120-entry three-era addendum (medieval / baroque / industrial, four
layers each), and the regrounded elven pass — aggressively cut,
merged, and rewritten here: roughly half kept, a quarter folded
into other entries, a quarter cut (the cut list and its rescue
candidates are in the session report, designlog 2026-08-06 D). The
historical anchor rides each entry in parentheses as design
shorthand; player-facing words get the writing.md pass at
implementation (sheriff, not reeve — the CRPG-vocabulary rule).
Assistant additions are marked **[PROPOSED]** (adopted wholesale
2026-08-07 — the intro's ruling).

**The selection doctrine (the designer's framing).** A packet is a
POOL, not a description. The stereotype is the constant — feudal
humans, herding orcs, mining dwarves — and worldgen ROLLS the
color, so no single land carries all its weirdness in one
playthrough, and the same land comes up a different flavor of
itself across playthroughs. Three pieces make that concrete, all
adopted as drafted 2026-08-07 (plan.md's rulings) — they ship at the
ladder's politics session; the settlement authority tier stays out
(jerkify, postponed):

- **The constitution slot** — one per land, exclusive (the
  wealth-band pattern), rolled at worldgen on a default-heavy die.
  Defaults per the designer: Firascir DECENTRALIZED FEUDALISM,
  Mortellaria ABSOLUTISM, Ensimaa CONSTITUTIONAL MONARCHY; the
  maximally decentralized option for a crowned land is
  ARISTOCRATIC ANARCHY — the Polish shape: elective crown, magnate
  veto, rule of independent barons (carried in Firascir's packet).
  The other three lands' defaults read from their packets. Cards
  never flip the slot; the rare card that would (the junta, the
  commune) says so explicitly.
- **The tension roll** — each packet lists STANDING TENSIONS: two
  named blocs and what they fight over. A land rolls ONE at
  worldgen (**[PROPOSED]** a second under CRISIS wealth), and only
  cards whose tension holds enter the land's crisis deck — the
  SAME deck as the econ cards, no second pile. Political cards
  admit on tensions the way econ cards admit on states; the
  tension is the gate that keeps the pool wide and each rolled
  world specific.
- **Factions and edges** — the in-land counterpart of `relation`:
  the rolled tension implies a small faction cast, and authored
  directed verb edges carry the wiring. The designer's edge
  sketch, kept as the worked model (a crowned frame over Gibili's
  cast — the formalism must serve both): crown INFLUENCES
  aristocracy; crown FUNDS secret police; secret police INFILTRATE
  anarchists; anarchists SABOTAGE steel barons; steel barons LOBBY
  crown and HIRE mercenaries; mercenaries GUARD steel barons.
  Cards admit on an edge; the notables cast (quests.py's RULER /
  SAGE / WILDCARD) supplies faction faces for free.

**What politics owns vs the econ packets.** Econ owns flows,
prices, and livelihoods; politics owns right, office, and
allegiance. Where a dump entry was an econ card wearing a crown —
the lord's mill (banalities), the company town and its scrip,
pistolerismo policing, guild monopolies, the smuggling markets —
it stays in the econ packet and is referenced, not duplicated.

### The war layer's feed (land-agnostic)

story.py rolls an aggressor and wages waves; conquest.py already
does tribute and raids. What the war lacks is the WHY line and the
endings — cheap to add, high rumor value.

- **CASUS BELLI pool** (rolled beside the aggressor; feeds herald
  and news lines): border dispute; broken betrothal; succession
  claim pressed from abroad; religious conflict; embargo answered;
  foreign merchants' goods seized; **[PROPOSED]** a harbored
  pretender, a bought wardship enforced, prospectors over the
  border (the Dvarvengrond edge) — and Tergal's standing one, the
  Sky's mandate (its packet: neighbors are rebels, not equals).
- **DIPLOMATIC INSTRUMENTS** (how wars end and stay ended; each an
  authored relation edge with cards in it): a truce sealed with a
  COURTLY HOSTAGE — the hostage grows up in the enemy's hall, a
  person the party can guard, meet, or steal back; YEARLY TRIBUTE
  (danegeld — conquest.py's tribute machinery models the player
  side, NPC edges reuse the shape, and econ's Tergal packet
  already carries one); a MARRIAGE PACT (**[PROPOSED]** as the
  instrument whose breaking is the betrothal casus belli);
  PERSONAL UNION — two crowns on one head, separate laws and
  parliaments (the succession jackpot: the union inherits both
  lands' tensions).
- **SUCCESSION CRISES** (cards; they admit on the ruler sheet's
  succession-state circumstance — this cluster is the consumer
  that [PROPOSED] entry was waiting for): the infant heir and the
  regency council knife-fight (puppet/puppeteer wiring for free);
  three branches of the family, three readings of the inheritance
  law; the dead king returns from a crusade — or a pretender
  wearing his face does; the bought recognition — a lifetime of
  bribes to make the neighbors accept a daughter's succession, all
  void the day the king dies (the pragmatic sanction;
  Mortellaria's natural shape). Per-land shapes: Tergal's tanistry
  makes EVERY succession a scramble by design; Dvarvengrond's is
  the deadlocked electors' conclave; Ensimaa's, at most once an
  age, is THE SEARCH (its packet); Gibili has no crown to pass —
  its version is the junta.

### Ensimaa — elves. Politics axis: FACE, PURITY & THE FROZEN LADDER

The two brainstorm passes — the polished 21st-century satire and
the regrounded isolationist-theocracy pass (island isolation,
mountain theocracy, purity-church discipline) — merged on their
shared spine: a perfected society defending its stillness. The
satire keeps the frame (it continues the econ axis and the
designer's constitutional-monarchy default); the regrounding
supplies the mechanisms. Dropped from the theocracy pass to keep
one-per-world: compulsory court attendance (Mortellaria's gilded
cage owns it) and the ceremonial/working dual throne (the ruler
sheet's puppet flag already rolls it).

- **Constitution (exclusive slot).** Default CONSTITUTIONAL
  MONARCHY: an ancient crown that reigns serenely and rules
  nothing, over a parliament of infinite performative debate —
  every micro-faction holds a free veto, so nothing passes, and
  debate itself is formalized verbal combat: stylized, clapped,
  and shouted in the courtyards (the monastic debate form — the
  parliament is a sport the state mistakes for governing).
  Variants: COUNCIL OF ELDERS — the crown set aside, pure
  gerontocracy; THE SEALED REALM — isolation made law, entry a
  capital offense, exit permanent exile (arms the exile cards
  below).
- **Standing tensions:** the ageless elders vs the merely young;
  the purity establishment vs the authenticity fringe; the
  automation's dependents vs the primitivists who would break it.
- **fact THE FROZEN LADDER**: the elite hoard life-extending and
  aesthetic magic, wealth, seats, and precedence — three millennia
  of compound advantage that looks twenty years old. Nothing opens
  because nobody dies and nobody yields; the "young" (a mere
  century old) own nothing and matter nothing.
- **fact FACE IS THE CURRENCY**: standing writs — purity
  certificates renewed by interview — gate office, contract, and
  polite existence (temple recommends); the neighborhood
  association watches and reports as a civic duty. Ruin is
  reputational, not judicial.
- **fact SHUNNING IS THE CAPITAL PUNISHMENT**: the erased elf is
  looked through, unnamed, contract-void — social death in a
  society where nothing else dies (disfellowship; the satire's
  deplatforming, same mechanism). WIRING: an elven heat that
  posses never enforce — the crime layer's Ensimaa flavor.
- **fact THE MALAISE**: the automation meets every need and asks
  nothing back; the commons are safe, idle, and meaning-starved
  (econ's decadence worn politically — the designer's anchor: the
  idle young gentleman and his valet).
- **card THE WRIT REVOKED**: a grandee's purity certificate is
  denied over an old association; offices, tenants, and name
  cascade away inside a season. Someone arranged it — work on both
  sides: prove the sin, or prove the frame.
- **card THE SEARCH** (rare by construction): the crown actually
  dies — the first succession in an age. Doctrine says the
  sovereign returns in a newborn; the factions each produce their
  own infant, and a regency of decades begins (the reincarnate
  search, landing on a race that had forgotten succession exists).
- **card ONE HEIR, FOUR BROTHERS**: great houses concentrate on a
  single heir across several brothers to keep the estate whole
  (fraternal polyandry bent to the manpower axis) — scandal,
  inheritance knives, and one child everyone owns.
- **card THE UNEARTHED RECORD**: a document surfaces contradicting
  the elders' account of the founding — and the elders were THERE.
  The scandal is not discovery but proof of curation: living
  memory shown to be an edited thing (the treasure-revealer, aimed
  at people who remember).
- **card THE MORTALITY CLUB**: young elves who idolize the
  short-lived — un-warded fights, real scars, borrowed grime. A
  patron pays the party to be WATCHED at work, or to take one
  along and keep it alive anyway (the fetish is the employer;
  direct PC interaction).
- **card THE PRIMITIVISTS**: woodland-ways purists foraging on a
  manicured private reserve with healing wards on standby —
  comedy, until one band goes genuinely feral. The real thing
  exists too: unsanctioned wild hermits the polished state quietly
  fears — the primitivists cosplay what the hermits are, and each
  hates being confused for the other.
- **card THE HUNTERS SENT AFTER**: under the sealed realm, exit is
  exile and prominent exiles are followed — quiet fanatics sent
  abroad to erase the escaped. Fires in OTHER lands: the party
  meets the target, or the hunters, on somebody else's road
  (cross-land encounter outlet).
- **option THE FLOATING QUARTER**: one walled district where face
  is suspended — pleasure, Powder, debt, every hypocrisy,
  unmentionable outside its gate (the floating world; econ's drug
  market has its address here).
- **card THE INVISIBLE STAFF**: the black market in mortal
  laborers who do the maintenance elves will not — unseen by
  custom, and therefore the best-informed network in the land
  (nobody guards their tongue around furniture). Econ's rented
  concessions and robot servants are this card's legal face.
- **relation** The exile edge: Ensimaa's erased and escaped pool
  in every neighbor — Gibili's cafes, Mortellaria's ports — and
  the hunters follow (the emigre entries abroad read this edge).

### Tergal — orcs. Politics axis: AUTHORITY IS PERSONAL

The strongest dump, by the designer's read and this pass's:
Mongol, plains-nations, and Germanic mechanisms carried near
verbatim. Authority here is charisma, kinship, and obligation —
never an office; the wars are over summer valleys and winter
shelter, never lines on a map.

- **Constitution (exclusive slot).** Default THE CLAN CONFEDERACY:
  sovereign clans under a GREAT COUNCIL (the kurultai) that elects
  the high chief, arbitrates the feuds it was founded to outlaw
  (the Great Law of Peace reading), and votes war. Attendance is
  law — the empty saddle at council IS the declaration of civil
  war. The high chief's court is a moving city of tents; foreign
  envoys chase the capital across the seasons (the orda).
  Variants: THE GREAT KHAN — a unifier holds the whole steppe
  under the Sky's mandate and reorganizes the warbands across clan
  lines (the decimal reform); story.py's orc aggressor is this
  variant in motion; TWO CHIEFS — a peace chief for law and
  seasons, a war chief who commands only while the banner is up
  (the white/red split); THE FRACTURED CLANS — no high chief, the
  feuds running unarbitrated.
- **Standing tensions:** clan against clan over pasture and
  precedence; the chiefs against the clan mothers; the confederacy
  against its own outlaw fringe.
- **fact TANISTRY**: the ablest kinsman inherits, never merely the
  eldest son — strong chiefs by design, and a succession scramble
  by design, every single time.
- **fact THE SKY'S MANDATE**: the high chief is destined to rule
  everything under the sky; neighboring realms are not equals but
  rebels who have not yet submitted (the standing casus belli).
  The sky speaks through readers of bones — and an omen can halt a
  campaign the council already voted (the shamanic veto).
- **fact WERGILD**: every life and limb has a price in livestock,
  payable to the wronged kin; the alternative is the blood feud,
  and the feud binds every cousin. WIRING: in Tergal sin can be
  SETTLED — the karma layer's bribe machinery reads as the lawful
  price list; unpaid, it reads as the feud.
- **fact GUEST RIGHT**: whoever eats at the fire is safe, blood
  enemies included; breaking it is the one sin no wergild covers
  (per-land sin weighting — the elven-murder pattern).
- **fact THE CLAN MOTHERS**: lineage and the herds run through the
  women; the mothers seat chiefs and can unseat them (the
  matrilineal veto) — the power behind every tent that the
  barbarian stereotype misses.
- **fact THE DOG SOLDIERS**: a warrior society polices the camps
  and the migrations with absolute authority over any rank, chiefs
  included — law enforcement with a face, and not the chief's.
- **fact PRESTIGE IS GIVEN AWAY**: authority is earned by
  charisma, mediation, and open hands, and lost overnight when the
  giving stops (the big man); rivals are buried under gifts they
  cannot repay (the potlatch). Dvarvengrond's mirror image — the
  hoard and the giveaway are the two nonhuman answers to the same
  question.
- **fact VOTING WITH THE FEET**: a cruel or failing chief wakes to
  empty grass — families fold their tents in the night and ride to
  a rival. The commons' whole franchise, and it is enough.
- **card THE HOSTAGE GUARD**: the high chief's bodyguard is drawn
  from the rival chiefs' sons — elite corps and hostage crop in
  one (the keshig). A son flees; a father wavers; a guard's
  loyalty splits. Card fuel with named faces, and the courtly-
  hostage instrument's home culture.
- **card SWORN BROTHERS**: two chiefs cut palms and become
  brothers-by-oath across clan lines (anda) — a super-faction
  overnight; the council tilts, and both clans' mothers object.
- **card COUNTING COUP**: prestige for touching the enemy and
  living, above killing him — the duel where the party is judged
  by orcish rules. WIRING: the mercy/ferocity layer already models
  capture-over-kill; here mercy SCORES, and slaughter loses face.
- **card THE MOURNING WAR**: a raid to seize people, not plunder —
  captives to fill the tents the last sickness or war emptied
  (demographic war; reads econ's desperate-herd state). The camp's
  thrall underclass is its residue — and its own quiet politics.
- **card THE SHAMING POLE**: a carved pole and a formal curse make
  a named enemy a pariah (the nithing pole) — shame as a siege
  weapon, aimable at a chief, a clan, or the party.
- **card THE GHOST DANCE**: when the herds fail and the tribute
  chiefs fatten, a revitalization faith sweeps the camps — against
  the settled lands AND the old chiefs at once (reads econ's
  lost-herd desperation; the apocalyptic turn).
- **fact OUTLAWRY**: the cast-out is stripped of law entirely —
  anyone may kill him without price (the wolfshead; wergild's
  shadow). WIRING: Tergal's crime layer runs on outlawry, not
  posses — no jail, no fine, just the declaration and whoever
  feels lucky.
- **fact THE COMPANIONS**: free warriors who abandon clan to swear
  to a charismatic nobody (the nokhor; the sworn-band oath that
  outranks blood) — the outlaw meritocracy that has, before now,
  taken the whole steppe. WIRING: this is exactly what a PC party
  IS in Tergal's eyes — the land reads the party as a
  companion-band and judges its chief.
- **option THE SINGERS**: wandering skalds own the oral record —
  praise and mockery ARE the propaganda layer, and chiefs court
  and fear them (rumor outlet with a face; a singer hired against
  a chief is a card in waiting).
- **relation** Border market towns — treaty-neutral posts where
  steppe law meets settled law (econ's trading-outpost card is one
  of them mid-escalation); hostage and tribute edges to every
  frightened neighbor (econ carries the tribute edge; the courtly
  hostage above upgrades it); the mercenary edge — warbands abroad
  under foreign coin (econ's returned-mercenary card comes home
  along it, and Firascir's settled-warband card is its far end).

### Dvarvengrond — dwarves. Politics axis: THE LEDGER IS THE STATE

The designer flagged this packet as hard — a polity built on
mining alone. The read here: that IS the distinct thing, not a
gap. The econ axis (everything follows from mining) extends
cleanly into a state that is a property registry with an army; no
other land has that.

- **Constitution (exclusive slot).** Default THE ARBITER CROWN:
  the King under the Mountain is chairman, not autocrat — keeper
  of the GRAND LEDGER (the sacred registry of every claim, vein,
  and water right) and arbiter-in-chief whose real function is
  keeping the clans out of civil war. The council of clan heads
  convenes only to set claim borders, split water, or vote a
  unified war when something outside threatens the mountain.
  Variants: THE WAR KING — an external threat hands the arbiter
  real command, and the clans already fear what he will keep when
  it ends; **[PROPOSED]** THE EMPTY THRONE — the electors'
  conclave deadlocks for years and the Ledger's clerks quietly run
  everything.
- **Standing tensions:** clan against clan along every shared
  wall; the deep clans against the surface envoys; the clans
  against the unclanned fringe.
- **fact GEOLOGICAL LAW**: all law is extraction law. Murder is a
  crime; collapsing a rival's gallery is HIGH TREASON (per-land
  sin weighting — the elven-murder pattern, in stone).
- **fact CLAIMS ARE ETERNAL**: a claim binds to blood and to the
  dead who first cut it — clans cannot simply sell; rezoning one
  tunnel needs the living AND rites to release the founders' dead.
  Politics at glacial pace, by construction.
- **fact HOARDING IS STATESMANSHIP**: the mightiest thanes hold
  court inside their own unmined veins — power displayed by NOT
  extracting (Tergal's mirror; the potlatch inverted).
- **fact BLOOD AND QUOTAS**: a commoner owes the clan tonnage, and
  standing tracks it — a missed quota is a spiritual failing
  before the ancestors, not merely a debt (econ's strike, scrip,
  and company-shop cards sit on this fact).
- **card THE MARRIAGE OF VEINS**: betrothal as claim consolidation
  — the neighboring clan owns the other half of the iron seam. The
  couple is the smallest thing in the room, and one of them may be
  paying the party.
- **card THE FOUNDER SAYS NO [PROPOSED]**: the rites to release a
  dead founder's tunnel are performed — and the dead REFUSES. In
  this world that is no metaphor: the ancestor speaks, the claim
  freezes, and someone wants a second opinion — the priestly way
  or the necromancer's way.
- **card THE ARBITRATION**: two great clans at the brink over one
  silver vein; the king must rule; both sides have sworn to defy
  him — and the crown survives only if the ruling is too clever to
  defy. Work on every side, including the king's.
- **fact THE WILDCATTERS**: claim-jumpers mining the condemned
  upper galleries and the unmapped deep — persecuted less as
  thieves than as structural traitors (an unregulated tunnel
  threatens everyone's). Encounter and employer both.
- **fact THE SHORN**: the unclanned — name stripped, no legal
  person, killable without price (outlawry under the mountain;
  Tergal's wolfshead parallel). Day-labor, mercenary meat, and the
  recruiting pool for anyone hiring deniable hands. WIRING: a
  protection-zero band for the crime layer's mark tables.
- **fact THE SURFACE ENVOYS**: the despised caste that handles
  everything above ground — rich, indispensable, "sun-addled"
  traitors to the traditionalists. Nearly every dwarf the party
  meets ABROAD is one: standing color for every other land.
- **relation** Prospecting edges: dwarven claim-law walks abroad
  in boots — Firascir's silver-vein card (its packet) is
  finders-keepers to the prospectors and the-lord's-land to
  Firascir law; the Ensimaa crystal concession (econ) has the same
  collision sleeping in it.

### Firascir — humans. Politics axis: CUSTOM AGAINST PREROGATIVE

The baseline land takes the deepest packet (the asymmetry
doctrine; the ruler sheet's weights are already Firascir's).
Rights here are OLD — written nowhere, or somewhere flammable —
and every scale of the land is a tug-of-war between ancient custom
and someone's prerogative. Entries grouped by scale. The manor
tension is STANDING (it is the econ packet's oppression axis); the
realm rolls one tension from the list.

- **Constitution (exclusive slot).** Default DECENTRALIZED
  FEUDALISM: a crown among great lords, strong on its own manors
  and weak beyond them. Variants: THE CENTRALIZING CROWN — royal
  judges riding circuit, castle licenses enforced, shield money
  taken instead of service (scutage): the king slowly winning, and
  every crown-vs-lords card armed; ARISTOCRATIC ANARCHY — the
  maximally decentralized pole (the designer's Polish shape): an
  elective crown, a magnate veto, rule of independent barons — the
  king may convene, preside, and beg; THE REGENCY — an infant
  king, the council governing (succession cluster standing; puppet
  wiring for free).
- **Standing realm tensions (roll one):** the crown vs the great
  lords; the crown vs the merchant guilds' wealth; the temple vs
  the crown (who names the bishops — the investiture fight; the
  militant order is its armed edge); old blood vs the new men
  (risen clerks and bought titles in velvet).

REALM & CROWN:

- **card THE INTERDICT**: the temple closes the land — no rites,
  no weddings, no burials — until the crown submits (the
  investiture fight's nuclear option). Every settlement feels it
  the same week: services stop, and the dead wait (news + state
  flip; reads temple-vs-crown).
- **card THE ORDER'S OWN LAW**: the militant religious order hangs
  a local man under its own court and its own gallows; the county
  demands the body and the precedent (an order answering only to
  the church, garrisoned in a land that thinks otherwise). Econ's
  templar move is the crown's eventual answer; this card is the
  provocation years earlier.
- **card THE ROYAL PROGRESS**: the itinerant court arrives — a
  hundred mouths with precedence, eating a lord toward ruin as a
  loyalty test. WIRING: the ruler sheet's `itinerant` flag
  promised this settlement event; here it is.
- **card THE BAN**: the crown declares a rebel lord legally dead —
  lands forfeit, killable by anyone (the imperial ban: outlawry at
  lord scale). A posse card where the posse is EVERYONE — and the
  banned lord is hiring.
- **card THE SETTLED WARBAND**: the crown (or a desperate march
  lord) grants border land to an orc warband in exchange for
  service (foederati). The neighbors are terrified; the warband
  keeps its own law; both sides are right about each other
  (Tergal's mercenary edge, landed).
- **card THE BADGE**: a lord pays armed men to wear his livery and
  lean on the courts (bastard feudalism) — and by the time the
  crown's inspectors arrive to break the private army up, the
  badge-men ARE the local law (jerkify on both ends).
- **card THE WARD**: a neighbor lord dies leaving a child heir;
  the crown auctions the wardship — raise the child, drain the
  estate, marry it to your own son at majority. The child is a
  person, an asset, and a quest object in one, and everyone
  bidding knows it.

MANOR & VILLAGE (the standing tension; econ's mill, toll, and
revolt-chain cards live here already — these are the rights-side
additions):

- **card THE CUSTOM STRIKE**: the bailiff demands extra harvest
  days; the village cites the manor's ancient custom, shows up on
  time, and works at a crawl (work-to-custom as a weapon — the
  go-slow the lord cannot quite punish).
- **card BURNING THE ROLLS**: in a bad season the mob does not
  kill the lord — it burns the manor's COURT ROLLS, the written
  proof of who owes what and who was born unfree. Every debt and
  every servile birth, ash — unless the clerk kept a second copy,
  which is suddenly the most valuable object in the land.
- **card A YEAR AND A DAY**: a skilled smith flees the manor to a
  chartered town — town air makes free after a year and a day, and
  the guild will not give him up. The lord's men are at the gate;
  the clock is public knowledge; the party fits on either side of
  it.
- **card WHILE THE LORD IS AWAY**: the bailiff invents fines (bad
  ale, gathered deadwood) and runs the manor court as his purse;
  the village-elected reeve, meanwhile, sells the lord's grain and
  books the shortfall to blight. Petty tyranny and petty theft
  feeding each other until the lord returns — or someone writes to
  him (two jerks, one address each).
- **card THE RENT STRIKE**: the village hides its coin and pleads
  a blight (reads the actual drought/blight state — some years it
  is TRUE); the bailiff cannot evict everyone at once and knows
  it. Casing work in reverse: is the plea honest?
- **card THE WIDOW'S HOLDING**: a rich widow pays the yearly fine
  to stay unmarried and keeps prime land out of every scheming
  hand — suitors, heirs, and the lord's own plans circle her (a
  person with an address, holding against the tide).
- **card THE PEASANT MERGER**: two big village families betroth
  their strips into a local monopoly on the best soil — the
  balance of power wobbles from BELOW (the marriage-of-veins
  pattern, in dirt; the lord notices late).
- **card THE JURY THAT LIES**: the manor court's jury — the
  accused's neighbors — swears an heir true-born, or a starving
  thief innocent, in the law's teeth and at their own risk of
  fines (nullification: the community closing ranks; the party's
  testimony tips it either way).
- **card THE CRY IGNORED**: the forester raises the hue and cry on
  the beloved poacher and the village goes conveniently deaf —
  failing the cry is itself a collective fine, and everyone is
  counting on nobody testifying. WIRING: the crime layer's posse
  machinery, refused from below.
- **card FOREST LAW**: the royal woods stand outside common law —
  draconian foresters, savage penalties for deer, the customary
  take (forage, deadwood, gleaning after harvest) fenced off year
  by year. The revolt's demand is the OLD rights back; the
  nobleman version is the poaching war — dead deer, hanged
  "poachers," then retinue skirmishes between two lords' woods.
- **card THE SILVER VEIN**: a strike on the local lord's land
  makes him suddenly, dangerously rich — armed men, bought judges,
  new walls, new appetites. Option, per the designer: DWARVEN
  prospectors found it, and their claim-law says finding is
  keeping (the Dvarvengrond relation; two legal cultures, one hole
  in the ground).
- **card TRIAL BY COMBAT**: the loophole standing wide open —
  wealthy knights answer lawsuits at swordpoint through hired
  champions. WIRING: champion-for-hire is a quest shape the duel
  machinery already supports; the party IS the loophole.

TOWN:

- **card THE CHARTER RUN**: a market town secretly pools silver to
  buy a royal charter out from under its lord; the lord blockades
  the roads to stop the purse reaching the king. The payload is a
  DELIVERY — the courier machinery with politics on top, and both
  sides hiring.
- **card THE MAYOR IN VELVET**: a wool merchant elected mayor
  dresses past his blood, rides a warhorse, and demands equal
  address; the insulted barons choke the town's grain to starve
  him down (old blood vs new men, made local; reads econ's food
  states — econ's fair and pie-powder court give the town its
  stage).

TEMPLE & PARISH:

- **card THE TITHE WAR**: the village tithes its sickliest lambs
  and lightest sheaves, systematically; the priest's barn keeps
  the evidence (passive resistance with an audit trail — casing
  work again).
- **card THE SCANDALOUS PRIEST**: the concubine at the rectory,
  church funds buying land for his children, the pious elite
  petitioning the bishop — who has a price for acting. Jerkify:
  the priest may still be the village's best friend.
- **card THE WITCH-FINDER**: a self-appointed finder of witches
  arrives offering to root out the village's witch — for a fee, and
  he always finds one (moved here from the baroque pile: witch-fear
  is genre-true in the medieval land). WIRING: the ruler sheet's
  spell-fearing cell — and SUBORDINATE to the magic packets'
  CONDUCT, NOT CREED doctrine (2026-08-07): the finder is a fraud,
  his "witch" is almost never a real caster, and a caster party is
  a mark for his con, never a magnet for the land's hostility.
- **card THE DANCING PLAGUE**: a street of villagers cannot stop
  dancing; flagellant columns arrive behind the news. The temple
  calls it penance, the wise woman calls it poison — and the
  fog-necromancer pattern applies: the cause may have an ADDRESS,
  and rumor lines lead there (mass hysteria as a landmark-lite
  problem).
- **option SANCTUARY**: a fugitive who reaches the altar cannot be
  taken for forty days — then walks barefoot to the border into
  exile. WIRING: a priced, timed heat valve the crime layer can
  quote (the party WILL use this), and a card when the posse
  decides not to wait out the clock.
- **card THE FREE COMPANY**: the war winds down and the unpaid
  company does not — a mercenary micro-state on the roads, tolling
  bridges and renting itself to whichever tension pays (encounter,
  employer, and target in one; Tergal's mercenary edge feeds it,
  econ's robber-baron tolls are its business model).
- **card THE MIDNIGHT COURT**: where the lawful courts are bought,
  a secret tribunal of masked freemen tries and hangs by night
  (the vehmic court). The vigilante option with a membership list
  — the party can be hired by it, sent against it, or JUDGED by
  it.

### Mortellaria — humans. Politics axis: ONE KING, ONE LAW, ONE FAITH

The absolutist project, and everyone it grinds: the centralized
state against its own nobility, its provinces, and its heretics —
with the finance axis (econ) as its bloodstream.

- **Constitution (exclusive slot).** Default ABSOLUTISM: the
  centralized state — royal commissioners (intendants) over the
  old courts, the sun-court palace over the old seats. Variants:
  MINISTERIAL RULE — the crown reigns, the cardinal governs (the
  puppeteer made office); THE FRONDE STATE — the princes openly in
  arms to CONTROL the crown, never to depose it (civil war as
  court politics by other means); **[PROPOSED]** THE BANKRUPT
  SUMMONS — the treasury empty, the ancient estates called for the
  first time in living memory, every faction arriving with a
  grievance list.
- **Standing tensions:** sword vs robe — ancient, proud, poor
  blood against purchased office and new money; the crown vs the
  minority faith it has resolved to erase; the court vs the
  provinces that pay for it.
- **fact THE GILDED CAGE**: the high nobility must attend the
  palace — precedence wars, ruinous mandatory wardrobe, bedchamber
  offices (handing the king his shirt is a ministry), the salons
  as unofficial ministries run by hostesses — kept beautifully
  broke and far from their power bases. The ruined duke's heir is
  suddenly available to a rich commoner's daughter, and every
  salon discusses it.
- **fact EVERYTHING IS FOR SALE**: offices, titles, judgeships,
  colonelcies — the crown mints dignities to cover its debts
  (venality; the robe nobility is this fact compounding). The
  absurd office is real power: the Grand Inspector of Barrels can
  stop every cooper in the city until paid.
- **fact THE BLACK CHAMBER**: the post is read — every sealed
  letter through the capital is opened, copied, and resealed by
  the crown's cryptographers. WIRING: the game's delivery quests
  pass through this fact; carried letters are not safe, and
  knowing so is a job qualification.
- **card THE REVOCATION**: the tolerated minority faith is made
  illegal overnight — dragoons quartered in refusers' homes, the
  skilled trades fleeing abroad with their capital (state flip:
  wealth drops within a season — econ feels it first).
  Priest-holes in the manors, services in the cellars, informers
  paid by the head: the hidden-faith fringe arrives with the
  edict.
- **card THE DUELING EDICT**: the code duello made a capital
  crime; two grandees fight anyway; one is dead, and the survivor
  — estate in limbo, family baying — is on the road: abroad,
  hireable, and hunted (cross-land encounter fuel).
- **card THE SEALED WARRANT**: blank royal arrest orders exist,
  and they can be BOUGHT (lettres de cachet) — a rival vanishes
  into a fortress without charge or trial. WIRING: the crime
  layer's legal disappearance — a priced menu entry for the
  connected, a fate to rescue someone from, a paper the party
  might be carrying unopened.
- **card THE TONTINE**: an elite investment pool where the last
  survivor takes everything — and the survivors have begun dying
  in interesting ways (the murder mystery that names its own
  motive).
- **card THE MONOPOLY BUBBLE**: the crown grants a colony-trade
  monopoly; the shares go mad; the crash ruins half the merchant
  quarter overnight. The POLITICAL act is the grant (econ's
  bank-run card is this card's neighbor, and sometimes its morning
  after).
- **card THE ALCHEMISTS' WING**: the crown funds a stable of
  alchemists to transmute the war debt away (moved from the
  village list — it is a crown project, and gold-at-the-center is
  this land's axis). Option, per the designer: IT WORKS — and the
  treasury's triumph is finance's apocalypse: what is gold worth
  the day after? WIRING: the game's alchemy layer gives the
  project texture for free.
- **card THE FLOUR WAR**: the crown lifts bread price controls in
  a lean year — prices quintuple, bakeries are sacked, merchants
  lynched as hoarders; the act is read to the crowd, the hour runs
  out, and the musketeers fire (the decree-made famine; econ's
  famine chain is the harvest-made one).
- **card THE SALT REVOLT**: the salt tax rises once too often; a
  province butchers its tax collectors; the army answers with
  burned villages and hanged ringleaders (reads
  court-vs-provinces; econ's tax-farmer card is the standing
  cause).
- **card THE AUTO-DA-FE**: the faith's tribunal arrests a mountain
  village wholesale — heresy, witchcraft, the old religion — and
  stages the penance-and-execution spectacle in the capital square
  as political theater (reads crown-vs-faith; SUBORDINATE to the
  magic packets' CONDUCT, NOT CREED doctrine, 2026-08-07 — the
  tribunal prosecutes heresy, "witchcraft" meaning harm by hidden
  means; casting as such stays legal, the capital's academy the
  proof).
- **card THE BANDIT KING**: enclosure and debt made him, charisma
  armed him, and he robs ONLY tax shipments and the rich — so the
  peasants hide him, the magistrates hang whoever they catch
  instead, and both sides pay for road work (the two-sided
  standing employer).
- **fact THE OARS**: the state's galleys are rowed by the
  sentenced — vagrants, heretics, debtors — and the port's press
  gangs take the rest on a bad night (a punishment with a place in
  it, and a rescue shape; grim Mediterranean color the axis
  earns).
- **option LETTERS OF MARQUE**: the colony war licenses privateers
  — state piracy with paperwork, a legal employer for violence at
  sea, one revoked commission away from ordinary piracy.
- **fact THE SMUGGLER STATE**: the internal tariffs and the salt
  price built a parallel nation — armed syndicates better funded
  than the coast guard, bankrolled by respectable money (econ's
  smuggling option at political scale: in the smuggler country,
  THEY are the magistrates).
- **relation** The seditious print: Gibili's basement presses
  print what Mortellaria's censors burn, and the pamphlets ride
  the smuggler roads back in (the reverse of the arms flow). The
  emigre edge: the Revocation's exiles and the edict's duelists
  pool in Gibili's cafes (its packet).

### Gibili — goblins. Politics axis: THE STATE THAT ISN'T

Econ already owns labor vs capital (the strikes, the company
police, the scrip); politics adds the paralyzed state above it,
the split loyalties inside it, and the foreigners feeding on it.

- **Constitution (exclusive slot).** Default THE PAPER STATE: a
  flag, a parliament, an army — and no writ that runs past the
  mill gates; corporate power governs in fact (econ's founding
  fact, made constitutional). Variants: THE JUNTA — the generals
  lose patience (the split-army fact resolving upward); THE
  COMMUNE — a syndicate city wins and keeps itself: schools,
  courts, rations, firing squads (the barricade state made
  permanent); OCCUPATION — Mortellaria's big econ card, worn as
  the constitution.
- **Standing tensions:** the parliament's three-way deadlock
  (restorationists / mill liberals / socialists); the army against
  its own ranks; the syndicates against each other.
- **fact THE PARLIAMENT OF CHAOS**: deadlocked, brawling,
  inkwell-throwing — and OWNED: seats sit on depopulated rotten
  districts where one landlord commands all three voters, and
  ministers are priced like any other commodity. The barons' tool,
  which occasionally bites its owner.
- **fact THE BUFFER DOCTRINE**: the whole foreign policy is "give
  the empire no excuse." Mortellaria buys the cannon, prefers the
  mills cheap and the state weak, and quietly funds rival radical
  groups to keep them so — the occupation card is what happens the
  day the doctrine fails.
- **fact THE SPLIT ARMY**: aristocrat generals who despise the
  mill barons command slum-drafted ranks who sympathize with the
  strikers they are ordered to shoot. Every crowd order is a coin
  flip. WIRING: econ's uprising card gains its
  which-way-do-the-soldiers-point read; the junta and the commune
  are the two ways the coin lands.
- **fact THE SYNDICATES AS SHADOW STATE**: the unions run schools,
  clinics, courts, and dues in the districts the state forgot —
  parallel government is not a metaphor here (econ's strike
  machinery sits on this fact).
- **card THE GENERAL STRIKE**: every industry at once — the nation
  simply stops (the escalation past econ's per-town STRIKE state;
  admits on strike-on plus a spark). It begins, as ever, with the
  poisoned trades — the match-workers the phosphorus is eating —
  and ends however the split army decides.
- **card THE PROVOCATEUR**: the secret police's card-catalog
  archive has a man in every cell — and this bomb plot was HIS
  idea (the agent provocateur; the archive is the one organ of the
  state that works). Work for every side: expose him, protect him,
  become him.
- **card THE MANUFACTURED ATROCITY**: a press baron fabricates an
  outrage to sell papers and force the war party's hand — and
  under the buffer doctrine a manufactured border incident can
  bring the empire in for real (yellow journalism with existential
  stakes).
- **card THE BARRICADE DAYS**: a district overturns its trams,
  pries up its cobbles, and declares itself autonomous (the
  commune in miniature). Inside, three flags argue — anarchist,
  socialist, reformist — and shoot at each other nearly as readily
  as at the police (the fractured left: two-sided work INSIDE the
  barricade, not just across it).
- **card THE MACHINE-BREAKERS**: a fringe that wants no wage rise
  — they want the engines DEAD (the saboteur heresy; econ's
  sabotage angle worn as faith). The unions fear them more than
  the barons do: every broken loom is the strike blamed.
- **option THE EMIGRE CAFES**: deposed royals, cashiered generals,
  spy-masters, and duel fugitives plot restorations over credit —
  every neighbor's exiles end up HERE (Mortellaria's heretics and
  duelists, Ensimaa's erased), and half of them are somebody's
  informant. Standing employer fauna.
- **option THE BASEMENT PRESSES**: seditious print for every
  appetite — manifesto, bomb manual, scandal sheet — smuggled into
  Mortellaria against the censors (the reverse arms trade; the
  relation edge sits in Mortellaria's packet).
- **card THE MUCKRAKER**: a journalist goes undercover into a mill
  or an asylum and comes out with a story someone will kill to
  keep unprinted — escort it, suppress it, or finish it (one quest
  shape, three employers).

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
