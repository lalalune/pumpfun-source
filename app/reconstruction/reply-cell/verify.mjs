const PINS={
  "204478": [
    "27cc0223b79ff95cac02f490600cc4de894dee66af739beca525502c424dae3f"
  ],
  "349919": [
    "d9e37561efe6c7dfc134d7ace63aa44c5f74e6c406700bd925e0fb7cd4569bc6"
  ],
  "163807": [
    "828b7d1e93dd4135f930646c9f29729e82209232a020fca54e3e775a20eafe44"
  ],
  "365089": [
    "8957b61a69e89f0148cf9a43ca9bc4089cc0c2c892e476af960d1a02c966f4d1"
  ],
  "639374": [
    "491277c531d85bf7569a6e10587108c9b7658ffe5dd0ee76852939c4e20b16c4"
  ],
  "741084": [
    "1877fed09a6363588057a816a53c9d14fa46d3a3cb285321349a29a6ce48812a",
    "64085dc31cc9ebbcde019719b8096cfd198d84216b08826b70461fdfa689dc55",
    "9fa49ca7090d955ed1650833d4a5adb620e11fd63ee88437701c50bd419832a2"
  ],
  "860787": [
    "d27771d5ffd2a78b9b5857b8125fc606122c7b40a1e8e377da8cb34681036183"
  ],
  "540805": [
    "058ef17f92b13d44c2ead869a78a52961abc88fd4814fa72514f5c11c1fc85be"
  ],
  "787494": [
    "9241a70842a79f8b83695e7aac04a184c3ac75d9b3b9595e7d6a9b261615787c"
  ],
  "344048": [
    "ec13507ba1c2b6dffb7746a1b6259debbc527c47bcee769df11e65290f7cc78f"
  ],
  "367498": [
    "6edb8b08b4979a964468e3ddf338d9ebad66e68259310abd1b5c0b3ee1c2a5d1"
  ],
  "179736": [
    "65c55fd94aae19033823800ac95d722d88c4cd549c869927bfe53b6b675596f1",
    "8b4fa23b4c652bb17188ff843e8878e509e6f1bb661a7ccefea3d84710cf150b"
  ],
  "545063": [
    "aa7be3b30b5015ac048674dfe56bba607e457aaeea5d4a5101c81cc3127c60f3"
  ],
  "428189": [
    "9d89ced96773ae39ab3b07723fc130c2e27970b0d7383ce157978a7691e82b78"
  ],
  "369091": [
    "088fd0b0aa42de2a5d4a2797e3fbc2190ae623da2e301374857636ac7c9caa29",
    "d75fd268adfb74ad9472afcdb0f4d73b7a11ac4f568c83048ad8ed7dff054ee1"
  ],
  "174251": [
    "c0467989c10ed4eee1b974863874d108285ab3dddb948799e042424a82ed2038"
  ],
  "98525": [
    "38b7b65f7e40c1463314e2e5d484a63675c6d48338435ee54a71a4c5593f046b"
  ],
  "432626": [
    "98be45485d8453bae71b3fa5eaf90f97bedf30169d8987ea51734f168abe889d"
  ],
  "409954": [
    "fcb2e40ca1d849a9432477c7265d3720b015d3ef3786aefde383cf1e0a3b62e9",
    "7c87904f8f332e95744b3d16ca40fce14e88a97bea5be93d5e44a835f5984c74"
  ],
  "875737": [
    "5298ba552997b00aa1fec680b6f1300c94e06b990a5f0060d62a62bb5e938f57",
    "90d42bdbe09b0b4435e3f3d2c51cb100ef9c6dfd03a274849dbdb71be2df2d10"
  ],
  "529841": [
    "2c48084aa599d13dd584db59b0f98aaff7553849ceca936596d1063b20ded266"
  ],
  "609488": [
    "2b76f790369185efc3f3b2ab4637a2008653f7faa4e82230de54713112158b9b"
  ],
  "177852": [
    "c8c99eedebb78427b0e1fffcef870ec8f7416e40f524e6f28859507311801480"
  ],
  "157633": [
    "a2b26b88ffe57560a24d769c2cc85d620e337cbd9210757b02bc265ad486c048"
  ],
  "745018": [
    "4cc46a6d51b6a9b0fe8ce9f64d77e130e7961309e881fe14f64efa16fb09f660"
  ],
  "705313": [
    "d20ae1800486b11692b11f5a2172e262d6e11c84a1c8912eaa73b615d8d058b9"
  ],
  "364889": [
    "8e86c0d8ec8c4ede46d7fd8a949045c10ae434daf362f0bf26485fcf2504e094",
    "1eeb7e88c867c39e0e77454b5f5275beb50ee47351d8b9405305b613585b5e1b",
    "a4cb87e92ac156304798a162650e59347272e58057c65f60e52b6134d3fa06c1"
  ],
  "398902": [
    "6a277435e4b43e8ed386083bdfce657ee1b257e9dc52a191a8b27ccc70e6f267"
  ],
  "338319": [
    "5b27b6647671eec79898f430326e92e0e8c08d9fc9e2984c70a664def7ae1cb2"
  ],
  "146695": [
    "bb995bc856796eb404e21763f5a72275af2b0efa06b46f0d12507e1c6a3d90a1"
  ]
};
import assert from 'node:assert/strict';
import{readFile,writeFile,mkdir}from'node:fs/promises';
import path from'node:path';import{fileURLToPath}from'node:url';import{parse}from'@babel/parser';import prettier from'prettier';
import{openCorpus,findNodes,exactlyOne,member,sha256}from'../../scripts/original-contracts/source.mjs';
import{normalizeSession}from'../../scripts/verify-search-session.mjs';
import{verifyNavigation}from'../../scripts/verify-search-navigation.mjs';
import{parseFlightRecords}from'../../scripts/settings-client-contract.mjs';
export const APP_ROOT=fileURLToPath(new URL('../..',import.meta.url));export const DIRECTORY='reconstruction/reply-cell';
const decls=f=>f.node.body.body.flatMap(n=>n.type==='VariableDeclaration'?n.declarations:[]);
const decl=(f,name)=>exactlyOne(decls(f).filter(n=>n.id.name===name),'top binding '+name);
function exp(f,id,key){const call=exactlyOne(findNodes(f.node,n=>n.type==='CallExpression'&&member(n.callee,f.runtime,'s')&&(n.arguments[1]?.value===id||n.arguments.length===1)&&n.arguments[0]?.type==='ArrayExpression'&&n.arguments[0].elements.some(v=>v?.value===key)),'export '+id+'.'+key);const a=call.arguments[0].elements,at=a.findIndex(n=>n?.value===key),tag=a[at+1],node=tag?.value===0?a[at+2]:tag;return{call,node,getter:tag?.value!==0};}
function imported(f,alias,id){const d=decl(f,alias);assert.ok(member(d.init?.callee,f.runtime,'i'));assert.equal(d.init.arguments[0]?.value,id);return d;}
const functionDeclaration=(f,name)=>exactlyOne(f.node.body.body.filter(n=>n.type==='FunctionDeclaration'&&n.id.name===name),'function '+name);
function resolved(f,ex){let n=ex.node;if(ex.getter&&n.type==='ArrowFunctionExpression')n=n.body;if(n.type==='Identifier'){const fs=f.node.body.body.filter(x=>x.type==='FunctionDeclaration'&&x.id.name===n.name);return fs.length?exactlyOne(fs,'function export'):decl(f,n.name).init;}return n;}
const PORTS={r:[705313,'f','Avatar'],i:[98525,'f','VerifiedBadge'],s:[432626,'f','ProfileHover'],k:[409954,'o','ProfileLink'],j:[875737,'f','SocialLink'],N:[529841,'f','RelativeTime'],y:[174251,'f','RichText'],d:[364889,'f','ImagePreview'],w:[609488,'f','MuteMenu'],x:[177852,'f','ShareMenu'],
 c:[398902,'f','useTranslation'],P:[369091,'useIpfsPrefix','useIpfsPrefix'],v:[179736,'s','useVerified'],b:[545063,'$','useOwnId'],g:[428189,'f','useReplyLike']};
