// Editable source-adapted main /live outer preview components.
// Regenerate/check with recover.mjs; captured factories are never evaluated.
function buildMute(imports, dom, loadPreview) {
var n = imports(732486);
var i = imports(445242);
var r = imports(352386);
var t,
  a = ((t = {}).GLOBAL = "global", t.HERO_SLIDE = "HeroSlide", t.CARD = "Card", t);
let s = (0, r.createContext)(void 0),
  l = {
    global: !0,
    HeroSlide: !0,
    Card: !0
  };
return {56999: {"k": a,
"c": function (e) {
  let t,
    a,
    o,
    c,
    d,
    u,
    m = (0, i.c)(12),
    {
      children: f
    } = e,
    [p, h] = (0, r.useState)(l);
  m[0] === Symbol.for("react.memo_cache_sentinel") ? (a = () => {
    o("global");
  }, o = e => {
    h(t => ({
      ...t,
      [e]: !t[e]
    }));
  }, t = (e, t) => {
    h(n => ({
      ...n,
      [e]: t
    }));
  }, m[0] = t, m[1] = a, m[2] = o) : (t = m[0], a = m[1], o = m[2]);
  let g = t;
  m[3] !== p ? (c = e => p[e] ?? p.global, m[3] = p, m[4] = c) : c = m[4];
  let y = c,
    x = p.global;
  return m[5] !== y || m[6] !== p || m[7] !== x ? (d = {
    muteState: p,
    isMuted: x,
    isMutedFor: y,
    setMuteFor: g,
    toggleMute: a,
    toggleMuteFor: o
  }, m[5] = y, m[6] = p, m[7] = x, m[8] = d) : d = m[8], m[9] !== f || m[10] !== d ? (u = (0, n.jsx)(s.Provider, {
    value: d,
    children: f
  }), m[9] = f, m[10] = d, m[11] = u) : u = m[11], u;
},
"F": function () {
  let e = (0, r.useContext)(s);
  if (void 0 === e) throw Error("useVideoMute must be used within a VideoMuteProvider");
  return e;
}}};
}

function buildScroll(imports, dom, loadPreview) {
const {ResizeObserver,MutationObserver} = dom;
var t = imports(445242);
var a = imports(352386);
return {798394: {"f": e => {
  let i,
    l,
    r,
    s = (0, t.c)(5),
    {
      gapPx: n
    } = e,
    c = (0, a.useRef)(null),
    o = (0, a.useRef)(null),
    [d, m] = (0, a.useState)(null);
  return s[0] !== n ? (i = () => {
    let e = c.current,
      t = o.current;
    if (!e || !t) return;
    let a = () => {
        let e = t.children[0];
        return e ? e.offsetWidth + n : null;
      },
      i = () => {
        let e = a();
        null !== e && m(e);
      },
      l = new ResizeObserver(() => {
        let e = a();
        if (!e) return;
        m(e);
        let i = Math.round(t.scrollLeft / e);
        t.scrollTo({
          left: i * e,
          behavior: "instant"
        });
      });
    l.observe(e);
    let r = new MutationObserver(i);
    return r.observe(t, {
      childList: !0
    }), i(), () => {
      l.disconnect(), r.disconnect();
    };
  }, l = [n], s[0] = n, s[1] = i, s[2] = l) : (i = s[1], l = s[2]), (0, a.useEffect)(i, l), s[3] !== d ? (r = {
    containerRef: c,
    scrollRef: o,
    cardWidth: d
  }, s[3] = d, s[4] = r) : r = s[4], r;
}},
70678: {"f": ({
  selectedIndex: e,
  scrollRef: t,
  cardWidth: i,
  skipBehavior: l,
  isSkip: r
}) => {
  let s = (0, a.useRef)(null),
    n = (0, a.useRef)(r);
  n.current = r, (0, a.useEffect)(() => {
    if (void 0 === e || null === i) return;
    let a = s.current;
    s.current = e;
    let r = null !== a && (n.current ?? ((e, t) => Math.abs(t - e) > 1))(a, e);
    t.current?.scrollTo({
      left: e * i,
      behavior: r && l ? l : "smooth"
    });
  }, [e, i, t, l]);
}},
65769: {"f": ({
  scrollRef: e,
  cardWidth: t,
  onSnapIndexChange: i
}) => {
  let l = (0, a.useRef)(i);
  l.current = i, (0, a.useEffect)(() => {
    let a = e.current;
    if (!a || null === t || !l.current) return;
    let i = () => {
      if (0 === t) return;
      let e = Math.round(a.scrollLeft / t);
      l.current?.(e);
    };
    return a.addEventListener("scrollend", i), () => {
      a.removeEventListener("scrollend", i);
    };
  }, [e, t]);
}}};
}

