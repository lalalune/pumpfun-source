import test from "node:test";
import assert from "node:assert/strict";
import {
  mkdtempSync,
  readFileSync,
  rmSync,
  symlinkSync,
  truncateSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createHash } from "node:crypto";
import { buildApp, type Fixture } from "../src/app.js";
import {
  PayoutsStore,
  loadPayoutsStore,
  UnavailablePayoutWindowError,
  type PayoutsDataset,
  type PayoutFact,
} from "../src/payouts-store.js";
import { assertSchema } from "../src/schema-validator.js";

const now = "2026-10-29T00:00:00.000Z";
// Synthetic shape-only credential for in-process compatibility-gate tests.
const headers = { authorization: `Bearer pf_live_${"a".repeat(49)}` };
const path = "/v1/payouts/leaderboard";
const spec = JSON.parse(
  readFileSync(
    new URL("../../../contracts/developer.openapi.json", import.meta.url),
    "utf8",
  ),
);
function fact(
  id: string,
  wallet: string,
  amountAtomic: string,
  paidAt = "2026-10-28T12:00:00.000Z",
): PayoutFact {
  return { id, wallet, amountAtomic, paidAt, status: "confirmed" };
}
function dataset(): PayoutsDataset {
  return {
    schemaVersion: 1,
    dataSource: "synthetic",
    observedAt: now,
    generatedAt: now,
    owners: [
      {
        userId: "synthetic-user-a",
        wallets: ["z-solana", "0x-synthetic", "unused"],
        username: "Synthetic A",
        profileImageUrl: null,
        isVerified: true,
        verifiedBadgeVisible: false,
        twitterId: "123",
        walletAddress: "z-solana",
      },
    ],
    payouts: [
      fact("a1", "z-solana", "100000"),
      fact("a2", "0x-synthetic", "200000"),
      fact("bare", "bare-wallet", "250000"),
    ],
    windows: { "1d": { startAt: "2026-10-28T00:00:00.000Z", endAt: now } },
  };
}
function contract(body: unknown) {
  assertSchema(
    body,
    spec.paths["/payouts/leaderboard"].get.responses["200"].content[
      "application/json"
    ].schema,
    "payout leaderboard",
    spec,
  );
}
async function withApp(
  run: (app: ReturnType<typeof buildApp>) => Promise<void>,
  data: PayoutsDataset | undefined = dataset(),
  fixtures: Fixture[] = [],
) {
  const app = buildApp(
    fixtures,
    data ? { payoutsStore: new PayoutsStore(data) } : {},
  );
  try {
    await run(app);
  } finally {
    await app.close();
  }
}

test("opt-in read aggregates confirmed atoms across owned wallets and satisfies exact OpenAPI", async () => {
  await withApp(async (app) => {
    const res = await app.inject({ method: "GET", url: path, headers });
    assert.equal(res.statusCode, 200);
    const body = res.json();
    contract(body);
    assert.deepEqual(body, {
      generatedAt: now,
      totalEarners: 2,
      entries: [
        {
          rank: 1,
          userId: "synthetic-user-a",
          username: "Synthetic A",
          profileImageUrl: null,
          isVerified: true,
          verifiedBadgeVisible: false,
          twitterId: "123",
          twitterUrl: "https://x.com/i/user/123",
          wallets: ["0x-synthetic", "z-solana"],
          totalPaidUsdc: 0.3,
          payoutCount: 2,
          lastPaidAt: "2026-10-28T12:00:00.000Z",
          walletAddress: "z-solana",
        },
        {
          rank: 2,
          userId: null,
          username: null,
          profileImageUrl: null,
          isVerified: false,
          verifiedBadgeVisible: true,
          twitterId: null,
          twitterUrl: null,
          wallets: ["bare-wallet"],
          totalPaidUsdc: 0.25,
          payoutCount: 1,
          lastPaidAt: "2026-10-28T12:00:00.000Z",
          walletAddress: null,
        },
      ],
    });
    assert.equal(res.headers["x-reconstruction-data-source"], "synthetic");
    assert.equal(res.headers["x-reconstruction-observed-at"], now);
    assert.equal(res.headers["x-reconstruction-compatibility"], "unqualified");
    for (const row of body.entries) {
      assert.equal("isViewer" in row, false);
      assert.equal("viewerFollows" in row, false);
      assert.equal("resolvedAvatarDecoration" in row, false);
    }
  });
});

