// Complete source-bound query/store translation. Runtime and existing helpers are injected ports.
export const queryVariants = [
  {
    source: "evidence/web/objects/dba17a249156c6ff.js",
    sha256: "704bb073aaf4230b6cac309756c284803fe7d3cc4e2776a060d041af2341a786",
  },
  {
    source: "evidence/web/objects/ecf7ec803bfb3020.js",
    sha256: "dff1b5f10ee3af571bcc7fa3b0a7e8a0ec4b9eedc58a4cc3526600590f1529b4",
  },
  {
    source: "evidence/web/objects/9535b69d76e2a69b.js",
    sha256: "d9ab130a7e21782f4e8a294f011c25405d3690ef4aafcc5bcc5bdabd656a414b",
  },
];
export const storeVariants = [
  {
    source: "evidence/web/objects/dba17a249156c6ff.js",
    sha256: "c57dd65e642700694b2b65e1554a0d11ac5caca8b535bfa1062564366e344d61",
  },
  {
    source: "evidence/web/objects/ecf7ec803bfb3020.js",
    sha256: "4d8d931c538e4d5825c61fd3a88195ed022fb5aea372113ac4f31b594b2ada62",
  },
  {
    source: "evidence/web/objects/9535b69d76e2a69b.js",
    sha256: "8d033eb75f35cf9896bac25b3e151d4e7057dacd759e61c880aa24e1e52b1022",
  },
  {
    source: "evidence/web/objects/0e0a55c249b456d7.js",
    sha256: "7eeb7e121092f1cac917f25c0d222d0e79932ce86d62cb01a73e90cb541781e0",
  },
  {
    source: "evidence/web/objects/1681353d046eeca6.js",
    sha256: "90cc0b7b37585830da582b2f52fe2177074ed20f613713e894858b23a8d34a12",
  },
];
function store0({ createBoundStore, subscribeWithSelector, createBatch }) {
  const t = { $: createBoundStore };
  const r = { u: subscribeWithSelector };
  const n = { H: createBatch };
  let l = (e, t) => {
    let r = { ...e };
    for (let [e, n] of Object.entries(t)) null != n && (r[e] = n);
    return r;
  };
  let i = (e, t) => {
    if (!e) return t;
    let r = { ...e };
    for (let n of Object.keys(t)) {
      let i = t[n],
        u = e[n];
      r[n] = i && u ? l(u, i) : i;
    }
    return r;
  };
  let u = (e, t) => {
    let r;
    for (let n of Object.keys(t)) {
      let l = e[n],
        i = t[n];
      if (!l || !i) continue;
      let u = {};
      for (let [e, t] of Object.entries(i))
        null != t && (null === l[e] || void 0 === l[e]) && (u[e] = t);
      0 !== Object.keys(u).length && ((r ??= {})[n] = u);
    }
    return r;
  };
  let a = (0, t.$)()(
    (0, r.u)((e, t) => {
      let r = (0, n.H)({
        merge: i,
        onFlush: (t) =>
          e((e) => {
            let r = { ...e.marketActivity };
            for (let [n, l] of t) r[n] = i(e.marketActivity[n], l);
            return { marketActivity: r };
          }),
      });
      return {
        marketActivity: {},
        setMarketActivity: (e) => {
          for (let [t, n] of Object.entries(e)) r.set(t, n);
        },
        seedMarketActivity: (e) => {
          let { marketActivity: n } = t();
          for (let [t, l] of Object.entries(e)) {
            let e = r.peek(t),
              a = e ? i(n[t], e) : n[t];
            if (!a) {
              r.set(t, l);
              continue;
            }
            let s = u(a, l);
            s && r.set(t, s);
          }
        },
        clearMarketActivity: () => {
          (r.clear(), e({ marketActivity: {} }));
        },
      };
    }),
  );
  return {
    setMarketActivity: (e) => {
      a.getState().setMarketActivity(e);
    },
    seedMarketActivity: (e) => {
      a.getState().seedMarketActivity(e);
    },
    store: a,
  };
}
function store1({ createBoundStore, subscribeWithSelector, createBatch }) {
  const t = { $: createBoundStore };
  const r = { u: subscribeWithSelector };
  const a = { H: createBatch };
  let i = (e, t) => {
    let r = { ...e };
    for (let [e, a] of Object.entries(t)) null != a && (r[e] = a);
    return r;
  };
  let n = (e, t) => {
    if (!e) return t;
    let r = { ...e };
    for (let a of Object.keys(t)) {
      let n = t[a],
        l = e[a];
      r[a] = n && l ? i(l, n) : n;
    }
    return r;
  };
  let l = (e, t) => {
    let r;
    for (let a of Object.keys(t)) {
      let i = e[a],
        n = t[a];
      if (!i || !n) continue;
      let l = {};
      for (let [e, t] of Object.entries(n))
        null != t && (null === i[e] || void 0 === i[e]) && (l[e] = t);
      0 !== Object.keys(l).length && ((r ??= {})[a] = l);
    }
    return r;
  };
  let s = (0, t.$)()(
    (0, r.u)((e, t) => {
      let r = (0, a.H)({
        merge: n,
        onFlush: (t) =>
          e((e) => {
            let r = { ...e.marketActivity };
            for (let [a, i] of t) r[a] = n(e.marketActivity[a], i);
            return { marketActivity: r };
          }),
      });
      return {
        marketActivity: {},
        setMarketActivity: (e) => {
          for (let [t, a] of Object.entries(e)) r.set(t, a);
        },
        seedMarketActivity: (e) => {
          let { marketActivity: a } = t();
          for (let [t, i] of Object.entries(e)) {
            let e = r.peek(t),
              s = e ? n(a[t], e) : a[t];
            if (!s) {
              r.set(t, i);
              continue;
            }
            let o = l(s, i);
            o && r.set(t, o);
          }
        },
        clearMarketActivity: () => {
          (r.clear(), e({ marketActivity: {} }));
        },
      };
    }),
  );
  return {
    setMarketActivity: (e) => {
      s.getState().setMarketActivity(e);
    },
    seedMarketActivity: (e) => {
      s.getState().seedMarketActivity(e);
    },
    store: s,
  };
}
function store2({ createBoundStore, subscribeWithSelector, createBatch }) {
  const t = { $: createBoundStore };
  const a = { u: subscribeWithSelector };
  const i = { H: createBatch };
  let l = (e, t) => {
    let a = { ...e };
    for (let [e, i] of Object.entries(t)) null != i && (a[e] = i);
    return a;
  };
  let r = (e, t) => {
    if (!e) return t;
    let a = { ...e };
    for (let i of Object.keys(t)) {
      let r = t[i],
        n = e[i];
      a[i] = r && n ? l(n, r) : r;
    }
    return a;
  };
  let n = (e, t) => {
    let a;
    for (let i of Object.keys(t)) {
      let l = e[i],
        r = t[i];
      if (!l || !r) continue;
      let n = {};
      for (let [e, t] of Object.entries(r))
        null != t && (null === l[e] || void 0 === l[e]) && (n[e] = t);
      0 !== Object.keys(n).length && ((a ??= {})[i] = n);
    }
    return a;
  };
  let o = (0, t.$)()(
    (0, a.u)((e, t) => {
      let a = (0, i.H)({
        merge: r,
        onFlush: (t) =>
          e((e) => {
            let a = { ...e.marketActivity };
            for (let [i, l] of t) a[i] = r(e.marketActivity[i], l);
            return { marketActivity: a };
          }),
      });
      return {
        marketActivity: {},
        setMarketActivity: (e) => {
          for (let [t, i] of Object.entries(e)) a.set(t, i);
        },
        seedMarketActivity: (e) => {
          let { marketActivity: i } = t();
          for (let [t, l] of Object.entries(e)) {
            let e = a.peek(t),
              o = e ? r(i[t], e) : i[t];
            if (!o) {
              a.set(t, l);
              continue;
            }
            let s = n(o, l);
            s && a.set(t, s);
          }
        },
        clearMarketActivity: () => {
          (a.clear(), e({ marketActivity: {} }));
        },
      };
    }),
  );
  return {
    setMarketActivity: (e) => {
      o.getState().setMarketActivity(e);
    },
    seedMarketActivity: (e) => {
      o.getState().seedMarketActivity(e);
    },
    store: o,
  };
}
function store3({ createBoundStore, subscribeWithSelector, createBatch }) {
  const t = { $: createBoundStore };
  const r = { u: subscribeWithSelector };
  const i = { H: createBatch };
  let l = (e, t) => {
    let r = { ...e };
    for (let [e, i] of Object.entries(t)) null != i && (r[e] = i);
    return r;
  };
  let a = (e, t) => {
    if (!e) return t;
    let r = { ...e };
    for (let i of Object.keys(t)) {
      let a = t[i],
        n = e[i];
      r[i] = a && n ? l(n, a) : a;
    }
    return r;
  };
  let n = (e, t) => {
    let r;
    for (let i of Object.keys(t)) {
      let l = e[i],
        a = t[i];
      if (!l || !a) continue;
      let n = {};
      for (let [e, t] of Object.entries(a))
        null != t && (null === l[e] || void 0 === l[e]) && (n[e] = t);
      0 !== Object.keys(n).length && ((r ??= {})[i] = n);
    }
    return r;
  };
  let o = (0, t.$)()(
    (0, r.u)((e, t) => {
      let r = (0, i.H)({
        merge: a,
        onFlush: (t) =>
          e((e) => {
            let r = { ...e.marketActivity };
            for (let [i, l] of t) r[i] = a(e.marketActivity[i], l);
            return { marketActivity: r };
          }),
      });
      return {
        marketActivity: {},
        setMarketActivity: (e) => {
          for (let [t, i] of Object.entries(e)) r.set(t, i);
        },
        seedMarketActivity: (e) => {
          let { marketActivity: i } = t();
          for (let [t, l] of Object.entries(e)) {
            let e = r.peek(t),
              o = e ? a(i[t], e) : i[t];
            if (!o) {
              r.set(t, l);
              continue;
            }
            let s = n(o, l);
            s && r.set(t, s);
          }
        },
        clearMarketActivity: () => {
          (r.clear(), e({ marketActivity: {} }));
        },
      };
    }),
  );
  return {
    setMarketActivity: (e) => {
      o.getState().setMarketActivity(e);
    },
    seedMarketActivity: (e) => {
      o.getState().seedMarketActivity(e);
    },
    store: o,
  };
}
function store4({ createBoundStore, subscribeWithSelector, createBatch }) {
  const t = { $: createBoundStore };
  const i = { u: subscribeWithSelector };
  const l = { H: createBatch };
  let r = (e, t) => {
    let i = { ...e };
    for (let [e, l] of Object.entries(t)) null != l && (i[e] = l);
    return i;
  };
  let a = (e, t) => {
    if (!e) return t;
    let i = { ...e };
    for (let l of Object.keys(t)) {
      let a = t[l],
        n = e[l];
      i[l] = a && n ? r(n, a) : a;
    }
    return i;
  };
  let n = (e, t) => {
    let i;
    for (let l of Object.keys(t)) {
      let r = e[l],
        a = t[l];
      if (!r || !a) continue;
      let n = {};
      for (let [e, t] of Object.entries(a))
        null != t && (null === r[e] || void 0 === r[e]) && (n[e] = t);
      0 !== Object.keys(n).length && ((i ??= {})[l] = n);
    }
    return i;
  };
  let o = (0, t.$)()(
    (0, i.u)((e, t) => {
      let i = (0, l.H)({
        merge: a,
        onFlush: (t) =>
          e((e) => {
            let i = { ...e.marketActivity };
            for (let [l, r] of t) i[l] = a(e.marketActivity[l], r);
            return { marketActivity: i };
          }),
      });
      return {
        marketActivity: {},
        setMarketActivity: (e) => {
          for (let [t, l] of Object.entries(e)) i.set(t, l);
        },
        seedMarketActivity: (e) => {
          let { marketActivity: l } = t();
          for (let [t, r] of Object.entries(e)) {
            let e = i.peek(t),
              o = e ? a(l[t], e) : l[t];
            if (!o) {
              i.set(t, r);
              continue;
            }
            let s = n(o, r);
            s && i.set(t, s);
          }
        },
        clearMarketActivity: () => {
          (i.clear(), e({ marketActivity: {} }));
        },
      };
    }),
  );
  return {
    setMarketActivity: (e) => {
      o.getState().setMarketActivity(e);
    },
    seedMarketActivity: (e) => {
      o.getState().seedMarketActivity(e);
    },
    store: o,
  };
}
function query0({
  React,
  useQuery,
  useQueryClient,
  helpers,
  fetchBatch,
  clock,
  queueMicrotask,
  state,
}) {
  const Date = clock;
  const microtask = (e) => {
    queueMicrotask(e);
  };
  const n = React;
  const i = {
    f: state.store,
    u: state.setMarketActivity,
    c: state.seedMarketActivity,
  };
  const r = { useQueryClient };
  const u = helpers;
  const t = { useQuery };
  const a = { g: fetchBatch };
  const l = { f: microtask };
  let s = new Map();
  let o = {};
  let c = (e) => e.marketActivity;
  let f = () => o;
  return {
    useMarketActivity: (e, o = {}) => {
      let {
          shouldFetch: d = !0,
          enablePolling: h = !1,
          pollingInterval: E = u.t.POLLING_INTERVAL,
          readBack: y = !0,
        } = o,
        m = (0, i.f)(y ? c : f),
        g = (0, r.useQueryClient)(),
        S = (0, n.useMemo)(
          () => Array.from(new Set(e)).filter(Boolean).sort(),
          [e],
        ),
        p = S.join(","),
        w = (0, n.useRef)(0),
        {
          data: k,
          isLoading: b,
          refetch: T,
        } = (0, t.useQuery)({
          queryKey: [u.t.QUERY_KEY, p],
          queryFn: async ({ signal: e, queryKey: t }) => {
            if (0 === S.length) return {};
            let r = ++w.current,
              n =
                g.getQueryState(t)?.data === void 0
                  ? ((e, t) => {
                      let r = Date.now() - u.t.STALE_TIME,
                        n = new Map();
                      for (let l of e
                        .getQueryCache()
                        .findAll({ queryKey: [u.t.QUERY_KEY] })) {
                        let {
                          data: e,
                          dataUpdatedAt: i,
                          isInvalidated: u,
                        } = l.state;
                        if (e && !u && !(i < r))
                          for (let l of t) {
                            let t = e[l];
                            if (!t || (s.get(l) ?? 0) < r) continue;
                            let u = n.get(l);
                            (!u || u.updatedAt < i) &&
                              n.set(l, { activity: t, updatedAt: i });
                          }
                      }
                      let l = {};
                      for (let [e, { activity: t }] of n) l[e] = t;
                      return l;
                    })(g, S)
                  : {},
              l = S.filter((e) => !n[e]),
              o = (0, u.$)(l, u.t.BATCH_SIZE).map((t) =>
                (0, a.g)(t, {
                  intervals: u.t.INTERVALS,
                  metrics: u.t.METRICS,
                  signal: e,
                }),
              ),
              c = await Promise.all(o),
              f = {};
            c.forEach((e) => {
              e && "object" == typeof e && Object.assign(f, e);
            });
            let d = Date.now();
            for (let e of Object.keys(f)) s.set(e, d);
            return (
              r === w.current && Object.keys(f).length > 0 && (0, i.u)(f),
              { ...n, ...f }
            );
          },
          enabled: d && S.length > 0,
          staleTime: u.t.STALE_TIME,
          gcTime: u.t.CACHE_TIME,
          refetchInterval: !!h && E,
          refetchOnMount: !0,
          refetchOnWindowFocus: !1,
          refetchOnReconnect: !1,
        });
      (0, n.useEffect)(() => {
        k && (0, l.f)(() => (0, i.c)(k));
      }, [k]);
      let v = (0, n.useMemo)(() => {
          if (!S.length) return {};
          let e = {};
          return (
            S.forEach((t) => {
              let r = m[t];
              r && (e[t] = r);
            }),
            e
          );
        }, [S, m]),
        C = (0, n.useRef)({});
      return {
        marketActivity: (0, n.useMemo)(
          () =>
            (0, u.c)(v, C.current) ? C.current : ((C.current = { ...v }), v),
          [v],
        ),
        loading: b,
        refetchMints: (0, n.useCallback)(
          async (e) => {
            e?.length &&
              0 !== (0, u.P)(i.f.getState().marketActivity, e).length &&
              (await g.invalidateQueries({ queryKey: [u.t.QUERY_KEY, p] }),
              await T());
          },
          [g, p, T],
        ),
      };
    },
  };
}
function query1({
  React,
  useQuery,
  useQueryClient,
  helpers,
  fetchBatch,
  clock,
  queueMicrotask,
  state,
}) {
  const Date = clock;
  const microtask = (e) => {
    queueMicrotask(e);
  };
  const a = React;
  const n = {
    f: state.store,
    u: state.setMarketActivity,
    c: state.seedMarketActivity,
  };
  const r = { useQueryClient };
  const l = helpers;
  const t = { useQuery };
  const s = { g: fetchBatch };
  const i = { f: microtask };
  let o = new Map();
  let d = {};
  let u = (e) => e.marketActivity;
  let c = () => d;
  return {
    useMarketActivity: (e, d = {}) => {
      let {
          shouldFetch: m = !0,
          enablePolling: p = !1,
          pollingInterval: h = l.t.POLLING_INTERVAL,
          readBack: f = !0,
        } = d,
        g = (0, n.f)(f ? u : c),
        b = (0, r.useQueryClient)(),
        y = (0, a.useMemo)(
          () => Array.from(new Set(e)).filter(Boolean).sort(),
          [e],
        ),
        v = y.join(","),
        w = (0, a.useRef)(0),
        {
          data: k,
          isLoading: C,
          refetch: x,
        } = (0, t.useQuery)({
          queryKey: [l.t.QUERY_KEY, v],
          queryFn: async ({ signal: e, queryKey: t }) => {
            if (0 === y.length) return {};
            let r = ++w.current,
              a =
                b.getQueryState(t)?.data === void 0
                  ? ((e, t) => {
                      let r = Date.now() - l.t.STALE_TIME,
                        a = new Map();
                      for (let i of e
                        .getQueryCache()
                        .findAll({ queryKey: [l.t.QUERY_KEY] })) {
                        let {
                          data: e,
                          dataUpdatedAt: n,
                          isInvalidated: l,
                        } = i.state;
                        if (e && !l && !(n < r))
                          for (let i of t) {
                            let t = e[i];
                            if (!t || (o.get(i) ?? 0) < r) continue;
                            let l = a.get(i);
                            (!l || l.updatedAt < n) &&
                              a.set(i, { activity: t, updatedAt: n });
                          }
                      }
                      let i = {};
                      for (let [e, { activity: t }] of a) i[e] = t;
                      return i;
                    })(b, y)
                  : {},
              i = y.filter((e) => !a[e]),
              d = (0, l.$)(i, l.t.BATCH_SIZE).map((t) =>
                (0, s.g)(t, {
                  intervals: l.t.INTERVALS,
                  metrics: l.t.METRICS,
                  signal: e,
                }),
              ),
              u = await Promise.all(d),
              c = {};
            u.forEach((e) => {
              e && "object" == typeof e && Object.assign(c, e);
            });
            let m = Date.now();
            for (let e of Object.keys(c)) o.set(e, m);
            return (
              r === w.current && Object.keys(c).length > 0 && (0, n.u)(c),
              { ...a, ...c }
            );
          },
          enabled: m && y.length > 0,
          staleTime: l.t.STALE_TIME,
          gcTime: l.t.CACHE_TIME,
          refetchInterval: !!p && h,
          refetchOnMount: !0,
          refetchOnWindowFocus: !1,
          refetchOnReconnect: !1,
        });
      (0, a.useEffect)(() => {
        k && (0, i.f)(() => (0, n.c)(k));
      }, [k]);
      let I = (0, a.useMemo)(() => {
          if (!y.length) return {};
          let e = {};
          return (
            y.forEach((t) => {
              let r = g[t];
              r && (e[t] = r);
            }),
            e
          );
        }, [y, g]),
        _ = (0, a.useRef)({});
      return {
        marketActivity: (0, a.useMemo)(
          () =>
            (0, l.c)(I, _.current) ? _.current : ((_.current = { ...I }), I),
          [I],
        ),
        loading: C,
        refetchMints: (0, a.useCallback)(
          async (e) => {
            e?.length &&
              0 !== (0, l.P)(n.f.getState().marketActivity, e).length &&
              (await b.invalidateQueries({ queryKey: [l.t.QUERY_KEY, v] }),
              await x());
          },
          [b, v, x],
        ),
      };
    },
  };
}
function query2({
  React,
  useQuery,
  useQueryClient,
  helpers,
  fetchBatch,
  clock,
  queueMicrotask,
  state,
}) {
  const Date = clock;
  const microtask = (e) => {
    queueMicrotask(e);
  };
  const i = React;
  const r = {
    f: state.store,
    u: state.setMarketActivity,
    c: state.seedMarketActivity,
  };
  const a = { useQueryClient };
  const n = helpers;
  const t = { useQuery };
  const o = { g: fetchBatch };
  const l = { f: microtask };
  let s = new Map();
  let d = {};
  let c = (e) => e.marketActivity;
  let u = () => d;
  return {
    useMarketActivity: (e, d = {}) => {
      let {
          shouldFetch: m = !0,
          enablePolling: p = !1,
          pollingInterval: h = n.t.POLLING_INTERVAL,
          readBack: f = !0,
        } = d,
        g = (0, r.f)(f ? c : u),
        y = (0, a.useQueryClient)(),
        v = (0, i.useMemo)(
          () => Array.from(new Set(e)).filter(Boolean).sort(),
          [e],
        ),
        b = v.join(","),
        I = (0, i.useRef)(0),
        {
          data: w,
          isLoading: C,
          refetch: k,
        } = (0, t.useQuery)({
          queryKey: [n.t.QUERY_KEY, b],
          queryFn: async ({ signal: e, queryKey: t }) => {
            if (0 === v.length) return {};
            let a = ++I.current,
              i =
                y.getQueryState(t)?.data === void 0
                  ? ((e, t) => {
                      let a = Date.now() - n.t.STALE_TIME,
                        i = new Map();
                      for (let l of e
                        .getQueryCache()
                        .findAll({ queryKey: [n.t.QUERY_KEY] })) {
                        let {
                          data: e,
                          dataUpdatedAt: r,
                          isInvalidated: n,
                        } = l.state;
                        if (e && !n && !(r < a))
                          for (let l of t) {
                            let t = e[l];
                            if (!t || (s.get(l) ?? 0) < a) continue;
                            let n = i.get(l);
                            (!n || n.updatedAt < r) &&
                              i.set(l, { activity: t, updatedAt: r });
                          }
                      }
                      let l = {};
                      for (let [e, { activity: t }] of i) l[e] = t;
                      return l;
                    })(y, v)
                  : {},
              l = v.filter((e) => !i[e]),
              d = (0, n.$)(l, n.t.BATCH_SIZE).map((t) =>
                (0, o.g)(t, {
                  intervals: n.t.INTERVALS,
                  metrics: n.t.METRICS,
                  signal: e,
                }),
              ),
              c = await Promise.all(d),
              u = {};
            c.forEach((e) => {
              e && "object" == typeof e && Object.assign(u, e);
            });
            let m = Date.now();
            for (let e of Object.keys(u)) s.set(e, m);
            return (
              a === I.current && Object.keys(u).length > 0 && (0, r.u)(u),
              { ...i, ...u }
            );
          },
          enabled: m && v.length > 0,
          staleTime: n.t.STALE_TIME,
          gcTime: n.t.CACHE_TIME,
          refetchInterval: !!p && h,
          refetchOnMount: !0,
          refetchOnWindowFocus: !1,
          refetchOnReconnect: !1,
        });
      (0, i.useEffect)(() => {
        w && (0, l.f)(() => (0, r.c)(w));
      }, [w]);
      let x = (0, i.useMemo)(() => {
          if (!v.length) return {};
          let e = {};
          return (
            v.forEach((t) => {
              let a = g[t];
              a && (e[t] = a);
            }),
            e
          );
        }, [v, g]),
        T = (0, i.useRef)({});
      return {
        marketActivity: (0, i.useMemo)(
          () =>
            (0, n.c)(x, T.current) ? T.current : ((T.current = { ...x }), x),
          [x],
        ),
        loading: C,
        refetchMints: (0, i.useCallback)(
          async (e) => {
            e?.length &&
              0 !== (0, n.P)(r.f.getState().marketActivity, e).length &&
              (await y.invalidateQueries({ queryKey: [n.t.QUERY_KEY, b] }),
              await k());
          },
          [y, b, k],
        ),
      };
    },
  };
}
export function createMarketActivityState({
  queryVariant,
  storeVariant,
  ...ports
}) {
  const storeFactories = {
    c57dd65e642700694b2b65e1554a0d11ac5caca8b535bfa1062564366e344d61: store0,
    "4d8d931c538e4d5825c61fd3a88195ed022fb5aea372113ac4f31b594b2ada62": store1,
    "8d033eb75f35cf9896bac25b3e151d4e7057dacd759e61c880aa24e1e52b1022": store2,
    "7eeb7e121092f1cac917f25c0d222d0e79932ce86d62cb01a73e90cb541781e0": store3,
    "90cc0b7b37585830da582b2f52fe2177074ed20f613713e894858b23a8d34a12": store4,
  };
  const storeFactory =
    typeof storeVariant === "string" &&
    Object.hasOwn(storeFactories, storeVariant)
      ? storeFactories[storeVariant]
      : null;
  const queryFactories = {
    "704bb073aaf4230b6cac309756c284803fe7d3cc4e2776a060d041af2341a786": query0,
    dff1b5f10ee3af571bcc7fa3b0a7e8a0ec4b9eedc58a4cc3526600590f1529b4: query1,
    d9ab130a7e21782f4e8a294f011c25405d3690ef4aafcc5bcc5bdabd656a414b: query2,
  };
  const queryFactory =
    typeof queryVariant === "string" &&
    Object.hasOwn(queryFactories, queryVariant)
      ? queryFactories[queryVariant]
      : null;
  if (!storeFactory || !queryFactory)
    throw Error("explicit supported201629 and372743 variant hashes required");
  const state = storeFactory(ports),
    query = queryFactory({ ...ports, state });
  return { ...state, ...query };
}
