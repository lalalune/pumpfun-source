// Standalone React/DOM proof. Infrastructure approach credits #1846; no Next.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFile, writeFile, mkdir, stat } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import http from 'node:http';
import { once } from 'node:events';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const app = fileURLToPath(new URL('../..', import.meta.url));
assert.ok([4,6].includes(process.argv.length), 'usage: browser.mjs --output NEW_DIRECTORY [--from 3]'); assert.equal(process.argv[2], '--output');
const from=process.argv.length===6?(assert.equal(process.argv[4],'--from'),Number(process.argv[5])):1;
assert.ok([1,3].includes(from),'only full or preserved-first-two continuation is supported');
const output = path.resolve(process.argv[3]); await assert.rejects(stat(output), { code: 'ENOENT' }); await mkdir(output, { recursive: true });
const frontend = createRequire(path.join(app, 'packages/frontend/package.json'));
const backend = createRequire(path.join(app, 'packages/backend/package.json'));
const esbuild = createRequire(backend.resolve('tsx'))('esbuild'), { chromium } = frontend('@playwright/test');
const sha = (b) => createHash('sha256').update(b).digest('hex');
const built = await esbuild.build({ entryPoints: [fileURLToPath(new URL('./fixture.mjs', import.meta.url))],
  absWorkingDir: app, bundle: true, write: false, platform: 'browser', format: 'iife', metafile: true,
  define: { 'process.env.NODE_ENV': '"development"' }, alias: { react: frontend.resolve('react'),
    'react/jsx-runtime': frontend.resolve('react/jsx-runtime'), 'react/compiler-runtime': frontend.resolve('react/compiler-runtime'),
    'react-dom/client': frontend.resolve('react-dom/client') } });
const bundle = built.outputFiles[0].contents, inputs = [];
for (const name of Object.keys(built.metafile.inputs)) { const p = path.resolve(app,name), b = await readFile(p);
  inputs.push({ path: path.relative(app,p), bytes: b.length, sha256: sha(b) }); }
const record = { sourceHead: execFileSync('git',['rev-parse','HEAD'],{cwd:app,encoding:'utf8'}).trim(),
  scope: 'Real React/compiler/DOM, synthetic player/image/navigation/provider ports; no app mount or media/provider compatibility.',
  runtime: { node: process.version, esbuild: esbuild.version, react: frontend('react/package.json').version,
    playwright: frontend('@playwright/test/package.json').version },
  controller: { path: 'reconstruction/live-preview-flow/browser.mjs', sha256: sha(await readFile(fileURLToPath(import.meta.url))) },
  sourceProofSha256: sha(await readFile(path.join(app,'reconstruction/live-preview-flow/PROVENANCE.json'))),
  inputs, bundleSha256:sha(bundle), fromCase:from, unexecutedCases:[], cases:[], errors:[], blockedRequests:[], serverRequests:[] };
await writeFile(path.join(output,'INPUTS.json'),JSON.stringify(record,null,2)+'\n');
const server = http.createServer((request,response) => {
  record.serverRequests.push({method:request.method,path:request.url}); response.setHeader('Cache-Control','no-store');
  if(request.method!=='GET'){response.writeHead(405);response.end();return;}
  if(request.url==='/bundle.js'){response.setHeader('Content-Type','text/javascript');response.end(bundle);return;}
  if(request.url==='/'){response.setHeader('Content-Type','text/html');response.end('<!doctype html><meta charset="utf-8"><title>Synthetic outer-preview proof</title><style>#root{width:1000px}.snap-x{display:flex;gap:16px;overflow:auto;padding:0!important}[data-testid="live-hero-slot"]{flex:0 0 280px;width:280px}button,a{position:static!important}button{margin:3px}</style><div id="root"></div><script src="/bundle.js"></script>');return;}
  response.writeHead(404);response.end();
});
let browser,context,page;
async function observe(){return page.evaluate(()=>window.harness.observe());}
let ordinal=0;
async function run(name,fn){if(++ordinal<from){record.unexecutedCases.push({ordinal,name,reason:'explicit continuation; prior outcome remains in its original receipt'});return;}
  const item={ordinal,name,before:await observe()};record.cases.push(item);try{await fn(item);item.status='PASS';item.after=await observe();}
  catch(e){item.status='FAIL';item.error=String(e.stack??e);item.after=await observe().catch(()=>null);await page.screenshot({path:path.join(output,`failure-${record.cases.length}.png`)}).catch(()=>{});throw e;}}
async function selected(index){await page.locator('[data-testid="live-hero-slot"]').nth(index).waitFor();
  await page.waitForFunction((i)=>document.querySelectorAll('[data-testid="live-hero-slot"]')[i]?.dataset.selected==='true',index);}
