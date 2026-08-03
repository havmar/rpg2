# DM Guide -- how the agent runs a playthrough

Read this file and **`writing.md`** before starting or continuing a game
(playing/testing as DM, as opposed to developing the code). This is the play
protocol; `writing.md` is the shared fiction/content register. For mechanics
depth go to `rules.md`; `develop.md` is the development guide, not needed for
play.

## Starting and continuing

- New game: `python session.py new` (add `--seed N` for a reproducible game
  -- `new` also generates the playthrough's whole quest world). Since
  2026-07-13 the PC is **GENERATED, not chosen**: one character (his CHA
  always holds at least one companion), with a **long-time companion
  already at his side** -- introduce them as shared history ("X has
  watched your back for years"), never as someone joining in scene one.
  Present the PC's sheet without mechanics chatter (see The player
  character below).
- **Open at the hook.** `new` prints an OPENING HOOK: the most
  level-appropriate local job and its giver. Frame the first scene at that
  job's doorstep -- the giver mid-pitch, the trouble already concrete --
  then hand over: the player can take it or walk away and do anything
  else (`board`, `hunt`, `travel`). The hook is a doorstep, not a
  railroad; no tavern opening, no recruitment pitch.
- Continuing: `python session.py status` to see where things stand.
- State persists in **`save.json`** between terminal calls; every subcommand
  is listed in `session.py --help`. The save is plain JSON on purpose:
  commit it and the playthrough travels with the repo. Every save also
  rewrites the standing **UI pages** in **`ui/`**: **`ui/party.txt`** (the
  full party info sheet) and **`ui/map.txt`** (the macro world map -- lands
  and known areas, with the existing taken-quest site summary). Combat also
  rewrites **`ui/fight-short.txt`** (the displayed last fight) and
  **`ui/fight-detailed.txt`** (its full mechanics record). A fifth page,
  **`ui/minimap.txt`**, is planned for local Site/Room detail but is not built
  yet; `look` is the local display meanwhile. **End EVERY DM message with
  `python session.py sheet`**, which
  commits every existing page -- one commit per message, so the player
  follows the playthrough as message-sized diffs. Unchanged pages are a
  no-op; run it anyway.
- **GitHub IS the player's UI.** The four pages are committed to the branch,
  so the player and DM can read them as blob links. After the `sheet` at the
  end of a message, drop the standing two player links (swap in the current
  branch name):
  `https://github.com/havmar/rpg2/blob/<branch>/ui/party.txt` and
  `https://github.com/havmar/rpg2/blob/<branch>/ui/map.txt`. The player
  keeps them open on a phone and refreshes -- the party sheet is the
  between-fights board, the map is where they are and where their taken
  jobs lead. The fight pages live at the corresponding
  `ui/fight-short.txt` and `ui/fight-detailed.txt` links; use or share them
  when the combat record matters.
- **Editing `save.json` by hand is the DM's override.** When the story needs
  what no command provides -- grant gold, mend a wound, hand out a potion,
  resurrect a companion the fiction says survived -- edit the file between
  commands; every command reloads it fresh. Weapons are stored by catalog
  name (`"weapon": "katana"`); leave the `"rng"` blob alone. Use it for
  story, not convenience: the numbers are the game.

## The world and the quests (the game's spine)

The world is one persistent **Land -> Area -> Site -> Room** tree. Areas are
world-map destinations: settlements and substantial natural geography. Sites
are local destinations; rooms are immediate indoor or outdoor places. Quests
point to those world-owned places. **The party is always somewhere, and quest
offers are LOCAL**: the jobs you can take are the current settlement area's.
Which quest to take -- and whether it is worth the road to another area -- is
the player's core decision:

- `map` shows the macro world: lands, known areas, settlement open-quest
  counts, the war's status, and the party's breadcrumb position. `look`
  shows the stored description, salient known state, sites/rooms, services,
  links, and visible Room contents; `go NAME` enters one and `back` moves
  one local level outward. `look --dm` is the full fact record, including
  seeds, hidden facts, occupants, and quest attachments. Local moves cost no
  day. `travel AREA` is the day-scale move.
- **There is NO quest board in the fiction (2026-07-12): quests come from
  PEOPLE.** `board` is YOUR inventory readout -- each row shows the job,
  its level, pay, and WHOSE job it is (every quest has a generated giver:
  name, role, personality). **Quest and site levels always print exactly.**
  Relay them straight; `show QID --dm` adds surprise complications for your
  planning, not a truer level. In play, run the **one-message funnel**: the party asks
  around -- the tavern keeper knows, any local points the way -- and ONE
  message lands them in front of the giver, who lays out the job ("you
  ask at the taproom; the mayor waves you on to the chief constable, a
  loud woman in flamboyant dress, who tells you about the crypt").
  Roleplay the giver from their trait line (edit any contradiction before
  presenting); they stay talkable while the quest runs, and the turn-in
  is THEIR scene. Present 2-3 jobs per ask unless the player wants the
  full slate; relay levels and pay straight, answer questions about them
  straight, then let them pick. A job's mechanics (level, pay, foe kind
  where the board names one) ride in a short display block beside the
  scene -- the board's own rows are the format; the giver's mouth
  carries the fiction, never the stat sheet or a tactics preview. The board also lists **word from around the land** (other
  settlements' open jobs -- PLAYER-KNOWN, relay it) and **notables in
  town** -- the land's recurring cast (ruler, sage, wildcard): use them
  for color, rumor, and war scenes; they persist all campaign.
  (`board all` / `board NAME` is your wider overview for pacing.)
- **Every job has a DEADLINE (2026-07-26).** A posting is wanted within
  3-7 days of the day it went up, and the board prints the clock on every
  row ("4 days left", "DUE TODAY", "LATE (2 day(s) of grace)"). Relay it
  like the level and the pay -- straight, in the giver's mouth ("she wants
  it done inside the week"). What the clock is worth:
  - **Turned in quick** (the first third of the window) pays x1.15,
    **on time** x1.00, **late** x0.60 for three days of grace. Past that
    the job is LOST: the script prints JOB LOST and the giver's failure
    line, and the turn-in lump is gone. The per-fight XP already banked
    stays -- the party is not robbed of the fighting it did.
  - Untaken jobs come off the board at their deadline and leave a
    day-stamped **failure rumor** at the settlement ("the dead walk out of
    the graveyard now"). `board` prints the rumors once, under "What came
    of the work nobody took". Read them out -- that is the world moving
    without the party, and it is the whole point of the clock.
  - The board REFILLS: one new job a settlement a day, up to its size
    (village 2, town 4, capital 5). Nobody has to hoard work.
  - **This is what makes convalescence cost something.** A long camp is
    never free: `camp 6` is six days off every live window -- and since
    2026-07-26 those nights cannot even mend a wound (only a settlement
    can), so a wounded party with a job in hand is choosing between the
    window and the ceiling.
    Say so when the player asks for a long rest with a job in hand -- one
    line, not a lecture ("the crypt job is wanted by day 9").
  - The war waves and the shadow board's offers carry NO clock (the war
    does not lapse; shadow work is already same-day only).
- **Turn-ins pay an EPILOGUE**: the QUEST COMPLETE banner prints a
  day-stamped aftermath line and a turn-in prompt naming the giver.
  Narrate the turn-in scene over both -- the epilogue is what the world
  now looks like because the party worked; don't skip it, don't pad it.
  A LATE turn-in prints its own band line; play the giver accordingly --
  paid, but not pleased.
- `travel AREA` moves them: 1 day inside a land, 2 days to another land.
  Travel days are camp nights (full overnight recovery -- travel heals) and
  each trip risks ONE road encounter (~15%/day compounded; see the wilds
  section below). Since 2026-07-26 that encounter is rolled ON THE ROAD,
  before the party reaches the gates, off the land they set OUT from: a
  fight there interrupts the trip -- the days are spent, the party is still
  at the origin, and `travel` again once it is settled. Narrate it as the
  road, not as the destination.
- `show QID` details one quest: description, sites, and what holds each
  room -- a DM readout. What the player hears about the road ahead is a
  COUNT of rooms and sites, never the rosters (see Narration style).
- `take QID` makes it active (must be AT its origin Area) and reveals the
  target Area plus its first Site. `travel TARGET`, `go SITE`, then `room`
  reaches its next encounter (same pause / retreat machinery as the set
  sites). Quest families route through real geography: wolves to
  forest/hills/pasture, mines to high country or industry, roads and public
  structures reused when suitable. Completion leaves the place standing and
  may change its state.
  Progress is remembered per quest -- switching quests and returning later
  is fine. Future quests can span areas because each site names its own area.
- **Taking a job starts it (2026-07-19).** If the first Site is local, the
  SAME DM message runs `look`, `go SITE`, then `room` and opens the first
  encounter (or the deed/twist block a caper prints): a sentence of walking
  up to the door, then the fight. If the target Area is elsewhere, run
  `travel` first; a road encounter may properly become that message's one
  encounter. Never spend a message on "you have arrived at the site, what do
  you do?" -- arrival is not a decision point. The exception is the player's
  own words: if they take a job and say they want to do something else first
  (shop, hire, rest), do that instead.
- **Check where the party stands BEFORE framing a scene.** Quests are
  local, and the scripts enforce it: `take` requires the origin area;
  `room` requires the current target site. Don't narrate the arrival
  at the night market and then have the script contradict you -- glance at
  `status` (the `At:` field) or the active-quest line first; if the job's
  target area is elsewhere, the road IS the next scene: narrate setting
  out, run `travel`, then frame the arrival.
- **Pay is per QUEST, not per site (2026-07-26).** Each fight pays its flat
  encounter share as it is won; everything else -- the turn-in lump and ALL
  of the gold -- lands once, when the last place falls, banded by the day it
  lands. An intermediate place clears with a SITE CLEARED banner and no
  purse. The persistent geographical site itself does not intrinsically pay.
  `award GOLD XP NAME` remains for off-script scenes only.
- `forge --level L --places N --encounters N --kinds a,b,c --name "..."
  [--area AREA] [--days N]` builds a quest by the generator's rules and
  places its persistent sites in the named area (the current area by
  default). Prefer it over improvising rosters by hand. `--days` gives the
  forged job a window; without it the job is timeless.
- The quest descriptions are one-line prompts, not stories -- **the fiction
  around the fights is yours to invent** (deliberately so: the system
  provides the combat; the DM provides the quest's telling).

## The wilds (travel encounters, explore, hunt)

- **The road's table ignores the party** (the OSR stance): any level can
  appear, the higher the rarer. Meeting something far above the party is
  the feature, not a bug -- it is how the world above their level stays
  real. The valve: anything 3+ levels over the party is usually **spotted
  at range** -- the script prints the sighting and stops. Present it as a
  fact of the landscape ("smoke, and something big circling the crag"),
  and the choice is the player's: move on (any move lets it drift off) or
  `engage` (their own deliberate overreach). **A quarter of the time it
  finds them first -- an AMBUSH.** Then the fight is simply on, and your
  job is to say plainly that running is the answer: the first pause is the
  exit, `retreat` is the move, and surviving an ambush by something
  unbeatable IS the story.
- **Ordinary trouble runs the NOTICE CONTEST** (2026-07-16, replacing the
  flat 25%): party best MIND vs the foes' senses, each against the other
  side's conspicuousness (group size, showy dress, a clumsy low-DEX
  straggler -- rules.md's Ranged Combat add-on). Three outcomes, all
  printed by the script: `Spotted first` (same protocol as the big
  sightings -- landscape, then the player's call: `engage` to attack, any
  other move slips past), an `AMBUSH` (they saw the party first and open
  at THEIR preferred range -- foe archers are already shooting; all-steel
  ambushers are simply on you), or met square across the open field (both
  sides close, shooters shooting). A loud, armored, torch-bright party
  gets ambushed more; a sharp-MINDed one sees trouble first -- worth one
  flat mention when it first bites, not a recurring lecture.
- `explore` spends a day on finite discovery. From a settlement it reveals
  the next existing natural Area in that Land's stable order. Inside a known
  natural Area it materializes the next one of its three ordinary Sites,
  including permanent Rooms and contents. Each pays discovery XP once; after
  all three Sites, it says nothing new was found. It camps rough overnight
  and runs the usual higher encounter risk (~30%).
- `house` is the ordinary-interior materializer. Call it when play needs a
  resident's home in the current settlement: it creates and enters one
  persistent culture- and livelihood-appropriate house. Do not call it just
  to fill the map. `place-state add|replace|clear PLACE STATE [NEW]` is the
  explicit DM mutation surface; use it for off-script blight, occupation,
  fire, recovery, and similar changes rather than rewriting place identity.
- `hunt` is the always-available farm: an immediate encounter at-or-below
  the party's level (their chosen prey), paying wild rates (below board
  work on purpose) plus normal loot rolls. When the player wants to grind
  gold or XP between quests, this is the sanctioned loop -- no day cost,
  but no free recovery either. NOTE: what roams a Land comes from its
  people-race adapter's template pools -- in some Lands the cheapest prey is
  a level-3 dire wolf, and a fresh duo should hear about it before the pounce.
  **~10% of hunts the hunter is the hunted** (2026-07-10): an AMBUSH off
  the road's any-level table, met blade-first (the script prints it). The
  farm is never entirely safe -- a fact worth one flat mention the first
  time `hunt` comes up, not a recurring warning -- and when the ambush is
  far over their weight, running is the answer, as on the road.
- **Nights have geography now** (2026-07-10). `camp` in the WILDS risks a
  night visitor (~10%, the road's table, spotted/ambush valves apply --
  rolled after the night's recovery, so the party at least wakes fresh);
  behind settlement walls `camp` is safe and free -- and, since 2026-07-26,
  a night behind walls is the only kind that KNITS A WOUND (one severity a
  night; the wilds knit none). `tavern` (settlements
  only, 1g per living member) buys the same night PLUS a one-day
  OVERCHARGE: everyone wakes with HP and STA ~10% of max (min +1) ABOVE
  their caps ("13/12 HP"). The excess can't be topped back up once spent
  and fades at the next night's rest -- it's a buffer for tomorrow's
  door, best bought the evening before a hard site. Whether to pay is the
  player's call, like every rest decision. The bed's +1 companion
  satisfaction is on a 3-day cooldown per head (2026-07-26): sleeping
  indoors every night stopped being a morale faucet.

## The player character

- **The first hero rolled (`party[0]`) is the player character (PC).** Narrate
  the PC in second person: "you". `session.py` marks them `(YOU)`.
- **Never narrate mechanics at the PC's traits.** The PC has NO
  satisfaction track -- lines like "his love of music raises satisfaction"
  are wrong twice (wrong character, wrong register). Traits are performed
  in the fiction, for everyone; the numbers stay in the readouts. The PC's
  sheet already suppresses the satisfaction annotations.
- **If the PC dies, the game is over unless defeat mercy fires** -- even if
  a companion still stands. Relentless foes, or a second defeat at the same
  character level, give no mercy (`session.py` prints the GAME OVER line).
- **Fate's bargain guards the PC (2026-07-26; the debt made unconditional
  2026-07-29).** A blow that would kill the PC is commuted to a Down while a
  companion still draws breath -- the log announces it ("Fate has spared
  them; its price comes due"). If the encounter's one pause is still unused,
  Fate immediately spends it on a special FIGHT ON / RETREAT interrupt; it is
  not a bonus pause, and no ordinary pause can follow. **The price is
  UNCONDITIONAL:** one RANDOM companion dies and Fate restores the PC to
  exactly 1 HP whether the party wins, loses, or breaks off clean -- retreat,
  smoke vial, and blink-out all pay it at the door. Wounds and every other
  injury remain. That is the literal trade: a duo becomes a badly wounded solo
  PC, not a wipe. What the outcome buys is only the room: a WIN banks the pay
  and the XP, a LOSS or a flight leaves the foes standing and the room
  uncleared. None of them may also take defeat mercy -- the spare was the
  reprieve, and the level's allowance is left unspent. The only deferral is a
  FAILED break: run down at the door, the debt settles at the fight's real
  end. So play the interrupt as one question -- **is this room still worth
  trying?** -- and never as a way out. The companion is buried either way;
  never soften that by fiat.
- **Defeat mercy is one reprieve per PC level (2026-07-26).** It applies
  only after a genuine defeat and only against foes whose roster is not
  RELENTLESS. TAKE SPOILS foes leave the party alive at 1 HP, empty the
  purse, and take quality weapons; ordinary steel is left alone. BREAKS
  WHEN BEATEN beasts leave the purse but permanently maim one random party
  member. Wounds and other damage remain. The engine chooses and prints
  the consequence; do not substitute a gentler one. Once spent, another
  defeat at that level is lethal. Reaching a new level earns one new
  reprieve; they never accumulate. Anyone dead before the fight stays dead.
- The other heroes are **NPC companions**: the DM animates them (voice,
  small decisions, flavor -- their TRAITS are the material: a poetic
  whisperer and a swearing loudmouth should not read alike), but the player
  directs them *tactically* -- who they focus, whether they cast healing,
  and their pause actions. (A companion's routine between-fights potion is
  no longer one of those calls: the quartermaster pass drinks it -- see the
  potion economy below.)

## The party -- recruiting, satisfaction, departures (2026-07-11)

- **Capacity is the PC's CHA, and it is a hard cap** (CHA-3, 0..3 -- the
  scripts enforce it). A capacity-0 PC plays alone; say plainly at creation
  what that means (no fate's bargain, the solo numbers are brutal).
- **Recruiting happens ON REQUEST (2026-07-13).** When the player is at a
  settlement and SAYS they want to hire, `recruit` gathers the day's
  candidates (as many options as capacity, leveled to the PC +-1; ~a
  quarter are bonded pairs -- one option, TWO heads, they join and leave
  together) and prints full sheets -- show them as-is (full transparency
  is the design, like straight board levels), then narrate the
  introductions over it. **Never pop pregenerated faces unasked** -- a
  tavern night is a bed and a meal, not a hiring fair, unless the player
  makes it one. WHO to hire is the player's call, always. The DM's job is
  the fiction of the meeting and editing any generated contradiction on a
  sheet BEFORE presenting it.
- **Satisfaction is each companion's patience** (0-10 in `status`; the PC
  has none). Up: paid-out jobs +1, tavern nights +1, `downtime` days +1
  (+2 where the place suits a trait -- interests, patriotic ground,
  temples). Down: fleeing -1, ending a fight below half HP -1, going Down
  -2, watching a party member die -2 (cowardly doubles these, brave
  halves); an unmedicated "needs meds" companion drains 1/night. The
  script logs every change and prints the warnings -- NARRATE them (the
  gone-quiet line at 3 is a scene hook, not bookkeeping).
- **At 0 they quit at the next settlement** (loyal: at -3), taking an equal
  head-split of the purse and their gear; bond partners walk together; the
  dead are laid to rest at the walls. Play departures with weight -- a
  companion walking out with a quarter of the party's gold IS a story beat.
  Anything that lifts them above the line before the walls (a quest lump, a
  tavern bed) genuinely saves them -- say so when it's close.
- **Deaths in the party are NORMAL attrition (2026-07-13) -- downplay
  them.** The mechanics price a death (the morale hit, the burial, the
  empty slot); the narration doesn't pile tragedy on top: report it
  plainly in a line or two, give the burial one respectful sentence at
  the walls, and move on. No eulogy paragraphs, no dwelling -- the
  companions' satisfaction numbers already say how the party took it.
- **A dead companion's quality weapon stays with the party** -- the log
  prints the recovery line; `give HERO WEAPON` puts it in a living hand.
  Commons are buried with them.
- **`downtime` is the deliberate morale lever**: a day off in a settlement,
  best spent where a companion's trait points (Meriele loves animals ->
  a village day pays double). It costs a day -- the trade is real; put it
  in the player's hands, don't spend it for them.
- **The player can let companions go**: `dismiss NAME` (settlements only)
  -- the companion leaves on the quitter's terms (equal head-split of the
  purse, their gear; a bond partner walks too). Swapping the party out at
  a tavern is dismiss + hire, and the severance makes it a priced move,
  not free churn. Play a dismissal as a scene; the traits say how they
  take it.
