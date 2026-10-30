// Editable complete MAIN Explore owner; generated from authenticated AST.
// Captured factories stay inert. Initialized namespaces, providers/actions and
// resource acquisition are explicit caller-owned capabilities.
export const REQUIRED_MODULES = Object.freeze([732486,445242,613944,292686,985526,574472,352386,362388,322315,254010,453706,599077,398902,205761,415203,39548,871999,493367,48485,201629,54136,300157,646908,595673,680930,773755,148003,890088,592209,786147,671722,641770,600656,689794,929360,745018,426091,583695,458310,751275,248496,678700,211502,315706,947427,294707,333757,21617,338319,940721,455418,84121,946129,148269,998515,536925,311282,921999,358893,412237,482617,500793,152281,573525,649927,544514,960107,379705,555501,722876,653805,541710,231824,369091,583448,493025,440276,364043,949629,363250,530501,346431,456753,12692]);
export const LAZY_MODULES = Object.freeze([984385,564115,458738,687193,835378,344288,490258,223256,95433]);
export function createExplorePresentation({modules,loadModule,host}) {
  if (!(modules instanceof Map) || typeof loadModule !== 'function' || !host) throw new TypeError('explicit initialized source namespaces, loader and host capabilities required');
  for (const id of REQUIRED_MODULES) if (!modules.has(id)) throw new TypeError('required initialized source namespace '+id);
  for (const name of ["window","document","Date","setTimeout","clearTimeout","fetch","IntersectionObserver"]) if (!Object.hasOwn(host,name)) throw new TypeError('required actual host capability '+name);
  const lookupModule = id => { if (!modules.has(id)) throw new TypeError('unprovided source namespace '+id); return modules.get(id); };
  const {window,document,Date,setTimeout,clearTimeout,fetch,IntersectionObserver}=host;
  var t = lookupModule(732486),
    r = lookupModule(445242),
    l = lookupModule(613944),
    a = lookupModule(292686),
    n = lookupModule(985526),
    i = lookupModule(574472),
    s = lookupModule(352386),
    o = lookupModule(362388),
    c = lookupModule(322315),
    d = lookupModule(254010),
    u = lookupModule(453706),
    m = lookupModule(599077);
  lookupModule(12692);
  var f = lookupModule(398902),
    h = lookupModule(205761),
    p = lookupModule(415203),
    x = lookupModule(39548);
  let b = {
      type: "spring",
      stiffness: 520,
      damping: 42,
      mass: .6
    },
    g = {
      duration: .28,
      ease: "easeOut"
    },
    v = {
      duration: .18,
      ease: "easeIn"
    },
    y = () => loadModule(984385).then(e => e.default);
  function w(e) {
    let l,
      a,
      n = (0, r.c)(7),
      {
        coins: i,
        lastUpdatedMint: s,
        attachCard: o,
        renderItem: c
      } = e;
    return n[0] !== o || n[1] !== i || n[2] !== s || n[3] !== c ? (l = i.map((e, r) => (0, t.jsx)(x.m.div, {
      layout: !0,
      layoutDependency: s,
      initial: {
        opacity: 0,
        y: -8,
        scale: .985
      },
      animate: {
        opacity: 1,
        y: 0,
        scale: 1
      },
      exit: {
        opacity: 0,
        scale: .97,
        transition: v
      },
      transition: {
        layout: b,
        default: g
      },
      ref: o,
      id: e.mint,
      children: c(e, r)
    }, e.mint)), n[0] = o, n[1] = i, n[2] = s, n[3] = c, n[4] = l) : l = n[4], n[5] !== l ? (a = (0, t.jsx)(p.f, {
      features: y,
      children: (0, t.jsx)(h.f, {
        initial: !1,
        mode: "popLayout",
        children: l
      })
    }), n[5] = l, n[6] = a) : a = n[6], a;
  }
  var j = lookupModule(871999),
    _ = lookupModule(493367),
    C = lookupModule(48485),
    N = lookupModule(201629),
    k = lookupModule(54136),
    S = lookupModule(300157),
    M = lookupModule(646908),
    E = lookupModule(595673),
    T = lookupModule(680930),
    A = lookupModule(773755);
  let L = () => {
      let e,
        l = (0, r.c)(1);
      return l[0] === Symbol.for("react.memo_cache_sentinel") ? (e = (0, t.jsx)(t.Fragment, {
        children: [...Array(_.W)].map(F)
      }), l[0] = e) : e = l[0], e;
    },
    I = e => {
      let l,
        a,
        n,
        i,
        o,
        c,
        d,
        u,
        m,
        h,
        p,
        x,
        b,
        g,
        v,
        y,
        _,
        M,
        I,
        F,
        z,
        P,
        V,
        D,
        U,
        $,
        H,
        G = (0, r.c)(83),
        {
          t: K
        } = (0, f.f)(),
        {
          activeMeta: q,
          addToBookmark: X,
          bookmarkedCoinMints: Z,
          bookmarks: J,
          coins: Q,
          isLivePage: Y,
          isWatchlistView: ee,
          lastUpdatedMint: et,
          loading: er,
          onHover: el,
          onManageWatchlistClick: ea,
          sourceScreen: en,
          removeFromBookmark: ei,
          searchTerm: es,
          sort: eo
        } = e,
        ec = void 0 !== ee && ee;
      G[0] !== ec || G[1] !== eo ? (l = (0, E.v5)(eo, ec), G[0] = ec, G[1] = eo, G[2] = l) : l = G[2];
      let ed = l;
      G[3] === Symbol.for("react.memo_cache_sentinel") ? (a = {}, G[3] = a) : a = G[3];
      let [eu, em] = (0, s.useState)(a),
        ef = (e => {
          let t,
            l,
            a = (0, r.c)(4),
            [n, i] = (0, s.useState)(e),
            [o] = (0, s.useState)(R),
            c = (0, s.useRef)(o);
          return 500 !== a[0] || a[1] !== e ? (t = () => {
            let t = setTimeout(() => {
              Date.now() - c.current >= 500 && (i(e), c.current = Date.now());
            }, 500 - (Date.now() - c.current));
            return () => clearTimeout(t);
          }, l = [e, 500], a[0] = 500, a[1] = e, a[2] = t, a[3] = l) : (t = a[2], l = a[3]), (0, s.useEffect)(t, l), n;
        })(eu),
        eh = (0, s.useRef)(null);
      G[4] === Symbol.for("react.memo_cache_sentinel") ? (n = {}, G[4] = n) : n = G[4];
      let ep = (0, s.useRef)(n);
      if (G[5] !== Q) {
        let e = new Set();
        i = Q.filter(t => !e.has(t.mint) && (e.add(t.mint), !0)), G[5] = Q, G[6] = i;
      } else i = G[6];
      let ex = i;
      G[7] !== ex ? (o = ex.map(O), G[7] = ex, G[8] = o) : o = G[8];
      let eb = o,
        eg = ex.length > 0;
      G[9] !== eb || G[10] !== eg ? (c = {
        mints: eb,
        enabled: eg
      }, G[9] = eb, G[10] = eg, G[11] = c) : c = G[11];
      let {
        observe: ev,
        visibleMints: ey,
        seenMints: ew
      } = (0, k.f)(c);
      G[12] !== ey ? (d = new Set(ey), G[12] = ey, G[13] = d) : d = G[13];
      let ej = d;
      if (G[14] !== ex || G[15] !== ej) {
        let e;
        G[17] !== ej ? (e = e => ej.has(e.mint), G[17] = ej, G[18] = e) : e = G[18], u = ex.filter(e), G[14] = ex, G[15] = ej, G[16] = u;
      } else u = G[16];
      let e_ = u;
      (0, C.f)(e_, eg), G[19] !== ew ? (m = new Set(ew), G[19] = ew, G[20] = m) : m = G[20];
      let eC = m;
      G[21] !== ex ? (h = ex.flatMap(W), G[21] = ex, G[22] = h) : h = G[22];
      let eN = h;
      G[23] !== eg ? (p = {
        shouldFetch: eg,
        enablePolling: !0,
        pollingInterval: T.t.POLLING_INTERVAL
      }, G[23] = eg, G[24] = p) : p = G[24], (0, N.f)(eN, p), G[25] !== ev ? (x = e => {
        if (!e) return;
        let t = e.id;
        ep.current[t] = e;
        let r = ev(e);
        return () => {
          delete ep.current[t], r?.();
        };
      }, G[25] = ev, G[26] = x) : x = G[26];
      let ek = x;
      G[27] === Symbol.for("react.memo_cache_sentinel") ? (b = e => {
        let t = {};
        e.forEach(e => {
          t[e.target.id] = e.isIntersecting;
        }), em(e => ({
          ...e,
          ...t
        }));
      }, G[27] = b) : b = G[27];
      let eS = b;
      G[28] === Symbol.for("react.memo_cache_sentinel") ? (g = () => (eh.current = new IntersectionObserver(eS, {
        root: null,
        rootMargin: "0px",
        threshold: 1
      }), () => {
        eh.current && eh.current.disconnect();
      }), v = [eS], G[28] = g, G[29] = v) : (g = G[28], v = G[29]), (0, s.useEffect)(g, v), G[30] !== ex ? (y = () => {
        ex.forEach(e => {
          let t = ep.current[e.mint];
          t && eh.current && eh.current.observe(t);
        });
      }, _ = [ex], G[30] = ex, G[31] = y, G[32] = _) : (y = G[31], _ = G[32]), (0, s.useEffect)(y, _), G[33] !== el ? (M = () => () => {
        el?.(!1);
      }, I = [el], G[33] = el, G[34] = M, G[35] = I) : (M = G[34], I = G[35]), (0, s.useEffect)(M, I), G[36] !== Z ? (F = Z ?? [], G[36] = Z, G[37] = F) : F = G[37], G[38] !== F ? (z = new Set(F), G[38] = F, G[39] = z) : z = G[39];
      let eM = z;
      G[40] !== J ? (P = J?.reduce(B, {}), G[40] = J, G[41] = P) : P = G[41];
      let eE = P;
      G[42] !== q || G[43] !== X || G[44] !== eM || G[45] !== eE || G[46] !== J || G[47] !== ec || G[48] !== et || G[49] !== ea || G[50] !== ei || G[51] !== es || G[52] !== eC || G[53] !== eo || G[54] !== ed || G[55] !== en || G[56] !== ef ? (V = (e, r) => eC.has(e.mint) ? (0, t.jsx)(j.f, {
        coin: e,
        eagerLoadImage: r < 6,
        priorityImage: 0 === r,
        activeMeta: q,
        searchTerm: es,
        shouldAnimate: et === e.mint || et?.split(",").includes(e.mint),
        isInViewport: ef[e.mint] || !1,
        addToBookmark: X,
        removeFromBookmark: ei,
        impression: {
          itemPosition: r,
          marketCap: e.usd_market_cap ? Number(e.usd_market_cap.toFixed(2)) : 0,
          sourceScreen: en,
          rec_id: e.rec_id,
          sourceElement: ed
        },
        isBookmarked: eM.has((0, S.y)({
          mint: e.mint,
          chainId: e.chain_id
        })),
        bookmarks: J,
        bookmarkedItems: eE,
        onManageWatchlistClick: ea,
        sort: eo,
        isWatchlistView: ec
      }) : (0, t.jsx)(A.f, {}), G[42] = q, G[43] = X, G[44] = eM, G[45] = eE, G[46] = J, G[47] = ec, G[48] = et, G[49] = ea, G[50] = ei, G[51] = es, G[52] = eC, G[53] = eo, G[54] = ed, G[55] = en, G[56] = ef, G[57] = V) : V = G[57];
      let eT = V;
      if (!er && 0 === Q.length) {
        let e, r, l, a, n;
        return G[58] === Symbol.for("react.memo_cache_sentinel") ? (e = (0, t.jsxs)("svg", {
          width: "114px",
          className: "mx-auto",
          viewBox: "0 0 539 451",
          fill: "none",
          xmlns: "http://www.w3.org/2000/svg",
          children: [(0, t.jsx)("path", {
            d: "M36 295.5L492 116C492 116 547.5 135 537.5 228C527.5 321 390 372 390 372L300 345L332.5 408.5C267.5 438.5 213.5 452.5 182.5 450.5C151.5 448.5 115.5 449 74 403.5C32.5 358 36 295.5 36 295.5Z",
            fill: "black",
            fillOpacity: "0.1"
          }), (0, t.jsx)("path", {
            d: "M470.947 161.304C432.771 200.378 401.81 229.18 380.427 248.187C369.735 257.69 361.438 264.745 355.831 269.411C355.242 269.901 354.683 270.364 354.154 270.801L233.113 107.167C235.279 105.188 238.461 102.418 243.094 98.6121C257.347 86.902 284.906 65.7353 337.904 28.1688C386.822 -6.50546 437.236 8.80343 467.214 42.2822C497.544 76.1541 505.202 126.243 470.947 161.304Z",
            fill: "white",
            stroke: "#1D3934",
            strokeWidth: "17"
          }), (0, t.jsx)("path", {
            d: "M351.065 149.236C367.757 172.887 375.745 198.897 375.516 221.589C375.288 244.295 366.925 262.971 351.737 273.69C336.548 284.409 316.15 286.032 294.679 278.641C273.223 271.254 251.392 255.013 234.7 231.363C218.008 207.712 210.02 181.702 210.248 159.01C210.477 136.304 218.84 117.628 234.028 106.909C249.217 96.1897 269.615 94.5665 291.085 101.958C312.542 109.345 334.373 125.586 351.065 149.236Z",
            fill: "#E1E1E1",
            stroke: "#1D3934",
            strokeWidth: "17"
          }), (0, t.jsx)("path", {
            d: "M16.0141 246.223C7.54956 186.447 49.3591 131.097 109.398 122.596L219.075 107.065C219.075 107.065 242.161 156.219 249.79 221.618C257.419 287.017 249.728 323.532 249.728 323.532L140.051 339.062C80.0118 347.564 24.4786 305.999 16.0141 246.223Z",
            fill: "#5FCB88"
          }), (0, t.jsx)("path", {
            d: "M110.727 130.019L214.27 115.357C214.602 116.154 214.962 117.031 215.347 117.984C217.577 123.498 220.647 131.564 223.958 141.664C230.587 161.887 238.146 190.155 241.908 222.374C245.694 254.792 245.683 279.958 244.747 296.919C244.279 305.4 243.58 311.832 243.008 316.095C242.991 316.218 242.975 316.34 242.958 316.46L139.208 331.152C83.6668 339.016 32.266 300.367 24.4011 244.826C16.5362 189.285 55.1855 137.884 110.727 130.019Z",
            stroke: "#1D3934",
            strokeWidth: "17"
          }), (0, t.jsx)("path", {
            fillRule: "evenodd",
            clipRule: "evenodd",
            d: "M69.0978 252.344C71.1796 251.763 73.3384 252.979 73.9197 255.061L75.8974 262.144C76.4787 264.226 75.2623 266.385 73.1805 266.966C71.0987 267.548 68.9399 266.331 68.3586 264.249L66.3809 257.166C65.7996 255.084 67.016 252.925 69.0978 252.344ZM79.9079 277.183C81.461 275.68 83.9387 275.721 85.4418 277.274C92.6431 284.715 101.241 289.943 110.217 292.733C112.281 293.374 113.434 295.568 112.792 297.632C112.15 299.696 109.957 300.849 107.893 300.207C97.6304 297.017 87.9063 291.075 79.8173 282.717C78.3141 281.164 78.3547 278.686 79.9079 277.183ZM124.884 300.453C124.554 298.317 126.018 296.318 128.154 295.988L137.353 294.569C139.489 294.239 141.488 295.703 141.818 297.839C142.148 299.976 140.683 301.975 138.547 302.304L129.348 303.724C127.212 304.054 125.213 302.589 124.884 300.453Z",
            fill: "white"
          })]
        }), G[58] = e) : e = G[58], G[59] !== K ? (r = K("web.coin_list.empty_title"), G[59] = K, G[60] = r) : r = G[60], G[61] !== r ? (l = (0, t.jsx)("h2", {
          className: "my-4 text-sm font-bold",
          children: r
        }), G[61] = r, G[62] = l) : l = G[62], G[63] !== Y || G[64] !== K ? (a = (0, t.jsx)("div", {
          className: "mb-4 text-sm",
          children: Y ? (0, t.jsx)("p", {}) : (0, t.jsx)("p", {
            children: K("web.coin_list.empty_search_description")
          })
        }), G[63] = Y, G[64] = K, G[65] = a) : a = G[65], G[66] !== l || G[67] !== a ? (n = (0, t.jsx)("div", {
          className: "flex items-center justify-center",
          children: (0, t.jsx)("div", {
            className: "mx-auto flex h-fit items-center justify-center p-4 text-center text-text-primary",
            children: (0, t.jsxs)("div", {
              className: "",
              children: [e, l, a]
            })
          })
        }), G[66] = l, G[67] = a, G[68] = n) : n = G[68], n;
      }
      return G[69] !== el ? (D = () => el?.(!0), U = () => el?.(!1), G[69] = el, G[70] = D, G[71] = U) : (D = G[70], U = G[71]), G[72] !== ek || G[73] !== Q.length || G[74] !== et || G[75] !== er || G[76] !== eT || G[77] !== ex ? ($ = er && 0 === Q.length ? (0, t.jsx)(L, {}) : (0, t.jsx)(w, {
        coins: ex,
        lastUpdatedMint: et,
        attachCard: ek,
        renderItem: eT
      }), G[72] = ek, G[73] = Q.length, G[74] = et, G[75] = er, G[76] = eT, G[77] = ex, G[78] = $) : $ = G[78], G[79] !== D || G[80] !== U || G[81] !== $ ? (H = (0, t.jsx)("div", {
        className: "mb-8 grid grid-cols-2 gap-x-3 gap-y-5 sm:grid-cols-[repeat(auto-fill,minmax(200px,1fr))] sm:gap-x-4 sm:gap-y-6",
        onMouseEnter: D,
        onMouseLeave: U,
        children: $
      }), G[79] = D, G[80] = U, G[81] = $, G[82] = H) : H = G[82], H;
    };
  function R() {
    return Date.now();
  }
  function F(e, r) {
    return (0, t.jsx)(A.f, {}, r);
  }
  function O(e) {
    return e.mint;
  }
  function W(e) {
    return (0, M.e)(e) || (0, M.X)(e) || (0, M.a)(e) ? [] : [e.mint];
  }
  function B(e, t) {
    return e[t.id] = t.bookmark_items, e;
  }
  var z = lookupModule(148003),
    P = lookupModule(890088),
    V = lookupModule(592209);
  function D(e) {
    let l,
      a,
      n,
      i = (0, r.c)(11),
      {
        partial: s,
        heldOver: o,
        generatedAt: c
      } = e,
      {
        t: d,
        i18n: u
      } = (0, f.f)();
    if (i[0] !== c || i[1] !== o || i[2] !== u || i[3] !== s || i[4] !== d) {
      var m;
      let e;
      l = o ? d("web.home.calls_held_over_notice", {
        time: (m = u.language, Number.isFinite(e = null === c ? 0 / 0 : Date.parse(c)) ? (0, P.r)((0, V.v)(m) ?? "en", {
          timeStyle: "short"
        }).format(e) : "–")
      }) : s ? d("web.home.calls_partial_notice") : null, i[0] = c, i[1] = o, i[2] = u, i[3] = s, i[4] = d, i[5] = l;
    } else l = i[5];
    let h = l,
      p = null === h ? void 0 : "mb-2";
    return i[6] !== h ? (a = null === h ? null : (0, t.jsx)(z.f, {
      density: "comfortable",
      children: h
    }), i[6] = h, i[7] = a) : a = i[7], i[8] !== p || i[9] !== a ? (n = (0, t.jsx)("div", {
      className: p,
      "data-testid": "explore-calls-partial",
      role: "status",
      children: a
    }), i[8] = p, i[9] = a, i[10] = n) : n = i[10], n;
  }
  var U = lookupModule(786147),
    $ = lookupModule(671722);
  function H(e) {
    let l,
      a,
      n,
      i,
      s,
      o,
      c,
      d,
      u,
      m,
      h,
      p = (0, r.c)(31),
      {
        sort: x,
        onRetry: b,
        retrying: g
      } = e,
      v = void 0 !== g && g,
      {
        t: y
      } = (0, f.f)();
    p[0] !== x ? (l = (0, $.V)(x) ?? "movers", p[0] = x, p[1] = l) : l = p[1];
    let w = l;
    if (p[2] !== w || p[3] !== b || p[4] !== v || p[5] !== y) {
      let e,
        t = (0, U.f)(y, $.M[w].labelKey);
      p[13] !== b || p[14] !== v ? (e = () => {
        v || b?.();
      }, p[13] = b, p[14] = v, p[15] = e) : e = p[15], a = e, o = v, c = "flex flex-col items-center rounded-3xl border border-border-secondary px-6 py-12 text-center", d = "home-feed-load-failed", n = "text-sm text-text-tertiary", i = "alert", s = y("web.home.lens_load_failed", {
        lens: t
      }), p[2] = w, p[3] = b, p[4] = v, p[5] = y, p[6] = a, p[7] = n, p[8] = i, p[9] = s, p[10] = o, p[11] = c, p[12] = d;
    } else a = p[6], n = p[7], i = p[8], s = p[9], o = p[10], c = p[11], d = p[12];
    return p[16] !== n || p[17] !== i || p[18] !== s ? (u = (0, t.jsx)("p", {
      className: n,
      role: i,
      children: s
    }), p[16] = n, p[17] = i, p[18] = s, p[19] = u) : u = p[19], p[20] !== a || p[21] !== b || p[22] !== v || p[23] !== y ? (m = b ? (0, t.jsx)("button", {
      "aria-disabled": v || void 0,
      className: "mt-3 rounded-full border border-border-secondary px-4 py-1.5 text-xs font-semibold text-text-primary transition-colors hover:bg-bg-tertiary aria-disabled:opacity-60",
      onClick: a,
      type: "button",
      children: y("web.common.try_again")
    }) : null, p[20] = a, p[21] = b, p[22] = v, p[23] = y, p[24] = m) : m = p[24], p[25] !== m || p[26] !== o || p[27] !== c || p[28] !== d || p[29] !== u ? (h = (0, t.jsxs)("div", {
      "aria-busy": o,
      className: c,
      "data-testid": d,
      children: [u, m]
    }), p[25] = m, p[26] = o, p[27] = c, p[28] = d, p[29] = u, p[30] = h) : h = p[30], h;
  }
  var G = lookupModule(641770),
    K = lookupModule(600656),
    q = lookupModule(689794),
    X = lookupModule(929360),
    Z = lookupModule(745018),
    J = lookupModule(426091);
  function Q(e, t) {
    if (e <= 1) {
      let e = [1];
      return t && e.push(2, "ellipsis"), e;
    }
    if (2 === e) {
      let e = [1, 2];
      return t && e.push(3, "ellipsis"), e;
    }
    if (3 === e) {
      let e = [1, 2, 3];
      return t && e.push(4, "ellipsis"), e;
    }
    let r = [1, "ellipsis", e - 1, e];
    return t && r.push(e + 1, "ellipsis"), r;
  }
  var Y = lookupModule(583695);
  let ee = e => {
    let l,
      a,
      n,
      i,
      s,
      o,
      c,
      d,
      u,
      m = (0, r.c)(75),
      {
        offset: h,
        setOffset: p,
        items: x,
        LIMIT: b,
        loading: g
      } = e,
      {
        t: v
      } = (0, f.f)(),
      y = Math.floor(h / b) + 1,
      w = x.length >= b && !g,
      j = h > 0 && !g;
    if (m[0] !== b || m[1] !== y || m[2] !== w || m[3] !== j || m[4] !== g || m[5] !== h || m[6] !== p || m[7] !== v) {
      let e,
        r,
        d,
        u,
        f,
        x,
        _,
        C,
        N,
        k,
        S,
        M,
        E,
        T,
        A,
        L,
        I = Q(y, w);
      m[15] !== b || m[16] !== g || m[17] !== p ? (e = e => {
        g || p(Math.max(0, (e - 1) * b));
      }, m[15] = b, m[16] = g, m[17] = p, m[18] = e) : e = m[18];
      let R = e,
        F = !j;
      m[19] !== v ? (r = v("web.pagination.go_to_previous_page"), m[19] = v, m[20] = r) : r = m[20];
      let O = !j;
      m[21] !== O ? (d = (0, Y.A)(O), m[21] = O, m[22] = d) : d = m[22], m[23] !== b || m[24] !== j || m[25] !== h || m[26] !== p ? (u = () => {
        j && p(Math.max(0, h - b));
      }, m[23] = b, m[24] = j, m[25] = h, m[26] = p, m[27] = u) : u = m[27], m[28] === Symbol.for("react.memo_cache_sentinel") ? (f = (0, t.jsx)(Z.S, {
        className: "h-4 w-4 shrink-0"
      }), m[28] = f) : f = m[28], m[29] !== v ? (x = v("web.pagination.previous"), m[29] = v, m[30] = x) : x = m[30], m[31] !== x ? (_ = (0, t.jsx)("span", {
        children: x
      }), m[31] = x, m[32] = _) : _ = m[32], m[33] !== d || m[34] !== u || m[35] !== _ || m[36] !== F || m[37] !== r ? (C = (0, t.jsxs)("button", {
        type: "button",
        disabled: F,
        "aria-label": r,
        className: d,
        onClick: u,
        children: [f, _]
      }), m[33] = d, m[34] = u, m[35] = _, m[36] = F, m[37] = r, m[38] = C) : C = m[38];
      let W = C,
        B = !w;
      m[39] !== v ? (N = v("web.pagination.go_to_next_page"), m[39] = v, m[40] = N) : N = m[40];
      let z = !w;
      m[41] !== z ? (k = (0, Y.A)(z), m[41] = z, m[42] = k) : k = m[42], m[43] !== b || m[44] !== w || m[45] !== h || m[46] !== p ? (S = () => {
        w && p(h + b);
      }, m[43] = b, m[44] = w, m[45] = h, m[46] = p, m[47] = S) : S = m[47], m[48] !== v ? (M = v("common.next"), m[48] = v, m[49] = M) : M = m[49], m[50] !== M ? (E = (0, t.jsx)("span", {
        children: M
      }), m[50] = M, m[51] = E) : E = m[51], m[52] === Symbol.for("react.memo_cache_sentinel") ? (T = (0, t.jsx)(Z.kK, {
        className: "h-4 w-4 shrink-0"
      }), m[52] = T) : T = m[52], m[53] !== B || m[54] !== N || m[55] !== k || m[56] !== S || m[57] !== E ? (A = (0, t.jsxs)("button", {
        type: "button",
        disabled: B,
        "aria-label": N,
        className: k,
        onClick: S,
        children: [E, T]
      }), m[53] = B, m[54] = N, m[55] = k, m[56] = S, m[57] = E, m[58] = A) : A = m[58];
      let P = A;
      a = Y.B, o = "mt-4", l = Y.C, n = "mb-20", m[59] !== W ? (i = (0, t.jsx)(Y.w, {
        children: W
      }), m[59] = W, m[60] = i) : i = m[60], m[61] !== y || m[62] !== R || m[63] !== g ? (L = (e, r) => (0, t.jsx)(Y.w, {
        children: "ellipsis" === e ? (0, t.jsx)(Y.z, {}) : (0, t.jsx)("button", {
          type: "button",
          disabled: g,
          "aria-current": e === y ? "page" : void 0,
          className: (0, J.c)((0, Y.$)(e === y), g && "pointer-events-none cursor-not-allowed opacity-50"),
          onClick: () => R(e),
          children: e
        })
      }, `${String(e)}-${r}`), m[61] = y, m[62] = R, m[63] = g, m[64] = L) : L = m[64], s = I.map(L), c = (0, t.jsx)(Y.w, {
        children: P
      }), m[0] = b, m[1] = y, m[2] = w, m[3] = j, m[4] = g, m[5] = h, m[6] = p, m[7] = v, m[8] = l, m[9] = a, m[10] = n, m[11] = i, m[12] = s, m[13] = o, m[14] = c;
    } else l = m[8], a = m[9], n = m[10], i = m[11], s = m[12], o = m[13], c = m[14];
    return m[65] !== l || m[66] !== n || m[67] !== i || m[68] !== s || m[69] !== c ? (d = (0, t.jsxs)(l, {
      className: n,
      children: [i, s, c]
    }), m[65] = l, m[66] = n, m[67] = i, m[68] = s, m[69] = c, m[70] = d) : d = m[70], m[71] !== a || m[72] !== o || m[73] !== d ? (u = (0, t.jsx)(a, {
      className: o,
      children: d
    }), m[71] = a, m[72] = o, m[73] = d, m[74] = u) : u = m[74], u;
  };
  var et = lookupModule(458310);
  let er = e => {
    let l,
      a,
      n,
      i,
      s,
      o,
      c,
      d,
      u,
      m = (0, r.c)(46),
      {
        offset: h,
        setOffset: p,
        items: x,
        LIMIT: b,
        loading: g,
        getHref: v,
        hasNextPage: y
      } = e,
      {
        t: w
      } = (0, f.f)(),
      j = Math.floor(h / b) + 1,
      _ = (y ?? x.length >= b) && !g,
      C = h > 0 && !g;
    if (m[0] !== b || m[1] !== j || m[2] !== v || m[3] !== _ || m[4] !== C || m[5] !== g || m[6] !== h || m[7] !== p || m[8] !== w) {
      let e,
        r,
        d,
        u = Q(j, _),
        f = Math.max(0, h - b),
        x = h + b;
      m[16] !== v || m[17] !== C || m[18] !== f || m[19] !== p || m[20] !== w ? (e = C ? (0, t.jsxs)(et.default, {
        href: v(f),
        rel: "prev",
        "aria-label": w("web.pagination.go_to_previous_page"),
        className: (0, Y.A)(!1),
        onClick: e => {
          e.preventDefault(), p(f);
        },
        children: [(0, t.jsx)(Z.S, {
          className: "h-4 w-4 shrink-0"
        }), (0, t.jsx)("span", {
          children: w("web.pagination.previous")
        })]
      }) : (0, t.jsxs)("span", {
        "aria-disabled": "true",
        "aria-label": w("web.pagination.previous_page_disabled"),
        className: (0, Y.A)(!0),
        children: [(0, t.jsx)(Z.S, {
          className: "h-4 w-4 shrink-0"
        }), (0, t.jsx)("span", {
          children: w("web.pagination.previous")
        })]
      }), m[16] = v, m[17] = C, m[18] = f, m[19] = p, m[20] = w, m[21] = e) : e = m[21];
      let y = e;
      m[22] !== v || m[23] !== _ || m[24] !== x || m[25] !== p || m[26] !== w ? (r = _ ? (0, t.jsxs)(et.default, {
        href: v(x),
        rel: "next",
        "aria-label": w("web.pagination.go_to_next_page"),
        className: (0, Y.A)(!1),
        onClick: e => {
          e.preventDefault(), p(x);
        },
        children: [(0, t.jsx)("span", {
          children: w("common.next")
        }), (0, t.jsx)(Z.kK, {
          className: "h-4 w-4 shrink-0"
        })]
      }) : (0, t.jsxs)("span", {
        "aria-disabled": "true",
        "aria-label": w("web.pagination.next_page_disabled"),
        className: (0, Y.A)(!0),
        children: [(0, t.jsx)("span", {
          children: w("common.next")
        }), (0, t.jsx)(Z.kK, {
          className: "h-4 w-4 shrink-0"
        })]
      }), m[22] = v, m[23] = _, m[24] = x, m[25] = p, m[26] = w, m[27] = r) : r = m[27];
      let N = r;
      a = Y.B, o = "mt-4", l = Y.C, n = "mb-20", m[28] !== y ? (i = (0, t.jsx)(Y.w, {
        children: y
      }), m[28] = y, m[29] = i) : i = m[29], m[30] !== b || m[31] !== j || m[32] !== v || m[33] !== g || m[34] !== p ? (d = (e, r) => (0, t.jsx)(Y.w, {
        children: "ellipsis" === e ? (0, t.jsx)(Y.z, {}) : g ? (0, t.jsx)("span", {
          "aria-disabled": "true",
          "aria-current": e === j ? "page" : void 0,
          className: (0, J.c)((0, Y.$)(e === j), "pointer-events-none cursor-not-allowed opacity-50"),
          children: e
        }) : (0, t.jsx)(et.default, {
          href: v((e - 1) * b),
          "aria-current": e === j ? "page" : void 0,
          className: (0, J.c)((0, Y.$)(e === j)),
          onClick: t => {
            t.preventDefault(), p((e - 1) * b);
          },
          children: e
        })
      }, `${String(e)}-${r}`), m[30] = b, m[31] = j, m[32] = v, m[33] = g, m[34] = p, m[35] = d) : d = m[35], s = u.map(d), c = (0, t.jsx)(Y.w, {
        children: N
      }), m[0] = b, m[1] = j, m[2] = v, m[3] = _, m[4] = C, m[5] = g, m[6] = h, m[7] = p, m[8] = w, m[9] = l, m[10] = a, m[11] = n, m[12] = i, m[13] = s, m[14] = o, m[15] = c;
    } else l = m[9], a = m[10], n = m[11], i = m[12], s = m[13], o = m[14], c = m[15];
    return m[36] !== l || m[37] !== n || m[38] !== i || m[39] !== s || m[40] !== c ? (d = (0, t.jsxs)(l, {
      className: n,
      children: [i, s, c]
    }), m[36] = l, m[37] = n, m[38] = i, m[39] = s, m[40] = c, m[41] = d) : d = m[41], m[42] !== a || m[43] !== o || m[44] !== d ? (u = (0, t.jsx)(a, {
      className: o,
      children: d
    }), m[42] = a, m[43] = o, m[44] = d, m[45] = u) : u = m[45], u;
  };
  var el = lookupModule(751275),
    ea = lookupModule(248496),
    en = lookupModule(678700),
    ei = lookupModule(211502),
    es = lookupModule(315706);
  let eo = e => {
    (0, es.f)().then(({
      datadogRum: t
    }) => e(t)).catch(() => {});
  };
  var ec = lookupModule(947427),
    ed = lookupModule(294707),
    eu = lookupModule(333757),
    em = lookupModule(21617),
    ef = lookupModule(338319),
    eh = lookupModule(940721);
  let ep = () => {},
    ex = (0, u.default)(() => loadModule(564115).then(e => e.CoinTable), {
      loadableGenerated: {
        modules: [527645]
      },
      ssr: !1,
      loading: () => (0, t.jsx)(K.TableSkeleton, {})
    }),
    eb = (0, u.default)(() => loadModule(458738).then(e => e.CoinTable), {
      loadableGenerated: {
        modules: [397210]
      },
      ssr: !1,
      loading: () => (0, t.jsx)(G.h, {})
    }),
    eg = (0, u.default)(() => loadModule(687193).then(e => e.ExploreTable), {
      loadableGenerated: {
        modules: [356875]
      },
      ssr: !1,
      loading: () => (0, t.jsx)(q.ExploreTableSkeleton, {})
    }),
    ev = (0, u.default)(() => loadModule(835378).then(e => e.MoversCardRail), {
      loadableGenerated: {
        modules: [939344]
      }
    }),
    ey = (0, u.default)(() => loadModule(344288).then(e => e.BookmarksList), {
      loadableGenerated: {
        modules: [251703]
      }
    }),
    ew = (0, u.default)(() => loadModule(490258).then(e => e.ManageWatchlistDialog), {
      loadableGenerated: {
        modules: [796538]
      }
    }),
    ej = (0, u.default)(() => loadModule(223256), {
      loadableGenerated: {
        modules: [521437]
      }
    });
  function e_() {
    let e,
      l = (0, r.c)(1);
    return l[0] === Symbol.for("react.memo_cache_sentinel") ? (e = (0, t.jsx)("div", {
      "aria-busy": "true",
      className: "flex flex-col gap-2 px-3 py-2",
      "data-testid": "perp-watchlist-strip-bones",
      children: [0, 1].map(eC)
    }), l[0] = e) : e = l[0], e;
  }
  function eC(e) {
    return (0, t.jsx)(ea.l, {
      className: "h-10 w-full"
    }, e);
  }
  let eN = (0, u.default)(() => loadModule(95433).then(e => e.PerpWatchlistStrip), {
      loadableGenerated: {
        modules: [877761]
      },
      loading: () => (0, t.jsx)(e_, {})
    }),
    ek = (0, s.memo)(function (e) {
      let l,
        a,
        n,
        i,
        o,
        u,
        f,
        h,
        p,
        x,
        b,
        g,
        v,
        y,
        w,
        j,
        _,
        C,
        N,
        k = (0, r.c)(127),
        {
          coins: S,
          bookmarkedCoins: M,
          bookmarks: E,
          bookmarkedCoinMints: T,
          tableNotificationCoins: A,
          onTableNotificationExpand: L,
          followedHoldersByMint: R,
          rowsMatchBoard: F,
          callsStatus: O,
          sort: W,
          selectedBookmark: B,
          offset: z,
          hasMorePages: P,
          pageSize: V,
          watchlistOffset: U,
          lastUpdatedMint: $,
          athMap: G,
          sourceScreen: K,
          searchTerm: q,
          isLoading: Z,
          isWatchlistLoading: J,
          isWatchlistEmpty: Q,
          feedError: Y,
          onRetryFeed: et,
          bookmarkedCoinsUpdatedAt: ea,
          isUserValid: es,
          hasActiveFilters: e_,
          appliedFiltersKey: eC,
          onAnimationsPause: ek,
          onPageChange: eS,
          onWatchlistPageChange: eM,
          onBookmarkClick: eE,
          onWatchlistBackClick: eT,
          onManageWatchlistClick: eA,
          addToBookmark: eL,
          removeFromBookmark: eI,
          createBookmark: eR,
          deleteBookmark: eF,
          updateBookmarkName: eO,
          isManageWatchlistOpen: eW,
          hasOpenedManageWatchlistDialog: eB,
          setIsManageWatchlistOpen: ez
        } = e;
      k[0] !== A ? (l = void 0 === A ? [] : A, k[0] = A, k[1] = l) : l = k[1];
      let eP = l,
        eV = void 0 === F || F,
        eD = void 0 === V ? eh.s : V,
        eU = void 0 === eC ? "" : eC,
        {
          homeFeed: e$
        } = (0, en.N)(),
        {
          homeLayout: eH
        } = (0, ei.e)(),
        eG = (0, el.y)(),
        eK = (0, m.usePathname)(),
        eq = (0, m.useSearchParams)();
      k[2] !== eD || k[3] !== eK || k[4] !== eq ? (a = e => {
        let t = new URLSearchParams(eq),
          r = Math.floor(Math.max(0, e) / eD) + 1;
        r <= 1 ? t.delete("page") : t.set("page", String(r));
        let l = t.toString();
        return l ? `${eK}?${l}` : eK;
      }, k[2] = eD, k[3] = eK, k[4] = eq, k[5] = a) : a = k[5];
      let eX = a,
        eZ = e$ === en.z.WATCHLIST,
        eJ = (0, d.k)(c.D.WEB_PERPS, !1);
      k[6] !== M || k[7] !== S || k[8] !== eJ || k[9] !== es || k[10] !== eZ ? (n = eZ && es ? ((e, {
        perpsEnabled: t
      }) => {
        let r = [],
          l = [],
          a = 0;
        for (let n of e) {
          if ((0, em.x)(n)) {
            if (!t) continue;
            let e = (0, eu.K)(n);
            e ? l.push(e) : a += 1;
            continue;
          }
          r.push(n);
        }
        return {
          spotCoins: r,
          perpMarkets: l,
          undrawablePerps: a
        };
      })(M, {
        perpsEnabled: eJ
      }) : {
        spotCoins: S,
        perpMarkets: [],
        undrawablePerps: 0
      }, k[6] = M, k[7] = S, k[8] = eJ, k[9] = es, k[10] = eZ, k[11] = n) : n = k[11];
      let {
          spotCoins: eQ,
          perpMarkets: eY,
          undrawablePerps: e0
        } = n,
        e1 = eY.length > 0 || e0 > 0,
        e2 = Q || eZ && es && !J && 0 === eQ.length && !e1,
        e3 = eZ ? !M.length && J : Z,
        e4 = "social-terminal" === eG && void 0 !== Y && Y && 0 === S.length && !q,
        e5 = (0, s.useRef)(null),
        e6 = (0, s.useRef)(e4);
      k[12] !== e4 ? (i = () => {
        let e = e6.current;
        e6.current = e4, e && !e4 && document.activeElement === document.body && e5.current?.focus({
          preventScroll: !0
        });
      }, o = [e4], k[12] = e4, k[13] = i, k[14] = o) : (i = k[13], o = k[14]), (0, s.useEffect)(i, o);
      let e7 = q || "";
      k[15] !== e_ || k[16] !== e$ || k[17] !== eH || k[18] !== z || k[19] !== W || k[20] !== e7 || k[21] !== eG ? (u = (0, ed.H)({
        variant: eG,
        homeLayout: eH,
        homeFeed: e$,
        sort: W,
        offset: z,
        searchTerm: e7,
        hasActiveFilters: e_
      }), k[15] = e_, k[16] = e$, k[17] = eH, k[18] = z, k[19] = W, k[20] = e7, k[21] = eG, k[22] = u) : u = k[22];
      let e8 = u,
        e9 = e$ === en.z.WATCHLIST ? U : z,
        te = q || "";
      k[23] !== eL || k[24] !== T || k[25] !== E || k[26] !== e3 || k[27] !== $ || k[28] !== ek || k[29] !== eA || k[30] !== eI || k[31] !== eQ || k[32] !== W || k[33] !== K || k[34] !== e9 || k[35] !== te ? (f = {
        coins: eQ,
        bookmarkedCoinMints: T,
        lastUpdatedMint: $,
        loading: e3,
        sourceScreen: K,
        sort: W,
        pageNumber: e9,
        onHover: ek,
        bookmarks: E,
        addToBookmark: eL,
        removeFromBookmark: eI,
        onManageWatchlistClick: eA,
        searchTerm: te
      }, k[23] = eL, k[24] = T, k[25] = E, k[26] = e3, k[27] = $, k[28] = ek, k[29] = eA, k[30] = eI, k[31] = eQ, k[32] = W, k[33] = K, k[34] = e9, k[35] = te, k[36] = f) : f = k[36];
      let tt = f,
        tr = "social-terminal" === eG ? eZ ? "watchlist" : eH : null;
      k[37] !== tr ? (h = {
        key: "explore_layout",
        value: tr
      }, k[37] = tr, k[38] = h) : h = k[38], (e => {
        let t,
          l,
          a = (0, r.c)(4),
          {
            key: n,
            value: i
          } = e;
        a[0] !== n || a[1] !== i ? (t = () => {
          if (null != i) return (({
            key: e,
            value: t
          }) => eo(r => r.setGlobalContextProperty(e, t)))({
            key: n,
            value: i
          }), () => eo(e => e.removeGlobalContextProperty(n));
        }, l = [n, i], a[0] = n, a[1] = i, a[2] = t, a[3] = l) : (t = a[2], l = a[3]), (0, s.useEffect)(t, l);
      })(h), k[39] !== G || k[40] !== tt || k[41] !== eH || k[42] !== eG ? (p = eH === ei.M.TABLE ? (0, t.jsx)("div", {
        className: "min-w-0 w-full",
        children: "social-terminal" === eG ? (0, t.jsx)(eb, {
          coinListProps: tt,
          athMap: G,
          isWatchlistView: !0
        }) : (0, t.jsx)(ex, {
          coinListProps: tt,
          athMap: G,
          isWatchlistView: !0
        })
      }) : (0, t.jsx)(I, {
        ...tt,
        isWatchlistView: !0
      }), k[39] = G, k[40] = tt, k[41] = eH, k[42] = eG, k[43] = p) : p = k[43];
      let tl = p,
        ta = "social-terminal" === eG && "outline-none";
      k[44] !== ta ? (x = (0, ef.c)("flex flex-col", ta), k[44] = ta, k[45] = x) : x = k[45];
      let tn = "social-terminal" === eG ? e5 : void 0,
        ti = "social-terminal" === eG ? -1 : void 0;
      return k[46] !== E || k[47] !== e$ || k[48] !== eE || k[49] !== eA || k[50] !== B ? (b = e$ === en.z.WATCHLIST && (0, t.jsx)(ey, {
        bookmarks: E,
        selectedBookmark: B || "default",
        onBookmarkClick: eE,
        onAddNewBookmarkButtonClick: eA
      }), k[46] = E, k[47] = e$, k[48] = eE, k[49] = eA, k[50] = B, k[51] = b) : b = k[51], k[52] !== ea || k[53] !== e1 || k[54] !== e$ || k[55] !== eT || k[56] !== eY || k[57] !== eI || k[58] !== B || k[59] !== e2 || k[60] !== eQ || k[61] !== e0 || k[62] !== tl ? (g = e$ === en.z.WATCHLIST && (0, t.jsxs)(t.Fragment, {
        children: [e2 && (0, t.jsx)(ej, {
          onBackButtonClick: eT
        }), !e2 && (0, t.jsxs)(t.Fragment, {
          children: [e1 ? (0, t.jsx)(eN, {
            markets: eY,
            undrawableCount: e0,
            marksFetchedAt: ea,
            onUnstar: e => void eI(e, B || "default")
          }) : null, eQ.length > 0 || !e1 ? tl : null]
        })]
      }), k[52] = ea, k[53] = e1, k[54] = e$, k[55] = eT, k[56] = eY, k[57] = eI, k[58] = B, k[59] = e2, k[60] = eQ, k[61] = e0, k[62] = tl, k[63] = g) : g = k[63], k[64] !== e$ || k[65] !== Z || k[66] !== et || k[67] !== e4 || k[68] !== W ? (v = e$ === en.z.TERMINAL && e4 && (0, t.jsx)(H, {
        onRetry: et,
        retrying: Z,
        sort: W
      }), k[64] = e$, k[65] = Z, k[66] = et, k[67] = e4, k[68] = W, k[69] = v) : v = k[69], k[70] !== eU || k[71] !== G || k[72] !== O || k[73] !== tt || k[74] !== S || k[75] !== R || k[76] !== e_ || k[77] !== e$ || k[78] !== eH || k[79] !== Z || k[80] !== z || k[81] !== L || k[82] !== eV || k[83] !== e4 || k[84] !== e8 || k[85] !== W || k[86] !== K || k[87] !== eP || k[88] !== eG ? (y = e$ === en.z.TERMINAL && !e4 && (0, t.jsxs)(t.Fragment, {
        children: [eH === ei.M.GRID && (0, t.jsx)(I, {
          ...tt
        }), eH === ei.M.TABLE && "social-terminal" === eG && (0, t.jsxs)("div", {
          className: "min-w-0 w-full",
          children: [O ? (0, t.jsx)(D, {
            ...O
          }) : null, e8 ? Z || !eV ? (0, t.jsx)(X.MoversCardSkeleton, {
            labelKey: (0, ec.p)(W)
          }) : (0, t.jsx)(s.Suspense, {
            fallback: (0, t.jsx)(X.MoversCardSkeleton, {
              labelKey: (0, ec.p)(W)
            }),
            children: (0, t.jsx)(ev, {
              coins: S,
              followedHoldersByMint: R,
              offset: z,
              sort: W,
              sourceScreen: K
            })
          }) : null, (0, t.jsx)(eg, {
            coinListProps: tt,
            athMap: G,
            hydrationByMint: R,
            tableNotificationCoins: eP,
            onTableNotificationExpand: L,
            hasActiveFilters: e_,
            filtersKey: eU,
            isWatchlistView: !1
          })]
        }), eH === ei.M.TABLE && "social-terminal" !== eG && (0, t.jsx)("div", {
          className: "min-w-0 w-full",
          children: (0, t.jsx)(ex, {
            coinListProps: tt,
            athMap: G,
            tableNotificationCoins: eP,
            onTableNotificationExpand: L ?? ep,
            hasActiveFilters: e_,
            isWatchlistView: !1
          })
        })]
      }), k[70] = eU, k[71] = G, k[72] = O, k[73] = tt, k[74] = S, k[75] = R, k[76] = e_, k[77] = e$, k[78] = eH, k[79] = Z, k[80] = z, k[81] = L, k[82] = eV, k[83] = e4, k[84] = e8, k[85] = W, k[86] = K, k[87] = eP, k[88] = eG, k[89] = y) : y = k[89], k[90] !== x || k[91] !== tn || k[92] !== ti || k[93] !== b || k[94] !== g || k[95] !== v || k[96] !== y ? (w = (0, t.jsxs)("div", {
        className: x,
        ref: tn,
        tabIndex: ti,
        children: [b, g, v, y]
      }), k[90] = x, k[91] = tn, k[92] = ti, k[93] = b, k[94] = g, k[95] = v, k[96] = y, k[97] = w) : w = k[97], k[98] !== M || k[99] !== eX || k[100] !== S || k[101] !== e_ || k[102] !== P || k[103] !== e$ || k[104] !== Z || k[105] !== J || k[106] !== z || k[107] !== eS || k[108] !== eM || k[109] !== eD || k[110] !== e2 || k[111] !== U ? (j = e$ === en.z.WATCHLIST ? !e2 && (J || M) && M.length ? (0, t.jsx)(ee, {
        offset: U,
        setOffset: eM,
        items: M,
        LIMIT: eh.s,
        loading: J
      }) : null : e_ ? null : (0, t.jsx)(er, {
        offset: z,
        setOffset: eS,
        items: S,
        LIMIT: eD,
        loading: Z,
        getHref: eX,
        hasNextPage: P
      }), k[98] = M, k[99] = eX, k[100] = S, k[101] = e_, k[102] = P, k[103] = e$, k[104] = Z, k[105] = J, k[106] = z, k[107] = eS, k[108] = eM, k[109] = eD, k[110] = e2, k[111] = U, k[112] = j) : j = k[112], k[113] !== w || k[114] !== j ? (_ = (0, t.jsxs)("div", {
        className: "flex w-full min-w-0 flex-col",
        children: [w, j]
      }), k[113] = w, k[114] = j, k[115] = _) : _ = k[115], k[116] !== E || k[117] !== eR || k[118] !== eF || k[119] !== eB || k[120] !== eW || k[121] !== ez || k[122] !== eO ? (C = eW || eB ? (0, t.jsx)(ew, {
        isOpen: eW,
        onOpenChange: ez,
        bookmarks: E,
        createBookmark: eR,
        deleteBookmark: eF,
        updateBookmarkName: eO
      }) : null, k[116] = E, k[117] = eR, k[118] = eF, k[119] = eB, k[120] = eW, k[121] = ez, k[122] = eO, k[123] = C) : C = k[123], k[124] !== _ || k[125] !== C ? (N = (0, t.jsxs)(t.Fragment, {
        children: [_, C]
      }), k[124] = _, k[125] = C, k[126] = N) : N = k[126], N;
    });
  var eS = lookupModule(455418);
  function eM() {
    return {
      x: window.pageXOffset,
      y: window.pageYOffset
    };
  }
  function eE({
    x: e,
    y: t
  }) {
    {
      let r = {
        behavior: "smooth"
      };
      "number" == typeof e && (r.left = e), "number" == typeof t && (r.top = t), window.scrollTo(r);
    }
  }
  var eT = lookupModule(84121),
    eA = lookupModule(946129),
    eL = lookupModule(148269),
    eI = lookupModule(998515),
    eR = lookupModule(536925),
    eF = lookupModule(311282),
    eO = lookupModule(921999),
    eW = lookupModule(358893),
    eB = lookupModule(412237);
  function ez(e, t, r, l) {
    return a => {
      e(a), t(0), (0, eB.n)();
      let n = {
        offset: 0,
        ...(l ? l(a) : {})
      };
      r?.(n);
    };
  }
  function eP(e) {
    return {
      includeNsfw: e
    };
  }
  function eV(e) {
    return {
      selectedFeed: e
    };
  }
  function eD(e) {
    return {
      order: e
    };
  }
  var eU = lookupModule(482617),
    e$ = lookupModule(500793),
    eH = lookupModule(152281),
    eG = lookupModule(573525),
    eK = lookupModule(649927),
    eq = lookupModule(544514),
    eX = lookupModule(960107),
    eZ = lookupModule(379705),
    eJ = lookupModule(555501);
  function eQ(e) {
    return void 0 !== e;
  }
  function eY(e) {
    return e.mint;
  }
  var e0 = lookupModule(722876),
    e1 = lookupModule(653805);
  function e2(e) {
    return e.coins;
  }
  function e3(e) {
    return e.mint;
  }
  var e4 = lookupModule(541710),
    e5 = lookupModule(231824),
    e6 = lookupModule(369091),
    e7 = lookupModule(583448),
    e8 = lookupModule(493025),
    e9 = lookupModule(440276),
    te = lookupModule(364043),
    tt = lookupModule(949629),
    tr = lookupModule(363250);
  function tl(e, t) {
    let {
        layout: r = ei.M.GRID,
        includeNsfw: l,
        bumpOrderSort: a,
        creationTimeSort: n,
        offset: i,
        order: s,
        showAnimations: o,
        searchTerm: c,
        lastProcessedTrade: d
      } = t,
      u = !e || !e.nsfw || l && e.nsfw,
      m = a && d.current !== e || n,
      f = s === eI.L.DESC,
      h = "" === c || [e.name, e.symbol, e.mint].some(e => e.includes(c)),
      p = r === ei.M.TABLE;
    return u && m && 0 === i && f && (p || o) && h;
  }
  var ta = lookupModule(530501),
    tn = lookupModule(346431),
    ti = lookupModule(456753);
  const HomePageContainer = function (e) {
  let {
      homeLayout: c
    } = (0, ei.e)(),
    d = (0, el.y)(),
    {
      initialSearchParams: u,
      initialCoins: m
    } = e,
    {
      decodedJwt: f
    } = (0, i.F)(),
    h = (0, s.useMemo)(() => !!(f && f.address), [f]),
    {
      generateNewSession: p,
      notifyPageOrFilterChange: x
    } = (0, ti.j)(),
    [b, g] = (0, s.useState)(!1),
    [v, y] = (0, s.useState)(!1),
    [w, j] = (0, s.useState)(null),
    {
      tableNotificationCoins: _,
      setTableNotificationCoins: C,
      handleNotificationExpand: k
    } = (() => {
      let e,
        t,
        l,
        a = (0, r.c)(7);
      void 0 !== a[0] ? (e = [], a[0] = void 0, a[1] = e) : e = a[1];
      let n = e,
        [i, o] = (0, s.useState)(n),
        c = "social-terminal" !== (0, el.y)();
      a[2] !== c ? (t = (e, t, r) => {
        let l = c && (r?.scrollToTop ?? !0);
        o(r => {
          if (0 === r.length) return r;
          let a = new Set();
          return t([...r, ...(e ?? [])].filter(e => !a.has(e.mint) && a.add(e.mint))), l && (0, eB.n)(), [];
        });
      }, a[2] = c, a[3] = t) : t = a[3];
      let d = t;
      return a[4] !== d || a[5] !== i ? (l = {
        tableNotificationCoins: i,
        setTableNotificationCoins: o,
        handleNotificationExpand: d
      }, a[4] = d, a[5] = i, a[6] = l) : l = a[6], l;
    })(),
    {
      handleClearSearch: S,
      searchRefetchTrigger: M,
      setShouldTriggerSearch: E
    } = (0, eO.u)(),
    A = function (e) {
      var t;
      let l,
        a,
        n,
        i,
        o,
        c,
        d,
        u,
        m,
        f,
        h,
        p,
        x,
        b,
        g,
        v,
        y = (0, r.c)(63),
        {
          initialSearchParams: w,
          isUserValid: j,
          onStateChange: _
        } = e,
        C = void 0 !== j && j,
        {
          homeSort: N,
          setHomeSort: k
        } = (0, eA.f)(),
        {
          homeSortOrder: S,
          setHomeSortOrder: M
        } = (0, eI.J)(),
        {
          homeFeed: E,
          setHomeFeed: T
        } = (0, en.N)(),
        A = (0, el.y)(),
        {
          isSearchMode: L,
          searchTerm: I,
          handleExitSearchMode: R
        } = (0, eO.u)();
      y[0] !== L ? (l = (0, eh.m)(L), y[0] = L, y[1] = l) : l = y[1];
      let {
          homeOffset: F,
          setHomeOffset: O
        } = (0, eT.f)(l),
        W = (0, eW.M)(),
        B = (0, eW.O)(),
        [z, P] = (t = w.bookmark, g = (0, r.c)(2), v = void 0 === t ? "default" : t, g[0] !== v ? (b = eF.d.withDefault(v), g[0] = v, g[1] = b) : b = g[1], (0, eF.o)("watchlist", b)),
        [V, D] = (0, eR.j)("last_sort_update", null);
      y[2] !== E || y[3] !== C || y[4] !== T ? (a = () => {
        C || E === en.z.TERMINAL || T(en.z.TERMINAL);
      }, n = [C, E, T], y[2] = E, y[3] = C, y[4] = T, y[5] = a, y[6] = n) : (a = y[5], n = y[6]), (0, s.useEffect)(a, n), y[7] !== L || y[8] !== V || y[9] !== _ || y[10] !== O || y[11] !== k || y[12] !== M || y[13] !== D || y[14] !== A ? (i = () => {
        if ("social-terminal" === A) return;
        let e = Date.now();
        V && e - V > 18e5 && !L && V && (k(eL.Q), M(eI.I), O(0), (0, eB.n)(), _?.({
          sort: eL.Q,
          order: eI.I,
          offset: 0
        }), D(e));
      }, o = [A, V, L, D, M, k, O, _], y[7] = L, y[8] = V, y[9] = _, y[10] = O, y[11] = k, y[12] = M, y[13] = D, y[14] = A, y[15] = i, y[16] = o) : (i = y[15], o = y[16]), (0, s.useEffect)(i, o), y[17] !== L || y[18] !== D ? (c = () => {
        L && D(Date.now());
      }, d = [D, L], y[17] = L, y[18] = D, y[19] = c, y[20] = d) : (c = y[19], d = y[20]), (0, s.useEffect)(c, d), y[21] !== R || y[22] !== L || y[23] !== _ || y[24] !== O || y[25] !== k || y[26] !== M ? (u = e => {
        L && e === eL.E.FEATURED ? R({
          sort: eL.E.FEATURED
        }) : (k(e), M(eI.I), O(0), _?.({
          sort: e,
          order: eI.I,
          offset: 0
        }));
      }, y[21] = R, y[22] = L, y[23] = _, y[24] = O, y[25] = k, y[26] = M, y[27] = u) : u = y[27];
      let U = u;
      y[28] !== _ || y[29] !== O || y[30] !== M ? (m = ez(M, O, _, eD), y[28] = _, y[29] = O, y[30] = M, y[31] = m) : m = y[31];
      let $ = m;
      y[32] !== _ || y[33] !== T || y[34] !== O ? (f = ez(T, O, _, eV), y[32] = _, y[33] = T, y[34] = O, y[35] = f) : f = y[35];
      let H = f;
      y[36] !== _ || y[37] !== O || y[38] !== B ? (h = ez(B, O, _, eP), y[36] = _, y[37] = O, y[38] = B, y[39] = h) : h = y[39];
      let G = h;
      y[40] !== _ || y[41] !== O ? (p = e => {
        O(e), _?.({
          offset: e
        });
      }, y[40] = _, y[41] = O, y[42] = p) : p = y[42];
      let K = p;
      return y[43] !== H || y[44] !== G || y[45] !== $ || y[46] !== K || y[47] !== U || y[48] !== E || y[49] !== F || y[50] !== N || y[51] !== S || y[52] !== W || y[53] !== L || y[54] !== V || y[55] !== I || y[56] !== T || y[57] !== O || y[58] !== k || y[59] !== M || y[60] !== P || y[61] !== z ? (x = {
        sort: N,
        order: S,
        selectedFeed: E,
        includeNsfw: W,
        offset: F,
        watchlistParam: z,
        watchlistOffset: 0,
        isSearchMode: L,
        searchTerm: I,
        lastSortUpdate: V,
        setSort: k,
        setOrder: M,
        setSelectedFeed: T,
        setOffset: O,
        setWatchlistParam: P,
        handleSortChange: U,
        handleOrderChange: $,
        handleFeedChange: H,
        handleNsfwChange: G,
        handlePageChange: K
      }, y[43] = H, y[44] = G, y[45] = $, y[46] = K, y[47] = U, y[48] = E, y[49] = F, y[50] = N, y[51] = S, y[52] = W, y[53] = L, y[54] = V, y[55] = I, y[56] = T, y[57] = O, y[58] = k, y[59] = M, y[60] = P, y[61] = z, y[62] = x) : x = y[62], x;
    }({
      initialSearchParams: u,
      isUserValid: h,
      onStateChange: (0, s.useCallback)(e => {
        void 0 !== e.offset && (p(), x());
      }, [p, x])
    }),
    {
      isSearchMode: L,
      searchTerm: I
    } = A,
    {
      homeChain: R
    } = (0, eK.f)(),
    [F] = (0, e0.f)(),
    O = (0, ta.n)({
      sort: A.sort,
      hasSearchTerm: L
    }),
    W = O ? (0, tn.q)(F) : void 0,
    [B, z] = (0, s.useState)(A.watchlistParam || "default"),
    {
      apiFilterParams: P,
      appliedMarketCapRange: V,
      appliedVolumeRange: D,
      appliedFiltersKey: U,
      hasActiveFilters: $,
      hasMarketCapFilter: H,
      hasVolumeFilter: G,
      handleApplyFilters: K,
      handleClearFilters: q,
      resetMarketCapFilter: X,
      resetVolumeFilter: Z,
      resetFilters: Q,
      formatFilterValue: Y,
      constants: ee
    } = (0, te.f)();
  (0, s.useEffect)(() => () => {
    Q();
  }, [Q]);
  let {
      showAnimations: et,
      setShowAnimations: er,
      setPauseAnimations: ea,
      areAnimationsPaused: es,
      shouldShowAnimations: eo
    } = (e => {
      let t,
        l,
        a,
        n,
        i,
        o,
        c = (0, r.c)(16);
      c[0] !== e ? (t = void 0 === e ? {} : e, c[0] = e, c[1] = t) : t = c[1];
      let {
          hasActiveFilters: d,
          scrollThreshold: u
        } = t,
        m = void 0 === u ? 480 : u,
        [f, h] = (0, eS.f)(),
        [p, x] = (0, s.useState)(!1),
        [b, g] = (0, s.useState)(!1),
        [v, y] = (0, s.useState)(!1),
        [w] = function () {
          let e,
            t,
            l,
            a,
            n,
            i,
            o,
            c,
            d,
            u = (0, r.c)(10);
          u[0] === Symbol.for("react.memo_cache_sentinel") ? (e = {
            x: 0,
            y: 0
          }, u[0] = e) : e = u[0];
          let [m, f] = (0, s.useState)(e);
          u[1] === Symbol.for("react.memo_cache_sentinel") ? (t = () => {
            f(eM());
          }, u[1] = t) : t = u[1];
          let h = t;
          return u[2] === Symbol.for("react.memo_cache_sentinel") ? (l = () => (window.addEventListener("scroll", h), () => window.removeEventListener("scroll", h)), a = [h], u[2] = l, u[3] = a) : (l = u[2], a = u[3]), (0, s.useEffect)(l, a), u[4] === Symbol.for("react.memo_cache_sentinel") ? (n = () => (window.addEventListener("resize", h), () => window.removeEventListener("resize", h)), i = [h], u[4] = n, u[5] = i) : (n = u[4], i = u[5]), (0, s.useEffect)(n, i), u[6] === Symbol.for("react.memo_cache_sentinel") ? (o = () => {
            f(eM());
          }, c = [], u[6] = o, u[7] = c) : (o = u[6], c = u[7]), (0, s.useEffect)(o, c), u[8] !== m ? (d = [m, eE], u[8] = m, u[9] = d) : d = u[9], d;
        }(),
        {
          y: j
        } = w;
      c[2] === Symbol.for("react.memo_cache_sentinel") ? (l = () => {
        let e = window.matchMedia("(max-width: 767px)"),
          t = () => y(e.matches);
        return t(), e.addEventListener("change", t), () => e.removeEventListener("change", t);
      }, a = [], c[2] = l, c[3] = a) : (l = c[2], a = c[3]), (0, s.useEffect)(l, a), c[4] !== v || c[5] !== m || c[6] !== j ? (n = () => {
        v && j && g(j > m);
      }, i = [j, m, v], c[4] = v, c[5] = m, c[6] = j, c[7] = n, c[8] = i) : (n = c[7], i = c[8]), (0, s.useEffect)(n, i);
      let _ = p || b,
        C = f && !_ && !(void 0 !== d && d);
      return c[9] !== _ || c[10] !== b || c[11] !== p || c[12] !== h || c[13] !== C || c[14] !== f ? (o = {
        showAnimations: f,
        setShowAnimations: h,
        pauseAnimations: p,
        setPauseAnimations: x,
        areAnimationsPaused: _,
        shouldShowAnimations: C,
        hasScrolledPastThreshold: b
      }, c[9] = _, c[10] = b, c[11] = p, c[12] = h, c[13] = C, c[14] = f, c[15] = o) : o = c[15], o;
    })({
      hasActiveFilters: $
    }),
    ed = (0, s.useMemo)(() => (({
      initialCoins: e,
      isSearchMode: t,
      hasActiveFilters: r,
      sort: l,
      offset: a
    }) => ({
      initialCoins: e?.length && !t && !r && (0, ec.n)(l) && 0 === a ? e : void 0
    }))({
      initialCoins: m,
      isSearchMode: L,
      hasActiveFilters: $,
      sort: A.sort,
      offset: A.offset
    }), [m, L, $, A.sort, A.offset]),
    eu = (0, ec.r)(A.sort),
    em = (0, ec.H)({
      sort: A.sort,
      chain: R
    }),
    {
      loading: ef,
      coins: ep,
      hasMorePages: ex,
      setCoins: eb,
      error: eg,
      refetch: ev,
      requestKey: ey,
      rowsRequestKey: ew,
      servedCoins: ej
    } = (e => {
      let t,
        l,
        a,
        n,
        i,
        o,
        c,
        d,
        u,
        m,
        f,
        h,
        p,
        x,
        b,
        g,
        v = (0, r.c)(57);
      v[0] !== e ? ({
        filterParams: t,
        ...l
      } = e, v[0] = e, v[1] = t, v[2] = l) : (t = v[1], l = v[2]);
      e: {
        if (!t) {
          a = !1;
          break e;
        }
        a = Object.values(t).some(eQ);
      }
      let y = a;
      v[3] !== y || v[4] !== l ? (n = {
        ...l,
        forceLocalFiltering: y
      }, v[3] = y, v[4] = l, v[5] = n) : n = v[5];
      let w = (0, eZ.f)(n);
      v[6] !== w ? ({
        coins: c,
        loading: i,
        hasMorePages: d,
        ...o
      } = w, v[6] = w, v[7] = i, v[8] = o, v[9] = c, v[10] = d) : (i = v[7], o = v[8], c = v[9], d = v[10]), v[11] !== c ? (u = c.map(eY), v[11] = c, v[12] = u) : u = v[12];
      let j = u,
        _ = t?.verifiedOnly === !0,
        {
          data: C,
          isPending: k
        } = (0, eJ.i)(),
        S = _ && k;
      v[13] !== j || v[14] !== y ? (m = y ? j : [], v[13] = j, v[14] = y, v[15] = m) : m = v[15];
      let M = y && j.length > 0;
      v[16] !== M ? (f = {
        shouldFetch: M,
        enablePolling: !1
      }, v[16] = M, v[17] = f) : f = v[17];
      let {
        marketActivity: E,
        refetchMints: A
      } = (0, N.f)(m, f);
      v[18] !== j || v[19] !== E || v[20] !== t?.volume24hMax || v[21] !== t?.volume24hMin || v[22] !== A || v[23] !== y ? (h = () => {
        if (!y || 0 === j.length || t?.volume24hMin === void 0 && t?.volume24hMax === void 0) return;
        let e = (0, T.P)(E, j);
        e.length > 0 && A(e);
      }, v[18] = j, v[19] = E, v[20] = t?.volume24hMax, v[21] = t?.volume24hMin, v[22] = A, v[23] = y, v[24] = h) : h = v[24], v[25] !== j || v[26] !== E || v[27] !== t || v[28] !== A || v[29] !== y ? (p = [y, j, t, E, A], v[25] = j, v[26] = E, v[27] = t, v[28] = A, v[29] = y, v[30] = p) : p = v[30], (0, s.useEffect)(h, p);
      t: {
        let e;
        if (!y || !t) {
          x = null;
          break t;
        }
        let {
          marketCapMin: r,
          marketCapMax: l,
          volume24hMin: a,
          volume24hMax: n
        } = t;
        if (v[31] !== E || v[32] !== l || v[33] !== r || v[34] !== c || v[35] !== C || v[36] !== _ || v[37] !== n || v[38] !== a) {
          let t;
          v[40] !== E || v[41] !== l || v[42] !== r || v[43] !== C || v[44] !== _ || v[45] !== n || v[46] !== a ? (t = e => {
            if (_ && !(0, eJ.h)(C, e.mint, e.chain_id) || void 0 !== r && Number(e.usd_market_cap) < r || void 0 !== l && Number(e.usd_market_cap) > l) return !1;
            if (void 0 !== a || void 0 !== n) {
              if (!(0, T.G)(E, e.mint)) return !1;
              let t = (0, T.F)(E, e.mint);
              if (void 0 !== a && t < a || void 0 !== n && t > n) return !1;
            }
            return !0;
          }, v[40] = E, v[41] = l, v[42] = r, v[43] = C, v[44] = _, v[45] = n, v[46] = a, v[47] = t) : t = v[47], e = c.filter(t), v[31] = E, v[32] = l, v[33] = r, v[34] = c, v[35] = C, v[36] = _, v[37] = n, v[38] = a, v[39] = e;
        } else e = v[39];
        x = e;
      }
      let L = x,
        I = l.offset || 0,
        R = l.limit || 50;
      r: {
        let e;
        if (!L) {
          b = c;
          break r;
        }
        v[48] !== R || v[49] !== L || v[50] !== I ? (e = L.slice(I, I + R), v[48] = R, v[49] = L, v[50] = I, v[51] = e) : e = v[51], b = e;
      }
      let F = b,
        O = i || S,
        W = L ? L.length > I + R : d;
      return v[52] !== F || v[53] !== o || v[54] !== O || v[55] !== W ? (g = {
        coins: F,
        loading: O,
        hasMorePages: W,
        ...o
      }, v[52] = F, v[53] = o, v[54] = O, v[55] = W, v[56] = g) : g = v[56], g;
    })({
      sort: A.sort,
      order: A.order,
      offset: $ ? 0 : A.offset,
      limit: L ? eh.x : $ ? eh.y : eh.s,
      includeNsfw: A.includeNsfw,
      isSearchMode: A.isSearchMode,
      searchTerm: A.searchTerm,
      searchRefetchTrigger: M,
      chain: em,
      callsWindow: W,
      filterParams: Object.keys(P).length > 0 ? P : void 0,
      initialCoins: ed.initialCoins
    }),
    {
      ipfsPrefix: e_
    } = (0, e6.useIpfsPrefix)(),
    eC = (0, s.useMemo)(() => ({
      getId: e => e.mint,
      isTrending: () => !1,
      isGraduated: e => !!e.raydium_pool,
      getWeight: () => 1
    }), []),
    eN = (0, s.useMemo)(() => ep?.length ? (0, l.wrapItemsWithFeedItem)(ep, eC) : [], [ep, eC]),
    ts = (0, s.useMemo)(() => e => {
      "function" == typeof e ? eb(t => e(t.map(e => {
        let t = {
          ...e
        };
        return "id" in t || !eC || Object.defineProperty(t, "id", {
          value: eC.getId(e),
          enumerable: !0
        }), t;
      })).map(({
        ...e
      }) => e)) : eb(e.map(({
        ...e
      }) => e));
    }, [eb, eC]),
    to = (0, l.useFeedBump)({
      items: eN,
      setItems: ts,
      sort: A.sort,
      showAnimations: et,
      areAnimationsPaused: es || c === ei.M.TABLE,
      isTrending: eC.isTrending,
      isGraduated: eC.isGraduated,
      animationTriggerSort: eu ? A.sort : void 0
    }),
    tc = (0, s.useMemo)(() => eu ? to : null, [eu, to]) ?? w,
    td = (0, s.useMemo)(() => {
      var e, t;
      return e = A.sort, t = A.offset, !$ && !(t > 0) && e !== eL.E.FEATURED && [eL.E.TRADE, eL.E.NEWEST].includes(e);
    }, [A.sort, $, A.offset]),
    tu = A.sort === eL.E.NEWEST,
    tm = A.sort === eL.E.TRADE,
    tf = (0, s.useMemo)(() => tm && td && (!es || c === ei.M.TABLE), [tm, td, es, c]),
    th = (0, s.useMemo)(() => (ep ?? []).map(e => e.mint).filter(Boolean), [ep]),
    tp = ew === ey;
  (0, e9.f)({
    coins: ej,
    enabled: "trending" === eu && !L && tp,
    screen: eh.X
  });
  let {
      byMint: tx
    } = (0, e$.P)({
      mints: th,
      enabled: h && "social-terminal" === d && c === ei.M.TABLE && A.selectedFeed === en.z.TERMINAL
    }),
    tb = O && !L,
    tg = tb && "social-terminal" === d && c === ei.M.TABLE && A.selectedFeed === en.z.TERMINAL,
    {
      data: tv,
      dataUpdatedAt: ty,
      refetch: tw
    } = (0, eU.f)({
      window: W ?? tn.W,
      enabled: tg
    }),
    tj = (0, s.useCallback)(() => ev({
      background: !0
    }), [ev]),
    t_ = (0, s.useCallback)(() => {
      tw();
    }, [tw]);
  (e => {
    let t,
      l,
      a = (0, r.c)(9),
      {
        enabled: n,
        window: i,
        generatedAt: o,
        statsUpdatedAt: c,
        rowsLoading: d,
        refetchList: u,
        refetchStats: m
      } = e,
      f = (0, s.useRef)(null),
      h = (0, s.useRef)(null),
      p = (0, s.useRef)(null),
      x = (0, s.useRef)(!1),
      b = (0, s.useRef)(null),
      g = (0, s.useRef)(!1),
      v = (0, s.useRef)(d);
    a[0] !== n || a[1] !== o || a[2] !== u || a[3] !== m || a[4] !== d || a[5] !== c || a[6] !== i ? (t = () => {
      let e = d && !v.current;
      if (v.current = d, e && (g.current = !0), d || (g.current = !1), !n) {
        f.current = null, h.current = null, p.current = null, x.current = !1, b.current = null, g.current = !1;
        return;
      }
      if ((null === h.current || p.current !== i) && (f.current = null, h.current = Date.now(), p.current = i, x.current = d, b.current = null, m()), d && (x.current = !0), null === o || c < h.current) return;
      let t = e => {
        let {
          previousSeen: t,
          opening: r
        } = e;
        b.current = c;
        let l = u();
        if (void 0 === l) return;
        let a = () => {
          f.current === o && (f.current = t, r && (x.current = !1));
        };
        l.then(e => {
          !1 === e && a();
        }, a);
      };
      if (null === f.current) {
        if (!x.current && b.current === c || (f.current = o, x.current)) return;
        x.current = !0, t({
          previousSeen: null,
          opening: !0
        });
        return;
      }
      if (f.current === o || b.current === c || g.current) return;
      let r = f.current;
      f.current = o, t({
        previousSeen: r,
        opening: !1
      });
    }, l = [n, i, o, c, d, u, m], a[0] = n, a[1] = o, a[2] = u, a[3] = m, a[4] = d, a[5] = c, a[6] = i, a[7] = t, a[8] = l) : (t = a[7], l = a[8]), (0, s.useEffect)(t, l);
  })({
    enabled: tg,
    window: W ?? tn.W,
    generatedAt: tv?.generatedAt ?? null,
    statsUpdatedAt: ty,
    rowsLoading: ef,
    refetchList: tj,
    refetchStats: t_
  });
  let tC = (e => {
      let t,
        l = (0, r.c)(4),
        {
          refetchList: a,
          refetchStats: n,
          statsEnabled: i
        } = e;
      return l[0] !== a || l[1] !== n || l[2] !== i ? (t = () => {
        let e = a();
        if (!i) return;
        let t = () => n();
        Promise.resolve(e).then(t, t);
      }, l[0] = a, l[1] = n, l[2] = i, l[3] = t) : t = l[3], t;
    })({
      refetchList: ev,
      refetchStats: t_,
      statsEnabled: tg
    }),
    {
      latestTradeEventWithCoinData: tN
    } = (e => {
      let t,
        l,
        a,
        n,
        i,
        o,
        c,
        d,
        u,
        m,
        f,
        h = (0, r.c)(28);
      h[0] !== e ? (t = void 0 === e ? {} : e, h[0] = e, h[1] = t) : t = h[1];
      let {
        mint: p,
        mints: x,
        coins: b,
        enabled: g,
        throttleMs: v,
        onlyTradesWithCoinMeta: y
      } = t;
      h[2] !== b ? (l = void 0 === b ? [] : b, h[2] = b, h[3] = l) : l = h[3];
      let w = l,
        j = void 0 === v ? 500 : v,
        _ = void 0 !== y && y;
      h[4] === Symbol.for("react.memo_cache_sentinel") ? (a = {}, h[4] = a) : a = h[4];
      let {
          data: C
        } = (0, tr.f)(a),
        N = (0, s.useRef)(0);
      h[5] !== C ? (n = () => {
        N.current = "number" == typeof C && Number.isFinite(C) && C > 0 ? C : 0;
      }, i = [C], h[5] = C, h[6] = n, h[7] = i) : (n = h[6], i = h[7]), (0, s.useEffect)(n, i);
      e: {
        let e, t;
        if (p) {
          let e;
          h[8] !== p ? (e = [p], h[8] = p, h[9] = e) : e = h[9], o = e;
          break e;
        }
        h[10] !== x ? (e = x ?? [], h[10] = x, h[11] = e) : e = h[11], h[12] !== e ? (t = e.filter(Boolean), h[12] = e, h[13] = t) : t = h[13], o = t;
      }
      let k = o,
        S = (0, s.useRef)(w);
      h[14] !== w ? (c = () => {
        S.current = w;
      }, d = [w], h[14] = w, h[15] = c, h[16] = d) : (c = h[15], d = h[16]), (0, s.useEffect)(c, d);
      let [M, E] = (0, s.useState)(null),
        [T, A] = (0, s.useState)(null),
        L = (0, s.useRef)(null);
      h[17] !== p || h[18] !== _ || h[19] !== j ? (u = e => {
        let t = Date.now();
        if (j > 0) {
          let e = L.current;
          if (null != e && t - e < j) return;
          L.current = t;
        }
        let r = S.current.find(t => t.mint === e.mint),
          l = Number(e.amountSol),
          a = Number.isFinite(l) ? l : null,
          n = N.current;
        if (p) {
          if (e.mint !== p) return;
          A({
            mintAddress: e.mint,
            type: e.type,
            amountUsd: null != a && n > 0 ? a * n : null,
            amountSol: a
          }), E(null);
          return;
        }
        (!_ || r) && r && (E({
          slotIndexId: "",
          tx: "",
          baseAmount: e.amountSol,
          quoteAmount: "",
          userAddress: "",
          hasCoinMeta: !0,
          program: r.program,
          marketCap: e.marketCap,
          isBuy: "buy" === e.type,
          mint: r.mint,
          symbol: r.symbol,
          name: r.name,
          created_timestamp: r.created_timestamp ?? void 0,
          creator: r.creator
        }), A(null));
      }, h[17] = p, h[18] = _, h[19] = j, h[20] = u) : u = h[20];
      let I = u,
        R = (void 0 === g || g) && k.length > 0;
      return h[21] !== k || h[22] !== I || h[23] !== R ? (m = {
        mints: k,
        isEnabled: R,
        onLiteTrade: I
      }, h[21] = k, h[22] = I, h[23] = R, h[24] = m) : m = h[24], (0, tt.f)(m), h[25] !== T || h[26] !== M ? (f = {
        latestTradeEventWithCoinData: M,
        latestTradeEvent: T
      }, h[25] = T, h[26] = M, h[27] = f) : f = h[27], f;
    })({
      mints: th,
      coins: ep ?? [],
      onlyTradesWithCoinMeta: !0,
      enabled: tf,
      throttleMs: 1e3
    });
  !function (e) {
    let {
        enabled: t,
        maxListSize: r,
        setCoins: l,
        pollIntervalMs: a = 3e4,
        peekLimit: n = 25,
        chain: o = "all",
        board: c = "movers",
        maxPrependBoardRank: d = 10,
        paused: u = !1
      } = e,
      {
        ipfsPrefix: m
      } = (0, e6.useIpfsPrefix)(),
      {
        address: f,
        userId: h
      } = (0, i.F)(),
      {
        deviceId: p,
        sessionId: x,
        sessionStartTimestampMs: b
      } = (0, e5.f)(),
      g = f || void 0,
      v = h || void 0,
      y = (0, e4.l)(),
      w = (0, s.useRef)(l);
    (0, s.useEffect)(() => {
      w.current = l;
    }, [l]);
    let j = (0, s.useRef)(m);
    (0, s.useEffect)(() => {
      j.current = m;
    }, [m]);
    let _ = (0, s.useRef)(u);
    (0, s.useLayoutEffect)(() => {
      _.current = u;
    }, [u]);
    let C = (0, s.useRef)({
        endpoint: null,
        coins: []
      }),
      N = (0, s.useCallback)(e => {
        w.current(t => {
          let l = new Set(e.map(e => e.mint)),
            a = t.filter(e => l.has(e.mint)),
            n = new Set(a.map(e => e.mint)),
            i = [],
            s = [];
          for (let [t, r] of e.entries()) !r?.mint || n.has(r.mint) || (n.add(r.mint), (t < d ? i : s).push(r));
          return 0 === i.length && 0 === s.length && a.length === t.length ? t : [...i, ...a, ...s].slice(0, r);
        });
      }, [r, d]),
      k = (0, s.useMemo)(() => t ? (0, e7.f)({
        limit: Math.min(Math.max(n, 50, r), e7.y),
        userId: g,
        pumpUserId: v,
        sessionId: x,
        deviceId: p,
        sessionStartTimestampMs: b,
        chain: o,
        board: c,
        exposure: y
      }) : null, [t, n, r, g, v, x, p, b, o, c, y]),
      S = (0, s.useRef)(k);
    S.current = k;
    let M = (0, s.useCallback)(async e => {
      let t, r;
      if (!k) return;
      try {
        t = await fetch(k, {
          credentials: "include",
          headers: {
            "Content-Type": "application/json"
          },
          signal: e
        });
      } catch (e) {
        e?.name;
        return;
      }
      if (e.aborted || S.current !== k || !t.ok) return;
      try {
        r = await t.json();
      } catch {
        return;
      }
      if (e.aborted || S.current !== k) return;
      let l = (0, e7.$)(r);
      if (0 === l.length) return;
      let a = (0, e8.f)(l, j.current);
      if (_.current) {
        C.current = {
          endpoint: k,
          coins: a
        };
        return;
      }
      N(a);
    }, [k, N]);
    (0, s.useEffect)(() => {
      if (u) return;
      let e = C.current;
      0 === e.coins.length || (C.current = {
        endpoint: k,
        coins: []
      }, e.endpoint === k && N(e.coins));
    }, [u, k, N]), (0, s.useEffect)(() => {
      if (!t || !k) return;
      let e = new AbortController(),
        r = window.setInterval(() => {
          M(e.signal);
        }, a);
      return () => {
        e.abort(), window.clearInterval(r);
      };
    }, [t, k, a, M]);
  }({
    enabled: (({
      homeLayout: e,
      hasActiveFilters: t,
      isSearchMode: r,
      offset: l,
      sort: a,
      selectedFeed: n
    }) => !t && !r && !(l > 0) && "grid" === e && (0, ec.n)(a) && "terminal" === n)({
      homeLayout: c,
      hasActiveFilters: $,
      isSearchMode: L,
      offset: A.offset,
      sort: A.sort,
      selectedFeed: A.selectedFeed
    }),
    maxListSize: eh.s,
    setCoins: eb,
    board: eu,
    chain: em,
    paused: es && c !== ei.M.TABLE
  });
  let tk = (0, eq.f)(),
    tS = (0, s.useRef)(null),
    tM = (0, s.useRef)(A);
  (0, s.useEffect)(() => {
    tM.current = A;
  }, [A]);
  let {
      processEventWithNotifications: tE
    } = (({
      layout: e,
      hasActiveFilters: t,
      boardStateRef: r,
      setTableNotificationCoins: l
    }) => ({
      processEventWithNotifications: (0, s.useCallback)((a, n, i) => {
        let s = r.current;
        if (!t && !(s.offset > 0)) {
          if (e === ei.M.TABLE) {
            n(a, i) && l(e => new Set(e.map(e => e.mint)).has(a.mint) ? e : [{
              ...a
            }, ...e].slice(0, 10));
            return;
          }
          !function (e, t, r) {
            if (null == e || !t(e, r)) return;
            let {
              setCoins: l,
              setLastUpdatedMint: a
            } = r;
            l(t => function (e, t, r) {
              let {
                  order: l
                } = r,
                a = e.findIndex(e => e.mint === t.mint),
                n = [...e];
              if (-1 !== a) {
                let [e] = n.splice(a, 1);
                l === eI.L.DESC ? n.unshift(e) : n.push(e);
              } else {
                let e = {
                  ...t,
                  image_uri: (0, J.r)(t.image_uri, r.ipfsPrefix)
                };
                n.unshift(e);
              }
              return n.length > r.LIMIT && (l === eI.L.DESC ? n.pop() : n.shift()), n.filter((e, t, r) => r.findIndex(t => t.mint === e.mint) === t);
            }(t, e, r)), a(e.mint), r.lastProcessedTrade.current = e, setTimeout(() => a(""), 700);
          }(a, n, i);
        }
      }, [t, e])
    }))({
      layout: c,
      hasActiveFilters: $,
      boardStateRef: tM,
      setTableNotificationCoins: C
    }),
    tT = (0, s.useCallback)(e => {
      k(ep, eb, e);
    }, [k, ep, eb]);
  !function (e) {
    let t,
      l,
      a,
      n,
      i,
      o,
      c,
      d = (0, r.c)(15),
      {
        coins: u,
        setCoins: m,
        sort: f,
        enabled: h,
        copyWarmStore: p
      } = e,
      x = void 0 === h || h,
      b = void 0 !== p && p;
    d[0] !== x || d[1] !== f ? (t = x && (0, ec.n)(f), d[0] = x, d[1] = f, d[2] = t) : t = d[2];
    let g = t;
    d[3] !== u || d[4] !== g ? (l = g ? u.map(e3) : [], d[3] = u, d[4] = g, d[5] = l) : l = d[5];
    let v = l,
      y = (0, s.useRef)(m);
    d[6] !== m ? (a = () => {
      y.current = m;
    }, n = [m], d[6] = m, d[7] = a, d[8] = n) : (a = d[7], n = d[8]), (0, s.useEffect)(a, n), d[9] !== v ? (i = v.slice().sort().join(","), d[9] = v, d[10] = i) : i = d[10];
    let w = i;
    d[11] !== b || d[12] !== w ? (o = () => {
      if ("" === w) return;
      let e = w.split(","),
        t = new Map(),
        r = r => {
          for (let l of e) {
            let e = r[l]?.usdMarketCap;
            "number" != typeof e || e <= 0 || t.get(l) !== e && (t.set(l, e), y.current(t => t.some(t => t.mint === l && t.usd_market_cap !== e) ? t.map(t => t.mint === l ? {
              ...t,
              usd_market_cap: e
            } : t) : t));
          }
        };
      return b && r(e1.x.getState().coins), e1.x.subscribe(e2, r);
    }, c = [w, b], d[11] = b, d[12] = w, d[13] = o, d[14] = c) : (o = d[13], c = d[14]), (0, s.useEffect)(o, c);
  }({
    coins: ep || [],
    setCoins: eb,
    sort: A.sort,
    enabled: "social-terminal" !== d || c !== ei.M.TABLE,
    copyWarmStore: "social-terminal" === d
  });
  let tA = (0, s.useRef)(eb),
    tL = (0, s.useRef)(j);
  (0, s.useEffect)(() => {
    tA.current = eb;
  }, [eb]), (0, s.useEffect)(() => {
    tL.current = j;
  }, [j]);
  let tI = (0, s.useCallback)(() => ({
    layout: c,
    includeNsfw: A.includeNsfw,
    sort: A.sort,
    offset: A.offset,
    order: A.order,
    showAnimations: et,
    searchTerm: A.searchTerm || "",
    selectedFeed: A.selectedFeed,
    bumpOrderSort: tm,
    creationTimeSort: tu,
    setCoins: e => tA.current(e),
    setLastUpdatedMint: e => tL.current(e),
    lastProcessedTrade: tS,
    ipfsPrefix: e_,
    LIMIT: eh.s
  }), [c, A.includeNsfw, A.sort, A.offset, A.order, A.searchTerm, A.selectedFeed, et, tm, tu, tS, e_]);
  (0, s.useEffect)(() => {
    tN && tE(tN, tl, tI());
  }, [tN, tE, tI]);
  let tR = (0, s.useCallback)(e => {
    es && c !== ei.M.TABLE || tE("string" == typeof e ? JSON.parse(e) : e, tl, tI());
  }, [es, c, tE, tI]);
  (0, eG.f)({
    type: n.N.Core,
    subject: "newCoinCreated.prod",
    enabled: tu && td && tk,
    onEvent: tR
  }), (0, s.useEffect)(() => {
    C([]);
  }, [c, $, L, R, A.offset, A.sort, A.order, A.selectedFeed]);
  let {
      bookmarkedCoins: tF,
      bookmarkedCoinsLoading: tO,
      bookmarkedCoinsUpdatedAt: tW,
      addToBookmark: tB,
      removeFromBookmark: tz,
      bookmarks: tP,
      createBookmark: tV,
      deleteBookmark: tD,
      updateBookmarkName: tU
    } = (0, eX.j)(A.selectedFeed === en.z.WATCHLIST && h, h, 0, eh.s, !!(f && f.address), B),
    t$ = (0, s.useMemo)(() => A.selectedFeed === en.z.WATCHLIST ? a.Ae.WATCHLIST : L ? a.Ae.SEARCH : eh.X, [L, A.selectedFeed]),
    tH = (0, s.useCallback)(e => {
      C([]), z(e), tM.current.setWatchlistParam(e), tM.current.setOffset(0);
    }, []),
    tG = (0, s.useCallback)(e => {
      e && y(!0), g(e);
    }, []),
    tK = (0, s.useCallback)(() => {
      tG(!0);
    }, [tG]),
    tq = (0, s.useCallback)(() => {
      tM.current.setOffset(0);
    }, []),
    tX = (0, s.useMemo)(() => tP?.length ? tP.flatMap(e => e.bookmark_items || []) : [], [tP]),
    tZ = (0, s.useMemo)(() => ({
      onSortChange: e => tM.current.handleSortChange(e),
      onOrderChange: e => tM.current.handleOrderChange(e),
      onFeedChange: e => tM.current.handleFeedChange(e),
      onNsfwChange: e => tM.current.handleNsfwChange(e),
      onPageChange: e => tM.current.handlePageChange(e),
      onShowAnimationsChange: e => er(e),
      onAnimationsPause: e => ea(e),
      onWatchlistPageChange: () => {},
      onWatchlistBackClick: () => tM.current.handleFeedChange(en.z.TERMINAL),
      addToBookmark: (e, t) => tB(e, t || "default"),
      removeFromBookmark: (e, t) => tz(e, t || "default")
    }), [er, ea, tB, tz]),
    tJ = (0, s.useMemo)(() => A.selectedFeed === en.z.WATCHLIST && tF?.length === 0 && !tO, [A.selectedFeed, tF?.length, tO]),
    {
      fetchBatchATH: tQ,
      athMap: tY
    } = (0, eH.f)(),
    t0 = (0, s.useMemo)(() => [...th].sort().join(","), [th]);
  (0, s.useEffect)(() => {
    t0 && tQ(t0.split(","));
  }, [t0, tQ]);
  let t1 = (0, s.useMemo)(() => ({
    coins: ep || [],
    bookmarkedCoins: tF || [],
    bookmarks: tP || [],
    bookmarkedCoinMints: tX,
    tableNotificationCoins: _,
    onTableNotificationExpand: tT,
    followedHoldersByMint: tx,
    rowsMatchBoard: tp,
    callsStatus: tb ? {
      partial: tv?.complete === !1,
      heldOver: tv?.heldOver === !0,
      generatedAt: tv?.generatedAt ?? null
    } : void 0,
    sort: A.sort,
    order: A.order,
    selectedFeed: A.selectedFeed,
    includeNsfw: A.includeNsfw,
    showAnimations: et,
    areAnimationsPaused: es,
    pauseAnimations: es,
    shouldShowAnimations: eo,
    selectedBookmark: B,
    offset: A.offset,
    hasMorePages: ex,
    pageSize: (0, eh.m)(L),
    watchlistOffset: 0,
    lastUpdatedMint: tc,
    athMap: tY,
    sourceScreen: t$,
    searchTerm: I || "",
    isLoading: ef,
    isWatchlistLoading: tO,
    isWatchlistEmpty: tJ,
    feedError: eg,
    onRetryFeed: tC,
    bookmarkedCoinsUpdatedAt: tW,
    isUserValid: h,
    isSearchMode: L,
    hasActiveFilters: $,
    appliedFiltersKey: U,
    appliedMarketCapRange: V,
    appliedVolumeRange: D,
    hasMarketCapFilter: H,
    hasVolumeFilter: G,
    filterConstants: ee,
    onSortChange: tZ.onSortChange,
    onOrderChange: tZ.onOrderChange,
    onFeedChange: tZ.onFeedChange,
    onNsfwChange: tZ.onNsfwChange,
    onShowAnimationsChange: tZ.onShowAnimationsChange,
    onAnimationsPause: tZ.onAnimationsPause,
    onPageChange: tZ.onPageChange,
    onWatchlistPageChange: tZ.onWatchlistPageChange,
    onBookmarkClick: tH,
    onClearSearch: S,
    onWatchlistBackClick: tZ.onWatchlistBackClick,
    onManageWatchlistClick: tK,
    addToBookmark: tZ.addToBookmark,
    removeFromBookmark: tZ.removeFromBookmark,
    createBookmark: tV,
    deleteBookmark: tD,
    updateBookmarkName: tU,
    handleApplyFilters: K,
    handleClearFilters: q,
    resetMarketCapFilter: X,
    resetVolumeFilter: Z,
    formatFilterValue: Y,
    onFiltersChange: tq,
    isManageWatchlistOpen: b,
    hasOpenedManageWatchlistDialog: v,
    setIsManageWatchlistOpen: tG
  }), [ep, tF, tP, tX, _, tT, tx, tp, tv, tb, A.sort, A.order, A.selectedFeed, A.includeNsfw, et, es, eo, B, A.offset, ex, tc, t$, I, ef, tO, tJ, eg, tC, tW, h, L, $, U, V, D, H, G, ee, tZ, tH, S, tK, tV, tD, tU, K, q, X, Z, Y, tq, b, v, tG]);
  return (0, s.useEffect)(() => {
    A.isSearchMode && "" !== A.searchTerm.trim() && E(!0);
  }, [A.sort, A.order, A.includeNsfw, A.isSearchMode, A.searchTerm, E]), (0, s.useEffect)(() => {
    p();
  }, [p]), (0, t.jsxs)(t.Fragment, {
    children: [(0, t.jsx)(ek, {
      ...t1
    }), (0, t.jsx)(o.ConditionalMobileAppsFlyerSmartBanner, {})]
  });
};
  return Object.freeze({HomePageContainer,PresentationFrame:ek,CoinGrid:I,AnimatedGrid:w,Pagination:ee,LinkPagination:er,pageNumbers:Q,PartialStatus:D,FeedError:H,admitLiveCoin:tl});
}
