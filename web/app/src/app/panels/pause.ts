import { Component, computed, effect, inject, signal, untracked } from '@angular/core';
import { ESCAPES, Escape, MoveBody, PAUSE_ACTIONS, PauseAction, PauseChoice, PauseHero, PauseOption, moveWords } from '../model';
import { TableStore } from '../store';
import { Ui } from '../ui';

/**
 * The pause picker: the one mid-fight decision, in the Story above the
 * answer box while a fight stands paused. It shows the pause menu as data
 * (what tripped it, who the party faces, each hero's numbers) and builds the
 * `pause` move from what the menu offers: Fight on, with at most one action
 * per hero from the heroes each option names (none at a Fate pause), or
 * Retreat, with an optional blink or smoke. The summary line is the move in
 * the player's words (model.moveWords, as page.move_words says it); Send
 * writes it with the paused fight's published id. The keeper checks it
 * (page.py moves) and plays it only as the command printed. Once sent it
 * says so; a newer choice supersedes it. The exact menu sits in a fold.
 * The section keeps id="pause": ui.openPause() scrolls to it.
 */
@Component({
  selector: 'rpg-pause',
  template: `
    @if (pause(); as p) {
      <section id="pause" class="pause" aria-label="The fight is paused">
        <p class="label head">PAUSED after round {{ p.round }}@if (p.kind === 'fate') {<span class="fate">Fate</span>}</p>
        @if (p.trips) { <p class="trips">{{ p.trips }}.</p> }

        @if (sent(); as m) {
          @if (!editing()) {
            <div class="sent" role="status">
              <p><b>Sent. Waiting on the DM.</b></p>
              <p class="words" id="pause-sent">{{ words(m) }}</p>
              <button type="button" class="linkbtn" (click)="editing.set(true)">Change it</button>
            </div>
          }
        }
        @if (!sent() || editing()) {
          @if (p.facing.length) {
            <p class="facing"><span class="label">Facing</span>
              @for (f of p.facing; track $index) {<span class="foe">{{ f.name }} <span class="num">{{ f.hp }}/{{ f.maxHp }} HP</span></span>}
            </p>
          }
          <ul class="heroes">
            @for (h of p.party; track h.name) {
              <li [attr.data-hero]="h.name" [class.down]="h.down">
                <p class="row"><b>{{ h.name }}</b>@if (h.down) {<span class="tag hurt">DOWN</span>}<span class="state">{{ h.hpState }}</span></p>
                <p class="nums num">
                  <span>HP {{ h.hp }}/{{ h.hpCeiling }}@if (h.hpCeiling < h.maxHp) { (max {{ h.maxHp }})}</span>
                  <span>STA {{ h.sta }}/{{ h.staMax }}</span>
                  <span>Power {{ h.power }}/{{ h.powerMax }}</span>
                </p>
                @if (h.penalties) { <p class="pen num">{{ h.penalties }} to rolls</p> }
                @if (h.conditions.length || h.wounds.length) {
                  <p class="tags">
                    @for (c of h.conditions; track c) {<span class="tag warn">{{ c }}</span>}
                    @for (w of h.wounds; track w) {<span class="tag hurt">{{ w }}</span>}
                  </p>
                }
                <p class="kit num">healing x{{ h.healing }}, stamina x{{ h.stamina }}</p>
              </li>
            }
          </ul>

          <div class="choose" role="radiogroup" aria-label="Your call">
            <button type="button" role="radio" id="pause-fight-on" [attr.aria-checked]="choice() === 'fight_on'" (click)="choose('fight_on')">Fight on</button>
            <button type="button" role="radio" id="pause-retreat" [attr.aria-checked]="choice() === 'retreat'" (click)="choose('retreat')">Retreat</button>
          </div>

          @if (choice() === 'fight_on') {
            <div class="under" id="pause-actions">
              @if (p.kind === 'fate') {
                <p class="note">Fate's pause: fight on or retreat, with no pause action.</p>
              } @else if (actionRows().length) {
                <p class="note">One action a hero, before the next round (it costs that hero the round: defending worse). Or none.</p>
                @for (r of actionRows(); track r.hero) {
                  <div class="hero-acts" [attr.data-hero]="r.hero">
                    <span class="who">{{ r.hero }}</span>
                    <span class="chips">
                      @for (o of r.options; track o.choice) {
                        <button type="button" class="chip" [attr.data-action]="o.choice" [attr.aria-pressed]="actions()[r.hero] === o.choice"
                          (click)="toggle(r.hero, $any(o.choice))">{{ o.label }}</button>
                      }
                    </span>
                  </div>
                }
                <ul class="costs">
                  @for (o of actionOptions(); track o.choice) {<li><b>{{ o.label }}</b> -- {{ o.cost }}</li>}
                </ul>
              } @else {
                <p class="note">Nobody can take a pause action now.</p>
              }
            </div>
          }
          @if (choice() === 'retreat') {
            <div class="under" id="pause-escapes">
              @if (retreatCost()) { <p class="note">{{ retreatCost() }}</p> }
              @if (escapeOptions().length) {
                <span class="chips">
                  @for (o of escapeOptions(); track o.choice) {
                    <button type="button" class="chip" [attr.data-escape]="o.choice" [attr.aria-pressed]="escape()?.escape === o.choice"
                      (click)="toggleEscape(o)">{{ o.label }} ({{ o.hero }})</button>
                  }
                </span>
                <ul class="costs">
                  @for (o of escapeOptions(); track o.choice) {<li><b>{{ o.label }}</b> -- {{ o.cost }}</li>}
                </ul>
              }
            </div>
          }

          @if (body(); as b) {
            <p class="summary" id="pause-summary">{{ words(b) }}</p>
          }
          @if (!p.fight) {
            <p class="note">The paused fight is not on the page yet. Say your call in the box below.</p>
          }
          <div class="go">
            @if (editing()) { <button type="button" class="linkbtn" (click)="editing.set(false)">Keep the one sent</button> }
            <button type="button" class="send" id="pause-send" [disabled]="!canSend()" (click)="send()">{{ store.sending() ? 'Sending' : 'Send' }}</button>
          </div>
        }

        <div class="foot">
          @if (p.fight) { <button type="button" class="linkbtn" (click)="ui.openFight(p.fight)">Open the fight</button> }
        </div>
        <details class="fold">
          <summary>The exact menu</summary>
          <pre class="display" id="pause-menu">{{ p.text.join('\\n') }}</pre>
        </details>
      </section>
    }
  `,
  styles: [`
    :host { display: block; max-width: 64ch; }
    .pause { border: 1px solid var(--accent); border-left-width: 4px; background: var(--accent-soft); border-radius: 4px; padding: 12px 14px; display: flex; flex-direction: column; gap: 10px; min-width: 0; }
    .head { color: var(--accent); font-size: .78rem; }
    .fate { margin-left: 8px; border: 1px solid var(--accent); border-radius: 3px; padding: 0 5px; }
    .trips { font-weight: 600; }
    .facing { display: flex; flex-wrap: wrap; gap: 4px 12px; align-items: baseline; font-family: var(--mono); font-size: .84rem; }
    .foe .num { color: var(--ink-2); }
    .heroes { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
    .heroes li { background: var(--paper); border: 1px solid var(--rule); border-radius: 4px; padding: 8px 10px; display: flex; flex-direction: column; gap: 3px; }
    .heroes li.down { opacity: .75; }
    .row { display: flex; gap: 8px; align-items: baseline; flex-wrap: wrap; font-family: var(--mono); }
    .state { color: var(--ink-2); font-size: .84rem; }
    .nums { display: flex; flex-wrap: wrap; gap: 2px 12px; font-size: .82rem; }
    .pen, .kit { font-size: .78rem; color: var(--ink-2); }
    .tags { display: flex; gap: 6px; flex-wrap: wrap; }
    .tag.warn { border-color: var(--warn); color: var(--warn); }
    .tag.hurt { border-color: var(--hurt); color: var(--hurt); }
    .choose { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .choose button {
      min-height: 52px; border: 1px solid var(--accent); background: var(--paper); color: var(--ink); border-radius: 4px;
      font-family: var(--mono); font-size: .9rem; font-weight: 600; letter-spacing: .04em;
    }
    .choose button[aria-checked="true"] { background: var(--accent); color: var(--on-accent); }
    .under { display: flex; flex-direction: column; gap: 8px; }
    .hero-acts { display: flex; flex-direction: column; gap: 4px; }
    .who { font-family: var(--mono); font-size: .8rem; font-weight: 600; }
    .chips { display: flex; flex-wrap: wrap; gap: 8px; }
    .chip {
      min-height: 48px; min-width: 48px; padding: 0 16px; border: 1px solid var(--rule); background: var(--paper);
      border-radius: 24px; font-family: var(--mono); font-size: .82rem; color: var(--ink);
    }
    .chip[aria-pressed="true"] { border-color: var(--accent); background: var(--accent); color: var(--on-accent); }
    .costs { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 2px; font-size: .82rem; color: var(--ink-2); }
    .costs b { font-family: var(--mono); font-weight: 600; color: var(--ink); }
    .summary { font-style: italic; border-left: 2px solid var(--accent); padding-left: 10px; overflow-wrap: anywhere; }
    .go { display: flex; justify-content: flex-end; align-items: center; gap: 12px; flex-wrap: wrap; }
    .send { border: 0; background: var(--accent); color: var(--on-accent); min-height: 48px; min-width: 96px; padding: 0 18px; border-radius: 4px; font-family: var(--mono); font-size: .86rem; font-weight: 600; }
    .send:disabled { opacity: .45; cursor: default; }
    .sent { display: flex; flex-direction: column; gap: 4px; }
    .words { font-style: italic; overflow-wrap: anywhere; }
    .foot { display: flex; gap: 12px; flex-wrap: wrap; }
    .pause pre.display { background: none; border: 0; padding: 4px 0; }
    @media (max-width: 380px) { .pause { padding: 12px 10px; } }
    .linkbtn { align-self: flex-start; min-height: 48px; border: 0; background: none; padding: 0; font-family: var(--mono); font-size: .78rem; color: var(--accent); letter-spacing: .06em; text-transform: uppercase; }
  `],
})
export class Pause {
  readonly store = inject(TableStore);
  readonly ui = inject(Ui);
  readonly pause = this.store.pause;
  readonly sent = this.store.pauseSent;
  readonly words = moveWords;

