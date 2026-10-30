// Editable complete main LiveCard display flow; original factories are never executed.
import {profileRoute} from "../search-navigation/navigation.mjs";
function buildCard(imports){
var t=imports(732486);
var i=imports(445242);
var r=imports(292686);
var s=imports(426091);
var l=imports(458310);
var a=imports(352386);
var n=imports(146695);
var o=imports(705313);
imports(12692);
var c=imports(398902);
var d=imports(850175);
var m=imports(369091);
var u=imports(687505);
let f = e => {
  let r,
    f,
    h,
    x,
    p,
    v,
    g,
    b,
    w,
    y,
    N,
    j,
    _,
    C,
    E = (0, i.c)(47),
    {
      title: I,
      avatarUri: S,
      creator: T,
      mint: L,
      symbol: k,
      children: R,
      linkUrl: A,
      onOpenCoin: z
    } = e,
    {
      t: P
    } = (0, c.f)(),
    {
      ipfsPrefix: M
    } = (0, m.useIpfsPrefix)(),
    [F, O] = (0, a.useState)(!1),
    D = T.username || T.address.slice(0, 8);
  E[0] !== T.address ? (r = (0, n.$)(T.address), E[0] = T.address, E[1] = r) : r = E[1];
  let U = r,
    H = A || `/coin/${L}`,
    K = A ? void 0 : z;
  E[2] !== A || E[3] !== L ? (f = (0, u.f)(L, A) ? (0, d.e)(L) : null, E[2] = A, E[3] = L, E[4] = f) : f = E[4];
  let V = f,
    {
      prefetch: $,
      hoverProps: W
    } = (0, d.W)(V);
  E[5] !== V || E[6] !== W || E[7] !== $ ? (h = V ? {
    prefetch: $,
    ...W
  } : {
    prefetch: !1
  }, E[5] = V, E[6] = W, E[7] = $, E[8] = h) : h = E[8];
  let G = h,
    q = l.default,
    B = o.f,
    Z = P("web.live.creator_avatar_alt", {
      name: k || D
    }),
    Q = T.address,
    X = F ? "opacity-100" : "opacity-0";
  return E[9] !== X ? (x = (0, s.c)("mt-0.5 size-8 transition-opacity duration-75", X), E[9] = X, E[10] = x) : x = E[10], E[11] === Symbol.for("react.memo_cache_sentinel") ? (p = () => O(!0), v = () => O(!0), E[11] = p, E[12] = v) : (p = E[11], v = E[12]), E[13] !== B || E[14] !== S || E[15] !== T.address || E[16] !== M || E[17] !== x || E[18] !== Z ? (g = (0, t.jsx)(B, {
    ipfsPrefix: M,
    src: S,
    alt: Z,
    address: Q,
    className: x,
    height: 32,
    isAnonymous: !1,
    onLoad: p,
    onError: v,
    width: 32
  }), E[13] = B, E[14] = S, E[15] = T.address, E[16] = M, E[17] = x, E[18] = Z, E[19] = g) : g = E[19], E[20] !== q || E[21] !== U || E[22] !== g ? (b = (0, t.jsx)(q, {
    href: U,
    className: "flex-shrink-0",
    prefetch: !1,
    children: g
  }), E[20] = q, E[21] = U, E[22] = g, E[23] = b) : b = E[23], E[24] !== H || E[25] !== G || E[26] !== K || E[27] !== I ? (w = (0, t.jsx)(l.default, {
    href: H,
    onClick: K,
    className: "min-w-0 truncate text-sm font-semibold leading-snug text-text-primary",
    ...G,
    children: I
  }), E[24] = H, E[25] = G, E[26] = K, E[27] = I, E[28] = w) : w = E[28], E[29] !== H || E[30] !== G || E[31] !== K || E[32] !== k ? (y = k ? (0, t.jsx)(l.default, {
    href: H,
    onClick: K,
    className: "shrink-0 rounded bg-bg-tertiary px-1.5 py-px text-[11px] font-medium leading-4 text-text-secondary",
    ...G,
    "data-testid": "live-card-ticker",
    children: k
  }) : null, E[29] = H, E[30] = G, E[31] = K, E[32] = k, E[33] = y) : y = E[33], E[34] !== w || E[35] !== y ? (N = (0, t.jsxs)("div", {
    className: "flex min-w-0 items-center gap-1.5",
    children: [w, y]
  }), E[34] = w, E[35] = y, E[36] = N) : N = E[36], E[37] !== U || E[38] !== D ? (j = (0, t.jsx)(l.default, {
    href: U,
    className: "mt-0.5 min-w-0 truncate text-xs leading-snug text-text-tertiary",
    prefetch: !1,
    children: D
  }), E[37] = U, E[38] = D, E[39] = j) : j = E[39], E[40] !== R || E[41] !== N || E[42] !== j ? (_ = (0, t.jsxs)("div", {
    className: "flex min-w-0 flex-col",
    children: [N, j, R]
  }), E[40] = R, E[41] = N, E[42] = j, E[43] = _) : _ = E[43], E[44] !== b || E[45] !== _ ? (C = (0, t.jsxs)("div", {
    className: "flex w-full gap-2",
    children: [b, _]
  }), E[44] = b, E[45] = _, E[46] = C) : C = E[46], C;
};
var h=imports(564861);
let x = e => {
  let r,
    s,
    l,
    a,
    n = (0, i.c)(15),
    {
      title: o,
      creator: c,
      avatarUri: d,
      mint: m,
      tags: u,
      linkUrl: h,
      symbol: x,
      onOpenCoin: v
    } = e;
  n[0] !== u ? (r = void 0 === u ? [] : u, n[0] = u, n[1] = r) : r = n[1];
  let g = r;
  return n[2] !== g ? (s = g.map(p), n[2] = g, n[3] = s) : s = n[3], n[4] !== s ? (l = (0, t.jsx)("div", {
    className: "flex gap-1",
    children: s
  }), n[4] = s, n[5] = l) : l = n[5], n[6] !== d || n[7] !== c || n[8] !== h || n[9] !== m || n[10] !== v || n[11] !== x || n[12] !== l || n[13] !== o ? (a = (0, t.jsx)(f, {
    title: o,
    avatarUri: d,
    creator: c,
    mint: m,
    linkUrl: h,
    symbol: x,
    onOpenCoin: v,
    children: l
  }), n[6] = d, n[7] = c, n[8] = h, n[9] = m, n[10] = v, n[11] = x, n[12] = l, n[13] = o, n[14] = a) : a = n[14], a;
};
function p(e) {
  return (0, t.jsx)(h.f, {
    text: e
  }, e);
}
var v=imports(928196);
var g=imports(277167);
var b=imports(816882);
var w=imports(41705);
var y=imports(556120);
var N=imports(898337);
var j=imports(454430);
var _=imports(666863);
var C=imports(595673);
var E=imports(56999);
let I = [];
return e => {
  let n,
    o,
    c,
    m,
    f,
    h,
    p,
    S,
    T,
    L,
    k,
    R,
    A,
    z,
    P,
    M,
    F,
    O,
    D,
    U,
    H,
    K,
    V,
    $,
    W,
    G = (0, i.c)(97),
    {
      mint: q,
      coinCreatedTimestamp: B,
      title: Z,
      creator: Q,
      marketCap: X,
      thumbnail: Y,
      ipfsThumbnail: J,
      thumbnailUpdatedAt: ee,
      avatarUri: et,
      isLive: ei,
      tags: er,
      viewerCount: es,
      viewerCountLabel: el,
      playlistUrl: ea,
      linkUrl: en,
      symbol: eo,
      index: ec,
      coin: ed
    } = e,
    em = void 0 !== ei && ei,
    eu = void 0 === er ? I : er,
    ef = void 0 === ec ? 0 : ec,
    [eh, ex] = (0, a.useState)(!1),
    {
      isMutedFor: ep,
      toggleMuteFor: ev,
      setMuteFor: eg
    } = (0, E.F)();
  G[0] !== ep ? (n = ep(E.k.CARD), G[0] = ep, G[1] = n) : n = G[1];
  let eb = n,
    ew = (0, a.useRef)(null);
  G[2] !== ed || G[3] !== en || G[4] !== q ? (o = (0, u.f)(q, en) ? ed ?? (0, d.e)(q) : null, G[2] = ed, G[3] = en, G[4] = q, G[5] = o) : o = G[5];
  let ey = o,
    {
      prefetch: eN,
      hoverProps: ej
    } = (0, d.W)(ey);
  G[6] !== ey || G[7] !== ej || G[8] !== eN ? (c = ey ? {
    prefetch: eN,
    ...ej
  } : {
    prefetch: !1
  }, G[6] = ey, G[7] = ej, G[8] = eN, G[9] = c) : c = G[9];
  let e_ = c;
  G[10] !== X ? (m = X ? Number(X.toFixed(2)) : 0, G[10] = X, G[11] = m) : m = G[11], G[12] !== ef || G[13] !== m ? (f = {
    itemPosition: ef,
    marketCap: m,
    sourceScreen: r.Ae.LIVESTREAM
  }, G[12] = ef, G[13] = m, G[14] = f) : f = G[14];
  let eC = f,
    eE = (0, _.f)(q, eC, void 0, r.k9.LIVESTREAM_VIDEO_FEED);
  G[15] !== ef || G[16] !== em || G[17] !== X || G[18] !== q ? (h = () => {
    (0, C.iV)({
      coinId: q,
      itemPosition: ef,
      marketCap: X ? Number(X.toFixed(2)) : 0,
      sourceScreen: r.Ae.LIVESTREAM,
      sourceElement: r.k9.LIVESTREAM_VIDEO_FEED,
      isLivestreamActive: em
    });
  }, G[15] = ef, G[16] = em, G[17] = X, G[18] = q, G[19] = h) : h = G[19];
  let eI = h;
  G[20] !== eb || G[21] !== ep || G[22] !== eg ? (p = () => {
    ex(!0), eb || (ew.current = ep(E.k.HERO_SLIDE), eg(E.k.HERO_SLIDE, !0));
  }, G[20] = eb, G[21] = ep, G[22] = eg, G[23] = p) : p = G[23], G[24] !== eg ? (S = () => {
    ex(!1), null !== ew.current && (eg(E.k.HERO_SLIDE, ew.current), ew.current = null);
  }, G[24] = eg, G[25] = S) : S = G[25];
  let eS = en || `/coin/${q}`,
    eT = en ? void 0 : eI;
  G[26] === Symbol.for("react.memo_cache_sentinel") ? (T = (0, t.jsx)("span", {
    className: "block size-full",
    "aria-hidden": !0
  }), G[26] = T) : T = G[26], G[27] !== e_ || G[28] !== eS || G[29] !== eT ? (L = (0, t.jsx)(l.default, {
    href: eS,
    onClick: eT,
    className: "absolute inset-0 z-0",
    ...e_,
    children: T
  }), G[27] = e_, G[28] = eS, G[29] = eT, G[30] = L) : L = G[30], G[31] !== ef ? (k = ef < 6 ? {
    loading: "eager"
  } : void 0, G[31] = ef, G[32] = k) : k = G[32], G[33] !== Q.address || G[34] !== J || G[35] !== eh || G[36] !== em || G[37] !== eb || G[38] !== q || G[39] !== ea || G[40] !== k || G[41] !== Y || G[42] !== ee || G[43] !== Z ? (R = (0, t.jsx)("div", {
    className: "absolute inset-0 z-0 pointer-events-none",
    children: (0, t.jsx)(w.f, {
      mint: q,
      title: Z,
      thumbnail: Y,
      ipfsThumbnail: J,
      thumbnailUpdatedAt: ee,
      playlistUrl: ea,
      isHovering: eh,
      isMuted: eb,
      thumbnailProps: k,
      creator: Q.address,
      isLive: em
    })
  }), G[33] = Q.address, G[34] = J, G[35] = eh, G[36] = em, G[37] = eb, G[38] = q, G[39] = ea, G[40] = k, G[41] = Y, G[42] = ee, G[43] = Z, G[44] = R) : R = G[44], G[45] === Symbol.for("react.memo_cache_sentinel") ? (A = (0, s.c)("absolute inset-0 z-10 flex items-start p-1 md:p-2 pointer-events-none", "justify-between"), G[45] = A) : A = G[45], G[46] !== em ? (z = em && (0, t.jsx)(v.f, {}), G[46] = em, G[47] = z) : z = G[47], G[48] !== eg || G[49] !== ev ? (P = () => {
    ev(E.k.CARD), eg(E.k.HERO_SLIDE, !0);
  }, G[48] = eg, G[49] = ev, G[50] = P) : P = G[50];
  let eL = eh && "opacity-100";
  return G[51] !== eL ? (M = (0, s.c)("opacity-0 transition-opacity duration-300", eL), G[51] = eL, G[52] = M) : M = G[52], G[53] !== eb || G[54] !== P || G[55] !== M ? (F = (0, t.jsx)(b.f, {
    isMuted: eb,
    onMuteToggle: P,
    size: 16,
    className: M
  }), G[53] = eb, G[54] = P, G[55] = M, G[56] = F) : F = G[56], G[57] !== z || G[58] !== F ? (O = (0, t.jsxs)("div", {
    className: "flex items-center gap-2",
    children: [z, F]
  }), G[57] = z, G[58] = F, G[59] = O) : O = G[59], G[60] !== X ? (D = X && (0, t.jsx)(g.f, {
    marketCap: X
  }), G[60] = X, G[61] = D) : D = G[61], G[62] !== O || G[63] !== D ? (U = (0, t.jsxs)("div", {
    className: A,
    children: [O, D]
  }), G[62] = O, G[63] = D, G[64] = U) : U = G[64], G[65] !== B || G[66] !== em || G[67] !== q || G[68] !== es || G[69] !== el ? (H = (es || B) && (0, t.jsxs)("div", {
    className: "absolute bottom-0 left-0 right-0 p-2 flex items-end justify-between pointer-events-none",
    children: [es ? (0, t.jsx)(N.f, {
      count: es,
      label: el ?? (em ? "viewers" : "views")
    }) : (0, t.jsx)("div", {}), B && (0, t.jsx)(j.f, {
      coin: {
        mint: q,
        created_timestamp: B
      }
    })]
  }), G[65] = B, G[66] = em, G[67] = q, G[68] = es, G[69] = el, G[70] = H) : H = G[70], G[71] !== L || G[72] !== R || G[73] !== U || G[74] !== H ? (K = (0, t.jsxs)("div", {
    className: "relative rounded-lg overflow-hidden aspect-video isolate",
    children: [L, R, U, H]
  }), G[71] = L, G[72] = R, G[73] = U, G[74] = H, G[75] = K) : K = G[75], G[76] !== et || G[77] !== Q || G[78] !== eI || G[79] !== en || G[80] !== q || G[81] !== eo || G[82] !== eu || G[83] !== Z ? (V = (0, t.jsx)(x, {
    title: Z,
    creator: Q,
    avatarUri: et,
    mint: q,
    tags: eu,
    linkUrl: en,
    symbol: eo,
    onOpenCoin: eI
  }), G[76] = et, G[77] = Q, G[78] = eI, G[79] = en, G[80] = q, G[81] = eo, G[82] = eu, G[83] = Z, G[84] = V) : V = G[84], G[85] !== ed || G[86] !== eI || G[87] !== ef || G[88] !== q ? ($ = ed ? (0, t.jsx)(y.f, {
    coin: ed,
    href: `/coin/${q}`,
    index: ef,
    onOpenCoin: eI
  }) : null, G[85] = ed, G[86] = eI, G[87] = ef, G[88] = q, G[89] = $) : $ = G[89], G[90] !== eE || G[91] !== p || G[92] !== S || G[93] !== K || G[94] !== V || G[95] !== $ ? (W = (0, t.jsxs)("div", {
    ref: eE,
    className: "w-full flex flex-col gap-2 cursor-pointer transition-transform duration-150 hover:scale-[1.025]",
    onMouseEnter: p,
    onMouseLeave: S,
    children: [K, V, $]
  }), G[90] = eE, G[91] = p, G[92] = S, G[93] = K, G[94] = V, G[95] = $, G[96] = W) : W = G[96], W;
};
}

