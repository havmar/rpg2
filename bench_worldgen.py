"""Worldgen benchmark: the tile economy arc's three rolled layers, measured
over real worlds.

This is the arc's own safety net and it replaces econmap.py's `--sweep`
commands (2026-08-21, session 4).  The difference is the whole point: the
tool used to sweep a private simulation with a plain seeded rng and no
start tile, so its numbers were *like* the game's.  Every world here comes
out of `places.create_geography`, so the numbers ARE the game's -- derived
seeds, the nearby-trouble nudge, the authored answer keys and all.

Three sweeps, in the order the arc built them:

  HARVEST   problem coverage, region count and size, the cause mix, the
            drought guarantee, and how often the campaign opens within
            five days of trouble (the nudge's whole purpose, and the one
            number econmap could never measure).
  CENSUS    settlements per tier, slots per land tile, empty tiles, the
            fiction-anchored soul totals, and the quiet-rich share.
  TRADE     routes after merging, land tiles on a road, ports, sea-lane
            tiles, crossroads, and the unfed mines.

Run:  python bench_worldgen.py [--seeds N] [--only harvest|census|trade]

100 seeds is the default and takes about fifteen seconds.  The arc's PINS
were measured at 500; re-measure with `--seeds 500` after touching any
constant in places.py's rolled half, and append the result to benchlog.md.
The layers are deterministic per seed, so this bench -- unlike two of the
five calibration benches -- can be compared against itself.
"""

import argparse
import time
from collections import Counter

import places


def worlds(seeds: int):
    for seed in range(seeds):
        yield seed, places.create_geography(seed)


def _land(world: dict):
    return [world["tiles"][tid] for tid in world["tile_order"]
            if world["tiles"][tid]["biome"] != "sea"]


def _stat(name: str, values, fmt: str = ".1f", scale: float = 1.0) -> None:
    values = list(values)
    mean = sum(values) / len(values)
    print(f"  {name:<34} mean {mean * scale:{fmt}} "
          f"(min {min(values) * scale:{fmt}}, "
          f"max {max(values) * scale:{fmt}})")


def sweep_harvest(seeds: int) -> None:
    print(f"\n--- THE LAST HARVEST ({seeds} worlds) ---")
    coverage, regions, sizes, near = [], [], [], []
    causes: Counter = Counter()
    words: Counter = Counter()
    droughtless = 0
    for _seed, world in worlds(seeds):
        land = _land(world)
        coverage.append(sum(1 for tile in land
                            if tile["harvest"] < places.HARVEST_PROBLEM)
                        / len(land))
        rolled = world["harvest_regions"]
        regions.append(len(rolled))
        sizes += [len(region["tiles"]) for region in rolled]
        causes.update(region["cause"] for region in rolled)
        droughtless += not any(region["cause"] == "drought"
                               for region in rolled)
        start = world["party_tile"]
        near.append(min(places.path_days(start, region["center"])
                        for region in rolled) <= places.TROUBLE_DAYS)
        words.update(places.harvest_word(tile["harvest"]) for tile in land)
    _stat("problem coverage (% of land)", coverage, ".1f", 100)
    _stat("regions a world", regions, ".1f")
    _stat("region size (tiles)", sizes, ".1f")
    print(f"  {'worlds with no drought region':<34} {droughtless}  "
          f"(the guarantee: this is 0 or the law is broken)")
    print(f"  {'trouble within ' + str(places.TROUBLE_DAYS) + ' days of the start':<34} "
          f"{100 * sum(near) / len(near):.0f}%")
    print("  causes: " + ", ".join(f"{cause}: {n}"
                                   for cause, n in causes.most_common()))
    total = sum(words.values())
    print("  spoken words: " + ", ".join(
        f"{word} {100 * words.get(word, 0) / total:.1f}%"
        for _floor, word in places.HARVEST_WORDS))


