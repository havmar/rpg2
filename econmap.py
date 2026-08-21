"""The tile economy arc's eyeball tool (2026-08-21, plan.md Part 1).

Standalone and stdlib-only, in the archive/worldmap.py manner: it reads the
authored resources directly and imports nothing from the game, so it can be
run against a half-drawn overlay while the rules it will obey are still
being designed.  It validates each authored overlay against the base map
and renders them side by side as 30x18 ASCII, with censuses underneath.
Climate is the first layer; fertility, population and routes join it as
their rounds land.

    python econmap.py                  # the climate overlay + lint
    python econmap.py terrain          # the terrain overlay + land character
    python econmap.py potential        # the derived numbers (round 3's input)
    python econmap.py harvest [SEED]   # one rolled last-harvest layer
    python econmap.py harvest --sweep  # the distribution over 500 seeds
    python econmap.py population [SEED]   # one rolled settlement census
    python econmap.py population --sweep  # the census over 500 seeds

Validation (the law demoted to a lint -- the map is authored, the rules
only check it): every land tile carries exactly one climate letter, sea
carries none, and `a` (alpine) sits exactly on the `^` tiles.  The terrain
overlay lints the same way: every land tile painted, sea unpainted, and
`m` (mountains) exactly on the `^` tiles.

The TERRAIN mode is round 2's layer.  The authored half is relief and
drainage only -- plains, hills, marsh, with mountains fixed by the base
map; FOREST IS NOT AUTHORED (2026-08-21, round 2's reversal of its own
plan wording): the wildwood cap comes from climate and the deforestation
law decides what survives, so deep forest appears exactly where people
are few.  The derived half is the two-pass deforestation proposal made
law: arable potential from climate x terrain (+ the alluvial bonus),
clearance a saturating function of potential wheat, realized arable and
surviving forest falling out of it, and the pastoral index as the
complement -- what habitable ground does where the plow does poorly.
Everything here is DETERMINISTIC: authored overlays plus laws, no rng,
identical in every campaign like the map itself.

The POPULATION mode is round 3's layer, in two halves.  The SCORE is
deterministic law over rounds 1-2's outputs: food capacity (realized
arable + weighted pasture + coastal and river fishing), a transport
multiplier on rivers and coasts (a town exceeds its land's carrying
capacity only with transport), and the penalties -- marsh disease,
highland, the eastern frontier.  The CENSUS is a rolled arrangement per
tile, seeded per world: the score picks a BAND, the band picks from a
weighted table of settlement arrangements (hamlets, villages, towns,
cities, the authored metropolises) with deliberately high variance -- a
rich band can and does roll a village-only tile, which is what keeps the
grid from reading as a grid.  The absolute numbers of the real or the
downscaled world are ABANDONED BY DESIGN (2026-08-21, round 3): the tile
is the unit, the census IS the population, and the tier words carry the
scale (hamlet under a hundred souls, village hundreds, town thousands,
city tens of thousands, metropolis a hundred thousand and more).

The HARVEST mode is the round's rolled layer: last year's harvest as a
percentage per tile (100 = a full excellent harvest), generated as
contiguous problem REGIONS over the painted climates -- centers seeded
where the climate is failure-prone, each with a CAUSE (drought, the great
rains, frost), grown outward by contagion into the ground that cause can
hurt, severity deepest at the core.  One drought region is guaranteed in
every world: no year is a good year everywhere.  The tool rolls a plain
seeded rng; the shipped worldgen will use derived seeds per the arc's
standing rule.
"""

from __future__ import annotations

import random
import sys
from collections import Counter, deque
from pathlib import Path

RESOURCES = Path(__file__).with_name("resources")
BASE_PATH = RESOURCES / "europe_map.txt"
CLIMATE_PATH = RESOURCES / "europe_climate.txt"
TERRAIN_PATH = RESOURCES / "europe_terrain.txt"

ROWS, COLUMNS = 18, 30
BASE_GLYPHS = {".", "#", "^", "~"}

# The climate vocabulary (round 1, DRAFT until the round settles).
CLIMATES = {
    "u": "tundra",
    "t": "taiga",
    "c": "continental",
    "o": "oceanic",
    "m": "mediterranean",       # the medieval DRY one (its bad year is dry)
    "w": "wet mediterranean",   # the southern shore's Roman Warm regime
    "s": "steppe",
    "d": "desert",
    "n": "nile",                # river-fed floodplain granary
    "a": "alpine",              # exactly the mountain tiles
}


# The terrain vocabulary (round 2). Relief and drainage, nothing else:
# forest is derived below, farmland is population's footprint, and the
# quest tables' word for the high tiles is the plural -- `mountains` --
# which round 2's contract makes the one word everywhere outside the
# base-map glyph key (retiring the mountain/mountains near-miss).
TERRAINS = {
    "p": "plains",
    "h": "hills",
    "w": "marsh",       # authored by hand, few and famous
    "m": "mountains",   # exactly the ^ tiles
}


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


