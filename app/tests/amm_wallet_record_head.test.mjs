import assert from "node:assert/strict";
import { test } from "node:test";
import { createRequire } from "node:module";
import { createServer } from "node:http";

const backend = createRequire(
  new URL("../packages/backend/package.json", import.meta.url),
);
const { require: load } = backend("tsx/cjs/api");
const frontend = createRequire(
  new URL("../packages/frontend/package.json", import.meta.url),
);
const { autoImplementMethods } = frontend(
  "next/dist/server/route-modules/app-route/helpers/auto-implement-methods.js",
);
const { PublicKey } = frontend("@solana/web3.js");
const { handleAmmWalletRecord: handle } = load(
  "../packages/frontend/src/app/amm-wallet-record/handler.ts",
  import.meta.url,
);
const { readAmmWalletRecordWithRpc: read } = load(
  "../packages/frontend/src/app/amm-wallet-record/server.ts",
  import.meta.url,
);
const { PortfolioRpcError } = load(
  "../packages/frontend/src/app/portfolio/rpc.ts",
  import.meta.url,
);
const contract = load(
  "../packages/frontend/src/app/amm-wallet-record/contract.json",
  import.meta.url,
);

const USER = "So11111111111111111111111111111111111111112";
const GENESIS = "5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d";
const URL_BASE = `http://local/api/portfolio/amm-record?address=${USER}`;
const PDA = PublicKey.findProgramAddressSync(
  [Buffer.from(contract.pdaSeed), new PublicKey(USER).toBytes()],
  new PublicKey(contract.programId),
)[0].toBase58();
function account() {
  const bytes = Buffer.alloc(90);
  Buffer.from(contract.discriminator).copy(bytes);
  new PublicKey(USER).toBuffer().copy(bytes, 8);
  bytes[40] = 1;
  for (const offset of [41, 49, 57, 74, 82])
    bytes.writeBigUInt64LE((1n << 64n) - 1n - BigInt(offset), offset);
  bytes.writeBigInt64LE(-9n, 65);
  return {
    owner: contract.programId,
    executable: false,
    lamports: 1,
    space: bytes.length,
    data: [bytes.toString("base64"), "base64"],
  };
}
function fixture({ genesis = GENESIS, value = account() } = {}) {
  const calls = [];
  const readers = [];
  const reader = (address, { signal } = {}) => {
    readers.push({ address, signal });
    return read(
      address,
      async (method, params, forwarded) => {
        assert.equal(forwarded, signal);
        calls.push({ method, params });
        if (method === "getGenesisHash") {
          assert.deepEqual(params, []);
          return genesis;
        }
        assert.equal(method, "getAccountInfo");
        assert.deepEqual(params, [
          PDA,
          { encoding: "base64", commitment: "confirmed" },
        ]);
        return { context: { slot: 321 }, value };
      },
      "controlled-public.example",
      signal,
    );
  };
  return { calls, readers, reader };
}
const dispatch = (reader) =>
  autoImplementMethods({ GET: (request) => handle(request, reader) });

test("installed Next automatic HEAD executes the real SDK-backed read with GET metadata and an empty body", async () => {
  const f = fixture(),
    methods = dispatch(f.reader);
  const get = await methods.GET(new Request(URL_BASE));
  assert.equal(get.status, 200);
  const value = await get.json();
  assert.equal(value.record.user, USER);
  assert.equal(
    value.record.totalUnclaimedTokens,
    ((1n << 64n) - 42n).toString(),
  );
  assert.equal(value.record.lastUpdateTimestamp, "-9");
  const headRequest = new Request(URL_BASE, { method: "HEAD" });
  const head = await methods.HEAD(headRequest);
  assert.equal(head.status, 200);
  assert.deepEqual(
    Object.fromEntries(head.headers),
    Object.fromEntries(get.headers),
  );
  assert.equal(head.body, null);
  assert.equal(await head.text(), "");
  assert.equal(f.readers.length, 2);
  assert.equal(f.readers[1].address, USER);
  assert.equal(f.readers[1].signal, headRequest.signal);
  assert.deepEqual(
    f.calls.map((x) => x.method),
    ["getGenesisHash", "getAccountInfo", "getGenesisHash", "getAccountInfo"],
  );
});

