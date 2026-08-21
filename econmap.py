"""The tile economy arc's eyeball tool (2026-08-21, plan.md Part 1).

Standalone and stdlib-only, in the archive/worldmap.py manner: it reads the
authored resources directly and imports nothing from the game, so it can be
run against a half-drawn overlay while the rules it will obey are still
being designed.  It validates each authored overlay against the base map
and renders them side by side as 30x18 ASCII, with censuses underneath.
Climate is the first layer; fertility, population and routes join it as
their rounds land.

    python econmap.py

Validation (the law demoted to a lint -- the map is authored, the rules
only check it): every land tile carries exactly one climate letter, sea
carries none, and `a` (alpine) sits exactly on the `^` tiles.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

RESOURCES = Path(__file__).with_name("resources")
BASE_PATH = RESOURCES / "europe_map.txt"
CLIMATE_PATH = RESOURCES / "europe_climate.txt"

ROWS, COLUMNS = 18, 30
BASE_GLYPHS = {".", "#", "^", "~"}

# The climate vocabulary (round 1, DRAFT until the round settles).
CLIMATES = {
    "u": "tundra",
    "t": "taiga",
    "c": "continental",
    "o": "oceanic",
    "m": "mediterranean",       # the medieval DRY one (its bad year is dry)
    "w": "wet mediterranean",   # the southern shore's Roman Warm regime
    "s": "steppe",
    "d": "desert",
    "n": "nile",                # river-fed floodplain granary
    "a": "alpine",              # exactly the mountain tiles
}


def load_grid(path: Path, legal: set[str]) -> list[str]:
    rows = path.read_text(encoding="ascii").splitlines()
    if len(rows) != ROWS:
        sys.exit(f"{path.name}: expected {ROWS} rows, got {len(rows)}")
    for number, row in enumerate(rows, 1):
        if len(row) != COLUMNS:
            sys.exit(f"{path.name}: row {number} has {len(row)} columns; "
                     f"expected {COLUMNS}")
        for column, glyph in enumerate(row, 1):
            if glyph not in legal:
                sys.exit(f"{path.name}: invalid glyph {glyph!r} at "
                         f"row {number}, column {column}")
    return rows


def country_at(row: int, column: int) -> str:
    # places.country_at, restated so the tool stays standalone. Nothing here
    # is pinned -- the census below is an eyeball, not a contract.
    if row >= 11:
        return "mortellaria"
    return "firascir" if column <= 21 else "tergal"


def validate_climate(base: list[str], climate: list[str]) -> list[str]:
    problems = []
    for r in range(ROWS):
        for c in range(COLUMNS):
            ground, label = base[r][c], climate[r][c]
            where = f"R{r + 1:02d}C{c + 1:02d}"
            if ground == "." and label != ".":
                problems.append(f"{where}: sea tile carries {label!r}")
            elif ground != "." and label == ".":
                problems.append(f"{where}: land tile ({ground}) unpainted")
            elif ground == "^" and label != "a":
                problems.append(f"{where}: mountain painted {label!r}, "
                                f"expected 'a'")
            elif ground != "^" and label == "a":
                problems.append(f"{where}: alpine off the mountain "
                                f"({ground!r})")
    return problems


def render_side_by_side(left: list[str], right: list[str],
                        titles: tuple[str, str]) -> None:
    gap = "   "
    print(f"     {titles[0]:<{COLUMNS}}{gap}  {titles[1]}")
    tens = "".join(str((c // 10)) for c in range(1, COLUMNS + 1))
    ones = "".join(str(c % 10) for c in range(1, COLUMNS + 1))
    print(f"     {tens}{gap}  {tens}")
    print(f"     {ones}{gap}  {ones}")
    for number, (a, b) in enumerate(zip(left, right), 1):
        print(f"{number:2d}   {a}{gap}  {b}")


def censuses(climate: list[str]) -> None:
    total = Counter()
    by_country: dict[str, Counter] = {}
    for r in range(ROWS):
        for c in range(COLUMNS):
            label = climate[r][c]
            if label == ".":
                continue
            total[label] += 1
            by_country.setdefault(country_at(r + 1, c + 1),
                                  Counter())[label] += 1
    print("\nCLIMATE CENSUS "
          f"({sum(total.values())} land tiles)")
    for letter in CLIMATES:
        print(f"  {letter} {CLIMATES[letter]:<18} {total.get(letter, 0):3d}")
    for country in ("firascir", "mortellaria", "tergal"):
        counts = by_country.get(country, Counter())
        parts = ", ".join(f"{letter}:{counts[letter]}"
                          for letter in CLIMATES if counts.get(letter))
        print(f"  {country:<12} {parts}")


def main() -> None:
    base = load_grid(BASE_PATH, BASE_GLYPHS)
    climate = load_grid(CLIMATE_PATH, set(CLIMATES) | {"."})
    problems = validate_climate(base, climate)
    if problems:
        for line in problems:
            print(f"LINT: {line}")
        sys.exit(f"{len(problems)} problem(s) -- fix the overlay")
    render_side_by_side(base, climate, ("TERRAIN", "CLIMATE"))
    censuses(climate)


if __name__ == "__main__":
    main()
