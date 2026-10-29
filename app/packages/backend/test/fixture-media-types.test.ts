import test from 'node:test';
import assert from 'node:assert/strict';
import { buildApp } from '../src/app.js';

test('structured JSON fixture values retain declared success and explicit non-JSON media types over HTTP', async () => {
  for (const contentType of ['text/plain', 'application/octet-stream']) {
    for (const body of [{ value: 'synthetic' }, ['synthetic'], 3, false]) {
      const app = buildApp([{ method: 'GET', path: '/synthetic-body-type', status: 200, headers: { 'content-type': contentType }, body, source: 'synthetic-test' }]);
      try {
        const origin = await app.listen({ host: '127.0.0.1', port: 0 });
        const result = await fetch(origin + '/synthetic-body-type');
        assert.equal(result.status, 200);
        assert.equal(result.headers.get('content-type'), contentType);
        assert.deepEqual(JSON.parse(await result.text()), body);
      } finally { await app.close(); }
    }
  }
});

test('existing JSON defaults, raw text, null and raw byte fixture behavior stays intact', async () => {
  const rows = [
    { body: { value: 'synthetic' }, type: undefined, expected: '{"value":"synthetic"}' },
    { body: false, type: undefined, expected: 'false' },
    { body: 'synthetic', type: 'application/example+json', expected: '"synthetic"' },
    { body: null, type: 'application/json', expected: 'null' },
    { body: 'synthetic', type: 'text/plain', expected: 'synthetic' },
    { body: null, type: 'text/plain', expected: '' },
    { body: Buffer.from([0, 255]), type: 'application/octet-stream', expected: null },
  ];
  for (const { body, type, expected } of rows) {
    const app = buildApp([{ method: 'GET', path: '/synthetic-body-type', status: 200, headers: type ? { 'content-type': type } : undefined, body, source: 'synthetic-test' }]);
    try {
      const origin = await app.listen({ host: '127.0.0.1', port: 0 });
      const result = await fetch(origin + '/synthetic-body-type');
      assert.equal(result.status, 200);
      const bytes = Buffer.from(await result.arrayBuffer());
      if (expected === null) assert.deepEqual(bytes, body);
      else assert.equal(bytes.toString('utf8'), expected);
    } finally { await app.close(); }
  }
});
