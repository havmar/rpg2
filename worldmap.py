"""The ASCII world map -- procedural geography at area scale.

Generates the game world as a character map in the style of the reference
Europe map embedded below (`TEMPLATE`): `.` ocean, `#` land, `^` mountains,
rivers drawn with box-drawing glyphs. The full world is rolled at 80x40
(60x30 supported); only its 40x20 NORTHWEST CORNER is the playable game
world -- one civilisation's view of a larger world, the way the reference
map is Europe's view of Eurasia. Nothing is wired to the game yet: this
module is the generation algorithm and its inspection tools. rules.md's
"The World Map" add-on carries the geography principles; plan.md carries
the hook-up into the location system (a tile will correspond to an Area).

THE SCALE. One character is 30 km east-west and 60 km north-south -- a
terminal character cell is about twice as tall as it is wide, so the map
reads near-isotropic. A party walks about one tile east in a day, or half
a tile south: 30 km a day either way. There is no diagonal movement.

HOW A MAP IS ROLLED (the algorithm, chosen for stdlib-only determinism):

1. ELEVATION FIELD. Multi-octave value noise (anisotropy-corrected so
   features are round in km, not in characters), domain-warped by a second
   noise pair so coasts curve instead of following the lattice. On top of
   it, 2-3 plateau-shaped continent masks (flat core, linear rim) and a
   handful of small island masks: inside a continent's core the NOISE
   decides land vs water -- that is where the Europe-like raggedness, bays
   and inner seas come from -- while the rim fades the chance of land so
   each continent trails off into ocean instead of ending in a blob edge.
   The first continent is always anchored under the playable corner. A
   west-edge penalty (its width modulated by its own noise) rolls the map
   off into open ocean on the west without a straight cut.
2. SEA LEVEL BY PERCENTILE. The land/water ratio is not hoped for, it is
   SET: the threshold is the elevation percentile that yields the measured
   template ratio (plus a little slack for the fix-ups that drown tiles).
3. FIX-UPS, in order. The westernmost column becomes all ocean (the rule;
   the penalty above keeps the result organic). Then the diagonal rule:
   no two ocean tiles may touch only at a corner, and the fix is always
   LAND BECOMES OCEAN (per the design: straits open, inner seas grow),
   choosing the lower-elevation shoulder, repeated until stable -- this
   converges because land only ever shrinks. Then surplus specks drown
   (a few islands are wanted; an archipelago is not). Whole-component
   removal provably cannot create new diagonal violations, because two
   components touching at a corner would themselves be the forbidden
   pattern, which the previous pass removed.
4. MOUNTAINS as ranges, not speckle: random walks with momentum, started
   at high-elevation land (tournament pick) and steered uphill, so ranges
   sit on continent spines and shoulders. Budgeted to the template's
   mountain share of land.
5. RIVERS by descent of a breadth-first DISTANCE-TO-SEA field computed
   over land with mountains impassable -- so mountains are watershed
   divides, rivers rise beside them and never cross them, and every river
   provably reaches water (each step moves to a strictly closer tile).
   Sources prefer mountain feet far from the coast; a trace that touches
   an existing river joins it as a tributary (the junction becomes a
   three-way glyph); meander steps (sideways, same distance) keep them
   from beelining. Each tile's glyph is chosen by which neighbors the
   river actually connects to, so a bend is a corner glyph and a mouth
   visibly points into the sea -- the box-drawing answer to `~`'s
   ambiguous diagonals. Budgeted to the template's river share of land.
6. VALIDATE AND RETRY. A rolled map must pass the hard rules (west column,
   diagonal rule, 2-3 continents holding most of the land, a playable
   corner that is neither empty ocean nor wall-to-wall land, ratio bands).
   `generate` rolls deterministic sub-attempts of the seed until one
   passes, so the same seed always returns the same world.

WHY THESE RELATIONS AT THIS SCALE (30 km tiles): a river tile is mostly
land -- the tile has a hard-to-cross river IN it -- while an ocean tile
`.` is open water whose neighboring land tiles hold the coast; that is why
rivers get land-glyph treatment and the diagonal rule only polices ocean.
Mountains at this scale are RANGES (a tile of `^` is a massif, not a
peak), which is why they divide watersheds instead of hosting springs on
both slopes of one character. A strait one tile wide is sailable open
water; that is what the diagonal rule protects.

The one deliberate exception to the ASCII-output convention: river glyphs
are box-drawing characters (U+2500 block) by design. Run with
`PYTHONIOENCODING=utf-8` when piping on Windows.

Nothing here imports the rest of the game.

Run:  python worldmap.py                    # roll one world, print it + stats
      python worldmap.py --seed 7           # the same world every time
      python worldmap.py --lift             # full map, playable corner lifted
      python worldmap.py --play             # the playable 40x20 corner only
      python worldmap.py --size 60x30       # the smaller supported world
      python worldmap.py --count 5          # several seeds to eyeball
      python worldmap.py --check 100        # constraint pass-rate sweep
      python worldmap.py --template-stats   # the reference map, measured
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from collections import deque

# --------------------------------------------------------------------------- #
# The reference map (the hand-drawn Europe the generator is calibrated to)
# --------------------------------------------------------------------------- #

TEMPLATE = """\
..............................
...............#^^#######.....
...#.........#^^###.######.###
...##......^^####...##########
.#.##.....^^####...###########
.#..##....##.###.....#########
...####...........############
........###~####~############^
...########~####~#####~###~##^
....#######~#####^^^###~##~##^
.....######^^^#~~~~~~~~~.#.^^#
.....##^^####~.#^^####......##
.~~#^###....##...###.........#
.#####...#..^#...##..###^^####
..###......###........########
......###.................####
.##^^##########...##......####
##############################
"""

# Measured off TEMPLATE (`--template-stats` recomputes them): water 0.415 of
# all tiles, mountains 0.092 of land tiles, rivers 0.066 of land tiles, zero
# diagonal-only ocean contacts, one big landmass plus a Britain-sized island.
LAND_FRAC = 0.57        # target land share of all tiles, after fix-ups
MOUNTAIN_FRAC = 0.09    # target mountain share of land tiles
RIVER_FRAC = 0.065      # target river share of land tiles

# --------------------------------------------------------------------------- #
# Scale and vocabulary
# --------------------------------------------------------------------------- #

WORLD_W, WORLD_H = 80, 40    # the default full world
PLAY_W, PLAY_H = 40, 20      # the playable northwest corner (fits 40 columns)

KM_EW, KM_NS = 30, 60        # one tile in km; one day walks 30 km

OCEAN, LAND, MOUNTAIN = ".", "#", "^"

STEPS = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}
OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}

# A river tile's glyph is its actual connections: which of its four
# neighbors the river continues into (or, at the mouth, the sea it enters).
# A single-ended stub marks a source. This is why the diagonal river
# pattern cannot occur: a connection IS an orthogonal neighbor.
RIVER_GLYPHS = {
    frozenset("NS"): "│",   # |
    frozenset("EW"): "─",   # -
    frozenset("SE"): "┌",   # corner: down+right
    frozenset("SW"): "┐",   # corner: down+left
    frozenset("NE"): "└",   # corner: up+right
    frozenset("NW"): "┘",   # corner: up+left
    frozenset("NSE"): "├",  # tee
    frozenset("NSW"): "┤",
    frozenset("SEW"): "┬",
    frozenset("NEW"): "┴",
    frozenset("NSEW"): "┼",
    frozenset("N"): "╵",    # source stubs (half-lines)
    frozenset("S"): "╷",
    frozenset("E"): "╶",
    frozenset("W"): "╴",
}

# --------------------------------------------------------------------------- #
# Generation knobs (the tuning levers; see develop.md)
# --------------------------------------------------------------------------- #

ATTEMPTS = 60            # deterministic retry budget per seed
THRESHOLD_SLACK = 0.025  # extra land at sea level, for the fix-ups to drown

BASE_OCTAVES = ((26.0, 1.0), (13.0, 0.55), (6.5, 0.30), (3.2, 0.18))
WARP_OCTAVES = ((11.0, 1.0), (5.5, 0.5))
WARP_AMP = 3.0           # domain warp, in tiles east-west (halved north-south)

CONTINENT_WEIGHT = 0.50  # mask share of the elevation field
NOISE_WEIGHT = 0.50      # noise share (noise decides coasts at the rims;
                         # kept below the mask so the noise floor alone
                         # cannot bridge a strait between two continents)
PLATEAU = 2.2            # mask falloff steepness: core flat, rim linear
STRAIT_WEIGHT = 0.35     # trench depth where two continents' reaches meet
REACH = 1.35             # a continent repels land to this multiple of its
                         # radius: the trench lives in the channel BETWEEN
                         # rims (where masks are already zero), which is
                         # where bridges would otherwise form
COVER = 0.68             # continent domes cover more than the land target,
                         # so the sea-level cut stays inside their rims and
                         # the gaps between continents stay sea
SEPARATION = 1.08        # min seed distance as a share of dome tangency:
                         # a few tiles of guaranteed channel between rims
THREE_CONTINENTS = 0.6   # chance of 3 continents (else 2)
ISLAND_SEEDS = (3, 7)    # count range of small island masks
ISLAND_RADIUS = (2.5, 6.0)

WEST_SEA = 6             # west-edge ocean falloff width, tiles
WEST_PENALTY = (0.30, 0.45)   # base + noise-scaled part of the falloff

MAX_SMALL_ISLANDS = 8    # keep at most this many components under 12 tiles
SMALL_ISLAND = 12

RANGE_LEN = (4, 9)       # mountain range walk length
RANGE_WIDEN = 0.18       # chance a range step also paints one flank tile
RANGE_MOMENTUM = 3.2     # keep-direction weight over turning

MIN_SOURCE_DIST = 4      # a river rises at least this far from the sea
MAX_SOURCE_DIST = 11     # ...and at most this far (template rivers are 4-9)
SOURCE_NEAR_MOUNTAIN = 3.5   # score bonus for rising at a mountain foot
RIVER_MOMENTUM = 2.6     # keep-direction weight in the trace
RIVER_RUN = 4            # straight steps before momentum flips to a bend
MEANDER = 0.5            # weight of a sideways (same-distance) step
RIVERSIDE_PENALTY = 0.12     # weight factor for stepping beside another river
RIVER_RING2_PENALTY = 0.45   # milder factor two tiles from another river
                             # (keeps two rivers from sharing one valley)
SELF_SIDE_PENALTY = 0.05     # weight factor for stepping beside own path


# --------------------------------------------------------------------------- #
# Value noise (stdlib-only, anisotropy-corrected, continuous)
# --------------------------------------------------------------------------- #

class _Noise:
    """Fractal value noise sampleable at float coordinates.

    Coordinates are TILES; internally y is doubled so one unit is 30 km in
    both axes and features come out round in km. The lattice carries a
    margin so domain-warped samples stay in range.
    """

    _MARGIN = 8.0

    def __init__(self, rng: random.Random, w: int, h: int,
                 octaves=BASE_OCTAVES) -> None:
        self.octaves = []
        for wavelength, amp in octaves:
            nx = int((w + 2 * self._MARGIN) / wavelength) + 3
            ny = int((h * 2 + 2 * self._MARGIN) / wavelength) + 3
            lattice = [[rng.random() for _ in range(nx)] for _ in range(ny)]
            self.octaves.append((lattice, wavelength, amp))

    def at(self, x: float, y: float) -> float:
        u0 = x + self._MARGIN
        v0 = y * 2 + self._MARGIN
        total = 0.0
        norm = 0.0
        for lattice, wavelength, amp in self.octaves:
            u = max(0.0, u0 / wavelength)
            v = max(0.0, v0 / wavelength)
            xi = min(int(u), len(lattice[0]) - 2)
            yi = min(int(v), len(lattice) - 2)
            tx = u - xi
            ty = v - yi
            tx = tx * tx * (3 - 2 * tx) if tx < 1 else 1.0
            ty = ty * ty * (3 - 2 * ty) if ty < 1 else 1.0
            row0, row1 = lattice[yi], lattice[yi + 1]
            top = row0[xi] + (row0[xi + 1] - row0[xi]) * tx
            bot = row1[xi] + (row1[xi + 1] - row1[xi]) * tx
            total += amp * (top + (bot - top) * ty)
            norm += amp
        return total / norm


# --------------------------------------------------------------------------- #
# The elevation field and sea level
# --------------------------------------------------------------------------- #

def _continent_seeds(rng: random.Random, w: int,
                     h: int) -> tuple[list[tuple], list[tuple]]:
    """(continents, islands) as (x, v, radius) masks in 30-km units (v=2y).

    The FIRST continent is anchored under the playable corner so the game
    world is never an empty sea. The rest may sit anywhere east and south;
    a mask running off the east or south edge is simply cut by the frame,
    like Asia on a Europe map. Islands are small free-floating masks.
    """
    want = 3 if rng.random() < THREE_CONTINENTS else 2
    area = w * (2 * h)
    seeds: list[tuple] = []
    done = False
    for k in (want, 2):     # if three will not fit, roll a two-continent world
        base_r = math.sqrt(area * COVER / (k * math.pi))
        for shrink in (1.0, 0.92, 0.85):
            # unequal continents pack better and look more natural;
            # normalized in quadrature so total dome area honors COVER
            scales = [rng.uniform(0.8, 1.0), rng.uniform(0.9, 1.15)]
            if k == 3:
                scales += [rng.uniform(0.6, 0.9)]
            f = math.sqrt(k / sum(s * s for s in scales)) * shrink
            radii = [base_r * s * f for s in scales]
            for _layout in range(8):
                seeds = [(rng.uniform(0.30 * w, 0.48 * w),
                          rng.uniform(0.18 * 2 * h, 0.60 * 2 * h), radii[0])]
                for r in radii[1:]:
                    placed = None
                    while placed is None and r >= 0.5 * base_r * shrink:
                        for _try in range(120):
                            sx = rng.uniform(0.30 * w, 0.94 * w)
                            sv = rng.uniform(0.08 * 2 * h, 0.92 * 2 * h)
                            if all(math.hypot(sx - ox, sv - ov)
                                   >= SEPARATION * (r + orr)
                                   for ox, ov, orr in seeds):
                                placed = (sx, sv, r)
                                break
                        r *= 0.92
                    if placed is None:
                        break           # crowded layout; try a fresh one
                    seeds.append(placed)
                done = len(seeds) == k
                if done:
                    break
            if done:
                break
        if done:
            break
    islands = []
    for _ in range(rng.randint(*ISLAND_SEEDS)):
        for _try in range(60):
            ix = rng.uniform(0.12 * w, 0.96 * w)
            iv = rng.uniform(0.04 * 2 * h, 0.96 * 2 * h)
            ir = rng.uniform(*ISLAND_RADIUS)
            # an island may crowd ONE continent's shelf (a Britain), never
            # sit in the strait between two (a bridge) nor inside a
            # continent's own core (where it would just vanish into it)
            dists = [(math.hypot(ix - ox, iv - ov), orr)
                     for ox, ov, orr in seeds]
            near = sum(1 for d, orr in dists if d < orr + ir + 2)
            if near <= 1 and all(d >= 0.85 * orr for d, orr in dists):
                islands.append((ix, iv, ir))
                break
    return seeds, islands


def _elevation(rng: random.Random, w: int, h: int) -> list[list[float]]:
    base = _Noise(rng, w, h, BASE_OCTAVES)
    warp_x = _Noise(rng, w, h, WARP_OCTAVES)
    warp_y = _Noise(rng, w, h, WARP_OCTAVES)
    coast = _Noise(rng, w, h, ((7.0, 1.0), (3.0, 0.5)))
    continents, islands = _continent_seeds(rng, w, h)
    elev = [[0.0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            wx = x + (warp_x.at(x, y) - 0.5) * WARP_AMP
            wy = y + (warp_y.at(x, y) - 0.5) * WARP_AMP / 2
            mask = reach1 = reach2 = 0.0
            for sx, sv, r in continents:
                t = math.hypot(wx - sx, wy * 2 - sv) / r
                mask = max(mask, min(1.0, (1.0 - t) * PLATEAU))
                re = max(0.0, min(1.0, REACH - t))
                if re > reach1:
                    reach1, reach2 = re, reach1
                elif re > reach2:
                    reach2 = re
            for sx, sv, r in islands:
                t = math.hypot(wx - sx, wy * 2 - sv) / r
                mask = max(mask, min(1.0, (1.0 - t) * PLATEAU))
            e = (CONTINENT_WEIGHT * mask
                 - STRAIT_WEIGHT * math.sqrt(reach2)
                 + NOISE_WEIGHT * base.at(wx, wy)
                 + rng.uniform(0.0, 0.01))
            if x < WEST_SEA:
                fade = (1.0 - x / WEST_SEA) ** 1.3
                e -= fade * (WEST_PENALTY[0]
                             + WEST_PENALTY[1] * coast.at(2.0, y))
            elev[y][x] = e
    return elev


def _sea_level(elev: list[list[float]], w: int, h: int) -> list[list[str]]:
    flat = sorted(v for row in elev for v in row)
    cut = flat[min(int(len(flat) * (1 - LAND_FRAC - THRESHOLD_SLACK)),
                   len(flat) - 1)]
    return [[LAND if elev[y][x] >= cut else OCEAN for x in range(w)]
            for y in range(h)]


# --------------------------------------------------------------------------- #
# Fix-ups: the west edge, the diagonal rule, the island budget
# --------------------------------------------------------------------------- #

def _enforce_west(terrain: list[list[str]]) -> None:
    for row in terrain:
        row[0] = OCEAN


def _fix_diagonal_ocean(terrain: list[list[str]],
                        elev: list[list[float]]) -> int:
    """No ocean tiles touching only at a corner; land drowns to fix it.

    In every 2x2 with ocean on one diagonal and land on the other, the
    lower-elevation land shoulder becomes ocean (straits open along low
    ground). Repeats until stable; converges because land only shrinks.
    The same pass therefore also guarantees no two LAND components touch
    corner-to-corner.
    """
    w, h = len(terrain[0]), len(terrain)
    drowned = 0
    changed = True
    while changed:
        changed = False
        for y in range(h - 1):
            for x in range(w - 1):
                a = terrain[y][x] == OCEAN
                b = terrain[y][x + 1] == OCEAN
                c = terrain[y + 1][x] == OCEAN
                d = terrain[y + 1][x + 1] == OCEAN
                if a and d and not b and not c:
                    lx, ly = ((x + 1, y) if elev[y][x + 1] <= elev[y + 1][x]
                              else (x, y + 1))
                elif b and c and not a and not d:
                    lx, ly = ((x, y) if elev[y][x] <= elev[y + 1][x + 1]
                              else (x + 1, y + 1))
                else:
                    continue
                terrain[ly][lx] = OCEAN
                drowned += 1
                changed = True
    return drowned


def _components(terrain: list[list[str]], value_is_land: bool) -> list[set]:
    """4-connected components of land (or of ocean), largest first."""
    w, h = len(terrain[0]), len(terrain)
    seen: set[tuple[int, int]] = set()
    comps = []
    for y in range(h):
        for x in range(w):
            if ((terrain[y][x] != OCEAN) != value_is_land
                    or (x, y) in seen):
                continue
            comp = set()
            stack = [(x, y)]
            seen.add((x, y))
            while stack:
                cx, cy = stack.pop()
                comp.add((cx, cy))
                for dx, dy in STEPS.values():
                    nx, ny = cx + dx, cy + dy
                    if (0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen
                            and (terrain[ny][nx] != OCEAN) == value_is_land):
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            comps.append(comp)
    comps.sort(key=len, reverse=True)
    return comps


def _prune_islands(terrain: list[list[str]]) -> int:
    """Drown surplus specks: islands yes, an archipelago no."""
    comps = _components(terrain, value_is_land=True)
    small = [c for c in comps if len(c) < SMALL_ISLAND]
    drowned = 0
    for comp in small[MAX_SMALL_ISLANDS:]:
        for x, y in comp:
            terrain[y][x] = OCEAN
            drowned += 1
    return drowned


# --------------------------------------------------------------------------- #
# Mountains: ranges walked uphill
# --------------------------------------------------------------------------- #

def _near(terrain: list[list[str]], x: int, y: int, value: str,
          reach: int) -> bool:
    w, h = len(terrain[0]), len(terrain)
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and terrain[ny][nx] == value:
                return True
    return False


def _place_mountains(terrain: list[list[str]], elev: list[list[float]],
                     rng: random.Random) -> None:
    w, h = len(terrain[0]), len(terrain)
    land = [(x, y) for y in range(h) for x in range(w)
            if terrain[y][x] == LAND]
    if not land:
        return
    budget = round(len(land) * MOUNTAIN_FRAC)
    guard = 0
    while budget > 0 and guard < 200:
        guard += 1
        start = None
        for spread in (3, 3, 2):    # prefer spread ranges, then relax
            for _ in range(40):
                picks = [rng.choice(land) for _ in range(7)]
                x, y = max(picks, key=lambda p: elev[p[1]][p[0]])
                if terrain[y][x] == LAND and not _near(terrain, x, y,
                                                       MOUNTAIN, spread):
                    start = (x, y)
                    break
            if start is not None:
                break
        if start is None:
            break
        cx, cy = start
        direction = rng.choice(list(STEPS))
        for _ in range(rng.randint(*RANGE_LEN)):
            if budget <= 0:
                break
            if terrain[cy][cx] != LAND:
                break
            terrain[cy][cx] = MOUNTAIN
            budget -= 1
            if rng.random() < RANGE_WIDEN and budget > 0:
                flanks = [(cx + dx, cy + dy) for dx, dy in STEPS.values()
                          if 0 <= cx + dx < w and 0 <= cy + dy < h
                          and terrain[cy + dy][cx + dx] == LAND]
                if flanks:
                    fx, fy = rng.choice(flanks)
                    terrain[fy][fx] = MOUNTAIN
                    budget -= 1
            options = []
            for nd, (dx, dy) in STEPS.items():
                if nd == OPPOSITE[direction]:
                    continue
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < w and 0 <= ny < h and terrain[ny][nx] == LAND:
                    weight = (RANGE_MOMENTUM if nd == direction else 1.0)
                    weight *= 0.5 + elev[ny][nx]
                    options.append((weight, nd, nx, ny))
            if not options:
                break
            total = sum(o[0] for o in options)
            roll = rng.uniform(0, total)
            for weight, nd, nx, ny in options:
                roll -= weight
                if roll <= 0:
                    break
            direction, cx, cy = nd, nx, ny


# --------------------------------------------------------------------------- #
# Rivers: descent of the distance-to-sea field
# --------------------------------------------------------------------------- #

def _sea_distance(terrain: list[list[str]]) -> dict[tuple[int, int], int]:
    """BFS distance to water over land; mountains are impassable divides."""
    w, h = len(terrain[0]), len(terrain)
    dist: dict[tuple[int, int], int] = {}
    queue = deque()
    for y in range(h):
        for x in range(w):
            if terrain[y][x] == OCEAN:
                dist[(x, y)] = 0
                queue.append((x, y))
    while queue:
        cx, cy = queue.popleft()
        for dx, dy in STEPS.values():
            nx, ny = cx + dx, cy + dy
            if (0 <= nx < w and 0 <= ny < h and (nx, ny) not in dist
                    and terrain[ny][nx] == LAND):
                dist[(nx, ny)] = dist[(cx, cy)] + 1
                queue.append((nx, ny))
    return dist


def _near_set(pos: tuple[int, int], members, exclude=(),
              reach: int = 1) -> bool:
    x, y = pos
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            if dx == dy == 0:
                continue
            nb = (x + dx, y + dy)
            if nb in members and nb not in exclude:
                return True
    return False


def _pick_source(terrain: list[list[str]], dist, rivers,
                 rng: random.Random) -> tuple[int, int] | None:
    w, h = len(terrain[0]), len(terrain)
    best, best_score = None, -1.0
    tries, found = 0, 0
    while tries < 200 and found < 12:
        tries += 1
        x = rng.randrange(w)
        y = rng.randrange(h)
        if terrain[y][x] != LAND:
            continue
        d = dist.get((x, y))
        if (d is None or not MIN_SOURCE_DIST <= d <= MAX_SOURCE_DIST
                or (x, y) in rivers):
            continue
        if any((x + dx, y + dy) in rivers
               for dy in range(-2, 3) for dx in range(-2, 3)):
            continue
        found += 1
        score = d + rng.uniform(0, 1.5)
        if _near(terrain, x, y, MOUNTAIN, 1):
            score += SOURCE_NEAR_MOUNTAIN
        if score > best_score:
            best, best_score = (x, y), score
    return best


def _trace_river(src: tuple[int, int], terrain: list[list[str]], dist,
                 rivers: dict, rng: random.Random) -> int:
    """Trace one river from src to water; returns tiles added.

    Every step goes to a strictly closer-to-sea tile (so the trace always
    ends at a coast or a lake), except bounded MEANDER steps sideways.
    Touching an existing river joins it -- the junction grows a third arm.
    """
    w, h = len(terrain[0]), len(terrain)
    own: list[tuple[int, int]] = []
    ownset: set[tuple[int, int]] = set()
    cur = src
    prevdir = None
    run_len = 0
    last_was_eq = False
    eq_left = dist[src]
    while True:
        own.append(cur)
        ownset.add(cur)
        rivers.setdefault(cur, set())
        d = dist[cur]
        if d == 1:
            waters = [nd for nd, (dx, dy) in STEPS.items()
                      if 0 <= cur[0] + dx < w and 0 <= cur[1] + dy < h
                      and terrain[cur[1] + dy][cur[0] + dx] == OCEAN]
            mouth = prevdir if prevdir in waters else rng.choice(waters)
            rivers[cur].add(mouth)
            return len(own)
        merges = []
        cands = []
        for nd, (dx, dy) in STEPS.items():
            nb = (cur[0] + dx, cur[1] + dy)
            ndist = dist.get(nb)
            if nb in ownset or ndist is None or ndist == 0:
                continue
            if nb in rivers:
                if ndist < d:
                    merges.append((nd, nb))
                continue
            if ndist == d - 1:
                weight = 1.0
            elif ndist == d and not last_was_eq and eq_left > 0:
                weight = MEANDER
            else:
                continue
            if nd == prevdir:
                weight *= RIVER_MOMENTUM if run_len < RIVER_RUN else 0.5
            elif prevdir is not None and run_len >= RIVER_RUN:
                weight *= 1.8
            if _near_set(nb, rivers, exclude=ownset):
                weight *= RIVERSIDE_PENALTY
            elif _near_set(nb, rivers, exclude=ownset, reach=2):
                weight *= RIVER_RING2_PENALTY
            if _near_set(nb, ownset, exclude=set(own[-2:])):
                weight *= SELF_SIDE_PENALTY
            cands.append((weight, nd, nb, ndist))
        if merges:
            nd, nb = next(((nd, nb) for nd, nb in merges if nd == prevdir),
                          merges[rng.randrange(len(merges))])
            rivers[cur].add(nd)
            rivers[nb].add(OPPOSITE[nd])
            return len(own)
        if not cands:
            # cannot happen while the field is intact (a d-1 neighbor
            # always exists and is never own); kept as a safe exit
            return len(own)
        total = sum(c[0] for c in cands)
        roll = rng.uniform(0, total)
        for weight, nd, nb, ndist in cands:
            roll -= weight
            if roll <= 0:
                break
        rivers[cur].add(nd)
        rivers[nb] = rivers.get(nb, set())
        rivers[nb].add(OPPOSITE[nd])
        last_was_eq = ndist == d
        if last_was_eq:
            eq_left -= 1
        run_len = run_len + 1 if nd == prevdir else 1
        prevdir = nd
        cur = nb


def _trace_rivers(terrain: list[list[str]],
                  rng: random.Random) -> tuple[dict, int]:
    w, h = len(terrain[0]), len(terrain)
    dist = _sea_distance(terrain)
    land_total = sum(1 for y in range(h) for x in range(w)
                     if terrain[y][x] != OCEAN)
    budget = round(land_total * RIVER_FRAC)
    rivers: dict[tuple[int, int], set] = {}
    failures = 0
    count = 0
    while budget > 0 and failures < 40:
        src = _pick_source(terrain, dist, rivers, rng)
        if src is None:
            break
        added = _trace_river(src, terrain, dist, rivers, rng)
        if added >= 3:
            budget -= added
            count += 1
        else:
            failures += 1
    return rivers, count


# --------------------------------------------------------------------------- #
# Validation (the hard rules a rolled map must pass)
# --------------------------------------------------------------------------- #

LAND_BAND = (0.47, 0.66)         # land share of all tiles
PLAY_LAND_BAND = (0.30, 0.72)    # land share of the playable corner
MOUNTAIN_BAND = (0.05, 0.13)     # mountain share of land
RIVER_BAND = (0.035, 0.10)       # river share of land
CONTINENT_MIN = 0.10             # 2nd continent holds at least this of land
CONTINENTS_HOLD = 0.78           # top three components hold at least this


def validate(world: dict) -> list[str]:
    terrain, rivers = world["terrain"], world["rivers"]
    w, h = world["w"], world["h"]
    bad: list[str] = []
    if any(row[0] != OCEAN for row in terrain):
        bad.append("west edge not all ocean")
    for y in range(h - 1):
        for x in range(w - 1):
            a = terrain[y][x] == OCEAN
            b = terrain[y][x + 1] == OCEAN
            c = terrain[y + 1][x] == OCEAN
            d = terrain[y + 1][x + 1] == OCEAN
            if (a and d and not b and not c) or (b and c and not a
                                                 and not d):
                bad.append(f"diagonal-only ocean contact at {x},{y}")
    for (pos, dirs) in rivers.items():
        x, y = pos
        if terrain[y][x] != LAND:
            bad.append(f"river off plain land at {x},{y}")
        if frozenset(dirs) not in RIVER_GLYPHS:
            bad.append(f"unglyphable river connections at {x},{y}")
        for nd in dirs:
            dx, dy = STEPS[nd]
            nx, ny = x + dx, y + dy
            if not (0 <= nx < w and 0 <= ny < h):
                bad.append(f"river runs off the map at {x},{y}")
            elif (nx, ny) in rivers:
                if OPPOSITE[nd] not in rivers[(nx, ny)]:
                    bad.append(f"one-sided river link at {x},{y}")
            elif terrain[ny][nx] != OCEAN:
                bad.append(f"river arm into dry land at {x},{y}")
    m = measure(world)
    if not LAND_BAND[0] <= m["land_frac"] <= LAND_BAND[1]:
        bad.append(f"land share {m['land_frac']:.2f} outside {LAND_BAND}")
    if not PLAY_LAND_BAND[0] <= m["play_land_frac"] <= PLAY_LAND_BAND[1]:
        bad.append(f"play-corner land {m['play_land_frac']:.2f} "
                   f"outside {PLAY_LAND_BAND}")
    if not MOUNTAIN_BAND[0] <= m["mountain_frac"] <= MOUNTAIN_BAND[1]:
        bad.append(f"mountain share {m['mountain_frac']:.2f} "
                   f"outside {MOUNTAIN_BAND}")
    if not RIVER_BAND[0] <= m["river_frac"] <= RIVER_BAND[1]:
        bad.append(f"river share {m['river_frac']:.2f} outside {RIVER_BAND}")
    sizes = m["continent_sizes"]
    land_total = m["land_tiles"]
    if len(sizes) < 2 or sizes[1] < CONTINENT_MIN * land_total:
        bad.append("no second continent worth the name")
    if sum(sizes[:3]) < CONTINENTS_HOLD * land_total:
        bad.append("continents hold too little of the land")
    if m["small_islands"] > MAX_SMALL_ISLANDS:
        bad.append(f"archipelago: {m['small_islands']} specks")
    return bad


# --------------------------------------------------------------------------- #
# Measurement (stats for the eyeball and the sweep)
# --------------------------------------------------------------------------- #

def measure(world: dict) -> dict:
    terrain, rivers = world["terrain"], world["rivers"]
    w, h = world["w"], world["h"]
    total = w * h
    land_tiles = sum(1 for y in range(h) for x in range(w)
                     if terrain[y][x] != OCEAN)
    mountains = sum(1 for y in range(h) for x in range(w)
                    if terrain[y][x] == MOUNTAIN)
    river_tiles = len(rivers)
    comps = _components(terrain, value_is_land=True)
    sizes = [len(c) for c in comps]
    lakes = [c for c in _components(terrain, value_is_land=False)
             if not any(x in (0, w - 1) or y in (0, h - 1) for x, y in c)]
    pw, ph = min(PLAY_W, w), min(PLAY_H, h)
    play_land = sum(1 for y in range(ph) for x in range(pw)
                    if terrain[y][x] != OCEAN)
    return {
        "land_tiles": land_tiles,
        "land_frac": land_tiles / total,
        "mountain_frac": mountains / land_tiles if land_tiles else 0.0,
        "river_frac": river_tiles / land_tiles if land_tiles else 0.0,
        "river_tiles": river_tiles,
        "river_count": world["river_count"],
        "continent_sizes": sizes,
        "small_islands": sum(1 for s in sizes if s < SMALL_ISLAND),
        "lakes": len(lakes),
        "play_land_frac": play_land / (pw * ph),
    }


def stats_lines(world: dict) -> list[str]:
    m = measure(world)
    continents = [s for s in m["continent_sizes"]
                  if s >= CONTINENT_MIN * m["land_tiles"]]
    held = sum(m["continent_sizes"][:3]) / m["land_tiles"]
    lines = [
        f"seed {world['seed']} attempt {world['attempt']}  "
        f"world {world['w']}x{world['h']}  play {PLAY_W}x{PLAY_H}",
        f"land {m['land_frac']:.2f} (template 0.585)   "
        f"play corner {m['play_land_frac']:.2f}",
        f"mountains {m['mountain_frac']:.3f} of land (template 0.092)",
        f"rivers {m['river_frac']:.3f} of land (template 0.066), "
        f"{m['river_count']} rivers, {m['river_tiles']} tiles",
        f"continents {len(continents)}: "
        f"{', '.join(str(s) for s in continents)} tiles "
        f"(top three hold {held:.2f} of land)",
        f"islands {m['small_islands']} small, lakes/inner seas {m['lakes']}",
    ]
    if world.get("violations"):
        lines.append("UNRESOLVED: " + "; ".join(world["violations"]))
    return lines


# --------------------------------------------------------------------------- #
# The generator
# --------------------------------------------------------------------------- #

def _generate_once(rng: random.Random, w: int, h: int) -> dict:
    elev = _elevation(rng, w, h)
    terrain = _sea_level(elev, w, h)
    _enforce_west(terrain)
    _fix_diagonal_ocean(terrain, elev)
    _prune_islands(terrain)
    _fix_diagonal_ocean(terrain, elev)   # provably a no-op; cheap insurance
    _place_mountains(terrain, elev, rng)
    rivers, river_count = _trace_rivers(terrain, rng)
    return {"w": w, "h": h, "terrain": terrain, "rivers": rivers,
            "river_count": river_count}


def generate(seed: int | None = None, w: int = WORLD_W,
             h: int = WORLD_H) -> dict:
    """Roll a valid world; same seed, same world.

    Tries deterministic sub-attempts of the seed until validation passes.
    If none of ATTEMPTS passes (rare), the last roll is returned with its
    violations recorded under "violations".
    """
    if seed is None:
        seed = random.randrange(2 ** 30)
    world = None
    for attempt in range(ATTEMPTS):
        rng = random.Random(f"worldmap|{seed}|{attempt}")
        world = _generate_once(rng, w, h)
        world["seed"], world["attempt"] = seed, attempt
        world["violations"] = validate(world)
        if not world["violations"]:
            break
    return world


# --------------------------------------------------------------------------- #
# Display
# --------------------------------------------------------------------------- #

def tile_char(world: dict, x: int, y: int) -> str:
    dirs = world["rivers"].get((x, y))
    if dirs:
        return RIVER_GLYPHS[frozenset(dirs)]
    return world["terrain"][y][x]


def render(world: dict, view: str = "full", lift: bool = False) -> str:
    """The map as text. view "full" or "play"; lift separates the playable
    corner from the rest of the full map with a border of spaces."""
    w, h = world["w"], world["h"]
    if view == "play":
        return "\n".join(
            "".join(tile_char(world, x, y) for x in range(min(PLAY_W, w)))
            for y in range(min(PLAY_H, h)))
    lines = ["".join(tile_char(world, x, y) for x in range(w))
             for y in range(h)]
    if lift and w > PLAY_W and h > PLAY_H:
        lines = [line[:PLAY_W] + "  " + line[PLAY_W:] for line in lines]
        lines.insert(PLAY_H, "")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# The reference map, measured
# --------------------------------------------------------------------------- #

def template_stats() -> list[str]:
    rows = TEMPLATE.splitlines()
    w, h = len(rows[0]), len(rows)
    total = w * h
    water = sum(row.count(OCEAN) for row in rows)
    land = total - water
    mountains = sum(row.count(MOUNTAIN) for row in rows)
    river = sum(row.count("~") for row in rows)
    grid = [list(row) for row in rows]
    comps = _components(grid, value_is_land=True)
    diag = 0
    for y in range(h - 1):
        for x in range(w - 1):
            a, b = rows[y][x] == OCEAN, rows[y][x + 1] == OCEAN
            c, d = rows[y + 1][x] == OCEAN, rows[y + 1][x + 1] == OCEAN
            if (a and d and not b and not c) or (b and c and not a
                                                 and not d):
                diag += 1
    return [
        f"the reference map: {w}x{h}, {total} tiles",
        f"land {land / total:.3f}, water {water / total:.3f}",
        f"mountains {mountains / land:.3f} of land",
        f"rivers {river / land:.3f} of land",
        f"diagonal-only ocean contacts: {diag}",
        f"land components: {', '.join(str(len(c)) for c in comps)}",
    ]


# --------------------------------------------------------------------------- #
# Demo (the designer's eyeball check)
# --------------------------------------------------------------------------- #

def _parse_size(text: str) -> tuple[int, int]:
    w, _, h = text.lower().partition("x")
    w, h = int(w), int(h)
    if w < PLAY_W or h < PLAY_H:
        raise argparse.ArgumentTypeError(
            f"world must contain the {PLAY_W}x{PLAY_H} playable corner")
    return w, h


def main() -> None:
    # the one module whose output is not ASCII (the river glyphs): make
    # sure a cp1250 console or pipe does not choke on them
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--size", type=_parse_size, default=(WORLD_W, WORLD_H),
                    help="world size WxH (default 80x40; 60x30 supported)")
    ap.add_argument("--play", action="store_true",
                    help="print only the playable northwest corner")
    ap.add_argument("--lift", action="store_true",
                    help="separate the playable corner with a space border")
    ap.add_argument("--count", type=int, default=1,
                    help="roll several consecutive seeds")
    ap.add_argument("--check", type=int, default=0, metavar="N",
                    help="no maps: constraint pass-rate over N seeds")
    ap.add_argument("--template-stats", action="store_true",
                    help="measure the embedded reference map and exit")
    args = ap.parse_args()

    if args.template_stats:
        print(TEMPLATE)
        for line in template_stats():
            print(line)
        return

    w, h = args.size
    seed = args.seed if args.seed is not None else random.randrange(10 ** 6)

    if args.check:
        attempts = []
        unresolved = 0
        for s in range(seed, seed + args.check):
            world = generate(s, w, h)
            attempts.append(world["attempt"] + 1)
            if world["violations"]:
                unresolved += 1
                print(f"seed {s}: UNRESOLVED after {ATTEMPTS}: "
                      + "; ".join(world["violations"][:3]))
        first = sum(1 for a in attempts if a == 1)
        print(f"{args.check} seeds from {seed}: "
              f"{first} first-roll, "
              f"mean {sum(attempts) / len(attempts):.2f} rolls, "
              f"max {max(attempts)}, unresolved {unresolved}")
        return

    for s in range(seed, seed + args.count):
        world = generate(s, w, h)
        view = "play" if args.play else "full"
        print(render(world, view=view, lift=args.lift))
        for line in stats_lines(world):
            print(line)
        if args.count > 1:
            print()


if __name__ == "__main__":
    main()
