import React from "react";
import { c as useMemoCache } from "react/compiler-runtime";
import { createRoot } from "react-dom/client";
import { flushSync } from "react-dom";
import bs58 from "bs58";
import {
  createTopFeedRead,
  ownerVariants,
  readContexts,
  toFeedRows,
} from "../client.mjs";
import { createHelperPorts, helperVariants } from "./helper-ports.mjs";
const el = React.createElement,
  check = (v, l) => {
    if (!v) throw Error(l);
  },
  same = (a, b, l) =>
    check(
      JSON.stringify(a) === JSON.stringify(b),
      l + ": " + JSON.stringify(a),
    ),
  mint = "11111111111111111111111111111111";
const wire = (id, extra = {}) => ({
  coinMint: mint,
  walletAddress: "author",
  username: "Alice",
  callout: {
    calloutId: id,
    thesis: " note ",
    calloutTimestamp: "2026-01-01",
    updates: [],
  },
  ...extra,
});
let root, active;
function deferred() {
  let resolve;
  const promise = new Promise((r) => (resolve = r));
  return { promise, resolve };
}
async function until(fn) {
  const t = performance.now();
  while (!fn()) {
    check(performance.now() - t < 3000, "finite React wait");
    await new Promise((r) => setTimeout(r, 5));
  }
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
    rootChildren: document.getElementById("root").childElementCount,
  };
}
// Finite injected query/cache lifecycle: not a TanStack replacement or original endpoint.
function mount(
  index,
  { input, initial, reader = async () => ({ entries: [] }) } = {},
) {
  if (root)
    same(close(), { queryListeners: 0, rootChildren: 0 }, "prior cleanup");
  const s = {
    input,
    initial,
    reader,
    cells: new Map(),
    requests: [],
    prefetches: [],
    out: null,
    renders: 0,
  };
  active = s;
  function useQuery(options) {
    const key = JSON.stringify(options.queryKey);
    let cell = s.cells.get(key);
    if (!cell) {
      cell = {
        listeners: new Set(),
        started: false,
        options,
        snapshot: {
          data: s.cells.size === 0 ? s.initial : undefined,
          isPending: false,
          isError: false,
        },
      };
      cell.publish = (patch) => {
        cell.snapshot = { ...cell.snapshot, ...patch };
        for (const f of cell.listeners) f();
      };
      cell.refetch = async () => {
        cell.started = true;
        cell.publish({ isPending: true });
        try {
          const data = await cell.options.queryFn({
            signal: new AbortController().signal,
          });
          cell.publish({ data, isPending: false, isError: false });
          return { data };
        } catch (error) {
          cell.publish({ isPending: false, isError: true });
          return { error };
        }
      };
      s.cells.set(key, cell);
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
      ),
      snapshot = React.useSyncExternalStore(
        subscribe,
        () => cell.snapshot,
        () => cell.snapshot,
      );
    React.useEffect(() => {
      if (options.enabled && !cell.started && cell.snapshot.data === undefined)
        void cell.refetch();
    }, [cell, options.enabled]);
    return { ...snapshot, refetch: cell.refetch };
  }
  s.api = createTopFeedRead({
    ownerVariant: ownerVariants[index].sha256,
    readContext: readContexts[index].reader,
    useMemoCache,
    useQuery,
    getContractClient: () => async (operation, options) => {
      s.requests.push({
        operation,
        query: options.query,
        credentials: options.credentials,
        headers: options.headers,
        hasSignal: options.signal instanceof AbortSignal,
      });
      return s.reader(options);
    },
    ...createHelperPorts(helperVariants[0].normalizer),
    decodeBase58: bs58.decode,
  });
  function App() {
    s.out = s.api.useTopFeed(s.input);
    s.renders++;
    const rows = toFeedRows(s.out.callouts);
    return el(
      "section",
      null,
      el("output", { "data-testid": "rows" }, rows.map((r) => r.key).join(",")),
      el("output", { "data-testid": "error" }, s.out.error ?? ""),
      el("button", { onClick: s.out.refetch }, "Refresh"),
    );
  }
  s.render = (input) => {
    s.input = input;
    flushSync(() => root.render(el(App)));
  };
  s.patch = (patch) => flushSync(() => s.cell.publish(patch));
  s.prefetch = (input) =>
    s.api.prefetchTopFeed(
      {
        prefetchQuery(options) {
          s.prefetches.push(options);
          return options.queryFn({ signal: new AbortController().signal });
        },
      },
      input,
    );
  root = createRoot(document.getElementById("root"));
  s.render(input);
  return s;
}
async function mapping(index) {
  const pending = deferred(),
    s = mount(index, { reader: () => pending.promise });
  await until(() => s.requests.length === 1);
  check(s.out.isLoadingHistory, "initial pending");
  pending.resolve({
    entries: [
      wire("invalid", { coinMint: "bad" }),
      wire("first", {
        followedHolders: {
          holders: [{ username: "ALICE" }, { username: "Other" }],
          totalCount: 2,
        },
      }),
      wire("first", { username: "ignored" }),
      wire("last"),
    ],
    totalRanked: 4,
  });
  await until(() => s.out.callouts.length === 2);
  same(
    s.out.callouts.map((r) => r.key),
    ["cid:first", "cid:last"],
    "valid first key/order",
  );
  same(
    s.out.callouts[0].followedHolders,
    { holders: [{ username: "Other" }], totalCount: 1 },
    "exclude author by username",
  );
  same(s.requests[0].query, { period: "daily" }, "daily read");
  check(
    s.requests[0].credentials === "include" && s.requests[0].hasSignal,
    "exact source options",
  );
  check(
    document.querySelector("[data-testid=rows]").textContent ===
      "cid:first,cid:last",
    "rendered row handoff",
  );
  check(!s.out.hasNextPage && s.out.pendingNewCount === 0, "nonpaged result");
  return {
    rows: s.out.callouts.map((r) => r.key),
    request: s.requests[0],
    authorExcluded: true,
  };
}
async function optionsAndPrefetch(index) {
  const s = mount(index, {
    input: { enabled: false },
    reader: async (o) => ({ entries: [wire(o.query.period)] }),
  });
  check(
    s.requests.length === 0 && !s.out.isLoadingHistory,
    "disabled initial observer",
  );
  s.render({ enabled: true, period: "weekly", includeFollowedHolders: true });
  await until(() => s.out.callouts.length === 1);
  same(
    s.options.queryKey,
    ["callouts", "top-feed", "weekly", true],
    "weekly partition",
  );
  same(
    s.requests[0].query,
    { period: "weekly", includeFollowedHolders: true, followedHoldersLimit: 5 },
    "facepile limit",
  );
  check(
    s.options.refetchOnWindowFocus === true &&
      s.options.staleTime === 300000 &&
      s.options.retry === 3,
    "query policies",
  );
  const prefetched = await s.prefetch({
    includeFollowedHolders: true,
    period: "weekly",
  });
  same(
    s.prefetches[0].queryKey,
    ["callouts", "top-feed", "daily", true],
    "prefetch hardcodes daily",
  );
  same(
    s.requests[1].query,
    { period: "daily", includeFollowedHolders: true, followedHoldersLimit: 5 },
    "actual prefetch request",
  );
  check(prefetched.entries[0].callout.calloutId === "daily", "prefetch result");
  return {
    partitions: [s.options.queryKey, s.prefetches[0].queryKey],
    requests: s.requests.map((r) => r.query),
    policy: {
      focus: s.options.refetchOnWindowFocus,
      stale: s.options.staleTime,
      retry: s.options.retry,
    },
  };
}
async function errorRefetchMemo(index) {
  let fail = true;
  const s = mount(index, {
    reader: async () => {
      if (fail) throw Error("synthetic read rejection");
      return { entries: [wire("valid")] };
    },
  });
  await until(() => s.out.error !== null);
  same(s.out.error, "Could not load top callouts", "empty mapped error");
  fail = false;
  let returned;
  flushSync(() => {
    returned = s.out.refetch();
  });
  check(returned === undefined, "original refetch discards Promise");
  await until(() => s.out.callouts.length === 1);
  check(s.out.error === null, "successful refetch clears");
  const entries = s.cell.snapshot.data.entries,
    first = s.out.callouts;
  entries.push(wire("later"));
  s.patch({ data: { entries } });
  check(
    s.out.callouts === first && s.out.callouts.length === 1,
    "entries identity memo retained",
  );
  s.patch({ data: { entries: [...entries] } });
  check(s.out.callouts.length === 2, "immutable array updates");
  s.patch({ isError: true });
  check(s.out.error === null, "cached mapped rows suppress error");
  s.patch({ data: { entries: [wire("bad", { callout: null })] } });
  same(
    s.out.error,
    "Could not load top callouts",
    "invalid mapped entries expose error",
  );
  check(
    s.out.fetchNextPage() === undefined &&
      s.out.showNewCallouts() === undefined,
    "shared source noop result fields",
  );
  return {
    requests: s.requests.length,
    refetchReturn: "undefined",
    sameArrayMutationIgnored: true,
    newArrayObserved: true,
    errorAfterInvalidRows: s.out.error,
  };
}
const cases = new Map();
for (let i = 0; i < ownerVariants.length; i++) {
  const suffix = ownerVariants[i].sha256.slice(0, 12);
  cases.set("mapping-" + suffix, () => mapping(i));
  cases.set("options-prefetch-" + suffix, () => optionsAndPrefetch(i));
  cases.set("error-refetch-memo-" + suffix, () => errorRefetchMemo(i));
}
window.topFixture = {
  names: [...cases.keys()],
  run(name) {
    check(cases.has(name), "known case");
    return cases.get(name)();
  },
  cleanup: close,
};
