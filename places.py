"""Persistent procedural places for RPG2.

The checked-in catalog contains the accepted ordinary content from
placegen.md.  This module owns deterministic materialization, lightweight
Room contents, knowledge, place mutation, and place-oriented readouts.  It
does not own encounter budgets or quest rewards.
"""

from __future__ import annotations

import hashlib
import heapq
import json
import random
import re
import textwrap
from collections import Counter, deque
from pathlib import Path
from typing import Iterable


CATALOG_PATH = Path(__file__).with_name("place_catalog.json")
EUROPE_MAP_PATH = Path(__file__).with_name("resources") / "europe_map.txt"
with CATALOG_PATH.open(encoding="utf-8") as _catalog_file:
    _CATALOG = json.load(_catalog_file)


# --------------------------------------------------------------------------- #
# The ground and the sky: climate, terrain, and the land's potential
# (2026-08-21, the tile economy arc's session 1)
# --------------------------------------------------------------------------- #
# AUTHOR THE PHYSICAL, DERIVE THE HUMAN. Two hand-painted overlays ride
# beside the base map -- `resources/europe_climate.txt` (the sky's zone) and
# `resources/europe_terrain.txt` (relief and drainage) -- and everything
# below falls out of them by law: how much of a tile a plow can touch, how
# much of that its people bother to clear, what wildwood survives the
# clearing, and what the ground is good for when the plow does badly. The
# overlays carry no rng and no seed, so this whole layer is identical in
# every campaign, exactly like the map it sits on.
#
# HIDDEN NUMBERS, VISIBLE WORDS: the fractions below are worldgen
# intermediates and are never stored. What a Tile keeps is its climate, its
# terrain, its `cover` word and its tag list -- which is all the rest of the
# game ever asks for.

CLIMATE_PATH = Path(__file__).with_name("resources") / "europe_climate.txt"
TERRAIN_PATH = Path(__file__).with_name("resources") / "europe_terrain.txt"
COUNTRY_PATH = Path(__file__).with_name("resources") / "europe_countries.txt"

# The overlay letters are FILE FORMAT ONLY: a Tile stores the full word.
CLIMATE_LETTERS = {
    "u": "tundra",
    "t": "taiga",
    "c": "continental",
    "o": "oceanic",
    "m": "mediterranean",       # the medieval DRY one (its bad year is dry)
    "w": "wet_mediterranean",   # the southern shore's Roman Warm regime
    "s": "steppe",
    "d": "desert",
    "n": "nile",                # river-fed floodplain granary
    "a": "alpine",              # exactly the mountain tiles
}
TERRAIN_LETTERS = {
    "p": "plains",
    "h": "hills",
    "w": "marsh",               # authored by hand, five and famous
    "m": "mountains",           # exactly the `^` tiles
}
CLIMATES = tuple(CLIMATE_LETTERS.values())
TERRAINS = tuple(TERRAIN_LETTERS.values())

# THE LABEL TABLE. One row per climate, and the row is what the rest of the
# game reads instead of a per-tile weather record.
#
#   `ffd`         frost-free days at the climate's REFERENCE row, before the
#                 latitude gradient below
#   `reference`   the map row that ffd is quoted at (None: no gradient --
#                 alpine is altitude, not latitude)
#   `yield`       the wheat multiplier: what an acre of this climate gives
#   `winter`      winter severity 0-3 (the snapshot arc's input, shipped now
#                 as data so that arc starts from an authority)
#   `harvest`     the day of the campaign year the crop comes in, or None
#                 where there is no crop. THE GAME IS STATIC IN TIME, so
#                 chronological difference becomes REGIONAL difference: the
#                 south is already reaping while the north is still weeding
#   `drought_days` how many rainless days THIS ground calls a drought. It is
#                 per-climate because a drought is a RELATIVE thing -- a
#                 fortnight without rain is a disaster in the shaded forest
#                 and an ordinary Tuesday in the dry south
CLIMATE_PROFILES = {
    "tundra": {"ffd": 60, "reference": 2, "yield": 0.0, "winter": 3,
               "harvest": None, "drought_days": 20},
    "taiga": {"ffd": 100, "reference": 4, "yield": 0.3, "winter": 3,
              "harvest": 125, "drought_days": 15},
    "alpine": {"ffd": 90, "reference": None, "yield": 0.15, "winter": 3,
               "harvest": 125, "drought_days": 15},
    "continental": {"ffd": 170, "reference": 8, "yield": 1.0, "winter": 2,
                    "harvest": 100, "drought_days": 18},
    "oceanic": {"ffd": 220, "reference": 8, "yield": 1.0, "winter": 1,
                "harvest": 110, "drought_days": 15},
    "mediterranean": {"ffd": 270, "reference": 13, "yield": 0.8, "winter": 0,
                      "harvest": 50, "drought_days": 30},
    "wet_mediterranean": {"ffd": 300, "reference": 17, "yield": 1.3,
                          "winter": 0, "harvest": 45, "drought_days": 25},
    "steppe": {"ffd": 160, "reference": 10, "yield": 0.5, "winter": 3,
               "harvest": 90, "drought_days": 25},
    "desert": {"ffd": 330, "reference": 17, "yield": 0.05, "winter": 0,
               "harvest": None, "drought_days": 40},
    "nile": {"ffd": 330, "reference": 18, "yield": 1.5, "winter": 0,
             "harvest": 40, "drought_days": 40},
}
FFD_PER_ROW = 8             # the latitude gradient: frost-free days gained
FFD_SPREAD = 40             # per row south of the reference, clamped +-this

CLIMATE_ARABLE = {          # fraction of this climate's ground a plow can
    "tundra": 0.00, "taiga": 0.10,      # ever touch, before relief says
    "continental": 0.65, "oceanic": 0.60,   # its word
    "mediterranean": 0.50, "wet_mediterranean": 0.60,
    "steppe": 0.35, "desert": 0.02,
    "nile": 0.85, "alpine": 0.05,
}
TERRAIN_ARABLE = {          # ...and what relief and drainage leave of that
    "plains": 1.00, "hills": 0.45, "mountains": 0.10, "marsh": 0.15,
}
ALLUVIAL_BONUS = 0.12       # a river tile's floodplain soils (marsh IS the
ARABLE_CAP = 0.90           # undrained floodplain, so it takes no bonus)
CLEARANCE_K = 0.20          # clearance = wheat / (wheat + K): how much of
                            # its potential a population bothers to realize.
                            # The two-pass deforestation sketch collapsed to
                            # this closed form -- the provisional population
                            # it wanted is itself a function of potential
                            # wheat, so the middle variable cancels
FOREST_CAP = {              # the wildwood: what nature forests, before man
    "tundra": 0.05, "taiga": 0.95, "continental": 0.85, "oceanic": 0.85,
    "mediterranean": 0.45, "wet_mediterranean": 0.55, "steppe": 0.08,
    "desert": 0.00, "nile": 0.05, "alpine": 0.50,
}
MARSH_WOOD = 0.5            # carr and fen scrub, never the full wildwood
GRAZE_CLIMATE = {           # the pastoral index: herding by climate law,
    "tundra": 0.15, "taiga": 0.15,      # no hand-picking (the steppe, the
    "continental": 0.35, "oceanic": 0.45,   # Mesta's med hills and the
    "mediterranean": 0.50, "wet_mediterranean": 0.40,   # alpine summer
    "steppe": 0.90, "desert": 0.05,     # pastures all read pastoral by law
    "nile": 0.10, "alpine": 0.35,       # alone)
}
GRAZE_TERRAIN = {
    "plains": 0.60, "hills": 0.90, "mountains": 0.60, "marsh": 0.30,
}
DEEP_FOREST_MIN = 0.55      # surviving forest >= this: deep forest, the
WOODED_MIN = 0.25           # wilderness; >= this: wooded (the forest tag)
FARMLAND_MIN = 0.30         # realized arable >= this: the farmland tag
PASTURE_MIN = 0.20          # pastoral >= this AND > realized arable
CHARACTER_TAGS = ("steppe", "desert", "tundra")     # the climate words that
                            # ARE ground character; the rest stay sky-only
HAND_MARKS = {              # authored character the law cannot see: extra
    (11, 19): ("pasture",),  # tags per (row, column). The one seeded mark
}                           # is the middle Danube's horse country
HAND_ALLUVIAL = {           # floodplain soils with no drawn river: the Po
    (12, 12), (12, 13), (12, 14),   # plain, whose lagoon river the map
}                           # redraw cut for looks -- the water still exists
HAND_FOREST = {             # THE EASTERN WILDWOOD. The deforestation law
    (7, 24), (7, 25),       # clears the continental east the way it clears
    (8, 24), (8, 25),       # the west, but history left the great forest
}                           # standing between the marsh and the frontier:
                            # a Bialowieza writ at map scale. Clearance is
HAND_FOREST_CLEARANCE = 0.25    # capped here and the wood stands


def frost_free_days(climate: str, row: int) -> int:
    """This tile's growing season: the climate's own, bent by latitude."""
    profile = CLIMATE_PROFILES[climate]
    base, reference = profile["ffd"], profile["reference"]
    if reference is None:
        return base
    return max(base - FFD_SPREAD,
               min(base + FFD_SPREAD, base + FFD_PER_ROW * (row - reference)))


def tile_economy(climate: str, terrain: str, river: bool,
                 row: int, column: int) -> dict:
    """One tile's derived numbers and its cover word, by law. The numbers
    are worldgen intermediates -- recomputable from the same authorities by
    any later layer, and never stored on the Tile."""
    arable = CLIMATE_ARABLE[climate] * TERRAIN_ARABLE[terrain]
    if terrain != "marsh" and (river or (row, column) in HAND_ALLUVIAL):
        arable += ALLUVIAL_BONUS
    arable = min(ARABLE_CAP, arable)
    base = CLIMATE_PROFILES[climate]["ffd"]
    wheat = (arable * CLIMATE_PROFILES[climate]["yield"]
             * frost_free_days(climate, row) / base)
    clearance = wheat / (wheat + CLEARANCE_K)
    if (row, column) in HAND_FOREST:
        clearance = min(clearance, HAND_FOREST_CLEARANCE)
    wildwood = FOREST_CAP[climate] * (MARSH_WOOD if terrain == "marsh"
                                     else 1.0)
    forest = wildwood * (1 - clearance)
    if forest >= DEEP_FOREST_MIN:
        cover = "deep forest"
    elif forest >= WOODED_MIN:
        cover = "wooded"
    else:
        cover = "open"
    return {"arable": arable, "wheat": wheat, "clearance": clearance,
            "realized": arable * clearance, "forest": forest,
            "pastoral": GRAZE_CLIMATE[climate] * GRAZE_TERRAIN[terrain],
            "cover": cover}


def derived_tags(economy: dict, climate: str, row: int,
                 column: int) -> list[str]:
    """The words the law adds to a land Tile, in their settled order. This
    is the vocabulary the quest tables were reconciled against: every word
    here is one a job may ask for and a natural Area can answer with."""
    tags = []
    if economy["cover"] != "open":
        tags.append("forest")
    if economy["realized"] >= FARMLAND_MIN:
        tags.append("farmland")
    if (economy["pastoral"] >= PASTURE_MIN
            and economy["pastoral"] > economy["realized"]):
        tags.append("pasture")
    if climate in CHARACTER_TAGS:
        tags.append(climate)
    for mark in HAND_MARKS.get((row, column), ()):
        if mark not in tags:
            tags.append(mark)
    return tags


LAND_SPECS = _CATALOG["lands"]
CULTURE_SPECS = _CATALOG["cultures"]
COUNTRIES = tuple(LAND_SPECS)
CULTURES = tuple(CULTURE_SPECS)
# Which shared content a country wears. A COUNTRY owns identity -- tiles, a
# capital, a tongue, name pools; a CULTURE owns the reusable content --
# settlement templates, natural inventories, quest tables, card packets.
CULTURE_OF = {country: spec["culture"] for country, spec in LAND_SPECS.items()}
CULTURE_LANDS = {culture: tuple(c for c in COUNTRIES
                                if CULTURE_OF[c] == culture)
                 for culture in CULTURES}
AREA_SPECS: dict[str, dict] = {}
SETTLEMENT_SITE_SPECS: dict[str, list[dict]] = {}
NATURAL_SITE_SPECS: dict[str, list[dict]] = {}

MAP_ROWS = 18
MAP_COLUMNS = 30
BIOME_GLYPHS = {".": "sea", "#": "basic", "^": "mountain",
                "~": "river"}
PINNED_BIOME_COUNTS = {"basic": 267, "mountain": 29, "river": 18,
                       "sea": 226}
# THE COUNTRY OVERLAY (2026-08-21, the medieval world arc's session 2): the
# fourth authored grid, one letter per LAND tile, `.` on the sea. It replaced
# the geometric three-way split -- a row test and a column test -- that the
# human contraction had left behind, and it is what makes the nine countries
# a picture rather than an arithmetic. Letters are file format only; a Tile
# stores the country key.
COUNTRY_LETTERS = {
    "p": "phyrascia", "s": "seraptania", "t": "teutonia", "h": "thule",
    "v": "vellisclavia", "b": "byzantium", "a": "andalusia", "u": "umaia",
    "g": "tergal",
}
PINNED_COUNTRY_BIOMES = {
    "phyrascia": {"basic": 12, "mountain": 1, "river": 0},
    "seraptania": {"basic": 21, "mountain": 0, "river": 2},
    "teutonia": {"basic": 20, "mountain": 5, "river": 3},
    "thule": {"basic": 30, "mountain": 7, "river": 0},
    "vellisclavia": {"basic": 58, "mountain": 2, "river": 0},
    "byzantium": {"basic": 37, "mountain": 5, "river": 9},
    "andalusia": {"basic": 14, "mountain": 3, "river": 0},
    "umaia": {"basic": 58, "mountain": 2, "river": 0},
    "tergal": {"basic": 17, "mountain": 4, "river": 4},
}
# ...and what the census law makes of the same nine bundles. The BAND is
# campaign-invariant (the score reads only the ground and the shoreline), so
# a country's shape in the six bands is authored data the same way its biome
# census is: it moves when the overlay is repainted and never otherwise.
PINNED_COUNTRY_BANDS = {
    "phyrascia": {"wilderness": 0, "thin": 2, "low": 0, "mid": 5,
                  "high": 6, "dense": 0},
    "seraptania": {"wilderness": 0, "thin": 0, "low": 2, "mid": 3,
                   "high": 16, "dense": 2},
    "teutonia": {"wilderness": 5, "thin": 0, "low": 7, "mid": 0,
                 "high": 13, "dense": 3},
    "thule": {"wilderness": 9, "thin": 24, "low": 0, "mid": 1,
              "high": 3, "dense": 0},
    "vellisclavia": {"wilderness": 18, "thin": 8, "low": 5, "mid": 15,
                     "high": 14, "dense": 0},
    "byzantium": {"wilderness": 1, "thin": 5, "low": 4, "mid": 21,
                  "high": 10, "dense": 10},
    "andalusia": {"wilderness": 1, "thin": 2, "low": 4, "mid": 6,
                  "high": 4, "dense": 0},
    "umaia": {"wilderness": 17, "thin": 3, "low": 0, "mid": 9,
              "high": 27, "dense": 4},
    "tergal": {"wilderness": 3, "thin": 3, "low": 8, "mid": 9,
               "high": 2, "dense": 0},
}
PINNED_LAND_COMPONENTS = (300, 11, 2, 1)

# The two overlays' own censuses, pinned the way the base map's is: this
# land is AUTHORED, and a repaint that moves a number is a decision, not a
# drift. The marsh five are pinned by NAME because five hand-placed tiles
# are content, not statistics.
PINNED_CLIMATE_COUNTS = {"tundra": 8, "taiga": 42, "continental": 83,
                         "oceanic": 28, "mediterranean": 46,
                         "wet_mediterranean": 32, "steppe": 24,
                         "desert": 18, "nile": 4, "alpine": 29}
PINNED_TERRAIN_COUNTS = {"plains": 213, "hills": 67, "marsh": 5,
                         "mountains": 29}
PINNED_MARSHES = {(6, 6): "the Fens",
                  (8, 11): "the Low Countries delta",
                  (9, 23): "the Pripet",
                  (9, 24): "the Pripet",
                  (11, 24): "the Danube delta"}
# ...and what the LAW makes of them: the derived tag census and the cover
# census, which move only when a constant above moves.
PINNED_TAG_COUNTS = {"farmland": 128, "pasture": 116, "forest": 101,
                     "steppe": 24, "desert": 18, "tundra": 8}
PINNED_COVER_COUNTS = {"open": 213, "wooded": 55, "deep forest": 46}

HISTORICAL_CITIES = (
    (5, 2, "Dublin", "phyrascia", "basic", False),
    (6, 5, "London", "phyrascia", "basic", True),
    (8, 11, "Amsterdam", "teutonia", "river", False),
    (9, 10, "Paris", "seraptania", "basic", True),
    (9, 18, "Prague", "teutonia", "basic", True),
    (3, 23, "Stockholm", "thule", "basic", True),
    (7, 28, "Moscow", "vellisclavia", "basic", True),
    (8, 22, "Warsaw", "vellisclavia", "basic", False),
    (10, 27, "Kyiv", "tergal", "river", True),
    (13, 3, "Lisbon", "andalusia", "basic", False),
    (13, 7, "Madrid", "andalusia", "basic", False),
    (14, 4, "Cordoba", "andalusia", "basic", True),
    (12, 14, "Venice", "byzantium", "basic", False),
    (14, 14, "Rome", "byzantium", "basic", False),
    (14, 19, "Athens", "byzantium", "basic", False),
    (14, 27, "Constantinople", "byzantium", "basic", True),
    (17, 12, "Carthage", "umaia", "basic", False),
    (16, 27, "Jerusalem", "umaia", "basic", False),
    (18, 24, "Cairo", "umaia", "basic", True),
)
HISTORICAL_BY_TILE = {(row, column): (name, country, biome, capital)
                      for row, column, name, country, biome, capital
                      in HISTORICAL_CITIES}

# --------------------------------------------------------------------------- #
# THE ROLLED WORLD (2026-08-21, the tile economy arc's session 2)
# --------------------------------------------------------------------------- #
# The ground above is AUTHORED and identical in every campaign. What follows
# is the half that is each world's own: the LAST HARVEST (round 1's second
# sitting) and the SETTLEMENT CENSUS (round 3), both rolled once at worldgen
# off derived seeds, both left alone afterwards. The bands and the laws are
# fixed, so France always feels like France; which tiles carry the towns, and
# where last year failed, are this world's business.

# --------------------------------------------------------------------------- #
# The last harvest
# --------------------------------------------------------------------------- #
# THE SCALE: 100 is a full excellent harvest. 110-120 legendary, 95-109
# excellent, 75-94 ordinary, 55-74 poor, 35-54 failed, below 35 apocalyptic.
# A tile is a PROBLEM tile below 75. The percent is STORED and the words are
# session 4's (`HARVEST_CAUSE_LINES` and the spoken scale) -- this layer
# keeps the number and the cause word only.
#
# The method is seeded contagion, not noise: a handful of regions, each with
# a CAUSE its center's climate can actually suffer, spreading outward into
# the ground that cause can hurt. A drought sweeps the steppe and dies at the
# oceanic border; the great rains rot the Atlantic coast and never reach the
# desert.

HARVEST_REGIONS = (4, 6)            # rolled uniformly, inclusive
HARVEST_SEPARATION = 4              # min manhattan distance between centers
CENTER_WEIGHT = {                   # who hosts trouble: rich reliable cores
    "mediterranean": 1.0,           # rarely, the dry and open margins often,
    "steppe": 1.0,                  # the tundra and the open desert never --
    "continental": 0.7,             # nothing grows there to lose
    "taiga": 0.5,
    "wet_mediterranean": 0.4,
    "oceanic": 0.3,
    "alpine": 0.3,
    "nile": 0.2,
    "tundra": 0.0,
    "desert": 0.0,
}
HARVEST_CAUSES = {                  # what a center's climate can suffer
    "mediterranean": (("drought", 0.8), ("rains", 0.2)),
    "steppe": (("drought", 0.6), ("frost", 0.3), ("rains", 0.1)),
    "wet_mediterranean": (("drought", 0.7), ("rains", 0.3)),
    "continental": (("rains", 0.45), ("drought", 0.35), ("frost", 0.2)),
    "oceanic": (("rains", 0.8), ("drought", 0.2)),
    "taiga": (("frost", 0.6), ("rains", 0.4)),
    "alpine": (("frost", 0.7), ("rains", 0.3)),
    "nile": (("rains", 1.0),),      # the Nile's only failure is the bad flood
    "tundra": (("frost", 1.0),),
    "desert": (("drought", 1.0),),
}
SUSCEPTIBILITY = {                  # how far a cause spreads into a climate
    "drought": {"mediterranean": 1.0, "steppe": 1.0, "desert": 1.0,
                "wet_mediterranean": 0.7, "continental": 0.5, "alpine": 0.3,
                "oceanic": 0.2, "nile": 0.15, "taiga": 0.1, "tundra": 0.1},
    "rains": {"oceanic": 1.0, "continental": 0.8, "taiga": 0.7,
              "alpine": 0.6, "nile": 0.5, "tundra": 0.4,
              "mediterranean": 0.3, "wet_mediterranean": 0.3, "steppe": 0.2,
              "desert": 0.0},
    "frost": {"taiga": 1.0, "tundra": 1.0, "alpine": 1.0, "continental": 0.7,
              "steppe": 0.7, "oceanic": 0.4, "mediterranean": 0.1,
              "wet_mediterranean": 0.0, "nile": 0.0, "desert": 0.0},
}
HARVEST_SPREAD = {1: 1.0, 2: 0.95, 3: 0.70, 4: 0.40, 5: 0.18}   # by ring
SEVERITY_CENTER = (30, 65)          # the core's harvest percent
SEVERITY_RING = 6                   # it softens this much per ring outward
SEVERITY_JITTER = 8                 # plus this much noise either way
SEVERITY_CLAMP = (25, 74)           # a problem tile stays a problem tile
GOOD_MEAN, GOOD_SIGMA = 90, 9       # the fine-year distribution elsewhere
GOOD_CLAMP = (75, 120)
LEGENDARY_CHANCE = 0.03             # ...with a rare 110-120 tail
HARVEST_PROBLEM = 75                # below this the tile is in trouble
# THE NEARBY TROUBLE NUDGE. Raw rolls put a region center within five path
# days of the start in only about half of worlds, and a campaign that opens
# nowhere near the year's trouble opens with nothing to walk toward. So when
# no center is in reach, the LAST-rolled region moves into that radius three
# times in four -- which lifts the played posture to about seven worlds in
# eight and leaves the genuinely quiet start standing as the eighth.
TROUBLE_DAYS = 5
TROUBLE_CHANCE = 0.75

