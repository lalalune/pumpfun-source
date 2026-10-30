// Synthetic React host: all data/query/storage/router/renderer ports are supplied.
import React, {
  useContext,
  useState,
} from "../../packages/frontend/node_modules/react/index.js";
import { createRoot } from "../../packages/frontend/node_modules/react-dom/client.js";
import * as jsxRuntime from "../../packages/frontend/node_modules/react/jsx-runtime.js";
import { c } from "../../packages/frontend/node_modules/react/compiler-runtime.js";
import { createSearchDialogController } from "../../reconstruction/search-dialog-controller/client.mjs";
const { jsx, jsxs } = jsxRuntime,
  Context = React.createContext(null),
  events = [],
  resolverCalls = [],
  inputCalls = [];
const none = [],
  queryClient = {
    setQueryData: (key, value) =>
      events.push({ type: "group-cache", key, value }),
  };
const keyListeners = new Set();
const browserWindow = {
  addEventListener(type, handler) {
    if (type !== "keydown") throw Error("Unexpected event capability");
    keyListeners.add(handler);
    window.addEventListener(type, handler);
  },
  removeEventListener(type, handler) {
    keyListeners.delete(handler);
    window.removeEventListener(type, handler);
  },
};
let latest = {},
  patch,
  resetHost,
  root,
  serial = 0,
  lastOptions = {},
  lastGroupOptions,
  lastNearOptions;
const readScope = () => useContext(Context),
  translate = (k) => k;
const track =
  (type) =>
  (...args) =>
    events.push({ type, args });
const groupClient = async () => {
  throw Error("Unexpected synthetic group client operation");
};
function Input(p) {
  return jsxs("div", {
    children: [
      jsx("input", {
        ref: p.inputRef,
        value: p.value,
        onChange: (e) => p.onValueChange(e.target.value),
        onPaste: p.onPaste,
        "aria-label": "Synthetic search input",
        autoComplete: "off",
      }),
      jsx("button", {
        type: "button",
        onClick: () => {
          p.onClear();
          p.onValueChange("");
        },
        children: "Clear supplied input",
      }),
      jsx("button", { type: "submit", children: "Submit supplied input" }),
    ],
  });
}
function Dialog(p) {
  latest.dialog = p;
  return p.open
    ? jsxs("div", {
        role: "dialog",
        "aria-label": "Synthetic search dialog",
        children: [
          jsx("button", {
            type: "button",
            onClick: () => p.onOpenChange(false),
            children: "Close supplied dialog",
          }),
          ...p.children,
        ],
      })
    : null;
}
const Box = ({ children }) => jsx("div", { children });
const CoinRow = ({ coin, onClick, index }) =>
  jsx("button", {
    type: "button",
    onClick,
    "data-kind": "coin",
    "data-index": index,
    children: "Coin " + coin.mint,
  });
const UserRow = ({ user, onClick }) =>
  jsx("button", {
    type: "button",
    onClick,
    "data-kind": "user",
    children: "User " + (user.userId ?? user.address),
  });
const GroupRow = ({ squad, onClick }) =>
  jsx("button", {
    type: "button",
    onClick,
    "data-kind": "group",
    children: "Group " + squad.userId,
  });
