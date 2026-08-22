# RPG2 — Fiction and Content Style

This is the shared writing guide for RPG2. Read it when running the game and
when writing or generating fictional content: quests, places, encounters,
NPC hooks, item names, event lines, and epilogues.

This guide governs **words inside the game**. `dm.md` still owns play protocol,
pacing, and how much prose surrounds a script display. `develop.md` still owns
development communication, which should be thorough. A long design report may
explain a short quest line; the quest line itself still follows this guide.

## The target voice

RPG2 uses the **shared cultural memory of a retro text RPG**, not a strict
imitation of one game. Its backbone is the parser-adventure narrator: second
person, present tense, terse, spatial, and dry. Its accent is the old battle
announcer and system message: abrupt events, strong verbs, compact labels, and
an occasional exclamation mark when something actually happens.

The desired composite feels immediately familiar even when the reader cannot
name its sources:

- **World voice:** "You are at the old mill. The wheel has stopped. Two
  raiders watch the bridge."
- **Event voice:** "A troll draws near!" / "The IRON KEY is yours."
- **Command voice:** `> OPEN THE GATE`

These are three uses of one vocabulary, not three competing styles. The world
voice supplies most of the prose. Event and command voice are accents for
displays and real interaction points; do not turn every sentence into a
catchphrase.

One ranking governs everything below: **plain comes before terse.** "Terse"
and "dry" are instructions about length and restraint, not an invitation to
compress sentences into stylish turns. A longer plain sentence beats a
shorter clever one, every time.

## The load-bearing rules

- **Scenes address the player as "you," in present tense.** The PC is never a
  third-person protagonist. NPCs and companions are named in third person.
- **Describe the external world, not the player's interior.** State what is
  present, visible, audible, or changed. Do not assign thoughts, feelings,
  motives, awe, or fear to the player.
- **Use short declarative sentences and concrete nouns.** Prefer "The gate is
  shut" to "The imposing portal appears to have been sealed against you."
- **Put the useful fact first.** Name the place, obstacle, creature, object, or
  result before adding color. One strong detail is better than a paragraph of
  atmosphere.
- **Name the subject the first time it appears.** "Something in the factory came
  loose" withholds the one fact the sentence exists to carry. Say what it is: a
  cutting machine tore loose, killed two men, and is still running. The game does
  not do mystery for atmosphere -- when the job is called The Killer Machine, the
  prose says machine. "Something", "a shape", "a presence" are only honest when
  the characters genuinely cannot see the thing yet AND finding out is the scene
  the player is about to play.
- **Every invented detail must be readable on sight.** Concrete is not the same
  as technical. "It came off its bed-plates" gives the reader a term they cannot
  picture, cannot act on, and did not ask for -- noise wearing the costume of
  specificity. Use the plain verb (broke loose, tore free, went through the
  wall), and spend the one detail you get on something that changes the scene:
  what it did, what it is doing now, what stands between it and the player.
- **State; do not perform.** The narrator does not joke, wink, editorialize,
  foreshadow, sell the drama, or show off a voice. Dryness comes from restraint,
  not from clever asides.
- **Keep lore local and actionable.** A proper noun earns its place by changing
  what is here or what can be done now. Avoid lore dumps and history written
  only to make the world sound old.
- **Use familiar words without apology.** Gate, sword, witch, barrow, troll,
  king, road, and ruined tower are strengths. Specific arrangement makes them
  memorable; ornamental synonyms do not.
- **Use CRPG vocabulary, not period vocabulary.** Prefer sheriff, village,
  agent, and judge to reeve, parish, factor, and justiciar. Familiar fantasy
  words are useful; rare historical terms make the player stop and translate.
- **Say the job and result literally.** Do not hide the actor or action behind
  metonymy: "The priest pays you to destroy them" is clearer than "the parish
  purse opens." Epilogues state what changed and stop; they do not add a clever
  final beat merely to give the line flavor.
- **Keep game output ASCII, and fit display copy to 40 columns.** The width
  limit is for displays -- code-authored output and DM-composed blocks, where
  a broken line ruins a table; on the scene page (`dm.md`) each display sits
  in a code fence that preserves its shape. Narration prose is never
  hard-wrapped: plain paragraphs, reflowed by the reader's screen. Markdown
  in the DM's prose is structure only -- turn headings, the input quote,
  fences, links -- never bold or italics for emphasis; the voice does the
  emphasis.

