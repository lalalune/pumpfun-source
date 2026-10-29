import test from 'node:test';
import assert from 'node:assert/strict';
import {
  CompetitionStore,
  type RawCompetition,
} from '../src/competitions-store.js';

const HEADER = ['minMembers', 'maxMembers', 'maxEntries'] as const;
const PRIZE = ['rankFrom', 'rankTo'] as const;

function seedWithHeader(
  headerOverrides: Partial<Record<(typeof HEADER)[number], number>> = {},
  prizeOverrides: Partial<Record<(typeof PRIZE)[number], number>> = {},
): RawCompetition[] {
  return [
    {
      id: '11111111-1111-4000-8000-000000000001',
      slug: 'finite-arena',
      kind: 'person',
      title: 'Finite Arena',
      description: 'Seed for finite header measures',
      prizeCopy: 'Winner takes all',
      imageUrl: null,
      prizes: [{ rankFrom: 1, rankTo: 1, amount: '1000', ...prizeOverrides }],
      registrationOpensAt: null,
      registrationClosesAt: null,
      startsAt: null,
      endsAt: '2024-02-01T00:00:00.000Z',
      minMembers: 1,
      maxMembers: 1,
      maxEntries: 10,
      phase: 'ended',
      isFinal: true,
      joinable: false,
      entries: [
        {
          entryId: '22222222-2222-4000-8000-000000000001',
          participantId: 'nobody',
          registeredAt: '2024-01-01T00:00:00.000Z',
          struck: false,
          pnlUsd: 100,
          realizedPnlUsd: 60,
          unrealizedPnlUsd: 40,
          buySpendSol: 10,
          membersFresh: 0,
          lastRefreshedAtMs: 1000,
        },
      ],
      ...headerOverrides,
    },
  ];
}

test('competition header seeds reject nonfinite counts and prize ranks before serving', () => {
  for (const field of HEADER) {
    for (const value of [NaN, Infinity, -Infinity]) {
      assert.throws(
        () => new CompetitionStore(seedWithHeader({ [field]: value })),
        /finite/i,
        `${field}: ${value}`,
      );
    }
  }
  for (const field of PRIZE) {
    for (const value of [NaN, Infinity, -Infinity]) {
      assert.throws(
        () => new CompetitionStore(seedWithHeader({}, { [field]: value })),
        /finite/i,
        `${field}: ${value}`,
      );
    }
  }
});

test('finite header counts and prize ranks retain their supplied values', () => {
  const store = new CompetitionStore(seedWithHeader());
  const view = store.getByIdOrSlug('finite-arena')!.competition;
  assert.equal(view.minMembers, 1);
  assert.equal(view.maxMembers, 1);
  assert.equal(view.maxEntries, 10);
  assert.equal(JSON.parse(JSON.stringify(view)).minMembers, 1);
  assert.equal(view.winners.length, 1);
  assert.equal(view.winners[0].prize, '1000');
});
