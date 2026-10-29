// Editable pure-data/explicit-query boundary of the captured main-app bounty
// screener. All names and the recomputation facade are local descriptions.
export const BOUNTY_PUBLIC_PHASES = 'OPEN,PENDING_RESOLUTION,CLOSED,IN_DISPUTE_PERIOD';
export const REWARD_MINTS = { SOL: 'So11111111111111111111111111111111111111112' };
export const REWARD_RANGE = { min: 0, max: 10000 };
export const BOUNTY_SORTS = {
  'reward-desc': { sort: 'rewardTotalUsd', order: 'desc' },
  'reward-asc': { sort: 'rewardTotalUsd', order: 'asc' },
  'time-asc': { sort: 'expiresAt', order: 'asc' },
  'submissions-desc': { sort: 'submissionCount', order: 'desc' },
  recent: { sort: 'createdAt', order: 'desc' },
};
export const TIME_LEFT_OPTIONS = [
  { key: 'lt-24h', label: '< 24 hours' }, { key: 'lt-3d', label: '< 3 days' },
  { key: 'lt-7d', label: '< 7 days' }, { key: 'gte-7d', label: '7+ days' },
];

export const clampBountyQuery = (e) => null == e || 0 === e.length || e.length <= 256 ? e : e.slice(0, 256);
export const allowBountySort = (e, t) => t || 'creatorXFollowerCount' !== e ? e : void 0;
export const withoutStatuses = (e) => ({ ...e, statuses: [] });
export const withoutRewardTokens = (e) => ({ ...e, rewardTokens: [] });
export const withoutTimeLeft = (e) => ({ ...e, timeLeft: null });

export function buildBountyFilters({ sortKey: e, filters: t, nearMe: i = null, now: l = Date.now }) {
  let u = {}, d = l(), c = 'time-asc' === e;
  if (i) ((u.sort = 'distance'), (u.order = 'asc'), (u.lat = i.lat), (u.lng = i.lng), (u.radiusKm = i.radiusKm));
  else { let t = BOUNTY_SORTS[e]; t && ((u.sort = t.sort), (u.order = t.order)); }
  (t.q.trim().length > 0 && (u.q = t.q.trim()),
    c || (i && 0 === t.statuses.length) ? (u.phase = 'OPEN')
      : 0 === t.statuses.length ? (u.phase = BOUNTY_PUBLIC_PHASES)
        : 1 === t.statuses.length ? (u.phase = t.statuses[0])
          : t.statuses.length > 1 && (u.phase = t.statuses.join(',')),
    t.rewardTokens.length > 0 && (u.rewardMints = t.rewardTokens.map((e) => REWARD_MINTS[e])),
    null != t.rewardUsdMin && t.rewardUsdMin > 0 && (u.rewardTotalUsdGte = t.rewardUsdMin),
    null != t.rewardUsdMax && t.rewardUsdMax < REWARD_RANGE.max && (u.rewardTotalUsdLte = t.rewardUsdMax));
  let f = (function (e, t) {
    if (!e) return t;
    if (!t) return e;
    let r = e.gte && t.gte ? (e.gte > t.gte ? e.gte : t.gte) : (e.gte ?? t.gte),
      n = e.lte && t.lte ? (e.lte < t.lte ? e.lte : t.lte) : (e.lte ?? t.lte);
    return { ...(r ? { gte: r } : {}), ...(n ? { lte: n } : {}) };
  })(c ? { lte: new Date(d + 86400000).toISOString() } : null, (function (e, t) {
    if (!e) return null;
    let r = new Date(t).toISOString();
    switch (e) {
      case 'lt-24h': return { gte: r, lte: new Date(t + 86400000).toISOString() };
      case 'lt-3d': return { gte: r, lte: new Date(t + 259200000).toISOString() };
      case 'lt-7d': return { gte: r, lte: new Date(t + 604800000).toISOString() };
      case 'gte-7d': return { gte: new Date(t + 604800000).toISOString() };
      default: return null;
    }
  })(t.timeLeft, d));
  return (f && (f.gte && (u.expiresAtGte = f.gte), f.lte && (u.expiresAtLte = f.lte)), u);
}

export const bountyQueryKey = (e = {}) => ['bounties', 'publicListV2Infinite', e.q ?? null, e.creatorAddress ?? null,
    e.coinAddress ?? null, e.rewardMints?.join(',') ?? null, e.status ?? null, e.phase ?? null,
    e.sort ?? null, e.order ?? null, e.limit ?? null, e.expiresAtGte ?? null, e.expiresAtLte ?? null,
    e.rewardTotalUsdGte ?? null, e.rewardTotalUsdLte ?? null, e.likeCountGte ?? null,
    e.submissionCountGte ?? null, e.creatorXFollowerCountGte ?? null,
    true === e.includeBanned || null, true === e.facets || null, e.lat ?? null, e.lng ?? null, e.radiusKm ?? null];
