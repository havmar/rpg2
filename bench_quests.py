"""Quest-generator benchmark: is generated content's LEVEL honest, and does
a generated WORLD actually carry a career?

Three parts (each is a calibration target for quests.py's threat math --
THREAT_BASE, ROOM_SHARES, BOSS_ALLOWANCE are tuned against this file):

1. ENCOUNTERS: build_room at share 1.0 (a full at-level room, the generated
   sibling of a bestiary reference encounter) vs the reference duo at the
   target level and two either side, across the whole 1-20 line, pools drawn
   from the real quest templates. Target: the same band the calibrated
   catalog rows sit in (at-level win roughly 55-85%, the -2 column clearly
   worse) -- so a generated room speaks the same difficulty language as a
   hand-picked one.

2. SITES: a full generated site (1-3 rooms, rising shares) vs the at-level
   duo under the usual sim policy (pauses answered, potions at rests, one
   return trip to a fled room). Target: at-level clear in the ballpark of
   the hand-built hideout-at-level experience (~50-70%), the -2 column a
   real wall.

3. CAREERS: a fresh duo in a fresh generated world plays the board to the
   level cap or the grave -- take the best reachable quest (highest level
   <= party level + 1, else the lowest posted), run its sites via run_site,
   camp up between sites, buy potions and quality steel when the gold is
   there, spend points training-first (the sims' usual understatement of a
   real player). Reports how many careers reach the cap, die, or run out of
   board, and the pace (days, quests) of the ones that make it.

Run:  python bench_quests.py [--trials N] [--careers N] [--part enc|site|career]
"""

from __future__ import annotations

import argparse
import random
from collections import Counter

import rpg
from rpg import LEVEL_CAP
from sites import FOES, make_foe, run_site
from bench_bestiary import reference_hero
from quests import (TEMPLATES, EPIC_TEMPLATES, template_band, build_room,
                    build_site_rooms, room_budget, generate_world,
                    quest_to_sites, quest_xp_total, xp_to_cap)

ALL_TEMPLATES = [t for table in TEMPLATES.values() for t in table]
ALL_TEMPLATES += EPIC_TEMPLATES


def pools_for(level: int) -> list[tuple[str, ...]]:
    fitting = [t["pool"] for t in ALL_TEMPLATES
               if template_band(t)[0] <= level <= template_band(t)[1]]
    return fitting or [t["pool"] for t in ALL_TEMPLATES
                       if "warlord" in t["pool"]]


def bench_encounters(trials: int) -> None:
    print(f"\n--- generated ENCOUNTERS: one full at-level room (share 1.0) "
          f"vs the reference duo ({trials} trials/cell) ---")
    print(f"{'room L':<8}{'win-2':>8}{'win@L':>8}{'win+2':>8}"
          f"{'fled@L':>8}{'wipe@L':>8}{'down@L':>8}")
    for level in range(1, LEVEL_CAP + 1):
        cells = {}
        at_level = {}
        for off in (-2, 0, 2):
            party_l = level + off
            if party_l < 1 or party_l > LEVEL_CAP:
                cells[off] = None
                continue
            rng = random.Random(9000 + level * 10 + off)
            counts: Counter[str] = Counter()
            downs = 0
            for _ in range(trials):
                pool = rng.choice(pools_for(level))
                kinds = build_room(room_budget(level, 1.0), pool, rng,
                                   final=True)
                names = rng.sample(rpg.NAMES, 2)
                party = [reference_hero(rng, n, party_l) for n in names]
                foes = [make_foe(k, i + 1, rng) for i, k in enumerate(kinds)]
                log: list[str] = []
                result = rpg.sim_fight(party, foes, rng, log)
                downs += any("goes down" in line for line in log)
                if result == "fled":
                    counts["fled"] += 1
                elif not any(h.alive for h in party):
                    counts["wipe"] += 1
                elif any(f.alive for f in foes):
                    counts["stall"] += 1
                else:
                    counts["win"] += 1
            cells[off] = 100 * counts["win"] / trials
            if off == 0:
                at_level = {"fled": 100 * counts["fled"] / trials,
                            "wipe": 100 * counts["wipe"] / trials,
                            "down": 100 * downs / trials}
        def fmt(v):
            return f"{v:>7.1f}%" if v is not None else f"{'-':>8}"
        print(f"{level:<8}{fmt(cells[-2])}{fmt(cells[0])}{fmt(cells[2])}"
              f"{at_level['fled']:>7.1f}%{at_level['wipe']:>7.1f}%"
              f"{at_level['down']:>7.1f}%")


