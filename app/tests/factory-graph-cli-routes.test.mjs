import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const cli = fileURLToPath(new URL('../scripts/factory-graph/cli.mjs', import.meta.url));
const reportFile = new URL('../research/turbopack-route-graph-20261028/ROUTE-ATTRIBUTION.json', import.meta.url);
function route(name) {
  return spawnSync(process.execPath, [cli, 'route', name], { encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 });
}

test('graph route CLI rejects inherited names and returns the actual retained route report', async () => {
  const before = await readFile(reportFile, 'utf8');
  const report = JSON.parse(before);
  const valid = route('/go');
  assert.equal(valid.status, 0, valid.stderr);
  assert.deepEqual(JSON.parse(valid.stdout), report['/go']);
  for (const name of ['/not-a-retained-route', 'toString', 'constructor', '__proto__', 'hasOwnProperty']) {
    const result = route(name);
    assert.notEqual(result.status, 0, `${name}: ${result.stdout}`);
    assert.equal(result.stdout, '');
    assert.match(result.stderr, /unknown route/);
  }
  assert.equal(await readFile(reportFile, 'utf8'), before);
});
