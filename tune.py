"""Monte Carlo tuner for the dungeon, post survival add-on.

Deaths are now the rare tail (a killing blow with the saves run dry), so the
none/one/both death split is no longer the whole story. The real challenge is
attrition: how often someone goes Down, and how far Power / STA / potions are
drawn down by the end of a run. This sweeps room layouts and reports both.
"""

import random
from collections import Counter

import rpg


def simulate(rooms, trials=20000):
    counts = Counter()
    downed_runs = 0          # runs where at least one hero went Down
    cleared_runs = 0         # runs where the quest completed (site cleared)
    pow_left = sta_left = heal_left = gold = 0.0
    pow_max = sta_max = 0.0
    rng = random.Random(12345)
    saved = rpg.DUNGEON_ROOMS
    rpg.DUNGEON_ROOMS = rooms
    try:
        for _ in range(trials):
            party = rpg.make_party(rng)
            purse = rpg.Purse()
            log = []
            rpg.run_dungeon(party, rpg.Clock(), purse, rng, log)
            counts[rpg.outcome(party)] += 1
            # "Down" is transient (revived between rooms); a run shows it via the
            # narrative. Count it by scanning the log for the down line.
            if any("goes down" in line for line in log):
                downed_runs += 1
            if any("QUEST COMPLETE" in line for line in log):
                cleared_runs += 1
            gold += purse.gold
            for h in party:
                pow_left += h.cur_power
                sta_left += h.cur_sta
                heal_left += h.items.get("healing", 0)
                pow_max += h.power
                sta_max += h.sta
    finally:
        rpg.DUNGEON_ROOMS = saved
    n = trials * 2  # two heroes per run
    stats = {
        "down_pct": 100 * downed_runs / trials,
        "clear_pct": 100 * cleared_runs / trials,
        "pow_pct": 100 * pow_left / pow_max if pow_max else 0,
        "sta_pct": 100 * sta_left / sta_max if sta_max else 0,
        "heal_left": heal_left / n,
        "gold": gold / trials,
    }
    return counts, stats, trials


def main():
    layouts = [
        [2, 2, 3],      # the old (pre-collapse) default, for comparison
        [2, 3, 3],
        [3, 3, 3],
        [3, 3, 4],      # the current default (barrow = the TOUGH site now)
        [3, 4, 4],
        [3, 4, 5],
    ]
    print(f"{'rooms':<12}{'none':>7}{'one':>7}{'both':>7}"
          f"{'down%':>8}{'clear%':>8}{'Pow%':>7}{'STA%':>7}{'heal':>7}"
          f"{'gold':>7}")
    print("  (none/one/both = truly slain; down% = runs with a Down; "
          "clear% = quest done;\n   Pow%/STA% = avg budget left; "
          "heal = avg healing potions left; gold = avg purse)")
    for rooms in layouts:
        counts, stats, trials = simulate(rooms)
        pct = {k: 100 * counts[k] / trials for k in ("none", "one", "both")}
        print(f"{str(rooms):<12}"
              f"{pct['none']:>6.1f}%{pct['one']:>6.1f}%{pct['both']:>6.1f}%"
              f"{stats['down_pct']:>7.1f}%{stats['clear_pct']:>7.1f}%"
              f"{stats['pow_pct']:>6.1f}%"
              f"{stats['sta_pct']:>6.1f}%{stats['heal_left']:>7.2f}"
              f"{stats['gold']:>7.1f}")


if __name__ == "__main__":
    main()
