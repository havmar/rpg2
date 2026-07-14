"""The story layer -- the conquest questline (the game's L2-10 authored spine).

The board's local quests are formulaic placeholders; this file is AUTHORED
content: one aggressor race per playthrough starts a war of conquest, and
four waves of it -- pinned at levels 2 / 5 / 8 / 10 -- carry the campaign's
first half. (The apocalypse questline, the L12-20 second spine, waits on
the magic tier -- plan.md.) The design (2026-07-12, designer-vetted):

- **Four aggressor variants**, one rolled per playthrough: ELVES (fascist
  perfection -- beautiful, efficient, magic-fuelled steampunk industry),
  GOBLINS (chaotic evil tech -- robots, bombs, bioweapons, zany
  experiments), HUMANS (the deathless kingdom -- a crown corrupted by an
  evil god; conscription that does not end at death), ORCS (a khagan
  unites the clans -- might is right, war is glorious). Dwarves are never
  the aggressor: the stalwart victim/ally land.
- **Waves are ordinary quests underneath**: same schema, same threat math
  (quests.build_site_rooms), same level-pay formulas. What is authored:
  titles, descriptions, site names, reskins, heralds, epilogues, and the
  named faces -- the conqueror and two lieutenants who cap waves 2/3/4 as
  a DISPLAY NAME over a budget-honest roster (the boss is whatever row the
  threat math put in the last room, wearing the villain's name -- stats
  never fork on a skin, not even for the final boss).
- **Waves gate on the party, not the calendar**: wave N+1 posts when the
  previous wave's quest is DONE and the party has reached the wave level
  (2/5/8/10) -- a messenger scene, day-stamped. Level-gating means the war
  can neither outrun nor lag the party.
- **Wave 3 is scripted loss.** The land falls whether or not the quest is
  cleared -- success buys the evacuation (the epilogue), full quest pay,
  and the lieutenant's head, never the outcome. The fallen land is
  OCCUPIED until the war ends: boards, taverns, recruiting, and downtime
  refuse there (travel through is allowed); wave 4's victory lifts it.
- **Story state lives in the session save** (session.py `story` key);
  the sims never import this file, so no bench number can move from it.

Run:  python story.py [--seed N]   # eyeball dump: one rolled conquest,
                                   # all four waves force-posted
"""
from __future__ import annotations

import argparse
import random

from quests import (LADDER_POOL, WOLF_POOL, UNDEAD_POOL,
                    build_site_rooms, threat_value, attach_giver, lands,
                    quest_line, quest_detail_lines)

# --------------------------------------------------------------------------- #
# The shape (shared by every variant)
# --------------------------------------------------------------------------- #

WAVE_LEVELS = (2, 5, 8, 10)     # the pinned difficulty spine
WAVE_ROOMS = ((2, 2), (2, 2, 3), (2, 3, 3), (2, 3, 3))  # rooms per site
AGGRESSORS = ("elf", "goblin", "human", "orc")

# --------------------------------------------------------------------------- #
# The four conquests
# --------------------------------------------------------------------------- #
# Each variant: banner + creed (the ideology, said once, at wave 1's
# herald), the named faces' titles, one foe pool + reskin table (existing
# calibrated rows only -- v1 adds no stat blocks), and four waves: title,
# desc, herald (the messenger's line), site names, epilogue. {land} /
# {land_cap} = the wave's target land; {conqueror} / {lt1} / {lt2} = the
# named faces ("Karg, the Khagan").

