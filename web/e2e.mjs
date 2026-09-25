#!/usr/bin/env node
/**
 * The page played end to end against the fake store, with no claude.ai.
 *
 *   node web/e2e.mjs [--out DIR] [--headed]
 *
 * Needs web/dist (cd web/app && npx ng build && node ../build-artifact.mjs)
 * and a Chromium for playwright-core (PLAYWRIGHT_BROWSERS_PATH, or
 * CHROMIUM=/path/to/chrome). Plays its own game, rolled by `session.py new`
 * into DIR/home (RPG2_HOME), never the one in the repo, with the real
 * session.py, publish.py and page.py:
 *
 *   1. the opening: an opening scene with an options display goes out with
 *      publish.py --all; its batch seeds the fake store (web/dev/serve.mjs)
 *      and the phone shows the prose, the display in mono, the day and the
 *      place in the header, "Your move" and the answer box as the PC; the
 *      options display carries chips, and a chip fills the box and sends
 *      nothing;
 *   2. two moves, one in the game and one to the DM: both wait in the
 *      chronicle, and land in moves/ as m0001 and m0002;
 *   3. the keeper's turn: moves and game/state read with their versions,
 *      page.py moves, publish.py with the turn's prose, the batch posted,
 *      --sent: the new turn shows with the player's words under it, the
 *      queue clears, the same batch twice is refused by its pins, and
 *      ui/transcript.md gained the turn;
 *   4. a fight: session.py fight, kept on its own and published with prose
 *      that places it between two displays: the card sits in place, opens
 *      the Fight tab, whose lines are ui/fight-short.txt exactly, and the
 *      Fights list has it;
 *   5. the party: a card for the PC and the companion, and the whole sheet
 *      as printed is ui/party.txt;
 *   6. a job taken (session.py take): the Map (540 squares, the party's @
 *      on game/state's coord, a tap naming the square, the job's !, the
 *      text map as ui/map.txt, no unknown settlement anywhere in the
 *      store), the Quests card (sites, due day, the job as map.txt prints
 *      it) and the Record (its sections; the history as ui/history.txt);
 *      the Map's unread mark;
 *   7. a level crossed (session.py award): the Party tab's level-up menu,
 *      and "NAME reaches level N." in the chronicle;
 *   8. a paused fight (a foe the save's own dice pause against, found on a
 *      copy of the home): the Fight and More marks, cleared by looking and
 *      remembered over a reload; the picker offering only what the menu
 *      does; a tampered pause move REFUSED by page.py moves and answered
 *      in the fiction; the player's heal and fight on sent from the picker,
 *      printed by page.py moves as the resume command, played, and its
 *      second half published: the picker gone, both halves on the page;
 *   9. the layout: no side scroll at 412 and 360, every display unclipped,
 *      the bottom bar's five thumb-sized buttons; screenshots at phone
 *      (light and dark), small, mid and wide; the marks with storage
 *      blocked;
 *  10. the fallbacks: a read-only viewer, and a page with no db;
 *  11. game over: the PC killed in the save, published --status ended:
 *      data-over, the answer box closed, no picker.
 *
 * Screenshots land in DIR/shots (DIR defaults to a fresh temp directory).
 */
import { execFileSync } from 'node:child_process';
import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { startServer } from './dev/serve.mjs';

const web = dirname(fileURLToPath(import.meta.url));
const repo = resolve(web, '..');
const require = createRequire(join(web, 'app', 'package.json'));
const { chromium } = require('playwright-core');

const args = process.argv.slice(2);
const outArg = args.indexOf('--out');
const out = outArg >= 0 ? resolve(args[outArg + 1]) : await mkdtemp(join(tmpdir(), 'rpg2-e2e-'));
const shots = join(out, 'shots');
const home = join(out, 'home');
await mkdir(shots, { recursive: true });
if (!existsSync(join(web, 'dist', 'index.html'))) {
  console.error('no web/dist: run `cd web/app && npx ng build && node ../build-artifact.mjs` first');
  process.exit(2);
}

// ---------------------------------------------------------------- the story
const OPENING = `You stand in the square at Sidi Farhan, a village of Umaia on the coast road. The well is dry and the market is half set up.

The sheriff, Habiba, stops you at the well. Bandits hold the road north. Two carts are gone this week.

\`\`\`
  job: Bandits on the Road -- L1
  giver: Habiba, the sheriff
\`\`\`

\`\`\`
  options: take the road job, the
    board, the tavern, camp, travel
\`\`\`

What do you do?`;
const MOVE = 'I ask Habiba where the carts were taken, then I walk the road north.';
const QUESTION = 'How far is the next town from here?';
const TURN = `Habiba points up the coast road. "Past the second milestone," she says. "They come out of the olive trees."

The road is quiet. The trees are close on both sides.

(Out of the game: the next town is two days along the coast road.)`;
const TAKEN = `You tell Habiba you will clear the road. She marks the camp on your map.

\`\`\`
  job taken: Bandits on the Road
\`\`\``;
const LEVEL = `Yusuf counts the coin from the last caravan twice. Word of the wolves has gone ahead of you.`;
const REFUSED = `NAME reaches for a flask. There is no such flask in the pack. The fight holds its breath a moment longer.`;
const CONTINUED = `You pull the cork with your teeth and drink.

[fight]

The road is quiet again.`;
const OVER = `The last blow lands. The road goes dark.`;
const FIGHT = `Two wolves come out of the olive trees, low and fast.

\`\`\`
  2x Wolf -- fangs
\`\`\`

[fight]

\`\`\`
  options: go on north, back to
    Sidi Farhan, camp
\`\`\`

The road is clear again.`;

// ---------------------------------------------------------------- the Python helpers
/** The settlement slots the party does not know, bar names public anyway (test_page's rule). */
const UNKNOWN_PLACES = `
import json, session
s = session.load()
w = s["world"]
slots = w["settlement_slots"].values()
public = {x["name"] for x in slots if x["known"]}
public |= {land["name"] for land in w["lands"].values()} | {h.name for h in s["party"]}
print(json.dumps(sorted({x["name"] for x in slots if not x["known"] and x["name"]} - public)))
`;

/**
 * A foe the save's own dice pause the party against, found on copies of
 * RPG2_HOME (the dice live in the save, so the real home repeats the copy):
 * the fight pauses (not at Fate), the PC stands with a healing potion, and
 * resume --heal PC leaves him alive. Prints the fight's argv after "fight".
 */
