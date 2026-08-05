# Design log

Dated records of the major design sessions: what was discussed, the road
the discussion took, and what was decided. The *decisions* live on in
plan.md (roadmap), rules.md (mechanics), and dm.md (play) — this file
keeps the reasoning trail so a settled question stays settled. Newest
last. (The benchlog is this file's sibling for measured tuning.)

---

## 2026-07-19 — The villain pivot (brainstorm → karma & heat v1)

**Where it started.** The designer's diagnosis of the prototype: it
plays like an idle game — powerups plus some loss chance, very linear,
little mechanical and no narrative choice. It is not a strategy game and
shouldn't try to be (mechanics too shallow, stats hard to display,
complex tactical input tiring in chat). The experiment still has
promise, and the superpower to tap is the AI itself — free narration,
NPCs animated in a way CRPGs can't. Maybe the game works better as a
simulation engine for the narrative than as a gameplay-first game.

**The proposed direction.** Facilitate and encourage *evil play*: by
video-game logic conquering a map beats keeping it frozen. Conquer the
world by level 20; get stronger by taking territory while ever-stronger
alliances and heroes push back. Keep it dual (Good play must survive —
e.g. liberating a world half-conquered by someone else). The evil must
be cartoonish, not depressing (kick the puppy → its parent shows up for
a dire-wolf fight; pet it instead and you still fight the parent,
framed non-lethal). A candidate frame: an imp from hell tasked with
doing evil — helping people brings hell's disciplinary forces instead.
Satellite ideas from the same brainstorm: luxury items the PC is
encouraged to acquire and flaunt (envious hell officials, heroes coming
to reclaim the holy golden elephant); good/bad karma as XP that unlocks
abilities AND invites stronger attacks (a better version of the old
"gain power to do quests above your level" problem); characters more
prominent; food as a survival element; a very tight first 3 levels; a
Diablo-ish over-the-top weapon layer with bigger numbers; the map
question (province list vs grid vs hexes); more colorful combat moves;
tone less Warcraft, more Discworld/Conan.

**The discussion's key moves.**

1. *Sharpening the diagnosis*: the game had become a difficulty curve
   with a purse — every decision is "pick the right level number" and
   nothing the player does changes what the world is. The pivot is not
   "evil mode"; it is making the player the CAUSE of the world's state.
   Evil is the tone that makes that fun instead of grim.
2. *Karma-as-heat identified as the load-bearing idea*: the throwaway
   line "karma as xp unlocking abilities and inviting stronger attacks"
   replaces the quest board as the difficulty-selection mechanism
   (difficulty by consequence, a throttle the player pumps), collapses
   the content-escalation problem into one feedback loop (sin → posse →
   killing the posse is itself sin), and feeds the AI-DM superpower
   (retribution as recurring named people, not encounter rolls).
3. *Reuse discovered*: the conquest questline (story.py) is the new
   direction's machinery pointed the other way — waves, named faces
   over reskins, occupation tags. The rival-conqueror idea can BE the
   existing aggressor. The map answer falls out: the list of lands with
   ownership tags, exactly like `[UNDER THE YOKE]`.
4. *Pushbacks accepted*: no big-number rework (the Diablo feel comes
   from named/masterwork instances with authored riders — roadmap item
   5); no food/hunger meter (the luxury/greed economy does that job as
   a voluntary sink with consequences — and it is Discworld-funnier);
   hexes/grids dead on arrival at 40 columns.
5. *The fork*: karma beside XP vs merged. First lean was beside (safe);
   the designer, thinking it through mid-reply, flipped it — merged,
   because a separate currency re-opens "what does karma actually get
   you" while bucketing XP gets the whole loop for free. Settled: XP
   bucketed by the alignment of the work; heat = the level gap
   punishment arrives at; zero bad karma = the old game exactly, live
   and untouched.
6. *Tone doctrine landed*: the engine only ever resolves fights against
   things that fight back; the wickedness itself is narration, in the
   cartoon register (dm.md).

**What shipped the same session (karma & heat v1** — rules.md's Karma &
Heat add-on; `karma.py` + quests/session wiring**):** quest `align`
flags; XP bucketing with the penance burn (1:1); heat =
`bad_karma // (100 × level)` capped at 3; the shadow board
(`board --dark`, lazy per-settlement-day, bench-invisible, dark gold
×1.5); the punishment posses (Watch → bounty guild → crown's huntsmen →
heroes of the realm; cooldown 2 days, chance 0.6, at arrivals and
nights; generated named leader kept as the nemesis seed); the DM surface
(`karma`, `karma bad/good N`, `award --dark/--good`, `forge --dark`);
the seven generic dark templates (the puppy quest included, as
mandated). Verified: worldgen/benches untouched (sanity bench run
within noise), full dark loop played end to end in a test game.

**Deliberately NOT decided yet** (open in plan.md): karma AS the level
track (the full merge); what bad karma *buys* (hell ranks, evil powers);
conquest ticking's exact shape; the army-mechanic question; all heat
constants (hand-set, sim-unverified — the table tunes them).

**Next step agreed**: play the dark path's first ten messages — the
tone probe. The first 3 levels are the only part that ever gets tested.

## 2026-07-19 (later) — The hell pact (dark quests, the big content pass)

**The designer's input.** A long brainstorm reframing the dark path's
fiction and asking for a major dark-quests implementation: the PC is
NOT a neutral adventurer but a low-ranking employee of Hell — a mortal
of a game race (explicitly not an imp) under a pact with an evil god;
hell's aim is weakening the orderly universe's fabric (gates,
summonings); order is maintained by the gods of Light and their
agents (paladins, hunters, priests, hired heroes, watchmen, mobs) and
is often not Good. Hell assigns tasks (a curriculum in vice, difficulty
suited to the player with the margin of error running upward) via
unseen job boards / mail / couriers; refusing — Chickening Out — draws
infernal enforcers; hell can be bribed; tasks can be ignored up to a
point while questing normally. Plus ~30 task ideas, a mandate to
formalize a more complex quest structure, the rule that heroic
adventurers never kill the PC (he loses party, gold, and all bad
karma; heroes think him dead or he runs in shame, hell laughing), a
minor DM rule (taking a quest opens the fight in the same message, no
wasted arrival turn), and a directive: **abandon XP/gold balance for
now — quest variety does more good.**

**The triage** (asked for explicitly: cut / later / dm.md lore):

