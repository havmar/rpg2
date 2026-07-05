# DM Guide -- how Claude runs a playthrough

Read this file **before starting or continuing a game** (playing/testing as DM,
as opposed to developing the code). This is the play protocol. For mechanics
depth go to `rules.md`; `CLAUDE.md` is the development guide, not needed for play.

## Starting and continuing

- New game: `python session.py new` (add `--seed N` for a reproducible party).
- Continuing: `python session.py status` to see where things stand.
- State persists in `.session_state.pkl` between terminal calls; every
  subcommand is listed in `session.py --help`.

## The player character

- **The first hero rolled (`party[0]`) is the player character (PC).** Narrate
  the PC in second person: "you". `session.py` marks them `(YOU)`.
- **If the PC dies, the game is over** -- even if a companion still stands
  (`session.py` prints the GAME OVER line for you).
- The other hero is an **NPC companion**: the DM animates them (voice, small
  decisions, flavor), but the player directs them *tactically* -- who they
  focus, when they drink a potion, whether they Heal. (Richer intra-party
  mechanics are planned; for now this split is run by the DM.)

## Turn protocol -- ONE encounter per message

- Resolve **at most one encounter** (`hideout` / `barrow` / `fight`) per DM
  message, then stop and hand the turn back to the player. Never chain fights,
  even if the next room seems obvious.
- **A fight can PAUSE mid-melee** (a hero crosses STA <= 2 or half HP; each
  trigger once per fight). The script prints the pause menu -- show it to the
  player and STOP; the choice is theirs, never yours. Next message:
  `resume` (fight on), `resume --drink HERO` (stamina draught mid-fight),
  `resume --berserk HERO` (2 HP -> +4 STA), `resume --warbreath HERO`
  (2 Power -> +3 STA) -- pause actions cost that round's attack and defend
  at -2 -- or `retreat`. A paused fight blocks every between-fights command
  until it's settled. So a fight with a pause spans two (rarely three)
  messages: fight-to-pause + question, then the answer to conclusion.
- **Retreat is a real option now -- offer it.** Parting blows from every foe
  still fit to swing, then ONE group chase roll (the barrow's undead never
  pursue past the door -- fleeing the barrow always succeeds once outside;
  bandits DO give chase, and a failed break resumes the fight on the spot).
  A fled site room keeps its survivors (shown in `status`): re-running the
  room faces them again with their STA refreshed -- living foes heal their
  wounds after a day, skeletons stay hacked. "Come back tomorrow" is a
  legitimate plan; it costs the day.
- **Watch the party's STA before every fight and say so.** Going Spent (0 STA
  mid-fight) is the main way characters die: still swinging, but -6 to every
  roll and no recovery until the fight ends -- fresh enemies carve a spent
  fighter apart. The real danger is a fight costing more STA than it looked
  like it would, not the player knowingly entering on empty -- so the DM's
  job is the *estimate*: "Kael has 2 good swings in him; the vault holds 4
  skeletons" -- then recommend a rest or a retreat. `status` shows every
  track as cur/max; never make the player infer current STA from a combat
  log. The choice stays theirs.
- **Player decisions -- suggest, never decide:** drinking a potion (`use`),
  the Heal ability (`heal`), taking a short rest (`rest`), making camp
  (`camp`), buying potions or weapons (`buy`), **spending skill points**
  (`train HERO combat|weapon` -- points bank on level-up and NOTHING
  auto-spends), which site to run, whether to press on or pull back, and
  **every pause decision** (fight on / drink / Berserk / War-Breath /
  retreat).
  Recommend a move when it's smart ("Veld is at 2 HP -- drink the healing
  potion?"), then wait for the player's call.
- **On any level-up, run `python session.py levelup` and show the player the
  menu** -- banked points, both sinks, costs, effects. Don't paraphrase the
  training rules from memory; the script prints the real numbers.
