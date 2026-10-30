import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { CompetitionStore, type RawCompetition } from '../src/competitions-store.js';
import { buildApp } from '../src/app.js';

const group = (): RawCompetition => {
  const rows: RawCompetition[] = JSON.parse(readFileSync(new URL('../src/competitions-seed.json', import.meta.url), 'utf8'));
  return rows.find(row => row.kind === 'group')!;
};
test('a repeated roster member cannot inflate memberCount and duplicate contribution rows', () => {
  const input = group(), entry = input.entries.find(row => row.members?.length)!;
  entry.members!.push(structuredClone(entry.members![0]));
  assert.throws(() => new CompetitionStore([input]), /Duplicate competition roster member/);
});
test('real HTTP roster retains one row per distinct member and separate competition namespaces', async () => {
  const first = group(), entry = first.entries.find(row => row.members?.length)!;
  const second = structuredClone(first); second.id = '99999999-9999-4999-8999-999999999999'; second.slug += '-second';
  const app = buildApp([], {competitionStore: new CompetitionStore([first, second])});
  try {
    const response = await app.inject({url: `/v1/competitions/${first.id}/entries/${entry.entryId}`, headers: {authorization: `Bearer pf_live_${'A'.repeat(49)}`}});
    assert.equal(response.statusCode, 200);
    const result = response.json();
    assert.equal(result.entry.memberCount, entry.members!.length);
    assert.equal(new Set(result.members.map((row: {userId: string}) => row.userId)).size, result.members.length);
  } finally { await app.close(); }
});
