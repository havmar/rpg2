"""The character layer -- races, names, traits, and the person generator.

rpg.py owns the mechanics a character RUNS ON (stats, CHA/capacity, the
satisfaction track and its constants); this file owns the person: which race
they are, what they're called, how old they are, and -- for COMPANIONS --
the three-trait sketch that makes an archetype specific. session.py uses it
for the PC at game start and the tavern recruits; the sims never import it
(their throwaway duos come from rpg.make_party), so nothing here can move a
bench number.

The design (2026-07-11, designer-vetted):

- **Races are the world's five** (quests.py's RACES -- the lands ARE the
  races). Racial stat modifiers raise the FLOOR of a roll range, never the
  ceiling: an orc's STR rolls 4-6, so the natural cap 6 (the 1-20 doctrine)
  holds, the worst rolls vanish, and the average moves ~+0.5. The mods are
  deliberately unequal in combat terms (goblin DEX is the sharpest stat in
  the game; elf CHA is an economy stat) -- races feel different along
  different axes, on purpose.
- **Traits are a sketch, not a census**: ONE behavioral category (of five)
  and TWO presentation categories (of four), one trait each. What isn't
  described is average for the archetype; the DM edits any generated
  contradiction before presenting. Most traits are mechanics-free labels
  the DM performs; the few mechanical ones are documented in TRAIT_NOTES
  and checked by name (rpg.has_trait).
- **Traits are the COMPANION layer, and only that** (2026-08-05, designer
  directive -- the characteristic criterion of plan.md's world thread): a
  companion's traits are CHOSEN AGAINST at hiring and several of them are
  mechanical (armored, wealthy, the interests, the satisfaction hooks), so
  they earn their keep. On a dict NPC or on the PC they were unbacked
  flavor the DM had to perform, so neither rolls them any more:
  `make_npc` casts a face without a sketch and the PC's sheet is his stats.
- **Pairs**: a quarter of recruit options are a bonded pair (parent/child,
  couple, mentor/mentee, old friends) -- one option slot, TWO heads against
  the CHA capacity, joining and leaving together.
- **No trait recursion**: the side-people some traits generate (a child, an
  enemy) are name-and-line descriptions inside the trait string, never full
  characters -- the DM forges the enemy's fight when the story wants it.

Run:  python people.py [--seed N] [--level L]   -> print a sample of
      generated characters and a pair (the DM's eyeball check)
"""
from __future__ import annotations

import argparse
import random

import rpg
from rpg import Entity, MEDS_INTERVAL_DAYS, MEDS_PRICE
from quests import RACES

# --------------------------------------------------------------------------- #
# Races (the world's five; quests.RACES is the source of truth)
# --------------------------------------------------------------------------- #
# Floor-raise modifiers per race (see rpg._adjusted_range): key -> +1 floor.
# human: nothing (the baseline). elf: CHA (an elf PC is never solo -- floor
# 4 = capacity 1+). orc: STR. dwarf: HP. goblin: DEX (the combat pick).
# Under the fixed stat budget (2026-07-13) a floor raise stays a genuine
# net extra: races remain unequal on purpose.
RACE_MODS: dict[str, dict[str, int]] = {
    "human":  {},
    "elf":    {"cha": 1},
    "orc":    {"str": 1},
    "dwarf":  {"hp": 1},
    "goblin": {"dex": 1},
}

# Ceiling-drop modifiers per race: key -> -1 ceiling. Goblins are wiry, not
# strong (2026-07-13, designer call): STR rolls 3-5, so a goblin frame lands
# on the rapier, never naturally on the zweihander (rpg.develop_hero arms
# STR>DEX frames with the girder).
RACE_MODS_CEIL: dict[str, dict[str, int]] = {
    "goblin": {"str": 1},
}

SEXES = ("m", "f")


def roll_age(rng: random.Random) -> int:
    """2d20+10 (the Cairn table): 12-50. Twelve-year-old sellswords happen
    -- anime logic, designer-blessed (2026-07-11)."""
    return rng.randint(1, 20) + rng.randint(1, 20) + 10


