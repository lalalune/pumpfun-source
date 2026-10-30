// Editable complete main /live row carousel, geometry, selection and snap flow.
// Captures are parsed only; actual Card and provider/navigation behavior are excluded.
function buildGeometry(imports,dom,cardCounts){
const {IntersectionObserver,ResizeObserver,MutationObserver}=dom;
var t=imports(445242);
var a=imports(352386);
return{65769:{"f":({
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
}},70678:{"f":({
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
}},798394:{"f":e => {
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
}}};
}

function buildCarousel(imports,dom,cardCounts){
const {IntersectionObserver,ResizeObserver,MutationObserver}=dom;
var t=imports(732486);
var i=imports(426091);
var r=imports(352386);
var l=imports(445242);
var n=imports(798394);
var o=imports(70678);
var c=imports(65769);
let s = ({
  cardCount: e,
  gapPx: t
}) => {
  let i = "number" == typeof e,
    r = i ? e : e.large,
    s = i ? e : e.small,
    l = i ? e : e.extraSmall;
  if (r < 1 || s < 1 || l < 1) throw Error("Card count must be greater than 0");
  return {
    "--card-width-extra-small": `calc((100cqw - ${(({
      itemCount: e,
      gapPx: t
    }) => t * (e - 1))({
      itemCount: l,
      gapPx: t
    })}px) / ${l})`,
    "--card-width-small": `calc((100cqw - ${(({
      itemCount: e,
      gapPx: t
    }) => t * (e - 1))({
      itemCount: s,
      gapPx: t
    })}px) / ${s})`,
    "--card-width-large": `calc((100cqw - ${(({
      itemCount: e,
      gapPx: t
    }) => t * (e - 1))({
      itemCount: r,
      gapPx: t
    })}px) / ${r})`
  };
};
let a = e => {
  let i,
    s,
    a,
    n = (0, l.c)(6),
    {
      children: o,
      scrollRoot: c
    } = e,
    d = (0, r.useRef)(null),
    [m, u] = (0, r.useState)(!1);
  n[0] !== m || n[1] !== c ? (i = () => {
    if (m || !d.current || !c.current) return;
    let e = new IntersectionObserver(t => {
      let [i] = t;
      i.isIntersecting && (u(!0), e.disconnect());
    }, {
      root: c.current,
      rootMargin: "0px 300px 0px 300px"
    });
    return e.observe(d.current), () => e.disconnect();
  }, s = [m, c], n[0] = m, n[1] = c, n[2] = i, n[3] = s) : (i = n[2], s = n[3]), (0, r.useEffect)(i, s);
  let f = m ? o : null;
  return n[4] !== f ? (a = (0, t.jsx)("div", {
    ref: d,
    className: "w-full h-full",
    children: f
  }), n[4] = f, n[5] = a) : a = n[5], a;
};
return{1074:{"Carousel":({
  cardCount: e,
  gapPx: l,
  children: d,
  className: m,
  scrollContainerClassName: u,
  selectedIndex: f,
  onSnapIndexChange: h,
  onScrollNearEnd: x,
  useViewportIntersection: p = !1,
  eager: v = !1
}) => {
  let {
    containerRef: g,
    scrollRef: b,
    cardWidth: w
  } = (0, n.f)({
    gapPx: l
  });
  (0, o.f)({
    selectedIndex: f,
    scrollRef: b,
    cardWidth: w
  }), (0, c.f)({
    scrollRef: b,
    cardWidth: w,
    onSnapIndexChange: h
  });
  let y = (0, r.useRef)(null),
    N = (0, r.useRef)(x);
  N.current = x;
  let j = !!x;
  return (0, r.useEffect)(() => {
    let e = y.current,
      t = b.current;
    if (!e || !j || !p && !t) return;
    let i = new IntersectionObserver(e => {
      e[0].isIntersecting && N.current?.();
    }, {
      root: p ? null : t,
      rootMargin: p ? "0px 0px 400px 0px" : "0px 200px 200px 0px",
      threshold: 0
    });
    return i.observe(e), () => i.disconnect();
  }, [j, b, u, p, d.length]), (0, t.jsx)("div", {
    ref: g,
    className: (0, i.c)("@container -my-2", m),
    style: s({
      cardCount: e,
      gapPx: l
    }),
    children: (0, t.jsxs)("div", {
      ref: b,
      className: (0, i.c)("flex flex-row overflow-x-auto scrollbar-hidden snap-x snap-mandatory py-2", u),
      style: {
        gap: l
      },
      children: [d.map((e, i) => (0, t.jsx)("div", {
        className: "snap-start flex-shrink-0 w-[var(--card-width-extra-small)] md:w-[var(--card-width-small)] xl:w-[var(--card-width-large)]",
        children: v ? (0, t.jsx)("div", {
          className: "w-full h-full",
          children: e
        }) : (0, t.jsx)(a, {
          scrollRoot: b,
          children: e
        })
      }, i)), x && (0, t.jsx)("div", {
        ref: y,
        "aria-hidden": !0,
        className: "pointer-events-none flex-shrink-0 h-px w-px"
      })]
    })
  });
}},502540:{"f":s}};
}

function buildRows(imports,dom,cardCounts){
const {IntersectionObserver,ResizeObserver,MutationObserver}=dom;
var t=imports(732486);
var i=imports(445242);
var r=imports(763145);
var s=imports(1074);
const l=cardCounts;
function a(e, i) {
  return (0, t.jsx)(r.Card, {
    ...e,
    index: i
  }, e.id);
}
return{647145:{"X":e => {
  let r,
    n,
    o = (0, i.c)(9),
    {
      className: c,
      scrollContainerClassName: d,
      livestreams: m,
      onScrollNearEnd: u,
      useViewportIntersection: f,
      eager: h
    } = e;
  return o[0] !== m ? (r = m.map(a), o[0] = m, o[1] = r) : r = o[1], o[2] !== c || o[3] !== h || o[4] !== u || o[5] !== d || o[6] !== r || o[7] !== f ? (n = (0, t.jsx)(s.Carousel, {
    cardCount: l,
    gapPx: 16,
    className: c,
    scrollContainerClassName: d,
    onScrollNearEnd: u,
    useViewportIntersection: f,
    eager: h,
    children: r
  }), o[2] = c, o[3] = h, o[4] = u, o[5] = d, o[6] = r, o[7] = f, o[8] = n) : n = o[8], n;
}}};
}

// Authored construction: actual React/JSX/compiler/classnames/Card/DOM implementations remain capabilities.
export function createLiveRowCarousel({React,jsx,compiler,classNames,Card,cardCounts,dom}){
 if(typeof React?.useEffect!=='function'||typeof jsx?.jsx!=='function'||typeof jsx?.jsxs!=='function'||typeof compiler?.c!=='function'||typeof classNames!=='function'||typeof Card!=='function'||!cardCounts||
    !['extraSmall','small','large'].every(k=>Object.hasOwn(cardCounts,k))||!['IntersectionObserver','ResizeObserver','MutationObserver'].every(k=>typeof dom?.[k]==='function'))
   throw new TypeError('actual React/JSX/compiler/classnames/Card/count and DOM capabilities are required');
 const owned=new Map([[352386,React],[732486,jsx],[445242,compiler],[426091,{c:classNames}],[763145,{Card}]]);
 const imports=id=>{if(!owned.has(id))throw new TypeError('missing actual carousel import '+id);return owned.get(id);};
 for(const build of[buildGeometry,buildCarousel,buildRows])for(const[id,value]of Object.entries(build(imports,dom,cardCounts)))owned.set(Number(id),value);
 return Object.freeze({Rows:owned.get(647145).X,Carousel:owned.get(1074).Carousel,cardWidths:owned.get(502540).f,
   useGeometry:owned.get(798394).f,useSelection:owned.get(70678).f,useSnap:owned.get(65769).f});
}
