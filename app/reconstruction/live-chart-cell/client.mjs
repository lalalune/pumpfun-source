// Editable complete MAIN/live ChartCell/query/display/IO/lazy-chart owner.
// Captured factories remain inert; financial data, library and loader runtimes are required ports.
function frame454430_0(imports,dom,loadModule){
const IntersectionObserver=dom.IntersectionObserver;
const e={A:loadModule};
var t = imports(732486),
  n = imports(445242),
  r = imports(352386),
  i = imports(521368),
  o = imports(386017),
  s = imports(170450),
  a = imports(338319),
  l = imports(679553);
let c = e => {
    let r,
      o,
      s,
      a,
      c = (0, n.c)(10);
    c[0] !== e ? ({
      coin: r,
      ...o
    } = e, c[0] = e, c[1] = r, c[2] = o) : (r = c[1], o = c[2]), c[3] !== r.chain_id ? (s = {
      chainId: r.chain_id
    }, c[3] = r.chain_id, c[4] = s) : s = c[4];
    let {
      candlesticks: u,
      isLoading: d,
      error: m
    } = (0, i.f)(r.mint, r.created_timestamp ?? null, void 0, s);
    return c[5] !== u || c[6] !== m || c[7] !== d || c[8] !== o ? (a = (0, t.jsx)(l.f, {
      data: u,
      isLoading: d,
      error: m,
      ...o
    }), c[5] = u, c[6] = m, c[7] = d, c[8] = o, c[9] = a) : a = c[9], a;
  },
  u = e => {
    let i,
      l,
      u = (0, n.c)(7),
      d = (0, r.useRef)(null);
    u[0] === Symbol.for("react.memo_cache_sentinel") ? (i = {
      rootMargin: "320px 0px"
    }, u[0] = i) : i = u[0];
    let m = (0, o.f)(d, i);
    if (!(0, s.f)() || !m) {
      let n, r;
      return u[1] !== e.className ? (n = (0, a.c)("flex h-8 w-16", e.className), u[1] = e.className, u[2] = n) : n = u[2], u[3] !== n ? (r = (0, t.jsx)("div", {
        ref: d,
        "aria-hidden": !0,
        className: n,
        "data-testid": "chart-cell-pending"
      }), u[3] = n, u[4] = r) : r = u[4], r;
    }
    return u[5] !== e ? (l = (0, t.jsx)(c, {
      ...e
    }), u[5] = e, u[6] = l) : l = u[6], l;
  };
u.displayName = "ChartCell";
let d = r.default.memo(u);
return{"f":d};
}

function frame454430_1(imports,dom,loadModule){
const IntersectionObserver=dom.IntersectionObserver;
const e={A:loadModule};
var t = imports(732486),
  r = imports(445242),
  i = imports(352386),
  a = imports(521368),
  n = imports(386017),
  l = imports(170450),
  s = imports(338319),
  o = imports(679553);
let c = e => {
    let i,
      n,
      l,
      s,
      c = (0, r.c)(10);
    c[0] !== e ? ({
      coin: i,
      ...n
    } = e, c[0] = e, c[1] = i, c[2] = n) : (i = c[1], n = c[2]), c[3] !== i.chain_id ? (l = {
      chainId: i.chain_id
    }, c[3] = i.chain_id, c[4] = l) : l = c[4];
    let {
      candlesticks: m,
      isLoading: d,
      error: u
    } = (0, a.f)(i.mint, i.created_timestamp ?? null, void 0, l);
    return c[5] !== m || c[6] !== u || c[7] !== d || c[8] !== n ? (s = (0, t.jsx)(o.f, {
      data: m,
      isLoading: d,
      error: u,
      ...n
    }), c[5] = m, c[6] = u, c[7] = d, c[8] = n, c[9] = s) : s = c[9], s;
  },
  m = e => {
    let a,
      o,
      m = (0, r.c)(7),
      d = (0, i.useRef)(null);
    m[0] === Symbol.for("react.memo_cache_sentinel") ? (a = {
      rootMargin: "320px 0px"
    }, m[0] = a) : a = m[0];
    let u = (0, n.f)(d, a);
    if (!(0, l.f)() || !u) {
      let r, i;
      return m[1] !== e.className ? (r = (0, s.c)("flex h-8 w-16", e.className), m[1] = e.className, m[2] = r) : r = m[2], m[3] !== r ? (i = (0, t.jsx)("div", {
        ref: d,
        "aria-hidden": !0,
        className: r,
        "data-testid": "chart-cell-pending"
      }), m[3] = r, m[4] = i) : i = m[4], i;
    }
    return m[5] !== e ? (o = (0, t.jsx)(c, {
      ...e
    }), m[5] = e, m[6] = o) : o = m[6], o;
  };
m.displayName = "ChartCell";
let d = i.default.memo(m);
return{"f":d};
}

function frame454430_2(imports,dom,loadModule){
const IntersectionObserver=dom.IntersectionObserver;
const e={A:loadModule};
var t = imports(732486),
  r = imports(445242),
  a = imports(352386),
  l = imports(521368),
  n = imports(386017),
  i = imports(170450),
  s = imports(338319),
  o = imports(679553);
let c = e => {
    let a,
      n,
      i,
      s,
      c = (0, r.c)(10);
    c[0] !== e ? ({
      coin: a,
      ...n
    } = e, c[0] = e, c[1] = a, c[2] = n) : (a = c[1], n = c[2]), c[3] !== a.chain_id ? (i = {
      chainId: a.chain_id
    }, c[3] = a.chain_id, c[4] = i) : i = c[4];
    let {
      candlesticks: d,
      isLoading: u,
      error: m
    } = (0, l.f)(a.mint, a.created_timestamp ?? null, void 0, i);
    return c[5] !== d || c[6] !== m || c[7] !== u || c[8] !== n ? (s = (0, t.jsx)(o.f, {
      data: d,
      isLoading: u,
      error: m,
      ...n
    }), c[5] = d, c[6] = m, c[7] = u, c[8] = n, c[9] = s) : s = c[9], s;
  },
  d = e => {
    let l,
      o,
      d = (0, r.c)(7),
      u = (0, a.useRef)(null);
    d[0] === Symbol.for("react.memo_cache_sentinel") ? (l = {
      rootMargin: "320px 0px"
    }, d[0] = l) : l = d[0];
    let m = (0, n.f)(u, l);
    if (!(0, i.f)() || !m) {
      let r, a;
      return d[1] !== e.className ? (r = (0, s.c)("flex h-8 w-16", e.className), d[1] = e.className, d[2] = r) : r = d[2], d[3] !== r ? (a = (0, t.jsx)("div", {
        ref: u,
        "aria-hidden": !0,
        className: r,
        "data-testid": "chart-cell-pending"
      }), d[3] = r, d[4] = a) : a = d[4], a;
    }
    return d[5] !== e ? (o = (0, t.jsx)(c, {
      ...e
    }), d[5] = e, d[6] = o) : o = d[6], o;
  };
d.displayName = "ChartCell";
let u = a.default.memo(d);
return{"f":u};
}

