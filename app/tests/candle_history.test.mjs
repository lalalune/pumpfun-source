import assert from 'node:assert/strict';
import { test } from 'node:test';
import http from 'node:http';
import { once } from 'node:events';
import { mkdtemp, mkdir, copyFile, readFile, writeFile, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { CandleHistoryFetchError, CAPTURED_RETRY_DELAYS, buildCandleUrl, buildLineUrl,
  isCandlePage, isLinePage, decodeCandle, normalizeCandlePage, normalizeLinePage,
  utcWeekStart, requestHistory, readCandleHistory, createCandleHistoryClient } from '../reconstruction/candle-history/client.mjs';
import { APP_ROOT, DIRECTORY, PROOF, buildHistoryProof, verifyHistory } from '../reconstruction/candle-history/verify.mjs';

const bar = (time, close = 4, extras = {}) => ({ openTimeMs: time, open: 1, high: 9, low: 0.5, close, volumeUsd: 2, ...extras });
const page = (candles = [], res = '1m', extra = {}) => ({ candles, hasOlder: false, served: { res }, ...extra });
const line = (points = [], res = '1m') => ({ points, served: { res } });
const params = { chainId: 'solana:test', address: 'public/A?B', interval: '1m', measure: 'price_usd' };
const json = (response, body, status = 200) => { response.writeHead(status, { 'content-type': 'application/json' }); response.end(JSON.stringify(body)); };
async function local(t, handler) {
  const requests = [], server = http.createServer((request, response) => {
    requests.push({ method: request.method, url: request.url, publicMarker: request.headers['x-test-marker'] });
    handler(request, response, requests.length);
  });
  server.listen(0, '127.0.0.1'); await once(server, 'listening');
  t.after(async () => { server.closeAllConnections(); await new Promise((resolve) => server.close(resolve)); });
  const base = `http://127.0.0.1:${server.address().port}`;
  return { requests, base, client: createCandleHistoryClient({ baseUrl: `${base}/v1///`,
    fetchImpl: globalThis.fetch, relayFetchImpl: (url, init) => globalThis.fetch(new URL(url, base), init) }) };
}

test('URL construction retains count multiplication/clamps, raw field order, address encoding and exclusive cursor', () => {
  assert.equal(buildCandleUrl({ ...params, baseUrl: 'http://127.0.0.1:1/v1///', interval: '30m', count: 20.2, beforeTs: 20.9 }),
    'http://127.0.0.1:1/v1/candles/solana:test/public%2FA%3FB?res=15m&count=41&measure=price_usd&to=19');
  assert.match(buildCandleUrl({ ...params, baseUrl: 'http://127.0.0.1:1', interval: '1w', count: 100 }), /res=1d&count=300&measure=price_usd$/);
  assert.match(buildCandleUrl({ ...params, baseUrl: 'http://127.0.0.1:1', interval: '6h', count: 2, beforeTs: 0 }), /res=4h&count=2&measure=price_usd$/);
  assert.match(buildLineUrl({ ...params, baseUrl: 'http://127.0.0.1:1', res: '1s', count: 0, maxPoints: 3.6, beforeTs: 1 }),
    /\/line\?res=1s&count=1&maxPoints=4&measure=price_usd&to=0$/);
  assert.match(buildLineUrl({ ...params, baseUrl: 'http://127.0.0.1:1', res: '1m' }), /count=NaN&maxPoints=NaN/);
  assert.throws(() => buildCandleUrl({ ...params, baseUrl: 'x', interval: 'unsupported' }), TypeError);
});

test('candle decoder and last-valid timestamp dedup retain distinct numeric/volume/supply behavior without mutating input', () => {
  assert.equal(decodeCandle(bar('1')), null);
  assert.equal(decodeCandle(bar(1, 0)), null);
  assert.equal(decodeCandle(bar(1, 1, { high: NaN })), null);
  assert.equal(decodeCandle(bar(1, '2', { volumeUsd: -2 })).volume, -2);
  assert.equal(decodeCandle(bar(1, '2', { volumeUsd: Infinity })).volume, Infinity);
  const input = page([bar(2, '4'), bar(1, '2'), bar(2, '5'), bar(2, 0)], '1m', { supplyUsed: ' 7 ' });
  const before = structuredClone(input), result = normalizeCandlePage(input, '1m');
  assert.deepEqual(result.candles.map((b) => [b.timestamp, b.close]), [[1, 2], [2, 5]]);
  assert.equal(result.supplyUsed, 7); assert.deepEqual(input, before);
  assert.equal(normalizeCandlePage(page([], '1m', { supplyUsed: 7 }), '1m').supplyUsed, undefined);
  assert.deepEqual(normalizeCandlePage(page([null], 'wrong', { hasOlder: true }), '1m'),
    { candles: [], hasOlder: false, servedRes: 'wrong', intervalMismatch: true, supplyUsed: undefined });
});

test('bucket aggregation preserves first open/last close, high-low extrema, volume, weekly UTC and leading-bucket trim rule', () => {
  const input = page([bar(1, 3, { open: 2, high: 5, low: 1, volumeUsd: 3 }),
    bar(900001, 7, { open: 4, high: 10, low: 0.5, volumeUsd: 4 }), bar(1800001, 8)], '15m');
  const result = normalizeCandlePage(input, '30m');
  assert.deepEqual(result.candles[0], { timestamp: 0, open: 2, high: 10, low: 0.5, close: 7, volume: 7 });
  assert.equal(result.candles.length, 2);
  assert.deepEqual(normalizeCandlePage({ ...input, hasOlder: true }, '30m').candles, result.candles.slice(1));
  const single = normalizeCandlePage(page(input.candles.slice(0, 2), '15m', { hasOlder: true }), '30m');
  assert.equal(single.candles.length, 1);
  const monday = Date.UTC(2024, 0, 1);
  assert.equal(utcWeekStart(monday + 6 * 86400000 + 123), monday);
  assert.equal(normalizeCandlePage(page([bar(monday + 86400000), bar(monday + 2 * 86400000)], '1d'), '1w').candles[0].timestamp, monday);
  assert.deepEqual(normalizeCandlePage(page([bar(1), bar(2)], '4h'), '6h').candles.map((b) => b.timestamp), [1, 2]);
});

test('line normalization keeps raw barCount, filters/number-converts positive prices, sorts times and bypasses rows on res mismatch', () => {
  const result = normalizeLinePage(line([{ time: 2, price: '2' }, { time: 1, price: 1 }, { time: 3, price: 0 },
    { time: '4', price: 4 }, { time: 5, price: Infinity }]), '1m');
  assert.deepEqual(result, { points: [{ time: 1, price: 1 }, { time: 2, price: 2 }], barCount: 5, servedRes: '1m', intervalMismatch: false });
  assert.deepEqual(normalizeLinePage(line([null], 'wrong'), '1m'), { points: [], barCount: 1, servedRes: 'wrong', intervalMismatch: true });
  assert.throws(() => normalizeLinePage(line([null]), '1m'), TypeError);
  assert.equal(isCandlePage(page()), true); assert.equal(isCandlePage({ ...page(), hasOlder: 1 }), false);
  assert.equal(isLinePage(line()), true); assert.equal(isLinePage({ points: [], served: null }), false);
});

test('real loopback GET delivers normalized candles and exact encoded request/init without a service substitute', async (t) => {
  const { client, requests } = await local(t, (_request, response) => json(response, page([bar(2, 4), bar(1, 3)])));
  const result = await client.candles({ ...params, count: 2, beforeTs: 2, init: { headers: { 'x-test-marker': 'public-test-only' } } });
  assert.deepEqual(result.candles.map((b) => b.close), [3, 4]);
  assert.deepEqual(requests, [{ method: 'GET', url: '/v1/candles/solana:test/public%2FA%3FB?res=1m&count=2&measure=price_usd&to=1', publicMarker: 'public-test-only' }]);
});

test('real loopback line GET preserves source URL bounds and returns the normalized point result', async (t) => {
  const { client, requests } = await local(t, (_request, response) => json(response, line([{ time: 2, price: '4' }, { time: 1, price: '3' }])));
  assert.deepEqual(await client.line({ ...params, res: '1m', count: 999, maxPoints: 1 }),
    { points: [{ time: 1, price: 3 }, { time: 2, price: 4 }], barCount: 2, servedRes: '1m', intervalMismatch: false });
  assert.equal(requests[0].url, '/v1/candles/solana:test/public%2FA%3FB/line?res=1m&count=300&maxPoints=2&measure=price_usd');
});

test('default HTTP503 makes one attempt; exported retry delays are not applied implicitly', async (t) => {
  const { client, requests } = await local(t, (_request, response) => json(response, {}, 503));
  assert.deepEqual(CAPTURED_RETRY_DELAYS, [300, 900]);
  await assert.rejects(client.candles(params), (error) => {
    assert.ok(error instanceof CandleHistoryFetchError); assert.equal(error.name, 'CandleHistoryFetchError');
    assert.equal(error.status, 503); assert.equal(error.fallback, null);
    assert.deepEqual(Object.keys(error), ['status', 'fallback', 'name']); return true;
  });
  assert.equal(requests.length, 1);
});

test('real HTTP retry state handles retryable status then success with the supplied delay and same init', async (t) => {
  const { client, requests } = await local(t, (_request, response, count) => count === 1 ? json(response, {}, 429) : json(response, page()));
  const delays = [], observedInit = [], init = { headers: { 'x-test-marker': 'retry-public' } };
  const result = await client.candles({ ...params, retryDelaysMs: [5, 7], sleep: async (ms) => delays.push(ms), init,
    fetchImpl: (url, supplied) => { observedInit.push(supplied); return fetch(url, supplied); } });
  assert.deepEqual(result.candles, []); assert.deepEqual(delays, [5]); assert.equal(requests.length, 2);
  assert.ok(observedInit.every((value) => value === init));
});

test('invalid real HTTP JSON and envelope each consume retry budget, while HTTP404 stops without relay', async (t) => {
  const { client, requests } = await local(t, (_request, response, count) => {
    if (count === 1) { response.writeHead(200); response.end('not JSON'); }
    else if (count === 2) json(response, { candles: [] });
    else if (count === 3) json(response, page()); else json(response, {}, 404);
  });
  const delays = [];
  assert.deepEqual((await client.candles({ ...params, retryDelaysMs: [1, 2], sleep: async (ms) => delays.push(ms) })).candles, []);
  assert.deepEqual(delays, [1, 2]);
  await assert.rejects(client.candles({ ...params, relay: true, retryDelaysMs: [1], relayFetchImpl: () => { throw Error('must not relay an HTTP error'); } }),
    (error) => error.status === 404 && error.fallback === null);
  assert.equal(requests.length, 4);
});

test('real primary socket failure can use the explicit loopback relay and callback with source relative path', async (t) => {
  const { client, requests } = await local(t, (request, response) => {
    if (request.url.startsWith('/api/swap-api/')) json(response, page()); else request.socket.destroy();
  });
  const served = [];
  assert.deepEqual((await client.candles({ ...params, relay: true, onRelayServed: (event) => served.push(event) })).candles, []);
  assert.deepEqual(served, [{ attempt: 0 }]); assert.equal(requests.length, 2);
  assert.equal(requests[1].url, `/api/swap-api${requests[0].url}`);
  assert.ok(requests.every((request) => request.method === 'GET'));
});

test('failed relay details persist while primary retryability/status decide the final error', async (t) => {
  const { client, requests } = await local(t, (request, response, count) => {
    if (count === 1) request.socket.destroy();
    else if (request.url.startsWith('/api/swap-api/')) json(response, {}, 500);
    else json(response, {}, 404);
  });
  const delays = [];
  await assert.rejects(client.candles({ ...params, relay: true, retryDelaysMs: [3, 4], sleep: async (ms) => delays.push(ms) }), (error) => {
    assert.equal(error.status, 404); assert.equal(error.message, 'candle history responded 404');
    assert.deepEqual(error.fallback, { status: 500, message: 'candle history responded 500' }); return true;
  });
  assert.deepEqual(delays, [3]); assert.equal(requests.length, 3);
});

test('fetch AbortError propagates immediately; JSON-body AbortError follows the source malformed-JSON branch', async (t) => {
  const { client, requests } = await local(t, (_request, response) => { response.writeHead(200); response.write('{'); });
  const abort = new DOMException('public synthetic abort', 'AbortError');
  const preAborted = new AbortController(); preAborted.abort(abort);
  await assert.rejects(client.candles({ ...params, init: { signal: preAborted.signal }, retryDelaysMs: [1],
    sleep: () => { throw Error('must not retry fetch abort'); } }), (e) => e === abort);
  const bodyController = new AbortController();
  await assert.rejects(client.candles({ ...params, init: { signal: bodyController.signal }, fetchImpl: async (url, init) => {
    const response = await fetch(url, init); bodyController.abort(abort); return response;
  } }), (e) => e instanceof CandleHistoryFetchError && e.status === 200 && e.message === 'candle history body was not JSON');
  const retryController = new AbortController(), delays = []; let attempts = 0;
  await assert.rejects(client.candles({ ...params, init: { signal: retryController.signal }, retryDelaysMs: [3],
    sleep: async (ms) => delays.push(ms), fetchImpl: async (url, init) => {
      attempts++; const response = await fetch(url, init); retryController.abort(abort); return response;
    } }), (e) => e === abort);
  assert.deepEqual(delays, [3]); assert.equal(attempts, 2); assert.equal(requests.length, 2);
});

test('relay AbortError, sleep failure and relay-served callback failures retain their exact identities', async () => {
  const abort = { name: 'AbortError' }, sleepError = new Error('sleep marker'), callbackError = new Error('callback marker');
  const primaryFailure = async () => { throw new TypeError('synthetic network failure'); };
  await assert.rejects(requestHistory('http://127.0.0.1:1/candles/x/y', isCandlePage, {
    fetchImpl: primaryFailure, relay: true, relayFetchImpl: async () => { throw abort; } }), (e) => e === abort);
  await assert.rejects(requestHistory('public-explicit-url', isCandlePage, { fetchImpl: primaryFailure,
    retryDelaysMs: [0], sleep: async () => { throw sleepError; } }), (e) => e === sleepError);
  await assert.rejects(requestHistory('http://127.0.0.1:1/candles/x/y', isCandlePage, { fetchImpl: primaryFailure,
    relay: true, relayFetchImpl: async () => new Response(JSON.stringify(page())), onRelayServed: () => { throw callbackError; } }), (e) => e === callbackError);
});

test('the source retains non-Error fallback text, invalid-URL relay suppression and exact-false ok semantics', async () => {
  await assert.rejects(requestHistory('/relative-explicit-test', isCandlePage, { relay: true,
    fetchImpl: async () => { throw 'public-non-Error-marker'; },
    relayFetchImpl: async () => { throw Error('invalid absolute URL must not select a relay'); } }),
  (e) => e instanceof CandleHistoryFetchError && e.status === null && e.fallback === null && e.message === 'candle history fetch failed');
  const body = page();
  assert.strictEqual(await requestHistory('explicit-capability-test', isCandlePage, {
    fetchImpl: async () => ({ ok: 0, status: 500, json: async () => body }) }), body);
});

test('normalization errors after a valid HTTP envelope do not trigger a transport retry or error-class wrapping', async (t) => {
  const { client, requests } = await local(t, (_request, response) => json(response, line([null])));
  await assert.rejects(client.line({ ...params, res: '1m', count: 2, maxPoints: 2, retryDelaysMs: [1] }), TypeError);
  assert.equal(requests.length, 1);
});

test('the recovered candle operation rereads its interval after real HTTP delivery', async (t) => {
  let notify, release;
  const started = new Promise((resolve) => { notify = resolve; });
  const { base, requests } = await local(t, (_request, response) => { release = () => json(response, page([bar(1)])); notify(); });
  const input = { ...params, baseUrl: base, fetchImpl: fetch, relayFetchImpl: fetch };
  const pending = readCandleHistory(input);
  await started; input.interval = '5m'; release();
  assert.deepEqual(await pending, { candles: [], hasOlder: false, servedRes: '1m', intervalMismatch: true, supplyUsed: undefined });
  assert.match(requests[0].url, /res=1m&count=300/);
});

test('the explicit host facade rejects missing capabilities without selecting a production destination', () => {
  assert.throws(() => createCandleHistoryClient({}), /explicit baseUrl/);
  assert.throws(() => createCandleHistoryClient({ baseUrl: 'http://127.0.0.1:1', fetchImpl: fetch }), /relayFetchImpl/);
});

const proof = await buildHistoryProof();
async function isolated(t) {
  const root = await mkdtemp(path.join(os.tmpdir(), 'history public source '));
  t.after(() => rm(root, { recursive: true, force: true }));
  for (const relative of new Set(['evidence/web/manifest.json', 'recovered/modules.json', PROOF,
    `${DIRECTORY}/client.mjs`, ...proof.factories.map((f) => f.source)])) {
    await mkdir(path.dirname(path.join(root, relative)), { recursive: true });
    await copyFile(path.join(APP_ROOT, relative), path.join(root, relative));
  }
  return root;
}
test('all original provider/decoder/week and incoming-caller contexts authenticate from public raw inputs', async (t) => {
  const root = await isolated(t);
  assert.deepEqual(await verifyHistory(root), proof);
  assert.equal(proof.factories.length, 18); assert.equal(proof.incoming.length, 14);
});
test('implicit retries and zero-price line admission cannot be resealed as the source behavior', async (t) => {
  const root = await isolated(t), file = path.join(root, DIRECTORY, 'client.mjs');
  const original = await readFile(file, 'utf8');
  await writeFile(file, original.replace('retryDelaysMs = []', 'retryDelaysMs = CAPTURED_RETRY_DELAYS'));
  await assert.rejects(buildHistoryProof(root), /actual request default retryDelaysMs/);
  await writeFile(file, original.replace('price > 0', 'price >= 0'));
  await assert.rejects(buildHistoryProof(root), /finite-positive line point/);
});
test('a lost physical caller variant or changed raw capture fails closed', async (t) => {
  const root = await isolated(t), indexFile = path.join(root, 'recovered/modules.json');
  const bytes = await readFile(indexFile, 'utf8'), index = JSON.parse(bytes);
  index.modules = index.modules.filter((m) => !m.sha256.startsWith('b033cbe58c97'));
  await writeFile(indexFile, JSON.stringify(index));
  await assert.rejects(buildHistoryProof(root), /physical variant census 349942/);
  await writeFile(indexFile, bytes);
  const source = path.join(root, proof.factories[0].source);
  await writeFile(source, `${await readFile(source, 'utf8')} `);
  await assert.rejects(verifyHistory(root), /capture authentication failed/);
});
