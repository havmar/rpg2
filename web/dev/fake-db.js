/**
 * A fake `db` capability for the local table (web/dev/serve.mjs), loaded before
 * the page's bundles. It gives the page `window.claude.use("db")` with the
 * calls the page makes (doc().onSnapshot/get/set/update/delete,
 * collection().orderBy().limit().onSnapshot/get, collection().doc()), backed by
 * the server's in-memory store and kept live over server-sent events.
 *
 * Never published: the real page gets the real capability from claude.ai.
 * `?readonly` refuses every write with `invalid_argument`, as the store does
 * for a view-only viewer.
 */
(function () {
  'use strict';
  const params = new URLSearchParams(location.search);
  const readOnly = params.has('readonly');

  /** path -> {data, version}, as the server last sent it. */
  let docs = {};
  const listeners = new Set();
  let ready;
  const loaded = new Promise((ok) => (ready = ok));

  const events = new EventSource('__db/events');
  events.addEventListener('snapshot', (e) => {
    docs = JSON.parse(e.data);
    ready();
    for (const run of listeners) run();
  });

  const SEGMENT = /^[A-Za-z0-9_\-.~:@+]+$/;
  function parts(path, even) {
    const p = String(path).split('/');
    if (p.some((s) => !SEGMENT.test(s) || s === '.' || s === '..') || (p.length % 2 === 0) !== even) {
      throw new TypeError(`${path} is not a ${even ? 'document' : 'collection'} path (${p.length} segments)`);
    }
    return p;
  }

  function freeze(v) {
    if (v && typeof v === 'object') {
      Object.values(v).forEach(freeze);
      Object.freeze(v);
    }
    return v;
  }

  function docSnap(path) {
    const d = docs[path];
    const data = d ? freeze(structuredClone(d.data)) : undefined;
    return {
      id: path.split('/').pop(),
      exists: !!d,
      data: () => data,
      metadata: { fromCache: false, hasPendingWrites: false },
    };
  }

  /** Call `next` now (soon) and on every change of `key()`. */
  function listen(key, build, next) {
    let last;
    let live = true;
    const run = () => {
      if (!live) return;
      const k = key();
      if (k === last) return;
      last = k;
      next(build());
    };
    listeners.add(run);
    loaded.then(() => setTimeout(run, 0));
    return () => {
      live = false;
      listeners.delete(run);
    };
  }

  async function write(op, path, data) {
    await loaded;
    if (readOnly) throw { code: 'invalid_argument', message: 'this viewer may not write shared data' };
    if (op !== 'delete' && (!data || typeof data !== 'object' || Array.isArray(data))) {
      throw { code: 'invalid_argument', message: 'a document is a JSON object' };
    }
    const res = await fetch('__db/write', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ op, path, data }),
    });
    if (!res.ok) throw await res.json();
  }

  function docRef(path) {
    parts(path, true);
    return {
      id: path.split('/').pop(),
      path,
      get: async () => (await loaded, docSnap(path)),
      set: (data) => write('set', path, data),
      update: (data) => write('update', path, data),
      delete: () => write('delete', path),
      onSnapshot: (next, _error) =>
        listen(() => JSON.stringify(docs[path] ?? null), () => docSnap(path), next),
      collection: (sub) => collectionRef(`${path}/${sub}`),
    };
  }

  function query(path, opts) {
    const depth = path.split('/').length + 1;
    const run = () => {
      let paths = Object.keys(docs)
        .filter((p) => p.startsWith(path + '/') && p.split('/').length === depth)
        .sort();
      if (opts.orderBy) {
        const f = opts.orderBy;
        const sign = opts.dir === 'desc' ? -1 : 1;
        paths.sort((a, b) => {
          const x = docs[a].data[f];
          const y = docs[b].data[f];
          if (x === undefined) return y === undefined ? 0 : 1;   // missing sorts last
          if (y === undefined) return -1;
          return x < y ? -sign : x > y ? sign : 0;
        });
      }
      if (opts.limit) paths = paths.slice(0, opts.limit);
      return paths;
    };
    const snap = () => {
      const list = run().map(docSnap);
      return { docs: list, size: list.length, empty: !list.length, docChanges: () => [], metadata: { fromCache: false, hasPendingWrites: false } };
    };
    return {
      orderBy: (field, dir = 'asc') => query(path, { ...opts, orderBy: field, dir }),
      limit: (n) => {
        if (!(n >= 1 && n <= 1000)) throw { code: 'invalid_argument', message: 'limit is 1-1000' };
        return query(path, { ...opts, limit: n });
      },
      get: async () => (await loaded, snap()),
      onSnapshot: (next, _error) =>
        listen(() => JSON.stringify(run().map((p) => [p, docs[p].version])), snap, next),
    };
  }

  function collectionRef(path) {
    parts(path, false);
    return Object.assign(query(path, {}), {
      path,
      doc: (id) => docRef(`${path}/${id ?? Math.random().toString(36).slice(2, 12)}`),
    });
  }

  const db = Object.freeze({ doc: docRef, collection: collectionRef });
  window.claude = { use: async (name) => (name === 'db' ? db : null) };
  window.__fakeDb = { docs: () => docs };
})();
