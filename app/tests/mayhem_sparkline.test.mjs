import assert from 'node:assert/strict';
import { test } from 'node:test';
import { mkdtemp, mkdir, copyFile, readFile, writeFile, rm } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { isYoungCoin, youngCandleWindow, defaultLineWindow, lineParameters, createSparklineReader,
  planSparklineQuery, mayhemSparklineInput, renderMayhemSparkline, createMayhemSparkline,
  sparklineRefetchInterval } from '../reconstruction/mayhem-sparkline/sparkline.mjs';
import { APP_ROOT, DIRECTORY, PROOF, buildSparklineProof, verifySparkline } from '../reconstruction/mayhem-sparkline/verify.mjs';

const renderer = {
  jsx: (type, props) => ({ type, props }), jsxs: (type, props) => ({ type, props }),
  // Test capability only; the actual 338319.c utility is not reimplemented here.
  mergeClassNames: (...parts) => ({ suppliedClassParts: parts }),
};
const base = { coinAddress: 'public-synthetic-mint', coinCreatedTimestamp: 1000000, chainId: undefined };
function readPorts(overrides = {}) {
  return { now: () => 1100000, resolveChain: () => 'solana:test',
    readCandleHistory: async () => ({ candles: [] }), readLineHistory: async () => ({ points: [] }), ...overrides };
}

test('young-coin and age windows retain exact thresholds, future clamping and invalid creation behavior', () => {
  const created = 1000000;
  for (const [age, interval, limit] of [[0, '1s', 300], [299999, '1s', 300], [300000, '15s', 65],
    [900000, '30s', 65], [1800000, '1m', 65], [3600000, '1m', 65]]) {
    assert.deepEqual(youngCandleWindow(created, created + age), { interval, limit });
    assert.equal(isYoungCoin(created, created + age), true);
  }
  assert.equal(isYoungCoin(created, created + 3600001), false);
  assert.equal(isYoungCoin(created, created - 1), true);
  for (const created of [0, -1, NaN, Infinity, '1000000', null]) assert.equal(isYoungCoin(created, 1000000), false);
  for (const [age, timeframe, width] of [[0, '1m', 24], [300000, '5m', 28], [900000, '15m', 32],
    [1800000, '15m', 52], [3600000, '30m', 64], [21600000, '6h', 68],
    [86400000, '24h', 72], [172800000, '1w', 72]]) {
    assert.deepEqual(defaultLineWindow(created, created + age), { timeframe, width });
  }
  assert.deepEqual(defaultLineWindow(NaN, created), { timeframe: '1w', width: 72 });
});

test('line request parameters retain timeframe parsing, first-fit resolution and point/count bounds', () => {
  assert.deepEqual(lineParameters({ createdTs: 900000, timeframe: ' 6H ', width: 71.5, nowMs: 1000000 }),
    { res: '1s', count: 100, maxPoints: 72 });
  assert.deepEqual(lineParameters({ createdTs: 0, timeframe: '1w', width: Infinity, nowMs: 1000000000 }),
    { res: '1h', count: 168, maxPoints: 2 });
  assert.deepEqual(lineParameters({ createdTs: 1001, timeframe: '0m', width: 9999, nowMs: 1000 }),
    { res: '1s', count: 1, maxPoints: 2000 });
  assert.equal(lineParameters({ createdTs: 1, timeframe: 'unsupported', width: 72, nowMs: 1000 }), null);
  assert.throws(() => lineParameters({ timeframe: null }), TypeError);
});

test('the young reader consumes normalized candles, stringifies OHLCV then filters converted close/time', async () => {
  let delivered;
  const read = createSparklineReader(readPorts({
    resolveChain: (input) => { assert.deepEqual(input, { mint: base.coinAddress, chainId: undefined }); return 'solana:test'; },
    readCandleHistory: async (input) => { delivered = input; return { candles: [
      { timestamp: 1, open: 2, high: 3, low: 0, close: 0, volume: 4 },
      { timestamp: 2, close: '2.5' }, { timestamp: 3, close: null },
      { timestamp: '4', close: 4 }, { timestamp: 5, close: -1 },
      { timestamp: 6, close: Infinity }, { timestamp: 7, close: '' },
    ] }; },
    readLineHistory: async () => { throw Error('wrong branch'); },
  }));
  const init = { signal: 'explicit-test-token' };
  assert.deepEqual(await read({ ...base, fetchOptions: init }), [{ time: 1, price: 0 }, { time: 2, price: 2.5 }, { time: 7, price: 0 }]);
  assert.deepEqual(delivered, { chainId: 'solana:test', address: base.coinAddress, interval: '1s',
    measure: 'price_usd', count: 300, beforeTs: undefined, init });
  assert.ok(Object.hasOwn(delivered, 'beforeTs'));
});