CONQUESTS: dict[str, dict] = {
    "elf": dict(
        banner="the Radiant Ascendancy",
        creed="the elves have decided that perfection obliges: the lesser "
              "peoples are to be governed, improved, and grateful. Their "
              "machines are beautiful, efficient, and already moving.",
        conqueror_title="Radiant Marshal",
        lieutenant_titles=("Artificer-General", "Prefect of the Vanguard"),
        pool=LADDER_POOL + ("ogre", "troll"),
        skins={"cutthroat": "Gilded Blade", "archer": "Aether-Rifleman",
               "bruiser": "Steam Knight", "soldier": "Legion Automaton",
               "veteran": "Vanguard Automaton", "champion": "War-Artificer",
               "blademaster": "Blade-Perfect", "warlord": "Radiant Marshal",
               "ogre": "Colossus Engine", "troll": "Siege Colossus"},
        waves=(
            dict(title="Beautiful Machines at the Border",
                 desc="Surveyors in gilded coats mark farms they do not "
                      "own in the {land} borderlands; the machines that "
                      "follow them do not ask twice.",
                 herald="a mud-splashed rider from the {land} border: "
                        "gilded machines are pacing the frontier, and "
                        "where they stop, fences move.",
                 sites=("the surveyors' camp", "the marked farms"),
                 epilogue="The surveyors withdraw with perfect courtesy, "
                          "leaving pegs, a burned camp, and a promise: "
                          "this was a measurement, not a defeat."),
            dict(title="The Line Must Hold",
                 desc="The Ascendancy has stopped measuring the {land} "
                      "lands and started collecting them. {lt1} builds a "
                      "beachhead foundry; every day it stands, the line "
                      "of beautiful soldiers grows.",
                 herald="the war is open: Ascendancy columns are in the "
                        "{land} lands and a foundry is going up on the "
                        "coast road.",
                 sites=("the shattered watchtower", "the aqueduct works",
                        "the beachhead foundry"),
                 epilogue="The foundry burns for three days in perfect "
                          "silence. The {land} lands hold, and the "
                          "Ascendancy files the loss as an arithmetic "
                          "error to be corrected."),
            dict(title="The Fall of the {land_cap} Lands",
                 desc="{lt2} brings the main works against the {land} "
                      "lands: siege colossi, lens-fire, and no terms. The "
                      "walls will not hold -- what can still be won is "
                      "the road out.",
                 herald="black smoke over the {land} lands: the "
                        "Ascendancy's main works have arrived, and this "
                        "time the numbers say the walls fail.",
                 sites=("the burning outworks", "the last gate",
                        "the evacuation road"),
                 epilogue="The {land} lands fall behind the party -- silk "
                          "banners over machine-cut stone. The road out "
                          "stayed open one day longer than the enemy "
                          "planned, and every cart on it is someone the "
                          "party saved."),
            dict(title="The Radiant Court",
                 desc="{conqueror} holds court in the great works: the "
                      "war's whole beautiful machine, and the one elf it "
                      "cannot run without. Cut the head off.",
                 herald="the allied crowns have found the Radiant "
                        "Marshal's court -- and will pay whoever walks in "
                        "and ends this.",
                 sites=("the lens-field perimeter", "the great works",
                        "the marshal's court"),
                 epilogue="The great works fall silent mid-shift. The "
                          "Ascendancy sues for peace in flawless "
                          "calligraphy; nobody who signs believes them, "
                          "but the armies go home, and the fallen lands "
                          "breathe again."),
        ),
    ),
    "goblin": dict(
        banner="the Thousand Workshops",
        creed="the goblin overbosses have merged into one roaring "
              "concern: why should the world stay as built when it could "
              "be EXPERIMENTED on? Their soldiers are riveted, vat-grown, "
              "or ticking.",
        conqueror_title="Grand Tinkerer",
        lieutenant_titles=("Bomb-Marshal", "Chief Fleshwright"),
        pool=LADDER_POOL + WOLF_POOL + ("ogre", "troll"),
        skins={"wolf": "Vat-Hound", "dire wolf": "Vat-Alpha",
               "cutthroat": "Bomb-Lobber", "archer": "Rivet-Gunner",
               "bruiser": "Scrap-Golem", "soldier": "Tin Legionnaire",
               "veteran": "Tin Sergeant", "champion": "War-Tinker",
               "blademaster": "Buzzblade Duelist", "warlord": "Grand Tinkerer",
               "ogre": "Walking Bomb", "troll": "Flesh-Forge Hulk"},
        waves=(
            dict(title="Strange Salvage",
                 desc="Livestock, fence-iron, and one census-taker have "
                      "gone missing along the {land} border. What the "
                      "trackers found was half animal, half machine, and "
                      "all appetite.",
                 herald="word from the {land} border: something is "
                        "stealing iron and eating witnesses, and it "
                        "ticks.",
                 sites=("the picked-clean farmstead", "the salvage burrow"),
                 epilogue="The burrow is collapsed onto its own bomb "
                          "stores; the crater smokes for a week and the "
                          "livestock stop vanishing."),
            dict(title="The Sky Rains Scrap",
                 desc="The Thousand Workshops have declared the {land} "
                      "lands a 'test range'. {lt1}'s bombing line creeps "
                      "toward the walls while a tunneling engine chews in "
                      "from below.",
                 herald="the {land} lands are under open attack: bombs "
                        "by day, and the ground itself humming by night.",
                 sites=("the crash site", "the bombing line",
                        "the tunneling engine"),
                 epilogue="The tunneling engine dies with a cough that "
                          "registers three lands away. The {land} lands "
                          "hold; scrap-pickers will be rich for a "
                          "generation."),
            dict(title="The Fall of the {land_cap} Lands",
                 desc="{lt2} unveils the war's masterpiece against the "
                      "{land} lands: gas, hulks, and things with too many "
                      "sets of teeth. The walls are already lost -- hold "
                      "the road out instead.",
                 herald="the {land} lands are choking: the Fleshwright's "
                        "host is at the walls and the engineers give the "
                        "gates two days.",
                 sites=("the gas-choked walls", "the breach",
                        "the evacuation road"),
                 epilogue="The {land} lands fall under a sky the color "
                          "of engine oil. The party's rearguard held the "
                          "road while it emptied -- the Workshops got the "
                          "walls, not the people."),
            dict(title="The Grand Workshop",
                 desc="Every wire in the war runs back to {conqueror}'s "
                      "dome. The Workshops cannot agree on anything "
                      "without the Tinkerer -- so make them try.",
                 herald="deserters sell the secret cheap: the Grand "
                        "Tinkerer's dome stands past the minefields, and "
                        "the whole war is wired to it.",
                 sites=("the minefields", "the assembly floor",
                        "the Tinkerer's dome"),
                 epilogue="The dome comes down. Without the Grand "
                          "Tinkerer the Thousand Workshops turn on each "
                          "other by nightfall; the war ends as a thousand "
                          "small explosions, none of them aimed, and the "
                          "fallen lands are freed."),
        ),
    ),
    "human": dict(
        banner="the Deathless Crown",
        creed="a human king has sold his crown to a hungry god: service "
              "no longer ends at death, the graves are a recruiting "
              "ground, and order eternal marches on its neighbors.",
        conqueror_title="Deathless King",
        lieutenant_titles=("Gravemarshal", "Bone Chancellor"),
        pool=UNDEAD_POOL + LADDER_POOL,
        skins={"skeleton": "Deathless Conscript", "ghoul": "Grave-Sworn",
               "wight": "Deathless Knight", "cutthroat": "Cult Knife",
               "archer": "Cult Archer", "bruiser": "Cult Enforcer",
               "soldier": "Cult Legionary", "veteran": "Cult Captain",
               "champion": "Deathless Paladin",
               "blademaster": "Sword of the Crown",
               "warlord": "Deathless King"},
        waves=(
            dict(title="Empty Graves on the Border",
                 desc="Churchyards along the {land} border are being "
                      "emptied by night, and a chapel nobody built is "
                      "burning candles that do not gutter.",
                 herald="a shaken priest from the {land} border: the "
                        "graves are empty, and the missing dead were seen "
                        "WALKING, in step.",
                 sites=("the robbed churchyard", "the cult chapel"),
                 epilogue="The chapel's censers are smashed and the "
                          "graves re-filled, this time with rites said "
                          "over them. For now, the border's dead stay "
                          "down."),
            dict(title="The Marching Dead",
                 desc="The Deathless Crown crosses into the {land} lands "
                      "behind {lt1}: a host that does not eat, sleep, or "
                      "break. Its heart is a black reliquary that must "
                      "not reach the walls.",
                 herald="the {land} lands are invaded: a column that "
                        "marches through the night, every night, and "
                        "grows at each churchyard it passes.",
                 sites=("the ford of the dead", "the siege lines",
                        "the black reliquary"),
                 epilogue="The reliquary cracks and the host falls where "
                          "it stands, rank by rank, like a held breath "
                          "let out. The {land} lands hold; the crows do "
                          "not starve."),
            dict(title="The Fall of the {land_cap} Lands",
                 desc="{lt2} brings the full muster against the {land} "
                      "lands -- and every defender who falls stands back "
                      "up on the wrong side. The walls cannot win that "
                      "arithmetic. The road out still can.",
                 herald="the worst kind of word from the {land} lands: "
                        "the dead outside the walls now outnumber the "
                        "living inside, and the count only moves one "
                        "way.",
                 sites=("the plague-lit outskirts", "the last gate",
                        "the evacuation road"),
                 epilogue="The {land} lands fall to a host that does not "
                          "sleep. Those on the evacuation road live to "
                          "hate the crown another day -- and they know "
                          "exactly whose blades bought them the road."),
            dict(title="The Deathless Court",
                 desc="{conqueror} sits a cathedral of bone at the heart "
                      "of the war, the god's grip on three lands running "
                      "through one dead king's hands. Unclench them.",
                 herald="the free crowns have one hope left and it is "
                        "blunt: kill the Deathless King on his own "
                        "throne, and the god behind him starves.",
                 sites=("the silent approach", "the cathedral of bone",
                        "the throne of the Deathless King"),
                 epilogue="The Deathless King is cut from his throne and "
                          "the god behind him starves. At the same hour, "
                          "in three lands, every conscripted corpse lies "
                          "down -- and this time stays down."),
        ),
    ),
    "orc": dict(
        banner="the Iron Sky Horde",
        creed="a khagan has united the orc clans under one law: might is "
              "right, war is glory, and everything under the iron sky is "
              "theirs to take.",
        conqueror_title="Khagan",
        lieutenant_titles=("First Spear", "Wolf-Keeper"),
        pool=LADDER_POOL + WOLF_POOL,
        skins={"wolf": "War-Wolf", "dire wolf": "War-Wolf Alpha",
               "cutthroat": "Horde Raider", "archer": "Horde Skirmisher",
               "bruiser": "Horde Breaker", "soldier": "Horde Sworn",
               "veteran": "Blooded of the Horde",
               "champion": "Clan-Champion",
               "blademaster": "Deathblade of the Khagan",
               "warlord": "Khagan"},
        waves=(
            dict(title="Outriders",
                 desc="Waystations along the {land} border are burning, "
                      "one a night, each with a wolf-tail standard left "
                      "in the ashes. The horde is counting the roads in.",
                 herald="riders from the {land} border: waystations "
                        "burn, and the raiders are not raiding -- they "
                        "are MAPPING.",
                 sites=("the burned waystation", "the outriders' camp"),
                 epilogue="The outriders' standard is cast down and sent "
                          "back to the steppes. The clans read it as an "
                          "omen worth arguing about; the border buys a "
                          "season."),
            dict(title="The Horde at the Gates",
                 desc="The Iron Sky Horde is in the {land} lands in "
                      "force, {lt1} at its point. The siege camp grows "
                      "daily; the breach is a matter of time unless "
                      "someone makes it a matter of blood.",
                 herald="the horde has come down on the {land} lands "
                        "entire -- herds taken, walls invested, and the "
                        "First Spear's drums heard through the ground.",
                 sites=("the herd trails", "the siege camp",
                        "the breach in the wall"),
                 epilogue="The siege breaks and the horde pulls back to "
                          "argue about whose fault it was. The {land} "
                          "lands hold, and the wall's new stones are "
                          "mortared with boasting."),
            dict(title="The Fall of the {land_cap} Lands",
                 desc="The Khagan turns the whole horde on the {land} "
                      "lands, {lt2}'s war-wolves running ahead of it. "
                      "The walls will break -- the fight now is for the "
                      "road out and everyone on it.",
                 herald="the ground itself carries it: the whole horde "
                        "moves on the {land} lands, and no wall built "
                        "by hands is rated for that.",
                 sites=("the trampled fields", "the last gate",
                        "the evacuation road"),
                 epilogue="The {land} lands fall to the horde. The "
                          "party's stand on the road is already a song "
                          "-- an orc song, which is its own kind of "
                          "respect."),
            dict(title="The Khagan's Tent",
                 desc="{conqueror} rules the war from the great "
                      "war-tent, by the old law: the horde follows the "
                      "mightiest. The law cuts both ways -- walk in and "
                      "prove otherwise.",
                 herald="the clans' own law is the opening: whoever "
                        "kills the Khagan in his own circle breaks the "
                        "horde -- and the free lands will pay to see it "
                        "tried.",
                 sites=("the picket lines", "the champions' circle",
                        "the war-tent"),
                 epilogue="The Khagan dies in his own circle, by his own "
                          "law: might made right, and today the party "
                          "was right. The clans scatter to fight each "
                          "other -- which is peace, as the steppes count "
                          "it -- and the fallen lands are freed."),
        ),
    ),
}


