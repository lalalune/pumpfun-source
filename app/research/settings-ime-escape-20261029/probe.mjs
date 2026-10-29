import { createRequire } from 'node:module';
import { writeFile,readFile,mkdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
const root='/workspace/pump-app-privacy-links';
const require=createRequire(root+'/app/packages/frontend/package.json');
const {chromium,expect}=require('@playwright/test');
const origin=new URL(process.argv[2]).origin;
if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(origin))throw Error('Loopback only');
const source=root+'/app/packages/frontend/src/components/settings/settings-control.tsx';
const sha256=p=>readFile(p).then(x=>createHash('sha256').update(x).digest('hex'));
const beforeSource=await sha256(source);
const browser=await chromium.launch({headless:true});
try {
 const context=await browser.newContext({viewport:{width:390,height:844},storageState:{cookies:[{name:'clickwrap_accepted',value:'true',domain:'127.0.0.1',path:'/',expires:-1,httpOnly:false,secure:false,sameSite:'Lax'}],origins:[]}});
 const page=await context.newPage();const requests=[],errors=[];
 await page.route('https://**/*',r=>r.abort());
 page.on('request',r=>requests.push({method:r.method(),url:r.url()}));
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto(origin+'/?settings=notifications');
 const dialog=page.getByRole('dialog',{name:'Settings',exact:true});
 const search=dialog.getByRole('searchbox',{name:'Search settings'});
 await search.fill('follow');
 await expect(dialog.getByRole('button',{name:'Clear settings search'})).toBeVisible();
 await page.evaluate(()=>{
  window.imeTrace=[];
  for(const name of ['compositionstart','compositionupdate','compositionend','keydown','keyup','cancel','input'])document.addEventListener(name,e=>{
   window.imeTrace.push({event:name,key:e.key??null,isComposing:e.isComposing??null,isTrusted:e.isTrusted,data:e.data??null,defaultPrevented:e.defaultPrevented,value:e.target?.value??null,url:location.href,dialogOpen:!!document.querySelector('dialog[open]')});
  },true);
 });
 const cdp=await context.newCDPSession(page);
 await cdp.send('Input.imeSetComposition',{text:'にほん',selectionStart:3,selectionEnd:3});
 const read=()=>page.evaluate(()=>({url:location.href,dialogOpen:!!document.querySelector('dialog[open]'),active:document.activeElement?.outerHTML,trace:window.imeTrace}));
 const before=await read();
 await page.keyboard.press('Escape');
 await page.waitForLoadState('networkidle',{timeout:10000});
 const after=await read();
 const nativePage=await context.newPage();
 await nativePage.setContent('<!doctype html><dialog><label>Search<input type="search"></label></dialog>');
 await nativePage.evaluate(()=>{
  window.imeTrace=[];document.querySelector('dialog').showModal();
  for(const name of ['compositionstart','compositionupdate','compositionend','keydown','keyup','cancel','input'])document.addEventListener(name,e=>window.imeTrace.push({event:name,key:e.key??null,isComposing:e.isComposing??null,isTrusted:e.isTrusted,defaultPrevented:e.defaultPrevented,dialogOpen:!!document.querySelector('dialog[open]')}),true);
 });
 await nativePage.locator('input').fill('follow');
 const nativeCdp=await context.newCDPSession(nativePage);
 await nativeCdp.send('Input.imeSetComposition',{text:'にほん',selectionStart:3,selectionEnd:3});
 const nativeBefore=await nativePage.evaluate(()=>({dialogOpen:!!document.querySelector('dialog[open]'),trace:window.imeTrace}));
 await nativePage.keyboard.press('Escape');
 await nativePage.waitForLoadState('networkidle',{timeout:10000});
 const nativeAfter=await nativePage.evaluate(()=>({dialogOpen:!!document.querySelector('dialog[open]'),trace:window.imeTrace}));
 const folder=root+'/work/settings-ime-baseline';await mkdir(folder,{recursive:true});
 await page.screenshot({path:folder+'/after.png'});
 const proof={classification:'Observational Chromium CDP IME input; no OS/native-IME or other-browser equivalence claim',head:execFileSync('git',['rev-parse','HEAD'],{cwd:root,env:{...process.env,GIT_NO_LAZY_FETCH:'1'},encoding:'utf8'}).trim(),sourceSha256:beforeSource,sourceUnchanged:beforeSource===await sha256(source),browser:browser.version(),before,after,nativeControl:{before:nativeBefore,after:nativeAfter},requests,errors};
 await writeFile(folder+'/observed.json',JSON.stringify(proof,null,2)+'\n');
 console.log(JSON.stringify(proof,null,2));
} finally {await browser.close();}
