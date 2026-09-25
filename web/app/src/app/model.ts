/**
 * The documents of the player's page, as they live in the artifact's `db` store.
 *
 *   game/state, game/party, game/map, game/quests, game/record
 *                    singletons the keeper writes (page.py, player_view)
 *   chronicle/tNNNN  one DM turn each, written once (page.py, chronicle_entry)
 *   fights/fNNNN     one fight each, or a paused fight's second half,
 *                    written once (page.py, keep_fight / fight_doc)
 *   moves/mNNNN      one player move each, written by this page
 *
 * The contract is web/README.md, The documents. Every document arrives from another
 * writer and is untrusted: each is read field by field with a fallback, so one
 * malformed document cannot blank the page. Parse, never cast.
 */

export const SCHEMA_VERSION = 1;

export const PATHS = {
  state: 'game/state',
  party: 'game/party',
  map: 'game/map',
  quests: 'game/quests',
  record: 'game/record',
  chronicle: 'chronicle',
  fights: 'fights',
  moves: 'moves',
} as const;

// ------------------------------------------------------------------ game/state
export type Status = 'awaiting_player' | 'dm_thinking' | 'ended';
export type Over = 'wiped' | 'pc_dead';

/** One hero's row in the pause menu. */
export interface PauseHero {
  name: string;
  down: boolean;
  hpState: string;
  hp: number;
  hpCeiling: number;
  maxHp: number;
  sta: number;
  staMax: number;
  power: number;
  powerMax: number;
  penalties: string;
  conditions: string[];
  wounds: string[];
  healing: number;
  stamina: number;
}

/** One line of the pause menu: a choice, and who may take it right now. */
export interface PauseOption {
  choice: string;
  label: string;
  cost: string;
  /** An action's heroes: the names that pass the checker now. */
  heroes: string[];
  /** blink and smoke: the one hero the menu names. */
  hero: string | null;
}

/** The fight paused: the menu as data, and as printed. */
export interface Pause {
  /** The published fight that paused; null while it waits unpublished. */
  fight: string | null;
  round: number;
  kind: 'normal' | 'fate';
  trips: string;
  facing: { name: string; hp: number; maxHp: number }[];
  party: PauseHero[];
  options: PauseOption[];
  text: string[];
}

export interface LevelUp {
  hero: string;
  points: number;
  text: string[];
}

export interface GameState {
  v: number;
  status: Status;
  /** Highest move seq the keeper has answered. The handshake. */
  lastSeq: number;
  day: number;
  /** "Umaia > R17C11 > Dar Aziza" */
  where: string;
  coord: string;
  land: string;
  /** The id of the newest chronicle entry ("t0007"), or null before the first. */
  latest: string | null;
  /** The id of the newest fight ("f0003"), or null before the first. */
  lastFight: string | null;
  /** When the DM next looks: an ISO time, or words. */
  checkIn: string | null;
  over: Over | null;
  pause: Pause | null;
  levelUp: LevelUp | null;
}

export function readState(raw: unknown): GameState | null {
  const r = obj(raw);
  if (!r) return null;
  const over = r['over'] === 'wiped' || r['over'] === 'pc_dead' ? r['over'] : null;
  return {
    v: num(r['v'], SCHEMA_VERSION),
    status: over ? 'ended' : oneOf(r['status'], ['awaiting_player', 'dm_thinking', 'ended'], 'awaiting_player'),
    lastSeq: num(r['lastSeq'], 0),
    day: num(r['day'], 0),
    where: str(r['where']),
    coord: str(r['coord']),
    land: str(r['land']),
    latest: str(r['latest']) || null,
    lastFight: str(r['lastFight']) || null,
    checkIn: str(r['checkIn']) || null,
    over,
    pause: readPause(r['pause']),
    levelUp: readLevelUp(r['levelUp']),
  };
}