test('old and explicitly non-candle reads delegate normalized line points without another parser or sort', async () => {
  const points = [{ time: 2, price: 20 }, { time: 1, price: 10 }];
  const calls = [];
  const read = createSparklineReader(readPorts({ now: () => 5000000,
    readLineHistory: async (args) => { calls.push(args); return { points }; },
    readCandleHistory: async () => { throw Error('wrong branch'); } }));
  assert.strictEqual(await read({ ...base, timeframe: '6h', width: 3 }), points);
  assert.deepEqual(calls[0], { chainId: 'solana:test', address: base.coinAddress, res: '15s', count: 267,
    maxPoints: 3, measure: 'price_usd', init: undefined });
  const forced = createSparklineReader(readPorts({ readLineHistory: async () => ({ points }) }));
  assert.strictEqual(await forced({ ...base, youngCoinSource: null }), points);
});

test('reader failures propagate exact dependency errors and do not fabricate points or a transport fallback', async () => {
  const error = new Error('normalized history dependency failed');
  const read = createSparklineReader(readPorts({ readCandleHistory: async () => { throw error; } }));
  await assert.rejects(read(base), (e) => e === error);
  const missingChain = createSparklineReader(readPorts({ resolveChain: () => null }));
  await assert.rejects(missingChain(base), /Failed to fetch coin candles/);
  const badWindow = createSparklineReader(readPorts({ now: () => 5000000 }));
  await assert.rejects(badWindow({ ...base, timeframe: 'bad' }), /Failed to fetch coin line chart: bad/);
  const invalidBody = createSparklineReader(readPorts({ readCandleHistory: async () => ({}) }));
  await assert.rejects(invalidBody(base), TypeError);
});

test('planner preserves source cache partitions and option-spread override precedence', async () => {
  const readSparkline = async (args) => args;
  const query = planSparklineQuery({ ...base, timeframe: '6h', width: 11, queryOptions: { staleTime: 5 } }, { now: () => 1100000, readSparkline });
  assert.deepEqual(query.queryKey, ['coinCandles', base.coinAddress, 1000000, '1s', 300, 'sparklineLineChartPoints', null]);
  assert.deepEqual(await query.queryFn(), { ...base, timeframe: '6h', width: 11, youngCoinSource: 'candles' });
  assert.equal(query.enabled, true); assert.equal(query.staleTime, 5);
  const customFn = () => 'source permits this override';
  const overridden = planSparklineQuery({ ...base, queryOptions: { queryFn: customFn, queryKey: ['caller-key'], enabled: false } }, { readSparkline });
  assert.strictEqual(overridden.queryFn, customFn); assert.deepEqual(overridden.queryKey, ['caller-key']); assert.equal(overridden.enabled, false);
  const old = planSparklineQuery({ ...base, chainId: '', youngCoinSource: 'line' }, { now: () => 5000000, readSparkline });
  assert.deepEqual(old.queryKey, ['coinLineChart', base.coinAddress, 1000000, '30m', 64, 'sparklineLineChartPoints', '']);
});

test('generic TON eligibility and the actual Mayhem enabled guard remain separate', () => {
  const ports = { now: () => 5000000, readSparkline: async () => [] };
  const generic = planSparklineQuery({ coinAddress: 'ton-public-test', chainId: 'ton:-239' }, ports);
  assert.equal(generic.enabled, true);
  const caller = mayhemSparklineInput({ mint: 'ton-public-test', chainId: 'ton:-239', createdTimestamp: 0 }, () => { throw Error('invalid timestamp must not sample'); });
  assert.equal(planSparklineQuery(caller, ports).enabled, false);
  assert.equal(planSparklineQuery({ coinAddress: '', chainId: 'ton:-239' }, ports).enabled, false);
  assert.equal(planSparklineQuery({ coinAddress: 'a', coinCreatedTimestamp: Infinity }, ports).enabled, false);
});

test('adjusted parent time and independently sampled raw provider time can choose different age branches', async () => {
  const raw = 1100000, created = 1000000, calls = [];
  const now = () => { calls.push('raw'); return raw; };
  const descriptor = mayhemSparklineInput({ mint: base.coinAddress, createdTimestamp: created }, () => { calls.push('adjusted'); return raw + 90000000; });
  assert.equal(descriptor.timeframe, '1w');
  const read = createSparklineReader(readPorts({ now, readCandleHistory: async () => ({ candles: [] }) }));
  const query = planSparklineQuery(descriptor, { now, readSparkline: read });
  assert.equal(query.queryKey[0], 'coinCandles');
  assert.deepEqual(calls, ['adjusted', 'raw', 'raw', 'raw']);
  await query.queryFn();
  assert.deepEqual(calls, ['adjusted', 'raw', 'raw', 'raw', 'raw', 'raw']);
  let instant = created + 3599999, branch;
  const crossingNow = () => instant;
  const crossingRead = createSparklineReader(readPorts({ now: crossingNow,
    readCandleHistory: async () => { branch = 'candles'; return { candles: [] }; },
    readLineHistory: async () => { branch = 'line'; return { points: [] }; } }));
  const crossing = planSparklineQuery({ ...base, coinCreatedTimestamp: created }, { now: crossingNow, readSparkline: crossingRead });
  assert.equal(crossing.queryKey[0], 'coinCandles');
  instant = created + 3600001;
  await crossing.queryFn();
  assert.equal(branch, 'line');
  assert.equal(crossing.queryKey[0], 'coinCandles');
  assert.equal(sparklineRefetchInterval({ state: {} }), 10000);
  assert.equal(sparklineRefetchInterval({ state: { data: [1] } }), 10000);
  assert.equal(sparklineRefetchInterval({ state: { data: [1, 2] } }), false);
});

