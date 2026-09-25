import { Component, computed, inject } from '@angular/core';
import { Quest } from '../model';
import { TableStore } from '../store';

/**
 * The jobs in hand, a card each: the name, level and giver's settlement; the
 * sites with how far the party has got; the road; the due day and how it
 * stands; a delivery's cargo and where it goes; and the job as the map page
 * prints it. Only jobs taken appear -- the board is the DM's.
 */
@Component({
  selector: 'rpg-quests',
  template: `
    <div class="sub">
      <h2>Jobs in hand</h2>
      @if (quests().length) { <span class="label">{{ quests().length }} taken</span> }
    </div>
    @for (q of quests(); track q.id) {
      <article class="card" [attr.data-quest]="q.id" [class.active]="q.id === active()">
        <header>
          <h3>{{ q.name }}</h3>
          @if (q.level !== null) { <span class="lvl num">L{{ q.level }}</span> }
        </header>
        <p class="tags">
          @if (q.id === active()) { <span class="tag on">active</span> }
          @if (status(q); as s) { <span class="tag" [class]="q.status">{{ s }}</span> }
          @if (q.kind === 'delivery') { <span class="tag">delivery</span> }
          <span class="tag">{{ q.id }}</span>
        </p>
        @if (q.origin) { <p class="note">Taken at {{ q.origin }}</p> }
        <dl>
          @if (q.cargo) { <dt>Cargo</dt><dd>{{ q.cargo }}</dd> }
          @if (q.dest) { <dt>To</dt><dd>{{ q.dest }}</dd> }
          @for (s of q.sites; track $index) {
            <dt>Site</dt><dd>{{ s.name }} (L{{ s.level }})@if (s.mark) {<span class="mark">{{ s.mark }}</span>}</dd>
          }
          @if (q.road) { <dt>Road</dt><dd>{{ q.road }}</dd> }
          @if (q.due !== null) { <dt>Due</dt><dd>day {{ q.due }}@if (q.note) {<span class="mark" [class.late]="late(q)">{{ q.note }}</span>}</dd> }
          @else if (q.note) { <dt>Due</dt><dd>{{ q.note }}</dd> }
        </dl>
        <details class="fold">
          <summary>The job, as printed</summary>
          <pre class="display">{{ q.lines.join('\\n') }}</pre>
        </details>
      </article>
    } @empty {
      <p class="note">No job in hand.</p>
    }
  `,
  styles: [`
    :host { display: flex; flex-direction: column; gap: 14px; min-width: 0; }
    .sub { display: flex; justify-content: space-between; align-items: baseline; gap: 6px 10px; flex-wrap: wrap; }
    .card { border: 1px solid var(--rule); border-radius: 6px; background: var(--paper); padding: 12px 14px; display: flex; flex-direction: column; gap: 8px; min-width: 0; }
    .card.active { border-left: 3px solid var(--accent); }
    header { display: flex; align-items: baseline; gap: 8px; }
    h3 { font-family: var(--mono); font-size: 1.02rem; font-weight: 600; overflow-wrap: anywhere; min-width: 0; }
    .lvl { margin-left: auto; font-weight: 600; }
    .tags { display: flex; gap: 6px; flex-wrap: wrap; }
    .tag.on { border-color: var(--accent); color: var(--accent); }
    .tag.work_done { border-color: var(--good); color: var(--good); }
    .tag.proof_pending { border-color: var(--warn); color: var(--warn); }
    dl { margin: 0; display: grid; grid-template-columns: 3.6em minmax(0, 1fr); gap: 6px 10px; font-size: .92rem; }
    dt { font-family: var(--mono); font-size: .7rem; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-3); padding-top: 3px; }
    dd { margin: 0; overflow-wrap: anywhere; }
    .mark { display: block; font-family: var(--mono); font-size: .78rem; color: var(--ink-2); }
    .mark.late { color: var(--hurt); }
    .card pre.display { background: none; border: 0; padding: 0 0 4px; }
  `],
})
export class Quests {
  private readonly store = inject(TableStore);
  readonly quests = computed(() => this.store.quests()?.quests ?? []);
  readonly active = computed(() => this.store.quests()?.active ?? null);

  status(q: Quest): string {
    return q.status === 'work_done' ? 'work done: turn it in' : q.status === 'proof_pending' ? 'proof pending' : '';
  }

  late(q: Quest): boolean {
    return /late|lost|overdue/i.test(q.note);
  }
}