function readPause(raw: unknown): Pause | null {
  const r = obj(raw);
  if (!r) return null;
  return {
    fight: str(r['fight']) || null,
    round: num(r['round'], 0),
    kind: oneOf(r['kind'], ['normal', 'fate'], 'normal'),
    trips: str(r['trips']),
    facing: objs(r['facing'], 40).map((f) => ({ name: str(f['name']), hp: num(f['hp'], 0), maxHp: num(f['maxHp'], 0) })),
    party: objs(r['party'], 12).map((h) => ({
      name: str(h['name']),
      down: h['down'] === true,
      hpState: str(h['hpState']),
      hp: num(h['hp'], 0),
      hpCeiling: num(h['hpCeiling'], 0),
      maxHp: num(h['maxHp'], 0),
      sta: num(h['sta'], 0),
      staMax: num(h['staMax'], 0),
      power: num(h['power'], 0),
      powerMax: num(h['powerMax'], 0),
      penalties: str(h['penalties']),
      conditions: strs(h['conditions']),
      wounds: strs(h['wounds']),
      healing: num(h['healing'], 0),
      stamina: num(h['stamina'], 0),
    })),
    options: objs(r['options'], 20).map((o) => ({
      choice: str(o['choice']),
      label: str(o['label']) || str(o['choice']).replace('_', ' '),
      cost: str(o['cost']),
      heroes: strs(o['heroes']),
      hero: str(o['hero']) || null,
    })),
    text: lines(r['text']),
  };
}

function readLevelUp(raw: unknown): LevelUp | null {
  const r = obj(raw);
  const hero = r && str(r['hero']);
  if (!r || !hero) return null;
  return { hero, points: num(r['points'], 0), text: lines(r['text']) };
}

// ------------------------------------------------------------------ game/party
export interface Member {
  name: string;
  nickname: string;
  isPc: boolean;
  homeland: string;
  sex: string;
  age: number;
  level: number;
  training: number;
  xp: number;
  xpNext: number;
  points: number;
  dex: number;
  str: number;
  mind: number;
  cha: number;
  hp: number;
  hpCeiling: number;
  maxHp: number;
  hpState: string;
  sta: number;
  staMax: number;
  power: number;
  powerMax: number;
  weapon: string;
  /** Item name -> count, only what is carried. */
  kit: Record<string, number>;
  /** Spell -> rank. */
  spells: Record<string, number>;
  abilities: string[];
  moves: string[];
  alchemy: number;
  /** A companion's satisfaction; null for the player's own hero. */
  satisfaction: number | null;
  traits: string[];
  blood: string;
  tongues: string;
  conditions: string[];
  wounds: string[];
  woundLoad: number;
  dead: boolean;
  down: boolean;
  quitting: boolean;
  /** hero_block_lines, 40-column wrapped: the sheet as printed. */
  text: string[];
}

export interface PartyDoc {
  v: number;
  day: number;
  purse: number;
  slots: { filled: number; cap: number; cha: number };
  members: Member[];
  /** The sheet's tail: the active quest, sin, the pact, a paused fight. */
  status: string[];
  /** party_sheet_lines, wrapped: the whole ui/party.txt. */
  text: string[];
}

export function readParty(raw: unknown): PartyDoc | null {
  const r = obj(raw);
  if (!r) return null;
  const slots = obj(r['slots']) ?? {};
  return {
    v: num(r['v'], SCHEMA_VERSION),
    day: num(r['day'], 0),
    purse: num(r['purse'], 0),
    slots: { filled: num(slots['filled'], 0), cap: num(slots['cap'], 0), cha: num(slots['cha'], 0) },
    members: arr(r['members']).map(readMember).filter((m): m is Member => !!m).slice(0, 12),
    status: lines(r['status']),
    text: lines(r['text']),
  };
}

