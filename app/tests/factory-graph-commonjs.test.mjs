import assert from 'node:assert/strict';
import {mkdtemp,mkdir,readFile,writeFile,copyFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,dirname,resolve} from 'node:path';
import test from 'node:test';
import {analyzeFactory,buildGraph,publishGraph,verifyGraph,countSourceLines} from '../scripts/factory-graph/core.mjs';
import {openCorpus} from '../scripts/original-contracts/source.mjs';

test('captured CommonJS import 774101 -> 510914 survives authenticated graph publication',async(t)=>{
 const app=resolve(import.meta.dirname,'..');const corpus=await openCorpus(app);
 const importer=await corpus.factory(774101,{source:'evidence/web/objects/a0ec47219f76f808.js'});
 assert.equal(importer.provenance.sha256,'c69e3ff21e9162f1c81a5f8316bdf5b6ad131ecc0d3f8bced202a6b3339098ca');
 const root=await mkdtemp(join(tmpdir(),'graph-commonjs-'));t.after(()=>rm(root,{recursive:true,force:true}));
 const modules=corpus.index.modules.filter(m=>m.ids.includes(774101)||m.ids.includes(510914));
 assert.equal(modules.length,2);
 const paths=new Set(modules.flatMap(m=>[m.path,...m.origins.map(o=>o.source)]));
 for(const path of paths){await mkdir(dirname(join(root,path)),{recursive:true});await copyFile(join(app,path),join(root,path));}
 await mkdir(join(root,'contracts'),{recursive:true});
 await writeFile(join(root,'recovered/modules.json'),JSON.stringify({...corpus.index,modules}));
 await writeFile(join(root,'evidence/web/manifest.json'),JSON.stringify({records:corpus.manifest.records.filter(r=>paths.has(r.path))}));
 await writeFile(join(root,'contracts/internal-operations.json'),JSON.stringify({operations:[]}));
 await writeFile(join(root,'contracts/developer-bindings.json'),JSON.stringify({bindings:[]}));
 let lines=0;for(const module of modules)lines+=countSourceLines(await readFile(join(root,module.path),'utf8'));
 const options={routes:[],targetLines:lines,maximumLines:lines};
 const reports=await buildGraph(root,options);
 const identities=reports['MODULE-IDENTITIES.json.gz'];const source=identities.find(n=>n.id===774101);const target=identities.find(n=>n.id===510914);
 const edge=reports['IMPORT-EDGES.json.gz'].find(e=>e.source===source.key&&e.requestedId===510914);
 assert.ok(edge,'the captured top-level runtime.r call must be an import boundary');
 assert.equal(edge.runtimeMethod,'r');assert.equal(edge.kind,'direct');assert.equal(edge.resolution,'EXACT');assert.equal(edge.target,target.key);
 await publishGraph(root,'research/commonjs',options);await verifyGraph(root,'research/commonjs',options);
});

test('CommonJS recognition preserves import kinds and excludes other receivers',()=>{
 const imports=analyzeFactory('(runtime)=>{runtime.r(1);runtime.i(2);runtime.A(3);other.r(4)}').imports;
 assert.deepEqual(imports.map(({runtimeMethod,kind,target})=>[runtimeMethod,kind,target]),[['r','direct',1],['i','direct',2],['A','dynamic',3]]);
});
