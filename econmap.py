"""The tile economy arc's eyeball tool (2026-08-21, plan.md Part 1).

Stdlib-only and close to standalone: it reads the authored resources
directly and renders them as 30x18 ASCII with censuses underneath, so it
can be run against a half-drawn overlay while the rules it will obey are
still being designed.  What it no longer does is keep its own copy of a
number the game already owns: as each round SHIPS, its constants move
into places.py and the tool imports them back (the arc's one-authority-
per-constant rule).  The climate and terrain vocabularies and the whole
potential law went that way on 2026-08-21 with session 1; the harvest,
population and trade constants below are still authored here, because
their sessions have not shipped.

    python econmap.py                  # the climate overlay + lint
    python econmap.py terrain          # the terrain overlay + land character
    python econmap.py potential        # the derived numbers (round 3's input)
    python econmap.py harvest [SEED]   # one rolled last-harvest layer
    python econmap.py harvest --sweep  # the distribution over 500 seeds
    python econmap.py population [SEED]   # one rolled settlement census
    python econmap.py population --sweep  # the census over 500 seeds
    python econmap.py routes [SEED]    # the mines, goods and trade routes
    python econmap.py routes --sweep   # route stability over 100 seeds

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
identical in every campaign like the map itself.  Both layers SHIPPED into
worldgen on 2026-08-21 (designlog's (F) entry): a Tile now carries its
climate, its terrain, its cover word and the derived tags, and this mode
draws the same law the game does.

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

The ROUTES mode is round 4's layer.  Author the physical, derive the
human: the MINES and the goods no law can derive are authored, few and
famous; the land's produce (grain, wine, wool, horses, timber, furs) is
derived from rounds 1-3's own outputs; the ROUTES are computed by the
pathfinder between origins and markets -- except the named legendary
roads, whose endpoints and cargo are authored and whose line the same
pathfinder draws.  The EXOTICS are goods like any other (2026-08-21,
round 4 -- the plan's keep-them-off-the-map remark reversed at the
designer's direction): their origin tiles are simply the frame's doors,
the eastern gate and the delta port, which is exactly what keeps the
legendary roads worth taxing and robbing.  A mine seats an authored
MINE TOWN in the census (slot 1, tier town, always free -- the mining
law is its charter), and a mine town whose own ground cannot feed it
gets a grain road: the food caravan, a route and a vulnerability in one
stroke.

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

import heapq
import random
import sys
from collections import Counter, deque
from pathlib import Path

import places                   # the shipped layers' one authority

RESOURCES = Path(__file__).with_name("resources")
BASE_PATH = RESOURCES / "europe_map.txt"
CLIMATE_PATH = RESOURCES / "europe_climate.txt"
TERRAIN_PATH = RESOURCES / "europe_terrain.txt"

ROWS, COLUMNS = 18, 30
BASE_GLYPHS = {".", "#", "^", "~"}

# ONE AUTHORITY PER CONSTANT (the arc's standing rule). The climate and
# terrain vocabularies and every number of the potential law SHIPPED with
# the ground session on 2026-08-21: they live in places.py now, and the
# tool imports them back rather than keeping a second copy. What is still
# authored HERE is what has not shipped yet -- the harvest roll, the
# population score and census, and the trade layer.
CLIMATES = places.CLIMATE_LETTERS
TERRAINS = places.TERRAIN_LETTERS


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
# The land's potential (derived, deterministic -- SHIPPED 2026-08-21)
# --------------------------------------------------------------------------- #
# Author the physical, derive the human.  The law and every constant behind
# it now live in places.py, where worldgen reads them; the names below are
# the tool's window onto the same objects, so the eyeball map and the game
# can never drift.  What the game itself stores and speaks are the words --
# the cover word and the derived tags -- and those come from places too.

WOODED_MIN = places.WOODED_MIN
FARMLAND_MIN = places.FARMLAND_MIN
HAND_MARKS = places.HAND_MARKS
tile_economy = places.tile_economy


def tile_tags(economy: dict, terrain: str, letter: str,
              row: int, column: int) -> list[str]:
    """The tag list worldgen stamps on a land Tile, minus the country and
    the positional words the tool has no world to ask for."""
    return [terrain] + places.derived_tags(economy, CLIMATES[letter],
                                           row, column)


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
            economy = tile_economy(CLIMATES[climate[r][c]], word,
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
            mine = MINES.get((r + 1, c + 1))
            if name:
                tiers = (HISTORICAL_TIERS[name]
                         + _draw(rng, ARRANGEMENTS[band])[:3])
            elif mine:                  # the mine town: authored tier town
                tiers = "T" + _draw(rng, ARRANGEMENTS[band])[:3]
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
            if name or mine:            # the famous names hold their own
                free[0] = True          # charters, always -- a mine town's
                                        # mining law IS its charter
            manor = (len(tiers) >= 2 and tiers[0] == "V"
                     and rng.random() < MANOR_CHANCE)
            census[(r, c)] = {"band": band, "score": score,
                              "tiers": tiers, "free": free, "manor": manor,
                              "historical": name,
                              "mine": mine[0] if mine else None}
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
    print("\nMINE TOWNS (authored town in slot 1; round 4)")
    for (row, column), (name, goods) in sorted(MINES.items(),
                                               key=lambda kv: kv[1][0]):
        tile = census[(row - 1, column - 1)]
        print(f"  {name:<17} at R{row:02d}C{column:02d}: "
              f"{tile['band']:<10} rolled {tile['tiers']}  "
              f"({', '.join(goods)})")


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


# --------------------------------------------------------------------------- #
# The trade layer (round 4: mines, goods & the routes)
# --------------------------------------------------------------------------- #
# Author the physical, derive the human.  Mines and the goods no law can
# derive are AUTHORED, few and famous; the land's produce is DERIVED from
# rounds 1-3's outputs; the ordinary routes are COMPUTED between origins
# and markets by the same edge model the game walks, and the legendary
# roads are authored endpoints whose line the pathfinder draws.  Exotics
# are goods like any other -- their origins are the frame's doors.

MINES = {                   # (row, column): (the mine town, its goods).
    (9, 14): ("Goslar", ("silver", "copper")),    # Rammelsberg & the Harz
    (9, 19): ("Kutna Hora", ("silver",)),         # Bohemia's silver
    (3, 22): ("Falun", ("copper", "iron")),       # the great copper mount
    (10, 20): ("Banska Stiavnica", ("silver", "copper")),   # Carpathian
    (10, 8): ("Melle", ("silver",)),              # the old western seam
    (11, 14): ("Erzberg", ("iron",)),             # the iron mountain
    (13, 18): ("Novo Brdo", ("silver",)),         # the Balkan silver
    (8, 16): ("Luneburg", ("salt",)),             # the northern salt
    (10, 21): ("Wieliczka", ("salt",)),           # the eastern salt
}
GOODS_AUTHORED = {          # origin colour with no mine town under it
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
ENDPOINT_NAMES = {          # labels for endpoints that are not towns
    (11, 30): "the eastern gate", (18, 24): "the delta port",
    (18, 26): "the Nile granary", (6, 22): "the amber shore",
    (6, 15): "the Sound", (10, 5): "the salt pans",
    (11, 6): "the wine coast", (8, 11): "the Low Countries' looms",
    (13, 14): "the Tuscan looms", (12, 13): "the armouries",
    (11, 19): "the horse fairs",
}

# The derived origins, by law over rounds 1-3's numbers.
GRAIN_SURPLUS = 0.55        # realized arable at/above this exports grain:
                            # the alluvial river corridors and the Nile --
                            # ordinary plain country feeds itself only
WINE_CLIMATES = "mw"        # the vine: med and wet-med farmland
WINE_MIN = 0.30
WOOL_CLIMATES = "om"        # the sheep west: oceanic and med hill country
WOOL_PASTORAL = 0.40
HORSE_PASTORAL = 0.40       # the steppe's herds (plus the authored fairs)
FUR_CLIMATES = "tuc"        # deep forest in the cold north and east
MIN_PRODUCE_REGION = 2      # a derived produce region under this many
                            # tiles is local colour, never an export
                            # (grain exempt: one alluvial tile is a
                            # granary; timber moves by water only)

# Where each good goes.  destinations: markets = city-grade chiefs +
# historical towns + mine towns; cities = the same without mine towns;
# metropolises = the three M chiefs; smiths = the arms towns + cities;
# cloth = the cloth towns; capital = the origin's own crown; capitals =
# all three.  k = how many destinations; max_days = bulk range (None =
# rich goods travel any distance).  Silk, spice, sugar, dyes and amber
# have no row: they move only on the legendary roads.
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
MINE_FOOD_DAYS = 6          # a hungry mine's grain road reaches this far
CAPITALS = {"firascir": (9, 10), "mortellaria": (14, 14),
            "tergal": (10, 27)}

LEGENDARY = (               # authored endpoints and cargo; computed line
    {"name": "the Silk Road", "from": (11, 30), "to": (14, 27),
     "goods": ("silk", "dyes")},
    {"name": "the Spice Lane", "from": (18, 24), "to": (12, 14),
     "goods": ("spice", "sugar", "dyes")},
    {"name": "the Amber Road", "from": (6, 22), "to": (12, 14),
     "goods": ("amber",)},
    {"name": "the Fairs Road", "from": (12, 14), "to": (9, 10),
     "goods": ("silk", "spice", "sugar")},
    {"name": "the Grain Fleet", "from": (18, 26), "to": (14, 27),
     "goods": ("grain",)},
)

# places.py's settled edge model, restated so the tool stays standalone:
# north-south 2 days, east-west 1, +1 when EITHER end is a mountain (once,
# which is what keeps it symmetric); sea sails at land cost.
EAST_WEST_DAYS = 1
NORTH_SOUTH_DAYS = 2
MOUNTAIN_SURCHARGE = 1


def _at0(rc: tuple[int, int]) -> tuple[int, int]:
    return (rc[0] - 1, rc[1] - 1)


def _grid_neighbors(r: int, c: int):
    for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < ROWS and 0 <= cc < COLUMNS:
            yield rr, cc


def _edge_days(base: list[str], a: tuple[int, int],
               b: tuple[int, int]) -> int:
    days = EAST_WEST_DAYS if a[0] == b[0] else NORTH_SOUTH_DAYS
    if "^" in (base[a[0]][a[1]], base[b[0]][b[1]]):
        days += MOUNTAIN_SURCHARGE
    return days


def _tree(base: list[str], start: tuple[int, int]):
    """Dijkstra from one tile over the whole frame (sea included);
    frontier ordered by (cost, row, column) like places._single_source."""
    distance = {start: 0}
    previous: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    heap = [(0, start)]
    while heap:
        d, node = heapq.heappop(heap)
        if d > distance[node]:
            continue
        for nxt in _grid_neighbors(*node):
            nd = d + _edge_days(base, node, nxt)
            if nd < distance.get(nxt, 10 ** 9):
                distance[nxt] = nd
                previous[nxt] = node
                heapq.heappush(heap, (nd, nxt))
    return distance, previous


def _path_from(previous, tile):
    """The path from `tile` back to the tree's root, tile first."""
    path = [tile]
    while previous[path[-1]] is not None:
        path.append(previous[path[-1]])
    return path