export function readMember(raw: unknown): Member | null {
  const r = obj(raw);
  const name = r && str(r['name']);
  if (!r || !name) return null;
  return {
    name,
    nickname: str(r['nickname']),
    isPc: r['isPc'] === true,
    homeland: str(r['homeland']),
    sex: str(r['sex']),
    age: num(r['age'], 0),
    level: num(r['level'], 1),
    training: num(r['training'], 0),
    xp: num(r['xp'], 0),
    xpNext: num(r['xpNext'], 0),
    points: num(r['points'], 0),
    dex: num(r['dex'], 0),
    str: num(r['str'], 0),
    mind: num(r['mind'], 0),
    cha: num(r['cha'], 0),
    hp: num(r['hp'], 0),
    hpCeiling: num(r['hpCeiling'], num(r['maxHp'], 0)),
    maxHp: Math.max(1, num(r['maxHp'], 1)),
    hpState: str(r['hpState']),
    sta: num(r['sta'], 0),
    staMax: num(r['staMax'], 0),
    power: num(r['power'], 0),
    powerMax: num(r['powerMax'], 0),
    weapon: str(r['weapon']),
    kit: numbers(r['kit']),
    spells: numbers(r['spells']),
    abilities: strs(r['abilities']),
    moves: strs(r['moves']),
    alchemy: num(r['alchemy'], 0),
    satisfaction: isNum(r['satisfaction']) ? r['satisfaction'] : null,
    traits: strs(r['traits']),
    blood: str(r['blood']),
    tongues: str(r['tongues']),
    conditions: strs(r['conditions']),
    wounds: strs(r['wounds']),
    woundLoad: num(r['woundLoad'], 0),
    dead: r['dead'] === true,
    down: r['down'] === true,
    quitting: r['quitting'] === true,
    text: lines(r['text']),
  };
}

// ------------------------------------------------------------------ game/map
/** A place the party knows: a settlement slot, or one of the four gates. */
export interface MapPlace {
  coord: string;
  name: string;
  /** "village" ... "metropolis", "gate ruin", "gate city". */
  kind: string;
  land: string;
  capital: boolean;
}

export interface MapDoc {
  v: number;
  day: number;
  /** The party's cell, "R17C10". */
  coord: string;
  /** The grid's base glyphs, a row a string, with no party and no job marks. */
  rows: string[];
  /** The cells of the jobs in hand's sites. */
  objectives: string[];
  /** [glyph, word] pairs, map.txt's legend. */
  legend: [string, string][];
  places: MapPlace[];
  here: string[];
  land: { name: string; lines: string[] };
  known: string[];
  holdings: string[];
  /** map_sheet_lines, wrapped: the whole ui/map.txt. */
  text: string[];
}

export function readMap(raw: unknown): MapDoc | null {
  const r = obj(raw);
  if (!r) return null;
  const land = obj(r['land']) ?? {};
  return {
    v: num(r['v'], SCHEMA_VERSION),
    day: num(r['day'], 0),
    coord: str(r['coord']),
    rows: lines(r['rows']).slice(0, 60).map((row) => row.slice(0, 60)),
    objectives: strs(r['objectives']).slice(0, 40),
    legend: arr(r['legend'])
      .filter((p): p is [string, string] => Array.isArray(p) && typeof p[0] === 'string' && typeof p[1] === 'string')
      .map((p) => [p[0], p[1]] as [string, string])
      .slice(0, 30),
    places: objs(r['places'], 600).map((p) => ({
      coord: str(p['coord']),
      name: str(p['name']),
      kind: str(p['kind']),
      land: str(p['land']),
      capital: p['capital'] === true,
    })).filter((p) => p.coord && p.name),
    here: lines(r['here']),
    land: { name: str(land['name']), lines: lines(land['lines']) },
    known: lines(r['known']),
    holdings: lines(r['holdings']),
    text: lines(r['text']),
  };
}

/** "R17C10" for a 0-based row and column, as places.tile_coordinate writes it. */
export function cellCoord(row: number, col: number): string {
  return `R${String(row + 1).padStart(2, '0')}C${String(col + 1).padStart(2, '0')}`;
}

// ------------------------------------------------------------------ game/quests
export type QuestStatus = 'open' | 'work_done' | 'proof_pending';

