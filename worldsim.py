"""The world layer -- the WORLD & NPC SIMULATION build's FRAME (2026-08-07).

plan.md's ladder, the frame session: `worldsim.md`'s five record kinds stop
being prose and become data, and the save grows a world layer under every
land. The frame is the product -- the content here is the seed that proves
the loop, two or three economy cards a land lifted from the packets.

The shape, in the order the loop runs it:

- **The wealth roll.** Every land rolls 2d6 at worldgen: 2-4 CRISIS,
  5-9 NORMAL, 10-12 PROSPEROUS. Wealth is a STATE in an exclusive slot,
  not a constant -- a card can move it, and a later session's seasons can
  too. Rolled on a DERIVED rng (the armory's pattern), so no bench stream
  moves.
- **The states.** Day-stamped words on the land record, held through
  places.py's own state machinery (`add_state` / `clear_state`), so the
  world's states and a place's states are one vocabulary and one readout.
  Some live in EXCLUSIVE SLOTS (a land holds one deposit stage, one
  standing of its foreigners) -- setting a slot clears whatever it held.
- **The relations.** Authored directed edges between lands: who eats whose
  grain, who logs whose forest, whose mercenaries come when called. Never a
  traded quantity -- a lookup. The states they DERIVE (a failed harvest in
  Firascir puts grain-scarce on everyone it feeds) are computed at read
  time and never stored, so an edge can be re-authored without a migration.
- **The deck.** Each land's cards, shuffled once at worldgen (the pact
  deck's pattern). A land in CRISIS draws on need; NORMAL and PROSPEROUS
  stay mostly invisible and draw rarely -- prosperity shows through the
  absence of trouble, plus the odd positive card. The draw skips a card
  whose admitting conditions the land does not meet and leaves it in the
  deck for a later day; a card that would only re-assert a slot the land
  already holds never fires (exclusive slots are never contradicted).
- **The card.** Admitting conditions over land, wealth, states and weather;
  up to FIVE outlet effects (quest / priced menu / encounter / news /
  state flip); an optional day-stamp clock. THIS SESSION APPLIES TWO of the
  five -- the news line and the state flip, which are the surfaces the
  frame ships (the news at the roll points, the state diff on `map` and
  `world`). The quest, menu and encounter payloads are carried, validated
  and left for the economy floor session, which owns the full hookups.

Everything is LAZY, SEEDED and DAY-STAMPED: nothing ticks in the
background. A land's day is rolled off `stable_seed(world, land, day)`, so
the roll for day 40 is the same whether it is computed on day 40 or caught
up on day 300 -- which is what lets the world move while the party is away
and be there, changed, when it comes back.

Facts and options (worldsim.md's other two record kinds) ride the authored
packet data: they cost nothing at runtime and are read by the DM, not by
the engine.

The sims and benches never import this file (the karma doctrine). Every
knob is hand-set and sim-unverified -- tune at the table.

Run:  python worldsim.py [--seed N] [--days N]   # eyeball dump: every
                                                 # land's band, deck and
                                                 # states after N days
"""
from __future__ import annotations

import argparse
import random

from places import (LAND_SPECS, add_state, clear_state, land_id,
                    stable_seed)

# --------------------------------------------------------------------------- #
# The knobs (all hand-set, sim-unverified -- the karma layer's doctrine)
# --------------------------------------------------------------------------- #

WEALTH_DICE = (2, 6)            # 2d6 on a weighted middle (settled
                                # 2026-08-07; a knob thereafter)
WEALTH_BANDS = (               # (lo, hi, band) over the 2d6 total
    (2, 4, "crisis"),           # ~17%
    (5, 9, "normal"),           # ~67%
    (10, 12, "prosperous"),     # ~17%
)
BANDS = tuple(band for _lo, _hi, band in WEALTH_BANDS)

CARD_CHANCE = {                 # the chance a land with no live card draws
    "crisis": 0.30,             # one on a given day. Crisis is where content
    "normal": 0.02,             # lives; prosperity shows through the absence
    "prosperous": 0.02,         # of trouble and the rare positive card -- at
}                               # 0.02 a quiet land turns up about one card
                                # in a fifty-day stretch, which is roughly a
                                # played campaign
OPENING_DRAW = ("crisis",)      # bands that fire a card at worldgen, so a
                                # land in trouble is in trouble from scene
                                # one rather than from the first lucky roll