# --------------------------------------------------------------------------- #
# Story state -- lives in the session save under "story"
# --------------------------------------------------------------------------- #

def _names(story: dict) -> dict:
    """The .format keys authored content may use."""
    spec = CONQUESTS[story["aggressor"]]
    c = story["conqueror"]
    l1, l2 = story["lieutenants"]
    return {"banner": spec["banner"],
            "conqueror": f"{c['name']}, the {c['role']}",
            "lt1": f"{l1['name']}, the {l1['role']}",
            "lt2": f"{l2['name']}, the {l2['role']}"}


def init_story(world: dict, rng: random.Random,
               pc_race: str | None = None) -> dict:
    """Roll the playthrough's war at game start: the aggressor, the named
    faces, and the two victim lands. Nothing posts until the party earns
    wave 1 (level 2). `pc_race` is excluded from the aggressor roll
    (2026-07-13, designer call: the PC never fights his own people's war
    of conquest)."""
    from people import make_npc    # runtime import (people imports quests)
    present = list(lands(world))
    capital_land = world["settlements"][0]["race"]
    pool = [r for r in AGGRESSORS if r != pc_race] or list(AGGRESSORS)
    aggressor = rng.choice(pool)
    victims = [r for r in present if r != aggressor]
    # The land that FALLS (wave 3) must not host the capital -- wave 4 is
    # raised from the capital, which occupation would gate shut.
    b_pool = [r for r in victims if r != capital_land] or victims
    land_b = rng.choice(b_pool)
    a_pool = [r for r in victims if r != land_b] or victims
    land_a = rng.choice(a_pool)
    spec = CONQUESTS[aggressor]
    used: set[str] = set()
    faces = [make_npc(rng, aggressor, title, used_names=used)
             for title in (spec["conqueror_title"],)
             + spec["lieutenant_titles"]]
    return {"aggressor": aggressor,
            "conqueror": faces[0],
            "lieutenants": faces[1:],
            "targets": [land_a, land_b],
            "wave_posted": 0,       # how many waves have been posted
            "wave_done": 0,         # how many completed
            "quests": [],           # the wave qids, in posting order
            "fallen": None,         # the occupied land, after wave 3
            "over": False,
            "events": []}           # day-stamped story beats


