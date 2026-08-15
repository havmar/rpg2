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

2. SITES: a whole generated JOB in one place (1-3 encounters on the quest's
   own QUEST_ENCOUNTERS roll since 2026-07-26, rising shares) vs the at-level
   duo under the usual sim policy (pauses answered, potions at rests, one
   return trip to a fled room). Target: at-level clear in the ballpark of
   the hand-built hideout-at-level experience (~50-70%), the -2 column a
   real wall.

3. CAREERS: a fresh duo in a fresh generated world plays the board to the
   level cap or the grave -- take the best reachable quest (highest level
   <= party level + 1, else the lowest posted), fight its encounters,
   camp up between them, collect the QUEST's turn-in lump when the last
   place falls, buy potions and quality steel when the gold is
   there, spend points on doctrine v2 (rpg.autospend_points -- the sims'
   usual understatement of a
   real player). Reports how many careers reach the cap, die, or run out of
   board, and the pace (days, quests) of the ones that make it.

   Since 2026-07-26 (slice 2) the career also runs the BOARD'S CLOCK between
   jobs (`run_board_clock`): postings expire, settlements refill, and the
   turn-in is paid in its band. The sim has no travel layer, so its jobs land
   faster than a played one's -- read the band split with that caveat
   (benchlog), and read "board exhausted: 0%" as the slice's real acceptance.

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
                    quest_to_sites, quest_xp_posted, xp_to_cap,
                    QUEST_ENCOUNTERS, QUEST_PAY_BANDS,
                    settlements, expire_settlement_board,
                    refresh_settlement_board, refresh_deliveries,
                    quest_band, quest_days_left, quest_expired)

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
    # A whole JOB in one place: the quest's own encounter roll (2026-07-26),
    # so this row measures what the board actually posts.
    n_rooms = rng.choices(*QUEST_ENCOUNTERS)[0]
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
    print(f"\n--- generated JOBS: a whole quest (1-3 encounters) in one "
          f"place vs the reference duo, sim policy ({trials} trials/cell) ---")
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
CAREER_HEALER_LOAD = 2          # total wound severity that makes the town
                                # healer worth a day and the fee (slice 3b)
POTION_STOCK = 2                # buy up to this many of each kind per hero


def _allocate_points(party, log) -> None:
    """Spend banked skill points the way the bench reference does --
    doctrine v2 (rpg.autospend_points): pools to the old odd-level curve,
    then training to 3 (2n), then quality proficiency/school, then
    training to the cap."""
    for h in party:
        if h.dead:
            continue
        rpg.autospend_points(h, log)


def _fit_to_fight(h) -> bool:
    """Rested enough to walk through a door: CAREER_REST_TARGET of the pool,
    or the WOUND CEILING when wounds have put that out of reach (2026-07-26,
    slice 3b).

    Reading the target off `max_hp` alone was a harness bug the moment wounds
    shipped: a hero whose ceiling sits below the target can never satisfy it,
    so the rest loops burned their whole CAREER_REST_CAP before every single
    door and the career sim measured a calendar, not a game. The engine's own
    `camp --heal` stops at the ceiling for exactly this reason."""
    return h.hp >= min(h.max_hp * CAREER_REST_TARGET, h.hp_ceiling)


def _shop_and_rest(party, clock, purse, rng, log) -> None:
    """The between-QUESTS policy: this is the town step, so it camps in a BED
    (the treatment ladder's free rung -- one wound severity a night), pays the
    town healer when the party is carrying real damage and the purse can
    stand it, and then spends gold -- one potion of each kind per hero, then
    quality steel (the katana, the benches' pick), then potion stockpiles.
    Crude on purpose: the sims understate the player."""
    nights = 0
    living = [h for h in party if not h.dead]
    while nights < CAREER_REST_CAP and not all(_fit_to_fight(h)
                                               for h in living):
        rpg.long_rest(party, clock, log, bed=True)
        nights += 1
    if nights == 0:
        rpg.long_rest(party, clock, log, bed=True)  # at least sleep the day
    # The healer, crudely: a career that never buys treatment ratchets its
    # ceilings down to the half-pool floor and stays there, which is not the
    # shipped game -- the ladder exists and a player uses it. One town visit
    # (a day, HEALER_FEE per severity) whenever the load is worth the trip.
    if (sum(h.wound_load for h in living) >= CAREER_HEALER_LOAD
            and purse.gold >= rpg.HEALER_FEE * CAREER_HEALER_LOAD):
        rpg.healer_service(party, purse, "town", log)
        clock.day += rpg.HEALER_DAYS
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


