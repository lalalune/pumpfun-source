// Finite real-React/DOM host; infrastructure approach credits1879/1846.
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFile,writeFile,mkdir,stat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import http from 'node:http';
import {once} from 'node:events';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
const app=fileURLToPath(new URL('../..',import.meta.url));
assert.equal(process.argv.length,4,'usage: browser.mjs --output NEW_DIRECTORY');assert.equal(process.argv[2],'--output');
const output=path.resolve(process.argv[3]);await assert.rejects(stat(output),{code:'ENOENT'});await mkdir(output,{recursive:true});
const frontend=createRequire(path.join(app,'packages/frontend/package.json')),backend=createRequire(path.join(app,'packages/backend/package.json'));
const esbuild=createRequire(backend.resolve('tsx'))('esbuild'),{chromium}=frontend('@playwright/test'),sha=b=>createHash('sha256').update(b).digest('hex');
const built=await esbuild.build({entryPoints:[fileURLToPath(new URL('./fixture.mjs',import.meta.url))],absWorkingDir:app,bundle:true,write:false,platform:'browser',format:'iife',metafile:true,
  define:{'process.env.NODE_ENV':'"development"'},alias:{react:frontend.resolve('react'),'react/jsx-runtime':frontend.resolve('react/jsx-runtime'),
    'react/compiler-runtime':frontend.resolve('react/compiler-runtime'),'react-dom/client':frontend.resolve('react-dom/client')}});
const bundle=built.outputFiles[0].contents,inputs=[];
for(const name of Object.keys(built.metafile.inputs)){const p=path.resolve(app,name),b=await readFile(p);inputs.push({path:path.relative(app,p),bytes:b.length,sha256:sha(b)});}
const record={sourceHead:execFileSync('git',['rev-parse','HEAD'],{cwd:app,encoding:'utf8'}).trim(),scope:'Real React/compiler and native IntersectionObserver delegated by an instrumented DOM port; synthetic query/read/geo/render ports, not application/provider behavior.',
  runtime:{node:process.version,react:frontend('react/package.json').version,esbuild:esbuild.version,playwright:frontend('@playwright/test/package.json').version},
  controller:{path:'reconstruction/live-read-state/browser.mjs',sha256:sha(await readFile(fileURLToPath(import.meta.url)))},
  proofSha256:sha(await readFile(path.join(app,'reconstruction/live-read-state/PROVENANCE.json'))),inputs,bundleSha256:sha(bundle),observations:[],pageErrors:[],unexpected:[],requests:[]};
await writeFile(path.join(output,'INPUTS.json'),JSON.stringify(record,null,2)+'\n');
const server=http.createServer((req,res)=>{record.requests.push({method:req.method,path:req.url});res.setHeader('Cache-Control','no-store');
  if(req.method!=='GET'){res.writeHead(405);res.end();return;}if(req.url==='/bundle.js'){res.setHeader('Content-Type','text/javascript');res.end(bundle);return;}
  if(req.url==='/'){res.setHeader('Content-Type','text/html');res.end('<!doctype html><meta charset="utf-8"><title>Synthetic Live read-state</title><style>body{margin:0}#root{max-width:700px}</style><div id="root"></div><script src="/bundle.js"></script>');return;}res.writeHead(404);res.end();});
