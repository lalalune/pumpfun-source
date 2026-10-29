import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir, mkdtemp, copyFile, symlink, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildPreviewFlow, verifyPreviewFlow } from '../reconstruction/live-preview-flow/recover.mjs';

const app = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const packet = 'reconstruction/live-preview-flow/';
const proof = await buildPreviewFlow(app);
async function exported(t) {
  const root = await mkdtemp(path.join(os.tmpdir(), 'public live preview inputs '));
  t.after(() => rm(root, { recursive: true, force: true }));
  const sources = [...new Set([...proof.proof.factories.map((f) => f.source),...proof.proof.lazyAssets.map((a)=>a.path)])];
  const files = [packet+'recover.mjs', packet+'components.mjs', packet+'PROVENANCE.json',
    'scripts/original-contracts/source.mjs', 'scripts/settings-client-contract.mjs',
    'evidence/web/manifest.json', 'recovered/modules.json', proof.proof.origin.source, ...sources];
  for (const file of files) { const target = path.join(root,file); await mkdir(path.dirname(target),{recursive:true}); await copyFile(path.join(app,file),target); }
  await symlink(path.join(app,'node_modules'),path.join(root,'node_modules'),'dir');
  return root;
}
test('complete selected outer components and actual /live Flight/parent/lazy contexts authenticate', async () => {
  const result = await verifyPreviewFlow(app);
  assert.equal(result.factories.length,12); assert.equal(result.origin.component,'LiveHomepage');
  assert.deepEqual(result.origin.elementPath,['1']); assert.equal(result.components.length,12);
  assert.equal(result.contextEdges.length,9);assert.equal(result.lazyAssets.length,7);
  assert.ok(result.fragments.some((f)=>f.label==='complete 369731 local I'));
  assert.ok(result.fragments.some((f)=>f.label==='complete 41705 local u'));
  assert.equal(result.limits.authOrJoin,false); assert.equal(result.limits.innerPlayer,false);
});
test('public raw inputs replay from an unrelated path with spaces without formatted modules/private workfiles',async(t)=>{
  const root=await exported(t); const result=await verifyPreviewFlow(root);
  assert.equal(result.generatedSha256,proof.proof.generatedSha256);
});
test('a changed carousel clamp cannot masquerade as the source controller',async(t)=>{
  const root=await exported(t),file=path.join(root,packet,'components.mjs');
  const before=await readFile(file,'utf8'); assert.ok(before.includes('Math.min(t + e, d - 1)'));
  await writeFile(file,before.replace('Math.min(t + e, d - 1)','Math.min(t + e, d + 1)'));
  await assert.rejects(verifyPreviewFlow(root),/editable preview components differ/);
});
test('losing the actual grouped preview context fails closed',async(t)=>{
  const root=await exported(t),file=path.join(root,'recovered/modules.json');const index=JSON.parse(await readFile(file,'utf8'));
  index.modules=index.modules.filter((m)=>!m.ids.includes(41705));await writeFile(file,JSON.stringify(index));
  await assert.rejects(verifyPreviewFlow(root),/physical variant census 41705/);
});
test('a rehashed changed main-page Flight component is not accepted as the same /live origin binding',async(t)=>{
  const root=await exported(t),file=path.join(root,proof.proof.origin.source),before=await readFile(file,'utf8');
  assert.ok(before.includes('LiveHomepage'));await writeFile(file,before.replace('LiveHomepage','FalseHomepage'));
  const manifestFile=path.join(root,'evidence/web/manifest.json'),manifest=JSON.parse(await readFile(manifestFile,'utf8'));
  const {createHash}=await import('node:crypto'),bytes=await readFile(file);const entry=manifest.records.find((r)=>r.path===proof.proof.origin.source);
  entry.bytes=bytes.length;entry.sha256=createHash('sha256').update(bytes).digest('hex');await writeFile(manifestFile,JSON.stringify(manifest));
  await assert.rejects(verifyPreviewFlow(root),/LiveHomepage|FalseHomepage/);
});
