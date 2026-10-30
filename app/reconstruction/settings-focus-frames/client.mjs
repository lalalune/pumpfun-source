// Source-adapted complete original Settings focus, row and section frames.
export function createSettingsFocusFrames({
  jsx,
  jsxs,
  useMemoCache,
  createContext,
  use,
  useState,
  useEffect,
  useRef,
  classNames,
  window,
}) {
  const t = { jsx, jsxs },
    n = { c: useMemoCache },
    r = { c: classNames },
    l = { createContext, use, useState, useEffect, useRef };
  let a = (0, l.createContext)(null),
    s = () => (0, l.use)(a),
    o = (e) => {
      let t,
        i,
        r = (0, n.c)(3),
        [a, s] = (0, l.useState)(!0);
      return (
        r[0] !== e
          ? ((t = () => {
              if (!e) return;
              let t = window.setTimeout(() => s(!1), 2500);
              return () => window.clearTimeout(t);
            }),
            (i = [e]),
            (r[0] = e),
            (r[1] = t),
            (r[2] = i))
          : ((t = r[1]), (i = r[2])),
        (0, l.useEffect)(t, i),
        a && e ? e : null
      );
    };
  function c(e) {
    let i,
      l,
      a = (0, n.c)(5),
      { children: s, className: o } = e;
    return (
      a[0] !== o
        ? ((i = (0, r.c)(
            "pb-1 text-[11px] font-semibold uppercase tracking-[0.1em] text-text-tertiary",
            o,
          )),
          (a[0] = o),
          (a[1] = i))
        : (i = a[1]),
      a[2] !== s || a[3] !== i
        ? ((l = (0, t.jsx)("h3", { className: i, children: s })),
          (a[2] = s),
          (a[3] = i),
          (a[4] = l))
        : (l = a[4]),
      l
    );
  }
  const FocusProvider = function (e) {
      let i,
        r = (0, n.c)(3),
        { settingId: l, children: s } = e,
        c = o(l);
      return (
        r[0] !== s || r[1] !== c
          ? ((i = (0, t.jsx)(a.Provider, { value: c, children: s })),
            (r[0] = s),
            (r[1] = c),
            (r[2] = i))
          : (i = r[2]),
        i
      );
    },
    Row = function (e) {
      let i,
        a,
        o,
        c,
        d,
        u,
        x,
        m,
        p,
        f,
        h,
        g = (0, n.c)(30),
        {
          title: b,
          description: j,
          control: v,
          children: y,
          note: _,
          settingId: w,
          dense: N,
          className: C,
        } = e,
        k = s(),
        S = void 0 !== w && k === w,
        T = (0, l.useRef)(null);
      (g[0] !== S
        ? ((i = () => {
            S &&
              T.current?.scrollIntoView?.({
                block: "center",
                behavior: "smooth",
              });
          }),
          (a = [S]),
          (g[0] = S),
          (g[1] = i),
          (g[2] = a))
        : ((i = g[1]), (a = g[2])),
        (0, l.useEffect)(i, a));
      let A = S || void 0,
        P = N ? "py-2.5" : "py-3.5",
        F = S && "bg-text-accent/[0.06] ring-1 ring-inset ring-text-accent/30";
      return (
        g[3] !== C || g[4] !== P || g[5] !== F
          ? ((o = (0, r.c)(
              "-mx-3 rounded-lg px-3 transition-colors duration-500",
              P,
              F,
              C,
            )),
            (g[3] = C),
            (g[4] = P),
            (g[5] = F),
            (g[6] = o))
          : (o = g[6]),
        g[7] !== b
          ? ((c = (0, t.jsx)("h4", {
              className: "text-[13px] font-medium leading-5 text-text-primary",
              children: b,
            })),
            (g[7] = b),
            (g[8] = c))
          : (c = g[8]),
        g[9] !== j
          ? ((d = j
              ? (0, t.jsx)("p", {
                  className:
                    "mt-0.5 max-w-[56ch] text-xs leading-[1.45] text-text-tertiary",
                  children: j,
                })
              : null),
            (g[9] = j),
            (g[10] = d))
          : (d = g[10]),
        g[11] !== _
          ? ((u = _
              ? (0, t.jsx)("p", {
                  className:
                    "mt-1 text-[11px] leading-snug text-text-quaternary",
                  children: _,
                })
              : null),
            (g[11] = _),
            (g[12] = u))
          : (u = g[12]),
        g[13] !== c || g[14] !== d || g[15] !== u
          ? ((x = (0, t.jsxs)("div", {
              className: "min-w-0 flex-1",
              children: [c, d, u],
            })),
            (g[13] = c),
            (g[14] = d),
            (g[15] = u),
            (g[16] = x))
          : (x = g[16]),
        g[17] !== v
          ? ((m = v
              ? (0, t.jsx)("div", {
                  className: "flex shrink-0 items-center justify-end",
                  children: v,
                })
              : null),
            (g[17] = v),
            (g[18] = m))
          : (m = g[18]),
        g[19] !== x || g[20] !== m
          ? ((p = (0, t.jsxs)("div", {
              className: "flex items-start justify-between gap-6",
              children: [x, m],
            })),
            (g[19] = x),
            (g[20] = m),
            (g[21] = p))
          : (p = g[21]),
        g[22] !== y
          ? ((f = y
              ? (0, t.jsx)("div", { className: "mt-3", children: y })
              : null),
            (g[22] = y),
            (g[23] = f))
          : (f = g[23]),
        g[24] !== w || g[25] !== p || g[26] !== f || g[27] !== A || g[28] !== o
          ? ((h = (0, t.jsxs)("div", {
              ref: T,
              "data-setting-id": w,
              "data-focused": A,
              className: o,
              children: [p, f],
            })),
            (g[24] = w),
            (g[25] = p),
            (g[26] = f),
            (g[27] = A),
            (g[28] = o),
            (g[29] = h))
          : (h = g[29]),
        h
      );
    },
    Section = function (e) {
      let i,
        l,
        a,
        s,
        o,
        d = (0, n.c)(15),
        {
          label: u,
          description: x,
          children: m,
          className: p,
          "data-testid": f,
        } = e;
      return (
        d[0] !== p
          ? ((i = (0, r.c)("flex flex-col", p)), (d[0] = p), (d[1] = i))
          : (i = d[1]),
        d[2] !== x || d[3] !== u
          ? ((l = u
              ? (0, t.jsx)(c, { className: x ? "pb-0" : void 0, children: u })
              : null),
            (d[2] = x),
            (d[3] = u),
            (d[4] = l))
          : (l = d[4]),
        d[5] !== x
          ? ((a = x
              ? (0, t.jsx)("p", {
                  className: "pb-2 text-xs leading-[1.45] text-text-tertiary",
                  children: x,
                })
              : null),
            (d[5] = x),
            (d[6] = a))
          : (a = d[6]),
        d[7] !== m
          ? ((s = (0, t.jsx)("div", {
              className: "divide-y divide-border-secondary",
              children: m,
            })),
            (d[7] = m),
            (d[8] = s))
          : (s = d[8]),
        d[9] !== i || d[10] !== l || d[11] !== a || d[12] !== s || d[13] !== f
          ? ((o = (0, t.jsxs)("section", {
              "data-testid": f,
              className: i,
              children: [l, a, s],
            })),
            (d[9] = i),
            (d[10] = l),
            (d[11] = a),
            (d[12] = s),
            (d[13] = f),
            (d[14] = o))
          : (o = d[14]),
        o
      );
    };
  return {
    FocusContext: a,
    useFocusSettingId: s,
    useTransientSettingId: o,
    FocusProvider,
    Row,
    Section,
  };
}
