"""The world layer -- the WORLD & NPC SIMULATION build's frame, weather,
economy floor and politics.

plan.md's ladder. The FRAME session (2026-08-07): `worldsim.md`'s five record
kinds stop being prose and become data, and the save grows a world layer under
every land. The WEATHER session (2026-08-08): the first content rung on top of
it -- every land rolls a sky every day off its climate, and three tracks of
cards now run over one land instead of one. The ECONOMY FLOOR (2026-08-09):
the three outlets the frame carried but did not apply -- the BOARD, the
PRICED MENU and the ENCOUNTER TABLE -- are wired, the per-land card bill goes
up to the asymmetry doctrine's floor with chains running through it, and the
relations table grows past the frame's nine edges. POLITICS (2026-08-10):
the land stops being an economy with a sky over it and becomes a POLITY --
who holds it, what it is fighting about, and who is pulling at whom.

THE POLITICS FRAME, in the order worldgen rolls it. A land's politics is
three rolls and one authored table, and every one of them is a GATE on
content rather than a system of its own:

  the CONSTITUTION -- one exclusive slot per land, rolled on a default-heavy
                      die (the wealth-band pattern). Cards never flip it;
                      the two that do (the junta, the commune) say so.
  the TENSIONS     -- each land's packet lists two named blocs and what they
                      fight over. A land rolls ONE, and a second if it opens
                      in CRISIS. Only cards whose tension holds enter the
                      land's crisis deck -- the SAME deck as the econ cards,
                      no second pile -- which is what keeps the pool wide
                      and each rolled world specific.
  the FACTIONS     -- the rolled tensions imply a small faction cast, and
                      the authored directed verb EDGES between them (crown
                      FUNDS secret police; anarchists SABOTAGE steel barons)
                      are the in-land counterpart of a relation. An edge is
                      live when both its ends are in the cast, and cards
                      admit on it.
  the RULER        -- `rulers.py`'s sheet, rolled onto the land's RULER
                      notable: three weighted draws off 357 words, derived
                      `heart`, the succession and accession circumstances.
                      Cards admit on the bare trait word.

The WAR MATERIAL rides the same tables: four DIPLOMATIC INSTRUMENTS
authored as relation edges (the courtly hostage, the yearly tribute, the
marriage pact, the personal union), and the SUCCESSION cluster -- cards
that admit on the crown's succession state and can move it.

THE TWO INVARIANTS (the thread's own, landed by the economy floor):

  the BOARD reacts to world state -- a land's wealth band and the cards
  standing over it move how much work is posted, what it pays, and what work
  IS there (a card posts its own job, and one that stops the town takes
  slots off);

  something moves WITHOUT the player taking a job, and is VISIBLE on return
  -- the news and the state diff shipped with the frame; now the board, the
  prices and the road have all moved too by the time the party walks back in.

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
  A state may live in an EXCLUSIVE SLOT -- setting a slot clears whatever
  it held -- though `STATE_SLOTS` is empty since the human contraction and
  the frame is waiting on the next country packet.
- **The relations.** Authored directed edges between lands: who eats whose
  grain, who raids whose border, whose crowns are kin. Never a
  traded quantity -- a lookup. The states they DERIVE (a failed harvest in
  a granary puts grain-scarce on everyone it feeds) are computed at read
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
  encounter / news / state flip); an optional day-stamp clock. All five are
  applied now: the news line and the state flip here, the other three by the
  readers at the bottom of the file that the board, the shops and the road
  call (`board_shift` / `board_pay` / `board_postings`, `menu_terms`,
  `encounter_entries`).
- **The chain.** A card SETS a state that outlives it; the next card in the
  chain ADMITS on that state and CLEARS it as it fires. No new machinery --
  the admitting conditions already read what the last card left behind. The
  famine chain (a failed harvest leaves bread dear, and the dear bread is
  what the riot admits on), the forgers who move in after the bank fails,
  and the raid a dead pasture sends out are the shipped chains. One of
  them crosses a RELATION: a Tergal clan whose herds died raids the
  western grain the same failed harvest already made dear.
- **The sky.** Every land rolls one weather word a day against the weights
  of the GROUND THE PARTY IS STANDING ON and the season of the year
  (`CLIMATE_WEATHER` x `season_of`), tracking the WET and DRY spells
  running behind it. A land the party is not in reads its capital's
  climate instead; the spells stay on the land, which is why crossing a
  climate border does not reset the drought behind you. A held DROUGHT
  bends the roll that produced it. The sky is what the weather track's
  cards admit on, what the exposure check and the storm penalties read,
  and what the party sees on the road.

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

import rulers                    # the politics rung's person half: the
                                 # weighted trait pool a crown is rolled off
from places import (CAPITAL_TILES, CLIMATE_PROFILES, CULTURE_LANDS,
                    CULTURE_OF, LAND_SPECS, add_state, clear_state,
                    detail_wrap, land_id, stable_seed, tile_coordinate,
                    tile_id, tile_label)
from sites import FOES           # the encounter outlet's vocabulary: a card
                                 # that puts foes on a road names catalog rows
                                 # like every other roster in the game

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
                                # number: the threshold is then the
                                # GROUND's own (places.CLIMATE_PROFILES'
                                # drought_days), because a drought is a
                                # relative thing -- a fortnight without rain
                                # is a disaster in the forest and a Tuesday
                                # in the dry south
DROUGHT_WET_MULT = 0.15         # what a held drought does to the rain and
                                # storm weights -- the state bending the roll
                                # that made it, which is why a drought lasts
DROUGHT_DRY_BONUS = 1.35        # ...and what it does to clear and heat

# --- the economy floor's knobs (2026-08-09) -------------------------------- #
# THE BAND IS THE BASELINE the three outlets read; the cards move it from
# there. A land's wealth is not a decoration on a readout any more: it is how
# much work is posted, what the work pays, and what the shelves cost.
BAND_SLOTS = {                  # what the band does to a settlement's board
    "crisis": -1,               # the lords have other things to pay for --
    "normal": 0,                # and the CARDS post the trouble back on top,
    "prosperous": 1,            # so a crisis board is short of ORDINARY work
}
BAND_PAY = {                    # ...and to what a posting quotes
    "crisis": 0.85,             # a poor land pays poorly. This is the reason
    "normal": 1.0,              # to look at the map before taking the job
    "prosperous": 1.15,         # under your nose
}
BOARD_SLOTS_FLOOR = 1           # however bad it gets, a settlement is never a
                                # place with no work in it at all

# THE PRICED MENU. Six terms, each a MULTIPLIER on a price the game already
# charges, so the world layer never has to own a price -- it moves one.
MENU_TERMS = (
    "goods",        # the general shop: potions, salve, ammo, doses
    "steel",        # the smith: weapons, masterwork, a commission
    "lodging",      # a night at the inn
    "healer",       # the healer's fee per severity
    "toll",         # the road: what the bridges and the gates take
    "ferry",        # ...and what the ferrymen take when the fords are gone
)
BAND_MENU = {                   # the band's own hand on the shelf
    "crisis": {"goods": 1.20, "steel": 1.15, "lodging": 0.80},
    "normal": {},
    "prosperous": {"goods": 0.90, "steel": 0.90, "lodging": 1.30,
                   "healer": 1.15},
}
MENU_FLOOR, MENU_CEILING = 0.5, 4.0     # nothing is ever free and nothing is
                                        # ever unbuyable: the terms multiply,
                                        # so three bad states stacking gets
                                        # clamped rather than absurd
ROAD_TOLL_SILVER = 6              # the base a toll state takes off a party
                                # crossing one land, times the `toll` term
ROAD_FERRY_SILVER = 4             # ...and what the ferry costs, times `ferry`.
                                # Both are small on purpose: the road tax is
                                # a texture, not a wall (the fords cost a DAY,
                                # and days are the expensive currency here)

# THE LOCAL ENCOUNTER TABLE. A live entry does not replace the road's own
# table -- it sits ON it, and this is how often the road serves the world's
# trouble instead of its own wildlife.
ENCOUNTER_CHANCE = 0.5          # per rolled encounter, when an entry stands
ENCOUNTER_WHERE = ("road", "wilds", "any")

# --- the politics knobs (2026-08-10) --------------------------------------- #
TENSION_ROLLS = 1               # what a land is fighting about. ONE, so the
                                # packet stays a POOL and the same land comes
                                # up a different flavor of itself next
                                # playthrough...
CRISIS_TENSION_ROLLS = 2        # ...and two when it opens in CRISIS, because
                                # a land in trouble is in trouble about more
                                # than one thing at once

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
    # the western culture
    "harvest-failed": "the harvest has failed",
    "bread-dear": "bread is expensive",
    "bread-riots": "there is rioting over the bread",
    "toll-squeeze": "the tolls are doubled",
    "overtaxed": "the war tax is on",
    "monopoly-squeeze": "the lord's mill takes its share",
    "fair-on": "the great fair is on",
    # the southern culture
    "tax-farmed": "the province is farmed out",
    "paper-worthless": "the banks have shut their doors",
    "bad-paper": "forged notes are about",
    "note-hunt": "the note-hunters are out",
    "paper-pay": "wages are paid in paper",
    "coin-flush": "the colony fleet is in",
    # Tergal. The two words a Tergal card and a Thule card both set --
    # `raiding` and `tribute-taken` -- are worded for BOTH since the norse
    # packet (2026-08-22): the readout says what happened, the card's own
    # news line says whether it was horses or ships.
    "herd-loss": "the herds are dying",
    "grass-gone": "the grass has not come back",
    "raiding": "the raiding season is on",
    "tribute-taken": "a war-leader is paid to stay home",
    "herd-drive": "the great drive is on",
    "mercenary-home": "a war-rich mercenary is home",
    # Thule (2026-08-22, the norse packet)
    "kings-share": "the sea-king takes his share",
    "blood-feud": "two houses are in blood feud",
    "weregild": "a man's price is being haggled",
    "thing-sitting": "the assembly is sitting at the stone",
    "outlawed": "a man is outlawed for three years",
    "berserks": "the oath-drinkers are sworn",
    "ring-giver-poor": "the chief's silver has run out",
    "land-taking": "hazel poles mark a new claim",
    "grove-sacrifice": "the nine of every kind hang",
    "seer-spoke": "the seer has named the winter's dead",
    "curse-pole": "a curse-pole is up with a name on it",
    "drowned-crew": "a ship did not come home",
    "whale-ashore": "a whale is ashore and being cut up",
    "herring-run": "the herring run is on",
    "ice-locked": "the harbors are frozen shut",
    "wolf-winter": "wolves are at the byres",
    "white-storm": "the white storm has shut the coast",
    # Weather (2026-08-08, land-agnostic -- the sky's own states)
    "storm-bound": "the storm has closed the roads",
    "fords-out": "the fords are out",
    "drought": "the rains have not come",
    "bones-walk": "bones walk in the fog",
    "wildfire": "the forest is burning",
    "burned-over": "the burn is still black",
    "dust-storm": "a dust storm covers the plain",
    "smog": "the smoke will not lift",
    # Politics (2026-08-10) -- right, office and allegiance. The west
    # carries the most of them: the baseline land takes the deepest packet.
    "interdict": "the temple has closed the land",
    "order-trial": "the order hanged a local man",
    "royal-progress": "the king's court is here",
    "lord-banned": "a lord is dead in law",
    "warband-settled": "a Tergal warband holds the border grant",
    "badge-men": "a lord's badge-men are the law here",
    "wardship-sold": "a child heir's wardship is up for sale",
    "custom-strike": "the village works to the letter",
    "rolls-burned": "the manor's court rolls are ash",
    "town-air": "a runaway smith is behind the town gate",
    "bailiff-loose": "the bailiff runs the court as his purse",
    "rent-strike": "the village will not pay",
    "widow-holding": "a widow holds the valley's best land",
    "strips-merged": "two families hold the best soil",
    "jury-lies": "the jury swore it in the law's teeth",
    "cry-ignored": "nobody answers the hue and cry",
    "forest-law": "the royal woods are closed",
    "silver-strike": "there is silver on the lord's land",
    "champions-hired": "lawsuits are settled at swordpoint",
    "charter-run": "the town is buying its charter",
    "mayor-in-velvet": "a wool merchant sits as mayor",
    "tithe-war": "the tithe barn is being counted twice",
    "priest-scandal": "the rectory is a scandal",
    "witch-finder": "a witch-finder is working the villages",
    "dancing-plague": "a street cannot stop dancing",
    "free-company": "an unpaid company holds the roads",
    "midnight-court": "masked men are hanging by night",
    "faith-banned": "the old faith is outlawed",
    "duel-fugitive": "a duelist is on the road, and hunted",
    "warrants-sold": "arrest warrants are for sale blank",
    "tontine-deaths": "the tontine's survivors are dying",
    "shares-mad": "the colony shares have gone mad",
    "quarter-ruined": "half the merchant quarter is ruined",
    "alchemists-funded": "the crown's alchemists are at work",
    "salt-revolt": "the salt country is in revolt",
    "auto-da-fe": "the tribunal is staging its penance",
    "bandit-king": "a bandit king holds the tax roads",
    "hostage-guard": "the chiefs' sons ride in the guard",
    "sworn-brothers": "two chiefs are brothers by oath",
    "mourning-war": "the clans are raiding for people",
    "shaming-pole": "a pole is up with a name on it",
    "ghost-dance": "the ghost dance is in the camps",
    # The succession cluster (the war layer's feed)
    "regency-on": "an infant wears the crown",
    "claim-pressed": "three branches claim the inheritance",
    "pretender": "a dead king has come back",
    "recognition-bought": "the neighbours accept the heir",
    "tanist-scramble": "every able kinsman is counting spears",
    # Religion (2026-08-11) -- worship, rite and the week's own calendar.
    # Politics kept church POWER; these are what a parish actually does.
    "relic-hunt": "a shrine's relic has been stolen",
    "bones-tested": "a saint's bones are being tested",
    "holy-well": "a well is healing people",
    "feast-lock": "the feast days have stopped the work",
    "hermit-window": "the hermit at the wall sees all",
    "abbey-suit": "the abbey holds a boy against his kin",
    "penance-season": "the hooded columns are out",
    "carnival-on": "carnival fills the streets",
    "dead-abroad": "the dead are guests tonight",
    "two-hoods": "two burial clubs want one corpse",
    "debate-riot": "the theology debate has gone to clubs",
    "called-child": "a child has the shaman sickness",
    "river-fouled": "the river was fouled; a fine is due",
    "black-tent": "the black shaman's tent is busy",
    "foreign-graves": "a foreign graveyard makes ghosts",
    "cairn-angry": "the pass-spirit has been offended",
    # Magic (2026-08-11) -- the gift, the theory, the reagents and the hunt
    "talent-loose": "an untrained talent is loose",
    "hunt-up": "there is a witch-hunt posted",
    "recruiters-out": "the wizards' scouts are out",
    "reagents-moving": "a reagent shipment is on the road",
    "basement-open": "the academy basement is counted",
    "necromancy-open": "the necromancers are working openly",
    "necromancy-purged": "the academy burned its necromancy",
    "tower-open": "a tower wizard is taking volunteers",
    "sky-bought": "a weather-worker has been paid",
    # The diplomatic instruments (held on the source land)
    "marriage-pact": "a marriage pact binds two crowns",
    "betrothal-broken": "the betrothal is broken",
    "personal-union": "a foreign king wears this crown too",
    # Derived (never held -- computed off the relations table)
    "grain-scarce": "grain is scarce",
    "raiders-out": "raiders are on the border",
    # ...the rest of what the cultures sell each other (2026-08-15)
    "timber-dear": "there is no northern timber to be had",
    "credit-dry": "the southern banks have stopped lending",
    "southern-goods-short": "the southern road brings nothing",
    "horses-dear": "remounts are scarce and dear",
    "hides-dear": "hides and wool are short",
    "swords-gone": "the hired clans have gone home",
    "wool-short": "there is no wool for the looms",
    # ...the religion and magic rung's own edges (2026-08-11)
    "schism-near": "the two rites are one insult apart",
    "hostage-given": "an heir of this land is a hostage abroad",
    "danegeld-paid": "the danegeld is being raised here",
    "pact-kin": "the pact makes the two crowns kin",
    "union-crown": "the two crowns are one head now",
    # THE MINERS' LEAGUE (2026-08-21, the tile economy arc's session 4).
    # Recovered from the pre-contraction catalog and re-homed: every one of
    # every culture holds mines now, so the extraction chain belongs
    # to all of them and to no one of them.
    "claims-collide": "two chapters claim one seam",
    "rush-on": "the rush is on",
    "strike": "the pits stand idle",
    "caravan-due": "the food caravan is coming up",
    # THE ROLLED WARS (2026-08-22, the medieval world arc's session 5). One
    # word, held by every belligerent land from day 0 to the end of the
    # campaign: the wars are rolled once and never end (rules.md).
    "at-war": "the country is at war",
}

# The CARD-DECLARABLE exclusive slots. Both authored slots went out with the
# human contraction (2026-08-15) and the table stood EMPTY until the tile
# economy arc put mines back on the map: the DEPOSIT slot returns with the
# Miners' League (2026-08-21, session 4), and it returns land-wide rather
# than mine-wide -- a card's tile ADDRESS is the snapshot arc's, so for now
# a land holds one deposit stage the way it holds one constitution. The
# other authored slot -- the standing of a sealed realm's foreigners -- has
# no successor among the three and stays gone. The game's other two
# exclusive slots -- the wealth band and the constitution -- have never gone
# through this table; each has its own setter.
STATE_SLOTS: dict[str, tuple[str, ...]] = {
    "deposit": ("deposit-normal", "deposit-found", "deposit-drying"),
}
SLOT_WORDS: dict[str, str] = {                  # member -> what it reads as
    "deposit-normal": "the seams run as they always have",
    "deposit-found": "a new seam has been found",
    "deposit-drying": "the seams are drying up",
}
SLOT_OF = {member: slot for slot, members in STATE_SLOTS.items()
           for member in members}
STATE_WORDS.update(SLOT_WORDS)

# WHAT A STATE DOES TO THE SHELF (2026-08-09, the economy floor). A card's
# own `menu` payload covers what IT charges for; this table covers what a
# state charges for no matter which card -- or which RELATION -- put it
# there. It is the only way a derived state can reach a price, and derived
# states are the whole point of the relations table: a failed harvest in
# a western land is felt on a shelf in Tergal, three weeks' road away.
STATE_MENU = {
    # derived (the edges' end of the table)
    "grain-scarce": {"lodging": 1.50, "goods": 1.15},
    "raiders-out": {"goods": 1.20, "lodging": 1.20},
    "timber-dear": {"goods": 1.20, "lodging": 1.15},
    "credit-dry": {"goods": 1.20, "steel": 1.25},
    "southern-goods-short": {"goods": 1.35, "healer": 1.20},
    "horses-dear": {"goods": 1.15, "steel": 1.10},
    "hides-dear": {"goods": 1.25},
    "swords-gone": {"steel": 1.20, "goods": 1.10},
    "wool-short": {"goods": 1.25},
    # held (the states a card leaves standing after its own terms lapse)
    "harvest-failed": {"lodging": 1.60, "goods": 1.20},
    "bread-dear": {"lodging": 1.25},
    "drought": {"lodging": 1.25, "goods": 1.10},
    "storm-bound": {"lodging": 1.30},
    "wildfire": {"goods": 1.20},
    "coin-flush": {"goods": 1.25, "lodging": 1.40, "steel": 1.15},
    "overtaxed": {"goods": 1.15, "steel": 1.15},
    "tax-farmed": {"goods": 1.25, "lodging": 1.15},
    "paper-worthless": {"goods": 1.30, "steel": 1.25},
    "herd-loss": {"goods": 1.20},
    # politics (2026-08-10) -- the states that outlive their card, and the
    # ones an edge derives, are the ones that have to reach a price here
    "danegeld-paid": {"goods": 1.20},
    "union-crown": {"toll": 0.80},
    "faith-banned": {"goods": 1.20, "steel": 1.15},
    "silver-strike": {"lodging": 1.30, "steel": 0.90},
    "warband-settled": {"lodging": 1.15},
    "royal-progress": {"lodging": 1.60, "goods": 1.25},
    "interdict": {"healer": 1.30},
    "free-company": {"toll": 1.80},
    "forest-law": {"goods": 1.15},
    "quarter-ruined": {"goods": 1.25, "lodging": 0.80},
    "salt-revolt": {"goods": 1.25},
    "bandit-king": {"goods": 1.15},
    # religion and magic (2026-08-11) -- a rite is a WEEK, and a week the
    # whole land keeps is felt at every counter in it
    "feast-lock": {"goods": 1.20, "steel": 1.15},
    "carnival-on": {"lodging": 1.50, "goods": 1.15},
    "penance-season": {"goods": 0.90, "lodging": 0.85},
    "holy-well": {"healer": 0.75},
    "reagents-moving": {"goods": 1.15},
    "hunt-up": {"lodging": 1.15},
    # the Miners' League (2026-08-21) -- the ore price IS the steel price,
    # and the deposit slot is the one state in the game that makes steel
    # CHEAP. It stacks under the tile menu's own pithead discount, which is
    # right: a strike at a working mine in a year of new seams is the
    # cheapest steel in the world
    "deposit-drying": {"steel": 1.20},
    "deposit-found": {"steel": 0.85},
    "strike": {"steel": 1.35},
    # Thule (2026-08-22, the norse packet) -- the two states that shut the
    # sea. Every counter in a land whose harbors are frozen or whose coast
    # is under the white storm is buying from a cart instead of a hull.
    "ice-locked": {"goods": 1.30, "lodging": 1.15},
    "white-storm": {"lodging": 1.35},
}
# The discipline that keeps the two halves from double-charging: a state
# belongs HERE when no card of its own carries a `menu` payload, or when it
# is derived and so has no card in this land at all. Cards that price their
# own weather (the smog, the fair) are not repeated in the table --
# `validate_content` enforces it.

# WHAT A STATE PUTS ON THE ROAD. Same idea, same reason: a card names the
# foes it brings itself, but a DERIVED state has no card in this land to
# name them, and raiders on the border have to be met somewhere.
STATE_ENCOUNTERS = {
    "raiders-out": {"kinds": ("cutthroat", "bruiser", "soldier"),
                    "where": "road", "as": "riders off the border",
                    "skins": {"cutthroat": "Rider", "bruiser": "Horse-Chief",
                              "soldier": "Lance"},
                    "chance": 0.45},
    "free-company": {"kinds": ("cutthroat", "archer", "soldier", "veteran"),
                     "where": "road", "as": "the unpaid company's toll post",
                     "skins": {"cutthroat": "Free Lance",
                               "archer": "Company Bow",
                               "soldier": "Company Man",
                               "veteran": "Old Hand"},
                     "chance": 0.50},
    "badge-men": {"kinds": ("cutthroat", "bruiser", "soldier"),
                  "where": "road", "as": "men in the lord's livery",
                  "skins": {"cutthroat": "Badge-Man",
                            "bruiser": "Badge-Bruiser",
                            "soldier": "Livery Sergeant"},
                  "chance": 0.40},
    "warband-settled": {"kinds": ("cutthroat", "bruiser", "soldier"),
                        "where": "road",
                        "as": "the border grant's own riders",
                        "skins": {"cutthroat": "Grant-Rider",
                                  "bruiser": "Oath-Breaker",
                                  "soldier": "Border Lance"},
                        "chance": 0.30},
    "bandit-king": {"kinds": ("cutthroat", "archer", "bruiser"),
                    "where": "road", "as": "the bandit king's road watch",
                    "skins": {"cutthroat": "Road Watch",
                              "archer": "Hedge Bow", "bruiser": "Toll-Taker"},
                    "chance": 0.40},
    # religion and magic (2026-08-11)
    "hunt-up": {"kinds": ("cutthroat", "archer", "hunter"),
                "where": "road", "as": "witchhunters working the road",
                "skins": {"cutthroat": "Witchhunter",
                          "archer": "Hunt Bow", "hunter": "Finder"},
                "chance": 0.35},
    # Thule (2026-08-22, the norse packet)
    "wolf-winter": {"kinds": ("wolf", "dire wolf"), "where": "wilds",
                    "as": "the pack working down from the fells",
                    "skins": {"wolf": "Byre-Wolf",
                              "dire wolf": "Winter-Wolf"},
                    "chance": 0.45},
    "outlawed": {"kinds": ("cutthroat", "archer", "bruiser"),
                 "where": "road", "as": "the outlaw's people on the road",
                 "skins": {"cutthroat": "Wood-Man",
                           "archer": "Outlaw Bow",
                           "bruiser": "Forest-Goer"},
                 "chance": 0.35},
    "foreign-graves": {"kinds": ("skeleton", "ghoul"), "where": "wilds",
                       "as": "what the buried dead sent up",
                       "skins": {"skeleton": "Grave-Made",
                                 "ghoul": "Earth-Eater"},
                       "chance": 0.45},
    # The rolled wars (2026-08-22, session 5). A country at war puts one
    # thing on its roads that peace does not: men moving with the war and
    # men running from it. Who, never how hard -- the danger curve is the
    # road's own.
    "at-war": {"kinds": ("soldier", "cutthroat", "bruiser"),
               "where": "road",
               "as": "soldiery, deserters and people off the war road",
               "skins": {"soldier": "Levy", "cutthroat": "Deserter",
                         "bruiser": "Straggler"},
               "chance": 0.35},
}

# WHAT A STATE PUTS IN THE CRIME LAYER'S MARK TABLE (2026-08-11, the
# religion & magic rung). The third of the same shape: a state that makes a
# NEW kind of mark exist here adds its faces to a category's roll, and the
# casing prints them like any other. This is the reagent trade's crime-layer
# wiring (worldsim.md: compact, high-value, provenance-sensitive -- natural
# heist marks and the smuggling category's luxury end), plus the two the
# religion packets pre-ordered: the tomb that is the mountain's richest room
# and the mask that is perfect cover.
STATE_MARKS = {
    "reagents-moving": {
        "heist": ("the reagent vault under the academy",),
        "burglary": ("a wizard's reagent case, locked twice",),
        "caravan": ("the reagent train: four wagons and one wizard",),
        "powder": ("a crate of golden fleece, and worse",),
    },
    "relic-hunt": {
        "burglary": ("the rival shrine's reliquary",),
        "con": ("a pilgrim town that wants a saint badly",),
    },
    "carnival-on": {
        "pickpocket": ("a masked reveller with a full purse",),
        "burglary": ("a great house whose servants are all out",),
        "con": ("a masked table that cannot see your face either",),
    },
}

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

# COUNTRY vs CULTURE (2026-08-21, the medieval world arc's session 2). Nine
# countries wear four card packets. Everything authored below names EITHER a
# culture -- the packet is that culture's, wherever it is worn -- or a single
# land, where the content is that land's own. `_expand` is the one door
# between the two: it resolves the authored word into the land keys the
# runtime actually asks about, and it leaves ANY_LAND and a bare land key
# alone.
CULTURES = dict(CULTURE_LANDS)


def _expand(land: str | tuple[str, ...]) -> tuple[str, ...]:
    """The land keys an authored `land=` field names."""
    names = (land,) if isinstance(land, str) else tuple(land)
    out: list[str] = []
    for name in names:
        out.extend(CULTURES.get(name, (name,)))
    return tuple(dict.fromkeys(out))


def _by_land(table: dict) -> dict:
    """One authored table keyed by culture or by land, re-keyed by LAND --
    which is what every reader of it asks with.

    ADDITIVE since 2026-08-22 (the norse packet's card audit): a land's row
    is its culture's entries followed by its own. That is what lets a
    single land carry a tension its culture does not -- Byzantium's
    penitents-against-carnival is the southern heir's alone -- without a
    land having to repeat its whole culture's list to add one line."""
    out: dict = {}
    for key, value in table.items():
        for polity in _expand(key):
            out[polity] = out.get(polity, ()) + tuple(value)
    return out


def card(key: str, name: str, land: str | tuple[str, ...], *,
         track: str = "crisis",
         wealth: tuple[str, ...] = BANDS,
         states: tuple[str, ...] = (),
         without: tuple[str, ...] = (),
         weather: tuple[str, ...] = (),
         wet: int = 0,
         dry: int = 0,
         tension: tuple[str, ...] = (),
         constitution: tuple[str, ...] = (),
         traits: tuple[str, ...] = (),
         succession: tuple[str, ...] = (),
         faction_edge: tuple[str, ...] = (),
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
    behind it. The politics rung adds four more, each ANY-OF because each
    reads a slot that holds one or two values: `tension` (which is also the
    gate that decides whether the card enters this land's deck at all),
    `constitution`, `traits` (the land ruler's rolled words -- a card that
    wants a whole family names all of it), `succession` (the crown's
    circumstance) and `faction_edge` (a live edge key). `chance` is the
    card's own die once it is admitted -- 1.0 for
    an ordinary card, low for the rare and the supernatural. `days` is the
    optional day-stamp clock -- None for a pulse that stands until something
    else moves it. `sky` is for a card that IS the weather rather than a
    consequence of it: while such a card stands, the land's day roll is
    skipped and its sky is this word, so a storm that "sets in for two
    days" is a storm on both of them. `hook(world, land, day, rng)` runs at
    the firing and returns format fields for the news line (the fog's
    necromancer is the one customer: a card that has to NAME somebody).

    The keyword arguments are the OUTLET effects, at most one per outlet:

      news=      "the line the land hears"
      state=     {"set": (), "while": (), "clear": (), "slot": {},
                  "wealth": "band", "wealth_while": "band",
                  "constitution": "key", "succession": "state"}
      quest=     {"post": job(...), "pay": 1.25,     # what it PUTS UP
                  "slots": -1, "reprice": 0.9}       # ...and cancels/reprices
      menu=      {"goods": 1.2, ...}   MENU_TERMS -> multiplier
      encounter= {"kinds": (), "where": "road", "skins": {}, "as": "",
                  "chance": 0.5}       the local table entry it adds

    The news and the state flip are applied by `_fire` below, at the roll
    point. The other three are READ where they land -- the board when it
    refills (`board_shift` / `board_pay` / `board_postings`), the shop when
    it quotes (`menu_terms`), the road when it rolls (`encounter_entries`)
    -- because all three are questions asked of the world, not events done
    to it.
    """
    unknown = set(outlets) - set(OUTLETS)
    if unknown:
        raise ValueError(f"{key}: not an outlet: {sorted(unknown)}")
    state_effect = outlets.get("state") or {}
    if days is None and (state_effect.get("while")
                         or state_effect.get("wealth_while")):
        raise ValueError(f"{key}: a card with no clock never ends, so a "
                         f"'while' payload would never come off -- give it "
                         f"days or make the effect 'set'")
    lands = _expand(land)
    return {"key": key, "name": name, "land": lands, "track": track,
            "chance": chance, "hook": hook, "sky": sky,
            "admits": {"wealth": tuple(wealth), "states": tuple(states),
                       "without": tuple(without), "weather": tuple(weather),
                       "wet": wet, "dry": dry,
                       "tension": tuple(tension),
                       "constitution": tuple(constitution),
                       "traits": tuple(traits),
                       "succession": tuple(succession),
                       "edge": tuple(faction_edge)},
            "days": days,
            "outlets": {k: v for k, v in outlets.items() if v}}


def in_land(spec: dict, polity: str) -> bool:
    """Does this card belong to that land's deck? (ANY_LAND belongs to all.)"""
    return ANY_LAND in spec["land"] or polity in spec["land"]


def job(title: str, desc: str, *, pool: tuple[str, ...],
        sites: tuple[str, ...], giver: str, epilogue: str,
        failure_epilogue: str, places: int = 1,
        skins: dict | None = None, align: str = "good") -> dict:
    """A card's POSTED JOB -- an ordinary quest template (`quests.TEMPLATES`
    shape), authored on the card that puts it up. It goes through
    `quests.build_quest` like every other posting, so a card's work has real
    geography, a real giver's face and a real epilogue; the only thing the
    card adds is that it EXISTS while the card does and comes off with it.

    The level is the settlement's own band, clamped into the pool's
    (`template_band`), exactly as a rolled posting is -- the card decides
    what the work IS, never how hard it is."""
    return {"title": title, "desc": desc, "pool": tuple(pool),
            "sites": tuple(sites), "giver": giver, "epilogue": epilogue,
            "failure_epilogue": failure_epilogue, "places": places,
            "skins": dict(skins or {}), "align": align}


def relation(source: str, target: str, kind: str, *,
             when: tuple[str, ...], then: str, because: str) -> dict:
    """One authored directed edge. `when` are states of the SOURCE land
    (any of them is enough); `then` is the state the TARGET land derives
    while they hold; `because` is what the readout says the cause was.
    Static data read at roll time -- never a traded quantity."""
    return {"from": source, "to": target, "kind": kind,
            "when": tuple(when), "then": then, "because": because}


# --- the last two record kinds (2026-08-11, the religion & magic rung) ----- #
# worldsim.md opened with five. Three of them became code in the frame and
# the two content rungs after it; these are the other two, and they are the
# cheap ones on purpose.
#
# A FACT costs nothing at runtime: the engine never reads one. It is the
# standing colour of a land -- what its people believe, how magic works here
# -- and its whole surface is the DM's `lore` page. It earns its place by the
# characteristic criterion the same way a card does: every fact below either
# stands behind a card in this file or names a thing the player can pay for.
#
# An OPTION is the sixth outlet's own record: a STANDING player-initiated
# action whose terms local state sets. It is not a card and never fires --
# it sits at a counter waiting to be bought, and what it costs is the land's
# own priced menu.

SERVICES = ("bless", "book", "sky")     # the closed verb set an option buys


def fact(land: str | tuple[str, ...], key: str, title: str,
         line: str) -> dict:
    """One standing fact, for the DM. `land` is a land, a culture or
    ANY_LAND, exactly like a card's. `title` is the SHOUTED handle the table
    refers to it by; `line` is what it means in play."""
    return {"land": _expand(land), "key": key, "title": title, "line": line}


def option(key: str, name: str, land: str | tuple[str, ...], *,
           does: str, silver: int, term: str, line: str,
           states: tuple[str, ...] = (), without: tuple[str, ...] = (),
           tension: tuple[str, ...] = (), kinds: tuple[str, ...] = (),
           days: int = 0, gives: int = 0, word: str = "",
           holds: int = 0) -> dict:
    """One standing priced service a land sells. `does` is one of SERVICES
    -- the closed set of things the engine already knows how to do, because
    an option that needs new machinery is a feature request, not content.

    `silver` is the catalog price and `term` the priced-menu term that moves
    it, so a service is charged exactly the way a bed or a healer's day is:
    the world layer never owns a price, it moves one. `states` / `without` /
    `tension` gate it the way a card's admits do (an option nobody can reach
    is dead data, so every one of them is reachable in a rolled world), and
    `kinds` narrows it to settlement tiers where the packet says so.

    `days` is the per-party cooldown, `gives` what a blessing is worth,
    `word` the sky a weather-worker sells and `holds` how many days he
    holds it."""
    if does not in SERVICES:
        raise ValueError(f"{key}: no such service: {does}")
    lands = _expand(land)
    return {"key": key, "name": name, "land": lands, "does": does,
            "silver": silver, "term": term, "line": line,
            "states": tuple(states), "without": tuple(without),
            "tension": tuple(tension), "kinds": tuple(kinds),
            "days": days, "gives": gives, "word": word, "holds": holds}


# --------------------------------------------------------------------------- #
# The politics frame (2026-08-10): what a land IS, before anything happens
# --------------------------------------------------------------------------- #
# Three rolls and one authored table. None of them is a system: the
# constitution is a word on the readout, the tensions are the deck's gate,
# and the factions are names an edge joins. What they buy is that a land's
# trouble comes from its own axis and that two playthroughs of the same land
# are not the same land (worldsim.md's selection doctrine: a packet is a
# POOL, not a description).


def constitution(key: str, name: str, weight: int, line: str) -> dict:
    """One entry in a land's exclusive constitution slot. `weight` is its
    share of a DEFAULT-HEAVY die: the stereotype is the constant, and the
    variants are the colour worldgen rolls on top of it."""
    return {"key": key, "name": name, "weight": weight, "line": line}


def tension(key: str, line: str, *, factions: tuple[str, ...]) -> dict:
    """One standing tension: two named blocs and what they fight over. It
    is the gate a political card admits on, and the cast its faction edges
    are drawn from."""
    return {"key": key, "line": line, "factions": tuple(factions)}


def faction(key: str, name: str, face: str = "") -> dict:
    """One bloc. `face` names the notable post that fronts it where the
    cast already has one (quests.py's RULER / SAGE / WILDCARD), so a
    faction gets a face for free instead of asking for a new NPC."""
    return {"key": key, "name": name, "face": face}


def edge(scope: str, source: str, verb: str, target: str, line: str) -> dict:
    """One authored directed verb edge inside a land -- the in-land
    counterpart of `relation`. `scope` is the culture (or the single land)
    that owns the quarrel, and it is also the edge key's namespace. The edge
    is LIVE when both its ends are in a land's rolled faction cast, and a
    card admits on its key."""
    return {"key": f"{scope}/{source}-{verb}-{target}",
            "scope": scope, "land": _expand(scope),
            "from": source, "verb": verb, "to": target, "line": line}


_CONSTITUTIONS: dict[str, tuple[dict, ...]] = {
    "western": (
        constitution("feudal", "DECENTRALIZED FEUDALISM", 6,
                     "a crown among great lords, strong on its own manors "
                     "and weak past them"),
        constitution("centralizing", "THE CENTRALIZING CROWN", 2,
                     "royal judges ride the circuit, private castles need "
                     "a licence, and lords pay coin instead of service"),
        constitution("magnate-anarchy", "ARISTOCRATIC ANARCHY", 1,
                     "an elective crown, a veto in every great lord's "
                     "hand, and barons who rule their own ground"),
        constitution("regency", "THE REGENCY", 1,
                     "an infant king, and a council governing in his name"),
    ),
    "southern": (
        constitution("absolutism", "ABSOLUTISM", 6,
                     "one king, one law, one faith: the king's "
                     "commissioners sit over the old courts"),
        constitution("ministerial", "MINISTERIAL RULE", 2,
                     "the king reigns and the cardinal governs"),
        constitution("princes-in-arms", "THE PRINCES IN ARMS", 1,
                     "the great princes are under arms to control the "
                     "crown, never to depose it"),
        constitution("bankrupt-summons", "THE BANKRUPT SUMMONS", 1,
                     "the treasury is empty and the old estates are "
                     "called for the first time in living memory"),
    ),
    "tergal": (
        constitution("confederacy", "THE CLAN CONFEDERACY", 6,
                     "sovereign clans under a great council that elects "
                     "the high chief, settles the feuds and votes the wars"),
        constitution("great-chief", "THE GREAT CHIEF", 2,
                     "one chief holds the whole plain under the Sky's "
                     "mandate, and the warbands no longer ride by clan"),
        constitution("two-chiefs", "TWO CHIEFS", 1,
                     "a peace chief for law and the seasons, a war chief "
                     "who commands only while the banner is up"),
        constitution("fractured", "THE FRACTURED CLANS", 1,
                     "no high chief, and the feuds run with nobody to "
                     "settle them"),
    ),
    # The NORSE slot (2026-08-22, the norse packet; the first two shipped
    # with the nine as the minimum the frame demands).
    "norse": (
        constitution("sea-kings", "THE SEA-KINGS", 6,
                     "a dozen harbor lords with ships, and a first among "
                     "them who is obeyed as far as his oars reach"),
        constitution("allthing", "THE ALLTHING", 2,
                     "the free men meet at the stone every summer, speak "
                     "the law aloud, and go home again"),
        constitution("high-king", "THE HIGH KING", 1,
                     "one king over all the harbors, a foreign crown's "
                     "priest at his elbow, and taxes nobody used to pay"),
        constitution("scattered-jarls", "THE SCATTERED JARLS", 1,
                     "no first among them at all: every fjord its own "
                     "jarl, and the law stops at the next headland"),
    ),
}

# The blocs. Most are named by exactly one land's tensions; the shared ones
# (crown, clans) are named the same way in each so an edge reads the same
# everywhere.
FACTIONS: dict[str, dict] = {f["key"]: f for f in (
    # the western culture
    faction("crown", "the crown", face="ruler"),
    faction("great-lords", "the great lords"),
    faction("guilds", "the merchant guilds", face="wildcard"),
    faction("temple", "the temple", face="wildcard"),
    faction("militant-order", "the militant order"),
    faction("new-men", "the new men"),
    faction("manor-lord", "the lord of the manor"),
    faction("village", "the village"),
    # Tergal
    faction("clans", "the clans"),
    faction("rival-clans", "the rival clans"),
    faction("clan-mothers", "the clan mothers"),
    faction("outlaws", "the outlaw bands"),
    # the southern culture
    faction("sword", "the sword nobility"),
    faction("robe", "the robe nobility", face="wildcard"),
    faction("tribunal", "the faith's tribunal", face="wildcard"),
    faction("hidden-faith", "the hidden faith"),
    faction("commissioners", "the king's commissioners"),
    faction("provinces", "the provinces"),
    # -- religion and magic (2026-08-11). Politics kept church POWER; these
    # are the blocs that fight over worship, rite and the art itself.
    faction("shrines", "the shrine towns"),
    faction("rival-shrines", "the rival shrines"),
    faction("abbey", "the abbey", face="sage"),
    faction("penitents", "the penitent wing"),
    faction("carnival", "the carnival wing"),
    faction("academy", "the wizards' academy", face="sage"),
    faction("white-shamans", "the white shamans", face="sage"),
    faction("black-shaman", "the black shaman"),
    # -- Thule (2026-08-21, the nine; completed 2026-08-22 by the norse
    # packet's other two tensions).
    faction("jarls", "the jarls", face="ruler"),
    faction("freeholders", "the freeholders"),
    faction("sea-kings", "the sea-kings"),
    faction("land-chiefs", "the land-chiefs"),
    faction("grove-priests", "the grove priests", face="sage"),
    faction("missionaries", "the missionaries", face="wildcard"),
    faction("feud-house", "the house that struck first"),
    faction("rival-house", "the house that struck back"),
)}

# What each land is fighting about. A land rolls one (two in crisis); the
# STANDING entries are held on top of the roll, because some tensions are
# not colour -- the western manor is the econ packet's oppression axis and
# is always there.
_TENSIONS: dict[str, tuple[dict, ...]] = {
    "western": (
        tension("crown-vs-lords", "the crown against the great lords",
                factions=("crown", "great-lords")),
        tension("crown-vs-guilds", "the crown against the guilds' money",
                factions=("crown", "guilds")),
        tension("temple-vs-crown",
                "the bishops: temple against crown",
                factions=("crown", "temple", "militant-order")),
        tension("old-vs-new", "old blood against the new men",
                factions=("great-lords", "new-men")),
        tension("manor-vs-village", "the bailiff against the old custom",
                factions=("manor-lord", "village")),
        tension("shrine-vs-shrine", "two shrines, one saint, one road",
                factions=("shrines", "rival-shrines")),
        tension("abbey-vs-village", "the abbey against the families",
                factions=("abbey", "village")),
    ),
    "southern": (
        tension("sword-vs-robe", "old swords against bought offices",
                factions=("sword", "robe")),
        tension("crown-vs-faith", "the crown against the old faith",
                factions=("crown", "tribunal", "hidden-faith")),
        tension("court-vs-provinces",
                "the court against the provinces",
                factions=("commissioners", "provinces")),
        tension("academy-vs-tribunal",
                "the academy against the tribunal",
                factions=("academy", "tribunal")),
    ),
    "tergal": (
        tension("clan-vs-clan", "clan against clan over the pasture",
                factions=("clans", "rival-clans")),
        tension("chiefs-vs-mothers",
                "the chiefs against the clan mothers",
                factions=("clans", "clan-mothers")),
        tension("council-vs-outlaws",
                "the council against the outlaws",
                factions=("clans", "outlaws")),
        tension("white-vs-black",
                "the white shamans against the dark one",
                factions=("white-shamans", "black-shaman")),
    ),
    "norse": (
        tension("jarls-vs-thing", "the jarls against the assembly",
                factions=("jarls", "freeholders")),
        tension("sea-vs-land", "the sea-kings against the land-chiefs",
                factions=("sea-kings", "land-chiefs")),
        tension("old-vs-new-gods",
                "the old gods against the missionaries",
                factions=("grove-priests", "missionaries")),
        tension("feud", "two houses are counting their dead",
                factions=("feud-house", "rival-house")),
    ),
    # The land-specific rows (2026-08-22, the card audit). `_by_land` is
    # additive, so these stand BESIDE the culture's own list. The pendulum
    # calendar is the southern HEIR's, not the whole south's: Byzantium
    # keeps the death-face, the carnival and the penitents, and Andalusia
    # and Umaia share only the culture-generic south.
    "byzantium": (
        tension("penitents-vs-carnival",
                "which face of the god rules the year",
                factions=("penitents", "carnival")),
    ),
}
# The tensions that are NOT colour: held on top of the roll and never in the
# rollable pool. The western manor is the econ packet's oppression axis and
# is simply what the land is.
_STANDING_TENSIONS: dict[str, tuple[str, ...]] = {
    "western": ("manor-vs-village",),
}

# The authored tables are keyed by CULTURE (or by a single land where the
# content is that land's own); every reader asks with a LAND key.
CONSTITUTIONS = _by_land(_CONSTITUTIONS)
TENSIONS = _by_land(_TENSIONS)
STANDING_TENSIONS = _by_land(_STANDING_TENSIONS)

# The wiring: directed verb edges between blocs. The formalism has to serve
# a royal council, a clan confederacy and a manor alike, so the verb is a
# word and nothing reads it but a card.
FACTION_EDGES: tuple[dict, ...] = (
    # the western culture
    edge("western", "crown", "leans-on", "great-lords",
         "the crown leans on the great lords"),
    edge("western", "great-lords", "defy", "crown",
         "the great lords defy the crown"),
    edge("western", "guilds", "buy", "crown",
         "the guilds buy their charters from the crown"),
    edge("western", "temple", "excommunicates", "crown",
         "the temple threatens the crown with the interdict"),
    edge("western", "militant-order", "answers", "temple",
         "the militant order answers only to the temple"),
    edge("western", "new-men", "outbid", "great-lords",
         "the new men outbid the great lords for everything"),
    edge("western", "manor-lord", "squeezes", "village",
         "the bailiff squeezes the village"),
    edge("western", "village", "slows", "manor-lord",
         "the village works to the letter of the old custom"),
    # the southern culture
    edge("southern", "robe", "buy", "sword",
         "the robe nobility buys the sword's land out from under it"),
    edge("southern", "sword", "snub", "robe",
         "the sword nobility will not be seated beside the robe"),
    edge("southern", "tribunal", "hunts", "hidden-faith",
         "the tribunal hunts the hidden faith"),
    edge("southern", "commissioners", "overrule", "provinces",
         "the king's commissioners overrule the provincial courts"),
    edge("southern", "provinces", "resist", "commissioners",
         "the provinces answer the commissioners with closed gates"),
    # Tergal
    edge("tergal", "clans", "feud", "rival-clans",
         "the clans are in feud with each other"),
    edge("tergal", "clan-mothers", "seat", "clans",
         "the clan mothers seat the chiefs, and unseat them"),
    edge("tergal", "clans", "outlaw", "outlaws",
         "the council declares its outlaws killable"),
    edge("tergal", "outlaws", "raid", "clans",
         "the outlaw bands raid the clans that cast them out"),
    # -- religion and magic (2026-08-11) ---------------------------------- #
    edge("western", "shrines", "steal-from", "rival-shrines",
         "the shrine towns steal each other's relics outright"),
    edge("western", "rival-shrines", "undercut", "shrines",
         "the rival shrines undercut each other for the pilgrim trade"),
    edge("western", "abbey", "holds", "village",
         "the abbey holds the village's children, land and law"),
    edge("western", "village", "petitions", "abbey",
         "the village petitions the abbey and is answered in writing"),
    edge("byzantium", "penitents", "denounce", "carnival",
         "the penitent wing preaches against the carnival wing"),
    edge("byzantium", "carnival", "outnumber", "penitents",
         "the carnival wing simply outnumbers the penitents"),
    edge("southern", "tribunal", "watches", "academy",
         "the tribunal keeps a list of what the academy teaches"),
    edge("southern", "academy", "shelters", "tribunal",
         "the academy hands the tribunal a scapegoat every few years"),
    edge("tergal", "white-shamans", "shun", "black-shaman",
         "the white shamans camp the dark one outside the ring"),
    edge("tergal", "black-shaman", "serves", "white-shamans",
         "the dark one does the work the white shamans will not"),
    # -- Thule (2026-08-22, the norse packet): six edges over its four
    # tensions, so every axis the land can roll has a quarrel with a verb
    # in it and a card standing in the quarrel.
    edge("norse", "jarls", "pack", "freeholders",
         "the jarls bring their crews to the assembly and vote them"),
    edge("norse", "freeholders", "outlaw", "jarls",
         "the assembly has outlawed a jarl and means it"),
    edge("norse", "sea-kings", "tax", "land-chiefs",
         "the sea-kings take a share of every catch and cargo"),
    edge("norse", "land-chiefs", "withhold", "sea-kings",
         "the land-chiefs keep their crews ashore for the harvest"),
    edge("norse", "grove-priests", "curse", "missionaries",
         "the grove priests have a pole up with a priest's name on it"),
    edge("norse", "feud-house", "kill", "rival-house",
         "the two houses are six men in and still counting"),
)


# --------------------------------------------------------------------------- #
# The sky: the season calendar and the day roll (2026-08-08, the weather
# session; rebuilt 2026-08-21 onto climate and season)
# --------------------------------------------------------------------------- #
# Weather is a day-scale state with outlet effects: the cheapest world content
# there is, land-agnostic, and the only one that touches the party every day
# it is out of doors. The vocabulary is nine words shared by every land; what
# differs is the WEIGHTS, and since the ground session those come from two
# places -- the CLIMATE of the tile the party is standing on, and the SEASON
# of the year.
#
# A CALENDAR, NOT A TRACK. Day 1 of the campaign is April 1st. Nothing ticks,
# nothing is stored and nothing else in the game reads the season: it is a
# lookup that says which column of the weather table today uses. Autumn
# reuses spring's column -- the same cool wet middle -- so the table carries
# three. Winter is 150 days long and is not played time (the campaign year is
# spring to autumn); it exists here so that a long absence rolls a plausible
# sky and so the snapshot arc has a calendar to hang a winter on.

YEAR_DAYS = 360
SEASONS = (("spring", 60), ("summer", 90), ("autumn", 60), ("winter", 150))
SEASON_COLUMN = {"spring": "spring", "autumn": "spring",
                 "summer": "summer", "winter": "winter"}


def season_of(day: int) -> str:
    """Which season day `day` of the campaign falls in. Day 1 is April 1st
    and the year wraps at 360, so day 361 is spring again."""
    left = (day - 1) % YEAR_DAYS + 1
    for name, length in SEASONS:
        if left <= length:
            return name
        left -= length
    raise ValueError(f"the calendar does not cover day {day}")


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
WEATHER_ORDER = ("clear", "cloud", "wind", "rain", "storm", "fog", "frost",
                 "snow", "heat")
# Per climate, per season, per hundred days, in WEATHER_ORDER. Every row
# sums to 100 by contract (`validate_content` checks it at import), so a row
# can be read as a percentage and edited as one. The nile shares the
# desert's sky -- its granary is the river, not the rain.
_SKY = {
    "oceanic": ((20, 26, 12, 26, 4, 8, 4, 0, 0),
                (30, 24, 10, 24, 6, 4, 0, 0, 2),
                (12, 30, 16, 24, 6, 6, 5, 1, 0)),
    "continental": ((26, 22, 12, 20, 5, 5, 8, 2, 0),
                    (34, 16, 8, 18, 10, 2, 0, 0, 12),
                    (16, 22, 10, 4, 2, 6, 22, 18, 0)),
    "taiga": ((18, 24, 10, 16, 3, 10, 12, 7, 0),
              (28, 22, 8, 22, 5, 8, 4, 0, 3),
              (14, 20, 10, 0, 2, 6, 26, 22, 0)),
    "tundra": ((16, 20, 22, 6, 4, 8, 14, 10, 0),
               (22, 22, 16, 14, 4, 10, 8, 4, 0),
               (12, 16, 22, 0, 6, 4, 20, 20, 0)),
    "alpine": ((18, 20, 18, 12, 6, 8, 10, 8, 0),
               (26, 18, 14, 16, 10, 6, 6, 4, 0),
               (14, 16, 16, 0, 6, 6, 20, 22, 0)),
    "mediterranean": ((34, 14, 14, 18, 4, 4, 2, 0, 10),
                      (48, 8, 12, 4, 4, 2, 0, 0, 22),
                      (24, 20, 14, 30, 6, 4, 2, 0, 0)),
    "wet_mediterranean": ((32, 14, 12, 24, 4, 4, 0, 0, 10),
                          (42, 10, 10, 12, 6, 2, 0, 0, 18),
                          (26, 18, 12, 32, 6, 4, 0, 0, 2)),
    "steppe": ((28, 12, 24, 14, 6, 2, 10, 4, 0),
               (38, 8, 20, 8, 8, 0, 0, 0, 18),
               (18, 14, 22, 2, 4, 2, 22, 16, 0)),
    "desert": ((52, 6, 18, 4, 2, 2, 2, 0, 14),
               (50, 2, 14, 0, 2, 0, 0, 0, 32),
               (50, 10, 16, 6, 2, 4, 8, 0, 4)),
}
_SKY["nile"] = _SKY["desert"]
CLIMATE_WEATHER = {
    climate: {column: dict(zip(WEATHER_ORDER, row))
              for column, row in zip(("spring", "summer", "winter"), rows)}
    for climate, rows in _SKY.items()
}
# The same word reads differently on different ground. Display only -- never
# a second vocabulary. Keyed by CLIMATE, with one TERRAIN key: the fen's fog
# is the one place where relief and not the sky picks the words, and it
# beats the climate line when both have something to say.
WEATHER_LOCAL = {
    "alpine": {"storm": "a snowstorm", "rain": "sleet",
               "cloud": "low cloud"},
    "taiga": {"rain": "cold rain"},
    "tundra": {"rain": "cold rain"},
    "mediterranean": {"cloud": "haze", "wind": "the sea wind"},
    "wet_mediterranean": {"cloud": "haze", "wind": "the sea wind"},
    "steppe": {"wind": "a wind with no cover from it"},
    "desert": {"storm": "a dust storm", "wind": "a dry wind"},
    "nile": {"storm": "a dust storm", "wind": "a dry wind"},
    "marsh": {"fog": "fen fog"},
}
WEATHER_LOCAL_TERRAINS = ("marsh",)
# What the sky COSTS a party out in it: exposure (the STR check that gives
# colds -- rpg.py's disease family) and the storm's field penalties.
EXPOSURE_WEATHER = ("rain", "storm", "frost", "snow")
STORM_WEATHER = ("storm",)      # ...and the sky that drags a shot and trips
                                # a step (rpg.STORM_SHOT_PENALTY / _SLIP_DC)


def sky_tile(world: dict, polity: str) -> dict:
    """The GROUND this land's sky is read off today.

    The party's own tile when the party is in that land -- so a march from
    the Danube into the steppe changes what the sky can do that afternoon --
    and the land's capital otherwise, because the other two realms still
    have weather while nobody is watching. The open sea has no ground to
    read, so a party at sea reads the capital too."""
    tile = world["tiles"][world["party_tile"]]
    if tile["country"] == polity and tile["climate"] is not None:
        return tile
    return world["tiles"][CAPITAL_TILES[polity]]


def weather_phrase(climate: str, word: str,
                   terrain: str | None = None) -> str:
    """What this ground calls that sky."""
    if terrain is not None and word in WEATHER_LOCAL.get(terrain, {}):
        return WEATHER_LOCAL[terrain][word]
    return WEATHER_LOCAL.get(climate, {}).get(
        word, WEATHER_WORDS.get(word, word))


def sky_phrase(world: dict, polity: str, word: str) -> str:
    """...for the ground this land's sky is being read off right now."""
    tile = sky_tile(world, polity)
    return weather_phrase(tile["climate"], word, tile["terrain"])


def weather_weights(world: dict, polity: str, day: int) -> dict[str, float]:
    """The distribution today's sky is rolled from: the ground's climate,
    the season, and whatever season-scale state the land is holding. A
    drought is the state that made itself -- it cuts the rain and storm
    weights to DROUGHT_WET_MULT and lifts the dry ones, which is why
    droughts last past the day that started them."""
    climate = sky_tile(world, polity)["climate"]
    base = CLIMATE_WEATHER[climate][SEASON_COLUMN[season_of(day)]]
    weights = {word: float(w) for word, w in base.items() if w}
    if "drought" in state_ids(world, polity):
        for word in weights:
            if word in ("rain", "storm", "snow"):
                weights[word] *= DROUGHT_WET_MULT
            elif word in ("clear", "heat"):
                weights[word] *= DROUGHT_DRY_BONUS
    return weights


def drought_days(world: dict, polity: str) -> int:
    """How many rainless days THIS ground calls a drought."""
    return CLIMATE_PROFILES[sky_tile(world, polity)["climate"]][
        "drought_days"]


def roll_weather(world: dict, polity: str, day: int,
                 rng: random.Random) -> str:
    """One day's sky for one land. The weights are the die -- there is no
    separate chance anywhere in the weather track."""
    weights = weather_weights(world, polity, day)
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
    line = f"WEATHER: {sky_phrase(world, polity, word)}"
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
        homeland = polity
        first = pick_name(rng, homeland, rng.choice(("m", "f")))
        who = {"name": f"{first} {rng.choice(NECROMANCER_EPITHETS)}",
               "level": rng.randint(*NECROMANCER_LEVELS),
               "since": day}
        layer["necromancer"] = who
    return {"necromancer": who["name"]}


# --- the lesser named authorities a politics card creates ------------------ #
# The same trick, generalized (2026-08-10): a card that has to name somebody
# names him ONCE and the land keeps him, so the banned lord is still the same
# banned lord the next time the ban comes round. He draws TWO words off the
# crown-less pool (`rulers.py`), so the sheriff and the king come off one
# vocabulary and the DM has something to play the moment the news says his
# name.

def named_authority(world: dict, polity: str, key: str) -> dict | None:
    """A lesser named authority a card put on this land, if it has one."""
    return land_layer(world, polity).get("authorities", {}).get(key)


def _authority_hook(key: str, role: str, field: str = "who"):
    def hook(world: dict, polity: str, day: int,
             rng: random.Random) -> dict:
        from people import pick_name         # lazy: quests imports worldsim
        layer = land_layer(world, polity)
        who = layer.setdefault("authorities", {}).get(key)
        if who is None:
            homeland = polity
            sheet = rulers.roll_ruler(rng, crown=False)
            sheet.update(name=pick_name(rng, homeland,
                                        rng.choice(("m", "f"))),
                         role=role, since=day)
            layer["authorities"][key] = who = sheet
        return {field: who["name"]}
    return hook


# --------------------------------------------------------------------------- #
# The economy content: five or six cards a land (worldsim.md's econ packets)
# --------------------------------------------------------------------------- #
# The asymmetry doctrine's floor, reached by the economy floor session: every
# land has five or six crisis cards, at least one CHAIN running through them,
# and one FLAVOR ANCHOR that is not trouble at all (the fair, the fleet, the
# art market, the new seam, the gadget fair, the great drive) -- because a
# world where the only thing that ever happens is a disaster reads as a
# disaster, not as a world. Cards WAITING under plan.md's rulings (the robot
# servants, the sulfur trade) are not here.
#
# The pools a card's own posted work draws from are catalog rows like every
# other roster in the game. A pool's spread is also its LEVEL BAND
# (quests.template_band), so these run wide on purpose: a card's job has to
# be postable in a village and in a capital. Since the human contraction the
# pools differ by what the work ARMS, not by who the people are -- the three
# per-people rosters the world used to keep are gone.

_TOUGHS = ("cutthroat", "archer", "bruiser", "soldier", "veteran",
           "champion")                                      # band 1-12
_GUNHANDS = ("cutthroat", "gunner", "bruiser", "soldier", "veteran",
             "champion")                                    # band 1-12
_BEASTS = ("wolf", "dire wolf", "bear")                     # band 1-6
# The religion & magic rung's two additions (2026-08-11). Neither is a new
# creature ROW -- the monsters & fauna dump still owns that -- they are two
# named pools over the catalog the game already has, and the cultural arms
# rule has nothing to say about either: the dead and the gifted are not
# anybody's soldiery.
_UNDEAD = ("skeleton", "ghoul", "wight")                    # band 1-10
_CASTERS = ("hexer", "pyromancer", "magus")                 # band 2-12

CARDS = (
    # -- the west: MANORIAL OPPRESSION & THE CROWN'S DEBTS ---------------- #
    # The famine CHAIN: the harvest fails, and the dear bread it leaves
    # behind is what the riot admits on a season later.
    card("western/bad-harvest", "The harvest fails", "western",
         wealth=("crisis", "normal"), without=("bread-dear",),
         days=(35, 50),
         news="The harvest has failed here. Bread is short and the "
              "granaries are watched.",
         state={"while": ("harvest-failed",), "set": ("bread-dear",),
                "wealth_while": "crisis"},
         quest={"post": job(
             "The Grain Road",
             "A grain train is coming up from the south and the road is "
             "watched. Ride with it and see that it reaches the granary.",
             pool=_TOUGHS, sites=("the grain road", "the burnt wagon yard"),
             giver="the sheriff",
             epilogue="The grain is in the granary. The town eats this "
                      "week.",
             failure_epilogue="The grain train was taken on the road. The "
                              "granary stands empty and the queue outside "
                              "it is longer every morning."),
             "pay": 1.25}),
    card("western/bread-revolt", "The bread riot", "western",
         states=("bread-dear",), days=(10, 18),
         news="Bread went up again and the market went over with it. The "
              "stalls are wrecked, the sheriff has lost the square, and "
              "the grain merchants want their doors held tonight.",
         state={"clear": ("bread-dear",), "while": ("bread-riots",)},
         menu={"goods": 1.30},
         quest={"post": job(
             "The Warehouse Door",
             "A grain merchant wants his warehouse held until the square "
             "quiets. The crowd outside it has not eaten in three days.",
             pool=_TOUGHS, sites=("the grain warehouse",),
             giver="the grain merchant",
             epilogue="The warehouse held. The merchant pays and does not "
                      "ask what it cost the square.",
             failure_epilogue="The warehouse doors went in. The grain was "
                              "carried off down every lane in the town."),
             "pay": 1.30}),
    card("western/tolls", "The tolls are doubled", "western",
         wealth=("crisis", "normal"), days=(12, 20),
         news="The baron has doubled the road tolls. His toll-men hold the "
              "bridges, and nobody in town will say a word against them.",
         state={"while": ("toll-squeeze",)},
         menu={"toll": 2.0, "goods": 1.15},
         encounter={"kinds": ("cutthroat", "bruiser", "soldier"),
                    "where": "road", "as": "the baron's toll-men",
                    "skins": {"cutthroat": "Toll-Man",
                              "bruiser": "Toll-Bruiser",
                              "soldier": "Toll-Sergeant"},
                    "chance": 0.50}),
    card("western/war-debts", "The crown calls in its debts", "western",
         wealth=("crisis",), without=("harvest-failed",), days=(20, 30),
         news="The crown wants its war paid for. The tax men are out with "
              "the sheriff behind them.",
         state={"while": ("overtaxed",)},
         quest={"reprice": 0.85}),
    card("western/monopoly", "The lord shuts the hand-mills", "western",
         wealth=("crisis", "normal"), days=(20, 35),
         news="The lord has shut every hand-mill in the valley. Grind at "
              "his mill and pay his share, or answer to his bailiff for "
              "the flour in your house.",
         state={"while": ("monopoly-squeeze",)},
         menu={"goods": 1.20},
         quest={"post": job(
             "The Bailiff's Round",
             "The bailiff turns out the houses that still have a quern in "
             "them, and he wants swords walking with him. The village "
             "wants him stopped. Both sides are paying.",
             pool=_TOUGHS, sites=("the lord's mill", "the village lane"),
             giver="the lord's bailiff",
             epilogue="The round is finished. The querns are broken and "
                      "the mill has the valley's grinding again.",
             failure_epilogue="The bailiff was beaten out of the village. "
                              "The lord is hiring harder men."),
             "pay": 1.10}),
    # The flavor anchor: not trouble, and the one week of the year the
    # shelves are cheap and the beds are not.
    card("western/fair", "The great fair", "western",
         wealth=("normal", "prosperous"), days=(8, 14),
         news="The great fair is open on the water-meadow. Every trader in "
              "the land is here, so is every cutpurse, and the fair court "
              "hangs its verdicts the same day it hears them.",
         state={"while": ("fair-on",)},
         menu={"goods": 0.80, "steel": 0.85, "lodging": 1.60},
         quest={"post": job(
             "The Fair Court",
             "The fair court has more thieves in the crowd than it has men "
             "to take them. It pays by the head, and it wants them alive "
             "if that is convenient.",
             pool=_TOUGHS, sites=("the fair ground",),
             giver="the fair court's clerk",
             epilogue="The court has its thieves and the fair closes "
                      "quiet. The clerk pays out of the fine box.",
             failure_epilogue="The fair closed early. Half the traders "
                              "were robbed and the court hanged nobody."),
             "slots": 1}),

    # -- the south: FINANCE & THE ABSOLUTIST STATE ------------------------ #
    card("southern/tax-farmer", "The tax farmer buys the province",
         "southern", wealth=("crisis",), without=("tax-farmed",),
         days=(20, 35),
         news="The state has sold the right to squeeze this province. The "
              "tax farmer means to make his money back.",
         state={"set": ("tax-farmed",)},
         menu={"toll": 1.50},
         quest={"post": job(
             "The Tax Farmer's Column",
             "The tax farmer's men go out to the villages on Tuesday and "
             "the villages know it. He wants swords beside the strongbox.",
             pool=_TOUGHS, sites=("the tax road",),
             giver="the tax farmer",
             epilogue="The strongbox came back full. Three villages are "
                      "eating less this month.",
             failure_epilogue="The column was ambushed and the strongbox "
                              "is gone. The tax farmer has doubled the "
                              "demand to cover it."),
             "pay": 1.20}),
    # The forgery CHAIN: the bank fails, and the forgers who moved in
    # while nobody could tell one note from another are the next card.
    card("southern/bank-run", "The bank fails", "southern",
         wealth=("crisis",), without=("bad-paper",), days=(15, 25),
         news="The bank has shut its doors. Paper money buys nothing now, and "
              "every strongbox in the city is watched.",
         state={"while": ("paper-worthless",), "set": ("bad-paper",)},
         menu={"lodging": 1.20},
         quest={"post": job(
             "The Strongbox Walk",
             "A house that still has metal wants it moved across the city "
             "tonight, and does not want a coach doing it.",
             pool=_TOUGHS, sites=("the night street", "the counting house"),
             giver="the banker's agent",
             epilogue="The metal is in the new vault. Nobody saw it move.",
             failure_epilogue="The strongbox never reached the vault. The "
                              "house has stopped paying anybody."),
             "pay": 1.35}),
    card("southern/counterfeit", "The forged notes", "southern",
         states=("bad-paper",), days=(15, 25),
         news="Half the notes in the market are forged and nobody can tell "
              "which half. The state has sent note-hunters, and they are "
              "paid by the arrest.",
         state={"clear": ("bad-paper",), "while": ("note-hunt",)},
         menu={"goods": 1.20},
         quest={"post": job(
             "The Cellar Press",
             "The note-hunters have found the press. It is in a cellar "
             "with armed men in front of it.",
             pool=_TOUGHS, sites=("the cellar press",),
             giver="the state note-hunter",
             epilogue="The press is broken and the plates are in the "
                      "state's hands. The notes in the purse are worth a "
                      "little more this morning.",
             failure_epilogue="The press moved in the night. The forgers "
                              "know who came looking for them."),
             "pay": 1.15}),
    # The one quest shape no other land can offer -- a pure REPRICE card:
    # it puts nothing on the board and changes what everything on it pays.
    card("southern/paid-in-paper", "Paid in paper", "southern",
         wealth=("normal", "prosperous"), without=("paper-worthless",),
         days=(15, 25),
         news="The province is paying its hired swords in notes this "
              "season. Twice the number on the page -- and the page is "
              "worth face value at a bank counter and nowhere else.",
         state={"while": ("paper-pay",)},
         quest={"reprice": 1.50}),
    card("southern/colony-fleet", "The colony fleet comes in",
         "southern", wealth=("normal", "prosperous"), days=(10, 18),
         news="The colony fleet is in. There is gold on the wharves, the "
              "taverns are full, and every purse in the city is fat.",
         state={"while": ("coin-flush",)},
         quest={"slots": 1, "reprice": 1.20}),

    # -- Tergal: PASTURE & OBLIGATION --------------------------------------- #
    # The raid CHAIN: the herds die, the dead pasture outlives the dying,
    # and a clan with no grass and no herd goes where the grain is.
    card("tergal/herd-fails", "The herds are dying", "tergal",
         wealth=("crisis",), without=("grass-gone",), days=(25, 40),
         news="The grass is gone and the herds are dying with it. A tribe "
              "with no herd has nothing to lose and knows where the fat "
              "lands are.",
         state={"while": ("herd-loss",), "set": ("grass-gone",)}),
    card("tergal/raid", "The clans ride", "tergal",
         states=("grass-gone",), days=(20, 30),
         news="The clans that lost their herds have gone over the border "
              "to where the grain is. Nobody here is stopping them and "
              "nobody here is apologizing for them.",
         state={"clear": ("grass-gone",), "while": ("raiding",)},
         quest={"post": job(
             "The Empty Camp",
             "A clan that stayed behind is down to its last mares and the "
             "riders who took the rest are camped two days out.",
             pool=_TOUGHS, sites=("the raiders' camp",),
             giver="the clan's old chief",
             epilogue="The camp is broken and what was left of the horses "
                      "is back. The old chief gives you the pick of them.",
             failure_epilogue="The clan has nothing left on four legs. "
                              "Those who could ride have joined the "
                              "raiders."),
             "pay": 1.25}),
    card("tergal/returned-mercenary", "The mercenary comes home", "tergal",
         days=(15, 25),
         news="A mercenary is back from the southern wars rich and hardened, "
              "with foreign steel and a following. The old order does not "
              "suit him.",
         state={"while": ("mercenary-home",)},
         menu={"steel": 0.85}),
    card("tergal/tribute", "The tribute", "tergal",
         wealth=("crisis", "normal"), days=(20, 35),
         news="A southern crown is paying a chief not to ride. The chief "
              "is spending it on men, and the men are being spent on the "
              "other clans.",
         state={"while": ("tribute-taken",)},
         menu={"goods": 1.15},
         quest={"post": job(
             "The Chief's New Men",
             "A clan that will not kneel to the paid chief wants the men "
             "he sent kept off its grazing. It pays in horses, and it says "
             "so in front of witnesses.",
             pool=_TOUGHS, sites=("the disputed grazing",),
             giver="the clan's spear-woman",
             epilogue="The paid chief's men are off that grass. The clan "
                      "pays in horses in front of the whole camp.",
             failure_epilogue="The grazing is the paid chief's now. The "
                              "clan that hired you has moved south with "
                              "what it could drive."),
             "pay": 1.20}),
    # The flavor anchor.
    card("tergal/herd-drive", "The great drive", "tergal",
         wealth=("normal", "prosperous"), days=(10, 18),
         news="The great drive is on. Every horse and buffalo in the land "
              "is moving north, and the fords are the dangerous part.",
         state={"while": ("herd-drive",)},
         menu={"goods": 0.90},
         quest={"post": job(
             "The Ford Crossing",
             "The drive crosses at the ford on the fourth day. Rustlers "
             "work the crossings, and the herd is at its most scattered "
             "there.",
             pool=_TOUGHS, sites=("the crossing camp",),
             giver="the drive's trail boss",
             epilogue="The herd is over the ford and counted. The trail "
                      "boss is short a dozen head and calls that a good "
                      "crossing.",
             failure_epilogue="The drive scattered at the ford. Half the "
                              "herd is loose on the plain and the "
                              "rustlers are still working."),
             "slots": 1}),

    # -- Thule: THE SEA IS THE ECONOMY -------------------------------------- #
    # (2026-08-22, the norse packet.) Six cards on what the year is here:
    # the ships go out, the fish come in, the whale comes ashore, the ice
    # shuts the door, the wolves come down, and a foreign crown pays for
    # quiet. The politics, the grove and the seer are in the other packets.
    card("norse/raid-season", "The ships go out", "norse",
         wealth=("crisis", "normal"), without=("ice-locked",),
         days=(25, 40),
         news="The ships have gone out. Half the young men of every fjord "
              "are aboard them, the fields are being worked by whoever is "
              "left, and nobody here calls it robbery.",
         state={"while": ("raiding",)},
         menu={"steel": 0.90},
         quest={"post": job(
             "Short A Crew",
             "A shipmaster is four oars short and sails on the tide. The "
             "men he was promised took another ship's silver, and he "
             "wants them off that deck before it leaves.",
             pool=_TOUGHS, sites=("the boat strand",),
             giver="the shipmaster",
             epilogue="The four are back on the right deck and the ship "
                      "went out on the tide. The shipmaster pays in "
                      "hacksilver, weighed in front of you.",
             failure_epilogue="The ship went out four oars short. The "
                              "shipmaster said what he thought of that "
                              "on the strand, in front of the whole "
                              "harbor."),
             "pay": 1.20}),
    card("norse/herring-run", "The herring run", "norse",
         wealth=("normal", "prosperous"), days=(10, 18),
         news="The herring are running in the sound. Every boat that "
              "floats is out, the salt is going up, and the barrels are "
              "being nailed together on the beach.",
         state={"while": ("herring-run",)},
         menu={"goods": 0.90, "lodging": 1.15},
         quest={"post": job(
             "The Salt Boat",
             "The salt boat is three days late and the catch is on the "
             "beach going bad. It is beached in the next fjord and the "
             "men who beached it want paying twice.",
             pool=_TOUGHS, sites=("the next fjord",),
             giver="the curing-house woman",
             epilogue="The salt came round the headland in time and the "
                      "catch is in the barrels. The curing-house pays "
                      "and throws in as much fish as you can carry.",
             failure_epilogue="The catch went bad on the beach. A "
                              "season's fish is being carted onto the "
                              "fields as manure."),
             "slots": 1}),
    card("norse/whale-ashore", "A whale is ashore", "norse",
         days=(8, 14),
         news="A whale has come ashore below the headland. That is a "
              "winter's meat and oil, and three districts are already "
              "arguing about whose beach it died on.",
         state={"while": ("whale-ashore",)},
         menu={"goods": 0.85},
         quest={"post": job(
             "Whose Beach It Died On",
             "One district has started cutting and another is walking "
             "over the headland to stop it. The law-speaker wants the "
             "cutting finished and nobody killed over it.",
             pool=_TOUGHS, sites=("the whale beach",),
             giver="the district's law-speaker",
             epilogue="The whale is cut up and the shares are counted "
                      "out. Two men have broken hands and nobody is "
                      "dead, which the law-speaker calls a good day.",
             failure_epilogue="Two men are dead on the beach over a "
                              "whale, and the districts have started "
                              "counting that instead."),
             "pay": 1.15}),
    card("norse/ice-locked", "The harbors freeze shut", "norse",
         wealth=("crisis", "normal"), without=("raiding",), days=(30, 50),
         news="The harbors have frozen shut. Nothing comes in and nothing "
              "goes out until the thaw, and every household is counting "
              "what is in the store-loft against the weeks left.",
         state={"while": ("ice-locked",)}),
    card("norse/wolf-winter", "The wolf winter", "norse",
         wealth=("crisis",), days=(25, 40),
         news="The fodder is gone before the winter is. The byres are "
              "half empty of cattle and the wolves have worked out which "
              "farms cannot keep a watch all night.",
         state={"while": ("wolf-winter",)},
         menu={"goods": 1.20},
         quest={"post": job(
             "The Watch At The Byre",
             "A farm has lost six beasts in four nights and has nobody "
             "left to sit up with the rest. The pack comes down the same "
             "gully every time.",
             pool=_BEASTS, sites=("the byre gully",),
             giver="the farm's widow",
             epilogue="The pack is broken and the rest of the cattle are "
                      "alive. The widow pays in hides and winter food.",
             failure_epilogue="The byre is empty. The farm's people have "
                              "gone down to the harbor to be fed by "
                              "somebody else."),
             "pay": 1.25}),
    card("norse/danegeld", "The danegeld", "norse",
         wealth=("crisis", "normal"), days=(25, 40),
         news="A foreign crown is paying the fleet to stay home this "
              "year. The silver is landed and weighed, the sea-king is "
              "spending it on men, and the men have to be used on "
              "somebody.",
         state={"while": ("tribute-taken",)},
         menu={"goods": 1.15},
         quest={"post": job(
             "The Weighed Silver",
             "A share of the paid silver has to go up the fjord to the "
             "jarl who was promised it, and the crews that were promised "
             "a raid instead know which day it travels.",
             pool=_TOUGHS, sites=("the fjord road",),
             giver="the sea-king's steward",
             epilogue="The silver reached the jarl's hall and was "
                      "weighed in front of witnesses. The steward pays "
                      "out of the same chest.",
             failure_epilogue="The silver never reached the hall. The "
                              "jarl has told the strand he was cheated, "
                              "and half the coast believes him."),
             "pay": 1.20}),

    # -- THE MINERS' LEAGUE: EXTRACTION & THE CLAIMS ------------------------ #
    # (2026-08-21, the tile economy arc's session 4.) Recovered from the
    # catalog the human contraction cut and re-homed onto ANY_LAND: the
    # trade session put nine mines on the map and every country holds some,
    # so the extraction story is every land's. What was scrubbed was four
    # words, not a design -- the clans became the MINERS' LEAGUE and its
    # chapter masters, the under-thane the League steward, the clan books
    # the League's books, and the dwarf who found a way an old engineer.
    # The claim-keeper, the company shop, the winding gear and the pit
    # bosses stayed: they were period human mining language all along.
    #
    # The rush CHAIN: the seam is found (a slot, so it outlives the card),
    # and the bust that follows admits on it, puts the slot back, and
    # settles the argument the find started.
    card("mining/new-seam", "A new seam is found", ANY_LAND,
         wealth=("normal", "prosperous"), without=("claims-collide",),
         days=(15, 25),
         news="A new seam has been found in the hills. Two League "
              "chapters claim it and a third is strong enough to work it.",
         state={"slot": {"deposit": "deposit-found"},
                "set": ("claims-collide",), "wealth_while": "prosperous"},
         quest={"post": job(
             "Two Chapters, One Seam",
             "The chapter that found the seam wants the shaft head held "
             "while the claim is argued. The chapter that owns the rock "
             "has men walking up there tonight.",
             pool=_TOUGHS, sites=("the new shaft head",),
             giver="the chapter's claim-keeper",
             epilogue="The shaft head held through the argument. The "
                      "claim went to whoever was standing on it.",
             failure_epilogue="The shaft head changed hands twice and the "
                              "claim went to the chapter with the most "
                              "men."),
             "pay": 1.20}),
    card("mining/gold-rush", "The rush and the bust", ANY_LAND,
         states=("deposit-found",), days=(12, 20),
         news="Everyone who could walk came up for the new seam, and it is "
              "already thinning. The town has four times the people it can "
              "feed and half of them have nothing left to dig.",
         state={"slot": {"deposit": "deposit-normal"},
                "clear": ("claims-collide",), "while": ("rush-on",)},
         menu={"goods": 1.40, "lodging": 2.00},
         encounter={"kinds": ("cutthroat", "bruiser"), "where": "wilds",
                    "as": "claim-jumpers off the new workings",
                    "skins": {"cutthroat": "Claim-Jumper",
                              "bruiser": "Pit Boss"},
                    "chance": 0.40},
         quest={"post": job(
             "The Jumped Claim",
             "A digger who paid for his claim cannot get back onto it. The "
             "men on it now have been there a week and are not arguing "
             "about paper.",
             pool=_TOUGHS, sites=("the jumped workings",),
             giver="the ruined digger",
             epilogue="The claim is back in the digger's hands. It is "
                      "worth about a third of what he paid for it.",
             failure_epilogue="The digger has left the hills with "
                              "nothing. The men on his claim are still "
                              "there."),
             "pay": 1.15}),
    # The bust CHAIN: the vein runs out and the land goes to crisis, and
    # only the reopening takes it back out.
    card("mining/vein-dries", "The vein runs out", ANY_LAND,
         wealth=("normal", "prosperous"), days=None,
         news="The vein that fed the district is running out. The League's "
              "books say otherwise, and the League's books are the law.",
         state={"slot": {"deposit": "deposit-drying"}, "wealth": "crisis"}),
    card("mining/veins-reopened", "The dead veins are reopened", ANY_LAND,
         wealth=("crisis",), states=("deposit-drying",), days=None,
         news="An old engineer has found a way to work a seam everyone had "
              "written off. Every chapter with a dead pit wants him, and "
              "one of them wants him quiet.",
         state={"slot": {"deposit": "deposit-normal"}, "wealth": "normal"}),
    card("mining/strike", "The pits stand idle", ANY_LAND,
         wealth=("crisis",), days=(12, 20),
         news="The pits stand idle. The workers want their share of the "
              "new find before the League books it, and the company shop "
              "has stopped giving credit.",
         state={"while": ("strike",)},
         quest={"post": job(
             "The Company Shop",
             "The League wants the company shop and the winding gear held "
             "while it waits the strike out. The men at the gate are the "
             "same men who dug the pit.",
             pool=_TOUGHS, sites=("the pit gate",),
             giver="the League steward",
             epilogue="The gear is intact and the shop opened again on "
                      "the League's terms. The men went back down.",
             failure_epilogue="The winding gear is wrecked and the shop "
                              "is empty. The pit will not open this "
                              "season."),
             "pay": 1.20, "slots": -1}),
    # The relation reaching the BOARD: this card cannot be drawn at all
    # until somebody else's harvest fails, and the edge is what tells the
    # mining country about it. The trade layer drew the road it walks (the
    # grain road to a mine that cannot feed itself) two sessions ago.
    card("mining/food-caravan", "The food caravan", ANY_LAND,
         states=("grain-scarce",), days=(10, 18),
         news="A food caravan is coming up the mine road. Every chapter "
              "with an empty larder knows the day it is due, and so does "
              "everybody else on that road.",
         state={"while": ("caravan-due",)},
         menu={"goods": 1.20},
         quest={"post": job(
             "The Mine Road",
             "The food caravan wants swords for the last three days of the "
             "climb. Grain is treasure up here and everyone on that road "
             "knows it.",
             pool=_TOUGHS,
             sites=("the mine road", "the switchback camp"),
             giver="the caravan master",
             epilogue="The caravan is through the gate. The district eats, "
                      "and the price of bread comes down a little.",
             failure_epilogue="The caravan was taken on the switchbacks. "
                              "Nothing came up that road all week."),
             "pay": 1.35}),

    # -- THE WEATHER TRACK: the day-scale sky (2026-08-08) ------------------- #
    # Land-agnostic first, then the three that belong to one land's ground.
    # No wealth condition anywhere on this track: a prosperous land gets the
    # same storms as a starving one -- that is what makes weather the outlet
    # that reaches a quiet world.
    card("weather/storm", "The storm sets in", ANY_LAND, track="weather",
         weather=("storm",), days=(1, 3), sky="storm",
         state={"while": ("storm-bound",)}),
    card("weather/fords-out", "The ford is out",
         ("western", "southern"), track="weather",
         wet=3, days=(6, 12),
         news="Three days of rain and the fords are gone. The bridges and "
              "the ferries are the only way over now, and the men who hold "
              "them know it.",
         state={"while": ("fords-out",)},
         menu={"ferry": 3.0, "goods": 1.15}),
    card("weather/fog-bones", "The fog raises bones", ANY_LAND,
         track="weather", weather=("fog",), chance=0.05, days=(8, 16),
         hook=_name_the_necromancer,
         news="Bones walk in the fog. The village dogs will not go out, and "
              "the country people have a name for the man who calls them "
              "up: {necromancer}.",
         state={"while": ("bones-walk",)},
         encounter={"kinds": ("skeleton", "ghoul"), "where": "wilds",
                    "as": "what the fog put on its feet",
                    "skins": {"skeleton": "Fog-Walker",
                              "ghoul": "Grave-Thing"},
                    "chance": 0.60}),
    # The FIRE CHAIN: the drought's own consequence, and the scar that
    # outlives it. Both were authored for the forest land the contraction
    # deleted; every surviving country has woods and a dry summer, so the
    # pair is land-wide now rather than re-homed to one of the three.
    card("weather/wildfire", "The forest burns", ANY_LAND, track="weather",
         states=("drought",), weather=("clear", "heat", "wind"),
         chance=0.30, days=(4, 8),
         news="The forest is burning above the river villages. They are "
              "carrying out what they can, and already arguing about whose "
              "carelessness it was.",
         state={"while": ("wildfire",), "set": ("burned-over",)},
         quest={"post": job(
             "Carry Them Out",
             "The river villages under the burn have an afternoon to get "
             "out, and the road out goes through what the fire has already "
             "driven onto it.",
             pool=_BEASTS, sites=("the burning slope",),
             giver="the village headman",
             epilogue="The villages are out. What they left behind is "
                      "black, and the arguing about whose fault it was "
                      "has already started.",
             failure_epilogue="The fire took the river villages with "
                              "people still in them."),
             "pay": 1.20}),
    # THE TOWN SMOKE: the one sky a roof does not keep out (rpg.INDOOR_SKY).
    # TEUTONIA's, since the card audit (2026-08-22): the close-built
    # northern town with a forge in every second yard is the free cities'
    # own shape, and a still winter week puts every hearth, forge and
    # tannery back down in the street.
    card("weather/smog", "The smoke settles", "teutonia", track="weather",
         weather=("cloud", "fog"), chance=0.20, days=(2, 5),
         news="The town's own smoke has nowhere to go and has settled in "
              "the streets. Everyone is coughing. The aldermen say it is "
              "the weather.",
         state={"while": ("smog",)},
         menu={"healer": 1.30, "lodging": 0.85}),
    card("weather/dust-storm", "The dust storm", "tergal", track="weather",
         states=("drought",), weather=("wind", "heat", "clear"),
         chance=0.35, days=(1, 3), sky="wind",
         news="A dust storm covers the plain. Nothing moves on the roads, and when "
              "it lifts there will be herds scattered from here to the "
              "river.",
         state={"while": ("dust-storm",)},
         quest={"post": job(
             "Scattered From Here To The River",
             "The dust has put a clan's whole herd on the plain in every "
             "direction. Anything on four legs that is found first belongs "
             "to whoever found it.",
             pool=_BEASTS, sites=("the open plain",),
             giver="the clan's horse-keeper",
             epilogue="Most of the herd is back on its own grass. The "
                      "horse-keeper counts twice and pays once.",
             failure_epilogue="The herd is gone into other clans' hands "
                              "and there is no arguing it back."),
             "pay": 1.15}),
    # THE WHITE STORM: Thule's own sky (2026-08-22, the norse packet). The
    # blizzard off the water that shuts a coast for two days -- the norse
    # counterpart of the steppe's dust storm, and like it, it IS the
    # weather rather than a consequence of it.
    card("norse/white-storm", "The white storm", "norse", track="weather",
         weather=("snow", "storm"), chance=0.35, days=(2, 4),
         sky="snow",
         news="Snow is coming in off the water sideways and the coast "
              "road is gone under it. Nothing is putting out, and the "
              "farms up the valley will not be heard from for two days.",
         state={"while": ("white-storm",)}),
    # -- THE SEASON TRACK: the slow states the day roll reads ---------------- #
    card("weather/drought", "The rains do not come", ANY_LAND,
         track="season", dry=PROFILE_SPELL, chance=0.25, days=(45, 80),
         news="The rains have not come. The rivers are low, the grass is "
              "going brown, and the wells are being counted.",
         state={"while": ("drought",)}),
    card("weather/green-again", "The burn goes green", ANY_LAND,
         track="season", states=("burned-over",),
         without=("drought", "wildfire"), chance=0.03, days=None,
         news="Green is coming up through the black. Nobody alive will "
              "call it healed, but the deer are back.",
         state={"clear": ("burned-over",)}),
)

# --------------------------------------------------------------------------- #
# The politics content (2026-08-10): worldsim.md's politics packets
# --------------------------------------------------------------------------- #
# What politics owns that econ does not: right, office and allegiance. Where a
# packet entry was an econ card wearing a crown -- the lord's mill, the company
# scrip, the guild monopolies -- it stayed in the econ deck and is referenced
# here, never duplicated.
#
# Every card names the TENSION that admits it, and that is also the gate on
# the deck: a land where the crown is fighting its lords never draws the
# temple's cards at all. The west carries the deepest packet by the asymmetry
# doctrine (it is the baseline land, and the ruler sheet's weights are already
# its), and its manor tension is STANDING -- the econ packet's oppression axis
# is not colour, it is what the land is.
#
# The lesser named authorities these cards create -- the banned lord, the
# witch-finder, the bandit king -- draw TWO words off the crown-less pool
# through `_authority_hook`, and the land keeps them: the same man is still
# there the next time the card comes round, which is what makes him a face
# instead of a pulse.

_CROWNED = ("western", "southern", "tergal", "norse")

_BAN_HOOK = _authority_hook("banned-lord", "the banned lord", "lord")
_FINDER_HOOK = _authority_hook("witch-finder", "the witch-finder", "finder")
_BANDIT_HOOK = _authority_hook("bandit-king", "the bandit king", "bandit")
_PRETENDER_HOOK = _authority_hook("pretender", "the pretender", "claimant")

POLITICS_CARDS = (
    # == the west: CUSTOM AGAINST PREROGATIVE ============================= #
    # -- realm & crown ---------------------------------------------------- #
    card("western/interdict", "The temple closes the land", "western",
         tension=("temple-vs-crown",), days=(20, 35),
         news="The temple has closed the land. No weddings, no rites and "
              "no burials until the king gives way. The dead are waiting "
              "in the church porch.",
         state={"while": ("interdict",)},
         quest={"post": job(
             "The Dead Are Waiting",
             "A village wants its dead in the ground and the priest will "
             "not come out. There is a hedge-priest two valleys off who "
             "says he will, and the bishop's men are looking for him.",
             pool=_TOUGHS, sites=("the church porch", "the hedge road"),
             giver="the village headman",
             epilogue="The hedge-priest came and the dead are buried. The "
                      "bishop's men arrived a day late and wrote down "
                      "every name they could get.",
             failure_epilogue="The hedge-priest was taken on the road. The "
                              "village still buries its dead in the woods "
                              "at night."),
             "pay": 1.15, "slots": -1}),
    card("western/orders-law", "The order hangs a local man", "western",
         tension=("temple-vs-crown",),
         faction_edge=("western/militant-order-answers-temple",),
         days=(12, 20),
         news="The militant order tried a local man in its own court and "
              "hanged him on its own gallows. The county wants the body "
              "back, and wants the precedent more.",
         state={"while": ("order-trial",)},
         quest={"post": job(
             "The Body And The Precedent",
             "The sheriff means to take the hanged man down off the "
             "order's gallows and carry him to the county court. The "
             "order's knights are standing over him.",
             pool=_TOUGHS, sites=("the order's gallows",),
             giver="the county sheriff",
             epilogue="The body is in the county's ground and the county "
                      "clerk has written down how it got there.",
             failure_epilogue="The order kept its gallows and its dead. "
                              "The county has stopped asking."),
             "pay": 1.20, "reprice": 1.1}),
    card("western/royal-progress", "The royal progress arrives", "western",
         traits=("itinerant",), days=(8, 14),
         news="The king's court has arrived: a hundred mouths with "
              "precedence, quartered on whichever lord it is testing this "
              "month. He will be poorer when it moves on.",
         state={"while": ("royal-progress",)},
         quest={"post": job(
             "A Hundred Mouths",
             "The lord's steward has four days to feed a court and no "
             "hope of doing it honestly. He wants the deer road watched, "
             "and he wants nobody counting what comes down it.",
             pool=_BEASTS, sites=("the deer road",),
             giver="the lord's steward",
             epilogue="The court ate and the lord kept his name. The "
                      "steward pays out of a box he will not open twice.",
             failure_epilogue="The court ate poorly and said so out loud. "
                              "The lord's name is a joke as far as the "
                              "capital."),
             "slots": 1}),
    card("western/the-ban", "The crown declares a lord dead in law",
         "western", tension=("crown-vs-lords",),
         faction_edge=("western/great-lords-defy-crown",),
         days=(20, 35), hook=_BAN_HOOK,
         news="The crown has declared {lord} legally dead. His lands are "
              "forfeit, anyone may kill him without answering for it, and "
              "he is hiring.",
         state={"while": ("lord-banned",)},
         encounter={"kinds": ("cutthroat", "archer", "soldier"),
                    "where": "road", "as": "the banned lord's last men",
                    "skins": {"cutthroat": "Forfeit Man",
                              "archer": "Outlaw Bow",
                              "soldier": "Dead-In-Law"},
                    "chance": 0.45},
         quest={"post": job(
             "Nobody Answers For It",
             "The banned lord holds one tower and pays better than the "
             "crown does. The crown pays by the head and does not ask who "
             "the head belonged to. Both sides are hiring at the same "
             "inn.",
             pool=_TOUGHS, sites=("the forfeit tower",),
             giver="the crown's bailiff",
             epilogue="The tower is taken. The crown pays by the head and "
                      "the county is very quiet about it.",
             failure_epilogue="The tower held. The banned lord is still "
                              "in it, and the men he hired are on the "
                              "roads."),
             "pay": 1.30, "slots": 1}),
    # VELLISCLAVIA's alone since the card audit (2026-08-22): it is the one
    # western kingdom with the steppe at its back, so it is the only one
    # that can grant border land to a horde in exchange for service.
    card("vellisclavia/settled-warband", "The border grant",
         "vellisclavia",
         tension=("crown-vs-lords",), days=None,
         news="A march lord has granted border land to a Tergal warband in "
              "exchange for service. The neighbours are terrified. The "
              "warband keeps its own law, and both sides are right about "
              "each other.",
         state={"set": ("warband-settled",)},
         quest={"post": job(
             "Both Sides Are Right",
             "A village on the grant's edge wants the riders off its "
             "fields. The warband's chief says the fields were in the "
             "grant. Somebody is going to have to be wrong in front of "
             "witnesses.",
             pool=_TOUGHS, sites=("the granted fields",),
             giver="the march lord's herald",
             epilogue="The line is where the herald says it is, and both "
                      "sides walked away from it alive.",
             failure_epilogue="The village is off its fields and the "
                              "grant runs to the river now."),
             "pay": 1.15, "reprice": 1.1}),
    card("western/the-badge", "The badge-men take the courts", "western",
         tension=("crown-vs-lords", "old-vs-new"), days=(15, 25),
         news="A lord is paying armed men to wear his badge and lean on "
              "the courts. By the time the crown's inspectors come to "
              "break the private army up, the badge-men are the law here.",
         state={"while": ("badge-men",)},
         quest={"post": job(
             "The Inspector's Escort",
             "A crown inspector has come to count a lord's liveries and "
             "wants blades walking beside him. The last man who counted "
             "them was found in the mill race.",
             pool=_TOUGHS, sites=("the lord's hall", "the mill race"),
             giver="the crown's inspector",
             epilogue="The count is written and the inspector is alive to "
                      "carry it. The badges came off, for this month.",
             failure_epilogue="The inspector never finished his count. The "
                              "badge-men hold the courthouse door now."),
             "pay": 1.20, "slots": -1}),
    card("western/the-ward", "The wardship is auctioned", "western",
         tension=("crown-vs-lords", "old-vs-new"), days=(15, 25),
         news="A lord is dead and his heir is nine years old. The crown is "
              "auctioning the wardship: raise the child, drain the estate, "
              "marry it to your own son at majority. Everyone bidding "
              "knows what they are bidding on.",
         state={"while": ("wardship-sold",)},
         quest={"post": job(
             "The Ward",
             "The child's aunt wants the boy out of the winning bidder's "
             "house before the ink dries. The house has hired men who "
             "expect exactly this.",
             pool=_TOUGHS, sites=("the bidder's manor", "the north road"),
             giver="the child's aunt",
             epilogue="The boy is with his aunt and the wardship is a "
                      "lawsuit now instead of a life.",
             failure_epilogue="The boy stayed. The estate will be timber "
                              "and debt by the time he is grown."),
             "pay": 1.25, "reprice": 1.15}),

    # -- manor & village (the standing tension) --------------------------- #
    card("western/custom-strike", "The village works to the letter",
         "western", tension=("manor-vs-village",),
         faction_edge=("western/village-slows-manor-lord",),
         days=(12, 20),
         news="The bailiff demanded extra harvest days. The village cites "
              "the manor's ancient custom, arrives on time, and works at "
              "a crawl the lord cannot quite punish.",
         state={"while": ("custom-strike",)},
         quest={"reprice": 0.90}),
    card("western/burning-rolls", "The court rolls burn", "western",
         tension=("manor-vs-village",), without=("rolls-burned",),
         days=None,
         news="The mob did not go for the lord. It went for the manor's "
              "court rolls -- who owes what, and who was born unfree. "
              "Every debt and every servile birth is ash, unless the "
              "clerk kept a second copy.",
         state={"set": ("rolls-burned",)},
         quest={"post": job(
             "The Second Copy",
             "The clerk kept a second copy and three parties know it. The "
             "lord wants it, the village wants it burned, and the clerk "
             "wants to be somewhere else by Friday.",
             pool=_TOUGHS, sites=("the clerk's house", "the burnt hall"),
             giver="the manor clerk",
             epilogue="The second copy is where the party left it, and "
                      "the whole valley now knows which.",
             failure_epilogue="The copy went into somebody's fire in the "
                              "confusion. Nobody in the valley can prove "
                              "anything about anybody."),
             "pay": 1.25, "slots": 1}),
    card("western/year-and-a-day", "A year and a day", "western",
         tension=("manor-vs-village", "crown-vs-guilds"), days=(10, 18),
         news="A skilled smith has run from the manor to the chartered "
              "town. Town air makes a man free after a year and a day, "
              "the guild will not give him up, and the lord's men are at "
              "the gate counting.",
         state={"while": ("town-air",)},
         quest={"post": job(
             "The Gate Count",
             "The guild wants the smith kept inside the walls until the "
             "day runs out. The lord's men want him outside them for one "
             "hour. The clock is public knowledge.",
             pool=_TOUGHS, sites=("the town gate", "the guild yard"),
             giver="the guild warden",
             epilogue="The day ran out with the smith inside the walls. "
                      "He is a free man and the guild says so in writing.",
             failure_epilogue="The smith was taken off the street two "
                              "days short. He is back at the manor forge "
                              "with an iron collar on."),
             "pay": 1.20, "reprice": 1.1}),
    card("western/lord-away", "While the lord is away", "western",
         tension=("manor-vs-village",),
         faction_edge=("western/manor-lord-squeezes-village",),
         days=(15, 25),
         news="The bailiff has invented fines -- bad ale, gathered "
              "deadwood -- and runs the manor court as his own purse. The "
              "village reeve sells the lord's grain and books the "
              "shortfall to blight. Neither has told the lord.",
         state={"while": ("bailiff-loose",)},
         quest={"post": job(
             "Two Jerks, One Address",
             "Somebody has to ride to the lord with the truth, and both "
             "men in the valley with something to hide would rather that "
             "rider did not arrive.",
             pool=_TOUGHS, sites=("the manor court", "the lord's road"),
             giver="the village priest",
             epilogue="The lord has the whole account. The bailiff is in "
                      "his own stocks and the reeve has left the county.",
             failure_epilogue="The rider never reached the lord. The "
                              "fines have gone up again."),
             "pay": 1.15, "slots": -1}),
    card("western/rent-strike", "The rent strike", "western",
         tension=("manor-vs-village",), days=(12, 20),
         news="The village has hidden its coin and pleads a blight. The "
              "bailiff cannot evict everyone at once and knows it. Some "
              "years the plea is honest.",
         state={"while": ("rent-strike",)},
         quest={"post": job(
             "Is The Plea Honest",
             "The lord wants somebody who is not from here to walk the "
             "strips, look in the barns, and say whether the village is "
             "poor or lying. The village would rather the walk did not "
             "happen.",
             pool=_TOUGHS, sites=("the barn row", "the far strips"),
             giver="the lord's steward",
             epilogue="The walk is done and the answer is written. What "
                      "the lord does with it is his own business.",
             failure_epilogue="Nobody walked the strips. The lord has "
                              "sent men who will not ask first."),
             "pay": 1.10, "reprice": 0.9}),
    card("western/widows-holding", "The widow's holding", "western",
         tension=("manor-vs-village",), days=(15, 25),
         news="A rich widow pays the yearly fine to stay unmarried and "
              "keeps the best land in the valley out of every scheming "
              "hand. Suitors, heirs and the lord's own plans are circling "
              "her.",
         state={"while": ("widow-holding",)},
         quest={"post": job(
             "The Suitors",
             "The widow wants her gate watched for a season and her fine "
             "carried to the manor court in one piece. Two of the suitors "
             "have stopped writing letters.",
             pool=_TOUGHS, sites=("the widow's holding",),
             giver="the widow",
             epilogue="The fine is paid, the gate held, and the widow is "
                      "unmarried for another year.",
             failure_epilogue="The fine never reached the court. The land "
                              "is being surveyed for somebody's son."),
             "pay": 1.20, "reprice": 1.1}),
    card("western/peasant-merger", "The strips are merged", "western",
         tension=("manor-vs-village",), days=None,
         news="Two big village families have betrothed their strips "
              "together and now hold the best soil in the parish between "
              "them. The balance of the village has moved from below, and "
              "the lord will notice late.",
         state={"set": ("strips-merged",)},
         quest={"reprice": 1.10}),
    card("western/jury-lies", "The jury swears it true", "western",
         tension=("manor-vs-village",), days=(8, 14),
         news="The manor court's jury -- the accused's own neighbours -- "
              "has sworn a starving thief innocent in the law's teeth, "
              "and every one of them is liable for the fine.",
         state={"while": ("jury-lies",)},
         quest={"post": job(
             "One More Witness",
             "The lord's court will sit again on Thursday and one more "
             "witness either way settles it. Both sides have worked out "
             "who that could be and where he drinks.",
             pool=_TOUGHS, sites=("the manor court", "the ale house"),
             giver="the accused thief's sister",
             epilogue="The verdict held. The village paid its fine "
                      "together and nobody named anybody.",
             failure_epilogue="The verdict was overturned and the thief "
                              "hanged. Half the jury is paying the fine "
                              "and the other half has left."),
             "pay": 1.10, "reprice": 0.95}),
    card("western/cry-ignored", "The hue and cry goes unanswered",
         "western", tension=("manor-vs-village",), days=(10, 16),
         news="The forester raised the hue and cry on a poacher the "
              "village likes, and the village went conveniently deaf. "
              "Failing the cry is a collective fine, and everyone is "
              "counting on nobody testifying.",
         state={"while": ("cry-ignored",)},
         quest={"post": job(
             "The Forester's Own Cry",
             "The forester wants outsiders to walk the wood with him, "
             "since nobody local will. The poacher knows the wood and has "
             "friends in it.",
             pool=_BEASTS, sites=("the closed wood",),
             giver="the royal forester",
             epilogue="The wood is walked and the forester has his man. "
                      "The village has not spoken to him since.",
             failure_epilogue="The poacher is still in the wood and the "
                              "village fine has been levied on everybody "
                              "but him."),
             "pay": 1.10, "reprice": 0.95}),
    card("western/forest-law", "The royal woods are closed", "western",
         tension=("manor-vs-village", "crown-vs-lords"), days=(25, 40),
         news="The royal woods stand outside the common law again. The "
              "forage, the deadwood and the gleaning are fenced off year "
              "by year, the penalty for a deer is savage, and two lords' "
              "retinues are already skirmishing over a boundary oak.",
         state={"while": ("forest-law",)},
         quest={"post": job(
             "The Boundary Oak",
             "Two lords' men are fighting over which side of an oak the "
             "wood begins. One of them is paying for the argument to be "
             "settled before the crown's justice rides through.",
             pool=_TOUGHS, sites=("the boundary oak",),
             giver="the lord's forester",
             epilogue="The oak is where the party left it and the "
                      "boundary is what the surviving side says it is.",
             failure_epilogue="The skirmish ran on into the villages. "
                              "Both woods are closed now and the gleaning "
                              "with them."),
             "pay": 1.15, "slots": 1}),
    card("western/silver-vein", "Silver on the lord's land", "western",
         tension=("manor-vs-village", "old-vs-new"), days=None,
         news="A strike on the local lord's land has made him suddenly, "
              "dangerously rich. Armed men, bought judges, new walls, new "
              "appetites. The mountain prospectors who found it say that "
              "finding is keeping, and mining law agrees with them.",
         state={"set": ("silver-strike",)},
         quest={"post": job(
             "Finding Is Keeping",
             "The prospectors have a claim under mining law and the lord "
             "has a title under this one. Both are hiring, both are "
             "right, and the hole in the ground does not care.",
             pool=_GUNHANDS, sites=("the silver adit",),
             giver="the prospectors' claim-holder",
             epilogue="The adit is held and the claim is written down "
                      "twice, in two laws that still disagree.",
             failure_epilogue="The prospectors are off the hill. Their "
                              "claim is filed under the mountain, and the "
                              "mountain remembers."),
             "pay": 1.25, "slots": 1}),
    card("western/trial-by-combat", "The loophole stands open", "western",
         tension=("old-vs-new", "manor-vs-village"), days=(12, 20),
         news="Two wealthy houses are answering a lawsuit at swordpoint "
              "through hired champions. The court has agreed to it, which "
              "means every case in the county can go the same way now.",
         state={"while": ("champions-hired",)},
         quest={"post": job(
             "Champion For Hire",
             "A house that will lose its case on the evidence wants a "
             "champion who will not lose it on the field. The other side "
             "has been hiring for a week.",
             pool=_TOUGHS, sites=("the court field",),
             giver="the house's advocate",
             epilogue="The field is settled and so is the case. The "
                      "county's lawyers are all quietly hiring.",
             failure_epilogue="The champion went down and the case went "
                              "with him. The house is paying costs it "
                              "cannot pay."),
             "pay": 1.30, "slots": 1}),

    # -- town ------------------------------------------------------------- #
    card("western/charter-run", "The charter run", "western",
         tension=("crown-vs-guilds",),
         faction_edge=("western/guilds-buy-crown",), days=(10, 16),
         news="The market town has pooled its silver in secret to buy a "
              "royal charter out from under its lord. The lord has "
              "blockaded the roads to stop the purse reaching the king.",
         state={"while": ("charter-run",)},
         quest={"post": job(
             "The Purse And The Blockade",
             "The town's purse has to reach the king's clerk and every "
             "road out is watched. The lord's men have orders to find "
             "silver and no orders about who is carrying it.",
             pool=_TOUGHS, sites=("the blockaded road", "the king's court"),
             giver="the town's guild warden", places=2,
             epilogue="The purse reached the clerk. The town has its "
                      "charter and the lord has a grievance in writing.",
             failure_epilogue="The purse was taken on the road. The town "
                              "is the lord's for another generation and "
                              "knows who lost it."),
             "pay": 1.30, "reprice": 1.2}),
    card("western/mayor-in-velvet", "The mayor in velvet", "western",
         tension=("old-vs-new",),
         faction_edge=("western/new-men-outbid-great-lords",),
         days=(15, 25),
         news="A wool merchant has been elected mayor, dresses past his "
              "blood, rides a warhorse and demands to be addressed as an "
              "equal. The insulted barons are choking the town's grain to "
              "starve him down.",
         state={"while": ("mayor-in-velvet",)},
         menu={"goods": 1.25},
         quest={"post": job(
             "The Grain Road, Again",
             "The mayor wants one grain train through the barons' roads "
             "and does not much care what it costs. The barons want it "
             "stopped where the town can see it stop.",
             pool=_TOUGHS, sites=("the barons' road",),
             giver="the mayor",
             epilogue="The grain is in the town and the mayor rode out to "
                      "meet it in velvet. The barons are writing letters.",
             failure_epilogue="The train was turned back. The town is "
                              "hungry and has started to blame the "
                              "velvet."),
             "pay": 1.20, "slots": -1}),

    # -- temple & parish --------------------------------------------------- #
    card("western/tithe-war", "The tithe war", "western",
         tension=("manor-vs-village", "temple-vs-crown"), days=(15, 25),
         news="The village tithes its sickliest lambs and its lightest "
              "sheaves, and has done for years. The priest's barn keeps "
              "the evidence, and he has started writing it down.",
         state={"while": ("tithe-war",)},
         quest={"post": job(
             "The Barn Count",
             "The priest wants his barn counted by somebody the village "
             "cannot lean on. The village would prefer the count to be "
             "interrupted.",
             pool=_TOUGHS, sites=("the tithe barn",),
             giver="the parish priest",
             epilogue="The count is done and the tally is in the bishop's "
                      "hand. Next year's lambs will be better.",
             failure_epilogue="The barn burned in the night with the "
                              "tally in it. The priest is not asking "
                              "again."),
             "pay": 1.10, "reprice": 0.95}),
    card("western/scandalous-priest", "The rectory scandal", "western",
         tension=("manor-vs-village",), days=(15, 25),
         news="The priest keeps a woman at the rectory and buys land for "
              "his children out of the church box. The pious of the "
              "parish are petitioning the bishop, who has a price for "
              "acting. He is also the best friend this village has.",
         state={"while": ("priest-scandal",)},
         quest={"post": job(
             "The Bishop's Price",
             "Somebody has to carry the petition, or lose it. Both halves "
             "of the parish have found the party and both are paying.",
             pool=_TOUGHS, sites=("the rectory", "the bishop's road"),
             giver="the parish's pious widow",
             epilogue="The petition arrived, or it did not. The parish "
                      "knows which and has divided accordingly.",
             failure_epilogue="The petition was taken off the road by "
                              "people who wanted it read. The bishop is "
                              "coming himself."),
             "pay": 1.15, "reprice": 1.05}),
    card("western/witch-finder", "The witch-finder arrives", "western",
         traits=("spell-fearing",), days=(10, 18), hook=_FINDER_HOOK,
         news="A man calling himself {finder} has arrived offering to "
              "root out the village's witch, for a fee. He has never yet "
              "failed to find one.",
         state={"while": ("witch-finder",)},
         quest={"post": job(
             "He Always Finds One",
             "The finder has named the herb-woman and the village has "
             "started agreeing with him. Her son is paying anyone who "
             "will stand in the square and say what the trick is.",
             pool=_TOUGHS, sites=("the village square",),
             giver="the herb-woman's son",
             epilogue="The trick is out in front of the whole village and "
                      "the finder left before dark, still owed his fee.",
             failure_epilogue="The herb-woman is dead and the finder has "
                              "moved on to the next village with a "
                              "reference."),
             "pay": 1.20, "reprice": 1.1}),
    card("western/dancing-plague", "A street cannot stop dancing",
         "western", tension=("manor-vs-village",), chance=0.35,
         days=(10, 18),
         news="A street of villagers has been dancing for three days and "
              "cannot stop. Flagellant columns are arriving behind the "
              "news. The temple calls it penance and the wise woman calls "
              "it poison.",
         state={"while": ("dancing-plague",)},
         quest={"post": job(
             "The Wise Woman's Answer",
             "The wise woman says the cause has an address: the mill, the "
             "grain, and whoever sold it. She wants the mill looked at "
             "before the flagellants get here and make it a miracle.",
             pool=_TOUGHS, sites=("the mill loft", "the dancing street"),
             giver="the wise woman",
             epilogue="The bad grain is out of the mill and the dancing "
                      "stopped inside a week. The temple has claimed the "
                      "credit.",
             failure_epilogue="The flagellants have the street and the "
                              "mill is still grinding. Two more houses "
                              "started this morning."),
             "pay": 1.20, "slots": -1}),
    card("western/free-company", "The free company", "western",
         tension=("crown-vs-lords",), days=(20, 35),
         news="The war wound down and the unpaid company did not. It is a "
              "small state on the roads now: it tolls the bridges, it "
              "rents itself to whichever side pays, and it is recruiting.",
         state={"while": ("free-company",)},
         quest={"post": job(
             "Buy Them Or Break Them",
             "The county has raised money to pay the company off and "
             "would rather spend it on somebody who will break the "
             "company instead. The company has heard both offers.",
             pool=_TOUGHS, sites=("the company's bridge",),
             giver="the county's clerk",
             epilogue="The bridge is open and the company has moved on to "
                      "somebody else's roads.",
             failure_epilogue="The company holds the bridge and has "
                              "raised the toll to cover the trouble."),
             "pay": 1.30, "slots": -1}),
    card("western/midnight-court", "The midnight court", "western",
         tension=("old-vs-new", "crown-vs-guilds"), days=(15, 25),
         news="The lawful courts are bought, so a tribunal of masked "
              "freemen has started trying men by night and hanging them "
              "by morning. It has a membership list, and half the county "
              "would like to see it.",
         state={"while": ("midnight-court",)},
         quest={"post": job(
             "The Membership List",
             "The sheriff wants the list. The court wants the sheriff "
             "tried. Somebody in the party is going to be offered a seat "
             "before this is over.",
             pool=_TOUGHS, sites=("the night wood", "the sheriff's house"),
             giver="the county sheriff",
             epilogue="The list is in the sheriff's hand and four names "
                      "on it have already left the county.",
             failure_epilogue="The sheriff was tried and hanged by his "
                              "own neighbours. Nobody will say where."),
             "pay": 1.25, "reprice": 1.15}),

    # == the south: ONE KING, ONE LAW, ONE FAITH ========================== #
    card("southern/revocation", "The old faith is outlawed",
         "southern", tension=("crown-vs-faith",),
         faction_edge=("southern/tribunal-hunts-hidden-faith",),
         days=(25, 40),
         news="The tolerated faith was made illegal overnight. Dragoons "
              "are quartered in the houses of anyone who will not "
              "convert, and the skilled trades are leaving for the border "
              "with their capital.",
         state={"set": ("faith-banned",), "wealth_while": "crisis"},
         quest={"post": job(
             "The Border, Before Dawn",
             "Three families of dyers want to be over the border with "
             "their tools before the dragoons finish the street. "
             "Informers are paid by the head.",
             pool=_TOUGHS, sites=("the night quarter", "the border road"),
             giver="the dyers' master", places=2,
             epilogue="The families are over the border with their tools. "
                      "The street they left is quartered and quiet.",
             failure_epilogue="The families were taken at the last gate. "
                              "The tools were sold and the informer was "
                              "paid by the head."),
             "pay": 1.30, "slots": -1}),
    card("southern/dueling-edict", "The dueling edict", "southern",
         tension=("sword-vs-robe",),
         faction_edge=("southern/sword-snub-robe",), days=(15, 25),
         news="Duelling is a capital crime now. Two grandees fought "
              "anyway. One is dead and the other is on the road with his "
              "estate in limbo, the dead man's family behind him, and "
              "nothing to sell but his sword.",
         state={"while": ("duel-fugitive",)},
         quest={"post": job(
             "The Survivor",
             "The dead man's family wants the survivor brought back to "
             "the capital. The survivor wants an escort to anywhere else "
             "and can pay for exactly one.",
             pool=_TOUGHS, sites=("the coast road",),
             giver="the dead grandee's brother",
             epilogue="The survivor is where the party took him, and the "
                      "family has stopped paying either way.",
             failure_epilogue="The survivor went over the border with the "
                              "family two days behind. It will be settled "
                              "in somebody else's country."),
             "pay": 1.25, "reprice": 1.1}),
    card("southern/sealed-warrant", "The warrants go on sale",
         "southern", tension=("sword-vs-robe", "court-vs-provinces"),
         days=(20, 30),
         news="Blank royal arrest orders exist and can be bought. A name "
              "written in, a fortress door, and no charge and no trial "
              "after it. Half the court is buying and the other half is "
              "sleeping badly.",
         state={"while": ("warrants-sold",)},
         menu={"goods": 1.10},
         quest={"post": job(
             "The Name Left Blank",
             "A merchant's daughter has vanished into a fortress on "
             "somebody's paper. Her father has bought a warrant of his "
             "own and wants it delivered to the right door.",
             pool=_TOUGHS, sites=("the fortress gate",),
             giver="the merchant",
             epilogue="The daughter is out and the warrant that took her "
                      "is ash. Somebody at court has noticed.",
             failure_epilogue="The fortress kept her and the second "
                              "warrant was read by the wrong clerk. The "
                              "merchant's own name is on a list now."),
             "pay": 1.30, "reprice": 1.15}),
    card("southern/tontine", "The tontine", "southern",
         tension=("sword-vs-robe",), days=(15, 25),
         news="An elite investment pool pays out to the last survivor, "
              "and the survivors have begun dying in interesting ways. "
              "The pool names its own motive and everyone in it knows the "
              "arithmetic.",
         state={"while": ("tontine-deaths",)},
         quest={"post": job(
             "The Last Survivor",
             "One of the remaining eight wants to live to collect and "
             "will pay for a house watched, a road walked, and a cook "
             "questioned.",
             pool=_TOUGHS, sites=("the town house", "the physician's "
                                  "rooms"),
             giver="the seventh subscriber",
             epilogue="The subscriber is alive and two of the others are "
                      "not. The pool's clerk has stopped answering his "
                      "door.",
             failure_epilogue="The subscriber died at his own table. The "
                              "pool is down to five and the payout is "
                              "getting close."),
             "pay": 1.30, "reprice": 1.2}),
    # The bubble CHAIN: the crown grants the monopoly, the shares go mad,
    # and the crash is the next card in the deck.
    card("southern/monopoly-bubble", "The monopoly is granted",
         "southern", tension=("court-vs-provinces", "sword-vs-robe"),
         without=("shares-mad", "quarter-ruined"), days=(12, 20),
         news="The crown has granted one company the whole colony trade. "
              "The shares have gone mad. Servants are buying, and so is "
              "everyone who lends to servants.",
         state={"set": ("shares-mad",)},
         quest={"post": job(
             "The Subscription Book",
             "The company's subscription book has to reach the exchange "
             "before the doors open, and three houses would rather it did "
             "not arrive at all.",
             pool=_TOUGHS, sites=("the exchange steps",),
             giver="the company's factor",
             epilogue="The book opened on time. The price doubled before "
                      "noon and the factor has not stopped smiling.",
             failure_epilogue="The book never opened. The price doubled "
                              "anyway, on nothing at all."),
             "pay": 1.20, "slots": 1}),
    card("southern/the-crash", "The shares collapse", "southern",
         states=("shares-mad",), days=(15, 25),
         news="The colony shares are worth what the paper weighs. Half "
              "the merchant quarter is ruined by breakfast and the other "
              "half is being blamed for it in the street.",
         state={"clear": ("shares-mad",), "while": ("quarter-ruined",)},
         encounter={"kinds": ("cutthroat", "bruiser"), "where": "road",
                    "as": "men who were rich on Tuesday",
                    "skins": {"cutthroat": "Ruined Clerk",
                              "bruiser": "Ruined Broker"},
                    "chance": 0.40},
         quest={"post": job(
             "The Broker's Door",
             "A broker who sold at the top wants his house held until the "
             "crowd outside it gets bored. It has not got bored in two "
             "days.",
             pool=_TOUGHS, sites=("the broker's house",),
             giver="the broker's clerk",
             epilogue="The house held. The broker left by the garden with "
                      "everything he still had.",
             failure_epilogue="The house went in. There is nothing left "
                              "of it worth the name and the broker is "
                              "somewhere in the crowd."),
             "pay": 1.25, "slots": -1}),
    card("southern/alchemists-wing", "The crown funds the alchemists",
         "southern", tension=("court-vs-provinces",), days=(25, 40),
         news="The crown has put a wing of the palace and a great deal of "
              "money behind a stable of alchemists, on the understanding "
              "that they will transmute the war debt away. Nobody has "
              "asked what gold is worth the day after they succeed.",
         state={"while": ("alchemists-funded",)},
         menu={"goods": 1.15},
         quest={"post": job(
             "The Wing's Shopping List",
             "The alchemists want quicksilver, a lodestone the size of a "
             "fist, and something out of a barrow that they will only "
             "describe once. The crown is paying and not asking.",
             pool=_TOUGHS, sites=("the old barrow", "the palace wing"),
             giver="the crown's alchemist", places=2,
             epilogue="The list is filled and the wing is working day and "
                      "night. The treasury has stopped asking for "
                      "results.",
             failure_epilogue="The list is not filled and the wing has "
                              "gone quiet. The treasury is asking what "
                              "the money bought."),
             "pay": 1.20, "slots": 1}),
    card("southern/flour-war", "The bread price is let go",
         "southern", tension=("court-vs-provinces",),
         wealth=("crisis", "normal"), without=("bread-riots",),
         days=(10, 18),
         news="The crown lifted the bread price controls in a lean year. "
              "Bread has quintupled, the bakeries have been sacked, and "
              "two merchants were lynched as hoarders. The decree was "
              "read to the crowd and then the musketeers fired.",
         state={"while": ("bread-riots",)},
         quest={"post": job(
             "The Bakers' Street",
             "Three bakers who still have flour want their street held "
             "until the grain convoy arrives. The crowd knows the convoy "
             "is coming too.",
             pool=_TOUGHS, sites=("the bakers' street",),
             giver="the bakers' guild master",
             epilogue="The street held and the convoy got in. Bread is "
                      "only twice what it was.",
             failure_epilogue="The street went. There is no flour left in "
                              "it and no bakers either."),
             "pay": 1.25, "slots": -1}),
    card("southern/salt-revolt", "The salt country rises",
         "southern", tension=("court-vs-provinces",),
         states=("tax-farmed",), days=(15, 25),
         news="The salt tax went up once too often. A province has "
              "butchered its tax collectors, and the army has answered "
              "with burned villages and hanged ringleaders.",
         state={"while": ("salt-revolt",), "clear": ("tax-farmed",)},
         encounter={"kinds": ("cutthroat", "bruiser", "soldier"),
                    "where": "road", "as": "the salt country's own men",
                    "skins": {"cutthroat": "Salt Man",
                              "bruiser": "Salt-Breaker",
                              "soldier": "Punitive Lance"},
                    "chance": 0.45},
         quest={"post": job(
             "The Column And The Village",
             "A punitive column is a day from a village that has already "
             "given up its ringleaders. Somebody has to reach the column "
             "first, and somebody else has been paid to make sure nobody "
             "does.",
             pool=_TOUGHS, sites=("the salt road",),
             giver="the village's own priest",
             epilogue="The column stopped short of the village. The "
                      "ringleaders hanged and the roofs stayed on.",
             failure_epilogue="The column did not stop. The village is "
                              "black and the province is worse than it "
                              "was."),
             "pay": 1.25, "slots": -1}),
    card("southern/auto-da-fe", "The tribunal stages its penance",
         "southern", tension=("crown-vs-faith",), days=(12, 20),
         news="The tribunal has arrested a mountain village wholesale -- "
              "heresy, the old religion, harm by hidden means -- and "
              "means to stage the penance in the capital square as "
              "theatre. Casting is still legal; the academy is proof of "
              "that. This is about who the crown is willing to burn.",
         state={"while": ("auto-da-fe",)},
         quest={"post": job(
             "The Mountain Village",
             "A village elder's daughter got out and wants what the "
             "tribunal actually took: the parish book, which says who "
             "denounced whom and for how much.",
             pool=_TOUGHS, sites=("the tribunal's yard", "the mountain "
                                  "village"),
             giver="the elder's daughter", places=2,
             epilogue="The book is out and being read aloud in three "
                      "taverns. Two of the denouncers have left the "
                      "capital.",
             failure_epilogue="The book stayed in the tribunal's yard and "
                              "the square is being built for the "
                              "penance."),
             "pay": 1.30, "reprice": 1.15}),
    card("southern/bandit-king", "The bandit king", "southern",
         tension=("court-vs-provinces",), days=(25, 40),
         hook=_BANDIT_HOOK,
         news="{bandit} lost his land to enclosure and debt, and men follow "
              "him. He robs tax shipments and rich men and nothing else, so "
              "the peasants hide him and the magistrates hang whoever "
              "they catch instead.",
         state={"set": ("bandit-king",)},
         quest={"post": job(
             "Both Sides Pay For Road Work",
             "The magistrate wants the tax road walked. The bandit wants "
             "to know when the shipment moves. The party can be paid for "
             "the same week's work twice, once.",
             pool=_TOUGHS, sites=("the tax road", "the hedge camp"),
             giver="the provincial magistrate",
             epilogue="The road is walked and the shipment is where "
                      "somebody wanted it. Both employers paid.",
             failure_epilogue="The shipment is gone and the magistrate "
                              "has hanged three men out of the nearest "
                              "village for it."),
             "pay": 1.25, "slots": 1}),

    # == Tergal: AUTHORITY IS PERSONAL ===================================== #
    card("tergal/hostage-guard", "The hostage guard", "tergal",
         tension=("clan-vs-clan",),
         faction_edge=("tergal/clans-feud-rival-clans",), days=None,
         news="The high chief's bodyguard is drawn from the rival chiefs' "
              "sons: an elite corps and a hostage crop in one. One of the "
              "sons has run, and his father has stopped answering the "
              "council's messengers.",
         state={"set": ("hostage-guard",)},
         quest={"post": job(
             "The Son Who Ran",
             "The high chief wants the boy back in the guard tent before "
             "the council meets. His father wants him further away than "
             "that. The boy has opinions of his own.",
             pool=_TOUGHS, sites=("the guard tents", "the long grass"),
             giver="the high chief's herald", places=2,
             epilogue="The boy is back among the guard and his father "
                      "came to the council after all.",
             failure_epilogue="The boy is gone and his father's saddle "
                              "was empty at the council. That is the "
                              "declaration."),
             "pay": 1.25, "reprice": 1.15}),
    card("tergal/sworn-brothers", "Sworn brothers", "tergal",
         tension=("clan-vs-clan", "chiefs-vs-mothers"), days=(20, 30),
         news="Two chiefs cut their palms and became brothers by oath "
              "across clan lines. That is a super-faction overnight. The "
              "council has tilted and both clans' mothers have "
              "objected in public.",
         state={"while": ("sworn-brothers",)},
         quest={"post": job(
             "The Mothers Object",
             "The clan mothers want the oath witnessed as invalid and "
             "have named the witnesses they will accept. Two of those "
             "witnesses have been moved somewhere quiet.",
             pool=_TOUGHS, sites=("the mothers' tent", "the quiet camp"),
             giver="the eldest clan mother", places=2,
             epilogue="The witnesses spoke and the oath is a private "
                      "matter now, not a faction. Both chiefs are "
                      "furious and neither can say so.",
             failure_epilogue="The witnesses never came. The oath stands "
                              "and the two clans vote as one from here "
                              "on."),
             "pay": 1.20, "slots": 1}),
    card("tergal/counting-coup", "Counting coup", "tergal",
         tension=("clan-vs-clan",), days=(10, 18),
         news="A young chief has claimed coup on a rival: touched him in "
              "a fight and left him alive, which outranks killing him. "
              "The rival says it did not happen and wants it done again "
              "in front of witnesses.",
         quest={"post": job(
             "Judged By Tergal Law",
             "The party is invited into the second attempt as the "
             "neutral hands. Here, mercy scores and slaughter loses face, "
             "and everybody is watching to see whether foreigners can "
             "count.",
             pool=_TOUGHS, sites=("the challenge ground",),
             giver="the young chief",
             epilogue="Coup was counted in front of the whole camp and "
                      "nobody died. The party's name is worth something "
                      "on this grass now.",
             failure_epilogue="Somebody was killed on the challenge "
                              "ground. The coup is void, the party is "
                              "the reason, and the camps have noticed."),
             "pay": 1.20, "slots": 1}),
    card("tergal/mourning-war", "The mourning war", "tergal",
         tension=("clan-vs-clan",), states=("grass-gone",),
         days=(15, 25),
         news="The raid is not for plunder. It is for people: captives to "
              "fill the tents the sickness emptied. The clans that lost "
              "most are riding first.",
         state={"while": ("mourning-war",)},
         encounter={"kinds": ("cutthroat", "bruiser", "soldier"),
                    "where": "road", "as": "riders taking people, not "
                                           "goods",
                    "skins": {"cutthroat": "Taker",
                              "bruiser": "Tent-Filler",
                              "soldier": "Mourning Lance"},
                    "chance": 0.50},
         quest={"post": job(
             "The Tents They Emptied",
             "A border village has lost eleven people to a night raid and "
             "can name the clan. Buying them back is possible. Taking "
             "them back is faster.",
             pool=_TOUGHS, sites=("the raiders' camp",),
             giver="the village headman",
             epilogue="The eleven are home. The clan that took them has "
                      "been paid in something and considers it settled.",
             failure_epilogue="The eleven are in another clan's tents "
                              "with new names. In a year they will be "
                              "that clan."),
             "pay": 1.30, "slots": -1}),
    card("tergal/shaming-pole", "The shaming pole", "tergal",
         tension=("council-vs-outlaws",),
         faction_edge=("tergal/clans-outlaw-outlaws",), days=(12, 20),
         news="A carved pole is up outside a camp with a formal curse and "
              "a name on it. The named man is a pariah until it comes "
              "down. Shame is a siege weapon here and it can be aimed at "
              "anybody, including strangers.",
         state={"while": ("shaming-pole",)},
         quest={"post": job(
             "Take The Pole Down",
             "The named man wants the pole down and the singer who carved "
             "it made to say so out loud. The camp that raised it is "
             "sitting around it in shifts.",
             pool=_TOUGHS, sites=("the pole ground",),
             giver="the named man",
             epilogue="The pole is down and the singer unsaid it in front "
                      "of the camp. Slowly, and badly, but out loud.",
             failure_epilogue="The pole is still up and a second name has "
                              "been carved under the first."),
             "pay": 1.20, "reprice": 1.1}),
    card("tergal/ghost-dance", "The ghost dance", "tergal",
         tension=("council-vs-outlaws",), states=("grass-gone",),
         days=(20, 35),
         news="The herds have failed and the tribute chiefs have got fat. "
              "A new faith is sweeping the camps -- dance and the dead "
              "come back, the grass comes back, and the settled lands go "
              "under. It is against the old chiefs as much as anyone.",
         state={"while": ("ghost-dance",)},
         encounter={"kinds": ("cutthroat", "bruiser", "veteran"),
                    "where": "wilds", "as": "dancers who have stopped "
                                            "eating",
                    "skins": {"cutthroat": "Dancer",
                              "bruiser": "Drum-Keeper",
                              "veteran": "Dance-Chief"},
                    "chance": 0.40},
         quest={"post": job(
             "The Drum Camp",
             "A tribute chief wants the drum camp broken before the "
             "council hears about it. The camp has three hundred people "
             "in it and no weapons worth the name.",
             pool=_TOUGHS, sites=("the drum camp",),
             giver="the tribute chief",
             epilogue="The drums have stopped. What the chief paid for "
                      "and what happened are both known in the camps now.",
             failure_epilogue="The drums did not stop. Two more camps "
                              "have taken it up and the chief has moved "
                              "his tents south."),
             "pay": 1.25, "slots": -1}),

    # == Thule: THE LAW IS THE THING ======================================= #
    # (2026-08-22, the norse packet.) Authority here is a man with ships
    # and a hall full of men he has to keep paying, and the only thing over
    # him is an assembly of free men who can outlaw him. Seven cards over
    # the four tensions.
    card("norse/kings-share", "The sea-king takes his share", "norse",
         tension=("sea-vs-land",),
         faction_edge=("norse/sea-kings-tax-land-chiefs",), days=(15, 25),
         news="The sea-king has sent his men round the fjord for his "
              "share of every catch and every cargo. He calls it the "
              "price of a quiet coast. The land-chiefs call it a tax and "
              "are saying so in public.",
         state={"while": ("kings-share",)},
         menu={"goods": 1.15},
         quest={"post": job(
             "The Share Boat",
             "The share boat is going round the fjord with two men in "
             "it. One farm has decided this is the year it does not pay, "
             "and both sides want somebody standing on the jetty who is "
             "not from here.",
             pool=_TOUGHS, sites=("the fjord jetty",),
             giver="the sea-king's share-man",
             epilogue="The share was taken and nobody was killed for it. "
                      "The farm paid under protest and everyone heard "
                      "the protest.",
             failure_epilogue="The share boat came back empty and with a "
                              "dead man in it. The sea-king is coming "
                              "round himself next time."),
             "pay": 1.15}),
    card("norse/ring-giver-poor", "The chief's silver runs out", "norse",
         tension=("sea-vs-land", "jarls-vs-thing"), wealth=("crisis",),
         days=(20, 30),
         news="The chief has run out of silver to give. A hall full of "
              "men who are paid in arm-rings and are not being paid is a "
              "hall full of men looking at other halls.",
         state={"while": ("ring-giver-poor",)},
         quest={"post": job(
             "The Arm-Rings",
             "The chief wants his hall kept full for one more month and "
             "has nothing to fill it with. A neighbour is buying his men "
             "away one at a time, in the same drinking hall.",
             pool=_TOUGHS, sites=("the mead hall",),
             giver="the chief's oath-man",
             epilogue="The hall is still full and the neighbour's silver "
                      "went home in his own purse. The chief pays you in "
                      "the last of his.",
             failure_epilogue="Half the hall has gone over. The chief is "
                              "a landowner now and not much else."),
             "pay": 1.25, "slots": 1}),
    card("norse/the-thing", "The assembly at the stone", "norse",
         tension=("jarls-vs-thing",), days=(10, 16),
         news="The assembly is sitting at the stone. Every free man with "
              "a case is here, the law is being spoken aloud from "
              "memory, and nobody may be taken for anything while it "
              "sits.",
         state={"while": ("thing-sitting",)},
         menu={"lodging": 1.40, "goods": 1.15},
         quest={"post": job(
             "Brought To The Stone",
             "A man with a case at the assembly has to reach the stone "
             "alive, and the men he is bringing the case against know "
             "the road he has to walk.",
             pool=_TOUGHS, sites=("the assembly road", "the law stone"),
             giver="the man with the case", places=2,
             epilogue="He reached the stone and spoke. The case went "
                      "against him, which he says was worth it.",
             failure_epilogue="He never reached the stone. The case was "
                              "not heard, and the men who stopped him "
                              "sat through the whole assembly."),
             "pay": 1.20}),
    card("norse/outlawed", "Three years an outlaw", "norse",
         tension=("jarls-vs-thing",),
         faction_edge=("norse/freeholders-outlaw-jarls",), days=(20, 35),
         news="The assembly has made a man an outlaw for three years. He "
              "may not be fed, housed or ferried, and anyone may kill "
              "him. He has gone up into the hills with the men who owe "
              "him.",
         state={"while": ("outlawed",)},
         quest={"post": job(
             "Fed, Housed Or Ferried",
             "The outlaw's sister has been feeding him and the assembly "
             "has found out. One side wants him over the water before "
             "the hunt starts; the other wants the hunt.",
             pool=_TOUGHS, sites=("the hill camp", "the ferry strand"),
             giver="the outlaw's sister", places=2,
             epilogue="He is over the water and out of the law's reach. "
                      "His sister sold a farm to pay for it and says so "
                      "cheerfully.",
             failure_epilogue="The hunt found him in the hills. The men "
                              "who were with him are outlaws now too."),
             "pay": 1.25, "slots": -1}),
    card("norse/land-taking", "The hazel poles go in", "norse",
         tension=("jarls-vs-thing",), wealth=("normal", "prosperous"),
         days=(15, 25),
         news="A younger son has walked a boundary and put hazel poles "
              "in at the corners: unclaimed ground, taken and declared. "
              "The nearest jarl says it is not unclaimed and never was.",
         state={"while": ("land-taking",)},
         quest={"post": job(
             "The Corner Poles",
             "The poles have to stand until the assembly meets. The "
             "jarl's men pull one out every night and the son cannot "
             "watch four corners alone.",
             pool=_TOUGHS, sites=("the staked ground",),
             giver="the younger son",
             epilogue="The poles were standing when the assembly met, "
                      "and the claim held. The son pays in the first "
                      "year of the land.",
             failure_epilogue="The poles were down and the claim died "
                              "with them. The son has taken ship, which "
                              "is what the jarl wanted."),
             "slots": 1, "pay": 1.15}),
    card("norse/blood-feud", "The blood feud", "norse",
         tension=("feud",), faction_edge=("norse/feud-house-kill-rival-house",),
         without=("blood-feud",), days=(20, 35),
         news="Two houses are in feud. Six men are dead between them, "
              "each one a debt on the other side's books, and every "
              "household on this coast is related to one of them.",
         state={"set": ("blood-feud",)},
         encounter={"kinds": ("cutthroat", "bruiser", "soldier"),
                    "where": "road", "as": "one house's men on the road",
                    "skins": {"cutthroat": "Feud-Man",
                              "bruiser": "Axe-Bearer",
                              "soldier": "House-Sworn"},
                    "chance": 0.40}),
    card("norse/weregild", "A man's price", "norse",
         states=("blood-feud",), days=(12, 20),
         news="The law-speaker has put a price on the dead: so many "
              "marks a man, counted by rank, paid in silver or cattle. "
              "Both houses are haggling and neither will be first to "
              "call it settled.",
         state={"clear": ("blood-feud",), "while": ("weregild",)},
         quest={"post": job(
             "Counted By Rank",
             "The silver has to be carried to the paying and counted in "
             "front of both houses. Somebody on one side would rather "
             "the count never happened.",
             pool=_TOUGHS, sites=("the paying ground",),
             giver="the law-speaker",
             epilogue="The price was counted out and taken. The feud is "
                      "off the books, and both houses left by different "
                      "roads.",
             failure_epilogue="The silver never reached the ground. Both "
                              "houses read that as an answer and the "
                              "killing has started again."),
             "pay": 1.25}),

    # == THE WAR LAYER'S FEED ============================================== #
    # The succession cluster: the cards that admit on the crown's
    # circumstance, and move it. They are land-wide over the CROWNED lands,
    # which since the human contraction is all three: Tergal's high chief
    # is elected, but a contested election is a succession like any other.
    # The tuple stays named rather than becoming ANY_LAND so that a later
    # crownless country reads as an exception instead of a silent inclusion.
    card("crown/infant-heir", "The infant heir", _CROWNED,
         succession=("disputed",), without=("regency-on",), days=(25, 40),
         news="The crown has passed to a child and a regency council is "
              "governing in his name. Three of the five councillors have "
              "already stopped attending together.",
         state={"set": ("regency-on",)},
         quest={"post": job(
             "The Council's Fourth Chair",
             "One councillor wants a rival's correspondence out of a "
             "locked room before the next sitting. The rival has hired "
             "for the same room from the other side.",
             pool=_TOUGHS, sites=("the council chamber",),
             giver="the regent's secretary",
             epilogue="The letters are in the right hand and the council "
                      "sat five to nothing on Thursday.",
             failure_epilogue="The letters were burned in the grate and "
                              "the council has not sat at all this "
                              "month."),
             "pay": 1.25, "slots": -1}),
    card("crown/three-branches", "Three branches, three readings",
         _CROWNED, succession=("disputed",), without=("claim-pressed",),
         days=(20, 35),
         news="Three branches of the family claim the inheritance and "
              "each has a reading of the law that gives it to them. Two "
              "of the three have started hiring instead of arguing.",
         state={"set": ("claim-pressed",)},
         quest={"post": job(
             "The Reading Of The Law",
             "The oldest copy of the inheritance law is in a monastery "
             "two days out, and all three branches worked that out on the "
             "same morning.",
             pool=_TOUGHS, sites=("the monastery library",),
             giver="the second branch's advocate",
             epilogue="The copy is in the capital and being read aloud. "
                      "One branch has stopped claiming and started "
                      "negotiating.",
             failure_epilogue="The copy is ash and all three branches now "
                              "say it agreed with them."),
             "pay": 1.25, "reprice": 1.15}),
    card("crown/dead-king-returns", "The dead king comes back", _CROWNED,
         succession=("heirless", "disputed"), chance=0.35, days=(20, 35),
         hook=_PRETENDER_HOOK,
         news="A man calling himself {claimant} has come back from a war "
              "everyone watched him die in. He has the face, the scar and "
              "four old soldiers who swear to him.",
         state={"while": ("pretender",)},
         encounter={"kinds": ("cutthroat", "soldier", "veteran"),
                    "where": "road", "as": "men who swear to the returned "
                                           "king",
                    "skins": {"cutthroat": "Sworn Man",
                              "soldier": "Old Campaigner",
                              "veteran": "The Scar-Witness"},
                    "chance": 0.35},
         quest={"post": job(
             "The Face And The Scar",
             "Somebody at court wants the four old soldiers found and "
             "asked what they were paid. Somebody else wants them "
             "escorted to the capital to say it out loud.",
             pool=_TOUGHS, sites=("the veterans' inn",),
             giver="the court chamberlain",
             epilogue="The four have said their piece in front of "
                      "witnesses, and the capital has made up its mind "
                      "about the face.",
             failure_epilogue="Two of the four are dead and the other two "
                              "have gone over the border. The claim is "
                              "stronger for it."),
             "pay": 1.30, "slots": 1}),
    # The recognition CHAIN: a lifetime of bribes buys the neighbours'
    # acceptance, and the day the king dies it is all void.
    card("crown/bought-recognition", "The bought recognition", _CROWNED,
         succession=("heirless",), without=("recognition-bought",),
         days=None,
         news="A lifetime of gifts has bought the neighbours' agreement "
              "that a daughter may inherit. It is written, sealed, and "
              "worth exactly what the neighbours think of it on the day.",
         state={"set": ("recognition-bought",), "succession": "secure"},
         quest={"post": job(
             "The Last Signature",
             "One neighbour has not signed and wants the sealed copy "
             "brought to him rather than travelling to it. The road runs "
             "past three parties who would rather it never arrived.",
             pool=_TOUGHS, sites=("the sealed road",),
             giver="the crown's envoy",
             epilogue="The last seal is on the document. The succession "
                      "is agreed by everyone who matters, in writing.",
             failure_epilogue="The document was taken on the road. The "
                              "neighbour has heard about it and drawn his "
                              "own conclusions."),
             "pay": 1.25, "reprice": 1.1}),
    card("crown/void-the-day-he-dies", "The paper is void", _CROWNED,
         states=("recognition-bought",), succession=("secure",),
         chance=0.30, days=(20, 35),
         news="The old king is dead and the sealed agreement went with "
              "him. Every neighbour that took the gifts has found a "
              "lawyer, and two of them have found a general.",
         state={"clear": ("recognition-bought",), "set": ("claim-pressed",),
                "succession": "disputed"},
         quest={"reprice": 1.20,
                "slots": -1}),
    card("tergal/tanist-scramble", "Every succession is a scramble",
         "tergal", tension=("clan-vs-clan", "chiefs-vs-mothers"),
         days=(15, 25),
         news="The ablest kinsman inherits here, never merely the eldest "
              "son. That makes strong chiefs and it makes this: every "
              "able cousin on the grass counting spears and calling in "
              "favours at once.",
         state={"while": ("tanist-scramble",), "succession": "disputed"},
         quest={"post": job(
             "Counting Spears",
             "A cousin with a real claim and no herd wants the far camps "
             "visited before the council sits. Two other cousins are "
             "riding the same circuit a day ahead.",
             pool=_TOUGHS, sites=("the far camps",),
             giver="the landless cousin",
             epilogue="The far camps have committed and the council will "
                      "hear it. The cousin owes the party in horses and "
                      "says so in front of witnesses.",
             failure_epilogue="The circuit was ridden by somebody else. "
                              "The cousin has taken his people east and "
                              "is not coming to the council."),
             "pay": 1.25, "slots": 1}),
    # -- the diplomatic instruments: how wars end, and stay ended ---------- #
    # Each is a state one land HOLDS and an authored relation edge the other
    # derives off it -- and each has a card in it, which is the whole point
    # of writing an instrument down instead of narrating a peace.
    card("western/marriage-pact", "The marriage pact", "western",
         tension=("crown-vs-lords", "old-vs-new"),
         without=("marriage-pact", "betrothal-broken"), days=None,
         news="A marriage pact has been sealed with a neighbouring "
              "crown. It ends one war and, if it is ever broken at the "
              "church door, it starts the next one.",
         state={"set": ("marriage-pact",)},
         quest={"post": job(
             "The Bride's Road",
             "The betrothed and half a household have to cross two "
             "provinces to a wedding that several people would like "
             "cancelled.",
             pool=_TOUGHS, sites=("the wedding road", "the border "
                                  "chapel"),
             giver="the crown's herald", places=2,
             epilogue="The party reached the chapel and the pact is "
                      "signed. Two crowns are kin this morning.",
             failure_epilogue="The road went badly and the wedding is "
                              "postponed. Both courts are blaming each "
                              "other in writing."),
             "pay": 1.20, "reprice": 1.1}),
    card("western/broken-betrothal", "The betrothal is broken",
         "western", states=("marriage-pact",), chance=0.30, days=(15, 25),
         news="The betrothal has been broken at the church door. The "
              "insult is public, the dowry is not coming back, and there "
              "is now a reason for a war that only wanted one.",
         state={"clear": ("marriage-pact",), "while": ("betrothal-broken",)},
         quest={"post": job(
             "The Dowry Back",
             "The jilted crown's envoy wants the dowry recovered before "
             "it is spent, and would rather it did not travel by the "
             "main road with a herald in front of it.",
             pool=_TOUGHS, sites=("the treasury road",),
             giver="the jilted crown's envoy",
             epilogue="The dowry went home. The insult stands and the "
                      "accounting does not.",
             failure_epilogue="The dowry is spent and the envoy has gone "
                              "home. The heralds are already talking "
                              "about borders."),
             "pay": 1.25, "reprice": 1.2}),
    card("western/personal-union", "Two crowns, one head", "western",
         succession=("heirless",), without=("personal-union",),
         chance=0.20, days=None,
         news="The crown here has no heir, and the nearest claim belongs "
              "to a king who already wears another one. Separate laws, "
              "separate courts, one man -- and both realms' quarrels now "
              "arrive at the same table.",
         state={"set": ("personal-union",)},
         quest={"reprice": 1.10}),
    # The three READER cards each moved to the land the re-authored edge
    # actually points at (2026-08-22, the card audit): the marriage runs
    # Seraptania -> Phyrascia, the union Phyrascia -> Seraptania, the
    # hostage Tergal -> Vellisclavia and the danegeld Thule -> Phyrascia,
    # so the card that reads each derived word sits in the land wearing it.
    card("phyrascia/kin-claim", "Kin have claims", "phyrascia",
         states=("pact-kin",), days=(15, 25),
         news="The marriage pact made the two crowns kin, and kin have "
              "claims. A cousin from over the water has arrived at court "
              "with a genealogy, a lawyer, and no intention of going "
              "home.",
         quest={"post": job(
             "The Genealogy",
             "The cousin's genealogy has to be checked against the parish "
             "registers of two provinces, and somebody has already been "
             "to one of those churches with a knife and a candle.",
             pool=_TOUGHS, sites=("the parish church", "the second "
                                  "register"),
             giver="the court's own genealogist", places=2,
             epilogue="The registers are copied and the claim is exactly "
                      "as good as it looked. The court has stopped "
                      "laughing.",
             failure_epilogue="Both registers are gone. The claim is now "
                              "whatever the cousin says it is."),
             "pay": 1.20, "reprice": 1.10}),
    card("seraptania/union-inherits", "The union inherits both",
         "seraptania", states=("union-crown",), days=(20, 30),
         news="The two crowns are one head now, and the northern realm's "
              "quarrels have followed the king south. His own lords are "
              "being asked to pay for them.",
         state={"while": ("warrants-sold",)},
         quest={"post": job(
             "Somebody Else's Quarrel",
             "A northern faction has followed the king south to the "
             "court and wants a hearing. The lords here want them off "
             "the road before they get one.",
             pool=_TOUGHS, sites=("the court road",),
             giver="the northern faction's agent",
             epilogue="The northerners got their hearing. Nobody at "
                      "court is pleased and the king heard both "
                      "sides.",
             failure_epilogue="The northerners never reached the court. "
                              "The king has heard one side and made a "
                              "ruling on it."),
             "pay": 1.20, "reprice": 1.1}),
    card("vellisclavia/hostage-in-the-camp", "The heir in the Tergal camp",
         "vellisclavia", states=("hostage-given",), days=(20, 35),
         news="The truce with the steppe was sealed with a child. He is "
              "growing up in the high chief's guard tent, he is safe "
              "while the truce holds, and half this court would break the "
              "truce tomorrow.",
         quest={"post": job(
             "Guard, Meet, Or Steal Back",
             "One faction wants the boy visited and reassured. Another "
             "wants him out of the camp entirely, which ends the truce "
             "the same afternoon.",
             pool=_TOUGHS, sites=("the guard tents",),
             giver="the boy's uncle",
             epilogue="The boy was reached and the truce is intact. Both "
                      "factions think they were served.",
             failure_epilogue="The camp caught the attempt. The truce is "
                              "a dead letter and the boy is under "
                              "guard."),
             "pay": 1.30, "reprice": 1.15}),
    card("phyrascia/danegeld", "The danegeld is raised", "phyrascia",
         states=("danegeld-paid",), days=(15, 25),
         news="The northern fleet is being paid not to land, and this "
              "kingdom is paying. The collectors say it is cheaper than "
              "a war. The shires have done the arithmetic and disagree.",
         quest={"post": job(
             "Cheaper Than A War",
             "The tribute chest goes to the coast on Thursday with a "
             "small escort, because a large one looks like an army. "
             "Three villages on the route have decided it is not going.",
             pool=_TOUGHS, sites=("the coast road",),
             giver="the shire's collector",
             epilogue="The chest reached the strand and the ships did "
                      "not land this season. The kingdom paid twice: "
                      "once in silver and once in temper.",
             failure_epilogue="The chest never reached the coast. The "
                              "sea-kings have taken that as an answer."),
             "pay": 1.25, "slots": -1}),
)

# --------------------------------------------------------------------------- #
# The religion content (2026-08-11): worldsim.md's religion packets
# --------------------------------------------------------------------------- #
# What religion owns that politics does not: WORSHIP, RITE, and the parish's
# daily texture. Politics kept church POWER, and where a packet entry was a
# political card wearing a stole -- the interdict, the militant order, the
# witch-finder, the tribunal's penance -- it stayed in the politics deck and
# is referenced here, never duplicated (the dedupe doctrine).
#
# Three directives from the design round govern every line below. THE PACT
# STAYS OUT: nobody in the world knows of it and no card reacts to it. NO
# THEOLOGY RULING: the game never decides which land's religion is true, so
# each card is written from inside its own land and the contradictions
# between them are content. And TEMPLE SERVICES ARE PRICED, NOT PENITENTIAL:
# healing, burial and blessing are OPTIONS at the bottom of this file, and
# the sin/penance wiring is deliberately not designed.
#
# The gate is the same one politics uses: most cards name a TENSION, so a
# land whose shrines are at war never draws the abbey's cards at all,
# and the packet stays a wide pool instead of a content budget. What is left
# ungated is one card a land at most, kept rare by its own `chance`.

_HERMIT_HOOK = _authority_hook("hermit", "the walled-in hermit", "hermit")
_TALENT_HOOK = _authority_hook("wild-talent", "the wild talent", "talent")

RELIGION_CARDS = (
    # == the west: THE PARISH IS THE SECOND STATE ========================= #
    # The relic CHAIN: a town steals a saint, and the synod that has to rule
    # on which of three skulls is his is the card a season later.
    card("western/relic-theft", "The relic is stolen", "western",
         tension=("shrine-vs-shrine",),
         faction_edge=("western/shrines-steal-from-rival-shrines",),
         without=("relic-hunt",), days=(15, 25),
         news="A shrine town has stolen its rival's relic in the night, and "
              "the doctrine is that the saint consented -- the theft could "
              "not have worked otherwise. The pilgrim road has already "
              "moved.",
         state={"set": ("relic-hunt",)},
         quest={"post": job(
             "The Saint Goes Home",
             "The robbed shrine wants its saint back before the pilgrim "
             "season. The thieves are a whole town, and the town says the "
             "saint chose them.",
             pool=_TOUGHS, sites=("the rival shrine", "the pilgrim road"),
             giver="the robbed shrine's abbot",
             epilogue="The relic is back in its own case, and both towns "
                      "now have a written account of what the saint "
                      "wanted.",
             failure_epilogue="The saint stayed where he was taken. The "
                              "pilgrim road runs through the other town "
                              "now, and the old one is emptying."),
             "pay": 1.20}),
    card("western/third-skull", "The third skull", "western",
         states=("relic-hunt",), days=(12, 20),
         news="Three shrines own the same saint's skull. A synod has "
              "ordered authentication by miracle, and two of the three "
              "abbots already know what the test will find.",
         state={"clear": ("relic-hunt",), "while": ("bones-tested",)},
         menu={"lodging": 1.25},
         quest={"post": job(
             "Authentication By Miracle",
             "The synod's examiner is walking to all three shrines with a "
             "box and a clerk. Two of the shrines would rather he did not "
             "arrive at the third.",
             pool=_TOUGHS, sites=("the shrine road", "the synod hall"),
             giver="the synod's examiner",
             epilogue="The examiner reached all three shrines and wrote "
                      "down what he found. One abbot has left for the "
                      "capital.",
             failure_epilogue="The examiner never finished his round. All "
                              "three shrines are selling badges as the "
                              "true one."),
             "pay": 1.15}),
    card("western/holy-well", "The well starts healing", "western",
         tension=("shrine-vs-shrine",), wealth=("normal", "prosperous"),
         days=(15, 25),
         news="A well outside the village has started healing people, and "
              "the church has not ruled on it yet. The innkeepers have an "
              "opinion. So does the priest whose font sits empty.",
         state={"while": ("holy-well",)},
         quest={"post": job(
             "The Unlicensed Miracle",
             "The bishop's man is coming to license the well, suppress it, "
             "or quietly improve it. The village means to be sure he "
             "arrives in the right frame of mind, and so does the parish "
             "priest, differently.",
             pool=_TOUGHS, sites=("the well road", "the empty church"),
             giver="the bishop's man",
             epilogue="The well is licensed, and the takings are split in "
                      "writing. Everyone is equally unhappy, which the "
                      "clerk calls a settlement.",
             failure_epilogue="The well was filled in on a Tuesday night. "
                              "It started again on Thursday."),
             "slots": 1}),
    card("western/feast-week", "The feast days stop the work", "western",
         tension=("abbey-vs-village",), days=(8, 14),
         news="Feast days claim a third of the year here, and working them "
              "is an offence. The harvest is standing ripe under a week of "
              "them, and the abbey will not move a single one.",
         state={"while": ("feast-lock",)},
         quest={"post": job(
             "Ripe Under The Feast",
             "A village with no lord over it means to bring its harvest "
             "in during the feast anyway, and wants men between the "
             "carts and whoever the abbey sends to count them.",
             pool=_TOUGHS, sites=("the standing field",),
             giver="the village headman",
             epilogue="The harvest is in and the abbey has a list of "
                      "names. The village says the list can be read at "
                      "the next feast.",
             failure_epilogue="The carts were turned back and the grain "
                              "stood another week. Half of it is on the "
                              "ground now."),
             "slots": -1, "pay": 1.15}),
    card("western/the-oblate", "The abbey's boy wants out", "western",
         tension=("abbey-vs-village",),
         faction_edge=("western/abbey-holds-village",), days=(15, 25),
         news="A boy given to the abbey at seven wants out at fifteen. The "
              "abbey holds his labour, his inheritance and the law, and "
              "his mother has started asking who in the county does not.",
         state={"while": ("abbey-suit",)},
         quest={"post": job(
             "A Year And A Day",
             "The boy is going over the abbey wall on Friday whatever "
             "anyone hires. His mother is paying for an escort to the town "
             "gate; the abbey is paying to have him back before it. Both "
             "sides are at the same inn.",
             pool=_TOUGHS, sites=("the abbey wall", "the town gate"),
             giver="the boy's mother",
             epilogue="The boy is behind the town gate and the year has "
                      "started running. The abbey is writing to the "
                      "bishop about it.",
             failure_epilogue="The boy is back inside the abbey, and the "
                              "next one who tries this will get the same "
                              "answer faster."),
             "pay": 1.20}),
    card("western/the-hermit", "The hermit at the wall", "western",
         tension=("abbey-vs-village",),
         faction_edge=("western/village-petitions-abbey",),
         days=(20, 30), hook=_HERMIT_HOOK,
         news="{hermit} has been walled into the church with one window on "
              "the street for thirty years. The village brings her its "
              "quarrels, and she has watched every single thing that has "
              "happened out there.",
         state={"while": ("hermit-window",)},
         quest={"post": job(
             "The One Witness",
             "The walled-in hermit saw who did it and will say so to the "
             "court. Two families would rather she did not, and there is "
             "exactly one window between her and the street.",
             pool=_TOUGHS, sites=("the church wall", "the county court"),
             giver="the walled-in hermit",
             epilogue="The hermit's account is read into the county roll. "
                      "She is still at her window and the street is very "
                      "polite this week.",
             failure_epilogue="The window is bricked up and the hermit is "
                              "gone. Nobody in the village saw who did "
                              "that either."),
             "slots": 1, "pay": 1.10}),
    # == The Sun communion: ONE CHURCH, TWO RITES ========================== #
    # The one card that belongs to two lands, because the argument does:
    # every joint synod ends one insult short of the split. Narrowed by the
    # card audit (2026-08-22) to the two CROWNS that hold the quarrel --
    # Byzantium, the southern heir and the death-face's home, and
    # Seraptania, the western church's eldest daughter. It is the schism
    # clock's own card and the clock runs between exactly those two.
    card("communion/the-synod", "The joint synod",
         ("byzantium", "seraptania"), states=("schism-near",),
         days=(10, 18),
         news="The two rites have called a joint synod. The north says the "
              "southern death-face is creeping heresy; the south says a "
              "faith that refuses death its face is what makes death "
              "monstrous. Both are right and neither will yield.",
         quest={"post": job(
             "One Insult Short",
             "The synod's delegates have to reach the hall and get home "
             "again, through a town that has already picked a side. The "
             "bishop is paying for the whole journey and does not want a "
             "single delegate hurt on either side.",
             pool=_TOUGHS, sites=("the synod hall", "the cathedral road"),
             giver="the visiting bishop",
             epilogue="The synod broke up without a split, which is what "
                      "everybody calls a success. Both rites went home "
                      "saying they had won.",
             failure_epilogue="A delegate was beaten in the street and the "
                              "synod broke up over it. Both rites are "
                              "writing the account that will be read in "
                              "fifty years."),
             "pay": 1.25, "slots": -1}),

    # == BYZANTIUM: WHICH FACE RULES ====================================== #
    # The pendulum calendar, the death-rite and the carnival are the
    # southern HEIR's, not the whole southern culture's (2026-08-22, the
    # card audit; the call was settled at design time in designlog (J)).
    # Andalusia and Umaia wear the culture-generic south and nothing of
    # the death-face; Byzantium carries this cluster, its own tension and
    # its own two faction edges.
    card("byzantium/penance-season", "The penitential season",
         "byzantium", tension=("penitents-vs-carnival",),
         faction_edge=("byzantium/penitents-denounce-carnival",),
         without=("carnival-on",), days=(15, 25),
         news="The hooded columns are out, the statues are veiled and the "
              "flagellants march the main street at dusk. Attendance is "
              "close to universal and so is the muttering about it.",
         state={"while": ("penance-season",)},
         quest={"post": job(
             "The Column's Road",
             "A flagellant column is walking to the shrine through three "
             "districts that would rather it did not. The brotherhood "
             "wants it to arrive with the same number of men it left "
             "with.",
             pool=_TOUGHS, sites=("the procession road",),
             giver="the brotherhood's warden",
             epilogue="The column reached the shrine intact. The warden "
                      "pays without looking up.",
             failure_epilogue="The column was broken up in the third "
                              "district. The season's sermons are about "
                              "nothing else now."),
             "reprice": 0.90}),
    card("byzantium/carnival", "Carnival", "byzantium",
         tension=("penitents-vs-carnival",),
         faction_edge=("byzantium/carnival-outnumber-penitents",),
         without=("penance-season",), days=(8, 14),
         news="Carnival is on: masks, licence and the world upside down. "
              "Sins confessed masked are absolved wholesale, the theology "
              "of that is contested, and the last night is the best time "
              "of the year to be forgiven or to disappear.",
         state={"while": ("carnival-on",)},
         quest={"post": job(
             "Under The Mask",
             "The city watch cannot tell one masked man from another and "
             "has given up trying. A merchant house wants its own people "
             "walked home every night of the season, and does not want "
             "them counted on the way.",
             pool=_TOUGHS, sites=("the masked street", "the water stairs"),
             giver="the merchant house's steward",
             epilogue="Everyone got home every night. The steward pays in "
                      "a mask and does not give a name.",
             failure_epilogue="Two of the household did not come back, and "
                              "under carnival law nobody was anybody that "
                              "night."),
             "slots": 1, "pay": 1.15}),
    card("byzantium/day-of-the-dead", "The day of the dead", "byzantium",
         chance=0.30, days=(2, 3),
         news="Tonight the dead are guests. The tombs are picnicked in, "
              "plates are set at the family tables, and the graveyard is "
              "lit like a fair. Whether anyone actually comes is not a "
              "question the city asks out loud.",
         state={"while": ("dead-abroad",)},
         quest={"post": job(
             "A Plate At The Table",
             "A house wants its family tomb sat with all night, and will "
             "not say whether the worry is robbers or guests. The rate is "
             "the same either way.",
             pool=_UNDEAD, sites=("the family tomb",),
             giver="the house's eldest daughter",
             epilogue="The night passed. The plates were emptied, which "
                      "the family takes as an answer and does not "
                      "explain.",
             failure_epilogue="The tomb was open in the morning and the "
                              "plates were on the floor. The family has "
                              "stopped setting them."),
             "pay": 1.20}),
    card("byzantium/two-hoods", "Two brotherhoods, one corpse",
         "byzantium", tension=("penitents-vs-carnival",), days=(8, 14),
         news="A notable died in the street and two hooded burial "
              "brotherhoods reached him at once. Both are anonymous by "
              "rule, both have the paperwork, and the standoff is being "
              "conducted in full regalia.",
         state={"while": ("two-hoods",)},
         quest={"post": job(
             "In Full Regalia",
             "One brotherhood means to carry the body off tonight. The "
             "other means to be standing over it. The dead man's widow is "
             "paying whoever gets him into the ground she chose.",
             pool=_TOUGHS, sites=("the chapel steps",),
             giver="the dead man's widow",
             epilogue="The body is in the widow's ground. Both "
                      "brotherhoods have written to the archbishop about "
                      "the other one.",
             failure_epilogue="The body went to whichever brotherhood was "
                              "faster. The widow is not told which."),
             "pay": 1.15}),
    card("byzantium/debate-riot", "The disputation riot", "byzantium",
         tension=("penitents-vs-carnival",), days=(8, 14),
         news="The public theology debate on the two faces was staged as "
              "entertainment and wagered on like a duel. It ended in "
              "faction fighting in the square, with clubs.",
         state={"while": ("debate-riot",)},
         quest={"post": job(
             "The Second Session",
             "The debate is scheduled to continue tomorrow and both "
             "wings have brought friends. The magistrate wants the square "
             "held and the debate finished, in that order.",
             pool=_TOUGHS, sites=("the debate square",),
             giver="the city magistrate",
             epilogue="The second session finished and was written down. "
                      "Nobody was killed, which the magistrate calls a "
                      "verdict.",
             failure_epilogue="The square went over again and the "
                              "magistrate has banned public theology for "
                              "a year. Everyone is doing it in cellars."),
             "slots": -1, "pay": 1.20}),

    # == Thule: THE GROVE, THE SEA AND THE POLE ============================ #
    # (2026-08-22, the norse packet.) Worship here is a place and a count,
    # not a creed: an old stand of trees, nine of every kind, and a priest
    # who keeps the tally. The new faith arrives by ship with a foreign
    # king's silver behind it, which is why it is a POLITICAL quarrel and
    # sits on its own tension.
    card("norse/grove-sacrifice", "The great sacrifice", "norse",
         tension=("old-vs-new-gods",), days=(10, 16),
         news="The great sacrifice is at the grove: nine of every kind, "
              "horses and dogs and men, and the bones stay where they "
              "fall. Every district is expected and the priest keeps the "
              "count of who came.",
         state={"while": ("grove-sacrifice",)},
         menu={"goods": 1.15},
         quest={"post": job(
             "Nine Of Every Kind",
             "The grove is short of its ninth man and the priest has "
             "started looking at strangers. A district that will not "
             "send one this year wants the count made up some other way, "
             "and is paying for the argument.",
             pool=_TOUGHS, sites=("the grove path",),
             giver="the district's speaker",
             epilogue="The count was made up without anyone from that "
                      "district in it. The priest wrote the year down "
                      "as complete and said nothing else.",
             failure_epilogue="The count was made up out of that "
                              "district after all. Two families have "
                              "left the coast entirely."),
             "pay": 1.25}),
    card("norse/curse-pole", "The pole with a name on it", "norse",
         tension=("old-vs-new-gods",),
         faction_edge=("norse/grove-priests-curse-missionaries",),
         days=(12, 20),
         news="A carved pole is up on the headland with a horse's head "
              "on top of it and a name cut into the shaft. The name "
              "belongs to the missionary who has been buying converts, "
              "and the land-spirits are being asked to turn on him.",
         state={"while": ("curse-pole",)},
         quest={"post": job(
             "The Head On The Pole",
             "The missionary wants the pole down and the name unsaid "
             "before the tide turns. The grove priest has men sitting on "
             "the headland in shifts.",
             pool=_TOUGHS, sites=("the headland",),
             giver="the missionary",
             epilogue="The pole is down and the name was unsaid out "
                      "loud. The grove priest walked away without "
                      "arguing, which nobody here finds comforting.",
             failure_epilogue="The pole is still up and a second name "
                              "has been cut under the first. The "
                              "missionary has taken ship."),
             "pay": 1.20}),
    card("norse/drowned-crew", "A ship did not come home", "norse",
         chance=0.35, days=(10, 18),
         news="A ship went out and did not come back. The drowned belong "
              "to the sea and are not looked for, so the families are "
              "holding the ale-feast without bodies -- and one of the "
              "crew has been seen on the strand since.",
         state={"while": ("drowned-crew",)},
         quest={"post": job(
             "The Ale-Feast Without Bodies",
             "Somebody who was on that ship has been walking up from the "
             "water at night and going to his own house. His widow wants "
             "him put back where the sea keeps its own.",
             pool=_UNDEAD, sites=("the night strand", "the drowned "
                                  "man's house"),
             giver="the drowned man's widow", places=2,
             epilogue="He is back in the water with a stone on him and "
                      "the house has been slept in since. The widow "
                      "pays out of the ale-feast money.",
             failure_epilogue="He is still coming up at night, and two "
                              "more of the crew have started as well. "
                              "The house is empty now."),
             "pay": 1.30}),

    # == Tergal: THE PRACTICE, NOT THE CREED =============================== #
    card("tergal/called-child", "The called child", "tergal",
         tension=("white-vs-black",), days=(15, 25),
         news="A chief's child has the call: the sickness that takes the "
              "marked one, whose only cure is initiation under a living "
              "shaman. Refusing it ends in death or a broken mind, and the "
              "family is asking whether it can be refused anyway.",
         state={"while": ("called-child",)},
         quest={"post": job(
             "The Long Ride To The Teacher",
             "The family will pay to have the child taken nine days across "
             "the grass to a teacher who can finish it -- or, for the same "
             "money, to have the child hidden from the spirits, which "
             "every shaman says cannot be done.",
             pool=_TOUGHS, sites=("the open grass", "the teacher's camp"),
             giver="the chief's wife",
             epilogue="The child reached the teacher and the sickness has "
                      "a shape now. The camp is easier about it than the "
                      "family is.",
             failure_epilogue="The child never reached the teacher. The "
                              "family has stopped saying what happened, "
                              "which the camp reads as an answer."),
             "pay": 1.25}),
    card("tergal/river-fouled", "The river was fouled", "tergal",
         chance=0.30, days=(8, 14),
         news="Somebody washed in the river. Running water is never fouled "
              "here, a tent's threshold is never stepped on, and the dead's "
              "names go unspoken -- and the fine for the first is paid in "
              "livestock like everything else.",
         state={"while": ("river-fouled",)},
         quest={"post": job(
             "Paid In Livestock",
             "The fine is set at eleven head and the man who owes it has "
             "none. The camp will accept the herd of whoever brings it, "
             "and there is a herd four days out with a thin guard on it.",
             pool=_TOUGHS, sites=("the river camp", "the far pasture"),
             giver="the camp's law-speaker",
             epilogue="The fine is paid, the river is clean in law, and "
                      "the herd it came off is somebody else's problem "
                      "now.",
             failure_epilogue="The fine is unpaid and the camp has begun "
                              "reading it as a feud instead of a debt."),
             "pay": 1.10}),
    card("tergal/black-tent", "The black shaman is wanted", "tergal",
         tension=("white-vs-black",),
         faction_edge=("tergal/black-shaman-serves-white-shamans",),
         days=(12, 20),
         news="The herds are sickening and the white shamans cannot stop "
              "it. Everyone knows whose tent to visit after dark: the one "
              "camped outside the ring, paid double, and needed.",
         state={"while": ("black-tent",)},
         quest={"post": job(
             "Outside The Ring Of Tents",
             "The dark one will come, for a price and an escort, and will "
             "not walk the last stretch alone. What is following the herds "
             "is following him too.",
             pool=_UNDEAD, sites=("the outside tent", "the sick pasture"),
             giver="the camp's herd-master",
             epilogue="The herds have stopped dying and the dark one is "
                      "back outside the ring. Nobody thanks him where "
                      "anyone can hear it.",
             failure_epilogue="He never reached the pasture. The camp is "
                              "moving, and it is not saying where."),
             "pay": 1.30}),
    card("tergal/foreign-graves", "The foreign graveyard", "tergal",
         tension=("white-vs-black",), days=(15, 25),
         news="The dead go to the birds on the platforms here; burying a "
              "body in earth MAKES a ghost. Somebody has put a foreign "
              "graveyard on the plain, and the camps have started "
              "detouring around it.",
         state={"while": ("foreign-graves",)},
         quest={"post": job(
             "Put Them On The Platforms",
             "The camps want the foreign graveyard emptied and its dead "
             "laid out properly. Whoever buried them has views about that, "
             "and so, by now, do the dead.",
             pool=_UNDEAD, sites=("the foreign graveyard",),
             giver="the white shaman",
             epilogue="The graves are open, the dead are on the platforms, "
                      "and the birds have come. The detour is off.",
             failure_epilogue="The graveyard is still there and larger. "
                              "Two camps have moved their whole season "
                              "around it."),
             "pay": 1.25}),
    card("tergal/cairn", "The pass-spirit is offended", "tergal",
         tension=("white-vs-black",), days=(10, 18),
         news="Every spring, pass and mountain has an owner. A traveller "
              "went over the pass without adding a stone to the cairn, and "
              "the misfortune chain has started at the near end of it.",
         state={"while": ("cairn-angry",)},
         quest={"post": job(
             "A Stone At The Pass",
             "The shaman will carry the apology to the pass himself and "
             "wants company to the top. What has been taking the horses "
             "up there does not stop at the treeline.",
             pool=_BEASTS, sites=("the high pass",),
             giver="the white shaman",
             epilogue="The stone is on the cairn and the apology was "
                      "spoken out loud. The pass is quiet.",
             failure_epilogue="The apology was not delivered. The camps "
                              "are going the long way round and losing "
                              "four days a crossing."),
             "pay": 1.15}),

)

# --------------------------------------------------------------------------- #
# The magic content (2026-08-11): worldsim.md's magic packets
# --------------------------------------------------------------------------- #
# THE MARGIN is the doctrine every card below is written against: magic is
# real, known and SMALL. Everyone is secondhand familiar with its minor forms
# and almost nobody has seen a great working; no throne, market or war is
# decided by it. That is why these cards are gated hard and rolled rarely,
# and why not one of them changes a wealth band.
#
# CONDUCT, NOT CREED is the other: there is no inquisition against casting as
# such, and a caster playthrough is never dominated by automatic hostility.
# What gets a caster hunted is what they DID -- THE HUNT below is a paid
# trade, not a holy office, and its target is named by conduct.
#
# The five limits ride the content rather than the code: the gift is BORN
# (the wild talent, the recruiters, the called child in the religion packet),
# the THEORY is hoarded (the three teaching options), the COSTS are real (the
# reagent road), the DANGER is the untrained talent, and the DARK SHORTCUT is
# what the hunt is hired about.

MAGIC_CARDS = (
    # -- land-agnostic: the gift, and what the world does about it --------- #
    # The talent CHAIN, and the one that runs in every land: a gift with no
    # theory behind it goes off, and the trade that answers is the next card.
    card("magic/wild-talent", "The wild talent", ANY_LAND,
         chance=0.10, without=("talent-loose", "hunt-up"), days=None,
         hook=_TALENT_HOOK,
         news="A peasant called {talent} blew a man apart in a market "
              "quarrel and ran. Great gift, no training, no control: posse, "
              "recruiters, witchhunters and pity are all converging, and "
              "the target is one frightened person.",
         state={"set": ("talent-loose",)},
         quest={"post": job(
             "Three Employers, One Target",
             "The dead man's family wants the talent dead. A wizard's "
             "recruiter wants it delivered alive to a teacher. The village "
             "that raised it wants it gone quietly. All three are paying, "
             "and the talent is asleep in a barn nine miles out.",
             pool=_CASTERS, sites=("the burnt barn", "the hedge road"),
             giver="the wizard's recruiter",
             epilogue="The talent is out of the county alive and under "
                      "somebody's roof. Which of the three employers is "
                      "satisfied depends on who is asked.",
             failure_epilogue="The talent got away again, further out and "
                              "worse frightened. The next market it walks "
                              "into will hear about it."),
             "pay": 1.30}),
    card("magic/the-hunt", "The hunt is posted", ANY_LAND,
         states=("talent-loose",), days=(12, 20),
         news="Witchhunting is a trade, not a holy office, and one is "
              "posted: a named target, a price by the head, and specialists "
              "on the road for it. Nobody here objects to casting. They "
              "object to what this one did.",
         state={"clear": ("talent-loose",), "while": ("hunt-up",)},
         quest={"post": job(
             "Paid By The Head",
             "The posted price is real and so are the men already out "
             "collecting it. The contract does not say alive, and the "
             "specialists who took it first are not the sort to share a "
             "bounty.",
             pool=_CASTERS, sites=("the hunt's ground", "the hunters' inn"),
             giver="the hunt's paymaster",
             epilogue="The hunt is closed and paid. The paymaster writes "
                      "the name off a list he does not show anybody.",
             failure_epilogue="The hunt is still open and the price has "
                              "gone up. So has the number of people on "
                              "the road collecting it."),
             "pay": 1.25}),
    card("magic/recruiters", "The scouts are out",
         ("western", "southern"), chance=0.25, days=(12, 20),
         news="Talent born poor stays untrained, so the wizard "
              "organizations look for it: the scout at the fair, the "
              "family paid off, the tested orphan. Two of the scouts are "
              "working the villages this month and one of them is not "
              "asking first.",
         state={"while": ("recruiters-out",)},
         quest={"post": job(
             "The Tested Orphan",
             "A scout wants an escort round nine villages and a testing "
             "table carried. A family four villages back wants the child "
             "the last round took brought home. The scout's paperwork is "
             "in order, which is not the same thing.",
             pool=_TOUGHS, sites=("the village round", "the scout's wagon"),
             giver="the wizards' scout",
             epilogue="The round is finished and two children are signed "
                      "for. The families were paid, and one of them "
                      "spent it the same day.",
             failure_epilogue="The round broke up in the fourth village. "
                              "The scout is writing a report, and the "
                              "villages are hiding their bright ones."),
             "pay": 1.15}),
    card("magic/reagent-road", "The reagent road", "southern",
         chance=0.30, days=(12, 20),
         news="Great workings want rare and expensive reagents: crystal, "
              "specific animal parts, the wool of golden sheep. A "
              "consignment is moving, and compact high-value goods with "
              "nervous provenance move the same way everywhere.",
         state={"while": ("reagents-moving",)},
         quest={"post": job(
             "Four Wagons And One Wizard",
             "The consignment goes through in four wagons with one wizard "
             "riding it, and he will not say what is in the third one. "
             "Everybody on the road already knows the route.",
             pool=_TOUGHS, sites=("the reagent road", "the bonded yard"),
             giver="the consignment's factor",
             epilogue="Four wagons in, four wagons out, and the factor "
                      "pays without opening the third one.",
             failure_epilogue="The third wagon is gone. The factor has "
                              "posted its contents as a description "
                              "rather than a list, which tells the "
                              "fences enough."),
             "pay": 1.25}),

    # -- the south: THE ACADEMY ------------------------------------------- #
    card("southern/basement-children", "The basement children",
         "southern", tension=("academy-vs-tribunal",),
         faction_edge=("southern/tribunal-watches-academy",),
         days=(15, 25),
         news="The academy's scouts run the recruiting at scale, and the "
              "children taken young for the gift are raised in the "
              "basement by an institution that wanted the talent, not the "
              "child. Somebody has finally asked for a count of them.",
         state={"while": ("basement-open",)},
         quest={"post": job(
             "A Count Of The Basement",
             "The tribunal's inspector wants every child in the basement "
             "listed by name. The faculty wants the list to come out even. "
             "Three of the children have worked out what a list is for.",
             pool=_CASTERS, sites=("the academy basement",),
             giver="the tribunal's inspector",
             epilogue="The list is written and two names on it did not "
                      "match anything the faculty had. Both children are "
                      "in the inspector's keeping.",
             failure_epilogue="The count came out even, which everybody "
                              "involved knows is the wrong answer. The "
                              "basement door has a new lock."),
             "pay": 1.20, "slots": -1}),
    # The necromancy CHAIN: the affinity keeps surfacing here, wins some
    # acceptance, and the next scandal buries it again. BYZANTIUM's alone
    # since the card audit (2026-08-22): the affinity stands on the
    # death-face rite, and the death-face rite is the southern heir's.
    card("byzantium/necromancy-open", "Necromancy is tolerated again",
         "byzantium", tension=("academy-vs-tribunal",),
         without=("necromancy-open", "necromancy-purged"), days=None,
         news="The death-face rite makes necromancy thinkable here, and the "
              "academy has a chair in it again this decade. The northern "
              "rite is already calling the appointment proof of the "
              "creeping heresy.",
         state={"set": ("necromancy-open",)},
         quest={"post": job(
             "The New Chair",
             "The new professor's demonstration is public, ticketed and "
             "in three days. The tribunal has bought forty of the "
             "tickets. The faculty wants the hall held and the "
             "demonstration finished.",
             pool=_UNDEAD, sites=("the demonstration hall",),
             giver="the academy's warden",
             epilogue="The demonstration finished and was written up. The "
                      "tribunal's forty took notes and left early.",
             failure_epilogue="The hall went over in the second hour and "
                              "the demonstration is what everyone in the "
                              "city saw. The chair will not last the "
                              "year."),
             "pay": 1.20}),
    card("byzantium/necromancy-purge", "The academy burns its chair",
         "byzantium", states=("necromancy-open",), days=(40, 60),
         news="The scandal came, as it always does. The chair is abolished, "
              "the notes are burning in the quadrangle, and everyone who "
              "held a place under it has been examined and sent away.",
         state={"clear": ("necromancy-open",),
                "while": ("necromancy-purged",)},
         quest={"post": job(
             "What The Fire Missed",
             "Three of the examined men left with their working notes and "
             "one of them left with something else. The warden wants all "
             "of it back inside the walls before the tribunal finds it "
             "outside them.",
             pool=_CASTERS, sites=("the burnt quadrangle", "the coast road"),
             giver="the academy's warden",
             epilogue="The notes are back in the academy and the tribunal "
                      "was told nothing. Two of the three men are abroad "
                      "and one is not accounted for.",
             failure_epilogue="The notes went south with the men who wrote "
                              "them, and there is a market for them "
                              "there."),
             "pay": 1.25}),

    # -- Tergal: THE PRACTICE (religion owns the rest) --------------------- #
    # The dedupe doctrine: the call, the white and black shamans, the
    # weather-worker and taboo law are all in the religion packet. What
    # magic adds here is that a shaman is ARMAMENT, and that display magic
    # is prestige -- and prestige is power on this grass.
    card("tergal/flicker-dance", "The flicker dance", "tergal",
         tension=("clan-vs-clan", "chiefs-vs-mothers"),
         wealth=("normal", "prosperous"), days=(8, 14),
         news="Where there is a ritual there is an art: the fire dance, and "
              "the flicker dance where a dancer blinks out of sight and "
              "back across the circle. Two camps have brought their best "
              "to the same fire, and a warband counts its shaman in its "
              "strength.",
         quest={"post": job(
             "Best At The Fire",
             "The rival camp's dancer is being paid to fail, and the man "
             "paying has hired the road between here and the fire. The "
             "chief wants his own dancer at the circle on time and "
             "unbroken.",
             pool=_TOUGHS, sites=("the long road", "the fire circle"),
             giver="the chief's herald",
             epilogue="The dancer was at the fire and the camp has the "
                      "prestige, which here is the same word as power.",
             failure_epilogue="The dancer never reached the circle. The "
                              "other camp danced alone, and its chief has "
                              "been given three horses he did not ask "
                              "for."),
             "slots": 1, "pay": 1.15}),

    # -- Thule: THE SEER AND THE OATH ------------------------------------- #
    # (2026-08-22, the norse packet.) Two cards, the same shape as the
    # steppe's one: what magic ADDS here is a woman who is asked what is
    # already fixed, and a dozen men who make themselves into a weapon for
    # one morning. The bought wind is the packet's option, at the bottom.
    card("norse/seer-speaks", "The seer speaks", "norse",
         chance=0.30, days=(15, 25),
         news="The seer was set on the high seat, sung to, and asked. She "
              "named the men who will not see the spring and one of them "
              "was in the room. Nobody here argues with the thread once "
              "it is spoken.",
         state={"while": ("seer-spoke",)},
         quest={"post": job(
             "One Of Them Was In The Room",
             "A named man means to be somewhere else by spring and wants "
             "an escort over the fells. His own household has stopped "
             "feeding him, on the grounds that it would be wasted.",
             pool=_BEASTS, sites=("the fell crossing",),
             giver="the named man",
             epilogue="He is over the fells and out of the district. "
                      "Whether that counts against the thread is what "
                      "the whole coast is arguing about.",
             failure_epilogue="He did not get over the fells. The seer's "
                              "price has gone up and the queue at her "
                              "door is longer."),
             "pay": 1.25}),
    card("norse/berserk-oath", "The oath is drunk", "norse",
         tension=("sea-vs-land", "feud"), chance=0.40, days=(10, 18),
         news="A dozen men have drunk the oath and gone bear-shirt: no "
              "mail, no shield and no stopping until it is finished. "
              "They are worth twenty men for one morning and nothing at "
              "all afterwards, and somebody has paid for the morning.",
         state={"while": ("berserks",)},
         quest={"post": job(
             "Worth Twenty Men For One Morning",
             "The oath-drinkers are walking up the shore path to a farm "
             "they have been pointed at, and the man who bought the oath "
             "has changed his mind about it since.",
             pool=_TOUGHS, sites=("the shore path",),
             giver="the man who bought the oath",
             epilogue="They were stopped on the path. Two of them will "
                      "not get up again and none of them remembers what "
                      "the morning was about.",
             failure_epilogue="They reached the farm. The district is "
                              "counting what is left of it, and the man "
                              "who paid is denying that he paid."),
             "pay": 1.30}),

    # -- the west: THE TOWERS --------------------------------------------- #
    card("western/tower-door", "The tower door opens", "western",
         traits=("spell-friendly", "gifted", "brilliant"), days=(15, 25),
         news="Barely an organization: grumpy old wizards in scattered "
              "towers, hoarding books and meeting mostly to feud. One of "
              "them has let it be known that silver might open his door, and "
              "that volunteering as the subject of an experiment opens it "
              "faster.",
         state={"while": ("tower-open",)},
         quest={"post": job(
             "The Subject Of The Experiment",
             "The tower wizard needs three things fetched and one thing "
             "held still, and is prepared to teach whoever survives the "
             "fourth part. He has been asked what happened to the last "
             "apprentice and has not answered.",
             pool=_CASTERS, sites=("the tower stair", "the wizard's cellar"),
             giver="the tower wizard",
             epilogue="The experiment finished and the wizard is teaching. "
                      "The apprenticeship ends at his whim, which he "
                      "mentions daily.",
             failure_epilogue="The experiment did not finish. The tower "
                              "door is shut again and the wizard is "
                              "advertising for a new subject."),
             "pay": 1.30}),

)

CARDS = CARDS + POLITICS_CARDS + RELIGION_CARDS + MAGIC_CARDS
CARDS_BY_KEY = {c["key"]: c for c in CARDS}

GRAIN_FAILS = ("harvest-failed", "drought")     # what stops a granary: the
                                                # harvest, or the season that
                                                # took it (the economy floor
                                                # put the DROUGHT at the head
                                                # of the grain edges -- the
                                                # weather rung's slow state
                                                # reaching the other lands'
                                                # boards and shelves)

# THE RELATIONS, authored LAND TO LAND (2026-08-22, the norse packet's own
# session). Session 2 authored them by CULTURE and took the cross product,
# which reached every land cheaply and was deliberately crude -- Phyrascia
# derived `pact-kin` off Umaia's marriage pact, and every western kingdom
# ate every other one's grain. This table replaces it: twenty hand-placed
# edges between named countries, drawn on the map the overlay actually
# paints. The record and the one-hop derivation are unchanged, and
# `RELATIONS` is still the expansion of `_RELATIONS` -- it is simply a 1:1
# expansion now, because every `from` and `to` below is a land.
_RELATIONS = (
    # -- THE TWO GRAIN ROADS ---------------------------------------------- #
    # The Baltic one and the Nile one. Thule grows barley and not much of
    # it, so its bread comes up the Baltic out of the Vellisclav plains;
    # Byzantium's comes off the great river, which is what Umaia's delta
    # is for. Both stop for the same two reasons the granary always did.
    relation("vellisclavia", "thule", "grain", when=GRAIN_FAILS,
             then="grain-scarce", because="the Baltic grain ships"),
    relation("umaia", "byzantium", "grain", when=GRAIN_FAILS,
             then="grain-scarce", because="the great river's grain"),
    # -- THE RAIDERS ------------------------------------------------------ #
    # Two raiding frontiers and one word: the horde comes overland at
    # Vellisclavia, the ships come at the two coasts they can reach.
    relation("tergal", "vellisclavia", "raid",
             when=("herd-loss", "raiding", "mourning-war"),
             then="raiders-out", because="the dying steppe herds"),
    relation("thule", "phyrascia", "raid", when=("raiding",),
             then="raiders-out", because="the northern ships"),
    relation("thule", "seraptania", "raid", when=("raiding",),
             then="raiders-out", because="the northern ships"),
    # -- WHAT EACH COUNTRY SELLS ------------------------------------------ #
    # Each edge is the granary's shape: a state the SELLER holds that stops
    # the goods, and the priced word the BUYER wears while it does.
    # THE NORTHERN WOOD: Seraptania builds ships and roofs out of Thule's
    # timber, and a frozen harbor stops it as surely as a fire does.
    relation("thule", "seraptania", "timber",
             when=("ice-locked", "wildfire", "burned-over"),
             then="timber-dear", because="the frozen northern harbors"),
    # THE LOMBARD COIN: the western crowns borrow where the banks are.
    relation("byzantium", "seraptania", "coin",
             when=("paper-worthless", "shares-mad"),
             then="credit-dry", because="the shut Lombard banks"),
    # THE SOUTHERN ROAD: silk, spice and glass ride the same wagons over
    # the passes into the empire's northern neighbour.
    relation("byzantium", "teutonia", "trade",
             when=("salt-revolt", "quarter-ruined"),
             then="southern-goods-short",
             because="the broken southern road"),
    # THE GOLD CARAVANS: what comes up out of the deep south and crosses
    # to Iberia, and the same word for it on the shelf.
    relation("umaia", "andalusia", "trade",
             when=("bandit-king", "salt-revolt"),
             then="southern-goods-short",
             because="the stopped gold caravans"),
    # THE HORSES, sold twice: the steppe's remounts east, the Andalusian
    # stud west.
    relation("tergal", "vellisclavia", "horses",
             when=("herd-loss", "grass-gone"),
             then="horses-dear", because="the dying steppe herds"),
    relation("andalusia", "seraptania", "horses",
             when=("bandit-king", "faith-banned"),
             then="horses-dear", because="the closed Andalusian roads"),
    # THE HERDS AND THE HIRED CLANS: both go to the empire, which is the
    # buyer with the money.
    relation("tergal", "byzantium", "livestock",
             when=("herd-loss", "grass-gone"),
             then="hides-dear", because="the dying steppe herds"),
    relation("tergal", "byzantium", "service",
             when=("mourning-war", "raiding"),
             then="swords-gone", because="the clans' own war"),
    # THE WOOL-CLOTH AXIS: the era anchor's own trade. Phyrascia grows the
    # fleece, Teutonia's towns weave it, and a road nobody can walk stops
    # the clip where it stands.
    relation("phyrascia", "teutonia", "wool",
             when=("free-company", "custom-strike"),
             then="wool-short", because="the halted Phyrascian clip"),
    # -- THE DIPLOMATIC INSTRUMENTS --------------------------------------- #
    # How wars end and stay ended. Each is a state one land holds, a state
    # the other derives off it, and a card standing in the derived word:
    # the hostage in the horde's guard tent, the danegeld paid to the
    # fleet, the marriage across the channel and the union it argues into.
    relation("tergal", "vellisclavia", "hostage", when=("hostage-guard",),
             then="hostage-given",
             because="the hostage in the high chief's guard"),
    relation("thule", "phyrascia", "tribute", when=("tribute-taken",),
             then="danegeld-paid",
             because="the danegeld the fleet is paid"),
    relation("seraptania", "phyrascia", "marriage",
             when=("marriage-pact",), then="pact-kin",
             because="the marriage pact between the crowns"),
    relation("phyrascia", "seraptania", "union",
             when=("personal-union",), then="union-crown",
             because="the claim on the other crown"),
    # -- THE SCHISM CLOCK ------------------------------------------------- #
    # One church, two rites, and an argument that runs in BOTH directions
    # between exactly two crowns: the empire that keeps the death-face and
    # the western church's eldest daughter. The synod card sits in both
    # decks reading it, which is what makes a quarrel between two lands a
    # thing the party can be hired into.
    relation("byzantium", "seraptania", "rite",
             when=("necromancy-open", "dead-abroad", "carnival-on"),
             then="schism-near", because="the old rite's death-face"),
    relation("seraptania", "byzantium", "rite",
             when=("interdict", "relic-hunt", "bones-tested"),
             then="schism-near",
             because="the western church's accusations"),
)

RELATIONS = tuple(
    {**authored, "from": source, "to": target}
    for authored in _RELATIONS
    for source in _expand(authored["from"])
    for target in _expand(authored["to"])
    if source != target)


# --------------------------------------------------------------------------- #
# The FACTS (2026-08-11): the standing colour, for the DM and nobody else
# --------------------------------------------------------------------------- #
# The engine never reads one of these. They cost nothing at runtime, they ride
# no save, and their whole surface is the `lore` page. What they buy is that
# the DM can answer a question about a land's worship or its magic in one
# look, in the same register as everything else, instead of improvising a
# religion at the table and contradicting it three sessions later.
#
# The characteristic criterion applies here exactly as it does to a card:
# every fact below stands behind a card in this file, prices an option at the
# bottom of it, or names something the player can already do. The unbacked
# three-trait sketch is what the criterion cut, and nothing here is one.

FACTS = (
    # -- the west: THE PARISH IS THE SECOND STATE ------------------------- #
    fact("western", "parish-grid", "THE PARISH GRID",
         "Every village its priest, every life its rites, baptism to "
         "burial. The manor reaches the body; the church reaches "
         "everything else, and it is the one institution that touches "
         "every hearth in the land."),
    fact("western", "calendar", "THE CALENDAR RULES WORK",
         "Feast days claim a third of the year and working them is an "
         "offence -- which is the real medieval count, and why a ripe "
         "harvest under a week of them is a card and not a joke."),
    fact("western", "pilgrim-roads", "THE PILGRIM ROADS",
         "Shrine circuits, badges and the inns that live off them: "
         "standing escort work, a coin inflow nobody counted, and the "
         "reason two towns will steal a saint off each other."),
    fact("western", "towers", "THE TOWERS",
         "Western magic is grumpy old wizards in scattered towers, "
         "hoarding books and meeting mostly to feud. No formal teaching "
         "track exists, which makes this the wild talent's home ground "
         "and the fraud witch-finder's best market."),
    fact("western", "no-inquisition", "CONDUCT, NOT CREED",
         "There is no holy office against casting as such, here or "
         "anywhere. What gets a caster hunted is what they DID: a "
         "murderer's treatment with a specialist's surcharge."),

    # -- the south: WHAT THE WHOLE CULTURE KEEPS -------------------------- #
    fact("southern", "brotherhoods", "THE BURIAL BROTHERHOODS",
         "Hooded lay confraternities bury the poor and the plague dead on "
         "dues and donations. Anonymous by rule, ubiquitous by custom, and "
         "the hood is perfect cover."),
    fact("southern", "academy", "THE ACADEMY",
         "The archetypical wizarding university -- faculties, examinations, "
         "robes -- with the bureaucracy and class discrimination of the "
         "land it serves. The gifted commoner is admitted and made to feel "
         "the admission daily. The crown is patron and leash at once."),

    # -- BYZANTIUM: WHICH FACE RULES -------------------------------------- #
    # The death-face cluster is the southern HEIR's, not the culture's
    # (2026-08-22, the card audit): these three stand behind cards that
    # narrowed to Byzantium in the same pass.
    fact("byzantium", "two-faces", "THE PENDULUM CALENDAR",
         "The sun dies every evening and is born every dawn: Death and the "
         "Feast are the god's two faces. The year swings between the "
         "penitential season and carnival, both extremes are arguably "
         "orthodox, and attendance at both is near universal."),
    fact("byzantium", "bone-architecture", "BONE ARCHITECTURE",
         "Ossuary chapels walled in skulls, catacomb saints dressed in "
         "jewels and gold wire. Memento mori is the national art style -- "
         "and the crime layer's strangest marks."),
    fact("byzantium", "necromantic-affinity", "THE NECROMANTIC AFFINITY",
         "Necromancy keeps surfacing here: controversial, periodically "
         "half-accepted, and buried again by the next scandal. The "
         "death-face rite makes it thinkable; the northern rite cites it "
         "as proof of the creeping heresy."),

    # -- Tergal: THE PRACTICE, NOT THE CREED ------------------------------ #
    fact("tergal", "the-call", "THE CALL",
         "Shamans do not choose. A sickness or madness takes the marked "
         "one and initiation under a living shaman is the only cure; "
         "refusal ends in death or a broken mind. It is the wild talent, "
         "in a culture that has a working answer to it."),
    fact("tergal", "taboo-law", "TABOO LAW",
         "Running water is never fouled, a tent's threshold is never "
         "stepped on, the dead's names go unspoken. The party WILL trip "
         "one, and the fine is paid in livestock like everything else."),
    fact("tergal", "sky-burial", "THE SKY BURIAL",
         "The dead go to the birds on exposure platforms. Burying a body "
         "in earth MAKES a ghost, so a foreign graveyard is an "
         "abomination the camps detour around -- and a native haunting "
         "means somebody skipped the rites."),
    fact("tergal", "white-and-black", "WHITE AND BLACK",
         "The healer-shaman everyone loves, and the one who deals with "
         "the dark spirits: needed, paid double, and made to camp outside "
         "the ring of tents. When the herds sicken, everyone knows whose "
         "tent to visit, after dark."),
    fact("tergal", "owner-spirits", "OWNER-SPIRITS",
         "Every spring, pass and mountain has one. Travellers add a stone "
         "to the cairn at every pass, and an offended owner starts the "
         "misfortune chain the shaman is then paid to end."),
    fact("tergal", "magic-is-a-weapon", "MAGIC IS A WEAPON, AND A SHOW",
         "A warband counts its shaman in its strength and chiefs court "
         "spirit-workers the way settled lands court engineers. Where "
         "there is a ritual there is an art: the fire dance, and the "
         "flicker dance where a dancer blinks in and out of sight."),

    # -- THE MINERS' LEAGUE (2026-08-21, the tile economy arc) ------------- #
    # The standing colour behind the extraction cards. THE KNOCKERS comes
    # back word for word from the catalog the contraction cut: it was human
    # mining folklore when it was written and it is human mining folklore
    # now. It is also the file's first ANY_LAND fact, because the belief
    # follows the pits and every country has them.
    fact(ANY_LAND, "knockers", "THE KNOCKERS",
         "The mine-spirits knock before a collapse and are paid for it: "
         "the last bite of every meal, left at the working face. "
         "Whistling underground is forbidden. Skeptics exist; they are "
         "assigned the unluckiest shifts."),
    # Each League fact names ITS OWN land's mines and no others (2026-08-21:
    # re-homed to the actual owners under the country overlay).
    fact("teutonia", "league-teutonia", "THE MINERS' LEAGUE (TEUTONIA)",
         "Four of the nine famous mines are here and the League was born "
         "in them: Goslar is the oldest chapter, Kutna Hora cuts silver, "
         "Luneburg cuts salt, and Erzberg is the iron mountain that sets "
         "the price of a sword. A free miner answers to his chapter "
         "master and to mining law, not to the lord whose field he digs "
         "under -- which is why the lords hate the League and the emperor "
         "protects it."),
    fact("vellisclavia", "league-vellisclavia",
         "THE MINERS' LEAGUE (VELLISCLAVIA)",
         "Two chapters on the mountain road south: Banska Stiavnica cuts "
         "silver and Wieliczka cuts salt out of a mine so old the "
         "galleries are carved like a church. Both hold their charters "
         "from the crown and neither answers to the local lord."),
    fact("seraptania", "league-seraptania",
         "THE MINERS' LEAGUE (SERAPTANIA)",
         "One chapter, and a rich one: Melle's silver is the mint's, so "
         "the crown reads any dispute over that seam as a matter of "
         "state. The chapter master dines at court twice a year and "
         "complains about it."),
    fact("byzantium", "league-byzantium", "THE MINERS' LEAGUE (BYZANTIUM)",
         "One chapter, half a garrison: Novo Brdo's silver pays the "
         "soldiers, and the empire keeps a captain at the pithead who "
         "outranks the chapter master and pretends not to."),
    fact("thule", "league-thule", "THE MINERS' LEAGUE (THULE)",
         "One chapter, and the hardest of them: Falun's copper mountain "
         "is the northernmost pit in the world and no grain grows within "
         "a week's road of it, so it eats what the carts bring. The "
         "southern chapters send steward after steward to run it and none "
         "of them stays two winters."),

    # -- Thule: THE GROVE, THE SEA AND THE STONE (2026-08-22) ------------- #
    # Seven facts including the League chapter above, which is the scope
    # Tergal's packet set. THE GROVE shipped with the nine as the minimum
    # the frame demands; the other five are the norse packet's.
    fact("thule", "the-grove", "THE GROVE",
         "Every district has one: an old stand of trees nobody cuts, with "
         "a spring at its foot and a stone table beside it. Nine of every "
         "kind hang there at the great sacrifice -- horses, dogs, men -- "
         "and the bones stay where they fall. The grove priest keeps the "
         "count and nobody argues with it."),
    fact("thule", "ship-burial", "THE SHIP BURIAL",
         "A man of any standing is buried in a boat, or in a stone "
         "setting shaped like one, with his gear and whatever was killed "
         "for him. The mound is on the headland where his ships can be "
         "seen from it, it belongs to his family for ever, and opening "
         "one is the worst crime the law has a word for."),
    fact("thule", "the-thread", "THE THREAD OF FATES",
         "Three women spin, measure and cut, and a man's length is "
         "already cut before he hears it. The seer is set on the high "
         "seat, sung to, and asked -- and she tells the room who will "
         "not see the spring. Nobody argues with the thread; they argue "
         "about whether she read it right."),
    fact("thule", "land-spirits", "THE LAND-SPIRITS",
         "Every farm, rock and headland has one living in it, and it is "
         "fed at the door before anyone else eats. A ship coming home "
         "takes the carved head off the prow before it rounds the "
         "headland, so as not to frighten them off the land."),
    fact("thule", "the-drowned", "THE DROWNED BELONG TO THE SEA",
         "A man lost overboard is not looked for and not brought back. "
         "His family holds the ale-feast without a body and his seat is "
         "given away that night. When a drowned man does come back up "
         "the strand, he walks to his own house, and dealing with that "
         "is somebody's paid work."),
    fact("thule", "thing-law", "THE LAW AT THE STONE",
         "There is no king's court here. Free men meet at the stone, the "
         "law-speaker says the law aloud from memory, and the assembly "
         "decides. Its only real sentence is OUTLAWRY -- three years in "
         "which no one may feed, house or ferry you and anyone may kill "
         "you -- and the law does not carry it out. Somebody has to."),

    # -- THE SIGNATURE FACTS (2026-08-22, the norse packet's session) ----- #
    # One standing fact of its own for every country that had only its
    # culture's shared lore. A country with nothing but its culture's
    # facts on the lore page reads as a copy of its neighbour, which is
    # exactly what the country/culture split was supposed to prevent.
    fact("phyrascia", "the-wool", "THE WOOL",
         "The kingdom's money is on four legs. The great flocks are the "
         "abbeys' and the crown taxes every sack that leaves, so the "
         "wool merchants lend the crown against next year's clip and the "
         "crown listens to them for exactly as long as it owes them."),
    fact("seraptania", "the-kings-touch", "THE KING'S TOUCH",
         "The crowned king heals by laying hands on the sick -- the "
         "swollen neck, mostly -- and does it in public on the great "
         "feast days. The queue starts two days early. Whether it works "
         "is not the interesting question here; that he is the only man "
         "who may try it is."),
    fact("teutonia", "the-electors", "THE ELECTORS",
         "The emperor is ELECTED, by seven great men who are bribed to "
         "do it and know their own worth to the coin. Between the "
         "election and the crowning nobody is quite in charge, and the "
         "free cities time their charters and their lawsuits for exactly "
         "that gap."),
    fact("vellisclavia", "the-frozen-road", "THE FROZEN ROAD",
         "The rivers are the roads, and in winter they harden. A sledge "
         "carries three times what a cart does over ground that is mud "
         "eight months a year, so the trading season here is the cold "
         "one and the fairs are held on the ice."),
    fact("andalusia", "the-water-court", "THE WATER COURT",
         "The irrigation channels have a court of their own. It sits "
         "outside the cathedral door once a week, hears water theft, "
         "gives judgement the same hour, and writes nothing down. Its "
         "verdicts are obeyed by people who ignore every other court in "
         "the country."),
    fact("umaia", "the-flood-mark", "THE FLOOD MARK",
         "The great river's flood is measured on a marked pillar every "
         "summer and the year's tax is set off the number. A low mark is "
         "a hungry year, everybody in the country knows the figure by "
         "nightfall, and the men who read it are guarded."),
)

FACTS_BY_LAND: dict[str, tuple[dict, ...]] = {
    polity: tuple(f for f in FACTS if in_land(f, polity))
    for polity in LAND_SPECS
}


# --------------------------------------------------------------------------- #
# The OPTIONS (2026-08-11): the sixth outlet's standing half
# --------------------------------------------------------------------------- #
# The priced menu is "standing player-initiated actions whose terms local
# state sets" -- shops, services, the crime catalogue. The economy floor wired
# the terms that move prices the game ALREADY charges; these are the things a
# land sells that nothing else does, and the religion and magic packets are
# where they finally arrive: the temple counter, the weather-worker's rain
# stone, the charm trade, and the cultures where a wizard will teach.
#
# Every one of them does something the engine already knows how to do
# (SERVICES: a blessing, a book, a day of weather). An option that needed new
# machinery would be a feature request wearing a content hat, and the doctrine
# is the same one the cards run under: what the packets did not design does
# not get built.
#
# TEMPLE SERVICES, precisely (plan.md's ruling): healing, burial and blessing,
# as plain priced entries and nothing else. HEALING is not an option at all --
# the temple IS the healer in the Sun lands, so it is the `healer` term, which
# the interdict already puts up 30% and the holy well already undercuts. The
# sin/penance wiring stays deliberately undesigned.

OPTIONS = (
    # -- the Sun communion: one church, two rites, one counter ------------- #
    option("sun/burial", "a burial by the rite", ("western", "southern"),
           does="bless", silver=25, term="healer", days=6, gives=1,
           line="the ground, the rite and the name written in the book"),
    option("sun/blessing", "a blessing at the dawn service",
           ("western", "southern"), does="bless", silver=18, term="healer",
           days=4, gives=1,
           line="the dawn service, a hand on the head, a good week asked "
                "for out loud"),
    option("western/pilgrim-badge", "a pilgrim badge", "western",
           does="bless", silver=12, term="goods", days=8, gives=1,
           line="the shrine circuit's badge -- every inn on the road knows "
                "it and half of them charge less for it"),
    option("southern/brotherhood", "dues to a burial brotherhood",
           "southern", does="bless", silver=20, term="lodging", days=7,
           gives=1,
           line="a hooded burial brotherhood buries you whoever you turn "
                "out to have been, and the hood is nobody's business"),
    # -- Tergal: the priced thumb on the weather's scale ------------------- #
    option("tergal/rain-stone", "the rain stone", "tergal", does="sky",
           silver=60, term="goods", word="rain", holds=2,
           without=("sky-bought",),
           line="a shaman who moves weather can be hired: two days of rain "
                "over this land, dropped where you ask for it"),
    # -- Thule: the rain stone's northern cousin --------------------------- #
    # (2026-08-22, the norse packet.) The same verb and the same shape as
    # the steppe's, sold by a different trade for a different sky: what a
    # ship wants bought is WIND, and it is sold out of a cord with knots
    # in it, one knot a day.
    option("norse/weather-witch", "the weather-witch's cord", "norse",
           does="sky", silver=55, term="goods", word="wind", holds=2,
           without=("sky-bought", "white-storm"),
           line="a woman who sells wind out of a knotted cord: two days "
                "of it over this land, from the quarter you ask for"),
    # -- the south: the formal version of the whole business -------------- #
    option("southern/academy-fee", "a term at the academy", "southern",
           does="book", silver=130, term="goods", kinds=("capital",),
           line="faculties, examinations, robes, and a commoner's fee "
                "quoted twice as loudly as a noble's"),
    # -- the west: no ladder, one door ------------------------------------ #
    option("western/tower-fee", "the tower wizard's price", "western",
           does="book", silver=150, term="goods", states=("tower-open",),
           line="silver might open the door; volunteering as the subject of "
                "the experiment opens it faster and costs less"),
)

OPTIONS_BY_KEY = {o["key"]: o for o in OPTIONS}


def option_word(spec: dict) -> str:
    """The word the player types: an option's key without its land prefix.
    Unique across the whole catalogue (validated at import), so `service
    burial` means one thing wherever the party is standing."""
    return spec["key"].split("/", 1)[1]


def option_named(word: str) -> dict | None:
    """One option by the word the player typed, or by a unique prefix of
    it -- the `case` command's courtesy, applied to the counter."""
    word = word.lower().strip()
    exact = [o for o in OPTIONS if option_word(o) == word]
    if exact:
        return exact[0]
    hits = [o for o in OPTIONS if option_word(o).startswith(word)]
    return hits[0] if len(hits) == 1 else None


def facts_of(polity: str) -> tuple[dict, ...]:
    """The standing colour of one land, for the DM. Static -- no world."""
    return FACTS_BY_LAND[polity]


def options_of(polity: str) -> list[dict]:
    """Every option this land could ever sell, gates ignored."""
    return [o for o in OPTIONS if polity in o["land"]]


def option_open(world: dict, polity: str, spec: dict,
                kind: str = "") -> bool:
    """Is this option on sale here today? The gates are the card's own,
    minus the ones a standing service has no use for: states held or
    derived, states that shut it, the land's rolled tension, and the
    settlement tier where the packet named one."""
    held = set(state_ids(world, polity))
    if any(s not in held for s in spec["states"]):
        return False
    if any(s in held for s in spec["without"]):
        return False
    if spec["tension"] and not any(t in tensions_of(world, polity)
                                   for t in spec["tension"]):
        return False
    if spec["kinds"] and kind and kind not in spec["kinds"]:
        return False
    return True


def options_here(world: dict, polity: str, kind: str = "") -> list[dict]:
    """What this land is selling at this tier of settlement right now."""
    return [o for o in options_of(polity)
            if option_open(world, polity, o, kind)]


def option_price(world: dict, polity: str, spec: dict) -> int:
    """What the option costs here today: its catalog price, moved by the
    land's own priced term. A service is charged exactly the way a bed or a
    healer's day is -- the world state is on this counter too."""
    return priced(world, polity, spec["term"], spec["silver"])


def service_lines(world: dict, polity: str, kind: str = "") -> list[str]:
    """The services counter, for the player: what is on sale, what it costs
    here today, and the key to buy it with."""
    open_now = options_here(world, polity, kind)
    if not open_now:
        return []
    lines = [f"-- what {world['lands'][polity]['name']} sells --"]
    for spec in open_now:
        lines.append(f"  {spec['name']}: "
                     f"{option_price(world, polity, spec)}s "
                     f"(`service {option_word(spec)}`)")
        lines.append(f"    {spec['line']}")
    return lines


def lore_lines(world: dict, polity: str) -> list[str]:
    """The DM's page for one land: the standing facts behind its worship and
    its magic, then whatever its counters are selling today. Free, and never
    seen by the engine -- this is the one surface a FACT has."""
    lines = [f"-- {world['lands'][polity]['name']}: what is believed here --"]
    for entry in facts_of(polity):
        lines.append(f"  {entry['title']}")
        lines.append(f"    {entry['line']}")
    lines.extend(service_lines(world, polity))
    return lines


# --------------------------------------------------------------------------- #
# THE ROLLED WARS (2026-08-22, the medieval world arc's session 5)
# --------------------------------------------------------------------------- #
# The game is static in time, so its wars are static too: three of the six
# templates below are drawn once at worldgen, stand for the whole campaign,
# and smoulder rather than resolve (rules.md's The Rolled Wars add-on).
# `conquest.roll_campaigns` is what makes a front LOOK alive; this file rolls
# the wars, stamps `at-war` on every belligerent and posts each herald.
#
# A THEATER is an authored tuple of (row, column) map cells, drawn against
# the four overlays in `resources/`, and every cell in it belongs to one of
# the template's own belligerents -- the ground a war is fought over is the
# ground somebody in it holds.

WARS_ROLLED = 3                 # how many of the six a world gets. No
                                # exclusion rules: any three coexist, which
                                # is what the age actually looked like.

# Andalusia's vassalage, a d2 at worldgen (re-cut 2026-08-22: the
# peninsula's north is its own crown of the Sun rite and never Umaia's
# man): 1 Byzantium's vassal, 2 independent. An independent Andalusia is
# Byzantium's ALLY still -- the Reconquista marches either way, and the
# roll only decides whether the map legend prints a liege. Read by
# `politics_lines` and by `places.land_label`.
VASSALAGE = ("byzantium", None)

CRUSADERS = ("byzantium", "seraptania", "teutonia", "phyrascia")

WAR_TEMPLATES = (
    {
        "key": "crusade", "name": "THE CRUSADE", "posture": "invasion",
        # 1-3 of the four crowns take the cross; Umaia's east is the prize.
        "attackers": CRUSADERS, "attacker_draw": (1, 3),
        "defenders": ("umaia",),
        "herald": "The cross is preached in every square. An army is "
                  "marching on Jerusalem.",
        # the Levant, around Jerusalem
        "theater": ((15, 28), (15, 29), (15, 30), (16, 27), (16, 28),
                    (16, 29), (16, 30), (17, 28), (17, 29), (17, 30)),
    },
    {
        "key": "hundred-years", "name": "THE LONG WAR", "posture": "invasion",
        "attackers": ("phyrascia",), "defenders": ("seraptania",),
        "herald": "The king across the water claims the crown of "
                  "Seraptania. His army has landed.",
        # Seraptania's north and west coast, and Aquitaine
        "theater": ((8, 9), (8, 10), (9, 4), (9, 5), (10, 5), (10, 6),
                    (11, 6), (11, 7), (12, 6), (12, 7)),
    },
    {
        "key": "horde", "name": "THE HORDE RIDES WEST", "posture": "invasion",
        "attackers": ("tergal",), "defenders": ("vellisclavia",),
        "herald": "The horde has crossed the river. The border towns are "
                  "burning.",
        # the steppe frontier: row 8's south edge, and the western salient
        "theater": ((8, 22), (8, 23), (8, 24), (8, 25), (8, 26), (8, 27),
                    (8, 28), (8, 29), (9, 20), (9, 21), (10, 20), (10, 21)),
    },
    {
        "key": "vikings", "name": "THE RAIDING SEASON", "posture": "raiding",
        "attackers": ("thule",), "defenders": ("phyrascia", "seraptania"),
        "herald": "The ships are out of the north again. The raiding "
                  "season has opened on both coasts.",
        # both coasts: Britain, the channel and the west
        "theater": ((4, 4), (4, 5), (5, 2), (6, 2), (7, 4), (7, 7),
                    (8, 9), (9, 4), (9, 5), (10, 5)),
    },
    {
        "key": "reconquista", "name": "THE RECONQUISTA", "posture": "invasion",
        # The march to retake the peninsula's south, which Umaia holds
        # (2026-08-22, the Iberia split): Andalusia rides -- Byzantium's
        # vassal or its ally, the d2 decides only the paperwork -- and
        # Byzantine ships close the strait behind it.
        "attackers": ("andalusia", "byzantium"), "defenders": ("umaia",),
        "herald": "Andalusia has called the march on the lost south. Its "
                  "knights are riding for Qurtuba, and Byzantine ships "
                  "are closing the strait behind them.",
        # Umaia's al-Andalus, and the strait's far shore
        "theater": ((14, 2), (14, 3), (14, 4), (14, 5), (14, 6), (15, 3),
                    (15, 4), (15, 5), (16, 7), (16, 8)),
    },
    {
        "key": "eastern-war", "name": "THE EASTERN WAR", "posture": "invasion",
        "attackers": ("umaia",), "defenders": ("byzantium",),
        "herald": "Umaia's army is over the border. Byzantium is calling "
                  "up every man in the east.",
        # east Anatolia and the Levant border strip
        "theater": ((14, 28), (14, 29), (14, 30), (15, 23), (15, 24),
                    (15, 25), (15, 26), (15, 27)),
    },
)
WAR_TEMPLATES_BY_KEY = {spec["key"]: spec for spec in WAR_TEMPLATES}


def _belligerents(spec: dict,
                  rng: random.Random) -> tuple[tuple[str, ...],
                                               tuple[str, ...]]:
    """Who is actually in this war, this campaign. One template is not
    fixed: the CRUSADE draws 1-3 of the four crowns that could take the
    cross. (The Reconquista stopped reading the vassalage when the Iberia
    split retired Umaia as a possible liege, 2026-08-22: Andalusia rides
    with Byzantium behind it whatever the d2 said.)"""
    attackers, defenders = spec["attackers"], spec["defenders"]
    draw = spec.get("attacker_draw")
    if draw is not None:
        n = rng.randint(*draw)
        attackers = tuple(sorted(rng.sample(list(attackers), n),
                                 key=attackers.index))
    return tuple(attackers), tuple(defenders)


def new_war(spec: dict, rng: random.Random, day: int) -> dict:
    """One rolled war's record. `occupied` and `scars` are the campaign
    sim's ledgers (conquest.py) and open empty; `rolled_day` is its
    watermark, so catching a war up is living through it."""
    attackers, defenders = _belligerents(spec, rng)
    return {
        "key": spec["key"],
        "name": spec["name"],
        "attackers": list(attackers),
        "defenders": list(defenders),
        "theater": [tile_id(row, column) for row, column in spec["theater"]],
        "posture": spec["posture"],
        "herald": spec["herald"],
        "rolled_day": day,
        "occupied": [],
        "scars": [],
    }


def roll_wars(world: dict, day: int = 0) -> list[dict]:
    """THE WAR ROLL, once at worldgen, on its own derived stream so no
    other layer's numbers move: first Andalusia's vassalage, then three
    distinct templates. Every belligerent takes the `at-war` state and
    hears the herald.

    The world-level pass runs AFTER every land's layer exists, because
    setting a state and posting news both read the layer."""
    rng = random.Random(f"wars:{world.get('seed')}")
    for land in world["lands"].values():
        land["liege"] = None
    liege = VASSALAGE[rng.randint(1, len(VASSALAGE)) - 1]
    world["lands"]["andalusia"]["liege"] = liege
    wars = [new_war(spec, rng, day)
            for spec in rng.sample(list(WAR_TEMPLATES), WARS_ROLLED)]
    world["wars"] = wars
    for war in wars:
        for polity in war["attackers"] + war["defenders"]:
            set_state(world, polity, "at-war", day)
            post_news(world, polity, day, f"{war['name']}: {war['herald']}")
    return wars


def wars_of(world: dict, polity: str) -> list[dict]:
    """The wars this land is in, attacker or defender."""
    return [war for war in world.get("wars", ())
            if polity in war["attackers"] or polity in war["defenders"]]


def war_side(war: dict, polity: str) -> str:
    return "attacking" if polity in war["attackers"] else "defending"


def land_names(world: dict, keys) -> str:
    return ", ".join(world["lands"][key]["name"] for key in keys)


def war_lines(world: dict) -> list[str]:
    """The DM's inventory of the standing wars (`world`): who is in each,
    the herald it opened with, how far its campaign has been rolled, and
    what it is holding. Vassalage rides here too -- it is the other thing
    the war roll settled."""
    wars = world.get("wars") or []
    lines = ["-- the wars --"]
    for war in wars:
        lines.append(f"{war['name']} [{war['posture']}] "
                     f"(rolled to day {war['rolled_day']})")
        lines.append(f"  {land_names(world, war['attackers'])} -> "
                     f"{land_names(world, war['defenders'])}")
        lines.append(f"  {war['herald']}")
        for sid in war["occupied"]:
            slot = world["settlement_slots"][sid]
            area = world["areas"].get(slot["area"]) if slot["area"] else None
            tile = world["tiles"][slot["tile"]]
            lines.append(f"  occupied: {area['name']} "
                         f"({tile_coordinate(tile['row'], tile['column'])})"
                         if area is not None else
                         f"  occupied: a {slot['tier']} at "
                         f"{tile_label(tile)}")
    for polity, land in world["lands"].items():
        if land["liege"]:
            lines.append(f"{land['name']} is "
                         f"{world['lands'][land['liege']]['name']}'s vassal.")
    return detail_wrap(lines, MAP_WIDTH)


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


def roll_constitution(rng: random.Random, polity: str) -> str:
    """The land's exclusive constitution slot, on a DEFAULT-HEAVY die: the
    stereotype is the constant and the variants are the colour. One roll,
    at worldgen -- cards never flip it, and the two that do say so."""
    entries = CONSTITUTIONS[polity]
    roll = rng.randint(1, sum(c["weight"] for c in entries))
    for spec in entries:
        roll -= spec["weight"]
        if roll <= 0:
            return spec["key"]
    return entries[0]["key"]                        # unreachable


def roll_tensions(rng: random.Random, polity: str, band: str) -> list[str]:
    """What this land is fighting about: its standing tensions, plus ONE
    rolled from the packet -- two if it opened in CRISIS. This is the gate
    that decides which political cards its deck holds at all, which is what
    keeps the packet a pool and the rolled world specific."""
    standing = list(STANDING_TENSIONS.get(polity, ()))
    pool = [t["key"] for t in TENSIONS[polity] if t["key"] not in standing]
    draws = (CRISIS_TENSION_ROLLS if band == "crisis" else TENSION_ROLLS)
    rolled = rng.sample(pool, min(draws, len(pool))) if pool else []
    return standing + rolled


def _tension_gate(spec: dict, tensions) -> bool:
    """Does this card's tension hold here? A card that names none is
    land-wide and always passes -- every econ and weather card does."""
    wanted = spec["admits"].get("tension") or ()
    return not wanted or any(t in tensions for t in wanted)


def _deck(world: dict, polity: str, track: str = "crisis",
          tensions=()) -> list[str]:
    """One of the land's three decks, shuffled once (the pact deck's
    pattern). A weather or season card marked ANY_LAND sits in every land's
    deck; a land-named one sits in its own; and a POLITICAL card only enters
    the deck of a land whose rolled tension it names."""
    keys = [c["key"] for c in CARDS
            if c["track"] == track and in_land(c, polity)
            and _tension_gate(c, tensions)]
    random.Random(_land_seed(world, polity, f"worldsim-deck-{track}",
                             0)).shuffle(keys)
    return keys


def open_world(world: dict) -> dict:
    """Roll the world layer onto a fresh world: every land's wealth band,
    its politics (the constitution slot, the tensions, the ruler's sheet),
    its three shuffled decks, its opening sky, its state and news lists. A
    land that opens in CRISIS draws its first crisis card straight away -- a
    land in trouble is in trouble from scene one, not from the first lucky
    roll. The weather and season tracks open EMPTY: a sky is a thing that
    happens on a day, and day 0 is worldgen's bookkeeping.

    The politics rolls come AFTER the wealth roll on the same stream, so
    every world's bands are exactly what they were before politics existed
    -- and the tensions come before the decks, because they are the decks'
    gate.

    Called by `quests.generate_world` on a DERIVED rng, so the worldgen
    stream every career bench rides is untouched."""
    for polity in world["lands"]:
        rng = random.Random(_land_seed(world, polity, "worldsim-open", 0))
        band = roll_wealth(rng)
        tensions = roll_tensions(rng, polity, band)
        world["lands"][polity]["world"] = {
            "wealth": band,
            "wealth_day": 0,
            "constitution": roll_constitution(rng, polity),
            "tensions": tensions,
            "ruler": rulers.roll_ruler(rng),
            "authorities": {},      # the lesser named faces cards create
            "deck": _deck(world, polity, "crisis", tensions),
            "weather_deck": _deck(world, polity, "weather", tensions),
            "season_deck": _deck(world, polity, "season", tensions),
            "drawn": [],            # every card this land has fired
            "live": None,           # the card standing now, with its clock
            "weather_live": None,   # ...and the same for the other two
            "season_live": None,    # tracks (a storm must not block a
                                    # harvest failing, nor a drought a storm)
            "weather": "",          # today's sky, once a day has been rolled
            "weather_day": 0,
            "bought_sky": None,     # ...unless a weather-worker was paid
                                    # (the rain stone, an OPTION)
            "wet": 0,               # the wet and dry SPELLS running behind
            "dry": 0,               # it -- what the slow cards read
            "news": [],             # day-stamped lines, oldest first
            "news_seq": 0,          # lines ever posted (survives the trim)
            "told_seq": 0,          # ...and how many of them were told
            "rolled_day": 0,        # the last day this land was rolled
        }
    for polity in world["lands"]:
        layer = land_layer(world, polity)
        if layer["wealth"] in OPENING_DRAW:
            rng = random.Random(_land_seed(world, polity, "worldsim-open", 1))
            drawn = _draw(world, polity, rng)
            if drawn is not None:
                _fire(world, polity, drawn, OPENING_DAY, rng)
    # THE WORLD-LEVEL PASS (2026-08-22, session 5), last and after every
    # land's layer exists: Andalusia's vassalage and the three rolled wars,
    # each stamping `at-war` on its belligerents and posting its herald.
    roll_wars(world)
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
    never stored: a failed harvest in one land is grain-scarce in every land
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


# --- what a land IS: the politics slots, read at admit time ---------------- #

def constitution_of(world: dict, polity: str) -> str:
    return land_layer(world, polity)["constitution"]


def constitution_spec(world: dict, polity: str) -> dict:
    key = constitution_of(world, polity)
    return next(c for c in CONSTITUTIONS[polity] if c["key"] == key)


def set_constitution(world: dict, polity: str, key: str, day: int) -> None:
    """Move the exclusive constitution slot. Only a card that says so does
    this -- the junta and the commune are the two in the whole deck."""
    if key not in {c["key"] for c in CONSTITUTIONS[polity]}:
        raise ValueError(f"{polity} has no such constitution: {key}")
    layer = land_layer(world, polity)
    if layer["constitution"] == key:
        return
    layer["constitution"] = key
    layer["constitution_day"] = day


def tensions_of(world: dict, polity: str) -> list[str]:
    return list(land_layer(world, polity).get("tensions", ()))


def tension_spec(polity: str, key: str) -> dict:
    return next(t for t in TENSIONS[polity] if t["key"] == key)


def factions_of(world: dict, polity: str) -> list[str]:
    """The land's live faction cast: every bloc its rolled tensions name."""
    cast: list[str] = []
    for key in tensions_of(world, polity):
        for name in tension_spec(polity, key)["factions"]:
            if name not in cast:
                cast.append(name)
    return cast


def live_edges(world: dict, polity: str) -> list[dict]:
    """The faction edges standing in this land -- the authored ones whose
    BOTH ends are in the rolled cast. An edge with one end missing is not a
    half-edge; it simply is not there this playthrough."""
    cast = set(factions_of(world, polity))
    return [e for e in FACTION_EDGES
            if polity in e["land"] and e["from"] in cast
            and e["to"] in cast]


def ruler_sheet(world: dict, polity: str) -> dict:
    """The land ruler's rolled character (`rulers.py`). One copy, on the
    land layer -- `quests._cast_the_land` records the notable's id on it, so
    the sheet and the face it wears are joined without being stored twice."""
    return land_layer(world, polity)["ruler"]


def ruler_traits(world: dict, polity: str) -> list[str]:
    return list(ruler_sheet(world, polity)["traits"])


def succession_of(world: dict, polity: str) -> str:
    return ruler_sheet(world, polity)["succession"]


def set_succession(world: dict, polity: str, state: str, day: int) -> None:
    """Move the crown's succession circumstance -- what the succession
    cluster's cards do to each other (an heir found settles what a disputed
    claim opened)."""
    if state not in rulers.SUCCESSIONS:
        raise ValueError(f"no such succession state: {state}")
    sheet = ruler_sheet(world, polity)
    sheet["succession"] = state
    sheet["succession_day"] = day


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
        need = drought_days(world, polity)
    if need and layer.get("dry", 0) < need:
        return False
    # The politics slots. Each is ANY-OF: the land holds one constitution
    # and one succession state, one or two tensions, and a handful of live
    # edges, so a card names every value it will take. The `held` side is a
    # THUNK because this runs once per card per draw and the edge lookup is
    # the only expensive one -- almost no card asks for it.
    crown = layer.get("ruler") or {}
    for wanted, held in (
            (spec.get("tension"), lambda: layer.get("tensions", ())),
            (spec.get("constitution"), lambda: (layer.get("constitution"),)),
            (spec.get("traits"), lambda: crown.get("traits", ())),
            (spec.get("succession"), lambda: (crown.get("succession"),)),
            (spec.get("edge"),
             lambda: [e["key"] for e in live_edges(world, polity)])):
        if wanted and not any(w in held() for w in wanted):
            return False
    return True


def _says_nothing_new(world: dict, polity: str, drawn: dict) -> bool:
    """A card whose whole state effect is a slot the land already holds has
    nothing to say -- it stays in the deck rather than firing an empty
    pulse (the exclusive-slot discipline, from the other side)."""
    state = drawn["outlets"].get("state") or {}
    if (state.get("constitution")
            and state["constitution"] == constitution_of(world, polity)):
        return True         # the generals cannot take a palace they hold
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
        deck.extend(_deck(world, polity, track, layer.get("tensions", ())))
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
    layer["news_seq"] += 1
    layer["news"].append({"day": day, "line": line,
                          "seq": layer["news_seq"]})
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
    if state.get("constitution"):
        set_constitution(world, polity, state["constitution"], day)
    if state.get("succession"):
        set_succession(world, polity, state["succession"], day)
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
    # ...and the same trick, bought (2026-08-11): a hired weather-worker
    # holds the sky the way a card that IS the weather does, and the day it
    # runs out the land goes back to its own climate.
    bought = layer.get("bought_sky")
    if bought is not None:
        if day < bought["until"]:
            forced = forced or bought["word"]
        else:
            layer["bought_sky"] = None
            drop_state(world, polity, "sky-bought", day)
    word = forced or roll_weather(world, polity, day, rng)
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
                                      >= CARD_CHANCE[layer["wealth"]]):
                continue        # the crisis track's die is the wealth band;
                                # the other two are the sky's own
            drawn = _draw(world, polity, rng, sky, track)
            if drawn is not None:
                _fire(world, polity, drawn, today, rng)
        layer["rolled_day"] = today


def roll_world(world: dict, day: int) -> None:
    """Bring EVERY land up to `day`. Called at the roll points the game
    already has -- settlement arrivals, nights, travel legs, wherever the
    board's refill and the crown's raids fire.

    ONE DAY AT A TIME ACROSS THE WHOLE WORLD (2026-08-21, session 4). This
    used to run each land to `day` in turn, which meant the second land's
    day 5 draw read the first land's day 60 -- so a card admitting on a
    DERIVED state (`mining/food-caravan` on grain-scarce, the synod on
    schism-near) fired on a different history depending on whether the
    party had been watching. Six cards could see it and it only ever
    surfaced when the League made one of them ANY_LAND. Stepping the
    calendar instead of the land is what the promise above always said:
    a relation never reads a land that is ahead of it either.

    `roll_land` is a no-op for a land already at `today`, so a world whose
    lands are level costs one call each per day and nothing else."""
    if not world["lands"]:
        return
    start = min(land_layer(world, polity)["rolled_day"]
                for polity in world["lands"])
    for today in range(start + 1, day + 1):
        for polity in world["lands"]:
            roll_land(world, polity, today)


def post_news(world: dict, polity: str, day: int, line: str) -> None:
    """Put a line on a land's news from OUTSIDE the deck: authored content
    that happens to the world without a card behind it belongs on the same
    feed as everything else the land hears."""
    _news(world, polity, day, line)


def take_news(world: dict, polity: str, day: int) -> list[str]:
    """What this land has heard since the party last listened -- the state
    diff's spoken half. Told once: the count moves with the telling. The
    watermark is a running COUNT rather than a day, so a line posted later
    on an already-told day (the war herald's, through `post_news`) still
    reaches the next listener instead of dying between two tellings."""
    layer = land_layer(world, polity)
    fresh = [n for n in layer["news"] if n["seq"] > layer["told_seq"]]
    layer["told_seq"] = layer["news_seq"]
    if not fresh:
        return []
    lines = [f"  (day {n['day']}) {n['line']}" for n in fresh[-NEWS_TOLD:]]
    return [f"WORD FROM {world['lands'][polity]['name'].upper()}:"] + lines


# --------------------------------------------------------------------------- #
# The three outlets the frame carried (2026-08-09, the economy floor)
# --------------------------------------------------------------------------- #
# The board, the shop and the road all ASK the world layer a question at the
# moment they need the answer; nothing here writes to the save. That is why
# an edge can be re-authored, a knob re-tuned, or a card added without a
# migration -- the same reason the relations table derives instead of storing.

def live_cards(world: dict, polity: str) -> list[dict]:
    """Every card standing over the land right now, one per track."""
    layer = land_layer(world, polity)
    out = []
    for track in TRACKS:
        live = layer.get(LIVE_KEY[track])
        if live is not None:
            out.append(CARDS_BY_KEY[live["key"]])
    return out


def _outlet(world: dict, polity: str, outlet: str) -> list[dict]:
    return [c["outlets"][outlet] for c in live_cards(world, polity)
            if outlet in c["outlets"]]


# --- the QUEST outlet: post, cancel, reprice -------------------------------- #

def board_shift(world: dict, polity: str) -> int:
    """What the world does to the SIZE of a settlement's board here: the
    wealth band, plus every live card's `slots`. A fair or a fleet in adds
    work; cold mills take it away. The floor is applied by the caller
    (`quests.board_slots`) -- a settlement is never a place with no work."""
    shift = BAND_SLOTS[wealth_of(world, polity)]
    for spec in _outlet(world, polity, "quest"):
        shift += int(spec.get("slots", 0))
    return shift


def board_pay(world: dict, polity: str) -> float:
    """What the world does to what a posting QUOTES here: the band's own
    hand, times every live card's `reprice`. Applied once, at posting time
    -- a job taken keeps the terms it was posted at, which is what makes a
    good week on the board worth walking to."""
    pay = BAND_PAY[wealth_of(world, polity)]
    for spec in _outlet(world, polity, "quest"):
        pay *= float(spec.get("reprice", 1.0))
    return pay


def board_postings(world: dict, polity: str) -> list[dict]:
    """The jobs the live cards are PUTTING UP here -- the card key (so a
    board never carries two copies of one card's work), the authored
    template, and the premium the card pays over the going rate.

    Nothing is posted here: the board posts it, when it next refills, at a
    settlement of its own choosing (`quests.refresh_settlement_board`)."""
    out = []
    for spec in live_cards(world, polity):
        posted = (spec["outlets"].get("quest") or {}).get("post")
        if posted:
            out.append({"key": spec["key"], "card": spec["name"],
                        "job": posted,
                        "pay": float(spec["outlets"]["quest"].get("pay",
                                                                  1.0))})
    return out


# --- the MENU outlet: what the shelf costs here ----------------------------- #

def menu_terms(world: dict, polity: str) -> dict[str, float]:
    """Every priced term the land's world state moves, as a multiplier on
    the price the game already charges. Three sources multiply: the WEALTH
    BAND, the STATES the land holds or derives (STATE_MENU -- the only road
    a relation has to a price), and the live CARDS' own `menu` payloads.

    Clamped to MENU_FLOOR..MENU_CEILING so a bad month is expensive and
    never absurd. A term nobody moved is simply absent -- callers that ask
    for one get 1.0 (`term`), which is what an untouched price is."""
    terms: dict[str, float] = {}

    def apply(table) -> None:
        for name, mult in table.items():
            terms[name] = terms.get(name, 1.0) * float(mult)

    apply(BAND_MENU[wealth_of(world, polity)])
    for state_id in state_ids(world, polity):
        apply(STATE_MENU.get(state_id, {}))
    for payload in _outlet(world, polity, "menu"):
        apply(payload)
    return {name: max(MENU_FLOOR, min(MENU_CEILING, mult))
            for name, mult in terms.items() if abs(mult - 1.0) > 0.001}


def term(world: dict, polity: str, name: str) -> float:
    """One priced term over one land. 1.0 is the untouched catalog price --
    what a land nothing is happening to charges. A land the world layer has
    never been rolled onto is not a case: `quests.generate_world` opens the
    layer before it posts anything, so every land in every world has one."""
    return menu_terms(world, polity).get(name, 1.0)


def priced(world: dict, polity: str, name: str, base: int) -> int:
    """`base` silver, as this land currently charges it. Rounded, and never
    to zero: the world moves a price, it does not abolish one."""
    return max(1, round(base * term(world, polity, name)))


MENU_LABEL = {                  # what the price sheet calls each term --
    "goods": "the shop shelf",  # short, because the whole line has to fit
    "steel": "the smith",       # the phone beside the multiplier
    "lodging": "a bed at the inn",
    "healer": "the healer's fee",
    "toll": "the road tolls",
    "ferry": "the ferrymen",
}


def menu_lines(world: dict, polity: str) -> list[str]:
    """The priced menu's own state diff: what the world is doing to the
    prices here, and nothing when it is doing nothing."""
    terms = menu_terms(world, polity)
    if not terms:
        return []
    name = world["lands"][polity]["name"]
    lines = [f"-- what {name} charges today --"]
    for key in MENU_TERMS:
        mult = terms.get(key)
        if mult is None:
            continue
        way = "up" if mult > 1 else "down"
        lines.append(f"  {MENU_LABEL[key]}: {way} x{mult:.2f}")
    return lines


def road_charges(world: dict, lands) -> tuple[int, list[str]]:
    """What the roads TAKE on a trip: the toll each land on the leg is
    charging, plus the ferrymen's price where a land's fords are gone. One
    charge per land, the lines saying who took it.

    This is the priced menu's other half -- the terms above are asked at a
    counter the party walks up to; these are asked at a bridge that is
    already in front of it (`worldsim.travel_delay` is the same trip's
    time cost)."""
    silver, lines = 0, []
    for polity in dict.fromkeys(lands):
        if polity is None or polity not in world.get("lands", {}):
            continue
        held = set(state_ids(world, polity))
        name = world["lands"][polity]["name"]
        toll = term(world, polity, "toll")
        if toll > 1.0:
            take = max(1, round(ROAD_TOLL_SILVER * toll))
            silver += take
            lines.append(f"  {name}: the toll-men take {take}s at the "
                         f"bridge.")
        ferry = term(world, polity, "ferry")
        if "fords-out" in held:
            take = max(1, round(ROAD_FERRY_SILVER * ferry))
            silver += take
            lines.append(f"  {name}: the ferry across costs {take}s.")
    return silver, lines


# --- the ENCOUNTER outlet: what the world puts on the road ------------------ #

def encounter_entries(world: dict, polity: str,
                      where: str = "any") -> list[dict]:
    """The local encounter-table entries standing over this land: the live
    cards' own, plus the ones its STATES carry (STATE_ENCOUNTERS -- how a
    derived state gets onto a road, since no card in this land named it).

    `where` filters by ground: "road" is a travel leg, "wilds" is a day
    afield or a night camped, and an entry marked "any" answers to both."""
    entries = [dict(e) for e in _outlet(world, polity, "encounter")]
    for state_id in state_ids(world, polity):
        entry = STATE_ENCOUNTERS.get(state_id)
        if entry is not None:
            entries.append(dict(entry))
    return [e for e in entries
            if where == "any" or e.get("where", "any") in (where, "any")]


def local_encounter(world: dict, polity: str, where: str,
                    rng: random.Random) -> dict | None:
    """Roll ONE of the land's live entries onto an encounter that is about
    to happen, or None for the road's own wildlife. The entry does not
    replace the road's LEVEL table -- what the world puts out there is who
    it is, never how hard it is: the party-independent danger curve is a
    contract (rules.md's The explore move & the hunt) and the world layer
    does not get to bend it."""
    entries = encounter_entries(world, polity, where)
    if not entries:
        return None
    entry = entries[0] if len(entries) == 1 else rng.choice(entries)
    if rng.random() >= entry.get("chance", ENCOUNTER_CHANCE):
        return None
    return entry


# --- the MARK outlet's corner: what the world puts in the crime tables ------ #
# (2026-08-11, the religion & magic rung.) The priced menu covers what a state
# does to a price and the encounter table covers who it puts on a road; this
# covers what it makes ROBBABLE. It is the reagent trade's crime-layer wiring
# and the two marks the religion packets pre-ordered, and it is the same
# read-only shape: `crime.roll_mark` takes the extra faces and rolls them in
# beside the band's own.

def mark_roles(world: dict, polity: str, category: str) -> tuple[str, ...]:
    """The extra marks this land's world state puts in a crime category's
    table. Empty in a quiet land, which is the ordinary case."""
    out: list[str] = []
    for state_id in state_ids(world, polity):
        out.extend(STATE_MARKS.get(state_id, {}).get(category, ()))
    return tuple(out)


# --- the OPTION outlet's one world-changing verb ---------------------------- #

def hire_weather(world: dict, polity: str, day: int, word: str,
                 holds: int) -> None:
    """The rain stone, paid for: the land's day roll is held at `word` for
    `holds` days. The weather system gains a priced thumb on the scale and
    nothing else -- the sky is bought for a day or two, never a season, and
    a bought sky runs the wet/dry spells exactly as a rolled one does (the
    price rule: healing is retail, and so is weather)."""
    layer = land_layer(world, polity)
    # The purchase day's own sky is already rolled by the time anything is
    # sold (the session rolls the world before every command), so the paid
    # window is the NEXT `holds` days -- hence the +1.
    layer["bought_sky"] = {"word": word, "until": day + holds + 1}
    set_state(world, polity, "sky-bought", day)


# --------------------------------------------------------------------------- #
# Readouts (the state diff)
# --------------------------------------------------------------------------- #

def state_line(entry: dict) -> str:
    word = STATE_WORDS.get(entry["id"], entry["id"])
    if entry.get("derived"):
        return f"{word} ({entry['because']})"
    since = entry.get("since")
    return word + (f" (day {since})" if since is not None else "")


MAP_WIDTH = 40      # the map page's column, the same one session.py prints
                    # by; a long state list wraps with a hanging indent
                    # rather than running off the phone


def land_lines(world: dict, polity: str) -> list[str]:
    """The land's world state for the map page: the band, whatever it is
    living through, WHAT KIND OF PLACE IT IS, and the sky over it. Three
    things at most -- this is a phone page, so the constitution shows its
    name and keeps its sentence for `world` -- each wrapped to the page's
    own column (`places.detail_wrap`)."""
    layer = land_layer(world, polity)
    lines = [f"  [{layer['wealth'].upper()}]"]
    shown = held_states(world, polity) + derived_states(world, polity)
    if shown:
        lines[0] += " " + "; ".join(state_line(s) for s in shown)
    lines.append(f"  {constitution_spec(world, polity)['name']}")
    sky = weather_line(world, polity)
    if sky:
        lines.append(f"  {sky}")
    return detail_wrap(lines, MAP_WIDTH)


def notable_lines(world: dict, npc: dict) -> list[str]:
    """What a town says about one of its notables, where the world layer
    has something to say. Only the land RULER has a sheet, and only its
    PUBLIC half is printed: the words themselves are exactly the reputation
    everyone in the land already has of him, and the succession is the fact
    every court in the world is counting on. `heart` is never here -- it is
    the DM's, on `world`."""
    if npc.get("post") != "ruler":
        return []
    polity = npc.get("land")
    if polity not in world.get("lands", {}):
        return []
    sheet = ruler_sheet(world, polity)
    lines = [f"    said of {npc['name']}: {rulers.trait_phrase(sheet)}"]
    if sheet["succession"] != "secure":
        lines.append(f"    {rulers.SUCCESSION_WORDS[sheet['succession']]}")
    if sheet.get("puppeteer"):
        lines.append(f"    ...and that {sheet['puppeteer']} decides")
    return lines


def politics_lines(world: dict, polity: str) -> list[str]:
    """What the land IS, for the DM inventory: the constitution and its
    sentence, what it is fighting about, which authored faction edges are
    live in it, and the ruler's rolled sheet with the faces the cards have
    named beside it."""
    spec = constitution_spec(world, polity)
    lines = [f"  {spec['name']}: {spec['line']}"]
    liege = world["lands"][polity]["liege"]
    if liege:
        lines.append(f"  vassal of {world['lands'][liege]['name']}")
    for war in wars_of(world, polity):
        lines.append(f"  {war['name']}: {war_side(war, polity)}")
    for key in tensions_of(world, polity):
        standing = (" [standing]"
                    if key in STANDING_TENSIONS.get(polity, ()) else "")
        lines.append(f"  tension: {tension_spec(polity, key)['line']}"
                     f"{standing}")
    for live in live_edges(world, polity):
        lines.append(f"    edge: {live['line']}")
    lines.extend(rulers.ruler_lines(ruler_sheet(world, polity)))
    for who in land_layer(world, polity).get("authorities", {}).values():
        lines.append(f"  {who['role']}: {who['name']} -- "
                     f"{rulers.trait_phrase(who)} (named day {who['since']})")
    return lines


def world_lines(world: dict) -> list[str]:
    """The DM's inventory of the world layer (`world`): every land's band,
    what it holds, what it derives, the sky and the spell behind it, the
    cards standing over it on all three tracks, and how deep its decks
    still are."""
    lines = list(war_lines(world))
    lines.append("")
    lines.append("-- the world --")
    for polity, land in world["lands"].items():
        layer = land["world"]
        lines.append("")
        lines.append(f"{land['name']} -- {layer['wealth'].upper()} "
                     f"(rolled to day {layer['rolled_day']})")
        lines.extend(politics_lines(world, polity))
        sky = layer.get("weather")
        if sky:
            spell = (f"wet {layer.get('wet', 0)}"
                     if layer.get("wet") else f"dry {layer.get('dry', 0)}")
            lines.append(f"  sky: {sky_phrase(world, polity, sky)} "
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
            lines.append(f"  {track} card: {drawn['name']} "
                         f"(day {live['day']}, stands to day "
                         f"{live['until']})")
        who = layer.get("necromancer")
        if who is not None:
            lines.append(f"  the fog's cause: {who['name']}, L{who['level']} "
                         f"(named day {who['since']})")
        # The three outlets, as the DM needs to read them (2026-08-09): what
        # the board is doing here, what the shelf costs, and who is out on
        # the roads that would not be there otherwise.
        shift, pay = board_shift(world, polity), board_pay(world, polity)
        lines.append(f"  board: {shift:+d} slot(s), pay x{pay:.2f}")
        for posting in board_postings(world, polity):
            lines.append(f"    posts: {posting['job']['title']} "
                         f"(x{posting['pay']:.2f}, {posting['card']})")
        terms = menu_terms(world, polity)
        if terms:
            lines.append("  menu: " + ", ".join(
                f"{k} x{v:.2f}" for k, v in terms.items()))
        for entry in encounter_entries(world, polity):
            lines.append(f"  road: {entry['as']} "
                         f"({entry.get('where', 'any')}, "
                         f"{int(entry.get('chance', ENCOUNTER_CHANCE) * 100)}%)")
        # ...and the sixth outlet's standing half (2026-08-11): what this
        # land's counters are selling, and what the world state has made
        # robbable while nobody was looking.
        selling = options_here(world, polity)
        if selling:
            lines.append("  sells: " + ", ".join(
                f"{o['name']} {option_price(world, polity, o)}s"
                for o in selling))
        marks = sorted({cat for state_id in state_ids(world, polity)
                        for cat in STATE_MARKS.get(state_id, {})})
        if marks:
            lines.append("  marks: " + ", ".join(marks))
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
    "dust-storm": "a dust storm covers the plain -- nothing moves while it blows",
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

QUEST_KEYS = ("post", "pay", "slots", "reprice")
JOB_KEYS = ("title", "desc", "pool", "sites", "giver", "epilogue",
            "failure_epilogue", "places", "skins", "align")
ENCOUNTER_KEYS = ("kinds", "where", "as", "skins", "chance")


def _validate_quest(key: str, spec: dict) -> None:
    """The quest outlet's three verbs: post, cancel (a negative `slots`),
    reprice."""
    unknown = set(spec) - set(QUEST_KEYS)
    if unknown:
        raise ValueError(f"{key}: not a quest term: {sorted(unknown)}")
    for name in ("pay", "reprice"):
        if name in spec and not 0 < float(spec[name]) <= 4:
            raise ValueError(f"{key}: {name} out of range: {spec[name]}")
    if "slots" in spec and not isinstance(spec["slots"], int):
        raise ValueError(f"{key}: slots is a whole number of postings")
    posted = spec.get("post")
    if posted is None:
        return
    if not isinstance(posted, dict):
        raise ValueError(f"{key}: a posted job is a template -- see job()")
    missing = [k for k in JOB_KEYS if k not in posted]
    if missing:
        raise ValueError(f"{key}: the posted job wants {missing}")
    if not posted["pool"]:
        raise ValueError(f"{key}: the posted job draws from no pool")
    for kind in posted["pool"] + tuple(posted["skins"]):
        if kind not in FOES:
            raise ValueError(f"{key}: no such foe row: {kind}")
    if not posted["sites"]:
        raise ValueError(f"{key}: the posted job has nowhere to happen")
    if posted["places"] > len(posted["sites"]):
        raise ValueError(f"{key}: the posted job wants more places than it "
                         f"names sites")


def _validate_menu(key: str, spec: dict) -> None:
    unknown = set(spec) - set(MENU_TERMS)
    if unknown:
        raise ValueError(f"{key}: not a priced term: {sorted(unknown)}")
    for name, mult in spec.items():
        if not 0 < float(mult) <= MENU_CEILING:
            raise ValueError(f"{key}: {name} out of range: {mult}")


def _validate_encounter(key: str, spec: dict) -> None:
    unknown = set(spec) - set(ENCOUNTER_KEYS)
    if unknown:
        raise ValueError(f"{key}: not an encounter term: {sorted(unknown)}")
    if not spec.get("kinds"):
        raise ValueError(f"{key}: an encounter entry with no foes in it")
    for kind in tuple(spec["kinds"]) + tuple(spec.get("skins") or ()):
        if kind not in FOES:
            raise ValueError(f"{key}: no such foe row: {kind}")
    if spec.get("where", "any") not in ENCOUNTER_WHERE:
        raise ValueError(f"{key}: no such ground: {spec.get('where')}")
    if not 0 < float(spec.get("chance", ENCOUNTER_CHANCE)) <= 1:
        raise ValueError(f"{key}: chance out of range: {spec.get('chance')}")
    if not spec.get("as"):
        raise ValueError(f"{key}: an encounter entry says what it IS")


def _validate_menu_tables() -> None:
    """The no-double-charging discipline, per TERM: if a card already moves
    `goods` and the state it sets moves `goods` too, the two halves multiply
    every time that card stands and the shelf reads as a bug. Different
    terms on the two halves are fine and are the normal case -- the toll
    belongs to the tax farmer, the bread price belongs to the shortage he
    leaves behind."""
    for state_id, table in STATE_MENU.items():
        if state_id not in STATE_WORDS:
            raise ValueError(f"STATE_MENU: no such state: {state_id}")
        _validate_menu(f"state {state_id}", table)
        for drawn in CARDS:
            state = drawn["outlets"].get("state") or {}
            own = set(state.get("while", ())) | set(state.get("set", ()))
            own |= set((state.get("slot") or {}).values())
            clash = set(drawn["outlets"].get("menu") or {}) & set(table)
            if state_id in own and clash:
                raise ValueError(
                    f"{drawn['key']} prices {sorted(clash)} on {state_id} "
                    f"itself -- take it out of STATE_MENU or off the card")


def _validate_politics(drawn: dict) -> None:
    """The politics rung's admits and effects, checked against the authored
    tables. Every one of them names a slot value, so a typo is a card that
    silently never fires -- which is exactly the bug import-time validation
    exists to stop."""
    key, admits_ = drawn["key"], drawn["admits"]
    lands = ([p for p in LAND_SPECS] if ANY_LAND in drawn["land"]
             else list(drawn["land"]))
    for word in admits_.get("tension", ()):
        if not any(word in {t["key"] for t in TENSIONS[p]} for p in lands):
            raise ValueError(f"{key}: no land of its own has tension {word}")
    for word in admits_.get("constitution", ()):
        if not any(word in {c["key"] for c in CONSTITUTIONS[p]}
                   for p in lands):
            raise ValueError(f"{key}: no land of its own has constitution "
                             f"{word}")
    for word in admits_.get("traits", ()):
        if word not in rulers.VOCABULARY:
            raise ValueError(f"{key}: no such ruler trait: {word}")
    for word in admits_.get("succession", ()):
        if word not in rulers.SUCCESSIONS:
            raise ValueError(f"{key}: no such succession state: {word}")
    live = {e["key"]: e for e in FACTION_EDGES}
    for word in admits_.get("edge", ()):
        if word not in live:
            raise ValueError(f"{key}: no such faction edge: {word}")
        if not set(live[word]["land"]) & set(lands):
            raise ValueError(f"{key}: faction edge {word} is another "
                             f"land's")
    state = drawn["outlets"].get("state") or {}
    if state.get("constitution"):
        if len(lands) != 1:
            raise ValueError(f"{key}: a constitution flip belongs to ONE "
                             f"land's own slot")
        if state["constitution"] not in {c["key"]
                                         for c in CONSTITUTIONS[lands[0]]}:
            raise ValueError(f"{key}: {lands[0]} has no constitution "
                             f"{state['constitution']}")
    if (state.get("succession")
            and state["succession"] not in rulers.SUCCESSIONS):
        raise ValueError(f"{key}: no such succession state: "
                         f"{state['succession']}")


def _validate_politics_tables() -> None:
    """The authored politics tables themselves: every land has a
    constitution and a tension list, every tension names blocs that exist,
    every standing tension is in its land's list, and every faction edge
    joins two blocs of its own land."""
    for polity in LAND_SPECS:
        if not CONSTITUTIONS.get(polity):
            raise ValueError(f"{polity}: no constitution slot")
        if not TENSIONS.get(polity):
            raise ValueError(f"{polity}: no standing tensions")
        seen: set[str] = set()
        for spec in CONSTITUTIONS[polity]:
            if spec["key"] in seen:
                raise ValueError(f"{polity}: duplicate constitution "
                                 f"{spec['key']}")
            seen.add(spec["key"])
            if spec["weight"] < 1:
                raise ValueError(f"{polity}/{spec['key']}: a slot entry "
                                 f"that never rolls")
            if not spec["name"].isupper() or not spec["name"].isascii():
                raise ValueError(f"{polity}/{spec['key']}: the slot's name "
                                 f"is an ASCII display header")
        keys = {t["key"] for t in TENSIONS[polity]}
        if len(keys) != len(TENSIONS[polity]):
            raise ValueError(f"{polity}: duplicate tension key")
        for word in STANDING_TENSIONS.get(polity, ()):
            if word not in keys:
                raise ValueError(f"{polity}: standing tension {word} is "
                                 f"not in its own list")
        rollable = keys - set(STANDING_TENSIONS.get(polity, ()))
        if len(rollable) < CRISIS_TENSION_ROLLS:
            raise ValueError(f"{polity}: fewer rollable tensions than a "
                             f"crisis land draws")
        for spec in TENSIONS[polity]:
            for name in spec["factions"]:
                if name not in FACTIONS:
                    raise ValueError(f"{polity}/{spec['key']}: no such "
                                     f"faction: {name}")
    cast_of: dict[str, set[str]] = {
        polity: {name for spec in TENSIONS[polity]
                 for name in spec["factions"]} for polity in TENSIONS}
    seen_edges: set[str] = set()
    for live in FACTION_EDGES:
        if live["key"] in seen_edges:
            raise ValueError(f"duplicate faction edge: {live['key']}")
        seen_edges.add(live["key"])
        if not live["land"] or any(p not in LAND_SPECS
                                   for p in live["land"]):
            raise ValueError(f"{live['key']}: no such land")
        for polity in live["land"]:
            for side in ("from", "to"):
                if live[side] not in cast_of[polity]:
                    raise ValueError(f"{live['key']}: {live[side]} is not a "
                                     f"bloc any {polity} tension names")
    for face in FACTIONS.values():
        if face["face"] and face["face"] not in ("ruler", "sage",
                                                 "wildcard"):
            raise ValueError(f"{face['key']}: no such notable post: "
                             f"{face['face']}")

def _validate_lore_tables() -> None:
    """The religion & magic rung's two record kinds (2026-08-11): every fact
    belongs to a land and says something, every option names a real term, a
    real tier and real states, and no option is dead data -- an option whose
    gate no card in the game can open would never appear at a counter.

    A fact may name ANY_LAND since 2026-08-21 (the Miners' League): a belief
    that follows the pits rather than the crown is every land's, exactly the
    way a card is."""
    seen: set[str] = set()
    for entry in FACTS:
        for polity in entry["land"]:
            if polity != ANY_LAND and polity not in LAND_SPECS:
                raise ValueError(f"fact {entry['key']}: no such land")
        if entry["key"] in seen:
            raise ValueError(f"duplicate fact: {entry['key']}")
        seen.add(entry["key"])
        if not entry["title"].isupper() or not entry["title"].isascii():
            raise ValueError(f"fact {entry['key']}: the title is an ASCII "
                             f"display header")
        if not entry["line"].isascii():
            raise ValueError(f"fact {entry['key']}: not ASCII")
    for polity in LAND_SPECS:
        if not FACTS_BY_LAND[polity]:
            raise ValueError(f"{polity}: no standing facts")
    settable = {s for c in CARDS for group in ("set", "while")
                for s in (c["outlets"].get("state") or {}).get(group, ())}
    seen, words = set(), set()
    for spec in OPTIONS:
        key = spec["key"]
        if key in seen:
            raise ValueError(f"duplicate option: {key}")
        seen.add(key)
        word = option_word(spec)
        if word in words:      # the player types the bare word, so it has
            raise ValueError(  # to be unique across the whole catalogue
                f"{key}: two options answer to `service {word}`")
        words.add(word)
        for polity in spec["land"]:
            if polity not in LAND_SPECS:
                raise ValueError(f"{key}: no such land: {polity}")
        if spec["term"] not in MENU_TERMS:
            raise ValueError(f"{key}: not a priced term: {spec['term']}")
        if spec["silver"] < 1:
            raise ValueError(f"{key}: a service nobody charges for")
        for state_id in spec["states"] + spec["without"]:
            if state_id not in STATE_WORDS:
                raise ValueError(f"{key}: no such state: {state_id}")
        for state_id in spec["states"]:
            if state_id not in settable:
                raise ValueError(f"{key}: nothing in the game ever sets "
                                 f"{state_id} -- the option is dead data")
        for word in spec["tension"]:
            if not any(word in {t["key"] for t in TENSIONS[p]}
                       for p in spec["land"]):
                raise ValueError(f"{key}: no land of its own has tension "
                                 f"{word}")
        for kind in spec["kinds"]:
            if kind not in ("village", "town", "capital"):
                raise ValueError(f"{key}: no such settlement tier: {kind}")
        if spec["does"] == "bless" and not (spec["gives"] and spec["days"]):
            raise ValueError(f"{key}: a blessing wants a value and a "
                             f"cooldown")
        if spec["does"] == "sky":
            if spec["word"] not in WEATHER_WORDS:
                raise ValueError(f"{key}: no such weather: {spec['word']}")
            if spec["holds"] < 1:
                raise ValueError(f"{key}: a bought sky holds for a day at "
                                 f"least")
        if not spec["line"].isascii() or not spec["name"].isascii():
            raise ValueError(f"{key}: not ASCII")
    for state_id, table in STATE_MARKS.items():
        if state_id not in STATE_WORDS:
            raise ValueError(f"STATE_MARKS: no such state: {state_id}")
        for category, roles in table.items():
            if not roles:
                raise ValueError(f"STATE_MARKS/{state_id}: {category} adds "
                                 f"no marks")
            for role in roles:
                if not role.isascii():
                    raise ValueError(f"STATE_MARKS/{state_id}: not ASCII")


EXTERNAL_STATES = ("sky-bought",    # set by a verb, not by any card
                   "at-war")        # ...and by the war roll at worldgen


def _validate_reachability(cards) -> None:
    """No card may wait on a state nothing can put in front of it.

    The trap this exists for (found 2026-08-12, seven cards deep): a track
    draws only while its live slot is FREE, and `roll_land` expires the
    live card -- dropping its `while` states -- before it draws on the same
    track. So a state held only as a same-track card's `while` is never
    visible to that track's own draw: while it is held the slot is full,
    and the day the slot frees it is gone. A chain link must ride a state
    that OUTLIVES its setter (`set`, a slot value, a relation's derived
    state) or one another track holds up."""
    outlives: set[str] = set(EXTERNAL_STATES)
    outlives.update(r["then"] for r in RELATIONS)
    held_while: dict[str, set[str]] = {}
    for drawn in cards:
        state = drawn["outlets"].get("state") or {}
        outlives.update(state.get("set", ()))
        outlives.update((state.get("slot") or {}).values())
        for state_id in state.get("while", ()):
            held_while.setdefault(state_id, set()).add(drawn["track"])
    for drawn in cards:
        for state_id in drawn["admits"]["states"]:
            tracks = held_while.get(state_id, set())
            if (state_id not in outlives
                    and not (tracks - {drawn["track"]})):
                raise ValueError(
                    f"{drawn['key']}: admits on {state_id}, which "
                    f"{'only its own track holds while live' if tracks else 'nothing produces'}"
                    f" -- the card can never fire")


def _validate_state_tables() -> None:
    """A STATE_MENU / STATE_ENCOUNTERS / STATE_MARKS row keyed on a state
    nothing produces is dead data (deposit-dead was the shipped example)."""
    producible: set[str] = set(EXTERNAL_STATES)
    producible.update(r["then"] for r in RELATIONS)
    for drawn in CARDS:
        state = drawn["outlets"].get("state") or {}
        producible.update(state.get("set", ()))
        producible.update(state.get("while", ()))
        producible.update((state.get("slot") or {}).values())
    for table_name, table in (("STATE_MENU", STATE_MENU),
                              ("STATE_ENCOUNTERS", STATE_ENCOUNTERS),
                              ("STATE_MARKS", STATE_MARKS)):
        for state_id in table:
            if state_id not in producible:
                raise ValueError(f"{table_name}: {state_id} -- nothing in "
                                 f"the game produces that state")


def _validate_countries() -> None:
    """The world layer against the fixed Europe map (2026-08-15, Europe MVP
    Closure; over NINE countries since 2026-08-21). The contraction used to
    be enforced by FILTERING the catalog at import, which meant a packet
    could go missing without anything noticing. Nothing filters now, so this
    says out loud what every country owes: its own deck on every track it
    can draw from, its own lore, and a place in the relations table -- an
    isolated country is a country whose neighbours' troubles never reach
    it."""
    if set(LAND_SPECS) != set(CULTURE_OF):
        raise ValueError("the world layer reads its countries off the "
                         f"catalog, got {tuple(LAND_SPECS)}")
    for culture in set(CULTURE_OF.values()):
        if culture not in CULTURES:
            raise ValueError(f"{culture}: a culture with no lands")
    for polity in LAND_SPECS:
        for track in TRACKS:
            if not [c for c in CARDS
                    if c["track"] == track and in_land(c, polity)]:
                raise ValueError(f"{polity}: no {track} card can be drawn "
                                 f"there")
        if not FACTS_BY_LAND.get(polity):
            raise ValueError(f"{polity}: no standing lore")
        if not [e for e in RELATIONS
                if polity in (e["from"], e["to"])]:
            raise ValueError(f"{polity}: no relation reaches it")
        if polity not in CAPITAL_TILES:
            raise ValueError(f"{polity}: no capital Tile, so no sky to "
                             f"read while the party is elsewhere")


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
        _validate_politics(drawn)
        _validate_quest(key, drawn["outlets"].get("quest") or {})
        _validate_menu(key, drawn["outlets"].get("menu") or {})
        if drawn["outlets"].get("encounter"):
            _validate_encounter(key, drawn["outlets"]["encounter"])
        if not drawn["outlets"]:
            raise ValueError(f"{key}: a card with no outlet effect")
        if len(drawn["outlets"]) > len(OUTLETS):
            raise ValueError(f"{key}: more than {len(OUTLETS)} outlets")
    _validate_reachability(CARDS)
    _validate_state_tables()
    _validate_menu_tables()
    _validate_politics_tables()
    _validate_lore_tables()
    _validate_countries()
    for state_id, entry in STATE_ENCOUNTERS.items():
        if state_id not in STATE_WORDS:
            raise ValueError(f"STATE_ENCOUNTERS: no such state: {state_id}")
        _validate_encounter(f"state {state_id}", entry)
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
    if sum(length for _name, length in SEASONS) != YEAR_DAYS:
        raise ValueError("the season calendar does not fill the year")
    for climate, profile in CLIMATE_PROFILES.items():
        if not profile.get("drought_days"):
            raise ValueError(f"{climate}: no drought threshold")
        if climate not in CLIMATE_WEATHER:
            raise ValueError(f"{climate}: no sky of its own")
    for climate, seasons in CLIMATE_WEATHER.items():
        if climate not in CLIMATE_PROFILES:
            raise ValueError(f"no such climate: {climate}")
        for column, weights in seasons.items():
            if set(weights) != set(WEATHER_WORDS):
                raise ValueError(f"{climate}/{column}: the sky is nine "
                                 f"words, got {sorted(weights)}")
            if sum(weights.values()) != 100:
                raise ValueError(f"{climate}/{column}: the weights are per "
                                 f"hundred days, got "
                                 f"{sum(weights.values())}")
    for ground, local in WEATHER_LOCAL.items():
        if ground not in CLIMATE_PROFILES \
                and ground not in WEATHER_LOCAL_TERRAINS:
            raise ValueError(f"no such ground: {ground}")
        for word in local:
            if word not in WEATHER_WORDS:
                raise ValueError(f"{ground}: no such weather: {word}")


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
    # The wars settle beside the lands (2026-08-22): the eyeball dump is a
    # day-settling seam like any other, and a front rolled to day 0 under a
    # world rolled to day 200 would be the one lie on the page.
    import conquest                     # runtime: conquest imports quests,
    conquest.roll_campaigns(world, args.days)   # which imports this file
    for line in world_lines(world):
        print(line)
    print("")
    print("-- what the lands heard --")
    for polity in world["lands"]:
        for line in take_news(world, polity, args.days):
            print(line)
    print("")
    print("-- what the DM reads behind one land --")
    for line in lore_lines(world, next(iter(world["lands"]))):
        print(line)
    print("")
    print("-- a night under the storm --")
    found = cabin(random.Random(args.seed))
    print(f"  SHELTER ({found['kind']}): {found['sight']}")
    print(f"  ({found['dm']})")


if __name__ == "__main__":
    main()