function buildBadges(imports){
var t=imports(732486);
var a=imports(445242);
var l=imports(426091);
var p=imports(398902);
var v=imports(938277);
return{928196:{f:e => {
  let i,
    r,
    s,
    n = (0, a.c)(7),
    {
      className: c
    } = e,
    {
      t: o
    } = (0, p.f)();
  return n[0] !== c ? (i = (0, l.c)("flex items-center justify-center rounded-md bg-bg-accent font-semibold text-black px-1.5 py-0.5 text-xs", c), n[0] = c, n[1] = i) : i = n[1], n[2] !== o ? (r = o("livestream.controls.live"), n[2] = o, n[3] = r) : r = n[3], n[4] !== i || n[5] !== r ? (s = (0, t.jsx)("span", {
    className: i,
    children: r
  }), n[4] = i, n[5] = r, n[6] = s) : s = n[6], s;
}},277167:{f:e => {
  let i,
    r,
    s = (0, a.c)(5),
    {
      marketCap: n,
      className: c
    } = e;
  s[0] !== c ? (i = (0, l.c)("flex items-center justify-center rounded-md bg-bg-primary px-1.5 py-0.5 text-xs font-semibold text-text-accent", c), s[0] = c, s[1] = i) : i = s[1];
  let o = "$" + (0, v.M)(n);
  return s[2] !== i || s[3] !== o ? (r = (0, t.jsx)("span", {
    className: i,
    children: o
  }), s[2] = i, s[3] = o, s[4] = r) : r = s[4], r;
}},564861:{f:e => {
  let i,
    l = (0, a.c)(2),
    {
      text: r
    } = e;
  return l[0] !== r ? (i = (0, t.jsx)("div", {
    className: "rounded-md bg-black-3 px-2 py-1 text-xs text-white",
    children: r
  }), l[0] = r, l[1] = i) : i = l[1], i;
}},898337:{f:e => {
  let i,
    r,
    s,
    n = (0, a.c)(9),
    {
      count: c,
      className: o,
      label: d
    } = e,
    m = void 0 === d ? "viewers" : d,
    {
      t: u
    } = (0, p.f)();
  return n[0] !== o ? (i = (0, l.c)("flex items-center justify-center rounded-md bg-bg-primary/60 backdrop-blur-sm font-semibold text-white px-1.5 py-0.5 text-xs", o), n[0] = o, n[1] = i) : i = n[1], n[2] !== c || n[3] !== m || n[4] !== u ? (r = u("views" === m ? "web.live.view_count" : "web.live.viewer_count", {
    count: c,
    formatted_count: (0, v.C)(c)
  }), n[2] = c, n[3] = m, n[4] = u, n[5] = r) : r = n[5], n[6] !== i || n[7] !== r ? (s = (0, t.jsx)("span", {
    className: i,
    children: r
  }), n[6] = i, n[7] = r, n[8] = s) : s = n[8], s;
}}};
}

