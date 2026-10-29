import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';
import { readFile, writeFile, mkdir, stat } from 'node:fs/promises';
import { once } from 'node:events';
import http from 'node:http';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const appRoot = fileURLToPath(new URL('../../../', import.meta.url));
const repoRoot = path.dirname(appRoot);
const args = process.argv.slice(2);
assert.equal(args.length, 4, 'Usage: browser.mjs --source FULL_PUBLIC_OR_LOCAL_SHA --output NEW_DIRECTORY');
assert.equal(args[0], '--source'); assert.match(args[1], /^[a-f0-9]{40}$/); assert.equal(args[2], '--output');
const source = args[1], output = path.resolve(args[3]);
await assert.rejects(stat(output), { code: 'ENOENT' });
await mkdir(output, { recursive: true });
const sha = (b) => createHash('sha256').update(b).digest('hex');
const git = (...a) => execFileSync('git', a, { cwd: repoRoot, env: { ...process.env, GIT_NO_LAZY_FETCH: '1' } });
git('cat-file', '-e', `${source}^{commit}`);
const sourceFiles = ['reconstruction/create-advanced-fee/client.mjs', 'reconstruction/create-advanced-fee/client.d.mts',
  'reconstruction/create-advanced-fee/qualification/browser.mjs', 'reconstruction/create-advanced-fee/qualification/fixture.mjs'];
const sourceBinding = [];
for (const relative of sourceFiles) {
  const bytes = await readFile(path.join(appRoot, relative));
  assert.ok(bytes.equals(git('show', `${source}:app/${relative}`)), `actual source differs: ${relative}`);
  sourceBinding.push({ path: relative, bytes: bytes.length, sha256: sha(bytes), gitBlob: git('rev-parse', `${source}:app/${relative}`).toString().trim() });
}
const frontend = createRequire(path.join(appRoot, 'packages/frontend/package.json'));
const backend = createRequire(path.join(appRoot, 'packages/backend/package.json'));
const esbuild = createRequire(backend.resolve('tsx'))('esbuild');
const { chromium } = frontend('@playwright/test');
const built = await esbuild.build({ entryPoints: [fileURLToPath(new URL('fixture.mjs', import.meta.url))], absWorkingDir: appRoot,
  bundle: true, write: false, platform: 'browser', format: 'iife', metafile: true,
  define: { 'process.env.NODE_ENV': '"development"' },
  alias: { react: frontend.resolve('react'), 'react/jsx-runtime': frontend.resolve('react/jsx-runtime'),
    'react/compiler-runtime': frontend.resolve('react/compiler-runtime'), 'react-dom/client': frontend.resolve('react-dom/client'), 'react-dom': frontend.resolve('react-dom') } });
const bundle = built.outputFiles[0].contents;
const inputs = [];
for (const relative of Object.keys(built.metafile.inputs)) {
  const bytes = await readFile(path.resolve(appRoot, relative)); inputs.push({ path: relative, bytes: bytes.length, sha256: sha(bytes) });
}
for (const row of sourceBinding) if (!inputs.some((r) => r.path === row.path)) inputs.push({ path: row.path, bytes: row.bytes, sha256: row.sha256 });
const record = { scope: 'Standalone real React/compiler; complete selected control with synthetic store/quote/translation/primitive ports. No original provider, app mount, fee projection or service.',
  selectedSource: source, repositoryHead: git('rev-parse', 'HEAD').toString().trim(), sourceBinding, inputs, bundleSha256: sha(bundle),
  cases: [], requests: [], blockedRequests: [], pageErrors: [], startedAt: new Date().toISOString() };
