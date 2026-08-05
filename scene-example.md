# Scene page example

A reference model, not live game state: two turns in writing.md's voice and
dm.md's scene-page format -- a game start, then the fight turn that follows
it. Below the rule is exactly what `ui/scene.md` would show after turn 2 of a
real game (the page keeps the last three turns, oldest first). The engine
lines are illustrative, not exact script output; their formats follow
`ui/fight-short.txt`. Displays sit in code fences at their printed 40-column
shape; prose is plain paragraphs, never hard-wrapped, with no markdown beyond
structure. Swap `<branch>` for the current branch in the links.

---

## turn 1 (day 1)

> new game

You are Delg: a dwarf, 35, an alchemist a long way from the mountain. Your coat is out at the elbows and your chest is bad without its medicine. Years ago you signed a contract with Hell -- wealth and power, terms pending. So far the terms are still pending.

Isolde walks beside you: human, a scholar thrown out of somewhere, ice at her fingertips when she is angry. She has watched your back for years.

You are in Ventoro, a village of Mortellaria. Mud streets, vine country, one well. The morning market is setting up around a dry fountain.

Rosa the well-keeper stops you there. The rope is cut, the bucket is gone, and something knocks in the shaft at night. The village wants its well back. She wants the thing dead.

```
  job: The Thing in the Well -- L1
  giver: Rosa, well-keeper (blunt)
  pay: 18g. due day 6.
```

A letter finds you at the fountain. Black wax, no courier in sight. Work from below.

```
  WORD FROM BELOW: Sell the Powder
    at Ventoro -- take it by day 10.
```

```
  options: take the well job, the
    board (1 more job), the letter,
    hunt, travel
```

What do you do?

## turn 2 (day 1)

> take the well job and go down after it

Rosa spits on her palm and shakes on it. The winch lowers you into the shaft; Isolde takes the rungs behind you. Below the waterline the well opens on an old cellar, dry, smelling of vinegar. The knocking has stopped. Something heard you coming.

```
=== The Thing in the Well ===
the old cellar (L1), room 1/1:
  the broken cistern
2x Grave Rat -- fangs
DEX 4  STR 2  STA 8  HP 4/4
breaks when beaten
```

[the full fight, round by round](https://github.com/havmar/rpg2/blob/<branch>/ui/fight-short.txt)

Delg opens the first rat's skull on the cistern rim. The second gets its teeth into Isolde's forearm before her rime bolt cracks it dead. Short and ugly, the way well work is.

```
The party catches its breath (+1 STA)
Delg +35 XP (encounter) [35/100]
Isolde +35 XP (encounter) [35/100]

*** QUEST COMPLETE:
The Thing in the Well.
Reward: 18 gold. ***
Delg talks the pay up:
+2g (20g in all).
The party purse holds 20 gold.
Delg +53 XP (quest) [88/100]
Isolde +53 XP (quest) [88/100]
Isolde: satisfaction 7 -> 8/10
(a job paid out)
EPILOGUE (day 1): The well is
 cleared. Ventoro draws water again
 by evening.

-- the party --
Delg: Unhurt STA 4/6 Power 5/5
 (healing x1)
Isolde: Scratched STA 4/6 Power 5/5
 - a bitten forearm, torn (sev 1)
 (HP ceiling 7/8 until it mends)
Purse 20g; day 1.
```

Rosa counts the coin out at the well head. "Cheap at twice that," she says, and looks down the shaft once before she pays.

Isolde binds her arm herself. "An ordinary rat," she says. "Disappointing."

```
  options: the board (1 more job),
    the letter from below, tavern
    (1g/head), camp, travel
```

Where to?

[party](https://github.com/havmar/rpg2/blob/<branch>/ui/party.txt) | [map](https://github.com/havmar/rpg2/blob/<branch>/ui/map.txt)