function buildStage(imports, dom, loadPreview) {
var t = imports(732486);
var a = imports(445242);
var i = imports(426091);
let l = "lg:mx-12 xl:mx-16",
  r = "flex snap-x snap-mandatory gap-4 overflow-x-auto scrollbar-hidden [--hero-pad:24px] lg:[--hero-pad:48px] xl:[--hero-pad:96px] 2xl:[--hero-pad:128px]",
  s = () => ({
    "--hero-card-w": "min(1200px, calc(100cqw - 2 * var(--hero-pad)))",
    paddingInline: "calc((100cqw - var(--hero-card-w)) / 2)"
  });
return {187807: {"HeroStage": e => {
  let n,
    c,
    o,
    d,
    m,
    u,
    f = (0, a.c)(14),
    {
      children: h,
      containerRef: x,
      scrollRef: p,
      overlay: v,
      className: g
    } = e;
  return f[0] !== g ? (n = (0, i.c)("relative", g), f[0] = g, f[1] = n) : n = f[1], f[2] === Symbol.for("react.memo_cache_sentinel") ? (c = (0, i.c)("@container", l), f[2] = c) : c = f[2], f[3] === Symbol.for("react.memo_cache_sentinel") ? (o = s(), f[3] = o) : o = f[3], f[4] !== h || f[5] !== p ? (d = (0, t.jsx)("div", {
    ref: p,
    className: r,
    style: o,
    children: h
  }), f[4] = h, f[5] = p, f[6] = d) : d = f[6], f[7] !== x || f[8] !== d ? (m = (0, t.jsx)("div", {
    ref: x,
    className: c,
    children: d
  }), f[7] = x, f[8] = d, f[9] = m) : m = f[9], f[10] !== v || f[11] !== n || f[12] !== m ? (u = (0, t.jsxs)("div", {
    className: n,
    children: [m, v]
  }), f[10] = v, f[11] = n, f[12] = m, f[13] = u) : u = f[13], u;
}},
829010: {"F": "w-[var(--hero-card-w)] shrink-0 snap-center",
"B": "relative flex flex-col lg:block",
"c": 16,
"s": "w-full lg:absolute lg:inset-y-0 lg:right-0 lg:w-[260px] lg:overflow-hidden xl:w-[340px]",
"h": "w-full min-w-0 lg:pr-[260px] xl:pr-[340px]",
"C": r,
"U": l,
"f": s}};
}

function buildPagination(imports, dom, loadPreview) {
var t = imports(732486);
var a = imports(445242);
var i = imports(426091);
var l = imports(398902);
var r = imports(375670);
let s = "block h-2 rounded-full transition-all duration-300";
function n(e, a) {
  return (0, t.jsx)(r.f, {
    className: (0, i.c)(s, "mx-0.5 w-2 animate-pulse")
  }, a);
}
return {218921: {"PaginationDots": e => {
  let r,
    n,
    c,
    o = (0, a.c)(10),
    {
      count: d,
      selectedIndex: m,
      onSelect: u,
      className: f
    } = e,
    {
      t: h
    } = (0, l.f)();
  return d < 2 ? null : (o[0] !== f ? (r = (0, i.c)("flex items-center justify-center gap-2", f), o[0] = f, o[1] = r) : r = o[1], o[2] !== d || o[3] !== u || o[4] !== m || o[5] !== h ? (n = Array.from({
    length: d
  }, (e, a) => {
    let l = a === m;
    return (0, t.jsx)("button", {
      type: "button",
      className: "group flex h-6 items-center px-0.5",
      "aria-label": h("web.live.hero_slide_dot_aria", {
        index: a + 1,
        total: d
      }),
      "aria-current": l ? "true" : void 0,
      onClick: () => u(a),
      children: (0, t.jsx)("span", {
        className: (0, i.c)(s, l ? "w-6 bg-text-primary" : "w-2 bg-text-quaternary group-hover:bg-text-tertiary")
      })
    }, a);
  }), o[2] = d, o[3] = u, o[4] = m, o[5] = h, o[6] = n) : n = o[6], o[7] !== r || o[8] !== n ? (c = (0, t.jsx)("div", {
    className: r,
    "data-testid": "live-hero-dots",
    children: n
  }), o[7] = r, o[8] = n, o[9] = c) : c = o[9], c);
},
"PaginationDotsSkeleton": e => {
  let l,
    r,
    s,
    c = (0, a.c)(7),
    {
      count: o,
      className: d
    } = e;
  return c[0] !== d ? (l = (0, i.c)("flex h-6 items-center justify-center gap-2", d), c[0] = d, c[1] = l) : l = c[1], c[2] !== o ? (r = Array.from({
    length: o
  }, n), c[2] = o, c[3] = r) : r = c[3], c[4] !== l || c[5] !== r ? (s = (0, t.jsx)("div", {
    className: l,
    "aria-hidden": !0,
    children: r
  }), c[4] = l, c[5] = r, c[6] = s) : s = c[6], s;
}}};
}

