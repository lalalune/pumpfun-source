const PINS={
  "335703": [
    "ac958e6c1ea5ae37647619da80cee73000e79667bdb7e1ac2f0c49a2b43c4c20"
  ],
  "223363": [
    "5ecd3c60c45eac4b88bb28e57cfdd9418e734fa98a5fd72c169295859cc9d973",
    "0eeb90471c3b038b2cd0f8ae5bd5c168a235b0b3ff2c69c2e2768693323044b4",
    "944309355edd6be4a6567e7d5d76e0803224e91aef18e63c4589d1a77b00ba3e"
  ],
  "210940": [
    "5ecd3c60c45eac4b88bb28e57cfdd9418e734fa98a5fd72c169295859cc9d973",
    "0eeb90471c3b038b2cd0f8ae5bd5c168a235b0b3ff2c69c2e2768693323044b4",
    "944309355edd6be4a6567e7d5d76e0803224e91aef18e63c4589d1a77b00ba3e"
  ],
  "349919": [
    "d9e37561efe6c7dfc134d7ace63aa44c5f74e6c406700bd925e0fb7cd4569bc6"
  ],
  "163807": [
    "828b7d1e93dd4135f930646c9f29729e82209232a020fca54e3e775a20eafe44"
  ],
  "248496": [
    "98c7083f780ae537f4559367a338f469e2d9897504c37398858270a41e5d5da1"
  ],
  "338319": [
    "5b27b6647671eec79898f430326e92e0e8c08d9fc9e2984c70a664def7ae1cb2"
  ],
  "79631": [
    "cba1a94a5303b46d15281f9b7f6abcc1067a75ef331e9168d491df22add78a27",
    "107202cf55e5832ddd4cf6e1e1baf1bbcce6dfec9c3ddaab5e7e9d661c813f08",
    "f608cb1a5c8edfd9b2516b8bc011c6a260a1efdb9887757e29eef0059e5369ae",
    "a317c50f6bad5916dc36e75177825ab3690e9b5724cbf93a1a3410383249b3ab"
  ],
  "672287": [
    "e0807ccad10aef65699d92b021267532d440bb0691a31e57d5775a392db09579"
  ],
  "889451": [
    "12b6972190e36850c505a55bcd13e9630e2f7e95154fb97e043ab29c694f2a0f"
  ],
  "384886": [
    "9c9f618b76fb17141d8f9e484d08c037906da8c060c223efcd32bfee111f54cb"
  ],
  "928529": [
    "9d04e5080414026f18d95494bad5047decc0872662f442e6302712a002050c39"
  ],
  "398902": [
    "6a277435e4b43e8ed386083bdfce657ee1b257e9dc52a191a8b27ccc70e6f267"
  ],
  "667876": [
    "bd1f18f5200162371044f8b7caad4e466e3be151153723131a70f5901ec25a45"
  ],
  "34011": [
    "2e47964258000544484a80e0c6e499ba920ed0e03ea6569981e17352426690c0"
  ],
  "540805": [
    "058ef17f92b13d44c2ead869a78a52961abc88fd4814fa72514f5c11c1fc85be"
  ],
  "529841": [
    "2c48084aa599d13dd584db59b0f98aaff7553849ceca936596d1063b20ded266"
  ],
  "908163": [
    "992e64a7bd619ff1db73df8723c523ca60ab4577e8d4f0e0260484e1c07a51cf"
  ],
  "170450": [
    "72a61a3e662f4e2995ea53610e55b0658ec866cf82ddca6c904962252fe06ff7"
  ],
  "890088": [
    "b6933f856a7fe6205483d9adca13b97117fed3fc3822f1383ed3ba99e512040b",
    "f29f27e66af25973af60575b0ffea4e03a9fc939855c0ff7d4a8f3c02d448e09"
  ],
  "714283": [
    "b6933f856a7fe6205483d9adca13b97117fed3fc3822f1383ed3ba99e512040b",
    "f29f27e66af25973af60575b0ffea4e03a9fc939855c0ff7d4a8f3c02d448e09"
  ],
  "592209": [
    "6b3fe2082dbaa30d9d803777d25ef02aa53ccc736b312980dec097206324c790"
  ],
  "633311": [
    "791665a66d45f129d6c31e0e1f0a79b0a24e8b95904ddee3c559fafca0cade40"
  ],
  "876299": [
    "4a495022ede8ff2783c67081089ea3276c3e0d42e3e76cea8f4057290d58816c"
  ]
};
const ACCEPTED_READER_SHA='e135b54361f954eac3918124503dbab9cb35f322423af09483bdfed54905f1db';
import assert from'node:assert/strict';import{readFile,writeFile,mkdir}from'node:fs/promises';import path from'node:path';import{fileURLToPath}from'node:url';import{parse}from'@babel/parser';import prettier from'prettier';
import{openCorpus,findNodes,exactlyOne,member,propertyName,sha256}from'../../scripts/original-contracts/source.mjs';import{normalizeSession}from'../../scripts/verify-search-session.mjs';import{parseFlightRecords}from'../../scripts/settings-client-contract.mjs';import{recover as recoverAcceptedPositions}from'../../scripts/original-positions-by-mint.mjs';
export const APP_ROOT=fileURLToPath(new URL('../..',import.meta.url));export const DIRECTORY='reconstruction/coin-position-display';
const decls=f=>f.node.body.body.flatMap(n=>n.type==='VariableDeclaration'?n.declarations:[]);
const decl=(f,name)=>exactlyOne(decls(f).filter(n=>n.id.name===name),'top binding '+name);
const fn=(f,name)=>exactlyOne(f.node.body.body.filter(n=>n.type==='FunctionDeclaration'&&n.id.name===name),'local function '+name);
function exp(f,id,key){const call=exactlyOne(findNodes(f.node,n=>n.type==='CallExpression'&&member(n.callee,f.runtime,'s')&&(n.arguments[1]?.value===id||n.arguments.length===1)&&n.arguments[0]?.type==='ArrayExpression'&&n.arguments[0].elements.some(v=>v?.value===key)),'export '+id+'.'+key);const a=call.arguments[0].elements,at=a.findIndex(n=>n?.value===key),direct=a[at+1]?.value===0;return{call,node:direct?a[at+2]:a[at+1],getter:!direct};}
function value(f,x){let n=x.node;if(x.getter&&n.type==='ArrowFunctionExpression')n=n.body;if(n.type==='Identifier'){const fs=f.node.body.body.filter(x=>x.type==='FunctionDeclaration'&&x.id.name===n.name);return fs.length?exactlyOne(fs,'export function'):decl(f,n.name).init;}return n;}
function imp(f,name,id){const d=decl(f,name);assert.ok(member(d.init?.callee,f.runtime,'i'),'actual import '+name);assert.equal(d.init.arguments[0]?.value,id);return d;}