# 25 male + 25 female names per race. Flavor keyed to quests.py's settlement
# name-parts (goblins are the gadget-works culture, orcs the iron camps...).
# No epithets, anywhere -- "Inga", never "Inga the precise".
NAMES: dict[str, dict[str, tuple[str, ...]]] = {
    "human": {
        "m": ("Brand", "Corvin", "Doran", "Kael", "Tomas", "Veld", "Aldric",
              "Berrick", "Cole", "Dunstan", "Edwin", "Garrick", "Hale",
              "Jorik", "Lambert", "Martel", "Osric", "Perrin", "Quentin",
              "Rowan", "Simon", "Theobald", "Ulric", "Walt", "Yorick"),
        "f": ("Sela", "Mira", "Yssa", "Rhea", "Inga", "Nessa", "Anneth",
              "Bess", "Cateline", "Dara", "Elsbeth", "Ferra", "Gwen",
              "Hilde", "Isolde", "Jenna", "Lysse", "Maud", "Nel", "Odile",
              "Petra", "Rosamund", "Sabine", "Tilda", "Wynne"),
    },
    "elf": {
        "m": ("Aelar", "Aramil", "Berrian", "Caladrel", "Carric", "Daethis",
              "Erevan", "Faelar", "Galinndan", "Heian", "Ivellios",
              "Laucian", "Mindartis", "Naal", "Orrian", "Paelias",
              "Quarion", "Riardon", "Soveliss", "Thamior", "Theren",
              "Uthemar", "Vanuath", "Varis", "Wren"),
        "f": ("Adrie", "Althaea", "Anastrianna", "Andraste", "Antinua",
              "Bethrynna", "Birel", "Caelynn", "Drusilia", "Enna",
              "Felosial", "Ielenia", "Jelenneth", "Keyleth", "Leshanna",
              "Lia", "Meriele", "Mialee", "Naivara", "Quelenna", "Sariel",
              "Shanairra", "Silaqui", "Thia", "Vadania"),
    },
    "orc": {
        "m": ("Gruk", "Marok", "Thokk", "Drog", "Urzag", "Karg", "Snagg",
              "Bolg", "Ruk", "Ghor", "Muzgash", "Ogrim", "Varg", "Zug",
              "Krusk", "Dench", "Feng", "Gell", "Henk", "Holg", "Imsh",
              "Keth", "Krag", "Mhurren", "Ront"),
        "f": ("Baggi", "Emen", "Engong", "Kansif", "Myev", "Neega", "Ovak",
              "Ownka", "Shautha", "Sutha", "Vola", "Volen", "Yevelda",
              "Grushka", "Marga", "Urzoth", "Ketha", "Drena", "Ghorza",
              "Bura", "Sharn", "Togga", "Ulma", "Varga", "Zasha"),
    },
    "dwarf": {
        "m": ("Adrik", "Alberich", "Baern", "Barendd", "Borin", "Brottor",
              "Dain", "Darrak", "Delg", "Eberk", "Einkil", "Fargrim",
              "Flint", "Gardain", "Harbek", "Kildrak", "Morgran", "Orsik",
              "Oskar", "Rangrim", "Rurik", "Taklinn", "Thoradin", "Tordek",
              "Vondal"),
        "f": ("Artin", "Audhild", "Bardryn", "Bruni", "Dagna", "Dagnal",
              "Diesa", "Eldeth", "Falkrunn", "Finellen", "Gunnloda",
              "Gurdis", "Helja", "Hlin", "Ilde", "Kathra", "Kristryd",
              "Liftrasa", "Mardred", "Riswynn", "Sannl", "Thora", "Torbera",
              "Torgga", "Vistra"),
    },
    "goblin": {
        "m": ("Nizzet", "Fizzle", "Krix", "Zagnit", "Pox", "Snizzle",
              "Wozzek", "Grix", "Tikkit", "Blatz", "Skiv", "Mox", "Ratchet",
              "Cogg", "Widget", "Zizzer", "Klanker", "Nogg", "Spanner",
              "Boilo", "Greeze", "Smolt", "Tinket", "Vrix", "Zonk"),
        "f": ("Nix", "Tizzy", "Wexla", "Grizelle", "Pipka", "Zeena", "Klix",
              "Motka", "Sizzle", "Brixa", "Cindra", "Dizzy", "Fizzet",
              "Gadgeta", "Hexa", "Jinka", "Kettle", "Lugna", "Mizzle",
              "Nutta", "Ozka", "Quirka", "Rivet", "Vexa", "Zippa"),
    },
}