function frame521368_0(imports,dom,loadModule){
const IntersectionObserver=dom.IntersectionObserver;
const e={A:loadModule};
var t = imports(445242),
  r = imports(690877),
  i = imports(38279),
  a = imports(636882),
  n = imports(997627),
  s = imports(693908);
return{"f":(e, l, o, c) => {
  let m,
    d,
    u,
    h,
    x,
    f,
    b,
    p,
    y,
    v,
    g = (0, t.c)(35);
  g[0] !== l ? (m = null != l && Number.isFinite(l) && l > 0 && (0, s.a)(l), g[0] = l, g[1] = m) : m = g[1];
  let w = m;
  if (g[2] !== l || g[3] !== e || g[4] !== c?.chainId || g[5] !== c?.timeframe || g[6] !== w || g[7] !== o) {
    let t,
      n = null != l && Number.isFinite(l) && l > 0 ? (0, s.Y)(l) : {
        timeframe: i.v.COIN_LINE_CHART.TIMEFRAME,
        width: i.v.COIN_LINE_CHART.WIDTH
      },
      m = w ? (0, s.S)(l) : null;
    f = c?.timeframe ?? n.timeframe, u = o ?? n.width;
    let b = c?.chainId;
    g[13] !== l || g[14] !== e || g[15] !== b ? (t = (0, a.f)({
      coinAddress: e,
      coinCreatedTimestamp: l,
      chainId: b
    }), g[13] = l, g[14] = e, g[15] = b, g[16] = t) : t = g[16], d = t, x = r.useQuery, h = w ? [...i.Q.COIN_CANDLES({
      coinAddress: e,
      coinCreatedTimestamp: l ?? 0,
      interval: m.interval,
      limit: m.limit
    }), "sparklineCandlesticks", c?.chainId ?? null] : [...i.Q.COIN_LINE_CHART({
      coinAddress: e,
      coinCreatedTimestamp: l ?? 0,
      timeframe: f,
      width: u
    }), "sparklineCandlesticks", c?.chainId ?? null], g[2] = l, g[3] = e, g[4] = c?.chainId, g[5] = c?.timeframe, g[6] = w, g[7] = o, g[8] = d, g[9] = u, g[10] = h, g[11] = x, g[12] = f;
  } else d = g[8], u = g[9], h = g[10], x = g[11], f = g[12];
  g[17] !== l || g[18] !== e || g[19] !== c?.chainId || g[20] !== u || g[21] !== f ? (b = () => (0, n.u)({
    coinAddress: e,
    coinCreatedTimestamp: l ?? 0,
    chainId: c?.chainId,
    timeframe: f,
    width: u
  }), g[17] = l, g[18] = e, g[19] = c?.chainId, g[20] = u, g[21] = f, g[22] = b) : b = g[22];
  let k = c?.staleTime ?? (w ? 15e3 : 3e5),
    N = c?.refetchInterval;
  g[23] !== d || g[24] !== h || g[25] !== b || g[26] !== k || g[27] !== N ? (p = {
    queryKey: h,
    queryFn: b,
    enabled: d,
    staleTime: k,
    gcTime: 6e5,
    retry: 1,
    retryDelay: 2e3,
    refetchInterval: N
  }, g[23] = d, g[24] = h, g[25] = b, g[26] = k, g[27] = N, g[28] = p) : p = g[28];
  let {
    data: j,
    isLoading: _,
    error: C
  } = x(p);
  return g[29] !== j ? (y = j || [], g[29] = j, g[30] = y) : y = g[30], g[31] !== _ || g[32] !== y || g[33] !== C ? (v = {
    candlesticks: y,
    isLoading: _,
    error: C
  }, g[31] = _, g[32] = y, g[33] = C, g[34] = v) : v = g[34], v;
}};
}

function frame521368_1(imports,dom,loadModule){
const IntersectionObserver=dom.IntersectionObserver;
const e={A:loadModule};
var t = imports(445242),
  n = imports(690877),
  r = imports(38279),
  i = imports(636882),
  o = imports(997627),
  s = imports(693908);
return{"f":(e, a, l, c) => {
  let u,
    d,
    m,
    E,
    f,
    I,
    T,
    p,
    g,
    _,
    S = (0, t.c)(35);
  S[0] !== a ? (u = null != a && Number.isFinite(a) && a > 0 && (0, s.a)(a), S[0] = a, S[1] = u) : u = S[1];
  let y = u;
  if (S[2] !== a || S[3] !== e || S[4] !== c?.chainId || S[5] !== c?.timeframe || S[6] !== y || S[7] !== l) {
    let t,
      o = null != a && Number.isFinite(a) && a > 0 ? (0, s.Y)(a) : {
        timeframe: r.v.COIN_LINE_CHART.TIMEFRAME,
        width: r.v.COIN_LINE_CHART.WIDTH
      },
      u = y ? (0, s.S)(a) : null;
    I = c?.timeframe ?? o.timeframe, m = l ?? o.width;
    let T = c?.chainId;
    S[13] !== a || S[14] !== e || S[15] !== T ? (t = (0, i.f)({
      coinAddress: e,
      coinCreatedTimestamp: a,
      chainId: T
    }), S[13] = a, S[14] = e, S[15] = T, S[16] = t) : t = S[16], d = t, f = n.useQuery, E = y ? [...r.Q.COIN_CANDLES({
      coinAddress: e,
      coinCreatedTimestamp: a ?? 0,
      interval: u.interval,
      limit: u.limit
    }), "sparklineCandlesticks", c?.chainId ?? null] : [...r.Q.COIN_LINE_CHART({
      coinAddress: e,
      coinCreatedTimestamp: a ?? 0,
      timeframe: I,
      width: m
    }), "sparklineCandlesticks", c?.chainId ?? null], S[2] = a, S[3] = e, S[4] = c?.chainId, S[5] = c?.timeframe, S[6] = y, S[7] = l, S[8] = d, S[9] = m, S[10] = E, S[11] = f, S[12] = I;
  } else d = S[8], m = S[9], E = S[10], f = S[11], I = S[12];
  S[17] !== a || S[18] !== e || S[19] !== c?.chainId || S[20] !== m || S[21] !== I ? (T = () => (0, o.u)({
    coinAddress: e,
    coinCreatedTimestamp: a ?? 0,
    chainId: c?.chainId,
    timeframe: I,
    width: m
  }), S[17] = a, S[18] = e, S[19] = c?.chainId, S[20] = m, S[21] = I, S[22] = T) : T = S[22];
  let h = c?.staleTime ?? (y ? 15e3 : 3e5),
    A = c?.refetchInterval;
  S[23] !== d || S[24] !== E || S[25] !== T || S[26] !== h || S[27] !== A ? (p = {
    queryKey: E,
    queryFn: T,
    enabled: d,
    staleTime: h,
    gcTime: 6e5,
    retry: 1,
    retryDelay: 2e3,
    refetchInterval: A
  }, S[23] = d, S[24] = E, S[25] = T, S[26] = h, S[27] = A, S[28] = p) : p = S[28];
  let {
    data: O,
    isLoading: v,
    error: L
  } = f(p);
  return S[29] !== O ? (g = O || [], S[29] = O, S[30] = g) : g = S[30], S[31] !== v || S[32] !== g || S[33] !== L ? (_ = {
    candlesticks: g,
    isLoading: v,
    error: L
  }, S[31] = v, S[32] = g, S[33] = L, S[34] = _) : _ = S[34], _;
}};
}

