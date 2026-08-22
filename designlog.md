# Design log

Dated records of the major design sessions: what was discussed, the road
the discussion took, and what was decided. The *decisions* live on in
plan.md (roadmap), rules.md (mechanics), and dm.md (play) — this file
keeps the reasoning trail so a settled question stays settled. Newest
last. (The benchlog is this file's sibling for measured tuning.)

This is also where a FINISHED feature is written up: when something
ships, its plan.md entry is deleted and lands here as a dated entry —
what shipped, and the calls the spec left open that the build had to
settle. plan.md holds only what is still ahead (develop.md, "Where a
finished feature is written up").

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

## 2026-08-05 — Weather and the land economies: the first content packets

**Where it started.** The designer's second world-sim sitting brought
two idea dumps and a structural proposal. The proposal: places are
created on a NEED-TO-EXIST basis — a land starts with one capital, one
town, one village, and a further settlement materializes only when a
field demands a counterparty (a rival center of power), arriving
generic with few unique features. The dumps: WEATHER events (big rain
with a shelter-cabin table and a satisfaction dip; colds that deepen to
pneumonia; storm penalties on ranged and movement, with a dwarven
snowstorm variant; supernatural fog raising skeletons traced by rumor
to a necromancer; flooded fords and tolled bridges; drought hitting the
agricultural exporters and the orcs), and ECONOMY IDENTITIES for all
six lands from historical analogues — elves as 21st-century decadence
and manpower trouble, orcs as nomadic gift-economy herders whose lost
herds mean raids, dwarves as mining dynamics (deposit lifecycles, clan
claims, company-shop labor politics), Firascir as manorial feudalism
and crown debt, Mortellaria as baroque finance (paper money, banks,
tariffs, a colony), Gibili as stateless industrial labor-vs-capital —
with a weighted wealth roll (crisis / normal / prosperous) and the
principle that normal and prosperous stay mostly invisible. Questions
asked: is the direction good; is the material enough for the game
elements and agent-side content creation; should lands get similar
amounts; realistic detail beside generic-fantasy lands; can lazy
generation handle always-true / optional / wealth-dependent /
mutually-exclusive / relational entries.

**The calls.**

1. *Direction endorsed.* The packets are vocabulary-first, crisis-
   centered, and historically anchored — coherent trouble-bundles
   rather than random adjectives, which is exactly what the
   characteristic criterion demands. Crisis-as-content confirmed:
   prosperity shows through prices and the absence of trouble.
2. *The identity model resolved three-leveled*, refining the session
   agenda's earlier settlement-first sketch: authored LAND character
   (the packets), rolled land WEALTH state (weighted middle), an
   authored per-land CRISIS DECK drawn on need (the pact-deck
   pattern). Settlement identity derives from the land packet plus
   local tags plus the settlement-level rolls the session still owes
   (authority, disposition, tension).
3. *Need-to-exist settlements adopted as the trim's settled shape*,
   superseding count-picking: three seeded settlements per land, the
   authored catalog demoted to a reserve pool for lazy
   materialization — places.py's Site/house pattern lifted one tier.
4. *Lazy generation confirmed sufficient*, with the designer's five
   entry classes formalized as record kinds — fact / option / state /
   card / relation. Relations are authored directed edges read at
   roll time (derived states, never traded quantities); mutual
   exclusion is exclusive slots plus deck draws; the one guard rule:
   no quantity that needs per-day updating.
5. *Asymmetry doctrine*: lands do not need equal material — a floor
   (wealth roll, three-plus cards, one or two relations, one flavor
   anchor), depth above it following designer interest, generic-
   fantasy lands legitimate as contrast. The overlap guard for the
   four modern-flavored societies is the named PROBLEM AXIS per land.
6. *The cold cashes the parked DISEASE seed* — the attrition rework's
   third condition family arrives as weather fallout, with pneumonia
   as bounded deepening.
7. *Layer order recommended* for the dumps still to come: politics
   first (the authority/disposition schema needs it and half the
   economy cards lean on a political actor), religion folded into
   politics where it overlaps, monsters/fauna as assignment onto the
   existing per-land pools, magic and science riding the packets as
   flavor anchors until a card demands mechanics.
8. *Curation stance*: the designer hand-picks; assistant additions
   are few and marked [PROPOSED] (five in this pass — wildfire, dust
   storm, smog, the bank run, the herd drive). Flagged designer
   calls preserved in place: orc horse aesthetics, elven robot tone,
   dwarven sulfur sold to Hell.

**Recorded.** `worldsim.md` created as the thread's content resource
and framework (registered in develop.md's Files); plan.md's thread
section updated — the worldsim pointer, relations added to the
architecture doctrine, the trim entry rewritten to the need-to-exist
model, the identity-schema agenda bullet rewritten three-leveled.
Implementation deliberately deferred to its own session.

## 2026-08-06 — The ruler character: the politics dump's person half

**Where it started.** The designer opened the politics layer with a
historical-monarch trait catalog (~130 raw entries across ten
headings — personal character, intellect, religion, governing style,
political conduct, competence, war, health, relationships, plus a
non-trait circumstances footer), built to be filled with real
percentages: a parallel session is coding a dataset of European
monarchs to get the statistical distribution. This session's task was
the SHAPE only. The framing questions he brought: most entries are
scales of three (trait — unnamed neutral — opposite) while some are
binary (art patron has no hate-arts); how many named traits should an
NPC leader carry (3-5?); mark what is crown-only; merge duplicates
against the three uses — political land identity, PC interaction,
rumor fuel (frail health vs chronic illness need not be
distinguished); cut what cannot matter; find a SIMPLE consistency
guard so honorable and abusive never meet (goodness meta-tags?); what
to add (dumb/smart, something magic); tribal orc societies deferred;
keep it colorful but let extremes generate rarely; deliver fillable
column headers.

**The calls.**

1. *Axes and flags formalized.* An axis is two named poles around an
   unnamed neutral middle; a flag is one named pole and silence;
   neutral is never spoken. The fill-sheet answer to the presentation
   question: one row per axis, a probability cell per pole, neutral
   the unwritten remainder.
2. *The object is a flat word list.* Pole names are globally unique,
   so cards and rumor lines admit on bare words; the only companion
   keys are derived `heart` and `puppeteer`.
3. *Consistency by moral tags, not machinery.* Nine poles carry
   `good` or `dark`; one rule — never both tags on one person —
   blocks honorable+harsh-at-home while letting untagged traits mix
   freely (the honest miser king survives). `heart` is DERIVED from
   the tags, never rolled, stays hidden, and doubles as jerkify's
   desert anchor. Rejected alternatives: pairwise exclusion tables
   (bookkeeping), a rolled goodness core (a whole extra die for what
   derivation gives free). Plus a few row-level `never with` notes
   and an affliction cap of two.
4. *Count: rulers 3-5 centered on 4; lesser authorities 1-3 centered
   on 2.* Independent per-axis rolls off the dataset marginals,
   clamped to the window; one global scale knob reconciles real
   monarchs' trait density with the game's volume — the dataset
   supplies relative frequency, the knob supplies volume.
5. *Scope finding: one vocabulary serves the whole ladder.* Nearly
   every entry applies to any authority — king, border lord,
   toll-sheriff — which is exactly what the settlement identity
   roll needs; itinerant is the lone crown-only entry.
6. *Extremes are priced, not engineered.* Dramatic words stay in the
   vocabulary with small probability cells; the one structural
   extreme step (zealot, occupying faith's slot) demonstrates the
   mechanism without generalizing it.
7. *The big merges* (the full ledger lives in worldsim.md): the
   entire Competence heading collapsed into the wits axis; the
   24-entry health catalog into four affliction flags (sickly /
   drunkard / troubled / mad); the home-life cluster into hearth;
   the puppeteer crowd (mother, minister, favorite, elite capture)
   into one puppet flag whose `puppeteer` field carries the color;
   fratricidal moved out of traits into a kin-blood accession
   circumstance.
8. *Additions:* wits and the sorcery axis by request — sorcery
   shaped as a STANCE (spell-friendly / spell-fearing) plus a rare
   `gifted` flag, because the PC is always a caster and a
   spell-fearing court is a direct PC problem. Marked [PROPOSED]
   for the designer's cut: the strangers axis (how court receives a
   mixed party; Ensimaa's foreigner states already want it), the
   looks axis (epithet history runs on appearance), and the
   succession-state circumstance.
9. *Deferred by directive:* all probabilities (the dataset session's
   work — European monarchs fill the human-crown baseline column);
   orc/tribal rewording via later per-race probability columns; the
   trait-to-card wiring and the authority kind/tension schema (the
   design session still owns those).

**Recorded.** worldsim.md gained THE RULER CHARACTER section (the
shape, the consistency rules, both fill sheets, the annotated merge
ledger, the cut list, circumstances); its intro and layers-to-dump
note now show politics half-dumped. develop.md's worldsim.md Files
entry extended; plan.md's identity-schema and what-dict-NPCs-carry
agenda bullets point at the draft.

## 2026-08-06 (session B) — Range over restraint: the afflictions uncollapsed

**Where it started.** Reviewing the morning's ruler-character section,
the designer overruled two of its calls: the register-miss cut
(suicidal behavior, disordered eating, seizures, and memory impairment
removed as "register misses for this game") and the health collapse
(one `mad`, one `troubled` flag). The direction behind the reversal:
the game has been moving away from generic heroic fantasy — injuries,
crime, realistic economic trouble — and the priority is memorable,
vivid content. A suicidal or eating-disordered king is exactly the
rumor that is remembered; with a planned ~1% probability floor for
rare things, specific entries cost nothing. And the content
instructions themselves must not be able to sand this off.

**The calls.**

1. *The affliction family uncollapsed.* Melancholy, manic, sees
   visions, delusions, death-wish, failing mind, and sleepless
   replace `troubled` and `mad`; crippled and falling-sickness split
   out of sickly; the table axis (glutton / eats nothing) restores
   disordered eating widened to both extremes. "Mad King" is demoted
   to a fiction READING over the specific rolled words — cards that
   want the family admit on any-of; the specific word is what rolls.
2. *The register-miss cut deleted* and a RANGE DOCTRINE subsection
   written in its place: the widest range the catalog allows,
   scandalous and clinical included; rarity is the probability
   column's job, never the vocabulary's; no register or writing pass
   may collapse vivid specifics into a safer generic word.
3. *writing.md's Tone section rewritten to match.* "It is never
   grimdark realism" was a blanket over material; it now bans
   grimdark DELIVERY only — dark material is in range, wallowing is
   not, and restraint governs how a line is written, never which
   facts may exist.
4. *The affliction cap eased* from two to three of the family, with
   coherent combos welcomed as one story (melancholy + sleepless +
   drunkard is a person, not a pile-up). The mad x troubled
   exclusion died with the collapse.
5. *Two free-color notes added:* any affliction may carry a dated
   origin ("since the fever", "since the queen died" — absorbing
   illness-associated personality change), and persecutory shades of
   delusion may roll beside suspicious.

**Recorded.** worldsim.md's fill sheets, merge ledger, cut list, cap,
and the new Range doctrine subsection; writing.md's Tone and comedy
section; develop.md's worldsim.md Files entry line.

## 2026-08-06 (session C) — The dataset lands: the Firascir baseline and the pool roll

**Where it started.** The parallel session delivered the numbers: 734
European rulers coded against the sheet, 443 carrying at least one
trait at the kept resolution (the traitless discarded as minor), max
14 traits per ruler, average 3, percentages rounded up. The designer
brought the data and a roll proposal — floor the zeroed traits at 1,
number the summed list, roll three dice over it for three traits, or
compress to a d100 to bias the rare tail — plus one suspicion
(populist looks bland: what would it do for the game?) and, on
review, two amendments: the roll must respect axis opposites, and the
good/dark exclusion is not actually wanted — contradictions can work.

**The calls.**

1. *The pool roll adopted*, superseding session A's per-axis
   Bernoulli + clamp + global-knob machinery wholesale: one weighted
   list (total 357, magic included), three draws per ruler, two per
   lesser authority. The identity that makes it faithful: the
   dataset's average count was 3, so three weighted draws reproduce
   the measured marginals almost exactly (~27% rolled ambitious vs
   32% measured). A fourth ruler draw is the one thinness knob.
2. *Axis opposites and never-withs handled by the SHRINKING POOL* —
   the designer's own d351-style instinct: a drawn trait, its axis
   opposite, and its never-with partners leave the pool and the die
   shrinks by their weights (ambitious drawn on the d357 → the next
   roll is a d324). Exactly equivalent to rerolling invalid draws;
   terminates by construction; keeps remaining weights proportional.
3. *The moral tags demoted from law to bookkeeping* (designer call):
   an honorable cruel king is a contradiction the fiction can play,
   and the range doctrine would rather have him than not. The tags
   now only derive `heart` (both sides present → mixed); jerkify's
   desert anchor survives unchanged.
4. *No d100 compression.* Re-rounding to 100 either deletes the rare
   tail or triples it, and code reads a 357-list as easily as a
   100-list. To fatten the tail later: raise the floor at full
   resolution.
5. *The floor applied to the vivid zeros only* — godless, eats
   nothing, sees visions at weight 1 — not to populist.
6. *Populist cut.* Zero hits in 443 rulers, and the blandness
   suspicion confirmed on inspection: everything it would do in play
   is reformer + charismatic wearing different clothes. Its one
   usable idea (a reformer's enemies are the entrenched elites)
   moved into custom's annotation.
7. *The magic cells hand-set* [PROPOSED]: spell-friendly 2,
   spell-fearing 3, gifted 1 — witch-fear slightly ahead of
   patronage in a plain human land; prime per-land modifier targets.
8. *Strangers and looks graduate from [PROPOSED]* — the designer
   collected data for both (welcoming 4 / race-proud-as-`exclusive`
   3; striking 3 / ill-favored 1).
9. *Data notes for later, not action now:* reformer 25 vs
   traditionalist 7 and brilliant 18 vs dull 1 carry chronicle bias
   (history records the remarkable); honorable/faithless at 2/2 is
   thin for the axis the PC's deals lean on — watch in play, adjust
   with the land mods if needed. About a quarter of rolled rulers
   land some affliction — vivid, and roughly what the data says.

**Recorded.** worldsim.md's sheets carry the weights (fl = floored
zero, hs = hand-set magic); the shape section describes the pool
roll, the floor, and the hand-set cells; the consistency section is
rewritten around the shrinking pool and the demoted tags; the cut
list gains populist; develop.md's Files line and plan.md's agenda
pointer updated.

## 2026-08-06 (session D) — The politics packets: the dump's power half

**Where it started.** The designer delivered politics dump part 2 —
the power half: a per-land brainstorm (Firascir's casus belli,
diplomacy instruments, and centralization note; manor, temple,
nobleman, and city event lists; Mortellaria's absolutist material;
Gibili's paralyzed buffer state with a faction-edge sketch; two
Ensimaa passes — the 21st-century satire and a regrounded
isolationist-theocracy pass; the Dvarvengrond ledger-state; the
Tergal set the designer judged strongest for its clear historical
analogues) plus a 120-entry three-era addendum (medieval / baroque /
industrial x four layers). Directives: aggressive editing and
selection over coverage; watch econ overlap; and the design intent
is COLOR BY RANDOM SELECTION — the fantasy stereotype stays the
constant and worldgen rolls which political elements a land wears,
so no land carries all its weirdness at once. Defaults for the
crowned lands: Firascir decentralized feudalism, Mortellaria
absolutism, Ensimaa constitutional monarchy, with Polish-style
aristocratic anarchy as the maximally decentralized option.

**The calls.**

1. *The selection intent formalized as three idea-level pieces,*
   all the design session's to adopt or overrule: the CONSTITUTION
   SLOT (exclusive, default-heavy die, per-land variants; cards
   never flip it), the TENSION ROLL (one standing tension per land;
   political cards admit on tensions the way econ cards admit on
   states, into the SAME crisis deck — no second pile), and FACTION
   EDGES (directed verb edges as the in-land `relation`; the
   designer's sketch kept as the worked model; the notables cast
   supplies faces).
2. *The dedupe doctrine:* econ owns flows, prices, livelihoods;
   politics owns right, office, allegiance. Dump entries that were
   econ cards in political clothes (banalities, the company town
   and scrip, pistolerismo, guild monopolies, the smuggling
   markets) stayed in econ and are referenced, not duplicated.
3. *The Ensimaa merge:* both passes kept, merged on the shared
   spine — a perfected society defending its stillness. The satire
   keeps the frame (it continues the econ axis and the
   constitutional-monarchy default); the theocracy pass supplies
   the mechanisms (purity writs, shunning as the capital
   punishment, the sealed-realm variant, the reincarnate search,
   fraternal polyandry, the floating quarter). Dropped to keep
   one-per-world: compulsory court attendance (Mortellaria's gilded
   cage owns it) and the dual throne (the puppet flag rolls it).
4. *Dvarvengrond's mining-only worry answered, not padded:* the
   property-registry state IS the distinct thing — the Grand
   Ledger, eternal claims, the dead founders' veto (literal in this
   world — one [PROPOSED] card), the marriage of veins, the Shorn,
   the surface envoys. No breadth borrowed from other civs.
5. *A war-layer feed extracted land-agnostic:* the casus belli
   pool, the diplomatic instruments (courtly hostage, tribute,
   marriage pact, personal union), and the succession-crisis
   cluster — wired to the ruler sheet's succession-state
   circumstance, which gains its consumer.
6. *Cross-layer wiring noted wherever the material lands on shipped
   machinery:* wergild as the karma layer's lawful price list;
   outlawry / the Shorn as protection-zero crime bands; sanctuary
   as a priced heat valve; counting coup on the mercy/ferocity
   layer; the black chamber on delivery quests; trial by combat on
   the duel machinery; the royal progress on the itinerant flag.
7. *The cut side:* roughly a quarter of the raw material cut
   outright (era-pure administrivia, entries with no PC-sized
   handle, redundant restatements), a quarter folded as clauses.
   Deliberate exclusions flagged for the designer: the slave-trade
   contract (the colony stays offstage per econ's design) and the
   eugenics entry (low game value for its weight). Strong cuts
   named as rescue candidates in the session report: heriot, the
   castellation license, tournament ransom, the Peace of God, the
   seance parlor (a religion-dump candidate — mediums in a world
   where necromancy works).

**Recorded.** worldsim.md gained THE LAND PACKETS — POLITICS (the
selection doctrine, the war feed, six packets); its intro and
layers-to-dump notes updated — politics is now dumped BOTH halves,
and religion's future dump shrinks by what politics ate.
develop.md's worldsim.md Files entry extended; plan.md's
identity-schema and event-vocabulary bullets point at the packets.

## 2026-08-06 (session E) — The religion packets: the worship dump

**Where it started.** The designer delivered the religion notes —
one register per race: shamanic orcs; pagan-Germanic,
stereotypical-fantasy dwarves; folksy, superstitious, cult-like
goblin business religions (showy, busy, loud; self-help and MLM
shapes); secular / philosophical / nondual elves whose religion
stays personal and fragmented even under a totalitarian state; and
a Christian-coded Sun religion of the One God for both human
lands, Mortellaria's version obsessed with death imagery and
Dionysian hedonism as two aspects of the one (carnival and
day-of-the-dead vibes), with debauchery and self-flagellation both
arguably supported by scripture. Method directive: the mapping
doctrine, confirmed fruitful — find the real-world version and
carry its realistic or quirky detail rather than producing generic
fantasy. Protocol: two rounds — an assistant outline, designer
feedback, then the writeup.

**The feedback round's calls** (all three are standing directives,
not one-off edits):

1. *The pact isolation directive.* The player's hell pact predates
   the detailed worldbuilding and is a gameplay-focused gimmick,
   not lore: NOBODY in the world knows of it or can sense it, and
   no world content reacts to it — dark play is an option offered,
   never a mark that makes the party conspicuous. Hell as a place,
   actor, or church is parked for its own later treatment (the
   Caelum/pirates pattern). The outline's pact-reception frame
   (per-land reactions to a pact-holder) was cut wholesale, along
   with every entry that touched it (the black shaman smelling the
   pact, the dwarven contract review, Gibili's pact upsell).
2. *Penance deemphasized.* The designer is unsure what penance/sin
   mechanics currently are or should be; the worldbuilding must
   not lean on them for now. The outline's per-land
   penance-interface table was cut; temples stay option-level
   service material (healing, burial, blessing) with the karma
   wiring an explicitly open question.
3. *The elven regrounding.* The outline's modern-wellness satire
   (the retreat industry, the shun-immune enlightened one) was
   rejected as too clever and too modern. Target: recognizable
   high fantasy elves — a culture of grace and refinement with a
   few subtle twists of weirdness, projecting gravity: superhuman
   beings with one big flaw that puts the other races militarily
   on equal footing, quantity against their quality. The religion
   packet was rewritten to that register (reverence without
   worship, the star-courts, the contemplative schools, memory as
   the afterlife, the funeral as the flaw worn liturgically) — and
   the directive stands as a flag over the REST of the elven
   material, which the designer wants made more coherent, more
   subtle, and a bit more normal in a later pass.

4. *Adopted from the outline unopposed:* the Sun communion as ONE
   church with two contesting rites (the Latin/Greek shape) and
   the schism-clock relation; the no-theology-ruling doctrine (no
   religion is ever confirmed true; contradictions are content);
   the real-world anchors throughout (Tengrist/Siberian practice,
   the Cornish knockers and the völva, furta sacra and the
   anchoress, Semana Santa / Día de los Muertos / the Misericordia
   confraternities, the Millerites and the burial societies —
   including session D's flagged séance-parlor rescue, landed in
   Gibili). One flag left open for the designer: whether
   Mortellaria's dead ever actually attend the Day of the Dead.

**Recorded.** worldsim.md gained THE LAND PACKETS — RELIGION (the
three directives, the Sun communion frame, six packets); its intro
and layers-to-dump notes updated — religion is dumped, monsters &
fauna is next, with three creatures pre-ordered (the draugr, the
knockers, Tergal's grave-made ghosts). develop.md's worldsim.md
Files entry extended; plan.md's event-vocabulary bullet counts the
religion packets. All of it is a first version, to be playtested
before it hardens.

## 2026-08-07 — The magic packets: the arcane dump

**Where it started.** The designer delivered the magic brainstorm,
asking for the same processing the economy and politics dumps got,
plus feedback. Its contents: the healing question (a world of
standard-service magical healing generates sickly and crippled
kings — why can't they buy a cure?) and the designer's chosen answer
(don't delete the traits; make sickness and disability THEMSELVES
possibly supernatural, immune to ordinary healing magic, with an
origin list: exposure, gifted blood's mutations, botched experiments,
magical poisoning, bargains paid in health, saints' and witches'
curses, divine punishment); five scarcity limits (M1 rare inborn
gift, M2 theory and long training, M3 reagents and bounded Power, M4
the madness/sickness danger of untrained or reckless work, M5 the
dark-sacrifice shortcut); the margin stance (magic small, known,
never a world-forming force; useful-and-dangerous balancing to wary
respect); an explicit no-persecution requirement (no
magic-is-from-the-devil doctrine, no inquisitors — a caster
playthrough must not be dominated by automatic hostility); the
organization sketches (Firascir tower hermits, Mortellaria's
academy-university with its class discrimination and necromantic
affinity, Gibili's unreliable masters-for-hire, dwarven
artificing/alchemy/healing pragmatism, elven integration priced in
fees plus standing, orcish shamanic/voodoo practice valued as weapon
and performed as art); the gifted-children recruitment hook and the
wild-talent fugitive; the maths/physics/programming analogy with
device/potion substrates and "a large portion of the functional
technology of the world is magical"; the PC-as-prodigy reading;
reagent examples; and two development demotions (conquest questlines
are not lore; the magic-user start is a dev matter).

**The calls.**

1. *Classified into the packet shape:* the five limits and six
   stance doctrines land-agnostic at the head, four land-agnostic
   entries (the recruiters, the wild talent, the reagent trade, the
   hunt), the guild frame, and six land entries in the standing
   order — deduped against religion (Tergal reference-only: religion
   owns the practice, magic adds weapon-value, performance, and the
   voodoo relation to Gibili; Gibili split on a
   salvation-vs-capability commerce line).
2. *The affliction doctrine wired to the ruler sheet,* with the
   residue rule [PROPOSED]: wealth cures the curable, so the
   afflictions that persist on the great are exactly the
   supernatural, the bargained, and the divine — the sheet's
   measured weights survive unchanged (what history counted is what
   magic could not cure), the origin stamp extends ("since the
   working"), and every afflicted ruler gains the standing rumor
   "why can the king not be healed?".
3. *A scale doctrine added [PROPOSED]:* persons, never populations —
   healing is retail, no working scales to a plague, famine, or
   season — protecting every epidemic/famine/drought card from the
   ruler sheet's question; and NOBODY COMES BACK (necromancy
   animates, never returns the person), keeping death's full weight
   under the succession cluster, the elven funeral, and murder's
   gravity.
4. *Conduct-not-creed formalized* as the doctrine answering the
   designer's inquisitor worry, with rereads (not rewrites) of the
   two inquisition-adjacent politics cards: the witch-finder is a
   fraud whose victims are almost never real casters, and the
   auto-da-fé prosecutes heresy with witchcraft as a charge of harm,
   the academy in the same capital proving magic itself is legal.
   The spell-fearing cell stays a personal stance, never a norm.
5. *The margin vs magical-technology tension resolved on the
   designer's own analogy:* the personal/embedded split — casting is
   rare, devices amortize rare work across decades, and the
   discipline's practitioners are well-paid professionals, not
   kings, exactly like the analogy's engineers.
6. *M5's hell mention kept rumor-level* — "hell usually involved"
   stands as practitioner belief; hell as place/actor/church stays
   parked (the pact-isolation directive holds untouched).
7. *THE FLAG (the session's one open collision):* the dump demotes
   the always-caster start to a dev matter and calls
   cannot-become-a-caster-later unintentional — but rules.md and
   plan.md record that start as a design principle ("the gift is the
   one thing a character can never acquire"), and worldsim leans on
   it twice (the sorcery axis, the witch-finder wiring). M1 pulls
   the recorded way. Proposed reconciliation: a latent gift that can
   AWAKEN mid-career as an event — inborn and rare, never bought as
   training. Designer's ruling needed before rules.md, plan.md, or
   the annotations move.

**Recorded.** worldsim.md gained THE LAND PACKETS — MAGIC (the two
demotions with the flag, the five limits, the stance doctrines, the
land-agnostic material with the cursed-work and ruler-cell wiring
notes, the guild frame, six packets); its intro and layers-to-dump
notes updated — magic is dumped out of the recommended order,
monsters & fauna stays next, science & technology is the layer's
remaining half and owes the magic packets the
magical-vs-mundane-technology boundary. develop.md's worldsim.md
Files entry extended; plan.md's event-vocabulary bullet counts the
magic packets. All of it idea-level, awaiting the designer's cut.

## 2026-08-07 (session B) — Three rulings on the magic packets

**Where it started.** The feedback round on the arcane dump came
back with three rulings, all now worked into the docs.

**The rulings.**

1. *Mid-game casterhood opens (the flag resolved).* Becoming a
   caster halfway into the game is not a big design challenge — it
   is simply to keep the game open and fun. Realism makes the world
   interesting but does not restrict the player to this extent:
   gameplay openness outranks M1 at the character sheet, and the
   2026-08-05 never-acquire asymmetry is downgraded from doctrine
   to a temporary fact of the build. Worked in: the worldsim
   demotion note carries the ruling (M1 stays a worldbuilding fact,
   not a player gate); rules.md's always-a-magic-user bullet gains
   the dated softening (the reroll and wizard gate stand until the
   opening ships); plan.md's magic-remnant list gains THE MID-GAME
   CASTER (mechanism the implementer's call — a latent-gift
   awakening event is the cheapest fiction); the sorcery-axis
   annotation drops its "always."
2. *The price rule (why magic fixes nothing at scale).* The
   designer's own answer replaces the assistant's [PROPOSED] scale
   doctrine as the general principle: magic CAN'T, or it would cost
   twice as much as any mundane solution — there is no spell to
   create lots of food for free, or to fix the harvest. Retail
   healing and the persons-not-populations corollary now hang off
   it; NOBODY COMES BACK stays a [PROPOSED] companion line.
3. *Doctrine over cards.* The no-inquisitor requirement takes
   priority over the two inquisition-adjacent politics cards, which
   are assistant-written and lower priority: where they conflict
   they bend or go at implementation. Both cards subordinated in
   place (the witch-finder loses the word "inquisitor" and gains
   the fraud reading in its own wiring; the auto-da-fé's wiring now
   reads heresy-first, casting legal, the academy the proof).

**Recorded.** worldsim.md (the demotion ruling, M1's clause, CAN'T
OR COSTS DOUBLE, doctrine-outranks-cards, both card wirings, the
sorcery axis), rules.md (the dated softening), plan.md (the
mid-game caster item; the cursed-ring pointer on the non-weapon
magic items note), develop.md (the Files entry tracks the rulings).

## 2026-08-07 (session C) — Implementation prep: the design session dissolved into the ladder

**Where it started.** The designer called the dumps sufficient for
now — technology and the remaining layers wait — and moved the
thread to implementation prep with three questions: is anything huge
still unsettled before building; can the build go in one session or
should several be planned; and make plan.md implementation-ready
with the session plan if needed.

**The reading of the material** (worldsim.md in full against
plan.md's agenda and the designlog trail):

1. *No single huge blocker stands.* The old design session (plan.md's
   item 2) had been mostly answered out from under itself by the
   2026-08-05..07 dumps: the identity schema's LAND level is drafted
   whole (packets, wealth roll, crisis deck), the ruler character
   carries measured weights and a settled draw, the politics frame
   (constitution slot, tension roll, faction edges) is drafted to
   adopt, and what-dict-NPCs-carry is answered. The one genuinely
   unauthored piece: the SETTLEMENT authority's kind/tension
   vocabulary — real authoring work, but a session's worth, not a
   gate in front of everything else.
2. *The curation debt is real but distributable.* Nothing in the
   ~2,100 idea-level lines has been designer-cut yet ([PROPOSED]
   entries, the flagged calls — orc horses, robot tone, sulfur to
   Hell, the Day of the Dead, the wealth die). A full-file pass
   would be a blocking session that buys nothing the per-slice picks
   don't: each build session implements a handful of records, so the
   designer's cut happens at that session's head, scoped to exactly
   what ships.
3. *One go is not viable.* By this project's own session sizing (the
   dark rework took three sessions, the attrition rework four
   slices), the frame alone — schemas, save layer, worldgen rolls,
   roll points, readouts, a new contract suite — is a full session
   before any real content lands. The material now spans five
   layers; the honest answer is a ladder.

**The calls.**

1. *The design session dissolved* — its remaining obligations split
   into (a) formalization assigned to the frame session, (b) named
   per-session head calls, (c) per-slice curation. Recorded in
   plan.md's rewritten remaining order so the dissolution stays a
   decision, not a drift.
2. *The ladder adopted, five sessions:* the settlement trim (spec
   already settled, no designer input left) → the world frame (the
   record schemas as data, per-land save state, the wealth roll,
   relations and derived states, the deck draw, the roll points at
   arrivals/nights/travel, the news + STATE DIFF surfaces, two-three
   seed cards per land) → weather (the named first-slice candidate:
   smallest curation bill, touches every outlet, cashes the parked
   DISEASE family, seeds DROUGHT) → the economy floor (the thread's
   two invariants; the asymmetry floor's ~20 cards; the five-outlet
   hookups; relations live; card chains) → authority & jerkify (the
   ruler roll, the settlement authority roll with its vocabulary
   authoring, the constitution/tension frame, jerkify's numbers, the
   bully if it fits). Each session leaves the game playable; each
   lands contracts in a suite no sim or bench imports.
3. *Weather ahead of the economy floor* — econ is the thread's
   heart, but weather is self-contained, land-agnostic, and proves
   the whole card machinery with almost no curation needed, while
   its drought state is input the econ relations want anyway.
4. *The constitution slot and tension roll deferred to session 5* —
   econ cards admit on states, never tensions, so sessions 2-4 need
   neither; keeping them out of the frame session keeps it lean.
5. *Deferred confirmed:* science & technology (the designer's
   directive), the monsters & fauna dump (slots in before whichever
   content pass names its creatures; the fog card can ride earlier
   because skeletons already exist in the catalog), temple services
   and penance wiring, hell's treatment, the per-land ruler modifier
   columns and tribal rewording, the PC-background question.

**Recorded.** plan.md — the thread intro, the remaining order
rewritten as the ladder, retro roadmap item 4 closed out, the parked
off-screen-simulation pointer retargeted; worldsim.md — every
design-session pointer retargeted at the ladder (intro, the wealth
die, the ruler and politics sections, the layers-to-dump tail);
develop.md — the plan.md and worldsim.md Files entries.

**Open.** The head calls at each ladder session (listed in plan.md
per session); everything on the parked list above.

## 2026-08-07 (session D) — The worldsim build: scope corrected, everything settled up front

**Where it started.** The designer reviewed session C's ladder and
corrected it on five points, plus one question. The corrections: the
build's scope is IMPLEMENTING WORLDSIM.MD, not the whole thread
agenda; the [PROPOSED] set should simply be implemented; everything
settleable should be settled NOW, not at per-session pick lists; the
settlement authority's kind/tension vocabulary IS JERKIFY in the
designer's framing — not actually designed, so no implementation;
and monsters & fauna is postponed, like science & technology. The
question: what is the temple/penance wiring?

**The question answered.** The game already ships sin and penance as
numbers — the karma layer (`sin` / `sin_total` / `penance_total`;
honest work burns sin 1:1). The religion outline (2026-08-06)
proposed a per-land PENANCE INTERFACE — temples where sin is worked
off: confession, priced absolution, penance quests, each land's rite
flavoring it — and the designer's own feedback cut it: worldbuilding
must not lean on undesigned mechanics. "The temple/penance wiring"
is the recorded name for that deferred question — whether and how
temples interact with the sin/penance economy. It stays parked;
temples remain plain priced services (healing, burial, blessing),
and the carnival amnesty's mechanical reading waits with it.

**The calls** (the corrections applied, the remaining flags settled
by delegated judgment):

1. *Scope: the worldsim build.* The ladder implements worldsim.md
   whole; what the file does not design does not get built.
   Postponed past the build, each behind its own design work or
   dump: jerkify (the settlement-authority identity roll plus the
   desert mechanics) with bullies riding it; monsters & fauna;
   science & technology; the temple/penance wiring; hell; the ruler
   modifier columns and tribal rewording; the landmark tie-in; the
   PC background question.
2. *The [PROPOSED] set adopted wholesale* — implemented like
   everything else; the marks stay as provenance only. The
   cut-on-sight framing is struck everywhere it appeared.
3. *Everything settled up front* — plan.md's rulings block replaces
   the per-session head calls. The delegated judgment calls: the
   wealth die is 2d6 as quoted; orc horses stay as written (re-judge
   at the table); the robot-servants card waits for science &
   technology (its tone question is that layer's boundary call);
   sulfur-to-Hell waits with hell's treatment; the Day of the Dead
   stays deliberately unruled (the ambiguity is content); THE FOG
   RAISES BONES ships on the existing skeletons while THE DRAUGR
   waits for its creature row; the carnival amnesty ships as color;
   numbers no ruling covers are the build's call, table-tuned.
4. *The ruler roll stays in the build* — it is worldsim material,
   fully designed: the land RULER notable rolls it at worldgen,
   lesser named authorities that cards create draw two, and
   trait-to-card admits are written per card at implementation. The
   land politics frame (constitution slot, tension roll, faction
   edges) likewise ships as drafted — land-level worldsim material
   the politics cards admit on; only the SETTLEMENT tier is
   jerkify's.
5. *The ladder reshaped to six sessions:* trim → world frame →
   weather → economy floor → politics & the ruler roll → religion &
   magic — together consuming worldsim.md whole, minus the waits.
   The elven coherence-and-subtlety flag rides the writing pass at
   implementation of the Ensimaa cards (player-facing strings are
   written there anyway).

**Recorded.** plan.md — the remaining order rewritten as THE
WORLDSIM BUILD (the rulings block, the six-session ladder, the
postponed list carrying jerkify's and bullies' full descriptions);
worldsim.md — the [PROPOSED] adoption in the intro and the three
section notes, the settled flags in place (wealth die, orc horses,
robots, sulfur, Day of the Dead, the draugr), the ruler and politics
pointers retargeted, monsters & fauna marked postponed; develop.md —
the plan.md and worldsim.md Files entries.

**Open.** Nothing blocks the build. The postponed list above is the
thread's future work.

## 2026-08-07 (session E) — The roadmap holds only what is ahead

**The designer's instruction.** plan.md had become half archive: whole
sections marked SHIPPED or COMPLETE, built specs kept as trophies, and
shipped detail interleaved with the work still to do, so a reader had to
sort the roadmap from the museum. The rule, stated and now standing:
**plan.md is planned features and parked ideas only** — when an item is
processed and implemented, it comes OUT of plan.md and is written up in
the designlog instead. And the rule itself gets written down where dev
sessions actually read it, rather than being re-derived each cleanup.

**The doctrine, recorded** (develop.md's "Where a finished feature is
written up", one clause each in AGENTS.md's document list, and plan.md's
own header):

- `designlog.md` — the dated session write-up: what was discussed, the
  road it took, what was decided, what shipped, and the calls the spec
  left open that the build had to settle. This is the archive.
- `rules.md` — the played rules and the design spine.
- `develop.md` — the code index (Files), the dev map, the tuning levers.
- `benchlog.md` — measured numbers.
- Spec companions (`worldsim.md`, `placegen.md`) — their shipped
  sections get cut as their sessions land, same as plan.md's.
- `plan.md` — loses the entry entirely. Not struck through, not marked
  SHIPPED, not kept "as the built spec": deleted, leaving at most a
  one-line pointer where a planned or parked item still leans on
  something built.

**What came out** (each already recorded where it belongs): THE DARK
REWORK's three-session spec (2026-08-04, the three entries above); the
retro pivot's shipped combat-log half (2026-07-21, plus rules.md
"Reading the combat log" and the `ui/fight-short.txt` /
`ui/fight-detailed.txt` pages in dm.md and develop.md); the worldsim
thread's two short specs (2026-08-05 build session); the attrition
rework's why-and-spine and its settled decisions (2026-07-26, plus
rules.md's Wounds & Recovery and Conditions add-ons); conquest ticking
(2026-07-27); named and masterwork weapons (2026-07-28); the levelling
framework's completion header (its record is rules.md and develop.md —
it predates this log); the 2026-07-19 villain pivot's vision and settled
decisions (2026-07-19). The rework's parked lists, its open questions,
and every unscheduled idea stayed in plan.md, which is what that file is
for. The 2026-07-26 travel-encounter measurement table — the one piece
of shipped record with no other home — moved to benchlog, where measured
numbers live.

**Build detail preserved here.** THE DARK REWORK's plan.md section
carried three things no other doc held: the template sort, the calls
each build session had to settle beyond its spec, and the death list.
They are recorded now so the 2026-08-04 entries above are complete on
their own. (Pointers in those entries to "plan.md's THE DARK REWORK
section" resolve here.)

*The template sort.* **Occult ten** (kept as assignments, and all
`roll_dark_quest` draws from): Blood on the Altar, Sacrifice the Puppy,
Steal the Temple Relic, Kill the Priest, Corrupt the Holy Sword, Find
the Evil Sword, Guard the Cultists, Open the Hellgate, Capture the
Beast (hell is the customer — occult by giver), plus the newly authored
**Desecrate the Shrine**, which filled the desecration slot the list
lacked. **Crime fifteen** (retired from the quest system, their skins,
rosters, situations and epilogues kept in `karma.CRIME_FODDER` as scene
fodder — session B dresses each crime category's protection in one of
them): Kick the Puppy, Collect Protection Money, Burn the Granary,
Steal the Jewel, Collect the Debt, Rob the Tomb, Take Over the Road,
Dine and Dash, Loot the Village, Rob the Vault, Poison the Feast, Take
the Mansion, Betray an Old Friend, Sell the Powder, Take the Neighbor's
Land. Crime's own copy draws from neither list.

*Session A (the assignment ladder) settled two calls the spec left
open.* `deal_card` falls back to the NEAREST-band card when no card in
the deck admits the pin level — the high pins, where only the widest
bands reach — and the assignment levels into that band. And the
account's closure is SHARED by the write-off and hell's mercy
(`withdraw_assignment`), so a LOST visit also releases the job's sites
back to the land; the old mercy deleted the quest without releasing
them.

*Session B (crime as free actions) settled six.* (1) **Gold carries the
category multiplier too** — the spec quoted the coin formula without it,
which made a level-1 petty pickpocket pay the same 20g as a mugging;
petty stays FLAT on its own `PETTY_GOLD` range and everything else
carries the same multiplier as the lump, while gold never carries
monotony or the first-time bonus. (2) **The wilds are a crime market** —
gating availability by settlement kind alone would have put highway
robbery and the tax cart inside the walls, so mark bands declare which
place kinds hold them (the travelling bands reach the road; nobles and
magnates do not) and each CATEGORY declares where it happens, road work
being wilds-only against a settlements default. (3) **A botched deed
still pays if the fight is won** — the crime happened, the hard way; a
LOST fight and a retreat both pay nothing. (4) **Casing stores nothing**
— the mark is seeded off (world seed, place, day, category), so `crime`
re-rolls exactly what `case` showed and sleeping on it rolls a new mark
by construction. (5) **The commission is stamped when the crime is
COMMITTED**, not when it pays: a force job the party is driven off, or a
botched deed whose fight is lost, still ticks its category's monotony
window — hell was watching the attempt — which costs little (the second
stamp in a window is still x1.0) and keeps the ledger an honest record
of what the party has done. (6) **The ledger separates GRANTS from
by-deed unlocks** (`{"ledger": {...}, "grants": N}`), so committing a
locked category — which unlocks it by deed — never eats a suggestion the
ladder still owes.

*Session C (the surface) settled five*, three of them already in its
entry above (the tally's own `last` field, maimings scanned rather than
hooked, named kills detected by shape). The other two: **`history`
records carry a KIND** — the spec said "day-stamped lines", but the page
has two narrative sections, so each record is `{day, kind, line}` plus
an optional `note` for the epilogue, and the cap of 60 is applied PER
KIND, so a career of jobs can never push the write-offs and maimings off
the page. And **a hand-entered sin lands in the record only when it is
NAMED**: `sin dark 40 burned the tax rolls` writes a line, a bare `sin
dark 40` is bookkeeping, not history. Folded in during the same build:
the `crimes` sheet reads the BAND rather than a rolled mark (`case`
stays the exact read) and quotes each category's authored
what-stands-in-the-way line instead of dumping its guard pool;
`suggestions` takes an optional rng so the feed can be shuffled
(catalogue order would advertise the same two petty crimes forever); and
`main` was split into `build_parser` + `main` so the command surface is
testable.

*What died with the rework.* Session A: `TASK_INTERVAL_DAYS`,
`FIRST_TASK_LEVEL`, `last_task_day`, `DARK_JOBS_PER_DAY`,
`roll_dark_board` with the `dark_board` save key and `board --dark`, the
fifteen crime templates as QUESTS, and the collections ladder
(`beatings`, `ENFORCE_CAP_OVER`, the +1-per-visit escalation and its
relentless top rung — replaced by the one-visit write-off with
`ENFORCE_SPREAD`). Session C: the `karma` command name, the karma save
keys `bad` / `bad_total` / `good_total`, and — the
no-backwards-compatibility rule applied to a file the rename touched —
`session.ensure_weapon_layer`, the last named lazy-upgrade branch.

**Recorded.** plan.md rewritten to planned work, parked ideas and open
questions only (about a third of its former length), with the doctrine
at its head; develop.md's new doc-lifecycle section and its plan.md /
designlog.md Files entries; AGENTS.md's document list; benchlog's
re-homed travel-encounter table.

**Open.** Nothing. The next dev session's first duty under the new rule:
when the worldsim ladder's settlement trim lands, delete its rung from
plan.md rather than marking it shipped.

## 2026-08-07 (session F) — The settlement trim: the catalog becomes a reserve

**The task.** plan.md's worldsim ladder, rung 1 — the settlement trim,
whose spec had been settled since 2026-08-05 with no designer input
left. A land BEGINS with three settlements (one capital, one town, one
village); further settlements materialize only when something needs
them to exist; the authored catalog stops being the world's initial
census and becomes the RESERVE POOL those materializations draw names
and skeletons from. This is places.py's own lazy Site/house
materialization lifted one tier.

**Where it started.** `create_geography` built the whole catalog at
worldgen: 39 settlements across six lands (Firascir alone opened eight),
each with its authored Site/Room skeleton, its guaranteed services and,
in `quests.generate_world`, a face behind every service and one job on
every board. Nothing anywhere could ADD a settlement — the world's
census was a table, decided before the first scene.

**What shipped.**

- **The opening draw** (`places.create_geography`). Naturals first, as
  before; then the authored capital, then a town and a village drawn off
  the land's reserve. `SETTLEMENTS_AT_WORLDGEN` = 3 and `OPENING_TIERS` =
  (town, village) are the two constants; the world opens at 28 natural
  Areas + 18 settlements (was 67 Areas).
- **The reserve** (`_land_reserve`, stored per land in the save as
  `reserve`). The catalog's remaining towns, shuffled on the world seed;
  then its authored villages, likewise; then the generated-village
  pairing — the land's whole village-name pool, shuffled, paired with its
  village roles in rotation. Entries are plain JSON (`name`, `tier`,
  `role`, `tags`, `source`), so the reserve rides the save without a
  serializer.
- **The need-to-exist draw** (`places.materialize_settlement`), with a
  MANDATORY `need` string and optional `tier` / `tags` / `day`. It pops
  the first fitting entry — a tag intersection wins over reserve order,
  so "a counterparty port" gets the harbor town rather than the next
  hill town — builds the Area, its required Sites and Rooms and its
  services exactly as worldgen does, stamps `founded_day` /
  `founded_for` on the record and emits a `materialize` event.
  `reserve_settlements(world, land, tier=None)` is the read-before-you-
  commit companion.
- **The whole-stack entry point** (`quests.found_settlement`), because
  places.py cannot import quests: the draw plus the service faces.
  `_cast_service_providers`, a worldgen-wide loop, became
  `cast_service_providers(world, settlement, rng)` per settlement, and
  worldgen now calls it in a loop of its own.
- **`test_worldsim.py`** — the build's own contract suite (21 tests, no
  sim or bench imports it, per the karma doctrine). Session 1 pins the
  opening census and its tiers, the capital staying its land's FIRST
  settlement (story.py raises waves off `settlements_by_land[land][0]`),
  the reserve's completeness (nothing authored lost, nothing built
  twice, the save round-trip), the draw (a whole usable place — Sites,
  services, faces, a board that fills, a garrison in band), tier and tag
  steering, a dry land saying no, and the seeded stability of all of it.

**The calls the spec left open, and how the build settled them.**

1. *Dvarvengrond authors no village at all.* "One capital, one town, one
   village" is unbuildable there. The build made the COUNT the invariant
   and the tiers the ideal: a land takes one of each tier it has, then
   tops up to three from the head of what is left. The dwarves therefore
   keep all three of their authored settlements (capital + two towns) and
   hold NOTHING in reserve — which is also the honest reading of their
   catalog, and it forces every consumer to handle a land that cannot
   grow.
2. *What "generic, with few unique features" means.* The same spec
   sentence says materializations draw "names and skeletons" from the
   catalog, so a drawn settlement gets its authored skeleton — the
   genericness is that nothing bespoke is AUTHORED for it (no identity
   roll, no unique features; that is jerkify's business, postponed), not
   that its content is degraded. A drawn settlement is an ordinary
   settlement: the party cannot tell from the inside which three a land
   opened with.
3. *A dry reserve returns None* rather than inventing a name and a
   skeleton. placegen's rule stands ("finite Land slots with stable
   seeds, not unlimited `explore` results"), and it gives the card layer
   the discipline it already uses for exclusive slots: a card whose
   counterparty cannot be built simply does not fire. `reserve_settle-
   ments` exists so a card can check before it commits.
4. *Which town and village a land opens with is a seeded roll*, not the
   catalog's first row. The opening draw became a source of playthrough
   variety — a new Firascir game opens on a different town — which is
   what the trim buys back for the choice the smaller board costs.
5. *The generated-village pairing changed shape.* It was three roles ->
   three names, one village each. It is now the whole name pool paired
   with the roles in rotation, which makes the village reserve fifteen
   deep in the four lands that have one and lets a land grow villages
   with role variety instead of running out after three.
6. *Nothing is posted on a drawn settlement's board at founding.* An
   unread board fills to its band the first time the party looks at it
   (`refresh_settlement_board`), which is exactly when a new town's work
   should appear — so the draw stays cheap and the refill stays the one
   place postings are made.
7. *No live consumer yet.* Sessions 2 and 4 (the relations table and the
   econ cards) are the first callers by design; until then the contract
   lives in `test_worldsim.py`. The API was written for those two
   callers: `need` is required so a place always records WHY it exists,
   and `tags` exists because "a counterparty port" is the spec's own
   worked example.

**What it costs, measured** (full numbers in benchlog.md). The world
halves: 39 settlements -> 18, board slots 132 -> 68, the seeded opening
board 41 postings / ~19k XP -> 20 / ~8.7k. Per LAND — which is what the
player actually sees, since word travels within a land — open slots go
22 -> 11.3 and jobs within +/-1 of the party's level go ~4.6 -> ~2.1,
with the "nothing at your level in this land today" rate rising from
1-4% to 7-18% (at +/-2 it is 0-7%, and the world still holds 9-13 in-band
jobs). The career sim is unmoved on reach and death level; its turn-in
bands shift consistently (quick 41% -> ~32%, late 8% -> 13%), i.e. the
clock bites a little harder on a thinner board. **No dial was pulled** —
the trim's ruling says the posting bands do not move, and the parked
posting-band trim stays a separate item. If it bites at the table, the
dials in order are `QUEST_REFILL_PER_DAY`, the posting bands, and only
then the census.

**What it buys at the table.** The `map` page is now six lands of three
places instead of a 39-row directory: a world a player can hold in his
head, where each settlement is worth remembering. And the world can
GROW, which is the thing the ladder actually needed — the next four
sessions can name a place that does not exist yet and have it exist.

**Recorded.** rules.md's *The map* (the census and the reserve rule);
worldsim.md's need-to-exist paragraph CUT to a shipped-pointer;
placegen.md's counts table, MVP boundary, settlement model, per-land
village-pool lines and verification list re-captioned as the reserve
they now are; develop.md's Files (places.py, place_catalog.json,
test_worldsim.py), dev map and Running block; plan.md's ladder down to
five sessions with its rung deleted; benchlog's measurement entry.

**Open.** Whether three settlements a land is enough at the table is a
PLAY question, and the played band (levels 1-4) is where it will show
first: the low band's ±1 board is the thinnest of all (mean 1.5 jobs a
land at L1, nothing at all 18% of days). Worth watching in the next
playthrough before session 2 adds anything to the boards.

## 2026-08-07 (session G) — The world frame: the record kinds become code

**The task.** plan.md's worldsim ladder, the frame rung — the session
whose product is the frame itself. worldsim.md's five record kinds
(fact / option / state / card / relation) become data; the save grows a
world layer under every land; the wealth roll, the crisis deck, the
relations table and the roll points all land; and the seed content is
two or three economy cards a land, enough to prove the loop end to end.
Everything settleable had been settled in plan.md's rulings block, so
there was no designer input outstanding.

**Where it started.** Nothing in the codebase knew a land was anything
but a name, a race, a climate string and a list of areas. `places.py`
had a state API (`add_state` / `replace_state` / `clear_state` with an
event log) that only quest place-mutation ever used, and the land
records carried an empty `states` list nobody wrote to. The world could
not be in a mood, and nothing could happen in it that the party had not
gone and done.

**What shipped.**

- **`worldsim.py`** — the layer. `card(...)` and `relation(...)` are the
  two record constructors, validated at import (`validate_content`
  raises on an unknown outlet, an unknown state, a slot member set as a
  free state, a card with no effect, an edge between lands that do not
  exist). `STATE_WORDS` is the state vocabulary with its readout
  phrases; `STATE_SLOTS` the exclusive ones.
- **The wealth roll** — 2d6 per land at worldgen (the settled die),
  `open_world` writing the per-land layer: `wealth`, `wealth_day`,
  `deck` (the land's cards, shuffled on a stable seed), `drawn` (the
  record of everything it has fired), `live` (the card standing now),
  `news`, `told_day`, `rolled_day`. A land in CRISIS draws its first
  card at worldgen, dated day 1.
- **The states** ride places.py's own machinery, which gained a `since`
  day stamp and an optional `slot` tag on the state record — so a land's
  world states and a place's quest states are one shape, one event log
  and one readout. `worldsim.set_state` owns the slot discipline.
- **The deck draw on need** — the pact deck's pattern: the first card the
  land admits, skipped cards left for a later day, an exhausted deck
  reshuffling. A card whose only effect is a slot value the land already
  holds does not fire (the exclusive-slot rule from the other side).
- **The pulse** — `_fire` applies the two outlets the frame ships (news
  line, state flip) and stamps the clock; `_end` takes back what the
  card set WHILE it stood and leaves what it SET. The quest, menu and
  encounter payloads are authored on the seed cards, carried and
  validated, and left for the economy floor session.
- **The relations table** — nine authored directed edges (the grain out
  of Firascir and Mortellaria, timber down the tolled road, the elves'
  rented ground, Gibili's guns, Tergal's raiding when the herds die).
  Derived states are computed at read time and never stored, and cards
  admit on them like any other state.
- **The roll points** — `roll_world` inside `board_clock`, which is
  already the day-advance spine (travel, explore, camp, tavern,
  downtime, board). Every land is brought up to today together, so no
  relation reads a land behind the calendar. `world_news` prints beside
  `conquest_news` at the four points news lands.
- **The surfaces** — `WORD FROM <LAND>`, day-stamped and told once; the
  band-and-states line under each visited land on `map` / `ui/map.txt`
  (the STATE DIFF); and `world`, the DM inventory.
- **`test_worldsim.py`** grew the frame's contracts (73 tests total).

**The calls the spec left open, and how the build settled them.**

1. *The module's name.* `worldsim.py`, not `world.py` — `world` is the
   name of the world DICT in nearly every function of `session.py` and
   `quests.py`, and a module by that name would shadow it at every
   import site. It also matches `worldsim.md`, which is the file it
   implements.
2. *Where a land's states live.* In places.py's existing `states` list
   on the land record, not a new store — extended with a `since` day
   stamp and a `slot` tag. One vocabulary, one event log, one
   `active_known_facts`; the alternative was two state systems that
   would have had to be reconciled the first time a card wanted to
   flip a state on an AREA.
3. *How determinism survives laziness.* Each land-day rolls off
   `stable_seed(world, land, "worldsim-day", day)`, so day 40's roll is
   the same whether it is computed on day 40 or caught up on day 300.
   `roll_land` walks the days one at a time. This is pinned as a
   contract (`test_catching_up_is_the_same_as_living_through_it`) —
   without it, "the world moved while you were away" would depend on
   when you looked.
4. *One card at a time per land.* The spec does not say how many pulses
   a land may carry. One, with a clock: the news stays legible, the
   states stay coherent, and a card is a thing the land is LIVING
   THROUGH rather than an entry in a queue. A clockless card is a
   different animal — it leaves its mark and stands over nothing (the
   vein has run out; the land goes on having days).
5. *What a clock takes back.* Two flavors, all the way through:
   `set` outlives the card, `while` comes off with it — and the same
   split for the wealth band (`wealth` / `wealth_while`), which is what
   makes a failed harvest a season of crisis and a dead vein a
   permanent demotion.
6. *The band needed a way in and out.* The spec says wealth is a state
   that cards can move but seeds no card that moves it. A frame where
   the opening roll is destiny is not a simulation, so three seed cards
   move the band: the failed harvest pushes Firascir into crisis for a
   season and lets it back out; the vein running out demotes
   Dvarvengrond for good; and a fourth Dvarvengrond card — the dwarf who
   can work a written-off seam, straight out of the packet — is the way
   back up, and doubles as the frame's proof that a card can admit on a
   state another card set.
7. *Who hears what.* Only the land the party stands in tells its news
   (the board's own word-travels-within-a-land rule). Another land's
   trouble reaches the party either by going there or as a derived state
   naming its cause. A long absence is summarized at `NEWS_TOLD` 6
   lines, not scrolled.
8. *Which lands show on the map.* Only lands the party has visited (plus
   the one it stands in). Showing all six would have made the map a
   world dashboard and quietly repealed the knowledge model.
9. *The layer must not move a bench.* `open_world` is called last in
   `generate_world` and takes no rng from it (the armory's rule). The
   contract test regenerates a world with the layer stubbed out and
   asserts the whole thing is identical.
10. *The three unwired outlets.* Carried, validated, and NOT applied —
    posting a card's quest, repricing the menu and adding an encounter
    row are the economy floor session's, and faking them here would have
    produced content the next session had to unpick. The seed cards
    author the payloads so the shapes are exercised.
11. *Sessions are named, not numbered.* The ladder renumbers itself
    every time a rung ships, and this session started with the
    settlement trim calling itself "session 1" in one file and "the
    first rung" in another while plan.md's list had renumbered under
    both. `test_worldsim.py`, develop.md and plan.md now name sessions;
    only the date is a stable key.

**What it costs, measured** (full numbers in benchlog.md). Nothing in
the career moved — the layer is bench-invisible by construction and a
120-career run reads the post-trim baseline within noise. The layer's own
pacing at the shipped knobs: a crisis land fires 1.88 cards in sixty days
and is living through one on 67% of them; a normal land 0.88 and 24%; a
prosperous one 0.66 and 13%. 63% of worlds open with a land in crisis,
22% of lands carry a derived state at day 60, and the whole layer costs
about 2 KB of save.

**What it buys at the table.** A land is now a thing with a mood and a
memory: the party comes back from a week in the hills and Firascir's
harvest has failed, bread is short, and the dwarves it feeds are already
saying grain is scarce — none of which anybody went and did. That is the
thread's second invariant, at the frame's scale.

**Recorded.** rules.md's new *The World Layer* add-on; dm.md's "The land
itself" (play protocol) and its quick-reference numbers; develop.md's
Files (`worldsim.py`, the rewritten `test_worldsim.py` entry, places.py's
state-record note), dev map, Running block and Balance section;
worldsim.md's record-kind sections CUT and replaced with a shipped-frame
summary plus the two constructor signatures the remaining packets are
written against; plan.md's ladder down to four sessions with its rung
deleted, the shipped wealth-die ruling removed, and the economy floor's
entry re-scoped to what the frame did not do; benchlog's measurement.

**Open.** The layer's first impression is thin: a starting land is normal
or prosperous five times in six, and a normal land is living through
something only a quarter of the time, so an early playthrough may see
`[NORMAL]` and nothing else for a week. `CARD_CHANCE['normal']` is the
dial (0.02 -> 0.04 roughly doubles a quiet land's activity), but it is a
PLAY question and the die is the designer's own ruling — watch it before
turning it. The played band (levels 1-4) is where it will show first.

## 2026-08-08 — The weather: the world layer gets a sky

**The task.** plan.md's worldsim ladder, the weather rung — the first
CONTENT session on top of the frame, and the one worldsim.md named as
the strongest first slice: land-agnostic, self-contained, touching every
outlet, and the smallest curation bill on the board. Everything
settleable was settled in plan.md's rulings block (the [PROPOSED] trio
adopted wholesale among them), so there was no designer input
outstanding.

**Where it started.** `places.ENVIRONMENT_PROFILES` had carried a
`climate` SENTENCE for every environment since the place-generation MVP
— "Mild country with rain, cloud, wind, fog, and winter frost" — and
nothing had ever read it. The frame had left a `weather` axis on
`card()` admitting conditions with a comment saying the weather session
owned the day roll, and no day roll existed. The conditions framework
had had a third family parked since the attrition rework with a note
that the weather would cash it.

**What shipped.**

- **The day roll.** Nine weather words shared by every land; the WEIGHTS
  are per-environment and live in `ENVIRONMENT_PROFILES` — the climate
  sentence finally said in numbers. Two spell counters run behind it,
  and they measure two different things on purpose: DRY is days since
  the last rain (an overcast day extends it — a grey sky is not a
  drought ending), WET is a run of wet days that a dry day breaks and an
  overcast one does not (three days of rain with a grey one in the
  middle still puts the fords out). A held drought bends the roll that
  made it.
- **Three tracks.** The frame's one-card-at-a-time rule could not hold
  across the weather's timescales, so a land now carries three decks and
  three live slots — crisis (the wealth band's), weather (the day's
  sky's), season (a long spell's). `DECK_KEY` / `LIVE_KEY` keep the
  frame's existing save keys intact.
- **Eight cards.** THE STORM SETS IN (any land, holds its own sky 1-3
  days), THE FORD IS OUT (the human lands, after three wet days — the
  road costs a day), THE FOG RAISES BONES (rare, and it NAMES a
  necromancer), THE FOREST BURNS + THE BURN GOES GREEN (Ensimaa, under
  drought, the scar outliving the fire), THE DUST STORM (Tergal, under
  drought), THE SMOG SETTLES (Gibili), and the season card THE RAINS DO
  NOT COME.
- **The DISEASE family** in `rpg.py`: cold and pneumonia as
  `CONDITION_KINDS`, `catch_chill` (bounded deepening),
  `shake_disease` (the night's roll, easing one rung), `treat_disease`
  (the healer's tier gate), `exposure_check` (2d6 + STR vs the sky),
  `Entity.disease_load` docking `hp_ceiling`, and `long_rest` growing
  `sky=` / `sheltered=`.
- **The storm in a fight**: `group_combat(weather=)` puts
  `STORM_SHOT_PENALTY` on both sides' shots and a `STORM_SLIP_DC` save
  on every step of the movement phase; it rides `pending` to the resume.
- **The cabin table**, five rows and ten hosts, printed as a sight plus
  a `(DM eyes only:)` line.
- **The play wiring** in `session.py`: `sky_here` / `exposure_sky` /
  `fight_sky` / `weather_note` / `shelter_here`, the sky threaded into
  every night path, `travel_delay` in `cmd_travel`, `heal_the_sick` in
  `cmd_healer`.
- **`test_worldsim.py`** grew the rung's contracts (118 tests total).

**The calls the spec left open, and how the build settled them.**

1. *Weather needed its own track, and then a third one.* The spec says
   "one card stands over a land at a time" and also asks for a
   season-scale DROUGHT and a day-scale BIG RAIN. Those cannot share a
   slot: a 45-80 day drought would have blocked every storm under it,
   and it would have blocked the WILDFIRE that admits ON it. Three
   tracks, three decks, three live slots, three draw rules — and the
   crisis track is untouched, so the frame's contracts all still hold.
2. *The climate distribution belongs to the PROFILE, not the layer.*
   plan.md said placegen's environment profiles author it, and that is
   where it went. `worldsim.py` owns the roll; `places.py` owns what
   this ground's sky does. The alternative — a weather table inside
   worldsim keyed by environment — would have put half of a place's
   description in the world layer.
3. *A weather card can BE the weather.* A storm declared to stand 1-3
   days was, on the second day, a state saying "the storm has the roads"
   under clear skies — visible immediately in `world` and on `map`. So a
   weather card may declare a `sky`, and while it stands the day roll is
   skipped. Only cards that ARE weather carry it: the ford stays out
   after the rain stops, which is the whole point of the ford.
4. *A drought is RELATIVE, so its trigger is per-ground.* At a single
   fixed dry-spell length the card was dead in the wet lands and
   permanent in the dry ones, and it took WILDFIRE and its regrowth card
   down with it — an authored card that can never fire is worse than no
   card. `drought_days` per environment (12-25), each set so a drought
   is about a one-in-a-hundred day on that ground. This is the one
   number in the rung that is doing real work rather than flavor.
5. *An illness is not a poison, so its CLOCK is the night.* The obvious
   implementation — a `cold` condition with a power that ticks — makes a
   cold worth 6 HP in a six-round fight, which is a venom, not a cold.
   The disease family is therefore power 0 and skipped by
   `_tick_conditions` entirely; what it costs is the HP CEILING, like a
   wound. "Small, slow, treatable: an illness-shaped wound" is
   worldsim.md's own phrase, and the ceiling is what makes it literal.
6. *The shake rolls STR, not STA.* STA reads as the constitution stat
   and was the first choice. It is a POOL: 6.8 at level 1, 15.9 at level
   20. An illness that got easier to shake as you levelled would inflate
   exactly the way this game's costs never do (the wound rework's whole
   argument). STR is 3-6 and flat across all twenty levels. Both the
   catching and the shaking read it.
7. *CAUGHT COLD is not a card.* worldsim.md lists it as one, but it is a
   per-hero effect of a night, not a pulse over a land: it has no state,
   no news line, no clock, and it happens to some heroes and not others.
   It ships as the exposure check inside `long_rest`. The rest of what
   the spec calls "card BIG RAIN" — the satisfaction dip, the shelter
   roll, the cabin table — hangs off the storm card's sky the same way.
8. *The three unwired outlets stayed unwired.* The ladder gives quest,
   priced menu and encounter-table wiring to the economy floor, and this
   session did not take them: the fog's skeletons, the wildfire's
   evacuation posting and the ferrymen's rates are authored on the cards
   and carried. What DID ship is weather's own mechanics, which are not
   those outlets — the travel day, the exposure check, the field
   penalties, the shelter scene.
9. *The DM-eyes half of the cabin.* The sinister row is no scene at all
   if the display announces it, and there is no `--dm` command a camp
   could hang one on. It follows the quest twist's existing idiom: a
   `(DM eyes only: ...)` line in the same display, and a dm.md rule that
   it is never read aloud.
10. *The necromancer is a name and a level.* plan.md's ruling said keep
    the rumor address cheap. He goes on the land's world layer, the news
    line says his name, `world` shows him, and the next fog raises the
    SAME man's dead — which is the recurrence property the six outlets
    say is what makes an NPC exist. No landmark record, no site, no
    questline. His level is rolled 3-14 and is not scaled to the party.

**What it costs, measured** (full numbers in benchlog.md). Nothing in
the career moved, and this time the proof is byte-level: a fixed-seed
120-trial fight-and-rest harness hashes identically on the working tree
and the stashed pre-change tree. The layer's own pacing over 120 days: a
land sees about one storm a fortnight, Firascir's fords go out 1.2 times
a campaign, Gibili sits under smog 1.1 times, the fog raises bones
somewhere in most worlds, and a drought is a once-in-a-few-campaigns
event per land. A cold is ~3 nights in the wilds and ~1.6 in a bed;
pneumonia is a fortnight out there and under a week in a town.

**What it buys at the table.** The first thing every scene now has is
weather, and it is not decoration: the party sets out in the rain, the
ford is out and the road costs a day, the night in the open puts a cough
on the wizard that no camp will shift, and the fight at the end of it is
fought with the wind in everyone's shots. It is also the first world
content that reaches a QUIET land — no weather card carries a wealth
condition, so a prosperous, cardless, uninteresting land still has a sky
and still has a storm that drives the party to a stranger's door.

**Recorded.** rules.md's new *Weather* add-on; dm.md's "The sky" play
protocol under "The land itself" and its quick-reference numbers;
develop.md's Files (`worldsim.py`, `places.py`, `test_worldsim.py`), dev
map and Balance section; worldsim.md's WEATHER section CUT and its
shipped-frame header rewritten to cover the weather API; plan.md's
weather rung DELETED, the ladder renumbered to three, and the parked
DISEASE item replaced by the now-unblocked infection one; benchlog's
2026-08-08 entry.

---

## 2026-08-09 — The economy floor: the world layer starts costing money

**The rung.** plan.md's worldsim ladder, second content session. The
frame (2026-08-07) built the card and the relation and applied two of
the five outlets — the news line and the state flip. The weather
(2026-08-08) put a sky over every land on a second and third track.
This session wired **the three outlets the frame carried but did not
apply** — the quest board, the priced menu, the local encounter table —
and took the per-land card bill up to the asymmetry doctrine's floor
with chains running through it.

The thread's two invariants (2026-08-05 framing) land here, and they
were the whole brief: **the BOARD must react to world state**, and
**something must move WITHOUT the player taking a job, and be visible on
return.**

### What was built

**The board — three verbs.** A card's `quest` payload now carries
`post` (an authored quest template, via the new `worldsim.job()`), a
`slots` integer (negative is the CANCEL verb: a town whose mills are
cold stops hiring) and a `reprice` multiplier. Under all three sits the
WEALTH BAND, which is the baseline: prosperous posts one more job a
settlement and pays 1.15, crisis posts one fewer and pays 0.85, with a
floor of one posting so a settlement is never a place with no work in
it. A crisis board is short of *ordinary* work, not of work — its cards
post their own back on top.

**The priced menu — six terms.** `goods`, `steel`, `lodging`, `healer`,
`toll`, `ferry`, each a multiplier on a price the game already charges,
so the world layer never owns a price, only moves one. Three sources
multiply: the band, the STATES the land holds or derives, and the live
cards' own terms. `prices` became the priced menu — it quotes the whole
sheet at what this land charges today, and every `buy`, bed, healer's
day, commission and dose pays it.

**The encounter table.** A live card or a derived state can put its own
people on the land's ground, filtered by ground (`road` / `wilds`) and
rolled at its own chance. It replaces WHO the party meets and never how
hard: the level stays the road's party-independent roll.

**The content.** 30 crisis cards (five or six a land, up from two to
four), one flavor anchor per land that is not trouble at all, 17
relation edges (up from nine), and five card CHAINS — one of which
crosses a relation.

### The calls the spec left open that the build had to settle

- **The frame's `menu={"paper_rate": 0.25}` and `quest={"post": "grain
  escort"}` placeholders were not implementable as written**, and the
  `encounter={"kinds": ("bandit",)}` payloads named a foe row that does
  not exist. All three payload shapes were re-authored and are now
  validated at import against `sites.FOES`, `MENU_TERMS` and the quest
  verbs. `worldsim.py` imports `sites` for this; it is one-directional.
- **A card's posted job is a full quest template, not a title.** The
  alternative — retitling a rolled template — produced jobs whose
  description contradicted their name. Authoring the template on the
  card costs ~10 lines a card and buys real geography, a real giver's
  face and a real epilogue through the ordinary generator.
- **Card jobs never carry a weapon reward.** The reward mode zeroes
  `gold_total`, which would have silently eaten the card's pay premium.
- **Pay is stamped at posting time, not read out at turn-in.** A job
  taken keeps the terms it was posted at — which is what makes a good
  week on somebody else's board worth walking to, and what keeps the
  save honest.
- **The menu had to read STATES, not only cards.** Cards alone cannot
  reach a DERIVED state, because no card in the target land ever names
  it — and a relation reaching a price is the entire point of having a
  relations table. `STATE_MENU` is that road. Its risk is
  double-charging (a card and the state it sets both moving `goods`), so
  `_validate_menu_tables` makes the clash an import error.
- **The world layer's readers are STRICT** — asking about a land with no
  layer under it raises. The first cut had a `has_layer` guard that
  answered neutrally instead, and it was wrong for the reason the
  no-backcompat directive names: worldgen opens the layer before it posts
  anything, so a land without one is a state the game cannot produce, and
  a reader that returns a neutral answer for it is indistinguishable from
  a bug that returns a neutral answer. It existed only to keep one test's
  monkeypatched world loading; the test now builds a legal QUIET world
  (`_flat_world`: layer rolled, every land normal, no card, no state)
  instead, which is both a truer control and a stronger assertion. The
  directive gained a bullet naming this species (develop.md).
- **`generate_world` now opens the world layer FIRST, not last.** The
  board reads it, so it has to exist before the opening postings. A land
  in crisis quotes crisis money on day one.
- **The frame's "the layer moves no worldgen stream" contract had to be
  restated, not kept.** It is incompatible with "the board reacts to
  world state" — the plan chose the latter. The contract is now: the
  stream is untouched (same geography, cast, templates, levels, clocks,
  armory) and `gold_total` is the ONE field the layer moves, by exactly
  the band's multiplier. Two paired tests pin both halves.
- **Two content knobs moved during the session, for coverage rather than
  balance.** `ensimaa/rented-land` opened from crisis-only to crisis or
  normal, and the Ensimaa→Gibili timber edge now also reads
  `eviction-on`. Before them the cross-relation chain fired zero times in
  24 000 land-days; content that ships and is never observed did not
  ship.
- **The `lodging` term cannot discount.** `TAVERN_COST_PER_HERO` is 1g
  and prices never round to zero, so a 0.80 multiplier is invisible.
  Left alone: the base price is the engine's, not the world layer's.

### What it costs, measured

Full numbers in benchlog.md. This is the first worldsim rung the career
sim can see, and the honest read is that it is still noise: 120 careers
against a neutralized-band control give L5 81 vs 84, L8 71 vs 69, L11 38
vs 36, median death L9 both, turn-in bands and expiry unchanged. The one
directional read is PACE — a capped career runs ~94 days against ~92,
because crisis lands post shorter boards. Nothing was retuned.

The layer's own pacing over 43 200 land-days: a card is posting work on
22% of them, some price is moved on 65%, and somebody the world put
there is on the roads on 10%.

### What it buys at the table

The map page is the tell. Before this session it read the same board
counts in every land; now a prosperous Gibili shows 6/5/3 jobs beside a
Firascir in crisis showing 4/3/1, and the difference was not put there
by the player. Walk into a land whose lord has shut the hand-mills and
the potion costs fourteen instead of ten, the board is one row shorter,
the row that IS there is *The Bailiff's Round*, and the giver is the
bailiff. Cross a bridge his toll-men hold and the road takes twelve gold
before the trip starts, and the encounter it rolls is those same
toll-men. That is one card, reaching the player through four of the six
outlets in one afternoon — which is what the framing meant by RECURRENCE
being the property that makes an NPC exist.

**Recorded.** rules.md's new *The Economy Floor* add-on; dm.md's "What
the land costs" play protocol under "The land itself" and its
quick-reference numbers; develop.md's Files (`worldsim.py`, `quests.py`,
`session.py`, `test_worldsim.py`), dev map and Balance section;
worldsim.md's ECONOMY land packets section CUT; plan.md's economy-floor
rung DELETED and the ladder renumbered to two; benchlog's 2026-08-09
entry.

### Two follow-ups the designer called the same day

**The no-backcompat directive got a bullet it was missing.** Reviewing
the session, the designer asked whether the "nothing writes to the save,
so an edge can be re-authored without a migration" framing had smuggled
a compatibility shim in. It had, in a form the directive did not name:
`worldsim.has_layer`, a guard that made every outlet reader answer
neutrally for a land with no world layer under it. No save was involved
— but the failure mode is identical, because worldgen builds that layer
before it posts anything, so the missing case is unreachable and a
neutral answer for it is indistinguishable from a bug returning a
neutral answer. Its only real consumer was a test that monkeypatched
`open_world` away. **Fixed**: the guard is deleted, the readers raise,
and the test now builds a legal QUIET world instead of a broken one
(`_flat_world` — the layer rolled, then every land set normal with no
card and no state), which is both a truer control and a stronger
assertion. develop.md's "No backwards compatibility — ever" gained a
bullet naming the species, with the distinction that keeps it usable: an
optional AUTHORED field with a default is reading a schema, not
tolerating damage. `cmd_engage`'s `sighting.get("skins")` — a real
old-save fallback — was tightened in the same pass.

**`AGENTS.md` folded into `CLAUDE.md`.** Designer direction: one
instruction file, not a file plus a shim. `CLAUDE.md` now holds the
dispatcher text, and its body was scrubbed of every agent's proper name,
so restoring the two-file arrangement is a copy plus a six-line shim and
no rewriting. develop.md's Files entry carries the recipe — including the
correction that `git log --follow CLAUDE.md` does NOT cross the fold
(`CLAUDE.md` already existed, so git recorded a delete plus a modify, not
a rename); `git log -- AGENTS.md` plus `git show <parent>:AGENTS.md` is
what actually recovers the old file. The cost is stated plainly:
AGENTS.md-aware agents no longer auto-load anything from this repo until
the file is restored.

## 2026-08-10 — Politics & the ruler: the land becomes a polity

**The rung.** plan.md's worldsim ladder, third content session and the
last but one. The frame (2026-08-07) gave every land a wealth band, a
crisis deck and trade edges; the weather (2026-08-08) put a sky over it;
the economy floor (2026-08-09) made the board, the shelves and the road
read all of it. What none of them touched is what a land IS: who holds
it, what it is fighting about, and who is pulling at whom. This session
implemented `worldsim.md`'s **THE RULER CHARACTER** (the politics dump's
person half, 2026-08-06) and **THE LAND PACKETS — POLITICS** (its power
half, same day), plus the war layer's feed.

The framing that governed every choice: **politics is a GATE on content,
not a system.** Nothing here ticks, nothing accumulates, and no
political value is ever a quantity. Every piece exists to decide which
cards a land can draw and what its news says.

### What was built

**`rulers.py`** — a new file, and the only one in the repo that imports
nothing from the rest of the game. One weighted pool of 357 words
(twenty axes, one extreme step, twenty flags) with the designer's
measured column as its weights: 734 European rulers coded, 443 traited
at the kept resolution, average 3 traits each — which is the identity
that makes THREE weighted draws reproduce the per-trait marginals. The
pool SHRINKS between draws (the drawn word, its axis opposite, its
never-with partners), so three draws always land three distinct
compatible words; a lesser named authority draws two off the crown-less
355. Derived `heart` (hidden — the crime layer's desert anchor), the
affliction cap of three, the dated origin stamps, the `puppeteer` colour
beside `puppet`, and the two rolled circumstances the cluster needed:
the mode of accession (kin-blood included) and the succession state,
which reads the traits and the accession for free.

**The politics frame in `worldsim.py`.** The CONSTITUTION slot (one per
land, default-heavy die, the wealth-band pattern), the TENSION roll (one
at worldgen, two in crisis, standing ones held on top), the FACTION cast
the tensions imply and the 34 authored directed verb EDGES between them,
and the RULER sheet on the land layer. `card()` grew five ANY-OF admits
— `tension`, `constitution`, `traits`, `succession`, `faction_edge` —
and the state payload grew `constitution` and `succession`.

**The content.** 76 politics cards (31 of them Firascir's own, by the
asymmetry doctrine: it is the baseline land and the sheet's weights are
already its), 7 more relation edges, and the war feed — a casus belli
pool rolled beside story.py's aggressor, the four diplomatic instruments
as authored edges with cards standing in them, and the five-card
succession cluster.

### The calls the spec left open that the build had to settle

- **The tension is the DECK GATE, not just an admit.** worldsim.md said
  "only cards whose tension holds enter the land's crisis deck"; the
  cheap reading would have been an ordinary admitting condition. It is
  both, and the deck filter is the load-bearing half: without it
  Firascir's deck is 42 cards deep and its econ content drowns. With it,
  a land holds the six econ cards plus the one or two quarrels it
  rolled. That is what lets a packet be a wide POOL — the designer's
  selection doctrine — instead of a content budget.
- **The ruler sheet lives on the LAND LAYER, in one copy.** The obvious
  reading of "rolled onto the land RULER notable" is fields on the NPC
  dict. But `worldsim.open_world` runs before `quests._cast_the_land`
  (the board has read the layer since the economy floor), so the sheet
  has to exist before the face does. It is rolled with the constitution
  and the tensions, and `_cast_the_land` writes the notable's id ONTO
  the sheet. One copy in the save, and either half finds the other.
- **The politics rolls come AFTER the wealth roll on the same stream.**
  Every world's bands are therefore exactly what they were before
  politics existed — pinned by a test that re-rolls the band off the
  same derived seed and compares.
- **Trait admits are ANY-OF, states are ALL-OF.** The two read different
  shapes: a land holds every state in its list, but its crown holds
  three words out of 357. worldsim.md asked for any-of explicitly for
  the mad family; it is the only sane reading for all five politics
  slots, each of which reads a slot holding one or two values.
- **`heart` never reaches the player.** It is printed on `world` and
  nowhere else. What the town says of its king is the trait words
  themselves — which is not a leak but the point: those words ARE the
  reputation everyone in the land already has of him, and rumor fuel was
  one of the three things the sheet was merged for.
- **Most politics cards move the board.** They did not, in the first
  pass, and a fixed-seed check caught it: a world where all six lands
  roll NORMAL drew three politics cards in seventy days and its boards
  never moved, which fails the thread's first invariant. Sixty-odd cards
  gained a `slots` or a `reprice`. A regency posts less ordinary work; a
  disputed succession pays over the odds for blades; a general strike
  takes two rows off the board.
- **The casus belli rolls off a DERIVED rng** (`casus:<seed>:<land>`),
  so no existing world's aggressor, faces or targets move. It is said
  once, at the first herald, and left on the land's news — which needed
  `worldsim.post_news`, the one door into a land's news from outside the
  deck. The war layer is authored content that happens to the world
  without a card behind it, and that is the only legitimate customer.
- **The diplomatic instruments are edges with cards in them, and
  nothing more.** The tempting extra — rolling an instrument at wave 4
  to seal the peace — was left out: the ladder asked for "the diplomatic
  instruments as relation edges", and a generic seal would have needed
  edges for arbitrary land pairs. The four authored pairs each have a
  state one land holds, a state the other derives, and a card standing
  in it.
- **A card that names somebody keeps him.** `_authority_hook`
  generalizes the fog necromancer's trick: the banned lord, the
  witch-finder, the bandit king and the pretender each roll a two-word
  crown-less sheet, and the same man is still there the next time the
  card comes round. Recurrence is the property that makes an NPC exist
  at all (the 2026-08-05 framing), and no single outlet produces it.
- **One existing test was pinning a narrower claim than the code makes.**
  `test_the_quoted_gold_is_the_one_thing_the_layer_moves` asserted a
  posting's quote is the band's multiplier; the economy floor's actual
  contract is `board_pay` — the band TIMES whatever card stands over the
  land. It happened to hold because no opening card in that seed carried
  a `reprice`. It now asserts `board_pay`, and separately asserts the
  band alone where nothing stands.

### What did NOT ship, and why

The packets' **facts** and **options** stayed in worldsim.md beside the
econ leftovers — the same treatment the economy floor gave them. A fact
costs nothing at runtime and the engine never sees it; an option wants a
priced-menu entry or a crime-layer category of its own, which is a
different session's work. The ruler sheet's **per-land and per-race
modifier columns** are also still to author: the Firascir baseline
serves every land, which is exactly what worldsim.md said it would until
someone measures the others. The **PC's own blank sheet** remains the
open question it was.

### Where it landed

`rules.md` gained *Politics & the Ruler*; `rulers.py` is registered in
develop.md's Files with `worldsim.py`, `test_worldsim.py` and `story.py`
updated; worldsim.md's RULER CHARACTER and POLITICS sections are CUT and
replaced by a leftovers section; plan.md's ladder is down to one rung.
`test_worldsim.py` grew 51 tests across six classes. Nothing was
re-measured: the rung adds no bench-visible field the economy floor did
not already add, and every knob it introduces is hand-set and
sim-unverified by the standing convention.

**One softening caught in review and removed.** `story.casus_belli_line`
first returned `""` for a story dict with no `casus_belli` key, with a
comment about wars from before the reason existed. `init_story` always
rolls one, so that is precisely the species the 2026-08-09 rule names: a
reader softened for a state the code cannot produce, whose only caller
for the missing case was the test written beside it. The reader now
indexes, and the test asserts every rolled war carries a reason and that
an empty story raises.

---

## 2026-08-11 — Religion & magic: the last rung, and the two record kinds nobody had built

plan.md's worldsim-build ladder had one entry left, and it asked for two
packets at once: the Sun communion frame with the per-land worship facts
and options, and the whole magic dump — the recruiters, the wild talent,
the hunt, the reagent trade wired into the crime layer, and the per-land
organizations. Both shipped. **The ladder is now empty**, and the thread's
next move is a playthrough, not another rung.

### The thing the rung had to build before it could author

The ladder's own instruction was blunt — "the session below AUTHORS CARDS
AND EDGES; nothing in the frame is its to build" — but the rung's text asks
for **facts** and **options** by name, and worldsim.md's five record kinds
were still three. The two shipped rungs before this one had punted them
both to a leftovers section. There was nowhere to put a fact and no such
thing as an option, so the rung built them, and kept them as cheap as the
doctrine allows:

- **A FACT is DM-only and the engine cannot see it.** No fact key is a
  state, a card key, an option key or a tension — pinned as a test, because
  the only thing that keeps a fact free is that nothing can look one up.
  Its whole surface is a new `lore` command. Thirty-two of them, five or six
  a land, and every one stands behind a card, prices an option, or names
  something the player can already do (the characteristic criterion, applied
  to the record kind that most invites decoration).
- **An OPTION does exactly three things and there is no fourth.** `bless`
  (satisfaction, on a cooldown), `book` (the spellbook gate at this land's
  price), `sky` (Tergal's rain stone). The closed verb set is the whole
  design: an option that needed new machinery would be a feature request
  wearing a content hat, and the rung's standing rule is that what the
  packets did not design does not get built. An option never owns a price
  alone either — it carries a catalog number and the priced-menu **term**
  that moves it, so the world state is on this counter like every other.

### The calls the packets left open

- **Temple healing is not an option.** plan.md said temple services are
  "healing, burial, blessing" as priced-menu entries. Burial and blessing
  are new things to buy; **healing already exists** — in the two human lands
  the temple *is* the healer, so healing is the `healer` term, which the
  interdict already puts up and the unlicensed holy well now undercuts. A
  second healing counter would have been the same action at a second door.
- **Ensimaa sells nothing.** The obvious symmetry — a temple counter a land
  — is wrong here: the elven packet's whole axis is reverence without
  worship, and its only religious architecture is a silent open-roofed court
  with no clergy and no services. The asymmetry doctrine says a land does
  not need what its neighbour has. The counter's absence is the content.
- **The religion packets needed tensions of their own.** Politics kept
  church POWER, so gating worship cards on the political tensions would have
  put the parish's cards behind the bishops' quarrel. Eight new tensions
  with thirteen factions and sixteen edges under them, one or two a land:
  two shrines and one saint, the abbey against the families, which face of
  the god rules the year, one word in one old text, the tomb priests against
  the quota, the white shamans against the dark one, the chapels against the
  ladder faiths. The cost is dilution — a land now rolls one tension out of
  four or five instead of three or four — and that is the gate working as
  designed: the packet is a POOL, and each rolled world stays specific.
- **The schism clock runs BOTH ways.** worldsim.md said cards on the edge
  fire in both lands. That is two relation edges deriving the same word onto
  each other and ONE card whose `land` names both — the first card in the
  game that sits in two lands' decks. It needed no new machinery, which is
  the test that the frame was built right.
- **The reagent trade's crime wiring is a third state table**, in the shape
  of the two the economy floor shipped: `STATE_MARKS` says what a state
  makes ROBBABLE, and `crime.roll_mark` takes the faces as a default-empty
  argument. The extra marks are dealt in BESIDE the band's own rather than
  replacing them — a consignment in the bonded yard competes with the
  ordinary vault, it does not evict it. Two more rode along because the
  religion packets pre-ordered them: the opened tomb (the mountain's richest
  rooms are its tombs) and carnival's masks.
- **Two named pools, no new creature row.** `_UNDEAD` and `_CASTERS` over
  the catalog the game already has. The draugr, the knockers-as-creature and
  Tergal's grave-made ghosts still wait for the monsters & fauna dump, as
  ruled; the foreign-graveyard card ships over skeletons and ghouls instead.

### The doctrines, made mechanical

The magic packets are mostly stance, and stance is easy to write and easy to
contradict later. Three of them are pinned as tests instead:

- **THE MARGIN** — magic is real, known and SMALL. Not one magic card moves
  a wealth band or a constitution. No throne, market or war is decided by it,
  as a property of the data rather than a promise in a doc.
- **CONDUCT, NOT CREED** — the design requirement that a caster playthrough
  is never dominated by automatic hostility. The hunt admits on
  `talent-loose` and on nothing else: on what somebody DID, never on a land,
  a ruler or a faith.
- **THE PACT STAYS OUT** — no fact, option or news line in either packet
  contains the word.

The price rule got its own shape too: the rain stone buys **two days** of
rain over one land, never a season. Healing is retail and so is weather,
which is what keeps every famine and drought card safe from "why not just
cast something".

### What did NOT ship, and why

The **econ and politics packets' standing facts** stay in worldsim.md: they
belong to sessions that already ran, and hauling them into `FACTS` now would
be this rung rewriting someone else's leftovers. (They would fit the record
kind unchanged, which is the point — the door is open when someone wants it.)
**CURSED WORK** stays with the parked non-weapon magic items row, as ruled.
The **ruler sheet's magic cells** are still hand-set; the packets now say
which direction each land should move them, and the modifier columns are
still deferred. The **temple/penance wiring** was never this rung's.

### Where it landed

`rules.md` gained *Religion & Magic*; `worldsim.py`, `crime.py`,
`session.py` and `test_worldsim.py` are updated in develop.md's Files and
dev map, with a balance note recording that the rung's one bench-touching
surface is player-initiated and therefore invisible to a sim. worldsim.md's
RELIGION and MAGIC sections are CUT and replaced by a short residue section;
plan.md's ladder is **empty** and carries the call to play the build before
scheduling anything else. `test_worldsim.py` grew 35 tests across four
classes. Nothing was re-measured beyond a 12-career spot check that read in
family: the options are a purchase no bench makes, and `roll_mark`'s new
argument defaults to empty.

**One test was pinning the shuffle instead of the rule.**
`test_a_card_with_nothing_new_to_say_stays_in_the_deck` assumed a named card
would still be in a seed's deck after worldgen. Adding cards reshuffles it,
and the card was drawn at the opening. The contract is the SKIP, not the
order, so the test now puts the card in the deck itself and asserts what it
always meant to.

## 2026-08-11 (follow-up) — The funeral card is cut

**Where it started.** Three questions on the shipped politics and
religion rungs. One was a directive: `ensimaa/the-funeral` — the
worship card remembered as "the elves have forgotten their death
rites" — is out.

**The cut.** The card, its `land-mourning` state word and its
STATE_MENU row are gone (nothing else set or read the state). The
elven packet was the flaw-worn-liturgically pass's centerpiece (the
2026-08-06 regrounding), so the record: Ensimaa now runs FOUR worship
cards where every other land runs five, and is the one land with no
ungated religion card. The worship-floor test carries the exception by
name; develop.md's content bill and chance-knob note updated. The
2026-08-06 regrounding directive itself (recognizable high-fantasy
elves, subtle weirdness) still stands over the rest of the elven
material.

**Discussed, not changed.** (1) The politics distribution is as built
and intended: 31 of 76 cards are Firascir's own (asymmetry doctrine —
the baseline land whose weights the ruler sheet already carries),
Mortellaria 14, Ensimaa 8, Tergal 7, Gibili 7, Dvarvengrond 4, plus
the 5 crown-wide succession cards; the tension gate is what keeps the
deep packet from drowning a deck. (2) Whether worldgen should force at
least one land out of NORMAL — about one seed in eleven rolls all six
lands quiet ((24/36)^6 ≈ 9%) — was raised and analyzed; no decision
taken, the band roll is unchanged.

## 2026-08-12 — The build reviewed whole, and the review's findings fixed

The designer asked for the six-session worldsim build (plus the funeral
cut) to be reviewed against its pre-implementation plan — completeness,
cohesion, bug-freeness — and then for the findings to be fixed on the
reviewer's own judgement. One designer ruling arrived with the fix
order: `found_settlement` / `materialize_settlement` are KEPT as DM
tools and documented for the DM, for the player who wants to just
travel and explore around.

**What the review found.** Completeness ~95% and the paperwork lifecycle
tight (15 of 16 doc-claimed content counts verified exactly; every
settled ruling honored; the postponed list intact). The gaps clustered
where spec sections were cut as "consumed" without fully shipping: the
PLAGUE CHAIN (the one entry the ladder itself named), eight econ packet
cards, two magic-doctrine lines. The code half found real bugs the
247-test suite could not see, all verified by execution before fixing:

1. **Seven chain cards could never fire** — each admitted on a state its
   own track held as `while`. A track draws only while its live slot is
   free, and `roll_land` expires the live card (dropping its `while`
   states) BEFORE drawing on the same track — so the state and the free
   slot never coexist. Dead: the whole Gibili revolution arc past its
   first link (general strike → barricades → junta), the salt revolt,
   both Tergal escalations, the dwarven arbitration. Since the junta was
   the deck's only constitution flipper, no constitution could ever
   change in play. Verified dead over 180 worlds × 600+ days: zero fires
   against prerequisites firing 10-97 times (benchlog has the after
   table).
2. **The commune card did not exist** — rules.md, the module header and
   `set_constitution`'s own docstring all promise "the junta and the
   commune" as the two flippers; only the junta was written.
3. **`mortellaria/revocation` locked its land in CRISIS forever** —
   `wealth_while` on a clockless card stores no live entry, so `_end`
   never runs and the band never comes back.
4. **The rain stone sold two days and delivered one** (`until = day +
   holds` against a purchase day whose sky is already rolled; `holds=1`
   was a paid no-op the validator explicitly blessed).
5. **A completed card job blocked that card's job on that board
   forever** (the dedupe set read `world_card` off done postings too).
6. **Toll terms the road never charged** — `road_charges` gated on
   `toll-squeeze` alone, so the tax farmer's 1.50 and the free company's
   1.80 printed on the price sheet and took nothing at the bridge.
7. Smaller: `python quests.py --demo` crashed on the old `board_slots`
   signature (and its `--day` loop never rolled the world); an
   interrupted trip re-charged tolls and re-walked the weather detour on
   the retry; a news line posted late on an already-told day died
   between two same-day stamps (`post_news`'s herald was the customer);
   teleport arrivals heard no news/sky/prices; `ensimaa/writ-revoked`
   admitted on an edge its own gate could not cast; `deposit-dead` was
   authored menu data nothing could produce; the "goes through owing"
   travel line asserted a debt rules.md denies; a soft `CARD_CHANCE`
   reader; a stale STA-for-STR comment; and doc drift (the "30 crisis
   cards" miscount — 32; the frame pacing percentages shifted a slot;
   "three lands sell a teaching" — four; develop.md's worldsim.md entry
   contradicting itself; the overdue "off-screen event simulation"
   parked-entry deletion the economy floor owed).

**The chain repair, and the calls it took.** The working chains all use
one pattern — the setter `set`s a link state that OUTLIVES it, the
successor admits on it and `clear`s it — and the seven dead cards
deviated by holding their links as `while`. (The tell that this was a
typo, not a design: two successors already carried `clear` for states
that would have died with their setters anyway.) The links moved to
`set` on the six setters, `without=` guards went on each setter so it
does not stack its own link (the shipped chains' convention), and two
judgement calls went beyond the mechanical swap: **the salt revolt now
clears `tax-farmed`** (the revolt ends the farming-out; also keeps the
state from standing forever in worlds whose tension never rolled the
revolt in) and **the Tergal escalations admit `grass-gone` alone**
rather than herd-loss + grass-gone — the season scar is the thing that
drives a mourning war, it is the state built to outlive the card, and
the raid card already competes for it (the deck deciding which answer a
starving steppe gives is the junta/commune coin in miniature). The
general strike also clears `mills-stopped` (the whole nation stopping
subsumes the one mill town).

**The commune.** Written as the junta's mirror off the same
`barricades-up` admit at the same `chance` 0.25 — whichever the deck
draws first is how the split army lands, which is the packet's own
"which way do the soldiers point" coin. Its quest is the ration barge
(the commune governing with bread), its constitution flip is the record
`roll_constitution` already carried. Politics goes to 77 cards.

**The two new validators, because content will be authored again.**
`card()` itself now rejects a clockless card with a `while` /
`wealth_while` payload (bug 3's whole class), and import-time
`_validate_reachability` rejects a card admitting on a state only its
own track holds as `while` (bug 1's whole class) — plus
`_validate_state_tables`, which polices STATE_MENU / STATE_ENCOUNTERS /
STATE_MARKS keys against what the game can actually produce
(`deposit-dead`'s class; the member and its menu row are cut rather
than authored a producer, since the vein cards' drying/reopened cycle
is the story the slot actually tells). `EXTERNAL_STATES` names the one
state a verb sets that no card does (`rain-bought`).

**Revocation got a clock** (25-40 days, season-scale like the herd
failure) rather than a permanent `wealth:` drop — the frame's own
contract ("a failed harvest is a season of crisis and then it is over")
and the fact that the deck holds no Mortellarian recovery card decided
it. The ban itself (`faith-banned`, a `set`) still stands forever;
it is the ECONOMIC shock that passes.

**The toll gate widened to the term itself**: the road charges wherever
the effective toll term is over 1.0, whatever raised it — one state was
never going to stay the only toll story once politics started authoring
toll movers. A discount term with no toll under it charges nothing.
rules.md's line updated. With it, travel grew a paid-crossing marker
(`road_paid`): an interrupted trip's retry no longer pays the toll or
walks the detour again (the repeated base days stay, the standing
re-issue design), and the empty-purse line now says what rules.md says
— the party walks, owing nothing.

**The news watermark became a count** (`news_seq` / `told_seq` on the
layer) instead of a told-day: append-only sequence numbers survive the
NEWS_KEPT trim and a line posted late on a told day survives to the
next telling. Teleport arrivals now hear the same news/sky/prices a
road arrival does (an arrival is an arrival).

**The DM settlement tool** (the designer's ruling): dm.md's world-layer
section grew "The map can grow at your call" — a save-editing-family
snippet around `quests.found_settlement`, verified end-to-end (the
founded place arrives named off the reserve, serviced, known,
travelable, stamped with day and reason). plan.md's postponed list
records the other half honestly: no authored card or relation calls the
draw yet, and that content should come out of play.

**Restored, not ruled out.** The plague chain, the eight econ cards and
the two magic-doctrine lines went BACK into worldsim.md as residue with
their original packet text recovered from the pre-cut file — the
review's rule being that a cut section must equal shipped code plus
explicit waits, and these were neither. Nothing was ruled out; nothing
new was scheduled (the thread still wants play first).

**Left alone on purpose**: the succession slot's re-assertion (a second
tanist scramble re-stamping `disputed` is a new scramble, not a bug);
settlement `camp`/healer nights carrying no news line (mirrors
`conquest_news`; dm.md's "settlement nights" reads as tavern and
downtime); and the one-shot guards were added only where a re-fire
would be absurd (`burning-rolls`, `the-search`), not to every permanent
card — a reshuffle re-firing "the fair is on" is the deck breathing.

Fire counts, the revocation recovery distribution and the career-sim
sanity run (in family throughout) are benchlog's 2026-08-12 entry. The
suite grew 642 → 651: the two validator contracts, the chain-link
clock test, the politics chains each reaching their successor, the
Gibili arc run to BOTH constitutions, the two board repost rules, the
raised-toll road charge, the rain stone's full paid window, and the
late-posted news line.

## 2026-08-12 (later) — Quests are narrated: the display rule softened, and the retro list audited

**The prompt** (the designer): the standing instruction had quests
passing to the player as verbatim script output in a code block, and in
play that reads jarring — the template desc is a one-line prompt, and
what the quest actually IS is often not obvious from the row. The
ruling: script outputs and numbers stay good info to pass on, but
quests and quest resolutions are NARRATED, in the simple text-adventure
style, and the DM pays attention that the quests and events make sense.

**The rule, written in** (dm.md):

- The board/funnel bullet: the display block is the format for the
  NUMBERS only; what the job is gets told in the giver's mouth in the
  plain voice, never left to a pasted row or the desc line — say it so
  the player can picture it, and square it with the place and the
  day's news first.
- The turn-in bullet: the QUEST COMPLETE banner and its numbers stay
  display; the epilogue line and the turn-in prompt are MATERIAL — the
  job's ending is told as a short scene, the aftermath fact folded into
  the fiction.
- The turn protocol's fight-end fence: keeps the mechanics (XP, pay,
  satisfaction, tally, levelup menu); the resolution words (epilogue,
  turn-in prompt, a giver's failure line) come out of the fence and
  into the prose.
- Narration style grew the two governing bullets: "Quests and their
  resolutions are NARRATED" (the deliberate soft spot in
  displays-over-prose) and "Make the quest make sense" (read the
  pieces — desc, giver, sites, the land's state — before narrating;
  where they clash, the fiction bends and the numbers stay the
  engine's; the same duty covers waves, news lines, and hell's
  letters).
- scene-example.md's fight turn refit to model it: the EPILOGUE lines
  left the end fence, and the well's reopening is now told in the
  turn-in scene. plan.md's pivot consequence ("Displays over prose")
  softened in place with a pointer to dm.md.

**The retro list audited** (the designer's ask — several points looked
already implemented, and were):

- **The quest wording rework (retro item 2) had ALREADY SHIPPED and
  was never crossed off.** Commit ef9e7d9 ("Rewrite quest content in
  plain CRPG style", 2026-07-22) took the good templates in
  `quests.py`, the epics in `story.py`, and the then-current
  `karma.py` to the plain register the same day writing.md landed —
  the current desc lines ("Bandits are attacking travelers on the
  king's road. Find their camp and kill them.") are that pass. The
  karma half was later redone wholesale with the assignment ladder,
  and the crime layer's copy was written fresh in `crime.py`. The item
  is deleted from plan.md; the queued quest-shape pass's
  cross-reference now points at the shipped rework instead.
- **The levelup-menu sub-item of retro item 1 shipped 2026-07-28**
  (the display pass: fixed command-headed sections, the right-hand
  cost column, `Ability.brief` / `Move.brief` one-liners under every
  buy) together with the fitted hero readouts (`hero_block_lines`,
  shared by `status` and `ui/party.txt`) — develop.md's Files section
  already documents both. The sub-item is deleted; the STATUS DISPLAY
  sub-item is trimmed to what remains true (the quest/world/karma
  lines around the hero blocks, and `board` / `map`, still print
  DM-shaped output), and the fitting-pass sub-item now names
  `people.person_line` as a concrete straggler.
- **Still genuinely open, left standing**: the status/board/map
  fitting, the non-combat fitting pass, `ui/minimap.txt` (session.py
  still calls it planned), the parked E1/P1 shorthand, and playing the
  dark path in the new register (no probe playthrough on record).

## 2026-08-08 (in play) — Plain English first: the claudese problem named

A style session raised from the table, two turns into a fresh playthrough
(the branch's game continues around it). The designer stopped play to name
a narration failure that survives every existing rule in writing.md, and
that he could not prompt Claude Opus out of: "claudese" — literary
compression that reads as style but has to be translated back into plain
English to find out what happened. His examples from the two live turns,
with his own translations, became the spec:

- "Two days on the road and nothing on it" -> "nothing out of the
  ordinary has happened."
- "Ensimaa arrives as trees before it arrives as a city" -> "you reach
  the forests of Ensimaa, and then a city."
- "with the rain going sideways" -> "in heavy rain."
- "has the worse problem and says so straight" -> "also has a problem:"
- "one of them paying in steel" -> "offering a zweihander as a reward."
- "The rest of the porch is out of your weight entirely" -> "the rest of
  the jobs are probably too difficult for you." (Metonymy called out as
  painful by name.)
- "Word on the porch also runs to work elsewhere in the land" -> "some
  jobs mean travel to other parts of the land."

**Why the existing guide missed it.** writing.md's Avoid examples all
show purple prose and mystery-teasing; steering away from those lands on
clever-laconic, which the guide never exemplified as wrong. Worse, the
register words themselves ("terse", "dry", "deadpan") read as a style to
perform, and the model's idea of good compressed prose IS the crafted
turn. A third suspected cause: the instruction docs are themselves
written in the compressed register, and the narrator mirrors what it
reads.

**What shipped:**

- **writing.md, "Plain English first"** — the new section: the failure
  mode named, the designer's seven pairs kept verbatim as Avoid/Use, the
  TRANSLATION TEST (read the sentence word by word; if what it literally
  says is not what happened, write what happened), and the five forms to
  catch (non-actor subjects, metonymy, the crafted opener, idiom as
  intensity, the narrator describing delivery). Plus one ranking line in
  the target-voice section: plain comes before terse. Final check gains
  the translation-test bullet, so the scene-page reread applies it every
  message.
- **dm.md, Narration style** — a pointer bullet: the translation test
  governs every line; the reread's first job is finding sentences a
  reader would have to translate, and replacing rather than polishing
  them.
- **scene-example.md** — its own claudese purged ("fire in your hands
  that nobody taught you", "cracks it dead", "Short and ugly, the way
  well work is", "Ventoro draws water again").
- **The live turn 2** (ui/scene.md, transcript) rewritten to the plain
  register as the worked before/after.

**Open, deliberately:** a full register rewrite of dm.md itself (the
mirror-what-you-read theory says the play protocol's own prose teaches
the narrator its habits — ~1750 lines, a dedicated session if wanted),
and whether the model switch made this session (Opus -> Fable) moves the
needle on its own. The cheap standing lever: every line that bugs the
designer in play gets pasted into the chat and added to the Avoid/Use
list — real pairs from real turns are the strongest instruction this
file has.

## 2026-08-08 (later) — dm.md rewritten in the plain register; the naive directive

Follow-up to the morning's Plain English First session, on the
designer's direct instruction: rewrite dm.md itself in the plain style,
because the instruction docs teach the narrator its register by example
(the mirror theory from the morning entry). Two additions to the spec
first, both from a fresh flagged line:

- "A storm has held the land since yesterday" joined the Avoid/Use
  pairs ("There has been a storm since yesterday") — the non-actor
  possession shape ("X has held the Y") is the same failure as "the
  porch" and "word runs".
- **The naive directive**: err on the side of TOO naive. A flat,
  simple, almost childlike sentence is closer to the target than one
  that reads as good writing. Written into writing.md's Plain English
  First section as a standing rule; the designer's own word for the
  target register is stronger than "plain", and the direction of error
  is now explicit — when unsure, choose the more naive sentence.

**The dm.md rewrite.** Full register pass, every section, ~1760 lines:
rules, numbers, commands, dates, headings and section order all
preserved (verified mechanically: headings identical, every backtick
command token survives, all date markers survive, the number census
matches except the deliberate "half again" -> "1.5x"). What changed is
sentence-level register: aphorisms unpacked ("a doorstep, not a
railroad" -> "an offer, not a forced path"; "The world proposes; the
player disposes" -> "The world offers the options; the player
chooses"), metonymy and non-actor subjects replaced ("say it in the
world's mouth" -> "have somebody in the world say it"; "the fiction's
licence to make bread dear and faces thin" -> "make bread expensive and
people hungry"), instruction-register cleverness cut (the "qi, not iq"
pun; "narrate heat as weather" -> background pressure; "the spiral is
the player's own bed" -> plain consequence language), and the two
stylish example quotes flattened ("every exchange leans wrong now" ->
"Sela is at -3 now"; the moves narration example). Doctrine shorthand
with an established meaning was KEPT on purpose: "narrate the skin,
trust the row", "the numbers are the game", the ferocity tags.

**Worldsim copy audited** (the designer's third ask) — findings
reported in chat, not yet fixed: the card news lines and job descs are
MOSTLY compliant (concrete, present tense, named actors, deadpan), but
~15 of 164 news lines and a handful of STATE_WORDS phrases fail the new
rules, in five repeating shapes: the "X has the Y" possession line
("the storm has the roads", "the dust has the plain", "carnival has the
streets"), period vocabulary ("bread is dear", "timber is dear", "steel
is dear" — writing.md's CRPG-vocabulary rule), abstract subjects doing
person actions ("Enclosure and debt made {bandit}, and charisma armed
him"), narrator winks ("which is comedy until...", "Buyer beware,
constitutionally", "a level of badass richer"), and two register breaks
proper: an unnamed subject ("The death-face rite makes it locally
thinkable" — the "it" (necromancy) is never named) and design
vocabulary leaking into player-facing copy ("The card is the day
after..."). Fixing them is a small follow-up pass once the designer
signs off on the list.

## 2026-08-08 (still later) — The kept shorthand purged; the worldsim copy fixed

Two short follow-ups on the designer's sign-off of the audit list:

- **dm.md's kept doctrine shorthand is gone.** "Narrate the skin, trust
  the row" (both instances), "the numbers are the game", "the loot is
  the loot", and "STA is STA" are all unpacked into plain statements;
  the ferocity tags and other literal rule names stay.
- **The flagged worldsim copy is fixed** — six STATE_WORDS values (the
  three "X has the Y" possession lines and the three "dear" prices) and
  ten news lines (bank run, colony fleet, mercenary-home, dust storm,
  bandit king, one-heir, the purist reserve, the flagellants, the dated
  End, the death-face chair, the master's lessons). The two spots in
  rules.md that quote a changed state string, and one test docstring,
  were synced; test_worldsim (256), test_places and test_history pass.

## 2026-08-08 (play findings) — The rout, the loose end, and the turn-in

The first played session on the current build (a rolled L12 duo, the
Tergal troll bounty) surfaced one dissatisfaction that unwound, over
three chat rounds, into a designed feature cluster: **THE TURN-IN, THE
ROUT & THE HUNT**, now in plan.md ready for implementation. Nothing was
built this session; the road the discussion took, and the calls settled
on the way, are the record here.

**The complaint.** A won troll fight ended with the troll breaking and
escaping — the QUEST COMPLETE banner then paid in full and printed "the
giants are dead" over a log that said otherwise. The designer's framing:
enemy escape is only satisfying as a RELIEF (the party was in danger)
or as an EVENT (interesting for better or worse); as a common outcome
of comfortable wins it is neither, and handling all its narrative
outcomes by hand is not worth it. Remove it, make it rarer, or —
counterintuitively — make it more likely when the party is in bad
shape.

**The measurements** (300-fight probes, level-matched duos). Escape
concentrates in exactly the wrong fights: solo big monsters (troll 54%
of won fights, 50% with the party ending fresh; ogre/bear 23%) because
deep HP pools hover below the half-HP trigger while high DEX plus the
+2 FLEE_BONUS beats the party's average in the chase; ordinary at-level
packs almost never escape (L6 packs 0% — they die from above half in
one blow). The condition-correlation the designer wanted turned out to
be HALF BUILT already: pursuit DEX is STA-weighted and unfit heroes
never pursue, so the troll escapes 96% against a battered party. Only
the fresh-party base rate was broken.

**The decisions**, in the order they fell:

- **Keep the mechanic, fix the chase** (not removal, not new pursue
  micromanagement): the rout loses FLEE_BONUS (a collapse picks
  nothing; the party's deliberate retreat keeps its +2), runners'
  chase DEX gets HP-weighted, and the rout gets its own stricter
  trigger (~1/3) so `fight_winding_down` stays untouched at half for
  the standing orders. Estimated: ogre/bear ~0-6%, troll ~33% (its
  regeneration holds it in the band — accepted as honest troll
  fiction), run-downs roughly triple, hurt-party escapes stay 90%+.
  Plus a `(driven off, not slain)` banner tag for display honesty.
- **The escaped foe becomes a STATE** — the designer's second-round
  point that escaped/killed "would be useful to model the narrative"
  became the cluster's spine: a `loose_ends` save record (who, at what
  HP/wounds, where, when, from which fight), the substrate for
  pursuit, proof, DM continuity, and eventually the parked nemesis
  record.
- **Pursuit: yes, one roll, warm-trail only.** Same day, same area, no
  night slept: 2d6 + best MIND vs the runners' weighted DEX, then the
  fight re-opens at both sides' current tracks — or the trail is lost
  and that is the story. Cold trails are DM territory by design; a
  multi-day tracking subsystem was explicitly rejected as the
  micromanagement the game avoids.
- **Proof-of-kill: an authored flag on the bounty subset only.** After
  the chase fix, escapes correlate with a battered party — flagging
  every kill quest would turn the relief-escape into a pay denial, so
  ordinary quests stay driven-off-completable and the bounty says its
  terms on the board. The existing deadline prices the chase decision
  for free.
- **The turn-in became real** — the designer's third-round finding:
  the reward is instantaneous and the giver scene has no mechanics
  under it. Settled: lifecycle grows `work_done -> turned_in | lost`;
  the gold and a NEW smallish turn-in XP tranche (QUEST_TURNIN_SHARE
  0.20) move to a `turnin` command gated at the giver's settlement and
  banded by the TURN-IN day; the field tranche (0.40) and the world's
  place-state change stay at work-done; the encounter share (0.40,
  unchanged) keeps paying per fight, a routed field paying in full.
  The clock widens by the return leg via `stamp_quest_clock`'s
  existing `extra_days` (the delivery precedent). Lost-after-done
  keeps the banked 80%, fires no failure rumor, and reads "done,
  never paid".
- **The exemption set:** deliveries unchanged (arrival IS their
  turn-in); war waves, conquest jobs, hell assignments and dark work
  all pay at work-done (no honest giver to report to; wave 3's
  scripted fall makes a return scene impossible by design). The
  turn-in stage is for honest work with a giver.
- **Mop-up pay:** the pursuit fight pays wild rates
  (`wild_encounter_xp`) — the room's share was banked when the field
  cleared; zero would make the second fight pointless, double-pay
  wrong.

**Left open for the build** (listed in the plan entry): the pursue
contest's exact numbers, the mop-up formula if wild rates read wrong at
the table, the 0.20 share's tuning, and which templates carry `proof`.

---

## 2026-08-08 (B) — THE TURN-IN, THE ROUT & THE HUNT: the build

The cluster designed in the session above, built in one pass in its
designed order (A rout -> B loose ends -> C pursue -> D proof -> E
turn-in). Every part landed as specified; what follows is what the spec
left to the build, plus the three places where reality argued with the
plan. Shipped rules are in rules.md (the rout, loose ends, the
lifecycle, proof), the play protocol in dm.md, code pointers in
develop.md, numbers in benchlog.

### The open calls, settled

- **The pursue contest's numbers.** `2d6 + the party's best living MIND`
  vs `2d6 + the runners' HP-and-STA-weighted chase DEX`, trackers +2
  (`TRACK_WOUND_BONUS`) if any runner carries a named wound. No DC band
  was invented: making it an OPPOSED roll against the same weighted legs
  the rout was decided by means the fiction is already consistent — the
  thing that outran you is the thing you now have to out-track, and a
  runner too broken to escape is too broken to hide. Best MIND rather
  than a party average because tracking is one person's skill and the
  party has no reason to send its worst tracker.
- **The mop-up formula** stays `wild_encounter_xp(level)` as specced; no
  play evidence yet to argue with it. The level used is the highest
  among the survivors, not the original room's.
- **The 0.20 turn-in share** is unchanged, and the split is implemented
  as encounters (0.40 each) + turn-in (0.20) with the FIELD tranche as
  the arithmetic REMAINDER. That last choice matters: it makes the three
  tranches sum to `quest_xp_total` exactly at every level and encounter
  count, so tuning either share can never silently leak or mint XP
  (pinned by a test over the whole 1-20 x 1-3 grid).
- **Which templates carry `proof`:** nine, about a third of the
  kill-shaped ones, chosen where a bounty token is the natural fiction
  and written into the desc line so the giver says it — Wolves Attack
  (the pelts), Renegade Wizards (the rings), Blighted Beasts, Monster in
  the Mine, Dragon on the Mountain, The Dragon's Tribute, The Giant at
  the Border (heads), The Great Hunt (the hide, which the desc already
  demanded), Hounds in the Factory (the collars). Deliberately NOT
  flagged: every "clear the road / open the pass / destroy the dead"
  job, whose completion condition is the place being usable, not a
  corpse.

### What the build had to decide that the spec did not raise

- **A second rout during a pursuit.** The spec's pursuit fight can end
  in another rout, but not what that does to the record. Settled: the
  loose end RE-ARMS in place — same id, new day, new area, new fled
  state, and `pursue_tried` cleared. A new rout is a new collapse and
  earns its own warm trail; the alternative (one attempt ever) would
  have made the record a dead letter after one failure.
- **Breaking off a pursuit.** `retreat` out of a pursuit fight cannot
  write a fresh loose end (that would breed duplicates of the same
  monster). It updates the existing record to the runners' current state
  and says the chase was broken off.
- **`pursue --stage`.** The spec says cold trails are "the DM's
  territory, fed by the record" and stops there, which leaves the DM
  with a record and no way to spend it. Added: a switch that re-opens a
  fight against any loose end with no warm gate and no tracking roll,
  survivors healed by the days passed (`refresh_foes_after_retreat`, the
  same function the fled-room return trip uses). It is the cold trail's
  ENDING, not a second pursuit mechanic — the finding is still fiction.
- **The proof gate's release.** The spec gates work-done on the final
  roster being dead but does not say what fires the quest when it later
  is. Added `_maybe_finish_proof`: settling the last loose end of a
  proof quest lifts the flag and calls the work-done stage directly (the
  cursor never advanced past the final site). So the bounty completes
  from wherever the kill happens.
- **`_close_site` grew an exemption predicate** rather than four
  branches: `pays_here` is true for war waves, conquest jobs, hell tasks
  and dark work, and those keep the old whole-lump path with BOTH lump
  tranches paid at once. The turn-in path is the new branch, not the
  default — which is why no exempt kind changed behavior by a single XP.

### Where the plan's predictions missed

- **"Hurt-party escape rates staying 90%+" did not hold** (measured
  92.9% -> 66.7% for the troll, 100% -> 38.5% for the bear). The HP
  weighting handicaps the runners regardless of the party's state, so it
  pulls both columns down; the 90%+ case the machinery still guarantees
  is the narrower "no fit pursuers at all" auto-escape. The design goal
  — SEPARATION between a fresh party's escape rate and a spent one's —
  strengthened everywhere (troll 2.2x -> 4.7x), so this was reported
  rather than patched: whether the spent column wants floor support is
  the designer's call, and inventing one now would be tuning against a
  number nobody has felt at the table.
- **The predicted rates were pessimistic for solos and optimistic for
  packs.** Spec: packs 10%->8%, ogre/bear 23%->~0-6%, troll 54%->~33%.
  Measured on `bench_rout.py`'s harness: ogre 54%->18%, bear 37%->10%,
  troll 45%->18% — the solos fell FURTHER than hoped. The level-1
  cutthroat pack, however, measures 68%->44%, nowhere near the "packs
  barely escape" picture; the spec's pack figure came from generated
  at-level rooms (mixed rosters that die from above the band), and three
  same-row humanoids at level 1 are a different animal. Left alone and
  flagged in develop.md as the first dial.
- **The career sim's band split barely moved** (33/53/10/4 against
  34/50/12/3), which is the desired answer to "did widening the windows
  break the clock" and simultaneously a reminder that the sim cannot
  answer it: its careers teleport, so the return leg the widening pays
  for is a leg they never walk. plan.md's travel-layer item now carries
  that note explicitly.

### A note on the harness

The first version of `bench_rout.py` measured the relief-escape by
crippling the party AT THE DOOR (a third of HP, no breath). That reads
sensible and measures nothing: such a duo loses 99%+ of the time, and a
fight the party never won cannot contain an escape from the party. The
readout was rebuilt to split WON fights by how the party ENDED them,
which is the honest form of "does the outcome correlate with the party's
condition". Written down because the broken version looked more like the
spec's wording than the working one does.

### Also in this pass

The `ui/*.txt` pages of a live playthrough had been merged into master
by PRs #79 and #80 — per-game runtime state sitting in the repo as
source. They are untracked again. The pages are still deliberately
committable ON a playthrough's own branch (that is what `sheet` is for,
and .gitignore says so); what must not happen is a game branch carrying
them into master. Nothing was gitignored, since that would break the
documented UI workflow.

## 2026-08-08 (C) — Two travel guards that were never armed

Two bugs in the world layer's travel wiring, both of the same shape: a
rule that reads as shipped in the docs and does nothing at the table.
Neither is a design change — the designs were right, they simply were
not connected. Fixed together because both live in `cmd_travel`'s night
loop and its opening ledger.

### The paid crossing that never survived the fight

`road_paid` (the 2026-08-12 review's fix for the doubled toll) was set on
the state dict and read back off the state dict — and never written to
`save.json`. Its whole reason to exist is the case where the state dict
does not survive: a road fight breaks the leg off, the fight machinery
SAVES, the player re-issues `travel` in a fresh process, and the marker
is gone. So the guard held for exactly the code path that could not
happen and failed for the only one that could. An interrupted trip paid
its toll and walked its washed-out-ford detour again on every re-issue —
the exact bug the marker was added to kill, and no amount of re-reading
`cmd_travel` shows it, because the bug is a key missing from a function
two thousand lines away.

**Shipped:** `road_paid` on the save doc and the load dict, and
`move_party(state, area)` — now the ONE way position moves once a game is
running (the travel arrival, explore's discovery, the teleport). It
stands the party in the area and spends the marker.

**The call the fix had to settle:** whether a marker should expire.
Making it persist made staleness real for the first time — a marker for
A→B that outlives the standing still would hand a free crossing to that
same leg weeks later (teleport away, wander back, cross for free). A day
stamp with a window was considered and rejected as an invented number:
what the marker is actually bound to is the party STANDING at the origin
of a leg it has already paid for, so any move at all is what spends it.
That is a property of the move, not of the calendar, and it belongs in
`move_party` where no future call site can forget it. rules.md says so
in the played register ("one crossing, one charge").

### The four-night leg that was all one night's weather

`exposure_sky` — the sky a night is PAID for — did not roll the world up
to today, alone among the sky readers (`sky_here`, `weather_note`,
`local_term` and `world_news` all do). Travel's night loop asks it once a
night, and `long_rest` advances the day INSIDE that loop, so every night
of a multi-day leg was charged the departure day's weather: one storm at
the gate meant four exposure checks in it, four cabin rolls and four
nights of storm morale, days after the storm had blown out. The cabin
roll came along for free, since `worldsim.storming` is read straight
after and off the same unrolled layer.

**Shipped:** the one `roll_world` call, plus the docstring saying WHY it
is there — the reader's day-scale is the loop's, not the command's.

**Not changed:** the departure-day quote for `travel_delay` and
`road_charges`. Those are a price asked at the gate before the party
walks, and a price is a thing you are quoted now; the nights are a thing
you live through one at a time. Different clocks on purpose.

### The contract

`test_worldsim.py` grows `ThePaidCrossing` (three tests) and one more in
`TheWeatherSessionWiring`. The toll test drives `cmd_travel` twice with
the road fight stubbed at `wild_event` and a REAL `save`/`load` through a
sandboxed `STATE_PATH` in between — an in-memory round trip would have
passed against the broken code, which is the whole lesson of the bug. The
sky test rolls a twin world by hand day by day and demands the reader
agree with it on every one of twelve days, and that the twelve are not
one frozen sky.

## 2026-08-15 — THE ASCII WORLD MAP: the generator built, the location rework opened

The designer asked for a graphical ASCII map as the ground for a big
change to the location system, and supplied the reference himself: a
hand-drawn 30x18 Europe in `.` / `#` / `^` with `~` rivers, plus the
whole geographic contract. One character is 30 km east-west and 60 km
north-south (a character cell is twice as tall as wide, so the map reads
near-isotropic); a day walks one tile east or half a tile south; no
diagonal movement. The full world is rolled large but only a 40x20
northwest corner is the playable game world — one civilisation's view,
the way the reference map is Europe's. Two or three continents carry
most of the land, islands yes but never an archipelago, coasts ragged
the Europe way. The west edge is water down the whole column — visibly
sailable, kept organic, never a straight cut — the north edge may carry
land to the frame, and the east and south edges cut continents mid-body
(his own re-read settled that: continents generate as islands, so the
west needs no special landmass rule beyond the open column). Two
hard local rules: no two ocean tiles touching only at a corner (fix by
drowning land — straits open, inner seas grow), and rivers in
box-drawing glyphs, never `~`, because a tilde cannot say which way a
river runs or bends. A tile will correspond to an AREA; this session
ships the generator and its documentation ONLY — nothing in the game
reads the map yet.

**Shipped:** `worldmap.py` (standalone, stdlib-only, imports nothing
from the game) plus `test_worldmap.py`; rules.md's The World Map add-on
(the geography principles, flagged NOT AT THE TABLE); develop.md's
Files / dev-map / Running registrations; plan.md's "The ASCII world
map" item carrying the hook-up. `python worldmap.py --seed N` is the
eyeball check; `--lift` floats the playable corner out of the full map
with a border of spaces, `--play` prints the corner alone, `--check N`
sweeps constraint pass rates, `--template-stats` re-measures the
embedded reference.

### The algorithm (what was chosen and why)

- **Elevation = plateau continent masks + anisotropy-corrected fractal
  value noise, domain-warped.** Masks are flat-cored domes (flat middle,
  linear rim), so INSIDE a continent the noise decides land against
  water — that is where the Europe-grade bays and inner seas come from —
  while the rim fades the coast out organically. All distances and
  wavelengths run in 30-km units (y doubled), so features are round in
  kilometers, not in characters. Two to three continents (60/40 weighted),
  unequal by design, the first always anchored under the playable corner;
  3-7 small island masks besides.
- **Sea level by percentile, not by constant.** The land/water ratio is
  the template's number, so the cut is simply the elevation percentile
  that yields it (plus slack for the fix-ups that drown tiles). Ratio
  drift is impossible by construction.
- **Fix-ups in proved order.** West column to ocean first; then the
  diagonal-ocean rule, always drowning the lower-elevation shoulder,
  looped to stability (converges: land only shrinks); then the island
  budget (specks beyond eight drown, smallest first). Dropping whole
  components cannot create new diagonal contacts — two components
  corner-touching would themselves be the forbidden pattern, already
  fixed — so the passes compose cleanly.
- **Mountains as ranges walked uphill.** Tournament-picked
  high-elevation starts, 4-9 steps with momentum, occasional flank tile;
  budgeted to the template's mountain share of land. Chains and massifs
  land on continent spines because the walk follows the same field the
  coasts came from.
- **Rivers descend a BFS distance-to-sea field with mountains
  impassable.** Every step goes to a strictly closer tile, so every
  river provably reaches water (sea or inner sea) and no loop is
  possible; bounded sideways meanders and a momentum-then-bend rule
  (straight runs flip to preferring a turn after four tiles) keep them
  from beelining. Touching an existing river joins it — the junction
  becomes a tee. Sources want a mountain foot 4-11 tiles inland;
  spacing from other rivers guarantees the three-tile minimum before a
  merge can happen. Mountains impassable IS the geography rule at this
  scale: a range is a watershed divide, and a `^` tile is a massif, not
  a peak with springs on both slopes.
- **The glyph is the river's connections.** `│ ─` runs, `┌ ┐ └ ┘`
  bends, `├ ┤ ┬ ┴ ┼` junctions, half-line stubs `╵ ╷ ╶ ╴` for sources,
  and a mouth is an arm pointing into a `.` tile. The contract tests
  every link reciprocal and every connection set printable — the
  box-drawing answer to the `#~ / ~#` ambiguity the designer ruled out.
- **Generate-validate-retry.** A rolled map must pass the hard rules
  (west column, diagonal rule, continent shape, ratio bands, the
  playable corner neither empty sea nor wall-to-wall land, river
  grammar). `generate(seed)` walks deterministic sub-attempts until one
  passes: same seed, same world, always.

### The road there (what failed first)

The first working version already hit every ratio, and then the sweep
said a third of worlds rolled ONE landmass. Three lessons, all now in
the knobs:

- **Cover must exceed the land target.** With domes covering 55% of the
  map and the percentile demanding 59.5% land, the cut was FORCED into
  the noise between continents — bridges by construction. Domes now
  cover 68% and the cut stays inside their rims.
- **An overlap penalty is not a strait.** The first anti-bridge term
  keyed on the second-highest MASK — which is zero exactly in the
  channel between two separated continents, so it did nothing once
  separation was raised. The fix is REACH: each continent repels land
  out to 1.35 of its radius, and the trench digs wherever the
  second-highest reach is positive — that is, precisely in the channel.
  Islands are exempt (a Britain may hug one coast) but may not seed in
  the strait between two continents, and may not seed inside a
  continent's core, where they vanished into the mainland and left
  island-less worlds.
- **The corner is a view, so it gets its own band.** The playable
  corner kept rolling 75%+ land (the anchor dome sat square on it). Its
  placement box moved east and south so the anchor's coast rim falls
  inside the view, and validation holds the corner to 0.30-0.72 land.

**Measured** (benchlog carries the runs): the reference map is land
0.585, mountains 0.092 of land, rivers 0.066 of land, zero diagonal
contacts — the designer's own drawing already obeys the rule he asked
for. Rolled worlds: land 0.59, mountains 0.090, rivers 0.066-0.068,
continents 2-3 holding 0.97+ of land. Three hundred seeds swept: zero
unresolved, 54-58% pass on the first roll, mean 1.6-1.75 rolls, worst
seed 7 rolls.

### The calls the spec left open that the build settled

- **80x40 over 60x30** as the default (both asked-about sizes work,
  `--size` picks): at 80x40 the playable corner is a QUARTER of the
  world, so two or three continents genuinely surround it and sailing
  east or south leaves the page long before the world — at 60x30 the
  corner is 44% of the map and the world barely outreaches the view.
  Also 80 columns still fits a terminal.
- **Box glyphs are the one deliberate exception** to the ASCII-output
  convention, recorded in rules.md, develop.md's conventions note, and
  the module head (pipe with UTF-8 on Windows).
- **A river tile is land.** The overlay never changes terrain — "mostly
  land, with the hard-to-cross river", as specified — so the ocean
  rules ignore rivers entirely, and the paid-crossing marker has a
  future home.
- **"2-3 continents, most of the landmass" made checkable:** second
  component at least 10% of land, top three at least 78%, at most 8
  specks under 12 tiles. "Some islands desirable" stayed SOFT (zero
  islands is a legal world; the placement bias makes them common).
- **The playable corner is exactly 40 columns wide** — the display
  width writing.md already enforces; the full map is a dev view and may
  be wider.
- **The lift is a cross,** not a floating panel: the space border runs
  the full width and height, so tiles stay column-aligned across the
  gap and the corner still reads against the rest of the world.
- **A merged mouth is legal.** Two rivers may share an estuary tile
  (the junction tee at the coast); the grammar allows it and the eye
  reads it as a confluence, so no rule forbids it.

Nothing in session.py, places.py, or quests.py moved. The hook-up — a
tile per Area, travel off the grid, the map as the macro display,
worldgen placing settlements ON the map — is plan.md's item, opened
this session with its open calls listed.

## 2026-08-15 (B) — The fixed Europe map replaces the generators

The generated maps did not earn the location-system rework. A second
standalone attempt was reviewed beside the generator from the preceding
commit, and the designer rejected the procedural direction rather than
spending another pass tuning either algorithm. The world geography will
be the supplied Europe-shaped character map, fixed across campaigns.
Nothing was connected to play in this session.

**Shipped:** `resources/europe_map.txt`, the canonical 30x18 map in the
designer's exact `.` / `#` / `^` / `~` vocabulary. The first
generator and its contract moved together to `archive/worldmap.py` and
`archive/test_worldmap.py`; the second received script was preserved
verbatim as `archive/mapgen.py`. Both rejected implementations therefore
remain inspectable and runnable in the repository without presenting
either as the game's worldgen path.

The roadmap's open hook-up item was rewritten around loading the fixed
resource: a tile still becomes an Area, travel still moves on the grid,
and the map still replaces the list-shaped macro display, but geography
no longer consumes a seed or needs generation retries. The rules and dev
index now describe the fixed source; the preceding entry remains the
historical record of what the first experiment tried and measured.

### The calls this change settled

- **The source is literal.** Integration must validate and load the text
  file without normalizing its geography. In particular, its ninth row is
  the designer's supplied `...########~####~######~##~##^`, not the
  slightly different calibration row embedded in the first generator.
- **The archive is live history, not an alternate engine.** The scripts
  remain runnable and the first contract remains beside its code, but no
  game module imports them and no roadmap item offers procedural maps as
  an option.
- **The integration remains a later session.** No Area records,
  settlements, travel rules, discovery state, or UI pages changed here.

## 2026-08-15 (C) — The Europe-map implementation contract

This was a design and planning session only. It settled the fixed map's
location model, population, travel, human cultures, city overlay, quest
radius and staged build before implementation begins. No game behavior
changed.

The designer removed Dvarvengrond, Ensimaa and Gibili and removed dwarves,
elves, goblins and orcs as peoples. Firascir, Mortellaria and Tergal are now
three human countries. Tergal keeps its existing steppe, clan, horse, shaman
and Sky identity; only the biological/species claim is removed. Content
routing therefore moves from race to country/culture and characters retain a
homeland only where nationality has a rule to serve.

The first map-hook proposal said one Tile would be one Area. Discussion
rejected that collapse: the hierarchy becomes Country -> Tile -> Area -> Site
-> Room. A Tile is the travel node and may contain a natural Area beside a
town and villages. Every one of the 540 fixed Tiles receives a natural Area
in the MVP, including sea and famous-city Tiles. River Tiles are ordinary
inhabited land and are themselves riverside; an adjacent 30x60 km Tile is too
far away to inherit that tag. Mountain Tiles may roll villages but not towns.
Sea is navigable and uses the same coordinate country partition as land.

The political split is literal and 1-based: rows 11-18 are Mortellaria;
above them, columns 1-21 are Firascir and 22-30 are Tergal. The fixed terrain
is common knowledge. Ordinary settlement density is seeded and stored as
lightweight slots, with Mortellaria 10/35/55, Firascir 6/24/70 and Tergal
3/17/80 over town-plus-two-villages / one-village / none. Full settlement
records remain lazy. The opening is uniform over settlement slots anywhere
in the world, not over countries or populated Tiles.

Sixteen historical city Tiles were placed by reading the recognizable map
silhouette: Dublin, London, Amsterdam, Paris and Prague in Firascir;
Stockholm, Moscow, Warsaw and Kyiv in Tergal; Lisbon, Madrid, Venice, Rome,
Athens, Constantinople and Carthage in Mortellaria. Paris, Kyiv and Rome are
the three capitals, implemented as towns carrying `capital: true`. Each
historical Tile has the dense three-slot shape; the historical town is known
at world creation and the two villages stay lazy.

The review also recovered Firascir's apparently missing village pool. The
shipped catalog intentionally fixed Sturford, Ackham and Flurham and therefore
stored no generated reserve, but `placegen.md` still held fifteen models:
Sturham, Sturworth, Newton, Midton, Aston, Tomton, Walham, Coldcot, Thornley,
Blackton, Astmoor, Ackbridge, Ackton, Mickleham and Shepham. The new contract
restores them beside the three fixed names. Every country now has separate
town and village reserves and stable numbered placeholders after exhaustion.

Travel is cardinal: one day east/west, two north/south, plus one day on an
edge touching a mountain. Rivers and sea add no surcharge; sea requires no
ship or port system and rolls no random combat in the MVP. Weighted paths are
deterministic and symmetric. An edge completes atomically and an interruption
leaves the party at the Tile reached instead of returning it to the journey's
origin.

Quest knowledge becomes local. Capitals always have ordinary boards, other
towns on a stable 60% roll and villages on 25%; forced quest families may
still post anywhere. Reading a board refreshes and reports known settlements
within three shortest-path days. Ordinary quest targets also stay within
three days, while story and deliveries may explicitly exceed the radius.
Deadlines add the actual outward and return route, and delivery pay reads
actual path days. An empty settlement is a valid result.

The old roadmap was not discarded. It moved intact to
`archive/plan-pre-europe-2026-08-15.md`, marked as a historical snapshot with
no implementation authority. `plan.md` became the sole active contract and
splits the rework into five triggerable sessions: Human World Contraction;
Fixed Europe Geography; Grid Navigation and Map UI; Local Quest Geography;
Europe MVP Closure. Each must ship and be documented independently before the
next begins.

## 2026-08-15 (D) — Human World Contraction shipped

The first Europe-map implementation slice leaves the old list navigation
temporarily runnable but contracts its world to Firascir, Mortellaria and
Tergal. Every person is human. Character, NPC and place records use `homeland`
for cultural origin; the former identity field, its command-line switch, its
stat floors and ceilings, and its trait substitutions were deleted rather
than retained as compatibility data. Firascir and Mortellaria share the
western human personal-name pool. Tergal's existing personal names were kept
and reclassified as names of Tergal humans.

Quest and encounter routing now follows country. Firascir keeps its existing
human quest packet, Mortellaria takes that mechanically neutral human table,
and Tergal keeps its steppe, clan, horse and warband material after removing
species claims. All three use the same calibrated humanoid ladder, so no foe
statistics moved. Service providers, rulers, residents, recruits, law and
Hell posses, conquest defenders, smiths, wild encounters and delivery faces
now receive the settlement's homeland. The gun rows and smith mechanics stay;
the revolver is no longer restricted to one people or one country's shops.

The conquest spine now has exactly three country variants. Firascir carries
the Undead Kingdom, Mortellaria the magic-machine Golden Empire, and Tergal
the human Iron Horde. The aggressor roll selects a country and excludes the
PC's homeland. `story.init_story` gained an explicit aggressor override so all
three complete four-wave variants can be forced by tests and by the story
dump without recasting mismatched faces afterward.

The active world simulation is projected onto the three surviving country
packets. Shared cards have their scopes narrowed, relations require both ends
to survive, unreachable chains are pruned, and keyed state/menu/encounter
tables retain only states active cards can produce. Tergal-facing copy was
humanized. This leaves 104 active cards, eight directed relations, 16 facts
and seven services/options; import validation remains strict. Old packet
literals may remain as source material until the final cleanup session, but
they cannot enter `CARDS`, any keyed runtime catalog, a country deck, or a
player-facing readout.

The permanent regression contract now checks the three homeland sets,
repeated fresh-world people, all twelve forced story waves, absence of the
removed peoples/countries from active catalogs, and the contracted opening
census of 15 natural Areas and nine settlements. The content-only contraction
does not alter combat or progression knobs, so no balance benchmark was
remeasured.

## 2026-08-15 (E) — Fixed Europe Geography shipped

The runtime now loads the authored 30x18 Europe map as the sole geography.
World creation validates all 540 glyphs, the 224/266/29/21 sea/basic/
mountain/river census, the three country totals and the four land-component
sizes. It creates a stable Country -> Tile -> Area -> Site -> Room tree: each
Tile has reciprocal cardinal neighbors and exactly one natural Area, while
settlements are sibling Areas scoped beneath that Tile.

Population is rolled once into lightweight settlement slots. The exact
country density tables apply to non-sea Tiles, ordinary mountain towns are
downgraded to villages, and every historical city has the fixed dense shape.
The sixteen historical towns exist at world creation; Paris, Kyiv and Rome
are ordinary `town` records carrying the explicit `capital: true` flag.
Capital services, rulers, boards, conquest and equipment now read that flag
instead of relying on subtype or creation order.

Ordinary settlement Areas remain lazy, but the census does not. Revealing a
Tile materializes all of its slots; a quest, event or DM request may consume
an unused fitting slot elsewhere. Per-country town and village name reserves
are stably shuffled, and numbered placeholders are deterministic after
exhaustion. Saving and revisiting therefore cannot add, remove, rename or
move a settlement. The catalog's named natural Areas were retired as runtime
geography, but their natural Site definitions remain reusable content pools.

New games choose uniformly from every settlement slot in Europe, then
materialize and reveal that Tile. One combat quest is forced at the party's
exact starting level, and both heroes inherit the settlement's country as
homeland; the `--homeland` override was removed. `world["lands"]` and the
position's `land` field retain their existing internal spelling for the
country record so downstream world-simulation work does not need an unrelated
rename. Direct list-style travel remains temporarily runnable, but arrival
now reveals the destination Tile; weighted grid travel and map UI belong to
the next roadmap session.

The contract suite pins map structure, historical overlays, capital flags,
settlement density, name exhaustion, uniform-start reachability, lazy
persistence and derived homelands. The full 699-test suite passes. No combat,
progression or economy constant moved, so no balance benchmark was rerun.

## 2026-08-15 (F) — Grid Navigation and Map UI shipped

The party now walks the map. Day-scale movement is a walk along cardinal
Tile edges: east/west one day, north/south two, plus one day if either end
is a mountain. River is ordinary inhabited land at this scale and carries no
surcharge, sea carries the directional base and nothing more, and crossing a
country border costs nothing. The mountain rule is deliberately "either
end", which is what makes the whole cost model symmetric — descending a pass
costs exactly what climbing it cost — and shortest-path distance is
therefore symmetric by construction rather than by assertion.

The pathfinder is a deterministic Dijkstra whose frontier is ordered by
(cost, row, column) with strict relaxation, so equal-cost routes settle on
the northernmost-then-westernmost one with no hash or dict order anywhere in
the answer. It lives in `places.py` and takes **Tile IDs, never a world**:
the map is authored and immutable, so distance is geography, not save state,
and single-source results are memoized per origin across every campaign in
the process. Sea is navigable, so the frame is fully connected and all three
small landmasses — the eleven-Tile northern island, Dublin's two-Tile island
and the lone islet — are reachable without ports, ships or passage prices.

`travel north|south|east|west` is the primitive; `travel R09C18` and
`travel NAME` (a known settlement, or a historical city, which is also its
Tile's name) route by the cheapest road and walk it edge by edge. An edge is
atomic: its days pass as camp nights, the world clock and boards run, the
party is PLACED in the Tile it reached, and only then does the road roll.
That order is the whole rework. A fight or a sighting stops a route where it
stands, and the party keeps the ground it walked.

### Calls the spec left open, and how they were settled

- **What counts as a "sea edge".** The spec says sea edges roll no combat
  but does not say whether that is decided by the destination or by either
  endpoint. Settled as **either endpoint**: a passage is a passage in both
  directions, and stepping ashore off a boat is not a road arrival. This
  keeps the encounter rule as symmetric as the cost rule.
- **Where tolls and weather detours are charged.** Per **edge**, not per
  `travel` command. Charging per command would make ten single steps cost
  ten tolls where one long route over the same ground cost one, which is
  both gameable and untrue. The old per-day toll scale is roughly preserved
  because an edge is one to three days.
- **The paid-crossing marker is deleted, not migrated.** `road_paid` existed
  only because an interrupted trip bounced the party back to its origin, so
  the same crossing had to be walked twice and could not honestly be charged
  twice. With mid-route position the premise is gone: no edge is ever walked
  twice, so nothing is ever charged twice. Its save keys went with it, and
  `test_worldsim.ThePaidCrossing` was replaced by `TheRoadCharges`, which
  pins the new contract instead.
- **Where the arrival ceremony runs.** Once, where the party STOPS — not at
  every Tile a route passes through. News, prices, punishment, hell's
  collections and the delivery hand-off at each of ten intermediate
  countryside Tiles would be noise, and "arrival" plainly means the end of
  the journey. Reveal, recovery and the road roll stay per edge.
- **`explore` after `discover_area`.** The Session-2 country-wide "next
  undiscovered Area" sweep is deleted. Exploring is now going afield in
  THIS Tile's countryside; from a settlement the party first walks out into
  the Tile's natural Area, which is free because it is the same map cell.
  Three Sites to a Tile, then the answer is to travel for fresh ground.
- **Sibling Areas.** `go NAME` gained the free step between known Areas of
  one Tile, and `travel NAME` for a place on the current Tile does the same
  and says so. A 30x60 km cell holding a town, its villages and the
  countryside between them cannot charge a day to cross itself.
- **Open water is not wilderness.** Hunting is refused there, a night camped
  at sea draws no visitor, and `explore` rolls no wilds encounter — but the
  weather, exposure and overnight recovery are entirely ordinary.

### What the distance change moved

Everything that used to ask "same land or another?" now asks the map:
`quests.return_leg_days`, `build_delivery_quest`, `session._cast_teleport`
and the hell-task road estimate in `cmd_take`. `TRAVEL_DAYS_IN_LAND` and
`TRAVEL_DAYS_CROSS` are deleted.

**This is a real balance movement in one place and it should be looked at.**
Cross-country deliveries were priced at a flat two days: 40 g and 50 XP.
Measured over eight fresh seeds they are now 15–39 one-way days, paying
300–780 g and 375–975 XP with windows of 37–85 days. The per-day rates
(`DELIVERY_GOLD_PER_DAY` 20, `DELIVERY_XP_PER_DAY` 25) were not touched —
only the distance became honest, and a courier run is now a genuine career
choice rather than a chore. Local Quest Geography owns re-pricing deliveries
by unrestricted cross-country shortest path and is the place to confirm or
adjust the scale. Teleport moved the same way: its Power cost is now real
path days, which puts the far side of Europe out of reach of any pool, as
the spec intended. The career bench has no travel layer, so nothing it
measures moved and no benchmark was rerun.

### The map page

`map` and `ui/map.txt` draw the whole 30x18 grid under a two-line numeric
column axis with two-digit row labels — 33 characters, inside the 40-column
rule, so the map is never windowed. Overlay priority is strict: `@` party,
`!` an active quest objective, `C` a known capital, `T` any other known
town, `v` known village(s) with no known town, then the authored terrain.
No border characters are drawn through the grid; the fixed partition rule
and a by-country legend (historical cities first) carry political geography.
Below the grid sits the current Tile in detail — coordinate, real name,
country, biome, derived ground tags, every known Area with its job count —
the country's state diff, and the taken-quest list with shortest-path days
to each job's next mark. The old list-shaped Land/Area display is gone.
`look` was rebuilt to match: it leads with the TILE, then the Area on it,
then the sibling Areas and the four roads out with their day costs.

`_cast_teleport` also had a latent bug from the previous session: it matched
settlements by key substring, and tile-scoped Area keys (`tile/r09/c18/...`)
no longer contain the settlement's name, so no destination could ever be
found by name. It now matches name or key.

The new `test_navigation.py` pins the edge cost in every case, reciprocity
across all 540 Tiles, path symmetry, five representative distances, the
interrupted route's position across a save, the silent sea, teleport's real
price and the map page's overlay priority, ASCII and 40-column fit. The full
suite is 730 tests and green.

## 2026-08-15 (G) — Local Quest Geography shipped

plan.md's fourth Europe session, built as specified. The one-sentence
version: **work stopped being everywhere.** Before this, every settlement
posted jobs, the player heard about every open job in the whole country,
an ordinary job's target could be anywhere on the map, and its window
priced only the walk home. All four are now local facts measured in
`places.path_days`.

### What shipped

**Sparse ordinary boards.** `places.BOARD_ACTIVE_CHANCE` (capital 1.0 /
town 0.6 / village 0.25) and `board_active_roll`, a stable derived roll off
the SLOT's identity, stamped onto the Area as `board_active` when the slot
materializes. The start settlement is forced active in `create_geography`.
An inactive board has ordinary capacity zero — floor and all — refills to
nothing, and gets nothing at worldgen. Measured over 9000 slot identities:
100 / 56.5 / 23.8.

**Ordinary capacity separated from forced posting.**
`quests.is_ordinary_posting` is the one reader that tells the board's own
generated work from the forced families (delivery, `world_card`,
`story_wave`, `hell_task`, and a plain `forced` for anything later). Card
jobs now post OUTSIDE ordinary capacity instead of consuming it, so an
inactive board still hears everything the world forces onto it and never
becomes an active board by receiving it. `board_forecast` counts the forced
work straight and forecasts only the ordinary rest.

**The three-day rumor radius.** `quests.nearby_settlements` (known,
materialized, within `QUEST_RUMOR_DAYS` of a Tile, ordered
nearest-then-Tile-then-key) replaced the land-wide rumor rule everywhere:
`session.board_clock` refreshes and expires only those boards,
`refresh_deliveries` takes the same list as its origins, and `cmd_board`
prints `quests.rumor_lines` — the 1/2/3-day groups, empty ones omitted,
each remote row naming the settlement, its Tile and the days.

**The ordinary target radius.** `_select_quest_area(radius=)`, defaulting
to `ORDINARY_TARGET_DAYS` = 3, threaded through `build_quest(radius=)`.
Candidates are filtered by path days and sorted into stable Tile/Area order
BEFORE the quest's rng picks, so placement is deterministic off the seed.

**The whole road inside the window.** `return_leg_days` became
`route_days`: the ordered walk out through every Site in cursor order and
home again. A one-Site job therefore buys twice its distance — the doctrine
deliveries have carried since they shipped — and a two-Site job whose Sites
sit on opposite sides of the origin buys the detour between them.

Deliveries needed nothing: they were already priced and clocked off
`path_days` by the previous session. What they gained is the explicit
statement, in rules.md and in the suite, that their destinations are the
deliberate exception to the target radius.

### The calls the spec left open

- **Tag compatibility is never traded for the radius.** The spec said both
  "compatible Areas within three days" and "do not route a coast quest to
  generic inland ground merely to satisfy the radius", which conflict
  whenever nothing compatible stands within reach. Settled the way the spec
  named its own fallback: when the compatible set inside the radius is
  empty, the target is the ORIGIN Tile's natural Area, full stop — never
  incompatible ground that merely happens to be close, and never a
  compatible Area outside the radius. The old same-land-then-anywhere
  ladder is deleted.
- **World-card jobs keep the ordinary radius.** The spec listed
  "specifically authored world events" among the families that MAY override
  it. A card's job is a settlement's own crisis and belongs within walking
  distance of it, so `_post_card_quest` passes `radius=ORDINARY_TARGET_DAYS`
  EXPLICITLY rather than inheriting it — a forced family that wants the map
  has to say so. Only the capacity rule is lifted for a card, not the
  geography.
- **Hell's assignments keep the ordinary radius too, by choice.**
  `karma.roll_dark_quest` takes `radius=ORDINARY_TARGET_DAYS` and callers
  may lift it. Work whispered to you where you stand is local work, and the
  pact's own clock (`TASK_WINDOW_DAYS` plus the road days measured at
  `take`) assumes a target the party can walk to inside a window. An
  unrestricted hell job would routinely sit twenty-five days out.
- **`HERE` is the whole Tile, not the Area.** Switching between Areas of
  one Tile is free, so a sibling village's board is as available as the one
  the party stands in. `cmd_board` prints `board_lines` for every
  0-day settlement, not just the local one — which matters more than it
  sounds, because `reveal_tile` materializes all three slots of a Tile at
  once, so same-Tile siblings are the common case at a dense Tile.
- **A DM-authored settlement (`quests.new_area`) opens active.** The roll
  is for the world's own villages; a settlement the DM created by hand
  exists because he wanted work to happen there.
- **The career sim deliberately ignores the rumor radius.** It has no
  travel layer and no position, so a radius around it is meaningless. It
  DOES see the sparse boards. Its docstring now says so, and benchlog reads
  its board numbers as an upper bound on the played supply.

### What this found and did not fix

**The terrain vocabulary does not meet the map.** The quest tables ask for
`forest` / `hills` / `prairie` / `pasture` / `farmland` / `road`; a natural
Area's tags are its Tile's, which since the fixed map are `basic` /
`river` / `mountain` / `sea` plus `coast` / `riverside` / `mountain-foot` /
`border` / `island`. Only `coast` intersects, so outside the settlement
Areas (which carry rich template tags of their own) the compatible set
inside three days is usually empty and the origin-Tile fallback takes it.
Every job is still legal, close and playable — the radius rule is simply
doing less routing than it could.

This was NOT fixed here, deliberately. plan.md defers `basic` sub-biomes
until after the MVP is played, and inventing `forest`/`farmland` tags for
`basic` Tiles now would pre-empt that design. Even the near-miss between
the `mountain` biome tag and the tables' `mountains` was left alone rather
than aliased, because the honest fix is one reconciliation of both
vocabularies, not a patch. It is parked in plan.md's deferred list under
the sub-biome entry.

### Verification

Full suite 787 tests, green. `test_quest_geography.py` is the new contract
suite (56 tests, six parts — the activity roll and its rates, the shut
board, the five forced families reaching one, the rumor radius on a seed
chosen for having both a populated and an empty group, the target radius
across a twelve-seed sweep, the path-priced clock over local / one-Tile /
mountain / sea / multi-Site routes, and the opening quest). Three existing
suites were updated deliberately rather than shimmed: `test_places.py`'s
two routing contracts now measure the CONTENT claim with `radius=None`
(the new-rule half moved to the new suite), `test_turnin.py`'s return-leg
class became the road-inside-the-window class, and `test_worldsim.py`'s
band/slot test forces its town's board active plus five hand-built
positions became legal `session._area_position` records.

`bench_quests --part career` re-measured at 300 careers (benchlog): the
board supply fell 22% and both starvation guards held — zero exhausted
boards, zero forced-up picks, 51 open jobs standing at the median career's
end. Nothing was tuned.

---

## 2026-08-15 — Europe MVP Closure (the fifth and last Europe session)

The Europe rework's closing session: delete the scaffolding four staged
sessions left behind, audit what a player can actually read, tighten the
validation, reshape the tests around the model rather than the migration,
and prove the whole loop in a played game. plan.md's Europe contract is
emptied by this entry.

### What the closure found

**The contraction had never actually happened.** The Human World
Contraction session shipped by FILTERING: `worldsim.py` still held the
Ensimaa, Dvarvengrond and Gibili packets in full, and five comprehension
filters plus `_surviving_cards` and `_prune_unreachable_cards` cut them
out at import. About 1500 lines of cards, factions, constitutions,
tensions, relations, facts, options and state vocabulary for three
countries that do not exist, and — worse — a `validate_content` that was
policing a catalog somebody else had already cleaned behind its back.

**The place catalog was still the old world's geography, working as a
template source.** This was the find of the session and it is the one a
player would have hit in the first hour. `place_catalog.json` kept the
six-Land census — eight named Firascir settlements, four Mortellarian,
four Tergal — and `_settlement_template` used those records as templates
while `materialize_slot` overwrote only the NAME. So a generated Firascir
town called Tomburgh was cut from the Walhaven record and came out
containing a WALHAVEN SMITHY. Warsaw described itself as guarding "the
Flumenpur crossing" with "traders from Caelum" camped outside its western
wall — a river and a country the map does not have. Dublin and Amsterdam
shared a description word for word. Every ordinary settlement in Europe
carried one of sixteen descriptions asserting a geography that had been
deleted a session earlier.

**The conquest variants were on the wrong countries.** plan.md's contract
says Firascir is the Golden Empire and Mortellaria the Undead Kingdom;
`story.py` and `rules.md` both had the first two swapped. The tiebreak is
not the contract but the world layer: Mortellaria owns the death rite, the
tomb cults, `necromancy-open` and the academy's necromancers, and
Firascir's own religion cards are the ACCUSATIONS made against that rite.
A deathless Firascir contradicts its own deck. Fixed to the contract.

### What shipped

**worldsim.py lost 1526 lines and gained a contract.** The three packets
are physically gone — 56 cards, 22 factions, three constitution tables,
three tension tables, their standing tensions, 22 faction edges, 14
relations, 10 facts, 5 options and 62 words of state vocabulary — and so
are the filters, so import-time validation is now the only thing between
the file and a bad row. Proof the cut was surgical: the live catalog was
snapshotted before and after, and every surviving record is identical.

Three cards were rescued rather than deleted, because their scope was
land-specific by accident rather than by identity. `weather/wildfire` and
`weather/green-again` — the drought's own consequence and the scar that
outlives it — become ANY_LAND: every surviving country has woods and a dry
summer, and the drought card that feeds them already was. `weather/smog`
moved to Firascir as the close-built northern town's own hearth and forge
smoke, reworded off its mill origins; it is the SOLE producer of `smog`,
which is the one sky a roof does not keep out (`rpg.INDOOR_SKY`), so
deleting it would have orphaned a shipped engine mechanic and the
exposure rule that reads it. It fired in the smoke game on day 9, which is
how we know.

`firascir/franchise` was deleted instead: its producer was a Gibili
relation, so `_prune_unreachable_cards` had been silently dropping it
since the contraction. Live catalog: **107 cards** (was 104 with three
rescues and one deletion), 8 relations, 16 facts, 7 options, 27 faction
edges, 26 factions (was 48).

**The catalog became content.** `place_catalog.json` is restructured
around `settlement_templates`: a role per settlement kind, each with its
tier, the Tile tags it `fits`, its own tags, a description and its
required Sites. The whole fixed census is gone. Nothing in the file now
names a position, a river, a region or a neighbouring country — a
template's description has to be true of every Tile its `fits` admits,
because it will be read at all of them. Site names lost the proper nouns
they carried (TOMBURGH SMITHY -> TOWN SMITHY, FLUMENPUR BRIDGE -> RIVER
BRIDGE, CAELUM ROAD -> WEST ROAD), and CITY HALL became TOWN HALL, there
being no city subtype.

**`_settlement_template` chooses by fit**, which plan.md asked for
("a generated settlement chooses a fitting country/tier role
deterministically") and the staged build had never wired: only roles whose
`fits` tags the Tile carries are in the draw, and a Tile that fits none
draws from the roles that ask for nothing — which is why
`validate_catalog` now requires each country to keep one of those per
tier. The pick stays `slot["seed"] % n`, so it is stable across
materialization and the save.

**Validation says the contract out loud.** `places.validate_world` runs at
the end of `create_geography` and asserts plan.md's cross-cutting
invariants: the row-major 540-Tile frame, a natural Area and a real
country on every Tile, reciprocal cardinal links with no diagonals and
nothing off-frame, no settlement at sea, no ordinary town on a mountain,
each historical Tile carrying its declared country, biome and its one
authored town, unique slot ids registered on both their Tile and their
country, exactly Paris/Rome/Kyiv flagged capital, and a start that is a
materialized slot. `validate_catalog` grew the schema half: the old census
must be gone, every tier covered, exactly one capital role, real Tile
tags, no `city` anywhere. `worldsim._validate_three_countries` replaces
the discipline the import filter used to provide by accident — every
country owes a card on every track, standing lore, a relation that reaches
it, and an environment profile to roll a sky from.

**Dead branches.** `quests.NAME_PARTS` / `_settlement_name` (the old
fragment-assembled naming), `places.area_id` / `CULTURE_PROFILES` /
`MAP_OVERLAY_PRIORITY` / `OPPOSITE_DIRECTION`, worldsim's three orphaned
authority hooks, `_ELF_TOUGHS` / `_GOBLIN_TOUGHS` (`_DWARF_TOUGHS` became
`_GUNHANDS`, still used by `firascir/silver-vein`), and `places._room_pool`'s
"human yard" matcher. `session.py`'s save readers stopped defaulting nine
keys the writer always emits — the project has no save compatibility, so a
save missing `wounds` is damaged, not old, and should raise.

**Tests describe the model.** `HumanWorldContractionTests` became
`TheThreeHumanCountries`; `test_catalog_no_longer_owns_world_adjacency`
became `test_the_map_owns_geography_and_the_catalog_owns_content`. New:
templates fit their Tiles across a four-seed sweep with every role
reached, that choice surviving a save, one broken world per clause of
`validate_world`, each country waging the war its own packet supports (the
assertion that would have caught the swapped variants), and the
removed-peoples sweep widened from twelve catalogs to twenty-three plus a
whole built and walked-into world plus the play-facing documents. 794
tests, green.

### The calls this session had to settle

- **The exclusive-slot frame stays, empty.** Both authored `STATE_SLOTS`
  entries — the standing of a land's foreigners, the stage of its ore
  deposits — belonged wholly to deleted countries. Re-homing the deposit
  chain to Firascir was considered and rejected twice over: its gate is a
  Dvarvengrond politics tension Firascir does not have, and
  `firascir/silver-vein` already tells the found-seam story there. Deleting
  the frame was rejected too — it is a shipped world-layer mechanic and
  this session's invariants forbid changing one. So the table is empty, the
  machinery and its validation stand, and `test_worldsim`'s guard now pins
  the emptiness and says why, so it is not a silently vacuous test.
- **`_CROWNED` stays a named tuple** although it is now all three
  countries, so a later crownless country reads as an exception rather
  than a silent inclusion.
- **The spec companions are not rewritten.** `placegen.md` and
  `worldsim.md` still describe six Lands and four removed peoples. Both
  gained a HISTORICAL banner saying which parts are no longer the game and
  which method still holds; neither was edited to match the present,
  because project history is not edited. They are the only files the
  removed-peoples test deliberately does not sweep.
- **"City" is a fiction word, not a subtype.** The map legend still groups
  historical towns as "cities" and the world layer's Mortellarian cards
  still say "the city watch", because plan.md itself calls Rome and
  Constantinople historical cities. What was removed is the `city` SUBTYPE
  and every assertion that a generated settlement is one — the war heralds
  now evacuate the capital, and `validate_catalog` rejects a `city` tier
  or tag.

### The MVP smoke game

Seed 4242, level 2, played from `new` to a total party wipe on day 29,
covering every item under plan.md's Goal and MVP proof.

The random start was **Leehaven, a Firascir town on R09C15** — a
coordinate Tile with a town and two villages on it, both villages posting
nothing (the sparse-board roll). `map` drew the whole 30x18 grid at 33
columns with the party, the terrain, the known cities and the Tile detail.
The opening quest's target sat at **Prague, three days east**: the party
walked basic -> river -> basic at one day an edge, cleared two rooms at
the tollhouse road, walked home and turned in on day 7, inside a window
the road was priced into. `go Sturworth` crossed to a sibling Area for no
day; `explore` turned up a WOODCUTTER'S CAMP in the countryside. Two
`travel north` legs put the party **on open water at R07C15**, and a later
run west crossed the sea at R08C05 onto the **island** London stands on —
both landmasses walked, not asserted. The re-homed smog card fired in
Firascir and moved the healer's fee. Save and reload left tiles, slots,
areas, sites, rooms, name reserves and both start keys byte-identical, and
`validate_world` passes on the played save. A sweep of that save for
removed peoples returns nothing.

The rumor radius wanted a world with something to hear, so it was read on
seed 19 (the seed `test_quest_geography` already uses): from **Shepham**,
Dublin two days off posts a job and is heard, London three days off is in
earshot but has a shut board and is correctly silent, and nothing beyond
three days appears at all.

### Two notes for the designer, from the chair

**The template system will repeat itself, and that is not a bug to fix in
code.** Leehaven and Prague are both `market_town` and read the same
sentence. With four town roles and five village roles a country, any world
with twenty settlements will double up. The DM narrating over it is the
intended answer; if it ever grates, the cheap fix is more roles per
country, not a generator.

**A companion quitting mid-career is close to a death sentence now.**
Rowan quit at Leehaven on day 7 with the PC at HP ceiling 5 and six
wounds, and the solo leg that followed met a dire-wolf pack and ended the
run. That is the wound track and the satisfaction track both working as
designed, but the fixed map made the consequence much sharper: the road is
now genuinely long, so "walk somewhere and recruit" costs a dozen days a
wounded PC does not have. Worth watching in play before touching anything.

---

## 2026-08-15 — Post-build review of the Europe five (fixes)

**Where it started.** A read-over of the five shipped Europe commits
against the contract they were built from: did the build follow the plan,
is it complete, is it sound. The answer was yes on almost everything —
the pinned census, the components, the city table, the name pools, the
edge-cost model and the two radii all re-derive from the raw map and the
plan text, 794 tests pass, and a fresh smoke game plays the loop. Four
things did not survive the read.

**The DM's forged job was counted as the board's own work.**
`is_ordinary_posting` has exempted the forged family since Local Quest
Geography, keyed on `quest["forced"]` — and nothing ever set that key.
`forge_quest` built its dict without it, so the flag was unreachable and
the only test covering it fed a hand-written `{"forced": True}` the
builder never produced. Two things broke in play: a forged job at a shut
board vanished from `board_forecast` (the forecast clamps ordinary work
to a capacity of zero), and a forged job at an open board ate one of that
board's generated slots. One line in `forge_quest`, plus a test that
takes its quest from the builder instead of a literal.

**The relations table was a third of its contract.** The Human World
Contraction spec named eight export lines — Firascir grain and timber,
Mortellaria coin, luxury and southern trade, Tergal horses, livestock and
military service. Only the granary was ever rebuilt: the edges carrying
the other seven all pointed at deleted countries and were dropped rather
than re-homed, and nothing caught it, because the validator only asks that
some relation reach each land and the test pinned a bare `len(RELATIONS)
== 8`. The six missing edges are now authored off states their seller
already holds (`forest-law`, `paper-worthless`, `salt-revolt`,
`herd-loss`, `mourning-war`...), each deriving a new priced word, so every
one is felt on a shelf rather than merely present in a table. Luxury goods
and the southern road are deliberately ONE edge: they are one flow, and a
second state saying the same thing would be content for the count's sake.
**The count assertion is replaced by a coverage assertion** — the table is
now tested against what each land SELLS, which is the thing the spec
actually said.

**A passage paid the road's price.** Both halves of `_road_costs` are
land — the ford that is out and the toll-men at the bridge — and a sea leg
ran them anyway, so a mid-ocean crossing could be charged gold at a bridge
that is not there. Sea legs now skip it; the passage's weather is the
nights themselves, which is all the MVP asked for.

**`travel` matched too loosely.** Any known Area whose name merely
CONTAINED the query could answer to it, and Tile names are coordinates
that contain each other (`R09C1` is inside both `R09C10` and `R09C18`).
The whole name — exact on name, key or slug — now wins outright, and the
substring pass only runs when nothing answered to its full name.

**Also swept:** `quests.land_areas` was the one lenient reader left (an
unknown country returned `[]` instead of raising); the species sweep's
regex said `orcen` where it meant `orcish`; develop.md's places.py entry
still listed `OPPOSITE_DIRECTION` and `MAP_OVERLAY_PRIORITY` as live
twenty lines above its own note that they were deleted; and the density
table lived only in code, so rules.md now carries it beside the board
rates it already had.

**What this says about the build.** Every one of the four real defects sat
behind a test that was green — a flag tested through a literal, a table
tested by length, a cost path tested only on land, a matcher tested only
with whole names. The lesson worth keeping: **assert the contract, not the
shape.** A test that counts is a test that will pass while the thing it
counts is wrong.

## 2026-08-20 — The tile economy arc: planning the plan

**Where it started.** The Europe MVP is built and plan.md said the honest
next input is play — but the designer opened the next thread instead, and
named the mode on purpose: a LOOSER one, where indulging in simulation is
trusted to be good for the game and does not have to justify itself
feature by feature or ship fast. The want: deeper simulation of
geography, climate, resources and economy on the tile map. The
inspiration: researching the Firascir and Mortellaria economy and
politics cards had shown that the historical middle ages offer simple,
dramatic, formalizable dynamics — scarcity causing wars, overtaxation,
crime, banditry, revolts — and the tile map should carry them.

**The road the discussion took.** The first framing pass observed that
the dramatic dynamics are already formalized — the card/state/relation
machinery at country level IS the scarcity-to-revolt engine — and what
the country layer lacks is an ADDRESS, so the tile layer's job is to give
the existing dynamics geography rather than to build a second simulation
beside them. It proposed thinking in three economic shapes (flows that
fail, stocks that deplete, networks that get robbed), keeping value as
words rather than a stored score, and history over EU4-likes as the
content source (though EU4's one-trade-good-word-per-province is the
representation lesson). The designer zoomed out and corrected the frame
in four ways that stuck. One: population per tile is the interesting
quantity — the current rolled settlement-slot census is scaffolding, and
the chain should run geography → climate → agriculture → population →
census. Two: this is GENERATION, not simulation — roll the world by law
at worldgen, keep almost nothing running after; the event pulse stays
the part that lives forward. Three: the campaign year is spring to
autumn (about level 20 at half a year of played time), winter is out of
scope as played time and exists only as rolls — so the product is a
SPRING SNAPSHOT, and spring is the hungry gap, the point where last
year's harvest is most felt. Four: trouble should come as organic spots
in every country — never everything-everywhere, never one needle —
which is a spatial-correlation problem (multi-scale rolls; margins
amplify variance; trouble = shortfall × pressure ÷ access; state reach
siting tax squeeze near the crown and banditry far from it).

**What was decided.** The next work is THE TILE ECONOMY ARC — climate,
terrain, economy, population — planned as DESIGN rounds whose output is
settled specs (vocabularies, laws, tables, numbers) with implementation
trivial afterward. Five rounds, now Part 1 of plan.md: climate by law
(each tile a computed climate property; absorbs the deferred
tile-weather item; the Africa stripe authored as a river-fed, high-yield
LOW-VARIANCE granary), terrain and potential (author the physical,
derive the human — farmland is population's footprint via a
deforestation law; herding is the complement where arable potential is
low, not a second authored layer; absorbs the deferred sub-biome item
and the quest-vocabulary reconciliation), population and the census
(hidden numbers, transport bonus, penalties, calibration by RETRODICTION
against the authored historical towns, a census table with zero as a
real tier — replacing the slot census, no compatibility), resources and
routes (mines authored semi-historically and few, with the parked
deposit slot returning to service; trade goods sparse and authored with
the exotics kept off-map so the legendary routes matter; ordinary routes
computed by the pathfinder between surplus and populous regions, the
silk road and the sea lane authored at the frame edges), and the hookup
(the read surface — deliberately the vaguest round). The snapshot and
trouble arc, politics with MORE COUNTRIES (a viking/pirate-analogue
raider culture; Tergal as an aggressor), fantasy/magic, and a
settlements-revisited round went to Part 2 as the draft roadmap. The era
anchor is leaning **about 1500 without the age of exploration** —
the Europe frame argues against colonial dynamics, and higher technology
is heaven/hell/magic, not a tech line; pre-Columbus trade (silk roads,
the spice entrepôt monopoly, Hanse north, wool-cloth west, gold from
the south) is the model for what enters at the frame edges.

**Parked on the way**: the past-epidemic population scar (round 3's
entry), generated region names (take if cheap), and the wealth-band
question — whether the land's 2d6 becomes the aggregate of its tiles'
spring — which belongs to the snapshot arc.

**Calls the rounds will have to settle**, recorded so they are not lost:
the climate vocabulary and the numbers each word carries (the variance
column is what the snapshot arc rolls against); whether the Africa
stripe's river is authored into `resources/europe_map.txt` itself (row
18 is plain `#` today); the deforestation law's exact form (the proposal
on the table: two passes — provisional population off raw potential,
clearance off that population); the population scale anchor (what a
number means, the village/town/city thresholds); the census table's
exact bands; the mine and trade-good lists; the sea-leg route rule; and
round 5's storage question (overlay resources beside the map vs computed
tables in `places.py`). The arc's standing rules — hidden numbers
visible words, author-the-physical derive-the-human, derived seeds
throughout, validate-where-made, the render-script eyeball from round 1
— are written at the head of plan.md's Part 1.

## 2026-08-21 — Round 1 of the tile economy arc: climate, the sky, the last harvest

**Where it started.** The designer opened round 1 with a redrawn map
(Denmark added, Scandinavia adjusted to it, the seaside rivers cut for
looks), a proposed climate list, and the round's fundamental questions:
climate vs biome, whether either can be computed from a 30x18 map,
per-tile attributes vs a label, and which food-production factors the
round owes as numbers. A second sitting brought the harvest question
forward from the snapshot arc and closed the round.

**The map redraw** shipped first as ordinary dev work: new pinned
censuses (basic 268 / mountain 28 / river 18 / sea 226, mainland 300),
and three calls the drawing forced — Amsterdam FOLLOWED THE RHINE to
R08C11 to stay a river city (the pinned Amsterdam–Paris distance is now
3), Lisbon and Venice became basic tiles with their rivers, the
interrupted-route contract in test_navigation now computes its expected
stop as the first LAND-leg tile (the sea rolls no encounter — the rule
was already law, the test had assumed an inland start), and the one-day
rumor fixture moved from seed 37 to seed 28 (Solavela, Madrid one day
off) when the slot set shifted the uniform start draw.

**The road the discussion took.** Plan.md's round-1 entry said climate
by LAW; the designer reversed it — the map is too coarse for first
principles, hand-paint instead — and the reversal kept the plan's
spirit by DEMOTING THE LAW TO A LINT: the overlay is authored, the
tool checks what a rule can state (painted iff land, alpine iff
mountain, the census). Climate vs biome resolved as one merged zonal
vocabulary (the list freely mixes true climates and biomes; round 2's
terrain overlay carries within-climate texture, so a taiga tile with
cleared farmland is legal — that is southern-taiga agriculture, no
label bending). Per-tile climate attributes were REJECTED in favor of
label columns plus a latitude gradient (+8 frost-free days per row
south, clamped) — individual tile character enters at round 2 (soil,
alluvium, exceptions), not in the sky. The designer's three food
factors (growing season, precipitation reliability, winter severity)
became authored label columns: reliability is the interesting one, and
it ended as the harvest layer's tables rather than an abstract
variance number. The mediterranean split in two — the medieval DRY
European one and the Roman Warm WET southern shore — and Egypt got its
own tenth label, `nile` (highest yield, no winter; its granary reads
in the climate layer without authoring the river into the base map).
The sky gained a season CALENDAR, not a track: day 1 = April 1,
spring/summer/autumn/winter at 60/90/60/150, autumn reusing spring's
weights, `season_of(day)` a lookup nothing else reads; weights are per
climate x season and the day roll reads the party's current tile. The
per-tile-weather worry dissolved on inspection: last year's harvest is
history at worldgen and never counted rain days, this year's is
unwritten and the sky is its STORY — so the label is enough, and the
drought machinery stays the bridge.

**The second sitting: the last harvest.** The designer separated what
he had been conflating — population reads the label's averages (round
3, static, per-climate is fine); the CRISIS layer is a separate seeded
per-playthrough roll, and climate-wide uniformity is unacceptable
there while checkerboard noise is worse. His two-pass sketch (seed
problem spots low, reroll neighbours high) became SEEDED CONTAGION,
built and tuned in econmap.py the same day: 4-6 regions, centers
weighted to failure-prone climates, each region drawing a CAUSE from
its center's climate — drought, THE GREAT RAINS (the 1315 famine,
promoted to a first-class cause), frost; the Nile's only failure is
the bad flood — growth gated by cause-vs-climate susceptibility so a
drought sweeps the steppe and dies at the oceanic border, severity
deepest at the core. Scale: 100 = a full excellent harvest (110-120
legendary, below 35 apocalyptic, problem < 75). Measured over 500
seeds: 17.2% mean problem coverage (min 3, max 35), mean region 11
tiles, drought guaranteed always. Two postures were named and
guaranteed: NO WORLD IS A GOOD YEAR EVERYWHERE (a drought region
always exists), and the campaign USUALLY OPENS IN OR BESIDE A BAD
YEAR — raw rolls put trouble within 6 days of the start in only ~52%
of worlds, so the contract adds the nearby-trouble nudge (relocate one
region into 5 days of the start with chance 3 in 4 when none is
there), lifting it to ~88% while keeping the quiet start possible.
Harvest DATES were pulled early per climate (mediterranean ~day 50,
continental ~100, taiga ~125) under the designer's bring-forward
principle, stated generally: **the game is static in time, so
chronological difference becomes regional difference** — true for
harvests now, for technology later.

**What was decided** is plan.md's Round 1 implementation contract,
replacing the design entry: climate loaded onto tiles with
validate_world clauses and a pinned census; CLIMATE_PROFILES replacing
ENVIRONMENT_PROFILES (the five old profiles and the catalog
environment key acknowledged as scaffolding); the label table with the
gradient; the seasonal sky off the party's tile; the harvest roll into
worldgen with derived seeds, tiles and region records stored, the two
guarantees, and the distribution pinned by test. econmap.py's
constants are the contract's numbers. Part 2's snapshot arc was
updated: it keeps the last-WINTER roll (pastoral, reading the winter
column, with the great-rains regions doubling as murrain country), the
reading of both rolls, and the harvest-day consequences.

**Parked on the way**: the causes' fiction names (writing.md register,
with their first read surface); a small population discount for
high-variance climates in round 3 (carrying capacity is set by the bad
years); whether the wet/dry spell counters ever move off the land
layer (kept there — a party crossing a climate border keeps the
land's spell, good enough at this scale).

## 2026-08-21 (B) — Round 2 of the tile economy arc: terrain & the land's potential

**Where it started.** The designer opened round 2 with directives and a
hands-off mandate — decide and present everything not mentioned. Given:
where it is not mountainous the land should be about half hilly and half
plains, both staying `#` on the basic map; hills hand-placed at Scotland,
dry-and-hilly Spain, the Apennines and the Balkans; marshes hand-placed
at the Pripet, the Low Countries and the Fens (for flavor); and the
question whether northernmost Scotland should be a mountain tile.

**The map flip.** Northern Scotland — yes. R03C04 is a dead-end tip (sea
on three sides), so no pinned route crosses it; the flip is one glyph,
the climate letter `o`→`a`, and the census pins (basic 267 / mountain
29; firascir 79/11; climate o 28 / a 29 — round 1's contract updated in
place, since it has not shipped yet). Every map-facing suite passed
unchanged: no slot fixture shifted. Britain gains its one wilderness
massif — the Highlands.

**The vocabulary: relief only, forest derived.** Plan.md's round entry
said the authored overlay is "forest, hills, marsh"; the round reversed
the forest part the way round 1 reversed climate-by-law. At ~1500 the
wildwood is wherever people are not — authoring it per tile would be
authoring the OUTPUT of the deforestation law the same round defines.
So the overlay (`resources/europe_terrain.txt`, letters p/h/w/m) is
relief and drainage only — plains, hills, marsh, mountains pinned to the
`^` tiles by lint — and forest falls out of climate (the wildwood cap)
minus clearance. Hand-authored exceptions stay possible but none proved
necessary: the eyeball showed deep forest exactly where wanted (the
whole taiga north, 42 tiles) without any.

**The half-half prior vs. the drawn geography.** Painted by real
geography — Grampians, Pennines, Meseta, Massif Central, the German
Mittelgebirge belt, Bohemia's rim, Apennine flanks, the Balkan interior,
Anatolia, the shield uplands, the Rif — hills land at 67 tiles, 24% of
the open land, not half. The map's eastern half is the great plain and
its southern stripe is desert; painting half of THAT hilly would lie
about the North European Plain, the black-earth steppe and the Sahara.
In the settled west and the Mediterranean the mix does approach
half-and-half, which is likely the intuition's origin. The census is
pinned at the drawn numbers; pushing toward a hillier world is a
re-paint away if the played feel wants it.

**The marsh five.** The three given, sited: the Fens R06C06, the Low
Countries delta R08C11 (Amsterdam's own river tile — Holland IS the
marsh, and the lint therefore allows marsh over `~`), and the Pripet as
a pair R09C23+R09C24 at the river junction, the map's one great
wilderness marsh. One added: the Danube delta R11C24, the river's last
tile before the Black Sea. Marsh takes no alluvial bonus — it IS the
undrained floodplain — and carries half wildwood (carr and fen scrub).

**The laws, built and tuned in econmap.py.** Arable potential = climate
fraction × terrain fraction (+0.12 alluvial on rivers), wheat = arable ×
round 1's yield column × the ffd gradient; the two-pass deforestation
proposal collapsed to a closed form — clearance = wheat/(wheat+0.2) —
because the provisional population it wanted is itself a function of
potential wheat, so the middle variable cancels; realized arable =
arable × clearance; forest = wildwood × (1−clearance); pastoral index =
climate graze × terrain graze, no hand-picking (the steppe, the med
hills — the Mesta — and the alpine summer pastures all read pastoral by
law alone). Two hand mechanisms, both seeded minimally: HAND_MARKS
({(11,19): pasture} — the middle Danube's horse country) and
HAND_ALLUVIAL (the Po plain tiles, whose lagoon river the 2026-08-21
redraw cut for looks; without it Italy's richest farmland read as
ordinary med country — the one place the rule read wrong against
history). Measured: realized arable mean 0.25, the granaries ranked
Nile 0.73, Danube corridor ~0.6, Rhineland ~0.6, Paris basin ~0.5,
Po 0.44; farmland 132 tiles, pasture 112, forest 97, cover open 217 /
wooded 55 / deep forest 42.

**The quest-vocabulary audit** found the reconciliation is not cosmetic:
natural Areas today carry only `basic`/`mountain`/`river` (+the
positional tags), so the quest tables' `forest` / `hills` / `prairie` /
`pasture` / `farmland` match NO natural Area — every such job silently
falls back to the origin tile's countryside — and Firascir's `fields`
site inventory is dead data because one-template-per-biome always picks
`old_forest`. The contract therefore rewires Area tags to the terrain +
derived words, renames `prairie`→`steppe` (the climate layer's word),
settles `mountains` as the one word for high ground outside the glyph
key (retiring the mountain/mountains near-miss), extends the fit
vocabulary past coast/riverside/mountain-foot to character words, and
selects natural templates by terrain + cover.

**Decided against, on purpose**: hills costing travel days (the edge
model is settled and symmetric; every pinned distance survives), a marsh
glyph on the basic map (the designer's directive — hills and plains both
stay `#`; the character shows in detail lines when round 5 builds them),
terrain entering the harvest contagion (climate granularity is the
model), and terrain entering the sky.

**What was decided** is plan.md's Round 2 implementation contract,
replacing the design entry: terrain loaded onto tiles with lint clauses
and the pinned census, the laws into places.py with stored words and
hidden numbers, the tag reconciliation with its pinned censuses, area
naming and natural-template selection by character, the fit-tag
extension, and the end-to-end tests. econmap.py's constants are the
contract's numbers; the whole layer is deterministic (no rng, no seeds).

**Parked on the way**: the Stockholm retrodiction case (written into
round 3's entry — a taiga historical town that fishing and transport
must carry); a marsh fog / fen flavor line for `WEATHER_LOCAL` when
round 5 opens the read surface; the observation that no lowland
continental deep forest survives the law (a Białowieża- or
Ardennes-shaped wildwood would need a hand mark — none authored now;
the taiga, the mountains and the marshes carry the wilderness); and
wool as trade colour for the pastoral west (round 4's list).

## 2026-08-21 (C) — Round 3 of the tile economy arc: population & the settlement census

**Where it started.** The designer opened round 3 hands-off — decide and
present everything not mentioned — with directives: modifiers on the
farming base (shores and rivers a bonus, the eastern periphery a malus);
a hamlet tier under a hundred people; several cities in one tile only in
the densest country (the Low Countries, Tuscany); city-with-towns as the
realistic pattern; countries of 10–25 tiles that must NOT read as a town
per tile — a medieval feel needs village-only tiles even in France, even
when that drags the density "unrealistically low"; 2–3 filled slots as
the organic norm; make it very gamey; and, above all, a DIRECTION
CHANGE — completely depart from calculated, historical or downscaled
densities and start at the tile level.

**The scale doctrine**, settled and recorded prominently because it will
be asked about. A tile is SPOKEN OF as 30 km east–west by 60 km
north–south (one travel day east–west, two north–south; 1800 km²). The
drawn map corresponds to real Europe at roughly 160 km per column by
220 km per row (about 35,000 km² per tile) — the height is 1.4× the
width, NOT the 2× the travel costs suggest. The map is a deliberately
squashed Europe: north–south travel is priced by the fictional 60 km,
not the real 220. By area the game world is about 20× smaller than the
real one (5.3× east–west, 3.7× north–south linear). The designer's own
20× calculation is confirmed — it is the AREA ratio. Slots follow the
same anisotropy: at most 4 per tile, thought of as a 2×2 lattice 15 km
apart east–west and 30 km north–south (twice as dense horizontally),
which is the medieval market-day spacing and the reason four is the
natural cap. Slots carry no stored coordinates — the lattice is doctrine
for fiction and scale statements only.

**The direction change, made law.** The old plan wording ("population
per tile, a hidden number, scale anchoring, census table") survives with
its meaning inverted: the hidden number is no longer a population count
but a relative SCORE whose only job is to pick a band, and the scale
anchor is no longer a density but the tier words' headcounts. Real
medieval Europe held 40–80 million; downscaling suggested a few million;
the settled census lands at ~1.3M souls — accepted, gamey, and the
famous cities are deliberately NOT downscaled (a metropolis is a real
hundred-thousand city), so the urban ratio runs far above the medieval
one. The designer pre-accepted that. The census IS the population: no
rural remainder is tracked, and the low-density character the numbers
"lose" is expressed the way the designer asked — a 1800 km² tile of
thin country rolls a village and a hamlet, about a thousand people,
rather than the 5–10k a 2–5/km² calculation would demand.

**The law and its tuning.** Score = realized arable + 0.35 × pastoral +
fishing (0.08 coast, 0.05 river; nile counts as river), × 1.15 transport
on coast or river (a town exceeds local carrying capacity only with
transport), × 0.6 marsh (fen fever), × 0.6 highland, × the eastern
frontier malus (−0.04 per column past 22, floor 0.65). Six bands:
wilderness / thin / low / mid / high / dense at 0.05 / 0.15 / 0.30 /
0.50 / 0.82. The first cut (transport 1.25, coast 0.10, dense at 0.72)
lit every shoreline dense — 62 dense tiles and 40 generated cities, a
city-studded Ireland — so transport and fish came down and the dense
threshold went up until dense meant what the designer said it should:
~19 tiles (the Rhine, the Danube corridor, the Nile, plus the hand
marks). Retrodiction against the authored towns forced three calls.
One: the eastern malus is the STEPPE's reach, so it row-gates to rows
1–13 — the first cut had it cutting the Nile granary and
Constantinople's shore, which are sea-lane country, not raider country.
Two: two `HAND_DENSE` exceptions with written reasons — the Low
Countries delta (the law reads undrained fen; its people drained it —
the polders ARE the land) and the Lombardy–Veneto belt (the redraw cut
the lagoon river for looks, and no law sees the Italian north's city
culture). Three: a historical city's COMPANION settlements roll from
its own band's table (truncated to the three remaining slots), not from
a flat table — Paris gathers towns and villages, Stockholm and Moscow
stand nearly alone, frontier-metropolis style. Round 2's parked
Stockholm case dissolved on inspection: the 2026-08-21 redraw left
Stockholm's tile two tiles from the drawn sea, so no fishing law can
reach it — the authored override carries the town, and the coast law
instead carries what it was really for, the Norwegian shore (coastal
taiga and tundra read thin-to-low with fishing hamlets while the inland
north stays wilderness). Prague reads low (the Bohemian rim's hills) —
accepted, not patched: the one-tile Bohemia cannot be both forested rim
and dense center, and the authored city carries it.

**The census.** Five tiers — hamlet (under a hundred souls), village
(hundreds), town (thousands), city (tens of thousands), metropolis (a
hundred thousand and more; "supercity" stays dev slang — the game word
is metropolis). Three metropolises authored: Paris, Constantinople, and
Venice promoted on the designer's own megacity principle (Venice was a
real ~100k city in 1500). The rest of the sixteen historical towns are
authored city or town (`HISTORICAL_TIERS`); capitals unchanged (Paris,
Rome, Kyiv). Per ordinary tile the band draws a weighted ARRANGEMENT
string; **the variance lives in the tables** — every settled band keeps
a village-only or emptier roll, only the dense band ever rolls a
generated city (including the rare two-city tile), and the mid/high
tables carry the designer's named patterns: town-and-three-villages (the
lord's tile), two-to-three villages in rich France, one lone town.
Measured over 500 seeds: ~610 settlements a world (3 metropolis, ~18
city, ~93 town, ~406 village, ~90 hamlet), 1.94 slots per land tile,
~52 of 314 tiles empty (zero is a real tier), 39% of high+dense tiles
with no town at all (min 23%, never zero), world 1.30M souls (1.12–1.52M).
The slot histogram (58/66/73/81/36 for 0–4 filled at seed 1) delivers
the organic 2–3-not-all-four feel.

**Randomized per playthrough — settled yes.** The census rolls off
derived seeds and differs between worlds; the worry about later
difficulty dissolved on inspection, because this is ALREADY the status
quo — the old slot census rolled per world too, and everything authored
(the sixteen cities, the capitals, the bands themselves) is fixed. The
sweet spot falls out: the CHARACTER of every region is deterministic
(France always feels like France), the instances are each world's own.

**The manor and the charter** (the designer's feudal-status question,
answered then minimally built). Historically the distinction is law, not
size: towns absolutely could hold charters (market towns, free and royal
towns, Stadtrecht), lords founded seigneurial towns precisely to farm
the tolls, and "city" as a legal word was a separate thing from
population. So the game's word is not a tier but a flag: cities and
metropolises always FREE (chartered), a generated town free 1 in 3 (an
unchartered town is a lord's town), and a village-led tile of 2+
settlements seats a resident lord 1 in 2 — the MANOR mark on its chief
village, the designer's lord-of-three-villages arrangement made a
stored word. Both words are rolled with the census and read by NOTHING
yet; what freedom is worth (taxes, revolts, entry at the gate) belongs
to the politics arc.

**What was decided** is plan.md's Round 3 implementation contract,
replacing the design entry: the scale doctrine written prominently; the
score law with its hand marks; the census roll off derived seeds
replacing `_population_slots` and `SETTLEMENT_DENSITY` (no
compatibility — the quest-geography and places fixtures re-pin); the
five-tier vocabulary with fiction headcounts and the mechanical mapping
(service bands, `BOARD_ACTIVE_CHANCE` extension, `C`/`T`/`v` glyphs with
hamlets kept off the map, starts never in a hamlet); the content owed
(hamlet and city roles per country, hamlet naming, pool growth); the
charter/manor words; and the pinned tests. econmap.py's constants ARE
the contract's numbers (`python econmap.py population --sweep` is the
measurement).

**Parked on the way**: the past-epidemic population scar and named
natural regions (unchanged, in the round's contract footer); the
charter/manor read surface (politics arc); hamlet and metropolis detail
(Settlements revisited); whether board activity should later derive from
the tile's band rather than the extended `BOARD_ACTIVE_CHANCE` table
(round 5's existing candidate list already carries it).

## 2026-08-21 (D) — Round 4 of the tile economy arc: mines, goods & the trade network

**Where it started.** The designer opened round 4 hands-off — decide and
lead everything not mentioned — with directives: hand back some eastern
European plains forest the deforestation law cleared against the
historical analogues; the big question of whether the old Dvarvengrond
dwarf cards can return from the pre-cut commits as a miners' guild or
league, best if it works for any mountain with mining; five mines to
hand-place (Rammelsberg/Harz, Kutna Hora, Falun, Banska Stiavnica,
Melle) with license to override; route tiles labelled with endpoints
and goods traded; a challenge to the plan's keep-the-exotics-off-the-map
remark ("they are just goods on routes — why not treat them the same");
and a draft goods list to round out. A separate directive — the DM's
easy access to tile facts, the map.txt fold-in, the neighbours in less
detail — was named as NOT this round's and went to round 5's candidate
list in plan.md.

**The exotics reversal.** The designer is right, and the remark is dead.
The unification that survives everything the remark wanted: every good
has ORIGIN TILES on the map, and an exotic's origins are simply the
frame's doors — the eastern gate (R11C30, the steppe corner south of
the mountains) and the delta port (R18C24) — plus the entrepôts the
legendary roads connect. The legendary roads stay worth taxing and
robbing not because their cargo is off-map but because the door is the
only place it enters; nothing else about exotics is special. Silk,
spice, sugar and dyes move only on the authored legendary roads; amber
kept its own authored road for the same reason.

**The goods model, settled** (the piece the designer said he did not
understand — recorded carefully). Three kinds of origin, one route law.
(1) DERIVED produce, by law over rounds 1–3's own numbers: grain where
realized arable ≥ 0.55 (only the alluvial river corridors and the Nile
— ordinary plains feed themselves and export nothing, which keeps the
map sparse), wine on med farmland, wool in the oceanic and med hill
country, horses on the steppe, timber where forest meets water (never
the fen carr), furs-and-wax in the cold deep forest. Contiguous origin
tiles aggregate into one REGION and a region under two tiles is local
colour, not an export (grain exempt: one alluvial tile is a granary).
(2) AUTHORED colour where no law can see it: the bay salt pans, the
wine coast, the Sound's herring, the amber shore, the two cloth looms
(the Low Countries, Tuscany), the Lombard armouries, the horse fairs.
(3) The MINES. Then one law moves everything: per good, a destination
kind (markets / cities / the metropolises / the smiths / the cloth
looms / the capital), a count and a bulk range — silver to the crown's
mint, wool to the looms, arms to the capitals, grain to the nearest
market — and the pathfinder draws the line. Routes with shared
endpoints merge cargo. The result reads like the real map: the silver
roads converge on Paris, the wool crosses to the looms, Venice becomes
the hub by construction (the Spice Lane, the Amber Road and the Fairs
Road all meet there — the middleman monopoly the roadmap wants as a
Mortellaria hook emerges from three authored endpoint pairs).

**The mines: five given, nine authored.** The given five sited by the
historical anchors: Goslar R09C14 (the Rammelsberg's town; silver,
copper), Kutna Hora R09C19 (east of Prague, the rim's silver at the
plain's edge), Falun R03C22 (moved one column EAST of the literal spot
so the copper mountain sits beside Stockholm in Tergal — with it every
country hosts mines and the League reaches all three lands), Banska
Stiavnica R10C20 (the Carpathian arc north of the middle Danube), Melle
R10C08 (the old western seam — long dead by 1500, but the game is
static in time and chronological difference becomes regional
difference, the round-1 principle). Four added under the override
license: Erzberg R11C14 (the iron mountain — iron was on the designer's
goods list and needed an origin; its ore feeds the Lombard armouries
two tiles away), Novo Brdo R13C18 (the Balkan silver, so Mortellaria
mines too — Rome's own mint road), and the two salt mines the old plan
entry always wanted, Luneburg R08C16 (beside the Elbe) and Wieliczka
R10C21 (the Carpathian foothills). Salt also rises at the authored bay
pans R10C05. **The mining-town rule became two laws**: every mine seats
an authored TOWN in census slot 1 (tier town, named by the mine, always
free — mining law is its charter; companions from the tile's own band,
so Falun stands alone in the wilderness while Luneburg gathers
villages), and a mine whose tile cannot feed itself (realized < 0.30)
gets a grain road from the nearest granary within 6 days — the food
caravan, a route and a vulnerability in one stroke, and exactly the
recovered card's geography. Seven of nine mines are hungry; six get
caravans; **Falun finds no grain in reach and stays unfed by design**
(pinned) — the north's grain problem is real history and a standing DM
story.

**The eastern wildwood** (the forest directive). Round 2 had parked
exactly this: no lowland continental deep forest survives the law, and
a Bialowieza-shaped wildwood would need a hand mark. Authored now as
`HAND_FOREST`: four continental-plains tiles east of Warsaw and north
of the Pripet pair (R07C24, R07C25, R08C24, R08C25), where clearance is
capped at 0.25 — the law would clear the continental east like the
west, and history left the great forest standing between the marsh and
the frontier. The block reads as one deep-forest island on the
character map, joins the Pripet into a single great wilderness, and
feeds the furs-and-wax trade (the fur rule admits continental deep
forest for exactly this reason — Lithuanian furs were real). Round 2's
unshipped contract was amended in place, Scotland-precedent: farmland
132→128, pasture 112→116, forest 97→101, cover open 217→213, deep
forest 42→46. The Ardennes-shaped western mark is still unauthored and
stays parked.

**The Miners' League — the recovery, investigated and settled yes.**
The pre-cut catalog (`git show 4d9155b^:worldsim.py`) holds the
Dvarvengrond EXTRACTION & CLAN CLAIMS family: new-seam → gold-rush (the
rush chain over the `deposit` slot), vein-dries → veins-reopened (the
bust and the recovery), strike, and food-caravan (admits on
grain-scarce — the mining town that cannot feed itself, already
written). Read line by line, the wording is almost entirely period
human mining language — claim-keepers, jumped claims, the company shop,
the winding gear, pit bosses, "grain is treasure up here" — and the
dwarf residue is exactly four things: "clan" throughout, one "A dwarf
has found a way", one "under-thane", and the `_DWARF_TOUGHS` pool name.
The re-homing: the MINERS' LEAGUE (the name over "guild" for its
Hanse-like cross-border sound and the free-miner Bergrecht flavor), a
brotherhood with chapters at every mine, cards re-keyed `mining/*` for
all three lands — which works "for any mountain with mining" at the
land level, and gains the specific mine as an address when the snapshot
arc gives all cards geography. THE KNOCKERS fact returns verbatim: it
was always human mining folklore. The deposit slot, its three words and
its two `STATE_MENU` steel prices return with the chain. The scrub
table is in the round-4 contract.

**The label** (the designer's route-label directive) ships as the
round's ONE read surface: `tile_detail_lines` grows the mine line, the
goods line, and a line per route with named endpoints and cargo —
`Goslar – Paris: silver`; `the Silk Road: the eastern gate –
Constantinople, silk and dyes`. Endpoints name themselves through the
historical towns, the mine towns and the authored endpoint names (the
eastern gate, the delta port, the Nile granary, the amber shore...).
The rest of the read surface stays round 5's, where the DM tile brief
directive now sits.

**The sea rule, settled minimally**: sea sails at the settled edge cost
— no cheap freight, one distance model for war, trade and play (a
cheaper sea would fork the game's one notion of distance for a layer
nothing plays yet). A route's sea tiles are its sea lane, the two
shores where it changes element are ports, and the Spice Lane and Grain
Fleet sail by construction. Rejected on the way: re-export chains (the
entrepôt story is told by routes MEETING at Venice, not by transshipped
cargo); a Hanse-shaped authored northern circuit (the derived north —
Falun's copper, the taiga timber, the Sound's herring, Luneburg's salt,
the amber shore — draws the circuit organically); oil as a separate
good (wine carries the med export story; the old plan list's honey
folded into wax).

**Built and tuned in econmap.py** (`routes [SEED]` / `routes --sweep`),
with two instructive wrong turns recorded: the first cut derived grain
at realized ≥ 0.42, which painted half the continent as surplus — the
threshold sits at 0.55 now, above the ordinary-plains baseline (~0.50),
so only the alluvial corridors and the Nile export and the goods map
stays sparse; and an empty-census-tile chief tested `in "MC"`, which is
True for the empty string in Python, so every EMPTY tile briefly read
as a city and routes ended in wilderness — the kind of bug only the
eyeball map catches. Measured over 100 seeds: ~59 routes (58–59 — the
network is nearly deterministic, moving only with the rolled cities),
~114 of 314 land tiles on a route, ~27 ports, ~36 sea-lane tiles at
seed 1, crossroads (3+ routes) ~41. Wool capped at 12 days (an 18-day
Anatolian wool haul to Tuscany read wrong); horses at 12 (the eastern
gate's steppe was shipping horses 22 days to Rome).

**What was decided** is plan.md's Round 4 implementation contract,
replacing the design entry: storage and tags, the nine mines and the
two mining-town laws, the nineteen goods with their origin laws and
destination table, the computed network plus the legendary five, the
sea rule, the label as the one read surface, the Miners' League
recovery with its scrub table, and the pinned tests. econmap.py's
constants ARE the contract's numbers. Rounds 2 and 3's unshipped
contracts were amended in place (HAND_FOREST; the mine towns and both
rounds' re-measured pins).

**Parked on the way**: the Hanse circuit and the Ardennes wildwood (the
contract footer); route-aware prices and boards (round 5's list); the
DM tile brief with the neighbour lines (round 5's list, designer
directive); the cards' tile addresses and everything that walks the
network — inns, tolls, banditry, the plague from a port (the snapshot
and later arcs, addresses now on the map).

## 2026-08-21 (E) — Round 5 of the tile economy arc: the hookup, and the arc cut into four sessions

**Where it started.** The designer closed the arc's design phase with a
hands-off mandate: complete round 5 — the read surface, the vaguest
round on purpose — solo, then reorganize plan.md's Part 1 into numbered
implementation sessions triggerable by "implement session N". The stated
point of the round: the new systems must actually APPEAR in the game,
and the old pre-Europe-map systems must be integrated properly. One open
question: does the build need four sessions, or fewer?

**The road the discussion took: the read-surface audit.** Round 5's
design work was an inventory of what the game already reads and where
the new ground can enter without new machinery. The surfaces found: the
tile's public file is `tile_detail_lines` inside map.txt's here-block
(session.here_lines); the DM's per-land pages are `world` and `lore` —
there is no per-tile equivalent, which is exactly the hole the round-4
sitting's brief directive names; prices flow through one channel
(worldsim.term via session.local_term, the six MENU_TERMS words, the
clamps), so a tile's economy can price itself as one more multiplier
with nothing stored; the recruit roll (roll_recruits) offers the PC's
full CHA capacity in any settlement, so a hamlet currently hires like a
town; the hunt and the road roll off land-level pools, and giving them
tile geography would front-run the monsters & fauna dump; the tier
tables that must grow the five census words turned out to be more than
the board — quests.SETTLEMENT_KINDS and conquest's tribute, garrison
and raid tables all key on settlement_tier, so the round named them
explicitly in the census session's contract rather than leaving
"service/board band" implicit. Round 3's parked question — board
activity derived from the band instead of the tier table — was examined
and REJECTED: the tier is already the band's expression through the
census roll, and a second band read would count the same ground twice.

**What was decided: the round 5 contract** (now plan.md's Session 4).
The read surface, from cheap upward: (1) the CHARACTER LINE — one
composed phrase per tile off a fixed priority (mine, then goods origin,
then cover/terrain/climate), writing.md register, one phrase never a
list; (2) the HARVEST WORDS — the spoken scale words only, never the
stored percent, and the causes' fiction names settled (the drought, the
great rains, the black frost, and on nile tiles the low Nile), which
discharges round 1's parked fiction-names item since this is the
harvest's first read surface; (3) both folded into tile_detail_lines,
completing the tile's public file beside session 3's trade label; (4)
the DM TILE BRIEF — places.tile_brief_lines plus a new `tile [COORD]`
verb beside `world` and `lore`, DM eyes, free, the whole tile file plus
the four neighbours in a line each, with the dm.md protocol (consult on
arrival and before narrating travel; narration material, never a dump);
(5) the TILE MENU — the integration minimum for prices: three static
rows (grain origin lodging 0.90, mine steel 0.90, crossroads goods 0.95
+ lodging 1.10) multiplying beside the land's dynamic terms under the
existing clamps, resolving round 4's parked route-aware-prices item
minimally; toll and ferry untouched. Two smaller integrations were
settled INTO earlier sessions where their data ships: the recruit tier
cap (hamlet 1, village 2 — the census session's) and the fen-fog
WEATHER_LOCAL line (the ground session's, discharging round 2's parked
flavor item). The storage question the arc opened with was settled as a
standing rule: one authority per constant — each session moves its
layer's numbers from econmap.py into places.py and re-points the tool
to import them back; session 4 finishes the turn by drawing econmap's
renders from a built world and retiring its --sweep commands into
**bench_worldgen.py**, the arc's measured suite over real worldgen
(harvest, census and trade sweeps, benchlog discipline). A scaffolding
sweep test in the removed-peoples manner closes the integration story:
ENVIRONMENT_PROFILES, SETTLEMENT_DENSITY, _population_slots, the
catalog environment key, prairie, and the bare basic/mountain tags all
provably gone. Non-changes recorded so the arc stays this arc: no
trouble score, no forward simulation, no card changes or addresses (the
snapshot arc), no creature geography (the fauna dump), the wealth band
stays the 2d6, the charter and manor stay write-only, no new map
overlay page, and board activity stays the tier table.

**The session cut — four, and why.** Part 1 was reorganized from five
design rounds into four implementation sessions, cut by implementation
seam rather than one-round-one-session: Session 1 is rounds 1+2's
deterministic authored ground and the sky (both overlays load in one
create_geography pass, round 2's laws read round 1's columns, and the
whole layer moves no bench by construction); Session 2 is the ROLLED
world — round 1's harvest moved out of its round to ride with round 3's
census, so every derived-seed roll and every acknowledged fixture
re-pin lands in one sitting, verified once; Session 3 is round 4's
trade network over that census, minus the League; Session 4 is round 5
plus the Miners' League recovery, moved from round 4 because the
old-world cards returning is old-system integration — the hookup's own
business — and because it balances the trade session down to one
coherent layer. Fewer than four was considered and declined: merging
sessions 3 and 4 makes a sitting whose verification pass (routes +
League content + every read surface + the new bench) is too wide to
trust, and session 1 is already the largest safe bite. Five (the
literal round mapping) was declined too — the harvest alone under-fills
a sitting and splits the fixture churn across two. The designlog's
round names remain the design authority; the sessions are the build
cut, and each session's contract header points at its rounds.

**Parked on the way**: seeding `new`'s opening hook from the character
line (a build option, not contracted); creature and encounter geography
(the fauna dump, as before); tolls, inns and banditry walking the route
network (the snapshot and politics arcs); the exact character-word and
cause-name phrasings left to the build under writing.md, with the
contract's examples as canon.

## 2026-08-21 (F) — Session 1 of the tile economy arc: the ground & the sky, built

**What shipped.** Plan.md's Session 1 whole: rounds 1+2's authored ground
and the sky it hangs under, in one `create_geography` pass.

- **The two overlays load onto the Tiles.** `places.load_overlay` reads
  `resources/europe_climate.txt` and `resources/europe_terrain.txt` beside
  the base map and `create_geography` stamps `tile["climate"]` and
  `tile["terrain"]` with the full words (the letters stayed file format).
  `_validate_ground`, called from `validate_world`, is the law demoted to a
  lint: painted iff land, alpine and mountains exactly on the `^` tiles,
  only legal words, and the pinned climate (u8 t42 c83 o28 m46 w32 s24 d18
  n4 a29) and terrain (plains 213, hills 67, marsh 5, mountains 29)
  censuses, plus the marsh five by coordinate.
- **`CLIMATE_PROFILES` replaced `ENVIRONMENT_PROFILES`** — ffd and its
  reference row, the wheat yield, winter severity, the harvest day and
  `drought_days`, ten rows. The five old profiles, the catalog's
  `environment` key, the land record's `environment` field and
  `worldsim.ENVIRONMENT_PROFILES_BY_LAND` are gone.
- **The laws moved into `places.py`** beside the table — arable potential,
  the ffd gradient, the closed-form clearance, realized arable, surviving
  forest, the pastoral index, the three hand mechanisms (`HAND_ALLUVIAL`,
  `HAND_FOREST`, `HAND_MARKS`) — and `econmap.py` now imports them back,
  which is the arc's one-authority-per-constant rule taking its first turn.
  The tile keeps only the words: `terrain`, `cover` and the tag list; the
  fractions are worldgen intermediates and are never stored.
- **The tag vocabulary is reconciled.** A land Tile now leads with its
  terrain word and carries the derived ones — `forest`, `farmland`,
  `pasture`, the character climates — so the quest tables' `forest` /
  `hills` / `pasture` / `farmland` match real natural Areas for the first
  time (before this every such job fell back to the origin Tile's
  countryside). `basic` and `mountain` left the tag lists, `prairie` was
  renamed `steppe` everywhere, and `marsh` joined the beast-lair tables.
  Pinned: farmland 128, pasture 116, forest 101, steppe 24, desert 18,
  tundra 8; cover open 213, wooded 55, deep forest 46.
- **Natural Areas are named and stocked by CHARACTER** — one
  `natural_character` function behind both halves, so a Tile called
  Marshes cannot be stocked with windmills. Firascir's whole `fields`
  inventory was dead data before this (every basic tile drew
  `old_forest`); now every authored inventory in the catalog is drawn from
  somewhere, and `validate_catalog` fails if one is not.
- **Settlements fit by character too.** `TILE_FIT_TAGS` dropped `basic` /
  `mountain` / `sea` and grew the terrain and derived words, so a hill town
  wants hills and a fen village wants the fen.
- **The sky is climate x season.** A season CALENDAR (day 1 = April 1st,
  60/90/60/150, autumn reusing spring's column, `season_of` a lookup
  nothing stores), a `CLIMATE_WEATHER` table of thirty rows each summing to
  100, and a day roll whose weights come from the ground the party is
  standing on. `WEATHER_LOCAL` re-keyed by climate and grew its one
  terrain-keyed line, the fen's fog. The wet/dry counters, the drought
  bend, the cards' own skies and the bought sky are untouched.

**The calls the spec left open, and how the build settled them.**

1. **Where the party is standing.** The day roll needed a tile and
   `roll_world(world, day)` has no session state, so the world carries
   `world["party_tile"]`: stamped by `create_geography` with the start
   Tile and kept current by `session.move_party`, the one writer. It is a
   `validate_world` clause.
2. **The sky of a land the party is NOT in.** Every land still rolls one
   sky a day, so the other two realms needed a reference. The build chose
   their CAPITAL Tile — Paris, Rome, Kyiv — because it is concrete and
   already pinned, over a computed modal climate, which would have been a
   statistic rather than a place. The same rule stands in when the party is
   at sea, where there is no ground to read.
3. **Where the weather weights live.** In `worldsim.py`, which owns the
   sky, not in `CLIMATE_PROFILES`. The profile keeps the five columns the
   contract named; the table of thirty rows sits next to the roll that
   reads it, and `validate_content` checks the rows sum to 100 at import.
4. **`forest` the character vs `forest` the tag.** The Area suffix and the
   site inventory take DEEP forest only (46 Tiles), as the contract's
   naming line says; a merely `wooded` Tile keeps its terrain character and
   still carries the `forest` TAG, which is what a job matches on. That
   keeps 101 Tiles answering a den job while only the real wilderness is
   named Forest.
5. **An eighth character, `coast`.** Naming has seven words; SELECTION has
   eight. A shore Tile that would otherwise be plain countryside draws the
   country's coast inventory where it authors one, which is what keeps
   Mortellaria's `rocky_coast` alive. Its Area is still named Countryside.
6. **The inventory pick is POSITION-based**, `(row + column) % n`, not
   seed-based: this whole layer is identical in every campaign, and a
   checkerboard puts a country's two kinds of hill country next to each
   other instead of clumping them.
7. **A fourth new natural inventory.** The contract owed three (firascir
   hills, firascir marsh, tergal marsh). Tergal also needed a FOREST one:
   thirty of its Tiles are deep forest and it had no wood in its catalog at
   all. `taiga_wood` — the timber road, the trapper's line, the charcoal
   camp — is the addition.
8. **Two new settlement templates.** Moving `forest_village` onto
   `forest` left Firascir with no free village role, which
   `validate_catalog` requires (a plain inland Tile has to be able to draw
   something). `field_village` — a green, a plough inn, a tithe barn — is
   the free one now. Moving `herd_village` onto `steppe` did the mirror
   damage in Tergal: with the herd village gated, every one of the thirty
   forest Tiles in the taiga north drew `basin_village`, and a village of
   salt grass and goat pens in a dry hollow is not what stands in the
   Russian forest. `wood_village` — log houses, a sable inn, a fur store —
   fits `forest` and takes them. A settled world now spreads Tergal's
   villages 11 wood / 9 basin / 7 herd / 1 river instead of piling them
   all on one role.
9. **`ridge_town` kept `mountain-foot`.** The contract re-fitted both hill
   towns onto `hills`; Tergal carries exactly ONE hills Tile (R04C22, which
   the deforestation law makes deep forest and which rolls no settlement),
   so the re-fit would have made an authored template dead data — the very
   disease this session was cutting out. Mortellaria's `hill_town` took
   `hills` as written.
10. **`marsh` joined the beast-lair tables only** — Wolves Attack, The
    Great Hunt and the fallback den — not the two dragon tables, which are
    about high ground. The Great Hunt also lost `basin`: that word is
    carried only by Tergal's settlement templates, so on a hunt's table it
    was routing a den job at a town.
11. **The player never reads `basic` again.** `places.tile_ground` is the
    one word for what a Tile is made of — the terrain word, or `sea` — and
    the `HERE:` block, `look`'s TILE line and its roads-out list all speak
    it. The base map's four glyphs went back to being a drawing
    vocabulary. The full composed character line is still session 4's.
12. **Two test fixtures were re-pinned**, both because the world legitimately
    moved under them: `test_places`' natural-site test asserted three
    distinct site TEMPLATES (incidentally true of `old_forest`, not of
    `fields`) and now asserts three distinct SITES, which is what its name
    always said; `test_quest_geography`'s `_inactive` helper now asks for a
    shut board with no forced work already standing at it, since the
    template shift moved which settlement it picked.

**Measured.** `test_ground.py` is the new contract suite (30 tests, four
parts); the full suite went 798 to 828, all green, with only the two
fixtures above touched. Seven of the eight benches are byte-identical.
`bench_quests.py`'s career sim MOVED, and it was supposed to: with the
tag words finally real, a wolf hunt is posted at a genuine wood out on
the map instead of falling back to the origin Tile's own countryside, so
windows priced by the road got longer — turn-ins land earlier in them
(quick 30% to 39%), a sixth fewer postings expire (294 to 242 a career),
and a fresh world seeds 7% more XP. The progression cells are flat (L8
and L14 identical, the median death level 9 both ways). Nothing was
tuned; benchlog's 2026-08-21 entry has the table, and a note on the top
band caught swinging on a change that cannot touch combat.

**Parked on the way**: nothing new. The plan's own non-changes hold — hills
still cost no travel day, terrain is still out of the weather law and out
of the harvest model — and Session 2 (the rolled world: the last harvest
and the census) is next and unblocked.

## 2026-08-21 (G) — Session 2 of the tile economy arc: the rolled world, built

**What shipped.** Plan.md's Session 2 whole: the arc's two ROLLED layers —
round 1's last harvest and round 3's settlement census — plus the five-tier
vocabulary they speak in, the content the tiers owed, and every fixture
re-pin the churn cost. This was the arc's one fixture-churn sitting by
design, and it was verified once.

- **The last harvest rolls at worldgen.** `places.roll_harvest(world)`
  stamps `tile["harvest"]` (an int percent, 100 = a full excellent
  harvest) and `tile["harvest_cause"]`, and puts the region records —
  id, cause, center, member tiles — on `world["harvest_regions"]` as the
  addresses the snapshot arc will wire. Four to six regions, centers
  weighted by `CENTER_WEIGHT`, a cause drawn per center climate, contagion
  growth by ring, a fine year everywhere else. Both guarantees hold: the
  drought is re-caused onto the most drought-apt center when no region
  rolled one, and the NEARBY TROUBLE nudge relocates the last-rolled
  region into five path days of the start three times in four.
- **The census replaced `_population_slots` and `SETTLEMENT_DENSITY`
  whole.** `places.roll_census(world)` scores every land tile by law
  (`tile_score` / `score_band`, never stored — `population_band` recomputes
  it), draws a weighted ARRANGEMENT from the band's table, and turns the
  letters into slots sorted chief-first. Historical tiles take their
  authored tier from `HISTORICAL_TIERS`; the nine `MINES` seat their mine
  town in slot 1; both then draw companions from their own band, truncated
  to the three seats left. The charter and the manor ride along as one
  stored word each and are read by nothing.
- **Five tier words, everywhere they are keyed.** hamlet / village / town /
  city / metropolis. `quests.SETTLEMENT_KINDS`, conquest's
  `GARRISON_BANDS` / `CONQUEST_ENCOUNTERS` / `TRIBUTE_PER_DAY` /
  `GARRISON_CAP` / `RAID_STRENGTH`, `rpg.HEALER_TIER_CAP`,
  `rpg.DISEASE_REACH`, `places.BOARD_ACTIVE_CHANCE` and the crime market
  all carry them: city-grade takes the capital's rows, the hamlet the
  village's, and tribute halves for the hamlet. The 2026-07-27 merge of
  "city" into "town" is undone — the tier is a design rung now.
- **The map ladder is three rungs over five tiers.** `C` is any city-grade
  place (capital, metropolis, city), `T` a town, `v` a village, and a
  HAMLET IS NOT DRAWN. `MAP_MARK_LEGEND` says "C city"; a tile of only
  hamlets reads as its own ground and its hamlets appear in the detail
  lines.
- **The content the tiers owed.** A `walled_city` and a `cot_hamlet` role
  per country in `place_catalog.json`, city and hamlet name reserves per
  country and a modest village-pool growth. `validate_catalog` now demands
  a free role at every generated tier and rejects a metropolis role, and
  the "no `city` anywhere" clause the ground session added is gone.
- **econmap.py took its second turn.** The harvest and population
  constants moved into `places.py` and the tool imports them back through
  a `_by_letter` window (it draws letter grids; the game speaks words),
  keeping only the rendering. Only the trade constants are still authored
  there.

**The calls the spec left open, and how the build settled them.**

1. **Order inside `create_geography`.** Census, then the start draw, then
   the harvest. The harvest's nudge needs `world["party_tile"]`, and the
   start needs a census to stand in, so the harvest goes last. That is the
   ONE thing the harvest layer reads from the census, and the suite pins
   it: tear the whole census out, re-roll, and the same year comes back.
2. **The nudge runs BEFORE the drought guarantee.** The plan fixed the
   nudge only as "before growth". Running it first means re-drawing the
   relocated region's cause can never cost a world its year of dust; the
   other order could.
3. **The nudge's measured posture is 86%, not the plan's ~88%, and its raw
   base is 36%, not ~52%.** The plan's raw number came off econmap's
   private simulation with a different start-tile draw; the shipped one
   also excludes hamlets from the start. 36% + 64% x 0.75 = 84%, and the
   500-seed measurement is 86% for a center within five days and 92% for
   an actual problem tile within six. The posture the round asked for —
   the campaign usually opens in or beside a bad year, and the quiet start
   survives at about one world in eight — holds exactly.
4. **The hamlet has no smith.** The plan asked for a minimal hamlet ("a
   well, a shrine, no board sites") while also saying the hamlet takes the
   village's service gates. Cutting ALL four required services would have
   broken the standing contract that every settlement is a place the party
   can stand in — which this session was not asked to change — so the
   hamlet keeps a bed, a counter and the healer behind it and loses
   exactly the SMITH: a hundred souls cannot keep a forge, and a broken
   sword is a reason to walk to the next village. `REQUIRED_SERVICES` is
   now per tier, `places.has_service` is its reader, and
   `session.require_service` gates `buy`'s steel branch with a line that
   names the tier. Its four sites — the well, the wayside shrine, the cot
   inn and the general store — carry no hall, no market and no notice
   post, which is the "no board sites" line honored where it costs
   nothing.
5. **The hamlet's tribute is 1 g/day, not the plan's parenthetical 6.**
   The contract says the hamlet takes the village's rows "except tribute
   halved (6 g/day)", and the village's shipped row is 3. The intent —
   halved, barely worth holding — was taken over the number, so the
   hamlet pays 1. If 6 was meant literally it is a raise, not a halving,
   and it should be set deliberately.
6. **A metropolis wears the CITY role.** The plan cut metropolises from the
   city role "until the Settlements-revisited round gives them their own",
   which leaves them nothing to be cut FROM. `_settlement_template` maps
   metropolis onto the city role, `validate_catalog` rejects an authored
   metropolis role so the debt stays visible, and plan.md's Settlements
   section now carries it.
7. **The band is not stored.** The plan stores the harvest percent and the
   census, and says the score is "deterministic and never saved". The BAND
   is one derived step from the score, so it went the same way:
   `population_band(world, tile)` recomputes it, exactly as `tile_economy`
   recomputes session 1's fractions. Nothing stores a number this session
   did not name.
8. **The crime market reads an equivalence, not thirty rewritten rows.**
   `crime.py` keys 27 categories and six mark bands on three words.
   `crime.TIER_ROW` maps hamlet onto village and city/metropolis onto
   capital and is strict — every word a settlement can carry is in it — so
   a city is not silently a place with no marks.
9. **A mine town is authored but not KNOWN.** `slot["authored"]` means
   "known from day zero and listed among the historical cities", which is
   a privilege of the sixteen. A mine town has an authored NAME and an
   authored tier and stays hidden until its tile is entered; `validate_world`
   admits it on a mountain by looking the tile up in `MINES` rather than by
   a new stored flag. Two of the nine (Banska Stiavnica, Erzberg) sit on
   mountain tiles, which is what forced the clause to widen at all.
10. **Three fixtures were re-pinned, all because the world moved under
    them.** `test_quest_geography`'s rumor-radius class moved from seed 19
    to **seed 21** (Aston, with Dublin two days off carrying nothing and
    London three off carrying work — the same populated/empty pair,
    mirrored), and its one-day fixture from seed 28 to **seed 18**
    (Tomton, Prague a day off). Only ONE seed in 160 produced the pair at
    all, which is worth knowing: the rumor radius plus sparse boards make
    that fixture genuinely rare. Its plural test also stopped asserting
    `"1 days"` is absent — the window text "(11 days left)" contains it —
    and now asserts the two things it actually meant. `test_places`'
    historical-tile and population-constraint tests were rewritten around
    the new model, and `test_conquest`'s `test_city_tier_is_gone` became
    `test_every_census_tier_is_priced`.
11. **Two "usable settlement" tests became tier-aware.** `test_worldsim`
    asserted all four services of every settlement; both now read
    `places.REQUIRED_SERVICES` and additionally assert that the smith is
    present exactly where the tier is not hamlet. They passed unchanged by
    luck — the seeds they use happened to materialize no hamlet — which is
    precisely why they were fixed rather than left.

**Measured.** `test_rolled_world.py` is the new contract suite (33 tests,
four parts, twenty-two broken worlds); the full suite went 828 to 861, all
green. Over 500 worlds the census lands where the round said it would:
614.5 settlements a world (3.0 metropolis, 17.7 city, 100.6 town, 401.7
village, 91.6 hamlet), 1.96 slots per land tile, 49 of 314 tiles empty,
37% of high-and-dense tiles with no town (min 25%, never zero), 1.32M
souls, 64 chartered settlements and 52 manors. The harvest: 17.7% mean
problem coverage (6–33%, never zero), 5.1 regions of 11.3 tiles, a drought
in every world. benchlog's 2026-08-21 entry has the bench table.

**One finding that is not this session's.** `bench_abilities.py` came back
different and was tested against ITSELF on an unmodified tree: two
consecutive runs of the original code differ in the same cells. Its
warrior-moves matchup and alchemist career blocks are not reproducible;
the rest of the file is. develop.md's Files entry and plan.md's leftovers
list now carry the warning, because a bench that cannot be compared
against itself cannot be used to clear a change.

**Parked on the way**: nothing new that the plan did not already carry.
The four items session 2's contract footer held were moved into Part 2
where their owners are — the past-epidemic scar and named natural regions
to the snapshot arc and the leftovers list, the charter/manor readers to
the leftovers list pointing at the politics arc, and the hamlet/metropolis
detail to Settlements revisited. Session 3 (the trade network) is next and
unblocked: its `MINES` table is already in `places.py` and its mine towns
are already seated.

## 2026-08-21 (H) — Session 3 of the tile economy arc: the trade network, built

**What shipped.** Plan.md's Session 3 whole: round 4's trade layer — the
nine mines' whole reading, the nineteen goods and their three kinds of
origin, the computed route network with the five legendary roads, the sea
rule, the four tags, the `validate_world` clauses and the tile label that
is the layer's one read surface. econmap.py took its third and last turn:
**no constant in the tool is authored any more**, and its restated
pathfinder is gone.

- **The layer is a pure function of the census.** `places.roll_routes(world)`
  runs in `create_geography` immediately after `roll_census` and consumes
  NO rng — it takes no derived seed of its own, because it needs none.
  Sessions 1 and 2 each argued their derived seed carefully; this one
  argues the absence of one. The layer is still each world's own, because
  which Tiles are cities is what decides where the ordinary network goes:
  the trade skeleton is fixed in character (the mines, the origins, the
  legendary five) and each world's own in detail.
- **The three kinds of origin, one law.** `goods_origins` builds the
  authored mines, the authored colour with its two exotic doors, and the
  derived produce regions by law over sessions 1-2's numbers; `GOOD_ROUTES`
  then moves all of them with one table — destination kind, count, bulk
  range in days — and the pathfinder draws every line. Routes sharing both
  endpoints merge their cargo. On top of that the two authored additions:
  a grain road to every mine whose own ground cannot feed it, and the five
  legendary roads whose authored endpoint pairs the same pathfinder joins.
- **The label** — the one read surface. `tile_detail_lines` grew the mine
  line, the goods line and one line per route crossing the Tile, all of it
  common knowledge: `mine: Goslar`, `goods: silver, copper`, `Goslar -
  Paris: silver`, `the Silk Road: the eastern gate - Constantinople, silk
  and dyes`.
- **Measured over 500 worlds**, landing exactly on the round's pins: 58.7
  routes (58-59), 113.7 of 314 land Tiles on a route, 27.0 ports, 26.0
  sea-lane Tiles, ~37 crossroads. Falun unfed in all 500. Every
  reproducible bench byte-identical, and an exact five-seed worldgen hash
  identical on both trees. benchlog's 2026-08-21 (C) entry has the tables.

**The calls the spec left open, and how the build settled them.**

1. **The pathfinder is rooted at the DESTINATION, not the origin.** The
   plan said "places.py's own `_single_source`; ties settle
   deterministically" and left which end the tree hangs from open. Rooting
   at the market is the load-bearing choice: many origins ship to one
   market, so one tree serves them all AND every road into that market
   settles its ties the same way — the silver roads converge on the mint
   instead of each drawing its own equally cheap line one tile over.
   Rooting at the origin would have been correct and ugly. It is also what
   made the shipped numbers reproduce econmap's exactly, which is how the
   swap was verified: the tool's output before and after the pathfinder
   retirement is byte-identical.
2. **No derived seed for the routes.** Call 1's sibling. The arc's standing
   rule is "derived seeds throughout, so every existing bench measures the
   same board"; the honest reading here is that a layer which draws no
   random numbers cannot disturb a stream, and inventing a seed for it
   would have been ceremony. The benches confirm it.
3. **The trade tags are kept OFF an Area's tag list.** This was the one
   real bug the session found, and it was invisible until the benches ran.
   `materialize_slot` merges the Tile's tags into the settlement Area, and
   an Area's tags are QUEST vocabulary: `_select_quest_area` picks by them,
   and `quests._fallback_place_requirement` already asks for a `mine` tag
   for any forged job whose text says mine, deep or cave. Letting the four
   trade words through would have made the quest generator a silent reader
   of the trade layer — precisely what the contract's "nothing reads routes
   yet beyond the label" forbids. `materialize_slot` now merges the GROUND
   tags only. Worth noting for session 4: wiring that back on PURPOSE (a
   mine quest landing at a real mine is better fiction than a mine quest
   landing on any mountain) is a one-line change with the reason written
   beside it.
4. **The label wraps itself.** `tile_detail_lines` gained a `width` and a
   `_detail_wrap` that mirrors session.py's rule exactly (continuation two
   spaces past the indent), so the output is byte-identical after the
   driver's own wrap and the Tile's file is the same list of lines whoever
   asks for it. Without it a label test would have had to re-implement the
   wrap to check the wrap.
5. **An unnamed endpoint reads as its coordinate.** The design named the
   historical cities, the mine towns and the authored marks as the naming
   authorities and said nothing about a rolled market. Naming it would leak
   a settlement the party has not met; the coordinate is what the map
   already calls that Tile, so `R09C17 - Luneburg: salt` is consistent with
   the rest of the page. dm.md now says to narrate such an end as "the
   market east of here" rather than inventing a name.
6. **The `port` clause is about the SHORE, and the delta port is a grain
   origin.** Two small confirmations the build made concrete: a port is the
   LAND tile of an element change (so `validate_world` can demand `coast`
   on it), and the delta port at R18C24 turns out to sit on alluvial ground
   that clears the grain threshold — so it exports spice, sugar, dyes AND
   grain. That is the exotics reversal working as designed rather than an
   accident: an exotic door is an ordinary tile with an ordinary goods
   list, and the test now pins it.
7. **Two fixtures were re-pinned, both because the world moved.**
   `test_ground`'s seed-invariance test compares the GROUND tags only now —
   the three road words follow the rolled census, so which Tiles wear them
   IS the seed's business, and test_trade asserts the other half of the
   claim (the mines, the origins and the legendary roads identical across
   seeds). `test_ui_logs`'s wilderness test matched "the first indented
   line containing the settlement's name", and seed 27 opens at Goslar, so
   `  Goslar - Paris: silver` started answering; it now matches the Area
   line by its `name (` prefix.

**The finding that is not this session's.** `bench_quests.py` came back
different and was tested against ITSELF on an unmodified tree, three
consecutive runs: parts 1 and 2 (the room and site honesty blocks) are
byte-stable, and the CAREER block is not — reached-L20 came back 0.5%,
1.5% and 0.0% from identical code. This is the same defect session 2 found
in `bench_abilities.py`. Two of the five calibration benches now cannot be
compared against themselves; develop.md's Files entries carry both
warnings, and plan.md's leftovers list now names both. It is worth a
sitting of its own, because a bench that cannot clear a change is not a
safety net.

**One thing to feel at the table.** The label is crowded where the trade
is: Paris carries fourteen route lines, and the busiest Tile in an average
world is crossed by twelve or thirteen routes. That is honest — Paris IS
where the roads meet — but on a 40-column phone page it is twenty-odd lines
under the grid, and it will read as a wall before it reads as a trade
capital. The contract asked for one line per route and got it; the natural
place to decide whether a `+N more` cap belongs there is session 4, which
owns the whole read surface and is already giving the DM a separate tile
brief.

**Parked on the way**: nothing new. The round-4 footer's two items (the
Hanse-shaped northern circuit, the Ardennes-shaped western wildwood mark)
move to Part 2 with the rest of the arc's leftovers when session 4 deletes
Part 1; until then they stay on session 4's contract footer. Session 4 (the
hookup: the read surface and the Miners' League) is next and unblocked —
its tile character line, its harvest words, its tile brief and its tile
menu all read layers that are now on the ground.

## 2026-08-21 (I) — Session 4 of the tile economy arc: the hookup, built (and Part 1 deleted)

**What shipped.** plan.md's Session 4 whole, which is round 5 (the read
surface, the integration minimum) plus round 4's Miners' League recovery.
With it **the tile economy arc is finished and Part 1 is gone from
plan.md** — the file now carries only the roadmap beyond both arcs.

- **The read surface: one phrase and one word.** `tile_character` composes
  a Tile's whole geography into ONE short phrase by fixed priority — the
  mine by its first metal, then the good it is an origin of, then the land
  itself off cover, terrain and climate — and `harvest_line` speaks last
  year's harvest as its scale word plus its cause's fiction name. Both fold
  into `tile_detail_lines`, so the Tile's public file is now complete:
  header, character, ground tags, harvest, mine, goods, roads, Areas. The
  arc's hidden-numbers-visible-words rule finally has the page it was
  written for: the percent, the score and the yield are never printed.
- **The DM's tile brief.** `places.tile_brief_lines` behind a new `tile
  [COORD]` verb — the sibling of `lore`, one level down. One Tile's WHOLE
  file, including the two things the player's page must not have: the
  census in full (every slot by tier, `a village (unmet)` where nobody has
  been) and the four neighbours in a line each, so the DM narrates toward
  the next Tile knowing what is there. dm.md gained "The ground under the
  party" and its quick reference gained the tier scale, the season
  calendar and the climate words.
- **The tile menu.** Three static rows — grain-origin lodging 0.90, mine
  steel 0.90, crossroads goods 0.95 and lodging 1.10 — multiplying into
  `worldsim.term` under worldsim's own clamps, read by `session.local_term`
  and the `prices` sheet. Nothing stored, nothing rolled. This resolves
  round 4's parked route-aware-prices item at exactly the size round 5 cut
  it to; `toll` and `ferry` stay untouched.
- **The Miners' League.** The pre-contraction extraction family recovered,
  scrubbed of four dwarf words and re-keyed `mining/*` on ANY_LAND. The
  `deposit` slot is back (the first entry in `STATE_SLOTS` since the
  closure emptied it) with its three stages and its two steel prices; six
  cards; THE KNOCKERS returns verbatim as the game's first land-agnostic
  FACT, plus a League fact per land.
- **econmap.py finished its turn.** Every mode now renders a BUILT world
  (`places.create_geography`) — the tool's private `roll_harvest`,
  `roll_census`, `roll_routes` and their coordinate plumbing are gone, so
  its numbers are the game's rather than merely like them — and its
  `--sweep` commands retired into **`bench_worldgen.py`**, the arc's
  measured suite over real worldgen. A new `character` mode draws session
  4's own read surface.

**Measured over 500 worlds** (benchlog's 2026-08-21 (D) entry), landing on
every pin the arc published: harvest problem coverage 17.7%, 5.1 regions of
11.3 tiles, drought guaranteed in all 500, **trouble within five days of
the start in 86%** — the round-1 design said seven in eight and this is the
first time the shipped nudge has been measured at all, because econmap knew
no start tile; census 3 / 17.7 / 100.6 / 401.7 / 91.6 by tier and 1.96
slots a land tile; trade 58.7 routes, 113.7 land tiles on one, 27 ports, 26
sea-lane tiles, Falun unfed in all 500. Worldgen is byte-identical to
session 3's tree over a five-seed hash of every stamped word, and every
reproducible bench is unmoved.

**The calls the spec left open, and how the build settled them.**

1. **The chain the recovery would have left open, closed.** The pre-cut
   `new-seam` set `claims-collide` and guarded on it, and the card that
   CLEARED it was a politics card belonging to the deleted country. Brought
   back as written, the rush chain would have fired exactly once per world
   forever. `gold-rush` now clears it — which is not a repair bolted on but
   the 2026-08-12 chain rule applied exactly ("a link is a `set` state the
   successor admits on and clears"): the bust settles the argument the find
   started, and the chain closes so it can run again next year.
2. **`roll_world` was advancing the wrong axis, and the League found it.**
   It brought each land up to the target day IN TURN, so the second land's
   day 5 draw read the first land's day 60 — a world caught up at an
   arrival was not the world that had been watched. Six cards admit on a
   DERIVED state and could see it; it had never surfaced because none of
   them had ever fired on the differing side at a benched seed. Making
   `mining/food-caravan` ANY_LAND put it in all three decks and the
   catching-up test failed the same hour. It now steps the CALENDAR — one
   day across all lands, then the next — which is what its docstring
   already promised. This is a real pre-existing bug, not a fixture repin.
3. **`TILE_CHARACTER` is the goods half and `LAND_CHARACTER` the land
   half.** The contract named one table; the two halves have genuinely
   different shapes (a lookup by good, an ordered rule list over four
   fields), and forcing them into one structure would have made both
   unreadable. They sit in one commented block and are documented as one
   table.
4. **Two land-character rows never fire on the shipped overlays**, nor
   does the `plains` fall-through. Every
   deep-forest Tile is already a fur or timber origin and every non-marsh
   steppe Tile is horse country, so `deep forest` and `the open steppe`
   never reach a page — and `plains` never does either, because the earlier
   rules cover every plains Tile that lacks the farmland tag. They are kept:
   they are LAW rows over the whole climate/terrain/cover vocabulary, not
   fallbacks softening a state the code cannot produce, and an overlay
   change could bring any of them back tomorrow. `econmap.py character`
   prints which are unused so the fact stays visible, and plan.md carries
   the note. The alternative — letting the wilderness words outrank the
   produce — was rejected: "fur country" for the Lithuanian wildwood and
   "horse country" for the steppe are the better fiction, and the DM has
   the cover word in the brief either way.
5. **The route cap is 4, and the named roads lead.** Session 3 left the
   question on this desk (Paris carries fourteen lines). Four fits the
   phone page beside everything else the block now prints, and when the cap
   bites, a legendary road is what a player would want named — so
   `route_lines` sorts named-first and tails with `+N more`, the
   `map_legend_lines` pattern. The DM's brief is uncapped, because it is a
   file rather than a page.
6. **The character line is skipped where it would only repeat the header.**
   A bare-terrain Tile falls through to its own terrain word, which the
   HERE line has already said; printing it twice is noise. Sixteen mountain
   Tiles and every sea Tile take the guard.
7. **`fact()` may name ANY_LAND now.** THE KNOCKERS "returns verbatim" and
   belongs to all three lands; the alternative was three copies of the same
   paragraph. `FACTS_BY_LAND` admits it exactly the way `in_land` admits a
   card, which is the frame the file already had.
8. **The trade tags stayed OFF an Area's tag list.** Session 3 flagged
   wiring them back on purpose (a mine job landing at a real mine) as a
   one-line change for this session. Declined: the contract's own
   non-changes list says quest and encounter geography is a later arc's,
   and `mine` reaching `_fallback_place_requirement` would make the quest
   generator a reader of the trade layer through a side door. It stays a
   deliberate one-line change waiting for the arc that wants it.
9. **econmap's harvest numbers moved, and that is the point.** The tool
   used to roll a plain seeded rng with no start tile; it now draws the
   real layer, nudge and derived seeds included. Its output before and
   after is NOT comparable and was never meant to be — the deterministic
   censuses (terrain, cover, tags) reproduce exactly, which is the half
   that could be checked.

10. **The session added one `validate_world` clause after all.** The
   contract said "if any", and the layer stores nothing, so the honest
   first answer was none. But `tile_character` raises a KeyError on a good
   with no phrase, and it would raise INSIDE a map page mid-play, on
   whichever Tile happened to carry it. `_validate_read_surface` moves that
   to world creation: every Tile can say what it is and what it ate, in
   words the tables actually hold. Three broken worlds pin it.

11. **The neighbour line says `a village`, not `a village (unmet)`.** The
   contract asks the neighbour line for "chief settlement tier and name if
   any" and asks the CENSUS for `a village (unmet)`; built with the full
   marker on both, 70% of neighbour lines wrapped onto a second line and
   the four-neighbour block was eight lines deep. The indefinite article
   already carries the meaning against `village Erkhet`, and dropping the
   eight characters took the wrap rate to 20%. The census keeps the full
   word, where the DM is reading rather than glancing.

**Two fixtures were re-pinned**, both because the world genuinely changed.
`test_worldsim`'s quiet-land shop test stands the party at Paris, which is
now a crossroads, so its 1.0 claim is made against `worldsim.term` and the
card is asked to move the price; and its slot-discipline test asserted
`SLOT_OF == {}` to document the empty-slot era, which the deposit slot ends.

**One thing to feel at the table.** The Tile block is a fuller page than it
was — on a busy Tile it is the header, the character phrase, the tags, the
harvest, the mine, the goods, four roads and the Areas. That is the whole
point of the arc and it should read as a place rather than a coordinate,
but it is worth watching in play whether the character phrase earns its
line on the 227 Tiles that are farmland, hill country or wine country. If
it does not, the cheapest cut is to print it only where it says something
the ground word does not.

**Parked on the way**: the arc's two round-4 leftovers (a Hanse-shaped
authored northern circuit, an Ardennes-shaped western wildwood mark) moved
into plan.md's own section as Part 1 was deleted, joined by the two unused
land-character rows and the plains fall-through. Nothing else was parked: the arc is closed.

## 2026-08-21 (J) — The medieval world arc: nine countries, tongues & the rolled wars (design)

The designer asked for the full, rounded-out design of a big change,
delivered straight into plan.md as a build contract: replace the
three-country world with a nine-country one, only Tergal keeping its
name; give Thule (pagan vikings) a small deck of its own scoped like
Tergal's; author settlement and person names for every new country plus a
real historical town name per town-capable tile; give party members
tongues (Latin plus the homeland's, a random extra for Byzantines); roll
three standing wars at every new game from six historical templates and
run a cosmetic campaign sim over their theaters using the conquest
system; and remove the old main conquest questline. All open choices were
delegated. The result is plan.md's THE MEDIEVAL WORLD ARC — Part 1, five
sessions; this entry records the road and the calls.

**The load-bearing move is the COUNTRY/CULTURE split.** Nine countries
would be unaffordable if each owed what Firascir owed (53 cards, 12
templates, a quest table, two name pools). Instead identity and content
part ways: a COUNTRY owns tiles, capital, tongue, name pools, facts and
wars; a CULTURE owns the reusable content, and there are only four —
western (the Firascir packet, now serving Phyrascia, Seraptania, Teutonia
and Vellisclavia), southern (the Mortellaria packet, serving Byzantium,
Andalusia and Umaia), steppe (Tergal), and norse (Thule, new). The card
record already takes a land tuple, so the mechanism is a `CULTURES` map
and re-keyed ids, not new machinery. The catalog gets the same split
(version 3: `cultures` for templates and inventories, `lands` for
identity).

**The map became an authored artifact.** `country_at` is today a
two-line geometric rule; it becomes a fourth overlay grid
(`resources/europe_countries.txt`), and the draft grid was drawn in this
session and verified against the real census code: 314 land tiles
partition into 13/23/28/37/60/51/17/60/25
(p/s/t/h/v/b/a/u/g), every historical city and mine landing with a
historically sensible owner without moving a tile — Goslar, Kutna Hora,
Luneburg and Erzberg to Teutonia; Wieliczka and Banska Stiavnica to
Vellisclavia; Melle to Seraptania; Falun to Thule; Novo Brdo to
Byzantium. Sea tiles take the nearest land tile's country by rule
(north-then-west ties), not paint.

**Calls settled in this session**, so they stay settled:

- **Kyiv stays Tergal's capital.** The user's brief said Tergal is
  "same"; its capital today is Kyiv, and the horde seated in a taken
  river city is the Golden Horde pattern. The alternative (Kyiv to
  Vellisclavia, an authored Sarai in the east) was weighed and declined
  for churn without gain; Vellisclavia's Rus identity rests on Moscow,
  Warsaw and a build-time Novgorod. Cheap to reverse if it reads wrong.
- **Seraptania loses its Mediterranean coast** to Byzantium — (11,10)
  and (11,11) — per the brief; the Low Countries and the east Alps went
  to Teutonia (so Amsterdam and Erzberg are imperial), the west Alps and
  everything south to Byzantium, the Carpathian mines to Vellisclavia.
- **Byzantium is the southern heir**: Latin tongue, the four great
  southern cities, and the land-specific Mortellarian identity (death
  rite, carnival, academy, schism) narrows to it alone in the card
  audit; Umaia and Andalusia share only the culture-generic south.
- **Three historical cities added**: Cordoba (Andalusia's capital),
  Cairo (Umaia's capital and the FOURTH metropolis — the biggest city of
  the age), Jerusalem (a town, the crusade's prize). Capitals grow to
  nine; the sky-anchor rule is unchanged.
- **Vassalage is a d3** — Byzantium's vassal / Umaia's / independent —
  stored as `lands["andalusia"]["liege"]`, read by the readouts and the
  Reconquista template, nothing else yet.
- **The name check was actually run**: ~615 settlements a world; the
  town-capable tiles (mid/high/dense bands, campaign-invariant) number
  exactly 185, so the real-town table needs ~160 new authored names on
  top of the 25 authored tiles; villages stay invented-generic on
  purpose. Pools: city 4 / town 6 / village 24-or-16 / hamlet 10 per
  country, with wholesale reuse (Firascir pools -> Phyrascia,
  Mortellaria pools -> Byzantium, Tergal keeps its own) so only six
  settlement pool sets and seven person-name lists are authored new.
- **Tongues are a recorded fact plus a dm.md rule, not an engine gate.**
  Latin is Byzantium's tongue and the church-and-scholars tongue
  everywhere, which is why every character speaks it — the party is
  never soft-locked out of a country, only textured in it.
- **Wars are static, like the year.** Rolled once at worldgen (three
  distinct of six, no exclusion rules — the age ran its wars
  concurrently), standing for the whole campaign, smouldering through a
  lazy day-stepped sim in conquest.py that reuses the garrison authority
  for sieges and writes ordinary since-stamped states (war-raided,
  war-camp, battlefield, under-siege, sacked, occupied capped at 2) with
  hard caps and expiries. It never redraws a border, never touches
  boards or holdings, never ends. Dynamic borders stay parked.
- **The old conquest questline (story.py) is removed first**, whole —
  session 1 — so no later session renames a line of it. The worldsim war
  feed (CASUS_BELLI and kin) goes with its one customer; the war
  templates carry authored herald lines instead; post_news survives with
  the campaign sim as its next customer. conquest.py's player holdings
  layer stays untouched except seize_by_occupation.

**Session order was forced by green-ness**: the removal first; then the
map session must carry names, catalog, plumbing AND a mechanically
re-keyed worldsim (with a two-item Thule stub the validator demands),
because a nine-land world with a three-land world layer does not boot;
the town table and tongues are additive and come third; the full norse
packet, the card audit and the ~20-edge relations table fourth; the wars
last, on top of everything. The roadmap's "Politics, war & more
countries" section collapsed into the contract, leaving dynamic borders,
mechanical languages and vassalage-with-teeth parked.

## 2026-08-21 (K) — Session 1 of the medieval world arc: the fallen banner (the conquest questline removed)

**What shipped: a deletion.** plan.md's Session 1 whole. The scripted
main quest — one aggressor country, four war waves pinned at levels
2/5/8/10, the Golden Empire / Undead Kingdom / Iron Horde, the scripted
wave-3 fall and the occupation that followed it — is gone from the game,
code, docs and tests. It was three-country content at its core, the
rolled wars of session 5 replace its job, and taking it out first means
no later session in this arc renames a line of it. The game runs
warless: a new game prints no war line at all, and nothing on the board,
the map page, the status page or the save mentions a war.

**The death list.**

- **`story.py` deleted whole** (527 lines): `CONQUESTS`, `AGGRESSORS`,
  `WAVE_LEVELS` / `WAVE_ENCOUNTERS` / `WAVE_ROOMS`, `init_story`,
  `next_wave_due`, `wave_target_land`, `post_wave`, `on_wave_done`,
  `occupied`, `casus_belli_line`, `war_status_lines` and its `main`.
- **`session.py`**: `init_story` at `new` and the "the story layer is
  armed" print with its level-2/already-due branch; the `"story"` key in
  both `save` and `load`; `war_status_lines` in `status_lines` and in
  `map_sheet_lines` (with the `-- the war --` block and the
  `[UNDER THE YOKE]` land tag); `maybe_post_wave` and its six call
  sites (board, arrive, tavern, downtime, healer, teleport);
  `occupied_here` / `occupation_line` and all nine gates (recruit, take,
  board, tavern, downtime, healer, conquer, hell's assignment, the
  delivery hand-off); the wave-completion hook in `advance_quest`
  (the THE WAR record line and `on_wave_done`); `story_wave` in
  `pays_here` and in the `FEROCITY_RELENTLESS` spawn (the import went
  with it); and the help copy naming war waves.
- **`worldsim.py`**: `CASUS_BELLI`, `STANDING_CASUS_BELLI`,
  `roll_casus_belli`, `casus_belli_line` and the format-check clause in
  `_validate_politics_tables`. **`post_news` stays** — the campaign sim
  of session 5 is its next customer, and its docstring now says so
  without naming a customer that no longer exists.
- **`quests.py`**: the `story_wave` clause in `is_ordinary_posting` (the
  forced families are now delivery / world card / hell task / forced).
- **`conquest.py`**: `seize_by_occupation` only. The player's own
  holdings layer — conquer, garrison, holdings, tribute, raids, the heat
  floor — is untouched.
- **Tests**: `test_worldsim.TheWarFeed` (4 tests), `test_places`'s two
  story tests (the fixed banner pairing and the four-wave build sweep),
  `test_conquest.TheYokeOutranksTheFlag`,
  `test_quest_geography`'s story-wave posting, and `test_turnin`'s
  war-wave pay routing. Every state stub dropped `"story"`. 948 tests
  before, **939 after, OK**.

**Docs.** rules.md's add-on lost its questline half and is now *The Story
Layer — Add-on (2026-07-12; questline cut 2026-08-21)*, with a paragraph
at its head recording what was cut and why; the givers, epilogues, the
targeted NPC generator, the central cast and party chatter all stay.
Politics & the Ruler lost its casus-belli bullet and its section is now
"The war material" (the instruments and the succession cluster). dm.md
lost "The war -- the conquest questline" whole plus every war-wave
mention in the clock, turn-in, record, conquest and narration sections.
develop.md lost story.py's Files entry and rewrote the war plumbing out
of the session.py entry, the dev map's story-layer and politics rungs,
and the conquest/test_conquest entries. CLAUDE.md's code-file list lost
`story.py`.

**The calls the spec left open, and how the build settled them.**

1. **What replaces a war-flavoured comparison, rather than what deletes
   it.** A dozen docs and docstrings used the war waves as the reference
   shape for something else — hell's ten pins ("the war waves' proven
   shape"), the conquest job's room count ("the war waves' maximum"),
   how a conquest job is taken ("like a war wave"), the named-kill
   doctrine ("one of the war's lieutenants"). Each was rewritten to
   state the thing directly instead of pointing at a system that no
   longer exists; none of the numbers moved. The rule applied: a
   comparison to deleted content is a dangling reference even when it
   compiles.
2. **The occupation gates were removed, not neutered.** Nine commands
   asked `occupied_here(state)` before doing their work. Deleting the
   reader and leaving the guards would have meant nine `if False`
   branches; deleting both leaves the commands reading as they did
   before the war existed. The `--here` turn-in valve survives — the DM
   still needs it for a dead giver — with its help text pointing at a
   burned town rather than an occupied one.
3. **`FEROCITY_RELENTLESS` left session.py with the waves.** War-wave
   foes were the only rosters the session layer spawned relentless;
   with them gone the import was dead. `sites.py` still uses the
   constant for the catalog rows that carry it, so nothing about
   ferocity itself changed.
4. **`test_start` kept a test where one was deleted.** The old
   `test_the_war_line_stops_promising_level_two_to_a_career_party`
   pinned the new-game war print. Rather than delete it outright, it
   became `test_a_new_game_says_nothing_about_a_war`, which asserts the
   interim contract at both a level-1 and a career start — the arc's
   later sessions will put a war back, and this is what says the world
   in between is genuinely warless.
5. **worldsim.md was not touched.** Its war-feed mentions are its record
   of what the politics session SHIPPED on 2026-08-10, and project
   history is not edited (the file's own rule). designlog and benchlog
   likewise keep their war-wave entries.

**Not re-measured.** Nothing tunable moved: no constant, no pay formula,
no threat number. The bench suite is unaffected and benchlog gets no
entry.

## 2026-08-21 (L) — Session 2 of the medieval world arc: the map of nine

**What shipped.** plan.md's Session 2 whole: the world builds and plays
as NINE countries over FOUR cultures. A country owns identity — its
tiles, its capital, its tongue, its name pools, its ruler's title, its
League chapter; a culture owns the reusable content — settlement
templates, natural inventories, quest tables and the world layer's card
packet. Nothing about the census, the harvest, the routes or the read
surface changed: this session re-drew who owns the map and re-keyed the
catalogs that hung off the old three.

**The country overlay.** `resources/europe_countries.txt` is the fourth
authored 30x18 grid, one letter on each of the 314 land tiles and `.` on
the sea. `places.country_at` reads it instead of the geometric split (a
row test and a column test) that the human contraction had left behind,
and a SEA tile derives its country from the nearest land tile by tile
distance, ties settled north-then-west the way the pathfinder settles an
equal-cost route — so nothing about the water is hand-painted and there
is no ambiguity. The `border` tag stays derived. Two censuses are pinned
off the grid and checked at every worldgen by the new
`places._validate_countries`: `PINNED_COUNTRY_BIOMES` (which replaced the
three-country version) and the new `PINNED_COUNTRY_BANDS`, which is
authored data for the same reason — the population band reads only the
ground and the shoreline, so a country's shape in the six bands moves
when the overlay is repainted and never otherwise.

**The historical cities.** The sixteen keep their tiles and tiers and
take their new owners, and three are added: **Cordoba** (14,4), city,
Andalusia's capital; **Cairo** (18,24), METROPOLIS on the Nile and the
biggest city of the age, Umaia's capital; **Jerusalem** (16,27), town,
Umaia. `CAPITAL_TILES` is nine — London, Paris, Prague, Stockholm,
Moscow, Constantinople, Cordoba, Cairo, Kyiv — and each land's sky is
read off its own capital exactly as before. Rome is no longer a capital;
Constantinople is the southern empire's seat.

**The catalog, version 3.** `place_catalog.json` split in two at the top
level: `cultures` (the Firascir, Mortellaria and Tergal content moved
under `western`, `southern` and `steppe` UNCHANGED, plus the new `norse`)
and `lands` (nine records of `name` / `culture` / `tongue` /
`description` and nothing else). `places.CULTURE_SPECS` / `CULTURE_OF` /
`CULTURE_LANDS` are the readers, `template_id` and `natural_template` are
keyed by culture, and `validate_catalog` learned the shape: version 3,
nine lands, every land naming a real culture and carrying a letter on the
overlay, no culture unworn, and the old per-tier and per-character rules
applied to cultures instead of countries.

**The norse culture, authored new**: eight settlement roles (the
sea-king's harbor capital, a walled city, a harbor town, a market town, a
shore village, a wood village, a field village and a cot hamlet) and four
natural inventories of three sites each (`taiga_wood`, `fells`,
`skerry_coast`, `river_north`) mapped over the seven land characters.
Its houses eat barley bread and salt fish over a long hearth.

**The names.** One pool per COUNTRY, not per culture — a name is the most
country-shaped thing in the game, and Seraptania and Teutonia share a
card deck without sharing a syllable. Phyrascia inherits Firascir's
settlement pools and person names whole, Byzantium inherits
Mortellaria's settlement pools, Tergal keeps both of its own, and the
other six settlement pools and the other seven person-name lists (25
male + 25 female each) are authored to the contract's sound briefs.

**The plumbing sweep.** `HOMELANDS` is nine. `quests.TEMPLATES` and
`wild_pool` re-key by culture and the norse table is five authored
templates — the beached longship, the winter pack, the barrow on the
headland, the trolls in the fells and the blood in the grove.
`quests.RULER_TITLES` and `conquest.DEFENDER_ROLES` grew to nine rows
(what a crown is called is identity, so those did NOT re-key by culture);
`garrison_pool` stays `LADDER_POOL` for all. `worldsim` was re-keyed
MECHANICALLY, which is what let the game run in one session: card,
option, fact and faction-edge ids `firascir/*` -> `western/*` and
`mortellaria/*` -> `southern/*`, `land=` fields naming cultures, and one
door between the two vocabularies — `worldsim._expand`, which resolves an
authored culture name into land keys and leaves ANY_LAND and a bare land
key alone. `_by_land` does the same for the tables every reader indexes
by land (constitutions, tensions, standing tensions).
`_validate_three_countries` became `_validate_countries`. Thule got the
minimum the frame demands as real content: THE GROVE, its League chapter
fact, one relation edge (the raiding season), two constitutions and two
tensions with their four blocs. The Miners' League land facts re-homed to
the actual owners under the overlay — Teutonia (Goslar, Kutna Hora,
Luneburg, Erzberg), Vellisclavia (Banska Stiavnica, Wieliczka),
Seraptania (Melle), Byzantium (Novo Brdo), Thule (Falun).

**The calls the spec left open, and how the build settled them.**

1. **The pinned band census is the MEASURED one, not the contract's.**
   The grid shipped exactly as drafted and its land counts match the
   contract to the tile (13/23/28/37/60/51/17/60/25). The BAND row
   differs for four countries: Vellisclavia 18/8/5/15/14 against
   15/11/5/14/15, Byzantium 1/5/4/21/10/10 against 1/5/3/22/10/10, Umaia
   17/3/0/9/27/4 against 4/16/0/8/28/4, Tergal 3/3/8/9/2 against
   1/5/7/10/2. The shipped numbers are what `places.population_band`
   actually returns over a built world, so they are what got pinned. The
   consequence for a LATER session: plan.md's Session 3 counts the tiles
   that can ever roll a town or city as 185 (Byzantium 42, Tergal 12);
   the measured figure is **183** (Byzantium 41, Tergal 11), and the
   town-name table wants that many rows.
2. **Relations expand by CULTURE, which is why Thule needed exactly one
   edge.** The 14 authored edges name cultures now and `RELATIONS` is
   their land-by-land cross product (96 edges), which is what makes every
   land except Thule reachable without re-authoring anything. It is
   deliberately crude — Phyrascia derives `pact-kin` off Umaia's marriage
   pact — and session 4 re-authors the table whole for nine lands, which
   is where that gets fixed. `derived_states` dedupes by the derived
   word, so the crudeness costs nothing at the table today.
3. **Byzantium's village pool is 21, not the contract's 24.** The
   contract lists Byzantium among the 24-village countries AND says it
   inherits Mortellaria's pools whole. Inheritance won: the pools are
   Mortellaria's unchanged, and only the six genuinely new countries were
   authored to the stated sizes.
4. **Two authored inventories died with the old borders, and one moved.**
   The steppe's `taiga_wood` had no ground left — Tergal is the Pontic
   steppe now and holds no deep-forest tile — so it was cut and the
   steppe's `forest` character points at `great_fen`, which is what a
   wooded tile in the Pripet actually is. The norse `river_north` is
   drawn on Thule's COAST alternating with `skerry_coast` (a northern
   shore is skerries or a river mouth), because Thule holds no river and
   no marsh tile and the shipped no-dead-inventory contract forbids
   authoring one that nothing draws.
5. **Three settlement roles are now unreachable BY DESIGN, and the suite
   says so.** `validate_catalog` makes every culture keep a role per tier
   that asks for no Tile tag, so no Tile can ever draw nothing. Neither
   Tergal nor Thule holds a dense-band tile, so no generated city ever
   rolls there and their `walled_city` roles are pure guarantee; every
   Thule tile is coast or forest, so its `field_village` is too.
   `test_places` pins that set of three rather than asserting every
   authored role is drawn.
6. **`land_lines` learned to wrap.** A land's state diff could overflow
   the 40-column page whenever a long state word met a long clock stamp;
   it always could, and the re-keyed content is what finally produced one
   ("the village will not pay (day 1)", 43 columns). `places._detail_wrap`
   became public `places.detail_wrap` and the world layer wraps by it
   rather than keeping a copy of the rule. The page still says three
   things at most.
7. **Ruler titles did NOT become culture content.** They are the one
   homeland-keyed table that reads as identity rather than as reusable
   content, so nine rows: king, emperor, grand prince, sea-king, sultan,
   prince, high chief. `conquest.DEFENDER_ROLES` went the same way for
   the same reason.
8. **The steppe's `ridge_town` needed a wider sweep to prove.** Tergal is
   a quarter of its old size, so `test_places`' template sweep runs 12
   seeds instead of 4 to reach every reachable role.

**Measured** (benchlog 2026-08-21 (E)): the three worldgen sweeps moved
where the three new cities are and nowhere else. Cairo makes the
metropolis count 4 and adds ~178k souls; nine capitals instead of three
re-aim the capital-bound trade rule, which is the whole of the trade
column's movement (routes 58.7 -> 59.0, land tiles on a road 113.7 ->
115.7, crossroads 33.6 -> 31.7). The harvest layer is unmoved except for
the nearby-trouble nudge (86% -> 87%), which reads the start tile and the
start draw moved with the three new authored slots.

**The suite.** 939 tests before, **944 after, OK.**
`test_places.TheThreeHumanCountries` became `TheNineCountries` — the
closed homeland set over nine, the four cultures carrying the shared
content, each country's own names and tongue, the overlay painting land
and deriving sea, both country censuses pinned, every country owed a
deck, lore, a relation, a constitution, a tension and a capital, and
every capital standing on its own ground. The removed-peoples sweep is
unchanged and still passes. The border-seam test moved off column 21 to
the drawn Seraptania/Teutonia seam at (9,11)-(9,12).

## 2026-08-22 (M) — Session 3 of the medieval world arc: the towns & the tongues

**What shipped.** plan.md's Session 3 whole, and it is two small features
that share nothing but a date. The map's towns have REAL NAMES: 164
authored historical towns, one for every tile that can ever seat a town
and that no historical city and no mine already names, taken by the tile's
chief settlement when the census gives it town tier or better. And the
nine countries have TONGUES on the sheet: everyone speaks Latin plus their
homeland's, a Byzantine speaks Latin plus one other, and the party board
prints a SPEAKS row. No law moved, no number moved, and
`bench_worldgen.py --seeds 500` came back byte-identical to session 2's
run (benchlog 2026-08-22).

**The town-name table.** `places.TILE_TOWN_NAMES` is the map's third
authored answer key, under `HISTORICAL_CITIES` and `MINES`. The tiles a
town or a city can ever be rolled on are exactly the mid, high and dense
band tiles — **183 of 314**, campaign-invariant, because the population
score reads only the ground and the shoreline. Nineteen carry a historical
city or a mine town already (sixteen of the nineteen cities are in a
town-capable band; Prague, Stockholm and Cordoba are not, and only three
of the nine mines are — Luneburg, Kutna Hora and Novo Brdo). The other
**164 are the table**, and its per-country census is Phyrascia 9,
Seraptania 20, Teutonia 13, Thule 4, Vellisclavia 27, Byzantium 36,
Andalusia 8, Umaia 37, Tergal 10.

The rule is one line in `materialize_slot`: a slot with no authored name
asks `tile_town_name(tile, slot)` before falling through to the generic
pool, and that reader answers only for the CHIEF slot (index 1) and only
at `TOWN_GRADE` — town, city or metropolis. A second town on the same
tile and everything from village down draws the country pool as before.
That makes "a tile's town name is used at most once" STRUCTURAL rather
than bookkept: one slot per tile can claim it and a slot materializes
once, so the session added no stored state and nothing new rides the save.
`_validate_town_names` is the lint (the table covers exactly the tiles
owed a name, names nothing else, and no name is authored twice across the
three tables); it runs inside `_validate_countries`' existing sweep, which
already computes every tile's band, rather than walking the world again.

**The tongues.** `people.LANGUAGES` maps country to tongue but does not
own the words — it READS `places.LAND_SPECS`, because a country's tongue
is already in the catalog beside its name and its culture, and a second
copy would drift. `LATIN` is Byzantium's, and it is also the church's, the
schools' and the chanceries' language everywhere in the west, which is why
everyone has it: the party can always talk to a priest, a scholar or a
clerk, and cannot necessarily talk to a farmer. `roll_tongues` is called
from `make_character`, so the PC, the long-time companion, every recruit
and every half of a pair carry the list; `rpg.Entity.tongues` rides
`dataclasses.asdict` into the save like every other field. Dict NPCs carry
no key at all. Nothing in the engine gates on a tongue — dm.md's "The
tongues at the table" is the whole of the rule in play, and plan.md's
"Languages with mechanics" is where an engine reader would be designed.

**The calls the spec left open, and how the build settled them.**

1. **164 names, not the contract's ~160, and the per-country counts are
   the MEASURED ones.** Session 2's build record already corrected the
   contract's 185 town-capable tiles to 183 (Byzantium 41, Tergal 11);
   the rest of the contract's per-country row was drafted against the
   same stale census and is off almost everywhere. The shipped counts are
   what `population_band` returns over a built world and are pinned in
   `test_towns.TOWNS_PER_COUNTRY` and in `places._validate_town_names`'s
   coverage clause, which is stricter: it names the tiles, not the totals.
2. **Uppsala could not be placed, and that is the overlay's answer, not
   an omission.** The contract lists it among the wanted names. Sweden's
   tiles on the country overlay — rows 2-3, columns 21-26 — are entirely
   in the THIN band, so no tile there can ever seat a town; Stockholm and
   Falun are the only named places in that half of Thule and both are
   authored elsewhere. Thule's four town-capable tiles are one on the
   northern Norwegian coast and three on the Danish approaches, and they
   took Trondheim, Roskilde, Lund and Ribe. Every other name the contract
   listed is on the map.
3. **Placement is by plausibility, never by projection.** The drawn map
   is a squashed Europe (the scale doctrine: ~160 km a column against
   ~220 km a row) and its east is compressed hard — Athens and
   Constantinople sit eight columns apart. So each name was placed for
   the COUNTRY that owns its tile under the overlay, the coast/river/hill
   ground the overlays actually put there, and the right order relative
   to its neighbours; nothing was fitted to a real coordinate. Three
   consequences worth writing down: the Danube corridor (row 11, columns
   16-23) is Byzantium's under the overlay, so Vienna, Pressburg and Buda
   are Byzantine towns; Bruges is Seraptanian, because the overlay draws
   the Flanders tile into France and only Amsterdam and the Low Countries
   proper into Teutonia; and Sarai sits on Tergal's far south-eastern
   tile because that is the horde's farthest ground on this map.
4. **A real name beat a shipped invented one.** Tergal's hamlet pool
   contained `Sarai` — an invented steppe word that happens to be the
   Golden Horde's capital. The town took it and the pool entry became
   `Saruk` (same sound, same length). It is the only shipped name this
   session changed, and the suite now pins that no authored town name
   collides with any generic pool.
5. **A chief VILLAGE leaves its tile's town name unspent.** The rule
   keys on the chief slot's tier, not on the tile's band, so a
   high-band tile that rolled `VVV` simply does not use its name that
   campaign. The alternative — hand the name to the first town wherever
   it sits on the tile — was declined: it would put York in the shadow
   of the village that leads the tile, and the chief slot is what the
   census means by "the place this tile is".
6. **The SPEAKS row is lowercase on the page.** plan.md capitalises
   "SPEAKS" the way it capitalises every concept; the party board's
   neighbours are `abilities:`, `alchemy`, `satisfaction`, so the row
   renders as `speaks: Latin, Phyrascian`. It is printed both by
   `people.character_sheet` (the pre-hiring sheet) and by
   `session.hero_block_lines` (the party board and `status`), so a
   candidate and a hired companion read the same.
7. **`LANGUAGES` reads the catalog rather than owning a copy.** The
   contract says people.py owns it. It owns the mapping and the roll; the
   WORDS stay in `place_catalog.json`'s land records, where session 2 put
   them. A duplicated table of nine strings is exactly the kind of reader
   the no-backwards-compatibility rule warns about — it cannot be wrong
   loudly, only quietly.
8. **Two stale lines in rules.md were corrected in passing.** The census
   section still said "Paris, Venice and Constantinople are the three
   metropolises" and "`capital` remains an explicit FLAG on Paris, Rome
   and Kyiv" — both true before session 2 added Cairo, Cordoba and
   Jerusalem and nine capitals. The measured census line beside them
   (615 settlements, 1.3M souls) was refreshed to the shipped 618 and
   1.5M at the same time.

**Measured** (benchlog 2026-08-22): `bench_worldgen.py --seeds 500` is
identical to session 2's run line for line, including the spoken harvest
words. That is the predicted result — the names are read at
materialization, which no bench performs, and the tongue roll is inside
`people.make_character`, which no bench imports. Nothing was tuned.

**The suite.** 944 tests before, **976 after, OK.** The new
`test_towns.py` is the session's contract suite in four parts: the town-name
table (the 183/19/164 split, the per-country census, no name authored
twice or colliding with a pool, ASCII and inside the page, the
town-capable set identical across seeds, and four broken worlds), the
naming rule (the chief town, the chief village that leaves it unspent, the
second town, the authored slot, no name spent twice in a whole revealed
world, no village wearing a real one, the save and the seed), the tongues
(the nine off the catalog, both branches of the roll, the sweep that
reaches all eight of a Byzantine's possible seconds, and the NPC and the
sim body that carry none) and the SPEAKS line (both sheets, the absent
row, the save round-trip, and a real `new --seed 5 --level 1`).

## 2026-08-22 (N) — Session 4 of the medieval world arc: the norse packet & the nine-land relations

**What shipped.** plan.md's Session 4 whole, and it is three pieces of one
job: Thule stopped being a stub, the two big re-keyed packets were read
once against their new scope, and the relations table was re-authored land
to land. Nothing about the ground, the census, the harvest or the routes
moved: `bench_worldgen.py --seeds 500` came back identical to session 3's
run (benchlog 2026-08-22 (B)).

**The Thule deck**, scoped exactly like Tergal's. Eighteen crisis cards of
its own, spread over the four content tuples the way the steppe's are: the
sea and the year in the base deck (`norse/raid-season`, `herring-run`,
`whale-ashore`, `ice-locked`, `wolf-winter`, `danegeld`), the law and the
hall in politics (`kings-share`, `ring-giver-poor`, `the-thing`,
`outlawed`, `land-taking`, `blood-feud`, `weregild`), the grove and the
sea's own dead in religion (`grove-sacrifice`, `curse-pole`,
`drowned-crew`) and the seer and the oath in magic (`seer-speaks`,
`berserk-oath`). Plus the crown cluster, which already named `norse` in
`_CROWNED`, and one weather card, `norse/white-storm`. Four tensions —
the jarls against the assembly, the sea-kings against the land-chiefs, the
old gods against the missionaries, and two houses counting their dead —
over eight blocs, with six faction edges, at least one on every axis.
Seven facts: THE GROVE and the Falun League chapter from session 2, plus
THE SHIP BURIAL, THE THREAD OF FATES, THE LAND-SPIRITS, THE DROWNED BELONG
TO THE SEA and THE LAW AT THE STONE. One option, `norse/weather-witch` —
wind out of a knotted cord, `does="sky"`, the rain stone's cousin. Four
constitutions, default-heavy 6/2/1/1: THE SEA-KINGS, THE ALLTHING, THE
HIGH KING, THE SCATTERED JARLS.

**The card audit, and every call it settled.** Every re-keyed `western/*`
and `southern/*` card was read once. The DEFAULT held for the large
majority — 71 cards read, 13 narrowed:

- **To BYZANTIUM, the southern heir** (the call was already made at design
  time, designlog (J); the audit is where it became data): the whole
  death-face cluster. `southern/day-of-the-dead`, `southern/carnival`,
  `southern/penance-season`, `southern/two-hoods`, `southern/debate-riot`,
  `southern/necromancy-open` and `southern/necromancy-purge` re-keyed to
  `byzantium/*`; the `penitents-vs-carnival` TENSION and its two faction
  edges went with them, and so did three facts — THE PENDULUM CALENDAR,
  BONE ARCHITECTURE and THE NECROMANTIC AFFINITY. Andalusia and Umaia
  keep the culture-generic south (THE BURIAL BROTHERHOODS, THE ACADEMY)
  and none of the death-face.
- **`southern/basement-children` and `southern/brotherhoods` did NOT
  narrow.** The contract names "the academy necromancers", not the
  academy: a wizarding university per southern kingdom is culture
  content, and only its necromancy chair is Byzantium's. The burial
  brotherhoods stayed for the same reason and because a southern option
  (`southern/brotherhood`) prices them.
- **`communion/the-synod` to Byzantium AND Seraptania.** The schism clock
  is now a two-crown argument, so the card that stands in it sits in
  exactly those two decks. It is the one card in the game that names two
  lands of two different cultures, and the suite exempts it by name.
- **`weather/smog` to TEUTONIA**, per the contract: the close-built
  northern town with a forge in every second yard is the free cities'
  shape.
- **Four cards moved to the land their re-aimed edge points at**, because
  a card that reads a derived word has to sit where the word lands:
  `western/settled-warband` -> `vellisclavia/settled-warband` (the only
  western kingdom with the steppe at its back, and the only card whose
  text says "Tergal"), `western/hostage-in-the-camp` ->
  `vellisclavia/*`, `southern/kin-claim` -> `phyrascia/kin-claim` (the
  marriage runs Seraptania -> Phyrascia now), `southern/union-inherits`
  -> `seraptania/*` and `southern/danegeld` -> `phyrascia/danegeld`,
  re-written from a province paying steppe chiefs to a kingdom paying the
  northern fleet.
- **Three cards had text neutralised rather than scope narrowed.**
  `western/marriage-pact` said "sealed with the southern crown" and
  `western/broken-betrothal` had a "southern envoy" and a "southern road";
  both are drawn by four western kingdoms whose partners differ, so the
  prose lost the direction instead of the card losing three lands.
- **Nothing else in either packet names a river, a coast or a city.** The
  audit looked: the western manor cards, the shrine cards and the
  southern finance cards are all written to a generic parish, square or
  quarter, which is why they survived the country split without a word
  changing.

**The relations table, re-authored whole.** Twenty hand-placed LAND-TO-LAND
edges replace session 2's 14-authored / 96-expanded culture cross product,
and every one of the nine countries is reached. Two grain roads (the
Baltic one Vellisclavia -> Thule, the Nile one Umaia -> Byzantium), three
raiding edges (the horde at Vellisclavia, the ships at Phyrascia and
Seraptania), Thule's timber to Seraptania, Lombard coin to Seraptania, the
southern road to Teutonia, the gold caravans to Andalusia, horses twice
(Tergal -> Vellisclavia, Andalusia -> Seraptania), livestock and hired
swords to Byzantium, the wool axis Phyrascia -> Teutonia, the four
diplomatic instruments re-aimed, and the schism clock both ways between
Byzantium and Seraptania. `RELATIONS` is still `_RELATIONS` expanded and
is now a 1:1 expansion, which keeps the door open for a future culture
edge without pretending one exists.

**Signature facts.** Six new, one per country that had only its culture's
lore: THE WOOL (Phyrascia), THE KING'S TOUCH (Seraptania), THE ELECTORS
(Teutonia), THE FROZEN ROAD (Vellisclavia), THE WATER COURT (Andalusia),
THE FLOOD MARK (Umaia). The floor the suite now pins is not a count but a
shape: every land has at least one fact whose `land` is exactly itself.

**The calls the spec left open, and how the build settled them.**

1. **`_by_land` became ADDITIVE.** A land-specific TENSION was the one
   thing the narrowing needed that the mechanism could not do: the old
   `_by_land` REPLACED a culture's row with a land's, so Byzantium would
   have had to repeat the whole southern list to add one line. It now
   concatenates — a land's row is its culture's entries followed by its
   own. Constitutions run through the same function and no land adds one,
   so that half is unchanged.
2. **A narrowed card's id is re-keyed to its LAND.** `southern/carnival`
   became `byzantium/carnival`, because an id in a culture's namespace
   that only one country draws is a lie the next reader has to unpick.
   The TRACK namespaces are exempt and stay as they are — `weather/`,
   `crown/`, `mining/`, `communion/`, `magic/`, `sun/` name a track or an
   argument, not a packet, and `weather/dust-storm` has been a
   Tergal-only card under a track namespace since the weather session.
3. **`rain-bought` became `sky-bought`.** Two weather-workers in one game
   cannot share a state word named after one of their skies, and
   `hire_weather` hardcoded it. One rename, one marker, and the invariant
   the suite now pins is that no land can hold two bought skies.
4. **A live weather card still outranks a bought sky, and the witch will
   not sell into a standing storm.** `_roll_sky` has always let a card
   that IS the weather hold the day over a paid one — the alternative is
   a state readout saying "the white storm has shut the coast" over a
   sunny wind. Since the norse card sets its sky far more often than the
   steppe's dust storm does, the option gained
   `without=("sky-bought", "white-storm")`: you cannot hire wind while
   the storm stands. A storm arriving DURING a paid window still takes
   the days, and that is the rule, not a bug.
5. **`norse/white-storm` does not admit on `wind`.** It was drafted
   `("snow", "storm", "wind")`, which meant paying the witch for wind was
   the best way to invite the card that cancels it. A white storm sets in
   out of snow or a storm; the wind row came out.
6. **Two state words are shared with the steppe and were re-worded for
   both.** The contract has `norse/raid-season` set `raiding` and
   `norse/danegeld` set `tribute-taken`, both of which already existed
   with Tergal wording ("the clans are riding", "a chief is paid to keep
   the peace"). Adding norse twins would have doubled two words for no
   mechanical gain and broken the two relation edges that read them, so
   the READOUT went neutral ("the raiding season is on", "a war-leader is
   paid to stay home") and the card's news line carries whether it was
   horses or ships.
7. **The nithing pole and the shaming pole both stand.** Tergal already
   had `shaming-pole` and the contract asks for `norse/curse-pole`. They
   are the same custom in two cultures and both were kept: the cards
   never meet, the state words differ, and cutting one would have thinned
   a packet to avoid a coincidence the player cannot see.
8. **`thing-sitting`, not `the-thing`, is the state word.** The card is
   `norse/the-thing` per the contract; the state it holds had to say what
   is happening rather than name an institution, or the readout line
   ("the assembly is sitting at the stone") would have read as a noun.
9. **Thule's `feud` tension carries a faction edge and its own two-card
   chain.** The contract gives six edges over four tensions without
   saying how to spread them; two axes could have taken three each. One
   edge per axis with the two contested ones taking two keeps every
   rolled tension a live quarrel — a tension that gates cards but has no
   edge in it is a name, not an axis.
10. **The era anchor and the colony cards are a KNOWN clash, deliberately
    left.** `southern/colony-fleet`, `southern/monopoly-bubble` and
    `southern/the-crash` are three cards about colonial trade and colony
    shares, and the arc's era anchor is "about 1500 WITHOUT the age of
    exploration". The audit surfaced it and did not act: the audit's axis
    is SCOPE (which land draws a card), the era is a different axis, and
    re-writing three cards' fiction is a sitting of its own. Written down
    here so the next content session can take it.

**Measured** (benchlog 2026-08-22 (B)): `bench_worldgen.py --seeds 500`
line for line identical to session 3's. Predicted and confirmed — the
bench imports `places` and nothing else, and this session touched only
`worldsim.py`. Nothing was tuned; no lever moved.

**The suite.** 976 tests before, **988 after, OK.** The new
`TheCardAudit` class is the audit's own contract (the thirteen narrowed
cards by name and land, the default still culture-wide everywhere else,
the id namespace rule, Byzantium's exclusive pendulum calendar, the
additive `_by_land`, and the rule that no card names a country that does
not hold it). `TheLastTwoRecordKinds` gained the norse packet's shape
(deck floor, four rollable tensions each gating cards, six edges, seven
facts, one option, four constitutions) and the every-land-owes-its-own
fact rule; `TheEconomyFloorContent` gained the land-to-land table's own
three tests (who sells what over nine countries, the twenty edges with
every land reached and every `when` producible by the source, and the
wool axis wired through to a shelf); `TheServicesCounter` gained the
weather-witch. Five existing tests moved with the content: the derived
raider road is Vellisclavia's now, the schism runs Byzantium <->
Seraptania, the magic floor is three everywhere including Thule, a
politics card may be one land's, and the bought-sky marker is
`sky-bought`. `test_places.TheNineCountries` grew the other half of the
same contract: every country owes a fact whose scope is exactly itself,
and a country's relations are its own rather than its culture's (the
proof is that two lands of one culture no longer share an edge set --
under the cross product they always did).
