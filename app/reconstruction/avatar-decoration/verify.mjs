import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import prettier from 'prettier';
import {openCorpus,findNodes,exactlyOne,member,sha256} from '../../scripts/original-contracts/source.mjs';
export const APP_ROOT=fileURLToPath(new URL('../..',import.meta.url));
export const DIRECTORY='reconstruction/avatar-decoration';
const PINS={953283:'943e73d5053096c91c183d0a9126f41c0bd690889aebc0d2a1847254b1a1dc68',983737:'991bf1b40d439e6e6ce5152006cb1740bf0d57408235653544561dae07e6256a',538463:'eb34effe1040563c1a05943a22f8f036cdda237f4bb9631a8fe144d7699ba39a',322315:'5d08c12f771cccf43ebfa2740e4a0fbf8c67c9df5a781e8cd2c1183997178f26',254010:'68c2bf6f4fa12591ba132bd96e6e09f9d5cdb13093bde04cd29ef0d6ec0182dd',204478:'27cc0223b79ff95cac02f490600cc4de894dee66af739beca525502c424dae3f'};
const decls=f=>f.node.body.body.flatMap(n=>n.type==='VariableDeclaration'?n.declarations:[]);
const decl=(f,name)=>exactlyOne(decls(f).filter(n=>n.id.name===name),'actual top binding '+name);
function exp(f,id,key){const call=exactlyOne(findNodes(f.node,n=>n.type==='CallExpression'&&member(n.callee,f.runtime,'s')&&(id===null||n.arguments[1]?.value===id)&&n.arguments[0]?.type==='ArrayExpression'&&n.arguments[0].elements.some(x=>x?.value===key)),'qualified export '+id+'.'+key);const a=call.arguments[0].elements,at=a.findIndex(n=>n?.value===key);assert.equal(a[at+1].value,0);return{call,node:a[at+2]};}
function imported(f,name,id,method='i'){const d=decl(f,name);assert.ok(member(d.init?.callee,f.runtime,method));assert.equal(d.init.arguments[0]?.value,id);return d;}
export async function recover(root=APP_ROOT){
 const corpus=await openCorpus(root),fs={};for(const [key,hash]of Object.entries(PINS)){const id=Number(key),rows=corpus.index.modules.filter(m=>m.ids.includes(id));assert.equal(rows.length,1,'all physical variants '+id);assert.equal(rows[0].sha256,hash);assert.equal(rows[0].origins.length,1);fs[id]=await corpus.factory(id,{source:rows[0].origins[0].source});}
 const f=fs[953283],motion=fs[983737],init=fs[538463],caller=fs[204478],witnesses=[];
 const w=(factory,node,label)=>{const v=factory.witness(node,label);witnesses.push(v);return v;};
 for(const [alias,id]of Object.entries({t:732486,i:445242,r:426091,n:983737,a:352386,O:322315,y:254010}))w(f,imported(f,alias,id),'actual decoration provider '+id);
 const frame=exp(f,953283,'f'),artExport=exp(f,48623,'f'),art=exactlyOne(f.node.body.body.filter(n=>n.type==='FunctionDeclaration'&&n.id.name===artExport.node.name),'complete artwork owner'),keyHook=exp(f,279602,'f');
 for(const [node,slots,label]of [[frame.node,13,'decoration frame'],[art,16,'artwork owner'],[keyHook.node,2,'feature-gated key hook']]){assert.equal(findNodes(node,n=>n.type==='CallExpression'&&n.callee.type==='SequenceExpression'&&member(n.callee.expressions[1],'i','c')&&n.arguments[0]?.value===slots).length,1);w(f,node,'complete '+slots+'-slot '+label);}
 for(const call of [frame.call,artExport.call,keyHook.call])w(f,call,'actual bundled public registration');
 const helpers=['s','l','u','c','d','f','m','h','p','g'].map(n=>decl(f,n));for(const n of helpers)w(f,n,'complete used admission/scale/list-suffix/artwork closure');
 // The actually used normalizer is m; no achievements fetch, rarity election or equip policy is copied.
 assert.equal(exp(f,569083,'i').node.name,'m');w(f,exp(f,569083,'i').call,'actual key admission registration');
 for(const [alias,id]of Object.entries({t:758307,i:538463,r:352386}))w(motion,imported(motion,alias,id),'actual reduced-motion provider '+id);
 const hook=exp(motion,null,'f');w(motion,hook.node,'complete useState reduced-motion snapshot hook');
 const refs=['e','i','s'].map(n=>decl(init,n));for(const n of refs)w(init,n,'complete refs/browser-availability dependency');
 assert.equal(exp(init,758307,'E').node.name,'i');assert.equal(exp(init,758307,'d').node.name,'e');
 const initialize=exp(init,538463,'f');w(init,exp(init,758307,'E').call,'positive shared-ref bundled registration');w(init,initialize.call,'positive initializer registration');w(init,initialize.node,'complete initializer including original listener lifetime');
 const flags=fs[322315],flagSet=exactlyOne(findNodes(flags.node,n=>n.type==='AssignmentExpression'&&member(n.left,'t','WEB_AVATAR_DECORATIONS')),'exact flag assignment');assert.equal(flagSet.right.type,'StringLiteral');assert.equal(flagSet.right.value,'webAvatarDecorations');w(flags,flagSet,'only actual consumed flag value');
 const flagRegistration=exactlyOne(findNodes(flags.node,n=>n.type==='CallExpression'&&member(n.callee,flags.runtime,'s')&&n.arguments[0]?.elements?.some(x=>x?.value==='D')),'flag enum export');w(flags,flagRegistration,'actual D getter export');
 const flagArray=flagRegistration.arguments[0].elements;assert.equal(flagArray[0].value,'D');assert.equal(flagArray[1].body.name,'o');w(flags,decl(flags,'o'),'actual enum binding assignment chain');
 const flagPort=exp(fs[254010],null,'k');w(fs[254010],flagPort.call,'actual useFeatureFlag interface only; provider excluded');
 w(caller,imported(caller,'R',953283),'actual decoration frame dependency');w(caller,imported(caller,'W',279602),'actual resolved-key hook dependency');
 const names=n=>!n?[]:n.type==='Identifier'?[n.name]:n.type==='RestElement'?names(n.argument):n.type==='AssignmentPattern'?names(n.left):n.type==='ObjectPattern'?n.properties.flatMap(p=>names(p.type==='RestElement'?p.argument:p.value)):n.type==='ArrayPattern'?n.elements.flatMap(names):[];
 const unshadowed=(parents,alias)=>{for(const p of parents){if(p===caller.node||p===caller.node.body)continue;if(['FunctionDeclaration','FunctionExpression','ArrowFunctionExpression'].includes(p.type))assert.ok(!p.params.flatMap(names).includes(alias),'provider parameter shadow');if(p.type==='BlockStatement')for(const b of p.body)if(b.type==='VariableDeclaration')assert.ok(!b.declarations.flatMap(d=>names(d.id)).includes(alias),'provider local shadow');}};
 const calls=findNodes(caller.node,(n,parents)=>{if(!(n.type==='CallExpression'&&member(n.arguments[0],'R','f')&&n.arguments[1]?.type==='ObjectExpression'))return false;unshadowed(parents,'R');return true;});
 assert.equal(calls.length,3,'all actual compositor/viewer/callout frame handoffs');for(const n of calls)w(caller,n,'actual frame invocation with full descriptor');
 const keyCalls=findNodes(caller.node,(n,parents)=>{if(!(n.type==='CallExpression'&&n.callee.type==='SequenceExpression'&&member(n.callee.expressions[1],'W','f')))return false;unshadowed(parents,'W');return true;});
 assert.ok(keyCalls.length>0);for(const n of keyCalls)w(caller,n,'actual source key→frame consumer normalization');
 const text=await prettier.format(`
// Complete captured shared refs, initializer and snapshot hook. Construct one shared realm instance.
export function createReducedMotionSnapshot({React,window}){
 if(typeof React?.useState!=='function')throw new TypeError('Explicit React.useState required');
 const shared=(()=>{let ${refs.map(n=>init.text(n)).join(',')};return{E:i,d:e,initialize:${init.text(initialize.node)}};})();
 const t=shared,i={f:shared.initialize},r={useState:React.useState};
 return ${motion.text(hook.node)};
}
export const AVATAR_DECORATIONS_FLAG=${flags.text(flagSet.right)};
// Complete owners with actual JSX/compiler/class/flag/window interfaces; no asset/provider acquisition.
export function createAvatarDecorations({jsx,jsxs,Fragment,useMemoCache,React,classNames,useFeatureFlag,window}){
 for(const[name,value]of Object.entries({jsx,jsxs,useMemoCache,classNames,useFeatureFlag}))if(typeof value!=='function')throw new TypeError('Explicit decoration capability required: '+name);
 for(const name of ['useState','isValidElement','cloneElement'])if(typeof React?.[name]!=='function')throw new TypeError('Explicit decoration React operation required: '+name);
 if(Fragment==null)throw new TypeError('Explicit Fragment required');
 const t={jsx,jsxs,Fragment},i={c:useMemoCache},r={c:classNames},n={f:createReducedMotionSnapshot({React,window})},a={isValidElement:React.isValidElement,cloneElement:React.cloneElement},O={D:{WEB_AVATAR_DECORATIONS:AVATAR_DECORATIONS_FLAG}},y={k:useFeatureFlag};
 let ${helpers.map(n=>f.text(n)).join(',')};
 ${f.text(art)}
 const AvatarDecorationFrame=${f.text(frame.node)};
 const useResolvedDecoration=${f.text(keyHook.node)};
 return{AvatarDecorationFrame,AvatarDecorationImage:L,useResolvedDecoration};
}
`,{parser:'babel'});
 return{text,provenance:{schemaVersion:1,baseCommit:'094a06f18df738d41e77070c1a009e135671ac1a',anchors:corpus.anchors,contexts:Object.values(fs).map(f=>f.provenance),witnesses,moduleSha256:sha256(Buffer.from(text)),
 scope:'Complete13-slot frame/16-slot artwork/2-slot key hook with used admission/scale/list-suffix constants and complete shared native reduced-motion snapshot dependency',
 ports:{React:'Actual JSX/Fragment/compiler/useState/cloneElement/isValidElement/class interfaces; compatible implementation supplied',featureFlag:'Actual254010.k called with actual322315.D.WEB_AVATAR_DECORATIONS literal; configuration/provider/acquisition remains external',window:'Explicit supplied realm only; initializer uses matchMedia/addEventListener exactly and has no source cleanup'},
 credited:{Avatar:'Open1916 and competition1296 Avatar ports remain external; no implementation copied or recounted',contracts:'Accepted profile/follow DTOs document resolved decoration keys; no achievements/equip/backend policy inferred'},
 limits:['Original factories remain inert; only generated editable functions execute','Existing reduced-motion hook instances retain their initial snapshot; shared-ref change is not a state subscription','Listener lifetime is source-global; no component cleanup is invented. Browser realm teardown is separate','No original process/runtime shim execution, provider/auth/config acquisition, artwork/CDN availability/pixels, product/native/API/security/feature qualification']}};
}
export async function verify(root=APP_ROOT){const r=await recover(root);assert.equal(await readFile(path.join(root,DIRECTORY,'client.mjs'),'utf8'),r.text,'decoration editable source differs');assert.equal(await readFile(path.join(root,DIRECTORY,'PROVENANCE.json'),'utf8'),JSON.stringify(r.provenance,null,2)+'\n','decoration provenance differs');return r.provenance;}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){assert.ok(process.argv.length===3&&['--check','--write'].includes(process.argv[2]),'Use --write|--check');if(process.argv[2]==='--write'){const r=await recover();await mkdir(path.join(APP_ROOT,DIRECTORY),{recursive:true});await writeFile(path.join(APP_ROOT,DIRECTORY,'client.mjs'),r.text);await writeFile(path.join(APP_ROOT,DIRECTORY,'PROVENANCE.json'),JSON.stringify(r.provenance,null,2)+'\n');}else await verify();console.log('PASS complete decoration13/16/2-slot workflow +shared reduced-motion snapshot closure and actual consumers');}
