import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { mkdtemp, mkdir, readFile, writeFile, copyFile, rm, rename } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { avatarAssets as a, createAvatarWorkflow, FALLBACK_IMAGE } from '../reconstruction/avatar-workflow/client.mjs';
import { verifySession } from '../scripts/verify-search-session.mjs';
import { verify, APP_ROOT, DIRECTORY, canonicalUri } from '../reconstruction/avatar-workflow/verify.mjs';
const require=createRequire(new URL('../packages/frontend/package.json',import.meta.url));
const React=require('react'),{renderToStaticMarkup}=require('react-dom/server'),{jsx}=require('react/jsx-runtime'),{c:useMemoCache}=require('react/compiler-runtime');
const Avatar=createAvatarWorkflow({React,jsx,useMemoCache,classNames:(...xs)=>xs.filter(Boolean).join(' ')});
const render=props=>renderToStaticMarkup(jsx(Avatar,props));

test('complete raw source closure, actual five handoffs and both URI spellings regenerate',async()=>{
 const p=await verify();assert.equal(p.contexts.length,6);assert.equal(p.witnesses.filter(w=>w.label==='actual Avatar invocation with full props descriptor').length,5);
 assert.equal(p.witnesses.filter(w=>w.label.includes('slot ')).length,3);
});
test('both URL providers retain decode errors, query overwrite and exact 1.6 bucket sizing',()=>{
 const uri='https://imagedelivery.net/WL1JOIJiM_NAChp6rtB6Cw/pump-avatar/Bodies/a%20b/600x600?x=one&variant=old#gone';
 assert.deepEqual(a.sizeLayers([uri],36,36),['https://images.pump.fun/pump-avatar/Bodies/a%20b?x=one&variant=64x64']);
 assert.deepEqual(a.sizeLayers([uri]),['https://images.pump.fun/pump-avatar/Bodies/a%20b?x=one&variant=600x600']);
 assert.deepEqual(a.sizeLayers(['https://images.pump.fun/a?x=1'],24,1),['https://images.pump.fun/a?x=1&variant=64x64']);
 assert.deepEqual(a.sizeLayers([uri],601,1),['https://images.pump.fun/pump-avatar/Bodies/a%20b?x=one&variant=600x600']);
 assert.deepEqual(a.sizeLayers(['https://example.invalid/plain','not a URL']),['https://example.invalid/plain','not a URL']);
 assert.throws(()=>a.sizeLayers(['https://imagedelivery.net/WL1JOIJiM_NAChp6rtB6Cw/x/%E0%A4%A']),URIError);
});
test('Pinata sizing preserves exact parseInt, host/path, blob and existing-parameter behavior',()=>{
 const u='https://pump.mypinata.cloud/ipfs/CID';
 assert.equal(a.sizeSource(u,'36px',90),u+'?img-width=36&img-dpr=2&img-onerror=redirect');
 assert.equal(a.sizeSource(u+'?x=1',0,15.5),u+'?x=1&img-width=15.5&img-dpr=2&img-onerror=redirect');
 for(const v of ['https://example.invalid/ipfs/CID','blob:https://pump.mypinata.cloud/ipfs/CID',u+'?img-width=9','https://pump.mypinata.cloud/plain'])assert.equal(a.sizeSource(v,36,36),v);
 assert.equal(a.sizeSource('https://gateway.pinata.cloud/ipfs/CID',NaN,'-2'),'https://gateway.pinata.cloud/ipfs/CID');
});
test('normalization reuses accepted URI semantics while preserving HTTP/blob/data fallbacks',()=>{
 const prefix='https://host.invalid/ipfs/',cid='QmeSzchzEPqCU1jwTnsipwcBAeH7S4bmVvFGfF65iA1BY1';
 assert.equal(a.normalizeSource('https://host.invalid/ipfs/'+cid,prefix),prefix+cid);
 assert.equal(a.normalizeSource('https://ipfs.io/ipfs/'+cid), 'undefined'+cid);
 for(const uri of ['https://example.invalid/plain','blob:synthetic','data:image/svg+xml,synthetic'])assert.equal(a.normalizeSource(uri,prefix),uri);
 assert.equal(a.normalizeSource('ftp://example.invalid/plain',prefix),FALLBACK_IMAGE);
 assert.equal(a.normalizeSource(undefined,prefix),prefix+cid);
 assert.equal(a.normalizeSource(null), 'undefined'+cid);
});
test('deterministic full catalog output and seven-layer order are stable source-derived outputs',()=>{
 const layers=a.generate('synthetic-address-A');
 assert.deepEqual(layers.map(x=>x.split('/').slice(-3,-1).join('/')),['Backgrounds/Pink','Bodies/Body-Emerald','Face-expressions/Face-9','Face-Accessories/Glasses-brown','Head-accessories/Hairstyle-5','Arm-Accessories/Watch','Accessories/Scarf-Green']);
 assert.deepEqual(layers,a.generate('synthetic-address-A'));assert.notDeepEqual(layers,a.generate('synthetic-address-B'));
 assert.equal(a.generate('😀').length,7);assert.equal(a.generate('').length,7);
 assert.throws(()=>a.generate(null),TypeError);
});
test('catalog sorted selection, override skip draws, nullish defaults and string-only outputs remain intact',()=>{
 const keys=['backgrounds','bodies','faceExpressions','faceAccessories','headAccessories','armAccessories','accessories'];
 const empty=Object.fromEntries(keys.map(k=>[k,{}]));assert.deepEqual(a.generate('s',{catalog:empty}),[]);
 const catalog=Object.fromEntries(keys.map(k=>[k,{z:k+'/z',a:k+'/a'}]));
 const reverse=Object.fromEntries(keys.map(k=>[k,{a:k+'/a',z:k+'/z'}]));assert.deepEqual(a.generate('s',{catalog}),a.generate('s',{catalog:reverse}));
 const overrides={background:'a',body:'z',faceExpression:'a',faceAccessory:'',headAccessory:'missing',armAccessory:'z',accessory:'a'};
 assert.deepEqual(a.generate('s',{catalog,overrides}),['backgrounds/a','bodies/z','faceExpressions/a','armAccessories/z','accessories/a']);
 const literal={...catalog,backgrounds:{a:2},bodies:{z:''}};assert.deepEqual(a.generate('s',{catalog:literal,overrides}),['','faceExpressions/a','armAccessories/z','accessories/a']);
 assert.deepEqual(a.generate('s',{catalog,overrides:{background:null}}),a.generate('s',{catalog}));
 // An override suppresses its PRNG draw; subsequent layers differ from a post-hoc replacement.
 assert.notDeepEqual(a.generate('s',{catalog,overrides:{background:''}}),a.generate('s',{catalog}).slice(1));
});
test('actual dispatcher chooses generated only for nonanonymous address with missing/exact fallback source',()=>{
 const generated=render({address:'synthetic-address-A',width:36,height:36,alt:'Synthetic account'});
 assert.equal((generated.match(/<img /g)||[]).length,7);assert.match(generated,/scale\(1.6\) translate\(1%, 18%\)/);assert.match(generated,/variant=64x64/);
 assert.equal((render({address:'s',src:FALLBACK_IMAGE}).match(/<img /g)||[]).length,7);
 assert.equal((render({address:'s',src:''}).match(/<img /g)||[]).length,7);
 for(const props of [{address:'s',isAnonymous:true},{address:''},{address:'s',src:'data:image/png;base64,A'}])assert.equal((render(props).match(/<img /g)||[]).length,1);
});
test('complete supplied-image SSR retains alt default, rest props and authoritative source/class/dimensions',()=>{
 const result=render({src:'data:image/svg+xml,A',width:36,height:40,className:'extra','data-host':'reply',draggable:false});
 assert.match(result,/alt=""/);assert.match(result,/data-host="reply"/);assert.match(result,/width="36"/);assert.match(result,/height="40"/);assert.match(result,/object-cover rounded-full overflow-hidden extra/);assert.match(result,/draggable="false"/);
 assert.match(render({isAnonymous:true,src:'https://example.invalid/a',alt:'Explicit'}),/alt="Explicit"/);
 assert.throws(()=>createAvatarWorkflow({}),/Explicit Avatar/);
});
test('complete layered SSR retains outer style/ref route and per-layer inherited prop precedence',()=>{
 const html=render({address:'s',width:36,height:36,style:{width:36,height:36},alt:'layers',className:'outer','data-host':'layer',loading:'lazy'});
 assert.match(html,/relative overflow-hidden rounded-full outer/);assert.match(html,/style="width:36px;height:36px"/);
 assert.equal((html.match(/data-host="layer"/g)||[]).length,7);assert.equal((html.match(/loading="lazy"/g)||[]).length,7);
 assert.equal((html.match(/alt="layers"/g)||[]).length,7);
});
async function copyFixture(t){
 const root=await mkdtemp(path.join(os.tmpdir(),'avatar-source-'));t.after(()=>rm(root,{recursive:true,force:true}));
 for(const dir of ['evidence/web/objects','recovered',DIRECTORY,'reconstruction/search-session'])await mkdir(path.join(root,dir),{recursive:true});
 const sources=new Set();const gather=v=>{if(!v||typeof v!=='object')return;for(const [k,x]of Object.entries(v)){if(k==='source'&&typeof x==='string'&&x.startsWith('evidence/web/objects/'))sources.add(x);else gather(x);}};
 gather(JSON.parse(await readFile(path.join(APP_ROOT,DIRECTORY,'PROVENANCE.json'),'utf8')));gather(await verifySession(APP_ROOT));
 for(const name of sources)await copyFile(path.join(APP_ROOT,name),path.join(root,name));
 for(const name of ['evidence/web/manifest.json','recovered/modules.json',DIRECTORY+'/client.mjs',DIRECTORY+'/PROVENANCE.json','reconstruction/search-session/session.mjs'])await copyFile(path.join(APP_ROOT,name),path.join(root,name));
 return root;
}
test('a changed image-error guard is rejected by canonical original derivation',async t=>{
 const root=await copyFixture(t),file=path.join(root,DIRECTORY,'client.mjs'),s=await readFile(file,'utf8');
 assert.ok(s.includes('e.currentTarget.src === t.A'));await writeFile(file,s.replace('e.currentTarget.src === t.A','e.currentTarget.src !== t.A'));
 await assert.rejects(verify(root),/Avatar editable source differs/);
});
test('a false factory hash cannot be admitted by numeric inventory membership',async t=>{
 const root=await copyFixture(t),file=path.join(root,'recovered/modules.json'),s=JSON.parse(await readFile(file,'utf8'));
 s.modules.find(m=>m.ids.includes(367498)).sha256='0'.repeat(64);await writeFile(file,JSON.stringify(s));
 await assert.rejects(verify(root),/all physical variants 367498/);
});
test('raw capture tampering fails before extraction and URI correspondence preserves actual operations',async t=>{
 const root=await copyFixture(t),file=path.join(root,'evidence/web/objects/d048caae282716b0.js');
 // Replace only our independent temporary copy, preserving the donor input.
 await writeFile(file+'.new',Buffer.concat([await readFile(file),Buffer.from(' ')]));await rename(file+'.new',file);
 await assert.rejects(verify(root),/capture authentication failed/);
 const node={type:'BinaryExpression',operator:'===',left:{type:'Identifier',name:'r'},right:{type:'NumericLiteral',value:1}};
 assert.notDeepEqual(canonicalUri(node,{r:'t'}),canonicalUri({...node,operator:'!=='} ,{r:'t'}));
 assert.throws(()=>canonicalUri(node,{r:'x',s:'x'}),/bijective/);
});
