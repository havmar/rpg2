# Roadmap

What is left to build, in order. This file is **planned features only**:
design principles (the design spine, the three currencies, tone, legibility)
live in `rules.md`; the play protocol in `dm.md`; dev conventions and current
balance numbers in `develop.md`. Anything already implemented is documented in
`rules.md` and the code, not here — when a feature ships, delete it from this
file rather than marking it done.

---

## THE VILLAIN PIVOT (2026-07-19) — the direction the roadmap now serves

The 2026-07-19 design session reframed the game. The diagnosis: the game
had become a difficulty curve with a purse — real decisions, but all the
same decision (read the board, pick a level), and nothing the player does
changes what the world *is*. The project's actual superpower (the AI
freely narrating and animating people) had nothing to chew on.

**The vision:** the player becomes the *cause* of the world's state
instead of its janitor. The game facilitates and encourages a **cartoon-
villain campaign** — conquer, extort, steal, flaunt — while remaining
fully playable as the old Good game (dual by construction, never two
rulesets). Tone: Discworld/Conan, pratfall evil, never grimdark (dm.md
owns the register). ~~The candidate frame for the PC: an imp sent
topside with a quota~~ — **SETTLED later the same day (the dark-quests
session): the PC is a MORTAL of an ordinary race, a low-ranking
employee of Hell under a pact with an evil god.** Not an imp. The pact
rides every new save (`new --no-pact` opts out); rules.md's Karma &
Heat add-on, "The Hell Pact", has the shipped mechanics (assignments,
Chickening Out enforcement, bribes, the caper structure, the
left-for-dead mercy, seventeen new dark templates).