def wave_target_land(story: dict, i: int) -> str | None:
    """Waves 1-2 press land A, wave 3 takes land B, wave 4 is raised from
    the capital (None -- the strike goes to the conqueror's own seat)."""
    return (story["targets"][0] if i < 2
            else story["targets"][1] if i == 2 else None)


def next_wave_due(story: dict | None, party_level: int) -> int | None:
    """The wave index to post now, or None: the previous wave must be DONE
    and the party at the wave's level."""
    if not story or story["over"]:
        return None
    i = story["wave_posted"]
    if i >= len(WAVE_LEVELS) or story["wave_done"] < i:
        return None
    return i if party_level >= WAVE_LEVELS[i] else None


def post_wave(world: dict, story: dict, rng: random.Random,
              day: int) -> tuple[dict, list[str]]:
    """Build and post the next wave's quest (an ordinary quest underneath:
    same schema, threat math, and pay), put the target land's RULER behind
    it as giver, cap it with the wave's named villain, and return the
    messenger scene for the DM to deliver."""
    i = story["wave_posted"]
    spec = CONQUESTS[story["aggressor"]]
    wv = spec["waves"][i]
    level = WAVE_LEVELS[i]
    land = wave_target_land(story, i)
    if land:
        settlement = lands(world)[land][0]
    else:
        # Wave 4 is raised from the capital -- unless the capital happens
        # to be the aggressor's own race (its free kin disowning the war
        # reads confusing); then the wave-2 ally land raises it instead.
        settlement = world["settlements"][0]
        if settlement["race"] == story["aggressor"]:
            settlement = lands(world)[story["targets"][0]][0]
    fmt = dict(_names(story), land=land or settlement["race"],
               land_cap=(land or settlement["race"]).capitalize())
    qid = f"w{i + 1}"
    quest = {"id": qid,
             "name": wv["title"].format(**fmt),
             "desc": wv["desc"].format(**fmt),
             "settlement": settlement["key"],
             "level": level,
             "skins": dict(spec["skins"]),
             "sites": [],
             "next": {"site": 0, "room": 0},
             "status": "open",
             "epilogue": wv["epilogue"].format(**fmt),
             "story_wave": i}
    n_sites = len(wv["sites"])
    for j, (stem, n_rooms) in enumerate(zip(wv["sites"], WAVE_ROOMS[i])):
        site_level = max(1, level - (n_sites - 1 - j))
        rooms = build_site_rooms(site_level, n_rooms, spec["pool"], rng)
        quest["sites"].append({"name": stem, "level": site_level,
                               "rooms": [[rn, list(ks)] for rn, ks in rooms]})
    boss_face = ([None, story["lieutenants"][0], story["lieutenants"][1],
                  story["conqueror"]][i])
    if boss_face is not None:
        last = quest["sites"][-1]
        kinds = last["rooms"][-1][1]
        strongest = max(kinds, key=threat_value)
        last["boss"] = {"kind": strongest,
                        "display": f"{boss_face['name']}, "
                                   f"the {boss_face['role']}"}
    ruler = next((n for n in world.get("npcs", [])
                  if n.get("post") == "ruler"
                  and n["land"] == settlement["race"]), None)
    if ruler is not None:
        quest["giver"] = dict(ruler)
    else:
        attach_giver(quest, settlement["race"], rng,
                     role="the war-muster's captain")
    world["quests"][qid] = quest
    settlement["quests"].append(qid)
    story["quests"].append(qid)
    story["wave_posted"] = i + 1
    story["events"].append({"day": day,
                            "line": f"wave {i + 1} posted: {quest['name']} "
                                    f"(at {settlement['name']})"})
    lines = [f"*** WORD OF THE WAR (day {day}) ***"]
    if i == 0:
        lines.append(f"War is coming: {spec['banner']} -- {spec['creed']}")
    lines.append("Herald: " + wv["herald"].format(**fmt))
    g = quest["giver"]
    lines.append(f"{g['name']}, {g['role']}, calls for blades at "
                 f"{settlement['name']}: [{qid}] L{level} {quest['name']} "
                 f"({n_sites} sites).")
    return quest, lines


