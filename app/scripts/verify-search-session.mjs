import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from '@babel/parser';
import { openCorpus, findNodes, exactlyOne, member, propertyName, sha256 } from './original-contracts/source.mjs';

export const APP_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const ADAPTER = 'reconstruction/search-session/session.mjs';
export const PROOF = 'reconstruction/search-session/PROVENANCE.json';
const SOURCES = ['evidence/web/objects/dba17a249156c6ff.js', 'evidence/web/objects/767cc801e3f88f8b.js'];
const expect = (condition, message) => { if (!condition) throw new Error(`unqualified search session: ${message}`); };
const functions = new Set(['ArrowFunctionExpression', 'FunctionExpression', 'FunctionDeclaration', 'ObjectMethod']);
const ignored = new Set(['start', 'end', 'loc', 'extra', 'leadingComments', 'trailingComments', 'innerComments']);
const unbound = (callee) => callee?.type === 'SequenceExpression' && callee.expressions.length === 2 &&
  callee.expressions[0].value === 0 ? callee.expressions[1] : callee;

// Lexical alpha comparison only: preserve statements, declaration kinds,
// operators, values, branches, receiver calls and ordering. Qualified imported
// call targets map to their explicit maintained capabilities; !0/!1 are booleans.
export function normalizeSession(node, roles, imports = {}) {
  let next = 0;
  const unresolved = new Set();
  function bind(pattern, scope) {
    if (pattern.type === 'Identifier') scope.set(pattern.name, `local:${next++}`);
    else if (pattern.type === 'AssignmentPattern') bind(pattern.left, scope);
    else if (pattern.type === 'ObjectPattern') for (const item of pattern.properties) bind(item.value, scope);
    else throw new Error(`unsupported session binding: ${pattern.type}`);
  }
  function lookup(name, scopes) {
    for (let i = scopes.length - 1; i >= 0; i--) if (scopes[i].has(name)) return scopes[i].get(name);
    if (!roles[name]) unresolved.add(name);
    return roles[name] ?? `UNRESOLVED:${name}`;
  }
  function visit(value, scopes = [], parent, key) {
    if (!value || typeof value !== 'object') return value;
    if (Array.isArray(value)) return value.map((item) => visit(item, scopes, parent, key));
    if (value.type === 'UnaryExpression' && value.operator === '!' && value.argument.type === 'NumericLiteral' && [0, 1].includes(value.argument.value)) {
      return { type: 'BooleanLiteral', value: !value.argument.value };
    }
    if (value.type === 'MemberExpression' && !value.computed && value.object.type === 'Identifier') {
      const target = imports[`${value.object.name}.${propertyName(value.property)}`];
      if (target) return { type: 'Identifier', name: target };
    }
    if (value.type === 'SequenceExpression' && value.expressions.length === 2 && value.expressions[0].type === 'NumericLiteral' && value.expressions[0].value === 0) {
      const target = visit(value.expressions[1], scopes);
      expect(target.type === 'Identifier' && target.name.startsWith('operation:'), 'qualified unbound import');
      return target;
    }
    let current = scopes;
    if (functions.has(value.type)) {
      const scope = new Map();
      for (const parameter of value.params) bind(parameter, scope);
      current = [...scopes, scope];
    } else if (value.type === 'CatchClause') {
      const scope = new Map(); bind(value.param, scope); current = [...scopes, scope];
    } else if (value.type === 'BlockStatement') {
      const scope = new Map();
      for (const statement of value.body) if (statement.type === 'VariableDeclaration') {
        for (const entry of statement.declarations) bind(entry.id, scope);
      }
      current = [...scopes, scope];
    }
    if (value.type === 'Identifier') {
      const property = (key === 'key' && ['ObjectProperty', 'ObjectMethod'].includes(parent?.type) && !parent.computed) ||
        (key === 'property' && ['MemberExpression', 'OptionalMemberExpression'].includes(parent?.type) && !parent.computed);
      return { type: 'Identifier', name: property ? value.name : lookup(value.name, current) };
    }
    const result = {};
    for (const [childKey, child] of Object.entries(value)) if (!ignored.has(childKey)) {
      result[childKey] = childKey === 'shorthand' && value.type === 'ObjectProperty' ? false : visit(child, current, value, childKey);
    }
    return result;
  }
  const result = visit(node);
  if (unresolved.size) throw new Error(`unresolved session bindings: ${[...unresolved].join(', ')}`);
  return result;
}

