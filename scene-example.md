# Scene page example

A reference model, not live game state: two turns in writing.md's voice and
dm.md's scene-page format -- a game start, then the fight turn that follows
it. `ui/scene.md` holds ONE turn, rewritten whole every message, so the two
sections below the rule are two successive states of the page, not one page:
the first is the whole file after turn 1, the second replaces it after turn 2.
The engine lines are illustrative, not exact script output; their formats
follow `ui/fight-short.txt`. Displays sit in code fences at their printed
40-column shape; prose is plain paragraphs, never hard-wrapped, with no
markdown beyond structure. Swap `<branch>` for the current branch in the
links.

Each turn's chat message is that turn's own text copied back verbatim --
everything between the `>` line and the footer -- with the party page's link
(`ui/party.txt`) on a final line under it: the chat already holds the turn,
so the one link it gets is to the board it does not hold.

---

## turn 1 (day 1)

> new game

You are Corvin: a Byzantine, 35, a long way from anywhere that knows the name. You can throw fire; nobody taught you how. Your coat is worn through at the elbows and your purse is nearly empty. Years ago you signed a contract with Hell -- wealth and power, terms pending. So far the terms are still pending.

Isolde walks beside you: a woman out of Phyrascia, once a scholar. She throws ice when she is angry. She has watched your back for years.

You are in Ventoro, a village of Byzantium, on R12C11 -- vine country under the hills. Mud streets, one well. The morning market is setting up around a dry fountain.

Rosa the well-keeper stops you there. The rope is cut, the bucket is gone, and something knocks in the shaft at night. The village wants its well back. She wants the thing dead.

```
  job: The Thing in the Well -- L1
  giver: Rosa, well-keeper
  pay: 18s. due day 6.
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

[party](https://github.com/havmar/rpg2/blob/<branch>/ui/party.txt) | [map](https://github.com/havmar/rpg2/blob/<branch>/ui/map.txt)

---

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

Corvin's fire kills the first rat on the cistern rim. The second bites Isolde's forearm before her rime bolt kills it.

```
The party catches its breath (+1 STA)
Corvin +35 XP (encounter) [35/100]
Isolde +35 XP (encounter) [35/100]

*** QUEST COMPLETE:
The Thing in the Well.
Reward: 18 silver. ***
Corvin talks the pay up:
+2s (20s in all).
The party purse holds 20 silver.
Corvin +53 XP (quest) [88/100]
Isolde +53 XP (quest) [88/100]
Isolde: satisfaction 7 -> 8/10
(a job paid out)

-- the party --
Corvin: Unhurt STA 4/6 Power 5/5
 (healing x1)
Isolde: Scratched STA 4/6 Power 5/5
 - a bitten forearm, torn (sev 1)
 (HP ceiling 7/8 until it mends)
Purse 20s; day 1.
```

Rosa counts the coin out at the well head. "Cheap at twice that," she says, and looks down the shaft once before she pays. By evening the winch has a new rope and the well is back in use.

Isolde binds her arm herself. "An ordinary rat," she says. "Disappointing."

```
  options: the board (1 more job),
    the letter from below, tavern
    (1s/head), camp, travel
```

Where to?

[party](https://github.com/havmar/rpg2/blob/<branch>/ui/party.txt) | [map](https://github.com/havmar/rpg2/blob/<branch>/ui/map.txt)
