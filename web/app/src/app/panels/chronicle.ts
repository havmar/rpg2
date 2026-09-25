import { Component, computed, inject, signal } from '@angular/core';
import { ChronicleEntry, Move, moveWords, paragraphs } from '../model';
import { TableStore } from '../store';
import { Ui } from '../ui';
import { Prose } from './prose';

type Who = 'dm' | 'you' | 'pending' | 'level';

interface Item {
  key: string;
  who: Who;
  text: string;
  /** The newest DM entry: shown short, since it is set in full above. */
  latest?: boolean;
  /** Ids of the fights in this turn, each a card in place. */
  fights?: string[];
}

interface Day { day: number; places: string[]; items: Item[]; gist: string; }

/** A hero's level rising between two chronicle entries. */
interface LevelUp { entry: string; name: string; level: number; }

/**
 * The chronicle: every DM turn and every player move, grouped by day, newest
 * last, with each level reached as a line of its own (read off the entries'
 * `levels`). Collapsed days show a gist. Moves not yet answered show at the
 * end, waiting on the DM. A search marks what matches.
 */
@Component({
  selector: 'rpg-chronicle',
  imports: [Prose],
  template: `
    <section class="chron" aria-label="The chronicle">
      <div class="head">
        <h2>The chronicle</h2>
        <input id="chronicle-search" type="search" placeholder="Search" aria-label="Search the chronicle"
          [value]="ui.search()" (input)="ui.search.set($any($event.target).value)" />
      </div>
      @for (d of shown(); track d.day) {
        <details class="day" [id]="'day-' + d.day" [open]="isOpen(d.day)" (toggle)="toggled(d.day, $any($event.target).open)">
          <summary><h3>Day {{ d.day }}</h3><span class="gist">{{ d.gist }}</span></summary>
          @if (d.places.length) { <p class="label places">{{ d.places.join(', then ') }}</p> }
          @for (it of d.items; track it.key) {
            <div class="entry" [class]="it.who">
              <span class="who">{{ whoWords[it.who] }}</span>
              <div class="body">
                @if (it.who === 'dm') {
                  <rpg-prose [prose]="it.text" [fights]="it.fights ?? []" [short]="!!it.latest && !needle()" [needle]="needle()" />
                  @if (it.latest && !needle()) { <span class="hint">the last message, in full above</span> }
                } @else {
                  <p>{{ it.text }}</p>
                  @if (it.who === 'pending') { <span class="hint waiting">waiting on the DM</span> }
                }
              </div>
            </div>
          }
        </details>
      } @empty {
        <p class="note">{{ needle() ? 'Nothing matches.' : 'The chronicle begins with the first scene.' }}</p>
      }
    </section>
  `,
  styles: [`
    .chron { max-width: 64ch; display: flex; flex-direction: column; gap: 10px; }
    .head { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; }
    input { border: 1px solid var(--rule); background: var(--paper); color: var(--ink); border-radius: 4px; min-height: 44px; padding: 0 12px; font-family: var(--mono); font-size: .82rem; width: 200px; max-width: 100%; box-sizing: border-box; }
    .day { border-top: 1px solid var(--rule); }
    summary { list-style: none; cursor: pointer; display: flex; gap: 4px 12px; align-items: baseline; padding: 12px 0; min-height: 24px; flex-wrap: wrap; }
    summary::-webkit-details-marker { display: none; }
    summary h3 { min-width: 4.5em; }
    summary h3::before { content: ""; display: inline-block; width: 0; height: 0; margin-right: 8px; vertical-align: 2px; border-style: solid; border-width: 5px 0 5px 7px; border-color: transparent transparent transparent var(--ink-3); transition: transform .15s; }
    .day[open] > summary h3::before { transform: rotate(90deg); }
    .gist { color: var(--ink-2); font-size: .9rem; flex: 1; min-width: 12em; overflow-wrap: anywhere; }
    .places { padding-bottom: 8px; overflow-wrap: anywhere; }
    .entry { display: grid; grid-template-columns: 3.4em minmax(0, 1fr); gap: 10px; padding-bottom: 14px; }
    .who { font-family: var(--mono); font-size: .68rem; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-3); padding-top: 4px; }
    .body { display: flex; flex-direction: column; gap: 6px; overflow-wrap: anywhere; min-width: 0; }
    .you .body, .pending .body { font-style: italic; color: var(--ink-2); }
    .pending .who, .waiting { color: var(--accent); }
    .level .body, .level .who { font-family: var(--mono); font-size: .82rem; color: var(--accent); }
    .hint { font-family: var(--mono); font-style: normal; font-size: .72rem; color: var(--ink-3); }
    @media (max-width: 900px) {
      .entry { grid-template-columns: minmax(0, 1fr); gap: 2px; }
      .who { padding-top: 0; }
    }
  `],
})
export class Chronicle {
  private readonly store = inject(TableStore);
  readonly ui = inject(Ui);