def _regions(tiles: set) -> list[set]:
    """Connected components (4-neighbor) of an origin tile set."""
    remaining, out = set(tiles), []
    while remaining:
        seed_tile = min(remaining)
        component, frontier = {seed_tile}, deque([seed_tile])
        while frontier:
            r, c = frontier.popleft()
            for nxt in _grid_neighbors(r, c):
                if nxt in remaining and nxt not in component:
                    component.add(nxt)
                    frontier.append(nxt)
        remaining -= component
        out.append(component)
    return out


def build_origins(base, climate, terrain, economies) -> list[dict]:
    """Every goods origin: authored mines and colour, derived produce."""
    origins = []
    for rc, (name, goods) in MINES.items():
        origins.append({"tiles": {_at0(rc)}, "goods": tuple(goods),
                        "name": name})
    for rc, goods in GOODS_AUTHORED.items():
        origins.append({"tiles": {_at0(rc)}, "goods": tuple(goods),
                        "name": None})
    derived = {good: set() for good in
               ("grain", "wine", "wool", "horses", "timber", "furs")}
    for (r, c), eco in economies.items():
        letter = climate[r][c]
        river = base[r][c] == "~" or letter == "n"
        coast = _is_coast(base, r, c)
        if eco["realized"] >= GRAIN_SURPLUS:
            derived["grain"].add((r, c))
        if letter in WINE_CLIMATES and eco["realized"] >= WINE_MIN:
            derived["wine"].add((r, c))
        if letter in WOOL_CLIMATES and eco["pastoral"] >= WOOL_PASTORAL:
            derived["wool"].add((r, c))
        if letter == "s" and eco["pastoral"] >= HORSE_PASTORAL:
            derived["horses"].add((r, c))
        if (eco["forest"] >= WOODED_MIN and (river or coast)
                and TERRAINS[terrain[r][c]] != "marsh"):
            derived["timber"].add((r, c))      # fen carr is not ship timber
        if eco["cover"] == "deep forest" and letter in FUR_CLIMATES:
            derived["furs"].add((r, c))
    for good, tiles in derived.items():
        goods = ("furs", "wax") if good == "furs" else (good,)
        for region in _regions(tiles):
            if good != "grain" and len(region) < MIN_PRODUCE_REGION:
                continue                # a lone hill's wool is local colour,
            origins.append({"tiles": region, "goods": goods, "name": None})
    return origins                      # not an export; grain is exempt (a
                                        # single alluvial tile IS a granary)


