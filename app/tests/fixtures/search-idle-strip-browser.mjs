// Ordinary supplied discovery rows and inert browser/provider capabilities only.
import React, {
  useContext,
  useState,
} from "../../packages/frontend/node_modules/react/index.js";
import { createRoot } from "../../packages/frontend/node_modules/react-dom/client.js";
import * as jsxRuntime from "../../packages/frontend/node_modules/react/jsx-runtime.js";
import { c } from "../../packages/frontend/node_modules/react/compiler-runtime.js";
import { createSearchIdleStrip } from "../../reconstruction/search-idle-strip/client.mjs";
const { jsx, jsxs } = jsxRuntime,
  Scope = React.createContext(null),
  events = [],
  records = {
    profiles: [],
    coinImpressions: [],
    liveCaps: [],
    charts: [],
    prefetch: [],
    profileDisplay: [],
    sparkline: [],
    formats: [],
  };
let current,
  patch,
  root,
  serial = 0,
  storageValue = "invalid-seed";
const read = () => useContext(Scope),
  navigateA = () => events.push({ type: "navigate", label: "A" }),
  navigateB = () => events.push({ type: "navigate", label: "B" });
const coinRows = Array.from({ length: 6 }, (_, i) => ({
  mint: "supplied-mint-" + i,
  name: "Supplied coin " + i,
  symbol: i ? "S" + i : "",
  usd_market_cap: i ? 120.125 : 0,
  chain_id: i % 2 ? "eip155:1" : "solana:mainnet",
  created_timestamp: i ? 1700000000000 : null,
}));
const traders = Array.from({ length: 6 }, (_, i) => ({
  walletAddress: "suppliedWalletAddress" + i,
  username: i ? "Trader " + i : "",
  profileImage: "supplied-image-" + i,
  xUsername: "supplied-x-" + i,
  pnlUsd: i ? 40 : -10,
  pnlPercent: i ? 2 : -1,
}));
class TrackedMutationObserver extends MutationObserver {
  constructor(cb) {
    super(cb);
    events.push({ type: "mutation-create" });
  }
  observe(node, options) {
    events.push({ type: "mutation-observe", options });
    return super.observe(node, options);
  }
  disconnect() {
    events.push({ type: "mutation-disconnect" });
    return super.disconnect();
  }
}
class TrackedResizeObserver extends ResizeObserver {
  constructor(cb) {
    super(cb);
    events.push({ type: "resize-create" });
  }
  observe(node) {
    events.push({ type: "resize-observe" });
    return super.observe(node);
  }
  disconnect() {
    events.push({ type: "resize-disconnect" });
    return super.disconnect();
  }
}
const browserWindow = {
  sessionStorage: {
    getItem(key) {
      events.push({ type: "storage-get", key });
      if (current.readFails) throw Error("Synthetic read denied");
      return storageValue;
    },
    setItem(key, value) {
      events.push({ type: "storage-set", key, value });
      if (current.writeFails) throw Error("Synthetic write denied");
      storageValue = value;
    },
  },
  matchMedia(query) {
    events.push({ type: "motion-query", query });
    return { matches: current.reducedMotion };
  },
};
const renderers = {
  Heading: ({ title, action }) => jsxs("header", { children: [title, action] }),
  Empty: ({ children }) => jsx("p", { "data-testid": "empty", children }),
  SkeletonPart: (p) =>
    jsx("span", { "data-testid": "skeleton-part", children: "…" }),
  PreviousIcon: () =>
    jsx("span", { "aria-hidden": true, children: "previous" }),
  NextIcon: () => jsx("span", { "aria-hidden": true, children: "next" }),
  ArrowButton: (p) =>
    jsx("button", {
      type: "button",
      disabled: p.disabled,
      onClick: p.onClick,
      "aria-label": p["aria-label"],
      "data-search-strip-arrow": p["data-search-strip-arrow"],
      children: p.children,
    }),
  SegmentedControl: (p) =>
    jsx("div", {
      role: "tablist",
      "aria-label": p["aria-label"],
      children: p.options.map((o) =>
        jsx(
          "button",
          {
            type: "button",
            role: "tab",
            disabled: o.disabled,
            "aria-selected": p.value === o.value,
            onClick: () => p.onValueChange(o.value),
            children: o.label,
          },
          o.value,
        ),
      ),
    }),
  Link: ({ href, onClick, children, ...p }) =>
    jsx("a", {
      href,
      "aria-label": p["aria-label"],
      "data-search-tile": p["data-search-tile"],
      className: p.className,
      onClick: (e) => {
        e.preventDefault();
        onClick?.(e);
        events.push({ type: "host-link", href });
      },
      children: children ?? "supplied profile link",
    }),
  ProfileDisplay: (p) => {
    records.profileDisplay.push(p);
    return jsx("div", {
      "data-testid": "profile-display",
      "data-address": p.address,
      "data-decoration": p.avatarDecoration ?? "none",
      children: p.nameOverride,
    });
  },
  CoinAvatar: (p) =>
    jsx("span", {
      "data-testid": "coin-avatar",
      "data-mint": p.coin.mint,
      children: "avatar",
    }),
  CoinName: (p) => jsx("span", { children: p.coin.name }),
  Sparkline: (p) => {
    records.sparkline.push({
      data: p.data,
      error: p.error,
      isLoading: p.isLoading,
    });
    return jsx("span", {
      "data-testid": "sparkline",
      children: p.isLoading ? "loading" : p.error ? "error" : "provided-chart",
    });
  },
};
const tones = (value, threshold) => {
  records.formats.push({ kind: "tone", value, threshold });
  return "supplied-tone";
};
const caps = (value) => {
  records.formats.push({ kind: "cap", value });
  return "cap:" + value;
};
const ports = {
  React,
  jsxRuntime,
  memoCache: c,
  renderers,
  browserWindow,
  MutationObserver: TrackedMutationObserver,
  ResizeObserver: TrackedResizeObserver,
  avatarSize: 28,
  useTranslation: () => ({ t: (key) => key }),
  useFlag: (key) => {
    const s = read();
    events.push({ type: "flag", key });
    return s.decorationEnabled;
  },
  useProfile: (options) => {
    const s = read();
    records.profiles.push(options);
    return { data: s.profileData };
  },
  pnlTone: tones,
  formatPnlUsd: (value) => "usd:" + value,
  formatPnlPercent: (value) => "percent:" + value,
  formatMarketCap: caps,
  classNames: (...v) => v.filter(Boolean).join(" "),
  useLiveMarketCap: (options) => {
    const s = read();
    records.liveCaps.push(options);
    return s.liveCap;
  },
  useCoinImpression: (...args) => {
    records.coinImpressions.push(args);
    return undefined;
  },
  useCoinClickHandlers: () => ({
    handleCoinClick: (mint, props) =>
      events.push({ type: "coin-click", mint, props }),
  }),
  useImpressionContext: () => ({
    setLastClickImpression: (mint, props) =>
      events.push({ type: "last-impression", mint, props }),
  }),
  useCandlesticks: (...args) => {
    const s = read();
    records.charts.push(args);
    return {
      candlesticks: s.chartData,
      error: s.chartError ? Error("Synthetic supplied chart error") : null,
      isLoading: s.chartLoading,
    };
  },
  cleanSymbol: (value) => "clean:" + value,
  usePrefetch: (coin) => {
    records.prefetch.push(coin.mint);
    return {
      prefetch: false,
      hoverProps: { "data-supplied-hover": coin.mint },
    };
  },
};
const { DiscoverStrip } = createSearchIdleStrip(ports),
  { DiscoverStrip: WithoutResize } = createSearchIdleStrip({
    ...ports,
    ResizeObserver: undefined,
  });
