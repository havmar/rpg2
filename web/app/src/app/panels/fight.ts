import { Component, computed, inject, signal } from '@angular/core';
import { Fight as FightDoc, FightBlock, outcomeClass, outcomeWords } from '../model';
import { TableStore } from '../store';
import { Ui } from '../ui';

/** One printed line, with a class for its colour only. */
interface Line { text: string; cls: string; }
/** A round: its header line ("Round 2:"), and the lines under it. */
interface Round { head: Line | null; lines: Line[]; }
/** A block as the page sets it: plain lines, or rounds that fold. */
interface Part { kind: FightBlock['kind']; lines: Line[]; rounds: Round[]; }

const ROUND = /^Round (\d+)(?:-(\d+))?:/;

/**
 * The fight: its day, place, outcome and rounds, then the player log exactly
 * as the engine printed it (ui/fight-short.txt), block by block. The rounds
 * fold, the newest open. Lines are coloured by what they say (a kill, a hero
 * down, a warning, a big hit) and never reworded. A second half shows the
 * paused first half above it, folded; a paused fight points to the pause.
 * Opens on the fight a card or a row chose, else the newest.
 */
@Component({
  selector: 'rpg-fight',
  template: `
    @if (fight(); as f) {
      <div class="sub label">
        <span>Day {{ f.day }}</span>@if (f.coord) {<span>{{ f.coord }}</span>}
        <span class="outcome" [class]="cls(f)">{{ words(f) }}</span>
        <span>{{ f.rounds }} round{{ f.rounds === 1 ? '' : 's' }}</span>
      </div>
      <h2>{{ f.title }}</h2>
      @if (f.where) { <p class="note where">{{ f.where }}</p> }
      @if (all().length > 1) {
        <nav class="step" aria-label="Other fights">
          <button type="button" [disabled]="!prev()" (click)="go(prev())">&lt; Earlier</button>
          <span class="label">{{ index() + 1 }} of {{ all().length }}</span>
          <button type="button" [disabled]="!next()" (click)="go(next())">Later &gt;</button>
        </nav>
      }

      @if (pausedHere()) {
        <div class="paused">
          <p><b>PAUSED after round {{ f.rounds }}</b></p>
          <button type="button" class="act" (click)="ui.openPause()">To the pause</button>
        </div>
      }

      @if (firstHalf(); as h) {
        <details class="first fold">
          <summary>The first half: {{ words(h.fight) }}</summary>
          <div class="log half">
            @for (p of h.parts; track $index) {
              <div class="display block" [attr.data-block]="p.kind">@for (l of p.lines; track $index) {<span class="ln" [class]="l.cls">{{ l.text }}</span>}</div>
            }
          </div>
        </details>
      }

      @if (roundCount() > 1) {
        <button type="button" class="linkbtn" (click)="allOpen.set(!allOpen())">{{ allOpen() ? 'Fold the rounds' : 'Open every round' }}</button>
      }
      <div class="log main" [attr.data-fight]="f.id">
        @for (p of parts(); track $index; let pi = $index) {
          @if (p.kind === 'rounds') {
            @for (r of p.rounds; track $index; let ri = $index) {
              @if (r.head) {
                <details class="round" [open]="allOpen() || isNewest(pi, ri)">
                  <summary class="display"><span class="ln rh">{{ r.head.text }}</span></summary>
                  <div class="display block">@for (l of r.lines; track $index) {<span class="ln" [class]="l.cls">{{ l.text }}</span>}</div>
                </details>
              } @else {
                <div class="display block">@for (l of r.lines; track $index) {<span class="ln" [class]="l.cls">{{ l.text }}</span>}</div>
              }
            }
          } @else {
            <div class="display block" [attr.data-block]="p.kind">@for (l of p.lines; track $index) {<span class="ln" [class]="l.cls">{{ l.text }}</span>}</div>
          }
        }
      </div>

      @if (goesOn(); as g) {
        <button type="button" class="linkbtn" (click)="go(g)">The fight goes on &gt;</button>
      }
      <button type="button" class="linkbtn" (click)="ui.open('fights')">Every fight &gt;</button>
    } @else {
      <h2>The last fight</h2>
      <p class="note">No fight yet. When there is one, it is here as the game printed it, round by round.</p>
    }
  `,
  styles: [`
    :host { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
    .sub { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 0; }
    .sub > span + span::before { content: ""; display: inline-block; width: 4px; height: 4px; border-radius: 50%; background: var(--ink-3); margin: 0 8px; vertical-align: middle; }
    .outcome.won { color: var(--good); } .outcome.lost { color: var(--hurt); }
    .outcome.paused { color: var(--accent); } .outcome.off { color: var(--warn); }
    h2 { overflow-wrap: anywhere; text-transform: none; letter-spacing: .02em; font-size: 1.05rem; }
    .where { overflow-wrap: anywhere; }
    .step { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
    .step button, .linkbtn {
      border: 0; background: none; min-height: 48px; padding: 0 2px; font-family: var(--mono); font-size: .78rem;
      color: var(--accent); letter-spacing: .06em; text-transform: uppercase;
    }
    .step button:disabled { color: var(--ink-3); cursor: default; }
    .linkbtn { align-self: flex-start; }
    .paused { border: 1px solid var(--accent); border-left-width: 4px; background: var(--accent-soft); border-radius: 4px; padding: 10px 12px; display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; font-family: var(--mono); font-size: .85rem; }
    .act { border: 0; background: var(--accent); color: var(--on-accent); min-height: 48px; padding: 0 16px; border-radius: 4px; font-family: var(--mono); font-size: .8rem; font-weight: 600; }
    .first { border: 1px dashed var(--rule); border-radius: 4px; padding: 0 10px; }
    .first > summary { cursor: pointer; min-height: 48px; display: flex; align-items: center; font-family: var(--mono); font-size: .8rem; color: var(--ink-2); }
    .log { display: flex; flex-direction: column; gap: 10px; min-width: 0; }
    .half { padding-bottom: 10px; }
    .block { overflow-x: auto; }
    .ln { display: block; min-height: 1.45em; }
    .round > summary { cursor: pointer; list-style: none; min-height: 40px; display: flex; align-items: center; border-bottom: 1px solid var(--rule); }
    .round > summary::-webkit-details-marker { display: none; }
    .round > summary::before { content: ""; flex: none; width: 0; height: 0; margin-right: 8px; border-style: solid; border-width: 5px 0 5px 7px; border-color: transparent transparent transparent var(--ink-3); transition: transform .15s; }
    .round[open] > summary::before { transform: rotate(90deg); }
    .round > .block { padding: 6px 0 4px; }
    .rh { font-weight: 600; color: var(--ink); }
    .slain { color: var(--accent); font-weight: 600; }
    .down { color: var(--hurt); font-weight: 600; }
    .warn { color: var(--warn); }
    .hit { color: var(--ink); font-weight: 600; }
  `],
})
export class Fight {
  readonly ui = inject(Ui);
  private readonly store = inject(TableStore);
  readonly all = this.store.fights;
  readonly allOpen = signal(false);

