// Authored finite proof infrastructure. None of these providers, cards,
// animation primitives or policies reconstruct their original implementations.
import { createExplorePresentation, REQUIRED_MODULES } from './client.mjs';

export function createExploreFixture({ React, jsx, compiler, window, document, IntersectionObserver, Date: Clock = Date }) {
  const calls = { cards: [], visibility: [], impressions: [], polling: [], hover: [], pages: [], retry: [], lazy: [], telemetry: [], timers: new Set(), observed: new Set() };
  const state = { variant: 'ordinary', layout: 'grid', feed: 'terminal', seen: ['A', 'B'], visible: ['A'], search: 'q=kept&page=2', allowRail: false };
  const modules = new Map(REQUIRED_MODULES.map((id) => [id, Object.freeze({})]));
  const wrap = (tag) => ({ children, className }) => jsx.jsx(tag, { className, children });
  const icon = () => jsx.jsx('span', { 'aria-hidden': true, children: '›' });
  const t = (key, values) => values ? `${key}:${JSON.stringify(values)}` : key;
  const classNames = (...values) => values.filter(Boolean).join(' ');
  const card = (props) => {
    calls.cards.push(props);
    return jsx.jsx('article', {
      'data-card': props.coin.mint,
      'data-name': props.coin.name,
      'data-viewport': String(props.isInViewport),
      'data-priority': String(props.priorityImage),
      children: props.coin.name,
    });
  };
  const motionDiv = ({ children, ref, id }) => jsx.jsx('div', { ref, id, children });
  const syntheticTable = (props) => jsx.jsx('output', { 'data-synthetic-table': true, children: JSON.stringify({ mints: props.coinListProps.coins.map((coin) => coin.mint), filtersKey: props.filtersKey }) });
  const dynamic = (loader, options) => {
    calls.lazy.push({ loader, options });
    return syntheticTable;
  };
  modules.set(732486, jsx);
  modules.set(445242, compiler);
  modules.set(352386, React);
  modules.set(453706, { default: dynamic });
  modules.set(398902, { f: () => ({ t, i18n: { language: 'en' } }) });
  modules.set(599077, { usePathname: () => '/explore', useSearchParams: () => new URLSearchParams(state.search) });
  modules.set(205761, { f: wrap('section') });
  modules.set(415203, { f: wrap('section') });
  modules.set(39548, { m: { div: motionDiv } });
  modules.set(871999, { f: card });
  modules.set(493367, { W: 6 });
  modules.set(48485, { f: (coins, enabled) => calls.impressions.push({ coins, enabled }) });
  modules.set(201629, { f: (mints, options) => calls.polling.push({ mints, options }) });
  modules.set(54136, { f: (options) => {
    calls.visibility.push(options);
    return { visibleMints: state.visible, seenMints: state.seen,
      observe: (element) => { calls.observed.add(element.id); return () => calls.observed.delete(element.id); } };
  } });
  modules.set(300157, { y: ({ mint, chainId }) => `${chainId ?? 'solana'}:${mint}` });
  modules.set(646908, { e: (coin) => coin.family === 'one', X: (coin) => coin.family === 'two', a: (coin) => coin.family === 'three' });
  modules.set(595673, { v5: (sort, watchlist) => `${sort}:${watchlist}` });
  modules.set(680930, { t: { POLLING_INTERVAL: 17000 } });
  modules.set(773755, { f: () => jsx.jsx('span', { 'data-synthetic-card-skeleton': true, children: 'Loading' }) });
  modules.set(148003, { f: wrap('span') });
  modules.set(890088, { r: (locale, options) => new Intl.DateTimeFormat(locale, options) });
  modules.set(592209, { v: (language) => language });
  modules.set(786147, { f: (translate, key) => translate(key) });
  modules.set(671722, { V: () => 'movers', M: { movers: { labelKey: 'movers' } } });
  modules.set(745018, { S: icon, kK: icon });
  modules.set(426091, { c: classNames });
  modules.set(583695, { A: (disabled) => disabled ? 'disabled' : 'enabled', B: wrap('nav'), C: wrap('ul'), w: wrap('li'), z: () => jsx.jsx('span', { children: '…' }), $: (active) => active ? 'active' : '' });
  modules.set(458310, { default: (props) => jsx.jsx('a', props) });
  modules.set(751275, { y: () => state.variant });
  modules.set(678700, { N: () => ({ homeFeed: state.feed }), z: { TERMINAL: 'terminal', WATCHLIST: 'watchlist' } });
  modules.set(211502, { e: () => ({ homeLayout: state.layout }), M: { GRID: 'grid', TABLE: 'table' } });
  modules.set(322315, { D: { WEB_PERPS: 'web-perps' } });
  modules.set(254010, { k: () => false });
  modules.set(315706, { f: async () => ({ datadogRum: { setGlobalContextProperty: (...args) => calls.telemetry.push(['set', ...args]), removeGlobalContextProperty: (...args) => calls.telemetry.push(['remove', ...args]) } }) });
  modules.set(294707, { H: () => state.allowRail });
  modules.set(338319, { c: classNames });
  modules.set(940721, { s: 2 });
  modules.set(947427, { p: (sort) => sort });
  modules.set(998515, { L: { DESC: 'desc', ASC: 'asc' } });
  const host = { window, document, Date: Clock, IntersectionObserver,
    setTimeout: (callback, delay) => { const token = setTimeout(() => { calls.timers.delete(token); callback(); }, delay); calls.timers.add(token); return token; },
    clearTimeout: (token) => { calls.timers.delete(token); clearTimeout(token); },
    fetch: () => { throw new Error('Network/provider acquisition excluded from this fixture'); } };
  const flow = createExplorePresentation({ modules, loadModule: () => { throw new Error('Original resource loading excluded'); }, host });
  const base = { coins: [{ mint: 'A', name: 'first A', usd_market_cap: 12.345 }, { mint: 'A', name: 'duplicate A' }, { mint: 'B', name: 'B', family: 'one' }],
    bookmarkedCoins: [], bookmarks: [], bookmarkedCoinMints: ['solana:A'], sort: 'movers', offset: 2, pageSize: 2,
    hasMorePages: true, watchlistOffset: 0, isLoading: false, isWatchlistLoading: false, isWatchlistEmpty: false,
    isUserValid: false, hasActiveFilters: false, searchTerm: '', feedError: false, sourceScreen: 9,
    onAnimationsPause: (value) => calls.hover.push(value), onPageChange: (value) => calls.pages.push(value),
    onRetryFeed: () => calls.retry.push('retry'), lastUpdatedMint: 'A,B' };
  return { flow, modules, host, calls, state, base };
}
