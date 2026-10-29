import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFile, writeFile, mkdtemp, mkdir, copyFile, rm } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { RECENT_SEARCHES_KEY, createRecentSearchAdder, createRecentSearchClearer, recentSearchHref,
  decodeRecentSearches } from '../packages/frontend/src/components/shell/search/recent-searches.mjs';
import { APP_ROOT, KERNEL, UI, PROOF, verifyRecentSearches } from '../scripts/verify-recent-searches.mjs';

test('actual history operations, used caller and original storage boundaries reproduce', async () => {
  assert.deepEqual(await verifyRecentSearches(), JSON.parse(await readFile(path.join(APP_ROOT, PROOF), 'utf8')));
});

test('source promotion is strict, removes every matching occurrence, preserves case and caps at twenty', () => {
  const terms = ['needle', 'Needle', 'needle', ...Array.from({ length: 25 }, (_, index) => `term ${index}`)];
  const before = [...terms], writes = [];
  const add = createRecentSearchAdder(terms, (next) => writes.push(next));
  assert.equal(add('needle'), undefined);
  assert.deepEqual(writes[0], ['needle', 'Needle', ...Array.from({ length: 18 }, (_, index) => `term ${index}`)]);
  assert.equal(writes[0].length, 20); assert.deepEqual(terms, before);
});

test('each render callback retains its snapshot and preserves raw values and write errors', () => {
  const terms = ['first'], writes = [];
  const add = createRecentSearchAdder(terms, function (next) { assert.equal(this, undefined); writes.push(next); });
  add(' x '); add('second');
  assert.deepEqual(writes, [[' x ', 'first'], ['second', 'first']]);
  const failure = Error('synthetic writer failure');
  assert.throws(() => createRecentSearchAdder([], () => { throw failure; })('term'), (error) => error === failure);
});

test('clear writes a fresh empty array each time without mutating an earlier value', () => {
  const writes = [], clear = createRecentSearchClearer((terms) => writes.push(terms));
  clear(); clear(); assert.deepEqual(writes, [[], []]); assert.notEqual(writes[0], writes[1]);
  assert.equal(RECENT_SEARCHES_KEY, 'recently-searched-terms');
});

test('text-history href preserves the original encoding without term normalization', () => {
  assert.equal(recentSearchHref({ term: ' x & β/# ' }), '/explore?q=%20x%20%26%20%CE%B2%2F%23%20');
  assert.throws(() => recentSearchHref({ term: '\ud800' }), URIError);
});

test('the explicit local decoder distinguishes absence, malformed JSON and non-string-array data', () => {
  assert.deepEqual(decodeRecentSearches(null), []); assert.deepEqual(decodeRecentSearches(''), []);
  assert.deepEqual(decodeRecentSearches('[" x ","x","x",""]'), [' x ', 'x', 'x', '']);
  assert.throws(() => decodeRecentSearches('{'), SyntaxError);
  for (const value of ['{}', 'null', '1', '[1]', '["ok",null]', '"term"', '["\\ud800"]']) {
    assert.throws(() => decodeRecentSearches(value), /Invalid stored search history/);
  }
});

async function changed(t, file, edit) {
  const root = await mkdtemp(path.join(os.tmpdir(), 'recent-searches-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const proof = JSON.parse(await readFile(path.join(APP_ROOT, PROOF), 'utf8'));
  for (const name of new Set(['evidence/web/manifest.json', 'recovered/modules.json', KERNEL, UI, ...proof.proofs.map((item) => item.source)])) {
    await mkdir(path.dirname(path.join(root, name)), { recursive: true }); await copyFile(path.join(APP_ROOT, name), path.join(root, name));
  }
  const target = path.join(root, file), before = await readFile(target, 'utf8'), after = edit(before);
  assert.notEqual(after, before); await writeFile(target, after); return root;
}

test('source proof rejects cutoff, comparison, key, href and used-UI input mutations', async (t) => {
  for (const [file, edit] of [[KERNEL, (text) => text.replace('.slice(0, 19)', '.slice(0, 20)')],
    [KERNEL, (text) => text.replace('entry !== term', 'entry.toLowerCase() !== term.toLowerCase()')],
    [KERNEL, (text) => text.replace("'recently-searched-terms'", "'different-history'")],
    [KERNEL, (text) => text.replace('encodeURIComponent(row.term)', 'encodeURIComponent(row.term.trim())')],
    [UI, (text) => text.replace('historyTerms.slice(0, 3)', 'historyTerms.slice(0, 4)')]]) {
    await assert.rejects(verifyRecentSearches(await changed(t, file, edit)), /AST differs|storage key|row bound/);
  }
});