def country_at(row: int, column: int) -> str:
    # places.country_at, restated so the tool stays standalone. Nothing here
    # is pinned -- the census below is an eyeball, not a contract.
    if row >= 11:
        return "mortellaria"
    return "firascir" if column <= 21 else "tergal"


def validate_climate(base: list[str], climate: list[str]) -> list[str]:
    problems = []
    for r in range(ROWS):
        for c in range(COLUMNS):
            ground, label = base[r][c], climate[r][c]
            where = f"R{r + 1:02d}C{c + 1:02d}"
            if ground == "." and label != ".":
                problems.append(f"{where}: sea tile carries {label!r}")
            elif ground != "." and label == ".":
                problems.append(f"{where}: land tile ({ground}) unpainted")
            elif ground == "^" and label != "a":
                problems.append(f"{where}: mountain painted {label!r}, "
                                f"expected 'a'")
            elif ground != "^" and label == "a":
                problems.append(f"{where}: alpine off the mountain "
                                f"({ground!r})")
    return problems


def validate_terrain(base: list[str], terrain: list[str]) -> list[str]:
    problems = []
    for r in range(ROWS):
        for c in range(COLUMNS):
            ground, label = base[r][c], terrain[r][c]
            where = f"R{r + 1:02d}C{c + 1:02d}"
            if ground == "." and label != ".":
                problems.append(f"{where}: sea tile carries {label!r}")
            elif ground != "." and label == ".":
                problems.append(f"{where}: land tile ({ground}) unpainted")
            elif ground == "^" and label != "m":
                problems.append(f"{where}: mountain painted {label!r}, "
                                f"expected 'm'")
            elif ground != "^" and label == "m":
                problems.append(f"{where}: mountains off the mountain "
                                f"({ground!r})")
    return problems


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


def censuses(climate: list[str]) -> None:
    total = Counter()
    by_country: dict[str, Counter] = {}
    for r in range(ROWS):
        for c in range(COLUMNS):
            label = climate[r][c]
            if label == ".":
                continue
            total[label] += 1
            by_country.setdefault(country_at(r + 1, c + 1),
                                  Counter())[label] += 1
    print("\nCLIMATE CENSUS "
          f"({sum(total.values())} land tiles)")
    for letter in CLIMATES:
        print(f"  {letter} {CLIMATES[letter]:<18} {total.get(letter, 0):3d}")
    for country in ("firascir", "mortellaria", "tergal"):
        counts = by_country.get(country, Counter())
        parts = ", ".join(f"{letter}:{counts[letter]}"
                          for letter in CLIMATES if counts.get(letter))
        print(f"  {country:<12} {parts}")


# --------------------------------------------------------------------------- #
# The land's potential (derived, deterministic -- round 2's laws)
# --------------------------------------------------------------------------- #
# Author the physical, derive the human.  The numbers below are round 3's
# inputs (population reads realized arable, pastoral and fishing); what the
# game itself stores and speaks are the words at the bottom -- the cover
# word and the derived tags.

CLIMATE_ARABLE = {          # fraction of this climate's ground a plow can
    "u": 0.00, "t": 0.10,   # ever touch, before relief says its word
    "c": 0.65, "o": 0.60,
    "m": 0.50, "w": 0.60,
    "s": 0.35, "d": 0.02,
    "n": 0.85, "a": 0.05,
}
TERRAIN_ARABLE = {          # what relief and drainage leave of that
    "plains": 1.00, "hills": 0.45, "mountains": 0.10, "marsh": 0.15,
}
ALLUVIAL_BONUS = 0.12       # a river tile's floodplain soils (marsh IS the
ARABLE_CAP = 0.90           # undrained floodplain, so it takes no bonus)
WHEAT_YIELD = {             # round 1's yield column, restated for the tool
    "u": 0.0, "t": 0.3, "a": 0.15, "c": 1.0, "o": 1.0,
    "m": 0.8, "w": 1.3, "s": 0.5, "d": 0.05, "n": 1.5,
}
FFD = {                     # round 1's frost-free days: (base, reference
    "u": (60, 2), "t": (100, 4), "a": (90, None), "c": (170, 8),
    "o": (220, 8), "m": (270, 13), "w": (300, 17), "s": (160, 10),
    "d": (330, 17), "n": (330, 18),
}                           # row); the gradient scales wheat by ffd/base
CLEARANCE_K = 0.20          # clearance = wheat / (wheat + K): how much of
                            # its potential a population bothers to realize
