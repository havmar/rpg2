"""The quest & encounter generator -- structured combat content, worldgen.

sites.py holds the CATALOG (foe rows, the two hand-built anchor sites); this
file turns that catalog into a WORLD of areas and quests. Geography is a
persistent Land -> Area -> Site -> Room tree; quests point at world-owned
sites instead of carrying disposable geography inside themselves. Every
roster is still assembled from the bestiary by its bench-calibrated level
annotations. The design (2026-07):

- **The level IS the pay grade.** A quest's board level sets its rewards
  through rpg.py's site_* formulas; quest levels are rolled RANDOMLY within
  a settlement band and displayed straight, so under- and over-leveled work
  both show up -- reading the board is the decision, and punching up pays
  above your weight class by construction.
- **The threat math is deliberately dumb and sim-verified.** One catalog
  level ~ x1.5 threat (THREAT_BASE); a row member is worth
  THREAT_BASE**level / ref_pack units; a site's whole roster is ~2 reference
  encounters' worth spread over its rooms in rising shares -- the rule the
  two hand-built sites turned out to already follow (hideout 5 bandits vs a
  budget of ~6; barrow 10 skeletons vs ~9). bench_quests.py measures what
  the rule actually produces; anything cleverer must earn its way in there.
- **Reskinning: display name is fiction, the stat row is mechanics.** Five
  races share one calibrated catalog; a goblin scrap-hound is the wolf row
  (make_foe's `display`). Balance never forks on a skin.
- **The world is generated ONCE, seeded, at game start** (session.py `new`)
  and lives in the save file: permanent and learnable for that playthrough,
  different every playthrough. Worldgen seeds ONE job per settlement and
  stops there. Since 2026-07-26 (the attrition rework's slice 2) the board
  is a LIVE INVENTORY, not a fixed census: every posting carries a clock
  (`posted_day` / `deadline_day`), untaken work expires off the board, and
  each settlement refills toward its slot count as the days pass
  (`refresh_settlement_board`). The old up-front XP-coverage top-up and its
  assert are gone -- they asserted a total that expiry makes meaningless.

Local quests are FORMULAIC ON PURPOSE (placeholders, not authored content):
a stereotype of the settlement's race x a themed foe pool. The authored
questline layer lives in story.py (the conquest, 2026-07-12); since the
same date every quest also carries a GIVER (the face behind the job) and
an EPILOGUE, and each land a small persistent cast -- see rules.md's
Story Layer add-on.

Run:  python quests.py [--seed N]     # print a generated world's board
      python quests.py --demo         # also dump one quest's full rosters
"""

from __future__ import annotations

import argparse
import dataclasses
import random
import re
from typing import Iterable

from rpg import (LEVEL_CAP, xp_to_next, quest_xp_total, quest_encounter_xp,
                 quest_gold, conspicuousness, NOTICE_BASE, CAST_RANGE)
from sites import FOES, Site
from places import (
    LAND_SPECS, SITE_TEMPLATES, create_geography, generic_room_contents,
    materialize_settlement, stable_seed, land_race, add_state, replace_state,
)
import worldsim                  # the world layer (2026-08-09, the economy
                                 # floor): the board asks it how big it is,
                                 # what it pays, and what the cards standing
                                 # over the land are putting up. worldsim
                                 # imports places and sites only, so this is
                                 # one-directional

# --------------------------------------------------------------------------- #
# The threat math (the encounter builder's whole theory)
# --------------------------------------------------------------------------- #

THREAT_BASE = 1.5   # one catalog level ~ x1.5 threat: calibrated on the
                    # barrow (4 skeletons ~ one level over 3) and checked by
                    # bench_quests.py across the whole 1-20 line
ROOM_SHARES = {     # a QUEST's roster budget as ~2 at-level reference
                    # encounters, split over its encounters in rising shares
                    # -- the hand-built sites' observed shape. Since
                    # 2026-07-26 the key is the quest's ENCOUNTER count and
                    # the shares are consumed in QUEST order (a two-place job
                    # does not restart the escalation at the second place):
                    # one quest, one rising curve, ending at the destination.
                    # The values are unchanged -- they were calibrated as a
                    # unit and the bench reads them that way.
    1: (1.25,),     # a one-encounter quest is one HARD fight for full pay
    2: (0.85, 1.10),
    3: (0.55, 0.70, 0.85),
}
QUEST_ENCOUNTERS = ((1, 2, 3), (55, 30, 15))    # how many fights a job is:
                    # 1 by default, 2 for a middling job, 3 at most (mean
                    # 1.6). Before 2026-07-26 sites rolled 1/2/3 and then
                    # rooms rolled 1/2/3 PER SITE, centring quests on 3.74
                    # encounters with a tail to nine -- the generator's
                    # difficulty dial was quest LENGTH, and length is exactly
                    # what the attrition rework has to stop spending.
                    # (Deliberately still a roll: making the narrative
                    # content decide a job's length is its own queued pass,
                    # see plan.md.)
BOSS_ALLOWANCE = 1.35   # the FINAL room's anchor may exceed its budget by
                        # this factor: the level-5 ogre quest ends with the
                        # ogre, not with the biggest thing that fit
DUP_COST = 2.0          # crowding surcharge: a room's members are priced by
                        # PACK-EQUIVALENTS consumed -- each body adds
                        # 1/ref_pack of a pack, and a body bought while N
                        # whole packs already stand costs DUP_COST**N its
                        # base value. One reference pack is priced exactly;
                        # the 4th skeleton costs extra.
PACK_CAP = 1.4          # ...and a room never exceeds this many
                        # pack-equivalents NO MATTER the pricing: a
                        # reference pack plus a shade is all the bestiary
                        # bench ever validated, and bench_quests measured
                        # every deeper roster (4 blademasters, 3 wyverns)
                        # as many levels hotter than any unit algebra says.
                        # Solo-boss rows (ref_pack 1) are stricter still:
                        # calibrated as ALONE fights (their fairness against
                        # a duo IS the action economy), they never stack and
                        # never take or join an escort.
ROOM_MAX_BODIES = 6     # hard roster cap per room (log readability; the
                        # press makes bodies past this mostly circle anyway).
                        # The EFFECTIVE cap is anchor ref_pack + 2: action
                        # economy against a duo means a solo-boss room takes
                        # at most a couple of adds, while pack rows still
                        # swarm (bench_quests: 6-body elite rooms read ~15
                        # levels hot however they're priced).
FILLER_LEVEL_REACH = 4  # fillers must be within this many levels of the
                        # room's anchor (no dragons herding rats -- and at
                        # the top band even mid rows stay dangerous chaff)

# --------------------------------------------------------------------------- #
# Quest clocks & the banded refill (2026-07-26, the attrition rework's slice 2)
# --------------------------------------------------------------------------- #
# A job is a job SOMEONE NEEDS DONE, and needs done by a date. Every posting
# carries a window; the turn-in is paid in bands by when it lands. This is
# what makes a DAY cost something without ever pricing a bed: time and
# geography do not inflate, so a window is worth exactly as much at level 20
# as at level 1 (plan.md's spine -- do not make rest expensive, make rest
# incomplete).
#
# The board is a live inventory as a direct consequence: once work expires,
# a world posted up front against an XP-coverage target runs dry, so each
# settlement keeps its own slots full instead (SETTLEMENT_KINDS' first
# number). karma.roll_dark_quest is the shape this copies -- rolled lazily,
# never seen by worldgen, invisible to the benches until they ask for it.

QUEST_WINDOW_DAYS = (3, 7)   # the posting window, rolled per quest
QUEST_QUICK_SHARE = 1 / 3    # done within this fraction of the window: QUICK
QUEST_GRACE_DAYS = 3         # ...and this long past the deadline is LATE,
                             # still payable; past it the job is gone
QUEST_PAY_BANDS = {          # what the turn-in lump (and the gold) is worth
    "quick": 1.15,           # by the day it lands. The premium is small on
    "on time": 1.00,         # purpose: the clock is a pressure, not a
    "late": 0.60,            # second economy. A late job still pays --
    "expired": 0.0,          # walking away with nothing is the failure state
}
QUEST_REFILL_PER_DAY = 1     # new jobs a settlement posts per day once its
                             # board has been seen; a board seen for the FIRST
                             # time fills to its slot count (the land always
                             # has work, plan.md)


def threat_value(kind: str) -> float:
    """One member of this row, in threat units: a whole reference encounter
    at level L is worth THREAT_BASE**L regardless of how many bodies it is."""
    spec = FOES[kind]
    return THREAT_BASE ** spec.level / spec.ref_pack


def room_budget(level: int, share: float) -> float:
    return share * THREAT_BASE ** level


def build_room(budget: float, pool: tuple[str, ...], rng: random.Random,
               final: bool = False) -> list[str]:
    """Fill one room's roster from the pool against a threat budget.

    Anchor first: the biggest row that fits (the final room may overshoot by
    BOSS_ALLOWANCE -- the boss rule), then fill the remainder, preferring
    more of the anchor (homogeneous packs read best) with a chance of mixed
    lower fillers. A pool whose weakest row is over budget yields one weakest
    member: the room undershoots rather than empties."""
    allowance = BOSS_ALLOWANCE if final else 1.0
    fitting = [k for k in pool if threat_value(k) <= budget * allowance]
    if not fitting:
        return [min(pool, key=threat_value)]
    # Anchor: one of the two biggest fitting rows (variety without losing
    # the room's intended weight class).
    fitting.sort(key=threat_value, reverse=True)
    anchor = rng.choice(fitting[:2])
    if FOES[anchor].ref_pack == 1:
        return [anchor]     # solo bosses fight ALONE (see PACK_CAP)
    room = [anchor]
    packs = 1 / FOES[anchor].ref_pack   # pack-equivalents standing so far

    def next_cost(kind: str) -> float:
        # The crowding surcharge (see DUP_COST): base value, doubled per
        # whole pack already in the room.
        return threat_value(kind) * DUP_COST ** int(packs)

    spent = threat_value(anchor)
    anchor_level = FOES[anchor].level
    body_cap = min(ROOM_MAX_BODIES, FOES[anchor].ref_pack + 2)
    while len(room) < body_cap:
        remaining = budget - spent
        options = [k for k in pool
                   if FOES[k].ref_pack > 1
                   and packs + 1 / FOES[k].ref_pack <= PACK_CAP
                   and next_cost(k) <= remaining
                   and FOES[k].level >= anchor_level - FILLER_LEVEL_REACH]
        if not options:
            break
        if anchor in options and rng.random() < 0.75:
            pick = anchor
        else:
            pick = rng.choice(options)
        room.append(pick)
        spent += next_cost(pick)
        packs += 1 / FOES[pick].ref_pack
    # Biggest last: the roster line reads as an escalation ("2x Skeleton,
    # the Wight") and the focus-fire AI thins the chaff first anyway.
    room.sort(key=threat_value)
    return room


# Generic stages remain the bench/low-level fallback. Runtime quest Sites pass
# concrete roles from their place template.
ROOM_STAGES = ("the approach", "the way in", "the outer chamber",
               "the inner chamber", "the heart of it")


def build_site_rooms(level: int, n_rooms: int, pool: tuple[str, ...],
                     rng: random.Random,
                     room_roles: tuple[str, ...] | None = None,
                     shares: tuple[float, ...] | None = None,
                     final_room: bool = True
                     ) -> list[tuple[str, list[str]]]:
    """1-3 rooms escalating to the site's level: rising budget shares of the
    ~2-reference-encounter total, the last room carrying the anchor.

    `shares` overrides the ROOM_SHARES lookup -- a quest spanning two places
    passes THIS place's slice of the quest's one rising curve (build_quest).
    `final_room=False` says the anchor is still ahead (an earlier place of a
    multi-place job), so no room here gets the boss allowance."""
    if shares is None:
        shares = ROOM_SHARES[n_rooms]
    rooms = []
    for i, share in enumerate(shares):
        final = final_room and i == len(shares) - 1
        if room_roles:
            name = room_roles[min(i, len(room_roles) - 1)]
        else:
            name = ROOM_STAGES[-1] if final else ROOM_STAGES[i]
        rooms.append((name, build_room(room_budget(level, share), pool, rng,
                                       final=final)))
    return rooms