# --------------------------------------------------------------------------- #
# The settlement census
# --------------------------------------------------------------------------- #
# THE SCALE DOCTRINE (2026-08-21, round 3 -- it will be asked about):
#   - A tile is SPOKEN OF as 30 km east-west by 60 km north-south (one
#     travel day east-west, two north-south; 1800 km2).
#   - The drawn map corresponds to real Europe at roughly 160 km per column
#     and 220 km per row (about 35,000 km2 per tile): the height is 1.4x the
#     width, NOT the 2x the travel costs suggest. The map is a deliberately
#     squashed Europe, and north-south travel is priced by the fictional
#     60 km, not the real 220.
#   - By AREA the game world is therefore about 20x smaller than the real
#     one (5.3x east-west, 3.7x north-south linear).
#   - Consequence, and the round's direction change: real, historical and
#     downscaled densities are NEVER an input. The tile is the unit, the
#     rolled census IS the population, and the tier words carry the scale.
#   - Slots: at most 4 per tile, thought of as a 2x2 lattice 15 km apart
#     east-west and 30 km north-south (twice as dense horizontally,
#     mirroring the travel anisotropy). A settlement every 15-30 km is the
#     medieval market-day spacing, and about four is what a head can hold.
#     Slots carry NO coordinates: the lattice is doctrine for fiction and
#     scale statements, never a stored position.
#
# THE FIVE TIERS and their fiction anchors -- headcounts the DM speaks with,
# never numbers the game stores:
#   hamlet      under a hundred souls
#   village     hundreds
#   town        thousands
#   city        tens of thousands
#   metropolis  a hundred thousand and more ("supercity" is dev slang)

TIERS = ("metropolis", "city", "town", "village", "hamlet")
TIER_LETTERS = {"M": "metropolis", "C": "city", "T": "town",
                "V": "village", "H": "hamlet"}
TIER_LETTERS_BY_TIER = {tier: letter for letter, tier in TIER_LETTERS.items()}
TIER_ORDER = "MCTVH"        # chief settlement first: slot 1 leads the tile
CITY_GRADE = ("metropolis", "city")     # the tiers that read as a great city

# THE SCORE, deterministic and NEVER stored: a relative number whose only
# job is to pick a band. Recomputable by any later arc from the same
# authorities, exactly like session 1's fractions.
PASTORAL_PEOPLE = 0.35      # herds feed fewer than fields per unit of index
FISH_COAST = 0.08           # the shore feeds people the plow never counted
FISH_RIVER = 0.05           # so does the river, half as well
TRANSPORT_FACTOR = 1.15     # grain moves by water: a river or coast tile can
                            # feed a settlement its own fields cannot
MARSH_MALUS = 0.60          # the fen fever
HIGHLAND_MALUS = 0.60       # the high ground holds fewer, past low arable
EAST_MALUS_START = 22       # the raiding frontier: columns past this lose
EAST_MALUS_STEP = 0.04      # this much per column...
EAST_MALUS_FLOOR = 0.65     # ...down to this floor
EAST_MALUS_LAST_ROW = 13    # the frontier is the STEPPE's reach: the southern
                            # sea-lane stripe (rows 14-18, the Nile granary
                            # included) is not raider country
HAND_DENSE = {              # score the law cannot see, authored:
    (8, 11),                # - the Low Countries delta reads as fen by law,
                            #   but its people drained it: the polders ARE
                            #   the land
    (12, 13), (12, 14),     # - the Lombardy-Veneto city belt: the redraw cut
                            #   the lagoon river for looks, and no law sees
                            #   the city culture of the Italian north
}
BANDS = (                   # score -> band; the census table's key
    (0.05, "wilderness"), (0.15, "thin"), (0.30, "low"),
    (0.50, "mid"), (0.82, "high"), (9.99, "dense"),
)
BAND_WORDS = tuple(band for _ceiling, band in BANDS)

# THE CENSUS TABLES: arrangement strings over the tier letters, weighted per
# band. THE VARIANCE IS IN THE TABLES -- every settled band keeps a
# village-only or emptier roll, so rich country never reads as a town grid,
# and only the dense band ever rolls a generated city. At most four letters
# anywhere, because four is the slot cap.
ARRANGEMENTS = {
    "wilderness": (("", 72), ("H", 18), ("V", 10)),
    "thin": (("", 25), ("H", 30), ("V", 20), ("HH", 12), ("VH", 13)),
    "low": (("V", 28), ("VH", 22), ("VV", 14), ("H", 12), ("VHH", 9),
            ("VVH", 8), ("", 7)),
    "mid": (("VV", 20), ("VVV", 15), ("VVH", 12), ("V", 12), ("VH", 10),
            ("TV", 8), ("VVVH", 8), ("T", 5), ("VVVV", 5), ("VHH", 5)),
    "high": (("TVV", 20), ("TV", 15), ("VVV", 15), ("TVVV", 10),
             ("VVVV", 10), ("VV", 10), ("T", 5), ("TT", 5), ("V", 5),
             ("VVH", 5)),
    "dense": (("CTV", 15), ("TTV", 15), ("TVV", 15), ("CT", 10),
              ("CVV", 10), ("TTVV", 10), ("TVVV", 10), ("CC", 5),
              ("CTT", 5), ("VVV", 5)),
}
SLOT_CAP = 4                # the 2x2 lattice: no tile seats a fifth place
# The authored answer key, NOT downscaled -- a metropolis is a real
# hundred-thousand city. A historical tile takes its own tier in slot 1 and
# draws its COMPANIONS from its own band's table, so Paris gathers towns and
# villages while Stockholm stands nearly alone in thin country.
HISTORICAL_TIERS = {
    "Paris": "metropolis", "Venice": "metropolis",
    "Constantinople": "metropolis", "Cairo": "metropolis",
    "London": "city", "Amsterdam": "city", "Prague": "city",
    "Moscow": "city", "Kyiv": "city", "Lisbon": "city", "Rome": "city",
    "Carthage": "city", "Cordoba": "city",
    "Dublin": "town", "Stockholm": "town", "Warsaw": "town",
    "Madrid": "town", "Athens": "town", "Jerusalem": "town",
}
# THE MINES, authored, few and famous (round 4's table, landing here as data
# for the SEATING it drives: a mine tile seats its mine town in slot 1, tier
# town, named by the mine, always free -- its mining law IS its charter).
# Session 3 gives the goods their whole trade reading.
MINES = {
    (9, 14): ("Goslar", ("silver", "copper")),      # the Rammelsberg
    (9, 19): ("Kutna Hora", ("silver",)),
    (3, 22): ("Falun", ("copper", "iron")),
    (10, 20): ("Banska Stiavnica", ("silver", "copper")),
    (10, 8): ("Melle", ("silver",)),
    (11, 14): ("Erzberg", ("iron",)),
    (13, 18): ("Novo Brdo", ("silver",)),
    (8, 16): ("Luneburg", ("salt",)),
    (10, 21): ("Wieliczka", ("salt",)),
}
# THE CHARTER AND THE MANOR, one stored word each, rolled with the census and
# read by NOTHING yet -- the politics arc owns what freedom is worth.
# Historically the distinction is law, not size: market towns held charters,
# and lords founded seigneurial towns precisely to farm the tolls.
CHARTER_CHANCE = 1 / 3      # a generated town holds a charter this often;
                            # cities and metropolises always do
MANOR_CHANCE = 0.5          # a village-led tile of 2+ settlements seats a
                            # resident lord this often (else the lord is
                            # absent and the tile answers to a distant seat)


def tile_score(economy: dict, terrain: str, coast: bool, river: bool,
               row: int, column: int) -> float:
    """One tile's population score, by law -- the hidden relative number
    whose only job is to pick a band. Never stored: any later arc recomputes
    it from the same authorities the way it recomputes `tile_economy`."""
    food = economy["realized"] + PASTORAL_PEOPLE * economy["pastoral"]
    if coast:
        food += FISH_COAST
    elif river:
        food += FISH_RIVER
    score = food
    if coast or river:
        score *= TRANSPORT_FACTOR
    if terrain == "marsh":
        score *= MARSH_MALUS
    elif terrain == "mountains":
        score *= HIGHLAND_MALUS
    if row <= EAST_MALUS_LAST_ROW:
        east = 1.0 - EAST_MALUS_STEP * max(0, column - EAST_MALUS_START)
        score *= max(EAST_MALUS_FLOOR, east)
    return score


def score_band(score: float, row: int, column: int) -> str:
    """The six-band bucket the census table is keyed on."""
    if (row, column) in HAND_DENSE:
        return "dense"
    for ceiling, band in BANDS:
        if score < ceiling:
            return band
    return "dense"

# --------------------------------------------------------------------------- #
# The trade network
# --------------------------------------------------------------------------- #
# (2026-08-21, the tile economy arc's session 3 -- round 4's design.) The
# last authored layer and the last derived one, in one pass. AUTHOR THE
# PHYSICAL, DERIVE THE HUMAN: the mines above and the goods colour below are
# hand-placed, few and famous; the land's own produce falls out of sessions
# 1-3's numbers by law; and the ordinary routes are COMPUTED between those
# origins and the census's markets by the same edge model the party walks.
#
# EXOTICS ARE GOODS LIKE ANY OTHER. Silk, spice, sugar and dyes have origin
# tiles on the map like wool does -- theirs are the frame's DOORS, the
# eastern gate and the delta port -- and they move on the five authored
# legendary roads because the door is the only place they enter, not because
# anything about them is off the board.

GOODS = ("grain", "wine", "wool", "horses", "timber", "furs", "wax",
         "silver", "copper", "iron", "salt", "herring", "amber",
         "cloth", "arms", "silk", "spice", "sugar", "dyes")
# The four words the layer stamps on a Tile. Unlike the ground's tags these
# are NOT the same in every campaign: `mine` is authored, but the three road
# words follow the routes, and the routes follow the rolled census.
TRADE_TAGS = ("mine", "trade-route", "port", "sea-lane")
GOODS_AUTHORED = {          # origin colour with no mine town under it: the
    (10, 5): ("salt",),             # the bay salt pans
    (11, 6): ("wine",),             # the western wine coast
    (6, 15): ("herring",),          # the Sound's herring fair
    (6, 22): ("amber",),            # the amber shore
    (8, 11): ("cloth",),            # the Low Countries' looms
    (13, 14): ("cloth",),           # the Tuscan looms
    (12, 13): ("arms",),            # the Lombard armourers
    (11, 19): ("horses",),          # the middle Danube horse fairs
    (11, 30): ("silk", "dyes"),     # the eastern gate (the Silk Road's door)
    (18, 24): ("spice", "sugar", "dyes"),   # the delta port
}
ENDPOINT_NAMES = {          # what a route endpoint is CALLED where no
    (11, 30): "the eastern gate",   # historical city and no mine town names
    (18, 24): "the delta port",     # it. Anything not named here or by the
    (18, 26): "the Nile granary",   # two answer keys reads as its coordinate
    (6, 22): "the amber shore",     # -- the rolled market has no name the
    (6, 15): "the Sound",           # party could know yet
    (10, 5): "the salt pans",
    (11, 6): "the wine coast",
    (8, 11): "the Low Countries' looms",
    (13, 14): "the Tuscan looms",
    (12, 13): "the armouries",
    (11, 19): "the horse fairs",
}

# THE DERIVED ORIGINS, by law over sessions 1-2's own numbers. The
# thresholds are deliberately high: an origin is a place that EXPORTS, and
# ordinary plain country that feeds itself and no one else is the map's
# baseline, not its trade.
DERIVED_GOODS = ("grain", "wine", "wool", "horses", "timber", "furs")
GRAIN_SURPLUS = 0.55        # realized arable at/above this exports grain:
                            # the alluvial river corridors and the Nile --
                            # ordinary plain country (~0.50) feeds itself
WINE_CLIMATES = ("mediterranean", "wet_mediterranean")      # the vine
WINE_MIN = 0.30
WOOL_CLIMATES = ("oceanic", "mediterranean")    # the sheep west's hill
WOOL_PASTORAL = 0.40                            # country
HORSE_PASTORAL = 0.40       # the steppe's herds (plus the authored fairs)
FUR_CLIMATES = ("taiga", "tundra", "continental")   # deep forest in the
                            # cold north and the eastern wildwood
MIN_PRODUCE_REGION = 2      # a derived produce region under this many
                            # contiguous tiles is local colour, never an
                            # export. Grain is exempt: one alluvial tile IS
                            # a granary. Timber moves by water only.

# WHERE EACH GOOD GOES: (destination kind, how many, the bulk range in
# days). Rich goods carry their own freight and take `None` -- silver walks
# to the crown's mint from anywhere, cloth and wine to the metropolises,
# arms to the capitals. Bulk stops when the cart stops paying.
#   markets       city-grade chiefs + the historical towns + the mine towns
#   cities        the same without the mine towns
#   metropolises  the three M chiefs
#   smiths        the cities plus the armouries
#   cloth         the two authored loom tiles
#   capital       the origin's OWN crown; capitals: all three
# Silk, spice, sugar, dyes and amber have no row: they move only on the
# legendary roads.
GOOD_ROUTES = {
    "grain": ("markets", 1, 8),
    "timber": ("markets", 1, 10),
    "furs": ("markets", 1, 12),
    "wax": ("markets", 1, 12),
    "salt": ("markets", 2, 8),
    "herring": ("markets", 2, 10),
    "wine": ("metropolises", 1, 12),
    "wool": ("cloth", 1, 12),
    "horses": ("capital", 1, 12),
    "silver": ("capital", 1, None),
    "copper": ("cities", 1, None),
    "iron": ("smiths", 1, None),
    "cloth": ("metropolises", 2, None),
    "arms": ("capitals", 2, None),
}
MINE_FOOD_DAYS = 6          # THE GRAIN ROAD. A mine whose own tile cannot
                            # feed it (realized arable under FARMLAND_MIN)
                            # eats from the nearest granary this far off:
                            # the food caravan, a route and a vulnerability
                            # in one stroke. Falun finds no grain in reach
                            # and stands UNFED by design -- the north's
                            # grain problem is real, and the DM has a
                            # standing story in it.

LEGENDARY = (               # authored endpoints and cargo; the line between
    {"name": "the Silk Road", "from": (11, 30), "to": (14, 27),
     "goods": ("silk", "dyes")},                # them is the same
    {"name": "the Spice Lane", "from": (18, 24), "to": (12, 14),
     "goods": ("spice", "sugar", "dyes")},      # pathfinder's, so a
    {"name": "the Amber Road", "from": (6, 22), "to": (12, 14),
     "goods": ("amber",)},                      # legendary road walks the
    {"name": "the Fairs Road", "from": (12, 14), "to": (9, 10),
     "goods": ("silk", "spice", "sugar")},      # ground everything else
    {"name": "the Grain Fleet", "from": (18, 26), "to": (14, 27),
     "goods": ("grain",)},                      # walks. Venice is the hub
)                                               # by construction: three of
                                                # the five meet there.


# --------------------------------------------------------------------------- #
# THE READ SURFACE (2026-08-21, the arc's session 4 -- round 5's design)
# --------------------------------------------------------------------------- #
# Everything above this line WRITES the tile. This is what SPEAKS it. The
# arc's standing rule -- hidden numbers, visible words -- lands here: the
# percent, the score and the yield stay worldgen intermediates, and what a
# page prints is one phrase and one word.

# THE CHARACTER LINE. One short phrase for what kind of country a Tile is,
# composed by fixed priority: the mine first (by its first metal), then the
# good the Tile is an origin of, then the land itself. ONE phrase, never a
# list -- composing a fuller sentence out of the tile's facts is the DM's
# job, not the code's.
TILE_CHARACTER = {          # a mine's metal or an origin's good -> the phrase
    "silver": "silver country", "copper": "copper country",
    "iron": "iron country", "salt": "salt country",
    "grain": "grain country", "wine": "wine country",
    "wool": "wool country", "horses": "horse country",
    "timber": "timber country", "furs": "fur country",
    "wax": "wax country", "cloth": "cloth country",
    "arms": "armourers' country", "dyes": "dye country",
    "herring": "the herring coast", "amber": "the amber shore",
    "silk": "the eastern gate",     # the two exotic DOORS are places, not
    "spice": "the delta port",      # products: what the country is there is
    "sugar": "the delta port",      # the gate itself
}
LAND_CHARACTER = (          # ...and the fall-through, in priority order:
    ("cover", "deep forest", "deep forest"),        # (field, value, phrase)
    ("terrain", "hills", "hill country"),
    ("terrain", "marsh", "fenland"),
    ("climate", "steppe", "the open steppe"),
    ("climate", "tundra", "bare tundra"),
    ("climate", "desert", "open desert"),
    ("tag", "farmland", "rich farmland"),
)                           # ...else the terrain's own plain word

# THE HARVEST WORDS, discharging round 1's parked fiction names. The stored
# percent is NEVER spoken -- not by the page and not by the DM. The scale is
# rules.md's: 100 is a full excellent harvest.
HARVEST_WORDS = ((110, "legendary"), (95, "excellent"), (75, "ordinary"),
                 (55, "poor"), (35, "failed"), (0, "apocalyptic"))
HARVEST_CAUSE_LINES = {"drought": "the drought",
                       "rains": "the great rains",
                       "frost": "the black frost"}
NILE_CAUSE_LINES = {"rains": "the low Nile"}    # on the Nile the failure of
                            # the flood is the failure of the rains upstream

# HOW MANY ROUTES THE PLAYER'S PAGE PRINTS (2026-08-21, session 3's finding:
# Paris carries fourteen). The named roads lead, the rest follow in route
# order, and the overflow reads as `+N more` the way the map legend's does.
# The DM's brief is uncapped -- it is a file, not a page.
ROUTE_LINES = 4

# THE TILE MENU (round 5's integration minimum). A STATIC factor beside the
# land's dynamic terms: the tile's own economy on the shelf, derived from
# what is already stored and never itself stored. Three rows only -- the
# ones a party can feel by walking a day.
TILE_MENU = {
    # bread is cheap at the granary: the mirror of grain-scarce's 1.50
    "grain": {"lodging": 0.90},
    # a strike at the pithead is the cheapest steel in the world, and it
    # STACKS under deposit-found, which is right
    "mine": {"steel": 0.90},
    # full shelves and full beds where the roads meet
    "crossroads": {"goods": 0.95, "lodging": 1.10},
}
CROSSROADS_ROUTES = 2       # routes crossing a Tile before it is a crossroads


# SPARSE ORDINARY BOARDS (2026-08-15, Local Quest Geography). A settlement
# is not a job dispenser: at materialization a stable derived roll decides
# whether this one normally posts ORDINARY generated work at all. A capital
# always does, a town usually does, a village usually does not -- and a
# village with no work is a correct village, not a bug. What the flag gates
# is `quests.board_slots` (ordinary capacity); the forced families --
# world-card jobs, deliveries, pact assignments, punishment and the
# DM's own forged work -- post at an inactive board regardless and never
# turn it into an active one. The starting settlement is forced active by
# `create_geography`, because the opening quest has to have somewhere to be.
BOARD_ACTIVE_CHANCE = {"capital": 1.00, "metropolis": 1.00,
                       "city": 1.00, "town": 0.60,
                       "village": 0.25, "hamlet": 0.05}
