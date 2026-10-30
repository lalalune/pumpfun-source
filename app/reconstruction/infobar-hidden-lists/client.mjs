// Complete source-adapted ordinary InfoBar hidden-list values, descriptors and fields.
export function createHiddenInfoBarValues() {
  const canonical = function (e) {
      return e.startsWith("0x") ? e.toLowerCase() : e;
    },
    i = { c: canonical };
  let c = (e) => (0, i.c)(e.trim()),
    d = (e) =>
      "object" == typeof e &&
      null !== e &&
      "string" == typeof e.mint &&
      "" !== e.mint.trim(),
    u = (e) =>
      "object" == typeof e &&
      null !== e &&
      "string" == typeof e.address &&
      "" !== e.address.trim(),
    p = (e, t) => [...e].sort((e, t) => e.hiddenAt - t.hiddenAt).slice(-t),
    f = (e) =>
      "object" != typeof e || null === e
        ? {}
        : Object.fromEntries(
            p(
              Object.values(e)
                .filter(d)
                .map((e) => ({
                  mint: e.mint,
                  symbol: "string" == typeof e.symbol ? e.symbol : "",
                  hiddenAt: Number.isFinite(e.hiddenAt) ? e.hiddenAt : 0,
                })),
              200,
            ).map((e) => [(0, i.c)(e.mint), e]),
          ),
    m = (e) =>
      "object" != typeof e || null === e
        ? {}
        : Object.fromEntries(
            p(
              Object.values(e)
                .filter(u)
                .map((e) => ({
                  address: e.address,
                  username: "string" == typeof e.username ? e.username : "",
                  hiddenAt: Number.isFinite(e.hiddenAt) ? e.hiddenAt : 0,
                })),
              200,
            ).map((e) => [c(e.address), e]),
          );
  return {
    tokenKey: canonical,
    profileKey: c,
    coerceTokens: f,
    coerceProfiles: m,
  };
}
export function createHiddenInfoBarDefinitions({
  values,
  store,
  makeBucketAdapter,
}) {
  const l = { j: values.coerceTokens, W: values.coerceProfiles, L: store },
    f = { f: makeBucketAdapter };
  return [
    {
      id: "feed.infoBar.hiddenTokens",
      section: "feed",
      scope: "device",
      default: {},
      coerce: l.j,
      adapter: (0, f.f)({
        store: () => l.L,
        select: (e) => e.hiddenTokens,
        write: ({ next: e, state: t }) => t.setField("hiddenTokens", e),
      }),
      control: { kind: "custom", component: "info-bar-hidden-tokens" },
      labelKey: "web.info_bar.hidden_tokens",
      searchTerms: ["hidden", "hide token", "unhide", "info bar"],
    },
    {
      id: "feed.infoBar.hiddenProfiles",
      section: "feed",
      scope: "device",
      default: {},
      coerce: l.W,
      adapter: (0, f.f)({
        store: () => l.L,
        select: (e) => e.hiddenProfiles,
        write: ({ next: e, state: t }) => t.setField("hiddenProfiles", e),
      }),
      control: { kind: "custom", component: "info-bar-hidden-profiles" },
      labelKey: "web.info_bar.hidden_profiles",
      searchTerms: [
        "hidden",
        "hide account",
        "hide profile",
        "unhide",
        "info bar",
      ],
    },
  ];
}
export function createHiddenInfoBarFields({
  jsx,
  jsxs,
  useMemoCache,
  useTranslation,
  translateKey,
  useSetting,
  readSetting,
  Row,
  Action,
  CloseIcon,
  formatProfileLabel,
  truncateAddress,
  normalizeDisplayText,
  values,
}) {
  const t = { jsx, jsxs },
    i = { c: useMemoCache },
    l = { f: useTranslation },
    K = { f: translateKey },
    W = { l: useSetting, o: readSetting },
    T = { s: Row, O: Action },
    r = { x6: CloseIcon },
    M = { f: formatProfileLabel },
    B = { d: truncateAddress },
    _ = { T: normalizeDisplayText },
    R = { M: values.profileKey },
    E = { c: values.tokenKey };
  function L(e) {
    let s,
      n,
      l = (0, i.c)(8),
      { listLabel: a, chips: o, onUnhide: c } = e;
    if (l[0] !== o || l[1] !== c) {
      let e;
      (l[3] !== c
        ? ((e = (e) =>
            (0, t.jsx)(
              "li",
              {
                children: (0, t.jsxs)("button", {
                  type: "button",
                  "aria-label": e.unhideLabel,
                  onClick: () => c(e.id),
                  className:
                    "group flex h-7 items-center gap-1.5 rounded-md bg-bg-secondary pl-2.5 pr-1.5 text-xs font-medium text-text-primary ring-1 ring-inset ring-border-secondary/70 transition-colors hover:ring-border-tertiary focus-visible:outline-none focus-visible:ring-text-accent/60",
                  children: [
                    (0, t.jsx)("span", { children: e.label }),
                    (0, t.jsx)(r.x6, {
                      "aria-hidden": !0,
                      className:
                        "size-3 text-text-tertiary transition-colors group-hover:text-text-primary",
                    }),
                  ],
                }),
              },
              e.id,
            )),
          (l[3] = c),
          (l[4] = e))
        : (e = l[4]),
        (s = o.map(e)),
        (l[0] = o),
        (l[1] = c),
        (l[2] = s));
    } else s = l[2];
    return (
      l[5] !== a || l[6] !== s
        ? ((n = (0, t.jsx)("ul", {
            "aria-label": a,
            className: "flex flex-wrap gap-1.5",
            children: s,
          })),
          (l[5] = a),
          (l[6] = s),
          (l[7] = n))
        : (n = l[7]),
      n
    );
  }
  function q(e, t) {
    return t.hiddenAt - e.hiddenAt;
  }
  function $(e, t) {
    return t.hiddenAt - e.hiddenAt;
  }
  const HiddenTokens = function (e) {
      let r,
        s,
        n,
        a,
        o,
        c,
        d,
        x,
        u = (0, i.c)(31),
        { definition: m } = e,
        { t: h } = (0, l.f)(),
        [p, f] = (0, W.l)("feed.infoBar.hiddenTokens"),
        y = (0, W.o)("feed.infoBar.hiddenProfiles");
      if (
        u[0] !== m.id ||
        u[1] !== m.labelKey ||
        u[2] !== p ||
        u[3] !== y ||
        u[4] !== f ||
        u[5] !== h
      ) {
        let e,
          i,
          l = Object.values(p).sort(q),
          x = 0 === l.length && 0 === Object.keys(y).length;
        u[13] !== m.labelKey || u[14] !== h
          ? ((e = (0, K.f)(h, m.labelKey)),
            (u[13] = m.labelKey),
            (u[14] = h),
            (u[15] = e))
          : (e = u[15]);
        let b = e;
        u[16] !== f
          ? ((i = (e) => {
              let t = (0, E.c)(e);
              f((e) =>
                Object.fromEntries(
                  Object.entries(e).filter((e) => {
                    let [i] = e;
                    return i !== t;
                  }),
                ),
              );
            }),
            (u[16] = f),
            (u[17] = i))
          : (i = u[17]);
        let g = i;
        ((r = T.s),
          (s = m.id),
          (n = b),
          u[18] !== x || u[19] !== h
            ? ((a = x ? h("web.info_bar.no_hidden_tokens") : void 0),
              (u[18] = x),
              (u[19] = h),
              (u[20] = a))
            : (a = u[20]),
          u[21] !== h
            ? ((o = h("web.info_bar.hidden_positions_note")),
              (u[21] = h),
              (u[22] = o))
            : (o = u[22]),
          (c =
            l.length > 0
              ? (0, t.jsx)(T.O, {
                  onClick: () => f({}),
                  children: h("web.info_bar.show_all_hidden"),
                })
              : void 0),
          (d =
            l.length > 0
              ? (0, t.jsx)(L, {
                  listLabel: b,
                  chips: l.map((e) => {
                    let t = e.symbol || (0, B.d)(e.mint, 4, 4);
                    return {
                      id: e.mint,
                      label: (0, _.T)(t, "coin-symbol"),
                      unhideLabel: h("web.info_bar.unhide_token", {
                        symbol: t,
                      }),
                    };
                  }),
                  onUnhide: g,
                })
              : null),
          (u[0] = m.id),
          (u[1] = m.labelKey),
          (u[2] = p),
          (u[3] = y),
          (u[4] = f),
          (u[5] = h),
          (u[6] = r),
          (u[7] = s),
          (u[8] = n),
          (u[9] = a),
          (u[10] = o),
          (u[11] = c),
          (u[12] = d));
      } else
        ((r = u[6]),
          (s = u[7]),
          (n = u[8]),
          (a = u[9]),
          (o = u[10]),
          (c = u[11]),
          (d = u[12]));
      return (
        u[23] !== r ||
        u[24] !== s ||
        u[25] !== n ||
        u[26] !== a ||
        u[27] !== o ||
        u[28] !== c ||
        u[29] !== d
          ? ((x = (0, t.jsx)(r, {
              settingId: s,
              title: n,
              description: a,
              note: o,
              control: c,
              children: d,
            })),
            (u[23] = r),
            (u[24] = s),
            (u[25] = n),
            (u[26] = a),
            (u[27] = o),
            (u[28] = c),
            (u[29] = d),
            (u[30] = x))
          : (x = u[30]),
        x
      );
    },
    HiddenProfiles = function (e) {
      let r,
        s,
        n,
        a,
        o,
        c,
        d = (0, i.c)(21),
        { definition: x } = e,
        { t: u } = (0, l.f)(),
        [m, h] = (0, W.l)("feed.infoBar.hiddenProfiles");
      if (
        d[0] !== x.id ||
        d[1] !== x.labelKey ||
        d[2] !== m ||
        d[3] !== h ||
        d[4] !== u
      ) {
        let e,
          i,
          l = Object.values(m).sort($);
        d[10] !== x.labelKey || d[11] !== u
          ? ((e = (0, K.f)(u, x.labelKey)),
            (d[10] = x.labelKey),
            (d[11] = u),
            (d[12] = e))
          : (e = d[12]);
        let c = e;
        d[13] !== h
          ? ((i = (e) => {
              let t = (0, R.M)(e);
              h((e) =>
                Object.fromEntries(
                  Object.entries(e).filter((e) => {
                    let [i] = e;
                    return i !== t;
                  }),
                ),
              );
            }),
            (d[13] = h),
            (d[14] = i))
          : (i = d[14]);
        let p = i;
        ((r = T.s),
          (s = x.id),
          (n = c),
          (a =
            l.length > 0
              ? (0, t.jsx)(T.O, {
                  onClick: () => h({}),
                  children: u("web.info_bar.show_all_hidden"),
                })
              : void 0),
          (o =
            l.length > 0
              ? (0, t.jsx)(L, {
                  listLabel: c,
                  chips: l.map((e) => {
                    let t = (0, M.f)({
                      address: e.address,
                      username: e.username || null,
                    });
                    return {
                      id: e.address,
                      label: (0, _.T)(t, "user-name"),
                      unhideLabel: u("web.info_bar.unhide_profile", {
                        name: t,
                      }),
                    };
                  }),
                  onUnhide: p,
                })
              : null),
          (d[0] = x.id),
          (d[1] = x.labelKey),
          (d[2] = m),
          (d[3] = h),
          (d[4] = u),
          (d[5] = r),
          (d[6] = s),
          (d[7] = n),
          (d[8] = a),
          (d[9] = o));
      } else ((r = d[5]), (s = d[6]), (n = d[7]), (a = d[8]), (o = d[9]));
      return (
        d[15] !== r || d[16] !== s || d[17] !== n || d[18] !== a || d[19] !== o
          ? ((c = (0, t.jsx)(r, {
              settingId: s,
              title: n,
              control: a,
              children: o,
            })),
            (d[15] = r),
            (d[16] = s),
            (d[17] = n),
            (d[18] = a),
            (d[19] = o),
            (d[20] = c))
          : (c = d[20]),
        c
      );
    };
  return { HiddenTokens, HiddenProfiles };
}
