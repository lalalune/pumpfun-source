import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { generate } from '@babel/generator';
import { openCorpus, findNodes, exactlyOne, member, sha256 } from '../../scripts/original-contracts/source.mjs';
import { parseFlightRecords } from '../../scripts/settings-client-contract.mjs';

export const APP_ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
export const DIRECTORY='reconstruction/live-read-state';
const pins=[
  [31113,'aa72011769a3b4ed93846aa469860c5b661aafea0e98fbf5da8432305f2348c5'],
  [133244,'248fcf72a5bbbd3cb39cd391e161c90c6d496a0828ec3e07c15e7df093aecd97'],
  [859960,'d97c7c9447e248dcaeef4b872bb869c9056d2979cdf53731913116fb8544e429'],
  [944001,'1c56dd013720ae62a9c8ec316ebf1921d9fb13dc436bd75f7eefacdaad40aecb'],
  [788501,'db885fc927427d144544ada8524614dc33547634693bc8824951e2a65c25f6f0'],
  [647145,'e283089e5702f4d45228fbd9d7a68704974e622d4fc930f59ee22fe97d815b83'],
  [79472,'3770c90ff42ca5c74ad69e439814952167bcad231a64ecbd5f0d7d6b9ef782eb'],
  [369731,'fc87a2c85f17569e3f50a0b0bd960e814109550629c9baef4200792008e6d9b3'],
];
const specs=[
  {id:788501,name:'buildKinds',groups:[788501]},
  {id:859960,name:'buildQueries',locals:['n','w','N','E'],functions:[],importIds:[445242,761459,690877,133244,369091,358893],
    extra:'const {fetchCoins:y,fetchSection:j,nextLivePage:S,selectLivePages:k,livePageIdentity:P,LIVE_SORTS:o}=listing;',
    exports:{859960:['A','L','N'],606706:['O','B','o','R'],539335:['f']}},
  {id:133244,name:'buildHero',locals:['o','m'],extra:'const d=projectHeroCoin;',groups:[133244]},
  {id:944001,name:'buildSections',locals:['z','P','K'],functions:[],importIds:[788501,859960,445242,539335,732486,157633,426091,458310,352386,398902,647145,314982],
    extra:'const E=useClipsSection;',groups:[944001,310766]},
  {id:31113,name:'buildHomepage',locals:['u'],functions:['k'],importIds:[732486,445242,599077,352386,133244,944001,310766,314982,79472,327294],
    extra:'const f=FloatingControl; const {IntersectionObserver}=dom;',groups:[31113]},
];
const code=(n)=>generate(n,{comments:false}).code;
const variables=(f)=>f.node.body.body.flatMap((n)=>n.type==='VariableDeclaration'?n.declarations:[]);
const imported=(f,d)=>d.init?.type==='CallExpression'&&member(d.init.callee,f.runtime,'i');
function exportsOf(f,id){
  const call=exactlyOne(findNodes(f.node,(n)=>n.type==='CallExpression'&&member(n.callee,f.runtime,'s')&&
    (n.arguments[1]?.value===id||!n.arguments[1]&&f.ids.length===1&&f.id===id)),`actual ${id} exports`);
  const a=call.arguments[0].elements,out=[];
  for(let i=0;i<a.length;){assert.equal(a[i].type,'StringLiteral');const name=a[i++].value;
    if(a[i]?.type==='NumericLiteral'){assert.equal(a[i++].value,0);out.push({name,value:a[i++]});}
    else{const getter=a[i++];assert.equal(getter.type,'ArrowFunctionExpression');assert.equal(getter.params.length,0);assert.notEqual(getter.body.type,'BlockStatement');out.push({name,value:getter.body});}}
  return out;
}
const resolve=(f,n)=>n.type==='Identifier'?exactlyOne(variables(f).filter(d=>d.id.name===n.name),`binding ${n.name}`).init:n;
function getExport(f,id,name){return resolve(f,exactlyOne(exportsOf(f,id).filter(e=>e.name===name),`${id}.${name}`).value);}

