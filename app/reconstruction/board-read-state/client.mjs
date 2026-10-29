import { buildBoardRequest } from "../market-boards/request.mjs";
import { createSearchExecutor } from "../search-session/session.mjs";
import {
  SEARCH_SORT,
  buildCoinSearchQuery,
} from "../search-planner/planner.mjs";
// No implicit fetch, destination, identity, session, response decoder or provider.
export function createBoardCoinHook({
  React,
  cache,
  baseUrl,
  fetchResponse,
  parseBoard,
  seedBoardCoins,
  nowMs,
  AbortController: Controller,
  useViewerSnapshot,
  useSessionSnapshot,
  usePrimarySessionIdSnapshot,
  useVariant,
  useExposure,
  useIpfsPrefix,
  requestIdentity,
  debounce,
  useLivePollInterval,
  timers,
  logger,
}) {
  const capabilities = {
    fetchResponse,
    parseBoard,
    seedBoardCoins,
    nowMs,
    Controller,
    useViewerSnapshot,
    useSessionSnapshot,
    usePrimarySessionIdSnapshot,
    useVariant,
    useExposure,
    useIpfsPrefix,
    requestIdentity,
    debounce,
    useLivePollInterval,
  };
  for (const [name, value] of Object.entries(capabilities))
    if (typeof value !== "function")
      throw new TypeError("Explicit board capability required: " + name);
  if (
    !(cache?.entries instanceof Map) ||
    typeof cache.store !== "function" ||
    typeof baseUrl !== "string"
  )
    throw new TypeError("Explicit shared cache and destination are required");
  if (
    !["useState", "useRef", "useCallback", "useEffect"].every(
      (name) => typeof React?.[name] === "function",
    )
  )
    throw new TypeError("Explicit React hooks are required");
  if (
    typeof timers?.setInterval !== "function" ||
    typeof timers?.clearInterval !== "function" ||
    typeof logger?.error !== "function"
  )
    throw new TypeError("Explicit timer/logger capabilities are required");
  const excludedOperation = () => {
    throw new TypeError("Non-board request is outside this adapter domain");
  };
  const r = {
      get contract() {
        return excludedOperation();
      },
    },
    n = { F: useViewerSnapshot },
    l = React,
    i = { t: debounce },
    u = { y: useVariant },
    a = { i: 60000 },
    s = { E: SEARCH_SORT },
    d = { ASC: "ASC", DESC: "DESC" },
    y = { q: useLivePollInterval },
    S = { W: "1h", x: excludedOperation },
    p = { l: useExposure, M: excludedOperation },
    w = { a: excludedOperation },
    k = { f: requestIdentity },
    b = { d: usePrimarySessionIdSnapshot },
    T = { m: excludedOperation, K: excludedOperation },
    v = { useIpfsPrefix },
    C = { useSession: useSessionSnapshot },
    A = { f: excludedOperation },
    R = { f: (options) => buildBoardRequest(options, { baseUrl }).url },
    I = { $: seedBoardCoins },
    Date = { now: nowMs },
    setInterval = timers.setInterval,
    clearInterval = timers.clearInterval,
    console = logger;
  const M = cache.entries,
    L = cache.store,
    N = [],
    j = (e) => e === s.E.FEATURED || e === s.E.TRENDING || e === s.E.STOCKS;
  const originalHook = function (e) {
    let t,
      {
        sort: o,
        offset: c,
        limit: f,
        includeNsfw: h,
        order: E,
        creator: D,
        isSearchMode: P = !1,
        searchTerm: _,
        searchRefetchTrigger: x,
        useUnrestrictedSearch: q = !1,
        includePerps: F = !1,
        chain: K = "all",
        callsWindow: U = S.W,
        forceLocalFiltering: $ = !1,
        initialCoins: H,
      } = e,
      Q = "social-terminal" === (0, u.y)(),
      [Y, B] = (0, l.useState)(() => (H && Q && (0, I.$)(H), H ?? [])),
      [G, V] = (0, l.useState)(() => (H && o === s.E.TRENDING ? H : N)),
      [W, J] = (0, l.useState)(!H),
      [Z, z] = (0, l.useState)(null),
      [X, ee] = (0, l.useState)(() => H?.length ?? 0),
      et = JSON.stringify([
        (t = {
          sort: o ?? "",
          order: E ?? "",
          offset: c,
          limit: f,
          includeNsfw: h,
          isSearchMode: P,
          searchTerm: _ ?? "",
          chain: K,
          creator: D,
          callsWindow: U,
        }).sort,
        t.order,
        t.offset,
        t.limit,
        t.includeNsfw,
        t.isSearchMode,
        t.searchTerm.trim(),
        t.chain,
        t.filterParams ?? null,
        t.creator ?? null,
        t.callsWindow ?? null,
      ]),
      [er, en] = (0, l.useState)(() => (H ? et : null)),
      [el, ei] = (0, l.useState)(null),
      eu = null !== el && el === et,
      ea = (0, l.useRef)(et);
    ea.current = et;
    let es = (0, l.useRef)(er);
    es.current = er;
    let eo = (0, l.useRef)(!!H?.length),
      ec = (0, l.useRef)(!1),
      { ipfsPrefix: ef } = (0, v.useIpfsPrefix)(),
      { address: ed, userId: eh, authReady: eE } = (0, n.F)(),
      { sessionData: ey } = (0, C.useSession)(),
      em = (0, b.d)() ?? ey?.pump_session_id,
      eg = (0, p.l)(),
      eS = (0, l.useRef)(e.onSearchSettled);
    eS.current = e.onSearchSettled;
    let ep = (0, l.useRef)(0),
      ew = (0, l.useRef)(null),
      ek = (0, l.useRef)(0),
      eb = (0, l.useRef)(!1),
      eT = (0, l.useRef)(null),
      ev = (0, l.useCallback)(
        (e) =>
          e
            ? e === s.E.FEATURED ||
              e === s.E.CHARITY ||
              e === s.E.CUSTOM_PAIRS ||
              e === s.E.LIVE ||
              e === s.E.CALLS ||
              e === s.E.TRENDING ||
              e === s.E.STOCKS ||
              e === s.E.MAJORS
              ? s.E.MARKET_CAP
              : e === s.E.OLDEST
                ? s.E.NEWEST
                : e
            : e,
        [],
      ),
      eC = (0, l.useCallback)(
        (e, t) =>
          e === s.E.NEWEST && t ? t : e === s.E.OLDEST ? d.ASC : d.DESC,
        [],
      ),
      eA = (0, l.useCallback)(
        (args) =>
          buildCoinSearchQuery(
            args,
            { limit: f, includeNsfw: h, creator: D, sessionId: em },
            requestIdentity,
          ),
        [f, h, D, em, 100, ev, eC],
      ),
      eR = (0, l.useCallback)(
        createSearchExecutor(
          { offset: c, limit: f, ipfsPrefix: ef, socialTerminal: Q },
          {
            entries: M,
            store: L,
            requestKeyRef: ea,
            loadedKeyRef: es,
            sequenceRef: ep,
            abortRef: ew,
            setCoins: B,
            setPageSize: ee,
            setHasNextPage: z,
            setLoadedKey: en,
            setErrorKey: ei,
            setLoading: J,
            setServedCoins: V,
            emptyCoins: N,
            getContractClient: excludedOperation,
            fetchResponse,
            parseBoard,
            now: nowMs,
            AbortController: Controller,
          },
        ),
        [ef, c, f, Q],
      ),
      eI = (0, l.useCallback)(
        async ({ searchTerm: e, useLocalFiltering: t = !1 }) => {
          if (!e?.trim()) return;
          let r = o === s.E.CHARITY,
            n = {
              ...eA({
                searchTerm: e,
                offset: t ? 0 : c,
                sort: r ? s.E.MARKET_CAP : o,
                order: E,
                useLocalFilterLimit: t,
              }),
            };
          r && (n.isCharity = !0);
          let l = q
              ? {
                  kind: "client",
                  route: "GET /coins/search-unrestricted",
                  query: n,
                }
              : {
                  kind: "client",
                  route: "GET /coins/search-v2",
                  query: F ? { ...n, includePerps: !0 } : n,
                },
            i = t || 0 === c,
            u = e.trim();
          await eR(
            l,
            !1,
            t,
            !1,
            (e) =>
              e.filter((e) => (0, A.f)(e) && ((0, p.M)(eg) || !(0, w.a)(e))),
            (e, t) => {
              i &&
                eS.current?.({
                  searchTerm: u,
                  resultCount: e,
                  timeToLoadMs: t,
                });
            },
          );
        },
        [eA, c, o, E, eR, q, F, eg],
      ),
      eO = (0, l.useCallback)(
        async (e = !1, t = !1) => {
          var n, l;
          let i,
            u,
            a,
            d = ({ board: e, chain: t }) => ({
              kind: "board",
              board: e,
              url: (0, R.f)({
                limit: 300,
                userId: ed || void 0,
                pumpUserId: eh || void 0,
                ...(0, k.f)(em || void 0),
                chain: t,
                exposure: eg,
                board: e,
              }),
            }),
            y = {};
          switch (
            (o !== s.E.FEATURED &&
              (y = eA({
                sort: o,
                offset: e ? 0 : c,
                order: E,
                includeNsfw: h,
                useLocalFilterLimit: e,
              })),
            o)
          ) {
            case s.E.CHARITY:
              i = {
                kind: "client",
                route: "GET /coins/search-unrestricted",
                query: y,
              };
              break;
            case s.E.CUSTOM_PAIRS:
              i = {
                kind: "list",
                url:
                  ((u = new URLSearchParams({
                    offset: String(
                      (n = {
                        offset: e ? 0 : c,
                        limit: e ? 100 : f,
                        includeNsfw: h,
                      }).offset,
                    ),
                    limit: String(n.limit),
                    includeNsfw: String(n.includeNsfw),
                  })),
                  `/api/explore/custom-pairs?${u.toString()}`),
              };
              break;
            case s.E.MAJORS:
              i = {
                kind: "list",
                url:
                  ((a = new URLSearchParams({
                    offset: String(
                      (l = { offset: e ? 0 : c, limit: e ? 100 : f }).offset,
                    ),
                    limit: String(l.limit),
                  })),
                  `/api/explore/majors?${a.toString()}`),
              };
              break;
            case s.E.STOCKS:
              i = { kind: "list", url: (0, T.m)(!!ed), parse: T.K };
              break;
            case s.E.LIVE:
              ((ek.current = Date.now()),
                (i = {
                  kind: "client",
                  route: "GET /coins/currently-live",
                  query: {
                    limit: e ? 100 : f,
                    offset: e ? 0 : c,
                    includeNsfw: h,
                  },
                }));
              break;
            case s.E.CALLS:
              i = {
                kind: "list",
                url: (0, S.x)({
                  window: U,
                  offset: e ? 0 : c,
                  limit: e ? 100 : f,
                  includeNsfw: h,
                }),
                cache: "no-store",
              };
              break;
            case s.E.FEATURED:
              i = d({ board: "movers", chain: K });
              break;
            case s.E.TRENDING:
              i = d({ board: "trending" });
              break;
            default:
              i = {
                kind: "client",
                route: "GET /coins",
                query: r.contract["GET /coins"].query.parse(y),
              };
          }
          return eR(i, !t, j(o) ? !e : e, t);
        },
        [o, E, c, f, h, eA, eR, 100, K, U, eg, ed, eh, em],
      );
    eT.current = eO;
    let eM = (0, l.useCallback)(
      (0, i.t)(async (e) => {
        try {
          (J(!0), await eI(e));
        } catch (e) {
          console.error("Error during debounced search:", e);
        } finally {
          J(!1);
        }
      }, 1e3),
      [eI],
    );
    ((0, l.useEffect)(
      () => (
        P &&
          _?.trim() &&
          !eb.current &&
          (J(!0), eM({ searchTerm: _, useLocalFiltering: $ })),
        () => {
          eM.cancel();
        }
      ),
      [P, _, x, eM, $],
    ),
      (0, l.useEffect)(() => {
        let e = eT.current;
        !e || (ei(null), (!j(o) || 0 !== c || ec.current) && (P || e($)));
      }, [P, o, E, c, f, h, K, U, eg, $]));
    let eL = (0, l.useRef)(void 0);
    (0, l.useEffect)(() => {
      if (!j(o) || P || 0 !== c || !eE || (ec.current && ed === eL.current))
        return;
      let e = ec.current || eo.current;
      if (((ec.current = !0), Q)) {
        ((eL.current = ed), eT.current?.($, e));
        return;
      }
      eT.current?.($, e).then((e) => {
        e && (eL.current = ed);
      });
    }, [eE, ed, o, P, c, $, Q]);
    let eN = (0, y.q)(a.i, o === s.E.LIVE && !P);
    ((0, l.useEffect)(() => {
      if (!1 === eN) return;
      let e = () => {
          eT.current?.($, !0);
        },
        t = ek.current;
      0 !== t && Date.now() - t >= eN && e();
      let r = setInterval(e, eN);
      return () => clearInterval(r);
    }, [eN, $]),
      (0, l.useEffect)(
        () => () => {
          (eM.cancel(), ew.current && ew.current.abort());
        },
        [eM],
      ));
    let ej = (0, l.useCallback)(
        async (e) => {
          (eM.cancel(), (eb.current = !0), J(!0));
          try {
            await eI({ searchTerm: e, useLocalFiltering: $ });
          } finally {
            (J(!1), (eb.current = !1));
          }
        },
        [eM, eI, $],
      ),
      eD = (0, l.useCallback)((e) => eO($, e?.background === !0), [eO, $]);
    return {
      coins: Y,
      loading: W,
      error: eu,
      hasMorePages: Q ? (Z ?? X >= f) : X >= f,
      fetchCoins: eO,
      refetch: eD,
      fetchSearchCoins: eI,
      triggerSearch: ej,
      requestKey: et,
      rowsRequestKey: er,
      servedCoins: G,
      setCoins: (0, l.useCallback)((e) => {
        B(e);
      }, []),
    };
  };
  return function useBoardCoins(options) {
    if (
      ![SEARCH_SORT.FEATURED, SEARCH_SORT.TRENDING].includes(options?.sort) ||
      options.isSearchMode
    )
      throw new TypeError(
        "Only non-search featured/trending board inputs are admitted",
      );
    const result = originalHook(options);
    return {
      coins: result.coins,
      loading: result.loading,
      error: result.error,
      hasMorePages: result.hasMorePages,
      fetchCoins: result.fetchCoins,
      refetch: result.refetch,
      requestKey: result.requestKey,
      rowsRequestKey: result.rowsRequestKey,
      servedCoins: result.servedCoins,
      setCoins: result.setCoins,
    };
  };
}
