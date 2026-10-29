import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse, parseExpression } from '@babel/parser';
import { openCorpus, findNodes, exactlyOne, member, propertyName, objectProperty, sha256 } from '../../scripts/original-contracts/source.mjs';
import { parseFlightRecords } from '../../scripts/settings-client-contract.mjs';
import { normalizeSession } from '../../scripts/verify-search-session.mjs';

export const APP_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
export const DIRECTORY = 'reconstruction/go-screener-data';
export const PROOF = `${DIRECTORY}/PROVENANCE.json`;
const ignored = new Set(['start', 'end', 'loc', 'extra', 'comments', 'errors', 'leadingComments', 'trailingComments', 'innerComments']);
const globals = new Set(['Date', 'Number', 'String', 'Boolean', 'Map', 'Set', 'Math', 'Object', 'Error', 'undefined']);
const functions = new Set(['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression']);
function bindings(pattern, scope) {
  if (pattern.type === 'Identifier') scope.add(pattern.name);
  else if (pattern.type === 'AssignmentPattern') bindings(pattern.left, scope);
  else if (pattern.type === 'ObjectPattern') for (const p of pattern.properties) bindings(p.type === 'RestElement' ? p.argument : p.value, scope);
  else if (pattern.type === 'ArrayPattern') for (const p of pattern.elements) if (p) bindings(p, scope);
  else if (pattern.type === 'RestElement') bindings(pattern.argument, scope);
  else throw new Error(`unsupported GO binding ${pattern.type}`);
}
// Keep actual local binding names and syntax. Only FREE names/qualified imports
// map to recorded capabilities/constants; loop/function/block shadowing remains.
// This is a bounded comparator, not a compiler or captured-code evaluator.
function canonical(node, roles = {}, targets = {}) {
  const clean = (value) => !value || typeof value !== 'object' ? value : Array.isArray(value) ? value.map(clean)
    : Object.fromEntries(Object.entries(value).filter(([k]) => !ignored.has(k)).map(([k, v]) => [k, k === 'shorthand' ? false : clean(v)]));
  const replacement = (text) => clean(parseExpression(text));
  const bound = (name, scopes) => scopes.some((s) => s.has(name));
  function visit(value, scopes = [], parent, key) {
    if (!value || typeof value !== 'object') return value;
    if (Array.isArray(value)) return value.map((v) => visit(v, scopes, parent, key));
    let current = scopes;
    if (functions.has(value.type)) {
      const scope = new Set(); for (const p of value.params) bindings(p, scope);
      if (value.id) scope.add(value.id.name); current = [...scopes, scope];
    } else if (value.type === 'BlockStatement') {
      const scope = new Set();
      for (const s of value.body) if (s.type === 'VariableDeclaration') for (const d of s.declarations) bindings(d.id, scope);
      else if (s.type === 'FunctionDeclaration') scope.add(s.id.name);
      current = [...scopes, scope];
    } else if (['ForOfStatement', 'ForInStatement', 'ForStatement'].includes(value.type)) {
      const scope = new Set(), declaration = value.left ?? value.init;
      if (declaration?.type === 'VariableDeclaration') for (const d of declaration.declarations) bindings(d.id, scope);
      current = [...scopes, scope];
    }
    if (value.type === 'UnaryExpression' && value.operator === '!' && value.argument.type === 'NumericLiteral' && [0, 1].includes(value.argument.value)) return { type: 'BooleanLiteral', value: !value.argument.value };
    if (value.type === 'MemberExpression' && !value.computed && value.object.type === 'Identifier' && !bound(value.object.name, current)) {
      const target = targets[`${value.object.name}.${propertyName(value.property)}`];
      if (target) return replacement(target);
    }
    if (value.type === 'SequenceExpression' && value.expressions.length === 2 && value.expressions[0].type === 'NumericLiteral' && value.expressions[0].value === 0) {
      const last = value.expressions[1];
      if (last.type === 'MemberExpression' && targets[`${last.object.name}.${propertyName(last.property)}`] && !bound(last.object.name, current)) return visit(last, current);
    }
    if (value.type === 'Identifier') {
      const property = key === 'key' && parent?.type === 'ObjectProperty' && !parent.computed || key === 'property' && ['MemberExpression', 'OptionalMemberExpression'].includes(parent?.type) && !parent.computed;
      if (property || bound(value.name, current) || globals.has(value.name)) return { type: 'Identifier', name: value.name };
      if (!(value.name in roles)) throw new Error(`unbound GO name ${value.name}`);
      return replacement(roles[value.name]);
    }
    return Object.fromEntries(Object.entries(value).filter(([k]) => !ignored.has(k)).map(([k, v]) => [k, k === 'shorthand' ? false : visit(v, current, value, k)]));
  }
  return visit(node);
}
const callable = (n) => ({ type: 'ArrowFunctionExpression', async: !!n.async, params: n.params, body: n.body, start: n.start, end: n.end });
const top = (f, name) => exactlyOne(f.node.body.body.flatMap((n) => n.type === 'VariableDeclaration' ? n.declarations : []).filter((n) => n.id.name === name), `top ${name}`);
const declared = (node, name) => exactlyOne(findNodes(node, (n) => n.type === 'VariableDeclarator' && n.id.name === name && n.init), `declaration ${name}`).init;
function exp(f, name) {
  const array = exactlyOne(findNodes(f.node, (n) => n.type === 'CallExpression' && member(n.callee, f.runtime, 's') &&
    (n.arguments[1]?.value === f.id || f.ids.length === 1 && n.arguments.length === 1) && n.arguments[0]?.elements?.some((e) => e?.value === name)), `export ${f.id}.${name}`).arguments[0].elements;
  const i = array.findIndex((e) => e?.value === name); assert.equal(array[i + 1].value, 0);
  const node = array[i + 2];
  return node.type !== 'Identifier' ? node : f.node.body.body.find((n) => n.type === 'FunctionDeclaration' && n.id.name === node.name) ?? top(f, node.name).init;
}

