import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { once } from 'node:events';
import { createRequire } from 'node:module';
import { mkdtemp, mkdir, readFile, writeFile, copyFile, link, symlink, rm } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { promisify } from 'node:util';
import { execFile } from 'node:child_process';
import {
  ACTIVITY_CONFIG, isSolanaActivityAddress, isEvmActivityAddress,
  normalizeMarketActivity, splitActivityBatches, mergeActivityBatches,
  createMarketActivityModule,
} from '../reconstruction/market-activity/client.mjs';
import { APP_ROOT, DIRECTORY, verify } from '../reconstruction/market-activity/verify.mjs';

const A = 'A'.repeat(32), B = 'B'.repeat(32), C = 'C'.repeat(32), EVM = '0x' + 'a'.repeat(40);
const addresses = Array.from('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz', (x) => 'A'.repeat(31) + x);
const alphabet = addresses.slice(0, 51);
const defer = () => { let resolve; const promise = new Promise((r) => { resolve = r; }); return { promise, resolve }; };
const payload = (mint = A, volume = '12') => ({ [mint]: { '24h': { volumeUSD: volume, buyVolumeUSD: '2', sellVolumeUSD: '3', numTxs: 8 } } });
function setup(overrides = {}) {
  const calls = { fetch: [], warnings: [], queries: [], mutations: [], mutate: [], cache: [], invalidate: [] };
  const memo = Array(31).fill(Symbol.for('react.memo_cache_sentinel'));
  let states = [], combined;
  const client = {
    setQueryData: (...args) => { calls.cache.push(args); },
    invalidateQueries: (...args) => { calls.invalidate.push(args); },
  };
  const mutate = (batch) => { calls.mutate.push(batch); };
  const ports = {
    getBaseUrl: () => 'http://127.0.0.1:1/v1',
    fetchActivity: (...args) => { calls.fetch.push(args); throw Error('No test transport configured'); },
    logger: { warn: (...args) => { calls.warnings.push(args); } },
    useMemoCache: (count) => { assert.equal(count, 31); return memo; },
    useQueryClient: () => client,
    useQueries: (options) => { calls.queries.push(options); return combined ?? options.combine(states); },
    useMutation: (options) => { calls.mutations.push(options); return { mutate }; },
    ...overrides,
  };
  return { calls, ports, client, module: createMarketActivityModule(ports),
    states: (value) => { states = value; }, combined: (value) => { combined = value; } };
}
async function local(t, handler) {
  const requests = [];
  const server = createServer((req, res) => {
    (async () => {
      let text = ''; for await (const chunk of req) text += chunk;
      const request = { method: req.method, url: req.url, headers: req.headers, text,
        body: text ? JSON.parse(text) : null };
      requests.push(request); await handler(request, res, requests.length);
    })().catch((e) => { res.writeHead(500).end(JSON.stringify({ testHandlerError: e.message })); });
  });
  server.listen(0, '127.0.0.1'); await once(server, 'listening');
  t.after(async () => { server.closeAllConnections(); await new Promise((r) => server.close(r)); });
  const origin = 'http://127.0.0.1:' + server.address().port;
  return { origin, requests, fetchActivity: (url, init) => {
    assert.equal(new URL(url).origin, origin, 'only this synthetic loopback server may be contacted');
    return fetch(url, init);
  } };
}

test('source authenticates four full hook frames, six helper variants and complete used dependencies', async () => {
  const proof = await verify();
  assert.equal(proof.frames.length, 4);
  assert.equal(proof.factories.length, 16);
  assert.equal(proof.comparisons.length, 46);
  assert.equal(proof.factories.filter((p) => p.id === 680930 || p.ids?.includes(680930)).length, 6);
  assert.match(proof.ports.fetchActivity, /telemetry.*not recovered/);
});