def on_wave_done(story: dict, quest: dict, day: int) -> list[str]:
    """Bookkeeping when a wave quest completes: advance the story cursor,
    drop the occupation (wave 3) or end the war (wave 4). The quest's own
    epilogue has already been paid out by the normal quest machinery."""
    i = quest["story_wave"]
    story["wave_done"] = max(story["wave_done"], i + 1)
    lines: list[str] = []
    if i == 2:
        land = story["targets"][1]
        story["fallen"] = land
        lines.append(f"*** THE {land.upper()} LANDS ARE FALLEN. Their "
                     f"settlements lie under the {story['aggressor']} yoke "
                     f"-- no boards, no taverns, no hiring there until the "
                     f"war turns. The roads still pass through. ***")
    if i == 3:
        story["over"] = True
        if story["fallen"]:
            lines.append(f"*** The {story['fallen']} lands are FREE -- the "
                         f"occupation breaks with its master. ***")
            story["fallen"] = None
        lines.append("*** THE WAR IS OVER. ***")
    story["events"].append({"day": day,
                            "line": f"wave {i + 1} completed"})
    return lines


def occupied(story: dict | None, settlement: dict) -> bool:
    """Is this settlement under the aggressor's yoke (post-wave-3)?"""
    return bool(story) and story.get("fallen") == settlement["race"]