## Plain English first (2026-08-08)

The narrator's persistent failure mode is not purple prose. It is literary
compression: the crafted opener, the figure of speech standing in for a
fact, the place or abstraction doing a person's action. Each sentence looks
short and confident, but the player has to translate it to learn what
happened, and a page of them reads as a voice performing. These pairs were
collected from real play; the left column is the failure:

    Avoid: Two days on the road and
      nothing on it.
    Use:   Two days on the road;
      nothing out of the ordinary
      happens.

    Avoid: Byzantium arrives as vineyards
      before it arrives as a city.
    Use:   You reach the forests of
      Byzantium, and then the city.

    Avoid: You come in with the rain
      going sideways.
    Use:   You come in through the
      gate in heavy rain.

    Avoid: Erevan has the worse
      problem and says so straight.
    Use:   Erevan, the council's
      wizard, also has a problem:

    Avoid: ...one of them paying in
      steel.
    Use:   ...one of them offers a
      zweihander as the reward.

    Avoid: The rest of the porch is
      out of your weight entirely.
    Use:   The rest of the posted
      jobs are far above your level.

    Avoid: Word on the porch also
      runs to work elsewhere in the
      land.
    Use:   Some jobs mean travel to
      other settlements.

    Avoid: A storm has held the land
      since yesterday.
    Use:   There has been a storm
      since yesterday.

**The translation test.** Read the sentence word by word. If what it
literally says is not what happened, write what happened instead. "The job
pays in steel" literally describes coins; the fact is a weapon offered as a
reward, so the sentence says that. The test does not forbid strong verbs or
short sentences -- it forbids sentences the reader must decode.

The forms to catch:

- **A non-actor as the subject.** Cities do not arrive, word does not run,
  purses do not open, a porch does not offer work. A person does something,
  or a thing is somewhere; write it that way.
- **Metonymy.** "Steel" for a weapon, "the porch" for the people on it,
  "blades" for fighters: name the thing itself.
- **The crafted opener.** A first line built as a turn of phrase instead of
  a statement of fact.
- **Idiom as intensity.** "Rain going sideways" is an idiom doing the work
  of "heavy rain"; use the plain words.
- **The narrator describing delivery.** "Says so straight", "does not mince
  words": performance notes about a speech the reader can read themselves.
  Give the speech or the fact.

When a line trips the test, do not polish it -- replace it with the plain
statement, even if the result is longer and less striking. The target
register is a walkthrough, not a novel: plain first, short second.

**When in doubt, err toward too naive** (2026-08-08, designer directive).
A flat, simple, almost childlike sentence is closer to the target than one
that reads as good writing. The style can afford to be boring; it cannot
afford to need translating.

## The three writing layers

### 1. World and scene prose

Write like a parser adventure reporting a game state. Establish where the
player is, what stands out, and what has changed or blocks the way. Two or
three sentences usually suffice at a scene change; one sentence keeps place
alive between changes.

Spatial facts beat mood. "Rain runs down the milestone. The north road is
flooded" gives weather and a decision. "A mournful rain lends the road an air
of foreboding" gives neither.

Sensory facts are welcome when concrete: a bell rings behind the wall; smoke
comes through the floorboards; the cellar smells of lamp oil. Similes,
cinematic metaphors, and atmosphere piled for its own sake are not.

### 2. Events, battles, and system displays

Use abrupt subject-verb-result lines. A display should read in a glance and
sound like the game itself speaking:

    A grave troll draws near!
    Meriele deals 4 dmg!!
    TROLL SLAIN
    IRON KEY obtained.

ALL CAPS marks headers, state changes, important items, or a monster treated
as a game token. It does not capitalize every fantasy proper noun. Exclamation
marks belong to arrivals, discoveries, victories, and other discrete events;
they do not make ordinary narration excited. Repetition weakens both devices.

Use `>` only when presenting an actual command, input, or selectable action.
Do not append a fake prompt to ordinary narration merely to look retro.

Displays own numbers and rules. Fiction names what happens; it does not hide a
level, modifier, or resource count inside a metaphor.

### 3. Authored and generated content

Quest templates, place records (areas, sites, and rooms), NPC hooks, items,
and epilogues use the same plain vocabulary and hard edges even when they are
not written in second person. They are **game pieces, not miniature short
stories**. Each should
give the DM material that becomes a clear scene and gives the player something
to act on.

