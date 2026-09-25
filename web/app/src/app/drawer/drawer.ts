import { Component, computed, inject } from '@angular/core';
import { NgComponentOutlet } from '@angular/common';
import { Party } from '../panels/party';
import { Ui } from '../ui';
import { Unread } from '../unread';
import { DRAWER_TABS, DrawerTab, MORE_TABS } from './tabs';

const PARTY_TAB: DrawerTab = { id: 'party', label: 'Party', icon: [], component: Party };

/**
 * The right-hand zone: a row of tabs (wrapping when they do not fit) and the
 * selected tab's panel. On a phone the row is only there under More, as chips
 * for More's own tabs; the bottom bar holds the rest.
 */
@Component({
  selector: 'rpg-drawer',
  imports: [NgComponentOutlet],
  template: `
    <div class="tabs" role="tablist" aria-label="The drawer" [class.more]="inMore()">
      @for (t of tabs(); track t.id) {
        <button type="button" role="tab" [id]="'tab-' + t.id" [attr.aria-selected]="t.id === current().id"
          [attr.aria-controls]="'panel-' + t.id" [attr.data-tab]="t.id" (click)="ui.open(t.id)"
          >{{ t.label }}@if (unread.marks().has(t.id)) {<i class="unread" aria-hidden="true"></i><span class="vh">, changed</span>}</button>
      }
    </div>
    <section class="panel" role="tabpanel" [id]="'panel-' + current().id" [attr.aria-labelledby]="'tab-' + current().id">
      <ng-container *ngComponentOutlet="current().component; inputs: current().inputs ?? {}" />
    </section>
  `,
  styles: [`
    :host { display: flex; flex-direction: column; min-height: 0; }
    .tabs {
      display: flex; flex-wrap: wrap; gap: 0 4px; border-bottom: 1px solid var(--rule); padding: 0 12px;
      position: sticky; top: 0; background: var(--paper-2); z-index: 2;
    }
    .tabs button {
      position: relative; border: 0; background: none; min-height: 48px; padding: 0 10px; font-family: var(--mono);
      font-size: .78rem; letter-spacing: .06em; text-transform: uppercase; color: var(--ink-2);
      border-bottom: 2px solid transparent; white-space: nowrap;
    }
    .tabs button[aria-selected="true"] { color: var(--ink); border-bottom-color: var(--accent); }
    .unread { position: absolute; top: 10px; right: 2px; width: 7px; height: 7px; border-radius: 50%; background: var(--accent); }
    .panel { padding: 18px 18px 50px; display: flex; flex-direction: column; gap: 16px; min-width: 0; }
    @media (max-width: 900px) {
      .tabs { display: none; }
      .tabs.more { display: flex; flex-wrap: nowrap; overflow-x: auto; gap: 8px; padding: 10px 16px; scrollbar-width: none; }
      .tabs.more button {
        flex: 0 0 auto; padding: 0 16px; min-height: 44px; border: 1px solid var(--rule); border-radius: 22px;
        background: var(--paper);
      }
      .tabs.more button[aria-selected="true"] { border-color: var(--accent); background: var(--accent-soft); color: var(--ink); }
      .tabs.more .unread { top: 5px; right: 6px; }
      .panel { padding: 18px 16px 40px; }
    }
  `],
})
export class Drawer {
  readonly ui = inject(Ui);
  readonly unread = inject(Unread);

  /** Party is a drawer tab only when the party is not on screen beside it; a phone chips More's tabs only. */
  readonly tabs = computed(() =>
    this.ui.narrow() ? MORE_TABS : this.ui.wide() ? DRAWER_TABS : [PARTY_TAB, ...DRAWER_TABS]);

  /** On a phone, looking at one of the tabs under More. */
  readonly inMore = computed(() => this.ui.narrow() && MORE_TABS.some((t) => t.id === this.ui.drawerTab()));

  readonly current = computed<DrawerTab>(() => {
    const id = this.ui.drawerTab();
    return [PARTY_TAB, ...DRAWER_TABS].find((t) => t.id === id) ?? DRAWER_TABS[0];
  });
}
