import React from "react";
import { createRoot } from "react-dom/client";
import { flushSync } from "react-dom";
import bs58 from "bs58";
import {
  createFollowingFeedRead,
  readContexts,
  imageVariants,
  classificationVariants,
} from "../client.mjs";
import { createNormalizerHelpers, helperVariants } from "./helper-ports.mjs";
const el = React.createElement,
  check = (v, label) => {
    if (!v) throw Error(label);
  },
  same = (a, b, label) =>
    check(
      JSON.stringify(a) === JSON.stringify(b),
      label + ": " + JSON.stringify(a),
    );
const mint = "11111111111111111111111111111111";
const wire = (id, extra = {}) => ({
  kind: "callout",
  coinMint: mint,
  walletAddress: "author",
  createdAt: "2026-01-02",
  callout: {
    calloutId: id,
    calloutTimestamp: "2026-01-01",
    thesis: " note ",
    updates: [],
  },
  ...extra,
});
const data = (...pages) => ({
  pages: pages.map((items) => ({ items, nextCursor: null })),
  pageParams: pages.map((_, i) => (i ? String(i) : undefined)),
});
let active, root;
async function until(fn) {
  const start = performance.now();
  while (!fn()) {
    check(performance.now() - start < 3000, "finite React condition timeout");
    await new Promise((r) => setTimeout(r, 5));
  }
}
function deferred() {
  let resolve;
  const promise = new Promise((r) => (resolve = r));
  return { promise, resolve };
}
function close() {
  if (root) {
    flushSync(() => root.unmount());
    root = null;
  }
  return {
    queryListeners: active
      ? [...active.cells.values()].reduce((n, c) => n + c.listeners.size, 0)
      : 0,
    eventListeners: active?.events.size ?? 0,
    rootChildren: document.getElementById("root").childElementCount,
  };
}
// These are explicit finite qualification capabilities, not implementations of TanStack,
// the captured presence hook, viewport observer, Zod, telemetry or a personalized service.
function mount(
  context,
  {
    input = { viewer: "synthetic-viewer", chain: "near" },
    initial,
    auto = true,
    reader = async () => ({ items: [], nextCursor: null }),
  } = {},
) {
  if (root)
    same(
      close(),
      { queryListeners: 0, eventListeners: 0, rootChildren: 0 },
      "prior cleanup",
    );
  const s = {
    input,
    initial,
    auto,
    reader,
    cells: new Map(),
    events: new Set(),
    observations: [],
    metrics: [],
    calls: [],
    requests: [],
    schemaCalls: [],
    now: 1000000,
    out: null,
    invalidate: () => Promise.resolve(),
    renders: 0,
  };
  active = s;
  const publish = (cell, patch) => {
    cell.snapshot = { ...cell.snapshot, ...patch };
    for (const f of cell.listeners) f();
  };
  const cache = {
    getQueryData(key) {
      s.calls.push(["get", key]);
      return s.cells.get(JSON.stringify(key))?.snapshot.data;
    },
    setQueryData(key, value) {
      s.calls.push(["set", key]);
      const cell = s.cells.get(JSON.stringify(key));
      check(cell, "known cache key");
      publish(cell, { data: value });
    },
    invalidateQueries(options) {
      s.calls.push(["invalidate", options]);
      return s.invalidate(options);
    },
  };
  function useInfiniteQuery(options) {
    const key = JSON.stringify(options.queryKey);
    let cell = s.cells.get(key);
    if (!cell) {
      cell = {
        listeners: new Set(),
        started: false,
        snapshot: {
          data: s.cells.size === 0 ? s.initial : undefined,
          isPending: false,
          isError: false,
          hasNextPage: false,
          isFetchingNextPage: false,
        },
        options,
      };
      s.cells.set(key, cell);
      cell.load = async (next = false) => {
        cell.started = true;
        publish(
          cell,
          next
            ? { isFetchingNextPage: true }
            : { isPending: true, isError: false },
        );
        try {
          const prior = cell.snapshot.data,
            param = next
              ? cell.options.getNextPageParam(
                  prior.pages.at(-1),
                  prior.pages,
                  prior.pageParams.at(-1),
                )
              : cell.options.initialPageParam;
          const page = await cell.options.queryFn({
            pageParam: param,
            signal: new AbortController().signal,
          });
          const value = next
            ? {
                pages: [...prior.pages, page],
                pageParams: [...prior.pageParams, param],
              }
            : { pages: [page], pageParams: [param] };
          const last = value.pages.at(-1);
          publish(cell, {
            data: value,
            isPending: false,
            isError: false,
            isFetchingNextPage: false,
            hasNextPage:
              cell.options.getNextPageParam(
                last,
                value.pages,
                value.pageParams.at(-1),
              ) !== undefined,
          });
          return value;
        } catch (error) {
          publish(cell, {
            isPending: false,
            isError: true,
            isFetchingNextPage: false,
          });
          throw error;
        }
      };
    }
    cell.options = options;
    s.cell = cell;
    s.options = options;
    const subscribe = React.useCallback(
      (fn) => {
        cell.listeners.add(fn);
        return () => cell.listeners.delete(fn);
      },
      [cell],
    );
    const snapshot = React.useSyncExternalStore(
      subscribe,
      () => cell.snapshot,
      () => cell.snapshot,
    );
    React.useEffect(() => {
      if (
        options.enabled &&
        s.auto &&
        !cell.started &&
        cell.snapshot.data === undefined
      )
        void cell.load().catch(() => {});
    }, [cell, options.enabled]);
    return {
      ...snapshot,
      fetchNextPage() {
        s.calls.push(["next", this.hasNextPage]);
        void cell.load(true).catch(() => {});
      },
    };
  }
  function useFollowingEvents(options) {
    s.eventOptions = options;
    React.useEffect(() => {
      if (!options.enabled) return;
      const listener = (event) => options.onNewContent(event);
      s.events.add(listener);
      return () => s.events.delete(listener);
    }, [options.enabled, options.viewer, options.onNewContent]);
  }
  const api = createFollowingFeedRead({
    readContext: context.reader,
    imageVariant: imageVariants[0].sha256,
    classificationVariant: classificationVariants[0].sha256,
    React,
    useInfiniteQuery,
    useQueryClient: () => cache,
    getContractClient: () => async (operation, options) => {
      s.requests.push({
        operation,
        query: options.query,
        credentials: options.credentials,
        headers: options.headers,
        signal: options.signal instanceof AbortSignal,
      });
      return s.reader(options);
    },
    kindsSchema: {
      parse(values) {
        s.schemaCalls.push([...values]);
        return values;
      },
    },
    useFollowingEvents,
    useFirstRowsObserver: (o) => s.observations.push(o),
    recordRefresh: (o) => s.metrics.push(o),
    normalizerHelpers: createNormalizerHelpers(helperVariants[0].sha256),
    decodeBase58: bs58.decode,
    clock: { now: () => s.now },
  });
  function App() {
    s.out = api.useFollowingFeed(s.input);
    s.renders++;
    return el(
      "section",
      null,
      el(
        "output",
        { "data-testid": "rows" },
        s.out.rows.map((r) => r.key).join(","),
      ),
      el("output", { "data-testid": "pending" }, s.out.pendingNewCount),
      el("button", { onClick: () => s.out.fetchNextPage() }, "More"),
      el("button", { onClick: () => s.out.showNewCallouts() }, "Show new"),
    );
  }
  s.render = (input) => {
    if (input) s.input = input;
    flushSync(() => root.render(el(App)));
  };
  s.emit = (event) =>
    flushSync(() => {
      for (const listener of [...s.events]) listener(event);
    });
  s.put = (value) =>
    flushSync(() => cache.setQueryData(s.options.queryKey, value));
  s.patch = (patch) => flushSync(() => publish(s.cell, patch));
  root = createRoot(document.getElementById("root"));
  s.render();
  return s;
}
async function pagination(context) {
  const first = deferred(),
    next = deferred();
  let call = 0;
  const s = mount(context, {
    reader: () => (++call === 1 ? first.promise : next.promise),
  });
  await until(() => s.requests.length === 1);
  check(s.out.isLoadingHistory, "pending first read");
  first.resolve({
    items: [
      wire("duplicate", { chain: "ton:-239" }),
      wire("visible", { chain: "near:mainnet" }),
      { kind: "unknown" },
    ],
    nextCursor: "cursor",
  });
  await until(() => s.out.rows.length === 1);
  same(
    s.out.rows.map((r) => r.key),
    ["cid:visible"],
    "first page filtered",
  );
  same(
    s.requests[0].query.kinds,
    ["callout", "update", "reply", "quote", "repost"],
    "classic query kinds",
  );
  same(s.requests[0].query.chains, ["near:mainnet"], "chain query");
  check(s.out.hasNextPage, "next cursor");
  flushSync(() => s.out.fetchNextPage());
  await until(() => s.requests.length === 2);
  check(s.out.isFetchingNextPage, "next pending");
  s.out.fetchNextPage();
  check(s.requests.length === 2, "fetch guard");
  next.resolve({
    items: [
      wire("duplicate", { chain: "near:mainnet" }),
      wire("last", { chain: "near:mainnet" }),
    ],
    nextCursor: "cursor",
  });
  await until(() => s.out.rows.length === 2);
  same(
    s.out.rows.map((r) => r.key),
    ["cid:visible", "cid:last"],
    "dedup precedes chain filter",
  );
  check(!s.out.hasNextPage, "repeated previous cursor ends");
  s.out.fetchNextPage();
  check(s.requests.length === 2, "no cursor guard");
  check(
    s.requests.every((r) => r.credentials === "include" && r.signal),
    "exact source options",
  );
  same(s.observations.at(-1).itemCount, 2, "observer row count");
  return {
    rows: s.out.rows.map((r) => r.key),
    requests: s.requests.map((r) => ({
      operation: r.operation,
      query: r.query,
      credentials: r.credentials,
      signal: r.signal,
    })),
    nextCalls: s.calls.filter((c) => c[0] === "next").length,
  };
}
async function pending(context) {
  const s = mount(context, {
    input: { viewer: "v", chain: "all", bufferNewCallouts: true },
    initial: data([wire("old")], [wire("second")]),
    auto: false,
  });
  const promise = deferred();
  s.invalidate = () => promise.promise;
  for (const event of [
    { id: "null", coinMint: null },
    { id: "a", coinMint: mint, receivedAtMs: 998000 },
    { id: "undefined" },
    { id: "c", coinMint: "c" },
    { id: "d", coinMint: "d" },
  ])
    s.emit(event);
  s.emit({ id: "a", coinMint: "ignored" });
  check(s.out.pendingNewCount === 5, "pending raw id dedup");
  same(
    s.out.pendingPreview.map((x) => x.key),
    ["evt:a", "evt:undefined", "evt:c"],
    "null only skip and preview3",
  );
  s.render({ ...s.input, pageSize: 3 });
  check(s.out.pendingNewCount === 5, "pageSize preserves pending");
  s.put(data([wire("old")], [wire("second")]));
  const start = s.calls.length;
  let returned;
  flushSync(() => {
    returned = s.out.showNewCallouts({ trigger: "auto" });
  });
  check(returned === undefined, "source callback does not return Promise");
  check(s.out.pendingNewCount === 0, "cleared before await");
  same(
    s.calls.slice(start).map((c) => c[0]),
    ["get", "set", "invalidate"],
    "trim ordering",
  );
  check(s.cell.snapshot.data.pages.length === 1, "first page only");
  same(s.metrics, [], "no metric before invalidation");
  s.now = 1000500;
  promise.resolve();
  await until(() => s.metrics.length === 1);
  same(
    s.metrics[0],
    {
      surface: "classic-tab",
      path: "auto-revealed",
      receiptToPaintMs: 2500,
      pagesRefetched: 1,
      count: 5,
    },
    "awaited Q payload at synthetic time",
  );
  s.emit({ id: "new", coinMint: mint });
  check(s.out.pendingNewCount === 1, "enqueue again");
  s.render({ ...s.input, viewer: "other" });
  check(s.out.pendingNewCount === 0, "viewer resets pending");
  s.put(data([wire("other")]));
  s.emit({ id: "chain", coinMint: mint });
  check(s.out.pendingNewCount === 1, "viewer new cache");
  s.render({ ...s.input, chain: "near" });
  check(s.out.pendingNewCount === 0, "chain resets pending");
  return {
    previewCap: 3,
    count: 5,
    order: s.calls.slice(start, start + 3).map((c) => c[0]),
    metric: s.metrics[0],
    reset: "viewer+chain; pageSize retained",
  };
}
async function errorsAndThrottle(context) {
  const failure = deferred(),
    s = mount(context, {
      reader: () => failure.promise,
      input: { viewer: null, bufferNewCallouts: true },
    });
  check(
    s.requests.length === 0 && !s.out.isLoadingHistory && s.events.size === 0,
    "null viewer disabled",
  );
  s.render({ ...s.input, viewer: undefined });
  await until(() => s.requests.length === 1);
  check(
    s.out.isLoadingHistory && s.events.size === 1,
    "undefined viewer admitted by literal null-only gate",
  );
  failure.resolve(Promise.reject(new Error("synthetic read failure")));
  await until(() => s.out.error !== null);
  same(
    s.out.error,
    "Could not load your following feed",
    "read error with undefined data",
  );
  s.put(data([]));
  check(s.out.error === null, "cached empty data suppresses error");
  s.emit({ id: "a", coinMint: mint });
  s.emit({ id: "b", coinMint: mint });
  s.now = 1004999;
  s.emit({ id: "c", coinMint: mint });
  check(
    s.calls.filter((c) => c[0] === "invalidate").length === 1,
    "5s throttle before boundary",
  );
  s.now = 1005000;
  s.emit({ id: "d", coinMint: mint });
  check(
    s.calls.filter((c) => c[0] === "invalidate").length === 2,
    "5s inclusive boundary",
  );
  check(s.out.pendingNewCount === 0, "empty cache does not buffer");
  same(
    s.metrics,
    [
      { surface: "classic-tab", path: "empty-refetch" },
      { surface: "classic-tab", path: "empty-refetch" },
    ],
    "empty metrics",
  );
  s.put(data([wire("cached")]));
  s.render({ ...s.input, bufferNewCallouts: false });
  s.now = 1010000;
  s.emit({ id: "not-buffered", coinMint: mint });
  check(
    s.calls.filter((c) => c[0] === "invalidate").length === 3,
    "nonbuffered invalidation",
  );
  check(s.metrics.length === 2, "nonempty no empty metric");
  return {
    requests: 1,
    errorSuppressedByCachedData: true,
    invalidationCount: 3,
    manualTimeSteps: [1000000, 1004999, 1005000, 1010000],
    metrics: s.metrics,
  };
}
const cases = new Map();
for (const context of readContexts) {
  const suffix = context.reader.slice(0, 12);
  cases.set("pagination-" + suffix, () => pagination(context));
  cases.set("pending-reveal-" + suffix, () => pending(context));
  cases.set("error-throttle-" + suffix, () => errorsAndThrottle(context));
}
window.followingFixture = {
  names: [...cases.keys()],
  async run(name) {
    check(cases.has(name), "known case");
    return cases.get(name)();
  },
  cleanup: close,
};
