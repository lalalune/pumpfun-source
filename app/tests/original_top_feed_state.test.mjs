import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { once } from "node:events";
import {
  createTopFeedRead,
  ownerVariants,
  readContexts,
  toFeedRows,
} from "../reconstruction/top-feed-state/client.mjs";
import {
  createHelperPorts,
  helperVariants,
} from "../reconstruction/top-feed-state/qualification/helper-ports.mjs";
import { derive, verify } from "../scripts/original-top-feed-state.mjs";
const root = new URL("../", import.meta.url).pathname,
  frontend = createRequire(
    new URL("../packages/frontend/package.json", import.meta.url),
  ),
  decode = createRequire(frontend.resolve("@solana/web3.js"))("bs58").decode,
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
function harness(extra = {}) {
  const slots = Array(16).fill(Symbol.for("react.memo_cache_sentinel")),
    requests = [],
    queries = [];
  let snapshot = {
    data: undefined,
    isPending: false,
    isError: false,
    refetch() {
      return Promise.resolve();
    },
  };
  const api = createTopFeedRead({
    ownerVariant: ownerVariants[0].sha256,
    readContext: readContexts[0].reader,
    useMemoCache: (n) => (assert.equal(n, 16), slots),
    useQuery: (o) => (queries.push(o), snapshot),
    getContractClient:
      () =>
      async (...args) => (requests.push(args), { entries: [] }),
    ...createHelperPorts(helperVariants[0].normalizer),
    decodeBase58: decode,
    ...extra,
  });
  return {
    ...api,
    requests,
    queries,
    set query(v) {
      snapshot = { ...snapshot, ...v };
    },
    get options() {
      return queries.at(-1);
    },
  };
}
test("complete source95witnesses22entries and retained variants authenticate", async () =>
  assert.deepEqual(await verify(root), {
    witnesses: 95,
    sourceEntries: 22,
    ownerVariants: 2,
    readContexts: 2,
    qualificationHelperVariants: 6,
    mounted: false,
    productionOperationsQualified: 0,
  }));
test("real verifier rejects actual owner/reader/contract/fixture tampering", async () => {
  const d = await derive(root),
    changes = [
      { code: d.code.replace("staleTime: 3e5", "staleTime: 0") },
      { code: d.code.replace('credentials: "include"', 'credentials: "omit"') },
      {
        code: d.code.replace(
          "refetchOnWindowFocus: !0",
          "refetchOnWindowFocus: !1",
        ),
      },
      { fixture: d.fixture + "\n// changed\n" },
      { contract: { ...d.contract, witnesses: [] } },
      { contract: { ...d.contract, readContexts: [] } },
      { contract: { ...d.contract, productionOperationsQualified: 1 } },
    ];
  for (const x of changes) {
    if (x.code !== undefined) assert.notEqual(x.code, d.code);
    await assert.rejects(verify(root, x));
  }
});
test("exact required capabilities and explicit own-key physical variants", () => {
  assert.throws(() => createTopFeedRead({}), /capabilities/);
  for (const key of [
    "constructor",
    "__proto__",
    undefined,
    {},
    new String(ownerVariants[0].sha256),
  ])
    assert.throws(() => harness({ ownerVariant: key }), /supported/);
  assert.throws(() => harness({ readContext: "constructor" }), /supported/);
});
for (const context of readContexts)
  test(
    "full reader " +
      context.reader.slice(0, 12) +
      " retains source options/return and factoryorder",
    async () => {
      let factories = 0;
      const payload = { unvalidated: true },
        signal = new AbortController().signal,
        h = harness({
          readContext: context.reader,
          getContractClient: () => {
            factories++;
            return async (op, o) => {
              assert.equal(factories, 1);
              assert.equal(op, "GET /pnl-leaderboard/positions");
              assert.deepEqual(o.query, { period: "daily" });
              assert.deepEqual(o.headers, {
                "Content-Type": "application/json",
              });
              assert.equal(o.credentials, "include");
              assert.equal(o.signal, signal);
              assert.equal("body" in o, false);
              return payload;
            };
          },
        });
      assert.equal(await h.readPositions({ signal }), payload);
    },
  );
