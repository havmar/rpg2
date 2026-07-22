"""The quest & encounter generator -- structured combat content, worldgen.

sites.py holds the CATALOG (foe rows, the two hand-built anchor sites); this
file turns that catalog into a WORLD of quests: settlements with boards of
1-3-site quests, each site 1-3 encounters, every roster assembled from the
bestiary by its bench-calibrated level annotations. The design (2026-07):

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
  different every playthrough. Worldgen tops the board up until it carries
  enough total XP to take a duo from level 1 to LEVEL_CAP with margin --
  "enough structured content to max out" is asserted, not hoped.

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
import random

from rpg import (LEVEL_CAP, xp_to_next, site_xp_total, site_encounter_xp,
                 site_gold, conspicuousness, NOTICE_BASE, CAST_RANGE)
from sites import FOES, Site

# --------------------------------------------------------------------------- #
# The threat math (the encounter builder's whole theory)
# --------------------------------------------------------------------------- #

THREAT_BASE = 1.5   # one catalog level ~ x1.5 threat: calibrated on the
                    # barrow (4 skeletons ~ one level over 3) and checked by
                    # bench_quests.py across the whole 1-20 line
ROOM_SHARES = {     # a site's roster budget as ~2 at-level reference
                    # encounters, split over its rooms in rising shares --
                    # the hand-built sites' observed shape
    1: (1.25,),     # a one-room site is one HARD fight for full site pay
    2: (0.85, 1.10),
    3: (0.55, 0.70, 0.85),
}
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
WORLD_XP_MARGIN = 1.35  # the board must carry this x the XP a duo needs
                        # from level 1 to LEVEL_CAP -- surplus is grind
                        # room: a party that only took at-level work would
                        # die compounding the risk (bench_quests), so the
                        # board must hold enough BELOW-level work to climb on
WORLD_MAX_QUESTS = 60   # worldgen safety valve


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


# Room name stages -- generic on purpose; real flavor is the DM's layer.
ROOM_STAGES = ("the approach", "the way in", "the outer chamber",
               "the inner chamber", "the heart of it")


def build_site_rooms(level: int, n_rooms: int, pool: tuple[str, ...],
                     rng: random.Random) -> list[tuple[str, list[str]]]:
    """1-3 rooms escalating to the site's level: rising budget shares of the
    ~2-reference-encounter site total, the last room carrying the anchor."""
    shares = ROOM_SHARES[n_rooms]
    rooms = []
    for i, share in enumerate(shares):
        final = i == n_rooms - 1
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
# drake never at level 2. `sites` are name stems for the quest's 1-3 sites.
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
                      "again."),
        dict(title="Wolves Attack",
             desc="Wolves have killed sheep and a shepherd. Hunt the pack in "
                  "the hills and kill it.",
             pool=WOLF_POOL, skins={},
             sites=("the high pasture", "the den in the hills"),
             giver="the head shepherd",
             epilogue="The wolves are dead. No sheep are lost for the rest of "
                      "the season."),
        dict(title="The Restless Crypt",
             desc="The dead rise from the village graveyard. Enter the crypt "
                  "and destroy them.",
             pool=UNDEAD_POOL, skins={},
             sites=("the village graveyard", "the crypt below"),
             giver="the village priest",
             epilogue="The dead are destroyed. The priest blesses the graves "
                      "again."),
        dict(title="Deserter Raiders",
             desc="Army deserters are raiding the villages they once guarded. "
                  "Find their camp and stop them.",
             pool=LADDER_POOL, skins={"soldier": "Deserter",
                                      "veteran": "Deserter Sergeant"},
             sites=("the burned farm", "the deserters' camp"),
             giver="the army captain",
             epilogue="The deserters are defeated. Their weapons return to "
                      "the army."),
        dict(title="Renegade Wizards",
             desc="Renegade wizards have taken the tollhouse. They attack "
                  "travelers with fire and ice. Kill them and clear the road.",
             pool=CASTER_POOL, skins={},
             sites=("the tollhouse road", "the ruined guildhall"),
             giver="the bishop's mage hunter",
             epilogue="The wizards are dead. Travelers use the road again."),
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
                      "grove."),
        dict(title="Spiders in the Trees",
             desc="Giant spiders have covered the tree paths in webs. Several "
                  "wardens are missing. Clear the paths and find them.",
             pool=SPIDER_POOL, skins={"great spider": "Giant Tree Spider"},
             sites=("the lower branches", "the upper walkways"),
             giver="the walkway keeper",
             epilogue="The spiders are dead and the webs are gone. The "
                      "missing wardens are brought home."),
        dict(title="Blighted Beasts",
             desc="The blight has driven the boars and bears mad. They are "
                  "attacking the outer groves. Kill them.",
             pool=BEAST_POOL, skins={"boar": "Blighted Boar",
                                     "bear": "Blighted Bear"},
             sites=("the torn grove", "the beast den"),
             giver="the grove keeper",
             epilogue="The beasts are dead. The groves are safe again."),
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
                      "open again."),
        dict(title="The Mist Coven",
             desc="A group of mages stole forbidden songs from the circle. "
                  "Their magic covers the valley in mist. Find them and stop "
                  "the ritual.",
             pool=CASTER_POOL,
             skins={"hexer": "Mist Mage", "pyromancer": "Fire Mage"},
             sites=("the misty valley", "the stone circle"),
             giver="the circle elder",
             epilogue="The mages are dead. The mist fades from the valley."),
    ],
    "orc": [
        dict(title="The Great Hunt",
             desc="The clan has chosen a dangerous beast for the hunt. Kill "
                  "it and bring back its hide.",
             pool=BEAST_POOL + ("dire wolf",), skins={},
             sites=("the hunting grounds", "the beast den"),
             giver="the clan's lead hunter",
             epilogue="The hide hangs in the clan hall. The clan honors the "
                      "party."),
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
                      "safe again."),
        dict(title="Giants in the Pass",
             desc="Giants have blocked the mountain pass. They attack carts "
                  "and kill travelers. Find their cave and kill them.",
             pool=GIANTKIN_POOL, skins={},
             sites=("the boulder field", "the cave under the pass"),
             giver="the pass keeper",
             epilogue="The giants are dead. Carts use the mountain pass again."),
        dict(title="Dragon on the Mountain",
             desc="A dragon hunts the clan's herds from the high peaks. Climb "
                  "to its nest and kill it.",
             pool=DRAKE_POOL, skins={},
             sites=("the mountain slopes", "the dragon's nest"),
             giver="the clan elder",
             epilogue="The dragon is dead. The herds return to the mountain."),
        dict(title="Rebel Shamans",
             desc="A group of shamans has turned against the clan. They burn "
                  "the plains and attack the old shaman's followers. Defeat "
                  "them.",
             pool=CASTER_POOL,
             skins={"hexer": "Ice Shaman", "pyromancer": "Fire Shaman"},
             sites=("the burned plains", "the rebel camp"),
             giver="the clan shaman",
             epilogue="The rebels are defeated. Their ritual fire is put out."),
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
             epilogue="The monsters are dead. The deep road is open again."),
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
                      "sealed."),
        dict(title="Monster in the Mine",
             desc="A giant has taken over part of the mine. Kill it and clear "
                  "the tunnels.",
             pool=GIANTKIN_POOL, skins={"ogre": "Deep Ogre",
                                        "troll": "Stone Troll"},
             sites=("the mine tunnel", "the broken chamber"),
             giver="the mine foreman",
             epilogue="The monster is dead. The miners return to work."),
        dict(title="The Clan War",
             desc="A rival dwarf clan has attacked the gate and mine. Defeat "
                  "them and end the attack.",
             pool=DWARF_LADDER_POOL,
             skins={"cutthroat": "Rival Scout", "gunner": "Rival Gunner",
                    "bruiser": "Rival Brute", "soldier": "Rival Soldier",
                    "veteran": "Rival Veteran", "champion": "Rival Captain",
                    "blademaster": "Rival Swordmaster"},
             sites=("the main gate", "the mine entrance"),
             giver="the clan elder",
             epilogue="The rival clan is defeated. The fighting ends."),
        dict(title="Mages in the Mine",
             desc="A group of mages has opened a magic fire in a sealed mine. "
                  "Kill them and put out the fire.",
             pool=CASTER_POOL,
             skins={"hexer": "Ice Mage", "pyromancer": "Fire Mage"},
             sites=("the sealed mine", "the magic vault"),
             giver="the head runesmith",
             epilogue="The mages are dead. The vault is sealed again."),
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
                      "work."),
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
             epilogue="The gang is defeated. The workers return home safely."),
        dict(title="The Killer Machine",
             desc="A large machine has broken loose in the lower factory. "
                  "Destroy it.",
             pool=GIANTKIN_POOL,
             skins={"ogre": "Crusher Machine", "troll": "Furnace Machine",
                    "giant": "Great Machine"},
             sites=("the lower factory", "the furnace hall"),
             giver="the factory boss",
             epilogue="The machine is destroyed. The lower factory opens "
                      "again."),
        dict(title="Spiders Below",
             desc="Giant spiders have blocked the air shafts. Clear their "
                  "webs before the lower city runs out of air.",
             pool=SPIDER_POOL, skins={"great spider": "Giant Cave Spider"},
             sites=("the air shafts", "the old cistern"),
             giver="the air keeper",
             epilogue="The spiders are dead. Air flows into the lower city "
                      "again."),
        dict(title="The Boiler Cult",
             desc="A cult feeds workers to an old boiler. Enter their shrine "
                  "and kill them.",
             pool=CASTER_POOL,
             skins={"hexer": "Ice Tinker", "pyromancer": "Fire Tinker"},
             sites=("the boiler room", "the boiler shrine"),
             giver="the factory inspector",
             epilogue="The cult is gone. The old boiler is shut down."),
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
         epilogue="The dragon is dead. The valley keeps its harvest."),
    dict(title="The Giant at the Border",
         desc="A giant has destroyed several border forts. Track it to its "
              "stronghold and kill it.",
         pool=GIANTKIN_POOL, skins={},
         sites=("the ruined fort", "the border camp", "the giant's hall"),
         giver="the border commander",
         epilogue="The giant is dead. Soldiers return to the border forts."),
    dict(title="The Renegade Wizard",
         desc="A royal wizard has rebelled and taken control of a tower. Kill "
              "the wizard and stop the fires.",
         pool=MAGUS_POOL, skins={},
         sites=("the burned road", "the wizard's tower"),
         giver="the king's wizard",
         epilogue="The renegade wizard is dead. The tower goes dark."),
]

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
# point is BAD KARMA; karma.py). Dark quests never come from worldgen (the
# shadow board rolls them lazily, session.py), so no bench sees this knob.
DARK_GOLD_MULT = 1.5

DELIVERY_TEMPLATES: list[dict] = [
    dict(title="The Secret Message", cargo="a sealed letter",
         desc="A royal messenger never reached the next kingdom. Carry the "
              "sealed letter to the envoy. Enemies may try to take it.",
         giver="the head courier", recipient="the royal envoy",
         epilogue="The envoy reads the letter. More guards are sent to the "
                  "road."),
    dict(title="The Locked Chest", cargo="a locked chest",
         desc="A merchant guild must send payment to another city. Deliver "
              "the locked chest unopened.",
         giver="the guild agent", recipient="the merchant agent",
         epilogue="The chest arrives unopened. The guild records the party as "
                  "reliable."),
    dict(title="Medicine Delivery", cargo="a crate of medicine",
         desc="A plague has struck a city across the border. Deliver this "
              "medicine as quickly as possible.",
         giver="the town healer", recipient="the city healer",
         epilogue="The medicine reaches the sick. The number of deaths begins "
                  "to fall."),
    dict(title="The Smith's Delivery", cargo="a wrapped blade",
         desc="A smith has finished a sword for a buyer in another land. "
              "Deliver it safely.",
         giver="the master smith", recipient="the buyer",
         epilogue="The buyer accepts the sword. The job is complete."),
    dict(title="Return the Ashes", cargo="a sealed urn",
         desc="A traveler died far from home. Carry the ashes back to the "
              "family.",
         giver="the traveler's friend", recipient="the family",
         epilogue="The family buries the ashes. They thank the party."),
    dict(title="The Ransom Payment", cargo="a strongbox of ransom gold",
         desc="A town is paying to free a hostage across the border. Deliver "
              "the gold unopened.",
         giver="the town mayor", recipient="the kidnapper's agent",
         epilogue="The gold is delivered. The hostage is released."),
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
}


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


def quest_xp_total(quest: dict) -> int:
    if quest.get("kind") == "delivery":
        return quest["xp"]
    return sum(site_xp_total(s["level"]) for s in quest["sites"])


def quest_gold_total(quest: dict) -> int:
    if quest.get("kind") == "delivery":
        return quest["gold"]
    total = sum(site_gold(s["level"]) for s in quest["sites"])
    if quest.get("align") == "dark":
        total = round(total * DARK_GOLD_MULT)
    return total


def site_gold_for(quest: dict, site: dict) -> int:
    """One site's gold lump under the quest's alignment (the dark premium
    applies per site so the per-site pay and the board quote agree)."""
    gold = site_gold(site["level"])
    if quest.get("align") == "dark":
        gold = round(gold * DARK_GOLD_MULT)
    return gold


def build_quest(qid: str, tpl: dict, settlement_key: str, level: int,
                rng: random.Random) -> dict:
    """One quest instance: 1-3 sites (weighted toward fewer), each 1-3 rooms,
    sites escalating to the quest's level (an S-site quest runs its earlier
    sites at level-1, level-2... floored at 1). Rewards are never stored --
    they derive from each site's level via rpg's formulas."""
    n_sites = rng.choices((1, 2, 3), weights=(45, 40, 15))[0]
    n_sites = min(n_sites, len(tpl["sites"]))
    if tpl.get("deed") or tpl.get("twist"):
        # The caper shapes (karma.py's dark templates, 2026-07-19) are
        # AUTHORED, not rolled: the deed belongs to the first site and
        # the twist to the last, so every stem must stand.
        n_sites = len(tpl["sites"])
    stems = list(tpl["sites"][:n_sites])
    sites = []
    for j, stem in enumerate(stems):
        site_level = max(1, level - (n_sites - 1 - j))
        n_rooms = rng.choices((1, 2, 3), weights=(20, 40, 40))[0]
        rooms = build_site_rooms(site_level, n_rooms, tpl["pool"], rng)
        sites.append({"name": stem, "level": site_level,
                      "rooms": [[name, kinds] for name, kinds in rooms]})
    # The caper fields ride the site dicts (plain JSON, like everything):
    # deed on the FIRST site (the attempt comes before the fighting),
    # twist on the LAST (the complication waits at the end of the job).
    if tpl.get("deed"):
        sites[0]["deed"] = dict(tpl["deed"])
    if tpl.get("twist"):
        sites[-1]["twist"] = dict(tpl["twist"])
    return {
        "id": qid,
        "name": tpl["title"],
        "desc": tpl["desc"],
        "settlement": settlement_key,
        "level": level,
        "fuzz": rng.randint(-2, 2),     # quest sight (Magic & Mind): the
                                        # fixed error a dull-witted party
                                        # READS this job's level with --
                                        # rolled once so re-asking never
                                        # re-rolls it; clamped by the
                                        # party's best MIND (seen_level)
        "skins": dict(tpl["skins"]),
        "sites": sites,
        "next": {"site": 0, "room": 0},     # the progress cursor
        "status": "open",
        "align": tpl.get("align", "good"),  # karma & heat (2026-07-19):
                                            # whose XP bucket this work
                                            # pays into -- good burns bad
                                            # karma, dark accrues it
        "epilogue": tpl.get("epilogue", ""),
    }


def attach_giver(quest: dict, race: str, rng: random.Random,
                 role: str | None = None,
                 used_names: set[str] | None = None) -> None:
    """Put a face on a quest (2026-07-12): the person behind the job. In
    play there is NO board -- asking around funnels to this person in one
    message (dm.md), taking the quest is talking to them, and they receive
    the turn-in. Role comes from the template; the face is a targeted NPC
    (people.make_npc: race/role fixed, personality rolled). Stored as a
    plain dict on the quest, so it rides the save like everything else."""
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
    days = (TRAVEL_DAYS_IN_LAND if origin["race"] == dest["race"]
            else TRAVEL_DAYS_CROSS)
    return {
        "id": qid,
        "kind": "delivery",
        "name": tpl["title"],
        "desc": tpl["desc"],
        "cargo": tpl["cargo"],
        "settlement": origin["key"],
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


def forge_quest(qid: str, level: int, n_sites: int, n_rooms: int,
                pool: tuple[str, ...], name: str, rng: random.Random,
                settlement_key: str = "", align: str = "good") -> dict:
    """The DM's quest creator (session.py `forge`): level, shape, and foe
    kinds in -> a quest built by the same rules as worldgen and saved beside
    them. For improvised content the board doesn't cover. `align="dark"`
    forges a shadow job (karma & heat: bad-karma XP, the gold premium)."""
    tpl = dict(title=name, desc="(DM-forged)", pool=pool, skins={},
               align=align,
               sites=tuple(f"site {j + 1}" for j in range(n_sites)))
    quest = build_quest(qid, tpl, settlement_key, level, rng)
    # forge pins the shape exactly (build_quest rolls it): rebuild the sites
    # at the asked-for site count and room count.
    sites = []
    for j in range(n_sites):
        site_level = max(1, level - (n_sites - 1 - j))
        rooms = build_site_rooms(site_level, n_rooms, pool, rng)
        sites.append({"name": f"site {j + 1}", "level": site_level,
                      "rooms": [[rn, kinds] for rn, kinds in rooms]})
    quest["sites"] = sites
    return quest


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


def _cast_the_land(world: dict, race: str, seat: dict, rng: random.Random,
                   used_people: set[str]) -> None:
    from people import make_npc, SEXES     # runtime import (cycle: RACES)
    sex = rng.choice(SEXES)
    for role, post in ((RULER_TITLES[race][sex], "ruler"),
                       (rng.choice(SAGE_ROLES), "sage"),
                       (rng.choice(WILDCARD_ROLES), "wildcard")):
        # Rulers and sages skew old (a 20-year-old king every world read
        # wrong); the wildcard keeps the working-age roll.
        age = rng.randint(35, 70) if post in ("ruler", "sage") else None
        npc = make_npc(rng, race, role, sex=sex if post == "ruler" else None,
                       age=age, used_names=used_people)
        npc.update(land=race, seat=seat["key"], post=post)
        world["npcs"].append(npc)


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


def _post_quest(world: dict, settlement: dict, rng: random.Random,
                used_people: set[str] | None = None) -> dict:
    """Roll one quest onto a settlement's board: level uniform in the
    settlement band (displayed straight; too easy and too hard both happen),
    template drawn from the race's table (the capital also draws the epics)
    among those whose band contains the roll."""
    lo, hi = SETTLEMENT_KINDS[settlement["kind"]][1]
    level = rng.randint(lo, hi)
    tables = list(TEMPLATES[settlement["race"]])
    if settlement["kind"] == "capital":
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
    qid = f"q{len(world['quests']) + 1:02d}"
    quest = build_quest(qid, tpl, settlement["key"], level, rng)
    attach_giver(quest, settlement["race"], rng, role=tpl.get("giver"),
                 used_names=used_people)
    world["quests"][qid] = quest
    settlement["quests"].append(qid)
    return quest


def generate_world(seed: int | None = None) -> dict:
    """The whole playthrough's structured content, generated once: a capital,
    three towns (distinct races), villages as needed. The board is topped up
    -- an extra quest on a random settlement at a time -- until it carries
    WORLD_XP_MARGIN x the XP a duo needs to reach LEVEL_CAP, so a fresh
    world provably holds a full career of at-level work."""
    rng = random.Random(seed)
    used_names: set[str] = set()
    used_people: set[str] = set()   # one namespace for givers AND the cast:
                                    # two Ruriks in one town read as a bug
    world: dict = {"seed": seed, "settlements": [], "quests": {}, "npcs": []}

    races = list(RACES)
    rng.shuffle(races)
    plan = [("capital", races[0])] + [("town", r) for r in races[1:4]]
    plan += [("village", rng.choice(races)) for _ in range(2)]
    for kind, race in plan:
        name = _settlement_name(race, rng, used_names)
        settlement = {"key": name.lower(), "name": name, "race": race,
                      "kind": kind, "quests": []}
        world["settlements"].append(settlement)
        for _ in range(SETTLEMENT_KINDS[kind][0]):
            _post_quest(world, settlement, rng, used_people)

    for race, setts in lands(world).items():
        _cast_the_land(world, race, setts[0], rng, used_people)

    target = WORLD_XP_MARGIN * xp_to_cap(1)
    while (sum(quest_xp_total(q) for q in world["quests"].values()) < target
           and len(world["quests"]) < WORLD_MAX_QUESTS):
        _post_quest(world, rng.choice(world["settlements"]), rng,
                    used_people)

    # The deliveries go on last, ON TOP of the coverage target (courier work
    # is travel pay, not the climb's XP).
    for _ in range(DELIVERIES_PER_WORLD):
        _post_delivery(world, rng, used_people)
    return world


def _post_delivery(world: dict, rng: random.Random,
                   used_people: set[str] | None = None) -> dict:
    """Roll one cross-land delivery onto a random settlement's board: a
    destination in another land, a fresh template if one is left, a giver
    face at the origin and a RECIPIENT face at the destination (the
    hand-off is the turn-in scene)."""
    from people import make_npc     # runtime import (cycle: RACES)
    origin = rng.choice(world["settlements"])
    dests = [s for s in world["settlements"] if s["race"] != origin["race"]]
    dest = rng.choice(dests)
    posted = {q["name"] for q in world["quests"].values()
              if q.get("kind") == "delivery"}
    fresh = [t for t in DELIVERY_TEMPLATES if t["title"] not in posted]
    tpl = rng.choice(fresh or DELIVERY_TEMPLATES)
    qid = f"q{len(world['quests']) + 1:02d}"
    quest = build_delivery_quest(qid, tpl, origin, dest, rng)
    attach_giver(quest, origin["race"], rng, role=tpl.get("giver"),
                 used_names=used_people)
    quest["recipient"] = make_npc(rng, dest["race"], tpl["recipient"],
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
# worst-DEX stealth term). The party watches with its best MIND (the
# watchful mind -- MIND's third everyday job); beasts and foes sense with
# the sharper of MIND and DEX. One side seeing alone = spotted (the
# sighting choice) or AMBUSHED (they open at their preferred range); both
# or neither = met square across the open field.
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

# Wilderness place names, discovered by the explore move (race-neutral;
# the land's race colors the fiction, the DM colors the rest).
WILD_NAME_PARTS = (("Black", "Red", "Mist", "Thorn", "Crow", "Elk",
                    "Adder", "Howling", "Broken", "Old"),
                   ("fen", "hollow", "ridge", "wood", "moor", "caves",
                    "falls", "barrens", "tarn", "cairns"))


def lands(world: dict) -> dict[str, list[dict]]:
    """The map: race -> that land's settlements, in worldgen order. A land
    exists exactly when its race holds at least one settlement."""
    out: dict[str, list[dict]] = {}
    for s in world["settlements"]:
        out.setdefault(s["race"], []).append(s)
    return out


def wild_pool(race: str) -> tuple[str, ...]:
    """What roams a land's wilderness: the union of every foe pool the
    race's quest templates draw from, deduplicated, level-sorted."""
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


