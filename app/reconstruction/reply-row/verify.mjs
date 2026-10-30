const PINS={
  "349919": [
    "d9e37561efe6c7dfc134d7ace63aa44c5f74e6c406700bd925e0fb7cd4569bc6"
  ],
  "163807": [
    "828b7d1e93dd4135f930646c9f29729e82209232a020fca54e3e775a20eafe44"
  ],
  "390767": [
    "648d505abb256a21395a359f937f7746348b29815a4d99b7f7dd0e6a9ef23ada",
    "dee84889b3994ca9401e340e546db2cdfe5cdedf866e8d07d90b8fc93e6945d6",
    "c3d3119ca74b30bcd58df0db07ec2879bdfd9bcc8e1998d547aa6c43434852f1"
  ],
  "287129": [
    "75ce27324808ccd2b5cba5c591747c4c99cfdf42bc43ebdf06b5253c54a29ecb"
  ],
  "606178": [
    "7dc15a603fcf3afbf1682d31907959b84fea00cf3093553b80258b6df7fdf255"
  ],
  "204478": [
    "27cc0223b79ff95cac02f490600cc4de894dee66af739beca525502c424dae3f"
  ],
  "710416": [
    "27cc0223b79ff95cac02f490600cc4de894dee66af739beca525502c424dae3f"
  ],
  "386028": [
    "648d505abb256a21395a359f937f7746348b29815a4d99b7f7dd0e6a9ef23ada",
    "dee84889b3994ca9401e340e546db2cdfe5cdedf866e8d07d90b8fc93e6945d6",
    "c3d3119ca74b30bcd58df0db07ec2879bdfd9bcc8e1998d547aa6c43434852f1"
  ],
  "335703": [
    "ac958e6c1ea5ae37647619da80cee73000e79667bdb7e1ac2f0c49a2b43c4c20"
  ],
  "458310": [
    "637fd83c895d24a43cfd4243adbb9daea8b61e6c81df9feb82fb844f1e0cbe43"
  ],
  "398902": [
    "6a277435e4b43e8ed386083bdfce657ee1b257e9dc52a191a8b27ccc70e6f267"
  ],
  "365089": [
    "8957b61a69e89f0148cf9a43ca9bc4089cc0c2c892e476af960d1a02c966f4d1"
  ],
  "741084": [
    "1877fed09a6363588057a816a53c9d14fa46d3a3cb285321349a29a6ce48812a",
    "64085dc31cc9ebbcde019719b8096cfd198d84216b08826b70461fdfa689dc55",
    "9fa49ca7090d955ed1650833d4a5adb620e11fd63ee88437701c50bd419832a2"
  ],
  "860787": [
    "d27771d5ffd2a78b9b5857b8125fc606122c7b40a1e8e377da8cb34681036183"
  ],
  "338319": [
    "5b27b6647671eec79898f430326e92e0e8c08d9fc9e2984c70a664def7ae1cb2"
  ]
};
import assert from'node:assert/strict';import{readFile,writeFile,mkdir}from'node:fs/promises';import path from'node:path';import{fileURLToPath}from'node:url';import{parse}from'@babel/parser';import prettier from'prettier';
import{openCorpus,findNodes,exactlyOne,member,sha256}from'../../scripts/original-contracts/source.mjs';import{normalizeSession}from'../../scripts/verify-search-session.mjs';import{parseFlightRecords}from'../../scripts/settings-client-contract.mjs';import{extractUserReplies}from'../../scripts/original-user-replies.mjs';
export const APP_ROOT=fileURLToPath(new URL('../..',import.meta.url));export const DIRECTORY='reconstruction/reply-row';
const decls=f=>f.node.body.body.flatMap(n=>n.type==='VariableDeclaration'?n.declarations:[]),decl=(f,name)=>exactlyOne(decls(f).filter(n=>n.id.name===name),'top binding '+name);
function exp(f,id,key){const call=exactlyOne(findNodes(f.node,n=>n.type==='CallExpression'&&member(n.callee,f.runtime,'s')&&(n.arguments[1]?.value===id||n.arguments.length===1)&&n.arguments[0]?.type==='ArrayExpression'&&n.arguments[0].elements.some(v=>v?.value===key)),'export '+id+'.'+key);const a=call.arguments[0].elements,at=a.findIndex(n=>n?.value===key),direct=a[at+1]?.value===0;return{call,node:direct?a[at+2]:a[at+1],getter:!direct};}
function value(f,x){let n=x.node;if(x.getter&&n.type==='ArrowFunctionExpression')n=n.body;if(n.type==='Identifier'){const fn=f.node.body.body.filter(x=>x.type==='FunctionDeclaration'&&x.id.name===n.name);return fn.length?exactlyOne(fn,'export function'):decl(f,n.name).init;}return n;}
function imp(f,name,id){const d=decl(f,name);assert.ok(member(d.init?.callee,f.runtime,'i'));assert.equal(d.init.arguments[0]?.value,id);return d;}
export async function recover(root=APP_ROOT){const corpus=await openCorpus(root),fs={},contexts=[],witnesses=[];const w=(f,n,label)=>{const v=f.witness(n,label);witnesses.push(v);return v;};
 for(const[key,hashes]of Object.entries(PINS)){const id=Number(key),rows=corpus.index.modules.filter(m=>m.ids.includes(id));assert.deepEqual(rows.map(m=>m.sha256).sort(),[...hashes].sort(),'all provider variants '+id);fs[id]=[];for(const hash of hashes){const m=exactlyOne(rows.filter(x=>x.sha256===hash),'variant');for(const o of m.origins){const f=await corpus.factory(id,{source:o.source});fs[id].push(f);contexts.push(f.provenance);}}}
 const owner=fs[349919][0],publicFrame=exp(owner,349919,'f'),frame=value(owner,publicFrame);assert.equal(frame.type,'FunctionExpression');assert.equal(findNodes(frame,n=>n.type==='CallExpression'&&n.callee.type==='SequenceExpression'&&member(n.callee.expressions[1],'r','c')&&n.arguments[0]?.value===90).length,1);w(owner,frame,'complete90-slot ordinary row coordinator');w(owner,publicFrame.call,'actual public row registration');
 const APIs={t:[732486,'JSX'],r:[445242,'compiler memo'],l:[365089,'truncateAddress'],a:[458310,'Link'],i:[398902,'useTranslation'],n:[335703,'CoinPosition'],s:[204478,'RootCallout'],o:[386028,'QuotePreview'],d:[710416,'ReplyCell'],c:[741084,'normalizeAvatarInput'],u:[606178,'inset constant'],m:[860787,'previewImage'],f:[390767,'thread path'],p:[287129,'accepted replyContextPreview'],h:[338319,'classNames']};for(const[alias,[id,role]]of Object.entries(APIs))w(owner,imp(owner,alias,id),'actual consumed '+role+' dependency');
 const providerExports={365089:['d'],458310:['default'],398902:['f'],335703:['f'],204478:['f'],710416:['f'],386028:['f'],741084:['f'],860787:['Z','z'],338319:['c']};
 for(const[id,keys]of Object.entries(providerExports))for(const f of fs[id])for(const key of keys){
  if(id==='458310'){
   const table=decl(f,'n').init;assert.equal(table.type,'ObjectExpression');const getter=exactlyOne(table.properties.filter(p=>p.key.name==='default'),'actual CJS Link default getter');assert.equal(getter.value.body.body[0].argument.name,'w');w(f,getter,'actual CJS Link default getter; not an ESM s export');
   const registration=exactlyOne(findNodes(f.node,n=>n.type==='ForInStatement'&&n.right.name==='n'),'CJS export getter registration');w(f,registration,'actual Object.defineProperty CJS Link namespace registration');
   const assignment=exactlyOne(findNodes(f.node,n=>n.type==='AssignmentExpression'&&member(n.left,'t','exports')&&member(n.right,'r','default')),'CJS default interop');w(f,assignment,'actual CJS default interop; Link implementation external');continue;
  }
  const x=exp(f,Number(id),key);w(f,x.call,'required port export '+id+'.'+key);w(f,value(f,x),'source interface witness only; port '+id+'.'+key+' implementation external');}
 const inset=exp(fs[606178][0],606178,'U').node;assert.equal(inset.type,'ObjectExpression');w(fs[606178][0],inset,'complete consumed density inset constant');
 let canonicalThread,thread;for(const f of fs[390767]){const n=value(f,exp(f,390767,'f')),normalized=normalizeSession(n,{});if(!canonicalThread){canonicalThread=normalized;thread={f,n};}else assert.deepEqual(normalized,canonicalThread,'all three thread path variants');w(f,n,'complete pure thread path variant');}
 // Reuse accepted891's mapper and its existing source verifier, not another mapper copy.
 const accepted=await extractUserReplies(root);const mapperModule=await readFile(path.join(root,'reconstruction/user-replies/client.mjs'));w(fs[287129][0],exp(fs[287129][0],287129,'g').call,'accepted parent-first context-preview API');
 const home=fs[163807][0],homeView=value(home,exp(home,163807,'HomeView')),mobile=exactlyOne(home.node.body.body.filter(n=>n.type==='FunctionDeclaration'&&n.id.name==='eH'),'mobile Home owner'),planner=decl(home,'ez').init,list=decl(home,'eG').init;
 assert.equal(findNodes(homeView,n=>n.type==='CallExpression'&&n.arguments[0]?.name==='eH').length,1);assert.equal(findNodes(mobile,n=>n.type==='CallExpression'&&n.callee.name==='ez').length,1);assert.equal(findNodes(planner,n=>n.type==='CallExpression'&&n.arguments[0]?.name==='eG').length,1);
 for(const[n,label]of[[homeView,'complete HomeView viewport admission'],[mobile,'complete conditional mobile Home static context'],[planner,'complete tab→feed-list handoff']])w(home,n,label);w(home,imp(home,'c',349919),'actual ordinary MAIN row dependency');
 const caller=exactlyOne(findNodes(list,n=>n.type==='CallExpression'&&member(n.arguments[0],'c','f')&&n.arguments[1]?.type==='ObjectExpression'),'actual MAIN row invocation');w(home,caller,'actual MAIN non-repost row JSX invocation/descriptor');
 const html=await corpus.capture('evidence/web/objects/b713215f09b03c14');assert.equal(html.record.url,'https://pump.fun/');assert.equal(html.record.sha256,'5c54a668997394767a338ff5efe132ba3400bd5e1c4b6bb16c9c075b6a389409');let stream='';for(const m of html.text.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)){if(!m[1].includes('__next_f.push'))continue;for(const n of findNodes(parse(m[1],{sourceType:'script'}),n=>n.type==='CallExpression'&&member(n.callee.object,'self','__next_f')&&n.callee.property.name==='push'&&n.arguments[0]?.type==='ArrayExpression')){const a=n.arguments[0].elements;if(a[0]?.value===1&&a[1]?.type==='StringLiteral')stream+=a[1].value;}}
 const flight=parseFlightRecords(stream),imports=[...flight].filter(([,r])=>r.kind==='import'&&r.value[0]===163807&&r.value[2]==='HomeView');assert.equal(imports.length,1);const uses=[];function visit(v,p=[]){if(!v||typeof v!=='object')return;if(Array.isArray(v)&&v[0]==='$'&&v[1]==='$L'+imports[0][0])uses.push({path:p,props:v[3]});for(const[k,x]of Object.entries(v))visit(x,[...p,k]);}for(const[id,r]of flight)if(r.kind!=='import')visit(r.value,[id]);assert.equal(uses.length,1);
 const text=await prettier.format(`
import{replyContextPreview}from'../user-replies/client.mjs';
const threadPath=${thread.f.text(thread.n)};
const ROW_INSET=${fs[606178][0].text(inset)};
// Complete source owner; existing render/leaf/provider APIs are explicit capabilities.
export function createOrdinaryReplyRow({jsx,jsxs,Fragment,useMemoCache,classNames,useTranslation,truncateAddress,normalizeAvatarInput,previewImage,Link,CoinPosition,RootCallout,QuotePreview,ReplyCell}){
 for(const[name,cap]of Object.entries({jsx,jsxs,useMemoCache,classNames,useTranslation,truncateAddress,normalizeAvatarInput,previewImage}))if(typeof cap!=='function')throw new TypeError('Explicit ordinary row capability required: '+name);
 for(const[name,cap]of Object.entries({Fragment,Link,CoinPosition,RootCallout,QuotePreview,ReplyCell}))if(cap==null)throw new TypeError('Explicit ordinary row renderer required: '+name);
 const t={jsx,jsxs,Fragment},r={c:useMemoCache},l={d:truncateAddress},a={default:Link},i={f:useTranslation},n={f:CoinPosition},s={f:RootCallout},o={f:QuotePreview},d={f:ReplyCell},c={f:normalizeAvatarInput},u={U:ROW_INSET},m={Z:previewImage,z:{list:40}},f={f:threadPath},p={g:replyContextPreview},h={c:classNames};
 return ${owner.text(frame)};
}
`,{parser:'babel'});
 return{text,provenance:{schemaVersion:1,baseCommit:'094a06f18df738d41e77070c1a009e135671ac1a',anchors:corpus.anchors,contexts,witnesses,moduleSha256:sha256(Buffer.from(text)),
 mainAdmission:{rootHTML:html.record,flightImport:imports[0],elementUses:uses,path:'rootFlight→163807.HomeView conditional mobile eH→ez→eG non-repost rows→349919.f',scope:'Static conditional admitted MAIN path, not observed original row rendering or recovered Home query/coordinator',excluded:'316917/individual token/coin detail callers excluded'},
 credited:{mapper:'Accepted891 replyContextPreview and existing original-user-replies source verifier reused unchanged',mapperModuleSha256:sha256(mapperModule),mapperVerifierArtifactSha256:sha256(JSON.stringify(accepted)),renderers:'Open1523 quote preview and1943 reply cell, original204478 root and335703 position renderer remain exact required ports; no copies or recovery retally',leaf:'Existing365089 label/741084 image admission/860787 preview helpers remain explicit exact interfaces; no copied cores'},
 APIs,limits:['Captured factories parsed inertly only; generated editable source executes','No Home data/query/parent selection reconstruction or mounted-original/native/API/UI/security/feature qualification','All renderers/translation/leaf helpers are explicit source-signature ports; no original provider/class/React/framework equivalence','PositionRead is an opaque supplied value, with no financial/RPC/accounting interpretation','No protected like/share/mute/auth/service/router action or remote asset acquisition']}};
}
export async function verify(root=APP_ROOT){const r=await recover(root);assert.equal(await readFile(path.join(root,DIRECTORY,'client.mjs'),'utf8'),r.text,'ordinary row source differs');assert.equal(await readFile(path.join(root,DIRECTORY,'PROVENANCE.json'),'utf8'),JSON.stringify(r.provenance,null,2)+'\n','ordinary row provenance differs');return r.provenance;}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){assert.ok(process.argv.length===3&&['--write','--check'].includes(process.argv[2]),'Use --write|--check');if(process.argv[2]==='--write'){const r=await recover();await mkdir(path.join(APP_ROOT,DIRECTORY),{recursive:true});await writeFile(path.join(APP_ROOT,DIRECTORY,'client.mjs'),r.text);await writeFile(path.join(APP_ROOT,DIRECTORY,'PROVENANCE.json'),JSON.stringify(r.provenance,null,2)+'\n');}else await verify();console.log('PASS complete90-slot ordinary row, all thread/provider variants and conditional MAIN caller');}
