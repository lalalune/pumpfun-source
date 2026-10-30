import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import { test } from "node:test";

const app = process.env.PUMP_CREATOR_PAGE_TEST_APP ?? fileURLToPath(new URL("../", import.meta.url));
const requireBackend = createRequire(join(app, "packages/backend/package.json"));
const { require: requireTs } = requireBackend("tsx/cjs/api");
const { PayoutsStore } = requireTs(join(app, "packages/backend/src/payouts-store.ts"), import.meta.url);
const { normalizeUpstreamResponse, UpstreamValidationError } = requireTs(join(app, "packages/frontend/src/app/api/leaderboard/upstream.ts"), import.meta.url);
const { parseLeaderboardResponse } = requireTs(join(app, "packages/frontend/src/app/leaderboard/types.ts"), import.meta.url);
const { creatorPagination } = requireTs(join(app, "packages/frontend/src/app/leaderboard/creator-pagination.ts"), import.meta.url);
const instant = "2026-10-29T00:00:00.000Z";
const makeStore = (count) => new PayoutsStore({ schemaVersion: 1, dataSource: "synthetic", observedAt: instant,
  generatedAt: instant, owners: [], windows: {}, payouts: Array.from({ length: count }, (_, index) => ({
    id: `payout-${index}`, wallet: `wallet-${index}`, amountAtomic: String(100000 + index),
    status: "confirmed", paidAt: "2026-10-28T00:00:00.000Z",
  })) });
const stores = new Map([[41, makeStore(41)], [550, makeStore(550)], [0, makeStore(0)]]);
const envelope = (data) => ({ ok: true, data, source: { mode: "developer-api", label: "Pump developer API", fetchedAt: instant } });

test("actual payout producer pages keep their total, slice and cap consistent across HTTP", async (t) => {
  const server = createServer(async (request, response) => {
    const url = new URL(request.url, "http://localhost");
    const page = Number(url.searchParams.get("page") ?? 1);
    const store = stores.get(Number(url.searchParams.get("count") ?? 41));
    const raw = store.leaderboard({ page: page - 1, pageSize: 20 });
    if (url.searchParams.has("sparse")) raw.entries = raw.entries.slice(0, 3);
    let body = raw;
    if (url.pathname === "/normalized") body = envelope(normalizeUpstreamResponse("creators", raw, { page, competitionId: null }));
    if (url.searchParams.has("total")) {
      const selected = url.pathname === "/normalized" ? body.data : body;
      selected.totalEarners = Number(url.searchParams.get("total"));
    }
    response.writeHead(200, { "content-type": "application/json" }); response.end(JSON.stringify(body));
  });
  try {
    await new Promise((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
    const origin = `http://127.0.0.1:${server.address().port}`;
    const read = async (path) => (await fetch(origin + path)).json();
    await t.test("genuine pages, sparse pages, empty pages and the 500-row cap remain accepted", async () => {
      for (const [count, page, length] of [[41, 1, 20], [41, 3, 1], [41, 4, 0], [550, 25, 20], [550, 26, 0], [550, Number.MAX_SAFE_INTEGER, 0], [0, 1, 0]]) {
        const raw = await read(`/raw?count=${count}&page=${page}`);
        assert.equal(raw.entries.length, length);
        const data = normalizeUpstreamResponse("creators", raw, { page, competitionId: null });
        assert.equal(parseLeaderboardResponse(envelope(data)).ok, true);
        assert.equal(data.totalEarners, count);
        assert.equal(creatorPagination(data).totalPages, Math.max(1, Math.ceil(Math.min(count, 500) / 20)));
      }
      const sparse = await read("/raw?count=41&page=1&sparse=1");
      const data = normalizeUpstreamResponse("creators", sparse, { page: 1, competitionId: null });
      assert.equal(parseLeaderboardResponse(envelope(data)).data.entries.length, 3);
    });
    await t.test("upstream entries cannot exceed the supplied selected slice", async () => {
      for (const [page, total] of [[1, 0], [1, 1], [2, 21], [3, 40]]) {
        const raw = await read(`/raw?count=41&page=${page}&total=${total}`);
        assert.throws(() => normalizeUpstreamResponse("creators", raw, { page, competitionId: null }), UpstreamValidationError);
      }
    });
    await t.test("the client response boundary rejects the same inconsistent metadata", async () => {
      for (const [page, total] of [[1, 0], [1, 1], [2, 21], [3, 40]]) {
        const response = await read(`/normalized?count=41&page=${page}&total=${total}`);
        assert.throws(() => parseLeaderboardResponse(response), /invalid response/);
      }
    });
  } finally {
    await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
  }
});
