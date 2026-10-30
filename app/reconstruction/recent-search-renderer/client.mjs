// Complete original RecentTerms/read-state/address-row frames with explicit supplied capabilities.
import {
  normalizeSolanaInput,
  profileRoute,
} from "../search-navigation/navigation.mjs";
export function createRecentSearchRenderer(ports) {
  for (const name of [
    "useTranslation",
    "useChainFlags",
    "nearEnabled",
    "validSolanaAddress",
    "isEvmAddress",
    "canonicalCoinAddress",
    "isGroupIdentifier",
    "useGroupClient",
    "useGroupsEnabled",
    "readGroup",
    "useQueries",
    "useCoinHydration",
    "walletProfile",
    "useCoinUpdates",
    "classNames",
    "useProfile",
    "useVerifiedProfile",
    "formatFollowers",
    "memoCache",
    "groupProfileKey",
    "useNearCoins",
    "normalizeNearInput",
  ])
    if (typeof ports?.[name] !== "function")
      throw new TypeError(
        "Explicit recent search capability required: " + name,
      );
  for (const name of [
    "Heading",
    "Empty",
    "SkeletonPart",
    "Link",
    "SearchIcon",
    "ProfileDisplay",
    "CoinRow",
    "GroupRow",
  ])
    if (!ports.renderers?.[name])
      throw new TypeError("Explicit recent search renderer required: " + name);
  if (
    !ports.React ||
    !ports.jsxRuntime ||
    !ports.styles ||
    !Object.hasOwn(ports, "avatarSize")
  )
    throw new TypeError("Explicit React/JSX/style/size capabilities required");
  const a = ports.React,
    t = ports.jsxRuntime,
    r = { c: ports.memoCache },
    d = { R: normalizeSolanaInput },
    o = { $: profileRoute },
    to = ports.useNearCoins,
    ti = ports.normalizeNearInput,
    F = ports.styles.row,
    V = ports.styles.action,
    $ = ports.avatarSize,
    Z = ports.renderers.CoinRow,
    en = ports.renderers.GroupRow,
    eK = { f: { profile: ports.groupProfileKey } };
  const n = { Ae: { SEARCH: 9 }, k9: { RECENT_LIST: 30 } };
  const p = { f: ports.useTranslation };
  const eZ = { l: ports.useChainFlags, M: ports.nearEnabled };
  const tr = { f: ports.validSolanaAddress };
  const te = { h: ports.isEvmAddress, c: ports.canonicalCoinAddress };
  const c = { f: ports.isGroupIdentifier };
  const eO = { useClientServerContract: ports.useGroupClient };
  const eH = { f: ports.useGroupsEnabled };
  const eB = { N: ports.readGroup };
  const h = { f: ports.useQueries };
  const eQ = { f: ports.useCoinHydration };
  const tt = { f: ports.walletProfile };
  const eJ = { f: ports.useCoinUpdates };
  const H = { c: ports.classNames };
  const m = { T: ports.useProfile };
  const u = { s: ports.useVerifiedProfile };
  const P = { O: ports.formatFollowers };
  const q = { _: ports.renderers.Heading };
  const e_ = { L: ports.renderers.Empty };
  const T = { l: ports.renderers.SkeletonPart };
  const f = { default: ports.renderers.Link };
  const s = { L3: ports.renderers.SearchIcon };
  const A = { S: ports.renderers.ProfileDisplay };
  let tu = (e) => {
    let l,
      i,
      o,
      u,
      m,
      x,
      g,
      b,
      w,
      _,
      v = (0, r.c)(31),
      { terms: k, canExpand: y, onClear: j, onNavigate: N } = e,
      { t: C } = (0, p.f)(),
      [S, A] = (0, a.useState)(!1),
      E = y && S;
    v[0] !== E || v[1] !== k
      ? ((l = E ? k : k.slice(0, 3)), (v[0] = E), (v[1] = k), (v[2] = l))
      : (l = v[2]);
    let I = l,
      R = y && k.length > 3,
      M = ((e) => {
        let t,
          a,
          s,
          n,
          l,
          i,
          o,
          u = (0, r.c)(25),
          m = (0, eZ.l)();
        u[0] !== m ? ((t = (0, eZ.M)(m)), (u[0] = m), (u[1] = t)) : (t = u[1]);
        let f = t;
        if (u[2] !== f || u[3] !== e) {
          let t;
          (u[5] !== f
            ? ((t = (e) => ({
                term: e,
                candidate: ((e, t = !1) => {
                  let r = (0, d.R)(e);
                  if (r && (0, tr.f)(r)) return { address: r, chain: "solana" };
                  let a = e.trim();
                  if ((0, te.h)(a)) return { address: a, chain: "evm" };
                  let s = t ? ti(a) : null;
                  return s ? { address: s, chain: "near" } : null;
                })(e, f),
                groupId: (0, c.f)(e.trim()) ? e.trim() : null,
              })),
              (u[5] = f),
              (u[6] = t))
            : (t = u[6]),
            (a = e.map(t)),
            (u[2] = f),
            (u[3] = e),
            (u[4] = a));
        } else a = u[4];
        let x = a;
        u[7] !== x ? ((s = x.flatMap(tw)), (u[7] = x), (u[8] = s)) : (s = u[8]);
        let { squads: p, pendingIds: g } = ((e) => {
          let t,
            a,
            s,
            n = (0, r.c)(13),
            l = (0, eO.useClientServerContract)(),
            i = (0, eH.f)();
          if (n[0] !== l || n[1] !== e || n[2] !== i) {
            let r;
            (n[4] !== l || n[5] !== i
              ? ((r = (e) => ({
                  queryKey: eK.f.profile(e),
                  queryFn: (t) => {
                    let { signal: r } = t;
                    return (0, eB.N)({ api: l, groupId: e, signal: r });
                  },
                  enabled: i,
                  staleTime: 3e4,
                })),
                (n[4] = l),
                (n[5] = i),
                (n[6] = r))
              : (r = n[6]),
              (t = e.map(r)),
              (n[0] = l),
              (n[1] = e),
              (n[2] = i),
              (n[3] = t));
          } else t = n[3];
          return (
            n[7] !== e || n[8] !== i
              ? ((a = (t) => {
                  let r = new Map(),
                    a = new Set();
                  return (
                    i &&
                      t.forEach((t, s) => {
                        let n = e[s];
                        void 0 !== n &&
                          (void 0 !== t.data
                            ? r.set(n, t.data)
                            : t.isPending && a.add(n));
                      }),
                    { squads: r, pendingIds: a }
                  );
                }),
                (n[7] = e),
                (n[8] = i),
                (n[9] = a))
              : (a = n[9]),
            n[10] !== t || n[11] !== a
              ? ((s = { queries: t, combine: a }),
                (n[10] = t),
                (n[11] = a),
                (n[12] = s))
              : (s = n[12]),
            (0, h.f)(s)
          );
        })(s);
        u[9] !== x
          ? ((n = x.flatMap(t_)), (u[9] = x), (u[10] = n))
          : (n = u[10]);
        let b = n;
        u[11] !== x
          ? ((l = x.flatMap(tv)), (u[11] = x), (u[12] = l))
          : (l = u[12]);
        let w = l,
          _ = to(w, f && w.length > 0),
          v = 0 === b.length;
        u[13] !== b || u[14] !== v
          ? ((i = { mints: b, includeNsfw: !0, disabled: v }),
            (u[13] = b),
            (u[14] = v),
            (u[15] = i))
          : (i = u[15]);
        let {
          coins: k,
          loading: y,
          isLoadingError: j,
          fallbackPending: N,
        } = (0, eQ.f)(i);
        if (
          u[16] !== x ||
          u[17] !== k ||
          u[18] !== N ||
          u[19] !== j ||
          u[20] !== y ||
          u[21] !== _ ||
          u[22] !== g ||
          u[23] !== p
        ) {
          let e = new Map(k.map(tk));
          ((o = x.map((t) => {
            let { term: r, candidate: a, groupId: s } = t;
            if (null !== s) {
              let e = p.get(s);
              return e
                ? { kind: "squad", term: r, squad: e }
                : g.has(s)
                  ? { kind: "pending", term: r }
                  : { kind: "text", term: r };
            }
            if (!a) return { kind: "text", term: r };
            if ("near" === a.chain) {
              let e = _.byAddress.get(a.address);
              return e
                ? { kind: "coin", term: r, coin: e }
                : _.pending
                  ? { kind: "pending", term: r }
                  : { kind: "text", term: r };
            }
            let n = e.get((0, te.c)(a.address));
            return n
              ? { kind: "coin", term: r, coin: n }
              : y || N
                ? { kind: "pending", term: r }
                : !j && "solana" === a.chain && (0, tt.f)(a.address)
                  ? { kind: "user", term: r, address: a.address }
                  : { kind: "text", term: r };
          })),
            (u[16] = x),
            (u[17] = k),
            (u[18] = N),
            (u[19] = j),
            (u[20] = y),
            (u[21] = _),
            (u[22] = g),
            (u[23] = p),
            (u[24] = o));
        } else o = u[24];
        return o;
      })(I);
    (v[3] !== M ? ((i = M.flatMap(tN)), (v[3] = M), (v[4] = i)) : (i = v[4]),
      (0, eJ.f)(i),
      v[5] !== C
        ? ((o = C("web.search.recently_searched")), (v[5] = C), (v[6] = o))
        : (o = v[6]),
      v[7] !== R || v[8] !== E || v[9] !== C
        ? ((u = R
            ? (0, t.jsx)("button", {
                type: "button",
                className: V,
                onClick: () => A(tC),
                children: C(E ? "common.show_less" : "common.see_all"),
              })
            : null),
          (v[7] = R),
          (v[8] = E),
          (v[9] = C),
          (v[10] = u))
        : (u = v[10]));
    let L = 0 === k.length;
    return (
      v[11] !== C
        ? ((m = C("common.clear")), (v[11] = C), (v[12] = m))
        : (m = v[12]),
      v[13] !== j || v[14] !== L || v[15] !== m
        ? ((x = (0, t.jsx)("button", {
            type: "button",
            className: V,
            onClick: j,
            disabled: L,
            children: m,
          })),
          (v[13] = j),
          (v[14] = L),
          (v[15] = m),
          (v[16] = x))
        : (x = v[16]),
      v[17] !== u || v[18] !== x
        ? ((g = (0, t.jsxs)("span", {
            className: "flex items-center gap-3",
            children: [u, x],
          })),
          (v[17] = u),
          (v[18] = x),
          (v[19] = g))
        : (g = v[19]),
      v[20] !== o || v[21] !== g
        ? ((b = (0, t.jsx)(q._, {
            density: K,
            title: o,
            className: Q,
            aside: g,
          })),
          (v[20] = o),
          (v[21] = g),
          (v[22] = b))
        : (b = v[22]),
      v[23] !== N || v[24] !== M || v[25] !== C || v[26] !== k.length
        ? ((w =
            0 === k.length
              ? (0, t.jsx)(e_.L, {
                  density: K,
                  children: C("search.no_recent_searches"),
                })
              : (0, t.jsx)("div", {
                  className: "flex flex-col",
                  children: M.map((e, r) =>
                    "coin" === e.kind
                      ? (0, t.jsx)(
                          Z,
                          {
                            coin: e.coin,
                            index: r,
                            sourceScreen: n.Ae.SEARCH,
                            sourceElement: n.k9.RECENT_LIST,
                            searchTerm: e.term,
                            onClick: N,
                          },
                          e.term,
                        )
                      : "user" === e.kind
                        ? (0, t.jsx)(
                            td,
                            { address: e.address, onClick: N },
                            e.term,
                          )
                        : "squad" === e.kind
                          ? (0, t.jsx)(
                              en,
                              { squad: e.squad, onClick: N },
                              e.term,
                            )
                          : "pending" === e.kind
                            ? (0, t.jsxs)(
                                "div",
                                {
                                  "aria-hidden": !0,
                                  "data-testid": "recent-search-pending",
                                  className: (0, H.c)(
                                    F,
                                    "hover:bg-transparent",
                                  ),
                                  children: [
                                    (0, t.jsx)(T.l, {
                                      variant: "circle",
                                      size: $,
                                    }),
                                    (0, t.jsx)(T.l, { height: 14, width: 144 }),
                                  ],
                                },
                                e.term,
                              )
                            : (0, t.jsxs)(
                                f.default,
                                {
                                  href: `/explore?q=${encodeURIComponent(e.term)}`,
                                  onClick: N,
                                  className: (0, H.c)(F, "focus-inset"),
                                  children: [
                                    (0, t.jsx)("span", {
                                      className:
                                        "flex size-7 shrink-0 items-center justify-center text-text-quaternary",
                                      children: (0, t.jsx)(s.L3, {
                                        "aria-hidden": !0,
                                        className: "size-4",
                                      }),
                                    }),
                                    (0, t.jsx)("span", {
                                      className:
                                        "min-w-0 truncate text-sm leading-5 text-text-primary",
                                      children: e.term,
                                    }),
                                  ],
                                },
                                e.term,
                              ),
                  ),
                })),
          (v[23] = N),
          (v[24] = M),
          (v[25] = C),
          (v[26] = k.length),
          (v[27] = w))
        : (w = v[27]),
      v[28] !== w || v[29] !== b
        ? ((_ = (0, t.jsxs)("section", {
            className: "flex flex-col",
            "data-testid": "search-recently-searched",
            children: [b, w],
          })),
          (v[28] = w),
          (v[29] = b),
          (v[30] = _))
        : (_ = v[30]),
      _
    );
  };
  let td = (e) => {
    let a,
      s,
      n,
      l,
      i,
      c,
      d,
      h = (0, r.c)(26),
      { address: x, onClick: g } = e,
      { t: b } = (0, p.f)();
    h[0] !== x ? ((a = { address: x }), (h[0] = x), (h[1] = a)) : (a = h[1]);
    let { data: w } = (0, m.T)(a),
      _ = (0, u.s)(x);
    h[2] !== x || h[3] !== w?.username
      ? ((s = w?.username || x.slice(0, 6)),
        (h[2] = x),
        (h[3] = w?.username),
        (h[4] = s))
      : (s = h[4]);
    let v = s;
    (h[5] !== x ? ((n = (0, o.$)(x)), (h[5] = x), (h[6] = n)) : (n = h[6]),
      h[7] !== v || h[8] !== g || h[9] !== n
        ? ((l = (0, t.jsx)(f.default, {
            href: n,
            onClick: g,
            "aria-label": v,
            className: W,
          })),
          (h[7] = v),
          (h[8] = g),
          (h[9] = n),
          (h[10] = l))
        : (l = h[10]));
    let k = w?.username,
      y = w?.profile_image,
      j = w?.resolved_avatar_decoration,
      N = w?.x_username;
    return (
      h[11] !== b || h[12] !== w
        ? ((i = w
            ? b("common.followers_count", {
                count: w.followers ?? 0,
                compact_count: (0, P.O)(w.followers ?? 0),
              })
            : void 0),
          (h[11] = b),
          (h[12] = w),
          (h[13] = i))
        : (i = h[13]),
      h[14] !== x ||
      h[15] !== _ ||
      h[16] !== v ||
      h[17] !== k ||
      h[18] !== y ||
      h[19] !== j ||
      h[20] !== N ||
      h[21] !== i
        ? ((c = (0, t.jsx)(A.S, {
            address: x,
            username: k,
            profileImage: y,
            avatarDecoration: j,
            nameOverride: v,
            size: $,
            density: K,
            link: !1,
            hoverCard: !1,
            verified: _,
            xUsername: N,
            description: i,
            className: "min-w-0 flex-1",
          })),
          (h[14] = x),
          (h[15] = _),
          (h[16] = v),
          (h[17] = k),
          (h[18] = y),
          (h[19] = j),
          (h[20] = N),
          (h[21] = i),
          (h[22] = c))
        : (c = h[22]),
      h[23] !== c || h[24] !== l
        ? ((d = (0, t.jsxs)("div", {
            "data-search-row": !0,
            className: F,
            children: [l, c],
          })),
          (h[23] = c),
          (h[24] = l),
          (h[25] = d))
        : (d = h[25]),
      d
    );
  };
  function tw(e) {
    let { groupId: t } = e;
    return t ? [t] : [];
  }
  function t_(e) {
    let { candidate: t } = e;
    return t && "near" !== t.chain ? [t.address] : [];
  }
  function tv(e) {
    let { candidate: t } = e;
    return t?.chain === "near" ? [t.address] : [];
  }
  function tk(e) {
    return [(0, te.c)(e.mint), e];
  }
  function tN(e) {
    return "coin" === e.kind ? [e.coin] : [];
  }
  function tC(e) {
    return !e;
  }
  let K = "comfortable";
  let Q = "border-b-0";
  let W = "absolute inset-0 z-[1] focus-inset";
  return { RecentTerms: tu, AddressRow: td };
}
