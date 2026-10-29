import assert from "node:assert/strict";
import test, { type TestContext } from "node:test";
import dns from "node:dns/promises";
import https from "node:https";
import { EventEmitter, getEventListeners } from "node:events";
import { createRequire, syncBuiltinESMExports } from "node:module";

// Maintained application modules only; no captured JavaScript or live transport.
const require = createRequire(import.meta.url);
const { createPinnedRpcCall, readLivePortfolio, PortfolioRpcError } =
  require("../../frontend/src/app/portfolio/rpc.ts") as typeof import("../../frontend/src/app/portfolio/rpc.js");
const { readLiveWalletRecord } =
  require("../../frontend/src/app/wallet-program-record/server.ts") as typeof import("../../frontend/src/app/wallet-program-record/server.js");
const { readLiveHolderConfiguration } =
  require("../../frontend/src/app/holder-rewards-config/server.ts") as typeof import("../../frontend/src/app/holder-rewards-config/server.js");
const { MAINNET_GENESIS_HASH } =
  require("../../frontend/src/app/portfolio/types.ts") as typeof import("../../frontend/src/app/portfolio/types.js");
const ADDRESS = "HN7cABqLq46Es1jh92dQQisAq662SmxELLLsHHe4YWrH";
const URL = "https://rpc.example.test";
type Outcome = { value?: unknown; error?: unknown; pending?: true };

async function outcomeWithin(promise: Promise<unknown>): Promise<Outcome> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  try {
    return await Promise.race([
      promise.then(
        (value) => ({ value }),
        (error) => ({ error }),
      ),
      new Promise<Outcome>((resolve) => {
        timer = setTimeout(() => resolve({ pending: true }), 250);
      }),
    ]);
  } finally {
    clearTimeout(timer);
  }
}

function mockNetwork(t: TestContext, lookup: () => Promise<unknown>) {
  let requests = 0;
  t.mock.method(dns, "lookup", lookup);
  t.mock.method(https, "request", () => {
    requests++;
    throw new Error("Unexpected HTTPS request: DNS tests never open sockets");
  });
  syncBuiltinESMExports();
  t.after(() => {
    t.mock.restoreAll();
    syncBuiltinESMExports();
  });
  return () => requests;
}
function configured(t: TestContext) {
  const prior = process.env.SOLANA_RPC_URL;
  process.env.SOLANA_RPC_URL = URL;
  t.after(() => {
    if (prior === undefined) delete process.env.SOLANA_RPC_URL;
    else process.env.SOLANA_RPC_URL = prior;
  });
}
function deferred() {
  let resolve!: (value: unknown) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}
const readers: Array<[string, (signal: AbortSignal) => Promise<unknown>]> = [
  ["portfolio", (signal) => readLivePortfolio(ADDRESS, { signal })],
  [
    "public wallet record",
    (signal) => readLiveWalletRecord(ADDRESS, { signal }),
  ],
  [
    "holder configuration",
    (signal) => readLiveHolderConfiguration(ADDRESS, signal),
  ],
];

test("portfolio configured timeout bounds pending DNS and removes its listener", async (t) => {
  const requests = mockNetwork(t, async () => new Promise(() => {}));
  const controller = new AbortController();
  const result = await outcomeWithin(
    readLivePortfolio(ADDRESS, {
      rpcUrl: URL,
      timeoutMs: 20,
      signal: controller.signal,
    }),
  );
  assert.ok(result.error instanceof PortfolioRpcError, JSON.stringify(result));
  assert.equal(result.error.code, "RPC_TIMEOUT");
  assert.equal(getEventListeners(controller.signal, "abort").length, 0);
  assert.equal(requests(), 0);
});

for (const [name, read] of readers) {
  test(`${name} observes caller cancellation while DNS remains pending`, async (t) => {
    configured(t);
    const requests = mockNetwork(t, async () => new Promise(() => {}));
    const controller = new AbortController();
    const reason = new Error("synthetic caller cancellation");
    const pending = read(controller.signal);
    await Promise.resolve();
    controller.abort(reason);
    const result = await outcomeWithin(pending);
    assert.equal(result.error, reason, JSON.stringify(result));
    assert.equal(getEventListeners(controller.signal, "abort").length, 0);
    assert.equal(requests(), 0);
  });
  test(`${name} does not resolve DNS for an already canceled read`, async (t) => {
    configured(t);
    let lookups = 0;
    const requests = mockNetwork(t, async () => {
      lookups++;
      return [];
    });
    const controller = new AbortController();
    const reason = new Error("synthetic pre-cancellation");
    controller.abort(reason);
    const result = await outcomeWithin(read(controller.signal));
    assert.equal(result.error, reason);
    assert.equal(lookups, 0);
    assert.equal(requests(), 0);
  });
}

