import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {mkdtemp,mkdir,copyFile,readFile,writeFile,rm} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {createAvatarDecorations,createReducedMotionSnapshot,AVATAR_DECORATIONS_FLAG} from '../reconstruction/avatar-decoration/client.mjs';
import {APP_ROOT,DIRECTORY,verify} from '../reconstruction/avatar-decoration/verify.mjs';
const req=createRequire(new URL('../packages/frontend/package.json',import.meta.url));
const React=req('react'),{jsx,jsxs,Fragment}=req('react/jsx-runtime'),{c:useMemoCache}=req('react/compiler-runtime'),{renderToStaticMarkup}=req('react-dom/server');
const classNames=(...x)=>x.filter(Boolean).join(' ');
function host(window,flag=true){const reads=[];const c=createAvatarDecorations({jsx,jsxs,Fragment,useMemoCache,React,classNames,useFeatureFlag:key=>{reads.push(key);return flag;},window});return{...c,reads};}
const html=(C,props)=>renderToStaticMarkup(jsx(C,props));
test('complete source and all actual consumer/provider contexts regenerate',async()=>{const p=await verify();assert.equal(p.contexts.length,6);assert.equal(p.witnesses.filter(w=>w.label==='actual frame invocation with full descriptor').length,3);});
test('feature-gated source key admission preserves none/null/unknown and exact known grammar',()=>{
 for(const enabled of [true,false]){
  const h=host(undefined,enabled);function Key({value}){return jsx('output',{children:JSON.stringify(h.useResolvedDecoration(value))});}
  for(const [value,expected]of [['legendary','legendary'],['epic','epic'],['achievement:followers-1m','achievement:followers-1m'],['achievement:missing',null],['none',null],['',null],[undefined,null],[null,null]])assert.equal(html(Key,{value}),'<output>'+JSON.stringify(enabled?expected:null).replaceAll('"','&quot;')+'</output>');
  assert.ok(h.reads.every(k=>k===AVATAR_DECORATIONS_FLAG));assert.equal(AVATAR_DECORATIONS_FLAG,'webAvatarDecorations');
 }
 assert.throws(()=>{const h=host(undefined);function Key(){h.useResolvedDecoration(7);return null;}html(Key,{});},TypeError);
});
test('null frame clones valid child with rest props; Fragment path drops wrapper-only props',()=>{
 const{AvatarDecorationFrame:F}=host(undefined);
 const child=jsx('button',{'data-child':'yes',className:'child-class',children:'Child'});
 assert.equal(html(F,{decoration:null,className:'frame-class',title:'forwarded',children:child}),'<button data-child="yes" class="child-class" title="forwarded">Child</button>');
 assert.equal(html(F,{decoration:null,title:'ignored',children:'Text'}),'Text');
});
test('complete artwork retains list suffix/aspect, animation/eager/default/accessibility descriptors',()=>{
 const{AvatarDecorationImage:I}=host(undefined);
 const list=html(I,{decoration:'achievement:followers-1m',variant:'list',animated:false,eager:true});
 assert.match(list,/followers-1m-list-still.webp\?v=1/);assert.match(list,/width:144.44444444444443%/);assert.match(list,/loading="eager"/);assert.match(list,/aria-hidden="true"/);assert.match(list,/draggable="false"/);assert.match(list,/decoding="async"/);assert.match(list,/alt=""/);
 const profile=html(I,{decoration:'achievement:followers-1m'});assert.match(profile,/followers-1m.webp\?v=1/);assert.match(profile,/width:207.14285714285717%/);assert.match(profile,/loading="lazy"/);assert.match(profile,/data-animated="true"/);
 const noList=html(I,{decoration:'achievement:trades-100k',variant:'list'});assert.doesNotMatch(noList,/trades-100k-list/);
 assert.match(html(I,{decoration:'legendary',animated:false}),/legendary-still.webp/);
});
test('frame animated override wins over source reduced-motion snapshot and rest precedence remains exact',()=>{
 const listeners=[];const window={matchMedia:query=>({matches:true,addEventListener:(type,fn)=>listeners.push({query,type,fn})})};
 const{AvatarDecorationFrame:F}=host(window);const child=jsx('i',{children:'Host Avatar port'});
 assert.match(html(F,{decoration:'epic',children:child}),/epic-still.webp/);
 const forced=html(F,{decoration:'epic',animated:true,variant:'list','data-testid':'frame-id',title:'outer',className:'custom',children:child});
 assert.match(forced,/epic.webp/);assert.match(forced,/data-testid="frame-id"/);assert.match(forced,/class="relative flex w-fit shrink-0 custom"/);assert.match(forced,/title="outer"/);assert.equal(listeners.length,1);
});
test('shared native initializer runs once; new hook mounts read changed ref; no removal is invented',()=>{
 let calls=0,callback,removes=0;const media={matches:false,addEventListener(type,fn){assert.equal(type,'change');callback=fn;},removeEventListener(){removes++;}};
 const hook=createReducedMotionSnapshot({React,window:{matchMedia(query){calls++;assert.equal(query,'(prefers-reduced-motion)');return media;}}});
 function Read(){return jsx('output',{children:String(hook())});}
 assert.equal(html(Read,{}),'<output>false</output>');media.matches=true;callback();assert.equal(html(Read,{}),'<output>true</output>');assert.equal(calls,1);assert.equal(removes,0);
 const fallback=createReducedMotionSnapshot({React,window:{}});function F(){return jsx('output',{children:String(fallback())});}assert.equal(html(F,{}),'<output>false</output>');
 const server=createReducedMotionSnapshot({React,window:undefined});function S(){return jsx('output',{children:String(server())});}assert.equal(html(S,{}),'<output>null</output>');
});
test('null-decoration still invokes motion snapshot before the source conditional return',()=>{
 let calls=0;const{AvatarDecorationFrame:F}=host({matchMedia:()=>{calls++;return{matches:false,addEventListener(){}};}});html(F,{decoration:null,children:'Unframed'});assert.equal(calls,1);
 assert.throws(()=>createAvatarDecorations({}),/Explicit decoration/);
});
async function fixture(t){const root=await mkdtemp(path.join(os.tmpdir(),'avatar-decoration-'));t.after(()=>rm(root,{recursive:true,force:true}));
 for(const d of ['evidence/web/objects','recovered',DIRECTORY])await mkdir(path.join(root,d),{recursive:true});
 const p=JSON.parse(await readFile(path.join(APP_ROOT,DIRECTORY,'PROVENANCE.json'),'utf8'));
 for(const source of new Set(p.contexts.map(c=>c.source)))await copyFile(path.join(APP_ROOT,source),path.join(root,source));
 for(const name of ['evidence/web/manifest.json','recovered/modules.json',DIRECTORY+'/client.mjs',DIRECTORY+'/PROVENANCE.json'])await copyFile(path.join(APP_ROOT,name),path.join(root,name));return root;}
test('changed nullish animation precedence cannot pass raw derivation',async t=>{
 const root=await fixture(t),file=path.join(root,DIRECTORY,'client.mjs');const original=await readFile(file,'utf8');assert.ok(original.includes('f ?? !O'));await writeFile(file,original.replace('f ?? !O','f || !O'));await assert.rejects(verify(root),/decoration editable source differs/);
});
test('a dropped bundled provider or spoofed source hash cannot be hidden by ID membership',async t=>{
 const root=await fixture(t),file=path.join(root,'recovered/modules.json'),data=JSON.parse(await readFile(file,'utf8'));data.modules.find(m=>m.ids.includes(538463)).sha256='0'.repeat(64);await writeFile(file,JSON.stringify(data));await assert.rejects(verify(root));
});
