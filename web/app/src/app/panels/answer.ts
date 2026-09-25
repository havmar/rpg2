import { Component, ElementRef, computed, effect, inject, signal, untracked, viewChild } from '@angular/core';
import { TableStore } from '../store';
import { Ui } from '../ui';

type Kind = 'say' | 'ooc';
const DRAFT_KEY = 'rpg2.draft';

/** The status line and the answer box: free text, in the game or to the DM. */
@Component({
  selector: 'rpg-answer',
  template: `
    <p class="status" [class]="linkClass()" role="status">
      @if (linkClass() !== 'live') { <span class="dot" aria-hidden="true"></span> }
      @for (w of statusWords(); track $index) { <span class="w">{{ w }}</span> }
    </p>

    @if (closed(); as why) {
      <p class="closed note">{{ why }}</p>
    } @else {
      <form class="composer" (submit)="$event.preventDefault(); submit()">
        <label for="move" class="label">{{ heading() }}</label>
        <textarea #box id="move" name="move" rows="3" [value]="draft()" (input)="edit($any($event.target).value)"
          (keydown)="onKey($event)" [placeholder]="placeholder()" maxlength="2000"></textarea>
        <div class="bar">
          <span class="seg" role="group" aria-label="Who it is for">
            <button type="button" id="kind-say" [attr.aria-pressed]="kind() === 'say'" (click)="kind.set('say')">In the game</button>
            <button type="button" id="kind-ooc" [attr.aria-pressed]="kind() === 'ooc'" (click)="kind.set('ooc')">To the DM</button>
          </span>
          <button class="send" type="submit" [disabled]="!canSend()">{{ store.sending() ? 'Sending' : 'Send' }}</button>
        </div>
      </form>
      @if (store.writeError(); as err) { <p class="error">{{ err }}</p> }
    }
  `,
  styles: [`
    :host { display: flex; flex-direction: column; gap: 10px; max-width: 64ch; }
    .status { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 0; font-family: var(--mono); font-size: .76rem; color: var(--ink-2); }
    .status .w:first-of-type { color: var(--ink); font-weight: 600; }
    .status .w + .w::before { content: ""; display: inline-block; width: 4px; height: 4px; border-radius: 50%; background: var(--ink-3); margin: 0 8px; vertical-align: middle; }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--ink-3); display: inline-block; margin-right: 8px; }
    .status.broken .dot { background: var(--hurt); }
    .status.broken { color: var(--hurt); }
    .composer { border: 1px solid var(--rule); background: var(--paper); border-radius: 6px; display: flex; flex-direction: column; }
    .composer:focus-within { border-color: var(--accent); }
    .composer .label { padding: 12px 14px 0; }
    textarea { border: 0; background: transparent; resize: vertical; min-height: 84px; padding: 8px 14px 12px; font-family: var(--prose); font-size: 1.02rem; line-height: 1.55; color: var(--ink); }
    textarea:focus { outline: none; }
    textarea::placeholder { color: var(--ink-3); }
    .bar { display: flex; gap: 8px; align-items: center; justify-content: space-between; border-top: 1px solid var(--rule); padding: 6px 8px; }
    .seg { display: inline-flex; border: 1px solid var(--rule); border-radius: 4px; overflow: hidden; min-width: 0; }
    .seg button { border: 0; background: none; min-height: 48px; padding: 0 12px; font-family: var(--mono); font-size: .76rem; color: var(--ink-2); white-space: nowrap; }
    .seg button[aria-pressed="true"] { background: var(--ink); color: var(--paper); }
    .send { flex: none; border: 0; background: var(--accent); color: var(--on-accent); min-height: 48px; min-width: 72px; padding: 0 18px; border-radius: 4px; font-family: var(--mono); font-size: .82rem; font-weight: 600; }
    .send:disabled { opacity: .45; cursor: default; }
    .closed { border-left: 2px solid var(--rule); padding-left: 12px; }
    .error { color: var(--hurt); font-size: .88rem; }
  `],
})
export class Answer {
  readonly store = inject(TableStore);
  private readonly ui = inject(Ui);
  private readonly box = viewChild<ElementRef<HTMLTextAreaElement>>('box');

  readonly kind = signal<Kind>('say');
  readonly draft = signal(loadDraft());

  private readonly name = computed(() => this.store.pc()?.name ?? '');

