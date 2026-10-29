// Editable complete main /live query/unlock/read-state components.
// Original captures are parsed only; service/player/provider bodies stay ports.
function buildKinds(imports,listing,projectHeroCoin,useClipsSection,FloatingControl,dom){
var t,
  a = ((t = {}).HIGHEST_MARKET_CAP = "highest-market-cap", t.MOST_VIEWERS = "most-viewers", t.TRENDING_CLIPS = "trending-clips", t.POPULAR_RECORDINGS = "popular-recordings", t.NEW_CREATORS = "new-creators", t.FOR_YOU = "for-you", t);
return {788501:{"f":a}};
}

function buildQueries(imports,listing,projectHeroCoin,useClipsSection,FloatingControl,dom){
var a=imports(445242);
var i=imports(761459);
var l=imports(690877);
var r=imports(133244);
var f=imports(369091);
var h=imports(358893);
const {fetchCoins:y,fetchSection:j,nextLivePage:S,selectLivePages:k,livePageIdentity:P,LIVE_SORTS:o}=listing;
let n = 24;
let w = async e => (await y({
    limit: r.E,
    offset: 0,
    livePageSort: o.FEATURED,
    ...e
  })).map(r.g),
  N = e => {
    let t,
      i,
      r,
      s = (0, a.c)(10),
      {
        initialData: n,
        staleTime: c
      } = e,
      o = void 0 === c ? 1e4 : c,
      d = (0, h.M)(),
      {
        ipfsPrefix: m
      } = (0, f.useIpfsPrefix)();
    return s[0] !== d ? (t = ["live-hero-coins", d], s[0] = d, s[1] = t) : t = s[1], s[2] !== d || s[3] !== m ? (i = () => w({
      includeNsfw: d,
      ipfsPrefix: m
    }), s[2] = d, s[3] = m, s[4] = i) : i = s[4], s[5] !== n || s[6] !== o || s[7] !== t || s[8] !== i ? (r = {
      queryKey: t,
      queryFn: i,
      initialData: n,
      staleTime: o
    }, s[5] = n, s[6] = o, s[7] = t, s[8] = i, s[9] = r) : r = s[9], (0, l.useQuery)(r);
  },
  E = e => {
    let t,
      l,
      r,
      s,
      c,
      o,
      d = (0, a.c)(21),
      {
        limit: m,
        livePageSort: u,
        initialData: x,
        staleTime: p
      } = e,
      v = void 0 === m ? n : m,
      g = void 0 === p ? 1e4 : p,
      b = (0, h.M)(),
      {
        ipfsPrefix: y
      } = (0, f.useIpfsPrefix)();
    d[0] !== b || d[1] !== y || d[2] !== v || d[3] !== u ? (t = ["live-section-coins", u, b, v, y], l = async e => {
      let {
        pageParam: t
      } = e;
      return j({
        offset: t,
        limit: v,
        livePageSort: u,
        includeNsfw: b,
        ipfsPrefix: y
      });
    }, d[0] = b, d[1] = y, d[2] = v, d[3] = u, d[4] = t, d[5] = l) : (t = d[4], l = d[5]), d[6] !== x ? (r = x ? {
      pages: [x],
      pageParams: [0]
    } : void 0, d[6] = x, d[7] = r) : r = d[7], d[8] !== g || d[9] !== t || d[10] !== l || d[11] !== r ? (s = {
      queryKey: t,
      queryFn: l,
      initialPageParam: 0,
      getNextPageParam: S,
      select: k,
      initialData: r,
      staleTime: g
    }, d[8] = g, d[9] = t, d[10] = l, d[11] = r, d[12] = s) : s = d[12];
    let _ = (0, i.useInfiniteQuery)(s);
    return d[13] !== _.data?.pages ? (c = _.data?.pages.flatMap(P) ?? [], d[13] = _.data?.pages, d[14] = c) : c = d[14], d[15] !== _.fetchNextPage || d[16] !== _.hasNextPage || d[17] !== _.isFetchingNextPage || d[18] !== _.isLoading || d[19] !== c ? (o = {
      data: c,
      isLoading: _.isLoading,
      fetchNextPage: _.fetchNextPage,
      hasNextPage: _.hasNextPage,
      isFetchingNextPage: _.isFetchingNextPage
    }, d[15] = _.fetchNextPage, d[16] = _.hasNextPage, d[17] = _.isFetchingNextPage, d[18] = _.isLoading, d[19] = c, d[20] = o) : o = d[20], o;
  };
return {539335:{"f":o},606706:{"B":1e4,"o":10,"R":100,"O":n},859960:{"A":j,"L":N,"N":E}};
}

