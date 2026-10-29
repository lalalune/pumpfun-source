import React from "react";
import { c as useMemoCache } from "react/compiler-runtime";
import { createRoot } from "react-dom/client";
import { flushSync } from "react-dom";
import { createCoinQuery } from "../client.mjs";
import { queryClientPort } from "./ports.mjs";
const el = React.createElement,
  coin = (mint, extra = {}) => ({ mint, chain_id: "solana", ...extra });
const check = (condition, label) => {
  if (!condition) throw Error(label);
};
const same = (a, b, label) =>
  check(
    JSON.stringify(a) === JSON.stringify(b),
    label + ": " + JSON.stringify(a),
  );
let active, root;
async function until(fn) {
  const start = performance.now();
  while (!fn()) {
    if (performance.now() - start > 3000)
      throw Error("finite React condition timeout");
    await new Promise((r) => setTimeout(r, 5));
  }
}
function deferred() {
  let resolve, reject;
  const promise = new Promise((a, b) => {
    resolve = a;
    reject = b;
  });
  return { promise, resolve, reject };
}
function mount({
  mints,
  options = {},
  cache = [],
  now = 100000,
  reader = async () => [],
} = {}) {
  if (root) {
    flushSync(() => root.unmount());
    check(
      [...active.cells.values()].every((c) => c.listeners.size === 0),
      "observer subscriptions removed",
    );
  }
  const client = queryClientPort();
  for (const [key, value, at] of cache) client.put(key, value, at);
  const state = {
    mints,
    options,
    now,
    client,
    cells: new Map(),
    calls: [],
    factoryCalls: 0,
    snapshots: [],
    reader,
    out: null,
    bump: null,
  };
  active = state;
  function useQuery(o) {
    const key = JSON.stringify(o.queryKey);
    let cell = state.cells.get(key);
    if (!cell) {
      cell = {
        listeners: new Set(),
        started: false,
        options: o,
        snapshot: {
          data: undefined,
          error: null,
          isLoading: false,
          isError: false,
          isLoadingError: false,
        },
      };
      cell.refetch = async () => {
        cell.started = true;
        const set = (p) => {
          cell.snapshot = { ...cell.snapshot, ...p };
          for (const fn of cell.listeners) fn();
        };
        set({
          isLoading: true,
          error: null,
          isError: false,
          isLoadingError: false,
        });
        try {
          const data = await cell.options.queryFn();
          set({ data, isLoading: false });
          return data;
        } catch (error) {
          set({ error, isLoading: false, isError: true, isLoadingError: true });
          throw error;
        }
      };
      state.cells.set(key, cell);
    }
    cell.options = o;
    const subscribe = React.useCallback(
      (fn) => {
        cell.listeners.add(fn);
        return () => cell.listeners.delete(fn);
      },
      [cell],
    );
    const get = React.useCallback(() => cell.snapshot, [cell]);
    const snapshot = React.useSyncExternalStore(subscribe, get, get);
    React.useEffect(() => {
      if (o.enabled && !cell.started) void cell.refetch().catch(() => {});
    }, [cell, o.enabled]);
    state.lastOptions = o;
    return { ...snapshot, refetch: cell.refetch };
  }
  const api = createCoinQuery({
    useMemoCache,
    useQuery,
    useQueryClient: () => client,
    clock: { now: () => state.now },
    getContractClient: () => {
      state.factoryCalls++;
      return async (operation, options) => {
        state.calls.push({
          operation,
          body: options.body,
          credentials: options.credentials,
          keys: Object.keys(options).sort(),
        });
        return state.reader(operation, options);
      };
    },
  });
  function App() {
    const [, bump] = React.useReducer((n) => n + 1, 0);
    state.bump = bump;
    const out = api.useCoins(state.mints, state.options);
    state.out = out;
    const view = {
      rows: out.data.map((c) => ({ mint: c.mint, name: c.name ?? null })),
      loading: out.isLoading,
      success: out.isSuccess,
      error: out.error?.message ?? out.error ?? null,
    };
    state.snapshots.push(view);
    return el(
      "main",
      null,
      el("h1", null, "Injected coin query qualification"),
      el("output", { "data-testid": "state" }, JSON.stringify(view)),
      el(
        "button",
        { onClick: () => void out.refetch().catch(() => {}) },
        "Refetch",
      ),
      el("button", { onClick: () => bump() }, "Rerender"),
    );
  }
  root = createRoot(document.getElementById("root"));
  flushSync(() => root.render(el(App)));
  return state;
}
function rerender(s, changes = {}) {
  Object.assign(s, changes);
  flushSync(() => s.bump());
}
const observations = (s) => ({
  view: JSON.parse(document.querySelector("[data-testid=state]").textContent),
  calls: s.calls,
  queryKey: s.lastOptions.queryKey,
  writes: s.client.writes,
  observerCount: [...s.cells.values()].reduce(
    (n, c) => n + c.listeners.size,
    0,
  ),
  snapshots: s.snapshots,
});
window.coinFixture = {
  names: [
    "identity-cache-and-freshness",
    "deferred-reader-ordered-merge",
    "nsfw-bypass-request-body",
    "option-precedence-refetch",
    "raw-error-and-recovery",
    "canonical-fallback-disabled",
  ],
  async run(name) {
    if (name === "identity-cache-and-freshness") {
      const mints = ["a", "ton"],
        options = {},
        original = coin("a", { name: "old" }),
        ton = coin("ton", { chain_id: "ton:-239" });
      const s = mount({
        mints,
        options,
        cache: [
          [["coin", "a"], original, 100000],
          [["coin", "ton"], ton, -999999],
        ],
      });
      await until(() => s.out);
      check(s.calls.length === 0, "fresh and chain rows skip reader");
      const first = s.out;
      s.now = 999999;
      s.client.put(["coin", "a"], coin("a", { name: "new" }), 999999);
      rerender(s);
      check(s.out === first, "captured memo retains output on same identities");
      same(s.out.data, [original, ton], "memo output ignores cache mutation");
      rerender(s, { mints: [...mints] });
      same(
        s.out.data.map((c) => c.name ?? c.mint),
        ["new", "ton"],
        "new array observes new cache",
      );
      return observations(s);
    }
    if (name === "deferred-reader-ordered-merge") {
      const gate = deferred(),
        s = mount({
          mints: ["stale", "b", "fresh", "b"],
          cache: [
            [["coin", "stale"], coin("stale", { name: "stale" }), 0],
            [["coin", "fresh"], coin("fresh"), 100000],
          ],
          reader: () => gate.promise,
        });
      await until(() => s.calls.length === 1 && s.out.isLoading);
      same(
        s.calls[0].body,
        { mints: ["stale", "b", "b"] },
        "request order and duplicate mints",
      );
      same(
        s.lastOptions.queryKey,
        ["coinsByMints", "safe", "b", "b", "stale"],
        "separate sorted key",
      );
      same(
        s.out.data.map((c) => c.mint),
        ["stale", "fresh"],
        "pending retains stale/fresh",
      );
      gate.resolve([coin("b"), coin("stale", { name: "fetched" })]);
      await until(() => s.out.data.length === 4 && !s.out.isLoading);
      same(
        s.out.data.map((c) => c.mint),
        ["stale", "b", "fresh", "b"],
        "ordered duplicate merge",
      );
      check(s.out.data[0].name === "fetched", "fetched row supersedes stale");
      same(
        s.client.writes.map((x) => x[0]),
        [
          ["coin", "b"],
          ["coin", "stale"],
        ],
        "exact returned-mint writes",
      );
      return observations(s);
    }
    if (name === "nsfw-bypass-request-body") {
      const s = mount({
        mints: ["b", "a", "b"],
        options: { includeNsfw: true },
        cache: [[["coin", "a"], coin("a", { name: "cached" }), 100000]],
        reader: async () => [coin("a"), coin("b")],
      });
      await until(() => s.out.data.length === 3 && !s.out.isLoading);
      same(
        s.calls[0],
        {
          operation: "POST /coins-v2/mints",
          body: { mints: ["b", "a", "b"] },
          credentials: "include",
          keys: ["body", "credentials", "hooks"],
        },
        "captured reader options only",
      );
      same(
        s.lastOptions.queryKey,
        ["coinsByMints", "nsfw", "a", "b", "b"],
        "nsfw key",
      );
      check(s.client.reads.length === 0, "nsfw bypasses cache");
      return observations(s);
    }
    if (name === "option-precedence-refetch") {
      let count = 0;
      const s = mount({
        mints: ["a"],
        options: {
          limit: 1,
          offset: 7,
          sort: "x",
          order: "desc",
          queryKey: ["synthetic-override"],
          enabled: false,
          staleTime: 5,
          gcTime: 6,
          queryFn: async () => {
            count++;
            return [coin("a", { name: "override" })];
          },
        },
      });
      await until(() => s.out);
      same(s.lastOptions.queryKey, ["synthetic-override"], "last key override");
      check(
        s.lastOptions.staleTime === 5 && s.lastOptions.gcTime === 6,
        "last timing overrides",
      );
      check(s.calls.length === 0 && count === 0, "disabled auto fetch");
      await s.out.refetch();
      await until(() => s.out.data.length === 1);
      check(
        count === 1 && s.factoryCalls === 0,
        "forwarded refetch uses override queryFn",
      );
      check(
        !("limit" in s.lastOptions) && !("offset" in s.lastOptions),
        "unused pagination destructured",
      );
      return observations(s);
    }
    if (name === "raw-error-and-recovery") {
      const raw = { synthetic: "original query error" };
      let fail = true;
      const s = mount({
        mints: ["a"],
        reader: async () => {
          if (fail) throw raw;
          return [coin("a")];
        },
      });
      await until(() => s.out.error === raw);
      check(
        !s.out.isSuccess && s.out.isError && s.out.isLoadingError,
        "error flags propagate",
      );
      fail = false;
      await s.out.refetch();
      await until(() => s.out.data.length === 1 && !s.out.error);
      check(s.out.isSuccess, "recovery result");
      return observations(s);
    }
    if (name === "canonical-fallback-disabled") {
      const first = coin("0xAb", { name: "first" }),
        tie = coin("0xab", { name: "tie" }),
        s = mount({
          mints: ["0xAB", "0XAB"],
          options: { disabled: true },
          cache: [
            [["coin", "0xAb"], first, 90000],
            [["coin", "0xab"], tie, 90000],
          ],
        });
      check(
        s.out.data.length === 0 && s.calls.length === 0,
        "disabled has empty state",
      );
      rerender(s, { options: { enabled: false } });
      same(
        s.out.data,
        [first],
        "lowercase0x fallback first equal timestamp; uppercase0X not folded",
      );
      same(
        s.lastOptions.queryKey,
        ["coinsByMints", "safe", "0XAB"],
        "only uppercase missing",
      );
      check(
        s.calls.length === 0,
        "explicit query enabled override prevents reader",
      );
      return observations(s);
    }
    throw Error("unknown finite case");
  },
  cleanup() {
    if (root) {
      flushSync(() => root.unmount());
      root = null;
    }
    const observerCount = active
      ? [...active.cells.values()].reduce((n, c) => n + c.listeners.size, 0)
      : 0;
    return {
      observerCount,
      rootChildren: document.getElementById("root").childElementCount,
    };
  },
};
