"""Crime -- free ACTIONS against a leveled world (2026-08-04, THE DARK
REWORK's session B; plan.md has the spec, rules.md's Crime add-on the
played rules).

Crime used to be QUESTS: fifteen dark templates a questgiver handed out,
posted on a shadow board, taken and turned in like any job. The 2026-08-04
design session sorted that apart. What hell WANTS is the occult work --
hellgates, desecration, blood on the altar -- and that stayed a quest
(karma.OCCULT_TEMPLATES, the pinned assignment ladder). Everything else
was crime, and crime is not work anyone hands out:

    the PC does the thing because they want to, and keeps whatever
    material gain directly follows.

So there is no giver, no posting, no turn-in and no board. There is a
CATEGORY (mugging, burglary, the vault heist), a MARK, and a resolution.

**The mark is the difficulty dial** -- the conquest doctrine (geography,
not gates) applied to people. A mark's LEVEL fixes both its wealth and
its protection; availability is gated by the settlement kind (a magnate
does not live in a village); casing is free; and nothing auto-levels to
the party. Farming down is self-defeating because the rewards scale off
the mark: robbing commoners forever pays commoner money forever.

**Casing is free and honest** (the OSR straight-board stance). The local
mark for a category is SEEDED off (world seed, place, day, category), so
`case` and `crime` see exactly the same mark, the same take and the same
protection roster -- nothing is stored between them, and reading the
board costs nothing. Sleeping on it changes the mark: tomorrow rolls a
new one.

**Three shapes**, declared per category:

  petty  -- a trivial check or none at all, never a fight. Flat sin
            (PETTY_SIN) quoted as XP, coin in pennies. A miss is just a
            miss (no take, no sin); the token roster the fiction may want
            -- the pup's mother, the indignant innkeeper -- is the DM's
            `forge`, not the engine's.
  deed   -- 2d6 + stat vs DC (the caper machinery generalized). A MAKE
            takes it clean: the lump, the sin, no fight. A MISS botches
            it into the mark's protection (+WITNESS_SIN), and winning
            that fight still pays the take -- the crime happened, the
            hard way.
  force  -- no check at all: straight to the protection, then the take.
            Fight XP is dark as usual, and the crime lump lands on top.

**Monotony is per-category and TEMPORARY.** Every commission day-stamps
its category; stamps inside MONOTONY_WINDOW count against the next one's
SIN and XP (MONOTONY_MULTS, floor MONOTONY_FLOOR). Gold never
depreciates -- the loot is the loot; it is hell that gets bored.
Alternating two categories does NOT reset either: each window is its
own. A two-crime loop is supposed to stale; a portfolio, or honest days
between sprees, stays fresh. A category's FIRST-EVER commission pays
FIRST_TIME_MULT -- the creativity carrot, pointing at the suggestion
feed.

**Unlocks gate SUGGESTIONS, never permission.** Every category can be
committed from day one. What the unlock ledger buys is ADVERTISING: hell
suggests one new category on the first completed assignment, and one
more per CRIME_UNLOCK_STEP of lifetime sin, in random order. A "locked"
category committed anyway unlocks itself by deed and never consumes a
grant.

The sims and benches never import this file (the karma layer's doctrine
-- no sim plays dark). Every knob here is hand-set and table-tuned;
session.py owns the commands (`case`, `crime`), and the played rules live
in rules.md's Crime add-on and dm.md.

Run:  python crime.py [--seed N]   # the catalog + sample local marks
"""

from __future__ import annotations

import argparse
import random

import karma
from places import stable_seed
from quests import (LADDER_POOL, build_room, room_budget,
                    roster_kinds_line)

# --------------------------------------------------------------------------- #
# The knobs (all hand-set, per the karma layer's standing directive)
# --------------------------------------------------------------------------- #

CRIME_XP_PER_LEVEL = 50     # the crime LUMP: this x the mark's level x the
                            # category multiplier. An at-level quest quotes
                            # ~100L, so a crime is half a job -- because a
                            # crime is ONE SCENE, not an expedition. All of
                            # it is sin (it is dark work by construction)
CRIME_GOLD_PER_LEVEL = 20   # the coin take: this x mark level x the same
                            # category multiplier. A quest pays 15L a site
                            # plus the dark premium, so a crime lands in
                            # family with one site's honest pay
