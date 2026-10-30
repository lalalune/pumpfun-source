import test from "node:test";
import assert from "node:assert/strict";
import { createHomeFeedCoordination } from "../reconstruction/home-feed-coordination/client.mjs";
import {
  followingPrefixKey,
  followingChainKey,
} from "../reconstruction/home-feed-coordination/qualification/key-ports.mjs";
import {
  manualHooks,
  cachePort,
} from "../reconstruction/home-feed-coordination/qualification/ports.mjs";
import { derive, verify } from "../scripts/original-home-feed-coordination.mjs";
const root = new URL("../", import.meta.url).pathname,
  kinds = "callout,update,reply,quote,repost";
function harness(extra = {}) {
  const hooks = manualHooks(),
    memo = new Map(),
    cache = cachePort(),
    events = [],
    reads = [],
    normalizations = [];
  const descriptor = {
      synthetic: "opaque required following query descriptor",
    },
    api = createHomeFeedCoordination({
      React: hooks.React,
      useMemoCache(n) {
        if (!memo.has(n))
          memo.set(n, Array(n).fill(Symbol.for("react.memo_cache_sentinel")));
        return memo.get(n);
      },
      useQueryClient: () => cache,
      useFollowingEvents: (o) => events.push(o),
      prefetchHome: (...args) => Promise.resolve(reads.push(["home", ...args])),
      prefetchTop: (...args) => Promise.resolve(reads.push(["top", ...args])),
      followingQueryOptions: (o) => (
        reads.push(["followingOptions", o]),
        descriptor
      ),
      followingPrefixKey,
      followingChainKey,
      followingChain: {
        m(value) {
          normalizations.push(["m", value]);
          return { syntheticChain: value };
        },
        R(value) {
          normalizations.push(["R", value]);
          return "synthetic:" + value.syntheticChain;
        },
      },
      followingKinds: kinds,
      ...extra,
    });
  return {
    ...api,
    cache,
    events,
    reads,
    descriptor,
    normalizations,
    get event() {
      return events.at(-1);
    },
    badge(input) {
      let value;
      for (let i = 0; i < 6; i++) {
        hooks.begin();
        value = api.useFollowingBadge(input);
        if (!hooks.changed) return value;
      }
      throw Error("finite render settling");
    },
    ahead(input) {
      hooks.begin();
      api.useHomeReadAhead(input);
      return hooks.flushEffects();
    },
  };
}
test("full owners/source/callers24witnesses1physicalfactory verify", async () =>
  assert.deepEqual(await verify(root), {
    witnesses: 24,
    sourceEntries: 1,
    badgeMemoSlots: 15,
    readAheadMemoSlots: 8,
    mounted: false,
    productionOperationsQualified: 0,
  }));
