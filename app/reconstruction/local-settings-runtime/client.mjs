// Source-adapted original logic. Explicit ports only; importing reads no browser state.
export function createLocalKeyRuntime({ window, StorageEvent }) {
  let t = "local-storage",
    r = new Map(),
    i = new Map(),
    s = new Map(),
    n = !1,
    o = () => {
      if (n) return;
      n = !0;
      let e = (e) => {
        var t;
        null === (t = e.key ?? null)
          ? r.forEach((e) => {
              e.forEach((e) => e());
            })
          : r.get(t)?.forEach((e) => e());
      };
      (window.addEventListener("storage", e), window.addEventListener(t, e));
    };
  const localKey = ({ key: e, codec: n }) => ({
    kind: "localKey",
    read: () => {
      let t = s.get(e);
      if (t) return t.value;
      let r = ((e) => {
        try {
          return window.localStorage.getItem(e);
        } catch {
          return null;
        }
      })(e);
      if (null === r) return;
      let o = i.get(e);
      if (o && o.raw === r) return o.value;
      let a = ((e, t) => {
        if ("raw" === t) return e;
        try {
          return JSON.parse(e);
        } catch {
          return;
        }
      })(r, n);
      return (i.set(e, { raw: r, value: a }), a);
    },
    write: (r) => {
      o();
      let i = "raw" === n ? String(r) : JSON.stringify(r);
      try {
        (window.localStorage.setItem(e, i), s.delete(e));
      } catch {
        s.set(e, { raw: i, value: r });
      }
      window.dispatchEvent(new StorageEvent(t, { key: e }));
    },
    remove: () => {
      o();
      try {
        window.localStorage.removeItem(e);
      } catch {}
      (s.delete(e),
        i.delete(e),
        window.dispatchEvent(new StorageEvent(t, { key: e })));
    },
    subscribe: (t) => {
      o();
      let i = r.get(e);
      return (
        i || ((i = new Set()), r.set(e, i)),
        i.add(t),
        () => {
          i?.delete(t);
        }
      );
    },
  });
  return { localKey };
}
export function createLegacyInitializer({ window }) {
  let t = new WeakSet(),
    r = (e) =>
      "object" == typeof e &&
      null !== e &&
      !Array.isArray(e) &&
      Object.getPrototypeOf(e) === Object.prototype,
    i = (e, t) => {
      if (Array.isArray(e) && Array.isArray(t))
        return Array.from({ length: Math.max(e.length, t.length) }, (r, s) =>
          s < t.length ? i(e[s], t[s]) : e[s],
        );
      if (!r(e) || !r(t)) return t;
      let s = { ...e };
      for (let [e, r] of Object.entries(t)) s[e] = e in s ? i(s[e], r) : r;
      return s;
    },
    s = (e) => {
      try {
        let t = window.localStorage.getItem(e.key);
        if (null === t) return;
        if ("raw" === e.codec) return e.map(t);
        return e.map(JSON.parse(t));
      } catch {
        return;
      }
    };
  return (e) => {
    if (t.has(e)) return;
    t.add(e);
    let r = e.legacy;
    if (!r || 0 === r.length || void 0 !== e.adapter.read()) return;
    let n = e.default,
      o = !1;
    for (let e of r) {
      let t = s(e);
      void 0 !== t && ((o = !0), (n = i(n, t)));
    }
    if (o) {
      for (let t of (e.adapter.write(e.coerce(n)), r))
        if (!1 !== t.removeAfterAdopt)
          try {
            window.localStorage.removeItem(t.key);
          } catch {}
    }
  };
}
export function createSettingsRuntime({
  registry,
  initializeLegacy,
  useMemoCache,
  useSyncExternalStore,
}) {
  const t = { c: useMemoCache },
    r = { useSyncExternalStore },
    i = { f: initializeLegacy },
    s = { k: registry };
  let n = new WeakMap(),
    o = (e) => {
      let t,
        r = n.get(e);
      if (r) return r;
      let s = Symbol("unset"),
        o = {
          subscribe: e.adapter.subscribe,
          getSnapshot: () => {
            (0, i.f)(e);
            let r = e.adapter.read();
            return Object.is(r, s) ? t : ((s = r), (t = e.coerce(r)));
          },
          getServerSnapshot: () => e.default,
        };
      return (n.set(e, o), o);
    },
    a = (e) => s.k[e],
    l = (e) => o(a(e)).getSnapshot(),
    c = (e, t) => {
      let r = a(e);
      r.adapter.write(r.coerce(t));
    },
    d = (e, i) => {
      let s,
        n,
        l = (0, t.c)(5);
      l[0] !== e ? ((s = o(a(e))), (l[0] = e), (l[1] = s)) : (s = l[1]);
      let c = s,
        d = i?.serverValue;
      return (
        l[2] !== c.getServerSnapshot || l[3] !== d
          ? ((n = void 0 === d ? c.getServerSnapshot : () => d),
            (l[2] = c.getServerSnapshot),
            (l[3] = d),
            (l[4] = n))
          : (n = l[4]),
        (0, r.useSyncExternalStore)(c.subscribe, c.getSnapshot, n)
      );
    },
    u = (e) => {
      let r,
        i = (0, t.c)(2);
      return (
        i[0] !== e
          ? ((r = (t) => {
              let r = l(e);
              c(e, "function" == typeof t ? t(r) : t);
            }),
            (i[0] = e),
            (i[1] = r))
          : (r = i[1]),
        r
      );
    };
  const useSettingPair = (e, r) => {
    let i,
      s = (0, t.c)(3),
      n = d(e, r),
      o = u(e);
    return (
      s[0] !== n || s[1] !== o
        ? ((i = [n, o]), (s[0] = n), (s[1] = o), (s[2] = i))
        : (i = s[2]),
      i
    );
  };
  return {
    readSetting: l,
    writeSetting: c,
    useSetting: d,
    useSetter: u,
    useSettingPair,
  };
}
export function createFeedAnimationsDefinition({ localKey }) {
  const m = { f: localKey },
    b = { f: (e) => e };
  return (0, b.f)({
    id: "feed.showAnimations",
    section: "feed",
    scope: "device",
    default: !0,
    coerce: (e) => !1 !== e,
    adapter: (0, m.f)({ key: "home.show-animations", codec: "json" }),
    control: { kind: "switch" },
    labelKey: "web.home.animations_label",
    descriptionKey: "settings.animations_desc",
    searchTerms: ["animations", "motion", "shuffle", "flash"],
  });
}
export function createSettingsSwitch({
  jsx,
  jsxs,
  Fragment,
  useMemoCache,
  useState,
  useTranslation,
  translateKey,
  Switch,
  Button,
  confirmation,
  useHydrated,
  settings,
}) {
  const t = { jsx, jsxs, Fragment },
    n = { c: useMemoCache },
    i = { Z: Switch, K: Button },
    r = { useState },
    l = { f: useTranslation },
    a = { f: translateKey },
    s = confirmation,
    o = { f: useHydrated },
    c = { o: settings.useSetting, Z: settings.useSetter };
  function d(e) {
    return e.stopPropagation();
  }
  return function (e) {
    let u,
      x,
      m,
      p,
      f,
      h = (0, n.c)(20),
      { definition: g, label: b } = e,
      { t: j } = (0, l.f)(),
      v = g.id,
      y = (0, c.o)(v),
      _ = (0, c.Z)(v),
      w = (0, o.f)(),
      [N, C] = (0, r.useState)(null),
      k = "switch" === g.control.kind ? g.control.confirm : void 0,
      S = !0 === g.firstPaintSensitive && !w;
    h[0] !== k || h[1] !== _
      ? ((u = (e) => {
          k && e === k.when ? C(e) : _(e);
        }),
        (h[0] = k),
        (h[1] = _),
        (h[2] = u))
      : (u = h[2]);
    let T = u;
    h[3] !== N || h[4] !== _
      ? ((x = (e) => {
          (e && null !== N && _(N), C(null));
        }),
        (h[3] = N),
        (h[4] = _),
        (h[5] = x))
      : (x = h[5]);
    let A = x,
      P = !0 === y;
    return (
      h[6] !== S || h[7] !== b || h[8] !== T || h[9] !== P
        ? ((m = (0, t.jsx)("span", {
            className: "flex",
            onPointerDown: d,
            children: (0, t.jsx)(i.Z, {
              "aria-label": b,
              isChecked: P,
              isDisabled: S,
              onCheckedChange: T,
            }),
          })),
          (h[6] = S),
          (h[7] = b),
          (h[8] = T),
          (h[9] = P),
          (h[10] = m))
        : (m = h[10]),
      h[11] !== k || h[12] !== g.id || h[13] !== N || h[14] !== A || h[15] !== j
        ? ((p =
            k && null !== N
              ? (0, t.jsxs)(s.N, {
                  open: !0,
                  onOpenChange: (e) => {
                    e || A(!1);
                  },
                  density: "terminal",
                  size: "sm",
                  title: (0, a.f)(j, k.titleKey),
                  "data-testid": `setting-confirm-${g.id}`,
                  children: [
                    (0, t.jsx)(s.K, {
                      children: (0, t.jsx)("p", {
                        className: "text-[12px] leading-4 text-text-secondary",
                        children: (0, a.f)(j, k.descriptionKey),
                      }),
                    }),
                    (0, t.jsxs)(s.c, {
                      className: "flex-col items-stretch",
                      children: [
                        (0, t.jsx)(i.K, {
                          variant: "primary",
                          className: "bg-loss text-bg-primary hover:bg-loss/90",
                          size: s.$,
                          isFullWidth: !0,
                          onClick: () => A(!0),
                          children: (0, a.f)(j, k.confirmLabelKey),
                        }),
                        (0, t.jsx)(i.K, {
                          variant: "secondary",
                          size: s.Z,
                          isFullWidth: !0,
                          onClick: () => A(!1),
                          children: j("common.cancel"),
                        }),
                      ],
                    }),
                  ],
                })
              : null),
          (h[11] = k),
          (h[12] = g.id),
          (h[13] = N),
          (h[14] = A),
          (h[15] = j),
          (h[16] = p))
        : (p = h[16]),
      h[17] !== m || h[18] !== p
        ? ((f = (0, t.jsxs)(t.Fragment, { children: [m, p] })),
          (h[17] = m),
          (h[18] = p),
          (h[19] = f))
        : (f = h[19]),
      f
    );
  };
}