FOREST_CAP = {              # the wildwood: what nature forests, before man
    "u": 0.05, "t": 0.95, "c": 0.85, "o": 0.85, "m": 0.45,
    "w": 0.55, "s": 0.08, "d": 0.00, "n": 0.05, "a": 0.50,
}
MARSH_WOOD = 0.5            # carr and fen scrub, never the full wildwood
GRAZE_CLIMATE = {           # the pastoral index: herding by climate law,
    "u": 0.15, "t": 0.15,   # no hand-picking (the steppe reads pastoral
    "c": 0.35, "o": 0.45,   # everywhere; exceptions are HAND_MARKS)
    "m": 0.50, "w": 0.40,
    "s": 0.90, "d": 0.05,
    "n": 0.10, "a": 0.35,
}
GRAZE_TERRAIN = {
    "plains": 0.60, "hills": 0.90, "mountains": 0.60, "marsh": 0.30,
}
DEEP_FOREST_MIN = 0.55      # surviving forest >= this: deep forest, the
WOODED_MIN = 0.25           # wilderness; >= this: wooded (the forest tag)
FARMLAND_MIN = 0.30         # realized arable >= this: the farmland tag
PASTURE_MIN = 0.20          # pastoral >= this AND > realized arable
CHARACTER_TAGS = ("steppe", "desert", "tundra")   # climate words that ARE
                            # terrain character; the rest stay sky-only
HAND_MARKS = {              # authored character the law cannot see: extra
    (11, 19): ("pasture",), # tags per (row, column).  The one seeded mark
}                           # is the middle Danube's horse country.
HAND_ALLUVIAL = {           # floodplain soils with no drawn river: the Po
    (12, 12), (12, 13),     # plain (the 2026-08-21 redraw cut the lagoon
    (12, 14),               # river for looks; the water still exists)
}


def tile_economy(letter: str, terrain: str, river: bool, row: int,
                 column: int | None = None) -> dict:
    """One tile's derived numbers and words, by law.  1-based coordinates."""
    arable = CLIMATE_ARABLE[letter] * TERRAIN_ARABLE[terrain]
    alluvial = river or (column is not None
                         and (row, column) in HAND_ALLUVIAL)
    if alluvial and terrain != "marsh":
        arable += ALLUVIAL_BONUS
    arable = min(ARABLE_CAP, arable)
    base, reference = FFD[letter]
    if reference is None:
        ffd = base
    else:
        ffd = base + 8 * (row - reference)
        ffd = max(base - 40, min(base + 40, ffd))
    wheat = arable * WHEAT_YIELD[letter] * ffd / base
    clearance = wheat / (wheat + CLEARANCE_K)
    realized = arable * clearance
    wildwood = FOREST_CAP[letter] * (MARSH_WOOD if terrain == "marsh"
                                     else 1.0)
    forest = wildwood * (1 - clearance)
    pastoral = GRAZE_CLIMATE[letter] * GRAZE_TERRAIN[terrain]
    if forest >= DEEP_FOREST_MIN:
        cover = "deep forest"
    elif forest >= WOODED_MIN:
        cover = "wooded"
    else:
        cover = "open"
    return {"arable": arable, "wheat": wheat, "clearance": clearance,
            "realized": realized, "forest": forest, "pastoral": pastoral,
            "cover": cover}


CLIMATE_WORDS = {"u": "tundra", "t": "taiga", "s": "steppe", "d": "desert"}


def tile_tags(economy: dict, terrain: str, letter: str,
              row: int, column: int) -> list[str]:
    """The derived tag list round 2 reconciles the quest tables against."""
    tags = [terrain]
    if economy["cover"] != "open":
        tags.append("forest")
    if economy["realized"] >= FARMLAND_MIN:
        tags.append("farmland")
    if (economy["pastoral"] >= PASTURE_MIN
            and economy["pastoral"] > economy["realized"]):
        tags.append("pasture")
    word = CLIMATE_WORDS.get(letter)
    if word in CHARACTER_TAGS:
        tags.append(word)
    for mark in HAND_MARKS.get((row, column), ()):
        if mark not in tags:
            tags.append(mark)
    return tags


def character_glyph(economy: dict, terrain: str, tags: list[str]) -> str:
    """One letter of land character for the eyeball map."""
    if terrain == "mountains":
        return "M"
    if terrain == "marsh":
        return "w"
    if economy["cover"] == "deep forest":
        return "F"
    if "farmland" in tags:
        return "G"
    if "pasture" in tags:
        return "P"
    if economy["cover"] == "wooded":
        return "f"
    return "-"


def economy_grids(base: list[str], climate: list[str],
                  terrain: list[str]):
    """Per-tile economy dicts, tags and character glyphs for the whole map."""
    economies, tags, character = {}, {}, []
    for r in range(ROWS):
        line = ""
        for c in range(COLUMNS):
            if climate[r][c] == ".":
                line += "."
                continue
            word = TERRAINS[terrain[r][c]]
            economy = tile_economy(climate[r][c], word,
                                   base[r][c] == "~", r + 1, c + 1)
            economies[(r, c)] = economy
            tags[(r, c)] = tile_tags(economy, word, climate[r][c],
                                     r + 1, c + 1)
            line += character_glyph(economy, word, tags[(r, c)])
        character.append(line)
    return economies, tags, character


