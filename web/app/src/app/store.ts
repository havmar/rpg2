import { Injectable, Signal, computed, signal } from '@angular/core';
import {
  ChronicleEntry, Fight, Move, MoveBody, PATHS, cleanBody, moveId,
  readChronicle, readFight, readMove, readParty, readState,
} from './model';

/**
 * The db bridge: the one place the page touches the artifact's store.
 *
 * Ported from dream's store (itself from havmar/scratch's vault.store.ts).
 * Every document or query is subscribed ONCE, for the life of the page (never
 * from render or from a snapshot callback), and parsed into a signal. Writes
 * go one at a time onto a promise queue. The page only ever creates
 * `moves/mNNNN`; everything else is the keeper's, written with
 * `python publish.py` and an ArtifactData batch.
 *
 * To read a new document or collection, add one line below:
 *
 *   readonly map = this.doc(PATHS.map, readMap);
 *
 * `doc()` and `collection()` register the subscription; `connect()` opens them
 * all (and anything registered later opens at once).
 */

// ---------------------------------------------------------------- the runtime surface we call
interface DbSnapshot { id: string; exists: boolean; data(): Record<string, unknown> | undefined; }
interface DbQuerySnapshot { docs: DbSnapshot[]; }
export interface DbError { code: string; message: string; }
type Unsubscribe = () => void;
interface DbQuery {
  orderBy(field: string, dir?: 'asc' | 'desc'): DbQuery;
  limit(n: number): DbQuery;
  onSnapshot(next: (s: DbQuerySnapshot) => void, error?: (e: DbError) => void): Unsubscribe;
}
interface DbDoc {
  set(data: Record<string, unknown>): Promise<void>;
  onSnapshot(next: (s: DbSnapshot) => void, error?: (e: DbError) => void): Unsubscribe;
}
interface Db { doc(path: string): DbDoc; collection(path: string): DbQuery; }
declare const window: Window & { claude?: { use?<T>(name: string): Promise<T | null> } };

/** connecting: waiting on the viewer; live: reading the store; unavailable:
 * no db in this view (outside claude.ai, or not granted); lost: cut mid-visit. */
export type Link = 'connecting' | 'live' | 'unavailable' | 'lost';

export interface CollectionOptions {
  /** A top-level field to order by; without it, document id order. */
  orderBy?: string;
  dir?: 'asc' | 'desc';
  /** At most this many documents (the store allows 1-1000). */
  limit?: number;
}

@Injectable({ providedIn: 'root' })
export class TableStore {
  // Declared first: the subscriptions below register into them as fields initialise.
  private db: Db | null = null;
  private readonly openers = new Map<string, (db: Db) => void>();
  private writeQueue: Promise<unknown> = Promise.resolve();

  readonly link = signal<Link>('connecting');
  /** A refused write: this viewer may read the game but not write to it. */
  readonly readOnly = signal(false);
  readonly sending = signal(false);
  /** The last write that failed for a reason the player should see. */
  readonly writeError = signal<string | null>(null);

  // ------------------------------------------------------------ the keeper's documents
  readonly state = this.doc(PATHS.state, readState);
  readonly party = this.doc(PATHS.party, readParty);
  /** Every chronicle entry, oldest first (newest 1000 read). */
  readonly chronicle = this.collection<ChronicleEntry>(PATHS.chronicle, readChronicle, {
    orderBy: 'turn', dir: 'desc', limit: 1000, sortBy: (a, b) => a.turn - b.turn,
  });
  /** Every fight, oldest first (id order is fight order). */
  readonly fights = this.collection<Fight>(PATHS.fights, readFight, {
    limit: 1000, sortBy: (a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0),
  });

  /** The fights by id, for the cards in the story and the chronicle. */
  readonly fightById = computed(() => new Map(this.fights().map((f) => [f.id, f] as const)));

  // ------------------------------------------------------------ the page's documents
  /**
   * Every document in `moves/`, with the seq its id or body claims: a
   * malformed one is no move, but its seq still counts for the next one, so
   * the page never writes over it.
   */
  private readonly moveDocs = this.collection<{ seq: number; move: Move | null }>(
    PATHS.moves,
    (raw, id) => {
      const body = raw as Record<string, unknown> | undefined;
      const claimed = typeof body?.['seq'] === 'number' ? (body['seq'] as number) : 0;
      const seq = Math.max(Number.isFinite(claimed) ? claimed : 0, Number(id.replace(/\D/g, '')) || 0);
      return { seq, move: readMove(raw) };
    },
    { limit: 400 },
  );

  /** Moves still in the store: the keeper deletes each once it is answered. */
  readonly moves = computed<Move[]>(() =>
    this.moveDocs().flatMap((d) => (d.move ? [d.move] : [])));

  /** Moves sent and not yet answered, oldest first. */
  readonly pending = computed<Move[]>(() => {
    const last = this.state()?.lastSeq ?? 0;
    return this.moves().filter((m) => m.seq > last).sort((a, b) => a.seq - b.seq);
  });

