import { Injectable, computed, signal } from '@angular/core';
import { DRAWER_TABS, MORE_TABS } from './drawer/tabs';

/** Where the phone is looking: the story, the party, or the drawer's tab. */
export type View = 'story' | 'party' | 'drawer';

/**
 * Page-local state shared by the shell and its panels: the selected drawer
 * tab, the phone's view, the width band, a coarse clock, the fight on show and
 * words an option chip hands the answer box. Nothing here is written to the
 * store; the tab is remembered per viewer in localStorage.
 */
@Injectable({ providedIn: 'root' })
export class Ui {
  /** The drawer's tab: 'party' (only offered below the three-zone width) or a tab id. */
  readonly tab = signal<string>(remembered() ?? DRAWER_TABS[0].id);
  /** The tab More opens on the phone: the last one of its tabs looked at. */
  readonly moreTab = signal<string>(
    MORE_TABS.some((t) => t.id === remembered()) ? remembered()! : (MORE_TABS[0] ?? DRAWER_TABS[0]).id,
  );
  readonly view = signal<View>('story');
  /** Three zones: the party, the page and the drawer side by side. */
  readonly wide = media('(min-width: 1241px)');
  /** Phones: one zone at a time, with the bottom bar. */
  readonly narrow = media('(max-width: 900px)');
  /** Minute-ish ticks, for "the DM looks in about 5 min". */
  readonly now = signal(Date.now());
  /** Set by the chronicle's search box. */
  readonly search = signal('');
  /** The fight the Fight tab shows; null: the newest. */
  readonly fight = signal<string | null>(null);
  /**
   * Words for the answer box (an option chip's): the box takes them, focuses,
   * and clears this. Nothing is ever sent by it. n makes each ask new.
   */
  readonly prefill = signal<{ text: string; n: number } | null>(null);

  /** The drawer tab on show. */
  readonly drawerTab = computed(() => {
    let id = this.tab();
    if (id === 'party' && this.wide()) id = DRAWER_TABS[0].id;
    return id === 'party' || DRAWER_TABS.some((t) => t.id === id) ? id : DRAWER_TABS[0].id;
  });

  /** What the viewer has in front of them: the tabs to count as read. */
  readonly looking = computed<string[]>(() => {
    if (this.wide()) return ['party', this.drawerTab()];
    if (!this.narrow()) return [this.drawerTab()];
    const view = this.view();
    return view === 'party' ? ['party'] : view === 'drawer' ? [this.drawerTab()] : [];
  });

  constructor() {
    setInterval(() => this.now.set(Date.now()), 20_000);
  }

  /** Open the Fight tab on one fight (a card in the story, a row of the fights). */
  openFight(id: string): void {
    this.fight.set(id);
    this.open('fight');
    if (typeof window !== 'undefined' && this.narrow()) window.scrollTo({ top: 0 });
  }

  /** Back to the story, at the pause (the picker, from session 4). */
  openPause(): void {
    this.view.set('story');
    setTimeout(() => document.getElementById('pause')?.scrollIntoView({ block: 'start' }), 30);
  }

  /** Hand the answer box some words; it never sends them. */
  fill(text: string): void {
    this.prefill.set({ text, n: (this.prefill()?.n ?? 0) + 1 });
    this.view.set('story');
  }

  /** The phone's More button: the last of its tabs looked at. */
  openMore(): void {
    this.open(this.moreTab());
  }

  open(tab: string): void {
    if (MORE_TABS.some((t) => t.id === tab)) this.moreTab.set(tab);
    this.tab.set(tab);
    this.view.set(tab === 'party' ? 'party' : 'drawer');
    try {
      localStorage.setItem(TAB_KEY, tab);
    } catch {
      /* storage may be blocked; the tab is a convenience */
    }
  }
}

const TAB_KEY = 'rpg2.tab';

function remembered(): string | null {
  try {
    const tab = localStorage.getItem(TAB_KEY);
    return tab && (tab === 'party' || DRAWER_TABS.some((t) => t.id === tab)) ? tab : null;
  } catch {
    return null;
  }
}

function media(query: string) {
  const s = signal(false);
  if (typeof matchMedia === 'function') {
    const mq = matchMedia(query);
    s.set(mq.matches);
    mq.addEventListener('change', (e) => s.set(e.matches));
  }
  return s.asReadonly();
}
