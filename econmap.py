"""The tile economy arc's eyeball tool (2026-08-21, plan.md Part 1).

Stdlib-only, and since session 4 it renders a **BUILT WORLD**: every mode
below calls `places.create_geography(seed)` and draws what worldgen
actually stamped on the Tiles.  It no longer keeps a constant, a law or a
simulation of its own -- the arc's one-authority-per-constant rule, carried
to its end.  What is left here is the RENDERING: 30x18 letter grids with
censuses underneath, which is the one thing the game itself has no reason
to do.

    python econmap.py                  # the climate overlay + the lint
    python econmap.py terrain          # the terrain overlay + land character
    python econmap.py potential        # the derived numbers under the words
    python econmap.py harvest [SEED]   # one world's last harvest
    python econmap.py population [SEED]   # one world's settlement census
    python econmap.py routes [SEED]    # the mines, goods and trade routes
    python econmap.py character [SEED] # what each Tile is CALLED

The `--sweep` commands are GONE (2026-08-21, session 4).  Measuring the
layers over many worlds is a bench, not an eyeball, and it belongs to a
suite whose numbers land in benchlog: **`python bench_worldgen.py`**.

THE OVERLAY LINT still reads the two resource files directly, because it
has to survive a half-drawn overlay -- a world cannot be built from one.
Every land tile carries exactly one climate letter, sea carries none, and
`a` (alpine) / `m` (mountains) sit exactly on the `^` tiles.  Everything
after the lint is read off the world.

What the modes show, in the order the arc built them:

  CLIMATE and TERRAIN are the two hand-painted overlays (rounds 1 and 2).
  Relief and drainage are authored; FOREST IS NOT -- the wildwood cap comes
  from climate and the deforestation law decides what survives, so deep
  forest appears exactly where people are few.

  POTENTIAL is the law over them: arable from climate x terrain (+ the
  alluvial bonus), clearance a saturating function of potential wheat, and
  realized arable and surviving forest falling out of it.  Deterministic --
  identical in every campaign, like the map.

  HARVEST is last year's, rolled per world: contiguous problem REGIONS
  seeded where the climate fails, each with a cause (drought, the great
  rains, frost), grown outward by contagion.  One drought is guaranteed,
  and since it is the real layer being drawn, the nearby-trouble nudge is
  in it: a region usually sits within five days of the start.

  POPULATION is the deterministic score bucketed into six bands, and the
  rolled census over it -- the arrangement tables, the authored historical
  tiers, the mine towns, the charters and the manors.

  ROUTES is the trade network: authored mines and colour, derived produce
  by law, and the computed origin-to-market roads plus the five legendary
  ones.

  CHARACTER is session 4's read surface -- the one phrase a Tile is called
  by, which is what the DM actually speaks.

THE SCALE DOCTRINE (round 3, kept here because the designer will ask):
  - A tile is SPOKEN OF as 30 km east-west by 60 km north-south (one travel
    day east-west, two north-south; 1800 km2).
  - The drawn map corresponds to real Europe at roughly 160 km per column
    and 220 km per row (about 35,000 km2 per tile): the height is 1.4x the
    width, NOT the 2x the travel costs suggest.  The map is a deliberately
    squashed Europe; north-south travel is priced by the fictional 60 km.
  - By AREA the game world is therefore about 20x smaller than the real
    one.  Real, historical or downscaled densities are NEVER an input: the
    tile is the unit and the census IS the population.
  - Slots: at most 4 a tile, a 2x2 lattice 15 km apart east-west and 30 km
    north-south.  A settlement every 15-30 km is medieval market-day
    spacing; that is why four is the cap.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import places                   # the one authority for every layer below

RESOURCES = Path(__file__).with_name("resources")
BASE_PATH = RESOURCES / "europe_map.txt"

ROWS, COLUMNS = places.MAP_ROWS, places.MAP_COLUMNS
BASE_GLYPHS = {".", "#", "^", "~"}
CLIMATES = places.CLIMATE_LETTERS
TERRAINS = places.TERRAIN_LETTERS


# --------------------------------------------------------------------------- #
# The overlay lint (the only thing that reads a file rather than a world)
# --------------------------------------------------------------------------- #

def load_grid(path: Path, legal: set[str]) -> list[str]:
    rows = path.read_text(encoding="ascii").splitlines()
    if len(rows) != ROWS:
        sys.exit(f"{path.name}: expected {ROWS} rows, got {len(rows)}")
    for number, row in enumerate(rows, 1):
        if len(row) != COLUMNS:
            sys.exit(f"{path.name}: row {number} has {len(row)} columns; "
                     f"expected {COLUMNS}")
        for column, glyph in enumerate(row, 1):
            if glyph not in legal:
                sys.exit(f"{path.name}: invalid glyph {glyph!r} at "
                         f"row {number}, column {column}")
    return rows


def lint_overlay(base: list[str], overlay: list[str],
                 high: str, what: str) -> list[str]:
    """Every land tile painted, sea unpainted, and the high-ground letter
    exactly on the `^` tiles. `validate_world` says the same thing about a
    BUILT world; this says it about a half-drawn file, which is the case a
    world cannot be made for."""
    problems = []
    for r in range(ROWS):
        for c in range(COLUMNS):
            ground, label = base[r][c], overlay[r][c]
            where = f"R{r + 1:02d}C{c + 1:02d}"
            if ground == "." and label != ".":
                problems.append(f"{where}: sea tile carries {label!r}")
            elif ground != "." and label == ".":
                problems.append(f"{where}: land tile ({ground}) unpainted")
            elif ground == "^" and label != high:
                problems.append(f"{where}: mountain painted {label!r}, "
                                f"expected {high!r} ({what})")
            elif ground != "^" and label == high:
                problems.append(f"{where}: {what} off the mountain "
                                f"({ground!r})")
    return problems


def run_lint() -> None:
    base = load_grid(BASE_PATH, BASE_GLYPHS)
    climate = load_grid(places.CLIMATE_PATH, set(CLIMATES) | {"."})
    terrain = load_grid(places.TERRAIN_PATH, set(TERRAINS) | {"."})
    problems = (lint_overlay(base, climate, "a", "alpine")
                + lint_overlay(base, terrain, "m", "mountains"))
    if problems:
        for line in problems:
            print(f"LINT: {line}")
        sys.exit(f"{len(problems)} problem(s) -- fix the overlay")


# --------------------------------------------------------------------------- #
# Rendering a built world
# --------------------------------------------------------------------------- #

def render_side_by_side(left: list[str], right: list[str],
                        titles: tuple[str, str]) -> None:
    gap = "   "
    print(f"     {titles[0]:<{COLUMNS}}{gap}  {titles[1]}")
    tens = "".join(str((c // 10)) for c in range(1, COLUMNS + 1))
    ones = "".join(str(c % 10) for c in range(1, COLUMNS + 1))
    print(f"     {tens}{gap}  {tens}")
    print(f"     {ones}{gap}  {ones}")
    for number, (a, b) in enumerate(zip(left, right), 1):
        print(f"{number:2d}   {a}{gap}  {b}")


def tiles_of(world: dict) -> dict[tuple[int, int], dict]:
    """The world's Tiles by 0-based (row, column), which is what a grid
    row and column index into."""
    return {(tile["row"] - 1, tile["column"] - 1): tile
            for tile in world["tiles"].values()}


def grid(world: dict, cell) -> list[str]:
    """One 30x18 letter grid. `cell(tile)` returns a character, or the
    empty string to leave the Tile as the sea's own dot."""
    by_rc = tiles_of(world)
    rows = []
    for r in range(ROWS):
        line = ""
        for c in range(COLUMNS):
            line += cell(by_rc[(r, c)]) or "."
        rows.append(line)
    return rows


