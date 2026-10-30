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
const sourceFiles = ['reconstruction/create-asset-picker/client.mjs', 'reconstruction/create-asset-picker/client.d.mts',
  'reconstruction/create-asset-picker/qualification/browser.mjs', 'reconstruction/create-asset-picker/qualification/fixture.mjs'];
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
const record = { scope: 'Standalone real React/compiler; complete asset picker and inline query with synthetic query/debounce/provider/transport/translation/render ports. No original acquisition, service/provider access, wallet or submission.',
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
try {
 server.listen(0,'127.0.0.1');await once(server,'listening');record.origin=`http://127.0.0.1:${server.address().port}`;
 browser=await chromium.launch({headless:true});context=await browser.newContext({viewport:{width:900,height:750},hasTouch:true});
 await context.tracing.start({screenshots:true,snapshots:true,sources:true});page=await context.newPage();
 page.on('pageerror',error=>record.pageErrors.push(String(error.stack??error)));
 await page.route('**/*',route=>{if(new URL(route.request().url()).origin===record.origin)return route.continue();record.blockedRequests.push(route.request().url());return route.abort('blockedbyclient');});
 await page.goto(record.origin);await page.waitForFunction(()=>!!window.harness);
 const search=()=>page.getByRole('textbox',{name:/web.create.pair_stock_search_placeholder/});
 const category=value=>page.getByRole('tab',{name:'web.create.pair_category_'+value,exact:true});
 const rowButton=name=>page.locator('ul li button').filter({hasText:name});
 async function settle(term){await page.waitForFunction(value=>window.harness.observe().query?.key[2]===value,term);}
 await scenario('supplied pending readiness, actual local input/category filtering and exact stock callback',async row=>{
  assert.equal(await page.locator('li[aria-hidden="true"]').count(),4);assert.equal(await page.getByRole('tablist').count(),0);row.pending=await observed();
  await page.evaluate(()=>window.harness.loaded());await category('all').waitFor();assert.equal(await page.locator('ul li button').count(),3);
  await search().fill('  acme  ');assert.equal(await search().inputValue(),'  acme  ');assert.equal(await page.locator('ul li button').count(),1);await rowButton('Acme').click();row.selected=await observed();
  assert.deepEqual(row.selected.calls.find(c=>c[0]==='stock-selected')[1],{mint:'fixture-stock',sameReference:true});assert.ok((await rowButton('Acme').innerText()).includes('supplied:0'));
 });
 await scenario('real synthetic250ms hook plus exact source queryFn/normalizer to selected Pump row',async row=>{
  await page.evaluate(()=>window.harness.reset());await page.waitForFunction(()=>window.harness.observe().generation===1&&window.harness.observe().query?.key[2]==='');await search().fill('  needle  ');row.before=await observed();assert.equal(row.before.query.enabled,false);
  await settle('needle');row.settled=await observed();assert.equal(row.settled.query.enabled,true);assert.equal(row.settled.query.staleTime,30000);
  assert.ok(row.settled.calls.some(c=>c[0]==='debounce-settled'&&c[1]==='needle'&&c[2]===250&&c[3]>=240));
  row.execution=await page.evaluate(()=>window.harness.execute());assert.equal(row.execution.passed,true);await rowButton('Needle').waitFor();await rowButton('Needle').click();row.selected=await observed();
  const request=row.selected.calls.find(c=>c[0]==='request')[1];assert.equal(request.route,'GET /coins/search-unrestricted');assert.equal(request.credentials,'include');assert.equal(request.signalProvided,true);assert.deepEqual(request.query,{searchTerm:'needle',limit:20,offset:0,includeNsfw:false,sort:'market_cap',order:'DESC',program:'pump',maxDepth:1});
  assert.deepEqual(row.selected.calls.find(c=>c[0]==='pump-selected')[1],{mint:'fixture-pump',sameReference:true});assert.deepEqual(row.selected.ordinary,{created_timestamp:123,rec_id:'rec',is_charity:true});assert.ok(!(await rowButton('Needle').innerText()).includes('supplied:0'));
 });
 await scenario('native category choices hide Pump rows without disabling the actual query',async row=>{
  await category('stocks').click();assert.equal(await rowButton('Needle').count(),0);assert.equal((await observed()).query.enabled,true);assert.ok((await page.locator('ul').innerText()).includes('common.no_results'));
  await category('memes').click();assert.equal(await rowButton('Needle').count(),1);assert.equal((await observed()).query.enabled,true);
  await category('crypto').click();await search().fill('btc');await rowButton('Bitcoin').waitFor();assert.equal(await rowButton('Bitcoin').count(),1);row.crypto=await observed();
  await category('all').click();await search().fill('needle');await settle('needle');await rowButton('Needle').waitFor();
 });
 await scenario('synthetic503 afterResponse to actual error/report/Retry and supplied recovery',async row=>{
  await page.evaluate(()=>{window.harness.clearCalls();window.harness.responseError();});row.failed=await page.evaluate(()=>window.harness.execute());assert.equal(row.failed.passed,false);assert.match(row.failed.error,/Pump coin search failed: 503/);
  await page.getByRole('alert').waitFor();assert.equal(await rowButton('Needle').count(),0);await page.getByRole('button',{name:'Retry supplied query',exact:true}).click();row.retry=await observed();assert.ok(row.retry.calls.some(c=>c[0]==='refetch'));assert.ok(row.retry.calls.some(c=>c[0]==='report'&&c[1].operation==='pair-search'));
  await page.evaluate(()=>window.harness.responseSuccess());await page.evaluate(()=>window.harness.execute());await rowButton('Needle').waitFor();assert.equal(await page.getByRole('alert').count(),0);row.recovered=await observed();
 });
 await scenario('actual raw-first dedup/supported/Mayhem/depth selector and translated row/category consumers',async row=>{
  await page.evaluate(()=>window.harness.eligibility());await page.evaluate(()=>window.harness.execute());await rowButton('Depth One').waitFor();assert.equal(await page.locator('ul li button').count(),3);assert.equal(await rowButton('Supported Quote').count(),1);assert.equal(await rowButton('Second').count(),0);
  await page.evaluate(()=>window.harness.language());await page.getByRole('tab',{name:'changed:web.create.pair_category_all',exact:true}).waitFor();assert.equal(await search().getAttribute('placeholder'),'changed:web.create.pair_stock_search_placeholder');row.changed=await observed();
 });
 await scenario('trusted native mouse/touch propagation and source close plus port subscription/timer cleanup',async row=>{
  const input=search(),bounds=await input.boundingBox();assert.ok(bounds);const before=(await observed()).outerPointers;await page.mouse.click(bounds.x+4,bounds.y+bounds.height/2);assert.equal((await observed()).outerPointers,before);
  await page.touchscreen.tap(bounds.x+4,bounds.y+bounds.height/2);assert.ok((await observed()).outerPointers>before);row.pointers=await observed();
  await page.getByRole('button',{name:'changed:common.close',exact:true}).click();await page.getByText('Supplied parent closed',{exact:true}).waitFor();row.closed=await observed();assert.equal(row.closed.subscribers,1);assert.equal(row.closed.pendingTimers,0);
  row.unmounted=await page.evaluate(()=>window.harness.unmount());assert.equal(row.unmounted.subscribers,0);assert.equal(row.unmounted.pendingTimers,0);
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