def war_status_lines(world: dict, story: dict | None) -> list[str]:
    """The one-glance war readout for board/map: the open wave (if any),
    and the occupation."""
    if not story or not story["wave_posted"]:
        return []
    spec = CONQUESTS[story["aggressor"]]
    if story["over"]:
        return [f"The war is over: {spec['banner']} is broken."]
    lines = []
    open_wave = next((qid for qid in story["quests"]
                      if world["quests"][qid]["status"] == "open"), None)
    if open_wave is not None:
        q = world["quests"][open_wave]
        s = next(s for s in world["settlements"]
                 if s["key"] == q["settlement"])
        lines.append(f"THE WAR: [{q['id']}] L{q['level']} {q['name']} -- "
                     f"raised at {s['name']}.")
    else:
        nxt = story["wave_posted"]
        if nxt < len(WAVE_LEVELS):
            lines.append(f"THE WAR: {spec['banner']} regroups -- word of "
                         f"the next blow will find a party of level "
                         f"{WAVE_LEVELS[nxt]}.")
    if story.get("fallen"):
        lines.append(f"THE WAR: the {story['fallen']} lands lie under the "
                     f"{story['aggressor']} yoke.")
    return lines


# --------------------------------------------------------------------------- #
# Demo (the designer's eyeball check)
# --------------------------------------------------------------------------- #

