import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { buildApp, TEST_API_KEY } from './with-api-key.js';
import { UserStore } from '../src/users-store.js';

test('verified-profile ID length follows the declared Unicode-character limit over real HTTP', async t => {
  const spec = JSON.parse(readFileSync(new URL('../../../contracts/developer.openapi.json', import.meta.url), 'utf8'));
  const schema = spec.paths['/profiles/verified'].post.requestBody.content['application/json'].schema.properties.ids.items;
  assert.deepEqual(schema, { type: 'string', maxLength: 64 });
  const app = buildApp([], { userStore: new UserStore([]) });
  t.after(() => app.close());
  const base = await app.listen({ port: 0, host: '127.0.0.1' });
  const send = (id: string) => fetch(`${base}/v1/profiles/verified`, {
    method: 'POST',
    headers: { authorization: `Bearer ${TEST_API_KEY}`, 'content-type': 'application/json' },
    body: JSON.stringify({ ids: [id] }),
  });
  // Unknown IDs remain false; this does not add any identity-resolution behavior.
  for (const id of ['a'.repeat(64), '界'.repeat(64), '🚀'.repeat(64), 'a'.repeat(62) + '🚀🚀']) {
    const response = await send(id);
    assert.equal(response.status, 201, `${[...id].length} characters / ${id.length} UTF-16 units`);
    assert.deepEqual(await response.json(), { [id]: false });
  }
  for (const id of ['a'.repeat(65), '界'.repeat(65), '🚀'.repeat(65)]) {
    const response = await send(id);
    assert.equal(response.status, 400);
    assert.equal((await response.json() as { error: string }).error, 'INVALID_ID');
  }
});
