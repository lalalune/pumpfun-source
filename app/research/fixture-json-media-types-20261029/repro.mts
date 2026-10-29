import { buildApp } from '../../app/packages/backend/src/app.js';
import { writeFile } from 'node:fs/promises';

const cases = [
  ['json-object', 'application/json', { value: 'synthetic' }],
  ['json-suffix-object', 'application/example+json', { value: 'synthetic' }],
  ['plain-string', 'text/plain', 'synthetic text'],
  ['binary-buffer', 'application/octet-stream', Buffer.from([0, 255])],
  ['plain-object', 'text/plain', { value: 'synthetic' }],
  ['plain-array', 'text/plain', ['synthetic']],
  ['plain-number', 'text/plain', 3],
  ['plain-boolean', 'text/plain', false],
  ['plain-null', 'text/plain', null],
] as const;
const observations = [];
for (const [name, contentType, body] of cases) {
  const app = buildApp([{ method: 'GET', path: '/synthetic-body-type', status: 200, headers: { 'content-type': contentType, 'x-reconstruction-data-source': 'synthetic-mime-repro' }, body, source: 'synthetic-mime-repro' }]);
  try {
    const base = await app.listen({ host: '127.0.0.1', port: 0 });
    const result = await fetch(base + '/synthetic-body-type');
    observations.push({ name, declaredStatus: 200, declaredContentType: contentType, actualStatus: result.status, actualContentType: result.headers.get('content-type'), bytes: [...new Uint8Array(await result.arrayBuffer())] });
  } finally { await app.close(); }
}
await writeFile(new URL('./observed.json', import.meta.url), JSON.stringify({ scope: 'Actual loopback fixture replay only; no original/native compatibility claim', observations }, null, 2) + '\n');
console.log(JSON.stringify(observations.map(({ bytes, ...rest }) => ({ ...rest, bodyLength: bytes.length })), null, 2));