test('address admission retains trimmed Solana originals, strict EVM and pre-catch type failures', async () => {
  const h = setup();
  assert.equal(isSolanaActivityAddress(' ' + A + ' '), true);
  assert.equal(isSolanaActivityAddress('0'.repeat(32)), false);
  assert.equal(isSolanaActivityAddress('A'.repeat(31)), false);
  assert.equal(isSolanaActivityAddress('A'.repeat(45)), false);
  assert.equal(isEvmActivityAddress(EVM), true);
  assert.equal(isEvmActivityAddress(' ' + EVM), false);
  assert.equal(isEvmActivityAddress(EVM.replace('0x', '0X')), false);
  assert.equal(h.module.isActivityAddress(' ' + A), true);
  assert.throws(() => h.module.isActivityAddress(null), TypeError);
  await assert.rejects(h.module.readMarketActivity([A, null]), TypeError);
  assert.equal(h.calls.fetch.length, 0); assert.equal(h.calls.warnings.length, 0);
  assert.deepEqual(await h.module.readMarketActivity(null), {});
  assert.deepEqual(await h.module.readMarketActivity(['not-an-address']), {});
});

test('response normalization closes four windows and only the three volume fields', () => {
  const extra = { retained: true };
  const raw = { [A]: { '5m': { volumeUSD: 0, buyVolumeUSD: ' 1e12 ', sellVolumeUSD: '0x10', priceChangePercent: 'unvalidated', extra },
    '1h': { volumeUSD: -1, buyVolumeUSD: Infinity, sellVolumeUSD: ' ' },
    '6h': false, '24h': { volumeUSD: '1000000000001', buyVolumeUSD: null } },
    [B]: null };
  const out = normalizeMarketActivity(raw);
  assert.deepEqual(out[A]['5m'], { volumeUSD: 0, buyVolumeUSD: 1e12, sellVolumeUSD: 16, priceChangePercent: 'unvalidated', extra });
  assert.deepEqual(out[A]['1h'], { volumeUSD: null, buyVolumeUSD: null, sellVolumeUSD: null });
  assert.equal(out[A]['6h'], null);
  assert.deepEqual(out[A]['24h'], { volumeUSD: null, buyVolumeUSD: null, sellVolumeUSD: null });
  assert.deepEqual(out[B], { '5m': null, '1h': null, '6h': null, '24h': null });
  assert.notStrictEqual(out[A]['5m'], raw[A]['5m']); assert.strictEqual(out[A]['5m'].extra, extra);
  assert.equal(raw[A]['5m'].buyVolumeUSD, ' 1e12 ');
  assert.deepEqual(normalizeMarketActivity(undefined), {});
  assert.deepEqual(normalizeMarketActivity('invalid'), {});
  assert.deepEqual(normalizeMarketActivity([]), {});
});

test('dedup/sort/chunk and delivered-order merge retain exact values without case folding', () => {
  assert.deepEqual(splitActivityBatches([B, A, A, null, '', EVM], 2), [[EVM, A], [B]]);
  assert.deepEqual(splitActivityBatches(null), []);
  assert.deepEqual(splitActivityBatches(alphabet).map((x) => x.length), [50, 1]);
  const first = { [A]: { old: true }, [B]: 0 }, last = { [A]: null };
  assert.deepEqual(mergeActivityBatches([undefined, first, false, last]), { [A]: null, [B]: 0 });
  assert.deepEqual(first[A], { old: true });
  assert.deepEqual(mergeActivityBatches(null), {});
});

test('real loopback POST preserves duplicates/whitespace/option body order and returns normalized data', async (t) => {
  const wire = await local(t, (request, res) => { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(payload())); });
  const h = setup({ getBaseUrl: () => wire.origin + '/v1', fetchActivity: wire.fetchActivity });
  const out = await h.module.readMarketActivity([B, A, A, ' ' + A + ' ', EVM, ' ' + EVM, 'invalid'], { intervals: [], metrics: ['custom'] });
  assert.equal(wire.requests.length, 1);
  const request = wire.requests[0];
  assert.equal(request.method, 'POST'); assert.equal(request.url, '/v1/coins/market-activity/batch');
  assert.equal(request.headers['content-type'], 'application/json');
  assert.equal(request.headers.cookie, undefined); assert.equal(request.headers.authorization, undefined);
  assert.deepEqual(request.body, { addresses: [B, A, A, ' ' + A + ' ', EVM], intervals: [], metrics: ['custom'] });
  assert.deepEqual(Object.keys(JSON.parse(request.text)), ['addresses', 'intervals', 'metrics']);
  assert.equal(out[A]['24h'].volumeUSD, 12); assert.equal(out[A]['24h'].numTxs, 8);
  assert.equal(h.calls.warnings.length, 0);
});