const shouldPrefetch=(e, t) => null == t || t === `/coin/${e}` || t.startsWith(`/coin/${e}?`);
const mintOnly=e => ({
  mint: e,
  mintOnly: !0
});

function formats0(){
let t = (e, t = 3) => 0 === e ? t - 1 : Math.max(0, t - (Math.floor(Math.log10(Math.abs(e))) + 1));
let i = (e, i = 3) => {
  let r = t(e, i),
    n = Number(e.toFixed(r)),
    a = t(n, i);
  return n.toFixed(a);
};
let r = e => {
  if ("number" != typeof e) return "0";
  if (e >= 1e9) {
    let t = e / 1e9,
      r = Number(i(t));
    return r >= 1e3 ? `${i(r / 1e3)}T` : `${i(t)}B`;
  }
  if (e >= 1e6) {
    let t = e / 1e6,
      r = Number(i(t));
    return r >= 1e3 ? `${i(r / 1e3)}B` : `${i(t)}M`;
  }
  if (e >= 1e3) {
    let t = e / 1e3,
      r = Number(i(t));
    return r >= 1e3 ? `${i(r / 1e3)}M` : `${i(t)}K`;
  }
  return `${e.toFixed(0)}`;
};
let n = e => r(e);
return{M:n,C:r};
}

