import { Injectable, computed, effect, inject, signal } from '@angular/core';
import { TableStore } from './store';
import { Ui } from './ui';

const SEEN_KEY = 'rpg2.seen';

/**
 * Unread marks: a tab whose content changed since this viewer last had it in
 * front of them. Each tab has a signature of what it shows; the one last seen
 * is kept per viewer in localStorage, as a convenience only. Without storage
 * the marks last for the visit. A tab never seen before adopts what it shows,
 * so a first visit is not all marks. A new tab needs a line in `signatures`.
 */
@Injectable({ providedIn: 'root' })
export class Unread {
  private readonly store = inject(TableStore);
  private readonly ui = inject(Ui);

  /** What each tab shows, as a short signature; '' until its document has loaded. */
  readonly signatures = computed<Record<string, string>>(() => {
    const s = this.store;
    const fights = s.fights();
    return {
      party: sign(s.party()),
      fight: s.state()?.lastFight ?? '',
      fights: fights.length ? `${fights.length}:${fights.at(-1)!.id}` : '',
    };
  });

  private readonly seen = signal<Record<string, string>>(load());

  constructor() {
    effect(() => {
      const sigs = this.signatures();
      const looking = this.ui.looking();
      const seen = this.seen();
      let next: Record<string, string> | null = null;
      for (const [id, sig] of Object.entries(sigs)) {
        if (!sig || seen[id] === sig) continue;
        if (seen[id] === undefined || looking.includes(id)) (next ??= { ...seen })[id] = sig;
      }
      if (next) {
        this.seen.set(next);
        save(next);
      }
    });
  }

  /** Whether a tab changed since the viewer last looked at it. */
  readonly marks = computed<Set<string>>(() => {
    const seen = this.seen();
    const out = new Set<string>();
    for (const [id, sig] of Object.entries(this.signatures())) {
      if (sig && seen[id] !== undefined && seen[id] !== sig) out.add(id);
    }
    return out;
  });
}

/** A short hash of a document: it changed, or it did not. */
function sign(doc: unknown): string {
  if (!doc) return '';
  const text = JSON.stringify(doc);
  let h = 5381;
  for (let i = 0; i < text.length; i++) h = ((h << 5) + h + text.charCodeAt(i)) | 0;
  return (h >>> 0).toString(36) + ':' + text.length;
}

function load(): Record<string, string> {
  try {
    const raw = JSON.parse(localStorage.getItem(SEEN_KEY) ?? '{}');
    const out: Record<string, string> = {};
    if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
      for (const [k, v] of Object.entries(raw)) if (typeof v === 'string') out[k] = v;
    }
    return out;
  } catch {
    return {};
  }
}

function save(seen: Record<string, string>): void {
  try {
    localStorage.setItem(SEEN_KEY, JSON.stringify(seen));
  } catch {
    /* the marks are a convenience; they last for the visit */
  }
}
