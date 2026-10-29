import { normalizeSearchCoins } from "../search-session/session.mjs";
// Complete selected GO enrichment operations, with explicit query/viewer ports.
function createPolicy(nowMs) {
  const Date = { now: nowMs, parse: globalThis.Date.parse };
  let i = {
    SOL: {
      id: "So11111111111111111111111111111111111111112",
      imageUri:
        "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png",
      mint: "So11111111111111111111111111111111111111112",
      name: "Solana",
      symbol: "SOL",
    },
    USDC: {
      id: "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
      imageUri:
        "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v/logo.png",
      mint: "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
      name: "USD Coin",
      symbol: "USDC",
    },
    PUMP: {
      id: "pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn",
      imageUri: "https://pump.fun/pump-logomark.svg",
      mint: "pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn",
      name: "Pump",
      symbol: "PUMP",
    },
  };
  function o(e) {
    return (
      "open" === e.status &&
      ("WINNER_BY_WINNER" === e.payoutMode || !e.hasResolution)
    );
  }
  return {
    i: i,
    Q: o,
    u: function (e) {
      if ("PENDING_REVIEW" === e.moderationStatus || !o(e)) return !1;
      if (e.expiresAt) {
        let t = Date.parse(e.expiresAt);
        if (Number.isFinite(t) && t <= Date.now()) return !1;
      }
      return !0;
    },
  };
}
function createDisplayMapper(policy) {
  const t = policy;
  let r = t.i.SOL.mint;
  let i = t.i.USDC.mint;
  function a(e) {
    let t = e.trim();
    if (!t) return { summary: "", description: [] };
    let n = t
        .split(/\n\s*\n/)
        .map((e) => e.trim())
        .filter(Boolean),
      r = n[0] ?? t,
      i = r.split("\n", 1)[0]?.trim() ?? r;
    return {
      summary: i.length > 160 ? `${i.slice(0, 157).trimEnd()}…` : i,
      description: n,
    };
  }
  function m(e) {
    let t = e.rewardLegs.flatMap((e) =>
        c({
          amountAtomic: e.amountAtomic,
          decimals: e.decimalsSnapshot,
          mintAddress: e.mintAddress,
          symbolSnapshot: e.symbolSnapshot,
        }),
      ),
      n = e.rewardLegs[0];
    if (!n) return { reward: 0, currency: "USDC", rewardBreakdown: t };
    let s = n.decimalsSnapshot ?? 0,
      o = f(n.amountAtomic ?? "0", s);
    return n.mintAddress === r
      ? { reward: o, currency: "SOL", rewardTokenAmount: o, rewardBreakdown: t }
      : n.mintAddress === i
        ? {
            reward: o,
            currency: "USDC",
            rewardTokenAmount: o,
            rewardBreakdown: t,
          }
        : {
            reward: o,
            currency: "USDC",
            rewardTokenAmount: o,
            rewardToken: n.mintAddress
              ? {
                  id: n.mintAddress,
                  mint: n.mintAddress,
                  name: n.symbolSnapshot ?? n.mintAddress,
                  symbol: n.symbolSnapshot ?? n.mintAddress.slice(0, 4),
                  imageUri: "",
                }
              : void 0,
            rewardBreakdown: t,
          };
  }
  function c(e) {
    let n = f(e.amountAtomic ?? "0", e.decimals ?? 0);
    if (n <= 0) return [];
    switch (e.mintAddress) {
      case r:
        return [{ amount: n, currency: "SOL", token: { ...t.i.SOL } }];
      case i:
        return [{ amount: n, currency: "USDC", token: { ...t.i.USDC } }];
      default:
        return [
          {
            amount: n,
            currency: "USDC",
            token: e.mintAddress
              ? {
                  id: e.mintAddress,
                  mint: e.mintAddress,
                  name: e.symbolSnapshot ?? e.mintAddress,
                  symbol: e.symbolSnapshot ?? e.mintAddress.slice(0, 4),
                  imageUri: "",
                }
              : void 0,
          },
        ];
    }
  }
  function f(e, t) {
    if (!/^\d+$/.test(e)) return 0;
    if (t <= 0) {
      let t = Number(e);
      return Number.isFinite(t) ? t : 0;
    }
    let n = e.padStart(t + 1, "0"),
      r = n.slice(0, n.length - t),
      i = n.slice(n.length - t),
      s = Number(`${r}.${i}`);
    return Number.isFinite(s) ? s : 0;
  }
  function u(e) {
    return "CLOSED" === e.status
      ? e.resolution?.outcomeType === "WINNER_PAYOUT" ||
        e.resolution?.outcomeType === "SPLIT"
        ? "done"
        : "closed"
      : "open";
  }
  function l(e) {
    let t = Date.parse(e);
    return Number.isNaN(t) ? e : new Date(t + 6048e5).toISOString();
  }
  function w(e, t) {
    let n = t?.username?.trim(),
      r = t?.userId;
    return {
      address: e,
      id: t?.address ?? e,
      ...(r ? { creatorUserId: r } : {}),
      username: n && n.length > 0 ? n : null,
      profileImage: t?.profile_image ?? "",
      rating: 0,
    };
  }
  function p(e, t) {
    if (e)
      return {
        id: e,
        mint: e,
        name: t?.name ?? e,
        symbol: t?.symbol ?? e.slice(0, 4),
        imageUri: t?.imageUri ?? "",
      };
  }
  function o(e) {
    let t = e?.winnerCount;
    if (!e?.winners?.length) return { total: t ?? 0, claimed: 0 };
    let n = new Set(),
      r = 0;
    for (let t of e.winners) {
      let e = `${t.submissionId}|${t.mintAddress}`;
      !n.has(e) && (n.add(e), t.claimedAt && r++);
    }
    return { total: t ?? n.size, claimed: r };
  }
  function d(e) {
    if (
      !e.viewerAddress ||
      e.viewerAddress.toLowerCase() !== e.creatorAddress.toLowerCase()
    )
      return "none";
    let t = e.resolution;
    if (!t || ("REFUND" !== t.outcomeType && "SPLIT" !== t.outcomeType))
      return "none";
    let n = t.refundClaims ?? [],
      r = e.viewerAddress.toLowerCase();
    return n.some((e) => e.depositor.toLowerCase() === r)
      ? "claimed"
      : "pending";
  }
  return function (e, n = {}) {
    let { summary: r, description: i } = a(e.bodyMarkdown),
      s = [...e.criteria].sort((e, t) => e.order - t.order).map((e) => e.text),
      c = m({ rewardLegs: e.rewardLegs }),
      f = u({ status: e.status, resolution: e.resolution }),
      b = e.expiresAt ?? l(e.createdAt),
      A = e.publishedAt ?? e.fundedAt ?? e.createdAt,
      h = !!e.resolution,
      g = (0, t.u)({
        status: f,
        expiresAt: b,
        hasResolution: h,
        moderationStatus: e.moderationStatus,
        payoutMode: e.payoutMode,
      }),
      y = (0, t.Q)({ status: f, hasResolution: h, payoutMode: e.payoutMode }),
      S = w(e.creatorAddress, n.creatorUser),
      U = p(e.coinAddress, n.coinMeta),
      $ = o(e.resolution),
      k = !!(
        n.viewerAddress &&
        n.viewerAddress.toLowerCase() === e.creatorAddress.toLowerCase()
      ),
      v = d({
        resolution: e.resolution,
        viewerAddress: n.viewerAddress,
        creatorAddress: e.creatorAddress,
      });
    return {
      id: e.taskId,
      title: e.title,
      summary: r,
      tags: [],
      description: i,
      descriptionMarkdown: e.bodyMarkdown.trim(),
      deliverables: s,
      rewardDistribution: e.rewardDistribution,
      reward: c.reward,
      currency: c.currency,
      rewardTokenAmount: c.rewardTokenAmount,
      rewardToken: c.rewardToken,
      rewardBreakdown: c.rewardBreakdown,
      status: f,
      createdAt: A,
      expiresAt: b,
      submissionCount: e.counts.submissionCount,
      creator: S,
      token: U,
      attachments: e.attachments ?? [],
      acceptsSubmissions: g,
      allowsSubmissionMutations: y,
      likeCount: e.likeCount,
      viewerLiked: e.viewerLiked,
      winnerCount: $.total,
      claimedWinnerCount: $.claimed,
      viewerIsCreator: k,
      refundStatus: v,
      resolution: e.resolution,
      moderationStatus: e.moderationStatus,
      banInfo: e.banInfo,
      unbanInfo: e.unbanInfo,
      isNsfw: e.isNsfw,
      nsfwInfo: e.nsfwInfo,
      unNsfwInfo: e.unNsfwInfo,
      rewardTotalUsd: e.rewardTotalUsd,
      rewardLegsUsd: e.rewardLegsUsd,
      rewardPricedAt: e.rewardPricedAt,
      rewardLegSnapshots: e.rewardLegs.map((e) => ({
        mintAddress: e.mintAddress,
        decimalsSnapshot: e.decimalsSnapshot,
      })),
    };
  };
}
function createCoinResultHook(ports) {
  const t = { c: ports.memoCache };
  const r = { V: ports.useCoinQuery };
  const a = { useIpfsPrefix: ports.useIpfsPrefix };
  const i = { f: normalizeSearchCoins };
  return (e) => {
    let s,
      l,
      o,
      n,
      d,
      u,
      c,
      f,
      m,
      p,
      v,
      h,
      y,
      x = (0, t.c)(32);
    x[0] !== e
      ? (({
          mints: s,
          limit: o,
          offset: n,
          sort: d,
          order: u,
          includeNsfw: c,
          disabled: f,
          ...l
        } = e),
        (x[0] = e),
        (x[1] = s),
        (x[2] = l),
        (x[3] = o),
        (x[4] = n),
        (x[5] = d),
        (x[6] = u),
        (x[7] = c),
        (x[8] = f))
      : ((s = x[1]),
        (l = x[2]),
        (o = x[3]),
        (n = x[4]),
        (d = x[5]),
        (u = x[6]),
        (c = x[7]),
        (f = x[8]));
    let g = void 0 === o ? 50 : o,
      w = void 0 === n ? 0 : n,
      b = void 0 === d ? "market_cap" : d,
      N = void 0 === u ? "DESC" : u,
      j = void 0 !== c && c,
      R = void 0 !== f && f,
      { ipfsPrefix: S } = (0, a.useIpfsPrefix)();
    x[9] !== R ||
    x[10] !== j ||
    x[11] !== g ||
    x[12] !== w ||
    x[13] !== N ||
    x[14] !== l ||
    x[15] !== b
      ? ((m = {
          limit: g,
          offset: w,
          sort: b,
          order: N,
          includeNsfw: j,
          disabled: R,
          ...l,
        }),
        (x[9] = R),
        (x[10] = j),
        (x[11] = g),
        (x[12] = w),
        (x[13] = N),
        (x[14] = l),
        (x[15] = b),
        (x[16] = m))
      : (m = x[16]);
    let {
      data: C,
      isLoading: A,
      error: F,
      refetch: _,
      isError: k,
      isLoadingError: M,
    } = (0, r.V)(s, m);
    x[17] !== C
      ? ((p = void 0 === C ? [] : C), (x[17] = C), (x[18] = p))
      : (p = x[18]);
    let T = p;
    e: {
      let e;
      if (!T.length) {
        let e;
        (x[19] === Symbol.for("react.memo_cache_sentinel")
          ? ((e = []), (x[19] = e))
          : (e = x[19]),
          (v = e));
        break e;
      }
      (x[20] !== S || x[21] !== T
        ? ((e = (0, i.f)(T, S)), (x[20] = S), (x[21] = T), (x[22] = e))
        : (e = x[22]),
        (v = e));
    }
    let E = v;
    x[23] !== F
      ? ((h = F ? (F instanceof Error ? F : Error(String(F))) : null),
        (x[23] = F),
        (x[24] = h))
      : (h = x[24]);
    let I = h;
    return (
      x[25] !== E ||
      x[26] !== I ||
      x[27] !== k ||
      x[28] !== M ||
      x[29] !== A ||
      x[30] !== _
        ? ((y = {
            coins: E,
            loading: A,
            error: I,
            refetch: _,
            isError: k,
            isLoadingError: M,
          }),
          (x[25] = E),
          (x[26] = I),
          (x[27] = k),
          (x[28] = M),
          (x[29] = A),
          (x[30] = _),
          (x[31] = y))
        : (y = x[31]),
      y
    );
  };
}
function createTokenHook(ports, useCoinResult) {
  const t = { c: ports.memoCache };
  const n = { f: useCoinResult };
  function r(e) {
    return [e.mint, e];
  }
  function i(e) {
    return e.mint;
  }
  function s(e) {
    return !!e;
  }
  return function (e) {
    let o,
      d,
      a,
      u,
      l,
      m = (0, t.c)(13);
    m[0] !== e ? ((o = e.filter(s)), (m[0] = e), (m[1] = o)) : (o = m[1]);
    let c = o;
    m[2] !== c
      ? ((d = Array.from(new Set(c.map(i))).filter(Boolean)),
        (m[2] = c),
        (m[3] = d))
      : (d = m[3]);
    let f = d,
      w = 0 === f.length;
    m[4] !== f || m[5] !== w
      ? ((a = { mints: f, disabled: w }), (m[4] = f), (m[5] = w), (m[6] = a))
      : (a = m[6]);
    let { coins: p, loading: b } = (0, n.f)(a);
    if (m[7] !== p || m[8] !== c) {
      let e = new Map(p.map(r));
      ((u = new Map(
        c.map((t) => {
          let n = e.get(t.mint),
            r = n?.usd_market_cap || n?.market_cap || 0,
            i = n?.total_supply
              ? Number(n.total_supply) / 10 ** (n.base_decimals ?? 6)
              : 0;
          return [
            t.mint,
            {
              ...t,
              liveMarketCap: r,
              liveName: n?.name?.trim() || t.name,
              liveSymbol: n?.symbol?.trim() || t.symbol,
              liveImageUri: n?.image_uri || t.imageUri,
              livePriceUsd: i > 0 ? r / i : 0,
            },
          ];
        }),
      )),
        (m[7] = p),
        (m[8] = c),
        (m[9] = u));
    } else u = m[9];
    let A = u,
      h = f.length > 0 && b;
    return (
      m[10] !== A || m[11] !== h
        ? ((l = { liveTokens: A, isLoading: h }),
          (m[10] = A),
          (m[11] = h),
          (m[12] = l))
        : (l = m[12]),
      l
    );
  };
}
function createEnrichmentHooks(ports, useTokens, mapBounty, policy) {
  const t = { c: ports.memoCache };
  const r = { F: ports.useViewerSnapshot };
  const n = { f: ports.useBatchProfiles };
  const i = { m: mapBounty };
  const s = policy;
  const a = { f: useTokens };
  function o(e) {
    let t = new Map(),
      r = (e) => {
        !e ||
          t.has(e) ||
          [s.i.SOL.mint, s.i.USDC.mint].includes(e) ||
          t.set(e, {
            id: e,
            mint: e,
            name: e,
            symbol: e.slice(0, 4),
            imageUri: "",
          });
      };
    for (let t of e)
      for (let e of (r(t.coinAddress), t.rewardLegs ?? [])) r(e.mintAddress);
    return [...t.values()];
  }
  return {
    useEnrichedBounties: function (e) {
      let s,
        l,
        u,
        d,
        c,
        f,
        m = (0, t.c)(21),
        { address: p } = (0, r.F)();
      m[0] !== e ? ((s = o(e)), (m[0] = e), (m[1] = s)) : (s = m[1]);
      let w = s,
        { liveTokens: g, isLoading: b } = (0, a.f)(w);
      m[2] !== e
        ? ((l = (function (e) {
            let t = new Set();
            for (let r of e) r.creatorAddress && t.add(r.creatorAddress);
            return [...t];
          })(e)),
          (m[2] = e),
          (m[3] = l))
        : (l = m[3]);
      let h = l;
      m[4] !== h
        ? ((u = { userAddresses: h }), (m[4] = h), (m[5] = u))
        : (u = m[5]);
      let { data: v, isPending: y } = (0, n.f)(u);
      if (m[6] !== v) {
        for (let e of ((d = new Map()), v ?? [])) d.set(e.address, e);
        ((m[6] = v), (m[7] = d));
      } else d = m[7];
      let x = d;
      if (m[8] !== g || m[9] !== e || m[10] !== x || m[11] !== p) {
        let t;
        (m[13] !== g || m[14] !== x || m[15] !== p
          ? ((t = (e) => {
              let t = e.coinAddress ? g.get(e.coinAddress) : void 0;
              return (0, i.m)(e, {
                creatorUser: x.get(e.creatorAddress),
                coinMeta: t
                  ? {
                      mint: t.mint,
                      name: t.liveName,
                      symbol: t.liveSymbol,
                      imageUri: t.liveImageUri,
                    }
                  : void 0,
                viewerAddress: p ?? void 0,
              });
            }),
            (m[13] = g),
            (m[14] = x),
            (m[15] = p),
            (m[16] = t))
          : (t = m[16]),
          (c = e.map(t)),
          (m[8] = g),
          (m[9] = e),
          (m[10] = x),
          (m[11] = p),
          (m[12] = c));
      } else c = m[12];
      let S = c,
        N = (h.length > 0 && y) || (w.length > 0 && b);
      return (
        m[17] !== S || m[18] !== N || m[19] !== g
          ? ((f = { bounties: S, liveTokens: g, isEnriching: N }),
            (m[17] = S),
            (m[18] = N),
            (m[19] = g),
            (m[20] = f))
          : (f = m[20]),
        f
      );
    },
    useBountyTokens: function (e) {
      let r,
        n = (0, t.c)(2);
      n[0] !== e ? ((r = o([...e])), (n[0] = e), (n[1] = r)) : (r = n[1]);
      let i = r;
      return (0, a.f)(i).liveTokens;
    },
  };
}
export function createBountyEnrichment(ports) {
  for (const name of [
    "memoCache",
    "useViewerSnapshot",
    "useBatchProfiles",
    "useCoinQuery",
    "useIpfsPrefix",
    "nowMs",
  ])
    if (typeof ports?.[name] !== "function")
      throw new TypeError("Explicit enrichment capability required: " + name);
  const policy = createPolicy(ports.nowMs),
    mapBounty = createDisplayMapper(policy),
    useCoinResult = createCoinResultHook(ports),
    useTokens = createTokenHook(ports, useCoinResult);
  return {
    ...createEnrichmentHooks(ports, useTokens, mapBounty, policy),
    mapBounty,
  };
}
