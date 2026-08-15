"""The ruler character -- WHO holds power, as a rollable sheet.

The politics rung's person half (plan.md's worldsim ladder; worldsim.md's
THE RULER CHARACTER). One weighted pool of 357 words rolls a memorable
authority: a crown draws THREE, a lesser named authority a card creates
draws TWO, and between draws the drawn word, its axis opposite and its
never-with partners leave the pool while the die shrinks by their weights.
Three draws therefore always land three distinct compatible words.

Why the numbers are what they are: 734 European rulers were coded against
this vocabulary, 443 of them carried at least one trait at the kept
resolution, and the average was 3 traits a ruler -- so three weighted draws
reproduce the measured per-trait marginals almost exactly. The weights ARE
those percentages, rounded up; the pool is the HUMAN-CROWN / FIRASCIR
BASELINE, and it serves every land until per-country modifier
columns are authored (worldsim.md). If rulers ever feel thin at the table,
`CROWN_DRAWS = 4` is the one knob -- it scales every marginal by 4/3.

The shape:

- **An AXIS is two named poles around an unnamed neutral middle** (doting --
  silence -- harsh at home); a **FLAG is one named pole and silence** (an art
  patron exists, a hater-of-arts does not). Neutral is never mentioned in
  play: neutral is silence.
- **The trait list is words.** Pole names are unique across the whole
  vocabulary, so a card or a rumor line admits on a bare word
  (`"cruel" in sheet["traits"]`). Only three companion keys exist: derived
  `heart`, `puppeteer` (only beside `puppet`) and the affliction `origins`.
- **Extreme steps** occupy their pole's whole axis: a zealot IS devout,
  further out, so drawing zealot removes devout and godless, and drawing
  devout removes godless and zealot.
- **The floor.** Vivid entries the dataset zeroed -- godless, eats nothing,
  sees visions -- sit at weight 1: the range doctrine's ~1% floor made real.
  To fatten the rare tail later RAISE the floor at full resolution; never
  compress the pool to a d100 (re-rounding either deletes the tail or
  triples it, and code reads a 357-list as easily as a 100-list).
- **Scope.** Nearly the whole vocabulary applies to ANY authority --
  deliberate, so one sheet rolls a king, a border lord and a toll-sheriff.
  `itinerant` is the only crown-scope entry, which is why the crown-less
  pool is 355.
- **Moral tags are bookkeeping, not law.** Nine poles carry `good` or
  `dark`; they forbid nothing (an honorable cruel king is a contradiction,
  and contradictions can work). They exist only to derive `heart`, which
  stays hidden in play and is the crime layer's desert anchor.

RANGE DOCTRINE (worldsim.md, writing.md's Tone). The sheet's job is
MEMORABLE, VIVID rulers, so the vocabulary keeps the widest range the
catalog allows -- the scandalous and the clinical included. A king who
starves himself, or who tried to die by his own hand, is exactly the rumor
that is remembered. Rarity is the weight column's whole job: a rare entry
gets a small cell, never deletion, and no writing pass may collapse a
specific vivid entry into a safer generic word.

Nothing here imports the rest of the game -- `worldsim.py` keeps the rolled
sheet on the land layer and its cards admit on the words, `quests.py` casts
the face that wears it.

Run:  python rulers.py [--seed N] [--count N] [--lesser]   # roll a few
                                                           # sheets and
                                                           # print them
"""
from __future__ import annotations

import argparse
import random

# --------------------------------------------------------------------------- #
# The knobs
# --------------------------------------------------------------------------- #

CROWN_DRAWS = 3         # the dataset's average trait count -- the identity
                        # that makes three weighted draws faithful
LESSER_DRAWS = 2        # a lord, a sheriff, a guild master: named, not
                        # crowned, and thinner on purpose
AFFLICTION_CAP = 3      # melancholy + sleepless + drunkard reads as one
                        # story; a fourth reads as noise
ORIGIN_CHANCE = 0.5     # how often an affliction is stamped with a dated
                        # origin ("since the fever") -- the rumor's story,
                        # for free

