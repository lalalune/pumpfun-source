import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse, parseExpression } from '@babel/parser';
import { openCorpus, findNodes, exactlyOne, member, propertyName, sha256 } from '../../scripts/original-contracts/source.mjs';

export const APP_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
export const DIRECTORY = 'reconstruction/mayhem-view-data';
export const PROOF = `${DIRECTORY}/PROVENANCE.json`;
const source = 'evidence/web/objects/b5dd8c92e81b5961.js';
const counts = new Map([[457065, 1], [402030, 1], [540480, 1], [609252, 9],
  [849812, 4], [680930, 6], [26077, 1], [653805, 1], [915631, 1]]);
const ignored = new Set(['loc', 'start', 'end', 'range', 'extra', 'comments', 'errors', 'leadingComments', 'trailingComments', 'innerComments']);
function shape(value, replacements = {}, parent, key) {
  if (!value || typeof value !== 'object') return value;
  if (Array.isArray(value)) return value.map((child) => shape(child, replacements));
  const property = key === 'property' && ['MemberExpression', 'OptionalMemberExpression'].includes(parent?.type) && !parent.computed ||
    key === 'key' && parent?.type === 'ObjectProperty' && !parent.computed;
  if (value.type === 'Identifier' && !property && replacements[value.name]) return shape(parseExpression(replacements[value.name]));
  if (value.type === 'UnaryExpression' && value.operator === '!' && value.argument.type === 'NumericLiteral' && [0, 1].includes(value.argument.value))
    return { type: 'BooleanLiteral', value: !value.argument.value };
  return Object.fromEntries(Object.entries(value).filter(([name]) => !ignored.has(name)).map(([name, child]) =>
    [name, name === 'shorthand' ? false : shape(child, replacements, value, name)]));
}
const top = (factory, name) => exactlyOne(factory.node.body.body.flatMap((n) => n.type === 'VariableDeclaration' ? n.declarations : [])
  .filter((n) => n.id.name === name), `top declaration ${name}`);
const fn = (factory, name) => exactlyOne(factory.node.body.body.filter((n) => n.type === 'FunctionDeclaration' && n.id.name === name), `function ${name}`);
const declared = (node, name) => exactlyOne(findNodes(node, (n) => n.type === 'VariableDeclarator' && n.id.name === name), `declaration ${name}`).init;
const assignment = (node, name) => exactlyOne(findNodes(node, (n, parents) => n.type === 'AssignmentExpression' && n.left.name === name &&
  !parents.some((p) => p !== node && /Function|Method/.test(p.type)) &&
  // Select the computed value, not its separate compiler memo-cache read.
  !(n.right.type === 'MemberExpression' && n.right.object.name === 'eA')), `assignment ${name}`).right;
const property = (node, name) => exactlyOne(node.properties.filter((p) => propertyName(p.key) === name), `property ${name}`).value;
function exported(factory, name) {
  const a = exactlyOne(findNodes(factory.node, (n) => n.type === 'CallExpression' && member(n.callee, factory.runtime, 's') &&
    (n.arguments[1]?.value === factory.id || n.arguments.length === 1 && factory.ids.length === 1) &&
    n.arguments[0]?.type === 'ArrayExpression' && n.arguments[0].elements.some((e) => e?.value === name)), `export ${name}`).arguments[0].elements;
  const i = a.findIndex((e) => e?.value === name);
  assert.equal(a[i + 1].value, 0);
  return a[i + 2].type === 'Identifier' ? top(factory, a[i + 2].name).init : a[i + 2];
}
function imported(factory, alias, id) {
  const node = top(factory, alias);
  assert.equal(node.init?.arguments?.[0]?.value, id, `actual import ${alias}`);
  assert.ok(['i', 'r'].some((method) => member(node.init.callee, factory.runtime, method)));
  return factory.witness(node, `import ${alias} → ${id}`);
}