def pick_name(rng: random.Random, race: str, sex: str,
              used: set[str] | None = None) -> str:
    """A fresh name from the race/sex pool, avoiding `used` (name collisions
    would break the save's name-keyed lookups)."""
    pool = [n for n in NAMES[race][sex] if used is None or n not in used]
    suffix = 1
    while not pool:
        # The pool is finite (25 a race/sex) and the quest board CHURNS since
        # 2026-07-26 -- a long campaign can genuinely ask for more faces than
        # there are names. Number them rather than crashing on an empty pool.
        suffix += 1
        tag = " II" if suffix == 2 else f" {suffix}"
        pool = [n + tag for n in NAMES[race][sex]
                if used is None or n + tag not in used]
    name = rng.choice(pool)
    if used is not None:
        used.add(name)
    return name


# --------------------------------------------------------------------------- #
# Traits
# --------------------------------------------------------------------------- #
# Two groups: BEHAVIOR (who they are) and PRESENTATION (how they read).
# Generation rolls 1 behavior category + 2 distinct presentation categories,
# one trait each -- every character gets exactly one behavioral hook (where
# all the satisfaction mechanics live) and most dimensions stay blank.

BEHAVIOR_TRAITS: dict[str, tuple[str, ...]] = {
    "temperament": ("friendly", "mean", "gloomy", "cheerful", "loyal",
                    "cowardly", "brave"),
    "quirk": ("patriotic", "religious", "has a child", "has an enemy"),
    "interest": ("plants", "food", "animals", "history", "music", "art",
                 "fashion", "hunting"),
    "weakness": ("gambling", "smoker", "needs meds"),
    "background": ("poverty", "priest or monk", "military", "peasant",
                   "craftsman", "trader", "scholar", "wealthy", "tribesman"),
}

PRESENTATION_TRAITS: dict[str, tuple[str, ...]] = {
    "speech": ("swears a lot", "formal", "poetic", "verbose"),
    "voice": ("loud", "whispering", "mumbling", "melodious"),
    "dress": ("tattered", "flamboyant", "mismatched", "professional",
              "armored", "colorful", "ascetic", "elegant", "luxurious"),
    # "plain" goes without saying and stays off the list on purpose
    # (2026-07-13: pool widened so "beautiful" stops being every third face).
    "looks": ("ugly", "beautiful", "sickly", "big", "short", "thin", "fat",
              "scarred", "weathered", "bald", "tattooed", "pockmarked"),
}

# Race-flavored substitutions: a rolled trait that doesn't fit a race is
# swapped for its local equivalent (2026-07-13: goblins are never
# "beautiful" and don't sing).
RACE_TRAIT_SUBS: dict[str, dict[str, str]] = {
    "goblin": {"beautiful": "sharp-toothed",
               "melodious": "high, cackling"},
}

# The mechanical traits, and what they do (shown on the sheet so hiring is
# an informed choice; everything not listed here is DM-performed fiction).
ARMORED_DEF_BONUS = 1       # the "armored" dress trait: worn protection --
                            # deliberately minor; armor-the-system stays a
                            # separate roadmap item (designer call: armor
                            # should not be important, so looks stay varied)
TRAIT_GOLD = {"wealthy": 25, "luxurious": 10}   # joining gift to the purse
                            # (the swapped-in mechanic for luxurious, which
                            # lost its bandit-magnet idea -- 2026-07-11)

# Where an interest thrives: a downtime day there pays SAT_DOWNTIME_MATCH.
INTEREST_PLACES: dict[str, tuple[str, ...]] = {
    "plants": ("village",), "animals": ("village",), "hunting": ("village",),
    "food": ("town", "capital"), "music": ("town", "capital"),
    "history": ("capital",), "art": ("capital",), "fashion": ("capital",),
}

TRAIT_NOTES: dict[str, str] = {
    "loyal": "stays past the breaking point (leaves at "
             f"{rpg.SATISFACTION_FLOOR}, not 0)",
    "cowardly": "satisfaction losses from blood and fear cut twice as deep",
    "brave": "satisfaction losses from blood and fear are halved",
    "armored": f"+{ARMORED_DEF_BONUS} defense pressure",
    "wealthy": f"brings {TRAIT_GOLD['wealthy']}g to the purse",
    "luxurious": f"brings {TRAIT_GOLD['luxurious']}g to the purse",
    "big": "+1 STR floor at creation",
    "short": "-1 STR ceiling at creation",
    "needs meds": f"a dose every {MEDS_INTERVAL_DAYS} days ({MEDS_PRICE}g, "
                  f"capitals only) or their spirits drain nightly",
    "patriotic": "downtime in their own race's land suits them",
    "religious": "downtime in a capital (the temples) suits them",
}

