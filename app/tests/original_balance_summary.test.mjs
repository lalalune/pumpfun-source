import { test } from "node:test";
import assert from "node:assert/strict";
import { createServer } from "node:http";
import { once } from "node:events";
import { readFile, writeFile, mkdtemp, mkdir, cp, rm } from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { createHash } from "node:crypto";
import {
  BalanceSummaryHttpError,
  createBalanceSummaryClient,
  balanceSummaryStatus,
  balanceSummaryRetryAfter,
  parseBalanceSummaryRetryAfter,
  shouldRetryBalanceSummary,
  balanceSummaryRetryDelay,
  balanceSummaryPollInterval,
} from "../packages/frontend/src/original-contracts/balance-summary/client.mjs";
import {
  APP_ROOT,
  OUTPUT,
  verify,
  recover,
} from "../scripts/original-balance-summary.mjs";

const BASE = "https://synthetic.invalid/balance/summary";
const fixedNow = Date.parse("2026-01-01T00:00:00Z");
const make = (options = {}) =>
  createBalanceSummaryClient({
    baseUrl: BASE,
    fetchImplementation: async () => new Response("{}"),
    nowMs: () => fixedNow,
    ...options,
  });
test("source authenticates all six physical readers, exact origin/key provider and real UI handoff", async () => {
  const c = await verify();
  assert.equal(c.readers.length, 6);
  assert.equal(new Set(c.readers.map((r) => r.factory.sha256)).size, 6);
  for (const r of c.readers) {
    assert.equal(r.sourceNodes.length, 11);
    assert.ok(
      r.sourceNodes.every(
        (n) => n.utf16[1] > n.utf16[0] && /^[a-f0-9]{64}$/.test(n.sha256),
      ),
    );
  }
  assert.equal(
    c.provider.sourceNodes[0].text,
    '"https://profile-api.pump.fun"',
  );
  assert.equal(c.provider.sourceNodes[2].text, 'e=>["balanceSummary",e]');
  assert.equal(
    c.caller.sourceNodes.at(-1).text,
    "e5=eY?.success?eY.data:void 0",
  );
  assert.match(c.behavior.method, /default GET/);
});
test("fetch destination/options/subject semantics are explicit, without inferred encoding or query signal", async () => {
  const calls = [],
    value = { success: true, data: { total_value: 12 } };
  const fetchOptions = { headers: { "x-synthetic-case": "source" } };
  const c = make({
    fetchImplementation: async (...args) => {
      calls.push(args);
      return { status: 200, ok: true, json: () => value };
    },
  });
  assert.strictEqual(
    await c.read({
      userAddress: "a/b?existing=1",
      multiChain: true,
      fetchOptions,
    }),
    value,
  );
  assert.deepEqual(calls[0], [
    BASE + "/a/b?existing=1&multi_chain=true",
    fetchOptions,
  ]);
  await c.read({ userAddress: "雪 space", multiChain: false });
  assert.equal(calls[1][0], BASE + "/%E9%9B%AA%20space");
  assert.equal(calls[1][1], undefined);
  const ignored = new AbortController();
  ignored.abort();
  await c
    .queryOptions({ userAddress: "a" })
    .queryFn({ signal: ignored.signal });
  assert.equal(calls[2][1], undefined);
  assert.equal(calls[2][0], BASE + "/a?multi_chain=true");
  assert.throws(
    () => createBalanceSummaryClient({ fetchImplementation: fetch }),
    /explicit/,
  );
  assert.throws(() => make({ fetchImplementation: undefined }), /explicit/);
});
test("success returns raw decoded JSON, with no schema/success/shape repair; transport and JSON failures propagate", async () => {
  for (const value of [
    null,
    [],
    { success: false },
    5,
    "raw",
    { data: { native_balance: -5 } },
  ]) {
    assert.strictEqual(
      await make({
        fetchImplementation: async () => ({
          status: 200,
          ok: true,
          json: () => value,
        }),
      }).read({ userAddress: "a" }),
      value,
    );
  }
  const marker = Error("synthetic transport");
  await assert.rejects(
    make({
      fetchImplementation: async () => {
        throw marker;
      },
    }).read({ userAddress: "a" }),
    (e) => e === marker,
  );
  await assert.rejects(
    make({ fetchImplementation: async () => new Response("{") }).read({
      userAddress: "a",
    }),
    SyntaxError,
  );
});
test("401/other errors do not consume body; only429 reads retry header/clock", async () => {
  const events = [];
  for (const status of [401, 403, 503, 429]) {
    const c = make({
      nowMs: () => {
        events.push("clock");
        return fixedNow;
      },
      fetchImplementation: async () => ({
        status,
        ok: false,
        headers: {
          get: (name) => {
            events.push(name);
            return "120";
          },
        },
        json: () => assert.fail("error body must not be decoded"),
        text: () => assert.fail("error body must not be consumed"),
      }),
    });
    await assert.rejects(c.read({ userAddress: "a" }), (e) => {
      assert.ok(e instanceof BalanceSummaryHttpError);
      assert.equal(e.name, "BalanceSummaryHttpError");
      assert.deepEqual(Object.keys(e), ["status", "retryAfterMs", "name"]);
      assert.equal(e.status, status);
      assert.equal(
        e.message,
        status === 401
          ? "Unauthorized"
          : `Failed to fetch wallet summary (${status})`,
      );
      assert.equal(e.retryAfterMs, status === 429 ? 120000 : undefined);
      return true;
    });
  }
  assert.deepEqual(events, ["retry-after", "clock"]);
});
test("Retry-After numeric/date grammar retains zero, past dates, overflow and invalid distinctions", () => {
  for (const [header, expected] of [
    [null, undefined],
    ["", undefined],
    [" 0 ", 0],
    ["-0", -0],
    ["-1", undefined],
    ["5", 5000],
    ["bad", undefined],
    ["Thu, 01 Jan 2026 00:00:03 GMT", 3000],
    ["Wed, 31 Dec 2025 23:59:59 GMT", 0],
  ])
    assert.equal(parseBalanceSummaryRetryAfter(header, fixedNow), expected);
  assert.equal(
    parseBalanceSummaryRetryAfter("9".repeat(400), fixedNow),
    Infinity,
  );
  const overflow = new BalanceSummaryHttpError("x", 429, {
    retryAfterMs: Infinity,
  });
  assert.equal(balanceSummaryRetryAfter(overflow), undefined);
  assert.equal(balanceSummaryRetryDelay(0, overflow), 5000);
});
test("finite error property admission and exact retry/delay/polling policies", () => {
  for (const value of [
    null,
    undefined,
    1,
    "401",
    () => 0,
    { status: "401" },
    { status: Infinity },
  ])
    assert.equal(balanceSummaryStatus(value), undefined);
  assert.equal(balanceSummaryStatus({ status: 0 }), 0);
  assert.equal(shouldRetryBalanceSummary(0, { status: 401 }), false);
  assert.equal(shouldRetryBalanceSummary(1, { status: 503 }), true);
  assert.equal(shouldRetryBalanceSummary(2, Error("transport")), false);
  assert.equal(shouldRetryBalanceSummary(0, { status: "401" }), true);
  assert.deepEqual(
    [0, 1, 5, 100].map((n) => balanceSummaryRetryDelay(n, { status: 503 })),
    [1000, 2000, 30000, 30000],
  );
  assert.equal(
    balanceSummaryRetryDelay(0, { status: 429, retryAfterMs: 0 }),
    0,
  );
  assert.equal(
    balanceSummaryRetryDelay(0, { status: 429, retryAfterMs: 120000 }),
    60000,
  );
  assert.equal(balanceSummaryRetryDelay(2, { status: 429 }), 15000);
  for (const [status, data, expected] of [
    ["success", { success: true }, 60000],
    ["success", { success: 1 }, 15000],
    ["pending", { success: true }, 15000],
    ["error", undefined, 15000],
    ["success", null, 15000],
  ])
    assert.equal(
      balanceSummaryPollInterval({ state: { status, data } }),
      expected,
    );
});
test("query hook preserves memo identities/captured callbacks and last-spread overrides through injected ports", async () => {
  const cache = Array(7).fill(Symbol("uninitialized")),
    seen = [],
    calls = [];
  const c = make({
    memo: (slots) => {
      assert.equal(slots, 7);
      return cache;
    },
    useQuery: (options) => {
      seen.push(options);
      return options;
    },
    fetchImplementation: async (url, init) => {
      calls.push([url, init]);
      return new Response("{}");
    },
  });
  const fetchOptions = { headers: { "x-synthetic-case": "memo" } };
  const a = c.useBalanceSummary({ userAddress: "alice", fetchOptions });
  assert.strictEqual(
    c.useBalanceSummary({ userAddress: "alice", fetchOptions }),
    a,
  );
  assert.deepEqual(a.queryKey, ["balanceSummary", "alice"]);
  assert.equal(a.staleTime, Infinity);
  assert.equal(a.refetchOnMount, true);
  assert.equal(a.refetchOnWindowFocus, true);
  assert.equal(a.refetchOnReconnect, true);
  c.useBalanceSummary({ userAddress: "bob", fetchOptions });
  await a.queryFn();
  assert.equal(calls[0][0], BASE + "/alice?multi_chain=true");
  assert.strictEqual(calls[0][1], fetchOptions);
  assert.equal(c.useBalanceSummary({ userAddress: "" }).enabled, false);
  const replacement = () => 1,
    overrides = {
      enabled: true,
      staleTime: 9,
      queryFn: replacement,
      refetchInterval: 17,
    };
  const result = c.useBalanceSummary({
    userAddress: "",
    queryOptions: overrides,
  });
  assert.equal(result.enabled, true);
  assert.equal(result.staleTime, 9);
  assert.strictEqual(result.queryFn, replacement);
  assert.equal(result.refetchInterval, 17);
  assert.strictEqual(
    c.useBalanceSummary({ userAddress: "", queryOptions: overrides }),
    result,
  );
  assert.throws(() => make().useBalanceSummary({ userAddress: "x" }), /ports/);
});
test("real synthetic loopback HTTP binds request/JSON/errors/abort without live provider or automatic retries", async (t) => {
  const wire = [],
    requests = [];
  let notifySlow;
  const slowArrived = new Promise((resolve) => {
    notifySlow = resolve;
  });
  const server = createServer((req, res) => {
    requests.push({
      method: req.method,
      pathAndQuery: req.url,
      syntheticHeader: req.headers["x-synthetic-case"] ?? null,
    });
    const mode = req.url.split("/")[3]?.split("?")[0];
    res.setHeader("content-type", "application/json");
    if (mode === "slow") {
      notifySlow();
      return;
    }
    if (mode === "unauthorized") {
      res.statusCode = 401;
      return res.end('{"synthetic":"denied"}');
    }
    if (mode === "limited") {
      res.statusCode = 429;
      res.setHeader("retry-after", "120");
      return res.end('{"synthetic":"limited"}');
    }
    if (mode === "failed") {
      res.statusCode = 503;
      return res.end('{"synthetic":"unavailable"}');
    }
    if (mode === "empty") {
      res.statusCode = 204;
      return res.end();
    }
    if (mode === "invalid") return res.end("{");
    if (mode === "false")
      return res.end('{"success":false,"data":{"total_value":88}}');
    res.end(
      '{"success":true,"data":{"native_balance":2,"total_value":7},"unvalidated":"retained"}',
    );
  });
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  t.after(() => {
    server.closeAllConnections();
    server.close();
  });
  const c = make({
    baseUrl: `http://127.0.0.1:${server.address().port}/balance/summary`,
    fetchImplementation: async (url, init) => {
      const request = new Request(url, init);
      const response = await fetch(request);
      wire.push({
        request: {
          method: request.method,
          pathAndQuery: new URL(url).pathname + new URL(url).search,
          credentials: request.credentials,
          syntheticHeader: request.headers.get("x-synthetic-case"),
        },
        response: {
          status: response.status,
          contentType: response.headers.get("content-type"),
          retryAfter: response.headers.get("retry-after"),
          body: await response.clone().text(),
        },
      });
      return response;
    },
  });
  const got = await c
    .queryOptions({
      userAddress: "ok",
      fetchOptions: { headers: { "x-synthetic-case": "loopback" } },
    })
    .queryFn();
  assert.equal(got.data.total_value, 7);
  assert.equal(got.unvalidated, "retained");
  assert.equal((await c.read({ userAddress: "false" })).success, false);
  for (const mode of ["unauthorized", "limited", "failed"])
    await assert.rejects(
      c.read({ userAddress: mode }),
      BalanceSummaryHttpError,
    );
  for (const mode of ["empty", "invalid"])
    await assert.rejects(c.read({ userAddress: mode }), SyntaxError);
  const controller = new AbortController(),
    pending = c.read({
      userAddress: "slow",
      fetchOptions: { signal: controller.signal },
    });
  await slowArrived;
  controller.abort();
  await assert.rejects(pending, (e) => e.name === "AbortError");
  assert.equal(wire.length, 7);
  assert.equal(requests.length, 8);
  assert.equal(
    wire[0].request.pathAndQuery,
    "/balance/summary/ok?multi_chain=true",
  );
  assert.equal(wire[0].request.credentials, "same-origin");
  assert.ok(requests.every((r) => r.method === "GET"));
  if (process.env.PUMP_BALANCE_SUMMARY_WIRE_OUTPUT)
    await writeFile(
      process.env.PUMP_BALANCE_SUMMARY_WIRE_OUTPUT,
      JSON.stringify(
        {
          provenance:
            "Explicit synthetic loopback; no original server/accounting/auth or production traffic",
          normalization:
            "Ephemeral loopback origin omitted; ordered method/path/query/selected synthetic header/status/body retained",
          completedResponses: wire.length,
          abortedRequests: 1,
          wire,
          requests,
        },
        null,
        2,
      ) + "\n",
    );
});
test("source verification rejects resealed raw changes and noncanonical contract bytes", async (t) => {
  const root = await mkdtemp(path.join(os.tmpdir(), "balance-summary-audit-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  await mkdir(path.join(root, "evidence/web/objects"), { recursive: true });
  await mkdir(path.join(root, "recovered"));
  await cp(
    path.join(APP_ROOT, "evidence/web/manifest.json"),
    path.join(root, "evidence/web/manifest.json"),
  );
  await cp(
    path.join(APP_ROOT, "recovered/modules.json"),
    path.join(root, "recovered/modules.json"),
  );
  const c = await recover();
  const sources = new Set([
    ...c.readers.map((r) => r.factory.source),
    c.provider.factory.source,
    c.caller.factory.source,
  ]);
  for (const source of sources)
    await cp(path.join(APP_ROOT, source), path.join(root, source));
  await mkdir(path.dirname(path.join(root, OUTPUT)), { recursive: true });
  const original = await readFile(path.join(APP_ROOT, OUTPUT));
  await writeFile(
    path.join(root, OUTPUT),
    Buffer.concat([original, Buffer.from(" ")]),
  );
  await assert.rejects(verify(root), /contract bytes differ/);
  await writeFile(path.join(root, OUTPUT), original);
  const source = c.readers[0].factory.source;
  const bytes = await readFile(path.join(root, source));
  await writeFile(
    path.join(root, source),
    Buffer.concat([bytes, Buffer.from(" ")]),
  );
  await assert.rejects(recover(root), /capture authentication failed/);
  const originalText = bytes.toString("utf8"),
    changedText = originalText.replace("401===", "402===");
  assert.notEqual(changedText, originalText);
  const changed = Buffer.from(changedText);
  const hash = (v) => createHash("sha256").update(v).digest("hex");
  await writeFile(path.join(root, source), changed);
  const manifestPath = path.join(root, "evidence/web/manifest.json"),
    manifest = JSON.parse(await readFile(manifestPath));
  manifest.records.find((r) => r.path === source).sha256 = hash(changed);
  await writeFile(manifestPath, JSON.stringify(manifest));
  const indexPath = path.join(root, "recovered/modules.json"),
    index = JSON.parse(await readFile(indexPath));
  const variant = index.modules.find(
    (v) => v.sha256 === c.readers[0].factory.sha256,
  );
  const origin = variant.origins.find((o) => o.source === source);
  variant.sha256 = hash(
    Buffer.from(changedText.slice(origin.start, origin.end)),
  );
  await writeFile(indexPath, JSON.stringify(index));
  await assert.rejects(recover(root), /review required: changed factory/);
});
