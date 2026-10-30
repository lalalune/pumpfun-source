// Synthetic ordinary-history/read-result host; no actual storage/query/navigation.
import React, {
  useContext,
  useState,
  useMemo,
} from "../../packages/frontend/node_modules/react/index.js";
import { createRoot } from "../../packages/frontend/node_modules/react-dom/client.js";
import * as jsxRuntime from "../../packages/frontend/node_modules/react/jsx-runtime.js";
import { c } from "../../packages/frontend/node_modules/react/compiler-runtime.js";
import { createRecentSearchRenderer } from "../../reconstruction/recent-search-renderer/client.mjs";
const { jsx, jsxs } = jsxRuntime,
  Scope = React.createContext(null),
  SOL = "11111111111111111111111111111111",
  EVM = "0x" + "a".repeat(40),
  NEAR = "synthetic.near",
  GROUP = "00000000-0000-0000-0000-000000000001",
  events = [],
  records = {
    coinRows: [],
    groupRows: [],
    profiles: [],
    groupQueries: [],
    profilesRequested: [],
    updates: [],
  },
  empty = [];
let root,
  current,
  patch,
  setTerms,
  lastGroupOptions,
  serial = 0,
  lastHydration,
  lastNear;
const read = () => useContext(Scope),
  navigateA = () => events.push({ type: "navigate", label: "A" }),
  navigateB = () => events.push({ type: "navigate", label: "B" }),
  api = () => {
    throw Error("Actual group/account request excluded");
  };
const translate = (key, p) =>
  key === "common.followers_count"
    ? `followers:${p.count}|${p.compact_count}`
    : key;
const activeNavigate = () => (current.callbackB ? navigateB : navigateA);
const renderers = {
  Heading: ({ title, aside }) =>
    jsxs("header", { children: [jsx("h2", { children: title }), aside] }),
  Empty: ({ children }) => jsx("div", { "data-testid": "empty", children }),
  SkeletonPart: (p) =>
    jsx("span", { "data-testid": "pending-part", children: "…" }),
  SearchIcon: (p) =>
    jsx("span", { "aria-hidden": p["aria-hidden"], children: "search icon" }),
  Link: ({ href, onClick, children, ...p }) =>
    jsx("a", {
      href,
      onClick: (e) => {
        e.preventDefault();
        onClick?.(e);
        events.push({ type: "host-link", href });
      },
      "aria-label": p["aria-label"],
      style: {
        display: "inline-block",
        minWidth: 100,
        minHeight: 24,
        padding: 5,
      },
      children: children ?? "supplied link",
    }),
  CoinRow: (p) => {
    records.coinRows.push({
      mint: p.coin.mint,
      index: p.index,
      sourceScreen: p.sourceScreen,
      sourceElement: p.sourceElement,
      searchTerm: p.searchTerm,
      callbackMatches: p.onClick === activeNavigate(),
    });
    return jsx("button", {
      type: "button",
      "data-testid": "coin-row",
      onClick: () => p.onClick(),
      children: "Coin " + p.coin.mint,
    });
  },
  GroupRow: (p) => {
    records.groupRows.push({
      squad: p.squad,
      callbackMatches: p.onClick === activeNavigate(),
    });
    return jsx("button", {
      type: "button",
      "data-testid": "group-row",
      onClick: () => p.onClick(),
      children: "Group " + p.squad.groupId,
    });
  },
  ProfileDisplay: (p) => {
    records.profiles.push(p);
    return jsxs("div", {
      "data-testid": "profile-display",
      "data-name": p.nameOverride,
      "data-verified": String(p.verified),
      children: [
        jsx("b", { children: p.nameOverride }),
        jsx("span", { children: p.description }),
      ],
    });
  },
};
const ports = {
  React,
  jsxRuntime,
  memoCache: c,
  renderers,
  useTranslation: () => ({ t: translate }),
  useChainFlags: () => read().chainFlags,
  nearEnabled: (f) => f.near,
  validSolanaAddress: (value) => value === SOL,
  isEvmAddress: (value) => value === EVM,
  canonicalCoinAddress: (value) =>
    value.startsWith("0x") ? value.toLowerCase() : value,
  isGroupIdentifier: (value) =>
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
      value,
    ),
  useGroupClient: () => api,
  useGroupsEnabled: () => read().groupsEnabled,
  groupProfileKey: (id) => ["supplied-group", id],
  readGroup: async (options) => {
    events.push({
      type: "group-reader-port",
      id: options.groupId,
      apiMatches: options.api === api,
      hasSignal: options.signal instanceof AbortSignal,
    });
    if (current.rejectGroup) throw Error("Synthetic group port failure");
    return current.groupData;
  },
  useQueries: (options) => {
    const s = read();
    lastGroupOptions = options;
    records.groupQueries.push(
      options.queries.map((q) => ({
        key: q.queryKey,
        enabled: q.enabled,
        staleTime: q.staleTime,
      })),
    );
    return options.combine(
      options.queries.map((q) => ({
        data: s.groupData,
        isPending: s.groupPending,
        error: s.groupError ? Error("Synthetic supplied query error") : null,
      })),
    );
  },
  useNearCoins: (mints, enabled) => {
    const s = read();
    lastNear = { mints, enabled };
    return useMemo(
      () => ({ byAddress: new Map(s.nearData), pending: s.nearPending }),
      [s.nearData, s.nearPending],
    );
  },
  useCoinHydration: (options) => {
    const s = read();
    lastHydration = options;
    return {
      coins: s.coins,
      loading: s.coinLoading,
      isLoadingError: s.coinError,
      fallbackPending: s.fallbackPending,
    };
  },
  walletProfile: () => readCurrentCurve(),
  useCoinUpdates: (...args) => {
    records.updates.push({
      arity: args.length,
      mints: args[0].map((r) => r.mint),
    });
  },
  useProfile: (options) => {
    records.profilesRequested.push(options);
    return { data: read().profile };
  },
  useVerifiedProfile: (subject) => {
    events.push({ type: "verified-subject", subject });
    return read().verified;
  },
  formatFollowers: (value) => "compact:" + value,
  classNames: (...v) => v.filter(Boolean).join(" "),
  normalizeNearInput: (value) => {
    const t = value.trim();
    return t === NEAR ? t : null;
  },
  styles: { row: "synthetic-row", action: "synthetic-action" },
  avatarSize: 28,
};
function readCurrentCurve() {
  return current.curve;
}
const { RecentTerms } = createRecentSearchRenderer(ports),
  terms = ["plain & text", SOL, GROUP, NEAR, EVM, "  spaced term  "],
  initial = {
    terms,
    canExpand: true,
    chainFlags: { near: true },
    groupsEnabled: true,
    groupData: undefined,
    groupPending: true,
    groupError: false,
    rejectGroup: false,
    coins: empty,
    coinLoading: true,
    coinError: false,
    fallbackPending: false,
    nearData: empty,
    nearPending: true,
    curve: true,
    profile: undefined,
    verified: false,
    callbackB: false,
  };