function MixedResults(p) {
  latest.mixed = p;
  return jsx("section", {
    children: ["coins", "users", "squads"]
      .filter((k) => p[k].visible)
      .map((k) =>
        jsxs(
          "section",
          {
            "data-section": k,
            children: [
              jsx("b", { children: k }),
              p[k].loading
                ? jsx("span", { children: "Supplied " + k + " pending" })
                : null,
              ...p[k].rows.map((r, i) =>
                jsx(
                  "button",
                  {
                    type: "button",
                    onClick: () =>
                      ({
                        coins: p.onCoinClick,
                        users: p.onUserClick,
                        squads: p.onSquadClick,
                      })[k](r),
                    children: k + " " + (r.mint ?? r.userId ?? r.address),
                  },
                  i,
                ),
              ),
              p[k].hasMore
                ? jsx("button", {
                    type: "button",
                    onClick: () => p.onSeeAll(k),
                    children: "See all " + k,
                  })
                : null,
            ],
          },
          k,
        ),
      ),
  });
}
function Tabs(p) {
  latest.tabs = p;
  return jsx("nav", {
    "aria-label": "Supplied result tabs",
    children: p.tabs.map((tab) =>
      jsx(
        "button",
        {
          type: "button",
          disabled: tab.disabled,
          "aria-pressed": p.value === tab.value,
          onClick: () => {
            tab.onClick?.();
            if (p.value !== tab.value) p.onValueChange(tab.value);
          },
          children: tab.value + ":" + tab.count,
        },
        tab.value,
      ),
    ),
  });
}
function Recommendations(p) {
  latest.recommendations = p;
  return jsx("div", {
    "data-testid": "recommendations",
    children: JSON.stringify({
      traders: p.topTraders.length,
      coins: p.trendingCoins.length,
      loading: p.topTradersLoading || p.trendingLoading,
    }),
  });
}
function RecentTerms(p) {
  latest.terms = p;
  return jsx("div", {
    "data-testid": "recent-terms",
    children: p.terms.join("|"),
  });
}
const renderers = {
  Dialog,
  Body: Box,
  Footer: Box,
  Input,
  Heading: ({ title, aside }) => jsxs("div", { children: [title, aside] }),
  Empty: Box,
  Tabs,
  Link: ({ href, onClick, children, ...p }) =>
    jsx("a", {
      href,
      onClick: (e) => {
        e.preventDefault();
        onClick?.(e);
        events.push({ type: "link", href });
      },
      "data-testid": p["data-testid"],
      children,
    }),
  ArrowIcon: () => null,
  Recommendations,
  RecentTerms,
  RecentCard: ({ card, onClick }) =>
    jsx("button", {
      type: "button",
      onClick,
      children: "Card " + card.nftAddress,
    }),
  CoinRow,
  Skeleton: ({ variant }) =>
    jsx("div", { "data-testid": "skeleton", children: variant }),
  MixedResults,
  GroupRow,
  UserRow,
};
const ports = {
  React,
  jsxRuntime,
  memoCache: c,
  browserWindow,
  browserDocument: document,
  AbortController,
  DOMException,
  renderers,
  useTranslation: () => ({ t: translate }),
  useSearchOpen: () => readScope().open,
  useSetSearchOpen: () => readScope().setOpen,
  useNsfw: () => false,
  useLocalTerms: (key, initial) => {
    const s = readScope();
    latest.termsKey = key;
    return [s.terms, s.setTerms];
  },
  useDebouncedValue: (v, ms) => {
    const s = readScope();
    latest.debounce = { value: v, ms };
    return [s.debounced === null ? v : s.debounced];
  },
  useRecentCoins: () => {
    const s = readScope();
    return [s.recentCoins, null, s.clearCoins, s.viewedAt];
  },
  recentCoinViewedAt: ({ times, mint }) => times[mint],
  useRecentCards: () => {
    const s = readScope();
    return [s.recentCards, null, s.clearCards];
  },
  useChainFlags: () => readScope().chainFlags,
  nearEnabled: (f) => !!f.near,
  hexEnabled: (f) => !!f.hex,
  useCoinHydration: (options) => {
    latest.hydration = options;
    return { coins: readScope().hydratedCoins };
  },
  canonicalCoinAddress: (mint) => mint.toLowerCase(),
  isEvmAddress: (v) => /^0x[0-9a-fA-F]{40}$/.test(v),
  useFlag: (key) => {
    const s = readScope();
    return {
      webPacks: s.packs,
      webSearchMixedResults: s.mixed,
      webPerps: false,
    }[key];
  },
  useRouter: () => ({ push: track("push") }),
  useCoinClick: () => ({ handleCoinClick: track("coin-click") }),
  useLastClick: () => ({ setLastClickImpression: track("last-click") }),
  validSolanaAddress: (v) => v === "11111111111111111111111111111111",
  walletProfile: () => true,
  probeKnownMint: async () => false,
  probeSolanaMint: async () => false,
  resolveIdentifier: (term, signal) => {
    const call = { id: resolverCalls.length + 1, term, signal };
    call.promise = new Promise((resolve, reject) => {
      call.resolve = resolve;
      call.reject = reject;
    });
    resolverCalls.push(call);
    events.push({ type: "resolve", id: call.id, term });
    return call.promise;
  },
  getContractClient: () => async () => {
    throw Error("Unplanned service request excluded");
  },
  trackMintPaste: track("mint-paste"),
  trackWalletPaste: track("wallet-paste"),
  trackSearch: track("search"),
  trackOpen: track("open"),
  trackClear: track("clear"),
  trackTab: track("tab"),
  readCoin: async () => {
    throw Error("Unplanned coin reader excluded");
  },
  readTrendingCoins: async () => {
    events.push({ type: "trending-read" });
    return [];
  },
  readPnlLeaders: async (options) => {
    events.push({ type: "pnl-read", options });
    return { entries: [] };
  },
  useQuery: (options) => {
    const s = readScope(),
      trending = options.queryKey[0] === "trending";
    lastOptions[trending ? "trending" : "pnl"] = options;
    return {
      data: trending ? s.trending : s.leaders,
      isLoading: s.queryLoading,
    };
  },
  queryKeys: {
    TRENDING_COINS: ["trending"],
    PNL_LEADERBOARD: (o) => ["pnl", o],
    COIN: (o) => ["coin", o],
  },
  useCoinSearch: (options) => {
    const s = readScope();
    latest.coinOptions = options;
    return { coins: s.coins, loading: s.coinLoading };
  },
  isPerp: (row) => row.kind === "perp",
  perpDisplay: () => {
    throw Error("Deferred Perps branch excluded from finite proof");
  },
  useCoinUpdates: (coins, enabled) => {
    latest.coinUpdates = { coins, enabled };
  },
  useUserSearch: (options) => {
    const s = readScope();
    latest.userOptions = options;
    return {
      users: s.users,
      loading: s.userLoading,
      isSearchTermTooShort: options.searchTerm.trim().length < 2,
      isDebouncing: s.userDebouncing,
      minSearchTermLength: 2,
    };
  },
  useGroupsEnabled: () => readScope().groups,
  useGroupClient: () => groupClient,
  useQueryClient: () => queryClient,
  projectGroup: (row) => ({ ...row, projected: true }),
  useInfiniteQuery: (options) => {
    const s = readScope();
    lastGroupOptions = options;
    return {
      data: s.groupRows,
      isFetching: s.groupLoading,
      error: s.groupError,
      fetchNextPage: track("next-group-page"),
      hasNextPage: false,
      isFetchingNextPage: false,
    };
  },
  useQueries: (options) => {
    lastNearOptions = options;
    const s = readScope();
    return options.combine(
      options.queries.map((q) => ({
        data: s.nearCoins.find((r) => r.mint === q.queryKey[1].coinAddress),
        isLoading: false,
      })),
    );
  },
  searchGroups: async (options) => {
    inputCalls.push(options);
    if (options.searchTerm === "synthetic-reject")
      throw Error("Synthetic group reader failure");
    return [{ userId: "synthetic-group" }];
  },
  groupSearchKey: (term, limit) => ["supplied-groups", term, limit],
  groupProfileKey: (id) => ["supplied-group", id],
  keepPreviousData: (old) => old,
  normalizeHexIdentifier: (v) =>
    /^0x[0-9a-fA-F]{41,64}$/.test(v)
      ? "0x" + v.slice(2).toLowerCase().padStart(64, "0")
      : null,
  isNearCoin: (row) => row.chain_id === "near:mainnet",
  isHexCoin: (row) => row.chain_id === "starknet:SN_MAIN",
  isNearIdentifier: (v) => v.endsWith(".near"),
  classNames: (...v) => v.filter(Boolean).join(" "),
  styles: {
    key: "synthetic-key",
    viewAll: "synthetic-view-all",
    clear: "synthetic-clear",
  },
};
const { SearchDialogLazy } = createSearchDialogController(ports),
  initial = {
    open: false,
    mixed: true,
    packs: true,
    groups: true,
    terms: ["old"],
    recentCoins: [],
    recentCards: [],
    viewedAt: {},
    chainFlags: { near: false, hex: false },
    hydratedCoins: none,
    nearCoins: none,
    trending: none,
    leaders: { entries: none },
    coins: none,
    users: none,
    groupRows: none,
    coinLoading: false,
    userLoading: false,
    groupLoading: false,
    queryLoading: false,
    userDebouncing: false,
    groupError: null,
    debounced: null,
  };