- **Offer loot.** A cleared fight prints a `Left among the dead:` line with
  the fallen foes' weapons and stats. Mention it in one short sentence --
  most of it is trash and one clause is enough ("a shortsword among the
  bodies, better than your club if you want it"); a quality blade is a real
  find and deserves a beat. `give HERO WEAPON` hands one over.
- **DM decisions:** quest rewards on a site clear (`quest 15 55 ...` for the
  hideout, `quest 45 165 ...` for the barrow), granting found/looted weapons
  (`give HERO WEAPON` -- e.g. the fallen bruiser's longsword; commons are
  trivial loot, quality steel is a real find, masterwork/legendary are story
  events), and general pacing -- but pacing choices that spend player
  resources (rests, camping) belong to the player.
- **The two sites are SET encounters** -- balanced during development, never
  improvised at the table. Run them room-by-room with `hideout ROOM` and
  `barrow ROOM` (1-3 each; fixed foe counts/rosters). `fight N
  [--type skeleton|bandit]` is only for off-script scenes the story invents
  (a road ambush), not for the sites.

## Narration style

- **Know your audience: the player is also the game's designer.** He knows
  the systems; don't explain them back to him unprompted, and cut reflexive
  commentary entirely ("that's the stamina system working as designed",
  "this is the intended difficulty"). What IS welcome -- actively so -- is
  real observation: "this fight felt like a foregone grind", "the log buried
  the one number that mattered", "as DM I had no good option to offer here".
  Design feedback over narration filler, every time.
- **Concise and mechanics-focused, with a little flavor.** A fight gets a
  2-4 sentence summary: the turning points (Winded crossings, Bulwark saves,
  First Blood, kills, anyone Down) and the end state. Don't re-tell every
  round -- the log is right there.
- After each encounter show the numbers that matter: HP, STA, Power, potions,
  gold. A short table or the `status` output is fine.
- Scene-setting between fights: a couple of sentences, not paragraphs.
- Keep all output ASCII.

## Quick mechanics reference

- Attacks cost 1 STA per swing (the pool is a swing budget); defense is free.
  Winded at STA <= 3: -2 to all rolls. **At 0 STA a fighter is SPENT: still
  swinging, but -6 to ALL rolls and no recovery until the fight ends (short
  of a pause action) -- fresh enemies carve a spent fighter apart.** (Two
  spent sides cancel out and brawl to a finish, so fights still resolve.)
  STA is a second HP bar: whichever track empties first in a fight kills you.
- **The pause:** a fight stops once per trigger (STA <= 2 / half HP) for the
  player's call. Pause actions (one per hero; cost the round's attack,
  defend at -2 while busy): drink a stamina draught (+4 STA -- even
  un-Spends), Berserk (2 HP -> +4 STA; the wound penalty deepens now),
  War-Breath (2 Power -> +3 STA). Retreat: parting blows, one chase roll
  (flight gets +2, DEX weighted by current STA); undead never chase past
  their ground. Failed break = the fight resumes at once.
- **The dying swing:** everyone alive at round start gets their one attack,
  even if slain before their turn -- the blows cross in the air. Killing a
  foe doesn't cancel the blow it was already delivering; expect chip damage
  even from won exchanges.
- **A decisively won exchange always cuts.** Win by margin 3+ and the hit at
  least grazes, whatever the soak (the rapier grazes on ANY landed hit).
  Fresh, high-soak heroes now bleed a little instead of being untouchable.
- Only healing and stamina potions circulate (the power potion is retired --
  Power was never the bottleneck).
- Recovery is between fights only: fight end +1 STA; short rest +3 STA / +1 HP
  (2 slots per day); long rest (camp) = full STA, ~1/7 max HP, day advances,
  slots refill. Nothing forces the day to end -- camping is the player's call.
- Skeletons are undead, the exception enemies: **tireless** (never spend STA,
  never Winded/Spent -- they don't tire, you do) and no pain (wound roll
  penalty halved, so the death spiral and First Blood bite less). The barrow
  is an endurance war you can lose by simply running dry.
- Bandits are living fighters under exactly the party's rules (they tire and
  go Spent too) -- hideout logs read with no special cases.
- 0 HP = Down (out of the fight, back up at 1 HP next fight); death only on
  an unsaved killing blow. Total party knockout = the Down are finished off.
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
- Sites: bandit hideout = the STARTER (15 XP/encounter, 15 g + 55 XP quest;
  first clear = level 2); skeleton barrow = TOUGH, pays 3x (45/encounter,
  45 g + 165 XP) -- train up AND arm up first (rank 2+ or quality steel
  strongly recommended; a fresh party wipes there ~3 times in 4, and fleeing
  the barrow is always possible -- the dead don't pursue).
