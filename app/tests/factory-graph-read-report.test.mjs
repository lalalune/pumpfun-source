import assert from 'node:assert/strict';
import {readFile,writeFile,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {gzipSync} from 'node:zlib';
import test from 'node:test';
import {publishGraph,readReport} from '../scripts/factory-graph/core.mjs';
import {fixture} from './factory-graph-fixture.mjs';

test('report lookup authenticates plain and compressed records before returning data',async(t)=>{
 const root=await fixture();t.after(()=>rm(root,{recursive:true,force:true}));
 const out='research/read-report';const options={routes:['/'],targetLines:4,maximumLines:100};
 await publishGraph(root,out,options);
 const summary=await readReport(root,out,'GRAPH-SUMMARY.json');
 assert.ok(summary.identities>0);
 assert.ok((await readReport(root,out,'MODULE-IDENTITIES.json.gz')).length>0);
 await writeFile(join(root,out,'GRAPH-SUMMARY.json'),JSON.stringify({...summary,identities:123456}));
 await assert.rejects(readReport(root,out,'GRAPH-SUMMARY.json'),/generated evidence mismatch/);
 await writeFile(join(root,out,'MODULE-IDENTITIES.json.gz'),gzipSync('[]\n'));
 await assert.rejects(readReport(root,out,'MODULE-IDENTITIES.json.gz'),/generated evidence mismatch/);
});

test('report lookup requires one matching manifest entry and a supported packet version',async(t)=>{
 const root=await fixture();t.after(()=>rm(root,{recursive:true,force:true}));
 const out='research/read-report';await publishGraph(root,out,{routes:['/'],targetLines:4,maximumLines:100});
 const path=join(root,out,'MANIFEST.json');const original=JSON.parse(await readFile(path,'utf8'));
 for(const files of [original.files.filter(e=>e.path!=='GRAPH-SUMMARY.json'),[...original.files,original.files.find(e=>e.path==='GRAPH-SUMMARY.json')]]){
  await writeFile(path,JSON.stringify({...original,files}));
  await assert.rejects(readReport(root,out,'GRAPH-SUMMARY.json'),/manifest entry/);
 }
 await writeFile(path,JSON.stringify({...original,schemaVersion:999}));
 await assert.rejects(readReport(root,out,'GRAPH-SUMMARY.json'),/schema version/);
});
