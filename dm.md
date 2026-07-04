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
- **Watch the party's STA before every fight and say so.** Going Spent (0 STA
  mid-fight) is the main way characters die: still swinging, but -6 to every
  roll and no recovery until the fight ends -- fresh enemies carve a spent
  fighter apart. Entering a room with less STA than the fight will cost is
  walking into a grave -- warn the player plainly ("Kael has 2 good swings in
  him; the vault holds 4 skeletons") and recommend a rest or a retreat. The
  choice stays theirs.
- **Player decisions -- suggest, never decide:** drinking a potion (`use`),
  the Heal ability (`heal`), taking a short rest (`rest`), making camp
  (`camp`), buying (`buy`), which site to run, whether to press on or pull
  back. Recommend a move when it's smart ("Veld is at 2 HP -- drink the
  healing potion?"), then wait for the player's call.
- **DM decisions:** quest rewards on a site clear (`quest 15 55 ...` for the
  hideout, `quest 45 165 ...` for the barrow) and general pacing -- but pacing
  choices that spend player resources (rests, camping) belong to the player.
- **The two sites are SET encounters** -- balanced during development, never
  improvised at the table. Run them room-by-room with `hideout ROOM` and
  `barrow ROOM` (1-3 each; fixed foe counts/rosters). `fight N
  [--type skeleton|bandit]` is only for off-script scenes the story invents
  (a road ambush), not for the sites.

## Narration style

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
  swinging, but -6 to ALL rolls and NO recovery until the fight ends -- fresh
  enemies carve a spent fighter apart.** (Two spent sides cancel out and
  brawl to a finish, so fights still resolve.) STA is a second HP bar:
  whichever track empties first in a fight kills you.
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
- Sites: bandit hideout = the STARTER (15 XP/encounter, 15 g + 55 XP quest;
  first clear = level 2); skeleton barrow = TOUGH, pays 3x (45/encounter,
  45 g + 165 XP) -- train up first (rank 2+ strongly recommended; a fresh
  party wipes there ~3 times in 4).
