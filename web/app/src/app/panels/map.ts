import { Component, computed, inject, signal } from '@angular/core';
import { MapDoc, cellCoord } from '../model';
import { TableStore } from '../store';

/** One square of the grid, placed on the drawing. */
interface Cell { coord: string; row: number; col: number; x: number; y: number; glyph: string; ground: string; letter: string; }

const CELL = 10;
const LEFT = 15;
const TOP = 11;
const TERRAIN: Record<string, string> = { '.': 'sea', '#': 'land', '^': 'mtn', '~': 'river' };

/**
 * The map: the grid drawn from `rows` (sea, land, mountains, river; the
 * settlement letters as the map prints them), the party's `@` and the jobs'
 * `!` laid over it, and the axes every 5. Tapping a square names it:
 * "R12C14 -- land. Venice (city, Byzantium)", from the known places and the
 * legend's own words. Below: where the party stands, its land, the known
 * places and the holdings, as printed; "Text map" shows ui/map.txt exactly.
 */
@Component({
  selector: 'rpg-map',
  template: `
    @if (map(); as m) {
      <div class="sub">
        <h2>The map</h2>
        <button type="button" class="toggle" id="map-toggle" [attr.aria-pressed]="asText()" (click)="asText.set(!asText())">
          {{ asText() ? 'Drawn map' : 'Text map' }}
        </button>
      </div>
      @if (asText()) {
        <pre class="display" id="map-text">{{ m.text.join('\\n') }}</pre>
      } @else {
        <svg class="grid" [attr.viewBox]="viewBox()" role="img" tabindex="0"
          [attr.aria-label]="'The map, ' + cols() + ' by ' + m.rows.length + ' squares; the party at ' + m.coord + '. Arrow keys move the pick.'"
          (click)="pick($event)" (keydown)="step($event)">
          @for (n of colLabels(); track n) {
            <text class="axis" [attr.x]="left + (n - 0.5) * cell" [attr.y]="top - 3" text-anchor="middle">{{ n }}</text>
          }
          @for (n of rowLabels(); track n) {
            <text class="axis" [attr.x]="left - 2" [attr.y]="top + (n - 0.5) * cell + 2.2" text-anchor="end">{{ n }}</text>
          }
          @for (c of cells(); track c.coord) {
            <rect [attr.x]="c.x" [attr.y]="c.y" [attr.width]="cell" [attr.height]="cell" [attr.class]="'sq ' + c.ground"
              [attr.data-coord]="c.coord" [attr.data-glyph]="c.glyph" />
            @if (c.letter) {
              <text class="letter" [attr.x]="c.x + cell / 2" [attr.y]="c.y + cell / 2 + 3" text-anchor="middle">{{ c.letter }}</text>
            }
          }
          @for (o of objectiveCells(); track o.coord) {
            <g class="job" [attr.data-mark]="'job ' + o.coord">
              <rect [attr.x]="o.x + 0.8" [attr.y]="o.y + 0.8" [attr.width]="cell - 1.6" [attr.height]="cell - 1.6" rx="1.5" />
              @if (o.coord !== m.coord) { <text [attr.x]="o.x + cell / 2" [attr.y]="o.y + cell / 2 + 3" text-anchor="middle">!</text> }
            </g>
          }
          @if (partyCell(); as p) {
            <g class="party" [attr.data-mark]="'party ' + p.coord">
              <circle [attr.cx]="p.x + cell / 2" [attr.cy]="p.y + cell / 2" [attr.r]="cell / 2 - 0.4" />
              <text [attr.x]="p.x + cell / 2" [attr.y]="p.y + cell / 2 + 2.6" text-anchor="middle">&#64;</text>
            </g>
          }
          @if (pickedCell(); as s) {
            <rect class="picked" [attr.x]="s.x" [attr.y]="s.y" [attr.width]="cell" [attr.height]="cell" />
          }
        </svg>
        <p class="said" id="map-said" role="status">{{ said() }}</p>
        <ul class="legend" aria-label="The legend">
          @for (l of m.legend; track l[0]) {
            <li><span class="key" [class]="keyClass(l[0])" aria-hidden="true">{{ keyText(l[0]) }}</span>{{ l[1] }}</li>
          }
        </ul>
      }
      <pre class="display" id="map-here">{{ m.here.join('\\n') }}</pre>
      @if (m.land.lines.length) {
        <section class="block">
          <h3 class="label">-- {{ m.land.name }} --</h3>
          <pre class="display">{{ m.land.lines.join('\\n') }}</pre>
        </section>
      }
      @if (m.known.length) {
        <section class="block">
          <h3 class="label">Known places</h3>
          <pre class="display">{{ m.known.join('\\n') }}</pre>
        </section>
      }
      @if (m.holdings.length) {
        <section class="block">
          <h3 class="label">Holdings</h3>
          <pre class="display">{{ m.holdings.join('\\n') }}</pre>
        </section>
      }
    } @else {
      <h2>The map</h2>
      <p class="note">The map appears here once the game starts.</p>
    }
  `,
  styles: [`
    :host { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
    .sub { display: flex; justify-content: space-between; align-items: center; gap: 6px 10px; flex-wrap: wrap; }
    .toggle {
      border: 1px solid var(--rule); background: var(--paper); border-radius: 4px; min-height: 48px; padding: 0 14px;
      font-family: var(--mono); font-size: .76rem; color: var(--ink-2); letter-spacing: .04em;
    }
    .toggle[aria-pressed="true"] { border-color: var(--accent); color: var(--ink); background: var(--accent-soft); }
    .grid { display: block; width: 100%; height: auto; touch-action: manipulation; user-select: none; -webkit-user-select: none; }
    .grid:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
    .grid text { font-family: var(--mono); pointer-events: none; }
    .axis { font-size: 6px; fill: var(--ink-3); }
    .sq { stroke: var(--paper-2); stroke-width: .35; cursor: pointer; }
    .sq.sea { fill: var(--sea); } .sq.land { fill: var(--land); } .sq.mtn { fill: var(--mtn); } .sq.river { fill: var(--river); }
    .letter { font-size: 8px; font-weight: 700; fill: var(--ink); }
    .job rect { fill: none; stroke: var(--hurt); stroke-width: 1.3; pointer-events: none; }
    .job text { font-size: 8px; font-weight: 700; fill: var(--hurt); }
    .party circle { fill: var(--accent); stroke: var(--paper); stroke-width: .8; pointer-events: none; }
    .party text { font-size: 7px; font-weight: 700; fill: var(--on-accent); }
    .picked { fill: none; stroke: var(--ink); stroke-width: 1; pointer-events: none; }
    .said { font-family: var(--mono); font-size: .82rem; line-height: 1.5; min-height: 3em; overflow-wrap: anywhere; color: var(--ink); }
    .legend { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 6px 14px; font-family: var(--mono); font-size: .74rem; color: var(--ink-2); }
    .legend li { display: inline-flex; align-items: center; gap: 6px; }
    .key { display: inline-grid; place-items: center; width: 14px; height: 14px; border-radius: 2px; font-size: .7rem; font-weight: 700; color: var(--ink); background: var(--land); }
    .key.sea { background: var(--sea); } .key.mtn { background: var(--mtn); } .key.river { background: var(--river); }
    .key.party { background: var(--accent); color: var(--on-accent); border-radius: 50%; }
    .key.job { background: none; border: 1.5px solid var(--hurt); color: var(--hurt); box-sizing: border-box; }
    .block { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
    .block h3 { font-size: .7rem; }
  `],
})
export class MapTab {
  private readonly store = inject(TableStore);
  readonly map = this.store.map;
  readonly cell = CELL;
  readonly left = LEFT;
  readonly top = TOP;