test("all six non-confirmed lifecycle states contribute neither totals, wallets nor earners", () => {
  const data = dataset();
  for (const status of [
    "awaiting_approval",
    "pending",
    "signed",
    "submitted",
    "failed",
    "rejected",
  ] as const) {
    data.payouts.push({
      ...fact(status, `not-paid-${status}`, "100000000"),
      status,
      paidAt: null,
    });
    data.payouts.push({
      ...fact(`owner-${status}`, "unused", "100000000"),
      status,
    });
  }
  assert.deepEqual(
    new PayoutsStore(data).leaderboard(),
    new PayoutsStore(dataset()).leaderboard(),
  );
});

test("supplied windows use explicit local inclusive-start/exclusive-end cuts and rerank in-window totals", () => {
  const data = dataset();
  data.payouts.push(
    fact("before", "bare-wallet", "1000000", "2026-10-27T23:59:59.999Z"),
  );
  data.payouts.push(
    fact("start", "bare-wallet", "100000", "2026-10-28T00:00:00.000Z"),
  );
  data.payouts.push(fact("end", "outside-only", "9000000", now));
  data.windows["1w"] = { startAt: "2026-10-20T00:00:00.000Z", endAt: now };
  data.windows["1m"] = { startAt: "2026-09-29T00:00:00.000Z", endAt: now };
  const store = new PayoutsStore(data);
  const daily = store.leaderboard({ period: "1d" });
  contract(daily);
  assert.equal(daily.totalEarners, 2);
  assert.deepEqual(
    daily.entries.map((row) => [row.wallets[0], row.rank, row.totalPaidUsdc]),
    [
      ["bare-wallet", 1, 0.35],
      ["0x-synthetic", 2, 0.3],
    ],
  );
  assert.equal(
    store.leaderboard({ period: "1w" }).entries[0].totalPaidUsdc,
    1.35,
  );
  assert.deepEqual(
    store.leaderboard({ period: "1w" }),
    store.leaderboard({ period: "1m" }),
  );
  assert.equal(store.leaderboard().totalEarners, 3);
  assert.equal(store.leaderboard().entries[0].lastPaidAt, now);
});

test("missing window is explicitly unavailable, not an all-time or empty fallback", async () => {
  assert.throws(
    () => new PayoutsStore(dataset()).leaderboard({ period: "1w" }),
    UnavailablePayoutWindowError,
  );
  await withApp(async (app) => {
    const res = await app.inject({
      method: "GET",
      url: `${path}?period=1w`,
      headers,
    });
    assert.equal(res.statusCode, 501);
    assert.deepEqual(res.json(), {
      statusCode: 501,
      error: "COMPATIBILITY_NOT_IMPLEMENTED",
      reason: "PAYOUT_WINDOW_UNAVAILABLE",
    });
  });
});

test("immutable tie order is independent of input order and ranks remain global across pages", () => {
  const data = dataset();
  data.owners = [];
  data.payouts = [
    fact("b", "b", "1"),
    fact("a", "a", "1"),
    fact("c", "c", "1"),
  ];
  const store = new PayoutsStore(data);
  assert.deepEqual(
    store
      .leaderboard({ page: 1, pageSize: 1 })
      .entries.map((row) => [row.rank, row.wallets[0]]),
    [[2, "b"]],
  );
  const expected = store.leaderboard();
  data.payouts.reverse();
  assert.deepEqual(new PayoutsStore(data).leaderboard(), expected);
  assert.equal(expected.entries[0].totalPaidUsdc, 0.000001);
});

test("top-500 cap does not cap earner count and distant safe-integer pages stay empty", () => {
  const data = dataset();
  data.owners = [];
  data.payouts = Array.from({ length: 503 }, (_, index) =>
    fact(`id-${index}`, `wallet-${index}`, String(1000 - index)),
  );
  const store = new PayoutsStore(data);
  assert.equal(store.leaderboard().entries.length, 50);
  const pages = [0, 1, 2].map((page) =>
    store.leaderboard({ page, pageSize: 200 }),
  );
  for (const page of pages) {
    contract(page);
    assert.equal(page.totalEarners, 503);
  }
  const rows = pages.flatMap((page) => page.entries);
  assert.equal(rows.length, 500);
  assert.equal(rows[499].rank, 500);
  assert.equal(new Set(rows.map((row) => row.wallets[0])).size, 500);
  for (const page of [3, 500, Number.MAX_SAFE_INTEGER])
    assert.deepEqual(store.leaderboard({ page, pageSize: 200 }).entries, []);
});

test("empty confirmed inventory is a real empty board, with supplied null generation time", async () => {
  const data = dataset();
  data.payouts = [];
  data.generatedAt = null;
  await withApp(async (app) => {
    const res = await app.inject({
      method: "GET",
      url: `${path}?period=1d`,
      headers,
    });
    assert.equal(res.statusCode, 200);
    contract(res.json());
    assert.deepEqual(res.json(), {
      entries: [],
      totalEarners: 0,
      generatedAt: null,
    });
  }, data);
});

