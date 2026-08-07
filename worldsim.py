"""The world layer -- the WORLD & NPC SIMULATION build's frame and weather.

plan.md's ladder. The FRAME session (2026-08-07): `worldsim.md`'s five record
kinds stop being prose and become data, and the save grows a world layer under
every land. The WEATHER session (2026-08-08): the first content rung on top of
it -- every land rolls a sky every day off its climate, and three tracks of
cards now run over one land instead of one.

THE THREE TRACKS (2026-08-08). A land carries one live card per track, each
with its own deck, its own draw rule and its own timescale, because one slot
could not hold them: a season of drought would have blocked every storm under
it, and a storm would have blocked the harvest failing.

  crisis  -- the frame's. Drawn on need off the wealth band (CARD_CHANCE),
             the content of a land in trouble. Days-to-weeks.
  weather -- the DAY-scale pulse. Drawn when today's sky admits one, gated by
             the card's own `chance`: the climate distribution IS the deck's
             die. Hours-to-days.
  season  -- the SLOW state (drought). Drawn off a long dry or wet SPELL,
             stands for a season, and is what the day roll and the other two
             tracks then read.

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
- **The card.** Admitting conditions over land, wealth, states, weather and
  the wet/dry spell; up to FIVE outlet effects (quest / priced menu /
  encounter / news / state flip); an optional day-stamp clock. THE FRAME
  APPLIES TWO of the five -- the news line and the state flip, which are the
  surfaces it ships (the news at the roll points, the state diff on `map`
  and `world`). The quest, menu and encounter payloads are carried,
  validated and left for the economy floor session, which owns the hookups.
- **The sky.** Every land rolls one weather word a day against its
  environment profile's distribution (`places.ENVIRONMENT_PROFILES`, whose
  climate sentence is what those weights say in numbers), tracking the WET
  and DRY spells running behind it. A held DROUGHT bends the roll that
  produced it. The sky is what the weather track's cards admit on, what the
  exposure check and the storm penalties read, and what the party sees on
  the road.

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

from places import (ENVIRONMENT_PROFILES, LAND_SPECS, add_state, clear_state,
                    land_id, stable_seed)

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

# --- the weather knobs (2026-08-08) ---------------------------------------- #
# The DAY ROLL needs no chance of its own: the climate distribution is the
# die, and a weather card fires when the sky it wants comes up (times its own
# `chance`, which is what keeps the supernatural rare). What needs knobs is
# the SPELL -- how long a run of wet or dry days has to be before the slow
# cards notice it.
WET_WEATHER = ("rain", "storm", "snow")     # a day that breaks a dry spell
DRY_WEATHER = ("clear", "heat", "wind")     # ...and one that breaks a wet one
# The two counters measure two different things, deliberately. DRY is DAYS
# SINCE THE LAST RAIN, so an overcast day extends it -- a grey sky is not a
# drought ending. WET is a run of wet days that a dry day breaks and an
# overcast day does not -- three days of rain with a grey one in the middle
# is still what puts the fords out.
PROFILE_SPELL = "profile"       # a card's `dry` may name this instead of a
                                # number: the threshold is then the LAND's
                                # own (places.ENVIRONMENT_PROFILES'
                                # drought_days), because a drought is a
                                # relative thing -- a fortnight without rain
                                # is a disaster in the forest and a Tuesday
                                # in the dry south
DROUGHT_WET_MULT = 0.15         # what a held drought does to the rain and
                                # storm weights -- the state bending the roll
                                # that made it, which is why a drought lasts
DROUGHT_DRY_BONUS = 1.35        # ...and what it does to clear and heat

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
    # Weather (2026-08-08, land-agnostic -- the sky's own states)
    "storm-bound": "the storm has the roads",
    "fords-out": "the fords are out",
    "drought": "the rains have not come",
    "bones-walk": "bones walk in the fog",
    "wildfire": "the forest is burning",
    "burned-over": "the burn is still black",
    "dust-storm": "the dust has the plain",
    "smog": "the smoke will not lift",
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

# The three card tracks, each with its own deck, live slot and draw rule
# (2026-08-08, the weather session). ANY_LAND is the land-agnostic marker:
# a weather card belongs to every land's deck, a crisis card to one.
TRACKS = ("crisis", "weather", "season")
ANY_LAND = "*"
DECK_KEY = {"crisis": "deck", "weather": "weather_deck",
            "season": "season_deck"}
LIVE_KEY = {"crisis": "live", "weather": "weather_live",
            "season": "season_live"}


def card(key: str, name: str, land: str | tuple[str, ...], *,
         track: str = "crisis",
         wealth: tuple[str, ...] = BANDS,
         states: tuple[str, ...] = (),
         without: tuple[str, ...] = (),
         weather: tuple[str, ...] = (),
         wet: int = 0,
         dry: int = 0,
         chance: float = 1.0,
         days: tuple[int, int] | int | None = CARD_DAYS,
         sky: str = "",
         hook=None,
         **outlets) -> dict:
    """One event pulse. `land` is one land, a tuple of them, or ANY_LAND for
    a card every land's deck carries. `track` picks which of the land's three
    decks it sits in ("crisis" / "weather" / "season") -- and so which draw
    rule and which live slot it answers to.

    `wealth` / `states` / `without` / `weather` / `wet` / `dry` are the
    ADMITTING conditions (all must hold): the band, states held or derived,
    states forbidden, today's sky, and the length of the wet or dry SPELL
    behind it. `chance` is the card's own die once it is admitted -- 1.0 for
    an ordinary card, low for the rare and the supernatural. `days` is the
    optional day-stamp clock -- None for a pulse that stands until something
    else moves it. `sky` is for a card that IS the weather rather than a
    consequence of it: while such a card stands, the land's day roll is
    skipped and its sky is this word, so a storm that "sets in for two
    days" is a storm on both of them. `hook(world, land, day, rng)` runs at
    the firing and returns format fields for the news line (the fog's
    necromancer is the one customer: a card that has to NAME somebody).

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
    lands = (land,) if isinstance(land, str) else tuple(land)
    return {"key": key, "name": name, "land": lands, "track": track,
            "chance": chance, "hook": hook, "sky": sky,
            "admits": {"wealth": tuple(wealth), "states": tuple(states),
                       "without": tuple(without), "weather": tuple(weather),
                       "wet": wet, "dry": dry},
            "days": days,
            "outlets": {k: v for k, v in outlets.items() if v}}


