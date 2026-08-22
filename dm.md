# DM Guide -- how the agent runs a playthrough

Read this file and **`writing.md`** before starting or continuing a game
(playing/testing as DM, as opposed to developing the code). This file is
the play protocol; `writing.md` is the shared fiction and content style.
For mechanics depth go to `rules.md`; `develop.md` is the development guide
and is not needed for play.

## Starting and continuing

- New game: `python session.py new` (add `--seed N` for a reproducible game
  -- `new` also generates the playthrough's whole quest world). The PC is
  **GENERATED, not chosen**: one character (his CHA always holds at least
  one companion), always a **magic user**, with a **long-time companion
  already at his side**. Introduce the companion as shared history ("X has
  watched your back for years"), never as someone who joins in scene one.
  Present the PC's sheet without mechanics chatter (see The player
  character below).
- **The party's LEVEL is rolled 1-18** unless the player asks for one
  (`new --level N`, 1-20). The uniformly selected starting settlement fixes
  both heroes' homeland.
  Above level 1
  the pair arrives with the career those levels bought -- points spent,
  quality steel, a job-reward weapon, spellbooks, a purse -- and the
  opening hook is a job at THEIR level. Play a career start as a party with
  a past: they have been doing this work for years, and the telling simply
  starts today. Don't invent a backstory the player can't act on; if the
  player wants one, build it with him.
- **Open at the hook.** `new` prints an OPENING HOOK: a combat job posted at
  the party's exact level in their randomly selected settlement. Set the first scene at that
  job's doorstep -- the giver is already explaining the problem, and the
  problem is concrete -- then hand the turn over: the player can take the
  job or refuse it and do anything else (`board`, `hunt`, `travel`). The
  hook is an offer, not a forced path. Do not open in a tavern, and do not
  stage a recruitment scene.
- Continuing: `python session.py status` shows where things stand.
- State persists in **`save.json`** between terminal calls; every
  subcommand is listed in `session.py --help`. The save is plain JSON on
  purpose: it is committed, so the playthrough is stored in the repo with
  everything else. Every save also rewrites the standing **UI pages** in
  **`ui/`**: **`ui/party.txt`** (the full party info sheet),
  **`ui/map.txt`** (the drawn 30x18 world grid with the party and its work
  marked on it, the current Tile in detail, a by-country legend of every
  known settlement, and a summary of taken-quest sites with the road days
  to each) and **`ui/history.txt`** (the campaign
  record -- jobs done, the remarkable events, the tally of sin, hell's
  suggestions). Combat also rewrites **`ui/fight-short.txt`** (the
  displayed last fight) and **`ui/fight-detailed.txt`** (its full mechanics
  record). Two pages are YOURS to write, not the engine's:
  **`ui/scene.md`** (the DM message itself, drafted and reviewed there
  before it is said in chat -- see The scene page below) and
  **`ui/transcript.md`** (the append-only play log behind it). A further
  page, **`ui/minimap.txt`**, for local Site/Room detail stays out of the
  Europe MVP: the drawn macro map plus `look`'s Tile-and-Area breadcrumb
  is enough. **End EVERY DM
  message with `python session.py sheet`**, which commits every existing
  page -- one commit per message, so the player can follow the playthrough
  as message-sized diffs. Unchanged pages are a no-op; run it anyway. (The
  full end-of-message order is in The scene page below.)
- **GitHub IS the player's UI.** The pages are committed to the branch, so
  the player and the DM can both read them as blob pages. The player reads
  the TURN in the chat, so the link posted under every chat message is
  **`ui/party.txt`** (the between-fights board) -- the one page the chat
  does not already contain (see The scene page below). `ui/scene.md` holds
  the same turn rendered, for a wide screen or a reread, and its own footer
  links lead to the rest: `ui/map.txt` (where the party is and where their
  taken jobs lead), and `ui/history.txt` once the campaign has a record
  worth reading (after the first job, a conquest, a run of crime) -- that
  last page is also YOUR continuity reference across sessions: what the
  party did, who they killed, and what they are known for.
  `ui/fight-short.txt` is linked FROM the scene page at every fight (see
  the turn protocol); `ui/fight-detailed.txt` is shared on request, when
  the full mechanics record matters.
- **Editing `save.json` by hand is the DM's override.** When the story
  needs something no command provides -- grant gold, mend a wound, hand out
  a potion, resurrect a companion the fiction says survived -- edit the
  file between commands; every command reloads it fresh. Weapons are stored
  by catalog name (`"weapon": "katana"`); leave the `"rng"` blob alone. Use
  it for story reasons, not for convenience: the game is played on the
  engine's numbers, so do not edit away an outcome you merely dislike.

## The scene page -- the DM message is a file

**Everything you would say as DM goes into `ui/scene.md` first**, and only
the FINISHED text is spoken in chat. The point of the detour is REVISION: a
page can be reread and edited before the player sees it, and a chat message
cannot -- the style drift of a long session is caught in that reread. The
page is written, reviewed, committed, and THEN the turn is copied back into
chat verbatim, with the PARTY page's link under it. So the player reads the
scene in the chat, with no tab to open, and the one link they get points to
the board the chat does NOT hold. The scene page still holds THAT ONE TURN,
rendered, for the wide screen and the footer links. The chat scrollback is
the lookback; the page has no reason to repeat it.

- **Draft, review, commit, then copy back.** Write the full message into
  `ui/scene.md`, reread the draft against `writing.md` (its Final check is
  the checklist), and edit what fails it -- register, stray formatting,
  prose that restates a display. Gameplay inconsistencies (a contradicted
  fact, a wrong name, a scene that ignores where the party stands) are
  caught and edited the same way. Only then run `sheet`, and only then
  paste. A page shipped without the reread defeats the design, and so does
  a chat message written before the reread: **the chat copy is a COPY,
  never a first draft.** If a fix occurs to you after pasting, edit the
  page, `sheet` again, and state the correction in a plain line -- do not
  silently let the two diverge.
- **What gets copied: the turn's DM text, and nothing else.** Paste
  everything between the `>` line and the footer -- prose, code fences, the
  inline fight-log link -- exactly as committed. Leave OUT the `## turn`
  heading, the `>` quote of the player's own words, and the standing
  footer: the chat already has all of that or gets it from the link. Then
  the party link on its own final line. The two texts are identical by
  construction; never reword one for the other.
- **Format: rendered Markdown, structure only.** Raw text has no good
  reading surface (the phone app breaks words at the margin; 40-column text
  is a narrow strip on a PC screen), so the page is `.md` and is read
  RENDERED, reflowing to any screen. Markdown is used for structure and
  nothing else: a `## turn N (day D)` heading opens each turn, the player's
  input follows as a `>` blockquote line, links are real markdown links,
  and EVERY display block -- engine output pasted as printed, and any block
  you compose -- sits in a code fence, which is what keeps a 40-column
  display aligned in the rendered view. PROSE stays plain paragraphs: no
  bold, no italics, no lists, no headings inside the fiction -- the voice
  does the work (writing.md). Never hard-wrap prose; escape a literal `*`
  or `_` if the fiction ever needs one; keep everything ASCII.
- **Structure: the page is the CURRENT turn.** It is rewritten whole every
  message and holds one exchange -- the turn the player is reading right
  now, nothing older. The whole shape:

      ## turn 14 (day 3)

      > press on to the den

      (the DM text of the turn)

  The `>` line is the player's chat input, verbatim (trim only
  pleasantries); turn numbers count exchanges from game start.
- **End the page with the standing links**: one line of markdown links,
  current branch -- party and map always, history once it has a record
  worth reading. The pinned page is the player's front door; the footer is
  how they reach the other boards.
- **`ui/transcript.md` is the full record**: every turn appended in the
  same shape, never rewritten. The scene page keeps only the newest turn,
  so the transcript is where the game's past lives -- the page's history
  and yours. `new` starts both files fresh -- the old game lives on in its
  own branch.
- **End-of-message order, every message:** finish the commands, write
  `ui/scene.md`, append the new turn to `ui/transcript.md`, run
  `python session.py sheet` (it commits both with the other pages), then
  post in chat: the new turn's text as committed, and under it the PARTY
  link (swap in the branch):
  `https://github.com/havmar/rpg2/blob/<branch>/ui/party.txt`
  Nothing else goes in the chat message -- no preamble, no note on what you
  edited, no design talk. Out-of-game talk -- errors, design questions when
  the player raises them -- stays in chat and never on a page.
