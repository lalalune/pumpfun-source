// Full original Settings display/controller owner. Exactly2documented hook-port substitutions; no provider acquisition.
export function createSettingsModalOwner({
  jsx,
  jsxs,
  useMemoCache,
  useState,
  useEffect,
  useId,
  useRef,
  useTranslation,
  translateKey,
  useVisibleSections,
  useSettingsResourceAttempt,
  useTransientSettingId,
  FocusContextProvider,
  definitionsForSection,
  SearchResults,
  SectionContent,
  Loading,
  resetSection,
  DialogRoot,
  DialogContent,
  TabsRoot,
  TabsList,
  TabsTrigger,
  Button,
  CloseIcon,
  SearchIcon,
  ResetIcon,
  DeviceIcon,
}) {
  const t = { jsx, jsxs },
    i = { c: useMemoCache },
    n = { useState, useEffect, useId, useRef },
    l = { f: useTranslation },
    K = { f: translateKey },
    a = { h: useTransientSettingId, _: { Provider: FocusContextProvider } },
    ep = { n: definitionsForSection },
    eb = SearchResults,
    eF = SectionContent,
    eq = Loading,
    V = { t: resetSection },
    s = {
      v: DialogRoot,
      s: DialogContent,
      i: TabsRoot,
      R: TabsList,
      V: TabsTrigger,
      K: Button,
    },
    r = { x6: CloseIcon, L3: SearchIcon, B4: ResetIcon, mD: DeviceIcon };
  function eU(e) {
    return !1 !== e.resettable;
  }
  function eH(e) {
    return e.id;
  }
  return function (e) {
    let o,
      c,
      d,
      x,
      u,
      m,
      h,
      p,
      f,
      y,
      b,
      g,
      j,
      v,
      w,
      N,
      _,
      C,
      k,
      S,
      P,
      I,
      A,
      T,
      O,
      W,
      z,
      F,
      L,
      M,
      R,
      $,
      B,
      E,
      q,
      X = (0, i.c)(100),
      { section: U, focusSettingId: H, onSectionChange: Z, onClose: G } = e,
      { t: Q } = (0, l.f)(),
      Y = useVisibleSections(),
      J = useSettingsResourceAttempt(),
      ee = (0, a.h)(H),
      [et, ei] = (0, n.useState)(""),
      [er, es] = (0, n.useState)(!1),
      en = (0, n.useId)(),
      el = (0, n.useRef)(null),
      ea = Y.map(eH),
      eo = ea.includes(U) ? U : (ea[0] ?? "trading"),
      ec = Y.find((e) => e.id === eo),
      ed = ec ? (0, K.f)(Q, ec.labelKey) : "";
    X[0] !== et ? ((o = et.trim()), (X[0] = et), (X[1] = o)) : (o = X[1]);
    let ex = o.length > 0,
      eh = !ex && (0, ep.n)(eo).some(eU),
      ef = !ex && "notifications" !== eo;
    (X[2] === Symbol.for("react.memo_cache_sentinel")
      ? ((c = () => {
          el.current?.scrollTo?.({ top: 0 });
        }),
        (X[2] = c))
      : (c = X[2]),
      X[3] !== eo || X[4] !== ex
        ? ((d = [eo, ex]), (X[3] = eo), (X[4] = ex), (X[5] = d))
        : (d = X[5]),
      (0, n.useEffect)(c, d),
      X[6] !== Z
        ? ((x = (e) => {
            (es(!1), Z(e));
          }),
          (X[6] = Z),
          (X[7] = x))
        : (x = X[7]));
    let eg = x,
      ej = s.v;
    X[8] !== G
      ? ((u = (e) => {
          e || G();
        }),
        (X[8] = G),
        (X[9] = u))
      : (u = X[9]);
    let ev = s.s;
    if (
      (X[10] !== Q
        ? ((m = Q("web.settings.title")), (X[10] = Q), (X[11] = m))
        : (m = X[11]),
      X[12] !== m
        ? ((h = (0, t.jsx)("h2", {
            className: "text-[15px] font-semibold text-text-primary",
            children: m,
          })),
          (X[12] = m),
          (X[13] = h))
        : (h = X[13]),
      X[14] !== Q
        ? ((p = Q("web.settings.close")), (X[14] = Q), (X[15] = p))
        : (p = X[15]),
      X[16] === Symbol.for("react.memo_cache_sentinel")
        ? ((f = (0, t.jsx)(r.x6, { className: "size-4" })), (X[16] = f))
        : (f = X[16]),
      X[17] !== G || X[18] !== p
        ? ((y = (0, t.jsx)("button", {
            type: "button",
            onClick: G,
            "aria-label": p,
            className:
              "-mr-1.5 flex size-7 items-center justify-center rounded-md text-text-tertiary transition-colors hover:bg-bg-secondary hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-text-accent/40",
            children: f,
          })),
          (X[17] = G),
          (X[18] = p),
          (X[19] = y))
        : (y = X[19]),
      X[20] !== h || X[21] !== y
        ? ((b = (0, t.jsxs)("div", {
            className: "flex items-center justify-between gap-3",
            children: [h, y],
          })),
          (X[20] = h),
          (X[21] = y),
          (X[22] = b))
        : (b = X[22]),
      X[23] !== eg
        ? ((g = (e) => eg(e)), (X[23] = eg), (X[24] = g))
        : (g = X[24]),
      X[25] !== Q
        ? ((j = Q("web.settings.title")), (X[25] = Q), (X[26] = j))
        : (j = X[26]),
      X[27] !== Y || X[28] !== Q)
    ) {
      let e;
      (X[30] !== Q
        ? ((e = (e) =>
            (0, t.jsx)(
              s.V,
              {
                value: e.id,
                className: "mb-1.5 px-2.5 py-1.5 text-[13px]",
                children: (0, K.f)(Q, e.tabLabelKey),
              },
              e.id,
            )),
          (X[30] = Q),
          (X[31] = e))
        : (e = X[31]),
        (v = Y.map(e)),
        (X[27] = Y),
        (X[28] = Q),
        (X[29] = v));
    } else v = X[29];
    (X[32] !== j || X[33] !== v
      ? ((w = (0, t.jsx)(s.R, {
          "aria-label": j,
          className: "scrollbar-hide -mx-5 mt-2 border-border-secondary px-5",
          children: v,
        })),
        (X[32] = j),
        (X[33] = v),
        (X[34] = w))
      : (w = X[34]),
      X[35] !== eo || X[36] !== g || X[37] !== w
        ? ((N = (0, t.jsx)(s.i, { value: eo, onValueChange: g, children: w })),
          (X[35] = eo),
          (X[36] = g),
          (X[37] = w),
          (X[38] = N))
        : (N = X[38]),
      X[39] !== b || X[40] !== N
        ? ((_ = (0, t.jsxs)("header", {
            className: "shrink-0 px-5 pt-4",
            children: [b, N],
          })),
          (X[39] = b),
          (X[40] = N),
          (X[41] = _))
        : (_ = X[41]),
      X[42] === Symbol.for("react.memo_cache_sentinel")
        ? ((C = (0, t.jsx)(r.L3, {
            "aria-hidden": !0,
            className: "size-4 shrink-0 text-text-tertiary",
          })),
          (X[42] = C))
        : (C = X[42]),
      X[43] === Symbol.for("react.memo_cache_sentinel")
        ? ((k = (e) => ei(e.target.value)), (X[43] = k))
        : (k = X[43]),
      X[44] !== Q
        ? ((S = Q("web.settings.search_placeholder")), (X[44] = Q), (X[45] = S))
        : (S = X[45]),
      X[46] !== Q
        ? ((P = Q("web.settings.search_aria")), (X[46] = Q), (X[47] = P))
        : (P = X[47]),
      X[48] !== et || X[49] !== en || X[50] !== S || X[51] !== P
        ? ((I = (0, t.jsx)("input", {
            id: en,
            type: "search",
            value: et,
            onChange: k,
            placeholder: S,
            "aria-label": P,
            autoComplete: "off",
            spellCheck: !1,
            className:
              "min-w-0 flex-1 bg-transparent text-[13px] text-text-primary outline-none placeholder:text-text-tertiary [&::-webkit-search-cancel-button]:hidden",
            "data-testid": "settings-search",
          })),
          (X[48] = et),
          (X[49] = en),
          (X[50] = S),
          (X[51] = P),
          (X[52] = I))
        : (I = X[52]),
      X[53] !== ex || X[54] !== Q
        ? ((A = ex
            ? (0, t.jsx)("button", {
                type: "button",
                onClick: () => ei(""),
                "aria-label": Q("web.settings.clear_search"),
                className:
                  "-mr-1 flex size-6 shrink-0 items-center justify-center rounded-md text-text-tertiary transition-colors hover:bg-bg-tertiary hover:text-text-primary",
                children: (0, t.jsx)(r.x6, { className: "size-3.5" }),
              })
            : null),
          (X[53] = ex),
          (X[54] = Q),
          (X[55] = A))
        : (A = X[55]),
      X[56] !== en || X[57] !== I || X[58] !== A
        ? ((T = (0, t.jsx)("div", {
            className: "shrink-0 px-5 pt-3",
            children: (0, t.jsxs)("label", {
              htmlFor: en,
              className:
                "flex h-9 items-center gap-2 rounded-lg bg-bg-secondary px-3 ring-1 ring-inset ring-border-secondary/60 transition-colors focus-within:ring-text-accent/60",
              children: [C, I, A],
            }),
          })),
          (X[56] = en),
          (X[57] = I),
          (X[58] = A),
          (X[59] = T))
        : (T = X[59]));
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
    let eN = eh
      ? er
        ? (0, t.jsxs)("div", {
            role: "group",
            "aria-label": Q("web.settings.reset_confirm_title", {
              section: ed,
            }),
            className: "flex min-w-0 items-center gap-2",
            children: [
              (0, t.jsx)("p", {
                className:
                  "hidden min-w-0 truncate text-xs text-text-tertiary sm:block",
                children: Q("web.settings.reset_confirm_body"),
              }),
              (0, t.jsx)(s.K, {
                variant: "secondary",
                size: 32,
                onClick: () => es(!1),
                children: Q("common.cancel"),
              }),
              (0, t.jsx)(s.K, {
                variant: "primary",
                size: 32,
                className: "bg-loss text-bg-primary hover:bg-loss/90",
                onClick: () => {
                  ((0, V.t)(eo), es(!1));
                },
                children: Q("web.settings.reset_confirm_action"),
              }),
            ],
          })
        : (0, t.jsxs)("button", {
            type: "button",
            onClick: () => es(!0),
            className:
              "-ml-2 flex items-center gap-1.5 rounded-md px-2 py-1.5 text-xs font-medium text-text-tertiary transition-colors hover:bg-bg-secondary hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-text-accent/40",
            children: [
              (0, t.jsx)(r.B4, { "aria-hidden": !0, className: "size-3.5" }),
              Q("web.settings.reset_section"),
            ],
          })
      : null;
    return (
      X[71] !== eN
        ? ((z = (0, t.jsx)("div", {
            className: "flex min-w-0 items-center",
            children: eN,
          })),
          (X[71] = eN),
          (X[72] = z))
        : (z = X[72]),
      X[73] !== er || X[74] !== ef || X[75] !== Q
        ? ((F =
            ef && !er
              ? (0, t.jsxs)("span", {
                  className:
                    "hidden items-center gap-1.5 text-[11px] text-text-tertiary sm:flex",
                  children: [
                    (0, t.jsx)(r.mD, {
                      "aria-hidden": !0,
                      className: "size-3.5",
                    }),
                    Q("web.settings.device_note"),
                  ],
                })
              : null),
          (X[73] = er),
          (X[74] = ef),
          (X[75] = Q),
          (X[76] = F))
        : (F = X[76]),
      X[77] !== Q
        ? ((L = Q("common.done")), (X[77] = Q), (X[78] = L))
        : (L = X[78]),
      X[79] !== G || X[80] !== L
        ? ((M = (0, t.jsx)(s.K, {
            variant: "primary",
            size: 32,
            onClick: G,
            children: L,
          })),
          (X[79] = G),
          (X[80] = L),
          (X[81] = M))
        : (M = X[81]),
      X[82] !== F || X[83] !== M
        ? ((R = (0, t.jsxs)("div", {
            className: "flex shrink-0 items-center gap-4",
            children: [F, M],
          })),
          (X[82] = F),
          (X[83] = M),
          (X[84] = R))
        : (R = X[84]),
      X[85] !== z || X[86] !== R
        ? (($ = (0, t.jsxs)("footer", {
            className:
              "flex shrink-0 items-center justify-between gap-3 border-t border-border-secondary px-5 py-3",
            children: [z, R],
          })),
          (X[85] = z),
          (X[86] = R),
          (X[87] = $))
        : ($ = X[87]),
      X[88] !== _ || X[89] !== T || X[90] !== W || X[91] !== $
        ? ((B = (0, t.jsxs)("div", {
            className: "flex h-[min(82dvh,720px)] flex-col",
            children: [_, T, W, $],
          })),
          (X[88] = _),
          (X[89] = T),
          (X[90] = W),
          (X[91] = $),
          (X[92] = B))
        : (B = X[92]),
      X[93] !== ev || X[94] !== B
        ? ((E = (0, t.jsx)(ev, {
            className: "max-w-[720px] overflow-hidden p-0",
            "data-testid": "settings-modal",
            children: B,
          })),
          (X[93] = ev),
          (X[94] = B),
          (X[95] = E))
        : (E = X[95]),
      X[96] !== ej || X[97] !== E || X[98] !== u
        ? ((q = (0, t.jsx)(ej, { isOpen: !0, onIsOpenChange: u, children: E })),
          (X[96] = ej),
          (X[97] = E),
          (X[98] = u),
          (X[99] = q))
        : (q = X[99]),
      q
    );
  };
}