def in_land(spec: dict, polity: str) -> bool:
    """Does this card belong to that land's deck? (ANY_LAND belongs to all.)"""
    return ANY_LAND in spec["land"] or polity in spec["land"]


def relation(source: str, target: str, kind: str, *,
             when: tuple[str, ...], then: str, because: str) -> dict:
    """One authored directed edge. `when` are states of the SOURCE land
    (any of them is enough); `then` is the state the TARGET land derives
    while they hold; `because` is what the readout says the cause was.
    Static data read at roll time -- never a traded quantity."""
    return {"from": source, "to": target, "kind": kind,
            "when": tuple(when), "then": then, "because": because}


# --------------------------------------------------------------------------- #
# The sky: the day roll (2026-08-08, the weather session)
# --------------------------------------------------------------------------- #
# Weather is a day-scale state with outlet effects: the cheapest world content
# there is, land-agnostic, and the only one that touches the party every day
# it is out of doors. The vocabulary is nine words shared by every land; what
# differs is the WEIGHTS, which each environment profile authors as the
# numbers behind its climate sentence (places.ENVIRONMENT_PROFILES).

WEATHER_WORDS = {               # word -> what the party sees
    "clear": "clear skies",
    "cloud": "grey and close",
    "wind": "a hard wind",
    "rain": "steady rain",
    "storm": "a storm",
    "fog": "fog on the ground",
    "frost": "hard frost",
    "snow": "snow",
    "heat": "hard heat",
}
# The same word reads differently on different ground: a storm in the
# dwarves' highlands is a SNOWSTORM, and it is the same card underneath
# (worldsim.md's own note). Display only -- never a second vocabulary.
WEATHER_LOCAL = {
    "alpine_tundra": {"storm": "a snowstorm", "rain": "sleet",
                      "cloud": "low cloud"},
    "mediterranean": {"cloud": "haze", "wind": "the sea wind"},
    "prairie": {"wind": "a wind with no cover from it"},
}
# What the sky COSTS a party out in it: exposure (the STR check that gives
# colds -- rpg.py's disease family) and the storm's field penalties.
EXPOSURE_WEATHER = ("rain", "storm", "frost", "snow")
STORM_WEATHER = ("storm",)      # ...and the sky that drags a shot and trips
                                # a step (rpg.STORM_SHOT_PENALTY / _SLIP_DC)