# --------------------------------------------------------------------------- #
# The vocabulary -- the fill sheet, as data
# --------------------------------------------------------------------------- #
# One row per AXIS: (axis, (pole A, weight, tag), (pole B, weight, tag)).
# The weight is the pole's measured share of the 443 traited rulers, rounded
# up, and it serves directly as the pool weight. Neutral is the unwritten
# remainder and is never rolled.

AXES: tuple[tuple[str, tuple, tuple], ...] = (
    ("ambition",  ("ambitious", 32, ""),      ("content", 1, "")),
    ("industry",  ("tireless", 15, ""),       ("idle", 2, "")),
    ("nerve",     ("bold", 15, ""),           ("craven", 1, "")),
    ("trust",     ("trusting", 2, ""),        ("suspicious", 7, "")),
    ("mercy",     ("merciful", 3, "good"),    ("cruel", 10, "dark")),
    ("honor",     ("honorable", 2, "good"),   ("faithless", 2, "dark")),
    ("purse",     ("austere", 5, ""),         ("lavish", 5, "")),
    ("greed",     ("openhanded", 2, "good"),  ("grasping", 2, "")),
    ("faith",     ("devout", 31, ""),         ("godless", 1, "")),
    ("rule",      ("lawful", 12, "good"),     ("arbitrary", 14, "dark")),
    ("custom",    ("traditionalist", 7, ""),  ("reformer", 25, "")),
    ("door",      ("accessible", 2, ""),      ("walled", 3, "")),
    ("appetites", ("chaste", 2, ""),          ("lecherous", 3, "")),
    ("table",     ("glutton", 2, ""),         ("eats nothing", 1, "")),
    ("hearth",    ("doting", 3, "good"),      ("harsh at home", 1, "dark")),
    ("strangers", ("welcoming", 4, ""),       ("homeland-proud", 3, "")),
    ("sorcery",   ("spell-friendly", 2, ""),  ("spell-fearing", 3, "")),
    ("war",       ("martial", 28, ""),        ("unblooded", 1, "")),
    ("wits",      ("brilliant", 18, ""),      ("dull", 1, "")),
    ("looks",     ("striking", 3, ""),        ("ill-favored", 1, "")),
)

# The EXTREME steps: a rarer variant that occupies its pole's whole axis
# slot. The sheet demonstrates the mechanism once -- extremity is otherwise
# priced by the weight column alone, and the dramatic words simply keep
# small cells.
EXTREMES: tuple[tuple[str, str, int, str], ...] = (
    ("zealot", "faith", 17, ""),        # a zealot IS devout, further out
)

# The FLAGS: one named pole and silence. `scope` is "any" or "crown";
# `never` names the words this one refuses to be rolled beside.
FLAGS: tuple[tuple[str, int, str, tuple[str, ...]], ...] = (
    ("charismatic", 7, "any", ()),
    ("witty", 2, "any", ()),
    ("cultivated", 14, "any", ()),
    ("tinkerer", 1, "any", ()),
    ("nepotist", 1, "any", ()),
    ("puppet", 4, "any", ()),
    ("itinerant", 2, "crown", ()),      # the one crown-scope entry
    ("trade-minded", 3, "any", ()),
    ("gifted", 1, "any", ("spell-fearing",)),
    ("sickly", 7, "any", ()),
    ("crippled", 4, "any", ()),
    ("falling-sickness", 3, "any", ()),
    ("drunkard", 2, "any", ()),
    ("melancholy", 3, "any", ()),
    ("manic", 1, "any", ()),
    ("sees visions", 1, "any", ()),
    ("delusions", 3, "any", ()),
    ("death-wish", 1, "any", ()),
    ("failing mind", 2, "any", ()),
    ("sleepless", 1, "any", ()),
)

# The affliction family, and the cap that keeps a combo a story instead of a
# census. MAD is a READING, never a rolled word: the fiction may crown
# anyone "the Mad King" over any of the four below, but the specific word is
# what rolls and what cards admit on.
AFFLICTIONS = frozenset((
    "sickly", "crippled", "falling-sickness", "drunkard", "glutton",
    "eats nothing", "melancholy", "manic", "sees visions", "delusions",
    "death-wish", "failing mind", "sleepless",
))
MAD_FAMILY = ("sees visions", "delusions", "melancholy", "manic")