# The name reserves, drawn from at MATERIALIZATION and never at worldgen, so
# a pool has to cover what one playthrough walks into rather than what the
# census counts (~615 settlements a world). A tier that runs dry falls back
# to a numbered name. Metropolis carries no pool on purpose: the census rolls
# no generated one, and all four authored ones are named.
#
# The HAMLET pools take a humbler sound than the villages above them --
# Phyrascia's small endings (-cot, -stead, -hay, -garth), Byzantium's
# diminutives, Tergal's short camp words. A hamlet is under a hundred souls
# and its name should not sound like a market.
#
# ONE POOL PER COUNTRY, not per culture (2026-08-21, the nine): a name is
# the most country-shaped thing in the game, and Seraptania and Teutonia
# share a culture's card deck without sharing a syllable. Phyrascia keeps
# the old Firascir pools whole and Byzantium the old Mortellarian ones; the
# other six are authored here. These are invented sounds, not claims about
# any real language (writing.md).
SETTLEMENT_NAMES = {
    "phyrascia": {
        "city": ("Kingsmarch", "Highwater", "Greatbourne", "Stonegate",
                 "Crownford"),
        "town": ("Tomburgh", "Leehaven", "Walhaven", "Bradwhitchip",
                 "Redflurton"),
        "village": ("Sturford", "Ackham", "Flurham", "Sturham",
                    "Sturworth", "Newton", "Midton", "Aston", "Tomton",
                    "Walham", "Coldcot", "Thornley", "Blackton",
                    "Astmoor", "Ackbridge", "Ackton", "Mickleham",
                    "Shepham", "Coldbridge", "Thornham", "Bradmoor",
                    "Leeworth", "Shepton", "Blackford"),
        "hamlet": ("Ackcot", "Sturend", "Thornhay", "Walcroft",
                   "Oldstead", "Mickleshaw", "Redgarth", "Flurend",
                   "Blackhay", "Shepcot"),
    },
    "seraptania": {
        "city": ("Charmont", "Beauregarde", "Valcourt", "Roquefaille"),
        "town": ("Vaudrienne", "Montclaire", "Aubercy", "Fontenoy",
                 "Rochelieu", "Marnaville"),
        "village": ("Bercy", "Chalmont", "Doiselle", "Esquiac", "Fervais",
                    "Gournay", "Hautbois", "Livernay", "Malbois", "Noiret",
                    "Ourville", "Pierrefonds", "Quesnay", "Rouvres",
                    "Sancourt", "Thevray"),
        "hamlet": ("Petitbois", "Cormet", "Vaubry", "Loncet", "Marnet",
                   "Ferrat", "Ollier", "Chanay", "Brenot", "Grisel"),
    },
    "teutonia": {
        "city": ("Falkenau", "Steinbruck", "Hohenwald", "Reichenstadt"),
        "town": ("Eberfeld", "Wolfheim", "Grunbach", "Altmark",
                 "Rabenstein", "Lindenau"),
        "village": ("Ammerbach", "Birkenau", "Dornhof", "Eichgrund",
                    "Fuchsbach", "Gerstheim", "Hagenau", "Kirchdorf",
                    "Lammfeld", "Mohlen", "Nussbach", "Ochsenfurt",
                    "Rehberg", "Sandheim", "Tannwald", "Weidhof"),
        "hamlet": ("Krahenhof", "Steinkot", "Kleinbach", "Ulmen", "Espen",
                   "Rodung", "Winkel", "Halden", "Bruchen", "Sattel"),
    },
    "thule": {
        "city": ("Seljavik", "Hrafnstad", "Ulfsness", "Bjarnholm"),
        "town": ("Kvalfjord", "Eldvik", "Grimsstad", "Skarness",
                 "Ravnholm", "Isafell"),
        "village": ("Arnavik", "Birkdal", "Drangey", "Eyrarbakk",
                    "Fjardstad", "Gullvik", "Haukdal", "Ingvarstad",
                    "Jokulsa", "Kaldbak", "Langnes", "Myrdal", "Nordfjell",
                    "Reyrvik", "Svartkel", "Thorness"),
        "hamlet": ("Gardkot", "Naustby", "Selkot", "Vikby", "Hofstad",
                   "Baekkir", "Uthlid", "Snasa", "Verndal", "Kolgrof"),
    },
    "vellisclavia": {
        "city": ("Dubrov", "Mirogrod", "Zalesk", "Velibor"),
        "town": ("Novgrad", "Chernov", "Radomir", "Bystrica", "Ostrolek",
                 "Svetlograd"),
        "village": ("Berezno", "Borovica", "Chudovo", "Dolina", "Gorodok",
                    "Hrabno", "Ivanets", "Jelenka", "Kamenka", "Lipova",
                    "Malin", "Nizhny", "Olshany", "Peschany", "Ruda",
                    "Sosnovka", "Studna", "Toporov", "Uzhany", "Vishnya",
                    "Yavorov", "Zborov", "Krasnik", "Luhany"),
        "hamlet": ("Dubki", "Lipki", "Ruchey", "Zaton", "Kolno", "Mshany",
                   "Osina", "Peski", "Verba", "Zhitno"),
    },
    "andalusia": {
        "city": ("Torrelava", "Almazora", "Fuentebra", "Marvella"),
        "town": ("Castelmar", "Alvenda", "Monteclaro", "Sierrablanca",
                 "Puertoviejo", "Zafralba"),
        "village": ("Aldeanueva", "Bellavista", "Cabrillas", "Dosaguas",
                    "Encinar", "Foncalada", "Guadamar", "Higuera",
                    "Jarales", "Lomabaja", "Milagros", "Navalonga",
                    "Olivares", "Pinarejo", "Quintanar", "Retamosa"),
        "hamlet": ("Casilla", "Fuentina", "Majada", "Olivilla", "Pozuelo",
                   "Rincon", "Sotillo", "Ventorro", "Zarcita",
                   "Corralejo"),
    },
    "umaia": {
        "city": ("Al-Qasrin", "Al-Munya", "Madinat Sela", "Dar Nahir"),
        "town": ("Bir Hakla", "Wadi Sef", "Ras Amir", "Qalat Jubar",
                 "Ain Zafra", "Bab Ramla"),
        "village": ("Al-Basira", "Ain Dara", "Bir Salim", "Dar Aziza",
                    "El Qantar", "Ghadir Sef", "Hammam Nur", "Jebel Sidi",
                    "Kaf Nasir", "Wadi Lahm", "Marj Adin", "Nakhla",
                    "Ouled Barka", "Qasr Sabil", "Rashida", "Sidi Farhan",
                    "Tell Amara", "Umm Rayhan", "Wadi Nasim", "Yabis",
                    "Zawiya Halim", "Ain Tufayl", "Bir Khalaf",
                    "Dar Mansur"),
        "hamlet": ("Ain Kefr", "Bir Wahid", "Dar Sagir", "Kefr Zayd",
                   "Marj Sagir", "Qubba", "Ras Tin", "Sabkha", "Tell Rih",
                   "Zaytun"),
    },
    "byzantium": {
        "city": ("Aurelia", "Corvenza", "Palamare", "Serravalle",
                 "Tarenna"),
        "town": ("Castavera", "Portomera", "Belafonte", "Montaro"),
        "village": ("Alavera", "Beloro", "Calavento", "Doramonte",
                    "Fontela", "Lunaro", "Maravento", "Oliveta",
                    "Rosavera", "Sanoro", "Solavela", "Toralba",
                    "Valesero", "Ventoro", "Vilaro", "Aldovera",
                    "Cantoro", "Meravela", "Pontela", "Serovento",
                    "Valoro"),
        "hamlet": ("Casella", "Pozzino", "Fontina", "Solino", "Vallino",
                   "Roqueta", "Olivella", "Beloreta", "Sanino",
                   "Ventina"),
    },
    "tergal": {
        "city": ("Altan-Ordu", "Sarugan", "Khorgat", "Bayan-Tal",
                 "Temughal"),
        "town": ("Ulus-Gal", "Kharuk", "Temenur", "Ordubal"),
        "village": ("Aradun", "Balurun", "Borkal", "Enkhar", "Eshkar",
                    "Guratai", "Kharnam", "Kurugan", "Namuruk", "Ordaki",
                    "Sargul", "Teguren", "Tumengal", "Urkhal", "Zamutar",
                    "Batugan", "Chulun", "Erkhet", "Naranbal", "Sukhal",
                    "Tovkhar"),
        "hamlet": ("Ukhta", "Baruk", "Sarai", "Nogai", "Chagan", "Tolui",
                   "Kubai", "Ergen", "Zamut", "Khaya"),
    },
}


def slug(text: str) -> str:
    text = text.lower().replace("'", "")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def land_id(value: str) -> str:
    return value if value.startswith("land/") else f"land/{value}"


def tile_id(row: int, column: int) -> str:
    return f"tile/r{row:02d}/c{column:02d}"


def tile_coordinate(row: int, column: int) -> str:
    return f"R{row:02d}C{column:02d}"


def template_id(culture: str, role: str) -> str:
    """The catalog key of one CULTURE's settlement role. Never a runtime ID:
    a settlement Area is named by its SLOT and scoped under its Tile, so the
    template it was cut from has to live in a namespace of its own."""
    return f"template/settlement/{culture}/{role}"


def stable_seed(world_seed: int | None, parent_id: str, purpose: str,
                sequence: int) -> int:
    """Derive a process-independent child seed from stable ASCII inputs."""
    payload = f"{world_seed}|{parent_id}|{purpose}|{sequence}".encode("ascii")
    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(),
                          "big")


# THE NATURAL CHARACTER of a Tile: one word for what the ground IS, read
# off the two overlays and the deforestation law rather than off the base
# map's four glyphs (2026-08-21). It is the one authority behind both halves
# of a natural Area -- the name it carries and the site inventory it draws
# from -- so a Tile called Marshes cannot be stocked with windmills.
#
# The order is a priority: water beats ground, ground beats cover, and the
# `coast` character is the one that reads a POSITION, so a shore tile that
# would otherwise be plain countryside gets the country's coast inventory
# where it has one. `deep forest` and not merely `wooded` earns the forest
# character: a wooded tile still carries the `forest` TAG, which is what a
# job asking for woods matches on.
NATURAL_CHARACTERS = ("sea", "mountains", "river", "marsh", "forest",
                      "hills", "coast", "fields")
AREA_SUFFIXES = {"sea": "Sea", "mountains": "Mountains",
                 "river": "Riverlands", "marsh": "Marshes",
                 "forest": "Forest", "hills": "Hills",
                 "coast": "Countryside", "fields": "Countryside"}
AREA_CHARACTER_LINES = {
    "sea": "open sea",
    "mountains": "high mountain country",
    "river": "river country",
    "marsh": "fen and standing water",
    "forest": "deep forest",
    "hills": "hill country",
    "coast": "coastal countryside",
    "fields": "open countryside",
}
SEA_SITES = (
    {"id": "open-water", "name": "OPEN WATER", "rooms": [],
     "anchors": ["long swell", "distant gulls", "floating weed"]},
    {"id": "shoal", "name": "SHOAL", "rooms": [],
     "anchors": ["pale water", "sand below", "driftwood"]},
    {"id": "rocky-islet", "name": "ROCKY ISLET", "rooms": [],
     "anchors": ["black rocks", "tide pools", "bird nests"]},
)


def natural_character(tile: dict) -> str:
    """What this Tile's own ground is, in one word."""
    if tile["biome"] == "sea":
        return "sea"
    if tile["terrain"] == "mountains":
        return "mountains"
    if tile["biome"] == "river":
        return "river"
    if tile["terrain"] == "marsh":
        return "marsh"
    if tile["cover"] == "deep forest":
        return "forest"
    if tile["terrain"] == "hills":
        return "hills"
    if "coast" in tile["tags"]:
        return "coast"
    return "fields"


def natural_template(culture: str, character: str, row: int,
                     column: int) -> str:
    """The natural site inventory this ground draws from. A culture may
    author more than one per character -- the steppe's high ground is
    quarries or summer pasture -- and the pick alternates by POSITION, not by
    seed: the ground is the same in every campaign, and a checkerboard puts
    the two kinds next to each other instead of clumping them."""
    if character == "sea":
        return f"natural/{culture}/sea"
    keys = CULTURE_SPECS[culture]["natural"][character]
    return f"natural/{culture}/{keys[(row + column) % len(keys)]}"


def _build_definition_indexes() -> None:
    for culture, land in CULTURE_SPECS.items():
        for keys in land["natural"].values():
            for key in keys:
                NATURAL_SITE_SPECS[f"natural/{culture}/{key}"] = \
                    land["natural_sites"][key]
        NATURAL_SITE_SPECS[f"natural/{culture}/sea"] = [
            dict(spec) for spec in SEA_SITES]
        for role, spec in land["settlement_templates"].items():
            key = template_id(culture, role)
            AREA_SPECS[key] = {
                "id": key, "name": role, "kind": "settlement",
                "subtype": "town" if spec["tier"] == "capital"
                           else spec["tier"],
                "capital": spec["tier"] == "capital", "role": role,
                "tags": tuple(spec["tags"]),
                "fits": tuple(spec["fits"]),
                "description": spec["description"],
            }
            SETTLEMENT_SITE_SPECS[key] = spec["sites"]


_build_definition_indexes()


ROOM_CONTENT_POOLS = {
    "public_hall": ("long table", "raised seat", "benches", "wall banners",
                    "public notice board", "petition rail", "iron braziers"),
    "council": ("table", "chairs", "wall map", "account books",
                "contract box", "seal press", "locked chest"),
    "records": ("shelves", "document boxes", "ledgers", "road maps",
                "tax rolls", "spare ink", "seal box"),
    "market": ("stalls", "trading tables", "handcarts", "baskets",
               "awnings", "scales", "empty crates", "public notices"),
    "common_room": ("hearth", "tables and benches", "serving counter",
                    "ale barrels", "game board", "notice board", "coat pegs",
                    "stew pot"),
    "kitchen": ("cooking fire", "stove", "worktable", "iron pots", "knives",
                "crockery", "bread shelf", "water barrel"),
    "cellar": ("shelves", "racks", "ale barrels", "salt sacks",
               "root baskets", "smoked meat", "lamp"),
    "guest_room": ("bed", "bunks", "wash basin", "stool", "peg rail",
                   "blanket chest", "candle", "shuttered window"),
    "forge": ("forge", "anvil", "quench tub", "tool rack", "coal bin",
              "unfinished tools", "scrap basket", "bellows"),
    "shop": ("counter", "goods shelves", "baskets", "rope", "lamps",
             "crockery", "blankets", "tools", "food jars"),
    "alchemist_shop": ("counter", "bottle shelves", "mortar", "scales",
                       "dried herbs", "labeled jars", "locked cabinet"),
    "alchemist_work": ("workbench", "small furnace", "glass tubes",
                       "herb rack", "water basin", "charcoal box", "notes"),
    "guard": ("bench", "weapon rack", "duty board", "bell rope", "lanterns",
              "shield rack", "key board"),
    "landing": ("timber platform", "mooring posts", "rope coils",
                "cargo hook", "handcart", "fish baskets", "small crane"),
    "watch": ("stone parapet", "signal brazier", "warning bell",
              "arrow chest", "watch shelter"),
    "gate": ("timber gates", "portcullis", "guard bench", "weapon rack",
             "bell rope", "key board"),
    "bridge": ("stone roadway", "low parapets", "lamp posts",
               "drainage gaps", "cart ruts"),
    "stable": ("stalls", "hay rack", "water trough", "tack pegs",
               "feed bin", "pitchfork", "stable lantern"),
    "cargo": ("stacked crates", "barrels", "handcarts", "cargo net",
              "weighing scales", "tally board"),
    "fish_market": ("fish stalls", "cutting tables", "baskets",
                    "weighing scales", "salt barrels", "water buckets",
                    "canvas awnings"),
    "grain": ("grain sacks", "flour bins", "weighing scales",
              "tally board", "handcart", "grain scoops", "mouse traps"),
    "livestock": ("timber pens", "hitching rails", "water trough",
                  "feed baskets", "weighing gate", "straw"),
    "village_green": ("old tree", "stone well", "notice post", "benches",
                      "hitching rail", "water trough"),
    "ford": ("shallow water", "gravel bed", "marker posts", "guide rope",
             "muddy banks", "cart tracks"),
    "timber_yard": ("cut logs", "timber stacks", "splitting block",
                    "handcart", "saw frame", "wood chips"),
    "boat_yard": ("pulled-up skiffs", "trestles", "rope coils", "tar pot",
                  "spare planks", "oars"),
    "smokehouse": ("smoking racks", "fire trench", "fish hooks",
                   "salt barrel", "cutting table", "knives", "wood pile"),
    "courtyard": ("stone paving", "covered tables", "water basin",
                  "clay planters", "hitching rings", "canvas shade"),
    "oil_wine": ("olive baskets", "grape baskets", "stone press",
                 "wooden press", "clay jars", "barrel racks",
                 "wooden measures", "drain channel"),
    "fountain": ("carved basin", "iron spout", "water jars",
                 "stone bench", "drainage channel"),
    "pottery": ("clay jars", "stacked tiles", "potter's wheel",
                "drying shelves", "clay bins", "packing straw"),
    "gate_walk": ("timber walkway", "carved rails", "lantern hooks",
                  "warning bell", "root steps", "watch bench"),
    "warden": ("wall map", "duty board", "bow rack", "lantern shelf",
               "rope coils", "trail markers", "tool shed"),
    "craft": ("carving tables", "bow staves", "folded cloth",
              "herb baskets", "small awnings", "handcarts"),
    "herb": ("worktable", "drying rack", "labeled jars", "folded cloth",
             "water basin", "mortar", "locked cabinet"),
    "parts": ("parts bins", "rivet boxes", "gear wheels", "tool rack",
              "oil cans", "repair bench", "scrap baskets"),
    "metal": ("forge", "anvil", "quench barrel", "hand drill",
              "rivet tray", "scrap pile", "tool rack"),
    "brick": ("brick molds", "clay barrows", "stacked bricks",
              "charcoal baskets", "firing tongs", "water barrel"),
    "reed": ("reed bundles", "cutting knives", "drying racks",
             "woven mats", "cord bundles", "handcart"),
    "horse": ("timber pens", "hitching rails", "water troughs",
              "feed baskets", "tack racks", "tally board", "judging ring"),
    "tack": ("saddles", "rope halters", "folded blankets", "harness",
             "leather tools", "feed sacks"),
    "wool": ("wool bales", "shears", "weighing scales", "tally board",
             "packing cloth", "handcart"),
    "cistern": ("stone tank", "hand pump", "well rope", "water jars",
                "repair tools", "locked grate"),
    "caravan": ("wagons", "cargo stacks", "animal pens", "hitching rails",
                "cook fire", "tally board", "canvas shelters"),
    "yard": ("packed ground", "handcart", "water barrel",
             "stacked materials", "covered shelter"),
    "store": ("shelves", "crates", "barrels", "sacks", "lamp"),
    "work": ("workbench", "tool rack", "water bucket", "shelves",
             "waste basket"),
}

SITE_TEMPLATES = {
    "ordinary_house": {"domain": "built", "rooms": ("main-room",)},
    "camp": {"domain": "mixed", "room_roles": ("outer watch", "campfire",
                                                "leader's shelter")},
    "den": {"domain": "natural", "room_roles": ("tracks", "den",
                                                "deep den")},
    "road": {"domain": "mixed", "room_roles": ("road approach", "crossing",
                                               "road camp")},
    "crypt": {"domain": "built", "room_roles": ("graveyard", "crypt steps",
                                                "burial chamber")},
    "ruin": {"domain": "built", "room_roles": ("ruined yard", "broken hall",
                                               "inner chamber")},
    "mine": {"domain": "mixed", "room_roles": ("mine entrance", "work tunnel",
                                               "deep chamber")},
    "industrial": {"domain": "built", "room_roles": ("work yard",
                                                     "machine floor",
                                                     "boiler room")},
    "grove": {"domain": "natural", "room_roles": ("grove edge", "old trees",
                                                  "inner grove")},
    "tower": {"domain": "built", "room_roles": ("tower foot", "lower room",
                                                "upper room")},
    "shrine": {"domain": "mixed", "room_roles": ("shrine path", "outer altar",
                                                 "inner altar")},
    "wild": {"domain": "natural", "room_roles": ("trail", "open ground",
                                                 "lair")},
}


def _content_category(label: str) -> str:
    low = label.lower()
    if any(word in low for word in ("bread", "cheese", "onion", "stew",
                                     "fish", "meat", "apple", "olive",
                                     "mushroom", "curd", "pepper")):
        return "food"
    if any(word in low for word in ("chest", "box", "basket", "barrel",
                                     "sack", "crate", "jar", "bin")):
        return "container"
    if any(word in low for word in ("table", "bench", "chair", "stool",
                                     "bed", "shelf")):
        return "furniture"
    if any(word in low for word in ("knife", "axe", "hammer", "tool",
                                     "saw", "hook", "spade", "shears",
                                     "rake", "pickaxe")):
        return "tool"
    if any(word in low for word in ("letter", "token", "toy", "pipe",
                                     "portrait", "sewing")):
        return "personal"
    return "fixture"


def _content_records(room_id: str, labels: Iterable[str],
                     reveal: str = "visible") -> list[dict]:
    out = []
    for i, label in enumerate(dict.fromkeys(labels), 1):
        out.append({
            "id": f"{room_id}/content/{i}",
            "label": label,
            "category": _content_category(label),
            "reveal": reveal,
            "known": reveal == "visible",
        })
    return out


def _room_pool(name: str, site_name: str) -> str:
    low = name.lower()
    site_low = site_name.lower()
    if any(x in low for x in ("parts row", "parts store", "repair floor",
                              "tool row")):
        return "parts"
    if any(x in low for x in ("brick works", "brick shed",
                              "firing ground", "clay yard", "clay cut")):
        return "brick"
    if any(x in low for x in ("reed works", "cutting yard", "dry store",
                              "reed row")):
        return "reed"
    if any(x in low for x in ("horse market", "herd market", "herd yard",
                              "horse yard", "sheep pens", "goat pens")):
        return "horse"
    if any(x in low for x in ("tack row", "tack shed", "stable store")):
        return "tack"
    if any(x in low for x in ("wool row", "wool store")):
        return "wool"
    if any(x in low for x in ("cistern", "pump house", "water store",
                              "water tank", "stone well", "deep well")):
        return "cistern"
    if any(x in low for x in ("caravan yard", "trader's camp",
                              "wagon yard", "cargo store")):
        return "caravan"
    if any(x in low for x in ("oil and wine row", "press room",
                              "press house", "olive press", "wine press",
                              "jar store", "barrel store")):
        return "oil_wine"
    if any(x in low for x in ("stone fountain", "well")):
        return "fountain"
    if "courtyard" in low:
        return "courtyard"
    if any(x in low for x in ("pottery", "jar store")):
        return "pottery"
    if any(x in low for x in ("gate walk", "raised walk")):
        return "gate_walk"
    if any(x in low for x in ("warden post", "forester's yard",
                              "equipment store")):
        return "warden"
    if "craft row" in low:
        return "craft"
    if any(x in low for x in ("herb room", "healer's room", "herb shop")):
        return "herb"
    if any(x in low for x in ("cargo yard", "cargo walk", "loading yard",
                              "foreign yard")):
        return "cargo"
    if any(x in low for x in ("fish market", "fish stalls", "fish row",
                              "fish landing", "salt row", "fish house",
                              "fish shed", "cutting room", "net store",
                              "net yard")):
        return "fish_market"
    if any(x in low for x in ("grain row", "grain store", "grain house",
                              "weighing room")):
        return "grain"
    if any(x in low for x in ("livestock yard", "animal pens",
                              "goat yard", "corral", "sheepfold")):
        return "livestock"
    if any(x in low for x in ("village green", "village circle", "old oak",
                              "old beech", "old tree", "notice post")):
        return "village_green"
    if any(x in low for x in ("ford", "river crossing")):
        return "ford"
    if any(x in low for x in ("timber yard", "log yard", "wood yard")):
        return "timber_yard"
    if any(x in low for x in ("boat yard", "boat shed", "net yard")):
        return "boat_yard"
    if any(x in low for x in ("smoke room", "smokehouse", "salt store")):
        return "smokehouse"
    if any(x in low for x in ("public hall", "throne hall", "great hall",
                              "hill council", "duty room", "public counter",
                              "toll room")):
        return "public_hall"
    if "council room" in low or "contract room" in low:
        return "council"
    if any(x in low for x in ("records room", "map room")):
        return "records"
    if "common room" in low:
        return "common_room"
    if "kitchen" in low:
        return "kitchen"
    if "cellar" in low or "food store" in low:
        return "cellar"
    if "guest room" in low or "private room" in low:
        return "guest_room"
    if low == "forge":
        return ("metal" if "metal shop" in site_low or "metal shed" in site_low
                else "forge")
    if "alchemist" in site_low and low == "shop":
        return "alchemist_shop"
    if "alchemist" in site_low and ("work" in low or "locked" in low):
        return "alchemist_work" if "work" in low else "store"
    if "sales room" in low or low == "shop":
        return "shop"
    if any(x in low for x in ("guard room", "duty room")):
        return "guard"
    if any(x in low for x in ("signal platform", "watch platform", "lookout",
                              "wall walk", "roof walk", "harbor wall")):
        return "watch"
    if any(x in low for x in ("gate passage", "gatehouse", "gate walk",
                              "west gate", "east gate")):
        return "gate"
    if "bridge" in low:
        return "bridge"
    if "stable" in low or "animal pens" in low or "goat shed" in low:
        return "stable"
    if any(x in low for x in ("landing", "quay", "jetty", "harbor steps",
                              "river steps", "harbor stairs")):
        return "landing"
    if any(x in low for x in ("row", "market", "stalls", "square",
                              "village green", "village circle")):
        return "market"
    if "store" in low or "locked" in low or "equipment" in low:
        return "store"
    if any(x in low for x in ("yard", "floor", "works", "shed", "room",
                              "house", "office")):
        return "work"
    return "yard"


def _choose_pool_contents(room_seed: int, pool_id: str) -> list[str]:
    rng = random.Random(room_seed)
    pool = list(ROOM_CONTENT_POOLS[pool_id])
    rng.shuffle(pool)
    return pool[:rng.randint(2, min(4, len(pool)))]


def generic_room_contents(room_id: str, room_name: str, site_name: str,
                          seed: int) -> tuple[str, list[dict]]:
    """Resolve a concrete Room role through the shared fallback catalog."""
    pool_id = _room_pool(room_name, site_name)
    return pool_id, _content_records(
        room_id, _choose_pool_contents(seed, pool_id))


