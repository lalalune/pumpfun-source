import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse, parseExpression } from '@babel/parser';
import { openCorpus, findNodes, exactlyOne, member, propertyName, objectProperty, sha256 } from '../../scripts/original-contracts/source.mjs';

export const APP_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
export const DIRECTORY = 'reconstruction/candle-history';
export const PROOF = `${DIRECTORY}/PROVENANCE.json`;
const counts = new Map([[505835, 1], [771073, 1], [921152, 1], [503630, 1], [349942, 9], [997627, 5]]);
const ignored = new Set(['start', 'end', 'loc', 'range', 'extra', 'comments', 'errors', 'leadingComments', 'trailingComments', 'innerComments']);
function shape(node, roles = {}, parent, key) {
  if (!node || typeof node !== 'object') return node;
  if (Array.isArray(node)) return node.map((n) => shape(n, roles));
  const property = key === 'property' && ['MemberExpression', 'OptionalMemberExpression'].includes(parent?.type) && !parent.computed ||
    key === 'key' && ['ObjectProperty', 'ClassProperty'].includes(parent?.type) && !parent.computed;
  if (node.type === 'Identifier' && !property && roles[node.name]) return shape(parseExpression(roles[node.name]));
  if (node.type === 'UnaryExpression' && node.operator === '!' && node.argument.type === 'NumericLiteral' && [0, 1].includes(node.argument.value))
    return { type: 'BooleanLiteral', value: !node.argument.value };
  return Object.fromEntries(Object.entries(node).filter(([k]) => !ignored.has(k)).map(([k, value]) =>
    [k, k === 'shorthand' ? false : shape(value, roles, node, k)]));
}
function resolve(f, node) {
  if (node.type !== 'Identifier') return node;
  const value = exactlyOne(f.node.body.body.flatMap((n) => n.type === 'VariableDeclaration' ? n.declarations :
    ['FunctionDeclaration', 'ClassDeclaration'].includes(n.type) ? [n] : []).filter((n) => n.id.name === node.name), `local ${node.name}`);
  return value.type === 'VariableDeclarator' ? value.init : value;
}
function exp(f, id, name) {
  const call = exactlyOne(findNodes(f.node, (n) => n.type === 'CallExpression' && member(n.callee, f.runtime, 's') &&
    (n.arguments[1]?.value === id || n.arguments.length === 1 && f.ids.length === 1) &&
    n.arguments[0]?.elements?.some((e) => e?.value === name)), `${id}.${name} registration`);
  const a = call.arguments[0].elements, i = a.findIndex((n) => n?.value === name);
  assert.equal(a[i + 1].value, 0); return resolve(f, a[i + 2]);
}
const decl = (node, name) => exactlyOne(findNodes(node, (n) => n.type === 'VariableDeclarator' && n.id.name === name && n.init), `binding ${name}`).init;
const returned = (fn) => fn.body.type === 'BlockStatement' ? fn.body.body.at(-1).argument : fn.body;
const imported = (f, id) => exactlyOne(f.node.body.body.filter((n) => n.type === 'VariableDeclaration').flatMap((n) => n.declarations)
  .filter((n) => n.init?.type === 'CallExpression' && n.init.arguments[0]?.value === id &&
    ['i', 'r'].some((method) => member(n.init.callee, f.runtime, method))), `actual import ${id}`);
const operations = (block) => block.body.flatMap((n) => {
  assert.equal(n.type, 'ExpressionStatement'); return n.expression.type === 'SequenceExpression' ? n.expression.expressions : [n.expression];
});