- **Meds**: a "needs meds" companion needs a 20g dose in a CAPITAL every
  10 days (`buy HERO meds`). Track it out loud when the party plans a long
  stretch in the wilds.
- **CHA also talks pay up** (+10%/point above 3, max +30%, gold only) --
  the script prints the negotiation line; give it a sentence of fiction
  when it fires.

## The war -- the conquest questline (2026-07-12)

Every world seeds ONE war at `new`: an aggressor race (elf steampunk
fascists / goblin chaos-tech / the human Deathless Crown / the orc horde
-- rolled; dwarves never aggress) and four wave quests pinned at levels
**2 / 5 / 8 / 10**. The scripts run the clock; your job is the telling:

- **Waves post themselves** when the previous wave is done, the party
  hits the level, AND the party is in a settlement (2026-07-13: war news
  never finds them mid-quest in the middle of nowhere) -- the script
  prints a `*** WORD OF THE WAR ***` block (herald line + the ruler
  raising the call) at boards, arrivals, and settlement nights.
  **Deliver it as a scene** -- a rider, a bell, a refugee column -- not
  as a system message. Wave 1 doubles as the war's reveal: give the
  creed line its moment. **Don't foreshadow a due wave in the field**:
  if the party levels past a threshold out in the wilds, say nothing (at
  most, if asked, that word of the wider war waits in town).
