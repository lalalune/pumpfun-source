import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse, parseExpression } from '@babel/parser';
import { openCorpus, findNodes, exactlyOne, member, propertyName, objectProperty, sha256 } from '../../scripts/original-contracts/source.mjs';

export const APP_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
export const DIRECTORY = 'reconstruction/mayhem-sparkline';
export const PROOF = `${DIRECTORY}/PROVENANCE.json`;
const page = 'evidence/web/objects/7a7f27bff952614d.js';
const counts = new Map([[457065, 1], [375676, 3], [997627, 5], [349942, 9],
  [505835, 1], [646908, 1], [38279, 1], [668487, 1]]);
const ignored = new Set(['start', 'end', 'loc', 'range', 'extra', 'comments', 'errors', 'leadingComments', 'trailingComments', 'innerComments']);
function shape(value, roles = {}, parent, key) {
  if (!value || typeof value !== 'object') return value;
  if (Array.isArray(value)) return value.map((n) => shape(n, roles));
  const property = key === 'property' && ['MemberExpression', 'OptionalMemberExpression'].includes(parent?.type) && !parent.computed ||
    key === 'key' && parent?.type === 'ObjectProperty' && !parent.computed;
  if (value.type === 'Identifier' && !property && roles[value.name]) return shape(parseExpression(roles[value.name]));
  if (value.type === 'UnaryExpression' && value.operator === '!' && value.argument.type === 'NumericLiteral' && [0, 1].includes(value.argument.value))
    return { type: 'BooleanLiteral', value: !value.argument.value };
  return Object.fromEntries(Object.entries(value).filter(([key]) => !ignored.has(key)).map(([key, val]) => [key, key === 'shorthand' ? false : shape(val, roles, value, key)]));
}
function resolve(factory, node) {
  if (node.type !== 'Identifier') return node;
  const fn = factory.node.body.body.filter((n) => n.type === 'FunctionDeclaration' && n.id.name === node.name);
  if (fn.length) return exactlyOne(fn, 'local function');
  return exactlyOne(factory.node.body.body.flatMap((n) => n.type === 'VariableDeclaration' ? n.declarations : [])
    .filter((n) => n.id.name === node.name), `local ${node.name}`).init;
}
function exp(factory, name, id = factory.id) {
  const call = exactlyOne(findNodes(factory.node, (n) => n.type === 'CallExpression' && member(n.callee, factory.runtime, 's') &&
    (n.arguments[1]?.value === id || n.arguments.length === 1 && factory.ids.length === 1) &&
    n.arguments[0]?.elements?.some((e) => e?.value === name)), `actual ${id}.${name} export`);
  const a = call.arguments[0].elements, i = a.findIndex((n) => n?.value === name);
  assert.equal(a[i + 1].value, 0);
  return resolve(factory, a[i + 2]);
}
function imported(factory, id) {
  return exactlyOne(factory.node.body.body.flatMap((n) => n.type === 'VariableDeclaration' ? n.declarations : [])
    .filter((n) => n.init?.type === 'CallExpression' && n.init.arguments[0]?.value === id &&
      ['i', 'r'].some((method) => member(n.init.callee, factory.runtime, method))), `import ${id}`);
}
const fn = (factory, name) => exactlyOne(factory.node.body.body.filter((n) => n.type === 'FunctionDeclaration' && n.id.name === name), `function ${name}`);

