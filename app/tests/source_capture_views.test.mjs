import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { openCorpus, sha256 } from '../scripts/original-contracts/source.mjs';

const root = fileURLToPath(new URL('..', import.meta.url));
const source = 'evidence/web/objects/2b47dd0b38a1608f.js';

test('real captured witness bytes cannot be changed through a returned buffer', async () => {
  const corpus = await openCorpus(root);
  const factory = await corpus.factory(617159, { source });
  const before = factory.witness(factory.node, 'retained helper');
  const view = factory.capture.bytes;
  view[before.utf8[0]] ^= 1;
  const after = factory.witness(factory.node, 'retained helper');
  const physical = await readFile(new URL('../' + source, import.meta.url));
  assert.deepEqual(after, before);
  assert.equal(after.sha256, sha256(physical.subarray(...after.utf8)));
  assert.notEqual(factory.capture.bytes, view);
});

test('returned offset and metadata views cannot rebind retained source ranges', async () => {
  const corpus = await openCorpus(root);
  const factory = await corpus.factory(617159, { source });
  const before = factory.witness(factory.node, 'retained helper');
  factory.capture.byteOffsets[factory.node.start] = 0;
  const record = corpus.records.get(source);
  for (const [object, key, value] of [
    [factory.capture, 'text', 'changed'],
    [factory.capture, 'record', { ...record, sha256: 'changed' }],
    [record, 'url', 'https://example.invalid/changed.js'],
    [record, 'sha256', 'changed'],
    [record, 'bytes', 1],
  ]) {
    try { object[key] = value; } catch (error) { assert.ok(error instanceof TypeError); }
  }
  corpus.records.set(source, { ...record, sha256: 'changed' });
  assert.deepEqual(factory.witness(factory.node, 'retained helper'), before);
});

test('public manifest metadata is not authority for subsequent capture authentication', async () => {
  const corpus = await openCorpus(root);
  corpus.manifest.records.find(record => record.path === source).sha256 = 'changed';
  corpus.records.delete(source);
  const factory = await corpus.factory(617159, { source });
  assert.equal(factory.provenance.sha256,
    'e2578f8e5b5ad78b72da3056976e38a96e3d7e24f0768215374750f09229074e');
});
