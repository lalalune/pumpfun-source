import assert from 'node:assert/strict';
import { test } from 'node:test';
import { PositionsStore } from '../src/positions-store.js';
import { CalloutsStore } from '../src/callouts-store.js';
import { CalloutDiscussionsStore } from '../src/callout-discussions-store.js';
import { buildApp } from '../src/app.js';

const now = '2026-10-28T00:00:00.000Z';
const headers = {authorization: `Bearer pf_live_${'A'.repeat(49)}`};
test('malformed updatesLimit returns 400 before the perpetual availability refusal', async () => {
  const store = new PositionsStore({schemaVersion:1,dataSource:'synthetic',observedAt:now,subjects:[],coins:[],callouts:[],updates:[]});
  const app = buildApp([], {positionsStore: store});
  try {
    for (const value of ['abc', '-1', '21', '1.5', '']) {
      const response = await app.inject({url: `/v1/user-positions/person?mints=hlcore:BTC&updatesLimit=${value}`, headers});
      assert.equal(response.statusCode, 400, value);
      assert.equal(response.json().error, 'INVALID_QUERY');
    }
    const valid = await app.inject({url: '/v1/user-positions/person?mints=hlcore:BTC&updatesLimit=0', headers});
    assert.equal(valid.statusCode, 501);
    assert.equal(valid.json().reason, 'PERPETUAL_POSITIONS_DEFERRED');
  } finally { await app.close(); }
});
test('empty discussion linkage values return 400 before unavailable ranking', async () => {
  const callouts = new CalloutsStore({schemaVersion:1,dataSource:'synthetic',observedAt:now,authors:[],callouts:[],updates:[]});
  const discussions = new CalloutDiscussionsStore({schemaVersion:1,dataSource:'synthetic',observedAt:now,complete:true,calloutIds:[],authors:[],replies:[]}, callouts);
  const app = buildApp([], {calloutsStore: callouts, calloutDiscussionsStore: discussions});
  try {
    for (const query of ['sort=POSITION&beforeId=', 'sort=PNL&parentReplyId=', 'page=0&beforeId=']) {
      const response = await app.inject({url: `/v1/callout/00000000-0000-4000-8000-000000000000/replies?${query}`, headers});
      assert.equal(response.statusCode, 400, query);
      assert.equal(response.json().reason, 'CALLOUT_DISCUSSION_QUERY_INVALID');
    }
    const valid = await app.inject({url: '/v1/callout/00000000-0000-4000-8000-000000000000/replies?sort=POSITION', headers});
    assert.equal(valid.statusCode, 501);
    assert.equal(valid.json().reason, 'CALLOUT_DISCUSSION_RANKING_UNAVAILABLE');
  } finally { await app.close(); }
});
