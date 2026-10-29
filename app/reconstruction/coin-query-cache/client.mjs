// Generated from selected captured ASTs; no bundle/runtime evaluation.
import { readSearchCoins } from "../search-session/session.mjs";
export function createCoinQuery({
  useMemoCache,
  useQuery,
  useQueryClient,
  getContractClient,
  clock,
}) {
  for (const [name, value] of Object.entries({
    useMemoCache,
    useQuery,
    useQueryClient,
    getContractClient,
  }))
    if (typeof value !== "function")
      throw TypeError(name + " capability required");
  if (typeof clock?.now !== "function")
    throw TypeError("clock.now capability required");
  const Date = clock;
  const t = { c: useMemoCache };
  const v = {
    c: function (e) {
      return e.startsWith("0x") ? e.toLowerCase() : e;
    },
  };
  const n = { useQueryClient };
  const m = (() => {
    const i = "ton:-239";
    const a = "starknet:SN_MAIN";
    const d = "near:mainnet";
    return { L: (e) => e === i, B: (e) => e === d, _: (e) => e === a };
  })();
  const r = { useQuery };
  const d = { j: getContractClient };
  const i = { l: readSearchCoins };
  const T = 6e4;
  const S = 12e4;
  const M = {
    coin: (e) => ["coin", e],
    coinsByMints: (e, t = !1) => [
      "coinsByMints",
      t ? "nsfw" : "safe",
      ...[...e].sort(),
    ],
  };
  const D = async (e, t) => {
    if (!e || 0 === e.length) return [];
    t?.includeNsfw;
    {
      let t = await (0, d.j)()("POST /coins-v2/mints", {
        body: { mints: e },
        credentials: "include",
        hooks: {
          afterResponse: [
            (e, t, r) => {
              if (!r.ok) throw Error(`Failed to fetch coins: ${r.statusText}`);
            },
          ],
        },
      });
      return (0, i.l)(t);
    }
  };
  const useCoins = (e, a) => {
    let i,
      s,
      o,
      l,
      u,
      d,
      c,
      f,
      h,
      p,
      y,
      w,
      g,
      b,
      _ = (0, t.c)(52);
    (_[0] !== a
      ? ((i = void 0 === a ? {} : a), (_[0] = a), (_[1] = i))
      : (i = _[1]),
      _[2] !== i
        ? (({
            limit: o,
            offset: l,
            sort: u,
            order: d,
            includeNsfw: c,
            disabled: f,
            ...s
          } = i),
          (_[2] = i),
          (_[3] = s),
          (_[4] = o),
          (_[5] = l),
          (_[6] = u),
          (_[7] = d),
          (_[8] = c),
          (_[9] = f))
        : ((s = _[3]),
          (o = _[4]),
          (l = _[5]),
          (u = _[6]),
          (d = _[7]),
          (c = _[8]),
          (f = _[9])));
    let A = void 0 !== c && c,
      k = void 0 !== f && f,
      C = (0, n.useQueryClient)();
    e: {
      let t, r, n, a;
      if (!e.length || k) {
        let e;
        (_[10] === Symbol.for("react.memo_cache_sentinel")
          ? ((e = {
              cachedCoins: [],
              staleCoins: [],
              missingMints: [],
              hasCachedData: !1,
              hasNewMints: !1,
            }),
            (_[10] = e))
          : (e = _[10]),
          (h = e));
        break e;
      }
      if (A) {
        let t, r, n;
        _[11] === Symbol.for("react.memo_cache_sentinel")
          ? ((r = []), (t = []), (_[11] = t), (_[12] = r))
          : ((t = _[11]), (r = _[12]));
        let a = e.length > 0;
        (_[13] !== e || _[14] !== a
          ? ((n = {
              cachedCoins: r,
              staleCoins: t,
              missingMints: e,
              hasCachedData: !1,
              hasNewMints: a,
            }),
            (_[13] = e),
            (_[14] = a),
            (_[15] = n))
          : (n = _[15]),
          (h = n));
        break e;
      }
      if (_[16] !== e || _[17] !== C) {
        let a = null,
          i = (e) => {
            if (!a)
              for (let e of ((a = new Map()),
              C.getQueryCache().findAll({ queryKey: ["coin"] }))) {
                let { queryKey: t } = e;
                if (2 !== t.length || "string" != typeof t[1]) continue;
                let r = e.state.data;
                if (!r || "string" != typeof r.mint) continue;
                let n = (0, v.c)(t[1]),
                  i = a.get(n);
                (i && i.dataUpdatedAt >= e.state.dataUpdatedAt) ||
                  a.set(n, { coin: r, dataUpdatedAt: e.state.dataUpdatedAt });
              }
            return a.get((0, v.c)(e));
          };
        ((t = []), (n = []), (r = []));
        let s = Date.now();
        for (let a of e) {
          let e = C.getQueryState(M.coin(a)),
            o =
              e?.data !== void 0
                ? { coin: e.data, dataUpdatedAt: e.dataUpdatedAt }
                : a.startsWith("0x")
                  ? i(a)
                  : void 0;
          if (!o) {
            r.push(a);
            continue;
          }
          !(s - o.dataUpdatedAt > T) ||
          (0, m.L)(o.coin.chain_id) ||
          (0, m.B)(o.coin.chain_id) ||
          (0, m._)(o.coin.chain_id)
            ? t.push(o.coin)
            : (n.push(o.coin), r.push(a));
        }
        ((_[16] = e), (_[17] = C), (_[18] = t), (_[19] = r), (_[20] = n));
      } else ((t = _[18]), (r = _[19]), (n = _[20]));
      let i = t.length > 0,
        s = r.length > 0;
      (_[21] !== t || _[22] !== r || _[23] !== n || _[24] !== s || _[25] !== i
        ? ((a = {
            cachedCoins: t,
            staleCoins: n,
            missingMints: r,
            hasCachedData: i,
            hasNewMints: s,
          }),
          (_[21] = t),
          (_[22] = r),
          (_[23] = n),
          (_[24] = s),
          (_[25] = i),
          (_[26] = a))
        : (a = _[26]),
        (h = a));
    }
    let E = h;
    (_[27] !== E.missingMints || _[28] !== A
      ? ((p = M.coinsByMints(E.missingMints, A)),
        (_[27] = E.missingMints),
        (_[28] = A),
        (_[29] = p))
      : (p = _[29]),
      _[30] !== E.missingMints || _[31] !== A || _[32] !== C
        ? ((y = async () => {
            if (0 === E.missingMints.length) return [];
            let e = await D(E.missingMints, { includeNsfw: A });
            return (
              e.forEach((e) => {
                C.setQueryData(M.coin(e.mint), e);
              }),
              e
            );
          }),
          (_[30] = E.missingMints),
          (_[31] = A),
          (_[32] = C),
          (_[33] = y))
        : (y = _[33]));
    let U = E.hasNewMints && !k;
    _[34] !== s || _[35] !== y || _[36] !== U || _[37] !== p
      ? ((w = {
          queryKey: p,
          queryFn: y,
          enabled: U,
          staleTime: T,
          gcTime: S,
          ...s,
        }),
        (_[34] = s),
        (_[35] = y),
        (_[36] = U),
        (_[37] = p),
        (_[38] = w))
      : (w = _[38]);
    let N = (0, r.useQuery)(w);
    if (
      _[39] !== N.data ||
      _[40] !== E.cachedCoins ||
      _[41] !== E.staleCoins ||
      _[42] !== e
    ) {
      let t = N.data || [],
        r = [...E.staleCoins, ...E.cachedCoins, ...t],
        n = new Map();
      (r.forEach((e) => {
        n.set((0, v.c)(e.mint), e);
      }),
        (g = e.map((e) => n.get((0, v.c)(e))).filter(Boolean)),
        (_[39] = N.data),
        (_[40] = E.cachedCoins),
        (_[41] = E.staleCoins),
        (_[42] = e),
        (_[43] = g));
    } else g = _[43];
    let j = g,
      O = !!E.hasNewMints && j.length < e.length && N.isLoading,
      I = N.error,
      $ = !O && !I;
    return (
      _[44] !== j ||
      _[45] !== N.isError ||
      _[46] !== N.isLoadingError ||
      _[47] !== N.refetch ||
      _[48] !== I ||
      _[49] !== O ||
      _[50] !== $
        ? ((b = {
            data: j,
            isLoading: O,
            error: I,
            isSuccess: $,
            refetch: N.refetch,
            isError: N.isError,
            isLoadingError: N.isLoadingError,
          }),
          (_[44] = j),
          (_[45] = N.isError),
          (_[46] = N.isLoadingError),
          (_[47] = N.refetch),
          (_[48] = I),
          (_[49] = O),
          (_[50] = $),
          (_[51] = b))
        : (b = _[51]),
      b
    );
  };
  return { useCoins, readCoins: D };
}
