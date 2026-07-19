# Design log

Dated records of the major design sessions: what was discussed, the road
the discussion took, and what was decided. The *decisions* live on in
plan.md (roadmap), rules.md (mechanics), and dm.md (play) — this file
keeps the reasoning trail so a settled question stays settled. Newest
last. (The benchlog is this file's sibling for measured tuning.)

---

## 2026-07-19 — The villain pivot (brainstorm → karma & heat v1)

**Where it started.** The designer's diagnosis of the prototype: it
plays like an idle game — powerups plus some loss chance, very linear,
little mechanical and no narrative choice. It is not a strategy game and
shouldn't try to be (mechanics too shallow, stats hard to display,
complex tactical input tiring in chat). The experiment still has
promise, and the superpower to tap is the AI itself — free narration,
NPCs animated in a way CRPGs can't. Maybe the game works better as a
simulation engine for the narrative than as a gameplay-first game.

**The proposed direction.** Facilitate and encourage *evil play*: by
video-game logic conquering a map beats keeping it frozen. Conquer the
world by level 20; get stronger by taking territory while ever-stronger
alliances and heroes push back. Keep it dual (Good play must survive —
e.g. liberating a world half-conquered by someone else). The evil must
be cartoonish, not depressing (kick the puppy → its parent shows up for
a dire-wolf fight; pet it instead and you still fight the parent,
framed non-lethal). A candidate frame: an imp from hell tasked with
doing evil — helping people brings hell's disciplinary forces instead.
Satellite ideas from the same brainstorm: luxury items the PC is
encouraged to acquire and flaunt (envious hell officials, heroes coming
to reclaim the holy golden elephant); good/bad karma as XP that unlocks
abilities AND invites stronger attacks (a better version of the old
"gain power to do quests above your level" problem); characters more
prominent; food as a survival element; a very tight first 3 levels; a
Diablo-ish over-the-top weapon layer with bigger numbers; the map
question (province list vs grid vs hexes); more colorful combat moves;
tone less Warcraft, more Discworld/Conan.

**The discussion's key moves.**

1. *Sharpening the diagnosis*: the game had become a difficulty curve
   with a purse — every decision is "pick the right level number" and
   nothing the player does changes what the world is. The pivot is not
   "evil mode"; it is making the player the CAUSE of the world's state.
   Evil is the tone that makes that fun instead of grim.
2. *Karma-as-heat identified as the load-bearing idea*: the throwaway
   line "karma as xp unlocking abilities and inviting stronger attacks"
   replaces the quest board as the difficulty-selection mechanism
   (difficulty by consequence, a throttle the player pumps), collapses
   the content-escalation problem into one feedback loop (sin → posse →
   killing the posse is itself sin), and feeds the AI-DM superpower
   (retribution as recurring named people, not encounter rolls).
3. *Reuse discovered*: the conquest questline (story.py) is the new
   direction's machinery pointed the other way — waves, named faces
   over reskins, occupation tags. The rival-conqueror idea can BE the
   existing aggressor. The map answer falls out: the list of lands with
   ownership tags, exactly like `[UNDER THE YOKE]`.
4. *Pushbacks accepted*: no big-number rework (the Diablo feel comes
   from named/masterwork instances with authored riders — roadmap item
   5); no food/hunger meter (the luxury/greed economy does that job as
   a voluntary sink with consequences — and it is Discworld-funnier);
   hexes/grids dead on arrival at 40 columns.
5. *The fork*: karma beside XP vs merged. First lean was beside (safe);
   the designer, thinking it through mid-reply, flipped it — merged,
   because a separate currency re-opens "what does karma actually get
   you" while bucketing XP gets the whole loop for free. Settled: XP
   bucketed by the alignment of the work; heat = the level gap
   punishment arrives at; zero bad karma = the old game exactly, live
   and untouched.
6. *Tone doctrine landed*: the engine only ever resolves fights against
   things that fight back; the wickedness itself is narration, in the
   cartoon register (dm.md).

**What shipped the same session (karma & heat v1** — rules.md's Karma &
Heat add-on; `karma.py` + quests/session wiring**):** quest `align`
flags; XP bucketing with the penance burn (1:1); heat =
`bad_karma // (100 × level)` capped at 3; the shadow board
(`board --dark`, lazy per-settlement-day, bench-invisible, dark gold
×1.5); the punishment posses (Watch → bounty guild → crown's huntsmen →
heroes of the realm; cooldown 2 days, chance 0.6, at arrivals and
nights; generated named leader kept as the nemesis seed); the DM surface
(`karma`, `karma bad/good N`, `award --dark/--good`, `forge --dark`);
the seven generic dark templates (the puppy quest included, as
mandated). Verified: worldgen/benches untouched (sanity bench run
within noise), full dark loop played end to end in a test game.

