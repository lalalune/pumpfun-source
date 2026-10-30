// Authored synthetic namespace/clock/renderer inputs, not original providers.
import { createExploreCoinCard, CARD_CONTEXTS, REQUIRED_MODULES } from './client.mjs';

export function createCoinCardFixture({ React, jsx, compiler, context = CARD_CONTEXTS[1] }) {
  const state = { now: 1700000001000, marketCap: 100, quick: false, style: false,
    points: [{ time: 1, price: 2 }, { time: 2, price: 6 }], creator: {}, session: null };
  const calls = { media: [], badge: [], avatars: [], creatorQuery: [], chartQuery: [], queryCommits: [], impression: [], prefetch: [], links: [], click: [], routes: [], quote: [], dynamic: [], relative: [], format: [], intervals: new Map(), timeouts: new Map(), nextToken: 1 };
  const icon = () => jsx.jsx('span', { 'aria-hidden': true, children: 'icon' });
  const modules = new Map(REQUIRED_MODULES.map((id) => [id, Object.freeze({})]));
  const classNames = (...values) => values.filter(Boolean).join(' ');
  modules.set(157633, { cJ: icon, s4: icon, i$: icon });
  modules.set(322315, { D: { HOME_FEED_QUICK_BUY_V2: 'quick' } });
  modules.set(254010, { k: () => state.quick });
  modules.set(584582, { C: (timestamp, options) => { calls.relative.push({ timestamp, options }); return `relative:${timestamp}`; } });
  modules.set(782067, { T: (query) => { calls.creatorQuery.push(query); return { data: state.creator }; } });
  modules.set(7284, { U: classNames });
  modules.set(453706, { default: (loader, options) => { calls.dynamic.push({ loader, options }); return (props) => jsx.jsx('span', { 'data-protected-descriptor': true, children: props.coin.mint }); } });
  modules.set(458310, { default: (props) => {
    calls.links.push(props);
    const { onClick, prefetch, ...native } = props;
    return jsx.jsx('a', { ...native, onClick: async (event) => { event.preventDefault(); await onClick?.(event); } });
  } });
  modules.set(599077, { useRouter: () => ({ push: (url) => calls.routes.push(['push', url]) }) });
  modules.set(667876, { f: ({ mint, chainId }) => jsx.jsx('span', { 'data-token-badge': true, children: `${mint}:${chainId}` }) });
  modules.set(713380, { f: (props) => { calls.badge.push(props); return jsx.jsx('span', { 'data-chain-badge': true }); } });
  modules.set(644350, { f: (props) => { calls.media.push(props); return jsx.jsx('span', { 'data-synthetic-media': true, children: props.coin.symbol }); } });
  modules.set(574472, { F: () => ({ decodedJwt: state.session }) });
  modules.set(170450, { f: () => true });
  modules.set(300157, { y: ({ mint, chainId }) => `${chainId ?? 'solana'}:${mint}` });
  modules.set(642357, { T: () => 'unsupported' });
  modules.set(398902, { f: () => ({ t: (key) => key }) });
  modules.set(745018, { xI: icon, Sg: icon });
  modules.set(369091, { useIpfsPrefix: () => ({ ipfsPrefix: 'synthetic-ipfs' }) });
  modules.set(702067, { f: () => 'synthetic-color' });
  modules.set(529841, { f: ({ timestamp }) => jsx.jsx('span', { 'data-relative-time': true, children: `relative:${timestamp}` }) });
  modules.set(375676, { f: (query) => {
    const points = state.points;
    calls.chartQuery.push(query);
    React.useLayoutEffect(() => { calls.queryCommits.push({ mint: query.coinAddress, points: points.map((point) => ({ ...point })) }); });
    return { data: points };
  } });
  modules.set(850175, { W: (coin) => { calls.prefetch.push(coin); return { prefetch: false, hoverProps: { 'data-prefetch-port': true } }; } });
  modules.set(425890, { f: () => state.style });
  modules.set(235364, { f: () => ({ handleCoinClick: async (...args) => { calls.click.push(['coin', ...args]); } }) });
  modules.set(666863, { f: (mint, impression, meta, source) => { calls.impression.push({ mint, impression, meta, source }); return null; } });
  modules.set(646908, { e: () => false, X: () => false, a: () => false });
  modules.set(662093, { h: () => state.marketCap });
  modules.set(790431, { d: () => 'pump' });
  modules.set(561116, { W: () => false });
  modules.set(595673, { v5: (sort, watchlist) => `${sort}:${watchlist}` });
  modules.set(569526, { y: () => ({ setLastClickImpression: (...args) => calls.click.push(['last', ...args]) }) });
  modules.set(693124, { S: ({ username, onClick }) => jsx.jsx('button', { type: 'button', onClick, children: username }) });
  modules.set(456753, { j: () => ({ logSeenCoins: async () => { calls.click.push(['seen']); } }) });
  modules.set(538459, { A: () => (value) => calls.quote.push(value) });
  class Clock extends Date { static now() { return state.now; } }
  const host = { Date: Clock, window: { open: (...args) => calls.routes.push(['open', ...args]) },
    setInterval: (callback, delay) => { const token = calls.nextToken++; calls.intervals.set(token, { callback, delay }); return token; },
    clearInterval: (token) => calls.intervals.delete(token),
    setTimeout: (callback, delay) => { const token = calls.nextToken++; calls.timeouts.set(token, { callback, delay }); return token; } };
  const Avatar = (props) => { calls.avatars.push(props); return jsx.jsx('span', { 'data-synthetic-avatar': true, children: 'avatar' }); };
  const formatters = { M: (value) => { calls.format.push(value); return `compact:${value}`; } };
  const flow = createExploreCoinCard({ context, React, jsx, compiler, Avatar, formatters, modules,
    loadModule: () => { throw new Error('Protected resource loading excluded'); }, host });
  const coin = { mint: 'A', name: 'synthetic coin', symbol: 'TEST', description: 'synthetic description', creator: 'creator/with space', username: 'original-user',
    chain_id: 'solana', created_timestamp: 1700000000, usd_market_cap: 100, is_currently_live: false, mayhem_state: 'active', mayhem_is_multiplayer: true, is_charity: true };
  const props = { coin, impression: { sourceScreen: 9, sourceElement: 3, itemPosition: 1, rec_id: 'synthetic-rec' },
    isInViewport: true, eagerLoadImage: true, priorityImage: true };
  const tick = (now) => { state.now = now; for (const { callback } of calls.intervals.values()) callback(); };
  return { flow, state, calls, modules, host, Avatar, formatters, props, tick };
}
