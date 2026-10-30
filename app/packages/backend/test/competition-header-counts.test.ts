import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { CompetitionStore, type RawCompetition } from '../src/competitions-store.js';
import { buildApp } from '../src/app.js';

const seed = (): RawCompetition[] => JSON.parse(readFileSync(new URL('../src/competitions-seed.json', import.meta.url), 'utf8'));
test('competition capacity and membership counts reject fractional, negative and unsafe values', () => {
  for (const field of ['minMembers', 'maxMembers', 'maxEntries'] as const) {
    for (const value of [-1, .5, Number.MAX_SAFE_INTEGER + 1]) {
      const input = seed(); input[0][field] = value;
      assert.throws(() => new CompetitionStore(input), /must be a nonnegative safe integer/, `${field}=${value}`);
    }
  }
});
test('zero and positive integer capacities retain real HTTP projections', async () => {
  const input = seed();
  input[0].minMembers = 0; input[0].maxMembers = 10; input[0].maxEntries = 20;
  const app = buildApp([], { competitionStore: new CompetitionStore(input) });
  try {
    const response = await app.inject({url: `/v1/competitions/${input[0].id}`, headers: {authorization: `Bearer pf_live_${'A'.repeat(49)}`}});
    assert.equal(response.statusCode, 200);
    assert.equal(response.json().competition.minMembers, 0);
    assert.equal(response.json().competition.maxMembers, 10);
    assert.equal(response.json().competition.maxEntries, 20);
  } finally { await app.close(); }
});
