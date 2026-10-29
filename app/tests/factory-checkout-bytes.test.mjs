import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile,rm} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {tmpdir} from 'node:os';
import path from 'node:path';
import prettier from 'prettier';
import {openCorpus} from '../scripts/original-contracts/source.mjs';

test('autocrlf checkout preserves the exact formatter derivation of captured factory 376744', async (t) => {
  const corpus = await openCorpus(path.resolve(import.meta.dirname, '..'));
  const factory = await corpus.factory(376744);
  const expected = '// Recovered Turbopack factory. Requires original runtime/import IDs; not a standalone source module.\n'
    + await prettier.format(`(${factory.text()});`, {parser:'babel'});
  const name = 'app/recovered/modules/376744-c0394effad71.js';
  const root = await mkdtemp(path.join(tmpdir(), 'factory-checkout-'));
  t.after(() => rm(root, {recursive:true,force:true}));
  await mkdir(path.dirname(path.join(root,name)), {recursive:true});
  await writeFile(path.join(root,'app/.gitattributes'), await readFile(new URL('../.gitattributes',import.meta.url)));
  await writeFile(path.join(root,name),expected);
  const git=(...args)=>execFileSync('git',['-c','core.autocrlf=true','-c','core.safecrlf=false',...args],{cwd:root,stdio:'pipe'});
  git('init','--quiet');
  git('add','.');
  git('checkout-index','--all','--force','--prefix=checkout/');
  assert.ok((await readFile(path.join(root,'checkout',name),'utf8'))===expected,
    'autocrlf must preserve the complete pinned-formatter derivation');
});