export interface QuestSite { name: string; level: number; mark: string; }

export interface Quest {
  id: string;
  name: string;
  level: number | null;
  kind: 'delivery' | '';
  origin: string;
  status: QuestStatus;
  sites: QuestSite[];
  /** The first road line: "R17C10: here", "R16C12: 2 days". */
  road: string;
  /** The day it is wanted by; null for no deadline. */
  due: number | null;
  /** "5 days left", "late -- ...": the deadline in words. */
  note: string;
  cargo: string | null;
  dest: string | null;
  /** The job as the map page prints it. */
  lines: string[];
}

export interface QuestsDoc {
  v: number;
  /** The active job's id, or null. */
  active: string | null;
  quests: Quest[];
}

export function readQuests(raw: unknown): QuestsDoc | null {
  const r = obj(raw);
  if (!r) return null;
  return {
    v: num(r['v'], SCHEMA_VERSION),
    active: str(r['active']) || null,
    quests: objs(r['quests'], 50).map((q) => ({
      id: str(q['id']),
      name: str(q['name']) || str(q['id']),
      level: isNum(q['level']) ? q['level'] : null,
      kind: q['kind'] === 'delivery' ? ('delivery' as const) : ('' as const),
      origin: str(q['origin']),
      status: oneOf<QuestStatus>(q['status'], ['open', 'work_done', 'proof_pending'], 'open'),
      sites: objs(q['sites'], 20).map((s) => ({ name: str(s['name']), level: num(s['level'], 0), mark: str(s['mark']) })),
      road: str(q['road']),
      due: isNum(q['due']) ? q['due'] : null,
      note: str(q['note']),
      cargo: str(q['cargo']) || null,
      dest: str(q['dest']) || null,
      lines: lines(q['lines']),
    })).filter((q) => q.id),
  };
}

// ------------------------------------------------------------------ game/record
export interface RecordLine { day: number; line: string; note: string; }

export interface RecordDoc {
  v: number;
  day: number;
  /** QUESTS DONE, oldest first. */
  quests: RecordLine[];
  /** REMARKABLE, oldest first. */
  remarkable: RecordLine[];
  /** THE TALLY OF SIN, as printed. */
  tally: string[];
  /** SUGGESTIONS: what hell is advertising today. */
  suggestions: { key: string; name: string; line: string }[];
  /** history_sheet_lines, wrapped: the whole ui/history.txt. */
  text: string[];
}

export function readRecord(raw: unknown): RecordDoc | null {
  const r = obj(raw);
  if (!r) return null;
  const rows = (v: unknown) => objs(v, 2000).map((x) => ({ day: num(x['day'], 0), line: str(x['line']), note: str(x['note']) }))
    .filter((x) => x.line);
  return {
    v: num(r['v'], SCHEMA_VERSION),
    day: num(r['day'], 0),
    quests: rows(r['quests']),
    remarkable: rows(r['remarkable']),
    tally: lines(r['tally']),
    suggestions: objs(r['suggestions'], 20).map((x) => ({ key: str(x['key']), name: str(x['name']), line: str(x['line']) }))
      .filter((x) => x.key || x.name),
    text: lines(r['text']),
  };
}

// ------------------------------------------------------------------ moves
export type MoveKind = 'say' | 'ooc' | 'pause';
export const MOVE_KINDS: readonly MoveKind[] = ['say', 'ooc', 'pause'];
export const MOVE_TEXT_MAX = 2000;
export const HERO_NAME_MAX = 40;
export const ACTIONS_MAX = 8;
export const PAUSE_CHOICES = ['fight_on', 'retreat'] as const;
export const PAUSE_ACTIONS = ['drink', 'heal', 'berserk', 'warbreath', 'vanish'] as const;
export const ESCAPES = ['blink', 'smoke'] as const;
export type PauseChoice = (typeof PAUSE_CHOICES)[number];
export type PauseAction = (typeof PAUSE_ACTIONS)[number];
export type Escape = (typeof ESCAPES)[number];