test("automatic HEAD preserves GET query admission and unsupported methods remain rejected before the reader", async () => {
  let reads = 0;
  const methods = dispatch(async () => {
    reads++;
    throw new Error("Unexpected reader invocation");
  });
  for (const query of [
    "",
    `address=${USER}&x=1`,
    `address=${USER}&address=${USER}`,
    `address=${USER}&=1`,
  ]) {
    const url = "http://local/api/portfolio/amm-record?" + query;
    const get = await methods.GET(new Request(url));
    assert.equal(get.status, 400);
    const head = await methods.HEAD(new Request(url, { method: "HEAD" }));
    assert.equal(head.status, get.status);
    assert.deepEqual(
      Object.fromEntries(head.headers),
      Object.fromEntries(get.headers),
    );
    assert.equal(head.body, null);
    assert.equal(await head.text(), "");
  }
  const post = await handle(
    new Request(URL_BASE, { method: "POST" }),
    async () => {
      reads++;
    },
  );
  assert.equal(post.status, 405);
  assert.equal((await post.json()).error.code, "METHOD_NOT_ALLOWED");
  assert.equal(reads, 0);
});

test("automatic HEAD keeps cluster/provider status mapping and error privacy while returning no body", async () => {
  const cases = [
    [fixture({ genesis: "wrong-cluster" }).reader, 503, "WRONG_CLUSTER"],
    [
      fixture({ value: { ...account(), owner: USER } }).reader,
      502,
      "RPC_RESPONSE_INVALID",
    ],
    ...[
      ["RPC_RATE_LIMITED", 429],
      ["RPC_TIMEOUT", 504],
      ["RPC_CONFIGURATION_INVALID", 503],
    ].map(([code, status]) => [
      async () => {
        throw new PortfolioRpcError(code, "private-provider-message", true);
      },
      status,
      code,
    ]),
    [
      async () => {
        throw new Error("private-provider-message");
      },
      502,
      "RPC_UNAVAILABLE",
    ],
  ];
  for (const [reader, status, code] of cases) {
    const methods = dispatch(reader);
    const get = await methods.GET(new Request(URL_BASE));
    assert.equal(get.status, status);
    const body = await get.text();
    assert.ok(body.includes(code));
    assert.ok(!body.includes("private-provider-message"));
    const head = await methods.HEAD(new Request(URL_BASE, { method: "HEAD" }));
    assert.equal(head.status, status);
    assert.equal(head.headers.get("cache-control"), "no-store");
    assert.equal(head.body, null);
    assert.equal(await head.text(), "");
  }
});

test("real loopback HTTP traverses installed Next HEAD dispatch and actual handler/SDK reader without suppressing GET data", async () => {
  const f = fixture(),
    methods = dispatch(f.reader);
  const server = createServer(async (req, res) => {
    try {
      const request = new Request(`http://127.0.0.1${req.url}`, {
        method: req.method,
      });
      const response = await methods[req.method](request);
      res.writeHead(response.status, Object.fromEntries(response.headers));
      res.end(await response.text());
    } catch {
      res.writeHead(500);
      res.end();
    }
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  try {
    const endpoint = `http://127.0.0.1:${server.address().port}/api/portfolio/amm-record?address=${USER}`;
    const head = await fetch(endpoint, { method: "HEAD" });
    assert.equal(head.status, 200);
    assert.equal(head.headers.get("cache-control"), "no-store");
    assert.equal(head.headers.get("content-type"), "application/json");
    assert.equal(await head.text(), "");
    const get = await fetch(endpoint);
    assert.equal(get.status, 200);
    assert.equal((await get.json()).record.user, USER);
    assert.equal(f.readers.length, 2);
    const invalid = await fetch(endpoint + "&unknown=1", { method: "HEAD" });
    assert.equal(invalid.status, 400);
    assert.equal(await invalid.text(), "");
    assert.equal(f.readers.length, 2);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});