def run_board_clock(world, day: int, rng: random.Random) -> int:
    """The career sim's stand-in for session.board_clock: expire the closed
    windows off every settlement's board and let each settlement refill
    (2026-07-26, slice 2). The sim has no travel layer, so it reads the whole
    world as one board -- and therefore runs the clock on the whole world.
    Returns how many postings expired unfinished.

    IT DELIBERATELY IGNORES THE THREE-DAY RUMOR RADIUS (2026-08-15, Local
    Quest Geography). A played party hears the work within three days' road
    of where it stands; this sim hears all of it, because it does not walk
    anywhere and a radius around a party with no position is meaningless.
    What it DOES see is the sparse boards: a settlement whose activity roll
    came up shut refills to nothing here exactly as it does in play, which
    is why the supply this sim reports fell with that change. Read its
    board numbers as an upper bound on the played supply, never as it."""
    gone = 0
    for s in settlements(world):
        gone += len(expire_settlement_board(world, s, day))
        refresh_settlement_board(world, s, day, rng)
    refresh_deliveries(world, day, rng)
    return gone


def _pick_quest(world, done: set[str], party_level: int, day: int):
    """The board policy: the best-paying quest at least one level BELOW the
    party (the intended arc -- bank levels and steel on work you outmatch,
    step up only when the board forces it; an early draft that always took
    party level + 1 died at median level 2, the barrow-on-day-one mistake).
    If nothing sits below, the lowest-level quest posted. Returns
    (quest, forced_up).

    Since 2026-07-26 the tie-break is the CLOCK: among equally good work the
    sim takes the freshest window. That is the whole extent of its deadline
    play -- it does not hurry, skip a stale job, or read the pay bands, so
    the late turn-ins it eats are the floor a real player sits above (the
    standing tuning principle: the sims understate the player)."""
    open_q = [q for q in world["quests"].values()
              if q["status"] == "open" and q["id"] not in done
              and q.get("kind") != "delivery"   # the career sim has no
                                                # travel layer to carry one
              and not quest_expired(q, day)]
    if not open_q:
        return None, False
    def freshest(q):
        return (q["level"], quest_days_left(q, day) or 0)
    for depth in (2, 1):        # grind two below when the board allows it,
                                # one below when it doesn't
        safe = [q for q in open_q if q["level"] <= max(1, party_level - depth)]
        if safe:
            return max(safe, key=freshest), False
    def stalest(q):
        return (q["level"], -(quest_days_left(q, day) or 0))
    q = min(open_q, key=stalest)
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
           and any(not _fit_to_fight(h) or h.cur_sta < h.sta
                   for h in living)):
        rpg.long_rest(party, clock, log)
        nights += 1


