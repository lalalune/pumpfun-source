import assert from 'node:assert/strict';
import { test } from 'node:test';
import { buildApp, type Fixture } from '../src/app.js';

test('fixture replay retains the validated registration after caller mutation', async () => {
  const body = { rows: [{ label: 'recorded' }] };
  const fixture: Fixture = {
    method: 'GET', path: '/snapshot', query: { page: '1' }, status: 200,
    headers: { 'x-recorded': 'original' }, body, source: 'synthetic:fixture-snapshot',
  };
  const app = buildApp([fixture]);
  try {
    fixture.status = 503;
    fixture.headers!['x-recorded'] = 'changed';
    fixture.query!.page = '2';
    body.rows[0].label = 'changed';
    const response = await app.inject('/snapshot?page=1');
    assert.equal(response.statusCode, 200);
    assert.equal(response.headers['x-recorded'], 'original');
    assert.deepEqual(response.json(), { rows: [{ label: 'recorded' }] });
    assert.equal((await app.inject('/snapshot?page=2')).statusCode, 501);
  } finally { await app.close(); }
});
