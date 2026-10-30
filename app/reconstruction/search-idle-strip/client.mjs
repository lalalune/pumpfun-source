// Complete ordinary SearchDialog idle Discover strip and used tiles/scroll/skeleton frames.
import { profileRoute } from "../search-navigation/navigation.mjs";
export function createSearchIdleStrip(ports) {
  for (const name of [
    "useTranslation",
    "useFlag",
    "useProfile",
    "pnlTone",
    "formatPnlUsd",
    "formatPnlPercent",
    "formatMarketCap",
    "classNames",
    "useLiveMarketCap",
    "useCoinImpression",
    "useCoinClickHandlers",
    "useImpressionContext",
    "useCandlesticks",
    "cleanSymbol",
    "usePrefetch",
    "memoCache",
  ])
    if (typeof ports?.[name] !== "function")
      throw new TypeError("Explicit idle strip capability required: " + name);
  for (const name of [
    "PreviousIcon",
    "NextIcon",
    "ArrowButton",
    "Heading",
    "Empty",
    "SkeletonPart",
    "Link",
    "ProfileDisplay",
    "SegmentedControl",
    "CoinAvatar",
    "CoinName",
    "Sparkline",
  ])
    if (!ports.renderers?.[name])
      throw new TypeError("Explicit idle strip renderer required: " + name);
  if (
    !ports.React ||
    !ports.jsxRuntime ||
    !ports.browserWindow ||
    typeof ports.MutationObserver !== "function" ||
    !Object.hasOwn(ports, "ResizeObserver") ||
    !Object.hasOwn(ports, "avatarSize")
  )
    throw new TypeError(
      "Explicit React/JSX/browser/observer/size capabilities required",
    );
  const a = ports.React,
    t = ports.jsxRuntime,
    r = { c: ports.memoCache },
    o = { $: profileRoute },
    k = { s: { comfortable: ports.avatarSize } },
    window = ports.browserWindow,
    ResizeObserver = ports.ResizeObserver,
    MutationObserver = ports.MutationObserver;
  const n = { Ae: { SEARCH: 9 }, k9: { ACTIVE_SEARCH_TRENDING_COIN_LIST: 24 } },
    l = { D: { WEB_AVATAR_DECORATIONS: "webAvatarDecorations" } };
  const p = { f: ports.useTranslation };
  const i = { k: ports.useFlag };
  const m = { T: ports.useProfile };
  const P = {
    k: ports.pnlTone,
    u: ports.formatPnlUsd,
    c: ports.formatPnlPercent,
    l: ports.formatMarketCap,
  };
  const H = { c: ports.classNames };
  const O = { h: ports.useLiveMarketCap };
  const L = { f: ports.useCoinImpression };
  const M = { f: ports.useCoinClickHandlers };
  const B = { y: ports.useImpressionContext };
  const eN = { f: ports.useCandlesticks };
  const S = { W: ports.cleanSymbol };
  const R = { W: ports.usePrefetch };
  const s = { S: ports.renderers.PreviousIcon, kK: ports.renderers.NextIcon };
  const em = { _: ports.renderers.ArrowButton };
  const q = { _: ports.renderers.Heading };
  const e_ = { L: ports.renderers.Empty };
  const T = { l: ports.renderers.SkeletonPart };
  const f = { default: ports.renderers.Link };
  const A = { S: ports.renderers.ProfileDisplay };
  const ey = { X: ports.renderers.SegmentedControl };
  const N = { CoinAvatar: ports.renderers.CoinAvatar };
  const C = { f: ports.renderers.CoinName };
  const g = { f: ports.renderers.Sparkline };
  function eh() {
    return 3;
  }
  function ef() {}
  function ex(e) {
    let a,
      n,
      l,
      i,
      c,
      o,
      d,
      u = (0, r.c)(19),
      { density: m, atStart: h, atEnd: f, pagePrevious: x, pageNext: g } = e,
      { t: b } = (0, p.f)();
    return (
      u[0] !== b
        ? ((a = b("web.pagination.previous_page")), (u[0] = b), (u[1] = a))
        : (a = u[1]),
      u[2] === Symbol.for("react.memo_cache_sentinel")
        ? ((n = (0, t.jsx)(s.S, { "aria-hidden": !0 })), (u[2] = n))
        : (n = u[2]),
      u[3] !== h || u[4] !== m || u[5] !== x || u[6] !== a
        ? ((l = (0, t.jsx)(em._, {
            density: m,
            size: 24,
            variant: "ghost",
            "aria-label": a,
            disabled: h,
            onClick: x,
            "data-search-strip-arrow": "previous",
            children: n,
          })),
          (u[3] = h),
          (u[4] = m),
          (u[5] = x),
          (u[6] = a),
          (u[7] = l))
        : (l = u[7]),
      u[8] !== b
        ? ((i = b("web.pagination.next_page")), (u[8] = b), (u[9] = i))
        : (i = u[9]),
      u[10] === Symbol.for("react.memo_cache_sentinel")
        ? ((c = (0, t.jsx)(s.kK, { "aria-hidden": !0 })), (u[10] = c))
        : (c = u[10]),
      u[11] !== f || u[12] !== m || u[13] !== g || u[14] !== i
        ? ((o = (0, t.jsx)(em._, {
            density: m,
            size: 24,
            variant: "ghost",
            "aria-label": i,
            disabled: f,
            onClick: g,
            "data-search-strip-arrow": "next",
            children: c,
          })),
          (u[11] = f),
          (u[12] = m),
          (u[13] = g),
          (u[14] = i),
          (u[15] = o))
        : (o = u[15]),
      u[16] !== l || u[17] !== o
        ? ((d = (0, t.jsxs)("span", {
            className: "flex items-center gap-1",
            children: [l, o],
          })),
          (u[16] = l),
          (u[17] = o),
          (u[18] = d))
        : (d = u[18]),
      d
    );
  }
  let ep = "search.idle-strip";
  let eg = "hot-coins";
  let eb = () => {
    try {
      let e = window.sessionStorage.getItem(ep);
      return "hot-coins" === e || "top-traders" === e ? e : eg;
    } catch {
      return eg;
    }
  };
  let ta =
    "relative flex flex-col gap-2 rounded-md bg-bg-tertiary p-3 transition-colors hover:bg-bg-quaternary";
  let ts = "bg-bg-quaternary";
  let tm = (e) => {
    let a,
      s,
      n,
      c,
      d,
      u,
      h,
      x,
      p,
      g,
      b,
      w,
      _,
      v = (0, r.c)(53),
      { entry: k, onClick: y } = e,
      j = (0, i.k)(l.D.WEB_AVATAR_DECORATIONS);
    v[0] !== j || v[1] !== k.walletAddress
      ? ((a = { address: k.walletAddress, enabled: j }),
        (v[0] = j),
        (v[1] = k.walletAddress),
        (v[2] = a))
      : (a = v[2]);
    let { data: N } = (0, m.T)(a);
    v[3] !== k.username || v[4] !== k.walletAddress
      ? ((s =
          k.username ||
          `${k.walletAddress.slice(0, 4)}...${k.walletAddress.slice(-4)}`),
        (v[3] = k.username),
        (v[4] = k.walletAddress),
        (v[5] = s))
      : (s = v[5]);
    let C = s;
    if (
      v[6] !== C ||
      v[7] !== k.pnlUsd ||
      v[8] !== k.profileImage ||
      v[9] !== k.username ||
      v[10] !== k.walletAddress ||
      v[11] !== k.xUsername ||
      v[12] !== y ||
      v[13] !== N?.resolved_avatar_decoration
    ) {
      let e,
        r,
        a,
        s = (0, P.k)(k.pnlUsd, 0);
      ((u = !0),
        v[21] === Symbol.for("react.memo_cache_sentinel")
          ? ((h = (0, H.c)(ta, "min-w-40")), (v[21] = h))
          : (h = v[21]),
        v[22] !== k.walletAddress
          ? ((e = (0, o.$)(k.walletAddress)),
            (v[22] = k.walletAddress),
            (v[23] = e))
          : (e = v[23]),
        v[24] === Symbol.for("react.memo_cache_sentinel")
          ? ((r = (0, H.c)(W, "rounded-md")), (v[24] = r))
          : (r = v[24]),
        v[25] !== C || v[26] !== y || v[27] !== e
          ? ((x = (0, t.jsx)(f.default, {
              href: e,
              onClick: y,
              "aria-label": C,
              className: r,
            })),
            (v[25] = C),
            (v[26] = y),
            (v[27] = e),
            (v[28] = x))
          : (x = v[28]));
      let l = N?.resolved_avatar_decoration;
      (v[29] !== C ||
      v[30] !== k.profileImage ||
      v[31] !== k.username ||
      v[32] !== k.walletAddress ||
      v[33] !== k.xUsername ||
      v[34] !== l
        ? ((p = (0, t.jsx)(A.S, {
            address: k.walletAddress,
            username: k.username,
            profileImage: k.profileImage,
            avatarDecoration: l,
            nameOverride: C,
            size: $,
            density: K,
            link: !1,
            hoverCard: !1,
            xUsername: k.xUsername,
            className: "min-w-0",
          })),
          (v[29] = C),
          (v[30] = k.profileImage),
          (v[31] = k.username),
          (v[32] = k.walletAddress),
          (v[33] = k.xUsername),
          (v[34] = l),
          (v[35] = p))
        : (p = v[35]),
        (c = "flex flex-col gap-0.5"));
      let i = (0, H.c)(
        "whitespace-nowrap text-sm font-medium leading-5 tabular-nums",
        s,
      );
      (v[36] !== k.pnlUsd
        ? ((a = (0, P.u)(k.pnlUsd)), (v[36] = k.pnlUsd), (v[37] = a))
        : (a = v[37]),
        (d = (0, t.jsx)("span", { className: i, children: a })),
        (n = (0, H.c)("text-xs leading-4 tabular-nums", s)),
        (v[6] = C),
        (v[7] = k.pnlUsd),
        (v[8] = k.profileImage),
        (v[9] = k.username),
        (v[10] = k.walletAddress),
        (v[11] = k.xUsername),
        (v[12] = y),
        (v[13] = N?.resolved_avatar_decoration),
        (v[14] = n),
        (v[15] = c),
        (v[16] = d),
        (v[17] = u),
        (v[18] = h),
        (v[19] = x),
        (v[20] = p));
    } else
      ((n = v[14]),
        (c = v[15]),
        (d = v[16]),
        (u = v[17]),
        (h = v[18]),
        (x = v[19]),
        (p = v[20]));
    return (
      v[38] !== k.pnlPercent
        ? ((g = (0, P.c)(k.pnlPercent)), (v[38] = k.pnlPercent), (v[39] = g))
        : (g = v[39]),
      v[40] !== n || v[41] !== g
        ? ((b = (0, t.jsx)("span", { className: n, children: g })),
          (v[40] = n),
          (v[41] = g),
          (v[42] = b))
        : (b = v[42]),
      v[43] !== b || v[44] !== c || v[45] !== d
        ? ((w = (0, t.jsxs)("div", { className: c, children: [d, b] })),
          (v[43] = b),
          (v[44] = c),
          (v[45] = d),
          (v[46] = w))
        : (w = v[46]),
      v[47] !== w || v[48] !== u || v[49] !== h || v[50] !== x || v[51] !== p
        ? ((_ = (0, t.jsxs)("div", {
            "data-search-tile": u,
            className: h,
            children: [x, p, w],
          })),
          (v[47] = w),
          (v[48] = u),
          (v[49] = h),
          (v[50] = x),
          (v[51] = p),
          (v[52] = _))
        : (_ = v[52]),
      _
    );
  };
  let th = () => {
    let e,
      a,
      s,
      n = (0, r.c)(3);
    return (
      n[0] === Symbol.for("react.memo_cache_sentinel")
        ? ((e = (0, H.c)(ta, "min-w-40 hover:bg-bg-tertiary")), (n[0] = e))
        : (e = n[0]),
      n[1] === Symbol.for("react.memo_cache_sentinel")
        ? ((a = (0, t.jsxs)("div", {
            className: "flex items-center gap-2",
            children: [
              (0, t.jsx)(T.l, { variant: "circle", size: $, className: ts }),
              (0, t.jsx)(T.l, { height: 14, width: 64, className: ts }),
            ],
          })),
          (n[1] = a))
        : (a = n[1]),
      n[2] === Symbol.for("react.memo_cache_sentinel")
        ? ((s = (0, t.jsxs)("div", {
            "aria-hidden": !0,
            className: e,
            children: [
              a,
              (0, t.jsxs)("div", {
                className: "flex flex-col gap-1 py-0.5",
                children: [
                  (0, t.jsx)(T.l, { height: 14, width: 80, className: ts }),
                  (0, t.jsx)(T.l, { height: 12, width: 48, className: ts }),
                ],
              }),
            ],
          })),
          (n[2] = s))
        : (s = n[2]),
      s
    );
  };
  let tf = (e) => {
    let a,
      s,
      l,
      i,
      c,
      o,
      d,
      u,
      m,
      h,
      x,
      p,
      b,
      w,
      _,
      v,
      k,
      y = (0, r.c)(49),
      { coin: j, onClick: A, index: E } = e;
    y[0] !== j
      ? ((a = {
          mint: j.mint,
          chainId: j.chain_id,
          fallbackMarketCap: j.usd_market_cap,
          coin: j,
        }),
        (y[0] = j),
        (y[1] = a))
      : (a = y[1]);
    let I = (0, O.h)(a);
    (y[2] !== j.usd_market_cap
      ? ((s = j.usd_market_cap ? Number(j.usd_market_cap.toFixed(2)) : 0),
        (y[2] = j.usd_market_cap),
        (y[3] = s))
      : (s = y[3]),
      y[4] !== E || y[5] !== s
        ? ((l = {
            itemPosition: E,
            marketCap: s,
            sourceScreen: n.Ae.SEARCH,
            sourceElement: n.k9.ACTIVE_SEARCH_TRENDING_COIN_LIST,
          }),
          (y[4] = E),
          (y[5] = s),
          (y[6] = l))
        : (l = y[6]));
    let T = l,
      q = (0, L.f)(j.mint, T, void 0, n.k9.ACTIVE_SEARCH_TRENDING_COIN_LIST),
      { handleCoinClick: U } = (0, M.f)(),
      { setLastClickImpression: D } = (0, B.y)();
    y[7] !== j.chain_id
      ? ((i = { chainId: j.chain_id }), (y[7] = j.chain_id), (y[8] = i))
      : (i = y[8]);
    let {
      candlesticks: z,
      error: K,
      isLoading: F,
    } = (0, eN.f)(j.mint, j.created_timestamp ?? null, void 0, i);
    y[9] !== j.symbol
      ? ((c = (0, S.W)(j.symbol)), (y[9] = j.symbol), (y[10] = c))
      : (c = y[10]);
    let W = c,
      { prefetch: V, hoverProps: Q } = (0, R.W)(j),
      G = `/coin/${j.mint}`;
    (y[11] !== j.mint ||
    y[12] !== U ||
    y[13] !== T ||
    y[14] !== A ||
    y[15] !== D
      ? ((o = () => {
          (T && (D(j.mint, T), U(j.mint, T)), A());
        }),
        (y[11] = j.mint),
        (y[12] = U),
        (y[13] = T),
        (y[14] = A),
        (y[15] = D),
        (y[16] = o))
      : (o = y[16]),
      y[17] === Symbol.for("react.memo_cache_sentinel")
        ? ((d = (0, H.c)(ta, "focus-inset min-w-36")), (y[17] = d))
        : (d = y[17]),
      y[18] !== j
        ? ((u = (0, t.jsx)(N.CoinAvatar, { coin: j, size: $, hideCorner: !0 })),
          (y[18] = j),
          (y[19] = u))
        : (u = y[19]),
      y[20] !== j
        ? ((m = (0, t.jsx)(C.f, {
            coin: j,
            nameClassName: "text-sm leading-5",
          })),
          (y[20] = j),
          (y[21] = m))
        : (m = y[21]),
      y[22] !== W
        ? ((h = W
            ? (0, t.jsxs)("span", {
                className: "truncate text-xs leading-4 text-text-quaternary",
                children: ["$", W],
              })
            : null),
          (y[22] = W),
          (y[23] = h))
        : (h = y[23]),
      y[24] !== h || y[25] !== m
        ? ((x = (0, t.jsxs)("div", {
            className: "flex min-w-0 flex-col",
            children: [m, h],
          })),
          (y[24] = h),
          (y[25] = m),
          (y[26] = x))
        : (x = y[26]),
      y[27] !== x || y[28] !== u
        ? ((p = (0, t.jsxs)("div", {
            className: "flex items-center gap-2",
            children: [u, x],
          })),
          (y[27] = x),
          (y[28] = u),
          (y[29] = p))
        : (p = y[29]),
      y[30] !== z || y[31] !== K || y[32] !== F
        ? ((b = (0, t.jsx)("div", {
            className: "pointer-events-none",
            children: (0, t.jsx)(g.f, {
              className: "h-12 w-full",
              data: z,
              error: K,
              isLoading: F,
            }),
          })),
          (y[30] = z),
          (y[31] = K),
          (y[32] = F),
          (y[33] = b))
        : (b = y[33]));
    let J = I ?? j.usd_market_cap;
    return (
      y[34] !== J ? ((w = (0, P.l)(J)), (y[34] = J), (y[35] = w)) : (w = y[35]),
      y[36] !== w
        ? ((_ = (0, t.jsx)("span", {
            className:
              "text-sm font-medium leading-5 tabular-nums text-text-primary",
            children: w,
          })),
          (y[36] = w),
          (y[37] = _))
        : (_ = y[37]),
      y[38] !== Q ||
      y[39] !== V ||
      y[40] !== p ||
      y[41] !== b ||
      y[42] !== _ ||
      y[43] !== G ||
      y[44] !== o
        ? ((v = (0, t.jsxs)(f.default, {
            href: G,
            prefetch: V,
            ...Q,
            onClick: o,
            "data-search-tile": !0,
            className: d,
            children: [p, b, _],
          })),
          (y[38] = Q),
          (y[39] = V),
          (y[40] = p),
          (y[41] = b),
          (y[42] = _),
          (y[43] = G),
          (y[44] = o),
          (y[45] = v))
        : (v = y[45]),
      y[46] !== q || y[47] !== v
        ? ((k = (0, t.jsx)("div", { ref: q, className: "flex", children: v })),
          (y[46] = q),
          (y[47] = v),
          (y[48] = k))
        : (k = y[48]),
      k
    );
  };
  let tx = () => {
    let e,
      a,
      s,
      n,
      l = (0, r.c)(4);
    return (
      l[0] === Symbol.for("react.memo_cache_sentinel")
        ? ((e = (0, H.c)(ta, "min-w-36 hover:bg-bg-tertiary")), (l[0] = e))
        : (e = l[0]),
      l[1] === Symbol.for("react.memo_cache_sentinel")
        ? ((a = (0, t.jsx)(T.l, { variant: "art", size: $, className: ts })),
          (l[1] = a))
        : (a = l[1]),
      l[2] === Symbol.for("react.memo_cache_sentinel")
        ? ((s = (0, t.jsxs)("div", {
            className: "flex items-center gap-2",
            children: [
              a,
              (0, t.jsxs)("div", {
                className: "flex flex-col gap-1",
                children: [
                  (0, t.jsx)(T.l, { height: 14, width: 64, className: ts }),
                  (0, t.jsx)(T.l, { height: 12, width: 40, className: ts }),
                ],
              }),
            ],
          })),
          (l[2] = s))
        : (s = l[2]),
      l[3] === Symbol.for("react.memo_cache_sentinel")
        ? ((n = (0, t.jsxs)("div", {
            "aria-hidden": !0,
            className: e,
            children: [
              s,
              (0, t.jsx)(T.l, {
                height: 48,
                className: (0, H.c)("w-full", ts),
              }),
              (0, t.jsx)(T.l, { height: 14, width: 56, className: ts }),
            ],
          })),
          (l[3] = n))
        : (n = l[3]),
      n
    );
  };
  let tp = (e) => {
    let s,
      n,
      l,
      i,
      c,
      o,
      d,
      u,
      m,
      h,
      f,
      x,
      g,
      b,
      w,
      _,
      v,
      k = (0, r.c)(50),
      {
        topTraders: y,
        topTradersLoading: j,
        trendingCoins: N,
        trendingLoading: C,
        onNavigate: S,
      } = e,
      { t: A } = (0, p.f)(),
      [E, I] = (0, a.useState)(eb),
      T = (function () {
        let e,
          t,
          s,
          n,
          l,
          i,
          c = (0, r.c)(14),
          [o, d] = (0, a.useState)(null);
        c[0] !== o
          ? ((e = (e) => {
              if (!o) return ef;
              o.addEventListener("scroll", e, { passive: !0 });
              let t =
                "u" < typeof ResizeObserver ? null : new ResizeObserver(e);
              t?.observe(o);
              let r = new MutationObserver(e);
              return (
                r.observe(o, { childList: !0 }),
                () => {
                  (o.removeEventListener("scroll", e),
                    t?.disconnect(),
                    r.disconnect());
                }
              );
            }),
            (c[0] = o),
            (c[1] = e))
          : (e = c[1]);
        let u = e;
        c[2] !== o
          ? ((t = () => {
              let e;
              return o
                ? ((e = o.scrollWidth - o.clientWidth),
                  (o.scrollLeft <= 1) | (2 * (o.scrollLeft >= e - 1)))
                : 3;
            }),
            (c[2] = o),
            (c[3] = t))
          : (t = c[3]);
        let m = (0, a.useSyncExternalStore)(u, t, eh);
        c[4] !== o
          ? ((s = (e) => {
              o &&
                o.scrollBy({
                  left: e * o.clientWidth,
                  behavior: window.matchMedia?.(
                    "(prefers-reduced-motion: reduce)",
                  ).matches
                    ? "auto"
                    : "smooth",
                });
            }),
            (c[4] = o),
            (c[5] = s))
          : (s = c[5]);
        let h = s,
          f = (1 & m) != 0,
          x = (2 & m) != 0;
        return (
          c[6] !== h
            ? ((n = () => h(-1)),
              (l = () => h(1)),
              (c[6] = h),
              (c[7] = n),
              (c[8] = l))
            : ((n = c[7]), (l = c[8])),
          c[9] !== f || c[10] !== x || c[11] !== n || c[12] !== l
            ? ((i = {
                attachStrip: d,
                atStart: f,
                atEnd: x,
                pagePrevious: n,
                pageNext: l,
              }),
              (c[9] = f),
              (c[10] = x),
              (c[11] = n),
              (c[12] = l),
              (c[13] = i))
            : (i = c[13]),
          i
        );
      })();
    k[0] !== T
      ? (({ attachStrip: s, ...n } = T), (k[0] = T), (k[1] = s), (k[2] = n))
      : ((s = k[1]), (n = k[2]));
    let R = C || N.length > 0,
      M = j || y.length > 0;
    k[3] !== E || k[4] !== R || k[5] !== M
      ? ((i = (({ picked: e, available: t }) => {
          if (t[e]) return e;
          let r = "hot-coins" === e ? "top-traders" : "hot-coins";
          return t[r] ? r : null;
        })({
          picked: E,
          available: (l = { "hot-coins": R, "top-traders": M }),
        })),
        (k[3] = E),
        (k[4] = R),
        (k[5] = M),
        (k[6] = l),
        (k[7] = i))
      : ((l = k[6]), (i = k[7]));
    let L = i;
    k[8] === Symbol.for("react.memo_cache_sentinel")
      ? ((c = (e) => {
          I(e);
          try {
            window.sessionStorage.setItem(ep, e);
          } catch {}
        }),
        (k[8] = c))
      : (c = k[8]);
    let P = c;
    k[9] !== L ||
    k[10] !== S ||
    k[11] !== y ||
    k[12] !== j ||
    k[13] !== N ||
    k[14] !== C
      ? ((o =
          "top-traders" === L
            ? j
              ? Array.from({ length: 5 }, tS)
              : y.map((e) =>
                  (0, t.jsx)(tm, { entry: e, onClick: S }, e.walletAddress),
                )
            : "hot-coins" === L
              ? C
                ? Array.from({ length: 5 }, tA)
                : N.map((e, r) =>
                    (0, t.jsx)(tf, { coin: e, index: r, onClick: S }, e.mint),
                  )
              : null),
        (k[9] = L),
        (k[10] = S),
        (k[11] = y),
        (k[12] = j),
        (k[13] = N),
        (k[14] = C),
        (k[15] = o))
      : (o = k[15]);
    let O = o,
      U = "top-traders" === L ? "search-top-traders" : "search-hot-coins";
    k[16] !== A
      ? ((d = A("web.nav.discover")), (k[16] = A), (k[17] = d))
      : (d = k[17]);
    let D = L ?? E;
    k[18] !== A
      ? ((u = A("web.search.hot_coins")), (k[18] = A), (k[19] = u))
      : (u = k[19]);
    let z = !l["hot-coins"];
    (k[20] !== u || k[21] !== z
      ? ((m = { value: "hot-coins", label: u, disabled: z }),
        (k[20] = u),
        (k[21] = z),
        (k[22] = m))
      : (m = k[22]),
      k[23] !== A
        ? ((h = A("web.search.top_traders")), (k[23] = A), (k[24] = h))
        : (h = k[24]));
    let H = !l["top-traders"];
    return (
      k[25] !== h || k[26] !== H
        ? ((f = { value: "top-traders", label: h, disabled: H }),
          (k[25] = h),
          (k[26] = H),
          (k[27] = f))
        : (f = k[27]),
      k[28] !== m || k[29] !== f
        ? ((x = [m, f]), (k[28] = m), (k[29] = f), (k[30] = x))
        : (x = k[30]),
      k[31] !== x || k[32] !== d || k[33] !== D
        ? ((g = (0, t.jsx)(ey.X, {
            density: K,
            "aria-label": d,
            value: D,
            onValueChange: P,
            options: x,
          })),
          (k[31] = x),
          (k[32] = d),
          (k[33] = D),
          (k[34] = g))
        : (g = k[34]),
      k[35] !== L || k[36] !== n
        ? ((b = L ? (0, t.jsx)(ex, { density: K, ...n }) : void 0),
          (k[35] = L),
          (k[36] = n),
          (k[37] = b))
        : (b = k[37]),
      k[38] !== g || k[39] !== b
        ? ((w = (0, t.jsx)(q._, {
            density: K,
            titleAs: "span",
            truncateTitle: !1,
            title: g,
            className: Q,
            action: b,
          })),
          (k[38] = g),
          (k[39] = b),
          (k[40] = w))
        : (w = k[40]),
      k[41] !== L || k[42] !== s || k[43] !== O || k[44] !== A
        ? ((_ = L
            ? (0, t.jsx)(
                "div",
                {
                  ref: s,
                  className:
                    "flex gap-3 overflow-x-auto px-5 py-3 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden",
                  children: O,
                },
                L,
              )
            : (0, t.jsx)(e_.L, {
                density: K,
                children: A("web.search.no_trending_coins"),
              })),
          (k[41] = L),
          (k[42] = s),
          (k[43] = O),
          (k[44] = A),
          (k[45] = _))
        : (_ = k[45]),
      k[46] !== w || k[47] !== _ || k[48] !== U
        ? ((v = (0, t.jsxs)("section", {
            className: "flex flex-col",
            "data-testid": U,
            children: [w, _],
          })),
          (k[46] = w),
          (k[47] = _),
          (k[48] = U),
          (k[49] = v))
        : (v = k[49]),
      v
    );
  };
  function tS(e, r) {
    return (0, t.jsx)(th, {}, r);
  }
  function tA(e, r) {
    return (0, t.jsx)(tx, {}, r);
  }
  let K = "comfortable";
  let Q = "border-b-0";
  let W = "absolute inset-0 z-[1] focus-inset";
  let $ = k.s.comfortable;
  return {
    DiscoverStrip: tp,
    TraderTile: tm,
    CoinTile: tf,
    TraderSkeleton: th,
    CoinSkeleton: tx,
    Arrows: ex,
  };
}
