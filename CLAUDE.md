# RPG2 — Combat Sim Prototype

A combat simulator for a fantasy RPG, played through Claude Code with Claude
as DM. Fights resolve on their own (autocombat, with at most one mid-fight
pause) and produce an outcome plus a narrative log; the DM narrates *over*
that log. The player's real decisions happen *between* fights — and at the
pause. The engine owns the numbers; the DM owns the fiction.

## Which kind of session is this? (settle this first)

This file is only a dispatcher — the real instructions live in one of two
places, and the first thing to do is pick the right one:

- **PLAYING or TESTING a game (running a playthrough as DM):** `dm.md` is
  your ENTIRE instruction set — play protocol, narration style, verbosity,
  quick mechanics reference. Read it before the first scene. Nothing in the
  dev docs governs how you speak at the table: the dev guide's
  be-thorough-and-verbose reporting register does NOT apply to play, and
  out-of-character design commentary stays out of the game unless the
  player asks for it. Concise, in-fiction narration is the rule; dm.md
  says exactly how.
- **DEVELOPING (changing code, mechanics, docs, or tuning):** `develop.md`
  is the dev guide and is REQUIRED reading — the workflow, the file index,
  the dev map, conventions, difficulty levers, and the current measured
  balance numbers all live there. Don't start a dev task from this file
  alone.

## The documents

- `dm.md` — the DM playbook (play protocol, narration style, quick
  mechanics reference).
- `rules.md` — the ruleset: source of truth for mechanics and the design
  spine.
- `plan.md` — the roadmap: planned features only, plus parked ideas.
- `develop.md` — the dev guide: workflow, file index, dev map, conventions,
  tuning levers, current balance summary.
- `benchlog.md` — the dated tuning history (append an entry after every
  re-measurement; develop.md keeps only the current summary).

The code files (`rpg.py`, `sites.py`, `quests.py`, `people.py`, `story.py`,
`session.py`, `tune.py`, the `bench_*.py` suite) are indexed in develop.md's
**Files** section — register any new file there.

> Keep THIS file short and register-neutral: it is auto-injected into every
> session, play included. Dev content belongs in develop.md, play content in
> dm.md.

> Project-level environment (Python path, encoding, etc.) lives in the parent
> `C:\minden\projects\CLAUDE.md`. Don't duplicate it here.