  readonly heading = computed(() => (this.name() ? `Your move, as ${this.name()}` : 'Your move'));
  readonly placeholder = computed(() =>
    this.kind() === 'ooc' ? 'Ask the DM, out of the game' : 'What do you do?');

  readonly closed = computed<string | null>(() => {
    const link = this.store.link();
    if (link === 'connecting') return 'Connecting.';
    if (link === 'unavailable') return 'This page has no line to the game. Open it on claude.ai, signed in.';
    if (link === 'lost') return 'The connection dropped. Reload the page.';
    if (this.store.readOnly()) return 'You can read this game but not write to it.';
    if (!this.store.state()) return 'No game yet. Ask the DM in Claude Code to start one. The first scene appears here.';
    if (this.store.state()?.status === 'ended') return 'GAME OVER';
    return null;
  });

  readonly canSend = computed(() => !this.store.sending() && this.draft().trim().length > 0);

  readonly linkClass = computed(() => {
    const link = this.store.link();
    return link === 'live' ? 'live' : link === 'connecting' ? '' : 'broken';
  });

  readonly linkWords = computed(() => {
    switch (this.store.link()) {
      case 'live': return 'Live';
      case 'connecting': return 'Connecting';
      case 'unavailable': return 'Not connected';
      case 'lost': return 'Connection lost';
    }
  });

  /** The connection only when it is not live, then whose move it is and when the DM looks. */
  readonly statusWords = computed(() => {
    const words = [this.turnWords(), this.checkInWords()].filter(Boolean);
    if (this.store.link() !== 'live') words.unshift(this.linkWords());
    return words;
  });

  readonly turnWords = computed(() => {
    const s = this.store.state();
    if (!s || this.store.link() !== 'live') return '';
    if (s.status === 'ended') return 'GAME OVER';
    if (s.status === 'dm_thinking') return 'The DM is writing';
    const n = this.store.pending().length;
    if (n) return `${n} move${n === 1 ? '' : 's'} waiting on the DM`;
    return 'Your move';
  });

  /** When the DM next looks, from state.checkIn: an ISO time or words. */
  readonly checkInWords = computed(() => {
    const s = this.store.state();
    const at = s?.checkIn;
    if (!at || s?.status === 'ended' || this.store.link() !== 'live') return '';
    if (!/^\d{4}-\d\d-\d\dT/.test(at)) return `the DM looks ${at}`;
    const when = Date.parse(at);
    if (!Number.isFinite(when)) return '';
    const min = Math.round((when - this.ui.now()) / 60_000);
    if (min <= 1) return 'the DM looks any moment now';
    if (min < 60) return `the DM looks in about ${min} min`;
    const t = new Date(when);
    const hm = t.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    return min < 18 * 60 ? `the DM looks at ${hm}` : `the DM looks on ${t.toLocaleDateString([], { weekday: 'long' })} at ${hm}`;
  });

  constructor() {
    // An option chip's words: into the box, focused, never sent.
    effect(() => {
      const ask = this.ui.prefill();
      if (!ask) return;
      untracked(() => {
        this.kind.set('say');
        this.edit(ask.text);
        this.ui.prefill.set(null);
        setTimeout(() => {
          const box = this.box()?.nativeElement;
          box?.focus();
          box?.setSelectionRange(box.value.length, box.value.length);
        }, 30);
      });
    });
  }

  edit(value: string): void {
    this.draft.set(value);
    saveDraft(value);
  }

  onKey(event: KeyboardEvent): void {
    // Enter sends where there is a keyboard; on a phone Enter is a new line.
    if (event.key === 'Enter' && !event.shiftKey && !coarse()) {
      event.preventDefault();
      this.submit();
    }
  }

  async submit(): Promise<void> {
    if (!this.canSend()) return;
    const text = this.draft();
    this.edit('');
    const sent = await this.store.send({ kind: this.kind(), text });
    if (!sent && !this.draft()) this.edit(text);   // give the words back
  }
}

function coarse(): boolean {
  return typeof matchMedia === 'function' && matchMedia('(pointer: coarse)').matches;
}

function loadDraft(): string {
  try {
    return localStorage.getItem(DRAFT_KEY) ?? '';
  } catch {
    return '';
  }
}

function saveDraft(text: string): void {
  try {
    if (text) localStorage.setItem(DRAFT_KEY, text);
    else localStorage.removeItem(DRAFT_KEY);
  } catch {
    /* a draft is a convenience */
  }
}