ORIGIN_STAMPS = (
    "since the fever", "since the fall at the hunt", "since the siege year",
    "since the child died", "since the poisoning", "since the bad winter",
    "since the day of the oath",
)
# The puppeteer field carries the colour, and is the REAL door for PC
# dealings: the man who answers when the crown does not.
PUPPETEERS = (
    "the queen mother", "the chancellor", "the favorite",
    "the high priest", "the treasurer", "the captain of the guard",
    "the elder brother", "the foreign envoy",
)


def _build() -> dict[str, dict]:
    """The vocabulary as one flat table: word -> weight, scope, axis, tag,
    never-with. Pole names are unique across the whole sheet, which is what
    lets a card admit on a bare word."""
    table: dict[str, dict] = {}
    for axis, *poles in AXES:
        for word, weight, tag in poles:
            table[word] = {"weight": weight, "scope": "any", "axis": axis,
                           "tag": tag, "never": ()}
    for word, axis, weight, tag in EXTREMES:
        table[word] = {"weight": weight, "scope": "any", "axis": axis,
                       "tag": tag, "never": ()}
    for word, weight, scope, never in FLAGS:
        table[word] = {"weight": weight, "scope": scope, "axis": "",
                       "tag": "", "never": tuple(never)}
    return table


VOCABULARY = _build()
AXIS_WORDS: dict[str, frozenset[str]] = {
    axis: frozenset(word for word, row in VOCABULARY.items()
                    if row["axis"] == axis)
    for axis in {row["axis"] for row in VOCABULARY.values() if row["axis"]}
}
POOL_TOTAL = sum(row["weight"] for row in VOCABULARY.values())
CROWNLESS_TOTAL = sum(row["weight"] for row in VOCABULARY.values()
                      if row["scope"] != "crown")

# --------------------------------------------------------------------------- #
# Circumstances (worldsim.md: history, not disposition)
# --------------------------------------------------------------------------- #
# The catalog's footer list stands as the DM's non-trait record; two of it
# are rolled here because CARDS read them. Mode of accession absorbs
# fratricidal -- "took the throne over a brother's body" is a mode of
# accession and better rumor than any disposition word -- and the succession
# state is the most card-rich single fact about any crown.

ACCESSIONS: tuple[tuple[str, int, str], ...] = (
    ("inherited", 55, "came to it by birth, and nobody argued"),
    ("elected", 12, "was elected to it, and the losers remember"),
    ("minority", 10, "came to it as a child, under a council"),
    ("usurped", 8, "took it from the one who held it"),
    ("kin-blood", 7, "took the throne over a brother's body"),
    ("conquest", 5, "took the land by war and kept it"),
    ("restored", 3, "was put back on it after years abroad"),
)
SUCCESSIONS = ("secure", "disputed", "heirless")
SUCCESSION_BASE = {"secure": 6, "disputed": 3, "heirless": 2}
# It reads the traits and the accession for free: a chaste crown has no heir
# coming, a lecherous one has too many, and a child under a council was
# never uncontested.
SUCCESSION_READS = {
    "chaste": {"heirless": 6},
    "sickly": {"heirless": 3},
    "eats nothing": {"heirless": 2},
    "lecherous": {"disputed": 4},
    "harsh at home": {"disputed": 3},
    "doting": {"secure": 3},
    "failing mind": {"disputed": 2},
}
ACCESSION_READS = {
    "kin-blood": {"disputed": 3},
    "usurped": {"disputed": 3},
    "elected": {"disputed": 2},
    "minority": {"disputed": 2},
    "conquest": {"disputed": 2},
}
SUCCESSION_WORDS = {
    "secure": "the succession is settled",
    "disputed": "the succession is disputed",
    "heirless": "there is no heir",
}


# --------------------------------------------------------------------------- #
# The draw
# --------------------------------------------------------------------------- #

