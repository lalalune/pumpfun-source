import assert from 'node:assert/strict';
import test from 'node:test';
import { validateAgainstSchema, assertSchema } from '../packages/backend/src/schema-validator.ts';

const tree = { type: 'object', required: ['name'], properties: {
  name: { type: 'string' }, children: { type: 'array', items: { $ref: '#/tree' } },
} };
const validate = value => validateAgainstSchema(value, tree, '$', { tree });

test('valid recursive trees and repeated sibling objects remain valid', () => {
  const leaf = { name: 'leaf' };
  assert.deepEqual(validate({ name: 'root', children: [leaf, leaf, { name: 'branch', children: [leaf] }] }), []);
});

test('recursive schemas still validate nested properties', () => {
  const issues = validate({ name: 'root', children: [{ name: 42 }] });
  assert.equal(issues[0].path, '$.children[0].name');
  assert.match(issues[0].message, /expected type string/);
});

test('direct and mutual reference cycles produce issues rather than stack overflow', () => {
  for (const root of [{ a: { $ref: '#/a' } }, { a: { $ref: '#/b' }, b: { $ref: '#/a' } }]) {
    const issues = validateAgainstSchema('value', root.a, '$', root);
    assert.match(issues[0].message, /cyclic/);
    assert.throws(() => assertSchema('value', root.a, 'response', root), /response does not conform/);
  }
});

test('cyclic runtime payloads fail at the cycle path', () => {
  const value = { name: 'root', children: [] };
  value.children.push(value);
  const issues = validate(value);
  assert.equal(issues[0].path, '$.children[0]');
  assert.match(issues[0].message, /cyclic/);
});

test('branch cleanup allows valid alternatives and independent repeated checks', () => {
  const root = { loop: { $ref: '#/loop' } };
  for (const keyword of ['anyOf', 'oneOf']) {
    const schema = { [keyword]: [{ $ref: '#/loop' }, { type: 'string' }] };
    assert.deepEqual(validateAgainstSchema('ok', schema, '$', root), []);
  }
  const shared = { type: 'string' };
  assert.deepEqual(validateAgainstSchema('ok', { allOf: [shared, shared] }), []);
  assert.deepEqual(validate({ name: 'ok' }), []);
});

test('deep acyclic payloads have a bounded diagnostic', () => {
  let value = { name: 'leaf' };
  for (let i = 0; i < 200; i++) value = { name: 'branch', children: [value] };
  assert.ok(validate(value).some(issue => /nesting limit/.test(issue.message)));
});