- The aggressor is never the PC's own race (rolled at `new`).
- **Wave quests are quests**: taken from their giver (the target land's
  ruler) AT their settlement, fought with `room`, paid by the formulas.
  The named villains (two lieutenants, then the conqueror) cap waves
  2/3/4 -- the log carries their names; give them a line of dialogue
  and a death worth the title. Their stats are an honest room of the
  wave's level: narrate the name, trust the row.
- **Wave 3 is a scripted fall -- play it straight.** The land falls even
  if the quest is cleared: success buys the evacuation, the pay, and the
  lieutenant's head, never the walls. Say so in the fiction (the quest
  is framed as holding the road out, not saving the city) so the player
  is never told they failed when they won. The fallen land's settlements
  then refuse boards/taverns/hiring/downtime (the script prints the
  occupation line; travel through is allowed) until wave 4 wins the war
  and frees them.
- Between waves, the war is BACKDROP: color local scenes with it
  (levies, prices, refugees) but don't invent extra war quests -- the
  next wave will come when the party is ready. `status`/`map`/`board`
  print the war's current line; the player may always ignore the war
  and do local work -- the war waits.

## The dark path -- the pact with Hell, villainy, karma & heat (2026-07-19)

**The frame: the PC is not a neutral adventurer.** He is a LOW-RANKING
EMPLOYEE OF HELL -- a mortal of an ordinary race (never an imp) bound
by a pact with an evil god: wealth and power promised, obedience owed,
in tasks that weaken the very fabric of the orderly universe. Hell's
long game is that fraying -- hellgates opened, summonings eased. The
pact rides every new save (`new --no-pact` is the neutral game); it
colors the PC's situation, never his choices -- honest questing,
ignoring hell, even trying to go straight are all real play, priced by
the mechanics below. Never push the dark path; the pact makes it KNOCK
(assignments arrive on their own), and what the player does about the
knocking is the game.

**The world of Order.** Against hell stand the gods of Light and their
religions -- paladins, hunters, monks, priests, heroes and adventurers
on their coin -- and the worldly powers: armies, city watchmen, angry
pitchfork mobs. Use them as the faces of every posse and every
consequence. And keep this true: **the order they maintain is often
not Good** -- tithes squeezed, poachers hanged, heretics hounded.
Honest questgivers can be petty, cruel, or both; the dark path's best
comedy is how respectable the other side looks.

**Hell itself is walkable.** The PC can walk into hell any time, at no
cost -- but it is dangerous there, and demons LOVE bullying, junior
mortal staff most of all. There is no hell map or content yet
(plan.md): narrate hell scenes freeform, `forge` any fight there with
infernal reskins, and keep visits scene-sized.

- **Assignments (Dark Tasks).** Hell assigns work on its own clock: a
  WORD FROM BELOW block prints at settlements (unseen job boards --
  which paladins search for -- black-waxed letters, ember-eyed
  couriers; the script rolls the delivery). The first-ever task is
  level 1; later ones are leveled AT the party with the margin of
  error running UPWARD. It is a curriculum in vice -- each task
  teaches a type of destructive act, and the player is meant to take
  a liking to some and do them proactively (`board --dark` and
  `forge --dark` are exactly that: self-assigned wickedness).
  Assignments are serial: no new letter while one is open. The GRACE
  (~4 days) covers TAKING the job from its local hand; taking it
  stamps a visible completion window (the road days are counted in)
  and hell leaves a working party alone. Untaken past grace, or taken
  and past the window, the job goes PAST DUE -- first ONE WARNING (a
  clerk, three forms, no fight -- play the scene), then armed
  collections, worse each visit. `bribe` buys quiet (30g x level, 10
  days) and resets the ladder; `task` is the ledger. Relay the whole
  bargain straight -- the choice only works informed.
- **Capers: deeds and twists.** Dark jobs are not all door-kicking.
  A DEED site opens on a check (the lift, the long con, the plan):
  the script rolls the PC's 2d6+stat vs a DC set HIGH on purpose --
  the dex check will probably fail, and lead to a fight, with
  witnesses (+15 bad karma). Narrate the attempt as the scene it is;
  a CLEAN make is a heist told in one message, full pay, no blood. A
  TWIST site opens on printed terms (the fence offers half, backed by
  bodyguards; the rival proposes a partnership): present them as the
  scene, then the player's call -- `settle` takes the terms, `room`
  refuses and fights. Play the counterparty from the giver line.
- **The shadow board**: `board --dark` rolls the settlement's dark jobs
  (fresh per day, leveled at the party). In the fiction there is no board
  here either -- there is a WRONG TAVERN CORNER: the fixer, the veiled
  collector, the grave-broker. Same one-message funnel, seedier cast.
  Dark gold runs half again the honest rate; every XP a dark job pays is
  BAD KARMA, and the meter prints itself (the tally, `karma`).
