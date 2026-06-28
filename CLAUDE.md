# RPG2 — Combat Sim Prototype

A combat simulator for a fantasy RPG, intended to be played through Claude Code
with Claude as DM. Fights resolve on their own (no input once a fight starts) and
produce an outcome plus a narrative log; the DM narrates *over* that log. The
player's real decisions happen *between* fights.

> Project-level environment (Python path, encoding, etc.) lives in the parent
> `C:\minden\projects\CLAUDE.md`. Don't duplicate it here.

## Files

- `rpg2-rules.md` — the design doc and ruleset. The source of truth for *intent*
  (the "why"). Read this before changing mechanics.
- `rpg.py` — the implementation: combat engine, random party generation, and the
  skeleton dungeon. Self-contained, stdlib only.
- `tune.py` — Monte Carlo sweep over room layouts; prints the none/one/both death
  distribution. Use it to re-check balance after any mechanics change.
- `.notes.txt` — raw brainstorming notes (unstructured, historical).

## Running

```
python rpg.py            # random party + dungeon, full narrative log
python rpg.py --seed 7   # reproducible run
python tune.py           # outcome-distribution sweep over layouts
```

Use `PYTHONIOENCODING=utf-8` when piping output (Windows cp1250 default). Output
is intentionally ASCII-only, so plain runs are usually fine.

## Core mechanics (see `rpg2-rules.md` for the full spec)

- Three stats — **DEX** (who lands), **STR** (wound severity + soak), **STA**
  (a draining clock; **Winded** at STA ≤ 3) — plus an **HP** wound pool.
- Each round is an opposed `2d6 + DEX − (HP lost) − (2 if Winded)` exchange.
  Higher roll lands; `severity = margin + atkSTR − defSTR` maps to a wound tier
  (deflected/graze/wound/grievous/killing blow). **HP lost is itself a roll
  penalty — the death spiral is the whole point.**
- `group_combat` generalizes the 1v1 exchange to a melee so a party can be
  swarmed. Heroes focus-fire the weakest foe; foes target party members at random.

## Survival & Resources add-on (now implemented)

See the add-on section in `rpg2-rules.md` for intent. In `rpg.py`:
- **HP carries across the whole run** (drains like STA, never a per-fight reset),
  with only a minimal `HP_RECOVERY_BETWEEN_ROOMS` catch-breath; healing otherwise
  comes from potions/spells/resting between adventures. **0 HP = Down** (out of
  this fight; stands back up at `REVIVE_HP` next room), **not Dead**.
- **Power** + an **ability** (`heal` / `bulwark`) per entity. `_try_save` spends
  Power to step a blow down one tier — always buying off a *killing* blow, and a
  *would-Down grievous* only when a reserve remains. `_attack` logs the raw blow
  and the bought-down result.
- **STA is per-day**: it carries across rooms (drains, never resets) with only a
  small `STA_RECOVERY_BETWEEN_ROOMS` catch-breath. It's the binding clock.
- **Items** (`healing` / `power` / `stamina`) are a per-day stock. A healing
  potion is *prepped* before a room (`start_fight`) for HP regen; `rest` spends
  power/stamina potions deliberately when low.
- A character only truly **dies** on an unsaved killing blow; `outcome()` counts
  only the slain.

## The current prototype scenario

- **Party:** two random elite-veteran humans, each a `precise` / `powerful` /
  `steady` archetype (`ARCHETYPES` in `rpg.py`), each with Power, one save, and a
  starting `default_kit`.
- **Dungeon:** rooms of skeletons, `DUNGEON_ROOMS = [2, 2, 3]` (one "day"). HP,
  STA, and the resource stock all carry across rooms (only minimal catch-breaths);
  wounds persist for the run.
- **Skeletons:** brittle, weak individual hitters (DEX 3 / STR 2 / HP 5), no
  Power/kit but tireless — the threat is *numbers*, matching the goblin/swarm
  puzzle in the rules, not raw power.

## Balance / tuning

Deaths are now the **rare earned tail**, so `tune.py` reports attrition, not just
the death split. At `[2, 2, 3]` over 20k runs: ~**96% / 4% / 0.2%** truly slain,
a **Down in ~53%** of runs, and by the end ~**77% Power / ~13% STA** left with
healing potions fully spent. The fail state is depletion (STA is the binding
clock); single fights stay winnable, the *run* is the challenge.

Difficulty levers, easiest first: edit `DUNGEON_ROOMS`, then survival tunables
(`SAVE_COST`, `HEAL_REGEN`, `STA_RECOVERY_BETWEEN_ROOMS`, `default_kit`), then
skeleton stats, then party `ARCHETYPES` (Power/ability included). **Always re-run
`tune.py` after touching any of these** — small changes swing both lethality and
the attrition curve.

## Conventions

- Stdlib only; keep `rpg.py` self-contained and importable (`tune.py` imports it).
- Keep narrative/log output ASCII (no em-dashes or special glyphs) for Windows.
- `Entity` is `@dataclass(eq=False)` so instances are identity-hashable (used in
  combat sets) — don't switch it back to value equality.
- Two layers, kept separate: thin mechanics in code, rich flavor added by the DM
  over the log. Don't bake prose into the engine beyond terse event lines.

## Not yet built (the point of the design)

The **between-fights layer** as *player choice*: gold/XP, raising stats toward an
archetype, gear that shifts stats / soaks severity / adds STA, picking fights you
counter, composing the party so builds cover each other, and *buying* the
consumables the survival layer now spends automatically. The survival mechanics
(Power saves, items, Down/Dead, the day economy) exist; what's missing is the
player deciding how to allocate and stock them. See the "Between-fights layer"
and "Survival & Resources" sections in `rpg2-rules.md`.