def pool(crown: bool = True) -> dict[str, int]:
    """The weighted pool a draw starts from: 357 words for a crown, 355 for
    anyone else (itinerant is crown-scope and nothing else is)."""
    return {word: row["weight"] for word, row in VOCABULARY.items()
            if crown or row["scope"] != "crown"}


def _pick(rng: random.Random, live: dict[str, int]) -> str | None:
    """One draw against the SHRUNKEN die -- d357 the first time, and
    whatever is left after the removals every time after."""
    total = sum(live.values())
    if total <= 0:
        return None
    roll = rng.randint(1, total)
    for word, weight in live.items():
        roll -= weight
        if roll <= 0:
            return word
    return None                                     # unreachable


def _strike(live: dict[str, int], word: str, traits: list[str]) -> None:
    """Take the drawn word out of the pool, with everything it forbids: its
    axis (one pole per axis, extremes included), its never-with partners in
    both directions, and -- once the cap is reached -- the rest of the
    affliction family. The removals terminate by construction and leave
    every remaining weight in its measured proportion, which is what makes
    the shrinking pool exactly equivalent to rerolling invalid draws."""
    gone = {word}
    axis = VOCABULARY[word]["axis"]
    if axis:
        gone |= AXIS_WORDS[axis]
    gone |= set(VOCABULARY[word]["never"])
    gone |= {other for other, row in VOCABULARY.items()
             if word in row["never"]}
    if sum(1 for t in traits if t in AFFLICTIONS) >= AFFLICTION_CAP:
        gone |= AFFLICTIONS
    for dead in gone:
        live.pop(dead, None)


def heart_of(traits) -> str:
    """The hidden reading: dark-tagged traits and no good ones -> `dark`;
    good and no dark -> `good`; both or neither -> `mixed`. The
    contradictory ruler reads as complicated, which is what mixed means.
    Never shown in play -- it is the crime layer's desert anchor."""
    tags = {VOCABULARY[t]["tag"] for t in traits if t in VOCABULARY}
    if "dark" in tags and "good" not in tags:
        return "dark"
    if "good" in tags and "dark" not in tags:
        return "good"
    return "mixed"


def _weighted(rng: random.Random, weights: dict[str, int]) -> str:
    roll = rng.randint(1, sum(weights.values()))
    for key, weight in weights.items():
        roll -= weight
        if roll <= 0:
            return key
    raise ValueError("empty table")                 # unreachable


def roll_accession(rng: random.Random) -> str:
    return _weighted(rng, {mode: w for mode, w, _line in ACCESSIONS})


def roll_succession(rng: random.Random, traits, accession: str) -> str:
    """The succession state, read off the sheet that is already rolled."""
    weights = dict(SUCCESSION_BASE)
    for trait in traits:
        for state, bump in SUCCESSION_READS.get(trait, {}).items():
            weights[state] += bump
    for state, bump in ACCESSION_READS.get(accession, {}).items():
        weights[state] += bump
    return _weighted(rng, weights)


def roll_ruler(rng: random.Random, *, crown: bool = True,
               draws: int | None = None) -> dict:
    """One rolled authority: the flat `traits` list, derived `heart`, the
    succession and accession circumstances, and the two companion fields
    that only exist when their trait does (`puppeteer`, `origins`).

    A crown draws CROWN_DRAWS off the full pool; a lesser named authority a
    card creates draws LESSER_DRAWS off the crown-less one."""
    live = pool(crown)
    traits: list[str] = []
    for _ in range(CROWN_DRAWS if draws is None and crown
                   else LESSER_DRAWS if draws is None else draws):
        word = _pick(rng, live)
        if word is None:
            break
        traits.append(word)
        _strike(live, word, traits)
    sheet = {"traits": traits, "heart": heart_of(traits), "crown": crown}
    if "puppet" in traits:
        sheet["puppeteer"] = rng.choice(PUPPETEERS)
    origins = {t: rng.choice(ORIGIN_STAMPS) for t in traits
               if t in AFFLICTIONS and rng.random() < ORIGIN_CHANCE}
    if origins:
        sheet["origins"] = origins
    sheet["accession"] = roll_accession(rng)
    sheet["succession"] = roll_succession(rng, traits, sheet["accession"])
    return sheet