/** What a page sends, before the store gives it a seq (web/README.md, The documents). */
export type MoveBody =
  | { kind: 'say' | 'ooc'; text: string }
  | {
      kind: 'pause';
      fight: string;
      choice: PauseChoice;
      actions?: { hero: string; action: PauseAction }[];
      escape?: Escape;
      hero?: string;
    };

/** A move as stored in `moves/`, or as answered inside a chronicle entry. */
export type Move = MoveBody & { seq: number };

/** `moves/m0007`: zero-padded, so document id order is seq order. */
export function moveId(seq: number): string {
  return 'm' + String(seq).padStart(4, '0');
}

/**
 * A move's body with only the known fields of its kind, trimmed and capped;
 * null when it is not a move. Mirrors page.clean_move (bar the seq, which the
 * store gives): a pause move is whole or nothing, as there.
 */
export function cleanBody(raw: unknown): MoveBody | null {
  const r = obj(raw);
  if (!r) return null;
  const cap = (v: unknown, n: number) => (typeof v === 'string' ? v.trim().slice(0, n) : '');
  const kind = r['kind'];
  if (kind === 'say' || kind === 'ooc') {
    const text = cap(r['text'], MOVE_TEXT_MAX);
    return text ? { kind, text } : null;
  }
  if (kind !== 'pause') return null;
  const choice = r['choice'];
  if (choice !== 'fight_on' && choice !== 'retreat') return null;
  const fight = cap(r['fight'], HERO_NAME_MAX);
  if (choice === 'fight_on') {
    const raw = r['actions'] ?? [];
    if (!Array.isArray(raw) || raw.length > ACTIONS_MAX) return null;
    const actions: { hero: string; action: PauseAction }[] = [];
    for (const a of raw) {
      const o = obj(a);
      const hero = o ? cap(o['hero'], HERO_NAME_MAX) : '';
      const action = o?.['action'];
      if (!hero || !PAUSE_ACTIONS.includes(action as PauseAction)) return null;
      actions.push({ hero, action: action as PauseAction });
    }
    return { kind, fight, choice, actions };
  }
  const escape = r['escape'];
  if (escape === undefined || escape === null) return { kind, fight, choice };
  const hero = cap(r['hero'], HERO_NAME_MAX);
  if (!ESCAPES.includes(escape as Escape) || !hero) return null;
  return { kind, fight, choice, escape: escape as Escape, hero };
}

/** Mirrors page.clean_move: a whole seq of at least 1, and a clean body. */
export function readMove(raw: unknown): Move | null {
  const r = obj(raw);
  if (!r) return null;
  const seq = r['seq'];
  if (typeof seq !== 'number' || !Number.isInteger(seq) || seq < 1) return null;
  const body = cleanBody(r);
  return body ? { ...body, seq } : null;
}

const ACTION_WORDS: Record<PauseAction, string> = {
  drink: 'drinks a stamina draught',
  heal: 'drinks a healing potion',
  berserk: 'goes berserk',
  warbreath: 'draws the war-breath',
  vanish: 'vanishes',
};
const ESCAPE_WORDS: Record<Escape, string> = {
  blink: 'blinks the party out',
  smoke: 'breaks a smoke vial',
};

/** A move in the player's words, as page.move_words says it (the transcript's `>` lines). */
export function moveWords(m: MoveBody): string {
  switch (m.kind) {
    case 'say':
      return m.text;
    case 'ooc':
      return `(to the DM) ${m.text}`;
    case 'pause': {
      if (m.choice === 'fight_on') {
        const said = (m.actions ?? []).map((a) => `${a.hero} ${ACTION_WORDS[a.action]}`);
        return 'At the pause: ' + [...said, 'fight on'].join('; ');
      }
      if (m.escape && m.hero) return `At the pause: retreat -- ${m.hero} ${ESCAPE_WORDS[m.escape]}`;
      return 'At the pause: retreat';
    }
  }
}