OPENING_DAY = 1                 # ...dated the game's first day, because the
                                # player hears it then: day 0 is worldgen's
                                # bookkeeping, not a day anybody played
CARD_DAYS = (12, 25)            # the default clock a card stands for when it
                                # does not author its own (days)
NEWS_KEPT = 24                  # day-stamped news lines kept per land
NEWS_TOLD = 6                   # ...and the most told at once on return: a
                                # long absence is a summary, not a scroll

# --------------------------------------------------------------------------- #
# The record kinds (worldsim.md, formalized)
# --------------------------------------------------------------------------- #
# STATE -- a word the land holds, day-stamped, visible, changeable. Free
# states stand alone; SLOT states are exclusive (a land holds exactly one
# member of the slot), which is the placegen rule applied to the world.
#
# Two flavors, all the way through: what a card SETS outlives it, and what
# it sets WHILE it stands comes off with it. That holds for the wealth band
# too -- a failed harvest is a season of crisis and then it is over; a vein
# running out is simply what the mountain is now.

STATE_WORDS = {                 # state id -> the readout's short phrase
    # Firascir
    "harvest-failed": "the harvest has failed",
    "toll-squeeze": "the tolls are doubled",
    "overtaxed": "the war tax is on",
    # Mortellaria
    "tax-farmed": "the province is farmed out",
    "paper-worthless": "the banks have shut their doors",
    "coin-flush": "the colony fleet is in",
    # Ensimaa
    "craft-lost": "a master's work is lost",
    "children-taken": "children are being taken",
    # Dvarvengrond
    "strike": "the pits stand idle",
    "claims-collide": "two clans claim one seam",
    # Gibili
    "mills-stopped": "the mills have stopped",
    "convoy-running": "the arms convoys are running",
    # Tergal
    "herd-loss": "the herds are dying",
    "herd-drive": "the great drive is on",
    "mercenary-home": "a war-rich mercenary is home",
    # Derived (never held -- computed off the relations table)
    "grain-scarce": "grain is scarce",
    "timber-dear": "timber is dear",
    "claims-revoked": "the claims are revoked",
    "concession-lost": "the concession is lost",
    "arms-scarce": "arms are scarce",
    "raiders-out": "raiders are on the border",
}

STATE_SLOTS = {                 # slot -> its exclusive members, in order
    "foreigners": ("foreigners-welcome", "foreigners-tolerated",
                   "foreigners-unwelcome"),
    "deposit": ("deposit-normal", "deposit-found", "deposit-drying",
                "deposit-dead"),
}
SLOT_WORDS = {
    "foreigners-welcome": "foreigners are welcome",
    "foreigners-tolerated": "foreigners are tolerated",
    "foreigners-unwelcome": "foreigners are no longer welcome",
    "deposit-normal": "the seams run as they always have",
    "deposit-found": "a new seam has been found",
    "deposit-drying": "the seams are drying up",
    "deposit-dead": "the seams are dead",
}
SLOT_OF = {member: slot for slot, members in STATE_SLOTS.items()
           for member in members}
STATE_WORDS.update(SLOT_WORDS)

OUTLETS = ("quest", "menu", "encounter", "news", "state")


def card(key: str, name: str, land: str, *,
         wealth: tuple[str, ...] = BANDS,
         states: tuple[str, ...] = (),
         without: tuple[str, ...] = (),
         weather: tuple[str, ...] = (),
         days: tuple[int, int] | int | None = CARD_DAYS,
         **outlets) -> dict:
    """One event pulse. `wealth` / `states` / `without` / `weather` are the
    ADMITTING conditions (all must hold; `weather` is read by the weather
    session, which owns the day roll). `days` is the optional day-stamp
    clock -- None for a pulse that stands until something else moves it.
    The keyword arguments are the OUTLET effects, at most one per outlet:

      news=      "the line the land hears"           (applied here)
      state=     {"set": (), "while": (), "clear": (), "slot": {},
                  "wealth": "band", "wealth_while": "band"}
                                                     (applied here)
      quest=     {...}   posting / cancelling / repricing terms
      menu=      {...}   what the priced menu reads off this card
      encounter= {...}   the local encounter-table entry it adds

    The last three are carried and validated but NOT applied by the frame
    -- the economy floor session owns the board, the menu and the tables.
    """
    unknown = set(outlets) - set(OUTLETS)
    if unknown:
        raise ValueError(f"{key}: not an outlet: {sorted(unknown)}")
    return {"key": key, "name": name, "land": land,
            "admits": {"wealth": tuple(wealth), "states": tuple(states),
                       "without": tuple(without), "weather": tuple(weather)},
            "days": days,
            "outlets": {k: v for k, v in outlets.items() if v}}