  readonly choice = signal<PauseChoice | null>(null);
  /** Hero name -> the one action chosen for that hero. */
  readonly actions = signal<Record<string, PauseAction>>({});
  readonly escape = signal<{ escape: Escape; hero: string } | null>(null);
  /** Choosing again after a choice was sent. */
  readonly editing = signal(false);

  /** Which pause stands: a string, so a re-read of the same state changes nothing. */
  private readonly which = computed(() => {
    const p = this.pause();
    return p ? `${p.fight}:${p.round}:${p.kind}` : '';
  });

  constructor() {
    // A new pause (another fight, another round) starts the picker afresh.
    effect(() => {
      this.which();
      untracked(() => {
        this.choice.set(null);
        this.actions.set({});
        this.escape.set(null);
        this.editing.set(false);
      });
    });
  }

  readonly actionOptions = computed<PauseOption[]>(() => {
    const p = this.pause();
    if (!p || p.kind === 'fate') return [];
    return p.options.filter((o) => PAUSE_ACTIONS.includes(o.choice as PauseAction) && o.heroes.length);
  });

  /** Each hero who may act, with the actions the menu lets that hero take. */
  readonly actionRows = computed(() => {
    const p = this.pause();
    const opts = this.actionOptions();
    return (p?.party ?? [])
      .map((h: PauseHero) => ({ hero: h.name, options: opts.filter((o) => o.heroes.includes(h.name)) }))
      .filter((r) => r.options.length);
  });