def build_wild_encounter(level: int, race: str,
                         rng: random.Random) -> list[str]:
    """One wilderness encounter at `level` from the land's pool: a full
    reference-encounter budget (share 1.0), boss allowance on -- the road
    fight is a whole outing, not a room share."""
    return build_room(room_budget(level, 1.0), wild_pool(race), rng,
                      final=True)


def wild_encounter_xp(level: int) -> int:
    """What a won road/hunt encounter pays: a level-L site's MIDDLE
    (streak-2) room rate -- 15 at L1, the historic off-script flat. Below
    quest work on purpose: the wilds are the farm, the board is the game."""
    return site_encounter_xp(level, 3, 2)


def quest_to_sites(quest: dict) -> list[Site]:
    """A quest's sites as sites.Site instances, so the batch sims can run a
    generated quest through the very same run_site loop the hand-built sites
    (and tune.py) use. Session play doesn't need this -- it fights rooms
    one command at a time. A delivery has no sites: empty list (the career
    sim and any other site iterator just walks past it)."""
    out = []
    for i, s in enumerate(quest["sites"]):
        out.append(Site(
            key=f"{quest['id']}/s{i + 1}",
            level=s["level"],
            rooms=tuple((rn, tuple(kinds)) for rn, kinds in s["rooms"]),
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
    rooms = sum(len(s["rooms"]) for s in quest["sites"])
    n = len(quest["sites"])
    return (f"{n} site{'s' if n > 1 else ''}, "
            f"{rooms} encounter{'s' if rooms > 1 else ''}")

def mind_precision(mind: int) -> int:
    """Quest sight (Magic & Mind, 2026-07-15): how blurry the party's read
    of a job's level is. The party's BEST MIND does the reading: 6 = the
    savant sees it exact; 4-5 = within a level; 3 and under = within two.
    This deliberately spends part of the old levels-shown-straight stance
    to make MIND matter to every party (design discussion; pay always
    follows the TRUE level -- only the READ blurs)."""
    if mind >= 6:
        return 0
    if mind >= 4:
        return 1
    return 2


def seen_level(quest: dict, mind: int | None) -> tuple[int, bool]:
    """The level the party READS off a quest: its true level shifted by the
    quest's stored fuzz, clamped to the reading MIND's precision. Returns
    (shown level, exact?). mind=None is the DM's true view (and the sims':
    they never pass a mind, so no bench number moves)."""
    level = quest["level"]
    if mind is None or quest.get("kind") == "delivery":
        return level, True
    p = mind_precision(mind)
    if p == 0:
        return level, True
    f = max(-p, min(p, quest.get("fuzz", 0)))
    return max(1, level + f), False


def level_grade(quest: dict, mind: int | None = None) -> str:
    """The level column of a board row: 'L7 ' exact, 'L~7' an estimate
    (quest sight), 'DELIVERY' for the road jobs."""
    if quest.get("kind") == "delivery":
        return "DELIVERY"
    shown, exact = seen_level(quest, mind)
    return f"L{shown:<2}" if exact else f"L~{shown}"


def quest_line(quest: dict, mind: int | None = None) -> str:
    """One board row: id, level (exact to a sharp MIND; an estimate --
    'L~7' -- to a dull one: quest sight), shape, pay, status. A delivery
    has no site level: DELIVERY stands where the level would (the road's
    danger is the road's own table)."""
    mark = {"open": "", "done": "  [DONE]"}[quest["status"]]
    if quest.get("kind") == "delivery":
        return (f"[{quest['id']}] DELIVERY {quest['name']} -- to "
                f"{quest['dest_name']}, {quest_shape(quest)}; pays "
                f"{quest_gold_total(quest)}g, "
                f"{quest_xp_total(quest)} XP{mark}")
    dark = " DARK" if quest.get("align") == "dark" else ""
    xp_note = " (bad karma)" if dark else ""
    return (f"[{quest['id']}] {level_grade(quest, mind)}{dark} "
            f"{quest['name']} -- "
            f"{quest_shape(quest)}; pays {quest_gold_total(quest)}g, "
            f"{quest_xp_total(quest)} XP{xp_note}{mark}")


def board_lines(world: dict, settlement_key: str | None = None,
                mind: int | None = None) -> list[str]:
    """The DM's quest inventory per settlement (2026-07-12: in play there
    is no board -- each row shows WHOSE job it is, and the ask-around
    funnel leads to that person, see dm.md). `mind` is the reading party's
    best MIND: with it, levels blur to quest sight (L~7); without it (the
    default -- the DM/demo view) they print true."""
    lines = []
    for s in world["settlements"]:
        if settlement_key and s["key"] != settlement_key:
            continue
        lines.append(f"{s['name']} ({s['race']} {s['kind']}):")
        for qid in s["quests"]:
            q = world["quests"][qid]
            g = q.get("giver")
            who = f"    ({g['name']}, {g['role']})" if g else ""
            lines.append("  " + quest_line(q, mind) + who)
    return lines


def roster_kinds_line(kinds: list[str], skins: dict[str, str]) -> str:
    """A compact 'what you'd face' readout for a quest's detail view."""
    from collections import Counter
    counts = Counter(skins.get(k, FOES[k].display) for k in kinds)
    return ", ".join(f"{n}x {d}" if n > 1 else d for d, n in counts.items())


def quest_detail_lines(quest: dict, mind: int | None = None) -> list[str]:
    """The full quest view. With `mind` (quest sight) the site levels shift
    by the same read error as the headline -- a blurred read is blurred
    consistently, it never leaks the truth through a sub-line."""
    lines = [quest_line(quest, mind), f"    {quest['desc']}"]
    shown, exact = seen_level(quest, mind)
    offset = shown - quest["level"]
    g = quest.get("giver")
    if g:
        traits = "; ".join(f"{k}: {v}" for k, v in g["traits"].items())
        lines.append(f"    giver: {g['name']}, {g['role']} ({g['race']} "
                     f"{g['sex']}, age {g['age']}; {traits})")
    if quest.get("kind") == "delivery":
        lines.append(f"    the job: carry {quest['cargo']} to "
                     f"{quest['dest_name']} ({quest['days']} day(s) on the "
                     f"road) -- expect ONE interception en route; arriving "
                     f"is the turn-in")
        r = quest.get("recipient")
        if r:
            traits = "; ".join(f"{k}: {v}" for k, v in r["traits"].items())
            lines.append(f"    recipient: {r['name']}, {r['role']} "
                         f"({r['race']} {r['sex']}, age {r['age']}; "
                         f"{traits})")
        return lines
    for i, s in enumerate(quest["sites"]):
        cur = quest["next"]
        site_l = (f"L{s['level']}" if exact
                  else f"L~{max(1, s['level'] + offset)}")
        d = s.get("deed")
        if d and not d.get("done"):
            # The deed is the JOB's known nature (the player took a
            # burglary, not a battle) -- shown in every view.
            lines.append(f"    site {i + 1} DEED first: {d['text']} -- "
                         f"the PC rolls 2d6+{d['stat'].upper()} vs DC "
                         f"{d['dc']}; a make does the site clean, a miss "
                         f"starts the fight (with witnesses)")
        t = s.get("twist")
        if t and not t.get("resolved") and mind is None:
            # The twist is a SURPRISE -- DM eyes only (the true view).
            lines.append(f"    site {i + 1} TWIST (DM eyes only): "
                         f"{t['text']} -- `settle` takes the terms at "
                         f"x{t.get('pay', 0.5):g} of the site lump; "
                         f"fighting on refuses them")
        for j, (rname, kinds) in enumerate(s["rooms"]):
            here = (quest["status"] == "open"
                    and cur["site"] == i and cur["room"] == j)
            mark = "  <- next" if here else ""
            boss = s.get("boss")
            led = (f" -- led by {boss['display']}"
                   if boss and j == len(s["rooms"]) - 1 else "")
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
    args = ap.parse_args()
    world = generate_world(args.seed)
    total = sum(quest_xp_total(q) for q in world["quests"].values())
    print(f"World (seed={args.seed}): {len(world['settlements'])} settlements, "
          f"{len(world['quests'])} quests, {total} XP on the board "
          f"(a duo needs {xp_to_cap(1)} to L{LEVEL_CAP}).")
    print()
    for line in board_lines(world):
        print(line)
    print()
    print("The central cast:")
    from people import npc_line
    for npc in world["npcs"]:
        print(f"  [{npc['land']} lands, at {npc['seat']}] {npc_line(npc)}")
    if args.demo:
        for q in world["quests"].values():
            print()
            for line in quest_detail_lines(q):
                print(line)


if __name__ == "__main__":
    main()