def land_tiles(world: dict) -> list[dict]:
    return [world["tiles"][tid] for tid in world["tile_order"]
            if world["tiles"][tid]["biome"] != "sea"]


def economy_of(tile: dict) -> dict:
    """The Tile's derived numbers, recomputed from the words it stores --
    exactly as `places.goods_origins` and `roll_census` recompute them.
    They are worldgen intermediates and are deliberately never stored."""
    return places.tile_economy(tile["climate"], tile["terrain"],
                               tile["biome"] == "river",
                               tile["row"], tile["column"])


def letter_of(table: dict, word: str) -> str:
    """A climate or terrain WORD as the overlay letter that painted it."""
    for letter, value in table.items():
        if value == word:
            return letter
    raise KeyError(word)


def country_census(world: dict, label: str, of) -> None:
    total: Counter = Counter()
    by_country: dict[str, Counter] = {}
    for tile in land_tiles(world):
        value = of(tile)
        total[value] += 1
        by_country.setdefault(tile["country"], Counter())[value] += 1
    print(f"\n{label} ({sum(total.values())} land tiles)")
    for value, count in total.most_common():
        print(f"  {value:<20} {count:3d}")
    for country in places.COUNTRIES:
        counts = by_country.get(country, Counter())
        parts = ", ".join(f"{value}:{n}" for value, n in counts.most_common())
        print(f"  {country:<12} {parts}")