def relation(source: str, target: str, kind: str, *,
             when: tuple[str, ...], then: str, because: str) -> dict:
    """One authored directed edge. `when` are states of the SOURCE land
    (any of them is enough); `then` is the state the TARGET land derives
    while they hold; `because` is what the readout says the cause was.
    Static data read at roll time -- never a traded quantity."""
    return {"from": source, "to": target, "kind": kind,
            "when": tuple(when), "then": then, "because": because}


# --------------------------------------------------------------------------- #
# The seed content: two or three economy cards a land (worldsim.md's packets)
# --------------------------------------------------------------------------- #
# The floor the asymmetry doctrine names, minus the parts later sessions
# own: enough to prove the loop end to end and to give the relations table
# something real to read. Cards WAITING under plan.md's rulings (the robot
# servants, the sulfur trade) are not here.

CARDS = (
    # -- Firascir: MANORIAL OPPRESSION & THE CROWN'S DEBTS ------------------ #
    card("firascir/bad-harvest", "The harvest fails", "firascir",
         wealth=("crisis", "normal"), days=(35, 50),
         news="The harvest has failed in Firascir. Bread is short and the "
              "granaries are watched.",
         state={"while": ("harvest-failed",), "wealth_while": "crisis"},
         quest={"post": "grain escort", "level": "band", "pay": 1.25}),
    card("firascir/tolls", "The tolls are doubled", "firascir",
         wealth=("crisis", "normal"), days=(12, 20),
         news="The baron has doubled the road tolls. His toll-men hold the "
              "bridges, and nobody in town will say a word against them.",
         state={"while": ("toll-squeeze",)},
         menu={"toll": 2.0},
         encounter={"kinds": ("bandit",), "where": "road",
                    "as": "toll-men"}),
    card("firascir/war-debts", "The crown calls in its debts", "firascir",
         wealth=("crisis",), without=("harvest-failed",), days=(20, 30),
         news="The crown wants its war paid for. The tax men are out with "
              "the sheriff behind them.",
         state={"while": ("overtaxed",)}),

    # -- Mortellaria: FINANCE & THE ABSOLUTIST STATE ------------------------ #
    card("mortellaria/tax-farmer", "The tax farmer buys the province",
         "mortellaria", wealth=("crisis",), days=(20, 35),
         news="The state has sold the right to squeeze this province. The "
              "tax farmer means to make his money back.",
         state={"while": ("tax-farmed",)}),
    card("mortellaria/bank-run", "The bank fails", "mortellaria",
         wealth=("crisis",), days=(15, 25),
         news="The bank has shut its doors. Paper money is worth its weight "
              "and no more, and every strongbox in the city is watched.",
         state={"while": ("paper-worthless",)},
         menu={"paper_rate": 0.25}),
    card("mortellaria/colony-fleet", "The colony fleet comes in",
         "mortellaria", wealth=("normal", "prosperous"), days=(10, 18),
         news="The colony fleet is in. The wharves are gold, the taverns "
              "are full, and every purse in the city is fat.",
         state={"while": ("coin-flush",)}),

    # -- Ensimaa: MANPOWER & DECADENCE -------------------------------------- #
    card("ensimaa/master-dies", "An old master dies", "ensimaa",
         wealth=("crisis", "normal"), days=(25, 40),
         news="An old master of the elves is dead, and the work he alone "
              "could make is dead with him. His apprentice is asking after "
              "the last commission.",
         state={"while": ("craft-lost",)}),
    card("ensimaa/rented-land", "The rented land turns", "ensimaa",
         wealth=("crisis",), days=None,
         news="The goblin loggers and the dwarven crystal crews are out of "
              "line, the elves say. Word is they want them gone whether "
              "they are or not.",
         state={"slot": {"foreigners": "foreigners-unwelcome"}}),
    card("ensimaa/child-thieves", "The dark clan takes children",
         "ensimaa", wealth=("crisis", "normal"), days=(20, 30),
         news="Children are being taken from the forest villages. Everyone "
              "knows which clan does it. Nobody has gone to look.",
         state={"while": ("children-taken",)}),

    # -- Dvarvengrond: EXTRACTION & CLAN CLAIMS ----------------------------- #
    card("dvarvengrond/new-seam", "A new seam is found", "dvarvengrond",
         wealth=("normal", "prosperous"), days=(15, 25),
         news="A new seam has been found under the mountain. Two clans "
              "claim it and a third is strong enough to work it.",
         state={"slot": {"deposit": "deposit-found"},
                "while": ("claims-collide",), "wealth_while": "prosperous"}),
    card("dvarvengrond/vein-dries", "The vein runs out", "dvarvengrond",
         wealth=("normal", "prosperous"), days=None,
         news="The vein that fed the city is running out. The clan books "
              "say otherwise, and the clan books are the law.",
         state={"slot": {"deposit": "deposit-drying"}, "wealth": "crisis"}),
    card("dvarvengrond/veins-reopened", "The dead veins are reopened",
         "dvarvengrond", wealth=("crisis",), states=("deposit-drying",),
         days=None,
         news="A dwarf has found a way to work a seam everyone had written "
              "off. Every clan with a dead pit wants him, and one of them "
              "wants him quiet.",
         state={"slot": {"deposit": "deposit-normal"}, "wealth": "normal"}),
    card("dvarvengrond/strike", "The pits stand idle", "dvarvengrond",
         wealth=("crisis",), days=(12, 20),
         news="The pits stand idle. The workers want their share of the "
              "new find before the clan books it, and the company shop has "
              "stopped giving credit.",
         state={"while": ("strike",)},
         quest={"post": "strikebreaking", "level": "band"}),

    # -- Gibili: LABOR vs CAPITAL, NO STATE --------------------------------- #
    card("gibili/uprising", "The mills stop", "gibili",
         wealth=("crisis",), days=(12, 20),
         news="The mills have stopped. The workers hold the gates and the "
              "company police are hiring anyone who can hold a stick.",
         state={"while": ("mills-stopped",)},
         quest={"post": "both sides hire", "level": "band"}),
    card("gibili/arms-contract", "The firearms contract", "gibili",
         wealth=("normal", "prosperous"), days=(15, 25),
         news="A firearms contract for Mortellaria is going out by the "
              "cartload. Worth guarding. Worth robbing.",
         state={"while": ("convoy-running",)},
         encounter={"kinds": ("bandit",), "where": "road",
                    "as": "convoy raiders"}),

    # -- Tergal: PASTURE & OBLIGATION --------------------------------------- #
    card("tergal/herd-fails", "The herds are dying", "tergal",
         wealth=("crisis",), days=(25, 40),
         news="The grass is gone and the herds are dying with it. A tribe "
              "with no herd has nothing to lose and knows where the fat "
              "lands are.",
         state={"while": ("herd-loss",)}),
    card("tergal/returned-mercenary", "The mercenary comes home", "tergal",
         days=(15, 25),
         news="A mercenary is back from the southern wars a level of "
              "badass richer, with dwarven steel and a following. The old "
              "order does not suit him.",
         state={"while": ("mercenary-home",)}),
    card("tergal/herd-drive", "The great drive", "tergal",
         wealth=("normal", "prosperous"), days=(10, 18),
         news="The great drive is on. Every horse and buffalo in the land "
              "is moving north, and the fords are the dangerous part.",
         state={"while": ("herd-drive",)},
         quest={"post": "drive escort", "level": "band"}),
)