def _new_area_record(spec: dict, polity: str, tile: dict,
                     world_seed: int | None, index: int,
                     source: str = "authored") -> dict:
    aid = spec["id"]
    is_settlement = spec["kind"] == "settlement"
    tags = list(spec["tags"])
    if is_settlement:
        tags.extend(("settlement", spec["subtype"], CULTURE_OF[polity],
                     polity))
    capital = bool(spec.get("capital"))
    return {
        "id": aid, "key": aid, "name": spec["name"],
        "land": polity, "tile": tile["id"], "kind": spec["kind"],
        "subtype": spec["subtype"], "capital": capital,
        "culture": CULTURE_OF[polity], "homeland": polity,
        "role": spec["role"], "description": spec["description"],
        "source": source, "template": aid,
        "seed": stable_seed(world_seed, tile["id"], "area", index),
        "known": is_settlement, "visited": False,
        "sites": [], "quests": [], "tags": list(dict.fromkeys(tags)),
        "features": [], "states": [], "used_natural_sites": [],
        "natural_site_order": [], "services": [], "links": [],
        "sequences": {},
    }


def _new_land_record(polity: str, spec: dict, world_seed: int | None,
                     index: int) -> dict:
    lid = f"land/{polity}"
    return {
        "id": lid, "key": polity, "name": spec["name"], "owner": polity,
        "culture": spec["culture"], "homeland": polity,
        "description": spec.get("description", ""),
        "seed": stable_seed(world_seed, "world", "land", index),
        "areas": [], "tiles": [], "settlement_slots": [],
        "features": [], "states": [], "sequences": {},
    }


def _site_template(name: str, domain: str = "built") -> str:
    low = name.lower()
    if any(x in low for x in ("camp", "warband")):
        return "camp"
    if any(x in low for x in ("den", "nest", "lair")):
        return "den"
    if any(x in low for x in ("road", "path", "track", "crossing", "bridge",
                              "pass", "ford")):
        return "road"
    if any(x in low for x in ("grave", "crypt", "burial", "tomb")):
        return "crypt"
    if any(x in low for x in ("ruin", "abandoned", "wreck")):
        return "ruin"
    if any(x in low for x in ("mine", "quarry", "cave")):
        return "mine"
    if any(x in low for x in ("factory", "machine", "boiler", "works",
                              "kiln", "forge")):
        return "industrial"
    if any(x in low for x in ("grove", "forest", "wood")):
        return "grove"
    if any(x in low for x in ("tower", "watch", "lookout")):
        return "tower"
    if any(x in low for x in ("shrine", "temple", "altar")):
        return "shrine"
    return "wild" if domain == "natural" else slug(name)


def _materialize_room(world: dict, site: dict, room_spec: dict, sequence: int,
                      *, source: str = "worldgen", known: bool = False) -> dict:
    rid = f"{site['id']}/{room_spec['id']}"
    seed = stable_seed(world["seed"], site["id"], "room", sequence)
    anchors = list(room_spec.get("anchors", ()))
    pool_id = None
    if not anchors:
        pool_id = _room_pool(room_spec["name"], site["name"])
        if pool_id not in ROOM_CONTENT_POOLS:
            raise ValueError(f"Room has no content definition: {rid}")
        anchors = _choose_pool_contents(seed, pool_id)
    room = {
        "id": rid, "name": room_spec["name"], "site": site["id"],
        "template": room_spec.get("id", slug(room_spec["name"])),
        "role": room_spec.get("id", slug(room_spec["name"])),
        "content_pool": pool_id, "source": source, "seed": seed,
        "known": known, "visited": False,
        "contents": _content_records(rid, anchors),
        "features": [], "states": [], "occupants": [], "kinds": [],
        "quest_ids": [],
    }
    world["rooms"][rid] = room
    site["rooms"].append(rid)
    return room


def materialize_site(world: dict, area: dict, spec: dict, *,
                     source: str, domain: str, known: bool,
                     purpose: str, level: int | None = None) -> dict:
    sequence = area["sequences"].get(purpose, 0) + 1
    area["sequences"][purpose] = sequence
    template = _site_template(spec["name"], domain)
    sid = f"{area['id']}/site/{slug(spec['name'])}/{sequence}"
    seed = stable_seed(world["seed"], area["id"], purpose, sequence)
    site = {
        "id": sid, "name": spec["name"], "area": area["id"],
        "domain": domain, "template": template,
        "description": spec.get("description", ""), "source": source,
        "seed": seed, "known": known, "visited": False, "rooms": [],
        "quest_ids": [], "level": level, "tags": [template, domain],
        "features": [], "states": [], "services": [], "occupants": [],
        "contents": _content_records(
            f"{sid}/scene", spec.get("anchors", ())),
        "sequences": {},
    }
    world["sites"][sid] = site
    area["sites"].append(sid)
    for i, room_spec in enumerate(spec.get("rooms", ()), 1):
        _materialize_room(world, site, room_spec, i, source=source)
    return site


def _service_kind(site_name: str) -> list[str]:
    low = site_name.lower()
    out = []
    if "inn" in low:
        out.append("lodging")
    if any(x in low for x in ("smith", "forge", "metal shop", "metal shed")):
        out.append("smith")
    if "general shop" in low or "general store" in low:
        out.append("general_goods")
    if "alchemist" in low:
        out.append("alchemist")
    if any(x in low for x in ("market", "main market", "horse market")):
        out.append("market")
    if any(x in low for x in ("hall", "office", "palace", "high council")):
        out.append("government")
    if any(x in low for x in ("healer", "apothecar", "infirmar", "temple",
                              "physician")):
        out.append("healer")
    return out


# Where the HEALER hangs when a settlement has no building of its own for one
# (2026-07-26, the attrition rework's slice 3b). Every settlement has SOMEONE
# who sets bones -- the herb-wife over the counter at the general store, the
# apothecary behind the alchemist's shop -- and the treatment ladder gates on
# the SERVICE's tier cap (rpg.HEALER_TIER_CAP), never on which door it is
# behind. Preference order: the alchemist first (a capital's own apothecary),
# then the general shop, then the inn.
_HEALER_HOSTS = ("alchemist", "general_goods", "lodging")

# What a settlement of each tier OWES the party. Every settlement is a place
# the party can stand in -- a bed, a counter and somebody who sets bones --
# and until 2026-08-21 that was every settlement's whole required list. The
# HAMLET is the first tier that legitimately falls short of it: a hundred
# souls have no smith, and a broken sword is a reason to walk to the next
# village. `session.cmd_buy` is the one reader that has to notice.
REQUIRED_SERVICES = {
    "metropolis": ("lodging", "smith", "general_goods", "healer"),
    "city": ("lodging", "smith", "general_goods", "healer"),
    "town": ("lodging", "smith", "general_goods", "healer"),
    "village": ("lodging", "smith", "general_goods", "healer"),
    "hamlet": ("lodging", "general_goods", "healer"),
}


def _attach_services(area: dict, sites: list[dict]) -> None:
    seen = set()
    by_kind: dict[str, dict] = {}
    for site in sites:
        for kind in _service_kind(site["name"]):
            if kind in seen:
                continue
            seen.add(kind)
            by_kind[kind] = site
            service = {"id": f"{area['id']}/service/{kind}",
                       "kind": kind, "label": kind.replace("_", " "),
                       "site": site["id"], "provider": None}
            area["services"].append(service)
            site["services"].append(kind)
    if "healer" not in seen:
        host = next((by_kind[k] for k in _HEALER_HOSTS if k in by_kind), None)
        if host is not None:
            seen.add("healer")
            area["services"].append(
                {"id": f"{area['id']}/service/healer", "kind": "healer",
                 "label": "healer", "site": host["id"], "provider": None})
            host["services"].append("healer")
    required = set(REQUIRED_SERVICES[area["subtype"]])
    if area.get("capital"):
        required |= {"alchemist", "market", "government"}
    missing = required - seen
    if missing:
        raise ValueError(f"{area['name']} lacks required services: "
                         f"{sorted(missing)}")


# --------------------------------------------------------------------------- #
# Fixed Europe geography
# --------------------------------------------------------------------------- #

def load_europe_map(path: Path = EUROPE_MAP_PATH) -> tuple[str, ...]:
    """Read and hard-validate the checked-in 30x18 source grid."""
    try:
        text = path.read_text(encoding="ascii")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path}: map must be ASCII/UTF-8 text") from exc
    rows = text.splitlines()
    if len(rows) != MAP_ROWS:
        raise ValueError(f"{path}: expected {MAP_ROWS} rows, got {len(rows)}")
    for row_number, row in enumerate(rows, 1):
        if len(row) != MAP_COLUMNS:
            raise ValueError(
                f"{path}: row {row_number} has {len(row)} columns; "
                f"expected {MAP_COLUMNS}")
        for column, glyph in enumerate(row, 1):
            if glyph not in BIOME_GLYPHS:
                raise ValueError(
                    f"{path}: invalid glyph {glyph!r} at row {row_number}, "
                    f"column {column}")
    return tuple(rows)


def load_overlay(path: Path, letters: dict[str, str]) -> tuple[str, ...]:
    """Read and hard-validate one authored overlay beside the base map.

    The overlay grids are the same 30x18 frame as `europe_map.txt`, one
    letter per tile plus `.` for the sea. Shape and vocabulary are checked
    here; what the letters MEAN against the ground under them -- painted iff
    land, alpine and mountains exactly on the `^` tiles, the pinned censuses
    -- is `validate_world`'s business, because that is where the tiles are.
    """
    legal = set(letters) | {"."}
    try:
        text = path.read_text(encoding="ascii")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path}: overlays must be ASCII text") from exc
    rows = text.splitlines()
    if len(rows) != MAP_ROWS:
        raise ValueError(f"{path}: expected {MAP_ROWS} rows, got {len(rows)}")
    for row_number, row in enumerate(rows, 1):
        if len(row) != MAP_COLUMNS:
            raise ValueError(
                f"{path}: row {row_number} has {len(row)} columns; "
                f"expected {MAP_COLUMNS}")
        for column, glyph in enumerate(row, 1):
            if glyph not in legal:
                raise ValueError(
                    f"{path}: invalid glyph {glyph!r} at row {row_number}, "
                    f"column {column}")
    return tuple(rows)


_COUNTRY_GRID: tuple[str, ...] | None = None
_SEA_COUNTRY: dict[tuple[int, int], str] = {}


def europe_countries() -> tuple[str, ...]:
    """The country overlay, loaded and cached like the map it sits on."""
    global _COUNTRY_GRID
    if _COUNTRY_GRID is None:
        _COUNTRY_GRID = load_overlay(COUNTRY_PATH, COUNTRY_LETTERS)
    return _COUNTRY_GRID


def _derive_sea_countries() -> dict[tuple[int, int], str]:
    """A sea Tile belongs to the country of its NEAREST LAND, by tile
    distance, ties settled north-then-west the way the pathfinder settles
    its equal-cost routes. Nothing about the sea is hand-painted: the
    overlay carries land only, and the water falls out of it."""
    rows = europe_countries()
    land = [(row, column, COUNTRY_LETTERS[glyph])
            for row, line in enumerate(rows, 1)
            for column, glyph in enumerate(line, 1) if glyph != "."]
    out = {}
    for row, line in enumerate(rows, 1):
        for column, glyph in enumerate(line, 1):
            if glyph != ".":
                continue
            out[(row, column)] = min(
                land,
                key=lambda cell: (abs(cell[0] - row) + abs(cell[1] - column),
                                  cell[0], cell[1]))[2]
    return out


def country_at(row: int, column: int) -> str:
    """Which of the nine this Tile belongs to. Land reads the overlay; sea
    derives from the nearest land tile (`_derive_sea_countries`)."""
    glyph = europe_countries()[row - 1][column - 1]
    if glyph != ".":
        return COUNTRY_LETTERS[glyph]
    if not _SEA_COUNTRY:
        _SEA_COUNTRY.update(_derive_sea_countries())
    return _SEA_COUNTRY[(row, column)]


