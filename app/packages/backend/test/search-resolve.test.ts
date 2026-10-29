import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { buildApp } from './with-api-key.js';
import { type Fixture } from '../src/app.js';
import { UserStore, type User } from '../src/users-store.js';
import { assertSchema } from '../src/schema-validator.js';

const personId = '11111111-1111-4111-8111-111111111111';
const groupId = '22222222-2222-4222-8222-222222222222';
const missingId = '33333333-3333-4333-8333-333333333333';
const person: User = {
  userId: personId, address: '11111111111111111111111111111112',
  username: 'local-person', profile_image: null, bio: null,
  followers: 4, following: 2, x_username: null, is_pump_user: false,
  last_active_at: '2026-01-01T00:00:00Z', last_username_update_timestamp: 123,
};
const group: User = {
  ...person, userId: groupId, address: '', username: 'local-group',
  kind: 'group', member_count: 3, is_pump_user: true,
};
const spec = JSON.parse(readFileSync(new URL('../../../contracts/developer.openapi.json', import.meta.url), 'utf8'));
const schema = spec.paths['/search/resolve'].get.responses['200'].content['application/json'].schema;
function appWithAccounts() {
  return buildApp([], { userStore: new UserStore([person, group]) });
}
function resolved(user: User) {
  const { last_active_at: _activity, ...profile } = user;
  return {
    identifier: user.userId, kind: user.kind === 'group' ? 'squad' : 'user',
    chain: null, coin: null, user: profile,
    resolvedVia: user.kind === 'group' ? 'group' : 'cc_user', definitive: true,
  };
}

test('known UUID person and group resolve to the exact account DTO without presence data', async () => {
  const app = appWithAccounts();
  try {
    const response = await app.inject(`/v1/search/resolve?identifiers=${personId},${groupId}`);
    assert.equal(response.statusCode, 200);
    assert.deepEqual(response.json(), { results: [resolved(person), resolved(group)], degraded: [] });
    assertSchema(response.json(), schema, 'search resolve', spec);
    assert.deepEqual(Object.keys(response.json().results[0]).sort(),
      ['chain', 'coin', 'definitive', 'identifier', 'kind', 'resolvedVia', 'user']);
    assert.equal(response.headers['cache-control'], 'no-store');
    assert.equal(response.headers['x-reconstruction-data-source'], 'synthetic-seed-play');
    assert.equal(response.headers['x-reconstruction-compatibility'], 'unqualified');
  } finally { await app.close(); }
});

test('comma-separated, repeated and mixed identifiers preserve request order and duplicates', async () => {
  const app = appWithAccounts();
  try {
    for (const query of [
      `identifiers=${groupId},${personId},${groupId}`,
      `identifiers=${groupId}&identifiers=${personId}&identifiers=${groupId}`,
      `identifiers=${groupId},${personId}&%69dentifiers=${groupId}`,
    ]) {
      const response = await app.inject('/v1/search/resolve?' + query);
      assert.equal(response.statusCode, 200);
      assert.deepEqual(response.json().results, [resolved(group), resolved(person), resolved(group)]);
    }
  } finally { await app.close(); }
});

test('the documented count and string bounds are checked before resolving', async () => {
  const app = appWithAccounts();
  try {
    const five = Array(5).fill(personId).join(',');
    assert.equal((await app.inject('/v1/search/resolve?identifiers=' + five)).json().results.length, 5);
    for (const query of ['', '?identifiers=' + Array(6).fill(personId).join(','), '?identifiers=' + 'x'.repeat(129)]) {
      const response = await app.inject('/v1/search/resolve' + query);
      assert.equal(response.statusCode, 400);
      assert.equal(response.headers['x-reconstruction-data-source'], undefined);
    }
  } finally { await app.close(); }
});

test('unsupported, missing and wallet identifiers never produce a guessed or partial verdict', async () => {
  const app = appWithAccounts();
  try {
    for (const query of [
      `identifiers=${missingId}`, `identifiers=${person.address}`,
      `identifiers=${personId},${missingId}`, `identifiers=${personId}&viewerId=${groupId}`,
      'identifiers=user-001', 'identifiers=unknown', 'identifiers=',
    ]) {
      const response = await app.inject('/v1/search/resolve?' + query);
      assert.equal(response.statusCode, 501);
      assert.equal(response.json().error, 'COMPATIBILITY_NOT_IMPLEMENTED');
      assert.equal(response.json().results, undefined);
      assert.equal(response.headers['x-reconstruction-data-source'], undefined);
    }
  } finally { await app.close(); }
});

test('a UUID-shaped wallet alias is not silently treated as a canonical account ID', async () => {
  const app = buildApp([], { userStore: new UserStore([{ ...person, address: missingId }]) });
  try {
    assert.equal((await app.inject(`/v1/search/resolve?identifiers=${missingId}`)).statusCode, 501);
    assert.equal((await app.inject(`/v1/search/resolve?identifiers=${personId}`)).statusCode, 200);
  } finally { await app.close(); }
});

test('the API-key gate runs before resolver validation and native responses use the injected store', async () => {
  const app = appWithAccounts();
  const other = buildApp([], { userStore: new UserStore([{ ...person, username: 'other-local-snapshot' }]) });
  try {
    const denied = await app.inject({ url: '/v1/search/resolve', headers: { authorization: '' } });
    assert.equal(denied.statusCode, 401);
    assert.equal(denied.headers['x-reconstruction-data-source'], undefined);
    const url = `/v1/search/resolve?identifiers=${personId}`;
    assert.equal((await app.inject(url)).json().results[0].user.username, 'local-person');
    assert.equal((await other.inject(url)).json().results[0].user.username, 'other-local-snapshot');
  } finally { await app.close(); await other.close(); }
});

test('without an explicit user store the existing fixture and 501 harness remain intact', async () => {
  const fixture: Fixture = {
    method: 'GET', path: '/v1/search/resolve', query: { identifiers: personId },
    status: 200, body: { results: [], degraded: [] }, source: 'synthetic local test',
  };
  const replay = buildApp([fixture]);
  const unavailable = buildApp();
  const native = buildApp([fixture], { userStore: new UserStore([person]) });
  try {
    const url = `/v1/search/resolve?identifiers=${personId}`;
    assert.deepEqual((await replay.inject(url)).json(), fixture.body);
    assert.equal((await unavailable.inject(url)).statusCode, 501);
    assert.deepEqual((await native.inject(url)).json().results, [resolved(person)]);
  } finally { await replay.close(); await unavailable.close(); await native.close(); }
});