const adapter=`
// Authored construction only. Runtime/query/provider scheduling remains external.
export function createLiveReadState({React,jsx,compiler,modules,listing,projectHeroCoin,useClipsSection,FloatingControl,dom}){
  for(const key of ['fetchCoins','fetchSection','nextLivePage','selectLivePages','livePageIdentity'])
    if(typeof listing?.[key]!=='function')throw new TypeError('explicit1821 listing operation required: '+key);
  if(!listing.LIVE_SORTS||!listing.LIVE_CARD_COUNTS||typeof projectHeroCoin!=='function'||typeof useClipsSection!=='function'||
    !React||typeof jsx?.jsx!=='function'||typeof compiler?.c!=='function'||!modules||!FloatingControl||typeof dom?.IntersectionObserver!=='function')
    throw new TypeError('explicit original read-state/render/query/provider/DOM capabilities are required');
  const owned=new Map([[352386,React],[732486,jsx],[445242,compiler],
    [133244,{E:6,g:projectHeroCoin}], [647145,{g:listing.LIVE_CARD_COUNTS,X:modules[647145]?.X}]]);
  const imports=(id)=>{if(owned.has(id))return owned.get(id);if(!Object.hasOwn(modules,id))throw new TypeError('missing original module capability '+id);return modules[id];};
  for(const build of [buildKinds,buildQueries,buildHero,buildSections,buildHomepage])
    for(const[id,value]of Object.entries(build(imports,listing,projectHeroCoin,useClipsSection,FloatingControl,dom))){
      if(owned.has(Number(id)))Object.assign(owned.get(Number(id)),value);else owned.set(Number(id),value);}
  return Object.freeze({LiveHomepage:owned.get(31113).LiveHomepage,Hero:owned.get(133244)._,
    useHero:owned.get(859960).L,useSection:owned.get(859960).N,Section:owned.get(310766).Z,
    sections:owned.get(944001).Z,sectionById:owned.get(944001).A});
}
`;

