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
from pathlib import Path
from typing import Iterable


CATALOG_PATH = Path(__file__).with_name("place_catalog.json")
EUROPE_MAP_PATH = Path(__file__).with_name("resources") / "europe_map.txt"
with CATALOG_PATH.open(encoding="utf-8") as _catalog_file:
    _CATALOG = json.load(_catalog_file)


# The `weather` table is the climate SENTENCE made mechanical (2026-08-08,
# the worldsim ladder's weather session): the day-roll's weights over
# worldsim.WEATHER_WORDS, per hundred days, YEAR-ROUND -- the game has no
# season track, so a profile's winters and summers are averaged into one
# distribution rather than modelled. worldsim.py owns the roll, the states
# and the cards; the profile only says what this ground's sky does.
#
# `drought_days` is how many rainless days THIS ground calls a drought, and
# it is per-profile because a drought is a RELATIVE thing: a fortnight
# without rain is a disaster in the shaded forest and an ordinary Tuesday in
# the dry south. Each is set so a land's drought is about a one-in-a-hundred
# day (worldsim's own card chance thins it further from there) -- without
# that, the wet lands could never have one at all and the dry ones would
# never be out of it.
ENVIRONMENT_PROFILES = {
    "alpine_tundra": {
        "climate": "Cold, windy highlands with long winters and short summers.",
        "vegetation": ("mountain pine", "juniper", "lichen", "moss",
                       "alpine grass", "mountain flowers"),
        "weather": {"clear": 18, "cloud": 18, "wind": 18, "rain": 6,
                    "storm": 6, "fog": 6, "frost": 14, "snow": 14, "heat": 0},
        "drought_days": 15,
    },
    "temperate": {
        "climate": "Mild country with rain, cloud, wind, fog, and winter frost.",
        "vegetation": ("oak", "beech", "ash", "elm", "hedges",
                       "meadow grass", "reeds"),
        "weather": {"clear": 22, "cloud": 25, "wind": 10, "rain": 21,
                    "storm": 5, "fog": 8, "frost": 9, "snow": 0, "heat": 0},
        "drought_days": 15,
    },
    "temperate_forest": {
        "climate": "A damp, shaded forest with rain, mist, and winter frost.",
        "vegetation": ("oak", "beech", "birch", "fern", "bramble",
                       "moss", "mushrooms"),
        "weather": {"clear": 16, "cloud": 24, "wind": 5, "rain": 26,
                    "storm": 5, "fog": 16, "frost": 8, "snow": 0, "heat": 0},
        "drought_days": 12,
    },
    "mediterranean": {
        "climate": "Hot dry summers, mild wet winters, and sea wind.",
        "vegetation": ("olive", "cypress", "pine", "scrub oak",
                       "grapevine", "rosemary", "dry grass"),
        "weather": {"clear": 38, "cloud": 14, "wind": 15, "rain": 13,
                    "storm": 4, "fog": 4, "frost": 2, "snow": 0, "heat": 10},
        "drought_days": 25,
    },
    "prairie": {
        "climate": "Windy grassland with hot summers and cold winters.",
        "vegetation": ("tall grass", "short grass", "sage", "wildflowers",
                       "reeds", "willow"),
        "weather": {"clear": 26, "cloud": 15, "wind": 23, "rain": 12,
                    "storm": 6, "fog": 3, "frost": 7, "snow": 3, "heat": 5},
        "drought_days": 20,
    },
}

LAND_SPECS = _CATALOG["lands"]
COUNTRIES = tuple(LAND_SPECS)
AREA_SPECS: dict[str, dict] = {}
SETTLEMENT_SITE_SPECS: dict[str, list[dict]] = {}
NATURAL_SITE_SPECS: dict[str, list[dict]] = {}

MAP_ROWS = 18
MAP_COLUMNS = 30
BIOME_GLYPHS = {".": "sea", "#": "basic", "^": "mountain",
                "~": "river"}
PINNED_BIOME_COUNTS = {"basic": 266, "mountain": 29, "river": 21,
                       "sea": 224}
