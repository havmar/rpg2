#!/usr/bin/env node
/**
 * The keeper's side of the local table: ArtifactData's calls, against
 * web/dev/serve.mjs instead of claude.ai.
 *
 *   node web/dev/db.mjs list moves          > moves.json   (each with id and version)
 *   node web/dev/db.mjs get game/state      > state.json   (with its version)
 *   node web/dev/db.mjs batch web/out/batch.json            (atomic, pinned)
 *   node web/dev/db.mjs dump
 *
 * --url http://127.0.0.1:4321/ (or RPG2_TABLE) picks the server.
 */
import { readFile } from 'node:fs/promises';

const args = process.argv.slice(2);
let base = process.env.RPG2_TABLE || 'http://127.0.0.1:4321/';
const i = args.indexOf('--url');
if (i >= 0) base = args.splice(i, 2)[1];
const [cmd, arg] = args;

const call = async (path, init) => {
  const res = await fetch(new URL(path, base), init);
  const body = await res.json();
  if (!res.ok) {
    console.error(`${body.code}: ${body.message}`);
    process.exit(1);
  }
  return body;
};

let out;
if (cmd === 'list' && arg) out = await call(`__db/list?collection=${encodeURIComponent(arg)}`);
else if (cmd === 'get' && arg) out = await call(`__db/get?path=${encodeURIComponent(arg)}`);
else if (cmd === 'dump') out = await call('__db/dump');
else if (cmd === 'batch' && arg) {
  out = await call('__db/batch', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: await readFile(arg, 'utf8'),
  });
} else {
  console.error('usage: node web/dev/db.mjs list COLLECTION | get PATH | batch FILE | dump [--url URL]');
  process.exit(2);
}
console.log(JSON.stringify(out, null, 2));