export function nextBountyCursor(e) { return e.nextCursor ?? void 0; }

// client is the actual-shaped useLivestreamApiClient delivery. responseSchema
// is 711902.L. No transport, destination, credentials store or Zod substitute is
// installed here. xFeatures is the supplied 314197.f feature result, not auth.
export function bountyInfiniteQuery(e, { client: U, responseSchema, xFeatures: C }) {
  let { q: m, creatorAddress: p, coinAddress: w, rewardMints: g, status: b, phase: h,
    expiresAtGte: v, expiresAtLte: y, rewardTotalUsdGte: x, rewardTotalUsdLte: S,
    likeCountGte: N, submissionCountGte: E, creatorXFollowerCountGte: j, includeBanned: I,
    sort: R, order: A, lat: _, lng: L, radiusKm: T, limit: O, facets: D, enabled: M,
  } = void 0 === e ? {} : e;
  let P = void 0 === O ? 24 : O, k = void 0 === M || M,
    F = allowBountySort(R, C), B = C ? j : void 0, G = clampBountyQuery(m),
    $ = null != _ && null != L && null != T && Number.isFinite(_) && Number.isFinite(L) && Number.isFinite(T);
  const queryKey = bountyQueryKey({ q: G, creatorAddress: p, coinAddress: w, rewardMints: g,
    status: b, phase: h, sort: F, order: A, limit: P, expiresAtGte: v, expiresAtLte: y,
    rewardTotalUsdGte: x, rewardTotalUsdLte: S, likeCountGte: N, submissionCountGte: E,
    creatorXFollowerCountGte: B, includeBanned: I, facets: D, ...($ ? { lat: _, lng: L, radiusKm: T } : {}) });
  const queryFn = async (e) => {
    let { pageParam: t } = e, r = {};
    (G && G.length > 0 && (r.q = G), p && (r.creatorAddress = p), w && (r.coinAddress = w),
      g && g.length > 0 && (r.rewardMints = g.join(',')), b && (r.status = b), h && (r.phase = h),
      v && (r.expiresAtGte = v), y && (r.expiresAtLte = y),
      null != x && (r.rewardTotalUsdGte = String(x)), null != S && (r.rewardTotalUsdLte = String(S)),
      null != N && (r.likeCountGte = String(N)), null != E && (r.submissionCountGte = String(E)),
      null != B && (r.creatorXFollowerCountGte = String(B)), I && (r.includeBanned = 'true'),
      F && (r.sort = F), A && (r.order = A),
      $ && ((r.lat = String(_)), (r.lng = String(L)), (r.radiusKm = String(T))),
      (r.limit = String(P)), D && null == t && (r.facets = 'true'),
      null != t && '' !== t && (r.cursor = t));
    let n = await U.get('bounties/v2/tasks', { searchParams: r }).json();
    return responseSchema.parse(n);
  };
  return { enabled: k, queryKey, initialPageParam: void 0, queryFn, getNextPageParam: nextBountyCursor };
}

export const timeLeftMatches = (e, t, r) => {
  if (!t || !e.expiresAt) return true;
  let n = Date.parse(e.expiresAt);
  if (Number.isNaN(n)) return true;
  let i = n - r;
  switch (t) {
    case 'lt-24h': return i > 0 && i <= 86400000;
    case 'lt-3d': return i > 0 && i <= 259200000;
    case 'lt-7d': return i > 0 && i <= 604800000;
    case 'gte-7d': return i > 604800000;
    default: return true;
  }
};

export function createBountyFilterOperations({ now = Date.now } = {}) {
  const classifyPhase = (e, t) => {
    if ('DRAFT' === e) return 'DRAFT';
    if ('PENDING_RESOLUTION' !== e) return e;
    if (!t) return 'OPEN';
    let r = Date.parse(t);
    return Number.isNaN(r) || r > now() ? 'OPEN' : 'PENDING_RESOLUTION';
  };
  const facets = (e) => {
    let r = new Map(), n = new Map();
    for (let i of e) {
      let e = classifyPhase(i.status, i.expiresAt);
      for (let t of (r.set(e, (r.get(e) ?? 0) + 1), i.rewardLegs))
        t.mintAddress && n.set(t.mintAddress, (n.get(t.mintAddress) ?? 0) + 1);
    }
    return { phase: [...r.entries()].map(([e, t]) => ({ key: e, count: t })), status: [],
      rewardMints: [...n.entries()].map(([e, t]) => ({ key: e, count: t })) };
  };
  const countTimeLeft = (e, n = now()) => {
    let i = new Map();
    for (let { key: e } of TIME_LEFT_OPTIONS) i.set(e, 0);
    for (let s of e) for (let { key: e } of TIME_LEFT_OPTIONS) timeLeftMatches(s, e, n) && i.set(e, (i.get(e) ?? 0) + 1);
    return i;
  };
  const filterTasks = (e, n, i = now()) => e.filter((e) => {
    let s, a;
    return (!(s = n.q.trim().toLowerCase()) || [e.title, e.bodyMarkdown].filter(Boolean).join('\n').toLowerCase().includes(s)) &&
      ((e, r) => { if (0 === r.length) return true; let n = classifyPhase(e.status, e.expiresAt); return 'DRAFT' !== n && r.includes(n); })(e, n.statuses) &&
      ((e, r) => {
        if (0 === r.length) return true;
        let n = new Set(e.rewardLegs.map((e) => e.mintAddress).filter((e) => !!e));
        return (e.coinAddress && n.add(e.coinAddress), r.some((e) => n.has(REWARD_MINTS[e])));
      })(e, n.rewardTokens) &&
      (null == (a = e.rewardTotalUsd) || ((null == n.rewardUsdMin || !(n.rewardUsdMin > 0) || !(a < n.rewardUsdMin)) &&
        (null == n.rewardUsdMax || !(n.rewardUsdMax < REWARD_RANGE.max) || !(a > n.rewardUsdMax)))) && timeLeftMatches(e, n.timeLeft, i);
  });
  return { classifyPhase, facets, countTimeLeft, filterTasks };
}

