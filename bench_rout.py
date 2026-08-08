"""Rout benchmark: how often does a beaten foe line actually get away, and
does the outcome track the PARTY'S CONDITION?

The rout is the engine's one reverse-retreat: a ferocity-0/1 roster below
the rout band (rpg.rout_ready -- a THIRD of HP, or Spent) makes ONE break
attempt, and a chase contest decides it. This bench is the acceptance test
for the 2026-08-08 rebalance, whose complaint was measured, not felt: the
solo troll escaped 54% of WON fights and 50% even when the party ended
fresh, because a big HP pool sits in the trigger band for rounds while
DEX 6-7 plus the flee bonus beat the party average. Ordinary at-level
packs almost never escaped -- they die from above the band in one blow --
so the mechanic fired hardest in exactly the fights the party was flatly
winning, and the fiction it forced contradicted the job ("kill the
giants", completed by a troll jogging off).

What the rebalance changed, and therefore what this file measures:

- the rout lost FLEE_BONUS (a collapse under pursuit picks nothing);
- the runners' chase DEX is HP-weighted as well as STA-weighted, floored
  at rpg.CHASE_HP_WEIGHT_FLOOR (broken bodies run slowly, but a
  graze-rich pack is not automatically caught);
- the trigger moved from fight_winding_down's half to rout_ready's third.

`--legacy` restores all three (bonus, plain STA weighting, the half band)
so every readout prints BEFORE and AFTER off the same seeds -- the
comparison the benchlog wants, rather than two harnesses arguing.

Two readouts, both against level-matched reference duos:

- ESCAPE BY ROW: per foe row, the share of WON fights that ended in an
  escape, and the RUN-DOWN share (the break was tried and caught -- the
  fight resumed and finished with a kill). The design target is escape
  becoming rare and run-downs rising: a beaten thing tries to leave and
  usually fails.
- THE CONDITION CORRELATION: the same won fights split by how the PARTY
  ended them -- above half HP (fresh) against at-or-below (hurt). This is
  the rebalance's real acceptance test, and the two columns must separate:
  a fresh party should rarely let anything go, while a party with nothing
  left keeps its relief-escape. Pre-hurting the party at the door does
  NOT measure this (a crippled duo simply loses, and a fight it never won
  has no escape to count) -- the split has to be read off the fight's own
  ending.

The troll keeps a residue no chase math will remove: its regeneration
holds it inside the trigger band while it is otherwise fine. That is
honest troll fiction -- a regenerating monster slinking off to heal --
and the loose-ends record (session.py) makes it a hook rather than a
contradiction.

Run:  python bench_rout.py [--trials N] [--legacy] [--part rows|state]
"""

from __future__ import annotations

import argparse
import contextlib
import random
from collections import Counter

import rpg
from bench_bestiary import reference_hero
from sites import FOES, make_foe

# The rows that can rout at all (ferocity 0/1): an ordinary humanoid pack,
# a beast pack, the two mid solos, and the troll that drove the complaint.
ROWS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("pack (3 cutthroats)", ("cutthroat", "cutthroat", "cutthroat")),
    ("pack (3 wolves)",     ("wolf", "wolf", "wolf")),
    ("ogre",                ("ogre",)),
    ("bear",                ("bear",)),
    ("troll",               ("troll",)),
)


def row_level(kinds: tuple[str, ...]) -> int:
    """The level a duo meets this row at: the anchor's own."""
    return max(FOES[k].level for k in kinds)


@contextlib.contextmanager
def legacy_rout():
    """The pre-2026-08-08 rules, for the before column: the rout triggers
    at the winding-down half band, keeps FLEE_BONUS, and weighs its
    runners by STA alone."""
    real_ready, real_contest = rpg.rout_ready, rpg._chase_contest

    def plain_contest(runners, pursuers, rng, log, routed=False):
        return real_contest(runners, pursuers, rng, log, routed=False)

    rpg.rout_ready = rpg.fight_winding_down
    rpg._chase_contest = plain_contest
    try:
        yield
    finally:
        rpg.rout_ready = real_ready
        rpg._chase_contest = real_contest


