import assert from "node:assert/strict";
import { test } from "node:test";
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { createServer } from "node:http";
const backend = createRequire(
  new URL("../packages/backend/package.json", import.meta.url),
);
const { require: load } = backend("tsx/cjs/api");
const { readGlobalIncentiveRecordWithRpc: read } = load(
  "../packages/frontend/src/app/global-incentive-record/server.ts",
  import.meta.url,
);
const { handleGlobalIncentiveRecord: handle } = load(
  "../packages/frontend/src/app/global-incentive-record/handler.ts",
  import.meta.url,
);
const {
  isGlobalIncentiveRecord: accepts,
  fetchGlobalIncentiveRecord: fetchRecord,
} = load(
  "../packages/frontend/src/app/global-incentive-record/client.ts",
  import.meta.url,
);
const contract = load(
  "../packages/frontend/src/app/global-incentive-record/contract.json",
  import.meta.url,
);
const sdkRequire = createRequire(
  new URL("../packages/sdk/package.json", import.meta.url),
);
const sdk = sdkRequire("./dist/index.js");
const { PublicKey } = sdkRequire("@solana/web3.js");
const GENESIS = "5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d";
const MINT = "So11111111111111111111111111111111111111112";
const U64MAX = (1n << 64n) - 1n;
function bytes() {
  const data = Buffer.alloc(contract.minimumBytes);
  Buffer.from(contract.discriminator).copy(data);
  data.writeBigInt64LE(-(1n << 63n), 8);
  data.writeBigInt64LE((1n << 63n) - 1n, 16);
  data.writeBigInt64LE(86_400n, 24);
  new PublicKey(MINT).toBuffer().copy(data, 32);
  for (let i = 0; i < 60; i++)
    data.writeBigUInt64LE(U64MAX - BigInt(i), 64 + 8 * i);
  return data;
}
function account(data = bytes()) {
  return {
    owner: contract.programId,
    executable: false,
    lamports: 1,
    space: data.length,
    data: [data.toString("base64"), "base64"],
  };
}
function fixture(
  value = account(),
  genesis = GENESIS,
  context = { slot: 321 },
) {
  const calls = [];
  return {
    calls,
    call: async (method, params, signal) => {
      calls.push({ method, params, signal });
      return method === "getGenesisHash" ? genesis : { context, value };
    },
  };
}
const result = (f) => read(f.call, "controlled-public.example");