# --- climate (the default mode) -------------------------------------------- #

def render_climate(world: dict) -> None:
    base = grid(world, lambda t: places.BIOME_LETTERS[t["biome"]])
    climate = grid(world, lambda t: ("" if t["biome"] == "sea"
                                     else letter_of(CLIMATES, t["climate"])))
    render_side_by_side(base, climate, ("TERRAIN", "CLIMATE"))
    print("\nclimate letters: " + ", ".join(
        f"{letter} {word}" for letter, word in CLIMATES.items()))
    country_census(world, "CLIMATE CENSUS", lambda t: t["climate"])


# --- terrain and the land's character -------------------------------------- #

CHARACTER_GLYPHS = "M mountains, w marsh, F deep forest, f wooded, " \
                   "G farmland, P pasture, - waste"


def character_glyph(tile: dict) -> str:
    """One letter of land character for the eyeball map."""
    if tile["terrain"] == "mountains":
        return "M"
    if tile["terrain"] == "marsh":
        return "w"
    if tile["cover"] == "deep forest":
        return "F"
    if "farmland" in tile["tags"]:
        return "G"
    if "pasture" in tile["tags"]:
        return "P"
    if tile["cover"] == "wooded":
        return "f"
    return "-"


def render_terrain(world: dict) -> None:
    terrain = grid(world, lambda t: ("" if t["biome"] == "sea"
                                     else letter_of(TERRAINS, t["terrain"])))
    character = grid(world, lambda t: ("" if t["biome"] == "sea"
                                       else character_glyph(t)))
    render_side_by_side(terrain, character, ("TERRAIN", "CHARACTER"))
    print("\ncharacter: " + CHARACTER_GLYPHS)
    counts = Counter(tile["terrain"] for tile in land_tiles(world))
    land = sum(counts.values())
    print(f"\nTERRAIN CENSUS ({land} land tiles)")
    for word in ("plains", "hills", "marsh", "mountains"):
        print(f"  {word:<10} {counts[word]:3d}")
    open_land = land - counts["mountains"] - counts["marsh"]
    print(f"  hills are {100 * counts['hills'] / open_land:.0f}% of the "
          f"open (non-mountain, non-marsh) land")
    tags = Counter(tag for tile in land_tiles(world) for tag in tile["tags"]
                   if tag in ("forest", "farmland", "pasture")
                   or tag in places.CHARACTER_TAGS)
    print("\nDERIVED TAGS " + ", ".join(f"{tag}:{n}"
                                        for tag, n in tags.most_common()))
    covers = Counter(tile["cover"] for tile in land_tiles(world))
    print("COVER " + ", ".join(f"{word}:{n}"
                               for word, n in covers.most_common()))


def render_potential(world: dict) -> None:
    def tenths(key):
        return lambda t: ("" if t["biome"] == "sea"
                          else str(min(9, int(economy_of(t)[key] * 10))))
    render_side_by_side(grid(world, tenths("realized")),
                        grid(world, tenths("forest")),
                        ("REALIZED ARABLE (tenths)", "FOREST (tenths)"))
    values = [economy_of(tile)["realized"] for tile in land_tiles(world)]
    print(f"\nrealized arable: mean {sum(values) / len(values):.2f}, "
          f"max {max(values):.2f}; tiles at {places.FARMLAND_MIN:.2f}+: "
          f"{sum(1 for v in values if v >= places.FARMLAND_MIN)}")


