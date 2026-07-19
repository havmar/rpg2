"""Karma & heat + the hell pact -- the villain layer (2026-07-19).

The design (rules.md, the Karma & Heat add-on, has the full spine): the
game learns to be PLAYED WICKEDLY without forking into a second ruleset.
XP is bucketed by the ALIGNMENT of the work that paid it -- dark work
accrues BAD KARMA, honest work burns it 1:1 (penance) -- and the party's
current bad karma sets its HEAT: how many levels above the party the
world's retribution arrives. Zero heat is the old game exactly; the whole
layer is inert until the player takes dark work.

THE HELL PACT (2026-07-19, second slice -- the dark-quests session): the
PC is not a neutral adventurer but a LOW-RANKING EMPLOYEE OF HELL, a
mortal of an ordinary race bound by a pact with an evil god -- wealth
and power promised in exchange for obedience in tasks that fray the
orderly fabric of the universe (hell's long game: gates and summonings).
Mechanically:

- **Assignments.** Hell assigns Dark Tasks on its own clock (a fresh one
  ~TASK_INTERVAL_DAYS after the last resolved), leveled AT the party
  with the margin of error running UPWARD (spread 0..+2). They arrive by
  job boards unseen to ordinary men, black-waxed letters, ember-eyed
  couriers (HELL_MAIL). An assignment is an ordinary dark quest flagged
  `hell_task` -- take it, fight it, turn it in.
- **Chickening Out.** An assignment may be IGNORED for TASK_GRACE_DAYS;
  past that, infernal colleagues come to punish the disobedience
  (build_hell_posse -- the lawful posses' mirror, at party level +1,
  escalating with each beating survived). Beating them changes nothing:
  the job still stands. LOSING to them is hell's lesson (the mercy in
  session.py): the purse taken as a fine, the refused job withdrawn.
- **Bribes.** Hell can be bribed to ease off for a while (`bribe`:
  BRIBE_GOLD_PER_LEVEL x party level buys BRIBE_DAYS of no assignments
  and no enforcement).
- **The caper structure.** Dark templates may carry a `deed` (a skill
  check that can do the job CLEAN -- or botch it into the fight, with
  witnesses: DEED_FAIL_KARMA) and a `twist` (an authored complication
  with priced terms -- the fence's half-price offer; `settle` takes it,
  fighting on refuses it). The machinery lives in quests.build_quest
  and session.py; the templates below author the content.
- **Left for dead.** The PC is never killed by the law's heroes or
  hell's enforcers -- a lost posse fight costs the party, the purse,
  and (against the law) all bad karma instead (session.apply_mercy).

- **Heat is the throttle.** One at-level dark quest is ~one heat step
  (KARMA_HEAT_STEP * level bad karma per step; a level-L quest quotes
  ~100L XP). The player pumps difficulty by sinning and bleeds it off by
  honest work -- difficulty selection by consequence, not by board-reading.
- **Punishment is people, not weather.** At heat >= 1, time-spaced posses
  (cooldown + a chance roll at arrivals and nights) hunt the party at
  party level + heat: the Watch first, then bounty hunters, the crown's
  huntsmen, finally heroes of the realm -- all budget-honest ladder
  rosters wearing lawful display names, led by a generated face. Cutting
  them down pays XP like any road fight, and ALL of it is bad karma: the
  ratchet is the point.
- **Dark quests are the same machinery flagged.** Templates below ride
  build_quest/attach_giver unchanged; they are rolled LAZILY per
  settlement day (`board --dark`, the recruits-on-request pattern), so
  worldgen, the coverage assert, and every bench never see them. Crime
  pays a gold premium (quests.DARK_GOLD_MULT); its XP is the liability.
- **The fights stay honest.** A dark quest's foes are always people/things
  that fight back (guards, militia, an aggrieved parent dire wolf); the
  wickedness itself -- the theft, the arson, the kicked puppy -- is
  narration (dm.md owns the register: cartoonish, never grim).

The sims never import this file. State is one plain dict in the save
(`karma`): current bad karma, the lifetime ledgers, the punishment day
stamp, and the last posse leader's name (the future nemesis seed).

Run:  python karma.py [--seed N]   # sample dark boards and posses
"""

from __future__ import annotations

import argparse
import random

from rpg import LEVEL_CAP
from quests import (LADDER_POOL, WOLF_POOL, UNDEAD_POOL, CASTER_POOL,
                    BEAST_POOL, GIANTKIN_POOL,
                    build_quest, attach_giver, template_band, build_room,
                    room_budget)

# --------------------------------------------------------------------------- #
# Constants (the villain layer's knobs)
# --------------------------------------------------------------------------- #

