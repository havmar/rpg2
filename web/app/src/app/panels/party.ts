import { Component, computed, inject } from '@angular/core';
import { Member } from '../model';
import { TableStore } from '../store';

/** A meter: a value against its top, with a ceiling mark for HP under wounds. */
interface Meter { key: string; label: string; now: number; max: number; ceiling: number | null; }

/**
 * The party: a card per hero, with the numbers the party sheet prints, drawn
 * (level, XP, HP, STA, Power as bars; kit, weapon, spells, abilities, moves,
 * conditions and wounds as tags), each with its block of the sheet as
 * printed; then the purse, the companion slots, the sheet's tail, and the
 * whole of ui/party.txt. While the PC has points banked, the level-up menu
 * as printed sits on top, and the player says what to buy.
 */
@Component({
  selector: 'rpg-party',
  template: `
    @if (party(); as p) {
      <div class="sub">
        <h2>The party</h2>
        <span class="label facts"><span>Purse {{ p.purse }}s</span><span>Companions {{ p.slots.filled }} of {{ p.slots.cap }}</span></span>
      </div>
      @if (levelUp(); as l) {
        <section class="levelup" id="levelup" aria-label="Points to spend">
          <p class="label">Level up</p>
          <p><b>{{ l.hero }}</b> has {{ l.points }} point{{ l.points === 1 ? '' : 's' }} to spend. Say what to spend them on.</p>
          <details open>
            <summary>The spending menu, as printed</summary>
            <pre class="display" id="levelup-menu">{{ l.text.join('\\n') }}</pre>
          </details>
        </section>
      }
      @for (m of p.members; track m.name) {
        <article class="card" [attr.data-member]="m.name" [class.dead]="m.dead" [class.pc]="m.isPc">
          <header>
            <h3>{{ m.name }}@if (m.nickname) {<span class="nick"> "{{ m.nickname }}"</span>}</h3>
            <span class="tag" [class.you]="m.isPc">{{ m.isPc ? 'YOU' : 'companion' }}</span>
            <span class="lvl num">L{{ m.level }}</span>
          </header>
          <p class="who note">{{ cap(m.homeland) }} {{ m.sex }}, age {{ m.age }}@if (m.training) {, training {{ m.training }}}</p>
          @if (m.dead) { <p class="state down">DEAD</p> }
          @else if (m.down) { <p class="state down">DOWN</p> }
          @if (m.quitting) { <p class="state warn">wants to leave</p> }

          <div class="xp">
            <span class="label">XP</span>
            <span class="bar" role="img" [attr.aria-label]="'XP ' + m.xp + ' of ' + m.xpNext"><i [style.width.%]="pct(m.xp, m.xpNext)"></i></span>
            <span class="num">{{ m.xp }}/{{ m.xpNext }}</span>
          </div>
          @if (m.points) { <p class="state accent points">{{ m.points }} point{{ m.points === 1 ? '' : 's' }} to spend</p> }

          @for (g of meters(m); track g.key) {
            <div class="meter" [attr.data-meter]="g.key">
              <span class="label">{{ g.label }}</span>
              <span class="bar" [class]="g.key" role="img" [attr.aria-label]="g.label + ' ' + g.now + ' of ' + g.max">
                <i [style.width.%]="pct(g.now, g.max)"></i>
                @if (g.ceiling !== null) { <b class="ceil" [style.left.%]="pct(g.ceiling, g.max)"></b> }
              </span>
              <span class="num">{{ g.now }}/{{ g.max }}</span>
            </div>
          }

          <p class="stats num"><span>DEX {{ m.dex }}</span><span>STR {{ m.str }}</span><span>MIND {{ m.mind }}</span><span>CHA {{ m.cha }}</span></p>

          <div class="tags">
            @if (m.weapon) { <span class="tag">{{ m.weapon }}</span> }
            @for (k of kit(m); track k) { <span class="tag">{{ k }}</span> }
            @for (s of spells(m); track s) { <span class="tag spell">{{ s }}</span> }
            @for (a of m.abilities; track a) { <span class="tag">{{ a }}</span> }
            @for (a of m.moves; track a) { <span class="tag">{{ a }}</span> }
            @if (m.satisfaction !== null) { <span class="tag">satisfaction {{ m.satisfaction }}/10</span> }
          </div>
          @if (m.conditions.length || m.wounds.length) {
            <div class="tags">
              @for (c of m.conditions; track c) { <span class="tag warn">{{ c }}</span> }
              @for (w of m.wounds; track w) { <span class="tag hurt">{{ w }}</span> }
            </div>
          }
          @if (extra(m).length) {
            <div class="extra">@for (t of extra(m); track t) { <p class="note">{{ t }}</p> }</div>
          }

          <details>
            <summary>The sheet, as printed</summary>
            <pre class="display">{{ m.text.join('\\n') }}</pre>
          </details>
        </article>
      }
      @if (p.status.length) {
        <pre class="display status">{{ p.status.join('\\n') }}</pre>
      }
      <details class="whole">
        <summary>The whole party sheet, as printed</summary>
        <pre class="display" id="party-sheet">{{ p.text.join('\\n') }}</pre>
      </details>
    } @else {
      <h2>The party</h2>
      <p class="note">The party appears here once the game starts.</p>
    }
  `,
  styles: [`
    :host { display: flex; flex-direction: column; gap: 14px; min-width: 0; }
    .sub { display: flex; justify-content: space-between; align-items: baseline; gap: 6px 10px; flex-wrap: wrap; }
    .facts > span + span::before { content: ""; display: inline-block; width: 4px; height: 4px; border-radius: 50%; background: var(--ink-3); margin: 0 8px; vertical-align: middle; }
    .card { border: 1px solid var(--rule); border-radius: 6px; background: var(--paper); padding: 12px 14px; display: flex; flex-direction: column; gap: 8px; min-width: 0; }
    .card.pc { border-left: 3px solid var(--accent); }
    .card.dead { opacity: .6; }
    header { display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
    h3 { font-family: var(--mono); font-size: 1.05rem; font-weight: 600; letter-spacing: .02em; }
    .nick { font-weight: 400; color: var(--ink-2); }
    .tag.you { border-color: var(--accent); color: var(--accent); }
    .lvl { margin-left: auto; font-weight: 600; }
    .state { font-family: var(--mono); font-size: .8rem; font-weight: 600; }
    .state.down { color: var(--hurt); } .state.warn { color: var(--warn); } .state.accent { color: var(--accent); }
    .xp, .meter { display: grid; grid-template-columns: 4.2em minmax(0, 1fr) 4.2em; align-items: center; gap: 8px; }
    .xp .num, .meter .num { font-size: .8rem; text-align: right; }
    .bar { position: relative; height: 10px; border-radius: 5px; background: var(--paper-3); overflow: hidden; }
    .bar i { position: absolute; left: 0; top: 0; bottom: 0; background: var(--ink-3); border-radius: 5px; }
    .bar.hp i { background: var(--good); }
    .bar.sta i { background: var(--warn); }
    .bar.power i { background: var(--accent); }
    .ceil { position: absolute; top: -2px; bottom: -2px; right: 0; background: repeating-linear-gradient(45deg, var(--hurt) 0 2px, transparent 2px 4px); }
    .stats { display: flex; gap: 4px 12px; flex-wrap: wrap; font-size: .82rem; }
    .tags { display: flex; gap: 6px; flex-wrap: wrap; }
    .tag.spell { border-color: var(--accent); color: var(--accent); }
    .tag.warn { border-color: var(--warn); color: var(--warn); }
    .tag.hurt { border-color: var(--hurt); color: var(--hurt); }
    .card pre.display { background: none; border: 0; padding: 0 0 4px; }
    .extra { display: flex; flex-direction: column; gap: 2px; }
    .extra .note { font-size: .86rem; }
    .status { color: var(--ink-2); }
    .whole { border-top: 1px solid var(--rule); }
    .levelup { border: 1px solid var(--accent); border-left-width: 4px; background: var(--accent-soft); border-radius: 4px; padding: 10px 12px; display: flex; flex-direction: column; gap: 6px; min-width: 0; }
    .levelup .label { color: var(--accent); }
    .levelup pre.display { background: none; border: 0; padding: 4px 0; }
    @media (max-width: 380px) { .levelup { padding: 10px; } }
  `],
})
export class Party {
  private readonly store = inject(TableStore);
  readonly party = this.store.party;
  /** The PC's banked points and the spending menu, while there are some. */
  readonly levelUp = computed(() => {
    const s = this.store.state();
    return s && s.status !== 'ended' ? s.levelUp : null;
  });

  meters(m: Member): Meter[] {
    return [
      { key: 'hp', label: 'HP', now: m.hp, max: m.maxHp, ceiling: m.hpCeiling < m.maxHp ? m.hpCeiling : null },
      { key: 'sta', label: 'STA', now: m.sta, max: m.staMax, ceiling: null },
      { key: 'power', label: 'Power', now: m.power, max: m.powerMax, ceiling: null },
    ];
  }

  kit(m: Member): string[] {
    return Object.entries(m.kit).map(([k, n]) => `${k} x${n}`);
  }

  spells(m: Member): string[] {
    return Object.entries(m.spells).map(([k, n]) => `${k} ${n}`);
  }

  /** Blood, tongues and the traits, one line each (the traits as the sheet joins them). */
  extra(m: Member): string[] {
    return [m.blood, m.tongues, m.traits.join('; ')].filter(Boolean);
  }

  cap(s: string): string {
    return s.charAt(0).toUpperCase() + s.slice(1);
  }

  pct(now: number, max: number): number {
    return max > 0 ? Math.max(0, Math.min(100, (now / max) * 100)) : 0;
  }
}