def weather_phrase(environment: str, word: str) -> str:
    """What this ground calls that sky."""
    return WEATHER_LOCAL.get(environment, {}).get(
        word, WEATHER_WORDS.get(word, word))


def weather_weights(world: dict, polity: str) -> dict[str, float]:
    """The land's climate distribution, bent by whatever season-scale state
    it is holding. A drought is the state that made itself: it cuts the rain
    and storm weights to DROUGHT_WET_MULT and lifts the dry ones, which is
    why droughts last past the day that started them."""
    environment = world["lands"][polity]["environment"]
    base = ENVIRONMENT_PROFILES[environment]["weather"]
    weights = {word: float(w) for word, w in base.items() if w}
    if "drought" in state_ids(world, polity):
        for word in weights:
            if word in ("rain", "storm", "snow"):
                weights[word] *= DROUGHT_WET_MULT
            elif word in ("clear", "heat"):
                weights[word] *= DROUGHT_DRY_BONUS
    return weights


def roll_weather(world: dict, polity: str, rng: random.Random) -> str:
    """One day's sky for one land. The weights are the die -- there is no
    separate chance anywhere in the weather track."""
    weights = weather_weights(world, polity)
    words = sorted(weights)
    return rng.choices(words, weights=[weights[w] for w in words])[0]


def weather_of(world: dict, polity: str) -> str:
    """Today's sky over that land -- "" before the land has been rolled."""
    return land_layer(world, polity).get("weather", "")


def weather_line(world: dict, polity: str) -> str:
    """The one line the party reads on the road: the sky, and the spell
    behind it when the spell has become the story."""
    layer = land_layer(world, polity)
    word = layer.get("weather")
    if not word:
        return ""
    environment = world["lands"][polity]["environment"]
    line = f"WEATHER: {weather_phrase(environment, word)}"
    wet, dry = layer.get("wet", 0), layer.get("dry", 0)
    if word in WET_WEATHER and wet >= 3:
        line += f" -- the {_ordinal(wet)} wet day running"
    elif word in DRY_WEATHER and dry >= 7:
        line += f" -- {dry} days without rain"
    return line + "."


_ORDINAL_TAIL = {1: "st", 2: "nd", 3: "rd"}


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{_ORDINAL_TAIL.get(n % 10, 'th')}"


def exposed(world: dict, polity: str) -> bool:
    """Is the sky over that land one a night out of doors is paid for?"""
    return weather_of(world, polity) in EXPOSURE_WEATHER


def storming(world: dict, polity: str) -> bool:
    """Is it blowing hard enough to drag a shot and trip a step?"""
    return weather_of(world, polity) in STORM_WEATHER


# --- the fog's cause: one named face, and no machinery under it ------------ #
# THE FOG RAISES BONES is the weather deck's supernatural card, and the only
# one that needs somebody to BE somewhere. The rumor address is deliberately
# cheap (plan.md's ruling): a name and a level on the land record, which the
# news line says out loud and the DM runs from. No landmark record, no site,
# no questline -- the party goes looking or it does not, and the same man is
# still there next fog, which is what makes him a face instead of a pulse.

NECROMANCER_LEVELS = (3, 14)    # rolled once and kept: he is as far above or
                                # below the party as he happens to be, which
                                # is the landmark-problem stance in miniature
NECROMANCER_EPITHETS = (
    "the Pale", "the Grave-Warden", "the Unburied", "Bone-Wright",
    "the Sexton", "the Quiet", "Ash-Hand", "the Second Grave",
    "Corpse-Candle", "the Long Vigil",
)


def named_necromancer(world: dict, polity: str) -> dict | None:
    """The face behind the land's walking dead, if it has one yet."""
    return land_layer(world, polity).get("necromancer")


