"""Persistent procedural places for RPG2.

The checked-in catalog contains the accepted ordinary content from
placegen.md.  This module owns deterministic materialization, lightweight
Room contents, knowledge, place mutation, and place-oriented readouts.  It
does not own encounter budgets or quest rewards.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from pathlib import Path
from typing import Iterable


CATALOG_PATH = Path(__file__).with_name("place_catalog.json")
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
CULTURE_PROFILES = {
    land["culture"]: {"homeland": polity,
                      "environment": land["environment"]}
    for polity, land in LAND_SPECS.items()
}
AREA_SPECS: dict[str, dict] = {}
SETTLEMENT_SITE_SPECS: dict[str, list[dict]] = {}
NATURAL_SITE_SPECS: dict[str, list[dict]] = {}


def slug(text: str) -> str:
    text = text.lower().replace("'", "")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def land_id(value: str) -> str:
    return value if value.startswith("land/") else f"land/{value}"


def area_id(land: str, name: str) -> str:
    return f"area/{land.removeprefix('land/')}/{slug(name)}"


def stable_seed(world_seed: int | None, parent_id: str, purpose: str,
                sequence: int) -> int:
    """Derive a process-independent child seed from stable ASCII inputs."""
    payload = f"{world_seed}|{parent_id}|{purpose}|{sequence}".encode("ascii")
    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(),
                          "big")


def _build_definition_indexes() -> None:
    for polity, land in LAND_SPECS.items():
        for name, subtype, role, tags in land["natural"]:
            aid = area_id(polity, name)
            AREA_SPECS[aid] = {
                "id": aid, "name": name, "kind": "natural",
                "subtype": subtype, "role": role, "tags": tuple(tags),
                "description": land["descriptions"][name],
            }
            specs = land["natural_sites"][name]
            NATURAL_SITE_SPECS[aid] = specs
        for name, tier, role, tags in land["settlements"]:
            aid = area_id(polity, name)
            AREA_SPECS[aid] = {
                "id": aid, "name": name, "kind": "settlement",
                "subtype": tier, "role": role, "tags": tuple(tags),
                "description": land["descriptions"][name],
            }
            SETTLEMENT_SITE_SPECS[aid] = land["settlement_sites"][name]


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
                              "human yard", "foreign yard")):
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


def _new_area_record(spec: dict, polity: str, world_seed: int | None,
                     index: int, source: str = "authored") -> dict:
    aid = spec["id"]
    is_settlement = spec["kind"] == "settlement"
    tags = list(spec["tags"])
    if is_settlement:
        land = LAND_SPECS[polity]
        tags.extend(("settlement", spec["subtype"], land["culture"],
                     polity))
    return {
        "id": aid, "key": aid, "name": spec["name"],
        "land": polity, "kind": spec["kind"], "subtype": spec["subtype"],
        "culture": LAND_SPECS[polity]["culture"], "homeland": polity,
        "role": spec["role"], "description": spec["description"],
        "source": source, "template": aid,
        "seed": stable_seed(world_seed, f"land/{polity}", "area", index),
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
        "areas": [], "neighbors": list(_CATALOG["adjacency"][polity]),
        "features": [], "states": [], "links": [], "sequences": {},
        "discovery_order": [], "reserve": [],
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
    sid = (f"site/{area['land']}/{slug(area['name'])}/"
           f"{slug(spec['name'])}/{sequence}")
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
    if area["subtype"] == "capital":
        required |= {"alchemist", "market", "government"}
    missing = required - seen
    if missing:
        raise ValueError(f"{area['name']} lacks required services: "
                         f"{sorted(missing)}")


def _generated_village_spec(polity: str, role_id: str, name: str,
                            tags: list[str]) -> dict:
    land = LAND_SPECS[polity]
    aid = area_id(polity, name)
    return {
        "id": aid, "name": name, "kind": "settlement",
        "subtype": "village", "role": role_id, "tags": tuple(tags),
        "description": land["village_descriptions"][role_id],
    }


# --------------------------------------------------------------------------- #
# THE SETTLEMENT TRIM (2026-08-07 -- the worldsim ladder's first rung)
# --------------------------------------------------------------------------- #
# A land BEGINS with three settlements: one capital, one town, one village.
# Everything else the catalog holds is the RESERVE POOL -- unbuilt names and
# skeletons that materialize only when something needs them to EXIST (a
# relation names a rival center of power, a card needs a counterparty port).
# This is places.py's own lazy Site/house pattern lifted one tier: the
# catalog stopped being the world's census and became its reserve, so places
# arrive because the world asked for them, not because a table was filled in
# advance. A land whose reserve runs dry simply says no (see
# `materialize_settlement`) -- the world stays finite.
SETTLEMENTS_AT_WORLDGEN = 3
OPENING_TIERS = ("town", "village")     # beside the capital, in draw order


def _reserve_entry(name: str, tier: str, role: str, tags: Iterable[str],
                   source: str) -> dict:
    """One unbuilt settlement: the name, the skeleton it will be built from,
    and the tags a need is matched against. Plain JSON -- it rides the save."""
    return {"name": name, "tier": tier, "role": role,
            "tags": list(tags), "source": source}


def _land_reserve(polity: str, spec: dict,
                  world_seed: int | None) -> list[dict]:
    """The land's unbuilt settlements in the stable order they are drawn in:
    the catalog's remaining towns first (hand-written skeletons), then its
    villages -- authored ones before the generated roles, which pair the
    land's name pool with its village roles in rotation."""
    towns, authored_villages, generated = [], [], []
    for name, tier, role, tags in spec["settlements"]:
        if tier == "capital":
            continue
        entry = _reserve_entry(name, tier, role, tags, "authored")
        (authored_villages if tier == "village" else towns).append(entry)
    roles = [(role_id, tags) for role_id, _heading, tags in spec["villages"]]
    if roles:
        names = list(spec["village_names"])
        random.Random(stable_seed(world_seed, f"land/{polity}",
                                  "generated-villages", 0)).shuffle(names)
        for index, name in enumerate(names):
            role_id, tags = roles[index % len(roles)]
            generated.append(_reserve_entry(name, "village", role_id, tags,
                                            "worldgen"))
    rng = random.Random(stable_seed(world_seed, f"land/{polity}",
                                    "settlement-reserve", 0))
    rng.shuffle(towns)
    rng.shuffle(authored_villages)
    return towns + authored_villages + generated


