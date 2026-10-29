import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdtemp,mkdir,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import test from 'node:test';
import {generateInventory} from '../scripts/inventory.mjs';
import {openCorpus} from '../scripts/original-contracts/source.mjs';

test('inventory and corpus lookup agree on actual Turbopack registration receivers',async(t)=>{
 const root=await mkdtemp(join(tmpdir(),'inventory-registration-'));
 t.after(()=>rm(root,{recursive:true,force:true}));
 await mkdir(join(root,'evidence/web/objects'),{recursive:true});
 const source=`globalThis.TURBOPACK.push(['real.js',1,e=>{e.s(['real',0,1])}]);
 (globalThis.TURBOPACK||(globalThis.TURBOPACK=[])).push(['initialized.js',2,e=>{e.s(['initialized',0,2])}]);
 globalThis.TURBOPACK_LOG.push(['ordinary-log',99,e=>{e.s(['wrong',0,99])}]);
 other.TURBOPACK.push(['another-object',98,e=>{e.s(['wrong',0,98])}]);`;
 const path='evidence/web/objects/source.js';await writeFile(join(root,path),source);
 const record={url:'https://pump.fun/source.js',path,status:200,bytes:Buffer.byteLength(source),sha256:createHash('sha256').update(source).digest('hex')};
 await writeFile(join(root,'evidence/web/manifest.json'),JSON.stringify({records:[record]}));
 const report=await generateInventory(root,{log:()=>{}});
 assert.deepEqual(report.modules.flatMap(m=>m.ids).sort((a,b)=>a-b),[1,2]);
 const corpus=await openCorpus(root);
 assert.equal((await corpus.factory(1)).runtime,'e');
 assert.equal((await corpus.factory(2)).runtime,'e');
 await assert.rejects(corpus.factory(99),/0 origins/);
});
