import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, mkdir, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { formatBundles } from '../scripts/format-bundles.mjs';

test('formatter authenticates every supplied byte count and retains legacy omission', async (t) => {
  const root = await mkdtemp(path.join(tmpdir(), 'formatter-byte-counts-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const bytes = Buffer.from('const synthetic = "é😀";');
  await mkdir(path.join(root, 'evidence/web/objects'), { recursive: true });
  await writeFile(path.join(root, 'evidence/web/objects/source.js'), bytes);
  const record = { url: 'https://example.invalid/source.js', status: 200,
    path: 'evidence/web/objects/source.js', sha256: createHash('sha256').update(bytes).digest('hex') };
  const manifest = path.join(root, 'evidence/web/manifest.json');
  const reportPath = path.join(root, 'recovered/pretty/manifest.json');
  for (const count of [undefined, bytes.length, bytes.length + 1, bytes.length - 1, -1, 1.5, null, true, String(bytes.length)]) {
    await writeFile(manifest, JSON.stringify({ records: [{ ...record, ...(count === undefined ? {} : { bytes: count }) }] }));
    const valid = count === undefined || count === bytes.length;
    if (valid) await formatBundles(root);
    else await assert.rejects(formatBundles(root), /formatting failed/);
    const report = JSON.parse(await readFile(reportPath, 'utf8'));
    assert.equal(report.records[0].status, valid ? 'formatted' : 'failed', String(count));
    if (!valid) assert.match(report.records[0].error, /byte count mismatch/);
    assert.deepEqual(await readFile(path.join(root, record.path)), bytes);
  }
});