def _name_the_necromancer(world: dict, polity: str, day: int,
                          rng: random.Random) -> dict:
    """THE FOG RAISES BONES firing: name the cause, once, and keep him. A
    second fog raises the SAME man's dead -- recurrence is the whole point
    of naming him (worldsim.md's six outlets: no single one produces it)."""
    from people import pick_name          # lazy: quests imports worldsim
    layer = land_layer(world, polity)
    who = layer.get("necromancer")
    if who is None:
        race = LAND_SPECS[polity]["race"]
        first = pick_name(rng, race, rng.choice(("m", "f")))
        who = {"name": f"{first} {rng.choice(NECROMANCER_EPITHETS)}",
               "level": rng.randint(*NECROMANCER_LEVELS),
               "since": day}
        layer["necromancer"] = who
    return {"necromancer": who["name"]}


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

    # -- THE WEATHER TRACK: the day-scale sky (2026-08-08) ------------------- #
    # Land-agnostic first, then the three that belong to one land's ground.
    # No wealth condition anywhere on this track: a prosperous land gets the
    # same storms as a starving one -- that is what makes weather the outlet
    # that reaches a quiet world.
    card("weather/storm", "The storm sets in", ANY_LAND, track="weather",
         weather=("storm",), days=(1, 3), sky="storm",
         state={"while": ("storm-bound",)}),
    card("weather/fords-out", "The ford is out",
         ("firascir", "mortellaria"), track="weather",
         wet=3, days=(6, 12),
         news="Three days of rain and the fords are gone. The bridges and "
              "the ferries are the only way over now, and the men who hold "
              "them know it.",
         state={"while": ("fords-out",)},
         menu={"ferry": 3.0}),
    card("weather/fog-bones", "The fog raises bones", ANY_LAND,
         track="weather", weather=("fog",), chance=0.05, days=(8, 16),
         hook=_name_the_necromancer,
         news="Bones walk in the fog. The village dogs will not go out, and "
              "the country people have a name for the man who calls them "
              "up: {necromancer}.",
         state={"while": ("bones-walk",)},
         encounter={"kinds": ("skeleton",), "where": "wilds",
                    "as": "the fog's dead"}),
    card("weather/wildfire", "The forest burns", "ensimaa", track="weather",
         states=("drought",), weather=("clear", "heat", "wind"),
         chance=0.30, days=(4, 8),
         news="The forest is burning above the river villages. They are "
              "carrying out what they can, and already arguing about whose "
              "carelessness it was.",
         state={"while": ("wildfire",), "set": ("burned-over",)},
         quest={"post": "evacuation", "level": "band", "pay": 1.2}),
    card("weather/dust-storm", "The dust storm", "tergal", track="weather",
         states=("drought",), weather=("wind", "heat", "clear"),
         chance=0.35, days=(1, 3), sky="wind",
         news="The dust has the plain. Nothing moves on the roads, and when "
              "it lifts there will be herds scattered from here to the "
              "river.",
         state={"while": ("dust-storm",)},
         quest={"post": "herd recovery", "level": "band"}),
    card("weather/smog", "The smog settles", "gibili", track="weather",
         weather=("cloud", "fog"), chance=0.20, days=(2, 5),
         news="The mill smoke has nowhere to go and has settled over the "
              "town. Everyone is coughing. The owners say it is the "
              "weather.",
         state={"while": ("smog",)}),

    # -- THE SEASON TRACK: the slow states the day roll reads ---------------- #
    card("weather/drought", "The rains do not come", ANY_LAND,
         track="season", dry=PROFILE_SPELL, chance=0.25, days=(45, 80),
         news="The rains have not come. The rivers are low, the grass is "
              "going brown, and the wells are being counted.",
         state={"while": ("drought",)}),
    card("weather/green-again", "The burn goes green", "ensimaa",
         track="season", states=("burned-over",),
         without=("drought", "wildfire"), chance=0.03, days=None,
         news="Green is coming up through the black. The elves will not "
              "call it healed for a century, but the deer are back.",
         state={"clear": ("burned-over",)}),
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


def _deck(world: dict, polity: str, track: str = "crisis") -> list[str]:
    """One of the land's three decks, shuffled once (the pact deck's
    pattern). A weather or season card marked ANY_LAND sits in every land's
    deck; a land-named one sits in its own."""
    keys = [c["key"] for c in CARDS
            if c["track"] == track and in_land(c, polity)]
    random.Random(_land_seed(world, polity, f"worldsim-deck-{track}",
                             0)).shuffle(keys)
    return keys