async function origin(corpus,selected){
  const html=await corpus.capture('evidence/web/objects/c45d40b52df03727');assert.equal(html.record.url,'https://pump.fun/live');
  const pushes=[...html.text.matchAll(/<script>self\.__next_f\.push\(([\s\S]*?)\)<\/script>/g)].map(m=>({m,v:JSON.parse(m[1])})).filter(x=>x.v.length===2&&x.v[0]===1&&typeof x.v[1]==='string');
  assert.equal(pushes.length,1);const records=parseFlightRecords(pushes[0].v[1]);assert.equal(records.get('116').value[0],31113);assert.equal(records.get('116').value[2],'LiveHomepage');
  const elements=[];function scan(v,trail=[]){if(!v||typeof v!=='object')return;if(Array.isArray(v)&&v[0]==='$'&&v[1]==='$L116')elements.push({v,trail});for(const[k,c]of Object.entries(v))scan(c,[...trail,k]);}
  scan(records.get('7f').value);assert.equal(elements.length,1);assert.deepEqual(Object.keys(elements[0].v[3]),['initialHeroData','initialSectionData']);
  const scripts=new Set([...html.text.matchAll(/<script\b[^>]*src="([^"]+)"/g)].map(m=>new URL(m[1],html.record.url).href));
  for(const id of [31113,133244,859960,944001])assert.ok(scripts.has(selected.get(id).provenance.url));
  return{capture:{source:html.record.path,url:html.record.url,sha256:html.record.sha256,bytes:html.record.bytes},
    importRow:'116',elementRow:'7f',elementPath:elements[0].trail,component:'LiveHomepage',decodedFlightSha256:sha256(pushes[0].v[1]),
    push:html.witness({start:pushes[0].m.index,end:pushes[0].m.index+pushes[0].m[0].length},'actual /live Flight context'),
    limit:'Observed HTML and static parent chain only; no query/provider execution, current data or global active registration winner.'};
}
export async function recover(root=APP_ROOT){
  const corpus=await openCorpus(root),selected=new Map(),factories=[],fragments=[],imports=[],blocks=[];
  for(const[id,hash]of pins){const variants=corpus.index.modules.filter(m=>m.ids.includes(id));assert.equal(variants.length,1,`physical variants ${id}`);assert.equal(variants[0].origins.length,1);
    const f=await corpus.factory(id);assert.equal(f.provenance.sha256,hash);selected.set(id,f);factories.push(f.provenance);}
  const witness=(f,n,label)=>{const w=f.witness(n,label);fragments.push(w);return w;};
  for(const spec of specs){const f=selected.get(spec.id),lines=[];
    for(const d of variables(f).filter(d=>imported(f,d)&&(!spec.importIds||spec.importIds.includes(d.init.arguments[0].value)))){
      assert.equal(d.init.arguments[0].type,'NumericLiteral');const id=d.init.arguments[0].value;imports.push({factory:spec.id,alias:d.id.name,moduleId:id,...witness(f,d,`actual import ${spec.id}→${id}`)});lines.push(`var ${d.id.name}=imports(${id});`);}
    if(spec.extra)lines.push(spec.extra);
    for(const statement of f.node.body.body){if(statement.type==='VariableDeclaration'){
      const declarations=statement.declarations.filter(d=>!imported(f,d)&&(!spec.locals||spec.locals.includes(d.id.name)));if(!declarations.length)continue;
      for(const d of declarations)witness(f,d,`complete used ${spec.id} local ${d.id.name}`);lines.push(code({...statement,declarations}));
    }else if(statement.type==='FunctionDeclaration'&&(!spec.functions||spec.functions.includes(statement.id.name))){witness(f,statement,`complete used ${spec.id} function ${statement.id.name}`);lines.push(code(statement));}}
    const ids=spec.groups??Object.keys(spec.exports).map(Number),returns=[];
    for(const id of ids){const entries=exportsOf(f,id).filter(e=>!spec.exports||spec.exports[id].includes(e.name));
      for(const e of entries)witness(f,e.value,`complete selected ${id}.${e.name} export`);
      returns.push(`${id}:{${entries.map(e=>JSON.stringify(e.name)+':'+code(e.value)).join(',')}}`);}
    blocks.push(`function ${spec.name}(imports,listing,projectHeroCoin,useClipsSection,FloatingControl,dom){\n${lines.join('\n')}\nreturn {${returns.join(',')}};\n}`);
  }
  const query=selected.get(859960),hero=selected.get(133244),sections=selected.get(944001),page=selected.get(31113);
  const listingLinks=[];
  for(const[sourceName,api]of [['y','fetchCoins'],['j','fetchSection'],['S','nextLivePage'],['k','selectLivePages'],['P','livePageIdentity'],['o','LIVE_SORTS']]){
    const n=exactlyOne([...variables(query),...query.node.body.body.filter(n=>n.type==='FunctionDeclaration')].filter(d=>d.id.name===sourceName),`actual1821 callee ${sourceName}`);
    listingLinks.push({sourceName,api,source:query.witness(n,`credited OPEN1821 actual ${api}`)});}
  const external=[
    {operation:'projectHeroCoin',source:hero.witness(getExport(hero,133244,'g'),'actual133244.g projector; related1617 attribution')},
    {operation:'useClipsSection',source:sections.witness(exactlyOne(variables(sections).filter(d=>d.id.name==='E'),'actual clip result hook').init,'actual clips/VOD hook port; not implemented')},
    {operation:'FloatingControl',source:page.witness(exactlyOne(variables(page).filter(d=>d.id.name==='f'),'actual floating control').init,'actual account CTA port; not implemented')},
    {operation:'isLiveBlocked',source:selected.get(79472).witness(getExport(selected.get(79472),79472,'V'),'actual geographic/disabled-feature snapshot port; not implemented')},
    {operation:'HeroCarousel',source:selected.get(369731).witness(getExport(selected.get(369731),369731,'HeroCarousel'),'actual outer hero port; OPEN1879 credited, not copied')},
  ];
  const text=`// Editable complete main /live query/unlock/read-state components.\n// Original captures are parsed only; service/player/provider bodies stay ports.\n${blocks.join('\n\n')}\n${adapter}`;
  const proof={schemaVersion:1,baseCommit:'094a06f18df738d41e77070c1a009e135671ac1a',anchors:corpus.anchors,origin:await origin(corpus,selected),factories,fragments,imports,listingLinks,external,
    moduleSha256:sha256(text),credit:['OPEN1821 request/normalization/pager/result/section predicates; no new operation credit','OPEN1879 outer hero/preview components; explicit port, not imported/copied','OPEN1570/1617 archive/category/hero metadata work'],
    transformation:['complete selected declarations, effects, callbacks and compiler memo caches unchanged','module imports/exports become explicit supplied module values/returned objects','actual1821 helper/request pointers bound by their existing exact API names','actual clips/account/projector pointers supplied explicitly','IntersectionObserver binds supplied DOM capability; no scheduling emulation'],
    limits:{capturedExecution:false,liveAcquisition:false,providerQueryRuntime:false,clipsOrMediaService:false,geoAvailability:false,accountActions:false,appMount:false,visualOrNativeParity:false,featureCredit:false,securityApproval:false}};
  return{text,proof};
}
export async function verify(root=APP_ROOT){const r=await recover(root);assert.equal(await readFile(path.join(root,DIRECTORY,'client.mjs'),'utf8'),r.text,'complete Live read-state source differs');
  assert.deepEqual(JSON.parse(await readFile(path.join(root,DIRECTORY,'PROVENANCE.json'),'utf8')),r.proof,'Live read-state provenance differs');return r.proof;}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  if(process.argv[2]==='--write'){const r=await recover();await mkdir(path.join(APP_ROOT,DIRECTORY),{recursive:true});await writeFile(path.join(APP_ROOT,DIRECTORY,'client.mjs'),r.text);await writeFile(path.join(APP_ROOT,DIRECTORY,'PROVENANCE.json'),JSON.stringify(r.proof,null,2)+'\n');}
  else{assert.equal(process.argv[2],'--check');await verify();}console.log('Main /live complete read-state source PASS');
}
