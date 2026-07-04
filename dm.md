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

- Resolve **at most one encounter** (`fight` / `hideout`) per DM message, then
  stop and hand the turn back to the player. Never chain fights, even if the
  next room seems obvious.
- **Player decisions -- suggest, never decide:** drinking a potion (`use`),
  the Heal ability (`heal`), taking a short rest (`rest`), making camp
  (`camp`), buying (`buy`), which site to run, whether to press on or pull
  back. Recommend a move when it's smart ("Veld is at 2 HP -- drink the
  healing potion?"), then wait for the player's call.
- **DM decisions:** foe counts that fit the scene (`DUNGEON_ROOMS = [2, 2, 3]`
  is the reference for what barrow rooms look like; session play isn't bound
  to it), quest rewards on a site clear (`quest 15 55 ...` for the barrow,
  `quest 45 165 ...` for the hideout), and general pacing -- but pacing
  choices that spend player resources (rests, camping) belong to the player.

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

- Attacks cost STA (humans 2, skeletons 1); defense is free. At 0 STA a
  fighter guards instead of attacking and recovers 1 STA (swings every other
  round). Winded at STA <= 3: -2 to all rolls.
- Recovery sawtooth: fight end +1 STA; short rest +3 STA / +1 HP (2 slots per
  day); long rest (camp) = full STA, ~1/7 max HP, day advances, slots refill.
  Nothing forces the day to end -- camping is the player's call.
- Skeletons are undead: wound roll penalty halved (a graze doesn't slow
  them), so the death spiral and First Blood bite less at the barrow.
- 0 HP = Down (out of the fight, back up at 1 HP next fight); death only on
  an unsaved killing blow. Total party knockout = the Down are finished off.
- Sites: skeleton barrow = farmable (15 XP/encounter, 15 g + 55 XP quest);
  bandit hideout = tough, pays 3x -- train up first (rank 1+ recommended).