def open_world(world: dict) -> dict:
    """Roll the world layer onto a fresh world: every land's wealth band, its
    three shuffled decks, its opening sky, its state and news lists. A land
    that opens in CRISIS draws its first crisis card straight away -- a land
    in trouble is in trouble from scene one, not from the first lucky roll.
    The weather and season tracks open EMPTY: a sky is a thing that happens
    on a day, and day 0 is worldgen's bookkeeping.

    Called by `quests.generate_world` on a DERIVED rng, so the worldgen
    stream every career bench rides is untouched."""
    for polity in world["lands"]:
        rng = random.Random(_land_seed(world, polity, "worldsim-open", 0))
        world["lands"][polity]["world"] = {
            "wealth": roll_wealth(rng),
            "wealth_day": 0,
            "deck": _deck(world, polity),
            "weather_deck": _deck(world, polity, "weather"),
            "season_deck": _deck(world, polity, "season"),
            "drawn": [],            # every card this land has fired
            "live": None,           # the card standing now, with its clock
            "weather_live": None,   # ...and the same for the other two
            "season_live": None,    # tracks (a storm must not block a
                                    # harvest failing, nor a drought a storm)
            "weather": "",          # today's sky, once a day has been rolled
            "weather_day": 0,
            "wet": 0,               # the wet and dry SPELLS running behind
            "dry": 0,               # it -- what the slow cards read
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
    """Does the land meet this card's admitting conditions today? `weather`
    defaults to whatever sky the land's layer is currently holding, so a
    caller that has not rolled a day still reads the right one."""
    band = wealth_of(world, polity)
    if spec["wealth"] and band not in spec["wealth"]:
        return False
    held = set(state_ids(world, polity))
    if any(s not in held for s in spec["states"]):
        return False
    if any(s in held for s in spec["without"]):
        return False
    if spec["weather"]:
        sky = weather_of(world, polity) if weather is None else weather
        if sky not in spec["weather"]:
            return False
    layer = land_layer(world, polity)
    if spec.get("wet") and layer.get("wet", 0) < spec["wet"]:
        return False
    need = spec.get("dry")
    if need == PROFILE_SPELL:
        need = ENVIRONMENT_PROFILES[
            world["lands"][polity]["environment"]]["drought_days"]
    if need and layer.get("dry", 0) < need:
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
          weather: str | None = None, track: str = "crisis") -> dict | None:
    """Deal the land's next card off one of its decks: the first one it
    admits, skipped cards staying in the deck for a later day (the pact
    deck's pattern). An exhausted deck reshuffles. None when the deck holds
    nothing this land admits today.

    A card's own `chance` is rolled AFTER it is admitted and BEFORE it is
    taken: a rare card that loses its roll stays where it is and gets
    another fog to try on. That is what keeps the supernatural rare without
    a second knob anywhere else in the loop."""
    layer = land_layer(world, polity)
    deck = layer[DECK_KEY[track]]
    if not deck:
        deck.extend(_deck(world, polity, track))
        rng.shuffle(deck)
    for i, key in enumerate(deck):
        drawn = CARDS_BY_KEY[key]
        if not admits(world, polity, drawn["admits"], weather):
            continue
        if _says_nothing_new(world, polity, drawn):
            continue
        if drawn["chance"] < 1.0 and rng.random() >= drawn["chance"]:
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
    the frame ships), and stamp its clock in its own track's live slot.
    `while` states are the card's own and come off when it ends; `set`
    states and slot assignments outlive it. A card with NO clock leaves its
    mark and stands over nothing -- the vein has run out, and the land goes
    on having days.

    A card carrying a `hook` runs it first and formats its news line with
    what came back: the fog's necromancer is the one card that has to name
    somebody, and naming him is a world change like any other."""
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
        if drawn["hook"] is not None:
            line = line.format(**drawn["hook"](world, polity, day, rng))
        _news(world, polity, day, line)
    until = _clock(drawn, day, rng)
    layer = land_layer(world, polity)
    was = layer["wealth"]
    if state.get("wealth"):
        set_wealth(world, polity, state["wealth"], day)
    if state.get("wealth_while"):
        set_wealth(world, polity, state["wealth_while"], day)
    layer[LIVE_KEY[drawn["track"]]] = (
        None if until is None
        else {"key": drawn["key"], "day": day, "until": until,
              "wealth_was": (was if state.get("wealth_while") else None)})
    layer["drawn"].append({"key": drawn["key"], "day": day})


def _end(world: dict, polity: str, day: int, track: str = "crisis") -> None:
    """The track's live card has run out its clock: its own states come off
    and a band it moved for its duration comes back. Its slot assignments and
    `set` flips stand -- something else has to move those."""
    layer = land_layer(world, polity)
    live = layer[LIVE_KEY[track]]
    if live is None:
        return
    drawn = CARDS_BY_KEY[live["key"]]
    state = drawn["outlets"].get("state") or {}
    for state_id in state.get("while", ()):
        drop_state(world, polity, state_id, day)
    was, moved = live.get("wealth_was"), state.get("wealth_while")
    if was is not None and layer["wealth"] == moved:
        set_wealth(world, polity, was, day)      # ...unless something else
    layer[LIVE_KEY[track]] = None                # moved the band since


def _band_step(world: dict, polity: str, state: dict) -> bool:
    """Would this card's wealth effect actually move the land's band?"""
    band = wealth_of(world, polity)
    return any(state.get(key) not in (None, band)
               for key in ("wealth", "wealth_while"))


# --------------------------------------------------------------------------- #
# The roll points
# --------------------------------------------------------------------------- #

def _roll_sky(world: dict, polity: str, day: int,
              rng: random.Random) -> str:
    """Today's weather for one land, and the wet/dry spell it continues or
    breaks. Cloud, fog and frost break NEITHER spell: an overcast day does
    not end a drought and does not save a washed-out ford.

    A weather card that IS the weather (its `sky`) holds the day instead of
    rolling it, for as long as its clock has left -- otherwise a storm
    declared to last three days would be standing over clear skies by the
    second one, which is the kind of incoherence a state readout shows the
    player immediately."""
    layer = land_layer(world, polity)
    live = layer.get("weather_live")
    forced = (CARDS_BY_KEY[live["key"]]["sky"]
              if live is not None and day < live["until"] else "")
    word = forced or roll_weather(world, polity, rng)
    if word in WET_WEATHER:
        layer["wet"], layer["dry"] = layer.get("wet", 0) + 1, 0
    else:
        layer["dry"] = layer.get("dry", 0) + 1   # any day without rain is
        if word in DRY_WEATHER:                  # a day without rain...
            layer["wet"] = 0                     # ...but only real dry
    layer["weather"], layer["weather_day"] = word, day   # weather breaks a
    return word                                          # wet spell


def roll_land(world: dict, polity: str, day: int) -> None:
    """Bring one land up to `day`, one day at a time. Each day's roll runs
    off its own stable seed, so catching up thirty days at an arrival gives
    exactly the history that rolling them live would have -- which is what
    makes the world move while nobody is watching.

    The day, in order: the SKY is rolled first (the season track's states
    bend it, so a drought makes its own weather), then each of the three
    tracks expires its live card and draws a new one under its own rule --
    weather and season off the sky and the spell, crisis off the wealth
    band. Weather before crisis, because a crisis card may admit on the sky
    and a sky never admits on a crisis."""
    layer = land_layer(world, polity)
    while layer["rolled_day"] < day:
        today = layer["rolled_day"] + 1
        rng = random.Random(_land_seed(world, polity, "worldsim-day", today))
        sky = _roll_sky(world, polity, today, rng)
        for track in ("season", "weather", "crisis"):
            live = layer[LIVE_KEY[track]]
            if live is not None and today >= live["until"]:
                _end(world, polity, today, track)
            if layer[LIVE_KEY[track]] is not None:
                continue
            if track == "crisis" and (rng.random()
                                      >= CARD_CHANCE.get(layer["wealth"],
                                                         0.0)):
                continue        # the crisis track's die is the wealth band;
                                # the other two are the sky's own
            drawn = _draw(world, polity, rng, sky, track)
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
    is living through, then the sky over it. Two lines at most -- this is a
    phone page."""
    layer = land_layer(world, polity)
    lines = [f"  [{layer['wealth'].upper()}]"]
    shown = held_states(world, polity) + derived_states(world, polity)
    if shown:
        lines[0] += " " + "; ".join(state_line(s) for s in shown)
    sky = weather_line(world, polity)
    if sky:
        lines.append(f"  {sky}")
    return lines