function buildHero(imports,listing,projectHeroCoin,useClipsSection,FloatingControl,dom){
var t=imports(732486);
var a=imports(445242);
var i=imports(369731);
var l=imports(187807);
var r=imports(218921);
var s=imports(918391);
var n=imports(829010);
var c=imports(859960);
const d=projectHeroCoin;
let o = 6,
  m = e => {
    let d,
      m,
      u = (0, a.c)(5),
      {
        initialData: f
      } = e;
    u[0] !== f ? (d = {
      initialData: f
    }, u[0] = f, u[1] = d) : d = u[1];
    let {
      data: h,
      isLoading: x
    } = (0, c.L)(d);
    if (x) {
      let e;
      return u[2] === Symbol.for("react.memo_cache_sentinel") ? (e = (0, t.jsxs)("div", {
        className: "flex flex-col gap-3 isolate",
        children: [(0, t.jsx)(l.HeroStage, {
          children: (0, t.jsx)("div", {
            className: n.F,
            children: (0, t.jsx)(s.f, {})
          })
        }), (0, t.jsx)(r.PaginationDotsSkeleton, {
          count: o
        })]
      }), u[2] = e) : e = u[2], e;
    }
    return h && 0 !== h.length ? (u[3] !== h ? (m = (0, t.jsx)(i.HeroCarousel, {
      livestreams: h
    }), u[3] = h, u[4] = m) : m = u[4], m) : null;
  };
return {133244:{"E":o,"_":m,"g":d}};
}

function buildSections(imports,listing,projectHeroCoin,useClipsSection,FloatingControl,dom){
var t=imports(788501);
var i=imports(859960);
var r=imports(445242);
var l=imports(647145);
var A=imports(539335);
var M=imports(732486);
var F=imports(157633);
var O=imports(426091);
var D=imports(458310);
var U=imports(352386);
var H=imports(398902);
var V=imports(314982);
const E=useClipsSection;
let z = [{
    id: t.f.MOST_VIEWERS,
    titleKey: "livestream.feed.sort.most_viewers",
    useFetch: e => (0, i.N)({
      livePageSort: A.f.MOST_VIEWERS,
      ...e
    }),
    fetch: e => (0, i.A)({
      livePageSort: A.f.MOST_VIEWERS,
      ...e
    })
  }, {
    id: t.f.HIGHEST_MARKET_CAP,
    titleKey: "web.live.section_highest_market_cap",
    useFetch: e => (0, i.N)({
      livePageSort: A.f.MARKET_CAP,
      ...e
    }),
    fetch: e => (0, i.A)({
      livePageSort: A.f.MARKET_CAP,
      ...e
    })
  }, {
    id: t.f.TRENDING_CLIPS,
    titleKey: "web.live.section_trending_clips",
    useFetch: e => E({
      ...e,
      sectionId: t.f.TRENDING_CLIPS
    })
  }, {
    id: t.f.POPULAR_RECORDINGS,
    titleKey: "web.live.section_popular_recordings",
    useFetch: e => E({
      ...e,
      sectionId: t.f.POPULAR_RECORDINGS
    })
  }, {
    id: t.f.NEW_CREATORS,
    titleKey: "web.live.section_new_creators",
    useFetch: () => ({
      data: [],
      isLoading: !1,
      fetchNextPage: () => {},
      hasNextPage: !1,
      isFetchingNextPage: !1
    })
  }, {
    id: t.f.FOR_YOU,
    titleKey: "web.live.section_for_you",
    subtitleKey: "web.live.section_for_you_subtitle",
    useFetch: () => ({
      data: [],
      isLoading: !1,
      fetchNextPage: () => {},
      hasNextPage: !1,
      isFetchingNextPage: !1
    })
  }],
  P = new Map(z.map(e => [e.id, e]));
let K = e => {
  let t,
    i,
    s,
    l,
    a = (0, r.c)(8),
    {
      sectionId: n
    } = e,
    {
      t: o
    } = (0, H.f)(),
    c = `/live/${n}`;
  return a[0] !== o ? (t = o("web.live.show_all"), a[0] = o, a[1] = t) : t = a[1], a[2] !== t ? (i = (0, M.jsx)("p", {
    className: "text-sm font-medium",
    children: t
  }), a[2] = t, a[3] = i) : i = a[3], a[4] === Symbol.for("react.memo_cache_sentinel") ? (s = (0, M.jsx)(F.kK, {
    size: 12,
    className: "transition-transform duration-200"
  }), a[4] = s) : s = a[4], a[5] !== c || a[6] !== i ? (l = (0, M.jsxs)(D.default, {
    className: "flex flex-row items-center gap-2.5",
    href: c,
    children: [i, s]
  }), a[5] = c, a[6] = i, a[7] = l) : l = a[7], l;
};
return {944001:{"Z":z,"A":P},310766:{"Z":({
  sectionId: e,
  titleKey: t,
  subtitleKey: i,
  onShowAll: r,
  onSectionComplete: s,
  limit: a,
  isExpanded: n = !1,
  useFetch: o,
  initialData: c,
  eager: d = !1
}) => {
  let {
      t: m
    } = (0, H.f)(),
    {
      data: u,
      isLoading: f,
      fetchNextPage: h,
      hasNextPage: x,
      isFetchingNextPage: p
    } = o({
      limit: a,
      initialData: c
    });
  (0, U.useEffect)(() => {
    f || s?.(e);
  }, [f, e, s]);
  let v = (0, U.useCallback)(() => {
    x && !p && h();
  }, [x, p, h]);
  if (f) return (0, M.jsx)(V.SectionSkeleton, {});
  if (0 === u.length) return null;
  let g = r && (u.length > l.g.large || x);
  return (0, M.jsxs)("div", {
    className: "flex flex-col gap-4",
    children: [(0, M.jsxs)("div", {
      className: "flex flex-row items-center justify-between",
      children: [(0, M.jsxs)("div", {
        className: "flex flex-row items-center gap-2",
        children: [!g && n && (0, M.jsx)(D.default, {
          href: "/live",
          children: (0, M.jsx)(F.S, {
            size: 18
          })
        }), (0, M.jsxs)("p", {
          className: "text-xl font-semibold",
          children: [m(t), " ", i && (0, M.jsx)("span", {
            className: "text-text-mid-em text-sm",
            children: m(i)
          })]
        })]
      }), g && (0, M.jsx)(K, {
        sectionId: e
      })]
    }), (0, M.jsx)(l.X, {
      livestreams: u,
      scrollContainerClassName: (0, O.c)(n ? "flex-wrap" : "flex-nowrap"),
      onScrollNearEnd: v,
      useViewportIntersection: n,
      eager: d
    })]
  });
},"R":300}};
}

