# DM Guide -- how Claude runs a playthrough

Read this file **before starting or continuing a game** (playing/testing as DM,
as opposed to developing the code). This is the play protocol. For mechanics
depth go to `rules.md`; `CLAUDE.md` is the development guide, not needed for play.

## Starting and continuing

- New game: `python session.py new` (add `--seed N` for a reproducible game
  -- `new` also generates the playthrough's whole quest world). It rolls
  THREE player-character candidates; show the player all three sheets
  (including each one's CHA capacity line) and let THEM `pick`. If his CHA
  holds anyone, **an old ally joins automatically at pick** (the script
  prints the sheet -- introduce them warmly; they're the PC's history, not
  a stranger), and the free first-evening introductions follow: `recruit`
  shows the companion candidates, `hire NAME` signs the player's choices
  (see The party below).
- **Open with the options, then hand over.** After `pick`, the first real
  message should lay out what the party can DO, in one short menu: the
  level-appropriate local jobs (via the ask-around funnel -- see The world
  and the quests below; plus the old hideout outside the starting
  settlement -- the level-1 starter), a `hunt` in the wilds, or a `tavern`
  night to round out the party first. The player drives from the first
  turn; don't railroad an opening quest.
- Continuing: `python session.py status` to see where things stand.
- State persists in **`save.json`** between terminal calls; every subcommand
  is listed in `session.py --help`. The save is plain JSON on purpose:
  commit it and the playthrough travels with the repo. Every save also
  rewrites **`party.txt`** (the full party info sheet) and auto-commits
  that one file -- the designer follows the playthrough through it; you
  never need to maintain it.
- **Editing `save.json` by hand is the DM's override.** When the story needs
  what no command provides -- grant gold, mend a wound, hand out a potion,
  resurrect a companion the fiction says survived -- edit the file between
  commands; every command reloads it fresh. Weapons are stored by catalog
  name (`"weapon": "katana"`); leave the `"rng"` blob alone. Use it for
  story, not convenience: the numbers are the game.

## The world and the quests (the game's spine)

The world holds ~5 race LANDS, each with settlements posting combat quests
at rolled levels (1-3 sites of 1-3 encounters each), plus its wilderness.
**The party is always somewhere, and quests are LOCAL**: the jobs you can
take are the current settlement's. **Which quest to take -- and whether
it's worth the road to a better town -- is the player's core decision:**

- `map` shows the known world: lands, settlements (with open-quest counts),
  notables, discovered wild places, the war's status, and where the party
  stands -- plus the in-game day.
- **There is NO quest board in the fiction (2026-07-12): quests come from
  PEOPLE.** `board` is YOUR inventory readout -- each row shows the job,
  its level (straight; too easy and too hard both appear on purpose), pay,
  and WHOSE job it is (every quest has a generated giver: name, role,
  personality). In play, run the **one-message funnel**: the party asks
  around -- the tavern keeper knows, any local points the way -- and ONE
  message lands them in front of the giver, who lays out the job ("you
  ask at the taproom; the mayor waves you on to the chief constable, a
  loud woman in flamboyant dress, who tells you about the crypt").
  Roleplay the giver from their trait line (edit any contradiction before
  presenting); they stay talkable while the quest runs, and the turn-in
  is THEIR scene. Present 2-3 jobs per ask unless the player wants the
  full slate; relay levels and pay straight, advise honestly, then let
  them pick. The board also lists **word from around the land** (other
  settlements' open jobs -- PLAYER-KNOWN, relay it) and **notables in
  town** -- the land's recurring cast (ruler, sage, wildcard): use them
  for color, rumor, and war scenes; they persist all campaign.
  (`board all` / `board NAME` is your wider overview for pacing.)
- **Turn-ins pay an EPILOGUE**: the QUEST COMPLETE banner prints a
  day-stamped aftermath line and a turn-in prompt naming the giver.
  Narrate the turn-in scene over both -- the epilogue is what the world
  now looks like because the party worked; don't skip it, don't pad it.
- `travel PLACE` moves them: 1 day inside a land, 2 days to another land.
  Travel days are camp nights (full overnight recovery -- travel heals) and
  each trip risks ONE road encounter (~15%/day compounded; see the wilds
  section below). Travel also RESETS the site momentum streak -- leaving a
  half-cleared site costs its escalating pay.
- `show QID` details one quest: description, sites, and what holds each room.
- `take QID` makes it active (must be AT its settlement); `room` fights its
  next encounter (same pause / retreat machinery as the set sites).
  Progress is remembered per quest -- switching quests and coming back
  later is fine, but working it means being there.
- **Check where the party stands BEFORE framing a scene.** Quests are
  local, and the scripts enforce it: `room`/`take` refuse with a "travel
  there first" line when the party is elsewhere. Don't narrate the arrival
  at the night market and then have the script contradict you -- glance at
  `status` (the `At:` field) or the active-quest line first; if the job's
  settlement is elsewhere, the road IS the next scene: narrate setting
  out, run `travel`, then frame the arrival.
- Sites pay themselves: each cleared site pays its lump (gold + XP) and the
  last one completes the quest -- no manual award needed. `award GOLD XP
  NAME` remains for off-script scenes only.
- `forge --level L --sites N --rooms N --kinds a,b,c --name "..."` builds a
  quest by the generator's rules for scenes the board doesn't cover, and
  posts it like any other. Prefer it over improvising rosters by hand.
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
- **Ordinary trouble is spotted first ~25% of the time too** (2026-07-10):
  the script prints `Spotted first -- L2: 3x Wolf...` and stops. Same
  protocol as the big sightings -- present it as landscape ("shapes
  circling a carcass, downwind of you"), then the player's call: `engage`
  to attack, any other move slips past. It's a free pass on a fight they
  didn't order OR free initiative on one they want -- don't editorialize
  which; the level readout speaks for itself.
- `explore` spends a day ranging the current land: discovers a new named
  place (persists on `map`, pays a little XP), camps rough overnight, and
  runs a higher encounter risk (~30%). Discovered places are yours to hang
  fiction on -- `forge` a quest there when the story wants one.
- `hunt` is the always-available farm: an immediate encounter at-or-below
  the party's level (their chosen prey), paying wild rates (below board
  work on purpose) plus normal loot rolls. When the player wants to grind
  gold or XP between quests, this is the sanctioned loop -- no day cost,
  but no free recovery either. NOTE: what roams a land is that race's
  template pools -- in some lands the cheapest prey is a level-3 dire
  wolf, and a fresh duo should hear about it before the pounce.
  **~10% of hunts the hunter is the hunted** (2026-07-10): an AMBUSH off
  the road's any-level table, met blade-first (the script prints it). The
  farm is never entirely safe -- warn a player who treats `hunt` as a
  zero-risk button, and when the ambush is far over their weight, running
  is the answer, as on the road.
- **Nights have geography now** (2026-07-10). `camp` in the WILDS risks a
  night visitor (~10%, the road's table, spotted/ambush valves apply --
  rolled after the night's recovery, so the party at least wakes fresh);
  behind settlement walls `camp` is safe and free. `tavern` (settlements
  only, 1g per living member) buys the same night PLUS a one-day
  OVERCHARGE: everyone wakes with HP and STA ~10% of max (min +1) ABOVE
  their caps ("13/12 HP"). The excess can't be topped back up once spent
  and fades at the next night's rest -- it's a buffer for tomorrow's
  door, best bought the evening before a hard site. Whether to pay is the
  player's call, like every rest decision; both taverns and camps reset
  the momentum streak (any night does).

## The player character

- **The first hero rolled (`party[0]`) is the player character (PC).** Narrate
  the PC in second person: "you". `session.py` marks them `(YOU)`.
- **If the PC dies, the game is over** -- even if a companion still stands
  (`session.py` prints the GAME OVER line for you).
- **Fate's bargain guards the PC (2026-07-10).** A blow that would kill the
  PC is commuted to a Down while a companion still draws breath -- the log
  announces it ("Fate has spared them; its price comes due if this fight
  is won"). If the party WINS that fight, the last foe's dying blow kills
  one RANDOM companion: the trade is a companion's life for the player's,
  and the engine prints it. If the party loses anyway, it's still a wipe
  and GAME OVER; a clean retreat waives the debt (nothing owed, nothing
  won). Play it with weight: the reprieve is a huge beat, and the
  post-spare choice -- press on and pay a companion, or flee with the
  downed PC -- belongs to the player. Never soften the price by fiat.
- The other heroes are **NPC companions**: the DM animates them (voice,
  small decisions, flavor -- their TRAITS are the material: a poetic
  whisperer and a swearing loudmouth should not read alike), but the player
  directs them *tactically* -- who they focus, when they drink a potion,
  whether they Heal.

## The party -- recruiting, satisfaction, departures (2026-07-11)

- **Capacity is the PC's CHA, and it is a hard cap** (CHA-3, 0..3 -- the
  scripts enforce it). A capacity-0 PC plays alone; say plainly at creation
  what that means (no fate's bargain, the solo numbers are brutal).
- **Recruiting happens at tavern nights.** Each paid `tavern` night rolls a
  fresh set of candidates (as many options as capacity, leveled to the PC
  +-1; ~a quarter are bonded pairs -- one option, TWO heads, they join and
  leave together). `recruit` prints full sheets -- show them to the player
  as-is (full transparency is the design, like straight board levels), then
  narrate the introductions over it. WHO to hire is the player's call,
  always. The DM's job is the fiction of the meeting and editing any
  generated contradiction on a sheet BEFORE presenting it.
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
- **`downtime` is the deliberate morale lever**: a day off in a settlement,
  best spent where a companion's trait points (Meriele loves animals ->
  a village day pays double). It costs a day and breaks the streak -- the
  trade is real; put it in the player's hands, don't spend it for them.
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

- **Waves post themselves** when the previous wave is done and the party
  hits the level -- the script prints a `*** WORD OF THE WAR ***` block
  (herald line + the ruler raising the call) at boards, arrivals,
  settlement nights, or right after the fight that leveled the party.
  **Deliver it as a scene** -- a rider, a bell, a refugee column -- not
  as a system message. Wave 1 doubles as the war's reveal: give the
  creed line its moment.
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

## Flavor beats -- two per session rhythm, always brief (2026-07-12)

The game is combat-centered; these two beats are how the world stays
bigger than the fights WITHOUT pages of narration:

- **The visual block**: on every scene change (arrival, a site's door, a
  new room chain, a camp), 2-3 lines of what is SEEN -- one wide shot,
  one detail that stands out, done. No lore dumps; the detail can carry
  the war, the race, or the season.
- **Party chatter**: `python session.py chatter` prints a seed -- 1-2
  companions and what they're preoccupied with (a trait, their mood from
  satisfaction). Riff it into a line or three of talk around the fire or
  on the road, then hand the turn back. Use it between fights, at camps,
  and on travel days -- roughly once a settlement-to-settlement leg, not
  every message. It is also your early-warning surface: a companion gone
  quiet at satisfaction 3 SHOULD be heard going quiet.

## Turn protocol -- ONE encounter per message

- Resolve **at most one encounter** (`room` / `hideout` / `barrow` / `fight`)
  per DM message, then stop and hand the turn back to the player. Never chain
  fights, even if the next room seems obvious.
- **Paste the PLAYER LOG into the chat.** Every encounter command prints the
  full debug log and then a `--- PLAYER LOG ---` block: headlines only, HP
  loss folded in, no dice math. Copy that block into your message as-is --
  it IS the fight's mechanical account for the player -- then add your short
  narration around it. The full log is for you (checking the numbers), not
  for the chat.
- **A fight pauses AT MOST ONCE (2026-07-11)** -- at its first WOUNDS
  crossing (any member dropping past half HP mid-fight; crossing-only:
  entering a fight already low does NOT trip it -- that was the player's
  call at the door). That one pause is the retreat question; treat it so.
  The script prints the pause menu -- show it to the player and STOP; the
  choice is theirs, never yours. Next message: `resume` (fight on),
  `resume --drink HERO` (stamina draught mid-fight), `resume --heal HERO`
  (healing potion mid-fight, +5 HP -- the wounds answer), `resume
  --berserk HERO` (2 HP -> +4 STA), `resume --warbreath HERO`
  (2 Power -> +3 STA) -- pause actions cost that round's attack and defend
  at -2 -- or `retreat`. A paused fight blocks every between-fights command
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
- **Watch the party's STA before every fight and say so.** Going Spent (0 STA
  mid-fight) is the main way characters die: still swinging, but -6 to every
  roll until the fight ends (only a pause action buys STA back) -- fresh
  enemies carve a spent
  fighter apart. The real danger is a fight costing more STA than it looked
  like it would, not the player knowingly entering on empty -- so the DM's
  job is the *estimate*: "Kael has 2 good swings in him; the vault holds 4
  skeletons" -- then recommend a rest or a retreat. This matters MORE now
  that entering low no longer trips a round-1 pause: the door is where that
  decision happens, and the DM's estimate is the player's only warning.
  `status` shows every
  track as cur/max; never make the player infer current STA from a combat
  log. The choice stays theirs.
- **Player decisions -- suggest, never decide:** drinking a potion (`use`),
  the Heal ability (`heal`), taking a short rest (`rest`), making camp
  (`camp` -- and since 2026-07-09 camping mid-site RESETS the momentum
  streak: pressing on pays escalating XP per room, camping trades that pay
  for safety; say the trade out loud), paying for the tavern instead of
  camping free (`tavern`), buying potions, weapons, or meds (`buy`),
  **who to hire and whether to hire at all** (`hire` -- and which PC to
  `pick` at creation), **who to let go** (`dismiss`), spending a day on
  companion morale (`downtime`),
  **spending skill points** (`train HERO combat|weapon` -- points bank on
  level-up and NOTHING auto-spends), where to `travel` and which site to
  run, whether to `engage` a sighting, whether to press on or pull back,
  and **the pause decision** (fight on / drink / heal / Berserk /
  War-Breath / retreat).
  Recommend a move when it's smart ("Veld is at 2 HP -- drink the healing
  potion?"), then wait for the player's call.
- **The default night is "camp until whole" (2026-07-11).** When there is
  HP to heal and the player hasn't said otherwise, assume the party camps
  to full -- `camp --heal` runs the nights in one go and reports the days
  passed (HP knits at ~max/7 a night, so it's often several). One night
  only is the EXCEPTION the player asks for, not the default. The carve-out
  is the WILDS: each night out there rolls its own ~10% visitor, so a long
  convalescence in the open is a real gamble -- put THAT choice to the
  player ("limp back to town, or risk the nights here?") instead of
  auto-looping it.
- **On any level-up, run `python session.py levelup` and show the player the
  menu** -- banked points, both sinks, costs, effects. Don't paraphrase the
  training rules from memory; the script prints the real numbers.
- **Offer loot.** A cleared fight prints a `Left among the dead:` line with
  the fallen foes' weapons and stats. Mention it in one short sentence --
  most of it is trash and one clause is enough ("a shortsword among the
  bodies, better than your club if you want it"); a quality blade is a real
  find and deserves a beat. `give HERO WEAPON` hands one over.
- **DM decisions:** off-script bonuses (`award GOLD XP NAME` -- board quests
  and the two set sites pay themselves now), granting found/looted weapons
  (`give HERO WEAPON` -- e.g. the fallen bruiser's longsword; commons are
  trivial loot, quality steel is a real find, masterwork/legendary are story
  events), and general pacing -- but pacing choices that spend player
  resources (rests, camping) belong to the player.
- **Set content stays set.** Board quests (`room`) and the two hand-built
  sites (`hideout ROOM` / `barrow ROOM`) have fixed rosters -- never
  improvise their contents. `fight N [--type wolf|troll|...]` is only for
  off-script scenes the story invents (a road ambush, a beast on the trail);
  for anything bigger, `forge` a quest instead. Every bestiary row is
  spawnable -- **check its level annotation first** (`sites.FOES`; quoted
  for a duo AT that level, and the reference pack size matters: 4 wolves is
  the level-1 fight, ONE troll the level-8 one). Off-script monsters far
  above the party's level are a narrative tool ("you are not winning this;
  run"), not an encounter.

## Narration style

- **Know your audience: the player is also the game's designer.** He knows
  the systems; don't explain them back to him unprompted, and cut reflexive
  commentary entirely ("that's the stamina system working as designed",
  "this is the intended difficulty"). What IS welcome -- actively so -- is
  real observation: "this fight felt like a foregone grind", "the log buried
  the one number that mattered", "as DM I had no good option to offer here".
  Design feedback over narration filler, every time.
- **Concise and mechanics-focused, with a little flavor.** A fight = the
  pasted PLAYER LOG block plus a 2-4 sentence summary: the turning points
  (Winded crossings, Bulwark saves,
  First Blood, kills, anyone Down) and the end state. Don't re-tell every
  round in prose -- the player log already shows it.
- After each encounter show the numbers that matter: HP, STA, Power, potions,
  gold. A short table or the `status` output is fine.
- Scene-setting between fights: a couple of sentences, not paragraphs.
- Keep all output ASCII.

## Quick mechanics reference

- Attacks cost 1 STA per swing (the pool is a swing budget); defense is free.
  Winded at STA <= 3: -2 to all rolls. **At 0 STA a fighter is SPENT: still
  swinging, but -6 to ALL rolls until the fight ends (only a pause action
  buys STA back) -- fresh enemies carve a spent fighter apart.** (Two
  spent sides cancel out and brawl to a finish, so fights still resolve.)
  STA is a second HP bar: whichever track empties first in a fight kills you.
- **The pause:** a fight stops AT MOST ONCE, at its first WOUNDS crossing
  (someone dropping past half HP in-fight; entering already low never
  fires it) for the player's call. Pause actions (one per hero; cost the
  round's attack, defend at -2 while busy): drink a stamina draught
  (+4 STA -- even un-Spends), heal (a healing potion, +5 HP -- the wound
  penalty lightens), Berserk (2 HP -> +4 STA; the wound penalty deepens),
  War-Breath (2 Power -> +3 STA). Retreat: parting blows, one chase roll
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
- Only healing and stamina potions circulate (the power potion is retired --
  Power was never the bottleneck). **The kit restocks itself (2026-07-11):**
  every long rest tops each hero back up to 1 healing + 1 stamina, free
  (brewed at the fire, scrounged in town -- the log prints it). `buy` is
  for stocking ABOVE that line before a hard push; nobody shops for the
  baseline.
- Recovery is between fights: fight end +1 STA; short rest +3 STA / +1 HP /
  +1 Power
  (**ONE slot per day**); long rest (camp) = full STA and Power, ~1/7 max HP,
  day advances, the
  slot refills. Nothing forces the day to end -- camping is the player's call,
  and the played default is `camp --heal` (camp until whole) when nothing
  presses -- see the turn protocol.
  A `tavern` night (settlements, 1g/head) is a long rest plus a one-day
  +10% HP/STA overcharge above max; a wilds `camp` risks a ~10% night
  visitor PER NIGHT (see The wilds above).
- **The death spiral is geared for trained fighters** (2026-07-09): heroes
  and humanoid foes alike take `-(HP lost)/2` to rolls (the pain divisor),
  and the player log now prints the penalty on every wound line -- quote it
  when it matters ("Sela is at -3; every exchange leans wrong now"). Small
  beasts (wolves, spiders) still feel every point; apex monsters divide by
  3-4.
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
  mechanic). Total party knockout = the Down are finished off. The PC's
  death is intercepted by fate's bargain when a companion lives (see The
  player character above).
- **Weapons:** everyone wields exactly one (no inventory; swaps are narrative
  or `give`/`buy`). The quality four: rapier (+2 attack, -1 severity, always
  draws blood on a landed hit), katana (+1/+1, the all-rounder), zweihander
  (+1/+3 but -1 on defense -- the crowd-breaker), wooden staff (+1 parry,
  +1 HP per Heal, weak steel -- the healer's weapon). Commons are named trash
  (club/dagger... -1 severity; shortsword/spear... baseline; longsword/
  halberd... +1). Plain quality steel costs 60 g -- a real saving goal worth
  ~1 training rank at the barrow; masterwork/legendary are never for sale.
- **Weapon breaks are story beats.** On a parry or clash the flimsier weapon
  can SHATTER (`*** CRACK ***` in the log): the fighter drops to -2 attack /
  -2 severity until re-armed (`give` them a fallen foe's blade between
  fights). Skeleton rust-blades snap on good steel ~1 room in 10 -- narrate
  the party's steel earning its price. Equal-quality steel almost never
  breaks; a hero clinging to a club against real weapons risks losing it.
- Proficiency: `train HERO weapon` drills the WIELDED weapon type (+1 attack
  pressure & +1 severity per rank, cap 3, rank n costs n points). It stays with
  the weapon type -- switching weapons drops the bonus until re-drilled.
- **Pay scales with level everywhere** (a level-L site pays `50*(L+1)` XP
  and `15*L` gold, split rooms-then-lump): punching up pays above your
  weight class by construction, easy work pays less. **Per-encounter pay
  rides the momentum streak** (steepened 2026-07-10): the k-th consecutive
  encounter in the same site without a night's camp pays (1 + 2(k-1)) x
  base -- x1/x3/x5, so the hideout's rooms pay 5/15/25 in one go but 5/5/5
  camped-between (the clear lump is unchanged either way; piecemeal
  collects ~70% of the site total, and the last room of a one-go run plus
  the lump carries ~80% of it). Doing the whole site in one push IS the
  paying line -- say the trade out loud at every mid-site camp decision.
  Multi-site quests streak per site (each site ramps and pays on its own;
  nothing forces marathoning a whole quest in one day). Levels also grow
  the body: +1 max HP/STA/Power on reaching every odd level (3, 5, 7...),
  on top of the banked skill point per level.
- Set sites (both a short march from the STARTING settlement -- travel
  there first): bandit hideout = the STARTER, a level-1 site (5/15/25
  XP by room in one go, 15 g + 55 XP clear; a one-go first clear = level
  2) -- a real fight: a fresh duo clears ~72% (up from ~58 since the
  2026-07-11 mid-fight heal + kit) and someone still hits the floor in
  about a third of runs, so expect downs, drunk potions, and retreats
  from day one. Skeleton barrow = TOUGH, a level-3 site (10/30/50 by room,
  45 g + 110 XP clear) -- train up AND arm up first (a fresh duo clears
  ~19% and wipes ~3 times in 4; rank 2 clears ~74%, rank 2
  plus steel comfortably more; fleeing the barrow is always possible --
  the dead don't pursue).
- Enemies land more than they used to (skeletons DEX 4, cutthroats/archers
  DEX 5, bruisers DEX 4): every room draws blood, and "we can just push
  through without spending anything" is how parties die. Not using resources
  is the losing strategy by design.