  readonly fight = computed<FightDoc | null>(() => {
    const all = this.all();
    const id = this.ui.fight();
    return (id && all.find((f) => f.id === id)) || all[all.length - 1] || null;
  });

  readonly index = computed(() => {
    const f = this.fight();
    return f ? this.all().indexOf(f) : -1;
  });
  readonly prev = computed(() => this.all()[this.index() - 1]?.id ?? null);
  readonly next = computed(() => {
    const i = this.index();
    return i >= 0 ? this.all()[i + 1]?.id ?? null : null;
  });

  readonly parts = computed<Part[]>(() => toParts(this.fight()?.blocks ?? []));
  readonly roundCount = computed(() => this.parts().reduce((n, p) => n + p.rounds.filter((r) => r.head).length, 0));

  /** Where the newest round sits: [part, round]. */
  private readonly newest = computed<[number, number]>(() => {
    const parts = this.parts();
    for (let pi = parts.length - 1; pi >= 0; pi--) {
      const rs = parts[pi].rounds;
      for (let ri = rs.length - 1; ri >= 0; ri--) if (rs[ri].head) return [pi, ri];
    }
    return [-1, -1];
  });

  isNewest(pi: number, ri: number): boolean {
    const [p, r] = this.newest();
    return p === pi && r === ri;
  }

  /** The paused first half of a second half, folded above it. */
  readonly firstHalf = computed(() => {
    const id = this.fight()?.continues;
    const first = id ? this.store.fightById().get(id) : null;
    return first ? { fight: first, parts: toParts(first.blocks) } : null;
  });

  /** The second half of this fight, once it is on the page. */
  readonly goesOn = computed(() => {
    const f = this.fight();
    return (f && this.all().find((x) => x.continues === f.id)?.id) || null;
  });

  /** This fight is the one the game stands paused on. */
  readonly pausedHere = computed(() => {
    const f = this.fight();
    const s = this.store.state();
    return !!f && f.outcome === 'paused' && !!s && s.status !== 'ended' && s.pause?.fight === f.id && !this.goesOn();
  });

  go(id: string | null): void {
    if (id) {
      this.ui.fight.set(id);
      this.allOpen.set(false);
    }
  }

  words(f: FightDoc): string {
    return outcomeWords(f);
  }

  cls(f: FightDoc): string {
    return outcomeClass(f.outcome);
  }
}

function toParts(blocks: FightBlock[]): Part[] {
  return blocks.map((b) => {
    const lines = b.lines.map(line);
    if (b.kind !== 'rounds') return { kind: b.kind, lines, rounds: [] };
    const rounds: Round[] = [];
    for (const l of lines) {
      if (ROUND.test(l.text)) rounds.push({ head: { ...l, cls: 'rh' }, lines: [] });
      else if (rounds.length) rounds[rounds.length - 1].lines.push(l);
      else rounds.push({ head: null, lines: [l] });
    }
    return { kind: b.kind, lines, rounds };
  });
}

/** A line's colour, read off what it says; the words are never changed. */
function line(text: string): Line {
  let cls = '';
  if (/\bSLAIN\b/.test(text)) cls = 'slain';
  else if (/\bDOWN\b/.test(text)) cls = 'down';
  else if (/^!! /.test(text)) cls = 'warn';
  else if (/dmg!+/.test(text)) cls = 'hit';
  return { text, cls };
}