def render_terrain(base: list[str], climate: list[str],
                   terrain: list[str]) -> None:
    economies, tags, character = economy_grids(base, climate, terrain)
    render_side_by_side(terrain, character, ("TERRAIN", "CHARACTER"))
    print("\ncharacter: M mountains, w marsh, F deep forest, f wooded, "
          "G grain country, P pasture, - waste")
    total = Counter()
    for r in range(ROWS):
        for c in range(COLUMNS):
            if terrain[r][c] != ".":
                total[TERRAINS[terrain[r][c]]] += 1
    land = sum(total.values())
    print(f"\nTERRAIN CENSUS ({land} land tiles)")
    for word in ("plains", "hills", "marsh", "mountains"):
        print(f"  {word:<10} {total[word]:3d}")
    open_land = land - total["mountains"] - total["marsh"]
    print(f"  hills are {100 * total['hills'] / open_land:.0f}% of the "
          f"open (non-mountain, non-marsh) land")
    tag_census = Counter(tag for value in tags.values() for tag in value)
    print("\nDERIVED TAGS " + ", ".join(
        f"{tag}:{n}" for tag, n in tag_census.most_common()))
    covers = Counter(economy["cover"] for economy in economies.values())
    print("COVER " + ", ".join(f"{word}:{n}"
                               for word, n in covers.most_common()))


def render_potential(base: list[str], climate: list[str],
                     terrain: list[str]) -> None:
    economies, _tags, _character = economy_grids(base, climate, terrain)
    wheat, forest = [], []
    for r in range(ROWS):
        wheat_line, forest_line = "", ""
        for c in range(COLUMNS):
            if (r, c) not in economies:
                wheat_line += "."
                forest_line += "."
            else:
                economy = economies[(r, c)]
                wheat_line += str(min(9, int(economy["realized"] * 10)))
                forest_line += str(min(9, int(economy["forest"] * 10)))
        wheat.append(wheat_line)
        forest.append(forest_line)
    render_side_by_side(wheat, forest,
                        ("REALIZED ARABLE (tenths)", "FOREST (tenths)"))
    values = [economy["realized"] for economy in economies.values()]
    print(f"\nrealized arable: mean {sum(values) / len(values):.2f}, "
          f"max {max(values):.2f}; "
          f"tiles at 0.30+: {sum(1 for v in values if v >= 0.30)}")


# --------------------------------------------------------------------------- #
# The last-harvest layer (rolled, not authored)
# --------------------------------------------------------------------------- #
# The scale: 100 = a full excellent harvest. 110-120 legendary, 95-109
# excellent, 75-94 ordinary, 55-74 poor, 35-54 failed, below 35 apocalyptic.
# A tile is a PROBLEM tile below 75.

REGION_COUNT = (4, 6)               # rolled uniformly, inclusive
CENTER_SEPARATION = 4               # min manhattan distance between centers
CENTER_WEIGHT = {                   # who hosts trouble (the variance column's
    "m": 1.0, "s": 1.0, "c": 0.7,   # first half): rich reliable cores rarely,
    "t": 0.5, "w": 0.4, "o": 0.3,   # the dry and open margins often, the
    "a": 0.3, "n": 0.2,             # tundra and open desert never -- nothing
    "u": 0.0, "d": 0.0,             # grows there to lose
}
CAUSES = {                          # what a center's climate can suffer
    "m": (("drought", 0.8), ("rains", 0.2)),
    "s": (("drought", 0.6), ("frost", 0.3), ("rains", 0.1)),
    "w": (("drought", 0.7), ("rains", 0.3)),
    "c": (("rains", 0.45), ("drought", 0.35), ("frost", 0.2)),
    "o": (("rains", 0.8), ("drought", 0.2)),
    "t": (("frost", 0.6), ("rains", 0.4)),
    "a": (("frost", 0.7), ("rains", 0.3)),
    "n": (("rains", 1.0),),         # the Nile's failure is the bad flood
    "u": (("frost", 1.0),),
}
SUSCEPTIBILITY = {                  # how far a cause spreads into a climate
    "drought": {"m": 1.0, "s": 1.0, "d": 1.0, "w": 0.7, "c": 0.5, "a": 0.3,
                "o": 0.2, "n": 0.15, "t": 0.1, "u": 0.1},
    "rains":   {"o": 1.0, "c": 0.8, "t": 0.7, "a": 0.6, "n": 0.5, "u": 0.4,
                "m": 0.3, "w": 0.3, "s": 0.2, "d": 0.0},
    "frost":   {"t": 1.0, "u": 1.0, "a": 1.0, "c": 0.7, "s": 0.7, "o": 0.4,
                "m": 0.1, "w": 0.0, "n": 0.0, "d": 0.0},
}
SPREAD = {1: 1.0, 2: 0.95, 3: 0.70, 4: 0.40, 5: 0.18}   # join chance by ring
SEVERITY_CENTER = (30, 65)          # the core's harvest percent
SEVERITY_RING = 6                   # it softens this much per ring outward
SEVERITY_JITTER = 8                 # plus this much noise either way
SEVERITY_CLAMP = (25, 74)           # a problem tile stays a problem tile
GOOD_MEAN, GOOD_SIGMA = 90, 9       # the fine-year distribution elsewhere
GOOD_CLAMP = (75, 120)
LEGENDARY_CHANCE = 0.03             # ...with a rare 110-120 tail
CAUSE_MARKS = {"drought": "D", "rains": "R", "frost": "F"}


