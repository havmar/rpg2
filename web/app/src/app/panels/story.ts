import { Component, computed, inject } from '@angular/core';
import { moveWords } from '../model';
import { TableStore } from '../store';
import { Ui } from '../ui';
import { Prose } from './prose';

/**
 * The DM's last message, set as a reading column: its paragraphs, its
 * displays as printed, its fights as cards where the prose put them, and the
 * player's words it answered. While a fight stands paused, the pause sits
 * under it (the picker is session 4's; until then, the menu as printed).
 */
@Component({
  selector: 'rpg-story',
  imports: [Prose],
  template: `
    <section class="scene" aria-live="polite" aria-label="The DM's last message">
      <p class="eyebrow label">
        @if (entry(); as e) {
          <span>Turn {{ e.turn }}</span>
          @if (eyebrow().day) {<span>Day {{ eyebrow().day }}</span>}
          @if (eyebrow().where) {<span>{{ eyebrow().where }}</span>}
        }
      </p>
      @if (entry(); as e) {
        <rpg-prose class="prose" [prose]="e.prose" [fights]="e.fights" />
        @for (m of e.answered; track m.seq) {
          <p class="yousaid"><span class="who">You</span> {{ words(m) }}</p>
        }
      } @else {
        <p class="note">No scene yet. It appears here once the DM writes it.</p>
      }
    </section>
    @if (pause(); as p) {
      <section id="pause" class="pause" aria-label="The fight is paused">
        <p class="label">PAUSED after round {{ p.round }}@if (p.kind === 'fate') {<span class="fate">Fate</span>}</p>
        @if (p.trips) { <p>{{ p.trips }}</p> }
        <p class="note">Fight on or retreat: say it in the box below.</p>
        @if (p.fight) { <button type="button" class="linkbtn" (click)="ui.openFight(p.fight)">Open the fight</button> }
        <details>
          <summary>The menu, as printed</summary>
          <pre class="display">{{ p.text.join('\\n') }}</pre>
        </details>
      </section>
    }
  `,
  styles: [`
    :host { display: flex; flex-direction: column; gap: 18px; }
    .scene { max-width: 64ch; display: flex; flex-direction: column; gap: 14px; min-width: 0; }
    .eyebrow { display: flex; gap: 0; flex-wrap: wrap; align-items: center; min-height: 1.2em; }
    .eyebrow > span + span::before { content: ""; display: inline-block; width: 4px; height: 4px; border-radius: 50%; background: var(--ink-3); margin: 0 8px; vertical-align: middle; }
    .prose { font-size: 1.1rem; line-height: 1.7; }
    .yousaid { border-left: 2px solid var(--rule); padding-left: 12px; color: var(--ink-2); font-style: italic; overflow-wrap: anywhere; }
    .who { font-family: var(--mono); font-style: normal; font-size: .68rem; letter-spacing: .1em; text-transform: uppercase; color: var(--ink-3); margin-right: 4px; }
    .pause { max-width: 64ch; border: 1px solid var(--accent); border-left-width: 4px; background: var(--accent-soft); border-radius: 4px; padding: 12px 14px; display: flex; flex-direction: column; gap: 8px; min-width: 0; }
    .pause .label { color: var(--accent); }
    .fate { margin-left: 8px; border: 1px solid var(--accent); border-radius: 3px; padding: 0 5px; }
    .linkbtn { align-self: flex-start; min-height: 44px; border: 0; background: none; padding: 0; font-family: var(--mono); font-size: .78rem; color: var(--accent); letter-spacing: .06em; text-transform: uppercase; }
    @media (max-width: 900px) { .prose { font-size: 1.04rem; } }
  `],
})
export class Story {
  private readonly store = inject(TableStore);
  readonly ui = inject(Ui);
  readonly entry = this.store.latest;
  readonly words = moveWords;

  /** The pause, while it stands and the game goes on. */
  readonly pause = computed(() => {
    const s = this.store.state();
    return s && s.status !== 'ended' ? s.pause : null;
  });

  /** The last message's day and place, only when they are not the header's. */
  readonly eyebrow = computed(() => {
    const e = this.entry();
    const s = this.store.state();
    return {
      day: e && s && e.day !== s.day ? e.day : 0,
      where: e && s && e.where !== s.where ? e.where : '',
    };
  });
}
