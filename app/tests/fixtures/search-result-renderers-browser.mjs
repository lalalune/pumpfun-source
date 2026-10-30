// Supplied synthetic data/presentation ports; no provider or protected action.
import React, {
  useContext,
  useState,
} from "../../packages/frontend/node_modules/react/index.js";
import { createRoot } from "../../packages/frontend/node_modules/react-dom/client.js";
import * as jsxRuntime from "../../packages/frontend/node_modules/react/jsx-runtime.js";
import { c } from "../../packages/frontend/node_modules/react/compiler-runtime.js";
import { createSearchResultRenderers } from "../../reconstruction/search-result-renderers/client.mjs";
const { jsx, jsxs } = jsxRuntime,
  Scope = React.createContext(null),
  events = [],
  records = {
    profiles: [],
    avatars: [],
    menu: [],
    impressions: [],
    capInputs: [],
    capFormats: [],
    age: [],
    groupRoutes: [],
  },
  ids = new WeakMap();
let counter = 0,
  patch,
  root,
  serial = 0,
  current;
const id = (o) => {
    if (!ids.has(o)) ids.set(o, ++counter);
    return ids.get(o);
  },
  useScope = () => useContext(Scope),
  event = (type, ...args) => events.push({ type, args });
const translate = (key, values) =>
  key === "common.followers_count"
    ? `followers:${values.count}|${values.compact_count}`
    : key === "profile.squads.info.member_count"
      ? `members:${values.count}`
      : key;
function Link(p) {
  return jsx("a", {
    href: p.href,
    onClick: (e) => {
      e.preventDefault();
      p.onClick?.(e);
      event("host-link", p.href);
    },
    onMouseEnter: p.onMouseEnter,
    "aria-label": p["aria-label"],
    "data-testid": p["data-testid"],
    style: {
      display: "inline-block",
      minWidth: 100,
      minHeight: 24,
      padding: 6,
    },
    children: p.children ?? "supplied link",
  });
}
function ProfileDisplay(p) {
  records.profiles.push(p);
  return jsxs("div", {
    "data-testid": "profile-display",
    "data-name": p.nameOverride,
    "data-verified": String(p.verified),
    "data-outside": String(p.outsideWallet),
    children: [
      jsx("b", { children: p.nameOverride }),
      jsx("span", { children: p.description }),
    ],
  });
}
const Avatar = (p) => {
  records.avatars.push(p);
  return jsx("span", {
    "data-testid": "avatar",
    "data-address": p.address,
    children: "supplied avatar",
  });
};
const renderers = {
  Link,
  ProfileDisplay,
  Avatar,
  BookmarkMenu: (p) => {
    records.menu.push(p);
    return jsx("span", {
      "data-testid": "inert-menu-descriptor",
      children: "inert menu position " + p.position,
    });
  },
  CoinAvatar: (p) =>
    jsx("span", { children: "supplied coin avatar " + p.coin.mint }),
  CoinName: (p) => jsx("b", { children: p.coin.name ?? p.coin.mint }),
  RelativeTime: (p) => {
    records.age.push(p);
    return jsx("span", {
      "data-testid": "supplied-age",
      children: "age:" + p.timestamp,
    });
  },
  SkeletonPart: (p) =>
    jsx("span", {
      "data-testid": "skeleton-part",
      "data-variant": p.variant ?? "text",
      children: "…",
    }),
  GroupIcon: () => jsx("span", { children: "group icon" }),
  Badge: ({ children }) => jsx("span", { children }),
  Heading: ({ title, aside }) =>
    jsxs("header", { children: [jsx("h2", { children: title }), aside] }),
  PerpRow: () => {
    throw Error("Deferred Perps rendering excluded");
  },
};
const close = () => event("row-close"),
  lastClick = (mint, metadata, term) =>
    event("last-click", mint, metadata, term, id(metadata)),
  coinClick = (mint, metadata, term) =>
    event("coin-click", mint, metadata, term, id(metadata));