def probe(kinds: tuple[str, ...], trials: int, seed: int) -> Counter:
    """Fight one row `trials` times and count what the rout did. A fight
    counts as WON when the field is the party's -- every foe dead or
    withdrawn -- which is the only outcome an escape can happen in."""
    level = row_level(kinds)
    counts: Counter[str] = Counter()
    real_retreat = rpg.attempt_foe_retreat

    def spy(foes, party, rng, log, field=0):
        got_away = real_retreat(foes, party, rng, log, field=field)
        counts["escaped_attempt" if got_away else "run_down"] += 1
        counts["attempts"] += 1
        return got_away

    rng = random.Random(seed)
    for _ in range(trials):
        names = rng.sample(rpg.NAMES, 2)
        party = [reference_hero(rng, n, level) for n in names]
        foes = [make_foe(k, j + 1, rng) for j, k in enumerate(kinds)]
        log: list[str] = []
        rpg.attempt_foe_retreat = spy
        try:
            rpg.sim_fight(party, foes, rng, log)
        finally:
            rpg.attempt_foe_retreat = real_retreat
        if not any(h.alive for h in party):
            counts["wiped"] += 1
            continue
        if any(f.alive for f in foes):
            counts["unresolved"] += 1
            continue
        counts["won"] += 1
        got_away = any(f.withdrew for f in foes)
        counts["escaped"] += got_away
        # How the party ENDED the won fight: the condition correlation.
        # Read off the ending, never off the door -- a party hurt at the
        # door loses instead of winning, and measures nothing.
        living = [h for h in party if h.alive]
        fresh = all(h.hp * 2 > h.max_hp for h in living)
        counts["won_fresh" if fresh else "won_hurt"] += 1
        if got_away:
            counts["escaped_fresh" if fresh else "escaped_hurt"] += 1
    return counts


def _pct(n: int, d: int, width: int = 7) -> str:
    return f"{100 * n / d:>{width - 1}.1f}%" if d else f"{'-':>{width}}"


def _probe_both(kinds, trials, seed, legacy: bool):
    if not legacy:
        return probe(kinds, trials, seed)
    with legacy_rout():
        return probe(kinds, trials, seed)


def bench_rows(trials: int, legacy: bool) -> None:
    rules = "the OLD rules (bonus, STA-only, half band)" if legacy \
        else "the rebalanced rules"
    print(f"\n--- ESCAPE RATES: level-matched fresh duos, {rules} "
          f"({trials} fights/row) ---")
    print(f"{'row':<22}{'L':>3}{'won':>8}{'escape':>8}{'run-down':>10}"
          f"{'tries':>7}")
    for i, (label, kinds) in enumerate(ROWS):
        c = _probe_both(kinds, trials, 4242 + i * 101, legacy)
        print(f"{label:<22}{row_level(kinds):>3}{_pct(c['won'], trials, 8)}"
              f"{_pct(c['escaped'], c['won'], 8)}"
              f"{_pct(c['run_down'], c['attempts'], 10)}"
              f"{c['attempts']:>7}")
    print("  (escape = share of WON fights the survivors got away from;")
    print("   run-down = share of break ATTEMPTS the party caught)")


def bench_state(trials: int, legacy: bool) -> None:
    rules = "OLD rules" if legacy else "rebalanced"
    print(f"\n--- THE CONDITION CORRELATION ({rules}, {trials} "
          f"fights/row) ---")
    print(f"{'row':<22}{'escape|fresh':>14}{'escape|hurt':>13}"
          f"{'fresh wins':>12}{'hurt wins':>11}")
    for i, (label, kinds) in enumerate(ROWS):
        c = _probe_both(kinds, trials, 4242 + i * 101, legacy)
        print(f"{label:<22}"
              f"{_pct(c['escaped_fresh'], c['won_fresh'], 14)}"
              f"{_pct(c['escaped_hurt'], c['won_hurt'], 13)}"
              f"{c['won_fresh']:>12}{c['won_hurt']:>11}")
    print("  (fresh = the party ENDED the fight above half HP on every")
    print("   living body. The columns must separate: a fresh party lets")
    print("   little go; a spent one keeps its relief-escape.)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=300,
                    help="fights per row (the 2026-08-08 probes used 300)")
    ap.add_argument("--legacy", action="store_true",
                    help="measure the PRE-rebalance rules instead (the "
                         "before column: FLEE_BONUS, STA-only weighting, "
                         "the winding-down half band)")
    ap.add_argument("--part", choices=("rows", "state"), default=None,
                    help="run one readout only (default: both)")
    args = ap.parse_args()
    if args.part in (None, "rows"):
        bench_rows(args.trials, args.legacy)
    if args.part in (None, "state"):
        bench_state(args.trials, args.legacy)


if __name__ == "__main__":
    main()
