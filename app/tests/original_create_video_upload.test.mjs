import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { recover, verify } from '../scripts/original-contracts/create-video-upload/verify.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const packet = JSON.parse(await readFile(new URL('../contracts/original-create-video-upload.json', import.meta.url)));

test('rederive complete static video request, provider POST and both metadata handoffs', async () => {
  assert.deepEqual(await verify(root), { factoryRoles: 14, uniqueFactories: 13, witnesses: 88, productionOperationsQualified: 0 });
});

test('declared response and executor-returned cancellation retain their actual limits', async () => {
  const derived = await recover(root);
  assert.match(derived.request.responseValidation, /without validating/);
  assert.match(derived.providerUpload.cancellation, /Promise executor/);
  assert.match(derived.prerequisites.timing, /later than file-selection upload/);
  assert.equal(derived.mounted, false);
});

test('packet changes to origin, method, fields, status, result or invented auth/qualification fail', async () => {
  // Reconstruct once from real captured ASTs. These are packet integrity checks,
  // not simulated uploads, HTTP responses or tests of original runtime behavior.
  const actual = await recover(root);
  for (const mutate of [
    (x) => { x.request.origin = 'https://example.invalid'; },
    (x) => { x.providerUpload.method = 'PUT'; },
    (x) => { x.providerUpload.orderedParts.reverse(); },
    (x) => { x.providerUpload.success = 'all statuses accepted'; },
    (x) => { x.handoff.metadataVideo = 'videoURL'; },
    (x) => { x.prerequisites.upload = 'anonymous upload allowed'; },
    (x) => { x.productionOperationsQualified = 1; },
    (x) => { x.sources.selector.utf16[0]++; },
    (x) => { x.witnesses[0].sha256 = '0'.repeat(64); },
  ]) {
    const changed = structuredClone(packet);
    mutate(changed);
    assert.throws(() => assert.deepEqual(changed, actual));
  }
});
