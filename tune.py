"""Monte Carlo tuner for the sites, post survival add-on.

Deaths are the rare tail (a crippling blow with the saves run dry), so the
none/one/both death split is no longer the whole story. What the 2026-07
lethality retune tunes FOR:

- attrition: how often someone goes Down, and how far Power / STA / potions
  are drawn down by the end of a run;
- EARLY pressure: the first 1-2 rooms should already force resources (a
  pause, a Down, a potion) -- the party can always camp after any encounter,
  so danger has to live in each encounter itself, not only in the grind;
- the no-resource baseline ("reckless"): a party that never drinks, never
  takes a pause action, never retreats should MOSTLY DIE. If it doesn't, the
  resources aren't being forced, they're decoration.

Sweeps barrow room layouts (run_site's `rooms` override) and reports all of
it, then prints the resource-pressure check (policy vs reckless) for both
sites.
"""

import random
import re
from collections import Counter

import rpg
from sites import SITES, run_site

ROOM_BANNER = re.compile(r"=== Room (\d+)")

# Log markers meaning "this room forced something" -- all of them party-only
# lines. A hero going SPENT counts too, but its `!!` line prints for foes as
# well (bandits run dry constantly), so it's matched per hero name below.
PRESSURE_MARKS = ("hangs for a heartbeat", "goes down",
                  "downs a stamina draught", "drinks a healing potion")


def early_pressure(log, heroes) -> bool:
    """Did rooms 1-2 already force a pause / Down / Spent / potion on the
    PARTY? (The retune's per-encounter threat criterion: threat in the
    opening rooms, not just the last one. Foes going Spent don't count.)"""
    spent_marks = tuple(f"!! {name} is SPENT" for name in heroes)
    for line in log:
        m = ROOM_BANNER.search(line)
        if m and int(m.group(1)) >= 3:
            return False
        if (any(mark in line for mark in PRESSURE_MARKS)
                or any(mark in line for mark in spent_marks)):
            return True
    return False


def simulate(site_key, trials=20000, rooms=None, reckless=False):
    """One batch. site_key: "barrow" or "hideout". `rooms` = a barrow layout
    to sweep (a list of skeleton counts); None = the site's set rooms.
    Returns (death Counter, stats dict, trials)."""
    site = SITES[site_key]
    layout = None if rooms is None else tuple(
        (f"room {i + 1}", ("skeleton",) * n) for i, n in enumerate(rooms))
    counts = Counter()
    downed_runs = cleared_runs = fled_runs = early_runs = 0
    days = 0
    pow_left = sta_left = heal_left = gold = 0.0
    pow_max = sta_max = 0.0
    hp_hist = Counter()     # cleared runs only: party HP lost, bucketed --
                            # the "less binary outcomes" criterion (2026-07-09):
                            # the 25% and 75% middle should be reachable, not
                            # just walk-away-clean and the grave
    rng = random.Random(12345)
    for _ in range(trials):
        party = rpg.make_party(rng)
        purse = rpg.Purse()
        clock = rpg.Clock()
        log = []
        run_site(site, party, clock, purse, rng, log,
                 verbose_rosters=False, reckless=reckless, rooms=layout)
        counts[rpg.outcome(party)] += 1
        if any("goes down" in line for line in log):
            downed_runs += 1
        if any("QUEST COMPLETE" in line for line in log):
            cleared_runs += 1
            lost = sum(h.max_hp - h.hp for h in party)
            frac = lost / sum(h.max_hp for h in party)
            hp_hist["<10%" if frac < 0.10 else
                    "10-40%" if frac < 0.40 else
                    "40-70%" if frac < 0.70 else ">=70%"] += 1
        if any("breaks for safety" in line for line in log):
            fled_runs += 1
        if early_pressure(log, [h.name for h in party]):
            early_runs += 1
        days += clock.day
        gold += purse.gold
        for h in party:
            pow_left += h.cur_power
            sta_left += h.cur_sta
            heal_left += h.items.get("healing", 0)
            pow_max += h.power
            sta_max += h.sta
    n = trials * 2  # two heroes per run
    stats = {
        "hp_hist": hp_hist,
        "down_pct": 100 * downed_runs / trials,
        "clear_pct": 100 * cleared_runs / trials,
        "flee_pct": 100 * fled_runs / trials,
        "early_pct": 100 * early_runs / trials,
        "days": days / trials,
        "pow_pct": 100 * pow_left / pow_max if pow_max else 0,
        "sta_pct": 100 * sta_left / sta_max if sta_max else 0,
        "heal_left": heal_left / n,
        "gold": gold / trials,
        "wipe_pct": 100 * counts["both"] / trials,
    }
    return counts, stats, trials


