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

from rpg import site_xp_total, site_gold
from quests import (LADDER_POOL, WOLF_POOL, UNDEAD_POOL,
                    build_site_rooms, threat_value, attach_giver,
                    new_site, new_room, quest_sites, site_rooms,
                    settlements, settlements_by_land,
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
        banner="the Golden Empire",
        creed="The elf empire believes other peoples are weak and must be "
              "ruled. Its army of magic machines is crossing the border.",
        conqueror_title="High General",
        lieutenant_titles=("Chief Engineer", "Army Captain"),
        pool=LADDER_POOL + ("ogre", "troll"),
        skins={"cutthroat": "Golden Scout", "archer": "Magic Rifleman",
               "bruiser": "Steam Knight", "soldier": "War Machine",
               "veteran": "Heavy War Machine", "champion": "Battle Mage",
               "blademaster": "Master Swordsman", "warlord": "High General",
               "ogre": "Giant War Machine", "troll": "Siege Machine"},
        waves=(
            dict(title="Machines at the Border",
                 desc="Elf scouts are marking farms along the {land} border. "
                      "War machines follow them and drive the farmers out.",
                 herald="a rider from the {land} border: elf scouts and war "
                        "machines have crossed the border.",
                 sites=("the scout camp", "the occupied farms"),
                 epilogue="The scouts and machines are destroyed. The elves "
                          "pull back from the border."),
            dict(title="The Elf Invasion",
                 desc="The Golden Empire has invaded the {land} lands. {lt1} "
                      "is building a factory that makes new war machines. "
                      "Destroy it.",
                 herald="the Golden Empire has invaded the {land} lands. A "
                        "war factory is being built near the main road.",
                 sites=("the ruined watchtower", "the river works",
                        "the war factory"),
                 epilogue="The factory is destroyed. The {land} lands stop "
                          "the invasion."),
            dict(title="Evacuate the {land_cap} Lands",
                 desc="{lt2} leads the main army into the {land} lands. The "
                      "walls will fall. Keep the escape road open.",
                 herald="the main elf army has reached the {land} lands. The "
                        "city must be evacuated.",
                 sites=("the burning defenses", "the last gate",
                        "the evacuation road"),
                 epilogue="The {land} lands fall to the empire. The party "
                          "keeps the road open and many people escape."),
            dict(title="Kill the High General",
                 desc="{conqueror} commands the war from the main factory. "
                      "Kill the general and stop the army.",
                 herald="the allied kingdoms have found the High General's "
                        "base. They will pay the party to destroy it.",
                 sites=("the outer defenses", "the main factory",
                        "the general's hall"),
                 epilogue="The main factory stops. The empire asks for peace, "
                          "and its armies leave the conquered lands."),
        ),
    ),
    "goblin": dict(
        banner="the Thousand Workshops",
        creed="The goblin bosses have united. They plan to rebuild the world "
              "with bombs, machines, and monsters.",
        conqueror_title="Master Tinkerer",
        lieutenant_titles=("Bomb General", "Beast Maker"),
        pool=LADDER_POOL + WOLF_POOL + ("ogre", "troll"),
        skins={"wolf": "Mutant Hound", "dire wolf": "Mutant Dire Hound",
               "cutthroat": "Goblin Bomber", "archer": "Scrap Gunner",
               "bruiser": "Scrap-Golem", "soldier": "Tin Soldier",
               "veteran": "Tin Sergeant", "champion": "War Tinkerer",
               "blademaster": "Sawblade Duelist", "warlord": "Master Tinkerer",
               "ogre": "Walking Bomb", "troll": "Mutant Hulk"},
        waves=(
            dict(title="Stolen Parts",
                 desc="Animals, tools, and people are disappearing along the "
                      "{land} border. Goblins are using them to build new "
                      "monsters.",
                 herald="a guard from the {land} border: goblins are stealing "
                        "animals, tools, and people.",
                 sites=("the stripped farm", "the goblin workshop"),
                 epilogue="The workshop is destroyed. The thefts stop."),
            dict(title="Bombs and Tunnels",
                 desc="The Thousand Workshops have invaded the {land} lands. "
                      "{lt1} bombs the defenses while a machine digs under "
                      "the walls. Destroy both.",
                 herald="the {land} lands are under attack. Goblins bomb the "
                        "walls while a machine digs below them.",
                 sites=("the bombed camp", "the bomb line",
                        "the digging machine"),
                 epilogue="The digging machine and bomb line are destroyed. "
                          "The {land} lands hold."),
            dict(title="Evacuate the {land_cap} Lands",
                 desc="{lt2} attacks the {land} lands with poison gas and "
                      "mutant soldiers. The walls are lost. Keep the escape "
                      "road open.",
                 herald="the goblin army has broken the walls of the {land} "
                        "lands. The city must be evacuated.",
                 sites=("the poisoned walls", "the breach",
                        "the evacuation road"),
                 epilogue="The {land} lands fall to the Workshops. The party "
                          "holds the road while the people escape."),
            dict(title="Destroy the Main Workshop",
                 desc="All goblin armies take orders from {conqueror}'s main "
                      "workshop. Kill the Tinkerer and destroy it.",
                 herald="deserters have found the Master Tinkerer's workshop. "
                        "Destroy it to end the war.",
                 sites=("the minefields", "the main workshop",
                        "the Tinkerer's room"),
                 epilogue="The Tinkerer is dead. The Workshops fight each "
                          "other, and the war ends."),
        ),
    ),
    "human": dict(
        banner="the Undead Kingdom",
        creed="A human king serves a dark god. His army raises the dead and "
              "sends them to conquer nearby lands.",
        conqueror_title="Undead King",
        lieutenant_titles=("Grave General", "Bone Priest"),
        pool=UNDEAD_POOL + LADDER_POOL,
        skins={"skeleton": "Undead Soldier", "ghoul": "Ghoul Soldier",
               "wight": "Undead Knight", "cutthroat": "Cult Assassin",
               "archer": "Cult Archer", "bruiser": "Cult Guard",
               "soldier": "Cult Soldier", "veteran": "Cult Captain",
               "champion": "Undead Champion",
               "blademaster": "Royal Swordmaster",
               "warlord": "Undead King"},
        waves=(
            dict(title="The Dead Rise",
                 desc="Cultists are stealing bodies from graveyards along the "
                      "{land} border. They are raising the dead in a hidden "
                      "chapel.",
                 herald="a priest from the {land} border: the graves are "
                        "empty, and the dead are walking.",
                 sites=("the empty graveyard", "the hidden chapel"),
                 epilogue="The cultists are dead and the chapel is destroyed. "
                          "The stolen bodies are buried again."),
            dict(title="The Army of the Dead",
                 desc="The undead army has entered the {land} lands. A black "
                      "relic controls it. Destroy the relic before the army "
                      "reaches the city.",
                 herald="the undead army has invaded the {land} lands. It "
                        "marches through the night and grows at every "
                        "graveyard.",
                 sites=("the bridge of the dead", "the undead camp",
                        "the black relic"),
                 epilogue="The relic is destroyed. The undead army falls, and "
                          "the {land} lands hold."),
            dict(title="Evacuate the {land_cap} Lands",
                 desc="{lt2} leads the full undead army into the {land} "
                      "lands. Fallen defenders rise and join the enemy. Keep "
                      "the escape road open.",
                 herald="the undead have broken the defenses of the {land} "
                        "lands. The city must be evacuated.",
                 sites=("the ruined outskirts", "the last gate",
                        "the evacuation road"),
                 epilogue="The {land} lands fall to the undead. The party "
                          "holds the road while the people escape."),
            dict(title="Kill the Undead King",
                 desc="{conqueror} controls the undead army from his throne. "
                      "Kill the king and break the dark god's power.",
                 herald="the allied kingdoms know where the Undead King is. "
                        "Kill him to stop the army.",
                 sites=("the road to the castle", "the bone temple",
                        "the throne room"),
                 epilogue="The Undead King is dead. His army falls, and the "
                          "conquered lands are free."),
        ),
    ),
    "orc": dict(
        banner="the Iron Horde",
        creed="An orc warlord has united the clans. He plans to conquer every "
              "land his army can reach.",
        conqueror_title="Warlord",
        lieutenant_titles=("War Chief", "Wolf Master"),
        pool=LADDER_POOL + WOLF_POOL,
        skins={"wolf": "War Wolf", "dire wolf": "Dire War Wolf",
               "cutthroat": "Horde Raider", "archer": "Horde Archer",
               "bruiser": "Horde Brute", "soldier": "Horde Warrior",
               "veteran": "Horde Veteran",
               "champion": "Horde Champion",
               "blademaster": "Horde Swordmaster",
               "warlord": "Orc Warlord"},
        waves=(
            dict(title="Orc Scouts",
                 desc="Orc raiders are burning guard posts along the {land} "
                      "border. They are mapping the roads for an invasion.",
                 herald="a guard from the {land} border: orc raiders are "
                        "burning guard posts and mapping the roads.",
                 sites=("the burned guard post", "the orc camp"),
                 epilogue="The raiders are dead. The invasion is delayed."),
            dict(title="The Horde Invasion",
                 desc="The Iron Horde has invaded the {land} lands. {lt1} "
                      "leads the siege. Break the camp and stop the attack.",
                 herald="the Iron Horde has invaded the {land} lands. The War "
                        "Chief is attacking the main city.",
                 sites=("the occupied farms", "the siege camp",
                        "the broken wall"),
                 epilogue="The siege is broken. The horde leaves the {land} "
                          "lands."),
            dict(title="Evacuate the {land_cap} Lands",
                 desc="The Warlord sends the whole horde into the {land} "
                      "lands. The walls will fall. Keep the escape road open.",
                 herald="the whole horde is attacking the {land} lands. The "
                        "city must be evacuated.",
                 sites=("the ruined farms", "the last gate",
                        "the evacuation road"),
                 epilogue="The {land} lands fall to the horde. The party "
                          "holds the road while the people escape."),
            dict(title="Kill the Warlord",
                 desc="{conqueror} commands the horde from a guarded war "
                      "camp. Kill him and break the invasion.",
                 herald="the allied kingdoms have found the Warlord's camp. "
                        "Kill him to end the war.",
                 sites=("the outer camp", "the champion's ring",
                        "the warlord's tent"),
                 epilogue="The Warlord is dead. The clans turn on each other, "
                          "and the conquered lands are free."),
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
    present = list(world["lands"])
    capital_land = settlements(world)[0]["land"]
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
        settlement = settlements_by_land(world)[land][0]
    else:
        # Wave 4 is raised from the capital -- unless the capital happens
        # to be the aggressor's own race (its free kin disowning the war
        # reads confusing); then the wave-2 ally land raises it instead.
        settlement = settlements(world)[0]
        if settlement["land"] == story["aggressor"]:
            settlement = settlements_by_land(world)[story["targets"][0]][0]
    fmt = dict(_names(story), land=land or settlement["land"],
               land_cap=(land or settlement["land"]).capitalize())
    qid = f"w{i + 1}"
    quest = {"id": qid,
             "name": wv["title"].format(**fmt),
             "desc": wv["desc"].format(**fmt),
             "origin": settlement["key"],
             "level": level,
             "skins": dict(spec["skins"]),
             "sites": [], "site_count": len(wv["sites"]),
             "room_count": sum(WAVE_ROOMS[i]),
             "xp_total": 0, "gold_total": 0,
             "next": {"site": 0, "room": 0},
             "status": "open",
             "epilogue": wv["epilogue"].format(**fmt),
             "story_wave": i}
    n_sites = len(wv["sites"])
    for j, (stem, n_rooms) in enumerate(zip(wv["sites"], WAVE_ROOMS[i])):
        site_level = max(1, level - (n_sites - 1 - j))
        rooms = build_site_rooms(site_level, n_rooms, spec["pool"], rng)
        site_id = f"{qid}/s{j + 1}"
        new_site(world, settlement["key"], site_id, stem, site_level,
                 quest=qid)
        for k, (rn, kinds) in enumerate(rooms):
            new_room(world, site_id, f"{site_id}/r{k + 1}", rn, list(kinds),
                     quest=qid)
        quest["sites"].append(site_id)
        quest["xp_total"] += site_xp_total(site_level)
        quest["gold_total"] += site_gold(site_level)
    boss_face = ([None, story["lieutenants"][0], story["lieutenants"][1],
                  story["conqueror"]][i])
    if boss_face is not None:
        last = world["sites"][quest["sites"][-1]]
        kinds = site_rooms(world, last)[-1]["kinds"]
        strongest = max(kinds, key=threat_value)
        last["boss"] = {"kind": strongest,
                        "display": f"{boss_face['name']}, "
                                   f"the {boss_face['role']}"}
    ruler = next((n for n in world.get("npcs", [])
                  if n.get("post") == "ruler"
                  and n["land"] == settlement["land"]), None)
    if ruler is not None:
        quest["giver"] = dict(ruler)
    else:
        attach_giver(quest, settlement["land"], rng,
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
    return bool(story) and story.get("fallen") == settlement["land"]


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
        s = world["areas"][q["origin"]]
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
        for line in quest_detail_lines(world, quest):
            print(line)
        print(f"    epilogue: {quest['epilogue']}")
        quest["status"] = "done"        # force the gate for the dump
        for line in on_wave_done(story, quest, day=0):
            print(line)


if __name__ == "__main__":
    main()