test("source and returned objects cannot mutate an already constructed board", () => {
  const data = dataset();
  const store = new PayoutsStore(data);
  const original = store.leaderboard();
  data.owners[0].username = "changed";
  data.owners[0].wallets.length = 0;
  data.payouts[0].amountAtomic = "9";
  data.payouts.length = 0;
  data.windows["1d"]!.startAt = now;
  const result = store.leaderboard();
  result.entries[0].wallets.push("injected");
  result.entries[0].totalPaidUsdc = 9;
  result.entries.length = 0;
  assert.deepEqual(store.leaderboard(), original);
});

test("default harness stays501 and explicit fixture mode remains separate from opt-in read model", async () => {
  const app = buildApp();
  try {
    assert.equal(
      (await app.inject({ method: "GET", url: path, headers })).statusCode,
      501,
    );
    assert.equal(
      (await app.inject({ method: "GET", url: path })).statusCode,
      401,
    );
  } finally {
    await app.close();
  }
  const fixture: Fixture = {
    method: "GET",
    path,
    status: 200,
    body: { syntheticFixture: true },
    source: "synthetic-payout-test",
  };
  const replay = buildApp([fixture]);
  try {
    assert.deepEqual(
      (await replay.inject({ method: "GET", url: path, headers })).json(),
      fixture.body,
    );
  } finally {
    await replay.close();
  }
  await withApp(
    async (native) => {
      const response = await native.inject({
        method: "GET",
        url: path,
        headers,
      });
      contract(response.json());
      assert.equal("syntheticFixture" in response.json(), false);
    },
    dataset(),
    [fixture],
  );
});

test("existing shape-only gate runs before native data and no website/history/mutation aliases appear", async () => {
  await withApp(async (app) => {
    for (const credential of [undefined, "Bearer invalid"]) {
      const res = await app.inject({
        method: "GET",
        url: path,
        headers: credential ? { authorization: credential } : {},
      });
      assert.equal(res.statusCode, 401);
      assert.equal("entries" in res.json(), false);
    }
    const ambiguous = await app.inject({
      method: "GET",
      url: path,
      headers: { ...headers, "x-api-key": `pf_live_${"b".repeat(49)}` },
    });
    assert.equal(ambiguous.statusCode, 501);
    for (const url of ["/payouts/leaderboard", "/v1/payouts"])
      assert.equal(
        (await app.inject({ method: "GET", url, headers })).statusCode,
        501,
      );
    assert.equal(
      (await app.inject({ method: "POST", url: path, headers, payload: {} }))
        .statusCode,
      501,
    );
  });
});

test("strict queries reject unknown, duplicate, noncanonical, overflow and malformed values", async () => {
  await withApp(async (app) => {
    for (const query of [
      "page=-1",
      "page=01",
      "page=1.0",
      "page=1e2",
      "page=9007199254740992",
      "page=",
      "page=%200",
      "page=0?ignored",
      "page=0&page=0",
      "pageSize=0",
      "pageSize=201",
      "pageSize=1&pageSize=2",
      "period=all",
      "period=1D",
      "period=",
      "period=1d&period=1d",
      "viewer=x",
      "page[]=0",
    ]) {
      const res = await app.inject({
        method: "GET",
        url: `${path}?${query}`,
        headers,
      });
      assert.equal(res.statusCode, 400, query);
      assert.equal(res.json().error, "INVALID_QUERY", query);
    }
    const maxPage = await app.inject({
      method: "GET",
      url: `${path}?page=9007199254740991&pageSize=200&period=1d`,
      headers,
    });
    assert.equal(maxPage.statusCode, 200);
    assert.deepEqual(maxPage.json().entries, []);
  });
});