test("reader keeps falsey/truthy options, limit5 and plain error identity/message", async () => {
  const h = harness();
  await h.readPositions({ period: null, includeFollowedHolders: "truthy" });
  let options = h.requests[0][1];
  assert.deepEqual(options.query, {
    period: null,
    includeFollowedHolders: true,
    followedHoldersLimit: 5,
  });
  assert.throws(
    () =>
      options.hooks.afterResponse[0](
        null,
        null,
        new Response("{}", { status: 403 }),
      ),
    (e) =>
      e.constructor === Error &&
      e.message === "Failed to fetch pnl leaderboard: 403",
  );
  await h.readPositions({ period: "weekly", includeFollowedHolders: 0 });
  assert.deepEqual(h.requests[1][1].query, { period: "weekly" });
});
for (const variant of ownerVariants)
  test(
    "full16slot owner " +
      variant.sha256.slice(0, 12) +
      " defaults/query policies/prefetch",
    async () => {
      const h = harness({ ownerVariant: variant.sha256 });
      let out = h.useTopFeed();
      assert.deepEqual(h.options.queryKey, [
        "callouts",
        "top-feed",
        "daily",
        false,
      ]);
      assert.equal(h.options.enabled, true);
      assert.equal(h.options.refetchOnWindowFocus, true);
      assert.equal(h.options.staleTime, 300000);
      assert.equal(h.options.retry, 3);
      const signal = new AbortController().signal;
      await h.options.queryFn({ signal });
      assert.equal(h.requests[0][1].signal, signal);
      assert.equal(out.pendingNewCount, 0);
      assert.deepEqual(out.pendingPreview, []);
      assert.equal(out.hasNextPage, false);
      assert.equal(out.isFetchingNextPage, false);
      assert.equal(out.fetchNextPage(), undefined);
      assert.equal(out.showNewCallouts(), undefined);
      const result = {},
        calls = [];
      assert.equal(
        h.prefetchTopFeed({
          prefetchQuery(o) {
            calls.push(o);
            return result;
          },
        }),
        result,
      );
      assert.deepEqual(calls[0].queryKey, [
        "callouts",
        "top-feed",
        "daily",
        false,
      ]);
      h.prefetchTopFeed(
        { prefetchQuery: (o) => calls.push(o) },
        { includeFollowedHolders: true, period: "weekly" },
      );
      assert.deepEqual(calls[1].queryKey, [
        "callouts",
        "top-feed",
        "daily",
        true,
      ]);
    },
  );