function frame521368_2(imports,dom,loadModule){
const IntersectionObserver=dom.IntersectionObserver;
const e={A:loadModule};
var t = imports(445242),
  r = imports(690877),
  i = imports(38279),
  a = imports(636882),
  n = imports(997627),
  l = imports(693908);
return{"f":(e, s, o, c) => {
  let m,
    d,
    u,
    h,
    f,
    x,
    p,
    g,
    v,
    b,
    y = (0, t.c)(35);
  y[0] !== s ? (m = null != s && Number.isFinite(s) && s > 0 && (0, l.a)(s), y[0] = s, y[1] = m) : m = y[1];
  let w = m;
  if (y[2] !== s || y[3] !== e || y[4] !== c?.chainId || y[5] !== c?.timeframe || y[6] !== w || y[7] !== o) {
    let t,
      n = null != s && Number.isFinite(s) && s > 0 ? (0, l.Y)(s) : {
        timeframe: i.v.COIN_LINE_CHART.TIMEFRAME,
        width: i.v.COIN_LINE_CHART.WIDTH
      },
      m = w ? (0, l.S)(s) : null;
    x = c?.timeframe ?? n.timeframe, u = o ?? n.width;
    let p = c?.chainId;
    y[13] !== s || y[14] !== e || y[15] !== p ? (t = (0, a.f)({
      coinAddress: e,
      coinCreatedTimestamp: s,
      chainId: p
    }), y[13] = s, y[14] = e, y[15] = p, y[16] = t) : t = y[16], d = t, f = r.useQuery, h = w ? [...i.Q.COIN_CANDLES({
      coinAddress: e,
      coinCreatedTimestamp: s ?? 0,
      interval: m.interval,
      limit: m.limit
    }), "sparklineCandlesticks", c?.chainId ?? null] : [...i.Q.COIN_LINE_CHART({
      coinAddress: e,
      coinCreatedTimestamp: s ?? 0,
      timeframe: x,
      width: u
    }), "sparklineCandlesticks", c?.chainId ?? null], y[2] = s, y[3] = e, y[4] = c?.chainId, y[5] = c?.timeframe, y[6] = w, y[7] = o, y[8] = d, y[9] = u, y[10] = h, y[11] = f, y[12] = x;
  } else d = y[8], u = y[9], h = y[10], f = y[11], x = y[12];
  y[17] !== s || y[18] !== e || y[19] !== c?.chainId || y[20] !== u || y[21] !== x ? (p = () => (0, n.u)({
    coinAddress: e,
    coinCreatedTimestamp: s ?? 0,
    chainId: c?.chainId,
    timeframe: x,
    width: u
  }), y[17] = s, y[18] = e, y[19] = c?.chainId, y[20] = u, y[21] = x, y[22] = p) : p = y[22];
  let j = c?.staleTime ?? (w ? 15e3 : 3e5),
    N = c?.refetchInterval;
  y[23] !== d || y[24] !== h || y[25] !== p || y[26] !== j || y[27] !== N ? (g = {
    queryKey: h,
    queryFn: p,
    enabled: d,
    staleTime: j,
    gcTime: 6e5,
    retry: 1,
    retryDelay: 2e3,
    refetchInterval: N
  }, y[23] = d, y[24] = h, y[25] = p, y[26] = j, y[27] = N, y[28] = g) : g = y[28];
  let {
    data: _,
    isLoading: k,
    error: S
  } = f(g);
  return y[29] !== _ ? (v = _ || [], y[29] = _, y[30] = v) : v = y[30], y[31] !== k || y[32] !== v || y[33] !== S ? (b = {
    candlesticks: v,
    isLoading: k,
    error: S
  }, y[31] = k, y[32] = v, y[33] = S, y[34] = b) : b = y[34], b;
}};
}

function frame521368_3(imports,dom,loadModule){
const IntersectionObserver=dom.IntersectionObserver;
const e={A:loadModule};
var t = imports(445242),
  r = imports(690877),
  a = imports(38279),
  l = imports(636882),
  n = imports(997627),
  i = imports(693908);
return{"f":(e, s, o, c) => {
  let d,
    u,
    m,
    h,
    f,
    x,
    p,
    v,
    b,
    g,
    y = (0, t.c)(35);
  y[0] !== s ? (d = null != s && Number.isFinite(s) && s > 0 && (0, i.a)(s), y[0] = s, y[1] = d) : d = y[1];
  let j = d;
  if (y[2] !== s || y[3] !== e || y[4] !== c?.chainId || y[5] !== c?.timeframe || y[6] !== j || y[7] !== o) {
    let t,
      n = null != s && Number.isFinite(s) && s > 0 ? (0, i.Y)(s) : {
        timeframe: a.v.COIN_LINE_CHART.TIMEFRAME,
        width: a.v.COIN_LINE_CHART.WIDTH
      },
      d = j ? (0, i.S)(s) : null;
    x = c?.timeframe ?? n.timeframe, m = o ?? n.width;
    let p = c?.chainId;
    y[13] !== s || y[14] !== e || y[15] !== p ? (t = (0, l.f)({
      coinAddress: e,
      coinCreatedTimestamp: s,
      chainId: p
    }), y[13] = s, y[14] = e, y[15] = p, y[16] = t) : t = y[16], u = t, f = r.useQuery, h = j ? [...a.Q.COIN_CANDLES({
      coinAddress: e,
      coinCreatedTimestamp: s ?? 0,
      interval: d.interval,
      limit: d.limit
    }), "sparklineCandlesticks", c?.chainId ?? null] : [...a.Q.COIN_LINE_CHART({
      coinAddress: e,
      coinCreatedTimestamp: s ?? 0,
      timeframe: x,
      width: m
    }), "sparklineCandlesticks", c?.chainId ?? null], y[2] = s, y[3] = e, y[4] = c?.chainId, y[5] = c?.timeframe, y[6] = j, y[7] = o, y[8] = u, y[9] = m, y[10] = h, y[11] = f, y[12] = x;
  } else u = y[8], m = y[9], h = y[10], f = y[11], x = y[12];
  y[17] !== s || y[18] !== e || y[19] !== c?.chainId || y[20] !== m || y[21] !== x ? (p = () => (0, n.u)({
    coinAddress: e,
    coinCreatedTimestamp: s ?? 0,
    chainId: c?.chainId,
    timeframe: x,
    width: m
  }), y[17] = s, y[18] = e, y[19] = c?.chainId, y[20] = m, y[21] = x, y[22] = p) : p = y[22];
  let N = c?.staleTime ?? (j ? 15e3 : 3e5),
    w = c?.refetchInterval;
  y[23] !== u || y[24] !== h || y[25] !== p || y[26] !== N || y[27] !== w ? (v = {
    queryKey: h,
    queryFn: p,
    enabled: u,
    staleTime: N,
    gcTime: 6e5,
    retry: 1,
    retryDelay: 2e3,
    refetchInterval: w
  }, y[23] = u, y[24] = h, y[25] = p, y[26] = N, y[27] = w, y[28] = v) : v = y[28];
  let {
    data: k,
    isLoading: _,
    error: C
  } = f(v);
  return y[29] !== k ? (b = k || [], y[29] = k, y[30] = b) : b = y[30], y[31] !== _ || y[32] !== b || y[33] !== C ? (g = {
    candlesticks: b,
    isLoading: _,
    error: C
  }, y[31] = _, y[32] = b, y[33] = C, y[34] = g) : g = y[34], g;
}};
}