export async function buildSparklineProof(root = APP_ROOT) {
  const corpus = await openCorpus(root), factories = [], selected = new Map();
  const bytes = await readFile(path.join(root, DIRECTORY, 'sparkline.mjs'));
  const ast = parse(bytes.toString('utf8'), { sourceType: 'module' });
  const local = (name) => exactlyOne(ast.program.body.filter((n) => n.type === 'ExportNamedDeclaration')
    .flatMap((n) => n.declaration.type === 'VariableDeclaration' ? n.declaration.declarations : [n.declaration])
    .filter((n) => n.id.name === name), `editable ${name}`);
  for (const [id, count] of counts) {
    const variants = corpus.index.modules.filter((m) => m.ids.includes(id));
    assert.equal(variants.length, count, `physical variant census ${id}`);
    for (const v of variants) for (const origin of v.origins) {
      const f = await corpus.factory(id, { source: origin.source });
      factories.push(f.provenance); selected.set(`${id}:${origin.source}`, f);
    }
  }
  const pick = (id, source) => source ? selected.get(`${id}:${source}`)
    : exactlyOne([...selected.values()].filter((f) => f.id === id), `unique factory ${id}`);
  const fragments = [], imports = [], comparisons = [], variantContracts = [];
  const witness = (f, node, label) => {
    const result = f.witness(Array.isArray(node) ? { start: node[0].start, end: node.at(-1).end } : node, label);
    fragments.push(result); return result;
  };
  const compare = (f, original, actual, label, roles = {}) => {
    assert.deepEqual(shape(original, roles), shape(actual), `source differs: ${label}`);
    comparisons.push({ ...witness(f, original, label), roles, structuralSha256: sha256(JSON.stringify(shape(actual))) });
  };
  const parent = pick(457065), h = fn(parent, 'h');
  imports.push(parent.witness(imported(parent, 375676), 'actual row chart provider 375676.f'));
  imports.push(parent.witness(imported(parent, 668487), 'actual adjusted clock 668487.t'));
  for (const id of [732486, 352386, 338319]) imports.push(parent.witness(imported(parent, id), `actual JSX/ID/class operation ${id}`));
  witness(parent, h, 'complete Mayhem sparkline h consumer');
  const row = fn(parent, 'G');
  const rowCall = exactlyOne(findNodes(row, (n) => n.type === 'CallExpression' &&
    n.arguments[0]?.name === 'h' && n.arguments[1]?.type === 'ObjectExpression'), 'actual G → h JSX props');
  assert.deepEqual(rowCall.arguments[1].properties.map((n) => propertyName(n.key)),
    ['mint', 'createdTimestamp', 'chainId', 'colorClassName', 'className']);
  witness(parent, rowCall, 'actual row → h chart props');
  compare(parent, fn(parent, 'f').params, local('sparklineRefetchInterval').params, 'complete refetch callback parameters');
  compare(parent, fn(parent, 'f').body, local('sparklineRefetchInterval').body, 'complete refetch callback body');
  const group = pick(997627, page);
  assert.deepEqual([...group.ids].sort(), [636882, 693908, 997627].sort());
  for (const [symbol, name] of [['a', 'isYoungCoin'], ['S', 'youngCandleWindow']]) {
    const original = exp(group, symbol, 693908);
    compare(group, original.params, local(name).params, `${name} complete parameters`);
    compare(group, original.body, local(name).body, `${name} complete body`);
  }
  const read = exp(group, 'B', 997627), editableRead = local('createSparklineReader');
  for (const method of ['map', 'filter']) {
    const sourceCall = exactlyOne(findNodes(read, (n) => n.type === 'CallExpression' && propertyName(n.callee.property) === method), `source point ${method}`);
    const localCall = exactlyOne(findNodes(editableRead, (n) => n.type === 'CallExpression' && propertyName(n.callee.property) === method &&
      n.arguments[0]?.type === 'ArrowFunctionExpression' &&
      (method === 'filter' || n.arguments[0].body.type === 'ObjectExpression' && n.arguments[0].body.properties.some((p) => propertyName(p.key) === 'price'))), `editable point ${method}`);
    compare(group, sourceCall.arguments[0], localCall.arguments[0], `complete candle-point ${method} callback`);
  }
  const candleSource = pick(349942, page);
  const stringMap = exactlyOne(findNodes(exp(candleSource, 'f'), (n) => n.type === 'CallExpression' && propertyName(n.callee.property) === 'map'), 'candle string map');
  const localStringMap = exactlyOne(findNodes(editableRead, (n) => n.type === 'CallExpression' && propertyName(n.callee.property) === 'map' &&
    n.arguments[0]?.body?.type === 'ObjectExpression' && n.arguments[0].body.properties.some((p) => propertyName(p.key) === 'close')), 'editable candle string map');
  compare(candleSource, stringMap.arguments[0], localStringMap.arguments[0], 'complete OHLCV string delivery callback');
  const decl = (node, name) => exactlyOne(findNodes(node, (n) => n.type === 'VariableDeclarator' && n.id.name === name && n.init), `variable ${name}`).init;
  const render = local('renderMayhemSparkline');
  compare(parent, decl(h, 'n'), decl(render, 'min'), 'SVG minimum price', { t: 'prices' });
  compare(parent, decl(h, 'a'), decl(render, 'range'), 'SVG constant-price range fallback', { t: 'prices', n: 'min' });
  const point = exactlyOne(findNodes(h, (n) => n.type === 'ArrowFunctionExpression' && n.body.type === 'BlockStatement' &&
    n.body.body.at(-1)?.argument?.type === 'TemplateLiteral'), 'source SVG coordinate callback');
  const localPoint = exactlyOne(findNodes(render, (n) => n.type === 'ArrowFunctionExpression' && n.body.type === 'TemplateLiteral'), 'editable coordinate callback');
  compare(parent, decl(point, 'i'), localPoint.body.expressions[0], 'SVG index-spaced x coordinate', { s: 'i', t: 'prices' });
  compare(parent, point.body.body.at(-1).argument.expressions[1], localPoint.body.expressions[1], 'SVG 80-percent y coordinate', { e: 'price', n: 'min', a: 'range' });
  compare(parent, decl(h, 'A'), decl(render, 'fill'), 'SVG fill closure', { C: 'line' });
  const sourceJsx = findNodes(h, (n) => n.type === 'CallExpression' && n.callee.type === 'SequenceExpression' &&
    ['jsx', 'jsxs'].some((p) => member(n.callee.expressions.at(-1), 't', p)) && n.arguments[0]?.type === 'StringLiteral');
  const localJsx = findNodes(render, (n) => n.type === 'CallExpression' && ['jsx', 'jsxs'].includes(n.callee.name));
  const roles = { M: 'id', C: 'line', A: 'fill', R: '`url(#${id})`',
    m: "mergeClassNames('h-12 w-full', colorClassName, className)", e: "mergeClassNames('h-12 w-full', className)" };
  const classCalls = findNodes(h, (n) => n.type === 'CallExpression' && n.callee.type === 'SequenceExpression' &&
    member(n.callee.expressions.at(-1), 'u', 'c'));
  for (const length of [2, 3]) {
    const original = exactlyOne(classCalls.filter((n) => n.arguments.length === length), `actual ${length}-argument class merge`);
    const actual = exactlyOne(findNodes(render, (n) => n.type === 'CallExpression' && n.callee.name === 'mergeClassNames' && n.arguments.length === length), 'editable class merge');
    compare(parent, original.arguments, actual.arguments, `complete ${length}-argument class merge inputs`, { N: 'colorClassName', k: 'className' });
  }
  const sourceSvg = exactlyOne(sourceJsx.filter((n) => n.arguments[0].value === 'svg'), 'complete source SVG');
  const localSvg = exactlyOne(localJsx.filter((n) => n.arguments[0].value === 'svg'), 'complete editable SVG');
  const sourceChildren = objectProperty(sourceSvg.arguments[1], 'children').elements;
  const sourceTypes = sourceChildren.map((child) => exactlyOne(findNodes(h, (n) => n.type === 'AssignmentExpression' &&
    n.left.name === child.name && sourceJsx.includes(n.right)), 'source child binding').right.arguments[0].value);
  assert.deepEqual(sourceTypes, ['defs', 'path', 'path']);
  assert.deepEqual(objectProperty(localSvg.arguments[1], 'children').elements.map((n) => n.arguments[0].value), sourceTypes);
  witness(parent, objectProperty(sourceSvg.arguments[1], 'children'), 'complete SVG child order and bindings');
  const originalJoin = exactlyOne(findNodes(h, (n) => n.type === 'CallExpression' && propertyName(n.callee.property) === 'join'), 'source path delimiter');
  const actualJoin = exactlyOne(findNodes(render, (n) => n.type === 'CallExpression' && propertyName(n.callee.property) === 'join'), 'editable path delimiter');
  compare(parent, originalJoin.arguments, actualJoin.arguments, 'complete SVG path separator');
  for (const type of ['div', 'stop', 'linearGradient', 'defs', 'path', 'svg']) {
    const sourceNodes = sourceJsx.filter((n) => n.arguments[0].value === type);
    const localNodes = localJsx.filter((n) => n.arguments[0].value === type);
    assert.equal(localNodes.length, sourceNodes.length, `complete ${type} element count`);
    for (let i = 0; i < sourceNodes.length; i++) {
      const a = sourceNodes[i].arguments[1], b = localNodes[i].arguments[1];
      const props = a.properties.filter((p) => propertyName(p.key) !== 'children');
      assert.deepEqual(props.map((p) => propertyName(p.key)), b.properties.filter((p) => propertyName(p.key) !== 'children').map((p) => propertyName(p.key)));
      for (const prop of props) compare(parent, prop.value, objectProperty(b, propertyName(prop.key)),
        `SVG ${type}[${i}].${propertyName(prop.key)}`, roles);
    }
  }
  const defaults = exp(pick(38279), 'v');
  const candle = objectProperty(defaults, 'COIN_CANDLES'), line = objectProperty(defaults, 'COIN_LINE_CHART');
  const expectedDefaults = { candleInterval: objectProperty(candle, 'INTERVAL').value,
    candleLimit: objectProperty(candle, 'LIMIT').value, timeframe: objectProperty(line, 'TIMEFRAME').value,
    width: objectProperty(line, 'WIDTH').value };
  assert.deepEqual(Object.fromEntries(local('CHART_DEFAULTS').init.properties.map((p) => [propertyName(p.key), p.value.value])), expectedDefaults);
  witness(pick(38279), candle, 'actual candle defaults'); witness(pick(38279), line, 'actual line defaults');
  for (const name of ['COIN_CANDLES', 'COIN_LINE_CHART']) witness(pick(38279), objectProperty(exp(pick(38279), 'Q'), name), `actual ${name} cache key`);
  const provider = pick(505835);
  assert.deepEqual([...provider.ids].sort(), [505835, 442951, 628731].sort());
  const parameters = exp(provider, 'b', 628731), ownParameters = local('lineParameters');
  witness(provider, parameters, 'complete chart-parameter mapper');
  const privateValue = (name) => exactlyOne(ast.program.body.filter((n) => n.type === 'VariableDeclaration')
    .flatMap((n) => n.declarations).filter((n) => n.id.name === name), `editable table ${name}`).init;
  compare(provider, resolve(provider, { type: 'Identifier', name: 'a' }),
    objectProperty(ownParameters.body.body.at(-1).argument, 'count').arguments[0], 'actual maximum history count constant');
  compare(provider, resolve(provider, { type: 'Identifier', name: 'o' }), privateValue('durations'), 'complete timeframe-duration table');
  compare(provider, resolve(provider, { type: 'Identifier', name: 'i' }), privateValue('resolutions'), 'complete ordered resolution table');
  const regexp = exactlyOne(findNodes(parameters, (n) => n.type === 'CallExpression' && n.callee.object?.type === 'RegExpLiteral'), 'actual timeframe parser');
  compare(provider, regexp, decl(ownParameters, 'match'), 'complete timeframe regex and trim call', { t: 'timeframe' });
  const window = decl(parameters, 'u');
  assert.equal(window.type, 'SequenceExpression');
  compare(provider, window.expressions[0].right.consequent, decl(ownParameters, 'unit').consequent,
    'timeframe unit lookup', { o: 'durations', l: 'match' });
  compare(provider, window.expressions[1], decl(ownParameters, 'window'), 'parsed timeframe duration', { l: 'match', m: 'unit' });
  compare(provider, decl(parameters, 'c'), decl(ownParameters, 'span'), 'created-time bounded line span', { n: 'nowMs', u: 'window', e: 'createdTs' });
  compare(provider, decl(parameters, 'd'), decl(ownParameters, 'res'), 'first-fit resolution including fallback',
    { s: 'Object.keys(resolutions)', c: 'span', i: 'resolutions', e: 'key', a: '300' });
  const parameterResult = ownParameters.body.body.at(-1).argument;
  compare(provider, decl(parameters, 'h'), objectProperty(parameterResult, 'count'), 'line history count bounds',
    { a: '300', c: 'span', i: 'resolutions', d: 'res' });
  compare(provider, objectProperty(parameters.body.body.at(-1).argument, 'maxPoints'), objectProperty(parameterResult, 'maxPoints'),
    'line history maximum point bounds', { r: 'width' });
  const ownCandle = exactlyOne(findNodes(editableRead, (n) => n.type === 'FunctionDeclaration' && n.id.name === 'readCandles'), 'editable candle operation');
  const originalCandle = exp(candleSource, 'f');
  const sourceCandleNamespace = imported(candleSource, 505835).id.name;
  const historyCall = exactlyOne(findNodes(originalCandle, (n) => n.type === 'CallExpression' && n.callee.type === 'SequenceExpression' &&
    member(n.callee.expressions.at(-1), sourceCandleNamespace, 'Z')), 'actual normalized candle history invocation');
  const ownHistoryCall = exactlyOne(findNodes(ownCandle, (n) => n.type === 'CallExpression' && n.callee.name === 'readCandleHistory'), 'editable candle history invocation');
  const candlePattern = exactlyOne(findNodes(originalCandle, (n) => n.type === 'VariableDeclarator' && n.id.type === 'ObjectPattern'), 'actual candle input bindings').id;
  const candleRoles = Object.fromEntries(candlePattern.properties.map((p) =>
    [p.value.type === 'AssignmentPattern' ? p.value.left.name : p.value.name, propertyName(p.key)]));
  candleRoles[objectProperty(historyCall.arguments[0], 'chainId').name] = 'chain';
  compare(candleSource, historyCall.arguments[0], ownHistoryCall.arguments[0], 'complete normalized candle history request object', candleRoles);
  const lineNamespace = imported(group, 505835).id.name;
  const originalLineCall = exactlyOne(findNodes(group.node, (n) => n.type === 'CallExpression' && n.callee.type === 'SequenceExpression' &&
    member(n.callee.expressions.at(-1), lineNamespace, 'x')), 'actual normalized line history invocation');
  const ownLineCall = exactlyOne(findNodes(editableRead, (n) => n.type === 'CallExpression' && n.callee.name === 'readLineHistory'), 'editable normalized line invocation');
  compare(group, originalLineCall.arguments[0], ownLineCall.arguments[0], 'complete normalized line history request object',
    { m: 'chain', t: 'coinAddress', u: 'params', s: 'fetchOptions' });
  for (const symbol of ['U', 'Z', 'x']) witness(provider, exp(provider, symbol), `actual external normalized history provider ${symbol}`);
  witness(pick(646908), exp(pick(646908), 'L'), 'actual TON eligibility predicate');
  // Both clocks are source dependencies, not reimplemented services.
  for (const symbol of ['t', 's']) witness(pick(668487), exp(pick(668487), symbol), `existing adjusted clock ${symbol} boundary`);
  for (const f of selected.values()) {
    if (f.id === 375676) {
      for (const id of [636882, 693908, 997627, 38279]) imports.push(f.witness(imported(f, id), `planner actual dependency ${id}`));
      const hook = exp(f, 'f');
      const options = exactlyOne(findNodes(hook, (n) => n.type === 'ObjectExpression' &&
        n.properties.some((p) => propertyName(p.key) === 'queryFn') && n.properties.some((p) => propertyName(p.key) === 'enabled')), 'query options');
      const order = options.properties.map((p) => p.type === 'SpreadElement' ? '...options' : propertyName(p.key));
      assert.deepEqual(order, ['queryFn', 'queryKey', '...options', 'enabled']);
      const planner = local('planSparklineQuery'), editableOptions = planner.body.body.at(-1).argument;
      assert.deepEqual(editableOptions.properties.map((p) => p.type === 'SpreadElement' ? '...options' : propertyName(p.key)), order, 'editable query option spread order');
      const guard = exactlyOne(findNodes(hook, (n) => n.type === 'VariableDeclarator' &&
        n.id.name === objectProperty(options, 'enabled').name && n.init?.type === 'LogicalExpression' && n.init.operator === '&&'), 'actual enabled guard').init;
      assert.equal(guard.operator, '&&'); assert.equal(guard.right.operator, '??');
      compare(f, guard, objectProperty(editableOptions, 'enabled'), 'complete final enabled guard',
        { [guard.left.name]: 'eligible', [guard.right.left.name]: 'enabled' });
      const readerNamespace = imported(f, 997627).id.name;
      const readCall = exactlyOne(findNodes(hook, (n) => n.type === 'CallExpression' && n.callee.type === 'SequenceExpression' &&
        member(n.callee.expressions.at(-1), readerNamespace, 'B')), 'actual sparkline read invocation');
      const readArrow = exactlyOne(findNodes(hook, (n) => n.type === 'ArrowFunctionExpression' && n.body === readCall), 'actual query function');
      const inputRoles = {};
      const desiredRoles = { coinAddress: 'coinAddress', coinCreatedTimestamp: 'coinCreatedTimestamp', chainId: 'chainId',
        timeframe: 'resolvedTimeframe', width: 'resolvedWidth', youngCoinSource: 'youngCoinSource' };
      assert.deepEqual(readCall.arguments[0].properties.map((p) => propertyName(p.key)), Object.keys(desiredRoles));
      for (const prop of readCall.arguments[0].properties) {
        assert.equal(prop.value.type, 'Identifier'); inputRoles[prop.value.name] = desiredRoles[propertyName(prop.key)];
      }
      const adaptedRead = structuredClone(readArrow);
      adaptedRead.body.callee = { type: 'Identifier', name: 'readSparkline' };
      compare(f, adaptedRead, decl(planner, 'queryFn'), 'complete query read callback with authenticated B port', inputRoles);
      // The original key methods are pure array constructors. All four fields
      // are explicitly supplied here; no default field is synthesized/evaluated.
      const key = exactlyOne(findNodes(hook, (n) => n.type === 'AssignmentExpression' && n.right.type === 'ConditionalExpression' &&
        n.right.consequent.type === 'ArrayExpression' && n.right.alternate.type === 'ArrayExpression'), 'actual key branch').right;
      const expanded = structuredClone(key);
      const keyRoles = { ...inputRoles, [key.test.name]: 'young' };
      for (const branch of ['consequent', 'alternate']) {
        const spread = expanded[branch].elements[0];
        assert.equal(spread.type, 'SpreadElement');
        const call = spread.argument, name = propertyName(call.callee.property);
        assert.ok(['COIN_CANDLES', 'COIN_LINE_CHART'].includes(name));
        assert.ok(member(call.callee.object, imported(f, 38279).id.name, 'Q'));
        const method = objectProperty(exp(pick(38279), 'Q'), name);
        const fields = method.params[0].properties, args = call.arguments[0];
        assert.deepEqual(fields.map((p) => propertyName(p.key)), args.properties.map((p) => propertyName(p.key)));
        const bindings = new Map(fields.map((p) => [p.value.type === 'AssignmentPattern' ? p.value.left.name : p.value.name,
          objectProperty(args, propertyName(p.key))]));
        const values = method.body.elements.map((n) => n.type === 'Identifier' ? structuredClone(bindings.get(n.name)) : structuredClone(n));
        assert.ok(values.every(Boolean));
        expanded[branch].elements = [...values, ...expanded[branch].elements.slice(1)];
        for (const prop of args.properties) if (['interval', 'limit'].includes(propertyName(prop.key))) {
          assert.equal(prop.value.type, 'MemberExpression'); keyRoles[prop.value.object.name] = 'candles';
        }
        witness(f, call, `actual ${name} invocation and explicit field substitution`);
      }
      compare(f, expanded, decl(planner, 'queryKey'), 'complete cache-key branch after actual array-constructor substitution', keyRoles);
      witness(f, hook, 'complete planner variant including memo-cache boundaries');
      variantContracts.push({ id: f.id, source: f.provenance.source, sha256: f.provenance.sha256, optionsOrder: order });
    }
    if (f.id === 997627) {
      assert.deepEqual([...f.ids].sort(), [636882, 693908, 997627].sort());
      for (const id of [349942, 505835, 628731, 646908, 38279]) imports.push(f.witness(imported(f, id), `group actual dependency ${id}`));
      for (const [id, symbol] of [[636882, 'f'], [693908, 'a'], [693908, 'S'], [693908, 'Y'], [997627, 'B']])
        witness(f, exp(f, symbol, id), `complete grouped ${id}.${symbol} callback`);
    }
    if (f.id === 349942) {
      imports.push(f.witness(imported(f, 505835), 'candle wrapper actual history provider'));
      witness(f, exp(f, 'f'), 'complete candle-string delivery wrapper');
    }
  }
  return { schemaVersion: 1, baseCommit: '094a06f18df738d41e77070c1a009e135671ac1a', anchors: corpus.anchors,
    editableSha256: sha256(bytes), factories, fragments, imports, comparisons, variantContracts,
    providerContracts: { resolveChain: '505835.U({mint,chainId}) → chain string or null',
      readCandleHistory: '505835.Z(args) → normalized {candles}; 349942 stringifies OHLCV before 997627.B converts close to Number',
      readLineHistory: '505835.x(args) → normalized {points}; delivered array retained without another parser',
      getQueryResult: '375676.f actual useQuery(options) return, data consumed by 457065.h',
      now: 'Date.now default used independently by age/default-window/parameter functions',
      adjustedNow: '668487.t used only by 457065.h timeframe selection',
      rendering: '732486.jsx/jsxs, 338319.c class merge and owning352386.useId result are explicit ports' },
    limits: { capturedExecution: false, acquisition: false, services: false, originalReactMemoLifecycle: false,
      mountedUI: false, nativeCompatibility: false, financialDataQualified: false, progressCredit: false,
      fullStructuralEquivalence: false, descriptiveFacade: 'authored recomputation boundary' } };
}
export async function verifySparkline(root = APP_ROOT) {
  const proof = await buildSparklineProof(root);
  assert.deepEqual(JSON.parse(await readFile(path.join(root, PROOF), 'utf8')), proof, 'sparkline proof differs');
  return proof;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (process.argv[2] === '--write') await writeFile(path.join(APP_ROOT, PROOF), `${JSON.stringify(await buildSparklineProof(), null, 2)}\n`);
  else { assert.equal(process.argv[2], '--check'); await verifySparkline(); }
  console.log('Mayhem sparkline source proof PASS');
}
