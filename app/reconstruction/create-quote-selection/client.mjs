// Complete selected quote coordinator translation; external picker/reader/providers are explicit local ports.
// No original factories, asset search, private Create/H, submission, wallet or service acquisition execute.
export function createQuoteSelectionCoordinator({
  createBoundStore,
  React,
  compiler,
  jsxRuntime,
  useTranslation,
  useStocks,
  mayhemState,
  feeSharingState,
  toast,
  classes,
  Image,
  StockArt,
  CoinAvatar,
  Chevron,
  Dialog,
  DialogContent,
  PickerBody
}) {
  const v = {
      g: createBoundStore(t => ({
        pair: {
          kind: "sol"
        },
        setPair: e => t({
          pair: e,
          isQuoteMintEnabled: "usdc" === e.kind
        }),
        isQuoteMintEnabled: !1,
        setIsQuoteMintEnabled: e => t({
          pair: {
            kind: e ? "usdc" : "sol"
          },
          isQuoteMintEnabled: e
        })
      }))
    },
    m = React,
    _ = {
      c: compiler
    },
    t = jsxRuntime,
    u = {
      f: useTranslation
    },
    ef = {
      s: useStocks
    },
    R = {
      i: mayhemState
    },
    ea = feeSharingState,
    p = {
      c: toast
    },
    ek = {
      c: classes
    },
    eA = {
      T: (e, t) => e
    },
    es = {
      default: Image
    },
    f = {
      T: {
        solana: "/chains/solana.svg"
      }
    },
    eG = {
      f: {
        imageUri: "/usdc2.png"
      }
    },
    en = {
      f: StockArt
    },
    ej = {
      CoinAvatar
    },
    a = {
      kK: Chevron
    },
    i = {
      v: Dialog,
      s: DialogContent
    },
    eM = PickerBody;
  function eq() {
    let e,
      r,
      i,
      s,
      n,
      o,
      l,
      c,
      d,
      x,
      h,
      b,
      g,
      y,
      w,
      E,
      N,
      j,
      C,
      T,
      I,
      k,
      A,
      S = (0, _.c)(62),
      {
        t: O
      } = (0, u.f)(),
      {
        pair: P,
        setPair: L
      } = (0, v.g)(),
      [M, D] = (0, m.useState)(!1),
      F = (0, ef.s)();
    S[0] !== F.data ? (e = F.data ?? [], S[0] = F.data, S[1] = e) : e = S[1];
    let B = e,
      U = "stock" === P.kind ? P.stock : void 0,
      G = "pump" === P.kind ? P.coin : void 0,
      q = "stock" === P.kind || "pump" === P.kind,
      z = B.length > 0 || q;
    S[2] !== O ? (r = () => {
      let e = R.i.getState();
      e.isMayhemEnabled && (e.setIsMayhemEnabled(!1), p.c.info(O("web.create.pair_stock_mayhem_unsupported")));
      let t = ea.getState();
      t.enabled && (t.setEnabled(!1), p.c.info(O("web.create.pair_stock_fee_sharing_unsupported")));
    }, S[2] = O, S[3] = r) : r = S[3];
    let H = r;
    S[4] !== H || S[5] !== P.kind || S[6] !== L ? (i = e => {
      e !== P.kind && ("stock" === e && H(), L({
        kind: e
      }));
    }, S[4] = H, S[5] = P.kind, S[6] = L, S[7] = i) : i = S[7];
    let V = i;
    S[8] !== O ? (s = O("web.create.pair_asset_label"), S[8] = O, S[9] = s) : s = S[9], S[10] !== s ? (n = (0, t.jsx)("p", {
      className: "text-xs font-semibold text-text-primary",
      children: s
    }), S[10] = s, S[11] = n) : n = S[11], S[12] !== O ? (o = O("web.create.pair_asset_label"), S[12] = O, S[13] = o) : o = S[13];
    let W = z ? "grid-cols-3" : "grid-cols-2";
    S[14] !== W ? (l = (0, ek.c)("grid gap-2", W), S[14] = W, S[15] = l) : l = S[15], S[16] === Symbol.for("react.memo_cache_sentinel") ? (c = (0, eA.T)("SOL", "brand-name"), S[16] = c) : c = S[16];
    let $ = "sol" === P.kind;
    S[17] !== V ? (d = () => V("sol"), S[17] = V, S[18] = d) : d = S[18], S[19] === Symbol.for("react.memo_cache_sentinel") ? (x = (0, t.jsx)(es.default, {
      alt: "",
      className: "size-6 rounded-full",
      height: 24,
      src: f.T.solana,
      width: 24
    }), S[19] = x) : x = S[19], S[20] !== d || S[21] !== $ ? (h = (0, t.jsx)(eH, {
      label: c,
      isSelected: $,
      onSelect: d,
      children: x
    }), S[20] = d, S[21] = $, S[22] = h) : h = S[22], S[23] === Symbol.for("react.memo_cache_sentinel") ? (b = (0, eA.T)("USDC", "brand-name"), S[23] = b) : b = S[23];
    let K = "usdc" === P.kind;
    return S[24] !== V ? (g = () => V("usdc"), S[24] = V, S[25] = g) : g = S[25], S[26] === Symbol.for("react.memo_cache_sentinel") ? (y = (0, t.jsx)(es.default, {
      alt: "",
      className: "size-6 rounded-full object-cover",
      height: 24,
      src: eG.f.imageUri,
      width: 24
    }), S[26] = y) : y = S[26], S[27] !== K || S[28] !== g ? (w = (0, t.jsx)(eH, {
      label: b,
      isSelected: K,
      onSelect: g,
      children: y
    }), S[27] = K, S[28] = g, S[29] = w) : w = S[29], S[30] !== q || S[31] !== V || S[32] !== z || S[33] !== O ? (E = z ? (0, t.jsx)(eH, {
      label: O("web.create.pair_stocks"),
      isSelected: q,
      onSelect: () => {
        q || V("stock");
      },
      children: (0, t.jsx)(ez, {
        className: "size-8"
      })
    }) : null, S[30] = q, S[31] = V, S[32] = z, S[33] = O, S[34] = E) : E = S[34], S[35] !== h || S[36] !== w || S[37] !== E || S[38] !== o || S[39] !== l ? (N = (0, t.jsxs)("div", {
      role: "radiogroup",
      "aria-label": o,
      className: l,
      children: [h, w, E]
    }), S[35] = h, S[36] = w, S[37] = E, S[38] = o, S[39] = l, S[40] = N) : N = S[40], S[41] !== q || S[42] !== M || S[43] !== G || S[44] !== U || S[45] !== O ? (j = q ? (0, t.jsxs)("button", {
      type: "button",
      "aria-haspopup": "dialog",
      "aria-expanded": M,
      onClick: () => D(!0),
      className: "flex h-12 w-full items-center gap-2 rounded-xl border border-border-secondary bg-bg-secondary px-3 text-start text-xs font-semibold text-text-primary transition-colors hover:bg-bg-tertiary",
      children: [G ? (0, t.jsxs)(t.Fragment, {
        children: [(0, t.jsx)("span", {
          "aria-hidden": !0,
          className: "flex shrink-0",
          children: (0, t.jsx)(ej.CoinAvatar, {
            coin: G,
            size: 32,
            shape: "round",
            hideCorner: !0
          })
        }), (0, t.jsx)("span", {
          className: "min-w-0 flex-1 truncate",
          children: O("web.create.pair_with_stock", {
            symbol: G.symbol,
            ticker: G.name
          })
        }), (0, t.jsx)("span", {
          className: "font-normal text-text-tertiary",
          children: O("web.create.pair_change")
        })]
      }) : U ? (0, t.jsxs)(t.Fragment, {
        children: [(0, t.jsx)(en.f, {
          stock: U,
          className: "size-8"
        }), (0, t.jsx)("span", {
          className: "min-w-0 flex-1 truncate",
          children: O("web.create.pair_with_stock", {
            symbol: U.symbol,
            ticker: U.ticker
          })
        }), (0, t.jsx)("span", {
          className: "font-normal text-text-tertiary",
          children: O("web.create.pair_change")
        })]
      }) : (0, t.jsx)("span", {
        className: "min-w-0 flex-1 truncate",
        children: O("web.create.pair_select_stock")
      }), (0, t.jsx)(a.kK, {
        className: "shrink-0 text-text-tertiary",
        size: 16
      })]
    }) : null, S[41] = q, S[42] = M, S[43] = G, S[44] = U, S[45] = O, S[46] = j) : j = S[46], S[47] === Symbol.for("react.memo_cache_sentinel") ? (C = () => D(!1), S[47] = C) : C = S[47], S[48] !== L ? (T = e => {
      L({
        kind: "stock",
        stock: e
      }), D(!1);
    }, I = e => {
      L({
        kind: "pump",
        coin: {
          ...e,
          name: e.name ?? e.mint,
          symbol: e.symbol ?? e.mint
        }
      }), D(!1);
    }, S[48] = L, S[49] = T, S[50] = I) : (T = S[49], I = S[50]), S[51] !== M || S[52] !== B || S[53] !== F.isPending || S[54] !== T || S[55] !== I ? (k = (0, t.jsx)(eL, {
      isOpen: M,
      isLoading: F.isPending,
      stocks: B,
      onClose: C,
      onSelect: T,
      onSelectPumpCoin: I
    }), S[51] = M, S[52] = B, S[53] = F.isPending, S[54] = T, S[55] = I, S[56] = k) : k = S[56], S[57] !== N || S[58] !== j || S[59] !== k || S[60] !== n ? (A = (0, t.jsxs)("div", {
      className: "flex flex-col gap-2",
      children: [n, N, j, k]
    }), S[57] = N, S[58] = j, S[59] = k, S[60] = n, S[61] = A) : A = S[61], A;
  }
  function eH(e) {
    let r,
      a,
      i,
      s = (0, _.c)(10),
      {
        label: n,
        isSelected: o,
        onSelect: l,
        children: c
      } = e,
      d = o ? "border-positive bg-positive/10" : "border-border-secondary bg-bg-secondary hover:bg-bg-tertiary";
    return s[0] !== d ? (r = (0, ek.c)("flex h-12 items-center justify-center gap-2 rounded-xl border text-xs font-semibold text-text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bg-accent", d), s[0] = d, s[1] = r) : r = s[1], s[2] !== n ? (a = (0, t.jsx)("span", {
      children: n
    }), s[2] = n, s[3] = a) : a = s[3], s[4] !== c || s[5] !== o || s[6] !== l || s[7] !== r || s[8] !== a ? (i = (0, t.jsxs)("button", {
      type: "button",
      role: "radio",
      "aria-checked": o,
      onClick: l,
      className: r,
      children: [c, a]
    }), s[4] = c, s[5] = o, s[6] = l, s[7] = r, s[8] = a, s[9] = i) : i = s[9], i;
  }
  function ez(e) {
    let r,
      a,
      i,
      s,
      n,
      o = (0, _.c)(6),
      {
        className: l
      } = e;
    return o[0] === Symbol.for("react.memo_cache_sentinel") ? (r = (0, t.jsx)("rect", {
      fill: "#1B1B1F",
      height: "32",
      rx: "16",
      width: "32"
    }), o[0] = r) : r = o[0], o[1] === Symbol.for("react.memo_cache_sentinel") ? (a = (0, t.jsx)("defs", {
      children: (0, t.jsxs)("linearGradient", {
        gradientUnits: "userSpaceOnUse",
        id: "stocks-pair-gradient",
        x1: "16",
        x2: "16",
        y1: "8",
        y2: "24",
        children: [(0, t.jsx)("stop", {
          stopColor: "#FFFFFF",
          stopOpacity: "0.9"
        }), (0, t.jsx)("stop", {
          offset: "1",
          stopColor: "#9AF2B8"
        })]
      })
    }), i = (0, t.jsx)("path", {
      d: "M12.8 8.8C12.8 8.35817 12.4418 8 12 8C11.5582 8 11.2 8.35817 11.2 8.8V13.6H10.4C9.51634 13.6 8.8 14.3163 8.8 15.2V20C8.8 20.8837 9.51634 21.6 10.4 21.6H11.2V23.2C11.2 23.6418 11.5582 24 12 24C12.4418 24 12.8 23.6418 12.8 23.2V21.6H13.6C14.4837 21.6 15.2 20.8837 15.2 20V15.2C15.2 14.3163 14.4837 13.6 13.6 13.6H12.8V8.8Z",
      fill: "url(#stocks-pair-gradient)"
    }), s = (0, t.jsx)("path", {
      d: "M20.8 8.8C20.8 8.35817 20.4418 8 20 8C19.5582 8 19.2 8.35817 19.2 8.8V10.4H18.4C17.5163 10.4 16.8 11.1163 16.8 12V20C16.8 20.8837 17.5163 21.6 18.4 21.6H19.2V23.2C19.2 23.6418 19.5582 24 20 24C20.4418 24 20.8 23.6418 20.8 23.2V21.6H21.6C22.4837 21.6 23.2 20.8837 23.2 20V12C23.2 11.1163 22.4837 10.4 21.6 10.4H20.8V8.8Z",
      fill: "url(#stocks-pair-gradient)"
    }), o[1] = a, o[2] = i, o[3] = s) : (a = o[1], i = o[2], s = o[3]), o[4] !== l ? (n = (0, t.jsxs)("svg", {
      "aria-hidden": !0,
      className: l,
      fill: "none",
      viewBox: "0 0 32 32",
      xmlns: "http://www.w3.org/2000/svg",
      children: [r, a, i, s]
    }), o[4] = l, o[5] = n) : n = o[5], n;
  }
  function eL(e) {
    let r,
      a,
      s,
      n,
      o = (0, _.c)(15),
      {
        isOpen: l,
        isLoading: c,
        stocks: d,
        onSelect: m,
        onSelectPumpCoin: u,
        onClose: p
      } = e;
    return o[0] !== p ? (r = e => {
      e || p();
    }, o[0] = p, o[1] = r) : r = o[1], o[2] !== c || o[3] !== l || o[4] !== p || o[5] !== m || o[6] !== u || o[7] !== d ? (a = l ? (0, t.jsx)(eM, {
      isLoading: c,
      stocks: d,
      onSelect: m,
      onSelectPumpCoin: u,
      onClose: p
    }) : null, o[2] = c, o[3] = l, o[4] = p, o[5] = m, o[6] = u, o[7] = d, o[8] = a) : a = o[8], o[9] !== a ? (s = (0, t.jsx)(i.s, {
      className: "w-full max-h-[92dvh] overflow-hidden p-0 sm:max-w-[440px]",
      children: a
    }), o[9] = a, o[10] = s) : s = o[10], o[11] !== l || o[12] !== r || o[13] !== s ? (n = (0, t.jsx)(i.v, {
      isOpen: l,
      onIsOpenChange: r,
      children: s
    }), o[11] = l, o[12] = r, o[13] = s, o[14] = n) : n = o[14], n;
  }
  return {
    Control: eq,
    store: v.g
  };
}
