import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdtemp,mkdir,readFile,writeFile,readdir,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import test from 'node:test';
import {formatBundles} from '../scripts/format-bundles.mjs';
const digest=b=>createHash('sha256').update(b).digest('hex');
async function fixture(t){
 const root=await mkdtemp(join(tmpdir(),'formatter-packet-'));t.after(()=>rm(root,{recursive:true,force:true}));
 const app=fileURLToPath(new URL('../',import.meta.url));
 const manifest=JSON.parse(await readFile(join(app,'evidence/web/manifest.json'),'utf8'));
 const paths=['evidence/web/objects/a0ec47219f76f808.js','evidence/web/objects/f25d7686d048ae16.js'];
 const records=paths.map(path=>structuredClone(manifest.records.find(r=>r.path===path)));
 for(const record of records){const bytes=await readFile(join(app,record.path));assert.equal(digest(bytes),record.sha256);assert.equal(bytes.length,record.bytes);await mkdir(dirname(join(root,record.path)),{recursive:true});await writeFile(join(root,record.path),bytes);}
 await writeFile(join(root,'evidence/web/manifest.json'),JSON.stringify({records}));
 return{root,records};
}
async function snapshot(root){const out={};for(const entry of await readdir(join(root,'recovered/pretty'))){out[entry]=digest(await readFile(join(root,'recovered/pretty',entry)));}return out;}
for(const failure of ['digest','parser'])test(`a later ${failure} failure cannot replace an earlier complete formatted packet`,async(t)=>{
 const {root,records}=await fixture(t);await formatBundles(root);
 await writeFile(join(root,'recovered/pretty/notes.txt'),'unrelated retained note');const before=await snapshot(root);
 const first=Buffer.concat([await readFile(join(root,records[0].path)),Buffer.from('\n// next capture revision\n')]);
 await writeFile(join(root,records[0].path),first);Object.assign(records[0],{bytes:first.length,sha256:digest(first)});
 const second=Buffer.concat([await readFile(join(root,records[1].path)),Buffer.from(failure==='parser'?'\nfunction {':'\n// changed without a matching digest')]);
 await writeFile(join(root,records[1].path),second);
 if(failure==='parser')Object.assign(records[1],{bytes:second.length,sha256:digest(second)});
 await writeFile(join(root,'evidence/web/manifest.json'),JSON.stringify({records}));
 await assert.rejects(formatBundles(root),/formatting failed/);
 assert.deepEqual(await snapshot(root),before);
 const diagnostic=JSON.parse(await readFile(join(root,'recovered/pretty-failure.json'),'utf8'));
 assert.equal(diagnostic.records[1].status,'failed');
 assert.deepEqual((await readdir(join(root,'recovered'))).sort(),['pretty','pretty-failure.json']);
});
test('a successful complete replacement preserves unrelated files',async(t)=>{
 const {root,records}=await fixture(t);await formatBundles(root);
 await writeFile(join(root,'recovered/pretty/notes.txt'),'keep');
 const source=Buffer.concat([await readFile(join(root,records[0].path)),Buffer.from('\n// accepted next revision\n')]);
 await writeFile(join(root,records[0].path),source);Object.assign(records[0],{bytes:source.length,sha256:digest(source)});
 await writeFile(join(root,'evidence/web/manifest.json'),JSON.stringify({records}));
 await formatBundles(root);const packet=JSON.parse(await readFile(join(root,'recovered/pretty/manifest.json'),'utf8'));
 assert.equal(packet.records[0].sha256,digest(source));assert.match(await readFile(join(root,packet.records[0].output),'utf8'),/accepted next revision/);
 assert.equal(await readFile(join(root,'recovered/pretty/notes.txt'),'utf8'),'keep');
});
