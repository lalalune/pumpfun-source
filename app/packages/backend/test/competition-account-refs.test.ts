import test from 'node:test';
import assert from 'node:assert/strict';
import seed from '../src/competitions-seed.json' with { type: 'json' };
import { CompetitionStore, type RawCompetition } from '../src/competitions-store.js';
import { buildApp } from '../src/app.js';

const headers = { authorization: `Bearer pf_live_${'a'.repeat(49)}` };
function squad(): RawCompetition {
  const group = structuredClone(seed.find(row => row.kind === 'group')) as RawCompetition;
  group.entries = [group.entries[0]];
  return group;
}

test('competition account references require the string type used by the served DTO', () => {
  for (const value of [null, 0, false, [], {}]) {
    for (const field of ['participant', 'roster', 'highlight']) {
      const group = squad();
      const entry = group.entries[0];
      if (field === 'participant') entry.participantId = value as unknown as string;
      if (field === 'roster') entry.members![0].userId = value as unknown as string;
      if (field === 'highlight') entry.highlightTokens![0].members[0].userId = value as unknown as string;
      assert.throws(() => new CompetitionStore([group]), /must be a string/, field);
    }
  }
});

test('unknown and empty string keys retain fallback hydration and real HTTP projections', async () => {
  const group = squad();
  const entry = group.entries[0];
  entry.participantId = 'unknown-squad';
  entry.members!.forEach((member, i) => { member.userId = i === 0 ? '' : 'unknown-person'; });
  entry.highlightTokens![0].members.forEach((member, i) => {
    member.userId = entry.members![i].userId;
    member.pnlUsd = 1;
  });
  const app = buildApp([], { competitionStore: new CompetitionStore([group]) });
  try {
    const detail = await app.inject({ url: `/v1/competitions/${group.id}/entries/${entry.entryId}`, headers });
    const highlights = await app.inject({ url: `/v1/competitions/${group.id}/entries/${entry.entryId}/highlights`, headers });
    assert.equal(detail.statusCode, 200);
    assert.equal(highlights.statusCode, 200);
    assert.equal(detail.json().entry.participantId, 'unknown-squad');
    assert.equal(detail.json().entry.username, null);
    assert.deepEqual(detail.json().members.map((member: { userId: string }) => member.userId), ['', 'unknown-person']);
    assert.deepEqual(highlights.json().tokens[0].members.map((member: { userId: string }) => member.userId), ['', 'unknown-person']);
  } finally { await app.close(); }
});
