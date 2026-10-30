// Complete captured shared refs, initializer and snapshot hook. Construct one shared realm instance.
export function createReducedMotionSnapshot({ React, window }) {
  if (typeof React?.useState !== "function")
    throw new TypeError("Explicit React.useState required");
  const shared = (() => {
    let e = { current: null },
      i = { current: !1 },
      s = "u" > typeof window;
    return {
      E: i,
      d: e,
      initialize: function () {
        if (((i.current = !0), s))
          if (window.matchMedia) {
            let t = window.matchMedia("(prefers-reduced-motion)"),
              i = () => (e.current = t.matches);
            (t.addEventListener("change", i), i());
          } else e.current = !1;
      },
    };
  })();
  const t = shared,
    i = { f: shared.initialize },
    r = { useState: React.useState };
  return function () {
    t.E.current || (0, i.f)();
    let [e] = (0, r.useState)(t.d.current);
    return e;
  };
}
export const AVATAR_DECORATIONS_FLAG = "webAvatarDecorations";
// Complete owners with actual JSX/compiler/class/flag/window interfaces; no asset/provider acquisition.
export function createAvatarDecorations({
  jsx,
  jsxs,
  Fragment,
  useMemoCache,
  React,
  classNames,
  useFeatureFlag,
  window,
}) {
  for (const [name, value] of Object.entries({
    jsx,
    jsxs,
    useMemoCache,
    classNames,
    useFeatureFlag,
  }))
    if (typeof value !== "function")
      throw new TypeError("Explicit decoration capability required: " + name);
  for (const name of ["useState", "isValidElement", "cloneElement"])
    if (typeof React?.[name] !== "function")
      throw new TypeError(
        "Explicit decoration React operation required: " + name,
      );
  if (Fragment == null) throw new TypeError("Explicit Fragment required");
  const t = { jsx, jsxs, Fragment },
    i = { c: useMemoCache },
    r = { c: classNames },
    n = { f: createReducedMotionSnapshot({ React, window }) },
    a = {
      isValidElement: React.isValidElement,
      cloneElement: React.cloneElement,
    },
    O = { D: { WEB_AVATAR_DECORATIONS: AVATAR_DECORATIONS_FLAG } },
    y = { k: useFeatureFlag };
  let s = {
      "1000x-oracle": 288 / 252,
      "immortal-run": 288 / 252,
      "serial-winner": 380 / 252,
      "perfect-month": 580 / 252,
      "streak-365d": 398 / 252,
      "followers-1m": 522 / 252,
      "trades-100k": 406 / 252,
      "views-10m": 318 / 252,
      "callouts-2500": 426 / 252,
      "callouts-500": 352 / 252,
      "first-place": 374 / 252,
      "multiple-100x": 400 / 252,
      "post-likes-10k": 370 / 252,
      "post-likes-1k": 374 / 252,
      "streak-180d": 1.5,
      "trades-10k": 490 / 252,
      "podium-regular": 408 / 252,
      "followers-100k": 368 / 252,
      "views-1m": 382 / 252,
      "volume-10m": 384 / 252,
      phoenix: 522 / 252,
      veteran: 456 / 252,
    },
    l = {
      "followers-1m": 364 / 252,
      "perfect-month": 402 / 252,
      "trades-10k": 352 / 252,
      "views-1m": 306 / 252,
      phoenix: 394 / 252,
      veteran: 376 / 252,
    },
    u = "achievement:",
    c = (e) => "legendary" === e || "epic" === e,
    d = (e) => {
      if (c(e)) return null;
      let t = e.slice(u.length);
      return Object.hasOwn(s, t) ? t : null;
    },
    f = (e) => {
      if ("none" === e) return "none";
      if ("legendary" === e || "epic" === e) return e;
      if (e?.startsWith(u)) {
        let t = e.slice(u.length);
        if (Object.hasOwn(s, t)) return `achievement:${t}`;
      }
    },
    m = (e) => {
      let t = f(e);
      return void 0 === t || "none" === t ? null : t;
    },
    h = (e) => {
      let t = d(e);
      return null !== t && void 0 !== l[t];
    },
    p = (e, t = "profile") => {
      let i = d(e);
      return null === i ? 1.2 : (("list" === t ? l[i] : void 0) ?? s[i]);
    },
    g = "/achievements/avatar-decorations";
  function L(e) {
    let n,
      a,
      o,
      s,
      l = (0, i.c)(16),
      {
        decoration: u,
        animated: c,
        eager: d,
        variant: f,
        className: m,
        "data-testid": E,
      } = e,
      v = void 0 === c || c,
      L = void 0 === f ? "profile" : f,
      O = void 0 === E ? "profile-avatar-decoration" : E;
    l[0] !== u || l[1] !== L
      ? ((n = ((e, t = "profile") => {
          let i = "list" === t && h(e) ? "-list" : "",
            r = `${e.startsWith("achievement:") ? e.slice(12) : e}${i}`;
          return {
            animated: `${g}/${r}.webp?v=1`,
            still: `${g}/${r}-still.webp?v=1`,
          };
        })(u, L)),
        (l[0] = u),
        (l[1] = L),
        (l[2] = n))
      : (n = l[2]);
    let y = n,
      A = p(u, L),
      T = v ? y.animated : y.still,
      I = void 0 !== d && d ? "eager" : "lazy";
    l[3] !== m
      ? ((a = (0, r.c)(
          "pointer-events-none absolute left-1/2 top-1/2 aspect-square max-w-none -translate-x-1/2 -translate-y-1/2 select-none",
          m,
        )),
        (l[3] = m),
        (l[4] = a))
      : (a = l[4]);
    let C = `${100 * A}%`;
    l[5] !== C ? ((o = { width: C }), (l[5] = C), (l[6] = o)) : (o = l[6]);
    let w = v ? "true" : "false";
    return (
      l[7] !== u ||
      l[8] !== o ||
      l[9] !== w ||
      l[10] !== T ||
      l[11] !== I ||
      l[12] !== a ||
      l[13] !== O ||
      l[14] !== L
        ? ((s = (0, t.jsx)("img", {
            src: T,
            alt: "",
            "aria-hidden": !0,
            draggable: !1,
            decoding: "async",
            loading: I,
            className: a,
            style: o,
            "data-testid": O,
            "data-decoration": u,
            "data-variant": L,
            "data-animated": w,
          })),
          (l[7] = u),
          (l[8] = o),
          (l[9] = w),
          (l[10] = T),
          (l[11] = I),
          (l[12] = a),
          (l[13] = O),
          (l[14] = L),
          (l[15] = s))
        : (s = l[15]),
      s
    );
  }
  const AvatarDecorationFrame = function (e) {
    let o,
      s,
      l,
      u = (0, i.c)(13),
      {
        decoration: c,
        variant: d,
        animated: f,
        className: m,
        "data-testid": h,
        children: p,
        ...E
      } = e,
      v = void 0 === d ? "profile" : d,
      g = void 0 === h ? "avatar-decoration-frame" : h,
      O = (0, n.f)() ?? !1;
    if (null === c)
      return (0, a.isValidElement)(p)
        ? (0, a.cloneElement)(p, { ...E })
        : (0, t.jsx)(t.Fragment, { children: p });
    u[0] !== m
      ? ((o = (0, r.c)("relative flex w-fit shrink-0", m)),
        (u[0] = m),
        (u[1] = o))
      : (o = u[1]);
    let y = f ?? !O;
    return (
      u[2] !== c || u[3] !== y || u[4] !== v
        ? ((s = (0, t.jsx)(L, { decoration: c, variant: v, animated: y })),
          (u[2] = c),
          (u[3] = y),
          (u[4] = v),
          (u[5] = s))
        : (s = u[5]),
      u[6] !== p ||
      u[7] !== c ||
      u[8] !== o ||
      u[9] !== s ||
      u[10] !== g ||
      u[11] !== E
        ? ((l = (0, t.jsxs)("span", {
            ...E,
            className: o,
            "data-testid": g,
            "data-decoration": c,
            children: [p, s],
          })),
          (u[6] = p),
          (u[7] = c),
          (u[8] = o),
          (u[9] = s),
          (u[10] = g),
          (u[11] = E),
          (u[12] = l))
        : (l = u[12]),
      l
    );
  };
  const useResolvedDecoration = (e) => {
    let t,
      r = (0, i.c)(2);
    return (0, y.k)(O.D.WEB_AVATAR_DECORATIONS)
      ? (r[0] !== e ? ((t = m(e)), (r[0] = e), (r[1] = t)) : (t = r[1]), t)
      : null;
  };
  return {
    AvatarDecorationFrame,
    AvatarDecorationImage: L,
    useResolvedDecoration,
  };
}