function frame679553_0(imports,dom,loadModule){
const IntersectionObserver=dom.IntersectionObserver;
const e={A:loadModule};
var t = imports(732486),
  r = imports(445242),
  i = imports(453706),
  a = imports(352386),
  n = imports(338319);
let s = (0, i.default)(() => e.A(179843).then(e => e.LineChartCellChart), {
    loadableGenerated: {
      modules: [708937]
    },
    ssr: !1
  }),
  l = e => {
    let i,
      a,
      s,
      l = (0, r.c)(5),
      {
        className: o
      } = e;
    return l[0] !== o ? (i = (0, n.c)("flex h-8 w-16 items-center justify-center", o), l[0] = o, l[1] = i) : i = l[1], l[2] === Symbol.for("react.memo_cache_sentinel") ? (a = (0, t.jsx)("div", {
      className: "h-6 w-14 animate-pulse rounded bg-muted/60"
    }), l[2] = a) : a = l[2], l[3] !== i ? (s = (0, t.jsx)("div", {
      className: i,
      children: a
    }), l[3] = i, l[4] = s) : s = l[4], s;
  },
  o = e => {
    let i,
      a,
      s = (0, r.c)(4),
      {
        className: l
      } = e;
    return s[0] !== l ? (i = (0, n.c)("flex h-8 w-16 items-center justify-center text-xs text-text-tertiary", l), s[0] = l, s[1] = i) : i = s[1], s[2] !== i ? (a = (0, t.jsx)("div", {
      className: i,
      children: "-"
    }), s[2] = i, s[3] = a) : a = s[3], a;
  },
  c = a.default.memo(e => {
    let i,
      a,
      c,
      m = (0, r.c)(11),
      {
        data: d,
        isLoading: u,
        error: h,
        className: x
      } = e;
    if (void 0 !== u && u) {
      let e;
      return m[0] !== x ? (e = (0, t.jsx)(l, {
        className: x
      }), m[0] = x, m[1] = e) : e = m[1], e;
    }
    if ((void 0 === h ? null : h) || !d || d.length <= 1) {
      let e;
      return m[2] !== x ? (e = (0, t.jsx)(o, {
        className: x
      }), m[2] = x, m[3] = e) : e = m[3], e;
    }
    return m[4] !== x ? (i = (0, n.c)("relative flex h-8 w-16 items-center justify-self-center transition-all duration-200 hover:scale-110 hover:brightness-110", x), m[4] = x, m[5] = i) : i = m[5], m[6] !== d ? (a = (0, t.jsx)(s, {
      data: d
    }), m[6] = d, m[7] = a) : a = m[7], m[8] !== i || m[9] !== a ? (c = (0, t.jsx)("div", {
      className: i,
      children: a
    }), m[8] = i, m[9] = a, m[10] = c) : c = m[10], c;
  }, (e, t) => e.isLoading === t.isLoading && e.error === t.error && e.className === t.className && (e.data && t.data ? e.data.length === t.data.length && e.data[e.data.length - 1]?.close === t.data[t.data.length - 1]?.close : e.data === t.data));
return{"f":c};
}

function frame679553_1(imports,dom,loadModule){
const IntersectionObserver=dom.IntersectionObserver;
const e={A:loadModule};
var t = imports(732486),
  n = imports(445242),
  r = imports(453706),
  i = imports(352386),
  o = imports(338319);
let s = (0, r.default)(() => e.A(179843).then(e => e.LineChartCellChart), {
    loadableGenerated: {
      modules: [708937]
    },
    ssr: !1
  }),
  a = e => {
    let r,
      i,
      s,
      a = (0, n.c)(5),
      {
        className: l
      } = e;
    return a[0] !== l ? (r = (0, o.c)("flex h-8 w-16 items-center justify-center", l), a[0] = l, a[1] = r) : r = a[1], a[2] === Symbol.for("react.memo_cache_sentinel") ? (i = (0, t.jsx)("div", {
      className: "h-6 w-14 animate-pulse rounded bg-muted/60"
    }), a[2] = i) : i = a[2], a[3] !== r ? (s = (0, t.jsx)("div", {
      className: r,
      children: i
    }), a[3] = r, a[4] = s) : s = a[4], s;
  },
  l = e => {
    let r,
      i,
      s = (0, n.c)(4),
      {
        className: a
      } = e;
    return s[0] !== a ? (r = (0, o.c)("flex h-8 w-16 items-center justify-center text-xs text-text-tertiary", a), s[0] = a, s[1] = r) : r = s[1], s[2] !== r ? (i = (0, t.jsx)("div", {
      className: r,
      children: "-"
    }), s[2] = r, s[3] = i) : i = s[3], i;
  },
  c = i.default.memo(e => {
    let r,
      i,
      c,
      u = (0, n.c)(11),
      {
        data: d,
        isLoading: m,
        error: E,
        className: f
      } = e;
    if (void 0 !== m && m) {
      let e;
      return u[0] !== f ? (e = (0, t.jsx)(a, {
        className: f
      }), u[0] = f, u[1] = e) : e = u[1], e;
    }
    if ((void 0 === E ? null : E) || !d || d.length <= 1) {
      let e;
      return u[2] !== f ? (e = (0, t.jsx)(l, {
        className: f
      }), u[2] = f, u[3] = e) : e = u[3], e;
    }
    return u[4] !== f ? (r = (0, o.c)("relative flex h-8 w-16 items-center justify-self-center transition-all duration-200 hover:scale-110 hover:brightness-110", f), u[4] = f, u[5] = r) : r = u[5], u[6] !== d ? (i = (0, t.jsx)(s, {
      data: d
    }), u[6] = d, u[7] = i) : i = u[7], u[8] !== r || u[9] !== i ? (c = (0, t.jsx)("div", {
      className: r,
      children: i
    }), u[8] = r, u[9] = i, u[10] = c) : c = u[10], c;
  }, (e, t) => e.isLoading === t.isLoading && e.error === t.error && e.className === t.className && (e.data && t.data ? e.data.length === t.data.length && e.data[e.data.length - 1]?.close === t.data[t.data.length - 1]?.close : e.data === t.data));
return{"f":c};
}

