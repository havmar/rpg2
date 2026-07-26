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
