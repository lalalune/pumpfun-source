// Source-bound editable translation; captured factories are parsed, never evaluated.
export const protocolVariantHashes = [
  "d07a60b6380a193ffe870306c705b0c8c289663dcb883d57e7605a296425dc27",
  "d2419cfba7861ae41660985a0fa4b586b8e48c353aa46ccb1c55d1011a4cd04d",
];
function protocol0() {
  let t;
  let n;
  let s =
    (((t = {}).Advanced = "ADVANCED"),
    (t.Core = "CORE"),
    (t.Unified = "UNIFIED"),
    (t.Multichain = "MULTICHAIN"),
    t);
  let i =
    (((n = {}).CONNECTING = "CONNECTING"),
    (n.CONNECTED = "CONNECTED"),
    (n.DISCONNECTED = "DISCONNECTED"),
    n);
  return {
    get N() {
      return (() => s)();
    },
    get m() {
      return (() => i)();
    },
  };
}
function protocol1() {
  let t;
  let n;
  let r =
    (((t = {}).Advanced = "ADVANCED"),
    (t.Core = "CORE"),
    (t.Unified = "UNIFIED"),
    (t.Multichain = "MULTICHAIN"),
    t);
  let a =
    (((n = {}).CONNECTING = "CONNECTING"),
    (n.CONNECTED = "CONNECTED"),
    (n.DISCONNECTED = "DISCONNECTED"),
    n);
  return {
    get N() {
      return (() => r)();
    },
    get m() {
      return (() => a)();
    },
  };
}
export function createLiteTradeHooks({
  protocolVariant,
  React,
  useConnection,
  useReady,
  liveCoinStore,
  logger,
  DatePort,
}) {
  const protocol =
    protocolVariant === protocolVariantHashes[0]
      ? protocol0()
      : protocolVariant === protocolVariantHashes[1]
        ? protocol1()
        : null;
  if (!protocol) throw Error("explicit supported985526 variant hash required");
  const Date = DatePort;
  const n = { V: "unifiedTradeEvent.lite" };
  const t = { y: logger };
  const r = React;
  const u = { N: useConnection };
  const s = { f: useReady };
  const c = { x: liveCoinStore };
  const l = protocol;
  let a = new Map();
  function i(e, t, r) {
    if (0 === t.listeners.size) {
      if (null != t.natsId)
        try {
          r.unsubscribe(l.N.Unified, t.natsId);
        } catch {}
      a.delete(e);
      return;
    }
    let i = (function (e) {
      for (let t of e.listeners.values()) if ("none" === t) return "none";
      return "latest";
    })(t);
    if (null != t.natsId && t.subscribedMode === i) return;
    if (null != t.natsId) {
      try {
        r.unsubscribe(l.N.Unified, t.natsId);
      } catch {}
      t.natsId = null;
    }
    let s = `${n.V}.${e}`;
    ((t.natsId = r.subscribe(
      l.N.Unified,
      s,
      (t) =>
        (function (e, t) {
          let r = a.get(e);
          if (r)
            for (let e of r.listeners.keys())
              try {
                e(t);
              } catch {}
        })(e, t),
      void 0,
      { coalesce: i },
    )),
      (t.subscribedMode = i));
  }
  let o = ({
    mints: e,
    isEnabled: t,
    onLiteTrade: n,
    coalesce: o = "none",
  }) => {
    let { subscribe: c, unsubscribe: d, isInstanceActive: f } = (0, u.N)(),
      p = (0, s.f)(),
      m = (0, r.useRef)(new Map()),
      h = (0, r.useRef)(o),
      b = (0, r.useRef)(n);
    (0, r.useEffect)(() => {
      b.current = n;
    }, [n]);
    let g = (0, r.useCallback)((e) => {
        b.current(e);
      }, []),
      y = (0, r.useMemo)(
        () => (0 === e.length ? "" : [...e].sort().join(",")),
        [e],
      );
    ((0, r.useEffect)(() => {
      let r = m.current,
        n = () => {
          (r.forEach((e) => e()), r.clear());
        };
      if (!t || !p || 0 === e.length || !f(l.N.Unified)) return void n();
      h.current !== o && (n(), (h.current = o));
      let s = new Set(e.filter(Boolean));
      (r.forEach((e, t) => {
        s.has(t) || (e(), r.delete(t));
      }),
        s.forEach((e) => {
          if (r.has(e)) return;
          let t = (function (e, t, r, l = {}) {
            let n = e.trim();
            if (!n) return () => {};
            let s = l.coalesce ?? "none",
              u = a.get(n);
            return (
              u ||
                ((u = {
                  listeners: new Map(),
                  natsId: null,
                  subscribedMode: null,
                }),
                a.set(n, u)),
              u.listeners.set(t, s),
              i(n, u, r),
              () => {
                let e = a.get(n);
                !e || (e.listeners.delete(t) && i(n, e, r));
              }
            );
          })(e, g, { subscribe: c, unsubscribe: d }, { coalesce: o });
          r.set(e, t);
        }));
    }, [y, t, p, o, f, c, d, g]),
      (0, r.useEffect)(() => {
        let e = m.current;
        return () => {
          (e.forEach((e) => e()), e.clear());
        };
      }, []));
  };
  return {
    useSubscriptions: o,
    useLiteTrades: function (e, l = !0) {
      let n = (0, c.x)((e) => e.updateCoin);
      o({
        mints: e,
        isEnabled: l,
        onLiteTrade: (0, r.useCallback)(
          (e) => {
            try {
              let t = e?.mint;
              if (!t) return;
              let r = Number(e.marketCap);
              if (!Number.isFinite(r) || r <= 0) return;
              let l = c.x.getState().peekCoin(t)?.usdAthMarketCap,
                a = {
                  usdMarketCap: r,
                  priceUsd: e.priceUsd ? Number(e.priceUsd) : void 0,
                  lastTradeTimestamp: e.timestamp
                    ? new Date(e.timestamp).getTime()
                    : Date.now(),
                  lastTradeIsBuy: "buy" === e.type,
                };
              (l && r > l && (a.usdAthMarketCap = r), n(t, a));
            } catch (e) {
              t.y.error("Error handling lite trade event", { error: e });
            }
          },
          [n],
        ),
        coalesce: "latest",
      });
    },
  };
}
