import { Component, OnInit, computed, effect, inject, untracked } from '@angular/core';
import { Drawer } from './drawer/drawer';
import { BAR_TABS, MORE_ICON, MORE_TABS, PARTY_ICON, STORY_ICON } from './drawer/tabs';
import { Answer } from './panels/answer';
import { Chronicle } from './panels/chronicle';
import { Party } from './panels/party';
import { Story } from './panels/story';
import { TableStore } from './store';
import { Ui } from './ui';
import { Unread } from './unread';

/**
 * The shell: a header, then three zones on wide screens (the party, the
 * page, the drawer), two below 1240px (the party folds into the drawer), and
 * one at a time on phones, with a bottom bar. `data-paused` and `data-over`
 * on :root say when a fight stands paused and when the game is over.
 */
@Component({
  selector: 'rpg-root',
  imports: [Story, Answer, Chronicle, Party, Drawer],
  template: `
    <div class="app" [attr.data-view]="ui.view()">
      <header class="top">
        <span class="brand">RPG2</span>
        @if (state(); as s) {
          <span class="where">
            <span class="day">Day {{ s.day }}</span>
            <b>{{ s.where }}</b>
          </span>
        }
        @if (store.link() !== 'live') {
          <span class="link" [class]="linkClass()"><span class="dot" aria-hidden="true"></span>{{ linkWord() }}</span>
        }
      </header>

      <div class="zones">
        <aside class="line" aria-label="The party"><rpg-party /></aside>

        <main class="page">
          @if (state()) {
            <rpg-story />
            <rpg-answer />
            <rpg-chronicle />
          } @else {
            <section class="notice">
              <p>{{ notice() }}</p>
            </section>
          }
        </main>

        <aside class="drawer" aria-label="The drawer"><rpg-drawer /></aside>
      </div>

      <nav class="bottom" aria-label="Sections">
        <button type="button" [attr.aria-current]="ui.view() === 'story'" (click)="ui.view.set('story')">
          <svg viewBox="0 0 24 24" aria-hidden="true">@for (d of storyIcon; track $index) {<path [attr.d]="d" />}</svg>Story
        </button>
        <button type="button" [attr.aria-current]="ui.view() === 'party'" (click)="ui.open('party')">
          <svg viewBox="0 0 24 24" aria-hidden="true">@for (d of partyIcon; track $index) {<path [attr.d]="d" />}</svg>Party
          @if (unread.marks().has('party')) {<i class="unread" aria-hidden="true"></i><span class="vh">, changed</span>}
        </button>
        @for (t of tabs; track t.id) {
          <button type="button" [attr.aria-current]="ui.view() === 'drawer' && ui.drawerTab() === t.id" (click)="ui.open(t.id)">
            <svg viewBox="0 0 24 24" aria-hidden="true">@for (d of t.icon; track $index) {<path [attr.d]="d" />}</svg>{{ t.label }}
            @if (unread.marks().has(t.id)) {<i class="unread" aria-hidden="true"></i><span class="vh">, changed</span>}
          </button>
        }
        <button type="button" class="more" [attr.aria-current]="inMore()" (click)="ui.openMore()">
          <svg viewBox="0 0 24 24" aria-hidden="true">@for (d of moreIcon; track $index) {<path [attr.d]="d" />}</svg>More
          @if (moreUnread()) {<i class="unread" aria-hidden="true"></i><span class="vh">, changed</span>}
        </button>
      </nav>
    </div>
  `,
})
export class App implements OnInit {
  readonly store = inject(TableStore);
  readonly ui = inject(Ui);
  readonly unread = inject(Unread);
  readonly state = this.store.state;
  readonly tabs = BAR_TABS;
  readonly storyIcon = STORY_ICON;
  readonly partyIcon = PARTY_ICON;
  readonly moreIcon = MORE_ICON;

  /** Looking at one of the tabs under More. */
  readonly inMore = computed(() => this.ui.view() === 'drawer' && MORE_TABS.some((t) => t.id === this.ui.drawerTab()));
  readonly moreUnread = computed(() => MORE_TABS.some((t) => this.unread.marks().has(t.id)));

  /** The newest fight's id: a string, so a re-read of the same state changes nothing. */
  private readonly lastFight = computed(() => this.state()?.lastFight ?? null);

  constructor() {
    // A new fight on the page: the Fight tab turns to it (the newest).
    effect(() => {
      this.lastFight();
      untracked(() => this.ui.fight.set(null));
    });
    // What the game waits on dresses the page (styles.css reads these).
    effect(() => {
      const s = this.state();
      const root = document.documentElement.dataset;
      if (s && s.status !== 'ended' && s.pause) root['paused'] = 'true';
      else delete root['paused'];
      if (s?.status === 'ended') root['over'] = s.over ?? 'true';
      else delete root['over'];
    });
  }

  ngOnInit(): void {
    void this.store.connect();
  }

  readonly linkWord = computed(() => {
    switch (this.store.link()) {
      case 'live': return 'Live';
      case 'connecting': return 'Connecting';
      case 'unavailable': return 'Not connected';
      case 'lost': return 'Connection lost';
    }
  });

  readonly linkClass = computed(() => {
    const link = this.store.link();
    return link === 'live' ? 'live' : link === 'connecting' ? '' : 'broken';
  });

  readonly notice = computed(() => {
    switch (this.store.link()) {
      case 'connecting':
        return 'Connecting.';
      case 'live':
        return 'No game yet. Ask the DM in Claude Code to start one. The first scene appears here.';
      case 'lost':
        return 'The connection dropped. Reload the page.';
      default:
        return 'This page has no line to the game. Open it on claude.ai, signed in.';
    }
  });
}