def main() -> None:
    from quests import generate_world
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--aggressor", choices=AGGRESSORS, default=None)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    world = generate_world(rng.randrange(1 << 30))
    story = init_story(world, rng)
    if args.aggressor:
        story["aggressor"] = args.aggressor      # eyeball a chosen variant
        from people import make_npc
        spec = CONQUESTS[args.aggressor]
        used: set[str] = set()
        faces = [make_npc(rng, args.aggressor, t, used_names=used)
                 for t in (spec["conqueror_title"],)
                 + spec["lieutenant_titles"]]
        story["conqueror"], story["lieutenants"] = faces[0], faces[1:]
    spec = CONQUESTS[story["aggressor"]]
    print(f"Aggressor: {story['aggressor']} -- {spec['banner']}")
    print(f"  {spec['creed']}")
    n = _names(story)
    print(f"  conqueror: {n['conqueror']}; lieutenants: {n['lt1']}; "
          f"{n['lt2']}")
    print(f"  targets: waves 1-2 press the {story['targets'][0]} lands, "
          f"wave 3 takes the {story['targets'][1]} lands")
    for i in range(len(WAVE_LEVELS)):
        print()
        quest, lines = post_wave(world, story, rng, day=0)
        for line in lines:
            print(line)
        for line in quest_detail_lines(quest):
            print(line)
        print(f"    epilogue: {quest['epilogue']}")
        quest["status"] = "done"        # force the gate for the dump
        for line in on_wave_done(story, quest, day=0):
            print(line)


if __name__ == "__main__":
    main()