function Host() {
  const [s, set] = useState(initial);
  serial++;
  patch = (p) => set((old) => ({ ...old, ...p }));
  const scope = {
    ...s,
    setOpen: (v) => set((old) => ({ ...old, open: v })),
    setTerms: (v) => set((old) => ({ ...old, terms: v })),
    clearCoins: () => {
      events.push({ type: "clear-coins" });
      set((old) => ({ ...old, recentCoins: [] }));
    },
    clearCards: () => {
      events.push({ type: "clear-cards" });
      set((old) => ({ ...old, recentCards: [] }));
    },
  };
  latest.scope = scope;
  return jsx(Context.Provider, {
    value: scope,
    children: jsx(SearchDialogLazy, {
      onMounted: () => events.push({ type: "mounted" }),
    }),
  });
}
const simpleOptions = (o) => ({
  queryKey: o.queryKey,
  enabled: o.enabled,
  staleTime: o.staleTime,
  gcTime: o.gcTime,
  refetchOnWindowFocus: o.refetchOnWindowFocus,
  refetchOnMount: o.refetchOnMount,
  initialPageParam: o.initialPageParam,
  hasPlaceholder: o.placeholderData !== undefined,
});
window.searchDialogHarness = {
  mount() {
    root = createRoot(document.getElementById("root"));
    root.render(jsx(Host, {}));
  },
  patch: (p) => patch(p),
  serial: () => serial,
  state: () => ({
    open: latest.scope.open,
    terms: latest.scope.terms,
    query: latest.coinOptions.searchTerm,
    tab: latest.tabs?.value,
    coinUpdates: latest.coinUpdates.coins.map((r) => r.mint),
    updatesEnabled: latest.coinUpdates.enabled,
    hydration: latest.hydration,
    termsKey: latest.termsKey,
    keyListeners: keyListeners.size,
    debounce: latest.debounce,
    trending: simpleOptions(lastOptions.trending),
    pnl: simpleOptions(lastOptions.pnl),
    group: simpleOptions(lastGroupOptions),
    near: lastNearOptions.queries.map((q) => ({
      queryKey: q.queryKey,
      retry: q.retry,
      refetchOnWindowFocus: q.refetchOnWindowFocus,
    })),
    mixed: latest.mixed
      ? Object.fromEntries(
          ["coins", "users", "squads"].map((k) => [
            k,
            {
              ...latest.mixed[k],
              rows: latest.mixed[k].rows.map(
                (r) => r.mint ?? r.userId ?? r.address,
              ),
            },
          ]),
        )
      : null,
  }),
  events: () => events,
  resolveCalls: () =>
    resolverCalls.map((c) => ({
      id: c.id,
      term: c.term,
      aborted: c.signal.aborted,
    })),
  release: (id, value) => resolverCalls.find((c) => c.id === id).resolve(value),
  paste(text) {
    const input = document.querySelector("input");
    const data = new DataTransfer();
    data.setData("text", text);
    input.dispatchEvent(
      new ClipboardEvent("paste", {
        bubbles: true,
        cancelable: true,
        clipboardData: data,
      }),
    );
  },
  async groupRequest(page) {
    const signal = new AbortController().signal;
    const result = await lastGroupOptions.queryFn({ pageParam: page, signal });
    return {
      result,
      forwardedSignal: inputCalls.at(-1).signal === signal,
      offset: inputCalls.at(-1).offset,
      limit: inputCalls.at(-1).limit,
      clientMatches: inputCalls.at(-1).api === groupClient,
    };
  },
  groupNext: (last, pages) => lastGroupOptions.getNextPageParam(last, pages),
  groupSelect: (data) => lastGroupOptions.select(data),
  queryRead: (kind) => lastOptions[kind].queryFn(),
  unmount() {
    root.unmount();
  },
};
window.searchDialogHarness.mount();