def _land_components(rows: tuple[str, ...]) -> list[set[tuple[int, int]]]:
    remaining = {(row, column)
                 for row, line in enumerate(rows, 1)
                 for column, glyph in enumerate(line, 1) if glyph != "."}
    components = []
    while remaining:
        component = set()
        stack = [min(remaining)]
        while stack:
            cell = stack.pop()
            if cell not in remaining:
                continue
            remaining.remove(cell)
            component.add(cell)
            row, column = cell
            stack.extend((row + dr, column + dc)
                         for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
        components.append(component)
    return sorted(components, key=len, reverse=True)


def _validate_fixed_data(rows: tuple[str, ...]) -> None:
    counts = {biome: 0 for biome in PINNED_BIOME_COUNTS}
    countries = {country: {biome: 0 for biome in ("basic", "mountain",
                                                   "river")}
                 for country in COUNTRIES}
    for row, line in enumerate(rows, 1):
        for column, glyph in enumerate(line, 1):
            biome = BIOME_GLYPHS[glyph]
            counts[biome] += 1
            if biome != "sea":
                countries[country_at(row, column)][biome] += 1
    if counts != PINNED_BIOME_COUNTS:
        raise ValueError(f"Europe map biome census changed: {counts}")
    if countries != PINNED_COUNTRY_BIOMES:
        raise ValueError(f"Europe map country census changed: {countries}")
    sizes = tuple(len(component) for component in _land_components(rows))
    if sizes != PINNED_LAND_COMPONENTS:
        raise ValueError(f"Europe map land components changed: {sizes}")
    for row, column, name, country, biome, _capital in HISTORICAL_CITIES:
        actual_biome = BIOME_GLYPHS[rows[row - 1][column - 1]]
        actual_country = country_at(row, column)
        if (actual_biome, actual_country) != (biome, country):
            raise ValueError(
                f"{name} at {tile_coordinate(row, column)} declares "
                f"{country}/{biome}, map has {actual_country}/{actual_biome}")
    capitals = {name for _r, _c, name, _p, _b, cap in HISTORICAL_CITIES
                if cap}
    if capitals != {"London", "Paris", "Prague", "Stockholm", "Moscow",
                    "Constantinople", "Cordoba", "Cairo", "Kyiv"}:
        raise ValueError(f"historical capitals changed: {sorted(capitals)}")
    seated = {country for _r, _c, _n, country, _b, cap in HISTORICAL_CITIES
              if cap}
    if seated != set(COUNTRIES):
        raise ValueError(f"every country seats one capital; got {seated}")


def _slot(slot_id: str, tier: str, seed: int, *, name: str | None = None,
          capital: bool = False, authored: bool = False,
          charter: str | None = None, manor: str | None = None) -> dict:
    return {"id": slot_id, "tier": tier, "name": name,
            "capital": capital, "authored": authored, "area": None,
            "known": authored, "seed": seed,
            "charter": charter, "manor": manor}


def _is_coast(world: dict, tile: dict) -> bool:
    return any(world["tiles"][nid]["biome"] == "sea"
               for nid in tile["neighbors"])


def _draw(rng: random.Random, table) -> str:
    return rng.choices([row[0] for row in table],
                       [row[1] for row in table])[0]


def roll_census(world: dict) -> None:
    """THE SETTLEMENT CENSUS, rolled once at worldgen off a derived seed.

    Per land Tile: the deterministic score picks a band, the band draws a
    weighted ARRANGEMENT over the five tier letters, and the letters become
    settlement slots sorted chief-first. An authored tile -- a historical
    city or a mine -- takes its own tier in slot 1 and draws its companions
    from ITS OWN BAND's table truncated to the three seats left, which is
    what makes Paris gather towns while Stockholm stands nearly alone.

    Zero is a real tier: about fifty of the 314 land Tiles roll empty, and a
    tile of quiet country is a correct tile, not a gap in the map.

    The two feudal words ride along -- the CHARTER (cities and metropolises
    always, a generated town one time in three) and the MANOR (a village-led
    tile of two or more seats one time in two). Both are stored and read by
    nothing yet; the politics arc owns what freedom is worth.
    """
    seed = world["seed"]
    rng = random.Random(stable_seed(seed, "world", "census", 0))
    for tid in world["tile_order"]:
        tile = world["tiles"][tid]
        if tile["biome"] == "sea":
            continue
        row, column = tile["row"], tile["column"]
        economy = tile_economy(tile["climate"], tile["terrain"],
                               tile["biome"] == "river", row, column)
        river = tile["biome"] == "river" or tile["climate"] == "nile"
        score = tile_score(economy, tile["terrain"], _is_coast(world, tile),
                           river, row, column)
        band = score_band(score, row, column)
        historical = HISTORICAL_BY_TILE.get((row, column))
        mine = MINES.get((row, column))
        if historical:
            letters = (TIER_LETTERS_BY_TIER[HISTORICAL_TIERS[historical[0]]]
                       + _draw(rng, ARRANGEMENTS[band])[:SLOT_CAP - 1])
        elif mine:      # the mine town: authored, tier town, slot 1
            letters = "T" + _draw(rng, ARRANGEMENTS[band])[:SLOT_CAP - 1]
        else:
            letters = _draw(rng, ARRANGEMENTS[band])
        letters = "".join(sorted(letters, key=TIER_ORDER.index))
        charters = []
        for letter in letters:
            tier = TIER_LETTERS[letter]
            if tier in CITY_GRADE:
                charters.append("free")
            elif tier == "town":
                charters.append("free" if rng.random() < CHARTER_CHANCE
                                else None)
            else:
                charters.append(None)
        if letters and (historical or mine):
            charters[0] = "free"    # the famous names hold their own
                                    # charters, and a mine town's mining
                                    # law IS its charter
        manor = ("manor" if len(letters) >= 2 and letters[0] == "V"
                 and rng.random() < MANOR_CHANCE else None)
        for index, letter in enumerate(letters, 1):
            first = index == 1
            name = capital = None
            if first and historical:
                name, capital = historical[0], historical[3]
            elif first and mine:
                name = mine[0]
            sid = f"{tile['id']}/settlement/{index:02d}"
            slot = _slot(sid, TIER_LETTERS[letter],
                         stable_seed(seed, tile["id"], "settlement-slot",
                                     index),
                         name=name, capital=bool(capital),
                         authored=bool(first and historical),
                         charter=charters[index - 1],
                         manor=manor if first else None)
            slot.update(tile=tid, index=index)
            world["settlement_slots"][sid] = slot
            tile["settlement_slots"].append(sid)
            world["lands"][tile["country"]]["settlement_slots"].append(sid)


def population_band(world: dict, tile: dict | str) -> str:
    """One land Tile's population band, RECOMPUTED. The score behind it is a
    worldgen intermediate and is never stored, so this is how a later arc --
    or the eyeball tool -- asks what the census was rolled against."""
    if isinstance(tile, str):
        tile = world["tiles"][tile]
    if tile["biome"] == "sea":
        raise ValueError(f"{tile['id']}: the sea carries no population band")
    row, column = tile["row"], tile["column"]
    economy = tile_economy(tile["climate"], tile["terrain"],
                           tile["biome"] == "river", row, column)
    river = tile["biome"] == "river" or tile["climate"] == "nile"
    score = tile_score(economy, tile["terrain"], _is_coast(world, tile),
                       river, row, column)
    return score_band(score, row, column)


def _origin_regions(world: dict, tiles: set[str]) -> list[set[str]]:
    """The connected components (cardinal) of one good's origin tiles. Each
    walk starts at the remainder's row-major minimum, so the components come
    out in the same order in every process."""
    remaining, out = set(tiles), []
    while remaining:
        start = min(remaining)
        component, frontier = {start}, deque([start])
        while frontier:
            tid = frontier.popleft()
            for nid in world["tiles"][tid]["neighbors"]:
                if nid in remaining and nid not in component:
                    component.add(nid)
                    frontier.append(nid)
        remaining -= component
        out.append(component)
    return out


def goods_origins(world: dict) -> list[dict]:
    """Every place a good comes FROM: the authored mines, the authored
    colour, and the produce regions the law derives from sessions 1-2's
    numbers. A region is one origin however many tiles it spans, so the
    Danube's wine ships from the Danube rather than from eleven separate
    vineyards.

    Not stored: the origins are a worldgen intermediate, and what survives
    them is `tile["goods"]` and the routes they drew.
    """
    origins = [{"tiles": {tile_id(row, column)}, "goods": tuple(goods),
                "name": name}
               for (row, column), (name, goods) in MINES.items()]
    origins += [{"tiles": {tile_id(row, column)}, "goods": tuple(goods),
                 "name": None}
                for (row, column), goods in GOODS_AUTHORED.items()]
    derived: dict[str, set[str]] = {good: set() for good in DERIVED_GOODS}
    for tid in world["tile_order"]:
        tile = world["tiles"][tid]
        if tile["biome"] == "sea":
            continue
        row, column, climate = tile["row"], tile["column"], tile["climate"]
        economy = tile_economy(climate, tile["terrain"],
                               tile["biome"] == "river", row, column)
        river = tile["biome"] == "river" or climate == "nile"
        watered = river or _is_coast(world, tile)
        if economy["realized"] >= GRAIN_SURPLUS:
            derived["grain"].add(tid)
        if climate in WINE_CLIMATES and economy["realized"] >= WINE_MIN:
            derived["wine"].add(tid)
        if climate in WOOL_CLIMATES and economy["pastoral"] >= WOOL_PASTORAL:
            derived["wool"].add(tid)
        if climate == "steppe" and economy["pastoral"] >= HORSE_PASTORAL:
            derived["horses"].add(tid)
        if (economy["forest"] >= WOODED_MIN and watered
                and tile["terrain"] != "marsh"):
            derived["timber"].add(tid)      # fen carr is not ship timber
        if economy["cover"] == "deep forest" and climate in FUR_CLIMATES:
            derived["furs"].add(tid)
    for good in DERIVED_GOODS:
        goods = ("furs", "wax") if good == "furs" else (good,)
        for region in _origin_regions(world, derived[good]):
            if good != "grain" and len(region) < MIN_PRODUCE_REGION:
                continue        # a lone hill's wool is local colour
            origins.append({"tiles": region, "goods": goods, "name": None})
    return origins


def _route_path(destination: str, origin: str) -> list[str]:
    """The cheapest line from `origin` to `destination`, walked back down a
    tree ROOTED AT THE DESTINATION.

    Rooting at the market rather than at the origin is the deliberate half:
    many origins ship to one market, so one tree serves them all and every
    road into that market settles its ties the same way. The silver roads
    converge on the mint instead of each drawing its own equally cheap line
    beside the last.
    """
    _distance, previous = _single_source(destination)
    path = [origin]
    while path[-1] != destination:
        path.append(previous[path[-1]])
    return path


def roll_routes(world: dict) -> None:
    """THE TRADE NETWORK, drawn at worldgen over the census it reads.

    Three kinds of origin (`goods_origins`) and one law moves all of them:
    per good, `GOOD_ROUTES` names a destination kind, how many, and the
    bulk range in days; the pathfinder draws the line; routes that share
    both endpoints merge their cargo. On top of that the two authored
    additions -- a GRAIN ROAD from the nearest granary to every mine whose
    own ground cannot feed it, and the five LEGENDARY roads, authored
    endpoint pairs whose line the same pathfinder draws.

    Nothing here rolls dice. The layer is each world's own anyway, because
    the CENSUS it reads was rolled: which tiles are cities decides where the
    ordinary network goes, so the trade skeleton is fixed in character
    (mines, origins, the legendary five) and each world's own in detail.

    THE SEA RULE: sea sails at the settled edge cost. There is no cheap
    freight, because there is one notion of distance in this game and war,
    trade and travel all use it. A route's sea tiles are its SEA LANE and
    the two shores where it changes element are its PORTS.

    Stored: `tile["goods"]`, `tile["mine"]`, the four tags, and the route
    records on `world["routes"]`.
    """
    tiles = world["tiles"]
    origins = goods_origins(world)
    historical = {tile_id(row, column) for row, column in HISTORICAL_BY_TILE}
    mine_tiles = {tile_id(row, column) for row, column in MINES}
    chiefs = {tid: (world["settlement_slots"][
                        tiles[tid]["settlement_slots"][0]]["tier"]
                    if tiles[tid]["settlement_slots"] else None)
              for tid in world["tile_order"]}
    # A market is a place with a market: city-grade rolled chiefs, the
    # sixteen historical towns whatever tier they wear, and the mine towns,
    # which buy far above their thousand souls. An EMPTY tile has no chief
    # and is nobody's destination -- a route that ended in wilderness would
    # be a road to a field.
    cities = {tid for tid, tier in chiefs.items()
              if tier in CITY_GRADE} | historical
    demand = {
        "markets": cities | mine_tiles,
        "cities": cities,
        "metropolises": {tid for tid, tier in chiefs.items()
                         if tier == "metropolis"},
        "smiths": cities | {tile_id(*rc) for rc, goods
                            in GOODS_AUTHORED.items() if "arms" in goods},
        "cloth": {tile_id(*rc) for rc, goods in GOODS_AUTHORED.items()
                  if "cloth" in goods},
        "capitals": set(CAPITAL_TILES.values()),
    }

    raw: list[dict] = []
    for origin in origins:
        by_rule: dict[tuple, list[str]] = {}
        for good in origin["goods"]:
            rule = GOOD_ROUTES.get(good)
            if rule is not None:        # the exotics ride the legendary
                by_rule.setdefault(rule, []).append(good)
        for (kind, count, max_days), goods in by_rule.items():
            if kind == "capital":
                row, column = tile_row_column(min(origin["tiles"]))
                targets = {CAPITAL_TILES[country_at(row, column)]}
            else:
                targets = demand[kind]
            ranked = []
            for dest in sorted(targets - origin["tiles"]):
                distance, _previous = _single_source(dest)
                member = min(origin["tiles"],
                             key=lambda t, d=distance: (d[t], t))
                ranked.append((distance[member], dest, member))
            ranked.sort()
            for days, dest, member in ranked[:count]:
                if max_days is not None and days > max_days:
                    continue    # the nearest buyer is past the cart's range
                raw.append({"name": None, "goods": tuple(goods),
                            "days": days,
                            "path": _route_path(dest, member)})

    granaries = [tid for origin in origins if "grain" in origin["goods"]
                 for tid in origin["tiles"]]
    for (row, column), (_name, _goods) in MINES.items():
        mine = tile_id(row, column)
        tile = tiles[mine]
        economy = tile_economy(tile["climate"], tile["terrain"],
                               tile["biome"] == "river", row, column)
        if economy["realized"] >= FARMLAND_MIN:
            continue                # the mine's own ground feeds it
        distance, _previous = _single_source(mine)
        reach = [(distance[tid], tid) for tid in granaries
                 if distance[tid] <= MINE_FOOD_DAYS]
        if not reach:
            continue                # UNFED: no granary within reach
        days, member = min(reach)
        # The tree is rooted at the MINE, so the path already runs
        # grain-country -> mine town: the food caravan's own direction.
        raw.append({"name": None, "goods": ("grain",), "days": days,
                    "path": _route_path(mine, member)})

    for spec in LEGENDARY:
        start, goal = tile_id(*spec["from"]), tile_id(*spec["to"])
        distance, _previous = _single_source(goal)
        raw.append({"name": spec["name"], "goods": tuple(spec["goods"]),
                    "days": distance[start],
                    "path": _route_path(goal, start)})

    merged: dict[tuple[str, str], dict] = {}
    for route in raw:
        key = (route["path"][0], route["path"][-1])
        kept = merged.get(key)
        if kept is None:
            merged[key] = route
        else:                       # one road, two cargoes
            kept["goods"] = tuple(dict.fromkeys(kept["goods"]
                                                + route["goods"]))
            kept["name"] = kept["name"] or route["name"]
    world["routes"] = [{"id": f"route/{index:02d}", "name": route["name"],
                        "goods": list(route["goods"]), "days": route["days"],
                        "path": list(route["path"])}
                       for index, route in enumerate(merged.values(), 1)]

    goods_at: dict[str, list[str]] = {}
    for origin in origins:
        for tid in origin["tiles"]:
            goods_at.setdefault(tid, []).extend(origin["goods"])
    on_route, sea_lane, ports = set(), set(), set()
    for route in world["routes"]:
        for tid in route["path"]:
            (sea_lane if tiles[tid]["biome"] == "sea" else on_route).add(tid)
        for a, b in zip(route["path"], route["path"][1:]):
            at_sea = (tiles[a]["biome"] == "sea", tiles[b]["biome"] == "sea")
            if at_sea[0] != at_sea[1]:
                ports.add(b if at_sea[0] else a)
    for tid in world["tile_order"]:
        tile = tiles[tid]
        mine = MINES.get((tile["row"], tile["column"]))
        tile["mine"] = mine[0] if mine else None
        tile["goods"] = list(dict.fromkeys(goods_at.get(tid, ())))
        for tag, carried in zip(TRADE_TAGS, (mine is not None,
                                             tid in on_route,
                                             tid in ports,
                                             tid in sea_lane)):
            if carried:
                tile["tags"].append(tag)


def tile_routes(world: dict, tile: dict | str) -> list[dict]:
    """Every route crossing one Tile, in the world's own route order."""
    tid = tile_key(tile)
    return [route for route in world["routes"] if tid in route["path"]]


def endpoint_name(world: dict, tile: dict | str) -> str:
    """What a route's end is CALLED. The historical cities and the mine
    towns name themselves, the authored doors and marks have their own
    words, and anything else -- a rolled city the party has never heard of
    -- reads as its coordinate, the same way the map labels it."""
    row, column = tile_row_column(tile)
    historical = HISTORICAL_BY_TILE.get((row, column))
    if historical:
        return historical[0]
    if (row, column) in MINES:
        return MINES[(row, column)][0]
    return ENDPOINT_NAMES.get((row, column), tile_coordinate(row, column))


def _cargo_words(goods: Iterable[str]) -> str:
    """`silver` / `copper and iron` / `spice, sugar and dyes`."""
    words = list(goods)
    if len(words) < 2:
        return "".join(words)
    return ", ".join(words[:-1]) + " and " + words[-1]


def route_line(world: dict, route: dict) -> str:
    """One route as the tile's label speaks it: `Goslar - Paris: silver`,
    and a legendary road by its own name first."""
    ends = (f"{endpoint_name(world, route['path'][0])} - "
            f"{endpoint_name(world, route['path'][-1])}")
    cargo = _cargo_words(route["goods"])
    if route["name"]:
        return f"{route['name']}: {ends}, {cargo}"
    return f"{ends}: {cargo}"


def route_lines(world: dict, tile: dict | str,
                limit: int | None = None) -> list[str]:
    """Every road across one Tile, as lines. `limit` caps the list with a
    `+N more` tail the way the map legend's does (2026-08-21, session 4 --
    Paris carries fourteen roads and a phone page carries four). The NAMED
    roads lead when the list is capped: a legendary road is the one a
    player would want named, and the ordinary ones keep route order behind
    it. Uncapped, the order is the world's own."""
    routes = tile_routes(world, tile)
    if limit is None or len(routes) <= limit:
        return [route_line(world, route) for route in routes]
    named = [route for route in routes if route["name"]]
    rest = [route for route in routes if not route["name"]]
    shown = (named + rest)[:limit]
    return ([route_line(world, route) for route in shown]
            + [f"+{len(routes) - limit} more"])


def _harvest_neighbors(world: dict, tid: str):
    for nid in world["tiles"][tid]["neighbors"]:
        if world["tiles"][nid]["biome"] != "sea":
            yield nid


def roll_harvest(world: dict) -> None:
    """THE LAST HARVEST, rolled once at worldgen off a derived seed.

    Four to six regions of trouble, their centers weighted toward the
    climates that fail, each drawing a CAUSE its own ground can suffer and
    growing outward by contagion into the ground that cause can hurt. Every
    other tile had a fine year. Two postures are guaranteed:

    - NO WORLD IS A GOOD YEAR EVERYWHERE. If nothing rolled a drought, the
      most drought-apt center re-causes: somewhere there is always dust.
    - THE CAMPAIGN USUALLY OPENS IN OR BESIDE A BAD YEAR. The nearby-trouble
      nudge (`TROUBLE_DAYS` / `TROUBLE_CHANCE`) moves one region into reach
      of the start when none is there -- three worlds in four, so the quiet
      start survives as the fourth.

    Stored: `tile["harvest"]` (an int percent) and `tile["harvest_cause"]`
    (the cause word, or None for a fine year), plus the region records on
    the world. The cause's fiction name is session 4's read surface.
    """
    rng = random.Random(stable_seed(world["seed"], "world", "harvest", 0))
    land = [tid for tid in world["tile_order"]
            if world["tiles"][tid]["biome"] != "sea"]
    climate = {tid: world["tiles"][tid]["climate"] for tid in land}
    weights = [CENTER_WEIGHT[climate[tid]] for tid in land]
    centers: list[str] = []
    n_regions = rng.randint(*HARVEST_REGIONS)
    while len(centers) < n_regions:
        pick = rng.choices(land, weights=weights)[0]
        row, column = tile_row_column(pick)
        if all(abs(row - r) + abs(column - c) > HARVEST_SEPARATION
               for r, c in (tile_row_column(t) for t in centers)):
            centers.append(pick)
    regions = [{"center": tid, "cause": _draw(rng, HARVEST_CAUSES[
        climate[tid]])} for tid in centers]
    _nudge_trouble(world, rng, regions, land, weights, climate)
    if not any(region["cause"] == "drought" for region in regions):
        # No year is a good year everywhere: the most drought-apt center
        # re-causes, so every world has its year of dust somewhere.
        best = max(regions,
                   key=lambda g: SUSCEPTIBILITY["drought"][climate[g["center"]]])
        best["cause"] = "drought"

    harvest: dict[str, int] = {}
    cause_at: dict[str, str] = {}
    for index, region in enumerate(regions, 1):
        members = {region["center"]: 0}
        frontier = deque([(region["center"], 0)])
        while frontier:
            tid, ring = frontier.popleft()
            if ring >= max(HARVEST_SPREAD):
                continue
            for nid in _harvest_neighbors(world, tid):
                if nid in members:
                    continue
                chance = (HARVEST_SPREAD[ring + 1]
                          * SUSCEPTIBILITY[region["cause"]][climate[nid]])
                if rng.random() < chance:
                    members[nid] = ring + 1
                    frontier.append((nid, ring + 1))
        region["id"] = f"harvest/{index:02d}"
        region["tiles"] = list(members)
        core = rng.randint(*SEVERITY_CENTER)
        for tid, ring in members.items():
            severity = core + SEVERITY_RING * ring + rng.randint(
                -SEVERITY_JITTER, SEVERITY_JITTER)
            severity = min(SEVERITY_CLAMP[1], max(SEVERITY_CLAMP[0],
                                                  severity))
            if tid not in harvest or severity < harvest[tid]:
                harvest[tid] = severity
                cause_at[tid] = region["cause"]
    for tid in land:
        if tid not in harvest:
            draw = rng.gauss(GOOD_MEAN, GOOD_SIGMA)
            if rng.random() < LEGENDARY_CHANCE:
                draw = rng.uniform(110, 120)
            harvest[tid] = int(min(GOOD_CLAMP[1], max(GOOD_CLAMP[0], draw)))
    for tid in world["tile_order"]:
        tile = world["tiles"][tid]
        tile["harvest"] = harvest.get(tid)
        tile["harvest_cause"] = cause_at.get(tid)
    world["harvest_regions"] = [
        {"id": region["id"], "cause": region["cause"],
         "center": region["center"], "tiles": region["tiles"]}
        for region in regions]


def _nudge_trouble(world: dict, rng: random.Random, regions: list[dict],
                   land: list[str], weights: list[float],
                   climate: dict[str, str]) -> None:
    """THE NEARBY TROUBLE NUDGE. When no region center lies within
    `TROUBLE_DAYS` path days of the start, relocate the LAST-rolled region
    into that radius `TROUBLE_CHANCE` of the time, re-drawing its cause from
    the new climate -- before growth, so the region grows out of the ground
    it actually sits on. Runs before the drought guarantee, so the nudge can
    never cost a world its year of dust."""
    start = world["party_tile"]
    near = [tid for tid, weight in zip(land, weights)
            if weight > 0 and path_days(start, tid) <= TROUBLE_DAYS]
    if any(path_days(start, region["center"]) <= TROUBLE_DAYS
           for region in regions):
        return
    if not near or rng.random() >= TROUBLE_CHANCE:
        return
    moved = rng.choices(near, weights=[CENTER_WEIGHT[climate[tid]]
                                       for tid in near])[0]
    regions[-1]["center"] = moved
    regions[-1]["cause"] = _draw(rng, HARVEST_CAUSES[climate[moved]])


def _name_state(seed: int | None) -> tuple[dict, dict]:
    reserves, counters = {}, {}
    for country, pools in SETTLEMENT_NAMES.items():
        reserves[country], counters[country] = {}, {}
        for tier, names in pools.items():
            draw = list(names)
            random.Random(stable_seed(seed, f"land/{country}",
                                      f"{tier}-names", 0)).shuffle(draw)
            reserves[country][tier] = draw
            counters[country][tier] = 0
    return reserves, counters


def _next_settlement_name(world: dict, country: str, tier: str) -> str:
    reserve = world["name_reserves"][country][tier]
    if reserve:
        return reserve.pop(0)
    world["name_counters"][country][tier] += 1
    return (f"{world['lands'][country]['name']} {tier.title()} "
            f"{world['name_counters'][country][tier]}")


def _settlement_template(country: str, tier: str, slot: dict,
                         tile_tags: Iterable[str] = ()
                         ) -> tuple[dict, list[dict]]:
    """The country/tier role this slot is cut from, chosen deterministically
    and by FIT (2026-08-15, Europe MVP Closure). A template declares the Tile
    tags it wants -- `coast` for a harbour, `river` for a ford, `mountain-foot`
    for a hill town -- and only templates the Tile can honor are in the draw.
    A Tile that fits none of them draws from the templates that ask for
    nothing, which is why every country keeps at least one of those per tier.
    The pick is `slot["seed"] % len(...)`, so it is the same every time this
    slot materializes and it survives the save."""
    culture = CULTURE_OF[country]
    templates = CULTURE_SPECS[culture]["settlement_templates"]
    if slot.get("capital"):
        role = next(r for r, spec in templates.items()
                    if spec["tier"] == "capital")
        key = template_id(culture, role)
        return dict(AREA_SPECS[key]), SETTLEMENT_SITE_SPECS[key]
    have = set(tile_tags)
    # A METROPOLIS draws the city role (2026-08-21, the census session):
    # the census rolls no generated metropolis, and the three authored ones
    # wear a great city's shape until the Settlements-revisited round gives
    # them their own.
    wanted_tier = "city" if tier == "metropolis" else tier
    roles = [role for role, spec in templates.items()
             if spec["tier"] == wanted_tier]
    if not roles:
        raise ValueError(f"{culture}: no {tier} settlement template")
    fitting = [role for role in roles
               if set(templates[role]["fits"]) <= have]
    wanted = [role for role in fitting if templates[role]["fits"]] \
        or [role for role in fitting] \
        or roles
    role = wanted[slot["seed"] % len(wanted)]
    key = template_id(culture, role)
    return dict(AREA_SPECS[key]), SETTLEMENT_SITE_SPECS[key]


def board_active_roll(seed: int | None, slot: dict) -> bool:
    """Does this settlement normally post ordinary work? A stable derived
    roll off the slot's own identity, so the answer is the same whenever the
    slot is materialized and survives the save unchanged."""
    band = "capital" if slot["capital"] else slot["tier"]
    roll = random.Random(stable_seed(seed, slot["id"], "board-active", 0))
    return roll.random() < BOARD_ACTIVE_CHANCE[band]


def materialize_slot(world: dict, slot: dict | str, *,
                     need: str | None = None, day: int | None = None,
                     known: bool = True) -> dict:
    if isinstance(slot, str):
        slot = world["settlement_slots"][slot]
    if slot["area"] is not None:
        return world["areas"][slot["area"]]
    tile = world["tiles"][slot["tile"]]
    country = tile["country"]
    if slot["name"] is None:
        slot["name"] = _next_settlement_name(world, country, slot["tier"])
    template, site_specs = _settlement_template(country, slot["tier"], slot,
                                                tile["tags"])
    aid = f"{tile['id']}/area/settlement/{slot['index']:02d}"
    spec = {**template, "id": aid, "name": slot["name"],
            "subtype": slot["tier"], "capital": slot["capital"]}
    area = _new_area_record(spec, country, tile, world["seed"],
                            slot["index"] + 1,
                            "historical" if slot["authored"] else "worldgen")
    # THE AREA INHERITS THE GROUND, NOT THE TRADE (2026-08-21, session 3).
    # An Area's tag list is QUEST vocabulary -- `quests._select_quest_area`
    # picks by it, and `mine` is already a word a forged job asks for -- so
    # letting the four trade words through would quietly make the quest
    # generator a reader of the trade layer, which this session's one read
    # surface (the tile label) deliberately is not. The words are on the
    # TILE, where the hookup session's readers will find them.
    ground = [tag for tag in tile["tags"] if tag not in TRADE_TAGS]
    area["tags"] = list(dict.fromkeys(area["tags"] + ground))
    area["known"] = known
    area["settlement_slot"] = slot["id"]
    area["board_active"] = board_active_roll(world["seed"], slot)
    world["areas"][aid] = area
    tile["areas"].append(aid)
    world["lands"][country]["areas"].append(aid)
    slot["area"] = aid
    slot["known"] = known
    sites = [materialize_site(world, area, site_spec, source="authored",
                              domain="built", known=known,
                              purpose="required-site")
             for site_spec in site_specs]
    _attach_services(area, sites)
    if need is not None:
        area["founded_day"] = day
        area["founded_for"] = need
        _event(world, day, area["id"], "materialize")
    return area


def reserve_settlements(world: dict, polity: str,
                        tier: str | None = None) -> list[dict]:
    return [world["settlement_slots"][sid]
            for sid in world["lands"][polity]["settlement_slots"]
            if world["settlement_slots"][sid]["area"] is None
            and (tier is None or world["settlement_slots"][sid]["tier"] == tier)]


def materialize_settlement(world: dict, polity: str, *,
                           need: str, tier: str | None = None,
                           tags: Iterable[str] = (),
                           day: int | None = None) -> dict | None:
    pool = reserve_settlements(world, polity, tier)
    wanted = set(tags)
    fitting = [slot for slot in pool
               if wanted.intersection(world["tiles"][slot["tile"]]["tags"])]
    slot = (fitting or pool or [None])[0]
    return (materialize_slot(world, slot, need=need, day=day)
            if slot is not None else None)


def reveal_tile(world: dict, tile: dict | str, day: int | None = None) -> list[dict]:
    if isinstance(tile, str):
        tile = world["tiles"][tile]
    tile["known"] = tile["visited"] = True
    natural = world["areas"][tile["natural_area"]]
    natural["known"] = True
    if day is not None and "discovered_day" not in natural:
        natural["discovered_day"] = day
    found = []
    for sid in tile["settlement_slots"]:
        found.append(materialize_slot(world, sid, day=day, known=True))
    return found


def create_geography(seed: int | None) -> dict:
    """Build the fixed 540-Tile Europe frame and its seeded population."""
    rows = load_europe_map()
    _validate_fixed_data(rows)
    climate_rows = load_overlay(CLIMATE_PATH, CLIMATE_LETTERS)
    terrain_rows = load_overlay(TERRAIN_PATH, TERRAIN_LETTERS)
    name_reserves, name_counters = _name_state(seed)
    world = {
        "seed": seed, "lands": {}, "tiles": {}, "tile_order": [],
        "settlement_slots": {}, "areas": {}, "sites": {}, "rooms": {},
        "quests": {}, "npcs": [], "events": [],
        "name_reserves": name_reserves,
        "name_counters": name_counters,
    }
    for index, country in enumerate(COUNTRIES, 1):
        world["lands"][country] = _new_land_record(
            country, LAND_SPECS[country], seed, index)

    mainland = _land_components(rows)[0]
    for row, line in enumerate(rows, 1):
        for column, glyph in enumerate(line, 1):
            tid = tile_id(row, column)
            biome = BIOME_GLYPHS[glyph]
            country = country_at(row, column)
            historical = HISTORICAL_BY_TILE.get((row, column))
            name = historical[0] if historical else tile_coordinate(row, column)
            neighbors = [tile_id(row + dr, column + dc)
                         for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0))
                         if 1 <= row + dr <= MAP_ROWS
                         and 1 <= column + dc <= MAP_COLUMNS]
            climate = CLIMATE_LETTERS.get(climate_rows[row - 1][column - 1])
            terrain = TERRAIN_LETTERS.get(terrain_rows[row - 1][column - 1])
            # The sea carries neither overlay and no derived word: the
            # laws below are about GROUND. What a sea Tile has is its one
            # biome word and its country, which is all the map asks of it.
            if biome == "sea":
                tags, cover = ["sea", country], None
            else:
                economy = tile_economy(climate, terrain,
                                       biome == "river", row, column)
                cover = economy["cover"]
                tags = [terrain, country]
                if biome == "river":
                    tags += ["river", "riverside"]
                tags += derived_tags(economy, climate, row, column)
            tile = {"id": tid, "row": row, "column": column, "name": name,
                    "country": country, "biome": biome,
                    "climate": climate, "terrain": terrain, "cover": cover,
                    "known": True,
                    "visited": False, "neighbors": neighbors, "areas": [],
                    "natural_area": None, "settlement_slots": [],
                    "tags": tags, "seed": stable_seed(seed, tid, "tile", 0)}
            world["tiles"][tid] = tile
            world["tile_order"].append(tid)
            world["lands"][country]["tiles"].append(tid)

    for tid in world["tile_order"]:
        tile = world["tiles"][tid]
        row, column = tile["row"], tile["column"]
        neighbors = [world["tiles"][nid] for nid in tile["neighbors"]]
        if tile["biome"] != "sea" and any(n["biome"] == "sea" for n in neighbors):
            tile["tags"].append("coast")
        if tile["biome"] != "sea" and any(n["biome"] == "mountain" for n in neighbors):
            tile["tags"].append("mountain-foot")
        if any(n["country"] != tile["country"] for n in neighbors):
            tile["tags"].append("border")
        if tile["biome"] != "sea" and (row, column) not in mainland:
            tile["tags"].append("island")
        character = natural_character(tile)
        aid = f"{tid}/area/natural"
        template = natural_template(CULTURE_OF[tile["country"]], character,
                                    row, column)
        spec = {"id": aid,
                "name": f"{tile['name']} {AREA_SUFFIXES[character]}",
                "kind": "natural", "subtype": character,
                "role": character, "tags": tuple(tile["tags"]),
                "description": f"{tile['name']} is "
                               f"{AREA_CHARACTER_LINES[character]}."}
        area = _new_area_record(spec, tile["country"], tile, seed, 1)
        area["template"] = template
        ids = [site["id"] for site in NATURAL_SITE_SPECS[template]]
        random.Random(stable_seed(seed, aid, "natural-site-order", 0)).shuffle(ids)
        area["natural_site_order"] = ids
        world["areas"][aid] = area
        tile["areas"].append(aid)
        tile["natural_area"] = aid
        world["lands"][tile["country"]]["areas"].append(aid)

    # THE ROLLED WORLD (2026-08-21, sessions 2 and 3): the census first --
    # it is what a start can stand in -- then the trade network the census
    # feeds, then the start, then the harvest, whose nearby-trouble nudge
    # needs to know where the campaign opens.
    roll_census(world)
    roll_routes(world)

    # Historical towns exist and are known from day zero; their villages do
    # not. Capitals materialize first so country-level cast code has a stable
    # political seat without relying on coordinate order.
    historical = [slot for slot in world["settlement_slots"].values()
                  if slot["authored"]]
    for slot in sorted(historical, key=lambda value: not value["capital"]):
        materialize_slot(world, slot, known=True)

    # The uniform start draw skips HAMLETS (2026-08-21): a hundred souls
    # with no inn, no smith and no board is not a place to begin a career.
    candidates = [sid for sid, slot in world["settlement_slots"].items()
                  if slot["tier"] != "hamlet"]
    if not candidates:
        raise ValueError("fixed Europe population produced no settlement slots")
    start_slot = random.Random(stable_seed(seed, "world", "start-slot", 0)).choice(
        candidates)
    world["start_slot"] = start_slot
    start_tile = world["settlement_slots"][start_slot]["tile"]
    # WHERE THE PARTY IS STANDING, on the world rather than in the session
    # state, because the world layer's sky reads it every day (session.py's
    # `move_party` is the one writer once a game is running).
    world["party_tile"] = start_tile
    reveal_tile(world, start_tile, day=0)
    world["start_area"] = world["settlement_slots"][start_slot]["area"]
    # The opening settlement posts ordinary work whatever its own roll said:
    # the game has to start somewhere, and it starts at a board.
    world["areas"][world["start_area"]]["board_active"] = True
    roll_harvest(world)
    validate_world(world)
    return world


