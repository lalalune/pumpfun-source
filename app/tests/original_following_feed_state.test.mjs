import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { once } from "node:events";
import {
  createFollowingFeedRead,
  readContexts,
  imageVariants,
  classificationVariants,
} from "../reconstruction/following-feed-state/client.mjs";
import {
  createNormalizerHelpers,
  helperVariants,
} from "../reconstruction/following-feed-state/qualification/helper-ports.mjs";
import {
  manualHooks,
  queryCachePort,
} from "../reconstruction/following-feed-state/qualification/ports.mjs";
import { derive, verify } from "../scripts/original-following-feed-state.mjs";
const root = new URL("../", import.meta.url).pathname;
const frontend = createRequire(
    new URL("../packages/frontend/package.json", import.meta.url),
  ),
  decode = createRequire(frontend.resolve("@solana/web3.js"))("bs58").decode;
const mint = "11111111111111111111111111111111";
const wire = (id, extra = {}) => ({
  kind: "callout",
  coinMint: mint,
  walletAddress: " author ",
  createdAt: "2026-01-02",
  callout: {
    calloutId: id,
    calloutTimestamp: "2026-01-01",
    thesis: " note ",
    updates: [],
  },
  ...extra,
});
function harness(extra = {}) {
  const hooks = manualHooks(),
    cache = queryCachePort(),
    requests = [],
    schemaCalls = [],
    metrics = [],
    events = [],
    observations = [];
  let now = 1000000,
    options,
    input = { viewer: "synthetic-viewer" },
    query = {
      data: undefined,
      isPending: false,
      isError: false,
      hasNextPage: false,
      isFetchingNextPage: false,
      fetchNextPage() {
        return "next";
      },
    };
  const api = createFollowingFeedRead({
    readContext: readContexts[0].reader,
    imageVariant: imageVariants[0].sha256,
    classificationVariant: classificationVariants[0].sha256,
    React: hooks.React,
    useInfiniteQuery: (o) => ((options = o), query),
    useQueryClient: () => cache,
    getContractClient:
      () =>
      async (...args) => (requests.push(args), { items: [], nextCursor: null }),
    kindsSchema: {
      parse(a) {
        schemaCalls.push(a);
        return [...a];
      },
    },
    useFollowingEvents: (o) => events.push(o),
    useFirstRowsObserver: (o) => observations.push(o),
    recordRefresh: (o) => metrics.push(o),
    normalizerHelpers: createNormalizerHelpers(helperVariants[0].sha256),
    decodeBase58: decode,
    clock: { now: () => now },
    ...extra,
  });
  return {
    ...api,
    cache,
    requests,
    schemaCalls,
    metrics,
    events,
    observations,
    get options() {
      return options;
    },
    get event() {
      return events.at(-1);
    },
    set query(v) {
      query = { ...query, ...v };
    },
    set now(v) {
      now = v;
    },
    render(v) {
      if (v) input = v;
      let out;
      for (let count = 0; count < 5; count++) {
        hooks.begin();
        out = api.useFollowingFeed(input);
        if (!hooks.changed) return out;
      }
      throw Error("synthetic hook settling bound");
    },
    put(data) {
      cache.setQueryData(options.queryKey, data);
    },
  };
}
test("full source boundary and all retained variants verify", async () => {
  assert.deepEqual(await verify(root), {
    witnesses: 168,
    sourceEntries: 26,
    readContexts: 2,
    imageVariants: 2,
    classificationVariants: 2,
    qualificationHelperVariants: 6,
    mounted: false,
    productionOperationsQualified: 0,
  });
});
test("actual source verifier rejects changed owner/reader/options and false contract claims", async () => {
  const d = await derive(root);
  const changes = [
    {
      code: d.code.replace(
        "minTradeAmountUsd: r ?? void 0",
        "minTradeAmountUsd: 0",
      ),
    },
    { code: d.code.replace('credentials: "include"', 'credentials: "omit"') },
    { code: d.code.replace("e - g.current < 5e3", "e - g.current <= 5e3") },
    { fixture: d.fixture + "\n// changed\n" },
    { contract: { ...d.contract, witnesses: [] } },
    { contract: { ...d.contract, ports: [] } },
    { contract: { ...d.contract, productionOperationsQualified: 1 } },
  ];
  for (const changed of changes) {
    if (changed.code !== undefined)
      assert.notEqual(changed.code, d.code, "code mutation must alter bytes");
    await assert.rejects(verify(root, changed));
  }
});
test("all explicit capabilities/own-key variant selectors required", () => {
  assert.throws(() => createFollowingFeedRead({}), /capabilities/);
  for (const value of [
    undefined,
    "constructor",
    "__proto__",
    {},
    new String(readContexts[0].reader),
  ])
    assert.throws(() => harness({ readContext: value }), /supported/);
});
for (const context of readContexts)
  test(`reader/chain context ${context.reader.slice(0, 12)} preserves factory→schema→call and exact options`, async () => {
    const order = [],
      parsed = ["synthetic-parsed"],
      signal = new AbortController().signal,
      h = harness({
        readContext: context.reader,
        getContractClient: () => {
          order.push("factory");
          return async (op, o) => (order.push("operation"), { op, o });
        },
        kindsSchema: {
          parse(xs) {
            order.push("parse");
            assert.deepEqual(xs, ["callout", "update", "trade", "collectible"]);
            return parsed;
          },
        },
      });
    const result = await h.readAlerts({ signal });
    assert.deepEqual(order, ["factory", "parse", "operation"]);
    assert.equal(result.op, "GET /following-positions/alerts");
    assert.equal(result.o.query.kinds, parsed);
    assert.deepEqual(result.o.query, {
      pageSize: 10,
      kinds: parsed,
      minTradeAmountUsd: 10,
      minMarketCapUsd: undefined,
      maxMarketCapUsd: undefined,
      chainIds: undefined,
      chains: undefined,
      cursor: undefined,
    });
    assert.equal(result.o.signal, signal);
    assert.equal(result.o.credentials, "include");
    assert.deepEqual(result.o.headers, { "Content-Type": "application/json" });
    assert.equal("body" in result.o, false);
  });
