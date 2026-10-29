import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import prettier from 'prettier';
import { openCorpus, findNodes, exactlyOne, member, propertyName, sha256 } from '../../scripts/original-contracts/source.mjs';
import { verifySession } from '../../scripts/verify-search-session.mjs';
export const APP_ROOT = fileURLToPath(new URL('../..', import.meta.url));
export const DIRECTORY = 'reconstruction/avatar-workflow';
const PINS = {
  705313: ['d20ae1800486b11692b11f5a2172e262d6e11c84a1c8912eaa73b615d8d058b9'],
  367498: ['6edb8b08b4979a964468e3ddf338d9ebad66e68259310abd1b5c0b3ee1c2a5d1'],
  747337: ['448b95f7f1d0ef46b86e4c5d4f32b0b39892386637cf47fe086a728e158aaa2b','8b19b763747c211bcafe1a6d5f553bc08dfae3373a943a8cd54b62acd4e771e0'],
  426091: ['93b70fac45ba969c312e0f7ec965b181d06a8332f7e1a4bba6751a63fd5555a4'],
  204478: ['27cc0223b79ff95cac02f490600cc4de894dee66af739beca525502c424dae3f'],
};
const declarations = (f) => f.node.body.body.flatMap(n => n.type === 'VariableDeclaration' ? n.declarations : []);
function declaration(f, name) { return exactlyOne(declarations(f).filter(n=>n.id.name===name), 'top binding '+name); }
function exported(f,id,name) {
  const call = exactlyOne(findNodes(f.node,n=>n.type==='CallExpression' && member(n.callee,f.runtime,'s') &&
    (id===747337 || n.arguments[1]?.value===id) && n.arguments[0]?.type==='ArrayExpression' && n.arguments[0].elements.some(x=>x?.value===name)), 'actual qualified export '+id+'.'+name);
  const a=call.arguments[0].elements, at=a.findIndex(n=>n?.value===name); assert.equal(a[at+1].value,0);
  return { call, node:a[at+2] };
}
function importBinding(f, alias, id) {
  const d=declaration(f,alias); assert.ok(member(d.init?.callee,f.runtime,'i')); assert.equal(d.init.arguments.length,1); assert.equal(d.init.arguments[0].value,id); return d;
}
// Explicit bijective identifier spelling correspondence for the two URI variants.
// No operation/branch/optional/computed access, property, statement or literal is removed.
export function canonicalUri(node, aliases={}) {
  assert.equal(new Set(Object.values(aliases)).size,Object.keys(aliases).length,'URI spelling map must be bijective');
  function visit(value,parent,key) {
    if(Array.isArray(value)) return value.map(n=>visit(n,parent,key));
    if(!value || typeof value!=='object') return value;
    if(value.type==='Identifier') {
      const property = (key==='key' && parent?.type==='ObjectProperty' && !parent.computed) ||
        (key==='property' && ['MemberExpression','OptionalMemberExpression'].includes(parent?.type) && !parent.computed);
      return {type:'Identifier',name:property ? value.name : aliases[value.name]??value.name};
    }
    return Object.fromEntries(Object.entries(value).filter(([k])=>!['loc','start','end','extra','leadingComments','trailingComments','innerComments'].includes(k))
      .map(([k,v])=>[k,k==='shorthand' && value.type==='ObjectProperty' ? false : visit(v,value,k)]));
  }
  return visit(node);
}
export async function recover(root=APP_ROOT) {
  const corpus=await openCorpus(root), selected={}, contexts=[];
  for(const [key,hashes] of Object.entries(PINS)) {
    const id=Number(key), rows=corpus.index.modules.filter(m=>m.ids.includes(id));
    assert.deepEqual(rows.map(r=>r.sha256).sort(),[...hashes].sort(),'all physical variants '+id);
    selected[id]=[];
    for(const hash of hashes) { const row=exactlyOne(rows.filter(r=>r.sha256===hash),'pinned variant');
      for(const origin of row.origins) {const f=await corpus.factory(id,{source:origin.source}); selected[id].push(f); contexts.push(f.provenance); }
    }
  }
  assert.equal(contexts.length,6,'all selected physical contexts');
  const owner=selected[705313][0], assets=selected[367498][0], uri=selected[747337][0], otherUri=selected[747337][1], caller=selected[204478][0];
  const witnesses=[], witness=(f,n,label)=>{const w=f.witness(n,label);witnesses.push(w);return w;};
  for(const [alias,id] of Object.entries({r:732486,s:445242,t:426091,o:352386,a:367498,i:350606}))
    witness(owner,importBinding(owner,alias,id),'actual Avatar provider '+id);
  for(const [alias,id] of Object.entries({a:426091,n:747337}))witness(assets,importBinding(assets,alias,id),'used asset provider '+id);
  const supplied=exactlyOne(owner.node.body.body.filter(n=>n.type==='FunctionDeclaration' && n.id.name==='n'),'complete supplied-image owner');
  const layered=exactlyOne(owner.node.body.body.filter(n=>n.type==='FunctionDeclaration' && n.id.name==='c'),'complete layered-image owner');
  const dispatch=exported(owner,705313,'f');
  for(const [n,slots,label] of [[supplied,30,'supplied image failure/reset owner'],[layered,34,'deterministic layered owner'],[dispatch.node,13,'Avatar dispatcher']]) {
    assert.equal(findNodes(n,x=>x.type==='CallExpression' && x.callee.type==='SequenceExpression' && member(x.callee.expressions[1],'s','c') && x.arguments[0]?.value===slots).length,1);
    witness(owner,n,'complete '+slots+'-slot '+label);
  }
  witness(owner,dispatch.call,'actual Avatar public export registration');
  // This is a positive bundled export, not an absent standalone350606 file.
  const seed=exported(assets,350606,'f'); assert.ok(assets.ids.includes(350606)); witness(assets,seed.call,'bundled350606.f registration in actual367498 factory');
  const seedHelpers=assets.node.body.body.filter(n=>n.type==='FunctionDeclaration' && ['r','s'].includes(n.id.name)); assert.equal(seedHelpers.length,2);
  const seedConstants=['t','o'].map(n=>declaration(assets,n));
  for(const n of [...seedHelpers,...seedConstants,seed.node])witness(assets,n,'complete deterministic catalog/seed closure');
  const imageHelpers=['i','c','d','l','u','y','f'].map(n=>declaration(assets,n));
  const imageExports=['D','p','k'].map(name=>[name,exported(assets,367498,name).node]);
  for(const n of [...imageHelpers,...imageExports.map(([,n])=>n)])witness(assets,n,'complete used367498 D/p/k dependency');
  const uriParts=f=>[...declarations(f),...['T','N','F'].map(name=>exported(f,747337,name).node)];
  const first=uriParts(uri),second=uriParts(otherUri);
  assert.deepEqual(canonicalUri(first,{r:'t',s:'n',t:'r',o:'i',e:'e',a:'a',n:'o',i:'s'}),canonicalUri(second),'all used URI closure operations in both variants');
  for(const f of [uri,otherUri])for(const n of uriParts(f))witness(f,n,'complete used747337 URI variant closure');
  // Accepted426091 normalizer and fallback retain their existing implementation/credit.
  const accepted=await verifySession(root);
  for(const name of ['r','A'])witness(selected[426091][0],exported(selected[426091][0],426091,name).node,'credited accepted426091.'+name);
  const use=importBinding(caller,'r',705313);witness(caller,use,'actual reply/composer Avatar dependency');
  const boundNames=n=>!n?[]:n.type==='Identifier'?[n.name]:n.type==='RestElement'?boundNames(n.argument):n.type==='AssignmentPattern'?boundNames(n.left):n.type==='ObjectPattern'?n.properties.flatMap(p=>boundNames(p.type==='RestElement'?p.argument:p.value)):n.type==='ArrayPattern'?n.elements.flatMap(boundNames):[];
  const calls=findNodes(caller.node,(n,parents)=>{
    if(!(n.type==='CallExpression' && member(n.arguments[0],'r','f') && n.arguments[1]?.type==='ObjectExpression'))return false;
    assert.ok(n.callee.type==='SequenceExpression' && n.callee.expressions[0]?.value===0 && member(n.callee.expressions[1],'t','jsx'),'actual JSX invocation');
    for(const parent of parents){
      if(parent===caller.node||parent===caller.node.body)continue;
      if(['FunctionDeclaration','FunctionExpression','ArrowFunctionExpression'].includes(parent.type))assert.ok(!parent.params.flatMap(boundNames).includes('r'),'Avatar import must not be parameter-shadowed');
      if(parent.type==='BlockStatement')for(const statement of parent.body)if(statement.type==='VariableDeclaration')assert.ok(!statement.declarations.flatMap(d=>boundNames(d.id)).includes('r'),'Avatar import must not be locally shadowed');
    }return true;
  });
  assert.equal(calls.length,5,'all actual reply/composer/callout handoffs');
  for(const n of calls)witness(caller,n,'actual Avatar invocation with full props descriptor');
  const uriText=`(()=>{let ${declarations(uri).map(n=>uri.text(n)).join(',')};return {${['T','N','F'].map(name=>name+':'+uri.text(exported(uri,747337,name).node)).join(',')}};})()`;
  const seedText=`(()=>{${seedHelpers.map(n=>assets.text(n)).join('\n')}var ${seedConstants.map(n=>assets.text(n)).join(',')};return ${assets.text(seed.node)};})()`;
  const imageText=`(()=>{const a={r:normalizeSearchUri,A:FALLBACK_IMAGE},n=uri;let ${imageHelpers.map(n=>assets.text(n)).join(',')};return {${imageExports.map(([name,n])=>name+':'+assets.text(n)).join(',')}};})()`;
  const text=await prettier.format(`
import { normalizeSearchUri,FALLBACK_IMAGE } from '../search-session/session.mjs';
// Complete used asset closure; URI construction is not remote asset acquisition.
const uri=${uriText};
const generate=${seedText};
const image=${imageText};
export const avatarAssets={generate,normalizeSource:image.D,sizeSource:image.p,sizeLayers:image.k};
export { FALLBACK_IMAGE };
// Construct once using the caller's actual JSX/compiler/React/class interfaces.
export function createAvatarWorkflow({jsx,useMemoCache,React,classNames}){
 for(const [name,value] of Object.entries({jsx,useMemoCache,classNames}))if(typeof value!=='function')throw new TypeError('Explicit Avatar capability required: '+name);
 for(const name of ['useState','useEffect'])if(typeof React?.[name]!=='function')throw new TypeError('Explicit Avatar React hook required: '+name);
 const r={jsx},s={c:useMemoCache},t={A:FALLBACK_IMAGE,c:classNames},o={useState:React.useState,useEffect:React.useEffect},a={D:image.D,p:image.p,k:image.k},i={f:generate};
 ${owner.text(supplied)}
 ${owner.text(layered)}
 return ${owner.text(dispatch.node)};
}
`,{parser:'babel'});
  return {text,provenance:{schemaVersion:1,baseCommit:'094a06f18df738d41e77070c1a009e135671ac1a',anchors:corpus.anchors,
    scope:'Complete705313.f dispatch and both owning React frames with complete used350606/367498/747337 asset closure; explicit host capabilities; no product mount',
    contexts,witnesses,uriComparison:{kind:'Complete AST with explicit bijective identifier spelling correspondence; parser metadata/comment/raw-literal spelling excluded only',mapping:{r:'t',s:'n',t:'r',o:'i',e:'e',a:'a',n:'o',i:'s'},sha256:sha256(JSON.stringify(canonicalUri(second)))},
    credited:{normalizer:'Accepted search-session.normalizeSearchUri/FALLBACK_IMAGE are reused, not newly recovered;426091.c class join remains an explicit capability',acceptedAdapterSha256:accepted.adapterSha256,
      competition:'Open1296/1315/1380 use an explicit compatible Avatar port; their components/proofs are not copied or newly credited'},
    moduleSha256:sha256(Buffer.from(text)),ports:{React:'actual352386 useState/useEffect',compiler:'actual445242.c memo cache',rendering:'actual732486 jsx and426091.c class join'},
    limits:['Captured factories remain inert; only generated editable functions execute','Caller props/schema/identity/ownership/authentication and image-service acquisition/availability remain external','No CDN pixels, original visual/provider/React equivalence, product/native/API/security qualification or feature-count claim']}};
}
export async function verify(root=APP_ROOT) {
 const r=await recover(root);
 assert.equal(await readFile(path.join(root,DIRECTORY,'client.mjs'),'utf8'),r.text,'Avatar editable source differs');
 assert.equal(await readFile(path.join(root,DIRECTORY,'PROVENANCE.json'),'utf8'),JSON.stringify(r.provenance,null,2)+'\n','Avatar provenance differs');return r.provenance;
}
if(process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
 assert.ok(process.argv.length===3 && ['--write','--check'].includes(process.argv[2]),'Use --write|--check');
 if(process.argv[2]==='--write'){const r=await recover();await mkdir(path.join(APP_ROOT,DIRECTORY),{recursive:true});await writeFile(path.join(APP_ROOT,DIRECTORY,'client.mjs'),r.text);await writeFile(path.join(APP_ROOT,DIRECTORY,'PROVENANCE.json'),JSON.stringify(r.provenance,null,2)+'\n');}else await verify();
 console.log('PASS complete Avatar13/30/34-slot owners, bundled deterministic assets, both URI variants and5actual handoffs');
}
