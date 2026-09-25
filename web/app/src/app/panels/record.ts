import { Component, computed, inject } from '@angular/core';
import { TableStore } from '../store';

/**
 * The campaign's record, as ui/history.txt keeps it, in its four sections:
 * QUESTS DONE and REMARKABLE (newest first here), THE TALLY OF SIN as
 * printed, and SUGGESTIONS (what hell advertises today). The whole page as
 * printed sits in a fold at the end.
 */
@Component({
  selector: 'rpg-record',
  template: `
    @if (record(); as r) {
      <h2>The record</h2>
      <section data-section="quests">
        <h3 class="label">Quests done</h3>
        <ul>
          @for (x of quests(); track $index) {
            <li><span class="day num">day {{ x.day }}</span><span class="line">{{ x.line }}</span>@if (x.note) {<span class="note">{{ x.note }}</span>}</li>
          } @empty { <li class="note">No job finished yet.</li> }
        </ul>
      </section>
      <section data-section="remarkable">
        <h3 class="label">Remarkable</h3>
        <ul>
          @for (x of remarkable(); track $index) {
            <li><span class="day num">day {{ x.day }}</span><span class="line">{{ x.line }}</span></li>
          } @empty { <li class="note">Nothing yet.</li> }
        </ul>
      </section>
      <section data-section="tally">
        <h3 class="label">The tally of sin</h3>
        <pre class="display">{{ r.tally.join('\\n') }}</pre>
      </section>
      <section data-section="suggestions">
        <h3 class="label">Suggestions</h3>
        <ul>
          @for (s of r.suggestions; track s.key) {
            <li><span class="line"><b>{{ s.key }}</b> -- {{ s.name }}</span><span class="note">{{ s.line }}</span></li>
          } @empty { <li class="note">Hell is not advertising.</li> }
        </ul>
      </section>
      <details class="fold whole">
        <summary>The history, as printed</summary>
        <pre class="display" id="record-text">{{ r.text.join('\\n') }}</pre>
      </details>
    } @else {
      <h2>The record</h2>
      <p class="note">The record appears here once the game starts.</p>
    }
  `,
  styles: [`
    :host { display: flex; flex-direction: column; gap: 16px; min-width: 0; }
    section { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
    h3.label { font-size: .72rem; border-bottom: 1px solid var(--rule); padding-bottom: 4px; }
    ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
    li { display: flex; flex-direction: column; gap: 1px; overflow-wrap: anywhere; font-size: .94rem; }
    .day { font-size: .72rem; color: var(--ink-3); }
    .line b { font-family: var(--mono); font-weight: 600; font-size: .86rem; }
    li .note { font-size: .86rem; }
    .whole { border-top: 1px solid var(--rule); }
  `],
})
export class RecordTab {
  private readonly store = inject(TableStore);
  readonly record = this.store.record;
  readonly quests = computed(() => [...(this.record()?.quests ?? [])].reverse());
  readonly remarkable = computed(() => [...(this.record()?.remarkable ?? [])].reverse());
}