def land_tiles(climate: list[str]) -> list[tuple[int, int]]:
    return [(r, c) for r in range(ROWS) for c in range(COLUMNS)
            if climate[r][c] != "."]


def _neighbors(climate: list[str], r: int, c: int):
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < ROWS and 0 <= cc < COLUMNS and climate[rr][cc] != ".":
            yield rr, cc


def roll_harvest(climate: list[str], seed: int):
    """One world's last harvest: {tile: percent}, {tile: cause}, regions."""
    rng = random.Random(seed)
    land = land_tiles(climate)
    n_regions = rng.randint(*REGION_COUNT)
    weights = [CENTER_WEIGHT[climate[r][c]] for r, c in land]
    centers: list[tuple[int, int]] = []
    while len(centers) < n_regions:
        pick = rng.choices(land, weights=weights)[0]
        if all(abs(pick[0] - r) + abs(pick[1] - c) > CENTER_SEPARATION
               for r, c in centers):
            centers.append(pick)
    regions = []
    for r, c in centers:
        pool = CAUSES[climate[r][c]]
        cause = rng.choices([p[0] for p in pool], [p[1] for p in pool])[0]
        regions.append({"center": (r, c), "cause": cause})
    if not any(g["cause"] == "drought" for g in regions):
        # No year is a good year everywhere: the most drought-apt center
        # re-causes, so every world has its year of dust somewhere.
        best = max(regions, key=lambda g: SUSCEPTIBILITY["drought"][
            climate[g["center"][0]][g["center"][1]]])
        best["cause"] = "drought"
    harvest: dict[tuple[int, int], int] = {}
    cause_at: dict[tuple[int, int], str] = {}
    for region in regions:
        members = {region["center"]: 0}
        frontier = deque([(region["center"], 0)])
        while frontier:
            (r, c), ring = frontier.popleft()
            if ring >= max(SPREAD):
                continue
            for rr, cc in _neighbors(climate, r, c):
                if (rr, cc) in members:
                    continue
                chance = (SPREAD[ring + 1]
                          * SUSCEPTIBILITY[region["cause"]][climate[rr][cc]])
                if rng.random() < chance:
                    members[(rr, cc)] = ring + 1
                    frontier.append(((rr, cc), ring + 1))
        region["members"] = members
        core = rng.randint(*SEVERITY_CENTER)
        for (r, c), ring in members.items():
            sev = core + SEVERITY_RING * ring + rng.randint(
                -SEVERITY_JITTER, SEVERITY_JITTER)
            sev = min(SEVERITY_CLAMP[1], max(SEVERITY_CLAMP[0], sev))
            if (r, c) not in harvest or sev < harvest[(r, c)]:
                harvest[(r, c)] = sev
                cause_at[(r, c)] = region["cause"]
    for r, c in land:
        if (r, c) not in harvest:
            draw = rng.gauss(GOOD_MEAN, GOOD_SIGMA)
            if rng.random() < LEGENDARY_CHANCE:
                draw = rng.uniform(110, 120)
            harvest[(r, c)] = int(min(GOOD_CLAMP[1],
                                      max(GOOD_CLAMP[0], draw)))
    return harvest, cause_at, regions