def run_generated_site(level: int, party_l: int, rng: random.Random) -> dict:
    """One generated site vs a fresh reference duo at party_l, under the
    normal sim policy (the same loop tune.py runs the hand-built sites
    through)."""
    from sites import Site
    pool = rng.choice(pools_for(level))
    n_rooms = rng.choices((1, 2, 3), weights=(20, 40, 40))[0]
    rooms = tuple((rn, tuple(kinds)) for rn, kinds
                  in build_site_rooms(level, n_rooms, pool, rng))
    site = Site(key="bench", level=level, rooms=rooms,
                quest_line="site cleared", spawn_phrase="{n} foes",
                abandon_line="abandoned.", intro="")
    names = rng.sample(rpg.NAMES, 2)
    party = [reference_hero(rng, n, party_l) for n in names]
    clock, purse = rpg.Clock(), rpg.Purse()
    log: list[str] = []
    run_site(site, party, clock, purse, rng, log)
    return {
        "clear": any("QUEST COMPLETE" in line for line in log),
        "wipe": not any(h.alive for h in party),
        "down": any("goes down" in line for line in log),
    }


def bench_sites(trials: int) -> None:
    print(f"\n--- generated SITES: full site (1-3 rooms) vs the reference "
          f"duo, sim policy ({trials} trials/cell) ---")
    print(f"{'site L':<8}{'clear-2':>9}{'clear@L':>9}{'clear+2':>9}"
          f"{'wipe@L':>8}{'down@L':>8}")
    for level in range(1, LEVEL_CAP + 1):
        cells = {}
        at_level = {}
        for off in (-2, 0, 2):
            party_l = level + off
            if party_l < 1 or party_l > LEVEL_CAP:
                cells[off] = None
                continue
            rng = random.Random(7000 + level * 10 + off)
            clears = wipes = downs = 0
            for _ in range(trials):
                r = run_generated_site(level, party_l, rng)
                clears += r["clear"]
                wipes += r["wipe"]
                downs += r["down"]
            cells[off] = 100 * clears / trials
            if off == 0:
                at_level = {"wipe": 100 * wipes / trials,
                            "down": 100 * downs / trials}
        def fmt(v):
            return f"{v:>8.1f}%" if v is not None else f"{'-':>9}"
        print(f"{level:<8}{fmt(cells[-2])}{fmt(cells[0])}{fmt(cells[2])}"
              f"{at_level['wipe']:>7.1f}%{at_level['down']:>7.1f}%")


# --------------------------------------------------------------------------- #
# The career sim
# --------------------------------------------------------------------------- #

CAREER_MAX_DAYS = 600           # safety valve
CAREER_REST_TARGET = 0.8        # camp until everyone is at this HP fraction
CAREER_REST_CAP = 14            # ...but never more nights than this at once
POTION_STOCK = 2                # buy up to this many of each kind per hero


def _allocate_points(party, log) -> None:
    """Spend banked skill points the way the bench reference does (monotone:
    training to 3, katana proficiency to 3, training to 5) -- run_site's
    greedy training-only spend leaves a career duo fighting two or three
    levels below its sheet."""
    for h in party:
        if h.dead:
            continue
        while h.training < 3 and rpg.train_combat_once(h, log):
            pass
        if (h.weapon is not None and h.weapon.quality
                and not h.weapon_broken):
            while (h.proficiency.get(h.weapon.name, 0) < rpg.PROFICIENCY_MAX
                   and rpg.train_proficiency(h, log)):
                pass
        while h.training < rpg.TRAINING_MAX and rpg.train_combat_once(h, log):
            pass