let browser,context,page;
const observe=()=>page.evaluate(()=>window.harness.observe());
async function save(name){record.observations.push({name,state:await observe()});}
async function update(name){const before=(await observe()).commits;await page.evaluate(n=>window.harness[n](),name);await page.waitForFunction(n=>window.harness.observe().commits>n,before);}
try{
  server.listen(0,'127.0.0.1');await once(server,'listening');record.origin=`http://127.0.0.1:${server.address().port}`;
  browser=await chromium.launch({headless:true});context=await browser.newContext({viewport:{width:1000,height:700}});
  await context.route('**/*',route=>{if(new URL(route.request().url()).origin!==record.origin||route.request().method()!=='GET'){record.unexpected.push(route.request().url());return route.abort();}return route.continue();});
  await context.tracing.start({screenshots:true,snapshots:true,sources:true});page=await context.newPage();page.on('pageerror',e=>record.pageErrors.push(String(e.stack??e)));
  await page.goto(record.origin);await page.waitForFunction(()=>window.harness?.observe().commits>0);
  let s=await observe();assert.ok(s.events.some(e=>e.type==='section-query'&&e.sort==='most_viewers'));assert.ok(!s.events.some(e=>e.type==='section-query'&&e.sort==='market_cap'||e.type==='clips-port'));assert.equal(s.activeObservers,0);await save('initial loading keeps only first section unlocked; eager first section has no observer');
  await update('settleMostEmpty');await page.waitForFunction(()=>window.harness.observe().events.some(e=>e.type==='section-query'&&e.sort==='market_cap'));
  assert.deepEqual((await observe()).rowIds,[]);await save('not-loading empty first section still completes and unlocks second');
  await update('settleTwo');await page.waitForFunction(()=>window.harness.observe().activeObservers===1);
  s=await observe();assert.deepEqual(s.rowIds,['most-row','cap-row']);assert.ok(!s.events.some(e=>e.type==='clips-port'));
  assert.deepEqual(await page.locator('[data-testid="synthetic-rows"]').evaluateAll(nodes=>nodes.map(n=>n.dataset.eager)),['true','true']);await save('first two eager rows complete; third requires native intersection admission');
  await update('changePrefix');s=await observe();assert.equal(s.latest.sameHeroKey,true);assert.equal(s.latest.sameHeroFn,false);assert.equal(s.latest.sameSectionOptions,false);
  assert.deepEqual(s.latest.heroKey,['live-hero-coins',false]);assert.equal(s.latest.sectionKey.at(-1),'prefix-two');await save('IPFS change preserves hero key but changes function; section key/options include prefix');
  await update('errorOnly');s=await observe();assert.equal(s.latest.sameSectionResult,true);assert.ok(!s.latest.sectionKeys.includes('error')&&!s.latest.sectionKeys.includes('isError'));await save('query error-only changes preserve section result identity and do not invent an error field');
  assert.equal(await page.evaluate(()=>typeof window.harness.nearEnd()),'undefined');let count=(await observe()).events.filter(e=>e.type==='next-page').length;assert.equal(count,1);
  await update('setFetching');assert.equal(await page.evaluate(()=>typeof window.harness.nearEnd()),'undefined');assert.equal((await observe()).events.filter(e=>e.type==='next-page').length,count);await save('actual near-end handoff does not await and blocks concurrent next-page calls');
  await page.evaluate(()=>window.harness.scrollAdmission());await page.waitForFunction(()=>window.harness.observe().events.some(e=>e.type==='clips-port'&&e.sectionId==='trending-clips'));
  s=await observe();assert.ok(s.events.filter(e=>e.type==='observer-create').every(e=>e.options.rootMargin==='150px'));assert.ok(s.events.some(e=>e.type==='intersection'&&e.intersecting.some(Boolean)));await save('native IntersectionObserver150px margin admits the third section');
  count=s.events.filter(e=>e.type==='observer-create').length;await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));
  await page.waitForFunction(()=>window.harness.observe().activeObservers===0);assert.equal((await observe()).events.filter(e=>e.type==='observer-create').length,count);await save('leaving viewport does not revoke persistent seen admission');
  await update('settleClips');await page.waitForFunction(()=>window.harness.observe().activeObservers===1);s=await observe();assert.ok(s.rowIds.includes('clip-row'));assert.ok(!s.events.some(e=>e.type==='clips-port'&&e.sectionId==='popular-recordings'));await save('completed clips unlock the next offscreen section without running its provider');
  await update('blocked');await page.getByTestId('synthetic-blocked').waitFor();await page.waitForFunction(()=>window.harness.observe().activeObservers===0);
  await page.evaluate(()=>window.harness.unmount());s=await observe();assert.equal(s.activeObservers,0);assert.equal(s.subscriptions,0);assert.equal(await page.locator('#root').textContent(),'');await save('geo snapshot branch unmounts sections; actual cleanup disconnects observers and subscriptions');
  assert.deepEqual(record.pageErrors,[]);assert.deepEqual(record.unexpected,[]);record.result='PASS';
}catch(error){record.result='FAIL';record.error=String(error.stack??error);if(page){record.last=await observe().catch(()=>null);await page.screenshot({path:path.join(output,'failure.png')}).catch(()=>{});}throw error;
}finally{
  if(context)await context.tracing.stop({path:path.join(output,'trace.zip')}).catch(()=>{});if(browser)await browser.close();
  if(server.listening){server.close();server.closeAllConnections();await once(server,'close');}
  record.cleanup={browserClosed:!browser||!browser.isConnected(),serverStopped:!server.listening};await writeFile(path.join(output,'RESULT.json'),JSON.stringify(record,null,2)+'\n');
}
console.log(JSON.stringify({result:record.result,observations:record.observations.length,pageErrors:record.pageErrors.length,output}));