# --------------------------------------------------------------------------- #
# Quest templates -- the formulaic local-quest tables
# --------------------------------------------------------------------------- #
# One entry = a race stereotype x a themed foe pool (+ optional reskins:
# kind -> display name). A template's usable level range derives from its
# pool (template_band), so the wolf quest never rolls at level 18 and the
# drake never at level 2. `sites` are name stems for the quest's sites, and
# `places` (2026-07-26; default 1, and only the first `places` stems are
# used) says how many of them a job actually spans. It is 2 only where the
# FICTION genuinely moves between two places -- the high pasture where the
# wolves killed and the den in the hills you track them to. "the village
# graveyard" and "the crypt below" are one place; so is a mine and the
# chamber at the end of it. Place count is not a difficulty dial: the fights
# are QUEST_ENCOUNTERS' job.
# Since 2026-07-12 each template also carries `giver` (the ROLE of the
# person behind the job -- worldgen puts a generated face on it, see
# attach_giver; in play there is no board, quests come from these people)
# and `epilogue` (one authored line of aftermath, delivered at turn-in).

BANDIT_POOL = ("cutthroat", "archer", "bruiser")
LADDER_POOL = BANDIT_POOL + ("soldier", "veteran", "champion",
                             "blademaster", "warlord")
# Cultural arms (ranged combat, 2026-07-16) -- NPC-side constraints, per
# the designer: ELVES always shoot bows (the ladder's archer, plus their
# own hunter row), GOBLINS never do (slings instead), DWARVES shoot powder
# (the gunner's hand bombard). Enforced where rosters are drawn: each
# race's warband templates use its own ladder variant; wild_pool inherits
# them, so a land's roads shoot culturally too. Humans and orcs field the
# plain ladder (bows are everyone else's normal).
GOBLIN_LADDER_POOL = tuple(k for k in LADDER_POOL
                           if k != "archer") + ("slinger",)
DWARF_LADDER_POOL = tuple(k for k in LADDER_POOL
                          if k != "archer") + ("gunner",)
ELF_LADDER_POOL = LADDER_POOL + ("hunter",)
# The casters get their OWN quests (2026-07-14; the Magic & Mind layer
# kept the containment): one
# caster template per race below plus the magus epic -- NOT the ladder
# pool. The first cut seeded hexer/pyromancer into LADDER_POOL and the
# career sim collapsed (L11 47% -> 18%, capped 7.5% -> 3.5%): individually
# band-fair rows, but at 50-77% of all warband rooms their ranged chip
# bled the duo across chained rooms (rooms measured fine at level; SITES
# dropped 15-25 points mid-band). Contained instead: caster danger is
# identifiable content the board names, not an ambient tax on every
# warband.
CASTER_POOL = ("hexer", "pyromancer")
MAGUS_POOL = CASTER_POOL + ("magus",)
WOLF_POOL = ("wolf", "dire wolf")
BEAST_POOL = ("boar", "bear")
UNDEAD_POOL = ("skeleton", "ghoul", "wight")
GIANTKIN_POOL = ("ogre", "troll", "giant")
SPIDER_POOL = ("great spider",)
DRAKE_POOL = ("wyvern", "drake", "dragon")

TEMPLATES: dict[str, list[dict]] = {
    "human": [
        dict(title="Bandits on the Road",
             desc="Bandits are attacking travelers on the king's road. Find "
                  "their camp and kill them. The sheriff will pay you.",
             pool=LADDER_POOL, skins={},
             sites=("the roadside camp", "the toll bridge", "the old fort"),
             giver="the sheriff",
             epilogue="The bandits are dead. The road and bridge are safe "
                      "again.",
             failure_epilogue="The bandits are still on the road. Two carters "
                              "are dead and the toll bridge is theirs now."),
        dict(title="Wolves Attack",
             desc="Wolves have killed sheep and a shepherd. Hunt the pack in "
                  "the hills and kill it.",
             pool=WOLF_POOL, skins={}, places=2,
             sites=("the high pasture", "the den in the hills"),
             giver="the head shepherd",
             epilogue="The wolves are dead. No sheep are lost for the rest of "
                      "the season.",
             failure_epilogue="The pack moved down into the valley. Another "
                              "shepherd is dead and the flocks are penned in."),
        dict(title="The Restless Crypt",
             desc="The dead rise from the village graveyard. Enter the crypt "
                  "and destroy them.",
             pool=UNDEAD_POOL, skins={},
             sites=("the village graveyard", "the crypt below"),
             giver="the village priest",
             epilogue="The dead are destroyed. The priest blesses the graves "
                      "again.",
             failure_epilogue="The dead walk out of the graveyard now. The "
                              "priest has locked the church and the village "
                              "sleeps armed."),
        dict(title="Deserter Raiders",
             desc="Army deserters are raiding the villages they once guarded. "
                  "Find their camp and stop them.",
             pool=LADDER_POOL, skins={"soldier": "Deserter",
                                      "veteran": "Deserter Sergeant"},
             sites=("the burned farm", "the deserters' camp"),
             giver="the army captain",
             epilogue="The deserters are defeated. Their weapons return to "
                      "the army.",
             failure_epilogue="The deserters burned another village and rode "
                              "east. The army hunts its own men now."),
        dict(title="Renegade Wizards",
             desc="Renegade wizards have taken the tollhouse. They attack "
                  "travelers with fire and ice. Kill them and clear the road.",
             pool=CASTER_POOL, skins={},
             sites=("the tollhouse road", "the ruined guildhall"),
             giver="the bishop's mage hunter",
             epilogue="The wizards are dead. Travelers use the road again.",
             failure_epilogue="The wizards hold the tollhouse. The road is "
                              "closed and traffic goes the long way round."),
    ],
    "elf": [
        dict(title="The Blighted Grove",
             desc="A curse has poisoned the grove. Wolves and spiders attack "
                  "anyone who enters. Kill them and burn the source of the "
                  "blight.",
             pool=SPIDER_POOL + WOLF_POOL,
             skins={"great spider": "Blighted Spider",
                    "wolf": "Blighted Wolf", "dire wolf": "Blighted Dire Wolf"},
             sites=("the outer grove", "the heart of the grove"),
             giver="the head warden",
             epilogue="The blight is gone. New plants grow at the edge of the "
                      "grove.",
             failure_epilogue="The blight spread past the grove. The wardens "
                              "have pulled back to the inner wood."),
        dict(title="Spiders in the Trees",
             desc="Giant spiders have covered the tree paths in webs. Several "
                  "wardens are missing. Clear the paths and find them.",
             pool=SPIDER_POOL, skins={"great spider": "Giant Tree Spider"},
             sites=("the lower branches", "the upper walkways"),
             giver="the walkway keeper",
             epilogue="The spiders are dead and the webs are gone. The "
                      "missing wardens are brought home.",
             failure_epilogue="The webs reached the main walkways. The "
                              "missing wardens are not coming back."),
        dict(title="Blighted Beasts",
             desc="The blight has driven the boars and bears mad. They are "
                  "attacking the outer groves. Kill them.",
             pool=BEAST_POOL, skins={"boar": "Blighted Boar",
                                     "bear": "Blighted Bear"},
             sites=("the torn grove", "the beast den"),
             giver="the grove keeper",
             epilogue="The beasts are dead. The groves are safe again.",
             failure_epilogue="The mad beasts came out of the groves and into "
                              "the orchards. The outer paths are closed."),
        dict(title="Rogue Wardens",
             desc="A group of wardens has taken over the forest road. They "
                  "demand money from travelers. Stop them.",
             pool=ELF_LADDER_POOL,
             skins={"archer": "Rogue Warden", "cutthroat": "Rogue Scout",
                    "soldier": "Rogue Warden", "veteran": "Warden Captain",
                    "champion": "Forest Champion",
                    "hunter": "Rogue Hunter"},
             sites=("the forest road", "the rogue lodge"),
             giver="the council judge",
             epilogue="The rogue wardens are defeated. The forest road is "
                      "open again.",
             failure_epilogue="The rogue wardens hold the forest road and set "
                              "their own price. The council pays it."),
        dict(title="The Mist Coven",
             desc="A group of mages stole forbidden songs from the circle. "
                  "Their magic covers the valley in mist. Find them and stop "
                  "the ritual.",
             pool=CASTER_POOL,
             skins={"hexer": "Mist Mage", "pyromancer": "Fire Mage"},
             sites=("the misty valley", "the stone circle"),
             giver="the circle elder",
             epilogue="The mages are dead. The mist fades from the valley.",
             failure_epilogue="The ritual finished. The mist lies over the "
                              "whole valley and nobody walks in it."),
    ],
    "orc": [
        dict(title="The Great Hunt",
             desc="The clan has chosen a dangerous beast for the hunt. Kill "
                  "it and bring back its hide.",
             pool=BEAST_POOL + ("dire wolf",), skins={}, places=2,
             sites=("the hunting grounds", "the beast den"),
             giver="the clan's lead hunter",
             epilogue="The hide hangs in the clan hall. The clan honors the "
                      "party.",
             failure_epilogue="The beast was not taken. The hunt is called "
                              "off and the clan eats winter stores early."),
        dict(title="Rival Warband",
             desc="A rival clan is raiding the herd trails. Find their camp "
                  "and defeat them.",
             pool=LADDER_POOL,
             skins={"cutthroat": "Orc Raider", "archer": "Orc Skirmisher",
                    "bruiser": "Orc Breaker", "soldier": "Orc Raider",
                    "veteran": "Orc Veteran", "champion": "Orc Warchief",
                    "blademaster": "Orc Swordmaster", "warlord": "Orc Overlord"},
             sites=("the raided trail", "the rival camp", "the war camp"),
             giver="the warchief",
             epilogue="The rival warband is defeated. The herd trails are "
                      "safe again.",
             failure_epilogue="The rival warband took the herd trails. The "
                              "clan drives its beasts the long way now."),
        dict(title="Giants in the Pass",
             desc="Giants have blocked the mountain pass. They attack carts "
                  "and kill travelers. Find their cave and kill them.",
             pool=GIANTKIN_POOL, skins={},
             sites=("the boulder field", "the cave under the pass"),
             giver="the pass keeper",
             epilogue="The giants are dead. Carts use the mountain pass again.",
             failure_epilogue="The giants still hold the pass. The carts turn "
                              "back and the goods rot at the road head."),
        dict(title="Dragon on the Mountain",
             desc="A dragon hunts the clan's herds from the high peaks. Climb "
                  "to its nest and kill it.",
             pool=DRAKE_POOL, skins={},
             sites=("the mountain slopes", "the dragon's nest"),
             giver="the clan elder",
             epilogue="The dragon is dead. The herds return to the mountain.",
             failure_epilogue="The dragon took the rest of the herd. The clan "
                              "moved its camp down off the mountain."),
        dict(title="Rebel Shamans",
             desc="A group of shamans has turned against the clan. They burn "
                  "the plains and attack the old shaman's followers. Defeat "
                  "them.",
             pool=CASTER_POOL,
             skins={"hexer": "Ice Shaman", "pyromancer": "Fire Shaman"},
             sites=("the burned plains", "the rebel camp"),
             giver="the clan shaman",
             epilogue="The rebels are defeated. Their ritual fire is put out.",
             failure_epilogue="The rebel shamans burned the plains black. The "
                              "old shaman has lost half the followers."),
    ],
    "dwarf": [
        dict(title="Monsters in the Deep Road",
             desc="Giant spiders and tunnel hounds have blocked the road to "
                  "another dwarf city. Clear the tunnels.",
             pool=SPIDER_POOL + WOLF_POOL,
             skins={"great spider": "Tunnel Spider", "wolf": "Tunnel Hound",
                    "dire wolf": "Tunnel Stalker"},
             sites=("the checkpoint", "the deep road", "the crossroads"),
             giver="the trade guild agent",
             epilogue="The monsters are dead. The deep road is open again.",
             failure_epilogue="The deep road stays shut. The trade guild "
                              "sends its goods over the surface at four times "
                              "the price."),
        dict(title="The Lost Hold",
             desc="An old dwarf hold has drained after years under water. "
                  "Undead now walk its halls. Destroy them.",
             pool=UNDEAD_POOL,
             skins={"skeleton": "Drowned Miner", "ghoul": "Pale Miner",
                    "wight": "Dead Lord"},
             sites=("the cracked gate", "the flooded halls",
                    "the central hall"),
             giver="the last heir of the hold",
             epilogue="The undead are destroyed. The entrance to the hold is "
                      "sealed.",
             failure_epilogue="The dead still walk the hold. The heir gave up "
                              "the claim and sold the deed."),
        dict(title="Monster in the Mine",
             desc="A giant has taken over part of the mine. Kill it and clear "
                  "the tunnels.",
             pool=GIANTKIN_POOL, skins={"ogre": "Deep Ogre",
                                        "troll": "Stone Troll"},
             sites=("the mine tunnel", "the broken chamber"),
             giver="the mine foreman",
             epilogue="The monster is dead. The miners return to work.",
             failure_epilogue="The mine stays half shut. The foreman moved "
                              "the crews to a poorer seam."),
        dict(title="The Clan War",
             desc="A rival dwarf clan has attacked the gate and mine. Defeat "
                  "them and end the attack.",
             pool=DWARF_LADDER_POOL,
             skins={"cutthroat": "Rival Scout", "gunner": "Rival Gunner",
                    "bruiser": "Rival Brute", "soldier": "Rival Soldier",
                    "veteran": "Rival Veteran", "champion": "Rival Captain",
                    "blademaster": "Rival Swordmaster"},
             places=2,
             sites=("the main gate", "the mine entrance"),
             giver="the clan elder",
             epilogue="The rival clan is defeated. The fighting ends.",
             failure_epilogue="The rival clan holds the gate and the mine "
                              "mouth. The fighting goes on without you."),
        dict(title="Mages in the Mine",
             desc="A group of mages has opened a magic fire in a sealed mine. "
                  "Kill them and put out the fire.",
             pool=CASTER_POOL,
             skins={"hexer": "Ice Mage", "pyromancer": "Fire Mage"},
             sites=("the sealed mine", "the magic vault"),
             giver="the head runesmith",
             epilogue="The mages are dead. The vault is sealed again.",
             failure_epilogue="The magic fire burned through the vault. The "
                              "seal is broken and the mine is written off."),
    ],
    "goblin": [
        dict(title="Hounds in the Factory",
             desc="The boss's guard dogs escaped into the factory. They are "
                  "killing workers. Hunt them down.",
             pool=WOLF_POOL, skins={"wolf": "Factory Hound",
                                    "dire wolf": "Boiler Hound"},
             sites=("the scrapyard", "the factory floor"),
             giver="the shift boss",
             epilogue="The hounds are dead. The factory workers return to "
                      "work.",
             failure_epilogue="The hounds still run the night floor. Two more "
                              "workers are dead and the shift is cut."),
        dict(title="Stolen Workers",
             desc="A rival boss is kidnapping workers from the night shift. "
                  "Find the gang and stop them.",
             pool=GOBLIN_LADDER_POOL,
             skins={"cutthroat": "Kidnapper", "slinger": "Gang Slinger",
                    "bruiser": "Gang Boss", "soldier": "Gang Guard",
                    "veteran": "Gang Veteran", "champion": "Gang Captain",
                    "blademaster": "Gang Swordmaster", "warlord": "The Big Boss"},
             sites=("the night market", "the gang hideout",
                    "the boss's tower"),
             giver="the night shift boss",
             epilogue="The gang is defeated. The workers return home safely.",
             failure_epilogue="The gang cleared out the night shift. The "
                              "rival boss has the workers and the contract."),
        dict(title="The Killer Machine",
             desc="A large machine has broken loose in the lower factory. "
                  "Destroy it.",
             pool=GIANTKIN_POOL,
             skins={"ogre": "Crusher Machine", "troll": "Furnace Machine",
                    "giant": "Great Machine"},
             sites=("the lower factory", "the furnace hall"),
             giver="the factory boss",
             epilogue="The machine is destroyed. The lower factory opens "
                      "again.",
             failure_epilogue="The machine wrecked the lower factory. The "
                              "floor is walled off and written down as a "
                              "loss."),
        dict(title="Spiders Below",
             desc="Giant spiders have blocked the air shafts. Clear their "
                  "webs before the lower city runs out of air.",
             pool=SPIDER_POOL, skins={"great spider": "Giant Cave Spider"},
             sites=("the air shafts", "the old cistern"),
             giver="the air keeper",
             epilogue="The spiders are dead. Air flows into the lower city "
                      "again.",
             failure_epilogue="The air shafts stayed blocked. The lower city "
                              "has been emptied and its doors are sealed."),
        dict(title="The Boiler Cult",
             desc="A cult feeds workers to an old boiler. Enter their shrine "
                  "and kill them.",
             pool=CASTER_POOL,
             skins={"hexer": "Ice Tinker", "pyromancer": "Fire Tinker"},
             sites=("the boiler room", "the boiler shrine"),
             giver="the factory inspector",
             epilogue="The cult is gone. The old boiler is shut down.",
             failure_epilogue="The cult still feeds the boiler. The inspector "
                              "has stopped filing reports."),
    ],
}