def _shop_and_rest(party, clock, purse, rng, log) -> None:
    """The between-sites policy: camp up to strength, then spend gold -- one
    potion of each kind per hero, then quality steel (the katana, the
    benches' pick), then potion stockpiles. Crude on purpose: the sims
    understate the player."""
    nights = 0
    living = [h for h in party if not h.dead]
    while (nights < CAREER_REST_CAP
           and any(h.hp < h.max_hp * CAREER_REST_TARGET for h in living)):
        rpg.long_rest(party, clock, log)
        nights += 1
    if nights == 0:
        rpg.long_rest(party, clock, log)    # at least sleep off the day
    katana = rpg.WEAPONS["katana"]
    for stock in (1, POTION_STOCK):
        for h in living:
            for kind in rpg.STOCKED_POTION_KINDS:
                while (h.items.get(kind, 0) < stock
                       and purse.gold >= rpg.POTION_PRICE):
                    rpg.buy_potion(h, purse, kind, log)
        if stock == 1:      # steel outranks the second potion of a kind
            for h in living:
                needs_steel = (h.weapon is None or h.weapon_broken
                               or (not h.weapon.quality))
                if needs_steel and purse.gold >= katana.value:
                    rpg.buy_weapon(h, purse, "katana", log)
    _allocate_points(party, log)


def _pick_quest(world, done: set[str], party_level: int):
    """The board policy: the best-paying quest at least one level BELOW the
    party (the intended arc -- bank levels and steel on work you outmatch,
    step up only when the board forces it; an early draft that always took
    party level + 1 died at median level 2, the barrow-on-day-one mistake).
    If nothing sits below, the lowest-level quest posted. Returns
    (quest, forced_up)."""
    open_q = [q for q in world["quests"].values()
              if q["status"] == "open" and q["id"] not in done]
    if not open_q:
        return None, False
    for depth in (2, 1):        # grind two below when the board allows it,
                                # one below when it doesn't
        safe = [q for q in open_q if q["level"] <= max(1, party_level - depth)]
        if safe:
            return max(safe, key=lambda q: q["level"]), False
    q = min(open_q, key=lambda q: q["level"])
    return q, q["level"] > party_level + 1


def _rest_up(party, clock, log) -> None:
    """Camp until fit to fight (HP back to CAREER_REST_TARGET, bounded).
    The career sim rests BETWEEN ROOMS, not just between sites: the game's
    own tuning principle says the player can camp after any encounter and
    reads the STA math before every door -- run_site's press-on-depleted
    pacing is the single-site experience, not a career's."""
    living = [h for h in party if not h.dead]
    nights = 0
    while (nights < CAREER_REST_CAP
           and any(h.hp < h.max_hp * CAREER_REST_TARGET or h.cur_sta < h.sta
                   for h in living)):
        rpg.long_rest(party, clock, log)
        nights += 1


def career_run_site(site, party, clock, purse, rng, log) -> bool:
    """One site, room by room, camping up before every door (see _rest_up).
    A fled room gets one rested return trip, then the site is abandoned.
    Returns True on a full clear (pays the site's lump like run_site)."""
    foe_n = 0
    for room_i, (room_name, roster) in enumerate(site.rooms):
        _rest_up(party, clock, log)
        attempts = 0
        foes = None
        while True:
            attempts += 1
            day_before = clock.day
            if foes is None:
                foes = []
                for kind in roster:
                    foe_n += 1
                    foes.append(make_foe(kind, foe_n, rng))
            living = [h for h in party if not h.dead]
            for h in living:
                rpg.start_fight(h, log)
            result = rpg.sim_fight(living, foes, rng, log)
            if rpg.party_wiped(party, log) or any(h.dead for h in party):
                return False
            if result == "fled" or any(f.alive for f in foes):
                if attempts >= rpg.SIM_MAX_ROOM_ATTEMPTS:
                    return False        # abandoned
                _rest_up(party, clock, log)
                rpg.auto_use_potions_on_rest(
                    [h for h in party if h.alive], log)
                foes = rpg.refresh_foes_after_retreat(
                    foes, clock.day - day_before)
                continue
            break
        rpg.award_xp(party, site.encounter_xp, log, "encounter")
        rpg.roll_loot(party, purse, rng, log)
    rpg.award_quest(party, purse, site.quest_gold, site.quest_xp,
                    log, site.quest_line)
    return True


