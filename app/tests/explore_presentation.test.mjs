import assert from 'node:assert/strict';
import test from 'node:test';
import { createRequire } from 'node:module';
import { mkdtemp, mkdir, readFile, writeFile, rm, copyFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { createExploreFixture } from '../reconstruction/explore-presentation/fixture.mjs';
import { createExplorePresentation, REQUIRED_MODULES, LAZY_MODULES } from '../reconstruction/explore-presentation/client.mjs';
import { verify, recover, APP_ROOT } from '../reconstruction/explore-presentation/recover.mjs';

const require = createRequire(new URL('../packages/frontend/package.json', import.meta.url));
const React = require('react');
const jsx = require('react/jsx-runtime');
const compiler = require('react/compiler-runtime');
const { renderToStaticMarkup } = require('react-dom/server');
const make = () => createExploreFixture({ React, jsx, compiler, window: {}, document: {}, IntersectionObserver: class {} });
const render = (Component, props) => renderToStaticMarkup(jsx.jsx(Component, props));

test('complete authenticated owner and actual MAIN Flight context regenerate', async () => {
  const proof = await verify();
  assert.equal(proof.factory.sha256, '3417e48c11cff94d2efdafcfae6018010e97d1003122b734cd3e019f280a1134');
  assert.equal(proof.origin.exportName, 'HomePageContainer');
  assert.equal(proof.origin.elementRow, '109');
  assert.equal(proof.imports.length, 83);
  assert.equal(proof.lazy.length, 9);
  assert.ok(proof.operations.some(({ label }) => label === 'complete HomePageContainer owner'));
});

test('missing initialized namespace and host inputs fail before executing an owner', () => {
  const f = make();
  assert.equal(REQUIRED_MODULES.length, 84);
  assert.equal(LAZY_MODULES.length, 9);
  f.modules.delete(12692);
  assert.throws(() => createExplorePresentation({ modules: f.modules, loadModule() {}, host: f.host }), /12692/);
  f.modules.set(12692, {});
  const { fetch, ...host } = f.host;
  assert.throws(() => createExplorePresentation({ modules: f.modules, loadModule() {}, host }), /fetch/);
});

test('page window retains thresholds, ellipsis and no invented integer validation', () => {
  const { pageNumbers } = make().flow;
  assert.deepEqual(pageNumbers(1, false), [1]);
  assert.deepEqual(pageNumbers(2, true), [1, 2, 3, 'ellipsis']);
  assert.deepEqual(pageNumbers(3, false), [1, 2, 3]);
  assert.deepEqual(pageNumbers(8, true), [1, 'ellipsis', 7, 8, 9, 'ellipsis']);
  assert.deepEqual(pageNumbers(4.5, false), [1, 'ellipsis', 3.5, 4.5]);
});

test('grid deduplicates first mint, keeps card metadata and distinct visibility/read ports', () => {
  const f = make();
  const html = render(f.flow.CoinGrid, { ...f.base, loading: false });
  assert.match(html, /first A/); assert.doesNotMatch(html, /duplicate A/);
  assert.deepEqual(f.calls.visibility.at(-1), { mints: ['A', 'B'], enabled: true });
  assert.deepEqual(f.calls.impressions.at(-1).coins.map((coin) => coin.mint), ['A']);
  assert.deepEqual(f.calls.polling.at(-1), { mints: ['A'], options: { shouldFetch: true, enablePolling: true, pollingInterval: 17000 } });
  assert.equal(f.calls.cards[0].isBookmarked, true);
  assert.equal(f.calls.cards[0].priorityImage, true);
  assert.equal(f.calls.cards[1].priorityImage, false);
  assert.equal(f.calls.cards[0].impression.marketCap, 12.35);
  assert.equal(f.calls.cards[0].shouldAnimate, true);
});

test('unseen rows use explicit skeleton port; empty and loading branches remain distinct', () => {
  const f = make(); f.state.seen = ['B'];
  const html = render(f.flow.CoinGrid, { ...f.base, loading: false });
  assert.match(html, /data-synthetic-card-skeleton/);
  assert.deepEqual(f.calls.cards.map(({ coin }) => coin.mint), ['B']);
  const empty = render(f.flow.CoinGrid, { ...f.base, coins: [], loading: false });
  assert.match(empty, /web.coin_list.empty_title/);
  const loading = render(f.flow.CoinGrid, { ...f.base, coins: [], loading: true });
  assert.equal((loading.match(/data-synthetic-card-skeleton/g) ?? []).length, 6);
  assert.doesNotMatch(loading, /web.coin_list.empty_title/);
});

test('full presentation forwards canonical page href while next-page override beats row count', () => {
  const f = make();
  const html = render(f.flow.PresentationFrame, f.base);
  assert.match(html, /href="\/explore\?q=kept&amp;page=3"/);
  assert.match(html, /href="\/explore\?q=kept"/);
  const noNext = render(f.flow.LinkPagination, { offset: 0, LIMIT: 2, items: [1, 2], hasNextPage: false, getHref: (offset) => `/p/${offset}`, setOffset() {}, loading: false });
  assert.doesNotMatch(noNext, /rel="next"/);
  const unknownNext = render(f.flow.LinkPagination, { offset: 0, LIMIT: 2, items: [1, 2], hasNextPage: null, getHref: (offset) => `/p/${offset}`, setOffset() {}, loading: false });
  assert.match(unknownNext, /rel="next"/);
});

test('error is social-terminal empty/no-search only; actual frame retains read-only table handoff', () => {
  const f = make(); f.state.variant = 'social-terminal';
  const error = render(f.flow.PresentationFrame, { ...f.base, coins: [], feedError: true });
  assert.match(error, /home-feed-load-failed/);
  const search = render(f.flow.PresentationFrame, { ...f.base, coins: [], feedError: true, searchTerm: 'A' });
  assert.doesNotMatch(search, /home-feed-load-failed/);
  f.state.layout = 'table';
  const table = render(f.flow.PresentationFrame, { ...f.base, appliedFiltersKey: 'canonical-key' });
  assert.match(table, /data-synthetic-table/);
  assert.match(table, /canonical-key/);
});

test('held-over time takes precedence over partial and malformed time keeps source dash', () => {
  const f = make();
  const held = render(f.flow.PartialStatus, { partial: true, heldOver: true, generatedAt: 'bad-date' });
  assert.match(held, /calls_held_over_notice/); assert.match(held, /–/);
  assert.doesNotMatch(held, /calls_partial_notice/);
  const neither = render(f.flow.PartialStatus, { partial: false, heldOver: false, generatedAt: null });
  assert.doesNotMatch(neither, /calls_held_over_notice|calls_partial_notice/);
});

test('live-row admission preserves layout/order/offset/NSFW/trade-identity gates', () => {
  const f = make(), coin = { mint: 'A', name: 'Alpha', symbol: 'AA', nsfw: false };
  const options = { includeNsfw: false, bumpOrderSort: true, creationTimeSort: false, offset: 0, order: 'desc', showAnimations: true, searchTerm: '', lastProcessedTrade: { current: null } };
  assert.equal(f.flow.admitLiveCoin(coin, options), true);
  assert.equal(f.flow.admitLiveCoin(coin, { ...options, lastProcessedTrade: { current: coin } }), false);
  assert.equal(f.flow.admitLiveCoin(coin, { ...options, showAnimations: false }), false);
  assert.equal(f.flow.admitLiveCoin(coin, { ...options, showAnimations: false, layout: 'table' }), true);
  assert.equal(f.flow.admitLiveCoin(coin, { ...options, offset: 1 }), false);
  assert.equal(f.flow.admitLiveCoin({ ...coin, nsfw: true }, options), false);
  assert.equal(f.flow.admitLiveCoin(coin, { ...options, searchTerm: 'alpha' }), false);
});

test('portable public-input export needs no formatted factories/private snapshot', async () => {
  const temp = await mkdtemp(path.join(tmpdir(), 'explore-owner-'));
  try {
    const proof = await verify();
    const paths = ['evidence/web/manifest.json', 'recovered/modules.json', proof.factory.source, proof.origin.capture.source];
    for (const source of paths) { const target = path.join(temp, source); await mkdir(path.dirname(target), { recursive: true }); await copyFile(path.join(APP_ROOT, source), target); }
    const result = await recover(temp);
    assert.equal(result.proof.moduleSha256, proof.moduleSha256);
    const rawPath = path.join(temp, proof.factory.source);
    const bytes = await readFile(rawPath); bytes[bytes.length - 1] ^= 1; await writeFile(rawPath, bytes);
    await assert.rejects(recover(temp), /capture authentication failed/);
  } finally { await rm(temp, { recursive: true }); }
});
