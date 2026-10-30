// Authored standalone React/loopback infrastructure; approach credited to1846
// and this author's1879/1897/1961 hosts. No original CSS/provider/library runtime.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFile, writeFile, mkdir, stat } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import http from 'node:http';
import { once } from 'node:events';

const app = fileURLToPath(new URL('../..', import.meta.url));
assert.equal(process.argv.length, 4, 'usage: browser.mjs --output NEW_DIRECTORY');
assert.equal(process.argv[2], '--output');
const output = path.resolve(process.argv[3]);
await assert.rejects(stat(output), { code: 'ENOENT' });
await mkdir(output, { recursive: true });
const frontend = createRequire(path.join(app, 'packages/frontend/package.json'));
const backend = createRequire(path.join(app, 'packages/backend/package.json'));
const esbuild = createRequire(backend.resolve('tsx'))('esbuild');
const { chromium } = frontend('@playwright/test');
const sha = (bytes) => createHash('sha256').update(bytes).digest('hex');
const built = await esbuild.build({ entryPoints: [fileURLToPath(new URL('./browser-fixture.mjs', import.meta.url))], absWorkingDir: app,
  bundle: true, write: false, platform: 'browser', format: 'iife', metafile: true,
  define: { 'process.env.NODE_ENV': '"development"' },
  alias: { react: frontend.resolve('react'), 'react/jsx-runtime': frontend.resolve('react/jsx-runtime'),
    'react/compiler-runtime': frontend.resolve('react/compiler-runtime'), 'react-dom/client': frontend.resolve('react-dom/client') } });
const bundle = built.outputFiles[0].contents;
const inputs = [];
await writeFile(path.join(output, 'bundle.js'), bundle);
for (const name of Object.keys(built.metafile.inputs)) {
  const bytes = await readFile(path.resolve(app, name));
  inputs.push({ path: path.relative(app, path.resolve(app, name)), bytes: bytes.length, sha256: sha(bytes) });
}
const record = { sourceHead: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: app, encoding: 'utf8' }).trim(),
  scope: 'Actual complete127memo presentation frame/83memo grid/pagination/error callbacks under React/compiler/nativeIO. All module providers/cards/animation/telemetry/dynamic/table/policy inputs are authored synthetic capabilities; whole root provider/network/auth runtime is source-only.',
  controller: { path: 'reconstruction/explore-presentation/browser.mjs', sha256: sha(await readFile(fileURLToPath(import.meta.url))) },
  proofSha256: sha(await readFile(path.join(app, 'reconstruction/explore-presentation/PROVENANCE.json'))), inputs, bundleSha256: sha(bundle),
  runtime: { node: process.version, react: frontend('react/package.json').version, esbuild: esbuild.version, playwright: frontend('@playwright/test/package.json').version },
  observations: [], pageErrors: [], unexpected: [], requests: [] };
