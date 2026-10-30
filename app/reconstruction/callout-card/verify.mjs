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
  "146695": [
    "bb995bc856796eb404e21763f5a72275af2b0efa06b46f0d12507e1c6a3d90a1"
  ],
  "432626": [
    "98be45485d8453bae71b3fa5eaf90f97bedf30169d8987ea51734f168abe889d"
  ],
  "705313": [
    "d20ae1800486b11692b11f5a2172e262d6e11c84a1c8912eaa73b615d8d058b9"
  ],
  "98525": [
    "38b7b65f7e40c1463314e2e5d484a63675c6d48338435ee54a71a4c5593f046b"
  ],
  "458310": [
    "637fd83c895d24a43cfd4243adbb9daea8b61e6c81df9feb82fb844f1e0cbe43"
  ],
  "398902": [
    "6a277435e4b43e8ed386083bdfce657ee1b257e9dc52a191a8b27ccc70e6f267"
  ],
  "364889": [
    "8e86c0d8ec8c4ede46d7fd8a949045c10ae434daf362f0bf26485fcf2504e094",
    "1eeb7e88c867c39e0e77454b5f5275beb50ee47351d8b9405305b613585b5e1b",
    "a4cb87e92ac156304798a162650e59347272e58057c65f60e52b6134d3fa06c1"
  ],
  "354002": [
    "492e7790a26bf03961b2bb2ff21607788b50d1b5a3098751da1831498d9912ab"
  ],
  "157633": [
    "a2b26b88ffe57560a24d769c2cc85d620e337cbd9210757b02bc265ad486c048"
  ],
  "745018": [
    "4cc46a6d51b6a9b0fe8ce9f64d77e130e7961309e881fe14f64efa16fb09f660"
  ],
  "177852": [
    "c8c99eedebb78427b0e1fffcef870ec8f7416e40f524e6f28859507311801480"
  ],
  "783358": [
    "c8c99eedebb78427b0e1fffcef870ec8f7416e40f524e6f28859507311801480"
  ],
  "787494": [
    "9241a70842a79f8b83695e7aac04a184c3ac75d9b3b9595e7d6a9b261615787c"
  ],
  "428189": [
    "9d89ced96773ae39ab3b07723fc130c2e27970b0d7383ce157978a7691e82b78"
  ],
  "174251": [
    "c0467989c10ed4eee1b974863874d108285ab3dddb948799e042424a82ed2038"
  ],
  "409954": [
    "fcb2e40ca1d849a9432477c7265d3720b015d3ef3786aefde383cf1e0a3b62e9",
    "7c87904f8f332e95744b3d16ca40fce14e88a97bea5be93d5e44a835f5984c74"
  ],
  "529841": [
    "2c48084aa599d13dd584db59b0f98aaff7553849ceca936596d1063b20ded266"
  ],
  "338319": [
    "5b27b6647671eec79898f430326e92e0e8c08d9fc9e2984c70a664def7ae1cb2"
  ],
  "369091": [
    "088fd0b0aa42de2a5d4a2797e3fbc2190ae623da2e301374857636ac7c9caa29",
    "d75fd268adfb74ad9472afcdb0f4d73b7a11ac4f568c83048ad8ed7dff054ee1"
  ],
  "953283": [
    "943e73d5053096c91c183d0a9126f41c0bd690889aebc0d2a1847254b1a1dc68"
  ],
  "279602": [
    "943e73d5053096c91c183d0a9126f41c0bd690889aebc0d2a1847254b1a1dc68"
  ],
  "540805": [
    "058ef17f92b13d44c2ead869a78a52961abc88fd4814fa72514f5c11c1fc85be"
  ],
  "561259": [
    "a4a01894bb48aa90cd817bcde3e6fab7bb732afa14ec5e1549d095728ca3b6d4"
  ]
};
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {parse} from '@babel/parser';
import prettier from 'prettier';
import {openCorpus,findNodes,exactlyOne,member,sha256} from '../../scripts/original-contracts/source.mjs';
import {parseFlightRecords} from '../../scripts/settings-client-contract.mjs';
export const APP_ROOT=fileURLToPath(new URL('../..',import.meta.url));
export const DIRECTORY='reconstruction/callout-card';
const decls=f=>f.node.body.body.flatMap(n=>n.type==='VariableDeclaration'?n.declarations:[]);
const decl=(f,name)=>exactlyOne(decls(f).filter(n=>n.id.name===name),'top binding '+name);
const fn=(f,name)=>exactlyOne(f.node.body.body.filter(n=>n.type==='FunctionDeclaration'&&n.id.name===name),'local function '+name);
function exp(f,id,key){const call=exactlyOne(findNodes(f.node,n=>n.type==='CallExpression'&&member(n.callee,f.runtime,'s')&&(n.arguments[1]?.value===id||n.arguments.length===1)&&n.arguments[0]?.type==='ArrayExpression'&&n.arguments[0].elements.some(v=>v?.value===key)),'export '+id+'.'+key);const a=call.arguments[0].elements,at=a.findIndex(n=>n?.value===key),direct=a[at+1]?.value===0;return{call,node:direct?a[at+2]:a[at+1],getter:!direct};}
function value(f,x){let n=x.node;if(x.getter&&n.type==='ArrowFunctionExpression')n=n.body;if(n.type==='Identifier'){const fs=f.node.body.body.filter(x=>x.type==='FunctionDeclaration'&&x.id.name===n.name);return fs.length?exactlyOne(fs,'export function'):decl(f,n.name).init;}return n;}
function imp(f,name,id){const d=decl(f,name);assert.ok(member(d.init?.callee,f.runtime,'i'),'actual import '+name);assert.equal(d.init.arguments[0]?.value,id);return d;}
// Bounded lexical audit of these complete frames. Bind array destructuring
// explicitly; do not flatten nested locals into a module-wide identifier set.
function freeNames(root){
 const free=new Set();
 const bind=(n,s)=>{if(!n)return;if(n.type==='Identifier')s.add(n.name);else if(n.type==='ArrayPattern')n.elements.forEach(x=>bind(x,s));else if(n.type==='ObjectPattern')n.properties.forEach(x=>bind(x.type==='RestElement'?x.argument:x.value,s));else if(n.type==='AssignmentPattern')bind(n.left,s);else if(n.type==='RestElement')bind(n.argument,s);else throw Error('unsupported frame binding '+n.type);};
 const visit=(n,scopes=[])=>{if(!n||typeof n!=='object')return;if(Array.isArray(n)){n.forEach(x=>visit(x,scopes));return;}
  if(['FunctionExpression','FunctionDeclaration','ArrowFunctionExpression'].includes(n.type)){const local=new Set();if(n.id)bind(n.id,local);n.params.forEach(p=>bind(p,local));for(const p of n.params)if(p.type==='AssignmentPattern')visit(p.right,[...scopes,local]);visit(n.body,[...scopes,local]);return;}
  if(n.type==='BlockStatement'){const local=new Set();for(const s of n.body){if(s.type==='VariableDeclaration')s.declarations.forEach(d=>bind(d.id,local));else if(s.type==='FunctionDeclaration')bind(s.id,local);}visit(n.body,[...scopes,local]);return;}
  if(n.type==='Identifier'){if(!scopes.some(s=>s.has(n.name)))free.add(n.name);return;}
  if(n.type==='VariableDeclarator'){visit(n.init,scopes);return;}
  if(['MemberExpression','OptionalMemberExpression'].includes(n.type)){visit(n.object,scopes);if(n.computed)visit(n.property,scopes);return;}
  if(n.type==='ObjectProperty'){if(n.computed)visit(n.key,scopes);visit(n.value,scopes);return;}
  assert.ok(!['CatchClause','ForStatement','ForInStatement','ForOfStatement','ObjectMethod','ClassDeclaration'].includes(n.type),'unsupported selected frame scope '+n.type);
  for(const[k,v]of Object.entries(n))if(!['loc','start','end','extra','comments','leadingComments','trailingComments','innerComments'].includes(k))visit(v,scopes);
 };visit(root);return [...free].sort();
}
export async function recover(root=APP_ROOT){
 const corpus=await openCorpus(root),fs={},contexts=[],witnesses=[];
 const w=(f,n,label)=>{const p=f.witness(n,label);witnesses.push(p);return p;};
 for(const[key,hashes]of Object.entries(PINS)){const id=Number(key),rows=corpus.index.modules.filter(m=>m.ids.includes(id));assert.deepEqual(rows.map(m=>m.sha256).sort(),[...hashes].sort(),'all physical variants '+id);fs[id]=[];for(const hash of hashes){const m=exactlyOne(rows.filter(x=>x.sha256===hash),'variant');for(const origin of m.origins){const f=await corpus.factory(id,{source:origin.source});fs[id].push(f);contexts.push(f.provenance);}}}
 const owner=fs[204478][0],registration=exp(owner,204478,'f'),frame=value(owner,registration);
 assert.equal(frame.type,'FunctionExpression');
 const slots=n=>findNodes(n,x=>x.type==='CallExpression'&&x.callee.type==='SequenceExpression'&&member(x.callee.expressions[1],'l','c')).map(x=>x.arguments[0]?.value);
 assert.deepEqual(slots(frame),[208]);w(owner,registration.call,'actual public204478.f registration');w(owner,frame,'complete208-slot ordinary root display owner');
 const frames=[['em',48,'updates collapse/list owner'],['ep',21,'native expand-updates control'],['ex',1,'dotted thread rail'],['ef',117,'complete update display row']];
 for(const[name,count,label]of frames){const n=fn(owner,name);assert.deepEqual(slots(n),[count]);w(owner,n,'complete'+count+'-slot '+label);}
 const locals=['eh','eg','ey','eb'];for(const name of locals)w(owner,fn(owner,name),'complete local state/propagation helper '+name);
 const clamp=decl(owner,'ew');w(owner,clamp,'complete used note-clamp class map');
 const APIs={t:[732486,'jsx/jsxs/Fragment'],l:[445242,'compiler memo'],o:[352386,'useState/useRef/useEffect'],a:[146695,'profileRoute'],s:[432626,'ProfileHover'],r:[705313,'Avatar'],i:[98525,'VerifiedBadge'],n:[458310,'Link'],c:[398902,'useTranslation'],d:[364889,'ImagePreview'],u:[354002,'Video'],m:[157633,'FilledHeart'],p:[745018,'OutlineHeart/ShareIcon/CommentIcon'],x:[177852,'ShareMenu'],f:[783358,'action classes'],h:[787494,'hot classes'],g:[428189,'useReplyLike'],y:[174251,'RichText f, not N'],k:[409954,'ProfileLink'],N:[529841,'RelativeTime'],L:[540805,'formatCount'],z:[338319,'classNames'],P:[369091,'useIpfsPrefix'],R:[953283,'AvatarDecoration'],W:[279602,'useDecorationKey'],ev:[561259,'isVideoUrl']};
 for(const[alias,[id,label]]of Object.entries(APIs))w(owner,imp(owner,alias,id),'actual consumed '+label+' import');
 const exports={146695:['$'],432626:['f'],705313:['f'],98525:['f'],398902:['f'],364889:['f'],354002:['f'],157633:['cJ'],745018:['q4','cJ','Z2'],177852:['f'],783358:['I','L','d'],787494:['$','k'],428189:['f'],174251:['f'],409954:['o'],529841:['f'],540805:['O'],338319:['c'],369091:['useIpfsPrefix'],953283:['f'],279602:['f'],561259:['y']};
 for(const[id,keys]of Object.entries(exports))for(const f of fs[id])for(const key of keys){const x=exp(f,Number(id),key);w(f,x.call,'required actual export '+id+'.'+key);w(f,value(f,x),'required source-interface witness '+id+'.'+key+'; no provider implementation claim');}
 for(const f of fs[458310]){const table=decl(f,'n').init;assert.equal(table.type,'ObjectExpression');const getter=exactlyOne(table.properties.filter(p=>p.key.name==='default'),'CJS default getter');assert.equal(getter.value.body.body[0].argument.name,'w');w(f,getter,'actual CJS Link default getter');w(f,exactlyOne(findNodes(f.node,n=>n.type==='ForInStatement'&&n.right.name==='n'),'CJS namespace registration'),'complete actual CJS Link getter registration');w(f,exactlyOne(findNodes(f.node,n=>n.type==='AssignmentExpression'&&member(n.left,'t','exports')&&member(n.right,'r','default')),'CJS default interop'),'actual CJS Link default interop');}
 const comments=exp(owner,673259,'f');assert.equal(comments.node.name,'ed');w(owner,comments.call,'exported673259.f Comments required renderer handoff');w(owner,fn(owner,'ed'),'complete Comments interface witness only; implementation external');
 const allowedFree=new Set([...Object.keys(APIs),'Symbol','ResizeObserver','ew','em','ep','ex','ef','eh','eg','ey','eb','ed']);
 const scopeClosure=[{name:'204478.f',node:frame},...frames.map(([name])=>({name,node:fn(owner,name)})),...locals.map(name=>({name,node:fn(owner,name)}))].map(({name,node})=>{const free=freeNames(node);assert.deepEqual(free.filter(n=>!allowedFree.has(n)),[],'unresolved actual frame binding '+name);return{name,freeBindings:free,sourceSha256:sha256(owner.text(node))};});
 const video=value(fs[561259][0],exp(fs[561259][0],561259,'y'));assert.equal(video.type,'ArrowFunctionExpression');w(fs[561259][0],video,'complete used pure URL suffix classifier; no media acquisition');
 const action={};for(const key of ['I','L','d']){const n=value(fs[783358][0],exp(fs[783358][0],783358,key));assert.ok(['ObjectExpression','StringLiteral'].includes(n.type));action[key]=fs[783358][0].text(n);w(fs[783358][0],n,'used source action class data '+key);}
 const hot={};for(const key of ['$','k']){const n=value(fs[787494][0],exp(fs[787494][0],787494,key));assert.equal(n.type,'StringLiteral');hot[key]=fs[787494][0].text(n);}
 const row=fs[349919][0];w(row,imp(row,'s',204478),'actual ordinary row root-display import');
 const descriptors=findNodes(row.node,n=>n.type==='CallExpression'&&member(n.arguments[0],'s','f')&&n.arguments[1]?.type==='ObjectExpression');assert.equal(descriptors.length,1);w(row,descriptors[0],'complete incoming ordinary MAIN root-callout JSX descriptor');
 const home=fs[163807][0],homeView=value(home,exp(home,163807,'HomeView')),mobile=fn(home,'eH'),planner=decl(home,'ez').init,list=decl(home,'eG').init;
 assert.equal(findNodes(homeView,n=>n.type==='CallExpression'&&n.arguments[0]?.name==='eH').length,1);assert.equal(findNodes(mobile,n=>n.type==='CallExpression'&&n.callee.name==='ez').length,1);assert.equal(findNodes(planner,n=>n.type==='CallExpression'&&n.arguments[0]?.name==='eG').length,1);
 for(const[n,label]of[[homeView,'complete HomeView viewport admission'],[mobile,'complete conditional mobile Home context'],[planner,'complete tab-to-list handoff']])w(home,n,label);w(home,imp(home,'c',349919),'actual ordinary MAIN row dependency');w(home,exactlyOne(findNodes(list,n=>n.type==='CallExpression'&&member(n.arguments[0],'c','f')&&n.arguments[1]?.type==='ObjectExpression'),'actual MAIN row invocation'),'actual MAIN non-repost row invocation');
 const html=await corpus.capture('evidence/web/objects/b713215f09b03c14');assert.equal(html.record.url,'https://pump.fun/');assert.equal(html.record.sha256,'5c54a668997394767a338ff5efe132ba3400bd5e1c4b6bb16c9c075b6a389409');
 let stream='';for(const m of html.text.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)){if(!m[1].includes('__next_f.push'))continue;for(const n of findNodes(parse(m[1],{sourceType:'script'}),n=>n.type==='CallExpression'&&member(n.callee.object,'self','__next_f')&&n.callee.property.name==='push'&&n.arguments[0]?.type==='ArrayExpression')){const a=n.arguments[0].elements;if(a[0]?.value===1&&a[1]?.type==='StringLiteral')stream+=a[1].value;}}
 const flight=parseFlightRecords(stream),imports=[...flight].filter(([,r])=>r.kind==='import'&&r.value[0]===163807&&r.value[2]==='HomeView');assert.equal(imports.length,1);const uses=[];function visit(v,p=[]){if(!v||typeof v!=='object')return;if(Array.isArray(v)&&v[0]==='$'&&v[1]==='$L'+imports[0][0])uses.push({path:p,props:v[3]});for(const[k,x]of Object.entries(v))visit(x,[...p,k]);}for(const[id,r]of flight)if(r.kind!=='import')visit(r.value,[id]);assert.equal(uses.length,1);
 const text=await prettier.format(`
// Complete original display owners. Required existing APIs stay explicit; captured factories never execute.
export function createCalloutCard(capabilities){
 const{jsx,jsxs,Fragment,useMemoCache,useState,useRef,useEffect,useTranslation,classNames,profileRoute,Avatar,ProfileHover,ProfileLink,Link,AvatarDecoration,useDecorationKey,VerifiedBadge,RelativeTime,RichText,ImagePreview,Video,ShareMenu,useReplyLike,Comments,useIpfsPrefix,formatCount,ShareIcon,OutlineHeart,FilledHeart,CommentIcon,ResizeObserver}=capabilities;
 for(const[name,value]of Object.entries({jsx,jsxs,useMemoCache,useState,useRef,useEffect,useTranslation,classNames,profileRoute,useDecorationKey,useReplyLike,useIpfsPrefix,formatCount}))if(typeof value!=='function')throw new TypeError('Explicit callout capability required: '+name);
 for(const[name,value]of Object.entries({Fragment,Avatar,ProfileHover,ProfileLink,Link,AvatarDecoration,VerifiedBadge,RelativeTime,RichText,ImagePreview,Video,ShareMenu,Comments,ShareIcon,OutlineHeart,FilledHeart,CommentIcon}))if(value==null)throw new TypeError('Explicit callout renderer required: '+name);
 if(!Object.hasOwn(capabilities,'ResizeObserver'))throw new TypeError('Explicit ResizeObserver presence/absence required');
 const t={jsx,jsxs,Fragment},l={c:useMemoCache},o={useState,useRef,useEffect},c={f:useTranslation},z={c:classNames},a={$:profileRoute},r={f:Avatar},s={f:ProfileHover},k={o:ProfileLink},n={default:Link},R={f:AvatarDecoration},W={f:useDecorationKey},i={f:VerifiedBadge},N={f:RelativeTime},y={f:RichText},d={f:ImagePreview},u={f:Video},x={f:ShareMenu},g={f:useReplyLike},ed=Comments,P={useIpfsPrefix},L={O:formatCount},p={q4:ShareIcon,cJ:OutlineHeart,Z2:CommentIcon},m={cJ:FilledHeart};
 const f={I:${action.I},L:${action.L},d:${action.d}},h={$:${hot.$},k:${hot.k}},ev={y:${fs[561259][0].text(video)}};
 const ew=${owner.text(clamp.init)};
 ${frames.map(([name])=>owner.text(fn(owner,name))).join('\n')}
 ${locals.map(name=>owner.text(fn(owner,name))).join('\n')}
 return ${owner.text(frame)};
}
`,{parser:'babel'});
 return{text,provenance:{schemaVersion:1,baseCommit:'094a06f18df738d41e77070c1a009e135671ac1a',anchors:corpus.anchors,contexts,witnesses,moduleSha256:sha256(Buffer.from(text)),frames:[{name:'204478.f',slots:208},...frames.map(([name,slots,role])=>({name,slots,role}))],scopeClosure,APIs,
 mainAdmission:{rootHTML:html.record,flightImport:imports[0],elementUses:uses,path:'rootFlight→163807.HomeView conditional mobile eH→ez→eG ordinary rows→349919.f→204478.f',scope:'Static conditional MAIN admission only; no original row/rendered Home observation',excluded:'316917/individual coin/token-detail incoming callers excluded'},
 credited:{owner:'1959 ordinary row admission/descriptor evidence credited; parent core stays external',display:'1889 ImagePreview,1916 Avatar,1927 decoration,1943 ReplyCell,1374 RichText,1472 RelativeTime,1960 ProfileHover and prior navigation/count/action display remain exact required APIs, no copied cores/recovery retally',helpers:'561259.y used suffix expression included only inside this full owner; no media/acquisition/library claim'},
 limits:['Captured factories inert parsed data; only generated editable functions execute','Exact ports for original React/compiler/JSX/class/translation/renderers/profile-route/IPFS/action/comment APIs; providers and open-PR cores are not imported or copied','Native ResizeObserver/target/ref/geometry behavior is supplied per realm; source effect depends only on clamp eligibility and keeps expansion state','No Home query, auth, protected like/share/comment, router, media acquisition, financial, native/API/security/UI/pixel or feature-completion claim','Provider variants remain physical interface witnesses; no global active winner inferred']}};
}
export async function verify(root=APP_ROOT){const r=await recover(root);assert.equal(await readFile(path.join(root,DIRECTORY,'client.mjs'),'utf8'),r.text,'callout card source differs');assert.equal(await readFile(path.join(root,DIRECTORY,'PROVENANCE.json'),'utf8'),JSON.stringify(r.provenance,null,2)+'\n','callout card provenance differs');return r.provenance;}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){assert.ok(process.argv.length===3&&['--write','--check'].includes(process.argv[2]),'Use --write|--check');if(process.argv[2]==='--write'){const r=await recover();await mkdir(path.join(APP_ROOT,DIRECTORY),{recursive:true});await writeFile(path.join(APP_ROOT,DIRECTORY,'client.mjs'),r.text);await writeFile(path.join(APP_ROOT,DIRECTORY,'PROVENANCE.json'),JSON.stringify(r.provenance,null,2)+'\n');}else await verify();console.log('PASS complete208+48+21+1+117-slot callout workflow and MAIN/provider closure');}