For a **quest**, establish:

1. a concrete problem already happening;
2. who wants it changed and why;
3. a visible objective; and
4. one complication or memorable material detail at most.

Titles should be short and noun-heavy. Descriptions and giver pitches should
name the job instead of teasing it. Epilogues state the changed result in one
beat. Do not write a mystery unless discovering the answer is genuinely part
of play.

For a **place**, start with an ordinary, legible kind, then give it one defining
feature and one current condition: who holds it, what is broken, what moves
there, or which way remains open. Respect the spatial scale: an area establishes
the broad destination, a site adds a landmark or function, and a room adds an
immediate obstacle or affordance. Never repeat the parent as filler (“forest
site,” “forest room”). Build a place the player can navigate, not a vista the
narrator can admire.

When improvising a place name, follow the COUNTRY the scene is in -- there
are nine and each keeps its own sound. "The nine name sounds" below is the
standing table. Retain a plain English type noun when it makes the place
immediately legible: the mill at Ashenden, the Dubki crossing, Ain Zafra's
well.

For a **person**, lead with role and immediate intent. Add one visible or
behavioral marker that can recur. A COMPANION's generated traits are
prompts for conduct, not invitations to write a biography or a speech
about the trait. Everyone else -- givers, notables, keepers, the marks --
comes with a role and no sketch (2026-08-05): invent only the marker the
scene needs, and keep it if they come back.

For an **item or creature**, prefer a readable base noun plus one meaningful
modifier: rust blade, ember hound, glass key, tollhouse ghost. Stack modifiers
only when each one matters in play.

For a **wound** (`rpg.WOUND_NAMES` / `WOUND_MAIM_NAMES`), name the
injury the way a field surgeon would write it down: **body part, what was done
to it, and its current state**, in that order, with no adjective of feeling. "A
gut wound, still seeping" and "two fingers gone" are the register; "a searing
agony in his side" and "a wound that would trouble him for years" are not. The
name is a durable game object — it is printed on the sheet for as long as the
wound lasts, and it is what lets the DM refer back to an injury sessions later
— so it must stay true after fifty readings and must fit the 40-column
display. A **maiming** loses the clinical detail and becomes a plain fact about
the body: "a blind eye", "a withered arm". Severity 1 is a cut, severity 3 is a
thing the character now lives with; say which without reaching for intensity
words.

## The nine name sounds (the standing brief, 2026-08-22)

Each of the nine countries keeps its own name pools, for settlements and for
people both -- a name is the most country-shaped thing in the game, and two
countries can share a card deck without sharing a syllable. When you invent
one, match the row of the country the party is standing in. **These are
invented sounds, not claims about any real language.** ASCII only.

| country | place sound | example places | person sound | example people |
|---|---|---|---|---|
| Phyrascia | English/Anglo-Saxon compounds off real roots: -ham, -ford, -worth, -den, -mere, -minster; hamlets take -cot, -stead, -hay, -croft | Ashenden, Cranmere, Osbridge, Hazelcot | Anglo-Saxon and medieval English | Alfred, Godwin, Edith, Mildred |
| Seraptania | French: Mont-, Val-, -ville, -court, -nay, -bois | Montclaire, Fontenoy, Gournay, Petitbois | French | Thierry, Amaury, Alienor, Blanche |
| Teutonia | German compounds: -bach, -feld, -heim, -hof, -stein, -wald | Eberfeld, Grunbach, Dornhof, Steinkot | German | Konrad, Dietrich, Adelheid, Greta |
| Vellisclavia | old Slavic: -grad, -ov, -ka, -no, Bere-, Dubr- | Novgrad, Chernov, Berezno, Dubki | old Slavic and Rus | Bogdan, Vsevolod, Ludmila, Milena |
| Thule | old Norse: -vik, -fjord, -stad, -ness, -holm, -dal, -by | Eldvik, Kvalfjord, Arnavik, Naustby | old Norse | Orm, Ketil, Astrid, Sigrun |
| Byzantium | Latin, the empire's own tongue: -um, -ia, -anum for estates, -etum for orchards; hamlets take true diminutives -ulus, -ula | Castranova, Fontanum, Olivetum, Viculus | LATIN: the empire names its people in the church's tongue | Cassius, Aurelius, Livia, Claudia |
| Andalusia | Spanish: Castel-, Monte-, Fuente-, -ares, -uelo | Castelmar, Monteclaro, Olivares, Pozuelo | Spanish | Alvaro, Rodrigo, Beatriz, Ines |
| Umaia | Arabic construct pairs: Bir-, Wadi-, Ras-, Ain-, Dar-, Kefr-, Al- | Bir Hakla, Ain Zafra, Dar Aziza | Arabic | Harun, Yusuf, Zaynab, Layla |
| Tergal | steppe and clan words, often hyphenated: -gal, -khar, -run, -tai | Ulus-Gal, Kharuk, Aradun, Ukhta | short, hard, guttural | Gruk, Marok, Baggi, Kansif |

