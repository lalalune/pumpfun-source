// Full selected following read owner. Required runtimes/providers are explicit capabilities.
import { mapUserReplyRow, mapReplyCallout } from "../user-replies/client.mjs";
import {
  createSolanaGuards,
  isSolanaText,
} from "../search-navigation/navigation.mjs";
export const readContexts = [
  {
    source: "evidence/web/objects/3740fc4e7a24596d.js",
    reader: "bd59c4bee5702bebd7d5a2b91640d9ed9c3170493c0809861e33f4c926744f3d",
    chain: "be5d1879b2367fa656f2076f6099f95e09966bef2f47e7cd9231d8d65b8e1ed5",
  },
  {
    source: "evidence/web/objects/cf2bb278631744da.js",
    reader: "3adabf21c26e22024c9c08c3e218b88d0c052d972cf3c25779c1c8efc3350ba2",
    chain: "63b0ae0a4046cf9d5e5098bb1460fd0e661d05ccc8cf387a1695bf68bd8da12f",
  },
];
export const imageVariants = [
  {
    source: "evidence/web/objects/3740fc4e7a24596d.js",
    sha256: "5eeb70ba118c78cfac5c12f6076086df0d2101d7d7ce07cf076db28b591b992b",
  },
  {
    source: "evidence/web/objects/cf2bb278631744da.js",
    sha256: "6e4a4333b2542dd42e35dcc902ca61451ca19e5e6e9643736452979e7d799bfd",
  },
];
export const classificationVariants = [
  {
    source: "evidence/web/objects/0fea5750534737b2.js",
    sha256: "e3ade9570aef5bef1709871e34a348d5175fede0689284312028c2ca0f7517a4",
  },
  {
    source: "evidence/web/objects/316ff95d024f8997.js",
    sha256: "5dcc6ddfc4d1c08e2852d9903a39eccd09764b4cd4d3d6b71db7a06b5178c5ce",
  },
];
function namespace() {
  let r = "starknet";
  let n = "near";
  let i = "ton:-239";
  let a = "starknet:SN_MAIN";
  let d = "near:mainnet";
  return {
    C: (e) => e === i || e === a || e === d,
    L: (e) => e === i,
    B: (e) => e === d,
    _: (e) => e === a,
    h: "starknet",
    Q: "near",
    z: "ton",
    J: "ton:-239",
    W: "starknet:SN_MAIN",
    d: "near:mainnet",
  };
}
function mintNamespace() {
  return {
    h: function (e) {
      return "string" == typeof e && /^0x[0-9a-fA-F]{40}$/.test(e);
    },
    w: function i(e) {
      if (!e) return null;
      let a = e.trim();
      return a ? (a.startsWith("eip155:") ? a.slice(7) : a) : null;
    },
  };
}
function reader0({ getContractClient, kindsSchema }) {
  const t = {
    contract: {
      "GET /following-positions/alerts": {
        query: { shape: { kinds: kindsSchema } },
      },
    },
  };
  const p = { j: getContractClient };
  return {
    read: async function k(e) {
      let {
        pageSize: a = 10,
        cursor: i,
        kinds: n = "callout,update,trade,collectible",
        minTradeAmountUsd: r = 10,
        minMarketCapUsd: l = null,
        maxMarketCapUsd: s = null,
        signal: o,
        chainIds: d,
        chains: u,
      } = e;
      return await (0, p.j)()("GET /following-positions/alerts", {
        query: {
          pageSize: a,
          kinds: t.contract[
            "GET /following-positions/alerts"
          ].query.shape.kinds.parse(n.split(",")),
          minTradeAmountUsd: r ?? void 0,
          minMarketCapUsd: l ?? void 0,
          maxMarketCapUsd: s ?? void 0,
          chainIds: d,
          chains: u,
          cursor: i || void 0,
        },
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        signal: o,
        hooks: {
          afterResponse: [
            (e, t, a) => {
              if (!a.ok)
                throw Error(`Failed to fetch alerts feed: ${a.status}`);
            },
          ],
        },
      });
    },
    kinds: "callout,update,reply,quote,repost",
    assets: (e) => ({
      ...(null != e.assetClass ? { assetClass: e.assetClass } : {}),
      ...(null != e.collectible ? { collectible: e.collectible } : {}),
    }),
  };
}
function reader1({ getContractClient, kindsSchema }) {
  const t = {
    contract: {
      "GET /following-positions/alerts": {
        query: { shape: { kinds: kindsSchema } },
      },
    },
  };
  const p = { j: getContractClient };
  return {
    read: async function _(e) {
      let {
        pageSize: r = 10,
        cursor: n,
        kinds: i = "callout,update,trade,collectible",
        minTradeAmountUsd: a = 10,
        minMarketCapUsd: l = null,
        maxMarketCapUsd: o = null,
        signal: s,
        chainIds: d,
        chains: u,
      } = e;
      return await (0, p.j)()("GET /following-positions/alerts", {
        query: {
          pageSize: r,
          kinds: t.contract[
            "GET /following-positions/alerts"
          ].query.shape.kinds.parse(i.split(",")),
          minTradeAmountUsd: a ?? void 0,
          minMarketCapUsd: l ?? void 0,
          maxMarketCapUsd: o ?? void 0,
          chainIds: d,
          chains: u,
          cursor: n || void 0,
        },
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        signal: s,
        hooks: {
          afterResponse: [
            (e, t, r) => {
              if (!r.ok)
                throw Error(`Failed to fetch alerts feed: ${r.status}`);
            },
          ],
        },
      });
    },
    kinds: "callout,update,reply,quote,repost",
    assets: (e) => ({
      ...(null != e.assetClass ? { assetClass: e.assetClass } : {}),
      ...(null != e.collectible ? { collectible: e.collectible } : {}),
    }),
  };
}
function chain0({ namespace, mint, isSolanaMint, perpsChain }) {
  const l = { g: perpsChain };
  const n = mint;
  const s = { f: isSolanaMint };
  const i = namespace;
  let o = [
    "solana",
    "robinhood",
    "hyperevm",
    "base",
    "bsc",
    "ethereum",
    "arc",
    "megaeth",
    "xlayer",
    "monad",
    "polygon",
    "arbitrum",
    i.Q,
    i.z,
  ];
  let u = "perps";
  let h = {
    ethereum: "1",
    base: "8453",
    bsc: "56",
    robinhood: "4663",
    hyperevm: "999",
    arc: "5042",
    megaeth: "4326",
    xlayer: "196",
    monad: "143",
    polygon: "137",
    arbitrum: "42161",
  };
  let f = (e, t = {}) => {
    if (!e?.length || e.includes(i.h)) return {};
    let a = e.includes(u);
    if (a && !1 === t.hype) return {};
    let n = o.filter((t) => e.includes(t));
    if (n.length === o.length)
      return a ? { chains: ["all", "hlcore:mainnet"] } : {};
    let r = n
        .flatMap((e) =>
          "solana" === e
            ? [0x536f6c4d]
            : e === i.Q || e === i.z
              ? []
              : [Number(h[e])],
        )
        .sort((e, t) => e - t),
      s = [];
    return (
      a && s.push(l.g),
      n.includes(i.z) && s.push(i.J),
      n.includes(i.Q) && s.push(i.d),
      {
        ...(r.length > 0 ? { chainIds: r } : {}),
        ...(s.length > 0 ? { chains: s } : {}),
      }
    );
  };
  return {
    m: (e) => f("all" === e ? void 0 : [e]),
    R: (e) => [...(e.chainIds ?? []), ...(e.chains ?? [])].join(","),
    N: (e, t) => {
      if ("all" === t) return !0;
      if (t === u) return !0 === e.perp;
      if (e.perp) return !1;
      let a = "string" == typeof e.chainId && (0, i.L)(e.chainId);
      if (t === i.z) return a;
      if (a) return !1;
      let r = "string" == typeof e.chainId && (0, i._)(e.chainId);
      if (t === i.h) return r;
      if (r) return !1;
      let l = "string" == typeof e.chainId && (0, i.B)(e.chainId);
      if (t === i.Q) return l;
      if (l) return !1;
      if ("solana" === t) return (0, s.f)(e.coinMint);
      if ((0, s.f)(e.coinMint)) return !1;
      let o = null == e.chainId ? null : (0, n.w)(String(e.chainId));
      return null !== o && o === h[t];
    },
  };
}
function chain1({ namespace, mint, isSolanaMint, perpsChain }) {
  const l = { g: perpsChain };
  const i = mint;
  const o = { f: isSolanaMint };
  const n = namespace;
  let s = [
    "solana",
    "robinhood",
    "hyperevm",
    "base",
    "bsc",
    "ethereum",
    "arc",
    "megaeth",
    "xlayer",
    "monad",
    "polygon",
    "arbitrum",
    n.Q,
    n.z,
  ];
  let u = "perps";
  let h = {
    ethereum: "1",
    base: "8453",
    bsc: "56",
    robinhood: "4663",
    hyperevm: "999",
    arc: "5042",
    megaeth: "4326",
    xlayer: "196",
    monad: "143",
    polygon: "137",
    arbitrum: "42161",
  };
  let f = (e, t = {}) => {
    if (!e?.length || e.includes(n.h)) return {};
    let r = e.includes(u);
    if (r && !1 === t.hype) return {};
    let i = s.filter((t) => e.includes(t));
    if (i.length === s.length)
      return r ? { chains: ["all", "hlcore:mainnet"] } : {};
    let a = i
        .flatMap((e) =>
          "solana" === e
            ? [0x536f6c4d]
            : e === n.Q || e === n.z
              ? []
              : [Number(h[e])],
        )
        .sort((e, t) => e - t),
      o = [];
    return (
      r && o.push(l.g),
      i.includes(n.z) && o.push(n.J),
      i.includes(n.Q) && o.push(n.d),
      {
        ...(a.length > 0 ? { chainIds: a } : {}),
        ...(o.length > 0 ? { chains: o } : {}),
      }
    );
  };
  return {
    m: (e) => f("all" === e ? void 0 : [e]),
    R: (e) => [...(e.chainIds ?? []), ...(e.chains ?? [])].join(","),
    N: (e, t) => {
      if ("all" === t) return !0;
      if (t === u) return !0 === e.perp;
      if (e.perp) return !1;
      let r = "string" == typeof e.chainId && (0, n.L)(e.chainId);
      if (t === n.z) return r;
      if (r) return !1;
      let a = "string" == typeof e.chainId && (0, n._)(e.chainId);
      if (t === n.h) return a;
      if (a) return !1;
      let l = "string" == typeof e.chainId && (0, n.B)(e.chainId);
      if (t === n.Q) return l;
      if (l) return !1;
      if ("solana" === t) return (0, o.f)(e.coinMint);
      if ((0, o.f)(e.coinMint)) return !1;
      let s = null == e.chainId ? null : (0, i.w)(String(e.chainId));
      return null !== s && s === h[t];
    },
  };
}
function image0() {
  let t = "https://img.phygitals.com";
  let a = [`${t}/`, "https://gateway.irys.xyz/"];
  let i = "-cropped";
  let n = 512;
  let r = (e, r = n) => {
    let l = ((e) => {
      let t = a.find((t) => e.startsWith(t));
      if (void 0 === t) return;
      let n = e.slice(t.length);
      if (!("" === n || n.includes("/") || n.includes("?")))
        return n.endsWith(i) ? n.slice(0, -i.length) : n;
    })(e);
    if (void 0 === l) return e;
    let s = encodeURIComponent(`${t}/${l}${i}`);
    return `${t}/cdn-cgi/image/width=${r},quality=85,format=auto,fit=scale-down/${s}`;
  };
  return (e, t) => {
    let a = t?.trim() ?? "";
    return "" === a ? null : "phygitals" === e ? r(a) : a;
  };
}
function image1() {
  let t = "https://img.phygitals.com";
  let r = [`${t}/`, "https://gateway.irys.xyz/"];
  let n = "-cropped";
  let i = 512;
  let a = (e, a = i) => {
    let l = ((e) => {
      let t = r.find((t) => e.startsWith(t));
      if (void 0 === t) return;
      let i = e.slice(t.length);
      if (!("" === i || i.includes("/") || i.includes("?")))
        return i.endsWith(n) ? i.slice(0, -n.length) : i;
    })(e);
    if (void 0 === l) return e;
    let o = encodeURIComponent(`${t}/${l}${n}`);
    return `${t}/cdn-cgi/image/width=${a},quality=85,format=auto,fit=scale-down/${o}`;
  };
  return (e, t) => {
    let r = t?.trim() ?? "";
    return "" === r ? null : "phygitals" === e ? a(r) : r;
  };
}
function classification0({ mint, shape, perpsChain }) {
  const p = { g: perpsChain };
  const d = mint;
  const o = { k: shape };
  let c = /^(?:[a-z0-9]{1,16}:)?[A-Za-z0-9]{1,24}$/;
  let u = (e) => {
    let t = e?.trim() ?? "";
    return c.test(t) && !(0, o.k)(t) && !(0, d.h)(t);
  };
  let m = (e) => e?.chain === p.g;
  let x = (e) => m(e) || null != e.perp;
  let h = (e) => u(e?.coinMint);
  return (e) => {
    switch (e.type) {
      case "callout":
        return x(e.entry);
      case "reply":
      case "quote":
        return h(e.row.callout);
      case "repost":
        return h(e.callout);
      default:
        return !1;
    }
  };
}
function classification1({ mint, shape, perpsChain }) {
  const m = { g: perpsChain };
  const d = mint;
  const o = { k: shape };
  let c = /^(?:[a-z0-9]{1,16}:)?[A-Za-z0-9]{1,24}$/;
  let u = (e) => {
    let t = e?.trim() ?? "";
    return c.test(t) && !(0, o.k)(t) && !(0, d.h)(t);
  };
  let p = (e) => e?.chain === m.g;
  let x = (e) => p(e) || null != e.perp;
  let h = (e) => u(e?.coinMint);
  return (e) => {
    switch (e.type) {
      case "callout":
        return x(e.entry);
      case "reply":
      case "quote":
        return h(e.row.callout);
      case "repost":
        return h(e.callout);
      default:
        return !1;
    }
  };
}
function entries({
  normalizerHelpers,
  assets,
  classify,
  namespace,
  collectibleImage,
}) {
  const collectible = (() => {
    const t = { G: collectibleImage };
    let n = (e) => {
      if (null == e) return null;
      let t = e.trim();
      return "" === t ? null : t;
    };
    return (e, r) =>
      null == r
        ? null
        : {
            nftAddress: e,
            name: n(r.name),
            image: (0, t.G)(r.provider, r.imageUrl),
            grade: n(r.grade),
            setName: n(r.setName),
          };
  })();
  const r = normalizerHelpers;
  const t = { q: collectible };
  const l = { j: mapUserReplyRow, m: mapReplyCallout };
  const a = namespace;
  const i = { l: classify };
  const n = { E: assets };
  let o = (e) => ((0, a.C)(e) ? { chain: e } : {});
  let s = (e) => {
    if (!e) return 0;
    let t = Date.parse(e);
    return Number.isFinite(t) ? t : 0;
  };
  let u = (e) =>
    e.walletAddress?.trim() ||
    e.author?.walletAddress?.trim() ||
    e.author?.userId ||
    void 0;
  let c = (e, t) => {
    let n = e.coinMint || t?.coinMint;
    return n
      ? {
          mint: n,
          chainId: e.chainId,
          ...o(e.chain),
          name: e.coinName ?? t?.coinName ?? null,
          symbol: e.symbol ?? t?.symbol ?? null,
          image: e.coinImage ?? t?.coinImage ?? null,
        }
      : null;
  };
  return {
    o: (e) => {
      if ("callout" === e.kind) {
        let { callout: t } = e;
        if (!t || null === t.calloutId) return null;
        let i = u(e);
        if (!i) return null;
        let l = s(e.createdAt) || s(t.calloutTimestamp),
          a = s(t.calloutTimestamp) || l,
          c = e.position ? (0, r.g)(e.position) : void 0;
        return {
          type: "callout",
          key: `cid:${t.calloutId}`,
          chainId: e.chainId,
          ...o(e.chain),
          createdAtMs: l,
          entry: {
            key: `cid:${t.calloutId}`,
            calloutId: t.calloutId,
            coinMint: e.coinMint,
            userId: i,
            authorCcUserId: e.author?.userId ?? void 0,
            multiple: t.multiple ?? 0,
            marketCapUsd: t.calledOutAtMcap ?? void 0,
            createdAt: a,
            coinName: e.coinName ?? void 0,
            coinSymbol: e.symbol ?? void 0,
            coinImage: e.coinImage ?? void 0,
            username: e.author?.userName || void 0,
            xUsername: e.author?.xUsername ?? void 0,
            profileImage: e.author?.profileImage ?? void 0,
            resolvedAvatarDecoration:
              e.author?.resolvedAvatarDecoration ?? void 0,
            note: t.thesis?.trim() || void 0,
            ...(t.mediaUrl ? { mediaUrl: t.mediaUrl } : {}),
            ...(t.chain ? { chain: t.chain } : {}),
            ...(t.perp ? { perp: t.perp } : {}),
            ...(0, n.E)(t),
            updates: (0, r.v)({
              updates: t.updates,
              mint: e.coinMint,
              calloutId: t.calloutId,
            }),
            updateCount: (0, r.s)({
              updates: t.updates,
              updateCount: t.updateCount,
            }),
            ...(c ? { positionPnl: c } : {}),
          },
        };
      }
      if ("update" === e.kind) {
        let t = e.reply,
          n = t?.callout,
          i = n?.callout;
        if (!t || !n || !i || null === i.calloutId) return null;
        let l = u(e);
        if (!l) return null;
        let a = e.coinMint || n.coinMint;
        if (!a) return null;
        let c = {
            id: t.reply.id,
            content: t.reply.content,
            createdAt: t.reply.createdAt,
            likeCount: t.reply.likeCount ?? 0,
            mediaUrl: t.reply.mediaUrl ?? null,
            parentMessageId: null,
            repostCount: t.reply.repostCount,
          },
          d = [c, ...(i.updates ?? []).filter((e) => e.id !== c.id)].sort(
            (e, t) => s(t.createdAt) - s(e.createdAt),
          ),
          m = s(e.createdAt) || s(t.reply.createdAt) || s(i.calloutTimestamp),
          f = s(i.calloutTimestamp) || m;
        return {
          type: "callout",
          key: `upd:${t.reply.id}`,
          chainId: e.chainId,
          ...o(e.chain),
          createdAtMs: m,
          entry: {
            key: `upd:${t.reply.id}`,
            calloutId: i.calloutId,
            coinMint: a,
            userId: l,
            authorCcUserId: e.author?.userId ?? void 0,
            multiple: i.multiple ?? 0,
            marketCapUsd: i.calledOutAtMcap ?? void 0,
            createdAt: f,
            coinName: (e.coinName ?? n.coinName) || void 0,
            coinSymbol: (e.symbol ?? n.symbol) || void 0,
            coinImage: (e.coinImage ?? n.coinImage) || void 0,
            username: e.author?.userName || void 0,
            xUsername: e.author?.xUsername ?? void 0,
            profileImage: e.author?.profileImage ?? void 0,
            resolvedAvatarDecoration:
              e.author?.resolvedAvatarDecoration ?? void 0,
            note: i.thesis?.trim() || void 0,
            ...(i.mediaUrl ? { mediaUrl: i.mediaUrl } : {}),
            ...(i.chain ? { chain: i.chain } : {}),
            ...(i.perp ? { perp: i.perp } : {}),
            updates: (0, r.v)({ updates: d, mint: a, calloutId: i.calloutId }),
            updateCount: (0, r.s)({ updates: d, updateCount: i.updateCount }),
          },
        };
      }
      if ("trade" === e.kind || "collectible" === e.kind) {
        let { trade: n } = e;
        return n?.tx && e.coinMint
          ? {
              type: "trade",
              key: `trade:${n.tx}:${e.walletAddress ?? ""}:${e.coinMint}:${n.isBuy ? "buy" : "sell"}`,
              createdAtMs: s(e.createdAt) || s(n.timestamp),
              trade: n,
              author: {
                name: e.author?.userName || null,
                avatarUrl: e.author?.profileImage ?? null,
                avatarDecoration: e.author?.resolvedAvatarDecoration ?? void 0,
                address: u(e) ?? null,
                userId: e.author?.userId ?? null,
                xUsername: e.author?.xUsername ?? null,
              },
              coin: {
                mint: e.coinMint,
                chainId: e.chainId,
                ...o(e.chain),
                name: e.coinName,
                symbol: e.symbol,
                image: e.coinImage,
                marketCapUsd: e.marketCap ?? null,
              },
              card: (0, t.q)(e.coinMint, n.collectible),
            }
          : null;
      }
      if ("reply" === e.kind || "quote" === e.kind) {
        let t = e.reply;
        if (!t?.reply?.id) return null;
        let n = (0, l.j)({
          callout: t.callout,
          parent: t.parent ?? null,
          reply: t.reply,
        });
        return {
          type: e.kind,
          key: `${e.kind}:${t.reply.id}`,
          createdAtMs: s(e.createdAt) || s(t.reply.createdAt),
          row: n,
          coin: c(e, t.callout),
          xUsername: e.author?.xUsername ?? null,
        };
      }
      if ("repost" === e.kind) {
        let t = e.repost;
        return t?.id && t.callout?.callout
          ? {
              type: "repost",
              key: `repost:${t.id}`,
              createdAtMs: s(e.createdAt) || s(t.createdAt),
              reposter: {
                name: e.author?.userName || null,
                avatarUrl: e.author?.profileImage ?? null,
                address: e.author?.walletAddress?.trim() || null,
                xUsername: e.author?.xUsername ?? null,
              },
              callout: (0, l.m)(t.callout),
              coin: c(e, t.callout),
            }
          : null;
      }
      return null;
    },
    D: (e) => {
      let t = (0, i.l)(e);
      return "callout" === e.type
        ? {
            coinMint: e.entry.coinMint,
            chainId: e.chain ?? e.entry.chain ?? e.chainId ?? null,
            perp: t,
          }
        : {
            coinMint: e.coin?.mint ?? "",
            chainId: e.coin?.chain ?? e.coin?.chainId ?? null,
            perp: t,
          };
    },
  };
}
function select(table, key, label) {
  if (typeof key !== "string" || !Object.hasOwn(table, key))
    throw TypeError("explicit supported " + label + " hash required");
  return table[key];
}
export function createFollowingFeedRead({
  readContext,
  imageVariant,
  classificationVariant,
  React,
  useInfiniteQuery,
  useQueryClient,
  getContractClient,
  kindsSchema,
  useFollowingEvents,
  useFirstRowsObserver,
  recordRefresh,
  normalizerHelpers,
  decodeBase58,
  clock,
}) {
  for (const fn of [
    React?.useMemo,
    React?.useState,
    React?.useRef,
    React?.useCallback,
    useInfiniteQuery,
    useQueryClient,
    getContractClient,
    kindsSchema?.parse,
    useFollowingEvents,
    useFirstRowsObserver,
    recordRefresh,
    normalizerHelpers?.g,
    normalizerHelpers?.v,
    normalizerHelpers?.s,
    decodeBase58,
    clock?.now,
  ])
    if (typeof fn !== "function")
      throw TypeError(
        "all explicit following read/runtime/schema/event/observer/helper capabilities required",
      );
  const Date = clock,
    ns = namespace(),
    mint = mintNamespace(),
    perpsChain = "hlcore:mainnet";
  const reader = select(
    {
      bd59c4bee5702bebd7d5a2b91640d9ed9c3170493c0809861e33f4c926744f3d: reader0,
      "3adabf21c26e22024c9c08c3e218b88d0c052d972cf3c25779c1c8efc3350ba2":
        reader1,
    },
    readContext,
    "read context",
  )({ getContractClient, kindsSchema });
  const chains = select(
    {
      bd59c4bee5702bebd7d5a2b91640d9ed9c3170493c0809861e33f4c926744f3d: chain0,
      "3adabf21c26e22024c9c08c3e218b88d0c052d972cf3c25779c1c8efc3350ba2":
        chain1,
    },
    readContext,
    "chain context",
  )({
    namespace: ns,
    mint,
    isSolanaMint: createSolanaGuards({ base58: { decode: decodeBase58 } })
      .validAddress,
    perpsChain,
  });
  const image = select(
    {
      "5eeb70ba118c78cfac5c12f6076086df0d2101d7d7ce07cf076db28b591b992b":
        image0,
      "6e4a4333b2542dd42e35dcc902ca61451ca19e5e6e9643736452979e7d799bfd":
        image1,
    },
    imageVariant,
    "image",
  )();
  const classify = select(
    {
      e3ade9570aef5bef1709871e34a348d5175fede0689284312028c2ca0f7517a4:
        classification0,
      "5dcc6ddfc4d1c08e2852d9903a39eccd09764b4cd4d3d6b71db7a06b5178c5ce":
        classification1,
    },
    classificationVariant,
    "classification",
  )({ mint, shape: isSolanaText, perpsChain });
  const rows = entries({
    normalizerHelpers,
    assets: reader.assets,
    classify,
    namespace: ns,
    collectibleImage: image,
  });
  const ea = rows;
  const ei = { f: useFollowingEvents };
  const ee = { I: 3 };
  const i = React;
  const er = { f: useFirstRowsObserver };
  const es = { Q: recordRefresh };
  const Y = { useQueryClient };
  const eo = chains;
  const en = { r: reader.read, G: reader.kinds };
  const X = { useInfiniteQuery };
  let et = (e, t, l) => ["callouts", "following-alerts", e, t, l];
  let el = (e, t, l, r) => [...et(e, t, l), r];
  let ed = "classic-tab";
  let ec = (e) => {
    let { viewer: t, pageSize: l, chain: r } = e,
      i = (0, eo.m)(r);
    return {
      queryKey: el(t, l, en.G, (0, eo.R)(i)),
      initialPageParam: void 0,
      queryFn: ({ pageParam: e, signal: t }) =>
        (0, en.r)({ pageSize: l, cursor: e, kinds: en.G, ...i, signal: t }),
      getNextPageParam: (e, t, l) => {
        let r = e.nextCursor ?? null;
        if (null !== r && r !== l) return r;
      },
      staleTime: 6e4,
      retry: 3,
    };
  };
  const useFollowingFeed = (e) => {
    let {
        viewer: t,
        enabled: l = !0,
        pageSize: r = 20,
        bufferNewCallouts: a = !1,
        chain: n = "all",
      } = e,
      o = l && null !== t,
      s = ec({ viewer: t, pageSize: r, chain: n }),
      { queryKey: d } = s,
      c = (0, X.useInfiniteQuery)({ ...s, enabled: o }),
      u = (0, i.useMemo)(() => {
        let e = new Set(),
          t = [];
        for (let l of c.data?.pages ?? [])
          for (let r of l.items) {
            let l = (0, ea.o)(r);
            !(!l || e.has(l.key)) &&
              (e.add(l.key), (0, eo.N)((0, ea.D)(l), n) && t.push(l));
          }
        return t;
      }, [c.data, n]),
      m = (0, Y.useQueryClient)();
    (0, er.f)({
      surface: ed,
      enabled: o,
      identity: `${t ?? ""}|${r}|${n}`,
      hasData: void 0 !== c.data,
      itemCount: u.length,
      queryClient: m,
      queryKey: d,
    });
    let [f, p] = (0, i.useState)([]),
      g = (0, i.useRef)(0),
      b = (0, i.useCallback)(
        (e) => {
          let t = m.getQueryData(d),
            l = t?.pages.flatMap((e) => e.items) ?? [];
          if (0 === l.length || !a) {
            let e = Date.now();
            if (e - g.current < 5e3) return;
            ((g.current = e),
              0 === l.length &&
                (0, es.Q)({ surface: ed, path: "empty-refetch" }),
              m.invalidateQueries({ queryKey: d, exact: !0 }));
            return;
          }
          p((t) => (t.some((t) => t.id === e.id) ? t : [...t, e]));
        },
        [a, m, d],
      );
    (0, ei.f)({
      enabled: o,
      viewer: t,
      queryKey: d,
      kinds: en.G,
      surface: ed,
      onNewContent: b,
    });
    let x = `${t ?? ""}|${n}`,
      [h, w] = (0, i.useState)(x);
    h !== x && (w(x), f.length > 0 && p([]), (g.current = 0));
    let y = (0, i.useMemo)(
        () =>
          f
            .flatMap((e) =>
              null === e.coinMint
                ? []
                : [{ key: `evt:${e.id}`, coinMint: e.coinMint }],
            )
            .slice(0, ee.I),
        [f],
      ),
      v = (0, i.useCallback)(
        (e) => {
          if (0 === f.length) return;
          let t = e?.trigger ?? "tap",
            l = Date.now(),
            r = f.reduce((e, t) => Math.min(e, t.receivedAtMs ?? l), l);
          p([]);
          let i = m.getQueryData(d);
          i &&
            i.pages.length > 1 &&
            m.setQueryData(d, {
              pages: i.pages.slice(0, 1),
              pageParams: i.pageParams.slice(0, 1),
            });
          let a = f.length;
          m.invalidateQueries({ queryKey: d, exact: !0 }).then(() => {
            (0, es.Q)({
              surface: ed,
              path: "auto" === t ? "auto-revealed" : "tap-revealed",
              receiptToPaintMs: Date.now() - r,
              pagesRefetched: 1,
              count: a,
            });
          });
        },
        [f, m, d],
      ),
      _ = (0, i.useCallback)(() => {
        c.hasNextPage && !c.isFetchingNextPage && c.fetchNextPage();
      }, [c]);
    return {
      rows: u,
      isLoadingHistory: o && c.isPending,
      error:
        c.isError && void 0 === c.data
          ? "Could not load your following feed"
          : null,
      pendingNewCount: f.length,
      pendingPreview: y,
      showNewCallouts: v,
      hasNextPage: c.hasNextPage ?? !1,
      isFetchingNextPage: c.isFetchingNextPage,
      fetchNextPage: _,
    };
  };
  return {
    useFollowingFeed,
    readAlerts: reader.read,
    queryOptions: ec,
    normalizeEntry: rows.o,
    entryChain: rows.D,
  };
}
