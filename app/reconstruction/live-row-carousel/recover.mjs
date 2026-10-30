import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {generate} from '@babel/generator';
import {openCorpus,findNodes,exactlyOne,member,sha256} from '../../scripts/original-contracts/source.mjs';
import {parseFlightRecords} from '../../scripts/settings-client-contract.mjs';
export const APP_ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..'),DIRECTORY='reconstruction/live-row-carousel';
const pins=[
 [1074,'a4a67a1e86f324e07452dba9f3da2f879f115cd2d3bc4065780ef56c06515c30'],
 [798394,'e575a7a694ecf784c0719f294ce12dc3e26802bb533fc5cdce704afd1e664945'],
 [647145,'e283089e5702f4d45228fbd9d7a68704974e622d4fc930f59ee22fe97d815b83'],
 [763145,'d6c5fb78571198cbdce125397e28ac5a9cda6f2fa2b71dca1836de1e13821064'],
 [944001,'1c56dd013720ae62a9c8ec316ebf1921d9fb13dc436bd75f7eefacdaad40aecb'],
 [31113,'aa72011769a3b4ed93846aa469860c5b661aafea0e98fbf5da8432305f2348c5'],
 [445242,'2d7f3e592645b5e2d997e444ee9b10be6dc8c357680552dccddafb63e4887576'],
 [532815,'30e0e70b96ec8bc14a84e8ebab1dc7a376f543667300fa43b118f00c3199ae9a'],
];
const code=n=>generate(n,{comments:false}).code;
const variables=f=>f.node.body.body.flatMap(n=>n.type==='VariableDeclaration'?n.declarations:[]);
function exportsOf(f,id){const call=exactlyOne(findNodes(f.node,n=>n.type==='CallExpression'&&member(n.callee,f.runtime,'s')&&n.arguments[1]?.value===id),`actual ${id} export group`),a=call.arguments[0].elements,out=[];for(let i=0;i<a.length;){assert.equal(a[i].type,'StringLiteral');const name=a[i++].value;if(a[i]?.type==='NumericLiteral'){assert.equal(a[i++].value,0);out.push({name,value:a[i++]});}else{const g=a[i++];assert.equal(g.type,'ArrowFunctionExpression');assert.equal(g.params.length,0);assert.notEqual(g.body.type,'BlockStatement');out.push({name,value:g.body});}}return out;}
const getExport=(f,id,name)=>exactlyOne(exportsOf(f,id).filter(e=>e.name===name),`export ${id}.${name}`).value;
const spec=[{id:798394,name:'buildGeometry',locals:[],functions:[],imports:[445242,352386],groups:{798394:['f'],70678:['f'],65769:['f']}},
 {id:1074,name:'buildCarousel',locals:['s','a'],functions:[],imports:[732486,426091,352386,445242,798394,70678,65769],groups:{502540:['f'],1074:['Carousel']}},
 {id:647145,name:'buildRows',locals:[],functions:['a'],imports:[732486,445242,763145,1074],extra:'const l=cardCounts;',groups:{647145:['X']}}];