def render_harvest(climate: list[str], seed: int) -> None:
    harvest, cause_at, regions = roll_harvest(climate, seed)
    print(f"LAST HARVEST, seed {seed}: " + "; ".join(
        f"{g['cause']} at R{g['center'][0] + 1:02d}"
        f"C{g['center'][1] + 1:02d} ({len(g['members'])} tiles)"
        for g in regions))
    causes, tens = [], []
    for r in range(ROWS):
        cause_line, tens_line = "", ""
        for c in range(COLUMNS):
            if climate[r][c] == ".":
                cause_line += "."
                tens_line += "."
            elif (r, c) in cause_at:
                cause_line += CAUSE_MARKS[cause_at[(r, c)]]
                tens_line += str(min(9, harvest[(r, c)] // 10))
            else:
                cause_line += "-"
                tens_line += str(min(9, harvest[(r, c)] // 10))
        causes.append(cause_line)
        tens.append(tens_line)
    render_side_by_side(causes, tens, ("CAUSE", "HARVEST (tens of %)"))
    bad = [v for v in harvest.values() if v < 75]
    print(f"\nproblem tiles: {len(bad)}/{len(harvest)} "
          f"= {100 * len(bad) / len(harvest):.0f}% of the land, "
          f"mean severity {sum(bad) / len(bad):.0f}%")


def sweep_harvest(climate: list[str], seeds: int = 500) -> None:
    coverage, sizes, causes = [], [], Counter()
    for seed in range(seeds):
        harvest, cause_at, regions = roll_harvest(climate, seed)
        coverage.append(len(cause_at) / len(harvest))
        sizes += [len(g["members"]) for g in regions]
        causes.update(g["cause"] for g in regions)
    print(f"{seeds} seeds: problem coverage mean "
          f"{100 * sum(coverage) / len(coverage):.1f}% "
          f"(min {100 * min(coverage):.0f}%, max {100 * max(coverage):.0f}%)")
    print(f"region size mean {sum(sizes) / len(sizes):.1f} tiles "
          f"(max {max(sizes)}); causes: "
          + ", ".join(f"{c}: {n}" for c, n in causes.most_common()))


# --------------------------------------------------------------------------- #
# The population layer (round 3: a deterministic score, a rolled census)
# --------------------------------------------------------------------------- #
# THE SCALE DOCTRINE (2026-08-21, round 3 -- the designer will ask):
#   - A tile is SPOKEN OF as 30 km east-west by 60 km north-south (one
#     travel day east-west, two north-south; 1800 km2).
#   - The drawn map corresponds to real Europe at roughly 160 km per
#     column and 220 km per row (about 35,000 km2 per tile): the height
#     is 1.4x the width, NOT the 2x the travel costs suggest.  The map is
#     a deliberately squashed Europe; north-south travel is priced by the
#     fictional 60 km, not the real 220.
#   - By AREA the game world is therefore about 20x smaller than the real
#     one (5.3x east-west, 3.7x north-south linear).
#   - Consequence: real, historical or downscaled densities are NEVER an
#     input.  The tile is the unit; the census below IS the population.
#   - Slots: at most 4 per tile, thought of as a 2x2 lattice -- 15 km
#     apart east-west, 30 km north-south (twice as dense horizontally,
#     mirroring the travel anisotropy).  A settlement every 15-30 km is
#     the medieval market-day spacing; that is why four is the cap.

PASTORAL_PEOPLE = 0.35      # herds feed fewer than fields per unit of index
FISH_COAST = 0.08           # the shore feeds people the plow never counted
FISH_RIVER = 0.05           # so does the river, half as well
TRANSPORT_FACTOR = 1.15     # grain moves by water: a river or coast tile
                            # can feed a settlement its own fields cannot
MARSH_MALUS = 0.60          # the fen fever
HIGHLAND_MALUS = 0.60       # the high ground holds fewer, past low arable
EAST_MALUS_START = 22       # the raiding frontier: columns past this lose
EAST_MALUS_STEP = 0.04      # this much per column...
EAST_MALUS_FLOOR = 0.65     # ...down to this floor
EAST_MALUS_LAST_ROW = 13    # the frontier is the STEPPE's reach: the
                            # southern sea-lane stripe (rows 14-18, the
                            # Nile granary included) is not raider country
HAND_DENSE = {              # score the law cannot see, authored:
    (8, 11),                # - the Low Countries delta reads as fen by
                            #   law, but its people drained it -- the
                            #   polders ARE the land
    (12, 13), (12, 14),     # - the Lombardy-Veneto city belt: the redraw
                            #   cut the lagoon river for looks, and no law
                            #   sees the city culture of the Italian north
}
BANDS = (                   # score -> band; the census table's key
    (0.05, "wilderness"), (0.15, "thin"), (0.30, "low"),
    (0.50, "mid"), (0.82, "high"), (9.99, "dense"),
)
BAND_MARKS = {"wilderness": "-", "thin": "t", "low": "l", "mid": "m",
              "high": "h", "dense": "D"}

# The census: arrangement strings over the tier letters -- H hamlet,
# V village, T town, C city, M metropolis -- weighted per band.  The
# variance is IN the tables: every settled band keeps a village-only
# (or emptier) roll, so France still hides quiet country, and only the
# dense band ever rolls a generated city.  At most 4 letters anywhere.
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
# An authored historical settlement fills slot 1; its companions come from
# ITS OWN BAND's table, truncated to the three remaining slots -- so Paris
# gathers towns and villages (city-with-towns, the realistic pattern) while
# Stockholm and Moscow stand nearly alone in thin country, frontier
# metropolis style.
HISTORICAL_TIERS = {        # the authored answer key, NOT downscaled: the
    "Paris": "M", "Venice": "M", "Constantinople": "M",   # metropolises
    "London": "C", "Amsterdam": "C", "Prague": "C", "Moscow": "C",
    "Kyiv": "C", "Lisbon": "C", "Rome": "C", "Carthage": "C",
    "Dublin": "T", "Stockholm": "T", "Warsaw": "T", "Madrid": "T",
    "Athens": "T",
}
HISTORICAL_TILES = {        # (row, column) -> name; restates places.py's
    (5, 2): "Dublin", (6, 5): "London", (8, 11): "Amsterdam",
    (9, 10): "Paris", (9, 18): "Prague", (3, 23): "Stockholm",
    (7, 28): "Moscow", (8, 22): "Warsaw", (10, 27): "Kyiv",
    (13, 3): "Lisbon", (13, 7): "Madrid", (12, 14): "Venice",
    (14, 14): "Rome", (14, 19): "Athens", (14, 27): "Constantinople",
    (17, 12): "Carthage",
}                           # list so the tool stays standalone
TIER_PEOPLE = {             # fiction anchors for the eyeball totals only --
    "H": 60, "V": 300,      # the game stores tier WORDS, never heads
    "T": 3000, "C": 25000, "M": 150000,
}
TIER_ORDER = "MCTVH"        # chief settlement first: slot 1 leads the tile
CHARTER_CHANCE = 1 / 3      # a generated town holds a charter this often;
                            # cities and metropolises always do
MANOR_CHANCE = 0.5          # a village-led tile of 2+ settlements seats a
                            # resident lord this often (else the lord is
                            # absent and the tile answers to a distant seat)


def _is_coast(base: list[str], r: int, c: int) -> bool:
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < ROWS and 0 <= cc < COLUMNS and base[rr][cc] == ".":
            return True
    return False


def tile_score(economy: dict, letter: str, terrain_word: str,
               coast: bool, river: bool, row: int, column: int) -> float:
    """The deterministic population score, by law.  1-based coordinates."""
    food = economy["realized"] + PASTORAL_PEOPLE * economy["pastoral"]
    if coast:
        food += FISH_COAST
    elif river:
        food += FISH_RIVER
    score = food
    if coast or river:
        score *= TRANSPORT_FACTOR
    if terrain_word == "marsh":
        score *= MARSH_MALUS
    elif terrain_word == "mountains":
        score *= HIGHLAND_MALUS
    if row <= EAST_MALUS_LAST_ROW:
        east = 1.0 - EAST_MALUS_STEP * max(0, column - EAST_MALUS_START)
        score *= max(EAST_MALUS_FLOOR, east)
    return score


def score_band(score: float, row: int, column: int) -> str:
    if (row, column) in HAND_DENSE:
        return "dense"
    for ceiling, band in BANDS:
        if score < ceiling:
            return band
    return "dense"


def _draw(rng: random.Random, table) -> str:
    return rng.choices([row[0] for row in table],
                       [row[1] for row in table])[0]


def roll_census(base: list[str], climate: list[str], terrain: list[str],
                seed: int):
    """One world's settlement census: {tile: {band, tiers, flags}}."""
    rng = random.Random(seed)
    economies, _tags, _character = economy_grids(base, climate, terrain)
    census = {}
    for r in range(ROWS):
        for c in range(COLUMNS):
            if (r, c) not in economies:
                continue
            letter = climate[r][c]
            word = TERRAINS[terrain[r][c]]
            river = base[r][c] == "~" or letter == "n"
            coast = _is_coast(base, r, c)
            score = tile_score(economies[(r, c)], letter, word, coast,
                               river, r + 1, c + 1)
            band = score_band(score, r + 1, c + 1)
            name = HISTORICAL_TILES.get((r + 1, c + 1))
            if name:
                tiers = (HISTORICAL_TIERS[name]
                         + _draw(rng, ARRANGEMENTS[band])[:3])
            else:
                tiers = _draw(rng, ARRANGEMENTS[band])
            tiers = "".join(sorted(tiers, key=TIER_ORDER.index))
            free = []
            for tier in tiers:
                if tier in "MC":
                    free.append(True)
                elif tier == "T":
                    free.append(rng.random() < CHARTER_CHANCE)
                else:
                    free.append(False)
            if name:                    # the famous names hold their own
                free[0] = True          # charters, always
            manor = (len(tiers) >= 2 and tiers[0] == "V"
                     and rng.random() < MANOR_CHANCE)
            census[(r, c)] = {"band": band, "score": score,
                              "tiers": tiers, "free": free, "manor": manor,
                              "historical": name}
    return census


def render_population(base: list[str], climate: list[str],
                      terrain: list[str], seed: int) -> None:
    census = roll_census(base, climate, terrain, seed)
    bands, chiefs = [], []
    for r in range(ROWS):
        band_line, chief_line = "", ""
        for c in range(COLUMNS):
            if (r, c) not in census:
                band_line += "."
                chief_line += "."
            else:
                tile = census[(r, c)]
                band_line += BAND_MARKS[tile["band"]]
                if not tile["tiers"]:
                    chief_line += "0"
                else:
                    chief = tile["tiers"][0]
                    chief_line += {"H": "h", "V": "v", "T": "T",
                                   "C": "C", "M": "M"}[chief]
        bands.append(band_line)
        chiefs.append(chief_line)
    render_side_by_side(bands, chiefs, ("BAND", "CHIEF SETTLEMENT"))
    print("\nband: - wilderness, t thin, l low, m mid, h high, D dense;"
          "\nchief: M metropolis, C city, T town, v village, h hamlet, "
          "0 empty")
    band_census = Counter(tile["band"] for tile in census.values())
    print("\nBAND CENSUS " + ", ".join(
        f"{band}:{band_census.get(band, 0)}"
        for _ceiling, band in BANDS))
    tier_census = Counter(tier for tile in census.values()
                          for tier in tile["tiers"])
    slots = Counter(len(tile["tiers"]) for tile in census.values())
    print("SETTLEMENTS " + ", ".join(
        f"{tier}:{tier_census.get(tier, 0)}" for tier in TIER_ORDER)
        + f"  (total {sum(tier_census.values())})")
    print("SLOTS FILLED " + ", ".join(
        f"{n}:{slots.get(n, 0)}" for n in range(5)))
    by_country = Counter()
    for (r, c), tile in census.items():
        by_country[country_at(r + 1, c + 1)] += sum(
            TIER_PEOPLE[tier] for tier in tile["tiers"])
    print("SOULS " + ", ".join(
        f"{country}: {by_country[country]:,}"
        for country in ("firascir", "mortellaria", "tergal"))
        + f"  (world {sum(by_country.values()):,})")
    high = [tile for tile in census.values()
            if tile["band"] in ("high", "dense") and not tile["historical"]]
    quiet = sum(1 for tile in high if "T" not in tile["tiers"]
                and "C" not in tile["tiers"])
    print(f"QUIET RICH COUNTRY {quiet}/{len(high)} high+dense tiles "
          f"rolled no town at all")
    frees = sum(1 for tile in census.values() for flag in tile["free"]
                if flag)
    manors = sum(1 for tile in census.values() if tile["manor"])
    print(f"CHARTERS {frees} free settlements; MANORS {manors} "
          f"village tiles with a resident lord")
    print("\nRETRODICTION (authored tile: its band by law)")
    for (row, column), name in sorted(HISTORICAL_TILES.items(),
                                      key=lambda kv: kv[1]):
        tile = census[(row - 1, column - 1)]
        print(f"  {name:<15} {HISTORICAL_TIERS[name]} at "
              f"R{row:02d}C{column:02d}: {tile['band']:<10} "
              f"(score {tile['score']:.2f}) rolled {tile['tiers']}")


def sweep_population(base: list[str], climate: list[str],
                     terrain: list[str], seeds: int = 500) -> None:
    tier_totals = Counter()
    souls, filled, empties, quiet_share = [], [], [], []
    for seed in range(seeds):
        census = roll_census(base, climate, terrain, seed)
        tier_totals.update(tier for tile in census.values()
                           for tier in tile["tiers"])
        souls.append(sum(TIER_PEOPLE[tier] for tile in census.values()
                         for tier in tile["tiers"]))
        counts = [len(tile["tiers"]) for tile in census.values()]
        filled.append(sum(counts) / len(counts))
        empties.append(sum(1 for n in counts if n == 0))
        high = [tile for tile in census.values()
                if tile["band"] in ("high", "dense")
                and not tile["historical"]]
        quiet_share.append(sum(1 for tile in high
                               if "T" not in tile["tiers"]
                               and "C" not in tile["tiers"]) / len(high))
    n = seeds
    print(f"{n} seeds: souls mean {sum(souls) / n:,.0f} "
          f"(min {min(souls):,}, max {max(souls):,})")
    print("settlements per world " + ", ".join(
        f"{tier}: {tier_totals[tier] / n:.1f}" for tier in TIER_ORDER)
        + f"; total {sum(tier_totals.values()) / n:.1f}")
    print(f"slots filled per land tile mean {sum(filled) / n:.2f}; "
          f"empty tiles mean {sum(empties) / n:.0f}/314")
    print(f"quiet rich country: {100 * sum(quiet_share) / n:.0f}% of "
          f"high+dense tiles roll no town (min "
          f"{100 * min(quiet_share):.0f}%, max "
          f"{100 * max(quiet_share):.0f}%)")


def main() -> None:
    base = load_grid(BASE_PATH, BASE_GLYPHS)
    climate = load_grid(CLIMATE_PATH, set(CLIMATES) | {"."})
    terrain = load_grid(TERRAIN_PATH, set(TERRAINS) | {"."})
    problems = validate_climate(base, climate) + validate_terrain(base,
                                                                  terrain)
    if problems:
        for line in problems:
            print(f"LINT: {line}")
        sys.exit(f"{len(problems)} problem(s) -- fix the overlay")
    if len(sys.argv) > 1 and sys.argv[1] == "terrain":
        render_terrain(base, climate, terrain)
        return
    if len(sys.argv) > 1 and sys.argv[1] == "potential":
        render_potential(base, climate, terrain)
        return
    if len(sys.argv) > 1 and sys.argv[1] == "population":
        if "--sweep" in sys.argv[2:]:
            sweep_population(base, climate, terrain)
        else:
            seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            render_population(base, climate, terrain, seed)
        return
    if len(sys.argv) > 1 and sys.argv[1] == "harvest":
        if "--sweep" in sys.argv[2:]:
            sweep_harvest(climate)
        else:
            seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            render_harvest(climate, seed)
        return
    render_side_by_side(base, climate, ("TERRAIN", "CLIMATE"))
    censuses(climate)


if __name__ == "__main__":
    main()