def _reserve_build(polity: str, entry: dict) -> tuple[dict, list[dict]]:
    """The Area spec and required-Site skeleton behind one reserve entry."""
    land = LAND_SPECS[polity]
    if entry["source"] == "authored":
        aid = area_id(polity, entry["name"])
        return dict(AREA_SPECS[aid]), SETTLEMENT_SITE_SPECS[aid]
    spec = _generated_village_spec(polity, entry["role"], entry["name"],
                                   entry["tags"])
    return spec, land["village_sites"][entry["role"]]


def _add_settlement(world: dict, polity: str, entry: dict, *,
                    day: int | None = None,
                    need: str | None = None) -> dict:
    """Build one settlement Area out of a reserve entry: the Area record, its
    required Sites and Rooms, and its guaranteed services. `need` marks the
    ones the world asked for after worldgen (the opening three pass None)."""
    land = world["lands"][polity]
    spec, site_specs = _reserve_build(polity, entry)
    area = _new_area_record(spec, polity, world["seed"],
                            len(land["areas"]) + 1, entry["source"])
    world["areas"][area["id"]] = area
    land["areas"].append(area["id"])
    sites = [materialize_site(world, area, site_spec, source="authored",
                              domain="built", known=True,
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
    """What the land can still be asked to grow -- read before committing to
    a card or a relation that names a place the world may not hold."""
    return [entry for entry in world["lands"][polity]["reserve"]
            if tier is None or entry["tier"] == tier]


def materialize_settlement(world: dict, polity: str, *,
                           need: str, tier: str | None = None,
                           tags: Iterable[str] = (),
                           day: int | None = None) -> dict | None:
    """Draw the next settlement out of a land's reserve because something
    needs it to exist. `tier` narrows the draw, `tags` prefer a fitting
    skeleton (a port for a counterparty port), and `need` is recorded on the
    Area as the reason it was founded.

    Returns None when the reserve holds nothing that fits: the world is
    finite, and a card whose counterparty cannot be built simply does not
    fire (the exclusive-slot discipline, applied to geography)."""
    reserve = world["lands"][polity]["reserve"]
    pool = [entry for entry in reserve
            if tier is None or entry["tier"] == tier]
    wanted = set(tags)
    entry = next((e for e in pool if wanted.intersection(e["tags"])),
                 pool[0] if pool else None)
    if entry is None:
        return None
    reserve.remove(entry)
    return _add_settlement(world, polity, entry, day=day, need=need)


def create_geography(seed: int | None) -> dict:
    """Create the finite Lands and natural Areas, and open every land with
    its three settlements (the trim) -- the rest of the catalog becomes the
    land's reserve, drawn on need by `materialize_settlement`."""
    world = {
        "seed": seed, "lands": {}, "areas": {}, "sites": {}, "rooms": {},
        "quests": {}, "npcs": [], "events": [],
        "links": list(_CATALOG["travel_links"]),
        "water_links": list(_CATALOG["water_links"]),
    }
    for land_index, polity in enumerate(_CATALOG["land_order"], 1):
        spec = LAND_SPECS[polity]
        land = _new_land_record(polity, spec, seed, land_index)
        world["lands"][polity] = land
        natural_ids = []
        for index, (name, _subtype, _role, _tags) in enumerate(
                spec["natural"], 1):
            aid = area_id(polity, name)
            area = _new_area_record(AREA_SPECS[aid], polity, seed, index)
            world["areas"][aid] = area
            land["areas"].append(aid)
            natural_ids.append(aid)
        # The opening three (the trim): the authored capital, then a town and
        # a village drawn off the reserve. A land whose catalog is short of a
        # tier tops up from the head of what is left, so every country still
        # opens with three.
        capital = next(entry for entry in spec["settlements"]
                       if entry[1] == "capital")
        _add_settlement(world, polity,
                        _reserve_entry(capital[0], "capital", capital[2],
                                       capital[3], "authored"))
        land["reserve"] = _land_reserve(polity, spec, seed)
        opening = []
        for tier in OPENING_TIERS:
            opening.extend([entry for entry in land["reserve"]
                            if entry["tier"] == tier][:1])
        for entry in land["reserve"]:
            if len(opening) >= SETTLEMENTS_AT_WORLDGEN - 1:
                break
            if entry not in opening:
                opening.append(entry)
        for entry in opening:
            land["reserve"].remove(entry)
            _add_settlement(world, polity, entry)
        order_rng = random.Random(
            stable_seed(seed, land["id"], "area-discovery", 0))
        order_rng.shuffle(natural_ids)
        land["discovery_order"] = natural_ids
        for aid in natural_ids:
            site_specs = NATURAL_SITE_SPECS[aid]
            ids = [spec["id"] for spec in site_specs]
            site_rng = random.Random(
                stable_seed(seed, aid, "natural-site-order", 0))
            site_rng.shuffle(ids)
            world["areas"][aid]["natural_site_order"] = ids

    for polity, land in world["lands"].items():
        routed_pairs = {
            frozenset((link["a"], link["b"])) for link in world["links"]
        }
        land["links"] = [
            {"target": neighbor, "kind": "border"}
            for neighbor in land["neighbors"]
            if frozenset((polity, neighbor)) not in routed_pairs
        ]
        for link in world["links"]:
            if polity == link["a"]:
                land["links"].append({**link, "target": link["b"]})
            elif polity == link["b"]:
                land["links"].append({**link, "target": link["a"]})
    for water in world["water_links"]:
        ids = [f"area/{value}" for value in water["areas"]]
        for left, right in zip(ids, ids[1:]):
            if left in world["areas"] and right in world["areas"]:
                world["areas"][left]["links"].append(
                    {"target": right, "kind": "river",
                     "name": water["name"]})
                world["areas"][right]["links"].append(
                    {"target": left, "kind": "river",
                     "name": water["name"]})
    return world


def land_homeland(world: dict, polity: str) -> str:
    """The country a local person calls home."""
    return world["lands"][polity]["homeland"]


def land_culture(world: dict, polity: str) -> str:
    return world["lands"][polity]["culture"]


def discover_area(world: dict, polity: str, day: int) -> dict | None:
    """Reveal the next finite natural Area in its stable shuffled order."""
    land = world["lands"][polity]
    for aid in land["discovery_order"]:
        area = world["areas"][aid]
        if not area["known"]:
            area["known"] = True
            area["discovered_day"] = day
            _event(world, day, aid, "reveal")
            return area
    return None


def materialize_natural_site(world: dict, area: dict | str,
                             day: int | None = None) -> dict | None:
    if isinstance(area, str):
        area = world["areas"][area]
    if area["kind"] != "natural":
        raise ValueError("natural Sites require a natural Area")
    used = set(area["used_natural_sites"])
    template_id = next((sid for sid in area["natural_site_order"]
                        if sid not in used), None)
    if template_id is None:
        return None
    spec = next(s for s in NATURAL_SITE_SPECS[area["template"]]
                if s["id"] == template_id)
    site = materialize_site(world, area, spec, source="lazy",
                            domain="natural", known=True,
                            purpose="natural-site")
    area["used_natural_sites"].append(template_id)
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


def validate_catalog() -> None:
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


validate_catalog()