  readonly whoWords: Record<Who, string> = { dm: 'DM', you: 'You', pending: 'Sent', level: 'Level' };
  readonly needle = computed(() => this.ui.search().trim().toLowerCase());

  /** Days the player opened or closed by hand; the rest follow the default. */
  private readonly manual = signal<Map<number, boolean>>(new Map());

  /** Each level reached, on the entry it first shows on. */
  readonly levelUps = computed<LevelUp[]>(() => {
    const was = new Map<string, number>();
    const out: LevelUp[] = [];
    for (const e of this.store.chronicle()) {
      for (const [name, level] of Object.entries(e.levels)) {
        const before = was.get(name);
        if (before !== undefined) {
          for (let l = before + 1; l <= Math.min(level, before + 5); l++) out.push({ entry: e.id, name, level: l });
        }
        was.set(name, level);
      }
    }
    return out;
  });

  readonly days = computed<Day[]>(() => {
    const state = this.store.state();
    const latestId = this.store.latest()?.id;
    const days = new Map<number, Day>();
    const day = (n: number): Day => {
      let d = days.get(n);
      if (!d) days.set(n, (d = { day: n, places: [], items: [], gist: '' }));
      return d;
    };
    const levels = this.levelUps();
    for (const e of this.store.chronicle()) {
      const d = day(e.day);
      if (e.where && d.places.at(-1) !== e.where) d.places.push(e.where);
      d.items.push(...e.answered.map((m) => moveItem(e, m)));
      d.items.push({ key: e.id, who: 'dm', text: e.prose, latest: e.id === latestId, fights: e.fights });
      for (const l of levels) {
        if (l.entry === e.id) d.items.push({ key: `${e.id}.${l.name}.${l.level}`, who: 'level', text: `${l.name} reaches level ${l.level}.` });
      }
    }
    const pending = this.store.pending();
    if (pending.length && state) {
      day(state.day).items.push(...pending.map<Item>((m) => ({ key: `m${m.seq}`, who: 'pending', text: moveWords(m) })));
    }
    const out = [...days.values()].sort((a, b) => a.day - b.day);
    for (const d of out) d.gist = gist(d);
    return out;
  });

  /** The days, cut down to what matches the search. */
  readonly shown = computed<Day[]>(() => {
    const needle = this.needle();
    if (!needle) return this.days();
    return this.days()
      .map((d) => ({ ...d, items: d.items.filter((it) => it.text.toLowerCase().includes(needle)) }))
      .filter((d) => d.items.length);
  });

  private readonly lastDay = computed(() => this.days().at(-1)?.day ?? -1);

  isOpen(day: number): boolean {
    if (this.needle()) return true;
    return this.manual().get(day) ?? day === this.lastDay();
  }

  toggled(day: number, open: boolean): void {
    if (this.needle() || open === this.isOpen(day)) return;
    const next = new Map(this.manual());
    next.set(day, open);
    this.manual.set(next);
  }
}

function moveItem(e: ChronicleEntry, m: Move): Item {
  return { key: `${e.id}.${m.seq}`, who: 'you', text: moveWords(m) };
}

/** A day in a line: the first sentence of its first DM message, and how many fights. */
function gist(d: Day): string {
  const first = d.items.find((it) => it.who === 'dm');
  const fights = d.items.reduce((n, it) => n + (it.fights?.length ?? 0), 0);
  const lead = first ? firstSentence(first.text) : 'Waiting on the DM';
  return fights ? `${lead} -- ${fights === 1 ? 'a fight' : `${fights} fights`}` : lead;
}

function firstSentence(text: string): string {
  const para = paragraphs(text.replace(/```[\s\S]*?(```|$)/g, '')).find((p) => p !== '[fight]') ?? '';
  const m = para.match(/^.{12,}?[.!?](?=\s|$)/);
  const s = m ? m[0] : para;
  return s.length > 90 ? s.slice(0, 88).replace(/\s+\S*$/, '') + ' ...' : s;
}