function frame679553_2(imports,dom,loadModule){
const IntersectionObserver=dom.IntersectionObserver;
const e={A:loadModule};
var t = imports(732486),
  r = imports(445242),
  i = imports(453706),
  a = imports(352386),
  n = imports(338319);
let l = (0, i.default)(() => e.A(179843).then(e => e.LineChartCellChart), {
    loadableGenerated: {
      modules: [708937]
    },
    ssr: !1
  }),
  s = e => {
    let i,
      a,
      l,
      s = (0, r.c)(5),
      {
        className: o
      } = e;
    return s[0] !== o ? (i = (0, n.c)("flex h-8 w-16 items-center justify-center", o), s[0] = o, s[1] = i) : i = s[1], s[2] === Symbol.for("react.memo_cache_sentinel") ? (a = (0, t.jsx)("div", {
      className: "h-6 w-14 animate-pulse rounded bg-muted/60"
    }), s[2] = a) : a = s[2], s[3] !== i ? (l = (0, t.jsx)("div", {
      className: i,
      children: a
    }), s[3] = i, s[4] = l) : l = s[4], l;
  },
  o = e => {
    let i,
      a,
      l = (0, r.c)(4),
      {
        className: s
      } = e;
    return l[0] !== s ? (i = (0, n.c)("flex h-8 w-16 items-center justify-center text-xs text-text-tertiary", s), l[0] = s, l[1] = i) : i = l[1], l[2] !== i ? (a = (0, t.jsx)("div", {
      className: i,
      children: "-"
    }), l[2] = i, l[3] = a) : a = l[3], a;
  },
  c = a.default.memo(e => {
    let i,
      a,
      c,
      m = (0, r.c)(11),
      {
        data: d,
        isLoading: u,
        error: h,
        className: f
      } = e;
    if (void 0 !== u && u) {
      let e;
      return m[0] !== f ? (e = (0, t.jsx)(s, {
        className: f
      }), m[0] = f, m[1] = e) : e = m[1], e;
    }
    if ((void 0 === h ? null : h) || !d || d.length <= 1) {
      let e;
      return m[2] !== f ? (e = (0, t.jsx)(o, {
        className: f
      }), m[2] = f, m[3] = e) : e = m[3], e;
    }
    return m[4] !== f ? (i = (0, n.c)("relative flex h-8 w-16 items-center justify-self-center transition-all duration-200 hover:scale-110 hover:brightness-110", f), m[4] = f, m[5] = i) : i = m[5], m[6] !== d ? (a = (0, t.jsx)(l, {
      data: d
    }), m[6] = d, m[7] = a) : a = m[7], m[8] !== i || m[9] !== a ? (c = (0, t.jsx)("div", {
      className: i,
      children: a
    }), m[8] = i, m[9] = a, m[10] = c) : c = m[10], c;
  }, (e, t) => e.isLoading === t.isLoading && e.error === t.error && e.className === t.className && (e.data && t.data ? e.data.length === t.data.length && e.data[e.data.length - 1]?.close === t.data[t.data.length - 1]?.close : e.data === t.data));
return{"f":c};
}

function frame679553_3(imports,dom,loadModule){
const IntersectionObserver=dom.IntersectionObserver;
const e={A:loadModule};
var t = imports(732486),
  r = imports(445242),
  a = imports(453706),
  l = imports(352386),
  n = imports(338319);
let i = (0, a.default)(() => e.A(179843).then(e => e.LineChartCellChart), {
    loadableGenerated: {
      modules: [708937]
    },
    ssr: !1
  }),
  s = e => {
    let a,
      l,
      i,
      s = (0, r.c)(5),
      {
        className: o
      } = e;
    return s[0] !== o ? (a = (0, n.c)("flex h-8 w-16 items-center justify-center", o), s[0] = o, s[1] = a) : a = s[1], s[2] === Symbol.for("react.memo_cache_sentinel") ? (l = (0, t.jsx)("div", {
      className: "h-6 w-14 animate-pulse rounded bg-muted/60"
    }), s[2] = l) : l = s[2], s[3] !== a ? (i = (0, t.jsx)("div", {
      className: a,
      children: l
    }), s[3] = a, s[4] = i) : i = s[4], i;
  },
  o = e => {
    let a,
      l,
      i = (0, r.c)(4),
      {
        className: s
      } = e;
    return i[0] !== s ? (a = (0, n.c)("flex h-8 w-16 items-center justify-center text-xs text-text-tertiary", s), i[0] = s, i[1] = a) : a = i[1], i[2] !== a ? (l = (0, t.jsx)("div", {
      className: a,
      children: "-"
    }), i[2] = a, i[3] = l) : l = i[3], l;
  },
  c = l.default.memo(e => {
    let a,
      l,
      c,
      d = (0, r.c)(11),
      {
        data: u,
        isLoading: m,
        error: h,
        className: f
      } = e;
    if (void 0 !== m && m) {
      let e;
      return d[0] !== f ? (e = (0, t.jsx)(s, {
        className: f
      }), d[0] = f, d[1] = e) : e = d[1], e;
    }
    if ((void 0 === h ? null : h) || !u || u.length <= 1) {
      let e;
      return d[2] !== f ? (e = (0, t.jsx)(o, {
        className: f
      }), d[2] = f, d[3] = e) : e = d[3], e;
    }
    return d[4] !== f ? (a = (0, n.c)("relative flex h-8 w-16 items-center justify-self-center transition-all duration-200 hover:scale-110 hover:brightness-110", f), d[4] = f, d[5] = a) : a = d[5], d[6] !== u ? (l = (0, t.jsx)(i, {
      data: u
    }), d[6] = u, d[7] = l) : l = d[7], d[8] !== a || d[9] !== l ? (c = (0, t.jsx)("div", {
      className: a,
      children: l
    }), d[8] = a, d[9] = l, d[10] = c) : c = d[10], c;
  }, (e, t) => e.isLoading === t.isLoading && e.error === t.error && e.className === t.className && (e.data && t.data ? e.data.length === t.data.length && e.data[e.data.length - 1]?.close === t.data[t.data.length - 1]?.close : e.data === t.data));
return{"f":c};
}

function frame386017_0(imports,dom,loadModule){
const IntersectionObserver=dom.IntersectionObserver;
const e={A:loadModule};
var t = imports(445242),
  r = imports(352386);
function a(e) {
  return e.isIntersecting;
}
function i() {
  return "u" < typeof IntersectionObserver;
}
return{"f":function (e, n) {
  let l,
    s,
    o,
    d = (0, t.c)(7);
  d[0] !== n ? (l = void 0 === n ? {} : n, d[0] = n, d[1] = l) : l = d[1];
  let {
      rootMargin: u
    } = l,
    c = void 0 === u ? "200px 0px" : u,
    [m, p] = (0, r.useState)(i);
  return d[2] !== e || d[3] !== c || d[4] !== m ? (s = () => {
    if (m) return;
    let t = e.current;
    if (!t) return;
    let r = new IntersectionObserver(e => {
      e.some(a) && (r.disconnect(), p(!0));
    }, {
      rootMargin: c
    });
    return r.observe(t), () => r.disconnect();
  }, o = [e, m, c], d[2] = e, d[3] = c, d[4] = m, d[5] = s, d[6] = o) : (s = d[5], o = d[6]), (0, r.useEffect)(s, o), m;
}};
}

function frame386017_1(imports,dom,loadModule){
const IntersectionObserver=dom.IntersectionObserver;
const e={A:loadModule};
var t = imports(445242),
  a = imports(352386);
function i(e) {
  return e.isIntersecting;
}
function l() {
  return "u" < typeof IntersectionObserver;
}
return{"f":function (e, r) {
  let n,
    o,
    s,
    d = (0, t.c)(7);
  d[0] !== r ? (n = void 0 === r ? {} : r, d[0] = r, d[1] = n) : n = d[1];
  let {
      rootMargin: c
    } = n,
    u = void 0 === c ? "200px 0px" : c,
    [m, p] = (0, a.useState)(l);
  return d[2] !== e || d[3] !== u || d[4] !== m ? (o = () => {
    if (m) return;
    let t = e.current;
    if (!t) return;
    let a = new IntersectionObserver(e => {
      e.some(i) && (a.disconnect(), p(!0));
    }, {
      rootMargin: u
    });
    return a.observe(t), () => a.disconnect();
  }, s = [e, m, u], d[2] = e, d[3] = u, d[4] = m, d[5] = o, d[6] = s) : (o = d[5], s = d[6]), (0, a.useEffect)(o, s), m;
}};
}