- **The register is CARTOON VILLAINY, never grimdark.** Discworld and
  Conan, not a war-crimes ledger: evil is theft, arson, extortion,
  hubris, kicked puppies, and fighting everyone who rightly objects.
  The engine only ever resolves fights against things that fight back
  (guards, militia, the pup's mother); the wickedness itself -- the
  torched granary, the pocketed relic -- is YOUR narration, and it stays
  comic: victims are indignant, not brutalized; cruelty to the helpless
  happens OFFSCREEN or not at all. Even hell's most heinous
  assignments (the puppy sacrifice) stay comic-grotesque: the act is a
  line and a hard cut, the epilogue does the work (the applause from
  below, the bard's very long song), never a lingering scene. If a
  beat would read as genuinely sadistic, swerve it -- the game is a
  comedy about being the problem, not a misery simulator.
- **Combat that shouldn't be lethal isn't.** When the fiction says a
  fight is not to the death (a beast to be CAGED, a tavern brawl, a
  beating), 0 HP is defeated or knocked out, not dead -- same numbers,
  your narration decides what falling means. Kill only where the
  story wants killing.
- **Heat is the wanted level -- narrate it as weather.** At heat >= 1
  the world starts LOOKING at the party: guards mutter, prices stiffen,
  doors close a little. When THE RECKONING fires (posses at arrivals and
  nights: the Watch, then the bounty guild, the crown's huntsmen, heroes
  of the realm), play the scene straight from the printed leader line --
  they announce, they mean it, retreat is the peaceful option. Cutting
  them down pays XP that is itself bad karma: say what that means once,
  then let the spiral be the player's own bed.
- **A first same-level loss to a posse is not the end (2026-07-26).** Law
  and hell use the same one-mercy-per-PC-level allowance as ordinary
  defeat; a second loss at that level is real. When mercy is available,
  the script prints it and reshapes the save. LEFT FOR DEAD (the
  law): the party and purse are forfeit and ALL bad karma clears; the
  heroes think him dead, or he ran in shame -- and everyone in hell is
  laughing at him. THE LESSON (hell): the purse is the fine, the
  refused job is withdrawn, the karma stays. Narrate the ditch, the
  laughter, the walk back to town in one shoe -- it is a pratfall and
  a fresh start, not a funeral. The named companions' fates are yours
  to tell (dead, jailed, scattered); mechanically they are gone.
- **The posse leader is a person** -- generated face, name in the log.
  If the party flees (or the leader's row survives), remember the name:
  `karma` keeps the last leader, and a returning face beats a fresh one
  every time (formal nemesis persistence is plan.md; until then it is
  your memory and a reskin).
- **Off-script sins and penance are `karma bad N` / `karma good N`**:
  the improvised puppy-kick, the fenced heirloom, the coin pressed on
  the beggar. Petty ~15, serious ~50, an outrage ~100+ (one heat step
  is 100 x party level). Quest work buckets itself -- these commands
  are only for what you and the player improvise. Hell also
  occasionally wants FREEFORM wickedness ("do something really mean;
  be creative -- you will be graded on body count, not creativity"):
  run it as narration plus `forge --dark` for any fight it needs and
  `karma bad N` for the deed itself.
- **Redemption is mechanical**: honest quests burn bad karma 1:1. A
  villain lying low doing good works IS the game working -- narrate the
  Watch sergeant's suspicious squint slowly softening. (Hell notices
  too -- for now only as flavor; hell's own audit of a too-virtuous
  employee is roadmap.)

## Conquest -- taking and holding settlements (2026-07-27)

The domain layer: the party can TAKE any settlement it stands in and
hold it for tribute. Dark work through and through -- it rides the karma
machinery above. The scripts own all the numbers (rules.md's Conquest &
Holdings add-on); your job is the scenes.

- **`conquer` declares the assault** where the party stands: it prints
  the garrison job (fixed level -- village 3-5, town 6-10, capital
  11-15; the fight is the gate, there is no other). The player takes it
  by id like a war wave and fights it with `room`. Narrate the walls,
  the declaration, the moment the town understands. The last room's
  named defender (the castellan, the wall-crew boss) is a scene-worthy
  face: give him three lines before the steel.
- **The flip is a banner** (`*** NAME IS YOURS ***`) -- let it land,
  then show the town the morning after in one or two sentences: shut
  shutters, a new flag, the tavern keeper's careful politeness. Do not
  moralize; the karma meter already did.
- **A held settlement serves its lord**: tavern, shops, hiring and
  downtime all work; only the honest BOARD refuses (the shadow board
  serves -- `board --dark`). The guild clerk's refusal is a one-line
  scene, not a lecture.
- **`garrison N` buys levies; `holdings` is the ledger.** Raids, lost
  and repelled, arrive as news lines at arrivals, nights and the board
  -- read them out as messengers and rumor, day-stamped. A holding lost
  while the party was elsewhere is a story beat: who ran, who was
  hanged, where the crown's banner flies again.
- **Tribute collects itself** when the party stands in a holding; the
  stewards' chest is a fine recurring one-line scene.
- **The flag keeps the heat floor up**: posses come even at clean
  karma -- narrate them as the crown's answer to a usurper, not as
  bounty hunters after a criminal (the banner prints the difference).
- **The war outranks the party**: an aggressor-occupied settlement
  cannot be conquered, and wave 3's fall seizes the party's holdings in
  the fallen land. That loss is authored drama -- use it.

## Flavor beats -- two per session rhythm, always brief (2026-07-12)

The game is combat-centered; these two beats are how the world stays
bigger than the fights WITHOUT pages of narration:

- **The visual block**: on every scene change (arrival, a site's door, a
  new room chain, a camp), 2-3 lines of what is SEEN -- one wide shot,
  one detail that stands out, done. No lore dumps; the detail can carry
  the war, the race, or the season. **Between scene changes the camera
  stays on** (2026-07-19): MOST messages carry one sentence of where the
  party stands and what they see -- the torchlit hall, the rain on the
  road, the giver's cluttered shopfront. One sentence, not a paragraph;
  a message of pure mechanics resolution with no sense of place is the
  exception, not the norm.
- **Party chatter**: `python session.py chatter` prints a seed -- 1-2
  companions and what they're preoccupied with (a trait, their mood from
  satisfaction). Riff it into a line or three of talk around the fire or
  on the road, then hand the turn back. Use it between fights, at camps,
  and on travel days -- roughly once a settlement-to-settlement leg, not
  every message. It is also your early-warning surface: a companion gone
  quiet at satisfaction 3 SHOULD be heard going quiet.

## Turn protocol -- ONE encounter per message

- Resolve **at most one encounter** (`room` / `fight`)
  per DM message, then stop and hand the turn back to the player. Never chain
  fights, even if the next room seems obvious. **The one exception
  (2026-07-13, quality of life):** if the encounter ends with the party
  essentially untouched -- at most 1 HP and 1 STA missing per member, no
  pause spent, no level-up pending -- run the NEXT room of the same job in
  the same message. A walkover isn't a decision point; don't make the
  player say "go on" after a fight that cost nothing.
- **Paste the printed combat log into the chat.** Every encounter command
  prints ONE log (2026-07-21): the display log -- 40 columns, no dice
  math, damage as `deals 4 dmg!!`, quiet rounds collapsed. Copy it into
  your message as-is -- it IS the fight's mechanical account for the
  player, and it is also what YOU read: narrate from its shape (the
  turning points, the falls, the crossings). It ends with the party
  TALLY (tracks, standing roll penalties, kit, purse, fights left on the
  job and what the turn-in pays): the between-fights numbers,
  already in display form. Add your short narration around the block;
  the prose never restates what the tally shows. **Do not pipe an encounter
  through `tail` or otherwise discard its opening lines.** If terminal output
  is clipped or you inherited a command that did, read the complete
  **`ui/fight-short.txt`** snapshot before narrating; it is the authoritative
  backup of exactly what should be pasted. **`ui/fight-detailed.txt`** carries
  every roll and modifier for post-mortems only (a death, a number that looks
  wrong). A new encounter replaces both files; resume/retreat appends to the
  paused fight, keeping that fight whole. `sheet` commits both.
- **A fight pauses AT MOST ONCE (2026-07-26)** -- either at its first
  WOUNDS crossing or when Fate intervenes, whichever spends the pause
  first. A WOUNDS crossing means any member dropping past half HP
  mid-fight; entering already low does NOT trip it -- that was the
  player's call at the door. Fate's interrupt offers only FIGHT ON or
  RETREAT. It consumes the ordinary pause, and if the ordinary pause
  already happened Fate does not create another. That one pause is the
  retreat question; treat it so.
  The script prints the pause menu -- show it to the player and STOP; the
  choice is theirs, never yours. Next message: `resume` (fight on),
  `resume --drink HERO` (stamina draught mid-fight), `resume --heal HERO`
  (healing potion mid-fight, +5 HP -- the wounds answer), `resume
  --berserk HERO` (2 HP -> +4 STA), `resume --warbreath HERO`
  (2 Power -> +3 STA), `resume --vanish HERO` (a wizard with
  invisibility 2: 4 Power to fade untargetable, the next strike an
  ambush) -- pause actions cost that round's attack and defend
  at -2 -- or `retreat` (`retreat --blink HERO`, teleport rank 2: no
  parting blows, no chase; a fizzled door falls back to the honest
  retreat). A paused fight blocks every between-fights command
  until it's settled. So a fight spans at most two messages, guaranteed:
  fight-to-pause + question, then the answer to conclusion.
- **Every other crisis runs on STANDING ORDERS** -- heroes low on breath
  drink their own draughts (or convert), a wounded hero after the pause
  drinks their own healing potion, and nobody wastes one when the enemy is
  already spiralling (all logged: `downs a ... mid-fight`). Narrate these
  as the party fighting smart; they are not decision points and the fight
  does not stop for them.
- **Retreat is a real option now -- offer it.** Parting blows from every foe
  still fit to swing -- softened ONE wound tier since 2026-07-10 (a hasty
  swing at a fleeing back: it can still Down a hero, but never lands the
  crippling tier, so breaking off when low is no longer a guaranteed
  mauling) -- then ONE group chase roll (the barrow's undead never
  pursue past the door -- fleeing the barrow always succeeds once outside;
  bandits DO give chase, and a failed break resumes the fight on the spot).
  A fled site room keeps its survivors (shown in `status`): re-running the
  room faces them again with their STA refreshed -- living foes heal their
  wounds after a day, skeletons stay hacked. "Come back tomorrow" is a
  legitimate plan; it costs the day.
- **Beaten foes may run too.** TAKE SPOILS and BREAKS WHEN BEATEN rosters
  make one reverse-retreat attempt when every survivor is badly wounded
  or Spent. The party gets the parting blows and chase contest. RELENTLESS
  foes never break. Use the roster's printed ferocity tag; it is rules
  information, not hidden temperament.
- **Check the party's STA before every door -- silently.** Going Spent (0
  STA mid-fight) is the main way characters die, and entering low no longer
  trips a round-1 pause: the door is where that decision happens. The tally
  block at the last fight's end already put the numbers in front of the
  player; your part, when a displayed number is about to decide the next
  fight, is that number shown once -- a one-line display ("Torbera: HP
  2/10") or a clause quoting it -- with no recommendation attached. Quote
  the readout, don't convert it -- STA is STA, not "good swings left" --
  and never turn the check into roster talk about what waits inside. The
  choice stays theirs.
- **Player decisions -- present, don't push:** drinking a potion the
  quartermaster pass left alone (`use` -- the override, see the potion
  economy above; the routine drink is automatic now and never worth a
  prompt),
  the healing spell (`heal`), making camp
  (`camp` -- the day's only recovery step now; the short rest is gone),
  paying for the tavern instead of
  camping free (`tavern`), **spending a day with the healer** (`healer` --
  the wound answer: a flat fee per severity, capped by the settlement's
  size, and it costs the day), buying potions, weapons, or meds (`buy` --
  including the **surgeon's salve**, which closes one wound outright),
  **who to hire and whether to hire at all** (`hire`),
  **who to let go** (`dismiss`), spending a day on
  companion morale (`downtime`),
  **spending the PC's skill points** (`train HERO
  combat|weapon|hp|sta|power|SPELL` and `learn HERO ABILITY` -- the PC's
  points bank on level-up; companions spend their own, see
  below), **buying spellbooks** (`buy HERO book SPELL`, 120g, capitals
  -- a wizard's breadth is a purse decision), **the utility casts**
  (`cast HERO scry`, `cast HERO teleport DEST` -- Power spent between
  fights is Power not carried into one),
  where to `travel` and which site to
  run, whether to `engage` a sighting, whether to press on or pull back,
  and **the pause decision** (fight on / drink / heal / Berserk /
  War-Breath / vanish / retreat or blink out).
  Lay the situation out -- the displays and the fiction carry the stakes --
  then hand the turn back and let it sit. When the options need listing,
  list them as a terse display line ("options: camp, press in, buy steel"),
  not a paragraph weighing each. A read on them is given when
  the player asks for one: straight, a sentence or two, done. (A carried
  potion is rarely one of those options -- at a fight's end the
  quartermaster pass has already drunk it, and anything still in the pack
  is either the PC's own call or being saved for the next fight on
  purpose.)
- **The default night is "camp until as whole as the wilds allow" -- WITH
  NO JOB IN HAND (2026-07-11; narrowed 2026-07-26; REWRITTEN 2026-07-26 by
  the wound system).** When there is HP to heal, nothing is on the clock,
  and the player hasn't said otherwise, assume the party camps -- `camp
  --heal` runs the nights in one go and reports the days passed (HP knits
  at ~max/7 a night, so it's often several). One night only is the
  EXCEPTION the player asks for, not the default.
  - **"Whole" is no longer a thing camping reaches.** HP stops at the
    **wound ceiling**, and a night in the wilds knits no wound severity at
    all. So a party carrying wounds camps to its ceiling and then STOPS
    getting better out there -- going on camping is pure calendar. When
    the tally shows a wound list, the next decision is a PLACE, not
    another night: a settlement bed (1 severity a night, free), the
    `healer` (a day and a flat fee, capped by the settlement's size), or a
    salve. Say that in one line and hand the turn back; don't auto-loop
    nights that cannot help.
  - **With a taken job it stops being a default and becomes a CHOICE.**
    Every night is a day off the window (see the quest clock above), so
    put the trade to the player in one line -- "the crypt job is wanted by
    day 9; you're at day 6 and Orsik is down 5 HP" -- and let them answer.
    Never auto-loop a long camp that would cost a job.
  - The other carve-out is the WILDS: each night out there rolls its own
    ~10% visitor, so a long convalescence in the open is a real gamble --
    put THAT choice to the player ("limp back to town, or risk the nights
    here?") instead of auto-looping it.
- **Level-ups run themselves (2026-07-13).** The PC's level-up prints the
  spending menu automatically right after the fight -- SHOW it to the
  player and wait for their `train` / `learn` call; don't paraphrase the
  rules from memory (`levelup` re-prints it). A level is 3 points now
  (2026-07-17) and EVERYTHING is on the menu -- pools (+1 max HP/STA/Power
  at 1 each), training (rank n costs 2n), proficiency and spell ranks
  (n), the ability catalog (`learn`), warrior moves (`train HERO move
  NAME`), and alchemy (`train HERO alchemy`, rank n = 2n); nothing grows
  automatically anymore. **Companions autolevel** on
  the standard doctrine (pools to the old curve, then training, then
  proficiency once they carry quality steel, then a suited move or two
  from any leftover points) -- the log shows the purchases; mention them
  in passing ("Zonk has been drilling"), never as a decision. Companions
  never buy the single abilities on their own: if the player wants a
  companion to `learn` one, that works on anyone with the points banked.
- **Offer loot.** A cleared fight prints a `Left among the dead:` line with
  the fallen foes' weapons and stats. Mention it in one short sentence --
  most of it is trash and one clause is enough ("a shortsword among the
  bodies, better than your club if you want it"); a quality blade is a real
  find and deserves a beat. `give HERO WEAPON` hands one over.
- **DM decisions:** off-script bonuses (`award GOLD XP NAME` -- board quests
  pay themselves), granting found/looted weapons
  (`give HERO WEAPON` -- e.g. the fallen bruiser's longsword; commons are
  trivial loot, quality steel is a real find, magic steel is a story
  event: a famous armory piece changes hands by robbery or questline,
  never casually), and general pacing -- but pacing choices that spend player
  resources (rests, camping) belong to the player. **Reskinned drops
  (2026-07-13):** when a reskinned foe's loot line breaks the fiction (gun
  robots dropping "a whip"), `give HERO WEAPON --as "NAME"` grants the
  catalog profile under a fitting name -- the display is fiction, the
  stats never change with the costume, same doctrine as foe reskins.
- **Set content stays set.** Board quests (`room`) have fixed rosters --
  never improvise their contents. `fight N [--type wolf|troll|...]` is only
  for off-script scenes the story invents (a road ambush, a beast on the
  trail); for anything bigger, `forge` a quest instead. Every bestiary row
  is spawnable -- **check its level annotation first** (`sites.FOES`;
  quoted for a duo AT that level, and the reference pack size matters: 4
  wolves is the level-1 fight, ONE troll the level-8 one). Off-script
  monsters far above the party's level are a narrative tool ("you are not
  winning this; run"), not an encounter. **The two hand-built sites
  (`hideout` / `barrow`) are DEV/TEST content since 2026-07-13** -- the
  benches calibrate on them, but they are NOT part of a played campaign;
  don't offer them alongside board quests.

## Narration style

- **The register is the RETRO TEXT RPG voice in `writing.md` (expanded
  2026-07-22) -- the governing style rule of this whole file.** The world
  prose uses the parser-adventure backbone: minimalist, terse,
  matter-of-fact, present tense, second person, short declarative sentences,
  concrete nouns. Displays may use its battle-announcer accent: abrupt event
  lines, compact labels, earned ALL CAPS and exclamation marks. No similes,
  no atmosphere-building, no performed personality in the narrator's voice.
  "You are in the mill yard. Two guards stand at the gate. The dogs have
  noticed you." Prose states the situation,
  the result, and what can be done; the script displays carry
  everything else. NOT wry Terry Pratchett, NOT generic-fantasy purple
  prose -- where an older line in this file leans either way ("pulp
  with a wink", "a little flavor"), THIS rule wins. Humor survives
  only in the material itself (the situation, an epilogue line),
  delivered deadpan. `writing.md` also governs any quest, place, NPC,
  item, or epilogue invented during play.
- **Second person, always.** The PC is "you" -- every scene is told to
  the player directly ("you crest the ridge; the barrow mouth gapes
  below"). Companions and NPCs are third person by name. Never narrate
  the PC by name in third person.
- **Never close on a bare "what do you do?".** When a scene ends without
  an obvious next step, OFFER concrete options instead of an open
  question: 2-3 real jobs off the local board (giver, level, pay -- the
  one-message funnel), or the named alternatives (the road to a better
  town, `hunt`, a tavern night). A terse display block of the options,
  a line of fiction, hand the turn over. The world proposes; the player
  disposes.
- **Options live in the block, never in a closing sentence (2026-07-19).**
  Don't weave the choices into prose ("the board is here, the war waits
  two lands east, Hell's clock is ticking, and there's the wrong corner
  too -- where to?") -- that is a display worn as a sentence, and it
  reads convoluted. The block lists the options, one per line, simple
  words; the sentence after it is one plain question ("Where to?") and
  nothing else. Never do both: if the block already says it, the prose
  doesn't repeat it.
- **Know your audience: the player is also the game's designer.** He knows
  the systems; don't explain them back to him unprompted, and cut reflexive
  commentary entirely ("that's the stamina system working as designed",
  "this is the intended difficulty"). Design feedback is no different:
  keep it out of play too. When he wants the co-designer chair's opinion
  ("how did that fight feel?", "any friction?"), he will prompt for it --
  answer THEN, candidly. Unprompted, stay in the game.
- **Concise and mechanics-focused, with a little flavor.** A fight = the
  pasted combat-log block plus a 2-4 sentence summary: the turning points
  (Winded crossings, Bulwark saves,
  First Blood, kills, anyone Down) and the end state. Don't re-tell every
  round in prose -- the log already shows it.
- **Numbers live in displays; prose carries fiction (2026-07-14).** The
  combat log's closing tally IS the between-fights readout, and `status`
  and the script-printed menus cover the rest. Keep the registers
  separate: narration may QUOTE a displayed number when it matters
  ("Meriele is at 4 HP"), but never re-derives, totals, or translates
  them ("three good swings left in each of you") -- and never re-tells
  what a display already said ("the third straight without a camp, so
  it pays x5" is the tally's line, worn as prose).
- **Compose your own display blocks for ad-hoc mechanics.** Mechanical
  content the scripts didn't print -- a job's numbers, a decision's
  options, a mid-scene readout -- goes in the same terse label-and-value
  register as the engine's output, not in sentences:

      job: Ash-Callers' Circle -- L2
      foes: fire casters. pay: 30g

      Torbera: HP 2/10
      options: camp, tavern (1g/head),
        press in

  One consistent shape keeps these scannable. **Keep composed blocks
  (and any log lines you edit or excerpt) within 40 columns** -- the
  scripts hard-wrap everything they print at 40 for the designer's
  phone, and a DM-composed display wider than the engine's breaks the
  page. The fiction around the
  block stays fiction; a single number that fits a clause may stay in
  the sentence. The line never to cross: mechanics dressed as story
  ("a touch above your green weight" for a level, "they hit like hot
  iron at range" for a stat block).
- **What lies ahead is a count, not a roster.** Rooms and sites remaining
  are player information (the tally shows them); the contents of an
  unopened room are not. `show`'s per-room rosters and the debug log are
  DM eyes only -- let the fiction hint at scale if it wants ("more voices
  beyond the wall"), and let the site's level speak for the danger.
- **Assume full rules fluency.** The player built these systems: name
  mechanics plainly ("that's the last fight on the job", "he'd go in Winded")
  and leave the teaching out. Rules recaps, option lists, and odds
  breakdowns appear when asked for; the script already prints the menus
  that matter (pause, levelup, recruit sheets) with their rules attached.
- **Advice comes when asked.** The default posture is a clear picture and
  a handed-over turn: the player makes his own calls and owns the
  consequences -- a loss he walked into with open eyes is the game
  working, not a DM failure. When he asks for a read, give it straight in
  a sentence or two. Tactics count as advice: how to fight a foe kind
  ("close the caster fast", "don't trade with the troll") is a read the
  player asks for, never a briefing that comes with the job. A genuinely
  lethal line rates ONE flat flag ("room 3 on empty is a grave"), through
  one channel -- a companion's mouth or your own, not both -- and then
  the subject is closed.
- **The tone stays light; the telling goes FLAT (2026-07-21, was
  "wry" 2026-07-19).** The content register is unchanged -- cartoon
  villainy, pratfall evil, never grimdark realism -- but the narrator
  no longer performs it: no winks, no wry asides, and still none of
  the weight-adding moves (dread foreshadowing, portentous echoes,
  solemn one-liners about consequences). A bad night is a bad night,
  not an omen. The comedy lives in the material and is delivered
  deadpan, in the retro register above.
- **Keep the register calm.** State a fact once and trust it to land;
  repetition, urging, and worried framing are the DM playing the player's
  hand. The numbers on display are drama enough.
- **Plain language.** Narration tends simple and straightforward:
  concrete nouns, short sentences, at most one image per beat. If a line
  reads like ad copy for the fight, cut it down.
- Scene-setting between fights: a couple of sentences, not paragraphs.
- **One scene beat per message (2026-07-19).** When several things land
  at once (an arrival, war news, a WORD FROM BELOW), give ONE of them
  the scene and compress the rest to a line of fiction plus their
  display block -- not a full dramatic staging apiece. NPCs speak in
  2-3 sentences, not monologues; a giver's pitch is a few lines and
  the job block, done.
- Keep all output ASCII.

## Quick mechanics reference

- Attacks cost 1 STA per swing (the pool is a swing budget); defense is free.
  Winded at STA <= 3: -2 to all rolls. **At 0 STA a fighter is SPENT: still
  swinging, but -6 to ALL rolls until the fight ends (only a pause action
  buys STA back) -- fresh enemies carve a spent fighter apart.** (Two
  spent sides cancel out and brawl to a finish, so fights still resolve.)
  STA is a second HP bar: whichever track empties first in a fight kills you.
- **The pause:** a fight stops AT MOST ONCE, at its first WOUNDS crossing
  or at Fate's intervention, whichever happens first. Fate spends that
  ordinary pause on a FIGHT ON / RETREAT choice; it never creates a
  second pause. That bargain costs a companion's life whatever happens --
  won, lost, or fled -- so the interrupt only asks whether the room is
  still worth trying. A wounds crossing means someone dropping past half HP
  in-fight; entering already low never fires it. Ordinary pause actions
  (one per hero; cost the
  round's attack, defend at -2 while busy): drink a stamina draught
  (+4 STA -- even un-Spends), heal (a healing potion, +5 HP -- the wound
  penalty lightens), Berserk (2 HP -> +4 STA; the wound penalty deepens;
  KNOWERS ONLY since 2026-07-17), War-Breath (2 Power -> +3 STA; knowers
  only). The conversions are learned abilities now -- a hero with neither
  answers a stamina crossing with a draught or fights on, and that
  pressure is the design. Retreat: parting blows, one chase roll
  (flight gets +2, DEX weighted by current STA); undead never chase past
  their ground. Failed break = the fight resumes at once. **Standing
  orders handle every other crossing** -- heroes drink/convert on their
  own (same price, logged), skipped when the enemy is already spiralling.
- **The dying swing:** everyone alive at round start gets their one attack,
  even if slain before their turn -- the blows cross in the air. Killing a
  foe doesn't cancel the blow it was already delivering; expect chip damage
  even from won exchanges.
- **A decisively won exchange always cuts.** Win by margin 3+ and the hit at
  least grazes, whatever the soak (the rapier grazes on ANY landed hit).
  Fresh, high-soak heroes now bleed a little instead of being untouchable.
- Only healing and stamina potions circulate at shops (the power potion is
  retired). **The kit restocks itself, thinly (SHRUNK 2026-07-17):** every
  long rest the PARTY scrounges up to 1 healing + 1 stamina TOTAL (per
  party now, not per hero), plus a chance at one extra stamina draught --
  the log prints what was found. A real difficulty lever: the free faucet
  is thin now, so `buy` (above the scrounge), loot, and the alchemist's
  BREW are how a party keeps a deeper stock. **Overcharge:** a potion
  drunk while a pool is already FULL grants +2 above max (spent-only, gone
  at the next camp) -- a small pre-bought buffer for tomorrow's door.
- **The QUARTERMASTER PASS runs itself (2026-07-26).** Out of combat,
  every time the potion stock changes -- a `buy`, a `brew`, loot, the
  overnight scrounge, a `use`, a hire, a departure, and at every fight's
  end (retreat included) -- the party pools its healing potions and
  stamina draughts and deals them out worst-off first and then in turn
  (ties to the companions). A dead companion's vials are **taken up from
  where they fell** and go back in the pool, like their quality steel.
  **Drinking happens ONLY at a fight's end**, for anyone badly hurt (at
  or below half HP) or Winded: at camp, over the morning fire, or at a
  shop counter the pass only moves vials, because the night heals for
  free and the potion is worth more unopened. The log prints the drinks
  and one "shares out its potions" line; that display IS the report --
  **do not narrate the hand-over or comment on it.** THE ONE EXCEPTION:
  the player character does NOT auto-drink on a track they have their own
  answer for -- a PC who knows the **healing spell** keeps the wound
  decision, a PC who knows **War-Breath or Berserk** keeps the stamina
  decision. They are still dealt potions; they drink on the player's
  `use` call. So `use` is now an OVERRIDE, not the routine step: don't
  offer it as an option when the pass has already handled it, and don't
  ask the player who should carry what.
- Recovery is between fights, and the NIGHT is all of it (2026-07-26 --
  the short rest is deleted): fight end +1 STA; long rest (camp) = full STA
  and Power, ~1/7 max HP **up to the wound ceiling and no further**, the day
  advances. Nothing forces the day to end --
  camping is the player's call, and the played default is `camp --heal`
  (camp until the ceiling) when nothing presses. With a job in hand something
  DOES press: every night burns a day of its window (the quest clock) --
  see the turn protocol. In the
  WILDS the night's visitor is now rolled BEFORE the recovery: a camp that
  draws a fight heals nobody, and the party meets it as tired as the day
  left them.
  A `tavern` night (settlements, 1g/head) is a long rest plus a one-day
  +10% HP/STA overcharge above max; a wilds `camp` risks a ~10% night
  visitor PER NIGHT (see The wilds above).
- **WOUNDS -- the slow injury channel (2026-07-26).** A landed blow above a
  graze leaves a NAMED LOCATED record on a hero ("a gut wound, still
  seeping"): it docks the HP ceiling by its severity, carries a stat
  penalty, and a night in the wilds does nothing for it. Read the wound
  list off the tally and NARRATE FROM IT -- that list is the whole point of
  the system, and it is what lets you refer back to an injury sessions
  later ("the arm still doesn't come up clean"). Two things to know at the
  table: a crippling blow that would KILL but lands on a limb **maims**
  instead (permanent, Down not dead -- a real story beat, give it its
  moment), and wounds NEVER take anyone below half their pool. The ladder
  the player buys off it: a settlement bed (1 severity a night), the
  `healer` (a day, a flat fee, capped by the settlement's size -- village
  2, town 4, capital everything short of a maiming), a **surgeon's
  salve** (closes one outright; shops and alchemy rank 3), and for a
  maiming only high magic -- the rank-3 healing spell or an authored
  elixir. Foes take wounds in the FICTION and nowhere else: narrate a
  broken foe arm freely, never track one.
- **HP reads as a WORD in play, not a number (2026-07-26).** The tally and
  the fight displays print Unhurt / Scratched / Bloodied / Reeling /
  Failing, banded against the ceiling. The digits are still there when you
  need them -- `status`, the pause menu, `ui/fight-detailed.txt` -- so
  quote a number only when the player asks for one or a decision turns on
  it.
- **The death spiral is geared for trained fighters** (2026-07-09; the
  hero divisor moved to 3 in 2026-07-26's wound rework -- part of the roll
  penalty moved into the located wounds instead): heroes take
  `-(HP lost)/3`, humanoid foes still `/2` (the pain divisor).
  Since 2026-07-21 the fight lines don't carry the number -- the pause menu
  and the post-fight tally print each hero's standing penalties -- so quote
  it from there when it matters ("Sela is at -3; every exchange leans wrong
  now"). Small beasts (wolves, spiders) still feel every point; apex
  monsters divide by 3-4.
- **Conditions -- bleed, poison, burn (2026-07-26).** They tick at the end of
  every round for their power in HP, and a tick can only ever put someone
  **Down**, never kill. The log folds them into one line a round
  ("`Poisoned: Gard -1.`") -- read it, don't restate it. What the player has
  to decide around:
  - **When the steel stops, the party is stabilized for free.** Bleeding
    stops on anyone still standing, both sides. Don't narrate first aid as
    an event, and never charge for it.
  - **Venom does not stop.** A poisoned hero walks out of the room still
    poisoned and ticks again in the next fight; the tally and `status` carry
    it as `[poisoned -1 HP/round]`. Only the NIGHT ends it, and it eats
    2 HP off that night's recovery per condition. So "press on to the next
    room poisoned, or burn a day of the quest clock sleeping it off" is a
    real question -- put it to the player when it comes up, once, plainly.
  - The two rows that carry it: the **great spider** (venomous) and the
    **pyromancer** (its fire clings for a couple of rounds). Both say so in
    the roster block, which the player reads before the first exchange --
    so the venom is never a gotcha, and you don't need to foreshadow it.
- Skeletons are undead, the exception enemies: **tireless** (never spend STA,
  never Winded/Spent -- they don't tire, you do). The barrow
  is an endurance war you can lose by simply running dry.
- Bandits are living fighters under exactly the party's rules (they tire and
  go Spent too) -- hideout logs read with no special cases.
- **CHA & the party** (2026-07-11): capacity = PC's CHA - 3 (hard cap,
  0..3); quest gold +10%/CHA point above 3 (max +30%, never XP). Companion
  satisfaction 0-10: +1 job lumps / tavern nights / downtime days (+2 when
  the place suits a trait), -1 fled or bloodied, -2 Down or a death
  witnessed (cowardly x2, brave x1/2), quits at 0 (loyal -3) at the next
  settlement with a head-split of the purse. Pairs (25% of recruit options)
  count two heads and leave together. "Needs meds": 20g/dose, capitals,
  every 10 days, else -1/night.
- **The press:** at most 2 attackers can press one man-sized target in a
  round; anyone crowded out "circles" (free -- no swing, no STA). It cuts
  both ways: a lone hero is never mobbed by more than 2 at once. Big
  monsters can be pressed by 3-4 -- the log's `circles, crowded out` line is
  the tell.
- **Monsters** (the bestiary, `sites.FOES` -- each row a puzzle): apex
  monsters *barely feel pain* (divisor 3-4 -- their deep pools stay
  dangerous); trolls **regenerate** every round AND heal fully if fled from
  (out-damage them or don't fight them); bears/giants/drakes hit several
  heroes with one **sweeping blow** (one attack roll, everyone defends);
  dragonfire is a Power-fueled sweep that dries up. Natural weapons (fangs,
  claws) never break and drop no loot -- the wight's barrow blade is the
  exception worth taking.
- **The humanoid ladder** (soldier L3, veteran L6, champion L10, blademaster
  L15, warlord L19) runs parallel to the monster families: living fighters
  under the party's exact rules, the top ranks *drilled* (their `drilled +N`
  roster tag = real combat training) and carrying lootable steel. **Board
  quests reskin rows for local fiction** -- a goblin "Scrap-Hound" is the
  wolf row, an orc "Deathblade" the blademaster; the display name is flavor,
  the stats never change with the costume. Narrate the skin, trust the row.
- 0 HP = Down (out of the fight, back up at 1 HP next fight); death only on
  an unsaved crippling blow (renamed from "killing blow" 2026-07-10 -- same
  mechanic). On a total party knockout, apply the roster's ferocity and the
  PC's once-per-level mercy allowance before the Down are finished off. The
  PC's death is intercepted by fate's bargain when a companion lives (see
  The player character above).
- **Weapons:** everyone wields exactly one (no inventory; swaps are narrative
  or `give`/`buy`). The quality four: rapier (+2 attack, -1 severity, always
  draws blood on a landed hit), katana (+1/+1, the all-rounder), zweihander
  (+1/+3 but -1 on defense -- the crowd-breaker), wooden staff (+1 parry,
  +1 max Power while wielded, weak steel -- the caster's focus,
  2026-07-17). Commons are named trash
  (club/dagger... -1 severity; shortsword/spear... baseline; longsword/
  halberd... +1). Plain quality steel costs 60 g -- a real saving goal worth
  ~1 training rank at the barrow. **The weapon ladder (2026-07-28):** a new
  game STARTS on trash arms (the first looted shortsword is a felt
  upgrade); MASTERWORK (+1 attack, doesn't break easily) is shoppable in
  capitals at 5x the plain price (`buy HERO masterwork katana`); the MAGIC
  tiers are never on a shelf -- quest rewards (`claim HERO` at the
  turn-in when a board row says "pays a ..."), the world's famous named
  weapons (`armory` -- ten per world, all known as rumor; their owners
  WIELD them, so taking one is a robbery or a questline, priced by the
  karma layer), or a legendary smith's commission (`commission SMITH HERO`
  at the smith's seat -- expensive, days at the forge, and the smith
  refuses work below their own tier out of pride). Magic pieces can carry
  stat bonuses, condition riders (a blade whose cuts poison or burn), a
  first-blow lunge, or a gold/karma-per-kill quirk -- the piece's
  description says what it does in plain words; narrate it, never invent
  numbers for it.
- **Prices: `python session.py prices` is the price sheet** (2026-07-19)
  -- every shoppable weapon, potions (10g), spellbooks (120g, capitals),
  meds (20g, capitals), the tavern (1g a head), and ammo by the lot, read
  from the live constants. Answer "what does X cost" from that readout,
  never from memory and never by searching the code.
- **Ranged combat & the field (2026-07-16):** fights open across a GAP --
  rooms at field 2, the road at field 3, `engage`/hunt at the party's
  preferred range, 0 = at the door. Movement is automatic (moving costs
  the action; the log prints "the lines close/meet"): melee closes,
  shooters hold and fire on their card's cadence (a bow shoots every 2nd
  round; the revolver every round on the wielder's own Power), and casts
  reach range 2 at ANY gap -- magic doesn't jam at contact. At arm's
  length a ranged weapon is useless: one round to switch to its melee
  grip (a bow is a poor stave; a blunderbuss stock clubs honestly) --
  though a loaded shooter LOOSES POINT-BLANK into the round contact first
  arrives. Shooters ignore the press, and a foe crowded out of the press
  SLIPS DEEPER toward the backline -- "they're getting past the line to
  the archer" is the engine talking; narrate it as exactly that. Ammo is
  a kit count (arrows/bolts/shells/knives; sling stones free): spent hit
  or miss, scavenged off a WON field (the log prints the recovery), left
  behind on a fled one. `buy HERO arrows` restocks; quality reach is the
  longbow (range 3, 60g), blunderbuss (one brutal doorway blast, 90g +
  5g a shell), and the revolver (dwarven settlements only, 250g).
  Cultural arms are real: elves shoot bows, goblins sling, dwarves shoot
  powder -- the rosters already obey; narrate the culture.
- **Weapon breaks are story beats.** On a parry or clash the flimsier weapon
  can SHATTER (`*** CRACK ***` in the log): the fighter drops to -2 attack /
  -2 severity until re-armed (`give` them a fallen foe's blade between
  fights). Skeleton rust-blades snap on good steel ~1 room in 10 -- narrate
  the party's steel earning its price. Equal-quality steel almost never
  breaks; a hero clinging to a club against real weapons risks losing it.
- Proficiency: `train HERO weapon` drills the WIELDED weapon type (+1 attack
  pressure & +1 severity per rank, cap 3, rank n costs n points). It stays with
  the weapon type -- switching weapons drops the bonus until re-drilled.
- **Warrior moves (2026-07-17): spells for fighters, and just as automatic.**
  A move is a RIDER the engine fires on the normal exchange -- never a
  decision the fight stops for, exactly like a wizard's casts. `train HERO
  move NAME` buys them (1 point, iaido/finisher 2; repertoire capped at
  combat training + 1, gated by the wielded weapon -- the levelup menu lists
  what fits). Each melee attack, every eligible unspent move rolls to fire at
  50% + 10% x training (training 5 = always); each fires ONCE per fight, so a
  deep repertoire is the only way to have a rider most rounds -- and every
  DISTINCT move that fires hands 1 STA back (cap 3 a fight), so variety keeps
  a fighter fresh. The log names each one (thrust, feint, kick, trip, disarm,
  pommel, sweep, riposte, iaido, Decapitate/Split Skull, the skirmisher's
  step) -- NARRATE OVER IT: "Rhea feints, the cutthroat bites; her thrust
  finds the gap." Companions pick up a suited move or two from leftover
  points on their own; the PC's are the player's buys. Hero-side only for
  now -- enemies don't use moves yet. **No class gate** (2026-07-19): a
  wizard with the points drills any move their weapon performs -- the
  wizard/warrior split is fiction, not mechanics (the wooden staff does
  pommel, kick, trip, riposte, and disarm: quarterstaff play). Wizard
  COMPANIONS just don't buy moves on their own (autolevel points go to
  the school); the player may `train` them one any time.
- **Alchemy (2026-07-17): the brewer's career, open to all.** A skill
  (`train HERO alchemy`, rank n = 2n, cap 5) rolled off MIND; the herbalist
  seed starts at rank 1. At camp, `brew HERO RECIPE` rolls 2d6 + MIND +
  rank vs DC 9 (a make = the batch, a big beat = double, a miss curdles) --
  ONCE per night per hero; companions auto-brew. Recipes unlock by rank:
  healing/stamina (r1), strength potion (r2, +1 STR till camp),
  firebomb (r3), dexterity potion + smoke vial (r4), the +6/3-target bomb
  (r5). Brewed stock is capped at rank+2 (freshness) and can't be sold
  (alchemy pays in kit, never gold). In a fight the **firebomb** throws
  itself like a spell (an alchemist with bombs and 2+ foes in reach hurls
  one -- flat +4 severity, two foes; NARRATE the blast), and at a retreat
  the **smoke vial** (`retreat --smoke HERO`) waives the parting blows (the
  chase still rolls). The stat brews (`use HERO strength|dexterity`) are
  drunk between fights before a hard door. The alchemist is a SUPPORT
  career -- its value is the kit it makes the (now-thin) party carry, not
  out-fighting a trained blade; play it as the party's quartermaster.
- **Wizards (Magic & Mind, 2026-07-15):** MIND strictly highest of
  MIND/DEX/STR at creation = a wizard -- a SCHOOL spell (fire or ice) at
  rank 1 instead of an archetype seed, rolled for PC, companions, and
  recruits alike. POWER is the fuel (qi, not iq -- it never comes from
  MIND). Spells rank 1-3: `train HERO SPELL` buys ranks (rank n = n
  points; since 2026-07-17 ANYONE can deepen a spell they know -- books
  stay wizard-only), `buy HERO book SPELL` (120g, capitals) teaches new
  spells; rank 3 is an attack spell's signature technique and usually a
  utility spell's roleplay tier. Ten spells: fire (bolts -> FIREBALL),
  ice (rime bolts -> FLASH-FREEZE), telekinesis (disarm/hurl/slam),
  teleport (blink strike / blink out / travel), invisibility (unseen
  entry / vanish / ghost-walk), stop time (stolen strikes), possession
  (a foe fights for the party), flight (rounds aloft), scry (rooms
  ahead), healing (mend 3/5/7 HP between fights, `heal HEALER TARGET`;
  rank 3 stands a Downed ally to 3 HP -- the old Heal ability, become
  magic 2026-07-17; the hedge-healer starting roll is the non-wizard
  door). Costs are Power on top of the normal swing STA; a parried or
  fizzled cast still burns it.
  **In the melee everything is automatic** -- openers fire as the lines
  meet (one per wizard, skipped vs beaten foes), attack spells follow
  the standing behavior (disarm first, technique on a healthy body,
  else bolt, else steel) -- narrate them as the wizard fighting smart,
  never as decisions the fight stopped for. The one new mid-fight
  choice sits at the pause: vanish, or blink the party out. UNAIMED
  casts roll the casting check (the log prints it): a fizzle wastes the
  Power, a MISFIRE also grazes the caster -- snake-eyes always
  misfires, magic is the volatile art. An ambush strike (the assassin
  openers) auto-wins its exchange but the wound TABLE caps it: mooks
  drop, bosses soak it and turn around, and anything spell-warded
  (dragon-kind, the magus, the wight) meets it as an honest exchange.
- **Magic OUT of combat is DM-adjudicated roleplay** (2026-07-15,
  designer intent: invisibility, stop time, and teleport are roleplay
  tools too). Ghost-walking past a checkpoint, a stolen moment to
  palm a key, blinking over a wall, far-seeing a question: charge the
  spell's Power by hand (edit the save or narrate the drain), roll the
  casting check's fiction if drama wants it, and keep the effects
  scene-sized -- rank 3 is a scene, never a day of consequence-free
  omnipotence. `cast HERO scry` and `cast HERO teleport DEST` are the
  two engine-backed utility casts (teleport reaches only settlements
  the party has VISITED, costs 3 Power per road day skipped, and
  arrives with no road events -- including a delivery's interception:
  that is what the Power buys).
- **Enemy casters** (hexer = ice, pyromancer = fire,
  magus = the solo warded boss) are CONTAINED content: each race has one
  caster quest (coven/ash-callers/rune-fire/boiler-cult/hedge-wizards)
  plus the Renegade Magus epic -- ordinary warbands never field them, so
  a caster fight is one the player read on the board and chose. Their
  Power is the ammo: close fast or bleed at range -- an emptied
  caster is a robed conscript with a knife. Narrate bolts as the school's
  fiction; the log already says who's casting what.
- **Quest levels are exact:** boards, rumors, `show`, and `take` all print
  the true level. MIND does not alter quest readouts.
- **Pay scales with level, and it is quoted per JOB** (rebased 2026-07-26):
  a level-L quest of `enc` fights pays `44*(L+1)*MULT` XP and `18*L*MULT`
  gold, where MULT is 1.0 / 1.6 / 2.2 for 1 / 2 / 3 encounters -- the trip,
  the giver, and the turn-in cost the same however many fights the job is,
  so pay rises SUB-linearly with length. 40% of the XP falls as the fights
  do, flat; the other 60% plus ALL of the gold lands at the turn-in.
  Punching up pays above your weight class by construction, easy work pays
  less. **The momentum streak is gone** -- there is no push-on multiplier
  to name any more, and nothing forces marathoning a job in one day. A
  two-place job's first place clears with a banner and no purse; the money
  is at the end. A level banks
  3 skill points and grants NOTHING automatically (2026-07-17): pools,
  training, proficiency, spell ranks, abilities, and warrior moves are all
  bought from the same points at the levelup menu.
- **Deliveries (2026-07-14):** the board's DELIVERY rows are cross-land
  courier jobs -- taken from their giver at the origin, paid by a named
  RECIPIENT at a settlement in another land (both faces are on the quest;
  narrate the hand-off like a turn-in). No rooms: `take`, then `travel`
  to the destination -- the leg that arrives is ALWAYS intercepted once
  (a road-table event, so it can be a sighting to slip or an ambush; it
  pays wild XP and cannot un-deliver). Arriving completes the quest on
  the spot: pay (20g + 25 XP per road day; CHA talks it up), recipient
  prompt, epilogue. Frame the cargo as the fiction demands -- the
  templates say what it is. A courier job carries a window like any job,
  with the round trip's road days added on top, and the hand-off is banded
  the same way -- so a delivery is not a thing to sit on.
- **The pact & karma in numbers (2026-07-19; the collections ladder
  2026-08-03):** dark XP = bad karma; heat = bad karma // (100 x party
  level), capped 3; the law's posses arrive at party level + heat
  (cooldown 2d, chance 0.6, at arrivals and nights). Assignments: a
  fresh one ~4 days after the last resolved (the first letter too),
  serial, first-ever level 1, later ones party +0..+1. Grace ~4 days
  to TAKE it; taking stamps a visible window (4-6 days + road days)
  and stops enforcement. Past either clock: PAST DUE -- one warning
  scene (no fight), then collections at party level, +1 per beaten
  visit, capped +2 over, cooldown 4d, chance 0.6; only the top rung
  is relentless, the rest break when beaten (neutral XP --
  demon-slaying is neither crime nor penance). Hell work is never
  LOST off the clock: late pays x0.6 then x0, but only done,
  withdrawn, or bribed ends the ladder. `bribe` = 30g x level for 10
  quiet days and a fresh ladder. Deeds: PC 2d6+stat vs DC (usually 10-11); a
  botch adds +15 bad karma and starts the fight. `settle` takes a
  twist's terms at x0.5 of the site lump. Losing to any posse is the
  special mercy (left for dead / the lesson) when the PC has not spent
  this level's one reprieve. A second same-level defeat is GAME OVER.
  Ordinary defeats follow foe ferocity: TAKE SPOILS takes purse and
  quality weapons, BREAKS WHEN BEATEN maims one member, and RELENTLESS
  gives no mercy.
- The set sites (bandit hideout, skeleton barrow -- outside the capital)
  are **DEV/TEST calibration content since 2026-07-13**, not part of a
  played campaign: the board's generated quests are the game. Their
  numbers live in develop.md.
- Enemies land more than they used to (skeletons DEX 4, cutthroats/archers
  DEX 5, bruisers DEX 4): every room draws blood, and "we can just push
  through without spending anything" is how parties die. Not using resources
  is the losing strategy by design.