def world_lines(world: dict) -> list[str]:
    """The DM's inventory of the world layer (`world`): every land's band,
    what it holds, what it derives, the sky and the spell behind it, the
    cards standing over it on all three tracks, and how deep its decks
    still are."""
    lines = ["-- the world --"]
    for polity, land in world["lands"].items():
        layer = land["world"]
        lines.append("")
        lines.append(f"{land['name']} -- {layer['wealth'].upper()} "
                     f"(rolled to day {layer['rolled_day']})")
        sky = layer.get("weather")
        if sky:
            spell = (f"wet {layer.get('wet', 0)}"
                     if layer.get("wet") else f"dry {layer.get('dry', 0)}")
            lines.append(f"  sky: {weather_phrase(land['environment'], sky)} "
                         f"[{sky}, {spell}]")
        for entry in held_states(world, polity):
            lines.append(f"  state: {state_line(entry)}")
        for entry in derived_states(world, polity):
            lines.append(f"  derived: {state_line(entry)}")
        for track in TRACKS:
            live = layer.get(LIVE_KEY[track])
            if live is None:
                continue
            drawn = CARDS_BY_KEY[live["key"]]
            until = (f", stands to day {live['until']}"
                     if live["until"] else ", no clock")
            lines.append(f"  {track} card: {drawn['name']} "
                         f"(day {live['day']}{until})")
        who = layer.get("necromancer")
        if who is not None:
            lines.append(f"  the fog's cause: {who['name']}, L{who['level']} "
                         f"(named day {who['since']})")
        lines.append("  deck: "
                     + ", ".join(f"{track} {len(layer[DECK_KEY[track]])}"
                                 for track in TRACKS)
                     + f" left, {len(layer['drawn'])} drawn")
    return lines