  readonly escapeOptions = computed<PauseOption[]>(() =>
    (this.pause()?.options ?? []).filter((o) => ESCAPES.includes(o.choice as Escape) && !!o.hero));

  readonly retreatCost = computed(() => this.pause()?.options.find((o) => o.choice === 'retreat')?.cost ?? '');

  /** The move the picker would send; null until Fight on or Retreat is chosen. */
  readonly body = computed<MoveBody | null>(() => {
    const p = this.pause();
    const choice = this.choice();
    if (!p || !choice) return null;
    const fight = p.fight ?? '';
    if (choice === 'fight_on') {
      const chosen = this.actions();
      const actions = p.kind === 'fate' ? [] : p.party
        .filter((h) => chosen[h.name])
        .map((h) => ({ hero: h.name, action: chosen[h.name] }));
      return { kind: 'pause', fight, choice, actions };
    }
    const esc = this.escape();
    return esc ? { kind: 'pause', fight, choice, escape: esc.escape, hero: esc.hero } : { kind: 'pause', fight, choice };
  });

  readonly canSend = computed(() =>
    !!this.body() && !!this.pause()?.fight && !this.store.sending() && !this.store.readOnly());

  choose(choice: PauseChoice): void {
    this.choice.set(choice);
  }

  toggle(hero: string, action: PauseAction): void {
    const next = { ...this.actions() };
    if (next[hero] === action) delete next[hero];
    else next[hero] = action;
    this.actions.set(next);
  }

  toggleEscape(o: PauseOption): void {
    const esc = o.choice as Escape;
    this.escape.set(this.escape()?.escape === esc ? null : { escape: esc, hero: o.hero ?? '' });
  }

  async send(): Promise<void> {
    const body = this.body();
    if (!body || !this.canSend()) return;
    if (await this.store.send(body)) {
      this.editing.set(false);
      this.choice.set(null);
      this.actions.set({});
      this.escape.set(null);
    }
  }
}
