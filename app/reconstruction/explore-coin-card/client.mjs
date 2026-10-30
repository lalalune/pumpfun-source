// Editable complete ordinary MAIN Explore Card and local display/clock owners.
// Required initialized namespaces/providers/actions stay explicit; captures never execute.
import {profileRoute} from '../search-navigation/navigation.mjs';
function context0(lookupModule,loadModule,host){
const {window,Date,setTimeout,setInterval,clearInterval}=host;
var t = lookupModule(732486),
  i = lookupModule(445242),
  r = lookupModule(157633),
  a = lookupModule(322315),
  n = lookupModule(254010),
  s = lookupModule(584582),
  l = lookupModule(146695),
  o = lookupModule(782067),
  c = lookupModule(7284),
  m = lookupModule(453706),
  u = lookupModule(458310),
  d = lookupModule(599077),
  f = lookupModule(352386),
  p = lookupModule(667876),
  h = lookupModule(938277);
function x(e) {
  let r,
    a,
    n,
    s,
    l,
    o,
    c,
    m,
    u = (0, i.c)(18);
  u[0] !== e ? ({
    value: a,
    className: n,
    transition: s,
    ...r
  } = e, u[0] = e, u[1] = r, u[2] = a, u[3] = n, u[4] = s) : (r = u[1], a = u[2], n = u[3], s = u[4]);
  let d = void 0 === a ? 0 : a,
    p = void 0 === n ? "" : n,
    [x, v] = (0, f.useState)(d),
    [g, b] = (0, f.useState)(!1);
  if (x !== d) {
    let e = Math.abs((d - x) / x) >= .01;
    v(d), b(e);
  }
  let y = s?.duration != null ? 1e3 * s.duration : void 0,
    _ = `inline-block rounded-sm transform-gpu text-foreground ${g ? "animate-market-cap-flash will-change-[background-color]" : ""} ${p}`;
  return u[5] !== _ ? (l = _.trim(), u[5] = _, u[6] = l) : l = u[6], u[7] !== y || u[8] !== g ? (o = g && null != y ? {
    animationDuration: `${y}ms`
  } : void 0, u[7] = y, u[8] = g, u[9] = o) : o = u[9], u[10] !== d ? (c = (0, h.M)(d), u[10] = d, u[11] = c) : c = u[11], u[12] !== r || u[13] !== l || u[14] !== o || u[15] !== c || u[16] !== d ? (m = (0, t.jsxs)("div", {
    className: l,
    style: o,
    ...r,
    children: ["$", c]
  }, d), u[12] = r, u[13] = l, u[14] = o, u[15] = c, u[16] = d, u[17] = m) : m = u[17], m;
}
var v = lookupModule(713380),
  g = lookupModule(644350);
function b(e) {
  let r,
    a,
    n,
    s = (0, i.c)(14),
    {
      coin: l,
      eager: o,
      priority: c
    } = e;
  return s[0] !== l || s[1] !== o || s[2] !== c ? (r = (0, t.jsx)(g.f, {
    coin: l,
    width: 600,
    height: 600,
    eager: o,
    priority: c
  }), s[0] = l, s[1] = o, s[2] = c, s[3] = r) : r = s[3], s[4] !== l.board_program || s[5] !== l.chain_id || s[6] !== l.mint || s[7] !== l.platform || s[8] !== l.program || s[9] !== l.protocol ? (a = (0, t.jsx)(v.f, {
    mint: l.mint,
    chainId: l.chain_id,
    program: l.program,
    platform: l.platform,
    protocol: l.protocol,
    boardProgram: l.board_program,
    seal: !1,
    size: 20,
    chainSize: 20,
    venueSize: 20,
    className: "absolute bottom-1 right-1"
  }), s[4] = l.board_program, s[5] = l.chain_id, s[6] = l.mint, s[7] = l.platform, s[8] = l.program, s[9] = l.protocol, s[10] = a) : a = s[10], s[11] !== r || s[12] !== a ? (n = (0, t.jsxs)("span", {
    className: "relative block size-full",
    children: [r, a]
  }), s[11] = r, s[12] = a, s[13] = n) : n = s[13], n;
}
var y = lookupModule(670169),
  _ = lookupModule(574472),
  j = lookupModule(56267),
  N = lookupModule(66732),
  w = lookupModule(887827),
  k = lookupModule(960107),
  C = lookupModule(170450),
  I = lookupModule(300157);
function S(e) {
  let r,
    a,
    n,
    s,
    l,
    o,
    m,
    u,
    d,
    p,
    h,
    x = (0, i.c)(34),
    {
      addToBookmark: v,
      bookmarkedItems: g,
      bookmarks: b,
      coin: S,
      isBookmarked: E,
      isOpen: M,
      onManageWatchlistClick: R,
      removeFromBookmark: T,
      setOpen: $
    } = e,
    {
      decodedJwt: A
    } = (0, _.F)(),
    z = (0, C.f)() && !!A?.address,
    [F, O] = (0, f.useState)(!1);
  x[0] !== S.chain_id || x[1] !== S.mint ? (r = (0, I.y)({
    mint: S.mint,
    chainId: S.chain_id
  }), x[0] = S.chain_id, x[1] = S.mint, x[2] = r) : r = x[2];
  let P = r;
  x[3] !== v || x[4] !== P || x[5] !== b || x[6] !== T ? (a = function (e) {
    let t = b?.find(t => t.id === e)?.bookmark_items;
    (0, k.w)(t, P) && T && e ? T((0, k.T)(t, P), e) : v && (O(!0), v(P, e), setTimeout(() => O(!1), 600));
  }, x[3] = v, x[4] = P, x[5] = b, x[6] = T, x[7] = a) : a = x[7];
  let D = a;
  if (!z) return null;
  x[8] !== $ ? (n = e => $(e), x[8] = $, x[9] = n) : n = x[9];
  let L = M ? "flex" : void 0;
  return x[10] !== L ? (s = {
    display: L
  }, x[10] = L, x[11] = s) : s = x[11], x[12] !== E || x[13] !== F ? (l = E ? (0, t.jsx)(j.j, {
    className: (0, c.U)("text-green-300", F && "animate-watchlist-star-sparkle"),
    style: {
      fill: "#86efac"
    }
  }) : (0, t.jsx)(j.j, {
    className: (0, c.U)("text-text-tertiary hover:stroke-green-400", F && "animate-watchlist-star-sparkle")
  }), x[12] = E, x[13] = F, x[14] = l) : l = x[14], x[15] !== s || x[16] !== l ? (o = (0, t.jsx)(N.J, {
    className: "flex size-6 cursor-pointer items-center justify-center [@media(hover:hover)]:hidden [@media(hover:hover)]:group-hover:flex",
    style: s,
    children: l
  }), x[15] = s, x[16] = l, x[17] = o) : o = x[17], x[18] === Symbol.for("react.memo_cache_sentinel") ? (m = (0, t.jsx)(y.r, {
    className: "pointer-events-none absolute right-0 top-0 size-6"
  }), x[18] = m) : m = x[18], x[19] !== o ? (u = (0, t.jsxs)("div", {
    className: "relative",
    children: [o, m]
  }), x[19] = o, x[20] = u) : u = x[20], x[21] !== P || x[22] !== g || x[23] !== b || x[24] !== D || x[25] !== R ? (d = b && g && R ? (0, t.jsx)(w.f, {
    bookmarkedItems: g,
    bookmarks: b,
    mint: P,
    onBookmarkClick: D,
    onManageClick: R
  }) : null, x[21] = P, x[22] = g, x[23] = b, x[24] = D, x[25] = R, x[26] = d) : d = x[26], x[27] !== d ? (p = (0, t.jsx)(N.T, {
    align: "end",
    className: "w-48 border-border-tertiary bg-bg-tertiary p-0",
    children: d
  }), x[27] = d, x[28] = p) : p = x[28], x[29] !== M || x[30] !== p || x[31] !== n || x[32] !== u ? (h = (0, t.jsxs)(N.V, {
    onOpenChange: n,
    open: M,
    children: [u, p]
  }), x[29] = M, x[30] = p, x[31] = n, x[32] = u, x[33] = h) : h = x[33], h;
}
var E = lookupModule(642357);
lookupModule(12692);
var M = lookupModule(398902);
function R() {
  let e,
    a,
    n,
    s = (0, i.c)(5),
    {
      t: l
    } = (0, M.f)();
  return s[0] === Symbol.for("react.memo_cache_sentinel") ? (e = (0, t.jsx)(r.cJ, {
    className: "text-pink-500 drop-shadow-[0_1px_4px_rgba(236,72,153,0.55)]",
    size: 14
  }), s[0] = e) : e = s[0], s[1] !== l ? (a = l("creator_fees.charity.label"), s[1] = l, s[2] = a) : a = s[2], s[3] !== a ? (n = (0, t.jsxs)("div", {
    className: "flex h-5 w-fit shrink-0 items-center justify-center gap-x-1 rounded-[90px] border border-solid border-pink-500/40 bg-black/80 px-1.5",
    children: [e, (0, t.jsx)("p", {
      className: "text-xs font-medium text-pink-500",
      children: a
    })]
  }), s[3] = a, s[4] = n) : n = s[4], n;
}
function T() {
  let e,
    a,
    n,
    s = (0, i.c)(5),
    {
      t: l
    } = (0, M.f)();
  return s[0] === Symbol.for("react.memo_cache_sentinel") ? (e = (0, t.jsx)(r.s4, {
    className: "text-text-on-accent",
    size: 14
  }), s[0] = e) : e = s[0], s[1] !== l ? (a = l("web.nav.live"), s[1] = l, s[2] = a) : a = s[2], s[3] !== a ? (n = (0, t.jsxs)("div", {
    className: "flex rounded-[4px] bg-bg-accent px-1 items-center h-5 gap-x-1",
    children: [e, (0, t.jsx)("p", {
      className: "text-xs text-text-on-accent uppercase font-medium",
      children: a
    })]
  }), s[3] = a, s[4] = n) : n = s[4], n;
}
var $ = lookupModule(745018);
function A(e) {
  let r,
    a,
    n,
    s,
    l = (0, i.c)(10),
    {
      multiplayer: o
    } = e,
    c = void 0 !== o && o,
    {
      t: m
    } = (0, M.f)();
  return l[0] !== c ? (r = c ? (0, t.jsx)($.xI, {
    className: "text-text-accent",
    size: 14
  }) : (0, t.jsx)($.Sg, {
    className: "text-text-accent",
    size: 14
  }), l[0] = c, l[1] = r) : r = l[1], l[2] !== c || l[3] !== m ? (a = m(c ? "web.mayhem.mode_multiplayer" : "web.nav.mayhem"), l[2] = c, l[3] = m, l[4] = a) : a = l[4], l[5] !== a ? (n = (0, t.jsx)("p", {
    className: "text-xs font-medium text-text-primary",
    children: a
  }), l[5] = a, l[6] = n) : n = l[6], l[7] !== r || l[8] !== n ? (s = (0, t.jsxs)("div", {
    className: "flex h-5 items-center gap-x-1 rounded-[4px] bg-bg-secondary px-1",
    children: [r, n]
  }), l[7] = r, l[8] = n, l[9] = s) : s = l[9], s;
}
lookupModule(107240);
var z = lookupModule(693124),
  F = lookupModule(705313),
  O = lookupModule(369091),
  P = lookupModule(702067);
let D = e => {
  let r,
    a,
    n,
    s,
    o,
    m,
    u,
    f,
    p,
    h,
    x,
    v = (0, i.c)(34),
    {
      username: g,
      profile_image: b,
      address: y,
      devAddress: _,
      withBackground: j
    } = e,
    N = (0, d.useRouter)(),
    {
      ipfsPrefix: w
    } = (0, O.useIpfsPrefix)();
  v[0] !== y ? (r = (0, P.f)(y?.slice(0, 6) || "anon"), v[0] = y, v[1] = r) : r = v[1];
  let k = r;
  v[2] !== y || v[3] !== N ? (a = e => {
    e.preventDefault(), e.ctrlKey || e.metaKey ? window.open((0, l.$)(y), "_blank", "noopener") : N.push((0, l.$)(y));
  }, v[2] = y, v[3] = N, v[4] = a) : a = v[4];
  let C = a;
  v[5] !== C ? (n = e => C(e), v[5] = C, v[6] = n) : n = v[6];
  let I = !g,
    S = `${y}'s profile picture`;
  v[7] !== y || v[8] !== w || v[9] !== b || v[10] !== I || v[11] !== S ? (s = (0, t.jsx)(F.f, {
    ipfsPrefix: w,
    src: b,
    address: y,
    isAnonymous: I,
    width: 16,
    height: 16,
    alt: S,
    className: "h-4 w-4"
  }), v[7] = y, v[8] = w, v[9] = b, v[10] = I, v[11] = S, v[12] = s) : s = v[12];
  let E = j && "text-black";
  v[13] !== E ? (o = (0, c.U)("flex gap-1 rounded hover:underline", E), v[13] = E, v[14] = o) : o = v[14];
  let M = j ? k : "transparent";
  return v[15] !== M ? (m = {
    backgroundColor: M
  }, v[15] = M, v[16] = m) : m = v[16], v[17] !== y || v[18] !== g ? (u = g?.slice(0, 10) || y?.slice(0, 6) || "anon", v[17] = y, v[18] = g, v[19] = u) : u = v[19], v[20] !== y || v[21] !== _ ? (f = _ && y.toLowerCase() === _.toLowerCase() && "(dev)", v[20] = y, v[21] = _, v[22] = f) : f = v[22], v[23] !== m || v[24] !== u || v[25] !== f || v[26] !== o ? (p = (0, t.jsxs)("span", {
    className: o,
    style: m,
    children: [u, " ", f]
  }), v[23] = m, v[24] = u, v[25] = f, v[26] = o, v[27] = p) : p = v[27], v[28] !== p || v[29] !== s ? (h = (0, t.jsxs)("span", {
    className: "flex items-center gap-1",
    children: [s, p]
  }), v[28] = p, v[29] = s, v[30] = h) : h = v[30], v[31] !== h || v[32] !== n ? (x = (0, t.jsx)("button", {
    type: "button",
    onClick: n,
    children: h
  }), v[31] = h, v[32] = n, v[33] = x) : x = v[33], x;
};
var L = lookupModule(529841),
  W = lookupModule(375676),
  B = lookupModule(850175),
  q = lookupModule(425890),
  U = lookupModule(235364),
  H = lookupModule(666863),
  V = lookupModule(646908),
  G = lookupModule(662093),
  K = lookupModule(790431),
  Q = lookupModule(561116),
  X = lookupModule(595673),
  Y = lookupModule(569526),
  Z = lookupModule(456753),
  J = lookupModule(538459);
let ee = (0, m.default)(() => loadModule(240916), {
    loadableGenerated: {
      modules: [920386]
    },
    ssr: !1
  }),
  et = Date.now(),
  ei = null,
  er = new Set();
function ea(e) {
  return er.add(e), null == ei && (et = Date.now(), ei = setInterval(() => {
    for (let e of (et = Date.now(), er)) e();
  }, 6e4)), () => {
    er.delete(e), 0 === er.size && null != ei && (clearInterval(ei), ei = null);
  };
}
function en() {
  return et;
}
function es() {
  return null;
}
function el(e) {
  return e.price;
}
const Card=function (e) {
  let m,
    h,
    v,
    g,
    y,
    _,
    j,
    N,
    w,
    k,
    C,
    I,
    M,
    $,
    F,
    O,
    P,
    et,
    ei,
    er,
    eo,
    ec,
    em,
    eu,
    ed,
    ef,
    ep,
    eh,
    ex,
    ev,
    eg,
    eb,
    ey,
    e_,
    ej,
    eN,
    ew,
    ek,
    eC,
    eI,
    eS,
    eE,
    eM,
    eR,
    eT = (0, i.c)(153),
    {
      activeMeta: e$,
      addToBookmark: eA,
      bookmarkedItems: ez,
      bookmarks: eF,
      coin: eO,
      impression: eP,
      isBookmarked: eD,
      onManageWatchlistClick: eL,
      removeFromBookmark: eW,
      searchTerm: eB,
      isInViewport: eq,
      shouldAnimate: eU,
      sort: eH,
      isWatchlistView: eV,
      eagerLoadImage: eG,
      priorityImage: eK
    } = e,
    eQ = void 0 !== eq && eq,
    eX = void 0 === eH ? "featured" : eH,
    eY = void 0 !== eV && eV,
    eZ = void 0 !== eG && eG,
    eJ = void 0 !== eK && eK,
    [e1, e0] = (0, f.useState)(!1),
    [e2, e3] = (0, f.useState)(!1),
    [e4, e5] = (0, f.useState)(!1),
    e6 = (0, f.useSyncExternalStore)(ea, en, es),
    e7 = null != e6 && null != eO.created_timestamp && e6 - (eO.created_timestamp < 1e10 ? 1e3 * eO.created_timestamp : eO.created_timestamp) < 36e5,
    {
      handleCoinClick: e8
    } = (0, U.f)(),
    {
      prefetch: e9,
      hoverProps: te
    } = (0, B.W)(eO),
    {
      logSeenCoins: tt
    } = (0, Z.j)(),
    {
      setLastClickImpression: ti
    } = (0, Y.y)(),
    tr = e$ || eB;
  eT[0] !== eY || eT[1] !== eX ? (m = (0, X.v5)(eX, eY), eT[0] = eY, eT[1] = eX, eT[2] = m) : m = eT[2];
  let ta = m,
    tn = (0, H.f)(eO.mint, eP, tr, ta),
    ts = (0, d.useRouter)(),
    tl = (0, q.f)();
  eT[3] !== eO.creator || eT[4] !== eQ ? (h = {
    address: eO.creator,
    enabled: eQ
  }, eT[3] = eO.creator, eT[4] = eQ, eT[5] = h) : h = eT[5];
  let {
      data: to
    } = (0, o.T)(h),
    tc = eO.created_timestamp ?? 0,
    tm = eQ && null != eO.created_timestamp && eO.created_timestamp > 0;
  eT[6] !== tm ? (v = {
    enabled: tm,
    staleTime: 3e5,
    gcTime: 6e5
  }, eT[6] = tm, eT[7] = v) : v = eT[7], eT[8] !== eO.chain_id || eT[9] !== eO.mint || eT[10] !== v || eT[11] !== tc ? (g = {
    coinAddress: eO.mint,
    coinCreatedTimestamp: tc,
    chainId: eO.chain_id,
    queryOptions: v
  }, eT[8] = eO.chain_id, eT[9] = eO.mint, eT[10] = v, eT[11] = tc, eT[12] = g) : g = eT[12];
  let {
    data: tu
  } = (0, W.f)(g);
  e: {
    let e;
    if (!tu || tu.length <= 1) {
      y = null;
      break e;
    }
    if (eT[13] !== tu) {
      let t = tu.map(el),
        i = Math.min(...t),
        r = Math.max(...t) - i || 1;
      e = t.map((e, a) => {
        let n = a / (t.length - 1) * 100;
        return `${n},${100 - (e - i) / r * 80 - 10}`;
      }).join(" L"), eT[13] = tu, eT[14] = e;
    } else e = eT[14];
    y = `M${e}`;
  }
  let td = y,
    tf = (0, n.k)(a.D.HOME_FEED_QUICK_BUY_V2);
  eT[15] !== eO || eT[16] !== tf ? (_ = tf && (0, Q.W)(eO), eT[15] = eO, eT[16] = tf, eT[17] = _) : _ = eT[17];
  let tp = _,
    th = (0, J.A)();
  eT[18] !== eO.quote_mint ? (j = (0, E.T)(eO.quote_mint), eT[18] = eO.quote_mint, eT[19] = j) : j = eT[19];
  let tx = j,
    tv = "pump" === (0, K.d)({
      program: eO.program,
      raydium_pool: eO.raydium_pool
    }) || "unsupported" === tx ? null : tx,
    tg = (0, f.useRef)(!1);
  eT[20] !== th ? (N = () => () => {
    tg.current && th(null);
  }, w = [th], eT[20] = th, eT[21] = N, eT[22] = w) : (N = eT[21], w = eT[22]), (0, f.useEffect)(N, w), eT[23] !== eO ? (k = {
    mint: eO.mint,
    chainId: eO.chain_id,
    fallbackMarketCap: eO.usd_market_cap,
    coin: eO
  }, eT[23] = eO, eT[24] = k) : k = eT[24];
  let tb = (0, G.h)(k),
    ty = tb ?? 0;
  eT[25] !== eO || eT[26] !== tb ? (C = void 0 === tb && ((0, V.e)(eO) || (0, V.X)(eO) || (0, V.a)(eO)), eT[25] = eO, eT[26] = tb, eT[27] = C) : C = eT[27];
  let t_ = C;
  eT[28] !== eO.mint || eT[29] !== tr || eT[30] !== e8 || eT[31] !== eP || eT[32] !== tt || eT[33] !== ti ? (I = async function () {
    eP && (ti(eO.mint, eP, tr), await e8(eO.mint, eP, tr), await tt());
  }, eT[28] = eO.mint, eT[29] = tr, eT[30] = e8, eT[31] = eP, eT[32] = tt, eT[33] = ti, eT[34] = I) : I = eT[34];
  let tj = I,
    tN = "active" === eO.mayhem_state,
    tw = eO.is_currently_live,
    tk = !tw && tN,
    tC = !!eO.is_charity;
  eT[35] !== tp || eT[36] !== tv || eT[37] !== th ? (M = tp ? () => {
    tg.current = !0, e5(!0), th(tv);
  } : void 0, eT[35] = tp, eT[36] = tv, eT[37] = th, eT[38] = M) : M = eT[38], eT[39] !== tp || eT[40] !== th ? ($ = tp ? () => {
    tg.current = !1, e5(!1), th(null);
  } : void 0, eT[39] = tp, eT[40] = th, eT[41] = $) : $ = eT[41];
  let tI = `/coin/${eO.mint}`,
    tS = void 0 !== eU && eU && "animate-coin-pulse";
  eT[42] !== tS ? (F = (0, c.U)("relative aspect-square w-full overflow-hidden rounded-lg bg-bg-secondary", tS), eT[42] = tS, eT[43] = F) : F = eT[43], eT[44] !== eO || eT[45] !== eZ || eT[46] !== eJ ? (O = (0, t.jsx)("div", {
    className: "flex size-full items-center justify-center",
    children: (0, t.jsx)(b, {
      coin: eO,
      eager: eZ,
      priority: eJ
    })
  }), eT[44] = eO, eT[45] = eZ, eT[46] = eJ, eT[47] = O) : O = eT[47], eT[48] !== tw ? (P = tw && (0, t.jsx)("div", {
    className: "pointer-events-none absolute inset-0 rounded-lg bg-bg-accent p-0.5",
    style: {
      WebkitMask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
      WebkitMaskComposite: "xor",
      mask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
      maskComposite: "exclude"
    }
  }), eT[48] = tw, eT[49] = P) : P = eT[49], eT[50] !== tk ? (et = tk && (0, t.jsx)("div", {
    className: "pointer-events-none absolute inset-0 rounded-lg bg-gradient-to-b from-green-300 to-red-500 p-0.5",
    style: {
      WebkitMask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
      WebkitMaskComposite: "xor",
      mask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
      maskComposite: "exclude"
    }
  }), eT[50] = tk, eT[51] = et) : et = eT[51], eT[52] !== tw ? (ei = tw && (0, t.jsx)("div", {
    className: "absolute right-2 top-2 flex items-center gap-x-1",
    children: (0, t.jsx)(T, {})
  }), eT[52] = tw, eT[53] = ei) : ei = eT[53], eT[54] !== eO.mayhem_is_multiplayer || eT[55] !== tk ? (er = tk && (0, t.jsx)("div", {
    className: "absolute right-2 top-2 flex items-center gap-x-1",
    children: (0, t.jsx)(A, {
      multiplayer: !0 === eO.mayhem_is_multiplayer
    })
  }), eT[54] = eO.mayhem_is_multiplayer, eT[55] = tk, eT[56] = er) : er = eT[56], eT[57] !== tC ? (eo = tC && (0, t.jsx)("div", {
    className: "absolute left-2 top-2 flex items-center gap-x-1",
    children: (0, t.jsx)(R, {})
  }), eT[57] = tC, eT[58] = eo) : eo = eT[58], eT[59] === Symbol.for("react.memo_cache_sentinel") ? (ec = (0, t.jsx)("div", {
    className: "pointer-events-none absolute inset-x-0 bottom-0 h-[35%] bg-gradient-to-t from-black/25 to-transparent transition-all duration-300 ease-out [@media(hover:hover)]:group-hover:h-[55%] [@media(hover:hover)]:group-hover:from-black/70"
  }), eT[59] = ec) : ec = eT[59], eT[60] !== eO.mint || eT[61] !== td ? (em = td && (0, t.jsx)("div", {
    className: "pointer-events-none absolute bottom-2 right-2 h-[25%] w-1/2 transition-all duration-300 ease-out [@media(hover:hover)]:group-hover:h-[45%] [@media(hover:hover)]:group-hover:w-[calc(100%-16px)]",
    children: (0, t.jsxs)("svg", {
      className: "size-full",
      viewBox: "0 0 100 100",
      preserveAspectRatio: "none",
      children: [(0, t.jsx)("defs", {
        children: (0, t.jsxs)("filter", {
          id: `glow-${eO.mint}`,
          children: [(0, t.jsx)("feGaussianBlur", {
            stdDeviation: "5",
            result: "blur"
          }), (0, t.jsxs)("feMerge", {
            children: [(0, t.jsx)("feMergeNode", {
              in: "blur"
            }), (0, t.jsx)("feMergeNode", {
              in: "SourceGraphic"
            })]
          })]
        })
      }), (0, t.jsx)("path", {
        d: td,
        fill: "none",
        stroke: "#86EFAC",
        strokeWidth: "4",
        strokeOpacity: "0.2",
        vectorEffect: "non-scaling-stroke",
        filter: `url(#glow-${eO.mint})`
      }), (0, t.jsx)("path", {
        d: td,
        fill: "none",
        stroke: "#86EFAC",
        strokeWidth: "1.5",
        vectorEffect: "non-scaling-stroke"
      })]
    })
  }), eT[60] = eO.mint, eT[61] = td, eT[62] = em) : em = eT[62], eT[63] !== eO || eT[64] !== eP?.itemPosition || eT[65] !== eP?.rec_id || eT[66] !== eP?.sourceElement || eT[67] !== eP?.sourceScreen || eT[68] !== e4 || eT[69] !== eQ || eT[70] !== e2 || eT[71] !== tp || eT[72] !== ta ? (eu = (eQ || e4 || e2) && tp && (0, t.jsx)("div", {
    className: "absolute bottom-3 right-3 z-10 hidden justify-end transition duration-200 ease-out [@media(hover:hover)]:pointer-events-none [@media(hover:hover)]:flex [@media(hover:hover)]:translate-y-1 [@media(hover:hover)]:opacity-0 [@media(hover:hover)]:group-hover:pointer-events-auto [@media(hover:hover)]:group-hover:translate-y-0 [@media(hover:hover)]:group-hover:opacity-100",
    children: (0, t.jsx)(ee, {
      coin: eO,
      onActiveChange: e3,
      sourceScreen: eP?.sourceScreen,
      sourceElement: eP?.sourceElement ?? ta,
      absolutePosition: eP?.itemPosition,
      recommendationId: eP?.rec_id
    })
  }), eT[63] = eO, eT[64] = eP?.itemPosition, eT[65] = eP?.rec_id, eT[66] = eP?.sourceElement, eT[67] = eP?.sourceScreen, eT[68] = e4, eT[69] = eQ, eT[70] = e2, eT[71] = tp, eT[72] = ta, eT[73] = eu) : eu = eT[73], eT[74] !== eO.is_currently_live || eT[75] !== tn || eT[76] !== F || eT[77] !== O || eT[78] !== P || eT[79] !== et || eT[80] !== ei || eT[81] !== er || eT[82] !== eo || eT[83] !== em || eT[84] !== eu ? (ed = (0, t.jsxs)("div", {
    className: F,
    "data-is-live": eO.is_currently_live,
    ref: tn,
    children: [O, P, et, ei, er, eo, ec, em, eu]
  }), eT[74] = eO.is_currently_live, eT[75] = tn, eT[76] = F, eT[77] = O, eT[78] = P, eT[79] = et, eT[80] = ei, eT[81] = er, eT[82] = eo, eT[83] = em, eT[84] = eu, eT[85] = ed) : ed = eT[85], eT[86] !== eO.name ? (ef = (0, t.jsx)("p", {
    className: "min-w-0 truncate text-base font-semibold leading-snug text-text-primary",
    children: eO.name
  }), eT[86] = eO.name, eT[87] = ef) : ef = eT[87];
  let tE = "string" == typeof eO.chain_id ? eO.chain_id : null;
  eT[88] !== eO.mint || eT[89] !== tE ? (ep = (0, t.jsx)(p.f, {
    mint: eO.mint,
    chainId: tE
  }), eT[88] = eO.mint, eT[89] = tE, eT[90] = ep) : ep = eT[90], eT[91] !== ef || eT[92] !== ep ? (eh = (0, t.jsxs)("div", {
    className: "flex min-w-0 items-center gap-1",
    children: [ef, ep]
  }), eT[91] = ef, eT[92] = ep, eT[93] = eh) : eh = eT[93];
  let tM = eO.symbol ? `$${eO.symbol}` : null;
  eT[94] !== tM ? (ex = (0, t.jsx)("p", {
    className: "mt-0.5 truncate text-sm font-normal leading-snug text-text-tertiary",
    children: tM
  }), eT[94] = tM, eT[95] = ex) : ex = eT[95], eT[96] !== ty || eT[97] !== t_ ? (ev = t_ ? (0, t.jsx)("span", {
    className: "font-semibold text-bg-accent",
    children: "—"
  }) : (0, t.jsx)(x, {
    className: "font-semibold text-bg-accent",
    value: ty
  }), eT[96] = ty, eT[97] = t_, eT[98] = ev) : ev = eT[98], eT[99] === Symbol.for("react.memo_cache_sentinel") ? (eg = (0, t.jsx)("span", {
    className: "text-sm text-text-tertiary",
    children: "MC"
  }), eT[99] = eg) : eg = eT[99], eT[100] !== ev ? (eb = (0, t.jsxs)("div", {
    className: "mt-1.5 flex items-baseline gap-1 text-base leading-normal",
    children: [ev, eg]
  }), eT[100] = ev, eT[101] = eb) : eb = eT[101], eT[102] !== eO.creator || eT[103] !== eO.profile_image || eT[104] !== eO.username || eT[105] !== to?.profile_image || eT[106] !== to?.username || eT[107] !== ts || eT[108] !== tl ? (ey = eO.creator && (tl ? (0, t.jsx)(z.S, {
    address: eO.creator,
    username: to?.username ?? eO.username,
    profileImage: to?.profile_image ?? eO.profile_image,
    size: "xs",
    nameClassName: "font-normal text-text-tertiary",
    link: !1,
    onClick: e => {
      e.preventDefault();
      let t = (0, l.$)(eO.creator);
      e.ctrlKey || e.metaKey ? window.open(t, "_blank", "noopener") : ts.push(t);
    }
  }) : (0, t.jsx)(D, {
    address: eO.creator,
    profile_image: to?.profile_image ?? eO.profile_image,
    username: to?.username ?? eO.username,
    withBackground: !1
  })), eT[102] = eO.creator, eT[103] = eO.profile_image, eT[104] = eO.username, eT[105] = to?.profile_image, eT[106] = to?.username, eT[107] = ts, eT[108] = tl, eT[109] = ey) : ey = eT[109], eT[110] !== ey ? (e_ = (0, t.jsx)("div", {
    className: "flex items-center text-sm font-normal leading-none text-text-tertiary",
    children: ey
  }), eT[110] = ey, eT[111] = e_) : e_ = eT[111];
  let tR = e7 ? tl ? "text-gain" : "text-green-400" : "text-text-tertiary";
  return eT[112] !== tR ? (ej = (0, c.U)("flex items-center gap-0.5 text-sm font-normal leading-none", tR), eT[112] = tR, eT[113] = ej) : ej = eT[113], eT[114] === Symbol.for("react.memo_cache_sentinel") ? (eN = (0, t.jsx)(r.i$, {
    size: 14
  }), eT[114] = eN) : eN = eT[114], eT[115] !== eO.created_timestamp || eT[116] !== tl ? (ew = eO.created_timestamp ? tl ? (0, t.jsx)(L.f, {
    timestamp: eO.created_timestamp,
    suffix: !1
  }) : (0, s.C)(eO.created_timestamp, {
    removeAgo: !0
  }) : "—", eT[115] = eO.created_timestamp, eT[116] = tl, eT[117] = ew) : ew = eT[117], eT[118] !== ej || eT[119] !== ew ? (ek = (0, t.jsxs)("span", {
    className: ej,
    suppressHydrationWarning: !0,
    children: [eN, ew]
  }), eT[118] = ej, eT[119] = ew, eT[120] = ek) : ek = eT[120], eT[121] !== e_ || eT[122] !== ek ? (eC = (0, t.jsxs)("div", {
    className: "mt-2 flex items-center gap-2",
    children: [e_, ek]
  }), eT[121] = e_, eT[122] = ek, eT[123] = eC) : eC = eT[123], eT[124] !== eO.description ? (eI = eO.description && (0, t.jsx)("p", {
    className: "mt-1.5 line-clamp-2 w-full break-words text-sm font-normal leading-normal text-text-tertiary",
    children: eO.description
  }), eT[124] = eO.description, eT[125] = eI) : eI = eT[125], eT[126] !== eh || eT[127] !== ex || eT[128] !== eb || eT[129] !== eC || eT[130] !== eI ? (eS = (0, t.jsxs)("div", {
    className: "mt-2 flex min-w-0 flex-col",
    children: [eh, ex, eb, eC, eI]
  }), eT[126] = eh, eT[127] = ex, eT[128] = eb, eT[129] = eC, eT[130] = eI, eT[131] = eS) : eS = eT[131], eT[132] !== te || eT[133] !== tj || eT[134] !== e9 || eT[135] !== tI || eT[136] !== ed || eT[137] !== eS ? (eE = (0, t.jsxs)(u.default, {
    className: "group flex transform-gpu flex-col",
    href: tI,
    prefetch: e9,
    onClick: tj,
    ...te,
    children: [ed, eS]
  }), eT[132] = te, eT[133] = tj, eT[134] = e9, eT[135] = tI, eT[136] = ed, eT[137] = eS, eT[138] = eE) : eE = eT[138], eT[139] !== eA || eT[140] !== ez || eT[141] !== eF || eT[142] !== eO || eT[143] !== eD || eT[144] !== e1 || eT[145] !== eL || eT[146] !== eW ? (eM = (0, t.jsx)("div", {
    className: "absolute right-1 top-1 flex items-center gap-1",
    children: (0, t.jsx)(S, {
      addToBookmark: eA,
      bookmarkedItems: ez,
      bookmarks: eF,
      coin: eO,
      isBookmarked: eD,
      isOpen: e1,
      onManageWatchlistClick: eL,
      removeFromBookmark: eW,
      setOpen: e0
    })
  }), eT[139] = eA, eT[140] = ez, eT[141] = eF, eT[142] = eO, eT[143] = eD, eT[144] = e1, eT[145] = eL, eT[146] = eW, eT[147] = eM) : eM = eT[147], eT[148] !== M || eT[149] !== $ || eT[150] !== eE || eT[151] !== eM ? (eR = (0, t.jsxs)("div", {
    className: "group relative border border-solid border-transparent transition-transform duration-150 [@media(hover:hover)]:hover:scale-[1.025]",
    onMouseEnter: M,
    onMouseLeave: $,
    children: [eE, eM]
  }), eT[148] = M, eT[149] = $, eT[150] = eE, eT[151] = eM, eT[152] = eR) : eR = eT[152], eR;
};
return Object.freeze({Card,MarketCap:x,Media:b,BookmarkControl:S,CharityBadge:R,LiveBadge:T,MayhemBadge:A,Creator:D,subscribeClock:ea,clockSnapshot:en,clockServerSnapshot:es});
}

