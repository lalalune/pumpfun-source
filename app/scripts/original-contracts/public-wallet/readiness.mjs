/** Read the captured readiness boundary as AST data; never execute it. */
import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { openCorpus, findNodes, exactlyOne, propertyName, literal, member, walk } from '../source.mjs';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const corpus = await openCorpus(root);
const topbar = await corpus.factory(400466, { source: 'evidence/web/objects/13c13db9eb86191b.js' });
const hydration = await corpus.factory(170450, { source: 'evidence/web/objects/994c0030bcc62017.js' });
assert.equal(topbar.provenance.sha256, 'b55e1d78341162edfc6c5ff1ba32c4b4faa3d0ade6de3a39f440fe39f2e9e5dd');
assert.equal(hydration.provenance.sha256, '72a61a3e662f4e2995ea53610e55b0658ec866cf82ddca6c904962252fe06ff7');
const one = (factory, predicate, label) => exactlyOne(findNodes(factory.node, predicate), label);
const importNode = one(topbar, n => n.type === 'VariableDeclarator' && n.id.name === 'e8' &&
  n.init?.type === 'CallExpression' && member(n.init.callee, 'e', 'i') && n.init.arguments[0]?.value === 170450, 'hydration import');
const hydrationValue = one(topbar, n => n.type === 'VariableDeclarator' && n.id.name === 'eQ' &&
  n.init?.type === 'CallExpression' && n.init.callee.type === 'SequenceExpression' &&
  member(n.init.callee.expressions[1], 'e8', 'f'), 'used hydration flag');
let consumer;
walk(topbar.node, (node, parents) => {
  if (node === hydrationValue) consumer = parents.findLast(n => n.type === 'FunctionDeclaration');
});
assert.ok(consumer, 'flag has a real caller function');
assert.equal(findNodes(consumer, n => n.type === 'VariableDeclarator' && n.id.name === 'e8').length, 0, 'no local import shadow');
const assigned = (name) => exactlyOne(findNodes(consumer, n => n.type === 'AssignmentExpression' && n.left.type === 'Identifier' && n.left.name === name && n.right.type === 'LogicalExpression'), `used ${name} assignment`);
const before = assigned('er');
assert.equal(before.right.type, 'LogicalExpression');
assert.equal(before.right.operator, '&&');
assert.equal(before.right.left.type, 'UnaryExpression');
assert.equal(before.right.left.operator, '!');
assert.equal(before.right.left.argument.name, 'eQ');
assert.equal(findNodes(before.right.right, n => n.type === 'Identifier' && n.name === 'aq').length, 1);
const after = assigned('ea');
assert.equal(after.right.type, 'LogicalExpression');
assert.equal(after.right.operator, '&&');
assert.equal(after.right.left.left.name, 'eQ');
assert.equal(after.right.left.right.operator, '!');
assert.equal(after.right.left.right.argument.name, 'eY');
const namedProperty = (node, name, value) => findNodes(node, n => n.type === 'ObjectProperty' && propertyName(n.key) === name && n.value?.value === value);
assert.equal(namedProperty(after, 'data-testid', 'sign-in-button').length, 1);
const prepaint = one(topbar, n => n.type === 'FunctionDeclaration' && n.id.name === 'aq', 'prepaint function');
assert.equal(namedProperty(prepaint, 'data-testid', 'sign-in-prepaint').length, 1);
const disabled = exactlyOne(findNodes(prepaint, n => n.type === 'ObjectProperty' && propertyName(n.key) === 'disabled'), 'prepaint disabled flag');
assert.equal(literal(disabled.value), true);
const store = one(hydration, n => n.type === 'CallExpression' && n.callee?.type === 'SequenceExpression' &&
  member(n.callee.expressions[1], 't', 'useSyncExternalStore'), 'actual hydration store call');
assert.deepEqual(store.arguments.map(n => n.name), ['r', 'a', 'i']);
for (const [name, value] of [['a', true], ['i', false]]) {
  const declaration = one(hydration, n => n.type === 'VariableDeclarator' && n.id.name === name, `snapshot ${name}`);
  assert.equal(declaration.init.type, 'ArrowFunctionExpression');
  assert.equal(literal(declaration.init.body), value);
}
const output = {
  scope: 'Captured physical source instances show pre-hydration disabled sign-in and post-hydration actionable sign-in. This does not recover authentication or assert a global runtime registration winner.',
  factories: [topbar.provenance, hydration.provenance],
  witnesses: [
    topbar.witness(importNode, 'Actual hydration-module import'),
    topbar.witness(hydrationValue, 'Used hydration flag in same caller as both branches'),
    topbar.witness(before, 'Pre-hydration fallback branch'),
    topbar.witness(prepaint, 'Disabled native prepaint button'),
    topbar.witness(after, 'Post-hydration signed-out actionable trigger'),
    hydration.witness(hydration.node, 'True client snapshot and false server snapshot'),
  ],
  localBoundary: 'AuthControl already tracks mounted to portal the chooser. Reuse that readiness for its trigger; no provider readiness, authReady, session, signing or original runtime equivalence claim.',
};
const serialized = JSON.stringify(output, null, 2) + '\n';
const target = new URL('../../../packages/frontend/PUBLIC-WALLET-READINESS-SOURCE.json', import.meta.url);
if (process.argv.includes('--check')) assert.equal(await readFile(target, 'utf8'), serialized);
else await writeFile(target, serialized);
console.log('Captured sign-in readiness verified: two physical factories, six AST witnesses; no captured code executed');