export function bountyFeedItem(e) {
  return { type: 'bounty', bounty: e.bounty,
    resolvedToken: e.resolvedTokens && e.bounty.token ? e.resolvedTokens.get(e.bounty.token.mint) : void 0,
    resolvedTokens: e.resolvedTokens, isDraft: e.isDraft,
    timestamp: new Date(e.bounty.createdAt).getTime(), key: `${e.keyPrefix}-${e.bounty.id}` };
}
export function bountyPageItems(e) { return e.items; }
const EMPTY_STATUSES = [];

// No provider, query cache, enrichment, observer or React effect is installed.
// Enrichment is the actual 260095.E result shape and must be supplied by the host.
export function createGoScreener({ client, responseSchema, xFeatures, enrichTasks, now = Date.now }) {
  const operations = createBountyFilterOperations({ now });
  return {
    plan({ filters, sortKey, nearMe = null }) {
      const listing = buildBountyFilters({ sortKey, filters, nearMe, now });
      const phaseFacets = buildBountyFilters({ sortKey, filters: withoutStatuses(filters), nearMe, now });
      const ports = { client, responseSchema, xFeatures };
      return {
        listing: bountyInfiniteQuery({ ...listing, limit: 24, facets: true, enabled: true }, ports),
        phaseFacets: bountyInfiniteQuery({ ...phaseFacets, limit: 1, facets: true, enabled: true }, ports),
      };
    },
    derive({ filters, nearMe = null, viewMode, listingResult, facetsResult, sentinelRef }) {
      const tasks = listingResult.data?.pages.flatMap(bountyPageItems) ?? [];
      const serverPhases = facetsResult.data?.pages[0]?.facets?.phase;
      const noStatuses = operations.filterTasks(tasks, withoutStatuses(filters));
      const noRewardTokens = operations.filterTasks(tasks, withoutRewardTokens(filters));
      const phase = serverPhases ?? operations.facets(noStatuses).phase;
      const reward = operations.facets(noRewardTokens);
      const facets = { phase, status: EMPTY_STATUSES, rewardMints: reward.rewardMints };
      const timeLeftCounts = operations.countTimeLeft(operations.filterTasks(tasks, withoutTimeLeft(filters)));
      const { bounties, liveTokens } = enrichTasks(tasks);
      const byId = new Map(); for (const bounty of bounties) byId.set(bounty.id, bounty);
      const items = tasks.flatMap((e) => {
        let t = byId.get(e.taskId);
        return t ? [bountyFeedItem({ bounty: t, resolvedTokens: liveTokens, keyPrefix: 'screener-bounty' })] : [];
      });
      const mintSet = new Set();
      for (let e of tasks) {
        for (let t of e.rewardLegs) t.mintAddress && mintSet.add(t.mintAddress);
        e.coinAddress && mintSet.add(e.coinAddress);
      }
      const visibleMints = [...mintSet];
      const sentinel = { hasMore: listingResult.hasNextPage, isLoading: listingResult.isFetchingNextPage, onLoadMore: listingResult.fetchNextPage };
      const body = listingResult.isLoading && 0 === tasks.length ? 'loading'
        : listingResult.isError && 0 === tasks.length ? 'error' : 0 === tasks.length ? 'empty' : 'feed';
      return { tasks, facets, timeLeftCounts, items, visibleMints, subscribeVisible: visibleMints.length > 0,
        sentinel, body, nearMeActive: null != nearMe,
        footerProps: { hasMore: listingResult.hasNextPage, isLoading: listingResult.isFetchingNextPage, sentinelRef, visibleCount: tasks.length },
        feedProps: { disableHoverCards: true, feedKind: 'bounties', items, viewMode } };
    },
  };
}