test("invalid local facts fail closed rather than guessing ownership, timing or amount precision", () => {
  const mutations: Array<(data: any) => void> = [
    (d) => {
      d.schemaVersion = 2;
    },
    (d) => {
      d.dataSource = "production";
    },
    (d) => {
      d.unexpected = true;
    },
    (d) => {
      d.observedAt = "+012026-01-01T00:00:00.000Z";
    },
    (d) => {
      d.generatedAt = "2026-10-30T00:00:00.000Z";
    },
    (d) => {
      d.owners.push(d.owners[0]);
    },
    (d) => {
      d.owners.push({ ...d.owners[0], userId: "other" });
    },
    (d) => {
      d.owners[0].wallets.push("z-solana");
    },
    (d) => {
      d.owners[0].walletAddress = "unknown";
    },
    (d) => {
      d.owners[0].twitterId = "https://unexpected";
    },
    (d) => {
      d.owners[0].isVerified = 1;
    },
    (d) => {
      d.payouts.push(d.payouts[0]);
    },
    (d) => {
      d.payouts[0].status = "unknown";
    },
    (d) => {
      d.payouts[0].paidAt = null;
    },
    (d) => {
      d.payouts[0].paidAt = "2026-10-30T00:00:00.000Z";
    },
    (d) => {
      d.payouts[0].paidAt = "2026-02-30T00:00:00.000Z";
    },
    (d) => {
      d.payouts[0].paidAt = "2026-10-28T12:00:00Z";
    },
    ...[0, "0", "-1", "01", "1.5", "1e6", "9007199254740992"].map(
      (value) => (d: any) => {
        d.payouts[0].amountAtomic = value;
      },
    ),
    (d) => {
      d.windows.all = d.windows["1d"];
    },
    (d) => {
      d.windows["1d"].startAt = now;
    },
    (d) => {
      d.windows["1d"].endAt = "2026-10-30T00:00:00.000Z";
    },
    (d) => {
      d.payouts[0].amountAtomic = "9007199254740991";
      d.payouts = [d.payouts[0]];
    },
    (d) => {
      d.payouts[0].amountAtomic = "9007199254000000";
      d.payouts[1].amountAtomic = "1000000";
    },
  ];
  for (const [index, mutate] of mutations.entries()) {
    const data = dataset();
    mutate(data);
    assert.throws(() => new PayoutsStore(data), TypeError, `mutation ${index}`);
  }
});

test("bounded startup loader reads only explicit regular UTF-8 JSON and leaves bytes untouched", () => {
  assert.equal(loadPayoutsStore(undefined), undefined);
  assert.equal(loadPayoutsStore(""), undefined);
  const dir = mkdtempSync(join(tmpdir(), "pump-payouts-test-"));
  const file = join(dir, "facts.json");
  try {
    const bytes = Buffer.from(JSON.stringify(dataset()));
    writeFileSync(file, bytes);
    assert.deepEqual(
      loadPayoutsStore(file)!.leaderboard(),
      new PayoutsStore(dataset()).leaderboard(),
    );
    assert.deepEqual(readFileSync(file), bytes);
    assert.throws(() => loadPayoutsStore(dir));
    writeFileSync(file, Buffer.from([0xff]));
    assert.throws(() => loadPayoutsStore(file));
    writeFileSync(file, "{");
    assert.throws(() => loadPayoutsStore(file));
    truncateSync(file, 16 * 1024 * 1024 + 1);
    assert.throws(() => loadPayoutsStore(file));
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("startup loader rejects symlink files when creation is permitted", (t) => {
  const dir = mkdtempSync(join(tmpdir(), "pump-payouts-symlink-test-"));
  const file = join(dir, "facts.json");
  const link = join(dir, "link");
  try {
    writeFileSync(file, JSON.stringify(dataset()));
    try {
      symlinkSync(file, link);
    } catch (error) {
      if (process.platform === "win32" && (error as NodeJS.ErrnoException).code === "EPERM") {
        t.skip("Windows account cannot create file symlinks; requires Developer Mode or symlink privilege");
        return;
      }
      throw error;
    }
    assert.throws(() => loadPayoutsStore(link));
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("declared payout behavior is bound to immutable raw factory bytes, never executed", () => {
  const bytes = readFileSync(
    new URL(
      "../../../evidence/web/objects/2b47dd0b38a1608f.js",
      import.meta.url,
    ),
  );
  assert.equal(
    createHash("sha256").update(bytes).digest("hex"),
    "e78d2f38b06f971847c18dd05457c75afc85208135f50d6e4022a5f197e8839d",
  );
  const factory = new TextDecoder("utf-8", { fatal: true })
    .decode(bytes)
    .slice(295433, 300163);
  assert.equal(
    createHash("sha256").update(factory).digest("hex"),
    "36fb23be0c2cded3fa8b2c242b0ebf06a594381c34236e2341fa6408e635118d",
  );
  for (const declaration of [
    "GET /payouts/leaderboard",
    "leaderboards.read",
    "top-500",
    "Total distinct earners on the whole board (not capped)",
    "in-flight/failed/rejected never count",
    "never on the API host",
    "stored 6-decimal atomic amount",
  ])
    assert.ok(factory.includes(declaration));
  assert.equal(
    spec.paths["/payouts/leaderboard"].get["x-api-scope"],
    "leaderboards.read",
  );
});

test('owner wallet arrays must not contain absent positions',()=>{
  const data=dataset();data.owners[0].wallets=new Array(1);data.owners[0].walletAddress=null;
  assert.throws(()=>new PayoutsStore(data),/wallet|owner|array/);
  assert.doesNotThrow(()=>new PayoutsStore(dataset()));
});
