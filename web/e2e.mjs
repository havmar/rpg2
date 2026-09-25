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
 *      place in the header, "Your move" and the answer box as the PC;
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
 *   6. the layout: no side scroll at 412 and 360, the bottom bar fits and
 *      its targets are thumb-sized; screenshots at phone (light and dark),
 *      small, mid and wide;
 *   7. the fallbacks: a read-only viewer, and a page with no db.
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

  // ---------------------------------------------------------------- 6. the layout
  console.log('6. the layout');
  for (const [page, width] of [[phone, 412]]) {
    const bar = await page.locator('nav.bottom button').evaluateAll((els) => els.map((e) => { const r = e.getBoundingClientRect(); return { right: r.right, h: r.height, w: r.width }; }));
    check(bar.length === 4 && Math.max(...bar.map((b) => b.right)) <= width && bar.every((b) => b.h >= 48 && b.w >= 48),
      `${width}: the bottom bar is four thumb-sized buttons, and they fit`);
  }
  check((await phone.locator('nav.bottom').innerText()).replace(/\s+/g, ' ').trim() === 'Story Party Fight More', 'the bar: Story, Party, Fight, More');
  await phone.locator('nav.bottom').getByRole('button', { name: /^Story/ }).click();
  const small = await smallTargets(phone, 'rpg-answer button, rpg-fight-chip button, nav.bottom button');
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
      await page.context().close();
    }
  }
  for (const [device, name] of [[MID, 'mid'], [WIDE, 'wide']]) {
    for (const scheme of ['light', 'dark']) {
      const page = await open(browser, device, scheme);
      await page.locator('rpg-story rpg-fight-chip').waitFor();
      check(await page.locator('.drawer rpg-fight').isVisible(), `${name}, ${scheme}: the drawer shows the fight`);
      if (name === 'wide') check(await page.locator('.line rpg-party').isVisible(), `${name}, ${scheme}: three zones, the party beside the story`);
      else check(!(await page.locator('.line').isVisible()) && await page.getByRole('tab', { name: 'Party' }).isVisible(), `${name}, ${scheme}: the party folds into a tab`);
      await noSideScroll(page, `${name}, ${scheme}`);
      await displaysFit(page, `${name}, ${scheme}`);
      await shoot(page, `${name}-${scheme}`, false);
      await page.context().close();
    }
  }

  // ---------------------------------------------------------------- 7. the fallbacks
  console.log('7. the fallbacks');
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
} catch (e) {
  check(false, `the run finished: ${e.stack || e}`);
} finally {
  await browser.close();
  await server.close();
}

console.log(failures ? `\n${failures} check(s) failed. Screenshots: ${shots}` : `\nAll checks pass. Screenshots: ${shots}`);
process.exit(failures ? 1 : 0);
