// Local synthetic read-model reproduction; no upstream requests or auth claims.
import { buildApp } from '../../app/packages/backend/src/app.js';
import { UserStore, SYNTHETIC_SEED } from '../../app/packages/backend/src/users-store.js';
import { TEST_API_KEY } from '../../app/packages/backend/test/with-api-key.js';
import { validateAgainstSchema } from '../../app/packages/backend/src/schema-validator.js';
import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';

const root = new URL('../../', import.meta.url);
const spec = JSON.parse(await readFile(new URL('app/contracts/developer.openapi.json', root), 'utf8'));
const schema = spec.paths['/users'].get.responses['200'].content['application/json'].schema;
const sources = ['app/packages/backend/src/users-store.ts', 'app/packages/backend/src/users-routes.ts', 'app/packages/backend/src/app.ts', 'app/packages/backend/src/schema-validator.ts', 'app/contracts/developer.openapi.json'];
const sha = (bytes: Buffer) => createHash('sha256').update(bytes).digest('hex');
const inputs: Record<string, string> = {};
for (const path of sources) inputs[path] = sha(await readFile(new URL(path, root)));
const badge = { group_id: 'synthetic-group', username: 'synthetic_group', profile_image_url: null, role: 'MEMBER' };
const variants: [string, Record<string, unknown>][] = [
  ['valid-control', { kind: 'group', member_count: 3, group_badges: [badge] }],
  ['string-member-count', { member_count: '3' }],
  ['null-member-count', { member_count: null }],
  ['null-badges', { group_badges: null }],
  ['missing-badge-field', { group_badges: [{ group_id: 'synthetic-group', username: 'synthetic_group', role: 'MEMBER' }] }],
  ['boolean-badge-role', { group_badges: [{ ...badge, role: false }] }],
  ['extra-badge-field', { group_badges: [{ ...badge, extra: 'not-in-declared-schema' }] }],
];
const observations = [];
for (const [name, patch] of variants) {
  const seed = SYNTHETIC_SEED.map((row) => structuredClone(row));
  // Deliberately malformed local JSON-shaped metadata exercises admission.
  // No production credential or domain account is used.
  Object.assign(seed[0]!, patch);
  let store: UserStore;
  try {
    store = new UserStore(seed);
  } catch (error) {
    if (name === 'valid-control') throw error;
    assert.ok(error instanceof TypeError);
    assert.match(error.message, /^Invalid user (member_count|group_badges)$/);
    observations.push({ name, admission: 'rejected-before-listen', errorType: error.name, error: error.message, httpRequests: 0 });
    continue;
  }
  const app = buildApp([], { userStore: store });
  try {
    const address = await app.listen({ host: '127.0.0.1', port: 0 });
    assert.equal(new URL(address).hostname, '127.0.0.1');
    const response = await fetch(address + '/v1/users', { headers: { authorization: `Bearer ${TEST_API_KEY}` } });
    const body = await response.json();
    const issues = validateAgainstSchema(body, schema, '$', spec);
    observations.push({ name, status: response.status, dataSource: response.headers.get('x-reconstruction-data-source'), issues, body });
  } finally {
    await app.close();
  }
}
for (const path of sources) assert.equal(sha(await readFile(new URL(path, root))), inputs[path]);
assert.equal(observations[0]!.status, 200);
assert.equal(observations[0]!.issues.length, 0);
assert.ok(observations.slice(1).every((row) => 'admission' in row && row.admission === 'rejected-before-listen'));
const record = { scope: 'Actual loopback HTTP against maintained synthetic read model; captured specification is the schema oracle, not an upstream runtime', sourceInputs: inputs, observations, upstreamRequests: 0, authenticationCompatibilityClaimed: false, originalCompatibilityClaimed: false };
await writeFile(new URL('work/backend-group-metadata/after-http.json', root), JSON.stringify(record, null, 2) + '\n');
console.log(JSON.stringify(observations, null, 2));