try {
  server.listen(0,'127.0.0.1');await once(server,'listening');record.origin=`http://127.0.0.1:${server.address().port}`;
  browser=await chromium.launch({headless:true});context=await browser.newContext({viewport:{width:1000,height:900}});
  await context.route('**/*',(route)=>{if(new URL(route.request().url()).origin!==record.origin){record.blockedRequests.push(route.request().url());return route.abort();}return route.continue();});
  await context.tracing.start({screenshots:true,snapshots:true,sources:true});page=await context.newPage();
  page.on('pageerror',(e)=>record.errors.push(String(e.stack??e)));await page.goto(record.origin);
  await page.waitForFunction(()=>window.harness?.observe().mounted===1);
  if(from===3){await page.getByRole('button',{name:'Slide 2 of 3',exact:true}).click();await selected(1);
    await page.waitForFunction(()=>window.harness.observe().players[0]?.mint==='fixture-B');}
  await run('selected-only media activation, original lazy metadata and disabled provider flags',async()=>{
    await selected(0);let o=await observe();assert.deepEqual(o.players,[{mint:'fixture-A',playlistUrl:'fixture-playlist-A',muted:true,isLoading:true,playOnHover:false,playWhenVisible:false,loaderType:'progress-bar'}]);
    assert.ok(o.events.some(e=>e[0]==='loader-port'&&e[1]===47367));
    assert.ok(o.events.some(e=>e[0]==='dynamic-options'&&e[1].ssr===false&&e[1].loadableGenerated.modules[0]===971491));
    const flags=o.events.find(e=>e[0]==='provider-flags')[2];assert.deepEqual(flags,{shouldGetLivestreamData:false,shouldGetCoinInfo:false,isModeratorCheckEnabled:false,shouldJoinChatRoom:true});
  });
  await run('ready callback clears outer loading; inactive click captures before child callback/navigation',async()=>{
    await page.getByRole('button',{name:'Synthetic ready',exact:true}).click();await page.waitForFunction(()=>window.harness.observe().players[0].isLoading===false);
    await page.evaluate(()=>window.harness.clear());await page.locator('[data-testid="live-hero-slot"]').nth(1).getByRole('button',{name:'Synthetic image Fixture B'}).click();
    await selected(1);await page.waitForFunction(()=>window.harness.observe().players[0]?.mint==='fixture-B');
    const o=await observe();assert.equal(o.mounted,1);assert.equal(o.players[0].isLoading,true);assert.ok(!o.events.some(e=>e[0]==='link'||e[0]==='analytics-port'));
  });
  await run('shared HeroSlide mute and outer autoplay-failure gesture recovery',async()=>{
    await page.getByTestId('icon-muted').locator('..').click();await page.waitForFunction(()=>window.harness.observe().players[0].muted===false);
    await page.evaluate(()=>window.harness.autoplayFailure());await page.getByTestId('icon-unmuted').waitFor({state:'detached'});
    assert.equal((await observe()).players[0].muted,false);await page.keyboard.press('Shift');await page.getByTestId('icon-unmuted').waitFor();
  });
  await run('thumbnail error/load state and inactive selection retain keyed slide state',async()=>{
    const image=page.getByRole('button',{name:'Synthetic image Fixture B',exact:true});assert.match(await image.getAttribute('data-image-class'),/opacity-0/);
    await page.evaluate(()=>window.harness.imageError('Fixture B'));await page.waitForFunction(()=>[...document.querySelectorAll('[data-testid="synthetic-image"]')].find(e=>e.textContent==='Synthetic image Fixture B').dataset.imageClass.includes('opacity-100'));
    assert.equal(await image.getAttribute('data-src'),'fixture-updated-B');await page.getByRole('button',{name:'Slide 1 of 3',exact:true}).click();await selected(0);
    await page.getByRole('button',{name:'Slide 2 of 3',exact:true}).click();await selected(1);assert.match(await image.getAttribute('data-image-class'),/opacity-100/);
    assert.equal((await observe()).players[0].muted,false);
  });
  await run('looping arrows and count-shrink clamp retain actual scroll callback outputs',async()=>{
    await page.evaluate(()=>{document.getElementById('root').style.width='320px';});
    await page.getByRole('button',{name:'Slide 1 of 3',exact:true}).click();await selected(0);await page.evaluate(()=>window.harness.clear());
    await page.getByRole('button',{name:'web.pagination.go_to_previous_page',exact:true}).click();await selected(2);
    assert.ok((await observe()).events.some(e=>e[0]==='scrollTo'&&e[1].behavior==='instant'&&e[1].left>0));
    await page.getByRole('button',{name:'web.pagination.go_to_next_page',exact:true}).click();await selected(0);
    await page.getByRole('button',{name:'Slide 3 of 3',exact:true}).click();await selected(2);await page.evaluate(()=>window.harness.replace(['A']));await selected(0);
    await page.getByRole('button',{name:'Slide 1 of 1',exact:true}).waitFor({state:'detached'});assert.equal((await observe()).players[0].mint,'fixture-A');
    await page.evaluate(()=>window.harness.replace([]));await page.getByTestId('synthetic-player').waitFor({state:'detached'});
  });
  await run('actual trailing stream spread can override child selection; unmount releases the synthetic player',async()=>{
    await page.evaluate(()=>window.harness.override());await page.waitForFunction(()=>window.harness.observe().mounted===2);
    assert.equal(await page.locator('[data-testid="live-hero-slot"][data-selected="true"]').count(),1);
    await page.evaluate(()=>window.harness.unmount());await page.waitForFunction(()=>window.harness.observe().mounted===0);
  });
  assert.deepEqual(record.errors,[]);assert.deepEqual(record.blockedRequests,[]);
} finally {
  if(context)await context.tracing.stop({path:path.join(output,'trace.zip')}).catch(()=>{});
  if(browser)await browser.close();if(server.listening){server.close();server.closeAllConnections();await once(server,'close');}
  record.cleanup={browserClosed:!browser||!browser.isConnected(),serverStopped:!server.listening};
  await writeFile(path.join(output,'RESULT.json'),JSON.stringify(record,null,2)+'\n');
}
console.log(JSON.stringify({cases:record.cases.length,passed:record.cases.filter(c=>c.status==='PASS').length,errors:record.errors.length,output}));
