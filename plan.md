# Roadmap

**Planned features and parked ideas only.** What is left to build, in
order; the ideas agreed to exist but not scheduled; the questions still
open.

**Nothing implemented lives in this file.** When a feature ships, its
entry is DELETED here in the same session and written up in
`designlog.md` — the dated design-session history is the archive of what
was built and why; this file is only what is still ahead. Never mark an
item "SHIPPED" and leave it standing, and never keep a built spec here as
a trophy. The rest of the shipped record has its own homes: the played
rules and the design spine in `rules.md`, the code index and the dev map
in `develop.md`, measured numbers in `benchlog.md`, fiction and content
style in `writing.md`, the play protocol in `dm.md`. Where a planned item
leans on something already built, leave a one-line pointer to the doc
that owns it — never a copy of the shipped spec.

---

## THE RETRO PIVOT (2026-07-21) — the direction, and what is left of it

The 2026-07-21 session (designlog has the reasoning) reframed the
presentation and the seat the AI sits in: a mechanics-centered game in
the mold of a **retro text adventure**, where the mechanics are MACRO
decisions and a SIMULATED WORLD the player watches play out, and the
LLM's advantage is not that it narrates but that it is a **coding agent
running the game** — the central game function need not exist, only
subsystems the agent calls, generating content where needed and keeping
the whole coherent and open.

Three consequences still govern the roadmap:

- **Displays over prose.** Script-generated logs and menus are the
  primary thing the player reads; the chat should usually display them
  directly, at 40 columns. *(Softened 2026-08-12: logs, menus and
  numbers stay displays, but quests and their resolutions are narrated
  in the text-adventure voice, and the DM checks that quests and
  events make sense -- dm.md's Narration style owns the rule.)*
- **Dark quests stay the most important pre-authored content**, and
  their wording gets a simple-and-straightforward rewrite.
- **The villain/karma layer is one layer among several**, not the
  direction the roadmap serves. Nemesis persistence and rival posses are
  bumped way back: they serve narrative strength, not mechanical, and
  narrative is not the focus now.

The style itself is `writing.md`'s; the simulated-world half is the
active thread below. What is left of the pivot's own build order:

1. **The log/menu rework — the non-combat half.** The 2026-07-28
   display pass took the hero readouts (`hero_block_lines`, shared by
   `status` and `ui/party.txt`) and the levelup menu with its ability
   briefs (develop.md's Files section carries the record). Still open:
   - a player **STATUS DISPLAY** — a fitted, pasteable `status` in the
     same register (the hero blocks are fitted; the quest/world/karma
     lines around them, and `board` / `map`, still print DM-shaped,
     wrap-reliant output);
   - a **fitting pass over the remaining non-combat surfaces** — rests,
     travel, recruit sheets (`people.person_line` still runs one long
     semicolon-joined line) — where lines still hang a word past the
     width. `fit_lines` and the tally/pause penalty display are the
     pattern to reuse;
   - **`ui/minimap.txt`**, a local map page beside `ui/map.txt` and
     `ui/history.txt`: the current Area/Site/Room branch, visible exits,
     and local quest markers, built off the shipped `look`/breadcrumb
     data and joining the same rewrite + `sheet` commit lifecycle. UI
     only.
   - Parked from the same session (designer skepticism recorded):
     **E1/P1 shorthand** for enemy and party names in fight lines —
     saves width on long names but reads cryptic; try only if long-name
     fights prove noisy in play.
2. **Play the dark path in the new register.** The probe tests the retro
   style AND the dark content at once — the first ten messages, the
   first three levels.

---

## THE WORLD & NPC SIMULATION (2026-08-05) — the active thread

The problem it serves: **places and NPCs don't matter.** The player
cares about quests and levelling; the world fades to background. Places
are quest furniture the board abstracts into level numbers, givers are
faces attached after the roll, and the land notables do nothing. Combat,
levelling and the quest system are judged good; this thread is where the
world catches up. **Its build is DONE as of 2026-08-11** and it is kept
here as the framing behind five shipped rules.md add-ons and the postponed
list below. Its content companion is **`worldsim.md`**, now down to the
residue no session was asked to build (the economy and politics packets'
standing facts, the options that want a counter the game does not have, and
the ruler sheet's per-land modifier columns). The record kinds it opened
with are `worldsim.py` and rules.md's The World Layer, the weather it
sketched is rules.md's Weather, its economy packets are The Economy Floor,
its ruler sheet and politics packets are `rulers.py` and Politics & the
Ruler, and its worship and arcane packets are Religion & Magic. (designlog
carries the trail: the 2026-08-05 framing, the 2026-08-06..07 content
dumps, the 2026-08-07 sessions C and D that turned the thread into this
build, and the five rungs shipped since.)

### The framing (settled 2026-08-05)

- **The characteristic criterion.** A world detail earns its place only
  if it is mechanically backed (changes a number, posts work) or the
  player already has history with it. Everything else is homework for
  the DM — the unbacked three-trait NPC sketch was the type case and the
  first thing the criterion cut (rules.md carries the traits' scope).
- **The six outlets.** Everything the game can present the player
  arrives through six channels: QUESTS; RANDOM ENCOUNTERS; SIGHTS (the
  player sees something); NEWS AND RUMORS; the PRICED MENU (standing
  player-initiated actions whose terms local state sets: shops,
  services, the crime catalogue); and the STATE DIFF (persistent
  readouts that show change on return: the sheets, the map, place
  states, holdings). Every feature is a way to generate these six with
  good variety. RECURRENCE — one named face threaded through several
  outlets — is the property that makes an NPC exist at all; no single
  outlet produces it.
- **Events are pulses keyed to vocabulary, never to places.** A world
  event template declares which place tags and states admit it, and
  touches up to five outlets: post / cancel / reprice a quest, adjust
  the priced menu, add a local encounter-table entry, emit a news line,
  flip a visible place state. A place's identity is a cheap seeded roll
  over shared vocabularies; the content bill is the template set (~20
  for a first pass), written once for the whole world. Worked example: a
  fishing village rolls authority = greedy toll-reeve, tension = toll
  squeeze; the TOLL DOUBLED event fires — news line, a premium merchant
  delivery posts, the local road gets toll-men; the player can run the
  delivery, rob the toll house (nobody in town testifies), depose the
  reeve, or leave — and return later to a state that moved on its own.
- **Macro decisions are which stimuli you answer.** No new decision UX:
  which land, which jobs taken or let lapse, which marks cased, when to
  go home. The sim's whole job is making the generators state-driven,
  held honest by two invariants: the BOARD must react to world state,
  and something must move WITHOUT the player taking a job — and be
  visible on return.
- **Architecture doctrine.** Lazy, seeded, day-stamped, rolled at
  settlement arrivals and the news points (the raids / refill / news
  pattern). No background tick. No numeric supply-demand flows, no
  cross-settlement trade, no NPC-to-NPC interaction simulation: discrete
  states plus events that flip them. The premade simulated cast is
  REJECTED as overkill — events name the actors they need, and those
  persist (the record page and named-kill detection are the persistence
  surfaces). Cross-land RELATIONS are authored directed edges read at
  roll time (who imports grain, who rents land, who pays tribute) —
  lookups feeding derived states, never traded quantities
  (`worldsim.md`).

### The settled rulings (2026-08-07 — reopen only with the designer)

The build's SCOPE is **implementing `worldsim.md`** — not the whole
thread agenda: what worldsim.md does not design does not get built.
Everything settleable is settled here, not at per-session pick lists.
The settlement-authority identity roll (the kind/tension vocabulary and
the desert mechanics) IS JERKIFY under the designer's framing, is not
yet designed, and is postponed past the build. What NPCs carry instead
of the retired sketch was answered and has since shipped: the authority
tier rolls THE RULER CHARACTER (rules.md's Politics & the Ruler),
ordinary givers and service faces stay blank (the characteristic
criterion — rulers are card-backed, givers are not); only the PC's blank
sheet stays open, parked below.

- **The [PROPOSED] set is adopted wholesale** — implement it like
  everything else; the marks stay in worldsim.md as provenance only.
- **Orc horses stay as written** (the aesthetic flag resolves to the
  text; re-judge at the table).
- **The robot-servants card waits for SCIENCE & TECHNOLOGY** — its
  tone/tech question is that layer's magical-vs-mundane boundary call.
- **Sulfur-to-Hell waits with hell's own treatment.**
- **The Day of the Dead stays deliberately unruled** — the rite is
  written to work either way; the ambiguity is content.
- **THE FOG RAISES BONES ships** (skeletons are in the catalog); **THE
  DRAUGR waits** for the postponed monsters & fauna dump (it names a new
  creature row).
- **The carnival amnesty ships as color**; its mechanical reading stays
  deferred with the temple/penance wiring (below).
- **The elven coherence-and-subtlety flag rides the writing pass** —
  final player-facing strings are written at implementation under
  writing.md anyway, so the Ensimaa cards get the designer's
  more-coherent-more-normal pass there (religion is already regrounded).
- **Numbers no ruling covers** (the cold's condition values, clocks,
  prices) are the build's call, hand-set and tuned at the table (the
  standing convention).

### The ladder is EMPTY (2026-08-11)

Every rung has shipped: the settlement trim and the world frame
(2026-08-07), the weather (2026-08-08), the economy floor (2026-08-09),
politics & the ruler (2026-08-10), and religion & magic (2026-08-11).
worldsim.md is down to residue nobody was asked to build, its packets are
cut, and the played rules are rules.md's five world-layer add-ons.

**What the thread now wants is PLAY, not another rung.** The two invariants
it was built to land are in the code and pinned in `test_worldsim.py` — the
board reacts to world state, and something moves without the player taking
a job and is visible on return — and not one of them has been seen at a
table yet. Nothing below should be scheduled before a playthrough has
walked into a land that moved while it was away. (The played-reality note
at the head of CLAUDE.md is the reason: no playthrough has ever gone past
level 4, and everything this thread built is meant to be felt in the first
four or five.)

### Postponed past the build

Each needs its own design work or dump before it can be scheduled. The
ladder is empty, so nothing here is blocked by anything except the call
above: play the build first.

- **Jerkify** — the designer's framing: the settlement-authority
  identity roll (kind, disposition, standing tension — the kind/tension
  vocabulary is unauthored) and the desert mechanics (sin/heat modifiers
  by desert off `heart`, surfaced by `case` — a DISTRIBUTION, not
  uniform rudeness; choosing targets by casing IS the vigilante game;
  the lore hook stands, dm.md: Order is often not Good). Not yet
  designed — no implementation; its own design session after the build.
- **Bullies** — rides the jerkify design. The ferocity-0 mercy IS the
  encounter (purse taken, party left at 1 HP); what's needed is the
  spawn hook, the face persisting on the record page, and a revenge
  address on the priced menu — the grudge is the PLAYER's, which fixes
  the shelved nemesis's motivation problem.
- **Monsters & fauna** — postponed, like science & technology. The
  religion packets pre-order three creatures (the draugr, the knockers as
  a creature rather than the shipped fact, Tergal's grave-made ghosts);
  their cards wait with the dump. Everything ELSE in those packets shipped
  2026-08-11 over the catalog's existing rows.
- **Science & technology** — postponed; owes the magic packets the
  magical-vs-mundane boundary when it lands (the robot question, the
  guns).
- **The temple/penance wiring** — whether and how temples interact with
  the shipped sin/penance economy (priced absolution, confession,
  per-rite flavor on penance). Deliberately undesigned at the designer's
  2026-08-06 direction; temples stay plain priced services until it gets
  its own design round.
- **The econ packets' standing OPTIONS** — the four things the economy
  floor identified as wanting a priced-menu entry of their OWN rather
  than a multiplier on an existing price (worldsim.md holds the list):
  paid mercenary hiring in Tergal, Mortellaria's banking (paper-to-gold,
  credit), the two drug markets, and smuggling / the gadget-and-arms
  trade. The last two belong with the crime layer's smuggling category
  rather than a shop counter; the first two want a counter that does not
  exist yet. The religion & magic rung built the OPTION record and its
  `service` counter (2026-08-11), so three of the four now want only
  authoring plus one new verb apiece; the smuggling pair still wants the
  crime category written.
- **Cards and relations founding settlements** — the trim's
  need-to-exist draw is built, tested and DM-documented
  (`quests.found_settlement`; dm.md, "The map can grow at your call"),
  but no authored card or relation calls it yet: nothing in the shipped
  content names a rival center of power or a counterparty port. The
  engine half is done; what remains is content that WANTS a place to
  exist, which should come out of play (2026-08-12 review finding).
- **Hell's own treatment**; **the per-land ruler modifier columns and
  the tribal rewording**; **the landmark-problems tie-in** (re-raise
  once the build is played); **the PC's blank sheet** (a player-chosen
  background?).

---

## The villain layer — what remains (2026-07-19, demoted 2026-07-21)

The layer's spine is built and played from `rules.md` (Karma & Heat, The
Hell Pact, the Crime add-on, Conquest & Holdings); the reasoning trail is
designlog's 2026-07-19 and 2026-08-04 sessions. What is DEMOTED is the
villain ARC as the roadmap's direction — the retro pivot supersedes that
framing. The order below is the layer's internal one, for when it
returns; conquest ticking and the greed economy are its most retro-
compatible entries (macro decisions, world state).

1. **Nemesis persistence.** Posse leaders who survive (party fled, or
   the leader's row lived) RETURN: same face, +1 level, a grudge line.
   The save already keeps `last_leader`; grow it into a small nemesis
   record. Cheap (a thin save record plus one posse-spawn hook), but
   bumped way back with the layer — it serves narrative strength.
   *(2026-08-05: the cheaper inverted entry is the BULLY, postponed past
   the worldsim build — the NPC wrongs the player first, so the grudge
   needs no manufacturing. Absorbs the parked "rival" idea.)*
   *(2026-08-08: it now has something to stand on. The **loose-ends
   record** — rules.md, "Loose ends" — already persists escapees with
   their real stat rows, day, place and wounds, and `pursue --stage`
   already re-opens a fight against one. A nemesis is that record plus a
   face and a level bump; build it as a promotion of a loose end, not a
   second parallel list.)*
2. **The good-karma mirror — the dual campaign.** Hell's disciplinary
   side already punishes DISOBEDIENCE; what remains is the mirror
   proper: hell auditing a too-*virtuous* employee (good karma as the
   liability axis), so the hypocritical middle path (both meters hot)
   becomes the comedy jackpot. One mechanic, two skins.
3. **The greed economy.** Luxury items as gold sinks that generate sin
   and heat when FLAUNTED (envious hell officials, heroes coming for the
   holy golden elephant): each displayed trophy is a standing quest hook
   pointed at the party. Feasts (cook the monster) as the
   satisfaction/karma variant. This is also the L15+ "what is gold for"
   answer arriving early — coordinate with domain play.
4. **Dark content pass**: race-flavored dark templates, war-integration
   (side WITH the story layer's aggressor?), parley and bribery with
   posses. The karma-on-kill weapon quirk is already a live generator
   roll — what remains here is authoring SPECIFIC villain pieces onto
   it.

---

## Queued — landmark problems

- **Objective high-level problems that exist independent of the
  player**: landmark problems known by rumor from level 1, standing on
  the board regardless of the party's level and NOT subject to the
  refill's churn (a dragon does not lapse in seven days). The refill
  posts ordinary work; this is the authored counterweight to it.
- Later sim hook (parked): other heroes occasionally solve, or die to, a
  landmark problem while the player is elsewhere. *(2026-08-05: this
  hook is an ordinary event pulse; the tie-in question is postponed past
  the worldsim build.)*
- Cheap story-layer content, once wanted in play: war-flavored reskins
  on local quests in threatened lands, and a rescued recruit as an extra
  wave-3 tangible.

---

## Queued — quest shape from narrative content (its own design pass)

*(Opened 2026-07-26, the quest-length session: encounter count stays a
weighted roll for now — a deliberate placeholder — while site count is
already a template-declared place count.)*

- The designer's intent: **the narrative content should decide how long
  a job is** — a template's premise, its stakes, and its place structure
  imply whether it is one fight, a two-stage hunt, or a three-beat
  escalation, and a rolled 1/2/3 only approximates that. The pass makes
  the encounter count (and the shape of each encounter's role in the
  quest) an authored property of the template, so the board's mix of
  short and long work is designed rather than sampled.
- Wants the same pass over the good templates in `quests.py`, the epics,
  and the occult templates in `karma.py` — the same files the wording
  rework already took to the plain style (2026-07-22 and the dark
  rework; designlog), same content register (`writing.md`).
- Schedule after the quest-clock and wound slices have been played: what
  a job's *right* length feels like is a play finding, not a desk one.

Story items on the shelf:

- **The apocalypse questline — the L12-20 second spine.** Parked until
  the magic tier exists (its payoff enemies are demons above the dragon
  row). *(Pivot note: under the villain frame this may become the RIVAL
  conquering force — the thing that conquers half the world if the
  player doesn't, or the employer the player answers to. Decide when the
  good-karma mirror lands.)*
- **Progression frames** (guild advancement, the legendary-smith arc) —
  narrative wrappers around the same combat quests; cheap now that
  questlines exist. The smiths themselves are commission vendors
  already; what stays parked is the narrative ARC around one: winning a
  smith's respect, fetching the ore, the rival buyer.

**A career finding to design against**: the top band (15-20) is still
the hard edge (per-quest wipe 40-65% at level) and still waits on the
rank-4 capstones for part of its missing player power. The gear half is
in hands the sim cannot use yet, so **a top-band career re-bench with
generated steel actually reaching sim parties is owed**.

---

## Carry-forwards from the levelling framework (2026-07-17)

- **Enemy-side moves** (giving the drilled soldiery two moves each) and
  the **second-wave moves** (guard-break, taunt, battle-cry) — a later
  content pass with its own bench round.
- **The day-stamp spoilage variant** — the freshness STOCK CAP shipped
  instead. If spoilage should ever be FELT, the cheap variant is one
  day-stamp per hero's brewed batch — noted, not built.
- **Alchemy conditions** (poisons, oils) — UNBLOCKED since the
  conditions framework shipped: a poison oil is now a recipe plus one
  `apply_condition` call.

Open to feel out in PLAY: points-per-level 3 vs 4 and training 2n
(re-open only if the mid-band feels grim); the **kit-shrink dial**
(`KIT_STAMINA` 1->2 or a higher `KIT_FORAGE_CHANCE` if play reads too
grim); the **DEX potion** (rank 4/+1 under the standing +DEX warning).

---

## Parked — follow-ons from the attrition rework (2026-07-26)

The rework itself is built and played; its spine (*do not make rest
expensive, make rest incomplete* — gate recovery on rate and access,
never on price) is in `rules.md`, and its settled constraints — HP stays
the scalar, injury is one system with two time constants, foes keep the
scalar, the permanent setback is a maiming — are in designlog's
2026-07-26 entry. **Do not reopen those without a design session.** What
was parked out of it is additive to the shipped schemas:

- **Damage types and weapon profiles** (cut / pierce / blunt / burn /
  poison / magic). `Weapon` already carries `move_tags` and severity
  flats, so a `damage_type` field is cheap now that conditions exist.
- **Magic energy bypassing protections.** Waits on damage types, and on
  armour existing at all.
- **Armour interacting with wounds** — with the wound system in, a tier
  shift also decides whether a crippling blow kills, maims, or merely
  wounds, and whether the record is severity 1, 2 or 3. That is a far
  better job than "+DEF", and the strongest argument armour has ever
  had. Still the designer's call to adopt, simplify, or defer.
- **Foe wound records.** Rejected for v1; revisit only if persistent
  named enemies (the nemesis record) ever need scars.
- **Prosthetics** — steampunk and magical limbs and eyes, including ones
  that push a stat **above** the natural cap. `Wound.prosthetic` is
  already a seed field, so the schema cost is paid: what remains is the
  item content and the above-cap rule. Note the synergy with non-weapon
  magic items (the After-that list) — a magic item with a scar attached.
- **Infection / wound complications over time** — an untreated wound
  worsening rather than merely persisting. Disease now exists (the
  weather rung's cold and pneumonia — rules.md's Weather), so this is
  unblocked: the shape to reuse is the nightly shake roll, run the
  other way.
- **Removing HP from the MODEL.** The played surfaces already band it
  into a state word; the model keeps the scalar, and the settled
  decision above says why.
- **A true en-route travel position.** The roll happens on the road off
  the origin land's pool, but an interrupted trip still bounces back to
  the origin, and a road SIGHTING is slipped past rather than offered as
  a choice. Proper mid-road positioning wants the local navigation layer
  and `ui/minimap.txt`.
- **Road-encounter rate trim.** `TRAVEL_ENCOUNTER_CHANCE` 0.15/day,
  `EXPLORE_ENCOUNTER_CHANCE` 0.30, `CAMP_ENCOUNTER_CHANCE` 0.10 were
  sized against 3.74-fight quests; at the current 1.66 the road is a
  much larger *share* of all combat, and the quest clocks price the
  trips. Re-judge from played evidence; the lever is a trim to ~0.10 /
  ~0.20, not a redesign. (The 2026-07-26 per-level sighting/ambush
  measurements are in benchlog — do not re-derive them.)
- **A travel layer in the career sim.** `bench_quests`' careers still
  teleport between jobs, which is why its turn-ins skew early — a played
  campaign, paying 1-2 days each way, will sit in "on time" and drift
  late. Adding the road would make the sim's calendar honest against the
  clock, at the cost of breaking comparability with every career number
  in benchlog. Do it deliberately, in its own pass, not as a side effect
  of another slice. *(2026-08-08 raised the stakes: the turn-in stage
  put a RETURN leg in the played loop and widened every window to pay
  for it, and the sim walks neither. Its bands are now measuring a
  clock the played game no longer has — see benchlog's entry. This is
  the item that closes that gap.)*
- **Wilds camping restoring less than full STA** (`CAMP_STA_FRACTION`
  ~0.75, a bed 1.0). Held at 1.0; pull it only if multi-encounter quests
  get chunked into one-fight days.

---

## After that (in rough order)

1. **What remains of the magic item**: **the wraith** (buildable now
   that attack spells exist); **rank-4 capstones** (authored
   tomes/mentors — the 14-20 band's player power); **enemy spell use**
   (openers, not just bolts); **flight ranks 3-4**; **the mid-game
   caster** (ruled 2026-08-07: cannot-become-a-caster-later is
   unintentional — the game should stay open and fun, so the 2026-08-05
   never-acquire asymmetry is softened to a temporary fact of the build.
   Open casterhood after creation; mechanism the implementer's call — a
   latent-gift awakening event is the cheapest fiction, and the shipped
   magic layer now supplies the in-world reading for free: the WILD TALENT
   card, the recruiters and the three teaching counters are all about a
   gift waking in somebody who had no theory). **Non-weapon magic items**
   — rings, amulets — would reuse the weapon generator's sp table if ever
   wanted, and CURSED WORK is their first flavor: the cursed ring that
   grants +3 DEX and takes 1 point of natural DEX, power with a receipt.
   It is the affliction doctrine (rules.md's Religion & Magic) sized to
   an item, and worldsim.md's residue section keeps the note.
2. **Armor** — provisional design: shifts the incoming wound tier down
   at the cost of a DEX penalty and higher STA drain. *Status: adopt,
   simplify, or defer.* (Designer lean: probably never important. The
   wound system gives it a far better home than "+DEF" — see the
   attrition follow-ons above.)
3. **Signature weapon pieces** — content, not framework: hand-authoring
   specific blades where the fiction wants a SPECIFIC weapon rather than
   a rolled one, and the leech blade, which waits on an authored regen
   rider.

---

## The major-feature shortlist (2026-07-14) — ordering notes

- **The conditions framework's queued customers** — cheap now that the
  framework exists: a school-wide cast rider (every fire bolt burns —
  deliberately held back, it moves every bestiary row because hero
  wizards gain it too), the firebomb, poisoned blades and the rot spell,
  and varied-enemy riders generally.
- **Free-play facilitation / overriding the mechanics** — mostly dm.md
  doctrine plus the override surfaces that already exist (`forge`,
  `give --as`, the hand-editable save). Cheap, worth doing early.
- **Professions** — a between-fights layer off downtime and the economy;
  natural feeder for domain play.
- **Intraparty mechanics & prominent main NPCs** — deepens shipped
  layers; its big multiplier is the world thread's event pulses. *(The
  nemesis record is this thread's first concrete customer.)*
- **Domain play** — the fuller layer (followers, rulership, buildings);
  the natural answer to "what is gold FOR at L15+". Its thin edge is
  already in as holdings, tribute and levy garrisons; grow the rest out
  of that state, with the greed economy as the natural next hookup.
- **The content passes** — deliberately last within their threads.

---

## Parked ideas (agreed to exist, not scheduled)

- **The posting-band trim** (2026-07-27) — the designer floated lowering
  `SETTLEMENT_KINDS` posting caps (capital 15, town ~9, village ~6). The
  conquest ladder that motivated it shipped as separate GARRISON bands
  instead, leaving the calibrated quest economy untouched; the trim
  stands on its own merits only. Note the cost before pulling it:
  capital 20 -> 15 means no L16-20 board work ever posts, and it needs a
  bench re-run.
- **The conquest mirror for the good campaign** (2026-07-27) —
  liberating a war-occupied settlement for its own crown (or a
  protectorate flavor of holding). One mechanic, two skins, like the
  karma mirror; park until the dark conquest has been played.
- **Hell as a place** (2026-07-19) — walkable any time at no cost,
  dangerous, demons love bullying. Today it is pure DM narration
  (dm.md); the parked content: the gladiator pits of hell (with the
  bribe-to-lose-on-purpose bout), the castle bought in human bones,
  hell's org chart above the collections agent. First customer of any
  hell map. *(Hell's own worldsim treatment is postponed with the
  build.)*
- **A geographic wanted level** (2026-07-19) — searched-for in one
  settlement / the whole land / all lands. Heat is the GLOBAL version
  and is shipped; the geographic split is a refinement — park until heat
  has been felt at the table.
- **Standing dark enterprises** (2026-07-19) — the powder network (and
  rackets generally) as HOLDINGS that earn and draw rivals over time,
  not one-shot actions. The smuggling/powder crime category carries the
  seed; the standing layer feeds domain play and conquest ticking.
- **Karma-gated powers / hell ranks** (2026-07-19) — lifetime sin has
  its first job (the crime-suggestion unlock feed) but buys no powers.
  Whether wickedness should UNLOCK anything (evil abilities, hell
  hierarchy ranks, promotions) is deliberately open — see Open
  questions.
- **The rot spell & evil magic content** (2026-07-19) — "learn an evil
  spell that quickly rots the opponent alive; use it on an innocent
  bystander" wants a new spell on the conditions framework; park with
  the magic content pass, alongside the school-wide cast rider that pass
  also owes.
- **War-side-taking** ("a land has attacked a neighbor — help the
  aggressor") — already the dark content pass's war-integration item;
  noted here so the brainstorm line has a home.
- **An army mechanic** (2026-07-19) — armies that MOVE (rival powers,
  fronts, army-vs-army campaigns). Its seed is the garrison levy number,
  resolved heads-against-heads off-screen; feel out the shipped raids
  first. The guard rail stands: one chat line per decision, or it's out.
- **Summoning** (2026-07-15) — needs its own design round (action
  economy is the game's strongest measured force).
- **Antimagic** (2026-07-15) — trivial to build, nothing to counter yet.
- **Ward, the tier-shift shield spell** (2026-07-15) — note it doubled
  as the provisional armor design.
- **Opener economy in play** (2026-07-15) — if played wizards resent the
  pool burning on trash fights, the fix is a session-side hold toggle,
  not engine smarts.
- **Opt-out tutorial register** (2026-07-14) — relevant only if the game
  gets a second player.
- **Faction reputation** — designer has more to spec; nothing until
  then. *(Note: karma IS a first faction axis — law vs the party; spec
  the rest against it.)*
- **Settlement flavor lines** — valuable but easy; deliberately not yet.
  *(2026-08-05: gated by the characteristic criterion — unbacked flavor
  is the trait-sketch mistake; write them only onto identity fields the
  simulation thread actually reads.)*
- **The rival** — ABSORBED into nemesis persistence and the
  apocalypse-as-rival-conqueror note; bumped way back with the nemesis.
- **The traitor twist** — one authored questgiver per conquest variant
  collaborating with the aggressor; cheap authored beat.
- **Morale & surrender** — the foe half is in (`FoeSpec.ferocity`, low-
  ferocity rosters breaking off); what remains is the party-facing side:
  yielding, bargaining, parley. *(Posse PARLEY — bribing the Watch,
  demanding surrender — wants this; build them together.)*
- **Story recruitment** — "the ogre yields and joins you", DM-driven.
- **Weapon reach** — a small first-exchange modifier; distinct from the
  field.
- **Cover & terrain on the field** (2026-07-16) — prose until the
  wilderness gets a terrain pass.
- **Friendly fire into the press** (2026-07-16) — only if play shows
  free focus-fire reading wrong.
- **The 2-STA heavy swing** — sim-rejected while Spent is lethal.
- **d12 variance experiment** — don't fork the dial while lethality is
  settling.
- **Asymmetric Spent** — soften attack to −3 if spent-vs-fresh grinds
  ever feel wrong.
- **A PC happiness stat** — kept OFF (2026-07-11).
- **Prey depletion (the hunt-spam lever)** — only if play shows
  hunt-spam degenerate.
- **Survival/adventure-sim pivot** (hunger, upkeep, inventory) — kept on
  the books as a possible deliberate pivot, but 2026-07-19 chose the
  GREED ECONOMY over food as the villain game's sink, and the attrition
  rework took the pivot on the WOUND axis instead (named injuries, blood
  loss, convalescence, maiming, prosthetics later). Food and upkeep stay
  rejected as gold sinks for the reason that rework turns on — flat
  prices inflate away. If rations ever return it is as carrying
  CAPACITY on long wilderness trips, never as a price.
- **Power potion re-stock** — if War-Breath ever makes Power scarce.
- **Crit/fumble on the 2d6** — fattens both tails of every exchange;
  full bench re-run before judging.
- **Party members as lives, the wipe version** — the in-fight half is in
  as fate's bargain, and left-for-dead answers the wipe half a different
  way (once per character level, with a maiming as the price). Re-judge
  from play; watch whether recruit renewal softens it.
- **A PC-centric career sim** — if played campaigns drift from the
  bench's even-duo story. *(A karma-playing career variant — dark work +
  posses in the policy — is the natural check once the villain game has
  been played; today no sim sees karma at all.)*
- **Site persistence / repopulation** — the stick version of one-go
  sites. *(2026-07-26: its old trigger is gone with the XP streak. The
  new pressure is the wound track: camping restores stamina but never
  HP, so a multi-encounter quest is a real HP budget. Re-judge only if
  that proves too soft.)*
- **Give the rapier its niche back** — do nothing until felt in play.
- **Re-annotate the bestiary for the pain-2 party** — calibration
  polish, not a fire. (The venomous spider and the pyromancer were
  deliberately NOT re-fit when conditions landed; benchlog has the
  numbers.)

### Rejected, and staying rejected

- **Per-weapon pressure dice** — 2d6 stays the one dial.
- **Level requirements on masterwork/legendary weapons** — authored
  placement gates them.
- **The "obliterating" wound tier** — effectively answered by the wound
  system: a crippling blow to a vital already reads as the killing one,
  and the same blow to a limb maims instead. Re-open only if the top
  band, once authored, still wants a fifth tier of its own.
- **Scaling tavern prices, food/upkeep as a gold sink, dearer potions,
  retribution attacks as healing pressure** — the attrition rework's
  four rejects, each for a recorded reason (designlog 2026-07-26).

---

## Open questions

- **Karma AS the level track?** (2026-07-19) Karma runs beside XP
  (bucketed awards). The radical version — karma IS progression, levels
  EARNED by wickedness under hell's quota — would make the villain frame
  total. Decide after the dark path has been played; the bucket design
  was chosen precisely so the merge stays cheap.
- **What does sin BUY?** Heat, gold-rich work, and the crime-suggestion
  unlock feed, today. Candidates: karma-gated abilities, hell ranks
  (titles + perks), the luxury economy's prices. The other half of the
  original "good and bad karma as xp unlocking abilities" idea —
  deliberately deferred.
- **The crime layer's two play judgments** (2026-08-04, recorded in
  rules.md's Crime add-on): the **heat pump** (crime lumps are smaller
  than quest lumps, so `CRIME_XP_PER_LEVEL` is the lever if heat proves
  hard to reach), and the **flat deed DC** (9-11 whatever the mark's
  level, so a low-level party can gamble one roll against a very rich
  mark — if the make proves too cheap, the levers are a DC that climbs
  with the mark or a lump the clean take only partly pays).
- **The heat curve's numbers** — `KARMA_HEAT_STEP` 100, `HEAT_CAP` 3,
  the cooldown, chance 0.6, dark gold ×1.5: all provisional, hand-set,
  sim-unverified (no sim plays dark). Tune at the table first; a karma
  career sim is parked above.
- **Armor:** adopt, simplify, or defer (the least-developed system;
  designer lean: never important).
- Every constant is provisional and sim-tuned, never hand-designed — the
  current numbers live in `develop.md` ("Balance / tuning").
