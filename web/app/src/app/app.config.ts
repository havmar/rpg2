import {
  ApplicationConfig, provideBrowserGlobalErrorListeners, provideZonelessChangeDetection,
} from '@angular/core';

/** Zoneless: signals drive every render, so there is no zone.js and no polyfills.js. */
export const appConfig: ApplicationConfig = {
  providers: [provideBrowserGlobalErrorListeners(), provideZonelessChangeDetection()],
};
