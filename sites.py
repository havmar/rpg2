"""The game's content: the foe catalog and the two hand-built sites.

The engine lives in rpg.py; this file holds what you FIGHT and WHERE. It is
the seed of the encounter & quest system (plan.md): foe stat blocks (FOES),
the two set sites (SITES -- the bandit hideout and the skeleton barrow), and
ONE generic site runner (run_site) shared by the one-shot entry point and the
batch sims (tune.py, bench_training.py), so the layout that gets tuned is the
layout that gets played. Session play (session.py) draws rooms and foes from
the same tables.

The two sites, by design:
- The bandit HIDEOUT is the STARTER site. Bandits are living fighters who
  play by exactly the party's rules: real DEX/STR, they spend STA to swing,
  go Winded, and are SPENT at 0 like anyone alive -- its logs teach the
  system with no special cases. A level-1 site: a full clear (3 encounters +
  quest) is exactly the level-1 -> 2 XP cost.
- The skeleton BARROW is the TOUGH site (level 3 -- double XP, triple gold,
  by the level formulas like every site). Skeletons are the exception
  enemies: undead and tireless (never spend STA, never Winded/Spent), so
  the threat is numbers outlasting a party whose stamina is a death-track.
  Met second on purpose: living foes first.

Run:  python sites.py                        # one-shot barrow run, full log
      python sites.py --site hideout         # one-shot starter-site run
      python sites.py --seed 7               # reproducible
      python sites.py --training 2           # start the party pre-trained
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass

from rpg import (Entity, Weapon, Clock, Purse, RUSTED_BLADE, CROWD_CAP,
                 WEAPONS, make_party, stat_line, outcome, start_fight,
                 short_rest, long_rest, party_wiped,
                 award_xp, award_quest, roll_loot, auto_use_potions_on_rest,
                 train_combat, random_common_weapon,
                 sim_fight, refresh_foes_after_retreat,
                 site_encounter_xp, site_clear_xp, site_gold,
                 SIM_MAX_ROOM_ATTEMPTS)


# --------------------------------------------------------------------------- #
# The foe catalog
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class FoeSpec:
    """One foe stat block. The monster/opponent catalog (the seed of the
    encounter & quest system, plan.md): every foe in the game is a row here,
    and make_foe() is the one place a stat block becomes a fighting Entity.

    `level` is the catalog's difficulty annotation: the party level (at the
    TWO-hero baseline the game is balanced for) for which this row's
    reference encounter -- `ref_pack` of these, benched in bench_bestiary.py
    -- is a fair, still-scary fight. The future encounter generator builds
    from these annotations; they are guidance, not engine input."""
    display: str            # log name stem ("Skeleton" -> "Skeleton 3")
    level: int              # difficulty annotation (duo baseline; see above)
    dex: int
    str_: int
    sta: int
    hp: int
    ref_pack: int = 1       # how many of these make the reference encounter
                            # at `level` (wolves hunt in packs; a troll is
                            # a fight alone)
    training: int = 0       # combat training rank (the party's own +1/rank
                            # to all pressure rolls) -- the elite-humanoid
                            # lever: how a champion outfences you without a
                            # monster's DEX. 0 for everything that isn't a
                            # drilled fighter.
    undead: bool = False    # dead flesh: wounds never knit back on their own
    pain: int = 1           # wound penalty divisor (1 feels everything --
                            # small critters; 2 the trained-fighter norm,
                            # matching HERO_PAIN, plus undead/brutes; 3-4
                            # the apex monsters)
    tireless: bool = False  # never spends STA, never Winded/Spent
    pursues: bool = True    # gives chase when the party retreats
    power: int = 0          # ability fuel (dragonfire is paid for). For a
                            # CASTER row it is double-duty: the bolt's
                            # pressure stat AND the ammo pool (a power-6
                            # caster throws 6 bolts at +6), exactly like a
                            # hero wizard's POWER
    school: str = ""        # placeholder magic: "fire"/"ice" makes the row
                            # a caster -- bolts while the power lasts, then
                            # the carried weapon (rpg.Entity.school)
    school_prof: int = 0    # the caster row's school proficiency rank (+1
                            # bolt pressure AND +1 bolt severity per rank)
                            # -- the same ranks heroes drill, and the
                            # severity lever enemy casters need (BOLT_SEVERITY
                            # is global: buffing it would buff hero wizards
                            # too)
    crowd_cap: int = CROWD_CAP  # attackers that can press it at once
                                # (big monsters take 3-4: boss fights
                                # stay full-party under the press)
    regen: int = 0          # HP knit per round while up (the troll)
    sweep: int = 1          # max targets per attack (the giant's sweep,
                            # dragonfire); 1 = normal single attacks
    sweep_cost_power: int = 0   # Power per multi-target use; 0 = free
    sweep_label: str = ""   # log flavor for the multi-target blow
    weapon: Weapon | None = None    # fixed armament (the skeletons' rusted
                                    # blades, a wolf's fangs); None = roll
                                    # the common table like a starting hero


# Natural weapons -- fangs, claws, tusks: part of the body. They never break,
# never break steel (breakage is a steel-on-steel event), and are never left
# as loot. Profiles stay small on purpose: a monster's severity lives in its
# STR; the natural weapon just shades it.
NATURAL_WEAPONS = {w.name: w for w in [
    Weapon("fangs", 0, 0, 1, durability=3, natural=True,
           description="Teeth made for smaller prey than you. Quick, shallow work."),
    Weapon("heavy claws", 0, 1, 1, durability=3, natural=True,
           description="Claws that open a man like a latch."),
    Weapon("tusks", 0, 1, 1, durability=3, natural=True,
           description="A boar's gore: low, sudden, and deeper than it looks."),
    Weapon("grave claws", 0, 0, 1, durability=3, natural=True,
           description="Cold fingers ending in cracked black nails."),
    Weapon("ogre club", 0, 2, 1, durability=3, natural=True,
           description="A torn-up sapling in a fist the size of a keg."),
    Weapon("giant's club", 0, 2, 1, durability=3, natural=True,
           description="A whole tree, swung. There is no parrying the weather."),
    Weapon("venomous sting", 0, 2, 1, durability=3, natural=True,
           description="A tail-lash that hits like a spear thrust."),
    Weapon("fang and claw", 0, 1, 1, durability=3, natural=True,
           description="An armory that walks: teeth, talons, and tail."),
    Weapon("fang and fury", 0, 2, 1, durability=3, natural=True,
           description="A dragon at arm's length. Every part of it kills."),
]}

# The wight's grave-steel is REAL steel -- a chieftain was buried with his
# blade, and it has kept its edge (and is worth looting, unlike the
# skeletons' corroded rubbish).
BARROW_BLADE = Weapon("barrow blade", 0, 1, 1, durability=2, tags=("ancient",),
                      value=15,
                      description="A chieftain's burial sword, still true. "
                                  "Heavy-arms steel with a dead man's name.")

# Enemy DEX runs hot across the board (2026-07 lethality retune): who hits is
# DEX's job, and danger has to live in each encounter itself -- the party can
# always camp after it. A single point of foe DEX moves clear rates by tens
# of percent; it is the sharpest tuning knife in this table.
#
# THE BESTIARY (2026-07). Six monster families span the 1-20 curve; humanoids
# (the bandit rows here, soldiers, champions...) run parallel across every
# level, and the tier ABOVE the dragon is humanoid on purpose -- demons,
# demigods, liches are authored one-offs built on the hero tables (rules.md),
# never catalog rows. Each family introduces at most one mechanic and each
# row is a puzzle with a hole (rules.md: lopsidedness); the dragon is a boss
# precisely because it has none. Levels are bench-calibrated
# (bench_bestiary.py) at the two-hero baseline; `ref_pack` says what the
# benched encounter is (3 wolves, ONE troll).
FOES = {
    # --- Humanoids: the bandits (levels 1-2). Raw living fighters, no
    # Power/ability/kit. They arm from the same common-weapon table as
    # starting heroes (50% crude / 45% soldier's arms / 5% heavy) -- always a
    # specific named weapon, so the logs read "Cutthroat 2's dagger", never
    # "a crude weapon".
    "cutthroat": FoeSpec("Cutthroat", level=1, dex=5, str_=3, sta=5, hp=7,
                         ref_pack=3, pain=2),   # nimble knife-work
    "bruiser":   FoeSpec("Bruiser",   level=2, dex=4, str_=5, sta=5, hp=9,
                         ref_pack=3, pain=2),   # heavy and durable, quicker
                                                # than he looks
    "archer":    FoeSpec("Archer",    level=1, dex=5, str_=2, sta=5, hp=6,
                         ref_pack=3, pain=2),   # lands often, soft
    # --- The soldiery (levels 3-19): the humanoid LADDER. Living fighters
    # who play by exactly the party's rules at every band -- no mechanic, no
    # hole but their humanity: they tire, they bleed, and they grit through
    # pain like any drilled fighter (pain 2, the human-combatant norm). They exist so the level line has humanoids parallel to the
    # monster families (plan.md prescribed them to fill the catalog's level
    # gaps: 6-7, 15-17, 19-20), and so the encounter generator always has a
    # reskinnable fallback for any race's fiction ("rival warband",
    # "grave-robbers", "press-gang"...). Fixed military steel -- a soldier
    # does not roll on the mook table -- rising with rank; the top ranks
    # carry lootable quality blades (a story beat by then, not an economy
    # break). Statlines climb toward rules.md's Heroes table: the warlord IS
    # roughly the Legend row on the wrong side.
    "soldier":     FoeSpec("Soldier",     level=3,  dex=5, str_=4, sta=6,
                           hp=10, ref_pack=3, pain=2, weapon=WEAPONS["spear"]),
    "veteran":     FoeSpec("Veteran",     level=6,  dex=6, str_=5, sta=7,
                           hp=13, ref_pack=3, pain=2,
                           weapon=WEAPONS["longsword"]),
    "champion":    FoeSpec("Champion",    level=10, dex=7, str_=6, sta=8,
                           hp=17, ref_pack=2, training=2, pain=2,
                           weapon=WEAPONS["longsword"]),
    "blademaster": FoeSpec("Blademaster", level=15, dex=8, str_=6, sta=8,
                           hp=16, ref_pack=2, training=2, pain=2,
                           weapon=WEAPONS["katana"]),
    "warlord":     FoeSpec("Warlord",     level=19, dex=8, str_=8, sta=9,
                           hp=20, ref_pack=2, training=2, pain=2,
                           weapon=WEAPONS["zweihander"]),
    # --- The casters (placeholder magic, 2026-07-14): humanoid wizards, the
    # enemy mirror of the party's own. Bolts roll off POWER (double-duty:
    # stat AND ammo -- see FoeSpec.power) and IGNORE the caster's soft body,
    # which is the family's whole shape: dangerous until the Power runs dry,
    # then a robed conscript with a knife. Close fast or bleed at range.
    # The hexer's ice bolts barely cut but RIME (-1 DEX per landed bolt,
    # stacking, all fight) -- the debuff showcase; the pyromancer's fire
    # bolts hit like heavy steel off a stat no wound slows as fast. The
    # magus is the solo tower fight: drilled, deep Power, real steel after.
    "hexer":      FoeSpec("Hexer",      level=3,  dex=4, str_=2, sta=6,
                          hp=10, ref_pack=2, pain=2, power=8, school="ice",
                          school_prof=2, weapon=WEAPONS["dagger"]),
    "pyromancer": FoeSpec("Pyromancer", level=6,  dex=4, str_=2, sta=7,
                          hp=12, ref_pack=2, pain=2, power=8, school="fire",
                          school_prof=2, weapon=WEAPONS["dagger"]),
    "magus":      FoeSpec("Magus",      level=10, dex=6, str_=4, sta=9,
                          hp=24, ref_pack=1, training=3, pain=2, power=11,
                          school="fire", school_prof=3,
                          weapon=WEAPONS["longsword"]),
    # --- The restless dead (levels 2-8): tireless + slow to pain, the rules
    # broken on purpose (living foes teach the system; undead break it).
    # The skeleton: brittle and a weak individual hitter (low STR -> low
    # severity), but the stamina war is one-sided; the bones don't have to
    # beat you, just outlast you. pursues=False: bound to the grave -- they
    # swing at a fleeing party's backs but never follow past the door, which
    # is what makes "come back tomorrow and finish it" a real plan instead of
    # a death sentence. Their corroded grave-steel (durability 1) snaps on
    # good steel -- the barrow visibly eases as the party's gear improves.
    "skeleton":  FoeSpec("Skeleton",  level=2, dex=4, str_=2, sta=8, hp=5,
                         ref_pack=3, undead=True, pain=2, tireless=True,
                         pursues=False, weapon=RUSTED_BLADE),
    # The ghoul: the skeleton's upgrade with the barrow's one mercy removed --
    # hunger FOLLOWS (pursues). Meat on the bones: more HP, real claws.
    "ghoul":     FoeSpec("Ghoul",     level=4, dex=5, str_=3, sta=8, hp=8,
                         ref_pack=3, undead=True, pain=2, tireless=True,
                         weapon=NATURAL_WEAPONS["grave claws"]),
    # The wight: the tireless DUELIST -- a barrow-lord with a champion's DEX
    # and his burial blade (real, lootable steel). Grave-bound like his
    # soldiers. The puzzle: skill that never tires; your clock runs, his
    # doesn't.
    "wight":     FoeSpec("Wight",     level=8, dex=7, str_=5, sta=8, hp=16,
                         ref_pack=2, undead=True, pain=2, tireless=True,
                         pursues=False, weapon=BARROW_BLADE),
    # --- The wolves (levels 1-4): the pack. Fast, fragile, and they set the
    # pace -- and they PURSUE: retreating from wolves is how heroes die tired.
    "wolf":      FoeSpec("Wolf",      level=1, dex=4, str_=2, sta=8, hp=4,
                         ref_pack=4, weapon=NATURAL_WEAPONS["fangs"]),
    "dire wolf": FoeSpec("Dire Wolf", level=3, dex=6, str_=3, sta=10, hp=9,
                         ref_pack=2, weapon=NATURAL_WEAPONS["fangs"]),
    # --- The beasts (levels 2-5): the soak wall. Low DEX, heavy STR both
    # ways, slow to pain -- the first foes chip damage struggles against.
    "boar":      FoeSpec("Boar",      level=2, dex=3, str_=5, sta=6, hp=9,
                         ref_pack=2, pain=2,
                         weapon=NATURAL_WEAPONS["tusks"]),
    "bear":      FoeSpec("Bear",      level=4, dex=5, str_=7, sta=8, hp=22,
                         ref_pack=1, pain=2, crowd_cap=3, sweep=2,
                         sweep_label="a mauling swipe",
                         weapon=NATURAL_WEAPONS["heavy claws"]),
    # --- Vermin grown large (level 3): the ambusher -- lands often, folds
    # fast. (Venom is parked with the conditions system, plan.md; the bite
    # itself carries the row for now.)
    "great spider": FoeSpec("Great Spider", level=3, dex=6, str_=2, sta=7,
                            hp=6, ref_pack=3,
                            weapon=NATURAL_WEAPONS["fangs"]),
    # --- Giant-kin (levels 6-12): the severity cliff. Every landed blow is a
    # tier the party can't afford; the hole is a DEX that rarely lands it.
    "ogre":      FoeSpec("Ogre",      level=5, dex=6, str_=8, sta=8, hp=24,
                         ref_pack=1, pain=2, crowd_cap=3,
                         weapon=NATURAL_WEAPONS["ogre club"]),
    # The troll: REGENERATION -- the anti-attrition puzzle. Chip damage and
    # camp-and-return both fail (a fled troll is a healed troll); you must
    # out-damage the knitting or lose to it.
    "troll":     FoeSpec("Troll",     level=8, dex=6, str_=7, sta=10, hp=22,
                         ref_pack=1, pain=2, regen=3, crowd_cap=3,
                         weapon=NATURAL_WEAPONS["heavy claws"]),
    # The giant: the cliff at full height, and the first SWEEP -- one blow,
    # two heroes. (The sweep is also the top end's party-size counterweight:
    # more swords in the line means more swords under the club.)
    "giant":     FoeSpec("Giant",     level=12, dex=6, str_=9, sta=10, hp=26,
                         ref_pack=1, pain=3, crowd_cap=4, sweep=2,
                         sweep_label="a great sweeping blow",
                         weapon=NATURAL_WEAPONS["giant's club"]),
    # --- The drakes (levels 10-20): the apex family. Real DEX on a monster
    # frame -- the wyvern is the gate, the drake adds fire, the dragon has
    # no hole at all.
    "wyvern":    FoeSpec("Wyvern",    level=10, dex=8, str_=7, sta=10, hp=26,
                         ref_pack=1, pain=2, crowd_cap=3, sweep=2,
                         sweep_label="a lashing tail",
                         weapon=NATURAL_WEAPONS["venomous sting"]),
    "drake":     FoeSpec("Drake",     level=14, dex=8, str_=7, sta=10, hp=30,
                         ref_pack=1, pain=3, power=6, crowd_cap=4,
                         sweep=3, sweep_cost_power=2,
                         sweep_label="a gout of fire",
                         weapon=NATURAL_WEAPONS["fang and claw"]),
    "dragon":    FoeSpec("Dragon",    level=18, dex=8, str_=9, sta=12, hp=50,
                         ref_pack=1, pain=4, power=12, crowd_cap=4,
                         sweep=4, sweep_cost_power=3,
                         sweep_label="a torrent of dragonfire",
                         weapon=NATURAL_WEAPONS["fang and fury"]),
}

BANDIT_KINDS = ("archer", "bruiser", "cutthroat")   # the living-foe pool


def make_foe(kind: str, n: int, rng: random.Random,
             display: str | None = None) -> Entity:
    """Stat block -> fighting Entity, numbered for the log ("Cutthroat 2").

    `display` reskins the row for the log ("Scrap-Hound 2" over the wolf
    block): display name is FICTION, the stat row is MECHANICS -- the quest
    generator's one trick for making 5 races out of one calibrated catalog
    (quests.py THEMES). Balance never forks on a skin."""
    spec = FOES[kind]
    weapon = spec.weapon if spec.weapon is not None else random_common_weapon(rng)
    e = Entity(name=f"{display or spec.display} {n}", dex=spec.dex, str_=spec.str_,
               sta=spec.sta, max_hp=spec.hp, training=spec.training,
               undead=spec.undead,
               pain=spec.pain, tireless=spec.tireless,
               pursues=spec.pursues, power=spec.power, school=spec.school,
               crowd_cap=spec.crowd_cap, regen=spec.regen,
               sweep=spec.sweep, sweep_cost_power=spec.sweep_cost_power,
               sweep_label=spec.sweep_label, weapon=weapon)
    if spec.school and spec.school_prof:
        e.proficiency[e.school_prof_key] = spec.school_prof
    return e


def roster_lines(foes: list[Entity]) -> list[str]:
    """The room's roster for the log. Identical foes collapse into one
    counted line ("3x Skeleton: ..."); foes that differ (a bandit's rolled
    weapon, a survivor's wounds) each get their own."""
    def body(e: Entity) -> str:
        wpn = e.weapon.name if e.weapon else "unarmed"
        tags = []
        if e.training:
            tags.append(f"drilled +{e.training}")
        if e.undead:
            tags.append("undead")
        # pain 2 is the trained-fighter norm now (heroes included), so only
        # the apex divisors rate a tag.
        if e.pain >= 3:
            tags.append("barely feels pain")
        if e.tireless:
            tags.append("tireless")
        if e.regen:
            tags.append(f"wounds knit +{e.regen}/round")
        if e.school:
            prof = f" +{e.school_prof}" if e.school_prof else ""
            tags.append(f"{e.school} magic{prof}, {e.power} Power")
        if e.sweep > 1:
            tags.append(e.sweep_label or "sweeping blows")
        tag = f"; {', '.join(tags)}" if tags else ""
        sta = "" if e.tireless else f"STA {e.sta}  "
        return (f"DEX {e.dex}  STR {e.str_}  {sta}HP {e.hp}/{e.max_hp}  "
                f"({wpn}{tag})")

    groups: list[tuple[str, list[Entity]]] = []
    for f in foes:
        b = body(f)
        for gb, members in groups:
            if gb == b:
                members.append(f)
                break
        else:
            groups.append((b, [f]))
    lines = []
    for b, members in groups:
        if len(members) == 1:
            lines.append(f"{members[0].name}: {b}")
        else:
            stem = members[0].name.rsplit(" ", 1)[0]
            lines.append(f"{len(members)}x {stem}: {b}")
    return lines


# --------------------------------------------------------------------------- #
# The sites
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Site:
    """One authored site: set rooms, set rosters, level-set pay. The sites
    are balanced during development and never improvised at the table -- the
    DM runs them room-by-room (session.py `hideout ROOM` / `barrow ROOM`);
    `fight N` is the off-script escape hatch for improvised scenes only.
    Pay derives from `level` (rpg.site_encounter_xp / site_clear_xp /
    site_gold): the level IS the pay grade, for these two exactly as for
    every generated site (quests.py)."""
    key: str                # save-file / CLI identity ("hideout", "barrow")
    level: int              # the site's difficulty/pay level
    rooms: tuple[tuple[str, tuple[str, ...]], ...]  # (room name, foe kinds)
    quest_line: str         # the QUEST COMPLETE banner
    spawn_phrase: str       # room banner flavor; {n} = foe count
    abandon_line: str       # the sims' walk-away line
    intro: str              # the one-shot opening line

    def encounter_xp(self, streak: int = 1) -> int:
        """Per-encounter pay at streak position k (rpg.site_encounter_xp:
        consecutive same-site encounters without a camp pay on a rising
        multiplier; a camp resets to base)."""
        return site_encounter_xp(self.level, len(self.rooms), streak)

    @property
    def quest_xp(self) -> int:
        return site_clear_xp(self.level, len(self.rooms))

    @property
    def quest_gold(self) -> int:
        return site_gold(self.level)


# The set room layouts -- the first difficulty lever (develop.md "Balance /
# tuning"). Edit these here; every consumer (one-shot, session, tune, bench)
# reads the same tables.
# 2026-07-09: an archer joined the den (5 -> 6 bandits). The pain-2 regear
# (heroes and humanoids alike feel wounds at half rate -- see rpg.HERO_PAIN)
# made the old layout ~72% clear; the sixth bandit puts the starter back on
# the designer's ~55-60% target with someone hitting the floor in about half
# the runs.
HIDEOUT_ROOMS = (
    ("the lookout post", ("cutthroat",)),
    ("the common room", ("cutthroat", "archer")),
    ("the boss's den", ("bruiser", "cutthroat", "archer")),
)
BARROW_ROOMS = (
    ("the collapsed entry", ("skeleton",) * 3),
    ("the ossuary", ("skeleton",) * 3),
    ("the burial vault", ("skeleton",) * 4),
)

SITES = {
    "hideout": Site(
        key="hideout",
        level=1,        # the starter site: a clear is exactly the L1->2 cost
        rooms=HIDEOUT_ROOMS,
        quest_line="the hideout is broken",
        spawn_phrase="{n} bandits",
        abandon_line="the hideout is left be.",
        intro="The party slips into the bandit hideout:",
    ),
    "barrow": Site(
        key="barrow",
        level=3,        # the tough site: level-3 pay a fresh party can see
                        # on the board and reach for anyway
        rooms=BARROW_ROOMS,
        quest_line="the barrow is cleansed",
        spawn_phrase="{n} skeletons rise from the bones",
        abandon_line="the barrow is abandoned.",
        intro="The party descends into the barrow:",
    ),
}

# Every fixed Weapon instance by name -- the save file (session.py) stores a
# hero's or foe's armament as a name reference into this index, so save.json
# stays hand-editable ("weapon": "katana"). Rolled/authored one-off weapons
# would serialize in full; nothing creates those yet.
WEAPON_INDEX: dict[str, Weapon] = {
    **WEAPONS, **NATURAL_WEAPONS,
    RUSTED_BLADE.name: RUSTED_BLADE, BARROW_BLADE.name: BARROW_BLADE,
}


# --------------------------------------------------------------------------- #
# The generic site runner (one-shot + batch sims)
# --------------------------------------------------------------------------- #

def run_site(site: Site, party: list[Entity], clock: Clock, purse: Purse,
             rng: random.Random, log: list[str], *,
             verbose_rosters: bool = True, reckless: bool = False,
             rooms=None, auto_train: bool = True) -> None:
    """Run a site start to finish under the batch-sim policies (sim_fight
    answers pauses via sim_pause_policy; a fled room gets one return trip).
    Session play shares the same engine and tables but the PLAYER answers the
    pauses -- see session.py.

    `rooms` overrides the site's layout (tune.py's sweep knob).
    reckless=True is the no-resource baseline: no pauses (so no drinks,
    conversions, or retreats) and no potions drunk at rests -- short rests
    still happen (pacing, not a consumable).
    auto_train=False leaves banked skill points alone (bench_quests's career
    sim allocates them itself, reference-style, instead of the greedy
    training-only spend)."""
    rooms = site.rooms if rooms is None else rooms
    count = 0
    cleared_all = True
    room_i = 0
    attempts = 0
    streak = 0      # encounters cleared here since the last night's camp
                    # (the momentum multiplier's k; long_rest resets it)
    held_over: list[Entity] | None = None   # survivors of a room the party fled
    while room_i < len(rooms):
        room_name, roster = rooms[room_i]
        living = [h for h in party if not h.dead]
        if not living:
            cleared_all = False
            break

        log.append("")
        if held_over is None:
            attempts = 1
            spawn = site.spawn_phrase.format(n=len(roster))
            log.append(f"=== Room {room_i + 1}: {room_name} ({spawn}) ===")
            foes = []
            for kind in roster:
                count += 1
                foes.append(make_foe(kind, count, rng))
            if verbose_rosters:
                for line in roster_lines(foes):
                    log.append("  " + line)
        else:
            attempts += 1
            foes = held_over
            held_over = None
            standing = sum(1 for f in foes if f.alive)
            log.append(f"=== Room {room_i + 1}: {room_name}, again -- "
                       f"{standing} foe(s) still hold it ===")
        for h in living:
            start_fight(h, log)

        result = sim_fight(living, foes, rng, log, reckless=reckless)

        if party_wiped(party, log):
            cleared_all = False
            break
        if result == "fled":
            if attempts >= SIM_MAX_ROOM_ATTEMPTS:
                log.append(f"  The party has had enough -- {site.abandon_line}")
                cleared_all = False
                break
            # Rest up and go back in (the sims' determined-player policy):
            # a short rest if a slot is left today, else camp overnight.
            day_before = clock.day
            survivors = [h for h in party if h.alive]
            if not short_rest(survivors, clock, log):
                long_rest(party, clock, log)
                streak = 0      # a night's camp breaks the momentum streak
            auto_use_potions_on_rest([h for h in party if h.alive], log)
            held_over = refresh_foes_after_retreat(foes,
                                                   clock.day - day_before)
            continue    # the same room, again
        if any(f.alive for f in foes):
            # Unresolved (the fight staggered apart): no award, no clear.
            log.append("  The room is not cleared -- the party pulls back.")
            cleared_all = False
            break

        streak += 1
        award_xp(party, site.encounter_xp(streak), log,
                 "encounter" if streak == 1 else f"encounter, streak {streak}")
        roll_loot(party, purse, rng, log)

        survivors = [h for h in party if h.alive]
        if survivors:
            log.append(f"  Room cleared. {len(survivors)} still standing.")
            short_rest(survivors, clock, log)
            if not reckless:
                auto_use_potions_on_rest(survivors, log)  # sim: sensible party
        room_i += 1

    if cleared_all and any(not h.dead for h in party):
        award_quest(party, purse, site.quest_gold, site.quest_xp,
                    log, site.quest_line)
        if auto_train:
            for h in party:
                if not h.dead:
                    train_combat(h, log)    # sim policy: auto-spend on training


# --------------------------------------------------------------------------- #
# One-shot entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", choices=sorted(SITES), default="barrow")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--training", type=int, default=0,
                    help="start the party at this combat-training rank")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    site = SITES[args.site]

    party = make_party(rng)
    for h in party:
        h.training = args.training
    clock = Clock()
    purse = Purse()
    log = [f"Day {clock.day}. {site.intro}"]
    for h in party:
        log.append("  " + stat_line(h))

    run_site(site, party, clock, purse, rng, log)
    # No auto-night: making camp (long_rest) is a deliberate call Claude makes
    # between adventuring days, not something the site loop does on its own.

    log.append("")
    dead = [h for h in party if h.dead]
    alive = [h for h in party if not h.dead]
    log.append(f"OUTCOME: {outcome(party)} of the party died. "
               f"Purse: {purse.gold} gold.")
    if dead:
        log.append("  Fallen:   " + ", ".join(h.name for h in dead))
    if alive:
        log.append("  Survived: " + ", ".join(
            f"{h.name} (L{h.level}, HP {h.hp}/{h.max_hp}, "
            f"Power {h.cur_power}/{h.power}, STA {h.cur_sta}/{h.sta})"
            for h in alive))

    print("\n".join(log))


if __name__ == "__main__":
    main()
