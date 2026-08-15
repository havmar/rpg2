"""The weapon generation system (2026-07-28) -- the sp currency and its uses.

The design currency is the SEVERITY-POINT (sp): the exchange rate the
shipped quality four already encode (set rapier = katana = zweihander and
solve -- +1 attack pressure = 2 sp, +1 defense pressure = 2 sp, +1 severity
= 1 sp; all four chassis land at exactly 3 sp, which bench_weapons verified
as "suited, not ranked" long before it had a name). This module owns:

- the sp price table and `weapon_sp` (melee steel only -- ranged cards
  price their severity flats as replaced STR and sit outside the ladder);
- `generate_weapon`, the budgeted generator: a quality CHASSIS plus a
  budget spent under the profile rule (at least two-thirds of the budget on
  the chassis's signature axis, at most one condition rider, at most one
  quirk), true +DEX gated to the legendary tiers;
- the famous ARMORY (`roll_armory`): the world's pregenerated named magic
  weapons, owners drawn from the cast, known from day one -- steal, rob,
  or quest for them, never buy them;
- the legendary SMITHS (`roll_smiths` / `commission_weapon`): three per
  world, each with a cap tier and the pride floor (cap - 1) below which
  they will not work.

The sims never import this module. Worldgen (quests.generate_world) calls
it through a runtime import with a DERIVED rng, so the main worldgen
stream -- and every bench number -- is untouched.

`python weapons.py [--seed N]` prints one world's armory and smiths (the
eyeball check, like karma.py's).
"""

from __future__ import annotations

import argparse
import dataclasses
import random

from rpg import (WEAPONS, Weapon, MASTERWORK_PRICE_MULT, masterwork_of,
                 fit_lines)

# --------------------------------------------------------------------------- #
# The sp price table (rules.md, "The weapon ladder")
# --------------------------------------------------------------------------- #

SP_ATK = 2          # +1 attack pressure (proven by rapier = katana)
SP_SEV = 1          # +1 severity (the base unit)
SP_DEF = 2          # +1 defense pressure (proven by katana = zweihander)
SP_POWER = 2        # +1 max Power while wielded (the staff's focus rate)
SP_STA = 1          # +1 max STA while wielded (the cheap pool axis)
SP_HP = 1           # +2 max HP while wielded (bought in pairs)
SP_DEX = 3          # +1 true DEX -- lands AND defends AND feeds severity
                    # through the margin; legendary tiers only
SP_STR = 2          # +1 true STR -- severity and soak; magic tiers up
SP_LUNGE = 1        # the lunge quirk (once per fight)
RIDER_SP = {        # the condition riders, priced off the measured shipped
    "burn": 1,      # customers (pyromancer ~5 win-% at level; spider ~8)
    "bleed": 1,     # untimed, but the free field stabilize makes it cheap
    "poison": 2,    # untimed -- follows the victim out of the room
    "rime": 2,      # -DEX per landed hit, fight-only (enemy-DEX is dear)
}
RIDER_ROUNDS = {"burn": 2, "bleed": None, "poison": None, "rime": None}

QUALITY_SP = 3      # every quality chassis prices at exactly 3 sp
MAGIC_MIN_SP = 6    # true stat bonuses (the membrane) start here
LEGENDARY_MIN_SP = 8    # true +DEX starts here (the standing warning)
MYTHIC_SP = 10      # the cap: +3 signature-stat equivalents -- half of the
                    # doctrine's stat-doubling comes from the weapon, never
                    # more. There is deliberately NO all-stats artifact.

# The gold curve is superlinear in sp (doubling per point above quality):
# career gold is ~thousands, and a linear price would sell mythic steel for
# lunch money -- and let gold buy DEX-axis power at HP-axis rates.
GOLD_AT_QUALITY = 60


def tier_for_sp(sp: int) -> str:
    if sp >= MYTHIC_SP:
        return "mythic"
    if sp >= LEGENDARY_MIN_SP:
        return "legendary"
    if sp >= MAGIC_MIN_SP:
        return "magic"
    if sp > QUALITY_SP:
        return "masterwork"
    return "plain"


