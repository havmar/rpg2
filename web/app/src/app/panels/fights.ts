import { Component, computed, inject } from '@angular/core';
import { Fight, outcomeClass, outcomeWords } from '../model';
import { TableStore } from '../store';
import { Ui } from '../ui';

/** Every fight, newest first: the day, the place, the title, how it ended, the rounds. */
@Component({
  selector: 'rpg-fights',
  template: `
    <div class="sub">
      <h2>Every fight</h2>
      @if (all().length) {
        <span class="label tally">@for (w of tally(); track $index) {<span>{{ w }}</span>}</span>
      }
    </div>
    <ul class="list">
      @for (f of shown(); track f.id) {
        <li>
          <button type="button" class="row" [attr.data-fight]="f.id" [class.on]="f.id === current()" (click)="ui.openFight(f.id)">
            <span class="meta label">
              <span>Day {{ f.day }}@if (f.coord) {<span class="sep">{{ f.coord }}</span>}</span>
              <span [class]="cls(f)">{{ words(f) }}</span>
            </span>
            <span class="title">@if (f.continues) {<span class="goes">the fight goes on: </span>}{{ f.title }}</span>
            <span class="facts">{{ f.rounds }} round{{ f.rounds === 1 ? '' : 's' }}@if (place(f); as p) {<span class="sep">{{ p }}</span>}</span>
          </button>
        </li>
      } @empty {
        <li class="note">No fight yet.</li>
      }
    </ul>
  `,
  styles: [`
    :host { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
    .sub { display: flex; justify-content: space-between; align-items: baseline; gap: 6px 10px; flex-wrap: wrap; }
    .tally > span + span::before, .sep::before { content: ""; display: inline-block; width: 4px; height: 4px; border-radius: 50%; background: var(--ink-3); margin: 0 8px; vertical-align: middle; }
    .list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; border-top: 1px solid var(--rule); }
    .row {
      width: 100%; min-height: 56px; text-align: left; border: 0; border-bottom: 1px solid var(--rule); background: none;
      padding: 10px 6px; display: flex; flex-direction: column; gap: 3px; color: var(--ink);
    }
    .row:hover, .row.on { background: var(--paper); }
    .meta { display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap; }
    .title { font-family: var(--mono); font-size: .88rem; overflow-wrap: anywhere; }
    .goes { color: var(--ink-2); }
    .facts { font-family: var(--mono); font-size: .74rem; color: var(--ink-2); overflow-wrap: anywhere; }
    .won { color: var(--good); } .lost { color: var(--hurt); } .paused { color: var(--accent); } .off { color: var(--warn); }
  `],
})
export class Fights {
  readonly ui = inject(Ui);
  private readonly store = inject(TableStore);
  readonly all = this.store.fights;

  readonly shown = computed(() => [...this.all()].reverse());
  readonly current = computed(() => this.ui.fight() ?? this.all().at(-1)?.id ?? null);

  readonly tally = computed(() => {
    const all = this.all();
    const won = all.filter((f) => f.outcome === 'won').length;
    const lost = all.filter((f) => f.outcome === 'lost').length;
    return [`${all.length} fought`, `${won} won`, `${lost} lost`];
  });

  words(f: Fight): string {
    return outcomeWords(f);
  }

  cls(f: Fight): string {
    return outcomeClass(f.outcome);
  }

  /** The settlement, the last part of "Umaia > R17C11 > Dar Aziza". */
  place(f: Fight): string {
    const parts = f.where.split(' > ');
    return parts.length > 2 ? parts.slice(2).join(' > ') : '';
  }
}