  readonly asText = signal(false);
  /** The square picked; null: the party's. */
  readonly picked = signal<string | null>(null);

  readonly cols = computed(() => Math.max(0, ...(this.map()?.rows ?? []).map((r) => r.length)));
  readonly viewBox = computed(() => `0 0 ${LEFT + this.cols() * CELL + 1} ${TOP + (this.map()?.rows.length ?? 0) * CELL + 1}`);
  readonly colLabels = computed(() => fives(this.cols()));
  readonly rowLabels = computed(() => fives(this.map()?.rows.length ?? 0));

  readonly cells = computed<Cell[]>(() => {
    const m = this.map();
    if (!m) return [];
    return m.rows.flatMap((row, r) => [...row].map((glyph, c) => ({
      coord: cellCoord(r, c), row: r, col: c, x: LEFT + c * CELL, y: TOP + r * CELL, glyph,
      ground: TERRAIN[glyph] ?? 'land',
      letter: TERRAIN[glyph] ? '' : glyph,
    })));
  });

  private readonly byCoord = computed(() => new Map(this.cells().map((c) => [c.coord, c] as const)));
  readonly partyCell = computed(() => this.byCoord().get(this.map()?.coord ?? '') ?? null);
  readonly objectiveCells = computed(() =>
    (this.map()?.objectives ?? []).map((o) => this.byCoord().get(o)).filter((c): c is Cell => !!c));
  readonly pickedCell = computed(() => this.byCoord().get(this.picked() ?? '') ?? this.partyCell());

  /** The picked square in words. */
  readonly said = computed(() => {
    const m = this.map();
    const c = this.pickedCell();
    return m && c ? describe(m, c) : 'Tap a square to name it.';
  });

  pick(event: Event): void {
    const coord = (event.target as Element | null)?.getAttribute?.('data-coord');
    if (coord) this.picked.set(coord);
  }

  step(event: KeyboardEvent): void {
    const moves: Record<string, [number, number]> = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] };
    const d = moves[event.key];
    const at = this.pickedCell();
    if (!d || !at) return;
    event.preventDefault();
    const next = this.byCoord().get(cellCoord(at.row + d[0], at.col + d[1]));
    if (next) this.picked.set(next.coord);
  }

  keyClass(glyph: string): string {
    return glyph === '@' ? 'party' : glyph === '!' ? 'job' : TERRAIN[glyph] ?? 'place';
  }

  keyText(glyph: string): string {
    return TERRAIN[glyph] ? '' : glyph;
  }
}

/** 5, 10, 15 ... up to n. */
function fives(n: number): number[] {
  const out: number[] = [];
  for (let i = 5; i <= n; i += 5) out.push(i);
  return out;
}

/** "R12C14 -- land. Venice (city, Byzantium)." in the legend's own words. */
function describe(m: MapDoc, c: Cell): string {
  const word = new Map(m.legend.map(([g, w]) => [g, w] as const));
  const ground = TERRAIN[c.glyph] ? word.get(c.glyph) ?? TERRAIN[c.glyph] : word.get('#') ?? 'land';
  const parts = [`${c.coord} -- ${ground}`];
  if (c.coord === m.coord) parts.push('The party is here');
  if (m.objectives.includes(c.coord)) parts.push('A job in hand leads here');
  const places = m.places.filter((p) => p.coord === c.coord)
    .map((p) => `${p.name} (${[p.kind, p.land, p.capital ? 'capital' : ''].filter(Boolean).join(', ')})`);
  if (places.length) parts.push(places.join(', '));
  return parts.join('. ') + '.';
}