function frame386017_2(imports,dom,loadModule){
const IntersectionObserver=dom.IntersectionObserver;
const e={A:loadModule};
var t = imports(445242),
  n = imports(352386);
function r(e) {
  return e.isIntersecting;
}
function i() {
  return "u" < typeof IntersectionObserver;
}
return{"f":function (e, o) {
  let s,
    a,
    l,
    c = (0, t.c)(7);
  c[0] !== o ? (s = void 0 === o ? {} : o, c[0] = o, c[1] = s) : s = c[1];
  let {
      rootMargin: u
    } = s,
    d = void 0 === u ? "200px 0px" : u,
    [m, E] = (0, n.useState)(i);
  return c[2] !== e || c[3] !== d || c[4] !== m ? (a = () => {
    if (m) return;
    let t = e.current;
    if (!t) return;
    let n = new IntersectionObserver(e => {
      e.some(r) && (n.disconnect(), E(!0));
    }, {
      rootMargin: d
    });
    return n.observe(t), () => n.disconnect();
  }, l = [e, m, d], c[2] = e, c[3] = d, c[4] = m, c[5] = a, c[6] = l) : (a = c[5], l = c[6]), (0, n.useEffect)(a, l), m;
}};
}

function frame386017_3(imports,dom,loadModule){
const IntersectionObserver=dom.IntersectionObserver;
const e={A:loadModule};
var t = imports(445242),
  r = imports(352386);
function i(e) {
  return e.isIntersecting;
}
function a() {
  return "u" < typeof IntersectionObserver;
}
return{"f":function (e, n) {
  let l,
    s,
    o,
    c = (0, t.c)(7);
  c[0] !== n ? (l = void 0 === n ? {} : n, c[0] = n, c[1] = l) : l = c[1];
  let {
      rootMargin: m
    } = l,
    d = void 0 === m ? "200px 0px" : m,
    [u, h] = (0, r.useState)(a);
  return c[2] !== e || c[3] !== d || c[4] !== u ? (s = () => {
    if (u) return;
    let t = e.current;
    if (!t) return;
    let r = new IntersectionObserver(e => {
      e.some(i) && (r.disconnect(), h(!0));
    }, {
      rootMargin: d
    });
    return r.observe(t), () => r.disconnect();
  }, o = [e, u, d], c[2] = e, c[3] = d, c[4] = u, c[5] = s, c[6] = o) : (s = c[5], o = c[6]), (0, r.useEffect)(s, o), u;
}};
}

function frame386017_4(imports,dom,loadModule){
const IntersectionObserver=dom.IntersectionObserver;
const e={A:loadModule};
var t = imports(445242),
  r = imports(352386);
function a(e) {
  return e.isIntersecting;
}
function l() {
  return "u" < typeof IntersectionObserver;
}
return{"f":function (e, n) {
  let i,
    s,
    o,
    c = (0, t.c)(7);
  c[0] !== n ? (i = void 0 === n ? {} : n, c[0] = n, c[1] = i) : i = c[1];
  let {
      rootMargin: d
    } = i,
    u = void 0 === d ? "200px 0px" : d,
    [m, h] = (0, r.useState)(l);
  return c[2] !== e || c[3] !== u || c[4] !== m ? (s = () => {
    if (m) return;
    let t = e.current;
    if (!t) return;
    let r = new IntersectionObserver(e => {
      e.some(a) && (r.disconnect(), h(!0));
    }, {
      rootMargin: u
    });
    return r.observe(t), () => r.disconnect();
  }, o = [e, m, u], c[2] = e, c[3] = u, c[4] = m, c[5] = s, c[6] = o) : (s = c[5], o = c[6]), (0, r.useEffect)(s, o), m;
}};
}

function frame170450_0(imports,dom,loadModule){
const IntersectionObserver=dom.IntersectionObserver;
const e={A:loadModule};
var t = imports(352386);
let r = () => () => {},
  a = () => !0,
  i = () => !1;
return{"f":() => (0, t.useSyncExternalStore)(r, a, i)};
}

function frame832914_0(imports,dom,loadModule){
const IntersectionObserver=dom.IntersectionObserver;
const i={A:loadModule};
var e = imports(732486),
  t = imports(445242),
  s = imports(352386),
  o = imports(116368),
  a = imports(612531),
  r = imports(671603),
  l = imports(25264),
  c = imports(998188),
  n = (0, a.f)({
    chartName: "AreaChart",
    GraphicalChild: o.f,
    axisComponents: [{
      axisType: "xAxis",
      AxisComp: r.f
    }, {
      axisType: "yAxis",
      AxisComp: l.f
    }],
    formatAxisMap: c.t
  }),
  p = imports(45143),
  f = imports(216934);
function m(i, e) {
  return {
    timestamp: i.time || i.timestamp,
    price: 0 === e ? i.open : i.close
  };
}
function d(i) {
  return i.price;
}
function h(i, t) {
  return (0, e.jsx)("stop", {
    offset: i.offset,
    stopColor: i.color,
    stopOpacity: i.opacity
  }, t);
}
return{"LineChartCellChart":i => {
  let a,
    r,
    c,
    x,
    u,
    y,
    A,
    C,
    j,
    T,
    b,
    g,
    v,
    I,
    K,
    M,
    O,
    k,
    B,
    G = (0, t.c)(48),
    {
      data: P
    } = i,
    R = s.default.useId();
  if (G[0] !== R) {
    let i;
    G[2] === Symbol.for("react.memo_cache_sentinel") ? (i = /:/g, G[2] = i) : i = G[2], a = R.replace(i, ""), G[0] = R, G[1] = a;
  } else a = G[1];
  let S = a;
  if (G[3] !== P || G[4] !== S) {
    let i,
      e,
      t,
      s,
      o,
      a = [{
        offset: "0%",
        color: o = x = (0, f.f)().positive,
        opacity: 1
      }, {
        offset: "100%",
        color: o,
        opacity: 0
      }];
    if (G[18] !== P) {
      let s = (i = P.map(m)).map(d);
      e = Math.min(...s), t = Math.max(...s), G[18] = P, G[19] = i, G[20] = e, G[21] = t;
    } else i = G[19], e = G[20], t = G[21];
    let l = t,
      K = (l - e) * .05 || .01 * l,
      M = e - K,
      O = l + K;
    G[22] !== M || G[23] !== O ? (s = [M, O], G[22] = M, G[23] = O, G[24] = s) : s = G[24], I = s, c = p.f, u = "100%", y = "100%", r = n, v = i, A = S, C = "0", j = "0", T = "0", b = "1", g = a.map(h), G[3] = P, G[4] = S, G[5] = r, G[6] = c, G[7] = x, G[8] = u, G[9] = y, G[10] = A, G[11] = C, G[12] = j, G[13] = T, G[14] = b, G[15] = g, G[16] = v, G[17] = I;
  } else r = G[5], c = G[6], x = G[7], u = G[8], y = G[9], A = G[10], C = G[11], j = G[12], T = G[13], b = G[14], g = G[15], v = G[16], I = G[17];
  G[25] !== A || G[26] !== C || G[27] !== j || G[28] !== T || G[29] !== b || G[30] !== g ? (K = (0, e.jsx)("defs", {
    children: (0, e.jsx)("linearGradient", {
      id: A,
      x1: C,
      y1: j,
      x2: T,
      y2: b,
      children: g
    })
  }), G[25] = A, G[26] = C, G[27] = j, G[28] = T, G[29] = b, G[30] = g, G[31] = K) : K = G[31];
  let U = `url(#${S})`;
  return G[32] !== x || G[33] !== U ? (M = (0, e.jsx)(o.f, {
    type: "linear",
    dataKey: "price",
    stroke: x,
    strokeWidth: 1.5,
    fill: U,
    isAnimationActive: !1,
    yAxisId: "price"
  }), G[32] = x, G[33] = U, G[34] = M) : M = G[34], G[35] !== I ? (O = (0, e.jsx)(l.f, {
    yAxisId: "price",
    domain: I,
    hide: !0
  }), G[35] = I, G[36] = O) : O = G[36], G[37] !== r || G[38] !== K || G[39] !== M || G[40] !== O || G[41] !== v ? (k = (0, e.jsxs)(r, {
    data: v,
    children: [K, M, O]
  }), G[37] = r, G[38] = K, G[39] = M, G[40] = O, G[41] = v, G[42] = k) : k = G[42], G[43] !== c || G[44] !== u || G[45] !== y || G[46] !== k ? (B = (0, e.jsx)(c, {
    width: u,
    height: y,
    children: k
  }), G[43] = c, G[44] = u, G[45] = y, G[46] = k, G[47] = B) : B = G[47], B;
}};
}

