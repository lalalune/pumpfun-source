import assert from "node:assert/strict";
import { test } from "node:test";
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { createServer } from "node:http";
const backendRequire = createRequire(
  new URL("../packages/backend/package.json", import.meta.url),
);
const { require: ts } = backendRequire("tsx/cjs/api");
const server = ts(
  "../packages/frontend/src/app/amm-wallet-record/server.ts",
  import.meta.url,
);
const { handleAmmWalletRecord } = ts(
  "../packages/frontend/src/app/amm-wallet-record/handler.ts",
  import.meta.url,
);
const { isAmmWalletRecord, fetchAmmWalletRecord } = ts(
  "../packages/frontend/src/app/amm-wallet-record/client.ts",
  import.meta.url,
);
const { PortfolioRpcError } = ts(
  "../packages/frontend/src/app/portfolio/rpc.ts",
  import.meta.url,
);
const contract = ts(
  "../packages/frontend/src/app/amm-wallet-record/contract.json",
  import.meta.url,
);
const sdkRequire = createRequire(
  new URL("../packages/sdk/package.json", import.meta.url),
);
const sdk = await import("../packages/sdk/dist/swap/index.mjs");
const pump = sdkRequire("./dist/index.js");
const { PublicKey } = sdkRequire("@solana/web3.js");
const USER = "So11111111111111111111111111111111111111112",
  OTHER = "11111111111111111111111111111111";
const GENESIS = "5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d";
const PDA = sdk.userVolumeAccumulatorPda(new PublicKey(USER)).toBase58();
function bytes() {
  const b = Buffer.alloc(90);
  Buffer.from(contract.discriminator).copy(b);
  new PublicKey(USER).toBuffer().copy(b, 8);
  b[40] = 1;
  b[73] = 0;
  for (const offset of [41, 49, 57, 74, 82])
    b.writeBigUInt64LE((1n << 64n) - 1n - BigInt(offset), offset);
  b.writeBigInt64LE(-(1n << 63n), 65);
  return b;
}
function account(data = bytes()) {
  return {
    owner: contract.programId,
    executable: false,
    lamports: 2039280,
    space: data.length,
    data: [data.toString("base64"), "base64"],
  };
}
function fixture(value = account(), genesis = GENESIS) {
  const calls = [];
  return {
    calls,
    call: async (method, params, signal) => {
      calls.push({ method, params, signal });
      return method === "getGenesisHash"
        ? genesis
        : { context: { slot: 321 }, value };
    },
  };
}
const read = (f, signal) =>
  server.readAmmWalletRecordWithRpc(USER, f.call, "public-rpc.example", signal);