PINNED_COUNTRY_BIOMES = {
    "firascir": {"basic": 81, "mountain": 11, "river": 5},
    "mortellaria": {"basic": 117, "mountain": 15, "river": 12},
    "tergal": {"basic": 68, "mountain": 3, "river": 4},
}
PINNED_LAND_COMPONENTS = (302, 11, 2, 1)

HISTORICAL_CITIES = (
    (5, 2, "Dublin", "firascir", "basic", False),
    (6, 5, "London", "firascir", "basic", False),
    (8, 12, "Amsterdam", "firascir", "river", False),
    (9, 10, "Paris", "firascir", "basic", True),
    (9, 18, "Prague", "firascir", "basic", False),
    (3, 23, "Stockholm", "tergal", "basic", False),
    (7, 28, "Moscow", "tergal", "basic", False),
    (8, 22, "Warsaw", "tergal", "basic", False),
    (10, 27, "Kyiv", "tergal", "river", True),
    (13, 3, "Lisbon", "mortellaria", "river", False),
    (13, 7, "Madrid", "mortellaria", "basic", False),
    (12, 14, "Venice", "mortellaria", "river", False),
    (14, 14, "Rome", "mortellaria", "basic", True),
    (14, 19, "Athens", "mortellaria", "basic", False),
    (14, 27, "Constantinople", "mortellaria", "basic", False),
    (17, 12, "Carthage", "mortellaria", "basic", False),
)
HISTORICAL_BY_TILE = {(row, column): (name, country, biome, capital)
                      for row, column, name, country, biome, capital
                      in HISTORICAL_CITIES}

SETTLEMENT_DENSITY = {
    "mortellaria": (0.10, 0.35),
    "firascir": (0.06, 0.24),
    "tergal": (0.03, 0.17),
}

