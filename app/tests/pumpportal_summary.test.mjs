import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
  buildTokenIndex,
  countEventTypes,
  summariseCapture,
} from '../../scripts/pumpportal-summary.mjs';

const ev = (data, receivedAt = '2026-10-29T00:00:00.000Z') => ({ receivedAt, data });

test('tokens whose mint collides with an Object.prototype name are indexed, not dropped', () => {
  const events = [
    ev({ mint: 'NormalMint111', txType: 'buy', solAmount: 2 }),
    ev({ mint: 'constructor', txType: 'buy', solAmount: 3 }),
    ev({ mint: 'toString', txType: 'sell', solAmount: 4 }),
    ev({ mint: 'valueOf', txType: 'create' }),
    ev({ mint: 'hasOwnProperty', txType: 'buy', solAmount: 5 }),
  ];
  const { tokenIndex } = summariseCapture(events);
  assert.equal(Object.values(tokenIndex).length, 5, 'every mint must produce an index entry');
  for (const mint of ['NormalMint111', 'constructor', 'toString', 'valueOf', 'hasOwnProperty']) {
    assert.ok(Object.hasOwn(tokenIndex, mint), `missing own index entry for ${mint}`);
  }
  assert.equal(tokenIndex['constructor'].event_count, 1);
  assert.equal(tokenIndex['constructor'].buys, 1);
  assert.equal(tokenIndex['constructor'].total_sol_volume, 3);
  assert.equal(tokenIndex['toString'].sells, 1);
  assert.equal(tokenIndex['valueOf'].creates, 1);
});

test('a __proto__ mint is indexed as an own key and does not pollute Object.prototype', () => {
  const { tokenIndex } = summariseCapture([
    ev({ mint: '__proto__', txType: 'buy', solAmount: 7 }),
    ev({ mint: '__proto__', txType: 'sell', solAmount: 1 }),
  ]);
  assert.ok(Object.hasOwn(tokenIndex, '__proto__'), '__proto__ must be an own key');
  assert.equal(tokenIndex['__proto__'].event_count, 2);
  assert.equal(tokenIndex['__proto__'].buys, 1);
  assert.equal(tokenIndex['__proto__'].sells, 1);
  // The accumulator and the global prototype must be untouched.
  assert.equal(Object.getPrototypeOf(tokenIndex), null);
  for (const polluted of ['event_count', 'buys', 'total_sol_volume', 'mint', 'first_seen']) {
    assert.ok(!Object.hasOwn(Object.prototype, polluted), `Object.prototype polluted with ${polluted}`);
    assert.equal({}[polluted], undefined, `Object.prototype.${polluted} leaked`);
  }
});

test('event-type labels colliding with prototype names are counted', () => {
  const counts = countEventTypes([
    ev({ txType: 'buy' }),
    ev({ txType: 'constructor' }),
    ev({ txType: '__proto__' }),
    ev({ method: 'toString' }),
    ev({}),
  ]);
  assert.equal(counts['buy'], 1);
  assert.equal(counts['constructor'], 1);
  assert.equal(counts['__proto__'], 1);
  assert.equal(counts['toString'], 1);
  assert.equal(counts['unknown'], 1);
  assert.equal(Object.getPrototypeOf(counts), null);
});

test('normal captures keep their existing counts, volume and ordering', () => {
  const events = [
    ev({ mint: 'aaa', txType: 'create', name: 'A', symbol: 'AA' }, '2026-10-29T00:00:01.000Z'),
    ev({ mint: 'aaa', txType: 'buy', solAmount: 1.5 }, '2026-10-29T00:00:02.000Z'),
    ev({ mint: 'aaa', txType: 'sell', solAmount: 0.5 }, '2026-10-29T00:00:03.000Z'),
    ev({ mint: 'bbb', txType: 'buy', solAmount: 2 }, '2026-10-29T00:00:04.000Z'),
  ];
  const index = buildTokenIndex(events);
  assert.deepEqual(Object.keys(index), ['aaa', 'bbb'], 'insertion order preserved');
  assert.equal(index['aaa'].name, 'A');
  assert.equal(index['aaa'].first_seen, '2026-10-29T00:00:01.000Z');
  assert.equal(index['aaa'].last_seen, '2026-10-29T00:00:03.000Z');
  assert.equal(index['aaa'].event_count, 3);
  assert.equal(index['aaa'].creates, 1);
  assert.equal(index['aaa'].buys, 1);
  assert.equal(index['aaa'].sells, 1);
  assert.equal(index['aaa'].total_sol_volume, 2);
  assert.equal(index['bbb'].total_sol_volume, 2);
  assert.equal(JSON.stringify(Object.values(index)).includes('NormalMint'), false);
});