test("undefined-only defaults and actual raw enabled/loading semantics retained", () => {
  const h = harness();
  h.query = { isPending: true };
  const input = { enabled: null, includeFollowedHolders: null, period: null },
    out = h.useTopFeed(input);
  assert.equal(h.options.enabled, null);
  assert.deepEqual(h.options.queryKey, ["callouts", "top-feed", null, null]);
  assert.equal(out.isLoadingHistory, null);
});
test("mapped invalids omitted, first valid key wins; output order and row handoff identity", () => {
  const h = harness(),
    first = wire("a"),
    second = wire("b");
  h.query = {
    data: {
      entries: [
        wire("bad", { coinMint: "bad" }),
        wire("a", { callout: null }),
        first,
        wire("a", { username: "ignored" }),
        second,
      ],
    },
  };
  const out = h.useTopFeed();
  assert.deepEqual(
    out.callouts.map((x) => x.key),
    ["cid:a", "cid:b"],
  );
  const rows = toFeedRows(out.callouts);
  assert.deepEqual(
    rows.map((x) => ({ type: x.type, key: x.key, createdAtMs: x.createdAtMs })),
    out.callouts.map((x) => ({
      type: "callout",
      key: x.key,
      createdAtMs: x.createdAt,
    })),
  );
  assert.equal(rows[0].entry, out.callouts[0]);
});
test("compiler memo compares entries reference, preserving source in-place-mutation quirk", () => {
  const h = harness(),
    entries = [wire("a")],
    input = {};
  h.query = { data: { entries } };
  const a = h.useTopFeed(input);
  assert.equal(h.useTopFeed(input), a);
  entries.push(wire("b"));
  h.query = { data: { entries } };
  assert.equal(h.useTopFeed(input).callouts, a.callouts);
  assert.equal(a.callouts.length, 1);
  h.query = { data: { entries: [...entries] } };
  assert.equal(h.useTopFeed(input).callouts.length, 2);
});
test("source error condition depends on mapped-row emptiness and loading respects enable", () => {
  const h = harness();
  h.query = {
    data: { entries: [wire("invalid", { callout: null })] },
    isError: true,
    isPending: true,
  };
  let out = h.useTopFeed({ enabled: false });
  assert.equal(out.error, "Could not load top callouts");
  assert.equal(out.isLoadingHistory, false);
  h.query = { data: { entries: [wire("a")] } };
  out = h.useTopFeed({ enabled: true });
  assert.equal(out.error, null);
  assert.equal(out.isLoadingHistory, true);
});
test("refetch retains query receiver, discards returned promise, propagates synchronous failure", () => {
  const h = harness();
  let receiver;
  const promise = Promise.resolve("synthetic");
  h.query = {
    refetch() {
      receiver = this;
      return promise;
    },
  };
  const out = h.useTopFeed();
  assert.equal(out.refetch(), undefined);
  assert.equal(receiver.data, undefined);
  assert.equal(typeof receiver.refetch, "function");
  const failure = { synthetic: true };
  h.query = {
    refetch() {
      throw failure;
    },
  };
  assert.throws(
    () => h.useTopFeed().refetch(),
    (e) => e === failure,
  );
});
test("username author exclusion keeps identity/count policy in both matched reader contexts", () => {
  for (const r of readContexts) {
    const h = harness({ readContext: r.reader }),
      sameHolder = { holders: [{ username: "Other" }], totalCount: 8 };
    assert.equal(
      h.mapEntry(wire("a", { followedHolders: sameHolder })).followedHolders,
      sameHolder,
    );
    const mixed = {
      holders: [{ username: "ALICE" }, { username: "other" }],
      totalCount: 1,
    };
    assert.deepEqual(
      h.mapEntry(wire("b", { followedHolders: mixed })).followedHolders,
      { holders: [{ username: "other" }], totalCount: 1 },
    );
    assert.equal(
      "followedHolders" in
        h.mapEntry(
          wire("c", {
            followedHolders: {
              holders: [{ username: "alice" }],
              totalCount: 9,
            },
          }),
        ),
      false,
    );
  }
});
test("all six prior1846 helper contexts preserve timestamp/engagement/update-count ports", () => {
  for (const v of helperVariants) {
    const h = harness(createHelperPorts(v.normalizer)),
      out = h.mapEntry(
        wire("a", {
          callout: {
            calloutId: "a",
            thesis: " n ",
            calloutTimestamp: "2026-01-01",
            likes: 0,
            replyCount: null,
            hasLiked: false,
            hasReposted: "wrong",
            updates: [
              { id: "child", parentMessageId: "p" },
              { id: "root", createdAt: "2026-01-01", content: "root" },
            ],
            updateCount: 9,
          },
        }),
      );
    assert.equal(out.createdAt, Date.parse("2026-01-01"));
    assert.equal(out.likeCount, 0);
    assert.equal(out.likedByViewer, false);
    assert.equal("replyCount" in out, false);
    assert.equal("repostedByViewer" in out, false);
    assert.deepEqual(
      out.updates.map((x) => x.id),
      ["root"],
    );
    assert.equal(out.updateCount, 8);
  }
});
test("mapper preserves exact null/undefined/media/metadata/raw field behavior and decoded admission", () => {
  const h = harness();
  assert.equal(h.mapEntry(wire("a", { callout: null })), null);
  assert.equal(
    h.mapEntry(wire("a", { callout: { calloutId: null, thesis: "x" } })),
    null,
  );
  assert.equal(
    h.mapEntry(wire("a", { callout: { calloutId: "a", thesis: " " } })),
    null,
  );
  assert.equal(h.mapEntry(wire("a", { coinMint: "z".repeat(44) })), null);
  const out = h.mapEntry(
    wire("a", {
      walletAddress: " raw ",
      username: "",
      isViewer: true,
      viewerFollows: false,
      callout: {
        thesis: " n ",
        mediaUrl: " ",
        multiple: null,
        calledOutAtMcap: 0,
        updates: [],
      },
    }),
  );
  assert.equal(out.key, "cid:undefined");
  assert.equal(out.userId, " raw ");
  assert.equal(out.note, "n");
  assert.equal(out.mediaUrl, " ");
  assert.equal(out.marketCapUsd, 0);
  assert.equal(out.multiple, 0);
  assert.equal(out.username, undefined);
  assert.equal(out.isViewer, true);
  assert.equal(out.viewerFollows, false);
});
test("real loopbackGET success/status/JSON/cancel retain response and no Cookie/Authorization", async () => {
  let mode = "ok";
  const seen = [],
    server = createServer((req, res) => {
      seen.push({ method: req.method, url: req.url, headers: req.headers });
      if (mode === "abort") return;
      res.writeHead(mode === "status" ? 503 : 200, {
        "Content-Type": "application/json",
      });
      res.end(
        mode === "json"
          ? "bad-json"
          : JSON.stringify({ entries: [wire("a")], totalRanked: 1 }),
      );
    });
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  let closed = false;
  try {
    const origin = `http://127.0.0.1:${server.address().port}`,
      h = harness({
        getContractClient: () => async (op, o) => {
          assert.equal(op, "GET /pnl-leaderboard/positions");
          const url = new URL("/positions", origin);
          for (const [k, v] of Object.entries(o.query))
            url.searchParams.set(k, String(v));
          const response = await fetch(url, {
            method: "GET",
            headers: o.headers,
            signal: o.signal,
            credentials: o.credentials,
          });
          for (const hook of o.hooks.afterResponse) await hook({}, o, response);
          return response.json();
        },
      });
    const options = h.queryOptions({
        period: "weekly",
        includeFollowedHolders: true,
      }),
      body = await options.queryFn({ signal: new AbortController().signal });
    assert.equal(body.totalRanked, 1);
    assert.equal(h.mapEntry(body.entries[0]).key, "cid:a");
    mode = "status";
    await assert.rejects(
      h.readPositions({}),
      /Failed to fetch pnl leaderboard: 503/,
    );
    mode = "json";
    await assert.rejects(h.readPositions({}), SyntaxError);
    mode = "abort";
    const controller = new AbortController(),
      pending = h.readPositions({ signal: controller.signal }),
      started = Date.now();
    while (seen.length < 4) {
      assert.ok(Date.now() - started < 3000);
      await new Promise((r) => setTimeout(r, 1));
    }
    controller.abort();
    await assert.rejects(pending, (e) => e.name === "AbortError");
    assert.equal(
      new URL(seen[0].url, origin).searchParams.get("followedHoldersLimit"),
      "5",
    );
    assert.equal(
      new URL(seen[0].url, origin).searchParams.get("period"),
      "weekly",
    );
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
