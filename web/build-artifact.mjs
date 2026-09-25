/**
 * Assembles the publishable page.
 *
 *   web/page.html  +  web/app/dist/rpg2/browser/{main.js,styles.css}  ->  web/dist/
 *
 * Run after `npx ng build` in web/app. The published page must not carry its
 * own <!doctype>, <html>, <head> or <body> (the Artifact host supplies that
 * skeleton), so web/page.html holds page content only, with `base href ./`,
 * and this script drops it in beside the bundles as index.html. The build has
 * `outputHashing: none`, so the bundle names are stable, and it is zoneless,
 * so there is no polyfills.js.
 */
import { cp, mkdir, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const web = dirname(fileURLToPath(import.meta.url));
const built = join(web, 'app/dist/rpg2/browser');
const out = join(web, 'dist');
const bundles = ['main.js', 'styles.css'];

const found = await readdir(built).catch(() => {
  throw new Error(`no build in ${built}: run \`npx ng build\` in web/app first`);
});
const stray = found.filter((f) => /\.(js|css)$/.test(f) && !bundles.includes(f));
if (stray.length) {
  // A lazy chunk or a hashed name would be missing from the published files.
  throw new Error(`unexpected bundles ${stray.join(', ')}: the page references only ${bundles.join(', ')}`);
}

const page = await readFile(join(web, 'page.html'), 'utf8');
if (/<!doctype|<html|<head|<body/i.test(page)) {
  throw new Error('page.html must not have a doctype, <html>, <head> or <body>: the host adds them');
}

await rm(out, { recursive: true, force: true });
await mkdir(out, { recursive: true });
for (const name of bundles) {
  if (!page.includes(name)) throw new Error(`page.html never references ${name}`);
  await cp(join(built, name), join(out, name));
}
await writeFile(join(out, 'index.html'), page);

console.log(`web/dist ready: index.html + ${bundles.join(', ')}`);
