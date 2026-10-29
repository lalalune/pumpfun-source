import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from '@babel/parser';
import { openCorpus, findNodes, exactlyOne, member, propertyName, sha256 } from './original-contracts/source.mjs';
import { normalizePlanner } from './verify-search-planner.mjs';

export const APP_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const KERNEL = 'packages/frontend/src/components/shell/search/recent-searches.mjs';
export const UI = 'packages/frontend/src/components/shell/search/SearchDialog.tsx';
export const PROOF = 'reconstruction/recent-searches/PROVENANCE.json';
const expect = (value, label) => { if (!value) throw Error('unqualified recent searches: ' + label); };
const unbound = (callee) => callee?.type === 'SequenceExpression' && callee.expressions[0]?.value === 0 ? callee.expressions[1] : callee;

export async function verifyRecentSearches(root = APP_ROOT) {
  const corpus = await openCorpus(root), factory = await corpus.factory(238128, { source: 'evidence/web/objects/ccb10fa3de5597c4.js' });
  const component = exactlyOne(findNodes(factory.node, (node) => node.type === 'FunctionDeclaration' && node.id.name === 'tg'), 'actual dialog component');
  const tuple = exactlyOne(findNodes(component, (node) => node.type === 'VariableDeclarator' && node.id.type === 'ArrayPattern' &&
    node.id.elements.map((entry) => entry?.name).join(',') === 'N,C,S'), 'actual history tuple');
  expect(tuple.init.type === 'CallExpression' && tuple.init.callee.type === 'ArrowFunctionExpression', 'history IIFE');
  const hook = tuple.init.callee;
  const storage = exactlyOne(findNodes(hook, (node) => node.type === 'CallExpression' && member(unbound(node.callee), 'eM', 'j')), 'actual storage hook');
  expect(storage.arguments[0]?.value === 'recently-searched-terms' && storage.arguments.length === 2 && storage.arguments[1].name === 'e', 'storage key/default boundary');
  const stored = exactlyOne(findNodes(hook, (node) => node.type === 'VariableDeclarator' && node.init === storage), 'actual storage result');
  expect(stored.id.type === 'ArrayPattern' && stored.id.elements.map((node) => node.name).join(',') === 'l,i', 'actual terms/write storage slots');
  const initial = exactlyOne(findNodes(hook, (node) => node.type === 'AssignmentExpression' && node.left.name === 'e' && node.right.type === 'ArrayExpression'), 'empty initial history');
  expect(initial.right.elements.length === 0, 'empty default');
  const add = exactlyOne(findNodes(hook, (node) => node.type === 'AssignmentExpression' && node.left.name === 't' && node.right.type === 'ArrowFunctionExpression'), 'used add callback');
  const clear = exactlyOne(findNodes(hook, (node) => node.type === 'AssignmentExpression' && node.left.name === 'a' && node.right.type === 'ArrowFunctionExpression'), 'used clear callback');
  for (const [name, from] of [['c', 't'], ['o', 'a']]) exactlyOne(findNodes(hook, (node) => node.type === 'VariableDeclarator' && node.id.name === name && node.init?.name === from), 'callback alias');
  const returned = exactlyOne(findNodes(hook, (node) => node.type === 'AssignmentExpression' && node.left.name === 's' && node.right.type === 'ArrayExpression'), 'returned history tuple');
  expect(returned.right.elements.map((entry) => entry.name).join(',') === 'l,c,o', 'actual tuple wiring');
  const kernelBytes = await readFile(path.join(root, KERNEL));
  const ast = parse(kernelBytes.toString('utf8'), { sourceType: 'module' });
  const keyDeclaration = exactlyOne(ast.program.body.filter((node) => node.type === 'ExportNamedDeclaration')
    .flatMap((node) => node.declaration?.declarations ?? []).filter((node) => node.id.name === 'RECENT_SEARCHES_KEY'), 'kernel storage key');
  expect(keyDeclaration.init?.value === storage.arguments[0].value, 'actual maintained storage key');
  const exported = (name) => exactlyOne(ast.program.body.filter((node) => node.type === 'ExportNamedDeclaration').map((node) => node.declaration)
    .filter((node) => node?.id?.name === name), 'kernel export ' + name);
  for (const [name, source, names, roles] of [
    ['createRecentSearchAdder', add.right, ['terms', 'write'], { terms: 'snapshot:terms', write: 'storage:write' }],
    ['createRecentSearchClearer', clear.right, ['write'], { write: 'storage:write' }],
  ]) {
    const maintained = exported(name);
    expect(maintained.params.map((node) => node.name).join(',') === names.join(',') && maintained.body.body.length === 1 &&
      maintained.body.body[0].type === 'ReturnStatement', 'constructor wiring');
    expect(JSON.stringify(normalizePlanner(source, { l: 'snapshot:terms', i: 'storage:write' })) ===
      JSON.stringify(normalizePlanner(maintained.body.body[0].argument, roles)), name + ' complete AST differs');
  }
  const historyList = exactlyOne(findNodes(factory.node, (node) => node.type === 'VariableDeclarator' && node.id.name === 'tu'), 'actual history list').init;
  const href = exactlyOne(findNodes(historyList, (node) => node.type === 'ObjectProperty' && propertyName(node.key) === 'href' &&
    node.value.type === 'TemplateLiteral' && node.value.quasis[0].value.cooked === '/explore?q='), 'actual text-history href');
  const maintainedHref = exported('recentSearchHref');
  expect(maintainedHref.params.length === 1 && maintainedHref.params[0].name === 'row' && maintainedHref.body.body.length === 1 &&
    JSON.stringify(normalizePlanner(href.value, { e: 'row', encodeURIComponent: 'global:uri' })) ===
      JSON.stringify(normalizePlanner(maintainedHref.body.body[0].argument, { row: 'row', encodeURIComponent: 'global:uri' })), 'href AST differs');
  const used = exactlyOne(findNodes(component, (node) => node.type === 'CallExpression' && node.arguments[0]?.name === 'tu'), 'actual history render consumer');
  const props = used.arguments[1];
  for (const [name, value] of [['terms', 'N'], ['onClear', 'S'], ['onNavigate', 'ea'], ['canExpand', 'ei']]) {
    expect(props.properties.some((node) => propertyName(node.key) === name && node.value.name === value), 'actual render prop ' + name);
  }
  const visibility = exactlyOne(findNodes(component, (node) => node.type === 'ConditionalExpression' && node.test.name === 'w' &&
    node.consequent.type === 'NullLiteral' && node.start < used.start && node.end > used.end), 'actual raw-query visibility');
  const submit = exactlyOne(findNodes(component, (node) => node.type === 'VariableDeclarator' && node.id.name === 'tB'), 'actual submit').init;
  const recorded = exactlyOne(findNodes(submit, (node) => node.type === 'CallExpression' && node.callee.name === 'C' && node.arguments[0]?.name === 't'), 'actual fallback record call');
  const trimmed = exactlyOne(findNodes(submit, (node) => node.type === 'VariableDeclarator' && node.id.name === 't'), 'actual trimmed submit value');
  expect(member(trimmed.init.callee, 'w', 'trim'), 'actual term admission');
  const imported = exactlyOne(findNodes(factory.node, (node) => node.type === 'VariableDeclarator' && node.id.name === 'eM'), 'actual storage import');
  expect(member(imported.init.callee, factory.runtime, 'i') && imported.init.arguments[0]?.value === 536925, 'storage dependency identity');
  const storageFactory = await corpus.factory(536925, { source: 'evidence/web/objects/d048caae282716b0.js' });
  const exports = exactlyOne(findNodes(storageFactory.node, (node) => node.type === 'CallExpression' && member(node.callee, storageFactory.runtime, 's')), 'storage exports').arguments[0].elements;
  const index = exports.findIndex((node) => node?.value === 'j'); expect(index >= 0 && exports[index + 1].value === 0, 'actual j export');
  const storageHook = exports[index + 2];
  const uiBytes = await readFile(path.join(root, UI)), ui = parse(uiBytes.toString('utf8'), { sourceType: 'module', plugins: ['typescript', 'jsx'] });
  const uiImports = exactlyOne(ui.program.body.filter((node) => node.type === 'ImportDeclaration' && node.source.value === './recent-searches.mjs'), 'actual UI history import');
  for (const name of ['RECENT_SEARCHES_KEY', 'createRecentSearchAdder', 'createRecentSearchClearer', 'recentSearchHref', 'decodeRecentSearches']) {
    expect(uiImports.specifiers.some((node) => node.imported?.name === name && node.local.name === name), 'UI import ' + name);
  }
  const bindings = [];
  for (const [name, constructor] of [['addRecentSearch', 'createRecentSearchAdder'], ['clearRecentSearches', 'createRecentSearchClearer']]) {
    const binding = exactlyOne(findNodes(ui, (node) => node.type === 'VariableDeclarator' && node.id.name === name && node.init?.callee?.name === constructor), 'actual UI constructor');
    expect(binding.init.arguments.map((node) => node.name).join(',') === (name === 'addRecentSearch' ? 'historyTerms,persistHistory' : 'persistHistory'), 'UI callback inputs');
    bindings.push(binding.init);
  }
  const recordedUI = exactlyOne(findNodes(ui, (node) => node.type === 'CallExpression' && node.callee.name === 'addRecentSearch' && node.arguments[0]?.name === 'normalized'), 'UI form record');
  const uiSubmit = exactlyOne(findNodes(ui, (node) => node.type === 'FunctionDeclaration' && node.id.name === 'onSubmit'), 'actual UI submit');
  const uiTrim = exactlyOne(findNodes(uiSubmit, (node) => node.type === 'VariableDeclarator' && node.id.name === 'normalized'), 'actual UI trimmed input');
  expect(JSON.stringify(normalizePlanner(trimmed.init, { w: 'input:query' })) ===
    JSON.stringify(normalizePlanner(uiTrim.init, { query: 'input:query' })), 'UI input trimming AST differs');
  exactlyOne(findNodes(uiSubmit, (node) => node.type === 'IfStatement' && node.test.name === 'normalized' &&
    node.consequent.type === 'ExpressionStatement' && node.consequent.expression === recordedUI), 'nonempty UI record admission');
  const link = exactlyOne(findNodes(ui, (node) => node.type === 'CallExpression' && node.callee.name === 'recentSearchHref'), 'used UI history href');
  const clearUI = exactlyOne(findNodes(ui, (node) => node.type === 'JSXAttribute' && node.name.name === 'onClick' && node.value?.expression?.name === 'clearRecentSearches'), 'used clear control');
  const visibleUI = exactlyOne(findNodes(ui, (node) => node.type === 'ConditionalExpression' && node.test.name === 'query' && node.consequent.type === 'NullLiteral'), 'raw UI query visibility');
  const selected = exactlyOne(findNodes(ui, (node) => node.type === 'CallExpression' && member(node.callee, 'historyTerms', 'slice')), 'bounded first-three UI selection');
  expect(selected.arguments.map((node) => node.value).join(',') === '0,3', 'local collapsed row bound');
  const collapsed = exactlyOne(findNodes(historyList, (node) => node.type === 'CallExpression' && member(node.callee, 'k', 'slice') &&
    node.arguments[0]?.value === 0 && node.arguments[1]?.value === 3), 'actual original collapsed selection');
  expect(JSON.stringify(normalizePlanner(collapsed, { k: 'terms' })) ===
    JSON.stringify(normalizePlanner(selected, { historyTerms: 'terms' })), 'collapsed selection AST differs');
  const roles = { createRecentSearchAdder: 'kernel:add', createRecentSearchClearer: 'kernel:clear', historyTerms: 'state:terms', persistHistory: 'storage:write',
    addRecentSearch: 'ui:add', normalized: 'ui:trimmed', recentSearchHref: 'kernel:href', term: 'row:term', query: 'state:query' };
  const uiBinding = [bindings, recordedUI, uiTrim.init, link, visibleUI.test, selected].map((node) => normalizePlanner(node, roles));
  const persist = exactlyOne(findNodes(ui, (node) => node.type === 'VariableDeclarator' && node.id.name === 'persistHistory'), 'actual storage writer').init;
  const writerCalls = persist.body.body[0].block.body.filter((node) => node.type === 'ExpressionStatement').map((node) => node.expression);
  expect(writerCalls[0].callee?.type === 'MemberExpression' && member(writerCalls[0].callee.object, 'window', 'localStorage') &&
    propertyName(writerCalls[0].callee.property) === 'setItem', 'write precedes publish');
  expect(writerCalls[1].callee.name === 'setHistoryTerms' && member(writerCalls.at(-1).callee, 'window', 'dispatchEvent'), 'publish precedes same-tab notification');
  const readerEffect = exactlyOne(findNodes(ui, (node) => node.type === 'CallExpression' && node.callee.name === 'useEffect' &&
    findNodes(node.arguments[0], (entry) => entry.type === 'CallExpression' && entry.callee.type === 'MemberExpression' &&
      member(entry.callee.object, 'window', 'localStorage') && propertyName(entry.callee.property) === 'getItem').length === 1), 'actual storage effect');
  const persistenceRoles = { window: 'dom:window', RECENT_SEARCHES_KEY: 'storage:key', JSON: 'global:JSON', StorageEvent: 'dom:StorageEvent',
    Event: 'dom:Event', useEffect: 'react:effect', decodeRecentSearches: 'local:decoder', setHistoryTerms: 'state:publish', setHistoryError: 'state:error', setHistoryReady: 'state:ready' };
  const persistence = [persist, readerEffect].map((node) => normalizePlanner(node, persistenceRoles));
  return { schemaVersion: 1, kernelSha256: sha256(kernelBytes), uiBindingSha256: sha256(JSON.stringify(uiBinding)), uiPersistenceSha256: sha256(JSON.stringify(persistence)), manifestSha256: corpus.anchors.manifestSha256,
    proofs: [factory.witness(tuple, 'actual history hook and tuple consumer'), factory.witness(add, 'complete used add operation'),
      factory.witness(clear, 'complete used clear operation'), factory.witness(href, 'actual text-query history destination'),
      factory.witness(collapsed, 'actual collapsed first-three capability, not a flag-default inference'),
      factory.witness(used, 'actual terms/clear/navigation/expansion consumer'), factory.witness(visibility.test, 'raw query visibility'),
      factory.witness(recorded, 'actual fallback submission records term'), factory.witness(trimmed, 'actual trimmed record input'),
      factory.witness(imported, 'actual storage dependency'), storageFactory.witness(storageHook, 'original general local-storage hook boundary')],
    limits: ['Full add/clear/href ASTs reuse the unchanged planner comparator. Captured bundles are never executed.',
      'Browser persistence/type-error UI is local integration. General hook deserialization/corruption, memoization and scheduling are not claimed equivalent.',
      'Only the collapsed first-three text-query history is presented. Feature-flag expansion and coin/user/squad enrichment remain unknown/unimplemented.'] };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const mode = process.argv[2]; expect(['--write', '--check'].includes(mode) && process.argv.length === 3, 'usage --write|--check');
    const output = JSON.stringify(await verifyRecentSearches(), null, 2) + '\n';
    if (mode === '--write') { await mkdir(path.join(APP_ROOT, 'reconstruction/recent-searches'), { recursive: true }); await writeFile(path.join(APP_ROOT, PROOF), output); }
    else expect(await readFile(path.join(APP_ROOT, PROOF), 'utf8') === output, 'saved proof differs');
    console.log('Recent searches: actual add/clear, text destination and used client boundaries verified without capture execution.');
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