// ------------------------------------------------------------------ chronicle/tNNNN
export interface ChronicleEntry {
  v: number;
  id: string;
  turn: number;
  day: number;
  where: string;
  coord: string;
  prose: string;
  /** The player's moves this turn answered, in seq order. */
  answered: Move[];
  /** Ids of the `fights/` documents in this turn, in order. */
  fights: string[];
  /** Each hero's level when the turn was written. */
  levels: Record<string, number>;
  over: boolean;
}

export function readChronicle(raw: unknown, id: string): ChronicleEntry | null {
  const r = obj(raw);
  if (!r) return null;
  const prose = str(r['prose']).trim();
  const turn = num(r['turn'], Number(id.replace(/\D/g, '')) || 0);
  if (!prose || turn < 1) return null;
  return {
    v: num(r['v'], SCHEMA_VERSION),
    id: str(r['id']) || id,
    turn,
    day: num(r['day'], 0),
    where: str(r['where']),
    coord: str(r['coord']),
    prose,
    answered: arr(r['answered'])
      .map((m) => readMove(m))
      .filter((m): m is Move => !!m)
      .sort((a, b) => a.seq - b.seq),
    fights: strs(r['fights']).slice(0, 50),
    levels: numbers(r['levels']),
    over: r['over'] === true,
  };
}

/** Prose to paragraphs: blank lines split them, inner whitespace collapses. */
export function paragraphs(text: string): string[] {
  return text
    .split(/\n\s*\n/)
    .map((p) => p.replace(/\s+/g, ' ').trim())
    .filter(Boolean);
}

export const FIGHT_MARKER = '[fight]';

/** One piece of a DM turn: a paragraph, a fenced display, or a fight in place. */
export type Block =
  | { kind: 'p'; text: string }
  | { kind: 'display'; lines: string[]; options: string[] | null }
  | { kind: 'fight'; id: string };

/**
 * The choices of an `options:` display, or null for any other display. The
 * first line starts `options:` (after trimming); wrapped continuation lines
 * are joined, the prefix cut, and the rest split on ", ". The page turns them
 * into chips that put the words in the answer box and never send them.
 */
export function optionChoices(lines: readonly string[]): string[] | null {
  if (!lines.length || !lines[0].trim().startsWith('options:')) return null;
  const joined = lines.map((l) => l.trim()).filter(Boolean).join(' ').slice('options:'.length);
  const out = joined.split(', ').map((o) => o.trim()).filter(Boolean);
  return out.length ? out.slice(0, 20) : null;
}

/**
 * A turn's prose as blocks. Fenced ``` displays keep their lines verbatim; a
 * line that is exactly `[fight]` (trimmed), outside a fence, with a blank line
 * or the start/end of the prose on both sides is where the turn's next fight
 * goes -- page.fight_markers' rule, to the letter. A marker past the fights is
 * left as written; fights no marker placed follow the prose.
 */
export function proseBlocks(prose: string, fights: readonly string[]): Block[] {
  const lines = prose.split('\n');
  const out: Block[] = [];
  const queue = [...fights];
  let para: string[] = [];
  let display: string[] | null = null;
  const endPara = () => {
    const text = para.join(' ').replace(/\s+/g, ' ').trim();
    if (text) out.push({ kind: 'p', text });
    para = [];
  };
  lines.forEach((line, i) => {
    const t = line.trim();
    if (t.startsWith('```')) {
      if (display) {
        out.push({ kind: 'display', lines: display, options: optionChoices(display) });
        display = null;
      } else {
        endPara();
        display = [];
      }
      return;
    }
    if (display) {
      display.push(line.replace(/\s+$/, ''));
      return;
    }
    if (!t) {
      endPara();
      return;
    }
    const before = i > 0 ? lines[i - 1].trim() : '';
    const after = i + 1 < lines.length ? lines[i + 1].trim() : '';
    if (t === FIGHT_MARKER && !before && !after && queue.length) {
      endPara();
      out.push({ kind: 'fight', id: queue.shift()! });
      return;
    }
    para.push(t);
  });
  if (display) out.push({ kind: 'display', lines: display, options: optionChoices(display) });
  endPara();
  for (const id of queue) out.push({ kind: 'fight', id });
  return out;
}