# --------------------------------------------------------------------------- #
# What the weather does to the road, and what the storm drives you into
# --------------------------------------------------------------------------- #

TRAVEL_SLOW = {                 # a state that makes a leg take a day longer
    "fords-out": "the fords are out -- the road goes round by the bridges",
    "dust-storm": "the dust has the plain -- nothing moves while it blows",
}


def travel_delay(world: dict, lands) -> tuple[int, list[str]]:
    """What the weather costs a trip: one extra day per LAND the leg touches
    that is holding a road-closing state, and the line that says why. This is
    THE FORD IS OUT's travel half -- the priced menu half (the ferrymen's
    rates) is authored on the card and waits for the economy floor."""
    days, lines, seen = 0, [], set()
    for polity in dict.fromkeys(lands):
        if polity is None or polity not in world["lands"]:
            continue
        held = set(state_ids(world, polity))
        hit = next((s for s in TRAVEL_SLOW if s in held), None)
        if hit is None:
            continue
        days += 1
        if hit not in seen:
            seen.add(hit)
            lines.append(f"  {world['lands'][polity]['name']}: "
                         f"{TRAVEL_SLOW[hit]} (+1 day).")
    return days, lines


# --- the cabin table (BIG RAIN's other half) -------------------------------- #
# The storm's real content is not the penalty, it is where the penalty drives
# you. A wilds night under a storm rolls for SHELTER, and what the shelter
# HOLDS is the table -- five owners, one of whom means it and one of whom
# very much does not. The replayability is the table; the mechanics are two
# lines (a dry night skips the exposure check and the foul-weather grumble).
#
# Each row is what the party SEES plus a DM-eyes note: the sinister row would
# be no scene at all if the display announced it, so the display does not.

SHELTER_CHANCE = 0.45           # of wilds nights spent under a storm
CABIN_HOSTS = ("a charcoal-burner", "an old shepherd", "a soldier's widow",
               "a hermit", "a forester", "a trapper", "a bee-keeper",
               "a herb-woman", "a retired sergeant", "a miller's brother")