function buildHomepage(imports,listing,projectHeroCoin,useClipsSection,FloatingControl,dom){
var t=imports(732486);
var s=imports(445242);
var i=imports(599077);
var a=imports(352386);
var c=imports(133244);
var l=imports(944001);
var n=imports(310766);
var m=imports(314982);
var r=imports(327294);
var d=imports(79472);
const f=FloatingControl; const {IntersectionObserver}=dom;
let u = e => {
  let i,
    c,
    l,
    u,
    r,
    o = (0, s.c)(10);
  o[0] !== e ? ({
    isUnlocked: i,
    eager: l,
    ...c
  } = e, o[0] = e, o[1] = i, o[2] = c, o[3] = l) : (i = o[1], c = o[2], l = o[3]);
  let h = void 0 !== l && l,
    b = (0, a.useRef)(null),
    j = i && !h;
  o[4] !== j ? (u = {
    enabled: j
  }, o[4] = j, o[5] = u) : u = o[5];
  let f = ((e, t, i) => {
    let c,
      l,
      n = (0, s.c)(6),
      [m, u] = (0, a.useState)(!1),
      r = i?.enabled ?? !0;
    return n[0] !== r || n[1] !== m || n[2] !== e || n[3] !== t ? (c = () => {
      if (!r || m || !e.current) return;
      let s = new IntersectionObserver(e => {
        let [t] = e;
        t.isIntersecting && (u(!0), s.disconnect());
      }, {
        rootMargin: `${Math.floor(t / 2)}px`
      });
      return s.observe(e.current), () => s.disconnect();
    }, l = [r, m, e, t], n[0] = r, n[1] = m, n[2] = e, n[3] = t, n[4] = c, n[5] = l) : (c = n[4], l = n[5]), (0, a.useEffect)(c, l), m;
  })(b, n.R, u);
  if (!i) return null;
  if (!h && !f) {
    let e;
    return o[6] === Symbol.for("react.memo_cache_sentinel") ? (e = (0, t.jsx)(m.SectionSkeleton, {
      ref: b,
      className: "opacity-0"
    }), o[6] = e) : e = o[6], e;
  }
  return o[7] !== h || o[8] !== c ? (r = (0, t.jsx)(n.Z, {
    ...c,
    eager: h
  }), o[7] = h, o[8] = c, o[9] = r) : r = o[9], r;
};
function k() {
  return new Set();
}
return {31113:{"LiveHomepage":e => {
  let n,
    m,
    o,
    h,
    b,
    j = (0, s.c)(12),
    {
      initialHeroData: x,
      initialSectionData: v
    } = e,
    g = (0, i.useRouter)(),
    p = (0, d.V)(),
    [y, _] = (0, a.useState)(k);
  j[0] === Symbol.for("react.memo_cache_sentinel") ? (n = e => {
    _(t => new Set(t).add(e));
  }, j[0] = n) : n = j[0];
  let w = n;
  if (p) {
    let e;
    return j[1] === Symbol.for("react.memo_cache_sentinel") ? (e = (0, t.jsx)("div", {
      className: "flex min-h-[50vh] items-center justify-center",
      children: (0, t.jsx)(r.LivestreamBlockedMessage, {
        className: "max-w-sm"
      })
    }), j[1] = e) : e = j[1], e;
  }
  return j[2] === Symbol.for("react.memo_cache_sentinel") ? (m = (0, t.jsx)(f, {}), j[2] = m) : m = j[2], j[3] !== x ? (o = (0, t.jsx)(c._, {
    initialData: x
  }), j[3] = x, j[4] = o) : o = j[4], j[5] !== y || j[6] !== v || j[7] !== g ? (h = l.Z.map((e, s) => (0, t.jsx)(u, {
    sectionId: e.id,
    titleKey: e.titleKey,
    subtitleKey: e.subtitleKey,
    onShowAll: () => g.push(`/live/${e.id}`),
    useFetch: e.useFetch,
    isUnlocked: 0 === s || y.has(l.Z[s - 1].id),
    onSectionComplete: w,
    initialData: v?.[s],
    eager: s < 2
  }, e.id)), j[5] = y, j[6] = v, j[7] = g, j[8] = h) : h = j[8], j[9] !== o || j[10] !== h ? (b = (0, t.jsxs)(t.Fragment, {
    children: [m, (0, t.jsxs)("div", {
      className: "pb-8 flex flex-col gap-8",
      children: [o, h]
    })]
  }), j[9] = o, j[10] = h, j[11] = b) : b = j[11], b;
}}};
}