FENCE_RATE = 0.5            # goods crimes (jewels, relics, cattle, a
                            # wagon's freight) pay what the FENCE gives,
                            # not what the thing is worth. The gap is the
                            # reason coin crimes exist
PETTY_SIN = (10, 15)        # petty crime's flat sin/XP, rolled -- small,
                            # and all of it sin (designer call: petty crime
                            # pays XP). Never scaled by the mark: a kicked
                            # puppy is a kicked puppy
PETTY_GOLD = (1, 5)         # ...and its coin, in pennies

MONOTONY_WINDOW = 10        # days a commission stays on its category's
                            # record for monotony purposes
MONOTONY_MULTS = (1.0, 1.0, 0.5, 0.25)   # sin/XP multiplier by how many
                                          # stamps are ALREADY in the window
MONOTONY_FLOOR = 0.25       # past the table's end
FIRST_TIME_MULT = 1.5       # a category's first-EVER commission

WITNESS_SIN = karma.DEED_FAIL_KARMA     # a botched deed is talked about --
                                        # the caper's number, shared on
                                        # purpose (one rule, two customers)

CRIME_UNLOCK_STEP = 200     # lifetime sin per suggestion after the first.
                            # The full catalogue lands around 4,750 lifetime
                            # sin: the XP budget to L20 is 19,000 quoted, at
                            # most half of it can be sin if heat is ever to
                            # come down (each sin point wants a penance
                            # point), and half of THAT again is the target

SUGGESTIONS_SHOWN = 3       # how many unlocked-but-uncommitted categories
                            # the feed advertises at a time


# --------------------------------------------------------------------------- #
# The mark bands -- level fixes WEALTH and PROTECTION together
# --------------------------------------------------------------------------- #
# Availability is by place kind, the garrison-band logic applied to people:
# a village holds nobody worth a heist, a capital holds everything. The
# WILDS admit the bands that TRAVEL -- the road is where a merchant's
# caravan and the crown's tax cart actually are -- which is what makes
# highway work a real ladder instead of a village-capped one.

MARK_BANDS = (
    dict(key="commoner", label="commoner",
         roles=("a commoner", "a stray dog", "an unpaid lunch",
                "a drunk with a full purse", "a farmhand"),
         levels=(1, 2),
         where=("village", "town", "capital", "wilds")),
    dict(key="tradesman", label="tradesman",
         roles=("a tradesman", "an innkeeper", "a miller", "a carter",
                "a smith"),
         levels=(2, 4),
         where=("village", "town", "capital", "wilds")),
    dict(key="merchant", label="merchant",
         roles=("a merchant", "a priest", "a wool factor",
                "a caravan master"),
         levels=(4, 7),
         where=("town", "capital", "wilds")),
    dict(key="notable", label="notable",
         roles=("a guild master", "a noble", "a magistrate",
                "the abbot"),
         levels=(8, 12),
         where=("town", "capital")),
    dict(key="magnate", label="magnate",
         roles=("a magnate", "the high temple", "the bank of three lands",
                "the ducal house"),
         levels=(12, 16),
         where=("capital",)),
    dict(key="crown", label="the crown",
         roles=("the royal vault", "the crown's tax cart",
                "the king's own treasury"),
         levels=(16, 20),
         where=("capital", "wilds")),
)

BANDS_BY_KEY = {b["key"]: b for b in MARK_BANDS}


def band_of(key: str) -> dict:
    return BANDS_BY_KEY[key]


# --------------------------------------------------------------------------- #
# The protection -- recycled scene material (karma.CRIME_FODDER)
# --------------------------------------------------------------------------- #
# The fifteen retired crime TEMPLATES kept their rosters and skins when
# they stopped being quests (session A). A category names one by title and
# wears its pool and display names over a build_room budget at the MARK's
# level -- so the merchant's vault guards and the village militia are the
# same faces they always were, now sized by who is being robbed.

_FODDER = {t["title"]: t for t in karma.CRIME_FODDER}