def roll_routes(base, climate, terrain, seed: int):
    """One world's trade network: routes, origins, census, unfed mines."""
    census = roll_census(base, climate, terrain, seed)
    economies, _tags, _character = economy_grids(base, climate, terrain)
    origins = build_origins(base, climate, terrain, economies)
    historical = {_at0(rc) for rc in HISTORICAL_TILES}
    mine_tiles = {_at0(rc) for rc in MINES}
    chiefs = {t: (rec["tiers"][0] if rec["tiers"] else "")
              for t, rec in census.items()}
    cities = {t for t, chief in chiefs.items()
              if chief in ("M", "C")} | historical
    demand_sets = {
        "markets": cities | mine_tiles,
        "cities": cities,
        "metropolises": {t for t, chief in chiefs.items() if chief == "M"},
        "smiths": cities | {_at0(rc) for rc, goods in GOODS_AUTHORED.items()
                            if "arms" in goods},
        "cloth": {_at0(rc) for rc, goods in GOODS_AUTHORED.items()
                  if "cloth" in goods},
        "capitals": {_at0(rc) for rc in CAPITALS.values()},
    }
    trees: dict[tuple[int, int], tuple] = {}

    def tree(dest):
        if dest not in trees:
            trees[dest] = _tree(base, dest)
        return trees[dest]

    raw = []
    for origin in origins:
        by_rule: dict[tuple, list[str]] = {}
        for good in origin["goods"]:
            rule = GOOD_ROUTES.get(good)
            if rule is not None:        # exotics ride the legendary roads
                by_rule.setdefault(rule, []).append(good)
        for (dest_kind, k, max_days), goods in by_rule.items():
            if dest_kind == "capital":
                r, c = min(origin["tiles"])
                dests = {_at0(CAPITALS[country_at(r + 1, c + 1)])}
            else:
                dests = demand_sets[dest_kind]
            ranked = []
            for dest in sorted(dests - origin["tiles"]):
                distance, _previous = tree(dest)
                member = min(origin["tiles"],
                             key=lambda t: (distance[t], t))
                ranked.append((distance[member], dest, member))
            ranked.sort()
            for days, dest, member in ranked[:k]:
                if max_days is not None and days > max_days:
                    continue
                _distance, previous = tree(dest)
                raw.append({"name": None, "goods": tuple(goods),
                            "days": days,
                            "path": _path_from(previous, member)})
    unfed = []
    for rc, (name, _goods) in MINES.items():
        mine = _at0(rc)
        if economies[mine]["realized"] >= FARMLAND_MIN:
            continue                    # the mine's own ground feeds it
        distance, previous = tree(mine)
        grain = [(distance[t], t) for origin in origins
                 if "grain" in origin["goods"] for t in origin["tiles"]
                 if distance[t] <= MINE_FOOD_DAYS]
        if not grain:
            unfed.append(name)          # no grain within reach: the
            continue                    # mountain feeds itself badly
        days, member = min(grain)
        raw.append({"name": None, "goods": ("grain",), "days": days,
                    "path": _path_from(previous, member)})
        # the tree is rooted at the mine, so the path already runs
        # grain-country -> mine town: the food caravan's own direction
    for spec in LEGENDARY:
        goal = _at0(spec["to"])
        distance, previous = tree(goal)
        start = _at0(spec["from"])
        raw.append({"name": spec["name"], "goods": tuple(spec["goods"]),
                    "days": distance[start],
                    "path": _path_from(previous, start)})
    routes: dict[tuple, dict] = {}      # merged on shared endpoints
    for route in raw:
        key = (route["path"][0], route["path"][-1])
        kept = routes.get(key)
        if kept is None:
            routes[key] = route
        else:
            kept["goods"] = tuple(dict.fromkeys(kept["goods"]
                                                + route["goods"]))
            kept["name"] = kept["name"] or route["name"]
    return list(routes.values()), origins, census, unfed