await writeFile(path.join(output, 'INPUTS.json'), JSON.stringify(record, null, 2) + '\n');
const server = http.createServer((req, res) => {
  record.requests.push({ method: req.method, path: req.url });
  res.setHeader('Cache-Control', 'no-store');
  if (req.method !== 'GET') { res.writeHead(405); res.end(); return; }
  if (req.url === '/bundle.js') { res.setHeader('Content-Type', 'text/javascript'); res.end(bundle); return; }
  if (req.url === '/') {
    res.setHeader('Content-Type', 'text/html');
    res.end('<!doctype html><meta charset="utf-8"><title>Authored Explore host</title><style>body{margin:0}article{height:64px;width:220px}ul{display:flex;gap:10px;list-style:none}nav{margin:10px}.grid{display:grid;grid-template-columns:220px 220px;gap:8px}svg{width:80px;height:65px}</style><div id="root"></div><script src="/bundle.js"></script>');
    return;
  }
  res.writeHead(404); res.end();
});
let browser, context, page;
const observe = () => page.evaluate(() => window.harness.observe());
async function save(name) { record.observations.push({ name, state: await observe() }); }
async function update(name) {
  const before = (await observe()).committed;
  await page.evaluate((name) => window.harness[name](), name);
  await page.waitForFunction((before) => window.harness.observe().committed > before, before);
}
try {
  server.listen(0, '127.0.0.1'); await once(server, 'listening');
  record.origin = `http://127.0.0.1:${server.address().port}`;
  browser = await chromium.launch({ headless: true }); context = await browser.newContext();
  await context.route('**/*', (route) => {
    if (new URL(route.request().url()).origin !== record.origin || route.request().method() !== 'GET') {
      record.unexpected.push(route.request().url()); return route.abort();
    }
    return route.continue();
  });
  await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
  page = await context.newPage(); page.on('pageerror', (error) => record.pageErrors.push(String(error.stack ?? error)));
  await page.goto(record.origin); await page.waitForFunction(() => window.harness?.observe().committed > 0);
  assert.equal(await page.locator('[data-card]').count(), 2);
  assert.equal(await page.locator('[data-card="A"]').getAttribute('data-name'), 'first A');
  let state = await observe(); assert.equal(state.activeObservers, 1);
  assert.equal(state.observers[0].options.threshold, 1);
  assert.deepEqual(state.visibility.at(-1), { mints: ['A', 'B'], enabled: true });
  assert.deepEqual(state.polling.at(-1).mints, ['A']);
  await save('actual presentation→deduplicated grid retains first mint and distinct supplied visibility/impression/polling/card handoffs');

  await page.waitForFunction(() => document.querySelector('[data-card="A"]')?.dataset.viewport === 'true');
  state = await observe(); assert.ok(state.observers[0].callbacks.some((entries) => entries.some(({ id, isIntersecting }) => id === 'A' && isIntersecting)));
  await save('real native threshold1 observer drives original500ms state/ref/effect viewport callback into supplied card props');

  await page.locator('[data-card="A"]').hover();
  assert.equal((await observe()).hover.at(-1), true);
  await page.mouse.move(800, 500); assert.equal((await observe()).hover.at(-1), false);
  await save('grid pointer entry/exit preserves original animation-pause callback ordering');

  const next = page.locator('a[rel="next"]');
  assert.equal(await next.getAttribute('href'), '/explore?q=kept&page=3');
  await next.click(); assert.equal((await observe()).pages.at(-1), 4);
  assert.equal(page.url(), record.origin + '/');
  await save('canonical committed query is kept in page href; actual original link callback prevents navigation and hands offset4 to supplied owner');

  await update('error'); await page.getByTestId('home-feed-load-failed').waitFor();
  await page.getByRole('button', { name: 'web.common.try_again' }).click();
  assert.equal((await observe()).retry.length, 1);
  await update('busy');
  const busyRetry = page.getByRole('button', { name: 'web.common.try_again' });
  await busyRetry.focus();
  assert.equal(await busyRetry.getAttribute('aria-disabled'), 'true');
  assert.equal(await busyRetry.evaluate((button) => button.disabled), false);
  await busyRetry.press('Enter');
  assert.equal((await observe()).retry.length, 1);
  await save('social-terminal empty/no-search error uses complete31memo failure frame; native keyboard activation reaches aria-busy callback guard without repeated retry');

  await page.evaluate(() => document.activeElement?.blur());
  await update('recover'); await page.waitForFunction(() => document.activeElement?.classList.contains('outline-none'));
  assert.equal(await page.locator('[data-card]').count(), 2);
  await save('source error→recovery effect restores focus only from body to the actual social-terminal presentation owner');

  await update('filters'); assert.equal(await page.locator('a[rel="next"]').count(), 0);
  await update('table'); await page.locator('[data-synthetic-table]').waitFor();
  assert.match(await page.locator('[data-synthetic-table]').textContent(), /host-canonical-filter/);
  await save('active-filter pagination suppression and exact table prop handoff remain distinct; table/dynamic implementation is synthetic');

  await page.evaluate(() => window.harness.unmount()); state = await observe();
  assert.equal(state.activeObservers, 0); assert.equal(state.timers, 0); assert.deepEqual(state.observedPorts, []);
  assert.equal(state.hover.at(-1), false); assert.equal(await page.locator('#root').textContent(), '');
  await save('source grid observer/timer/ref and hover cleanup plus authored host unmount leave no owned subscription; no provider cleanup inference');
  assert.deepEqual(record.pageErrors, []); assert.deepEqual(record.unexpected, []); record.result = 'PASS';
} catch (error) {
  record.result = 'FAIL'; record.error = String(error.stack ?? error);
  if (page) { record.last = await observe().catch(() => null); await page.screenshot({ path: path.join(output, 'failure.png') }).catch(() => {}); }
  throw error;
} finally {
  if (context) await context.tracing.stop({ path: path.join(output, 'trace.zip') }).catch(() => {});
  if (browser) await browser.close();
  if (server.listening) { server.close(); server.closeAllConnections(); await once(server, 'close'); }
  record.cleanup = { browserClosed: !browser || !browser.isConnected(), serverStopped: !server.listening };
  await writeFile(path.join(output, 'RESULT.json'), JSON.stringify(record, null, 2) + '\n');
}
console.log(JSON.stringify({ result: record.result, observations: record.observations.length, output }));