CAPITAL_TOWNS = frozenset(name for *_r, name, _p, _b, capital
                          in HISTORICAL_CITIES if capital)
# The Tile a land's own sky is read off when the party is somewhere else
# (2026-08-21, the ground session). The day roll takes its weights from the
# ground the party is standing on, which leaves the other eight lands
# needing a reference: their CAPITAL is the concrete, pinned answer -- London
# weather for Phyrascia, Cairo's for Umaia, Stockholm's for Thule -- and it
# is also what stands in for the party itself when it is out at sea, where
# there is no ground to read.
CAPITAL_TILES = {country: tile_id(row, column)
                 for row, column, _name, country, _biome, capital
                 in HISTORICAL_CITIES if capital}


def _validate_ground(world: dict) -> None:
    """The two authored overlays and the law over them, checked against the
    world that was built from them (2026-08-21, the tile economy arc).

    THE LAW IS A LINT. The map is hand-painted, so nothing here computes
    what the climate ought to be -- it checks the things a rule can state
    about an authored picture: that the paint reaches every land Tile and
    no sea Tile, that the two words nature fixes (alpine, mountains) sit
    exactly on the high ground, and that the censuses are the ones the
    painting was signed off with. The DERIVED censuses are pinned too,
    because they move only when one of the law's constants moves, and that
    is a decision somebody should have to make on purpose.
    """
    climates, terrains, covers, marshes = (Counter(), Counter(), Counter(),
                                           {})
    tag_counts = Counter()
    for tid, tile in world["tiles"].items():
        where = tile_coordinate(tile["row"], tile["column"])
        if tile["biome"] == "sea":
            if (tile["climate"], tile["terrain"], tile["cover"]) != \
                    (None, None, None):
                raise ValueError(f"{where}: the sea carries no ground")
            continue
        if tile["climate"] not in CLIMATE_PROFILES:
            raise ValueError(f"{where}: no such climate: {tile['climate']!r}")
        if tile["terrain"] not in TERRAINS:
            raise ValueError(f"{where}: no such terrain: {tile['terrain']!r}")
        if tile["cover"] not in ("open", "wooded", "deep forest"):
            raise ValueError(f"{where}: no such cover: {tile['cover']!r}")
        high = tile["biome"] == "mountain"
        if (tile["climate"] == "alpine") != high:
            raise ValueError(f"{where}: alpine is exactly the mountain "
                             f"Tiles, and this one is {tile['biome']}")
        if (tile["terrain"] == "mountains") != high:
            raise ValueError(f"{where}: mountains is exactly the mountain "
                             f"Tiles, and this one is {tile['biome']}")
        for retired in ("basic", "mountain"):
            if retired in tile["tags"]:
                raise ValueError(f"{where}: the bare biome word "
                                 f"{retired!r} left the tag vocabulary")
        climates[tile["climate"]] += 1
        terrains[tile["terrain"]] += 1
        covers[tile["cover"]] += 1
        if tile["terrain"] == "marsh":
            marshes[(tile["row"], tile["column"])] = tid
        for tag in tile["tags"]:
            if tag in PINNED_TAG_COUNTS:
                tag_counts[tag] += 1
    if dict(climates) != PINNED_CLIMATE_COUNTS:
        raise ValueError(f"the climate census changed: {dict(climates)}")
    if dict(terrains) != PINNED_TERRAIN_COUNTS:
        raise ValueError(f"the terrain census changed: {dict(terrains)}")
    if set(marshes) != set(PINNED_MARSHES):
        raise ValueError(f"the marsh five are {sorted(PINNED_MARSHES)}, "
                         f"got {sorted(marshes)}")
    if dict(covers) != PINNED_COVER_COUNTS:
        raise ValueError(f"the cover census changed: {dict(covers)}")
    if dict(tag_counts) != PINNED_TAG_COUNTS:
        raise ValueError(f"the derived tag census changed: "
                         f"{dict(tag_counts)}")


def _validate_countries(world: dict) -> None:
    """The country overlay against the world built from it (2026-08-21, the
    nine). Same shape of lint as `_validate_ground`: the picture is
    authored, so nothing here computes where a border ought to run -- it
    checks that every Tile wears the letter that was painted on it, that the
    sea derives instead of being painted, that each of the nine seats one
    capital, and that the two censuses are the ones the grid was signed off
    with. The BAND census is in here rather than in the suite because the
    band is campaign-invariant: it can only move when the overlay does."""
    biomes = {country: {biome: 0 for biome in ("basic", "mountain", "river")}
              for country in COUNTRIES}
    bands = {country: {band: 0 for band in BAND_WORDS}
             for country in COUNTRIES}
    for tid in world["tile_order"]:
        tile = world["tiles"][tid]
        row, column = tile["row"], tile["column"]
        where = tile_coordinate(row, column)
        if tile["country"] != country_at(row, column):
            raise ValueError(f"{where}: the overlay says "
                             f"{country_at(row, column)}, the Tile says "
                             f"{tile['country']}")
        if tile["country"] not in tile["tags"]:
            raise ValueError(f"{where}: a Tile carries its country as a tag")
        if tile["biome"] == "sea":
            if europe_countries()[row - 1][column - 1] != ".":
                raise ValueError(f"{where}: the sea is derived, never "
                                 f"painted")
            continue
        biomes[tile["country"]][tile["biome"]] += 1
        bands[tile["country"]][population_band(world, tile)] += 1
    if biomes != PINNED_COUNTRY_BIOMES:
        raise ValueError(f"the per-country biome census changed: {biomes}")
    if bands != PINNED_COUNTRY_BANDS:
        raise ValueError(f"the per-country band census changed: {bands}")
    if set(CAPITAL_TILES) != set(COUNTRIES):
        raise ValueError(f"every country seats one capital; got "
                         f"{sorted(CAPITAL_TILES)}")
    for country, tid in CAPITAL_TILES.items():
        if world["tiles"][tid]["country"] != country:
            raise ValueError(f"{country}: its capital stands in "
                             f"{world['tiles'][tid]['country']}")


def validate_world(world: dict) -> None:
    """The fixed geography's own contract, checked once at world creation.

    Every clause here is a cross-cutting invariant of the Europe build, and
    every one of them is cheap over 540 Tiles. They live in the CONSTRUCTOR
    rather than only in the suite because a world that breaks one of them is
    not a world the readers below may be handed: the whole point of the
    strict-reader discipline is that illegal world state raises where it is
    made, not three commands later inside a display.
    """
    tiles = world["tiles"]
    order = world["tile_order"]
    expected = [tile_id(row, column)
                for row in range(1, MAP_ROWS + 1)
                for column in range(1, MAP_COLUMNS + 1)]
    if order != expected:
        raise ValueError("tile_order is not the row-major 18x30 frame")
    if set(tiles) != set(expected):
        raise ValueError("the tile store and tile_order disagree")
    _validate_ground(world)
    _validate_countries(world)

    capitals, slot_ids = set(), set()
    for tid in order:
        tile = tiles[tid]
        if tile["country"] not in COUNTRIES:
            raise ValueError(f"{tid}: no such country: {tile['country']}")
        natural = tile["natural_area"]
        if natural is None or natural not in world["areas"]:
            raise ValueError(f"{tid}: every Tile has one natural Area")
        if world["areas"][natural]["kind"] != "natural":
            raise ValueError(f"{tid}: natural_area is not natural")
        for nid in tile["neighbors"]:
            other = tiles.get(nid)
            if other is None:
                raise ValueError(f"{tid}: neighbor off the frame: {nid}")
            step = (abs(other["row"] - tile["row"])
                    + abs(other["column"] - tile["column"]))
            if step != 1:
                raise ValueError(f"{tid}: {nid} is not a cardinal neighbor")
            if tid not in other["neighbors"]:
                raise ValueError(f"{tid} -> {nid} is not reciprocal")
        slots = [world["settlement_slots"][sid]
                 for sid in tile["settlement_slots"]]
        if tile["biome"] == "sea" and slots:
            raise ValueError(f"{tid}: the sea is never populated")
        historical = HISTORICAL_BY_TILE.get((tile["row"], tile["column"]))
        mine = MINES.get((tile["row"], tile["column"]))
        if historical:
            name, country, biome, capital = historical
            if (tile["biome"], tile["country"]) != (biome, country):
                raise ValueError(f"{tid}: {name} declares {country}/{biome}")
            if tile["name"] != name:
                raise ValueError(f"{tid}: a historical Tile IS its city")
            authored = [slot for slot in slots if slot["authored"]]
            if len(authored) != 1 or authored[0]["name"] != name:
                raise ValueError(f"{tid}: {name} has no authored town")
            if authored[0]["capital"] != capital:
                raise ValueError(f"{tid}: {name}'s capital flag is wrong")
            if authored[0]["tier"] != HISTORICAL_TIERS[name]:
                raise ValueError(f"{tid}: {name} is a "
                                 f"{HISTORICAL_TIERS[name]}, not a "
                                 f"{authored[0]['tier']}")
            if authored[0] is not slots[0]:
                raise ValueError(f"{tid}: {name} leads its own Tile")
        elif mine:
            # THE MINE TOWN (2026-08-21): seated in slot 1, tier town, named
            # by the mine, always free -- its mining law IS its charter.
            if not slots or slots[0]["name"] != mine[0]:
                raise ValueError(f"{tid}: the {mine[0]} mine seats no town")
            if slots[0]["tier"] != "town":
                raise ValueError(f"{tid}: a mine town is a town")
            if slots[0]["charter"] != "free":
                raise ValueError(f"{tid}: a mine town is always free")
        elif tile["biome"] == "mountain":
            if any(slot["tier"] not in ("village", "hamlet")
                   for slot in slots):
                raise ValueError(f"{tid}: only an AUTHORED town -- a "
                                 f"historical city or a mine -- sits on a "
                                 f"mountain")
        if len(slots) > SLOT_CAP:
            raise ValueError(f"{tid}: {len(slots)} settlements on a Tile "
                             f"the lattice seats {SLOT_CAP}")
        for slot in slots:
            if slot["id"] in slot_ids:
                raise ValueError(f"duplicate settlement slot: {slot['id']}")
            slot_ids.add(slot["id"])
            if slot["tile"] != tid:
                raise ValueError(f"{slot['id']}: not scoped to its Tile")
            if slot["id"] not in \
                    world["lands"][tile["country"]]["settlement_slots"]:
                raise ValueError(f"{slot['id']}: not on its country")
            if slot["tier"] not in TIERS:
                raise ValueError(f"{slot['id']}: no such settlement tier: "
                                 f"{slot['tier']!r}")
            if slot["charter"] not in (None, "free"):
                raise ValueError(f"{slot['id']}: no such charter: "
                                 f"{slot['charter']!r}")
            if slot["manor"] not in (None, "manor"):
                raise ValueError(f"{slot['id']}: no such manor mark: "
                                 f"{slot['manor']!r}")
            if slot["tier"] in CITY_GRADE and slot["charter"] != "free":
                raise ValueError(f"{slot['id']}: a city is always free")
            if slot["capital"]:
                capitals.add(slot["name"])
        if len(slots) > 1 and [TIER_ORDER.index(TIER_LETTERS_BY_TIER[s["tier"]])
                               for s in slots] != sorted(
                TIER_ORDER.index(TIER_LETTERS_BY_TIER[s["tier"]])
                for s in slots):
            raise ValueError(f"{tid}: the slots are not chief-first")
        manors = [slot for slot in slots if slot["manor"]]
        if manors and (manors[0] is not slots[0]
                       or slots[0]["tier"] != "village"
                       or len(slots) < 2):
            raise ValueError(f"{tid}: the manor mark rides the chief "
                             f"village of a Tile of two or more")

    if slot_ids != set(world["settlement_slots"]):
        raise ValueError("the slot store and the Tiles disagree")
    if capitals != CAPITAL_TOWNS:
        raise ValueError(f"the three capitals are {sorted(CAPITAL_TOWNS)}, "
                         f"got {sorted(capitals)}")
    if world["start_slot"] not in world["settlement_slots"]:
        raise ValueError("the start is not a settlement slot")
    if world["start_area"] not in world["areas"]:
        raise ValueError("the start settlement was never materialized")
    if world["party_tile"] not in tiles:
        raise ValueError("the party is standing off the frame")
    if world["settlement_slots"][world["start_slot"]]["tier"] == "hamlet":
        raise ValueError("a career does not open in a hamlet")
    _validate_trade(world)
    _validate_harvest(world)
    _validate_read_surface(world)


def _validate_read_surface(world: dict) -> None:
    """THE READ SURFACE's one clause (2026-08-21, session 4). Every Tile
    can say what it is and what it ate, in words the tables actually hold.

    This exists because the failure it catches is a KeyError raised INSIDE
    a display, mid-play, on whichever Tile happens to carry the good
    somebody added to `GOODS` without a phrase. The strict-reader
    discipline says an illegal world raises where it is made."""
    legal = set(TILE_CHARACTER.values())
    legal.update(phrase for _field, _value, phrase in LAND_CHARACTER)
    legal.update(TERRAINS)
    legal.add("open sea")
    missing = [good for good in GOODS if good not in TILE_CHARACTER]
    if missing:
        raise ValueError(f"goods with no character phrase: {missing}")
    for tid in world["tile_order"]:
        tile = world["tiles"][tid]
        phrase = tile_character(world, tile)
        if phrase not in legal:
            raise ValueError(f"{tid}: {phrase!r} is not a character phrase")
        if tile["biome"] == "sea":
            continue
        if harvest_word(tile["harvest"]) is None:
            raise ValueError(f"{tid}: a land Tile with no harvest word")
        cause = tile["harvest_cause"]
        if cause and cause not in HARVEST_CAUSE_LINES:
            raise ValueError(f"{tid}: {cause!r} has no fiction name")


def _validate_trade(world: dict) -> None:
    """The trade network, checked against the world it was drawn on.

    The ordinary half is the census's own, so nothing here pins a count.
    What a rule CAN state about it: that the authored half is all present
    and ends where it was authored to end, that every word anywhere is a
    good the game knows, that a route is a real walk over real edges whose
    days are the walk's own, and that the four tags say exactly what the
    routes did -- a `port` with no route through it, or a road across a
    Tile the tag forgot, is the kind of damage a display would render
    without complaint.
    """
    tiles = world["tiles"]
    on_route, sea_lane, ports = set(), set(), set()
    for index, route in enumerate(world["routes"], 1):
        where = route["id"]
        if where != f"route/{index:02d}":
            raise ValueError(f"{where}: the routes are numbered in order")
        path = route["path"]
        if len(path) < 2:
            raise ValueError(f"{where}: a route runs between two Tiles")
        if not route["goods"]:
            raise ValueError(f"{where}: a route carries something")
        illegal = [good for good in route["goods"] if good not in GOODS]
        if illegal:
            raise ValueError(f"{where}: no such good: {illegal}")
        days = 0
        for a, b in zip(path, path[1:]):
            days += edge_days(a, b)     # raises on anything but a real edge
        if days != route["days"]:
            raise ValueError(f"{where}: a {days}-day walk recorded as "
                             f"{route['days']} days")
        for tid in path:
            if tid not in tiles:
                raise ValueError(f"{where}: {tid} is off the frame")
            (sea_lane if tiles[tid]["biome"] == "sea"
             else on_route).add(tid)
        for a, b in zip(path, path[1:]):
            at_sea = (tiles[a]["biome"] == "sea", tiles[b]["biome"] == "sea")
            if at_sea[0] != at_sea[1]:
                ports.add(b if at_sea[0] else a)
    named = sorted(route["name"] for route in world["routes"]
                   if route["name"])
    if named != sorted(spec["name"] for spec in LEGENDARY):
        raise ValueError(f"the named roads are the legendary {len(LEGENDARY)}"
                         f", got {named}")
    by_name = {route["name"]: route for route in world["routes"]
               if route["name"]}
    for spec in LEGENDARY:
        route = by_name[spec["name"]]
        ends = (tile_id(*spec["from"]), tile_id(*spec["to"]))
        if (route["path"][0], route["path"][-1]) != ends:
            raise ValueError(f"{spec['name']} runs {ends[0]} to {ends[1]}, "
                             f"not {route['path'][0]} to "
                             f"{route['path'][-1]}")
        dropped = [good for good in spec["goods"]
                   if good not in route["goods"]]
        if dropped:
            raise ValueError(f"{spec['name']} carries {dropped}")

    for tid in world["tile_order"]:
        tile = tiles[tid]
        where = tile_coordinate(tile["row"], tile["column"])
        mine = MINES.get((tile["row"], tile["column"]))
        illegal = [good for good in tile["goods"] if good not in GOODS]
        if illegal:
            raise ValueError(f"{where}: no such good: {illegal}")
        if tile["biome"] == "sea" and (tile["goods"] or tile["mine"]):
            raise ValueError(f"{where}: the sea digs and grows nothing")
        if mine:
            if tile["mine"] != mine[0]:
                raise ValueError(f"{where}: the {mine[0]} mine is not on "
                                 f"its own Tile ({tile['mine']!r})")
            absent = [good for good in mine[1]
                      if good not in tile["goods"]]
            if absent:
                raise ValueError(f"{where}: {mine[0]} raises {absent} and "
                                 f"the Tile does not carry it")
        elif tile["mine"] is not None:
            raise ValueError(f"{where}: {tile['mine']!r} is not one of the "
                             f"{len(MINES)} authored mines")
        for tag, carried in zip(TRADE_TAGS, (mine is not None,
                                             tid in on_route,
                                             tid in ports,
                                             tid in sea_lane)):
            if (tag in tile["tags"]) != carried:
                raise ValueError(f"{where}: the {tag!r} tag and the routes "
                                 f"disagree")
        if tid in ports and "coast" not in tile["tags"]:
            raise ValueError(f"{where}: a port stands on the coast")


def _validate_harvest(world: dict) -> None:
    """The last harvest, checked against the world it was rolled onto.

    The roll is each world's own, so nothing here pins a number: what a rule
    can state about it is that every land Tile has a percent on the settled
    scale, that the sea has none, that each region is a CONTIGUOUS piece of
    land whose tiles all carry its cause, and that the two guarantees held.
    """
    tiles = world["tiles"]
    regions = world["harvest_regions"]
    caused = set()
    for tid in world["tile_order"]:
        tile = tiles[tid]
        where = tile_coordinate(tile["row"], tile["column"])
        if tile["biome"] == "sea":
            if (tile["harvest"], tile["harvest_cause"]) != (None, None):
                raise ValueError(f"{where}: the sea has no harvest")
            continue
        percent = tile["harvest"]
        if not isinstance(percent, int) or not (
                SEVERITY_CLAMP[0] <= percent <= GOOD_CLAMP[1]):
            raise ValueError(f"{where}: {percent!r} is off the harvest "
                             f"scale ({SEVERITY_CLAMP[0]}-{GOOD_CLAMP[1]})")
        cause = tile["harvest_cause"]
        if cause is not None and cause not in SUSCEPTIBILITY:
            raise ValueError(f"{where}: no such harvest cause: {cause!r}")
        if (cause is None) != (percent >= HARVEST_PROBLEM):
            raise ValueError(f"{where}: a caused Tile is a problem Tile and "
                             f"a fine year has no cause ({percent}, "
                             f"{cause!r})")
        if cause is not None:
            caused.add(tid)
    if not regions:
        raise ValueError("no world is a good year everywhere")
    if not any(region["cause"] == "drought" for region in regions):
        raise ValueError("every world has its year of dust somewhere")
    members = set()
    for region in regions:
        if region["cause"] not in SUSCEPTIBILITY:
            raise ValueError(f"{region['id']}: no such cause")
        if region["center"] not in region["tiles"]:
            raise ValueError(f"{region['id']}: a region holds its center")
        reached, frontier = {region["center"]}, [region["center"]]
        pool = set(region["tiles"])
        while frontier:
            tid = frontier.pop()
            for nid in tiles[tid]["neighbors"]:
                if nid in pool and nid not in reached:
                    reached.add(nid)
                    frontier.append(nid)
        if reached != pool:
            raise ValueError(f"{region['id']}: the region is not contiguous")
        for tid in pool:
            if tiles[tid]["biome"] == "sea":
                raise ValueError(f"{region['id']}: trouble at sea")
        members |= pool
    if members != caused:
        raise ValueError("the caused Tiles and the regions disagree")