const initial = {
  coins: [],
  traders: [],
  coinLoading: true,
  traderLoading: false,
  decorationEnabled: false,
  profileData: undefined,
  liveCap: undefined,
  chartData: [{ t: 1, v: 2 }],
  chartError: null,
  chartLoading: false,
  callbackB: false,
  readFails: false,
  writeFails: false,
  reducedMotion: false,
  modeNoResize: false,
  epoch: 0,
  width: 360,
};
function Host() {
  const [s, set] = useState(initial);
  current = s;
  serial++;
  patch = (p) => set((old) => ({ ...old, ...p }));
  const Component = s.modeNoResize ? WithoutResize : DiscoverStrip;
  return jsxs(Scope.Provider, {
    value: s,
    children: [
      jsx("style", {
        children: `.overflow-x-auto{display:flex;width:${s.width}px;overflow-x:auto;gap:12px}.overflow-x-auto>div,.overflow-x-auto>a{box-sizing:border-box;flex:0 0 170px;width:170px;min-height:100px}.overflow-x-auto>div[data-search-tile]{position:relative}.absolute{position:absolute;inset:0}header{display:flex;gap:20px}body{font:14px sans-serif}`,
      }),
      jsx(
        Component,
        {
          topTraders: s.traders,
          topTradersLoading: s.traderLoading,
          trendingCoins: s.coins,
          trendingLoading: s.coinLoading,
          onNavigate: s.callbackB ? navigateB : navigateA,
        },
        s.epoch,
      ),
    ],
  });
}
window.idleStripHarness = {
  patch: (p) => patch(p),
  serial: () => serial,
  load: () =>
    patch({
      coins: coinRows,
      traders,
      coinLoading: false,
      traderLoading: false,
    }),
  events: () => events,
  records: () => records,
  state: () => ({
    coinCount: current.coins.length,
    traderCount: current.traders.length,
    storageValue,
    width: current.width,
  }),
  resetStorage: (value) => {
    storageValue = value;
  },
  unmount: () => root.unmount(),
};
root = createRoot(document.getElementById("root"));
root.render(jsx(Host, {}));
