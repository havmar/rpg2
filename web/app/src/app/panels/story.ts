import { Component, computed, inject } from '@angular/core';
import { moveWords } from '../model';
import { TableStore } from '../store';
import { Ui } from '../ui';
import { Pause } from './pause';
import { Prose } from './prose';

/**
 * The DM's last message, set as a reading column: its paragraphs, its
 * displays as printed, its fights as cards where the prose put them, and the
 * player's words it answered; an `options:` display carries chips that put
 * an option's words in the answer box. While a fight stands paused, the
 * pause picker (panels/pause.ts) sits under it.
 */
@Component({
  selector: 'rpg-story',
  imports: [Prose, Pause],
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
        <rpg-prose class="prose" [prose]="e.prose" [fights]="e.fights" [chips]="canAnswer()" />
        @for (m of e.answered; track m.seq) {
          <p class="yousaid"><span class="who">You</span> {{ words(m) }}</p>
        }
      } @else {
        <p class="note">No scene yet. It appears here once the DM writes it.</p>
      }
    </section>
    <rpg-pause />
  `,
  styles: [`
    :host { display: flex; flex-direction: column; gap: 18px; }
    .scene { max-width: 64ch; display: flex; flex-direction: column; gap: 14px; min-width: 0; }
    .eyebrow { display: flex; gap: 0; flex-wrap: wrap; align-items: center; min-height: 1.2em; }
    .eyebrow > span + span::before { content: ""; display: inline-block; width: 4px; height: 4px; border-radius: 50%; background: var(--ink-3); margin: 0 8px; vertical-align: middle; }
    .prose { font-size: 1.1rem; line-height: 1.7; }
    .yousaid { border-left: 2px solid var(--rule); padding-left: 12px; color: var(--ink-2); font-style: italic; overflow-wrap: anywhere; }
    .who { font-family: var(--mono); font-style: normal; font-size: .68rem; letter-spacing: .1em; text-transform: uppercase; color: var(--ink-3); margin-right: 4px; }
    @media (max-width: 900px) { .prose { font-size: 1.04rem; } }
  `],
})
export class Story {
  private readonly store = inject(TableStore);
  readonly ui = inject(Ui);
  readonly entry = this.store.latest;
  readonly words = moveWords;

  /** Whether the player can answer now: the option chips only show then. */
  readonly canAnswer = computed(() =>
    this.store.link() === 'live' && !this.store.readOnly() && this.store.state()?.status !== 'ended');

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
