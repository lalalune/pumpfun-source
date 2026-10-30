// Complete inactive badge and read-ahead owners; prior read/query cores are required ports.
export function createHomeFeedCoordination({
  React,
  useMemoCache,
  useQueryClient,
  useFollowingEvents,
  prefetchHome,
  prefetchTop,
  followingQueryOptions,
  followingPrefixKey,
  followingChainKey,
  followingChain,
  followingKinds,
}) {
  for (const fn of [
    React?.useEffect,
    React?.useState,
    useMemoCache,
    useQueryClient,
    useFollowingEvents,
    prefetchHome,
    prefetchTop,
    followingQueryOptions,
    followingPrefixKey,
    followingChainKey,
    followingChain?.m,
    followingChain?.R,
  ])
    if (typeof fn !== "function")
      throw TypeError(
        "all explicit coordination/runtime/read/key/event capabilities required",
      );
  if (typeof followingKinds !== "string")
    throw TypeError("original following kinds namespace required");
  const em = { Z: prefetchHome };
  const ei = { f: useFollowingEvents };
  const i = React;
  const ep = { H: prefetchTop };
  const l = { c: useMemoCache };
  const Y = { useQueryClient };
  const eo = followingChain;
  const en = { G: followingKinds };
  const ec = followingQueryOptions,
    et = followingPrefixKey,
    el = followingChainKey;
  function eu(e) {
    return e && e.pages.length > 1
      ? { pages: e.pages.slice(0, 1), pageParams: e.pageParams.slice(0, 1) }
      : void 0;
  }
  const useFollowingBadge = function (e) {
      let t,
        r,
        a,
        n,
        o,
        s,
        d = (0, l.c)(15),
        { viewer: c, isActive: u, chain: m } = e,
        f = void 0 === m ? "all" : m,
        p = null !== c,
        g = (0, Y.useQueryClient)();
      d[0] !== f || d[1] !== c
        ? ((t = el(c, 20, en.G, (0, eo.R)((0, eo.m)(f)))),
          (d[0] = f),
          (d[1] = c),
          (d[2] = t))
        : (t = d[2]);
      let b = t;
      d[3] === Symbol.for("react.memo_cache_sentinel")
        ? ((r = []), (d[3] = r))
        : (r = d[3]);
      let [x, h] = (0, i.useState)(r);
      d[4] !== g || d[5] !== c
        ? ((a = (e) => {
            h((t) => (t.includes(e.id) ? t : [...t, e.id]));
            let t = et(c, 20, en.G);
            (g.setQueriesData({ queryKey: t }, eu),
              g.invalidateQueries({ queryKey: t, refetchType: "none" }));
          }),
          (d[4] = g),
          (d[5] = c),
          (d[6] = a))
        : (a = d[6]);
      let w = a,
        y = p && !u;
      (d[7] !== b || d[8] !== w || d[9] !== y || d[10] !== c
        ? ((n = {
            enabled: y,
            viewer: c,
            queryKey: b,
            kinds: en.G,
            surface: "classic-tab-badge",
            onNewContent: w,
          }),
          (d[7] = b),
          (d[8] = w),
          (d[9] = y),
          (d[10] = c),
          (d[11] = n))
        : (n = d[11]),
        (0, ei.f)(n),
        u && x.length > 0 && h([]));
      let [v, _] = (0, i.useState)(c);
      v !== c && (_(c), h([]));
      let j = p && !u ? x.length : 0;
      d[12] === Symbol.for("react.memo_cache_sentinel")
        ? ((o = () => {
            h([]);
          }),
          (d[12] = o))
        : (o = d[12]);
      let N = o;
      return (
        d[13] !== j
          ? ((s = { newCount: j, reset: N }), (d[13] = j), (d[14] = s))
          : (s = d[14]),
        s
      );
    },
    useHomeReadAhead = (e) => {
      let t,
        r,
        a = (0, l.c)(8),
        {
          chain: n,
          followingChain: o,
          isLoggedIn: s,
          address: d,
          viewer: c,
        } = e,
        u = void 0 === o ? "all" : o,
        m = (0, Y.useQueryClient)();
      (a[0] !== d ||
      a[1] !== n ||
      a[2] !== u ||
      a[3] !== s ||
      a[4] !== m ||
      a[5] !== c
        ? ((t = () => {
            ((0, em.Z)(m, {
              chain: n,
              includeFollowedHolders: s,
              viewerAddress: d,
            }),
              (0, ep.H)(m, { includeFollowedHolders: s }),
              ((e, t) => {
                let { viewer: l, pageSize: r = 20, chain: i = "all" } = t;
                return null === l
                  ? Promise.resolve()
                  : e.prefetchInfiniteQuery(
                      ec({ viewer: l, pageSize: r, chain: i }),
                    );
              })(m, { viewer: c, chain: u }));
          }),
          (r = [m, n, u, s, d, c]),
          (a[0] = d),
          (a[1] = n),
          (a[2] = u),
          (a[3] = s),
          (a[4] = m),
          (a[5] = c),
          (a[6] = t),
          (a[7] = r))
        : ((t = a[6]), (r = a[7])),
        (0, i.useEffect)(t, r));
    };
  return { useFollowingBadge, useHomeReadAhead, trimExtraPages: eu };
}
