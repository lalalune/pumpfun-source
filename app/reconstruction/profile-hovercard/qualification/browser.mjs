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
const sourceFiles = ['reconstruction/profile-hovercard/client.mjs', 'reconstruction/profile-hovercard/client.d.mts',
  'reconstruction/profile-hovercard/qualification/browser.mjs', 'reconstruction/profile-hovercard/qualification/fixture.mjs'];
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
const record = { scope: 'Standalone real React/compiler; complete profile hover owner with synthetic query/provider/financial-reader/display/clock/clipboard/render ports. No original provider or financial acquisition, auth/follow, operator clipboard or action execution.',
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
async function observed() { return page.evaluate(() => window.harness.observe()); }
async function scenario(name, run) {
  const row = { name, startedAt: new Date().toISOString() }; record.cases.push(row);
  try { await run(row); row.status = 'PASS'; }
  catch (e) { row.status = 'FAIL'; row.error = String(e.stack ?? e); await page.screenshot({ path: path.join(output, `failure-${record.cases.length}.png`) }).catch(() => {}); throw e; }
  finally { row.endedAt = new Date().toISOString(); }
}
try{
 server.listen(0,'127.0.0.1');await once(server,'listening');record.origin=`http://127.0.0.1:${server.address().port}`;
 browser=await chromium.launch({headless:true});context=await browser.newContext({viewport:{width:1000,height:850}});await context.tracing.start({screenshots:true,snapshots:true,sources:true});page=await context.newPage();
 page.on('pageerror',error=>record.pageErrors.push(String(error.stack??error)));await page.route('**/*',route=>{if(new URL(route.request().url()).origin===record.origin)return route.continue();record.blockedRequests.push(route.request().url());return route.abort('blockedbyclient');});
 await page.goto(record.origin);await page.waitForFunction(()=>!!window.harness);const trigger=page.getByRole('button',{name:'Supplied profile trigger',exact:true}),display=page.getByRole('tooltip',{name:'Supplied profile display',exact:true});
 await trigger.waitFor();
 await scenario('native trigger to complete pending display and exact query identity/order/options',async row=>{
  assert.equal(await display.count(),0);row.closed=await observed();assert.equal(row.closed.summaryOptions.enabled,false);assert.equal(row.closed.pnlOptions.enabled,false);assert.equal(row.closed.profileOptions.enabled,false);
  assert.deepEqual(row.closed.calls.slice(0,7).map(c=>c[0]==='query'?c[0]+':'+c[1]:c[0]),['config','verified','profile','config','query:summary','config','query:pnl']);
  await trigger.focus();await page.keyboard.press('Enter');await display.waitFor();row.open=await observed();assert.equal(row.open.summaryOptions.enabled,true);assert.equal(row.open.pnlOptions.enabled,true);assert.equal(row.open.profileOptions.enabled,true);assert.equal(row.open.profileOptions.userIdentifier,'fixture-address-A');assert.ok(row.open.calls.some(c=>c[0]==='verified'&&c[1]==='fixture-user-id'));
  assert.equal(await page.locator('[data-port-root]').getAttribute('data-open-delay'),'500');assert.equal(await page.locator('[data-port-root]').getAttribute('data-close-delay'),'100');assert.equal(await display.getAttribute('data-side'),'top');assert.equal(await display.getAttribute('data-align'),'center');assert.equal(await display.getAttribute('data-collision-padding'),'12');assert.ok(!row.open.calls.some(c=>c[0].startsWith('read-')));
 });
 await scenario('in-memory required read callbacks to supplied identity/stats/badge and exact request arguments',async row=>{
  await page.evaluate(()=>window.harness.executeReads());await page.getByTestId('user-profile-hover-bio').waitFor();assert.equal(await page.getByTestId('user-profile-hover-bio').innerText(),'Supplied bio.');assert.ok((await page.getByTestId('user-profile-hover-stats').innerText()).includes('providedMoney:123'));assert.ok((await page.getByTestId('user-profile-hover-stats').innerText()).includes('providedSigned:-5'));assert.ok((await page.getByTestId('user-profile-hover-follows').innerText()).includes('providedCount:12'));assert.equal(await page.getByLabel('Supplied verified badge').count(),1);
  row.read=await observed();assert.deepEqual(row.read.calls.find(c=>c[0]==='read-summary')[1],{profileApiUrl:'https://supplied.invalid/profile',userAddress:'fixture-address-A'});assert.deepEqual(row.read.calls.find(c=>c[0]==='read-pnl').slice(1),['https://supplied.invalid/client','fixture-address-A']);assert.deepEqual(row.read.summaryOptions.key,['balanceSummary','fixture-address-A']);assert.deepEqual(row.read.pnlOptions.key,['userProfileHoverWindowPnl','1w','fixture-address-A']);
 });
 await scenario('complete fallback/X/squad/opaque-follow display handoffs without remote navigation or images',async row=>{
  await page.evaluate(()=>window.harness.social());await page.getByLabel('View @supplied on X',{exact:true}).waitFor();assert.equal(await page.getByLabel('View @supplied on X',{exact:true}).getAttribute('href'),'https://supplied.invalid/x');assert.equal(await page.getByLabel('View @supplied on X',{exact:true}).getAttribute('rel'),'noreferrer');assert.equal(await page.getByLabel('View @supplied on X',{exact:true}).getAttribute('target'),'_blank');assert.equal(await page.getByTestId('user-profile-hover-squad').getAttribute('href'),'/supplied-squad/fixture-squad');assert.equal(await page.getByTestId('user-profile-hover-squad').getAttribute('title'),'Squad: Squad');
  assert.ok((await page.getByTestId('user-profile-hover-identity').innerText()).includes('Fallback User'));const avatar=page.locator('[data-avatar-address="fixture-address-A"]').first();assert.equal(await avatar.getAttribute('data-avatar-src'),'');assert.equal(await avatar.getAttribute('data-avatar-prefix'),' https://supplied.invalid/ipfs/ ');assert.equal(await page.locator('[data-follow-slot]').innerText(),'Provided follow slot only');row.display=await observed();
 });
 await scenario('source immediate/30s registration and dependency/close cleanup with explicit manual clock port',async row=>{
  row.initial=await observed();const initial=row.initial.timers.find(t=>t.kind==='interval');assert.ok(initial);assert.equal(initial.delay,30000);await page.evaluate(()=>window.harness.tickIntervals());await page.waitForFunction(()=>document.querySelector('[data-testid="user-profile-hover-updated"]').textContent.includes('providedTime:123000:1'));
  await page.evaluate(()=>window.harness.changeTimestamp());await page.waitForFunction(()=>document.querySelector('[data-testid="user-profile-hover-updated"]').textContent.includes('456000'));row.changed=await observed();assert.ok(!row.changed.timers.some(t=>t.id===initial.id));assert.equal(row.changed.timers.filter(t=>t.kind==='interval').length,1);
  await trigger.click();await display.waitFor({state:'hidden'});row.closed=await observed();assert.equal(row.closed.timers.filter(t=>t.kind==='interval').length,0);assert.equal(row.closed.summaryOptions.enabled,false);await trigger.click();await display.waitFor();
 });
 await scenario('supplied error/pending/recovery and disabled display branch preserve independent read state',async row=>{
  await page.evaluate(()=>window.harness.error());await page.getByText('Balance unavailable',{exact:true}).waitFor();assert.ok((await page.getByTestId('user-profile-hover-stats').innerText()).includes('providedSigned:0'));await page.evaluate(()=>window.harness.pending());await page.waitForFunction(()=>document.querySelector('[data-testid="user-profile-hover-updated"] span[aria-hidden="true"]'));
  await page.evaluate(()=>window.harness.success());await page.waitForFunction(()=>document.querySelector('[data-testid="user-profile-hover-stats"]').textContent.includes('providedMoney:123'));await page.evaluate(()=>window.harness.disabled(true));await display.waitFor({state:'hidden'});row.disabled=await observed();assert.equal(row.disabled.summaryOptions.enabled,true);assert.equal(row.disabled.pnlOptions.enabled,true);assert.equal(await trigger.count(),1);await page.evaluate(()=>window.harness.disabled(false));await trigger.click();await display.waitFor();
 });
 await scenario('in-memory deferred clipboard/old callback completion and source-vs-host timer cleanup',async row=>{
  await page.getByRole('button',{name:'Copy address',exact:true}).click();assert.equal(await page.getByRole('button',{name:'Address copied',exact:true}).count(),0);await page.evaluate(()=>window.harness.newAddress());await page.evaluate(()=>window.harness.resolveClipboard());await page.getByRole('button',{name:'Address copied',exact:true}).waitFor();row.copied=await observed();assert.deepEqual(row.copied.calls.filter(c=>c[0]==='clipboard').map(c=>c[1]),['fixture-address-A']);assert.equal(row.copied.address,'fixture-address-B');assert.ok(row.copied.timers.some(t=>t.kind==='timeout'&&t.delay===2000));
  row.unmounted=await page.evaluate(()=>window.harness.unmount());assert.equal(row.unmounted.subscribers,0);assert.equal(row.unmounted.timers.filter(t=>t.kind==='interval').length,0);assert.equal(row.unmounted.timers.filter(t=>t.kind==='timeout').length,1,'source retains feedback timeout');row.environmentCleanup=await page.evaluate(()=>window.harness.cleanupEnvironment());assert.equal(row.environmentCleanup.timers.length,0);
 });
 assert.equal(record.cases.length,6);assert.deepEqual(record.pageErrors,[]);assert.deepEqual(record.blockedRequests,[]);record.status='PASS';
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
