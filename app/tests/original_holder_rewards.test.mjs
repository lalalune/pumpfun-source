import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { extractHolderRewards } from '../scripts/original-contracts/holder-rewards.mjs';
import { validateDeclared } from '../scripts/original-contracts/validate.mjs';

const root = fileURLToPath(new URL('..', import.meta.url));
const committed = JSON.parse(await fs.readFile(new URL('../contracts/original-holder-rewards.json', import.meta.url), 'utf8'));
const { declarations } = committed;
const check = (kind, value) => validateDeclared(declarations, declarations[`x-holder-rewards-${kind}`], value).success;
const book = {
  generatedAt: '2026-10-29T00:00:00.000Z', coins: [], next: null, quotes: {},
  totals: { coinCount: 0, payingCount: 0, accruedUsdAtTrade: '0', accruedUsdNow: '0', unpricedCoinCount: 0,
    walletsRewarded: 0, walletsRewardedDistinct: 0, payoutCount: 0 },
  matchingCount: 0, offset: 0, byQuote: [],
};
const quote = { mint: 'Q', decimals: 6, usdPrice: null, symbol: null, name: null, imageUri: null };

test('committed contract is exactly what the frozen captures produce', async () => {
  assert.deepEqual(await extractHolderRewards(root), committed);
});

test('only the declaration names the operation; no captured caller is claimed', () => {
  assert.deepEqual(committed.reachability.occurrences, ['evidence/web/objects/2b47dd0b38a1608f.js']);
  assert.equal(committed.reachability.capturedCallers, 0);
  assert.equal(committed.siblingTransport.reads.includes(committed.operation), false);
});

test('declared query keeps the regex quote filter and the page/limit bounds', () => {
  assert.equal(check('query', {}), true);
  assert.equal(check('query', { quote: 'So11111111111111111111111111111111111111112' }), true);
  assert.equal(check('query', { quote: `0${'1'.repeat(40)}` }), false);
  assert.equal(check('query', { quote: '1'.repeat(31) }), false);
  assert.equal(check('query', { limit: 2000, page: 1 }), true);
  assert.equal(check('query', { limit: 2001 }), false);
  assert.equal(check('query', { page: 0 }), false);
  assert.equal(check('query', { sort: 'accruedNow', direction: 'asc' }), true);
  assert.equal(check('query', { sort: 'volume' }), false);
});

test('declared quotes record checks every entry, while row shapes accept extra fields', () => {
  assert.equal(check('response', book), true);
  assert.equal(check('response', { ...book, quotes: { Q: quote } }), true);
  assert.equal(check('response', { ...book, quotes: { Q: { mint: 'Q' } } }), false);
  assert.equal(check('response', { ...book, quotes: { Q: 1 } }), false);
  assert.equal(check('response', { ...book, extra: true }), true);
  assert.equal(check('response', { ...book, next: undefined }), false);
});
