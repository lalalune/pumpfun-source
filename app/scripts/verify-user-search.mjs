import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from '@babel/parser';
import { openCorpus, findNodes, exactlyOne, member, propertyName, objectProperty, sha256 } from './original-contracts/source.mjs';
import { createSchemaExtractor } from './original-contracts/schema.mjs';
export const APP_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const ADAPTER = 'reconstruction/user-search/query.mjs';
export const PROOF = 'reconstruction/user-search/PROVENANCE.json';
const expect = (ok, message) => { if (!ok) throw Error('unqualified user search: ' + message); };
// Bounded lexical comparison reused from earlier source proofs; not new recovery.
const functions = new Set(['ArrowFunctionExpression', 'FunctionExpression', 'FunctionDeclaration', 'ObjectMethod']);
const ignored = new Set(['start', 'end', 'loc', 'extra', 'leadingComments', 'trailingComments', 'innerComments']);
const unbound = (callee) => callee?.type === 'SequenceExpression' && callee.expressions.length === 2 &&
  callee.expressions[0].value === 0 ? callee.expressions[1] : callee;

// Lexical alpha comparison only: preserve statements, declaration kinds,
// operators, values, branches, receiver calls and ordering. Qualified imported
// call targets map to their explicit maintained capabilities; !0/!1 are booleans.
export function normalizeUserSearch(node, roles, imports = {}) {
  let next = 0;
  const unresolved = new Set();
  function bind(pattern, scope) {
    if (pattern.type === 'Identifier') scope.set(pattern.name, `local:${next++}`);
    else if (pattern.type === 'AssignmentPattern') bind(pattern.left, scope);
    else if (pattern.type === 'ObjectPattern') for (const item of pattern.properties) bind(item.value, scope);
    else throw new Error(`unsupported user-search binding: ${pattern.type}`);
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
    } else if (value.type === 'ForOfStatement') {
      expect(value.left.type === 'VariableDeclaration', 'lexical for-of binding');
      const scope = new Map(); for (const entry of value.left.declarations) bind(entry.id, scope);
      current = [...scopes, scope];
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
  if (unresolved.size) throw new Error(`unresolved user-search bindings: ${[...unresolved].join(', ')}`);
  return result;
}

const contexts = [
  ['ecf7ec803bfb3020', { label: 'n', identity: 'l', request: 's', user: 'o', pagination: 'd', select: 'u', client: 'i', debounce: 'a', queryRuntime: 'r',
    raw: 'b', enabled: 'y', pageSize: 'v', active: 'w', limit: 'k', trimmed: 'i', debounced: 'C', short: 'x', debouncing: 'n', key: 'l', callback: 'c', next: 'm', options: 'p', queryEnabled: '_' }],
  ['9535b69d76e2a69b', { label: 'r', identity: 'n', request: 'o', user: 's', pagination: 'd', select: 'c', client: 'l', debounce: 'i', queryRuntime: 'a',
    raw: 'y', enabled: 'v', pageSize: 'b', active: 'I', limit: 'w', trimmed: 'l', debounced: 'C', short: 'k', debouncing: 'r', key: 'n', callback: 'u', next: 'm', options: 'p', queryEnabled: 'T' }],
  ['767cc801e3f88f8b', { label: 'i', identity: 's', request: 'n', user: 'o', pagination: 'u', select: 'c', client: 'a', debounce: 'l', queryRuntime: 'r',
    raw: 'x', enabled: 'b', pageSize: 'w', active: 'y', limit: 'v', trimmed: 'a', debounced: 'E', short: 'k', debouncing: 'i', key: 's', callback: 'd', next: 'm', options: 'f', queryEnabled: 'S' }],
];
function declared(node, name) {
  return exactlyOne(findNodes(node, (entry) => entry.type === 'VariableDeclarator' && entry.id.name === name && entry.init), 'initialized declaration ' + name).init;
}
function top(factory, name) {
  const entry = exactlyOne(factory.node.body.body.flatMap((entry) => entry.type === 'VariableDeclaration' ? entry.declarations : entry.type === 'FunctionDeclaration' ? [entry] : [])
    .filter((entry) => entry.id.name === name), 'factory declaration ' + name);
  return entry.type === 'FunctionDeclaration' ? entry : entry.init;
}
function exported(factory, name) {
  const array = exactlyOne(findNodes(factory.node, (node) => node.type === 'CallExpression' && member(node.callee, factory.runtime, 's') &&
    node.arguments[0]?.type === 'ArrayExpression' && node.arguments[0].elements.some((item) => item?.value === name)), 'export ' + name).arguments[0].elements;
  const index = array.findIndex((entry) => entry?.value === name); expect(array[index + 1]?.value === 0, 'direct export');
  return array[index + 2].type === 'Identifier' ? top(factory, array[index + 2].name) : array[index + 2];
}
function assigned(node, name, type) {
  return exactlyOne(findNodes(node, (entry) => entry.type === 'AssignmentExpression' && entry.operator === '=' &&
    entry.left.type === 'Identifier' && entry.left.name === name && entry.right.type === type), 'assigned ' + name).right;
}
function difference(a, b, at = '') {
  if (a === b) return null;
  if (!a || !b || typeof a !== 'object' || typeof b !== 'object') return `${at}: ${JSON.stringify(a)} != ${JSON.stringify(b)}`;
  for (const key of new Set([...Object.keys(a), ...Object.keys(b)])) { const error = difference(a[key], b[key], at + '.' + key); if (error) return error; }
  return null;
}
export async function verifyUserSearch(root = APP_ROOT) {
  const corpus = await openCorpus(root), bytes = await readFile(path.join(root, ADAPTER)), ast = parse(bytes.toString('utf8'), { sourceType: 'module' });
  const local = (name) => exactlyOne(ast.program.body.filter((entry) => entry.type === 'ExportNamedDeclaration').flatMap((entry) =>
    entry.declaration?.type === 'FunctionDeclaration' ? [entry.declaration] : entry.declaration?.declarations ?? []).filter((entry) => entry.id.name === name), 'adapter ' + name);
  const proofs = [];
  function compare(label, factory, original, roles, imports, adapter, adaptedRoles) {
    const expected = normalizeUserSearch(original, roles, imports), actual = normalizeUserSearch(adapter, adaptedRoles);
    const error = difference(expected, actual); expect(!error, label + ' AST differs: ' + error);
    proofs.push({ ...factory.witness(original, label), normalizedSha256: sha256(JSON.stringify(expected)) });
  }
  const query = local('createUserSearchQuery');
  expect(query.params.length === 2 && query.params[0].type === 'ObjectPattern' && query.params[1].name === 'getContractClient', 'query factory inputs');
  expect(JSON.stringify(query.params[0].properties.map((entry) => [propertyName(entry.key), entry.value.name])) === JSON.stringify(['searchTerm', 'enabled', 'pageSize', 'debouncedTerm'].map((name) => [name, name])), 'snapshot wiring');
  const declarations = ['active', 'limit', 'trimmedTerm', 'isSearchTermTooShort', 'isDebouncing', 'request', 'queryKey', 'queryFn', 'getNextPageParam', 'queryEnabled', 'queryOptions'];
  expect(query.body.body.length === declarations.length + 1 && query.body.body.slice(0, -1).every((node, index) =>
    node.type === 'VariableDeclaration' && node.kind === 'const' && node.declarations.length === 1 && node.declarations[0].id.name === declarations[index]), 'snapshot-only construction');
  for (const [name, factory, argument] of [['request', 'createUserSearchRequest', 'getContractClient'], ['getNextPageParam', 'createUserSearchNextPage', 'limit']]) {
    const value = declared(query.body, name);
    expect(value.type === 'CallExpression' && value.callee.name === factory && value.arguments.length === 1 && value.arguments[0].name === argument, 'helper capability wiring');
  }
  const returned = query.body.body.at(-1);
  expect(returned.type === 'ReturnStatement' && returned.argument.type === 'ObjectExpression' &&
    JSON.stringify(returned.argument.properties.map((entry) => [propertyName(entry.key), entry.value.type === 'Identifier' ? entry.value.name : entry.value.value])) ===
      JSON.stringify([['queryOptions', 'queryOptions'], ['trimmedTerm', 'trimmedTerm'], ['isSearchTermTooShort', 'isSearchTermTooShort'], ['isDebouncing', 'isDebouncing'], ['minSearchTermLength', 2], ['debounceMs', 500]]), 'returned query/meta wiring');
  const adapterRoles = { searchTerm: 'snapshot:raw', enabled: 'snapshot:enabled', pageSize: 'snapshot:pageSize', debouncedTerm: 'snapshot:debounced',
    active: 'flag:active', limit: 'snapshot:limit', isSearchTermTooShort: 'flag:short', queryEnabled: 'flag:queryEnabled',
    queryKey: 'query:key', queryFn: 'query:callback', getNextPageParam: 'query:next', selectUserSearchPages: 'operation:select',
    request: 'operation:request', isUserRow: 'operation:user', isPaginationUser: 'operation:pagination' };
  for (const [source, names] of contexts) {
    const factory = await corpus.factory(600775, { source: 'evidence/web/objects/' + source + '.js' }), hook = exported(factory, 'N');
    const helperRoles = { Set: 'global:Set', [names.label]: 'operation:label', [names.identity]: 'operation:identity' };
    const maintainedRoles = { Set: 'global:Set', isLabelledWallet: 'operation:label', userSearchIdentity: 'operation:identity' };
    for (const [sourceName, adapterName] of [[names.label, 'isLabelledWallet'], [names.identity, 'userSearchIdentity'], [names.user, 'isUserRow'], [names.pagination, 'isPaginationUser'], [names.select, 'selectUserSearchPages']]) {
      const node = local(adapterName), maintained = node.type === 'FunctionDeclaration' ? node : node.init;
      compare(adapterName, factory, top(factory, sourceName), helperRoles, {}, maintained, maintainedRoles);
    }
    const request = local('createUserSearchRequest'); expect(request.params.length === 1 && request.params[0].name === 'getContractClient' && request.body.body.length === 1, 'request port wiring');
    compare('complete user-search request', factory, top(factory, names.request), { Error: 'global:Error' }, { [`${names.client}.j`]: 'operation:client' },
      request.body.body[0].argument, { Error: 'global:Error', getContractClient: 'operation:client' });
    const roles = { [names.raw]: 'snapshot:raw', [names.enabled]: 'snapshot:enabled', [names.pageSize]: 'snapshot:pageSize',
      [names.debounced]: 'snapshot:debounced', [names.active]: 'flag:active', [names.limit]: 'snapshot:limit', [names.short]: 'flag:short',
      [names.queryEnabled]: 'flag:queryEnabled', [names.key]: 'query:key', [names.callback]: 'query:callback', [names.next]: 'query:next',
      [names.select]: 'operation:select', [names.request]: 'operation:request', [names.user]: 'operation:user', [names.pagination]: 'operation:pagination' };
    for (const [sourceName, adapterName] of [[names.active, 'active'], [names.limit, 'limit'], [names.short, 'isSearchTermTooShort'], [names.queryEnabled, 'queryEnabled']]) {
      compare(adapterName, factory, declared(hook.body, sourceName), roles, {}, declared(query.body, adapterName), adapterRoles);
    }
    compare('trimmed term', factory, assigned(hook.body, names.trimmed, 'LogicalExpression'), roles, {}, declared(query.body, 'trimmedTerm'), adapterRoles);
    compare('debouncing flag', factory, assigned(hook.body, names.debouncing, 'LogicalExpression'), roles, {}, declared(query.body, 'isDebouncing'), adapterRoles);
    compare('query key', factory, assigned(hook.body, names.key, 'ArrayExpression'), roles, {}, declared(query.body, 'queryKey'), adapterRoles);
    compare('used query callback', factory, assigned(hook.body, names.callback, 'ArrowFunctionExpression'), roles, {}, declared(query.body, 'queryFn'), adapterRoles);
    const next = local('createUserSearchNextPage'); expect(next.params.length === 1 && next.params[0].name === 'pageSize' && next.body.body.length === 1, 'page factory wiring');
    compare('next-page offset', factory, assigned(hook.body, names.next, 'ArrowFunctionExpression'), roles, {}, next.body.body[0].argument,
      { pageSize: 'snapshot:limit', isUserRow: 'operation:user', isPaginationUser: 'operation:pagination' });
    compare('query options', factory, assigned(hook.body, names.options, 'ObjectExpression'), roles, {}, declared(query.body, 'queryOptions'), adapterRoles);
    const debounce = exactlyOne(findNodes(hook.body, (node) => node.type === 'VariableDeclarator' && node.id.type === 'ArrayPattern' && node.id.elements[0]?.name === names.debounced), 'actual debounce hook');
    expect(member(unbound(debounce.init.callee), names.debounce, 'r') && debounce.init.arguments[0].name === names.trimmed && debounce.init.arguments[1]?.value === 500, '500ms debounce input boundary');
    proofs.push(factory.witness(debounce, 'actual debounce call, scheduler not recovered'));
    const useQuery = exactlyOne(findNodes(hook.body, (node) => node.type === 'CallExpression' && member(unbound(node.callee), names.queryRuntime, 'useInfiniteQuery')), 'used infinite query');
    expect(useQuery.arguments[0]?.name === names.options, 'actual query-options consumer'); proofs.push(factory.witness(useQuery, 'actual useInfiniteQuery options binding'));
    for (const [binding, id] of [[names.client, 759257], [names.debounce, 536925], [names.queryRuntime, 761459]]) {
      const imported = exactlyOne(factory.node.body.body.flatMap((node) => node.type === 'VariableDeclaration' ? node.declarations : []).filter((node) => node.id.name === binding), 'actual import').init;
      expect(member(imported.callee, factory.runtime, 'i') && imported.arguments[0]?.value === id, 'dependency identity'); proofs.push(factory.witness(imported, 'import ' + id));
    }
    expect(exported(factory, 'B').value === 2, 'captured minimum length');
  }
  const dialog = await corpus.factory(238128, { source: 'evidence/web/objects/ccb10fa3de5597c4.js' });
  const imported = exactlyOne(dialog.node.body.body.flatMap((node) => node.type === 'VariableDeclaration' ? node.declarations : []).filter((node) => node.id.name === 'eX'), 'dialog user-search import');
  expect(imported.init.arguments[0]?.value === 600775, 'actual dialog import');
  const used = exactlyOne(findNodes(dialog.node, (node) => node.type === 'CallExpression' && member(unbound(node.callee), 'eX', 'N')), 'used dialog user-search hook');
  expect(used.arguments[0].type === 'ObjectExpression' && used.arguments[0].properties.length === 1 && propertyName(used.arguments[0].properties[0].key) === 'searchTerm', 'dialog hook input');
  proofs.push(dialog.witness(imported, 'dialog user-search import')); proofs.push(dialog.witness(used, 'actual dialog user-search consumer'));
  const catalog = await corpus.factory(941660, { source: 'evidence/web/objects/2b47dd0b38a1608f.js' });
  const route = exactlyOne(findNodes(catalog.node, (node) => node.type === 'ObjectProperty' && propertyName(node.key) === 'GET /users/search-v2'), 'catalog route');
  expect(member(unbound(route.value.callee), 's', 'publicRead') && route.value.arguments[0]?.value === 'profiles.read', 'declared wrapper/scope');
  const wrapperImport = top(catalog, 's');
  expect(member(wrapperImport.callee, catalog.runtime, 'r') && wrapperImport.arguments[0]?.value === 785036, 'publicRead dependency identity');
  const contract = await corpus.factory(402030, { source: 'evidence/web/objects/2b47dd0b38a1608f.js' });
  const routesImport = top(contract, 'eb');
  expect(member(routesImport.callee, contract.runtime, 'r') && routesImport.arguments[0]?.value === 941660, 'contract usersRoutes import');
  const routesSpread = exactlyOne(findNodes(contract.node, (node) => node.type === 'SpreadElement' && member(node.argument, 'eb', 'usersRoutes')), 'contract usersRoutes spread');
  proofs.push(catalog.witness(wrapperImport, 'publicRead import'));
  proofs.push(contract.witness(routesImport, 'actual catalog usersRoutes import'));
  proofs.push(contract.witness(routesSpread, 'actual catalog usersRoutes spread'));
  const shape = route.value.arguments[1], sources = { 941660: 'evidence/web/objects/2b47dd0b38a1608f.js', 896727: 'evidence/web/objects/2b47dd0b38a1608f.js',
    876543: 'evidence/web/objects/2b47dd0b38a1608f.js', 599565: 'evidence/web/objects/06e532443c8db686.js', 408162: 'evidence/web/objects/d50c5c8832449b79.js' };
  const schemas = await createSchemaExtractor(corpus, { sources });
  const declaredSchemas = schemas.document({ type: 'object', properties: {
    query: await schemas.compile(objectProperty(shape, 'query'), catalog), response: await schemas.compile(objectProperty(shape, 'response'), catalog),
  } });
  proofs.push(catalog.witness(route, 'complete declared users/search-v2 route'));
  return { schemaVersion: 1, adapterSha256: sha256(bytes), manifestSha256: corpus.anchors.manifestSha256, proofs,
    declaredSchemas, schemaWitnesses: schemas.witnesses(),
    comparison: 'Exact selected AST alpha comparison; loop/catch/function scopes, operators, declarations, calls and order preserved. Imported call targets and boolean spellings normalize.',
    boundaries: ['React/compiler memoization, the 500ms debounce scheduler and useInfiniteQuery runtime are not executed/reconstructed.',
      'queryOptions.enabled is a runtime input; calling queryFn directly still performs its request, including for short/disabled terms.',
      'Declared response is array(userRow), including optional string wallet_label; the client consumes raw JSON and classifies wallet_label by presence. No schema rewrite or server compatibility claim.',
      'profiles.read is captured publicRead metadata, not proof of live server scope enforcement or current authentication.'] };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const mode = process.argv[2]; expect(['--write', '--check'].includes(mode) && process.argv.length === 3, 'usage: --write|--check');
    const proof = JSON.stringify(await verifyUserSearch(), null, 2) + '\n';
    if (mode === '--write') { await mkdir(path.join(APP_ROOT, 'reconstruction/user-search'), { recursive: true }); await writeFile(path.join(APP_ROOT, PROOF), proof); }
    else expect(await readFile(path.join(APP_ROOT, PROOF), 'utf8') === proof, 'saved provenance differs');
    console.log('User search: three source contexts, actual dialog/query consumers and declared schemas verified without capture execution.');
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
