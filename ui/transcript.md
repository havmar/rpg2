## turn 1 (day 1)

> start a new game

You are Edwin, twenty-four, born in Mortellaria and still working in it. You throw fire. You did not learn it at the Academy. You carry a wooden staff and twenty-two gold, and you have been taking paid fighting work long enough that villages send for you by name.

Brand walks with you and has for years. He is thirty-six, wears expensive clothes, talks a great deal, and expects the worst of every day. He fights with a dagger and he is quick with it.

Years ago you signed a contract with Hell. Wealth and power were promised. So far nothing has been asked of you.

You are in Solavela, a village of vineyards and olive terraces in southern Mortellaria. Wine carts stand outside the press house. The heat is hard today and people are keeping to the shade.

Garrick is waiting for you in the square. He is thirty-one and he hunts mages for the bishop. Renegade wizards have taken the tollhouse on the road and they rob everyone who uses it, with fire and with ice. He wants them dead. He also wants their rings brought back: the bishop pays on the rings, not on Garrick's word, and Garrick says so plainly.

```
  job: Renegade Wizards [q01] -- L2
  giver: Garrick, the bishop's mage
    hunter
  pay: 36g, 132 XP. due day 4.
  proof: the wizards' rings
```

A rider from the Tergal border came through the square this morning. The Golden Empire has crossed into Tergal with machines. Varga, the high chief, is calling for fighters at Kyiv, far to the north.

```
  WORD OF THE WAR: [w1] L2 Machines
    at the Border -- raised at Kyiv.
```

```
  options: take the wizards job,
    the other job here (L3,
    deserters), spend Edwin's
    skill point, the vine inn,
    hunt, travel
```

What do you do?

