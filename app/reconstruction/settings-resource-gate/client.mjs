// Source-adapted original Settings resource-attempt and complete content/loading branch.
// Browser/i18n/translation-provider/section capabilities are explicit. No global Settings mount.
export function createSettingsResourceContent({
  jsx,
  jsxs,
  useMemoCache,
  useState,
  useEffect,
  useTranslation,
  normalizeLocale,
  defaultLocale,
  prefetchCatalog,
  SearchResults,
  Section,
  FocusProvider,
}) {
  const t = { jsx, jsxs },
    i = { c: useMemoCache },
    n = { useState, useEffect },
    l = { f: useTranslation },
    eB = { v: normalizeLocale, T: defaultLocale },
    e$ = { u: prefetchCatalog },
    a = { _: { Provider: FocusProvider } },
    eb = SearchResults,
    eF = Section;
  let eE = [0, 1, 2, 3, 4];
  function eq() {
    let e,
      r = (0, i.c)(1);
    return (
      r[0] === Symbol.for("react.memo_cache_sentinel")
        ? ((e = (0, t.jsx)("div", {
            "aria-hidden": !0,
            className: "flex flex-col divide-y divide-border-secondary",
            children: eE.map(eX),
          })),
          (r[0] = e))
        : (e = r[0]),
      e
    );
  }
  function eX(e) {
    return (0, t.jsxs)(
      "div",
      {
        className: "flex items-center justify-between gap-6 py-4",
        children: [
          (0, t.jsxs)("div", {
            className: "flex flex-col gap-2",
            children: [
              (0, t.jsx)("div", {
                className: "h-3 w-40 animate-pulse rounded bg-bg-tertiary",
              }),
              (0, t.jsx)("div", {
                className: "h-2.5 w-64 animate-pulse rounded bg-bg-secondary",
              }),
            ],
          }),
          (0, t.jsx)("div", {
            className: "h-5 w-9 animate-pulse rounded-full bg-bg-secondary",
          }),
        ],
      },
      e,
    );
  }
  function useSettingsResourceAttempt() {
    return (() => {
      let e,
        t,
        r,
        s = (0, i.c)(6),
        { i18n: a } = (0, l.f)();
      s[0] !== a
        ? ((e = () => a.exists("web.trade.max_slippage")),
          (s[0] = a),
          (s[1] = e))
        : (e = s[1]);
      let [o, c] = (0, n.useState)(e);
      return (
        s[2] !== a || s[3] !== o
          ? ((t = () => {
              if (o) return;
              let e = !1,
                t = (0, eB.v)(a.language) ?? eB.T;
              return (
                (0, e$.u)(a, t).finally(() => {
                  e || c(!0);
                }),
                () => {
                  e = !0;
                }
              );
            }),
            (r = [a, o]),
            (s[2] = a),
            (s[3] = o),
            (s[4] = t),
            (s[5] = r))
          : ((t = s[4]), (r = s[5])),
        (0, n.useEffect)(t, r),
        o
      );
    })();
  }
  function SettingsResourceContent({
    query: et,
    visibleSections: ea,
    section: eo,
    focusValue: ee,
    onRequestClose: G,
    scrollRef: el,
  }) {
    let O,
      W,
      o,
      X = (0, i.c)(100),
      J = useSettingsResourceAttempt();
    X[0] !== et ? ((o = et.trim()), (X[0] = et), (X[1] = o)) : (o = X[1]);
    let ex = o.length > 0;
    let ew = !J || void 0;
    (X[60] !== eo ||
    X[61] !== J ||
    X[62] !== ee ||
    X[63] !== G ||
    X[64] !== et ||
    X[65] !== ex ||
    X[66] !== ea
      ? ((O = J
          ? ex
            ? (0, t.jsx)(eb, { query: et.trim(), visibleSections: ea })
            : (0, t.jsx)(a._.Provider, {
                value: ee,
                children: (0, t.jsx)(
                  "div",
                  {
                    className: "animate-in fade-in-0 duration-200",
                    children: (0, t.jsx)(eF, {
                      section: eo,
                      onRequestClose: G,
                    }),
                  },
                  eo,
                ),
              })
          : (0, t.jsx)(eq, {})),
        (X[60] = eo),
        (X[61] = J),
        (X[62] = ee),
        (X[63] = G),
        (X[64] = et),
        (X[65] = ex),
        (X[66] = ea),
        (X[67] = O))
      : (O = X[67]),
      X[68] !== ew || X[69] !== O
        ? ((W = (0, t.jsx)("div", {
            ref: el,
            className:
              "custom-scrollbar min-h-0 flex-1 overflow-y-auto px-5 pb-6 pt-4 [mask-image:linear-gradient(to_bottom,transparent,#000_16px,#000_calc(100%-20px),transparent)]",
            "aria-busy": ew,
            children: O,
          })),
          (X[68] = ew),
          (X[69] = O),
          (X[70] = W))
        : (W = X[70]));
    return W;
  }
  return { SettingsResourceContent, Loading: eq, useSettingsResourceAttempt };
}