def value_for_sp(sp: int) -> int:
    """Gold value on the superlinear curve, rounded to tens."""
    v = GOLD_AT_QUALITY * (2 ** max(0, sp - QUALITY_SP))
    return int(round(v / 10.0) * 10)


def weapon_sp(w: Weapon) -> int:
    """Price a MELEE weapon in severity-points (the design currency).
    Ranged cards sit outside this function on purpose: a shot's severity
    flat replaces STR entirely, so their numbers are not on this scale."""
    if w.range:
        raise ValueError(f"{w.name} is a ranged card -- not on the sp scale")
    sp = (SP_ATK * w.atk_pressure + SP_SEV * w.severity
          + SP_DEF * w.def_pressure + SP_POWER * w.power_bonus
          + SP_STA * w.sta_bonus + SP_HP * (w.hp_bonus // 2)
          + SP_DEX * w.dex_bonus + SP_STR * w.str_bonus)
    if w.rider:
        sp += RIDER_SP[w.rider] * w.rider_power
    if w.lunge:
        sp += SP_LUNGE
    return sp


# --------------------------------------------------------------------------- #
# The generator
# --------------------------------------------------------------------------- #
# A generated weapon is a quality CHASSIS plus a budget. The profile rule
# keeps identities legible: at least two-thirds of the budget lands on the
# chassis's signature axis, at most one rider, at most one quirk -- a
# generated blade reads as "a rapier, but more so, with one twist", never a
# stat soup. The theoretical max-everything weapon exists only as the
# yardstick that defines the budget (and, by designer call 2026-07-28, is
# NOT in the world -- no McGuffin).

CHASSIS = ("rapier", "katana", "zweihander", "wooden staff")
CHASSIS_WEIGHTS = (5, 5, 5, 2)      # the staff's magic tier is rarer: its
                                    # buyers are casters, a narrower band
CHASSIS_NOUN = {"wooden staff": "staff"}    # display noun for names

# Per-axis caps keep even a mythic budget from flattening a profile.
CAP_DEX = 3         # the mythic signature: +3 on the DEX axis
CAP_STR = 3
CAP_ATK = 3
CAP_SEV = 4
CAP_POWER = 3
CAP_DEF = 1         # one point of guard is a niche, two is a wall

RIDER_CHANCE = 0.6
QUIRK_CHANCE = 0.3
MIDAS_GOLD = 2      # gold per felled foe (capped per fight in the engine)
DARK_KARMA = 2      # sin per felled foe

# Name pools (writing.md: a readable base noun plus one meaningful
# modifier). The generated form is "MODIFIER CHASSIS" -- "ember katana",
# "frost rapier"; famous armory pieces take proper names instead.
RIDER_MODIFIERS = {
    "burn": ("ember", "brand", "cinder"),
    "bleed": ("razor", "thorn", "cruel"),
    "poison": ("viper", "adder", "pale"),
    "rime": ("frost", "winter", "rimed"),
}
AXIS_MODIFIERS = {
    "dex": ("swift", "keen", "quick"),
    "str": ("brute", "iron", "heavy"),
    "atk": ("keen", "true", "sharp"),
    "sev": ("grim", "deep", "butcher's"),
    "power": ("runed", "focused", "bright"),
    "pool": ("old", "trusted", "warded"),
}
QUIRK_MODIFIERS = {"midas": ("gilded",), "dark": ("black",)}


def _signature_axis(chassis: str) -> str:
    return {"rapier": "dex", "katana": "dex",
            "zweihander": "str", "wooden staff": "power"}[chassis]


def generate_weapon(rng: random.Random, sp: int,
                    chassis: str | None = None,
                    name: str | None = None) -> Weapon:
    """One budget-honest magic weapon at exactly `sp` severity-points.

    The spend order: reserve the off-axis share (at most budget minus
    ceil(2/3 budget)) for a rider and/or a quirk, pour the rest into the
    chassis's signature axis (true stats where the tier allows, the steel
    knobs below that), and drip any remainder into filler (severity, STA,
    HP pairs) -- integer sp all the way down, so the total always lands."""
    if sp < MAGIC_MIN_SP or sp > MYTHIC_SP:
        raise ValueError(f"generated weapons run sp {MAGIC_MIN_SP}"
                         f"-{MYTHIC_SP}, not {sp}")
    if chassis is None:
        chassis = rng.choices(CHASSIS, weights=CHASSIS_WEIGHTS)[0]
    base = WEAPONS[chassis]
    budget = sp - QUALITY_SP
    sig_min = -(-2 * budget // 3)           # ceil(2/3): the profile rule
    off_allow = budget - sig_min
    allow_dex = sp >= LEGENDARY_MIN_SP
    allow_stats = sp >= MAGIC_MIN_SP

    adds = dict(atk=0, sev=0, dfs=0, dex=0, strn=0, sta=0, hp=0, power=0)
    rider = ""
    quirk = ""
    spent_off = 0

    # The one rider (off-axis; power 1 across the board -- deeper doses are
    # authored, not rolled).
    if rng.random() < RIDER_CHANCE:
        fitting = [k for k, c in sorted(RIDER_SP.items())
                   if c <= off_allow - spent_off]
        if fitting:
            rider = rng.choice(fitting)
            spent_off += RIDER_SP[rider]

    # The one quirk. Lunge costs a point (melee reach is real power); the
    # economy quirks are free in sp and priced in story instead.
    if rng.random() < QUIRK_CHANCE:
        options = ["midas", "dark"]
        if base.range == 0 and off_allow - spent_off >= SP_LUNGE:
            options.append("lunge")
        quirk = rng.choice(options)
        if quirk == "lunge":
            spent_off += SP_LUNGE

    remaining = budget - spent_off

    def buy(key: str, cost: int, cap: int, n: int | None = None) -> int:
        nonlocal remaining
        bought = 0
        while (remaining >= cost and adds[key] < cap
               and (n is None or bought < n)):
            adds[key] += 1
            remaining -= cost
            bought += 1
        return bought

    axis = _signature_axis(chassis)
    if axis == "dex":
        if allow_dex:
            buy("dex", SP_DEX, CAP_DEX)
        buy("atk", SP_ATK, CAP_ATK)
    elif axis == "str":
        if allow_stats:
            buy("strn", SP_STR, CAP_STR)
        buy("sev", SP_SEV, CAP_SEV)
    else:   # power -- the staff
        buy("power", SP_POWER, CAP_POWER)
        buy("dfs", SP_DEF, CAP_DEF)

    # Filler: whatever the axis caps or granularity left over.
    if axis != "power":
        buy("sev", SP_SEV, CAP_SEV)
    buy("sta", SP_STA, 3)
    buy("hp", SP_HP, 3)             # each unit is +2 max HP
    assert remaining == 0, (chassis, sp, adds, rider, quirk, remaining)

    tier = tier_for_sp(sp)
    durability = 5 if tier == "magic" else 6
    if name is None:
        pools = []
        if rider:
            pools.append(RIDER_MODIFIERS[rider])
        if quirk in QUIRK_MODIFIERS:
            pools.append(QUIRK_MODIFIERS[quirk])
        if adds["dex"] or adds["atk"]:
            pools.append(AXIS_MODIFIERS["dex" if adds["dex"] else "atk"])
        if adds["strn"] or adds["sev"]:
            pools.append(AXIS_MODIFIERS["str" if adds["strn"] else "sev"])
        if adds["power"]:
            pools.append(AXIS_MODIFIERS["power"])
        if not pools:
            pools.append(AXIS_MODIFIERS["pool"])
        modifier = rng.choice(rng.choice(pools))
        name = f"{modifier} {CHASSIS_NOUN.get(chassis, chassis)}"

    parts = []
    if adds["dex"]:
        parts.append(f"+{adds['dex']} DEX")
    if adds["strn"]:
        parts.append(f"+{adds['strn']} STR")
    if adds["atk"]:
        parts.append(f"+{adds['atk']} attack")
    if adds["sev"]:
        parts.append(f"+{adds['sev']} severity")
    if adds["dfs"]:
        parts.append(f"+{adds['dfs']} guard")
    if adds["power"]:
        parts.append(f"+{adds['power']} max Power")
    if adds["sta"]:
        parts.append(f"+{adds['sta']} max STA")
    if adds["hp"]:
        parts.append(f"+{2 * adds['hp']} max HP")
    if rider:
        parts.append({"burn": "its hits burn",
                      "bleed": "its cuts keep bleeding",
                      "poison": "its wounds poison",
                      "rime": "its hits rime the body with frost"}[rider])
    if quirk == "lunge":
        parts.append("its first blow lunges a bound out")
    elif quirk == "midas":
        parts.append(f"each kill pays {MIDAS_GOLD}g")
    elif quirk == "dark":
        parts.append(f"each kill is {DARK_KARMA} sin")
    desc = (f"A {tier} {chassis}, over the plain steel: "
            + "; ".join(parts) + ".")

    return dataclasses.replace(
        base,
        name=name, base=chassis, tier=tier, quality=True,
        durability=durability,
        atk_pressure=base.atk_pressure + adds["atk"],
        severity=base.severity + adds["sev"],
        def_pressure=base.def_pressure + adds["dfs"],
        power_bonus=base.power_bonus + adds["power"],
        dex_bonus=adds["dex"], str_bonus=adds["strn"],
        sta_bonus=adds["sta"], hp_bonus=2 * adds["hp"],
        rider=rider, rider_power=1,
        rider_rounds=RIDER_ROUNDS.get(rider) if rider else None,
        lunge=quirk == "lunge",
        gold_on_kill=MIDAS_GOLD if quirk == "midas" else 0,
        karma_on_kill=DARK_KARMA if quirk == "dark" else 0,
        value=value_for_sp(sp),
        description=desc)


# --------------------------------------------------------------------------- #
# The quest-reward ladder (the pay-band mode; quests.py calls this)
# --------------------------------------------------------------------------- #
# A weapon reward REPLACES the turn-in gold lump (never the XP, never the
# per-encounter shares): the level is the pay grade here as everywhere.

def reward_weapon_for_level(level: int, rng: random.Random,
                            chassis: str | None = None) -> Weapon:
    """The weapon a level-L job may post instead of its gold lump.

    `chassis` fixes what the piece is BUILT ON instead of rolling it (the
    quest board never passes one -- it wants the whole table). session's
    career start does: a caster on his focus staff is owed the staff of
    his band, not a rapier that would cost him the focus."""
    if level <= 4:
        return WEAPONS[chassis or rng.choice(CHASSIS)]
    if level <= 9:
        return masterwork_of(chassis or rng.choice(CHASSIS))
    sp = (6 if level <= 13 else
          7 if level <= 16 else
          8 if level <= 18 else 9)
    return generate_weapon(rng, sp, chassis=chassis)


# --------------------------------------------------------------------------- #
# The famous armory (pregenerated at worldgen, known from day one)
# --------------------------------------------------------------------------- #

ARMORY_TIERS = (6, 6, 6, 7, 7, 7, 8, 8, 9, 10)      # ten famous weapons:
                    # six magic, three legendary, one mythic per world
FAMOUS_NAMES = (
    "Frostfang", "Emberbrand", "Adderfang", "Bonecleaver", "Kingsbane",
    "Wolfbrand", "Stormneedle", "Graveward", "Redharvest", "Thornpoint",
    "Winterbite", "Goldentooth", "Oathbiter", "Palefire", "the Long Thorn",
    "Duskmetal", "Hollowedge", "the Quiet Blade", "Ironsorrow", "Lawbreaker",
)
KEEPER_LINES = (            # the resting places of the unclaimed pieces
    "sealed in a barrow, its dead owner still holding it",
    "in a beast's hoard, under the bones of the last party",
    "sunk with a ferry; the fisher folk know the spot",
    "walled up in a ruined shrine; the wall has a crack",
)


def roll_armory(world: dict, rng: random.Random) -> list[dict]:
    """The world's famous magic weapons: rolled once at worldgen, named,
    and KNOWN -- the player can hear of every one from day one. Owners are
    drawn from the world's cast and wield their weapon in any fight over
    it (the weapon guards itself); the rest lie in named resting places.
    Never for sale, by doctrine. Returns plain dicts (JSON-safe: they ride
    the save like everything else)."""
    names = rng.sample(FAMOUS_NAMES, len(ARMORY_TIERS))
    notables = [n for n in world.get("npcs", ())
                if n.get("post") not in (None, "service")]
    rng.shuffle(notables)
    wilds = [a for a in world["areas"].values()
             if a.get("kind") == "natural"]
    armory = []
    for i, sp in enumerate(ARMORY_TIERS):
        w = generate_weapon(rng, sp, name=names[i])
        entry = {"weapon": dataclasses.asdict(w), "sp": sp, "tier": w.tier,
                 "name": w.name, "status": "known"}
        # The mythic piece never sits in a pocket: it is always a resting-
        # place find (the endgame is going and getting it).
        if sp < MYTHIC_SP and notables and rng.random() < 0.6:
            npc = notables.pop()
            entry["owner"] = {"name": npc["name"], "role": npc["role"],
                              "land": npc["land"], "seat": npc["seat"]}
            entry["where"] = (f"carried by {npc['name']}, {npc['role']}, "
                              f"at {world['areas'][npc['seat']]['name']}")
        else:
            area = rng.choice(wilds)
            entry["owner"] = None
            entry["where"] = (f"{rng.choice(KEEPER_LINES)} -- "
                              f"in {area['name']}")
        armory.append(entry)
    return armory


# --------------------------------------------------------------------------- #
# The legendary smiths
# --------------------------------------------------------------------------- #

SMITH_CAPS = (7, 8, 9)          # one smith per cap; the pride floor is
SMITH_PRIDE_FLOOR = 1           # cap - this: they refuse lesser work
SMITH_STYLES = (                # what each will forge (style is identity)
    ("any steel", CHASSIS),
    ("blades only", ("rapier", "katana")),
    ("war steel", ("zweihander", "katana")),
)
COMMISSION_MULT = 1.5           # the pride premium over the open value
COMMISSION_DAYS_PER_SP = 1      # forging days: sp - QUALITY_SP days


def roll_smiths(world: dict, rng: random.Random) -> list[dict]:
    """The world's legendary smiths: three, seated in distinct capitals,
    each with a CAP (the best sp they can forge) and the pride floor
    (cap - 1) below which they will not work. Commissions are the one way
    gold buys magic steel -- new steel, never the famous names."""
    from people import make_npc     # runtime: people imports quests
    capitals = [a for a in world["areas"].values() if a.get("capital")]
    rng.shuffle(capitals)
    styles = list(SMITH_STYLES)
    rng.shuffle(styles)
    smiths = []
    for cap_sp, seat, (style, chassis) in zip(SMITH_CAPS, capitals, styles):
        npc = make_npc(rng, seat["homeland"], "legendary smith", level=cap_sp)
        smiths.append({"name": npc["name"], "homeland": npc["homeland"],
                       "sex": npc["sex"], "age": max(40, npc["age"]),
                       "seat": seat["key"], "seat_name": seat["name"],
                       "land": seat["land"], "cap": cap_sp,
                       "floor": cap_sp - SMITH_PRIDE_FLOOR,
                       "style": style, "chassis": list(chassis)})
    return smiths


def commission_price(sp: int) -> int:
    """A commission's gold price: the open value plus the pride premium,
    rounded to tens."""
    return int(round(value_for_sp(sp) * COMMISSION_MULT / 10.0) * 10)


def commission_weapon(smith: dict, rng: random.Random, sp: int | None = None,
                      chassis: str | None = None) -> tuple[Weapon, int, int]:
    """Forge one commission at `sp` (default: the smith's cap). Raises
    ValueError below the pride floor, above the cap, or off the smith's
    style. Returns (weapon, price, forging days)."""
    sp = smith["cap"] if sp is None else sp
    if sp > smith["cap"]:
        raise ValueError(f"{smith['name']} cannot forge sp {sp} "
                         f"(cap {smith['cap']})")
    if sp < smith["floor"]:
        raise ValueError(f"{smith['name']} will not stoop to sp {sp} "
                         f"(floor {smith['floor']} -- pride)")
    if chassis is None:
        chassis = rng.choice(tuple(smith["chassis"]))
    elif chassis not in smith["chassis"]:
        raise ValueError(f"{smith['name']} forges {smith['style']}, "
                         f"not the {chassis}")
    w = generate_weapon(rng, sp, chassis=chassis)
    days = (sp - QUALITY_SP) * COMMISSION_DAYS_PER_SP
    return w, commission_price(sp), days


# --------------------------------------------------------------------------- #
# Readouts (40-column display copy)
# --------------------------------------------------------------------------- #

def _fragments(text: str) -> list[str]:
    """Break display copy into fit_lines fragments on its own punctuation
    seams (fit_lines never splits a fragment -- the caller keeps them
    short). The separator stays glued to its left fragment."""
    for sep in (" -- ", "; ", ", ", ": "):
        text = text.replace(sep, sep.rstrip() + "\x00")
    return [p for p in text.split("\x00") if p]


def _fit_indented(text: str, indent: str = "  ") -> list[str]:
    """fit_lines with an indent that COUNTS against the 40 columns."""
    width = 40 - len(indent)
    lines, cur = [], ""
    for p in _fragments(text):
        if not cur:
            cur = p
        elif len(cur) + 1 + len(p) <= width:
            cur += " " + p
        else:
            lines.append(cur)
            cur = p
    if cur:
        lines.append(cur)
    return [indent + ln for ln in lines]


def weapon_lines(w: Weapon) -> list[str]:
    """One weapon's display block, fitted to the 40-column screen."""
    head = w.name.upper() if w.tier in ("legendary", "mythic") else w.name
    lines = [f"{head} ({w.tier} {w.base or w.name})"]
    lines += fit_lines(_fragments(w.description))
    return lines


def armory_lines(armory: list[dict]) -> list[str]:
    lines = ["THE FAMOUS WEAPONS (all known):"]
    for entry in armory:
        w = entry["weapon"]
        lines.append(f"- {entry['name']} -- {entry['tier']} "
                     f"{w['base']}")
        lines += _fit_indented(entry["where"])
    return lines


def smith_lines(smiths: list[dict]) -> list[str]:
    lines = ["THE LEGENDARY SMITHS:"]
    for s in smiths:
        lines.append(f"- {s['name']} of {s['seat_name']} "
                     f"({s['style']})")
        lines.append(f"  forges sp {s['floor']}-{s['cap']}; "
                     f"{commission_price(s['floor'])}g-"
                     f"{commission_price(s['cap'])}g")
    return lines


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    import quests
    world = quests.generate_world(args.seed)
    rng = random.Random(f"armory:{args.seed}")
    print("\n".join(armory_lines(world["armory"])))
    print()
    print("\n".join(smith_lines(world["smiths"])))
    print()
    print("sample commissions:")
    for smith in world["smiths"]:
        w, price, days = commission_weapon(smith, rng)
        print(f"  {smith['name']}: {price}g, {days} days --")
        for ln in weapon_lines(w):
            print("    " + ln)


if __name__ == "__main__":
    main()
