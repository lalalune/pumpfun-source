import assert from "node:assert/strict";
import test from "node:test";
import { performance } from "node:perf_hooks";
import { readFile } from "node:fs/promises";
import {
  createFrameBatchRuntime,
  createLiveCoinState,
  batchVariantHashes,
  subscribeWithSelector,
} from "../reconstruction/live-coin-state/client.mjs";
import {
  manualEnvironment,
  manualHooks,
  syntheticBoundStore,
} from "../reconstruction/live-coin-state/qualification/ports.mjs";
import { verify } from "../scripts/original-live-coin-state.mjs";
function setup(variant, options) {
  const host = manualEnvironment(options),
    hooks = manualHooks();
  const frame = createFrameBatchRuntime({
    variant,
    React: hooks.React,
    compiler: hooks.compiler,
    ...host,
  });
  const live = createLiveCoinState({
    React: hooks.React,
    compiler: hooks.compiler,
    createBoundStore: syntheticBoundStore(),
    frameBatch: frame,
    clock: host.clock,
  });
  return { host, hooks, frame, live, api: live.store.getState() };
}
for (const variant of batchVariantHashes) {
  const tag = variant.slice(0, 12);
  test(`${tag}: pending reads versus committed getters, duplicates and ordered flush`, () => {
    const { host, api, live } = setup(variant);
    let calls = 0;
    live.store.subscribe(() => calls++);
    host.setTime(10);
    api.setCoin({ mint: "a", usdMarketCap: 2, usdAthMarketCap: 7 });
    host.setTime(11);
    api.updateCoin("a", { usdMarketCap: 9, usdAthMarketCap: 9 });
    assert.equal(api.getCoin("a"), undefined);
    assert.equal(api.hasLiveData("a"), false);
    assert.deepEqual(api.peekCoin("a"), {
      mint: "a",
      usdMarketCap: 9,
      usdAthMarketCap: 9,
      lastUpdated: 11,
      isLiveData: true,
    });
    assert.deepEqual(api.getCoins(["a", "missing", "a"]), [
      undefined,
      undefined,
      undefined,
    ]);
    host.advance(16);
    const a = api.getCoin("a");
    assert.equal(a.lastUpdated, 11);
    assert.equal(api.hasLiveData("a"), true);
    assert.deepEqual(api.getCoins(["a", "missing", "a"]), [a, undefined, a]);
    assert.equal(calls, 1);
    assert.equal(host.handles().length, 0);
    assert.equal(host.listeners("visibilitychange"), 1);
  });
  test(`${tag}: exact set/update/remove interleavings retain pending patches`, () => {
    const { api, host } = setup(variant);
    api.setCoin({ mint: "a", usdMarketCap: 3, extra: "base" });
    api.removeCoin("a");
    assert.equal(api.peekCoin("a"), undefined);
    api.updateCoin("a", { usdMarketCap: 4, usdAthMarketCap: 8 });
    assert.equal(api.peekCoin("a").extra, undefined);
    assert.equal(api.peekCoin("a").usdMarketCap, 4);
    api.setCoin({
      mint: "a",
      usdMarketCap: 1,
      usdAthMarketCap: 2,
      other: "new",
    });
    const pending = api.peekCoin("a");
    assert.equal(pending.other, "new");
    assert.equal(pending.usdMarketCap, 4);
    assert.equal(pending.usdAthMarketCap, 8);
    api.removeCoin("a");
    assert.equal(api.peekCoin("a").usdMarketCap, 4); // prior patch survives empty base
    host.advance(16);
    assert.equal(api.getCoin("a").usdMarketCap, 4);
    api.removeCoin("a");
    host.advance(16);
    assert.equal(api.getCoin("a"), undefined);
  });
  test(`${tag}: defined ATH maximum, unvalidated values and latest nonmonotonic time`, () => {
    const { api, host } = setup(variant);
    host.setTime(50);
    api.setCoin({ mint: "a", usdAthMarketCap: 10 });
    host.advance(16);
    host.setTime(9);
    api.updateCoin("a", { usdAthMarketCap: 2, usdMarketCap: null });
    host.setTime(4);
    api.updateCoin("a", { usdAthMarketCap: undefined, priceUsd: NaN });
    host.fireKind("raf");
    const a = api.getCoin("a");
    assert.equal(a.lastUpdated, 4);
    assert.equal(a.usdAthMarketCap, 10);
    assert.equal(a.usdMarketCap, null);
    assert.ok(Number.isNaN(a.priceUsd));
    api.updateCoin("a", { usdAthMarketCap: NaN });
    host.advance(16);
    assert.ok(Number.isNaN(api.getCoin("a").usdAthMarketCap));
  });
  test(`${tag}: plain set does not force live flag; undefined patches and absent rows`, () => {
    const { api, host } = setup(variant);
    api.setCoin({ mint: "a", usdMarketCap: 3, isLiveData: false });
    host.advance(16);
    assert.equal(api.hasLiveData("a"), false);
    api.updateCoin("a", undefined);
    host.advance(16);
    assert.equal(api.hasLiveData("a"), false);
    api.updateCoin("b", {});
    host.advance(16);
    assert.deepEqual(api.getCoin("b"), {
      mint: "b",
      usdMarketCap: 0,
      lastUpdated: 32,
      isLiveData: true,
    });
  });
  test(`${tag}: per-selector listeners, immediate callback and unsubscribe`, () => {
    const { api, live, host } = setup(variant);
    const events = [];
    const off = live.store.subscribe(
      (s) => s.coins.a?.usdMarketCap,
      (a, b) => events.push([a, b]),
      { fireImmediately: true },
    );
    api.setCoin({ mint: "b" });
    host.advance(16);
    assert.deepEqual(events, [[undefined, undefined]]);
    api.updateCoin("a", { usdMarketCap: 2 });
    host.advance(16);
    assert.deepEqual(events, [
      [undefined, undefined],
      [2, undefined],
    ]);
    api.updateCoin("a", { usdMarketCap: 2 });
    host.advance(16);
    assert.equal(events.length, 2);
    off();
    api.updateCoin("a", { usdMarketCap: 3 });
    host.advance(16);
    assert.equal(events.length, 2);
    let eqCalls = 0;
    const custom = [];
    const off2 = live.store.subscribe(
      (s) => s.coins.a,
      (n, o) => custom.push([n, o]),
      {
        equalityFn: () => {
          eqCalls++;
          return true;
        },
      },
    );
    api.updateCoin("a", {});
    host.advance(16);
    assert.equal(eqCalls, 1);
    assert.equal(custom.length, 0);
    off2();
  });
  test(`${tag}: visible RAF, 100ms fallback, hidden/noRAF250 and visibility flush`, () => {
    const { host, api } = setup(variant);
    api.setCoin({ mint: "a" });
    assert.deepEqual(
      host.handles().map((h) => [h.kind, h.at]),
      [
        ["raf", 16],
        ["timeout", 100],
      ],
    );
    host.fireKind("timeout");
    assert.ok(api.getCoin("a"));
    assert.equal(host.handles().length, 0);
    host.visibility("hidden");
    api.setCoin({ mint: "b" });
    assert.deepEqual(
      host.handles().map((h) => [h.kind, h.at]),
      [["timeout", 250]],
    );
    host.advance(249);
    assert.equal(api.getCoin("b"), undefined);
    host.advance(1);
    assert.ok(api.getCoin("b"));
    host.visibility("visible");
    api.setCoin({ mint: "c" });
    host.visibility("hidden");
    assert.ok(api.getCoin("c"));
    assert.equal(host.handles().length, 0);
    const n = setup(variant, { raf: false });
    n.api.setCoin({ mint: "n" });
    n.host.advance(249);
    assert.equal(n.api.getCoin("n"), undefined);
    n.host.advance(1);
    assert.ok(n.api.getCoin("n"));
  });
  test(`${tag}: batch overwrite/merge/clear/direct flush and reentrancy`, () => {
    const { frame, host } = setup(variant);
    const snapshots = [];
    const b = frame.createBatch({
      merge: (a, b) => a + b,
      onFlush: (s) => {
        snapshots.push([...s]);
        if (s.get("a") === 3) b.set("b", 4);
      },
    });
    b.set("a", 1);
    b.set("a", 2);
    assert.equal(b.peek("a"), 3);
    assert.equal(b.size, 1);
    b.flush();
    assert.deepEqual(snapshots, [[["a", 3]]]);
    assert.equal(b.peek("b"), 4);
    host.advance(16);
    assert.deepEqual(snapshots, [[["a", 3]], [["b", 4]]]);
    assert.equal(b.size, 0);
    b.set("z", 5);
    b.clear();
    assert.equal(b.size, 0);
    host.advance(16);
    assert.equal(snapshots.length, 2);
    const plain = frame.createBatch({ onFlush: (s) => snapshots.push([...s]) });
    plain.set("x", 1);
    plain.set("x", 2);
    plain.flush();
    assert.deepEqual(snapshots.at(-1), [["x", 2]]);
  });
  test(`${tag}: callback Set snapshot, logger isolation and requeued callback`, () => {
    const { frame, host } = setup(variant);
    const order = [];
    const again = () => {
      order.push("again");
      if (order.length < 3) frame.enqueue(again);
    };
    frame.enqueue(() => {
      order.push("bad");
      throw Error("finite synthetic callback");
    });
    frame.enqueue(again);
    frame.enqueue(again);
    frame.enqueue(() => order.push("last"));
    host.advance(16);
    assert.deepEqual(order, ["bad", "again", "last"]);
    assert.equal(host.errors.length, 1);
    assert.equal(host.errors[0][0], "[frameBatch] flush failed");
    host.advance(16);
    assert.deepEqual(order, ["bad", "again", "last", "again"]);
  });
  test(`${tag}: nested pause release, direct flush during pause and cleanup reschedules`, () => {
    const { host, hooks, frame, api } = setup(variant);
    api.setCoin({ mint: "a" });
    hooks.render("p1", () => frame.usePause("x"));
    hooks.render("p2", () => frame.usePause("y"));
    host.visibility("hidden");
    assert.equal(api.getCoin("a"), undefined);
    const b = frame.createBatch({ onFlush: () => {} });
    b.set("direct", 1);
    b.flush();
    assert.equal(b.size, 0);
    hooks.unmount("p1");
    assert.equal(api.getCoin("a"), undefined);
    hooks.unmount("p2");
    assert.equal(api.getCoin("a"), undefined);
    assert.deepEqual(
      host.handles().map((h) => [h.kind, h.at]),
      [["timeout", 250]],
    );
    host.advance(250);
    assert.ok(api.getCoin("a"));
    assert.equal(host.handles().length, 0);
  });
  test(`${tag}: pause completion flushes, dependency transition and idempotent cleanup`, () => {
    const { host, hooks, frame, api } = setup(variant);
    hooks.render("p", () => frame.usePause(1));
    api.setCoin({ mint: "a" });
    host.advance(16);
    assert.ok(api.getCoin("a"));
    assert.equal(host.handles().length, 0);
    hooks.unmount("p");
    assert.equal(host.handles().length, 0);
    hooks.render("p", () => frame.usePause(2));
    hooks.render("p", () => frame.usePause(3));
    api.setCoin({ mint: "b" });
    host.advance(16);
    assert.ok(api.getCoin("b"));
    hooks.unmount("p");
    assert.equal(host.handles().length, 0);
    const n = setup(variant, { raf: false });
    n.hooks.render("pause", () => n.frame.usePause(1));
    n.api.setCoin({ mint: "t" });
    n.host.advance(249);
    assert.equal(n.api.getCoin("t"), undefined);
    n.host.advance(1);
    assert.ok(n.api.getCoin("t"));
    n.hooks.unmount("pause");
  });
  test(`${tag}: all selectors preserve references/order and shallow object/Map/iterable rules`, () => {
    const { api, host, hooks, live } = setup(variant);
    api.setCoin({ mint: "a", usdMarketCap: 0 });
    host.advance(16);
    assert.equal(
      hooks.render("cap", () => live.useMarketCap("a")),
      0,
    );
    assert.equal(
      hooks.render("coin", () => live.useCoin("a")),
      api.getCoin("a"),
    );
    const mints = ["a", "missing", "a"];
    const one = hooks.render("many", () => live.useCoins(mints));
    const two = hooks.render("many", () => live.useCoins([...mints]));
    assert.equal(one, two);
    assert.equal(one[0], one[2]);
    assert.equal(one[1], undefined);
    api.setCoin({ mint: "b" });
    host.advance(16);
    assert.equal(
      hooks.render("many", () => live.useCoins(mints)),
      one,
    );
    api.updateCoin("a", {});
    host.advance(16);
    assert.notEqual(
      hooks.render("many", () => live.useCoins(mints)),
      one,
    );
    assert.equal(
      hooks.render("empty1", () => live.useCoins([])),
      hooks.render("empty2", () => live.useCoins([])),
    );
    let selected;
    const read = () =>
      hooks.render("shallow", () => live.useShallow(() => selected))({});
    selected = { a: 1 };
    const obj = read();
    selected = { a: 1 };
    assert.equal(read(), obj);
    selected = Object.assign(Object.create(null), { a: 1 });
    assert.notEqual(read(), obj);
    selected = new Map([["a", undefined]]);
    const map = read();
    selected = new Map([["b", undefined]]);
    assert.equal(read(), map); // captured size/get equality, not key-set equality
    selected = new Set([1, 2]);
    const set = read();
    selected = new Set([1, 2]);
    assert.equal(read(), set);
    selected = new Set([2, 1]);
    assert.equal(read(), set); // entries comparison ignores Set insertion order
    class Ordered {
      constructor(values) {
        this.values = values;
      }
      *[Symbol.iterator]() {
        yield* this.values;
      }
    }
    selected = new Ordered([1, 2]);
    const ordered = read();
    selected = new Ordered([1, 2]);
    assert.equal(read(), ordered);
    selected = new Ordered([2, 1]);
    assert.notEqual(read(), ordered);
    selected = new URLSearchParams("a=1");
    const iterable = read();
    selected = new URLSearchParams("a=1");
    assert.equal(read(), iterable);
  });
}
test("real Node noRAF250ms fallback commits once; finite actual timer control", async () => {
  const events = [];
  const before = performance.now();
  const frame = createFrameBatchRuntime({
    variant: batchVariantHashes[0],
    React: {},
    compiler: () => {},
    environment: { window: {}, document: undefined, setTimeout, clearTimeout },
    logger: { error: (e) => events.push(e) },
  });
  await new Promise((resolve, reject) => {
    const b = frame.createBatch({
      onFlush: (s) => {
        try {
          assert.equal(s.get("a"), 2);
          resolve();
        } catch (e) {
          reject(e);
        }
      },
    });
    b.set("a", 1);
    b.set("a", 2);
  });
  assert.ok(performance.now() - before >= 200);
  assert.deepEqual(events, []);
});
test("unknown physical variant is rejected rather than choosing a loader winner", () => {
  assert.throws(
    () => createFrameBatchRuntime({ variant: "unknown" }),
    /explicit supported811005/,
  );
});
test("source gate rejects actual generated code, contract values, variants, witnesses and ports mutations", async () => {
  const code = await readFile(
    new URL("../reconstruction/live-coin-state/client.mjs", import.meta.url),
    "utf8",
  );
  const contract = JSON.parse(
    await readFile(
      new URL(
        "../reconstruction/live-coin-state/contract.json",
        import.meta.url,
      ),
    ),
  );
  assert.equal((await verify()).witnesses, 66);
  for (const change of [
    (c) => {
      c.batchVariants.pop();
    },
    (c) => {
      c.witnesses[0].sha256 = "0".repeat(64);
    },
    (c) => {
      c.state.methods.pop();
    },
    (c) => {
      c.externalPorts = [];
    },
    (c) => {
      c.mounted = true;
    },
    (c) => {
      c.consumers[0].uses[0].utf16[0]++;
    },
  ]) {
    const c = structuredClone(contract);
    change(c);
    await assert.rejects(verify(undefined, { code, contract: c }));
  }
  await assert.rejects(
    verify(undefined, {
      code: code.replace("Math.max(e, t)", "Math.min(e, t)"),
      contract,
    }),
  );
  await assert.rejects(
    verify(undefined, {
      code: code.replace("setTimeout(f, 100)", "setTimeout(f, 101)"),
      contract,
    }),
  );
});