# One-line enemy descriptors for the "has an enemy" trait (flavor only --
# the DM forges the actual fight when the story wants it).
ENEMY_CALLINGS = ("duelist", "outlaw", "mercenary captain", "bounty hunter",
                  "disgraced soldier", "rival adventurer")


def _detail_traits(traits: dict[str, str], rng: random.Random, race: str,
                   level: int, used: set[str] | None) -> None:
    """Fill in the generated side-people some quirks carry, inline in the
    trait string (no recursion: the child and the enemy are a name and a
    line, never full characters)."""
    quirk = traits.get("quirk")
    if quirk == "has a child":
        sex = rng.choice(SEXES)
        name = pick_name(rng, race, sex, used)
        traits["quirk"] = (f"has a child (with them: {name}, age "
                           f"{rng.randint(8, 12)})")
    elif quirk == "has an enemy":
        e_race = race if rng.random() < 0.5 else rng.choice(RACES)
        sex = rng.choice(SEXES)
        name = pick_name(rng, e_race, sex, used)
        traits["quirk"] = (f"has an enemy ({name}, a {e_race} "
                           f"{rng.choice(ENEMY_CALLINGS)}, level "
                           f"{level + 2}, out there somewhere)")


def roll_traits(rng: random.Random, race: str, level: int,
                used: set[str] | None = None) -> dict[str, str]:
    """The three-trait sketch: 1 behavior category + 2 distinct presentation
    categories, one trait each. COMPANIONS only since 2026-08-05 -- the PC
    and dict NPCs carry no sketch (see the module docstring), which is what
    retired the old `no_family` switch: the PC rolled it to keep a child
    out of the opening scene, and now he rolls nothing at all."""
    traits: dict[str, str] = {}
    bcat = rng.choice(sorted(BEHAVIOR_TRAITS))
    traits[bcat] = rng.choice(BEHAVIOR_TRAITS[bcat])
    for pcat in rng.sample(sorted(PRESENTATION_TRAITS), 2):
        traits[pcat] = rng.choice(PRESENTATION_TRAITS[pcat])
    subs = RACE_TRAIT_SUBS.get(race, {})
    for cat, value in traits.items():
        if value in subs:
            traits[cat] = subs[value]
    _detail_traits(traits, rng, race, level, used)
    return traits


def joining_gold(e: Entity) -> int:
    """What a wealthy/luxurious character adds to the party purse on
    joining (or, for the PC, starts the game with)."""
    return sum(gold for name, gold in TRAIT_GOLD.items()
               if rpg.has_trait(e, name))


# --------------------------------------------------------------------------- #
# The generator
# --------------------------------------------------------------------------- #

WIZARD_ROLL_TRIES = 200     # make_character(wizard=True) rerolls the stat
                            # budget until MIND comes out strictly highest
                            # (rpg.make_human's gift test). A natural wizard
                            # is a ~14-24% roll depending on the race's floor
                            # mods, so this ceiling is never approached; it
                            # exists so a future stat change can't hang the
                            # generator in a loop.


def make_character(rng: random.Random, level: int = 1,
                   race: str | None = None, sex: str | None = None,
                   used_names: set[str] | None = None,
                   with_traits: bool = True,
                   wizard: bool = False) -> Entity:
    """One person, any level: race/sex/name/age, the three-trait sketch,
    stats budgeted with the racial + trait floor/ceiling shifts, then grown
    to `level` by the reference progression doctrine (rpg.develop_hero --
    points mostly pre-spent, quality steel from L4). Works for recruits and,
    with DM edits, for non-adventurer NPCs. Satisfaction stays None until
    the character is actually HIRED (session sets it).

    `with_traits=False` casts the person WITHOUT the sketch -- the PC's
    setting since 2026-08-05 (traits are the companion layer; see the
    module docstring). A trait-less roll takes no trait floor/ceiling
    shifts and no trait mechanics, so "big"/"short"/"armored" simply do
    not happen to him.

    `wizard=True` REROLLS the stat budget until the gift lands (MIND
    strictly above both DEX and STR -- rpg.make_human's test), which is
    how the PC is always a magic user. The reroll keeps the natural shape
    of a wizard's stats: nothing is nudged after the fact, an unlucky
    budget is simply thrown away."""
    race = race or rng.choice(RACES)
    sex = sex or rng.choice(SEXES)
    name = pick_name(rng, race, sex, used_names)
    traits = (roll_traits(rng, race, level, used_names)
              if with_traits else {})
    floors = dict(RACE_MODS[race])
    ceilings = dict(RACE_MODS_CEIL.get(race, {}))
    if "big" in traits.values():
        floors["str"] = floors.get("str", 0) + 1
    if "short" in traits.values():
        ceilings["str"] = ceilings.get("str", 0) + 1
    h = rpg.make_human(rng, name, floors=floors, ceilings=ceilings)
    for _ in range(WIZARD_ROLL_TRIES if wizard else 0):
        if h.school:
            break
        h = rpg.make_human(rng, name, floors=floors, ceilings=ceilings)
    h.race, h.sex, h.age, h.traits = race, sex, roll_age(rng), traits
    if "armored" in traits.values():
        h.def_bonus = ARMORED_DEF_BONUS
    rpg.develop_hero(h, level, rng)
    return h


