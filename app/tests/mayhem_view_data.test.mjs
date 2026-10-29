import assert from 'node:assert/strict';
import { test } from 'node:test';
import { mkdtemp, mkdir, copyFile, readFile, writeFile, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { createMayhemUpdate, createMayhemEvent, deriveMayhemView, previousMayhemPage, nextMayhemPage } from '../reconstruction/mayhem-view-data/view.mjs';
import { APP_ROOT, DIRECTORY, PROOF, verifyMayhemView, buildMayhemViewProof } from '../reconstruction/mayhem-view-data/verify.mjs';

function store(byMint = {}) {
  let root = { byMint, marker: 'other state' };
  const update = createMayhemUpdate((operation) => {
    const result = operation(root);
    if (result !== root) root = { ...root, ...result };
  });
  return { update, event: createMayhemEvent(update), get: () => root };
}
const coin = (mint, fields = {}) => Object.freeze({ mint, ...fields });
const input = (changes = {}) => ({ data: [], hydratedCoins: [], marketActivity: {}, byMint: {},
  coinState: { coins: {} }, sort: 'lastTraded', pageIndex: 0, isLoading: false, isError: false, paused: false, ...changes });

test('partial live events merge without validating modes, retaining exact root identity on a no-op', () => {
  const state = store();
  state.event({ mint: 'a', state: 'active', mode: 'manual' });
  const before = state.get();
  state.event({ mint: 'a', state: null, mode: undefined });
  assert.strictEqual(state.get(), before);
  state.event({ mint: 'a', state: '', mode: 'unknown-live-mode' });
  assert.deepEqual(state.get().byMint.a, { state: '', mode: 'unknown-live-mode' });
  assert.equal(state.get().marker, 'other state');
  assert.deepEqual(before.byMint.a, { state: 'active', mode: 'manual' });
  const changed = state.get();
  state.event(null); state.event({ mint: '' }); state.event({ mint: 0 });
  assert.strictEqual(state.get(), changed);
  state.event({ mint: 'b' });
  assert.ok(Object.hasOwn(state.get().byMint, 'b'));
  assert.deepEqual(state.get().byMint.b, { state: undefined, mode: undefined });
});

test('the 500-entry cap follows enumeration, changed-key reinsertion and no-op identity, not a generic LRU', () => {
  const byMint = Object.fromEntries(Array.from({ length: 500 }, (_, i) => [`m${i}`, { state: 'active', mode: 'auto' }]));
  const state = store(byMint);
  state.update('m0', { state: 'paused' });
  assert.equal(Object.keys(state.get().byMint).at(-1), 'm0');
  const before = state.get();
  state.update('m1', { state: 'active' });
  assert.strictEqual(state.get(), before);
  state.update('new', { state: 'active' });
  assert.equal(Object.keys(state.get().byMint).length, 500);
  assert.ok(!Object.hasOwn(state.get().byMint, 'm1'));
  assert.ok(Object.hasOwn(state.get().byMint, 'm0'));
  const integers = store(byMint);
  integers.update('1', { state: 'paused' });
  // Integer-looking property names enumerate first: the just-added key is evicted.
  assert.ok(!Object.hasOwn(integers.get().byMint, '1'));
  assert.equal(Object.keys(integers.get().byMint).length, 500);
  assert.equal(Object.keys(byMint).length, 500);
});

test('byMint copying preserves the source for-in behavior for enumerable inherited keys', () => {
  const byMint = Object.create({ inherited: { state: 'paused' } });
  byMint.a = { state: 'active' };
  const state = store(byMint);
  state.update('b', { mode: 'manual' });
  assert.ok(Object.hasOwn(state.get().byMint, 'inherited'));
  assert.strictEqual(state.get().byMint.inherited, byMint.inherited);
});

test('served coins drive both provider plans and row identity; hydration supplies only valid last modes', () => {
  const a = coin('a', { usd_market_cap: 7, mayhem_state: 'active' }), b = coin('b');
  const data = Object.freeze([a, b]);
  const view = deriveMayhemView(input({ data, hydratedCoins: [
    { mint: 'a', mayhem: { mode: 'manual' }, usd_market_cap: 999999 },
    { mint: 'a', mayhem: { mode: 'auto' } },
    { mint: 'a', mayhem: { mode: 'invalid' } },
    { mint: 'b', mayhem: { mode: null } }, { mint: '', mayhem: { mode: 'manual' } },
  ] }));
  assert.strictEqual(view.coins, data); assert.strictEqual(view.ordered, data);
  assert.strictEqual(view.rows[0].coin, a); assert.strictEqual(view.rows[1].coin, b);
  assert.deepEqual(view.hydration, { mints: ['a', 'b'], limit: 2, includeNsfw: true, disabled: false });
  assert.strictEqual(view.hydration.mints, view.mints);
  assert.deepEqual([...view.modes], [['a', 'auto']]);
  assert.equal(view.rows[0].mode, 'auto'); assert.equal(view.rows[1].mode, undefined);
});

test('live mode/state and cap display override fallbacks independently, including null cap and zero volume', () => {
  const data = [coin('a', { mayhem_state: 'paused', usd_market_cap: 100 }), coin('b', { usd_market_cap: 50 }), coin('c')];
  const activity = { a: { '24h': { volumeUSD: 0, priceChangePercent: -1 } } };
  const view = deriveMayhemView(input({ data, marketActivity: activity, hydratedCoins: [
    { mint: 'a', mayhem: { mode: 'manual' } }, { mint: 'b', mayhem: { mode: 'auto' } },
  ], byMint: { a: { state: null, mode: 'unvalidated-live' }, b: { state: '', mode: '' } },
  coinState: { coins: { a: { usdMarketCap: null }, b: { usdMarketCap: 0 } } } }));
  assert.equal(view.rows[0].state, 'paused'); assert.equal(view.rows[1].state, '');
  assert.equal(view.rows[0].mode, 'unvalidated-live'); assert.equal(view.rows[1].mode, '');
  assert.equal(view.rows[0].modeTranslationKey, 'web.mayhem.agent_mode_auto');
  assert.equal(view.rows[1].modeTranslationKey, undefined);
  assert.equal(view.rows[0].marketCap, null); assert.equal(view.rows[1].marketCap, 0);
  assert.equal(view.rows[2].marketCap, 0); assert.equal(view.rows[0].marketCapPositive, false);
  assert.strictEqual(view.rows[0].change, activity.a['24h']);
  assert.equal(view.rows[0].volumePresent, true); assert.equal(view.rows[0].volumeUSD, 0);
  assert.equal(view.rows[1].volumePresent, false);
  assert.equal(view.rows[0].trendClass, 'text-loss'); assert.equal(view.rows[1].trendClass, 'text-gain');
  assert.equal(view.rows[0].telemetryMarketCap, 100);
});

test('volume sorting joins 24h activity while display-only caps do not change base-cap or newest order', () => {
  const a = coin('a', { usd_market_cap: 10, created_timestamp: 20 });
  const b = coin('b', { usd_market_cap: 20, created_timestamp: 10 });
  const c = coin('c', { usd_market_cap: 20, created_timestamp: 10 });
  const data = Object.freeze([a, b, c]);
  const values = { data, marketActivity: { c: { '24h': { volumeUSD: 3 } }, a: { '24h': { volumeUSD: null } } },
    coinState: { coins: { a: { usdMarketCap: 1000000 } } } };
  assert.deepEqual(deriveMayhemView(input({ ...values, sort: 'volume' })).ordered, [c, a, b]);
  assert.deepEqual(deriveMayhemView(input({ ...values, sort: 'mcap' })).ordered, [b, c, a]);
  assert.deepEqual(deriveMayhemView(input({ ...values, sort: 'newest' })).ordered, [a, b, c]);
  assert.strictEqual(deriveMayhemView(input({ ...values, sort: 'lastTraded' })).ordered, data);
  assert.strictEqual(deriveMayhemView(input({ ...values, sort: 'unrecognized' })).ordered, data);
  assert.deepEqual(data, [a, b, c]);
});

test('ten-row pages clamp a shrinking result and retain absolute ranks and visible subscription inputs', () => {
  const data = Array.from({ length: 15 }, (_, i) => coin(`m${i}`));
  const view = deriveMayhemView(input({ data, pageIndex: 4 }));
  assert.equal(view.pageCount, 2); assert.equal(view.currentPage, 1); assert.equal(view.pageIndexCorrection, 1);
  assert.deepEqual(view.visibleMints, ['m10', 'm11', 'm12', 'm13', 'm14']);
  assert.deepEqual(view.rows.map((r) => r.rank), [11, 12, 13, 14, 15]);
  assert.equal(view.subscribeVisible, true);
  assert.deepEqual(view.pagination, { visible: true, previousDisabled: false, nextDisabled: true });
  assert.equal(previousMayhemPage(0), 0); assert.equal(previousMayhemPage(view.currentPage), 0);
  assert.equal(nextMayhemPage(view.pageCount, view.currentPage), 1);
  const shrink = deriveMayhemView(input({ data: data.slice(0, 3), pageIndex: view.currentPage }));
  assert.equal(shrink.pageIndexCorrection, 0); assert.equal(shrink.currentPage, 0);
  assert.deepEqual(shrink.rows.map((r) => r.rank), [1, 2, 3]);
  assert.equal(shrink.pagination.visible, false);
});

test('loading/error/empty precedence does not invent provider cancellation or discard a visible-mint handoff', () => {
  const data = Array.from({ length: 11 }, (_, i) => coin(`m${i}`));
  const loading = deriveMayhemView(input({ data, isLoading: true, isError: true, paused: true }));
  assert.equal(loading.body, 'loading'); assert.deepEqual(loading.rows, []);
  assert.equal(loading.visibleMints.length, 10); assert.equal(loading.subscribeVisible, true);
  assert.equal(loading.pagination.visible, false); assert.equal(loading.refetchInterval, false);
  const error = deriveMayhemView(input({ data, isError: true }));
  assert.equal(error.body, 'error'); assert.deepEqual(error.rows, []); assert.equal(error.refetchInterval, 10000);
  for (const data of [null, undefined, []]) {
    const empty = deriveMayhemView(input({ data, pageIndex: 2 }));
    assert.equal(empty.body, 'empty'); assert.equal(empty.pageCount, 1); assert.equal(empty.pageIndexCorrection, 0);
    assert.deepEqual(empty.hydration, { mints: [], limit: 1, includeNsfw: true, disabled: true });
    assert.equal(empty.subscribeVisible, false); assert.deepEqual(empty.rows, []);
  }
});

const proof = await buildMayhemViewProof();
async function isolated(t) {
  const root = await mkdtemp(path.join(os.tmpdir(), 'mayhem view source '));
  t.after(() => rm(root, { recursive: true, force: true }));
  const files = new Set(['evidence/web/manifest.json', 'recovered/modules.json', PROOF,
    `${DIRECTORY}/view.mjs`, ...proof.factories.map((f) => f.source)]);
  for (const file of files) {
    await mkdir(path.dirname(path.join(root, file)), { recursive: true });
    await copyFile(path.join(APP_ROOT, file), path.join(root, file));
  }
  return root;
}
test('all physical provider contexts and callbacks reauthenticate from raw captures in a path with spaces', async (t) => {
  const root = await isolated(t);
  assert.deepEqual(await verifyMayhemView(root), proof);
  assert.equal(proof.factories.filter((f) => f.id === 849812).length, 4);
  assert.equal(proof.factories.filter((f) => f.id === 609252).length, 9);
  assert.equal(proof.limits.mountedUI, false); assert.equal(proof.limits.nativeCompatibility, false);
});
test('a resealed editable callback mutation cannot pass the original AST comparison', async (t) => {
  const root = await isolated(t), file = path.join(root, DIRECTORY, 'view.mjs');
  await writeFile(file, (await readFile(file, 'utf8')).replace('r.length > 500', 'r.length > 499'));
  await assert.rejects(buildMayhemViewProof(root), /complete store update callback/);
});
test('a resealed live-cap fallback mutation cannot erase the original null-versus-undefined distinction', async (t) => {
  const root = await isolated(t), file = path.join(root, DIRECTORY, 'view.mjs');
  await writeFile(file, (await readFile(file, 'utf8')).replace('void 0 !== liveMarketCap', 'null != liveMarketCap'));
  await assert.rejects(buildMayhemViewProof(root), /undefined-only fallback/);
});
test('missing a physical activity variant and corrupting a raw capture each fail closed', async (t) => {
  const root = await isolated(t), indexFile = path.join(root, 'recovered/modules.json');
  const inventory = await readFile(indexFile, 'utf8'), parsed = JSON.parse(inventory);
  parsed.modules = parsed.modules.filter((m) => !m.sha256.startsWith('8e943b080637'));
  await writeFile(indexFile, JSON.stringify(parsed));
  await assert.rejects(buildMayhemViewProof(root), /physical variant census 849812/);
  await writeFile(indexFile, inventory);
  const file = path.join(root, proof.factories[0].source);
  await writeFile(file, `${await readFile(file, 'utf8')} `);
  await assert.rejects(verifyMayhemView(root), /capture authentication failed/);
});