CARDS_BY_KEY = {c["key"]: c for c in CARDS}

RELATIONS = (
    # THE GRANARY (Firascir) and the southern harvest (Mortellaria).
    relation("firascir", "ensimaa", "grain", when=("harvest-failed",),
             then="grain-scarce", because="the Firascir grain"),
    relation("firascir", "dvarvengrond", "grain", when=("harvest-failed",),
             then="grain-scarce", because="the Firascir grain"),
    relation("firascir", "gibili", "grain", when=("harvest-failed",),
             then="grain-scarce", because="the Firascir grain"),
    relation("mortellaria", "dvarvengrond", "grain",
             when=("tax-farmed", "paper-worthless"),
             then="grain-scarce", because="the southern food ships"),
    # Timber and the roads it comes down.
    relation("firascir", "dvarvengrond", "timber", when=("toll-squeeze",),
             then="timber-dear", because="the tolls on the timber road"),
    # The elves' rented ground: the claims and the concession hang on it.
    relation("ensimaa", "dvarvengrond", "crystal",
             when=("foreigners-unwelcome",), then="claims-revoked",
             because="the elven crystal claim"),
    relation("ensimaa", "gibili", "timber", when=("foreigners-unwelcome",),
             then="concession-lost", because="the elven logging concession"),
    # Gibili arms Mortellaria.
    relation("gibili", "mortellaria", "arms", when=("mills-stopped",),
             then="arms-scarce", because="the Gibili gun mills"),
    # A tribe with no herd goes where the grain is.
    relation("tergal", "firascir", "raid", when=("herd-loss",),
             then="raiders-out", because="the dying Tergal herds"),
)