**The load-bearing mechanism (SHIPPED as the first slice, 2026-07-19 —
rules.md's Karma & Heat add-on):** XP bucketed by the alignment of the
work that paid it; bad karma sets HEAT; heat sends escalating lawful
posses at party level + heat; honest work burns karma 1:1. Difficulty
selection by consequence — the throttle the player pumps — and the
ratchet (killing the law is itself a crime) is the villain campaign's
level curve. Karma rides *beside* levels for now: merging them fully
(karma AS the level track) stays an open question below.

**Decisions settled in the session** (recorded so they stay settled):

- **Karma merged into XP accounting** (bucketed awards) over a separate
  currency — a separate track would re-open "what does karma actually
  get you"; the bucket answer is free.
- **The map stays a LIST.** Conquest will be ownership tags on the
  existing lands/settlements readout (`[YOURS]` beside `[UNDER THE
  YOKE]`), like the occupation layer already does. No hexes, no grid —
  everything prints at 40 columns.
- **No big-number rework.** The Diablo feel (whip of bad karma, the
  Midas sword) comes from named/masterwork instances with authored
  riders (the named-weapons item in "After that" below), never from
  renumbering the 2d6 engine the whole bench suite calibrates.
- **No food/hunger meter.** The job food was meant to do (a scaling
  gold sink with flavor) goes to the GREED ECONOMY instead (below):
  luxury display as a voluntary sink with consequences, monster-cooking
  as its flavor. A hunger meter is the upkeep bookkeeping the heroic
  tone bans.
- **Conquest is ticking a list, not a strategy layer.** The player's
  dials stay few and chat-legible: where to strike, how hot to run,
  what to flaunt. Anything that can't be decided in one chat line is
  over the line. (An army mechanic is parked as an open question, not
  promised.)

### The villain roadmap (build order)

1. **Play the dark path** (no code): run the first ten messages of a
   wicked campaign on the shipped slice — the tone probe. Does cartoon
   evil sing at the table? Does heat feel like a throttle? The first
   3 levels are the only part that ever gets tested; make them land.
2. **Nemesis persistence.** Posse leaders who survive (party fled, or
   the leader's row lived) RETURN: same face, +1 level, a grudge line.
   The save already keeps `last_leader`; grow it into a small nemesis
   record. This is the AI-DM superpower feature — recurring named
   enemies the DM can animate. (Absorbs the parked "rival" idea.)
   *Pulled ahead of conquest (2026-07-19, the ordering vibe check):
   it is the cheapest item on the board (a thin save record + one
   posse-spawn hook), it makes the just-shipped heat layer read as
   story instead of a random tax, and it is small enough to slot in
   mid-playtest the moment the first surviving leader is felt to be
   forgotten.*
3. **Conquest ticking** — the `conquer` verb: beat a settlement's
   garrison (a generated site at the settlement's band), flip an owner
   tag on the map, collect a daily tribute trickle; occupied-by-you
   settlements refuse honest boards but keep shadow ones. Reuses the
   occupation machinery. Bad karma prices the deed; holding land should
   probably RAISE the heat floor (standing wickedness). *Deliberately
   after the play probe and the nemesis slice: it is the meatier build,
   and its open calls (the heat-floor question, tribute rates) want a
   played dark run behind them.*
4. **The good-karma mirror — the dual campaign.** *Half-shipped
   2026-07-19*: hell's disciplinary posses exist (Chickening Out — they
   punish DISOBEDIENCE, an ignored assignment), and the PC frame is
   settled (mortal pact-holder, default-on). What remains is the mirror
   proper: hell auditing a too-*virtuous* employee (good karma as the
   liability axis), so the hypocritical middle path (both meters hot)
   becomes the comedy jackpot. One mechanic, two skins.
5. **The greed economy.** Luxury items as gold sinks that generate bad
   karma and heat when FLAUNTED (envious hell officials, heroes coming
   for the holy golden elephant): each displayed trophy is a standing
   quest hook pointed at the party. Feasts (cook the monster) as the
   satisfaction/karma variant. This is also the L15+ "what is gold
   for" answer arriving early — coordinate with domain play.
6. **Dark content pass**: race-flavored dark templates (the generic
   seven ship in the slice), war-integration (side WITH the story
   layer's aggressor?), parley/bribery with posses, karma-flavored
   named weapons riding item 5 below.

---

## The levelling framework — COMPLETE (A/B/C shipped 2026-07-17)

Carry-forwards, parked (not scheduled):

- **Enemy-side moves** (giving the drilled soldiery two moves each) and the
  **second-wave moves** (guard-break, taunt, battle-cry) — a later content
  pass with its own bench round (from session B).
- **The day-stamp spoilage variant** — session C shipped the freshness
  STOCK CAP (rank + 2 brewed items) over per-potion spoil timestamps. If
  spoilage should ever be FELT, the cheap variant is one day-stamp per
  hero's brewed batch — noted, not built.
- **Alchemy conditions** (poisons, oils) — wait for the conditions system;
  alchemy is its first customer (the parked venom note).

Open to feel out in PLAY: points-per-level 3 vs 4 and training 2n
(re-open only if the mid-band feels grim); the **kit-shrink dial**
(`KIT_STAMINA` 1->2 or a higher `KIT_FORAGE_CHANCE` if play reads too
grim); the **DEX potion** (rank 4/+1 under the standing +DEX warning).

---

## Queued — the banded quest inventory (worldgen reframed)

*(Story-layer batches 1-2 shipped 2026-07-12; pacing anchors measured
2026-07-12: played campaigns L10 ~ day 45-65 (~10-12 chat hours), L20 ~
day 110-150 (~25-30 hours). Still good and cheap once wanted in play:
war-flavored reskins on local quests in threatened lands, and a rescued
recruit as an extra wave-3 tangible.)*

- The designer's vision made concrete: **a land always has work at every
  band, plus objective high-level problems that exist independent of the
  player** (landmark problems known by rumor from level 1) and **banded
  refill** (each settlement keeps a few live problems per level band,
  lazily generated as consumed). Replaces the up-front ~26k-XP posting
  and its coverage assert. Schedule as its own session. *(The shadow
  board, 2026-07-19, is a working precedent: lazily rolled, pruned,
  bench-invisible — the refill wants the same shape.)*
- Later sim hook (parked): other heroes occasionally solve, or die to, a
  landmark problem while the player is elsewhere.

Story items on the shelf:

- **The apocalypse questline — the L12-20 second spine.** Parked until
  the magic tier exists (its payoff enemies are demons above the dragon
  row). *(Pivot note: under the villain frame this may become the
  RIVAL conquering force — the thing that conquers half the world if
  the player doesn't, or the employer the player answers to. Decide
  when the good-karma mirror lands.)*
- **Progression frames** (guild advancement, the legendary-smith arc) —
  narrative wrappers around the same combat quests; cheap now that
  questlines exist.

**A career finding to design against**: the top band (15-20) is still
the hard edge (per-quest wipe 40-65% at level) and still waits on
masterwork gear, armor, and magic for its missing player power.

---

## After that (in rough order)

*(Shipped and struck from this list: placeholder magic + cross-land
deliveries 2026-07-14; Magic & MIND 2026-07-15; ranged combat & guns
2026-07-16; party/CHA layer 2026-07-11 — mechanics all in rules.md.)*

1. **What remains of the magic item**: stat transcendence + magic items
   (the membrane: +stats to ~double the natural cap; +DEX an order of
   magnitude rarer than +STR/+pool); **the wraith** (buildable now that
   attack spells exist); **rank-4 capstones** (authored tomes/mentors —
   the 14-20 band's player power); **enemy spell use** (openers, not
   just bolts); **flight ranks 3-4**.
2. **Armor** — provisional design: shifts the incoming wound tier down
   at the cost of a DEX penalty and higher STA drain. *Status: adopt,
   simplify, or defer.* (Designer lean: probably never important.)
3. **Named & masterwork weapon instances** — the tiers exist in the
   schema; nothing placed yet. Named weapons carry authored provenance
   and are story beats, never drops. **The pivot leans on this item**:
   the over-the-top villain arsenal (leech blades via the regen field,
   the Midas sword's gold rider, the whip of bad karma paying karma on
   kills) are named instances with authored riders — no renumbering.

---

## The major-feature shortlist (2026-07-14) — ordering notes

Foundations all shipped (magic, ranged, levelling); what stands:

- **Conditions** (poison, bleed, disease) — the missing enabler behind
  "more varied enemies"; varied magic wants it too.
- **Free-play facilitation / overriding the mechanics** — mostly dm.md
  doctrine plus the override surfaces that already exist (`forge`,
  `give --as`, the hand-editable save). Cheap, worth doing early.
- **Professions** — a between-fights layer off downtime and the economy;
  natural feeder for domain play.
- **Intraparty mechanics & prominent main NPCs** — deepens shipped
  layers; its big multiplier is the parked off-screen event simulation.
  *(The nemesis record — villain roadmap item 2 — is this thread's
  first concrete customer.)*
- **Region detail & exploration depth** — content plus the same
  off-screen tick.
- **Domain play** — the endgame layer (holdings, followers, rulership);
  the natural answer to "what is gold FOR at L15+". *(Pivot note:
  conquest ticking is domain play's thin edge — build item 3 of the
  villain roadmap first and let domain play grow out of whatever
  tribute/holding state it creates.)*
- **The content passes** — deliberately last within their threads.

---

## Parked ideas (agreed to exist, not scheduled)

- **Hell as a place** (2026-07-19, dark-quests session) — walkable any
  time at no cost, dangerous, demons love bullying. Today it is pure
  DM narration (dm.md); the parked content: the gladiator pits of hell
  (with the bribe-to-lose-on-purpose bout), the castle bought in human
  bones, hell's org chart above the collections agent. First customer
  of any hell map.
- **A geographic wanted level** (2026-07-19, dark-quests session) —
  searched-for in one settlement / the whole land / all lands, as the
  designer's brainstorm named it. Heat is the GLOBAL version and
  shipped; the geographic split is a refinement — park until heat has
  been felt at the table.
- **Standing dark enterprises** (2026-07-19, dark-quests session) —
  the powder network (and rackets generally) as HOLDINGS that earn and
  draw rivals over time, not one-shot quests. The Powder Trade
  template ships the seed version; the standing layer feeds domain
  play / conquest ticking.
- **The rot spell & evil magic content** (2026-07-19, dark-quests
  session) — "learn an evil spell that quickly rots the opponent
  alive; use it on an innocent bystander" wants a new spell (and the
  conditions system); park with the magic content pass.
- **War-side-taking** ("a land has attacked a neighbor — help the
  aggressor") — already the dark content pass / war-integration item
  (villain roadmap 6); noted here so the brainstorm line has a home.
- **An army mechanic** (2026-07-19) — "some army mechanic might be
  good" for the conquest game; parked until conquest ticking has been
  felt. The guard rail stands: one chat line per decision, or it's out.
- **Karma-gated powers / hell ranks** (2026-07-19) — bad karma
  currently buys nothing but heat and rich work; whether lifetime
  wickedness should UNLOCK anything (evil abilities, hell hierarchy
  ranks, the imp's promotions) is deliberately open — see Open
  questions.
- **Summoning** (2026-07-15) — needs its own design round (action
  economy is the game's strongest measured force).
- **Antimagic** (2026-07-15) — trivial to build, nothing to counter yet.
- **Ward, the tier-shift shield spell** (2026-07-15) — note it doubled
  as the provisional armor design.
- **Opener economy in play** (2026-07-15) — if played wizards resent
  the pool burning on trash fights, the fix is a session-side hold
  toggle, not engine smarts.
- **Opt-out tutorial register** (2026-07-14) — relevant only if the
  game gets a second player.
- **Off-screen event simulation** (2026-07-12) — a world tick rolled at
  settlement arrivals from small event tables, day-stamped. First
  customers: the landmark problems, the nemesis record, the rival.
- **Faction reputation** — designer has more to spec; nothing until
  then. *(Note: karma IS a first faction axis — law vs the party;
  spec the rest against it.)*
- **Settlement flavor lines** — valuable but easy; deliberately not yet.
- **The rival** — ABSORBED into the villain roadmap (nemesis
  persistence, item 2) and the apocalypse-as-rival-conqueror note.
- **The traitor twist** — one authored questgiver per conquest variant
  collaborating with the aggressor; cheap authored beat.
- **Morale & surrender** — enemies breaking, yielding, bargaining.
  *(Pivot note: posse PARLEY — bribing the Watch, demanding surrender
  — wants this; build them together.)*
- **Story recruitment** — "the ogre yields and joins you", DM-driven.
- **Weapon reach** — a small first-exchange modifier; distinct from the
  field.
- **Cover & terrain on the field** (2026-07-16) — prose until the
  wilderness gets a terrain pass.
- **Friendly fire into the press** (2026-07-16) — only if play shows
  free focus-fire reading wrong.
- **The 2-STA heavy swing** — sim-rejected while Spent is lethal.
- **d12 variance experiment** — don't fork the dial while lethality is
  settling.
- **Asymmetric Spent** — soften attack to −3 if spent-vs-fresh grinds
  ever feel wrong.
- **A PC happiness stat** — kept OFF (2026-07-11).
- **Prey depletion (the hunt-spam lever)** — only if play shows
  hunt-spam degenerate.
- **Per-weapon pressure dice** — rejected; 2d6 stays the one dial.
- **Level requirements on masterwork/legendary weapons** — rejected;
  authored placement gates them.
- **The "obliterating" wound tier** — parked until the top band is
  authored.
- **Venom / conditions** — the bite carries the spider row until
  conditions exist.
- **Survival/adventure-sim pivot** (hunger, upkeep, inventory) — kept
  on the books as a possible deliberate pivot, but note 2026-07-19
  chose the GREED ECONOMY over food as the villain game's sink; this
  pivot is further away than it was.
- **Power potion re-stock** — if War-Breath ever makes Power scarce.
- **Crit/fumble on the 2d6** — fattens both tails of every exchange;
  full bench re-run before judging.
- **Party members as lives, the wipe version** — the in-fight half
  shipped as fate's bargain; watch whether recruit renewal softens it.
- **A PC-centric career sim** — if played campaigns drift from the
  bench's even-duo story. *(Pivot note: a karma-playing career variant
  — dark quests + posses in the policy — is the natural check once the
  villain game has been played; today no sim sees karma at all.)*
- **Quest history readout** — cheap; gives the save a memoir.
- **Site persistence / repopulation** — the stick version of one-go
  sites; only if the streak isn't pressure enough.
- **Give the rapier its niche back** — do nothing until felt in play.
- **Re-annotate the bestiary for the pain-2 party** — calibration
  polish, not a fire.

---

## Open questions

- **Karma AS the level track?** (2026-07-19) The shipped slice runs
  karma beside XP (bucketed awards). The radical version — karma IS
  progression, levels EARNED by wickedness under the imp's quota —
  would make the villain frame total. Decide after the dark path has
  been played; the bucket design was chosen precisely so the merge
  stays cheap.
- **What does bad karma BUY?** Heat and gold-rich work only, today.
  Candidates: karma-gated abilities, hell ranks (titles + perks), the
  luxury economy's prices. The other half of the original "good and bad
  karma as xp unlocking abilities" idea — deliberately deferred out of
  the first slice.
- **The heat curve's numbers** — KARMA_HEAT_STEP 100, HEAT_CAP 3,
  cooldown 2 days, chance 0.6, dark gold ×1.5: all provisional,
  hand-set, sim-unverified (no sim plays dark). Tune at the table
  first; a karma career sim is parked above.
- **Armor:** adopt, simplify, or defer (the least-developed system;
  designer lean: never important).
- Every constant is provisional and sim-tuned, never hand-designed — the
  current numbers live in `develop.md` ("Balance / tuning").
