import { Component, computed, input } from '@angular/core';
import { Block, proseBlocks } from '../model';
import { FightChip } from './fight-chip';

/** A run of text, marked where it matches the search. */
interface Run { text: string; hit: boolean; }

/**
 * A DM turn's prose as the page sets it, for the story and the chronicle
 * alike: paragraphs; each fenced display as printed, in mono at 40 columns;
 * each `[fight]` paragraph as the card of the turn's next fight, in place;
 * fights no marker placed after the prose (model.ts, proseBlocks).
 */
@Component({
  selector: 'rpg-prose',
  imports: [FightChip],
  template: `
    @for (b of shown(); track $index) {
      @switch (b.kind) {
        @case ('p') {
          <p>@for (r of runs(b.text); track $index) {@if (r.hit) {<mark>{{ r.text }}</mark>} @else {<ng-container>{{ r.text }}</ng-container>}}</p>
        }
        @case ('display') { <pre class="display">{{ b.lines.join('\\n') }}</pre> }
        @case ('fight') { <rpg-fight-chip [id]="b.id" /> }
      }
    }
    @if (cut()) { <p class="more">...</p> }
  `,
  styles: [`
    :host { display: flex; flex-direction: column; gap: 1em; min-width: 0; }
    p { overflow-wrap: anywhere; }
    .more { color: var(--ink-3); font-family: var(--mono); font-size: .8rem; }
    mark { background: var(--accent-soft); color: inherit; }
  `],
})
export class Prose {
  readonly prose = input.required<string>();
  readonly fights = input<readonly string[]>([]);
  /** Only the first paragraph (the chronicle's line for the message set in full above). */
  readonly short = input(false);
  /** Lower-case words to mark. */
  readonly needle = input('');

  readonly blocks = computed<Block[]>(() => proseBlocks(this.prose(), this.fights()));

  readonly shown = computed<Block[]>(() => {
    const all = this.blocks();
    if (!this.short()) return all;
    const first = all.find((b) => b.kind === 'p');
    return first ? [first] : all.slice(0, 1);
  });

  readonly cut = computed(() => this.short() && this.shown().length < this.blocks().length);

  runs(text: string): Run[] {
    const needle = this.needle();
    if (!needle) return [{ text, hit: false }];
    const out: Run[] = [];
    const lower = text.toLowerCase();
    let at = 0;
    for (let i = lower.indexOf(needle); i >= 0; i = lower.indexOf(needle, at)) {
      if (i > at) out.push({ text: text.slice(at, i), hit: false });
      out.push({ text: text.slice(i, i + needle.length), hit: true });
      at = i + needle.length;
    }
    if (at < text.length) out.push({ text: text.slice(at), hit: false });
    return out;
  }
}