# The fallback for categories the fodder never covered: a plain hired
# watch. Ordinary people who object, which is the whole doctrine -- the
# engine only ever fights things that fight back.
GUARD_POOL = LADDER_POOL
GUARD_SKINS = {"cutthroat": "Hired Knife", "archer": "Watchful Bowman",
               "bruiser": "Heavy Guard", "soldier": "Hired Guard",
               "veteran": "Guard Sergeant", "champion": "Guard Captain",
               "blademaster": "the House Duelist",
               "warlord": "the Lord's Champion"}


def protection_dress(cat: dict) -> tuple[tuple[str, ...], dict]:
    """(pool, skins) for a category's protection roster: its named fodder
    template's, or the plain hired watch."""
    tpl = _FODDER.get(cat.get("fodder", ""))
    if tpl is None:
        return GUARD_POOL, GUARD_SKINS
    return tuple(tpl["pool"]), dict(tpl["skins"])


# --------------------------------------------------------------------------- #
# The catalogue (27 categories: 5 petty, 10 deeds, 12 force)
# --------------------------------------------------------------------------- #
# Nothing grim: writing.md's cartoon register gates this list. Every entry
# is theft, arson, extortion, hubris or a kicked puppy -- indignant
# victims, never brutalized ones.
#
# Fields:
#   key    -- the command word (`case burglary` / `crime burglary`)
#   name   -- the display name
#   shape  -- petty | deed | force
#   stat   -- petty/deed: the check's stat ("str"/"dex"/"mind"/"cha")
#   dc     -- petty/deed: the DC (10-11 against stats 3-5, caper doctrine)
#   bands  -- which mark bands this crime can draw
#   where  -- which place kinds this crime is committed in (default: the
#             three settlement kinds). ROAD work names the wilds instead --
#             a caravan is robbed on the road, never inside the walls
#   pay    -- "coin" (full) | "goods" (fenced at FENCE_RATE) | None (no take)
#   mult   -- the category multiplier on the lump AND the coin
#   fodder -- the retired template whose roster/skins dress the protection
#   roles  -- optional per-band mark faces, where the band's generic list
#             would read wrong (the puppy is not "a farmhand")
#   line   -- what the crime IS, one deadpan sentence
#   hint   -- what stands in the way (the casing report's protection note)

SETTLEMENT_KINDS = ("village", "town", "capital")