// ------------------------------------------------------------------ fights/fNNNN
export type Outcome = 'won' | 'lost' | 'unresolved' | 'retreated' | 'paused';
export const OUTCOMES: readonly Outcome[] = ['won', 'lost', 'unresolved', 'retreated', 'paused'];
export type BlockKind = 'opening' | 'rounds' | 'between' | 'closing';

export interface FightBlock {
  kind: BlockKind;
  lines: string[];
}

export interface Fight {
  v: number;
  id: string;
  day: number;
  where: string;
  coord: string;
  title: string;
  outcome: Outcome;
  /** The paused fight this one finishes, or null. */
  continues: string | null;
  /** The highest round named. */
  rounds: number;
  /** The player log exactly, cut at the log's round spans. */
  blocks: FightBlock[];
}

export function readFight(raw: unknown, id: string): Fight | null {
  const r = obj(raw);
  if (!r) return null;
  const blocks = objs(r['blocks'], 200)
    .map((b) => ({ kind: oneOf<BlockKind>(b['kind'], ['opening', 'rounds', 'between', 'closing'], 'between'), lines: lines(b['lines']) }))
    .filter((b) => b.lines.length);
  return {
    v: num(r['v'], SCHEMA_VERSION),
    id: str(r['id']) || id,
    day: num(r['day'], 0),
    where: str(r['where']),
    coord: str(r['coord']),
    title: str(r['title']) || 'a fight',
    outcome: oneOf(r['outcome'], OUTCOMES, 'unresolved'),
    continues: str(r['continues']) || null,
    rounds: num(r['rounds'], 0),
    blocks,
  };
}

/** "won", "lost", "PAUSED after round 3": how a fight stands, in a word or three. */
export function outcomeWords(f: Pick<Fight, 'outcome' | 'rounds'>): string {
  return f.outcome === 'paused' ? `PAUSED after round ${f.rounds}` : f.outcome;
}

/** The colour class of an outcome. */
export function outcomeClass(o: Outcome): string {
  return o === 'won' ? 'won' : o === 'lost' ? 'lost' : o === 'paused' ? 'paused' : 'off';
}

// ------------------------------------------------------------------ helpers
export function num(v: unknown, fallback: number): number {
  return typeof v === 'number' && Number.isFinite(v) ? v : fallback;
}

export function str(v: unknown, fallback = ''): string {
  return typeof v === 'string' ? v : fallback;
}

export function arr(v: unknown): unknown[] {
  return Array.isArray(v) ? v : [];
}

export function obj(v: unknown): Record<string, unknown> | null {
  return v && typeof v === 'object' && !Array.isArray(v) ? (v as Record<string, unknown>) : null;
}

export function strs(v: unknown): string[] {
  return arr(v).filter((x): x is string => typeof x === 'string' && x.length > 0);
}

/** Printed lines: strings kept as they are, blank ones included. */
export function lines(v: unknown): string[] {
  return arr(v).filter((x): x is string => typeof x === 'string').slice(0, 4000);
}

export function objs(v: unknown, max: number): Record<string, unknown>[] {
  return arr(v).map(obj).filter((o): o is Record<string, unknown> => !!o).slice(0, max);
}

export function isNum(v: unknown): v is number {
  return typeof v === 'number' && Number.isFinite(v);
}

export function numbers(v: unknown): Record<string, number> {
  const out: Record<string, number> = {};
  for (const [k, x] of Object.entries(obj(v) ?? {})) if (isNum(x)) out[k] = x;
  return out;
}

export function oneOf<T extends string>(v: unknown, allowed: readonly T[], fallback: T): T {
  return allowed.includes(v as T) ? (v as T) : fallback;
}