# Race-agnostic top-band work -- only the capital posts these, and only when
# the roll comes up high (template_band gates them to the drake band).
EPIC_TEMPLATES: list[dict] = [
    dict(title="The Dragon's Tribute",
         desc="A dragon takes food and gold from an entire valley. Kill it "
              "and end the tribute.",
         pool=DRAKE_POOL, skins={},
         sites=("the burned storehouses", "the mountain path",
                "the dragon's cave"),
         giver="the king's general",
         epilogue="The dragon is dead. The valley keeps its harvest.",
         failure_epilogue="The valley pays the tribute. The storehouses go "
                          "out to the mountain every month."),
    dict(title="The Giant at the Border",
         desc="A giant has destroyed several border forts. Track it to its "
              "stronghold and kill it.",
         pool=GIANTKIN_POOL, skins={}, places=2,
         sites=("the ruined fort", "the giant's hall"),
         giver="the border commander",
         epilogue="The giant is dead. Soldiers return to the border forts.",
         failure_epilogue="The giant took another fort. The border line has "
                          "been pulled back ten miles."),
    dict(title="The Renegade Wizard",
         desc="A royal wizard has rebelled and taken control of a tower. Kill "
              "the wizard and stop the fires.",
         pool=MAGUS_POOL, skins={},
         sites=("the burned road", "the wizard's tower"),
         giver="the king's wizard",
         epilogue="The renegade wizard is dead. The tower goes dark.",
         failure_epilogue="The wizard holds the tower and the fires burn on. "
                          "The king's wizard has stopped answering questions "
                          "about it."),
]

# Geographic routing for the existing quest families.  The encounter tables
# stay exactly as calibrated; this layer selects persistent geography and a
# concrete Site/Room shape for them.
QUEST_PLACE_REQUIREMENTS: dict[str, dict] = {
    "Bandits on the Road": dict(
        area_any=("road", "farmland", "pasture", "coast"),
        site_template="camp", domain="mixed", reuse="never"),
    "Wolves Attack": dict(
        area_any=("forest", "hills", "pasture", "prairie"),
        site_template="den", domain="natural", reuse="never"),
    "The Restless Crypt": dict(
        area_any=("settlement",),
        site_template="crypt", domain="built", reuse="prefer"),
    "Deserter Raiders": dict(
        area_any=("road", "farmland", "pasture"),
        site_template="camp", domain="mixed", reuse="never"),
    "Renegade Wizards": dict(
        area_any=("ruin", "road", "settlement"),
        site_template="ruin", domain="built", reuse="prefer"),
    "The Blighted Grove": dict(
        area_any=("forest", "hollow"),
        site_template="grove", domain="natural", reuse="never",
        state_on_post="blighted", state_on_complete="recovering"),
    "Spiders in the Trees": dict(
        area_any=("forest", "hollow", "hills"),
        site_template="grove", domain="natural", reuse="never"),
    "Blighted Beasts": dict(
        area_any=("forest", "hollow", "hills"),
        site_template="den", domain="natural", reuse="never"),
    "Rogue Wardens": dict(
        area_any=("forest", "road", "warden"),
        site_template="road", domain="mixed", reuse="prefer"),
    "The Mist Coven": dict(
        area_any=("hollow", "river", "forest", "hills"),
        site_template="shrine", domain="mixed", reuse="never"),
    "Monsters in the Deep Road": dict(
        area_any=("mountains", "mine"),
        site_template="mine", domain="mixed", reuse="prefer"),
    "The Lost Hold": dict(
        area_any=("mountains", "mine"),
        site_template="ruin", domain="built", reuse="never"),
    "Monster in the Mine": dict(
        area_any=("mountains", "mine"),
        site_template="mine", domain="mixed", reuse="prefer"),
    "The Clan War": dict(
        area_any=("mountains", "mine", "settlement"),
        site_template="camp", domain="mixed", reuse="never"),
    "Mages in the Mine": dict(
        area_any=("mountains", "mine"),
        site_template="mine", domain="mixed", reuse="prefer"),
    "Hounds in the Factory": dict(
        area_any=("industry", "repair"),
        site_template="industrial", domain="built", reuse="prefer"),
    "Stolen Workers": dict(
        area_any=("market", "industry", "settlement"),
        site_template="camp", domain="built", reuse="never"),
    "The Killer Machine": dict(
        area_any=("industry", "clay", "quarry"),
        site_template="industrial", domain="built", reuse="prefer"),
    "Spiders Below": dict(
        area_any=("industry", "quarry", "clay", "repair"),
        site_template="mine", domain="built", reuse="prefer"),
    "The Boiler Cult": dict(
        area_any=("industry", "repair"),
        site_template="industrial", domain="built", reuse="prefer"),
    "The Great Hunt": dict(
        area_any=("prairie", "pasture", "hills", "basin"),
        site_template="den", domain="natural", reuse="never"),
    "Rival Warband": dict(
        area_any=("prairie", "pasture", "road", "hills"),
        site_template="camp", domain="mixed", reuse="never"),
    "Giants in the Pass": dict(
        area_any=("hills", "pass", "ridge"),
        site_template="mine", domain="natural", reuse="never"),
    "Dragon on the Mountain": dict(
        area_any=("hills", "ridge", "mountains"),
        site_template="den", domain="natural", reuse="never"),
    "Rebel Shamans": dict(
        area_any=("prairie", "ridge", "basin", "hills"),
        site_template="shrine", domain="mixed", reuse="never"),
    "The Dragon's Tribute": dict(
        area_any=("mountains", "hills", "ridge"),
        site_template="den", domain="natural", reuse="never"),
    "The Giant at the Border": dict(
        area_any=("road", "hills", "pass"),
        site_template="ruin", domain="built", reuse="never"),
    "The Renegade Wizard": dict(
        area_any=("ruin", "road", "settlement"),
        site_template="tower", domain="built", reuse="prefer"),
}

for _templates in list(TEMPLATES.values()) + [EPIC_TEMPLATES]:
    for _template in _templates:
        _template["place"] = dict(QUEST_PLACE_REQUIREMENTS[_template["title"]])

# Villages post the same race tables, just fewer and lower-leveled: samey on
# purpose -- placeholders for authored content, not competition for it.

# --------------------------------------------------------------------------- #
# Cross-land deliveries (2026-07-14)
# --------------------------------------------------------------------------- #
# The quest kind that sends the party TRAVELLING: taken at its origin
# settlement, paid at a named settlement in ANOTHER land. No sites -- the
# road is the content: ONE guaranteed interception en route (session.py
# forces a road-table event on the travel leg that reaches the destination;
# spotted/ambush valves apply as ever), and the pay scales with the trip's
# travel days. The hand-off itself is the turn-in: arriving at the
# destination with the quest active completes it (session.deliver_if_arrived).
# A couple per world at worldgen, race-agnostic templates.
DELIVERIES_PER_WORLD = 2
DELIVERY_GOLD_PER_DAY = 20  # the courier premium: gold-rich for the effort...
DELIVERY_XP_PER_DAY = 25    # ...XP-light next to site work (a 2-day cross-land
                            # run pays 50 XP, half a level-1 site) -- walking
                            # isn't fighting, and the interception pays its
                            # own wild XP on top