test("fresh process executes the used lazy SDK read without a CommonJS preload", () => {
  const output = execFileSync(
    process.execPath,
    [
      "--input-type=module",
      "-e",
      `
    import {createRequire} from "node:module";
    const require=createRequire(new URL("./packages/backend/package.json",import.meta.url));
    const {require:ts}=require("tsx/cjs/api");
    const {readAmmWalletRecordWithRpc}=ts("./packages/frontend/src/app/amm-wallet-record/server.ts",import.meta.url);
    const methods=[];
    const result=await readAmmWalletRecordWithRpc(${JSON.stringify(USER)},async(method)=>{
      methods.push(method);
      return method==="getGenesisHash"?${JSON.stringify(GENESIS)}:{context:{slot:321},value:null};
    },"public-rpc.example");
    const cjsSwap=Object.keys(require.cache).some(path=>path.endsWith("/packages/sdk/dist/swap/index.js"));
    console.log(JSON.stringify({result,methods,cjsSwap}));
  `,
    ],
    { cwd: new URL("..", import.meta.url), encoding: "utf8" },
  );
  const actual = JSON.parse(output.trim().split("\n").at(-1));
  assert.equal(actual.cjsSwap, false);
  assert.equal(actual.result.record, null);
  assert.equal(actual.result.recordPda, PDA);
  assert.deepEqual(actual.methods, ["getGenesisHash", "getAccountInfo"]);
});
test("archive-bound AMM contract is90 bytes and has no invented stable-cashback fields", () => {
  execFileSync(
    process.execPath,
    ["scripts/amm-wallet-record/contract.mjs", "--check"],
    { cwd: new URL("..", import.meta.url) },
  );
  assert.equal(contract.minimumBytes, 90);
  assert.equal(contract.programId, sdk.PUMP_AMM_PROGRAM_ID.toBase58());
  assert.notEqual(
    PDA,
    pump.userVolumeAccumulatorPda(new PublicKey(USER)).toBase58(),
  );
  assert.deepEqual(
    contract.fields.slice(-2).map((f) => [f.decoded, f.bytes]),
    [
      ["cashbackEarned", [74, 82]],
      ["totalCashbackClaimed", [82, 90]],
    ],
  );
  assert.ok(
    !contract.fields.some((f) => f.decoded.toLowerCase().includes("stable")),
  );
});
test("actual published AMM decoder preserves exact u64 and signed i64 in the used read", async () => {
  const f = fixture(),
    value = await read(f);
  const decoded = sdk.PUMP_AMM_SDK.decodeUserVolumeAccumulator({
    data: bytes(),
    owner: new PublicKey(contract.programId),
    lamports: 1,
    executable: false,
  });
  assert.equal(value.recordPda, PDA);
  assert.equal(value.record.user, USER);
  assert.equal(value.dataBytes, 90);
  for (const field of contract.fields)
    if (["u64", "i64"].includes(field.type))
      assert.equal(
        value.record[field.decoded],
        decoded[field.decoded].toString(10),
      );
  assert.equal(value.record.lastUpdateTimestamp, "-9223372036854775808");
  assert.equal(value.record.needsClaim, true);
  assert.equal(value.record.hasTotalClaimedTokens, false);
  assert.equal(Object.hasOwn(value.record, "stableCashbackEarned"), false);
  assert.equal(isAmmWalletRecord(value, USER), true);
  assert.deepEqual(
    f.calls.map(({ method, params }) => ({ method, params })),
    [
      { method: "getGenesisHash", params: [] },
      {
        method: "getAccountInfo",
        params: [PDA, { encoding: "base64", commitment: "confirmed" }],
      },
    ],
  );
});
test("missing stays absent, short records fail and unknown trailing bytes are not interpreted", async () => {
  const absent = await read(fixture(null));
  assert.equal(absent.record, null);
  assert.equal(absent.dataBytes, null);
  for (const length of [0, 8, 40, 74, 89])
    await assert.rejects(
      read(fixture(account(bytes().subarray(0, length)))),
      /unavailable or unsupported/,
    );
  // The other program's SDK codec does not enforce its full106-byte width:
  // its BN layout turns missing trailing buffers into zero counters. This is
  // why this view uses its own program/layout admission and omits those fields.
  const otherCodec = pump.PUMP_SDK.decodeUserVolumeAccumulator({
    data: bytes(),
    owner: pump.PUMP_PROGRAM_ID,
    lamports: 1,
    executable: false,
  });
  assert.equal(otherCodec.stableCashbackEarned.toString(10), "0");
  assert.equal(otherCodec.totalStableCashbackClaimed.toString(10), "0");
  assert.equal(
    Object.hasOwn((await read(fixture())).record, "stableCashbackEarned"),
    false,
  );
  const extended = await read(
    fixture(account(Buffer.concat([bytes(), Buffer.alloc(16, 255)]))),
  );
  assert.equal(extended.dataBytes, 106);
  assert.deepEqual(extended.record, (await read(fixture())).record);
});
test("program ownership, embedded user, discriminator, booleans and metadata fail closed", async () => {
  const mutations = [
    (a) => {
      a.owner = pump.PUMP_PROGRAM_ID.toBase58();
    },
    (a) => {
      a.executable = true;
    },
    (a) => {
      a.lamports = Number.MAX_SAFE_INTEGER + 1;
    },
    (a) => {
      a.lamports = "1";
    },
    (a) => {
      a.space = 91;
    },
    (a) => {
      a.data[1] = "jsonParsed";
    },
    (a) => {
      a.data[0] += " ";
    },
    (a) => {
      a.data[0] = "A".repeat(22001);
    },
  ];
  for (const mutate of mutations) {
    const a = account();
    mutate(a);
    await assert.rejects(read(fixture(a)), /unavailable or unsupported/);
  }
  for (const offset of [0, 8, 40, 73]) {
    const b = bytes();
    b[offset] = offset === 40 || offset === 73 ? 2 : b[offset] ^ 255;
    await assert.rejects(
      read(fixture(account(b))),
      /unavailable or unsupported/,
    );
  }
});
test("canonical user, mainnet genesis, safe slot and abort order are enforced", async () => {
  const f = fixture();
  await assert.rejects(
    server.readAmmWalletRecordWithRpc("invalid", f.call, "public-rpc.example"),
    /canonical/,
  );
  assert.equal(f.calls.length, 0);
  const wrong = fixture(account(), "wrong-cluster");
  await assert.rejects(read(wrong), /not Solana mainnet/);
  assert.equal(wrong.calls.length, 1);
  for (const slot of [-1, 0.5, Number.MAX_SAFE_INTEGER + 1, "321"]) {
    await assert.rejects(
      read({
        call: async (method) =>
          method === "getGenesisHash"
            ? GENESIS
            : { context: { slot }, value: account() },
      }),
      /unavailable or unsupported/,
    );
  }
  const c = new AbortController();
  c.abort(new Error("cancelled"));
  const cancelled = fixture();
  await assert.rejects(read(cancelled, c.signal), /cancelled/);
  assert.equal(cancelled.calls.length, 0);
  const during = new AbortController();
  let count = 0;
  await assert.rejects(
    read(
      {
        call: async () => {
          count++;
          during.abort(new Error("cancelled"));
          return GENESIS;
        },
      },
      during.signal,
    ),
    /cancelled/,
  );
  assert.equal(count, 1);
});
test("client rejects cross-program/identity data and fabricated unavailable fields", async () => {
  const v = await read(fixture());
  for (const mutate of [
    (x) => {
      x.programId = pump.PUMP_PROGRAM_ID.toBase58();
    },
    (x) => {
      x.recordPda = pump
        .userVolumeAccumulatorPda(new PublicKey(USER))
        .toBase58();
    },
    (x) => {
      x.address = OTHER;
    },
    (x) => {
      x.record.user = OTHER;
    },
    (x) => {
      x.dataBytes = 89;
    },
    (x) => {
      x.record.stableCashbackEarned = "0";
    },
    (x) => {
      x.record.totalStableCashbackClaimed = "0";
    },
    (x) => {
      x.record.cashbackEarned = "18446744073709551616";
    },
    (x) => {
      x.record.needsClaim = 1;
    },
  ]) {
    const x = structuredClone(v);
    mutate(x);
    assert.equal(isAmmWalletRecord(x, USER), false);
  }
});
test("GET handler rejects malformed query/method before reading and retains no-store", async () => {
  let calls = 0;
  const value = await read(fixture());
  const reader = async (address) => {
    server.walletKey(address);
    calls++;
    return value;
  };
  for (const query of [
    "",
    `address=${USER}&extra=1`,
    `address=${USER}&address=${USER}`,
    `address=${USER}&=1`,
  ]) {
    const r = await handleAmmWalletRecord(
      new Request("http://local/api?" + query),
      reader,
    );
    assert.equal(r.status, 400);
    assert.equal(r.headers.get("cache-control"), "no-store");
  }
  const post = await handleAmmWalletRecord(
    new Request("http://local/api?address=" + USER, { method: "POST" }),
    reader,
  );
  assert.equal(post.status, 405);
  assert.equal(calls, 0);
  const valid = await handleAmmWalletRecord(
    new Request("http://local/api?address=" + USER),
    reader,
  );
  assert.equal(valid.status, 200);
  assert.equal(calls, 1);
  assert.deepEqual(await valid.json(), value);
});
test("bounded handler failures never expose provider text", async () => {
  for (const [code, status] of [
    ["RPC_RATE_LIMITED", 429],
    ["RPC_TIMEOUT", 504],
    ["WRONG_CLUSTER", 503],
    ["RPC_CONFIGURATION_INVALID", 503],
    ["RPC_RESPONSE_INVALID", 502],
  ]) {
    const r = await handleAmmWalletRecord(
      new Request("http://local/api?address=" + USER),
      async () => {
        throw new PortfolioRpcError(code, "provider-private-message", true);
      },
    );
    assert.equal(r.status, status);
    assert.equal(r.headers.get("cache-control"), "no-store");
    const body = await r.text();
    assert.ok(!body.includes("provider-private-message"));
    assert.ok(body.includes(code));
  }
});
test("real loopback HTTP client uses fixed read path and credentials-omitting options", async () => {
  const value = await read(fixture());
  const seen = [];
  const http = createServer((req, res) => {
    seen.push({ url: req.url, method: req.method, cookie: req.headers.cookie });
    res.writeHead(200, {
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
    });
    res.end(JSON.stringify(value));
  });
  await new Promise((resolve) => http.listen(0, "127.0.0.1", resolve));
  try {
    const endpoint = `http://127.0.0.1:${http.address().port}`;
    const c = new AbortController();
    const actual = await fetchAmmWalletRecord(
      USER,
      c.signal,
      (url, options) => {
        assert.equal(options.credentials, "omit");
        assert.equal(options.cache, "no-store");
        assert.equal(options.signal, c.signal);
        return fetch(new URL(url, endpoint), options);
      },
    );
    assert.deepEqual(actual, value);
    assert.deepEqual(seen, [
      {
        url: `/api/portfolio/amm-record?address=${USER}`,
        method: "GET",
        cookie: undefined,
      },
    ]);
  } finally {
    await new Promise((resolve) => http.close(resolve));
  }
});
