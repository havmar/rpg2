"""Equal-cost benchmark for the point economy (levelling session A).

THE question the 2026-07-16 design asks the sims: do different ways of
spending the SAME banked points buy comparable combat value? Reference
frames at L4 / L8 / L14; each COLUMN is one whole-budget spending policy
over the frame's (L-1) x SKILL_POINTS_PER_LEVEL points; each ROW is a
fixed suite:

  room  -- one full at-level generated room (bench_quests' chassis), win%
  site  -- one at-level generated site under the sim policy, clear%
  duel  -- the soldiery ladder's nearest row (ref_pack of it), win%

Columns (every one spends the full budget, leftovers banked):
  reference -- doctrine v2: pools to the old curve, training to 3 (2n),
               proficiency (n), training to cap. The old default build.
  training  -- training first (to cap), then proficiency, then pools.
  pools     -- pools first (to the +10 cap, spread evenly), then training,
               then proficiency.
  weapon    -- proficiency first, then training to 3, then pools.
  saves     -- Bulwark + War-Breath + Berserk (6 points), then doctrine.
  strikes   -- First Blood + Rage (4 points), then doctrine.

ACCEPTANCE BAND (plan.md): combat options of equal point cost land within
~+-10 clear-rate points of the column MEDIAN; wildly-different-at-same-
price is the failure to catch. Perfect balance is explicitly NOT the bar
(equipment and party context may weigh in). Utility buys (storyteller,
survivalist, field medic) are measured on their own axis: the exact-odds
table at the bottom (they buy nights and lives, not clear rate).

Session B grew this file with the warrior-moves matchup block (a doctrine
duo with a granted katana repertoire vs one without) and the disarm-move-
vs-telekinesis-rank-1 pricing check; session C adds the alchemist career
column.

Run:  python bench_abilities.py [--trials N] [--frame 8]
"""

import argparse
import random
import statistics
from collections import Counter

import rpg
from sites import FOES, Site, make_foe, run_site
from bench_quests import pools_for
from quests import build_room, build_site_rooms, room_budget

FRAMES = (4, 8, 14)
# The duel row per frame: the soldiery ladder's nearest annotation.
DUEL_ROW = {4: "soldier", 8: "veteran", 14: "blademaster"}
_NO_LOG: list[str] = []


def _base_hero(rng: random.Random, name: str, level: int) -> rpg.Entity:
    """A frame hero with the GIFTS ZEROED (no rolled archetype seed, no
    wizardhood) so the columns measure only what the points bought, and
    quality steel (the katana, the benches' pick) in hand."""
    h = rpg.make_human(rng, name)
    h.school = ""
    h.spells = {}
    h.abilities = set()
    h.alchemy = 0
    h.moves = set()
    if h.weapon is not None and h.weapon.power_bonus:
        h.power -= h.weapon.power_bonus         # the staff goes back
        h.cur_power = min(h.cur_power, h.power)
    h.weapon = rpg.WEAPONS["katana"]
    h.level = level
    h.skill_points = (level - 1) * rpg.SKILL_POINTS_PER_LEVEL
    return h


def _pools_to(h: rpg.Entity, target: int) -> None:
    """Spread pool buys evenly (hp, sta, power, hp, ...) toward `target`
    bought per pool."""
    for _ in range(3 * target):
        kind = min(rpg.POOL_KINDS, key=lambda k: h.pool_bought.get(k, 0))
        if h.pool_bought.get(kind, 0) >= min(target, rpg.POOL_BUY_CAP):
            break
        if h.skill_points < 1 or not rpg.buy_pool(h, kind, _NO_LOG):
            break
        _NO_LOG.clear()


def _training_to(h: rpg.Entity, cap: int) -> None:
    while (h.training < cap
           and h.skill_points >= rpg.training_cost(h.training)
           and rpg.train_combat_once(h, _NO_LOG)):
        _NO_LOG.clear()