# --------------------------------------------------------------------------- #
# The save layer: what a land carries
# --------------------------------------------------------------------------- #

def land_layer(world: dict, polity: str) -> dict:
    """The land's world-layer record in the save (`world` on the land)."""
    return world["lands"][polity]["world"]


def _land_seed(world: dict, polity: str, purpose: str, day: int) -> int:
    return stable_seed(world.get("seed"), land_id(polity), purpose, day)


def roll_wealth(rng: random.Random) -> str:
    """2d6 on the weighted middle: 2-4 CRISIS, 5-9 NORMAL, 10-12 PROSPEROUS."""
    n, faces = WEALTH_DICE
    total = sum(rng.randint(1, faces) for _ in range(n))
    for lo, hi, band in WEALTH_BANDS:
        if lo <= total <= hi:
            return band
    raise ValueError(f"no band holds {total}")


def _deck(world: dict, polity: str) -> list[str]:
    """The land's cards, shuffled once (the pact deck's pattern)."""
    keys = [c["key"] for c in CARDS if c["land"] == polity]
    random.Random(_land_seed(world, polity, "worldsim-deck", 0)).shuffle(keys)
    return keys


def open_world(world: dict) -> dict:
    """Roll the world layer onto a fresh world: every land's wealth band,
    its shuffled deck, its state and news lists. A land that opens in CRISIS
    draws its first card straight away -- a land in trouble is in trouble
    from scene one, not from the first lucky roll.

    Called by `quests.generate_world` on a DERIVED rng, so the worldgen
    stream every career bench rides is untouched."""
    for polity in world["lands"]:
        rng = random.Random(_land_seed(world, polity, "worldsim-open", 0))
        world["lands"][polity]["world"] = {
            "wealth": roll_wealth(rng),
            "wealth_day": 0,
            "deck": _deck(world, polity),
            "drawn": [],            # every card this land has fired
            "live": None,           # the card standing now, with its clock
            "news": [],             # day-stamped lines, oldest first
            "told_day": -1,         # the last day whose news was told
            "rolled_day": 0,        # the last day this land was rolled
        }
    for polity in world["lands"]:
        layer = land_layer(world, polity)
        if layer["wealth"] in OPENING_DRAW:
            rng = random.Random(_land_seed(world, polity, "worldsim-open", 1))
            drawn = _draw(world, polity, rng)
            if drawn is not None:
                _fire(world, polity, drawn, OPENING_DAY, rng)
    return world


# --------------------------------------------------------------------------- #
# States: what a land holds, and what it derives
# --------------------------------------------------------------------------- #

def set_state(world: dict, polity: str, state_id: str,
              day: int | None = None) -> None:
    """Flip a state ON, day-stamped. A SLOT member clears whatever else the
    slot held first: exclusive slots are never contradicted."""
    land = world["lands"][polity]
    slot = SLOT_OF.get(state_id)
    if slot:
        for member in STATE_SLOTS[slot]:
            if member != state_id:
                clear_state(world, land, member, day=day)
    add_state(world, land, state_id, day=day, slot=slot)


def drop_state(world: dict, polity: str, state_id: str,
               day: int | None = None) -> bool:
    return clear_state(world, world["lands"][polity], state_id, day=day)


def held_states(world: dict, polity: str) -> list[dict]:
    """The states the land itself holds, day-stamped, oldest first."""
    return [s for s in world["lands"][polity].get("states", ())
            if s.get("active")]


