"""Party-size benchmark: what a head is worth (the "Balanced for two" check).

Runs both sites at rank 0 with parties of 1-4 rolled heroes and prints
wipe/down/clear rates per size. This is the measurement behind rules.md's
"Balanced for two": in-fight, numbers dominate every other progression axis
(hideout ~15/64/93/99% clear for sizes 1-4), and the counterweights that
drag on that are mostly OUTSIDE this sweep -- XP x 2/N and flat gold
compound across a campaign, not within one run. Re-run after touching the
press (CROWD_CAP / crowd_cap), sweeps, or anything in the melee loop.

Run:  python bench_party.py [--trials N]
"""

import argparse
import random

import rpg
from sites import SITES, run_site


def make_party_n(rng: random.Random, n: int) -> list[rpg.Entity]:
    names = rng.sample(rpg.NAMES, n)
    return [rpg.make_human(rng, name) for name in names]


def simulate(site: str, trials: int) -> None:
    print(f"\n--- {site} ({trials} trials per size, rank 0) ---")
    print(f"{'size':<6}{'wipe%':>8}{'down%':>8}{'clear%':>8}")
    for size in (1, 2, 3, 4):
        rng = random.Random(9999)
        wiped = downed = cleared = 0
        for _ in range(trials):
            party = make_party_n(rng, size)
            purse = rpg.Purse()
            log: list[str] = []
            run_site(SITES[site], party, rpg.Clock(), purse, rng, log,
                     verbose_rosters=False)
            wiped += all(h.dead for h in party)
            downed += any("goes down" in line for line in log)
            cleared += any("QUEST COMPLETE" in line for line in log)
        print(f"{size:<6}{100 * wiped / trials:>7.1f}%"
              f"{100 * downed / trials:>7.1f}%"
              f"{100 * cleared / trials:>7.1f}%")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=5000)
    args = ap.parse_args()
    simulate("hideout", args.trials)
    simulate("barrow", args.trials)


if __name__ == "__main__":
    main()
