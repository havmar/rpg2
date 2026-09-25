import { Component, computed, inject, input } from '@angular/core';
import { outcomeClass, outcomeWords } from '../model';
import { TableStore } from '../store';
import { Ui } from '../ui';

/**
 * A fight inside a turn, as a card where the prose put it: "a fight: 2x Wolf
 * -- fangs, won", or "the fight goes on: ..." for a paused fight's second
 * half. It opens the Fight tab on that fight.
 */
@Component({
  selector: 'rpg-fight-chip',
  template: `
    <button type="button" class="fightchip" [attr.data-fight]="id()" (click)="ui.openFight(id())"
      [attr.aria-label]="'Open the fight: ' + words()">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 19L19 5M14 5h5v5M5 5l14 14M5 14v5h5" /></svg>
      <span class="what">{{ lead() }}: {{ fight()?.title ?? id() }}@if (fight(); as f) {, <b [class]="cls()">{{ tail() }}</b>}</span>
    </button>
  `,
  styles: [`
    :host { display: block; }
    .fightchip {
      display: flex; gap: 10px; align-items: center; text-align: left; width: 100%; min-height: 48px;
      border: 1px solid var(--rule); border-left: 3px solid var(--accent); background: var(--paper-2); color: var(--ink);
      padding: 8px 12px; border-radius: 4px; font-family: var(--mono); font-size: .8rem; line-height: 1.45;
    }
    .fightchip:hover { border-color: var(--accent); }
    svg { width: 18px; height: 18px; flex: none; fill: none; stroke: var(--accent); stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
    .what { overflow-wrap: anywhere; min-width: 0; }
    b { font-weight: 600; }
    .won { color: var(--good); }
    .lost { color: var(--hurt); }
    .paused { color: var(--accent); }
    .off { color: var(--warn); }
  `],
})
export class FightChip {
  readonly ui = inject(Ui);
  private readonly store = inject(TableStore);
  readonly id = input.required<string>();

  readonly fight = computed(() => this.store.fightById().get(this.id()) ?? null);
  readonly lead = computed(() => (this.fight()?.continues ? 'the fight goes on' : 'a fight'));
  readonly tail = computed(() => {
    const f = this.fight();
    return f ? outcomeWords(f) : '';
  });
  readonly cls = computed(() => {
    const f = this.fight();
    return f ? outcomeClass(f.outcome) : '';
  });
  readonly words = computed(() => [this.fight()?.title ?? this.id(), this.tail()].filter(Boolean).join(', '));
}