test("actual verifier rejects changed lifecycle/cache/read-ahead and false contract", async () => {
  const d = await derive(root),
    changes = [
      { code: d.code.replace('refetchType: "none"', 'refetchType: "all"') },
      { code: d.code.replace("null !== c", "null === c") },
      { code: d.code.replace("null === l", "null !== l") },
      { fixture: d.fixture + "\n// changed\n" },
      { contract: { ...d.contract, witnesses: [] } },
      { contract: { ...d.contract, priorQualifiedPorts: [] } },
      { contract: { ...d.contract, productionOperationsQualified: 1 } },
    ];
  for (const x of changes) {
    if (x.code !== undefined) assert.notEqual(x.code, d.code);
    await assert.rejects(verify(root, x));
  }
});
test("all original runtime/read/key/chain/event capabilities required", () => {
  assert.throws(() => createHomeFeedCoordination({}), /capabilities/);
  assert.throws(() => harness({ followingKinds: null }), /kinds/);
  assert.throws(() => harness({ followingChain: { m() {} } }), /capabilities/);
});
test("complete cache updater trims2pages, drops extrafields, skips1page/undefined preserving references", () => {
  const h = harness(),
    single = { pages: [{ id: 1 }], pageParams: ["a"], extra: true };
  assert.equal(h.trimExtraPages(undefined), undefined);
  assert.equal(h.trimExtraPages(single), undefined);
  const a = {
      pages: [{ id: 1 }, { id: 2 }],
      pageParams: ["a", "b"],
      extra: true,
    },
    out = h.trimExtraPages(a);
  assert.deepEqual(out, { pages: [a.pages[0]], pageParams: ["a"] });
  assert.equal(out.pages[0], a.pages[0]);
  assert.equal(a.pages.length, 2);
});
test("inactive null-onlyviewer gate and exact event API/querychain normalization", () => {
  const h = harness();
  h.badge({ viewer: null, isActive: false });
  assert.equal(h.event.enabled, false);
  h.badge({ viewer: undefined, isActive: false });
  assert.equal(h.event.enabled, true);
  assert.equal(h.event.viewer, undefined);
  assert.equal(h.event.surface, "classic-tab-badge");
  assert.equal(h.event.kinds, kinds);
  assert.deepEqual(
    h.event.queryKey,
    followingChainKey(undefined, 20, kinds, "synthetic:all"),
  );
  assert.deepEqual(h.normalizations.slice(-2), [
    ["m", "all"],
    ["R", { syntheticChain: "all" }],
  ]);
  h.badge({ viewer: "v", isActive: true, chain: "near" });
  assert.equal(h.event.enabled, false);
});
test("event rawID dedup still trims/invalidates every time across all matchingchain caches", () => {
  const h = harness(),
    input = { viewer: "v", isActive: false, chain: "near" },
    prefix = followingPrefixKey("v", 20, kinds),
    keys = ["", "near", "base"].map((c) => [...prefix, c]);
  for (const key of keys)
    h.cache.put(key, {
      pages: [{ id: 1 }, { id: 2 }],
      pageParams: [undefined, "cursor"],
      extra: "discard",
    });
  const other = [...followingPrefixKey("other", 20, kinds), "near"],
    size = [...followingPrefixKey("v", 5, kinds), "near"];
  for (const key of [other, size])
    h.cache.put(key, { pages: [1, 2], pageParams: [0, 1] });
  h.badge(input);
  const event = h.event;
  event.onNewContent({ id: "x" });
  assert.equal(h.badge(input).newCount, 1);
  h.event.onNewContent({ id: "x" });
  assert.equal(h.badge(input).newCount, 1);
  h.event.onNewContent({ id: "y" });
  assert.equal(h.badge(input).newCount, 2);
  for (const key of keys)
    assert.deepEqual(h.cache.get(key), {
      pages: [{ id: 1 }],
      pageParams: [undefined],
    });
  assert.equal(h.cache.get(other).pages.length, 2);
  assert.equal(h.cache.get(size).pages.length, 2);
  assert.deepEqual(
    h.cache.calls.map((x) => x[0]),
    [
      "setQueriesData",
      "invalidateQueries",
      "setQueriesData",
      "invalidateQueries",
      "setQueriesData",
      "invalidateQueries",
    ],
  );
  for (const c of h.cache.calls.filter((x) => x[0] === "invalidateQueries"))
    assert.deepEqual(c[1], { queryKey: prefix, refetchType: "none" });
});
test("chain change preservespending IDs, active/viewer change clears, reset callback stable", () => {
  const h = harness(),
    i = { viewer: "v", isActive: false },
    a = h.badge(i);
  h.event.onNewContent({ id: "x" });
  assert.equal(h.badge(i).newCount, 1);
  let out = h.badge({ ...i, chain: "near" });
  assert.equal(out.newCount, 1);
  assert.equal(out.reset, a.reset);
  out = h.badge({ ...i, isActive: true });
  assert.equal(out.newCount, 0);
  assert.equal(h.badge(i).newCount, 0);
  h.event.onNewContent({ id: "y" });
  assert.equal(h.badge(i).newCount, 1);
  assert.equal(h.badge({ ...i, viewer: "new" }).newCount, 0);
  h.event.onNewContent({ id: "z" });
  out = h.badge({ ...i, viewer: "new" });
  assert.equal(out.newCount, 1);
  assert.equal(out.reset(), undefined);
  assert.equal(h.badge({ ...i, viewer: "new" }).newCount, 0);
});
test("render output memo and event callback source dependencies preserve identity", () => {
  const h = harness(),
    i = { viewer: "v", isActive: false };
  const a = h.badge(i),
    callback = h.event.onNewContent;
  assert.equal(h.badge(i), a);
  h.badge({ ...i, chain: "near" });
  assert.equal(h.event.onNewContent, callback);
  h.badge({ ...i, viewer: "other" });
  assert.notEqual(h.event.onNewContent, callback);
});
test("read-ahead exactHome→Top→Following order, nullskip and opaque descriptor identity", () => {
  const h = harness(),
    i = {
      chain: "base",
      followingChain: "near",
      isLoggedIn: true,
      address: "a",
      viewer: "v",
    };
  assert.deepEqual(h.ahead(i), [undefined]);
  assert.deepEqual(h.reads, [
    [
      "home",
      h.cache,
      { chain: "base", includeFollowedHolders: true, viewerAddress: "a" },
    ],
    ["top", h.cache, { includeFollowedHolders: true }],
    ["followingOptions", { viewer: "v", pageSize: 20, chain: "near" }],
  ]);
  assert.deepEqual(h.cache.calls, [["prefetchInfiniteQuery", h.descriptor]]);
  assert.deepEqual(h.ahead({ ...i }), []);
  h.ahead({ ...i, viewer: null });
  assert.equal(h.reads.filter((x) => x[0] === "home").length, 2);
  assert.equal(h.reads.filter((x) => x[0] === "top").length, 2);
  assert.equal(h.reads.filter((x) => x[0] === "followingOptions").length, 1);
  assert.equal(h.cache.calls.length, 1);
});
test("read-ahead undefinedviewer admitted, followingChain undefined→all only, rawnull retained", () => {
  const h = harness();
  h.ahead({ chain: "all", viewer: undefined });
  assert.deepEqual(h.reads.at(-1), [
    "followingOptions",
    { viewer: undefined, pageSize: 20, chain: "all" },
  ]);
  h.ahead({ chain: "all", followingChain: null, viewer: undefined });
  assert.deepEqual(h.reads.at(-1), [
    "followingOptions",
    { viewer: undefined, pageSize: 20, chain: null },
  ]);
});
test("read-ahead doesnotawait first result; same dependencies skip, changedaddress retriggers", () => {
  let resolve;
  const first = new Promise((r) => (resolve = r)),
    order = [],
    h = harness({
      prefetchHome: (...a) => (order.push("home"), first),
      prefetchTop: () => order.push("top"),
      followingQueryOptions: () => {
        order.push("following");
        return {};
      },
    });
  const i = { chain: "all", viewer: "v", address: "a", isLoggedIn: false };
  h.ahead(i);
  assert.deepEqual(order, ["home", "top", "following"]);
  assert.equal(h.ahead(i).length, 0);
  h.ahead({ ...i, address: "b" });
  assert.deepEqual(order, [
    "home",
    "top",
    "following",
    "home",
    "top",
    "following",
  ]);
  resolve();
});
test("read-ahead synchronous firstportfailure stopslatercalls, no invented catch", () => {
  const failure = { synthetic: true },
    later = [],
    h = harness({
      prefetchHome() {
        throw failure;
      },
      prefetchTop: () => later.push("top"),
    });
  assert.throws(
    () => h.ahead({ viewer: "v" }),
    (e) => e === failure,
  );
  assert.deepEqual(later, []);
});