PAIR_CHANCE = 0.25      # a recruit option is a bonded pair this often
PAIR_KINDS = ("parent and child", "a married couple", "mentor and mentee",
              "two old friends")
PARENT_AGE_GAP = 16     # a parent is at least this much older than the child
MENTOR_AGE_GAP = 10     # a mentor at least this much older than the mentee


def make_pair(rng: random.Random, level: int,
              used_names: set[str] | None = None
              ) -> tuple[str, list[Entity]]:
    """A bonded pair of recruits (one option slot, two heads, one fate):
    both at the option's level; parent/child share a race; ages fixed up so
    the relationship reads (parent 16+ years older, mentor 10+)."""
    kind = rng.choice(PAIR_KINDS)
    race = rng.choice(RACES)
    a = make_character(rng, level, race=race, used_names=used_names)
    b = make_character(rng, level,
                       race=race if kind == "parent and child" else None,
                       used_names=used_names)
    if kind == "parent and child":
        a, b = (a, b) if a.age >= b.age else (b, a)     # a = the parent
        if a.age < b.age + PARENT_AGE_GAP:
            a.age = b.age + PARENT_AGE_GAP + rng.randint(0, 8)
    elif kind == "mentor and mentee":
        a, b = (a, b) if a.age >= b.age else (b, a)     # a = the mentor
        if a.age < b.age + MENTOR_AGE_GAP:
            a.age = b.age + MENTOR_AGE_GAP + rng.randint(0, 8)
    a.bond, a.bond_kind = b.name, kind
    b.bond, b.bond_kind = a.name, kind
    return kind, [a, b]


# --------------------------------------------------------------------------- #
# Targeted NPC generation (2026-07-12) -- the DM casts, the dice flesh out
# --------------------------------------------------------------------------- #
# An NPC is a plain dict, not an Entity: quest givers, rulers, sages, and
# shopkeepers carry no stat block. If the story ever needs one to FIGHT,
# forge the encounter (a reskinned catalog row) or make_character a leveled
# body and borrow the face. The split from make_character is deliberate: for
# PARTY members race and background are random (the dice cast the whole
# person); for NPCs the DM already knows the race, the job, and roughly the
# age -- the caller FIXES those and the dice roll only what is left, the
# name.
#
# The sketch is GONE from this path (2026-08-05, designer directive): a
# giver's temperament, voice and dress were three lines of flavor per face
# that no rule read and the DM had to perform on top of the scene. What a
# dict NPC carries instead -- a want, a problem, a disposition with
# mechanical teeth -- is the world thread's open question (plan.md); this
# side of it just stops paying for the flavor.

NPC_MIN_AGE = 20    # roll_age (2d20+10) floored here for NPCs with a JOB;
                    # callers pass an exact age when the fiction knows better


def make_npc(rng: random.Random, race: str, role: str,
             sex: str | None = None, age: int | None = None,
             level: int | None = None,
             used_names: set[str] | None = None) -> dict:
    """One cast NPC: fixed race/role (and optionally sex/age) in, a rolled
    name out. `level` is recorded when the caller knows one (posse and hell
    leaders, the famous smiths) and left off the dict otherwise."""
    sex = sex or rng.choice(SEXES)
    name = pick_name(rng, race, sex, used_names)
    if age is None:
        age = max(NPC_MIN_AGE, roll_age(rng))
    npc = {"name": name, "race": race, "sex": sex, "age": age, "role": role}
    if level is not None:
        npc["level"] = level
    return npc


def npc_line(npc: dict) -> str:
    """One line of who this NPC is -- the person_line sibling for dict NPCs
    (quest givers, the central cast). The DM riffs the scene off it."""
    return (f"{npc['name']} ({npc['role']}) -- "
            f"{npc['race']} {npc['sex']}, age {npc['age']}")


