#!/usr/bin/env python3
"""
mapgen.py -- fractal ASCII world-map generator for a 30 km/tile strategy game.

Scale: one tile = 30 km east-west, 60 km north-south (a tile is twice as
tall as it is wide in world space; noise is sampled anisotropically so
landforms come out isotropic in kilometres).

Tiles:
    '.'  open water (ocean / sea)
    '#'  land
    '^'  mountain (on land)
    box-drawing chars  major river on a land tile

Hard rules enforced:
    * westernmost column is always water (organic coast, not a straight cut)
    * no two water tiles that touch only diagonally  ( .# / #. )
    * every water body connects to the border ocean (straits are carved)
    * rivers are 4-connected paths from highlands to the sea, drawn with
      box-drawing characters, never touching themselves or each other
    * land ratio of the playable NW corner matches the template (~0.58)

Usage:
    python mapgen.py [seed]        # prints full (lifted) + playable views
"""

import heapq
import math
import random

WATER = '.'
LAND = '#'
MOUNTAIN = '^'
RIVER_CHARS = {
    frozenset('NS'): '\u2502',  # |
    frozenset('EW'): '\u2500',  # -
    frozenset('NE'): '\u2514',  # L
    frozenset('NW'): '\u2518',
    frozenset('SE'): '\u250c',
    frozenset('SW'): '\u2510',
    frozenset('N'): '\u2502',
    frozenset('S'): '\u2502',
    frozenset('E'): '\u2500',
    frozenset('W'): '\u2500',
}
RIVER_SET = set(RIVER_CHARS.values())
DIR_NAME = {(0, -1): 'N', (0, 1): 'S', (1, 0): 'E', (-1, 0): 'W'}


# ---------------------------------------------------------------- noise ----

def _mix(n):
    n &= 0xFFFFFFFF
    n ^= n >> 15
    n = (n * 0x2C1B3C6D) & 0xFFFFFFFF
    n ^= n >> 12
    n = (n * 0x297A2D39) & 0xFFFFFFFF
    n ^= n >> 15
    return n


class Noise:
    """Seeded value noise + fBm + ridged fBm. Pure stdlib, ports 1:1 to JS."""

    def __init__(self, seed):
        self.seed = seed & 0xFFFFFFFF

    def h(self, ix, iy, k):
        n = ((ix & 0xFFFFFFFF) * 0x27D4EB2D) & 0xFFFFFFFF
        n ^= ((iy & 0xFFFFFFFF) * 0x165667B1) & 0xFFFFFFFF
        n ^= ((k & 0xFFFFFFFF) * 0x9E3779B9) & 0xFFFFFFFF
        n ^= self.seed
        return _mix(n) / 4294967296.0

    def value(self, x, y, k):
        x0 = math.floor(x)
        y0 = math.floor(y)
        fx = x - x0
        fy = y - y0
        u = fx * fx * fx * (fx * (fx * 6.0 - 15.0) + 10.0)
        v = fy * fy * fy * (fy * (fy * 6.0 - 15.0) + 10.0)
        a = self.h(x0, y0, k)
        b = self.h(x0 + 1, y0, k)
        c = self.h(x0, y0 + 1, k)
        d = self.h(x0 + 1, y0 + 1, k)
        return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v

    def fbm(self, x, y, k, octaves=4, freq=1.0, lac=2.0, gain=0.5):
        amp, tot, norm, f = 1.0, 0.0, 0.0, freq
        for o in range(octaves):
            tot += amp * self.value(x * f, y * f, k * 31 + o)
            norm += amp
            amp *= gain
            f *= lac
        return tot / norm

    def ridged(self, x, y, k, octaves=3, freq=1.0):
        amp, tot, norm, f = 1.0, 0.0, 0.0, freq
        for o in range(octaves):
            n = self.value(x * f, y * f, k * 57 + o)
            r = 1.0 - abs(2.0 * n - 1.0)
            tot += amp * r * r
            norm += amp
            amp *= 0.5
            f *= 2.0
        return tot / norm


# ---------------------------------------------------------- helper bits ----

def nb4(x, y, W, H):
    if x > 0:
        yield x - 1, y
    if x < W - 1:
        yield x + 1, y
    if y > 0:
        yield x, y - 1
    if y < H - 1:
        yield x, y + 1


# ------------------------------------------------------------ elevation ----