# SPARSE ORDINARY BOARDS (2026-08-15, Local Quest Geography). A settlement
# is not a job dispenser: at materialization a stable derived roll decides
# whether this one normally posts ORDINARY generated work at all. A capital
# always does, a town usually does, a village usually does not -- and a
# village with no work is a correct village, not a bug. What the flag gates
# is `quests.board_slots` (ordinary capacity); the forced families -- story
# waves, world-card jobs, deliveries, pact assignments, punishment and the
# DM's own forged work -- post at an inactive board regardless and never
# turn it into an active one. The starting settlement is forced active by
# `create_geography`, because the opening quest has to have somewhere to be.
BOARD_ACTIVE_CHANCE = {"capital": 1.00, "town": 0.60, "village": 0.25}
SETTLEMENT_NAMES = {
    "firascir": {
        "town": ("Tomburgh", "Leehaven", "Walhaven", "Bradwhitchip",
                 "Redflurton"),
        "village": ("Sturford", "Ackham", "Flurham", "Sturham",
                    "Sturworth", "Newton", "Midton", "Aston", "Tomton",
                    "Walham", "Coldcot", "Thornley", "Blackton",
                    "Astmoor", "Ackbridge", "Ackton", "Mickleham",
                    "Shepham"),
    },
    "mortellaria": {
        "town": ("Castavera", "Portomera", "Belafonte", "Montaro"),
        "village": ("Alavera", "Beloro", "Calavento", "Doramonte",
                    "Fontela", "Lunaro", "Maravento", "Oliveta",
                    "Rosavera", "Sanoro", "Solavela", "Toralba",
                    "Valesero", "Ventoro", "Vilaro"),
    },
    "tergal": {
        "town": ("Ulus-Gal", "Kharuk", "Temenur", "Ordubal"),
        "village": ("Aradun", "Balurun", "Borkal", "Enkhar", "Eshkar",
                    "Guratai", "Kharnam", "Kurugan", "Namuruk", "Ordaki",
                    "Sargul", "Teguren", "Tumengal", "Urkhal", "Zamutar"),
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


def template_id(polity: str, role: str) -> str:
    """The catalog key of one country's settlement role. Never a runtime ID:
    a settlement Area is named by its SLOT and scoped under its Tile, so the
    template it was cut from has to live in a namespace of its own."""
    return f"template/settlement/{polity}/{role}"


def stable_seed(world_seed: int | None, parent_id: str, purpose: str,
                sequence: int) -> int:
    """Derive a process-independent child seed from stable ASCII inputs."""
    payload = f"{world_seed}|{parent_id}|{purpose}|{sequence}".encode("ascii")
    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(),
                          "big")


def _build_definition_indexes() -> None:
    for polity, land in LAND_SPECS.items():
        natural = list(land.get("natural", ()))
        by_biome = {
            "river": next((entry for entry in natural
                           if entry[1] == "river"), natural[0]),
            "mountain": next((entry for entry in natural
                              if entry[1] in ("hills", "ridge")),
                             natural[0]),
            "basic": next((entry for entry in natural
                           if entry[1] != "river"), natural[0]),
        }
        for biome, entry in by_biome.items():
            template = f"natural/{polity}/{biome}"
            NATURAL_SITE_SPECS[template] = land["natural_sites"][entry[0]]
        NATURAL_SITE_SPECS[f"natural/{polity}/sea"] = [
            {"id": "open-water", "name": "OPEN WATER", "rooms": [],
             "anchors": ["long swell", "distant gulls", "floating weed"]},
            {"id": "shoal", "name": "SHOAL", "rooms": [],
             "anchors": ["pale water", "sand below", "driftwood"]},
            {"id": "rocky-islet", "name": "ROCKY ISLET", "rooms": [],
             "anchors": ["black rocks", "tide pools", "bird nests"]},
        ]
        for role, spec in land["settlement_templates"].items():
            key = template_id(polity, role)
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
        land = LAND_SPECS[polity]
        tags.extend(("settlement", spec["subtype"], land["culture"],
                     polity))
    capital = bool(spec.get("capital"))
    return {
        "id": aid, "key": aid, "name": spec["name"],
        "land": polity, "tile": tile["id"], "kind": spec["kind"],
        "subtype": spec["subtype"], "capital": capital,
        "culture": LAND_SPECS[polity]["culture"], "homeland": polity,
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
        "environment": spec["environment"],
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
    required = {"lodging", "smith", "general_goods", "healer"}
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


def country_at(row: int, column: int) -> str:
    if row >= 11:
        return "mortellaria"
    return "firascir" if column <= 21 else "tergal"


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
    if capitals != {"Paris", "Rome", "Kyiv"}:
        raise ValueError(f"historical capitals changed: {sorted(capitals)}")


def _slot(slot_id: str, tier: str, seed: int, *, name: str | None = None,
          capital: bool = False, authored: bool = False) -> dict:
    return {"id": slot_id, "tier": tier, "name": name,
            "capital": capital, "authored": authored, "area": None,
            "known": authored, "seed": seed}


def _population_slots(seed: int | None, tile: dict) -> list[dict]:
    if tile["biome"] == "sea":
        return []
    historical = HISTORICAL_BY_TILE.get((tile["row"], tile["column"]))
    if historical:
        name, _country, _biome, capital = historical
        tiers = ("town", "village", "village")
    else:
        dense, village = SETTLEMENT_DENSITY[tile["country"]]
        roll = random.Random(stable_seed(seed, tile["id"],
                                        "population", 0)).random()
        if roll < dense:
            tiers = ("village",) if tile["biome"] == "mountain" else (
                "town", "village", "village")
        elif roll < dense + village:
            tiers = ("village",)
        else:
            tiers = ()
        name, capital = None, False
    slots = []
    for index, tier in enumerate(tiers, 1):
        sid = f"{tile['id']}/settlement/{index:02d}"
        slots.append(_slot(
            sid, tier, stable_seed(seed, tile["id"], "settlement-slot", index),
            name=name if historical and index == 1 else None,
            capital=capital if index == 1 else False,
            authored=bool(historical and index == 1)))
    return slots


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
    land = LAND_SPECS[country]
    templates = land["settlement_templates"]
    if slot.get("capital"):
        role = next(r for r, spec in templates.items()
                    if spec["tier"] == "capital")
        key = template_id(country, role)
        return dict(AREA_SPECS[key]), SETTLEMENT_SITE_SPECS[key]
    have = set(tile_tags)
    roles = [role for role, spec in templates.items()
             if spec["tier"] == tier]
    if not roles:
        raise ValueError(f"{country}: no {tier} settlement template")
    fitting = [role for role in roles
               if set(templates[role]["fits"]) <= have]
    wanted = [role for role in fitting if templates[role]["fits"]] \
        or [role for role in fitting] \
        or roles
    role = wanted[slot["seed"] % len(wanted)]
    key = template_id(country, role)
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
    area["tags"] = list(dict.fromkeys(area["tags"] + tile["tags"]))
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
            tags = [biome, country]
            if biome == "river":
                tags.append("riverside")
            tile = {"id": tid, "row": row, "column": column, "name": name,
                    "country": country, "biome": biome, "known": True,
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
        suffix = {"basic": "Countryside", "mountain": "Mountains",
                  "river": "Riverlands", "sea": "Sea"}[tile["biome"]]
        aid = f"{tid}/area/natural"
        template = f"natural/{tile['country']}/{tile['biome']}"
        spec = {"id": aid, "name": f"{tile['name']} {suffix}",
                "kind": "natural", "subtype": tile["biome"],
                "role": tile["biome"], "tags": tuple(tile["tags"]),
                "description": f"{tile['name']} is {suffix.lower()}."}
        area = _new_area_record(spec, tile["country"], tile, seed, 1)
        area["template"] = template
        ids = [site["id"] for site in NATURAL_SITE_SPECS[template]]
        random.Random(stable_seed(seed, aid, "natural-site-order", 0)).shuffle(ids)
        area["natural_site_order"] = ids
        world["areas"][aid] = area
        tile["areas"].append(aid)
        tile["natural_area"] = aid
        world["lands"][tile["country"]]["areas"].append(aid)
        slots = _population_slots(seed, tile)
        for index, slot in enumerate(slots, 1):
            slot.update(tile=tid, index=index)
            world["settlement_slots"][slot["id"]] = slot
            tile["settlement_slots"].append(slot["id"])
            world["lands"][tile["country"]]["settlement_slots"].append(slot["id"])

    # Historical towns exist and are known from day zero; their villages do
    # not. Capitals materialize first so country-level cast code has a stable
    # political seat without relying on coordinate order.
    historical = [slot for slot in world["settlement_slots"].values()
                  if slot["authored"]]
    for slot in sorted(historical, key=lambda value: not value["capital"]):
        materialize_slot(world, slot, known=True)

    candidates = list(world["settlement_slots"])
    if not candidates:
        raise ValueError("fixed Europe population produced no settlement slots")
    start_slot = random.Random(stable_seed(seed, "world", "start-slot", 0)).choice(
        candidates)
    world["start_slot"] = start_slot
    start_tile = world["settlement_slots"][start_slot]["tile"]
    reveal_tile(world, start_tile, day=0)
    world["start_area"] = world["settlement_slots"][start_slot]["area"]
    # The opening settlement posts ordinary work whatever its own roll said:
    # the game has to start somewhere, and it starts at a board.
    world["areas"][world["start_area"]]["board_active"] = True
    validate_world(world)
    return world


CAPITAL_TOWNS = frozenset(name for *_r, name, _p, _b, capital
                          in HISTORICAL_CITIES if capital)


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
        raise ValueError("tile_order is not the row-major 30x18 frame")
    if set(tiles) != set(expected):
        raise ValueError("the tile store and tile_order disagree")

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
        elif tile["biome"] == "mountain":
            if any(slot["tier"] == "town" for slot in slots):
                raise ValueError(f"{tid}: only authored towns sit on a "
                                 f"mountain")
        for slot in slots:
            if slot["id"] in slot_ids:
                raise ValueError(f"duplicate settlement slot: {slot['id']}")
            slot_ids.add(slot["id"])
            if slot["tile"] != tid:
                raise ValueError(f"{slot['id']}: not scoped to its Tile")
            if slot["id"] not in \
                    world["lands"][tile["country"]]["settlement_slots"]:
                raise ValueError(f"{slot['id']}: not on its country")
            if slot["capital"]:
                capitals.add(slot["name"])

    if slot_ids != set(world["settlement_slots"]):
        raise ValueError("the slot store and the Tiles disagree")
    if capitals != CAPITAL_TOWNS:
        raise ValueError(f"the three capitals are {sorted(CAPITAL_TOWNS)}, "
                         f"got {sorted(capitals)}")
    if world["start_slot"] not in world["settlement_slots"]:
        raise ValueError("the start is not a settlement slot")
    if world["start_area"] not in world["areas"]:
        raise ValueError("the start settlement was never materialized")


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
MAP_MARK_LEGEND = "@ party  ! job  C capital  T town  v village"


def known_slots(world: dict, tile: dict | str) -> list[dict]:
    """The settlement slots on a Tile the player knows about."""
    if isinstance(tile, str):
        tile = world["tiles"][tile]
    return [world["settlement_slots"][sid] for sid in tile["settlement_slots"]
            if world["settlement_slots"][sid]["known"]]


def settlement_glyph(world: dict, tile: dict) -> str | None:
    """`C` a known capital, `T` any other known town, `v` known village(s)
    with no known town, None when nothing here is known."""
    mark = None
    for slot in known_slots(world, tile):
        if slot["capital"]:
            return "C"
        if slot["tier"] == "town":
            mark = "T"
        elif mark is None:
            mark = "v"
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


def tile_detail_lines(world: dict, tile: dict | str,
                      areas: bool = True) -> list[str]:
    """What the glyph could not say: where this Tile is, whose it is, what
    it is made of, and (unless the caller lists them itself) which of its
    Areas the party knows."""
    if isinstance(tile, str):
        tile = world["tiles"][tile]
    lines = [f"HERE: {tile_label(tile)} -- "
             f"{world['lands'][tile['country']]['name']}, {tile['biome']}"]
    extra = [tag for tag in tile["tags"]
             if tag not in (tile["biome"], tile["country"])]
    if extra:
        lines.append("  ground: " + ", ".join(extra))
    known = [world["areas"][aid] for aid in tile["areas"]
             if world["areas"][aid].get("known")]
    if areas and known:
        lines.append("  areas: " + ", ".join(area["name"] for area in known))
    return lines


def land_homeland(world: dict, polity: str) -> str:
    """The country a local person calls home."""
    return world["lands"][polity]["homeland"]


def land_culture(world: dict, polity: str) -> str:
    return world["lands"][polity]["culture"]


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
    "firascir": ("brown bread", "onions", "hard cheese", "dried apples",
                 "smoked fish", "pot of stew"),
    "mortellaria": ("flatbread", "onions", "hard cheese", "olives",
                    "smoked fish", "pot of stew"),
    "tergal": ("flatbread", "onions", "hard cheese", "dried curds",
               "smoked fish", "pot of stew"),
}
HOUSE_HEAT = {
    "firascir": ("stone hearth", "iron stove"),
    "mortellaria": ("stone hearth", "iron stove", "tiled hearth"),
    "tergal": ("stone hearth", "iron stove", "clay stove"),
}
HOUSE_LIVELIHOOD = {
    "firascir": ("account book", "fishing net", "grain sack", "reed knife",
                 "hand saw", "boat hook"),
    "mortellaria": ("account book", "fishing net", "pruning knife",
                    "olive basket", "grape basket", "sickle"),
    "tergal": ("tack repair kit", "wool bundle", "cargo tally",
               "wool shears", "salt scoop", "water skin"),
}
HOUSE_LIVELIHOOD_BY_ROLE = {
    ("firascir", "capital"):
        ("account book", "sealing wax", "guard belt", "folded cloth",
         "writing case"),
    ("firascir", "northern_harbor_city"):
        ("fishing net", "iron hooks", "cork floats", "sailcloth",
         "fish basket"),
    ("firascir", "southern_harbor_city"):
        ("cargo tally", "rope coil", "tar pot", "crate bar",
         "merchant scales"),
    ("firascir", "inland_market_town"):
        ("sickle", "grain sack", "seed basket", "harness",
         "wooden measure"),
    ("firascir", "riverside_town"):
        ("reed knife", "eel basket", "ferry rope", "waterproof boots",
         "fish trap"),
    ("firascir", "river_crossing_village"):
        ("plough blade", "grain sack", "ferry pole", "horse tack",
         "seed basket"),
    ("firascir", "forest_edge_village"):
        ("hand saw", "splitting axe", "timber wedges", "charcoal basket",
         "leather apron"),
    ("firascir", "pond_village"):
        ("fishing line", "reed basket", "cork floats", "boat hook",
         "salt sack"),
    ("mortellaria", "capital"):
        ("account book", "sealing wax", "folded cloth", "oil jar",
         "writing case"),
    ("mortellaria", "harbor_city"):
        ("fishing net", "sailcloth", "cargo tally", "tar pot",
         "fish basket"),
    ("mortellaria", "inland_market_town"):
        ("pruning knife", "olive basket", "oil measure", "pottery tools",
         "market scales"),
    ("mortellaria", "hill_town"):
        ("grape basket", "barrel hoops", "goat bell", "pruning hook",
         "wine tally"),
    ("mortellaria", "vineyard_village"):
        ("pruning knife", "grape basket", "picking net", "clay wine jug",
         "olive rake"),
    ("mortellaria", "river_plain_village"):
        ("sickle", "grain sack", "sluice key", "reed basket",
         "wooden measure"),
    ("mortellaria", "coast_road_village"):
        ("fishing line", "cork floats", "salt sack", "boat hook",
         "net needle"),
    ("tergal", "capital"):
        ("tack repair kit", "market tally", "wool bundle", "bow case",
         "seal box"),
    ("tergal", "western_town"):
        ("cargo tally", "harness", "ferry rope", "foreign coin weights",
         "crate bar"),
    ("tergal", "northern_town"):
        ("wool shears", "saddle blanket", "shepherd's crook", "bow stave",
         "salt blocks"),
    ("tergal", "southern_town"):
        ("salt scoop", "water tally", "goat bell", "clay jar",
         "caravan rope"),
    ("tergal", "herd_road_village"):
        ("horse brush", "rope halter", "feed basket", "leather needle",
         "wool shears"),
    ("tergal", "tergal_river_village"):
        ("fishing net", "ferry pole", "fish basket", "boat hook",
         "reed mat"),
    ("tergal", "tergal_basin_village"):
        ("water skin", "salt scoop", "goat tack", "reed mat",
         "well rope"),
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
    for key in ("owner", "culture", "homeland", "environment", "kind",
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
TILE_FIT_TAGS = ("coast", "riverside", "mountain-foot", "border", "island",
                 "basic", "mountain", "river", "sea")


def validate_catalog() -> None:
    if tuple(LAND_SPECS) != ("firascir", "mortellaria", "tergal"):
        raise ValueError("place catalog must define the three Europe countries")
    if any(key in _CATALOG for key in OBSOLETE_CATALOG_KEYS):
        raise ValueError("place catalog still contains obsolete geography")
    for polity, land in LAND_SPECS.items():
        stale = [key for key in OBSOLETE_LAND_KEYS if key in land]
        if stale:
            raise ValueError(f"{polity}: the fixed settlement census is "
                             f"gone; drop {stale}")
        templates = land["settlement_templates"]
        tiers = {spec["tier"] for spec in templates.values()}
        if tiers != {"capital", "town", "village"}:
            raise ValueError(f"{polity}: settlement templates must cover "
                             f"capital, town and village; got {sorted(tiers)}")
        capitals = [r for r, s in templates.items()
                    if s["tier"] == "capital"]
        if len(capitals) != 1:
            raise ValueError(f"{polity}: expected one capital template, "
                             f"got {capitals}")
        for tier in ("town", "village"):
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
            if "city" in (spec["tier"], *spec["tags"]):
                raise ValueError(f"{polity}/{role}: there is no city "
                                 f"subtype; a great town is a town")
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
    for country in COUNTRIES:
        for tier in ("town", "village"):
            names = SETTLEMENT_NAMES[country][tier]
            if not names or len(names) != len(set(names)):
                raise ValueError(f"invalid {country} {tier} name reserve")
    _validate_fixed_data(load_europe_map())


validate_catalog()
