import assert from 'node:assert/strict';
import { test } from 'node:test';
import { mkdtemp, mkdir, copyFile, readFile, writeFile, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { createLiveListing, createPlaylistMapRead, projectLiveCoin, nextLivePage,
  selectLivePages, liveSectionQuery, liveSectionResult, createLiveSectionNearEnd,
  createLiveSectionCompletion, liveSectionView, mostViewedSectionArguments, highestCapSectionArguments } from '../reconstruction/live-listing-data/listing.mjs';
import { APP_ROOT, DIRECTORY, PROOF, buildLiveListingProof, verifyLiveListing } from '../reconstruction/live-listing-data/verify.mjs';

const options = { livePageSort: 'market_cap', ipfsPrefix: 'https://images.example.test/ipfs/', includeNsfw: false };
const coin = (mint, fields = {}) => ({ mint, creator: 'creator', name: `coin-${mint}`, ...fields });
function listing(pages, overrides = {}) {
  const calls = [], warnings = [], errors = [], playlists = [];
  const api = createLiveListing({
    getContractClient: () => async (route, init) => {
      calls.push({ route, init });
      const data = pages.shift();
      if (data instanceof Error) throw data;
      await init.hooks.afterResponse[0](route, init, { ok: true });
      return data;
    },
    readPlaylistMap: async (mints) => { playlists.push(mints); return {}; },
    logger: { warn: (e) => warnings.push(e), error: (e) => errors.push(e) },
    errorContext: (e) => ({ original: e }), ...overrides,
  });
  return { ...api, calls, warnings, errors, playlists };
}

test('complete query→accepted normalizer→projection flow retains served order and source request policy', async () => {
  const first = coin('b', { created_at: 7, recommendation_id: 'rec', name: '', playlist_url: 'main', thumbnail: 'thumb' });
  const second = coin('a', { playlist_url_low: 'low', playlist_url: 'other', is_currently_live: false });
  const service = listing([[first, second]]);
  const rows = await service.fetchSection({ ...options, offset: 3 });
  assert.deepEqual(rows.map((e) => e.mint), ['b', 'a']);
  assert.strictEqual(rows[0].coin, first);
  assert.equal(first.created_timestamp, 7); assert.equal(first.rec_id, 'rec');
  assert.equal(rows[0].title, ''); assert.equal(rows[1].playlistUrl, 'low');
  assert.equal(rows[1].isLive, false); // currentlyLive is a request input, not a new local filter.
  assert.equal(service.playlists.length, 0);
  const { route, init } = service.calls[0];
  assert.equal(route, 'GET /coins/search-unrestricted');
  assert.deepEqual(init.query, { limit: 24, offset: 3, includeNsfw: false, order: 'desc', currentlyLive: true, sort: 'market_cap' });
  assert.equal(init.credentials, 'include');
  assert.deepEqual(init.headers, { 'Content-Type': 'application/json' });
  assert.deepEqual(init.next, { revalidate: 10 });
  assert.equal(Object.hasOwn(init, 'signal'), false);
});

test('most-viewers limit override and warning preserve undefined-only defaults and raw sort lookup', async () => {
  const service = listing([[], [], [], []]);
  await service.fetchCoins({ ...options, livePageSort: 'most_viewers' });
  await service.fetchCoins({ ...options, livePageSort: 'most_viewers', limit: 100 });
  await service.fetchCoins({ ...options, limit: null, livePageSort: 'unknown' });
  await service.fetchCoins({ ...options, limit: 0, livePageSort: 'featured' });
  assert.deepEqual(service.calls.map((e) => e.init.query.limit), [100, 100, null, 0]);
  assert.deepEqual(service.calls.map((e) => e.init.query.sort), ['livestream_num_participants', 'livestream_num_participants', undefined, 'featured']);
  assert.equal(service.warnings.length, 1);
  assert.match(service.warnings[0], /Non-default limit/);
});

test('missing-playlist mints retain duplicates and use exact map precedence without dropping cards', async () => {
  const a = coin('a'), b = coin('b'), c = coin('c'), present = coin('present', { playlist_url: 'kept' });
  const requests = [];
  const service = listing([[a, b, a, c, present]], { readPlaylistMap: async (mints) => {
    requests.push(mints);
    return { a: { playlistUrlLow: '', playlistUrl: 'standard', playlistUrlHigh: 'high' }, b: { vodPlaylistUrl: 'vod' }, c: {} };
  } });
  const rows = await service.fetchSection(options);
  assert.deepEqual(requests, [['a', 'b', 'a', 'c']]);
  assert.deepEqual(rows.map((e) => e.playlistUrl), ['standard', 'vod', 'standard', undefined, 'kept']);
  assert.strictEqual(rows[0].coin, a); assert.strictEqual(rows.at(-1).coin, present);
});

test('playlist-map URL/POST/body/status/JSON/schema order is preserved through explicit ports', async () => {
  const events = [], map = { a: { playlistUrlLow: 'low' } };
  const read = createPlaylistMapRead({
    getServiceOrigin: () => { events.push('origin'); return 'https://service.example.test/base'; },
    fetchResponse: async (url, init) => { events.push({ url, init }); return { ok: true, json: async () => { events.push('json'); return { raw: true }; } }; },
    playlistSchema: { parse(value) { assert.deepEqual(value, { raw: true }); events.push('schema'); return { map }; } },
  });
  assert.strictEqual(await read(['a', 'a']), map);
  assert.deepEqual(events, ['origin', { url: 'https://service.example.test/livestream/playlist-map', init: {
    method: 'POST', body: '{"mints":["a","a"]}', credentials: 'include', headers: { 'Content-Type': 'application/json' }, cache: 'no-store',
  } }, 'json', 'schema']);
  const bad = createPlaylistMapRead({ getServiceOrigin: () => 'https://service.example.test', fetchResponse: async () => ({ ok: false, statusText: 'Unavailable', json: () => assert.fail('no failed-response JSON') }), playlistSchema: { parse: () => assert.fail('no failed-response parse') } });
  await assert.rejects(bad([]), { message: 'Error fetching playlist map: Unavailable' });
});

test('playlist errors are best effort while base query, abort and malformed response errors propagate', async () => {
  const failure = new Error('playlist parse'), logs = [];
  const service = listing([[coin('a')]], { readPlaylistMap: async () => { throw failure; },
    logger: { warn() {}, error: (value) => logs.push(value) }, errorContext: (e) => ({ same: e }) });
  assert.equal((await service.fetchSection(options))[0].playlistUrl, undefined);
  assert.strictEqual(logs[0].same, failure);
  const abort = Object.assign(new Error('aborted'), { name: 'AbortError' });
  const base = listing([abort, null]);
  await assert.rejects(base.fetchSection(options), (e) => e === abort);
  await assert.rejects(base.fetchSection(options), TypeError);
  assert.equal(base.playlists.length, 0);
  const hook = listing([[]]); await hook.fetchCoins(options);
  assert.throws(() => hook.calls[0].init.hooks.afterResponse[0](null, null, { ok: false, statusText: 'Forbidden' }), { message: 'Error fetching coins: Forbidden' });
});

test('projection preserves nullish and truthy distinctions without validating media, live or metrics', () => {
  const raw = coin('m', { name: null, created_timestamp: 0, username: '', image_uri: null,
    playlist_url_low: '', playlist_url: '', num_participants: null, usd_market_cap: -4, is_currently_live: null });
  const card = projectLiveCoin(raw);
  assert.equal(card.title, 'm'); assert.equal(card.coinCreatedTimestamp, 0);
  assert.equal(card.creator.username, ''); assert.equal(card.avatarUri, '');
  assert.equal(card.playlistUrl, undefined); assert.equal(card.viewerCount, null);
  assert.equal(card.marketCap, -4); assert.equal(card.isLive, null); assert.strictEqual(card.coin, raw);
});

test('pagination deduplicates first media key across all pages, not mint; raw page length advances the offset', () => {
  const a = { mint: 'same', playlistUrl: 'one' }, b = { mint: 'other', thumbnail: 'one' };
  const c = { mint: 'same', playlistUrl: 'two' }, blank = { mint: 'blank', thumbnail: '' };
  const raw = { pages: [[a, b, blank], [c, a, blank]], pageParams: [0, 3], extra: 'retained' };
  const selected = selectLivePages(raw);
  assert.deepEqual(selected.pages, [[a, blank], [c, blank]]);
  assert.strictEqual(selected.pages[0][0], a); assert.strictEqual(selected.pageParams, raw.pageParams);
  assert.equal(selected.extra, 'retained'); assert.equal(raw.pages[0].length, 3);
  assert.equal(nextLivePage(raw.pages[1], raw.pages, 3), 6);
  assert.equal(nextLivePage([], raw.pages, 6), undefined);
  assert.equal(nextLivePage(undefined, raw.pages, 6), undefined);
});

test('query descriptor→page query→selected result retains keys, seed truthiness, flags and capabilities', async () => {
  const calls = [], seed = [], fetchSection = async (args) => { calls.push(args); return []; };
  const config = liveSectionQuery({ livePageSort: 'most_viewers', initialData: seed }, { includeNsfw: true, ipfsPrefix: 'prefix', fetchSection });
  assert.deepEqual(config.queryKey, ['live-section-coins', 'most_viewers', true, 24, 'prefix']);
  assert.deepEqual(config.initialData, { pages: [seed], pageParams: [0] });
  assert.strictEqual(config.initialData.pages[0], seed); assert.equal(config.initialPageParam, 0); assert.equal(config.staleTime, 10000);
  await config.queryFn({ pageParam: 9 });
  assert.deepEqual(calls, [{ offset: 9, limit: 24, livePageSort: 'most_viewers', includeNsfw: true, ipfsPrefix: 'prefix' }]);
  const nulls = liveSectionQuery({ limit: null, staleTime: null, initialData: null }, { fetchSection });
  assert.equal(nulls.queryKey[3], null); assert.equal(nulls.staleTime, null); assert.equal(nulls.initialData, undefined);
  const fetchNextPage = () => 'external';
  const delivered = liveSectionResult({ data: { pages: [[1], [2]] }, isLoading: false, hasNextPage: true, isFetchingNextPage: false, fetchNextPage });
  assert.deepEqual(delivered.data, [1, 2]); assert.strictEqual(delivered.fetchNextPage, fetchNextPage); assert.equal(delivered.hasNextPage, true);
  assert.deepEqual(liveSectionResult({}).data, []);
});

test('actual section arguments→two query pages→dedup→flatten→consumer retains raw offset and caller precedence', async () => {
  const a = coin('a', { playlist_url: 'shared' }), b = coin('b', { thumbnail: 'shared' });
  const c = coin('c', { playlist_url: 'unique' });
  const service = listing([[a, b], [c, a]]);
  const descriptor = liveSectionQuery(mostViewedSectionArguments({ limit: 24 }),
    { ...options, fetchSection: service.fetchSection });
  const first = await descriptor.queryFn({ pageParam: descriptor.initialPageParam });
  const next = descriptor.getNextPageParam(first, [first], 0);
  const second = await descriptor.queryFn({ pageParam: next });
  const selected = descriptor.select({ pages: [first, second], pageParams: [0, next] });
  const delivered = liveSectionResult({ data: selected, isLoading: false, hasNextPage: true, isFetchingNextPage: false });
  const view = liveSectionView(delivered, { onShowAll() {} });
  assert.deepEqual(service.calls.map((e) => e.init.query.offset), [0, 2]);
  assert.deepEqual(service.calls.map((e) => e.init.query.limit), [100, 100]);
  assert.deepEqual(delivered.data.map((e) => e.mint), ['a', 'c']);
  assert.strictEqual(view.livestreams, delivered.data); assert.equal(view.showAll, true);
  assert.equal(highestCapSectionArguments({}).livePageSort, 'market_cap');
  assert.equal(mostViewedSectionArguments({ livePageSort: 'featured' }).livePageSort, 'featured');
});

test('section handoff preserves near-end gating, completion, loading/empty and show-all/back conditions', () => {
  let fetches = 0, completions = [];
  for (const [hasNextPage, isFetchingNextPage] of [[true, false], [false, false], [true, true]]) {
    assert.equal(createLiveSectionNearEnd({ hasNextPage, isFetchingNextPage, fetchNextPage: () => ++fetches })(), undefined);
  }
  assert.equal(fetches, 1);
  for (const isLoading of [true, false]) createLiveSectionCompletion({ isLoading, sectionId: 'highest-market-cap', onSectionComplete: (e) => completions.push(e) })();
  assert.deepEqual(completions, ['highest-market-cap']);
  assert.deepEqual(liveSectionView({ data: [], isLoading: true }, {}), { body: 'loading' });
  assert.deepEqual(liveSectionView({ data: [], isLoading: false }, {}), { body: 'empty' });
  const data = [1, 2, 3, 4];
  const expanded = liveSectionView({ data, isLoading: false, hasNextPage: false }, { onShowAll() {}, isExpanded: true, eager: true });
  assert.equal(expanded.showAll, false); assert.equal(expanded.showBack, true); assert.equal(expanded.scrollContainerClassName, 'flex-wrap'); assert.strictEqual(expanded.livestreams, data);
  assert.equal(liveSectionView({ data, hasNextPage: true }, { onShowAll() {} }).showAll, true);
  assert.equal(liveSectionView({ data: [...data, 5] }, {}).showAll, undefined);
});

const proof = await buildLiveListingProof();
async function isolated(t) {
  const root = await mkdtemp(path.join(os.tmpdir(), 'live listing proof '));
  t.after(() => rm(root, { recursive: true, force: true }));
  await mkdir(path.join(root, DIRECTORY), { recursive: true });
  // Use public source/corpus inputs through ordinary file copies, preserving
  // immutable originals. Every needed raw dependency is explicitly enumerated.
  const files = new Set(['evidence/web/manifest.json', 'recovered/modules.json', PROOF, `${DIRECTORY}/listing.mjs`,
    ...proof.factories.map((f) => f.source), 'reconstruction/search-session/session.mjs',
    'reconstruction/search-session/PROVENANCE.json', ...Object.keys(proof.dependencyHashes)]);
  const shared = JSON.parse(await readFile(path.join(APP_ROOT, 'reconstruction/search-session/PROVENANCE.json'), 'utf8'));
  const sources = (value) => {
    if (!value || typeof value !== 'object') return;
    if (typeof value.source === 'string' && value.source.startsWith('evidence/web/objects/')) files.add(value.source);
    for (const child of Object.values(value)) sources(child);
  };
  sources(shared);
  for (const file of files) {
    await mkdir(path.dirname(path.join(root, file)), { recursive: true });
    await copyFile(path.join(APP_ROOT, file), path.join(root, file));
  }
  return root;
}
test('source proof reauthenticates the public input closure in a path with spaces without evaluating captures', async (t) => {
  const actual = await verifyLiveListing(await isolated(t));
  assert.equal(actual.adapterSha256, proof.adapterSha256);
  assert.ok(actual.comparisons.length >= 20);
  assert.equal(actual.limits.activeRuntimeWinner, false); assert.equal(actual.limits.networkAcquisition, false);
});
test('source proof rejects a semantic edit even when its adapter hash could be resealed', async (t) => {
  const root = await isolated(t);
  const file = path.join(root, DIRECTORY, 'listing.mjs');
  await writeFile(file, (await readFile(path.join(APP_ROOT, DIRECTORY, 'listing.mjs'), 'utf8')).replace('a + e.length', 'a + 24'));
  await assert.rejects(buildLiveListingProof(root), /complete nextLivePage/);
});