function formats1(){
let t = (e, t = 3) => 0 === e ? t - 1 : Math.max(0, t - (Math.floor(Math.log10(Math.abs(e))) + 1));
let r = (e, r = 3) => {
  let n = t(e, r),
    i = Number(e.toFixed(n)),
    s = t(i, r);
  return i.toFixed(s);
};
let n = e => {
  if ("number" != typeof e) return "0";
  if (e >= 1e9) {
    let t = e / 1e9,
      n = Number(r(t));
    return n >= 1e3 ? `${r(n / 1e3)}T` : `${r(t)}B`;
  }
  if (e >= 1e6) {
    let t = e / 1e6,
      n = Number(r(t));
    return n >= 1e3 ? `${r(n / 1e3)}B` : `${r(t)}M`;
  }
  if (e >= 1e3) {
    let t = e / 1e3,
      n = Number(r(t));
    return n >= 1e3 ? `${r(n / 1e3)}M` : `${r(t)}K`;
  }
  return `${e.toFixed(0)}`;
};
let i = e => n(e);
return{M:i,C:n};
}

export const CARD_FORMAT_CONTEXTS=Object.freeze(["545894110a73dff365be7a9abf03f0e26f66033993f80b40e125fe1697bd19f6","88db731a9e6cae25cc2d89b46bda5bd2aad0299984f114c04b69bc753c87b5de"]);
export function createLiveCardFormats(context){const builders=new Map([["545894110a73dff365be7a9abf03f0e26f66033993f80b40e125fe1697bd19f6",formats0],["88db731a9e6cae25cc2d89b46bda5bd2aad0299984f114c04b69bc753c87b5de",formats1]]);if(!builders.has(context))throw new TypeError('explicit captured compact-format context required');return Object.freeze(builders.get(context)());}
// Module values/bootstrap, provider/action/rendering lifecycles are required capabilities, not acquired here.
export function createLiveCardDisplay({React,jsx,compiler,classNames,Avatar,preview,formatters,modules}){
 if(typeof React?.useState!=='function'||typeof jsx?.jsx!=='function'||typeof compiler?.c!=='function'||typeof classNames!=='function'||!Avatar||typeof preview?.useVideoMute!=='function'||!preview?.MuteButton||!preview?.PreviewMedia||!preview?.VideoMuteProvider||typeof formatters?.M!=='function'||typeof formatters?.C!=='function'||!modules)throw new TypeError('exact Card React/Avatar/1879preview/format/module capabilities required');
 for(const id of[12692,458310,398902,850175,369091,556120,454430,666863,595673])if(!Object.hasOwn(modules,id))throw new TypeError('required actual Card module capability '+id);
 if(typeof modules[398902]?.f!=='function'||typeof modules[369091]?.useIpfsPrefix!=='function'||typeof modules[850175]?.W!=='function'||typeof modules[666863]?.f!=='function'||typeof modules[595673]?.iV!=='function')throw new TypeError('actual hook/telemetry signatures required');
 const owned=new Map([[352386,React],[732486,jsx],[445242,compiler],[426091,{c:classNames}],[705313,{f:Avatar}],[146695,{$:profileRoute}],[938277,formatters],[292686,{"Ae":{"LIVESTREAM":6},"k9":{"LIVESTREAM_VIDEO_FEED":100}}],[56999,{F:preview.useVideoMute,k:{"CARD":"Card","HERO_SLIDE":"HeroSlide"}}],[816882,{f:preview.MuteButton}],[41705,{f:preview.PreviewMedia}],[687505,{f:shouldPrefetch}]]);
 const imports=id=>{if(owned.has(id))return owned.get(id);if(!Object.hasOwn(modules,id))throw new TypeError('missing actual Card import '+id);if(id===850175)return{...modules[id],e:mintOnly};return modules[id];};
 for(const[id,value]of Object.entries(buildBadges(imports)))owned.set(Number(id),value);
 return Object.freeze({Card:buildCard(imports),VideoMuteProvider:preview.VideoMuteProvider});
}