test('the actual caller/query/reader/SVG recomputation flow retains id use and line/fill/gradient delivery', async () => {
  let data, options, ids = 0;
  const read = createSparklineReader(readPorts({ readCandleHistory: async () => ({ candles: [
    { timestamp: 10, close: 10 }, { timestamp: 1000, close: 20 },
  ] }) }));
  const render = createMayhemSparkline({ ...renderer, adjustedNow: () => 1100000, now: () => 1100000,
    readSparkline: read, useId: () => { ids++; return ':test-id:'; },
    getQueryResult: (query) => { options = query; return { data }; } });
  const props = { mint: base.coinAddress, createdTimestamp: 1000000, colorClassName: 'text-gain', className: 'row-chart' };
  const empty = render(props);
  assert.equal(empty.type, 'div'); assert.equal(ids, 1); assert.equal(options.enabled, true);
  assert.deepEqual(empty.props.className.suppliedClassParts, ['h-12 w-full', 'row-chart']);
  assert.equal(options.staleTime, 300000); assert.equal(options.gcTime, 600000);
  data = await options.queryFn();
  const svg = render(props);
  assert.equal(svg.type, 'svg'); assert.equal(ids, 2);
  assert.deepEqual(svg.props.className.suppliedClassParts, ['h-12 w-full', 'text-gain', 'row-chart']);
  const [defs, fill, line] = svg.props.children;
  assert.equal(defs.props.children.type, 'linearGradient'); assert.equal(defs.props.children.props.id, ':test-id:');
  assert.deepEqual(defs.props.children.props.children.map((stop) => stop.props.stopOpacity), [0.28, 0]);
  assert.equal(line.props.d, 'M0,90 L100,10'); assert.equal(line.props.vectorEffect, 'non-scaling-stroke');
  assert.equal(fill.props.d, 'M0,90 L100,10 L100,100 L0,100 Z'); assert.equal(fill.props.fill, 'url(#:test-id:)');
});

test('SVG fallback and malformed-data behavior are source operations, not extra admission rules', () => {
  for (const data of [null, undefined, [], [{ price: 1 }], { length: 1 }]) {
    const view = renderMayhemSparkline({ data, id: 'id' }, renderer);
    assert.equal(view.type, 'div'); assert.equal(view.props['aria-hidden'], true);
  }
  assert.throws(() => renderMayhemSparkline({ data: {}, id: 'id' }, renderer), TypeError);
  const flat = renderMayhemSparkline({ data: [{ price: 5 }, { price: 5 }, { price: 5 }], id: 'id' }, renderer);
  assert.equal(flat.props.children[2].props.d, 'M0,90 L50,90 L100,90');
  const invalid = renderMayhemSparkline({ data: [{ price: NaN }, { price: 5 }], id: 'id' }, renderer);
  assert.equal(invalid.props.children[2].props.d, 'M0,NaN L100,NaN');
});

const proof = await buildSparklineProof();
async function isolated(t) {
  const root = await mkdtemp(path.join(os.tmpdir(), 'sparkline public source '));
  t.after(() => rm(root, { recursive: true, force: true }));
  for (const rel of new Set(['evidence/web/manifest.json', 'recovered/modules.json', PROOF,
    `${DIRECTORY}/sparkline.mjs`, ...proof.factories.map((f) => f.source)])) {
    await mkdir(path.dirname(path.join(root, rel)), { recursive: true });
    await copyFile(path.join(APP_ROOT, rel), path.join(root, rel));
  }
  return root;
}
test('the full physical-variant source proof replays from raw public inputs without formatted modules', async (t) => {
  const root = await isolated(t);
  assert.deepEqual(await verifySparkline(root), proof);
  assert.equal(proof.factories.length, 22);
  assert.equal(proof.variantContracts.length, 3);
});
test('changed geometry, option precedence and provider variants cannot be resealed as original source', async (t) => {
  const root = await isolated(t), file = path.join(root, DIRECTORY, 'sparkline.mjs');
  const original = await readFile(file, 'utf8');
  await writeFile(file, original.replace('/ range * 80', '/ range * 75'));
  await assert.rejects(buildSparklineProof(root), /y coordinate/);
  await writeFile(file, original.replace('{ queryFn, queryKey, ...rest, enabled:', '{ ...rest, queryFn, queryKey, enabled:'));
  await assert.rejects(buildSparklineProof(root), /editable query option spread order/);
  await writeFile(file, original);
  const indexFile = path.join(root, 'recovered/modules.json'), index = JSON.parse(await readFile(indexFile, 'utf8'));
  index.modules = index.modules.filter((m) => !m.sha256.startsWith('87ebb7ab3bf5'));
  await writeFile(indexFile, JSON.stringify(index));
  await assert.rejects(buildSparklineProof(root), /physical variant census 375676/);
});