[party](https://github.com/havmar/rpg2/blob/claude/new-game-gugilu/ui/party.txt) | [map](https://github.com/havmar/rpg2/blob/claude/new-game-gugilu/ui/map.txt)

---

## turn 2 (day 1)

> take the wizards job

Garrick shakes on it and tells you where the tollhouse is. The road runs west out of the village between the vine rows. The tollhouse is a burnt shell with a walled yard behind it, and only one of the wizards is still in the yard when you get there.

```
=== Renegade Wizards ===
the tollhouse road (L2),
room 1/1: ruined yard
Hexer 1 -- dagger
DEX 4  STR 2  STA 6  HP 10/10
takes spoils, leaves the fallen,
caster: ice 2; 8 Power
```

[the full fight, round by round](https://github.com/havmar/rpg2/blob/claude/new-game-gugilu/ui/fight-short.txt)

Your first fire bolt catches him across the yard and burns him badly. He throws ice twice and your ward turns it both times. You are winded by the second round; the second bolt drops him before Brand gets close enough to use the dagger.

```
The party catches its breath (+1 STA)
Edwin +53 XP (encounter) [53/200]
Brand +53 XP (encounter) [53/200]
Left among the dead:
a dagger (+0 atk/-1 sev, 2g).

*** THE JOB IS DONE: Renegade Wizards
-- the tollhouse road. ***
Edwin +53 XP (the work done) [106/200]
Brand +53 XP (the work done) [106/200]

-- the party --
Edwin: Unhurt STA 4/5 Power 4/6
  (healing x1, stamina x1)
Brand: Unhurt STA 8/8 Power 6/6
  (healing x1, stamina x1)
Purse 22g; day 1.
```

You take the ring off his hand. His dagger is no better than the one Brand already carries. The tollhouse road is open, and it is still early enough to walk back into Solavela with the ring.

Garrick turns it over once in the square and pays you on the spot, out of a purse he keeps under his coat.

```
*** QUEST COMPLETE: Renegade Wizards
-- paid in full. Reward: 41 gold. ***
Edwin talks the pay up: +8g (CHA 5
  -- 49g in all).
The party purse holds 71 gold.
Edwin gains 30 XP (quest) [136/200]
Brand gains 30 XP (quest) [136/200]
Brand: satisfaction 7 -> 8/10 (a job
  paid out)
(turned in QUICK -- day 1 against a
  deadline of day 4: x1.15)
```

The wizards are dead and the road is in use again. Two wine carts go out through the tollhouse yard before dark. Brand counts the gold twice and says at some length that it will not last.

```
  options: the deserters job
    (L3, Ulric), the smith
    (quality steel, 60g),
    Edwin's skill point, the
    vine inn (1g/head), hunt,
    travel
```

Where to?

[party](https://github.com/havmar/rpg2/blob/claude/new-game-gugilu/ui/party.txt) | [map](https://github.com/havmar/rpg2/blob/claude/new-game-gugilu/ui/map.txt) | [history](https://github.com/havmar/rpg2/blob/claude/new-game-gugilu/ui/history.txt)

---

## turn 3 (day 1)

> buy a good weapon for brand, take the deserter job

The smith's shed has one piece of quality steel in it. Brand takes the rapier, sixty gold, and sets the dagger aside. He is quick and not strong, and the rapier is the right weapon for that.

Ulric, the army captain, is at the well and has been waiting for somebody to ask. Soldiers who used to garrison these villages walked off the muster and are robbing them now. He knows where they sleep: a burned farm out in the countryside, an hour's walk from the square. He wants it stopped and he does not want prisoners.

```
  job: Deserter Raiders [q11] -- L3
  giver: Ulric, the army captain
  pay: 54g, 176 XP. due day 4.
```

You walk out while the heat is still on the fields. Three of them are standing watch in the outer yard.

```
=== Deserter Raiders ===
the burned farm (L3),
room 1/1: outer watch
3x Deserter -- spear
DEX 5  STR 4  STA 6  HP 10/10
takes spoils, leaves the fallen
```

[the full fight, round by round](https://github.com/havmar/rpg2/blob/claude/new-game-gugilu/ui/fight-short.txt)

Your first bolt goes wide and all three come in at once. Brand kills one of them and takes a spear through the right arm doing it. He kills the second in the seventh round; the third puts a spear into his chest before you can turn, and he goes down and does not get up. You are out of Power and nearly out of breath by then. The last deserter breaks and runs into the vines.

```
The party catches its breath (+1 STA)
Edwin +70 XP (encounter) [206/200]
*** Edwin reaches level 3!
(4 skill points unspent) ***
Loot: 5 gold (purse 16g).
Left among the dead:
2x spear (+0 atk/+0 sev, 5g).
(LOOSE END le1: Deserter 4 got away --
  `pursue` while the trail is warm:
  today, here, before a night's sleep)

*** THE JOB IS DONE (driven off, not
  slain):
Deserter Raiders -- the burned farm. ***
Edwin +71 XP (the work done) [77/300]
Brand's rapier
is taken up from where they fell
(`give HERO rapier`).
Brand's potions are taken up
from where they fell (2 vial(s)).
The party shares out its potions:
Edwin: 2 healing, 1 stamina.

-- the party --
Edwin: Unhurt STA 1/5 Power 0/6
  (Winded -2 to rolls)
  (healing x2, stamina x1)
Purse 16g; day 1.
```

Brand is dead in the yard of the burned farm, an hour after he bought the rapier. You take the rapier and his vials and leave the spears. The raiding is over either way; the man who ran is out in the vines somewhere, hurt, and the trail stays warm until you sleep.

You are alone now. Fate's bargain buys your life with a companion's, and there is no companion.

The day's work also put you at level 3.

```
Edwin -- L3, 4 point(s) banked, XP
77/300 to L4
(* = buyable now; costs in points)
POOLS -- train Edwin hp|sta|power
* +1 max HP/STA/Power (cap +10)    1 ea
    bought hp +0, sta +0, power +0
TRAINING -- train Edwin combat
* combat rank 1 -> 2                  4
    +1 to every pressure roll (cap 5)
SPELLS -- train Edwin SPELL
* fire rank 1 -> 2                    2
    next: +1 bolt pressure & severity
      (the rank bonus)
  (new spells: a spellbook teaches one
    -- 120g in a capital, buy Edwin book
    SPELL)
WEAPON -- train Edwin weapon
* wooden staff rank 0 -> 1            1
    +1 atk & sev; drops on switch
ALCHEMY -- train Edwin alchemy
* alchemy rank 0 -> 1                 2
    brew 1/night, stock 3; +healing
      potion, stamina draught
MOVES -- train Edwin move NAME (0/2
  known)
* pommel                              1
    softer hit stuns an unhurt foe
* disarm                              1
    a decisive hit flings the weapon
* kick                                1
    on a hit: foe defends -2 next round
* trip                                1
    a decisive hit trips the foe a round
* riposte                             1
    +2 attack the round after your parry
ABILITIES -- learn Edwin NAME
* bulwark                             3
    2 Power softens a deadly hit a tier
* first_blood                         2
    2 Power: a free graze before rd 1
* war_breath                          2
    at a pause: 2 Power -> +3 STA
* berserk                             1
    2 HP -> +4 STA; wounds bite deeper
* rage                                2
    +2 atk after a kill (a miss stalls)
* field_medic                         3
    1/day DEX check: death becomes Down
* storyteller                         2
    camp tale: party +1 Power for a day
* survivalist                         2
    MIND check: camp rests as a tavern
* arrow_parry                         2
    +2 defense vs arrows (melee grip)
* point_blank                         3
    ranged card keeps firing at contact
* rapid_reload                        3
    fire every round on a reload-1 card
```

```
  options: spend the 4 points,
    pursue the runner (today
    only), turn in at Solavela
    (62g, Ulric), recruit at
    Solavela, camp
```

Where to?

[party](https://github.com/havmar/rpg2/blob/claude/new-game-gugilu/ui/party.txt) | [map](https://github.com/havmar/rpg2/blob/claude/new-game-gugilu/ui/map.txt) | [history](https://github.com/havmar/rpg2/blob/claude/new-game-gugilu/ui/history.txt)