# Crime pays (karma & heat, 2026-07-19): a DARK quest's gold is multiplied
# -- the shadow economy's premium. Its XP is the liability instead (every
# point is SIN; karma.py). Dark quests never come from worldgen (the
# shadow board rolls them lazily, session.py), so no bench sees this knob.
DARK_GOLD_MULT = 1.5

DELIVERY_TEMPLATES: list[dict] = [
    dict(title="The Secret Message", cargo="a sealed letter",
         desc="A royal messenger never reached the next kingdom. Carry the "
              "sealed letter to the envoy. Enemies may try to take it.",
         giver="the head courier", recipient="the royal envoy",
         epilogue="The envoy reads the letter. More guards are sent to the "
                  "road.",
         failure_epilogue="The letter never arrived. The envoy has left the "
                          "city and the road stays unguarded."),
    dict(title="The Locked Chest", cargo="a locked chest",
         desc="A merchant guild must send payment to another city. Deliver "
              "the locked chest unopened.",
         giver="the guild agent", recipient="the merchant agent",
         epilogue="The chest arrives unopened. The guild records the party as "
                  "reliable.",
         failure_epilogue="The payment never came. The guild has cancelled "
                          "the contract and hired other couriers."),
    dict(title="Medicine Delivery", cargo="a crate of medicine",
         desc="A plague has struck a city across the border. Deliver this "
              "medicine as quickly as possible.",
         giver="the town healer", recipient="the city healer",
         epilogue="The medicine reaches the sick. The number of deaths begins "
                  "to fall.",
         failure_epilogue="The medicine sat in the crate. The plague city has "
                          "closed its gates and stopped counting."),
    dict(title="The Smith's Delivery", cargo="a wrapped blade",
         desc="A smith has finished a sword for a buyer in another land. "
              "Deliver it safely.",
         giver="the master smith", recipient="the buyer",
         epilogue="The buyer accepts the sword. The job is complete.",
         failure_epilogue="The blade was never carried. The buyer took the "
                          "deposit back and the smith is short."),
    dict(title="Return the Ashes", cargo="a sealed urn",
         desc="A traveler died far from home. Carry the ashes back to the "
              "family.",
         giver="the traveler's friend", recipient="the family",
         epilogue="The family buries the ashes. They thank the party.",
         failure_epilogue="The urn is still here. The family has held the "
                          "funeral without it."),
    dict(title="The Ransom Payment", cargo="a strongbox of ransom gold",
         desc="A town is paying to free a hostage across the border. Deliver "
              "the gold unopened.",
         giver="the town mayor", recipient="the kidnapper's agent",
         epilogue="The gold is delivered. The hostage is released.",
         failure_epilogue="The ransom was never paid. The kidnappers have "
                          "sent the town a finger."),
]

RACES = tuple(TEMPLATES)

# Settlement name fragments per race (worldgen flavor; ASCII only).
NAME_PARTS = {
    "human":  (("Alder", "King's", "Marsh", "Stone", "Fair", "Oak"),
               ("mere", "ford", "field", "bridge", "haven", "market")),
    "elf":    (("Silver", "Moon", "Green", "Dawn", "Whisper", "Star"),
               ("glade", "spire", "hollow", "reach", "song", "veil")),
    "orc":    (("Iron", "Red", "Ash", "Bone", "Storm", "Black"),
               ("hold", "camp", "maw", "ridge", "spear", "fang")),
    "dwarf":  (("Deep", "Gold", "Grim", "Karak", "Under", "Hammer"),
               ("delve", "forge", "gate", "vault", "helm", "hall")),
    "goblin": (("Gear", "Sprocket", "Grease", "Boiler", "Scrap", "Smog"),
               ("town", "works", "burrow", "pit", "sprawl", "market")),
}

SETTLEMENT_KINDS = {         # (quest slots, level band)
    "capital": (5, (1, LEVEL_CAP)),
    "town":    (4, (1, 14)),
    "village": (2, (1, 8)),
}                            # the "city" tier was merged into "town"
                             # 2026-07-27 -- it existed by accident (three
                             # harbor settlements), never as a design rung


def template_band(tpl: dict) -> tuple[int, int]:
    """The level range a template can be posted at, derived from its pool:
    one below its weakest row (count-scaling reaches down) to two above its
    strongest (the same rule reaches up), clamped to 1..LEVEL_CAP."""
    levels = [FOES[k].level for k in tpl["pool"]]
    return max(1, min(levels) - 1), min(LEVEL_CAP, max(levels) + 2)


def xp_to_cap(level: int = 1) -> int:
    """Quoted XP one hero needs from `level` to LEVEL_CAP (a duo member earns
    quoted awards unchanged -- the coverage target for worldgen)."""
    return sum(xp_to_next(l) for l in range(level, LEVEL_CAP))


# The board's QUOTES: what a posted quest says it pays. `quest_xp_total` /
# `quest_gold` (rpg.py) are the FORMULAS -- these two read the numbers the
# formulas already stamped on the quest dict, with the dark premium folded in.
def quest_xp_posted(quest: dict) -> int:
    if quest.get("kind") == "delivery":
        return quest["xp"]
    return quest.get("xp_total", 0)


def quest_gold_posted(quest: dict) -> int:
    if quest.get("kind") == "delivery":
        return quest["gold"]
    total = quest.get("gold_total", 0)
    if quest.get("align") == "dark":
        total = round(total * DARK_GOLD_MULT)
    return total


# --------------------------------------------------------------------------- #
# The clock on a posting (2026-07-26)
# --------------------------------------------------------------------------- #
# A quest carries `posted_day`, `window` and `deadline_day`, and nothing else:
# every band below is derived, so a save written before the clocks (or a job
# that deliberately has none -- the war waves, the shadow board's day-scoped
# offers) reads as an untimed job and behaves exactly as it always did.

def stamp_quest_clock(quest: dict, day: int, rng: random.Random,
                      extra_days: int = 0) -> dict:
    """Put a window on a posting. `extra_days` buys road time: a courier job
    is due at the other end of a trip it has to walk first."""
    window = rng.randint(*QUEST_WINDOW_DAYS) + extra_days
    quest["posted_day"] = day
    quest["window"] = window
    quest["deadline_day"] = day + window
    return quest


def quest_days_left(quest: dict, day: int) -> int | None:
    """Days to the deadline (0 = due today, negative = into the grace).
    None when the job has no clock."""
    deadline = quest.get("deadline_day")
    return None if deadline is None else deadline - day


def quest_band(quest: dict, day: int) -> str:
    """Which pay band a turn-in on `day` lands in: quick / on time / late /
    expired. An untimed job is always on time."""
    deadline = quest.get("deadline_day")
    if deadline is None:
        return "on time"
    posted = quest.get("posted_day", 0)
    window = quest.get("window", deadline - posted)
    if day <= posted + int(window * QUEST_QUICK_SHARE):
        return "quick"
    if day <= deadline:
        return "on time"
    if day <= deadline + QUEST_GRACE_DAYS:
        return "late"
    return "expired"


def quest_pay_mult(quest: dict, day: int) -> float:
    return QUEST_PAY_BANDS[quest_band(quest, day)]


def quest_expired(quest: dict, day: int, taken: bool = False) -> bool:
    """Is this posting past saving? An UNTAKEN job comes off the board the
    day after its deadline -- nobody waits on a party that never came. A
    TAKEN one keeps the grace: the party is out there working on it."""
    deadline = quest.get("deadline_day")
    if deadline is None:
        return False
    return day > deadline + (QUEST_GRACE_DAYS if taken else 0)


def deadline_note(quest: dict, day: int) -> str:
    """The board's clock column, terse enough for 40 columns."""
    left = quest_days_left(quest, day)
    if left is None:
        return ""
    if left > 1:
        return f"{left} days left"
    if left == 1:
        return "due tomorrow"
    if left == 0:
        return "DUE TODAY"
    grace = QUEST_GRACE_DAYS + left     # days of grace still ahead
    if grace > 0:
        return f"LATE ({grace} day(s) of grace)"
    if grace == 0:
        return "LATE -- LAST DAY"
    return "EXPIRED"


def failure_line(quest: dict) -> str:
    """What the world says about a job nobody finished."""
    return (quest.get("failure_epilogue")
            or f"No one took {quest['name']}. The trouble stands.")


# --------------------------------------------------------------------------- #
# Persistent geography -- Land -> Area -> Site -> Room
# --------------------------------------------------------------------------- #

def new_area(world: dict, key: str, name: str, land: str, kind: str,
             *, subtype: str | None = None, known: bool = True,
             discovered_day: int | None = None) -> dict:
    """Add a DM-authored Area with the same persistent schema as worldgen."""
    area = {
        "id": key, "key": key, "name": name, "land": land, "kind": kind,
        "subtype": subtype or kind, "role": "dm", "description": "",
        "source": "dm", "template": "dm",
        "seed": stable_seed(world.get("seed"), f"land/{land}", "dm-area",
                            len(world["areas"]) + 1),
        "sites": [], "quests": [], "known": known, "visited": False,
        "tags": [kind, subtype or kind], "features": [], "states": [],
        "used_natural_sites": [], "natural_site_order": [], "services": [],
        "links": [], "sequences": {},
    }
    if discovered_day is not None:
        area["discovered_day"] = discovered_day
    world["areas"][key] = area
    world["lands"][land]["areas"].append(key)
    return area


def new_site(world: dict, area_key: str, site_id: str, name: str, level: int,
             *, quest: str | None = None, known: bool = False,
             template: str = "wild", domain: str = "mixed",
             source: str = "worldgen") -> dict:
    if site_id in world["sites"]:
        raise ValueError(f"duplicate Site ID: {site_id}")
    area = world["areas"][area_key]
    seed = stable_seed(world.get("seed"), area_key, f"quest-site:{site_id}",
                       len(area["sites"]) + 1)
    site = {
        "id": site_id, "name": name, "area": area_key,
        "domain": domain, "template": template, "description": "",
        "source": source, "seed": seed, "known": known, "visited": False,
        "rooms": [], "quest_ids": [quest] if quest else [],
        "level": level, "tags": [template, domain],
        "features": [], "states": [], "services": [], "occupants": [],
        "contents": [], "sequences": {},
    }
    world["sites"][site_id] = site
    area["sites"].append(site_id)
    return site


def new_room(world: dict, site_id: str, room_id: str, name: str,
             kinds: list[str], *, quest: str | None = None) -> dict:
    """Add an immediate place. `room` covers interiors and outdoor text-
    adventure nodes such as clearings, ledges, and stretches of path."""
    if room_id in world["rooms"]:
        raise ValueError(f"duplicate Room ID: {room_id}")
    site = world["sites"][site_id]
    seed = stable_seed(world.get("seed"), site_id, f"quest-room:{room_id}",
                       len(site["rooms"]) + 1)
    pool_id, contents = generic_room_contents(room_id, name, site["name"],
                                               seed)
    room = {
        "id": room_id, "name": name, "site": site_id,
        "template": slug_name(name), "role": slug_name(name),
        "content_pool": pool_id, "source": "worldgen", "seed": seed,
        "known": False, "visited": False, "contents": contents,
        "features": [], "states": [], "occupants": [],
        "kinds": list(kinds), "quest_ids": [quest] if quest else [],
    }
    world["rooms"][room_id] = room
    site["rooms"].append(room_id)
    return room