- **`scene-example.md` is the worked model** (a game start and a fight
  turn, in this format and writing.md's voice). Imitate its shape when in
  doubt.

## The world and the quests (the game's spine)

The world is one persistent **Country -> Tile -> Area -> Site -> Room** tree.
Tiles are day-scale map cells; Areas are sibling settlements and natural
destinations within them.
Sites are local destinations; rooms are immediate indoor or outdoor places.
Quests point to those world-owned places. **The party is always somewhere,
and quest offers are LOCAL**: the jobs you can take are the current
settlement area's. Which quest to take -- and whether it is worth the road
to another area -- is the player's core decision:

- `map` shows the macro world: lands, known areas, settlement open-quest
  counts, and the party's position. `look` shows the
  stored description, salient known state, sites/rooms, services, links,
  and visible Room contents; `go NAME` enters one and `back` moves one
  local level outward. `look` leads with the TILE (coordinate, country,
  terrain), then the Area on it, then the sibling Areas sharing that Tile and
  the four roads out with their day costs. `look --dm` is the full fact
  record, including seeds, hidden facts, occupants, and quest attachments.
  Local moves cost no day -- and since the grid shipped that includes
  crossing between Areas of the SAME Tile (`go NAME`). `travel` is the
  day-scale move, and it is what leaves the Tile.
- **There is NO quest board in the fiction: quests come from PEOPLE.**
  `board` is YOUR inventory readout -- each row shows the job, its level,
  pay, and WHOSE job it is (every quest has a generated giver: name, role,
  personality). **Quest and site levels always print exactly.** Relay them
  straight; `show QID --dm` adds surprise complications for your planning,
  not a truer level. In play, run the **one-message funnel**: the party
  asks around -- the tavern keeper knows, any local points the way -- and
  ONE message lands them in front of the giver, who lays out the job ("you
  ask at the taproom; the mayor waves you on to the chief constable, a loud
  woman in flamboyant dress, who tells you about the crypt"). A giver's
  line is name, role, homeland, sex and age -- no trait sketch (2026-08-05):
  play them off their ROLE and the job they need done, inventing only what
  the scene needs and keeping it consistent if they come back. They stay
  talkable while the quest runs, and the turn-in is THEIR scene. Present
  2-3 jobs per ask unless the player wants the full slate; relay levels and
  pay straight, answer questions about them straight, then let them pick. A
  job's mechanics (level, pay, foe kind where the board names one) ride in
  a short display block beside the scene -- the board's own rows are the
  format for the NUMBERS, and only the numbers: **what the job actually IS
  is narrated** (2026-08-12), told in the giver's own words in the plain
  text-adventure voice, never left to a pasted row or the template's desc
  line. **The desc is usually already the whole job** -- one plain sentence
  naming a thing and what to do about it -- so say THAT, in the giver's
  words, and spend the rest of the pitch on SPECIFICITY, NOT COMPLICATION:
  who is asking and why it fell to them, where the place is, what the job
  looks like from outside the door. Expand the desc itself only where it
  genuinely fails to say what the work IS, and then settle the plainest
  reading rather than adding a layer. **Name the thing outright** -- the
  machine, the gang, the wolves -- never "something in the factory": the
  desc's own words are usually the plain word already, and withholding them
  is the register mistake this section keeps producing (writing.md, "Name
  the subject the first time it appears"). Make it square with the place
  and the day's news before you say it. The giver's dialogue carries the
  fiction; never deliver it as a stat sheet or a tactics preview. The board
  also lists **word from up to three days' road away** (the open jobs at
  every KNOWN settlement in that radius, grouped `HERE` / `1 DAY AWAY` /
  `2 DAYS AWAY` / `3 DAYS AWAY` -- PLAYER-KNOWN, relay it) and **notables
  in town** -- the land's recurring
  cast (ruler, sage, wildcard): use them for color, rumor, and war scenes;
  they persist all campaign. (`board all` / `board NAME` is your wider
  overview for pacing.)
- **MOST PLACES HAVE NO WORK, and that is correct** (2026-08-15). Capitals
  and cities always post ordinary jobs; about three towns in five do, about
  one village in four, and a HAMLET one time in twenty. When the local
  board is empty, do NOT invent a job to
  fill the scene and do NOT apologise for the world: play the place as a
  place -- nobody here needs anything from armed strangers -- and let the
  rumor groups do their work. "No work here; a carter mentions they are
  short-handed at Ackham, a day west" is the scene, and the decision to walk
  there is the player's. `HERE` covers the whole TILE, so a sibling village
  in the same cell is a free step away, not a day's travel.
- **Every job has a DEADLINE.** A posting is wanted within 3-7 days of the
  day it went up, and the board prints the clock on every row ("4 days
  left", "DUE TODAY", "LATE (2 day(s) of grace)"). Relay it like the level
  and the pay -- straight, in the giver's words ("she wants it done inside
  the week"). What the clock is worth:
  - **Turned in quick** (the first third of the window) pays x1.15, **on
    time** x1.00, **late** x0.60 for three days of grace. Past that the job
    is LOST: the script prints JOB LOST and the giver's failure line, and
    the turn-in lump is gone. The per-fight XP already banked stays -- the
    party is not robbed of the fighting it did.
  - Untaken jobs come off the board at their deadline and leave a
    day-stamped **failure rumor** at the settlement ("the dead walk out of
    the graveyard now"). `board` prints the rumors once, under "What came
    of the work nobody took". Read them out -- that is the world changing
    while the party did other things, and it is the whole point of the
    clock.
  - The board REFILLS: one new job a settlement a day, up to its size
    (hamlet and village 2, town 4, city-grade 5) -- at the settlements that post ordinary
    work at all, and only within three days' road of the party. Nobody has
    to hoard work.
  - **A window now buys the whole road** (2026-08-15): 3-7 days plus the
    walk out through the job's places and home again. A job two days off is
    posted with four extra days in it, so relay the deadline straight and
    let the player do the arithmetic -- the clock is honest about travel now
    and does not need softening.
  - **This is why a long recovery costs something.** A long camp is never
    free: `camp 6` is six days off every live window -- and those nights
    cannot even mend a wound (only a settlement can), so a wounded party
    with a job in hand is choosing between the job's window and the HP
    ceiling. Say so when the player asks for a long rest with a job in hand
    -- one line, not a lecture ("the crypt job is wanted by day 9").
  - Hell's assignments carry their own pair instead -- the grace to take
    one, then the completion window -- and never lapse off the board.
- **The job ends in TWO beats now (2026-08-08): the field, then the
  giver.** Clearing the last place prints **THE JOB IS DONE** and names the
  giver, the area and the deadline; the field XP lands there and then, and
  the gold does not. Play that beat as the fight's aftermath, standing over
  the bodies -- the deed is done, the road home is not walked yet. Then the
  party travels back and `turnin QID` is run AT the giver's settlement,
  where the pay, the epilogue and the QUEST COMPLETE banner all land. Two
  practical consequences at the table:
  - **The return leg is a real leg.** Say what it costs when the party is
    deciding ("Kristryd is two days back, and the job is wanted by day 9").
    The windows were widened to cover it, so a straight walk home is
    affordable -- dawdling is not.
  - **The world already changed at work-done.** The pass is open, the
    crypt is quiet: narrate that in the field, not at the turn-in. What
    waits at the giver is the money and the ending, not the effect.
- **The turn-in is the GIVER'S SCENE, and the resolution is NARRATED
  (2026-08-12)**: `turnin` prints the day-stamped epilogue and the pay.
  The banner and its numbers stay in the display block; the epilogue line
  is MATERIAL, not display -- tell the job's ending as a short scene in the
  text-adventure voice, the giver paying and the aftermath fact folded into
  the fiction. The epilogue is what the world now looks like because the
  party worked; don't skip it, don't pad it, and don't paste it and move
  on. A LATE turn-in prints its own band line; play the giver accordingly
  -- paid, but not pleased. If the fiction has made the ordinary turn-in
  impossible -- the giver is dead, the town is burned -- `turnin QID
  --here` pays it wherever the story says; use the valve rather than
  bending the scene around the gate.
- **A job whose window closes on the road home is DONE, NEVER PAID.** The
  script says so, keeps the 80% already banked, and fires no failure rumor
  -- the monsters really are dead. Play the giver's grievance as story, not
  as punishment: the work was done and nobody paid for it, which is its own
  kind of scene.
- **BOUNTIES want proof.** About a third of kill jobs ask for the pelts,
  the rings, the head -- the board row says so and the giver's words must
  too, plainly, when the job is offered. On a bounty the target has to be
  DEAD: if it routs off the last site, the script prints THE TARGET
  ESCAPED and the job sits unfinished until the runner is killed. That is
  the moment to offer `pursue` (below) -- and if the trail goes cold, the
  loose end is a hook you can bring back rather than a dead job.
- `travel` walks the map GRID. `travel north|south|east|west` is one Tile
  edge -- 1 day east/west, 2 north/south, +1 if either end is mountain;
  river and sea cost the plain base. `travel R09C18` or `travel Prague`
  routes there by the cheapest road and walks it edge by edge. Travel days
  are camp nights (full overnight recovery -- travel heals) and each LAND
  edge risks a road encounter (~15%/day compounded; see the wilds section
  below), rolled at the Tile just REACHED, off THAT country's pool. A fight
  or a sighting stops the route right there: the party keeps the ground it
  walked, and `travel` again once it is settled. Narrate the fight where it
  happened -- on that Tile's ground, not back at the origin and not at the
  final destination.
- **The sea is open road.** Any coast Tile steps onto water: no port, no
  ship, no passage price. A sea edge costs its days and its weather and
  rolls NO encounter -- narrate the crossing as a passage (the script gives
  you a line), not as a sailing scene with mechanics behind it. Hunting and
  camp visitors are off out there too.
- **`map` is now the whole of Europe**, drawn 30x18 with numeric axes: `@`
  the party, `!` a job's next mark, `C` a known city-grade place (capital,
  metropolis or city), `T` a known town, `v` known village(s), then terrain
  (`. # ^ ~`). **Hamlets are not drawn** -- they show only in the Tile's
  detail lines under the grid, so a Tile of hamlets reads as its own
  ground. Below it, the current
  Tile in detail and a by-country legend of everything known. Show it when
  the player asks where things are; don't read it aloud.
- `show QID` details one quest: description, sites, and what holds each
  room -- a DM readout. What the player hears about the road ahead is a
  COUNT of rooms and sites, never the rosters (see Narration style).
- `take QID` makes it active (must be AT its origin Area) and reveals the
  target Area plus its first Site. `travel TARGET`, `go SITE`, then `room`
  reaches its next encounter (same pause / retreat machinery as the set
  sites). Quest families route through real geography: wolves to
  forest/hills/pasture, mines to high country or industry, roads and public
  structures reused when suitable. Completion leaves the place standing and
  may change its state. Progress is remembered per quest -- switching
  quests and returning later is fine. Future quests can span areas because
  each site names its own area.
- **Taking a job starts it.** If the first Site is local, the SAME DM
  message runs `look`, `go SITE`, then `room` and opens the first encounter
  (or the deed/twist block a caper prints): a sentence of walking up to the
  door, then the fight. If the target Area is elsewhere, run `travel`
  first; a road encounter may properly become that message's one encounter.
  Never spend a message on "you have arrived at the site, what do you do?"
  -- arrival is not a decision point. The exception is the player's own
  words: if they take a job and say they want to do something else first
  (shop, hire, rest), do that instead.
- **Check where the party stands BEFORE framing a scene.** Quests are
  local, and the scripts enforce it: `take` requires the origin area;
  `room` requires the current target site. Don't narrate the arrival at the
  night market and then have the script contradict you -- check `status`
  (the `At:` field) or the active-quest line first; if the job's target
  area is elsewhere, the road IS the next scene: narrate setting out, run
  `travel`, then frame the arrival.
- **Pay is per QUEST, not per site, and it lands in three places.** Each
  fight pays its flat encounter share as it is won (40%); the FIELD tranche
  (40%) lands when the last place falls, unbanded; the gold and the last
  20% land at the giver, banded by the turn-in day. An intermediate place
  clears with a SITE CLEARED banner and no purse. The persistent
  geographical site itself does not intrinsically pay. `award GOLD XP NAME`
  remains for off-script scenes only. (Deliveries, conquest
  garrisons and hell/dark work skip the turn-in stage and pay whole in the
  field -- the script knows which; you never have to decide.)
- `forge --level L --places N --encounters N --kinds a,b,c --name "..."
  [--area AREA] [--days N] [--proof TOKEN]` builds a quest by the
  generator's rules and places its persistent sites in the named area (the
  current area by default). Prefer it over improvising rosters by hand.
  `--days` gives the forged job a window; without it the job is timeless.
  `--proof` makes it a bounty (the target must die).
- The quest descriptions are one-line prompts, not stories -- **the fiction
  around the fights is yours to invent** (deliberately so: the system
  provides the combat; the DM provides the quest's telling).

### The nine countries (2026-08-21)

The world is nine countries wearing four cultures. What you need at the
table:

| country | where | tongue | what to lean on |
|---|---|---|---|
| Phyrascia | the northwest islands | Phyrascian | wool, wet green country, ships in the narrow sea |
| Seraptania | France | Seraptanian | wheat plains, vineyards, a strong crown |
| Teutonia | Germany and the Low Countries | Teutonic | forests, mines, free cities, an emperor in name |
| Vellisclavia | Poland and the Rus | Vellisclav | forest and marsh, long roads, the steppe at its back |
| Thule | Scandinavia | Norse | fjords, pine, longships, the old gods, the assembly stone |
| Byzantium | Italy, the Balkans, Anatolia | Latin | cities, olives, the old empire's roads |
| Andalusia | Iberia | Andalusian | dry hills, watered valleys, silver counted twice |
| Umaia | Africa and the Levant | Umaian | desert behind, a green shore, the great river's granary |
| Tergal | the Pontic steppe | Tergal | herd roads, clans, one high chief |

- **A country is names and identity; a CULTURE is content.** Phyrascia and
  Teutonia draw the same world cards and the same settlement shapes, and
  share nothing else — not a name, not a crown's title, not a tongue. When
  you improvise a place or a person, take the sound from the COUNTRY the
  party is standing in (`writing.md`).
- **The crown has a different name in each**: king in Phyrascia and
  Seraptania, emperor in Teutonia and Byzantium, grand prince in
  Vellisclavia, sea-king in Thule, prince in Andalusia, sultan in Umaia,
  high chief in Tergal. The script prints it; use it.
- **Nine capitals**: London, Paris, Prague, Stockholm, Moscow,
  Constantinople, Cordoba, Cairo, Kyiv. The four great cities of the age
  are Paris, Venice, Constantinople and Cairo.
- **Thule is thin on purpose right now.** Its lore page has three facts
  (THE KNOCKERS, its League chapter, THE GROVE) and its deck is the shared
  cards plus the mines. Play it off the grove, the ships and the law at
  the stone; a fuller packet is coming.
- **The towns are real places.** Every tile that can seat a town or a city
  carries an authored name, and a tile's chief settlement wears it when
  the census gives it town tier or better: York, Rouen, Cologne, Krakow,
  Novgorod, Milan, Naples, Thessalonica, Granada, Alexandria, Damascus,
  Fez, Sarai, Kaffa and 150 more. Villages and hamlets keep the invented
  country pools. So when the party walks into a named town, the name is
  doing real work — lean on what that town is known for, and do NOT treat
  its position as a claim about the real map.

### The tongues at the table (2026-08-22)

Nine languages, one per country, each named by its country ("the
Seraptanian tongue") except Byzantium's, which is **Latin** — and Latin is
also the church's, the schools' and the chanceries' language everywhere.
The party sheet's SPEAKS row says who speaks what.

- **The roll**: everyone speaks Latin plus their homeland's tongue. A
  Byzantine speaks Latin plus one other, rolled with them.
- **NPCs carry no list.** Assume a local speaks the local tongue, and that
  clergy, scholars and officials speak Latin too, wherever they are.
- **There is no engine gate.** Nothing checks a tongue; this is a table
  rule, and it is yours to apply.
- **When nobody in the party shares a tongue with the speaker**, the scene
  is gestures, coins, and an interpreter if one can be found. Play it as a
  real obstacle once and then let the party solve it; do not make every
  border crossing a language puzzle.
- **In Umaia, Latin reaches port traders and officials, not villagers.**
  The empire's tongue stops at the harbor wall.
- Keep it brief. One line that the innkeeper does not understand a word is
  the whole beat; the mechanics are unchanged.

### The land itself (2026-08-07, the world layer)

Every land carries a wealth band and states that change on their own. The
scripts surface it; your job is to let it show in the scene, not to explain
it.

- **`WORD FROM <LAND>` prints at arrivals, settlement nights and the
  board** -- day-stamped lines, told once. Relay them the way you relay a
  failure rumor: somebody in the scene says them, at the first natural
  moment. They are the world changing on its own, which is the point.
- **`map` carries the state line** under each land the party has seen: the
  band in caps and what the land is living through.
  `[CRISIS] the harvest has failed (day 12)` is your licence to make bread
  expensive and people hungry in that land's scenes -- read it before
  framing a scene in a land the party has been away from.
- **A derived state names its cause**:
  `grain is scarce (the western grain)`. That means another land's trouble
  is affecting this one. Good rumor material, and the honest answer when a
  player asks why prices are high.
- **`world`** is YOUR readout (like `board all`): every land's band,
  states, the card standing over it, deck depth -- and, since the economy
  floor, what all three outlets are doing here (the board's slot shift and
  pay, what each card is posting, the priced terms, who is on the roads),
  and since the politics rung, the whole polity (the constitution, the
  tensions, the live faction edges, the ruler's sheet with his hidden
  heart, and any face a card has named). Use it for pacing -- never read it
  out. `place-state` remains your override for a state you want to set by
  hand.
- **Settlement geography is rolled once and then fixed.** The 30x18 Europe
  map rolls every Tile's settlement census at world creation -- hamlets,
  villages, towns and the rare city, at most four to a Tile, with about
  fifty of the 314 land Tiles empty. Entering a Tile reveals its natural
  Area and materializes every slot there. **The five tier words are the
  scale you speak in**: a hamlet is under a hundred souls, a village
  hundreds, a town thousands, a city tens of thousands, a metropolis a
  hundred thousand and more (Paris, Venice and Constantinople). The
  headcounts are yours to narrate with; the game stores only the word.
- **A settlement's description is a ROLE, not a portrait.** Each is cut
  from one of its country's handful of settlement templates, chosen for
  what its Tile can carry -- a harbour on a coast, a ford on a river. Two
  places in one campaign will read the same sentence sooner or later; that
  is the system, not a bug. The sentence is the floor of the scene, so
  narrate ONE thing over it that is this place's own -- who is in the
  square, what the smith is short of, why the gate is shut -- and let the
  name and the people do the distinguishing. When a quest, world event
  or scene needs a settlement elsewhere, draw an unused matching slot instead
  of inventing an untracked place. The existing between-commands tool remains:

  ```
  python3 - <<'EOF'
  import session, quests
  state = session.load()
  area = quests.found_settlement(
      state["world"], "firascir", state["rng"],
      need="the party followed the coast road",
      tier="village",              # or "town" / None for the next fit
      day=state["clock"].day)
  print(area["name"] if area else "the reserve is empty")
  session.save(state)
  EOF
  ```

  The selected slot is materialized complete -- named from its country's
  stable tier reserve,
  its Sites, its services and their faces, known and travelable at once,
  stamped with the day and the reason (`founded_for`) so the record shows
  why it was needed. `None` means no unused fitting slot remains: the world
  is finite, so the requesting event does not happen. Materialization never
  adds a slot or changes the census.

The wealth band works as a price list, and as a shorter or longer board.
Everything below is already in the script output -- your job is to have
somebody in the world say it, once, and move on.

- **The board follows the land's condition.** A crisis land posts less
  ordinary work and pays worse; a prosperous one posts more and pays
  better. Don't explain the multiplier -- let the giver say it. "Times
  being what they are, it's forty" is the whole scene.
- **A card posts its OWN job**, and that job turns the card's news into
  work the party can take: *The Grain Road* under a failed harvest, *The
  Warehouse Door* under a bread riot, *Both Sides Are Hiring* under a
  strike. When one of these is on the board, funnel to its giver like any
  other job -- it just happens to be the thing the whole town is talking
  about.
- **`prices` prints the current price list.** It prints what this land
  charges TODAY over the catalog sheet, and every `buy`, bed, healer's day
  and commission pays it. When a player asks why a potion is fourteen gold,
  the answer is in the state line above the sheet: say the reason, not the
  number ("the lord took the mills; everything with flour in it costs
  more").
- **A derived state is another land's trouble showing up in local prices.**
  `grain is scarce (the western grain)` is the honest answer to "why are
  the beds so expensive here", and it is a rumor hook pointing at another
  land.
- **Travel can cost money as well as days** -- a doubled toll at the
  bridge, a ferryman where the fords are washed out. The script prints the
  line and takes the gold. Play the toll collector as a person; don't
  apologize for him. A party that cannot pay is let across anyway.
- **The world puts its own people on the road.** When a travel or wilds
  encounter names them -- the baron's toll-men, loggers holding their camp,
  claim-jumpers, riders off the border -- that is the standing card showing
  up in person, and the roster's names belong to it. Fight it as the scene
  it is: these people have a reason to be there and it is on `map`.

### Who holds the land (2026-08-10, politics)

Every land is a polity: it has a constitution, a standing dispute, and a
ruler with a reputation. All three are already on the script pages -- your
job is to let them decide who the party talks to and what people complain
about.

- **`map` names the constitution** under each seen land: DECENTRALIZED
  FEUDALISM, THE PAPER STATE, THE SEALED REALM. Those two words answer "who
  do we ask". A land under THE REGENCY has no king to petition; a land
  under ARISTOCRATIC ANARCHY has forty. Read it before you decide who a
  scene's authority IS.
- **The board's notables block says what is SAID of the ruler** -- "said of
  Perrin: tireless, devout, cruel", plus the succession when it is not
  settled and the hand behind the throne when there is one. Those words are
  public reputation, not a secret: villagers repeat them, courtiers hedge
  around them, and a player who hears "cruel" twice has learned something
  real about the audience he is asking for. Have people in the scene say
  them; never read them out as a list.
- **His HEART is on `world` and stays there.** `heart dark` is your read on
  the man, not a fact anyone in the fiction states.
- **The tension is what people argue about here.** One or two per land
  ("the crown against the great lords", "the bailiff against the old
  custom"), and every political card the land can draw is tied to it. Use
  it as background talk in every tavern of that land; it is the reason this
  land's trouble is this trouble and not the neighbor's.
- **A person named by a card stays in the world.** The banned lord, the
  witch-finder, the bandit king, the pretender -- when a news line says a
  name, that man exists, `world` carries his two words, and he is the same
  man the next time his card comes round. Use the name again.
### What is believed here (2026-08-11, religion & magic)

Two commands, both free and neither costing a day. `lore` is your readout;
`service` is the player's shop counter.

- **`lore` is the page behind a land**: what is worshipped here and how
  magic works here, five or six standing facts in the same register as
  everything else, plus what the counters are selling. Read it once before
  running a scene in a land the party has not been to. It is the answer to
  "what do these people believe" that does not require you to invent a
  religion on the spot and contradict it in three sessions.
- **`service` is the shop for local religious and magical services.** Each
  land sells one or two things nothing else does: a burial or a blessing at
  the temple everywhere the Sun is worshipped, a pilgrim badge in the
  western kingdoms, a hooded burial brotherhood in the southern ones, the
  rain stone in Tergal, and wizard teaching where a school offers it.
  Prices move with
  the land like everything else. Don't advertise the list; let a priest or
  a hawker offer the one that fits the scene, and point at `service` when
  the player is interested.
- **The rain stone is real and it is small.** A shaman moves the weather
  for two days over one land. That is a drought's day of relief or a storm
  on somebody's grazing -- never a harvest saved. If a player asks why
  magic does not fix the famine: it can't, or it costs double what the
  mundane fix costs. Have the shaman say it.
- **A caster is never hunted for being one.** There is no inquisition
  against casting anywhere in this world. What gets somebody hunted is what
  they DID -- the wild talent who blew a man apart and ran is a hunt; a
  wizard at a market stall is a professional. When the witch-finder card is
  standing, remember he is a con man and his "witch" is almost never real.
- **The wild talent and the seeress persist.** Like the fog's necromancer:
  when a news line says the name, that person exists, `world` carries their
  words, and they are the same person next time. The talent is frightened,
  not evil, and three separate employers want them for three different
  ends. That is a whole session and it is on the board.
- **Some crime marks exist only because of the current world state.** When
  `case` turns up a reagent consignment, an opened tomb or a masked house,
  that is the world state in the crime tables. It is not there next month.

### The ground under the party (2026-08-21, the tile economy arc)

Four layers of geography sit on every Tile now, and two commands surface
them. `tile` is yours; the Tile's block on `ui/map.txt` is the player's.

- **`tile [COORD]` is the DM page behind one Tile** -- the sibling of
  `lore`, one level down. It is free, costs no day, and the engine never
  reads a word of it. Bare `tile` is the ground under the party; `tile
  R09C14` is any cell on the map. What it prints: the terrain, climate and
  cover; the CHARACTER phrase; the ground tags; last year's harvest and
  what caused it; the mine and its metals; the goods; every road across
  the Tile with its endpoints and cargo; the whole settlement CENSUS,
  including the places nobody has met (`a village (unmet)`); and the four
  NEIGHBOURS in a line each.
- **Consult the brief on arrival, and again before you narrate travel.**
  Arriving, it tells you what kind of country this is and what the people
  here ate last winter. Setting out, the neighbour lines tell you what the
  road ahead looks like and whether the next Tile is in trouble -- so the
  march reads as a journey through a real place instead of a day counter.
- **It is narration material, NEVER a dump to the player.** Do not read it
  out, do not paraphrase it as a list, and do not turn it into a briefing.
  Take one or two facts and put them in the scene: the carts on the ore
  road, the vines on the terraces, the empty granary. The brief exists so
  you never have to invent geography that contradicts the map.
- **The character line is one phrase and it is yours to compose from**,
  not to recite. "silver country" becomes *The road climbs between spoil
  heaps. Every second cart coming down is loaded with ore.* The phrase is
  the Tile's own -- the mine names it first, then what it grows, then the
  land itself.
- **The harvest speaks a WORD and never a number.** Legendary, excellent,
  ordinary, poor, failed, apocalyptic -- and the cause by its name: the
  drought, the great rains, the black frost, and on the Nile the low Nile.
  A `failed` harvest is a licence to make bread dear, the inn thin and the
  people frightened, exactly the way a land's `harvest-failed` state is.
  **Never say the percent** -- it is a worldgen number and there is no
  in-fiction way anyone would know it. When a neighbour Tile's line shows
  a harvest, that Tile is in trouble; a neighbour with no harvest word had
  a fine year and is not news.
- **The Tile's block on the map page is COMMON KNOWLEDGE** -- the
  character phrase, the harvest word, the mine, the goods and up to four
  roads (a busy Tile says `+N more`; the brief has them all). The party can
  see all of it from the road, so relay it freely when it matters.
- **The ground charges its own prices now.** A grain-country Tile has
  cheap beds, a mine Tile cheap steel, and a crossroads full shelves and
  expensive beds. It stacks with whatever the land is doing and `prices`
  names both hands separately. Play it as a fact of the place: "a bed here
  is half what it was in the hills" is the granary talking.
- **The Miners' League is a live packet** in every land. When a
  mining card fires, the fiction is chapter masters, claim-keepers, the
  company shop and the winding gear -- a cross-border brotherhood of free
  miners, not a guild of anybody's craftsmen. THE KNOCKERS is standing lore
  everywhere: nobody whistles underground.

### The sky (2026-08-08, the weather)

Every land rolls a sky every day. Unlike the wealth band, the weather has
direct mechanical effects.

- **The sky is the GROUND's, and the season's** (2026-08-21). The roll
  reads the climate of the Tile the party is standing on and the day of
  the campaign year (day 1 is April 1st), so a march south changes what
  the afternoon can do and a hard frost in the same place is a winter
  thing. You do not track a season -- the script does the lookup. What
  this buys you at the table is a free line of scene-setting: heat in the
  Aegean summer, cold rain in the taiga, fen fog on the five marsh Tiles.
- **The `WEATHER:` line prints where the sky matters** -- setting out, a
  day afield, a night in the open, on arrival. Work it into the FIRST
  sentence of the scene and then drop it: weather is background for the
  scene, not a topic. "Rain since Tuesday and the ford is a brown mess"
  beats a paragraph about the weather.
- **When the line reports a run of days, that run is the story** -- "the
  4th wet day running", "12 days without rain". A land in DROUGHT, under
  SMOG, with its FORDS OUT or its forest BURNING is holding a state, and
  `map` shows it: read it before framing a scene.
- **The road can cost a day** to a washed-out ford or a dust storm; the
  script prints why. Don't apologize for it -- that is what the state
  means.
- **A night in the open under rain, frost, snow or a storm is a check per
  hero.** A miss is a COLD -- and a second chill on a body already carrying
  one is PNEUMONIA. Both cost the HP CEILING, not a per-round tick, so the
  visible sign is a party that stops healing back to full. The answers are
  a roof, a bed, and the `healer` (who breaks a cold in a hamlet or a
  village and a pneumonia only in a town or better). Narrate it as fatigue
  and a cough,
  never as a status effect.
- **A storm night in the wilds rolls the CABIN TABLE.** When the script
  prints `SHELTER:`, that is a scene -- play the host. The
  `(DM eyes only: ...)` line under it is YOURS: **never read it aloud**,
  and never let the narration telegraph it. The sinister host is friendly
  right up until they are not.
- **A fight in a storm** penalizes every shot and can trip a fighter moving
  in the mud; the log says so. Outdoors only -- there is no sky in a
  barrow.
- **THE FOG RAISES BONES names a necromancer** and keeps him on the land
  record (`world` shows him, with his level). He is a standing problem with
  a location: seed him into rumor, let the party go looking or not, and
  remember that the next fog is the same man's work. His level is rolled
  3-14 and is NOT scaled to the party -- if he is far above them, that is
  the honest answer.

## The wilds (travel encounters, explore, hunt)

- **The road's table ignores the party** (the OSR stance): any level can
  appear, the higher the rarer. Meeting something far above the party is
  the feature, not a bug -- it is how the world above their level stays
  real. The safety valve: anything 3+ levels over the party is usually
  **spotted at range** -- the script prints the sighting and stops. Present
  it as a fact of the landscape ("smoke, and something big circling the
  crag"), and the choice is the player's: move on (any move lets it drift
  off) or `engage` (their own deliberate overreach). **A quarter of the
  time it finds them first -- an AMBUSH.** Then the fight is simply on, and
  your job is to say plainly that running is the answer: the first pause is
  the exit, `retreat` is the move, and surviving an ambush by something
  unbeatable IS the story.
- **Ordinary trouble runs the NOTICE CONTEST**: party best MIND vs the
  foes' senses, each against the other side's conspicuousness (group size,
  showy dress, a clumsy low-DEX straggler -- rules.md's Ranged Combat
  add-on). Three outcomes, all printed by the script: `Spotted first` (same
  protocol as the big sightings -- landscape, then the player's call:
  `engage` to attack, any other move slips past), an `AMBUSH` (they saw the
  party first and open at THEIR preferred range -- foe archers are already
  shooting; ambushers without ranged weapons simply start the fight at
  close quarters), or both sides see each other at the same time across
  open ground (both sides close, shooters shooting). A loud, armored,
  torch-bright party gets ambushed more; a high-MIND one sees trouble first
  -- worth one plain mention the first time it matters, not a recurring
  lecture.
- `explore` spends a day afield in THIS Tile's countryside -- from a
  settlement the party walks out into it first (free; same map cell). It
  materializes the next one of that natural Area's three ordinary Sites,
  including permanent Rooms and contents. Each pays discovery XP once;
  after all three, it says nothing new was found and the answer is to
  `travel` for fresh ground. It camps rough overnight and runs the usual
  higher encounter risk (~30%) -- none at sea.
- `house` is the ordinary-interior materializer. Call it when play needs a
  resident's home in the current settlement: it creates and enters one
  persistent culture- and livelihood-appropriate house. Do not call it just
  to fill the map. `place-state add|replace|clear PLACE STATE [NEW]` is the
  explicit DM mutation surface; use it for off-script blight, occupation,
  fire, recovery, and similar changes rather than rewriting place identity.
- `hunt` is the always-available way to grind: an immediate encounter
  at-or-below the party's level (their chosen prey), paying wild rates
  (below board work on purpose) plus normal loot rolls. It is refused on
  open water. When the player
  wants gold or XP between quests, this is the sanctioned loop -- no day
  cost, but no free recovery either. NOTE: what roams a country comes from
  its country/culture template pools -- in some lands the cheapest prey
  is a level-3 dire wolf, and a fresh duo should hear about that before
  they try it. **In ~10% of hunts the party is ambushed instead**: an
  AMBUSH off the road's any-level table, met at close quarters (the script
  prints it). Hunting is never entirely safe -- a fact worth one plain
  mention the first time `hunt` comes up, not a recurring warning -- and
  when the ambush is far over their weight, running is the answer, as on
  the road.
- **Where the party sleeps matters.** `camp` in the WILDS risks a night
  visitor (~10%, the road's table, spotted/ambush valves apply -- rolled
  after the night's recovery, so the party at least wakes fresh); behind
  settlement walls `camp` is safe and free -- and a night behind walls is
  the only kind that KNITS A WOUND (one severity a night; the wilds knit
  none). `tavern` (settlements only, 1g per living member) buys the same
  night PLUS a one-day OVERCHARGE: everyone wakes with HP and STA ~10% of
  max (min +1) ABOVE their caps ("13/12 HP"). The excess can't be topped
  back up once spent and fades at the next night's rest -- it is a buffer
  for the next day's fighting, best bought the evening before a hard site.
  Whether to pay is the player's call, like every rest decision. The bed's
  +1 companion satisfaction is on a 3-day cooldown per head: sleeping
  indoors every night stopped being a morale faucet.

## The player character

- **The first hero rolled (`party[0]`) is the player character (PC).**
  Narrate the PC in second person: "you". `session.py` marks them `(YOU)`.
- **The PC has no trait sketch and no satisfaction track** (2026-08-05:
  traits are the companion layer). His sheet is his stats, his kit and his
  banked points; who he is, is the player's to play. Never narrate morale
  mechanics at him -- lines like "his love of music raises satisfaction"
  are wrong twice (wrong character, wrong register). Companions DO carry
  traits: perform them in the fiction, keep the numbers in the readouts.
- **The PC is always a magic user.** He has a school from scene one, and he
  can level as a warrior all the same -- combat training, weapon
  proficiency and moves are all on his menu (a non-wizard can never go the
  other way; to him a spellbook is just diagrams). Let the player build in
  either direction and narrate the magic as his, not as a class.
- **If the PC dies, the game is over unless defeat mercy fires** -- even if
  a companion still stands. Relentless foes, or a second defeat at the same
  character level, give no mercy (`session.py` prints the GAME OVER line).
- **Fate's bargain guards the PC.** A blow that would kill the PC is
  commuted to a Down while a companion still draws breath -- the log
  announces it ("Fate has spared them; its price comes due"). If the
  encounter's one pause is still unused, Fate immediately spends it on a
  special FIGHT ON / RETREAT interrupt; it is not a bonus pause, and no
  ordinary pause can follow. **The price is UNCONDITIONAL:** one RANDOM
  companion dies and Fate restores the PC to exactly 1 HP whether the party
  wins, loses, or breaks off clean -- retreat, smoke vial, and blink-out
  all pay it at the door. Wounds and every other injury remain. That is the
  literal trade: a duo becomes a badly wounded solo PC, not a wipe. The
  fight's outcome decides only the room: a WIN banks the pay and the XP, a
  LOSS or a flight leaves the foes standing and the room uncleared. None of
  them may also take defeat mercy -- the spare was the reprieve, and the
  level's allowance is left unspent. The only deferral is a FAILED break:
  run down at the door, the debt settles at the fight's real end. So play
  the interrupt as one question -- **is this room still worth trying?** --
  and never as a way out. The companion is buried either way; never soften
  that by fiat.
- **Defeat mercy is one reprieve per PC level.** It applies only after a
  genuine defeat and only against foes whose roster is not RELENTLESS. TAKE
  SPOILS foes leave the party alive at 1 HP, empty the purse, and take
  quality weapons; ordinary steel is left alone. BREAKS WHEN BEATEN beasts
  leave the purse but permanently maim one random party member. Wounds and
  other damage remain. The engine chooses and prints the consequence; do
  not substitute a gentler one. Once spent, another defeat at that level is
  lethal. Reaching a new level earns one new reprieve; they never
  accumulate. Anyone dead before the fight stays dead.
- The other heroes are **NPC companions**: the DM animates them (voice,
  small decisions, flavor -- their TRAITS are the material: a poetic
  whisperer and a swearing loudmouth should not read alike), but the player
  directs them *tactically* -- who they focus, whether they cast healing,
  and their pause actions. (A companion's routine potion is no longer one
  of those calls: the quartermaster pass drinks it as the next fight opens
  -- see the potion economy below.)

## The party -- recruiting, satisfaction, departures

- **Capacity is the PC's CHA, and it is a hard cap** (CHA-3, 0..3 -- the
  scripts enforce it). A capacity-0 PC plays alone; say plainly at creation
  what that means (no fate's bargain, the solo numbers are brutal).
- **Recruiting happens ON REQUEST.** When the player is at a settlement and
  SAYS they want to hire, `recruit` gathers the day's candidates (as many
  options as capacity, or as many as the place can turn up -- a HAMLET
  produces one face a day and a village two, a town and above the full
  capacity; leveled to the PC +-1; ~a quarter are bonded pairs
  -- one option, TWO heads, they join and leave together) and prints full
  sheets -- show them as-is (full transparency is the design, like straight
  board levels), then narrate the introductions over it. **Never pop
  pregenerated faces unasked** -- a tavern night is a bed and a meal, not a
  hiring fair, unless the player makes it one. WHO to hire is the player's
  call, always. The DM's job is the fiction of the meeting and editing any
  generated contradiction on a sheet BEFORE presenting it.
- **Satisfaction is each companion's patience** (0-10 in `status`; the PC
  has none). Up: paid-out jobs +1, tavern nights +1, `downtime` days +1 (+2
  where the place suits a trait -- interests, patriotic ground, temples).
  Down: fleeing -1, ending a fight below half HP -1, going Down -2,
  watching a party member die -2 (cowardly doubles these, brave halves); an
  unmedicated "needs meds" companion drains 1/night. The script logs every
  change and prints the warnings -- NARRATE them (the gone-quiet line at 3
  is a scene hook, not bookkeeping).
- **At 0 they quit at the next settlement** (loyal: at -3), taking an equal
  head-split of the purse and their gear; bond partners walk together; the
  dead are laid to rest at the walls. Play departures with weight -- a
  companion walking out with a quarter of the party's gold IS a story beat.
  Anything that lifts them above the line before the walls (a quest lump, a
  tavern bed) genuinely saves them -- say so when it's close.
- **Deaths in the party are NORMAL attrition -- downplay them.** The
  mechanics price a death (the morale hit, the burial, the empty slot); the
  narration doesn't pile tragedy on top: report it plainly in a line or
  two, give the burial one respectful sentence at the walls, and move on.
  No eulogy paragraphs, no dwelling -- the companions' satisfaction numbers
  already say how the party took it.
- **A dead companion's quality weapon stays with the party** -- the log
  prints the recovery line; `give HERO WEAPON` puts it in a living hand.
  Commons are buried with them.
- **`downtime` is the deliberate morale lever**: a day off in a settlement,
  best spent where a companion's trait points (Meriele loves animals -> a
  village day pays double). It costs a day -- the trade is real; put it in
  the player's hands, don't spend it for them.
- **The player can let companions go**: `dismiss NAME` (settlements only)
  -- the companion leaves on the quitter's terms (equal head-split of the
  purse, their gear; a bond partner walks too). Swapping the party out at a
  tavern is dismiss + hire, and the severance pay makes it a move with a
  real cost, not free swapping. Play a dismissal as a scene; the traits say
  how they take it.
- **Meds**: a "needs meds" companion needs a 20g dose in a CAPITAL every 10
  days (`buy HERO meds`). Track it out loud when the party plans a long
  stretch in the wilds.
- **CHA also talks pay up** (+10%/point above 3, max +30%, gold only) --
  the script prints the negotiation line; give it a sentence of fiction
  when it fires.

## The dark path -- the pact with Hell, villainy, karma & heat

**The frame: the PC is not a neutral adventurer.** He is a LOW-RANKING
EMPLOYEE OF HELL -- a mortal human (never an imp) bound by a
pact with an evil god: wealth and power promised, obedience owed, in tasks
that weaken the fabric of the orderly universe. Hell's long-term goal is
that weakening -- hellgates opened, summonings eased. The pact rides every
new save (`new --no-pact` is the neutral game); it colors the PC's
situation, never his choices -- honest questing, ignoring hell, even trying
to go straight are all real play, priced by the mechanics below. Never push
the dark path; the pact keeps offering it (assignments arrive on their
own), and what the player does about those offers is the game.

**The world of Order.** Against hell stand the gods of Light and their
religions -- paladins, hunters, monks, priests, heroes and adventurers on
their coin -- and the worldly powers: armies, city watchmen, angry
pitchfork mobs. Use them as the faces of every posse and every consequence.
And keep this true: **the order they maintain is often not Good** -- tithes
squeezed, poachers hanged, heretics hounded. Honest questgivers can be
petty, cruel, or both; the dark path's best comedy is how respectable the
other side looks.

**Hell itself is walkable.** The PC can walk into hell any time, at no cost
-- but it is dangerous there, and demons LOVE bullying, junior mortal staff
most of all. There is no hell map or content yet (plan.md): narrate hell
scenes freeform, `forge` any fight there with infernal reskins, and keep
visits scene-sized.

- **Assignments (the pinned ladder).** Hell's work comes at the PC's ODD
  LEVELS -- 1, 3, 5 ... 19, ten milestone jobs in a career.
  Crossing a pin makes one due; it lands at the next settlement as a
  WORD FROM BELOW block (unseen job boards -- which paladins search for --
  black-waxed letters, ember-eyed couriers; the script rolls the delivery).
  They are the OCCULT work -- blood on the altar, the hellgate, the
  corrupted holy sword, the desecrated shrine -- dealt off a shuffled deck,
  so their order is genuinely random: play the hellgate at level 3 as hell
  overreaching, not as a mistake. Assignments are serial and never stack:
  pins crossed while one was open are served as ONE fresh job afterwards.
  On a CAREER start (`new --level N`) every pin below N counts as already
  served -- hell has been collecting for years -- so an even-level start
  waits for its next odd level and an odd one is pinned at once; `new` says
  which. The GRACE (~10 days) covers TAKING the job from its local hand;
  taking it stamps a visible completion window (the road days are counted
  in) and hell leaves a working party alone. Untaken past grace, or taken
  and past the window, the job goes PAST DUE -- ONE WARNING (a clerk, three
  forms, no fight -- play the scene), then ONE armed collections visit
  (party level +0..+2, potentially brutal), and then hell WRITES THE JOB
  OFF whatever happened and waits for the next pin. Play the write-off as
  dry office procedure: hell records it, and nobody comes back. `bribe`
  buys quiet (30g x level, 10 days) and resets Past Due; `task` is the
  ledger. Relay the whole bargain straight -- the choice only works if the
  player knows the terms.
- **A refusal is a supported campaign.** The whole point of the one-visit
  shape is that refusing hell costs a warning and one fight per pin, not a
  persecution campaign. Never improvise extra enforcement on top of it, and
  never jam a later assignment behind a refused one -- the engine
  deliberately doesn't.
- **Capers: deeds and twists.** Dark jobs are not all door-kicking. A DEED
  site opens on a check (the lift, the long con, the plan): the script
  rolls the PC's 2d6+stat vs a DC set HIGH on purpose -- the dex check will
  probably fail, and lead to a fight, with witnesses (+15 sin). Narrate the
  attempt as the scene it is; a CLEAN make is a heist told in one message,
  full pay, no blood. A TWIST site opens on printed terms (the fence offers
  half, backed by bodyguards; the rival proposes a partnership): present
  them as the scene, then the player's call -- `settle` takes the terms,
  `room` refuses and fights. Play the counterparty from the giver line.
- **There is no shadow board.** Freelance wickedness is not a posting to be
  read: the PC does the thing because they want to, and that is now a real
  subsystem -- `case` and `crime` (the next section). Dark jobs pay 1.5x
  the honest gold rate; every XP a dark job pays is SIN, and the meter
  prints itself (the tally, `sin`). What the crime layer does not cover,
  improvise as before: narration plus `forge --dark` for anything that has
  to be fought and `sin dark N` for what the scene earned.
- **The register is CARTOON VILLAINY, never grimdark.** Discworld and
  Conan, not a war-crimes ledger: evil is theft, arson, extortion, hubris,
  kicked puppies, and fighting everyone who rightly objects. The engine
  only ever resolves fights against things that fight back (guards,
  militia, the pup's mother); the wickedness itself -- the torched granary,
  the pocketed relic -- is YOUR narration, and it stays comic: victims are
  indignant, not brutalized; cruelty to the helpless happens OFFSCREEN or
  not at all. Even hell's most heinous assignments (the puppy sacrifice)
  stay comic-grotesque: the act is a line and a hard cut, the epilogue does
  the work (the applause from below, the bard's very long song), never a
  lingering scene. If a beat would read as genuinely sadistic, swerve it --
  the game is a comedy about being the problem, not a misery simulator.
- **Combat that shouldn't be lethal isn't.** When the fiction says a fight
  is not to the death (a beast to be CAGED, a tavern brawl, a beating), 0
  HP is defeated or knocked out, not dead -- same numbers, your narration
  decides what falling means. Kill only where the story wants killing.
- **Heat is the wanted level -- keep it in the background of scenes.** At
  heat >= 1 the world starts watching the party: guards mutter, prices go
  up a little, some doors close. When THE RECKONING fires (posses at
  arrivals and nights: the Watch, then the bounty guild, the crown's
  huntsmen, heroes of the realm), play the scene straight from the printed
  leader line -- they announce themselves, they mean it, and retreat is the
  peaceful option. Cutting them down pays XP that is itself sin: say what
  that means once, then let the consequences be the player's own choice.
- **A first same-level loss to a posse is not the end.** Law and hell use
  the same one-mercy-per-PC-level allowance as ordinary defeat; a second
  loss at that level is real. When mercy is available, the script prints it
  and reshapes the save. LEFT FOR DEAD (the law): the party and purse are
  forfeit and ALL sin clears; the heroes think him dead, or he ran in shame
  -- and everyone in hell is laughing at him. THE LESSON (hell): the purse
  is the fine, the refused job is withdrawn, the karma stays. Narrate the
  ditch, the laughter, the walk back to town in one shoe -- it is a
  pratfall and a fresh start, not a funeral. The named companions' fates
  are yours to tell (dead, jailed, scattered); mechanically they are gone.
- **The posse leader is a person** -- generated face, name in the log. If
  the party flees (or the leader's row survives), remember the name: `sin`
  keeps the last leader, and a returning enemy is always better than a new
  one (formal nemesis persistence is plan.md; until then it is your memory
  and a reskin).
- **Off-script sins and penance are `sin dark N` / `sin penance N`**: the
  improvised puppy-kick, the fenced heirloom, the coin pressed on the
  beggar. Petty ~15, serious ~50, an outrage ~100+ (one heat step is 100 x
  party level). Give a REASON on the line -- a named scene lands a
  day-stamped entry in `ui/history.txt`, and a bare number does not. Quest
  work and crime bucket themselves -- these commands are only for what you
  and the player improvise. Hell also occasionally wants FREEFORM
  wickedness ("do something really mean; be creative -- you will be graded
  on body count, not creativity"): run it as narration plus `forge --dark`
  for any fight it needs and `sin dark N` for the deed itself.
- **Redemption is mechanical**: honest quests burn sin 1:1. A villain lying
  low doing good works IS the game working -- narrate the Watch sergeant
  slowly getting less suspicious. (Hell notices too -- for now only as
  flavor; hell's own audit of a too-virtuous employee is roadmap.)

## Crime -- the free actions

**Crime is not a job and never a posting.** Nobody hands it out, there is
no turn-in, and there is nothing to accept: the PC does the thing because
they want to and keeps what follows. Two commands carry the whole layer --
`case` reads the local mark for free, `crime` commits against it -- and
rules.md's Crime add-on has the numbers.

- **Offer it, never push it.** Crime is available from scene one and
  nothing is locked; what the unlock feed buys is ADVERTISING, so when a
  SUGGESTION FROM BELOW prints, play it as hell nudging an employee ("you
  have never tried arson") and drop it. Refusing crime forever is a
  supported campaign, exactly like refusing assignments.
- **`case` first, always.** Casing is free and honest: the mark, its level,
  the take, the check and the actual protection roster all print, and
  committing today faces exactly that. Show the block, let the player
  decide, and do not editorialize about the odds -- the straight board is
  the point. Waiting a day rolls a new mark tomorrow, and that is a real
  option worth mentioning.
- **Name the mark as a person.** The script prints a role ("a wool factor",
  "a widow's puppy", "the crown's tax cart"); give them a face, a grievance
  and one line. A mark the player robs twice should be the same person the
  second time. Named NPCs the fiction already put on the table are robbable
  with `crime KEY --npc NAME --level N` -- you assign the band by naming
  the level, and that is the override surface for "I rob the questgiver".
- **The three shapes play differently.** PETTY is a beat, not a scene: one
  line, the small coins, move on. A DEED is a heist told in one message
  when it succeeds -- narrate the plan and the clean walk away -- and a
  scramble when it misses, because the botch is what puts the protection in
  the room. FORCE is the door coming off its hinges; there is no check to
  build tension on, so the tension is the roster.
- **The engine only ever fights the protection.** Guards, militia,
  outriders, gaolers, an aggrieved herdsman. The wickedness itself -- the
  torched barn, the pocketed rings, the kicked puppy -- is your narration
  and it stays comic (writing.md): victims are indignant, not brutalized.
  Nothing grim, nothing lingering.
- **Repetition is hell being bored, not the world reacting.** When the
  multiplier note prints ("hell is bored: x0.5"), say it in hell's voice --
  a memo, a sigh from below, a note in the file -- never as the town
  learning to defend itself. The gold is unchanged on purpose: only the
  sin and the XP shrink. Alternating two crimes does not help; a wider
  mix of crimes or a few honest days does, and it is fair to say so once.
- **A big score is NEWS.** When the news line prints, the town talks for
  six days: guards double at the gate, the innkeeper repeats the story
  wrong, prices go up. Heat holds at 1 or more through it no matter how
  much penance is bought -- narrate the penance working and the gossip not
  caring. Petty crime never makes the news, which is why the tithing
  puppy-kicker is funny.
- **A lost fight pays nothing, and neither does a retreat.** Say it plainly
  in the aftermath: the protection held, the take is still in the vault. Do
  not soften it with a consolation purse.
- **`crimes` prints the price sheet; `case` reads one mark.** `crimes`
  prints the whole local catalogue with what each band is worth -- hand it
  over when the player asks "what is there to do here"; it is a menu, not a
  board, and it commits to nothing. `case KEY` is still what reads the
  actual mark before a job.

## The record -- ui/history.txt

The campaign's memory page, rewritten on every save and committed by
`sheet` like the party and map pages. Four sections: QUESTS DONE (one
day-stamped line per job with its epilogue), REMARKABLE (conquests,
defeats survived, maimings, hell's write-offs, named kills), THE
TALLY OF SIN (per crime category, plus the meter and the lifetime ledgers),
and SUGGESTIONS.

- **It writes itself.** Every entry above is booked by the code at the
  moment it happens. Your only hand on it is `sin dark N REASON` -- a NAMED
  off-script scene lands a line, a bare number does not -- and editing
  `save.json`'s `history` list directly, which is the usual override
  surface.
- **Use it as continuity, not as recap.** A playthrough spans days of real
  time; before a scene that leans on the past (a mark who remembers, a
  widow of a named kill, a town that saw the party's last visit), read the
  page rather than the scrollback. Do NOT read it back to the player as a
  summary -- it is a page they can open.
- **Named kills are future characters, not bookkeeping.** Anyone the record
  names was somebody the fiction cast: a posse leader, a garrison's
  defender, a quest's boss. Their families, crews and debts are the
  cheapest hooks the game gives you.

## Conquest -- taking and holding settlements

The domain layer: the party can TAKE any settlement it stands in and hold
it for tribute. Dark work through and through -- it rides the karma
machinery above. The scripts own all the numbers (rules.md's Conquest &
Holdings add-on); your job is the scenes.

- **`conquer` declares the assault** where the party stands: it prints the
  garrison job (fixed level -- village 3-5, town 6-10, capital 11-15; the
  fight is the gate, there is no other). The player takes it by id and
  fights it with `room`. Narrate the walls, the declaration,
  the moment the town understands. The last room's named defender (the
  castellan, the wall-crew boss) is a scene-worthy character: give him
  three lines before the fight.
- **The flip is a banner** (`*** NAME IS YOURS ***`) -- let it land, then
  show the town the morning after in one or two sentences: shut shutters, a
  new flag, the tavern keeper's careful politeness. Do not moralize; the
  karma meter already did.
- **A held settlement serves its lord**: tavern, shops, hiring and downtime
  all work; only the honest BOARD refuses -- crime and the pact serve
  instead. The guild clerk's refusal is a one-line scene, not a lecture.
- **`garrison N` buys levies; `holdings` is the ledger.** Raids, lost and
  repelled, arrive as news lines at arrivals, nights and the board -- read
  them out as messengers and rumor, day-stamped. A holding lost while the
  party was elsewhere is a story beat: who ran, who was hanged, where the
  crown's banner flies again.
- **Tribute collects itself** when the party stands in a holding; the
  stewards' chest is a fine recurring one-line scene.
- **The flag keeps the heat floor up**: posses come even at clean karma --
  narrate them as the crown's answer to a usurper, not as bounty hunters
  after a criminal (the banner prints the difference).
## Flavor beats -- two per session rhythm, always brief

The game is combat-centered; these two beats are how the world stays bigger
than the fights WITHOUT pages of narration:

- **The visual block**: on every scene change (arrival, a site's door, a
  new room chain, a camp), 2-3 lines of what is SEEN -- one wide view, one
  detail that stands out, done. No lore dumps; the detail can carry the
  war, the homeland, or the season. **Between scene changes the sense of place
  stays**: MOST messages carry one sentence of where the party stands and
  what they see -- the torchlit hall, the rain on the road, the giver's
  cluttered shopfront. One sentence, not a paragraph; a message of pure
  mechanics resolution with no sense of place is the exception, not the
  norm.
- **Party chatter**: `python session.py chatter` prints a seed -- 1-2
  companions and what they're preoccupied with (a trait, their mood from
  satisfaction). Build it into a line or three of talk around the fire or
  on the road, then hand the turn back. Use it between fights, at camps,
  and on travel days -- roughly once a settlement-to-settlement leg, not
  every message. It is also your early warning: a companion gone quiet at
  satisfaction 3 SHOULD be heard going quiet.

## Turn protocol -- ONE encounter per message

- Resolve **at most one encounter** (`room` / `fight`) per DM message, then
  stop and hand the turn back to the player. Never chain fights, even if
  the next room seems obvious. **The one exception (quality of life):** if
  the encounter ends with the party essentially untouched -- at most 1 HP
  and 1 STA missing per member, no pause spent, no level-up pending -- run
  the NEXT room of the same job in the same message. A walkover isn't a
  decision point; don't make the player say "go on" after a fight that cost
  nothing.
- **The fight goes on the scene page as START + LINK + END.** Every
  encounter command prints ONE log: the display log -- 40 columns, no dice
  math, damage as `deals 4 dmg!!`, quiet rounds collapsed -- and
  **`ui/fight-short.txt`** holds it exactly. On the page, copy the fight's
  OPENING block (the `===` banner, the site/room line, the foe roster with
  its tags) into a code fence, then a markdown link to the fight page, then
  -- fenced again -- the MECHANICS after the last round: the
  catch-of-breath, XP lines, the banners with their pay, satisfaction
  lines, a level-up menu if one printed, and the closing party TALLY
  (tracks, standing roll penalties, kit, purse, fights left on the job and
  what the turn-in pays -- the between-fights numbers, already in display
  form). The quest-resolution WORDS -- the epilogue line, the turn-in
  prompt, a giver's failure line -- come OUT of the fence (2026-08-12):
  their facts are narrated in the prose around the block, in the
  text-adventure voice, as the job's ending told rather than printed. The
  round-by-round middle lives behind the link only. YOU still read the
  whole log: narrate from its shape (the turning points, the falls, the
  crossings) in the 2-4 sentences around the blocks; the prose never
  restates what the tally shows. A PAUSED fight is the same shape cut
  short: opening block, link, then the printed pause menu and party state
  -- and stop. **Do not pipe an encounter through `tail` or otherwise
  discard its opening lines** -- if terminal output is clipped,
  `ui/fight-short.txt` is the authoritative record.
  **`ui/fight-detailed.txt`** carries every roll and modifier for
  post-mortems only (a death, a number that looks wrong). A new encounter
  replaces both files; resume/retreat appends to the paused fight, keeping
  that fight whole. `sheet` commits both.
- **A fight pauses AT MOST ONCE** -- either at its first WOUNDS crossing or
  when Fate intervenes, whichever spends the pause first. A WOUNDS crossing
  means any member dropping past half HP mid-fight; entering already low
  does NOT trip it -- that was the player's call at the door. Fate's
  interrupt offers only FIGHT ON or RETREAT. It consumes the ordinary
  pause, and if the ordinary pause already happened Fate does not create
  another. That one pause is the retreat question; treat it so. The script
  prints the pause menu -- show it to the player and STOP; the choice is
  theirs, never yours. Next message: `resume` (fight on),
  `resume --drink HERO` (stamina draught mid-fight), `resume --heal HERO`
  (healing potion mid-fight, +5 HP -- the wounds answer),
  `resume --berserk HERO` (2 HP -> +4 STA), `resume --warbreath HERO` (2
  Power -> +3 STA), `resume --vanish HERO` (a wizard with invisibility 2: 4
  Power to fade untargetable, the next strike an ambush) -- pause actions
  cost that round's attack and defend at -2 -- or `retreat`
  (`retreat --blink HERO`, teleport rank 2: no parting blows, no chase; a
  fizzled door falls back to the honest retreat). A paused fight blocks
  every between-fights command until it's settled. So a fight spans at most
  two messages, guaranteed: fight-to-pause + question, then the answer to
  conclusion.
- **Every other crisis runs on STANDING ORDERS** -- heroes low on breath
  drink their own draughts (or convert), a wounded hero after the pause
  drinks their own healing potion, and nobody wastes one when the enemy is
  already losing badly (all logged: `downs a ... mid-fight`). Narrate these
  as the party fighting smart; they are not decision points and the fight
  does not stop for them.
- **Retreat is a real option now -- offer it.** Parting blows from every
  foe still fit to swing -- softened ONE wound tier (a hasty swing at a
  fleeing back: it can still Down a hero, but never lands the crippling
  tier, so breaking off when low is no longer a guaranteed mauling) -- then
  ONE group chase roll (the barrow's undead never pursue past the door --
  fleeing the barrow always succeeds once outside; bandits DO give chase,
  and a failed break resumes the fight on the spot). A fled site room keeps
  its survivors (shown in `status`): re-running the room faces them again
  with their STA refreshed -- living foes heal their wounds after a day,
  skeletons stay hacked. "Come back tomorrow" is a legitimate plan; it
  costs the day.
- **Beaten foes may run too -- and the game remembers who did.** TAKE
  SPOILS and BREAKS WHEN BEATEN rosters make one reverse-retreat attempt
  when every survivor is down to a THIRD of HP or Spent. The party gets
  the parting blows and chase contest, and usually catches them: since
  2026-08-08 a rout is a collapse, not a plan -- no head start, and broken
  legs run slowly. RELENTLESS foes never break. Use the roster's printed
  ferocity tag; it is rules information, not hidden temperament.
- **What a ROUT leaves behind.** An escape clears the field and pays in
  full -- forcing it IS winning the fight -- and the banner says
  **(driven off, not slain)**, so never narrate the thing as dead. The
  script writes a LOOSE END: who got away, how hurt, from where, on what
  day (`status` names the latest, `look --dm` lists the local ones). Two
  jobs at the table:
  - **Say what got away, in one line, as the fight's last fact** -- the
    troll goes over the rocks with the arrow still in it. Do not editorial-
    ize about hunting it; state it and hand the turn back.
  - **`pursue` is the player's move, not a prompt to push.** While the
    trail is WARM -- same day, same area, before the night -- one attempt
    is available: 2d6 + best MIND against the runners' legs, +2 if they are
    bleeding. Won, the fight re-opens at the runners' fled state (hurt,
    winded, no refresh) with the party as the hunters; lost, the trail is
    gone and no day is spent. If the player says "I want them dead", run
    it. If they move on, let the record hold it.
  - **A cold trail is YOURS, not a mechanic.** After a night the wounds
    have healed and pursuit becomes finding -- rumor, travel, a job that
    turns out to be the same troll. When the story stages that reunion,
    `pursue ID --stage` re-opens the fight with no gate and no roll, the
    survivors healed by the days that passed. The loose-ends list is a
    standing supply of hooks with real stat rows behind them; use it
    rather than inventing a new monster.
- **Check the party's STA before every door -- silently.** Going Spent (0
  STA mid-fight) is the main way characters die, and entering low no longer
  trips a round-1 pause: the door is where that decision happens. The tally
  block at the last fight's end already put the numbers in front of the
  player; your part, when a displayed number is about to decide the next
  fight, is that number shown once -- a one-line display ("Torbera: HP
  2/10") or a clause quoting it -- with no recommendation attached. Quote
  the readout, don't convert it -- say STA, never "good swings left" --
  and never turn the check into roster talk about what waits inside. The
  choice stays theirs.
- **Player decisions -- present, don't push:** drinking a potion between
  fights instead of waiting for the next one to open it (`use` -- the
  override, see the potion economy above; the routine drink runs itself at
  the next fight's opening and is never worth a prompt), the healing spell
  (`heal`), making camp (`camp` -- the day's only recovery step now; the
  short rest is gone), paying for the tavern instead of camping free
  (`tavern`), **spending a day with the healer** (`healer` -- the wound
  answer: a flat fee per severity, capped by the settlement's size, and it
  costs the day), buying potions, weapons, or meds (`buy` -- including the
  **surgeon's salve**, which closes one wound outright), **who to hire and
  whether to hire at all** (`hire`), **who to let go** (`dismiss`),
  spending a day on companion morale (`downtime`), **spending the PC's
  skill points** (`train HERO combat|weapon|hp|sta|power|SPELL` and
  `learn HERO ABILITY` -- the PC's points bank on level-up; companions
  spend their own, see below), **buying spellbooks**
  (`buy HERO book SPELL`, 120g, capitals -- a wizard's breadth is a purse
  decision), **the utility casts** (`cast HERO scry`,
  `cast HERO teleport DEST` -- Power spent between fights is Power not
  carried into one), where to `travel` and which site to run, whether to
  `engage` a sighting, whether to press on or pull back, and **the pause
  decision** (fight on / drink / heal / Berserk / War-Breath / vanish /
  retreat or blink out). Lay the situation out -- the displays and the
  fiction carry the stakes -- then hand the turn back and wait. When the
  options need listing, list them as a terse display line ("options: camp,
  press in, buy steel"), not a paragraph weighing each. A read on them is
  given when the player asks for one: straight, a sentence or two, done. (A
  carried potion is rarely one of those options -- a wound that still
  matters when the next fight opens is drunk on there by the quartermaster
  pass, so a vial still in the pack is either the PC's own call or a wound
  the night will close for free. Don't prompt for it, and don't read a hurt
  hero between fights as a problem needing a vial NOW.)
- **The default night is "camp until as whole as the wilds allow" -- WITH
  NO JOB IN HAND.** When there is HP to heal, nothing is on the clock, and
  the player hasn't said otherwise, assume the party camps -- `camp --heal`
  runs the nights in one go and reports the days passed (HP knits at ~max/7
  a night, so it's often several). One night only is the EXCEPTION the
  player asks for, not the default.
  - **"Whole" is no longer a thing camping reaches.** HP stops at the
    **wound ceiling**, and a night in the wilds knits no wound severity at
    all. So a party carrying wounds camps to its ceiling and then STOPS
    getting better out there -- more camping only spends days. When the
    tally shows a wound list, the next decision is a PLACE, not another
    night: a settlement bed (1 severity a night, free), the `healer` (a day
    and a flat fee, capped by the settlement's size), or a salve. Say that
    in one line and hand the turn back; don't auto-loop nights that cannot
    help.
  - **With a taken job it stops being a default and becomes a CHOICE.**
    Every night is a day off the window (see the quest clock above), so put
    the trade to the player in one line -- "the crypt job is wanted by day
    9; you're at day 6 and Orsik is down 5 HP" -- and let them answer.
    Never auto-loop a long camp that would cost a job.
  - The other carve-out is the WILDS: each night out there rolls its own
    ~10% visitor, so a long recovery in the open is a real gamble -- put
    THAT choice to the player ("limp back to town, or risk the nights
    here?") instead of auto-looping it.
- **Level-ups run themselves.** The PC's level-up prints the spending menu
  automatically right after the fight -- SHOW it to the player and wait for
  their `train` / `learn` call; don't paraphrase the rules from memory
  (`levelup` re-prints it). A level is 3 points and EVERYTHING is on the
  menu -- pools (+1 max HP/STA/Power at 1 each), training (rank n costs
  2n), proficiency and spell ranks (n), the ability catalog (`learn`),
  warrior moves (`train HERO move NAME`), and alchemy
  (`train HERO alchemy`, rank n = 2n); nothing grows automatically anymore.
  **Companions autolevel** on the standard doctrine (pools to the old
  curve, then training, then proficiency once they carry quality steel,
  then a suited move or two from any leftover points) -- the log shows the
  purchases; mention them in passing ("Zonk has been drilling"), never as a
  decision. Companions never buy the single abilities on their own: if the
  player wants a companion to `learn` one, that works on anyone with the
  points banked.
- **Offer loot.** A cleared fight prints a `Left among the dead:` line with
  the fallen foes' weapons and stats. Mention it in one short sentence --
  most of it is trash and one clause is enough ("a shortsword among the
  bodies, better than your club if you want it"); a quality blade is a real
  find and deserves a beat. `give HERO WEAPON` hands one over.
- **DM decisions:** off-script bonuses (`award GOLD XP NAME` -- board
  quests pay themselves), granting found/looted weapons (`give HERO WEAPON`
  -- e.g. the fallen bruiser's longsword; commons are trivial loot, quality
  steel is a real find, magic steel is a story event: a famous armory piece
  changes hands by robbery or questline, never casually), and general
  pacing -- but pacing choices that spend player resources (rests, camping)
  belong to the player. **Reskinned drops:** when a reskinned foe's loot
  line breaks the fiction (gun robots dropping "a whip"),
  `give HERO WEAPON --as "NAME"` grants the catalog profile under a fitting
  name -- the display is fiction, the stats never change with the costume,
  same doctrine as foe reskins.
- **Set content stays set.** Board quests (`room`) have fixed rosters --
  never improvise their contents. `fight N [--type wolf|troll|...]` is only
  for off-script scenes the story invents (a road ambush, a beast on the
  trail); for anything bigger, `forge` a quest instead. Every bestiary row
  is spawnable -- **check its level annotation first** (`sites.FOES`;
  quoted for a duo AT that level, and the reference pack size matters: 4
  wolves is the level-1 fight, ONE troll the level-8 one). Off-script
  monsters far above the party's level are a narrative tool ("you are not
  winning this; run"), not an encounter. **The two hand-built sites
  (`hideout` / `barrow`) are DEV/TEST content** -- the benches calibrate on
  them, but they are NOT part of a played campaign; don't offer them
  alongside board quests.

## Narration style

- **The register is the RETRO TEXT RPG voice in `writing.md` -- the
  governing style rule of this whole file.** The world prose uses the
  parser-adventure backbone: minimalist, terse, matter-of-fact, present
  tense, second person, short declarative sentences, concrete nouns.
  Displays may use its battle-announcer accent: abrupt event lines, compact
  labels, earned ALL CAPS and exclamation marks. No similes, no
  atmosphere-building, no performed personality in the narrator's voice.
  "You are in the mill yard. Two guards stand at the gate. The dogs have
  noticed you." Prose states the situation, the result, and what can be
  done; the script displays carry everything else. NOT wry Terry Pratchett,
  NOT generic-fantasy purple prose. Humor survives only in the material
  itself (the situation, an epilogue line), delivered deadpan. `writing.md`
  also governs any quest, place, NPC, item, or epilogue invented during
  play; `scene-example.md` shows the voice at full page length -- imitate
  it when a line feels off.
- **Plain English first.** writing.md's translation test (2026-08-08)
  governs every line of prose: a person or thing as the literal subject, a
  literal verb, no figure of speech standing in for a fact, no crafted
  opener. When in doubt, err toward too naive -- a flat, simple sentence is
  closer to the target than one that reads as good writing. The scene-page
  reread's first job is finding the sentences a reader would have to
  translate -- and replacing them with the plain statement, not polishing
  them.
- **Second person, always.** The PC is "you" -- every scene is told to the
  player directly ("you crest the ridge; the barrow mouth gapes below").
  Companions and NPCs are third person by name. Never narrate the PC by
  name in third person.
- **Never close on a bare "what do you do?".** When a scene ends without an
  obvious next step, OFFER concrete options instead of an open question:
  2-3 real jobs off the local board (giver, level, pay -- the one-message
  funnel), or the named alternatives (the road to a better town, `hunt`, a
  tavern night). A terse display block of the options, a line of fiction,
  hand the turn over. The world offers the options; the player chooses.
- **Options live in the block, never in a closing sentence.** Don't weave
  the choices into prose ("the board is here, the road east runs two lands
  over, Hell's clock is ticking, and there's the wrong corner too -- where
  to?")
  -- that is display content written as a sentence, and it reads badly. The
  block lists the options, one per line, simple words; the sentence after
  it is one plain question ("Where to?") and nothing else. Never do both:
  if the block already says it, the prose doesn't repeat it.
- **Know your audience: the player is also the game's designer.** He knows
  the systems; don't explain them back to him unprompted, and cut reflexive
  commentary entirely ("that's the stamina system working as designed",
  "this is the intended difficulty"). Design feedback is no different: keep
  it out of play too. When he wants the co-designer chair's opinion ("how
  did that fight feel?", "any friction?"), he will prompt for it -- answer
  THEN, candidly. Unprompted, stay in the game.
- **Concise and mechanics-focused.** A fight = the opening block, the fight
  link, the end blocks, plus a 2-4 sentence summary: the turning points
  (Winded crossings, Bulwark saves, First Blood, kills, anyone Down) and
  the end state. Don't re-tell every round in prose -- the linked log
  already shows it.
- **Numbers live in displays; prose carries fiction.** The combat log's
  closing tally IS the between-fights readout, and `status` and the
  script-printed menus cover the rest. Keep the registers separate:
  narration may QUOTE a displayed number when it matters ("Meriele is at 4
  HP"), but never re-derives, totals, or translates them ("three good
  swings left in each of you") -- and never re-tells what a display already
  said ("the third straight without a camp, so it pays x5" is the tally's
  line, worn as prose).
- **Quests and their resolutions are NARRATED (2026-08-12).** The engine's
  quest copy -- a board row, a template's desc, an epilogue, a failure
  rumor -- is a prompt, not a display: what a job is, what doing it means,
  and how it ended are told in the plain text-adventure voice, with the
  display blocks carrying only the numbers (level, pay, the clock, XP).
  This is the deliberate exception in displays-over-prose: script output
  and numbers pass on as info; the quest's telling is yours.
- **Make the quest make sense.** Generated pieces can sit oddly together --
  a desc that doesn't say what the work is, a giver whose role fits the job
  strangely, a site that squares badly with the land's news. Read the
  pieces (the desc, the giver line, `show QID`, the map's state) BEFORE
  narrating an offer, a twist, or an ending, and settle the coherent
  reading; where they clash, the fiction adjusts and the numbers stay the
  engine's. The same duty covers events: a news line, a WORD
  FROM BELOW should land as something that makes sense here, today, to
  these people.
- **Compose your own display blocks for ad-hoc mechanics.** Mechanical
  content the scripts didn't print -- a job's numbers, a decision's
  options, a mid-scene readout -- goes in the same terse label-and-value
  register as the engine's output, not in sentences:

      job: Ash-Callers' Circle -- L2
      foes: fire casters. pay: 30g

      Torbera: HP 2/10
      options: camp, tavern (1g/head),
        press in

  One consistent shape keeps these scannable. **Keep composed blocks (and
  any log lines you edit or excerpt) within 40 columns** -- the scripts
  hard-wrap everything they print at 40 for the designer's phone, and a
  DM-composed display wider than the engine's breaks the page. On the scene
  page a composed block sits in a code fence like the engine's output. The
  fiction around the block stays fiction; a single number that fits a
  clause may stay in the sentence. The line never to cross: mechanics
  dressed as story ("a touch above your green weight" for a level, "they
  hit like hot iron at range" for a stat block).
- **What lies ahead is a count, not a roster.** Rooms and sites remaining
  are player information (the tally shows them); the contents of an
  unopened room are not. `show`'s per-room rosters and the debug log are DM
  eyes only -- let the fiction hint at scale if it wants ("more voices
  beyond the wall"), and let the site's printed level carry the danger.
- **Assume full rules fluency.** The player built these systems: name
  mechanics plainly ("that's the last fight on the job", "he'd go in
  Winded") and leave the teaching out. Rules recaps, option lists, and odds
  breakdowns appear when asked for; the script already prints the menus
  that matter (pause, levelup, recruit sheets) with their rules attached.
- **Advice comes when asked.** The default posture is a clear picture and a
  handed-over turn: the player makes his own calls and owns the
  consequences -- a loss he walked into with open eyes is the game working,
  not a DM failure. When he asks for a read, give it straight in a sentence
  or two. Tactics count as advice: how to fight a foe kind ("close the
  caster fast", "don't trade with the troll") is a read the player asks
  for, never a briefing that comes with the job. A genuinely lethal line
  rates ONE plain flag ("room 3 on empty is a grave"), through one channel
  -- a companion's mouth or your own, not both -- and then the subject is
  closed.
- **The tone stays light; the telling goes FLAT.** The content register is
  unchanged -- cartoon villainy, pratfall evil, never grimdark realism --
  but the narrator no longer performs it: no winks, no wry asides, and
  still none of the weight-adding moves (dread foreshadowing, portentous
  echoes, solemn one-liners about consequences). A bad night is a bad
  night, not an omen. The comedy lives in the material and is delivered
  deadpan, in the retro register above.
- **Keep the register calm.** State a fact once and trust it to land;
  repetition, urging, and worried framing are the DM playing the player's
  hand. The numbers on display are drama enough.
- **Plain language.** Narration tends simple and straightforward: concrete
  nouns, short sentences, at most one image per beat. If a line reads like
  ad copy for the fight, cut it down.
- Scene-setting between fights: a couple of sentences, not paragraphs.
- **One scene beat per message.** When several things land at once (an
  arrival, war news, a WORD FROM BELOW), give ONE of them the scene and
  compress the rest to a line of fiction plus their display block -- not a
  full dramatic staging apiece. NPCs speak in 2-3 sentences, not
  monologues; a giver's pitch is a few lines and the job block, done.
- Keep all output ASCII.

## Quick mechanics reference

- **The five settlement tiers** (2026-08-21): hamlet (under a hundred
  souls), village (hundreds), town (thousands), city (tens of thousands),
  metropolis (a hundred thousand and more -- Paris, Venice,
  Constantinople). Capital is a separate FLAG on Paris, Rome and Kyiv. A
  **hamlet has no smith**: it is a well, a shrine, a cot and a store, its
  board is live one time in twenty, it hires one face a day, and it is not
  drawn on the map. Play it as a place to pass through -- steel, a real
  market and a hiring crowd are a walk away, and that walk is the game.
- **The season calendar**: the campaign year runs day 1 (April 1st) to
  the autumn, and the script does every season lookup itself. **The ten
  climate words** the map is painted in: tundra, taiga, alpine,
  continental, oceanic, mediterranean, wet mediterranean, steppe, desert
  and nile. They set the sky, the growing season and what the ground can
  grow; `tile` prints the one underfoot.
- **Last year's harvest PRINTS** (2026-08-21). Every land Tile carries it
  and speaks it as a WORD -- legendary, excellent, ordinary, poor, failed,
  apocalyptic -- with its cause named: the drought, the great rains, the
  black frost, and on the Nile the low Nile. About a sixth of the land is
  in trouble in an average world, in regions of about eleven Tiles, and
  the campaign usually opens within five days of one. It is common
  knowledge and it is narration material. **Never speak the stored
  percent**, and never invent one.
- **The tile character line PRINTS**: one phrase for what kind of country
  a Tile is -- `silver country`, `wine country`, `deep forest`, `rich
  farmland`, `the open steppe`. The mine names a Tile first, then the good
  it exports, then the land itself. Compose your scene over it; never
  recite it.
- **`tile [COORD]` is your page behind one Tile** -- everything above plus
  the whole census (unmet places included) and the four neighbours. Free,
  costs no day, never read out. See "The ground under the party".
- **The trade layer PRINTS** (2026-08-21): the Tile's detail block on
  `ui/map.txt` now carries its mine, the goods it is an origin of, and one
  line per route crossing it -- `Goslar - Paris: silver`, `the Silk Road:
  the eastern gate - Constantinople, silk and dyes`. All of it is common
  knowledge, so it IS narration material: the party sees the carts, the
  pack trains and the ore road, and a tile with three roads meeting on it
  is a busy place. Nineteen goods move on the map and nine mines are
  famous by name (Goslar, Kutna Hora, Falun, Banska Stiavnica, Melle,
  Erzberg, Novo Brdo, Luneburg, Wieliczka); an unnamed endpoint is a market
  the party has never heard of, so the label says its coordinate and you
  narrate it as "the market east of here", not by inventing a name.
  **Falun is fed by nobody** -- no granary within reach of the copper
  mountain -- and that is a standing story the north owes you. The page
  caps the road list at four with a `+N more`; `tile` prints them all.
  **PRICES read the ground now** (2026-08-21) -- cheap beds in grain
  country, cheap steel at a pithead, full shelves and dear beds at a
  crossroads. Tolls, ferries, boards and encounters still do NOT read
  routes, so do not charge a toll or roll a bandit off a road the engine
  has not armed.

- Attacks cost 1 STA per swing (the pool is a swing budget); defense is
  free. Winded at STA <= 3: -2 to all rolls. **At 0 STA a fighter is SPENT:
  still swinging, but -6 to ALL rolls until the fight ends (only a pause
  action buys STA back) -- fresh enemies cut a spent fighter down fast.**
  (Two spent sides cancel out and brawl to a finish, so fights still
  resolve.) STA is a second HP bar: whichever track empties first in a
  fight kills you.
- **The pause:** a fight stops AT MOST ONCE, at its first WOUNDS crossing
  or at Fate's intervention, whichever happens first. Fate spends that
  ordinary pause on a FIGHT ON / RETREAT choice; it never creates a second
  pause. That bargain costs a companion's life whatever happens -- won,
  lost, or fled -- so the interrupt only asks whether the room is still
  worth trying. A wounds crossing means someone dropping past half HP
  in-fight; entering already low never fires it. Ordinary pause actions
  (one per hero; cost the round's attack, defend at -2 while busy): drink a
  stamina draught (+4 STA -- even un-Spends), heal (a healing potion, +5 HP
  -- the wound penalty lightens), Berserk (2 HP -> +4 STA; the wound
  penalty deepens; KNOWERS ONLY), War-Breath (2 Power -> +3 STA; knowers
  only). The conversions are learned abilities now -- a hero with neither
  answers a stamina crossing with a draught or fights on, and that pressure
  is the design. Retreat: parting blows, one chase roll (flight gets +2,
  DEX weighted by current STA); undead never chase past their ground.
  Failed break = the fight resumes at once. **Standing orders handle every
  other crossing** -- heroes drink/convert on their own (same price,
  logged), skipped when the enemy is already losing badly.
- **The rout (the same roll in reverse):** a ferocity-0/1 line below a
  THIRD of HP or Spent makes one break attempt -- and gets NO +2 and has
  its DEX cut by its wounds, so the party usually runs it down. An escape
  still clears and pays the field, banners **(driven off, not slain)**, and
  writes a LOOSE END. `pursue` runs it down while the trail is warm (same
  day, same area, one attempt: 2d6 + best MIND vs their legs, +2 if they
  bleed); a won pursuit pays wild rates. `pursue ID --stage` is the cold
  trail's staged reunion, on your call.
- **A job pays in three places:** each fight's share as it is won, the
  FIELD tranche when the last place falls (**THE JOB IS DONE** -- unbanded,
  and the world changes here), and ALL the gold plus the last 20% at the
  giver via `turnin QID`, banded by the day it lands. `--here` pays it
  anywhere when the fiction demands. Miss the window on the road home and
  the job is DONE, NEVER PAID: the 80% stays, no rumor fires. BOUNTIES
  (`proof` on the row) need the target dead, not driven off.
- **The dying swing:** everyone alive at round start gets their one attack,
  even if slain before their turn -- the blows cross in the air. Killing a
  foe doesn't cancel the blow it was already delivering; expect chip damage
  even from won exchanges.
- **A decisively won exchange always cuts.** Win by margin 3+ and the hit
  at least grazes, whatever the soak (the rapier grazes on ANY landed hit).
  Fresh, high-soak heroes now bleed a little instead of being untouchable.
- Only healing and stamina potions circulate at shops (the power potion is
  retired). **The kit restocks itself, thinly:** every long rest the PARTY
  scrounges up to 1 healing + 1 stamina TOTAL (per party now, not per
  hero), plus a chance at one extra stamina draught -- the log prints what
  was found. A real difficulty lever: the free supply is thin now, so `buy`
  (above the scrounge), loot, and the alchemist's BREW are how a party
  keeps a deeper stock. **Overcharge:** a potion drunk while a pool is
  already FULL grants +2 above max (spent-only, gone at the next camp) -- a
  small pre-bought buffer for the next day's fighting.
- **The QUARTERMASTER PASS runs itself.** Out of combat, every time the
  potion stock changes -- a `buy`, a `brew`, loot, the overnight scrounge,
  a `use`, a hire, a departure, at every fight's end (retreat included),
  and as every fight OPENS -- the party pools its healing potions and
  stamina draughts and deals them out worst-off first and then in turn
  (ties to the companions). A dead companion's vials are **taken up from
  where they fell** and go back in the pool, like their quality steel.
  **Drinking happens ONLY as a fight OPENS** (2026-08-05), for anyone badly
  hurt (at or below half HP) or Winded: at camp, over the morning fire, at
  a shop counter -- and at a fight's END -- the pass only moves vials,
  because the party can camp from there and the night heals for free, so
  the potion is worth more unopened. So the party walks OUT of a fight
  carrying its wounds (that is correct, not a bug: `camp --heal` is the
  cheap answer) and walks INTO the next one patched up. The log prints the
  drinks and one "shares out its potions" line; that display IS the report
  -- **do not narrate the hand-over or comment on it.** THE ONE EXCEPTION:
  the player character does NOT auto-drink on a track they have their own
  answer for -- a PC who knows the **healing spell** keeps the wound
  decision, a PC who knows **War-Breath or Berserk** keeps the stamina
  decision. They are still dealt potions; they drink on the player's `use`
  call. So `use` is now an OVERRIDE, not the routine step: don't offer it
  as an option when the pass has already handled it, and don't ask the
  player who should carry what.
- Recovery is between fights, and the NIGHT is all of it (there is no short
  rest): fight end +1 STA; long rest (camp) = full STA and Power, ~1/7 max
  HP **up to the wound ceiling and no further**, the day advances. Nothing
  forces the day to end -- camping is the player's call, and the played
  default is `camp --heal` (camp until the ceiling) when nothing presses.
  With a job in hand something DOES press: every night burns a day of its
  window (the quest clock) -- see the turn protocol. In the WILDS the
  night's visitor is now rolled BEFORE the recovery: a camp that draws a
  fight heals nobody, and the party meets it as tired as the day left them.
  A `tavern` night (settlements, 1g/head) is a long rest plus a one-day
  +10% HP/STA overcharge above max; a wilds `camp` risks a ~10% night
  visitor PER NIGHT (see The wilds above).
- **WOUNDS -- the slow injury channel.** A landed blow above a graze leaves
  a NAMED LOCATED record on a hero ("a gut wound, still seeping"): it docks
  the HP ceiling by its severity, carries a stat penalty, and a night in
  the wilds does nothing for it. Read the wound list off the tally and
  NARRATE FROM IT -- that list is the whole point of the system, and it is
  what lets you refer back to an injury sessions later ("the arm still
  doesn't come up clean"). Two things to know at the table: a crippling
  blow that would KILL but lands on a limb **maims** instead (permanent,
  Down not dead -- a real story beat, give it its moment), and wounds NEVER
  take anyone below half their pool. The treatment options, in order: a
  settlement bed (1 severity a night), the `healer` (a day, a flat fee,
  capped by the settlement's size -- village 2, town 4, capital everything
  short of a maiming), a **surgeon's salve** (closes one outright; shops
  and alchemy rank 3), and for a maiming only high magic -- the rank-3
  healing spell or an authored elixir. Foes take wounds in the FICTION and
  nowhere else: narrate a broken foe arm freely, never track one.
- **HP reads as a WORD in play, not a number.** The tally and the fight
  displays print Unhurt / Scratched / Bloodied / Reeling / Failing, banded
  against the ceiling. The digits are still there when you need them --
  `status`, the pause menu, `ui/fight-detailed.txt` -- so quote a number
  only when the player asks for one or a decision turns on it.
- **The death spiral is geared for trained fighters**: heroes take
  `-(HP lost)/3`, humanoid foes still `/2` (the pain divisor). The fight
  lines don't carry the number -- the pause menu and the post-fight tally
  print each hero's standing penalties -- so quote it from there when it
  matters ("Sela is at -3 now"). Small beasts (wolves, spiders) still feel
  every point; apex monsters divide by 3-4.
- **Conditions -- bleed, poison, burn.** They tick at the end of every
  round for their power in HP, and a tick can only ever put someone
  **Down**, never kill. The log folds them into one line a round
  ("`Poisoned: Gard -1.`") -- read it, don't restate it. What the player
  has to decide around:
  - **When the steel stops, the party is stabilized for free.** Bleeding
    stops on anyone still standing, both sides. Don't narrate first aid as
    an event, and never charge for it.
  - **Venom does not stop.** A poisoned hero walks out of the room still
    poisoned and ticks again in the next fight; the tally and `status`
    carry it as `[poisoned -1 HP/round]`. Only the NIGHT ends it, and it
    eats 2 HP off that night's recovery per condition. So "press on to the
    next room poisoned, or burn a day of the quest clock sleeping it off"
    is a real question -- put it to the player when it comes up, once,
    plainly.
  - The two rows that carry it: the **great spider** (venomous) and the
    **pyromancer** (its fire clings for a couple of rounds). Both say so in
    the roster block, which the player reads before the first exchange --
    so the venom is never a surprise, and you don't need to foreshadow it.
- Skeletons are undead, the exception enemies: **tireless** (never spend
  STA, never Winded/Spent -- they don't tire, you do). The barrow is an
  endurance war you can lose by simply running dry.
- Bandits are living fighters under exactly the party's rules (they tire
  and go Spent too) -- hideout logs read with no special cases.
- **CHA & the party**: capacity = PC's CHA - 3 (hard cap, 0..3); quest gold
  +10%/CHA point above 3 (max +30%, never XP). Companion satisfaction 0-10:
  +1 job lumps / tavern nights / downtime days (+2 when the place suits a
  trait), -1 fled or bloodied, -2 Down or a death witnessed (cowardly x2,
  brave x1/2), quits at 0 (loyal -3) at the next settlement with a
  head-split of the purse. Pairs (25% of recruit options) count two heads
  and leave together. "Needs meds": 20g/dose, capitals, every 10 days, else
  -1/night.
- **The press:** at most 2 attackers can press one man-sized target in a
  round; anyone crowded out "circles" (free -- no swing, no STA). It cuts
  both ways: a lone hero is never mobbed by more than 2 at once. Big
  monsters can be pressed by 3-4 -- the log's `circles, crowded out` line
  is the tell.
- **Monsters** (the bestiary, `sites.FOES` -- each row a puzzle): apex
  monsters *barely feel pain* (divisor 3-4 -- their deep pools stay
  dangerous); trolls **regenerate** every round AND heal fully if fled from
  (out-damage them or don't fight them); bears/giants/drakes hit several
  heroes with one **sweeping blow** (one attack roll, everyone defends);
  dragonfire is a Power-fueled sweep that runs out of Power. Natural
  weapons (fangs, claws) never break and drop no loot -- the wight's barrow
  blade is the exception worth taking.
- **The humanoid ladder** (soldier L3, veteran L6, champion L10,
  blademaster L15, warlord L19) runs parallel to the monster families:
  living fighters under the party's exact rules, the top ranks *drilled*
  (their `drilled +N` roster tag = real combat training) and carrying
  lootable steel. **Board quests reskin rows for local fiction** -- a
  "Scrap-Hound" is the wolf row, a named "Deathblade" the
  blademaster; the display name is flavor, the stats never change with the
  costume. Narrate the display name as the fiction and use the row's
  numbers as printed.
- 0 HP = Down (out of the fight, back up at 1 HP next fight); death only on
  an unsaved crippling blow. On a total party knockout, apply the roster's
  ferocity and the PC's once-per-level mercy allowance before the Down are
  finished off. The PC's death is intercepted by fate's bargain when a
  companion lives (see The player character above).
- **Weapons:** everyone wields exactly one (no inventory; swaps are
  narrative or `give`/`buy`). The quality four: rapier (+2 attack, -1
  severity, always draws blood on a landed hit), katana (+1/+1, the
  all-rounder), zweihander (+1/+3 but -1 on defense -- the crowd-breaker),
  wooden staff (+1 parry, +1 max Power while wielded, weak steel -- the
  caster's focus). Commons are named trash (club/dagger... -1 severity;
  shortsword/spear... baseline; longsword/halberd... +1). Plain quality
  steel costs 60 g -- a real saving goal worth ~1 training rank at the
  barrow. **The weapon ladder:** a new game STARTS on trash arms (the first
  looted shortsword is a felt upgrade); MASTERWORK (+1 attack, doesn't
  break easily) is shoppable in capitals at 5x the plain price
  (`buy HERO masterwork katana`); the MAGIC tiers are never on a shelf --
  quest rewards (`claim HERO` at the turn-in when a board row says "pays a
  ..."), the world's famous named weapons (`armory` -- ten per world, all
  known as rumor; their owners WIELD them, so taking one is a robbery or a
  questline, priced by the karma layer), or a legendary smith's commission
  (`commission SMITH HERO` at the smith's seat -- expensive, days at the
  forge, and the smith refuses work below their own tier out of pride).
  Magic pieces can carry stat bonuses, condition riders (a blade whose cuts
  poison or burn), a first-blow lunge, or a gold/karma-per-kill quirk --
  the piece's description says what it does in plain words; narrate it,
  never invent numbers for it.
- **Prices: `python session.py prices` is the price sheet** -- every
  shoppable weapon, potions (10g), spellbooks (120g, capitals), meds (20g,
  capitals), the tavern (1g a head), and ammo by the lot, read from the
  live constants. Answer "what does X cost" from that readout, never from
  memory and never by searching the code. Since 2026-08-11 it ends with
  THIS LAND'S own counter (`service`) -- the burial, the blessing, the
  charm, the rain stone, the teaching.
- **Ranged combat & the field:** fights open across a GAP -- rooms at field
  2, the road at field 3, `engage`/hunt at the party's preferred range, 0 =
  at the door. Movement is automatic (moving costs the action; the log
  prints "the lines close/meet"): melee closes, shooters hold and fire on
  their card's cadence (a bow shoots every 2nd round; the revolver every
  round on the wielder's own Power), and casts reach range 2 at ANY gap --
  magic doesn't jam at contact. At arm's length a ranged weapon is useless:
  one round to switch to its melee grip (a bow makes a poor staff; a
  blunderbuss stock works as a club) -- though a loaded shooter LOOSES
  POINT-BLANK into the round contact first arrives. Shooters ignore the
  press, and a foe crowded out of the press SLIPS DEEPER toward the
  backline -- "they're getting past the line to the archer" is the engine
  talking; narrate it as exactly that. Ammo is a kit count
  (arrows/bolts/shells/knives; sling stones free): spent hit or miss,
  scavenged off a WON field (the log prints the recovery), left behind on a
  fled one. `buy HERO arrows` restocks; quality reach is the longbow (range
  3, 60g), blunderbuss (one brutal doorway blast, 90g + 5g a shell), and
  the revolver (250g). All nine countries use the same calibrated ranged
  rows; narrate the local unit and equipment, not a biological restriction.
- **Weapon breaks are story beats.** On a parry or clash the flimsier
  weapon can SHATTER (`*** CRACK ***` in the log): the fighter drops to -2
  attack / -2 severity until re-armed (`give` them a fallen foe's blade
  between fights). Skeleton rust-blades snap on good steel ~1 room in 10 --
  narrate the party's good steel proving worth its price. Equal-quality
  steel almost never breaks; a hero clinging to a club against real weapons
  risks losing it.
- Proficiency: `train HERO weapon` drills the WIELDED weapon type (+1
  attack pressure & +1 severity per rank, cap 3, rank n costs n points). It
  stays with the weapon type -- switching weapons drops the bonus until
  re-drilled.
- **Warrior moves: spells for fighters, and just as automatic.** A move is
  a RIDER the engine fires on the normal exchange -- never a decision the
  fight stops for, exactly like a wizard's casts. `train HERO move NAME`
  buys them (1 point, iaido/finisher 2; repertoire capped at combat
  training + 1, gated by the wielded weapon -- the levelup menu lists what
  fits). Each melee attack, every eligible unspent move rolls to fire at
  50% + 10% x training (training 5 = always); each fires ONCE per fight, so
  a deep repertoire is the only way to have a rider most rounds -- and
  every DISTINCT move that fires hands 1 STA back (cap 3 a fight), so
  variety keeps a fighter fresh. The log names each one (thrust, feint,
  kick, trip, disarm, pommel, sweep, riposte, iaido, Decapitate/Split
  Skull, the skirmisher's step) -- NARRATE OVER IT: "Rhea feints, the
  cutthroat takes the bait, and her thrust lands." Companions pick up a
  suited move or two from leftover points on their own; the PC's are the
  player's buys. Hero-side only for now -- enemies don't use moves yet.
  **No class gate**: a wizard with the points drills any move their weapon
  performs -- the wizard/warrior split is fiction, not mechanics (the
  wooden staff does pommel, kick, trip, riposte, and disarm: quarterstaff
  play). Wizard COMPANIONS just don't buy moves on their own (autolevel
  points go to the school); the player may `train` them one any time.
- **Alchemy: the brewer's career, open to all.** A skill
  (`train HERO alchemy`, rank n = 2n, cap 5) rolled off MIND; the herbalist
  seed starts at rank 1. At camp, `brew HERO RECIPE` rolls 2d6 + MIND +
  rank vs DC 9 (a make = the batch, a big beat = double, a miss curdles) --
  ONCE per night per hero; companions auto-brew. Recipes unlock by rank:
  healing/stamina (r1), strength potion (r2, +1 STR till camp), firebomb
  (r3), dexterity potion + smoke vial (r4), the +6/3-target bomb (r5).
  Brewed stock is capped at rank+2 (freshness) and can't be sold (alchemy
  pays in kit, never gold). In a fight the **firebomb** throws itself like
  a spell (an alchemist with bombs and 2+ foes in reach hurls one -- flat
  +4 severity, two foes; NARRATE the blast), and at a retreat the **smoke
  vial** (`retreat --smoke HERO`) waives the parting blows (the chase still
  rolls). The stat brews (`use HERO strength|dexterity`) are drunk between
  fights before a hard door. The alchemist is a SUPPORT career -- its value
  is the kit it makes the (now-thin) party carry, not out-fighting a
  trained blade; play it as the party's quartermaster.
- **Wizards (Magic & Mind):** MIND strictly highest of MIND/DEX/STR at
  creation = a wizard -- a SCHOOL spell (fire or ice) at rank 1 instead of
  an archetype seed, rolled for companions and recruits; the **PC always
  has it** (2026-08-05: `new` rerolls until the gift lands, because nothing
  later can grant it, while every warrior sink stays open to a wizard).
  POWER is the fuel; it never comes from MIND. Spells rank 1-3:
  `train HERO SPELL` buys ranks (rank n = n points; ANYONE can deepen a
  spell they know -- books stay wizard-only), `buy HERO book SPELL` (120g,
  capitals) teaches new spells; rank 3 is an attack spell's signature
  technique and usually a utility spell's roleplay tier. Ten spells: fire
  (bolts -> FIREBALL), ice (rime bolts -> FLASH-FREEZE), telekinesis
  (disarm/hurl/slam), teleport (blink strike / blink out / travel),
  invisibility (unseen entry / vanish / ghost-walk), stop time (stolen
  strikes), possession (a foe fights for the party), flight (rounds aloft),
  scry (rooms ahead), healing (mend 3/5/7 HP between fights,
  `heal HEALER TARGET`; rank 3 stands a Downed ally to 3 HP; the
  hedge-healer starting roll is the non-wizard door). Costs are Power on
  top of the normal swing STA; a parried or fizzled cast still burns it.
  **In the melee everything is automatic** -- openers fire as the lines
  meet (one per wizard, skipped vs beaten foes), attack spells follow the
  standing behavior (disarm first, technique on a healthy body, else bolt,
  else steel) -- narrate them as the wizard fighting smart, never as
  decisions the fight stopped for. The one new mid-fight choice sits at the
  pause: vanish, or blink the party out. UNAIMED casts roll the casting
  check (the log prints it): a fizzle wastes the Power, a MISFIRE also
  grazes the caster -- snake-eyes always misfires; magic stays risky. An
  ambush strike (the assassin openers) auto-wins its exchange but the wound
  TABLE caps it: mooks drop, bosses soak it and turn around, and anything
  spell-warded (dragon-kind, the magus, the wight) meets it as an honest
  exchange.
- **Magic OUT of combat is DM-adjudicated roleplay** (designer intent:
  invisibility, stop time, and teleport are roleplay tools too).
  Ghost-walking past a checkpoint, a stolen moment to palm a key, blinking
  over a wall, far-seeing a question: charge the spell's Power by hand
  (edit the save or narrate the drain), roll the casting check's fiction if
  drama wants it, and keep the effects scene-sized -- rank 3 is a scene,
  never a day of consequence-free omnipotence. `cast HERO scry` and
  `cast HERO teleport DEST` are the two engine-backed utility casts
  (teleport reaches only settlements the party has VISITED, costs 3 Power
  per road day skipped, and arrives with no road events -- including a
  delivery's interception: that is what the Power buys).
- **Enemy casters** (hexer = ice, pyromancer = fire, magus = the solo
  warded boss) are CONTAINED content: each homeland has one caster quest
  (coven/ash-callers/rune-fire/boiler-cult/hedge-wizards) plus the Renegade
  Magus epic -- ordinary warbands never field them, so a caster fight is
  one the player read on the board and chose. Their Power is the ammo:
  close fast or bleed at range -- a caster with no Power left is just a
  person in a robe with a knife. Narrate bolts as the school's fiction; the
  log already says who's casting what.
- **Quest levels are exact:** boards, rumors, `show`, and `take` all print
  the true level. MIND does not alter quest readouts.
- **Pay scales with level, and it is quoted per JOB**: a level-L quest of
  `enc` fights pays `44*(L+1)*MULT` XP and `18*L*MULT` gold, where MULT is
  1.0 / 1.6 / 2.2 for 1 / 2 / 3 encounters -- the trip, the giver, and the
  turn-in cost the same however many fights the job is, so pay rises
  SUB-linearly with length. 40% of the XP falls as the fights do, flat; the
  other 60% plus ALL of the gold lands at the turn-in. Punching up pays
  above your weight class by construction, easy work pays less. **The
  momentum streak is gone** -- there is no push-on multiplier to name any
  more, and nothing forces marathoning a job in one day. A two-place job's
  first place clears with a banner and no purse; the money is at the end. A
  level banks 3 skill points and grants NOTHING automatically: pools,
  training, proficiency, spell ranks, abilities, and warrior moves are all
  bought from the same points at the levelup menu.
- **Deliveries:** the board's DELIVERY rows are cross-land courier jobs --
  taken from their giver at the origin, paid by a named RECIPIENT at a
  settlement in another land (both faces are on the quest; narrate the
  hand-off like a turn-in). No rooms: `take`, then `travel` to the
  destination -- the leg that arrives is ALWAYS intercepted once (a
  road-table event, so it can be a sighting to slip or an ambush; it pays
  wild XP and cannot un-deliver). Arriving completes the quest on the spot:
  pay (20g + 25 XP per road day; CHA talks it up), recipient prompt,
  epilogue. Frame the cargo as the fiction demands -- the templates say
  what it is. A courier job carries a window like any job, with the round
  trip's road days added on top, and the hand-off is banded the same way --
  so a delivery is not a job to sit on.
- **The pact & karma in numbers:** dark XP = sin; heat = bad karma // (100
  x party level), capped 3; the law's posses arrive at party level + heat
  (cooldown 6d, chance 0.6, at arrivals and nights). Assignments: pinned to
  the PC's ODD LEVELS (1, 3, 5 ... 19 -- ten a career), dealt off a
  shuffled deck of the occult ten, served at the next settlement, leveled
  party +0..+1; serial, and crossed pins never stack (the highest is
  served, once). Grace ~10 days to TAKE it; taking stamps a visible window
  (6-8 days + road days) and stops enforcement. Past either clock: PAST DUE
  -- one warning scene (no fight), then ONE collections visit at party
  level +0..+2 (cooldown 4d, chance 0.6; breaks when beaten, neutral XP --
  demon-slaying is neither crime nor penance), and then the job is WRITTEN
  OFF however that visit ended. Hell work is never LOST off the clock: late
  pays x0.6 then x0, but only done, written off, or bribed ends it. `bribe`
  = 30g x level for 10 quiet days and a fresh Past Due clock. Deeds: PC
  2d6+stat vs DC (usually 10-11); a botch adds +15 sin and starts the
  fight. `settle` takes a twist's terms at x0.5 of the site lump. Losing to
  any posse is the special mercy (left for dead / the lesson) when the PC
  has not spent this level's one reprieve. A second same-level defeat is
  GAME OVER. Ordinary defeats follow foe ferocity: TAKE SPOILS takes purse
  and quality weapons, BREAKS WHEN BEATEN maims one member, and RELENTLESS
  gives no mercy.
- **Crime in numbers:** the MARK's level fixes both the take and the
  protection -- commoner 1-2 / tradesman 2-4 anywhere, merchant 4-7 town+,
  guild master or noble 8-12 town or capital, magnate 12-16 and the royal
  vault 16-20 in a capital; the wilds hold the bands that travel. The lump
  = 50 x mark level x the category's multiplier (half an at-level quest),
  coin = 20 x mark level x the same, goods fenced at x0.5; petty is flat
  (10-15 sin, 1-5g) and never scales. Deed DCs sit 9-11; a botch adds +15
  sin and starts the fight, and winning it still pays. A category repeated
  inside 10 days pays x1 / x1 / x0.5 / x0.25 of its SIN and XP (gold never
  depreciates), and a first-ever category pays x1.5. A single sin gain at
  or above the heat step floors heat at 1 for 6 days, penance or no. Hell
  suggests one category on the first completed assignment and one more per
  200 lifetime sin -- suggestions only; nothing is ever locked.
- **The world layer in numbers:** every land rolls 2d6 at worldgen -- 2-4
  CRISIS (~17%), 5-9 NORMAL (~67%), 10-12 PROSPEROUS (~17%). A land in
  crisis is living through a card most days and fires roughly two a season;
  a quiet land turns up about one in fifty days. One card stands over a
  land at a time, usually 12-25 days. States are words with day stamps,
  exclusive where the fiction demands it (a land holds ONE deposit stage,
  one standing of its foreigners), and a land's trouble reaches the lands
  it feeds as a derived state for exactly as long as it lasts. Nothing
  ticks in the background: the world's day is rolled where the calendar
  advances, so a land is always where its own dice put it, visited or not.
- **The weather in numbers:** one sky a land a day, off the climate of
  the Tile underfoot and the season (a land the party is not in reads its
  capital's) -- roughly a third of days are wet or freezing in the north
  and the taiga, a fifth in the south. A storm holds 1-3 days; a wilds night under one finds
  a cabin a bit under half the time. The exposure check is 2d6 + STR vs the
  sky (a rainy night gets through ~6% of the time, a stormy one ~33%); a
  cold costs 2 HP off the ceiling and pneumonia 5, and the nightly shake is
  2d6 + STR vs 13 (+2 for pneumonia, -2 under a roof) -- about 3 nights for
  a cold in the wilds, 2 in a bed. A storm in a fight costs -2 on every
  shot and a 2d6+DEX save on every step. Over a 120-day campaign a land
  sees about one storm a fortnight, a drought once in a few campaigns, and
  the fog's bones once in three.
- **The economy floor in numbers:** the band moves a settlement's board by
  -1/0/+1 posting and its pay by x0.85/x1.00/x1.15, and a card can move
  both again (a local crisis may remove more postings or reprice the work).
  A card's own job pays a
  10-35% premium over the going rate and never pays in steel. On the shelf,
  six terms multiply -- goods, steel, lodging, healer, toll, ferry --
  clamped to x0.5-x4.0; across a 60-day sweep some price is moved on about
  two land-days in three, a card is posting work on about one in five, and
  somebody the world put there is on the roads on about one in ten. The
  road's own charges are small (a toll is ~12g doubled, a ferry ~12g): the
  fords cost a DAY, and days cost the party more than gold does.
- **Politics in numbers:** every land rolls one constitution off a
  default-heavy die (the stereotype holds about three worlds in five) and
  ONE standing tension, two if it opened in CRISIS -- and only cards whose
  tension holds are in its deck at all, which is why two playthroughs of
  the same land are not the same land. A crown draws THREE trait words off
  a pool of 357 (a lesser named authority two off 355), so a rolled king is
  three vivid facts and silence everywhere else; the words are measured off
  443 historical rulers, and rare ones are rare rather than absent. At most
  three afflictions on one person. The succession is secure, disputed or
  heirless, and it reads the crown's own words -- a chaste or sickly king
  trends heirless. Most political cards move the board the same way an
  economic one does.