CABIN_TABLE = (
    (25, "helpful",
     "The door opens before anyone knocks: {host}, alone out here and glad "
     "of the faces. The fire is built up and the pot is filled out, and "
     "nothing is asked for.",
     "Exactly what they look like. A free dry night -- and they know this "
     "ground better than any map does."),
    (20, "job",
     "{host} takes the party in and keeps looking at the door. Something "
     "out here has been going wrong for a while, and they have been waiting "
     "for somebody to tell about it.",
     "A job offered over the fire: local, small and real. Post it or run it "
     "on the spot."),
    (20, "valuable",
     "{host} takes the party in. One thing in this cabin does not belong in "
     "it, and the way they keep themselves between it and the room says "
     "they know what it is worth.",
     "Wealth in a house with no lock. Either it is still theirs -- or "
     "robbers had it last week and they want it back."),
    (15, "sinister",
     "{host} is very glad to see the party. The stew has been on a long "
     "time, and they keep filling bowls nobody asked for.",
     "DM EYES ONLY: the host means them harm -- the pot, then the axe, and "
     "the last guests are under the floor."),
    (20, "priced",
     "{host} holds the door half-open and names a price for the night. It "
     "is a serious price. The rain says it is worth it.",
     "A dry night for coin -- the priced menu, out here. Haggling is fair; "
     "so is the door shutting again."),
)


def cabin(rng: random.Random) -> dict:
    """One roll on the cabin table: who is inside, and what they are."""
    row = rng.choices(CABIN_TABLE, weights=[r[0] for r in CABIN_TABLE])[0]
    host = rng.choice(CABIN_HOSTS)
    return {"kind": row[1], "sight": row[2].format(host=host),
            "dm": row[3], "host": host}


def shelter_roll(rng: random.Random) -> dict | None:
    """A storm-night roll for a roof: the cabin, or another night in it."""
    if rng.random() >= SHELTER_CHANCE:
        return None
    return cabin(rng)


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
        if drawn["track"] not in TRACKS:
            raise ValueError(f"{key}: no such track: {drawn['track']}")
        for polity in drawn["land"]:
            if polity != ANY_LAND and polity not in LAND_SPECS:
                raise ValueError(f"{key}: no such land: {polity}")
        if ANY_LAND in drawn["land"] and len(drawn["land"]) > 1:
            raise ValueError(f"{key}: {ANY_LAND} names every land already")
        if not 0 < drawn["chance"] <= 1:
            raise ValueError(f"{key}: chance out of range: {drawn['chance']}")
        for word in drawn["admits"]["weather"] + (drawn["sky"],):
            if word and word not in WEATHER_WORDS:
                raise ValueError(f"{key}: no such weather: {word}")
        if drawn["sky"] and drawn["track"] != "weather":
            raise ValueError(f"{key}: only the weather track holds the sky")
        if drawn["admits"]["wet"] and drawn["admits"]["dry"]:
            raise ValueError(f"{key}: a spell is wet or dry, never both")
        need = drawn["admits"]["dry"]
        if not (need == PROFILE_SPELL or isinstance(need, int)):
            raise ValueError(f"{key}: a dry spell is a count or "
                             f"{PROFILE_SPELL!r}: {need!r}")
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
    for environment, profile in ENVIRONMENT_PROFILES.items():
        weights = profile.get("weather")
        if not weights:
            raise ValueError(f"{environment}: no weather distribution")
        if not profile.get("drought_days"):
            raise ValueError(f"{environment}: no drought threshold")
        for word in weights:
            if word not in WEATHER_WORDS:
                raise ValueError(f"{environment}: no such weather: {word}")
        if not sum(weights.values()):
            raise ValueError(f"{environment}: a sky that never rolls")
    for environment, local in WEATHER_LOCAL.items():
        if environment not in ENVIRONMENT_PROFILES:
            raise ValueError(f"no such environment: {environment}")
        for word in local:
            if word not in WEATHER_WORDS:
                raise ValueError(f"{environment}: no such weather: {word}")


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
    print("")
    print("-- a night under the storm --")
    found = cabin(random.Random(args.seed))
    print(f"  SHELTER ({found['kind']}): {found['sight']}")
    print(f"  ({found['dm']})")


if __name__ == "__main__":
    main()
