import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { LeaderboardStore } from '../src/leaderboard-store.js';

const seed = JSON.parse(readFileSync(new URL('../src/leaderboard-seed.json', import.meta.url), 'utf8'));
test('JSON numeric overflow in a top-position chain cannot serialize as null', () => {
  const data = structuredClone(seed);
  data.daily[0].positions[0].chainId = JSON.parse('1e400');
  assert.throws(() => new LeaderboardStore(data), /position chainId must be finite/);
});

test('all period boards reject nonfinite or mistyped nested chain numbers', () => {
  for (const period of ['daily', 'weekly', 'monthly']) {
    for (const chainId of [NaN, Infinity, -Infinity, null, '0']) {
      const data = structuredClone(seed);
      data[period][0].positions[0].chainId = chainId;
      assert.throws(() => new LeaderboardStore(data), /position chainId must be finite/);
    }
  }
});

test('finite declared numbers and count-only projections retain their values', () => {
  const data = structuredClone(seed);
  data.daily[0].positions[0].chainId = -0.25;
  const store = new LeaderboardStore(data);
  const board = store.getBoard({ period: 'daily', positionsLimit: 5 });
  assert.equal(board.entries[0].topPositions[0].chainId, -0.25);
  assert.equal(store.getBoard({ period: 'daily', positionsLimit: 0 }).entries[0].positionsCount,
    board.entries[0].positionsCount);
});
