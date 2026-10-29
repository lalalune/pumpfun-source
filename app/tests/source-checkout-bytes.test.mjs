import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, readFile, rm } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';

test('autocrlf checkout preserves authenticated maintained source bytes', async (t) => {
  const root = await mkdtemp(path.join(tmpdir(), 'source-checkout-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  await mkdir(path.join(root, 'app'), { recursive: true });
  await writeFile(path.join(root, 'app/.gitattributes'),
    await readFile(new URL('../.gitattributes', import.meta.url)));
  const source = Buffer.from('// reviewed source\nexport const value = 1;\n');
  const paths = [
    'app/scripts/original-contracts/source.mjs',
    'app/packages/frontend/src/original-contracts/auth/kernels/reader.mjs',
    'app/packages/frontend/src/original-contracts/example.mts',
    'app/packages/frontend/src/app/portfolio/rpc.ts',
    'app/packages/frontend/src/app/competitions/page.tsx',
    'app/packages/frontend/src/app/captured-shell.css',
    'app/packages/frontend/src/theme/captured-theme.json',
    'app/packages/frontend/public/pump-logomark.svg',
    'app/tests/original_privacy_external_links.browser.mjs',
    'app/packages/frontend/src/app/wallet-program-record/contract.json',
    'app/research/wallet-program-record-20261029/SOURCE.json',
  ];
  const expected = (name) => name.endsWith('.json')
    ? Buffer.from('{\n  "reviewed": true\n}\n') : source;
  for (const name of paths) {
    await mkdir(path.dirname(path.join(root, name)), { recursive: true });
    await writeFile(path.join(root, name), expected(name));
  }
  const git = (...args) => execFileSync('git', [
    '-c', 'core.autocrlf=true', '-c', 'core.safecrlf=false', ...args,
  ], { cwd: root, stdio: 'pipe' });
  git('init', '--quiet');
  git('add', '.');
  git('checkout-index', '--all', '--force', '--prefix=checkout/');
  for (const name of paths) {
    assert.deepEqual(await readFile(path.join(root, 'checkout', name)), expected(name), name);
  }
  for (const name of ['app/evidence/web/object.mjs', 'app/packages/sdk/src/index.ts']) {
    assert.equal(git('check-attr', 'eol', '--', name).toString().trim(),
      `${name}: eol: unspecified`);
  }
});
