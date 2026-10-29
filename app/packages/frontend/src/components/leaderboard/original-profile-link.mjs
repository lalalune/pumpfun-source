"use client";
export { c as useMemoCache } from "react/compiler-runtime";
export { profileRoute } from "../../../../../reconstruction/search-navigation/navigation.mjs";
// Complete source-adapted common409954.o; original material retains its authorship.
// Ports retain Next/React/class-merging/navigation boundaries; no bundle factory executes.
export function createProfileLinkModule({
  jsx,
  useMemoCache,
  useContext,
  createContext,
  Link,
  profileRoute,
  classNames,
  isOrdinaryClick,
}) {
  const t = { jsx: jsx },
    r = { c: useMemoCache },
    i = { $: profileRoute },
    l = { default: Link },
    o = { useContext: useContext },
    n = { c: classNames },
    s = { f: isOrdinaryClick };
  const a = createContext(null);
  const ProfileLink = (e) => {
    let c,
      d,
      u,
      f,
      p,
      m,
      h,
      x,
      g,
      y,
      w = (0, r.c)(23);
    w[0] !== e
      ? (({
          profileId: m,
          href: u,
          className: d,
          onClick: p,
          children: c,
          ...f
        } = e),
        (w[0] = e),
        (w[1] = c),
        (w[2] = d),
        (w[3] = u),
        (w[4] = f),
        (w[5] = p),
        (w[6] = m))
      : ((c = w[1]),
        (d = w[2]),
        (u = w[3]),
        (f = w[4]),
        (p = w[5]),
        (m = w[6]));
    let { isPending: b, onClick: v } = ((e) => {
      let t,
        i,
        l = (0, r.c)(7),
        n = (0, o.useContext)(a);
      if (!n || !e) {
        let e;
        return (
          l[0] === Symbol.for("react.memo_cache_sentinel")
            ? ((e = { isPending: !1, onClick: void 0 }), (l[0] = e))
            : (e = l[0]),
          e
        );
      }
      l[1] !== e || l[2] !== n
        ? ((t = (t) => {
            (0, s.f)(t) && (t.preventDefault(), n.navigateToProfile(e));
          }),
          (l[1] = e),
          (l[2] = n),
          (l[3] = t))
        : (t = l[3]);
      let c = t,
        d = n.pendingProfileId === e;
      return (
        l[4] !== c || l[5] !== d
          ? ((i = { isPending: d, onClick: c }),
            (l[4] = c),
            (l[5] = d),
            (l[6] = i))
          : (i = l[6]),
        i
      );
    })(m);
    w[7] !== p || w[8] !== v
      ? ((h = (e) => {
          (p?.(e), v?.(e));
        }),
        (w[7] = p),
        (w[8] = v),
        (w[9] = h))
      : (h = w[9]);
    let j = h;
    w[10] !== u || w[11] !== m
      ? ((x = u ?? (0, i.$)(m)), (w[10] = u), (w[11] = m), (w[12] = x))
      : (x = w[12]);
    let _ = b || void 0,
      I = b && "cursor-progress opacity-60";
    return (
      w[13] !== d || w[14] !== I
        ? ((g = (0, n.c)(d, I)), (w[13] = d), (w[14] = I), (w[15] = g))
        : (g = w[15]),
      w[16] !== c ||
      w[17] !== f ||
      w[18] !== j ||
      w[19] !== x ||
      w[20] !== _ ||
      w[21] !== g
        ? ((y = (0, t.jsx)(l.default, {
            ...f,
            href: x,
            onClick: j,
            "aria-busy": _,
            className: g,
            children: c,
          })),
          (w[16] = c),
          (w[17] = f),
          (w[18] = j),
          (w[19] = x),
          (w[20] = _),
          (w[21] = g),
          (w[22] = y))
        : (y = w[22]),
      y
    );
  };
  return { ProfileLink, ProfileNavigationProvider: a.Provider };
}