# --------------------------------------------------------------------------- #
# Readouts (candidate sheets, the status person-line)
# --------------------------------------------------------------------------- #

def trait_note(value: str) -> str:
    """The mechanics annotation for a trait value, if it has one."""
    name = value.split(" (")[0]
    if name in TRAIT_NOTES:
        return f" [{TRAIT_NOTES[name]}]"
    if name in INTEREST_PLACES:
        places = "/".join(INTEREST_PLACES[name])
        return f" [downtime in a {places} suits them]"
    return ""


def person_line(e: Entity) -> str:
    """One line of who this is (the sheet/status companion to rpg.stat_line's
    body readout): race, sex, age, and -- for a companion -- the trait
    sketch. The PC carries no sketch, so his line stops at the age."""
    nick = f' "{e.nickname}"' if e.nickname else ""
    bits = [f"{e.race} {e.sex}, age {e.age}"] if e.race else []
    for cat in ("temperament", "quirk", "interest", "weakness", "background",
                "speech", "voice", "dress", "looks"):
        if cat in e.traits:
            bits.append(f"{cat}: {e.traits[cat]}")
    return f"{e.name}{nick} -- " + "; ".join(bits)


def character_sheet(e: Entity) -> list[str]:
    """The full sheet the player sees before hiring (yes, all of it --
    transparency over realism, same stance as straight-shown quest levels).
    The PC's sheet runs through the same call: with no traits to annotate
    it is simply his person line, his stats and his banked points (the old
    `for_pc` switch existed to suppress satisfaction-trait notes on a sheet
    that no longer has traits to suppress)."""
    def wanted(value: str) -> bool:
        # the gold traits get their own line below
        return bool(trait_note(value)) and value not in TRAIT_GOLD

    lines = [person_line(e), "  " + rpg.stat_line(e)]
    notes = [f"{e.traits[cat]}{trait_note(e.traits[cat])}"
             for cat in sorted(e.traits)
             if wanted(e.traits[cat])]
    if notes:
        lines.append("  notes: " + "; ".join(notes))
    if e.skill_points:
        lines.append(f"  {e.skill_points} skill point(s) unspent")
    gold = joining_gold(e)
    if gold:
        lines.append(f"  brings {gold}g to the party purse")
    if e.bond:
        lines.append(f"  bound to {e.bond} ({e.bond_kind}) -- they join and "
                     f"leave together")
    return lines


def downtime_match(e: Entity, settlement: dict) -> str | None:
    """Why a downtime day HERE suits this companion (the
    SAT_DOWNTIME_MATCH trigger), or None for the plain SAT_DOWNTIME day:
    patriotic in their race's land, religious at a capital's temples, an
    interest where it thrives (INTEREST_PLACES)."""
    if rpg.has_trait(e, "patriotic") and settlement.get(
            "race", settlement["land"]) == e.race:
        return "walking their own land"
    subtype = settlement.get("subtype")
    if rpg.has_trait(e, "religious") and subtype == "capital":
        return "the temples"
    interest = e.traits.get("interest")
    if interest and subtype in INTEREST_PLACES.get(interest, ()):
        return f"indulging their love of {interest}"
    return None


# --------------------------------------------------------------------------- #
# Demo (the DM's eyeball check)
# --------------------------------------------------------------------------- #

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--level", type=int, default=1)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    used: set[str] = set()
    print(f"--- six recruits (level {args.level}; companions keep the "
          f"sketch) ---")
    for _ in range(6):
        for line in character_sheet(make_character(rng, args.level,
                                                   used_names=used)):
            print(line)
        print()
    kind, pair = make_pair(rng, args.level, used_names=used)
    print(f"--- a pair: {kind} ---")
    for e in pair:
        for line in character_sheet(e):
            print(line)
        print()
    print(f"--- a PC roll (no sketch, always the gift: level "
          f"{args.level}) ---")
    for line in character_sheet(make_character(rng, args.level, sex="m",
                                               used_names=used,
                                               with_traits=False,
                                               wizard=True)):
        print(line)
    print()
    print("--- two cast NPCs (targeted: the DM fixes race/role) ---")
    print(npc_line(make_npc(rng, "human", "chief constable", used_names=used)))
    print(npc_line(make_npc(rng, "dwarf", "mine-masters' speaker",
                            used_names=used)))


if __name__ == "__main__":
    main()