test('real HTTP failures and malformed JSON are swallowed once without retries', async (t) => {
  const wire = await local(t, (request, res, n) => {
    if (n === 1) res.writeHead(503).end('unavailable'); else res.writeHead(200).end('{');
  });
  const h = setup({ getBaseUrl: () => wire.origin, fetchActivity: wire.fetchActivity });
  assert.deepEqual(await h.module.readMarketActivity([A]), {});
  assert.deepEqual(await h.module.readMarketActivity([A]), {});
  assert.equal(wire.requests.length, 2); assert.equal(h.calls.warnings.length, 2);
  assert.equal(h.calls.warnings[0][0], 'Error fetching market activity');
  assert.match(h.calls.warnings[0][1].error.message, /503/);
  assert.equal(h.calls.warnings[0][1].mintCount, 1);
  assert.equal(h.calls.warnings[1][1].error.name, 'SyntaxError');
});

test('real aborted fetch becomes empty activity, but option getters and throwing loggers escape', async (t) => {
  const wire = await local(t, (request, res) => res.end('{}'));
  const h = setup({ getBaseUrl: () => wire.origin, fetchActivity: wire.fetchActivity });
  const controller = new AbortController(); controller.abort();
  assert.deepEqual(await h.module.readMarketActivity([A], { signal: controller.signal }), {});
  assert.equal(h.calls.warnings[0][1].error.name, 'AbortError'); assert.equal(wire.requests.length, 0);
  const error = Error('synthetic option getter');
  await assert.rejects(h.module.readMarketActivity([A], { get intervals() { throw error; } }), (e) => e === error);
  const loggerError = Error('synthetic logger failure');
  const broken = setup({ logger: { warn() { throw loggerError; } } });
  await assert.rejects(broken.module.readMarketActivity([A]), (e) => e === loggerError);
});

test('normalization errors are inside the reader catch and direct signal/init fields are exact', async () => {
  const bad = { [A]: { '24h': { get volumeUSD() { throw Error('synthetic normalizer getter'); } } } };
  const signal = new AbortController().signal;
  const calls = [];
  const h = setup({ fetchActivity: async (url, init) => { calls.push([url, init]); return { ok: true, json: async () => bad }; } });
  assert.deepEqual(await h.module.readMarketActivity([A], { signal }), {});
  assert.equal(h.calls.warnings[0][1].error.message, 'synthetic normalizer getter');
  assert.strictEqual(calls[0][1].signal, signal);
  assert.deepEqual(Object.keys(calls[0][1]), ['method', 'headers', 'body', 'signal']);
  assert.deepEqual(JSON.parse(calls[0][1].body).intervals, ACTIVITY_CONFIG.INTERVALS);
});

