import { createTestSymlink } from './helpers/test-symlink.mjs';
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { mkdtemp, mkdir, readFile, writeFile, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { openCorpus, decodeSource, sha256, RANGE_ENCODING } from '../scripts/original-contracts/source.mjs';

async function fixture(t) {
  const root = await mkdtemp(path.join(os.tmpdir(), 'original-source-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  await mkdir(path.join(root, 'evidence/web/objects'), { recursive: true });
  await mkdir(path.join(root, 'recovered'));
  const text = '\ufeff(globalThis.TURBOPACK||(globalThis.TURBOPACK=[])).push(["/chunk.js",7,e=>{const label="é😀";e.s(["x",0,label])}]);\r\n';
  const start = text.indexOf('e=>');
  const end = text.indexOf('}]);') + 1;
  const source = 'evidence/web/objects/chunk.js';
  const record = { path: source, url: 'https://example.invalid/chunk.js', status: 200,
    bytes: Buffer.byteLength(text), sha256: sha256(Buffer.from(text)) };
  const index = { rangeEncoding: RANGE_ENCODING, modules: [{ ids: [7],
    sha256: sha256(text.slice(start, end)), path: 'unused-formatted.js',
    origins: [{ source, url: record.url, start, end }] }] };
  const save = async () => {
    await writeFile(path.join(root, 'evidence/web/manifest.json'), JSON.stringify({ records: [record] }));
    await writeFile(path.join(root, 'recovered/modules.json'), JSON.stringify(index));
  };
  await writeFile(path.join(root, source), text);
  await save();
  return { root, text, source, record, index, save };
}

test('factory lookup authenticates original AST and preserves BOM, CRLF and Unicode byte ranges', async (t) => {
  const f = await fixture(t);
  const corpus = await openCorpus(f.root);
  const factory = await corpus.factory(7);
  assert.equal(factory.runtime, 'e');
  assert.deepEqual(factory.ids, [7]);
  assert.equal(factory.provenance.utf8[0], factory.provenance.utf16[0] + 2);
  const bytes = await readFile(path.join(f.root, f.source));
  assert.equal(sha256(bytes.subarray(...factory.provenance.utf8)), factory.provenance.sha256);
  assert.equal(factory.text(), 'e=>{const label="é😀";e.s(["x",0,label])}');
  assert.equal(factory.capture.text, f.text);
});

test('UTF-16 offsets inside an astral character are not byte boundaries', async (t) => {
  const f = await fixture(t);
  const capture = await (await openCorpus(f.root)).capture(f.source);
  const start = f.text.indexOf('😀');
  assert.throws(() => capture.witness({ start: start + 1, end: start + 2 }, 'bad split'), /boundary/);
  assert.deepEqual(capture.witness({ start, end: start + 2 }, 'emoji').utf8.map((n, i, a) => i ? n - a[0] : 0), [0, 4]);
  assert.throws(() => decodeSource(Buffer.from([0xc3, 0x28])), /encoded data/);
});

test('capture hash and length changes fail before AST attribution', async (t) => {
  const f = await fixture(t);
  await writeFile(path.join(f.root, f.source), f.text + ' ');
  await assert.rejects((await openCorpus(f.root)).factory(7), /authentication failed/);
});

test('an updated manifest cannot make malformed UTF-8 into source text', async (t) => {
  const f = await fixture(t);
  const bytes = Buffer.from([0xef, 0xbb, 0xbf, 0xc3, 0x28]);
  f.record.bytes = bytes.length;
  f.record.sha256 = sha256(bytes);
  await writeFile(path.join(f.root, f.source), bytes);
  await f.save();
  await assert.rejects((await openCorpus(f.root)).factory(7), /encoded data/);
});

test('indexed arbitrary substrings cannot substitute for actual registered factories', async (t) => {
  const f = await fixture(t);
  f.index.modules[0].origins[0].start += 1;
  await f.save();
  await assert.rejects((await openCorpus(f.root)).factory(7), /registration/);
});

test('an aggregate inventory ID cannot substitute for the actual registration ID', async (t) => {
  const f = await fixture(t);
  f.index.modules[0].ids.push(8);
  await f.save();
  await assert.rejects((await openCorpus(f.root)).factory(8), /registration/);
});

test('multiple origin contexts stay ambiguous until explicitly selected', async (t) => {
  const f = await fixture(t);
  f.index.modules[0].origins.push({ ...f.index.modules[0].origins[0] });
  await f.save();
  await assert.rejects((await openCorpus(f.root)).factory(7), /explicit chunk context required/);
});

test('manifest source symlinks are rejected', async (t) => {
  const f = await fixture(t);
  await rm(path.join(f.root, f.source));
  if (!await createTestSymlink(t, path.join(f.root, 'recovered/modules.json'), path.join(f.root, f.source))) return;
  await assert.rejects((await openCorpus(f.root)).factory(7), /symlink/);
});

test('manifest source traversal paths are rejected', async (t) => {
  const f = await fixture(t);
  f.record.path = '../escape.js';
  f.index.modules[0].origins[0].source = '../escape.js';
  await f.save();
  await assert.rejects((await openCorpus(f.root)).factory(7), /non-object capture path/);
});

test('a forged manifest cannot authorize reading a repository file outside retained objects', async (t) => {
  const f = await fixture(t);
  const harmless = 'recovered/harmless.txt';
  const bytes = Buffer.from('Synthetic non-sensitive file; not capture evidence.');
  await writeFile(path.join(f.root, harmless), bytes);
  f.record.path = harmless;
  f.record.bytes = bytes.length;
  f.record.sha256 = sha256(bytes);
  await f.save();
  await assert.rejects((await openCorpus(f.root)).capture(harmless), /non-object capture path/);
});

test('the runtime-leading nested-array grammar validates nested and trailing factories', async (t) => {
  const f = await fixture(t);
  const text = '(globalThis.TURBOPACK||(globalThis.TURBOPACK=[])).push(["c",[7,e=>{}],9,e=>{}]);';
  f.record.bytes = Buffer.byteLength(text);
  f.record.sha256 = sha256(text);
  f.index.modules = [7, 9].map((id, i) => {
    const start = text.indexOf('e=>{}', i ? text.indexOf('e=>{}') + 1 : 0);
    return { ids: [id], sha256: sha256('e=>{}'), origins: [{ source: f.source, url: f.record.url, start, end: start + 'e=>{}'.length }] };
  });
  await writeFile(path.join(f.root, f.source), text);
  await f.save();
  const corpus = await openCorpus(f.root);
  assert.deepEqual((await corpus.factory(7)).ids, [7]);
  assert.deepEqual((await corpus.factory(9)).ids, [9]);
  const moved = text.replace('["c",[7,e=>{}],9,e=>{}]', '["c",9,e=>{},[7,e=>{}]]');
  f.record.bytes = Buffer.byteLength(moved);
  f.record.sha256 = sha256(moved);
  const nested = moved.indexOf('e=>{}', moved.indexOf('e=>{}') + 1);
  f.index.modules = [{ ids: [7], sha256: sha256('e=>{}'), origins: [{ source: f.source, url: f.record.url, start: nested, end: nested + 'e=>{}'.length }] }];
  await writeFile(path.join(f.root, f.source), moved);
  await f.save();
  await assert.rejects((await openCorpus(f.root)).factory(7), /registration/);
});

test('outer two-element registration is metadata, not a nested factory container', async (t) => {
  const f = await fixture(t);
  const text = '(globalThis.TURBOPACK||(globalThis.TURBOPACK=[])).push(["metadata",[7,e=>{}]]);';
  f.record.bytes = Buffer.byteLength(text);
  f.record.sha256 = sha256(text);
  const start = text.indexOf('e=>{}');
  f.index.modules[0].sha256 = sha256('e=>{}');
  f.index.modules[0].origins[0] = { source: f.source, url: f.record.url, start, end: start + 'e=>{}'.length };
  await writeFile(path.join(f.root, f.source), text);
  await f.save();
  await assert.rejects((await openCorpus(f.root)).factory(7), /registration/);
});