const adapter=`
// Authored construction: actual React/JSX/compiler/classnames/Card/DOM implementations remain capabilities.
export function createLiveRowCarousel({React,jsx,compiler,classNames,Card,cardCounts,dom}){
 if(typeof React?.useEffect!=='function'||typeof jsx?.jsx!=='function'||typeof jsx?.jsxs!=='function'||typeof compiler?.c!=='function'||typeof classNames!=='function'||typeof Card!=='function'||!cardCounts||
    !['extraSmall','small','large'].every(k=>Object.hasOwn(cardCounts,k))||!['IntersectionObserver','ResizeObserver','MutationObserver'].every(k=>typeof dom?.[k]==='function'))
   throw new TypeError('actual React/JSX/compiler/classnames/Card/count and DOM capabilities are required');
 const owned=new Map([[352386,React],[732486,jsx],[445242,compiler],[426091,{c:classNames}],[763145,{Card}]]);
 const imports=id=>{if(!owned.has(id))throw new TypeError('missing actual carousel import '+id);return owned.get(id);};
 for(const build of[buildGeometry,buildCarousel,buildRows])for(const[id,value]of Object.entries(build(imports,dom,cardCounts)))owned.set(Number(id),value);
 return Object.freeze({Rows:owned.get(647145).X,Carousel:owned.get(1074).Carousel,cardWidths:owned.get(502540).f,
   useGeometry:owned.get(798394).f,useSelection:owned.get(70678).f,useSnap:owned.get(65769).f});
}
`;
async function origin(corpus,selected){const html=await corpus.capture('evidence/web/objects/c45d40b52df03727');assert.equal(html.record.url,'https://pump.fun/live');const pushes=[...html.text.matchAll(/<script>self\.__next_f\.push\(([\s\S]*?)\)<\/script>/g)].map(m=>({m,v:JSON.parse(m[1])})).filter(x=>x.v.length===2&&x.v[0]===1&&typeof x.v[1]==='string');assert.equal(pushes.length,1);const records=parseFlightRecords(pushes[0].v[1]);assert.equal(records.get('116').value[0],31113);assert.equal(records.get('116').value[2],'LiveHomepage');let count=0;function scan(v){if(!v||typeof v!=='object')return;if(Array.isArray(v)&&v[0]==='$'&&v[1]==='$L116')count++;for(const c of Object.values(v))scan(c);}scan(records.get('7f').value);assert.equal(count,1);const scripts=new Set([...html.text.matchAll(/<script\b[^>]*src="([^"]+)"/g)].map(m=>new URL(m[1],html.record.url).href));for(const id of[31113,944001,647145,1074,798394])assert.ok(scripts.has(selected.get(id).provenance.url));return{source:html.record.path,url:html.record.url,sha256:html.record.sha256,bytes:html.record.bytes,importRow:'116',elementRow:'7f',decodedFlightSha256:sha256(pushes[0].v[1]),push:html.witness({start:pushes[0].m.index,end:pushes[0].m.index+pushes[0].m[0].length},'actual main /live Flight context'),limit:'Observed static main-page chain and initial-script presence; no active registration winner, original UI execution or current availability.'};}
export async function recover(root=APP_ROOT){const corpus=await openCorpus(root),selected=new Map(),factories=[],fragments=[],imports=[],blocks=[];
 for(const[id,hash]of pins){const variants=corpus.index.modules.filter(v=>v.ids.includes(id));assert.equal(variants.length,1);assert.equal(variants[0].origins.length,1);const f=await corpus.factory(id);assert.equal(f.provenance.sha256,hash);selected.set(id,f);factories.push(f.provenance);}
 const witness=(f,n,label)=>{const w=f.witness(n,label);fragments.push(w);return w;};
 for(const s of spec){const f=selected.get(s.id),lines=['const {IntersectionObserver,ResizeObserver,MutationObserver}=dom;'];
  for(const d of variables(f).filter(d=>d.init?.type==='CallExpression'&&member(d.init.callee,f.runtime,'i')&&s.imports.includes(d.init.arguments[0]?.value))){const id=d.init.arguments[0].value;imports.push({factory:s.id,alias:d.id.name,moduleId:id,...witness(f,d,`actual import ${s.id}→${id}`)});lines.push(`var ${d.id.name}=imports(${id});`);}
  if(s.extra)lines.push(s.extra);
  for(const name of s.locals){const d=exactlyOne(variables(f).filter(d=>d.id.name===name),`used local ${name}`);witness(f,d,`complete used ${s.id} local ${name}`);lines.push('let '+code(d)+';');}
  for(const name of s.functions){const n=exactlyOne(f.node.body.body.filter(n=>n.type==='FunctionDeclaration'&&n.id.name===name),`complete ${name}`);witness(f,n,`complete used ${s.id} function ${name}`);lines.push(code(n));}
  const returns=[];for(const[id,names]of Object.entries(s.groups)){const e=names.map(name=>{const n=getExport(f,Number(id),name);witness(f,n,`complete selected ${id}.${name}`);return JSON.stringify(name)+':'+code(n);});returns.push(id+':{'+e.join(',')+'}');}
  blocks.push(`function ${s.name}(imports,dom,cardCounts){\n${lines.join('\n')}\nreturn{${returns.join(',')}};\n}`);
 }
 const sections=selected.get(944001),rows=selected.get(647145),widths=selected.get(1074),page=selected.get(31113);
 const parentEdges=[];for(const[id,ids]of[[31113,[944001,310766]],[944001,[647145]],[647145,[1074,763145]]]){const f=selected.get(id);for(const d of variables(f).filter(d=>d.init?.type==='CallExpression'&&member(d.init.callee,f.runtime,'i')&&ids.includes(d.init.arguments[0]?.value)))parentEdges.push(f.witness(d,`actual parent import ${id}→${d.init.arguments[0].value}`));}
 const rowCall=exactlyOne(findNodes(sections.node,n=>n.type==='CallExpression'&&n.callee.type==='SequenceExpression'&&member(n.callee.expressions.at(-1),'M','jsx')&&n.arguments[0]?.type==='MemberExpression'&&member(n.arguments[0],'l','X')),'actual section row handoff');parentEdges.push(sections.witness(rowCall,'actual310766 full row props and near-end handoff; credited1897'));
 const count=exactlyOne(variables(rows).filter(d=>d.id.name==='l'),'actual shared card counts');witness(rows,count,'existing1821 shared card-count values; supplied, not newly recovered');
 const text='// Editable complete main /live row carousel, geometry, selection and snap flow.\n// Captures are parsed only; actual Card and provider/navigation behavior are excluded.\n'+blocks.join('\n\n')+'\n'+adapter;
 const proof={schemaVersion:1,baseCommit:'094a06f18df738d41e77070c1a009e135671ac1a',anchors:corpus.anchors,origin:await origin(corpus,selected),factories,fragments,imports,parentEdges,cardPort:selected.get(763145).provenance,moduleSha256:sha256(text),ports:{React:'352386',jsx:'732486',compiler:'445242.c→532815',classNames:'426091.c',Card:'complete763145.Card source; presentation/navigation/providers remain outside',cardCounts:'existing1821 LIVE_CARD_COUNTS API; actual647145.g witnessed',dom:'actual IntersectionObserver, ResizeObserver, MutationObserver; captured globals bound explicitly'},credit:['OPEN1897 actual main/section query/unlock and near-end consumer; not copied','OPEN1879 distinct hero carousel, not this row Carousel','OPEN1821 existing shared card counts and listing operations; no duplicate helper/count credit','1570/1617 archive/main-page metadata attribution'],transformation:['Complete used locals, helpers and export expressions retain all operations/callbacks/effect dependencies/ref lifetimes/cleanup.','Only module imports/exports and three DOM global constructors become explicit supplied bindings.','Existing shared card-count literal is witnessed but supplied by its existing API, not copied.','No Card/provider/navigation body, generic classnames library or React/query implementation is reconstructed.'],limits:{capturedExecution:false,providerAcquisition:false,cardOrCoinPage:false,accountActions:false,mediaOrPlayback:false,applicationMount:false,originalCSSOrVisualParity:false,nativeCompatibility:false,featureCredit:false,securityApproval:false}};
 return{text,proof};}
export async function verify(root=APP_ROOT){const r=await recover(root);assert.equal(await readFile(path.join(root,DIRECTORY,'client.mjs'),'utf8'),r.text,'complete row carousel source differs');assert.deepEqual(JSON.parse(await readFile(path.join(root,DIRECTORY,'PROVENANCE.json'),'utf8')),r.proof,'row carousel provenance differs');return r.proof;}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){if(process.argv[2]==='--write'){const r=await recover();await mkdir(path.join(APP_ROOT,DIRECTORY),{recursive:true});await writeFile(path.join(APP_ROOT,DIRECTORY,'client.mjs'),r.text);await writeFile(path.join(APP_ROOT,DIRECTORY,'PROVENANCE.json'),JSON.stringify(r.proof,null,2)+'\n');}else{assert.equal(process.argv[2],'--check');await verify();}console.log('Complete main /live row carousel source PASS');}