function frame832914_1(imports,dom,loadModule){
const IntersectionObserver=dom.IntersectionObserver;
const e={A:loadModule};
var t = imports(732486),
  n = imports(445242),
  r = imports(352386),
  o = imports(116368),
  i = imports(612531),
  s = imports(671603),
  c = imports(25264),
  a = imports(998188),
  f = (0, i.f)({
    chartName: "AreaChart",
    GraphicalChild: o.f,
    axisComponents: [{
      axisType: "xAxis",
      AxisComp: s.f
    }, {
      axisType: "yAxis",
      AxisComp: c.f
    }],
    formatAxisMap: a.t
  }),
  l = imports(45143),
  p = imports(216934);
function u(e, t) {
  return {
    timestamp: e.time || e.timestamp,
    price: 0 === t ? e.open : e.close
  };
}
function h(e) {
  return e.price;
}
function v(e, n) {
  return (0, t.jsx)("stop", {
    offset: e.offset,
    stopColor: e.color,
    stopOpacity: e.opacity
  }, n);
}
return{"LineChartCellChart":e => {
  let i,
    s,
    a,
    y,
    m,
    x,
    d,
    _,
    g,
    A,
    b,
    C,
    j,
    w,
    O,
    T,
    L,
    P,
    k,
    S = (0, n.c)(48),
    {
      data: E
    } = e,
    I = r.default.useId();
  if (S[0] !== I) {
    let e;
    S[2] === Symbol.for("react.memo_cache_sentinel") ? (e = /:/g, S[2] = e) : e = S[2], i = I.replace(e, ""), S[0] = I, S[1] = i;
  } else i = S[1];
  let K = i;
  if (S[3] !== E || S[4] !== K) {
    let e,
      t,
      n,
      r,
      o,
      i = [{
        offset: "0%",
        color: o = y = (0, p.f)().positive,
        opacity: 1
      }, {
        offset: "100%",
        color: o,
        opacity: 0
      }];
    if (S[18] !== E) {
      let r = (e = E.map(u)).map(h);
      t = Math.min(...r), n = Math.max(...r), S[18] = E, S[19] = e, S[20] = t, S[21] = n;
    } else e = S[19], t = S[20], n = S[21];
    let c = n,
      O = (c - t) * .05 || .01 * c,
      T = t - O,
      L = c + O;
    S[22] !== T || S[23] !== L ? (r = [T, L], S[22] = T, S[23] = L, S[24] = r) : r = S[24], w = r, a = l.f, m = "100%", x = "100%", s = f, j = e, d = K, _ = "0", g = "0", A = "0", b = "1", C = i.map(v), S[3] = E, S[4] = K, S[5] = s, S[6] = a, S[7] = y, S[8] = m, S[9] = x, S[10] = d, S[11] = _, S[12] = g, S[13] = A, S[14] = b, S[15] = C, S[16] = j, S[17] = w;
  } else s = S[5], a = S[6], y = S[7], m = S[8], x = S[9], d = S[10], _ = S[11], g = S[12], A = S[13], b = S[14], C = S[15], j = S[16], w = S[17];
  S[25] !== d || S[26] !== _ || S[27] !== g || S[28] !== A || S[29] !== b || S[30] !== C ? (O = (0, t.jsx)("defs", {
    children: (0, t.jsx)("linearGradient", {
      id: d,
      x1: _,
      y1: g,
      x2: A,
      y2: b,
      children: C
    })
  }), S[25] = d, S[26] = _, S[27] = g, S[28] = A, S[29] = b, S[30] = C, S[31] = O) : O = S[31];
  let M = `url(#${K})`;
  return S[32] !== y || S[33] !== M ? (T = (0, t.jsx)(o.f, {
    type: "linear",
    dataKey: "price",
    stroke: y,
    strokeWidth: 1.5,
    fill: M,
    isAnimationActive: !1,
    yAxisId: "price"
  }), S[32] = y, S[33] = M, S[34] = T) : T = S[34], S[35] !== w ? (L = (0, t.jsx)(c.f, {
    yAxisId: "price",
    domain: w,
    hide: !0
  }), S[35] = w, S[36] = L) : L = S[36], S[37] !== s || S[38] !== O || S[39] !== T || S[40] !== L || S[41] !== j ? (P = (0, t.jsxs)(s, {
    data: j,
    children: [O, T, L]
  }), S[37] = s, S[38] = O, S[39] = T, S[40] = L, S[41] = j, S[42] = P) : P = S[42], S[43] !== a || S[44] !== m || S[45] !== x || S[46] !== P ? (k = (0, t.jsx)(a, {
    width: m,
    height: x,
    children: P
  }), S[43] = a, S[44] = m, S[45] = x, S[46] = P, S[47] = k) : k = S[47], k;
}};
}