KARMA_HEAT_STEP = 100   # bad karma per heat step is this * the PC's level:
                        # a level-L quest quotes ~100L XP (site_xp_total),
                        # so ONE at-level dark quest ~ one heat step, and
                        # one honest at-level quest ~ one step of penance
HEAT_CAP = 3            # posses arrive at party level + heat, capped: +3
                        # is already a truly dangerous fight (the punching-
                        # up measurements); past it the number is noise
PUNISH_COOLDOWN_DAYS = 2   # the law is never instantaneous: at least this
                           # many days between posses ("a bit time spaced")
PUNISH_CHANCE = 0.6     # per eligible stop (arrival / settlement night /
                        # wilds camp) once the cooldown has passed
DARK_JOBS_PER_DAY = 3   # the shadow board's size, rolled per settlement day

# The hell pact's knobs (2026-07-19, second slice). ALL hand-set and
# sim-unverified BY DIRECTIVE: the designer abandoned XP/gold balance for
# the dark layer this session -- quest VARIETY first, the table tunes
# numbers later (develop.md, Balance / tuning).
TASK_INTERVAL_DAYS = 4  # a fresh assignment ~this long after the last one
                        # resolved (done, withdrawn, or bribed away)
TASK_GRACE_DAYS = 4     # an assignment may be ignored this long; past it,
                        # Chickening Out -- hell's enforcers come calling
ENFORCE_COOLDOWN_DAYS = 2   # hell's patience between beatings (mirrors
ENFORCE_CHANCE = 0.6        # the law's cooldown + chance shape)
BRIBE_GOLD_PER_LEVEL = 30   # `bribe`: this x party level buys...
BRIBE_DAYS = 10             # ...this many days of no assignments and no
                            # enforcement (the task clock restarts after)
DEED_FAIL_KARMA = 15    # witnesses are hard to avoid: a BOTCHED deed is
                        # talked about -- flat bad karma on top of the fight

# How WORD FROM BELOW arrives (rolled flavor for the assignment scene).
HELL_MAIL = (
    "a job board stands where a bare wall stood yesterday -- unseen by "
    "ordinary folk, searched for by paladins",
    "a letter arrives, sealed in black wax that is faintly warm and "
    "will not cool",
    "a courier finds the party: a polite urchin whose eyes catch the "
    "light like embers",
    "the taproom smoke curls into words meant for one reader only",
)

# --------------------------------------------------------------------------- #
# Karma state (one plain dict in the save)
# --------------------------------------------------------------------------- #


def new_karma() -> dict:
    return {"bad": 0,           # current, burnable -- drives heat
            "bad_total": 0,     # lifetime wickedness (never decreases --
                                # the player's badness level, for titles
                                # and the DM's memory)
            "good_total": 0,    # lifetime penance (record only)
            "last_punish_day": -99,
            "last_leader": None}   # the last posse's named leader -- the
                                   # nemesis seed (persistence is plan.md)


def new_pact() -> dict:
    """The hell pact's state (one plain dict in the save, `pact`). Rides
    every new game by default (`new --no-pact` is the neutral-adventurer
    switch): the PC is hell's employee from scene one."""
    return {"task": None,           # the current assignment's quest id
            "assigned_day": 0,      # when it landed (grace runs from here)
            "last_task_day": -99,   # when the last one resolved -- the
                                    # interval clock (fresh pact: hell's
                                    # first letter comes early)
            "bribed_until": 0,      # no assignments/enforcement before this
            "last_enforce_day": -99,
            "beatings": 0,          # enforcer visits survived over the
                                    # CURRENT refusal (escalates them)
            "done": 0}              # lifetime assignments completed (the
                                    # curriculum ledger -- titles later)


