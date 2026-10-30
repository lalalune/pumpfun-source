export function createQuoteAssetPicker({
  React,
  compiler,
  jsxRuntime,
  useTranslation,
  useDebouncedValue,
  useIpfsPrefix,
  useIncludeNsfw,
  useSupportedMints,
  useQuery,
  getContractClient,
  readCoins,
  normalizeCoins,
  reportError,
  formatUsd,
  classes,
  CategorySelector,
  StockArt,
  CoinAvatar,
  CoinName,
  LoadError,
  Skeleton,
  CloseIcon,
  SearchIcon
}) {
  const m = React,
    _ = {
      c: compiler
    },
    t = jsxRuntime,
    u = {
      f: useTranslation
    },
    ex = {
      r: useDebouncedValue
    },
    e_ = {
      useIpfsPrefix
    },
    eg = {
      M: useIncludeNsfw
    },
    ef = {
      u: useSupportedMints
    },
    ep = {
      useQuery
    },
    et = {
      j: getContractClient
    },
    eh = {
      l: readCoins
    },
    ey = {
      f: normalizeCoins
    },
    eb = {
      l: reportError
    },
    G = {
      N: formatUsd
    },
    ek = {
      c: classes
    },
    ed = {
      f: CategorySelector
    },
    en = {
      f: StockArt
    },
    ej = {
      CoinAvatar
    },
    eC = {
      f: CoinName
    },
    eT = {
      f: LoadError
    },
    eI = {
      l: Skeleton
    },
    a = {
      AD: CloseIcon,
      L3: SearchIcon
    };
  const P = {
      z: e => null != e.mayhem_state || e.mayhem?.state != null
    },
    z = (() => {
      let n = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",
        r = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        i = "So11111111111111111111111111111111111111112",
        o = [n, r],
        u = [i, "11111111111111111111111111111111"];
      const Q = e => !e || u.includes(e),
        Y = e => null != e && o.includes(e);
      return {
        Q,
        Y
      };
    })(),
    eA = {
      T: (e, t) => e
    },
    eu = {
      y: function (t) {
        return t;
      }
    },
    eo = {
      "s": {
        terminal: 24,
        comfortable: 36
      },
      "x": {
        terminal: "flex h-4 min-w-0 items-center gap-1",
        comfortable: "flex h-5 min-w-0 items-center gap-1"
      },
      "n": {
        terminal: "min-w-0 text-[13px] leading-4",
        comfortable: "min-w-0 text-sm leading-5"
      },
      "B": {
        terminal: "text-[11px] leading-4 text-text-quaternary",
        comfortable: "text-xs leading-4 text-text-quaternary"
      },
      "e": {
        terminal: "text-[13px] font-medium leading-4 tabular-nums text-text-primary",
        comfortable: "text-sm font-medium leading-5 tabular-nums text-text-primary"
      },
      "N": "flex h-4 items-center justify-end",
      "C": {
        terminal: "text-[11px] leading-4 tabular-nums",
        comfortable: "text-xs leading-4 tabular-nums"
      }
    };
  let el = {
      rwa: "stocks",
      crypto: "crypto",
      meme: "memes"
    },
    ec = e => void 0 === e.assetType ? void 0 : el[e.assetType],
    eU = (e, t) => {
      let r = t.trim().toLowerCase();
      return r ? e.filter(e => e.symbol.toLowerCase().includes(r) || e.ticker.toLowerCase().includes(r)) : e;
    },
    ev = new Set(),
    ew = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/,
    eS = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/,
    eO = "comfortable",
    eP = eo.s[eO],
    eR = e => {
      "mouse" === e.pointerType && e.stopPropagation();
    };
  function eE(e, t, r) {
    if (!r.ok) throw Error(`Pump coin search failed: ${r.status}`);
  }
  function eN(e) {
    return e.mint;
  }
  function em(e) {
    let r,
      a,
      i,
      s,
      n,
      o,
      l,
      c,
      d,
      m,
      p = (0, _.c)(25),
      {
        value: x,
        onValueChange: h
      } = e,
      {
        t: f
      } = (0, u.f)();
    p[0] !== f ? (r = f("web.create.pair_category_all"), p[0] = f, p[1] = r) : r = p[1], p[2] !== r ? (a = {
      value: "all",
      label: r
    }, p[2] = r, p[3] = a) : a = p[3], p[4] !== f ? (i = f("web.create.pair_category_stocks"), p[4] = f, p[5] = i) : i = p[5], p[6] !== i ? (s = {
      value: "stocks",
      label: i
    }, p[6] = i, p[7] = s) : s = p[7], p[8] !== f ? (n = f("web.create.pair_category_crypto"), p[8] = f, p[9] = n) : n = p[9], p[10] !== n ? (o = {
      value: "crypto",
      label: n
    }, p[10] = n, p[11] = o) : o = p[11], p[12] !== f ? (l = f("web.create.pair_category_memes"), p[12] = f, p[13] = l) : l = p[13], p[14] !== l ? (c = {
      value: "memes",
      label: l
    }, p[14] = l, p[15] = c) : c = p[15], p[16] !== a || p[17] !== s || p[18] !== o || p[19] !== c ? (d = [a, s, o, c], p[16] = a, p[17] = s, p[18] = o, p[19] = c, p[20] = d) : d = p[20];
    let b = d;
    return p[21] !== b || p[22] !== h || p[23] !== x ? (m = (0, t.jsx)("div", {
      className: "px-4 pt-3",
      children: (0, t.jsx)(ed.f, {
        items: b,
        value: x,
        onValueChange: h
      })
    }), p[21] = b, p[22] = h, p[23] = x, p[24] = m) : m = p[24], m;
  }
  function eM(e) {
    let r,
      i,
      s,
      n,
      o,
      l,
      c,
      d,
      p,
      x,
      h,
      f,
      b,
      g,
      y,
      v,
      w,
      E,
      N,
      j = (0, _.c)(54),
      {
        isLoading: C,
        stocks: T,
        onSelect: I,
        onSelectPumpCoin: k,
        onClose: A
      } = e,
      {
        t: S
      } = (0, u.f)(),
      [O, R] = (0, m.useState)(""),
      [L, M] = (0, m.useState)("all");
    j[0] !== T ? (r = T.some(e => void 0 !== ec(e)), j[0] = T, j[1] = r) : r = j[1];
    let D = r,
      F = eU("all" === L ? T : T.filter(e => ec(e) === L), O),
      B = O.trim(),
      U = function (e) {
        let t,
          r,
          a,
          i,
          s,
          n,
          o,
          l,
          c,
          d,
          u,
          p = (0, _.c)(34),
          {
            term: x
          } = e;
        p[0] !== x ? (t = x.trim(), p[0] = x, p[1] = t) : t = p[1];
        let [h] = (0, ex.r)(t, 250),
          {
            ipfsPrefix: f
          } = (0, e_.useIpfsPrefix)(),
          b = (0, eg.M)(),
          g = (0, ef.u)();
        p[2] !== g.data ? (r = g.data ? new Set(g.data.map(eN)) : ev, p[2] = g.data, p[3] = r) : r = p[3];
        let y = r;
        p[4] !== h || p[5] !== b || p[6] !== f ? (a = ["create", "pump-quote-coin-search", h, 1, b, f], p[4] = h, p[5] = b, p[6] = f, p[7] = a) : a = p[7];
        let v = "" !== h;
        p[8] !== y ? (i = e => e.filter((t, r) => !!(t.name && t.symbol) && "pump" === t.program && !t.raydium_pool && (t.depth ?? 0) <= 1 && !(0, P.z)(t) && !0 !== t.is_banned && void 0 !== t.base_decimals && !y.has(t.mint) && ((t.depth ?? 0) > 0 || (0, z.Q)(t.quote_mint) || (0, z.Y)(t.quote_mint) || y.has(t.quote_mint ?? "")) && e.findIndex(e => e.mint === t.mint) === r), p[8] = y, p[9] = i) : i = p[9], p[10] !== h || p[11] !== b || p[12] !== f ? (s = async e => {
          let {
              signal: t
            } = e,
            r = await (0, et.j)()("GET /coins/search-unrestricted", {
              query: {
                searchTerm: h,
                limit: 20,
                offset: 0,
                includeNsfw: b,
                sort: "market_cap",
                order: "DESC",
                program: "pump",
                maxDepth: 1
              },
              credentials: "include",
              signal: t,
              hooks: {
                afterResponse: [eE]
              }
            });
          return (0, ey.f)((0, eh.l)(r), f);
        }, p[10] = h, p[11] = b, p[12] = f, p[13] = s) : s = p[13], p[14] !== a || p[15] !== v || p[16] !== i || p[17] !== s ? (n = {
          queryKey: a,
          enabled: v,
          staleTime: 3e4,
          placeholderData: eu.y,
          select: i,
          queryFn: s
        }, p[14] = a, p[15] = v, p[16] = i, p[17] = s, p[18] = n) : n = p[18];
        let w = (0, ep.useQuery)(n),
          E = w.isError && !w.isFetching ? w.error : null;
        p[19] !== h || p[20] !== E ? (o = () => {
          E && (0, eb.l)({
            error: E,
            feature: "coin-creation",
            operation: "pair-search",
            context: {
              mint: ew.test(h) ? h : void 0
            }
          });
        }, l = [E, h], p[19] = h, p[20] = E, p[21] = o, p[22] = l) : (o = p[21], l = p[22]), (0, m.useEffect)(o, l);
        let N = w.isError ? void 0 : w.data;
        p[23] !== h || p[24] !== w.isFetching || p[25] !== x ? (c = w.isFetching || x.trim() !== h, p[23] = h, p[24] = w.isFetching, p[25] = x, p[26] = c) : c = p[26];
        let j = null !== E;
        return p[27] !== w ? (d = () => {
          w.refetch();
        }, p[27] = w, p[28] = d) : d = p[28], p[29] !== N || p[30] !== c || p[31] !== j || p[32] !== d ? (u = {
          data: N,
          isSearching: c,
          isError: j,
          refetch: d
        }, p[29] = N, p[30] = c, p[31] = j, p[32] = d, p[33] = u) : u = p[33], u;
      }({
        term: B
      }),
      G = "" !== B && ("all" === L || "memes" === L);
    j[2] !== G || j[3] !== U ? (i = G && !U.isError ? U.data ?? [] : [], j[2] = G, j[3] = U, j[4] = i) : i = j[4];
    let q = i,
      H = 0 === F.length && 0 === q.length,
      V = G && U.isSearching,
      W = G && U.isError,
      $ = H && (C || V);
    j[5] !== S ? (s = S("web.create.pair_stock_dialog_title"), j[5] = S, j[6] = s) : s = j[6], j[7] !== s ? (n = (0, t.jsx)("p", {
      className: "min-w-0 flex-1 text-base font-bold text-text-primary",
      children: s
    }), j[7] = s, j[8] = n) : n = j[8], j[9] !== S ? (o = S("common.close"), j[9] = S, j[10] = o) : o = j[10], j[11] === Symbol.for("react.memo_cache_sentinel") ? (l = (0, t.jsx)(a.AD, {
      className: "size-4"
    }), j[11] = l) : l = j[11], j[12] !== A || j[13] !== o ? (c = (0, t.jsx)("button", {
      type: "button",
      "aria-label": o,
      onClick: A,
      className: "flex size-7 shrink-0 items-center justify-center rounded-full text-text-tertiary transition-colors hover:bg-bg-quaternary hover:text-text-primary focus-visible:outline focus-visible:outline-2 focus-visible:outline-white/30",
      children: l
    }), j[12] = A, j[13] = o, j[14] = c) : c = j[14], j[15] !== n || j[16] !== c ? (d = (0, t.jsxs)("div", {
      className: "flex items-start gap-3 border-b border-solid border-border-secondary px-4 pb-3 pt-4",
      children: [n, c]
    }), j[15] = n, j[16] = c, j[17] = d) : d = j[17], j[18] === Symbol.for("react.memo_cache_sentinel") ? (p = (0, t.jsx)(a.L3, {
      "aria-hidden": !0,
      className: "pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-text-tertiary"
    }), j[18] = p) : p = j[18], j[19] === Symbol.for("react.memo_cache_sentinel") ? (x = e => R(e.target.value), j[19] = x) : x = j[19], j[20] !== S ? (h = S("web.create.pair_stock_search_placeholder"), j[20] = S, j[21] = h) : h = j[21], j[22] !== S ? (f = S("web.create.pair_stock_search_placeholder"), j[22] = S, j[23] = f) : f = j[23], j[24] !== O || j[25] !== h || j[26] !== f ? (b = (0, t.jsx)("div", {
      className: "px-4 pt-3",
      children: (0, t.jsxs)("div", {
        className: "relative",
        children: [p, (0, t.jsx)("input", {
          autoFocus: !0,
          type: "text",
          value: O,
          onChange: x,
          placeholder: h,
          "aria-label": f,
          className: "w-full rounded-lg border border-solid border-border-secondary bg-bg-primary py-2 pl-9 pr-3 text-sm text-text-primary outline-none transition-colors placeholder:text-text-tertiary hover:border-border-tertiary focus-visible:border-white/30"
        })]
      })
    }), j[24] = O, j[25] = h, j[26] = f, j[27] = b) : b = j[27], j[28] !== L || j[29] !== D ? (g = D ? (0, t.jsx)(em, {
      value: L,
      onValueChange: M
    }) : null, j[28] = L, j[29] = D, j[30] = g) : g = j[30], j[31] !== S ? (y = S("web.create.pair_stock_dialog_title"), j[31] = S, j[32] = y) : y = j[32];
    let K = $ ? (0, t.jsx)(eF, {}) : H && !W ? (0, t.jsx)("li", {
      className: "px-2.5 py-8 text-center text-sm text-text-tertiary",
      children: S(G && eS.test(B) ? "web.create.pair_pump_not_eligible" : "common.no_results")
    }) : F.map(e => (0, t.jsx)(eD, {
      coin: {
        mint: e.mint,
        name: e.symbol,
        symbol: e.ticker
      },
      art: (0, t.jsx)(en.f, {
        stock: e,
        className: "size-full rounded-none"
      }),
      name: (0, eA.T)(e.symbol, "coin-symbol"),
      meta: (0, eA.T)(e.ticker, "coin-symbol"),
      marketCapUsd: e.marketCapUsd,
      liquidityUsd: e.liquidityUsd,
      onClick: () => I(e)
    }, e.mint));
    if (j[33] !== k || j[34] !== q) {
      let e;
      j[36] !== k ? (e = e => (0, t.jsx)(eD, {
        coin: e,
        name: (0, eA.T)(e.name ?? e.mint, "coin-name"),
        meta: (0, eA.T)(e.symbol ?? e.mint, "coin-symbol"),
        marketCapUsd: e.usd_market_cap || void 0,
        liquidityUsd: e.canonical_pool_liquidity_usd || void 0,
        onClick: () => k(e)
      }, e.mint), j[36] = k, j[37] = e) : e = j[37], v = q.map(e), j[33] = k, j[34] = q, j[35] = v;
    } else v = j[35];
    return j[38] !== U || j[39] !== W || j[40] !== $ || j[41] !== S ? (w = W && !$ ? (0, t.jsx)("li", {
      children: (0, t.jsx)(eT.f, {
        density: eO,
        onRetry: U.refetch,
        children: S("web.create.pair_search_unavailable")
      })
    }) : null, j[38] = U, j[39] = W, j[40] = $, j[41] = S, j[42] = w) : w = j[42], j[43] !== y || j[44] !== K || j[45] !== v || j[46] !== w ? (E = (0, t.jsxs)("ul", {
      "aria-label": y,
      className: "custom-scrollbar flex max-h-[60vh] min-h-[160px] flex-col gap-1 overflow-y-auto p-2",
      children: [K, v, w]
    }), j[43] = y, j[44] = K, j[45] = v, j[46] = w, j[47] = E) : E = j[47], j[48] !== d || j[49] !== b || j[50] !== g || j[51] !== E || j[52] !== eR ? (N = (0, t.jsxs)("div", {
      className: "flex flex-col",
      onPointerDown: eR,
      children: [d, b, g, E]
    }), j[48] = d, j[49] = b, j[50] = g, j[51] = E, j[52] = eR, j[53] = N) : N = j[53], N;
  }
  function eD(e) {
    let r,
      a,
      i,
      s,
      n,
      o,
      l,
      c,
      d,
      m,
      p,
      x,
      h,
      f = (0, _.c)(31),
      {
        coin: b,
        art: g,
        name: y,
        meta: v,
        marketCapUsd: w,
        liquidityUsd: E,
        onClick: N
      } = e,
      {
        t: j
      } = (0, u.f)();
    return f[0] !== g || f[1] !== b ? (r = (0, t.jsx)(ej.CoinAvatar, {
      coin: b,
      size: eP,
      children: g
    }), f[0] = g, f[1] = b, f[2] = r) : r = f[2], f[3] !== b || f[4] !== y ? (a = (0, t.jsx)("span", {
      className: eo.x[eO],
      children: (0, t.jsx)(eC.f, {
        coin: b,
        nameClassName: eo.n[eO],
        children: y
      })
    }), f[3] = b, f[4] = y, f[5] = a) : a = f[5], f[6] === Symbol.for("react.memo_cache_sentinel") ? (i = (0, ek.c)("truncate", eo.B[eO]), f[6] = i) : i = f[6], f[7] !== v ? (s = (0, t.jsx)("span", {
      className: i,
      children: v
    }), f[7] = v, f[8] = s) : s = f[8], f[9] !== a || f[10] !== s ? (n = (0, t.jsxs)("span", {
      className: "flex min-w-0 flex-1 flex-col",
      children: [a, s]
    }), f[9] = a, f[10] = s, f[11] = n) : n = f[11], f[12] === Symbol.for("react.memo_cache_sentinel") ? (o = (0, ek.c)("flex h-5 items-center", eo.e[eO]), f[12] = o) : o = f[12], f[13] !== w ? (l = void 0 === w ? null : (0, G.N)(w), f[13] = w, f[14] = l) : l = f[14], f[15] !== l ? (c = (0, t.jsx)("span", {
      className: o,
      children: l
    }), f[15] = l, f[16] = c) : c = f[16], f[17] === Symbol.for("react.memo_cache_sentinel") ? (d = (0, ek.c)(eo.N, eo.C[eO], "text-text-quaternary"), f[17] = d) : d = f[17], f[18] !== E || f[19] !== j ? (m = void 0 === E ? null : `${j("mayhem_mode.summary_pills.liquidity")} • ${(0, G.N)(E)}`, f[18] = E, f[19] = j, f[20] = m) : m = f[20], f[21] !== m ? (p = (0, t.jsx)("span", {
      className: d,
      children: m
    }), f[21] = m, f[22] = p) : p = f[22], f[23] !== p || f[24] !== c ? (x = (0, t.jsxs)("span", {
      className: "flex shrink-0 flex-col items-end",
      children: [c, p]
    }), f[23] = p, f[24] = c, f[25] = x) : x = f[25], f[26] !== N || f[27] !== r || f[28] !== x || f[29] !== n ? (h = (0, t.jsx)("li", {
      children: (0, t.jsxs)("button", {
        type: "button",
        className: "flex w-full items-center gap-3 rounded-lg px-2.5 py-2 text-left transition-colors hover:bg-bg-tertiary focus-visible:bg-bg-tertiary focus-visible:outline-none",
        onClick: N,
        children: [r, n, x]
      })
    }), f[26] = N, f[27] = r, f[28] = x, f[29] = n, f[30] = h) : h = f[30], h;
  }
  function eF() {
    let e,
      r = (0, _.c)(1);
    return r[0] === Symbol.for("react.memo_cache_sentinel") ? (e = (0, t.jsx)(t.Fragment, {
      children: Array.from({
        length: 4
      }, eB)
    }), r[0] = e) : e = r[0], e;
  }
  function eB(e, r) {
    return (0, t.jsxs)("li", {
      "aria-hidden": !0,
      className: "flex items-center gap-3 px-2.5 py-2",
      children: [(0, t.jsx)(eI.l, {
        variant: "art",
        size: eP
      }), (0, t.jsxs)("span", {
        className: "flex flex-1 flex-col gap-1 py-0.5",
        children: [(0, t.jsx)(eI.l, {
          height: 14,
          width: 112
        }), (0, t.jsx)(eI.l, {
          height: 12,
          width: 48
        })]
      }), (0, t.jsxs)("span", {
        className: "flex shrink-0 flex-col items-end gap-1 py-0.5",
        children: [(0, t.jsx)(eI.l, {
          height: 14,
          width: 48
        }), (0, t.jsx)(eI.l, {
          height: 12,
          width: 64
        })]
      })]
    }, r);
  }
  return {
    Picker: eM
  };
}
