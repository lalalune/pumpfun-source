import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile,writeFile,rm} from 'node:fs/promises';
import {join,resolve,sep,basename} from 'node:path';
import {tmpdir} from 'node:os';
import test from 'node:test';
import {buildGraph,publishGraph,verifyGraph} from '../scripts/factory-graph/core.mjs';
import {fixture} from './factory-graph-fixture.mjs';

test('graph preserves authenticated UTF-16 ranges after a captured UTF-8 BOM',async()=>{
 const root=await fixture();const options={routes:['/'],targetLines:4,maximumLines:100};
 try{
  const baseline=await buildGraph(root,options);
  const relative='evidence/web/objects/source.js';
  const original=await readFile(join(root,relative));
  const bytes=Buffer.concat([Buffer.from([0xef,0xbb,0xbf]),original]);
  await writeFile(join(root,relative),bytes);
  const manifest=JSON.parse(await readFile(join(root,'evidence/web/manifest.json'),'utf8'));
  const record=manifest.records.find(r=>r.path===relative);
  record.bytes=bytes.length;record.sha256=createHash('sha256').update(bytes).digest('hex');
  await writeFile(join(root,'evidence/web/manifest.json'),JSON.stringify(manifest));
  const index=JSON.parse(await readFile(join(root,'recovered/modules.json'),'utf8'));
  for(const module of index.modules)for(const origin of module.origins)if(origin.source===relative){origin.start++;origin.end++;}
  await writeFile(join(root,'recovered/modules.json'),JSON.stringify(index));
  const next=await buildGraph(root,options);
  assert.equal(next['MODULE-IDENTITIES.json.gz'].length,baseline['MODULE-IDENTITIES.json.gz'].length);
  await publishGraph(root,'research/bom-graph',options);
  await verifyGraph(root,'research/bom-graph',options);
  const corrupt=Buffer.from(bytes);corrupt[1]=0xff;
  await writeFile(join(root,relative),corrupt);
  record.sha256=createHash('sha256').update(corrupt).digest('hex');
  await writeFile(join(root,'evidence/web/manifest.json'),JSON.stringify(manifest));
  await assert.rejects(buildGraph(root,options),/invalid UTF-8/);
 }finally{
  assert.ok(resolve(root).startsWith(resolve(tmpdir())+sep)&&basename(root).startsWith('factory-graph-'));
  await rm(root,{recursive:true,force:true});
 }
});