def heat(karma: dict, pc_level: int) -> int:
    """Current heat: how many levels above the party retribution arrives.
    Derived, never stored -- bad karma over KARMA_HEAT_STEP * level, so
    the same sins cool as the party's legend grows (the Watch that hunts
    a level-2 puppy-kicker has better sense at level 10)."""
    step = KARMA_HEAT_STEP * max(1, pc_level)
    return min(HEAT_CAP, karma["bad"] // step)


def record_karma(karma: dict, xp: int, align: str, log: list,
                 pc_level: int) -> None:
    """Bucket a QUOTED XP award by the work's alignment: dark work accrues
    bad karma, good work burns it 1:1 (penance -- 'the basic quests delete
    the karma'). Neutral work (the wilds, the hunt) touches nothing.
    Appends the bookkeeping line so the player always sees the meter."""
    if align == "dark" and xp > 0:
        karma["bad"] += xp
        karma["bad_total"] += xp
        log.append(f"    (dark work: +{xp} bad karma -- "
                   f"{karma_line(karma, pc_level)})")
    elif align == "good" and xp > 0:
        karma["good_total"] += xp
        if karma["bad"] > 0:
            burned = min(karma["bad"], xp)
            karma["bad"] -= burned
            log.append(f"    (penance: -{burned} bad karma -- "
                       f"{karma_line(karma, pc_level)})")


def karma_line(karma: dict, pc_level: int) -> str:
    """The one-line meter for tallies and status readouts -- always
    self-contained (current bad karma + what it means)."""
    h = heat(karma, pc_level)
    step = KARMA_HEAT_STEP * max(1, pc_level)
    if h >= 1:
        return (f"bad karma {karma['bad']}; HEAT {h} -- retribution "
                f"hunts {h} level(s) above the party")
    if karma["bad"] > 0:
        return (f"bad karma {karma['bad']}/{step}; heat 0 -- lying low")
    return "clean; heat 0"


# --------------------------------------------------------------------------- #
# Dark quest templates
# --------------------------------------------------------------------------- #
# Race-agnostic on purpose (dark work is cosmopolitan; race-flavored dark
# tables are a later content pass -- plan.md). Same schema as
# quests.TEMPLATES plus `align: "dark"`; the foes are always someone who
# FIGHTS BACK -- guards, militia, the relic's keepers, the puppy's parent
# -- so the engine only ever resolves honest fights and the wickedness
# itself stays narration (dm.md, the villain register).
#
# THE CAPER SCHEMA (2026-07-19, the dark-quests session) -- two optional
# fields formalize the more-complex quest structure:
#   deed  = dict(stat="dex|str|mind|cha", dc=N, text=..., fail=...)
#           -- attached to the quest's FIRST site: before its first fight,
#           the PC rolls 2d6 + stat vs dc. A make does the site CLEAN
#           (site closed, full lump, no fight); a miss botches it into
#           the fight, with witnesses (+DEED_FAIL_KARMA bad karma). DCs
#           sit high on purpose: "the dex check will probably fail, and
#           lead to a fight" is the design sentence.
#   twist = dict(text=..., accept=..., pay=0.5)
#           -- attached to the LAST site: arriving there prints the
#           authored complication and its priced terms. `settle` takes
#           them (site closed at pay x lump); fighting on refuses them.
# A template carrying either pins its site count (capers are authored
# shapes, not rolled). Machinery: quests.build_quest + session.cmd_room /
# cmd_settle; rules.md's Karma & Heat add-on documents the math.

DARK_TEMPLATES: list[dict] = [
    dict(title="The Puppy on the Doorstep", align="dark",
         desc="A widow's guard-pup keeps fouling the fixer's doorstep. "
              "Kick it down the lane, says the fixer. The pup, it turns "
              "out, has family.",
         pool=WOLF_POOL,
         skins={"wolf": "Very Big Dog", "dire wolf": "the Pup's Mother"},
         sites=("the back lane", "the kennel yard"),
         giver="the fixer",
         epilogue="The pup limps home. Somewhere a tavern bard is already "
                  "singing about the brutes who kicked it, with gestures."),
    dict(title="The Protection Round", align="dark",
         desc="Three streets of shopkeepers pooled their coin and hired "
              "steel instead of paying up. The racket wants the lesson "
              "delivered anyway.",
         pool=LADDER_POOL,
         skins={"cutthroat": "Hired Knife", "archer": "Rooftop Lookout",
                "bruiser": "Shop-Door Tough", "soldier": "Hired Guard",
                "veteran": "Guard Sergeant", "champion": "the Streets' "
                "Champion"},
         sites=("the market row", "the counting room"),
         giver="the racket's collector",
         epilogue="The shutters go up meekly on rent day. The shopkeepers "
                  "smile at the party in the street, carefully, with "
                  "every tooth."),
    dict(title="Burn the Granary", align="dark",
         desc="The miller's rival pays for a fire and no witnesses. The "
              "miller, regrettably, pays for guards and dogs.",
         pool=("wolf",) + LADDER_POOL[:4],
         skins={"wolf": "Miller's Mastiff", "cutthroat": "Night Watchman",
                "archer": "Granary Archer", "bruiser": "Miller's Man",
                "soldier": "Hired Guard"},
         sites=("the mill yard", "the granary floor"),
         giver="the rival in silk",
         epilogue="Grain prices double by market day. The rival in silk "
                  "is very sorry to hear it, publicly, at length."),
    dict(title="The Reliquary Job", align="dark",
         desc="A collector wants the temple's golden relic, feels the "
              "temple has had its turn. The keepers keep it with steel "
              "and scripture.",
         pool=LADDER_POOL[:6] + CASTER_POOL,
         skins={"cutthroat": "Temple Novice", "archer": "Roof Warden",
                "bruiser": "Lay Brother", "soldier": "Temple Guard",
                "veteran": "Warden of the Shrine",
                "champion": "the Faith's Sworn Blade",
                "hexer": "Curse-Chanter", "pyromancer": "Censer-Burner"},
         sites=("the temple court", "the reliquary vault"),
         giver="the veiled collector",
         epilogue="The empty plinth draws bigger crowds than the relic "
                  "ever did. The priests declare a miracle of absence "
                  "and double the alms box takings."),
    dict(title="The Debt Collection", align="dark",
         desc="A whole village signed, sealed, and stopped paying. The "
              "moneylender pays a fifth of the book to whoever squeezes "
              "it out of them -- and the village has raised a militia.",
         pool=LADDER_POOL[:5],
         skins={"cutthroat": "Village Rough", "archer": "Poacher-Turned-"
                "Sentry", "bruiser": "the Blacksmith", "soldier":
                "Militiaman", "veteran": "the Old Campaigner"},
         sites=("the barricaded bridge", "the village square"),
         giver="the moneylender's broker",
         epilogue="The village pays to the copper, then names its new "
                  "well after the party. The bucket, specifically."),
    dict(title="Grave Goods", align="dark",
         desc="The old barrow is consecrated ground and the parish is "
              "touchy about it. The broker is not: the dead wear gold "
              "down there, and gold belongs to the living.",
         pool=UNDEAD_POOL,
         skins={},
         sites=("the broken seal", "the gold-hung galleries"),
         giver="the grave-broker",
         epilogue="The parish re-consecrates the barrow at great expense. "
                  "The broker weighs the grave-gold twice and asks, "
                  "brightly, about the OTHER barrow."),
    dict(title="Toll the King's Road", align="dark",
         desc="Why rob a road when you can OWN one? Set up the chain, "
              "post the rates -- and hold the crossing when the garrison "
              "comes to take it down.",
         pool=LADDER_POOL,
         skins={"cutthroat": "Garrison Scout", "archer": "Garrison "
                "Crossbowman", "bruiser": "Garrison Mauler",
                "soldier": "Garrison Regular", "veteran": "Garrison "
                "Sergeant", "champion": "the Garrison Captain",
                "blademaster": "the Crown's Duelist",
                "warlord": "the Lord Marshal"},
         sites=("the toll chain", "the fordside camp", "the held crossing"),
         giver="the ambitious lieutenant",
         epilogue="For one glorious week the road pays the party, not "
                  "the crown. Clerks in three counting-houses develop "
                  "nervous conditions."),
    # --- the 2026-07-19 dark-quests content pass (the curriculum) --- #
    dict(title="The Five-Finger Discount", align="dark",
         desc="A collector wants one small, priceless thing lifted from "
              "a merchant's strongroom. Then there is the fence, who has "
              "opinions about prices.",
         pool=LADDER_POOL[:4],
         skins={"cutthroat": "Shop Guard", "archer": "Rooftop Watchman",
                "bruiser": "Strongroom Tough", "soldier": "Hired Guard"},
         sites=("the merchant's strongroom", "the fence's cellar"),
         deed=dict(stat="dex", dc=11, text="the lift -- in through the "
                   "coal chute, out with the goods, touching nothing",
                   fail="a shelf goes over; the whole house wakes"),
         twist=dict(text="The fence turns the piece over once and offers "
                    "HALF its price -- 'damaged in transit, see' -- and "
                    "his bodyguards lean off the wall in unison.",
                    accept="Half is half. The fence smiles like a purse "
                    "closing.", pay=0.5),
         giver="the veiled collector",
         epilogue="The piece surfaces in a private gallery three lands "
                  "away. The merchant posts a reward; the Watch posts "
                  "a description; neither is close."),
    dict(title="The Menagerie Order", align="dark",
         desc="Hell wants a rare beast, caged and delivered breathing. "
              "The catching is one job; the part where it slips the cage "
              "at the town gates is another.",
         pool=BEAST_POOL + ("dire wolf",), skins={},
         sites=("the trapping ground", "the beast loose at the gates"),
         giver="the fixer",
         epilogue="The crate goes down the hellmouth stairs, growling. "
                  "A receipt comes back up, signed in something brown."),
    dict(title="Dine and Dash", align="dark",
         desc="Take the best table, order everything, compliment the "
              "cellar -- then rob the owner to settle the bill. The "
              "house employs discreet, well-fed muscle.",
         pool=LADDER_POOL[:4],
         skins={"cutthroat": "Coat-Check Knife", "archer": "Balcony "
                "Lookout", "bruiser": "the Door's Opinion",
                "soldier": "House Guard"},
         sites=("the proprietor's back office",),
         deed=dict(stat="cha", dc=10, text="the long con -- twelve "
                   "courses of charm, ending alone with the host and "
                   "the strongbox", fail="the sommelier remembers your "
                   "face from a poster"),
         giver="the rival in silk",
         epilogue="The review, dictated to a terrified waiter on the "
                  "way out: five stars, would rob again."),
    dict(title="The Last Sermon", align="dark",
         desc="Hell wants the local priest on the altar he preaches "
              "from. He is, for the record, a bad man -- a usurer in "
              "vestments who has ruined more families than any bandit. "
              "Will you still chicken out?",
         pool=LADDER_POOL[:5] + CASTER_POOL,
         skins={"cutthroat": "Outraged Sexton", "archer": "Bell-Tower "
                "Warden", "bruiser": "Lay Brother", "soldier": "Temple "
                "Guard", "veteran": "the Old Crusader",
                "hexer": "the Curate", "pyromancer": "the Censer-Swinger"},
         sites=("the vestry", "the altar steps"),
         giver="the fixer",
         epilogue="The parish, freed of its usurer, is oddly quiet about "
                  "the how. The ledger of debts burns in the vestry "
                  "grate, and nobody claims to have lit it."),
    dict(title="A Most Heinous Act", align="dark",
         desc="Hell requires one act no healthy mind would contemplate: "
              "a puppy, an altar, a knife. It is a direwolf pup, and its "
              "parents can smell the altar from two valleys off.",
         pool=WOLF_POOL,
         skins={"wolf": "Direwolf Kin", "dire wolf": "the Pup's "
                "Mother"},
         sites=("the shrine in the woods",),
         giver="the grave-broker",
         epilogue="Cooked afterwards, as the rite requires, and -- this "
                  "is the worst part -- it tastes genuinely good. "
                  "Somewhere below, applause. Somewhere above, a bard "
                  "starts a very long song."),
    dict(title="Sack the Village", align="dark",
         desc="A whole village, one night, everything in it: all their "
              "gold is yours. They have a palisade, a militia, and "
              "strong opinions about visitors with torches.",
         pool=LADDER_POOL[:5],
         skins={"cutthroat": "Village Rough", "archer": "Palisade "
                "Bowman", "bruiser": "the Blacksmith", "soldier":
                "Militiaman", "veteran": "the Old Campaigner"},
         sites=("the palisade gate", "the high street", "the moot hall"),
         giver="the ambitious lieutenant",
         epilogue="The village will rebuild, the ballads insist. The "
                  "ballads are mostly about what the party took, listed, "
                  "with amounts."),
    dict(title="The Vault Job", align="dark",
         desc="The counting-house vault holds three lands' worth of "
              "deposits. The plan is elegant. The guards are not part "
              "of the plan.",
         pool=LADDER_POOL[:6],
         skins={"cutthroat": "Night Clerk", "archer": "Gallery Guard",
                "bruiser": "Vault-Door Muscle", "soldier": "House "
                "Guard", "veteran": "Guard Sergeant",
                "champion": "the Guild's Duelist"},
         sites=("the counting floor", "the vault below"),
         deed=dict(stat="mind", dc=11, text="the plan -- cased for a "
                   "week, timed to the minute, in through the lamplit "
                   "gallery between rounds", fail="the rounds changed "
                   "this morning; the plan meets the guards"),
         giver="the moneylender's broker",
         epilogue="Three counting-houses fail by month's end and the "
                  "broker, who sold their debts short, sends a fruit "
                  "basket. It is not poisoned. Probably."),
    dict(title="A Round on the House", align="dark",
         desc="Season the feast-day cask, then stand everyone a round "
              "and watch the hall fold. The philter is gut-rot, not "
              "grave-dirt -- hell wants the humiliation, and whoever "
              "did not drink wants you.",
         pool=LADDER_POOL[:4],
         skins={"cutthroat": "Furious Potboy", "archer": "the Innkeep's "
                "Nephew", "bruiser": "the Town Wrestler",
                "soldier": "Feast-Day Guard"},
         sites=("the reeling feast-hall",),
         deed=dict(stat="mind", dc=10, text="the philter, slipped into "
                   "the cask between toasts", fail="a potboy sees the "
                   "vial go in and screams the house down"),
         giver="the fixer",
         epilogue="Nobody dies; everybody remembers. The feast day is "
                  "renamed for the disaster, which hell counts as a "
                  "monument."),
    dict(title="The Inheritance", align="dark",
         desc="A fine mansion, elderly owners, no heirs anyone will "
              "press about. Murder them and it's yours. They were bad "
              "people. Probably. The household guard is definitely "
              "well paid.",
         pool=LADDER_POOL[:6],
         skins={"cutthroat": "Under-Butler", "archer": "Gatehouse "
                "Archer", "bruiser": "the Groundskeeper", "soldier":
                "House Guard", "veteran": "the Majordomo",
                "champion": "the Old Master-at-Arms"},
         sites=("the garden wall", "the master's study"),
         giver="the veiled collector",
         epilogue="The deed reads cleanly enough, if nobody holds it to "
                  "the light. The staff stay on; the pay is better and "
                  "they ask no questions at all."),
    dict(title="The Blade That Thirsts", align="dark",
         desc="A famous evil weapon lies in the barrow of the last fool "
              "who wielded it. Hell would like it back in circulation. "
              "The barrow disagrees.",
         pool=UNDEAD_POOL, skins={},
         sites=("the sealed tomb", "the wielder's rest"),
         giver="the grave-broker",
         epilogue="The blade comes up humming, faintly, in a key that "
                  "makes dogs leave the room. It is very pleased to "
                  "meet you. (The DM places the actual weapon -- a "
                  "reskinned quality blade until named instances land.)"),
    dict(title="The Unmaking", align="dark",
         desc="A sacred sword hangs above a shrine's altar, famous for "
              "three miracles. Corrupt it by dark ritual where it "
              "hangs. The faithful will object, in ranks.",
         pool=LADDER_POOL[:6] + CASTER_POOL,
         skins={"cutthroat": "Shrine Novice", "archer": "Pilgrim "
                "Warden", "bruiser": "Lay Brother", "soldier": "Temple "
                "Guard", "veteran": "Warden of the Shrine",
                "champion": "the Faith's Sworn Blade",
                "hexer": "the Anchorite", "pyromancer": "Censer-Burner"},
         sites=("the pilgrim road", "the reliquary shrine"),
         giver="the veiled collector",
         epilogue="The blade still hangs there. It looks the same. The "
                  "miracles stop, and the pilgrims' road grows quietly "
                  "over with grass."),
    dict(title="Blood on the Altar", align="dark",
         desc="Desecrate the altar with blood before the dawn bell. "
              "Whose blood is not specified -- your own works, if you "
              "are a coward. Hell will know.",
         pool=LADDER_POOL[:5],
         skins={"cutthroat": "Outraged Sexton", "archer": "Bell-Tower "
                "Warden", "bruiser": "Lay Brother", "soldier": "Temple "
                "Guard", "veteran": "the Old Crusader"},
         sites=("the midnight chapel",),
         giver="the grave-broker",
         epilogue="The altar is scrubbed, re-blessed, and roped off. "
                  "Attendance, perversely, has never been better."),
    dict(title="An Old Friend", align="dark",
         desc="A hellish coworker has been skimming. Work with the "
              "authorities: testify, then help take their crew. It is "
              "an old friend. They once saved your life. Hell calls "
              "this a loyalty exercise, and means yours.",
         pool=LADDER_POOL[:6],
         skins={"cutthroat": "Old Friend's Knife", "archer": "Crew "
                "Lookout", "bruiser": "Crew Muscle", "soldier": "Sworn "
                "Crewman", "veteran": "the Lieutenant",
                "champion": "the Old Friend"},
         sites=("the safehouse door", "the last back room"),
         giver="the ambitious lieutenant",
         epilogue="The Watch captain shakes your hand in public, which "
                  "does your reputation no good anywhere. The old "
                  "friend's chair at the fixer's table stays empty; "
                  "nobody sits in it."),
    dict(title="The Shepherds", align="dark",
         desc="A cabal of cultists is inviting something old and "
              "nameless through, and heroic adventurers have come to "
              "stop them. Hold the cordon: the cultists must not be "
              "interrupted. The heroes are exactly as good as the "
              "songs say.",
         pool=LADDER_POOL,
         skins={"cutthroat": "Hero's Scout", "archer": "Far-Famed "
                "Archer", "bruiser": "the Strong Companion",
                "soldier": "Sworn Companion", "veteran": "Errant Hero",
                "champion": "Famous Hero",
                "blademaster": "Legendary Swordmaster",
                "warlord": "the Realm's Chosen"},
         sites=("the cordon of campfires", "the standing stones"),
         giver="the veiled collector",
         epilogue="The chanting reaches its end and something arrives. "
                  "The cultists look delighted, then thoughtful, then "
                  "very briefly alarmed. Hell rates the outcome "
                  "'acceptable'."),
    dict(title="The Doorman's Surprise", align="dark",
         desc="Open a hellgate by dark ritual at the appointed place. "
              "One administrative wrinkle: the invading forces were "
              "never told you are one of them.",
         pool=GIANTKIN_POOL + CASTER_POOL,
         skins={"ogre": "Pit Bruiser", "troll": "Flesh-Render",
                "giant": "a Duke's Champion", "hexer": "Frost-Fiend",
                "pyromancer": "Flame-Fiend"},
         sites=("the ritual ground", "the open gate"),
         giver="the grave-broker",
         epilogue="The gate is closed by the time the paperwork "
                  "arrives, stamped IN ERROR. Hell apologizes for the "
                  "inconvenience in writing, which the fixer says has "
                  "never happened before."),
    dict(title="The Powder Trade", align="dark",
         desc="Seed a network selling a terrible, moreish powder -- "
              "hell provides the recipe. The town's standing criminals "
              "regard the market as spoken for.",
         pool=LADDER_POOL[:6],
         skins={"cutthroat": "Corner Knife", "archer": "Rooftop "
                "Spotter", "bruiser": "Rival Muscle", "soldier": "Sworn "
                "Legbreaker", "veteran": "the Underboss",
                "champion": "the Kingpin"},
         sites=("the night market", "the rival den"),
         twist=dict(text="The kingpin's envoy proposes a PARTNERSHIP "
                    "instead: half the take, no blood, his people run "
                    "the corners.", accept="Half the take, none of the "
                    "work. The envoy's handshake counts your rings.",
                    pay=0.5),
         giver="the fixer",
         epilogue="The powder sells itself; that is the terrible part. "
                  "The standing enterprise -- routes, rivals, the "
                  "slow rot -- is a later layer (plan.md); for now the "
                  "seed money is yours."),
    dict(title="The Neighbor Dispute", align="dark",
         desc="A scheming nobleman wants his neighbor's estates. The "
              "neighbor is a good, honorable man, which is why he has "
              "no idea what is about to happen to him.",
         pool=LADDER_POOL[:6],
         skins={"cutthroat": "Estate Poacher-Turned-Guard", "archer":
                "Gatehouse Archer", "bruiser": "the Good Man's "
                "Huntsman", "soldier": "Liveried Guard", "veteran":
                "the Old Steward", "champion": "the Good Man Himself"},
         sites=("the disputed orchard", "the honorable house"),
         giver="the rival in silk",
         epilogue="The papers are signed at sword-point and notarized "
                  "at a distance. The nobleman throws a garden party "
                  "in the orchard within the month; the fruit, "
                  "everyone agrees, tastes of nothing at all."),
]


def roll_dark_quest(world: dict, settlement: dict, pc_level: int,
                    rng: random.Random,
                    used_names: set[str] | None = None,
                    spread: tuple[int, int] = (-1, 2)) -> dict:
    """One shadow job: leveled AT the party (-1..+2 -- the fixer offers
    what the taker can handle; the public board's OSR stance is about the
    honest world), built by build_quest unchanged, flagged dark, given a
    shady face. Registered in world['quests'] (so show/take work) but on
    NO settlement board -- the shadow board lists it (session.py).
    `spread` is the level roll around the party: hell's ASSIGNMENTS pass
    (0, 2) -- suited to the taker, the margin of error running upward."""
    level = max(1, min(LEVEL_CAP, pc_level + rng.randint(*spread)))
    fitting = [t for t in DARK_TEMPLATES
               if template_band(t)[0] <= level <= template_band(t)[1]]
    tpl = rng.choice(fitting or DARK_TEMPLATES)
    lo, hi = template_band(tpl)
    level = max(lo, min(hi, level))
    # First free id: stale shadow jobs are PRUNED from world['quests']
    # (session.py rolls a fresh board per settlement day), so the count
    # alone can collide with a surviving taken job's id.
    n = len(world["quests"]) + 1
    while f"q{n:02d}" in world["quests"]:
        n += 1
    qid = f"q{n:02d}"
    quest = build_quest(qid, tpl, settlement["key"], level, rng)
    attach_giver(quest, settlement["race"], rng, role=tpl.get("giver"),
                 used_names=used_names)
    world["quests"][qid] = quest
    return quest


# --------------------------------------------------------------------------- #
# Punishment (the posses)
# --------------------------------------------------------------------------- #
# Budget-honest ladder rosters (the same threat math as any wild
# encounter) wearing LAWFUL display names by band, led by a generated
# face. The bands escalate with the posse's level, not with time: the
# Watch chases petty villains; heroes of the realm chase warlords.

POSSE_BANDS = (
    # (min posse level, band label, leader role, skins over LADDER_POOL)
    (14, "heroes of the realm", "famous hero",
     {"cutthroat": "Hero's Scout", "archer": "Far-Famed Archer",
      "bruiser": "the Strong Companion", "soldier": "Sworn Companion",
      "veteran": "Errant Hero", "champion": "Famous Hero",
      "blademaster": "Legendary Swordmaster",
      "warlord": "the Realm's Chosen"}),
    (9, "the crown's huntsmen", "knight-captain of the hunt",
     {"cutthroat": "Crown Informer", "archer": "Royal Tracker",
      "bruiser": "the King's Mauler", "soldier": "King's Huntsman",
      "veteran": "Knight-Errant", "champion": "Knight-Captain",
      "blademaster": "the Crown's Blade", "warlord": "the Lord Marshal"}),
    (4, "the bounty guild", "bounty captain",
     {"cutthroat": "Bounty Knife", "archer": "Bounty Archer",
      "bruiser": "Man-Catcher", "soldier": "Bounty Hunter",
      "veteran": "Seasoned Man-Hunter", "champion": "the Guild's Best",
      "blademaster": "the Guild's Legend"}),
    (0, "the Watch", "sergeant of the Watch",
     {"cutthroat": "Watch Runner", "archer": "Watch Bowman",
      "bruiser": "Watch Bruiser", "soldier": "Watchman",
      "veteran": "Watch Sergeant", "champion": "Watch Captain"}),
)


def posse_band(level: int) -> tuple[str, str, dict]:
    for floor, label, role, skins in POSSE_BANDS:
        if level >= floor:
            return label, role, skins
    return POSSE_BANDS[-1][1:]      # unreachable; keeps the checker honest


def build_posse(level: int, race: str, rng: random.Random,
                used_names: set[str] | None = None
                ) -> tuple[list[str], dict, dict, str]:
    """One punishment encounter at `level`: (kinds, skins, leader npc,
    band label). A full reference-encounter budget off the plain ladder
    -- exactly a wild encounter's weight, wearing the law's names. The
    leader is a generated face (people.make_npc) for the strongest slot
    and the DM's scene; their name is the nemesis seed."""
    from people import make_npc     # runtime import (people imports quests)
    label, role, skins = posse_band(level)
    kinds = build_room(room_budget(level, 1.0), LADDER_POOL, rng,
                       final=True)
    leader = make_npc(rng, race, role, level=level, used_names=used_names)
    return kinds, skins, leader, label


# --------------------------------------------------------------------------- #
# Hell's enforcers (Chickening Out -- the hell pact, 2026-07-19)
# --------------------------------------------------------------------------- #
# The lawful posses' mirror: budget-honest ladder rosters wearing INFERNAL
# display names ("demons love bullying" -- and disobedient employees most
# of all), led by a generated face in a borrowed body. One band for now
# (hell's org chart is a later content pass); the escalation is the LEVEL
# (party + 1, +1 per beating survived, capped at +3 over).

HELL_SKINS = {
    "cutthroat": "Spite-Imp", "archer": "Barb-Flinger",
    "bruiser": "Pit Bully", "soldier": "Chain-Devil",
    "veteran": "Collections Fiend", "champion": "the Under-Manager",
    "blademaster": "the Auditor of Souls", "warlord": "a Duke of Hell",
}
HELL_LEADER_ROLE = "collections agent of Hell (in a borrowed body)"


def build_hell_posse(level: int, race: str, rng: random.Random,
                     used_names: set[str] | None = None
                     ) -> tuple[list[str], dict, dict, str]:
    """One Chickening Out encounter at `level`: (kinds, skins, leader,
    band label) -- build_posse's shape exactly, wearing hell's names."""
    from people import make_npc     # runtime import (people imports quests)
    kinds = build_room(room_budget(level, 1.0), LADDER_POOL, rng,
                       final=True)
    leader = make_npc(rng, race, HELL_LEADER_ROLE, level=level,
                      used_names=used_names)
    return kinds, HELL_SKINS, leader, "hell's enforcers"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    from quests import generate_world, quest_detail_lines
    world = generate_world(rng.randrange(1 << 30))
    s = world["settlements"][0]
    print(f"Sample shadow board at {s['name']} (PC level 3):")
    for _ in range(DARK_JOBS_PER_DAY):
        q = roll_dark_quest(world, s, 3, rng)
        for line in quest_detail_lines(q):
            print(line)
        print()
    print("Sample posses (one per heat band):")
    for lvl in (3, 6, 11, 16):
        kinds, skins, leader, label = build_posse(lvl, s["race"], rng)
        shown = ", ".join(skins.get(k, k) for k in kinds)
        print(f"  L{lvl} ({label}): {shown}")
        print(f"    led by {leader['name']}, {leader['role']}")
    print()
    print("Sample hell enforcers (Chickening Out):")
    for lvl in (4, 9):
        kinds, skins, leader, label = build_hell_posse(lvl, s["race"], rng)
        shown = ", ".join(skins.get(k, k) for k in kinds)
        print(f"  L{lvl} ({label}): {shown}")
        print(f"    led by {leader['name']}, {leader['role']}")


if __name__ == "__main__":
    main()