Two things the table does not cover:

- **The towns already have real names** (2026-08-22). Every tile that can
  seat a town or a city carries an authored one -- York, Rouen, Cologne,
  Krakow, Novgorod, Milan, Naples, Thessalonica, Gharnata, Alexandria,
  Damascus, Fez, Sarai, Kaffa and 150 more -- and the script prints it. The
  table is for what you invent BELOW that: villages, hamlets, farms, mills,
  inns, ruins and the people in them. Never rename a town the script named,
  and do not read a town's position as a claim about the real map.
- **The tongues are not the name pools.** Who can talk to whom is a separate
  rule and lives in `dm.md` ("The tongues at the table").

## Tone and comedy

The world is light-handed fantasy with room for cartoon villainy, pratfall
evil, and large archetypes — and, on the same shelf, for named wounds, crime
that pays, debt, hunger, and a king who has not eaten in a week. Keep the
range of material as wide as possible: vivid and specific beat safe and
generic, and no tone rule in this guide is license to cut or soften a fact
the game rolled (2026-08-06 directive; worldsim.md's range doctrine is the
companion piece). The comedy lives in the **material**: raiders collecting a
bridge toll, Hell sending a polite audit, a necromancer whose dead will not
follow instructions. The sentence reports the fact straight. No punchline,
wink, or knowing comparison is required.

What the game never becomes is grimdark in DELIVERY. Dark material is in
range; wallowing is not. Consequences remain concrete. A village burns, a
companion dies, a tyrant wins, the rumor says the old duke tried to hang
himself — without the prose becoming solemn, gruesome, or portentous. Flat
delivery does not erase the event; it trusts the event. Restraint governs
how a line is written, never which facts may exist.

## Examples

**Place**

Avoid:

> Moonlight spills like silver across the melancholy bones of an ancient
> mill, whose groaning wheel seems to whisper of forgotten tragedies.

Use:

> You are at the old mill. The wheel turns, but the stream is dry. Someone is
> inside.

**Naming the thing**

Avoid:

> Something in the lower factory came off its bed-plates two nights ago and
> started walking.

Use:

> A cutting machine tore loose in the lower factory two nights ago. It has
> killed two men. It is still running.

**Quest**

Avoid:

> Unravel the sinister mystery lurking in the shadow-haunted tollhouse before
> its dark legacy consumes the countryside.

Use:

> **Raiders at the Tollhouse**
>
> The tollkeeper is missing. Raiders collect the road tax now. Bring back his
> brass key.

**Comic material**

Avoid:

> In a display of infernal bureaucracy that would almost be funny if it were
> not so ominous, Hell has apparently decided to audit you.

Use:

> A clerk from Hell waits outside your room. He has three forms and no weapon.

**A full page.** `scene-example.md` shows this voice at message length -- a
game start and a fight turn, in the scene-page format `dm.md` specifies. When
a line will not come out right, find its nearest neighbor there and imitate
it.

## Final check

Before shipping a line of fiction, ask:

- Can the reader picture the concrete game state on the first read?
- Does every sentence pass the translation test (Plain English first): a
  literal subject, a literal verb, nothing the reader must decode?
- Is every subject named outright rather than withheld, and can the reader
  picture each invented detail without being told what it means?
- Does the line tell them something present, changed, or actionable?
- Is the player still free to decide what "you" think and feel?
- Is the humor or drama in the event rather than the narrator's performance?
- Could one adjective, sentence, proper noun, or lore clause be removed?
- If it is a display, is it legible at 40 columns and is its emphasis earned?

If yes, it belongs in RPG2.
