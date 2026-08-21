# RPG2 — Combat Sim Prototype

A mechanics-centered fantasy RPG played through a terminal coding agent in
the style of a retro text adventure, with the agent running the game
(2026-07-21 pivot). Fights resolve on their own
(autocombat, with at most one mid-fight pause) and produce an outcome plus a
narrative log; the DM's prose over the script output is minimal — present
tense, second person (`writing.md` owns the shared fiction register; `dm.md`
owns its use at the table). The player's real decisions happen *between*
fights — and at the pause. The engine owns the numbers.

## Which kind of session is this? (settle this first)

This file is only a dispatcher — the first thing to do is pick the right
mode guide. `writing.md` is the shared fiction/content guide across both
modes:

Before reading or changing project state, run `git status --short --branch`.
If the tree is clean, fast-forward it with `git pull --ff-only`; if it is
dirty, preserve and understand the local work before pulling. Never assume
the checked-out copy already contains the latest UI or rules changes.

- **PLAYING or TESTING a game (running a playthrough as DM):** `dm.md` and
  `writing.md` are your ENTIRE instruction set — play protocol, fiction
  style, verbosity, quick mechanics reference. Read both before the first
  scene. Nothing in the dev docs governs how you speak at the table: its
  be-thorough-and-verbose reporting register does NOT apply to play, and
  out-of-character design commentary stays out of the game unless the
  player asks for it. Concise, in-fiction narration is the rule; dm.md
  says exactly how.
- **DEVELOPING (changing code, mechanics, docs, or tuning):** `develop.md`
  is the dev guide and is REQUIRED reading — the workflow, the file index,
  the dev map, conventions, difficulty levers, and the current measured
  balance numbers all live there. Read `writing.md` too whenever the task
  writes or generates fictional content. Don't start a dev task from this
  file alone.

> **Played reality (2026-07-27):** no playthrough has ever gone past
> level 4. Getting further takes hours of play, and something important
> to fix has always come up first. Treat everything above the low band
> as unplayed: when designing, building, or testing, put whatever needs
> to be learned or felt inside the first four or five levels. (Since
> 2026-08-05 `new` rolls the starting level 1-18 and `new --level N`
> fixes it, so an unplayed band can at least be LOOKED at directly.)

## The documents

- `dm.md` — the DM playbook (play protocol, application of the fiction
  style at the table, quick mechanics reference).
- `writing.md` — shared fiction and content style for DM prose and authored
  or generated quests, places, people, items, and event lines.
- `scene-example.md` — the worked model of the DM's scene page: a game
  start and a fight turn in the play voice (see dm.md and writing.md).
- `rules.md` — the ruleset: source of truth for mechanics and the design
  spine.
- `plan.md` — the sole active roadmap and build contract. Shipped work is
  removed from it: since 2026-08-21 it carries only the roadmap BEYOND the
  fixed-Europe and tile-economy arcs (the spring snapshot and trouble,
  politics and war, fantasy and magic, settlements revisited, the deferred
  leftovers). Each item is a future design conversation; none is scheduled.
- `develop.md` — the dev guide: workflow, file index, dev map, conventions,
  tuning levers, current balance summary.
- `benchlog.md` — the dated tuning history (append an entry after every
  re-measurement; develop.md keeps only the current summary).
- `designlog.md` — the dated design-session history (the reasoning trail
  behind plan.md's decisions; append after every major design session).
- `archive/plan-pre-europe-2026-08-15.md` — the complete roadmap snapshot
  displaced by the Europe-map reset. It is marked historical and is not
  implementation authority; its unfinished and parked ideas return only if
  a later design session deliberately moves them back into `plan.md`.

> **When a feature ships, DELETE its entry from plan.md and write the
> session up in designlog.md** — played rules to rules.md, code pointers
> to develop.md, measured numbers to benchlog.md. Never leave an item in
> plan.md marked SHIPPED or COMPLETE. develop.md's "Where a finished
> feature is written up" has the full rule.

The code files (`rpg.py`, `sites.py`, `quests.py`, `people.py`,
`karma.py`, `conquest.py`, `session.py`, `tune.py`, the `bench_*.py` suite) are indexed in develop.md's
**Files** section — register any new file there.

> Keep THIS file short and register-neutral: it is auto-injected into every
> agent session, play included. Shared fiction style belongs in writing.md,
> dev content in develop.md, and play protocol in dm.md. The body is
> deliberately free of any one agent's name, so the file can be copied to
> another agent's instruction filename unchanged (develop.md's `CLAUDE.md`
> entry has the recipe).

> Project-level environment (Python path, encoding, etc.) lives in the parent
> project's agent-instructions file. Don't duplicate it here.