test('full query frame preserves batch keys/defaults/options/combine and omits query-context signal', async () => {
  const observed = [];
  const h = setup({ fetchActivity: async (url, init) => { observed.push(init); return { ok: true, json: async () => payload() }; } });
  const error = Error('first truthy query error');
  h.states([{ data: { [A]: 'old', [B]: 2 }, isPending: false, error: null },
    { data: { [A]: 'new' }, isPending: true, error }, { data: undefined, isPending: false, error: Error('later') }]);
  const result = h.module.useMarketActivity([...alphabet].reverse().concat(alphabet[0], 'invalid'));
  const input = h.calls.queries[0];
  assert.equal(input.queries.length, 2);
  assert.deepEqual(input.queries[0].queryKey, ['marketActivity', [...alphabet].sort().slice(0, 50).join(',')]);
  assert.deepEqual(result.marketActivity, { [A]: 'new', [B]: 2 });
  assert.equal(result.loading, true); assert.strictEqual(result.error, error);
  const q = input.queries[0];
  assert.equal(q.enabled, true); assert.equal(q.staleTime, 300000); assert.equal(q.gcTime, 600000);
  for (const name of ['refetchOnMount', 'refetchOnWindowFocus', 'refetchOnReconnect', 'retry', 'refetchInterval']) assert.equal(q[name], false);
  await q.queryFn({ signal: new AbortController().signal });
  assert.equal(observed[0].signal, undefined);
  const second = setup(); second.module.useMarketActivity([A], { shouldFetch: null, enablePolling: true, pollingInterval: 0 });
  assert.equal(second.calls.queries[0].queries[0].enabled, null);
  assert.equal(second.calls.queries[0].queries[0].refetchInterval, 0);
  const third = setup(); third.module.useMarketActivity([A], { enablePolling: true });
  assert.equal(third.calls.queries[0].queries[0].refetchInterval, 30000);
  const empty = setup(); const value = empty.module.useMarketActivity([]);
  assert.deepEqual(empty.calls.queries[0].queries, []); assert.deepEqual(value.marketActivity, {});
  assert.equal(value.loading, false); assert.equal(value.error, undefined);
});

test('memo frame retains same-array stale batches and callback identity without inventing query scheduling', () => {
  const h = setup(); h.combined({ data: [], pending: false, error: undefined });
  const input = [A], first = h.module.useMarketActivity(input), firstQueries = h.calls.queries[0];
  input.push(B);
  const second = h.module.useMarketActivity(input);
  assert.strictEqual(second, first); assert.strictEqual(h.calls.queries[1], firstQueries);
  assert.equal(firstQueries.queries[0].queryKey[1], A);
  const third = h.module.useMarketActivity([...input]);
  assert.notStrictEqual(third, first);
  assert.equal(h.calls.queries[2].queries[0].queryKey[1], [A, B].join(','));
  assert.throws(() => h.module.useMarketActivity([A], null), TypeError);
});

test('manual refresh selects whole matching batches once and invalidates all current keys without awaiting', () => {
  const h = setup(), state = h.module.useMarketActivity(alphabet), queries = h.calls.queries[0].queries;
  assert.equal(state.refetchMints([alphabet[0], alphabet[0], alphabet[50], C]), undefined);
  assert.equal(h.calls.mutate.length, 2);
  assert.equal(h.calls.mutate[0].join(','), queries[0].queryKey[1]);
  assert.equal(h.calls.mutate[1].join(','), queries[1].queryKey[1]);
  state.refetchMints([]); assert.equal(h.calls.mutate.length, 2);
  assert.equal(state.invalidateCache(), undefined);
  assert.deepEqual(h.calls.invalidate.map(([v]) => v.queryKey), queries.map((q) => q.queryKey));
});

test('real HTTP mutation reader resolves before cache write; failed reader caches its actual empty delivery', async (t) => {
  const reached = defer(), release = defer();
  const wire = await local(t, async (request, res, n) => {
    if (n === 1) { reached.resolve(); await release.promise; res.end(JSON.stringify(payload())); }
    else res.writeHead(503).end('unavailable');
  });
  const h = setup({ getBaseUrl: () => wire.origin, fetchActivity: wire.fetchActivity });
  h.module.useMarketActivity([A]); const mutation = h.calls.mutations[0].mutationFn;
  const pending = mutation([A, A]); await reached.promise;
  assert.equal(h.calls.cache.length, 0); release.resolve(); const result = await pending;
  assert.equal(h.calls.cache.length, 1); assert.deepEqual(h.calls.cache[0][0], ['marketActivity', [A, A].join(',')]);
  assert.strictEqual(h.calls.cache[0][1], result); assert.equal(result[A]['24h'].volumeUSD, 12);
  const empty = await mutation([A]); assert.deepEqual(empty, {}); assert.strictEqual(h.calls.cache[1][1], empty);
  assert.equal(h.calls.warnings.length, 1); assert.equal(wire.requests.length, 2);
  const error = Error('synthetic cache write failure'); h.client.setQueryData = () => { throw error; };
  await assert.rejects(mutation(['invalid']), (e) => e === error); assert.equal(wire.requests.length, 2);
});

