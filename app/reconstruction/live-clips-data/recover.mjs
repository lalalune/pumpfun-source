import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {generate} from '@babel/generator';
import {openCorpus,findNodes,exactlyOne,member,sha256} from '../../scripts/original-contracts/source.mjs';
import {parseFlightRecords} from '../../scripts/settings-client-contract.mjs';
export const APP_ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
export const DIRECTORY='reconstruction/live-clips-data';
const pins=[
 [944001,'1c56dd013720ae62a9c8ec316ebf1921d9fb13dc436bd75f7eefacdaad40aecb'],
 [31113,'aa72011769a3b4ed93846aa469860c5b661aafea0e98fbf5da8432305f2348c5'],
 [445242,'2d7f3e592645b5e2d997e444ee9b10be6dc8c357680552dccddafb63e4887576'],
 [532815,'30e0e70b96ec8bc14a84e8ebab1dc7a376f543667300fa43b118f00c3199ae9a'],
 [458013,'598394177ad289f8638adbc0c5567c263e5f9d61f1567a26dca7b08dcabcbc21'],
 [363250,'e6fea22fefde82715cf2e611ea91240e636eda105ce2d4da95af63753d341e26'],
 [606706,'d97c7c9447e248dcaeef4b872bb869c9056d2979cdf53731913116fb8544e429'],
 [647145,'e283089e5702f4d45228fbd9d7a68704974e622d4fc930f59ee22fe97d815b83'],
 [788501,'db885fc927427d144544ada8524614dc33547634693bc8824951e2a65c25f6f0'],
];
const clientHashes=['eb97d758430643b5c14b01e535a4bc5490b13e7d5437d04b76fe7bb3525d1395','6e0b85a81829493018b501cb1137b5cf667eec841ea56b6921e6ad0875271b96'];
const code=n=>generate(n,{comments:false}).code;
const variables=f=>f.node.body.body.flatMap(n=>n.type==='VariableDeclaration'?n.declarations:[]);
const local=(f,name)=>exactlyOne(variables(f).filter(d=>d.id.name===name),`complete local ${name}`);
const fn=(f,name)=>exactlyOne(f.node.body.body.filter(n=>n.type==='FunctionDeclaration'&&n.id.name===name),`complete helper ${name}`);
const capabilityBindings=`
  const r={c:ports.memoCache},o={useQuery:ports.useQuery},n={useLivestreamApiClient:ports.useLivestreamApiClient},
    s={f:ports.useCoinMetadata},_={f:ports.useSolPrice},t={f:ports.sectionKinds},
    a={O:ports.listingConstants.LIVE_LISTING_LIMIT},l={g:ports.listingConstants.LIVE_CARD_COUNTS},
    h=ports.arraySchemaModule,N=ports.analyticsItemSchema,w=ports.clipItemSchema,
    y={y:ports.analyticsLogger},x={logger:ports.clipLogger},Date=ports.Date;
`;
const validation=`
  for(const name of ['memoCache','useQuery','useLivestreamApiClient','useCoinMetadata','useSolPrice'])
    if(typeof ports?.[name]!=='function')throw new TypeError('required original hook capability: '+name);
  if(typeof ports.arraySchemaModule?.z?.array!=='function'||!ports.analyticsItemSchema||!ports.clipItemSchema||
     typeof ports.analyticsLogger?.error!=='function'||typeof ports.clipLogger?.error!=='function'||
     typeof ports.Date!=='function'||typeof ports.Date.now!=='function'||typeof ports.Date.parse!=='function'||
     typeof ports.Date.prototype?.getTime!=='function'||!ports.sectionKinds||
     !Object.hasOwn(ports.sectionKinds,'TRENDING_CLIPS')||!Object.hasOwn(ports.sectionKinds,'POPULAR_RECORDINGS')||
     !Object.hasOwn(ports.listingConstants??{},'LIVE_LISTING_LIMIT')||!ports.listingConstants?.LIVE_CARD_COUNTS||
     !Object.hasOwn(ports.listingConstants.LIVE_CARD_COUNTS,'large'))
    throw new TypeError('required exact schema, logger, Date, section-kind and existing1821 constant capabilities');
`;
async function origin(corpus,selected){
 const html=await corpus.capture('evidence/web/objects/c45d40b52df03727');assert.equal(html.record.url,'https://pump.fun/live');
 const pushes=[...html.text.matchAll(/<script>self\.__next_f\.push\(([\s\S]*?)\)<\/script>/g)].map(m=>({m,v:JSON.parse(m[1])})).filter(x=>x.v.length===2&&x.v[0]===1&&typeof x.v[1]==='string');
 assert.equal(pushes.length,1);const records=parseFlightRecords(pushes[0].v[1]);assert.equal(records.get('116').value[0],31113);assert.equal(records.get('116').value[2],'LiveHomepage');
 const elements=[];function scan(v,trail=[]){if(!v||typeof v!=='object')return;if(Array.isArray(v)&&v[0]==='$'&&v[1]==='$L116')elements.push({v,trail});for(const[k,c]of Object.entries(v))scan(c,[...trail,k]);}scan(records.get('7f').value);
 assert.equal(elements.length,1);assert.deepEqual(Object.keys(elements[0].v[3]),['initialHeroData','initialSectionData']);
 const scripts=new Set([...html.text.matchAll(/<script\b[^>]*src="([^"]+)"/g)].map(m=>new URL(m[1],html.record.url).href));for(const id of[31113,944001])assert.ok(scripts.has(selected.get(id).provenance.url));
 return{capture:{source:html.record.path,url:html.record.url,sha256:html.record.sha256,bytes:html.record.bytes},importRow:'116',elementRow:'7f',elementPath:elements[0].trail,component:'LiveHomepage',decodedFlightSha256:sha256(pushes[0].v[1]),push:html.witness({start:pushes[0].m.index,end:pushes[0].m.index+pushes[0].m[0].length},'actual main /live Flight context'),limit:'Static main-page context and selected script presence only; not an active registration winner, provider request or mounted application result.'};
}
export async function recover(root=APP_ROOT){
 const corpus=await openCorpus(root),selected=new Map(),factories=[],fragments=[],imports=[];
 for(const[id,hash]of pins){const variants=corpus.index.modules.filter(v=>v.ids.includes(id));assert.equal(variants.length,1,`variants ${id}`);assert.equal(variants[0].origins.length,1,`origins ${id}`);const f=await corpus.factory(id);assert.equal(f.provenance.sha256,hash);selected.set(id,f);factories.push(f.provenance);}
 const clientVariants=corpus.index.modules.filter(v=>v.ids.includes(944410));assert.deepEqual(clientVariants.map(v=>v.sha256).sort(),[...clientHashes].sort());
 for(const variant of clientVariants){assert.equal(variant.origins.length,1);const f=await corpus.factory(944410,{source:variant.origins[0].source});assert.equal(f.provenance.sha256,variant.sha256);factories.push(f.provenance);}
 const f=selected.get(944001),witness=(node,label)=>{const w=f.witness(node,label);fragments.push(w);return w;};
 for(const d of variables(f).filter(d=>d.init?.type==='CallExpression'&&member(d.init.callee,f.runtime,'i'))){assert.equal(d.init.arguments[0].type,'NumericLiteral');imports.push({alias:d.id.name,moduleId:d.init.arguments[0].value,...witness(d,`actual module binding ${d.id.name}`)});}
 const names=['j','I','S','T','L','k','R'],declarations=[];
 for(const name of names){const n=fn(f,name);witness(n,`complete used helper ${name}`);declarations.push(code(n));}
 for(const name of['C','E']){const n=local(f,name);witness(n,`complete clips/VOD ${name}`);declarations.push('let '+code(n)+';');}
 const schemas=['p','v','g','b','w','N'].map(name=>witness(local(f,name),`complete external item-schema declaration ${name}; not executed/copied`));
 const registry=local(f,'z').init;const callers=registry.elements.filter(n=>findNodes(n,c=>c.type==='CallExpression'&&c.callee.type==='Identifier'&&c.callee.name==='E').length);
 assert.equal(callers.length,2);for(const n of callers)witness(n,'actual registry clip section caller; related1897 coordinator');
 const page=selected.get(31113);const pageImports=variables(page).filter(d=>d.init?.type==='CallExpression'&&member(d.init.callee,page.runtime,'i')&&[944001,310766].includes(d.init.arguments[0]?.value));assert.equal(pageImports.length,2);
 const parentEdges=pageImports.map(d=>page.witness(d,'actual main page→section registry/component'));
 const consumer=exactlyOne(findNodes(f.node,n=>n.type==='CallExpression'&&n.callee.type==='Identifier'&&n.callee.name==='o'&&n.arguments[0]?.type==='ObjectExpression'&&n.arguments[0].properties.some(p=>p.key?.name==='initialData')),'actual section useFetch result invocation');parentEdges.push(f.witness(consumer,'actual310766 useFetch→data/loading/page handoff; complete coordinator credited1897'));
 const forwarders=corpus.index.modules.filter(v=>v.ids.includes(866890)).map(v=>({sha256:v.sha256,ids:v.ids,origins:v.origins}));assert.ok(forwarders.length>0);
 const text=`// Editable complete 944001.E main /live clips/VOD query-and-join flow.\n// Captures are parsed only. Actual provider/schema/query runtime capabilities are required.\nexport function createLiveClipsData(ports){\n${validation}${capabilityBindings}${declarations.join('\n')}\nreturn Object.freeze({useClipSection:E});\n}\n`;
 const proof={schemaVersion:1,baseCommit:'094a06f18df738d41e77070c1a009e135671ac1a',anchors:corpus.anchors,origin:await origin(corpus,selected),factories,fragments,imports,schemas,parentEdges,
  arrayRuntime:{moduleId:866890,inventoryForwarders:forwarders,limit:'Shared schema-runtime forwarding registrations are not an active winner or reconstructed runtime; the actual array constructor and both complete item-schema objects are required capabilities.'},
  ports:[['memoCache','445242.c→532815; actual compiler runtime'],['useQuery','690877.useQuery; result/options/scheduling supplied'],['useLivestreamApiClient','944410.useLivestreamApiClient; both physical variants retained, transport/auth/cancellation outside boundary'],['useCoinMetadata','458013.f({mints}); actual hook result supplied'],['useSolPrice','363250.f({}); actual hook result supplied'],['listingConstants','existing1821 API LIVE_LISTING_LIMIT and LIVE_CARD_COUNTS'],['sectionKinds','788501.f'],['arraySchemaModule','866890.z.array'],['analyticsItemSchema','complete source N declaration'],['clipItemSchema','complete source w and p/v/g/b declarations'],['analyticsLogger','254667.y.error'],['clipLogger','54567.logger.error'],['Date','Date-compatible constructor/getTime, static parse/now; each actual sample preserved']],
  moduleSha256:sha256(text),credit:['1570/1617 archive/category/hero metadata attribution, not dependencies','OPEN1821 existing request/normalization/listing constants API, not copied helper operations','OPEN1897 main-page unlock/query coordinator supplies this exact useClipsSection capability; not imported/copied'],
  transformation:['Complete E, C and seven actual helper declarations retain their operations and all10/13/21/12 compiler memo slots.','Only source free-import bindings become explicit capabilities; full item schemas are witnessed and required, not approximated.','No outer query override surface is added; E still destructures only limit and sectionId.','Native intrinsics other than Date remain host JavaScript; Date is required and its separate constructor/parse/now samples are unchanged.'],
  limits:{capturedExecution:false,serviceAcquisition:false,parserReimplementation:false,queryRuntime:false,clientTransportOrAuth:false,mediaOrPlayback:false,accountActions:false,applicationMount:false,nativeCompatibility:false,financialCorrectness:false,featureCredit:false,securityApproval:false}};
 return{text,proof};
}
export async function verify(root=APP_ROOT){const r=await recover(root);assert.equal(await readFile(path.join(root,DIRECTORY,'client.mjs'),'utf8'),r.text,'complete clips/VOD source differs');assert.deepEqual(JSON.parse(await readFile(path.join(root,DIRECTORY,'PROVENANCE.json'),'utf8')),r.proof,'clips/VOD provenance differs');return r.proof;}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){if(process.argv[2]==='--write'){const r=await recover();await mkdir(path.join(APP_ROOT,DIRECTORY),{recursive:true});await writeFile(path.join(APP_ROOT,DIRECTORY,'client.mjs'),r.text);await writeFile(path.join(APP_ROOT,DIRECTORY,'PROVENANCE.json'),JSON.stringify(r.proof,null,2)+'\n');}else{assert.equal(process.argv[2],'--check');await verify();}console.log('Complete main /live clips/VOD source PASS');}