export const CHART_VARIANTS=Object.freeze({"170450":Object.freeze(["72a61a3e662f4e2995ea53610e55b0658ec866cf82ddca6c904962252fe06ff7"]),"386017":Object.freeze(["d6b9c34a180db4d44c86f047de2f26094a4b3ff5263e0b0c31fbb8e1f13e84ad","8ea9d12526cc15d7b47af077aff21ff6ae43d1c35424f3d289493b6045695c84","d749b567542ed3af01533c4206a8ea8a35e36fb557db7ea800e58ff13567e226","6b00abe779e9d8502a14c75a6c9b5574f4eae130641b9138dc52d15efc256f39","60cdc515e0ec3f800f669f2286bcfcd0c66408901f7331460afc34786d9695a6"]),"454430":Object.freeze(["614e1d58f424bd18fd7f15332f7e454ca49e2048d5832ed93cd8040c43bea819","b2992755c5890a934147d1c7a51f1d824ac7f5c5d17d3b2be8d211ab764b7ca9","8c677ca0b1c46e75ecff831a27becc91d58c1c77b2f186b43e45f658becb66dd"]),"521368":Object.freeze(["033214e7ab7a6368e7fd3910418604c4638cec544c339c60bfa52e4afe2821ba","6a6a2a472e3e55bab066fb14eb8edc756a08c4290bfa9e467f322ad890053f9f","85e5b3c165812b25823a092b0402c52fda891e78c74ccd25ecfe650dbc6d1a17","6a049a7bd9df66642f938770506dedd2663a8d5e22ef5ec963e6762c9fb48e1b"]),"679553":Object.freeze(["37500a511f88ab004f89e228bdeae866cfca662a11319f556c2c8507d4a253f5","bd3aaaf5ed128d22e7c252d11cf6240f4df93b8e3335bf6ce22cf07f2def7eba","568125f604fcd394d8bdf62571830cae765848a8c98122ab06680b05412dd077","5dd1efbd72dcc4b9a68f6b146df3c4fc93a9c882a17bf93c15f9bb57a60a9f9d"]),"832914":Object.freeze(["c39ddacc20fccd376886ef55a6f305062e4a2ed76de5ea59dff4d2eb4337ad46","4d43be60506c247c698b9d94dff9ee4e675bff5ff815df0390639ec74477cfd2"])});
export const MAIN_CAPTURE_CHART_CONTEXT=Object.freeze({"170450":"72a61a3e662f4e2995ea53610e55b0658ec866cf82ddca6c904962252fe06ff7","386017":"d749b567542ed3af01533c4206a8ea8a35e36fb557db7ea800e58ff13567e226","454430":"614e1d58f424bd18fd7f15332f7e454ca49e2048d5832ed93cd8040c43bea819","521368":"6a6a2a472e3e55bab066fb14eb8edc756a08c4290bfa9e467f322ad890053f9f","679553":"bd3aaaf5ed128d22e7c252d11cf6240f4df93b8e3335bf6ce22cf07f2def7eba","832914":"4d43be60506c247c698b9d94dff9ee4e675bff5ff815df0390639ec74477cfd2"});
// Authored composition of actual source interfaces. No library/service/provider is installed.
export function createLiveChartCell({contexts,React,jsx,compiler,classNames,useQuery,helpers,eligibility,readOHLC,queryKeys,dynamic,loadModule,chartModules,dom}){
 if(!contexts||!React?.default||typeof React.default.memo!=='function'||typeof React.default.useId!=='function'||typeof React.useSyncExternalStore!=='function'||typeof jsx?.jsx!=='function'||typeof compiler?.c!=='function'||typeof classNames!=='function'||typeof useQuery!=='function'||typeof eligibility!=='function'||typeof readOHLC!=='function'||typeof dynamic!=='function'||typeof loadModule!=='function'||!dom||!Object.hasOwn(dom,'IntersectionObserver'))throw new TypeError('actual source contexts/React/query/data/library/DOM capabilities required');
 for(const name of['isYoungCoin','youngCandleWindow','defaultLineWindow'])if(typeof helpers?.[name]!=='function')throw new TypeError('required existing1827 helper '+name);
 if(helpers.CHART_DEFAULTS?.timeframe!=='1w'||helpers.CHART_DEFAULTS?.width!==72||typeof queryKeys?.COIN_CANDLES!=='function'||typeof queryKeys?.COIN_LINE_CHART!=='function')throw new TypeError('actual captured key constructors and existing1827 defaults required');
 for(const id of[116368,612531,671603,25264,998188,45143,216934])if(!Object.hasOwn(chartModules??{},id))throw new TypeError('required actual chart library/palette module '+id);
 const owned=new Map([[352386,React],[732486,jsx],[445242,compiler],[338319,{c:classNames}],[690877,{useQuery}],[636882,{f:eligibility}],[693908,{a:helpers.isYoungCoin,S:helpers.youngCandleWindow,Y:helpers.defaultLineWindow}],[997627,{u:readOHLC}],[38279,{Q:queryKeys,v:{COIN_LINE_CHART:{TIMEFRAME:helpers.CHART_DEFAULTS.timeframe,WIDTH:helpers.CHART_DEFAULTS.width}}}],[453706,{default:dynamic}]]);
 for(const[id,value]of Object.entries(chartModules))if([116368,612531,671603,25264,998188,45143,216934].includes(Number(id)))owned.set(Number(id),value);
 const choices=new Map([["614e1d58f424bd18fd7f15332f7e454ca49e2048d5832ed93cd8040c43bea819",{id:454430,build:frame454430_0}],["b2992755c5890a934147d1c7a51f1d824ac7f5c5d17d3b2be8d211ab764b7ca9",{id:454430,build:frame454430_1}],["8c677ca0b1c46e75ecff831a27becc91d58c1c77b2f186b43e45f658becb66dd",{id:454430,build:frame454430_2}],["033214e7ab7a6368e7fd3910418604c4638cec544c339c60bfa52e4afe2821ba",{id:521368,build:frame521368_0}],["6a6a2a472e3e55bab066fb14eb8edc756a08c4290bfa9e467f322ad890053f9f",{id:521368,build:frame521368_1}],["85e5b3c165812b25823a092b0402c52fda891e78c74ccd25ecfe650dbc6d1a17",{id:521368,build:frame521368_2}],["6a049a7bd9df66642f938770506dedd2663a8d5e22ef5ec963e6762c9fb48e1b",{id:521368,build:frame521368_3}],["37500a511f88ab004f89e228bdeae866cfca662a11319f556c2c8507d4a253f5",{id:679553,build:frame679553_0}],["bd3aaaf5ed128d22e7c252d11cf6240f4df93b8e3335bf6ce22cf07f2def7eba",{id:679553,build:frame679553_1}],["568125f604fcd394d8bdf62571830cae765848a8c98122ab06680b05412dd077",{id:679553,build:frame679553_2}],["5dd1efbd72dcc4b9a68f6b146df3c4fc93a9c882a17bf93c15f9bb57a60a9f9d",{id:679553,build:frame679553_3}],["d6b9c34a180db4d44c86f047de2f26094a4b3ff5263e0b0c31fbb8e1f13e84ad",{id:386017,build:frame386017_0}],["8ea9d12526cc15d7b47af077aff21ff6ae43d1c35424f3d289493b6045695c84",{id:386017,build:frame386017_1}],["d749b567542ed3af01533c4206a8ea8a35e36fb557db7ea800e58ff13567e226",{id:386017,build:frame386017_2}],["6b00abe779e9d8502a14c75a6c9b5574f4eae130641b9138dc52d15efc256f39",{id:386017,build:frame386017_3}],["60cdc515e0ec3f800f669f2286bcfcd0c66408901f7331460afc34786d9695a6",{id:386017,build:frame386017_4}],["72a61a3e662f4e2995ea53610e55b0658ec866cf82ddca6c904962252fe06ff7",{id:170450,build:frame170450_0}],["c39ddacc20fccd376886ef55a6f305062e4a2ed76de5ea59dff4d2eb4337ad46",{id:832914,build:frame832914_0}],["4d43be60506c247c698b9d94dff9ee4e675bff5ff815df0390639ec74477cfd2",{id:832914,build:frame832914_1}]]);
 const imports=id=>{if(owned.has(id))return owned.get(id);const entry=choices.get(contexts[id]);if(!entry||entry.id!==id)throw new TypeError('explicit captured context required for '+id);const value=entry.build(imports,dom,loadModule);owned.set(id,value);return value;};
 return Object.freeze({ChartCell:imports(454430).f,useCandlesticks:imports(521368).f,Display:imports(679553).f,useViewport:imports(386017).f,useClientReady:imports(170450).f,LineChartCellChart:imports(832914).LineChartCellChart});
}