def _prof_to(h: rpg.Entity, cap: int) -> None:
    while (h.proficiency.get(h.weapon.name, 0) < cap
           and h.skill_points >= h.proficiency.get(h.weapon.name, 0) + 1
           and rpg.train_proficiency(h, _NO_LOG)):
        _NO_LOG.clear()


def _learn(h: rpg.Entity, *names: str) -> None:
    for name in names:
        rpg.learn_ability(h, name, _NO_LOG)
        _NO_LOG.clear()


def _doctrine(h: rpg.Entity) -> None:
    """Doctrine v2's spending order on whatever points remain."""
    _pools_to(h, min((h.level - 1) // rpg.POOL_GROWTH_LEVELS,
                     rpg.POOL_BUY_CAP))
    _training_to(h, 3)
    _prof_to(h, rpg.PROFICIENCY_MAX)
    _training_to(h, rpg.TRAINING_MAX)


COLUMNS = {
    "reference": _doctrine,
    "training": lambda h: (_training_to(h, rpg.TRAINING_MAX),
                           _prof_to(h, rpg.PROFICIENCY_MAX),
                           _pools_to(h, rpg.POOL_BUY_CAP)),
    "pools": lambda h: (_pools_to(h, rpg.POOL_BUY_CAP),
                        _training_to(h, rpg.TRAINING_MAX),
                        _prof_to(h, rpg.PROFICIENCY_MAX)),
    "weapon": lambda h: (_prof_to(h, rpg.PROFICIENCY_MAX),
                         _training_to(h, 3),
                         _pools_to(h, rpg.POOL_BUY_CAP),
                         _training_to(h, rpg.TRAINING_MAX)),
    "saves": lambda h: (_learn(h, "bulwark", "war_breath", "berserk"),
                        _doctrine(h)),
    "strikes": lambda h: (_learn(h, "first_blood", "rage"),
                          _doctrine(h)),
}


def _column_duo(column: str, level: int, rng: random.Random) -> list:
    names = rng.sample(rpg.NAMES, 2)
    duo = [_base_hero(rng, n, level) for n in names]
    for h in duo:
        COLUMNS[column](h)
    return duo


def _row_room(column: str, level: int, rng: random.Random) -> bool:
    pool = rng.choice(pools_for(level))
    kinds = build_room(room_budget(level, 1.0), pool, rng, final=True)
    party = _column_duo(column, level, rng)
    foes = [make_foe(k, i + 1, rng) for i, k in enumerate(kinds)]
    log: list[str] = []
    rpg.sim_fight(party, foes, rng, log)
    return (any(h.alive for h in party)
            and not any(f.alive for f in foes))


def _row_site(column: str, level: int, rng: random.Random) -> bool:
    pool = rng.choice(pools_for(level))
    n_rooms = rng.choices((1, 2, 3), weights=(20, 40, 40))[0]
    rooms = tuple((rn, tuple(kinds)) for rn, kinds
                  in build_site_rooms(level, n_rooms, pool, rng))
    site = Site(key="bench", level=level, rooms=rooms,
                quest_line="site cleared", spawn_phrase="{n} foes",
                abandon_line="abandoned.", intro="")
    party = _column_duo(column, level, rng)
    log: list[str] = []
    run_site(site, party, rpg.Clock(), rpg.Purse(), rng, log,
             auto_train=False)
    return any("QUEST COMPLETE" in line for line in log)


def _row_duel(column: str, level: int, rng: random.Random) -> bool:
    spec = FOES[DUEL_ROW[level]]
    party = _column_duo(column, level, rng)
    foes = [make_foe(DUEL_ROW[level], i + 1, rng)
            for i in range(spec.ref_pack)]
    log: list[str] = []
    rpg.sim_fight(party, foes, rng, log)
    return (any(h.alive for h in party)
            and not any(f.alive for f in foes))


ROWS = {"room": _row_room, "site": _row_site, "duel": _row_duel}