function buildPreview(imports, dom, loadPreview) {
var t = imports(732486);
var a = imports(445242);
var i = imports(157633);
var l = imports(426091);
var r = imports(325320);
var s = imports(845785);
var n = imports(855376);
var c = imports(453706);
var o = imports(352386);
var d = imports(405048);
var f = imports(425444);
var h = imports(369091);
let m = (0, c.default)(() => loadPreview(47367).then(e => e.LivestreamPreviewPlayer), {
    loadableGenerated: {
      modules: [971491]
    },
    ssr: !1
  }),
  u = e => {
    let i,
      l,
      c,
      u,
      f = (0, a.c)(19),
      {
        mint: h,
        playlistUrl: x,
        onReady: p,
        isMuted: v,
        children: g,
        onAutoPlayFail: b,
        className: y,
        containerClassName: _,
        creator: j,
        isLive: w
      } = e,
      [N, E] = (0, o.useState)(!1);
    f[0] !== p ? (i = () => {
      p?.(), E(!0);
    }, f[0] = p, f[1] = i) : i = f[1];
    let S = !N;
    return f[2] !== y || f[3] !== _ || f[4] !== j || f[5] !== w || f[6] !== v || f[7] !== b || f[8] !== x || f[9] !== i || f[10] !== S ? (l = (0, t.jsx)(m, {
      creator: j,
      playOnHover: !1,
      playWhenVisible: !1,
      muted: v,
      playlistUrl: x,
      onIsReady: i,
      isLoading: S,
      loaderType: "progress-bar",
      onAutoPlayFail: b,
      className: y,
      containerClassName: _,
      isLive: w
    }), f[2] = y, f[3] = _, f[4] = j, f[5] = w, f[6] = v, f[7] = b, f[8] = x, f[9] = i, f[10] = S, f[11] = l) : l = f[11], f[12] !== g || f[13] !== l ? (c = (0, t.jsxs)(d.V, {
      property: n.f.PUMP_WEB,
      playerName: s.w.WEB_PREVIEW_PLAYER,
      children: [l, g]
    }), f[12] = g, f[13] = l, f[14] = c) : c = f[14], f[15] !== w || f[16] !== h || f[17] !== c ? (u = (0, t.jsx)(r.t, {
      mint: h,
      shouldGetLivestreamData: !1,
      shouldGetCoinInfo: !1,
      isModeratorCheckEnabled: !1,
      shouldJoinChatRoom: w,
      children: c
    }), f[15] = w, f[16] = h, f[17] = c, f[18] = u) : u = f[18], u;
  };
let x = e => {
  let i,
    r,
    s,
    n,
    c,
    d,
    m,
    u,
    x,
    p,
    v,
    g,
    b,
    y,
    _,
    j = (0, a.c)(25);
  j[0] !== e ? ({
    title: d,
    thumbnail: n,
    ipfsThumbnail: r,
    thumbnailUpdatedAt: c,
    className: i,
    ...s
  } = e, j[0] = e, j[1] = i, j[2] = r, j[3] = s, j[4] = n, j[5] = c, j[6] = d) : (i = j[1], r = j[2], s = j[3], n = j[4], c = j[5], d = j[6]);
  let {
    ipfsPrefix: w
  } = (0, h.useIpfsPrefix)();
  j[7] !== w || j[8] !== r ? (m = (0, l.r)(r, w), j[7] = w, j[8] = r, j[9] = m) : m = j[9];
  let N = m,
    [E, S] = (0, o.useState)(!1),
    k = (y = c, _ = n, y && _) ? n : N,
    P = !E && !i && "w-[280px] h-[160px]";
  j[10] !== i || j[11] !== P ? (u = (0, l.c)("relative rounded-lg bg-bg-secondary", P, i), j[10] = i, j[11] = P, j[12] = u) : u = j[12];
  let C = E ? "opacity-100" : "opacity-0";
  return j[13] !== C ? (x = (0, l.c)("w-full h-full object-cover transition-opacity duration-75", C), j[13] = C, j[14] = x) : x = j[14], j[15] === Symbol.for("react.memo_cache_sentinel") ? (p = () => S(!0), v = () => S(!0), j[15] = p, j[16] = v) : (p = j[15], v = j[16]), j[17] !== s || j[18] !== k || j[19] !== x || j[20] !== d ? (g = (0, t.jsx)(f.default, {
    width: 280,
    height: 160,
    unoptimized: !0,
    className: x,
    src: k,
    alt: d,
    onLoad: p,
    onError: v,
    ...s
  }), j[17] = s, j[18] = k, j[19] = x, j[20] = d, j[21] = g) : g = j[21], j[22] !== u || j[23] !== g ? (b = (0, t.jsx)("div", {
    className: u,
    children: g
  }), j[22] = u, j[23] = g, j[24] = b) : b = j[24], b;
};
return {816882: {"f": e => {
  let r,
    s,
    n,
    c,
    o = (0, a.c)(11),
    {
      size: d,
      className: m,
      isMuted: u,
      onMuteToggle: f
    } = e;
  return o[0] !== m ? (r = (0, l.c)("bg-bg-primary/60 backdrop-blur-sm p-1 rounded-full pointer-events-auto", m), o[0] = m, o[1] = r) : r = o[1], o[2] !== f ? (s = e => {
    e.stopPropagation(), e.preventDefault(), f();
  }, o[2] = f, o[3] = s) : s = o[3], o[4] !== u || o[5] !== d ? (n = u ? (0, t.jsx)(i.QA, {
    size: d
  }) : (0, t.jsx)(i.e, {
    size: d
  }), o[4] = u, o[5] = d, o[6] = n) : n = o[6], o[7] !== r || o[8] !== s || o[9] !== n ? (c = (0, t.jsx)("button", {
    type: "button",
    className: r,
    onClick: s,
    children: n
  }), o[7] = r, o[8] = s, o[9] = n, o[10] = c) : c = o[10], c;
}},
41705: {"f": e => {
  let i,
    r,
    s,
    n,
    c,
    o = (0, a.c)(22),
    {
      className: d,
      mint: m,
      title: f,
      thumbnail: h,
      thumbnailUpdatedAt: p,
      ipfsThumbnail: v,
      playlistUrl: g,
      isHovering: b,
      isMuted: y,
      children: _,
      onAutoPlayFail: j,
      thumbnailProps: w,
      creator: N,
      isLive: E
    } = e;
  return o[0] !== d ? (i = (0, l.c)("relative w-full aspect-video", d), o[0] = d, o[1] = i) : i = o[1], o[2] !== _ || o[3] !== N || o[4] !== b || o[5] !== E || o[6] !== y || o[7] !== m || o[8] !== j || o[9] !== g ? (r = b && (0, t.jsx)(u, {
    mint: m,
    playlistUrl: g,
    isMuted: y,
    onAutoPlayFail: j,
    containerClassName: "z-10",
    creator: N,
    isLive: E,
    children: _
  }), o[2] = _, o[3] = N, o[4] = b, o[5] = E, o[6] = y, o[7] = m, o[8] = j, o[9] = g, o[10] = r) : r = o[10], o[11] === Symbol.for("react.memo_cache_sentinel") ? (s = (0, l.c)("absolute inset-0 w-full h-full aspect-video object-cover z-0 transition-opacity duration-300"), o[11] = s) : s = o[11], o[12] !== v || o[13] !== h || o[14] !== w || o[15] !== p || o[16] !== f ? (n = (0, t.jsx)(x, {
    title: f,
    thumbnail: h,
    thumbnailUpdatedAt: p,
    ipfsThumbnail: v,
    className: s,
    ...w
  }), o[12] = v, o[13] = h, o[14] = w, o[15] = p, o[16] = f, o[17] = n) : n = o[17], o[18] !== i || o[19] !== r || o[20] !== n ? (c = (0, t.jsxs)("div", {
    className: i,
    children: [r, n]
  }), o[18] = i, o[19] = r, o[20] = n, o[21] = c) : c = o[21], c;
}}};
}