function Host() {
  const [s, set] = useState(initial);
  serial++;
  current = s;
  patch = (p) => set((old) => ({ ...old, ...p }));
  setTerms = (terms) => set((old) => ({ ...old, terms }));
  return jsx(Scope.Provider, {
    value: s,
    children: jsx(RecentTerms, {
      terms: s.terms,
      canExpand: s.canExpand,
      onClear: () => {
        events.push({ type: "clear" });
        setTerms([]);
      },
      onNavigate: activeNavigate(),
    }),
  });
}
window.recentSearchHarness = {
  values: { SOL, EVM, NEAR, GROUP, terms },
  patch: (p) => patch(p),
  serial: () => serial,
  state: () => ({
    termCount: current.terms.length,
    canExpand: current.canExpand,
    groupQueries: lastGroupOptions.queries.map((q) => ({
      key: q.queryKey,
      enabled: q.enabled,
      staleTime: q.staleTime,
    })),
    hydration: lastHydration,
    near: lastNear,
    updates: records.updates.at(-1),
  }),
  records: () => ({
    coinRows: records.coinRows,
    groupRows: records.groupRows,
    profiles: records.profiles.map(
      ({
        address,
        username,
        profileImage,
        avatarDecoration,
        nameOverride,
        verified,
        xUsername,
        description,
        link,
        hoverCard,
      }) => ({
        address,
        username,
        profileImage,
        avatarDecoration,
        nameOverride,
        verified,
        xUsername,
        description,
        link,
        hoverCard,
      }),
    ),
    profilesRequested: records.profilesRequested,
    groupQueries: records.groupQueries,
    updates: records.updates,
  }),
  events: () => events,
  async groupRequest() {
    const signal = new AbortController().signal;
    const q = lastGroupOptions.queries[0];
    try {
      const result = await q.queryFn({ signal });
      return { result };
    } catch (e) {
      return { error: e.message };
    }
  },
  unmount: () => root.unmount(),
};
root = createRoot(document.getElementById("root"));
root.render(jsx(Host, {}));