def sweep_census(seeds: int) -> None:
    print(f"\n--- THE SETTLEMENT CENSUS ({seeds} worlds) ---")
    people = {"hamlet": 60, "village": 300, "town": 3000,
              "city": 25000, "metropolis": 150000}
    tiers: Counter = Counter()
    filled, empty, souls, quiet, charters, manors = [], [], [], [], [], []
    for _seed, world in worlds(seeds):
        land = _land(world)
        counts = [len(tile["settlement_slots"]) for tile in land]
        filled.append(sum(counts) / len(counts))
        empty.append(sum(1 for n in counts if n == 0))
        here: Counter = Counter(slot["tier"] for slot
                                in world["settlement_slots"].values())
        tiers.update(here)
        souls.append(sum(people[tier] * n for tier, n in here.items()))
        rich = [tile for tile in land
                if places.population_band(world, tile) in ("high", "dense")
                and (tile["row"], tile["column"])
                not in places.HISTORICAL_BY_TILE]
        quiet.append(sum(1 for tile in rich if not {
            world["settlement_slots"][sid]["tier"]
            for sid in tile["settlement_slots"]}
            & {"town", *places.CITY_GRADE}) / len(rich))
        slots = world["settlement_slots"].values()
        charters.append(sum(1 for slot in slots if slot["charter"]))
        manors.append(sum(1 for slot in slots if slot["manor"]))
    print("  settlements a world: " + ", ".join(
        f"{tier} {tiers.get(tier, 0) / seeds:.1f}" for tier in places.TIERS)
        + f"; total {sum(tiers.values()) / seeds:.1f}")
    _stat("slots filled a land tile", filled, ".2f")
    _stat(f"empty tiles (of {len(_land(places.create_geography(0)))})",
          empty, ".0f")
    _stat("souls in the world", souls, ",.0f")
    _stat("quiet rich country (% no town)", quiet, ".0f", 100)
    _stat("free (chartered) settlements", charters, ".1f")
    _stat("manors", manors, ".1f")


def sweep_trade(seeds: int) -> None:
    print(f"\n--- THE TRADE NETWORK ({seeds} worlds) ---")
    routes, on_land, ports, lanes, crossroads = [], [], [], [], []
    unfed: Counter = Counter()
    for _seed, world in worlds(seeds):
        routes.append(len(world["routes"]))
        traffic = Counter(tid for route in world["routes"]
                          for tid in route["path"])
        tiles = world["tiles"]
        on_land.append(sum(1 for tid in traffic
                           if tiles[tid]["biome"] != "sea"))
        lanes.append(sum(1 for tid in traffic
                         if tiles[tid]["biome"] == "sea"))
        ports.append(sum(1 for tile in _land(world)
                         if "port" in tile["tags"]))
        crossroads.append(sum(1 for tid, n in traffic.items()
                              if n >= 3 and tiles[tid]["biome"] != "sea"))
        fed = {route["path"][-1] for route in world["routes"]
               if "grain" in route["goods"]}
        for (row, column), (name, _goods) in places.MINES.items():
            tid = places.tile_id(row, column)
            tile = tiles[tid]
            economy = places.tile_economy(tile["climate"], tile["terrain"],
                                          tile["biome"] == "river",
                                          row, column)
            if economy["realized"] < places.FARMLAND_MIN and tid not in fed:
                unfed[name] += 1
    _stat("routes after merging", routes, ".1f")
    _stat(f"land tiles on a route (of {len(_land(places.create_geography(0)))})",
          on_land, ".1f")
    _stat("ports", ports, ".1f")
    _stat("sea-lane tiles", lanes, ".1f")
    _stat("crossroads (3+ routes)", crossroads, ".1f")
    print("  unfed mines: " + (", ".join(f"{name} in {n}/{seeds}"
                                         for name, n in unfed.most_common())
                               or "none"))


SWEEPS = {"harvest": sweep_harvest, "census": sweep_census,
          "trade": sweep_trade}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=100,
                    help="how many worlds to build (the arc's pins: 500)")
    ap.add_argument("--only", choices=sorted(SWEEPS), default=None)
    args = ap.parse_args()
    chosen = [args.only] if args.only else ["harvest", "census", "trade"]
    started = time.time()
    for name in chosen:
        SWEEPS[name](args.seeds)
    print(f"\n({args.seeds} worlds x {len(chosen)} sweep(s) in "
          f"{time.time() - started:.0f}s)")


if __name__ == "__main__":
    main()
