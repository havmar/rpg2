import { Type } from '@angular/core';
import { Fight } from '../panels/fight';
import { Fights } from '../panels/fights';
import { MapTab } from '../panels/map';
import { Quests } from '../panels/quests';
import { RecordTab } from '../panels/record';

/**
 * The drawer's tabs, in order. Wide screens show them as tabs on the right.
 * Phones have a bar at the bottom: Story, Party, the tabs marked `bar` (Map
 * and Fight), and More, which opens the rest (Fights, Quests, Record) with a
 * row of chips to switch among them. The bar holds five buttons at most.
 *
 * A tab is one standalone component in `panels/`, reading `TableStore`, and
 * one entry here. The drawer, the phone's bottom bar and the unread marks
 * (`unread.ts`, which needs a signature for a new tab) follow the list.
 */
export interface DrawerTab {
  id: string;
  label: string;
  /** SVG path data on a 24x24 grid, stroked with the current colour. */
  icon: string[];
  component: Type<unknown>;
  /** Inputs for the component, if it takes any. */
  inputs?: Record<string, unknown>;
  /** A button of its own in the phone's bottom bar; the rest are under More. */
  bar?: boolean;
}

export const DRAWER_TABS: DrawerTab[] = [
  {
    id: 'map', label: 'Map', icon: ['M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2z', 'M9 4v14M15 6v14'],
    component: MapTab, bar: true,
  },
  {
    id: 'fight', label: 'Fight', icon: ['M5 19L19 5M14 5h5v5M5 5l14 14M5 14v5h5'],
    component: Fight, bar: true,
  },
  {
    id: 'fights', label: 'Fights', icon: ['M6 21V4h12l-2.5 4L18 12H6'],
    component: Fights,
  },
  {
    id: 'quests', label: 'Quests', icon: ['M7 3h10v18l-5-4-5 4z'],
    component: Quests,
  },
  {
    id: 'record', label: 'Record', icon: ['M5 4h14v16H5z', 'M8 8h8M8 12h8M8 16h5'],
    component: RecordTab,
  },
];

/** The phone's bottom bar has these; More holds the rest. */
export const BAR_TABS = DRAWER_TABS.filter((t) => t.bar);
export const MORE_TABS = DRAWER_TABS.filter((t) => !t.bar);
export const MORE_ICON = ['M4 12a1 1 0 1 0 2 0a1 1 0 1 0-2 0M11 12a1 1 0 1 0 2 0a1 1 0 1 0-2 0M18 12a1 1 0 1 0 2 0a1 1 0 1 0-2 0'];

/** The two views every width has besides the drawer's tabs. */
export const STORY_ICON = ['M4 5h11a4 4 0 0 1 4 4v10H8a4 4 0 0 1-4-4z', 'M8 9h7M8 13h7'];
export const PARTY_ICON = ['M9 8a3 3 0 1 0 0.01 0M3 20c0-3.5 2.7-6 6-6s6 2.5 6 6', 'M16 5.5a3 3 0 0 1 0 5.5M18 14.5c1.8.8 3 2.8 3 5.5'];