test("pending DNS preserves arbitrary caller abort reasons, including NaN", async (t) => {
  const requests = mockNetwork(t, async () => new Promise(() => {}));
  for (const reason of [NaN, 0, null, "caller stopped", Symbol("caller"), {}]) {
    const controller = new AbortController();
    const pending = readLivePortfolio(ADDRESS, {
      rpcUrl: URL,
      signal: controller.signal,
    });
    await Promise.resolve();
    controller.abort(reason);
    const result = await outcomeWithin(pending);
    assert.ok(Object.is(result.error, reason));
    assert.equal(getEventListeners(controller.signal, "abort").length, 0);
  }
  assert.equal(requests(), 0);
});

test("DNS errors and private answers preserve fail-closed admission and cleanup", async (t) => {
  const controller = new AbortController();
  let mode = "error";
  const requests = mockNetwork(t, async () => {
    if (mode === "error") throw new Error("synthetic lookup failure");
    return [{ address: "127.0.0.1", family: 4 }];
  });
  for (mode of ["error", "private"]) {
    const result = await outcomeWithin(
      createPinnedRpcCall(URL, 100, controller.signal),
    );
    assert.ok(result.error instanceof PortfolioRpcError);
    assert.equal(result.error.code, "RPC_DNS_REJECTED");
    assert.equal(getEventListeners(controller.signal, "abort").length, 0);
  }
  assert.equal(requests(), 0);
});

test("a late DNS success cannot start RPC calls after the setup timeout", async (t) => {
  const lookup = deferred();
  const requests = mockNetwork(t, () => lookup.promise);
  const result = await outcomeWithin(
    readLivePortfolio(ADDRESS, { rpcUrl: URL, timeoutMs: 20 }),
  );
  assert.ok(result.error instanceof PortfolioRpcError);
  assert.equal(result.error.code, "RPC_TIMEOUT");
  lookup.resolve([{ address: "8.8.8.8", family: 4 }]);
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(requests(), 0);
});

test("a late DNS rejection after cancellation is observed without starting HTTPS", async (t) => {
  const lookup = deferred();
  const requests = mockNetwork(t, () => lookup.promise);
  const controller = new AbortController();
  const reason = new Error("synthetic cancellation");
  const pending = readLivePortfolio(ADDRESS, {
    rpcUrl: URL,
    signal: controller.signal,
  });
  await Promise.resolve();
  controller.abort(reason);
  assert.equal((await outcomeWithin(pending)).error, reason);
  lookup.reject(new Error("synthetic late DNS failure"));
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(getEventListeners(controller.signal, "abort").length, 0);
  assert.equal(requests(), 0);
});

test("successful DNS still pins the same public address for four synthetic RPC reads", async (t) => {
  let lookups = 0;
  mockNetwork(t, async () => {
    lookups++;
    return [{ address: "8.8.8.8", family: 4 }];
  });
  const methods: string[] = [];
  const addresses: string[] = [];
  t.mock.method(
    https,
    "request",
    (
      _url: unknown,
      options: {
        lookup: (
          host: string,
          options: object,
          callback: (
            error: unknown,
            addresses: Array<{ address: string }>,
          ) => void,
        ) => void;
      },
      callback: (
        response: EventEmitter & { statusCode: number; headers: object },
      ) => void,
    ) => {
      options.lookup("rpc.example.test", { all: true }, (error, selected) => {
        assert.equal(error, null);
        addresses.push(selected[0].address);
      });
      const request = new EventEmitter() as EventEmitter & {
        end(body: string): void;
      };
      request.end = (body) =>
        queueMicrotask(() => {
          const input = JSON.parse(body) as { id: number; method: string };
          methods.push(input.method);
          const result =
            input.method === "getGenesisHash"
              ? MAINNET_GENESIS_HASH
              : {
                  context: { slot: 123 },
                  value: input.method === "getBalance" ? 0 : [],
                };
          const response = Object.assign(new EventEmitter(), {
            statusCode: 200,
            headers: {},
          });
          callback(response);
          response.emit(
            "data",
            Buffer.from(
              JSON.stringify({ jsonrpc: "2.0", id: input.id, result }),
            ),
          );
          response.emit("end");
        });
      return request;
    },
  );
  syncBuiltinESMExports();
  const controller = new AbortController();
  const value = await readLivePortfolio(ADDRESS, {
    rpcUrl: URL,
    timeoutMs: 100,
    signal: controller.signal,
  });
  assert.equal(value.address, ADDRESS);
  assert.equal(value.sol.lamports, "0");
  assert.equal(value.endpointHost, "rpc.example.test");
  assert.equal(lookups, 1);
  assert.deepEqual(methods.sort(), [
    "getBalance",
    "getGenesisHash",
    "getTokenAccountsByOwner",
    "getTokenAccountsByOwner",
  ]);
  assert.deepEqual(addresses, Array(4).fill("8.8.8.8"));
  assert.equal(getEventListeners(controller.signal, "abort").length, 0);
});

test("invalid timer values fail before DNS rather than overflow the local deadline", async (t) => {
  let lookups = 0;
  const requests = mockNetwork(t, async () => {
    lookups++;
    return [];
  });
  for (const timeout of [-1, 1.5, NaN, Infinity, 2_147_483_648])
    await assert.rejects(createPinnedRpcCall(URL, timeout), RangeError);
  assert.equal(lookups, 0);
  assert.equal(requests(), 0);
});
