import test from 'node:test';
import assert from 'node:assert/strict';
import {
  CompetitionStore,
  type RawCompetition,
  type RawEntry,
} from '../src/competitions-store.js';

const MEMBER_MEASURES = ['pnlUsd', 'realizedPnlUsd', 'unrealizedPnlUsd', 'buySpendSol', 'lastRefreshedAtMs'] as const;
const HIGHLIGHT_MEASURES = ['pnlUsd', 'realizedPnlUsd', 'unrealizedPnlUsd', 'buySpendUsd'] as const;

function baseEntry(): RawEntry {
  return {
    entryId: '22222222-2222-4000-8000-000000000001',
    participantId: 'nobody',
    registeredAt: '2024-01-01T00:00:00.000Z',
    struck: false,
    pnlUsd: 100,
    realizedPnlUsd: 60,
    unrealizedPnlUsd: 40,
    buySpendSol: 10,
    membersFresh: 1,
    lastRefreshedAtMs: 1000,
    members: [
      { userId: 'a', pnlUsd: 50, realizedPnlUsd: 30, unrealizedPnlUsd: 20, buySpendSol: 5, fresh: true, lastRefreshedAtMs: 1000 },
    ],
    highlightTokens: [
      {
        mint: 'mint1', chainId: 101, symbol: 'T', name: 'Tok', imageUri: null,
        pnlUsd: 70, realizedPnlUsd: 40, unrealizedPnlUsd: 30, buySpendUsd: 9,
        members: [
          { userId: 'a', pnlUsd: 70, realizedPnlUsd: 40, unrealizedPnlUsd: 30, buySpendUsd: 9 },
        ],
      },
    ],
  };
}

function seedWithEntry(entry: RawEntry): RawCompetition[] {
  return [
    {
      id: '11111111-1111-4000-8000-000000000001',
      slug: 'nested-arena',
      kind: 'group',
      title: 'Nested Arena',
      description: 'Seed for finite nested measures',
      prizeCopy: 'Winner takes all',
      imageUrl: null,
      prizes: [{ rankFrom: 1, rankTo: 1, amount: '1000' }],
      registrationOpensAt: null,
      registrationClosesAt: null,
      startsAt: null,
      endsAt: null,
      minMembers: 1,
      maxMembers: 4,
      maxEntries: 10,
      phase: 'live',
      isFinal: false,
      joinable: true,
      entries: [entry],
    },
  ];
}

test('competition nested seeds reject nonfinite measures before sorting or JSON serialization', () => {
  for (const measure of MEMBER_MEASURES) {
    for (const value of [NaN, Infinity, -Infinity]) {
      const entry = baseEntry();
      entry.members = [{ ...entry.members![0], [measure]: value }];
      assert.throws(
        () => new CompetitionStore(seedWithEntry(entry)),
        /finite/i,
        `member ${measure}: ${value}`,
      );
    }
  }
  for (const measure of HIGHLIGHT_MEASURES) {
    for (const value of [NaN, Infinity, -Infinity]) {
      const tokenEntry = baseEntry();
      tokenEntry.highlightTokens = [{ ...tokenEntry.highlightTokens![0], [measure]: value }];
      assert.throws(
        () => new CompetitionStore(seedWithEntry(tokenEntry)),
        /finite/i,
        `highlight token ${measure}: ${value}`,
      );
      const memberEntry = baseEntry();
      memberEntry.highlightTokens = [{
        ...memberEntry.highlightTokens![0],
        members: [{ ...memberEntry.highlightTokens![0].members[0], [measure]: value }],
      }];
      assert.throws(
        () => new CompetitionStore(seedWithEntry(memberEntry)),
        /finite/i,
        `highlight member ${measure}: ${value}`,
      );
    }
  }
});

test('finite losses, zero and fractional nested measures retain their supplied values', () => {
  const entry = baseEntry();
  entry.members = [{ ...entry.members![0], pnlUsd: -1.25, realizedPnlUsd: 0, unrealizedPnlUsd: -1.25 }];
  entry.highlightTokens = [{
    ...entry.highlightTokens![0],
    pnlUsd: -2.5,
    members: [{ ...entry.highlightTokens![0].members[0], pnlUsd: -2.5 }],
  }];
  const store = new CompetitionStore(seedWithEntry(entry));
  const detail = store.getEntryDetail('nested-arena', '22222222-2222-4000-8000-000000000001')!;
  assert.equal(detail.members[0].pnlUsd, -1.25);
  assert.equal(JSON.parse(JSON.stringify(detail.members[0])).pnlUsd, -1.25);
  const highlights = store.getEntryHighlights('nested-arena', '22222222-2222-4000-8000-000000000001')!;
  assert.equal(highlights.tokens[0].pnlUsd, -2.5);
  assert.equal(highlights.tokens[0].members[0].pnlUsd, -2.5);
  assert.equal(JSON.parse(JSON.stringify(highlights.tokens[0])).pnlUsd, -2.5);
});
