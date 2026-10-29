import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from '@babel/parser';
import { openCorpus, exactlyOne, findNodes, member, propertyName, objectProperty, sha256 } from '../../scripts/original-contracts/source.mjs';
import { normalizeSession, verifySession } from '../../scripts/verify-search-session.mjs';

export const APP_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
export const DIRECTORY = 'reconstruction/live-listing-data';
export const PROOF = `${DIRECTORY}/PROVENANCE.json`;
const source = 'evidence/web/objects/44a65b4313e51497.js';
const top = (f, name) => exactlyOne(f.node.body.body.flatMap((n) => n.type === 'VariableDeclaration' ? n.declarations : [])
  .filter((n) => n.id.name === name), `top ${name}`);
const named = (f, name) => exactlyOne(f.node.body.body.filter((n) => n.type === 'FunctionDeclaration' && n.id.name === name), `function ${name}`);
const declared = (node, name) => exactlyOne(findNodes(node, (n) => n.type === 'VariableDeclarator' && n.id.name === name), `declaration ${name}`).init;
const assigned = (node, name) => exactlyOne(findNodes(node, (n) => n.type === 'AssignmentExpression' && n.left.name === name &&
  !(n.right.type === 'MemberExpression' && ['d', 's'].includes(n.right.object.name))), `assignment ${name}`).right;
const result = (node) => node.body.body.at(-1).argument;
const globals = Object.fromEntries(['Error', 'Object', 'Set', 'URL', 'JSON'].map((n) => [n, `global:${n}`]));

// Captured exports use both getter pairs and name/0/value triples. The target
// registration ID is explicit for co-registered factories.
function exported(f, id, name) {
  const call = exactlyOne(findNodes(f.node, (n) => n.type === 'CallExpression' && member(n.callee, f.runtime, 's') &&
    (n.arguments[1]?.value === id || f.ids.length === 1 && n.arguments.length === 1) &&
    n.arguments[0]?.type === 'ArrayExpression' && n.arguments[0].elements.some((e) => e?.value === name)), `export ${id}.${name}`);
  const values = call.arguments[0].elements;
  for (let i = 0; i < values.length;) {
    const key = values[i].value;
    const direct = values[i + 1]?.type === 'NumericLiteral' && values[i + 1].value === 0;
    let value = values[i + (direct ? 2 : 1)];
    if (!direct) { assert.equal(value.type, 'ArrowFunctionExpression'); assert.equal(value.params.length, 0); value = value.body; }
    if (key === name) return value.type === 'Identifier' ? top(f, value.name).init : value;
    i += direct ? 3 : 2;
  }
  throw new Error(`missing export ${id}.${name}`);
}
const callable = (n) => ({ type: 'ArrowFunctionExpression', async: !!n.async, params: n.params, body: n.body, start: n.start, end: n.end });