export async function recover(root=APP_ROOT){
 const corpus=await openCorpus(root),selected={},contexts=[],witnesses=[];const w=(f,n,label)=>{const x=f.witness(n,label);witnesses.push(x);return x;};
 for(const[key,hashes]of Object.entries(PINS)){const id=Number(key),rows=corpus.index.modules.filter(m=>m.ids.includes(id));assert.deepEqual(rows.map(x=>x.sha256).sort(),[...hashes].sort(),'all physical variants '+id);selected[id]=[];for(const hash of hashes){const row=exactlyOne(rows.filter(x=>x.sha256===hash),'variant pin');for(const o of row.origins){const f=await corpus.factory(id,{source:o.source});selected[id].push(f);contexts.push(f.provenance);}}}
 const owner=selected[204478][0],frameExport=exp(owner,710416,'f');assert.equal(frameExport.node.name,'O');const frame=functionDeclaration(owner,'O');
 assert.equal(findNodes(frame,n=>n.type==='CallExpression'&&n.callee.type==='SequenceExpression'&&member(n.callee.expressions[1],'l','c')&&n.arguments[0]?.value===96).length,1);w(owner,frame,'complete96-slot reply-cell owner');w(owner,frameExport.call,'actual710416 public owner registration');
 const helpers=['A','U'].map(n=>decl(owner,n)),stop=functionDeclaration(owner,'T'),focus=decl(owner,'q');for(const n of [...helpers,stop,focus])w(owner,n,'complete owner-local identity/label/stop/focus dependency');
 const providerInterfaces=[];
 for(const[alias,[id,key,port]]of Object.entries(PORTS)){w(owner,imported(owner,alias,id),'actual '+port+' capability import');for(const f of selected[id]??[]){const x=exp(f,id,key);providerInterfaces.push({port,id,key,factory:f.provenance,registration:w(f,x.call,'required '+port+' actual export'),value:w(f,resolved(f,x),'required '+port+' implementation witness only; port not reconstructed')});}}
 for(const[id,keys]of [[157633,['cJ']],[745018,['cJ','q4','Z2']],[338319,['c']]])for(const f of selected[id])for(const key of keys)w(f,exp(f,id,key).call,'actual glyph/class capability export; implementation external');
 for(const[alias,id]of Object.entries({t:732486,l:445242,z:338319,C:365089,S:639374,a:146695,I:860787,_:741084,L:540805,h:787494,m:157633,p:745018}))w(owner,imported(owner,alias,id),'actual leaf/render namespace '+id);
 // Reuse accepted profile route and decoded32-byte guard, not another claimed codec recovery.
 const acceptedNavigation=await verifyNavigation(root);
 for(const f of selected[639374]){w(f,imported(f,'t',344048),'actual base58 decoder namespace');w(f,resolved(f,exp(f,639374,'f')),'credited accepted decoded32-byte predicate');}
 w(selected[344048][0],exp(selected[344048][0],344048,'f').call,'required base58 codec API only; implementation external');
 const formatted=selected[365089][0],truncate=functionDeclaration(formatted,exp(formatted,365089,'d').node.name);w(formatted,truncate,'complete used address label formatter');
 const count=selected[540805][0],countBody=resolved(count,exp(count,540805,'O')),countDeps=['n','r','i'].map(n=>decl(count,n));for(const n of [...countDeps,countBody])w(count,n,'complete used count formatting closure');
 let normalizedImage,canonicalImage;for(const f of selected[741084]){const imp=exactlyOne(decls(f).filter(n=>member(n.init?.callee,f.runtime,'i')&&n.init.arguments[0]?.value===426091),'actual fallback import');const n=resolved(f,exp(f,741084,'f'));const normalized=normalizeSession(n,{}, {[imp.id.name+'.A']:'constant:fallback'});if(!normalizedImage){normalizedImage=normalized;canonicalImage={f,n,alias:imp.id.name};}else assert.deepEqual(normalized,normalizedImage,'all three image-admission variants');w(f,imp,'actual accepted fallback constant import');w(f,n,'complete image-admission variant body');}
 const preview=selected[860787][0],previewBody=resolved(preview,exp(preview,860787,'Z')),prefix=decl(preview,'r'),sizes=exp(preview,860787,'z').node;assert.equal(previewBody.type,'ArrowFunctionExpression');assert.equal(sizes.type,'ObjectExpression');const list=exactlyOne(sizes.properties.filter(p=>p.key.name==='list'),'source list size');assert.equal(list.value.value,40);w(preview,imported(preview,'t',367498),'required existing URI dependency D/d');for(const n of[prefix,previewBody,list])w(preview,n,'complete preview URI/40px-list/default-prefix handoff');
 for(const key of ['D','d'])w(selected[367498][0],exp(selected[367498][0],367498,key).call,'credited existing actual URI API '+key+'; implementation external');
 const style=selected[787494][0],hot=exp(style,787494,'k').node,hover=exp(style,787494,'$').node;assert.equal(hot.type,'StringLiteral');assert.equal(hover.type,'StringLiteral');w(style,hot,'used liked-heart style');w(style,hover,'used like-hover style');
 // Exact admitted MAIN path.316917 detail-only incoming uses are deliberately excluded.
 const home=selected[163807][0],homeExport=exp(home,163807,'HomeView'),homeView=resolved(home,homeExport),mobile=functionDeclaration(home,'eH'),planner=decl(home,'ez').init,listOwner=decl(home,'eG').init;
 const jsxCall=(n,name)=>n.type==='CallExpression'&&n.arguments[0]?.name===name;
 assert.equal(findNodes(homeView,n=>jsxCall(n,'eH')).length,1);assert.equal(findNodes(mobile,n=>n.type==='CallExpression'&&n.callee.name==='ez').length,1);assert.equal(findNodes(planner,n=>jsxCall(n,'eG')).length,1);
 w(home,homeView,'complete original HomeView viewport branch');w(home,mobile,'complete mobile Home owner static admission only');w(home,planner,'complete mobile Home tab→feed-list handoff');
 w(home,imported(home,'c',349919),'actual admitted MAIN reply-row import');const rowUse=exactlyOne(findNodes(listOwner,n=>n.type==='CallExpression'&&member(n.arguments[0],'c','f')),'actual MAIN feed row invocation');w(home,rowUse,'actual MAIN non-repost row→349919 descriptor');
 const parent=selected[349919][0];w(parent,imported(parent,'d',710416),'actual parent→reply-cell import');const parentBody=resolved(parent,exp(parent,349919,'f'));w(parent,parentBody,'complete ordinary MAIN parent frame static context');
 const calls=findNodes(parentBody,n=>n.type==='CallExpression'&&member(n.arguments[0],'d','f')&&n.arguments[1]?.type==='ObjectExpression');assert.equal(calls.length,3);for(const n of calls)w(parent,n,'actual ordinary MAIN reply-cell invocation with full props');
 const html=await corpus.capture('evidence/web/objects/b713215f09b03c14');assert.equal(html.record.url,'https://pump.fun/');assert.equal(html.record.sha256,'5c54a668997394767a338ff5efe132ba3400bd5e1c4b6bb16c9c075b6a389409');let stream='';for(const m of html.text.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)){if(!m[1].includes('__next_f.push'))continue;const ast=parse(m[1],{sourceType:'script'});for(const n of findNodes(ast,x=>x.type==='CallExpression'&&x.callee.type==='MemberExpression'&&x.callee.property.name==='push'&&member(x.callee.object,'self','__next_f')&&x.arguments[0]?.type==='ArrayExpression')){const a=n.arguments[0].elements;if(a[0]?.value===1&&a[1]?.type==='StringLiteral')stream+=a[1].value;}}
 const records=parseFlightRecords(stream),homeImports=[...records].filter(([,r])=>r.kind==='import'&&r.value[0]===163807&&r.value[2]==='HomeView');assert.equal(homeImports.length,1);const uses=[];function visit(v,p=[]){if(!v||typeof v!=='object')return;if(Array.isArray(v)&&v[0]==='$'&&v[1]==='$L'+homeImports[0][0])uses.push({path:p,props:v[3]});for(const[k,x]of Object.entries(v))visit(x,[...p,k]);}for(const[id,r]of records)if(r.kind!=='import')visit(r.value,[id]);assert.equal(uses.length,1);
 const pure=`const truncateAddress=(()=>{${formatted.text(truncate)}return ${truncate.id.name};})();const formatCount=(()=>{let ${countDeps.map(n=>count.text(n)).join(',')};return ${count.text(countBody)};})();const normalizeAvatarInput=(()=>{const ${canonicalImage.alias}={A:FALLBACK_IMAGE};return ${canonicalImage.f.text(canonicalImage.n)};})();`;
 const declarations=`t={jsx,jsxs},l={c:useMemoCache},z={c:classNames},C={d:truncateAddress},S={f:createSolanaGuards({base58}).validAddress},a={$:profileRoute},I={z:{list:40},Z:previewImage},_={f:normalizeAvatarInput},L={O:formatCount},h={k:${style.text(hot)},$:${style.text(hover)}},m={cJ:HeartFilled},p={cJ:HeartOutline,q4:ShareIcon,Z2:CommentIcon},${Object.entries(PORTS).map(([alias,[,,port]])=>alias+'={'+PORTS[alias][1]+':'+port+'}').join(',')}`;
 const source=await prettier.format(`
import{FALLBACK_IMAGE}from'../search-session/session.mjs';
import{profileRoute,createSolanaGuards}from'../search-navigation/navigation.mjs';
${pure}
export function createReplyCell({jsx,jsxs,useMemoCache,classNames,base58,sourceUri,${Object.values(PORTS).map(x=>x[2]).join(',')},HeartFilled,HeartOutline,ShareIcon,CommentIcon}){
 for(const[name,value]of Object.entries({jsx,jsxs,useMemoCache,classNames,${Object.values(PORTS).filter(x=>x[2].startsWith('use')).map(x=>x[2]).join(',')}}))if(typeof value!=='function')throw new TypeError('Explicit reply-cell capability required: '+name);
 for(const[name,value]of Object.entries({${Object.values(PORTS).filter(x=>!x[2].startsWith('use')).map(x=>x[2]).join(',')},HeartFilled,HeartOutline,ShareIcon,CommentIcon}))if(value==null)throw new TypeError('Explicit reply renderer required: '+name);
 if(typeof base58?.decode!=='function'||typeof sourceUri?.D!=='function'||typeof sourceUri?.d!=='function')throw new TypeError('Explicit base58.decode and existing URI D/d capabilities required');
 const previewImage=(()=>{const t=sourceUri;let ${preview.text(prefix)};return ${preview.text(previewBody)};})();
 const ${declarations};
 let ${helpers.map(n=>owner.text(n)).join(',')},${owner.text(focus)};
 ${owner.text(stop)}
 ${owner.text(frame)}
 return O;
}
// Actual descriptors; parent selection/data/query/navigation are not reconstructed here.
export function createMainReplyRenderers({jsx,ReplyCell}){
 if(typeof jsx!=='function'||ReplyCell==null)throw new TypeError('Explicit JSX and stable ReplyCell required');const t={jsx},d={f:ReplyCell};
 return {${calls.map((n,i)=>`${['missingCallout','linkedCallout','unlinkedCallout'][i]}:({reply,callout,replierAvatarShape,replierHref,fallbackXUsername})=>{const w=reply,v=callout,L=replierAvatarShape,Z=replierHref,B=fallbackXUsername;return ${parent.text(n)};}`).join(',')}};
}
`,{parser:'babel'});
 return{text:source,provenance:{schemaVersion:1,baseCommit:'094a06f18df738d41e77070c1a009e135671ac1a',anchors:corpus.anchors,contexts,witnesses,providerInterfaces,
 mainAdmission:{rootHTML:html.record,flightImport:homeImports[0],elementUses:uses,path:'rootFlight→163807.HomeView conditional mobile eH→ez→eG non-repost row→349919.f→710416.f',scope:'Static conditional MAIN admission; no claim that reply rows rendered in retained HTML or that Home data/query/caller implementation is reconstructed',excluded:'316917/individual coin/token-detail contexts are not admission evidence'},
 credited:{navigation:{source:'Accepted search-navigation.profileRoute/createSolanaGuards.validAddress reused unchanged',adapterSha256:acceptedNavigation.adapterSha256},display:'Avatar1916, image1889, text1374, RelativeTime1472, competition1296 and accepted mute/navigation work remain explicit credited interfaces; no copied cores/recovery retally',URI:'Existing367498 D/d API remains an explicit required sourceUri port; no provider acquisition/normalizer copied'},
 comparison:'Complete owner and selected helper bodies regenerated; all image-admission variants use existing strict lexical-alpha AST comparison. Provider variants are witnesses only, with no global winner or implementation-equivalence claim.',
 moduleSha256:sha256(Buffer.from(source)),ports:PORTS,limits:['Captured factories inert parsed only; generated editable callbacks execute','Like/own-ID/verified/IPFS/translation and all renderers are exact required host interfaces; no auth/service/provider acquisition','No real like/share/mute/protected actions, router execution, CDN/media read or identity trust','MAIN admission is conditional static evidence, not observed original row/native/product/API/UI/security/feature qualification']}};
}
export async function verify(root=APP_ROOT){const r=await recover(root);assert.equal(await readFile(path.join(root,DIRECTORY,'client.mjs'),'utf8'),r.text,'reply-cell editable source differs');assert.equal(await readFile(path.join(root,DIRECTORY,'PROVENANCE.json'),'utf8'),JSON.stringify(r.provenance,null,2)+'\n','reply-cell provenance differs');return r.provenance;}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){assert.ok(process.argv.length===3&&['--write','--check'].includes(process.argv[2]),'Use --write|--check');if(process.argv[2]==='--write'){const r=await recover();await mkdir(path.join(APP_ROOT,DIRECTORY),{recursive:true});await writeFile(path.join(APP_ROOT,DIRECTORY,'client.mjs'),r.text);await writeFile(path.join(APP_ROOT,DIRECTORY,'PROVENANCE.json'),JSON.stringify(r.provenance,null,2)+'\n');}else await verify();console.log('PASS complete96-slot reply cell, full selected helpers/providers and conditional MAIN caller chain');}
