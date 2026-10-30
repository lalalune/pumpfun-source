import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import { test } from "node:test";

const app = process.env.PUMP_OBSERVATION_TEST_APP ?? fileURLToPath(new URL("../", import.meta.url));
const requireBackend = createRequire(join(app, "packages/backend/package.json"));
const { require: requireTs } = requireBackend("tsx/cjs/api");
const load = (name) => requireTs(join(app, "packages/frontend/src/app", name), import.meta.url);
const { readPortfolioWithRpc } = load("portfolio/rpc.ts");
const { isPortfolioResponse, MAINNET_GENESIS_HASH } = load("portfolio/types.ts");
const { readWalletRecordWithRpc } = load("wallet-program-record/server.ts");
const { isWalletRecord } = load("wallet-program-record/client.ts");
const { readHolderConfigurationWithRpc } = load("holder-rewards-config/server.ts");
const { isHolderConfiguration } = load("holder-rewards-config/client.ts");
const ADDRESS = "So11111111111111111111111111111111111111112";
const invalid = ["0", "10/30/2026", "2026-02-30T00:00:00.000Z", "2026-04-31T12:00:00.000Z", "2026-01-01T24:00:00Z", "2026-10-30T00:00:00"];
const valid = ["2026-10-30T00:00:00Z", "2026-10-30T00:00:00.1Z", "2026-10-30T00:00:00.12Z", "2026-10-30T00:00:00.123Z", "2026-10-30T00:00:00.123456Z", "2026-10-30T00:00:00+00:00", "2026-10-30T00:00:00-05:00", "2024-02-29T00:00:00Z"];

test("actual public read producers over loopback HTTP retain valid observation instants only", async (t) => {
  let origin;
  const rpc = async (method, params, signal) => {
    const response = await fetch(`${origin}/rpc`, { method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", id: 1, method, params }), signal });
    return (await response.json()).result;
  };
  const reads = [];
  const server = createServer(async (request, response) => {
    try {
      if (request.url === "/rpc") {
        let text = ""; for await (const chunk of request) text += chunk;
        const message = JSON.parse(text); reads.push(message.method);
        let result;
        if (message.method === "getGenesisHash") result = MAINNET_GENESIS_HASH;
        else if (message.method === "getBalance") result = { context: { slot: 321 }, value: 0 };
        else if (message.method === "getTokenAccountsByOwner") result = { context: { slot: 321 }, value: [] };
        else if (message.method === "getAccountInfo") result = { context: { slot: 321 }, value: null };
        else if (message.method === "getMultipleAccounts") result = { context: { slot: 321 }, value: [null, null] };
        else throw new Error("Unsupported local fixture method");
        response.writeHead(200, { "content-type": "application/json" }); response.end(JSON.stringify({ jsonrpc: "2.0", id: 1, result }));
        return;
      }
      const value = request.url === "/portfolio" ? await readPortfolioWithRpc(ADDRESS, rpc, "public-rpc.example")
        : request.url === "/record" ? await readWalletRecordWithRpc(ADDRESS, rpc, "public-rpc.example")
        : await readHolderConfigurationWithRpc(ADDRESS, rpc, "public-rpc.example");
      response.writeHead(200, { "content-type": "application/json" }); response.end(JSON.stringify(value));
    } catch (error) { response.writeHead(500); response.end(String(error)); }
  });
  try {
    await new Promise((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
    origin = `http://127.0.0.1:${server.address().port}`;
    for (const [name, guard] of [["portfolio", (value) => isPortfolioResponse(value, ADDRESS)],
      ["record", (value) => isWalletRecord(value, ADDRESS)],
      ["configuration", (value) => isHolderConfiguration(value, ADDRESS, value.holderRewardsPda)]]) {
      await t.test(name, async () => {
        const response = await fetch(`${origin}/${name}`);
        assert.equal(response.status, 200, await response.clone().text());
        const genuine = await response.json();
        assert.equal(guard(genuine), true, "unchanged actual producer output");
        assert.match(genuine.observedAt, /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/);
        assert.deepEqual(valid.map((observedAt) => guard({ ...genuine, observedAt })), valid.map(() => true));
        assert.deepEqual(invalid.map((observedAt) => guard({ ...genuine, observedAt })), invalid.map(() => false));
      });
    }
    assert.equal(reads.filter((name) => name === "getGenesisHash").length, 3);
  } finally {
    await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
  }
});