def derived_states(world: dict, polity: str) -> list[dict]:
    """The states the RELATIONS put on this land, computed at read time and
    never stored: a failed harvest in Firascir is grain-scarce in every land
    down its grain edges, for exactly as long as it lasts.

    ONE HOP ONLY -- an edge reads what its source land HOLDS, never what it
    derives. Trouble reaches a land's trading partners, not their partners'
    partners, and the table can never chase its own tail."""
    out: list[dict] = []
    seen = set()
    for edge in RELATIONS:
        if edge["to"] != polity:
            continue
        source = {s["id"] for s in held_states(world, edge["from"])}
        hit = [w for w in edge["when"] if w in source]
        if not hit or edge["then"] in seen:
            continue
        seen.add(edge["then"])
        out.append({"id": edge["then"], "from": edge["from"],
                    "kind": edge["kind"], "because": edge["because"],
                    "derived": True})
    return out


def state_ids(world: dict, polity: str) -> list[str]:
    """Everything the land counts as holding: its own states and the ones
    its edges derive. This is what a card's admitting conditions read."""
    return ([s["id"] for s in held_states(world, polity)]
            + [s["id"] for s in derived_states(world, polity)])


def wealth_of(world: dict, polity: str) -> str:
    return land_layer(world, polity)["wealth"]


def set_wealth(world: dict, polity: str, band: str, day: int) -> None:
    """Move the land's wealth band -- the one slot every land holds."""
    if band not in BANDS:
        raise ValueError(f"no such wealth band: {band}")
    layer = land_layer(world, polity)
    if layer["wealth"] == band:
        return
    layer["wealth"] = band
    layer["wealth_day"] = day


# --------------------------------------------------------------------------- #
# The deck: the draw on need
# --------------------------------------------------------------------------- #

def admits(world: dict, polity: str, spec: dict,
           weather: str | None = None) -> bool:
    """Does the land meet this card's admitting conditions today?"""
    band = wealth_of(world, polity)
    if spec["wealth"] and band not in spec["wealth"]:
        return False
    held = set(state_ids(world, polity))
    if any(s not in held for s in spec["states"]):
        return False
    if any(s in held for s in spec["without"]):
        return False
    if spec["weather"] and weather not in spec["weather"]:
        return False
    return True


def _says_nothing_new(world: dict, polity: str, drawn: dict) -> bool:
    """A card whose whole state effect is a slot the land already holds has
    nothing to say -- it stays in the deck rather than firing an empty
    pulse (the exclusive-slot discipline, from the other side)."""
    state = drawn["outlets"].get("state") or {}
    slots = state.get("slot") or {}
    if not slots or state.get("set") or state.get("while"):
        return False
    if _band_step(world, polity, state):
        return False
    held = set(state_ids(world, polity))
    return all(value in held for value in slots.values())


def _draw(world: dict, polity: str, rng: random.Random,
          weather: str | None = None) -> dict | None:
    """Deal the land's next card off its deck: the first one it admits,
    skipped cards staying in the deck for a later day (the pact deck's
    pattern). An exhausted deck reshuffles. None when the deck holds
    nothing this land admits today."""
    layer = land_layer(world, polity)
    deck = layer["deck"]
    if not deck:
        deck.extend(_deck(world, polity))
        rng.shuffle(deck)
    for i, key in enumerate(deck):
        drawn = CARDS_BY_KEY[key]
        if not admits(world, polity, drawn["admits"], weather):
            continue
        if _says_nothing_new(world, polity, drawn):
            continue
        return CARDS_BY_KEY[deck.pop(i)]
    return None


# --------------------------------------------------------------------------- #
# The pulse: firing a card, and its clock running out
# --------------------------------------------------------------------------- #

def _news(world: dict, polity: str, day: int, line: str) -> None:
    layer = land_layer(world, polity)
    layer["news"].append({"day": day, "line": line})
    del layer["news"][:-NEWS_KEPT]


def _clock(drawn: dict, day: int, rng: random.Random) -> int | None:
    days = drawn["days"]
    if days is None:
        return None
    if isinstance(days, int):
        return day + days
    return day + rng.randint(*days)


