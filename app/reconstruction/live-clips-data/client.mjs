// Editable complete 944001.E main /live clips/VOD query-and-join flow.
// Captures are parsed only. Actual provider/schema/query runtime capabilities are required.
export function createLiveClipsData(ports){

  for(const name of ['memoCache','useQuery','useLivestreamApiClient','useCoinMetadata','useSolPrice'])
    if(typeof ports?.[name]!=='function')throw new TypeError('required original hook capability: '+name);
  if(typeof ports.arraySchemaModule?.z?.array!=='function'||!ports.analyticsItemSchema||!ports.clipItemSchema||
     typeof ports.analyticsLogger?.error!=='function'||typeof ports.clipLogger?.error!=='function'||
     typeof ports.Date!=='function'||typeof ports.Date.now!=='function'||typeof ports.Date.parse!=='function'||
     typeof ports.Date.prototype?.getTime!=='function'||!ports.sectionKinds||
     !Object.hasOwn(ports.sectionKinds,'TRENDING_CLIPS')||!Object.hasOwn(ports.sectionKinds,'POPULAR_RECORDINGS')||
     !Object.hasOwn(ports.listingConstants??{},'LIVE_LISTING_LIMIT')||!ports.listingConstants?.LIVE_CARD_COUNTS||
     !Object.hasOwn(ports.listingConstants.LIVE_CARD_COUNTS,'large'))
    throw new TypeError('required exact schema, logger, Date, section-kind and existing1821 constant capabilities');

  const r={c:ports.memoCache},o={useQuery:ports.useQuery},n={useLivestreamApiClient:ports.useLivestreamApiClient},
    s={f:ports.useCoinMetadata},_={f:ports.useSolPrice},t={f:ports.sectionKinds},
    a={O:ports.listingConstants.LIVE_LISTING_LIMIT},l={g:ports.listingConstants.LIVE_CARD_COUNTS},
    h=ports.arraySchemaModule,N=ports.analyticsItemSchema,w=ports.clipItemSchema,
    y={y:ports.analyticsLogger},x={logger:ports.clipLogger},Date=ports.Date;
function j(e, t) {
  return t.roomName && t.vodId && e.push({
    roomName: t.roomName,
    clipId: t.vodId
  }), e;
}
function I(e, t) {
  return (t.viewCount ?? 0) - (e.viewCount ?? 0);
}
function S(e, t) {
  return e.index - t.index;
}
function T(e) {
  return e.clip;
}
function L(e) {
  return e.roomName;
}
function k(e, t) {
  return e[t.mint] = t, e;
}
function R() {}
let C = {
  [t.f.TRENDING_CLIPS]: {
    type: "weekly",
    clipType: "HIGHLIGHT"
  },
  [t.f.POPULAR_RECORDINGS]: {
    type: "monthly",
    clipType: "COMPLETE"
  }
};
let E = e => {
  let t,
    i,
    c,
    d,
    m,
    u,
    f = (0, r.c)(10),
    {
      limit: p,
      sectionId: v
    } = e,
    g = void 0 === p ? a.O : p,
    b = C[v],
    E = Math.floor(3 * g);
  f[0] === Symbol.for("react.memo_cache_sentinel") ? (t = {
    staleTime: 36e5
  }, i = {
    staleTime: 36e5
  }, f[0] = t, f[1] = i) : (t = f[0], i = f[1]), f[2] !== b || f[3] !== E ? (c = {
    ...b,
    limit: E,
    vodAnalyticsOptions: t,
    clipsOptions: i
  }, f[2] = b, f[3] = E, f[4] = c) : c = f[4];
  let {
      clipsQuery: A,
      vodAnalyticsQuery: z
    } = (e => {
      var t, i;
      let s,
        l,
        a,
        c,
        d,
        m,
        u,
        f,
        p,
        v,
        g,
        b,
        _,
        C,
        E,
        I,
        S,
        T,
        L,
        k,
        R,
        A,
        z = (0, r.c)(13),
        {
          type: P,
          limit: M,
          clipType: F,
          vodAnalyticsOptions: O,
          clipsOptions: D
        } = e;
      z[0] !== F || z[1] !== M || z[2] !== P || z[3] !== O ? (s = {
        type: P,
        limit: M,
        clipType: F,
        ...O
      }, z[0] = F, z[1] = M, z[2] = P, z[3] = O, z[4] = s) : s = z[4];
      let U = (t = s, (_ = (0, r.c)(21))[0] !== t ? ({
        type: p,
        limit: m,
        clipType: d,
        oversampleFactor: f,
        ...u
      } = t, _[0] = t, _[1] = d, _[2] = m, _[3] = u, _[4] = f, _[5] = p) : (d = _[1], m = _[2], u = _[3], f = _[4], p = _[5]), C = void 0 === f ? 5 : f, E = (0, n.useLivestreamApiClient)(), _[6] !== d || _[7] !== m || _[8] !== C || _[9] !== p ? (v = ["vod-analytics", p, m, d, C], _[6] = d, _[7] = m, _[8] = C, _[9] = p, _[10] = v) : v = _[10], _[11] !== E || _[12] !== d || _[13] !== m || _[14] !== C || _[15] !== p ? (g = async () => {
        let e = new URLSearchParams();
        e.set("type", p), e.set("limit", m.toString()), e.set("timestamp", Math.floor(new Date().getTime() / 1e3).toString()), e.set("oversample", (m * C).toString()), e.set("clipType", d);
        let t = await E.get("vod-analytics/top", {
          searchParams: e
        }).json();
        try {
          return h.z.array(N).parse(t);
        } catch (e) {
          throw y.y.error("Failed to parse vod analytics", {
            error: e
          }), e;
        }
      }, _[11] = E, _[12] = d, _[13] = m, _[14] = C, _[15] = p, _[16] = g) : g = _[16], _[17] !== u || _[18] !== v || _[19] !== g ? (b = {
        queryKey: v,
        queryFn: g,
        ...u
      }, _[17] = u, _[18] = v, _[19] = g, _[20] = b) : b = _[20], (0, o.useQuery)(b));
      z[5] !== U.data ? (l = U.data?.reduce(j, []) ?? [], z[5] = U.data, z[6] = l) : l = z[6], z[7] !== D || z[8] !== l ? (a = {
        ids: l,
        ...D
      }, z[7] = D, z[8] = l, z[9] = a) : a = z[9];
      let H = (i = a, (R = (0, r.c)(12))[0] !== i ? ({
        ids: I,
        ...S
      } = i, R[0] = i, R[1] = I, R[2] = S) : (I = R[1], S = R[2]), A = (0, n.useLivestreamApiClient)(), R[3] !== I ? (T = ["clips-by-ids", I], R[3] = I, R[4] = T) : T = R[4], R[5] !== A || R[6] !== I ? (L = async () => {
        if (0 === I.length) return [];
        let e = await A.post("clips/by-ids", {
          json: {
            ids: I
          }
        }).json();
        try {
          return h.z.array(w).parse(e);
        } catch (e) {
          throw x.logger.error("[useClipsByIds] Failed to parse clips", {
            error: e
          }), e;
        }
      }, R[5] = A, R[6] = I, R[7] = L) : L = R[7], R[8] !== S || R[9] !== T || R[10] !== L ? (k = {
        queryKey: T,
        queryFn: L,
        ...S
      }, R[8] = S, R[9] = T, R[10] = L, R[11] = k) : k = R[11], (0, o.useQuery)(k));
      return z[10] !== H || z[11] !== U ? (c = {
        vodAnalyticsQuery: U,
        clipsQuery: H
      }, z[10] = H, z[11] = U, z[12] = c) : c = z[12], c;
    })(c),
    P = [...(A.data ?? [])].sort(I),
    M = new Map();
  f[5] === Symbol.for("react.memo_cache_sentinel") ? (d = function (e, t, i) {
    let r = 0;
    for (let s of e.values()) for (let {
      index: e
    } of s) (i ? e <= t : e < t) && r++;
    return r;
  }, f[5] = d) : d = f[5];
  let F = d;
  for (let e = 0; e < P.length; e++) {
    let t = P[e],
      i = M.get(t.roomName) ?? [],
      r = i[i.length - 1];
    if (r) {
      let t = F(M, r.index, !1);
      if (F(M, e, !1) - t < l.g.large) continue;
    }
    i.push({
      index: e,
      clip: t
    }), M.set(t.roomName, i);
  }
  let O = [...M.values()].flat().sort(S).map(T),
    D = (0, s.f)({
      mints: [...new Set(O.map(L) ?? [])]
    }),
    U = D.data?.reduce(k, {}) ?? {};
  f[6] === Symbol.for("react.memo_cache_sentinel") ? (m = {}, f[6] = m) : m = f[6];
  let H = (0, _.f)(m),
    K = O.reduce((e, t) => {
      let i = U[t.roomName],
        r = H.data && i?.market_cap ? i.market_cap * H.data : null;
      return e.push({
        id: t.clipId,
        mint: t.roomName,
        coinCreatedTimestamp: i?.created_timestamp ?? null,
        title: t.title || i?.name || t.roomName,
        creator: {
          address: i?.creator,
          username: i?.username || void 0
        },
        marketCap: r,
        thumbnail: t.thumbnailUrl,
        ipfsThumbnail: t.thumbnailUrl,
        thumbnailUpdatedAt: Date.parse(t.createdAt) || Date.now(),
        avatarUri: i?.image_uri ?? "",
        isLive: i?.is_currently_live || !1,
        playlistUrl: t.playlistUrl || t.mp4Url || i?.playlist_url_low || i?.playlist_url || void 0,
        viewerCount: t.viewCount ?? 0,
        viewerCountLabel: "views",
        linkUrl: `/coin/${t.roomName}?clip=${t.clipId}`,
        symbol: i?.symbol,
        coin: i
      }), e;
    }, []),
    V = z.isLoading || A.isLoading || D.isLoading;
  return f[7] !== K || f[8] !== V ? (u = {
    data: K,
    isLoading: V,
    fetchNextPage: R,
    hasNextPage: !1,
    isFetchingNextPage: !1
  }, f[7] = K, f[8] = V, f[9] = u) : u = f[9], u;
};
return Object.freeze({useClipSection:E});
}
