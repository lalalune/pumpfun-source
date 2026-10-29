import test from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { openCorpus } from '../scripts/original-contracts/source.mjs';
import { createSchemaExtractor } from '../scripts/original-contracts/schema.mjs';

const corpus = await openCorpus(fileURLToPath(new URL('..', import.meta.url)));
const sources = { 617159: 'evidence/web/objects/2b47dd0b38a1608f.js' };
const unsupported = /unsupported schema expression.*ArrowFunctionExpression/;

test('a rejected real captured helper cannot become an empty cached schema', async () => {
  const extractor = createSchemaExtractor(corpus, { sources });
  await assert.rejects(extractor.schema(617159, 'openEnum'), unsupported);
  await assert.rejects(extractor.schema(617159, 'openEnum'), unsupported);
  assert.throws(() => extractor.document({}), unsupported);
  assert.throws(() => extractor.witnesses(), unsupported);
});

test('parallel requests cannot publish a pending placeholder as a declaration', async () => {
  const extractor = createSchemaExtractor(corpus, { sources });
  const results = await Promise.allSettled([
    extractor.schema(617159, 'openEnum'),
    extractor.schema(617159, 'openEnum'),
  ]);
  assert.deepEqual(results.map(result => result.status), ['rejected', 'rejected']);
  for (const result of results) assert.match(result.reason.message, unsupported);
  assert.throws(() => extractor.document({}), unsupported);
});

test('documents and witnesses require the queued compilation to finish', async () => {
  const extractor = createSchemaExtractor(corpus, { sources });
  const result = extractor.schema(617159, 'openEnum').catch(error => error);
  let documentError;
  let witnessError;
  try { extractor.document({}); } catch (error) { documentError = error; }
  try { extractor.witnesses(); } catch (error) { witnessError = error; }
  await result;
  assert.match(documentError?.message ?? '', /in progress/);
  assert.match(witnessError?.message ?? '', /in progress/);
});

test('a fresh extractor still compiles real recursive schemas concurrently', async () => {
  const extractor = createSchemaExtractor(corpus);
  const [callout, reply] = await Promise.all([
    extractor.schema(421504, 'calloutDto'),
    extractor.schema(421504, 'calloutReplyDto'),
  ]);
  const document = extractor.document({ callout, reply });
  assert.equal(document.$defs['421504.calloutDto'].type, 'object');
  assert.equal(document.$defs['421504.calloutReplyDto'].properties.previewReplies.items.$ref,
    '#/$defs/421504.calloutReplyDto');
  assert.ok(extractor.witnesses().length > 0);
});
