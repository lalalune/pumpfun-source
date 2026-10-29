// Authored synthetic host for the complete reconstructed hook. This is not an app route.
import * as React from "react";
import { createRoot } from "react-dom/client";
import { c as useMemoCache } from "react/compiler-runtime";
import {
  createHomeFeedRead,
  normalizerVariants,
  helperContexts,
} from "../client.mjs";

let revision = 0,
  instance = 0,
  input = {
    args: {},
    seed: null,
    query: { data: undefined, isPending: false, isError: false },
  };
const subscribers = new Set(),
  intervals = new Map();
let serial = 0,
  cleared = 0,
  options,
  last;
function emit(change) {
  input = { ...input, ...change, revision: ++revision };
  for (const fn of subscribers) fn();
}
const timers = {
  setInterval(callback, delay) {
    const token = { id: ++serial },
      record = { callback, delay, mode: input.timerMode ?? "manual" };
    if (record.mode === "real")
      record.native = window.setInterval(callback, delay);
    intervals.set(token, record);
    return token;
  },
  clearInterval(token) {
    const record = intervals.get(token);
    if (record?.native !== undefined) window.clearInterval(record.native);
    intervals.delete(token);
    cleared++;
  },
};
const boundary = createHomeFeedRead({
  normalizerVariant: normalizerVariants[0].sha256,
  helperContext: helperContexts[0],
  React,
  useMemoCache,
  useQuery: (value) => {
    options = value;
    return input.query;
  },
  useHomeFeedSeed: () => input.seed,
  fetchHomeFeed: () => {
    throw Error(
      "This browser host supplies synthetic query snapshots; no service request",
    );
  },
  decodeBase58: () => new Uint8Array(32),
  timers,
});
const element = React.createElement,
  root = createRoot(document.getElementById("root"));
function Host() {
  const state = React.useSyncExternalStore(
    (fn) => {
      subscribers.add(fn);
      return () => subscribers.delete(fn);
    },
    () => input,
    () => input,
  );
  const feed = boundary.useHomeFeed(state.args);
  React.useEffect(() => {
    last = { revision: state.revision, feed };
  });
  return element(
    "main",
    null,
    element("h1", null, "Synthetic source-bound Home read-state host"),
    element(
      "p",
      null,
      "Injected query/seed/codec ports; no website UI or service compatibility claim.",
    ),
    element("button", { onClick: () => feed.fetchNextPage() }, "Fetch next"),
    element("button", { onClick: () => feed.showNewCallouts() }, "Show new"),
    element(
      "button",
      { onClick: () => step(100) },
      "Step 100 artificial timer callbacks",
    ),
    element(
      "output",
      { "data-testid": "pending" },
      String(feed.pendingNewCount),
    ),
    element("output", { "data-testid": "error" }, feed.error ?? ""),
    element(
      "ol",
      null,
      ...feed.callouts.map((row) =>
        element(
          "li",
          { key: row.key, "data-key": row.key },
          row.coinSymbol ?? "",
        ),
      ),
    ),
  );
}
function render() {
  root.render(element(Host, { key: instance }));
}
function step(count) {
  for (let i = 0; i < count; i++)
    for (const record of [...intervals.values()])
      if (record.mode === "manual") record.callback();
}
function makeRows(prefix, count) {
  return Array.from({ length: count }, (_, i) => ({
    coinMint: `${prefix}-mint-${i}`,
    chain: "solana",
    symbol: `${prefix}-${i}`,
    position: {
      userId: `${prefix}-author-${i}`,
      walletAddress: `${prefix}-wallet-${i}`,
      callout: {
        calloutId: `${prefix}-${i}`,
        thesis: `${prefix} note`,
        calloutTimestamp: "2026-10-28T00:00:00Z",
      },
    },
  }));
}
window.harness = {
  makeRows,
  reset(value) {
    input = {
      args: {},
      seed: null,
      query: { data: undefined, isPending: false, isError: false },
      ...value,
      revision: ++revision,
    };
    last = undefined;
    instance++;
    render();
    return revision;
  },
  update(value) {
    emit(value);
    return revision;
  },
  identity(phase) {
    const coins = input.query.data.coins;
    let next = coins;
    if (phase === 1) coins[0].symbol = "MUTATED";
    if (phase === 2) next = [...coins];
    if (phase === 3) next = [{ ...coins[0] }, ...coins.slice(1)];
    emit({ query: { ...input.query, data: { coins: next } } });
    return revision;
  },
  step,
  unmount() {
    root.render(null);
  },
  observe() {
    const f = last?.feed;
    return {
      revision,
      lastRevision: last?.revision,
      keys: f?.callouts.map((x) => x.key) ?? [],
      symbols: f?.callouts.map((x) => x.coinSymbol) ?? [],
      pending: f?.pendingNewCount,
      preview: f?.pendingPreview,
      hasNextPage: f?.hasNextPage,
      hasUnseen: f?.hasUnseen,
      loading: f?.isLoadingHistory,
      error: f?.error,
      fetching: f?.isFetchingNextPage,
      options: options
        ? {
            queryKey: options.queryKey,
            enabled: options.enabled,
            staleTime: options.staleTime,
            retry: options.retry,
            refetchOnWindowFocus: options.refetchOnWindowFocus,
            refetchInterval: options.refetchInterval,
            refetchIntervalInBackground: options.refetchIntervalInBackground,
            hasPlaceholder: options.placeholderData !== undefined,
          }
        : null,
      intervals: [...intervals.values()].map((x) => ({
        delay: x.delay,
        mode: x.mode,
      })),
      cleared,
    };
  },
};
render();
