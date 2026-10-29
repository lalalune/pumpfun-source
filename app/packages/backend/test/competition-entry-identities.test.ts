import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { CompetitionStore, type RawCompetition } from '../src/competitions-store.js';
import { buildApp } from './with-api-key.js';

function seed(): RawCompetition[] {
  return JSON.parse(readFileSync(new URL('../src/competitions-seed.json', import.meta.url), 'utf8'));
}

test('rejects duplicate entry IDs inside one competition before ambiguous detail reads', () => {
  const row = seed().find(row => row.phase === 'live')!;
  row.entries[1].entryId = row.entries[0].entryId;
  assert.throws(() => new CompetitionStore([row]), /Duplicate competition entry identity/);
});

test('default leaderboard entries each resolve to their own HTTP detail', async () => {
  const rows = seed();
  const app = buildApp([], { competitionStore: new CompetitionStore(rows) });
  try {
    for (const row of rows) {
      const response = await app.inject(`/v1/competitions/${row.id}`);
      assert.equal(response.statusCode, 200);
      const board = response.json().leaderboard.entries;
      assert.equal(new Set(board.map((entry: {entryId: string}) => entry.entryId)).size, board.length);
      for (const entry of board) {
        const detail = await app.inject(`/v1/competitions/${row.id}/entries/${entry.entryId}`);
        assert.equal(detail.statusCode, 200);
        assert.equal(detail.json().entry.entryId, entry.entryId);
        assert.equal(detail.json().entry.participantId, entry.participantId);
        assert.equal(detail.json().entry.pnlUsd, entry.pnlUsd);
      }
    }
  } finally { await app.close(); }
});

test('entry IDs remain scoped to their competition, not a global namespace', async () => {
  const row = seed().find(row => row.phase === 'live')!;
  const other = structuredClone(row);
  other.id = '11111111-1111-4000-8000-000000000099';
  other.slug = 'separate-entry-namespace';
  other.entries[0].pnlUsd += 123;
  const app = buildApp([], { competitionStore: new CompetitionStore([row, other]) });
  try {
    for (const competition of [row, other]) {
      const response = await app.inject(`/v1/competitions/${competition.id}/entries/${competition.entries[0].entryId}`);
      assert.equal(response.statusCode, 200);
      assert.equal(response.json().entry.pnlUsd, competition.entries[0].pnlUsd);
    }
  } finally { await app.close(); }
});
