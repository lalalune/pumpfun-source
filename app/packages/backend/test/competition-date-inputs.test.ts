import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { CompetitionStore, type RawCompetition } from '../src/competitions-store.js';
import { buildApp } from './with-api-key.js';

const seed = JSON.parse(readFileSync(new URL('../src/competitions-seed.json', import.meta.url), 'utf8')) as RawCompetition[];
const nullableDates = ['registrationOpensAt', 'registrationClosesAt', 'startsAt', 'endsAt'] as const;

for (const field of nullableDates) {
  for (const value of ['', 'not-a-date', '999999-12-31T00:00:00Z']) {
    test(`rejects unparseable competition ${field}=${JSON.stringify(value)}`, () => {
      const row = structuredClone(seed[0]);
      row[field] = value;
      assert.throws(() => new CompetitionStore([row]), /Competition .*date/);
    });
  }
}

for (const value of ['not-a-date', '', null]) {
  test(`rejects an unusable registration tie-break date ${JSON.stringify(value)}`, () => {
    const row = structuredClone(seed.find(row => row.entries.length > 1)!);
    Object.assign(row.entries[0], { registeredAt: value });
    assert.throws(() => new CompetitionStore([row]), /Competition entry registeredAt.*date/);
  });
}

test('valid default dates retain finite HTTP leaderboard windows', async () => {
  const app = buildApp([], { competitionStore: new CompetitionStore(seed) });
  try {
    for (const row of seed) {
      const response = await app.inject(`/v1/competitions/${row.id}`);
      assert.equal(response.statusCode, 200);
      const body = response.json();
      assert.equal(body.leaderboard.startSec, row.startsAt === null ? 0 : Math.trunc(Date.parse(row.startsAt) / 1000));
      assert.ok(Number.isFinite(body.leaderboard.endSec));
    }
  } finally { await app.close(); }
});

test('nullable schedule dates remain supported without invented windows', async () => {
  const row = structuredClone(seed.find(row => row.isFinal)!);
  for (const field of nullableDates) row[field] = null;
  const app = buildApp([], { competitionStore: new CompetitionStore([row]) });
  try {
    const response = await app.inject(`/v1/competitions/${row.id}`);
    assert.equal(response.statusCode, 200);
    assert.equal(response.json().leaderboard.startSec, 0);
    assert.equal(response.json().leaderboard.endSec, 0);
  } finally { await app.close(); }
});