# --------------------------------------------------------------------------- #
# Grid navigation (2026-08-15, Grid Navigation and Map UI)
# --------------------------------------------------------------------------- #
# Distance is GEOGRAPHY, not save state. The map is authored and immutable,
# so an edge's cost is a pure function of the two Tiles' biomes and the
# direction between them -- identical in every campaign, on every seed. That
# is why the pathfinder takes Tile IDs and never a world: there is nothing a
# world could tell it that the grid does not already know, and a reader that
# asked for one would invite a caller to believe distance is mutable.
#
# The cost model (rules.md's Travel section): a tile is 30 km east-west and
# 60 km north-south, so an east/west edge is one day and a north/south edge
# two. A mountain at EITHER end adds a day, which makes the cost symmetric by
# construction -- descending a pass costs exactly what climbing it cost.
# River is ordinary land at this scale and sea is navigable open water; both
# take the directional base and nothing more.

EDGE_DAYS_EAST_WEST = 1
EDGE_DAYS_NORTH_SOUTH = 2
MOUNTAIN_EDGE_SURCHARGE = 1

DIRECTIONS = {"north": (-1, 0), "west": (0, -1),
              "east": (0, 1), "south": (1, 0)}
DIRECTION_WORDS = {**{name: name for name in DIRECTIONS},
                   "n": "north", "w": "west", "e": "east", "s": "south"}
BIOME_LETTERS = {biome: glyph for glyph, biome in BIOME_GLYPHS.items()}

_GRID: tuple[str, ...] | None = None
# Single-source Dijkstra results, keyed by origin Tile ID. Cacheable across
# worlds for the reason above: the grid the search runs on is the checked-in
# map, which no campaign can edit.
_PATHS: dict[str, tuple[dict[str, int], dict[str, str]]] = {}


def europe_grid() -> tuple[str, ...]:
    """The validated map rows, read and checked once per process."""
    global _GRID
    if _GRID is None:
        rows = load_europe_map()
        _validate_fixed_data(rows)
        _GRID = rows
    return _GRID


def tile_row_column(tile: dict | str) -> tuple[int, int]:
    """The 1-based (row, column) of a Tile record or Tile ID.

    Raises on anything that is not a Tile inside the frame -- an unknown
    coordinate is a bug in the caller, never a place to invent.
    """
    if isinstance(tile, dict):
        return tile["row"], tile["column"]
    match = re.fullmatch(r"tile/r(\d{2})/c(\d{2})", tile)
    if match is None:
        raise ValueError(f"not a Tile ID: {tile!r}")
    row, column = int(match[1]), int(match[2])
    if not (1 <= row <= MAP_ROWS and 1 <= column <= MAP_COLUMNS):
        raise ValueError(f"{tile} lies outside the "
                         f"{MAP_ROWS}x{MAP_COLUMNS} frame")
    return row, column


def tile_key(tile: dict | str) -> str:
    """The Tile ID of a Tile record or a validated Tile ID."""
    if isinstance(tile, dict):
        return tile["id"]
    tile_row_column(tile)
    return tile


def biome_at(row: int, column: int) -> str:
    if not (1 <= row <= MAP_ROWS and 1 <= column <= MAP_COLUMNS):
        raise ValueError(f"R{row:02d}C{column:02d} lies outside the frame")
    return BIOME_GLYPHS[europe_grid()[row - 1][column - 1]]


def direction_word(text: str) -> str | None:
    """`n` / `North` -> `north`; anything else -> None (not a direction)."""
    return DIRECTION_WORDS.get(text.strip().lower())


def parse_coordinate(text: str) -> tuple[int, int] | None:
    """`R09C18`, `r9c18` or `9,18` -> (9, 18). None when it is not a
    coordinate at all; a coordinate OUTSIDE the frame raises, because the
    player named a cell the world does not have."""
    match = re.fullmatch(r"r\s*(\d{1,2})\s*[c,]\s*(\d{1,2})",
                         text.strip().lower().replace(" ", ""))
    if match is None:
        match = re.fullmatch(r"(\d{1,2})\s*[,x]\s*(\d{1,2})", text.strip())
    if match is None:
        return None
    row, column = int(match[1]), int(match[2])
    if not (1 <= row <= MAP_ROWS and 1 <= column <= MAP_COLUMNS):
        raise ValueError(
            f"R{row:02d}C{column:02d} is off the map -- rows are 1-"
            f"{MAP_ROWS}, columns 1-{MAP_COLUMNS}")
    return row, column


def neighbor_id(tile: dict | str, direction: str) -> str | None:
    """The Tile one cardinal step away, or None at the frame's edge."""
    name = direction_word(direction)
    if name is None:
        raise ValueError(f"not a cardinal direction: {direction!r}")
    row, column = tile_row_column(tile)
    row_step, column_step = DIRECTIONS[name]
    row, column = row + row_step, column + column_step
    if not (1 <= row <= MAP_ROWS and 1 <= column <= MAP_COLUMNS):
        return None
    return tile_id(row, column)


def edge_direction(origin: dict | str, dest: dict | str) -> str:
    """Which way one cardinal edge runs. Raises on a non-edge."""
    origin_row, origin_column = tile_row_column(origin)
    dest_row, dest_column = tile_row_column(dest)
    step = (dest_row - origin_row, dest_column - origin_column)
    for name, offset in DIRECTIONS.items():
        if offset == step:
            return name
    raise ValueError(f"{tile_key(origin)} and {tile_key(dest)} are not "
                     f"cardinal neighbors")


def edge_days(origin: dict | str, dest: dict | str) -> int:
    """The symmetric day cost of one cardinal edge (see the block above)."""
    edge_direction(origin, dest)        # rejects diagonals and non-edges
    origin_row, origin_column = tile_row_column(origin)
    dest_row, dest_column = tile_row_column(dest)
    days = (EDGE_DAYS_NORTH_SOUTH if dest_row != origin_row
            else EDGE_DAYS_EAST_WEST)
    if "mountain" in (biome_at(origin_row, origin_column),
                      biome_at(dest_row, dest_column)):
        days += MOUNTAIN_EDGE_SURCHARGE
    return days


def _single_source(origin: str) -> tuple[dict[str, int], dict[str, str]]:
    """Dijkstra from one Tile over the whole frame.

    Deterministic without a tie-break table: the frontier is ordered by
    (cost, row, column), relaxation is strict, and neighbors are expanded
    north/west/east/south. Equal-cost routes therefore always settle on the
    one whose frontier tile is northernmost, then westernmost -- the same
    answer in every process, with no reliance on dict or hash order.
    """
    cached = _PATHS.get(origin)
    if cached is not None:
        return cached
    row, column = tile_row_column(origin)
    distance: dict[str, int] = {origin: 0}
    previous: dict[str, str] = {}
    frontier = [(0, row, column, origin)]
    while frontier:
        cost, _row, _column, current = heapq.heappop(frontier)
        if cost > distance[current]:
            continue
        for direction in DIRECTIONS:
            nid = neighbor_id(current, direction)
            if nid is None:
                continue
            step = cost + edge_days(current, nid)
            if step < distance.get(nid, step + 1):
                distance[nid] = step
                previous[nid] = current
                nrow, ncolumn = tile_row_column(nid)
                heapq.heappush(frontier, (step, nrow, ncolumn, nid))
    _PATHS[origin] = (distance, previous)
    return distance, previous


def path_days(origin: dict | str, dest: dict | str) -> int:
    """Shortest-path days between two Tiles. Symmetric, and always finite:
    sea is navigable, so every Tile in the frame reaches every other."""
    start, end = tile_key(origin), tile_key(dest)
    distance, _previous = _single_source(start)
    if end not in distance:
        raise ValueError(f"no route from {start} to {end}")
    return distance[end]


def shortest_path(origin: dict | str, dest: dict | str) -> list[str]:
    """The cheapest route as Tile IDs, origin first, destination last."""
    start, end = tile_key(origin), tile_key(dest)
    distance, previous = _single_source(start)
    if end not in distance:
        raise ValueError(f"no route from {start} to {end}")
    route = [end]
    while route[-1] != start:
        route.append(previous[route[-1]])
    route.reverse()
    return route


# --------------------------------------------------------------------------- #
# The 40-column map display
# --------------------------------------------------------------------------- #
# One cell never tries to show everything on a Tile: the overlay is a strict
# priority, party first and terrain last, and the detail block below the grid
# carries what the glyph had to drop.

MAP_GUTTER = "   "               # room for the two-digit row label
MAP_GLYPH_LEGEND = ". sea  # land  ^ mtns  ~ river"
MAP_MARK_LEGEND = "@ party  ! job  C city  T town  v village"


def known_slots(world: dict, tile: dict | str) -> list[dict]:
    """The settlement slots on a Tile the player knows about."""
    if isinstance(tile, str):
        tile = world["tiles"][tile]
    return [world["settlement_slots"][sid] for sid in tile["settlement_slots"]
            if world["settlement_slots"][sid]["known"]]


# The glyph ladder is three rungs over five tiers (2026-08-21): `C` is any
# CITY-GRADE place -- a metropolis, a city or a capital, which the legend
# distinguishes -- `T` a town, `v` a village, and a HAMLET IS NOT DRAWN. At
# 30x18 the map is a country-scale picture and a hundred souls are not a
# feature of it; the hamlet lives in the Tile's detail lines instead.
_GLYPH_TIERS = {"metropolis": "C", "city": "C", "town": "T", "village": "v"}
_GLYPH_RANK = {"C": 0, "T": 1, "v": 2}


def settlement_glyph(world: dict, tile: dict) -> str | None:
    """`C` a known city-grade place (metropolis, city or capital), `T` a
    known town, `v` known village(s) with nothing greater, None when nothing
    drawable here is known -- a Tile of hamlets reads as its own ground."""
    mark = None
    for slot in known_slots(world, tile):
        glyph = "C" if slot["capital"] else _GLYPH_TIERS.get(slot["tier"])
        if glyph is not None and (mark is None
                                  or _GLYPH_RANK[glyph] < _GLYPH_RANK[mark]):
            mark = glyph
    return mark


def map_glyph(world: dict, tile: dict, party: str | None = None,
              objectives: Iterable[str] = ()) -> str:
    if tile["id"] == party:
        return "@"
    if tile["id"] in set(objectives):
        return "!"
    return settlement_glyph(world, tile) or BIOME_LETTERS[tile["biome"]]