const table = [
  { offset: 'c', limit: 'f', ipfsPrefix: 'ef', socialTerminal: 'Q', requestKeyRef: 'ea', loadedKeyRef: 'es',
    entries: 'M', store: 'L', sequenceRef: 'ep', abortRef: 'ew', setCoins: 'B', setPageSize: 'ee',
    setHasNextPage: 'z', setLoadedKey: 'en', setErrorKey: 'ei', setLoading: 'J', setServedCoins: 'V', emptyCoins: 'N',
    client: 'g', read: 'm', normalize: 'O', board: 'R' },
  { offset: 'c', limit: 'd', ipfsPrefix: 'ed', socialTerminal: '$', requestKeyRef: 'en', loadedKeyRef: 'eo',
    entries: 'j', store: 'P', sequenceRef: 'ew', abortRef: 'ey', setCoins: 'Q', setPageSize: 'ee',
    setHasNextPage: 'Z', setLoadedKey: 'el', setErrorKey: 'ei', setLoading: 'J', setServedCoins: 'K', emptyCoins: '_',
    client: 'x', read: 'g', normalize: 'A', board: 'N' },
];
const globalRoles = { JSON: 'global:JSON', Error: 'global:Error', fetch: 'operation:fetch', AbortController: 'global:AbortController' };
const portNames = ['offset', 'limit', 'ipfsPrefix', 'socialTerminal', 'requestKeyRef', 'loadedKeyRef', 'entries', 'store',
  'sequenceRef', 'abortRef', 'setCoins', 'setPageSize', 'setHasNextPage', 'setLoadedKey', 'setErrorKey', 'setLoading', 'setServedCoins', 'emptyCoins'];

function topDeclaration(factory, name) {
  return exactlyOne(factory.node.body.body.flatMap((statement) => statement.type === 'VariableDeclaration' ? statement.declarations : [])
    .filter((entry) => entry.id.type === 'Identifier' && entry.id.name === name), `top-level ${name}`);
}

function exported(factory, name) {
  const array = exactlyOne(findNodes(factory.node, (node) => node.type === 'CallExpression' && member(node.callee, factory.runtime, 's') &&
    node.arguments[0]?.type === 'ArrayExpression' && node.arguments[0].elements.some((item) => item?.value === name)), `export ${name}`).arguments[0].elements;
  const i = array.findIndex((item) => item?.value === name);
  expect(array[i + 1]?.value === 0, `direct export ${name}`);
  const value = array[i + 2];
  return value.type === 'Identifier' ? topDeclaration(factory, value.name).init : value;
}

function diff(a, b, location = '') {
  if (a === b) return null;
  if (!a || !b || typeof a !== 'object' || typeof b !== 'object') return `${location}: ${JSON.stringify(a)} != ${JSON.stringify(b)}`;
  for (const key of new Set([...Object.keys(a), ...Object.keys(b)])) {
    const error = diff(a[key], b[key], `${location}.${key}`); if (error) return error;
  }
  return null;
}