def _endpoint_label(tile, census) -> str:
    rc = (tile[0] + 1, tile[1] + 1)
    if rc in HISTORICAL_TILES:
        return HISTORICAL_TILES[rc]
    if rc in MINES:
        return MINES[rc][0]
    if rc in ENDPOINT_NAMES:
        return ENDPOINT_NAMES[rc]
    return f"R{rc[0]:02d}C{rc[1]:02d}"


GOOD_PRIORITY = ("grain", "wine", "wool", "horses", "furs", "timber",
                 "salt", "herring", "amber", "cloth", "arms")
GOOD_MARKS = {"grain": "g", "wine": "v", "wool": "w", "horses": "h",
              "furs": "f", "timber": "t", "salt": "s", "herring": "r",
              "amber": "b", "cloth": "c", "arms": "a"}


def render_routes(base, climate, terrain, seed: int) -> None:
    routes, origins, census, unfed = roll_routes(base, climate, terrain,
                                                 seed)
    goods_at: dict[tuple[int, int], list[str]] = {}
    for origin in origins:
        for t in origin["tiles"]:
            goods_at.setdefault(t, []).extend(origin["goods"])
    traffic = Counter()
    ports, sea_tiles = set(), set()
    for route in routes:
        for t in route["path"]:
            traffic[t] += 1
            if base[t[0]][t[1]] == ".":
                sea_tiles.add(t)
        for a, b in zip(route["path"], route["path"][1:]):
            a_sea, b_sea = base[a[0]][a[1]] == ".", base[b[0]][b[1]] == "."
            if a_sea != b_sea:
                ports.add(b if a_sea else a)
    left, right = [], []
    for r in range(ROWS):
        goods_line, traffic_line = "", ""
        for c in range(COLUMNS):
            if base[r][c] == ".":
                goods_line += "."
                traffic_line += (str(min(9, traffic[(r, c)]))
                                 if (r, c) in sea_tiles else ".")
                continue
            if (r + 1, c + 1) in MINES:
                goods_line += "M"
            elif (r + 1, c + 1) in ((11, 30), (18, 24)):
                goods_line += "x"
            else:
                here = goods_at.get((r, c), ())
                mark = next((GOOD_MARKS[g] for g in GOOD_PRIORITY
                             if g in here), "-")
                goods_line += mark
            traffic_line += (str(min(9, traffic[(r, c)]))
                             if traffic[(r, c)] else "-")
        left.append(goods_line)
        right.append(traffic_line)
    render_side_by_side(left, right,
                        ("GOODS & MINES", "TRAFFIC (routes crossing)"))
    print("\ngoods: M mine, x exotic door, g grain, v wine, w wool, "
          "h horses,\n  f furs+wax, t timber, s salt, r herring, b amber, "
          "c cloth, a arms")
    print(f"\nROUTES, seed {seed} ({len(routes)} after merging; "
          f"{len(LEGENDARY)} legendary)")
    named = [route for route in routes if route["name"]]
    plain = [route for route in routes if not route["name"]]
    for route in named + sorted(plain, key=lambda x: x["goods"]):
        label = (f"{_endpoint_label(route['path'][0], census)} -> "
                 f"{_endpoint_label(route['path'][-1], census)}")
        name = route["name"] or ""
        print(f"  {name:<15} {label:<28} {', '.join(route['goods'])} "
              f"({route['days']}d)")
    land_on = sum(1 for t, n in traffic.items()
                  if n and base[t[0]][t[1]] != ".")
    print(f"\nTRAFFIC {land_on} land tiles on a route, "
          f"{len(sea_tiles)} sea-lane tiles, {len(ports)} ports; "
          f"crossroads (3+): "
          f"{sum(1 for n in traffic.values() if n >= 3)}")
    goods_census = Counter()
    for origin in origins:
        for good in origin["goods"]:
            goods_census[good] += len(origin["tiles"])
    print("GOODS CENSUS (origin tiles) " + ", ".join(
        f"{good}:{n}" for good, n in goods_census.most_common()))
    if unfed:
        print(f"UNFED MINES (no grain within {MINE_FOOD_DAYS} days): "
              + ", ".join(unfed))