CATEGORIES: list[dict] = [
    # ----------------------------- petty ---------------------------------- #
    dict(key="puppy", name="Kick the Puppy", shape="petty",
         stat=None, dc=None, bands=("commoner",), pay=None, mult=0.0,
         fodder="Kick the Puppy",
         roles={"commoner": ("a stray puppy", "a widow's puppy",
                             "a very small dog")},
         line="A puppy sits in a doorway. Kick it into the alley.",
         hint="Nobody guards a puppy. Its mother is another matter."),
    dict(key="dash", name="Dine and Dash", shape="petty",
         stat="cha", dc=9, bands=("tradesman",), pay="coin", mult=0.0,
         fodder="Dine and Dash",
         roles={"tradesman": ("an innkeeper", "a cookshop keeper",
                              "the good table at the sign of the Swan")},
         line="Eat the good dinner. Leave through the kitchen.",
         hint="An innkeeper, a cook, and a door."),
    dict(key="dice", name="Cheat at Dice", shape="petty",
         stat="cha", dc=10, bands=("commoner", "tradesman"), pay="coin",
         mult=0.0, fodder=None,
         roles={"commoner": ("a table of drunks", "a soldier on leave",
                             "a lucky farmhand")},
         line="The dice are loaded. Keep talking while they roll.",
         hint="Drunks, and one of them counts."),
    dict(key="vandalism", name="Petty Vandalism", shape="petty",
         stat=None, dc=None, bands=("commoner", "tradesman"), pay=None,
         mult=0.0, fodder=None,
         line="Break the shutters. Paint the door. Salt the window box.",
         hint="Nothing. That is the point."),
    dict(key="pickpocket", name="Pickpocket a Commoner", shape="petty",
         stat="dex", dc=10, bands=("commoner", "tradesman"), pay="coin",
         mult=0.0, fodder=None,
         roles={"commoner": ("a drunk with a full purse", "a commoner",
                             "a pilgrim counting his coppers")},
         line="A purse hangs at a belt in a crowd. Take it.",
         hint="A crowd, and whoever in it is looking."),

    # ------------------------------ deeds --------------------------------- #
    dict(key="burglary", name="Burglary", shape="deed",
         stat="dex", dc=11, bands=("tradesman", "merchant", "notable"),
         pay="goods", mult=1.0, fodder="Steal the Jewel",
         line="Go in through the roof, take what is loose, leave the "
              "rest.",
         hint="House guards, and a dog that does not sleep."),
    dict(key="heist", name="The Vault Heist", shape="deed",
         stat="mind", dc=11,
         bands=("merchant", "notable", "magnate", "crown"),
         pay="coin", mult=1.25, fodder="Rob the Vault",
         line="The vault opens between patrols, or it does not open.",
         hint="Clerks, hall guards, and the vault's own men."),
    dict(key="con", name="The Con", shape="deed",
         stat="cha", dc=10, bands=("tradesman", "merchant", "notable"),
         pay="coin", mult=1.0, fodder=None,
         line="Sell them a saint's finger bone. There are many fingers.",
         hint="A mark's household, once the bone is examined."),
    dict(key="counterfeit", name="Counterfeiting", shape="deed",
         stat="mind", dc=11, bands=("merchant", "notable", "magnate"),
         pay="coin", mult=1.0, fodder="Rob the Vault",
         line="Press the coin, sweat the edge, spend it far from the "
              "press.",
         hint="Assayers, then the guards the assayers call."),
    dict(key="blackmail", name="Blackmail", shape="deed",
         stat="cha", dc=10, bands=("merchant", "notable", "magnate"),
         pay="coin", mult=1.0, fodder="Take the Mansion",
         line="You know what they did. Name a price for forgetting it.",
         hint="Household men, sent quietly and told to be thorough."),
    dict(key="impersonate", name="Impersonate an Official", shape="deed",
         stat="cha", dc=11, bands=("merchant", "notable", "magnate"),
         pay="coin", mult=1.0, fodder="Take Over the Road",
         line="Wear the sash. Collect the fee. Sign the receipt.",
         hint="Real officials, and the soldiers who escort them."),
    dict(key="poison", name="Poison the Feast", shape="deed",
         stat="mind", dc=10, bands=("merchant", "notable", "magnate"),
         pay="coin", mult=1.0, fodder="Poison the Feast",
         line="Into the drink, while the room is loud.",
         hint="Servants, and the guards who stayed sober."),
    dict(key="graverob", name="Grave-Robbing", shape="deed",
         stat="dex", dc=10, bands=("tradesman", "merchant", "notable"),
         pay="goods", mult=1.0, fodder="Rob the Tomb",
         line="The good rings go in with the good families. Dig.",
         hint="Whatever the family buried to keep diggers out."),
    dict(key="powder", name="The Powder Trade", shape="deed",
         stat="mind", dc=11, bands=("tradesman", "merchant", "notable"),
         pay="goods", mult=1.0, fodder="Sell the Powder",
         line="Move the sacks at night. Take the price at dawn.",
         hint="The local gang, who had this street first."),
    dict(key="rustling", name="Cattle Rustling", shape="deed",
         stat="dex", dc=10, bands=("commoner", "tradesman", "merchant"),
         where=("village", "wilds"),
         pay="goods", mult=1.0, fodder="Burn the Granary",
         roles={"commoner": ("a smallholder's four cows",
                             "a widow's milk herd"),
                "tradesman": ("a drover's string", "a farmer's herd"),
                "merchant": ("a cattle factor's drive",
                             "the abbey's fat herd")},
         line="Cut the fence, walk the herd, be two valleys away by "
              "morning.",
         hint="Herdsmen, dogs, and a hired night guard."),

    # ------------------------------ force --------------------------------- #
    dict(key="mugging", name="Mugging", shape="force",
         stat=None, dc=None, bands=("commoner", "tradesman", "merchant"),
         pay="coin", mult=1.0, fodder=None,
         line="Step out of the doorway. Ask for everything.",
         hint="Whoever walks with them."),
    dict(key="racket", name="Protection Racket", shape="force",
         stat=None, dc=None, bands=("tradesman", "merchant", "notable"),
         pay="coin", mult=1.0, fodder="Collect Protection Money",
         line="A fine shop. It would be a shame. Collect weekly.",
         hint="The guards the street hired the last time this happened."),
    dict(key="debt", name="Strong-Arm Debt Collection", shape="force",
         stat=None, dc=None, bands=("commoner", "tradesman", "merchant"),
         pay="coin", mult=1.0, fodder="Collect the Debt",
         line="They owe. Explain the interest with both hands.",
         hint="A debtor's neighbors, who have also been explained to."),
    dict(key="highway", name="Highway Robbery", shape="force",
         stat=None, dc=None, bands=("commoner", "tradesman", "merchant"),
         where=("wilds",),
         pay="goods", mult=1.0, fodder="Take Over the Road",
         roles={"commoner": ("a carter and his mule",
                             "two pilgrims and a handcart"),
                "tradesman": ("a pedlar's wagon", "a carrier's dray"),
                "merchant": ("a wool train", "a merchant's coach")},
         line="A rope across the road at the narrow place.",
         hint="Outriders, and travellers who fight for their carts."),
    dict(key="taxcart", name="Rob the Tax Collector", shape="force",
         stat=None, dc=None, bands=("crown",), where=("wilds",),
         pay="coin", mult=1.25, fodder="Take Over the Road",
         roles={"crown": ("the crown's tax cart",
                          "the shire's whole year, in one box")},
         line="The crown's own coin, in one box, on one road.",
         hint="An armed escort. This one is answered for."),
    dict(key="arson", name="Arson", shape="force",
         stat=None, dc=None, bands=("tradesman", "merchant", "notable"),
         pay="coin", mult=1.0, fodder="Burn the Granary",
         line="Straw, lamp oil, an open door, and a long walk.",
         hint="Night guards, and a very awake dog."),
    dict(key="kidnap", name="Kidnapping for Ransom", shape="force",
         stat=None, dc=None, bands=("merchant", "notable", "magnate"),
         pay="coin", mult=1.25, fodder="Take the Mansion",
         line="Take the heir. Write politely. Wait.",
         hint="A household that expected exactly this."),
    dict(key="jailbreak", name="Jailbreak", shape="force",
         stat=None, dc=None, bands=("tradesman", "merchant", "notable"),
         pay="coin", mult=0.75, fodder=None,
         line="Somebody useful is in a cell. Open it.",
         hint="Gaolers, and the watch two streets away."),
    dict(key="caravan", name="Caravan Robbery", shape="force",
         stat=None, dc=None, bands=("merchant", "notable"),
         where=("wilds",), pay="goods",
         mult=1.1, fodder="Steal the Jewel",
         roles={"merchant": ("a twelve-wagon train",
                             "a spice caravan two days out"),
                "notable": ("a guild convoy under contract",
                            "a noble house's baggage train")},
         line="Twelve wagons, four days out, nobody expected within "
              "shouting.",
         hint="Paid outriders who have done this before."),
    dict(key="raid", name="The Village Raid", shape="force",
         stat=None, dc=None, bands=("tradesman", "merchant"),
         where=("village", "wilds"), pay="coin",
         mult=1.25, fodder="Loot the Village",
         roles={"tradesman": ("a hamlet with one good barn",
                              "a fishing village"),
                "merchant": ("a market village", "a fat river village")},
         line="Come at night. Take the strongbox and the good horses.",
         hint="A wooden wall and a militia that drills on Sundays."),
    dict(key="landgrab", name="The Land Grab", shape="force",
         stat=None, dc=None, bands=("notable", "magnate"),
         where=("village", "town", "wilds"), pay="coin",
         mult=1.25, fodder="Take the Neighbor's Land",
         roles={"notable": ("a knight's home farm", "a squire's valley"),
                "magnate": ("a ducal estate", "the abbey's best land")},
         line="Ride onto the land. Stay on it until the papers change.",
         hint="Estate guards, huntsmen, and the owner's own sword."),
    dict(key="betrayal", name="Betrayal", shape="force",
         stat=None, dc=None, bands=("tradesman", "merchant", "notable"),
         pay="coin", mult=1.0, fodder="Betray an Old Friend",
         line="Sell out the crew. Then help take them.",
         hint="The crew, who trusted you as far as the door."),
]