def _fire(world: dict, polity: str, drawn: dict, day: int,
          rng: random.Random) -> None:
    """Apply one card: its state flips and its news line (the two outlets
    the frame ships), and stamp its clock. `while` states are the card's
    own and come off when it ends; `set` states and slot assignments
    outlive it. A card with NO clock leaves its mark and stands over
    nothing -- the vein has run out, and the land goes on having days."""
    state = drawn["outlets"].get("state") or {}
    for state_id in state.get("clear", ()):
        drop_state(world, polity, state_id, day)
    for value in (state.get("slot") or {}).values():
        set_state(world, polity, value, day)
    for state_id in (tuple(state.get("set", ()))
                     + tuple(state.get("while", ()))):
        set_state(world, polity, state_id, day)
    line = drawn["outlets"].get("news")
    if line:
        _news(world, polity, day, line)
    until = _clock(drawn, day, rng)
    layer = land_layer(world, polity)
    was = layer["wealth"]
    if state.get("wealth"):
        set_wealth(world, polity, state["wealth"], day)
    if state.get("wealth_while"):
        set_wealth(world, polity, state["wealth_while"], day)
    layer["live"] = (None if until is None
                     else {"key": drawn["key"], "day": day, "until": until,
                           "wealth_was": (was if state.get("wealth_while")
                                          else None)})
    layer["drawn"].append({"key": drawn["key"], "day": day})


def _end(world: dict, polity: str, day: int) -> None:
    """The live card's clock has run out: its own states come off and a band
    it moved for its duration comes back. Its slot assignments and `set`
    flips stand -- something else has to move those."""
    layer = land_layer(world, polity)
    live = layer["live"]
    if live is None:
        return
    drawn = CARDS_BY_KEY[live["key"]]
    state = drawn["outlets"].get("state") or {}
    for state_id in state.get("while", ()):
        drop_state(world, polity, state_id, day)
    was, moved = live.get("wealth_was"), state.get("wealth_while")
    if was is not None and layer["wealth"] == moved:
        set_wealth(world, polity, was, day)      # ...unless something else
    layer["live"] = None                         # moved the band since


def _band_step(world: dict, polity: str, state: dict) -> bool:
    """Would this card's wealth effect actually move the land's band?"""
    band = wealth_of(world, polity)
    return any(state.get(key) not in (None, band)
               for key in ("wealth", "wealth_while"))


# --------------------------------------------------------------------------- #
# The roll points
# --------------------------------------------------------------------------- #

def roll_land(world: dict, polity: str, day: int,
              weather: str | None = None) -> None:
    """Bring one land up to `day`, one day at a time. Each day's roll runs
    off its own stable seed, so catching up thirty days at an arrival gives
    exactly the history that rolling them live would have -- which is what
    makes the world move while nobody is watching."""
    layer = land_layer(world, polity)
    while layer["rolled_day"] < day:
        today = layer["rolled_day"] + 1
        rng = random.Random(_land_seed(world, polity, "worldsim-day", today))
        live = layer["live"]
        if live is not None and today >= live["until"]:
            _end(world, polity, today)
        if layer["live"] is None:
            if rng.random() < CARD_CHANCE.get(layer["wealth"], 0.0):
                drawn = _draw(world, polity, rng, weather)
                if drawn is not None:
                    _fire(world, polity, drawn, today, rng)
        layer["rolled_day"] = today


def roll_world(world: dict, day: int) -> None:
    """Bring EVERY land up to `day`. Called at the roll points the game
    already has -- settlement arrivals, nights, travel legs, wherever the
    board's refill and the crown's raids fire. The whole world moves
    together so a relation never reads a land that is behind the calendar."""
    for polity in world["lands"]:
        roll_land(world, polity, day)


def take_news(world: dict, polity: str, day: int) -> list[str]:
    """What this land has heard since the party last listened -- the state
    diff's spoken half. Told once: the day stamp moves with the telling."""
    layer = land_layer(world, polity)
    fresh = [n for n in layer["news"] if n["day"] > layer["told_day"]]
    layer["told_day"] = day
    if not fresh:
        return []
    lines = [f"  (day {n['day']}) {n['line']}" for n in fresh[-NEWS_TOLD:]]
    return [f"WORD FROM {world['lands'][polity]['name'].upper()}:"] + lines


# --------------------------------------------------------------------------- #
# Readouts (the state diff)
# --------------------------------------------------------------------------- #

def state_line(entry: dict) -> str:
    word = STATE_WORDS.get(entry["id"], entry["id"])
    if entry.get("derived"):
        return f"{word} ({entry['because']})"
    since = entry.get("since")
    return word + (f" (day {since})" if since is not None else "")


