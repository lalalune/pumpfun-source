// Complete captured SearchDialog owner and lazy child. Required capabilities never acquire data by default.
import {
  createSolanaSearchNavigator,
  createSearchSubmit,
  normalizeSolanaInput,
  profileRoute,
  SEARCH_TYPE,
  SCREEN,
  ELEMENT,
} from "../search-navigation/navigation.mjs";
import { createSearchShortcutHandler } from "../../packages/frontend/src/components/shell/search/search-shortcuts.mjs";
export function createSearchDialogController(ports) {
  for (const name of [
    "useTranslation",
    "useSearchOpen",
    "useSetSearchOpen",
    "useNsfw",
    "useLocalTerms",
    "useDebouncedValue",
    "useRecentCoins",
    "recentCoinViewedAt",
    "useChainFlags",
    "nearEnabled",
    "hexEnabled",
    "useCoinHydration",
    "canonicalCoinAddress",
    "isEvmAddress",
    "useFlag",
    "useRecentCards",
    "useRouter",
    "useCoinClick",
    "useLastClick",
    "validSolanaAddress",
    "probeKnownMint",
    "probeSolanaMint",
    "walletProfile",
    "getContractClient",
    "trackMintPaste",
    "trackWalletPaste",
    "trackSearch",
    "trackOpen",
    "trackClear",
    "trackTab",
    "readCoin",
    "useQuery",
    "useCoinSearch",
    "isPerp",
    "perpDisplay",
    "useCoinUpdates",
    "useUserSearch",
    "useGroupsEnabled",
    "useGroupClient",
    "useQueryClient",
    "projectGroup",
    "useInfiniteQuery",
    "useQueries",
    "isNearIdentifier",
    "classNames",
    "memoCache",
    "readTrendingCoins",
    "readPnlLeaders",
    "resolveIdentifier",
    "searchGroups",
    "groupSearchKey",
    "groupProfileKey",
    "normalizeHexIdentifier",
    "isNearCoin",
    "isHexCoin",
  ])
    if (typeof ports?.[name] !== "function")
      throw new TypeError("Explicit SearchDialog capability required: " + name);
  for (const name of [
    "Dialog",
    "Body",
    "Footer",
    "Input",
    "Heading",
    "Empty",
    "Tabs",
    "Link",
    "ArrowIcon",
    "Recommendations",
    "RecentTerms",
    "RecentCard",
    "CoinRow",
    "Skeleton",
    "MixedResults",
    "GroupRow",
    "UserRow",
  ])
    if (!ports.renderers?.[name])
      throw new TypeError("Explicit SearchDialog renderer required: " + name);
  if (
    !ports.React ||
    !ports.jsxRuntime ||
    !ports.browserWindow ||
    !ports.browserDocument ||
    !ports.queryKeys ||
    !ports.styles ||
    !ports.AbortController
  )
    throw new TypeError(
      "Explicit framework, DOM, query-key and style capabilities required",
    );
  if (!Object.hasOwn(ports, "keepPreviousData"))
    throw new TypeError("Explicit placeholder-data capability required");
  const p = { f: ports.useTranslation };
  const e8 = { F: ports.useSearchOpen, Z: ports.useSetSearchOpen };
  const e9 = { M: ports.useNsfw };
  const eM = { j: ports.useLocalTerms, r: ports.useDebouncedValue };
  const eP = { U: ports.useRecentCoins, A: ports.recentCoinViewedAt };
  const eZ = {
    l: ports.useChainFlags,
    M: ports.nearEnabled,
    k: ports.hexEnabled,
  };
  const eQ = { f: ports.useCoinHydration };
  const te = { c: ports.canonicalCoinAddress, h: ports.isEvmAddress };
  const i = { k: ports.useFlag };
  const eL = { f: ports.useRecentCards };
  const x = { useRouter: ports.useRouter };
  const M = { f: ports.useCoinClick };
  const B = { y: ports.useLastClick };
  const tr = { f: ports.validSolanaAddress };
  const eA = { Q: ports.probeKnownMint };
  const e1 = { isSolanaMintOnChain: ports.probeSolanaMint };
  const tt = { f: ports.walletProfile };
  const eI = { j: ports.getContractClient };
  const z = {
    pL: ports.trackMintPaste,
    Cv: ports.trackWalletPaste,
    iu: ports.trackSearch,
    P8: ports.trackOpen,
    bG: ports.trackClear,
    mM: ports.trackTab,
  };
  const eS = { k: ports.readCoin };
  const eE = { useQuery: ports.useQuery };
  const eV = { f: ports.useCoinSearch };
  const D = { x: ports.isPerp };
  const U = { K: ports.perpDisplay };
  const eJ = { f: ports.useCoinUpdates };
  const eX = { N: ports.useUserSearch };
  const eH = { f: ports.useGroupsEnabled };
  const eO = { useClientServerContract: ports.useGroupClient };
  const ez = { useQueryClient: ports.useQueryClient };
  const eo = { h: ports.projectGroup };
  const eD = { useInfiniteQuery: ports.useInfiniteQuery };
  const h = { f: ports.useQueries };
  const e0 = { D: ports.isNearIdentifier };
  const H = { c: ports.classNames };
  const ew = {
    N: ports.renderers.Dialog,
    K: ports.renderers.Body,
    c: ports.renderers.Footer,
  };
  const ek = { o: ports.renderers.Input };
  const q = { _: ports.renderers.Heading };
  const e_ = { L: ports.renderers.Empty };
  const ej = { p: ports.renderers.Tabs };
  const f = { default: ports.renderers.Link };
  const s = { kK: ports.renderers.ArrowIcon };
  const a = ports.React,
    t = ports.jsxRuntime,
    r = { c: ports.memoCache },
    window = ports.browserWindow,
    document = ports.browserDocument,
    AbortController = ports.AbortController;
  const l = {
      D: {
        WEB_PACKS: "webPacks",
        WEB_SEARCH_MIXED_RESULTS: "webSearchMixedResults",
        WEB_PERPS: "webPerps",
      },
    },
    n = { B8: SEARCH_TYPE, Ae: SCREEN, k9: { ...ELEMENT, RECENT_LIST: 30 } },
    d = { R: normalizeSolanaInput },
    o = { $: profileRoute };
  const eY = {
    d: "near:mainnet",
    W: "starknet:SN_MAIN",
    a: ports.isNearCoin,
    X: ports.isHexCoin,
    Y: ports.normalizeHexIdentifier,
  };
  const eC = { Q: ports.queryKeys },
    eK = {
      f: { search: ports.groupSearchKey, profile: ports.groupProfileKey },
    },
    eU = { y: ports.keepPreviousData },
    eB = { B: ports.searchGroups, V: 20, J: 500 };
  const e4 = ports.resolveIdentifier,
    eR = ports.readTrendingCoins,
    eT = ports.readPnlLeaders,
    tn = ports.styles.key,
    tl = ports.styles.viewAll,
    V = ports.styles.clear;
  const tp = ports.renderers.Recommendations;
  const tu = ports.renderers.RecentTerms;
  const ec = ports.renderers.RecentCard;
  const Z = ports.renderers.CoinRow;
  const et = ports.renderers.Skeleton;
  const eu = ports.renderers.MixedResults;
  const en = ports.renderers.GroupRow;
  const ee = ports.renderers.UserRow;
  let e$ = [];
  function eF(e, t) {
    return e + t.length;
  }
  function eW(e) {
    return e.pages.flat();
  }
  let e2 = 4;
  let e3 = ({ rows: e, loading: t, skipped: r = !1, limit: a = e2 }) => {
    if (r) return { rows: [], hasMore: !1, visible: !1, loading: !1 };
    let s = e.slice(0, a);
    return {
      rows: s,
      hasMore: e.length > a,
      visible: s.length > 0 || t,
      loading: 0 === s.length && t,
    };
  };
  let e5 = ["coins", "users", "squads"];
  let e6 = /^0x[0-9a-fA-F]{41,64}$/;
  let e7 = (e) => {
    let t = e.trim();
    return e6.test(t) ? (0, eY.Y)(t) : null;
  };
  let ti = (e) => {
    let t = e.trim();
    return (0, e0.D)(t) ? t : null;
  };
  let tc = (e) => {
    let t = new Map();
    for (let r of e) {
      let e = r.data;
      e?.mint && t.set(e.mint, { ...e, chain_id: eY.d });
    }
    return { byAddress: t, pending: e.some((e) => e.isLoading) };
  };
  let to = (e, t) => {
    let a,
      s,
      n,
      l = (0, r.c)(7);
    return (
      l[0] !== e || l[1] !== t
        ? ((a = t ? e : []), (l[0] = e), (l[1] = t), (l[2] = a))
        : (a = l[2]),
      l[3] !== a ? ((s = a.map(tb)), (l[3] = a), (l[4] = s)) : (s = l[4]),
      l[5] !== s
        ? ((n = { queries: s, combine: tc }), (l[5] = s), (l[6] = n))
        : (n = l[6]),
      (0, h.f)(n)
    );
  };
  function tb(e) {
    return {
      queryKey: eC.Q.COIN({
        coinAddress: e,
        includeDataLivestream: !1,
        chainId: eY.d,
      }),
      queryFn: () =>
        (0, eS.k)({ coinAddress: e, includeDataLivestream: !1, chainId: eY.d }),
      retry: !1,
      refetchOnWindowFocus: !1,
    };
  }
  function ty(e) {
    return (0, eY.a)(e) ? [e.mint] : [];
  }
  function tj(e) {
    return [(0, te.c)(e.mint), e];
  }
  let K = "comfortable";
  let Q = "border-b-0";
  let G = "flex flex-col gap-2";
  let J = { coins: "art", users: "circle", squads: "art" };
  function tg() {
    var e;
    let c,
      u,
      m,
      { t: h } = (0, p.f)(),
      g = (0, e8.F)(),
      b = (0, e8.Z)(),
      [w, _] = (0, a.useState)(""),
      [v, k] = (0, a.useState)("all"),
      y = (0, e9.M)(),
      j = (0, a.useRef)(null),
      [N, C, S] = (() => {
        let e,
          t,
          a,
          s,
          n = (0, r.c)(10);
        n[0] === Symbol.for("react.memo_cache_sentinel")
          ? ((e = []), (n[0] = e))
          : (e = n[0]);
        let [l, i] = (0, eM.j)("recently-searched-terms", e);
        n[1] !== l || n[2] !== i
          ? ((t = (e) => {
              let t = l.filter((t) => t !== e).slice(0, 19);
              i([e, ...t]);
            }),
            (n[1] = l),
            (n[2] = i),
            (n[3] = t))
          : (t = n[3]);
        let c = t;
        n[4] !== i
          ? ((a = () => {
              i([]);
            }),
            (n[4] = i),
            (n[5] = a))
          : (a = n[5]);
        let o = a;
        return (
          n[6] !== c || n[7] !== o || n[8] !== l
            ? ((s = [l, c, o]), (n[6] = c), (n[7] = o), (n[8] = l), (n[9] = s))
            : (s = n[9]),
          s
        );
      })(),
      [A, , E, I] = (0, eP.U)(),
      T = ((e, t) => {
        let a,
          s,
          n,
          l,
          i,
          c = (0, r.c)(18),
          o = (0, eZ.l)();
        c[0] !== o ? ((a = (0, eZ.M)(o)), (c[0] = o), (c[1] = a)) : (a = c[1]);
        let d = a;
        if (c[2] !== d || c[3] !== e) {
          let t;
          (c[5] !== d
            ? ((t = (e) => (d && (0, eY.a)(e) ? [] : [e.mint])),
              (c[5] = d),
              (c[6] = t))
            : (t = c[6]),
            (s = e.flatMap(t)),
            (c[2] = d),
            (c[3] = e),
            (c[4] = s));
        } else s = c[4];
        let u = s;
        c[7] !== d || c[8] !== e
          ? ((n = d ? e.flatMap(ty) : []), (c[7] = d), (c[8] = e), (c[9] = n))
          : (n = c[9]);
        let m = n,
          h = to(m, t && m.length > 0),
          f = !t || 0 === u.length;
        c[10] !== u || c[11] !== f
          ? ((l = { mints: u, includeNsfw: !0, disabled: f }),
            (c[10] = u),
            (c[11] = f),
            (c[12] = l))
          : (l = c[12]);
        let { coins: x } = (0, eQ.f)(l);
        e: {
          let t;
          if (0 === x.length && 0 === h.byAddress.size) {
            i = e;
            break e;
          }
          if (c[13] !== x || c[14] !== h || c[15] !== d || c[16] !== e) {
            let r = new Map(x.map(tj));
            ((t = e.map((e) =>
              d && (0, eY.a)(e)
                ? (h.byAddress.get(e.mint) ?? e)
                : (r.get((0, te.c)(e.mint)) ?? e),
            )),
              (c[13] = x),
              (c[14] = h),
              (c[15] = d),
              (c[16] = e),
              (c[17] = t));
          } else t = c[17];
          i = t;
        }
        return i;
      })(A, g),
      R = (0, i.k)(l.D.WEB_PACKS, !1),
      [L, , P] = (0, eL.f)(),
      O = (0, a.useMemo)(
        () =>
          (({ coins: e, viewedAtByMint: t = {}, cards: r }) =>
            [
              ...e.map((e, r) => ({
                item: { kind: "coin", coin: e },
                viewedAt: (0, eP.A)({ times: t, mint: e.mint }) ?? -r,
              })),
              ...r.map((e) => ({
                item: { kind: "card", card: e },
                viewedAt: e.viewedAt,
              })),
            ]
              .sort((e, t) => t.viewedAt - e.viewedAt)
              .map((e) => e.item))({
            coins: T,
            viewedAtByMint: I,
            cards: R ? L : [],
          }),
        [T, I, R, L],
      ),
      $ = A.length > 0 || (R && L.length > 0),
      { push: F } = (0, x.useRouter)(),
      { handleCoinClick: W } = (0, M.f)(),
      { setLastClickImpression: X } = (0, B.y)(),
      Y = (0, a.useRef)(null),
      er = (0, a.useRef)(null),
      ea = (0, a.useCallback)(() => {
        (Y.current?.abort(),
          (Y.current = null),
          (er.current = null),
          _(""),
          k("all"),
          b(!1));
      }, [b]),
      es = (0, a.useCallback)(
        (e) => {
          e ? b(!0) : ea();
        },
        [ea, b],
      ),
      el = (0, a.useCallback)(() => {
        g ? ea() : b(!0);
      }, [ea, g, b]),
      ei = (0, i.k)(l.D.WEB_SEARCH_MIXED_RESULTS),
      ed = (0, eZ.l)(),
      em = (0, eZ.k)(ed),
      eh = (0, eZ.M)(ed),
      ef = (0, a.useCallback)(
        createSolanaSearchNavigator({
          controllerRef: Y,
          pasteRef: er,
          validAddress: tr.f,
          walletProfile: tt.f,
          resolveIdentifier: e4,
          getContractClient: eI.j,
          probeKnownMint: eA.Q,
          probeSolanaMint: e1.isSolanaMintOnChain,
          closeDialog: ea,
          rememberTerm: C,
          trackMintPaste: z.pL,
          trackWalletPaste: z.Cv,
          trackSearch: z.iu,
          setLastClick: X,
          handleCoinClick: W,
          push: F,
          AbortController,
        }),
        [C, ea, W, F, X],
      ),
      ex = (0, a.useCallback)(
        async (e) => {
          (Y.current?.abort(), (Y.current = null));
          let t = e.trim();
          if (!(0, te.h)(t)) return !1;
          let r = new AbortController();
          Y.current = r;
          let a = () => {
              Y.current === r && (Y.current = null);
            },
            s = null,
            l = await e4(t, r.signal);
          if (Y.current !== r || r.signal.aborted) return (a(), "cancelled");
          let i = "fallback" !== l.kind;
          if (("coin" === l.kind && (s = l.mint), !i))
            try {
              let e = !1,
                n = await (0, eI.j)()("GET /coins-v3/{address}", {
                  params: { address: t },
                  query: {},
                  signal: r.signal,
                  throwHttpErrors: !1,
                  parseJson: (e) => {
                    try {
                      return JSON.parse(e);
                    } catch {
                      return null;
                    }
                  },
                  hooks: {
                    afterResponse: [
                      (t, r, a) => {
                        e = a.ok;
                      },
                    ],
                  },
                });
              if (r.signal.aborted) return (a(), "cancelled");
              if (e) {
                if (Y.current !== r || r.signal.aborted)
                  return (a(), "cancelled");
                s = n?.mint ?? null;
              }
              if (!s) {
                let e = await (0, eA.Q)(t, r.signal);
                if (Y.current !== r || r.signal.aborted)
                  return (a(), "cancelled");
                e && (s = t);
              }
            } catch (e) {
              if ((a(), e instanceof DOMException && "AbortError" === e.name))
                return "cancelled";
              return !1;
            }
          if ((a(), !s)) return !1;
          let c = er.current === t;
          ((er.current = null),
            ea(),
            C(t),
            c && (0, z.pL)({ mint: s }),
            (0, z.iu)({ searchTerm: t, searchType: n.B8.COINS }));
          let o = {
            itemPosition: 0,
            marketCap: 0,
            sourceScreen: n.Ae.SEARCH,
            sourceElement: n.k9.SEARCH_INPUT,
          };
          return (X(s, o, t), W(s, o, t), F(`/coin/${s}`), !0);
        },
        [C, ea, W, F, X],
      ),
      ep = (0, a.useCallback)(
        async (e) => {
          (Y.current?.abort(), (Y.current = null));
          let t = em ? e7(e) : null;
          if (!t) return !1;
          let r = new AbortController();
          Y.current = r;
          let a = () => Y.current === r && !r.signal.aborted,
            s = (e) => (Y.current === r && (Y.current = null), e),
            l = null,
            i = t,
            c = await e4(t, r.signal);
          if (!a()) return s("cancelled");
          if ("coin" === c.kind) ((i = c.mint), (l = "coin"));
          else if ("user" === c.kind || "external_wallet" === c.kind)
            l = "profile";
          else
            try {
              let e = await (0, eS.k)({
                coinAddress: t,
                chainId: eY.W,
                fetchOptions: { signal: r.signal },
              });
              if (!a()) return s("cancelled");
              e.mint && (0, eY.X)(e) && ((i = e.mint), (l = "coin"));
            } catch (e) {
              if (
                !a() ||
                (e instanceof DOMException && "AbortError" === e.name)
              )
                return s("cancelled");
              return s(!1);
            }
          if ((s(!1), null === l)) return !1;
          let d = er.current === t;
          if (((er.current = null), ea(), C(t), "coin" === l)) {
            (d && (0, z.pL)({ mint: i }),
              (0, z.iu)({ searchTerm: t, searchType: n.B8.COINS }));
            let e = {
              itemPosition: 0,
              marketCap: 0,
              sourceScreen: n.Ae.SEARCH,
              sourceElement: n.k9.SEARCH_INPUT,
            };
            (X(i, e, t), W(i, e, t), F(`/coin/${i}`));
          } else
            (d && (0, z.Cv)({ wallet: t }),
              (0, z.iu)({ searchTerm: t, searchType: n.B8.USERS }),
              F((0, o.$)(t)));
          return !0;
        },
        [C, ea, W, em, F, X],
      ),
      eg = (0, a.useCallback)(
        async (e) => {
          (Y.current?.abort(), (Y.current = null));
          let t = eh ? ti(e) : null;
          if (!t) return !1;
          let r = new AbortController();
          Y.current = r;
          let a = () => Y.current === r && !r.signal.aborted,
            s = (e) => (Y.current === r && (Y.current = null), e),
            l = null,
            i = t,
            c = await e4(t, r.signal);
          if (!a()) return s("cancelled");
          if ("coin" === c.kind && "near" === c.chain)
            ((i = c.mint), (l = "coin"));
          else if ("user" === c.kind || "external_wallet" === c.kind)
            l = "profile";
          else
            try {
              let e = await (0, eS.k)({
                coinAddress: t,
                chainId: eY.d,
                fetchOptions: { signal: r.signal },
              });
              if (!a()) return s("cancelled");
              e.mint && ((i = e.mint), (l = "coin"));
            } catch (e) {
              if (
                !a() ||
                (e instanceof DOMException && "AbortError" === e.name)
              )
                return s("cancelled");
              return s(!1);
            }
          if ((s(!1), null === l)) return !1;
          let d = er.current === t;
          if (((er.current = null), ea(), C(t), "coin" === l)) {
            (d && (0, z.pL)({ mint: i }),
              (0, z.iu)({ searchTerm: t, searchType: n.B8.COINS }));
            let e = {
              itemPosition: 0,
              marketCap: 0,
              sourceScreen: n.Ae.SEARCH,
              sourceElement: n.k9.SEARCH_INPUT,
            };
            (X(i, e, t), W(i, e, t), F(`/coin/${i}`));
          } else
            (d && (0, z.Cv)({ wallet: t }),
              (0, z.iu)({ searchTerm: t, searchType: n.B8.USERS }),
              F((0, o.$)(t)));
          return !0;
        },
        [C, ea, W, eh, F, X],
      ),
      { data: eb = [], isLoading: ev } = (function (e) {
        let t,
          a,
          s = (0, r.c)(4);
        s[0] !== e
          ? ((t = void 0 === e ? {} : e), (s[0] = e), (s[1] = t))
          : (t = s[1]);
        let { queryOptions: n } = t;
        return (
          s[2] !== n
            ? ((a = {
                queryFn: eR,
                queryKey: eC.Q.TRENDING_COINS,
                staleTime: 3e5,
                gcTime: 6e5,
                refetchOnWindowFocus: !1,
                refetchOnMount: !1,
                ...n,
              }),
              (s[2] = n),
              (s[3] = a))
            : (a = s[3]),
          (0, eE.useQuery)(a)
        );
      })({ queryOptions: { enabled: g } }),
      { data: ey, isLoading: eN } = (function (e) {
        let t,
          a,
          s,
          n = (0, r.c)(9),
          { period: l, sort: i, limit: c, queryOptions: o } = e;
        return (
          n[0] !== c || n[1] !== l || n[2] !== i
            ? ((t = () => eT({ period: l, sort: i, limit: c })),
              (a = eC.Q.PNL_LEADERBOARD({ period: l, sort: i, limit: c })),
              (n[0] = c),
              (n[1] = l),
              (n[2] = i),
              (n[3] = t),
              (n[4] = a))
            : ((t = n[3]), (a = n[4])),
          n[5] !== o || n[6] !== t || n[7] !== a
            ? ((s = {
                queryFn: t,
                queryKey: a,
                staleTime: 3e5,
                gcTime: 6e5,
                refetchOnWindowFocus: !1,
                refetchOnMount: !1,
                ...o,
              }),
              (n[5] = o),
              (n[6] = t),
              (n[7] = a),
              (n[8] = s))
            : (s = n[8]),
          (0, eE.useQuery)(s)
        );
      })({
        period: "daily",
        sort: "combined",
        limit: 20,
        queryOptions: { enabled: g },
      }),
      eq = ey?.entries ?? [],
      e0 = (0, i.k)(l.D.WEB_PERPS, !1),
      { coins: e6, loading: ta } = (0, eV.f)({
        offset: 0,
        limit: 50,
        includeNsfw: y,
        isSearchMode: !0,
        searchTerm: w,
        includePerps: e0,
        onSearchSettled: (e) =>
          (0, z.iu)({
            searchTerm: e.searchTerm,
            searchType: n.B8.COINS,
            timeToLoadMs: e.timeToLoadMs,
            resultCount: e.resultCount,
          }),
      }),
      ts = (0, a.useMemo)(
        () => e6.filter((e) => !(0, D.x)(e) || null !== (0, U.K)(e)),
        [e6],
      ),
      tc = ts.filter((e) => (0, D.x)(e) || !0 === e.search_priority),
      td = tc.some((e) => !(0, D.x)(e)) ? tc : ts,
      tm = (0, a.useMemo)(
        () => (w ? td.filter((e) => !(0, D.x)(e)) : [...T, ...eb]),
        [w, td, T, eb],
      );
    (0, eJ.f)(tm, g);
    let {
        users: th,
        loading: tf,
        isSearchTermTooShort: tx,
        isDebouncing: tg,
        minSearchTermLength: tb,
      } = (0, eX.N)({ searchTerm: w }),
      tw = (0, eH.f)(),
      {
        squads: t_,
        loading: tv,
        isSearchTermTooShort: tk,
        isDebouncing: tN,
        minSearchTermLength: tC,
      } = ((e) => {
        let t,
          a,
          s,
          n,
          l,
          i,
          c,
          o = (0, r.c)(31),
          { searchTerm: d, enabled: u, pageSize: m } = e,
          h = void 0 === m ? eB.V : m,
          f = (0, eO.useClientServerContract)(),
          x = (0, ez.useQueryClient)(),
          p = (0, eH.f)();
        o[0] !== d
          ? ((t = d?.trim() ?? ""), (o[0] = d), (o[1] = t))
          : (t = o[1]);
        let [g] = (0, eM.r)(t, 500),
          b = (void 0 === u || u) && p,
          w = b && g.length < 2;
        o[2] !== g || o[3] !== b || o[4] !== d
          ? ((a = b && (d?.trim() ?? "") !== g),
            (o[2] = g),
            (o[3] = b),
            (o[4] = d),
            (o[5] = a))
          : (a = o[5]);
        let _ = a;
        (o[6] !== g || o[7] !== h
          ? ((s = eK.f.search(g, h)), (o[6] = g), (o[7] = h), (o[8] = s))
          : (s = o[8]),
          o[9] !== f || o[10] !== g || o[11] !== h || o[12] !== x
            ? ((n = async (e) => {
                let { pageParam: t, signal: r } = e,
                  a = await (0, eB.B)({
                    api: f,
                    searchTerm: g,
                    offset: t,
                    limit: h,
                    signal: r,
                  });
                for (let e of a)
                  x.setQueryData(eK.f.profile(e.userId), (0, eo.h)(e));
                return a;
              }),
              (o[9] = f),
              (o[10] = g),
              (o[11] = h),
              (o[12] = x),
              (o[13] = n))
            : (n = o[13]),
          o[14] !== h
            ? ((l = (e, t) => {
                if (e.length < h) return;
                let r = t.reduce(eF, 0);
                return r > eB.J ? void 0 : r;
              }),
              (o[14] = h),
              (o[15] = l))
            : (l = o[15]));
        let v = b && !w,
          k = w ? void 0 : eU.y;
        o[16] !== s || o[17] !== n || o[18] !== l || o[19] !== v || o[20] !== k
          ? ((i = {
              queryKey: s,
              queryFn: n,
              initialPageParam: 0,
              getNextPageParam: l,
              select: eW,
              enabled: v,
              staleTime: 3e4,
              refetchOnWindowFocus: !1,
              placeholderData: k,
            }),
            (o[16] = s),
            (o[17] = n),
            (o[18] = l),
            (o[19] = v),
            (o[20] = k),
            (o[21] = i))
          : (i = o[21]);
        let y = (0, eD.useInfiniteQuery)(i),
          j = p ? (y.data ?? e$) : e$,
          N = p && y.isFetching;
        return (
          o[22] !== _ ||
          o[23] !== w ||
          o[24] !== y.error ||
          o[25] !== y.fetchNextPage ||
          o[26] !== y.hasNextPage ||
          o[27] !== y.isFetchingNextPage ||
          o[28] !== j ||
          o[29] !== N
            ? ((c = {
                squads: j,
                loading: N,
                error: y.error,
                isSearchTermTooShort: w,
                isDebouncing: _,
                minSearchTermLength: 2,
                fetchNextPage: y.fetchNextPage,
                hasNextPage: y.hasNextPage,
                isFetchingNextPage: y.isFetchingNextPage,
              }),
              (o[22] = _),
              (o[23] = w),
              (o[24] = y.error),
              (o[25] = y.fetchNextPage),
              (o[26] = y.hasNextPage),
              (o[27] = y.isFetchingNextPage),
              (o[28] = j),
              (o[29] = N),
              (o[30] = c))
            : (c = o[30]),
          c
        );
      })({ searchTerm: w, enabled: tw }),
      tS = ta || tf || tv,
      tA = { coins: td.length, users: th.length, squads: t_.length },
      tE = td.length > 0 || th.length > 0 || t_.length > 0,
      tI = w.trim().length,
      tT = {
        coins: e3({
          rows: (0, a.useMemo)(() => {
            let e = td.findIndex((e) => (0, D.x)(e));
            if (e < e2) return td;
            let t = td[e];
            if (void 0 === t) return td;
            let r = td.filter((e) => e !== t);
            return [...r.slice(0, e2 - 1), t, ...r.slice(e2 - 1)];
          }, [td]),
          loading: ta,
        }),
        users: e3({ rows: th, loading: tf || tg, skipped: tI < tb }),
        squads: e3({ rows: t_, loading: tv || tN, skipped: !tw || tI < tC }),
      },
      tq = tT.coins.visible || tT.users.visible || tT.squads.visible,
      tR = tI < tb || (tw && tI < tC),
      tM = "all" === v ? "coins" : v,
      tL = ei
        ? (({ selected: e, visible: t }) => ("all" === e || t[e] ? e : "all"))({
            selected: v,
            visible: {
              coins: tT.coins.visible,
              users: tT.users.visible,
              squads: tT.squads.visible,
            },
          })
        : (({ selected: e, counts: t }) =>
            t[e] > 0 ? e : (e5.find((e) => t[e] > 0) ?? e))({
            selected: tM,
            counts: tA,
          }),
      tP = "all" === tL ? "coins" : tL,
      tO = (({ view: e, coinsVisible: t }) =>
        "all" === e ? t : "coins" === e)({
        view: tL,
        coinsVisible: tT.coins.visible,
      }),
      tU = [
        ...(ei
          ? [{ key: "all", label: h("common.all"), count: null, isEmpty: !1 }]
          : []),
        ...e5
          .filter((e) => "squads" !== e || tw)
          .map((e) => ({
            key: e,
            label: ((e, t) => {
              switch (e) {
                case "coins":
                  return t("search.coins");
                case "users":
                  return t("search.users");
                case "squads":
                  return t("search.squads");
              }
            })(e, h),
            count: ei && !tT[e].visible ? 0 : tA[e],
            isEmpty: ei ? !tT[e].visible : 0 === tA[e],
          })),
      ],
      tD = ei ? tq : !tS && tE,
      tz = ei ? !tq : !tS && !tE;
    (0, a.useEffect)(() => {
      g && (0, z.P8)();
    }, [g]);
    let tH = (0, a.useCallback)((e) => {
        if (((j.current = e), !e)) return;
        let t = e.closest('[role="dialog"]');
        t?.contains(document.activeElement) || e.focus();
      }, []),
      tB = createSearchSubmit({
        searchTerm: w,
        navigateSolana: ef,
        navigateEvm: ex,
        navigateHex: ep,
        navigateNear: eg,
        closeDialog: ea,
        rememberTerm: C,
        push: F,
      });
    ((e = [
      { keys: ["Meta", "k"], callback: el },
      { keys: ["Control", "k"], callback: el },
      { keys: ["/"], callback: el },
    ]),
      (m = (0, r.c)(3))[0] !== e
        ? ((c = () => {
            let t = createSearchShortcutHandler(e);
            return (
              window.addEventListener("keydown", t),
              () => {
                window.removeEventListener("keydown", t);
              }
            );
          }),
          (u = [e]),
          (m[0] = e),
          (m[1] = c),
          (m[2] = u))
        : ((c = m[1]), (u = m[2])),
      (0, a.useEffect)(c, u));
    let tK = (e) => {
        (ei && !(0, D.x)(e) && C(e.mint), ea());
      },
      t$ = (e) => {
        (ei && e.address && (0, tr.f)(e.address) && C(e.address), ea());
      },
      tF = (e) => {
        (C(e.userId), ea());
      };
    return (0, t.jsxs)(ew.N, {
      open: g,
      onOpenChange: es,
      density: K,
      size: "lg",
      hideClose: !0,
      "aria-label": h("web.search.title"),
      className: "max-h-[85dvh]",
      "data-testid": "search-dialog",
      children: [
        (0, t.jsxs)("form", {
          onSubmit: tB,
          className: "shrink-0",
          children: [
            (0, t.jsx)(ek.o, {
              density: K,
              size: "hero",
              inputRef: tH,
              value: w,
              onValueChange: (e) => {
                (Y.current?.abort(),
                  (Y.current = null),
                  (er.current = null),
                  _(e));
              },
              onClear: () => (0, z.bG)({ searchTerm: w }),
              label: h("web.search.input_placeholder"),
              "aria-label": h("web.search.input_a11y"),
              name: "search-token",
              id: "search-token",
              autoComplete: "off",
              enterKeyHint: "search",
              onPaste: (e) => {
                let t = e.clipboardData.getData("text"),
                  r = (0, d.R)(t),
                  a = (0, te.h)(t.trim()) ? t.trim() : null,
                  s = em ? e7(t) : null,
                  n = eh ? ti(t) : null,
                  l = r && (0, tr.f)(r) ? r : (a ?? s ?? n);
                if (!l) return;
                (e.preventDefault(), (er.current = l));
                let i = j.current,
                  c = i?.value ?? w,
                  o = i?.selectionStart ?? c.length,
                  u = i?.selectionEnd ?? c.length;
                (_(c.slice(0, o) + l + c.slice(u)),
                  l === a ? ex(l) : l === s ? ep(l) : l === n ? eg(l) : ef(l));
              },
              className:
                "rounded-none border-0 border-b border-border-secondary bg-transparent",
            }),
            (0, t.jsx)("p", {
              className: "sr-only",
              children: h("web.search.dialog_description"),
            }),
          ],
        }),
        (0, t.jsxs)(ew.K, {
          className: (0, H.c)(
            G,
            "p-0 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden",
          ),
          children: [
            w
              ? null
              : (0, t.jsxs)(t.Fragment, {
                  children: [
                    (0, t.jsx)(tp, {
                      topTraders: eq,
                      topTradersLoading: eN,
                      trendingCoins: eb,
                      trendingLoading: ev,
                      onNavigate: ea,
                    }),
                    (0, t.jsx)(tu, {
                      terms: N,
                      canExpand: ei,
                      onClear: S,
                      onNavigate: ea,
                    }),
                    (0, t.jsxs)("section", {
                      className: "flex flex-col",
                      "data-testid": "search-recently-viewed",
                      children: [
                        (0, t.jsx)(q._, {
                          density: K,
                          title: h("profile.recently_viewed"),
                          className: Q,
                          aside: (0, t.jsx)("button", {
                            type: "button",
                            className: V,
                            onClick: () => {
                              (E(), P());
                            },
                            disabled: !$,
                            children: h("common.clear"),
                          }),
                        }),
                        $
                          ? (0, t.jsx)("div", {
                              className: "flex flex-col",
                              children: O.map((e, r) =>
                                "card" === e.kind
                                  ? (0, t.jsx)(
                                      ec,
                                      { card: e.card, onClick: ea },
                                      `card:${e.card.nftAddress}`,
                                    )
                                  : (0, t.jsx)(
                                      Z,
                                      {
                                        coin: e.coin,
                                        index: r,
                                        sourceScreen: n.Ae.SEARCH,
                                        sourceElement: n.k9.RECENT_LIST,
                                        searchTerm: w,
                                        onClick: ea,
                                      },
                                      (0, te.c)(e.coin.mint),
                                    ),
                              ),
                            })
                          : (0, t.jsx)(e_.L, {
                              density: K,
                              children: h("web.search.no_recently_viewed"),
                            }),
                      ],
                    }),
                  ],
                }),
            w && !ei && tS ? (0, t.jsx)(et, { rows: 5, variant: J[tP] }) : null,
            w && tD
              ? (0, t.jsxs)("div", {
                  className: "flex flex-col",
                  "data-testid": "search-results",
                  children: [
                    (0, t.jsx)(ej.p, {
                      density: K,
                      "aria-label": h("web.search.filter_results_a11y"),
                      value: tL,
                      onValueChange: (e) => {
                        ("all" !== e &&
                          (0, z.mM)({ tab: "users" === e ? "accounts" : e }),
                          k(e));
                      },
                      tabs: tU.map((e) => ({
                        value: e.key,
                        label: e.label,
                        count: e.count,
                        disabled: e.isEmpty,
                        onClick: () => {
                          var t;
                          let r;
                          return (
                            (t = e.key),
                            (r = ei ? v : tM),
                            void (
                              tL === t &&
                              r !== t &&
                              ("all" !== t &&
                                (0, z.mM)({
                                  tab: "users" === t ? "accounts" : t,
                                }),
                              k(t))
                            )
                          );
                        },
                      })),
                    }),
                    ei && "all" === tL
                      ? (0, t.jsx)(eu, {
                          searchTerm: w,
                          coins: tT.coins,
                          users: tT.users,
                          squads: tT.squads,
                          onSeeAll: (e) => {
                            ((0, z.mM)({ tab: "users" === e ? "accounts" : e }),
                              k(e));
                          },
                          onCoinClick: tK,
                          onUserClick: t$,
                          onSquadClick: tF,
                        })
                      : ei && tT[tP].loading
                        ? (0, t.jsx)(et, { rows: 5, variant: J[tP] })
                        : "coins" === tP
                          ? (0, t.jsx)("div", {
                              className: "flex flex-col",
                              children: td.map((e, r) =>
                                (0, t.jsx)(
                                  Z,
                                  {
                                    coin: e,
                                    index: r,
                                    searchTerm: w,
                                    onClick: () => tK(e),
                                  },
                                  e.mint,
                                ),
                              ),
                            })
                          : "squads" === tP
                            ? (0, t.jsx)("div", {
                                className: "flex flex-col",
                                children: t_.map((e) =>
                                  (0, t.jsx)(
                                    en,
                                    {
                                      squad: (0, eo.h)(e),
                                      onClick: () => tF(e),
                                    },
                                    e.userId,
                                  ),
                                ),
                              })
                            : (0, t.jsx)("div", {
                                className: "flex flex-col",
                                children: th.map((e) =>
                                  (0, t.jsx)(
                                    ee,
                                    { user: e, onClick: () => t$(e) },
                                    e.userId ?? e.address,
                                  ),
                                ),
                              }),
                    tO
                      ? (0, t.jsxs)(f.default, {
                          href: `/explore?q=${encodeURIComponent(w.trim())}`,
                          className: tl,
                          onClick: () => {
                            (C(w.trim()), ea());
                          },
                          "data-testid": "search-view-all-results",
                          children: [
                            h("web.search.view_all_results"),
                            (0, t.jsx)(s.kK, {
                              "aria-hidden": !0,
                              className: "size-3 shrink-0 text-text-quaternary",
                            }),
                          ],
                        })
                      : null,
                  ],
                })
              : null,
            !w || !tz || tR || tx || tk
              ? null
              : (0, t.jsx)(e_.L, {
                  density: K,
                  children: h("web.search.no_results_for", { query: w }),
                }),
          ],
        }),
        (0, t.jsxs)(ew.c, {
          className: "justify-between",
          children: [
            (0, t.jsxs)("div", {
              className:
                "flex items-center gap-4 text-xs leading-4 text-text-tertiary",
              children: [
                (0, t.jsxs)("span", {
                  className: "flex items-center gap-1.5",
                  children: [
                    (0, t.jsx)("kbd", { className: tn, children: "↵" }),
                    (0, t.jsx)("span", {
                      children: h("web.search.kbd_to_search"),
                    }),
                  ],
                }),
                (0, t.jsxs)("span", {
                  className: "flex items-center gap-1.5",
                  children: [
                    (0, t.jsx)("kbd", { className: tn, children: "esc" }),
                    (0, t.jsx)("span", {
                      children: h("web.search.kbd_to_close"),
                    }),
                  ],
                }),
              ],
            }),
            (0, t.jsx)("kbd", { className: tn, children: "⌘K" }),
          ],
        }),
      ],
    });
  }
  const SearchDialogLazy = function (e) {
    let s,
      n,
      l,
      i = (0, r.c)(4),
      { onMounted: c } = e;
    return (
      i[0] !== c
        ? ((s = () => {
            c();
          }),
          (n = [c]),
          (i[0] = c),
          (i[1] = s),
          (i[2] = n))
        : ((s = i[1]), (n = i[2])),
      (0, a.useEffect)(s, n),
      i[3] === Symbol.for("react.memo_cache_sentinel")
        ? ((l = (0, t.jsx)(tg, {})), (i[3] = l))
        : (l = i[3]),
      l
    );
  };
  return { SearchDialog: tg, SearchDialogLazy };
}