function buildHero(imports, dom, loadPreview) {
const {document} = dom;
var t = imports(732486);
var a = imports(445242);
var i = imports(157633);
var l = imports(426091);
var r = imports(352386);
var s = imports(398902);
var n = imports(798394);
var c = imports(70678);
var o = imports(65769);
var d = imports(187807);
var u = imports(218921);
var f = imports(292686);
var h = imports(458310);
var x = imports(816882);
var p = imports(41705);
var v = imports(146695);
var g = imports(705313);
var b = imports(928196);
var y = imports(277167);
var _ = imports(564861);
var j = imports(556120);
var w = imports(898337);
var N = imports(454430);
var E = imports(850175);
var S = imports(369091);
var L = imports(829010);
var R = imports(595673);
var T = imports(56999);
let m = e => {
  let i,
    r,
    s,
    n = (0, a.c)(9),
    {
      children: c,
      onClick: o,
      label: d,
      className: m
    } = e;
  return n[0] !== m ? (i = (0, l.c)("flex h-full items-center justify-center", m), n[0] = m, n[1] = i) : i = n[1], n[2] !== c || n[3] !== d || n[4] !== o ? (r = (0, t.jsx)("button", {
    type: "button",
    "aria-label": d,
    className: "flex items-center justify-center rounded-full bg-bg-tertiary p-3 text-text-primary transition-colors hover:bg-bg-quaternary",
    onClick: o,
    children: c
  }), n[2] = c, n[3] = d, n[4] = o, n[5] = r) : r = n[5], n[6] !== i || n[7] !== r ? (s = (0, t.jsx)("div", {
    className: i,
    children: r
  }), n[6] = i, n[7] = r, n[8] = s) : s = n[8], s;
};
let k = [],
  P = e => {
    let i,
      l,
      r,
      n,
      c,
      o,
      d,
      m,
      u,
      f,
      x,
      p,
      _,
      P,
      L,
      R,
      T,
      A,
      I = (0, a.c)(66),
      {
        title: U,
        mint: M,
        creator: O,
        symbol: D,
        marketCap: F,
        avatarUri: z,
        tags: V,
        isLive: W,
        viewerCount: H,
        viewerCountLabel: q,
        coinCreatedTimestamp: B,
        onOpenCoin: G,
        coin: $
      } = e,
      K = void 0 === V ? k : V,
      Q = void 0 !== W && W,
      {
        t: J
      } = (0, s.f)(),
      {
        ipfsPrefix: Y
      } = (0, S.useIpfsPrefix)(),
      X = O.username || O.address.slice(0, 8),
      Z = `/coin/${M}`;
    I[0] !== O.address ? (i = (0, v.$)(O.address), I[0] = O.address, I[1] = i) : i = I[1];
    let ee = i;
    I[2] !== $ || I[3] !== M ? (l = $ ?? (0, E.e)(M), I[2] = $, I[3] = M, I[4] = l) : l = I[4];
    let {
      prefetch: et,
      hoverProps: ea
    } = (0, E.W)(l);
    I[5] !== Q ? (r = Q && (0, t.jsx)(b.f, {}), I[5] = Q, I[6] = r) : r = I[6], I[7] !== Q || I[8] !== H || I[9] !== q ? (n = H && H > 0 ? (0, t.jsx)(w.f, {
      count: H,
      className: "bg-bg-tertiary",
      label: q ?? (Q ? "viewers" : "views")
    }) : null, I[7] = Q, I[8] = H, I[9] = q, I[10] = n) : n = I[10], I[11] !== r || I[12] !== n ? (c = (0, t.jsxs)("div", {
      className: "flex items-center gap-2",
      children: [r, n]
    }), I[11] = r, I[12] = n, I[13] = c) : c = I[13], I[14] !== Z || I[15] !== ea || I[16] !== G || I[17] !== et || I[18] !== U ? (o = (0, t.jsx)(h.default, {
      href: Z,
      onClick: G,
      className: "line-clamp-2 text-xl font-bold leading-tight text-text-hero hover:text-text-accent lg:text-2xl",
      prefetch: et,
      ...ea,
      children: U
    }), I[14] = Z, I[15] = ea, I[16] = G, I[17] = et, I[18] = U, I[19] = o) : o = I[19];
    let ei = h.default,
      el = g.f,
      er = J("web.live.creator_avatar_alt", {
        name: D || X
      });
    return I[20] !== el || I[21] !== z || I[22] !== O.address || I[23] !== Y || I[24] !== er ? (d = (0, t.jsx)(el, {
      ipfsPrefix: Y,
      src: z,
      alt: er,
      address: O.address,
      className: "size-10",
      height: 40,
      width: 40,
      isAnonymous: !1
    }), I[20] = el, I[21] = z, I[22] = O.address, I[23] = Y, I[24] = er, I[25] = d) : d = I[25], I[26] !== ei || I[27] !== ee || I[28] !== d ? (m = (0, t.jsx)(ei, {
      href: ee,
      className: "shrink-0",
      prefetch: !1,
      children: d
    }), I[26] = ei, I[27] = ee, I[28] = d, I[29] = m) : m = I[29], I[30] !== Z || I[31] !== ea || I[32] !== G || I[33] !== et || I[34] !== D ? (u = D ? (0, t.jsx)(h.default, {
      href: Z,
      onClick: G,
      className: "truncate text-sm font-semibold text-text-primary",
      prefetch: et,
      ...ea,
      children: D
    }) : null, I[30] = Z, I[31] = ea, I[32] = G, I[33] = et, I[34] = D, I[35] = u) : u = I[35], I[36] !== F ? (f = (0, t.jsx)(y.f, {
      marketCap: F
    }), I[36] = F, I[37] = f) : f = I[37], I[38] !== u || I[39] !== f ? (x = (0, t.jsxs)("div", {
      className: "flex items-center gap-2",
      children: [u, f]
    }), I[38] = u, I[39] = f, I[40] = x) : x = I[40], I[41] !== ee || I[42] !== X ? (p = (0, t.jsx)(h.default, {
      href: ee,
      className: "truncate text-sm text-text-tertiary",
      prefetch: !1,
      children: X
    }), I[41] = ee, I[42] = X, I[43] = p) : p = I[43], I[44] !== x || I[45] !== p ? (_ = (0, t.jsxs)("div", {
      className: "flex min-w-0 flex-1 flex-col",
      children: [x, p]
    }), I[44] = x, I[45] = p, I[46] = _) : _ = I[46], I[47] !== m || I[48] !== _ ? (P = (0, t.jsxs)("div", {
      className: "flex items-center gap-3",
      children: [m, _]
    }), I[47] = m, I[48] = _, I[49] = P) : P = I[49], I[50] !== B || I[51] !== M ? (L = B ? (0, t.jsx)(N.f, {
      coin: {
        mint: M,
        created_timestamp: B
      },
      className: "hidden h-24 w-full hover:scale-100 xl:flex"
    }) : null, I[50] = B, I[51] = M, I[52] = L) : L = I[52], I[53] !== K ? (R = K.length > 0 ? (0, t.jsx)("div", {
      className: "flex flex-wrap gap-1",
      children: K.map(C)
    }) : null, I[53] = K, I[54] = R) : R = I[54], I[55] !== $ || I[56] !== Z || I[57] !== G ? (T = $ ? (0, t.jsx)(j.f, {
      coin: $,
      href: Z,
      index: 0,
      onOpenCoin: G,
      placement: "hero",
      className: "max-w-xs"
    }) : null, I[55] = $, I[56] = Z, I[57] = G, I[58] = T) : T = I[58], I[59] !== P || I[60] !== L || I[61] !== R || I[62] !== T || I[63] !== c || I[64] !== o ? (A = (0, t.jsxs)("div", {
      className: "flex w-full flex-col gap-3",
      children: [c, o, P, L, R, T]
    }), I[59] = P, I[60] = L, I[61] = R, I[62] = T, I[63] = c, I[64] = o, I[65] = A) : A = I[65], A;
  };
function C(e) {
  return (0, t.jsx)(_.f, {
    text: e
  }, e);
}
let A = [],
  I = e => {
    let i,
      n,
      c,
      o,
      d,
      m,
      u,
      v,
      g,
      b,
      y,
      _,
      j,
      w,
      N,
      S,
      k = (0, a.c)(65),
      {
        mint: C,
        title: I,
        creator: U,
        symbol: M,
        marketCap: O,
        thumbnail: D,
        ipfsThumbnail: F,
        thumbnailUpdatedAt: z,
        avatarUri: V,
        tags: W,
        isLive: H,
        viewerCount: q,
        viewerCountLabel: B,
        playlistUrl: G,
        coinCreatedTimestamp: $,
        isSelected: K,
        coin: Q
      } = e,
      J = void 0 === W ? A : W,
      Y = void 0 !== H && H,
      {
        t: X
      } = (0, s.f)(),
      {
        isMutedFor: Z,
        toggleMuteFor: ee
      } = (0, T.F)();
    k[0] !== Z ? (i = Z(T.k.HERO_SLIDE), k[0] = Z, k[1] = i) : i = k[1];
    let et = i,
      [ea, ei] = (e => {
        let t,
          i,
          l,
          s = (0, a.c)(5),
          [n, c] = (0, r.useState)(void 0 !== e && e);
        return s[0] !== n ? (t = () => {
          if (n) return;
          let e = () => c(!0);
          return document.addEventListener("click", e), document.addEventListener("keydown", e), () => {
            document.removeEventListener("click", e), document.removeEventListener("keydown", e);
          };
        }, i = [n], s[0] = n, s[1] = t, s[2] = i) : (t = s[1], i = s[2]), (0, r.useEffect)(t, i), s[3] !== n ? (l = [n, c], s[3] = n, s[4] = l) : l = s[4], l;
      })(!0);
    k[2] !== Q || k[3] !== C ? (n = Q ?? (0, E.e)(C), k[2] = Q, k[3] = C, k[4] = n) : n = k[4];
    let {
      prefetch: el,
      hoverProps: er
    } = (0, E.W)(n);
    k[5] !== Y || k[6] !== O || k[7] !== C ? (c = () => {
      (0, R.iV)({
        coinId: C,
        itemPosition: 0,
        marketCap: Number(O.toFixed(2)),
        sourceScreen: f.Ae.LIVESTREAM,
        sourceElement: f.k9.LIVESTREAM_VIDEO_FEED,
        isLivestreamActive: Y
      });
    }, k[5] = Y, k[6] = O, k[7] = C, k[8] = c) : c = k[8];
    let es = c,
      en = `/coin/${C}`;
    return k[9] !== M || k[10] !== X || k[11] !== I ? (o = M ? X("web.live.open_stream_symbol_aria", {
      title: I,
      symbol: M
    }) : X("web.live.open_stream_aria", {
      title: I
    }), k[9] = M, k[10] = X, k[11] = I, k[12] = o) : o = k[12], k[13] === Symbol.for("react.memo_cache_sentinel") ? (d = (0, t.jsx)("span", {
      className: "block size-full",
      "aria-hidden": !0
    }), k[13] = d) : d = k[13], k[14] !== es || k[15] !== er || k[16] !== el || k[17] !== en || k[18] !== o ? (m = (0, t.jsx)(h.default, {
      href: en,
      onClick: es,
      prefetch: el,
      ...er,
      "aria-label": o,
      className: "absolute inset-0 z-[15]",
      children: d
    }), k[14] = es, k[15] = er, k[16] = el, k[17] = en, k[18] = o, k[19] = m) : m = k[19], k[20] === Symbol.for("react.memo_cache_sentinel") ? (u = (0, l.c)("pointer-events-none relative z-20", L.B), v = (0, l.c)("pointer-events-auto group relative", L.h), k[20] = u, k[21] = v) : (u = k[20], v = k[21]), k[22] !== ei ? (g = () => {
      ei(!1);
    }, k[22] = ei, k[23] = g) : g = k[23], k[24] === Symbol.for("react.memo_cache_sentinel") ? (b = {
      loading: "eager"
    }, k[24] = b) : b = k[24], k[25] !== ea || k[26] !== et || k[27] !== ee ? (y = ea && (0, t.jsx)("div", {
      className: "absolute inset-0 flex items-center justify-center",
      children: (0, t.jsx)(x.f, {
        size: 22,
        className: (0, l.c)("z-10 transition-opacity duration-300 group-hover:opacity-100", et ? "opacity-100" : "opacity-0"),
        isMuted: et,
        onMuteToggle: () => ee(T.k.HERO_SLIDE)
      })
    }), k[25] = ea, k[26] = et, k[27] = ee, k[28] = y) : y = k[28], k[29] !== U.address || k[30] !== F || k[31] !== Y || k[32] !== et || k[33] !== K || k[34] !== C || k[35] !== G || k[36] !== g || k[37] !== y || k[38] !== D || k[39] !== z || k[40] !== I ? (_ = (0, t.jsx)("div", {
      className: v,
      children: (0, t.jsx)(p.f, {
        className: "w-full",
        mint: C,
        title: I,
        thumbnail: D,
        ipfsThumbnail: F,
        thumbnailUpdatedAt: z,
        playlistUrl: G,
        isHovering: K,
        isMuted: et,
        onAutoPlayFail: g,
        thumbnailProps: b,
        creator: U.address,
        isLive: Y,
        children: y
      })
    }), k[29] = U.address, k[30] = F, k[31] = Y, k[32] = et, k[33] = K, k[34] = C, k[35] = G, k[36] = g, k[37] = y, k[38] = D, k[39] = z, k[40] = I, k[41] = _) : _ = k[41], k[42] === Symbol.for("react.memo_cache_sentinel") ? (j = (0, l.c)("pointer-events-auto flex min-w-0 flex-col justify-center p-4 xl:p-5", L.s), k[42] = j) : j = k[42], k[43] !== V || k[44] !== Q || k[45] !== $ || k[46] !== U || k[47] !== es || k[48] !== Y || k[49] !== O || k[50] !== C || k[51] !== M || k[52] !== J || k[53] !== D || k[54] !== z || k[55] !== I || k[56] !== q || k[57] !== B ? (w = (0, t.jsx)("div", {
      className: j,
      children: (0, t.jsx)(P, {
        title: I,
        mint: C,
        creator: U,
        symbol: M,
        marketCap: O,
        avatarUri: V,
        thumbnail: D,
        thumbnailUpdatedAt: z,
        tags: J,
        isLive: Y,
        viewerCount: q,
        viewerCountLabel: B,
        coinCreatedTimestamp: $,
        onOpenCoin: es,
        coin: Q
      })
    }), k[43] = V, k[44] = Q, k[45] = $, k[46] = U, k[47] = es, k[48] = Y, k[49] = O, k[50] = C, k[51] = M, k[52] = J, k[53] = D, k[54] = z, k[55] = I, k[56] = q, k[57] = B, k[58] = w) : w = k[58], k[59] !== _ || k[60] !== w ? (N = (0, t.jsxs)("div", {
      className: u,
      children: [_, w]
    }), k[59] = _, k[60] = w, k[61] = N) : N = k[61], k[62] !== N || k[63] !== m ? (S = (0, t.jsxs)("div", {
      className: "relative h-full w-full cursor-pointer overflow-hidden rounded-xl bg-bg-secondary",
      children: [m, N]
    }), k[62] = N, k[63] = m, k[64] = S) : S = k[64], S;
  };
return {369731: {"HeroCarousel": e => {
  let f,
    h,
    x,
    p,
    v,
    g,
    b,
    y,
    _,
    j,
    w,
    N,
    E = (0, a.c)(39),
    {
      livestreams: S
    } = e,
    {
      t: k
    } = (0, s.f)();
  E[0] !== S.length ? (f = {
    itemCount: S.length,
    isLooping: !0
  }, E[0] = S.length, E[1] = f) : f = E[1];
  let {
    selectedIndex: P,
    nextIndex: C,
    previousIndex: R,
    hasPrevious: T,
    hasNext: A,
    setSelectedIndex: U
  } = (e => {
    let t,
      i,
      l,
      s,
      n,
      c,
      o = (0, a.c)(19),
      {
        itemCount: d,
        isLooping: m
      } = e,
      u = void 0 !== m && m,
      [f, h] = (0, r.useState)(0);
    o[0] !== d ? (t = e => {
      h(t => Math.max(0, Math.min(t + e, d - 1)));
    }, o[0] = d, o[1] = t) : t = o[1];
    let x = t;
    o[2] !== u || o[3] !== d || o[4] !== x ? (i = () => {
      u ? h(e => (e + 1) % d) : x(1);
    }, o[2] = u, o[3] = d, o[4] = x, o[5] = i) : i = o[5];
    let p = i;
    o[6] !== u || o[7] !== d || o[8] !== x ? (l = () => {
      u ? h(e => (e - 1 + d) % d) : x(-1);
    }, o[6] = u, o[7] = d, o[8] = x, o[9] = l) : l = o[9];
    let v = l,
      g = d > 1 && u || f > 0,
      b = d > 1 && u || f < d - 1;
    return o[10] !== d ? (s = () => {
      h(e => Math.min(e, Math.max(0, d - 1)));
    }, n = [d], o[10] = d, o[11] = s, o[12] = n) : (s = o[11], n = o[12]), (0, r.useEffect)(s, n), o[13] !== b || o[14] !== g || o[15] !== p || o[16] !== v || o[17] !== f ? (c = {
      selectedIndex: f,
      nextIndex: p,
      previousIndex: v,
      hasPrevious: g,
      hasNext: b,
      setSelectedIndex: h
    }, o[13] = b, o[14] = g, o[15] = p, o[16] = v, o[17] = f, o[18] = c) : c = o[18], c;
  })(f);
  E[2] === Symbol.for("react.memo_cache_sentinel") ? (h = {
    gapPx: L.c
  }, E[2] = h) : h = E[2];
  let {
      containerRef: M,
      scrollRef: O,
      cardWidth: D
    } = (0, n.f)(h),
    F = (0, r.useRef)(!1),
    z = S.length - 1;
  E[3] === Symbol.for("react.memo_cache_sentinel") ? (x = (e, t) => F.current || Math.abs(t - e) > 1, E[3] = x) : x = E[3], E[4] !== D || E[5] !== O || E[6] !== P ? (p = {
    selectedIndex: P,
    scrollRef: O,
    cardWidth: D,
    skipBehavior: "instant",
    isSkip: x
  }, E[4] = D, E[5] = O, E[6] = P, E[7] = p) : p = E[7], (0, c.f)(p);
  let V = e => {
    F.current = !1, U(e);
  };
  E[8] !== z || E[9] !== C || E[10] !== P ? (v = () => {
    F.current = P === z, C();
  }, E[8] = z, E[9] = C, E[10] = P, E[11] = v) : v = E[11];
  let W = v;
  E[12] !== R || E[13] !== P ? (g = () => {
    F.current = 0 === P, R();
  }, E[12] = R, E[13] = P, E[14] = g) : g = E[14];
  let H = g;
  (0, o.f)({
    scrollRef: O,
    cardWidth: D,
    onSnapIndexChange: V
  });
  let q = d.HeroStage;
  E[15] !== H || E[16] !== T || E[17] !== k ? (b = T && (0, t.jsx)(m, {
    className: "absolute inset-y-0 left-0 z-20 hidden w-12 lg:flex xl:w-16",
    onClick: H,
    label: k("web.pagination.go_to_previous_page"),
    children: (0, t.jsx)(i.S, {
      size: 16
    })
  }), E[15] = H, E[16] = T, E[17] = k, E[18] = b) : b = E[18], E[19] !== W || E[20] !== A || E[21] !== k ? (y = A && (0, t.jsx)(m, {
    className: "absolute inset-y-0 right-0 z-20 hidden w-12 lg:flex xl:w-16",
    onClick: W,
    label: k("web.pagination.go_to_next_page"),
    children: (0, t.jsx)(i.v$, {
      size: 16
    })
  }), E[19] = W, E[20] = A, E[21] = k, E[22] = y) : y = E[22], E[23] !== b || E[24] !== y ? (_ = (0, t.jsxs)(t.Fragment, {
    children: [b, y]
  }), E[23] = b, E[24] = y, E[25] = _) : _ = E[25];
  let B = S.map((e, a) => {
    let i = P === a;
    return (0, t.jsx)("div", {
      className: (0, l.c)(L.F, "transition-[transform,opacity] duration-300 ease-out", i ? "opacity-100" : "scale-[0.94] opacity-50"),
      "data-testid": "live-hero-slot",
      "data-selected": i,
      onClickCapture: e => {
        a !== P && (e.preventDefault(), e.stopPropagation(), V(a));
      },
      children: (0, t.jsx)(I, {
        isSelected: i,
        ...e
      })
    }, e.mint);
  });
  return E[26] !== q || E[27] !== M || E[28] !== O || E[29] !== _ || E[30] !== B ? (j = (0, t.jsx)(q, {
    containerRef: M,
    scrollRef: O,
    overlay: _,
    children: B
  }), E[26] = q, E[27] = M, E[28] = O, E[29] = _, E[30] = B, E[31] = j) : j = E[31], E[32] !== S.length || E[33] !== V || E[34] !== P ? (w = (0, t.jsx)(u.PaginationDots, {
    count: S.length,
    selectedIndex: P,
    onSelect: V
  }), E[32] = S.length, E[33] = V, E[34] = P, E[35] = w) : w = E[35], E[36] !== j || E[37] !== w ? (N = (0, t.jsxs)("div", {
    className: "flex flex-col gap-3 isolate",
    children: [j, w]
  }), E[36] = j, E[37] = w, E[38] = N) : N = E[38], N;
}}};
}