def bench_frame(level: int, trials: int) -> None:
    budget = (level - 1) * rpg.SKILL_POINTS_PER_LEVEL
    duel = FOES[DUEL_ROW[level]]
    print(f"\n--- frame L{level} ({budget} points a head; duel: "
          f"{duel.ref_pack}x {duel.display} L{duel.level}; "
          f"{trials} trials/cell) ---")
    header = f"{'row':<8}" + "".join(f"{c:>11}" for c in COLUMNS)
    print(header + f"{'median':>9}{'flags':>7}")
    for row_i, (row_name, row_fn) in enumerate(ROWS.items()):
        rates = {}
        for column in COLUMNS:
            rng = random.Random(31337 + level * 100 + row_i)
            wins = sum(row_fn(column, level, rng) for _ in range(trials))
            rates[column] = 100 * wins / trials
        med = statistics.median(rates.values())
        flags = sum(1 for v in rates.values() if abs(v - med) > 10)
        line = f"{row_name:<8}" + "".join(f"{rates[c]:>10.1f}%"
                                          for c in COLUMNS)
        print(line + f"{med:>8.1f}%{flags or '':>7}")
    print("  (flags = columns landing outside +-10 of the row median -- "
          "the acceptance band)")


def _grant_repertoire(h: rpg.Entity) -> None:
    """Grant a katana fighter a full suited repertoire FOR FREE (points set
    aside), so the block measures what the moves BUY in the fight, isolated
    from their point cost -- the ceiling, priced separately below."""
    keep = h.skill_points
    h.skill_points = 99
    rpg.autolearn_moves(h, _NO_LOG)
    _NO_LOG.clear()
    h.skill_points = keep


def _moves_duo(level: int, rng: random.Random, with_moves: bool) -> list:
    names = rng.sample(rpg.NAMES, 2)
    duo = [_base_hero(rng, n, level) for n in names]
    for h in duo:
        _doctrine(h)
        if with_moves:
            _grant_repertoire(h)
    return duo


def _run_room(duo: list, level: int, rng: random.Random) -> bool:
    pool = rng.choice(pools_for(level))
    kinds = build_room(room_budget(level, 1.0), pool, rng, final=True)
    foes = [make_foe(k, i + 1, rng) for i, k in enumerate(kinds)]
    rpg.sim_fight(duo, foes, rng, _NO_LOG)
    _NO_LOG.clear()
    return any(h.alive for h in duo) and not any(f.alive for f in foes)


def _run_duel(duo: list, level: int, rng: random.Random) -> bool:
    spec = FOES[DUEL_ROW[level]]
    foes = [make_foe(DUEL_ROW[level], i + 1, rng) for i in range(spec.ref_pack)]
    rpg.sim_fight(duo, foes, rng, _NO_LOG)
    _NO_LOG.clear()
    return any(h.alive for h in duo) and not any(f.alive for f in foes)


def moves_matchup(trials: int) -> None:
    """The warrior-moves matchup block (session B): the reference doctrine duo
    with a full katana repertoire GRANTED vs the same duo without one, on the
    room and duel rows. The gap is what the repertoire buys in the fight (the
    riders + the flow refund); the moves cost points too (leftover on the
    doctrine, or a pool shaved), so this is the value CEILING, not a free win.
    Acceptance: a repertoire should read as a modest, positive edge -- the
    riders are small and near-equivalent by design, the value is legibility +
    the flow refund, not a power spike."""
    print(f"\n--- the warrior moves: doctrine duo, repertoire GRANTED vs "
          f"none ({trials} trials/cell) ---")
    print(f"{'frame':<8}{'room base':>11}{'room +moves':>13}"
          f"{'duel base':>11}{'duel +moves':>13}{'repertoire':>13}")
    for level in FRAMES:
        rates = {}
        for tag, rowfn in (("room", _run_room), ("duel", _run_duel)):
            for wm in (False, True):
                rng = random.Random(9001 + level)
                wins = sum(rowfn(_moves_duo(level, rng, wm), level, rng)
                           for _ in range(trials))
                rates[(tag, wm)] = 100 * wins / trials
        # a sample repertoire (deterministic: what a katana fighter learns)
        sample = _base_hero(random.Random(1), "x", level)
        _doctrine(sample)
        _grant_repertoire(sample)
        rep = ",".join(sorted(sample.moves)) or "-"
        print(f"L{level:<7}{rates[('room', False)]:>10.1f}%"
              f"{rates[('room', True)]:>12.1f}%{rates[('duel', False)]:>10.1f}%"
              f"{rates[('duel', True)]:>12.1f}%   {rep}")
    print("  (repertoire = the suited katana moves the fighter is granted at "
          "that frame)")