const PAUSING_FOE = `
import json, os, shutil, subprocess, sys, tempfile
home = os.environ["RPG2_HOME"]
def run(h, *argv):
    env = dict(os.environ, RPG2_HOME=h)
    subprocess.run([sys.executable, "session.py", *argv], env=env, capture_output=True, text=True, check=True)
def load(h):
    with open(os.path.join(h, "save.json")) as f:
        return json.load(f)
for kind in ("troll", "ogre", "bear", "wight", "champion", "giant"):
    for n in ("1", "2"):
        t = tempfile.mkdtemp()
        try:
            shutil.copy(os.path.join(home, "save.json"), t)
            os.makedirs(os.path.join(t, "ui"))
            run(t, "fight", n, "--type", kind)
            s = load(t)
            pc, p = s["party"][0], s.get("pending")
            if not p or p.get("pause_kind") == "fate" or pc["dead"] or pc["down"] or pc["items"].get("healing", 0) < 1:
                continue
            run(t, "resume", "--heal", pc["name"])
            s = load(t)
            if not s["party"][0]["dead"] and not s.get("pending"):
                print(json.dumps([n, "--type", kind]))
                sys.exit(0)
        finally:
            shutil.rmtree(t, ignore_errors=True)
sys.exit("no foe paused the party on a copy of the home")
`;

// ---------------------------------------------------------------- plumbing
let failures = 0;
function check(ok, what) {
  console.log(`${ok ? '  ok  ' : '  FAIL'} ${what}`);
  if (!ok) failures++;
}

const env = { ...process.env, RPG2_HOME: home, PYTHONIOENCODING: 'utf-8' };
const pub = join(home, 'web', 'out');

function python(...argv) {
  return execFileSync('python3', argv, { cwd: repo, encoding: 'utf8', env });
}

let turn = 0;
async function publish(prose, extra = []) {
  // the turn's prose goes where page play keeps it: ui/scene.md
  const file = join(home, 'ui', 'scene.md');
  await writeFile(file, prose);
  await writeFile(join(out, `prose-${++turn}.md`), prose);
  python('publish.py', '--prose', file, ...extra);
  return JSON.parse(await readFile(join(pub, 'batch.json'), 'utf8'));
}

async function launch() {
  const headless = !args.includes('--headed');
  try {
    return await chromium.launch({ headless, executablePath: process.env.CHROMIUM || undefined });
  } catch (e) {
    const fallback = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
    if (!existsSync(fallback)) throw e;
    return chromium.launch({ headless, executablePath: fallback });
  }
}