BY_KEY = {c["key"]: c for c in CATEGORIES}

SHAPES = ("petty", "deed", "force")


def category(key: str) -> dict | None:
    """Look a category up by key, then by a unique name prefix (the
    player types `case vault`, not `case heist`)."""
    key = (key or "").strip().lower()
    if key in BY_KEY:
        return BY_KEY[key]
    hits = [c for c in CATEGORIES
            if c["name"].lower().startswith(key)
            or key in c["name"].lower()]
    return hits[0] if len(hits) == 1 else None


# --------------------------------------------------------------------------- #
# The ledger (the `crimes` save key)
# --------------------------------------------------------------------------- #
# Two parts on purpose: the per-category record (count, day stamps, the
# unlocked flag -- what monotony, the tally and the feed read), and the
# count of suggestions hell has GRANTED. They are separate so that
# committing a locked category -- which unlocks it by deed, decision 8 --
# never eats a grant the ladder still owes.


def new_crimes() -> dict:
    return {"ledger": {},    # category key -> {count, days, last, unlocked}
            "grants": 0}     # suggestions handed out so far


EMPTY_RECORD = {"count": 0, "days": [], "last": -1, "unlocked": False}


def record_for(crimes: dict, key: str) -> dict:
    """The live record, created on demand. Use `peek` for displays --
    every call here writes a row into the save."""
    return crimes.setdefault("ledger", {}).setdefault(key,
                                                      dict(EMPTY_RECORD))


