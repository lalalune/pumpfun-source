// Complete TOP feed owner/read boundary. Providers and prior helpers remain required capabilities.
import { createSolanaGuards } from "../search-navigation/navigation.mjs";
export const toFeedRows = (e) =>
  e.map((e) => ({
    type: "callout",
    key: e.key,
    createdAtMs: e.createdAt,
    entry: e,
  }));
export const ownerVariants = [
  {
    source: "evidence/web/objects/91795a66d4097dbd.js",
    sha256: "15362ee5bd0064faecc1064fa9f8f0fab9bd7ad7c725d0d71e0d6e72dc5ae63d",
  },
  {
    source: "evidence/web/objects/c3601a995a6b7f37.js",
    sha256: "a77c407f788dff679e4871e8f7f9275f2904f0e6846789ebf81ff31243194ec4",
  },
];
export const readContexts = [
  {
    source: "evidence/web/objects/3740fc4e7a24596d.js",
    reader: "bd59c4bee5702bebd7d5a2b91640d9ed9c3170493c0809861e33f4c926744f3d",
    holders: "725b498159f8de3640c8c0dee181399ac8cf23fac8ccb165f513e4e21fba49f5",
  },
  {
    source: "evidence/web/objects/cf2bb278631744da.js",
    reader: "3adabf21c26e22024c9c08c3e218b88d0c052d972cf3c25779c1c8efc3350ba2",
    holders: "250c5ade38f9102e1d386f5988a84f1793689813497627f40abc4a1d2b95b9ee",
  },
];
function reader0({ getContractClient }) {
  const u = { A: 5 };
  const p = { j: getContractClient };
  return async function x(e) {
    let { period: t = "daily", includeFollowedHolders: a = !1, signal: i } = e;
    return await (0, p.j)()("GET /pnl-leaderboard/positions", {
      query: {
        period: t,
        ...(a ? { includeFollowedHolders: !0, followedHoldersLimit: u.A } : {}),
      },
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      signal: i,
      hooks: {
        afterResponse: [
          (e, t, a) => {
            if (!a.ok)
              throw Error(`Failed to fetch pnl leaderboard: ${a.status}`);
          },
        ],
      },
    });
  };
}
function holders0() {
  let l = (e, t) => {
    let a = e.holders.filter((e) => !t(e));
    if (a.length === e.holders.length) return e;
    if (0 === a.length) return null;
    let i = e.holders.length - a.length;
    return { holders: a, totalCount: Math.max(e.totalCount - i, a.length) };
  };
  return {
    h: (e, t) => {
      if (!e || !t) return e;
      let a = t.toLowerCase();
      return l(e, (e) => e.username.toLowerCase() === a);
    },
  };
}
function reader1({ getContractClient }) {
  const u = { A: 5 };
  const p = { j: getContractClient };
  return async function E(e) {
    let { period: t = "daily", includeFollowedHolders: r = !1, signal: n } = e;
    return await (0, p.j)()("GET /pnl-leaderboard/positions", {
      query: {
        period: t,
        ...(r ? { includeFollowedHolders: !0, followedHoldersLimit: u.A } : {}),
      },
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      signal: n,
      hooks: {
        afterResponse: [
          (e, t, r) => {
            if (!r.ok)
              throw Error(`Failed to fetch pnl leaderboard: ${r.status}`);
          },
        ],
      },
    });
  };
}
function holders1() {
  let l = (e, t) => {
    let r = e.holders.filter((e) => !t(e));
    if (r.length === e.holders.length) return e;
    if (0 === r.length) return null;
    let n = e.holders.length - r.length;
    return { holders: r, totalCount: Math.max(e.totalCount - n, r.length) };
  };
  return {
    h: (e, t) => {
      if (!e || !t) return e;
      let r = t.toLowerCase();
      return l(e, (e) => e.username.toLowerCase() === r);
    },
  };
}
function owner0({
  useMemoCache,
  useQuery,
  reader,
  normalizerHelpers,
  engagementHelpers,
  holderHelpers,
  isSolanaMint,
}) {
  const n = normalizerHelpers;
  const t = { c: useMemoCache };
  const i = holderHelpers;
  const a = engagementHelpers;
  const s = { f: isSolanaMint };
  const r = { useQuery };
  const l = { F: reader };
  let o = (e) => {
    let t = e.callout,
      r = t?.thesis?.trim();
    if (!t || !r || null === t.calloutId || !(0, s.f)(e.coinMint)) return null;
    let l = (0, i.h)(e.followedHolders, e.username);
    return {
      key: `cid:${t.calloutId}`,
      calloutId: t.calloutId,
      coinMint: e.coinMint,
      userId: e.walletAddress,
      multiple: t.multiple ?? 0,
      marketCapUsd: t.calledOutAtMcap ?? void 0,
      createdAt: (0, n.l)(t.calloutTimestamp),
      username: e.username || void 0,
      xUsername: e.xUsername ?? void 0,
      profileImage: e.profileImage ?? void 0,
      note: r,
      ...(t.mediaUrl ? { mediaUrl: t.mediaUrl } : {}),
      ...(0, a.P)(t),
      updates: (0, n.v)({
        updates: t.updates,
        mint: e.coinMint,
        calloutId: t.calloutId,
      }),
      updateCount: (0, n.s)({ updates: t.updates, updateCount: t.updateCount }),
      ...(l?.holders.length ? { followedHolders: l } : {}),
      isViewer: e.isViewer,
      viewerFollows: e.viewerFollows,
    };
  };
  let d = () => {};
  let c = [];
  let u = (e) => {
    let { includeFollowedHolders: t, period: r } = e;
    return {
      queryKey: ["callouts", "top-feed", r, t],
      queryFn: ({ signal: e }) =>
        (0, l.F)({ period: r, includeFollowedHolders: t, signal: e }),
      staleTime: 3e5,
      retry: 3,
    };
  };
  return {
    useTopFeed: (e) => {
      let l,
        a,
        i,
        n,
        s,
        m,
        f,
        p = (0, t.c)(16);
      if (p[0] !== e) {
        let {
          enabled: t,
          includeFollowedHolders: n,
          period: s,
        } = void 0 === e ? {} : e;
        ((l = void 0 === t || t),
          (i = r.useQuery),
          (a = u({
            includeFollowedHolders: void 0 !== n && n,
            period: void 0 === s ? "daily" : s,
          })),
          (p[0] = e),
          (p[1] = l),
          (p[2] = a),
          (p[3] = i));
      } else ((l = p[1]), (a = p[2]), (i = p[3]));
      p[4] !== l || p[5] !== a
        ? ((n = { ...a, enabled: l, refetchOnWindowFocus: !0 }),
          (p[4] = l),
          (p[5] = a),
          (p[6] = n))
        : (n = p[6]);
      let h = i(n);
      if (p[7] !== h.data?.entries) {
        let e = new Set();
        for (let t of ((s = []), h.data?.entries ?? [])) {
          let r = o(t);
          !r || e.has(r.key) || (e.add(r.key), s.push(r));
        }
        ((p[7] = h.data?.entries), (p[8] = s));
      } else s = p[8];
      let v = s,
        b = l && h.isPending,
        g = h.isError && 0 === v.length ? "Could not load top callouts" : null;
      return (
        p[9] !== h
          ? ((m = () => void h.refetch()), (p[9] = h), (p[10] = m))
          : (m = p[10]),
        p[11] !== v || p[12] !== b || p[13] !== g || p[14] !== m
          ? ((f = {
              callouts: v,
              isLoadingHistory: b,
              error: g,
              pendingNewCount: 0,
              pendingPreview: c,
              showNewCallouts: d,
              hasNextPage: !1,
              isFetchingNextPage: !1,
              fetchNextPage: d,
              refetch: m,
            }),
            (p[11] = v),
            (p[12] = b),
            (p[13] = g),
            (p[14] = m),
            (p[15] = f))
          : (f = p[15]),
        f
      );
    },
    prefetchTopFeed: (e, t = {}) => {
      let { includeFollowedHolders: r = !1 } = t;
      return e.prefetchQuery(u({ includeFollowedHolders: r, period: "daily" }));
    },
    mapEntry: o,
    queryOptions: u,
  };
}
function owner1({
  useMemoCache,
  useQuery,
  reader,
  normalizerHelpers,
  engagementHelpers,
  holderHelpers,
  isSolanaMint,
}) {
  const n = normalizerHelpers;
  const t = { c: useMemoCache };
  const a = holderHelpers;
  const i = engagementHelpers;
  const s = { f: isSolanaMint };
  const r = { useQuery };
  const l = { F: reader };
  let o = (e) => {
    let t = e.callout,
      r = t?.thesis?.trim();
    if (!t || !r || null === t.calloutId || !(0, s.f)(e.coinMint)) return null;
    let l = (0, a.h)(e.followedHolders, e.username);
    return {
      key: `cid:${t.calloutId}`,
      calloutId: t.calloutId,
      coinMint: e.coinMint,
      userId: e.walletAddress,
      multiple: t.multiple ?? 0,
      marketCapUsd: t.calledOutAtMcap ?? void 0,
      createdAt: (0, n.l)(t.calloutTimestamp),
      username: e.username || void 0,
      xUsername: e.xUsername ?? void 0,
      profileImage: e.profileImage ?? void 0,
      note: r,
      ...(t.mediaUrl ? { mediaUrl: t.mediaUrl } : {}),
      ...(0, i.P)(t),
      updates: (0, n.v)({
        updates: t.updates,
        mint: e.coinMint,
        calloutId: t.calloutId,
      }),
      updateCount: (0, n.s)({ updates: t.updates, updateCount: t.updateCount }),
      ...(l?.holders.length ? { followedHolders: l } : {}),
      isViewer: e.isViewer,
      viewerFollows: e.viewerFollows,
    };
  };
  let d = () => {};
  let c = (e) => {
    let { includeFollowedHolders: t, period: r } = e;
    return {
      queryKey: ["callouts", "top-feed", r, t],
      queryFn: ({ signal: e }) =>
        (0, l.F)({ period: r, includeFollowedHolders: t, signal: e }),
      staleTime: 3e5,
      retry: 3,
    };
  };
  let u = [];
  return {
    useTopFeed: (e) => {
      let l,
        i,
        a,
        n,
        s,
        m,
        p,
        h = (0, t.c)(16);
      if (h[0] !== e) {
        let {
          enabled: t,
          includeFollowedHolders: n,
          period: s,
        } = void 0 === e ? {} : e;
        ((l = void 0 === t || t),
          (a = r.useQuery),
          (i = c({
            includeFollowedHolders: void 0 !== n && n,
            period: void 0 === s ? "daily" : s,
          })),
          (h[0] = e),
          (h[1] = l),
          (h[2] = i),
          (h[3] = a));
      } else ((l = h[1]), (i = h[2]), (a = h[3]));
      h[4] !== l || h[5] !== i
        ? ((n = { ...i, enabled: l, refetchOnWindowFocus: !0 }),
          (h[4] = l),
          (h[5] = i),
          (h[6] = n))
        : (n = h[6]);
      let f = a(n);
      if (h[7] !== f.data?.entries) {
        let e = new Set();
        for (let t of ((s = []), f.data?.entries ?? [])) {
          let r = o(t);
          !r || e.has(r.key) || (e.add(r.key), s.push(r));
        }
        ((h[7] = f.data?.entries), (h[8] = s));
      } else s = h[8];
      let g = s,
        y = l && f.isPending,
        b = f.isError && 0 === g.length ? "Could not load top callouts" : null;
      return (
        h[9] !== f
          ? ((m = () => void f.refetch()), (h[9] = f), (h[10] = m))
          : (m = h[10]),
        h[11] !== g || h[12] !== y || h[13] !== b || h[14] !== m
          ? ((p = {
              callouts: g,
              isLoadingHistory: y,
              error: b,
              pendingNewCount: 0,
              pendingPreview: u,
              showNewCallouts: d,
              hasNextPage: !1,
              isFetchingNextPage: !1,
              fetchNextPage: d,
              refetch: m,
            }),
            (h[11] = g),
            (h[12] = y),
            (h[13] = b),
            (h[14] = m),
            (h[15] = p))
          : (p = h[15]),
        p
      );
    },
    prefetchTopFeed: (e, t = {}) => {
      let { includeFollowedHolders: r = !1 } = t;
      return e.prefetchQuery(c({ includeFollowedHolders: r, period: "daily" }));
    },
    mapEntry: o,
    queryOptions: u,
  };
}
function select(table, key, label) {
  if (typeof key !== "string" || !Object.hasOwn(table, key))
    throw TypeError("explicit supported " + label + " hash required");
  return table[key];
}
export function createTopFeedRead({
  ownerVariant,
  readContext,
  useMemoCache,
  useQuery,
  getContractClient,
  normalizerHelpers,
  engagementHelpers,
  decodeBase58,
}) {
  for (const fn of [
    useMemoCache,
    useQuery,
    getContractClient,
    normalizerHelpers?.l,
    normalizerHelpers?.v,
    normalizerHelpers?.s,
    engagementHelpers?.P,
    decodeBase58,
  ])
    if (typeof fn !== "function")
      throw TypeError(
        "all explicit top read/runtime/helper capabilities required",
      );
  const reader = select(
    {
      bd59c4bee5702bebd7d5a2b91640d9ed9c3170493c0809861e33f4c926744f3d: reader0,
      "3adabf21c26e22024c9c08c3e218b88d0c052d972cf3c25779c1c8efc3350ba2":
        reader1,
    },
    readContext,
    "reader",
  )({ getContractClient });
  const holderHelpers = select(
    {
      bd59c4bee5702bebd7d5a2b91640d9ed9c3170493c0809861e33f4c926744f3d:
        holders0,
      "3adabf21c26e22024c9c08c3e218b88d0c052d972cf3c25779c1c8efc3350ba2":
        holders1,
    },
    readContext,
    "holder context",
  )();
  const owner = select(
    {
      "15362ee5bd0064faecc1064fa9f8f0fab9bd7ad7c725d0d71e0d6e72dc5ae63d":
        owner0,
      a77c407f788dff679e4871e8f7f9275f2904f0e6846789ebf81ff31243194ec4: owner1,
    },
    ownerVariant,
    "owner",
  )({
    useMemoCache,
    useQuery,
    reader,
    normalizerHelpers,
    engagementHelpers,
    holderHelpers,
    isSolanaMint: createSolanaGuards({ base58: { decode: decodeBase58 } })
      .validAddress,
  });
  return { ...owner, readPositions: reader };
}