def disarm_pricing(trials: int) -> None:
    """Disarm-the-move vs telekinesis rank 1 (the cast disarm) -- the plan's
    equal-price check: both are ~1 point and both strip a foe's weapon (the
    move on a decisive melee hit, the cast on a won opposed exchange). Measured
    on the L8 soldiery duel (armed foes). They should read comparably; the
    move is melee-gated and free of Power, the cast reaches at range and costs
    Power -- different bills, similar value."""
    level = 8
    print(f"\n--- disarm-the-move vs telekinesis rank 1 (L{level} armed-foe "
          f"duel, {trials} trials) ---")

    def duo_move(rng):
        duo = [_base_hero(rng, n, level) for n in rng.sample(rpg.NAMES, 2)]
        for h in duo:
            _doctrine(h)
            h.moves.add("disarm")      # the ~1-point move
        return duo

    def duo_tk(rng):
        duo = [_base_hero(rng, n, level) for n in rng.sample(rpg.NAMES, 2)]
        for h in duo:
            _doctrine(h)
            h.school = "telekinesis"   # rank-1 telekinesis = the disarm only
            h.spells = {"telekinesis": 1}
        return duo

    for label, builder in (("disarm move", duo_move),
                           ("telekinesis 1", duo_tk),
                           ("plain doctrine", None)):
        rng = random.Random(4242 + level)
        wins = sum(_run_duel((builder(rng) if builder
                              else _moves_duo(level, rng, False)), level, rng)
                   for _ in range(trials))
        print(f"  {label:<16}{100 * wins / trials:>6.1f}% duel win")


def utility_axis() -> None:
    """The utility buys, on their own axis: exact 2d6 odds per stat (they
    buy nights, Power and lives, not clear rate -- plan.md)."""
    def p_2d6_at_least(n: int) -> float:
        ways = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6,
                8: 5, 9: 4, 10: 3, 11: 2, 12: 1}
        return sum(w for v, w in ways.items() if v >= n) / 36

    print("\n--- the utility abilities (exact odds; measured on their own "
          "axis, not the matrix) ---")
    print(f"{'stat':<6}{'storyteller (duo)':>19}{'storyteller (4)':>17}"
          f"{'survivalist':>13}{'field medic':>13}")
    for stat in range(3, 7):
        duo = p_2d6_at_least(rpg.STORYTELLER_DC - stat)
        four = p_2d6_at_least(rpg.STORYTELLER_DC + 1 - stat)
        surv = p_2d6_at_least(rpg.SURVIVALIST_DC - stat)
        medic = p_2d6_at_least(rpg.FIELD_MEDIC_DC - stat)
        print(f"{stat:<6}{100 * duo:>18.1f}%{100 * four:>16.1f}%"
              f"{100 * surv:>12.1f}%{100 * medic:>12.1f}%")
    print("  (storyteller: +1 Power above max party-wide per made night; "
          "survivalist: a wilds camp\n   becomes a tavern night, visitors "
          "halved; field medic: one true death a day -> a Down)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=400)
    ap.add_argument("--frame", type=int, choices=FRAMES, default=None,
                    help="bench a single frame (default: all three)")
    args = ap.parse_args()
    for level in ([args.frame] if args.frame else FRAMES):
        bench_frame(level, args.trials)
    moves_matchup(args.trials)
    disarm_pricing(args.trials)
    utility_axis()


if __name__ == "__main__":
    main()
