import assert from 'node:assert/strict';
import {watch,mkdirSync,writeFileSync} from 'node:fs';
import {readFile,rm,mkdir,writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import test from 'node:test';
import {publishGraph,verifyGraph} from '../scripts/factory-graph/core.mjs';
import {fixture} from './factory-graph-fixture.mjs';

test('a real backup-rename failure preserves the last published graph',async(t)=>{
 const root=await fixture();t.after(()=>rm(root,{recursive:true,force:true}));
 const out='research/graph';const options={routes:['/'],targetLines:4,maximumLines:100};
 await publishGraph(root,out,options);
 const manifest=join(root,out,'MANIFEST.json');const before=await readFile(manifest);
 let collision=false;let watchError;
 const watcher=watch(join(root,'research'),(_event,name)=>{
  if(String(name)!==`graph.tmp-${process.pid}`||collision)return;
  try{
   const backup=join(root,`research/graph.previous-${process.pid}`);
   mkdirSync(backup,{recursive:true});writeFileSync(join(backup,'occupied'),'retained');
   collision=true;
  }catch(error){watchError=error;}
 });
 t.after(()=>watcher.close());
 await assert.rejects(publishGraph(root,out,options));
 assert.ifError(watchError);assert.equal(collision,true,'real filesystem collision must occur');
 assert.deepEqual(await readFile(manifest),before);
 await verifyGraph(root,out,options);
});

test('a retained recovery backup is preserved and blocks another replacement',async(t)=>{
 const root=await fixture();t.after(()=>rm(root,{recursive:true,force:true}));
 const out='research/graph';const options={routes:['/'],targetLines:4,maximumLines:100};
 await publishGraph(root,out,options);
 const backup=join(root,`research/graph.previous-${process.pid}`);
 await mkdir(backup);await writeFile(join(backup,'recovery'),'previous recovery bytes');
 await assert.rejects(publishGraph(root,out,options),/backup already exists/);
 assert.equal(await readFile(join(backup,'recovery'),'utf8'),'previous recovery bytes');
 await verifyGraph(root,out,options);
});
