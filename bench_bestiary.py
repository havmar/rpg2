"""Bestiary benchmark: is each catalog row's LEVEL annotation honest?

For every monster in sites.FOES, runs its reference encounter (`ref_pack` of
the row) against reference DUOS -- the two-hero baseline the game is balanced
for -- at the annotated level and two levels either side, and prints win /
fled / wipe / down rates. The calibration target: the AT-LEVEL duo wins
roughly 55-75% of the time (a fair, still-scary single encounter -- one
fight, not a site: no attrition, so it can sit above a site's clear target),
with the -2 column visibly worse and the +2 column visibly safer. That is
what makes `level` a difficulty language the future encounter generator (and
the player) can trust.

The reference duo is PROVISIONAL, built to the rules.md progression
DOCTRINE V2 (2026-07-17, the point economy: the OLD default build priced in
the new currency, so every pre-economy number stays comparable):
  - rolled like any hero (make_human), then leveled to L with
    (L-1) x SKILL_POINTS_PER_LEVEL points;
  - pools bought to the old odd-level curve first (+1 HP/STA/Power per two
    levels, 3 points a step -- rpg.grow_pools as the doctrine helper);
  - then training to 3 (rank n costs 2n now), then proficiency/school
    (rank n costs n), then training to the cap -- monotone;
  - quality steel from level 4 (katana -- the reliable all-rounder).

Run:  python bench_bestiary.py [--trials N] [--kind wolf]
"""

import argparse
import random
from collections import Counter

import rpg
from sites import FOES, make_foe


def reference_hero(rng: random.Random, name: str, level: int) -> rpg.Entity:
    """A hero of the given level under the progression doctrine v2 (see
    module docstring): the old default build bought back in the new point
    economy -- pools to the old curve, training at 2n, proficiency/school
    at n, quality steel from L4, monotone throughout (a bench reference
    must never get worse with levels)."""
    h = rpg.make_human(rng, name)
    h.level = level
    points = (level - 1) * rpg.SKILL_POINTS_PER_LEVEL

    # Pools first: the old automatic growth, bought at 3 points a step.
    growth = min((level - 1) // rpg.POOL_GROWTH_LEVELS, rpg.POOL_BUY_CAP)
    for _ in range(growth):
        rpg.grow_pools(h)
        points -= 3
    for kind in rpg.POOL_KINDS:
        h.pool_bought[kind] = h.pool_bought.get(kind, 0) + growth

    def buy_training(cap: int) -> None:
        nonlocal points
        while (h.training < cap
               and points >= rpg.training_cost(h.training)):
            points -= rpg.training_cost(h.training)
            h.training += 1

    buy_training(3)
    if level >= 4:
        h.weapon = rpg.WEAPONS["katana"]
    # A rolled wizard trains the SCHOOL SPELL (their real offense), like
    # develop_hero: katana ranks would be dead points on a caster.
    if h.school:
        rank = h.spells.get(h.school, 1)
        while rank < rpg.SPELLS[h.school].max_rank and points >= rank + 1:
            points -= rank + 1
            rank += 1
        h.spells[h.school] = rank
    else:
        rank = 0
        while rank < rpg.PROFICIENCY_MAX and points >= rank + 1:
            points -= rank + 1
            rank += 1
        if rank:
            h.proficiency[h.weapon.name] = rank
    buy_training(rpg.TRAINING_MAX)
    h.skill_points = points
    return h


def run_encounter(kind: str, level: int, rng: random.Random) -> tuple[str, bool]:
    """One reference fight: a fresh reference duo vs the row's ref_pack.
    Returns (result, someone_downed): result in win / fled / wipe / stall
    (stall = the round cap fired with both sides up -- a regen wall the
    party can't out-cut is a failed encounter, not a win).

    Ranged rows (2026-07-16) are benched at WILD_FIELD -- their natural
    engagement (a shooter benched at the door never shoots); melee rows
    keep field 0, so every pre-ranged annotation is measured exactly as
    before."""
    spec = FOES[kind]
    names = rng.sample(rpg.NAMES, 2)
    party = [reference_hero(rng, n, level) for n in names]
    foes = [make_foe(kind, i + 1, rng) for i in range(spec.ref_pack)]
    ranged = spec.weapon is not None and spec.weapon.range > 0
    log: list[str] = []
    result = rpg.sim_fight(party, foes, rng, log,
                           field=rpg.WILD_FIELD if ranged else 0)
    downed = any("goes down" in line for line in log)
    if result == "fled":
        return "fled", downed
    if not any(h.alive for h in party):
        return "wipe", downed
    if any(f.alive for f in foes):
        return "stall", downed
    return "win", downed


def bench(kind: str, trials: int) -> None:
    spec = FOES[kind]
    pack = f"{spec.ref_pack}x " if spec.ref_pack > 1 else ""
    print(f"\n--- {pack}{spec.display} (annotated level {spec.level}, "
          f"{trials} trials per column) ---")
    print(f"{'party L':<10}{'win%':>8}{'fled%':>8}{'wipe%':>8}{'stall%':>8}"
          f"{'down%':>8}")
    for level in (spec.level - 2, spec.level, spec.level + 2):
        if level < 1:
            continue
        rng = random.Random(4242)
        counts: Counter[str] = Counter()
        downs = 0
        for _ in range(trials):
            result, downed = run_encounter(kind, level, rng)
            counts[result] += 1
            downs += downed
        mark = " <- annotated" if level == spec.level else ""
        print(f"{level:<10}{100 * counts['win'] / trials:>7.1f}%"
              f"{100 * counts['fled'] / trials:>7.1f}%"
              f"{100 * counts['wipe'] / trials:>7.1f}%"
              f"{100 * counts['stall'] / trials:>7.1f}%"
              f"{100 * downs / trials:>7.1f}%{mark}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=2000)
    ap.add_argument("--kind", choices=sorted(FOES), default=None,
                    help="bench a single row (default: the whole catalog)")
    args = ap.parse_args()
    kinds = [args.kind] if args.kind else sorted(
        FOES, key=lambda k: (FOES[k].level, k))
    for kind in kinds:
        bench(kind, args.trials)


if __name__ == "__main__":
    main()