def sweep_routes(base, climate, terrain, seeds: int = 100) -> None:
    counts, land_on, port_counts = [], [], []
    for seed in range(seeds):
        routes, _origins, _census, _unfed = roll_routes(
            base, climate, terrain, seed)
        counts.append(len(routes))
        traffic = Counter(t for route in routes for t in route["path"])
        land_on.append(sum(1 for t in traffic if base[t[0]][t[1]] != "."))
        ports = set()
        for route in routes:
            for a, b in zip(route["path"], route["path"][1:]):
                a_sea = base[a[0]][a[1]] == "."
                b_sea = base[b[0]][b[1]] == "."
                if a_sea != b_sea:
                    ports.add(b if a_sea else a)
        port_counts.append(len(ports))
    n = seeds
    print(f"{n} seeds: routes mean {sum(counts) / n:.1f} "
          f"(min {min(counts)}, max {max(counts)}); "
          f"land tiles on a route mean {sum(land_on) / n:.0f}/314; "
          f"ports mean {sum(port_counts) / n:.1f}")


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
    if len(sys.argv) > 1 and sys.argv[1] == "routes":
        if "--sweep" in sys.argv[2:]:
            sweep_routes(base, climate, terrain)
        else:
            seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            render_routes(base, climate, terrain, seed)
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