await writeFile(path.join(output, 'INPUTS.json'), JSON.stringify(record, null, 2) + '\n');
await writeFile(path.join(output, 'bundle.js'), bundle);
const server = http.createServer((req, res) => {
  record.requests.push({ method: req.method, path: req.url });
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('Content-Security-Policy', "default-src 'none'; script-src 'self'; connect-src 'none'; style-src 'none'; img-src 'none'");
  if (req.method !== 'GET') { res.writeHead(405); return res.end(); }
  if (req.url === '/') { res.setHeader('Content-Type', 'text/html'); return res.end('<!doctype html><meta charset="utf-8"><title>Synthetic Create control</title><div id="root"></div><script src="/bundle.js"></script>'); }
  if (req.url === '/bundle.js') { res.setHeader('Content-Type', 'text/javascript'); return res.end(bundle); }
  res.writeHead(404); res.end();
});
let browser, context, page;
const fieldId = 'create-coin-creator-fee-percent', errorId = `${fieldId}-error`;
async function observed() { return page.evaluate(() => window.harness.observe()); }
async function scenario(name, run) {
  const row = { name, startedAt: new Date().toISOString() }; record.cases.push(row);
  try { await run(row); row.status = 'PASS'; }
  catch (e) { row.status = 'FAIL'; row.error = String(e.stack ?? e); await page.screenshot({ path: path.join(output, `failure-${record.cases.length}.png`) }).catch(() => {}); throw e; }
  finally { row.endedAt = new Date().toISOString(); }
}
try {
  server.listen(0, '127.0.0.1'); await once(server, 'listening'); record.origin = `http://127.0.0.1:${server.address().port}`;
  browser = await chromium.launch({ headless: true }); context = await browser.newContext({ viewport: { width: 850, height: 700 } });
  await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
  page = await context.newPage(); page.on('pageerror', (e) => record.pageErrors.push(String(e.stack ?? e)));
  await page.route('**/*', (route) => {
    if (new URL(route.request().url()).origin === record.origin) return route.continue();
    record.blockedRequests.push(route.request().url()); return route.abort('blockedbyclient');
  });
  await page.goto(record.origin); await page.waitForFunction(() => !!window.harness);
  const field = page.locator(`#${fieldId}`), error = page.locator(`#${errorId}`);
  await scenario('actual pair-kind visibility and empty optional control attributes', async (row) => {
    row.initial = await observed(); assert.equal(await field.count(), 0);
    await page.evaluate(() => window.harness.setQuote('usdc')); assert.equal(await field.count(), 0);
    await page.evaluate(() => window.harness.setQuote('pump')); await field.waitFor();
    assert.equal(await field.inputValue(), ''); assert.equal(await field.getAttribute('type'), 'text');
    assert.equal(await field.getAttribute('inputmode'), 'decimal'); assert.equal(await field.getAttribute('maxlength'), '4');
    assert.equal(await field.getAttribute('aria-invalid'), null); assert.equal(await error.count(), 0);
    assert.equal(await page.locator(`label[for="${fieldId}"]`).innerText(), 'A Creator fee (Optional)');
    assert.equal(await page.locator('section').getAttribute('data-synthetic-default-open'), 'true');
    await page.evaluate(() => window.harness.setQuote('stock')); await field.waitFor();
    row.visible = await observed();
  });
  await scenario('trusted field entry propagates optional, decimal and range states to errors/ARIA', async (row) => {
    row.steps = [];
    for (const [value, invalid] of [['0', true], ['.01', false], ['1.', false], ['3.00', false], ['3.01', true], ['', false]]) {
      await field.fill(value); assert.equal(await field.inputValue(), value);
      assert.equal((await observed()).value, value); assert.equal(await field.getAttribute('aria-invalid'), invalid ? 'true' : null);
      assert.equal(await field.getAttribute('aria-describedby'), invalid ? errorId : null);
      assert.equal(await error.count(), invalid ? 1 : 0);
      if (invalid) assert.equal(await error.innerText(), 'A invalid 0.01 to 3');
      row.steps.push({ value, invalid, state: await observed() });
    }
  });
  await scenario('native text input preserves raw whitespace and enforces declared four-character maxlength', async (row) => {
    await field.fill(' 1'); assert.equal((await observed()).value, ' 1'); assert.equal(await field.getAttribute('aria-invalid'), 'true');
    await field.fill(''); await field.pressSequentially('1.234');
    assert.equal(await field.inputValue(), '1.23'); assert.equal((await observed()).value, '1.23');
    assert.equal(await field.getAttribute('aria-invalid'), null); row.after = await observed();
  });
  await scenario('hidden quote transition retains local value and restores the actual error consumer', async (row) => {
    await field.fill('0'); await page.evaluate(() => window.harness.setQuote('sol')); assert.equal(await field.count(), 0);
    assert.equal((await observed()).value, '0'); await page.evaluate(() => window.harness.setQuote('stock')); await field.waitFor();
    assert.equal(await field.inputValue(), '0'); assert.equal(await error.innerText(), 'A invalid 0.01 to 3'); row.after = await observed();
  });
  await scenario('real compiler memo updates translator-dependent label/error without replacing raw state or callback', async (row) => {
    await page.evaluate(() => window.harness.setLanguage('B'));
    assert.equal(await page.locator(`label[for="${fieldId}"]`).innerText(), 'B Creator fee (Optional)');
    assert.equal(await error.innerText(), 'B invalid 0.01 to 3'); assert.equal(await field.getAttribute('placeholder'), 'B range 0.01 to 3');
    assert.equal(await field.inputValue(), '0'); row.after = await observed(); assert.equal(row.after.callbackSameAsFirst, true);
  });
  await scenario('supplied state callback redraws controlled value and real hook subscriptions clean up', async (row) => {
    await page.evaluate(() => window.harness.setValue('2.50')); assert.equal(await field.inputValue(), '2.50'); assert.equal(await error.count(), 0);
    row.beforeUnmount = await observed(); assert.equal(row.beforeUnmount.callbackSameAsFirst, true);
    row.afterUnmount = await page.evaluate(() => window.harness.unmount());
    assert.equal(row.afterUnmount.subscribers, 0); assert.equal(row.afterUnmount.quoteSubscribers, 0); assert.equal(row.afterUnmount.translationSubscribers, 0);
  });
  assert.equal(record.cases.length, 6); assert.deepEqual(record.pageErrors, []); assert.deepEqual(record.blockedRequests, []); record.status = 'PASS';
} finally {
  if (context) await context.tracing.stop({ path: path.join(output, 'trace.zip') }).catch(() => {});
  if (browser) await browser.close(); record.browserClosed = browser ? !browser.isConnected() : true;
  if (server.listening) await new Promise((resolve) => server.close(resolve)); record.serverListening = server.listening;
  for (const input of record.inputs) {
    const bytes = await readFile(path.resolve(appRoot, input.path)); input.afterRunSha256 = sha(bytes); input.unchanged = input.sha256 === input.afterRunSha256;
  }
  record.endedAt = new Date().toISOString(); await writeFile(path.join(output, 'RESULT.json'), JSON.stringify(record, null, 2) + '\n');
}
assert.ok(record.inputs.every((i) => i.unchanged));
console.log(JSON.stringify({ status: record.status, cases: record.cases.length, pageErrors: record.pageErrors,
  browserClosed: record.browserClosed, serverListening: record.serverListening, allInputsUnchanged: record.inputs.every((i) => i.unchanged) }));