# --- the last harvest ------------------------------------------------------ #

CAUSE_MARKS = {"drought": "D", "rains": "R", "frost": "F"}


def render_harvest(world: dict, seed: int) -> None:
    regions = world["harvest_regions"]
    print(f"LAST HARVEST, seed {seed}: " + "; ".join(
        f"{region['cause']} at "
        f"{places.tile_coordinate(*places.tile_row_column(region['center']))}"
        f" ({len(region['tiles'])} tiles)" for region in regions))
    causes = grid(world, lambda t: (
        "" if t["biome"] == "sea"
        else CAUSE_MARKS[t["harvest_cause"]] if t["harvest_cause"] else "-"))
    tens = grid(world, lambda t: ("" if t["biome"] == "sea"
                                  else str(min(9, t["harvest"] // 10))))
    render_side_by_side(causes, tens, ("CAUSE", "HARVEST (tens of %)"))
    start = world["party_tile"]
    print(f"\nthe campaign opens at {places.tile_label(world['tiles'][start])}"
          f"; nearest region center "
          f"{min(places.path_days(start, region['center']) for region in regions)}"
          f" days off")
    land = land_tiles(world)
    bad = [tile["harvest"] for tile in land
           if tile["harvest"] < places.HARVEST_PROBLEM]
    print(f"problem tiles: {len(bad)}/{len(land)} "
          f"= {100 * len(bad) / len(land):.0f}% of the land, "
          f"mean severity {sum(bad) / len(bad):.0f}%")
    words = Counter(places.harvest_word(tile["harvest"]) for tile in land)
    print("SPOKEN WORDS " + ", ".join(
        f"{word}:{words.get(word, 0)}" for _floor, word
        in places.HARVEST_WORDS))


# --- the census ------------------------------------------------------------ #

BAND_MARKS = {"wilderness": "-", "thin": "t", "low": "l", "mid": "m",
              "high": "h", "dense": "D"}
CHIEF_MARKS = {"metropolis": "M", "city": "C", "town": "T",
               "village": "v", "hamlet": "h"}
TIER_PEOPLE = {             # fiction anchors for the eyeball totals only --
    "hamlet": 60, "village": 300, "town": 3000,     # the game stores tier
    "city": 25000, "metropolis": 150000,            # WORDS, never heads
}


def tiers_of(world: dict, tile: dict) -> list[str]:
    return [world["settlement_slots"][sid]["tier"]
            for sid in tile["settlement_slots"]]


def render_population(world: dict, seed: int) -> None:
    bands = grid(world, lambda t: ("" if t["biome"] == "sea" else
                                   BAND_MARKS[places.population_band(world, t)]))
    chiefs = grid(world, lambda t: (
        "" if t["biome"] == "sea"
        else CHIEF_MARKS[tiers_of(world, t)[0]] if t["settlement_slots"]
        else "0"))
    render_side_by_side(bands, chiefs, ("BAND", "CHIEF SETTLEMENT"))
    print("\nband: - wilderness, t thin, l low, m mid, h high, D dense;"
          "\nchief: M metropolis, C city, T town, v village, h hamlet, "
          "0 empty")
    land = land_tiles(world)
    band_census = Counter(places.population_band(world, tile)
                          for tile in land)
    print(f"\nBAND CENSUS, seed {seed} " + ", ".join(
        f"{band}:{band_census.get(band, 0)}"
        for _ceiling, band in places.BANDS))
    tiers = Counter(slot["tier"] for slot in world["settlement_slots"].values())
    print("SETTLEMENTS " + ", ".join(f"{tier}:{tiers.get(tier, 0)}"
                                     for tier in places.TIERS)
          + f"  (total {sum(tiers.values())})")
    filled = Counter(len(tile["settlement_slots"]) for tile in land)
    print("SLOTS FILLED " + ", ".join(f"{n}:{filled.get(n, 0)}"
                                      for n in range(places.SLOT_CAP + 1)))
    souls: Counter = Counter()
    for tile in land:
        souls[tile["country"]] += sum(TIER_PEOPLE[tier]
                                      for tier in tiers_of(world, tile))
    print("SOULS " + ", ".join(f"{country}: {souls[country]:,}"
                               for country in places.COUNTRIES)
          + f"  (world {sum(souls.values()):,})")
    rich = [tile for tile in land
            if places.population_band(world, tile) in ("high", "dense")
            and (tile["row"], tile["column"]) not in places.HISTORICAL_BY_TILE]
    quiet = sum(1 for tile in rich
                if not set(tiers_of(world, tile)) & {"town", *places.CITY_GRADE})
    print(f"QUIET RICH COUNTRY {quiet}/{len(rich)} high+dense tiles "
          f"rolled no town at all")
    slots = world["settlement_slots"].values()
    print(f"CHARTERS {sum(1 for s in slots if s['charter'])} free "
          f"settlements; MANORS {sum(1 for s in slots if s['manor'])} "
          f"village tiles with a resident lord")
    print("\nRETRODICTION (authored tile: its band by law)")
    for (row, column), (name, *_rest) in sorted(
            places.HISTORICAL_BY_TILE.items(), key=lambda kv: kv[1][0]):
        tile = world["tiles"][places.tile_id(row, column)]
        print(f"  {name:<15} {places.HISTORICAL_TIERS[name]:<11} at "
              f"R{row:02d}C{column:02d}: "
              f"{places.population_band(world, tile):<10} rolled "
              f"{''.join(places.TIER_LETTERS_BY_TIER[t] for t in tiers_of(world, tile))}")
    print("\nMINE TOWNS (authored town in slot 1)")
    for (row, column), (name, goods) in sorted(places.MINES.items(),
                                               key=lambda kv: kv[1][0]):
        tile = world["tiles"][places.tile_id(row, column)]
        print(f"  {name:<17} at R{row:02d}C{column:02d}: "
              f"{places.population_band(world, tile):<10} rolled "
              f"{''.join(places.TIER_LETTERS_BY_TIER[t] for t in tiers_of(world, tile))}"
              f"  ({', '.join(goods)})")


# --- the trade network ----------------------------------------------------- #

GOOD_PRIORITY = ("grain", "wine", "wool", "horses", "furs", "timber",
                 "salt", "herring", "amber", "cloth", "arms")
GOOD_MARKS = {"grain": "g", "wine": "v", "wool": "w", "horses": "h",
              "furs": "f", "timber": "t", "salt": "s", "herring": "r",
              "amber": "b", "cloth": "c", "arms": "a"}
EXOTIC_DOORS = frozenset(places.ENDPOINT_NAMES) & frozenset(
    rc for rc, goods in places.GOODS_AUTHORED.items()
    if set(goods) & {"silk", "spice", "sugar"})


def render_routes(world: dict, seed: int) -> None:
    traffic = Counter(tid for route in world["routes"]
                      for tid in route["path"])

    def goods_cell(tile: dict) -> str:
        if tile["biome"] == "sea":
            return ""
        if tile["mine"]:
            return "M"
        if (tile["row"], tile["column"]) in EXOTIC_DOORS:
            return "x"
        return next((GOOD_MARKS[good] for good in GOOD_PRIORITY
                     if good in tile["goods"]), "-")

    def traffic_cell(tile: dict) -> str:
        crossings = traffic.get(tile["id"], 0)
        if tile["biome"] == "sea":
            return str(min(9, crossings)) if crossings else ""
        return str(min(9, crossings)) if crossings else "-"

    render_side_by_side(grid(world, goods_cell), grid(world, traffic_cell),
                        ("GOODS & MINES", "TRAFFIC (routes crossing)"))
    print("\ngoods: M mine, x exotic door, g grain, v wine, w wool, "
          "h horses,\n  f furs+wax, t timber, s salt, r herring, b amber, "
          "c cloth, a arms")
    routes = world["routes"]
    print(f"\nROUTES, seed {seed} ({len(routes)} after merging; "
          f"{len(places.LEGENDARY)} legendary)")
    named = [route for route in routes if route["name"]]
    plain = sorted((route for route in routes if not route["name"]),
                   key=lambda route: tuple(route["goods"]))
    for route in named + plain:
        label = (f"{places.endpoint_name(world, route['path'][0])} -> "
                 f"{places.endpoint_name(world, route['path'][-1])}")
        print(f"  {route['name'] or '':<15} {label:<28} "
              f"{', '.join(route['goods'])} ({route['days']}d)")
    tiles = world["tiles"]
    on_land = sum(1 for tid in traffic if tiles[tid]["biome"] != "sea")
    sea_lane = sum(1 for tid in traffic if tiles[tid]["biome"] == "sea")
    ports = sum(1 for tile in land_tiles(world) if "port" in tile["tags"])
    crossroads = sum(1 for tid, n in traffic.items()
                     if n >= 3 and tiles[tid]["biome"] != "sea")
    print(f"\nTRAFFIC {on_land} land tiles on a route, {sea_lane} sea-lane "
          f"tiles, {ports} ports; crossroads (3+): {crossroads}")
    census: Counter = Counter()
    for tile in land_tiles(world):
        census.update(tile["goods"])
    print("GOODS CENSUS (origin tiles) " + ", ".join(
        f"{good}:{n}" for good, n in census.most_common()))
    fed = {route["path"][-1] for route in routes if "grain" in route["goods"]}
    unfed = [name for (row, column), (name, _goods) in places.MINES.items()
             if places.tile_id(row, column) not in fed
             and economy_of(world["tiles"][places.tile_id(row, column)])
             ["realized"] < places.FARMLAND_MIN]
    if unfed:
        print(f"UNFED MINES (no grain within {places.MINE_FOOD_DAYS} days): "
              + ", ".join(sorted(unfed)))


# --- the character line (session 4's read surface) ------------------------- #

def render_character(world: dict, seed: int) -> None:
    """What each Tile is CALLED -- the phrase the DM speaks. The map is a
    legend index rather than a glyph key, because the vocabulary is bigger
    than the alphabet is comfortable with."""
    phrases = sorted({places.tile_character(world, tile)
                      for tile in land_tiles(world)})
    index = {phrase: "0123456789abcdefghijklmnopqrstuvwxyz"[n]
             for n, phrase in enumerate(phrases)}
    chief = grid(world, lambda t: (
        "" if t["biome"] == "sea"
        else CHIEF_MARKS[tiers_of(world, t)[0]] if t["settlement_slots"]
        else "0"))
    render_side_by_side(grid(world, lambda t: (
        "" if t["biome"] == "sea" else index[places.tile_character(world, t)])),
        chief, ("TILE CHARACTER", "CHIEF SETTLEMENT"))
    counts = Counter(places.tile_character(world, tile)
                     for tile in land_tiles(world))
    print(f"\nTILE CHARACTER, seed {seed} ({len(phrases)} phrases)")
    for phrase in phrases:
        print(f"  {index[phrase]}  {phrase:<20} {counts[phrase]:3d}")
    unused = [phrase for _f, _v, phrase in places.LAND_CHARACTER
              if phrase not in counts]
    if unused:
        print("  (land rows the goods layer always outranks on this map: "
              + ", ".join(unused) + ")")


# --------------------------------------------------------------------------- #

MODES = {"terrain": render_terrain, "potential": render_potential,
         "harvest": render_harvest, "population": render_population,
         "routes": render_routes, "character": render_character}


def main() -> None:
    run_lint()
    argv = sys.argv[1:]
    mode = argv[0] if argv and not argv[0].isdigit() else ""
    if "--sweep" in argv:
        sys.exit("`--sweep` retired 2026-08-21 -- the layers are measured "
                 "over many worlds by `python bench_worldgen.py`.")
    if mode and mode not in MODES:
        sys.exit(f"no such mode: {mode!r} -- "
                 f"{', '.join(sorted(MODES))}, or none for the climate map")
    rest = argv[1:] if mode else argv
    if rest and not rest[0].isdigit():
        sys.exit(f"not a seed: {rest[0]!r}")
    seed = int(rest[0]) if rest else 1
    world = places.create_geography(seed)
    if not mode:
        render_climate(world)
        return
    render = MODES[mode]
    if render in (render_terrain, render_potential):
        render(world)               # the deterministic layers: no seed to
    else:                           # name, because every world has them
        render(world, seed)


if __name__ == "__main__":
    main()
