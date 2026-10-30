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

test('a summary cannot disagree with the fresh flags of its explicit roster', () => {
  for (const membersFresh of [0, 1, 3, -1, 1.5]) {
    const group = squad();
    group.entries[0].membersFresh = membersFresh;
    assert.throws(() => new CompetitionStore([group]), /fresh member count.*roster/i,
      `summary ${membersFresh} versus two fresh members`);
  }
  const group = squad();
  group.entries[0].members![0].fresh = false;
  assert.throws(() => new CompetitionStore([group]), /fresh member count.*roster/i,
    'summary two versus one fresh and one stale member');
});

test('real board and detail reads preserve mixed/zero freshness and last-good legs', async () => {
  for (const freshFlags of [[true, false], [false, false], [true, true]]) {
    const group = squad();
    const raw = group.entries[0];
    raw.membersFresh = freshFlags.filter(Boolean).length;
    raw.members!.forEach((member, i) => { member.fresh = freshFlags[i]; });
    // Wallet absence is independent of whether a supplied scoring leg is fresh.
    raw.members![1].walletAddress = null;
    const app = buildApp([], { competitionStore: new CompetitionStore([group]) });
    try {
      const board = await app.inject({ url: `/v1/competitions/${group.id}`, headers });
      const detail = await app.inject({ url: `/v1/competitions/${group.id}/entries/${raw.entryId}`, headers });
      assert.equal(board.statusCode, 200);
      assert.equal(detail.statusCode, 200);
      const entry = board.json().leaderboard.entries[0];
      const result = detail.json();
      assert.equal(entry.membersFresh, result.members.filter((member: { fresh: boolean }) => member.fresh).length);
      assert.equal(result.entry.membersFresh, entry.membersFresh);
      assert.equal(entry.memberCount, 2);
      assert.deepEqual(result.members.map((member: { pnlUsd: number }) => member.pnlUsd), raw.members!.map(member => member.pnlUsd));
      assert.equal(result.members[1].walletAddress, null);
    } finally {
      await app.close();
    }
  }
});