def run_career(seed: int) -> dict:
    """One whole playthrough under the batch policies. Ends at the level
    cap, the grave, an empty board, or the day-cap safety valve."""
    rng = random.Random(seed)
    world = generate_world(rng.randrange(1 << 30))
    party = rpg.make_party(rng)
    clock, purse = rpg.Clock(), rpg.Purse()
    done: set[str] = set()          # cleared or abandoned: never retaken
    quests_cleared = 0
    forced_up = 0
    log: list[str] = []

    def party_level() -> int:
        return max(h.level for h in party if not h.dead)

    while True:
        if any(h.dead for h in party):
            # First true death ends the career (session play's PC rule, and
            # a halved duo against duo-baseline content is dead anyway --
            # the party-size sweep's 15%-solo-clear number).
            return {"end": "died", "level": max(h.level for h in party),
                    "days": clock.day, "quests": quests_cleared,
                    "forced_up": forced_up}
        if party_level() >= LEVEL_CAP:
            return {"end": "capped", "level": LEVEL_CAP, "days": clock.day,
                    "quests": quests_cleared, "forced_up": forced_up}
        if clock.day >= CAREER_MAX_DAYS:
            return {"end": "timeout", "level": party_level(),
                    "days": clock.day, "quests": quests_cleared,
                    "forced_up": forced_up}
        quest, was_forced = _pick_quest(world, done, party_level())
        if quest is None:
            return {"end": "no_content", "level": party_level(),
                    "days": clock.day, "quests": quests_cleared,
                    "forced_up": forced_up}
        forced_up += was_forced
        cleared_all = True
        for site in quest_to_sites(quest):
            log.clear()
            cleared = career_run_site(site, party, clock, purse, rng, log)
            if any(h.dead for h in party):
                cleared_all = False     # a death ends the career (above)
                break
            if not cleared:
                cleared_all = False     # fled out / abandoned: drop the quest
                break
            _shop_and_rest(party, clock, purse, rng, log)
        quest["status"] = "done" if cleared_all else quest["status"]
        done.add(quest["id"])
        quests_cleared += cleared_all


def bench_careers(n: int) -> None:
    print(f"\n--- CAREERS: fresh duo, fresh world, play the board to "
          f"L{LEVEL_CAP} or the grave ({n} careers) ---")
    results = [run_career(31337 + i) for i in range(n)]
    ends = Counter(r["end"] for r in results)
    capped = [r for r in results if r["end"] == "capped"]
    died = [r for r in results if r["end"] == "died"]
    print(f"reached L{LEVEL_CAP}: {100 * len(capped) / n:.1f}%   "
          f"died: {100 * len(died) / n:.1f}%   "
          f"board exhausted: {100 * ends['no_content'] / n:.1f}%   "
          f"timeout: {100 * ends['timeout'] / n:.1f}%")
    marks = [5, 8, 11, 14, 17, LEVEL_CAP]
    reach = "   ".join(
        f"L{m}: {100 * sum(1 for r in results if r['level'] >= m) / n:.0f}%"
        for m in marks)
    print(f"careers reaching at least   {reach}")
    if capped:
        days = sorted(r["days"] for r in capped)
        qs = sorted(r["quests"] for r in capped)
        print(f"the capped: median {days[len(days) // 2]} days, "
              f"{qs[len(qs) // 2]} quests cleared "
              f"(days p10-p90: {days[len(days) // 10]}-"
              f"{days[9 * len(days) // 10]})")
    if died:
        lv = sorted(r["level"] for r in died)
        print(f"the dead: median level {lv[len(lv) // 2]} "
              f"(p10-p90: {lv[len(lv) // 10]}-{lv[9 * len(lv) // 10]})")
    stalls = sum(r["forced_up"] for r in results)
    print(f"forced-up picks (nothing within party level +1 on the board): "
          f"{stalls / n:.2f} per career")
    total = sum(quest_xp_total(q) for q in
                generate_world(1)["quests"].values())
    print(f"(a fresh world posts ~{total} XP; a duo needs {xp_to_cap(1)} "
          f"to L{LEVEL_CAP})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=300,
                    help="trials per cell for the encounter/site parts")
    ap.add_argument("--careers", type=int, default=200)
    ap.add_argument("--part", choices=("enc", "site", "career"), default=None,
                    help="run one part only (default: all three)")
    args = ap.parse_args()
    if args.part in (None, "enc"):
        bench_encounters(args.trials)
    if args.part in (None, "site"):
        bench_sites(args.trials)
    if args.part in (None, "career"):
        bench_careers(args.careers)


if __name__ == "__main__":
    main()