  /** True while the DM owes the player a turn. */
  readonly awaitingDm = computed(() => {
    const state = this.state();
    if (!state || state.status === 'ended') return false;
    return state.status === 'dm_thinking' || this.pending().length > 0;
  });

  /** The chronicle entry the DM wrote last. */
  readonly latest = computed<ChronicleEntry | null>(() => {
    const all = this.chronicle();
    const id = this.state()?.latest;
    return (id && all.find((e) => e.id === id)) || all[all.length - 1] || null;
  });

  /** The player's own hero. */
  readonly pc = computed(() => this.party()?.members.find((m) => m.isPc) ?? null);

  // ------------------------------------------------------------ plumbing
  async connect(): Promise<void> {
    let db: Db | null = null;
    try {
      db = (await window.claude?.use?.<Db>('db')) ?? null;
    } catch {
      db = null;
    }
    if (!db) {
      this.link.set('unavailable');
      return;
    }
    this.db = db;
    for (const open of this.openers.values()) open(db);
  }

  /** A singleton document as a signal: null until it exists (or if it is unreadable). */
  doc<T>(path: string, read: (raw: unknown) => T | null): Signal<T | null> {
    const out = signal<T | null>(null);
    this.register(`doc:${path}`, (db) =>
      db.doc(path).onSnapshot(
        (snap) => {
          if (path === PATHS.state) this.link.set('live');
          out.set(snap.exists ? read(snap.data()) : null);
        },
        (err) => this.onDbError(err),
      ),
    );
    return out.asReadonly();
  }

  /** A collection as a signal of parsed documents; unreadable ones are dropped. */
  collection<T>(
    path: string,
    read: (raw: unknown, id: string) => T | null,
    opts: CollectionOptions & { sortBy?: (a: T, b: T) => number } = {},
  ): Signal<T[]> {
    const out = signal<T[]>([]);
    this.register(`collection:${path}`, (db) => {
      let query = db.collection(path);
      if (opts.orderBy) query = query.orderBy(opts.orderBy, opts.dir ?? 'asc');
      query = query.limit(opts.limit ?? 1000);
      return query.onSnapshot(
        (snap) => {
          const docs = snap.docs
            .map((d) => read(d.data(), d.id))
            .filter((x): x is T => x !== null);
          out.set(opts.sortBy ? docs.sort(opts.sortBy) : docs);
        },
        (err) => this.onDbError(err),
      );
    });
    return out.asReadonly();
  }

  private register(key: string, open: (db: Db) => Unsubscribe): void {
    if (this.openers.has(key)) throw new Error(`${key} is subscribed twice`);
    // Keep the handle for the page's life; the page never unsubscribes.
    this.openers.set(key, (db) => void open(db));
    if (this.db) open(this.db);
  }

  /**
   * Send one move of any kind (plan section 2). The store gives it the next
   * seq and writes `moves/mNNNN`. Resolves true once the move is durably
   * stored. A pause move is sent only while that very fight stands paused on
   * the page: with no published fight to point at, the keeper would refuse it.
   */
  send(body: MoveBody): Promise<boolean> {
    const db = this.db;
    const doc = cleanBody(body);
    if (!doc || !db || this.readOnly()) return Promise.resolve(false);
    if (doc.kind === 'pause') {
      const pause = this.state()?.pause;
      if (!pause?.fight || pause.fight !== doc.fight || this.state()?.status === 'ended') {
        return Promise.resolve(false);
      }
    }

    this.sending.set(true);
    this.writeError.set(null);
    // One write at a time: chain onto whatever is already in flight.
    const queued = this.writeQueue.then(async () => {
      const seq = this.nextSeq();
      await db.doc(`${PATHS.moves}/${moveId(seq)}`).set({ ...doc, seq, at: Date.now() });
    });
    this.writeQueue = queued.catch(() => undefined);

    return queued
      .then(() => true)
      .catch((err: DbError) => {
        // A well-formed write refused means this viewer may not write shared
        // data; stop offering the answer box rather than failing again.
        if (err?.code === 'invalid_argument' || err?.code === 'not_granted') {
          this.readOnly.set(true);
        } else if (err?.code === 'quota_exceeded') {
          this.writeError.set('The store is full. The DM has to clear old moves before a new one fits.');
        } else if (err?.code === 'resource_exhausted' || err?.code === 'unavailable') {
          this.writeError.set('That did not go through. Wait a moment and send it again.');
        } else {
          this.onDbError(err);
        }
        return false;
      })
      .finally(() => this.sending.set(false));
  }

  /** The handshake: one past the highest seq either side has seen. */
  private nextSeq(): number {
    const answered = this.state()?.lastSeq ?? 0;
    const queued = this.moveDocs().reduce((hi, m) => Math.max(hi, m.seq), 0);
    return Math.max(answered, queued) + 1;
  }

  private onDbError(err: DbError | undefined): void {
    const code = err?.code;
    if (code === 'revoked') {
      this.link.set('lost');
      this.readOnly.set(true);
    } else if (code === 'not_granted' || code === 'capability_disabled' || code === 'capability_removed') {
      this.link.set('unavailable');
    } else {
      this.link.set('lost');
    }
  }
}
