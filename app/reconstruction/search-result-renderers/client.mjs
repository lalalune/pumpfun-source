// Full ordinary shared-search result components; all data/rendering providers are required capabilities.
import { profileRoute } from "../search-navigation/navigation.mjs";
export function createSearchResultRenderers(ports) {
  for (const name of [
    "useTranslation",
    "useCoinMarketCap",
    "useCoinImpression",
    "useCoinClick",
    "useLastClick",
    "useCoinPrefetch",
    "trackBookmark",
    "formatSymbol",
    "shortenAddress",
    "classNames",
    "formatMarketCap",
    "formatFollowers",
    "useVerifiedProfile",
    "groupRoute",
    "normalizeImage",
    "projectGroup",
    "isPerp",
    "perpDisplay",
    "memoCache",
  ])
    if (typeof ports?.[name] !== "function")
      throw new TypeError(
        "Explicit search result capability required: " + name,
      );
  for (const name of [
    "BookmarkMenu",
    "CoinAvatar",
    "CoinName",
    "RelativeTime",
    "Link",
    "ProfileDisplay",
    "SkeletonPart",
    "Avatar",
    "GroupIcon",
    "Badge",
    "Heading",
    "PerpRow",
  ])
    if (!ports.renderers?.[name])
      throw new TypeError("Explicit search result renderer required: " + name);
  if (
    !ports.jsxRuntime ||
    !ports.theme ||
    !ports.styles ||
    !Object.hasOwn(ports, "avatarSize") ||
    !Object.hasOwn(ports, "imagePrefix")
  )
    throw new TypeError(
      "Explicit JSX/theme/style/avatar/image-prefix capabilities required",
    );
  const t = ports.jsxRuntime,
    r = { c: ports.memoCache },
    o = { $: profileRoute },
    k = ports.theme,
    F = ports.styles.row,
    V = ports.styles.seeAll,
    $ = ports.avatarSize,
    ea = { f: ports.imagePrefix },
    X = ports.renderers.PerpRow;
  const n = { Ae: { SEARCH: 9 }, k9: { ACTIVE_SEARCH_COIN_SEARCH_FEED: 15 } };
  const p = { f: ports.useTranslation };
  const O = { h: ports.useCoinMarketCap };
  const L = { f: ports.useCoinImpression };
  const M = { f: ports.useCoinClick };
  const B = { y: ports.useLastClick };
  const R = { W: ports.useCoinPrefetch };
  const z = { Op: ports.trackBookmark };
  const S = { W: ports.formatSymbol, e: ports.shortenAddress };
  const H = { c: ports.classNames };
  const P = { l: ports.formatMarketCap, O: ports.formatFollowers };
  const u = { s: ports.useVerifiedProfile };
  const es = { Z: ports.groupRoute };
  const _ = { f: ports.normalizeImage };
  const eo = { h: ports.projectGroup };
  const D = { x: ports.isPerp };
  const U = { K: ports.perpDisplay };
  const y = { f: ports.renderers.BookmarkMenu };
  const N = { CoinAvatar: ports.renderers.CoinAvatar };
  const C = { f: ports.renderers.CoinName };
  const E = { f: ports.renderers.RelativeTime };
  const f = { default: ports.renderers.Link };
  const A = { S: ports.renderers.ProfileDisplay };
  const T = { l: ports.renderers.SkeletonPart };
  const w = { f: ports.renderers.Avatar };
  const b = { BQ: ports.renderers.GroupIcon };
  const er = { E: ports.renderers.Badge };
  const q = { _: ports.renderers.Heading };
  let v = (e) => {
    let a,
      s,
      n = (0, r.c)(3),
      { className: l } = e;
    return (
      n[0] === Symbol.for("react.memo_cache_sentinel")
        ? ((a = (0, t.jsx)("path", {
            d: "M6 6V5.25C6 3.317 4.433 1.75 2.5 1.75H1.75V2.5C1.75 4.433 3.317 6 5.25 6H6ZM6 6V10.25M9.5 3.25H10.25V4C10.25 5.933 8.683 7.5 6.75 7.5H6V6.75C6 4.817 7.567 3.25 9.5 3.25Z",
            stroke: "currentColor",
            strokeLinecap: "round",
            strokeLinejoin: "round",
          })),
          (n[0] = a))
        : (a = n[0]),
      n[1] !== l
        ? ((s = (0, t.jsx)("svg", {
            xmlns: "http://www.w3.org/2000/svg",
            width: "12",
            height: "12",
            viewBox: "0 0 12 12",
            fill: "none",
            className: l,
            children: a,
          })),
          (n[1] = l),
          (n[2] = s))
        : (s = n[2]),
      s
    );
  };
  let Z = (e) => {
    let a,
      s = (0, r.c)(8);
    if ((0, D.x)(e.coin)) {
      let r, a;
      s[0] !== e.coin
        ? ((r = (0, U.K)(e.coin)), (s[0] = e.coin), (s[1] = r))
        : (r = s[1]);
      let n = r;
      return (
        s[2] !== n || s[3] !== e.index || s[4] !== e.onClick
          ? ((a = n
              ? (0, t.jsx)(X, { market: n, index: e.index, onClick: e.onClick })
              : null),
            (s[2] = n),
            (s[3] = e.index),
            (s[4] = e.onClick),
            (s[5] = a))
          : (a = s[5]),
        a
      );
    }
    return (
      s[6] !== e
        ? ((a = (0, t.jsx)(Y, { ...e })), (s[6] = e), (s[7] = a))
        : (a = s[7]),
      a
    );
  };
  let Y = (e) => {
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
      g,
      b,
      w,
      _,
      j,
      A,
      I,
      T,
      q,
      U,
      D,
      W,
      V,
      Q,
      G = (0, r.c)(70),
      {
        coin: J,
        onClick: X,
        index: Z,
        sourceScreen: Y,
        sourceElement: ee,
        searchTerm: et,
      } = e,
      er = void 0 === Y ? n.Ae.SEARCH : Y,
      ea = void 0 === ee ? n.k9.ACTIVE_SEARCH_COIN_SEARCH_FEED : ee,
      { t: es } = (0, p.f)();
    G[0] !== J
      ? ((a = {
          mint: J.mint,
          chainId: J.chain_id,
          fallbackMarketCap: J.usd_market_cap,
          coin: J,
        }),
        (G[0] = J),
        (G[1] = a))
      : (a = G[1]);
    let en = (0, O.h)(a);
    (G[2] !== J.usd_market_cap
      ? ((s = J.usd_market_cap ? Number(J.usd_market_cap.toFixed(2)) : 0),
        (G[2] = J.usd_market_cap),
        (G[3] = s))
      : (s = G[3]),
      G[4] !== J.rec_id ||
      G[5] !== Z ||
      G[6] !== ea ||
      G[7] !== er ||
      G[8] !== s
        ? ((l = {
            itemPosition: Z,
            marketCap: s,
            sourceScreen: er,
            rec_id: J.rec_id,
            sourceElement: ea,
          }),
          (G[4] = J.rec_id),
          (G[5] = Z),
          (G[6] = ea),
          (G[7] = er),
          (G[8] = s),
          (G[9] = l))
        : (l = G[9]));
    let el = l,
      ei = (0, L.f)(J.mint, el, et, ea),
      { handleCoinClick: ec } = (0, M.f)(),
      { setLastClickImpression: eo } = (0, B.y)(),
      { prefetch: ed, hoverProps: eu } = (0, R.W)(J);
    G[10] !== ea || G[11] !== er
      ? ((i = {
          trackBookmarkToggle: (e, t) => {
            "add" === t &&
              (0, z.Op)({ mint: e, screen: er, sourceElement: ea });
          },
        }),
        (G[10] = ea),
        (G[11] = er),
        (G[12] = i))
      : (i = G[12]);
    let em = i;
    G[13] !== J.symbol
      ? ((c = (0, S.W)(J.symbol)), (G[13] = J.symbol), (G[14] = c))
      : (c = G[14]);
    let eh = c;
    G[15] === Symbol.for("react.memo_cache_sentinel")
      ? ((o = (0, H.c)(F, "group gap-2")), (G[15] = o))
      : (o = G[15]);
    let ef = Z + 1;
    G[16] !== J || G[17] !== ef || G[18] !== em
      ? ((d = (0, t.jsx)(y.f, {
          coin: J,
          align: "start",
          position: ef,
          analytics: em,
        })),
        (G[16] = J),
        (G[17] = ef),
        (G[18] = em),
        (G[19] = d))
      : (d = G[19]);
    let ex = `/coin/${J.mint}`;
    (G[20] !== J.mint ||
    G[21] !== ec ||
    G[22] !== el ||
    G[23] !== X ||
    G[24] !== et ||
    G[25] !== eo
      ? ((u = () => {
          (el && (eo(J.mint, el, et), ec(J.mint, el, et)), X());
        }),
        (G[20] = J.mint),
        (G[21] = ec),
        (G[22] = el),
        (G[23] = X),
        (G[24] = et),
        (G[25] = eo),
        (G[26] = u))
      : (u = G[26]),
      G[27] !== J
        ? ((m = (0, t.jsx)(N.CoinAvatar, { coin: J, size: $ })),
          (G[27] = J),
          (G[28] = m))
        : (m = G[28]),
      G[29] !== J
        ? ((h = (0, t.jsx)("span", {
            className: k.x[K],
            children: (0, t.jsx)(C.f, { coin: J, nameClassName: k.n[K] }),
          })),
          (G[29] = J),
          (G[30] = h))
        : (h = G[30]),
      G[31] === Symbol.for("react.memo_cache_sentinel")
        ? ((x = (0, H.c)("flex min-w-0 items-center", k.B[K], k.Y[K])),
          (G[31] = x))
        : (x = G[31]),
      G[32] !== eh
        ? ((g = eh
            ? (0, t.jsxs)("span", {
                className: "shrink-0",
                children: ["$", eh],
              })
            : null),
          (G[32] = eh),
          (G[33] = g))
        : (g = G[33]),
      G[34] !== J.mint
        ? ((b = (0, S.e)(J.mint)), (G[34] = J.mint), (G[35] = b))
        : (b = G[35]),
      G[36] !== b
        ? ((w = (0, t.jsx)("span", {
            className: "min-w-0 truncate tabular-nums",
            children: b,
          })),
          (G[36] = b),
          (G[37] = w))
        : (w = G[37]),
      G[38] !== g || G[39] !== w
        ? ((_ = (0, t.jsxs)("span", { className: x, children: [g, w] })),
          (G[38] = g),
          (G[39] = w),
          (G[40] = _))
        : (_ = G[40]),
      G[41] !== h || G[42] !== _
        ? ((j = (0, t.jsxs)("div", {
            className: "flex min-w-0 flex-1 flex-col",
            children: [h, _],
          })),
          (G[41] = h),
          (G[42] = _),
          (G[43] = j))
        : (j = G[43]));
    let ep = en ?? J.usd_market_cap;
    return (
      G[44] !== ep
        ? ((A = (0, P.l)(ep)), (G[44] = ep), (G[45] = A))
        : (A = G[45]),
      G[46] !== A
        ? ((I = (0, t.jsx)("span", {
            "data-testid": "search-coin-row-mcap",
            className: k.e[K],
            children: A,
          })),
          (G[46] = A),
          (G[47] = I))
        : (I = G[47]),
      G[48] === Symbol.for("react.memo_cache_sentinel")
        ? ((T = (0, H.c)(k.N, k.C[K], "gap-1 text-text-quaternary")),
          (q = (0, t.jsx)(v, { className: "size-3 shrink-0" })),
          (G[48] = T),
          (G[49] = q))
        : ((T = G[48]), (q = G[49])),
      G[50] !== J.created_timestamp || G[51] !== es
        ? ((U = J.created_timestamp
            ? (0, t.jsx)(E.f, {
                timestamp: J.created_timestamp,
                density: K,
                suffix: !1,
              })
            : es("web.search.unknown_creation_date")),
          (G[50] = J.created_timestamp),
          (G[51] = es),
          (G[52] = U))
        : (U = G[52]),
      G[53] !== U
        ? ((D = (0, t.jsxs)("span", {
            "data-search-row-age": !0,
            className: T,
            children: [q, U],
          })),
          (G[53] = U),
          (G[54] = D))
        : (D = G[54]),
      G[55] !== I || G[56] !== D
        ? ((W = (0, t.jsxs)("div", {
            className: "flex shrink-0 flex-col items-end",
            children: [I, D],
          })),
          (G[55] = I),
          (G[56] = D),
          (G[57] = W))
        : (W = G[57]),
      G[58] !== eu ||
      G[59] !== ed ||
      G[60] !== ex ||
      G[61] !== u ||
      G[62] !== m ||
      G[63] !== j ||
      G[64] !== W
        ? ((V = (0, t.jsxs)(f.default, {
            href: ex,
            prefetch: ed,
            ...eu,
            onClick: u,
            className: "focus-inset flex min-w-0 flex-1 items-center gap-3",
            children: [m, j, W],
          })),
          (G[58] = eu),
          (G[59] = ed),
          (G[60] = ex),
          (G[61] = u),
          (G[62] = m),
          (G[63] = j),
          (G[64] = W),
          (G[65] = V))
        : (V = G[65]),
      G[66] !== ei || G[67] !== V || G[68] !== d
        ? ((Q = (0, t.jsxs)("div", {
            ref: ei,
            "data-search-row": !0,
            className: o,
            children: [d, V],
          })),
          (G[66] = ei),
          (G[67] = V),
          (G[68] = d),
          (G[69] = Q))
        : (Q = G[69]),
      Q
    );
  };
  let ee = (e) => {
    let a,
      s,
      n,
      l,
      i,
      c,
      d = (0, r.c)(29),
      { user: m, onClick: h } = e,
      { t: x } = (0, p.f)(),
      g = (0, u.s)(m.userId ?? m.address);
    d[0] !== m.address || d[1] !== m.userId
      ? ((a = (0, o.$)({ address: m.address, userId: m.userId })),
        (d[0] = m.address),
        (d[1] = m.userId),
        (d[2] = a))
      : (a = d[2]);
    let b = a;
    d[3] !== x ||
    d[4] !== m.address ||
    d[5] !== m.username ||
    d[6] !== m.wallet_label
      ? ((s =
          m.wallet_label ||
          m.username ||
          m.address?.slice(0, 6) ||
          x("web.search.anonymous_fallback")),
        (d[3] = x),
        (d[4] = m.address),
        (d[5] = m.username),
        (d[6] = m.wallet_label),
        (d[7] = s))
      : (s = d[7]);
    let w = s;
    d[8] !== b || d[9] !== w || d[10] !== h
      ? ((n = b
          ? (0, t.jsx)(f.default, {
              href: b,
              onClick: h,
              "aria-label": w,
              className: W,
            })
          : null),
        (d[8] = b),
        (d[9] = w),
        (d[10] = h),
        (d[11] = n))
      : (n = d[11]);
    let _ = m.address ?? null,
      v = m.userId,
      k = m.username,
      y = m.profile_image,
      j = m.resolved_avatar_decoration,
      N = m.x_username,
      C = !1 === m.is_pump_user;
    if (d[12] !== x || d[13] !== m)
      ((l =
        void 0 === m.wallet_label
          ? x("common.followers_count", {
              count: m.followers ?? 0,
              compact_count: (0, P.O)(m.followers ?? 0),
            })
          : !1 === m.is_pump_user
            ? x("search.external_wallet.subtitle")
            : m.address?.slice(0, 6)),
        (d[12] = x),
        (d[13] = m),
        (d[14] = l));
    else l = d[14];
    return (
      d[15] !== g ||
      d[16] !== w ||
      d[17] !== C ||
      d[18] !== l ||
      d[19] !== _ ||
      d[20] !== m.profile_image ||
      d[21] !== m.resolved_avatar_decoration ||
      d[22] !== m.userId ||
      d[23] !== m.username ||
      d[24] !== m.x_username
        ? ((i = (0, t.jsx)(A.S, {
            address: _,
            userId: v,
            username: k,
            profileImage: y,
            avatarDecoration: j,
            nameOverride: w,
            size: $,
            density: K,
            link: !1,
            hoverCard: !1,
            verified: g,
            xUsername: N,
            outsideWallet: C,
            description: l,
            className: "min-w-0 flex-1",
          })),
          (d[15] = g),
          (d[16] = w),
          (d[17] = C),
          (d[18] = l),
          (d[19] = _),
          (d[20] = m.profile_image),
          (d[21] = m.resolved_avatar_decoration),
          (d[22] = m.userId),
          (d[23] = m.username),
          (d[24] = m.x_username),
          (d[25] = i))
        : (i = d[25]),
      d[26] !== i || d[27] !== n
        ? ((c = (0, t.jsxs)("div", {
            "data-search-row": !0,
            className: F,
            children: [n, i],
          })),
          (d[26] = i),
          (d[27] = n),
          (d[28] = c))
        : (c = d[28]),
      c
    );
  };
  let et = (e) => {
    let a,
      s = (0, r.c)(5),
      { rows: n, variant: l } = e;
    if (s[0] !== n || s[1] !== l) {
      let e;
      (s[3] !== l
        ? ((e = (e, r) =>
            (0, t.jsxs)(
              "div",
              {
                className: (0, H.c)(F, "hover:bg-transparent"),
                children: [
                  (0, t.jsx)(T.l, { variant: l, size: $ }),
                  (0, t.jsxs)("div", {
                    className: "flex min-w-0 flex-1 flex-col gap-1 py-0.5",
                    children: [
                      (0, t.jsx)(T.l, { height: 14, width: 112 }),
                      (0, t.jsx)(T.l, { height: 12, width: 48 }),
                    ],
                  }),
                  (0, t.jsxs)("div", {
                    className: "flex shrink-0 flex-col items-end gap-1 py-0.5",
                    children: [
                      (0, t.jsx)(T.l, { height: 14, width: 48 }),
                      (0, t.jsx)(T.l, { height: 12, width: 40 }),
                    ],
                  }),
                ],
              },
              r,
            )),
          (s[3] = l),
          (s[4] = e))
        : (e = s[4]),
        (a = (0, t.jsx)("div", {
          "aria-hidden": !0,
          className: "flex flex-col",
          "data-testid": "search-results-skeleton",
          children: Array.from({ length: n }, e),
        })),
        (s[0] = n),
        (s[1] = l),
        (s[2] = a));
    } else a = s[2];
    return a;
  };
  function en(e) {
    let a,
      s,
      n,
      l,
      i,
      c,
      o,
      d,
      u,
      m,
      h,
      x,
      g,
      v = (0, r.c)(32),
      { squad: k, onClick: y } = e,
      { t: j } = (0, p.f)();
    v[0] !== j
      ? ((a = j("profile.squads.profile.pill")), (v[0] = j), (v[1] = a))
      : (a = v[1]);
    let N = a,
      C = k.username || N;
    (v[2] === Symbol.for("react.memo_cache_sentinel")
      ? ((s = (0, H.c)(F, "focus-inset")), (v[2] = s))
      : (s = v[2]),
      v[3] !== k.groupId || v[4] !== k.username
        ? ((n = (0, es.Z)({ groupId: k.groupId, username: k.username })),
          (v[3] = k.groupId),
          (v[4] = k.username),
          (v[5] = n))
        : (n = v[5]));
    let S = k.groupId;
    return (
      v[6] !== k.profileImage
        ? ((l = (0, _.f)(k.profileImage)), (v[6] = k.profileImage), (v[7] = l))
        : (l = v[7]),
      v[8] !== k.groupId || v[9] !== l
        ? ((i = (0, t.jsx)(w.f, {
            address: S,
            alt: "",
            className: "size-7 shrink-0 rounded-md object-cover",
            height: $,
            ipfsPrefix: ea.f,
            isAnonymous: !1,
            src: l,
            width: $,
          })),
          (v[8] = k.groupId),
          (v[9] = l),
          (v[10] = i))
        : (i = v[10]),
      v[11] !== C
        ? ((c = (0, t.jsx)("span", {
            className:
              "min-w-0 truncate text-sm font-medium leading-5 text-text-primary",
            children: C,
          })),
          (v[11] = C),
          (v[12] = c))
        : (c = v[12]),
      v[13] === Symbol.for("react.memo_cache_sentinel")
        ? ((o = (0, t.jsx)(b.BQ, { "aria-hidden": !0, size: 12 })), (v[13] = o))
        : (o = v[13]),
      v[14] !== N
        ? ((d = (0, t.jsxs)(er.E, {
            density: K,
            tone: "mint",
            children: [o, N],
          })),
          (v[14] = N),
          (v[15] = d))
        : (d = v[15]),
      v[16] !== c || v[17] !== d
        ? ((u = (0, t.jsxs)("span", {
            className: "flex h-5 min-w-0 items-center gap-1.5",
            children: [c, d],
          })),
          (v[16] = c),
          (v[17] = d),
          (v[18] = u))
        : (u = v[18]),
      v[19] !== k.memberCount || v[20] !== j
        ? ((m = j("profile.squads.info.member_count", {
            count: k.memberCount,
          })),
          (v[19] = k.memberCount),
          (v[20] = j),
          (v[21] = m))
        : (m = v[21]),
      v[22] !== m
        ? ((h = (0, t.jsx)("span", {
            className: "truncate text-xs leading-4 text-text-tertiary",
            children: m,
          })),
          (v[22] = m),
          (v[23] = h))
        : (h = v[23]),
      v[24] !== u || v[25] !== h
        ? ((x = (0, t.jsxs)("div", {
            className: "flex min-w-0 flex-1 flex-col",
            children: [u, h],
          })),
          (v[24] = u),
          (v[25] = h),
          (v[26] = x))
        : (x = v[26]),
      v[27] !== y || v[28] !== x || v[29] !== n || v[30] !== i
        ? ((g = (0, t.jsxs)(f.default, {
            className: s,
            "data-testid": "search-squad-row",
            href: n,
            onClick: y,
            prefetch: !1,
            children: [i, x],
          })),
          (v[27] = y),
          (v[28] = x),
          (v[29] = n),
          (v[30] = i),
          (v[31] = g))
        : (g = v[31]),
      g
    );
  }
  let ed = (e) => {
    let a,
      s,
      n,
      l,
      i = (0, r.c)(16),
      { tab: c, title: o, section: d, onSeeAll: u, children: m } = e,
      { t: h } = (0, p.f)(),
      f = `search-preview-${c}`;
    return (
      i[0] !== u || i[1] !== d.hasMore || i[2] !== h || i[3] !== c
        ? ((a = d.hasMore
            ? (0, t.jsx)("button", {
                type: "button",
                className: V,
                onClick: () => u(c),
                children: h("common.see_all"),
              })
            : void 0),
          (i[0] = u),
          (i[1] = d.hasMore),
          (i[2] = h),
          (i[3] = c),
          (i[4] = a))
        : (a = i[4]),
      i[5] !== a || i[6] !== o
        ? ((s = (0, t.jsx)(q._, {
            density: K,
            title: o,
            className: Q,
            aside: a,
          })),
          (i[5] = a),
          (i[6] = o),
          (i[7] = s))
        : (s = i[7]),
      i[8] !== m || i[9] !== d.loading || i[10] !== c
        ? ((n = d.loading
            ? (0, t.jsx)(et, { rows: 2, variant: J[c] })
            : (0, t.jsx)("div", { className: "flex flex-col", children: m })),
          (i[8] = m),
          (i[9] = d.loading),
          (i[10] = c),
          (i[11] = n))
        : (n = i[11]),
      i[12] !== f || i[13] !== s || i[14] !== n
        ? ((l = (0, t.jsxs)("section", {
            className: "flex flex-col",
            "data-testid": f,
            children: [s, n],
          })),
          (i[12] = f),
          (i[13] = s),
          (i[14] = n),
          (i[15] = l))
        : (l = i[15]),
      l
    );
  };
  let eu = (e) => {
    let a,
      s,
      n,
      l,
      i = (0, r.c)(20),
      {
        searchTerm: c,
        coins: o,
        users: d,
        squads: u,
        onSeeAll: m,
        onCoinClick: h,
        onUserClick: f,
        onSquadClick: x,
      } = e,
      { t: g } = (0, p.f)();
    return (
      i[0] !== o || i[1] !== h || i[2] !== m || i[3] !== c || i[4] !== g
        ? ((a = o.visible
            ? (0, t.jsx)(ed, {
                tab: "coins",
                title: g("search.coins"),
                section: o,
                onSeeAll: m,
                children: o.rows.map((e, r) =>
                  (0, t.jsx)(
                    Z,
                    { coin: e, index: r, searchTerm: c, onClick: () => h(e) },
                    e.mint,
                  ),
                ),
              })
            : null),
          (i[0] = o),
          (i[1] = h),
          (i[2] = m),
          (i[3] = c),
          (i[4] = g),
          (i[5] = a))
        : (a = i[5]),
      i[6] !== m || i[7] !== f || i[8] !== g || i[9] !== d
        ? ((s = d.visible
            ? (0, t.jsx)(ed, {
                tab: "users",
                title: g("search.users"),
                section: d,
                onSeeAll: m,
                children: d.rows.map((e) =>
                  (0, t.jsx)(
                    ee,
                    { user: e, onClick: () => f(e) },
                    e.userId ?? e.address,
                  ),
                ),
              })
            : null),
          (i[6] = m),
          (i[7] = f),
          (i[8] = g),
          (i[9] = d),
          (i[10] = s))
        : (s = i[10]),
      i[11] !== m || i[12] !== x || i[13] !== u || i[14] !== g
        ? ((n = u.visible
            ? (0, t.jsx)(ed, {
                tab: "squads",
                title: g("search.squads"),
                section: u,
                onSeeAll: m,
                children: u.rows.map((e) =>
                  (0, t.jsx)(
                    en,
                    { squad: (0, eo.h)(e), onClick: () => x(e) },
                    e.userId,
                  ),
                ),
              })
            : null),
          (i[11] = m),
          (i[12] = x),
          (i[13] = u),
          (i[14] = g),
          (i[15] = n))
        : (n = i[15]),
      i[16] !== a || i[17] !== s || i[18] !== n
        ? ((l = (0, t.jsxs)("div", {
            className: G,
            "data-testid": "search-results-preview",
            children: [a, s, n],
          })),
          (i[16] = a),
          (i[17] = s),
          (i[18] = n),
          (i[19] = l))
        : (l = i[19]),
      l
    );
  };
  let K = "comfortable";
  let Q = "border-b-0";
  let G = "flex flex-col gap-2";
  let J = { coins: "art", users: "circle", squads: "art" };
  let W = "absolute inset-0 z-[1] focus-inset";
  return {
    CoinRow: Z,
    OrdinaryCoinRow: Y,
    UserRow: ee,
    GroupRow: en,
    Skeleton: et,
    MixedResults: eu,
  };
}
