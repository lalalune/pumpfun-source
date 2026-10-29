// Complete selected advanced-fee control translation; explicit local ports, never whole captured factories.
// Fee projection, funding, submission and all service/provider acquisition remain outside this module.
export function createAdvancedCreatorFeeControl({
  createBoundStore,
  useQuoteState,
  useTranslation,
  compiler,
  jsxRuntime,
  Collapsible,
  Input,
  Chevron
}) {
  const y = {
      $: createBoundStore
    },
    v = {
      g: useQuoteState,
      Q: t => "stock" === t.kind || "pump" === t.kind
    },
    _ = {
      c: compiler
    },
    t = jsxRuntime,
    u = {
      f: useTranslation
    },
    w = Collapsible,
    E = {
      f: Input
    },
    a = {
      J0: Chevron
    },
    N = {
      f: {
        CREATE_COIN_PAGE: {
          SECTION: {
            DETAIL: {
              INPUT: {
                OPTIONAL: "(Optional)"
              }
            }
          }
        }
      }
    };
  let j = /^\d*\.?\d{0,2}$/,
    C = (0, y.$)(e => ({
      creatorFeePercent: "",
      setCreatorFeePercent: t => e({
        creatorFeePercent: t
      })
    })),
    T = e => !e || j.test(e) && Number(e) >= .01 && 3 >= Number(e),
    k = "create-coin-creator-fee-percent",
    A = `${k}-error`;
  function S() {
    let e,
      r,
      i,
      s,
      n,
      o,
      l,
      c,
      d,
      m,
      p,
      x = (0, _.c)(39),
      {
        t: h
      } = (0, u.f)(),
      f = (0, v.g)(O),
      {
        creatorFeePercent: b,
        setCreatorFeePercent: g
      } = C();
    if (!f) return null;
    x[0] !== b ? (e = T(b), x[0] = b, x[1] = e) : e = x[1];
    let y = !e;
    if (x[2] !== b || x[3] !== y || x[4] !== g || x[5] !== h) {
      let e,
        m,
        u,
        p,
        f,
        _,
        v = {
          min_percent: .01,
          max_percent: 3
        };
      i = w.Y, c = !0, x[14] !== h ? (e = h("web.create.advanced"), x[14] = h, x[15] = e) : e = x[15], x[16] !== e ? (m = (0, t.jsx)("p", {
        className: "text-xs",
        children: e
      }), x[16] = e, x[17] = m) : m = x[17], x[18] === Symbol.for("react.memo_cache_sentinel") ? (u = (0, t.jsx)(a.J0, {
        size: 16,
        strokeWidth: 1
      }), x[18] = u) : u = x[18], x[19] !== m ? (d = (0, t.jsx)(w.v, {
        asChild: !0,
        children: (0, t.jsxs)("button", {
          type: "button",
          className: "flex items-center gap-2 text-text-primary [&>svg]:transition-transform [&>svg]:duration-200 data-[state=open]:[&>svg]:rotate-180",
          children: [m, u]
        })
      }), x[19] = m, x[20] = d) : d = x[20], r = w.C, s = "mt-4 flex flex-col gap-2 sm:max-w-[calc(50%-6px)]", x[21] !== h ? (p = h("web.create.creator_fee_label"), x[21] = h, x[22] = p) : p = x[22], x[23] === Symbol.for("react.memo_cache_sentinel") ? (f = (0, t.jsx)("span", {
        className: "text-[#9da3ae]",
        children: N.f.CREATE_COIN_PAGE.SECTION.DETAIL.INPUT.OPTIONAL
      }), x[23] = f) : f = x[23], x[24] !== p ? (n = (0, t.jsxs)("label", {
        htmlFor: k,
        className: "text-xs font-semibold text-text-primary",
        children: [p, " ", f]
      }), x[24] = p, x[25] = n) : n = x[25], x[26] !== g ? (_ = e => g(e.target.value), x[26] = g, x[27] = _) : _ = x[27], o = (0, t.jsx)(E.f, {
        id: k,
        className: "rounded-lg border-border-secondary bg-transparent text-white dark:border-border-secondary dark:bg-transparent",
        type: "text",
        inputMode: "decimal",
        maxLength: 4,
        autoComplete: "off",
        placeholder: h("web.create.creator_fee_placeholder", v),
        value: b,
        onChange: _,
        "aria-invalid": y || void 0,
        "aria-describedby": y ? A : void 0
      }), l = y ? (0, t.jsx)("p", {
        id: A,
        className: "text-xs text-red-500",
        children: h("web.create.creator_fee_invalid", v)
      }) : null, x[2] = b, x[3] = y, x[4] = g, x[5] = h, x[6] = r, x[7] = i, x[8] = s, x[9] = n, x[10] = o, x[11] = l, x[12] = c, x[13] = d;
    } else r = x[6], i = x[7], s = x[8], n = x[9], o = x[10], l = x[11], c = x[12], d = x[13];
    return x[28] !== r || x[29] !== s || x[30] !== n || x[31] !== o || x[32] !== l ? (m = (0, t.jsxs)(r, {
      className: s,
      children: [n, o, l]
    }), x[28] = r, x[29] = s, x[30] = n, x[31] = o, x[32] = l, x[33] = m) : m = x[33], x[34] !== i || x[35] !== c || x[36] !== d || x[37] !== m ? (p = (0, t.jsxs)(i, {
      defaultOpen: c,
      children: [d, m]
    }), x[34] = i, x[35] = c, x[36] = d, x[37] = m, x[38] = p) : p = x[38], p;
  }
  function O(e) {
    return (0, v.Q)(e.pair);
  }
  return {
    Control: S,
    store: C
  };
}