def peek(crimes: dict, key: str) -> dict:
    """A category's record WITHOUT creating it: a detached copy of the
    empty record when there is none. Reading the catalogue must not write
    27 empty rows into the save."""
    rec = (crimes.get("ledger") or {}).get(key)
    return rec if rec is not None else dict(EMPTY_RECORD)


def recent_days(rec: dict, day: int) -> list[int]:
    """Day stamps still inside the monotony window (the record is pruned
    as it is read -- stamps age out by construction, which is what makes
    monotony temporary)."""
    fresh = [d for d in rec.get("days", []) if day - d < MONOTONY_WINDOW]
    rec["days"] = fresh
    return fresh


def monotony_mult(rec: dict, day: int) -> float:
    n = len(recent_days(rec, day))
    if n < len(MONOTONY_MULTS):
        return MONOTONY_MULTS[n]
    return MONOTONY_FLOOR


def sin_mult(rec: dict, day: int) -> float:
    """The full sin/XP multiplier: the first-EVER commission pays the
    creativity bonus, everything after it pays monotony. (They never
    stack -- a first commission has an empty window anyway.)"""
    if rec.get("count", 0) == 0:
        return FIRST_TIME_MULT
    return monotony_mult(rec, day)


def stamp(crimes: dict, key: str, day: int) -> dict:
    """Book one commission: the count, the day stamp, and the by-deed
    unlock (a crime the player found on their own is never locked again).
    Call AFTER reading sin_mult -- the multipliers describe the state the
    crime was committed against.

    `last` is kept SEPARATELY from `days` (2026-08-04, session C): the
    day stamps age out of the monotony window by design, so the tally's
    'last done' column would forget a career-defining crime ten days
    after it happened. The window is hell's boredom; the tally is the
    record."""
    rec = record_for(crimes, key)
    recent_days(rec, day)
    rec["count"] += 1
    rec["days"].append(day)
    rec["last"] = max(rec.get("last", -1), day)
    rec["unlocked"] = True
    return rec


def lifetime_sin(karma_state: dict) -> int:
    return karma_state.get("sin_total", 0)


def unlocks_due(karma_state: dict, pact: dict | None) -> int:
    """How many SUGGESTIONS hell should have handed out by now: the first
    on the first COMPLETED assignment, one more per CRIME_UNLOCK_STEP of
    lifetime sin thereafter. Pactless saves get none -- nobody is
    advertising."""
    if not pact or pact.get("done", 0) < 1:
        return 0
    return 1 + lifetime_sin(karma_state) // CRIME_UNLOCK_STEP