test('installed real React/compiler runtime admits the complete hook frame with explicit query capabilities', () => {
  const require = createRequire(new URL('../packages/frontend/package.json', import.meta.url));
  const React = require('react'), { renderToString } = require('react-dom/server'), compiler = require('react/compiler-runtime');
  const h = setup({ useMemoCache: compiler.c }); let result;
  function Host() { result = h.module.useMarketActivity([A]); return React.createElement('output', null, JSON.stringify(result.marketActivity)); }
  assert.equal(renderToString(React.createElement(Host)), '<output>{}</output>');
  assert.equal(result.loading, false); assert.equal(h.calls.queries[0].queries.length, 1);
  assert.equal(h.calls.fetch.length, 0);
});

test('construction has no implicit destination/fetch/query/compiler/logging capability', () => {
  const h = setup();
  for (const name of ['getBaseUrl', 'fetchActivity', 'useMemoCache', 'useQueryClient', 'useQueries', 'useMutation'])
    assert.throws(() => createMarketActivityModule({ ...h.ports, [name]: undefined }), /Explicit activity capability/);
  assert.throws(() => createMarketActivityModule({ ...h.ports, logger: {} }), /logger.warn/);
});

test('public-input CLI works in a path with spaces and rejects changed module, omitted variant and corrupt raw input', async (t) => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'activity public inputs '));
  t.after(() => rm(root, { recursive: true, force: true }));
  const provenance = JSON.parse(await readFile(path.join(APP_ROOT, DIRECTORY, 'PROVENANCE.json'), 'utf8'));
  async function copy(name, immutable = false) {
    const target = path.join(root, name); await mkdir(path.dirname(target), { recursive: true });
    if (immutable) { try { await link(path.join(APP_ROOT, name), target); return; } catch (e) { if (e.code !== 'EXDEV') throw e; } }
    await copyFile(path.join(APP_ROOT, name), target);
  }
  for (const name of ['evidence/web/manifest.json', 'recovered/modules.json', DIRECTORY + '/client.mjs', DIRECTORY + '/PROVENANCE.json',
    DIRECTORY + '/verify.mjs', 'scripts/original-contracts/source.mjs', 'scripts/verify-search-session.mjs']) await copy(name);
  const rawSources = [...new Set(provenance.factories.map((f) => f.source))];
  for (const name of rawSources) await copy(name, true);
  await symlink(path.join(APP_ROOT, 'node_modules'), path.join(root, 'node_modules'));
  const command = promisify(execFile);
  const result = await command(process.execPath, [path.join(root, DIRECTORY, 'verify.mjs'), '--check'], { cwd: root });
  assert.match(result.stdout, /PASS complete market-activity/);
  const clientPath = path.join(root, DIRECTORY, 'client.mjs'), original = await readFile(clientPath, 'utf8');
  assert.ok(original.includes('t > 1e12'));
  await writeFile(clientPath, original.replace('t > 1e12', 't >= 1e12'));
  await assert.rejects(verify(root), /module differs/); await writeFile(clientPath, original);
  const indexPath = path.join(root, 'recovered/modules.json'), index = await readFile(indexPath, 'utf8'), modified = JSON.parse(index);
  modified.modules.splice(modified.modules.findIndex((m) => m.ids.includes(849812)), 1);
  await writeFile(indexPath, JSON.stringify(modified)); await assert.rejects(verify(root), /physical variants/); await writeFile(indexPath, index);
  const source = rawSources[0], to = path.join(root, source), bytes = await readFile(to);
  await rm(to); await writeFile(to, Buffer.concat([bytes, Buffer.from(' ')]));
  await assert.rejects(verify(root), (e) => e.message === `capture authentication failed: ${source}`);
});