def build_elevation(seed, W, H, PW, PH):
    """Domain-warped fBm on top of 2-3 lobed continent masks."""
    nz = Noise(seed)
    rng = random.Random(seed ^ 0x5F3759)
    WU, HU = W * 1.0, H * 2.0          # world units, 30 km each

    n_cont = rng.choice((2, 3, 3))
    anchors = []
    # anchor 0: the homeland, guaranteed inside the playable NW corner
    anchors.append({
        'cu': rng.uniform(0.38, 0.75) * PW,
        'cv': rng.uniform(0.30, 0.75) * PH * 2.0,
        'R': rng.uniform(0.24, 0.32) * WU,
        'theta': rng.uniform(0.0, math.pi),
        'ar': rng.uniform(0.75, 1.35),
    })
    min_sep = 0.42 * WU
    tries = 0
    while len(anchors) < n_cont and tries < 400:
        tries += 1
        c = {
            'cu': rng.uniform(0.22, 0.94) * WU,
            'cv': rng.uniform(0.08, 0.92) * HU,
            'R': rng.uniform(0.20, 0.30) * WU,
            'theta': rng.uniform(0.0, math.pi),
            'ar': rng.uniform(0.75, 1.35),
        }
        if all(math.hypot(c['cu'] - a['cu'], c['cv'] - a['cv']) >= min_sep
               for a in anchors):
            anchors.append(c)
        if tries % 120 == 0:
            min_sep *= 0.9

    warp_amp = 24.0
    elev = [[0.0] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            u = x + 0.5
            v = 2.0 * (y + 0.5)
            qx = nz.fbm(u * 0.045, v * 0.045, 11, octaves=3) - 0.5
            qy = nz.fbm(u * 0.045, v * 0.045, 12, octaves=3) - 0.5
            wu = u + warp_amp * qx
            wv = v + warp_amp * qy
            mask = 0.0
            for i, a in enumerate(anchors):
                du = wu - a['cu']
                dv = wv - a['cv']
                ct = math.cos(a['theta'])
                st = math.sin(a['theta'])
                ru = du * ct + dv * st
                rv = -du * st + dv * ct
                dist = math.hypot(ru / a['ar'], rv * a['ar'])
                ang = math.atan2(dv, du)
                lobe = nz.fbm(math.cos(ang) * 1.5 + 9.7 * i,
                              math.sin(ang) * 1.5 + 4.3 * i,
                              800 + i, octaves=3)
                reff = a['R'] * (0.60 + 0.85 * lobe)
                m = 1.0 - dist / reff
                if m > mask:
                    mask = m
            mask = max(0.0, min(1.0, mask))
            detail = nz.fbm(wu * 0.065, wv * 0.065, 13, octaves=4)
            e = mask * 0.9 + (detail - 0.5) * 0.9
            if u < 7.0:                     # western open-ocean falloff
                t = (7.0 - u) / 7.0
                e -= 1.8 * t * t
            elev[y][x] = e
    return elev


def corner_threshold(elev, PW, PH, target):
    vals = sorted(elev[y][x] for y in range(PH) for x in range(PW))
    idx = int(round((1.0 - target) * len(vals)))
    idx = min(len(vals) - 1, max(0, idx))
    return vals[idx]


# --------------------------------------------------------- post-process ----

def fix_diagonals(land, elev, W, H):
    """No water pair may touch only diagonally: sink the lower land tile."""
    changed = True
    while changed:
        changed = False
        for y in range(H - 1):
            for x in range(W - 1):
                a = land[y][x]
                b = land[y][x + 1]
                c = land[y + 1][x]
                d = land[y + 1][x + 1]
                if (not a) and (not d) and b and c:
                    if elev[y][x + 1] <= elev[y + 1][x]:
                        land[y][x + 1] = False
                    else:
                        land[y + 1][x] = False
                    changed = True
                elif (not b) and (not c) and a and d:
                    if elev[y][x] <= elev[y + 1][x + 1]:
                        land[y][x] = False
                    else:
                        land[y + 1][x + 1] = False
                    changed = True


def components(grid_pred, W, H):
    """4-connected components of tiles where grid_pred(x, y) is true."""
    seen = [[False] * W for _ in range(H)]
    comps = []
    for y in range(H):
        for x in range(W):
            if seen[y][x] or not grid_pred(x, y):
                continue
            comp = []
            stack = [(x, y)]
            seen[y][x] = True
            while stack:
                cx, cy = stack.pop()
                comp.append((cx, cy))
                for nx, ny in nb4(cx, cy, W, H):
                    if not seen[ny][nx] and grid_pred(nx, ny):
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            comps.append(comp)
    return comps


def carve_to_ocean(land, elev, sea, region, main_set, W, H):
    """Dijkstra a lowest-terrain strait from an inland sea to the ocean."""
    dist = {}
    prev = {}
    pq = []
    for p in region:
        dist[p] = 0.0
        heapq.heappush(pq, (0.0, p[0], p[1]))
    while pq:
        d, x, y = heapq.heappop(pq)
        if d > dist.get((x, y), 1e18) + 1e-12:
            continue
        if (x, y) in main_set:
            cur = (x, y)
            while cur in prev:
                cur = prev[cur]
                if land[cur[1]][cur[0]]:
                    land[cur[1]][cur[0]] = False
            return True
        for nx, ny in nb4(x, y, W, H):
            if land[ny][nx]:
                c = 1.0 + 5.0 * max(0.0, elev[ny][nx] - sea)
            else:
                c = 0.2
            nd = d + c
            if nd < dist.get((nx, ny), 1e18) - 1e-12:
                dist[(nx, ny)] = nd
                prev[(nx, ny)] = (x, y)
                heapq.heappush(pq, (nd, nx, ny))
    return False


def enforce_ocean(land, elev, sea, W, H):
    """All water joins one ocean; tiny lakes become land, seas get straits."""
    fix_diagonals(land, elev, W, H)
    for _ in range(12):
        comps = components(lambda x, y: not land[y][x], W, H)
        main = None
        for c in comps:
            if any(p[0] == 0 for p in c):
                main = c
                break
        if main is None:
            main = max(comps, key=len)
        others = [c for c in comps if c is not main]
        if not others:
            return
        main_set = set(main)
        for c in others:
            if len(c) <= 3:
                for (x, y) in c:
                    land[y][x] = True
            else:
                if not carve_to_ocean(land, elev, sea, c, main_set, W, H):
                    for (x, y) in c:
                        land[y][x] = True
        fix_diagonals(land, elev, W, H)


# ------------------------------------------------------------- features ----

def place_mountains(land, elev, sea, seed, W, H):
    nz = Noise((seed ^ 0xA5A5A5) & 0xFFFFFFFF)
    scores = []
    for y in range(H):
        for x in range(W):
            if not land[y][x]:
                continue
            u = x + 0.5
            v = 2.0 * (y + 0.5)
            r = nz.ridged(u * 0.15, v * 0.15, 21)
            s = (r * r * r * 2.4
                 + 0.30 * max(0.0, elev[y][x] - sea)
                 + 0.06 * nz.h(x, y, 99))
            scores.append((s, x, y))
    scores.sort(reverse=True)
    target = int(round(0.085 * len(scores)))
    return {(x, y) for _, x, y in scores[:target]}


def _river_path_ok(path, river_tiles):
    """A river may not touch itself or another river, except consecutively."""
    pset = {p: i for i, p in enumerate(path)}
    for i, (x, y) in enumerate(path):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                q = (x + dx, y + dy)
                if q in river_tiles:
                    return False
                j = pset.get(q)
                if j is not None and abs(i - j) >= 2:
                    return False
    return True


def place_rivers(land, elev, sea, mts, seed, W, H):
    rng = random.Random(seed ^ 0x1234)
    nz = Noise((seed ^ 0x77) & 0xFFFFFFFF)
    land_tiles = [(x, y) for y in range(H) for x in range(W) if land[y][x]]
    n_land = len(land_tiles)
    n_target = max(3, min(18, int(round(n_land / 85.0))))

    def near_water(x, y, r):
        for ny in range(max(0, y - r), min(H, y + r + 1)):
            for nx in range(max(0, x - r), min(W, x + r + 1)):
                if not land[ny][nx]:
                    return True
        return False

    def near_mt(x, y):
        for ny in range(max(0, y - 2), min(H, y + 3)):
            for nx in range(max(0, x - 2), min(W, x + 3)):
                if (nx, ny) in mts:
                    return True
        return False

    hi = sorted(elev[y][x] for x, y in land_tiles)[int(0.8 * n_land)]
    cands = []
    for (x, y) in land_tiles:
        if (x, y) in mts or near_water(x, y, 2):
            continue
        if near_mt(x, y) or elev[y][x] >= hi:
            cands.append((elev[y][x] + rng.uniform(0, 0.15), x, y))
    cands.sort(reverse=True)

    river_tiles = {}          # (x,y) -> box char
    near1 = set()             # Chebyshev-1 halo: excluded outright
    near2 = set()             # Chebyshev-2 ring: soft repulsion
    springs = []
    n_rivers = 0

    def coast_adj(x, y):
        return any(not land[ny][nx] for nx, ny in nb4(x, y, W, H))

    for _, sx, sy in cands:
        if n_rivers >= n_target:
            break
        if any(max(abs(sx - qx), abs(sy - qy)) < 6 for qx, qy in springs):
            continue
        if (sx, sy) in river_tiles:
            continue
        # Dijkstra downhill-ish to the nearest sea
        dist = {(sx, sy): 0.0}
        prev = {}
        pq = [(0.0, sx, sy)]
        goal = None
        while pq:
            d, x, y = heapq.heappop(pq)
            if d > dist.get((x, y), 1e18) + 1e-12:
                continue
            if not land[y][x]:
                goal = (x, y)
                break
            for nx, ny in nb4(x, y, W, H):
                if land[ny][nx]:
                    if (nx, ny) in mts or (nx, ny) in near1:
                        continue
                    c = (1.0
                         + 9.0 * max(0.0, elev[ny][nx] - elev[y][x])
                         + (2.6 if coast_adj(nx, ny) else 0.0)
                         + (1.4 if (nx, ny) in near2 else 0.0)
                         + 2.6 * nz.h(nx, ny, 7))
                else:
                    c = 0.1
                nd = d + c
                if nd < dist.get((nx, ny), 1e18) - 1e-12:
                    dist[(nx, ny)] = nd
                    prev[(nx, ny)] = (x, y)
                    heapq.heappush(pq, (nd, nx, ny))
        if goal is None:
            continue
        # reconstruct: land tiles from spring to mouth, plus the sea tile
        path = []
        cur = prev.get(goal)
        sea_tile = goal
        while cur is not None:
            path.append(cur)
            cur = prev.get(cur)
        path.reverse()                       # spring ... mouth
        if len(path) < 4 or len(path) > 18:
            continue
        if not _river_path_ok(path, river_tiles):
            continue
        mouth_dir = (sea_tile[0] - path[-1][0], sea_tile[1] - path[-1][1])
        for i, p in enumerate(path):
            dirs = set()
            if i > 0:
                q = path[i - 1]
                dirs.add(DIR_NAME[(q[0] - p[0], q[1] - p[1])])
            if i < len(path) - 1:
                q = path[i + 1]
                dirs.add(DIR_NAME[(q[0] - p[0], q[1] - p[1])])
            else:
                dirs.add(DIR_NAME[mouth_dir])
            river_tiles[p] = RIVER_CHARS[frozenset(dirs)]
        for (px, py) in path:
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    q = (px + dx, py + dy)
                    if max(abs(dx), abs(dy)) <= 1:
                        near1.add(q)
                    else:
                        near2.add(q)
        springs.append((sx, sy))
        n_rivers += 1
    return river_tiles, n_rivers


# ------------------------------------------------- interestingness pass ----

def bfs_dist(sources, W, H):
    INF = 10 ** 9
    dist = [[INF] * W for _ in range(H)]
    q = []
    for (x, y) in sources:
        dist[y][x] = 0
        q.append((x, y))
    head = 0
    while head < len(q):
        x, y = q[head]
        head += 1
        for nx, ny in nb4(x, y, W, H):
            if dist[ny][nx] > dist[y][x] + 1:
                dist[ny][nx] = dist[y][x] + 1
                q.append((nx, ny))
    return dist


def _island_placement_ok(land, x, y, W, H):
    """Would turning (x,y) into land create a diagonal-only water pair?"""
    for bx in (x - 1, x):
        for by in (y - 1, y):
            if bx < 0 or by < 0 or bx + 1 >= W or by + 1 >= H:
                continue
            cells = [(bx, by), (bx + 1, by), (bx, by + 1), (bx + 1, by + 1)]
            vals = [land[cy][cx] or (cx, cy) == (x, y) for cx, cy in cells]
            if vals[0] and vals[3] and not vals[1] and not vals[2]:
                return False
            if vals[1] and vals[2] and not vals[0] and not vals[3]:
                return False
    return True


def fix_boring(land, elev, sea, mts, river_tiles, seed, W, H):
    """No large featureless plain, no large empty sea: seed hills / islands."""
    rng = random.Random(seed ^ 0xBEEF)
    added_isl = []
    # --- empty ocean -> small islands
    for _ in range(12):
        land_src = [(x, y) for y in range(H) for x in range(W) if land[y][x]]
        d = bfs_dist(land_src, W, H)
        far = [(d[y][x], elev[y][x], x, y) for y in range(H) for x in range(W)
               if not land[y][x] and d[y][x] > 6 and x >= 2]
        if not far:
            break
        far.sort(reverse=True)
        _, _, ix, iy = far[0]
        if not _island_placement_ok(land, ix, iy, W, H):
            placed = False
            for nx, ny in nb4(ix, iy, W, H):
                if not land[ny][nx] and nx >= 2 and \
                        _island_placement_ok(land, nx, ny, W, H):
                    ix, iy = nx, ny
                    placed = True
                    break
            if not placed:
                break
        land[iy][ix] = True
        added_isl.append((ix, iy))
        # small chance of a 2-3 tile island
        for nx, ny in nb4(ix, iy, W, H):
            if rng.random() < 0.45 and not land[ny][nx] and nx >= 2 and \
                    _island_placement_ok(land, nx, ny, W, H):
                land[ny][nx] = True
                added_isl.append((nx, ny))
    # --- featureless plains -> lone hills / small ranges
    for _ in range(6):
        feats = [(x, y) for y in range(H) for x in range(W)
                 if (not land[y][x]) or (x, y) in mts or (x, y) in river_tiles]
        d = bfs_dist(feats, W, H)
        best = None
        for y in range(H):
            for x in range(W):
                if land[y][x] and d[y][x] > 4:
                    if best is None or d[y][x] > best[0]:
                        best = (d[y][x], x, y)
        if best is None:
            break
        _, mx, my = best
        mts.add((mx, my))
        if rng.random() < 0.6:
            opts = [(nx, ny) for nx, ny in nb4(mx, my, W, H)
                    if land[ny][nx] and (nx, ny) not in river_tiles]
            if opts:
                mts.add(rng.choice(opts))
    return added_isl


# ------------------------------------------------------------- pipeline ----

def _compose(land, mts, river_tiles, W, H):
    tiles = []
    for y in range(H):
        row = []
        for x in range(W):
            if not land[y][x]:
                row.append(WATER)
            elif (x, y) in river_tiles:
                row.append(river_tiles[(x, y)])
            elif (x, y) in mts:
                row.append(MOUNTAIN)
            else:
                row.append(LAND)
        tiles.append(row)
    return tiles


def _stats(land, mts, river_tiles, n_rivers, W, H, PW, PH):
    n_land = sum(land[y][x] for y in range(H) for x in range(W))
    n_corner = sum(land[y][x] for y in range(PH) for x in range(PW))
    comps = components(lambda x, y: land[y][x], W, H)
    sizes = sorted((len(c) for c in comps), reverse=True)
    majors = [s for s in sizes if s >= 0.10 * max(1, n_land)]
    coast = sum(1 for y in range(H) for x in range(W) if land[y][x]
                and any(not land[ny][nx] for nx, ny in nb4(x, y, W, H)))
    feats = [(x, y) for y in range(H) for x in range(W)
             if (not land[y][x]) or (x, y) in mts or (x, y) in river_tiles]
    d = bfs_dist(feats, W, H)
    worst_plain = max((d[y][x] for y in range(H) for x in range(W)
                       if land[y][x]), default=0)
    land_src = [(x, y) for y in range(H) for x in range(W) if land[y][x]]
    ds = bfs_dist(land_src, W, H)
    worst_sea = max((ds[y][x] for y in range(H) for x in range(W)
                     if not land[y][x]), default=0)
    return {
        'full_land': n_land / (W * H),
        'corner_land': n_corner / (PW * PH),
        'n_land': n_land,
        'n_mts': len(mts),
        'mt_frac': len(mts) / max(1, n_land),
        'n_rivers': n_rivers,
        'river_tiles': len(river_tiles),
        'n_major': len(majors),
        'largest_share': (sizes[0] / max(1, n_land)) if sizes else 0.0,
        'n_islands': sum(1 for s in sizes if s <= 20),
        'comp_sizes': sizes[:6],
        'coast_frac': coast / max(1, n_land),
        'worst_plain': worst_plain,
        'worst_sea': worst_sea,
    }


def _penalty(st):
    p = 0.0
    cr = st['corner_land']
    if cr < 0.50:
        p += (0.50 - cr) * 40
    if cr > 0.68:
        p += (cr - 0.68) * 40
    fr = st['full_land']
    if fr < 0.28:
        p += (0.28 - fr) * 20
    if fr > 0.64:
        p += (fr - 0.64) * 20
    if st['n_major'] < 2:
        p += 4
    if st['n_major'] > 3:
        p += 2 * (st['n_major'] - 3)
    if st['largest_share'] > 0.85:
        p += 3
    if st['n_rivers'] < 3:
        p += 2
    if st['coast_frac'] < 0.24:
        p += (0.24 - st['coast_frac']) * 10
    return p


def validate(land, W, H):
    assert all(not land[y][0] for y in range(H)), 'west edge not water'
    for y in range(H - 1):
        for x in range(W - 1):
            a, b = land[y][x], land[y][x + 1]
            c, d = land[y + 1][x], land[y + 1][x + 1]
            assert not ((not a) and (not d) and b and c), 'diag water A'
            assert not ((not b) and (not c) and a and d), 'diag water B'
    water_comps = components(lambda x, y: not land[y][x], W, H)
    assert len(water_comps) == 1, 'disconnected water'


def generate(seed, W=80, H=40, PW=40, PH=20, attempts=8, target=0.58):
    best = None
    for att in range(attempts):
        aseed = (seed * 2654435761 + att * 977) & 0xFFFFFFFF
        elev = build_elevation(aseed, W, H, PW, PH)
        sea = corner_threshold(elev, PW, PH, target)
        land = [[elev[y][x] > sea for x in range(W)] for y in range(H)]
        for y in range(H):
            land[y][0] = False
        enforce_ocean(land, elev, sea, W, H)
        mts = place_mountains(land, elev, sea, aseed, W, H)
        river_tiles, n_rivers = place_rivers(land, elev, sea, mts, aseed, W, H)
        fix_boring(land, elev, sea, mts, river_tiles, aseed, W, H)
        validate(land, W, H)
        st = _stats(land, mts, river_tiles, n_rivers, W, H, PW, PH)
        pen = _penalty(st)
        m = {'tiles': _compose(land, mts, river_tiles, W, H),
             'W': W, 'H': H, 'PW': PW, 'PH': PH,
             'seed': seed, 'attempt': att, 'stats': st, 'penalty': pen}
        if best is None or pen < best['penalty']:
            best = m
        if pen == 0.0:
            break
    return best


# -------------------------------------------------------------- display ----

def render(m, view='full', lift=False):
    g = m['tiles']
    PW, PH = m['PW'], m['PH']
    if view == 'play':
        return '\n'.join(''.join(row[:PW]) for row in g[:PH])
    out = []
    for y, row in enumerate(g):
        s = ''.join(row)
        if lift:
            s = s[:PW] + '  ' + s[PW:]
        out.append(s)
        if lift and y == PH - 1:
            out.append('')
    return '\n'.join(out)


def describe(m):
    st = m['stats']
    return (f"seed={m['seed']} attempt={m['attempt']} pen={m['penalty']:.2f} | "
            f"land full={st['full_land']:.2f} corner={st['corner_land']:.2f} | "
            f"mts={st['n_mts']} ({st['mt_frac']:.2f} of land) | "
            f"rivers={st['n_rivers']} ({st['river_tiles']} tiles) | "
            f"majors={st['n_major']} sizes={st['comp_sizes']} | "
            f"coast={st['coast_frac']:.2f} plain<={st['worst_plain']} "
            f"sea<={st['worst_sea']}")


if __name__ == '__main__':
    import sys
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else random.randrange(1 << 32)
    m = generate(seed)
    print(describe(m))
    print()
    print(render(m, view='full', lift=True))
    print()
    print('--- playable 40x20 ---')
    print(render(m, view='play'))