async function originContext(corpus, parent, loader, screener) {
  const html = await corpus.capture('evidence/web/objects/e66810e11f481135');
  assert.equal(html.record.url, 'https://pump.fun/go'); assert.equal(html.record.final_url, html.record.url);
  const pushes = [...html.text.matchAll(/<script>self\.__next_f\.push\(([\s\S]*?)\)<\/script>/g)]
    .map((m) => ({ match: m, value: JSON.parse(m[1]) })).filter(({ value }) => value.length === 2 && value[0] === 1 && typeof value[1] === 'string');
  assert.equal(pushes.length, 3);
  const stream = pushes.map((p) => p.value[1]).join(''), records = parseFlightRecords(stream);
  assert.equal(records.get('11a').kind, 'import'); assert.equal(records.get('11a').value[0], 768385);
  assert.equal(records.get('11a').value[2], '$119'); assert.equal(records.get('119').value, 'BountiesDiscoverRoutePage');
  assert.deepEqual(records.get('82').value.slice(0, 2), ['$', '$L11a']);
  assert.ok(Object.hasOwn(records.get('82').value[3], 'trendingTab'));
  const link = exactlyOne([...html.text.matchAll(/<a\b[^>]*href="\/go\/bounties"[^>]*>[\s\S]*?<\/a>/g)], 'retained main-app Bounties tab');
  const scripts = new Set([...html.text.matchAll(/<script\b[^>]*src="([^"]+)"/g)].map((m) => new URL(m[1], html.record.url).href));
  for (const relative of [parent.provenance.source, loader.provenance.source]) {
    const asset = await corpus.capture(relative); assert.ok(scripts.has(asset.record.url)); assert.equal(new URL(asset.record.url).origin, 'https://pump.fun');
  }
  const asset = await corpus.capture(screener.provenance.source);
  assert.equal(asset.record.url, 'https://pump.fun/_next/static/immutable/chunks/3v64vaswz40vp.js');
  assert.ok(!scripts.has(asset.record.url));
  return { capture: { source: html.record.path, url: html.record.url, sha256: html.record.sha256, bytes: html.record.bytes },
    pushes: pushes.map(({ match }) => html.witness({ start: match.index, end: match.index + match[0].length }, 'inert main-app Flight push')),
    decodedFlightSha256: sha256(stream), usedImport: { row: '11a', module: 768385, nameRow: '119', name: records.get('119').value },
    actualElement: { row: '82', tag: '$L11a', propKeys: Object.keys(records.get('82').value[3]) },
    routeAnchor: html.witness({ start: link.index, end: link.index + link[0].length }, 'actual first-party /go/bounties tab'),
    observed: 'Only https://pump.fun/go HTML/Flight observed. /go/bounties selection is bound through actual pathname/route/lazy source, not a captured route response or mounted execution.' };
}

export async function buildGoScreenerProof(root = APP_ROOT) {
  const corpus = await openCorpus(root), factories = [], selected = new Map(), fragments = [], comparisons = [], imports = [];
  const counts = new Map([[768385, 1], [409355, 2], [660787, 1], [851373, 1], [170258, 1], [158791, 1], [51447, 1],
    [146742, 2], [310717, 2], [314197, 3], [711902, 3], [959193, 2], [38279, 1], [462024, 2], [260095, 1], [471106, 1], [944410, 2]]);
  for (const [id, count] of counts) {
    const variants = corpus.index.modules.filter((m) => m.ids.includes(id)); assert.equal(variants.length, count, `physical variant census ${id}`);
    for (const m of variants) for (const origin of m.origins) { const f = await corpus.factory(id, { source: origin.source }); factories.push(f.provenance); selected.set(`${id}:${origin.source}`, f); }
  }
  const pick = (id, source) => source ? selected.get(`${id}:${source}`) : exactlyOne([...selected.values()].filter((f) => f.id === id), `unique ${id}`);
  const bytes = await readFile(path.join(root, DIRECTORY, 'screener.mjs'));
  const ast = parse(bytes.toString('utf8'), { sourceType: 'module' });
  const local = (name) => exactlyOne(ast.program.body.flatMap((n) => n.type === 'ExportNamedDeclaration' ? n.declaration.type === 'VariableDeclaration' ? n.declaration.declarations : [n.declaration] : []).filter((n) => n.id.name === name), `editable ${name}`);
  const witness = (f, node, label) => { const w = f.witness(node, label); fragments.push(w); return w; };
  const compare = (f, original, actual, label, roles = {}, localRoles = roles, targets = {}) => {
    const expected = canonical(original, roles, targets), actualShape = canonical(actual, localRoles);
    assert.deepEqual(actualShape, expected, `GO source differs: ${label}`);
    comparisons.push({ ...witness(f, original, label), roles, localRoles, targets, structuralSha256: sha256(JSON.stringify(actualShape)) });
  };
  const compareFn = (f, original, actual, ...rest) => compare(f, callable(original), callable(actual), ...rest);
  const compareSimpleFn = (f, original, actual, label) => {
    const expected = normalizeSession(callable(original), {}), observed = normalizeSession(callable(actual), {});
    assert.deepEqual(observed, expected, `GO source differs: ${label}`);
    comparisons.push({ ...witness(f, original, label), structuralSha256:sha256(JSON.stringify(observed)),
      comparison:'Existing accepted lexical alpha comparator for simple parameter-only clamp/sort expressions' });
  };
  const parent = pick(768385), loader = pick(660787), screener = pick(851373), query = pick(170258), helpers = pick(51447), builder = pick(158791);
  const origin = await originContext(corpus, parent, loader, screener);
  for (const f of [parent, loader, screener, query, helpers, builder]) witness(f, f.node, 'complete main-app caller/loader/query/filter context');
  const imported = (f, id) => {
    const n = exactlyOne(f.node.body.body.flatMap((n) => n.type === 'VariableDeclaration' ? n.declarations : []).filter((n) => n.init?.type === 'CallExpression' && member(n.init.callee, f.runtime, 'i') && n.init.arguments[0]?.value === id), `actual import ${f.id}→${id}`);
    imports.push(f.witness(n, `actual import ${f.id}→${id}`)); return n.id.name;
  };
  for (const id of [409355, 170258, 158791, 51447]) imported(parent, id);
  for (const id of [170258, 51447, 158791, 260095, 471106]) imported(screener, id);
  for (const id of [944410, 38279, 146742, 314197, 711902, 310717]) imported(query, id);
  // Assert the actual conditional/lazy path, not mere numeric ID presence.
  const lazy = exactlyOne(findNodes(parent.node, (n) => n.type === 'CallExpression' && member(n.callee, parent.runtime, 'A') && n.arguments[0]?.value === 660787), 'actual screener lazy import');
  witness(parent, lazy, 'actual lazy import660787');
  const lazyThen = exactlyOne(findNodes(parent.node, (n) => n.type === 'ArrowFunctionExpression' && n.body.type === 'ObjectExpression' && n.body.properties.some((p) => p.value?.property?.name === 'ScreenerListingView')), 'lazy named export');
  witness(parent, lazyThen, 'ScreenerListingView lazy named handoff');
  const discoverEntry = exp(parent, 'BountiesDiscoverRoutePage'), discover = top(parent, 'eY').init;
  witness(parent, exactlyOne(findNodes(discoverEntry, (n) => n.type === 'CallExpression' && n.arguments[0]?.name === 'eY'), 'used discover child'), 'actual Flight component→discover child');
  const pathname = exactlyOne(findNodes(discover, (n) => n.type === 'CallExpression' && n.callee.type === 'SequenceExpression' && member(n.callee.expressions.at(-1), 'm', 'usePathname')), 'actual pathname input');
  witness(parent, pathname, 'main-app pathname source');
  const routeSelection = exactlyOne(findNodes(discover,(n)=>n.type==='AssignmentExpression'&&n.left.name==='e'&&n.right.type==='ConditionalExpression'&&
    findNodes(n.right,(n)=>member(n,'x','b')).length===1),'actual pathname route selection');
  witness(parent,routeSelection,'actual pathname→bounties route classification');
  const bountyBranch = exactlyOne(findNodes(discover,(n)=>n.type==='AssignmentExpression'&&n.left.name==='ec'&&n.right.type==='ConditionalExpression'),'used bounties branch');
  assert.equal(bountyBranch.right.test.left.value,'bounties');assert.equal(bountyBranch.right.test.right.name,'ez');
  const lazyRender=exactlyOne(findNodes(bountyBranch.right.consequent,(n)=>n.type==='CallExpression'&&n.arguments[0]?.name==='e$'),'actual lazy screener element');
  assert.deepEqual(lazyRender.arguments[1].properties.map((p)=>propertyName(p.key)),['filters','nearMe','onFacetsChange','onTimeLeftCountsChange','sortKey','viewMode']);
  witness(parent,bountyBranch,'actual bounties tab→lazy screener props');
  for (const f of selected.values()) if (f.id === 409355) {
    assert.equal(exp(f, 'b').value, '/go/bounties'); witness(f, exp(f, 'b'), 'main-app bounty route constant');
  }
  assert.ok(findNodes(parent.node, (n) => n.type === 'MemberExpression' && member(n, 'x', 'b')).length >= 1);
  const loaderImport = exactlyOne(findNodes(loader.node, (n) => n.type === 'CallExpression' && n.callee.name === 's' && n.arguments[0]?.value === 851373), 'actual loaded screener module');
  witness(loader, loaderImport, 'loader imports851373');
  const chunk = exactlyOne(findNodes(loader.node, (n) => n.type === 'StringLiteral' && n.value === 'static/immutable/chunks/3v64vaswz40vp.js'), 'actual lazy chunk'); witness(loader, chunk, 'same-origin captured lazy chunk');
  for (const f of [...selected.values()].filter((f) => f.id === 310717)) compareSimpleFn(f, exp(f, 'f'), local('clampBountyQuery').init, 'complete UTF16 query clamp');
  for (const f of [...selected.values()].filter((f) => f.id === 146742)) {
    compareSimpleFn(f, exp(f, 'G'), local('allowBountySort').init, 'complete follower sort gate');
    compare(f, exp(f, 'H'), local('BOUNTY_PUBLIC_PHASES').init, 'public phase string');
  }
  for (const [symbol, name] of [['L', 'withoutStatuses'], ['h', 'withoutRewardTokens'], ['Z', 'withoutTimeLeft']]) compareFn(helpers, exp(helpers, symbol), local(name).init, `complete ${name}`);
  compare(builder, top(builder, 'o').init, local('BOUNTY_SORTS').init, 'complete sort table');
  compare(builder, top(builder, 'a').init, local('REWARD_RANGE').init, 'reward filter numeric bounds');
  compare(builder, exp(builder, 'w'), local('TIME_LEFT_OPTIONS').init, 'complete time bucket choices');
  for (const f of selected.values()) if (f.id === 462024) compare(f,
    objectProperty(objectProperty(exp(f, 'i'), 'SOL'), 'mint'), objectProperty(local('REWARD_MINTS').init, 'SOL'), 'actual public SOL mint');
  compareFn(builder, exp(builder, 'N'), local('buildBountyFilters'), 'complete filter→query builder',
    { o: 'BOUNTY_SORTS', s: 'REWARD_MINTS', a: 'REWARD_RANGE' },
    { BOUNTY_SORTS: 'BOUNTY_SORTS', REWARD_MINTS: 'REWARD_MINTS', REWARD_RANGE: 'REWARD_RANGE', BOUNTY_PUBLIC_PHASES: 'BOUNTY_PUBLIC_PHASES' },
    { 'n.d': "'OPEN'", 'r.H': 'BOUNTY_PUBLIC_PHASES' });
  compareFn(pick(38279), objectProperty(exp(pick(38279), 'Q'), 'BOUNTY_PUBLIC_LIST_V2_INFINITE'), local('bountyQueryKey').init, 'complete infinite query key');
  const originalQuery = exp(query, 'f'), editableQuery = local('bountyInfiniteQuery');
  compareFn(query, exactlyOne(query.node.body.body.filter((n) => n.type === 'FunctionDeclaration' && n.id.name === 'u'), 'cursor callback'), local('nextBountyCursor'), 'complete cursor callback');
  const arrow = exactlyOne(findNodes(originalQuery, (n) => n.type === 'ArrowFunctionExpression' && n.async), 'complete query read arrow');
  const names = ['G','p','w','g','b','h','v','y','x','S','N','E','B','I','F','A','$','_','L','T','P','D','U'];
  const roles = Object.fromEntries(names.map((n) => [n, n]));
  compareFn(query, arrow, declared(editableQuery, 'queryFn'), 'complete lazy GET→JSON→schema callback', roles, { ...roles, responseSchema: 'responseSchema' }, { 'o.L': 'responseSchema' });
  for (const name of ['P', 'k', 'B', '$']) compare(query, declared(originalQuery, name), declared(editableQuery, name), `query default/gate ${name}`,
    Object.fromEntries(['O','M','C','j','_','L','T'].map((n) => [n,n])));
  compare(query, declared(originalQuery, 'F'), declared(editableQuery, 'F'), 'feature-dependent sort input', { R:'R', C:'C' }, { R:'R', C:'C', allowBountySort:'allowBountySort' }, { 's.G':'allowBountySort' });
  compare(query, declared(originalQuery, 'G'), declared(editableQuery, 'G'), 'normalized query input', { m:'m' }, { m:'m', clampBountyQuery:'clampBountyQuery' }, { 'l.f':'clampBountyQuery' });
  const keyCall = exactlyOne(findNodes(originalQuery, (n) => n.type === 'CallExpression' && n.callee.property?.name === 'BOUNTY_PUBLIC_LIST_V2_INFINITE'), 'actual key invocation');
  compare(query, keyCall.arguments[0], declared(editableQuery, 'queryKey').arguments[0], 'complete query key inputs', roles);
  const operations = local('createBountyFilterOperations');
  compareFn(builder, exp(builder, 'v'), declared(operations, 'classifyPhase'), 'complete phase classifier', {}, { now:'now' }, { 'Date.now':'now' });
  compareFn(helpers, top(helpers, 'r').init, local('timeLeftMatches').init, 'complete local time-left predicate');
  for (const [symbol, name] of [['k','facets'],['t','countTimeLeft'],['x','filterTasks']]) compareFn(helpers, exp(helpers, symbol), declared(operations, name), `complete local ${name}`,
    { r:'timeLeftMatches' }, { now:'now', classifyPhase:'classifyPhase', TIME_LEFT_OPTIONS:'TIME_LEFT_OPTIONS', REWARD_MINTS:'REWARD_MINTS', REWARD_RANGE:'REWARD_RANGE', timeLeftMatches:'timeLeftMatches' },
    { 'Date.now':'now', 't.v':'classifyPhase', 't.w':'TIME_LEFT_OPTIONS', 't.h':'REWARD_MINTS', 't.V':'REWARD_RANGE' });
  compareFn(pick(471106), exp(pick(471106), 'N'), local('bountyFeedItem'), 'complete feed projection');
  compareFn(screener, exactlyOne(screener.node.body.body.filter((n) => n.type === 'FunctionDeclaration' && n.id.name === 'v'), 'page items'), local('bountyPageItems'), 'complete page flatten callback');
  const caps = (...names) => Object.fromEntries(names.map((n) => [n,n]));
  const view = exp(screener,'ScreenerListingView'), facade = local('createGoScreener');
  const plan = exactlyOne(findNodes(facade,(n)=>n.type==='ObjectMethod'&&propertyName(n.key)==='plan'),'facade plan');
  const derive = exactlyOne(findNodes(facade,(n)=>n.type==='ObjectMethod'&&propertyName(n.key)==='derive'),'facade derive');
  const own = (name) => declared(derive,name);
  const assignment = (name,predicate=()=>true) => exactlyOne(findNodes(view,(n)=>n.type==='AssignmentExpression'&&n.left.name===name&&predicate(n.right)),`screener assignment ${name}`).right;
  const calls = (object,key) => findNodes(view,(n)=>n.type==='CallExpression'&&n.callee.type==='SequenceExpression'&&member(n.callee.expressions.at(-1),object,key));
  for(const [name,input] of [['listing','H'],['phaseFacets','V']]) {
    const original = assignment(name==='listing'?'n':'i',(n)=>n.type==='CallExpression');
    assert.ok(member(original.callee.expressions.at(-1),'d','N'));
    const actual = declared(plan,name);
    assert.equal(actual.callee.name,'buildBountyFilters');
    compare(screener,original.arguments[0],{...actual.arguments[0],properties:actual.arguments[0].properties.filter((p)=>propertyName(p.key)!=='now')},`complete ${name} filter-builder inputs`,
      {K:'sortKey',z:'filters',F:'nearMe'},caps('sortKey','filters','nearMe','withoutStatuses'),{'u.L':'withoutStatuses'});
    assert.equal(objectProperty(actual.arguments[0],'now').name,'now');
    const queryArgs=assignment(name==='listing'?'w':'_',(n)=>n.type==='ObjectExpression');
    const actualRead=objectProperty(plan.body.body.at(-1).argument,name);
    assert.equal(actualRead.callee.name,'bountyInfiniteQuery');
    compare(screener,queryArgs,actualRead.arguments[0],`complete ${name} query handoff`,{[input]:name},caps(name));
  }
  const flatten=exactlyOne(findNodes(view,(n)=>n.type==='ArrowFunctionExpression'&&n.body.type==='LogicalExpression'&&
    findNodes(n.body,(n)=>['CallExpression','OptionalCallExpression'].includes(n.type)&&propertyName(n.callee.property)==='flatMap').length===1),'actual selected-page flatten');
  compare(screener,flatten.body,own('tasks'),'served task flatten/nullish default',{Z:'listingResult.data',v:'bountyPageItems'},caps('listingResult','bountyPageItems'));
  compare(screener,declared(view,'ee'),own('serverPhases'),'first proxy page phase facets',{Y:'facetsResult.data'},caps('facetsResult'));
  const filterTargets={'u.x':'operations.filterTasks','u.L':'withoutStatuses','u.h':'withoutRewardTokens','u.Z':'withoutTimeLeft','u.k':'operations.facets','u.t':'operations.countTimeLeft'};
  const ownCaps=caps('operations','tasks','filters','withoutStatuses','withoutRewardTokens','withoutTimeLeft');
  for(const [symbol,name] of [['L','noStatuses'],['h','noRewardTokens']]) {
    const call=exactlyOne(calls('u','x').filter((n)=>n.arguments[1]?.type==='CallExpression'&&member(n.arguments[1].callee.expressions.at(-1),'u',symbol)),`actual ${name} local filter`);
    compare(screener,call,own(name),`complete ${name} facet filter`,{$:'tasks',z:'filters'},ownCaps,filterTargets);
  }
  compare(screener,assignment('N',(n)=>n.type==='LogicalExpression'),own('phase'),'server phase/fallback precedence',
    {ee:'serverPhases',e:'noStatuses'},caps('serverPhases','noStatuses','operations'),filterTargets);
  compare(screener,assignment('M',(n)=>n.type==='CallExpression'),own('reward'),'local reward facet input',
    {t:'noRewardTokens'},caps('operations','noRewardTokens'),filterTargets);
  compare(screener,assignment('R',(n)=>n.type==='ObjectExpression'),own('facets'),'complete facet handoff',
    {N:'phase',L:'EMPTY_STATUSES',M:'reward'},caps('phase','EMPTY_STATUSES','reward'));
  const ownEmpty=exactlyOne(ast.program.body.filter((n)=>n.type==='VariableDeclaration').flatMap((n)=>n.declarations).filter((n)=>n.id.name==='EMPTY_STATUSES'),'empty status constant').init;
  compare(screener,top(screener,'g').init,ownEmpty,'shared empty status array');
  compare(screener,exactlyOne(calls('u','t'),'actual time-count calculation'),own('timeLeftCounts'),'complete time-left count handoff',
    {$:'tasks',z:'filters'},ownCaps,filterTargets);
  const enrichment=exactlyOne(calls('a','E'),'used task enrichment');
  const ownEnrichment=exactlyOne(findNodes(derive,(n)=>n.type==='CallExpression'&&n.callee.name==='enrichTasks'),'editable enrichment');
  compare(screener,enrichment,ownEnrichment,'actual served tasks→enrichment capability',{$:'tasks'},caps('tasks','enrichTasks'),{'a.E':'enrichTasks'});
  const mapper=exactlyOne(findNodes(view,(n)=>n!==view&&n.type==='ArrowFunctionExpression'&&findNodes(n,(n)=>n.type==='CallExpression'&&n.callee.type==='SequenceExpression'&&member(n.callee.expressions.at(-1),'l','N')).length===1),'actual feed mapper');
  compareFn(screener,mapper,own('items').arguments[0],'complete task-order→resolved bounty/feed mapper',
    {ei:'byId',es:'liveTokens'},caps('byId','liveTokens','bountyFeedItem'),{'l.N':'bountyFeedItem'});
  const mintLoop=exactlyOne(findNodes(view,(n)=>n.type==='ForOfStatement'&&n.right.type==='SequenceExpression'&&n.right.expressions[0]?.left?.name==='C'),'actual live-mint collection');
  const ownLoop=exactlyOne(findNodes(derive,(n)=>n.type==='ForOfStatement'&&n.right.name==='tasks'),'editable live-mint collection');
  compare(screener,mintLoop.right.expressions[0].right,own('mintSet'),'subscription mint set creation');
  compare(screener,mintLoop.body,ownLoop.body,'complete reward-leg-before-coin mint collection',{e:'e',C:'mintSet'},caps('e','mintSet'));
  compare(screener,assignment('k',(n)=>n.type==='ArrayExpression'),own('visibleMints'),'ordered subscription mint handoff',{C:'mintSet'},caps('mintSet'));
  const sourceResultRoles={Q:'listingResult.hasNextPage',D:'listingResult.isFetchingNextPage',W:'listingResult.fetchNextPage'};
  compare(screener,assignment('E',(n)=>n.type==='ObjectExpression'),own('sentinel'),'complete sentinel inputs',sourceResultRoles,caps('listingResult'));
  const body=own('body');
  for(const [flag,actual] of [['q',body.test],['X',body.alternate.test]]) {
    const guard=exactlyOne(findNodes(view,(n)=>n.type==='IfStatement'&&n.test.type==='LogicalExpression'&&n.test.left.name===flag),'empty data body guard').test;
    compare(screener,guard,actual,`body ${flag} precedence`,{[flag]:flag==='q'?'listingResult.isLoading':'listingResult.isError',$:'tasks'},caps('listingResult','tasks'));
  }
  const empty=exactlyOne(findNodes(view,(n)=>n.type==='IfStatement'&&n.test.type==='BinaryExpression'&&n.test.right.type==='MemberExpression'&&n.test.right.object.name==='$'),'empty body guard').test;
  compare(screener,empty,body.alternate.alternate.test,'empty body precedence',{$:'tasks'},caps('tasks'));
  const returned=derive.body.body.at(-1).argument;
  const subscription=exactlyOne(calls('c','f'),'visible token subscription');
  compare(screener,subscription.arguments[1],objectProperty(returned,'subscribeVisible'),'subscription enabled guard',{ea:'visibleMints'},caps('visibleMints'));
  const footer=exactlyOne(findNodes(view,(n)=>n.type==='CallExpression'&&n.arguments[0]&&member(n.arguments[0],'x','f')),'actual footer').arguments[1];
  compare(screener,footer,objectProperty(returned,'footerProps'),'complete footer inputs',{...sourceResultRoles,eo:'sentinelRef',$:'tasks'},caps('listingResult','sentinelRef','tasks'));
  const feed=exactlyOne(findNodes(view,(n)=>n.type==='CallExpression'&&n.arguments[0]&&member(n.arguments[0],'s','f')),'actual feed').arguments[1];
  const forwarded={...feed,properties:feed.properties.filter((p)=>propertyName(p.key)!=='footer')};
  compare(screener,forwarded,objectProperty(returned,'feedProps'),'complete non-rendered feed inputs',{el:'items',P:'viewMode'},caps('items','viewMode'));
  witness(screener,feed,'complete feed including external JSX footer boundary');
  // Full parser/enrichment/feature/client boundaries remain explicit capabilities.
  for (const f of selected.values()) {
    if (f.id === 711902) witness(f, exp(f, 'L'), 'complete task-list schema declaration; parser external');
    if (f.id === 314197) witness(f, exp(f, 'f'), 'X feature-result capability; not authorization');
    if (f.id === 944410) witness(f, exp(f, 'useLivestreamApiClient'), 'configured client capability; no session read');
    if (f.id === 260095) witness(f, exp(f, 'E'), 'complete used enrichment boundary; provider/viewer inputs external');
    if (f.id === 959193) assert.equal(exp(f, 'd').value, 'OPEN');
  }
  return { schemaVersion:1, baseCommit:'094a06f18df738d41e77070c1a009e135671ac1a', anchors:corpus.anchors,
    adapterSha256:sha256(bytes), origin, factories, imports, fragments, comparisons,
    providerContracts:{client:'944410.useLivestreamApiClient result; get(relativePath,{searchParams}).json(), origin/transport/auth/error/retry behavior external',
      responseSchema:'711902.L actual parse capability; defaults, attachment transformation, stripping/validation are not reimplemented',
      xFeatures:'314197.f supplied feature-result value; controls follower sort/count fields, not backend authorization',
      enrichTasks:'260095.E actual result {bounties,liveTokens}; source viewer/user/token providers and task adaptation remain external',
      now:'Raw Date.now-shaped capability; builder/filter/phase/time-count sampling remains independent',
      queryResult:'Actual170258 infinite-query snapshot; scheduling/cache/error/refetch/cancellation belongs to host',
      parent:'Actual851373 props from conditional768385 main-app bounties branch; parent URL/sync/extra proxy query remains outside recomputation',
      handoff:'Returns actual facet/time-count, token subscription, sentinel/footer/feed inputs; no React effect, observer, subscription or rendering implementation'},
    dependencies: { 'scripts/original-contracts/source.mjs':sha256(await readFile(path.join(root,'scripts/original-contracts/source.mjs'))),
      'scripts/verify-search-session.mjs':sha256(await readFile(path.join(root,'scripts/verify-search-session.mjs'))),
      'scripts/settings-client-contract.mjs':sha256(await readFile(path.join(root,'scripts/settings-client-contract.mjs'))) },
    limits:{ capturedExecution:false, network:false, directBountiesRouteCapture:false, activeRuntimeWinner:false, parserOrEnrichmentImplementation:false,
      providerAuthOrQueryLifecycle:false, mountedUI:false, nativeCompatibility:false, progressCredit:false,
      comparison:'Exact local binding names/syntax and scope-aware recorded free/import substitutions, Boolean spelling normalization and declaration-wrapper→arrow comparison; not universal React equivalence' } };
}
export async function verifyGoScreener(root=APP_ROOT) {
  const proof=await buildGoScreenerProof(root);
  assert.deepEqual(JSON.parse(await readFile(path.join(root,PROOF),'utf8')),proof,'GO screener provenance differs'); return proof;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  if(process.argv[2]==='--write')await writeFile(path.join(APP_ROOT,PROOF),`${JSON.stringify(await buildGoScreenerProof(),null,2)}\n`);
  else {assert.equal(process.argv[2],'--check');await verifyGoScreener();}
  console.log('GO screener source proof PASS');
}
