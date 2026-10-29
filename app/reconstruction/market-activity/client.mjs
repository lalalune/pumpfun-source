// Source-bound editable activity operations. No implicit destination or provider.
export const ACTIVITY_CONFIG = {
  INTERVALS: ["5m", "1h", "6h", "24h"],
  METRICS: ["numTxs", "volumeUSD", "numUsers", "priceChangePercent"],
  STALE_TIME: 3e5,
  CACHE_TIME: 6e5,
  POLLING_INTERVAL: 3e4,
  QUERY_KEY: "marketActivity",
  BATCH_SIZE: 50,
};
export const isSolanaActivityAddress = (() => {
  let t = /^[1-9A-HJ-NP-Za-km-z]+$/;
  return (e) => {
    let r = e.trim();
    return !(r.length < 32) && !(r.length > 44) && t.test(r);
  };
})();
export const isEvmActivityAddress = function (e) {
  return "string" == typeof e && /^0x[0-9a-fA-F]{40}$/.test(e);
};
export const normalizeMarketActivity = (() => {
  let t = ["volumeUSD", "buyVolumeUSD", "sellVolumeUSD"];
  function r(e) {
    let t =
      "number" == typeof e
        ? e
        : "string" == typeof e && "" !== e.trim()
          ? Number(e)
          : 0 / 0;
    return !Number.isFinite(t) || t < 0 || t > 1e12 ? null : t;
  }
  function n(e) {
    if (!e || "object" != typeof e) return null;
    let n = { ...e };
    for (let a of t) n[a] = r(e[a]);
    return n;
  }
  function a(e) {
    let t = e && "object" == typeof e ? e : {};
    return {
      "5m": n(t["5m"]),
      "1h": n(t["1h"]),
      "6h": n(t["6h"]),
      "24h": n(t["24h"]),
    };
  }
  return function (e) {
    if (!e || "object" != typeof e) return {};
    let t = {};
    for (let [r, n] of Object.entries(e)) t[r] = a(n);
    return t;
  };
})();
const batchOperations = (() => {
  const r = ACTIVITY_CONFIG;
  return {
    split: function (e, t = r.BATCH_SIZE) {
      if (!e || 0 === e.length) return [];
      let n = Array.from(new Set(e)).filter(Boolean).sort(),
        l = [];
      for (let e = 0; e < n.length; e += t) l.push(n.slice(e, e + t));
      return l;
    },
    merge: function (e) {
      if (!e || 0 === e.length) return {};
      let t = {};
      return (
        e.forEach((e) => {
          e && "object" == typeof e && Object.assign(t, e);
        }),
        t
      );
    },
  };
})();
export const splitActivityBatches = batchOperations.split;
export const mergeActivityBatches = batchOperations.merge;
export function createMarketActivityModule({
  getBaseUrl,
  fetchActivity,
  logger,
  useMemoCache,
  useQueryClient,
  useQueries,
  useMutation,
}) {
  for (const [name, value] of Object.entries({
    getBaseUrl,
    fetchActivity,
    useMemoCache,
    useQueryClient,
    useQueries,
    useMutation,
  }))
    if (typeof value !== "function")
      throw new TypeError("Explicit activity capability required: " + name);
  if (typeof logger?.warn !== "function")
    throw new TypeError("Explicit activity logger.warn required");
  const t = { c: useMemoCache },
    r = { y: logger },
    n = { k: isSolanaActivityAddress },
    l = { f: useMutation },
    i = { f: useQueries },
    u = { useQueryClient: useQueryClient },
    a = { f: fetchActivity },
    s = { V: getBaseUrl },
    o = { h: isEvmActivityAddress },
    c = { f: normalizeMarketActivity },
    f = {
      t: ACTIVITY_CONFIG,
      $: splitActivityBatches,
      d: mergeActivityBatches,
    };
  let d = (e) => (0, n.k)(e) || (0, o.h)(e);
  async function h(e, t) {
    let n = (e ?? []).filter(d);
    if (0 === n.length) return {};
    let l = t?.intervals || f.t.INTERVALS,
      i = t?.metrics || f.t.METRICS;
    try {
      let e = await (0, a.f)(`${(0, s.V)()}/coins/market-activity/batch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ addresses: n, intervals: l, metrics: i }),
        signal: t?.signal,
      });
      if (!e.ok)
        throw Error(`Failed to fetch batch market activity: ${e.status}`);
      return (0, c.f)(await e.json());
    } catch (e) {
      return (
        r.y.warn("Error fetching market activity", {
          error: e,
          mintCount: n.length,
        }),
        {}
      );
    }
  }
  function E(e) {
    return e.data;
  }
  function y(e) {
    return e.isPending;
  }
  function m(e) {
    return e.error;
  }
  function g(e) {
    return { data: e.map(E), pending: e.some(y), error: e.find(m)?.error };
  }
  return {
    isActivityAddress: d,
    readMarketActivity: h,
    useMarketActivity: (e, r) => {
      let n,
        a,
        s,
        o,
        c,
        E,
        y,
        m,
        S,
        p = (0, t.c)(31);
      p[0] !== r
        ? ((n = void 0 === r ? {} : r), (p[0] = r), (p[1] = n))
        : (n = p[1]);
      let { shouldFetch: w, enablePolling: k, pollingInterval: b } = n,
        T = void 0 === w || w,
        v = void 0 !== k && k,
        C = void 0 === b ? f.t.POLLING_INTERVAL : b,
        A = (0, u.useQueryClient)();
      p[2] !== e
        ? ((a = (0, f.$)(e.filter(d), f.t.BATCH_SIZE)), (p[2] = e), (p[3] = a))
        : (a = p[3]);
      let R = a;
      if (p[4] !== v || p[5] !== R || p[6] !== C || p[7] !== T) {
        let e;
        (p[9] !== v || p[10] !== C || p[11] !== T
          ? ((e = (e) => ({
              queryKey: [f.t.QUERY_KEY, e.join(",")],
              queryFn: () =>
                h(e, { intervals: f.t.INTERVALS, metrics: f.t.METRICS }),
              enabled: T && e.length > 0,
              staleTime: f.t.STALE_TIME,
              gcTime: f.t.CACHE_TIME,
              refetchOnMount: !1,
              refetchOnWindowFocus: !1,
              refetchOnReconnect: !1,
              retry: !1,
              refetchInterval: !!v && C,
            })),
            (p[9] = v),
            (p[10] = C),
            (p[11] = T),
            (p[12] = e))
          : (e = p[12]),
          (s = R.map(e)),
          (p[4] = v),
          (p[5] = R),
          (p[6] = C),
          (p[7] = T),
          (p[8] = s));
      } else s = p[8];
      let I = s;
      p[13] !== I
        ? ((o = { queries: I, combine: g }), (p[13] = I), (p[14] = o))
        : (o = p[14]);
      let O = (0, i.f)(o);
      p[15] !== A
        ? ((c = {
            mutationFn: async (e) => {
              let t = await h(e, {
                intervals: f.t.INTERVALS,
                metrics: f.t.METRICS,
              });
              return (A.setQueryData([f.t.QUERY_KEY, e.join(",")], t), t);
            },
          }),
          (p[15] = A),
          (p[16] = c))
        : (c = p[16]);
      let { mutate: M } = (0, l.f)(c);
      p[17] !== R || p[18] !== M
        ? ((E = (e) => {
            if (!e.length) return;
            let t = Array.from(new Set(e));
            R.filter((e) => e.some((e) => t.includes(e))).forEach((e) => M(e));
          }),
          (p[17] = R),
          (p[18] = M),
          (p[19] = E))
        : (E = p[19]);
      let L = E;
      p[20] !== O.data
        ? ((y = (0, f.d)(O.data)), (p[20] = O.data), (p[21] = y))
        : (y = p[21]);
      let N = y,
        j = O.pending,
        D = O.error;
      p[22] !== R || p[23] !== A
        ? ((m = () => {
            R.length &&
              R.forEach((e) => {
                A.invalidateQueries({ queryKey: [f.t.QUERY_KEY, e.join(",")] });
              });
          }),
          (p[22] = R),
          (p[23] = A),
          (p[24] = m))
        : (m = p[24]);
      let P = m;
      return (
        p[25] !== D || p[26] !== P || p[27] !== j || p[28] !== N || p[29] !== L
          ? ((S = {
              marketActivity: N,
              loading: j,
              error: D,
              refetchMints: L,
              invalidateCache: P,
            }),
            (p[25] = D),
            (p[26] = P),
            (p[27] = j),
            (p[28] = N),
            (p[29] = L),
            (p[30] = S))
          : (S = p[30]),
        S
      );
    },
  };
}