def refresh_unlocks(crimes: dict, karma_state: dict, pact: dict | None,
                    rng: random.Random) -> list[dict]:
    """Hand out whatever grants are owed, in random order, and return the
    categories newly suggested (the caller prints them). Idempotent: run
    it at any settlement stop."""
    due = unlocks_due(karma_state, pact)
    granted = crimes.get("grants", 0)
    if due <= granted:
        return []
    locked = [c for c in CATEGORIES
              if not peek(crimes, c["key"])["unlocked"]]
    rng.shuffle(locked)
    fresh = locked[:due - granted]
    for c in fresh:
        record_for(crimes, c["key"])["unlocked"] = True
    crimes["grants"] = granted + len(fresh)
    return fresh


def suggestions(crimes: dict, n: int = SUGGESTIONS_SHOWN,
                rng: random.Random | None = None) -> list[dict]:
    """The feed: unlocked categories the party has never committed. This
    is advertising, not permission -- everything is always available.

    Pass an `rng` for a SHUFFLED feed (session C's history page seeds one
    off the world and the day): catalogue order would advertise the same
    two petty crimes forever, because the catalogue is sorted by shape."""
    out = []
    for c in CATEGORIES:
        rec = peek(crimes, c["key"])
        if rec["unlocked"] and rec["count"] == 0:
            out.append(c)
    if rng is not None:
        rng.shuffle(out)
    return out[:n]


def tally_rows(crimes: dict) -> list[tuple[str, int, int]]:
    """(category name, count, last day) for every committed category,
    busiest first -- THE TALLY OF SIN's rows (session C's history page).
    Reads `last`, not the monotony window's day stamps: the window
    forgets on purpose and the tally never does."""
    rows = []
    for c in CATEGORIES:
        rec = (crimes.get("ledger") or {}).get(c["key"])
        if rec and rec["count"]:
            last = rec.get("last", -1)
            if last < 0 and rec.get("days"):
                last = max(rec["days"])
            rows.append((c["name"], rec["count"], last))
    rows.sort(key=lambda r: (-r[1], r[0]))
    return rows


def total_crimes(crimes: dict) -> int:
    """Every commission the ledger has ever booked -- counted off the
    same rows the tally prints, so the total and the rows can never
    disagree (a key the catalogue no longer carries is not a crime)."""
    return sum(count for _, count, _ in tally_rows(crimes))


# --------------------------------------------------------------------------- #
# The mark (rolled off a stable seed -- casing is free AND honest)
# --------------------------------------------------------------------------- #


def where_of(cat: dict) -> tuple[str, ...]:
    """The place kinds a category is committed in -- settlements unless it
    says otherwise (road work names the wilds)."""
    return tuple(cat.get("where") or SETTLEMENT_KINDS)


def bands_here(cat: dict, place_kind: str) -> list[dict]:
    """The mark bands this category can draw where the party stands: the
    crime has to belong here at all, and the place has to hold the band
    (no magnate in a village, no caravan inside the walls)."""
    if place_kind not in where_of(cat):
        return []
    return [band_of(k) for k in cat["bands"]
            if place_kind in band_of(k)["where"]]


def roles_of(cat: dict, band_key: str) -> tuple[str, ...]:
    """The faces this category's mark can wear in a band: the category's
    own list where it has one, the band's generic list otherwise."""
    own = (cat.get("roles") or {}).get(band_key)
    return tuple(own) if own else tuple(band_of(band_key)["roles"])


def available(place_kind: str) -> list[dict]:
    """Every category with a mark where the party stands."""
    return [c for c in CATEGORIES if bands_here(c, place_kind)]


def mark_rng(world_seed: int | None, place_id: str, day: int,
             key: str) -> random.Random:
    """The mark's own stream: stable per (world, place, day, category), so
    `case` and `crime` roll the SAME mark, take and roster on the same
    day, and a new day rolls a new one. Nothing is stored."""
    return random.Random(stable_seed(world_seed, place_id,
                                     f"crime:{key}", day))


def roll_mark(cat: dict, world_seed: int | None, place_id: str,
              place_kind: str, day: int) -> dict | None:
    """The local mark for one category, or None if this category has no
    mark here (a magnate in a village, highway work inside the walls).
    The roster is rolled from the same stream, so the protection hint the
    casing prints IS the protection that fights."""
    bands = bands_here(cat, place_kind)
    if not bands:
        return None
    rng = mark_rng(world_seed, place_id, day, cat["key"])
    band = rng.choice(bands)
    level = rng.randint(*band["levels"])
    role = rng.choice(roles_of(cat, band["key"]))
    return build_mark(cat, band["key"], role, level, rng)