# --------------------------------------------------------------------------- #
# Readouts (the DM's eyes -- `world`, and the notables block)
# --------------------------------------------------------------------------- #

def trait_phrase(sheet: dict) -> str:
    """The trait list as one phrase, each affliction carrying its dated
    origin where it rolled one."""
    origins = sheet.get("origins") or {}
    return ", ".join(t + (f" ({origins[t]})" if t in origins else "")
                     for t in sheet["traits"]) or "nothing anyone says"


def accession_line(sheet: dict) -> str:
    return next(line for mode, _w, line in ACCESSIONS
                if mode == sheet["accession"])


def ruler_lines(sheet: dict, label: str = "the crown") -> list[str]:
    """Two or three lines of who this authority is, for the DM inventory.
    Heart is printed HERE and nowhere the player can see it."""
    lines = [f"  {label}: {trait_phrase(sheet)} [heart {sheet['heart']}]"]
    lines.append(f"    {accession_line(sheet)}; "
                 f"{SUCCESSION_WORDS[sheet['succession']]}")
    if sheet.get("puppeteer"):
        seat = "the throne" if sheet.get("crown") else "the seat"
        lines.append(f"    the hand behind {seat}: {sheet['puppeteer']}")
    return lines


# --------------------------------------------------------------------------- #
# Validation (the sheet has to be legal at import time)
# --------------------------------------------------------------------------- #

def validate_content() -> None:
    seen: set[str] = set()
    for word, row in VOCABULARY.items():
        if word in seen:
            raise ValueError(f"duplicate trait word: {word}")
        seen.add(word)
        if row["weight"] < 1:
            raise ValueError(f"{word}: every entry sits at the floor or "
                             f"above it")
        if row["scope"] not in ("any", "crown"):
            raise ValueError(f"{word}: no such scope: {row['scope']}")
        if row["tag"] not in ("", "good", "dark"):
            raise ValueError(f"{word}: no such moral tag: {row['tag']}")
        for other in row["never"]:
            if other not in VOCABULARY:
                raise ValueError(f"{word}: never-with names no such trait: "
                                 f"{other}")
        if not word.isascii():
            raise ValueError(f"{word}: game output is ASCII")
    for word in AFFLICTIONS | set(MAD_FAMILY):
        if word not in VOCABULARY:
            raise ValueError(f"affliction family names no such trait: {word}")
    for word in SUCCESSION_READS:
        if word not in VOCABULARY:
            raise ValueError(f"succession reads no such trait: {word}")
    modes = {mode for mode, _w, _line in ACCESSIONS}
    if set(ACCESSION_READS) - modes:
        raise ValueError(f"succession reads no such accession: "
                         f"{sorted(set(ACCESSION_READS) - modes)}")
    if set(SUCCESSION_BASE) != set(SUCCESSIONS):
        raise ValueError("the succession table and its states disagree")
    # The two totals the design is stated in. They are asserted, not
    # computed into the doc: if a weight moves, this is where it is noticed.
    if POOL_TOTAL != 357:
        raise ValueError(f"the pool is 357, not {POOL_TOTAL}")
    if CROWNLESS_TOTAL != 355:
        raise ValueError(f"the crown-less pool is 355, not {CROWNLESS_TOTAL}")


validate_content()


# --------------------------------------------------------------------------- #
# Demo (the designer's eyeball check)
# --------------------------------------------------------------------------- #

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--count", type=int, default=8)
    ap.add_argument("--lesser", action="store_true",
                    help="roll lesser named authorities (two draws, no "
                         "crown-scope entries)")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    crown = not args.lesser
    print(f"-- {'the crown' if crown else 'a lesser authority'}: "
          f"{CROWN_DRAWS if crown else LESSER_DRAWS} draws off "
          f"d{POOL_TOTAL if crown else CROWNLESS_TOTAL} --")
    for i in range(args.count):
        sheet = roll_ruler(rng, crown=crown)
        print("")
        for line in ruler_lines(sheet, label=f"{i + 1}"):
            print(line)


if __name__ == "__main__":
    main()