def main():
    layouts = [
        [2, 2, 3],
        [2, 3, 3],
        [3, 3, 3],
        [3, 3, 4],      # the current default (barrow = the TOUGH site)
        [3, 4, 4],
        [3, 4, 5],
    ]
    print(f"{'rooms':<12}{'none':>7}{'one':>7}{'both':>7}"
          f"{'down%':>8}{'clear%':>8}{'flee%':>7}{'early%':>8}{'days':>6}"
          f"{'Pow%':>7}{'STA%':>7}{'heal':>7}{'gold':>7}")
    print("  (none/one/both = truly slain; down% = runs with a Down; "
          "clear% = quest done;\n   flee% = runs with a retreat; "
          "early% = rooms 1-2 forced a pause/Down/potion;\n   "
          "days = avg days; Pow%/STA% = avg budget left; "
          "heal = avg healing potions left)")
    for rooms in layouts:
        counts, stats, trials = simulate("barrow", rooms=rooms)
        pct = {k: 100 * counts[k] / trials for k in ("none", "one", "both")}
        print(f"{str(rooms):<12}"
              f"{pct['none']:>6.1f}%{pct['one']:>6.1f}%{pct['both']:>6.1f}%"
              f"{stats['down_pct']:>7.1f}%{stats['clear_pct']:>7.1f}%"
              f"{stats['flee_pct']:>6.1f}%{stats['early_pct']:>7.1f}%"
              f"{stats['days']:>6.2f}{stats['pow_pct']:>6.1f}%"
              f"{stats['sta_pct']:>6.1f}%{stats['heal_left']:>7.2f}"
              f"{stats['gold']:>7.1f}")

    # The resource-pressure check: the same sites with resources vs without.
    # "reckless" = no pauses (no drink/convert/retreat) and no potions --
    # its wipe rate is the price of ignoring your resources, and the retune
    # wants that price to be most of a party's life expectancy.
    print()
    print("Resource pressure at rank 0 (policy = pause/potions/retreat as "
          "usual; reckless = none of it):")
    print(f"{'site':<24}{'policy wipe%':>14}{'policy clear%':>15}"
          f"{'reckless wipe%':>16}{'reckless clear%':>17}")
    hp_rows = []
    for site_key, label in (("hideout", "hideout (starter)"),
                            ("barrow", "barrow [3,3,4]")):
        _, pol, _ = simulate(site_key, trials=10000)
        _, rek, _ = simulate(site_key, trials=10000, reckless=True)
        print(f"{label:<24}{pol['wipe_pct']:>13.1f}%{pol['clear_pct']:>14.1f}%"
              f"{rek['wipe_pct']:>15.1f}%{rek['clear_pct']:>16.1f}%")
        hp_rows.append((label, pol["hp_hist"]))

    # The outcome-shape check (2026-07-09): among CLEARED runs, how much HP
    # the party walked out short -- the "less binary" criterion wants the
    # middle buckets populated, not a spike at clean and a cliff at dead.
    print()
    print("HP lost on CLEARED runs (walk-away wounds; deaths are the "
          "wipe% above):")
    buckets = ("<10%", "10-40%", "40-70%", ">=70%")
    print(f"{'site':<24}" + "".join(f"{b:>9}" for b in buckets))
    for label, hist in hp_rows:
        total = sum(hist.values()) or 1
        print(f"{label:<24}" + "".join(
            f"{100 * hist[b] / total:>8.1f}%" for b in buckets))


if __name__ == "__main__":
    main()