test("schema rejection occurs after factory acquisition but before operation, with exact rejection identity", async () => {
  const failure = { synthetic: "schema" },
    order = [],
    h = harness({
      getContractClient: () => {
        order.push("factory");
        return async () => order.push("operation");
      },
      kindsSchema: {
        parse(xs) {
          order.push("parse");
          assert.deepEqual(xs, [""]);
          throw failure;
        },
      },
    });
  await assert.rejects(h.readAlerts({ kinds: "" }), (e) => e === failure);
  assert.deepEqual(order, ["factory", "parse"]);
});
test("reader retains nullish band omission, falsy cursor omission, array identities and raw payload", async () => {
  const payload = { not: "validated" },
    chainIds = [1, 8453],
    chains = ["near:mainnet"],
    h = harness({
      getContractClient: () => async (op, o) => {
        assert.equal(o.query.pageSize, 0);
        assert.equal(o.query.minTradeAmountUsd, undefined);
        assert.equal(o.query.minMarketCapUsd, 0);
        assert.equal(o.query.maxMarketCapUsd, undefined);
        assert.equal(o.query.cursor, undefined);
        assert.equal(o.query.chainIds, chainIds);
        assert.equal(o.query.chains, chains);
        return payload;
      },
    });
  assert.equal(
    await h.readAlerts({
      pageSize: 0,
      minTradeAmountUsd: null,
      minMarketCapUsd: 0,
      maxMarketCapUsd: null,
      cursor: "",
      chainIds,
      chains,
    }),
    payload,
  );
});
test("query descriptor uses20/classic five kinds and chain partition; cursor compares only previous param", () => {
  const h = harness(),
    o = h.queryOptions({ viewer: "v", pageSize: 20, chain: "near" });
  assert.deepEqual(o.queryKey, [
    "callouts",
    "following-alerts",
    "v",
    20,
    "callout,update,reply,quote,repost",
    "near:mainnet",
  ]);
  assert.equal(o.initialPageParam, undefined);
  assert.equal(o.staleTime, 60000);
  assert.equal(o.retry, 3);
  assert.equal(o.getNextPageParam({ nextCursor: "x" }, [], "x"), undefined);
  assert.equal(
    o.getNextPageParam({ nextCursor: "earlier" }, [{}], "latest"),
    "earlier",
  );
  assert.equal(o.getNextPageParam({ nextCursor: "" }, [], undefined), "");
  assert.equal(o.getNextPageParam({ nextCursor: 0 }, [], undefined), 0);
  assert.equal(o.getNextPageParam({}, [], undefined), undefined);
});
test("query callback forwards pageParam/signal plus classicG and normalized chain filter", async () => {
  const h = harness(),
    signal = new AbortController().signal,
    o = h.queryOptions({ viewer: "v", pageSize: 4, chain: "base" });
  await o.queryFn({ pageParam: "cursor", signal });
  assert.deepEqual(h.schemaCalls[0], [
    "callout",
    "update",
    "reply",
    "quote",
    "repost",
  ]);
  const options = h.requests[0][1];
  assert.equal(options.query.pageSize, 4);
  assert.equal(options.query.cursor, "cursor");
  assert.deepEqual(options.query.chainIds, [8453]);
  assert.equal(options.signal, signal);
});
test("raw viewer null-only gate is not authentication; observer/event object signatures preserved", () => {
  const h = harness();
  const a = h.render({ viewer: null });
  assert.equal(h.options.enabled, false);
  assert.equal(h.event.enabled, false);
  assert.equal(a.isLoadingHistory, false);
  h.render({ viewer: undefined });
  assert.equal(h.options.enabled, true);
  assert.equal(h.event.viewer, undefined);
  assert.equal(h.observations.at(-1).identity, "|20|all");
  assert.equal(h.observations.at(-1).surface, "classic-tab");
  assert.equal(h.event.kinds, "callout,update,reply,quote,repost");
  assert.equal(h.event.surface, "classic-tab");
});
test("wire pages/keys first-occurrence dedup BEFORE chain filtering, order and null mapping", () => {
  const h = harness();
  h.query = {
    data: {
      pages: [
        {
          items: [
            wire("same", { chain: "ton:-239" }),
            { kind: "unknown" },
            wire("other", { chain: "near:mainnet" }),
          ],
        },
        {
          items: [
            wire("same", { chain: "near:mainnet" }),
            wire("last", { chain: "near:mainnet" }),
          ],
        },
      ],
    },
  };
  const out = h.render({ viewer: "v", chain: "near" });
  assert.deepEqual(
    out.rows.map((r) => r.key),
    ["cid:other", "cid:last"],
  );
  assert.equal(h.observations.at(-1).itemCount, 2);
  assert.equal(h.observations.at(-1).hasData, true);
});
test("query history flags and error only when data undefined; next-page guard forwards original receiver", () => {
  const h = harness();
  let receiver;
  h.query = {
    isPending: true,
    isError: true,
    fetchNextPage() {
      receiver = this;
      return "next";
    },
  };
  let out = h.render({ viewer: "v" });
  assert.equal(out.isLoadingHistory, true);
  assert.equal(out.error, "Could not load your following feed");
  out.fetchNextPage();
  assert.equal(receiver, undefined);
  h.query = { data: { pages: [] }, hasNextPage: true };
  out = h.render();
  assert.equal(out.error, null);
  assert.equal(out.fetchNextPage(), undefined);
  assert.ok(receiver?.hasNextPage);
  receiver = null;
  h.query = { isFetchingNextPage: true };
  out = h.render();
  out.fetchNextPage();
  assert.equal(receiver, null);
});
test("empty cache invalidation is throttled5s inclusive, no pending enqueue and exact metric", () => {
  const h = harness();
  h.render({ viewer: "v", bufferNewCallouts: true });
  h.event.onNewContent({ id: "a", coinMint: mint });
  h.event.onNewContent({ id: "b", coinMint: mint });
  assert.equal(h.cache.calls.filter((x) => x[0] === "invalidate").length, 1);
  assert.deepEqual(h.metrics, [
    { surface: "classic-tab", path: "empty-refetch" },
  ]);
  h.now = 1004999;
  h.event.onNewContent({ id: "c", coinMint: mint });
  assert.equal(h.cache.calls.filter((x) => x[0] === "invalidate").length, 1);
  h.now = 1005000;
  h.event.onNewContent({ id: "d", coinMint: mint });
  assert.equal(h.cache.calls.filter((x) => x[0] === "invalidate").length, 2);
  assert.equal(h.render().pendingNewCount, 0);
});
test("bufferingfalse invalidates nonemptycache without empty metric; bufferingtrue id-dedups raw events", () => {
  const h = harness();
  h.render({ viewer: "v" });
  h.put({ pages: [{ items: [wire("old")] }], pageParams: [undefined] });
  h.event.onNewContent({ id: "a", coinMint: mint });
  assert.equal(h.cache.calls.filter((x) => x[0] === "invalidate").length, 1);
  assert.deepEqual(h.metrics, []);
  h.render({ viewer: "v", bufferNewCallouts: true });
  h.event.onNewContent({ id: "a", coinMint: mint });
  h.render();
  h.event.onNewContent({ id: "a", coinMint: "different" });
  assert.equal(h.render().pendingNewCount, 1);
});
test("pending preview excludes only nullmint and caps3; pendingcount remains raw length", () => {
  const h = harness();
  h.render({ viewer: "v", bufferNewCallouts: true });
  h.put({ pages: [{ items: [wire("old")] }], pageParams: [undefined] });
  for (const e of [
    { id: "null", coinMint: null },
    { id: "a", coinMint: mint },
    { id: "undefined" },
    { id: "c", coinMint: "c" },
    { id: "d", coinMint: "d" },
  ]) {
    h.event.onNewContent(e);
    h.render();
  }
  const out = h.render();
  assert.equal(out.pendingNewCount, 5);
  assert.deepEqual(out.pendingPreview, [
    { key: "evt:a", coinMint: mint },
    { key: "evt:undefined", coinMint: undefined },
    { key: "evt:c", coinMint: "c" },
  ]);
});
test("showNew clears→trimfirstpage→invalidate→then metric, preserves count/minreceipt and returnsundefined", async () => {
  const h = harness();
  let resolve;
  h.cache.setInvalidation(() => new Promise((r) => (resolve = r)));
  h.render({ viewer: "v", bufferNewCallouts: true });
  const cache = {
    pages: [{ items: [wire("old")] }, { items: [wire("second")] }],
    pageParams: [undefined, "cursor"],
    extra: "dropped",
  };
  h.put(cache);
  h.event.onNewContent({ id: "a", coinMint: mint, receivedAtMs: 999000 });
  h.render();
  h.event.onNewContent({ id: "b", coinMint: mint, receivedAtMs: 998000 });
  const out = h.render(),
    start = h.cache.calls.length;
  assert.equal(out.showNewCallouts({ trigger: "auto" }), undefined);
  assert.equal(h.render().pendingNewCount, 0);
  assert.deepEqual(
    h.cache.calls.slice(start).map((c) => c[0]),
    ["get", "set", "invalidate"],
  );
  const after = h.cache.data.get(JSON.stringify(h.options.queryKey));
  assert.deepEqual(after, { pages: [cache.pages[0]], pageParams: [undefined] });
  assert.deepEqual(h.metrics, []);
  h.now = 1000500;
  resolve();
  await Promise.resolve();
  assert.deepEqual(h.metrics, [
    {
      surface: "classic-tab",
      path: "auto-revealed",
      receiptToPaintMs: 2500,
      pagesRefetched: 1,
      count: 2,
    },
  ]);
});
test("showNew empty callback skipscache/metrics; synchronous invalidation error retains source failure", () => {
  const h = harness();
  h.render({ viewer: "v", bufferNewCallouts: true });
  assert.equal(h.render().showNewCallouts(), undefined);
  h.put({ pages: [{ items: [wire("old")] }], pageParams: [undefined] });
  h.event.onNewContent({ id: "a", coinMint: mint });
  const out = h.render(),
    failure = { synthetic: "invalidate" };
  h.cache.setInvalidation(() => {
    throw failure;
  });
  assert.throws(
    () => out.showNewCallouts(),
    (e) => e === failure,
  );
  assert.equal(h.render().pendingNewCount, 0);
});
test("pending resets for viewer/chain identity, not pageSize; throttle restarts on identity change", () => {
  const h = harness();
  h.render({ viewer: "v", bufferNewCallouts: true });
  h.put({ pages: [{ items: [wire("old")] }], pageParams: [undefined] });
  h.event.onNewContent({ id: "a", coinMint: mint });
  assert.equal(h.render().pendingNewCount, 1);
  assert.equal(
    h.render({ viewer: "v", pageSize: 3, bufferNewCallouts: true })
      .pendingNewCount,
    1,
  );
  assert.equal(
    h.render({ viewer: "other", bufferNewCallouts: true }).pendingNewCount,
    0,
  );
  h.event.onNewContent({ id: "b", coinMint: mint });
  assert.ok(h.cache.calls.some((c) => c[0] === "invalidate"));
  assert.equal(
    h.render({ viewer: "other", chain: "near", bufferNewCallouts: true })
      .pendingNewCount,
    0,
  );
});
test("all6 existing1846 helper contexts preserve reused update/time/count and positionfacts", () => {
  for (const v of helperVariants) {
    const h = harness({ normalizerHelpers: createNormalizerHelpers(v.sha256) });
    const out = h.normalizeEntry(
      wire("c", {
        position: { amountHeld: 0, pnlUsd: 5 },
        callout: {
          calloutId: "c",
          updates: [
            { id: "child", parentMessageId: "p", createdAt: "2026-01-01" },
            { id: "root", createdAt: "2026-01-02", content: "x" },
          ],
          updateCount: 8,
        },
      }),
    );
    assert.deepEqual(out.entry.positionPnl, {
      amountHeld: 0,
      valueUsd: undefined,
      pnlUsd: 5,
      pnlPercentage: undefined,
      costBasisUsd: undefined,
      amountBoughtUsd: undefined,
      receiptBasisUsd: undefined,
      realizedPnlUsd: undefined,
      isExited: undefined,
    });
    assert.equal(out.entry.updateCount, 7);
    assert.deepEqual(
      out.entry.updates.map((x) => x.id),
      ["root"],
    );
  }
});
test("full mapping covers callout/update/trade/collectible/reply/quote/repost and omits unsupportedkind", () => {
  const h = harness();
  assert.equal(h.normalizeEntry(wire("c")).type, "callout");
  const callout = {
    coinMint: mint,
    callout: { calloutId: "c", calloutTimestamp: "2026-01-01", updates: [] },
    userId: "cc",
    userName: "name",
  };
  const reply = {
    reply: { id: "r", userId: "cc", content: "hi", createdAt: "2026-01-02" },
    callout,
    parent: null,
  };
  for (const kind of ["reply", "quote"]) {
    const out = h.normalizeEntry({ kind, reply, coinMint: mint });
    assert.equal(out.type, kind);
    assert.equal(out.row.reply.replyId, "r");
  }
  assert.equal(
    h.normalizeEntry({
      kind: "update",
      reply,
      coinMint: mint,
      walletAddress: "author",
    }).key,
    "upd:r",
  );
  const trade = { tx: "tx", isBuy: true, timestamp: "2026-01-01" };
  for (const kind of ["trade", "collectible"]) {
    const out = h.normalizeEntry({
      kind,
      coinMint: mint,
      trade,
      createdAt: "2026-01-02",
    });
    assert.equal(out.type, "trade");
    assert.equal(out.trade, trade);
    assert.equal(out.card, null);
  }
  assert.equal(
    h.normalizeEntry({
      kind: "repost",
      coinMint: mint,
      repost: { id: "rp", callout },
    }).key,
    "repost:rp",
  );
  for (const kind of ["like", "post", "unknown"])
    assert.equal(h.normalizeEntry({ kind }), null);
});
test("both pureimage/classification variants remain explicit and preserve source URI strings only", () => {
  for (const image of imageVariants)
    for (const classification of classificationVariants) {
      const h = harness({
        imageVariant: image.sha256,
        classificationVariant: classification.sha256,
      });
      const out = h.normalizeEntry({
        kind: "collectible",
        coinMint: mint,
        trade: {
          tx: "tx",
          isBuy: false,
          collectible: {
            provider: "phygitals",
            imageUrl: " https://img.phygitals.com/card-cropped ",
            name: " name ",
            grade: " ",
          },
        },
      });
      assert.equal(out.card.name, "name");
      assert.equal(out.card.grade, null);
      assert.ok(
        out.card.image.includes(
          "/cdn-cgi/image/width=512,quality=85,format=auto,fit=scale-down/",
        ),
      );
      assert.ok(
        out.card.image.endsWith(
          encodeURIComponent("https://img.phygitals.com/card-cropped"),
        ),
      );
      assert.equal(h.entryChain(out).perp, false);
    }
});
test("acceptedshape and decoded32 guards are distinct in actualchain/classification paths", () => {
  let decodes = 0;
  const h = harness({ decodeBase58: (value) => (decodes++, decode(value)) }),
    shapeOnly = "z".repeat(44);
  assert.equal(decode(shapeOnly).length, 33);
  const out = h.normalizeEntry(wire("c", { coinMint: shapeOnly }));
  assert.equal(h.entryChain(out).perp, false);
  assert.equal(decodes, 0, "classification does not call decoded guard");
  h.query = {
    data: { pages: [{ items: [wire("c", { coinMint: shapeOnly })] }] },
  };
  assert.deepEqual(h.render({ viewer: "v", chain: "solana" }).rows, []);
  assert.equal(decodes, 1, "chain filter calls actual decoded guard");
});
test("actual loopbackGET receives exact options; HTTP/JSON/cancel failures propagate without cookies", async () => {
  const seen = [];
  let mode = "ok";
  const server = createServer((req, res) => {
    seen.push({ method: req.method, url: req.url, headers: req.headers });
    if (mode === "abort") return;
    res.writeHead(mode === "http" ? 503 : 200, {
      "Content-Type": "application/json",
    });
    res.end(
      mode === "json"
        ? "bad-json"
        : JSON.stringify({ items: [], nextCursor: "next" }),
    );
  });
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  let closed = false;
  try {
    const base = `http://127.0.0.1:${server.address().port}`;
    const h = harness({
      getContractClient: () => async (op, o) => {
        assert.equal(op, "GET /following-positions/alerts");
        const url = new URL("/alerts", base);
        for (const [k, v] of Object.entries(o.query))
          if (v !== undefined)
            url.searchParams.set(k, Array.isArray(v) ? v.join(",") : String(v));
        const response = await fetch(url, {
          method: "GET",
          headers: o.headers,
          signal: o.signal,
          credentials: o.credentials,
        });
        for (const hook of o.hooks.afterResponse)
          await hook({ synthetic: true }, o, response);
        return response.json();
      },
    });
    const plan = h.queryOptions({ viewer: "v", pageSize: 20, chain: "near" });
    assert.deepEqual(
      await plan.queryFn({
        pageParam: "cursor",
        signal: new AbortController().signal,
      }),
      { items: [], nextCursor: "next" },
    );
    mode = "http";
    await assert.rejects(h.readAlerts({}), /Failed to fetch alerts feed: 503/);
    mode = "json";
    await assert.rejects(h.readAlerts({}), SyntaxError);
    mode = "abort";
    const controller = new AbortController(),
      pending = h.readAlerts({ signal: controller.signal }),
      started = Date.now();
    while (seen.length < 4) {
      assert.ok(Date.now() - started < 3000, "finite arrival");
      await new Promise((r) => setTimeout(r, 1));
    }
    controller.abort();
    await assert.rejects(pending, (e) => e.name === "AbortError");
    const url = new URL(seen[0].url, base);
    assert.equal(
      url.searchParams.get("kinds"),
      "callout,update,reply,quote,repost",
    );
    assert.equal(url.searchParams.get("chains"), "near:mainnet");
    assert.equal(url.searchParams.get("cursor"), "cursor");
    assert.equal(url.searchParams.get("minTradeAmountUsd"), "10");
    for (const r of seen) {
      assert.equal(r.method, "GET");
      assert.equal(r.headers.cookie, undefined);
      assert.equal(r.headers.authorization, undefined);
    }
  } finally {
    server.closeAllConnections();
    await new Promise((r) =>
      server.close(() => {
        closed = true;
        r();
      }),
    );
  }
  assert.equal(closed, true);
});
