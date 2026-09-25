#!/usr/bin/env node
/**
 * A local table: the built page and a fake `db` store, with no claude.ai.
 *
 *   node web/dev/serve.mjs [--port 4321] [--batch FILE]...
 *
 * Serves web/dist/index.html inside the skeleton the Artifact host would add,
 * with web/dev/fake-db.js loaded first: that shim gives the page
 * `window.claude.use("db")`, backed by an in-memory store held here and kept
 * live over server-sent events. Each `--batch` is a publish.py batch.json
 * (ArtifactData `writes`), applied at start to seed the store.
 *
 * Query flags on the page's URL:  ?nodb  no capability (the page's fallback);
 * ?readonly  every write is refused, as for a view-only viewer;
 * ?theme=dark|light  stamps data-theme, as the viewer's theme toggle does.
 *
 * The keeper's side (as ArtifactData would do it): web/dev/db.mjs, or
 *   GET  /__db/list?collection=moves   the documents, each with id and version
 *   GET  /__db/get?path=game/state     one document, with its version
 *   POST /__db/batch                   a batch.json, atomic, pinned by if_version
 */
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { dirname, extname, join, normalize, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const DIST = resolve(here, '..', 'dist');

// ---------------------------------------------------------------- the store
export class FakeStore {
  /** path -> {data, version} */
  docs = new Map();
  listeners = new Set();

  dump() {
    return Object.fromEntries([...this.docs].map(([p, d]) => [p, d]));
  }

  onChange(fn) {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  changed() {
    for (const fn of this.listeners) fn();
  }

  /** One page write: set, update or delete a document. Throws {code, message}. */
  write({ op, path, data }) {
    checkPath(path);
    this.apply([{ op, path, data }]);
  }

  /** An ArtifactData batch: every if_version is checked before anything is written. */
  async batch(writes) {
    if (!Array.isArray(writes) || !writes.length) throw err('invalid_argument', 'a batch is a list of writes');
    if (writes.length > 50) throw err('invalid_argument', 'at most 50 writes in a batch');
    const ops = [];
    for (const w of writes) {
      const path = `${w.collection}/${w.doc_id}`;
      checkPath(path);
      let data = w.data;
      if (w.file_path) data = JSON.parse(await readFile(w.file_path, 'utf8'));
      if ('if_version' in w && w.if_version != null) {
        const have = this.docs.get(path)?.version ?? 0;
        if (have !== Number(w.if_version)) {
          throw err('conflict', `${path} is at version ${have}, not ${w.if_version}: re-read and redo`);
        }
      } else if (w.op !== 'delete' && this.docs.has(path)) {
        // as ArtifactData does: a write over a document it holds names the version it replaces
        throw err('conflict', `${path} already exists and carried no if_version: read it and pin the write`);
      }
      ops.push({ op: w.op, path, data });
    }
    return this.apply(ops);
  }

  apply(ops) {
    for (const { op, path, data } of ops) {
      if (op === 'set' || op === 'update') {
        if (!data || typeof data !== 'object' || Array.isArray(data)) throw err('invalid_argument', 'a document is a JSON object');
        if (JSON.stringify(data).length > 256 * 1024) throw err('invalid_argument', `${path} is over 256 KiB`);
        if (op === 'update' && !this.docs.has(path)) throw err('invalid_argument', `${path} does not exist`);
      } else if (op !== 'delete') {
        throw err('invalid_argument', `unknown op ${op}`);
      }
    }
    const versions = {};
    for (const { op, path, data } of ops) {
      const prev = this.docs.get(path);
      if (op === 'delete') {
        this.docs.delete(path);
        continue;
      }
      const body = op === 'update' ? merge(structuredClone(prev.data), data) : structuredClone(data);
      const version = (prev?.version ?? 0) + 1;
      this.docs.set(path, { data: body, version });
      versions[path] = version;
    }
    this.changed();
    return versions;
  }

  list(collection) {
    const depth = collection.split('/').length + 1;
    return [...this.docs]
      .filter(([p]) => p.startsWith(collection + '/') && p.split('/').length === depth)
      .sort(([a], [b]) => (a < b ? -1 : 1))
      .map(([p, d]) => ({ ...d.data, id: p.split('/').pop(), version: d.version }));
  }

  get(path) {
    const d = this.docs.get(path);
    return d ? { ...d.data, version: d.version } : null;
  }
}

function merge(into, from) {
  for (const [k, v] of Object.entries(from)) {
    into[k] = v && typeof v === 'object' && !Array.isArray(v) && into[k] && typeof into[k] === 'object'
      ? merge(into[k], v) : v;
  }
  return into;
}

function checkPath(path) {
  const parts = String(path).split('/');
  if (parts.length % 2 || parts.some((p) => !/^[A-Za-z0-9_\-.~:@+]+$/.test(p) || p === '.' || p === '..')) {
    throw err('invalid_argument', `${path} is not a document path`);
  }
}

function err(code, message) {
  return { code, message };
}

// ---------------------------------------------------------------- the server
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json' };

/** The skeleton the Artifact host wraps a page in, near enough. */
function skeleton(page, { shim, theme }) {
  return `<!doctype html>
<html lang="en"${theme ? ` data-theme="${theme}"` : ''}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0;font:14px/1.4 system-ui,sans-serif;background:#faf9f7}img{max-width:100%}[hidden]{display:none!important}</style>
</head>
<body>
${shim ? '<script src="__dev/fake-db.js"></script>\n' : ''}${page}
</body>
</html>`;
}

export async function startServer({ port = 4321, dist = DIST, batches = [], quiet = false } = {}) {
  const store = new FakeStore();
  for (const file of batches) await store.batch(JSON.parse(await readFile(file, 'utf8')));

  const server = createServer(async (req, res) => {
    const url = new URL(req.url, 'http://localhost');
    const send = (status, body, type = 'application/json') => {
      res.writeHead(status, { 'content-type': type, 'cache-control': 'no-store' });
      res.end(typeof body === 'string' || Buffer.isBuffer(body) ? body : JSON.stringify(body));
    };
    try {
      if (url.pathname === '/' || url.pathname === '/index.html') {
        const page = await readFile(join(dist, 'index.html'), 'utf8');
        const theme = ['dark', 'light'].includes(url.searchParams.get('theme')) ? url.searchParams.get('theme') : '';
        return send(200, skeleton(page, { shim: !url.searchParams.has('nodb'), theme }), TYPES['.html']);
      }
      if (url.pathname === '/__dev/fake-db.js') {
        return send(200, await readFile(join(here, 'fake-db.js'), 'utf8'), TYPES['.js']);
      }
      if (url.pathname === '/__db/events') {
        res.writeHead(200, { 'content-type': 'text/event-stream', 'cache-control': 'no-store', connection: 'keep-alive' });
        const push = () => res.write(`event: snapshot\ndata: ${JSON.stringify(store.dump())}\n\n`);
        push();
        const off = store.onChange(push);
        req.on('close', off);
        return;
      }
      if (url.pathname === '/__db/dump') return send(200, store.dump());
      if (url.pathname === '/__db/list') return send(200, store.list(url.searchParams.get('collection') ?? ''));
      if (url.pathname === '/__db/get') {
        const doc = store.get(url.searchParams.get('path') ?? '');
        return doc ? send(200, doc) : send(404, err('not_found', 'no such document'));
      }
      if (req.method === 'POST' && (url.pathname === '/__db/write' || url.pathname === '/__db/batch')) {
        const body = JSON.parse(await readBody(req));
        try {
          if (url.pathname === '/__db/write') {
            store.write(body);
            return send(200, { ok: true });
          }
          return send(200, { ok: true, versions: await store.batch(body) });
        } catch (e) {
          return send(e?.code === 'conflict' ? 409 : 400, e?.code ? e : err('invalid_argument', String(e)));
        }
      }
      // the bundles
      const file = normalize(join(dist, url.pathname));
      if (!file.startsWith(dist)) return send(403, 'no');
      const type = TYPES[extname(file)] ?? 'application/octet-stream';
      return send(200, await readFile(file), type);
    } catch (e) {
      if (e?.code === 'ENOENT') return send(404, `not found: ${url.pathname}`, 'text/plain');
      if (!quiet) console.error(e);
      return send(500, String(e), 'text/plain');
    }
  });

  await new Promise((ok, fail) => server.once('error', fail).listen(port, '127.0.0.1', ok));
  const address = `http://127.0.0.1:${server.address().port}/`;
  return {
    url: address,
    store,
    close: () => new Promise((ok) => { server.closeAllConnections?.(); server.close(ok); }),
  };
}

function readBody(req) {
  return new Promise((ok, fail) => {
    let s = '';
    req.on('data', (c) => (s += c));
    req.on('end', () => ok(s));
    req.on('error', fail);
  });
}

// ---------------------------------------------------------------- the command
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  let port = 4321;
  const batches = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--port') port = Number(args[++i]);
    else if (args[i] === '--batch' || args[i] === '--seed') batches.push(args[++i]);
    else {
      console.error(`unknown argument ${args[i]}\nusage: node web/dev/serve.mjs [--port N] [--batch FILE]...`);
      process.exit(2);
    }
  }
  const { url } = await startServer({ port, batches });
  console.log(`The page is at ${url} (fake db; ?nodb, ?readonly, ?theme=dark to vary it).`);
}