// Authored construction only. Runtime/query/provider scheduling remains external.
export function createLiveReadState({React,jsx,compiler,modules,listing,projectHeroCoin,useClipsSection,FloatingControl,dom}){
  for(const key of ['fetchCoins','fetchSection','nextLivePage','selectLivePages','livePageIdentity'])
    if(typeof listing?.[key]!=='function')throw new TypeError('explicit1821 listing operation required: '+key);
  if(!listing.LIVE_SORTS||!listing.LIVE_CARD_COUNTS||typeof projectHeroCoin!=='function'||typeof useClipsSection!=='function'||
    !React||typeof jsx?.jsx!=='function'||typeof compiler?.c!=='function'||!modules||!FloatingControl||typeof dom?.IntersectionObserver!=='function')
    throw new TypeError('explicit original read-state/render/query/provider/DOM capabilities are required');
  const owned=new Map([[352386,React],[732486,jsx],[445242,compiler],
    [133244,{E:6,g:projectHeroCoin}], [647145,{g:listing.LIVE_CARD_COUNTS,X:modules[647145]?.X}]]);
  const imports=(id)=>{if(owned.has(id))return owned.get(id);if(!Object.hasOwn(modules,id))throw new TypeError('missing original module capability '+id);return modules[id];};
  for(const build of [buildKinds,buildQueries,buildHero,buildSections,buildHomepage])
    for(const[id,value]of Object.entries(build(imports,listing,projectHeroCoin,useClipsSection,FloatingControl,dom))){
      if(owned.has(Number(id)))Object.assign(owned.get(Number(id)),value);else owned.set(Number(id),value);}
  return Object.freeze({LiveHomepage:owned.get(31113).LiveHomepage,Hero:owned.get(133244)._,
    useHero:owned.get(859960).L,useSection:owned.get(859960).N,Section:owned.get(310766).Z,
    sections:owned.get(944001).Z,sectionById:owned.get(944001).A});
}
