import test from 'node:test';
import assert from 'node:assert/strict';
import {formatBundles} from '../scripts/format-bundles.mjs';
import {createHash} from 'node:crypto';
import {mkdtemp,mkdir,writeFile,readFile,rm} from 'node:fs/promises';
import {createTestSymlink} from './helpers/test-symlink.mjs';
import {tmpdir} from 'node:os';
import path from 'node:path';
for (const kind of ['traversal', 'absolute', 'symlink']) test(`formatter refuses ${kind} manifest source paths`,async(t)=>{
  const temporary=await mkdtemp(path.join(tmpdir(),'formatter-paths-'));const root=path.join(temporary,'app');
  try{
    await mkdir(path.join(root,'evidence/web'),{recursive:true});const outside=path.join(temporary,'outside.js');const source='const synthetic=1;';await writeFile(outside,source);
    await mkdir(path.join(root,'evidence/web/objects'),{recursive:true});
    if(kind==='symlink'&&!await createTestSymlink(t,outside,path.join(root,'evidence/web/objects/linked.js')))return;
    const sourcePath=kind==='traversal'?'../outside.js':kind==='absolute'?outside:'evidence/web/objects/linked.js';
      await writeFile(path.join(root,'evidence/web/manifest.json'),JSON.stringify({records:[{url:'https://example.invalid/source.js',status:200,path:sourcePath,sha256:createHash('sha256').update(source).digest('hex')}]}));
      await assert.rejects(formatBundles(root),/formatting failed/);
      const report=JSON.parse(await readFile(path.join(root,'recovered/pretty/manifest.json'),'utf8'));
      assert.match(report.records[0].error,/Unsafe source path/);
  }finally{
    assert.equal(path.dirname(path.resolve(temporary)),path.resolve(tmpdir()));
    assert.ok(path.basename(temporary).startsWith('formatter-paths-'));
    await rm(temporary,{recursive:true,force:true});
  }
});
