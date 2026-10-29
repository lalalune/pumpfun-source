// Source-bound editable translation. Captured factories are parsed, never evaluated.
// Provider, React/compiler, clock, browser scheduler and logger are explicit ports.
export const batchVariantHashes = [
  "eaadb129bb56009d4029f5ad08f8a52fb30da20d64ab9218ff56359dfdead966",
  "c232e5e54526261f925817dc14fbf1a253b4e89e2515f7a8c5bf2c3b7d2de8d8",
];
function frameVariant0({ React, compiler, environment, logger }) {
  const { window, document, setTimeout, clearTimeout } = environment;
  const n = { y: logger };
  const r = React;
  const t = { c: compiler };
  let i = new Set();
  let l = new Set();
  let a = null;
  let o = null;
  let s = 0;
  let u = !1;
  let d = () => "u" > typeof document && "hidden" === document.visibilityState;
  let c = () => {
    (null !== a && (window.cancelAnimationFrame(a), (a = null)),
      null !== o && (clearTimeout(o), (o = null)));
  };
  let f = () => {
    if ((c(), s > 0)) return;
    let e = [...i];
    for (let t of (i.clear(), e))
      try {
        t();
      } catch (e) {
        n.y.error("[frameBatch] flush failed", { error: e });
      }
  };
  let m = () => {
    d() && 0 !== i.size && f();
  };
  let p = () => {
    if (null === a && null === o) {
      if (
        (!u &&
          "u" > typeof document &&
          (document.addEventListener("visibilitychange", m), (u = !0)),
        d() || "function" != typeof window.requestAnimationFrame)
      ) {
        o = setTimeout(f, 250);
        return;
      }
      ((a = window.requestAnimationFrame(f)), (o = setTimeout(f, 100)));
    }
  };
  let h = (e) => {
    (i.add(e), s > 0 || p());
  };
  function y() {
    let e,
      t =
        ((s += 1),
        c(),
        (e = !1),
        () => {
          !e && ((e = !0), 0 === (s = Math.max(0, s - 1)) && i.size > 0 && p());
        }),
      n = !1,
      r = null,
      l = null,
      a = () => {
        ((n = !0),
          null !== r && window.cancelAnimationFrame(r),
          null !== l && clearTimeout(l),
          t());
      },
      o = () => {
        !n && (a(), s > 0 || f());
      };
    return (
      "function" == typeof window.requestAnimationFrame &&
        (r = window.requestAnimationFrame(o)),
      (l = setTimeout(o, 250)),
      () => {
        n || a();
      }
    );
  }
  return {
    createBatch: ({ onFlush: e, merge: t }) => {
      let n = new Map(),
        r = () => {
          if (0 === n.size) return;
          let t = new Map(n);
          (n.clear(), e(t));
        },
        i = {
          set: (e, i) => {
            let l = n.get(e);
            (n.set(e, t && n.has(e) ? t(l, i) : i), h(r));
          },
          peek: (e) => n.get(e),
          clear: () => n.clear(),
          flush: r,
          get size() {
            return n.size;
          },
        };
      return (l.add(i), i);
    },
    enqueue: h,
    usePause: (e) => {
      let n,
        i = (0, t.c)(2);
      (i[0] !== e ? ((n = [e]), (i[0] = e), (i[1] = n)) : (n = i[1]),
        (0, r.useEffect)(y, n));
    },
  };
}
function frameVariant1({ React, compiler, environment, logger }) {
  const { window, document, setTimeout, clearTimeout } = environment;
  const n = { y: logger };
  const r = React;
  const t = { c: compiler };
  let i = new Set();
  let o = new Set();
  let s = null;
  let a = null;
  let l = 0;
  let u = !1;
  let c = () => "u" > typeof document && "hidden" === document.visibilityState;
  let f = () => {
    (null !== s && (window.cancelAnimationFrame(s), (s = null)),
      null !== a && (clearTimeout(a), (a = null)));
  };
  let d = () => {
    if ((f(), l > 0)) return;
    let e = [...i];
    for (let t of (i.clear(), e))
      try {
        t();
      } catch (e) {
        n.y.error("[frameBatch] flush failed", { error: e });
      }
  };
  let h = () => {
    c() && 0 !== i.size && d();
  };
  let p = () => {
    if (null === s && null === a) {
      if (
        (!u &&
          "u" > typeof document &&
          (document.addEventListener("visibilitychange", h), (u = !0)),
        c() || "function" != typeof window.requestAnimationFrame)
      ) {
        a = setTimeout(d, 250);
        return;
      }
      ((s = window.requestAnimationFrame(d)), (a = setTimeout(d, 100)));
    }
  };
  let g = (e) => {
    (i.add(e), l > 0 || p());
  };
  function m() {
    let e,
      t =
        ((l += 1),
        f(),
        (e = !1),
        () => {
          !e && ((e = !0), 0 === (l = Math.max(0, l - 1)) && i.size > 0 && p());
        }),
      n = !1,
      r = null,
      o = null,
      s = () => {
        ((n = !0),
          null !== r && window.cancelAnimationFrame(r),
          null !== o && clearTimeout(o),
          t());
      },
      a = () => {
        !n && (s(), l > 0 || d());
      };
    return (
      "function" == typeof window.requestAnimationFrame &&
        (r = window.requestAnimationFrame(a)),
      (o = setTimeout(a, 250)),
      () => {
        n || s();
      }
    );
  }
  return {
    createBatch: ({ onFlush: e, merge: t }) => {
      let n = new Map(),
        r = () => {
          if (0 === n.size) return;
          let t = new Map(n);
          (n.clear(), e(t));
        },
        i = {
          set: (e, i) => {
            let o = n.get(e);
            (n.set(e, t && n.has(e) ? t(o, i) : i), g(r));
          },
          peek: (e) => n.get(e),
          clear: () => n.clear(),
          flush: r,
          get size() {
            return n.size;
          },
        };
      return (o.add(i), i);
    },
    enqueue: g,
    usePause: (e) => {
      let n,
        i = (0, t.c)(2);
      (i[0] !== e ? ((n = [e]), (i[0] = e), (i[1] = n)) : (n = i[1]),
        (0, r.useEffect)(m, n));
    },
  };
}
export function createFrameBatchRuntime({ variant, ...ports }) {
  if (variant === batchVariantHashes[0]) return frameVariant0(ports);
  if (variant === batchVariantHashes[1]) return frameVariant1(ports);
  throw new Error("explicit supported811005 variant hash required");
}
export const subscribeWithSelector = (e) => (t, r, o) => {
  let n = o.subscribe;
  return (
    (o.subscribe = (e, t, r) => {
      let a = e;
      if (t) {
        let n = (null == r ? void 0 : r.equalityFn) || Object.is,
          i = e(o.getState());
        ((a = (r) => {
          let o = e(r);
          if (!n(i, o)) {
            let e = i;
            t((i = o), e);
          }
        }),
          (null == r ? void 0 : r.fireImmediately) && t(i, i));
      }
      return n(a);
    }),
    e(t, r, o)
  );
};
export function createLiveCoinState({
  React,
  compiler,
  createBoundStore,
  frameBatch,
  clock,
}) {
  const Date = clock;
  const n = { $: createBoundStore };
  const i = { default: React };
  const t = { c: compiler };
  const r = { u: subscribeWithSelector };
  const o = { H: frameBatch.createBatch };
  let l = (e, t) => {
    let n = e instanceof Map ? e : new Map(e.entries()),
      r = t instanceof Map ? t : new Map(t.entries());
    if (n.size !== r.size) return !1;
    for (let [e, t] of n) if (!Object.is(t, r.get(e))) return !1;
    return !0;
  };
  function a(e) {
    let t = i.default.useRef(void 0);
    return (n) => {
      let r = e(n);
      return !(function (e, t) {
        if (Object.is(e, t)) return !0;
        if (
          "object" != typeof e ||
          null === e ||
          "object" != typeof t ||
          null === t ||
          Object.getPrototypeOf(e) !== Object.getPrototypeOf(t)
        )
          return !1;
        if (Symbol.iterator in e && Symbol.iterator in t) {
          if ("entries" in e && "entries" in t) return l(e, t);
          let n = e[Symbol.iterator](),
            r = t[Symbol.iterator](),
            i = n.next(),
            a = r.next();
          for (; !i.done && !a.done; ) {
            if (!Object.is(i.value, a.value)) return !1;
            ((i = n.next()), (a = r.next()));
          }
          return !!i.done && !!a.done;
        }
        return l(
          { entries: () => Object.entries(e) },
          { entries: () => Object.entries(t) },
        );
      })(t.current, r)
        ? (t.current = r)
        : t.current;
    };
  }
  let s = (e, t) => (void 0 === e ? t : void 0 === t ? e : Math.max(e, t));
  let u = (e, t) => ({
    base: "committed" === t.base ? e.base : t.base,
    updates: ((e, t) => {
      if (!e) return t;
      if (!t) return e;
      let n = { ...e, ...t },
        r = s(e.usdAthMarketCap, t.usdAthMarketCap);
      return (void 0 !== r && (n.usdAthMarketCap = r), n);
    })(e.updates, t.updates),
    queuedAt: t.queuedAt,
  });
  let d = (e, t, n) => {
    let r,
      i =
        "committed" === n.base
          ? t
          : "empty" === n.base
            ? void 0
            : { ...n.base, lastUpdated: n.queuedAt };
    if (!n.updates) return i;
    let l =
        i ??
        ((r = {}),
        {
          mint: e,
          usdMarketCap: 0,
          lastUpdated: Date.now(),
          isLiveData: !1,
          ...r,
        }),
      a = s(l.usdAthMarketCap, n.updates.usdAthMarketCap);
    return {
      ...l,
      ...n.updates,
      ...(void 0 !== a ? { usdAthMarketCap: a } : {}),
      lastUpdated: n.queuedAt,
      isLiveData: !0,
    };
  };
  let c = (0, n.$)()(
    (0, r.u)((e, t) => {
      let n = (0, o.H)({
          merge: u,
          onFlush: (t) => {
            e((e) => {
              let n = { ...e.coins };
              return (
                t.forEach((e, t) => {
                  let r = d(t, n[t], e);
                  r ? (n[t] = r) : delete n[t];
                }),
                { coins: n }
              );
            });
          },
        }),
        r = (e, t) => n.set(e, { ...t, queuedAt: Date.now() });
      return {
        coins: {},
        updateCoin: (e, t) => r(e, { base: "committed", updates: t }),
        setCoin: (e) => r(e.mint, { base: e }),
        removeCoin: (e) => r(e, { base: "empty" }),
        getCoin: (e) => t().coins[e],
        getCoins: (e) => {
          let { coins: n } = t();
          return e.map((e) => n[e]);
        },
        hasLiveData: (e) => t().coins[e]?.isLiveData ?? !1,
        peekCoin: (e) => {
          let r = t().coins[e],
            i = n.peek(e);
          return i ? d(e, r, i) : r;
        },
      };
    }),
  );
  let f = [];
  return {
    store: c,
    useMarketCap: (e) => {
      let n,
        r = (0, t.c)(2);
      return (
        r[0] !== e
          ? ((n = (t) => t.coins[e]?.usdMarketCap), (r[0] = e), (r[1] = n))
          : (n = r[1]),
        c(n)
      );
    },
    useCoin: (e) => {
      let n,
        r = (0, t.c)(2);
      return (
        r[0] !== e
          ? ((n = (t) => t.coins[e]), (r[0] = e), (r[1] = n))
          : (n = r[1]),
        c(n)
      );
    },
    useCoins: (e) => {
      let n,
        r = (0, t.c)(2);
      return (
        r[0] !== e
          ? ((n = (t) => (0 === e.length ? f : e.map((e) => t.coins[e]))),
            (r[0] = e),
            (r[1] = n))
          : (n = r[1]),
        c(a(n))
      );
    },
    useShallow: a,
  };
}
