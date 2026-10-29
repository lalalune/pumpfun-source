import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { createServer } from 'node:http';
import { once } from 'node:events';
import { mkdtemp,readFile,writeFile,mkdir,rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { avatarAssets,FALLBACK_IMAGE } from '../reconstruction/avatar-workflow/client.mjs';
const app=fileURLToPath(new URL('..',import.meta.url));
const frontend=createRequire(new URL('../packages/frontend/package.json',import.meta.url));
const backend=createRequire(new URL('../packages/backend/package.json',import.meta.url));
const {chromium}=frontend('@playwright/test'),{build}=createRequire(backend.resolve('tsx'))('esbuild');
const sha256=b=>createHash('sha256').update(b).digest('hex');
test('complete Avatar source owners: native supplied-image failure/reset and deterministic layer handoff at two widths',{timeout:60000},async()=>{
 const output=process.env.PUMP_AVATAR_OUTPUT,temp=await mkdtemp(path.join(os.tmpdir(),'source-avatar-'));
 const packet={scope:'Generated complete Avatar owners with real React/compiler/native data-image events; remote images blocked. No product/CDN/visual/provider/identity parity.',requests:[],blocked:[],console:[],errors:[],observations:[]};
 let server,browser,currentPage;
 try{
  const built=await build({absWorkingDir:app,entryPoints:[path.join(app,'tests/fixtures/avatar-workflow.mjs')],bundle:true,platform:'browser',format:'esm',outfile:path.join(temp,'fixture.js'),define:{'process.env.NODE_ENV':'"development"'},logLevel:'silent',metafile:true});
  const bundle=await readFile(path.join(temp,'fixture.js'));packet.bundleSha256=sha256(bundle);packet.bundledInputs=[];
  for(const name of Object.keys(built.metafile.inputs).sort()){const b=await readFile(path.resolve(app,name));packet.bundledInputs.push({path:name,bytes:b.length,sha256:sha256(b)});}
  packet.inputs=[];for(const name of ['reconstruction/avatar-workflow/client.mjs','reconstruction/avatar-workflow/verify.mjs','reconstruction/avatar-workflow/PROVENANCE.json','tests/avatar_workflow.test.mjs','tests/avatar_workflow.browser.mjs','tests/fixtures/avatar-workflow.mjs','pnpm-lock.yaml']){const b=await readFile(path.join(app,name));packet.inputs.push({path:name,bytes:b.length,sha256:sha256(b)});}
  packet.versions={node:process.version,react:frontend('react/package.json').version,reactDom:frontend('react-dom/package.json').version,esbuild:createRequire(backend.resolve('tsx'))('esbuild').version};
  server=createServer((req,res)=>{
   packet.requests.push({method:req.method,path:req.url});if(req.method!=='GET'){res.writeHead(405).end();return;}
   res.setHeader('Content-Security-Policy',"default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'");
   if(req.url==='/fixture.js'){res.setHeader('Content-Type','text/javascript');res.end(bundle);}
   else if(req.url==='/'){res.setHeader('Content-Type','text/html');res.end('<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Authored Avatar source host</title><style>body{font:16px system-ui;margin:16px}#root>div{position:relative;width:36px;height:36px;overflow:hidden}#root>div>div{position:absolute;inset:0}#root>div>div>img{position:absolute;inset:0;width:100%;height:100%}</style><h1>Source Avatar host; remote assets blocked</h1><div id="root"></div><script type="module" src="/fixture.js"></script></html>');}
   else res.writeHead(404).end();
  });server.listen(0,'127.0.0.1');await once(server,'listening');const base='http://127.0.0.1:'+server.address().port;
  browser=await chromium.launch({headless:true,executablePath:process.env.PUMP_BROWSER_EXECUTABLE??chromium.executablePath()});packet.versions.chromium=browser.version();
  for(const width of [390,1280]){
   const context=await browser.newContext({viewport:{width,height:844}}),page=await context.newPage();currentPage=page;packet.phase={width,stage:'initial-data-image'};
   page.on('pageerror',e=>packet.errors.push({width,message:e.message}));page.on('console',e=>packet.console.push({width,type:e.type(),text:e.text()}));
   await page.route('**/*',r=>{const q=r.request();if(new URL(q.url()).origin!==base||q.method()!=='GET'){packet.blocked.push({width,method:q.method(),url:q.url()});return r.abort();}return r.continue();});
   const state=()=>page.evaluate(()=>window.avatarHarness.state());
   await page.goto(base);await page.waitForFunction(()=>window.avatarHarness?.state().ready);
   const img=page.getByTestId('source-avatar');await img.evaluate(i=>i.decode());
   assert.deepEqual(await img.evaluate(i=>[i.naturalWidth,i.naturalHeight]),[40,20]);assert.equal(await img.getAttribute('alt'),'Synthetic reply avatar');
   await img.evaluate(i=>{window.initialAvatarNode=i;});
   packet.phase={width,stage:'native-invalid-data-then-blocked-fallback'};
   await page.evaluate(()=>window.avatarHarness.props({src:window.avatarHarness.images.invalid}));
   await page.waitForFunction(f=>{const s=window.avatarHarness.state();return s.errors.length===2&&s.images[0]?.src===f;},FALLBACK_IMAGE);
   const failed=await state();assert.ok(failed.sourceEvents.findIndex(e=>e.type==='source-effect'&&e.deps[0]==='data:image/png;base64,broken')<failed.sourceEvents.findIndex(e=>e.type==='native-error'),'host flushSync commits source reset before native error');assert.equal(failed.errors[0].src,'data:image/png;base64,broken');assert.equal(failed.errors[1].src,FALLBACK_IMAGE);
   assert.ok(failed.violations.some(v=>v.directive==='img-src'&&v.blockedURI===FALLBACK_IMAGE));
   assert.equal(await img.evaluate(i=>i===window.initialAvatarNode),true);
   const commits=failed.commits;await page.evaluate(()=>window.avatarHarness.props({className:'changed-only'}));
   await page.waitForFunction(n=>window.avatarHarness.state().commits>n,commits);assert.equal(await img.getAttribute('src'),FALLBACK_IMAGE);assert.equal((await state()).errors.length,2);
   packet.phase={width,stage:'new-derived-source-resets-real-error-state'};
   await page.evaluate(()=>window.avatarHarness.props({src:window.avatarHarness.images.b}));
   await page.waitForFunction(()=>document.querySelector('#root img')?.getAttribute('src')===window.avatarHarness.images.b);await img.evaluate(i=>i.decode());
   assert.deepEqual(await img.evaluate(i=>[i.naturalWidth,i.naturalHeight]),[20,10]);assert.equal((await state()).errors.length,2);
   packet.phase={width,stage:'generated-branch-and-ref'};
   await page.evaluate(()=>window.avatarHarness.props({src:undefined,style:{width:36,height:36},forwardRef:window.avatarHarness.forwardRef}));
   await page.waitForFunction(()=>window.avatarHarness.state().images.length===7);
   const generated=await state();assert.deepEqual(generated.images.map(i=>i.src),avatarAssets.sizeLayers(avatarAssets.generate('synthetic-address-A'),36,36));assert.equal(generated.forwardedTag,'DIV');
   assert.equal(await page.locator('#root>div>div').evaluate(e=>e.style.transform),'scale(1.6) translate(1%, 18%)');
   packet.phase={width,stage:'anonymous-dispatch-and-unmount'};
   await page.evaluate(()=>window.avatarHarness.props({isAnonymous:true,src:window.avatarHarness.images.a,forwardRef:undefined}));await page.waitForFunction(()=>window.avatarHarness.state().images.length===1);
   await img.evaluate(i=>i.decode());assert.equal((await state()).forwardedTag,null);
   const final=await state();await page.evaluate(()=>window.avatarHarness.unmount());assert.equal((await state()).childCount,0);
   packet.observations.push({width,failed,generated,final,sourceLimit:'Native data-image success/error/reset and blocked remote attribute construction only; no CDN fallback/layer pixels or product mount.'});
   await context.close();currentPage=undefined;
  }
  assert.deepEqual(packet.errors,[]);assert.ok(packet.requests.every(r=>r.method==='GET'&&['/','/fixture.js'].includes(r.path)));
  assert.deepEqual(packet.blocked,[],'CSP must prevent remote image acquisition before routing');
  packet.result='PASS';
 }catch(e){packet.result='FAIL';packet.failure={name:e.name,message:e.message};if(currentPage&&!currentPage.isClosed())try{packet.lastState=await currentPage.evaluate(()=>window.avatarHarness?.state());}catch(d){packet.diagnosticError=d.message;}throw e;}
 finally{await browser?.close();if(server){server.closeAllConnections();await new Promise(r=>server.close(r));}packet.cleanup={browserClosed:!browser?.isConnected(),serverListening:server?.listening??false};
  if(output){await mkdir(output,{recursive:true});await writeFile(path.join(output,'observations.json'),JSON.stringify(packet,null,2)+'\n');}await rm(temp,{recursive:true,force:true});}
});
