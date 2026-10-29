import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { buildApp } from '../src/app.js';
import { UserStore, SYNTHETIC_SEED } from '../src/users-store.js';
import { validateAgainstSchema } from '../src/schema-validator.js';
import { TEST_API_KEY } from './with-api-key.js';

const spec = JSON.parse(readFileSync(new URL('../../../contracts/developer.openapi.json', import.meta.url), 'utf8'));
const badge = { group_id: 'synthetic-group', username: 'synthetic_group', profile_image_url: null, role: 'MEMBER' };
function seedWith(patch: Record<string, unknown>) {
  const seed = SYNTHETIC_SEED.map((row) => structuredClone(row));
  // Deliberately malformed JSON-shaped fields test the runtime admission boundary.
  Object.assign(seed[0]!, patch);
  return seed;
}

test('rejects non-number or nonfinite group member metadata before indexing', () => {
  for (const member_count of ['3', null, false, {}, [], NaN, Infinity, -Infinity]) {
    assert.throws(() => new UserStore(seedWith({ member_count })), /Invalid user member_count/);
  }
  // The captured schema says number, with no integer or nonnegative constraint.
  for (const member_count of [undefined, 0, -1.5, Number.MAX_VALUE]) {
    const seed = seedWith({ member_count });
    assert.equal(new UserStore(seed).getById(seed[0]!.address)!.member_count, member_count);
  }
});

test('admits only the declared complete group badge shape and preserves open string roles', () => {
  const missing = Object.keys(badge).map((field) => {
    const value: Record<string, unknown> = { ...badge };
    delete value[field];
    return [value];
  });
  const sparse = Array(1);
  const invalid: unknown[] = [
    null, {}, 'badge', [null], [false], [[]], sparse,
    ...missing,
    [{ ...badge, group_id: null }],
    [{ ...badge, username: 3 }],
    [{ ...badge, profile_image_url: false }],
    [{ ...badge, role: false }],
    [{ ...badge, extra: 'undeclared' }],
  ];
  for (const group_badges of invalid) {
    assert.throws(() => new UserStore(seedWith({ group_badges })), /Invalid user group_badges/);
  }
  for (const group_badges of [undefined, [], [badge], [{ group_id: '', username: '', profile_image_url: '', role: 'future-role' }]]) {
    const seed = seedWith({ group_badges });
    assert.deepEqual(new UserStore(seed).getById(seed[0]!.address)!.group_badges, group_badges);
  }
});

test('real loopback profile reads retain valid group metadata and satisfy the captured response schemas', async () => {
  const metadata = { kind: 'group', member_count: -1.5, group_badges: [{ ...badge, role: 'future-role' }] };
  const seed = seedWith(metadata);
  const store = new UserStore(seed);
  const app = buildApp([], { userStore: store });
  const reads = [
    ['/v1/users', '/users'],
    [`/v1/users/${encodeURIComponent(seed[0]!.userId!)}`, '/users/{id}'],
    [`/v1/users/search-v2?searchTerm=${encodeURIComponent(seed[0]!.username!)}`, '/users/search-v2'],
  ];
  try {
    const origin = await app.listen({ host: '127.0.0.1', port: 0 });
    assert.equal(new URL(origin).hostname, '127.0.0.1');
    for (const [path, operation] of reads) {
      const response = await fetch(origin + path, { headers: { authorization: `Bearer ${TEST_API_KEY}` } });
      assert.equal(response.status, 200);
      assert.equal(response.headers.get('x-reconstruction-data-source'), 'synthetic-seed-play');
      const body = await response.json();
      const schema = spec.paths[operation!].get.responses['200'].content['application/json'].schema;
      assert.deepEqual(validateAgainstSchema(body, schema, '$', spec), []);
      const row = Array.isArray(body) ? body.find((user) => user.address === seed[0]!.address) : body;
      assert.ok(row);
      assert.equal(row.member_count, metadata.member_count);
      assert.deepEqual(row.group_badges, metadata.group_badges);
    }
    assert.deepEqual(store.getById(seed[0]!.address)!.group_badges, metadata.group_badges);
  } finally {
    await app.close();
  }
});