const slots=(n,alias)=>findNodes(n,x=>x.type==='CallExpression'&&x.callee.type==='SequenceExpression'&&member(x.callee.expressions[1],alias,'c')).map(x=>x.arguments[0]?.value);
export async function recover(root=APP_ROOT){const corpus=await openCorpus(root),fs={},contexts=[],witnesses=[],comparisons=[];const w=(f,n,label)=>{const v=f.witness(n,label);witnesses.push(v);return v;};
 for(const[key,hashes]of Object.entries(PINS)){const id=Number(key),rows=corpus.index.modules.filter(m=>m.ids.includes(id));assert.deepEqual(rows.map(m=>m.sha256).sort(),[...hashes].sort(),'all physical variants '+id);fs[id]=[];for(const hash of hashes){const m=exactlyOne(rows.filter(x=>x.sha256===hash),'variant');for(const origin of m.origins){const f=await corpus.factory(id,{source:origin.source});fs[id].push(f);contexts.push(f.provenance);}}}
 const owner=fs[335703][0],memoOwner=value(owner,exp(owner,335703,'f')),frame=memoOwner.arguments[0];assert.equal(memoOwner.type,'CallExpression');assert.ok(member(memoOwner.callee.expressions[1],'a','memo'));assert.deepEqual(slots(frame,'i'),[16]);w(owner,memoOwner,'complete memo-wrapped16-slot supplied/read-position owner');w(owner,exp(owner,335703,'f').call,'actual public335703.f registration');
 const projected=decl(owner,'g').init;assert.deepEqual(slots(projected.arguments[0],'i'),[16]);w(owner,projected,'complete memo-wrapped16-slot projection handoff; financial outputs opaque');for(const[name,count]of[['d',8],['c',6]]){assert.deepEqual(slots(fn(owner,name),'i'),[count]);w(owner,fn(owner,name),'complete'+count+'-slot loading skeleton '+name);}
 const ownerImports={t:[732486,'JSX'],i:[445242,'compiler memo'],a:[352386,'React memo'],s:[248496,'Skeleton'],o:[338319,'classNames'],u:[79631,'usePositions'],m:[672287,'useLivePrice'],p:[889451,'projectLive/servedPosition'],h:[384886,'accepted positionLookupKey'],f:[223363,'complete PositionDisplay']};for(const[alias,[id,role]]of Object.entries(ownerImports))w(owner,imp(owner,alias,id),'actual '+role+' dependency');
 for(const f of fs[335703]){assert.equal(f.provenance.sha256,owner.provenance.sha256);w(f,value(f,exp(f,335703,'f')),'complete equal physical owner origin');}
 let canonicalDisplay,display,displayFactory,amount,ring;
 for(const f of fs[223363]){const n=value(f,exp(f,223363,'f'));assert.deepEqual(slots(n,'i'),[154]);const aliases=new Map(decls(f).filter(n=>n.init?.type==='CallExpression'&&member(n.init.callee,f.runtime,'i')).map(n=>[n.id.name,n.init.arguments[0]?.value]));const rings=exactlyOne(decls(f).filter(n=>n.init?.type==='ObjectExpression'&&n.init.properties.some(p=>propertyName(p.key)==='strip')),'ring map');
  const imports={};for(const used of findNodes(n,node=>node.type==='MemberExpression'&&!node.computed&&aliases.has(node.object?.name)))imports[used.object.name+'.'+propertyName(used.property)]='operation:'+aliases.get(used.object.name)+'.'+propertyName(used.property);
  const normalized=normalizeSession(n,{Symbol:'global:Symbol',Number:'global:Number',Date:'global:Date',p:'operation:formatAmount',[rings.id.name]:'data:ring'},imports);if(canonicalDisplay)assert.deepEqual(normalized,canonicalDisplay,'full154-slot display variants differ');else{canonicalDisplay=normalized;display=n;displayFactory=f;amount=value(f,exp(f,210940,'f'));ring=rings.init;}
  comparisons.push({source:f.provenance.source,factorySha256:f.provenance.sha256,normalizedSha256:sha256(JSON.stringify(normalized))});w(f,n,'complete154-slot display variant; lexical alpha equivalent under actual imports');w(f,exp(f,223363,'f').call,'actual public223363.f registration');w(f,value(f,exp(f,210940,'f')),'complete local amount-format callback210940.f');w(f,rings,'complete consumed variant ring data');
  for(const[alias,id]of aliases)w(f,imp(f,alias,id),'actual display namespace '+alias+'→'+id);
 }
 const displayImports={t:732486,i:445242,a:928529,r:398902,n:667876,l:34011,s:540805,o:529841,d:908163,c:170450,u:890088,m:714283,h:592209,f:338319,g:633311};for(const[alias,id]of Object.entries(displayImports))w(displayFactory,imp(displayFactory,alias,id),'canonical emitted namespace '+alias+'→'+id);
 const portExports={248496:['l'],338319:['c'],79631:['_'],672287:['f'],889451:['j','y'],384886:['h'],398902:['f'],667876:['f'],34011:['CoinAvatar'],540805:['k','l','w','u'],529841:['f'],908163:['E'],170450:['f'],890088:['J','R','V','u'],714283:['f'],592209:['v','T'],633311:['l']};
 for(const[id,keys]of Object.entries(portExports))for(const f of fs[id])for(const key of keys){const x=exp(f,Number(id),key);w(f,x.call,'actual required provider export '+id+'.'+key);w(f,value(f,x),'required interface witness only '+id+'.'+key);}
 // Positive ESM facade -> CJS named getter, with the actual Image value bound.
 for(const f of fs[928529]){w(f,imp(f,'t',876299),'actual Image facade provider');const x=exp(f,928529,'default');assert.equal(x.getter,true);assert.ok(member(x.node.body,'t','Image'));w(f,x.call,'actual928529 default getter to876299.Image');}
 for(const f of fs[876299]){const getter=exactlyOne(findNodes(f.node,n=>n.type==='CallExpression'&&member(n.callee,'Object','defineProperty')&&n.arguments[0]?.name==='n'&&n.arguments[1]?.value==='Image'),'actual CJS Image getter');const prop=exactlyOne(getter.arguments[2].properties.filter(p=>p.key.name==='get'),'Image get property');assert.equal(prop.value.body.body[0].argument.name,'p');w(f,getter,'actual876299 CJS Image getter');w(f,decl(f,'p'),'actual forwardRef Image value; library implementation external');}
 const accepted=await recoverAcceptedPositions(root),readerPath='packages/frontend/src/original-contracts/positions-by-mint/reader.mjs',reader=await readFile(path.join(root,readerPath));assert.equal(sha256(reader),ACCEPTED_READER_SHA,'accepted position-key module changed; review required');
 const readerAST=parse(reader.toString('utf8'),{sourceType:'module'}),key=exactlyOne(findNodes(readerAST,n=>n.type==='VariableDeclarator'&&n.id.name==='positionLookupKey'),'accepted position key export');assert.equal(key.init.type,'ArrowFunctionExpression');
 const row=fs[349919][0];w(row,imp(row,'n',335703),'actual ordinary MAIN position owner import');w(row,exactlyOne(findNodes(row.node,n=>n.type==='CallExpression'&&member(n.arguments[0],'n','f')&&n.arguments[1]?.type==='ObjectExpression'),'incoming MAIN position descriptor'),'complete incoming ordinary MAIN coin/position descriptor');
 const home=fs[163807][0],homeView=value(home,exp(home,163807,'HomeView')),mobile=fn(home,'eH'),planner=decl(home,'ez').init,list=decl(home,'eG').init;assert.equal(findNodes(homeView,n=>n.type==='CallExpression'&&n.arguments[0]?.name==='eH').length,1);assert.equal(findNodes(mobile,n=>n.type==='CallExpression'&&n.callee.name==='ez').length,1);assert.equal(findNodes(planner,n=>n.type==='CallExpression'&&n.arguments[0]?.name==='eG').length,1);for(const[n,label]of[[homeView,'complete viewport MAIN admission'],[mobile,'complete conditional mobile Home context'],[planner,'complete tab/list handoff']])w(home,n,label);w(home,imp(home,'c',349919),'actual ordinary row import');w(home,exactlyOne(findNodes(list,n=>n.type==='CallExpression'&&member(n.arguments[0],'c','f')&&n.arguments[1]?.type==='ObjectExpression'),'MAIN row descriptor'),'actual incoming MAIN row descriptor');
 const html=await corpus.capture('evidence/web/objects/b713215f09b03c14');assert.equal(html.record.url,'https://pump.fun/');assert.equal(html.record.sha256,'5c54a668997394767a338ff5efe132ba3400bd5e1c4b6bb16c9c075b6a389409');let stream='';for(const m of html.text.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)){if(!m[1].includes('__next_f.push'))continue;for(const n of findNodes(parse(m[1],{sourceType:'script'}),n=>n.type==='CallExpression'&&member(n.callee.object,'self','__next_f')&&n.callee.property.name==='push'&&n.arguments[0]?.type==='ArrayExpression')){const a=n.arguments[0].elements;if(a[0]?.value===1&&a[1]?.type==='StringLiteral')stream+=a[1].value;}}
 const flight=parseFlightRecords(stream),imports=[...flight].filter(([,r])=>r.kind==='import'&&r.value[0]===163807&&r.value[2]==='HomeView');assert.equal(imports.length,1);const uses=[];function visit(v,p=[]){if(!v||typeof v!=='object')return;if(Array.isArray(v)&&v[0]==='$'&&v[1]==='$L'+imports[0][0])uses.push({path:p,props:v[3]});for(const[k,x]of Object.entries(v))visit(x,[...p,k]);}for(const[id,r]of flight)if(r.kind!=='import')visit(r.value,[id]);assert.equal(uses.length,1);
 const text=await prettier.format(`
import{positionLookupKey}from'../../packages/frontend/src/original-contracts/positions-by-mint/reader.mjs';
// Complete original display behavior; finance/query/locale/media APIs remain explicit opaque capabilities.
export function createCoinPositionWorkflow(capabilities){
 const{jsx,jsxs,Fragment,useMemoCache,memo,Skeleton,classNames,usePositions,useLivePrice,projectLivePosition,projectServedPosition,LocalImage,useTranslation,ChainBadge,CoinAvatar,pnlTone,moneyCompact,moneyValue,moneySigned,RelativeTime,ClosedBadge,useClientReady,formatLargeAmount,makeNumberFormatter,formatFullDate,formatDate,normalizeNumberText,localeFor,defaultLocale,parseTimestamp}=capabilities;
 for(const[name,value]of Object.entries({jsx,jsxs,useMemoCache,memo,classNames,usePositions,useLivePrice,projectLivePosition,projectServedPosition,useTranslation,pnlTone,moneyCompact,moneyValue,moneySigned,useClientReady,formatLargeAmount,makeNumberFormatter,formatFullDate,formatDate,normalizeNumberText,localeFor,parseTimestamp}))if(typeof value!=='function')throw new TypeError('Explicit position display capability required: '+name);
 for(const[name,value]of Object.entries({Fragment,Skeleton,LocalImage,ChainBadge,CoinAvatar,RelativeTime,ClosedBadge}))if(value==null)throw new TypeError('Explicit position renderer required: '+name);
 if(!Object.hasOwn(capabilities,'defaultLocale'))throw new TypeError('Explicit source default locale required');
 const PositionDisplay=(()=>{const t={jsx,jsxs,Fragment},i={c:useMemoCache},a={default:LocalImage},r={f:useTranslation},n={f:ChainBadge},l={CoinAvatar},s={k:pnlTone,l:moneyCompact,w:moneyValue,u:moneySigned},o={f:RelativeTime},d={E:ClosedBadge},c={f:useClientReady},u={J:formatLargeAmount,R:makeNumberFormatter,V:formatFullDate,u:formatDate},m={f:normalizeNumberText},h={v:localeFor,T:defaultLocale},f={c:classNames},g={l:parseTimestamp};const p=${displayFactory.text(amount)},x=${displayFactory.text(ring)};return ${displayFactory.text(display)};})();
 const t={jsx,jsxs,Fragment},i={c:useMemoCache},a={memo},s={l:Skeleton},o={c:classNames},u={_:usePositions},m={f:useLivePrice},p={j:projectLivePosition,y:projectServedPosition},h={h:positionLookupKey},f={f:PositionDisplay};
 ${owner.text(fn(owner,'d'))}
 ${owner.text(fn(owner,'c'))}
 const g=${owner.text(projected)},x=${owner.text(memoOwner)};
 return{CoinPosition:x,PositionDisplay};
}
`,{parser:'babel'});
 return{text,provenance:{schemaVersion:1,baseCommit:'094a06f18df738d41e77070c1a009e135671ac1a',anchors:corpus.anchors,contexts,witnesses,comparisons,moduleSha256:sha256(Buffer.from(text)),frames:[{name:'335703.f',slots:16},{name:'g projection',slots:16},{name:'d framed skeleton',slots:8},{name:'c flat skeleton',slots:6},{name:'223363.f',slots:154}],ownerImports,
 mainAdmission:{rootHTML:html.record,flightImport:imports[0],elementUses:uses,path:'rootFlight→163807.HomeView conditional mobile eH→ez→eG ordinary rows→349919.f→335703.f→223363.f',scope:'Static conditional MAIN admission only, not original row rendering/query/positions observation',excluded:'316917/individual coin/token-detail callers excluded'},
 credited:{parent:'1959 ordinary-row admission/descriptor; implementation external',key:{path:readerPath,moduleSha256:sha256(reader),API:'positionLookupKey',sourceContractSha256:sha256(JSON.stringify(accepted)),status:'Existing accepted pure key reused unchanged; no read/service execution or duplicate recovery'},display:'Existing RelativeTime/CoinAvatar/NextImage/currency/date/locale/policy APIs remain exact required ports, no library/provider core copied'},limits:['Captured factories inert parsed data; generated editable functions execute','Four original read-hook variants and both price-hook origins remain exact provider witnesses only','Live-price/projected/served financial outputs are opaque required capabilities; no valuation, accounting, policy or financial derivation implemented','Read-hook construction/enabled/polling/positionFor fallback and supplied-value precedence preserved, no actual service/query cache/HTTP/RPC acquisition','Full154-slot renderers are lexical-alpha equivalent across all3physical contexts, not a global loader-winner or original framework assertion','No native/API/security/UI/pixel/translation/provider/financial/feature-completion claim; existing pages/captures/SDK/deps/ledger unchanged']}};
}
export async function verify(root=APP_ROOT){const r=await recover(root);assert.equal(await readFile(path.join(root,DIRECTORY,'client.mjs'),'utf8'),r.text,'coin position source differs');assert.equal(await readFile(path.join(root,DIRECTORY,'PROVENANCE.json'),'utf8'),JSON.stringify(r.provenance,null,2)+'\n','coin position provenance differs');return r.provenance;}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){assert.ok(process.argv.length===3&&['--write','--check'].includes(process.argv[2]),'Use --write|--check');if(process.argv[2]==='--write'){const r=await recover();await mkdir(path.join(APP_ROOT,DIRECTORY),{recursive:true});await writeFile(path.join(APP_ROOT,DIRECTORY,'client.mjs'),r.text);await writeFile(path.join(APP_ROOT,DIRECTORY,'PROVENANCE.json'),JSON.stringify(r.provenance,null,2)+'\n');}else await verify();console.log('PASS complete200-slot position read/display workflow and all physical variants');}