function context1(lookupModule,loadModule,host){
const {window,Date,setTimeout,setInterval,clearInterval}=host;
var t = lookupModule(732486),
  r = lookupModule(445242),
  a = lookupModule(157633),
  i = lookupModule(322315),
  n = lookupModule(254010),
  l = lookupModule(584582),
  s = lookupModule(146695),
  o = lookupModule(782067),
  c = lookupModule(7284),
  d = lookupModule(453706),
  m = lookupModule(458310),
  u = lookupModule(599077),
  f = lookupModule(352386),
  h = lookupModule(667876),
  p = lookupModule(938277);
function x(e) {
  let a,
    i,
    n,
    l,
    s,
    o,
    c,
    d,
    m = (0, r.c)(18);
  m[0] !== e ? ({
    value: i,
    className: n,
    transition: l,
    ...a
  } = e, m[0] = e, m[1] = a, m[2] = i, m[3] = n, m[4] = l) : (a = m[1], i = m[2], n = m[3], l = m[4]);
  let u = void 0 === i ? 0 : i,
    h = void 0 === n ? "" : n,
    [x, g] = (0, f.useState)(u),
    [b, v] = (0, f.useState)(!1);
  if (x !== u) {
    let e = Math.abs((u - x) / x) >= .01;
    g(u), v(e);
  }
  let y = l?.duration != null ? 1e3 * l.duration : void 0,
    j = `inline-block rounded-sm transform-gpu text-foreground ${b ? "animate-market-cap-flash will-change-[background-color]" : ""} ${h}`;
  return m[5] !== j ? (s = j.trim(), m[5] = j, m[6] = s) : s = m[6], m[7] !== y || m[8] !== b ? (o = b && null != y ? {
    animationDuration: `${y}ms`
  } : void 0, m[7] = y, m[8] = b, m[9] = o) : o = m[9], m[10] !== u ? (c = (0, p.M)(u), m[10] = u, m[11] = c) : c = m[11], m[12] !== a || m[13] !== s || m[14] !== o || m[15] !== c || m[16] !== u ? (d = (0, t.jsxs)("div", {
    className: s,
    style: o,
    ...a,
    children: ["$", c]
  }, u), m[12] = a, m[13] = s, m[14] = o, m[15] = c, m[16] = u, m[17] = d) : d = m[17], d;
}
var g = lookupModule(713380),
  b = lookupModule(644350);
function v(e) {
  let a,
    i,
    n,
    l = (0, r.c)(14),
    {
      coin: s,
      eager: o,
      priority: c
    } = e;
  return l[0] !== s || l[1] !== o || l[2] !== c ? (a = (0, t.jsx)(b.f, {
    coin: s,
    width: 600,
    height: 600,
    eager: o,
    priority: c
  }), l[0] = s, l[1] = o, l[2] = c, l[3] = a) : a = l[3], l[4] !== s.board_program || l[5] !== s.chain_id || l[6] !== s.mint || l[7] !== s.platform || l[8] !== s.program || l[9] !== s.protocol ? (i = (0, t.jsx)(g.f, {
    mint: s.mint,
    chainId: s.chain_id,
    program: s.program,
    platform: s.platform,
    protocol: s.protocol,
    boardProgram: s.board_program,
    seal: !1,
    size: 20,
    chainSize: 20,
    venueSize: 20,
    className: "absolute bottom-1 right-1"
  }), l[4] = s.board_program, l[5] = s.chain_id, l[6] = s.mint, l[7] = s.platform, l[8] = s.program, l[9] = s.protocol, l[10] = i) : i = l[10], l[11] !== a || l[12] !== i ? (n = (0, t.jsxs)("span", {
    className: "relative block size-full",
    children: [a, i]
  }), l[11] = a, l[12] = i, l[13] = n) : n = l[13], n;
}
var y = lookupModule(670169),
  j = lookupModule(574472),
  w = lookupModule(56267),
  N = lookupModule(66732),
  _ = lookupModule(887827),
  k = lookupModule(960107),
  S = lookupModule(170450),
  C = lookupModule(300157);
function M(e) {
  let a,
    i,
    n,
    l,
    s,
    o,
    d,
    m,
    u,
    h,
    p,
    x = (0, r.c)(34),
    {
      addToBookmark: g,
      bookmarkedItems: b,
      bookmarks: v,
      coin: M,
      isBookmarked: E,
      isOpen: A,
      onManageWatchlistClick: R,
      removeFromBookmark: D,
      setOpen: z
    } = e,
    {
      decodedJwt: T
    } = (0, j.F)(),
    P = (0, S.f)() && !!T?.address,
    [B, I] = (0, f.useState)(!1);
  x[0] !== M.chain_id || x[1] !== M.mint ? (a = (0, C.y)({
    mint: M.mint,
    chainId: M.chain_id
  }), x[0] = M.chain_id, x[1] = M.mint, x[2] = a) : a = x[2];
  let F = a;
  x[3] !== g || x[4] !== F || x[5] !== v || x[6] !== D ? (i = function (e) {
    let t = v?.find(t => t.id === e)?.bookmark_items;
    (0, k.w)(t, F) && D && e ? D((0, k.T)(t, F), e) : g && (I(!0), g(F, e), setTimeout(() => I(!1), 600));
  }, x[3] = g, x[4] = F, x[5] = v, x[6] = D, x[7] = i) : i = x[7];
  let L = i;
  if (!P) return null;
  x[8] !== z ? (n = e => z(e), x[8] = z, x[9] = n) : n = x[9];
  let H = A ? "flex" : void 0;
  return x[10] !== H ? (l = {
    display: H
  }, x[10] = H, x[11] = l) : l = x[11], x[12] !== E || x[13] !== B ? (s = E ? (0, t.jsx)(w.j, {
    className: (0, c.U)("text-green-300", B && "animate-watchlist-star-sparkle"),
    style: {
      fill: "#86efac"
    }
  }) : (0, t.jsx)(w.j, {
    className: (0, c.U)("text-text-tertiary hover:stroke-green-400", B && "animate-watchlist-star-sparkle")
  }), x[12] = E, x[13] = B, x[14] = s) : s = x[14], x[15] !== l || x[16] !== s ? (o = (0, t.jsx)(N.J, {
    className: "flex size-6 cursor-pointer items-center justify-center [@media(hover:hover)]:hidden [@media(hover:hover)]:group-hover:flex",
    style: l,
    children: s
  }), x[15] = l, x[16] = s, x[17] = o) : o = x[17], x[18] === Symbol.for("react.memo_cache_sentinel") ? (d = (0, t.jsx)(y.r, {
    className: "pointer-events-none absolute right-0 top-0 size-6"
  }), x[18] = d) : d = x[18], x[19] !== o ? (m = (0, t.jsxs)("div", {
    className: "relative",
    children: [o, d]
  }), x[19] = o, x[20] = m) : m = x[20], x[21] !== F || x[22] !== b || x[23] !== v || x[24] !== L || x[25] !== R ? (u = v && b && R ? (0, t.jsx)(_.f, {
    bookmarkedItems: b,
    bookmarks: v,
    mint: F,
    onBookmarkClick: L,
    onManageClick: R
  }) : null, x[21] = F, x[22] = b, x[23] = v, x[24] = L, x[25] = R, x[26] = u) : u = x[26], x[27] !== u ? (h = (0, t.jsx)(N.T, {
    align: "end",
    className: "w-48 border-border-tertiary bg-bg-tertiary p-0",
    children: u
  }), x[27] = u, x[28] = h) : h = x[28], x[29] !== A || x[30] !== h || x[31] !== n || x[32] !== m ? (p = (0, t.jsxs)(N.V, {
    onOpenChange: n,
    open: A,
    children: [m, h]
  }), x[29] = A, x[30] = h, x[31] = n, x[32] = m, x[33] = p) : p = x[33], p;
}
var E = lookupModule(642357);
lookupModule(12692);
var A = lookupModule(398902);
function R() {
  let e,
    i,
    n,
    l = (0, r.c)(5),
    {
      t: s
    } = (0, A.f)();
  return l[0] === Symbol.for("react.memo_cache_sentinel") ? (e = (0, t.jsx)(a.cJ, {
    className: "text-pink-500 drop-shadow-[0_1px_4px_rgba(236,72,153,0.55)]",
    size: 14
  }), l[0] = e) : e = l[0], l[1] !== s ? (i = s("creator_fees.charity.label"), l[1] = s, l[2] = i) : i = l[2], l[3] !== i ? (n = (0, t.jsxs)("div", {
    className: "flex h-5 w-fit shrink-0 items-center justify-center gap-x-1 rounded-[90px] border border-solid border-pink-500/40 bg-black/80 px-1.5",
    children: [e, (0, t.jsx)("p", {
      className: "text-xs font-medium text-pink-500",
      children: i
    })]
  }), l[3] = i, l[4] = n) : n = l[4], n;
}
function D() {
  let e,
    i,
    n,
    l = (0, r.c)(5),
    {
      t: s
    } = (0, A.f)();
  return l[0] === Symbol.for("react.memo_cache_sentinel") ? (e = (0, t.jsx)(a.s4, {
    className: "text-text-on-accent",
    size: 14
  }), l[0] = e) : e = l[0], l[1] !== s ? (i = s("web.nav.live"), l[1] = s, l[2] = i) : i = l[2], l[3] !== i ? (n = (0, t.jsxs)("div", {
    className: "flex rounded-[4px] bg-bg-accent px-1 items-center h-5 gap-x-1",
    children: [e, (0, t.jsx)("p", {
      className: "text-xs text-text-on-accent uppercase font-medium",
      children: i
    })]
  }), l[3] = i, l[4] = n) : n = l[4], n;
}
var z = lookupModule(745018);
function T(e) {
  let a,
    i,
    n,
    l,
    s = (0, r.c)(10),
    {
      multiplayer: o
    } = e,
    c = void 0 !== o && o,
    {
      t: d
    } = (0, A.f)();
  return s[0] !== c ? (a = c ? (0, t.jsx)(z.xI, {
    className: "text-text-accent",
    size: 14
  }) : (0, t.jsx)(z.Sg, {
    className: "text-text-accent",
    size: 14
  }), s[0] = c, s[1] = a) : a = s[1], s[2] !== c || s[3] !== d ? (i = d(c ? "web.mayhem.mode_multiplayer" : "web.nav.mayhem"), s[2] = c, s[3] = d, s[4] = i) : i = s[4], s[5] !== i ? (n = (0, t.jsx)("p", {
    className: "text-xs font-medium text-text-primary",
    children: i
  }), s[5] = i, s[6] = n) : n = s[6], s[7] !== a || s[8] !== n ? (l = (0, t.jsxs)("div", {
    className: "flex h-5 items-center gap-x-1 rounded-[4px] bg-bg-secondary px-1",
    children: [a, n]
  }), s[7] = a, s[8] = n, s[9] = l) : l = s[9], l;
}
lookupModule(107240);
var P = lookupModule(693124),
  B = lookupModule(705313),
  I = lookupModule(369091),
  F = lookupModule(702067);
let L = e => {
  let a,
    i,
    n,
    l,
    o,
    d,
    m,
    f,
    h,
    p,
    x,
    g = (0, r.c)(34),
    {
      username: b,
      profile_image: v,
      address: y,
      devAddress: j,
      withBackground: w
    } = e,
    N = (0, u.useRouter)(),
    {
      ipfsPrefix: _
    } = (0, I.useIpfsPrefix)();
  g[0] !== y ? (a = (0, F.f)(y?.slice(0, 6) || "anon"), g[0] = y, g[1] = a) : a = g[1];
  let k = a;
  g[2] !== y || g[3] !== N ? (i = e => {
    e.preventDefault(), e.ctrlKey || e.metaKey ? window.open((0, s.$)(y), "_blank", "noopener") : N.push((0, s.$)(y));
  }, g[2] = y, g[3] = N, g[4] = i) : i = g[4];
  let S = i;
  g[5] !== S ? (n = e => S(e), g[5] = S, g[6] = n) : n = g[6];
  let C = !b,
    M = `${y}'s profile picture`;
  g[7] !== y || g[8] !== _ || g[9] !== v || g[10] !== C || g[11] !== M ? (l = (0, t.jsx)(B.f, {
    ipfsPrefix: _,
    src: v,
    address: y,
    isAnonymous: C,
    width: 16,
    height: 16,
    alt: M,
    className: "h-4 w-4"
  }), g[7] = y, g[8] = _, g[9] = v, g[10] = C, g[11] = M, g[12] = l) : l = g[12];
  let E = w && "text-black";
  g[13] !== E ? (o = (0, c.U)("flex gap-1 rounded hover:underline", E), g[13] = E, g[14] = o) : o = g[14];
  let A = w ? k : "transparent";
  return g[15] !== A ? (d = {
    backgroundColor: A
  }, g[15] = A, g[16] = d) : d = g[16], g[17] !== y || g[18] !== b ? (m = b?.slice(0, 10) || y?.slice(0, 6) || "anon", g[17] = y, g[18] = b, g[19] = m) : m = g[19], g[20] !== y || g[21] !== j ? (f = j && y.toLowerCase() === j.toLowerCase() && "(dev)", g[20] = y, g[21] = j, g[22] = f) : f = g[22], g[23] !== d || g[24] !== m || g[25] !== f || g[26] !== o ? (h = (0, t.jsxs)("span", {
    className: o,
    style: d,
    children: [m, " ", f]
  }), g[23] = d, g[24] = m, g[25] = f, g[26] = o, g[27] = h) : h = g[27], g[28] !== h || g[29] !== l ? (p = (0, t.jsxs)("span", {
    className: "flex items-center gap-1",
    children: [l, h]
  }), g[28] = h, g[29] = l, g[30] = p) : p = g[30], g[31] !== p || g[32] !== n ? (x = (0, t.jsx)("button", {
    type: "button",
    onClick: n,
    children: p
  }), g[31] = p, g[32] = n, g[33] = x) : x = g[33], x;
};
var H = lookupModule(529841),
  K = lookupModule(375676),
  q = lookupModule(850175),
  U = lookupModule(425890),
  W = lookupModule(235364),
  V = lookupModule(666863),
  $ = lookupModule(646908),
  Y = lookupModule(662093),
  O = lookupModule(790431),
  Q = lookupModule(561116),
  G = lookupModule(595673),
  X = lookupModule(569526),
  J = lookupModule(456753),
  Z = lookupModule(538459);
let ee = (0, d.default)(() => loadModule(240916), {
    loadableGenerated: {
      modules: [920386]
    },
    ssr: !1
  }),
  et = Date.now(),
  er = null,
  ea = new Set();
function ei(e) {
  return ea.add(e), null == er && (et = Date.now(), er = setInterval(() => {
    for (let e of (et = Date.now(), ea)) e();
  }, 6e4)), () => {
    ea.delete(e), 0 === ea.size && null != er && (clearInterval(er), er = null);
  };
}
function en() {
  return et;
}
function el() {
  return null;
}
function es(e) {
  return e.price;
}
const Card=function (e) {
  let d,
    p,
    g,
    b,
    y,
    j,
    w,
    N,
    _,
    k,
    S,
    C,
    A,
    z,
    B,
    I,
    F,
    et,
    er,
    ea,
    eo,
    ec,
    ed,
    em,
    eu,
    ef,
    eh,
    ep,
    ex,
    eg,
    eb,
    ev,
    ey,
    ej,
    ew,
    eN,
    e_,
    ek,
    eS,
    eC,
    eM,
    eE,
    eA,
    eR,
    eD = (0, r.c)(153),
    {
      activeMeta: ez,
      addToBookmark: eT,
      bookmarkedItems: eP,
      bookmarks: eB,
      coin: eI,
      impression: eF,
      isBookmarked: eL,
      onManageWatchlistClick: eH,
      removeFromBookmark: eK,
      searchTerm: eq,
      isInViewport: eU,
      shouldAnimate: eW,
      sort: eV,
      isWatchlistView: e$,
      eagerLoadImage: eY,
      priorityImage: eO
    } = e,
    eQ = void 0 !== eU && eU,
    eG = void 0 === eV ? "featured" : eV,
    eX = void 0 !== e$ && e$,
    eJ = void 0 !== eY && eY,
    eZ = void 0 !== eO && eO,
    [e0, e1] = (0, f.useState)(!1),
    [e2, e3] = (0, f.useState)(!1),
    [e4, e5] = (0, f.useState)(!1),
    e6 = (0, f.useSyncExternalStore)(ei, en, el),
    e7 = null != e6 && null != eI.created_timestamp && e6 - (eI.created_timestamp < 1e10 ? 1e3 * eI.created_timestamp : eI.created_timestamp) < 36e5,
    {
      handleCoinClick: e8
    } = (0, W.f)(),
    {
      prefetch: e9,
      hoverProps: te
    } = (0, q.W)(eI),
    {
      logSeenCoins: tt
    } = (0, J.j)(),
    {
      setLastClickImpression: tr
    } = (0, X.y)(),
    ta = ez || eq;
  eD[0] !== eX || eD[1] !== eG ? (d = (0, G.v5)(eG, eX), eD[0] = eX, eD[1] = eG, eD[2] = d) : d = eD[2];
  let ti = d,
    tn = (0, V.f)(eI.mint, eF, ta, ti),
    tl = (0, u.useRouter)(),
    ts = (0, U.f)();
  eD[3] !== eI.creator || eD[4] !== eQ ? (p = {
    address: eI.creator,
    enabled: eQ
  }, eD[3] = eI.creator, eD[4] = eQ, eD[5] = p) : p = eD[5];
  let {
      data: to
    } = (0, o.T)(p),
    tc = eI.created_timestamp ?? 0,
    td = eQ && null != eI.created_timestamp && eI.created_timestamp > 0;
  eD[6] !== td ? (g = {
    enabled: td,
    staleTime: 3e5,
    gcTime: 6e5
  }, eD[6] = td, eD[7] = g) : g = eD[7], eD[8] !== eI.chain_id || eD[9] !== eI.mint || eD[10] !== g || eD[11] !== tc ? (b = {
    coinAddress: eI.mint,
    coinCreatedTimestamp: tc,
    chainId: eI.chain_id,
    queryOptions: g
  }, eD[8] = eI.chain_id, eD[9] = eI.mint, eD[10] = g, eD[11] = tc, eD[12] = b) : b = eD[12];
  let {
    data: tm
  } = (0, K.f)(b);
  e: {
    let e;
    if (!tm || tm.length <= 1) {
      y = null;
      break e;
    }
    if (eD[13] !== tm) {
      let t = tm.map(es),
        r = Math.min(...t),
        a = Math.max(...t) - r || 1;
      e = t.map((e, i) => {
        let n = i / (t.length - 1) * 100;
        return `${n},${100 - (e - r) / a * 80 - 10}`;
      }).join(" L"), eD[13] = tm, eD[14] = e;
    } else e = eD[14];
    y = `M${e}`;
  }
  let tu = y,
    tf = (0, n.k)(i.D.HOME_FEED_QUICK_BUY_V2);
  eD[15] !== eI || eD[16] !== tf ? (j = tf && (0, Q.W)(eI), eD[15] = eI, eD[16] = tf, eD[17] = j) : j = eD[17];
  let th = j,
    tp = (0, Z.A)();
  eD[18] !== eI.quote_mint ? (w = (0, E.T)(eI.quote_mint), eD[18] = eI.quote_mint, eD[19] = w) : w = eD[19];
  let tx = w,
    tg = "pump" === (0, O.d)({
      program: eI.program,
      raydium_pool: eI.raydium_pool
    }) || "unsupported" === tx ? null : tx,
    tb = (0, f.useRef)(!1);
  eD[20] !== tp ? (N = () => () => {
    tb.current && tp(null);
  }, _ = [tp], eD[20] = tp, eD[21] = N, eD[22] = _) : (N = eD[21], _ = eD[22]), (0, f.useEffect)(N, _), eD[23] !== eI ? (k = {
    mint: eI.mint,
    chainId: eI.chain_id,
    fallbackMarketCap: eI.usd_market_cap,
    coin: eI
  }, eD[23] = eI, eD[24] = k) : k = eD[24];
  let tv = (0, Y.h)(k),
    ty = tv ?? 0;
  eD[25] !== eI || eD[26] !== tv ? (S = void 0 === tv && ((0, $.e)(eI) || (0, $.X)(eI) || (0, $.a)(eI)), eD[25] = eI, eD[26] = tv, eD[27] = S) : S = eD[27];
  let tj = S;
  eD[28] !== eI.mint || eD[29] !== ta || eD[30] !== e8 || eD[31] !== eF || eD[32] !== tt || eD[33] !== tr ? (C = async function () {
    eF && (tr(eI.mint, eF, ta), await e8(eI.mint, eF, ta), await tt());
  }, eD[28] = eI.mint, eD[29] = ta, eD[30] = e8, eD[31] = eF, eD[32] = tt, eD[33] = tr, eD[34] = C) : C = eD[34];
  let tw = C,
    tN = "active" === eI.mayhem_state,
    t_ = eI.is_currently_live,
    tk = !t_ && tN,
    tS = !!eI.is_charity;
  eD[35] !== th || eD[36] !== tg || eD[37] !== tp ? (A = th ? () => {
    tb.current = !0, e5(!0), tp(tg);
  } : void 0, eD[35] = th, eD[36] = tg, eD[37] = tp, eD[38] = A) : A = eD[38], eD[39] !== th || eD[40] !== tp ? (z = th ? () => {
    tb.current = !1, e5(!1), tp(null);
  } : void 0, eD[39] = th, eD[40] = tp, eD[41] = z) : z = eD[41];
  let tC = `/coin/${eI.mint}`,
    tM = void 0 !== eW && eW && "animate-coin-pulse";
  eD[42] !== tM ? (B = (0, c.U)("relative aspect-square w-full overflow-hidden rounded-lg bg-bg-secondary", tM), eD[42] = tM, eD[43] = B) : B = eD[43], eD[44] !== eI || eD[45] !== eJ || eD[46] !== eZ ? (I = (0, t.jsx)("div", {
    className: "flex size-full items-center justify-center",
    children: (0, t.jsx)(v, {
      coin: eI,
      eager: eJ,
      priority: eZ
    })
  }), eD[44] = eI, eD[45] = eJ, eD[46] = eZ, eD[47] = I) : I = eD[47], eD[48] !== t_ ? (F = t_ && (0, t.jsx)("div", {
    className: "pointer-events-none absolute inset-0 rounded-lg bg-bg-accent p-0.5",
    style: {
      WebkitMask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
      WebkitMaskComposite: "xor",
      mask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
      maskComposite: "exclude"
    }
  }), eD[48] = t_, eD[49] = F) : F = eD[49], eD[50] !== tk ? (et = tk && (0, t.jsx)("div", {
    className: "pointer-events-none absolute inset-0 rounded-lg bg-gradient-to-b from-green-300 to-red-500 p-0.5",
    style: {
      WebkitMask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
      WebkitMaskComposite: "xor",
      mask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
      maskComposite: "exclude"
    }
  }), eD[50] = tk, eD[51] = et) : et = eD[51], eD[52] !== t_ ? (er = t_ && (0, t.jsx)("div", {
    className: "absolute right-2 top-2 flex items-center gap-x-1",
    children: (0, t.jsx)(D, {})
  }), eD[52] = t_, eD[53] = er) : er = eD[53], eD[54] !== eI.mayhem_is_multiplayer || eD[55] !== tk ? (ea = tk && (0, t.jsx)("div", {
    className: "absolute right-2 top-2 flex items-center gap-x-1",
    children: (0, t.jsx)(T, {
      multiplayer: !0 === eI.mayhem_is_multiplayer
    })
  }), eD[54] = eI.mayhem_is_multiplayer, eD[55] = tk, eD[56] = ea) : ea = eD[56], eD[57] !== tS ? (eo = tS && (0, t.jsx)("div", {
    className: "absolute left-2 top-2 flex items-center gap-x-1",
    children: (0, t.jsx)(R, {})
  }), eD[57] = tS, eD[58] = eo) : eo = eD[58], eD[59] === Symbol.for("react.memo_cache_sentinel") ? (ec = (0, t.jsx)("div", {
    className: "pointer-events-none absolute inset-x-0 bottom-0 h-[35%] bg-gradient-to-t from-black/25 to-transparent transition-all duration-300 ease-out [@media(hover:hover)]:group-hover:h-[55%] [@media(hover:hover)]:group-hover:from-black/70"
  }), eD[59] = ec) : ec = eD[59], eD[60] !== eI.mint || eD[61] !== tu ? (ed = tu && (0, t.jsx)("div", {
    className: "pointer-events-none absolute bottom-2 right-2 h-[25%] w-1/2 transition-all duration-300 ease-out [@media(hover:hover)]:group-hover:h-[45%] [@media(hover:hover)]:group-hover:w-[calc(100%-16px)]",
    children: (0, t.jsxs)("svg", {
      className: "size-full",
      viewBox: "0 0 100 100",
      preserveAspectRatio: "none",
      children: [(0, t.jsx)("defs", {
        children: (0, t.jsxs)("filter", {
          id: `glow-${eI.mint}`,
          children: [(0, t.jsx)("feGaussianBlur", {
            stdDeviation: "5",
            result: "blur"
          }), (0, t.jsxs)("feMerge", {
            children: [(0, t.jsx)("feMergeNode", {
              in: "blur"
            }), (0, t.jsx)("feMergeNode", {
              in: "SourceGraphic"
            })]
          })]
        })
      }), (0, t.jsx)("path", {
        d: tu,
        fill: "none",
        stroke: "#86EFAC",
        strokeWidth: "4",
        strokeOpacity: "0.2",
        vectorEffect: "non-scaling-stroke",
        filter: `url(#glow-${eI.mint})`
      }), (0, t.jsx)("path", {
        d: tu,
        fill: "none",
        stroke: "#86EFAC",
        strokeWidth: "1.5",
        vectorEffect: "non-scaling-stroke"
      })]
    })
  }), eD[60] = eI.mint, eD[61] = tu, eD[62] = ed) : ed = eD[62], eD[63] !== eI || eD[64] !== eF?.itemPosition || eD[65] !== eF?.rec_id || eD[66] !== eF?.sourceElement || eD[67] !== eF?.sourceScreen || eD[68] !== e4 || eD[69] !== eQ || eD[70] !== e2 || eD[71] !== th || eD[72] !== ti ? (em = (eQ || e4 || e2) && th && (0, t.jsx)("div", {
    className: "absolute bottom-3 right-3 z-10 hidden justify-end transition duration-200 ease-out [@media(hover:hover)]:pointer-events-none [@media(hover:hover)]:flex [@media(hover:hover)]:translate-y-1 [@media(hover:hover)]:opacity-0 [@media(hover:hover)]:group-hover:pointer-events-auto [@media(hover:hover)]:group-hover:translate-y-0 [@media(hover:hover)]:group-hover:opacity-100",
    children: (0, t.jsx)(ee, {
      coin: eI,
      onActiveChange: e3,
      sourceScreen: eF?.sourceScreen,
      sourceElement: eF?.sourceElement ?? ti,
      absolutePosition: eF?.itemPosition,
      recommendationId: eF?.rec_id
    })
  }), eD[63] = eI, eD[64] = eF?.itemPosition, eD[65] = eF?.rec_id, eD[66] = eF?.sourceElement, eD[67] = eF?.sourceScreen, eD[68] = e4, eD[69] = eQ, eD[70] = e2, eD[71] = th, eD[72] = ti, eD[73] = em) : em = eD[73], eD[74] !== eI.is_currently_live || eD[75] !== tn || eD[76] !== B || eD[77] !== I || eD[78] !== F || eD[79] !== et || eD[80] !== er || eD[81] !== ea || eD[82] !== eo || eD[83] !== ed || eD[84] !== em ? (eu = (0, t.jsxs)("div", {
    className: B,
    "data-is-live": eI.is_currently_live,
    ref: tn,
    children: [I, F, et, er, ea, eo, ec, ed, em]
  }), eD[74] = eI.is_currently_live, eD[75] = tn, eD[76] = B, eD[77] = I, eD[78] = F, eD[79] = et, eD[80] = er, eD[81] = ea, eD[82] = eo, eD[83] = ed, eD[84] = em, eD[85] = eu) : eu = eD[85], eD[86] !== eI.name ? (ef = (0, t.jsx)("p", {
    className: "min-w-0 truncate text-base font-semibold leading-snug text-text-primary",
    children: eI.name
  }), eD[86] = eI.name, eD[87] = ef) : ef = eD[87];
  let tE = "string" == typeof eI.chain_id ? eI.chain_id : null;
  eD[88] !== eI.mint || eD[89] !== tE ? (eh = (0, t.jsx)(h.f, {
    mint: eI.mint,
    chainId: tE
  }), eD[88] = eI.mint, eD[89] = tE, eD[90] = eh) : eh = eD[90], eD[91] !== ef || eD[92] !== eh ? (ep = (0, t.jsxs)("div", {
    className: "flex min-w-0 items-center gap-1",
    children: [ef, eh]
  }), eD[91] = ef, eD[92] = eh, eD[93] = ep) : ep = eD[93];
  let tA = eI.symbol ? `$${eI.symbol}` : null;
  eD[94] !== tA ? (ex = (0, t.jsx)("p", {
    className: "mt-0.5 truncate text-sm font-normal leading-snug text-text-tertiary",
    children: tA
  }), eD[94] = tA, eD[95] = ex) : ex = eD[95], eD[96] !== ty || eD[97] !== tj ? (eg = tj ? (0, t.jsx)("span", {
    className: "font-semibold text-bg-accent",
    children: "—"
  }) : (0, t.jsx)(x, {
    className: "font-semibold text-bg-accent",
    value: ty
  }), eD[96] = ty, eD[97] = tj, eD[98] = eg) : eg = eD[98], eD[99] === Symbol.for("react.memo_cache_sentinel") ? (eb = (0, t.jsx)("span", {
    className: "text-sm text-text-tertiary",
    children: "MC"
  }), eD[99] = eb) : eb = eD[99], eD[100] !== eg ? (ev = (0, t.jsxs)("div", {
    className: "mt-1.5 flex items-baseline gap-1 text-base leading-normal",
    children: [eg, eb]
  }), eD[100] = eg, eD[101] = ev) : ev = eD[101], eD[102] !== eI.creator || eD[103] !== eI.profile_image || eD[104] !== eI.username || eD[105] !== to?.profile_image || eD[106] !== to?.username || eD[107] !== tl || eD[108] !== ts ? (ey = eI.creator && (ts ? (0, t.jsx)(P.S, {
    address: eI.creator,
    username: to?.username ?? eI.username,
    profileImage: to?.profile_image ?? eI.profile_image,
    size: "xs",
    nameClassName: "font-normal text-text-tertiary",
    link: !1,
    onClick: e => {
      e.preventDefault();
      let t = (0, s.$)(eI.creator);
      e.ctrlKey || e.metaKey ? window.open(t, "_blank", "noopener") : tl.push(t);
    }
  }) : (0, t.jsx)(L, {
    address: eI.creator,
    profile_image: to?.profile_image ?? eI.profile_image,
    username: to?.username ?? eI.username,
    withBackground: !1
  })), eD[102] = eI.creator, eD[103] = eI.profile_image, eD[104] = eI.username, eD[105] = to?.profile_image, eD[106] = to?.username, eD[107] = tl, eD[108] = ts, eD[109] = ey) : ey = eD[109], eD[110] !== ey ? (ej = (0, t.jsx)("div", {
    className: "flex items-center text-sm font-normal leading-none text-text-tertiary",
    children: ey
  }), eD[110] = ey, eD[111] = ej) : ej = eD[111];
  let tR = e7 ? ts ? "text-gain" : "text-green-400" : "text-text-tertiary";
  return eD[112] !== tR ? (ew = (0, c.U)("flex items-center gap-0.5 text-sm font-normal leading-none", tR), eD[112] = tR, eD[113] = ew) : ew = eD[113], eD[114] === Symbol.for("react.memo_cache_sentinel") ? (eN = (0, t.jsx)(a.i$, {
    size: 14
  }), eD[114] = eN) : eN = eD[114], eD[115] !== eI.created_timestamp || eD[116] !== ts ? (e_ = eI.created_timestamp ? ts ? (0, t.jsx)(H.f, {
    timestamp: eI.created_timestamp,
    suffix: !1
  }) : (0, l.C)(eI.created_timestamp, {
    removeAgo: !0
  }) : "—", eD[115] = eI.created_timestamp, eD[116] = ts, eD[117] = e_) : e_ = eD[117], eD[118] !== ew || eD[119] !== e_ ? (ek = (0, t.jsxs)("span", {
    className: ew,
    suppressHydrationWarning: !0,
    children: [eN, e_]
  }), eD[118] = ew, eD[119] = e_, eD[120] = ek) : ek = eD[120], eD[121] !== ej || eD[122] !== ek ? (eS = (0, t.jsxs)("div", {
    className: "mt-2 flex items-center gap-2",
    children: [ej, ek]
  }), eD[121] = ej, eD[122] = ek, eD[123] = eS) : eS = eD[123], eD[124] !== eI.description ? (eC = eI.description && (0, t.jsx)("p", {
    className: "mt-1.5 line-clamp-2 w-full break-words text-sm font-normal leading-normal text-text-tertiary",
    children: eI.description
  }), eD[124] = eI.description, eD[125] = eC) : eC = eD[125], eD[126] !== ep || eD[127] !== ex || eD[128] !== ev || eD[129] !== eS || eD[130] !== eC ? (eM = (0, t.jsxs)("div", {
    className: "mt-2 flex min-w-0 flex-col",
    children: [ep, ex, ev, eS, eC]
  }), eD[126] = ep, eD[127] = ex, eD[128] = ev, eD[129] = eS, eD[130] = eC, eD[131] = eM) : eM = eD[131], eD[132] !== te || eD[133] !== tw || eD[134] !== e9 || eD[135] !== tC || eD[136] !== eu || eD[137] !== eM ? (eE = (0, t.jsxs)(m.default, {
    className: "group flex transform-gpu flex-col",
    href: tC,
    prefetch: e9,
    onClick: tw,
    ...te,
    children: [eu, eM]
  }), eD[132] = te, eD[133] = tw, eD[134] = e9, eD[135] = tC, eD[136] = eu, eD[137] = eM, eD[138] = eE) : eE = eD[138], eD[139] !== eT || eD[140] !== eP || eD[141] !== eB || eD[142] !== eI || eD[143] !== eL || eD[144] !== e0 || eD[145] !== eH || eD[146] !== eK ? (eA = (0, t.jsx)("div", {
    className: "absolute right-1 top-1 flex items-center gap-1",
    children: (0, t.jsx)(M, {
      addToBookmark: eT,
      bookmarkedItems: eP,
      bookmarks: eB,
      coin: eI,
      isBookmarked: eL,
      isOpen: e0,
      onManageWatchlistClick: eH,
      removeFromBookmark: eK,
      setOpen: e1
    })
  }), eD[139] = eT, eD[140] = eP, eD[141] = eB, eD[142] = eI, eD[143] = eL, eD[144] = e0, eD[145] = eH, eD[146] = eK, eD[147] = eA) : eA = eD[147], eD[148] !== A || eD[149] !== z || eD[150] !== eE || eD[151] !== eA ? (eR = (0, t.jsxs)("div", {
    className: "group relative border border-solid border-transparent transition-transform duration-150 [@media(hover:hover)]:hover:scale-[1.025]",
    onMouseEnter: A,
    onMouseLeave: z,
    children: [eE, eA]
  }), eD[148] = A, eD[149] = z, eD[150] = eE, eD[151] = eA, eD[152] = eR) : eR = eD[152], eR;
};
return Object.freeze({Card,MarketCap:x,Media:v,BookmarkControl:M,CharityBadge:R,LiveBadge:D,MayhemBadge:T,Creator:L,subscribeClock:ei,clockSnapshot:en,clockServerSnapshot:el});
}
export const CARD_CONTEXTS=Object.freeze(["bfec4df69fcd3f968311aa991fac862a02712595c4d38b60b07e74fd7f48a7a2","635d9d462036785668cd1805d8ace0515fa5d01b4744828a3193f9002af7c0dd"]);
export const MAIN_STATIC_CARD_CONTEXT="635d9d462036785668cd1805d8ace0515fa5d01b4744828a3193f9002af7c0dd";
export const REQUIRED_MODULES=Object.freeze([157633,322315,254010,584582,782067,7284,453706,458310,599077,667876,713380,644350,670169,574472,56267,66732,887827,960107,170450,300157,642357,398902,745018,693124,369091,702067,529841,375676,850175,425890,235364,666863,646908,662093,790431,561116,595673,569526,456753,538459,12692,107240]);
export function createExploreCoinCard({context,React,jsx,compiler,Avatar,formatters,modules,loadModule,host}){
if(!CARD_CONTEXTS.includes(context)||typeof React?.useSyncExternalStore!=='function'||typeof jsx?.jsx!=='function'||typeof compiler?.c!=='function'||!Avatar||typeof formatters?.M!=='function'||!(modules instanceof Map)||typeof loadModule!=='function'||!host)throw new TypeError('explicit original Card context/React/Avatar1939format/module/host capabilities required');
for(const id of REQUIRED_MODULES)if(!modules.has(id))throw new TypeError('required initialized source namespace '+id);
for(const name of ['window','Date','setTimeout','setInterval','clearInterval'])if(!Object.hasOwn(host,name))throw new TypeError('required actual host capability '+name);
const owned=new Map([[352386,React],[732486,jsx],[445242,compiler],[705313,{f:Avatar}],[938277,formatters],[146695,{$:profileRoute}]]);
const lookupModule=id=>{if(owned.has(id))return owned.get(id);if(!modules.has(id))throw new TypeError('unprovided source namespace '+id);return modules.get(id);};
return(context===CARD_CONTEXTS[0]?context0:context1)(lookupModule,loadModule,host);
}
