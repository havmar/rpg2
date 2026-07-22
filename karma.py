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
  narration (writing.md owns the register: cartoonish material, flat telling,
  never grim).

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
# itself stays narration (writing.md, the shared fiction register).
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
    dict(title="Kick the Puppy", align="dark",
         desc="The fixer wants a widow's puppy driven away from his door. "
              "Kick it into the alley. Its mother is nearby.",
         pool=WOLF_POOL,
         skins={"wolf": "Very Big Dog", "dire wolf": "the Pup's Mother"},
         sites=("the back alley", "the kennel yard"),
         giver="the fixer",
         epilogue="The puppy limps home. The widow tells the town what the "
                  "party did."),
    dict(title="Collect Protection Money", align="dark",
         desc="Shopkeepers on three streets refuse to pay protection money. "
              "They hired guards. Beat them and collect.",
         pool=LADDER_POOL,
         skins={"cutthroat": "Hired Thug", "archer": "Rooftop Lookout",
                "bruiser": "Heavy Guard", "soldier": "Hired Guard",
                "veteran": "Guard Sergeant", "champion": "Street Champion"},
         sites=("the market row", "the main office"),
         giver="the gang collector",
         epilogue="The shopkeepers pay. They now fear the party."),
    dict(title="Burn the Granary", align="dark",
         desc="A rival pays you to burn the miller's granary. Kill the guards "
              "and leave no witnesses.",
         pool=("wolf",) + LADDER_POOL[:4],
         skins={"wolf": "Guard Dog", "cutthroat": "Night Guard",
                "archer": "Granary Archer", "bruiser": "Heavy Guard",
                "soldier": "Hired Guard"},
         sites=("the mill yard", "the granary floor"),
         giver="the wealthy rival",
         epilogue="The granary burns. Food prices double."),
    dict(title="Steal the Temple Relic", align="dark",
         desc="A collector wants the gold relic inside the temple. Fight "
              "through the guards and steal it.",
         pool=LADDER_POOL[:6] + CASTER_POOL,
         skins={"cutthroat": "Temple Acolyte", "archer": "Temple Archer",
                "bruiser": "Temple Brawler", "soldier": "Temple Guard",
                "veteran": "Temple Guard Captain",
                "champion": "Temple Champion",
                "hexer": "Curse Mage", "pyromancer": "Fire Priest"},
         sites=("the temple yard", "the relic vault"),
         giver="the masked collector",
         epilogue="The relic is gone. The priests ask for donations to "
                  "replace it."),
    dict(title="Collect the Debt", align="dark",
         desc="A village stopped paying its debt. The moneylender will give "
              "you a share if you force the village to pay. The villagers "
              "have formed a militia.",
         pool=LADDER_POOL[:5],
         skins={"cutthroat": "Village Thug", "archer": "Village Hunter",
                "bruiser": "Blacksmith", "soldier": "Militiaman",
                "veteran": "Militia Veteran"},
         sites=("the barricaded bridge", "the village square"),
         giver="the moneylender's agent",
         epilogue="The village pays the debt. The moneylender takes the money."),
    dict(title="Rob the Tomb", align="dark",
         desc="A broker wants the gold buried in an old tomb. The tomb is "
              "sacred and full of undead. Take the gold.",
         pool=UNDEAD_POOL,
         skins={},
         sites=("the tomb entrance", "the burial halls"),
         giver="the grave robber",
         epilogue="The tomb is robbed. The priest blesses it again."),
    dict(title="Take Over the Road", align="dark",
         desc="Set up a toll on the king's road. Defeat the soldiers sent to "
              "remove it.",
         pool=LADDER_POOL,
         skins={"cutthroat": "Army Scout", "archer": "Army Crossbowman",
                "bruiser": "Heavy Soldier", "soldier": "Army Soldier",
                "veteran": "Army Sergeant", "champion": "Army Captain",
                "blademaster": "Royal Duelist",
                "warlord": "Army General"},
         sites=("the toll gate", "the roadside camp", "the bridge"),
         giver="the gang lieutenant",
         epilogue="The party controls the road for a week and takes the toll "
                  "money."),
    # --- the 2026-07-19 dark-quests content pass (the curriculum) --- #
    dict(title="Steal the Jewel", align="dark",
         desc="A collector wants a valuable jewel. Steal it from a merchant's "
              "vault, then sell it to the fence.",
         pool=LADDER_POOL[:4],
         skins={"cutthroat": "Store Guard", "archer": "Roof Guard",
                "bruiser": "Vault Guard", "soldier": "Hired Guard"},
         sites=("the merchant's vault", "the fence's cellar"),
         deed=dict(stat="dex", dc=11, text="enter through the coal chute, "
                                           "take the jewel, and leave without "
                                           "touching anything else",
                   fail="a shelf falls and wakes the whole house"),
         twist=dict(text="The fence claims the jewel is damaged and offers "
                         "half the price. His bodyguards wait for your "
                         "answer.",
                    accept="You accept half payment. The fence takes the "
                           "jewel.", pay=0.5),
         giver="the masked collector",
         epilogue="The jewel is sold in another land. The merchant offers a "
                  "reward for the thieves."),
    dict(title="Capture the Beast", align="dark",
         desc="Hell wants a rare beast alive. Trap it and take it to town. It "
              "escapes at the gate.",
         pool=BEAST_POOL + ("dire wolf",), skins={},
         sites=("the wilderness trap", "the town gate"),
         giver="the fixer",
         epilogue="Hell takes the beast. The party receives a signed receipt."),
    dict(title="Dine and Dash", align="dark",
         desc="Eat an expensive meal, then rob the owner to pay the bill. The "
              "owner has guards.",
         pool=LADDER_POOL[:4],
         skins={"cutthroat": "Cloakroom Guard", "archer": "Balcony Guard",
                "bruiser": "Door Guard",
                "soldier": "House Guard"},
         sites=("the owner's office",),
         deed=dict(stat="cha", dc=10,
                   text="charm the owner during dinner and get into the "
                        "office with the safe",
                   fail="the waiter recognizes you from a wanted poster"),
         giver="the wealthy rival",
         epilogue="The party robs the owner and leaves without paying."),
    dict(title="Kill the Priest", align="dark",
         desc="Hell orders you to kill a corrupt priest at his own altar. He "
              "ruined families with illegal loans. His guards will defend "
              "him.",
         pool=LADDER_POOL[:5] + CASTER_POOL,
         skins={"cutthroat": "Angry Guard", "archer": "Tower Archer",
                "bruiser": "Temple Brawler", "soldier": "Temple Guard",
                "veteran": "Old Knight",
                "hexer": "Priest", "pyromancer": "Fire Priest"},
         sites=("the priest's room", "the altar steps"),
         giver="the fixer",
         epilogue="The priest is dead. Someone burns his debt records."),
    dict(title="Sacrifice the Puppy", align="dark",
         desc="Hell orders you to sacrifice a dire wolf puppy at a forest "
              "shrine. Its pack is coming.",
         pool=WOLF_POOL,
         skins={"wolf": "Dire Wolf", "dire wolf": "Mother Dire Wolf"},
         sites=("the shrine in the woods",),
         giver="the fixer",
         epilogue="The puppy is sacrificed and cooked. Hell approves."),
    dict(title="Loot the Village", align="dark",
         desc="Attack a village at night and take its gold. The village has a "
              "wooden wall and a militia.",
         pool=LADDER_POOL[:5],
         skins={"cutthroat": "Village Thug", "archer": "Village Archer",
                "bruiser": "Blacksmith", "soldier": "Militiaman",
                "veteran": "Militia Veteran"},
         sites=("the village gate", "the main street", "the town hall"),
         giver="the gang lieutenant",
         epilogue="The party takes the village's gold. The survivors begin "
                  "rebuilding."),
    dict(title="Rob the Vault", align="dark",
         desc="A bank vault holds gold from three lands. Enter at night and "
              "steal it. The bank has many guards.",
         pool=LADDER_POOL[:6],
         skins={"cutthroat": "Bank Clerk", "archer": "Hall Guard",
                "bruiser": "Vault Guard", "soldier": "House Guard",
                "veteran": "Guard Captain",
                "champion": "Bank Champion"},
         sites=("the bank hall", "the bank vault"),
         deed=dict(stat="mind", dc=11,
                   text="enter the bank between guard patrols according to "
                        "the plan",
                   fail="the guards changed their patrol time"),
         giver="the banker's agent",
         epilogue="The stolen gold ruins three banks. The broker sends a gift."),
    dict(title="Poison the Feast", align="dark",
         desc="Hell wants you to put a sickness potion in the feast drink. "
              "Most guests will get sick. The guards who stay sober will "
              "attack.",
         pool=LADDER_POOL[:4],
         skins={"cutthroat": "Angry Servant",
                "archer": "Innkeeper's Nephew",
                "bruiser": "Town Wrestler",
                "soldier": "Feast Guard"},
         sites=("the feast hall",),
         deed=dict(stat="mind", dc=10,
                   text="pour the potion into the drink while nobody is "
                        "looking",
                   fail="a servant sees the potion and calls the guards"),
         giver="the fixer",
         epilogue="Nobody dies, but the town remembers the ruined feast. Hell "
                  "is satisfied."),
    dict(title="Take the Mansion", align="dark",
         desc="An old couple owns a mansion and has no heirs. Kill them and "
              "claim the house. Their guards will fight.",
         pool=LADDER_POOL[:6],
         skins={"cutthroat": "House Servant", "archer": "Gate Archer",
                "bruiser": "Groundskeeper", "soldier": "House Guard",
                "veteran": "Head Servant",
                "champion": "Old Swordmaster"},
         sites=("the garden gate", "the owner's office"),
         giver="the masked collector",
         epilogue="The owners are dead. The papers name the party as heirs, "
                  "and the staff stays."),
    dict(title="Find the Evil Sword", align="dark",
         desc="An evil sword is buried with its last owner. Enter the tomb "
              "and bring it back to Hell.",
         pool=UNDEAD_POOL, skins={},
         sites=("the sealed tomb", "the burial chamber"),
         giver="the grave robber",
         epilogue="The sword hums when it is found. Dogs avoid it. (The DM "
                  "uses a renamed quality weapon until named weapons are "
                  "added.)"),
    dict(title="Corrupt the Holy Sword", align="dark",
         desc="A holy sword hangs in a temple. Perform a dark ritual on it. "
              "The temple guards will try to stop you.",
         pool=LADDER_POOL[:6] + CASTER_POOL,
         skins={"cutthroat": "Temple Acolyte", "archer": "Temple Archer",
                "bruiser": "Temple Brawler", "soldier": "Temple Guard",
                "veteran": "Temple Guard Captain",
                "champion": "Temple Champion",
                "hexer": "Priest", "pyromancer": "Fire Priest"},
         sites=("the temple road", "the holy shrine"),
         giver="the masked collector",
         epilogue="The sword looks unchanged, but its miracles stop. The "
                  "temple closes."),
    dict(title="Blood on the Altar", align="dark",
         desc="Put blood on the altar before dawn. Any blood will work, "
              "including yours. Hell will know what you choose.",
         pool=LADDER_POOL[:5],
         skins={"cutthroat": "Angry Guard", "archer": "Tower Archer",
                "bruiser": "Temple Brawler", "soldier": "Temple Guard",
                "veteran": "Old Knight"},
         sites=("the midnight chapel",),
         giver="the fixer",
         epilogue="The priests clean and bless the altar. More people come to "
                  "see it."),
    dict(title="Betray an Old Friend", align="dark",
         desc="An old friend has been stealing from Hell. Tell the town guard "
              "where to find them, then help kill their crew. This friend "
              "once saved your life.",
         pool=LADDER_POOL[:6],
         skins={"cutthroat": "Crew Assassin", "archer": "Crew Lookout",
                "bruiser": "Crew Muscle", "soldier": "Crew Guard",
                "veteran": "Crew Lieutenant",
                "champion": "Old Friend"},
         sites=("the safehouse entrance", "the back room"),
         giver="the gang lieutenant",
         epilogue="The guard captain thanks the party in public. The old "
                  "friend is dead."),
    dict(title="Guard the Cultists", align="dark",
         desc="Cultists are summoning a demon. Heroes are coming to stop "
              "them. Hold the ritual site until the summoning is complete.",
         pool=LADDER_POOL,
         skins={"cutthroat": "Hero Scout", "archer": "Hero Archer",
                "bruiser": "Strong Hero",
                "soldier": "Hero Warrior", "veteran": "Veteran Hero",
                "champion": "Famous Hero",
                "blademaster": "Master Swordfighter",
                "warlord": "Chosen Hero"},
         sites=("the outer camp", "the ritual stones"),
         giver="the masked collector",
         epilogue="A demon appears. It attacks the cultists. Hell calls the "
                  "job complete."),
    dict(title="Open the Hellgate", align="dark",
         desc="Open a hellgate at the marked location. The demons on the "
              "other side do not know you work for Hell.",
         pool=GIANTKIN_POOL + CASTER_POOL,
         skins={"ogre": "Demon Brute", "troll": "Demon Troll",
                "giant": "Demon Champion", "hexer": "Ice Demon",
                "pyromancer": "Fire Demon"},
         sites=("the ritual ground", "the open gate"),
         giver="the fixer",
         epilogue="The gate closes. Hell sends a written apology."),
    dict(title="Sell the Powder", align="dark",
         desc="Hell gives you a drug recipe. Build a market in town. The "
              "local gang wants to stop you.",
         pool=LADDER_POOL[:6],
         skins={"cutthroat": "Street Thug", "archer": "Roof Lookout",
                "bruiser": "Gang Brute", "soldier": "Gang Guard",
                "veteran": "Gang Boss",
                "champion": "Gang Leader"},
         sites=("the night market", "the rival den"),
         twist=dict(text="The gang leader offers a deal: half the profit, no "
                         "fighting, and his gang handles the sales.",
                    accept="You accept half the profit. His gang handles the "
                           "sales.",
                    pay=0.5),
         giver="the fixer",
         epilogue="The powder begins to sell. The party receives the first "
                  "payment."),
    dict(title="Take the Neighbor's Land", align="dark",
         desc="A noble wants his neighbor's land. Attack the house and force "
              "the owner to sign it over.",
         pool=LADDER_POOL[:6],
         skins={"cutthroat": "Estate Guard", "archer": "Gate Archer",
                "bruiser": "Huntsman", "soldier": "House Guard",
                "veteran": "Old Guard", "champion": "Landowner"},
         sites=("the outer farm", "the main house"),
         giver="the wealthy rival",
         epilogue="The owner signs. The noble takes the land."),
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
    while (f"q{n:02d}" in world["quests"]
           or f"q{n:02d}/s1" in world["sites"]):
        n += 1
    qid = f"q{n:02d}"
    quest = build_quest(world, qid, tpl, settlement["key"], level, rng)
    attach_giver(quest, settlement["land"], rng, role=tpl.get("giver"),
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
    from quests import generate_world, quest_detail_lines, settlements
    world = generate_world(rng.randrange(1 << 30))
    s = settlements(world)[0]
    print(f"Sample shadow board at {s['name']} (PC level 3):")
    for _ in range(DARK_JOBS_PER_DAY):
        q = roll_dark_quest(world, s, 3, rng)
        for line in quest_detail_lines(world, q):
            print(line)
        print()
    print("Sample posses (one per heat band):")
    for lvl in (3, 6, 11, 16):
        kinds, skins, leader, label = build_posse(lvl, s["land"], rng)
        shown = ", ".join(skins.get(k, k) for k in kinds)
        print(f"  L{lvl} ({label}): {shown}")
        print(f"    led by {leader['name']}, {leader['role']}")
    print()
    print("Sample hell enforcers (Chickening Out):")
    for lvl in (4, 9):
        kinds, skins, leader, label = build_hell_posse(lvl, s["land"], rng)
        shown = ", ".join(skins.get(k, k) for k in kinds)
        print(f"  L{lvl} ({label}): {shown}")
        print(f"    led by {leader['name']}, {leader['role']}")


if __name__ == "__main__":
    main()