def map_lines(world: dict, party: str | None = None,
              objectives: Iterable[str] = ()) -> list[str]:
    """The whole 30x18 world as 18 rows under a two-line numeric axis.

    Thirty glyph columns plus a three-column row gutter is 33 -- inside the
    40-column rule with room to spare, which is why the map is drawn whole
    and never windowed."""
    objectives = set(objectives)
    tens = "".join(" " if column < 10 else str(column // 10)
                   for column in range(1, MAP_COLUMNS + 1))
    units = "".join(str(column % 10)
                    for column in range(1, MAP_COLUMNS + 1))
    lines = [MAP_GUTTER + tens, MAP_GUTTER + units]
    for row in range(1, MAP_ROWS + 1):
        cells = "".join(
            map_glyph(world, world["tiles"][tile_id(row, column)],
                      party, objectives)
            for column in range(1, MAP_COLUMNS + 1))
        lines.append(f"{row:02d} {cells}")
    return lines


def _legend_group(prefix: str, items: list[str], width: int = 40) -> list[str]:
    return textwrap.wrap(prefix + ", ".join(items), width,
                         subsequent_indent="    ", break_long_words=False,
                         break_on_hyphens=False)


def map_legend_lines(world: dict, width: int = 40,
                     limit: int = 10) -> list[str]:
    """Known settlements grouped by country: the historical cities first,
    then as many other known places as the page has room for."""
    lines: list[str] = []
    for country, land in world["lands"].items():
        cities: list[str] = []
        others: list[str] = []
        for sid in land["settlement_slots"]:
            slot = world["settlement_slots"][sid]
            if not slot["known"]:
                continue
            tile = world["tiles"][slot["tile"]]
            label = (f"{slot['name']} "
                     f"{tile_coordinate(tile['row'], tile['column'])}")
            if slot["capital"]:
                label += "*"
            (cities if slot["authored"] else others).append(label)
        if cities:
            lines.extend(_legend_group(f"{land['name']} cities: ", cities,
                                       width))
        if others:
            shown = sorted(others)[:limit]
            if len(others) > limit:
                shown.append(f"+{len(others) - limit} more")
            lines.extend(_legend_group(f"{land['name']} known: ", shown,
                                       width))
    return lines


def tile_label(tile: dict) -> str:
    """`R11C20`, or `Paris (R09C10)` where the Tile carries a real name."""
    coordinate = tile_coordinate(tile["row"], tile["column"])
    return (coordinate if tile["name"] == coordinate
            else f"{tile['name']} ({coordinate})")


def tile_ground(tile: dict) -> str:
    """The one word for what a Tile is made of, as the player reads it.
    The base map's four glyphs are a DRAWING vocabulary -- `basic` was
    never a thing anybody stands on -- so what is spoken is the terrain
    word, and the sea is the sea (2026-08-21)."""
    return "sea" if tile["biome"] == "sea" else tile["terrain"]


def tile_character(world: dict, tile: dict | str) -> str:
    """ONE short phrase for what kind of country this Tile is (2026-08-21,
    session 4). The priority is fixed and the answer is one phrase: what a
    traveller would call the country in three words, not an inventory of
    everything true about it.

    The mine leads, because a mine is what a place is known for wherever
    there is one; then the good the Tile is an origin of, because a
    vineyard is visible from the road; then the land itself off cover,
    terrain and climate. The DM composes the sentence -- this hands over
    the phrase.
    """
    if isinstance(tile, str):
        tile = world["tiles"][tile]
    if tile["biome"] == "sea":
        return "open sea"
    if tile["mine"]:
        metal = MINES[(tile["row"], tile["column"])][1][0]
        return TILE_CHARACTER[metal]
    if tile["goods"]:
        return TILE_CHARACTER[tile["goods"][0]]
    for field, value, phrase in LAND_CHARACTER:
        here = tile["tags"] if field == "tag" else [tile[field]]
        if value in here:
            return phrase
    return tile["terrain"]


def harvest_word(percent: int | None) -> str | None:
    """The spoken scale word for a stored harvest percent. The percent
    itself is never spoken -- not by a page and not by the DM."""
    if percent is None:
        return None
    for floor, word in HARVEST_WORDS:
        if percent >= floor:
            return word
    return HARVEST_WORDS[-1][1]


def harvest_line(world: dict, tile: dict | str) -> str | None:
    """`last harvest: failed -- the great rains`, or None at sea. The cause
    reads through its fiction name, and on the Nile the failure of the
    rains is the failure of the FLOOD, which is its own thing entirely."""
    if isinstance(tile, str):
        tile = world["tiles"][tile]
    word = harvest_word(tile["harvest"])
    if word is None:
        return None
    cause = tile["harvest_cause"]
    if not cause:
        return f"last harvest: {word}"
    if tile["climate"] == "nile" and cause in NILE_CAUSE_LINES:
        named = NILE_CAUSE_LINES[cause]
    else:
        named = HARVEST_CAUSE_LINES[cause]
    return f"last harvest: {word} -- {named}"


def tile_terms(world: dict, tile: dict | str) -> dict[str, float]:
    """THE TILE MENU (2026-08-21, session 4): what standing on THIS ground
    does to a priced term, beside what the land's world layer is doing.

    Static and derived -- the granary, the pithead and the crossroads are
    facts of the map, not events -- so nothing is stored and nothing is
    rolled. `session.local_term` multiplies it into `worldsim.term` and the
    same clamps catch the product."""
    if isinstance(tile, str):
        tile = world["tiles"][tile]
    terms: dict[str, float] = {}
    rows = []
    if "grain" in tile["goods"]:
        rows.append(TILE_MENU["grain"])
    if tile["mine"]:
        rows.append(TILE_MENU["mine"])
    if len(tile_routes(world, tile)) >= CROSSROADS_ROUTES:
        rows.append(TILE_MENU["crossroads"])
    for row in rows:
        for name, mult in row.items():
            terms[name] = terms.get(name, 1.0) * mult
    return terms


def detail_wrap(lines: list[str], width: int) -> list[str]:
    """The page's own hard wrap, the same rule session.py prints by:
    continuation lines hang two spaces past the original indent. The driver
    wraps everything it prints anyway, so doing it here changes no output --
    what it buys is that a page is the SAME list of lines whoever asks for
    it, which is what a label test can read. Public since 2026-08-21: the
    world layer's own state diff wraps by this rule too, rather than
    keeping a copy of it."""
    out: list[str] = []
    for line in lines:
        if len(line) <= width:
            out.append(line)
            continue
        indent = len(line) - len(line.lstrip(" "))
        out.extend(textwrap.wrap(
            line, width, break_long_words=False, break_on_hyphens=False,
            subsequent_indent=" " * min(indent + 2, width // 2)) or [""])
    return out


def tile_detail_lines(world: dict, tile: dict | str,
                      areas: bool = True, width: int = 40) -> list[str]:
    """What the glyph could not say: where this Tile is, whose it is, what
    it is made of, what it digs and grows, which roads cross it, and
    (unless the caller lists them itself) which of its Areas the party
    knows.

    THE TRADE LABEL (2026-08-21, session 3) is the one read surface the
    trade layer ships: the mine, the goods the Tile is an origin of, and
    one line per route crossing it -- the endpoints by name and the cargo.
    All three are common knowledge, because a mine, a vineyard and a road
    are things you can see from the road.

    THE CHARACTER AND THE HARVEST (2026-08-21, session 4) complete the
    file: what kind of country this is, and how last year's harvest came
    in. Both are common knowledge too -- everyone alive here knows what
    they ate last winter -- and neither speaks a number.
    """
    if isinstance(tile, str):
        tile = world["tiles"][tile]
    ground = tile_ground(tile)
    lines = [f"HERE: {tile_label(tile)} -- "
             f"{world['lands'][tile['country']]['name']}, {ground}"]
    character = tile_character(world, tile)
    if tile["biome"] != "sea" and character != ground:
        lines.append(f"  {character}")  # the bare terrain words fall through
                                        # to themselves; the header said it
    extra = [tag for tag in tile["tags"]
             if tag not in (ground, tile["country"])]
    if extra:
        lines.append("  ground: " + ", ".join(extra))
    harvest = harvest_line(world, tile)
    if harvest:
        lines.append(f"  {harvest}")
    if tile["mine"]:
        lines.append(f"  mine: {tile['mine']}")
    if tile["goods"]:
        lines.append("  goods: " + ", ".join(tile["goods"]))
    lines.extend(f"  {line}" for line in route_lines(world, tile,
                                                    limit=ROUTE_LINES))
    known = [world["areas"][aid] for aid in tile["areas"]
             if world["areas"][aid].get("known")]
    if areas and known:
        lines.append("  areas: " + ", ".join(area["name"] for area in known))
    return detail_wrap(lines, width)


def _slot_line(world: dict, slot: dict) -> str:
    """One census slot as the DM's brief reads it. A slot the party has
    never walked into has no NAME yet -- the name reserve is drawn at
    materialization -- so it reads by its tier and says so, rather than
    leaking a settlement nobody has met."""
    area = world["areas"].get(slot["area"]) if slot["area"] else None
    if area is None:
        who = f"a {slot['tier']} (unmet)"
    else:
        who = f"{slot['tier']} {area['name']}"
    marks = []
    if slot["capital"]:
        marks.append("CAPITAL")
    if slot["charter"]:
        marks.append(slot["charter"])
    if slot["manor"]:
        marks.append(slot["manor"])
    if area is not None and not area.get("board_active"):
        marks.append("board quiet")
    return who + (f" -- {', '.join(marks)}" if marks else "")


def _neighbour_line(world: dict, tile: dict) -> str:
    """A neighbouring Tile in one line: what it is called, what kind of
    country it is, who is the biggest thing on it, and its harvest ONLY
    where the harvest is a problem -- the DM is narrating toward it, not
    running a scene on it."""
    parts = [tile_character(world, tile)]
    if tile["settlement_slots"]:
        chief = world["settlement_slots"][tile["settlement_slots"][0]]
        area = world["areas"].get(chief["area"]) if chief["area"] else None
        # The indefinite article IS the unmet marker here -- `a village`
        # against `village Erkhet` -- and it saves the eight characters
        # that were wrapping seven of these lines in ten. The CENSUS block
        # above says `(unmet)` in full, where the DM is reading rather
        # than glancing and the room is there.
        parts.append(f"{chief['tier']} {area['name']}" if area
                     else f"a {chief['tier']}")
    if tile["harvest"] is not None and tile["harvest"] < HARVEST_PROBLEM:
        parts.append(f"harvest {harvest_word(tile['harvest'])}")
    return f"{tile_label(tile)} -- " + ", ".join(parts)


def tile_brief_lines(world: dict, tile: dict | str,
                     width: int = 40) -> list[str]:
    """ONE TILE'S WHOLE FILE, for DM eyes (2026-08-21, session 4 -- the
    round-4 sitting's designer directive). What `lore` is to a land, this
    is to a Tile: everything the layers below stamped on it, in one page,
    free and costing no day.

    It is NARRATION MATERIAL, never a dump to the player (dm.md has the
    protocol). Two things it carries that the player's own detail block
    does not: the census in full -- every slot, including the ones nobody
    has met, by tier and never by name -- and the four NEIGHBOURS in a line
    each, so the DM narrates toward the next Tile knowing what is there.

    The land layer stays `world` and `lore`'s business. This is the TILE's
    file only.
    """
    if isinstance(tile, str):
        tile = world["tiles"][tile]
    land = world["lands"][tile["country"]]["name"]
    lines = [f"TILE {tile_label(tile)} -- {land}"]
    if tile["biome"] == "sea":
        lines.append("  open sea")
        return detail_wrap(lines, width)
    ground = [tile["terrain"], tile["climate"], tile["cover"]]
    if tile["biome"] != "basic":        # `basic` is a map GLYPH, not ground
        ground.append(tile["biome"])
    lines.append("  " + " / ".join(ground))
    lines.append(f"  {tile_character(world, tile)}")
    extra = [tag for tag in tile["tags"]
             if tag not in (tile["terrain"], tile["country"])]
    if extra:
        lines.append("  tags: " + ", ".join(extra))
    harvest = harvest_line(world, tile)
    if harvest:
        lines.append(f"  {harvest}")
    if tile["mine"]:
        metals = ", ".join(MINES[(tile["row"], tile["column"])][1])
        lines.append(f"  mine: {tile['mine']} ({metals})")
    if tile["goods"]:
        lines.append("  goods: " + ", ".join(tile["goods"]))
    roads = route_lines(world, tile)        # uncapped: this is a file
    if roads:
        lines.append("  roads:")
        lines.extend(f"    {line}" for line in roads)
    slots = [world["settlement_slots"][sid] for sid in
             tile["settlement_slots"]]
    lines.append("  census: empty" if not slots else "  census:")
    lines.extend(f"    {_slot_line(world, slot)}" for slot in slots)
    lines.append("  neighbours:")
    for direction in DIRECTIONS:
        nid = neighbor_id(tile, direction)
        if nid is None:
            continue
        lines.append(f"    {direction[0].upper()} "
                     f"{_neighbour_line(world, world['tiles'][nid])}")
    return detail_wrap(lines, width)


def land_homeland(world: dict, polity: str) -> str:
    """The country a local person calls home."""
    return world["lands"][polity]["homeland"]


def land_culture(world: dict, polity: str) -> str:
    return world["lands"][polity]["culture"]


def has_service(area: dict, kind: str) -> bool:
    """Does this settlement keep a counter of this kind? Every tier above
    hamlet owes the four basics (`REQUIRED_SERVICES`), so this only ever
    says no about a hamlet's missing smith or about the capital-grade
    counters -- which is exactly what it is for."""
    return any(service["kind"] == kind for service in area["services"])


def settlement_tier(area: dict) -> str:
    """Mechanical service/board/conquest tier for a settlement Area."""
    return "capital" if area.get("capital") else area["subtype"]


def materialize_natural_site(world: dict, area: dict | str,
                             day: int | None = None) -> dict | None:
    if isinstance(area, str):
        area = world["areas"][area]
    if area["kind"] != "natural":
        raise ValueError("natural Sites require a natural Area")
    used = set(area["used_natural_sites"])
    next_site = next((sid for sid in area["natural_site_order"]
                      if sid not in used), None)
    if next_site is None:
        return None
    spec = next(s for s in NATURAL_SITE_SPECS[area["template"]]
                if s["id"] == next_site)
    site = materialize_site(world, area, spec, source="lazy",
                            domain="natural", known=True,
                            purpose="natural-site")
    area["used_natural_sites"].append(next_site)
    if site["rooms"]:
        world["rooms"][site["rooms"][0]]["known"] = True
    _event(world, day, site["id"], "materialize")
    return site


HOUSE_MAIN_ORDINARY = (
    "shelf of crockery", "water bucket", "oil lamp", "wool blankets",
    "coat pegs", "broom", "kindling basket", "covered food crock",
    "small household shrine",
)
HOUSE_PERSONAL = ("carved toy", "sewing basket", "smoking pipe", "whetstone",
                  "family token", "bundle of letters")
HOUSE_FOOD = {
    "western": ("brown bread", "onions", "hard cheese", "dried apples",
                "smoked fish", "pot of stew"),
    "southern": ("flatbread", "onions", "hard cheese", "olives",
                 "smoked fish", "pot of stew"),
    "steppe": ("flatbread", "onions", "hard cheese", "dried curds",
               "smoked fish", "pot of stew"),
    "norse": ("flat barley bread", "onions", "hard cheese", "dried berries",
              "salt fish", "pot of stew"),
}
HOUSE_HEAT = {
    "western": ("stone hearth", "iron stove"),
    "southern": ("stone hearth", "iron stove", "tiled hearth"),
    "steppe": ("stone hearth", "iron stove", "clay stove"),
    "norse": ("long hearth", "stone hearth", "iron stove"),
}
HOUSE_LIVELIHOOD = {
    "western": ("account book", "fishing net", "grain sack", "reed knife",
                "hand saw", "boat hook"),
    "southern": ("account book", "fishing net", "pruning knife",
                 "olive basket", "grape basket", "sickle"),
    "steppe": ("tack repair kit", "wool bundle", "cargo tally",
               "wool shears", "salt scoop", "water skin"),
    "norse": ("fishing net", "rope coil", "splitting axe", "net needle",
              "tar pot", "wool shears"),
}
# The livelihood a particular ROLE keeps in its houses. Keyed by (culture,
# template role), and a role with no row falls back to the culture's own
# list above. The role names are the catalog's, so a re-authored template
# takes its houses with it.
HOUSE_LIVELIHOOD_BY_ROLE = {
    ("western", "capital"):
        ("account book", "sealing wax", "guard belt", "folded cloth",
         "writing case"),
    ("western", "walled_city"):
        ("cargo tally", "merchant scales", "crate bar", "sealing wax",
         "wooden measure"),
    ("western", "harbor_town"):
        ("fishing net", "iron hooks", "cork floats", "sailcloth",
         "fish basket"),
    ("western", "dock_town"):
        ("cargo tally", "rope coil", "tar pot", "crate bar",
         "merchant scales"),
    ("western", "market_town"):
        ("sickle", "grain sack", "seed basket", "harness",
         "wooden measure"),
    ("western", "river_town"):
        ("reed knife", "eel basket", "ferry rope", "waterproof boots",
         "fish trap"),
    ("western", "ford_village"):
        ("plough blade", "grain sack", "ferry pole", "horse tack",
         "seed basket"),
    ("western", "forest_village"):
        ("hand saw", "splitting axe", "timber wedges", "charcoal basket",
         "leather apron"),
    ("western", "shore_village"):
        ("fishing line", "cork floats", "boat hook", "salt sack",
         "net needle"),
    ("western", "fen_village"):
        ("reed knife", "eel basket", "peat spade", "duck decoy",
         "reed basket"),
    ("western", "field_village"):
        ("plough blade", "grain sack", "seed basket", "sickle",
         "flail"),
    ("southern", "capital"):
        ("account book", "sealing wax", "folded cloth", "oil jar",
         "writing case"),
    ("southern", "walled_city"):
        ("market scales", "cargo tally", "oil measure", "sealing wax",
         "crate bar"),
    ("southern", "harbor_town"):
        ("fishing net", "sailcloth", "cargo tally", "tar pot",
         "fish basket"),
    ("southern", "market_town"):
        ("pruning knife", "olive basket", "oil measure", "pottery tools",
         "market scales"),
    ("southern", "hill_town"):
        ("grape basket", "barrel hoops", "goat bell", "pruning hook",
         "wine tally"),
    ("southern", "vineyard_village"):
        ("pruning knife", "grape basket", "picking net", "clay wine jug",
         "olive rake"),
    ("southern", "river_village"):
        ("sickle", "grain sack", "sluice key", "reed basket",
         "wooden measure"),
    ("southern", "coast_village"):
        ("fishing line", "cork floats", "salt sack", "boat hook",
         "net needle"),
    ("steppe", "capital"):
        ("tack repair kit", "market tally", "wool bundle", "bow case",
         "seal box"),
    ("steppe", "walled_city"):
        ("cargo tally", "market tally", "foreign coin weights", "harness",
         "crate bar"),
    ("steppe", "road_town"):
        ("cargo tally", "harness", "ferry rope", "foreign coin weights",
         "crate bar"),
    ("steppe", "ridge_town"):
        ("wool shears", "saddle blanket", "shepherd's crook", "bow stave",
         "salt blocks"),
    ("steppe", "well_town"):
        ("salt scoop", "water tally", "goat bell", "clay jar",
         "caravan rope"),
    ("steppe", "herd_village"):
        ("horse brush", "rope halter", "feed basket", "leather needle",
         "wool shears"),
    ("steppe", "river_village"):
        ("fishing net", "ferry pole", "fish basket", "boat hook",
         "reed mat"),
    ("steppe", "basin_village"):
        ("water skin", "salt scoop", "goat tack", "reed mat",
         "well rope"),
    ("steppe", "wood_village"):
        ("hand saw", "splitting axe", "charcoal basket", "fur bundle",
         "pine tar pot"),
    ("norse", "capital"):
        ("oar blade", "sealing wax", "silver weights", "sail needle",
         "rune stick"),
    ("norse", "walled_city"):
        ("cargo tally", "silver weights", "crate bar", "rope coil",
         "sail needle"),
    ("norse", "harbor_town"):
        ("tar pot", "sailcloth", "rope coil", "oar blade", "fish basket"),
    ("norse", "market_town"):
        ("silver weights", "hide bundle", "wool bundle", "market tally",
         "salt sack"),
    ("norse", "shore_village"):
        ("net needle", "cork floats", "salt sack", "boat hook",
         "drying rack"),
    ("norse", "wood_village"):
        ("splitting axe", "timber wedges", "charcoal basket", "hand saw",
         "pine tar pot"),
    ("norse", "field_village"):
        ("barley sack", "sickle", "seed basket", "byre fork",
         "hay rope"),
}
HOUSE_OPTIONAL = {
    "sleeping-alcove": ("one narrow bed", "blanket chest", "wash basin",
                        "stool", "wall peg", "candle"),
    "store-room": ("shelves", "sacks", "barrels", "rope", "lamp oil",
                   "preserved food", "spare tools", "empty baskets"),
    "work-room": ("workbench", "tool rack", "water bucket", "shelves"),
    "small-yard": ("wood pile", "water barrel", "handcart",
                   "chopping block", "drying line", "tool shed"),
}


def materialize_house(world: dict, area: dict | str) -> tuple[dict, dict]:
    """Create one persistent culture-compatible resident and ordinary house."""
    if isinstance(area, str):
        area = world["areas"][area]
    if area["kind"] != "settlement":
        raise ValueError("ordinary houses require a settlement")
    purpose = "ordinary-house"
    sequence = area["sequences"].get(purpose, 0) + 1
    seed = stable_seed(world["seed"], area["id"], purpose, sequence)
    rng = random.Random(seed)
    from people import make_npc

    homeland = land_homeland(world, area["land"])
    culture = land_culture(world, area["land"])
    used = {npc["name"] for npc in world["npcs"]}
    resident = make_npc(rng, homeland, "resident", used_names=used)
    npc_id = f"npc/{area['land']}/{slug(resident['name'])}/{sequence}"
    resident.update(id=npc_id, land=area["land"], seat=area["id"],
                    post="resident")
    world["npcs"].append(resident)
    spec = {"id": "ordinary-house", "name": f"{resident['name']}'s House",
            "rooms": [], "anchors": []}
    site = materialize_site(world, area, spec, source="lazy", domain="built",
                            known=True, purpose=purpose)
    site["template"] = "ordinary_house"
    site["occupants"].append(npc_id)

    main_id = f"{site['id']}/main-room"
    labels = [rng.choice(HOUSE_HEAT[culture]),
              rng.choice(("rough table and stools",
                          "narrow table and bench"))]
    ordinary = list(HOUSE_MAIN_ORDINARY)
    rng.shuffle(ordinary)
    labels.extend(ordinary[:rng.randint(1, 2)])
    livelihood = HOUSE_LIVELIHOOD_BY_ROLE.get(
        (culture, area["role"]), HOUSE_LIVELIHOOD[culture])
    extras = [rng.choice(HOUSE_FOOD[culture]),
              rng.choice(livelihood),
              rng.choice(HOUSE_PERSONAL)]
    rng.shuffle(extras)
    labels.extend(extras[:max(0, 5 - len(labels))])
    main = {
        "id": main_id, "name": "Main Room", "site": site["id"],
        "template": "main-room", "role": "main-room", "content_pool": None,
        "source": "lazy",
        "seed": stable_seed(world["seed"], site["id"], "room", 1),
        "known": True, "visited": False,
        "contents": _content_records(main_id, labels),
        "features": [], "states": [], "occupants": [npc_id], "kinds": [],
        "quest_ids": [],
    }
    world["rooms"][main_id] = main
    site["rooms"].append(main_id)

    optional = list(HOUSE_OPTIONAL)
    rng.shuffle(optional)
    for i, role in enumerate(optional[:rng.randint(0, 2)], 2):
        pool = list(HOUSE_OPTIONAL[role])
        rng.shuffle(pool)
        room_id = f"{site['id']}/{role}"
        room = {
            "id": room_id, "name": role.replace("-", " ").title(),
            "site": site["id"], "template": role, "role": role,
            "content_pool": f"house-{role}", "source": "lazy",
            "seed": stable_seed(world["seed"], site["id"], "room", i),
            "known": False, "visited": False,
            "contents": _content_records(room_id, pool[:rng.randint(2, 4)]),
            "features": [], "states": [], "occupants": [], "kinds": [],
            "quest_ids": [],
        }
        world["rooms"][room_id] = room
        site["rooms"].append(room_id)
    if rng.random() < 0.35:
        hidden_pool = [value for value in
                       ("bundle of letters", "family token",
                        "locked keepsake box")
                       if value not in labels]
        hidden = rng.choice(hidden_pool)
        rec = _content_records(main_id, [hidden], reveal="search")[0]
        rec["id"] = f"{main_id}/content/hidden"
        main["contents"].append(rec)
    _event(world, None, site["id"], "materialize")
    return site, resident


def reveal(target: dict) -> None:
    target["known"] = True


def _fact(state_id: str, reveal_rule: str = "public",
          day: int | None = None, slot: str | None = None) -> dict:
    """One state on a place. `day` is the DAY STAMP the world layer reads
    (worldsim.py, 2026-08-07: states are visible, dated and changeable);
    `slot` names the exclusive slot it belongs to, if any -- the slot
    discipline itself is the caller's, the record only carries the tag."""
    fact = {"id": state_id, "reveal": reveal_rule,
            "known": reveal_rule == "public", "active": True}
    if day is not None:
        fact["since"] = day
    if slot is not None:
        fact["slot"] = slot
    return fact


def _event(world: dict, day: int | None, target_id: str, action: str,
           old_state: str | None = None,
           new_state: str | None = None) -> None:
    event = {"day": day, "target": target_id, "action": action}
    if old_state is not None:
        event["old_state"] = old_state
    if new_state is not None:
        event["new_state"] = new_state
    world.setdefault("events", []).append(event)


def add_state(world: dict, place: dict, state_id: str, *,
              day: int | None = None, reveal_rule: str = "public",
              slot: str | None = None) -> dict:
    existing = next((s for s in place["states"]
                     if s["id"] == state_id and s.get("active")), None)
    if existing:
        return existing
    state = _fact(state_id, reveal_rule, day, slot)
    place["states"].append(state)
    _event(world, day, place["id"], "add_state", new_state=state_id)
    return state


def replace_state(world: dict, place: dict, old_state_id: str,
                  new_state_id: str, *, day: int | None = None) -> dict:
    clear_state(world, place, old_state_id, day=day, record=False)
    state = next((s for s in place["states"]
                  if s["id"] == new_state_id), None)
    if state is None:
        state = _fact(new_state_id, day=day)
        place["states"].append(state)
    else:
        state["active"] = state["known"] = True
        if day is not None:
            state["since"] = day    # a state that comes back is dated by
                                    # its return, not by its first turn
    _event(world, day, place["id"], "replace_state",
           old_state=old_state_id, new_state=new_state_id)
    return state


def clear_state(world: dict, place: dict, state_id: str, *,
                day: int | None = None, record: bool = True) -> bool:
    changed = False
    for state in place["states"]:
        if state["id"] == state_id and state.get("active"):
            state["active"] = False
            changed = True
    if changed and record:
        _event(world, day, place["id"], "clear_state", old_state=state_id)
    return changed


def active_known_facts(place: dict) -> list[dict]:
    return [fact for key in ("states", "features")
            for fact in place.get(key, ())
            if fact.get("active", True) and fact.get("known")]


def find_place(world: dict, query: str) -> dict | None:
    query = query.lower()
    stores = (world["lands"], world["areas"], world["sites"], world["rooms"])
    exact = []
    partial = []
    for store in stores:
        for key, value in store.items():
            if query in (key.lower(), value.get("id", "").lower(),
                         value.get("name", "").lower()):
                exact.append(value)
            elif query in key.lower() or query in value.get("name", "").lower():
                partial.append(value)
    return (exact or partial or [None])[0]


def place_debug_lines(world: dict, place: dict) -> list[str]:
    lines = [
        f"ID: {place.get('id', place.get('key'))}",
        f"name: {place['name']}",
        f"template/source: {place.get('template', '-')} / "
        f"{place.get('source', 'authored')}",
        f"seed: {place.get('seed', '-')}",
        f"known/visited: {place.get('known', True)} / "
        f"{place.get('visited', False)}",
    ]
    for key in ("owner", "culture", "homeland", "kind",
                "subtype", "role", "domain", "level", "description",
                "discovered_day", "founded_day", "founded_for"):
        if key in place and place[key] not in (None, ""):
            lines.append(f"{key}: {place[key]}")
    for key in ("tags", "features", "states", "services", "occupants",
                "quests", "quest_ids", "used_natural_sites",
                "natural_site_order", "links"):
        if key in place:
            lines.append(f"{key}: {place[key]}")
    children = (place.get("areas") or place.get("sites")
                or place.get("rooms") or [])
    lines.append(f"children: {children}")
    if "contents" in place:
        lines.append(f"contents: {place['contents']}")
    return lines


OBSOLETE_CATALOG_KEYS = ("land_order", "adjacency", "travel_links",
                         "water_links")
OBSOLETE_LAND_KEYS = ("settlements", "descriptions", "villages",
                      "village_sites", "village_descriptions",
                      "settlement_sites")
# What a settlement template may ask its Tile for. Until 2026-08-21 this
# was POSITION only (plus the three bare biome words), so the only thing a
# town could want was a shore, a ford or a mountain at its back. The ground
# session added CHARACTER: the terrain word and the words the law derives,
# which is how a hill town lands on hills and a fen village on the fen.
# `mountains` is deliberately absent -- nobody settles the high ground, and
# `mountain-foot` is the word for living under it.
TILE_FIT_TAGS = ("coast", "riverside", "mountain-foot", "border", "island",
                 "river", "plains", "hills", "marsh", "forest", "farmland",
                 "pasture", "steppe")


def validate_catalog() -> None:
    if _CATALOG.get("version") != 3:
        raise ValueError("place catalog must be version 3: cultures and "
                         "lands")
    if len(LAND_SPECS) != 9:
        raise ValueError(f"the map is nine countries, catalog has "
                         f"{len(LAND_SPECS)}")
    if any(key in _CATALOG for key in OBSOLETE_CATALOG_KEYS):
        raise ValueError("place catalog still contains obsolete geography")
    for country, spec in LAND_SPECS.items():
        missing = [key for key in ("name", "culture", "tongue",
                                   "description") if not spec.get(key)]
        if missing:
            raise ValueError(f"{country}: a land record is a name, a "
                             f"culture, a tongue and a description; "
                             f"missing {missing}")
        if spec["culture"] not in CULTURE_SPECS:
            raise ValueError(f"{country}: no such culture: "
                             f"{spec['culture']}")
        if country not in COUNTRY_LETTERS.values():
            raise ValueError(f"{country}: no letter on the country overlay")
    unworn = [culture for culture in CULTURE_SPECS
              if not CULTURE_LANDS[culture]]
    if unworn:
        raise ValueError(f"a culture no country wears: {unworn}")
    for polity, land in CULTURE_SPECS.items():
        stale = [key for key in OBSOLETE_LAND_KEYS if key in land]
        if stale:
            raise ValueError(f"{polity}: the fixed settlement census is "
                             f"gone; drop {stale}")
        if "environment" in land:
            raise ValueError(f"{polity}: the environment profile retired "
                             f"with the climate overlay (2026-08-21)")
        natural = land["natural"]
        missing = [character for character in NATURAL_CHARACTERS
                   if character != "sea" and character not in natural]
        if missing:
            raise ValueError(f"{polity}: every ground a Tile can be needs a "
                             f"natural inventory; missing {missing}")
        for character, keys in natural.items():
            if character not in NATURAL_CHARACTERS:
                raise ValueError(f"{polity}: no such ground: {character}")
            if not keys:
                raise ValueError(f"{polity}/{character}: no inventory")
            for key in keys:
                if key not in land["natural_sites"]:
                    raise ValueError(f"{polity}/{character}: no such "
                                     f"natural inventory: {key}")
        unused = [key for key in land["natural_sites"]
                  if not any(key in keys for keys in natural.values())]
        if unused:
            raise ValueError(f"{polity}: authored natural inventory no "
                             f"ground draws from: {unused}")
        templates = land["settlement_templates"]
        tiers = {spec["tier"] for spec in templates.values()}
        # METROPOLIS is deliberately absent: it draws the city role until
        # the Settlements-revisited round gives it its own (2026-08-21).
        if tiers != {"capital", "city", "town", "village", "hamlet"}:
            raise ValueError(f"{polity}: settlement templates must cover "
                             f"capital, city, town, village and hamlet; "
                             f"got {sorted(tiers)}")
        capitals = [r for r, s in templates.items()
                    if s["tier"] == "capital"]
        if len(capitals) != 1:
            raise ValueError(f"{polity}: expected one capital template, "
                             f"got {capitals}")
        for tier in ("city", "town", "village", "hamlet"):
            free = [r for r, s in templates.items()
                    if s["tier"] == tier and not s["fits"]]
            if not free:
                raise ValueError(
                    f"{polity}: every tier needs a {tier} template that "
                    f"asks for no Tile tag, or a plain inland Tile can "
                    f"draw nothing")
        for role, spec in templates.items():
            bad = [tag for tag in spec["fits"] if tag not in TILE_FIT_TAGS]
            if bad:
                raise ValueError(f"{polity}/{role}: no such Tile tag: {bad}")
            if spec["tier"] == "metropolis":
                raise ValueError(f"{polity}/{role}: a metropolis wears the "
                                 f"city role; it has none of its own yet")
    for aid, specs in {**NATURAL_SITE_SPECS,
                       **SETTLEMENT_SITE_SPECS}.items():
        for site in specs:
            for room in site.get("rooms", ()):
                if not room.get("anchors"):
                    pool = _room_pool(room["name"], site["name"])
                    if pool not in ROOM_CONTENT_POOLS:
                        raise ValueError(
                            f"{aid}: {site['name']} / {room['name']} "
                            "has no anchors or pool")
    for value in json.dumps(_CATALOG, ensure_ascii=False):
        if ord(value) > 127:
            raise ValueError("place catalog contains non-ASCII output")
    if set(SETTLEMENT_NAMES) != set(COUNTRIES):
        raise ValueError("every country keeps its own settlement name "
                         f"pools; got {sorted(SETTLEMENT_NAMES)}")
    for country in COUNTRIES:
        # Every tier the census can roll GENERATED needs a name reserve;
        # metropolis carries none because it never rolls one.
        pools = SETTLEMENT_NAMES[country]
        if set(pools) != {"city", "town", "village", "hamlet"}:
            raise ValueError(f"{country}: the name reserves are the four "
                             f"generated tiers; got {sorted(pools)}")
        for tier, names in pools.items():
            if not names or len(names) != len(set(names)):
                raise ValueError(f"invalid {country} {tier} name reserve")
        taken = [name for names in pools.values() for name in names]
        if len(taken) != len(set(taken)):
            raise ValueError(f"{country}: a settlement name is in two "
                             f"reserves")
    _validate_fixed_data(load_europe_map())


validate_catalog()