export async function verifySession(root = APP_ROOT) {
  const corpus = await openCorpus(root), bytes = await readFile(path.join(root, ADAPTER));
  const ast = parse(bytes.toString('utf8'), { sourceType: 'module' });
  const local = (name) => exactlyOne(ast.program.body.filter((statement) => statement.type === 'ExportNamedDeclaration')
    .flatMap((statement) => statement.declaration?.type === 'FunctionDeclaration' ? [statement.declaration] : statement.declaration?.declarations ?? [])
    .filter((entry) => (entry.id?.name === name)), `adapter ${name}`);
  const proofs = [], consumerBindings = [], stateBindings = [];
  function compare(label, factory, original, sourceRoles, sourceImports, maintained, adapterRoles, adapterImports = {}) {
    const expected = normalizeSession(original, sourceRoles, sourceImports), actual = normalizeSession(maintained, adapterRoles, adapterImports);
    const error = diff(expected, actual); expect(!error, `${label} AST differs: ${error}`);
    proofs.push({ ...factory.witness(original, label), normalizedSha256: sha256(JSON.stringify(expected)) });
  }
  const factory = local('createSearchExecutor');
  const operation = factory.body.body[0].argument;
  expect(factory.body.body.length === 1 && operation.type === 'ArrowFunctionExpression' && operation.async, 'executor factory boundary');
  expect(factory.params.length === 2 && factory.params.every((entry) => entry.type === 'ObjectPattern'), 'explicit executor snapshots/capabilities');
  expect(JSON.stringify(factory.params[0].properties.map((entry) => [propertyName(entry.key), entry.value.name])) ===
    JSON.stringify(['offset', 'limit', 'ipfsPrefix', 'socialTerminal'].map((name) => [name, name])), 'snapshot capability wiring');
  const expectedPorts = [...portNames.filter((name) => !['offset', 'limit', 'ipfsPrefix', 'socialTerminal'].includes(name)),
    'getContractClient', 'fetchResponse', 'parseBoard', 'now', 'AbortController'];
  expect(new Set(factory.params[1].properties.map((entry) => propertyName(entry.key))).size === expectedPorts.length &&
    factory.params[1].properties.length === expectedPorts.length, 'capability extent');
  for (const name of expectedPorts) {
    const value = exactlyOne(factory.params[1].properties.filter((entry) => propertyName(entry.key) === name), name).value;
    if (name === 'now') expect(value.type === 'AssignmentPattern' && value.left.name === 'now' && member(value.right, 'Date', 'now'), 'clock default');
    else if (name === 'AbortController') expect(value.type === 'AssignmentPattern' && value.left.name === 'Controller' && member(value.right, 'globalThis', 'AbortController'), 'AbortController default');
    else expect(value.type === 'Identifier' && value.name === name, 'capability wiring ' + name);
  }
  const adapterRoles = { ...globalRoles, Controller: 'global:AbortController', fetchResponse: 'operation:fetch',
    getContractClient: 'operation:client', readSearchCoins: 'operation:read', normalizeSearchCoins: 'operation:normalize',
    parseBoard: 'operation:board', now: 'operation:clock' };
  for (const name of portNames) adapterRoles[name] = `port:${name}`;
  for (let i = 0; i < SOURCES.length; i++) {
    const source = await corpus.factory(379705, { source: SOURCES[i] }), names = table[i];
    const executor = exactlyOne(findNodes(source.node, (node) => node.type === 'ArrowFunctionExpression' && node.async &&
      findNodes(node, (child) => child.type === 'StringLiteral' && child.value === 'Failed to fetch coins').length === 1), 'shared executor');
    const roles = { ...globalRoles }, imports = { 'Date.now': 'operation:clock',
      [`${names.client}.f`]: 'operation:client', [`${names.read}.l`]: 'operation:read',
      [`${names.normalize}.f`]: 'operation:normalize', [`${names.board}.$`]: 'operation:board' };
    for (const name of portNames) roles[names[name]] = `port:${name}`;
    for (const [name, id] of [['client', 759257], ['read', 997887], ['normalize', 493025], ['board', 583448]]) {
      const declaration = topDeclaration(source, names[name]);
      expect(member(declaration.init?.callee, source.runtime, 'i') && declaration.init.arguments[0]?.value === id, `actual ${name} import`);
      proofs.push(source.witness(declaration, `executor ${name} import`));
    }
    compare('complete shared executor', source, executor, roles, imports, operation, adapterRoles);
    const declaration = exactlyOne(findNodes(source.node, (node) => node.type === 'VariableDeclarator' && node.init?.type === 'CallExpression' && node.init.arguments[0] === executor), 'executor callback binding');
    const search = exactlyOne(findNodes(source.node, (node) => node.type === 'ArrowFunctionExpression' && node.async &&
      findNodes(node, (child) => child.type === 'StringLiteral' && child.value === 'GET /coins/search-v2').length === 1), 'owning search callback');
    const call = search.body.body.at(-1).expression;
    expect(call.type === 'AwaitExpression' && call.argument.callee.name === declaration.id.name, 'actual awaited executor consumer');
    const args = call.argument.arguments;
    expect(args.length === 6 && args[1].type === 'UnaryExpression' && args[1].operator === '!' && args[1].argument.value === 1 &&
      args[3].type === 'UnaryExpression' && args[3].operator === '!' && args[3].argument.value === 1, 'search showLoading/preserveExisting false');
    expect(args[2].type === 'Identifier' && args[2].name === search.params[0].properties[1].value.left.name, 'search local filtering argument');
    consumerBindings.push(source.witness(call, 'actual search callback awaits shared executor with filter/settled callbacks'));
    for (const name of ['setCoins', 'setPageSize', 'setHasNextPage', 'setLoadedKey', 'setErrorKey', 'setLoading', 'setServedCoins']) {
      const state = exactlyOne(findNodes(source.node, (node) => node.type === 'VariableDeclarator' && node.id.type === 'ArrayPattern' &&
        node.id.elements[1]?.name === names[name] && member(unbound(node.init?.callee), i === 0 ? 'l' : 'a', 'useState')), `actual ${name} state setter`);
      stateBindings.push({ port: name, ...source.witness(state, 'React useState binding') });
    }
    for (const [name, init] of [['sequenceRef', 0], ['abortRef', null]]) {
      const ref = exactlyOne(findNodes(source.node, (node) => node.type === 'VariableDeclarator' && node.id.name === names[name]), name);
      expect(member(unbound(ref.init?.callee), i === 0 ? 'l' : 'a', 'useRef') &&
        (init === null ? ref.init.arguments[0].type === 'NullLiteral' : ref.init.arguments[0].value === init), name + ' initialization');
      stateBindings.push({ port: name, ...source.witness(ref, 'React useRef binding') });
    }
    const entries = topDeclaration(source, names.entries), store = topDeclaration(source, names.store), empty = topDeclaration(source, names.emptyCoins);
    expect(entries.init.type === 'NewExpression' && entries.init.callee.name === 'Map' && empty.init.type === 'ArrayExpression' && empty.init.elements.length === 0, 'module cache/empty array');
    const cache = local('createSearchCache');
    expect(cache.body.body.length === 3 && cache.body.body[0].declarations[0].id.name === 'entries' &&
      cache.body.body[0].declarations[0].init.type === 'NewExpression' && cache.body.body[0].declarations[0].init.callee.name === 'Map' &&
      cache.body.body[2].type === 'ReturnStatement' && cache.body.body[2].argument.properties.map((entry) => entry.value.name).join(',') === 'entries,store', 'cache initialization/wiring');
    const maintained = cache.body.body[1].declarations[0].init;
    compare('cache write/eviction operation', source, store.init,
      { [names.entries]: 'port:entries' }, { 'Date.now': 'operation:clock' }, maintained,
      { entries: 'port:entries', now: 'operation:clock' });
    proofs.push(source.witness(entries, 'module-wide cache declaration'));
  }
  const uri = await corpus.factory(426091, { source: 'evidence/web/objects/92f43c917bbc50e2.js' });
  const uriOperation = exported(uri, 'r');
  compare('URI rewrite body', uri, uriOperation, { T: 'constant:fallback' }, {},
    { ...uriOperation, params: local('normalizeSearchUri').params, body: local('normalizeSearchUri').body }, { FALLBACK_IMAGE: 'constant:fallback' });
  const fallback = exported(uri, 'A');
  expect(fallback.value === local('FALLBACK_IMAGE').init.value, 'exact captured fallback URI');
  proofs.push(uri.witness(fallback, 'fallback URI constant'));
  const normalizer = await corpus.factory(493025, { source: 'evidence/web/objects/fd402d4185b44ce9.js' });
  const uriImport = topDeclaration(normalizer, 't');
  expect(member(uriImport.init?.callee, normalizer.runtime, 'i') && uriImport.init.arguments[0]?.value === 426091, 'actual URI normalizer import');
  proofs.push(normalizer.witness(uriImport, 'coin normalizer URI import'));
  const transform = exported(normalizer, 'f');
  compare('coin normalization body', normalizer, transform, { i: 'constant:httpRegex' }, { 't.r': 'operation:uri', 't.A': 'constant:fallback' },
    { ...transform, params: local('normalizeSearchCoins').params, body: local('normalizeSearchCoins').body },
    { normalizeSearchUri: 'operation:uri', FALLBACK_IMAGE: 'constant:fallback', HTTP_URI: 'constant:httpRegex' });
  const httpRegex = topDeclaration(normalizer, 'i').init;
  const adapterRegex = exactlyOne(ast.program.body.filter((entry) => entry.type === 'VariableDeclaration').flatMap((entry) => entry.declarations)
    .filter((entry) => entry.id.name === 'HTTP_URI'), 'HTTP_URI').init;
  expect(httpRegex.pattern === adapterRegex.pattern && httpRegex.flags === adapterRegex.flags, 'exact HTTP fallback regex');
  const response = await corpus.factory(997887, { source: 'evidence/web/objects/020facfab961bf67.js' });
  compare('coin array identity', response, exported(response, 'l'), {}, {}, local('readSearchCoins').init, {});
  return { schemaVersion: 1, adapterSha256: sha256(bytes), manifestSha256: corpus.anchors.manifestSha256,
    proofs, consumerBindings, stateBindings,
    comparison: 'Exact bounded AST alpha comparison; original declaration kinds, operations, values, branch and evaluation order retained; imported targets and Date.now map to explicit capabilities; !0/!1 normalize to booleans.',
    limits: ['No captured JavaScript executed or active runtime variant selected.',
      'Shared executor/normalizers are original-backed; HTTP bridge and synchronous headless state adapter are local design.',
      'No React scheduler/effects/debounce, backend schema/ranking, retry/ContractError, browser cookie or production qualification.',
      'The public search session rejects board/list descriptors; shared source branches are preserved and tested only with explicit capabilities.'] };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const mode = process.argv[2]; expect(['--write', '--check'].includes(mode) && process.argv.length === 3, 'usage: --write|--check');
    const proof = JSON.stringify(await verifySession(), null, 2) + '\n';
    if (mode === '--write') { await mkdir(path.join(APP_ROOT, 'reconstruction/search-session'), { recursive: true }); await writeFile(path.join(APP_ROOT, PROOF), proof); }
    else expect(await readFile(path.join(APP_ROOT, PROOF), 'utf8') === proof, 'saved provenance differs');
    console.log('Search session: both shared executor bodies, actual search consumers, state bindings and normalizers verified without capture execution.');
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
