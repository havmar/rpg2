"""Phase 3 benchmark: does a level of combat training NOTICEABLY change the
outcome against a fixed enemy? (plan.md Phase 3's test criterion.)

Runs the bandit hideout (the tough site) and the skeleton barrow with the party
pre-set to each training rank, and prints the wipe / death / clear rates per
rank. The intended shape: rank 0 mostly wipes at the hideout, each rank buys a
visible jump, and by rank 2-3 the hideout is a fair (still scary) fight.
"""

import random
from collections import Counter

import rpg
from scratch_bandits import run_hideout


def simulate(site, trials=5000, max_training=3):
    print(f"\n--- {site} ({trials} trials per rank) ---")
    print(f"{'training':<10}{'none':>7}{'one':>7}{'both':>7}{'down%':>8}"
          f"{'clear%':>8}")
    for training in range(max_training + 1):
        rng = random.Random(9999)
        counts = Counter()
        downed = cleared = 0
        for _ in range(trials):
            party = rpg.make_party(rng)
            for h in party:
                h.training = training
            purse = rpg.Purse()
            log = []
            if site == "hideout":
                run_hideout(party, rpg.Clock(), purse, rng, log,
                            verbose_rosters=False)
            else:
                rpg.run_dungeon(party, rpg.Clock(), purse, rng, log)
            counts[rpg.outcome(party)] += 1
            if any("goes down" in line for line in log):
                downed += 1
            if any("QUEST COMPLETE" in line for line in log):
                cleared += 1
        pct = {k: 100 * counts[k] / trials for k in ("none", "one", "both")}
        print(f"{training:<10}{pct['none']:>6.1f}%{pct['one']:>6.1f}%"
              f"{pct['both']:>6.1f}%{100 * downed / trials:>7.1f}%"
              f"{100 * cleared / trials:>7.1f}%")


def main():
    simulate("barrow")
    simulate("hideout")


if __name__ == "__main__":
    main()
