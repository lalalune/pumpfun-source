import React from "react";
import { c as useMemoCache } from "react/compiler-runtime";
import { createRoot } from "react-dom/client";
import { flushSync } from "react-dom";
import { createHomeFeedCoordination } from "../client.mjs";
import { followingPrefixKey, followingChainKey } from "./key-ports.mjs";
import { cachePort } from "./ports.mjs";
const el = React.createElement,
  check = (v, l) => {
    if (!v) throw Error(l);
  },
  same = (a, b, l) =>
    check(
      JSON.stringify(a) === JSON.stringify(b),
      l + ": " + JSON.stringify(a),
    ),
  kinds = "callout,update,reply,quote,repost";
let root, active;
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
    eventListeners: active?.listeners.size ?? 0,
    rootChildren: document.getElementById("root").childElementCount,
  };
}
// Explicit finite synthetic capabilities. Chain/query descriptors are opaque injected
// stand-ins; this does not rerun or copy1966/1846/1973's read/query implementations.
function mount({
  badge = { viewer: "v", isActive: false, chain: "all" },
  ahead = { chain: "all", isLoggedIn: false, address: "a", viewer: "v" },
  homeResult,
} = {}) {
  if (root)
    same(close(), { eventListeners: 0, rootChildren: 0 }, "prior cleanup");
  const s = {
    badgeInput: badge,
    aheadInput: ahead,
    cache: cachePort(),
    listeners: new Set(),
    eventHistory: [],
    reads: [],
    descriptors: [],
    normalizations: [],
    out: null,
  };
  active = s;
  const api = createHomeFeedCoordination({
    React,
    useMemoCache,
    useQueryClient: () => s.cache,
    useFollowingEvents(options) {
      s.event = options;
      React.useEffect(() => {
        if (!options.enabled) return;
        const listener = (e) => options.onNewContent(e);
        s.listeners.add(listener);
        s.eventHistory.push("subscribe");
        return () => {
          s.listeners.delete(listener);
          s.eventHistory.push("unsubscribe");
        };
      }, [options.enabled, options.viewer, options.onNewContent]);
    },
    prefetchHome: (client, input) => (
      s.reads.push({ kind: "home", client, input }),
      homeResult ?? Promise.resolve({ synthetic: "home-prefetch-result" })
    ),
    prefetchTop: (client, input) => (
      s.reads.push({ kind: "top", client, input }),
      Promise.resolve({ synthetic: "top-prefetch-result" })
    ),
    followingQueryOptions: (input) => {
      s.reads.push({ kind: "followingOptions", input });
      const descriptor = { syntheticDescriptor: true, input };
      s.descriptors.push(descriptor);
      return descriptor;
    },
    followingPrefixKey,
    followingChainKey,
    followingChain: {
      m(value) {
        s.normalizations.push(["m", value]);
        return { syntheticChain: value };
      },
      R(value) {
        s.normalizations.push(["R", value]);
        return "synthetic:" + value.syntheticChain;
      },
    },
    followingKinds: kinds,
  });
  function App() {
    s.out = api.useFollowingBadge(s.badgeInput);
    api.useHomeReadAhead(s.aheadInput);
    return el(
      "section",
      null,
      el("output", { "data-testid": "count" }, s.out.newCount),
      el(
        "button",
        { "data-testid": "reset", onClick: s.out.reset },
        "Reset badge",
      ),
    );
  }
  s.render = ({ badge, ahead } = {}) => {
    if (badge) s.badgeInput = badge;
    if (ahead) s.aheadInput = ahead;
    flushSync(() => root.render(el(App)));
  };
  s.emit = (event) =>
    flushSync(() => {
      for (const listener of [...s.listeners]) listener(event);
    });
  root = createRoot(document.getElementById("root"));
  s.render();
  return s;
}
function prefixTrim() {
  const s = mount(),
    prefix = followingPrefixKey("v", 20, kinds),
    keys = ["", "near", "base"].map((c) => [...prefix, c]);
  for (const key of keys)
    s.cache.put(key, {
      pages: [{ id: "first" }, { id: "later" }],
      pageParams: [undefined, "later"],
      extra: "drop",
    });
  const other = [...followingPrefixKey("other", 20, kinds), ""];
  s.cache.put(other, { pages: [1, 2], pageParams: [0, 1] });
  s.cache.calls.length = 0;
  s.emit({ id: "a" });
  s.emit({ id: "a" });
  s.emit({ id: "b" });
  check(s.out.newCount === 2, "rawid dedup");
  for (const key of keys)
    same(
      s.cache.get(key),
      { pages: [{ id: "first" }], pageParams: [undefined] },
      "allchain prefix trim",
    );
  check(s.cache.get(other).pages.length === 2, "other viewer unaffected");
  same(
    s.cache.calls.map((c) => c[0]),
    [
      "setQueriesData",
      "invalidateQueries",
      "setQueriesData",
      "invalidateQueries",
      "setQueriesData",
      "invalidateQueries",
    ],
    "every event updater then invalidate",
  );
  check(
    s.cache.calls
      .filter((c) => c[0] === "invalidateQueries")
      .every((c) => c[1].refetchType === "none"),
    "no refetch mode",
  );
  return {
    count: s.out.newCount,
    trimmedCaches: keys.length,
    unrelatedPages: s.cache.get(other).pages.length,
    calls: s.cache.calls.map((c) => c[0]),
  };
}
function lifecycle() {
  const s = mount();
  s.emit({ id: "a" });
  check(s.out.newCount === 1, "inactive badge");
  const callback = s.event.onNewContent;
  s.render({ badge: { ...s.badgeInput, chain: "near" } });
  check(
    s.out.newCount === 1 && s.event.onNewContent === callback,
    "chain preservesids/callback",
  );
  same(
    s.event.queryKey,
    followingChainKey("v", 20, kinds, "synthetic:near"),
    "chain key",
  );
  s.render({ badge: { ...s.badgeInput, isActive: true } });
  check(
    s.out.newCount === 0 && s.listeners.size === 0,
    "active clears and unsubscribes",
  );
  s.emit({ id: "blocked" });
  s.render({ badge: { ...s.badgeInput, isActive: false } });
  check(s.out.newCount === 0 && s.listeners.size === 1, "inactive resubscribe");
  s.emit({ id: "next" });
  check(s.out.newCount === 1, "resubscribed event");
  s.render({ badge: { ...s.badgeInput, viewer: "other" } });
  check(
    s.out.newCount === 0 && s.listeners.size === 1,
    "viewer reset and replace",
  );
  return {
    count: s.out.newCount,
    eventTransitions: s.eventHistory,
    key: s.event.queryKey,
  };
}
function readAheadOrder() {
  let resolve;
  const promise = new Promise((r) => (resolve = r)),
    s = mount({
      ahead: {
        chain: "base",
        followingChain: "near",
        isLoggedIn: true,
        address: "a",
        viewer: "v",
      },
      homeResult: promise,
    });
  same(
    s.reads.map((x) => x.kind),
    ["home", "top", "followingOptions"],
    "does not awaitHome",
  );
  same(
    s.reads[0].input,
    { chain: "base", includeFollowedHolders: true, viewerAddress: "a" },
    "Homeexact",
  );
  same(s.reads[1].input, { includeFollowedHolders: true }, "Topexact");
  same(
    s.reads[2].input,
    { viewer: "v", pageSize: 20, chain: "near" },
    "Followingexact",
  );
  const prefetch = s.cache.calls.filter(
    (c) => c[0] === "prefetchInfiniteQuery",
  );
  check(
    prefetch.length === 1 && prefetch[0][1] === s.descriptors[0],
    "opaque descriptor identity",
  );
  check(
    s.reads[0].client === s.cache && s.reads[1].client === s.cache,
    "same query client",
  );
  resolve();
  return {
    order: s.reads.map((x) => x.kind),
    inputs: s.reads.map((x) => x.input),
    descriptorSame: true,
    homePromiseNotAwaited: true,
  };
}
function dependencyAndClient() {
  const s = mount();
  check(s.reads.length === 3, "initialreadset");
  s.render({ ahead: { ...s.aheadInput } });
  check(s.reads.length === 3, "same dependencies skip");
  s.render({ ahead: { ...s.aheadInput, address: "b" } });
  check(s.reads.length === 6, "address change readahead");
  const old = s.cache,
    callback = s.event.onNewContent;
  s.cache = cachePort();
  s.render();
  check(s.reads.length === 9, "client replacement effect");
  check(
    s.event.onNewContent !== callback && s.listeners.size === 1,
    "client replacement callback",
  );
  s.emit({ id: "new-client" });
  check(s.out.newCount === 1, "newclient event");
  check(
    s.cache.calls.some((c) => c[0] === "invalidateQueries"),
    "new client mutated",
  );
  check(
    !old.calls.some((c) => c[0] === "invalidateQueries"),
    "old client unchanged",
  );
  return {
    readCalls: s.reads.length,
    listeners: s.listeners.size,
    newCacheInvalidated: true,
    oldCacheInvalidated: false,
  };
}
function nullUndefined() {
  const s = mount({
    badge: { viewer: null, isActive: false },
    ahead: { chain: "all", viewer: null },
  });
  check(
    s.listeners.size === 0 && s.out.newCount === 0,
    "null viewer badge disabled",
  );
  same(
    s.reads.map((x) => x.kind),
    ["home", "top"],
    "null skipsFollowing only",
  );
  s.render({
    badge: { viewer: undefined, isActive: false },
    ahead: { chain: "all", viewer: undefined },
  });
  check(s.listeners.size === 1, "undefined viewer enabled");
  same(
    s.reads.at(-1).input,
    { viewer: undefined, pageSize: 20, chain: "all" },
    "undefined chain default",
  );
  s.emit({ id: "undefined-viewer" });
  check(s.out.newCount === 1, "undefined event counted");
  s.render({
    ahead: { chain: "all", followingChain: null, viewer: undefined },
  });
  same(
    s.reads.at(-1).input,
    { viewer: undefined, pageSize: 20, chain: null },
    "null chain retained",
  );
  return {
    readKinds: s.reads.map((x) => x.kind),
    count: s.out.newCount,
    followingChain: s.reads.at(-1).input.chain,
  };
}
async function resetButton() {
  const s = mount(),
    reset = s.out.reset;
  s.emit({ id: "a" });
  s.emit({ id: "b" });
  check(
    document.querySelector("[data-testid=count]").textContent === "2",
    "rendered badge count",
  );
  document.querySelector("[data-testid=reset]").click();
  await until(() => s.out.newCount === 0);
  check(s.out.reset === reset, "stable reset callback");
  s.emit({ id: "after-reset" });
  check(s.out.newCount === 1, "new event after reset");
  s.render({ badge: { ...s.badgeInput, isActive: true } });
  check(
    s.out.newCount === 0 &&
      document.querySelector("[data-testid=count]").textContent === "0",
    "active tab reset",
  );
  return {
    resetStable: true,
    afterResetEventCount: 1,
    activeCount: s.out.newCount,
  };
}
const cases = new Map([
  ["prefix-trim-and-dedup", prefixTrim],
  ["viewer-active-chain-lifecycle", lifecycle],
  ["read-ahead-order-and-descriptor", readAheadOrder],
  ["dependencies-and-client-replacement", dependencyAndClient],
  ["null-undefined-readiness", nullUndefined],
  ["rendered-reset-callback", resetButton],
]);
window.coordinationFixture = {
  names: [...cases.keys()],
  run(name) {
    check(cases.has(name), "known case");
    return cases.get(name)();
  },
  cleanup: close,
};