const PHONE = { viewport: { width: 412, height: 915 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 };
const SMALL = { viewport: { width: 360, height: 740 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 };
const MID = { viewport: { width: 1100, height: 800 } };
const WIDE = { viewport: { width: 1440, height: 900 } };

async function open(browser, device, scheme, query = '') {
  const context = await browser.newContext({ ...device, colorScheme: scheme });
  const page = await context.newPage();
  page.on('pageerror', (e) => check(false, `no error on the page: ${e.message}`));
  await page.goto(server.url + query);
  return page;
}

/** A phone's tab: its own button in the bottom bar, or a chip under More. */
async function phoneTab(page, name) {
  const bar = page.locator('nav.bottom').getByRole('button', { name: new RegExp(`^${name}\\b`) });
  if (await bar.count()) {
    await bar.click();
    return;
  }
  const chip = page.getByRole('tab', { name: new RegExp(`^${name}\\b`) });
  if (!(await chip.isVisible())) await page.locator('nav.bottom').getByRole('button', { name: /^More/ }).click();
  await chip.click();
}

async function noSideScroll(page, where) {
  const [sw, cw] = await page.evaluate(() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]);
  check(sw <= cw, `${where}: no horizontal scroll (${sw} <= ${cw})`);
}

/** Every 40-column display on show fits its box: nothing clipped or scrolled. */
async function displaysFit(page, where) {
  const over = await page.evaluate(() => [...document.querySelectorAll('.display')]
    .filter((el) => el.getClientRects().length && el.scrollWidth > el.clientWidth + 1)
    .map((el) => `${el.className}: ${el.scrollWidth} > ${el.clientWidth}`));
  check(over.length === 0, `${where}: every display fits its width${over.length ? ` (${over.join('; ')})` : ''}`);
}

/** Buttons on show that are shorter than a thumb. */
async function smallTargets(page, selector) {
  return page.evaluate((sel) => [...document.querySelectorAll(sel)]
    .filter((el) => el.getClientRects().length)
    .map((el) => ({ what: (el.textContent || el.getAttribute('aria-label') || el.tagName).trim().slice(0, 30), h: el.getBoundingClientRect().height }))
    .filter((b) => b.h < 44), selector);
}

async function shoot(page, name, full = true) {
  await page.screenshot({ path: join(shots, `${name}.png`), fullPage: full });
}

/** The keeper's read: moves (list) and game/state (get), with their versions. */
async function keeperRead() {
  const read = join(pub, 'read');
  await mkdir(read, { recursive: true });
  const moves = join(read, 'moves.json');
  const state = join(read, 'state.json');
  await writeFile(moves, JSON.stringify(server.store.list('moves'), null, 2));
  await writeFile(state, JSON.stringify(server.store.get('game/state'), null, 2));
  return { moves, state, report: python('page.py', 'moves', moves, '--state', state) };
}

/** A batch posted to the fake store as ArtifactData would take it, then --sent. */
async function land(batch, what) {
  const res = await fetch(new URL('__db/batch', server.url), { method: 'POST', body: JSON.stringify(batch) });
  check(res.ok, `${what} lands`);
  python('publish.py', '--sent');
}

/** A keeper's turn with no moves to answer: the prose, pinned by the state read. */
async function turnOf(prose, what, extra = []) {
  const { state } = await keeperRead();
  await land(await publish(prose, ['--state', state, ...extra]), what);
}

/** Whether a bottom-bar button carries its unread mark. */
const barMarked = (page, name) => page.locator('nav.bottom').getByRole('button', { name: new RegExp(`^${name}\\b`) })
  .locator('.unread').count().then((n) => n > 0);

/** An element's screenshot without the phone's fixed bar laid across it. */
const NO_BAR = 'nav.bottom { display: none !important; }';

const text = (page, sel) => page.locator(sel).first().innerText();
const fileLines = async (path) => (await readFile(path, 'utf8')).replace(/\n$/, '').split('\n');

// ---------------------------------------------------------------- 1. the opening
// a fresh home in DIR: no save, publish or queue left from an earlier run
await rm(home, { recursive: true, force: true });
await mkdir(join(home, 'ui'), { recursive: true });
python('session.py', 'new', '--seed', '5', '--level', '1');
await publish(OPENING, ['--all']);
const server = await startServer({ port: 0, batches: [join(pub, 'batch.json')], quiet: true });
python('publish.py', '--sent');
const browser = await launch();
console.log(`Page at ${server.url}; output in ${out}`);
const party = server.store.get('game/party');
const pc = party.members.find((m) => m.isPc);
const companion = party.members.find((m) => !m.isPc);

try {
  console.log('1. the opening');
  const phone = await open(browser, PHONE, 'light');
  await phone.locator('rpg-story p', { hasText: 'Habiba, stops you' }).waitFor();
  const header = await text(phone, '.top');
  check(/Day 1/.test(header) && header.includes('Sidi Farhan'), `the header says Day 1 at Sidi Farhan (${header.replace(/\s+/g, ' ')})`);
  check(!/[^\x00-\x7f]/.test(header), 'the header is ASCII');
  const displays = phone.locator('rpg-story pre.display');
  check(await displays.count() === 2, 'the story holds its two displays');
  check((await displays.nth(1).innerText()).includes('options: take the road job, the\n    board'), 'the options display keeps its printed lines');
  const font = await displays.first().evaluate((el) => [getComputedStyle(el).fontFamily, getComputedStyle(el).whiteSpace]);
  check(/monospace/.test(font[0]) && font[1] === 'pre', `a display is mono, as printed (${font.join(', ')})`);
  check((await text(phone, 'rpg-answer .status')).startsWith('Your move'), 'the status line says "Your move"');
  check((await text(phone, 'rpg-answer .status')).includes('the DM looks when you call from Claude Code'), 'and when the DM looks');
  check(!(await phone.locator('.top .link').count()), 'a live connection shows no light');
  await phone.locator('label[for=move]', { hasText: `as ${pc.name}` }).waitFor();
  check(true, `the answer box is ${pc.name}'s`);
  await noSideScroll(phone, 'phone, story');
  await displaysFit(phone, 'phone, story');
  await shoot(phone, 'phone-light-opening');

  const opts = phone.locator('rpg-story .options .opt');
  const optWords = await opts.allInnerTexts();
  check(optWords.join('|') === 'take the road job|the board|the tavern|camp|travel',
    `the options display carries its choices as chips (${optWords.join('|')})`);
  check(await phone.locator('rpg-story .options').count() === 1, 'only the options display has chips');
  await opts.nth(2).click();
  await phone.waitForFunction(() => document.querySelector('#move')?.value === 'the tavern');
  check(true, 'a chip puts its words in the answer box');
  await phone.waitForFunction(() => document.activeElement?.id === 'move', null, { timeout: 3000 }).catch(() => null);
  check(await phone.evaluate(() => document.activeElement?.id) === 'move', 'and the box has the focus');
  await phone.waitForTimeout(300);
  check(server.store.list('moves').length === 0, 'a chip never sends: moves/ is still empty');
  await phone.fill('#move', '');

  // ---------------------------------------------------------------- 2. two moves
  console.log('2. two moves');
  await phone.fill('#move', MOVE);
  await phone.getByRole('button', { name: 'Send' }).click();
  await phone.locator('rpg-chronicle .entry.pending', { hasText: 'carts were taken' }).waitFor();
  check((await text(phone, 'rpg-answer .status')).startsWith('1 move waiting on the DM'), 'the status line counts one move');
  check((await phone.inputValue('#move')) === '', 'the box is empty again');
  await phone.getByRole('button', { name: 'To the DM' }).click();
  await phone.waitForFunction(() => document.querySelector('#move')?.getAttribute('placeholder') === 'Ask the DM, out of the game');
  check(true, 'to the DM, the box asks out of the game');
  await phone.fill('#move', QUESTION);
  await phone.getByRole('button', { name: 'Send' }).click();
  await phone.locator('rpg-chronicle .entry.pending', { hasText: 'next town' }).waitFor();
  check((await text(phone, 'rpg-answer .status')).startsWith('2 moves waiting on the DM'), 'two moves wait');
  check((await text(phone, 'rpg-chronicle .entry.pending >> nth=1')).includes(`(to the DM) ${QUESTION}`), 'the question waits as said to the DM');
  const moves = server.store.list('moves');
  check(moves.length === 2, 'two documents in moves/');
  check(moves[0]?.id === 'm0001' && moves[0]?.seq === 1 && moves[0]?.kind === 'say' && moves[0]?.text === MOVE, 'moves/m0001: seq 1, say, the words');
  check(moves[1]?.id === 'm0002' && moves[1]?.seq === 2 && moves[1]?.kind === 'ooc' && moves[1]?.text === QUESTION, 'moves/m0002: seq 2, ooc');
  check(moves.every((m) => Object.keys(m).sort().join() === 'at,id,kind,seq,text,version'), 'a move carries its known fields only');
  await shoot(phone, 'phone-light-queued');

  // ---------------------------------------------------------------- 3. the keeper's turn
  console.log("3. the keeper's turn");
  const read = join(pub, 'read');
  await mkdir(read, { recursive: true });
  await writeFile(join(read, 'moves.json'), JSON.stringify(server.store.list('moves'), null, 2));
  await writeFile(join(read, 'state.json'), JSON.stringify(server.store.get('game/state'), null, 2));
  const report = python('page.py', 'moves', join(read, 'moves.json'), '--state', join(read, 'state.json'));
  check(report.includes(`m0001 say: ${MOVE}`) && report.includes(`m0002 ooc: ${QUESTION}`), 'page.py moves reads both');
  const batch = await publish(TURN, ['--moves', join(read, 'moves.json'), '--state', join(read, 'state.json')]);
  check(batch.some((w) => w.op === 'set' && w.collection === 'game' && w.doc_id === 'state' && w.if_version), 'the batch pins game/state');
  check(batch.filter((w) => w.op === 'delete' && w.collection === 'moves' && w.if_version).length === 2, 'the batch deletes both moves, pinned');
  const sent = await fetch(new URL('__db/batch', server.url), { method: 'POST', body: JSON.stringify(batch) });
  check(sent.ok, 'the batch lands');
  python('publish.py', '--sent');

  await phone.locator('rpg-story p', { hasText: 'second milestone' }).waitFor();
  const said = await phone.locator('rpg-story .yousaid').allInnerTexts();
  check(said.length === 2 && said[0].includes(MOVE) && said[1].includes(`(to the DM) ${QUESTION}`), "the player's words sit under the new turn");
  await phone.waitForFunction(() => !document.querySelector('rpg-chronicle .entry.pending'));
  check(true, 'the waiting moves have cleared from the chronicle');
  check((await text(phone, 'rpg-answer .status')).startsWith('Your move'), 'the status line hands the turn back');
  check(server.store.list('moves').length === 0, 'moves/ is empty');
  check(server.store.get('game/state')?.lastSeq === 2 && server.store.get('game/state')?.latest === 't0002', 'game/state: lastSeq 2, latest t0002');
  const again = await fetch(new URL('__db/batch', server.url), { method: 'POST', body: JSON.stringify(batch) });
  check(again.status === 409 && server.store.get('game/state')?.lastSeq === 2, 'the same batch twice is refused by its pins');
  const transcript = await readFile(join(home, 'ui', 'transcript.md'), 'utf8');
  check(transcript.includes('## turn 2 (day 1)') && transcript.includes(`> ${MOVE}`) && transcript.includes(`> (to the DM) ${QUESTION}`),
    'ui/transcript.md gained the turn and the words it answered');
  check(await phone.locator('rpg-chronicle details.day').count() === 1, 'the chronicle holds one day');
  await phone.fill('#chronicle-search', 'milestone');
  check(await phone.locator('rpg-chronicle mark').count() >= 1, 'search marks what it finds');
  await phone.fill('#chronicle-search', 'zzz-nothing');
  check((await text(phone, 'rpg-chronicle')).includes('Nothing matches.'), 'search says when nothing matches');
  await phone.fill('#chronicle-search', '');
  await noSideScroll(phone, 'phone, after the turn');

  // ---------------------------------------------------------------- 4. a fight
  console.log('4. a fight');
  python('session.py', 'fight', '2', '--type', 'wolf');
  const short = await fileLines(join(home, 'ui', 'fight-short.txt'));
  await writeFile(join(read, 'state.json'), JSON.stringify(server.store.get('game/state'), null, 2));
  const fightBatch = await publish(FIGHT, ['--state', join(read, 'state.json')]);
  check(fightBatch.some((w) => w.collection === 'fights' && w.doc_id === 'f0001'), 'the fight goes out as fights/f0001');
  check((await fetch(new URL('__db/batch', server.url), { method: 'POST', body: JSON.stringify(fightBatch) })).ok, 'the fight turn lands');
  python('publish.py', '--sent');
  const chip = phone.locator('rpg-story rpg-fight-chip');
  await chip.waitFor();
  const order = await phone.locator('rpg-story rpg-prose > *').evaluateAll((els) => els.map((e) => e.tagName.toLowerCase()));
  const at = order.indexOf('rpg-fight-chip');
  check(at > 0 && order[at - 1] === 'pre' && order[at + 1] === 'pre', `the card sits in place, between the two displays (${order.join(' ')})`);
  const fight = server.store.get('fights/f0001');
  check((await chip.innerText()).includes(`a fight: ${fight.title}, ${fight.outcome === 'paused' ? 'PAUSED' : fight.outcome}`), 'the card names the fight and how it went');
  check(!(await phone.locator('rpg-story rpg-prose p', { hasText: '[fight]' }).count()), 'the marker itself is not shown');
  await noSideScroll(phone, 'phone, story with a fight');
  await displaysFit(phone, 'phone, story with a fight');
  await shoot(phone, 'phone-light-story');
  await chip.locator('button').click();
  await phone.locator('rpg-fight .main').waitFor();
  check(await phone.locator('.drawer rpg-fight').isVisible(), 'the card opens the Fight tab');
  check((await text(phone, 'rpg-fight h2')) === fight.title, 'the Fight tab is on that fight');
  const lines = await phone.locator('rpg-fight .main .ln').allTextContents();
  check(JSON.stringify(lines) === JSON.stringify(short), `the fight's lines are ui/fight-short.txt exactly (${lines.length} of ${short.length})`);
  const rounds = await phone.locator('rpg-fight details.round').count();
  const opened = await phone.locator('rpg-fight details.round[open]').count();
  check(rounds >= 1, `the rounds fold (${rounds})`);
  check(opened === 1 && await phone.locator('rpg-fight details.round').last().evaluate((d) => d.open), 'the newest round is open');
  await noSideScroll(phone, 'phone, fight');
  await displaysFit(phone, 'phone, fight');
  await shoot(phone, 'phone-light-fight');
  await phoneTab(phone, 'Fights');
  await phone.locator('rpg-fights [data-fight="f0001"]').waitFor();
  check((await text(phone, 'rpg-fights [data-fight="f0001"]')).includes(fight.title), 'the Fights list has it');
  await shoot(phone, 'phone-light-fights');

  // ---------------------------------------------------------------- 5. the party
  console.log('5. the party');
  await phoneTab(phone, 'Party');
  await phone.locator(`.line rpg-party [data-member="${pc.name}"]`).waitFor();
  check(await phone.locator(`.line rpg-party [data-member="${companion.name}"]`).count() === 1, `a card for ${pc.name} and one for ${companion.name}`);
  check(/YOU/.test(await text(phone, `.line [data-member="${pc.name}"] header`)) && /companion/.test(await text(phone, `.line [data-member="${companion.name}"] header`)),
    'the PC is YOU, the other a companion');
  await phone.locator('.line details.whole summary').click();
  const sheet = await phone.locator('.line #party-sheet').textContent();
  const partyTxt = (await readFile(join(home, 'ui', 'party.txt'), 'utf8')).replace(/\n$/, '');
  check(sheet === partyTxt, 'the whole sheet as printed is ui/party.txt');
  await noSideScroll(phone, 'phone, party');
  await displaysFit(phone, 'phone, party');
  await shoot(phone, 'phone-light-party');

  // ---------------------------------------------------------------- 6. a job: the map, the quests, the record
  console.log('6. a job taken: the map, the quests, the record');
  const qid = python('-c', 'import session; print(session.load()["world"]["opening_quest"])').trim();
  python('session.py', 'take', qid);
  await turnOf(TAKEN, 'the job turn');
  await phone.locator('.line rpg-party').waitFor();
  await phone.waitForFunction(() => document.querySelector('nav.bottom')?.textContent?.includes('Map'));
  await phone.waitForTimeout(200);
  check(await barMarked(phone, 'Map'), 'the Map is marked once its document changes');
  await phoneTab(phone, 'Map');
  await phone.locator('rpg-map svg.grid').waitFor();
  await phone.waitForTimeout(200);
  check(!(await barMarked(phone, 'Map')), 'looking at the Map clears its mark');
  const st = server.store.get('game/state');
  const mapDoc = server.store.get('game/map');
  check(await phone.locator('rpg-map rect[data-coord]').count() === 540, 'the map is 540 squares (30 by 18)');
  check((await phone.locator('rpg-map g.party').getAttribute('data-mark')) === `party ${st.coord}`, `the @ stands on game/state's coord (${st.coord})`);
  const glyph = await phone.locator(`rpg-map rect[data-coord="${st.coord}"]`).getAttribute('data-glyph');
  const [r0, c0] = st.coord.match(/\d+/g).map(Number);
  check(glyph === mapDoc.rows[r0 - 1][c0 - 1], `the square under the @ is the grid's own (${glyph})`);
  check(mapDoc.objectives.length > 0 && await phone.locator('rpg-map g.job').count() === mapDoc.objectives.length, `the job's site is marked (${mapDoc.objectives.join(', ')})`);
  const city = mapDoc.places.find((p) => p.kind === 'city' && !mapDoc.places.some((q) => q !== p && q.coord === p.coord));
  const cityGlyph = mapDoc.rows[Number(city.coord.slice(1, 3)) - 1][Number(city.coord.slice(4, 6)) - 1];
  await phone.locator(`rpg-map rect[data-coord="${city.coord}"]`).click();
  await phone.waitForFunction((c) => document.querySelector('#map-said')?.textContent?.startsWith(c), city.coord);
  const cityWords = await text(phone, '#map-said');
  check(cityWords === `${city.coord} -- land. ${city.name} (city, ${city.land}${city.capital ? ', capital' : ''}).` && cityGlyph === 'C',
    `tapping a city names it: ${cityWords}`);
  await phone.locator(`rpg-map rect[data-coord="${st.coord}"]`).click();
  await phone.waitForFunction((c) => document.querySelector('#map-said')?.textContent?.startsWith(c), st.coord);
  const named = await text(phone, '#map-said');
  check(named.startsWith(`${st.coord} -- `) && named.includes('The party is here') && named.includes('Sidi Farhan (village, Umaia)'),
    `tapping the party's square names it: ${named}`);
  await noSideScroll(phone, 'phone, map');
  await displaysFit(phone, 'phone, map');
  await shoot(phone, 'phone-light-map');
  await phone.click('#map-toggle');
  const mapText = await phone.locator('#map-text').textContent();
  check(mapText === (await fileLines(join(home, 'ui', 'map.txt'))).join('\n'), 'the text map is ui/map.txt exactly');
  await displaysFit(phone, 'phone, text map');
  await shoot(phone, 'phone-light-map-text');
  await phone.click('#map-toggle');
  const unknown = JSON.parse(python('-c', UNKNOWN_PLACES));
  const dump = JSON.stringify(await (await fetch(new URL('__db/dump', server.url))).json());
  const leaked = unknown.filter((n) => new RegExp(`\\b${n.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`).test(dump));
  check(unknown.length > 0 && leaked.length === 0, `no unknown settlement is anywhere in the store (${unknown.length} unknown${leaked.length ? `; leaked: ${leaked.join(', ')}` : ''})`);

  await phoneTab(phone, 'Quests');
  const card = phone.locator(`rpg-quests [data-quest="${qid}"]`);
  await card.waitFor();
  const quest = server.store.get('game/quests').quests[0];
  const cardText = await card.innerText();
  check(cardText.includes(quest.name) && quest.sites.length > 0 && quest.sites.every((s) => cardText.includes(s.name) && cardText.includes(s.mark)),
    `the Quests card has ${quest.name} and its sites, with how far the party has got`);
  check(quest.due !== null && cardText.includes(`day ${quest.due}`) && cardText.includes(quest.note), `and the due day (day ${quest.due}, ${quest.note})`);
  await card.locator('summary').click();
  const printedJob = await card.locator('pre.display').textContent();
  check(printedJob === quest.lines.join('\n') && mapText.includes(printedJob), 'the job as printed is map.txt\'s own lines');
  await noSideScroll(phone, 'phone, quests');
  await displaysFit(phone, 'phone, quests');
  await shoot(phone, 'phone-light-quests');

  await phoneTab(phone, 'Record');
  await phone.locator('rpg-record [data-section]').first().waitFor();
  const sections = await phone.locator('rpg-record [data-section] h3').allInnerTexts();
  check(sections.map((x) => x.toUpperCase()).join('|') === 'QUESTS DONE|REMARKABLE|THE TALLY OF SIN|SUGGESTIONS', `the Record's sections are history.txt's (${sections.join(', ')})`);
  await phone.locator('rpg-record details.whole summary').click();
  check((await phone.locator('#record-text').textContent()) === (await fileLines(join(home, 'ui', 'history.txt'))).join('\n'), 'the history as printed is ui/history.txt');
  check((await phone.locator('rpg-record [data-section="tally"] pre').textContent()) === server.store.get('game/record').tally.join('\n'), 'the tally is printed as the page prints it');
  await noSideScroll(phone, 'phone, record');
  await displaysFit(phone, 'phone, record');
  await shoot(phone, 'phone-light-record');

  // ---------------------------------------------------------------- 7. a level crossed
  console.log('7. a level crossed');
  const pcBefore = server.store.get('game/party').members.find((m) => m.isPc);
  python('session.py', 'award', '0', String(pcBefore.xpNext - pcBefore.xp), pcBefore.name);
  await turnOf(LEVEL, 'the level turn');
  await phoneTab(phone, 'Party');
  await phone.locator('.line #levelup').waitFor();
  const lu = server.store.get('game/state').levelUp;
  check(lu?.hero === pc.name && lu.points > 0, `game/state.levelUp: ${pc.name}, ${lu?.points} points`);
  check((await phone.locator('.line #levelup-menu').textContent()) === lu.text.join('\n'), 'the Party tab shows the spending menu as printed');
  check((await text(phone, '.line #levelup')).includes('Say what to spend them on.'), 'and asks the player to say what to buy');
  check(await phone.locator(`.line [data-member="${pc.name}"] .points`).count() === 1, "the PC's card is marked with points to spend");
  await noSideScroll(phone, 'phone, level-up');
  await displaysFit(phone, 'phone, level-up');
  await shoot(phone, 'phone-light-levelup');
  await phoneTab(phone, 'Story');
  const level = server.store.get('game/party').members.find((m) => m.isPc).level;
  check(await phone.locator('rpg-chronicle .entry.level', { hasText: `${pc.name} reaches level ${level}.` }).count() === 1, `the chronicle says "${pc.name} reaches level ${level}."`);

  // ---------------------------------------------------------------- 8. a paused fight
  console.log('8. a paused fight');
  const foe = JSON.parse(python('-c', PAUSING_FOE));
  python('session.py', 'fight', ...foe);
  check(python('-c', 'import session; print(bool(session.load()["pending"]))').trim() === 'True', `${foe.join(' ')} pauses, as it did on a copy of the home`);
  await turnOf(`A ${foe[2]} comes out of the olive trees onto the road.\n\n[fight]\n\nThe fight stops for a breath. The call is yours.`, 'the paused fight');
  const st2 = server.store.get('game/state');
  const pz = st2.pause;
  const pausedId = pz?.fight;
  check(!!pausedId && pausedId === st2.lastFight && server.store.get(`fights/${pausedId}`)?.outcome === 'paused', `game/state.pause.fight is the paused fight (${pausedId})`);
  await phone.locator('#pause').waitFor();
  check(await phone.evaluate(() => document.documentElement.dataset.paused) === 'true', ':root carries data-paused');
  check((await phone.locator('#pause .head').textContent()).startsWith(`PAUSED after round ${pz.round}`), 'the picker says the round');
  check(await barMarked(phone, 'Fight') && await barMarked(phone, 'More'), 'a new fight marks Fight, and More for Fights');
  await phoneTab(phone, 'Fight');
  await phone.locator(`rpg-fight .main[data-fight="${pausedId}"]`).waitFor();
  await phone.waitForTimeout(200);
  check(!(await barMarked(phone, 'Fight')) && await barMarked(phone, 'More'), 'looking at the Fight clears its mark; Fights keeps its own');
  await phone.getByRole('button', { name: 'To the pause' }).click();
  await phone.locator('#pause').waitFor();
  check(await phone.locator('.page').isVisible(), '"To the pause" goes back to the story, at the picker');
  await phone.reload();
  await phone.locator('#pause').waitFor();
  await phone.waitForTimeout(300);
  check(!(await barMarked(phone, 'Fight')) && await barMarked(phone, 'More'), 'a reload remembers what was looked at');
  await phoneTab(phone, 'Fights');
  await phone.waitForTimeout(200);
  check(!(await barMarked(phone, 'More')), 'looking at the Fights clears More');
  await phoneTab(phone, 'Story');

  // a tampered move: the page would never build it, the keeper refuses it
  const party2 = server.store.get('game/party').members;
  const lacks = (h) => (h.healing < 1 ? 'heal' : h.stamina < 1 ? 'drink' : null);
  let bad = pz.party.map((h) => ({ hero: h.name, action: lacks(h) })).find((b) => b.action);
  if (!bad) bad = { hero: party2.find((m) => (m.spells.invisibility ?? 0) < 2).name, action: 'vanish' };
  const seqNow = Math.max(st2.lastSeq, ...server.store.list('moves').map((m) => m.seq)) + 1;
  const badId = `m${String(seqNow).padStart(4, '0')}`;
  const badMove = { seq: seqNow, at: Date.now(), kind: 'pause', fight: pausedId, choice: 'fight_on', actions: [bad] };
  check((await fetch(new URL('__db/write', server.url), { method: 'POST', body: JSON.stringify({ op: 'set', path: `moves/${badId}`, data: badMove }) })).ok,
    `a tampered pause move is written: ${bad.hero} ${bad.action}`);
  const badWords = `At the pause: ${bad.hero} ${{ heal: 'drinks a healing potion', drink: 'drinks a stamina draught', vanish: 'vanishes' }[bad.action]}; fight on`;
  await phone.locator('#pause-sent').waitFor();
  check((await text(phone, '#pause-sent')) === badWords, 'the picker says a choice is sent, in the words page.move_words uses');
  const r1 = await keeperRead();
  const refusedLine = r1.report.split('\n').find((l) => l.startsWith(`${badId} pause REFUSED:`)) ?? '';
  check(refusedLine.includes(bad.hero) && refusedLine.endsWith('(answer it in the fiction)'), `page.py moves refuses it: ${refusedLine}`);
  await land(await publish(REFUSED.replace('NAME', bad.hero), ['--moves', r1.moves, '--state', r1.state]), 'the refusal turn');
  await phone.locator('rpg-story p', { hasText: 'no such flask' }).waitFor();
  check(server.store.list('moves').length === 0, 'the publish deletes the refused move');
  check((await phone.locator('rpg-story .yousaid').allInnerTexts()).some((t) => t.includes(badWords)), 'the turn answers it, with its words under the prose');
  await phone.locator('#pause-fight-on').waitFor();
  check(server.store.get('game/state').pause?.fight === pausedId, 'the pause still stands, and the picker is back');

  // the picker: only what the menu offers
  await phone.click('#pause-fight-on');
  await phone.locator('#pause .hero-acts').first().waitFor();
  const ACTS = ['drink', 'heal', 'berserk', 'warbreath', 'vanish'];
  const want = pz.party.map((h) => [h.name, pz.options.filter((o) => ACTS.includes(o.choice) && (o.heroes ?? []).includes(h.name)).map((o) => o.choice)])
    .filter(([, a]) => a.length);
  const offered = await phone.locator('#pause .hero-acts').evaluateAll((els) => els.map((el) => [el.dataset.hero, [...el.querySelectorAll('.chip')].map((c) => c.dataset.action)]));
  check(JSON.stringify(offered) === JSON.stringify(want), `the picker offers only what the menu does (${JSON.stringify(offered)})`);
  const healers = pz.party.filter((h) => !h.down && h.healing > 0).map((h) => h.name);
  check(JSON.stringify(offered.filter(([, a]) => a.includes('heal')).map(([h]) => h)) === JSON.stringify(healers), `heal is offered to the potion carriers only (${healers.join(', ')})`);
  const mine = phone.locator(`#pause .hero-acts[data-hero="${pc.name}"]`);
  const others = (want.find(([h]) => h === pc.name)?.[1] ?? []).filter((a) => a !== 'heal');
  if (others.length) {
    await mine.locator(`.chip[data-action="${others[0]}"]`).click();
    await mine.locator('.chip[data-action="heal"]').click();
    check(await mine.locator('.chip[aria-pressed="true"]').count() === 1, 'one action a hero: a second chip replaces the first');
  } else {
    await mine.locator('.chip[data-action="heal"]').click();
  }
  const pickWords = `At the pause: ${pc.name} drinks a healing potion; fight on`;
  check((await text(phone, '#pause-summary')) === pickWords, `the summary is the move in words: ${pickWords}`);
  await phone.click('#pause-retreat');
  await phone.locator('#pause-escapes').waitFor();
  check(!(await phone.locator('#pause-actions').count()) && (await text(phone, '#pause-summary')) === 'At the pause: retreat', 'Retreat puts the actions away');
  await phone.click('#pause-fight-on');
  await phone.locator('#pause-actions').waitFor();
  check((await text(phone, '#pause-summary')) === pickWords, 'and Fight on keeps the choice');
  const tiny = await smallTargets(phone, '#pause button, #pause summary, rpg-prose .opt');
  check(tiny.length === 0, `the picker's targets are thumb-sized${tiny.length ? ` (${JSON.stringify(tiny)})` : ''}`);
  await phone.locator('#pause details.fold summary').click();
  await noSideScroll(phone, 'phone, pause');
  await displaysFit(phone, 'phone, pause');
  await phone.locator('#pause').scrollIntoViewIfNeeded();
  await phone.locator('#pause').screenshot({ path: join(shots, 'phone-light-pause.png'), style: NO_BAR });
  await shoot(phone, 'phone-light-story-paused');
  for (const [device, name, scheme] of [[PHONE, 'phone', 'dark'], [SMALL, 'small', 'light'], [SMALL, 'small', 'dark']]) {
    const page = await open(browser, device, scheme);
    await page.locator('#pause-fight-on').waitFor();
    await page.click('#pause-fight-on');
    await page.locator(`#pause .hero-acts[data-hero="${pc.name}"] .chip[data-action="heal"]`).click();
    await page.locator('#pause details.fold summary').click();
    await noSideScroll(page, `${name}, ${scheme}, pause`);
    await displaysFit(page, `${name}, ${scheme}, pause`);
    await page.locator('#pause').screenshot({ path: join(shots, `${name}-${scheme}-pause.png`), style: NO_BAR });
    await page.context().close();
  }
  await phone.click('#pause-send');
  await phone.locator('#pause-sent').waitFor();
  const sentMoves = server.store.list('moves');
  const pm = sentMoves[0];
  check(sentMoves.length === 1 && pm.kind === 'pause' && pm.fight === pausedId && pm.choice === 'fight_on'
    && JSON.stringify(pm.actions) === JSON.stringify([{ hero: pc.name, action: 'heal' }]), `the move lands in moves/ for ${pausedId}: heal ${pc.name}, fight on`);
  check(Object.keys(pm).sort().join() === 'actions,at,choice,fight,id,kind,seq,version', 'a pause move carries its known fields only');
  check((await text(phone, '#pause-sent')) === pickWords && await phone.locator('#move').count() === 1, 'sent: the picker waits on the DM, and the box stays open for words');
  const r2 = await keeperRead();
  const cmd = r2.report.split('\n').find((l) => l.startsWith(`${pm.id} pause -> `)) ?? '';
  check(cmd === `${pm.id} pause -> python session.py resume --heal ${pc.name}`, `page.py moves prints the command: ${cmd}`);
  const argv = JSON.parse(python('-c', 'import json, shlex, sys; print(json.dumps(shlex.split(sys.argv[1])))', cmd.split(' -> python session.py ')[1]));
  python('session.py', ...argv);
  await land(await publish(CONTINUED, ['--moves', r2.moves, '--state', r2.state]), 'the second half');
  const st3 = server.store.get('game/state');
  const contId = st3.lastFight;
  const cont = server.store.get(`fights/${contId}`);
  check(cont?.continues === pausedId && st3.pause === null, `${contId} continues ${pausedId}; the pause is over`);
  await phone.locator(`rpg-story .fightchip[data-fight="${contId}"]`).waitFor();
  await phone.waitForFunction(() => !document.querySelector('#pause'));
  check(await phone.evaluate(() => document.documentElement.dataset.paused) === undefined, 'the picker is gone, and data-paused with it');
  check((await text(phone, `rpg-story .fightchip[data-fight="${contId}"]`)).includes('the fight goes on:'), 'the story holds the second half, as the fight going on');
  check(await phone.locator(`rpg-chronicle .fightchip[data-fight="${pausedId}"]`).count() === 1, 'the chronicle holds the first half');
  await phone.locator(`rpg-story .fightchip[data-fight="${contId}"]`).click();
  await phone.locator('rpg-fight details.first').waitFor();
  await phone.locator('rpg-fight details.first summary').click();
  const both = [...await phone.locator('rpg-fight .half .ln').allTextContents(), ...await phone.locator('rpg-fight .main .ln').allTextContents()];
  check(JSON.stringify(both) === JSON.stringify(await fileLines(join(home, 'ui', 'fight-short.txt'))), 'both halves, in order, are ui/fight-short.txt exactly');
  await noSideScroll(phone, 'phone, second half');
  await displaysFit(phone, 'phone, second half');
  await shoot(phone, 'phone-light-second-half');
  await phoneTab(phone, 'Story');

  // ---------------------------------------------------------------- 9. the layout
  console.log('9. the layout');
  for (const [page, width] of [[phone, 412]]) {
    const bar = await page.locator('nav.bottom button').evaluateAll((els) => els.map((e) => { const r = e.getBoundingClientRect(); return { right: r.right, h: r.height, w: r.width }; }));
    check(bar.length === 5 && Math.max(...bar.map((b) => b.right)) <= width && bar.every((b) => b.h >= 48 && b.w >= 48),
      `${width}: the bottom bar is five thumb-sized buttons, and they fit`);
  }
  check((await phone.locator('nav.bottom').innerText()).replace(/, changed/g, '').replace(/\s+/g, ' ').trim() === 'Story Party Map Fight More', 'the bar: Story, Party, Map, Fight, More');
  await phoneTab(phone, 'Quests');
  const moreTabs = (await phone.locator('.drawer .tabs.more button').allTextContents()).map((t) => t.replace(', changed', '').trim());
  check(moreTabs.join(' ') === 'Fights Quests Record', 'More holds Fights, Quests and Record');
  await phone.locator('nav.bottom').getByRole('button', { name: /^Story/ }).click();
  const small = await smallTargets(phone, 'rpg-answer button, rpg-fight-chip button, nav.bottom button, rpg-prose .opt');
  check(small.length === 0, `the story's buttons are thumb-sized${small.length ? ` (${JSON.stringify(small)})` : ''}`);
  await phone.context().close();

  for (const [device, name] of [[PHONE, 'phone'], [SMALL, 'small']]) {
    for (const scheme of name === 'phone' ? ['dark'] : ['light', 'dark']) {
      const page = await open(browser, device, scheme);
      await page.locator('rpg-story rpg-fight-chip').waitFor();
      await noSideScroll(page, `${name}, ${scheme}, story`);
      await displaysFit(page, `${name}, ${scheme}, story`);
      await shoot(page, `${name}-${scheme}-story`);
      await page.locator('rpg-story rpg-fight-chip button').click();
      await page.locator('rpg-fight .main').waitFor();
      await noSideScroll(page, `${name}, ${scheme}, fight`);
      await displaysFit(page, `${name}, ${scheme}, fight`);
      await shoot(page, `${name}-${scheme}-fight`);
      await phoneTab(page, 'Party');
      await page.locator('.line rpg-party .card').first().waitFor();
      await noSideScroll(page, `${name}, ${scheme}, party`);
      await displaysFit(page, `${name}, ${scheme}, party`);
      if (name === 'small') await shoot(page, `${name}-${scheme}-party`);
      for (const tab of ['Map', 'Quests', 'Record']) {
        await phoneTab(page, tab);
        const panel = page.locator(`.drawer rpg-${tab.toLowerCase()}`);
        await panel.waitFor();
        for (const fold of await panel.locator('details:not([open]) > summary').all()) await fold.click();
        await noSideScroll(page, `${name}, ${scheme}, ${tab}`);
        await displaysFit(page, `${name}, ${scheme}, ${tab}`);
        await shoot(page, `${name}-${scheme}-${tab.toLowerCase()}`);
        if (tab === 'Map') {
          const svg = await page.locator('rpg-map svg.grid').boundingBox();
          check(svg.x >= 0 && svg.x + svg.width <= device.viewport.width, `${name}, ${scheme}: the drawn map fits the width (${Math.round(svg.width)}px)`);
          await page.click('#map-toggle');
          await noSideScroll(page, `${name}, ${scheme}, text map`);
          await displaysFit(page, `${name}, ${scheme}, text map`);
        }
      }
      await page.context().close();
    }
  }
  for (const [device, name] of [[MID, 'mid'], [WIDE, 'wide']]) {
    for (const scheme of ['light', 'dark']) {
      const page = await open(browser, device, scheme);
      await page.locator('rpg-story rpg-fight-chip').waitFor();
      check(await page.locator('.drawer rpg-map svg.grid').isVisible(), `${name}, ${scheme}: the drawer opens on the map`);
      if (name === 'wide') check(await page.locator('.line rpg-party').isVisible(), `${name}, ${scheme}: three zones, the party beside the story`);
      else check(!(await page.locator('.line').isVisible()) && await page.getByRole('tab', { name: 'Party' }).isVisible(), `${name}, ${scheme}: the party folds into a tab`);
      await noSideScroll(page, `${name}, ${scheme}`);
      await displaysFit(page, `${name}, ${scheme}`);
      await shoot(page, `${name}-${scheme}`, false);
      await page.context().close();
    }
  }

  const blocked = await browser.newContext({ ...PHONE, colorScheme: 'light' });
  await blocked.addInitScript(() => {
    for (const name of ['localStorage', 'sessionStorage']) {
      Object.defineProperty(window, name, { configurable: true, get() { throw new DOMException('blocked', 'SecurityError'); } });
    }
  });
  const nostore = await blocked.newPage();
  nostore.on('pageerror', (e) => check(false, `storage blocked: no error on the page: ${e.message}`));
  await nostore.goto(server.url);
  await nostore.locator('rpg-story rpg-fight-chip').waitFor();
  await phoneTab(nostore, 'Map');
  await nostore.locator('rpg-map svg.grid').waitFor();
  await phoneTab(nostore, 'Fights');
  await nostore.locator('rpg-fights .row').first().waitFor();
  check(true, 'storage blocked: the page, its tabs and its marks still work');
  await blocked.close();

  // ---------------------------------------------------------------- 10. the fallbacks
  console.log('10. the fallbacks');
  const ro = await open(browser, PHONE, 'light', '?readonly');
  await ro.locator('rpg-story p').first().waitFor();
  await ro.fill('#move', 'This will not land.');
  await ro.getByRole('button', { name: 'Send' }).click();
  await ro.locator('rpg-answer .closed', { hasText: 'You can read this game but not write to it.' }).waitFor();
  check(server.store.list('moves').length === 0, 'read-only: the refused move is not stored, and the box closes');
  await ro.context().close();

  const none = await open(browser, PHONE, 'light', '?nodb');
  await none.locator('.notice p').waitFor();
  check((await text(none, '.notice p')) === 'This page has no line to the game. Open it on claude.ai, signed in.', 'no db: the page says it has no line to the game');
  check((await text(none, '.top .link')).includes('Not connected'), 'no db: the header says not connected');
  await shoot(none, 'nodb-phone-light');
  await none.context().close();

  // ---------------------------------------------------------------- 11. game over
  console.log('11. game over');
  python('-c', 'import json, os; p = os.path.join(os.environ["RPG2_HOME"], "save.json"); s = json.load(open(p)); '
    + 's["party"][0].update(hp=0, dead=True, down=False); json.dump(s, open(p, "w"))');
  await turnOf(OVER, 'the last turn', ['--status', 'ended']);
  check(server.store.get('game/state').over === 'pc_dead' && server.store.get('game/state').status === 'ended', 'game/state: over pc_dead, status ended');
  const end = await open(browser, PHONE, 'light');
  await end.locator('rpg-story p', { hasText: 'The road goes dark' }).waitFor();
  check(await end.evaluate(() => document.documentElement.dataset.over) === 'pc_dead', ':root carries data-over');
  check((await text(end, 'rpg-answer .closed')) === 'GAME OVER' && !(await end.locator('#move').count()), 'the answer box is closed: GAME OVER');
  check((await text(end, 'rpg-answer .status')).startsWith('GAME OVER'), 'the status line says GAME OVER');
  check(!(await end.locator('#pause').count()) && !(await end.locator('rpg-prose .opt').count()), 'no picker and no option chips');
  const grey = await end.locator('.zones').evaluate((el) => getComputedStyle(el).filter);
  check(/grayscale/.test(grey), `the page goes grey (${grey})`);
  await shoot(end, 'phone-light-over');
  await end.context().close();
} catch (e) {
  check(false, `the run finished: ${e.stack || e}`);
} finally {
  await browser.close();
  await server.close();
}

console.log(failures ? `\n${failures} check(s) failed. Screenshots: ${shots}` : `\nAll checks pass. Screenshots: ${shots}`);
process.exit(failures ? 1 : 0);