def career_run_site(site, party, clock, purse, rng, log,
                    encounter_xp: int) -> str:
    """One PLACE of a quest, encounter by encounter, camping up before every
    door (see _rest_up). A fled room gets one rested return trip, then the
    place is abandoned. Returns True on a full clear.

    Pay is the QUEST's (2026-07-26): each fight pays `encounter_xp`, flat,
    and the turn-in lump is the caller's to hand over once the whole job is
    done -- a place is no longer a pay grade of its own. Returns "cleared",
    "abandoned", "mercy", or "dead"; Slice 4's mercy is applied here before
    `party_wiped` destroys the Down/dead distinction."""
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
            mercy = rpg.apply_defeat_mercy(
                party, foes, purse, rng, log, participants=living)
            if mercy is not None:
                return "mercy"
            if rpg.party_wiped(party, log) or any(h.dead for h in party):
                return "dead"
            if result == "fled" or any(f.alive for f in foes):
                if attempts >= rpg.SIM_MAX_ROOM_ATTEMPTS:
                    return "abandoned"
                _rest_up(party, clock, log)
                rpg.auto_use_potions_on_rest(
                    [h for h in party if h.alive], log)
                foes = rpg.refresh_foes_after_retreat(
                    foes, clock.day - day_before)
                continue
            break
        rpg.award_xp(party, encounter_xp, log, "encounter")
        rpg.roll_loot(party, purse, rng, log)
    return "cleared"


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
    expired = 0                     # postings the board lost unfinished
    mercies = 0                     # Slice 4 losses the career survived
    bands: Counter[str] = Counter() # what the turn-ins were worth
    clock_day = -1
    log: list[str] = []

    def party_level() -> int:
        return max(h.level for h in party if not h.dead)

    def result(end: str, level: int) -> dict:
        return {"end": end, "level": level, "days": clock.day,
                "quests": quests_cleared, "forced_up": forced_up,
                "expired": expired, "mercies": mercies, "bands": bands,
                "board": sum(1 for q in world["quests"].values()
                             if q["status"] == "open"
                             and not quest_expired(q, clock.day))}

    while True:
        if any(h.dead for h in party):
            # First true death ends the career (session play's PC rule, and
            # a halved duo against duo-baseline content is dead anyway --
            # the party-size sweep's 15%-solo-clear number).
            return result("died", max(h.level for h in party))
        if party_level() >= LEVEL_CAP:
            return result("capped", LEVEL_CAP)
        if clock.day >= CAREER_MAX_DAYS:
            return result("timeout", party_level())
        # The board's clock, run between jobs: the days the last one cost
        # close windows on the ones nobody took, and the settlements post
        # fresh work (session.board_clock's bench sibling).
        if clock.day != clock_day:
            expired += run_board_clock(world, clock.day, rng)
            clock_day = clock.day
        quest, was_forced = _pick_quest(world, done, party_level(), clock.day)
        if quest is None:
            return result("no_content", party_level())
        forced_up += was_forced
        cleared_all = True
        level = quest["level"]
        enc = quest.get("encounters", 1)
        enc_xp = rpg.quest_encounter_xp(level, enc)
        for site in quest_to_sites(world, quest):
            log.clear()
            site_result = career_run_site(
                site, party, clock, purse, rng, log, enc_xp)
            if any(h.dead for h in party):
                cleared_all = False     # a death ends the career (above)
                break
            if site_result == "mercy":
                mercies += 1
                # Left for dead ends the job, not the career. The bench has
                # no travel layer, so this is its return-to-town recovery.
                _shop_and_rest(party, clock, purse, rng, log)
                cleared_all = False
                break
            if site_result != "cleared":
                cleared_all = False     # fled out / abandoned: drop the quest
                break
            _shop_and_rest(party, clock, purse, rng, log)
        if cleared_all and quest["sites"]:
            # Work-done and turn-in in one breath: the career teleports, so
            # the FIELD tranche (unbanded) and the TURN-IN tranche + gold
            # (banded by the day, slice 2) land together -- the same total
            # session play splits across the return leg (2026-08-08). A job
            # carried past the grace keeps its field tranche: only the
            # turn-in tranche and the gold ever expire.
            band = quest_band(quest, clock.day)
            mult = QUEST_PAY_BANDS[band]
            bands[band] += 1
            if mult:
                rpg.award_quest(party, purse,
                                round(rpg.quest_gold(level, enc) * mult),
                                rpg.quest_clear_xp(level, enc)
                                + round(rpg.quest_turnin_xp(level, enc)
                                        * mult),
                                log, quest["name"])
            else:
                # Done, never paid: the field tranche stays banked -- only
                # the turn-in tranche and the gold expire with the window.
                rpg.award_xp(party, rpg.quest_clear_xp(level, enc), log,
                             "the work done")
            quest["status"] = "done" if mult else "lost"
            quests_cleared += bool(mult)
        done.add(quest["id"])


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
    mercy_total = sum(r["mercies"] for r in results)
    mercy_careers = sum(1 for r in results if r["mercies"])
    print(f"defeat mercies: {mercy_total} total "
          f"({mercy_total / n:.2f}/career); "
          f"{100 * mercy_careers / n:.1f}% of careers survived at least one")
    stalls = sum(r["forced_up"] for r in results)
    print(f"forced-up picks (nothing within party level +1 on the board): "
          f"{stalls / n:.2f} per career")
    # The clock (slice 2): the board must churn and must never run dry.
    bands: Counter[str] = Counter()
    for r in results:
        bands.update(r["bands"])
    turned_in = sum(bands.values()) or 1
    split = "  ".join(f"{b}: {100 * bands[b] / turned_in:.0f}%"
                      for b in ("quick", "on time", "late", "expired"))
    print(f"turn-ins by band   {split}")
    boards = sorted(r["board"] for r in results)
    print(f"expired postings: {sum(r['expired'] for r in results) / n:.1f} "
          f"per career; live board at the end: median "
          f"{boards[len(boards) // 2]} open job(s) "
          f"(p10 {boards[len(boards) // 10]})")
    total = sum(quest_xp_posted(q) for q in
                generate_world(1)["quests"].values())
    print(f"(a fresh world SEEDS ~{total} XP and refills as days pass; "
          f"a duo needs {xp_to_cap(1)} to L{LEVEL_CAP})")


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