def land_lines(world: dict, polity: str) -> list[str]:
    """The land's world state for the map page: the band, then whatever it
    is living through. One line -- this is a phone page."""
    layer = land_layer(world, polity)
    lines = [f"  [{layer['wealth'].upper()}]"]
    shown = held_states(world, polity) + derived_states(world, polity)
    if shown:
        lines[0] += " " + "; ".join(state_line(s) for s in shown)
    return lines


def world_lines(world: dict) -> list[str]:
    """The DM's inventory of the world layer (`world`): every land's band,
    what it holds, what it derives, the card standing over it and how deep
    its deck still is."""
    lines = ["-- the world --"]
    for polity, land in world["lands"].items():
        layer = land["world"]
        lines.append("")
        lines.append(f"{land['name']} -- {layer['wealth'].upper()} "
                     f"(rolled to day {layer['rolled_day']})")
        for entry in held_states(world, polity):
            lines.append(f"  state: {state_line(entry)}")
        for entry in derived_states(world, polity):
            lines.append(f"  derived: {state_line(entry)}")
        live = layer["live"]
        if live is not None:
            drawn = CARDS_BY_KEY[live["key"]]
            until = (f", stands to day {live['until']}"
                     if live["until"] else ", no clock")
            lines.append(f"  card: {drawn['name']} "
                         f"(day {live['day']}{until})")
        lines.append(f"  deck: {len(layer['deck'])} left, "
                     f"{len(layer['drawn'])} drawn")
    return lines


# --------------------------------------------------------------------------- #
# Validation (the authored content has to be legal at import time)
# --------------------------------------------------------------------------- #

def validate_content() -> None:
    keys = set()
    for drawn in CARDS:
        key = drawn["key"]
        if key in keys:
            raise ValueError(f"duplicate card key: {key}")
        keys.add(key)
        if drawn["land"] not in LAND_SPECS:
            raise ValueError(f"{key}: no such land: {drawn['land']}")
        for band in drawn["admits"]["wealth"]:
            if band not in BANDS:
                raise ValueError(f"{key}: no such wealth band: {band}")
        for state_id in (drawn["admits"]["states"]
                         + drawn["admits"]["without"]):
            if state_id not in STATE_WORDS:
                raise ValueError(f"{key}: no such state: {state_id}")
        state = drawn["outlets"].get("state") or {}
        for group in ("set", "while", "clear"):
            for state_id in state.get(group, ()):
                if state_id not in STATE_WORDS:
                    raise ValueError(f"{key}: no such state: {state_id}")
                if state_id in SLOT_OF:
                    raise ValueError(f"{key}: {state_id} is a slot member -- "
                                     f"set it through 'slot'")
        for slot, value in (state.get("slot") or {}).items():
            if slot not in STATE_SLOTS:
                raise ValueError(f"{key}: no such slot: {slot}")
            if value not in STATE_SLOTS[slot]:
                raise ValueError(f"{key}: {value} is not in slot {slot}")
        for band_key in ("wealth", "wealth_while"):
            if state.get(band_key) and state[band_key] not in BANDS:
                raise ValueError(f"{key}: no such wealth band: "
                                 f"{state[band_key]}")
        if not drawn["outlets"]:
            raise ValueError(f"{key}: a card with no outlet effect")
        if len(drawn["outlets"]) > len(OUTLETS):
            raise ValueError(f"{key}: more than {len(OUTLETS)} outlets")
    for edge in RELATIONS:
        for side in ("from", "to"):
            if edge[side] not in LAND_SPECS:
                raise ValueError(f"relation {edge}: no such land")
        if edge["from"] == edge["to"]:
            raise ValueError(f"relation {edge}: a land does not trade "
                             f"with itself")
        for state_id in edge["when"] + (edge["then"],):
            if state_id not in STATE_WORDS:
                raise ValueError(f"relation {edge}: no such state: "
                                 f"{state_id}")


validate_content()


# --------------------------------------------------------------------------- #
# Demo (the designer's eyeball check)
# --------------------------------------------------------------------------- #

def main() -> None:
    from quests import generate_world
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--days", type=int, default=30,
                    help="roll the world this many days before dumping")
    args = ap.parse_args()
    world = generate_world(seed=args.seed)
    roll_world(world, args.days)
    for line in world_lines(world):
        print(line)
    print("")
    print("-- what the lands heard --")
    for polity in world["lands"]:
        for line in take_news(world, polity, args.days):
            print(line)


if __name__ == "__main__":
    main()