export async function buildLiveListingProof(root = APP_ROOT) {
  const corpus = await openCorpus(root), fragments = [], comparisons = [], imports = [];
  const selected = new Map(), factories = [];
  for (const id of [859960, 944001, 31113, 788501, 647145, 558898, 759257, 997887, 493025]) {
    const variants = corpus.index.modules.filter((m) => m.ids.includes(id));
    assert.equal(variants.length, 1, `physical variant census ${id}`);
    for (const origin of variants[0].origins) {
      const f = await corpus.factory(id, { source: origin.source });
      selected.set(id, f); factories.push(f.provenance);
    }
  }
  const listing = selected.get(859960), registry = selected.get(944001);
  assert.equal(listing.provenance.source, source);
  const bytes = await readFile(path.join(root, DIRECTORY, 'listing.mjs'));
  const ast = parse(bytes.toString('utf8'), { sourceType: 'module' });
  const local = (name) => exactlyOne(ast.program.body.flatMap((n) => n.type === 'ExportNamedDeclaration'
    ? n.declaration.type === 'FunctionDeclaration' ? [n.declaration] : n.declaration.declarations : [])
    .filter((n) => n.id.name === name), `editable ${name}`);
  const witness = (f, node, label) => { const w = f.witness(node, label); fragments.push(w); return w; };
  const imported = (f, alias, id) => {
    const d = top(f, alias);
    assert.ok(member(d.init.callee, f.runtime, 'i'));
    assert.equal(d.init.arguments[0].value, id);
    imports.push(f.witness(d, `actual import ${alias}→${id}`));
  };
  for (const [alias, id] of [['m', 759257], ['d', 997887], ['v', 493025], ['c', 558898], ['u', 503630], ['x', 419111], ['p', 54567]]) imported(listing, alias, id);
  for (const [alias, id] of [['i', 859960], ['A', 539335], ['a', 606706], ['l', 647145]]) imported(registry, alias, id);
  const compare = (label, original, actual, roles = {}, localRoles = roles, targets = {}, f = listing) => {
    const expected = normalizeSession(original, { ...globals, ...roles }, targets);
    const observed = normalizeSession(actual, { ...globals, ...localRoles });
    assert.deepEqual(observed, expected, `listing source differs: ${label}`);
    comparisons.push({ ...witness(f, original, label), roles, localRoles, targets, structuralSha256: sha256(JSON.stringify(observed)) });
  };
  const compareFunction = (label, original, actual, ...options) => compare(label, callable(original), callable(actual), ...options);
  assert.equal(top(listing, 'n').init.value, local('LIVE_LISTING_LIMIT').init.value);
  witness(listing, top(listing, 'n'), '606706 listing default limit24');
  assert.equal(exported(listing, 606706, 'O').value, local('LIVE_LISTING_LIMIT').init.value);
  const sorts = exported(listing, 539335, 'f');
  const assignments = findNodes(sorts, (n) => n.type === 'AssignmentExpression' && n.right.type === 'StringLiteral');
  assert.deepEqual(assignments.map((n) => [propertyName(n.left.property), n.right.value]),
    local('LIVE_SORTS').init.properties.map((n) => [propertyName(n.key), n.value.value]));
  witness(listing, sorts, '539335 listing sort constants, physical context only');
  compare('sort query fields', top(listing, 'g').init, local('LIVE_SORT_FIELDS').init);
  compare('complete coin-to-card projection', callable(top(listing, 'b').init), callable(local('projectLiveCoin').init));
  const queries = local('createLiveListing');
  compareFunction('complete credentialed coin-query arrow', top(listing, 'y').init, declared(queries, 'fetchCoins'),
    { n: 'constant:limit', o: 'constant:sorts', g: 'constant:fields' },
    { LIVE_LISTING_LIMIT: 'constant:limit', LIVE_SORTS: 'constant:sorts', LIVE_SORT_FIELDS: 'constant:fields',
      logger: 'operation:logger', getContractClient: 'operation:client', normalizeSearchCoins: 'operation:normalize', readSearchCoins: 'operation:identity' },
    { 'p.logger': 'operation:logger', 'm.j': 'operation:client', 'v.f': 'operation:normalize', 'd.l': 'operation:identity' });
  compareFunction('complete playlist-map HTTP arrow with injected capabilities', top(listing, '_').init, result(local('createPlaylistMapRead')),
    { fetch: 'operation:fetch' }, { fetchResponse: 'operation:fetch', getServiceOrigin: 'operation:origin', playlistSchema: 'operation:schema' },
    { 'u.c': 'operation:origin', 'c.S': 'operation:schema' });
  compareFunction('complete stream-list and best-effort playlist merge arrow', top(listing, 'j').init, declared(queries, 'fetchSection'),
    { y: 'operation:coins', b: 'operation:project', _: 'operation:playlists' },
    { fetchCoins: 'operation:coins', projectLiveCoin: 'operation:project', readPlaylistMap: 'operation:playlists', logger: 'operation:logger', errorContext: 'operation:context' },
    { 'p.logger': 'operation:logger', 'x.w': 'operation:context' });
  for (const [old, name] of [['S', 'nextLivePage'], ['k', 'selectLivePages'], ['P', 'livePageIdentity']]) {
    compareFunction(`complete ${name}`, named(listing, old), local(name));
  }
  const hook = exported(listing, 859960, 'N'), query = local('liveSectionQuery'), returnQuery = result(query);
  compare('undefined-only limit default', declared(hook, 'v'), declared(query, 'v'), { m: 'input:limit', n: 'constant:limit' }, { m: 'input:limit', LIVE_LISTING_LIMIT: 'constant:limit' });
  compare('undefined-only stale-time default', declared(hook, 'g'), declared(query, 'g'), { p: 'input:stale' });
  const queryRoles = { u: 'input:sort', b: 'input:nsfw', v: 'input:limit', y: 'input:prefix', j: 'operation:section' };
  compare('complete section query key', assigned(hook, 't'), objectProperty(returnQuery, 'queryKey'), queryRoles);
  compareFunction('complete page query function', assigned(hook, 'l'), declared(query, 'queryFn'), queryRoles);
  compare('truthy initial-data seed and pageParam0', assigned(hook, 'r'), objectProperty(returnQuery, 'initialData'), { x: 'input:initial' });
  const config = assigned(hook, 's');
  for (const [key, old, actual] of [['initialPageParam', null, null], ['getNextPageParam', 'S', 'nextLivePage'], ['select', 'k', 'selectLivePages'], ['staleTime', 'g', 'g']]) {
    compare(`section config ${key}`, objectProperty(config, key), objectProperty(returnQuery, key), old ? { [old]: `config:${key}` } : {}, actual ? { [actual]: `config:${key}` } : {});
  }
  const sectionResult = result(local('liveSectionResult'));
  compare('complete selected-page flatten/default', assigned(hook, 'c'), objectProperty(sectionResult, 'data'),
    { _: 'input:result', P: 'operation:pageIdentity' }, { result: 'input:result', livePageIdentity: 'operation:pageIdentity' });
  const hookResult = assigned(hook, 'o');
  for (const key of ['isLoading', 'fetchNextPage', 'hasNextPage', 'isFetchingNextPage']) compare(`result ${key}`, objectProperty(hookResult, key), objectProperty(sectionResult, key), { _: 'input:result' }, { result: 'input:result' });
  const section = exported(registry, 310766, 'Z');
  const entries = exported(registry, 944001, 'Z');
  assert.equal(entries.type, 'ArrayExpression');
  for (const [index, id, key, editable] of [[0, 'MOST_VIEWERS', 'MOST_VIEWERS', 'mostViewedSectionArguments'],
    [1, 'HIGHEST_MARKET_CAP', 'MARKET_CAP', 'highestCapSectionArguments']]) {
    const entry = entries.elements[index];
    const entryId = objectProperty(entry, 'id');
    assert.equal(propertyName(entryId.property), id); assert.ok(member(entryId.object, 't', 'f'));
    for (const field of ['useFetch', 'fetch']) {
      const callback = objectProperty(entry, field), call = callback.body;
      assert.equal(call.type, 'CallExpression');
      assert.ok(member(call.callee.expressions.at(-1), 'i', field === 'fetch' ? 'A' : 'N'));
      compare(`registry ${id} ${field} complete arguments`, call.arguments[0], local(editable).init.body,
        { e: 'input:options' }, { e: 'input:options', LIVE_SORTS: 'constant:sorts' }, { 'A.f': 'constant:sorts' }, registry);
      assert.equal(propertyName(objectProperty(call.arguments[0], 'livePageSort').property), key);
    }
  }
  const near = exactlyOne(findNodes(section, (n) => n.type === 'CallExpression' && n.callee.type === 'SequenceExpression' && member(n.callee.expressions.at(-1), 'U', 'useCallback')), 'near-end callback').arguments[0];
  compareFunction('complete near-end callback', near, result(local('createLiveSectionNearEnd')), { x: 'input:hasNext', p: 'input:fetchingNext', h: 'operation:fetchNext' }, undefined, {}, registry);
  const completion = exactlyOne(findNodes(section, (n) => n.type === 'CallExpression' && n.callee.type === 'SequenceExpression' && member(n.callee.expressions.at(-1), 'U', 'useEffect')), 'completion callback').arguments[0];
  compareFunction('complete completion callback', completion, result(local('createLiveSectionCompletion')), { f: 'input:loading', s: 'operation:complete', e: 'input:section' }, undefined, {}, registry);
  compare('responsive card-count input', top(selected.get(647145), 'l').init, local('LIVE_CARD_COUNTS').init, {}, {}, {}, selected.get(647145));
  const sectionView = local('liveSectionView');
  compare('show-all condition', declared(section, 'g'), declared(sectionView, 'g'),
    { r: 'input:showAll', u: 'input:data', x: 'input:hasNext' }, { r: 'input:showAll', u: 'input:data', x: 'input:hasNext', LIVE_CARD_COUNTS: 'constant:cards' }, { 'l.g': 'constant:cards' }, registry);
  const originalGuards = section.body.body.filter((n) => n.type === 'IfStatement');
  const localGuards = sectionView.body.body.filter((n) => n.type === 'IfStatement');
  assert.equal(originalGuards.length, 2); assert.equal(localGuards.length, 2);
  for (let i = 0; i < 2; i++) compare(`section body guard ${i}`, originalGuards[i].test, localGuards[i].test, { f: 'input:loading', u: 'input:data' }, undefined, {}, registry);
  const carousel = exactlyOne(findNodes(section, (n) => n.type === 'CallExpression' && n.arguments[0] && member(n.arguments[0], 'l', 'X')), 'actual carousel handoff').arguments[1];
  const sectionViewResult = result(sectionView);
  for (const field of ['livestreams', 'useViewportIntersection', 'eager']) compare(`carousel ${field} input`, objectProperty(carousel, field), objectProperty(sectionViewResult, field),
    { u: 'input:data', n: 'input:expanded', d: 'input:eager' }, undefined, {}, registry);
  compare('carousel wrapping class input', objectProperty(carousel, 'scrollContainerClassName').arguments[0], objectProperty(sectionViewResult, 'scrollContainerClassName'), { n: 'input:expanded' }, undefined, {}, registry);
  for (const node of [section, entries, selected.get(31113).node, exported(selected.get(558898), 558898, 'S')]) {
    const f = node === section || node === entries ? registry : node === selected.get(31113).node ? selected.get(31113) : selected.get(558898);
    witness(f, node, 'complete caller/registry or external playlist-schema boundary');
  }
  // Reuse the accepted normalizer's source proof; do not copy its operations or
  // reclassify the generic query transport as implemented by this unit.
  const shared = await verifySession(root);
  const dependencies = ['reconstruction/search-session/session.mjs', 'scripts/verify-search-session.mjs', 'scripts/original-contracts/source.mjs'];
  const dependencyHashes = Object.fromEntries(await Promise.all(dependencies.map(async (p) => [p, sha256(await readFile(path.join(root, p)))])));
  return { schemaVersion: 1, baseCommit: '094a06f18df738d41e77070c1a009e135671ac1a', anchors: corpus.anchors,
    adapterSha256: sha256(bytes), factories, imports, fragments, comparisons, dependencyHashes,
    acceptedNormalizerProofSha256: sha256(JSON.stringify(shared)),
    limits: { capturedExecution: false, networkAcquisition: false, anonymousAccessEstablished: false,
      activeRuntimeWinner: false, serviceOrCacheOrReactImplementation: false, mountedUI: false, nativeCompatibility: false,
      callbackComparison: 'Lexical alpha comparison from accepted search-session verifier; function declaration wrappers compare as arrows, with original parameters/body/async flag, explicit free/import roles and !0/!1 normalization.' } };
}

export async function verifyLiveListing(root = APP_ROOT) {
  const proof = await buildLiveListingProof(root);
  assert.deepEqual(JSON.parse(await readFile(path.join(root, PROOF), 'utf8')), proof, 'live listing provenance differs');
  return proof;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const mode = process.argv[2];
  if (mode === '--write') await writeFile(path.join(APP_ROOT, PROOF), `${JSON.stringify(await buildLiveListingProof(), null, 2)}\n`);
  else { assert.equal(mode, '--check'); await verifyLiveListing(); }
  console.log('Live listing source proof PASS');
}