def slug_name(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def all_areas(world: dict) -> list[dict]:
    return list(world["areas"].values())


def settlements(world: dict) -> list[dict]:
    return [a for a in all_areas(world) if a["kind"] == "settlement"]


def land_areas(world: dict, land: str) -> list[dict]:
    rec = world["lands"].get(land)
    return [world["areas"][key] for key in rec["areas"]] if rec else []


def area_sites(world: dict, area: dict | str) -> list[dict]:
    key = area if isinstance(area, str) else area["key"]
    return [world["sites"][sid] for sid in world["areas"][key]["sites"]]


def site_rooms(world: dict, site: dict | str) -> list[dict]:
    key = site if isinstance(site, str) else site["id"]
    return [world["rooms"][rid] for rid in world["sites"][key]["rooms"]]


def quest_sites(world: dict, quest: dict) -> list[dict]:
    return [world["sites"][sid] for sid in quest.get("sites", [])]


def _fallback_place_requirement(tpl: dict) -> dict:
    text = " ".join((tpl.get("title", ""), *tpl.get("sites", ()))).lower()
    if any(word in text for word in ("factory", "boiler", "machine")):
        template, tags, domain = "industrial", ("industry", "settlement"), "built"
    elif any(word in text for word in ("mine", "deep", "cave")):
        template, tags, domain = "mine", ("mountains", "mine", "quarry"), "mixed"
    elif any(word in text for word in ("grove", "forest", "tree")):
        template, tags, domain = "grove", ("forest", "hollow"), "natural"
    elif any(word in text for word in ("crypt", "grave", "dead")):
        template, tags, domain = "crypt", ("settlement", "tomb"), "built"
    elif any(word in text for word in ("tower", "wizard", "guildhall")):
        template, tags, domain = "tower", ("ruin", "road", "settlement"), "built"
    elif any(word in text for word in ("den", "hunt", "beast", "dragon")):
        template, tags, domain = "den", ("forest", "hills", "prairie"), "natural"
    else:
        template, tags, domain = "camp", ("road", "settlement", "prairie"), "mixed"
    return {"area_any": tags, "site_template": template, "domain": domain,
            "reuse": "never"}


def quest_place_requirement(tpl: dict) -> dict:
    return dict(tpl.get("place") or _fallback_place_requirement(tpl))


def _select_quest_area(world: dict, origin_key: str, requirement: dict,
                       rng: random.Random) -> dict:
    origin = world["areas"][origin_key]
    wanted = set(requirement.get("area_any", ()))
    candidates = [a for a in all_areas(world)
                  if wanted.intersection(a.get("tags", ())) and
                  a["land"] == origin["land"]]
    if not candidates:
        candidates = [a for a in all_areas(world)
                      if wanted.intersection(a.get("tags", ()))]
    if not candidates:
        candidates = [origin]
    domain = requirement.get("domain")
    if domain == "natural":
        natural = [a for a in candidates if a["kind"] == "natural"]
        if natural:
            candidates = natural
    elif domain == "built":
        built = [a for a in candidates if a["kind"] == "settlement"]
        if built:
            candidates = built
    return rng.choice(candidates)


def _reusable_site(world: dict, area: dict, requirement: dict,
                   n_rooms: int) -> dict | None:
    """An existing compatible place skeleton to hang this quest on -- but only
    if its room count is EXACTLY the encounter count this place was allotted
    (2026-07-26): a reused three-room crypt would silently turn a one-fight
    job back into a three-fight one."""
    if requirement.get("reuse") != "prefer":
        return None
    template = requirement["site_template"]
    compatible = {
        "crypt": {"crypt", "shrine"},
    }.get(template, {template})
    for site in area_sites(world, area):
        active_quests = [
            qid for qid in site.get("quest_ids", ())
            if qid not in world["quests"]
            or world["quests"][qid].get("status") not in ("done", "complete",
                                                          "failed")
        ]
        if (site.get("template") in compatible
                and not active_quests
                and len(site.get("rooms", ())) == n_rooms):
            return site
    return None


def _put_quest_in_site(world: dict, site: dict, qid: str, level: int,
                       pool: tuple[str, ...], rng: random.Random,
                       shares: tuple[float, ...],
                       final_place: bool) -> None:
    """Attach calibrated rosters to an existing compatible place skeleton."""
    rooms = site_rooms(world, site)
    built = build_site_rooms(
        level, len(rooms), pool, rng,
        tuple(room["name"] for room in rooms),
        shares=shares, final_room=final_place)
    site["level"] = level
    site["quest_ids"].append(qid)
    for room, (_name, kinds) in zip(rooms, built):
        room["kinds"] = list(kinds)
        room["quest_ids"].append(qid)


def split_encounters(encounters: int, places: int) -> list[int]:
    """Spread a quest's fights across its places FRONT-LIGHT: a three-fight
    two-place job is 1 then 2, so the escalation ends at the destination."""
    base, rem = divmod(encounters, places)
    return [base + (1 if j >= places - rem else 0) for j in range(places)]


def build_quest(world: dict, qid: str, tpl: dict, area_key: str, level: int,
                rng: random.Random) -> dict:
    """Build calibrated encounters into compatible persistent geography.

    Since 2026-07-26 (the attrition rework's slice 1) a quest is 1-3
    ENCOUNTERS rolled at the QUEST level (QUEST_ENCOUNTERS), and its PLACE
    count is authored on the template (`places`, default 1) rather than
    rolled -- a job spans two sites only when the fiction genuinely moves
    between two places, never as a difficulty dial. Every place of a quest
    stands at the quest's own level: one quest, one level (the rising
    ROOM_SHARES curve carries the escalation instead, and the board stops
    showing a job whose sites disagree about their own grade)."""
    requirement = quest_place_requirement(tpl)
    target_area = _select_quest_area(world, area_key, requirement, rng)
    n_places = min(max(1, tpl.get("places", 1)), len(tpl["sites"]))
    if tpl.get("deed") or tpl.get("twist"):
        # The caper shapes (karma.py's dark templates, 2026-07-19) are
        # AUTHORED, not rolled: the deed belongs to the first site and
        # the twist to the last, so every stem must stand.
        n_places = len(tpl["sites"])
    encounters = rng.choices(*QUEST_ENCOUNTERS)[0]
    encounters = min(max(encounters, n_places), max(ROOM_SHARES))
    per_place = split_encounters(encounters, n_places)
    shares = ROOM_SHARES[encounters]
    stems = list(tpl["sites"][:n_places])
    site_ids = []
    cut = 0
    for j, stem in enumerate(stems):
        n_rooms = per_place[j]
        place_shares = tuple(shares[cut:cut + n_rooms])
        cut += n_rooms
        last_place = j == n_places - 1
        reused = _reusable_site(world, target_area, requirement, n_rooms)
        if reused is not None:
            _put_quest_in_site(world, reused, qid, level, tpl["pool"], rng,
                               place_shares, last_place)
            site_id = reused["id"]
        else:
            roles = tuple(SITE_TEMPLATES[requirement["site_template"]]
                          .get("room_roles", ()))
            rooms = build_site_rooms(level, n_rooms, tpl["pool"], rng,
                                     roles, shares=place_shares,
                                     final_room=last_place)
            site_id = f"site/{target_area['land']}/{slug_name(target_area['name'])}/quest-{qid}-{j + 1}"
            new_site(world, target_area["key"], site_id, stem, level,
                     quest=qid, template=requirement["site_template"],
                     domain=requirement["domain"])
            for k, (name, kinds) in enumerate(rooms):
                new_room(world, site_id, f"{site_id}/{slug_name(name)}",
                         name, kinds, quest=qid)
        site_ids.append(site_id)
    xp_total = quest_xp_total(level, encounters)
    gold_total = quest_gold(level, encounters)
    # The caper fields ride the site dicts (plain JSON, like everything):
    # deed on the FIRST site (the attempt comes before the fighting),
    # twist on the LAST (the complication waits at the end of the job).
    if tpl.get("deed"):
        world["sites"][site_ids[0]]["deed"] = dict(tpl["deed"])
    if tpl.get("twist"):
        world["sites"][site_ids[-1]]["twist"] = dict(tpl["twist"])
    quest = {
        "id": qid,
        "name": tpl["title"],
        "desc": tpl["desc"],
        "origin": area_key,
        "target_area": target_area["id"],
        "place": requirement,
        "state_target": target_area["id"],
        "level": level,
        "skins": dict(tpl["skins"]),
        "sites": site_ids,
        "site_count": len(site_ids),
        "encounters": encounters,
        "xp_total": xp_total,
        "gold_total": gold_total,
        "next": {"site": 0, "room": 0},     # the progress cursor
        "status": "open",
        "align": tpl.get("align", "good"),  # karma & heat (2026-07-19):
                                            # whose XP bucket this work
                                            # pays into -- good burns bad
                                            # karma, dark accrues it
        "epilogue": tpl.get("epilogue", ""),
    }
    if requirement.get("state_on_post"):
        add_state(world, target_area, requirement["state_on_post"])
    return quest


def complete_quest_place_state(world: dict, quest: dict,
                               day: int | None = None) -> None:
    """Apply the quest's persistent geography transition, if it has one."""
    req = quest.get("place") or {}
    old = req.get("state_on_post")
    new = req.get("state_on_complete")
    target = world["areas"].get(quest.get("state_target"))
    if target is not None and old and new:
        replace_state(world, target, old, new, day=day)


def attach_giver(quest: dict, race: str, rng: random.Random,
                 role: str | None = None,
                 used_names: set[str] | None = None) -> None:
    """Put a face on a quest (2026-07-12): the person behind the job. In
    play there is NO board -- asking around funnels to this person in one
    message (dm.md), taking the quest is talking to them, and they receive
    the turn-in. Role comes from the template; the face is a targeted NPC
    (people.make_npc: race/role fixed, the name rolled -- a giver carries
    no trait sketch since 2026-08-05). Stored as a plain dict on the quest,
    so it rides the save like everything else."""
    from people import make_npc     # runtime import: people imports quests
                                    # (RACES), so top-level would be a cycle
    quest["giver"] = make_npc(rng, race, role or "the local patron",
                              level=quest["level"], used_names=used_names)


def build_delivery_quest(qid: str, tpl: dict, origin: dict, dest: dict,
                         rng: random.Random) -> dict:
    """One cross-land delivery: origin posts it, `dest` (another land's
    settlement) pays it. Pay derives from the trip's one-way travel days --
    the road IS the pay grade here, not a site level (`level` stays 0: no
    rooms, no threat math; the guaranteed interception rolls off the road's
    own party-independent table like any travel event)."""
    days = (TRAVEL_DAYS_IN_LAND if origin["land"] == dest["land"]
            else TRAVEL_DAYS_CROSS)
    return {
        "id": qid,
        "kind": "delivery",
        "name": tpl["title"],
        "desc": tpl["desc"],
        "cargo": tpl["cargo"],
        "origin": origin["key"],
        "dest": dest["key"],
        "dest_name": dest["name"],
        "days": days,
        "gold": DELIVERY_GOLD_PER_DAY * days,
        "xp": DELIVERY_XP_PER_DAY * days,
        "level": 0,             # deliveries have no site level; readouts
                                # print DELIVERY where a level would go
        "align": "good",        # courier work is honest work (karma)
        "skins": {},
        "sites": [],
        "next": {"site": 0, "room": 0},
        "intercepted": False,   # the guaranteed road event, spent on the
                                # travel leg that reaches the destination
        "status": "open",
        "epilogue": tpl.get("epilogue", ""),
    }


def forge_quest(world: dict, qid: str, level: int, places: int,
                encounters: int, pool: tuple[str, ...], name: str,
                rng: random.Random, area_key: str = "",
                align: str = "good") -> dict:
    """The DM's quest creator (session.py `forge`): level, shape, and foe
    kinds in -> a quest built by the same rules as worldgen and saved beside
    them. For improvised content the board doesn't cover. `align="dark"`
    forges a shadow job (karma & heat: bad-karma XP, the gold premium).

    The shape is (places, encounters) since 2026-07-26 -- the same two
    numbers a generated quest carries."""
    # Forge pins the shape, so build its world-owned places directly instead
    # of asking build_quest to roll and then discarding a second layout.
    places = max(1, places)
    encounters = min(max(encounters, places), max(ROOM_SHARES))
    per_place = split_encounters(encounters, places)
    shares = ROOM_SHARES[encounters]
    site_ids = []
    cut = 0
    for j in range(places):
        n_rooms = per_place[j]
        rooms = build_site_rooms(
            level, n_rooms, pool, rng,
            tuple(SITE_TEMPLATES["wild"]["room_roles"]),
            shares=tuple(shares[cut:cut + n_rooms]),
            final_room=j == places - 1)
        cut += n_rooms
        site_id = (f"site/{world['areas'][area_key]['land']}/"
                   f"{slug_name(world['areas'][area_key]['name'])}/"
                   f"quest-{qid}-{j + 1}")
        new_site(world, area_key, site_id, f"site {j + 1}", level,
                 quest=qid, template="wild", domain="mixed", source="dm")
        for k, (rn, kinds) in enumerate(rooms):
            new_room(world, site_id, f"{site_id}/{slug_name(rn)}", rn,
                     kinds, quest=qid)
        site_ids.append(site_id)
    return {"id": qid, "name": name, "desc": "(DM-forged)",
            "origin": area_key, "level": level,
            "skins": {}, "sites": site_ids, "site_count": places,
            "encounters": encounters,
            "xp_total": quest_xp_total(level, encounters),
            "gold_total": quest_gold(level, encounters),
            "next": {"site": 0, "room": 0},
            "status": "open", "align": align, "epilogue": ""}


# --------------------------------------------------------------------------- #
# Worldgen
# --------------------------------------------------------------------------- #
# The central cast (2026-07-12): every land gets three persistent figures,
# generated at worldgen and carried in the save -- a RULER (the war-wave
# questgiver once the conquest questline runs), a KNOWLEDGE figure (the
# exposition and foreshadowing voice), and one WILDCARD from a small role
# table. The design trick for roles beyond questgiver: each wildcard hangs
# on a system that already exists (recruiting, shopping, rumor, training)
# instead of asking for new mechanics. They are dict NPCs (people.make_npc):
# no stat blocks; if one must fight, forge the encounter.

RULER_TITLES = {
    "human":  {"m": "king", "f": "queen"},
    "elf":    {"m": "speaker of the high council",
               "f": "speaker of the high council"},
    "orc":    {"m": "great chief of the clans",
               "f": "great chief of the clans"},
    "dwarf":  {"m": "high thane", "f": "high thane"},
    "goblin": {"m": "chief overboss", "f": "chief overboss"},
}
SAGE_ROLES = ("loremaster", "court wizard", "keeper of records",
              "temple scholar", "star-reader")
WILDCARD_ROLES = ("spymaster", "mercenary captain", "master smith",
                  "high priest", "war profiteer", "guild factor")


def _cast_the_land(world: dict, polity: str, seat: dict, rng: random.Random,
                   used_people: set[str]) -> None:
    from people import make_npc, SEXES     # runtime import (cycle: RACES)
    race = land_race(world, polity)
    sex = rng.choice(SEXES)
    for role, post in ((RULER_TITLES[race][sex], "ruler"),
                       (rng.choice(SAGE_ROLES), "sage"),
                       (rng.choice(WILDCARD_ROLES), "wildcard")):
        # Rulers and sages skew old (a 20-year-old king every world read
        # wrong); the wildcard keeps the working-age roll.
        age = rng.randint(35, 70) if post in ("ruler", "sage") else None
        npc = make_npc(rng, race, role, sex=sex if post == "ruler" else None,
                       age=age, used_names=used_people)
        npc_id = f"npc/{polity}/{slug_name(npc['name'])}/{post}"
        npc.update(id=npc_id, land=polity, seat=seat["key"], post=post)
        world["npcs"].append(npc)
        if post == "ruler":
            # THE RULER CHARACTER (2026-08-10, the politics rung): the sheet
            # itself was rolled at `worldsim.open_world` and lives on the
            # land layer -- ONE copy. What happens here is that it acquires
            # the face that wears it, so the traits and the name are joined
            # without the save carrying either of them twice.
            worldsim.ruler_sheet(world, polity)["npc"] = npc_id


SERVICE_ROLES = {
    "lodging": "innkeeper", "smith": "smith",
    "general_goods": "shopkeeper", "alchemist": "alchemist",
    "market": "market keeper", "government": "clerk",
    "healer": "healer",         # slice 3b: every settlement has one, and its
                                # SUBTYPE sets how far the art reaches
                                # (rpg.HEALER_TIER_CAP)
}


def cast_service_providers(world: dict, settlement: dict,
                           rng: random.Random) -> None:
    """Give one settlement's required services their persistent local faces.
    Called for every settlement at worldgen and again for any the world
    materializes later (the trim's `found_settlement`)."""
    from people import make_npc
    race = land_race(world, settlement["land"])
    for service in settlement.get("services", ()):
        # Service faces are local to their settlement; their names do
        # not consume the campaign-wide giver/notable namespace.
        npc = make_npc(rng, race, SERVICE_ROLES[service["kind"]])
        npc_id = (f"npc/{settlement['land']}/{slug_name(npc['name'])}/"
                  f"{slug_name(settlement['name'])}/"
                  f"{slug_name(service['kind'])}")
        npc.update(id=npc_id, land=settlement["land"],
                   seat=settlement["id"], post="service")
        service["provider"] = npc_id
        site = world["sites"].get(service.get("site"))
        if site is not None and npc_id not in site["occupants"]:
            site["occupants"].append(npc_id)
        world["npcs"].append(npc)


def found_settlement(world: dict, polity: str, rng: random.Random, *,
                     need: str, tier: str | None = None,
                     tags: Iterable[str] = (), day: int | None = None
                     ) -> dict | None:
    """THE NEED-TO-EXIST DRAW (2026-08-07, the settlement trim). Grow a land
    by one settlement because the world needs it to exist -- the reserve
    entry, its Sites and services (places.py) plus the service faces that
    make it a place the party can actually use. Returns None when the land's
    reserve holds nothing that fits.

    Nothing is posted on its board here: an unread board fills to its band
    the first time the party looks at it (`refresh_settlement_board`), which
    is exactly when a new town's work should appear."""
    area = materialize_settlement(world, polity, need=need, tier=tier,
                                  tags=tags, day=day)
    if area is None:
        return None
    cast_service_providers(world, area, rng)
    return area


def _settlement_name(race: str, rng: random.Random, used: set[str]) -> str:
    pre, suf = NAME_PARTS[race]
    for _ in range(50):
        name = rng.choice(pre) + rng.choice(suf)
        if name not in used:
            used.add(name)
            return name
    name = rng.choice(pre) + rng.choice(suf) + " II"
    used.add(name)
    return name


def next_quest_id(world: dict) -> str:
    """The next free quest id. A monotonic counter, not a count: expired
    postings are DELETED from world['quests'] (slice 2), so counting what is
    left would hand a live job an id a released Site still remembers."""
    seq = world.get("quest_seq", len(world["quests"])) + 1
    while (f"q{seq:02d}" in world["quests"]
           or any(f"q{seq:02d}" in site.get("quest_ids", ())
                  for site in world["sites"].values())):
        seq += 1
    world["quest_seq"] = seq
    return f"q{seq:02d}"


def release_quest_places(world: dict, quest: dict) -> None:
    """Give a dead posting's geography back to the world. A Site built FOR
    this quest (and for no other) is deleted with its Rooms; a shared or
    reused skeleton just forgets the quest. Called when an untaken job
    expires -- without it a long career leaves a land littered with the
    bandit camps of jobs nobody ever took."""
    qid = quest["id"]
    for site_id in list(quest.get("sites", ())):
        site = world["sites"].get(site_id)
        if site is None:
            continue
        others = [q for q in site.get("quest_ids", ()) if q != qid]
        if others or f"quest-{qid}-" not in site_id:
            site["quest_ids"] = others
            for room in site_rooms(world, site):
                room["quest_ids"] = [q for q in room.get("quest_ids", ())
                                     if q != qid]
            continue
        for room_id in list(site.get("rooms", ())):
            world["rooms"].pop(room_id, None)
        area = world["areas"].get(site.get("area"))
        if area is not None and site_id in area.get("sites", ()):
            area["sites"].remove(site_id)
        world["sites"].pop(site_id, None)


def _post_quest(world: dict, settlement: dict, rng: random.Random,
                used_people: set[str] | None = None,
                day: int = 0) -> dict:
    """Roll one quest onto a settlement's board: level uniform in the
    settlement band (displayed straight; too easy and too hard both happen),
    template drawn from the race's table (the capital also draws the epics)
    among those whose band contains the roll. Since 2026-07-26 the posting is
    stamped with the day and a window (`stamp_quest_clock`)."""
    lo, hi = SETTLEMENT_KINDS[settlement["subtype"]][1]
    level = rng.randint(lo, hi)
    race = land_race(world, settlement["land"])
    tables = list(TEMPLATES[race])
    if settlement["subtype"] == "capital":
        tables += EPIC_TEMPLATES
    fitting = [t for t in tables
               if template_band(t)[0] <= level <= template_band(t)[1]]
    if not fitting:     # a roll above every local pool: snap to the ladder
        fitting = [t for t in tables if "warlord" in t["pool"]] or tables
        lo_t, hi_t = template_band(fitting[0])
        level = max(lo_t, min(hi_t, level))
    # Prefer a template not already on this settlement's board (the ladder
    # template fits every roll and would otherwise crowd its siblings out).
    posted = {world["quests"][qid]["name"] for qid in settlement["quests"]}
    fresh = [t for t in fitting if t["title"] not in posted]
    tpl = rng.choice(fresh or fitting)
    qid = next_quest_id(world)
    quest = build_quest(world, qid, tpl, settlement["key"], level, rng)
    quest["failure_epilogue"] = tpl.get("failure_epilogue", "")
    # THE BOARD REACTS TO WORLD STATE (2026-08-09): a poor land pays poorly
    # and a rich one pays well, and a card standing over the land can move
    # both -- the crown's war debts pay 0.85, a province paying its swords
    # in paper notes quotes 1.5. Stamped in, not read out, so the job keeps
    # the terms it was taken at.
    quest["gold_total"] = _world_pay(world, settlement, quest["gold_total"])
    stamp_quest_clock(quest, day, rng)
    _maybe_attach_weapon_reward(quest, qid)
    attach_giver(quest, race, rng, role=tpl.get("giver"),
                 used_names=used_people)
    world["quests"][qid] = quest
    settlement["quests"].append(qid)
    return quest


WEAPON_REWARD_CHANCE = 0.15     # this share of posted jobs pays its turn-in
                                # lump as a WEAPON instead of gold (2026-07-28,
                                # the weapon generation system): the level is
                                # the pay grade here as everywhere -- quality
                                # steel in the low band, masterwork in the
                                # middle, generated magic weapons at the top.
                                # XP and the per-encounter shares are never
                                # touched. Across a played campaign this is
                                # the designer's "10-15 weapon jobs".


def _maybe_attach_weapon_reward(quest: dict, qid: str) -> None:
    """Roll the weapon-reward mode onto a fresh posting. Runs on a rng
    DERIVED from the quest id, so the shared posting stream (and every
    career bench riding it) is untouched by the extra draws."""
    import weapons                  # runtime import (weapons imports rpg)
    wrng = random.Random(f"reward:{qid}")
    if wrng.random() >= WEAPON_REWARD_CHANCE:
        return
    w = weapons.reward_weapon_for_level(quest["level"], wrng)
    quest["reward_weapon"] = dataclasses.asdict(w)
    quest["gold_total"] = 0         # the lump IS the weapon; the encounter
                                    # shares still pay as they are earned


def board_slots(world: dict, settlement: dict) -> int:
    """How many live jobs this settlement keeps posted: its tier's own count
    (SETTLEMENT_KINDS), moved by the world layer (2026-08-09, the economy
    floor). A prosperous land posts more work and a land in crisis posts
    less ORDINARY work -- its crises post their own on top. The floor keeps
    every settlement a place with something in it."""
    base = SETTLEMENT_KINDS[settlement["subtype"]][0]
    shift = worldsim.board_shift(world, settlement["land"])
    return max(worldsim.BOARD_SLOTS_FLOOR, base + shift)


def open_quests(world: dict, settlement: dict, day: int | None = None) -> list:
    """The settlement's live board. `day`, when given, also drops postings
    whose window has closed but whose expiry has not been run yet (a distant
    land's board, read off the map)."""
    out = []
    for qid in settlement.get("quests", ()):
        q = world["quests"].get(qid)
        if q is None or q["status"] != "open":
            continue
        if day is not None and quest_expired(q, day):
            continue
        out.append(q)
    return out


def board_forecast(world: dict, settlement: dict, day: int) -> int:
    """How many live jobs the party would find if it walked in TODAY: what is
    posted now, minus what has lapsed, plus what the refill owes. Readouts
    (the map, `status`) use this rather than the raw count -- the clock only
    runs where the party stands, so a land it left would otherwise decay to
    "0 job(s)" on the map and read as a place with no work in it."""
    live = len(open_quests(world, settlement, day))
    slots = board_slots(world, settlement)
    seen = settlement.get("board_day")
    owed = (slots - live if seen is None
            else QUEST_REFILL_PER_DAY * max(0, day - seen))
    return min(slots, live + max(0, owed))


def expire_settlement_board(world: dict, settlement: dict, day: int,
                            taken: set[str] | frozenset = frozenset()
                            ) -> list[dict]:
    """Take the closed windows off one settlement's board. Returns the
    expired postings (their `failure_epilogue` is the rumour the settlement
    hears next). A TAKEN job is left alone here -- its clock is run by the
    caller wherever the party is standing, and its geography must survive
    with the party inside it."""
    gone = []
    for qid in list(settlement.get("quests", ())):
        quest = world["quests"].get(qid)
        if quest is None:
            settlement["quests"].remove(qid)
            continue
        if quest["status"] != "open" or qid in taken:
            continue
        if not quest_expired(quest, day):
            continue
        quest["status"] = "expired"
        quest["failed_day"] = day
        release_quest_places(world, quest)
        settlement["quests"].remove(qid)
        world["quests"].pop(qid, None)
        gone.append(quest)
    return gone


def _post_card_quest(world: dict, settlement: dict, posting: dict,
                     rng: random.Random,
                     used_people: set[str] | None = None,
                     day: int = 0) -> dict:
    """Put one live world card's own job on a settlement's board (the QUEST
    outlet's POST verb, 2026-08-09). The template is authored on the card
    (`worldsim.job`); everything else -- the geography, the giver's face,
    the clock, the pay grade -- is the ordinary generator's, because a
    card's work is work, not a special case.

    The level is the settlement's own band clamped into the template's, the
    same clamp a rolled posting gets. No WEAPON REWARD rides a card job: the
    reward mode is a flat share of the ordinary board, and a card that pays
    a premium in gold should not silently pay it in steel instead."""
    tpl = posting["job"]
    lo, hi = SETTLEMENT_KINDS[settlement["subtype"]][1]
    t_lo, t_hi = template_band(tpl)
    level = max(t_lo, min(t_hi, rng.randint(lo, hi)))
    qid = next_quest_id(world)
    quest = build_quest(world, qid, tpl, settlement["key"], level, rng)
    quest["failure_epilogue"] = tpl.get("failure_epilogue", "")
    quest["world_card"] = posting["key"]
    quest["gold_total"] = _world_pay(world, settlement, quest["gold_total"],
                                     posting["pay"])
    stamp_quest_clock(quest, day, rng)
    attach_giver(quest, land_race(world, settlement["land"]), rng,
                 role=tpl.get("giver"), used_names=used_people)
    world["quests"][qid] = quest
    settlement["quests"].append(qid)
    return quest


def _world_pay(world: dict, settlement: dict, gold: int,
               premium: float = 1.0) -> int:
    """What the world layer does to a posting's quoted lump: the land's
    band and whatever its live cards reprice, times the card's own premium
    where a card put the job up. Applied ONCE, at posting time -- the
    board's terms are the terms it was posted at."""
    mult = worldsim.board_pay(world, settlement["land"]) * premium
    return max(1, round(gold * mult))


def refresh_settlement_board(world: dict, settlement: dict, day: int,
                             rng: random.Random,
                             used_people: set[str] | None = None
                             ) -> list[dict]:
    """The banded lazy refill: top this settlement back toward its slot
    count. A board seen for the FIRST time fills up (the land has always had
    work, the party has just never asked); after that it posts at most
    QUEST_REFILL_PER_DAY per day elapsed, so the board is a place that
    changes rather than a slot machine to re-roll.

    Since the economy floor (2026-08-09) the CARDS standing over the land go
    up first and outside the refill rule: a world event is news, and news
    does not wait for a slot to open. A card's job carries its key, so one
    board never runs two copies of it; it lapses on its own window like any
    other posting, and the card puts it back up for as long as it stands."""
    slots = board_slots(world, settlement)
    posted = []
    have = {world["quests"][qid].get("world_card")
            for qid in settlement.get("quests", ())
            if qid in world["quests"]}
    for posting in worldsim.board_postings(world, settlement["land"]):
        if posting["key"] in have:
            continue
        if len(open_quests(world, settlement)) >= slots:
            break
        posted.append(_post_card_quest(world, settlement, posting, rng,
                                       used_people, day=day))
    live = len(open_quests(world, settlement))
    seen = settlement.get("board_day")
    room = slots - live
    if seen is not None:
        room = min(room, QUEST_REFILL_PER_DAY * max(0, day - seen))
    settlement["board_day"] = day
    return posted + [_post_quest(world, settlement, rng, used_people, day=day)
                     for _ in range(max(0, room))]


def generate_world(seed: int | None = None) -> dict:
    """Create the six-Land persistent world and seed its quest inventory.

    Since 2026-07-26 worldgen posts ONE job per settlement and stops. The
    board is filled and kept filled by `refresh_settlement_board` as the
    party actually looks at it: with clocks on every posting the old up-front
    XP-coverage top-up asserted a total that expiry immediately made a lie.
    A fresh world is therefore SMALL -- one job a settlement plus the
    couriers -- and that is not the content budget, it is the seed."""
    rng = random.Random(seed)
    used_people: set[str] = set()   # one namespace for givers AND the cast:
                                    # two Ruriks in one town read as a bug
    world = create_geography(seed)
    # The world layer (2026-08-07, the worldsim build's frame): every land's
    # wealth band, its three shuffled decks, and the opening card a land in
    # crisis is already living through. Seeded off the world seed inside
    # worldsim.py -- it draws nothing from this stream. It is rolled HERE,
    # before the first posting, because since the economy floor the board
    # READS it: a land in crisis quotes crisis money on day one.
    worldsim.open_world(world)
    world["quest_seq"] = 0
    for settlement in settlements(world):
        cast_service_providers(world, settlement, rng)
    for polity, setts in settlements_by_land(world).items():
        _cast_the_land(world, polity, setts[0], rng, used_people)

    for settlement in settlements(world):
        _post_quest(world, settlement, rng, used_people)

    for _ in range(DELIVERIES_PER_WORLD):
        _post_delivery(world, rng, used_people)

    # The weapon layer (2026-07-28): the famous pregenerated armory and the
    # legendary smiths. Rolled on a DERIVED rng so the main worldgen stream
    # -- and every career bench seeded off it -- is byte-identical to the
    # pre-armory worlds.
    from weapons import roll_armory, roll_smiths    # runtime import
                                                    # (weapons imports rpg)
    wrng = random.Random(f"armory:{seed}")
    world["armory"] = roll_armory(world, wrng)
    world["smiths"] = roll_smiths(world, wrng)
    return world


def refresh_deliveries(world: dict, day: int, rng: random.Random,
                       used_people: set[str] | None = None,
                       origins: list[dict] | None = None) -> list[dict]:
    """Keep DELIVERIES_PER_WORLD courier jobs live. `origins` restricts the
    posting to settlements the party can actually reach the news from (the
    local land) -- the board's refill is lazy in the same way."""
    live = sum(1 for q in world["quests"].values()
               if q.get("kind") == "delivery" and q["status"] == "open"
               and not quest_expired(q, day))
    return [_post_delivery(world, rng, used_people, day=day, origins=origins)
            for _ in range(max(0, DELIVERIES_PER_WORLD - live))]


def _post_delivery(world: dict, rng: random.Random,
                   used_people: set[str] | None = None,
                   day: int = 0,
                   origins: list[dict] | None = None) -> dict:
    """Roll one cross-land delivery onto a random settlement's board: a
    destination in another land, a fresh template if one is left, a giver
    face at the origin and a RECIPIENT face at the destination (the
    hand-off is the turn-in scene)."""
    from people import make_npc     # runtime import (cycle: RACES)
    origin = rng.choice(origins or settlements(world))
    dests = [s for s in settlements(world) if s["land"] != origin["land"]]
    dest = rng.choice(dests)
    posted = {q["name"] for q in world["quests"].values()
              if q.get("kind") == "delivery" and q["status"] == "open"}
    fresh = [t for t in DELIVERY_TEMPLATES if t["title"] not in posted]
    tpl = rng.choice(fresh or DELIVERY_TEMPLATES)
    qid = next_quest_id(world)
    quest = build_delivery_quest(qid, tpl, origin, dest, rng)
    quest["failure_epilogue"] = tpl.get("failure_epilogue", "")
    # A courier job's window buys the road it has to walk (both legs), so a
    # cross-land run is not late before it starts.
    stamp_quest_clock(quest, day, rng, extra_days=2 * quest["days"])
    attach_giver(quest, land_race(world, origin["land"]), rng,
                 role=tpl.get("giver"),
                 used_names=used_people)
    quest["recipient"] = make_npc(rng, land_race(world, dest["land"]),
                                  tpl["recipient"],
                                  used_names=used_people)
    world["quests"][qid] = quest
    origin["quests"].append(qid)
    return quest


# --------------------------------------------------------------------------- #
# The world map & navigation layer (2026-07-09)
# --------------------------------------------------------------------------- #
# The map is a LIST, not a grid: each race's LAND holds its settlements and
# its wilderness -- no coordinates. Travel inside a land takes
# TRAVEL_DAYS_IN_LAND day(s), to another land TRAVEL_DAYS_CROSS; every travel
# day is a camp night (the existing overnight recovery, so healing en route
# falls out for free) with a chance of a road encounter. The road's threat
# table is party-INDEPENDENT (the OSR stance: the world does not scale to
# you): any level can appear, weighted hard toward the low end
# (WILD_LEVEL_DECAY) -- the rare high tail is how the world above the
# party's level stays real. An encounter well above the party is usually
# SPOTTED at range (avoid it or engage it: the player's call); an
# AMBUSH_CHANCE of the time it finds them first, and what's left is the
# pause-and-retreat machinery. Hunting is the exception to the OSR table:
# the party CHOOSES its prey, so the hunt rolls relative to its level.

TRAVEL_DAYS_IN_LAND = 1      # settlement to settlement inside one land
TRAVEL_DAYS_CROSS = 2        # crossing into another race's land
TRAVEL_ENCOUNTER_CHANCE = 0.15   # per travel day (compounded over a trip)
EXPLORE_ENCOUNTER_CHANCE = 0.30  # the explore move beats more bushes
EXPLORE_XP = 15                  # discovering a new place pays this flat
WILD_LEVEL_DECAY = 0.75      # P(road encounter is level L) ~ DECAY**L
SPOTTED_MARGIN = 3           # foes this many levels above the party are
                             # spotted at range instead of met blade-first...
AMBUSH_CHANCE = 0.25         # ...except this often, when they find YOU.
                             # This towering-encounter valve is a CONTRACT
                             # (deadly-but-avoidable), so it stays a flat
                             # roll -- the notice contest below never
                             # overrides it.
# Ordinary encounters (below the margin) run the NOTICE CONTEST instead of
# the old flat 25% spotted roll (ranged combat, 2026-07-16): each side
# rolls 2d6 + its notice stat against NOTICE_BASE + the OTHER side's
# conspicuousness (rpg.conspicuousness: group size, showy traits, the
# worst-DEX stealth term). The party watches with its best MIND; beasts and
# foes sense with the sharper of MIND and DEX. One side seeing alone =
# spotted (the sighting choice) or AMBUSHED (they open at their preferred
# range); both or neither = met square across the open field.
HUNT_LEVEL_REACH = 2         # a hunt stalks prey up to this far below the
                             # party's level (never above it)
HUNT_AMBUSH_CHANCE = 0.10    # ...but this often the hunter is the hunted
                             # (2026-07-10): the ambusher rolls off the ROAD's
                             # party-independent table (roll_wild_level -- any
                             # level, the higher the rarer), met blade-first
CAMP_ENCOUNTER_CHANCE = 0.10  # a night camped in the WILDS (not at a
                              # settlement) risks a visitor (2026-07-10):
                              # rolled after the night's recovery, same road
                              # table and spotted/ambush valves

def settlements_by_land(world: dict) -> dict[str, list[dict]]:
    """Settlement areas grouped by land, preserving world generation order."""
    out: dict[str, list[dict]] = {}
    for s in settlements(world):
        out.setdefault(s["land"], []).append(s)
    return out


def wild_pool(race: str) -> tuple[str, ...]:
    """What roams a land's wilderness: the union of every foe pool the
    race's quest templates draw from, deduplicated, level-sorted."""
    if race in LAND_SPECS:
        race = LAND_SPECS[race]["race"]
    kinds: set[str] = set()
    for tpl in TEMPLATES[race]:
        kinds.update(tpl["pool"])
    return tuple(sorted(kinds, key=lambda k: FOES[k].level))


def roll_wild_level(rng: random.Random) -> int:
    """The road's level table: geometric decay over 1..LEVEL_CAP -- any
    level can appear, the higher the rarer (party-independent)."""
    levels = range(1, LEVEL_CAP + 1)
    weights = [WILD_LEVEL_DECAY ** l for l in levels]
    return rng.choices(list(levels), weights=weights)[0]


def notice_contest(party: list, kinds: list[str],
                   rng: random.Random) -> tuple[bool, bool]:
    """Who saw whom first (the ordinary band's valve -- see the constants
    block above): returns (party_sees, foes_see). Each side rolls 2d6 + its
    notice stat vs NOTICE_BASE + the other side's conspicuousness."""
    watchers = [h for h in party if not h.dead]
    specs = [FOES[k] for k in kinds]
    party_notice = max((h.mind for h in watchers), default=0)
    foe_notice = max(max(s.mind, s.dex) for s in specs)
    party_sees = (rng.randint(1, 6) + rng.randint(1, 6) + party_notice
                  >= NOTICE_BASE + conspicuousness(specs))
    foes_see = (rng.randint(1, 6) + rng.randint(1, 6) + foe_notice
                >= NOTICE_BASE + conspicuousness(watchers))
    return party_sees, foes_see


def foes_preferred_field(kinds: list[str]) -> int:
    """The gap an AMBUSHING roster opens at: its longest reach -- shooters
    start shooting, casters start casting -- or 0 when it is all steel
    (melee ambushers are simply ON you, exactly the old met-blade-first)."""
    best = 0
    for k in kinds:
        spec = FOES[k]
        if spec.weapon is not None and spec.weapon.range:
            best = max(best, spec.weapon.range)
        if spec.school:
            best = max(best, CAST_RANGE)
    return best


def build_wild_encounter(level: int, race: str, rng: random.Random,
                         pool: tuple[str, ...] | None = None) -> list[str]:
    """One wilderness encounter at `level` from the land's pool: a full
    reference-encounter budget (share 1.0), boss allowance on -- the road
    fight is a whole outing, not a room share.

    `pool` overrides what roams here: a live world card's local
    encounter-table entry (2026-08-09, the economy floor) names its own
    rows -- the baron's toll-men, the loggers holding their camp, riders off
    the border. It never overrides the LEVEL, which stays the road's own
    party-independent roll."""
    return build_room(room_budget(level, 1.0), pool or wild_pool(race), rng,
                      final=True)


def wild_encounter_xp(level: int) -> int:
    """What a won road/hunt encounter pays: one encounter's share of a
    level-L three-fight quest. Below quest work on purpose (a road fight
    carries no turn-in lump) -- the wilds are the farm, the board is the
    game."""
    return quest_encounter_xp(level, 3)


def quest_to_sites(world: dict, quest: dict) -> list[Site]:
    """A quest's sites as sites.Site instances, so the batch sims can run a
    generated quest through the very same run_site loop the hand-built sites
    (and tune.py) use. Session play doesn't need this -- it fights rooms
    one command at a time. A delivery has no sites: empty list (the career
    sim and any other site iterator just walks past it)."""
    out = []
    for s in quest_sites(world, quest):
        rooms = site_rooms(world, s)
        out.append(Site(
            key=s["id"],
            level=s["level"],
            rooms=tuple((r["name"], tuple(r["kinds"])) for r in rooms),
            quest_line=f"{quest['name']} -- {s['name']}",
            spawn_phrase="{n} foes",
            abandon_line="the site is abandoned.",
            intro="",
        ))
    return out


# --------------------------------------------------------------------------- #
# Board / readout helpers (session.py and the CLI share these)
# --------------------------------------------------------------------------- #

def quest_shape(quest: dict) -> str:
    if quest.get("kind") == "delivery":
        return (f"a road delivery, {quest['days']} "
                f"day{'s' if quest['days'] > 1 else ''} out")
    enc = quest.get("encounters", 0)
    n = quest.get("site_count", len(quest.get("sites", [])))
    return (f"{n} site{'s' if n > 1 else ''}, "
            f"{enc} encounter{'s' if enc > 1 else ''}")

def level_grade(quest: dict) -> str:
    """The exact level column of a board row, or DELIVERY for a road job."""
    if quest.get("kind") == "delivery":
        return "DELIVERY"
    return f"L{quest['level']:<2}"


def quest_line(quest: dict, day: int | None = None) -> str:
    """One board row: id, exact level, shape, pay, status, and -- since
    2026-07-26, when `day` is given -- the clock. A delivery has
    no site level: DELIVERY stands where the level would (the road's danger
    is the road's own table)."""
    mark = {"open": "", "done": "  [DONE]",
            "failed": "  [FAILED]", "expired": "  [GONE]"}.get(
                quest["status"], "")
    if not mark and day is not None:
        note = deadline_note(quest, day)
        mark = f"  ({note})" if note else ""
    if quest.get("kind") == "delivery":
        return (f"[{quest['id']}] DELIVERY {quest['name']} -- to "
                f"{quest['dest_name']}, {quest_shape(quest)}; pays "
                f"{quest_gold_posted(quest)}g, "
                f"{quest_xp_posted(quest)} XP{mark}")
    dark = " DARK" if quest.get("align") == "dark" else ""
    xp_note = " (sin)" if dark else ""
    rw = quest.get("reward_weapon")
    pay = (f"pays a {rw['name']}" if rw
           else f"pays {quest_gold_posted(quest)}g")
    return (f"[{quest['id']}] {level_grade(quest)}{dark} "
            f"{quest['name']} -- "
            f"{quest_shape(quest)}; {pay}, "
            f"{quest_xp_posted(quest)} XP{xp_note}{mark}")


def board_lines(world: dict,
                settlement_key: str | None = None,
                day: int | None = None) -> list[str]:
    """The DM's quest inventory per settlement (2026-07-12: in play there
    is no board -- each row shows WHOSE job it is, and the ask-around
    funnel leads to that person, see dm.md). Levels always print exactly;
    `day` adds each posting's clock."""
    lines = []
    for s in settlements(world):
        if settlement_key and s["key"] != settlement_key:
            continue
        land_name = world["lands"][s["land"]]["name"]
        lines.append(f"{s['name']} ({land_name} {s['subtype']}):")
        for qid in s["quests"]:
            q = world["quests"].get(qid)
            if q is None:
                continue
            g = q.get("giver")
            who = f"    ({g['name']}, {g['role']})" if g else ""
            lines.append("  " + quest_line(q, day) + who)
        if not s["quests"]:
            lines.append("  (no work posted here just now)")
    return lines


def roster_kinds_line(kinds: list[str], skins: dict[str, str]) -> str:
    """A compact 'what you'd face' readout for a quest's detail view."""
    from collections import Counter
    counts = Counter(skins.get(k, FOES[k].display) for k in kinds)
    return ", ".join(f"{n}x {d}" if n > 1 else d for d, n in counts.items())


def quest_detail_lines(world: dict, quest: dict,
                       dm: bool = True, day: int | None = None) -> list[str]:
    """The full quest view. `dm=False` withholds surprise twists; all public
    quest and site levels still print exactly."""
    lines = [quest_line(quest, day), f"    {quest['desc']}"]
    rw = quest.get("reward_weapon")
    if rw:
        lines.append(f"    the reward: a {rw['name']} in place of the "
                     f"gold lump -- {rw['description']}")
    if day is not None and quest.get("deadline_day") is not None:
        band = quest_band(quest, day)
        lines.append(f"    due day {quest['deadline_day']} "
                     f"({deadline_note(quest, day)}); turned in now it pays "
                     f"{band} -- x{QUEST_PAY_BANDS[band]:g}")
    g = quest.get("giver")
    if g:
        lines.append(f"    giver: {g['name']}, {g['role']} ({g['race']} "
                     f"{g['sex']}, age {g['age']})")
    if quest.get("kind") == "delivery":
        lines.append(f"    the job: carry {quest['cargo']} to "
                     f"{quest['dest_name']} ({quest['days']} day(s) on the "
                     f"road) -- expect ONE interception en route; arriving "
                     f"is the turn-in")
        r = quest.get("recipient")
        if r:
            lines.append(f"    recipient: {r['name']}, {r['role']} "
                         f"({r['race']} {r['sex']}, age {r['age']})")
        return lines
    for i, s in enumerate(quest_sites(world, quest)):
        cur = quest["next"]
        site_l = f"L{s['level']}"
        d = s.get("deed")
        if d and not d.get("done"):
            # The deed is the JOB's known nature (the player took a
            # burglary, not a battle) -- shown in every view.
            lines.append(f"    site {i + 1} DEED first: {d['text']} -- "
                         f"the PC rolls 2d6+{d['stat'].upper()} vs DC "
                         f"{d['dc']}; a make does the site clean, a miss "
                         f"starts the fight (with witnesses)")
        t = s.get("twist")
        if t and not t.get("resolved") and dm:
            # The twist is a SURPRISE -- DM eyes only (the true view).
            lines.append(f"    site {i + 1} TWIST (DM eyes only): "
                         f"{t['text']} -- `settle` takes the terms at "
                         f"x{t.get('pay', 0.5):g} of the site lump; "
                         f"fighting on refuses them")
        rooms = site_rooms(world, s)
        for j, room in enumerate(rooms):
            rname, kinds = room["name"], room["kinds"]
            here = (quest["status"] == "open"
                    and cur["site"] == i and cur["room"] == j)
            mark = "  <- next" if here else ""
            boss = s.get("boss")
            led = (f" -- led by {boss['display']}"
                   if boss and j == len(rooms) - 1 else "")
            lines.append(f"    site {i + 1} '{s['name']}' ({site_l}) "
                         f"room {j + 1}: {rname} -- "
                         f"{roster_kinds_line(kinds, quest['skins'])}"
                         f"{led}{mark}")
    return lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--demo", action="store_true",
                    help="also dump every quest's full rosters")
    ap.add_argument("--day", type=int, default=0,
                    help="run the board's clock forward to this day first")
    args = ap.parse_args()
    world = generate_world(args.seed)
    rng = random.Random(args.seed)
    for day in range(1, args.day + 1):
        for s in settlements(world):
            expire_settlement_board(world, s, day)
            refresh_settlement_board(world, s, day, rng)
        refresh_deliveries(world, day, rng)
    total = sum(quest_xp_posted(q) for q in world["quests"].values())
    slots = sum(board_slots(s) for s in settlements(world))
    print(f"World (seed={args.seed}), day {args.day}: "
          f"{len(settlements(world))} settlements, "
          f"{len(world['quests'])} quests posted, {total} XP standing "
          f"(the board holds {slots} slots and refills as days pass; "
          f"a duo needs {xp_to_cap(1)} to L{LEVEL_CAP}).")
    print()
    for line in board_lines(world, day=args.day):
        print(line)
    print()
    print("The central cast:")
    from people import npc_line
    for npc in world["npcs"]:
        if npc.get("post") not in ("ruler", "sage", "wildcard"):
            continue
        land_name = world["lands"][npc["land"]]["name"]
        seat = world["areas"][npc["seat"]]["name"]
        print(f"  [{land_name}, at {seat}] {npc_line(npc)}")
    if args.demo:
        for q in list(world["quests"].values()):
            print()
            for line in quest_detail_lines(world, q, day=args.day):
                print(line)


if __name__ == "__main__":
    main()
