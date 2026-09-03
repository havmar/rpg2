"""The wound-record bench (2026-09-03, the one-wound rebalance).

What the sheet shows the player after a fight: how many named wound records
a surviving hero carries out of one at-level ROOM and out of a whole cleared
JOB (1-3 rooms, camps between), how much wound LOAD (the ceiling dock, the
bed-nights) those records add up to, and which names come up. The reference
duo of bench_bestiary, the played band (L1-5 by default), won fights and
cleared jobs only.

This is the meter for the two FEEL knobs the rebalance added
(`WOUND_TIER_SEVERITY`, `WOUND_SEVERITY_MAX` -- develop.md's Balance /
tuning): records per hero is what "a catalogue of injuries" measures, and
load per hero is the mechanical cost that has to hold when the records get
rarer. The 2026-07-26 table read 0.3-0.5 records and 0.5-0.9 load per hero
per cleared job with 11-20% of jobs leaving two or more on one hero; the
one-wound table reads 0.1-0.2 records, the same load from L2 up, and never
two (benchlog 2026-09-03).

Run:  python bench_wounds.py [--trials N] [--levels 1-5]
"""

from __future__ import annotations

import argparse
import random
from collections import Counter

import rpg
from sites import Site, make_foe, run_site
from bench_bestiary import reference_hero
from bench_quests import pools_for
from quests import build_room, build_site_rooms, room_budget, QUEST_ENCOUNTERS


def _tally(party, stats: dict) -> None:
    """Fold the surviving heroes' records into the running stats."""
    two = False
    for h in party:
        if not h.alive:
            continue
        stats["heroes"] += 1
        k = sum(1 for w in h.wounds if not w.permanent)
        stats["records"] += k
        stats["load"] += h.wound_load
        stats["dist"][min(k, 2)] += 1
        two |= k >= 2
        for w in h.wounds:
            stats["names"][w.name] += 1
            stats["sev"][w.severity] += 1
    stats["two_any"] += two


def _row(level: int, won: int, trials: int, s: dict) -> str:
    n = max(1, s["heroes"])
    return (f"{level:<4}{100 * won / trials:>6.0f}%{s['records'] / n:>10.2f}"
            f"{s['load'] / n:>10.2f}{100 * s['dist'][0] / n:>7.0f}%"
            f"{100 * s['dist'][1] / n:>6.0f}%{100 * s['dist'][2] / n:>6.0f}%"
            f"{100 * s['two_any'] / max(1, won):>9.0f}%")


def _stats() -> dict:
    return {"heroes": 0, "records": 0, "load": 0, "dist": Counter(),
            "two_any": 0, "names": Counter(), "sev": Counter()}


HEADER = (f"{'L':<4}{'won':>7}{'rec/hero':>10}{'load/hero':>10}"
          f"{'0':>8}{'1':>7}{'2+':>7}{'2+ any':>10}")


def bench_rooms(trials: int, levels: range) -> None:
    print(f"\n--- one at-level ROOM vs the reference duo, won fights only "
          f"({trials} trials/level) ---")
    print(HEADER)
    tiers: Counter[str] = Counter()
    original = rpg.record_hit_wound

    def counting(defender, tier, rng, log=None):
        if defender.records_wounds and tier in rpg.WOUND_TIER_SEVERITY:
            tiers[tier] += 1
        return original(defender, tier, rng, log)

    rpg.record_hit_wound = counting
    try:
        for level in levels:
            rng = random.Random(777 + level)
            s, won = _stats(), 0
            for _ in range(trials):
                pool = rng.choice(pools_for(level))
                kinds = build_room(room_budget(level, 1.0), pool, rng,
                                   final=True)
                party = [reference_hero(rng, n, level)
                         for n in rng.sample(rpg.NAMES, 2)]
                foes = [make_foe(k, i + 1, rng) for i, k in enumerate(kinds)]
                result = rpg.sim_fight(party, foes, rng, [])
                if (result == "fled" or not any(h.alive for h in party)
                        or any(f.alive for f in foes)):
                    continue
                won += 1
                _tally(party, s)
            print(_row(level, won, trials, s))
    finally:
        rpg.record_hit_wound = original
    total = max(1, sum(tiers.values()))
    print("  recording blows by tier: "
          + ", ".join(f"{t} {100 * n / total:.0f}%" for t, n in tiers.items()))
    print("  (rec = non-permanent records; 0/1/2+ = share of surviving heroes;"
          " 2+ any = won fights leaving 2+ on one hero)")


def bench_jobs(trials: int, levels: range) -> None:
    print(f"\n--- a whole generated JOB (1-3 rooms, camps between) vs the "
          f"reference duo, cleared jobs only ({trials} trials/level) ---")
    print(HEADER.replace("won", "clear"))
    for level in levels:
        rng = random.Random(4242 + level)
        s, cleared = _stats(), 0
        for _ in range(trials):
            pool = rng.choice(pools_for(level))
            n_rooms = rng.choices(*QUEST_ENCOUNTERS)[0]
            rooms = tuple((rn, tuple(kinds)) for rn, kinds
                          in build_site_rooms(level, n_rooms, pool, rng))
            site = Site(key="bench", level=level, rooms=rooms,
                        quest_line="site cleared", spawn_phrase="{n} foes",
                        abandon_line="abandoned.", intro="")
            party = [reference_hero(rng, n, level)
                     for n in rng.sample(rpg.NAMES, 2)]
            log: list[str] = []
            run_site(site, party, rpg.Clock(), rpg.Purse(), rng, log)
            if not any("QUEST COMPLETE" in line for line in log):
                continue
            cleared += 1
            _tally(party, s)
        print(_row(level, cleared, trials, s))
        print("      severities " + str(dict(sorted(s["sev"].items()))))
        print("      " + "; ".join(f"{name} x{n}"
                                   for name, n in s["names"].most_common(5)))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--trials", type=int, default=1000,
                    help="trials per level (default 1000)")
    ap.add_argument("--levels", default="1-5",
                    help="level band, e.g. 1-5 (the played band) or 6-10")
    args = ap.parse_args()
    lo, hi = (int(x) for x in args.levels.split("-"))
    levels = range(lo, hi + 1)
    bench_rooms(args.trials, levels)
    bench_jobs(args.trials, levels)


if __name__ == "__main__":
    main()
