"""Verification for the world-map generator's geography contract.

The rules under test are rules.md's The World Map add-on: the west edge,
the diagonal-ocean rule, the river glyph grammar, the continent shape of
the world, and the calibration against the embedded reference map. The
generator is standalone and unwired; these are generation contracts, not
play contracts.
"""

from __future__ import annotations

import itertools
import unittest

import worldmap
from worldmap import LAND, MOUNTAIN, OCEAN, OPPOSITE, RIVER_GLYPHS, STEPS


SEEDS = (1, 5, 11)          # a few fixed worlds, rolled once for the suite


class WorldMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.worlds = [worldmap.generate(s) for s in SEEDS]
        cls.worlds.append(worldmap.generate(3, 60, 30))

    def test_deterministic(self) -> None:
        again = worldmap.generate(SEEDS[0])
        self.assertEqual(worldmap.render(again),
                         worldmap.render(self.worlds[0]))
        self.assertEqual(again["attempt"], self.worlds[0]["attempt"])

    def test_all_rolled_worlds_valid(self) -> None:
        for world in self.worlds:
            self.assertEqual(world["violations"], [])
            self.assertEqual(worldmap.validate(world), [])

    def test_west_edge_all_ocean(self) -> None:
        for world in self.worlds:
            for row in world["terrain"]:
                self.assertEqual(row[0], OCEAN)

    def test_no_diagonal_only_ocean(self) -> None:
        for world in self.worlds:
            t, w, h = world["terrain"], world["w"], world["h"]
            for y in range(h - 1):
                for x in range(w - 1):
                    a = t[y][x] == OCEAN
                    b = t[y][x + 1] == OCEAN
                    c = t[y + 1][x] == OCEAN
                    d = t[y + 1][x + 1] == OCEAN
                    self.assertFalse(a and d and not b and not c,
                                     f"checkerboard at {x},{y}")
                    self.assertFalse(b and c and not a and not d,
                                     f"checkerboard at {x},{y}")

    def test_river_glyph_grammar(self) -> None:
        # every non-empty subset of NSEW has a glyph, so no connection set
        # a trace can build is unprintable
        for n in range(1, 5):
            for combo in itertools.combinations("NSEW", n):
                self.assertIn(frozenset(combo), RIVER_GLYPHS)

    def test_river_links_reciprocal_and_on_land(self) -> None:
        for world in self.worlds:
            rivers, t = world["rivers"], world["terrain"]
            for pos, dirs in rivers.items():
                x, y = pos
                self.assertEqual(t[y][x], LAND)     # never ocean, never ^
                self.assertTrue(dirs)
                for nd in dirs:
                    dx, dy = STEPS[nd]
                    nb = (x + dx, y + dy)
                    if nb in rivers:
                        self.assertIn(OPPOSITE[nd], rivers[nb])
                    else:                           # a mouth arm
                        self.assertEqual(t[nb[1]][nb[0]], OCEAN)

    def test_every_river_reaches_water(self) -> None:
        # each river system, followed as a component, touches a mouth arm
        for world in self.worlds:
            rivers = world["rivers"]
            seen: set[tuple[int, int]] = set()
            for start in rivers:
                if start in seen:
                    continue
                comp, stack, mouths = [], [start], 0
                seen.add(start)
                while stack:
                    pos = stack.pop()
                    comp.append(pos)
                    for nd in rivers[pos]:
                        dx, dy = STEPS[nd]
                        nb = (pos[0] + dx, pos[1] + dy)
                        if nb in rivers:
                            if nb not in seen:
                                seen.add(nb)
                                stack.append(nb)
                        else:
                            mouths += 1
                self.assertGreaterEqual(mouths, 1, "a river with no mouth")
                self.assertGreaterEqual(len(comp), 3, "a stub river")

    def test_continent_shape(self) -> None:
        for world in self.worlds:
            m = worldmap.measure(world)
            sizes = m["continent_sizes"]
            self.assertGreaterEqual(len(sizes), 2)
            self.assertGreaterEqual(sizes[1], 0.10 * m["land_tiles"])
            self.assertGreaterEqual(sum(sizes[:3]),
                                    0.78 * m["land_tiles"])

    def test_ratio_bands(self) -> None:
        for world in self.worlds:
            m = worldmap.measure(world)
            self.assertTrue(0.47 <= m["land_frac"] <= 0.66)
            self.assertTrue(0.05 <= m["mountain_frac"] <= 0.13)
            self.assertTrue(0.035 <= m["river_frac"] <= 0.10)
            self.assertTrue(0.30 <= m["play_land_frac"] <= 0.72)

    def test_render_shapes(self) -> None:
        world = self.worlds[0]
        full = worldmap.render(world).splitlines()
        self.assertEqual(len(full), world["h"])
        self.assertTrue(all(len(line) == world["w"] for line in full))
        play = worldmap.render(world, view="play").splitlines()
        self.assertEqual(len(play), worldmap.PLAY_H)
        self.assertTrue(all(len(line) == worldmap.PLAY_W for line in play))
        # the playable corner is the northwest corner of the full map,
        # tile for tile
        for y, line in enumerate(play):
            self.assertEqual(line, full[y][:worldmap.PLAY_W])
        lifted = worldmap.render(world, lift=True).splitlines()
        self.assertEqual(len(lifted), world["h"] + 1)
        self.assertEqual(lifted[worldmap.PLAY_H], "")
        self.assertTrue(all(line[worldmap.PLAY_W:worldmap.PLAY_W + 2] == "  "
                            for line in lifted if line))

    def test_template_measurements(self) -> None:
        # the calibration source: if the embedded reference map is ever
        # edited, the targets in the module head must be re-derived
        rows = worldmap.TEMPLATE.splitlines()
        self.assertEqual((len(rows[0]), len(rows)), (30, 18))
        total = sum(len(r) for r in rows)
        water = sum(r.count(OCEAN) for r in rows)
        land = total - water
        mountains = sum(r.count(MOUNTAIN) for r in rows)
        rivers = sum(r.count("~") for r in rows)
        self.assertAlmostEqual(land / total, 0.585, places=3)
        self.assertAlmostEqual(mountains / land, 0.092, places=3)
        self.assertAlmostEqual(rivers / land, 0.066, places=3)


if __name__ == "__main__":
    unittest.main()