// Authored capability composition. Original module-loader caching, dynamic
// scheduling, providers and media behavior are outside this boundary.
export function createLivePreviewFlow({ React, jsx, compiler, modules, loadPreview, dom }) {
  if (!React || typeof React.useState !== 'function' || typeof jsx?.jsx !== 'function' ||
      typeof compiler?.c !== 'function' || typeof loadPreview !== 'function' || !modules ||
      !dom || typeof dom.document?.addEventListener !== 'function' ||
      typeof dom.ResizeObserver !== 'function' || typeof dom.MutationObserver !== 'function')
    throw new TypeError('explicit React/JSX/compiler, module, preview-loader and DOM capabilities are required');
  const owned = new Map([[352386, React], [732486, jsx], [445242, compiler]]);
  const imports = (id) => {
    if (owned.has(id)) return owned.get(id);
    if (!Object.hasOwn(modules, id)) throw new TypeError('missing explicit module capability ' + id);
    return modules[id];
  };
  for (const build of [buildMute, buildScroll, buildStage, buildPagination, buildPreview, buildHero])
    for (const [id, value] of Object.entries(build(imports, dom, loadPreview))) owned.set(Number(id), value);
  return Object.freeze({ HeroCarousel: owned.get(369731).HeroCarousel,
    VideoMuteProvider: owned.get(56999).c, useVideoMute: owned.get(56999).F,
    PreviewMedia: owned.get(41705).f, MuteButton: owned.get(816882).f,
    PaginationDots: owned.get(218921).PaginationDots });
}
