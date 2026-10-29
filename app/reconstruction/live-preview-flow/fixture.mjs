// Synthetic qualification host, never an application route or media player.
import * as React from 'react';
import * as jsx from 'react/jsx-runtime';
import { c } from 'react/compiler-runtime';
import { createRoot } from 'react-dom/client';
import { createLivePreviewFlow } from './components.mjs';
import { normalizeSearchUri } from '../search-session/session.mjs';

const element = React.createElement, events = [], context = React.createContext(null);
let setStreams, mounted = 0;
const players = new Map(), imageCallbacks = new Map();
const values = ['A', 'B', 'C'].map((id) => ({ mint: `fixture-${id}`, title: `Fixture ${id}`,
  creator: { address: `creator-${id}` }, symbol: id, marketCap: 1, thumbnail: `fixture-updated-${id}`,
  ipfsThumbnail: `ipfs://fixture-original-${id}`, thumbnailUpdatedAt: 1, avatarUri: '', isLive: true,
  playlistUrl: `fixture-playlist-${id}`, viewerCount: 1 }));
function SyntheticPlayer(props) {
  const mint = React.useContext(context);
  players.set(mint, props);
  React.useEffect(() => { mounted++; events.push(['player-mount', mint]);
    return () => { mounted--; players.delete(mint); events.push(['player-unmount', mint]); }; }, [mint]);
  return element('section', { 'data-testid': 'synthetic-player', 'data-mint': mint,
    'data-muted': String(props.muted), 'data-loading': String(props.isLoading),
    'data-playlist': props.playlistUrl ?? '(undefined)' },
  element('button', { type: 'button', onClick: props.onIsReady }, 'Synthetic ready'),
  element('button', { type: 'button', onClick: props.onAutoPlayFail }, 'Synthetic autoplay failure'));
}
function SyntheticImage(props) {
  imageCallbacks.set(props.alt, props);
  return element('button', { type: 'button', 'data-testid': 'synthetic-image',
    'data-src': props.src, 'data-image-class': props.className, onClick: props.onLoad }, `Synthetic image ${props.alt}`);
}
function SyntheticLink({ href, onClick, children, prefetch, ...rest }) {
  return element('a', { ...rest, href: '#synthetic-navigation-withheld', 'data-href': href,
    onClick(event) { events.push(['link', href, event.defaultPrevented]); onClick?.(event); event.preventDefault(); } }, children);
}
const empty = () => null;
const icon = (name) => () => element('span', { 'data-testid': `icon-${name}` }, name);
const stableHover = { prefetch: false, hoverProps: {} };
const modules = {
  157633: { QA: icon('muted'), e: icon('unmuted'), S: icon('previous'), v$: icon('next') },
  426091: { c: (...args) => args.flat(Infinity).filter(Boolean).join(' '), r: normalizeSearchUri },
  398902: { f: () => ({ t: (key, values) => values?.index ? `Slide ${values.index} of ${values.total}` : key }) },
  375670: { f: empty },
  325320: { t: ({ mint, children, ...flags }) => { events.push(['provider-flags', mint, flags]);
    return element(context.Provider, { value: mint }, children); } },
  845785: { w: { WEB_PREVIEW_PLAYER: 'synthetic-preview' } },
  855376: { f: { PUMP_WEB: 'synthetic-web' } },
  405048: { V: ({ children }) => children },
  453706: { default: (loader, options) => { events.push(['dynamic-options', options]);
    const Lazy = React.lazy(async () => ({ default: await loader() }));
    return (props) => element(React.Suspense, { fallback: element('span', {}, 'Synthetic lazy wait') }, element(Lazy, props)); } },
  425444: { default: SyntheticImage },
  369091: { useIpfsPrefix: () => ({ ipfsPrefix: 'https://fixture.invalid/ipfs/' }) },
  292686: { Ae: { LIVESTREAM: 'synthetic-live' }, k9: { LIVESTREAM_VIDEO_FEED: 'synthetic-feed' } },
  458310: { default: SyntheticLink },
  146695: { $: (address) => `/fixture-profile/${address}` },
  705313: { f: empty }, 928196: { f: empty }, 277167: { f: empty },
  564861: { f: ({ text }) => element('span', {}, text) },
  556120: { f: empty }, // Account/trade CTA is deliberately not implemented.
  898337: { f: empty }, 454430: { f: empty },
  850175: { e: (mint) => ({ mint }), W: () => stableHover },
  595673: { iV: (value) => events.push(['analytics-port', value]) },
};
const flow = createLivePreviewFlow({ React, jsx, compiler: { c }, modules,
  loadPreview: async (id) => { events.push(['loader-port', id]); return { LivestreamPreviewPlayer: SyntheticPlayer }; },
  dom: { document, ResizeObserver, MutationObserver } });
const originalScroll = Element.prototype.scrollTo;
Element.prototype.scrollTo = function (options) { events.push(['scrollTo', options]); return originalScroll.call(this, options); };
let revision = 0, committed = -1;
function Host() {
  const [streams, update] = React.useState(values); setStreams = (next) => { revision++; update(next); };
  React.useEffect(() => { committed = revision; });
  return element(flow.VideoMuteProvider, {}, element(flow.HeroCarousel, { livestreams: streams }));
}
const root = createRoot(document.getElementById('root'));
root.render(element(Host));
window.harness = {
  observe: () => ({ revision, committed, mounted, events: [...events],
    geometry: [...document.querySelectorAll('.snap-x')].map((e)=>({scrollLeft:e.scrollLeft,clientWidth:e.clientWidth,scrollWidth:e.scrollWidth})),
    selected: [...document.querySelectorAll('[data-testid="live-hero-slot"]')].map((e)=>e.dataset.selected),
    players: [...players].map(([mint, p]) =>
    ({ mint, playlistUrl: p.playlistUrl, muted: p.muted, isLoading: p.isLoading, playOnHover: p.playOnHover,
      playWhenVisible: p.playWhenVisible, loaderType: p.loaderType })) }),
  clear: () => { events.length = 0; },
  replace: (ids) => setStreams(ids.map((id) => ({ ...values.find((v) => v.symbol === id) }))),
  override: () => setStreams(values.map((v, index) => index === 1 ? { ...v, isSelected: true } : v)),
  imageError: (title) => imageCallbacks.get(title).onError(),
  autoplayFailure: () => { const player=players.values().next().value; if(!player)throw Error('no synthetic player');player.onAutoPlayFail(); },
  unmount: () => root.unmount(),
};
