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
a stereotype of the settlement's race x a themed foe pool. Major questlines
(the conqueror, the hellish invasion) are deferred -- see plan.md.

Run:  python quests.py [--seed N]     # print a generated world's board
      python quests.py --demo         # also dump one quest's full rosters
"""

from __future__ import annotations

import argparse
import random

from rpg import (LEVEL_CAP, xp_to_next, site_xp_total, site_encounter_xp,
                 site_gold)
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

BANDIT_POOL = ("cutthroat", "archer", "bruiser")
LADDER_POOL = BANDIT_POOL + ("soldier", "veteran", "champion",
                             "blademaster", "warlord")
WOLF_POOL = ("wolf", "dire wolf")
BEAST_POOL = ("boar", "bear")
UNDEAD_POOL = ("skeleton", "ghoul", "wight")
GIANTKIN_POOL = ("ogre", "troll", "giant")
SPIDER_POOL = ("great spider",)
DRAKE_POOL = ("wyvern", "drake", "dragon")

TEMPLATES: dict[str, list[dict]] = {
    "human": [
        dict(title="Bandits on the King's Road",
             desc="Wagons stripped, a toll of blood at the fords. The reeve "
                  "pays for the road made safe.",
             pool=LADDER_POOL, skins={},
             sites=("the roadside camp", "the toll bridge", "the old fort")),
        dict(title="Wolves at the Folds",
             desc="Sheep gone, then a shepherd. The commons want the pack "
                  "dug out of the hills.",
             pool=WOLF_POOL, skins={},
             sites=("the high pasture", "the den in the hills")),
        dict(title="The Restless Crypt",
             desc="The churchyard dead are not staying put. The parish "
                  "purse opens for whoever settles them.",
             pool=UNDEAD_POOL, skins={},
             sites=("the churchyard", "the crypt below")),
        dict(title="Deserters Turned Raiders",
             desc="Soldiers who kept their steel and lost their oaths, "
                  "living off the villages they once guarded.",
             pool=LADDER_POOL, skins={"soldier": "Deserter",
                                      "veteran": "Deserter Sergeant"},
             sites=("the burned farmstead", "the deserters' camp")),
    ],
    "elf": [
        dict(title="The Blighted Glade",
             desc="Something soured the heartwood; what lives there now "
                  "bites. The wardens want it cut out.",
             pool=SPIDER_POOL + WOLF_POOL,
             skins={"great spider": "Gloomweaver",
                    "wolf": "Blight-Wolf", "dire wolf": "Blight-Alpha"},
             sites=("the glade's edge", "the heartwood")),
        dict(title="Webs in the Canopy",
             desc="The high walkways are silked over and the wardens who "
                  "went up have not come down.",
             pool=SPIDER_POOL, skins={"great spider": "Canopy Weaver"},
             sites=("the lower boughs", "the silked walkways")),
        dict(title="Beasts Maddened by the Blight",
             desc="Boar and bear alike gone wrong-eyed, tearing through "
                  "the outlying groves.",
             pool=BEAST_POOL, skins={"boar": "Blight-Boar",
                                     "bear": "Blight-Bear"},
             sites=("the torn grove", "the beast's harbor")),
        dict(title="Wardens Gone Rogue",
             desc="A warden-band that answers to no council now, taxing "
                  "the forest roads at arrowpoint.",
             pool=LADDER_POOL,
             skins={"archer": "Rogue Warden", "cutthroat": "Rogue Scout",
                    "soldier": "Rogue Warden", "veteran": "Warden-Captain",
                    "champion": "Blade of the Wild"},
             sites=("the forest road", "the rogue lodge")),
    ],
    "orc": [
        dict(title="The Proving Hunt",
             desc="The clan sets a beast worth a name. Bring back its hide "
                  "and the clan pays in iron and standing.",
             pool=BEAST_POOL + ("dire wolf",), skins={},
             sites=("the hunting ground", "the beast's lair")),
        dict(title="Rival Warband",
             desc="A rival clan's raiders cut the herd trails. The warchief "
                  "pays for them driven off or dead.",
             pool=LADDER_POOL,
             skins={"cutthroat": "Orc Raider", "archer": "Orc Skirmisher",
                    "bruiser": "Orc Breaker", "soldier": "Orc Raider",
                    "veteran": "Orc Blooded", "champion": "Orc Warchief",
                    "blademaster": "Orc Deathblade", "warlord": "Orc Overlord"},
             sites=("the raided trail", "the rival camp", "the war-tent")),
        dict(title="The Troll Under the Pass",
             desc="The mountain road pays tribute in carts and drivers. "
                  "The clans want the pass opened.",
             pool=GIANTKIN_POOL, skins={},
             sites=("the boulder field", "the cave under the pass")),
        dict(title="Wyvern on the Crags",
             desc="A shadow over the herds, and herders who point at the "
                  "high crags and will not climb.",
             pool=DRAKE_POOL, skins={},
             sites=("the scree slopes", "the crag eyrie")),
    ],
    "dwarf": [
        dict(title="Things in the Deep Roads",
             desc="The under-way to the second hold is silked and skittering. "
                  "The toll-guild pays by the cleared mile.",
             pool=SPIDER_POOL + WOLF_POOL,
             skins={"great spider": "Deep Creeper", "wolf": "Tunnel Hound",
                    "dire wolf": "Tunnel Stalker"},
             sites=("the toll gate", "the deep road", "the junction vault")),
        dict(title="The Flooded Hold",
             desc="An old hold, lost and lately dry again. What was buried "
                  "with it did not stay buried.",
             pool=UNDEAD_POOL,
             skins={"skeleton": "Drowned Delver", "ghoul": "Pale Delver",
                    "wight": "Hold-Lord"},
             sites=("the cracked gate", "the drowned galleries",
                    "the hold's heart")),
        dict(title="The Breaker in the Dark",
             desc="Something big moved into the worked seams and it does "
                  "not share. The mine masters want their tunnels back.",
             pool=GIANTKIN_POOL, skins={"ogre": "Deep Ogre",
                                        "troll": "Stone Troll"},
             sites=("the worked seam", "the broken gallery")),
        dict(title="The Grudge War",
             desc="A rival clan pressed an old grudge with new axes. The "
                  "ledger wants balancing.",
             pool=LADDER_POOL,
             skins={"cutthroat": "Grudge-Sworn", "archer": "Grudge-Sworn",
                    "bruiser": "Grudge-Sworn", "soldier": "Grudge-Sworn",
                    "veteran": "Oathbreaker", "champion": "Grudge-Captain",
                    "blademaster": "Grudge-Lord"},
             sites=("the contested gate", "the rival delving")),
    ],
    "goblin": [
        dict(title="Scrap-Hounds Loose in the Works",
             desc="The bosses' hound-pack slipped its chains and dens in "
                  "the gearworks. Pay docked for every eaten shift-worker.",
             pool=WOLF_POOL, skins={"wolf": "Scrap-Hound",
                                    "dire wolf": "Boiler Hound"},
             sites=("the scrapyard", "the gearworks floor")),
        dict(title="Press-Gang Trouble",
             desc="A rival boss's press-gang is stealing crews off the "
                  "night shift. The foreman pays for it stopped, no "
                  "questions on the how.",
             pool=LADDER_POOL,
             skins={"cutthroat": "Press-Ganger", "archer": "Sling-Runt",
                    "bruiser": "Pit Boss", "soldier": "Wrench-Guard",
                    "veteran": "Shift-Breaker", "champion": "Under-Boss",
                    "blademaster": "Knife-King", "warlord": "The Big Boss"},
             sites=("the night market", "the press-gang den",
                    "the boss's tower")),
        dict(title="The Engine Gone Feral",
             desc="They built it too big and fed it too well, and now the "
                  "lower works belong to it.",
             pool=GIANTKIN_POOL,
             skins={"ogre": "Breaker-Engine", "troll": "Furnace Hulk",
                    "giant": "The Great Machine"},
             sites=("the lower works", "the furnace hall")),
        dict(title="Spiders in the Undercity",
             desc="The vent shafts are webbed shut and the air below is "
                  "going bad. Small pay, small heroes welcome.",
             pool=SPIDER_POOL, skins={"great spider": "Vent Crawler"},
             sites=("the vent shafts", "the web-choked cistern")),
    ],
}

# Race-agnostic top-band work -- only the capital posts these, and only when
# the roll comes up high (template_band gates them to the drake band).
EPIC_TEMPLATES: list[dict] = [
    dict(title="The Dragon's Tithe",
         desc="A whole valley pays it tribute and calls that peace. The "
              "crown calls it rebellion with wings.",
         pool=DRAKE_POOL, skins={},
         sites=("the burned tithe-barns", "the mountain approach",
                "the hoard-cave")),
    dict(title="The Giant of the Border Marches",
         desc="Border forts flattened, garrisons walking home weaponless. "
              "The marshal wants the marches quiet again.",
         pool=GIANTKIN_POOL, skins={},
         sites=("the flattened fort", "the march camps", "the high steading")),
]

# Villages post the same race tables, just fewer and lower-leveled: samey on
# purpose -- placeholders for authored content, not competition for it.

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
    return sum(site_xp_total(s["level"]) for s in quest["sites"])


def quest_gold_total(quest: dict) -> int:
    return sum(site_gold(s["level"]) for s in quest["sites"])


def build_quest(qid: str, tpl: dict, settlement_key: str, level: int,
                rng: random.Random) -> dict:
    """One quest instance: 1-3 sites (weighted toward fewer), each 1-3 rooms,
    sites escalating to the quest's level (an S-site quest runs its earlier
    sites at level-1, level-2... floored at 1). Rewards are never stored --
    they derive from each site's level via rpg's formulas."""
    n_sites = rng.choices((1, 2, 3), weights=(45, 40, 15))[0]
    n_sites = min(n_sites, len(tpl["sites"]))
    stems = list(tpl["sites"][:n_sites])
    sites = []
    for j, stem in enumerate(stems):
        site_level = max(1, level - (n_sites - 1 - j))
        n_rooms = rng.choices((1, 2, 3), weights=(20, 40, 40))[0]
        rooms = build_site_rooms(site_level, n_rooms, tpl["pool"], rng)
        sites.append({"name": stem, "level": site_level,
                      "rooms": [[name, kinds] for name, kinds in rooms]})
    return {
        "id": qid,
        "name": tpl["title"],
        "desc": tpl["desc"],
        "settlement": settlement_key,
        "level": level,
        "skins": dict(tpl["skins"]),
        "sites": sites,
        "next": {"site": 0, "room": 0},     # the progress cursor
        "status": "open",
    }


def forge_quest(qid: str, level: int, n_sites: int, n_rooms: int,
                pool: tuple[str, ...], name: str, rng: random.Random,
                settlement_key: str = "") -> dict:
    """The DM's quest creator (session.py `forge`): level, shape, and foe
    kinds in -> a quest built by the same rules as worldgen and saved beside
    them. For improvised content the board doesn't cover."""
    tpl = dict(title=name, desc="(DM-forged)", pool=pool, skins={},
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


def _post_quest(world: dict, settlement: dict, rng: random.Random) -> dict:
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
    world: dict = {"seed": seed, "settlements": [], "quests": {}}

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
            _post_quest(world, settlement, rng)

    target = WORLD_XP_MARGIN * xp_to_cap(1)
    while (sum(quest_xp_total(q) for q in world["quests"].values()) < target
           and len(world["quests"]) < WORLD_MAX_QUESTS):
        _post_quest(world, rng.choice(world["settlements"]), rng)
    return world


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
AMBUSH_CHANCE = 0.25         # ...except this often, when they find YOU
HUNT_LEVEL_REACH = 2         # a hunt stalks prey up to this far below the
                             # party's level (never above it)

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
    one command at a time."""
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
    rooms = sum(len(s["rooms"]) for s in quest["sites"])
    n = len(quest["sites"])
    return (f"{n} site{'s' if n > 1 else ''}, "
            f"{rooms} encounter{'s' if rooms > 1 else ''}")

def quest_line(quest: dict) -> str:
    """One board row: id, level (straight -- reading it is the decision),
    shape, pay, status."""
    mark = {"open": "", "done": "  [DONE]"}[quest["status"]]
    return (f"[{quest['id']}] L{quest['level']:<2} {quest['name']} -- "
            f"{quest_shape(quest)}; pays {quest_gold_total(quest)}g, "
            f"{quest_xp_total(quest)} XP{mark}")


def board_lines(world: dict, settlement_key: str | None = None) -> list[str]:
    lines = []
    for s in world["settlements"]:
        if settlement_key and s["key"] != settlement_key:
            continue
        lines.append(f"{s['name']} ({s['race']} {s['kind']}):")
        for qid in s["quests"]:
            lines.append("  " + quest_line(world["quests"][qid]))
    return lines


def roster_kinds_line(kinds: list[str], skins: dict[str, str]) -> str:
    """A compact 'what you'd face' readout for a quest's detail view."""
    from collections import Counter
    counts = Counter(skins.get(k, FOES[k].display) for k in kinds)
    return ", ".join(f"{n}x {d}" if n > 1 else d for d, n in counts.items())


def quest_detail_lines(quest: dict) -> list[str]:
    lines = [quest_line(quest), f"    {quest['desc']}"]
    for i, s in enumerate(quest["sites"]):
        cur = quest["next"]
        for j, (rname, kinds) in enumerate(s["rooms"]):
            here = (quest["status"] == "open"
                    and cur["site"] == i and cur["room"] == j)
            mark = "  <- next" if here else ""
            lines.append(f"    site {i + 1} '{s['name']}' (L{s['level']}) "
                         f"room {j + 1}: {rname} -- "
                         f"{roster_kinds_line(kinds, quest['skins'])}{mark}")
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
    if args.demo:
        for q in world["quests"].values():
            print()
            for line in quest_detail_lines(q):
                print(line)


if __name__ == "__main__":
    main()
