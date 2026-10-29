import { normalizeSearchCoins, readSearchCoins } from '../search-session/session.mjs';

// Editable operations from the physical 859960/606706/539335 factory. Names of
// this facade are local. Provider capabilities are mandatory and make no reads
// until the consumer explicitly invokes a returned function.
export const LIVE_LISTING_LIMIT = 24;
export const LIVE_SORTS = { FEATURED: 'featured', MARKET_CAP: 'market_cap', MOST_VIEWERS: 'most_viewers' };
export const LIVE_SORT_FIELDS = { most_viewers: 'livestream_num_participants', market_cap: 'market_cap', featured: 'featured' };
export const LIVE_CARD_COUNTS = { extraSmall: 2, small: 3, large: 4 };
export const mostViewedSectionArguments = (e) => ({ livePageSort: LIVE_SORTS.MOST_VIEWERS, ...e });
export const highestCapSectionArguments = (e) => ({ livePageSort: LIVE_SORTS.MARKET_CAP, ...e });

export const projectLiveCoin = (e) => ({
  id: e.mint,
  mint: e.mint,
  coinCreatedTimestamp: e.created_timestamp ?? null,
  title: e.name ?? e.mint,
  creator: { address: e.creator, username: e.username },
  marketCap: e.usd_market_cap,
  thumbnail: e.thumbnail,
  ipfsThumbnail: e.image_uri ?? '',
  thumbnailUpdatedAt: e.thumbnail_updated_at,
  avatarUri: e.image_uri ?? '',
  isLive: e.is_currently_live,
  playlistUrl: e.playlist_url_low || e.playlist_url || void 0,
  viewerCount: e.num_participants,
  linkUrl: `/coin/${e.mint}`,
  symbol: e.symbol,
  coin: e,
});

// This is the actual playlist-map read arrow with its service URL, HTTP and
// schema capabilities injected. No default fetch, destination or parser exists.
export function createPlaylistMapRead({ getServiceOrigin, fetchResponse, playlistSchema }) {
  return async (e) => {
    let t = new URL('/livestream/playlist-map', getServiceOrigin()),
      a = await fetchResponse(t.toString(), {
        method: 'POST',
        body: JSON.stringify({ mints: e }),
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        cache: 'no-store',
      });
    if (!a.ok) throw Error(`Error fetching playlist map: ${a.statusText}`);
    let i = await a.json();
    return playlistSchema.parse(i).map;
  };
}

export function createLiveListing({ getContractClient, readPlaylistMap, logger, errorContext }) {
  const fetchCoins = async ({
    limit: e = LIVE_LISTING_LIMIT,
    offset: t,
    includeNsfw: a,
    ipfsPrefix: i,
    livePageSort: l,
  }) => {
    let r = e;
    l === LIVE_SORTS.MOST_VIEWERS &&
      (e !== LIVE_LISTING_LIMIT && logger.warn(
        'Non-default limit set for MOST_VIEWERS coins query. It will be ignored and a custom default limit will be used.',
      ), (r = l === LIVE_SORTS.MOST_VIEWERS ? 100 : e));
    let s = await getContractClient()('GET /coins/search-unrestricted', {
      query: { limit: r, offset: t, includeNsfw: a, order: 'desc', currentlyLive: true, sort: LIVE_SORT_FIELDS[l] },
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      next: { revalidate: 10 },
      hooks: { afterResponse: [(e, t, a) => {
        if (!a.ok) throw Error(`Error fetching coins: ${a.statusText}`);
      }] },
    });
    return normalizeSearchCoins(readSearchCoins(s), i);
  };
  const fetchSection = async (e) => {
    let t = (await fetchCoins(e)).map(projectLiveCoin),
      a = t.reduce((e, t) => (t.playlistUrl || e.push(t.mint), e), []);
    if (0 === a.length) return t;
    let i = {};
    try {
      i = await readPlaylistMap(a);
    } catch (e) {
      logger.error(errorContext(e));
    }
    return 0 === Object.keys(i).length ? t : t.map((e) => i[e.mint]
      ? { ...e, playlistUrl: i[e.mint].playlistUrlLow || i[e.mint].playlistUrl ||
        i[e.mint].playlistUrlHigh || i[e.mint].vodPlaylistUrl || void 0 }
      : e);
  };
  return { fetchCoins, fetchSection };
}

export function nextLivePage(e, t, a) {
  if (e && 0 !== e.length) return a + e.length;
}

export function selectLivePages(e) {
  let t = new Set();
  return { ...e, pages: e.pages.map((e) => e.filter((e) => {
    let a = e.playlistUrl || e.thumbnail;
    if (a) {
      if (t.has(a)) return false;
      t.add(a);
    }
    return true;
  })) };
}

export function livePageIdentity(e) { return e; }

// Current provider/render inputs are supplied by the caller. These are data and
// arrows for a query consumer, not a replacement for useInfiniteQuery or a cache.
export function liveSectionQuery({ limit: m, livePageSort: u, initialData: x, staleTime: p },
  { includeNsfw: b, ipfsPrefix: y, fetchSection: j }) {
  const v = void 0 === m ? LIVE_LISTING_LIMIT : m;
  const g = void 0 === p ? 10000 : p;
  const queryFn = async (e) => {
    let { pageParam: t } = e;
    return j({ offset: t, limit: v, livePageSort: u, includeNsfw: b, ipfsPrefix: y });
  };
  return { queryKey: ['live-section-coins', u, b, v, y], queryFn,
    initialPageParam: 0, getNextPageParam: nextLivePage, select: selectLivePages,
    initialData: x ? { pages: [x], pageParams: [0] } : void 0, staleTime: g };
}

export function liveSectionResult(result) {
  return { data: result.data?.pages.flatMap(livePageIdentity) ?? [],
    isLoading: result.isLoading, fetchNextPage: result.fetchNextPage,
    hasNextPage: result.hasNextPage, isFetchingNextPage: result.isFetchingNextPage };
}

export function createLiveSectionNearEnd({ hasNextPage: x, isFetchingNextPage: p, fetchNextPage: h }) {
  return () => { x && !p && h(); };
}

export function createLiveSectionCompletion({ isLoading: f, onSectionComplete: s, sectionId: e }) {
  return () => { f || s?.(e); };
}

// Card rendering/viewport observation remains external. This describes exactly
// the 310766 section's conditional handoff for an already-delivered query result.
export function liveSectionView({ data: u, isLoading: f, hasNextPage: x },
  { onShowAll: r, isExpanded: n = false, eager: d = false } = {}) {
  if (f) return { body: 'loading' };
  if (0 === u.length) return { body: 'empty' };
  const g = r && (u.length > LIVE_CARD_COUNTS.large || x);
  return { body: 'section', showAll: g, showBack: !g && n,
    livestreams: u, scrollContainerClassName: n ? 'flex-wrap' : 'flex-nowrap',
    useViewportIntersection: n, eager: d };
}
