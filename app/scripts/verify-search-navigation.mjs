import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from '@babel/parser';
import { openCorpus, findNodes, exactlyOne, member, propertyName, sha256 } from './original-contracts/source.mjs';
export const APP_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const ADAPTER = 'reconstruction/search-navigation/navigation.mjs';
export const PROOF = 'reconstruction/search-navigation/PROVENANCE.json';
const expect = (ok, message) => { if (!ok) throw Error('unqualified search navigation: ' + message); };
// Reuse of the lexical comparator first developed in search-session; it is
// proof infrastructure, not an additional source-recovery contribution.
const functions = new Set(['ArrowFunctionExpression', 'FunctionExpression', 'FunctionDeclaration']);
const ignored = new Set(['start', 'end', 'loc', 'extra', 'leadingComments', 'trailingComments', 'innerComments']);
const unbound = (callee) => callee?.type === 'SequenceExpression' && callee.expressions.length === 2 &&
  callee.expressions[0].value === 0 ? callee.expressions[1] : callee;

// Lexical alpha comparison only: preserve statements, declaration kinds,
// operators, values, branches, receiver calls and ordering. Qualified imported
// call targets map to their explicit maintained capabilities; !0/!1 are booleans.
export function normalizeNavigation(node, roles, imports = {}) {
  let next = 0;
  const unresolved = new Set();
  function bind(pattern, scope) {
    if (pattern.type === 'Identifier') scope.set(pattern.name, `local:${next++}`);
    else if (pattern.type === 'AssignmentPattern') bind(pattern.left, scope);
    else if (pattern.type === 'ObjectPattern') for (const item of pattern.properties) bind(item.value, scope);
    else throw new Error(`unsupported navigation binding: ${pattern.type}`);
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
      if (value.id) bind(value.id, scope);
      for (const parameter of value.params) bind(parameter, scope);
      current = [...scopes, scope];
    } else if (value.type === 'CatchClause') {
      const scope = new Map(); if (value.param) bind(value.param, scope); current = [...scopes, scope];
    } else if (value.type === 'BlockStatement') {
      const scope = new Map();
      for (const statement of value.body) if (statement.type === 'VariableDeclaration') {
        expect(statement.kind !== 'var' || functions.has(parent?.type), 'nested function-scoped var binding is not qualified');
        for (const entry of statement.declarations) bind(entry.id, scope);
      }
      current = [...scopes, scope];
    }
    if (value.type === 'Identifier') {
      const property = (key === 'key' && parent?.type === 'ObjectProperty' && !parent.computed) ||
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
  if (unresolved.size) throw new Error(`unresolved navigation bindings: ${[...unresolved].join(', ')}`);
  return result;
}

function declaration(factory, name) {
  return exactlyOne(factory.node.body.body.flatMap((item) => item.type === 'VariableDeclaration' ? item.declarations : item.type === 'FunctionDeclaration' ? [item] : [])
    .filter((item) => item.id?.name === name), 'declaration ' + name);
}
function exported(factory, name) {
  const array = exactlyOne(findNodes(factory.node, (item) => item.type === 'CallExpression' && member(item.callee, factory.runtime, 's') &&
    item.arguments[0]?.type === 'ArrayExpression' && item.arguments[0].elements.some((item) => item?.value === name)), 'export ' + name).arguments[0].elements;
  const index = array.findIndex((item) => item?.value === name);
  expect(array[index + 1]?.value === 0, 'direct export ' + name);
  const value = array[index + 2];
  if (value.type !== 'Identifier') return value;
  const target = declaration(factory, value.name);
  return target.type === 'FunctionDeclaration' ? target : target.init;
}
function difference(a, b, key = '') {
  if (a === b) return null;
  if (!a || !b || typeof a !== 'object' || typeof b !== 'object') return `${key}: ${JSON.stringify(a)} != ${JSON.stringify(b)}`;
  for (const k of new Set([...Object.keys(a), ...Object.keys(b)])) {
    const error = difference(a[k], b[k], key + '.' + k); if (error) return error;
  }
  return null;
}

export async function verifyNavigation(root = APP_ROOT) {
  const corpus = await openCorpus(root), bytes = await readFile(path.join(root, ADAPTER));
  const ast = parse(bytes.toString('utf8'), { sourceType: 'module' });
  const local = (name) => exactlyOne(ast.program.body.filter((item) => item.type === 'ExportNamedDeclaration').flatMap((item) =>
    item.declaration?.type === 'FunctionDeclaration' ? [item.declaration] : item.declaration?.declarations ?? [])
    .filter((item) => item.id?.name === name), 'adapter ' + name);
  const proofs = [];
  const compare = (label, factory, original, roles, imports, maintained, adapterRoles) => {
    const expected = normalizeNavigation(original, roles, imports), actual = normalizeNavigation(maintained, adapterRoles);
    const error = difference(expected, actual); expect(!error, label + ' AST differs: ' + error);
    proofs.push({ ...factory.witness(original, label), normalizedSha256: sha256(JSON.stringify(expected)) });
  };
  const dialog = await corpus.factory(238128, { source: 'evidence/web/objects/ccb10fa3de5597c4.js' });
  const original = exactlyOne(findNodes(dialog.node, (node) => node.type === 'ArrowFunctionExpression' && node.async &&
    findNodes(node, (child) => child.type === 'MemberExpression' && propertyName(child.property) === 'isSolanaMintOnChain').length === 1 &&
    findNodes(node, (child) => child.type === 'StringLiteral' && child.value === 'GET /coins-v3/{address}').length === 1), 'Solana navigator');
  const wrapper = local('createSolanaSearchNavigator'), maintained = wrapper.body.body[0].argument;
  expect(wrapper.body.body.length === 1 && maintained.async, 'explicit navigator factory');
  const ports = ['controllerRef', 'pasteRef', 'validAddress', 'walletProfile', 'resolveIdentifier', 'getContractClient', 'probeKnownMint', 'probeSolanaMint',
    'closeDialog', 'rememberTerm', 'trackMintPaste', 'trackWalletPaste', 'trackSearch', 'setLastClick', 'handleCoinClick', 'push'];
  expect(wrapper.params.length === 1 && wrapper.params[0].type === 'ObjectPattern' && wrapper.params[0].properties.length === ports.length + 1, 'navigator capabilities');
  for (const name of ports) {
    const value = exactlyOne(wrapper.params[0].properties.filter((item) => propertyName(item.key) === name), name).value;
    expect(value.type === 'Identifier' && value.name === name, 'navigator port wiring ' + name);
  }
  const abort = exactlyOne(wrapper.params[0].properties.filter((item) => propertyName(item.key) === 'AbortController'), 'controller capability').value;
  expect(abort.type === 'AssignmentPattern' && abort.left.name === 'Controller' && member(abort.right, 'globalThis', 'AbortController'), 'controller default');
  const globals = { JSON: 'global:JSON', DOMException: 'global:DOMException', AbortController: 'global:AbortController', encodeURIComponent: 'global:encodeURIComponent' };
  const roles = { ...globals, Y: 'port:controllerRef', er: 'port:pasteRef', e4: 'operation:resolveIdentifier',
    ea: 'operation:closeDialog', C: 'operation:rememberTerm', X: 'operation:setLastClick', W: 'operation:handleCoinClick', F: 'operation:push' };
  const imports = { 'd.R': 'operation:normalizeSolanaInput', 'tr.f': 'operation:validAddress', 'tt.f': 'operation:walletProfile',
    'eA.Q': 'operation:probeKnownMint', 'e1.isSolanaMintOnChain': 'operation:probeSolanaMint', 'eI.j': 'operation:getContractClient',
    'z.pL': 'operation:trackMintPaste', 'z.Cv': 'operation:trackWalletPaste', 'z.iu': 'operation:trackSearch', 'o.$': 'operation:profileRoute',
    'n.B8': 'constant:SEARCH_TYPE', 'n.Ae': 'constant:SCREEN', 'n.k9': 'constant:ELEMENT' };
  const adapterRoles = { ...globals, Controller: 'global:AbortController', SEARCH_TYPE: 'constant:SEARCH_TYPE', SCREEN: 'constant:SCREEN', ELEMENT: 'constant:ELEMENT',
    controllerRef: 'port:controllerRef', pasteRef: 'port:pasteRef' };
  for (const name of [...ports.filter((name) => !name.endsWith('Ref')), 'normalizeSolanaInput', 'profileRoute']) adapterRoles[name] = 'operation:' + name;
  compare('complete Solana identifier navigation', dialog, original, roles, imports, maintained, adapterRoles);
  const owner = findNodes(dialog.node, (node) => functions.has(node.type) && node !== original && node.body?.start < original.start && node.body.end > original.end)
    .sort((a, b) => (a.end - a.start) - (b.end - b.start))[0];
  expect(owner && owner !== dialog.node, 'owning dialog component');
  for (const name of ['Y', 'er']) {
    const ref = exactlyOne(findNodes(owner.body, (node) => node.type === 'VariableDeclarator' && node.id.name === name && member(unbound(node.init?.callee), 'a', 'useRef')), 'shared dialog ref ' + name);
    expect(ref.init.arguments[0].type === 'NullLiteral', 'shared navigation ref starts empty');
    proofs.push(dialog.witness(ref, 'actual shared navigation ref initialization'));
  }
  const originalBinding = exactlyOne(findNodes(dialog.node, (node) => node.type === 'VariableDeclarator' && node.init?.arguments?.[0] === original), 'Solana callback declaration');
  const submit = exactlyOne(findNodes(dialog.node, (node) => node.type === 'ArrowFunctionExpression' && node.async &&
    findNodes(node, (child) => child.type === 'CallExpression' && child.callee.name === originalBinding.id.name).length === 1), 'actual form submission');
  const submitDeclaration = exactlyOne(findNodes(dialog.node, (node) => node.type === 'VariableDeclarator' && node.init === submit), 'submit declaration');
  const submitWrapper = local('createSearchSubmit'), adaptedSubmit = submitWrapper.body.body[0].argument;
  expect(submitWrapper.body.body.length === 1 && adaptedSubmit.async && submitWrapper.params.length === 1 &&
    submitWrapper.params[0].type === 'ObjectPattern' && submitWrapper.params[0].properties.length === 8, 'submit wrapper');
  const submitRoles = { w: 'snapshot:searchTerm', ef: 'operation:navigateSolana', ex: 'operation:navigateEvm', ep: 'operation:navigateHex', eg: 'operation:navigateNear',
    ea: 'operation:closeDialog', C: 'operation:rememberTerm', F: 'operation:push', ...globals };
  const adaptedRoles = Object.fromEntries(submitWrapper.params[0].properties.map((item) => {
    expect(item.value.type === 'Identifier' && item.value.name === propertyName(item.key), 'submit snapshot wiring');
    return [item.value.name, item.value.name === 'searchTerm' ? 'snapshot:searchTerm' : 'operation:' + item.value.name];
  }));
  compare('actual form submit orchestration', dialog, submit, submitRoles, {}, adaptedSubmit, { ...adaptedRoles, ...globals });
  const mount = exactlyOne(findNodes(dialog.node, (node) => node.type === 'ObjectProperty' && propertyName(node.key) === 'onSubmit' && node.value.name === submitDeclaration.id.name), 'used form handler');
  proofs.push(dialog.witness(mount, 'actual rendered onSubmit binding'));
  for (const [name, id] of [['d', 975982], ['tr', 639374], ['tt', 820190], ['eA', 620268], ['e1', 464403], ['eI', 759257], ['z', 595673], ['o', 146695], ['n', 292686]]) {
    const entry = declaration(dialog, name);
    expect(member(entry.init?.callee, dialog.runtime, 'i') && entry.init.arguments[0]?.value === id, 'actual navigation import ' + name);
    proofs.push(dialog.witness(entry, 'navigation import ' + id));
  }
  const text = await corpus.factory(975982, { source: 'evidence/web/objects/9eb69cb75e0ff997.js' });
  for (const [exportName, adapterName, sourceRoles] of [['k', 'isSolanaText', { t: 'constant:base58Text' }], ['R', 'normalizeSolanaInput', { r: 'operation:admit' }]]) {
    const source = exported(text, exportName);
    compare(adapterName, text, source, sourceRoles, {}, local(adapterName).init, { SOLANA_TEXT: 'constant:base58Text', isSolanaText: 'operation:admit' });
  }
  const sourceRegex = declaration(text, 't').init;
  const adapterRegex = exactlyOne(ast.program.body.filter((node) => node.type === 'VariableDeclaration').flatMap((node) => node.declarations).filter((node) => node.id.name === 'SOLANA_TEXT'), 'base58 text regex').init;
  expect(sourceRegex.pattern === adapterRegex.pattern && sourceRegex.flags === adapterRegex.flags, 'text regex');
  const guards = local('createSolanaGuards');
  expect(guards.params.length === 1 && guards.params[0].type === 'ObjectPattern' &&
    JSON.stringify(guards.params[0].properties.map((item) => [propertyName(item.key), item.value.name])) === JSON.stringify([['base58', 'base58'], ['PublicKey', 'PublicKey']]) &&
    guards.body.body.length === 3 && guards.body.body[2].type === 'ReturnStatement' &&
    guards.body.body[2].argument.properties.map((item) => item.value.name).join(',') === 'validAddress,walletProfile', 'guard capability wiring');
  const guardBody = Object.fromEntries(guards.body.body.slice(0, 2).map((node) => [node.declarations[0].id.name, node.declarations[0].init]));
  for (const [id, sources, name, importName, importRole] of [
    [639374, ['3740fc4e7a24596d', 'cf2bb278631744da'], 'validAddress', 't.f', 'value:base58'],
    [820190, ['c4c5abc83734bc1b', '43fc24878549d421'], 'walletProfile', 't.PublicKey', 'value:PublicKey'],
  ]) for (const sourceName of sources) {
    const factory = await corpus.factory(id, { source: 'evidence/web/objects/' + sourceName + '.js' }), source = exported(factory, 'f');
    const dependency = declaration(factory, 't');
    expect(member(dependency.init?.callee, factory.runtime, 'i') && dependency.init.arguments[0]?.value === (id === 639374 ? 344048 : 971370), 'actual guard vendor import');
    proofs.push(factory.witness(dependency, 'guard vendor import'));
    compare(name, factory, source, {}, { [importName]: importRole }, { ...source, params: guardBody[name].params, body: guardBody[name].body }, { base58: 'value:base58', PublicKey: 'value:PublicKey' });
  }
  const profile = await corpus.factory(146695, { source: 'evidence/web/objects/fd402d4185b44ce9.js' });
  const profileSource = exported(profile, '$');
  compare('profile route', profile, profileSource, globals, {}, { ...profileSource, params: local('profileRoute').params, body: local('profileRoute').body }, globals);
  const enums = await corpus.factory(292686, { source: 'evidence/web/objects/88945b987f03af34.js' });
  for (const [sourceName, name, keys] of [['B8', 'SEARCH_TYPE', ['COINS', 'USERS']], ['Ae', 'SCREEN', ['SEARCH']], ['k9', 'ELEMENT', ['SEARCH_INPUT']]]) {
    const original = exported(enums, sourceName), initializer = local(name).init;
    expect(initializer.type === 'CallExpression' && member(initializer.callee, 'Object', 'freeze') && initializer.arguments.length === 1 &&
      initializer.arguments[0].type === 'ObjectExpression', 'selected enum initializer');
    const adapted = initializer.arguments[0];
    expect(adapted.properties.length === keys.length, 'selected enum extent');
    for (const key of keys) {
      const value = exactlyOne(original.properties.filter((item) => propertyName(item.key) === key), 'captured enum ' + key);
      const localValue = exactlyOne(adapted.properties.filter((item) => propertyName(item.key) === key), 'maintained enum ' + key);
      expect(value.value.value === localValue.value.value, 'selected enum value'); proofs.push(enums.witness(value, name + '.' + key));
    }
  }
  const opaqueBoundaries = [];
  for (const [id, name] of [[620268, 'Q'], [464403, 'isSolanaMintOnChain']]) {
    const sources = new Set(corpus.index.modules.filter((item) => item.ids.includes(id)).flatMap((item) => item.origins.map((origin) => origin.source)));
    expect(sources.size > 0, 'available read-probe boundary');
    for (const source of [...sources].sort()) {
      const factory = await corpus.factory(id, { source });
      const array = exactlyOne(findNodes(factory.node, (node) => node.type === 'CallExpression' && member(node.callee, factory.runtime, 's') &&
        node.arguments[0]?.type === 'ArrayExpression' && node.arguments[0].elements.some((item) => item?.value === name)), 'available probe export').arguments[0].elements;
      const index = array.findIndex((item) => item?.value === name);
      opaqueBoundaries.push({ export: name, ...factory.provenance, exportReference: factory.witness(array[index + 2], 'read-probe export reference, implementation not executed/recovered') });
    }
  }
  return { schemaVersion: 1, adapterSha256: sha256(bytes), manifestSha256: corpus.anchors.manifestSha256, proofs, opaqueBoundaries,
    comparison: 'Exact bounded AST alpha comparison, preserving branches, declaration kinds, literals, operations and ordering; qualified capabilities and boolean spellings normalized.',
    dependencies: ['Merged search wire/resolver684 is a prerequisite, not new recovery.', 'Base58 decoder, PublicKey, RPC/mint probes, analytics, UI close/history and other-chain handlers are explicit capabilities.'],
    limits: ['No captured bundle execution, live RPC or production requests.', 'Coin/profile route destinations stop at excluded detail boundaries; no detail page is implemented.',
      'Only the used Solana identifier handler and form orchestration are recovered; other-chain handlers, RPC classification, analytics service and full React lifecycle remain unqualified.'] };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const mode = process.argv[2]; expect(['--check', '--write'].includes(mode) && process.argv.length === 3, 'usage: --check|--write');
    const proof = JSON.stringify(await verifyNavigation(), null, 2) + '\n';
    if (mode === '--write') { await mkdir(path.join(APP_ROOT, 'reconstruction/search-navigation'), { recursive: true }); await writeFile(path.join(APP_ROOT, PROOF), proof); }
    else expect(await readFile(path.join(APP_ROOT, PROOF), 'utf8') === proof, 'saved provenance differs');
    console.log('Search navigation: used submit/Solana bodies, admission helpers, routes and constants verified without bundle execution.');
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