def npc_mark(cat: dict, world_seed: int | None, name: str, level: int,
             day: int) -> dict:
    """A NAMED victim -- a giver, a notable, the innkeeper who talked.
    The DM assigns the band by naming the level; nothing else about the
    mark bands applies, because a person the fiction already put on the
    table is not a slot. Seeded off the name so casing and committing
    agree here too. NPCs are freely attackable and robbable through this
    door: it is the crime layer's override surface."""
    rng = random.Random(stable_seed(world_seed, f"npc:{name}",
                                    f"crime:{cat['key']}", day))
    return build_mark(cat, None, name, max(1, level), rng)


def build_mark(cat: dict, band_key: str | None, role: str, level: int,
               rng: random.Random) -> dict:
    """One resolved mark: who, at what level, what it pays, and who
    stands in front of it. `band_key` is None for a DM-assigned NPC mark
    (`crime X --npc NAME --level N`) -- the band table is the roller's
    tool, not a fence."""
    gold, xp = take_of(cat, level, rng)
    pool, skins = protection_dress(cat)
    kinds = ([] if cat["shape"] == "petty"
             else build_room(room_budget(level, 1.0), pool, rng,
                             final=True))
    return {"category": cat["key"], "band": band_key, "role": role,
            "level": level, "gold": gold, "xp": xp,
            "kinds": kinds, "skins": skins}


def take_of(cat: dict, level: int, rng: random.Random) -> tuple[int, int]:
    """(gold, quoted XP) for one commission at a mark of `level`, before
    the sin/XP multipliers. Petty crime is FLAT -- the mark's level buys
    it nothing, which is exactly why petty crime is a dead end. Gold
    never carries the multipliers: the loot is the loot."""
    if cat["shape"] == "petty":
        xp = rng.randint(*PETTY_SIN)
        if cat["pay"] is None:
            return 0, xp
        return rng.randint(*PETTY_GOLD), xp
    xp = round(CRIME_XP_PER_LEVEL * level * cat["mult"])
    if cat["pay"] is None:
        gold = 0
    else:
        gold = round(CRIME_GOLD_PER_LEVEL * level * cat["mult"])
        if cat["pay"] == "goods":
            gold = round(gold * FENCE_RATE)
    return gold, xp


def check_line(cat: dict) -> str:
    """The one-line statement of what the crime asks of the PC."""
    if cat["shape"] == "force":
        return "no check -- straight through the protection"
    if cat["stat"] is None:
        return "no check -- just do it"
    return f"2d6+{cat['stat'].upper()} vs DC {cat['dc']}"


def roster_hint(mark: dict) -> str:
    if not mark["kinds"]:
        return "no protection"
    return roster_kinds_line(mark["kinds"], mark["skins"])


# --------------------------------------------------------------------------- #
# The eyeball check
# --------------------------------------------------------------------------- #


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--day", type=int, default=1)
    args = ap.parse_args()
    seed = args.seed if args.seed is not None else 1

    print(f"{len(CATEGORIES)} crime categories "
          f"({sum(1 for c in CATEGORIES if c['shape'] == 'petty')} petty, "
          f"{sum(1 for c in CATEGORIES if c['shape'] == 'deed')} deed, "
          f"{sum(1 for c in CATEGORIES if c['shape'] == 'force')} force)")
    print()
    for kind in ("village", "town", "capital", "wilds"):
        print(f"-- local marks at a {kind} (day {args.day}) --")
        for cat in CATEGORIES:
            mark = roll_mark(cat, seed, f"demo-{kind}", kind, args.day)
            if mark is None:
                continue
            print(f"  {cat['name']} [{cat['shape']}]: {mark['role']} "
                  f"(L{mark['level']}) -- {mark['gold']}g, "
                  f"{mark['xp']} XP/sin; {check_line(cat)}")
            print(f"      protection: {roster_hint(mark)}")
        print()


if __name__ == "__main__":
    main()