export async function buildMayhemViewProof(root = APP_ROOT) {
  const corpus = await openCorpus(root);
  const editable = await readFile(path.join(root, DIRECTORY, 'view.mjs'));
  const ast = parse(editable.toString('utf8'), { sourceType: 'module' });
  const local = (name) => exactlyOne(ast.program.body.flatMap((n) => n.type === 'ExportNamedDeclaration'
    ? n.declaration.type === 'FunctionDeclaration' ? [n.declaration] : n.declaration.declarations : [])
    .filter((n) => n.id.name === name), `editable ${name}`);
  const factories = [], selected = new Map();
  for (const [id, count] of counts) {
    const variants = corpus.index.modules.filter((m) => m.ids.includes(id));
    assert.equal(variants.length, count, `complete physical variant census ${id}`);
    for (const variant of variants) for (const origin of variant.origins) {
      const f = await corpus.factory(id, { source: origin.source });
      factories.push(f.provenance); selected.set(`${id}:${origin.source}`, f);
    }
  }
  const parent = selected.get(`457065:${source}`);
  const parentMain = exported(parent, 'MayhemScreener');
  const imports = [['a', 402030], ['R', 609252], ['I', 849812], ['T', 915631], ['F', 653805]]
    .map(([alias, id]) => imported(parent, alias, id));
  const fragments = [], comparisons = [];
  const witness = (f, node, label) => {
    const range = Array.isArray(node) ? { start: node[0].start, end: node.at(-1).end } : node;
    const result = f.witness(range, label); fragments.push(result); return result;
  };
  function compare(label, original, actual, substitutions = {}) {
    assert.deepEqual(shape(original, substitutions), shape(actual), `source expression/callback differs: ${label}`);
    comparisons.push({ ...witness(parent, original, label), substitutions,
      structuralSha256: sha256(JSON.stringify(shape(actual))) });
  }
  const providerCalls = [];
  for (const [alias, symbol, input] of [['I', 'b', 'eG'], ['R', 'f', 'h'], ['T', 'f', 'e4']]) {
    const call = exactlyOne(findNodes(parentMain, (n) => n.type === 'CallExpression' &&
      n.callee.type === 'SequenceExpression' && member(n.callee.expressions.at(-1), alias, symbol)), `actual ${alias}.${symbol} provider call`);
    assert.equal(call.arguments[0].name, input, `provider ${alias}.${symbol} actual input`);
    providerCalls.push(witness(parent, call, `actual ${alias}.${symbol}(${input}) provider handoff`));
  }
  witness(parent, top(parent, 'j'), 'byMint subscription selector');
  const update = property(top(parent, 'w').init.arguments[0].body, 'update');
  compare('complete store update callback', update, local('createMayhemUpdate').body.body[0].argument);
  const event = exactlyOne(findNodes(parentMain, (n) => n.type === 'ArrowFunctionExpression' && n.params[0]?.name === 't' &&
    findNodes(n.body, (x) => x.type === 'OptionalMemberExpression' && x.object.name === 't' && propertyName(x.property) === 'mint').length > 0), 'event callback');
  compare('complete Unified event callback', event, local('createMayhemEvent').body.body[0].argument);
  for (const [oldName, newName] of [['Q', 'previousMayhemPage'], ['J', 'mayhemMint'], ['ee', 'mayhemMint'],
    ['X', 'newestMayhemFirst'], ['Z', 'largestMayhemFirst']]) {
    compare(`complete ${oldName} parameters`, fn(parent, oldName).params, local(newName).params);
    compare(`complete ${oldName} body`, fn(parent, oldName).body, local(newName).body);
  }
  // Actual barrel getter and leaf constant, not a presumed numeric-ID alias.
  const barrel = selected.get('402030:evidence/web/objects/2b47dd0b38a1608f.js');
  imports.push(imported(barrel, 'eR', 540480));
  const getter = exactlyOne(findNodes(barrel.node, (n) => n.type === 'CallExpression' && member(n.callee, 'Object', 'defineProperty') &&
    n.arguments[1]?.value === 'MAYHEM_MODES'), 'MAYHEM_MODES getter');
  const getBody = property(getter.arguments[2], 'get');
  assert.ok(member(getBody.body.body[0].argument, 'eR', 'MAYHEM_MODES'));
  witness(barrel, getter, '402030 actual MAYHEM_MODES forwarding getter');
  const leaf = selected.get('540480:evidence/web/objects/2b47dd0b38a1608f.js');
  const modes = exactlyOne(findNodes(leaf.node, (n) => n.type === 'AssignmentExpression' &&
    propertyName(n.left.property) === 'MAYHEM_MODES' && n.right.type === 'ArrayExpression'), 'mode values');
  assert.deepEqual(shape(modes.right), shape(local('MAYHEM_MODES').init));
  witness(leaf, modes, '540480 MAYHEM_MODES values');
  const modeCheck = top(parent, 'L').init;
  const adaptedModeCheck = structuredClone(modeCheck);
  exactlyOne(findNodes(adaptedModeCheck, (n) => member(n, 'a', 'MAYHEM_MODES')), 'qualified mode import');
  // Replace the one authenticated qualified value, preserving its includes call.
  const includes = exactlyOne(findNodes(adaptedModeCheck, (n) => n.type === 'MemberExpression' && propertyName(n.property) === 'includes'), 'mode includes');
  includes.object = { type: 'Identifier', name: 'MAYHEM_MODES' };
  assert.deepEqual(shape(adaptedModeCheck), shape(local('isMayhemMode').init));
  witness(parent, modeCheck, 'L hydration-only valid-mode predicate');

  const view = local('deriveMayhemView');
  compare('base query nullish array', assignment(parentMain, 'o'), declared(view, 'coins'), { eq: 'data' });
  compare('base query mint provider input', assignment(parentMain, 'd'), declared(view, 'mints'), { eK: 'coins', ee: 'mayhemMint' });
  compare('hydration limit', declared(parentMain, 'eJ'), declared(view, 'hydrationLimit'), { eG: 'mints' });
  compare('hydration disabled', declared(parentMain, 'eX'), declared(view, 'hydrationDisabled'), { eG: 'mints' });
  compare('complete hydration descriptor', assignment(parentMain, 'h'), declared(view, 'hydration'), { eG: 'mints', eJ: 'hydrationLimit', eX: 'hydrationDisabled' });
  const modeLoop = exactlyOne(findNodes(parentMain, (n) => n.type === 'ForOfStatement'), 'hydrated mode loop');
  compare('complete hydrated mode map loop', modeLoop, exactlyOne(findNodes(view, (n) => n.type === 'ForOfStatement'), 'editable mode loop'),
    { e: 'coin', t: 'mode', x: 'modes', eZ: 'hydratedCoins', L: 'isMayhemMode' });
  const volume = exactlyOne(findNodes(parentMain, (n) => n.type === 'ArrowFunctionExpression' && n.body.type === 'LogicalExpression' &&
    findNodes(n.body, (x) => x.type === 'Identifier' && x.name === 'eQ').length > 0), 'volume reader');
  compare('complete activity volume reader', volume, declared(view, 'volume'), { e: 'coin', eQ: 'marketActivity' });
  compare('page count', declared(parentMain, 'e2'), declared(view, 'pageCount'), { e1: 'ordered' });
  compare('current page upper clamp', declared(parentMain, 'e3'), declared(view, 'currentPage'), { ez: 'pageIndex', e2: 'pageCount' });
  compare('ten-row slice', assignment(parentMain, 'p'), declared(view, 'pageCoins'), { e1: 'ordered', e3: 'currentPage' });
  compare('visible subscription mint handoff', assignment(parentMain, 'j'), declared(view, 'visibleMints'), { e5: 'pageCoins', J: 'mayhemMint' });
  const result = view.body.body.at(-1).argument;
  compare('paused refetch interval', declared(parentMain, 'eY'), property(result, 'refetchInterval'), { eP: 'paused' });
  const subscription = exactlyOne(findNodes(parentMain, (n) => n.type === 'CallExpression' &&
    n.callee.type === 'SequenceExpression' && member(n.callee.expressions.at(-1), 'T', 'f')), 'actual visible subscription');
  compare('visible subscription enabled input', subscription.arguments[1], property(result, 'subscribeVisible'), { e4: 'visibleMints' });
  const body = assignment(parentMain, 'ej'), localBody = declared(view, 'body');
  compare('loading body precedence', body.test, localBody.test, { eV: 'isLoading' });
  compare('error body precedence', body.alternate.test, localBody.alternate.test, { eW: 'isError' });
  compare('empty body precedence', body.alternate.alternate.test, localBody.alternate.alternate.test, { e1: 'ordered' });
  compare('pagination visibility test', assignment(parentMain, 'ek').test, property(property(result, 'pagination'), 'visible').argument,
    { eV: 'isLoading', eW: 'isError', e1: 'ordered' });
  const next = exactlyOne(findNodes(parentMain, (n) => n.type === 'ArrowFunctionExpression' && n.body.type === 'CallExpression' &&
    member(n.body.callee, 'Math', 'min') && findNodes(n.body, (n) => n.type === 'Identifier' && n.name === 'e2').length > 0), 'next-page updater');
  compare('next-page updater result', next.body, local('nextMayhemPage').body.body[0].argument, { e2: 'pageCount', e: 'index' });
  const row = fn(parent, 'G');
  const rowCallback = exactlyOne(findNodes(view, (n) => n.type === 'ArrowFunctionExpression' && n.body.type === 'BlockStatement' &&
    findNodes(n.body, (x) => x.type === 'ObjectProperty' && propertyName(x.key) === 'telemetryMarketCap').length > 0), 'editable row projection');
  const rowResult = rowCallback.body.body.at(-1).argument;
  const rowProps = exactlyOne(findNodes(parentMain, (n) => n.type === 'ObjectExpression' &&
    n.properties.some((p) => propertyName(p.key) === 'coin') && n.properties.some((p) => propertyName(p.key) === 'rank')), 'actual G row props');
  const rowProp = (name) => property(rowProps, name);
  compare('actual row rank handoff', rowProp('rank'), property(rowResult, 'rank'), { e3: 'currentPage', n: 'index' });
  compare('actual row activity handoff', rowProp('change'), declared(rowCallback, 'change'), { eQ: 'marketActivity', e: 'coin' });
  compare('actual row hydrated mode handoff', rowProp('mode'), declared(rowCallback, 'modeFallback'), { e0: 'modes', e: 'coin' });
  compare('live state nullish fallback', declared(fn(parent, 'z'), 'm'), property(rowResult, 'state'), { l: 'live', r: 'coin.mayhem_state' });
  compare('live mode nullish fallback', declared(fn(parent, 'H'), 'm'), declared(rowCallback, 'mode'), { l: 'live', r: 'modeFallback' });
  compare('live market cap undefined-only fallback', declared(fn(parent, 'P'), 'c'), declared(rowCallback, 'marketCap'),
    { m: 'liveMarketCap', l: 'coin.usd_market_cap' });
  const positiveCap = exactlyOne(findNodes(fn(parent, 'P'), (n) => n.type === 'ConditionalExpression' && n.test.type === 'BinaryExpression' &&
    n.test.operator === '>' && n.test.left.name === 'c'), 'positive-cap branch');
  compare('positive display cap test', positiveCap.test, property(rowResult, 'marketCapPositive'), { c: 'marketCap' });
  const volumeDisplay = exactlyOne(findNodes(row, (n) => n.type === 'AssignmentExpression' && n.left.name === 'w' && n.right.type === 'ConditionalExpression'), 'volume display');
  compare('volume presence including zero', volumeDisplay.right.test, property(rowResult, 'volumePresent'), { L: 'change' });
  compare('chart creation timestamp input', declared(row, 'et'), property(rowResult, 'createdTimestamp'), { T: 'coin' });
  compare('chart trend class input', declared(row, 'en'), property(rowResult, 'trendClass'), { L: 'change' });
  compare('telemetry base cap input', declared(row, 'X'), property(rowResult, 'telemetryMarketCap'), { T: 'coin' });

  // Full parent/row helpers retain the branches, join sites and JSX handoff;
  // descriptive result keys in the pure facade are authored projection names.
  for (const name of ['G', 'z', 'H', 'P', 'D']) witness(parent, fn(parent, name), `complete row helper ${name}`);
  witness(parent, parentMain, 'complete exported MayhemScreener parent');
  for (const f of selected.values()) {
    if (f.id === 609252) {
      const namespace = exactlyOne(findNodes(f.node, (n) => n.type === 'VariableDeclarator' && n.init?.arguments?.[0]?.value === 493025), '493025 import');
      imports.push(f.witness(namespace, 'existing 493025 normalization input'));
      assert.equal(findNodes(f.node, (n) => n.type === 'CallExpression' && n.callee.type === 'SequenceExpression' &&
        member(n.callee.expressions.at(-1), namespace.id.name, 'f')).length, 1);
    }
    if (f.id === 849812) {
      for (const id of [680930, 26077]) assert.equal(findNodes(f.node, (n) => n.type === 'VariableDeclarator' && n.init?.arguments?.[0]?.value === id).length, 1);
      witness(f, exported(f, 'b'), 'complete activity-hook result boundary, not reconstructed service');
    }
    if (f.id === 680930) witness(f, exported(f, 'd'), 'activity-query result merge input contract');
    if (f.id === 653805) witness(f, exported(f, 'J'), 'display-only usdMarketCap selector');
    if (f.id === 915631) witness(f, exported(f, 'f'), 'visible-mint subscription external boundary');
  }
  return { schemaVersion: 1, baseCommit: '094a06f18df738d41e77070c1a009e135671ac1a', anchors: corpus.anchors,
    editableSha256: sha256(editable), factories, imports, providerCalls, fragments, comparisons,
    inputs: { data: '457065.C result (997887.l identity), served coin array; nullish becomes []',
      hydratedCoins: '609252.f coins, already normalized through existing 493025.f; used only for valid mode fallbacks',
      marketActivity: '849812.b delivered marketActivity by-mint/window record, after 26077.f and 680930.d',
      byMint: '457065.w store snapshot, empty initial byMint; update callback set capability supplied explicitly',
      coinState: '653805.x live store snapshot; actual J selects coins[mint]?.usdMarketCap',
      pageIndex: 'current-render nonnegative integer state; control callbacks separately reset it on filter/sort changes',
      isLoading: 'base-query loading flag', isError: 'base-query error flag', paused: 'current hover-pause state',
      sort: 'current sort state, initially lastTraded; unrecognized values retain served order' },
    limits: { originalExecution: false, providerAcquisition: false, mountedUI: false,
      nativeCompatibility: false, progressCredit: false, snapshotFacadeNames: 'authored',
      fullReactOrUniversalEquivalence: false } };
}

export async function verifyMayhemView(root = APP_ROOT) {
  const proof = await buildMayhemViewProof(root);
  assert.deepEqual(JSON.parse(await readFile(path.join(root, PROOF), 'utf8')), proof, 'Mayhem view proof differs');
  return proof;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const mode = process.argv[2];
  if (mode === '--write') await writeFile(path.join(APP_ROOT, PROOF), `${JSON.stringify(await buildMayhemViewProof(), null, 2)}\n`);
  else { assert.equal(mode, '--check'); await verifyMayhemView(); }
  console.log('Mayhem pure view-data source proof PASS');
}
