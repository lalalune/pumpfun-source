import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../..', import.meta.url));
const files = [
  'app/scripts/original-contracts/source.mjs',
  'app/reconstruction/competition-client/contract.json',
  'app/reconstruction/competition-countdown/contract.json',
  'app/recovered/modules.json',
  'app/contracts/developer.openapi.json',
  'app/packages/frontend/src/components/leaderboard/original-countdown.mjs',
];
function git(args) {
  const result = spawnSync('git', args, { cwd: root, maxBuffer: 32 * 1024 * 1024 });
  assert.equal(result.status, 0, result.stderr?.toString());
  return result.stdout;
}

test('Git checkout preserves authenticated derived inputs with Windows autocrlf enabled', async (t) => {
  const output = await mkdtemp(path.join(tmpdir(), 'derived-checkout-'));
  t.after(() => rm(output, { recursive: true, force: true }));
  git(['-c', 'core.autocrlf=true', 'checkout-index', `--prefix=${output.replaceAll('\\', '/')}/`, '--', ...files]);
  for (const file of files) {
    const digest = (bytes) => createHash('sha256').update(bytes).digest('hex');
    assert.equal(digest(await readFile(path.join(output, file))), digest(git(['show', `HEAD:${file}`])), file);
  }
});