export async function buildHistoryProof(root = APP_ROOT) {
  const corpus = await openCorpus(root), factories = [], selected = new Map();
  const bytes = await readFile(path.join(root, DIRECTORY, 'client.mjs'));
  const ast = parse(bytes.toString('utf8'), { sourceType: 'module' });
  const local = (name) => exactlyOne(ast.program.body.flatMap((n) => n.type === 'ExportNamedDeclaration' ?
    n.declaration.type === 'VariableDeclaration' ? n.declaration.declarations : [n.declaration] :
    n.type === 'VariableDeclaration' ? n.declarations : n.type === 'FunctionDeclaration' ? [n] : []).filter((n) => n.id.name === name), `editable ${name}`);
  for (const [id, count] of counts) {
    const variants = corpus.index.modules.filter((m) => m.ids.includes(id));
    assert.equal(variants.length, count, `physical variant census ${id}`);
    for (const v of variants) for (const origin of v.origins) {
      const f = await corpus.factory(id, { source: origin.source }); factories.push(f.provenance); selected.set(`${id}:${origin.source}`, f);
    }
  }
  const pick = (id) => exactlyOne([...selected.values()].filter((f) => f.id === id), `unique ${id}`);
  const fragments = [], comparisons = [], incoming = [], imports = [];
  const witness = (f, node, label) => {
    const range = Array.isArray(node) ? { start: node[0].start, end: node.at(-1).end } : node;
    const result = f.witness(range, label); fragments.push(result); return result;
  };
  const compare = (f, source, editable, label, roles = {}) => {
    assert.deepEqual(shape(source, roles), shape(editable), `history source differs: ${label}`);
    comparisons.push({ ...witness(f, source, label), roles, structuralSha256: sha256(JSON.stringify(shape(editable))) });
  };
  const f = pick(505835), decoder = pick(771073), week = pick(921152), origin = pick(503630);
  for (const id of [771073, 921152, 503630]) imports.push(f.witness(imported(f, id), `actual history dependency ${id}`));
  for (const [id, name] of [[505835, 'Z'], [505835, 'x'], [442951, 's'], [628731, 's']])
    witness(f, exp(f, id, name), `complete actual grouped ${id}.${name} callback`);
  const klass = exp(f, 442951, 's'), ownKlass = local('CandleHistoryFetchError');
  const fields = (node) => node.body.body.filter((n) => n.type === 'ClassProperty');
  compare(f, fields(klass), fields(ownKlass), 'complete error class field declarations');
  const ctor = exactlyOne(klass.body.body.filter((n) => n.kind === 'constructor'), 'source constructor');
  const ownCtor = exactlyOne(ownKlass.body.body.filter((n) => n.kind === 'constructor'), 'editable constructor');
  compare(f, ctor.params, ownCtor.params, 'error constructor parameters/default', { e: 'message', t: 'status', r: 'fallback' });
  const sourceOps = operations(ctor.body), ownOps = operations(ownCtor.body);
  assert.equal(sourceOps.length, ownOps.length);
  for (let i = 0; i < sourceOps.length; i++) compare(f, sourceOps[i], ownOps[i], `ordered error constructor operation ${i}`, { e: 'message', t: 'status', r: 'fallback' });
  compare(f, resolve(f, { type: 'Identifier', name: 'a' }), local('HISTORY_COUNT_LIMIT').init, 'actual count limit');
  compare(f, exp(f, 442951, 'o'), local('CAPTURED_RETRY_DELAYS').init, 'exported retry delays, not implicit defaults');
  compare(f, returned(resolve(f, { type: 'Identifier', name: 'y' })), local('candlePath').init.body, 'complete path builder', { e: 'base', t: 'chain', r: 'address' });
  compare(f, returned(resolve(f, { type: 'Identifier', name: 'g' })), local('beforeCursor').init.body, 'complete exclusive cursor', { e: 'value' });
  const intervalTable = structuredClone(resolve(f, { type: 'Identifier', name: 'b' }));
  const weekReference = exactlyOne(findNodes(intervalTable, (n) => member(n, 't', 'h')), 'actual used week-bucket reference');
  Object.assign(weekReference, { type: 'Identifier', name: 'utcWeekStart' });
  delete weekReference.object; delete weekReference.property; delete weekReference.computed;
  compare(f, intervalTable, local('INTERVALS').init, 'complete interval/resolution/bucket table', { p: 'direct', h: 'bucket' });
  compare(f, resolve(f, { type: 'Identifier', name: 'p' }).body, local('direct').init.body, 'complete direct-interval constructor', { e: 'res' });
  compare(f, resolve(f, { type: 'Identifier', name: 'h' }), local('bucket').init, 'complete fixed-duration bucket constructor', { e: 'size', t: 'time' });
  compare(f, exp(f, 505835, 'O').body, local('buildCandleUrl').body.body[0].declarations[0].init,
    'actual interval lookup', { b: 'INTERVALS', e: 'interval' });
  for (const [name, editable] of [['v', 'isCandlePage'], ['w', 'isLinePage']])
    compare(f, resolve(f, { type: 'Identifier', name }).body, local(editable).init.body, `complete ${editable} predicate`, { e: 'value' });

  const candleUrl = exp(f, 505835, 'h'), ownCandleUrl = local('buildCandleUrl');
  const candleInner = returned(candleUrl).callee;
  assert.equal(candleInner.type, 'ArrowFunctionExpression');
  compare(f, decl(candleInner, 'm'), decl(ownCandleUrl, 'parts'), 'complete candle query field construction after actual count-times-bars substitution',
    { i: 'res', s: 'count * bars', a: 'HISTORY_COUNT_LIMIT', n: 'measure' });
  const ownCandleCursor = exactlyOne(ownCandleUrl.body.body.filter((n) => n.type === 'IfStatement'), 'editable candle cursor append');
  const candleReturn = returned(candleInner); assert.equal(candleReturn.type, 'SequenceExpression'); assert.equal(candleReturn.expressions.length, 2);
  compare(f, decl(candleInner, 'u'), decl(ownCandleUrl, 'to'), 'complete candle cursor calculation', { g: 'beforeCursor', o: 'beforeTs' });
  compare(f, candleReturn.expressions[0].left, ownCandleCursor.test, 'complete candle cursor append condition', { u: 'to' });
  compare(f, candleReturn.expressions[0].right, ownCandleCursor.consequent.expression, 'complete candle cursor append', { u: 'to', m: 'parts' });
  compare(f, candleReturn.expressions[1], returned(ownCandleUrl), 'complete candle URL return',
    { y: 'candlePath', e: 'baseUrl', t: 'chainId', r: 'address', m: 'parts' });
  const lineRead = exp(f, 505835, 'x'), ownLineUrl = local('buildLineUrl');
  const lineInner = returned(lineRead).arguments[0].argument.arguments[0].callee;
  assert.equal(lineInner.type, 'ArrowFunctionExpression');
  compare(f, decl(lineInner, 'u'), decl(ownLineUrl, 'parts'), 'complete line query field construction',
    { i: 'res', s: 'count', n: 'maxPoints', a: 'HISTORY_COUNT_LIMIT', o: 'measure' });
  const ownLineCursor = exactlyOne(ownLineUrl.body.body.filter((n) => n.type === 'IfStatement'), 'editable line cursor append');
  const lineReturn = returned(lineInner); assert.equal(lineReturn.type, 'SequenceExpression'); assert.equal(lineReturn.expressions.length, 2);
  compare(f, decl(lineInner, 'c'), decl(ownLineUrl, 'to'), 'complete line cursor calculation', { g: 'beforeCursor', m: 'beforeTs' });
  compare(f, lineReturn.expressions[0].left, ownLineCursor.test, 'complete line cursor append condition', { c: 'to' });
  compare(f, lineReturn.expressions[0].right, ownLineCursor.consequent.expression, 'complete line cursor append', { c: 'to', u: 'parts' });
  compare(f, lineReturn.expressions[1], returned(ownLineUrl), 'complete line URL return',
    { y: 'candlePath', e: 'baseUrl', t: 'chainId', r: 'address', u: 'parts' });

  const candle = exp(decoder, 771073, 'Z'), ownCandle = local('decodeCandle');
  const sourceInitial = candle.body.body[0].declarations.map((n) => n.init), ownInitial = ownCandle.body.body[0].declarations.map((n) => n.init);
  assert.equal(sourceInitial.length, 4); assert.equal(ownInitial.length, 4);
  for (let i = 0; i < 4; i++) compare(decoder, sourceInitial[i], ownInitial[i], `complete OHLC conversion ${i}`, { o: 'positive', e: 'value' });
  compare(decoder, returned(candle), returned(ownCandle), 'complete candle acceptance/result', { t: 'open', r: 'high', a: 'low', i: 'close', e: 'value' });
  const positivity = resolve(decoder, { type: 'Identifier', name: 'o' });
  compare(decoder, positivity.body.body[0].declarations[0].init, local('positive').init.body.body[0].declarations[0].init, 'positive numeric conversion', { e: 'value' });
  compare(decoder, returned(positivity), returned(local('positive').init), 'positive finite acceptance', { t: 'n' });
  const monday = exp(week, 921152, 'h'), ownMonday = local('utcWeekStart');
  compare(week, monday.body.body[0].declarations.map((n) => n.init), ownMonday.body.body[0].declarations.map((n) => n.init),
    'complete UTC week input conversion', { e: 'time', t: 'date' });
  compare(week, returned(monday), returned(ownMonday), 'complete UTC Monday bucket', { t: 'date', r: 'day' });
  witness(decoder, candle, 'complete upstream candle decoder and dependency context');
  witness(week, monday, 'used week bucket only; unrelated chart/storage exports excluded');
  const endpoint = exp(origin, 503630, 'R');
  assert.equal(returned(endpoint).value, 'https://frontend-api-v3.pump.fun');
  witness(origin, endpoint, 'reused existing origin attribution; not a local network default');

  const candleNormalize = returned(exp(f, 505835, 'Z')).callee, ownNormalize = local('normalizeCandlePage');
  assert.equal(candleNormalize.type, 'ArrowFunctionExpression');
  witness(f, candleNormalize, 'complete post-delivery candle normalization callback');
  const objectReturns = (node) => findNodes(node, (n) => n.type === 'ReturnStatement' && n.argument?.type === 'ObjectExpression' &&
    n.argument.properties.some((p) => propertyName(p.key) === 'candles')).map((n) => n.argument);
  const sourceReturns = objectReturns(candleNormalize), ownReturns = objectReturns(ownNormalize);
  assert.equal(sourceReturns.length, 3); assert.equal(ownReturns.length, 3);
  const resultRoles = [{ i: 'servedRes', s: 'supply' }, { o: 'ordered', e: 'page', i: 'servedRes', s: 'supply' },
    { l: 'candles', e: 'page', i: 'servedRes', s: 'supply' }];
  for (let i = 0; i < 3; i++) compare(f, sourceReturns[i], ownReturns[i], `complete candle result branch ${i}`, resultRoles[i]);
  for (const field of ['high', 'low', 'close', 'volume']) {
    const assign = (node, receiver) => exactlyOne(findNodes(node, (n) => n.type === 'AssignmentExpression' && member(n.left, receiver, field)), `${receiver}.${field} aggregation`);
    compare(f, assign(candleNormalize, 'i'), assign(ownNormalize, 'existing'), `complete bucket ${field} update`, { i: 'existing', a: 'candle' });
  }
  const lineNormalize = exp(f, 628731, 's'), ownLineNormalize = local('normalizeLinePage');
  const sourceMap = exactlyOne(findNodes(lineNormalize, (n) => n.type === 'CallExpression' && propertyName(n.callee.property) === 'flatMap'), 'source normalized points map').arguments[0];
  const ownMap = exactlyOne(findNodes(ownLineNormalize, (n) => n.type === 'CallExpression' && propertyName(n.callee.property) === 'flatMap'), 'editable normalized points map').arguments[0];
  compare(f, sourceMap.body.body[0].declarations[0].init, ownMap.body.body[0].declarations[0].init, 'complete line price conversion', { e: 'point' });
  compare(f, returned(sourceMap), returned(ownMap), 'complete finite-positive line point filter/projection', { e: 'point', t: 'price' });
  const sortCall = (node) => exactlyOne(findNodes(node, (n) => n.type === 'CallExpression' && propertyName(n.callee.property) === 'sort'), 'line ordering').arguments[0];
  compare(f, sortCall(lineNormalize).body, sortCall(ownLineNormalize).body, 'complete ascending point order', { e: 'a', t: 'b' });

  const attempt = resolve(f, { type: 'Identifier', name: 'A' }), ownAttempt = local('attempt');
  witness(f, attempt, 'complete one-attempt fetch/JSON/body/error callback');
  assert.deepEqual(attempt.body.body.map((n) => n.type), ownAttempt.body.body.map((n) => n.type), 'complete attempt top-level operation order');
  const catches = findNodes(attempt, (n) => n.type === 'CatchClause'), ownCatches = findNodes(ownAttempt, (n) => n.type === 'CatchClause');
  assert.equal(catches.length, 2); assert.equal(ownCatches.length, 2);
  compare(f, catches[0].body.body[0], ownCatches[0].body.body[0], 'complete immediate fetch AbortError branch', { e: 'error' });
  compare(f, catches[0].body.body[1].argument, ownCatches[0].body.body[1].argument, 'complete network failure normalization',
    { e: 'error', r: 'CandleHistoryFetchError' });
  compare(f, catches[1].body.body[0].argument, ownCatches[1].body.body[0].argument, 'complete JSON failure normalization including body abort',
    { s: 'response', r: 'CandleHistoryFetchError' });
  const tries = attempt.body.body.filter((n) => n.type === 'TryStatement'), ownTries = ownAttempt.body.body.filter((n) => n.type === 'TryStatement');
  compare(f, tries[0].block.body[0].expression, ownTries[0].block.body[0].expression, 'complete awaited fetch invocation',
    { s: 'response', t: 'fetchImpl', e: 'url', a: 'init' });
  compare(f, tries[1].block.body[0].expression, ownTries[1].block.body[0].expression, 'complete original-response JSON consumption', { n: 'body', s: 'response' });
  const httpIf = exactlyOne(findNodes(attempt, (n) => n.type === 'IfStatement' && n.test.type === 'BinaryExpression' && propertyName(n.test.right.property) === 'ok'), 'exact HTTP branch');
  const ownHttpIf = exactlyOne(findNodes(ownAttempt, (n) => n.type === 'IfStatement' && n.test.type === 'BinaryExpression' && propertyName(n.test.right.property) === 'ok'), 'editable HTTP branch');
  compare(f, httpIf.test, ownHttpIf.test, 'HTTP branch only for exact false ok', { s: 'response' });
  const httpResult = exactlyOne(httpIf.consequent.body.filter((n) => n.type === 'ReturnStatement'), 'source HTTP failure result').argument;
  compare(f, objectProperty(httpResult, 'retryable'), objectProperty(ownHttpIf.consequent.argument, 'retryable'),
    'complete primary HTTP retry predicate', { e: 'status', s: 'response' });
  compare(f, objectProperty(httpResult, 'error').arguments, objectProperty(ownHttpIf.consequent.argument, 'error').arguments,
    'complete primary HTTP status/message fields', { s: 'response' });
  compare(f, returned(attempt), returned(ownAttempt), 'complete JSON body validation success/error result',
    { i: 'isBody', n: 'body', s: 'response', r: 'CandleHistoryFetchError' });
  const request = resolve(f, { type: 'Identifier', name: 'T' }), ownRequest = local('requestHistory');
  witness(f, request, 'complete retry/relay/final-error state machine');
  compare(f, resolve(f, { type: 'Identifier', name: 'M' }), local('wait').init, 'complete default retry sleeper', { e: 'ms', t: 'resolve' });
  const originalLoop = exactlyOne(findNodes(request, (n) => n.type === 'ForStatement'), 'source attempt loop');
  const ownLoop = exactlyOne(findNodes(ownRequest, (n) => n.type === 'ForStatement'), 'editable attempt loop');
  for (const key of ['init', 'test', 'update']) compare(f, originalLoop[key], ownLoop[key], `complete retry loop ${key}`, { r: 'index', o: 'retryDelaysMs' });
  const defaults = (node, name) => objectProperty(node.params[2], name).right;
  for (const name of ['relay', 'retryDelaysMs']) compare(f, defaults(request, name), defaults(ownRequest, name), `actual request default ${name}`);
  const sourceFinal = request.body.body.at(-1).argument;
  const ownFinal = ownRequest.body.body.at(-1).argument;
  compare(f, sourceFinal.arguments, ownFinal.arguments, 'complete final primary error and stale relay details', { c: 'primaryError', d: 'relayError' });
  const sourceRelayPath = exactlyOne(findNodes(request, (n) => n.type === 'TemplateLiteral' && n.quasis[0].value.cooked === '/api/swap-api'), 'source relay path');
  const ownRelayPath = exactlyOne(findNodes(ownRequest, (n) => n.type === 'TemplateLiteral'), 'editable relay path');
  compare(f, sourceRelayPath, ownRelayPath, 'complete relative relay path', { t: 'parsed' });
  const sourceAttempts = findNodes(originalLoop, (n) => n.type === 'CallExpression' && n.callee.name === 'A');
  const ownAttempts = findNodes(ownLoop, (n) => n.type === 'CallExpression' && n.callee.name === 'attempt');
  assert.equal(sourceAttempts.length, 2); assert.equal(ownAttempts.length, 2);
  for (let i = 0; i < 2; i++) compare(f, sourceAttempts[i].arguments, ownAttempts[i].arguments, `complete ordered fetch capability invocation ${i}`,
    { e: 'url', a: 'fetchImpl', i: 'init', t: 'isBody', u: 'relayUrl', n: 'relayFetchImpl' });
  const breakIf = (node) => exactlyOne(findNodes(node, (n) => n.type === 'IfStatement' && n.consequent.type === 'BreakStatement'), 'primary retryability stop');
  compare(f, breakIf(originalLoop), breakIf(ownLoop), 'complete primary-only retryability stop', { s: 'primary' });
  const sourceRelayIf = exactlyOne(findNodes(originalLoop, (n) => n.type === 'IfStatement' && n.test.type === 'SequenceExpression'), 'source relay eligibility');
  const ownRelayIf = exactlyOne(findNodes(ownLoop, (n) => n.type === 'IfStatement' && n.test.type === 'LogicalExpression'), 'editable relay eligibility');
  const ownPrimaryError = exactlyOne(ownLoop.body.body.filter((n) => n.type === 'ExpressionStatement' && n.expression.left?.name === 'primaryError'), 'primary error update').expression;
  compare(f, sourceRelayIf.test.expressions[0], ownPrimaryError, 'complete primary error state update', { c: 'primaryError', s: 'primary' });
  compare(f, sourceRelayIf.test.expressions[1], ownRelayIf.test, 'complete network-only relay eligibility', { s: 'primary', u: 'relayUrl' });
  const sourcePrimarySuccess = exactlyOne(findNodes(originalLoop, (n) => n.type === 'IfStatement' && member(n.test, 's', 'ok')), 'primary success branch');
  const ownPrimarySuccess = exactlyOne(findNodes(ownLoop, (n) => n.type === 'IfStatement' && member(n.test, 'primary', 'ok')), 'editable primary success branch');
  compare(f, sourcePrimarySuccess, ownPrimarySuccess, 'complete primary-success immediate return', { s: 'primary' });
  const sourceRelaySuccess = exactlyOne(findNodes(sourceRelayIf, (n) => n.type === 'IfStatement' && member(n.test, 'e', 'ok')), 'relay success branch');
  const ownRelaySuccess = exactlyOne(findNodes(ownRelayIf, (n) => n.type === 'IfStatement' && member(n.test, 'fallback', 'ok')), 'editable relay success branch');
  assert.equal(sourceRelaySuccess.consequent.argument.type, 'SequenceExpression');
  compare(f, sourceRelaySuccess.test, ownRelaySuccess.test, 'complete relay success guard', { e: 'fallback' });
  compare(f, sourceRelaySuccess.consequent.argument.expressions[0], ownRelaySuccess.consequent.body[0].expression,
    'complete synchronous relay-served callback before return', { m: 'onRelayServed', r: 'index' });
  compare(f, sourceRelaySuccess.consequent.argument.expressions[1], ownRelaySuccess.consequent.body[1].argument,
    'complete successful relay return', { e: 'fallback' });
  compare(f, sourceRelayIf.consequent.body.at(-1).expression, ownRelayIf.consequent.body.at(-1).expression,
    'complete failed relay detail update', { d: 'relayError', e: 'fallback' });
  const sleepStep = originalLoop.body.body[0].expression, ownSleep = ownLoop.body.body[0];
  compare(f, sleepStep.left, ownSleep.test, 'retry sleep occurs only after attempt zero', { r: 'index' });
  compare(f, sleepStep.right, ownSleep.consequent.expression, 'complete awaited retry-delay selection', { l: 'sleep', o: 'retryDelaysMs', r: 'index' });

  const sourceCandleRead = structuredClone(returned(exp(f, 505835, 'Z')));
  assert.equal(sourceCandleRead.callee.type, 'ArrowFunctionExpression');
  sourceCandleRead.callee = { type: 'Identifier', name: 'normalizeCandlePage' };
  compare(f, sourceCandleRead, returned(local('readCandleHistory')), 'complete candle read operation with bound normalization port',
    { T: 'requestHistory', x: 'buildCandleUrl', v: 'isCandlePage', e: 'input' });
  const sourceLineRead = structuredClone(returned(lineRead));
  sourceLineRead.arguments[0].argument.arguments[0].callee = { type: 'Identifier', name: 'buildLineUrl' };
  compare(f, sourceLineRead, returned(local('readLineHistory')), 'complete line read operation with bound URL-constructor port',
    { n: 'normalizeLinePage', T: 'requestHistory', w: 'isLinePage', c: 'rest', r: 'res', u: 'baseUrl',
      e: 'chainId', t: 'address', i: 'count', s: 'maxPoints', o: 'measure', m: 'beforeTs' });

  for (const item of selected.values()) if ([349942, 997627].includes(item.id)) {
    const imp = imported(item, 505835);
    const method = item.id === 349942 ? 'Z' : 'x';
    const call = exactlyOne(findNodes(item.node, (n) => n.type === 'CallExpression' && n.callee.type === 'SequenceExpression' &&
      member(n.callee.expressions.at(-1), imp.id.name, method)), `actual incoming ${method}`);
    incoming.push({ id: item.id, export: method, ...item.witness(call, 'reused actual normalized caller interface; no new caller recovery') });
  }
  return { schemaVersion: 1, baseCommit: '094a06f18df738d41e77070c1a009e135671ac1a', anchors: corpus.anchors,
    editableSha256: sha256(bytes), factories, fragments, imports, comparisons, incoming,
    boundary: { recovered: ['505835.Z/x request and normalization operations', 'retry/optional relay/error state', '771073.Z decoder', 'used921152.h week bucket'],
      reused: ['503630 origin attribution', '#1827 existing mapper/key/normalized-caller interface work'],
      hostFacade: 'authored explicit destination/fetch capability admission and call-options snapshot; source core candle operation preserves interval reread after await' },
    limits: { capturedExecution: false, externalAcquisition: false, serviceImplementation: false, RPC: false,
      financialDataQuality: false, mountedUI: false, nativeAPICompatibility: false, fullUniversalEquivalence: false, progressCredit: false } };
}
export async function verifyHistory(root = APP_ROOT) {
  const result = await buildHistoryProof(root);
  assert.deepEqual(JSON.parse(await readFile(path.join(root, PROOF), 'utf8')), result, 'history source proof differs');
  return result;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (process.argv[2] === '--write') await writeFile(path.join(APP_ROOT, PROOF), `${JSON.stringify(await buildHistoryProof(), null, 2)}\n`);
  else { assert.equal(process.argv[2], '--check'); await verifyHistory(); }
  console.log('Candle history source proof PASS');
}