const ports = {
  jsxRuntime,
  memoCache: c,
  renderers,
  useTranslation: () => ({ t: translate }),
  useCoinMarketCap: (options) => {
    records.capInputs.push({
      mint: options.mint,
      chainId: options.chainId,
      fallbackMarketCap: options.fallbackMarketCap,
      coinId: id(options.coin),
    });
    return useScope().marketCap;
  },
  useCoinImpression: (mint, metadata, term, element) => {
    records.impressions.push({
      mint,
      metadata,
      term,
      element,
      metadataId: id(metadata),
    });
    return null;
  },
  useCoinClick: () => ({ handleCoinClick: coinClick }),
  useLastClick: () => ({ setLastClickImpression: lastClick }),
  useCoinPrefetch: () => ({
    prefetch: false,
    hoverProps: {
      onClick: () => event("overridden-hover-click"),
      onMouseEnter: () => event("supplied-hover"),
    },
  }),
  trackBookmark: () => {
    throw Error("Menu action/analytics execution excluded from proof");
  },
  formatSymbol: (value) => value?.toUpperCase(),
  shortenAddress: (value) => "short:" + value,
  classNames: (...v) => v.filter(Boolean).join(" "),
  formatMarketCap: (value) => {
    records.capFormats.push(value);
    return "market:" + value;
  },
  formatFollowers: (value) => "compact:" + value,
  useVerifiedProfile: (subject) => {
    event("verified-subject", subject);
    return useScope().verified;
  },
  groupRoute: (options) => {
    records.groupRoutes.push(options);
    return "/supplied-group/" + encodeURIComponent(options.groupId);
  },
  normalizeImage: (value) => (value ? "supplied-image:" + value : null),
  projectGroup: (row) => {
    event("project-group", row.userId, id(row));
    return current.projected;
  },
  isPerp: (row) => row.kind === "perp",
  perpDisplay: () => {
    throw Error("Deferred Perps classification excluded");
  },
  theme: {
    x: { comfortable: "theme-x" },
    n: { comfortable: "theme-n" },
    B: { comfortable: "theme-B" },
    Y: { comfortable: "theme-Y" },
    e: { comfortable: "theme-e" },
    N: "theme-N",
    C: { comfortable: "theme-C" },
  },
  styles: { row: "synthetic-row", seeAll: "synthetic-see-all" },
  avatarSize: 28,
  imagePrefix: "synthetic-image-prefix",
};
// Projection is a required supplied result, not a reconstruction of760447.h.
const family = createSearchResultRenderers(ports),
  coin = {
    mint: "synthetic-coin",
    name: "Synthetic coin",
    symbol: "syn",
    usd_market_cap: 12.345,
    rec_id: "synthetic-rec",
    created_timestamp: 0,
  },
  user = {
    userId: "user-1",
    address: " wallet one ",
    username: "Name",
    followers: 7,
  },
  group = { userId: "source-group", memberCount: 9 };
const section = (rows) => ({
    rows,
    loading: false,
    visible: true,
    hasMore: true,
  }),
  initial = {
    mode: "mixed",
    marketCap: 0,
    verified: false,
    coins: section([coin]),
    users: section([user]),
    squads: section([group]),
    projected: {
      groupId: "projected-group",
      username: "",
      profileImage: "local-image",
      memberCount: 9,
    },
    searchTerm: "term",
    sourceScreen: undefined,
    sourceElement: undefined,
    directCoin: coin,
    skeletonRows: 2,
    skeletonVariant: "art",
  };
function Host() {
  const [s, set] = useState(initial);
  serial++;
  current = s;
  patch = (p) => set((old) => ({ ...old, ...p }));
  return jsx(Scope.Provider, {
    value: s,
    children:
      s.mode === "mixed"
        ? jsx(family.MixedResults, {
            searchTerm: s.searchTerm,
            coins: s.coins,
            users: s.users,
            squads: s.squads,
            onSeeAll: (tab) => event("see-all", tab),
            onCoinClick: (row) => event("selected-coin", row.mint, id(row)),
            onUserClick: (row) =>
              event("selected-user", row.userId ?? row.address, id(row)),
            onSquadClick: (row) => event("selected-group", row.userId, id(row)),
          })
        : s.mode === "coin"
          ? jsx(family.CoinRow, {
              coin: s.directCoin,
              index: 2,
              searchTerm: s.searchTerm,
              sourceScreen: s.sourceScreen,
              sourceElement: s.sourceElement,
              onClick: close,
            })
          : s.mode === "user"
            ? jsx(family.UserRow, { user: s.directUser, onClick: close })
            : jsx(family.Skeleton, {
                rows: s.skeletonRows,
                variant: s.skeletonVariant,
              }),
  });
}
window.searchResultHarness = {
  patch: (p) => patch(p),
  serial: () => serial,
  state: () => ({
    mode: current.mode,
    marketCap: current.marketCap,
    verified: current.verified,
    coinId: id(current.coins.rows[0] ?? coin),
    groupId: id(current.squads.rows[0] ?? group),
  }),
  events: () => events,
  records: () => ({
    profiles: records.profiles.map(
      ({
        nameOverride,
        address,
        userId,
        description,
        outsideWallet,
        verified,
        link,
        hoverCard,
      }) => ({
        nameOverride,
        address,
        userId,
        description,
        outsideWallet,
        verified,
        link,
        hoverCard,
      }),
    ),
    avatars: records.avatars,
    menu: records.menu.map((p) => ({
      mint: p.coin.mint,
      align: p.align,
      position: p.position,
      hasAnalytics: typeof p.analytics.trackBookmarkToggle === "function",
    })),
    impressions: records.impressions,
    capInputs: records.capInputs,
    capFormats: records.capFormats,
    age: records.age,
    groupRoutes: records.groupRoutes,
  }),
  unmount: () => root.unmount(),
};
root = createRoot(document.getElementById("root"));
root.render(jsx(Host, {}));