test("source producer binds six archive-equal SDK sources and the actual fixed Global PDA", () => {
  execFileSync(
    process.execPath,
    ["scripts/global-incentive-record/contract.mjs", "--check"],
    { cwd: new URL("..", import.meta.url) },
  );
  assert.equal(contract.minimumBytes, 544);
  assert.equal(
    contract.recordPda,
    sdk.GLOBAL_VOLUME_ACCUMULATOR_PDA.toBase58(),
  );
});
test("actual SDK decoding preserves all 60 u64 values, signed timestamp extremes and observed context", async () => {
  const f = fixture(),
    value = await result(f);
  const decoded = sdk.PUMP_SDK.decodeGlobalVolumeAccumulator({
    data: bytes(),
    owner: new PublicKey(contract.programId),
    executable: false,
    lamports: 1,
  });
  assert.equal(value.record.startTime, decoded.startTime.toString(10));
  assert.equal(value.record.endTime, decoded.endTime.toString(10));
  assert.equal(value.record.secondsInADay, "86400");
  assert.equal(value.record.mint, MINT);
  for (const name of ["totalTokenSupply", "solVolumes"])
    assert.deepEqual(
      value.record[name],
      decoded[name].map((x) => x.toString(10)),
    );
  assert.equal(value.contextSlot, 321);
  assert.equal(value.dataBytes, 544);
  assert.ok(accepts(value));
  assert.deepEqual(
    f.calls.map((x) => [x.method, x.params]),
    [
      ["getGenesisHash", []],
      [
        "getAccountInfo",
        [contract.recordPda, { encoding: "base64", commitment: "confirmed" }],
      ],
    ],
  );
});
test("absent Global account stays absent; unknown trailing bytes are not projected as fields", async () => {
  const missing = await result(fixture(null));
  assert.equal(missing.record, null);
  assert.equal(missing.dataBytes, null);
  assert.ok(accepts(missing));
  const ordinary = await result(fixture()),
    extended = await result(
      fixture(account(Buffer.concat([bytes(), Buffer.alloc(16, 77)]))),
    );
  assert.deepEqual(extended.record, ordinary.record);
  assert.equal(extended.dataBytes, 560);
});
test("owner/discriminator/base64/length/context admission rejects unsupported account responses before projection", async () => {
  const malformed = [
    { ...account(), owner: MINT },
    { ...account(), executable: true },
    { ...account(), lamports: -1 },
    { ...account(), lamports: 1.5 },
    { ...account(), space: 543 },
    { ...account(), data: ["not base64", "base64"] },
    { ...account(), data: [bytes().toString("base64"), "base64+zstd"] },
    account(Buffer.alloc(544)),
    account(bytes().subarray(0, 543)),
    account(Buffer.alloc(16_385)),
  ];
  for (const a of malformed)
    await assert.rejects(
      result(fixture(a)),
      (e) => e.code === "RPC_RESPONSE_INVALID",
    );
  for (const context of [
    null,
    {},
    { slot: -1 },
    { slot: 1.5 },
    { slot: Number.MAX_SAFE_INTEGER + 1 },
  ])
    await assert.rejects(
      result(fixture(account(), GENESIS, context)),
      (e) => e.code === "RPC_RESPONSE_INVALID",
    );
  const wrong = fixture(account(), "wrong-cluster");
  await assert.rejects(result(wrong), (e) => e.code === "WRONG_CLUSTER");
  assert.equal(wrong.calls.length, 1);
  const controller = new AbortController();
  controller.abort();
  const aborted = fixture();
  await assert.rejects(
    read(aborted.call, "controlled.example", controller.signal),
  );
  assert.equal(aborted.calls.length, 0);
});
test("browser acceptance binds fixed account, widths and 30-entry arrays; client omits credentials and uses no-store", async () => {
  const value = await result(fixture());
  for (const bad of [
    { ...value, programId: MINT },
    { ...value, recordPda: MINT },
    { ...value, cluster: "devnet" },
    { ...value, record: { ...value.record, mint: "invalid" } },
    { ...value, record: { ...value.record, startTime: "9223372036854775808" } },
    {
      ...value,
      record: {
        ...value.record,
        totalTokenSupply: value.record.totalTokenSupply.slice(1),
      },
    },
    {
      ...value,
      record: {
        ...value.record,
        solVolumes: Array(30).fill("18446744073709551616"),
      },
    },
  ])
    assert.equal(accepts(bad), false);
  let observed;
  await fetchRecord(undefined, async (url, options) => {
    observed = { url, options };
    return Response.json(value);
  });
  assert.equal(observed.url, "/api/portfolio/incentive-record");
  assert.equal(observed.options.credentials, "omit");
  assert.equal(observed.options.cache, "no-store");
  assert.equal(observed.options.method, "GET");
  await assert.rejects(
    fetchRecord(undefined, async () =>
      Response.json({ privateProviderError: "secret" }, { status: 502 }),
    ),
    /unavailable or unsupported/,
  );
});
test("handler has no caller-selected account, rejects query/method before reading, supports bodyless HEAD and masks failures", async () => {
  let reads = 0;
  const reader = async () => {
    reads++;
    return result(fixture());
  };
  for (const url of ["?address=" + MINT, "?x=1", "?=1"])
    assert.equal(
      (await handle(new Request("http://local/api" + url), reader)).status,
      400,
    );
  assert.equal(
    (await handle(new Request("http://local/api", { method: "POST" }), reader))
      .status,
    405,
  );
  assert.equal(reads, 0);
  const head = await handle(
    new Request("http://local/api", { method: "HEAD" }),
    reader,
  );
  assert.equal(head.status, 200);
  assert.equal(head.headers.get("cache-control"), "no-store");
  assert.equal(await head.text(), "");
  assert.equal(reads, 1);
  const failure = await handle(new Request("http://local/api"), async () => {
    throw new Error("private-provider-secret");
  });
  assert.equal(failure.status, 502);
  assert.ok(!(await failure.text()).includes("private-provider-secret"));
});
test("real local HTTP traverses client, handler, fixed PDA read and actual SDK decoder", async () => {
  const calls = fixture();
  const server = createServer(async (req, res) => {
    const response = await handle(
      new Request(`http://127.0.0.1${req.url}`),
      () => result(calls),
    );
    res.writeHead(response.status, Object.fromEntries(response.headers));
    res.end(await response.text());
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  try {
    const port = server.address().port;
    const value = await fetchRecord(undefined, (path, options) =>
      fetch(`http://127.0.0.1:${port}${path}`, options),
    );
    assert.equal(value.record.solVolumes[29], (U64MAX - 59n).toString());
    assert.equal(calls.calls.length, 2);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});
