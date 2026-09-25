# The player's page (2026-09-25): the arc SHIPPED

THE PLAYER'S PAGE ARC was planned on 2026-09-25 and **built whole the same
day, across five sessions**: rpg2's own claude.ai Artifact page for the
player, a port of dream's `web/` page and its keeper's-turn protocol. This
file was the arc's build contract -- what existed, the architecture calls,
the data contract, each session's files, tests and docs, and a "notes /
deviations" addendum under every shipped session. Every session has now
landed, so what is left is this note and a map of where the content went.
Nothing in the contract went unbuilt; the one idea it deliberately left
for later (structured moves beyond the pause) is a roadmap item in
`plan.md`.

## Where it all went

| what | where it lives now |
|---|---|
| how the DM runs a game on the page: a new game, the keeper's turn, the page shape of `ui/scene.md`, the pause, the save rule | **dm.md**, *Page play -- the player's page* (and the pointers in *Starting and continuing* and *The scene page*); `scene-example.md`'s page-play state |
| the data contract (the five `game/` singletons, `chronicle/`, `fights/`, `moves/`), the keeper's commands, pins, publishing, the page's tabs and picker, the build, the local table, the e2e, adding to the page | **web/README.md** |
| the code pointers | **develop.md**: Files (`page.py`, `publish.py`, `test_page.py`, `web/`, and the `session.py` / `rpg.py` entries), Running, the dev map's "The player's page", Conventions |
| the build records, with every settled call and the test counts | **designlog.md**, 2026-09-25 and (B) through (E) |

## The five sessions

1. **The projection** (designlog 2026-09-25) -- `page.py`: the five
   singletons built from the functions the ui pages use, the move
   contract, `pause_args` over the session's own pause checkers,
   `RPG2_HOME`.
2. **The fights kept and the keeper's publish** (B) -- `CombatLog`'s
   round spans and outcome, every session fight queued on its own,
   `publish.py` (pinned batches, the page's record), `page.py moves`.
3. **The Angular page** (C) -- `web/`: the store, Story, Answer,
   Chronicle, Party, Fight, Fights, the local table, the first e2e.
4. **The pause picker and the rest of the tabs** (D) -- the picker, Map,
   Quests, Record, the level-up, option chips, unread marks, the full
   e2e.
5. **The play protocol and the dress rehearsal** (E) -- dm.md's Page
   play, the docs, a rehearsal played from the docs alone, the player
   log held to 40 columns, a closed pipe no longer costing a save.

## The calls this arc stood on

Kept here because they outlive the build:

- **The page shows what rpg2's player-facing surfaces show, never more**:
  the projection calls the same functions the ui pages are built from,
  and the DM-only surfaces never feed it.
- **The pause is the one structured move.** Everything else the player
  says in words; option chips only fill the answer box. A move is data:
  the keeper plays a pause only as the command `page.py moves` prints.
- **The save stays out of git** (rpg2's rule, kept on purpose): the page
  and its record survive a lost container, the game does not. dm.md's
  Page play tells the DM to say so to the player, and to commit the save
  only when asked.
