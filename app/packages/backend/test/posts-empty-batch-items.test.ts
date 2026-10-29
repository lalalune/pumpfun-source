import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { buildApp, TEST_API_KEY } from './with-api-key.js';

const ONE = '00000000-0000-4000-8000-000000000001';
const TWO = '00000000-0000-4000-8000-000000000002';

test('post batch validation retains empty items until the documented array is checked over HTTP', async t => {
  const spec = JSON.parse(readFileSync(new URL('../../../contracts/developer.openapi.json', import.meta.url), 'utf8'));
  const ids = spec.paths['/posts'].get.parameters.find((parameter: { name: string }) => parameter.name === 'ids').schema;
  assert.equal(ids.maxItems, 100);
  assert.equal(ids.minItems, 1);
  assert.equal(new RegExp(ids.items.pattern).test(''), false);
  const app = buildApp([]);
  t.after(() => app.close());
  const base = await app.listen({ host: '127.0.0.1', port: 0 });
  const get = (query: string) => fetch(`${base}/v1/posts?${query}`, {
    headers: { authorization: `Bearer ${TEST_API_KEY}` },
  });
  for (const query of [
    `ids=,${ONE}`, `ids=${ONE},`, `ids=${ONE},,${TWO}`,
    `ids=${ONE}&ids=`, `ids=${ONE}&ids=%20`,
    `ids=${ONE}${','.repeat(100)}`,
  ]) {
    await t.test(query, async () => {
      const response = await get(query);
      assert.equal(response.status, 400);
      assert.equal((await response.json() as { statusCode: number }).statusCode, 400);
    });
  }
  await t.test('valid mixed forms retain order, whitespace normalization and duplicate collapse', async () => {
    const response = await get(`ids=%20${TWO}%20,${ONE}&ids=${TWO}`);
    assert.equal(response.status, 200);
    assert.deepEqual((await response.json() as { posts: { postId: string }[] }).posts.map(row => row.postId), [TWO, ONE]);
  });
  await t.test('exactly100 nonempty UUIDs still succeed', async () => {
    const response = await get(`ids=${Array(100).fill(ONE).join(',')}`);
    assert.equal(response.status, 200);
    assert.equal((await response.json() as { posts: unknown[] }).posts.length, 1);
  });
});
