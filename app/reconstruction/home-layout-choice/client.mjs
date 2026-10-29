// Source-adapted original choice flow. Explicit ports only; importing reads no browser state.
export function createHomeLayoutCookie({ document, location }) {
  let t = "home_feed_layout",
    r = { GRID: "grid", TABLE: "table" },
    i = r.TABLE,
    s = new Set(Object.values(r)),
    n = (e) => (e === r.GRID ? r.GRID : e === r.TABLE ? r.TABLE : i);
  return {
    key: t,
    layouts: r,
    defaultLayout: i,
    coerce: n,
    read: () => {
      if ("u" < typeof document) return null;
      for (let e of document.cookie.split(";")) {
        let [r, ...i] = e.trim().split("=");
        if (r === t && i.length > 0) {
          let e = decodeURIComponent(i.join("="));
          return s.has(e) ? e : null;
        }
      }
      return null;
    },
    readServer: (e) => {
      if (!e) return i;
      for (let r of e.split(";")) {
        let [e, ...i] = r.trim().split("=");
        if (e === t && i.length > 0) return n(decodeURIComponent(i.join("=")));
      }
      return i;
    },
    write: (e) => {
      if ("u" < typeof document) return;
      let r = "https:" === location.protocol ? "; secure" : "";
      document.cookie = `${t}=${e}; path=/; max-age=31536000; samesite=lax${r}`;
    },
  };
}
export function createCookieAdapter(options) {
  return (({ read: e, write: t, readServer: r }) => {
    let i = new Set();
    return {
      kind: "cookie",
      read: () => e() ?? void 0,
      write: (e) => {
        (t(e), i.forEach((e) => e()));
      },
      subscribe: (e) => (
        i.add(e),
        () => {
          i.delete(e);
        }
      ),
      readServer: r ? ({ cookieHeader: e }) => r(e) ?? void 0 : void 0,
    };
  })(options);
}
export function createHomeLayoutDefinition({ layout, cookieAdapter }) {
  const r = {
      x: layout.defaultLayout,
      E: layout.layouts,
      g: layout.coerce,
      i: layout.read,
      m: layout.write,
      b: layout.readServer,
    },
    u = { f: cookieAdapter },
    b = { f: (e) => e };
  return (0, b.f)({
    id: "feed.homeLayout",
    section: "feed",
    scope: "device",
    default: r.x,
    coerce: (e) => (0, r.g)("string" == typeof e ? e : null),
    adapter: (0, u.f)({
      read: () => (0, r.i)(),
      write: (e) => (0, r.m)(e),
      readServer: (e) => (0, r.b)(e),
    }),
    control: {
      kind: "pills",
      options: [
        {
          value: r.E.GRID,
          labelKey: "web.home.layout_grid",
          preview: "layout-grid",
        },
        {
          value: r.E.TABLE,
          labelKey: "web.home.layout_table",
          preview: "layout-table",
        },
      ],
    },
    labelKey: "web.home.feed_layout_a11y",
    descriptionKey: "web.settings.feed.layout_description",
    searchTerms: ["grid", "table", "list", "layout", "cards"],
  });
}
export function createLayoutPreviews({ jsx, jsxs, useMemoCache }) {
  const t = { jsx, jsxs },
    i = { c: useMemoCache };
  let c = (e) => {
      let r,
        s,
        n = (0, i.c)(3),
        { children: l } = e;
      return (
        n[0] === Symbol.for("react.memo_cache_sentinel")
          ? ((r = (0, t.jsx)("rect", {
              className: "text-bg-primary",
              fill: "currentColor",
              x: "0",
              y: "0",
              width: "120",
              height: "64",
              rx: "6",
            })),
            (n[0] = r))
          : (r = n[0]),
        n[1] !== l
          ? ((s = (0, t.jsxs)("g", { children: [r, l] })),
            (n[1] = l),
            (n[2] = s))
          : (s = n[2]),
        s
      );
    },
    d = (e) => {
      let r,
        s,
        n,
        l,
        a,
        o,
        c = (0, i.c)(9),
        { x: d, y: x, up: u } = e,
        m = `translate(${d} ${x})`;
      c[0] === Symbol.for("react.memo_cache_sentinel")
        ? ((r = (0, t.jsx)("rect", {
            className: "text-bg-tertiary",
            fill: "currentColor",
            width: "34",
            height: "26",
            rx: "3",
          })),
          (s = (0, t.jsx)("rect", {
            className: "text-text-tertiary",
            fill: "currentColor",
            opacity: "0.45",
            x: "3",
            y: "3",
            width: "28",
            height: "11",
            rx: "2",
          })),
          (n = (0, t.jsx)("rect", {
            className: "text-text-primary",
            fill: "currentColor",
            opacity: "0.9",
            x: "3",
            y: "17",
            width: "13",
            height: "2.4",
            rx: "1.2",
          })),
          (c[0] = r),
          (c[1] = s),
          (c[2] = n))
        : ((r = c[0]), (s = c[1]), (n = c[2]));
      let h = u ? "text-gain" : "text-loss";
      return (
        c[3] !== h
          ? ((l = (0, t.jsx)("rect", {
              className: h,
              fill: "currentColor",
              x: "21",
              y: "16.6",
              width: "10",
              height: "3.2",
              rx: "1.6",
            })),
            (c[3] = h),
            (c[4] = l))
          : (l = c[4]),
        c[5] === Symbol.for("react.memo_cache_sentinel")
          ? ((a = (0, t.jsx)("rect", {
              className: "text-text-tertiary",
              fill: "currentColor",
              x: "3",
              y: "21.5",
              width: "20",
              height: "2",
              rx: "1",
            })),
            (c[5] = a))
          : (a = c[5]),
        c[6] !== m || c[7] !== l
          ? ((o = (0, t.jsxs)("g", {
              transform: m,
              children: [r, s, n, l, a],
            })),
            (c[6] = m),
            (c[7] = l),
            (c[8] = o))
          : (o = c[8]),
        o
      );
    },
    x = (e) => {
      let r,
        s,
        n,
        l,
        a,
        o = (0, i.c)(18),
        { y: c, up: d, nameWidth: x, header: u } = e,
        m = void 0 !== u && u,
        h = `translate(0 ${c})`;
      o[0] !== m
        ? ((r = m
            ? null
            : (0, t.jsx)("circle", {
                className: "text-text-tertiary",
                fill: "currentColor",
                opacity: "0.55",
                cx: "12",
                cy: "4",
                r: "3",
              })),
          (o[0] = m),
          (o[1] = r))
        : (r = o[1]);
      let p = m ? "text-text-tertiary" : "text-text-primary",
        f = m ? 0.5 : 0.9,
        y = m ? 8 : 18;
      o[2] !== x || o[3] !== p || o[4] !== f || o[5] !== y
        ? ((s = (0, t.jsx)("rect", {
            className: p,
            fill: "currentColor",
            opacity: f,
            x: y,
            y: "2.8",
            width: x,
            height: "2.4",
            rx: "1.2",
          })),
          (o[2] = x),
          (o[3] = p),
          (o[4] = f),
          (o[5] = y),
          (o[6] = s))
        : (s = o[6]);
      let b = m ? 0.5 : 0.8;
      o[7] !== b
        ? ((n = (0, t.jsx)("rect", {
            className: "text-text-tertiary",
            fill: "currentColor",
            opacity: b,
            x: "62",
            y: "2.8",
            width: "14",
            height: "2.4",
            rx: "1.2",
          })),
          (o[7] = b),
          (o[8] = n))
        : (n = o[8]);
      let g = m ? "text-text-tertiary" : d ? "text-gain" : "text-loss",
        j = m ? 0.5 : 1;
      return (
        o[9] !== g || o[10] !== j
          ? ((l = (0, t.jsx)("rect", {
              className: g,
              fill: "currentColor",
              opacity: j,
              x: "90",
              y: "2.4",
              width: "22",
              height: "3.2",
              rx: "1.6",
            })),
            (o[9] = g),
            (o[10] = j),
            (o[11] = l))
          : (l = o[11]),
        o[12] !== l || o[13] !== h || o[14] !== r || o[15] !== s || o[16] !== n
          ? ((a = (0, t.jsxs)("g", { transform: h, children: [r, s, n, l] })),
            (o[12] = l),
            (o[13] = h),
            (o[14] = r),
            (o[15] = s),
            (o[16] = n),
            (o[17] = a))
          : (a = o[17]),
        a
      );
    };
  let j = {
    "layout-grid": (0, t.jsxs)(c, {
      children: [
        (0, t.jsx)(d, { x: 6, y: 5, up: !0 }),
        (0, t.jsx)(d, { x: 43, y: 5, up: !1 }),
        (0, t.jsx)(d, { x: 80, y: 5, up: !0 }),
        (0, t.jsx)(d, { x: 6, y: 35, up: !0 }),
        (0, t.jsx)(d, { x: 43, y: 35, up: !0 }),
        (0, t.jsx)(d, { x: 80, y: 35, up: !1 }),
      ],
    }),
    "layout-table": (0, t.jsxs)(c, {
      children: [
        (0, t.jsx)(x, { y: 4, nameWidth: 18, header: !0 }),
        (0, t.jsx)("line", {
          className: "text-border-secondary",
          stroke: "currentColor",
          strokeWidth: "0.6",
          x1: "4",
          x2: "116",
          y1: "13",
          y2: "13",
        }),
        (0, t.jsx)(x, { y: 15, nameWidth: 24, up: !0 }),
        (0, t.jsx)(x, { y: 26, nameWidth: 18, up: !1 }),
        (0, t.jsx)(x, { y: 37, nameWidth: 28, up: !0 }),
        (0, t.jsx)(x, { y: 48, nameWidth: 21, up: !0 }),
      ],
    }),
  };
  let v = (e) => void 0 !== e && e in j;
  function w(e) {
    let r,
      s = (0, i.c)(2),
      { id: n } = e,
      l = j[n];
    return l
      ? (s[0] !== l
          ? ((r = (0, t.jsx)("svg", {
              "aria-hidden": !0,
              viewBox: "0 0 120 64",
              className: "block h-auto w-full",
              focusable: "false",
              children: l,
            })),
            (s[0] = l),
            (s[1] = r))
          : (r = s[1]),
        r)
      : null;
  }
  return { isPreview: v, Preview: w };
}
export function createChoiceRenderer({
  jsx,
  jsxs,
  useMemoCache,
  useTranslation,
  translateKey,
  markString,
  classNames,
  previews,
}) {
  const t = { jsx, jsxs },
    i = { c: useMemoCache },
    l = { f: useTranslation },
    K = { f: translateKey },
    _ = { T: markString },
    o = { c: classNames },
    v = previews.isPreview,
    w = previews.Preview;
  function k(e) {
    let r,
      s,
      n,
      l = (0, i.c)(16),
      {
        choices: a,
        value: c,
        onChange: d,
        label: x,
        isDisabled: u,
        wrap: m,
        className: h,
      } = e;
    if (
      (l[0] !== h || l[1] !== m
        ? ((r = (0, o.c)(
            ((e = !1) =>
              (0, o.c)(
                "inline-flex max-w-full items-center gap-0.5 rounded-md bg-bg-tertiary p-0.5",
                e && "flex-wrap",
              ))(m),
            h,
          )),
          (l[0] = h),
          (l[1] = m),
          (l[2] = r))
        : (r = l[2]),
      l[3] !== a || l[4] !== u || l[5] !== d || l[6] !== c)
    ) {
      let e;
      (l[8] !== u || l[9] !== d || l[10] !== c
        ? ((e = (e) => {
            let i = Object.is(e.value, c);
            return (0, t.jsx)(
              "button",
              {
                type: "button",
                role: "radio",
                "aria-checked": i,
                disabled: u,
                onClick: () => d(e.value),
                className: ((e, t = !1) =>
                  (0, o.c)(
                    "h-7 whitespace-nowrap rounded-md px-2.5 text-xs font-medium leading-none tabular-nums transition-colors",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-text-accent/50",
                    e
                      ? "bg-bg-quaternary text-text-primary"
                      : "text-text-tertiary hover:text-text-primary",
                    t && "cursor-not-allowed opacity-50",
                  ))(i, u),
                children: e.label,
              },
              String(e.value),
            );
          }),
          (l[8] = u),
          (l[9] = d),
          (l[10] = c),
          (l[11] = e))
        : (e = l[11]),
        (s = a.map(e)),
        (l[3] = a),
        (l[4] = u),
        (l[5] = d),
        (l[6] = c),
        (l[7] = s));
    } else s = l[7];
    return (
      l[12] !== x || l[13] !== r || l[14] !== s
        ? ((n = (0, t.jsx)("div", {
            role: "radiogroup",
            "aria-label": x,
            className: r,
            children: s,
          })),
          (l[12] = x),
          (l[13] = r),
          (l[14] = s),
          (l[15] = n))
        : (n = l[15]),
      n
    );
  }
  let S = (e, t) =>
      t.labelKey
        ? (0, K.f)(e, t.labelKey)
        : (0, _.T)(t.rawLabel ?? "", "unicode-symbol"),
    P = (e) => e.length <= 4 && e.join("").length <= 26;
  function I(e) {
    let r,
      s,
      n = (0, i.c)(37),
      { options: a, value: c, onChange: d, label: x, isDisabled: u } = e,
      { t: m } = (0, l.f)();
    if (!a.some(A)) {
      let e, i, r, s, l, o, h, p;
      if (
        n[0] !== u ||
        n[1] !== x ||
        n[2] !== d ||
        n[3] !== a ||
        n[4] !== m ||
        n[5] !== c
      ) {
        let t;
        n[13] !== m
          ? ((t = (e) => S(m, e)), (n[13] = m), (n[14] = t))
          : (t = n[14]);
        let p = a.map(t);
        ((e = k),
          (r = a.map((e, t) => ({ value: e.value, label: p[t] }))),
          (s = c),
          (l = d),
          (o = x),
          (h = u),
          (i = P(p)),
          (n[0] = u),
          (n[1] = x),
          (n[2] = d),
          (n[3] = a),
          (n[4] = m),
          (n[5] = c),
          (n[6] = e),
          (n[7] = i),
          (n[8] = r),
          (n[9] = s),
          (n[10] = l),
          (n[11] = o),
          (n[12] = h));
      } else
        ((e = n[6]),
          (i = n[7]),
          (r = n[8]),
          (s = n[9]),
          (l = n[10]),
          (o = n[11]),
          (h = n[12]));
      let f = !i;
      return (
        n[15] !== e ||
        n[16] !== r ||
        n[17] !== s ||
        n[18] !== l ||
        n[19] !== o ||
        n[20] !== h ||
        n[21] !== f
          ? ((p = (0, t.jsx)(e, {
              choices: r,
              value: s,
              onChange: l,
              label: o,
              isDisabled: h,
              wrap: f,
            })),
            (n[15] = e),
            (n[16] = r),
            (n[17] = s),
            (n[18] = l),
            (n[19] = o),
            (n[20] = h),
            (n[21] = f),
            (n[22] = p))
          : (p = n[22]),
        p
      );
    }
    if (
      n[23] !== u ||
      n[24] !== d ||
      n[25] !== a ||
      n[26] !== m ||
      n[27] !== c
    ) {
      let e;
      (n[29] !== u || n[30] !== d || n[31] !== m || n[32] !== c
        ? ((e = (e) => {
            let i = Object.is(e.value, c);
            return (0, t.jsxs)(
              "button",
              {
                type: "button",
                role: "radio",
                "aria-checked": i,
                disabled: u,
                onClick: () => d(e.value),
                className: (0, o.c)(
                  "group flex flex-col items-stretch rounded-lg bg-bg-secondary p-1 text-left ring-1 ring-inset transition-[box-shadow,color]",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-text-accent/60",
                  i
                    ? "text-text-primary ring-text-accent"
                    : "text-text-tertiary ring-border-secondary/70 hover:text-text-primary hover:ring-border-tertiary",
                  u && "cursor-not-allowed opacity-50",
                ),
                children: [
                  v(e.preview)
                    ? (0, t.jsx)("div", {
                        className: "overflow-hidden rounded-md",
                        children: (0, t.jsx)(w, { id: e.preview }),
                      })
                    : null,
                  (0, t.jsxs)("span", {
                    className:
                      "flex items-center justify-between gap-2 px-1.5 pb-1 pt-1.5",
                    children: [
                      (0, t.jsx)("span", {
                        className: "truncate text-xs font-medium",
                        children: S(m, e),
                      }),
                      (0, t.jsx)("span", {
                        "aria-hidden": !0,
                        className: (0, o.c)(
                          "size-1.5 shrink-0 rounded-full transition-colors",
                          i ? "bg-text-accent" : "bg-border-tertiary",
                        ),
                      }),
                    ],
                  }),
                ],
              },
              String(e.value),
            );
          }),
          (n[29] = u),
          (n[30] = d),
          (n[31] = m),
          (n[32] = c),
          (n[33] = e))
        : (e = n[33]),
        (r = a.map(e)),
        (n[23] = u),
        (n[24] = d),
        (n[25] = a),
        (n[26] = m),
        (n[27] = c),
        (n[28] = r));
    } else r = n[28];
    return (
      n[34] !== x || n[35] !== r
        ? ((s = (0, t.jsx)("div", {
            role: "radiogroup",
            "aria-label": x,
            className: "grid grid-cols-2 gap-2 sm:grid-cols-4",
            children: r,
          })),
          (n[34] = x),
          (n[35] = r),
          (n[36] = s))
        : (s = n[36]),
      s
    );
  }
  function A(e) {
    return v(e.preview);
  }
  return { Choice: I, Pills: k, labelOption: S, isCompact: P };
}
export function createSettingsField({
  jsx,
  jsxs,
  useMemoCache,
  useTranslation,
  translateKey,
  useHydrated,
  settings,
  Row,
  Switch,
  NumberInput,
  customControls,
  choice,
  previews,
}) {
  const t = { jsx, jsxs },
    i = { c: useMemoCache },
    l = { f: useTranslation },
    K = { f: translateKey },
    el = { f: useHydrated },
    W = { o: settings.useSetting, Z: settings.useSetter },
    T = { s: Row },
    ec = { f: Switch },
    eo = NumberInput,
    en = customControls,
    I = choice.Choice,
    P = choice.isCompact,
    S = choice.labelOption,
    v = previews.isPreview;
  function ed(e) {
    let r,
      s,
      n,
      a,
      o,
      c,
      d = (0, i.c)(51),
      { definition: x, compact: u } = e,
      m = void 0 !== u && u,
      { t: h } = (0, l.f)(),
      p = x.id,
      f = (0, W.o)(p),
      y = (0, W.Z)(p),
      b = (0, el.f)(),
      g = x.control;
    if ("hidden" === g.kind) return null;
    if ("custom" === g.kind) {
      let e,
        i = en[g.component];
      return i
        ? (d[0] !== i || d[1] !== x
            ? ((e = (0, t.jsx)(i, { definition: x })),
              (d[0] = i),
              (d[1] = x),
              (d[2] = e))
            : (e = d[2]),
          e)
        : null;
    }
    d[3] !== x.labelKey || d[4] !== h
      ? ((r = (0, K.f)(h, x.labelKey)),
        (d[3] = x.labelKey),
        (d[4] = h),
        (d[5] = r))
      : (r = d[5]);
    let j = r;
    d[6] !== m || d[7] !== x.descriptionKey || d[8] !== h
      ? ((s = x.descriptionKey && !m ? (0, K.f)(h, x.descriptionKey) : void 0),
        (d[6] = m),
        (d[7] = x.descriptionKey),
        (d[8] = h),
        (d[9] = s))
      : (s = d[9]);
    let v = s,
      w = !0 === x.firstPaintSensitive && !b;
    if ("switch" === g.kind) {
      let e, i;
      return (
        d[10] !== x || d[11] !== j
          ? ((e = (0, t.jsx)(ec.f, { definition: x, label: j })),
            (d[10] = x),
            (d[11] = j),
            (d[12] = e))
          : (e = d[12]),
        d[13] !== m ||
        d[14] !== x.id ||
        d[15] !== v ||
        d[16] !== e ||
        d[17] !== j
          ? ((i = (0, t.jsx)(T.s, {
              settingId: x.id,
              title: j,
              description: v,
              dense: m,
              control: e,
            })),
            (d[13] = m),
            (d[14] = x.id),
            (d[15] = v),
            (d[16] = e),
            (d[17] = j),
            (d[18] = i))
          : (i = d[18]),
        i
      );
    }
    if ("number" === g.kind) {
      let e,
        i,
        r,
        s = "number" == typeof f ? f : Number(f);
      return (
        d[19] !== y
          ? ((e = (e) => y(e)), (d[19] = y), (d[20] = e))
          : (e = d[20]),
        d[21] !== g.min ||
        d[22] !== g.step ||
        d[23] !== g.unit ||
        d[24] !== w ||
        d[25] !== s ||
        d[26] !== e ||
        d[27] !== j
          ? ((i = (0, t.jsx)(eo, {
              value: s,
              onCommit: e,
              min: g.min,
              step: g.step,
              unit: g.unit,
              label: j,
              isDisabled: w,
            })),
            (d[21] = g.min),
            (d[22] = g.step),
            (d[23] = g.unit),
            (d[24] = w),
            (d[25] = s),
            (d[26] = e),
            (d[27] = j),
            (d[28] = i))
          : (i = d[28]),
        d[29] !== x.id || d[30] !== v || d[31] !== i || d[32] !== j
          ? ((r = (0, t.jsx)(T.s, {
              settingId: x.id,
              title: j,
              description: v,
              control: i,
            })),
            (d[29] = x.id),
            (d[30] = v),
            (d[31] = i),
            (d[32] = j),
            (d[33] = r))
          : (r = d[33]),
        r
      );
    }
    (d[34] !== y ? ((n = (e) => y(e)), (d[34] = y), (d[35] = n)) : (n = d[35]),
      d[36] !== g.options ||
      d[37] !== w ||
      d[38] !== n ||
      d[39] !== j ||
      d[40] !== f
        ? ((a = (0, t.jsx)(I, {
            options: g.options,
            value: f,
            onChange: n,
            label: j,
            isDisabled: w,
          })),
          (d[36] = g.options),
          (d[37] = w),
          (d[38] = n),
          (d[39] = j),
          (d[40] = f),
          (d[41] = a))
        : (a = d[41]));
    let N = a;
    d[42] !== g.options || d[43] !== h
      ? ((o = !g.options.some(ex) && P(g.options.map((e) => S(h, e)))),
        (d[42] = g.options),
        (d[43] = h),
        (d[44] = o))
      : (o = d[44]);
    let _ = o;
    return (
      d[45] !== x.id || d[46] !== v || d[47] !== _ || d[48] !== N || d[49] !== j
        ? ((c = _
            ? (0, t.jsx)(T.s, {
                settingId: x.id,
                title: j,
                description: v,
                control: N,
              })
            : (0, t.jsx)(T.s, {
                settingId: x.id,
                title: j,
                description: v,
                children: N,
              })),
          (d[45] = x.id),
          (d[46] = v),
          (d[47] = _),
          (d[48] = N),
          (d[49] = j),
          (d[50] = c))
        : (c = d[50]),
      c
    );
  }
  function ex(e) {
    return v(e.preview);
  }
  return ed;
}
