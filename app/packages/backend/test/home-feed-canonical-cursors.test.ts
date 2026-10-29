import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import test from 'node:test';
import { buildApp } from '../src/app.js';
import seed from '../src/home-feed-seed.json' with { type: 'json' };
import { HomeFeedStore } from '../src/home-feed-store.js';

// Local feed cursors use a public checksum, not an authentication secret.
function withTimestamp(token: string, timestamp: string): string {
  const payload = JSON.parse(Buffer.from(token.split('.')[0], 'base64url').toString('utf8'));
  payload.x[1] = timestamp;
  const body = Buffer.from(JSON.stringify(payload)).toString('base64url');
  const digest = createHash('sha256').update('pump-local-home-feed-cursor-v1\0')
    .update(body).digest().subarray(0, 16).toString('base64url');
  return `${body}.${digest}`;
}

test('count-new rejects noncanonical timestamps instead of losing same-time additions', async () => {
  for (const createdAt of ['1969-12-31T23:59:59.000Z', '1970-01-01T00:00:00.000Z', '1970-01-01T00:00:01.000Z']) {
    const data = structuredClone(seed);
    data.observedAt = '1970-01-01T12:00:00.000Z';
    const record = { ...data.records[0], createdAt, deleted: false, hidden: false };
    data.records = [{ ...record, calloutId: '00000000-0000-4000-8000-000000000002' }];
    const filters = { chains: [], assetClasses: [] };
    const head = new HomeFeedStore(data).newest({ filters, pageSize: 25 }).headToken!;
    data.records.push({ ...record, recordId: 'new-same-time-record', coinMint: 'NEW_TEST_MINT',
      calloutId: '00000000-0000-4000-8000-000000000001' });
    const app = buildApp([], { homeFeedStore: new HomeFeedStore(data) });
    try {
      const origin = await app.listen({ host: '127.0.0.1', port: 0 });
      const request = (token: string) => fetch(`${origin}/services/frontend/home-feed/new/count?since=${encodeURIComponent(token)}`);
      const valid = await request(head);
      assert.equal(valid.status, 200);
      assert.equal((await valid.json() as { newCount: number }).newCount, 1);
      const timestamp = (BigInt(Date.parse(createdAt)) * 1000n).toString();
      const aliases = timestamp.startsWith('-') ? [`-0${timestamp.slice(1)}`] : [`0${timestamp}`];
      if (timestamp === '0') aliases.push('-0', '-00');
      for (const alias of aliases) {
        const response = await request(withTimestamp(head, alias));
        const result = await response.json();
        assert.equal(response.status, 400, `${alias}: ${JSON.stringify(result)}`);
      }
    } finally {
      await app.close();
    }
  }
});