**Deliberately NOT decided yet** (open in plan.md): karma AS the level
track (the full merge); what bad karma *buys* (hell ranks, evil powers);
conquest ticking's exact shape; the army-mechanic question; all heat
constants (hand-set, sim-unverified — the table tunes them).

**Next step agreed**: play the dark path's first ten messages — the
tone probe. The first 3 levels are the only part that ever gets tested.

## 2026-07-19 (later) — The hell pact (dark quests, the big content pass)

**The designer's input.** A long brainstorm reframing the dark path's
fiction and asking for a major dark-quests implementation: the PC is
NOT a neutral adventurer but a low-ranking employee of Hell — a mortal
of a game race (explicitly not an imp) under a pact with an evil god;
hell's aim is weakening the orderly universe's fabric (gates,
summonings); order is maintained by the gods of Light and their
agents (paladins, hunters, priests, hired heroes, watchmen, mobs) and
is often not Good. Hell assigns tasks (a curriculum in vice, difficulty
suited to the player with the margin of error running upward) via
unseen job boards / mail / couriers; refusing — Chickening Out — draws
infernal enforcers; hell can be bribed; tasks can be ignored up to a
point while questing normally. Plus ~30 task ideas, a mandate to
formalize a more complex quest structure, the rule that heroic
adventurers never kill the PC (he loses party, gold, and all bad
karma; heroes think him dead or he runs in shame, hell laughing), a
minor DM rule (taking a quest opens the fight in the same message, no
wasted arrival turn), and a directive: **abandon XP/gold balance for
now — quest variety does more good.**

**The triage** (asked for explicitly: cut / later / dm.md lore):

- *Shipped as mechanics*: the pact frame (default-on at `new`,
  `--no-pact` opts out — settles plan.md's imp-frame question as
  MORTAL EMPLOYEE), assignments (`TASK_INTERVAL_DAYS` 4, spread 0..+2,
  WORD FROM BELOW), Chickening Out (grace 4 d, hell posses at party
  +1 escalating per beating, neutral XP), `bribe` (30g × level, 10 d),
  the caper structure (deed = PC 2d6+stat vs DC 10-11, clean-or-botch
  with +15 witness karma; twist = priced terms, `settle` at ×0.5), the
  left-for-dead mercy (law: party/purse/karma forfeit; hell: purse
  fine + task withdrawn — never GAME OVER vs posses), and 17 new dark
  templates (steal/fence, beast-caging, dine-and-dash, priest
  sacrifice, puppy sacrifice, village sack, bank vault, poisoned
  round, mansion murder, evil weapon, sacred-weapon corruption, altar
  desecration, coworker betrayal, cultist protection, hellgate,
  powder trade, nobleman's land grab) — 24 dark templates in all.
- *To dm.md as world lore*: the pact fiction, the world of Order
  ("often not Good" as questgiver color), hell walkable-but-bullying
  (narration-only), the curriculum doctrine (self-assigned dark work
  encouraged), the non-lethal combat note (0 HP = knocked out when the
  fiction says so), the freeform "graded on body count" tasks (forge
  --dark + karma bad N), and the take→fight turn rule.
- *Planned for later (plan.md)*: hell as a place (gladiator pits +
  bribe-to-lose, the bone-paid castle), the geographic wanted level
  (heat is the global version), standing enterprises (powder network
  as a holding), the rot spell (wants conditions), war-side-taking
  (already villain roadmap 6), artwork/relic flaunting (already the
  greed economy, item 5).
- *Cut / folded*: the tax-doubling nobleman (Debt Collection already
  is it), nothing else — the input was nearly all usable.

**Design calls made while implementing**: deed success closes the
site through the same `_close_site` path as a fight (full lump, no
encounter XP — stealth runs karma-light, kept as a happy accident);
enforcer XP is neutral (demon-farming must not become penance);
beating enforcers never closes the task (only doing it, bribing, or
losing does); the mercy covers POSSES only — roads and quests still
kill (the mandate was about heroic adventurers, and a deathless world
would unmake the game). Balance: everything hand-set, no bench (the
directive), recorded in develop.md.

**Next step unchanged**: play the dark path's first ten messages — now
with the pact knocking from message one.