- *Shipped as mechanics*: the pact frame (default-on at `new`,
  `--no-pact` opts out — settles plan.md's imp-frame question as
  MORTAL EMPLOYEE), assignments (`TASK_INTERVAL_DAYS` 4, spread 0..+2,
  WORD FROM BELOW), Chickening Out (grace 4 d, hell posses at party
  +1 escalating per beating, neutral XP), `bribe` (30g × level, 10 d),
  the caper structure (deed = PC 2d6+stat vs DC 10-11, clean-or-botch
  with +15 witness karma; twist = priced terms, `settle` at ×0.5), the
  left-for-dead mercy (law: party/purse/karma forfeit; hell: purse
  fine + task withdrawn — never GAME OVER vs posses), and 17 new dark
  templates (steal/fence, beast-caging, dine-and-dash, priest
  sacrifice, puppy sacrifice, village sack, bank vault, poisoned
  round, mansion murder, evil weapon, sacred-weapon corruption, altar
  desecration, coworker betrayal, cultist protection, hellgate,
  powder trade, nobleman's land grab) — 24 dark templates in all.
- *To dm.md as world lore*: the pact fiction, the world of Order
  ("often not Good" as questgiver color), hell walkable-but-bullying
  (narration-only), the curriculum doctrine (self-assigned dark work
  encouraged), the non-lethal combat note (0 HP = knocked out when the
  fiction says so), the freeform "graded on body count" tasks (forge
  --dark + karma bad N), and the take→fight turn rule.
- *Planned for later (plan.md)*: hell as a place (gladiator pits +
  bribe-to-lose, the bone-paid castle), the geographic wanted level
  (heat is the global version), standing enterprises (powder network
  as a holding), the rot spell (wants conditions), war-side-taking
  (already villain roadmap 6), artwork/relic flaunting (already the
  greed economy, item 5).
- *Cut / folded*: the tax-doubling nobleman (Debt Collection already
  is it), nothing else — the input was nearly all usable.

**Design calls made while implementing**: deed success closes the
site through the same `_close_site` path as a fight (full lump, no
encounter XP — stealth runs karma-light, kept as a happy accident);
enforcer XP is neutral (demon-farming must not become penance);
beating enforcers never closes the task (only doing it, bribing, or
losing does); the mercy covers POSSES only — roads and quests still
kill (the mandate was about heroic adventurers, and a deathless world
would unmake the game). Balance: everything hand-set, no bench (the
directive), recorded in develop.md.

**Next step unchanged**: play the dark path's first ten messages — now
with the pact knocking from message one.

## 2026-07-19 (playtest feedback) — Narration: tone and closing-options fixes

First played run of the pact game (Delg, the dwarf hell-employee; ended
in a party wipe on the Vault Job's Guard Sergeant). Two narration
problems surfaced and were written into dm.md:

- **Closing options read convoluted.** The DM wove the end-of-message
  choices into one dense prose sentence instead of the display block
  ("the board is here, the war waits two lands east, Hell's clock is
  ticking..."). New rule: options live in the block, one per line; the
  closing prose is one plain question, and never repeats the block.
- **Tone drifted heavy.** The narration leaned on dread, portent, and
  solemn consequence-lines — grimdark realism where the game wants pulp
  with a wink. New rule: the dark path's cartoon-villainy register is
  the WHOLE game's register; cut foreshadowing and prestige-drama
  weight.
- **Low-hanging fruit added alongside**: one scene beat per message
  (simultaneous news gets one scene + compressed blocks, not a full
  staging apiece), and NPC speech capped at a few lines, no monologues.

## 2026-07-19 (later still) — Ordering vibe check: nemesis pulled forward

A short what-next session (a vibe check over the whole board, not a new
design). Question: which major feature to introduce or improve next.

**The pick: nemesis persistence, moved from villain-roadmap item 4 to
item 2 — ahead of conquest ticking.** The reasoning, recorded so the
swap stays settled:

- *Leverage per cost.* It is the cheapest item on the board: the save
  already keeps `last_leader`; the build is a thin nemesis record plus
  one hook at posse-spawn time. Everything else on the shortlist
  (conquest ticking, the greed economy, the banded inventory) is a
  bigger slice.
- *It feeds the superpower.* The engine cannot make a recurring named
  enemy matter; the DM can, effortlessly, if the save just remembers
  the face. Purest case of thin-mechanics-in-code, flavor-from-the-DM.
- *It improves the shipped karma layer before extending it.* Heat
  currently sends anonymous, disposable posses; a surviving leader who
  returns with a grudge turns heat from a random tax into a story —
  which is what the pivot says heat is for.

**Conquest ticking drops to item 3, not out.** It is the villain
campaign's actual verb, but it is the meatier build and its open calls
(does holding land raise the heat floor? tribute rates?) want a played
dark run behind them. The good-karma mirror slides to 4 unchanged.

**Unchanged and reaffirmed**: item 1 stays *play the dark path, no
code* — the tone probe precedes everything, per the shipped slice's
own directive. Nemesis is small enough to slot in mid-playtest the
moment the first surviving posse leader feels forgotten. **Explicitly
not picked now**: the banded quest inventory — a Good-game plumbing
improvement while the project's energy is in the villain arc; it also
wants the shadow-board precedent felt in play before copying its
shape.

## 2026-07-21 — The retro pivot: mechanics-centered text adventure

**Where it started.** Verdict on the dark quests: an improvement,
somewhat more interesting than the vanilla ones. But strong
dissatisfaction with the AI's narration and DMing style — the table
manner, not the content. Proposed and adopted: drop the "ttrpg with an
AI DM" paradigm and work toward a **mechanics-centered game like a
retro text adventure**. The mechanics are not tactical combat but
MACRO decisions and a SIMULATED WORLD the player watches play out.

**The reframed superpower.** The LLM's advantage is NOT that it can
narrate — it is that it is a CODING AGENT running the game: the
central game function need not exist, only subsystems; the AI calls
them, generates content where necessary, and brings it together to
keep the game coherent and open. This inverts half of 2026-07-19's
diagnosis (there, the superpower was free narration and animated
NPCs, and the villain frame leaned on it) — recorded here so the
reversal is explicit and stays settled. Note the architecture half
was ALREADY this shape (develop.md's "no autopilot" doctrine: thin
mechanics in code, the AI calling primitives on purpose); what
changes is the register and which decisions the game is about.

**Decided:**

- **Style, shipped same day**: minimalist retro text adventure —
  present tense, second person, terse, deadpan; not wry Pratchett,
  not generic-fantasy purple prose. Written into dm.md as the
  governing rule at the head of Narration style; the 2026-07-19
  "pulp with a wink" tone bullet rewritten to match (content stays
  comic and light, the narrator stops performing it). The full dm.md
  protocol trim rides the log/menu rework.
- **Displays over prose**: a greater role for script-generated logs
  and menus, optimized so the chat can usually display them
  directly. Most important: the combat PLAYER LOG and a player
  STATUS DISPLAY log, plus the levelup menu with ability
  descriptions. Planned as retro roadmap item 1.
- **Quest wording rework** (item 2): the dark templates' words
  themselves rewritten simple and straightforward; the dark quests
  remain the most important pre-authored content.
- **The villain layer demoted**: dark quests + karma are ONE layer
  of the game we might return to, not the main direction. Nemesis
  persistence / rival posses — plan.md's next-up item until today —
  bumped way back: it serves narrative strength, not mechanical,
  and narrative is not the focus now. The villain roadmap is
  shelved as the layer's internal order; conquest ticking and the
  greed economy noted as its most retro-compatible re-entry points.

**Next steps** (plan.md, THE RETRO PIVOT): the log/menu rework, the
quest wording pass, then playing the dark path in the new register
(the probe now tests style and content at once), then a dedicated
macro-game design session — what the macro decisions ARE and what
the simulated world runs (seeds: the parked off-screen event
simulation, standing enterprises, conquest ticking / domain play).

## 2026-07-21 (later) — The one-log combat display (retro item 1, combat half)

**The trigger.** A real played log (the scrap-hounds quest) read back
against the retro pivot's bar: too much indentation (everything hung
under "Round 1:", wasting a third of a 40-column phone screen), lines
wrapped mid-thought ("Scrap-Hound 1 / is grazed (-1 HP) [Scrap-Hound
1: / 3/4 HP]"), and a two-log protocol whose roles had gone mushy —
the DM sometimes pasted the short log, sometimes hand-wrote a summary,
and nobody actually needed the full log at the table.

**The concept settled first, format second:**

- **One log.** The DM and the player read the SAME script-generated
  display; the DM narrates its shape in 2-4 sentences over it. The
  full debug log (dice, modifiers, stamina readouts) survives but
  stops printing — it appends to the untracked `fight.log` workfile,
  kept because post-mortems (a player death, a suspect number) are
  worth having on disk. It is a dev surface now, not a play surface.
- **What the log is FOR:** the DM needs the general shape, the
  memorable events, and the outcome; the player skims it for build
  feedback. Combat is central but non-interactive — legibility IS how
  autocombat gets appreciated. So: scannability over both kinds of
  minimization, but inefficiency cut everywhere it doesn't cost
  clarity.
- **Numbers moved to the decision surfaces.** Fight lines carry no
  roll penalties and no resulting-HP brackets; the pause menu and the
  post-fight tally now print each hero's standing penalties (wounds /
  Winded / Spent, with numbers). This consciously supersedes
  2026-07-09's "penalty on every wound line" doctrine — the number the
  player budgets around is now shown where the budgeting happens.

**The format decisions** (rules.md "Reading the combat log" is the doc
of record): column-1 lines pre-fitted to 40 (`fit_lines`, breaks only
on semantic seams); pressure narrated as the verb, severity as a bare
number with the wound tier as punctuation (deals 1 dmg. / 2 dmg! /
4 dmg!! / 6 dmg!!!); the attacker-HP tag as a rolling readout (no tag
= unhurt); "parried."/"deflected." with no margin garnish; quiet
rounds collapsed ("Round 4-5: nothing lands.") with Winded/Spent
crossings deferred past the collapse line rather than lost; movement
lines only when someone threatens at range; abilities and moves by
name only; Power printed only after casting spells; roster stat
blocks as the enemy introduction (the player learns what DEX/STA/HP
mean by reading them at every door); SLAIN/falls glued onto the wound
line where they fit.

**The one mechanical change:** the dying counterattack resolves
immediately after the felling blow (turn-queue promotion), so the kill
and the answer read together. Judged mechanically indifferent a
priori, then sanity-checked (tune 4k + bench_party 1.5k — all within
noise; benchlog 2026-07-21). Two cosmetic guards rode along: no
grip-switch line from a dying shooter, no rime on a corpse.

**Tried and rejected in-session:** E1/P1 name shorthand (parked in
plan.md — cryptic until proven needed); per-line resulting-HP
brackets (redundant against the rolling readout); keeping the printed
two-log protocol with a better short log (the full log earns nothing
at the table that the workfile doesn't keep).

**Scope line drawn:** the combat surface (banners, roster, exchanges,
pause menu, awards, tally) shipped now; the status display, the
levelup menu with descriptions, and the remaining non-combat surfaces
are recorded as the open half of retro item 1 in plan.md.

## 2026-07-22 — The shared retro text-RPG writing voice

**The prompt.** The retro pivot had established "second person, present
tense, terse, deadpan" for DM narration, but it did not yet define the larger
voice clearly enough to guide content generation. The desired reference was
the text-game vernacular that survives in cultural memory even for people who
did not play its source games: parser adventures, battle announcers,
roguelike/MUD event lines, and system/menu messages.

**The composite settled.** The parser-adventure voice is the backbone for
world prose: second person, present tense, spatial, external, and dry. The
JRPG/roguelike announcer is an accent for discrete events and displays:
abrupt subject-verb-result lines, compact labels, occasional earned ALL CAPS
and exclamation marks. The `>` prompt belongs only to real commands or
selectable actions. This is a shared cultural shorthand, not an imitation of
one title and not permission to fill every line with retro catchphrases.

**Content follows the same voice.** Quests, locations, NPC hooks, items,
creatures, and epilogues are game pieces rather than miniature stories. They
lead with a concrete problem or place, give one memorable material detail,
and expose something visible or actionable. Familiar fantasy nouns are a
strength; specificity comes from their arrangement, not from purple synonyms
or lore piled in front of the player. Comedy remains in the situation and is
reported straight.

**Documentation decision.** Added `writing.md` as the canonical shared guide
for words inside the game. `dm.md` continues to own play protocol and applies
the guide at the table. `develop.md` continues to own the thorough development
register, but points content authors and generators to `writing.md`. The
dispatcher now requires the shared guide in play and whenever development
touches fictional content. The planned quest wording pass remains open; this
session supplies its acceptance standard rather than performing that rewrite.

## 2026-07-22 — Unified place hierarchy and navigation foundation

**The problem.** Geography had two chains that met only at settlements:
lands contained settlement/wild `location` records, while each quest privately
contained sites and rooms. A tower therefore existed only as part of a quest,
natural places stopped at one undifferentiated level, and `region`, `location`,
and `site` had begun to overlap in discussion. The planned procedural-detail
system needed stable places before it could generate anything coherent.

**Vocabulary settled:** **Land -> Area -> Site -> Room**. Land remains the
evocative macro territory rather than being renamed Region. Area is the
world-map destination and may be a settlement, forest, mountain, plain, or
other substantial geography. Site is a local building, street, landmark, or
minor natural place. Room is the engine's smallest persistent node, literal
indoors and text-adventure-spatial outdoors. “Place” is the generic prose word;
`location` is no longer a schema tier, and the party carries a breadcrumb
`position`. Classification follows gameplay scale: a castle is normally a
site, but a fortress-city with independent districts is an area.

Area records use `kind=settlement|natural`; `subtype` carries the meaningful
shape (capital/town/village or forest/wetland/highlands/etc.). This keeps rules
that care about walls separate from descriptive geography without flattening
all of nature back into one "wilderness" type.

**Ownership settled.** Geography belongs to the world. Quests retain premise,
giver, objectives/progress, alignment, and rewards, but their site list now
contains IDs into the world's site store; sites likewise point to world-owned
rooms. The current quest generator still creates the same layouts and rosters
at the same time — procedural detail generation is explicitly out of scope —
but the resulting places persist and can later be revisited, changed, or used
by another system. A site-clear payment belongs to the quest challenge at the
site, not intrinsically to the geography.

**Navigation slice.** `travel AREA` remains the day-scale move and resets the
local breadcrumb. `look` shows the current branch, `go` enters a known site or
room at no day cost, and `back` moves outward. Taking a quest requires its
origin area and reveals its first site; fighting requires entering the current
target site. Settlement conveniences stay area-scoped shortcuts so the new
hierarchy does not manufacture walking chores. The tree may be sparse and UI
may collapse unary levels; generated children must add a landmark, function,
obstacle, or affordance instead of repeating “forest” at every depth.

**UI boundary.** The newly shipped `ui/map.txt` is the macro Land/Area page.
The desired lower-level companion is **`ui/minimap.txt`**, showing the current
Area/Site/Room branch, exits, and local quest markers through the same rewrite
and `sheet`-commit lifecycle. That page is planned UI work, not part of this
slice; `look` is its command-line precursor, and `map.txt` temporarily retains
its existing taken-quest site summary.

## 2026-07-23 — Procedural place generation structure

**The desired world.** The continental sketch establishes a small number of
large, distinct realms and environments: icy dwarf mountains, temperate and
mediterranean human lands, elven and wild forests, goblin mediterranean
country, orc prairie, northern and tropical pirate islands, jungle, desert,
and Caelum, the city of angels and devils. The scale remains deliberately
game-like: a Land has a handful of memorable geographic Areas and settlements,
not a realistic census. The map itself remains planned context rather than
this slice's implementation target.

**The authored/generated boundary settled.** The world map, Land identities,
major wonders, and each Land's three or four major natural Area themes are
authored. Area names and ordinary settlement details may be rolled inside
those constraints. Most Sites and Rooms are generated lazily, then saved
permanently. Areas are finite: `explore` should reveal the authored inventory
instead of creating an unlimited succession of random moors and woods. After
the major geography is known, exploration materializes Sites within an Area.
The local layer may grow without a hard cap, but does not promise infinite
novelty.

**Land is no longer race.** The current race-keyed placeholder cannot express
two human realms with different climates, shared cultures, wild country,
mixed Caelum, pirate holdings in different environments, or later conquest.
A Land therefore gets its own identity, owner/faction, cultures, default
environment, encounter profile, Areas, and adjacency. Race remains a people
and culture input. The future grid projects Lands and terrain; it does not add
a structural tier to Land -> Area -> Site -> Room.

**Environment settled as inheritance.** A Land supplies a default climate,
weather distribution, vegetation palette, terrain tags, and natural content
pools. Areas inherit and specialize them; children consult ancestor tags
without copying the same descriptors down the tree. Climate is a distribution,
not current weather. Persistent fog or magical snow is a feature; ordinary
rain belongs to a later day/weather roll.

**Place facts separated.** Core identity makes an ordinary place complete.
Template-specific required facets (cathedral material, path surface,
settlement wealth) are separate from optional features. Optional facts divide
into exclusive slots, compatible additive traits, mutable states, and rare
concrete curiosities. Links, services, resources, and child places remain
structural data rather than being flattened into adjectives. A Site is its own
default scene and may have no Rooms; deeper nodes exist only when they add a
landmark, function, obstacle, affordance, or local decision.

**Normality rule.** Optional feature counts roll 0/1/2/3 at
50%/30%/15%/5%, matching a 50% chance of any feature, 20% of a second, and
5% of a third. Required facets do not consume that budget. Within pools,
common/uncommon/rare content targets roughly 75%/20%/5%; unique wonders never
roll. Templates and exclusive slots prevent contradictions before pairwise
requirements and exclusions are checked. A place has at most one rare random
feature, and scope limits prevent rare curiosities from repeating throughout
one Area or Land.

**Knowledge and narration.** Feature knowledge uses `public`, `local`,
`explore`, and `hidden` reveal levels rather than calling the axis renown.
Scope, rarity, reveal, and salience are independent. A place may store several
facts while its DM-facing summary leads with one defining or actionable
detail, preserving `writing.md`'s restraint.

**Permanence and change.** Lazy generation uses stable child seeds and saves
the materialized result; returning never rerolls it. DM-authored and
DM-requested generated places become equally canonical when saved. Stable
identity remains beneath mutable states: a diseased forest may become
recovering without ceasing to be the same forest. Quests point at suitable
existing or newly materialized Sites and alter their state. They no longer
place every mountain, road, and den inside the giver's settlement merely
because the job originated there.

**Settlement boundary.** Settlement templates own tier, culture, setting,
wealth, resources, services, Sites, and civic states. Lodging, smith service,
and general goods are ordinary guarantees; capitals also guarantee an
alchemist, major market, and government seat. A service becomes a navigable
Site only when it creates a useful scene. Minor hamlets may be Sites in rural
Areas rather than equal macro destinations.

**Draft recorded.** `placegen.md` is the detailed planned specification and
first reviewable content inventory: nine environment profiles, natural Area
features and Site roles, paths, settlement tiers and pools, constructed Sites,
the cathedral and clergy-room example, curiosities, name generation, worked
forest/cathedral chains, and a vertical-slice implementation order. No
procedural-detail code ships in this session; `rules.md` remains unchanged.

## 2026-07-23 — Concrete place-content boundary and dwarf Land

**The review target corrected.** The first worksheet initially isolated an
environment profile and stopped before settlements, detailed Sites, Rooms,
and objects. That was too narrow for the intended implementation source. A
completed Land packet must now cover culture and environment together,
concrete Areas and their links, Site inventories, Room roles, and the visible
contents which make those Rooms usable in play.

**Room contents joined the MVP.** `placegen.md` now includes lightweight,
persistent Room-content records. An ordinary generated interior should list a
small number of stable furnishings, tools, food, containers, or personal
objects and allow the player to inspect the concrete scene. This is not yet a
general inventory, ownership, or object-physics system: only content which
already maps to a mechanical item needs portable-item behavior.

**Settlement counts settled.** An ordinary culturally settled Land begins
with one authored capital, two or three authored towns, and three
procedurally generated villages. The dwarf Land is the smaller exception:
one capital and two authored towns, with no extra initial villages. Ordinary
houses materialize lazily rather than simulating a full census, but once
generated their resident, Rooms, and contents persist.

**The first concrete Land.** The icy northwestern dwarf Land uses Alpine
Tundra and has three natural Areas: Frosthelm Mountains, Ironpine Forest, and
Lake Rime. Hammerhall is the normal central capital. Frostgate is the remote,
icier northern town. Ironhook is the southern fishing town on Lake Rime and
the trade link to the temperate human Land. Lake Rime and Ironhook are sibling
Areas; the lake owns its open water and wild shore, while the town owns the
built southern shore and its jetty.

**Vertical content chain.** `placegen_review.txt` now carries the first full
review packet through natural Sites, settlement Site inventories, Room roles,
shared object anchors, dwarf livelihood overlays, and an ordinary-house
example. The completion rule is structural rather than exhaustive: each Land
needs enough concrete templates and constrained pools to generate ordinary
places without improvising unsupported content at runtime.

**Completion track settled.** Procedural place generation is now the active
development track until it ships. Each Land, culture, and environment is
reviewed through the full Area -> Site -> Room -> contents chain in
`placegen_review.txt`; accepted decisions are consolidated into `placegen.md`;
then the canonical schemas and catalogs are implemented. Finishing the
worksheets alone does not finish the feature. Completion also requires stable
seeded generation, persistence, navigation/readouts, quest placement and
mutation, generated ordinary interiors, and reproducible verification. The
active track and its exit conditions are recorded in `plan.md`.

**The review surface simplified.** The worksheet is now a translation-style
string sheet rather than a miniature design packet. It contains names,
descriptions, Site and Room labels, and visible content strings under only the
context needed to identify them. The designer can cut an entry or give an
alternative wording without rereading schemas and rationale. Distribution,
counts, links, generation rules, explanations, completion criteria, and the
review process itself live in `placegen.md`; `plan.md` records the same
division for the active development track.

## 2026-07-24 — Dwarf naming and the optional-feature review pass

**Dwarf place names.** The dwarf culture uses an invented Germanic/Norse-
sounding creole, drawing loosely from Icelandic, Swedish, Norwegian, and
related languages rather than reproducing one real language. Names stay ASCII.
Plain English type nouns remain when useful for immediate recognition, as in
Drunurnar Mountains, Krokskogur Forest, and Lake Hornindal. The same rule
governs names improvised by the DM. The first Land's proper nouns are Drunurnar
Mountains, Krokskogur Forest, Lake Hornindal, Bjorgheim, Roros, and Svalaver.

**Review order.** Base Land sheets cover essential names, descriptions, Sites,
Rooms, and ordinary contents. Special nonessential material gets a separate
review phase: optional Area traits, mutable states, rare curiosities,
exceptional settlement features, and hidden or unusual Room contents. The
ordering was clarified after the first pass: finish the basic sheets for
**every** Land and climate first, consolidating each into `placegen.md`; only
then begin the global special-feature phase. This keeps the translation-style
base sheets readable and lets shared special pools be reviewed once instead
of repeated under every Land.

**Dwarf base pass consolidated.** The complete accepted worksheet now lives
canonically in `placegen.md`: the Alpine Tundra strings; six named Areas and
their descriptions; natural and settlement Site/Room inventories; the dwarf
ordinary-house and livelihood content; and shared basic Room-content pools
for halls, markets, inns, shops, smithies, guard rooms, jetties, and
smokehouses. The completed worksheet remains as the review record. The next
session begins the temperate human country basic pass; no special feature
review starts before then or between basic Land sessions.

## 2026-07-25 — Six-Land placegen MVP specification

**The implementation boundary narrowed.** Requiring every pirate,
wilderness, jungle, desert, and Caelum sheet before coding made the content
review process the critical path. The first implementation now covers the six
settled core Lands: Dvarvengrond, Firascir, Mortellaria, Ensimaa, Gibili, and
Tergal. Pirate islands, wilderness-only Lands, Caelum, and the global
special-feature pass remain planned content but no longer block an ordinary
place-generation vertical slice.

**The missing basic catalogs were completed.** Mortellaria, Ensimaa, Gibili,
and Tergal now match the concrete depth already established for Dvarvengrond
and Firascir. Each Land has Area descriptions, three ordinary natural Site
layouts per natural Area, authored settlement Site and Room skeletons, three
generated-village roles, culture-specific ordinary-house livelihood overlays,
and the additional Room-content pools needed by its materials and economy.
Their previously fixed proper nouns were not reopened.

**Finite worldgen counts are explicit.** All natural and settlement Area
records exist at world creation. Settlements begin known; natural Areas begin
unknown and discovery reveals rather than creates them. Generated village
names are drawn without replacement and assigned to fixed geographic roles.
Each natural Area exposes its three ordinary Site templates once in a stable
shuffled order; exhausted ordinary exploration may return nothing new while
quests and DM requests can still add compatible Sites.

**The first-pass code contract is explicit.** `placegen.md` now specifies the
definition/instance split, minimum saved fields, readable stable IDs,
digest-derived child seeds, world creation and lazy materialization order,
house-generation counts, quest geography requirements, Site-reuse rules,
minimum mutation operations, player and DM readouts, and deterministic
verification. The existing encounter budgets and foe pools remain unchanged.

**Implementation is the next handoff.** `placegen_review.txt` remains the
completed Firascir review record and a reusable narrow wording surface, not a
gate for four more Land sessions. The next build starts with the Firascir
vertical slice, verifies stable generation, contents, quest placement,
mutation, persistence, and output, then loads the other five catalogs through
the same path.

---

## 2026-07-26 — Quest length, and the attrition rework

**The trigger.** "There is too much combat per quest. 4 encounters for a
quest feel extremely long." The target: 1 encounter by default, 2 for a
middling job, 3 at most — and sites used only when the location genuinely
differs, never as the difficulty dial. Measurement confirmed the complaint
was structural, not a mood: the generator rolls sites 1/2/3 at 45/40/15 and
then rooms 1/2/3 at 20/40/40 *per site*, centring quests on **3.74
encounters**, with 47% at four or more and a tail reaching nine.

**The real problem was underneath.** Attrition currently lives inside a
quest — press through four rooms or camp and lose the XP streak. Cut to one
fight and there is nothing left to attrit: the party wins, camps to full
(`camp --heal` runs up to fourteen free nights; dm.md names "camp until
whole" as the played default), and HP has never mattered. The designer named
this himself: the goal is not a binary lose-win where winning means a free
full heal, leaving potions and healing with no place.

**Every cost-based fix dies on the same arithmetic.** Pricier taverns, food,
per-day upkeep, dearer potions — all of them price recovery in gold, and gold
is the one quantity that inflates. Quest gold is `15 x L` per site over
roughly four days: about **4 g/day at level 1 and 75 g/day at level 20**,
while HP pools barely double (12-20 base, +10 buyable). Flat prices are
brutal at the front door and rounding error at the back; scaled prices are a
curve to re-tune forever and, as the designer put it, make no sense — a bed
is a bed. The session's answer: **do not make rest expensive, make rest
incomplete.** Gate recovery on rate and access, never price. Time and
geography do not inflate.

**The wound system: two proposals met in the middle.** The first proposal was
an anonymous integer — wounds as HP the body cannot self-restore, capping
what a rest refills. The designer countered with a far more ambitious system:
named wounds as the primary track, HP demoted or removed, injury locations
with stat penalties, blood loss, lethal wounds at high severity, permanent
maiming, prosthetics that push stats past the natural cap, and tiered
potions. He was right that the anonymous integer was the balance-safe
minimum and a poor fit for a game whose whole pitch is an agent narrating
over engine output: the engine emits `deals 4 dmg, grievous` and the DM
invents the rest, differently each time, with no memory. Named located
wounds give the narration layer a persistent object it can refer back to
sessions later.

**Four decisions settled the scope.**

*HP stays the scalar.* Removing it is a rewrite, not a slice: the bestiary's
25 bench-fitted level/`ref_pack` annotations, the threat math, the death
spiral (`wound_penalty` = `hp_lost // pain`), the pause layer, and all five
bench harnesses are fitted against HP-as-a-number. Reframed instead — HP is
the blood-and-shock pool, max HP is the constitution stat already asked for,
and wounds lower the ceiling a rest can refill to. "HP only tracks how many
wounds you can carry" becomes literally true. The displayed number can still
vanish; that is a formatting pass, not a rewrite, and it buys the whole felt
effect.

*Injury is ONE system with two time constants* — settled after a reversal
worth recording. The first call was that wound stat-penalties should wait
until the *next* fight, to keep the running fight's math on terms the bench
already understands. The designer pushed back — he had understood the wound
system as unified all along — and he was right, on two counts. First, the
recap that reversal forced was itself wrong: `Entity.wound_penalty` is a live
property, `hp_lost // pain`, so because HP carries across fights the existing
penalty **already** carries across them; describing it as an "in-fight
spiral" was simply inaccurate. Second, a leg wound that does not slow you
until tomorrow is a bookkeeping entry, not the moment that locating wounds
exists to produce. So: one system, split by how fast each channel fades, not
by where it applies. HP is the fast channel (blood and shock, `wound_penalty`
unchanged, refills to the ceiling). Wounds are the slow channel (named,
located, ceiling-lowering, stat penalties). Both live in every fight,
including the one where the wound lands, with no `fresh` flag and no seam.
The real concern behind the original caution was magnitude, not architecture,
and it has a proper answer: shift part of the roll-penalty budget out of the
anonymous HP channel into the named wound channel by raising `HERO_PAIN`
2 -> 3, so total pressure at a given injury level stays near the bench
baseline while part of it becomes specific, located, and slow to heal.

*Foes keep the scalar.* They do not persist between fights, so records buy
nothing and would cost the entire bestiary calibration.

*The permanent setback is a maiming, not a stat point.* rules.md fixes STR
and DEX as immovable, and an unrecoverable stat point in a 1-20 ladder is a
death spiral in disguise. A maiming is the same mechanical hit, lives inside
the wound system, narrates better, and is curable — which turns a punishment
into a story hook and a gold sink, and makes prosthetics the natural first
customer of the already-queued stat-transcendence membrane.

**Conditions got built properly rather than as a bleed special case.** It has
been the named blocker behind varied enemies, venom, and varied magic for
three sessions; the designer's call was to do it once, as a framework, with
bleed and poison and burn as its first customers.

**Quest clocks turned out to be core, not an optional lever.** The designer's
insight, and a correction to the first proposal, which had filed day-costs as
a phase-three nicety: 3-7 day windows with pay banded by quick / on time /
late, and expiry with a failure epilogue, are what make days cost something
without a gold price. Healing takes days; days cost the job. The hidden price
is that quest expiry makes worldgen's up-front XP-coverage assert meaningless,
so the banded lazy refill — already queued — becomes a hard dependency rather
than a separate item.

**Three findings from checking the code rather than reasoning about it.**
Travel encounters are not broken, only rare and widest-valved exactly where a
new campaign is played: 15% per travel day, and then a notice contest turns
38% of level-1 rolls into a walk-away sighting, giving one road fight per
~11 one-day trips. But the roll fires *after* arrival, so a road fight is
narrated at the destination gates and draws from the destination land's pool
— a real wart, and one that stops being harmless the moment travel days
matter. `camp` likewise banks each night's healing *before* rolling the
visitor, which the designer had already suspected. And satisfaction ratchets:
gains (+1 quest clear, +1 tavern, +1/+2 downtime) beat losses (-1 fled, -1
bloodied, -2 Down, -2 death witness) on a normal cycle, and the rework makes
it worse by cutting fights and adding town nights — so the tavern bonus gets
a cooldown in slice 1 and wounds drain morale in slice 3, which is also how
"the party walks if you are laid up for weeks" arrives without new departure
machinery.

**Encounter count stays a weighted roll for now** (designer's call), with
site count becoming a template-declared place count. Letting the narrative
content decide a job's length is queued as its own design pass, to be
scheduled after the clock and wound slices have actually been played — what a
job's right length feels like is a play finding, not a desk one.

**Outcome.** A four-slice build contract as plan.md's NEXT BUILD section —
kept in the roadmap rather than a separate spec file, on the designer's call
that another top-level doc would be one more thing to keep in sync; it
propagates outward and is deleted slice by slice as each lands. One session
each:
quest shape and the pay rebase (with the streak and short rest deleted and
the three small fixes), quest clocks with the banded refill, the conditions
framework and then the wound system, and defeat-without-death built by
generalizing the mercy path that the karma layer already ships. Nothing
implemented this session by design; rules.md and dm.md stay untouched until
each slice lands, so the ruleset never describes a game that does not exist.

---

## 2026-07-26 (slice 4) — Literal Fate, one pause, survivable defeat

**The playtest found a false promise in Fate's bargain.** In a duo, the old
resolution killed the only companion after victory and left the PC Down, so
the ordinary wipe check immediately finished the spared PC. A larger party
did not guarantee safety either: if only one companion still stood, Fate
could kill that survivor rather than a Down companion and produce the same
wipe. The documented post-bargain retreat choice was also unreliable because
Fate's intervention did not create a pause of its own.

**The designer's recommendation was accepted:** make the trade literal. On a
paid victory Fate kills one companion and restores the PC to exactly 1 HP.
Wounds and all other damage remain. A duo therefore continues as a badly
wounded solo character. A Fate-paid victory is a victory and cannot then
spend Slice 4's defeat mercy; a genuinely lost Fate fight still can.

**The pause refinement mattered.** The first implementation direction called
the Fate decision independent of the wounds crossing. The designer clarified
that it must still consume the ordinary pause. The settled invariant is one
interrupt budget per encounter: the first ordinary wounds pause suppresses a
later Fate interrupt, and an unused pause spent by Fate suppresses every
later ordinary one. Fate's version offers only FIGHT ON / RETREAT because
drinking, healing, and conversion are not the bargain's question.

**Slice 4 generalized the existing posse mercy rather than adding another
resurrection system.** `FoeSpec.ferocity` is content:

- 0 — humanoids take the purse and quality weapons, then leave the party at
  1 HP;
- 1 — most beasts take nothing, but leave one random participant permanently
  maimed;
- 2 — undead, demons and conquest waves are relentless: no break and no
  mercy.

The allowance is one eligible mercy per PC character level and never banks.
The authored LAW / HELL outcomes keep their save reshaping but spend that
same allowance. Anyone dead before the encounter remains dead. Ferocity 0-1
foes also get one reverse-retreat attempt when every survivor is below half
HP or Spent; this reuses the party chase contest, and escaped foes are marked
withdrawn rather than manufactured as corpses.

**Measured outcome.** Across 500 careers, 500 defeat mercies fired and 86.2%
of careers survived at least one; median death rose from level 8 to 9. The
relentless barrow stayed at its old numbers, while the breaking-bandit
hideout returned to its intended clear band. Focused tests pin the original
failure cases explicitly: a paid duo victory, a depleted three-person party,
no post-Fate mercy, and both possible pause orderings.

## 2026-07-27 — Conquest slice 1: the domain game opens at level 4

**Where it came from.** The designer opened a brainstorm (partly in a
stray chat that lacked project context) about major additions: a 32x32
tile world map shaped like Europe, armies as units, a darker new setting,
and mechanics/quests ending with the world conquered by the level cap —
importing domain ideas from Reign / Birthright / Exalted / Godbound. The
out-of-context assistant's plan had good bones (prototype the loop, not
the map; armies never enter the combat engine; the hero's duel IS the
battle's resolution) but wrong premises: it warned about retrofitting a
province object the game already has (the settlement), proposed pacing
tiers the settlement bands already encode, and invented a `war.py` to
integrate with (the war layer is `story.py`, and its occupation machinery
is exactly the conquest chassis).

**The session's calls, in order:**

- **Map and new setting DEFERRED** — the designer's own call, first
  message. Conquest ships in the old setting on the list map; the tile
  map and the dark retheme wait for their own sessions.
- **The settlement is the ownership unit.** 6 lands / 39 settlements;
  the occupation layer already tags and gates settlements, so player
  ownership is the same shape with the seat swapped.
- **Do conquest FIRST, not after the arsenal.** The assistant initially
  recommended weapons/luxury first (the L15-20 band being the planned
  conquest home, and unplayable). The designer overruled with the
  project's own precedent — broad systems before content, prototype
  fast — and repointed conquest at the played band: village at 4-5,
  towns 6-8+. That also produced the AGENTS.md "played reality" note
  committed the same day: no playthrough has ever passed level 4;
  design inside the first four or five levels.
- **Garrison levels are fixed terrain, decoupled from posting bands.**
  The designer floated rebanding SETTLEMENT_KINDS (capital 15 / city 12
  / town 9 / village 6) and asked whether the city tier is even real
  (it was an accident: three harbor settlements — MERGED into town this
  session). Settled: a separate stable-seeded GARRISON band per
  settlement (village 3-5, town 6-10, capital 11-15, "maybe randomly" —
  the designer's numbers), so the quest economy's calibrated posting
  bands never moved and no bench broke. The posting-band trim is parked
  on its own merits.
- **Garrisons are levies, not party members.** The assistant's first
  "holding costs a body" idea died on a designer fact: recruits are
  free and replaceable. The army-resource framing (the designer's) won:
  one integer per holding, gold in, heads out, raids resolved
  heads-against-heads off screen. The parked army mechanic's seed, and
  gold's first standing job before L15.
- **Heat is the strategy layer.** Holding land raises the heat floor
  one step per holding (plan.md's 2026-07-19 suspicion, confirmed);
  posses answer the flag even at zero karma, and killing them feeds the
  karma ratchet. No new AI, no rival simulation — the crown's raids on
  ungarrisoned holdings are the only new pressure, and they are one
  rng roll.
- **Idea (b) sharpened**: the designer worried army-simulation-buys-
  easier-duels collapses into a difficulty slider. Answer adopted: the
  army side sets TERMS, not difficulty — in slice 1 that is simply
  garrison strength deciding retention, with richer terms (fighting the
  general without his bodyguard, guaranteed retreats) left to the
  army-movement session.
- **Pacing falls out instead of being pegged**: one land is a whole
  campaign (3 villages -> towns -> capital ~L14), answering "conquer a
  country by 10 or 15?" with ~15. The other five lands are where
  moving armies belong later — the player decapitates, armies do the
  repetition. World conquest by cap stays the target; nothing above the
  first land is designed yet, per the played-reality note.
- **The narrative framings** (chosen one / dark lord / mad inventor /
  imperial general / prophet) map almost 1:1 onto story.py's four
  authored aggressor variants; "the player as the fifth aggressor" is
  recorded as the cheap route when the content pass comes. Deferred
  with the setting rework.

**Shipped** (same session, "implementation using your best judgement"):
`conquest.py` + session surface (`conquer` / `garrison` / `holdings`,
conquest_news at the news points, the heat floor in maybe_punish, the
[YOURS] map tag, the flip in _close_site), the city-tier merge,
`test_conquest.py` (24 contracts), rules.md's Conquest & Holdings
add-on, and a benchlog sanity run (city merge invisible at 100 careers).
Every knob hand-set, sim-unverified, per the dark layer's standing
directive.

**The slice's play probe** (next): take one village by ~L5 on a fresh
save, hold it through a raid and a reckoning, feel the tribute. Watch
for: does the second conquest differ from the first; does the heat
floor read as a throttle or a tax; is 6%/day raiding too quiet to
notice or too loud to leave home.

## 2026-07-28 — The weapon generation system: one currency, ten rungs

**The ask** (designer): a full weapon assortment — trash chargen arms,
lootable martial steel, purchasable quality, a nonsupernatural master-smith
tier, then magic/legendary/mythic — with the design settled first: what is
max weapon power, how do profiles stay characteristic, how are unlike
advantages priced to equal value, how does the ladder map to levels, what
do interesting extras cost (statuses, a first-strike-at-range quirk,
gold/karma-per-kill oddities). Plus pregenerated famous magic weapons with
known owners who wield them, 10-15 weapon-reward quests, and legendary
smiths with a max tier and too much pride to work below it.

**The road.** Three existing doctrines answered most of it before anything
new was invented. (1) The transcendence doctrine already fixes the item
budget: gear may push a stat to ~double natural, so the weapon's share was
set at HALF of that — +3 signature-stat equivalents, the mythic cap.
(2) The standing +DEX warning became the price list's spine: DEX-axis
advantages cost 3x the severity unit and true +DEX is gated to legendary.
(3) The decisive find: the quality four already ENCODE the exchange rate —
they are bench-verified equal, and solving rapier = katana = zweihander
gives atk 2 / def 2 / sev 1, all four chassis at exactly 3 severity-points.
The sp became the design currency; gold derives from it superlinearly
(doubling per sp) because career gold is ~thousands and a linear price
would sell mythic steel for lunch money. The ladder came out at ~ten rungs
(-1 trash to 10 mythic), not twenty — tiers map to level bands through the
reward ladder instead of pretending one rung per level.

**Decided** (designer: masterwork shoppable, no all-stats McGuffin; the
rest delegated and called as follows):
- Mythic cap +3 signature equivalents (~10 sp) — half the doubling.
- True +DEX legendary+ only at 3 sp; attack pressure is the DEX axis
  below that.
- Masterwork = +1 attack pressure uniformly (+2 sp, so every chassis
  lands at 5 sp — the old "+1 signature axis" priced rapiers and
  zweihanders unequally), durability 5, 5x price, capitals only.
- Weapon rewards are a PAY-BAND MODE of the existing generator (15% of
  postings swap the turn-in gold lump for level-graded steel), not a
  separate quest family.
- Smith pride floor = cap - 1; three smiths per world at caps 7/8/9 with
  styles; commissions at value x1.5 — the L15+ gold sink arriving early.
- Riders priced off the measured shipped customers (burn/bleed 1 sp,
  poison/rime 2 sp); quirks capped at one per weapon; the economy quirks
  (Midas gold, karma-on-kill) cost 0 sp and are priced in story, with a
  3-kill-per-fight engine cap so swarm rooms are not mints.
- Profile rule: >= 2/3 of budget on the chassis's signature axis, at most
  one rider, one quirk — "a rapier, but more so, with one twist".
- The trash chargen deal is SESSION-ONLY (cmd_new); recruits and sims
  keep the old table, so the whole bench suite stays byte-identical.

**Shipped in the same session**: engine hooks (Weapon schema, equip
bookkeeping, the wielder rider hook, the lunge, on-kill counters,
proficiency-follows-the-chassis), weapons.py (generator + armory +
smiths), worldgen attachment on derived rngs (posting streams verified
byte-identical), the session surface (claim / armory / commission /
masterwork buy / quirk collection), test_weapon_gen.py (33 contracts),
and the docs. Deliberately NOT verified by sim: no magic weapon ever
reaches a bench party yet — the reward ladder and smiths are played
surfaces. The owed follow-ups: a top-band career re-bench once sim
parties can hold generated steel, and a bench_weapons budget-honesty
matrix (equal-sp columns on the bench_abilities pattern) before any
tuning of the sp prices is trusted.

**The play probe** (next, and inside the first five levels per the
played-reality rule): feel the trash start's first looted shortsword;
save toward quality by ~L3; hear the armory rumor at a tavern and check
the pull of a named blade with a known address; post one weapon-reward
job and see whether "pays a katana" reads better on the board than its
gold would.

---

## 2026-07-29 — Fate's bargain: the debt made unconditional

**Where it came from.** A play probe on a fresh save (Zonk, goblin
wizard duo, L1) took hell's day-1 assignment — an L3 room, 2x Ice Demon
— straight off the doorstep. Round 2 killed the PC and Fate commuted it;
the interrupt offered FIGHT ON / RETREAT; the player fought on and lost
in round 4. Feng took a crippling blow to a limb and was permanently
maimed by the wound table, then the demons' TAKE SPOILS mercy (the Ice
Demon is a hexer reskin, ferocity 0) took both staves and spent the
level's allowance. Feng **lived**, and the designer's immediate reaction
was that this was wrong: "the player got saved, party member must die."

**What the code was doing.** Correctly, per the old spec:
`_settle_fate_debt` cleared the debt but returned early while any foe
still stood, so the price was collected only on a victory. rules.md said
so explicitly ("If the party loses anyway, the debt is not collected.
That genuine loss may receive defeat mercy").

**Why that was a bug in the design, not just in taste.** It inverted the
interrupt's own decision. At the pause the three exits priced out as:

    win     -> a companion dies
    retreat -> the fight is given up
    lose    -> nothing owed

So *losing was strictly cheaper than winning*, and the played instance
proved it: fighting on with a Down PC and a bloodied companion against a
full-HP L3 caster was not a bet on victory, and the loss was the
outcome that kept the companion. Retreat was squeezed from both sides —
it cost the fight to avoid a price a loss avoided for free. Worse, the
loss branch made the spare *worthless* against a RELENTLESS roster: no
mercy, `party_wiped`, PC dead a moment later — exactly the "fake
reprieve followed by party_wiped" the docstring claimed to prevent.

**The first decision (superseded within the hour — see below).** Fate is
owed, not conditional: any fought-out fight pays, won or lost, while a
clean retreat still waived. That priced the exits as:

    win     -> a companion dies, fight banked
    lose    -> a companion dies, nothing banked
    retreat -> nobody dies, fight given up

**The correction.** The designer read that and rejected the retreat
carve-out on the spot: the bargain "should trigger also when retreating.
doesn't make sense otherwise." Correct, and for the same reason the loss
exemption was wrong — a waiver is an exit, and an exit is a discount on
a price the fiction says is already owed. The PC's life was spent in
round 2; nothing the party does in round 3 can un-spend it. Keeping the
waiver would just have moved the exploit from "lose on purpose" to "flee
on purpose", which is cheaper still (a flight costs less damage than a
loss).

So the debt is **unconditional**. Win, loss, staggered-apart, ordinary
retreat, smoke break, and rank-2 blink-out all bury one companion:

    win     -> a companion dies, fight banked
    lose    -> a companion dies, nothing banked
    retreat -> a companion dies, room given up

The interrupt stops being a question about the debt and becomes the only
question actually left: **is this room still worth trying?** Press on for
the pay, or break off and keep the damage you have. That reading also
makes the pause honest — it never again offers something it cannot
deliver.

**The one deferral** is a FAILED break: run down at the door, the fight
is not over, so the debt settles at its real end instead. Anything else
would collect twice.

**The considered alternative** (rejected by the designer) was to leave
the loss exemption and instead bar defeat mercy after a spare, making
the spare itself the level's one reprieve. It closes the same exploit
with a smaller diff, but it prices the spare in the PC's own safety
rather than in a companion's life, which is not what the bargain says
on the tin.

**Interactions settled while implementing.** A paid fight never also
spends slice 4's defeat mercy — and this needs no new guard, because the
1 HP restoration makes `party_defeated` false before `apply_mercy` is
reached; the existing `fate_paid` short-circuit in `finish_encounter`
covers the rest. A paid LOSS therefore resolves as UNCLEARED (foes still
standing): no pay, no XP, the room keeps its survivors, the purse and
the quality steel are kept, and the level's allowance is left unspent.
If every companion is already dead when the fight ends the debt has no
victim left, and it is treated as settled — the PC still rises at 1 HP.

`_settle_fate_debt` grew a `fled` flag and now has four call sites: the
melee tail in `group_combat`, both clean-escape branches of
`attempt_retreat`, and `blink_escape`. The escape branches settle
*before* the breath, so the restored PC catches it and the paid companion
does not. Three log wordings, one per ending (the dying blow, the lost
field, the price finding someone on the way out) — the spare's own line
no longer promises anything about winning, and the pause menu now states
that breaking off pays at the door rather than offering a waiver.

**Not a rebalance.** The sims never set the protagonist flag, so no
bench number moves; the whole suite (201 tests) is green with five new
Fate contracts — paid loss, paid retreat, paid blink-out, deferred failed
break, and a session-tail integration test asserting a paid loss banks
nothing.

## 2026-08-03 — Past Due: the collections ladder (the pact's clock made fair)

**The trigger was a playtest.** The first pact playthrough to actually
answer hell's letter hit the enforcement machinery head-on, and it played
as incoherent rather than hard. The sequence: the first assignment landed
on day 1 at level 2 against a level-1 day-one duo (spread 0..+2 rolled
+1); the grace ran from that day, flat 4 days, while leveling up enough to
survive the job — the sensible play — consumed all of it; the party then
TOOK the job and was punished twice for "Chickening Out" *while traveling
to the site*: a level-3 relentless posse on day 6 (a severity-2 wound) and
a level-4 one on day 8 (a permanent maiming and a lost eye, one blow short
of Fate's bargain). The designer's verdict: the expiry-and-injury dynamic
was felt and partly enjoyed, but the design was wrong — compliance was
being punished, and the name said so.

**What was judged a coherence bug, not tuning.** Three things would have
been wrong at any numbers: enforcement fired on a taken, actively-worked
assignment (the check only looked at "not done"); the flat grace ignored
geography in a world where reaching a job routinely costs road days; and
the fresh pact's letter came on day 1, above level, with the clock already
running. The escalation shape (+1 start, +1 per visit, cap +3 over,
cooldown 2, all relentless) was ALSO too steep, but that part is tuning.

**The mechanic stays — reshaped as debt collection.** Punishment posses
were kept (without teeth, ignoring hell is free and the pact layer goes
inert; and a collections agent of Hell in a borrowed body is exactly the
register). The alternative — purely economic punishment, rising bribe
costs and docked pay — was considered and rejected: coherent, but it
deletes the visits, and with them both the threat and the comedy.

**The shipped shape (the designer settled the open calls):**

- **The first-ever assignment is fixed level 1** (`FIRST_TASK_LEVEL`; the
  party always starts as a duo, so no scaling subtlety is needed). Later
  assignments soften from spread 0..+2 to 0..+1 (`TASK_SPREAD`). The
  first letter was briefly moved to ~day 4, then put back to day 1 on
  the designer's call the same session: with the job at L1 and the
  grace covering only the taking, the early letter is a free OPTION on
  the table, not a clock already running -- which is the point of the
  pact frame.
- **Grace covers TAKING, and taking stops enforcement.** The giver is
  local, so 4 days to take is honest. Taking stamps a **visible
  completion window** on the quest — `TASK_WINDOW_DAYS` (4-6) + the road
  days to the first site — carried by the ordinary deadline machinery, so
  every readout prints the clock (the designer chose visible over
  hidden). Hell work is never LOST off that clock: `board_clock` skips
  hell tasks, late turn-ins pay the ordinary bands down to x0, and only
  done / withdrawn / bribed ends the matter. Past the window the ladder
  resumes instead.
- **The ladder warns once, then climbs gently.** First visit of a refusal
  is a WARNING — a clerk from Hell, three forms, no weapon, no fight, no
  chance roll (informing is the point), naming the final-notice date.
  Fights then come at **party level, +1 per visit fought, capped +2
  over** (`ENFORCE_CAP_OVER`), cooldown 4 days (was 2). Only the capped
  top rung is relentless; earlier rungs break when beaten — junior
  devils who run when it goes badly and come back with paperwork.
  (One warning is enough — the designer's call; a blown taken-window
  does not re-warn, the visible clock was the warning.)
- **Assignments stay serial** (no letter while one is open — unchanged,
  now documented as a design fact), and **`bribe` resets the ladder**
  (warning and all) and stretches a taken job's window by the bought
  days — ease that left the deadline blown would be no ease.
- **Renamed.** "Chickening Out" was wrong twice — unclear on its own, and
  it fired on non-chickens. The state is **PAST DUE**, the posse label
  "hell's collections", the banner `*** PAST DUE ***`.

**Explicitly left alone:** the honest board's windows (3-7 days, priced
in gold, failure rumors working) — re-judge the overall time pressure
after this lands; the posting-window knob (`QUEST_WINDOW_DAYS`) is the
one lever if it still feels tight. The law's posses, the heat formula,
and the LAW/HELL mercy reshaping are untouched.

## 2026-08-04 — The dark rework: assignments from Hell, crime as actions

**The designer's brainstorm.** Dark quests should be sorted into two
different things. Actual assignments from hell should be FEW, like the
war waves — pinned levels, longer deadlines, occult content (hellgate,
desecration, blood sacrifice) — with refusal triggering a retribution
chain of three attacks at same level / +1 / +2. Crime, meanwhile,
should stop being quests at all: free actions the PC takes because they
want to (NPCs freely attacked or robbed, puppies kicked, lunches left
unpaid), the whole questgiver frame gone, material gain flowing directly
from the deed. Wanted from the session: a crime catalogue with
mechanics (XP/karma, gold, fights, checks), an answer to crime
difficulty that avoids both auto-levelling and impossible/trivial
noise, gamification (a log/history page with a crime tally and
suggestion unlocks), a bad-karma→sin rename, a monotony/creativity
mechanism, and an answer to the karma-neutralization dodge.

**The analysis that shaped the answers.** Most of the machinery already
existed: the requested retribution chain IS the shipped Past Due ladder
(+0/+1/+2 capped, warning first); level pins have the war-wave model;
the crime ability check is the caper deed generalized; leveled
individuals are the conquest garrison doctrine (geography, not gates)
applied to people. The refuser analysis found the real gap: under pins,
the old endless top-rung enforcement plus the serial rule would leave a
good-alignment campaign permanently besieged behind one refused job —
hence the FINITE chain with a write-off and a `defied` ledger.
Neutralization: the dodge is real (only good work burns, instantly,
1:1; small crime lumps make staying under the step easy), but lifetime
sin never burns, so the unlock spine is laundering-proof; the fix
chosen is a NEWS CYCLE (a big single score floors heat at 1 for a few
days regardless of penance) rather than a 2:1 penance rate, which would
break the tuned one-quest-one-step symmetry everywhere.

**Decided** (the full implementation spec is plan.md's THE DARK REWORK
section — three sessions, A assignments / B crime actions / C surface):

- Pins at ODD levels 1–19, ten per career — the designer chose "more
  frequent" over the proposed sparser six.
- The occult ten (nine existing + a new Desecrate the Shrine) form a
  per-save shuffled DECK dealt one per pin, in RANDOM order by
  directive: the proposed thematic curriculum arc (hellgate last) was
  overruled with the played-reality argument turned back on it — only
  the first levels ever get played, so variety beats sense. Band
  feasibility still gates the deal (skip-and-keep).
- The finite retribution chain: warning + three fights, then write-off.
- Crime difficulty by MARK level (banded wealth+protection, settlement
  kind gates the top, casing free); the posse/heat layer stays the
  world's aftermath pushback.
- Petty crime pays (small) XP, all sin — designer call.
- Monotony: per-category day-stamp window (temporary by construction;
  alternating two categories does NOT reset — intended), plus a
  first-time ×1.5 creativity bonus; gold never depreciates.
- Unlocks gate suggestions, never permission; full list ~4,750 lifetime
  sin (half of half the 19,000 XP budget), first suggestion unlocked by
  the first completed assignment.
- The news cycle for neutralization; petty laundering stays viable on
  purpose.
- Bad karma → SIN, save keys included.

**The no-backwards-compatibility directive** (recorded as a standing
rule, develop.md): the designer is the only player, playtests end at
the first big break and restart fresh — save compatibility is NEVER a
design input, old-save shims and round-trip assertions are to be
deleted as touched, never added. Optimize for the good game, not for
old saves.

## 2026-08-04 (later) — The punishment budget: one devastating visit

Designer follow-up on the dark rework, opening the retribution question
wider: how does punishment sit against the game's encounter budget?

**The arithmetic.** Levelling takes ~2-3 fights (one at-level quest ~
one level step; quests average 1.66 encounters; the career sim runs ~2
quests/level plus road fights). Ten pins x the three-fight chain = 30
hell fights ~ 1.6/level for a SINLESS career — a third of its combat
spent on a layer it opted out of. The mirror is worse: at sustained
heat the law fired every ~2.5 days ~ 2 posses/level at early pacing,
and that cadence was tuned 2026-07-19, BEFORE persistent wounds and
quest deadlines made every fight cost more — constant invasions that
make normal questing and deadline-keeping impossible. Both pure
playthroughs (max good, max evil) are the obvious ways to play; neither
may be dominated by punishment. The designer's doctrine, recorded: hell
quests are a HOOK into dark play, not the game; target ~0.5 punishment
fights per level per side.

**The decision.** Of the two candidate fixes — fewer pins (four total,
keeping the chain of three, ~0.6/level) vs ONE visit per refusal
(keeping the odd-level pins, 10/19 ~ 0.53/level) — the single visit
won: it hits the budget AND keeps the deck's variety in the only band
ever played (the four-pin variant would put one assignment before
level 4, against the same session's variety directive). The visit
rolls party level + 0..+2 (`ENFORCE_SPREAD`) — potentially devastating,
never dominating — ferocity breaks-when-beaten (retreat stays viable;
the +2 roll is the devastation, not relentlessness). The account
closes when the visit resolves HOWEVER it ends (won, lost, fled —
hell's point is made); losing keeps the mercy fine. The beatings
counter and the +1-per-visit escalation die with the chain. The law
eased to the same budget: PUNISH_COOLDOWN_DAYS 2 -> 6, ~0.8
posses/level at sustained max heat. plan.md's THE DARK REWORK section
updated in place (decisions 3 and 9, "The punishment budget").

## 2026-08-04 (session C) — The surface: the record, the sheet, the rename

The dark rework's third and last slice, built from plan.md's spec. No
new mechanics: session C is where the two shipped layers get a face.

**The record.** `ui/history.txt` joins party.txt and map.txt as a
rewritten-every-save, committed-by-`sheet` page. It cashes the parked
"quest history readout" and reframes it: not a memoir, a CONTINUITY
CRIB. A playthrough spans days of real time, and the chat scrollback is
not a record — before a scene that leans on the past, the DM reads the
page. Four sections (jobs done, the remarkable, the tally of sin, the
suggestions), and every entry is booked by the code at the moment it
happens; the DM's only hand on it is a NAMED `sin dark N REASON` and
editing the save.

**Three build decisions worth keeping.** (1) The tally's "last day"
could not be read off the monotony window: those stamps prune
themselves as they are read, which is exactly what makes monotony
temporary, so the record keeps its own `last`. The general shape —
*hell's boredom forgets, the record does not* — is the right split and
should survive any retune of the window. (2) Maimings are SCANNED at
save rather than hooked into `_attack`; the duplicate guard in
`remember` is what makes that safe, and it costs nothing. (3) Named
kills are detected by SHAPE (a foe whose name has no trailing catalog
number is somebody the fiction cast) rather than by a new Entity flag —
no serialization change, and it picks up every naming site for free:
quest bosses, conquest defenders, posse leaders, the war's lieutenants.

**The `crimes` sheet** is the `prices` pattern pointed at the dark
side. The distinction it draws is the useful one: `case` reads TODAY'S
rolled mark exactly (level, take, roster), `crimes` reads the BAND — it
answers "what is worth doing here" without twenty-seven casings. It
prints each category's authored what-stands-in-the-way line rather than
its guard pool, because the roster is built at the mark's level anyway
and a pool dump says nothing.

**The rename** ran through the save keys (`bad`/`bad_total`/
`good_total` → `sin`/`sin_total`/`penance_total`), every display
string, and the command (`karma` → `sin`, no alias). Heat kept its
name: it is the law's meter, not hell's. The sub-verbs became `sin dark
N` / `sin penance N` — the rename's own vocabulary rather than the old
bad/good pair. Applying the no-backwards-compatibility rule to the
files this touched also took out `session.ensure_weapon_layer`, the
last named lazy-upgrade branch in the codebase.

**What this closes.** THE DARK REWORK is complete. Nothing in it is
open, and the plan.md section stays only as the built spec. The next
dark-side questions are the ones the rework explicitly parked (hell
ranks and karma-gated powers, the geographic wanted level, standing
enterprises, nemesis persistence) plus the two things the crime layer
asked to judge from PLAY: the heat pump and the flat deed DC. All of
that wants a playthrough before it wants a design session.

## 2026-08-05 — The scene page: the DM message becomes a file

The problem on the table: the DM model does not hold writing.md's
register in chat. The guide is read once at session start and each
message is generated once, unrevised — by mid-session the voice has
drifted wry or purple and nothing in the loop pushes back.

**The fix is a medium change, not more instructions.** The DM message
moves out of chat into `ui/scene.txt`: draft, REREAD against
writing.md's Final check, edit, then commit — revision is possible in
a file and impossible in a sent message, and the reread is where both
style drift and gameplay inconsistencies get caught. The chat carries
the player's input and one link. The page holds the last three turns
(the lookback window, player input quoted as `>` lines);
`ui/transcript.txt` keeps the whole run, append-only. Both are
DM-authored; `sheet` commits them with the other pages
(`UI_COMMIT_PATHS` grew by two, plus a registration test).

**The fight display shrinks to start + link + end.** The scene page
carries the opening block (banner, room line, roster) and everything
after the last round (XP, banners, epilogue, tally); the
round-by-round middle stays behind the `ui/fight-short.txt` blob
link. The player's decisions live between fights, so the
between-fights numbers stay in front of them and the blow-by-blow
becomes opt-in.

**No markdown anywhere on a page.** The pages are GitHub text blobs:
code fences are noise there, and the engine's 40-column displays
render aligned without them. The whole page — prose included — wraps
at 40; a URL alone on its line is the one allowed overflow.

**`scene-example.txt` is the new worked model** (a game start and a
fight turn): "retro text adventure" is now answered by two full pages
to imitate rather than by rule text alone. dm.md's two stale style
lines died in the same pass ("with a little flavor", the
pulp-with-a-wink caveat) — the flat retro register no longer has
in-file competition.

Known trade-offs, accepted: URLs in a text blob are not clickable
(the player pins the scene page and refreshes; the chat link is the
way in), and the transcript is hand-maintained (the end-of-message
order in dm.md is the guard; engine-side turn bookkeeping is the
fallback if it proves leaky — parked).

## 2026-08-05 (session B) — Width corrected; dm.md sheds its dates

**The width rule, corrected same day.** Session A over-applied 40
columns to the whole scene page. The designer's phone soft-wraps plain
text; hard-wrapping prose just fossilizes ragged lines. The corrected
rule everywhere (dm.md, writing.md, scene-example.txt): 40 columns is
for DISPLAYS — engine printouts and DM-composed blocks, where a broken
line ruins a table — and narration prose is never hard-wrapped, one
plain line per paragraph, the screen does the rest. (The old
40-for-everything reasoning came from chat code blocks, which the
scene page retired anyway.)

**dm.md's inline history markers moved here.** Every dated marker —
"(2026-07-26)", "since 2026-07-13", "REWRITTEN ... by the wound
system", the renamed-from and replacing-the-flat-25% asides — is gone
from dm.md (writing.md's two went with them): the play docs now state
current law only. The dates were archaeology, they padded an already
long file, and `git log -p dm.md` recovers any exact attachment. For
the record, the ~70 removed markers clustered on the reworks this log
and benchlog.md already date: 07-09/07-10 (death spiral, retreat
softening, night geography, hunt ambush), 07-11 (party, CHA, the camp
default), 07-12 (the war, no-quest-board, flavor beats), 07-13 (the
streamlining batch: generated PC, on-request recruiting, autolevel,
reskinned drops, walkover chaining, set sites to DEV/TEST, level-up
menus), 07-14 (deliveries, numbers-live-in-displays), 07-15 (wizards,
out-of-combat magic), 07-16 (ranged combat, the notice contest),
07-17 (the 3-point level, moves, alchemy, kit shrink, knowers-only
conversions), 07-19 (the pact, prices, one-scene-beat, options-in-
the-block, taking-starts-it, no class gate), 07-21 (the one-log
rework, the flat telling), 07-22 (the retro register), 07-26 (the
wound system and everything it rewrote: deadlines, fate's bargain,
defeat mercy, quartermaster pass, per-quest pay, conditions, HP
words, night rules), 07-27/07-28 (conquest, the weapon ladder),
08-04 (the dark rework: crime, the record, the shadow board's
retirement), 08-05 (the scene page). New dm.md text gets no date
markers; this log carries the when.

## 2026-08-05 (session C) — The scene page becomes Markdown

Raw text turned out to have no good reading surface: the GitHub app
character-wraps txt blobs (words cut at the margin), and the 40-column
alternative reads as a ribbon on a PC. The scene page and transcript
are now **`ui/scene.md`** / **`ui/transcript.md`** — rendered
markdown, reflowing to any screen — and the links became real:
the fight log is a clickable link, and the page ends with a standing
party | map (| history) footer, so the pinned page hops to the boards
(the chat-once link drop is retired).

Markdown is STRUCTURE ONLY: a `## turn N (day D)` heading per turn,
the player's input as a `>` blockquote, links, and code fences around
every display block. Session A's "no code blocks" call is reversed
for displays alone — a fence is exactly what keeps a 40-column table
aligned in a rendered view — while prose stays plain paragraphs, no
emphasis, unwrapped, ASCII. The engine's own pages stay .txt: they
are pure displays and the code view suits them. scene-example.md
reworked to match; dm.md, writing.md, develop.md, AGENTS.md,
`UI_COMMIT_PATHS` and its test renamed along.

## 2026-08-05 (session D) — The scene page copies back to chat

Sessions B and C moved the DM's message onto a page for ONE reason: a
file can be reread and edited before the player sees it, a chat message
cannot. The side effect was not intended — the chat went silent, one
bare link per turn, and the player had to leave the conversation to read
the game. The revision workflow was the goal; the empty chat was the
price, and it turns out nothing charges it.

So the page keeps its job as the drafting and review surface, and the
finished turn is copied back: write `ui/scene.md`, reread it against
writing.md's Final check, edit, `sheet`, THEN paste the new turn's text
into chat with the page link under it. The order is the whole point —
the chat copy is a copy of committed text, never a first draft, or the
detour buys nothing.

Copied back: the turn's text, everything between the `>` line and the
footer, prose and fences and inline links as committed. Left off: the
turn heading, the quote of the player's own input, the standing footer —
the chat already has those or reaches them through the link.

**And the page drops to ONE turn.** Session B gave it a three-turn tail
because the chat had nothing in it: the page had to carry the lookback.
With the turn back in chat, the scrollback IS the lookback, and keeping
three turns on the page would mean the same text sitting in both places
two and three times over. So `ui/scene.md` is rewritten whole each
message and holds the current turn alone — rendered, wide-screen and
phone-legible, with the party | map | history footer. `ui/transcript.md`
was always the full record and now carries that job unshared. What is
left is one turn duplicated between chat and page, which is the point,
not waste: identical by construction, so a fix after posting is an edit
plus a plain correction line, never a silent divergence.

## 2026-08-05 — World & NPC simulation: the framing (macro-game part 1)

**Where it started.** The designer's brainstorm: the game's basic
problem is that NPCs and places don't matter — quests and levelling
carry everything and the world fades to background (combat, levelling
and the quest system judged good). On the table: places more
characteristic, with their own quests, and possibly FEWER of them (two
identical villages give no reason to care; a worry noted that cutting
might disturb conquest — which has never been played); a test mode
starting at a freely chosen or random high level, stats autogenerated;
simulating places (economic and political events, threats) and a large
premade cast of NPCs with simulated interactions (suspected overkill by
its own author); "jerkify the world" — powers and authorities often
oppressive, abusive, or provoking, inviting and part-justifying crime
and chaotic play (the GTA rude-civilians insight), grey-morality
freedom-fighter play, preferably from generated NPC character/morality
rather than authored content; BULLIES — high-level NPCs who confront
and defeat the player, revenge taken later; and rolling back the
three-trait sketch, under the criterion that a characteristic only
matters if mechanically backed or the player already cares.

**The discussion's moves.**

1. *The thread identified as retro roadmap item 4* — the macro-game
   design session, whose parked seed (off-screen event simulation) is
   the simulation half. The blandness diagnosis is 2026-07-19's
   "difficulty curve with a purse" one level up: places and NPCs are
   quest-delivery furniture — the board abstracts a settlement into a
   level number, givers are attached after the roll, notables do
   nothing.
2. *The designer's criterion adopted as the thread's design law* (the
   characteristic criterion, now in plan.md). It explains the trait
   sketch's failure and gates future flavor content — the parked
   settlement flavor lines are annotated with it.
3. *An ordering correction, the designer's catch*: the first proposed
   list had place identity + trim after the design session. Split
   instead — the TRIM is a subtraction needing no design input and
   goes first; the IDENTITY SCHEMA is what the session decides
   (authoring identities before the schema would author them twice).
   And the session is NOT a per-settlement content pass: its point is
   that identity is a seeded roll over shared vocabularies, and
   content is keyed to vocabulary, never to places.
4. *The designer's reduction*: everything presentable to the player
   comes through four primitives — quests, random encounters, sights,
   rumors/news — and every feature is a generator for them with good
   variety. Accepted with two additions: the PRICED MENU (standing
   player-initiated actions parameterized by local state — the crime
   layer's shape, which deliberately left the quest frame) and the
   STATE DIFF (persistent readouts showing change on return — the one
   channel where a simulation is legible as such), plus RECURRENCE as
   the cross-cutting property that makes an NPC exist. Six outlets,
   recorded in plan.md.
5. *"Isn't the macro layer just more quests?"* — the designer's push
   against the decision-verbs framing, largely conceded: the sim's
   main output IS board effects, and the macro-decision UX already
   exists (which stimuli you answer — which land, which jobs, which
   marks, when home). What "just quests" undersells survives as two
   invariants: the board must REACT to world state, and something must
   move WITHOUT a job being taken, visibly on return.
6. *The premade simulated cast rejected* as overkill in favor of
   event-named actors that persist (the record page's machinery).
   Numeric economy simulation likewise rejected — discrete states plus
   events that flip them; the strategy-game trap avoided again.
7. *Jerkify sharpened*: a disposition axis with mechanical teeth
   (sin/heat modifiers by desert, surfaced in `case`), and a
   DISTRIBUTION rather than uniform rudeness — choosing targets by
   casing is itself the vigilante game. *Bullies recognized as nearly
   free*: the ferocity-0 defeat mercy already is the encounter; what
   is missing is the spawn hook, the persisting face, and a revenge
   address — and the shape inverts the shelved nemesis, so the grudge
   needs no manufacturing.

**Decided.** The framing recorded as plan.md's THE WORLD & NPC
SIMULATION section; two implementation-ready specs greenlit there (the
high-level test start `new --level N`; the NPC trait rollback — dict
NPCs lose the sketch, heroes keep it); the settlement trim ordered
ahead of the design session, blocked only on the designer's counts;
the design session itself scheduled next, agenda in plan.md.

**Open.** The trim's counts; every identity field and event template;
the disposition mechanics' numbers; the bully's spawn hook; what dict
NPCs carry instead of traits; the landmark-problems tie-in.

---

## 2026-08-05 (build session) — The start at any level; traits become the companion layer

**Where it started.** The designer asked for plan.md's two ready specs
to be built — the high-level test start (spec A) and the NPC trait
rollback (spec B) — and amended both in the same breath. Three
amendments, each of which changed the shape of what shipped:

1. *The start level is ROLLED by default*, not asked for. Spec A had
   `--level N` on demand against an unchanged level-1 default; the
   designer wants a plain `new` to roll 1-18, with the flag as the
   override for a session testing one band.
2. *The PC is always a magic user* — with the designer's own reasoning
   attached as a question: a magic user can be levelled as a warrior,
   but not the other way around, right?
3. *The PC loses his traits too.* Spec B stopped at dict NPCs and said
   heroes keep the sketch; the amendment scopes traits to PARTY MEMBERS
   OTHER THAN THE PC.

**The road.**

- *The asymmetry checked, and it holds* (amendment 2's premise): the
  gift is rolled at creation and `learn_spell` refuses a non-wizard
  outright — a spellbook is diagrams to him — while nothing anywhere
  gates combat training, weapon proficiency or the move repertoire on
  being a non-caster. `autolearn_moves` skips wizards, but that is the
  autospend DOCTRINE choosing for a companion, not a rule about the
  player's menu. So the guarantee closes no door and opens the one door
  that cannot be opened later. It is implemented as a REROLL of the stat
  budget until MIND lands strictly highest (a ~23% roll, so a handful of
  tries), never as a nudge afterwards: a PC wizard's stats keep a
  wizard's natural shape.
- *Amendment 3 follows the same criterion that killed the giver sketch*
  (plan.md's characteristic criterion). Companion traits are chosen
  against at hiring and several move numbers; the PC's were neither —
  nobody hires him, and his sheet already suppressed the morale
  annotations because they baited mechanics talk at a character with no
  satisfaction track. Removing them retired `no_family` with them (the
  switch existed only to keep a child out of his opening scene) and made
  the `for_pc` sheet flag dead code.
- *A career start had to be more than a level number.* Points alone
  would have put a level-18 party in trash arms with an empty purse, so
  the start now hands the pair what those levels bought: the doctrine's
  spend (both heroes, PC included — the levelup menu is for played
  progression), quality steel plus the PC's band job-reward weapon, a
  purse at a fifth of the career's earnings, and the standard kit.
- *Two implementer's calls, both flagged for reversal.* (a) A FOCUS
  RULE: since the PC is now always a caster, handing him a rolled rapier
  would strip the staff's +Power — so a PC on the staff claims the STAFF
  of his band instead (`reward_weapon_for_level` took an optional
  chassis). (b) CAREER SPELLBOOKS: one per five levels at rank 1, because
  a level-18 wizard knowing exactly one spell is not what that band looks
  like from the inside. One constant turns it off.
- *A spec correction found by building it.* Spec A said stamp the pact's
  ledger to the highest pin "at or below" N. With level 1 now running
  through the same path, that would have marked pin 1 served and
  cancelled hell's tutorial job. Stamped STRICTLY BELOW instead: an even
  start waits for its next odd level, an odd start is pinned at once, and
  level 1 is untouched.
- *The opening ground generalized*: the start settlement and the opening
  hook now take the posting CLOSEST to the party's level. At level 1 that
  is arithmetically the old lowest-posting rule, so the ordinary opening
  did not move.

**Decided.** Both specs shipped with the three amendments (plan.md's
section rewritten as the built spec; rules.md's Party add-on carries the
played rules; `test_start.py` is the contract suite, 50 tests, and all
twelve suites pass). Traits are now the companion layer and only that.
The default `new` is a rolled level 1-18, `--level N` and `--race R` the
overrides.

**Open.** What dict NPCs carry instead of the sketch is still the design
session's question — and the PC's now-blank sheet asks it a second time:
he has no characteristics either, and whether he should (a background
chosen by the player, rather than rolled flavor) is a real question the
session can take. Whether the rolled band should be weighted rather than
uniform (the low levels are the played ones) is untested. The high bands
themselves remain unplayed — that is what the start exists to fix.

---

## 2026-08-05 — The drink moves to the fight's opening

**Where it started.** A player note, one sentence: the party auto-drinks
potions after a fight, and that doesn't make sense. It doesn't. The
quartermaster pass (2026-07-26) put the drink at a fight's END on the
reasoning that a potion answers the wound the fight just opened and the
next door may be an hour away. Played, the next thing after a fight is
usually not a door — it is `camp --heal`, or the road, or the healer. So
the pass was pouring a bought vial into a hero the NIGHT would have
healed for free. The old doctrine's own argument ("the vial is worth
more unopened when the night heals free") was aimed at the morning fire
and the shop counter; nobody noticed it points at the fight's end just
as hard.

**The road.** Three options were weighed. (a) Never auto-drink: every
drink a deliberate `use`. Clean, but it hands back exactly the
bookkeeping the pass was built to remove, and a companion bleeding out
with three potions in their pack is a bug in the fiction, not a
decision. (b) Keep the fight-end drink but narrow it to companions:
smallest change, keeps the waste. (c) Move the drink to the fight's
OPENING. The wound the pass exists to answer is the one a hero carries
INTO a fight, not out of one; and if the party camps, travels, or pays
the healer in between, the vial is simply never spent.

**Decided — (c).** `rpg.open_fight(party, log)` is the new party-level
opening: prep every living hero (`start_fight`, revive-only), then the
one drinking quartermaster pass. All seven played encounter openings go
through it; the two fight-END sites (`finish_encounter`, `cmd_retreat`'s
escape branch) deal only now, like every other trigger. `drink=True` has
exactly one caller in the whole codebase, and `test_potions.py` pins
that count in the source so the fence can't quietly widen again.

**What it costs.** Almost nothing in the numbers where two fights run
back to back — the same vial is spent, minutes later, and the standing
orders still drink mid-fight at the wounds crossing. It saves the vial
outright wherever a rest intervenes, which is most of the time. The one
visible change at the table: a hurt party now READS hurt between fights.
That is correct, and dm.md says so — don't prompt for a potion, and
don't read a low HP line as a problem needing a vial now; `camp --heal`
is the cheap answer, and the opening will spend the vial if the player
walks into steel still bleeding.

**Open.** Whether the opening drink makes the mid-fight standing-order
drink (the wounds crossing) partly redundant is untested — both are
cheap, and the redundancy only shows in a fight long enough to cross
twice.
