import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { buildApp, type Fixture } from "../src/app.js";
import {
  PositionsStore,
  type PositionsDataset,
  type PositionFacts,
  type Callout,
  type CalloutUpdate,
} from "../src/positions-store.js";
import { assertSchema } from "../src/schema-validator.js";

const headers = { authorization: `Bearer pf_live_${"a".repeat(49)}` };
const spec = JSON.parse(
  readFileSync(
    new URL("../../../contracts/developer.openapi.json", import.meta.url),
    "utf8",
  ),
);
const now = "2026-10-28T00:00:00.000Z";
const facts = (
  coinMint: string,
  extra: Partial<PositionFacts> = {},
): PositionFacts => ({
  coinMint,
  chainId: 101,
  chain: "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp",
  isExited: false,
  walletAddress: "synthetic-wallet-a",
  amountHeld: 5,
  pnlUsd: null,
  pnlPercentage: null,
  costBasisAmount: null,
  costBasisUsd: null,
  amountBoughtUsd: null,
  amountBought: null,
  tokenPriceUsd: null,
  ...extra,
});
const callout = (): Callout => ({
  calloutId: "callout-a",
  calledOutAtMcap: 100,
  multiple: 1,
  thesis: "Synthetic thesis",
  mediaUrl: null,
  calloutTimestamp: now,
  likes: 0,
  hasLiked: null,
  updates: [],
  updateCount: 25,
  commentCount: 0,
  replyCount: 25,
  maxMultiplier: null,
  maxMultiplierAt: null,
  calloutPrice: 1,
  repostCount: 0,
  quoteCount: 0,
  hasReposted: null,
  actingUserId: null,
  actingUser: null,
  quotedCallout: null,
});
const update = (id: string, createdAt: string | null): CalloutUpdate => ({
  id,
  content: `Synthetic update ${id}`,
  createdAt,
  likeCount: 0,
  mediaUrl: null,
  parentMessageId: "callout-a",
  repostCount: 0,
});
function dataset(): PositionsDataset {
  const a = facts("mint-a", {
    pnlUsd: 20,
    valueUsd: 100,
    tokenPriceUsd: 20,
    updatedAt: now,
    openedAt: "2026-10-01T00:00:00Z",
    tradeCount: 0,
  });
  return {
    schemaVersion: 1,
    dataSource: "synthetic",
    observedAt: now,
    subjects: [
      {
        kind: "person",
        id: "person-a",
        aliases: ["synthetic-wallet-a"],
        positions: [
          { facts: a, calloutId: "callout-a", publicSpam: true },
          {
            facts: facts("mint-b", {
              pnlUsd: 100,
              valueUsd: 5,
              updatedAt: "2026-10-27T00:00:00Z",
            }),
            publicSpam: true,
          },
          {
            facts: facts("mint-c", {
              pnlUsd: -5,
              amountHeld: 0,
              isExited: true,
              amountBoughtUsd: 80,
              amountBought: 8,
              amountSoldUsd: 75,
              updatedAt: "2026-10-26T00:00:00Z",
            }),
          },
          { facts: facts("mint-unknown") },
          {
            facts: facts("evm-mint", {
              chain: "eip155:8453",
              chainId: 8453,
              walletAddress: "synthetic-evm-a",
              pnlUsd: 30,
              valueUsd: null,
            }),
          },
        ],
      },
      { kind: "person", id: "empty-person", aliases: [], positions: [] },
    ],
    coins: [
      {
        coinMint: a.coinMint,
        chainId: a.chainId,
        chain: a.chain,
        coin: {
          name: "Synthetic A",
          symbol: "SYN",
          imageUri: null,
          marketCapUsd: null,
          totalSupply: null,
          protocol: null,
          platform: null,
          program: "pump",
        },
      },
    ],
    callouts: [
      { authorId: "person-a", updatesComplete: true, body: callout() },
    ],
    updates: Array.from({ length: 25 }, (_, i) => ({
      calloutId: "callout-a",
      authorId: "person-a",
      deleted: false,
      hidden: false,
      body: update(
        `update-${String(i).padStart(2, "0")}`,
        `2026-10-${String(i + 1).padStart(2, "0")}T00:00:00Z`,
      ),
    })),
  };
}
const withApp = (data = dataset(), fixtures: Fixture[] = []) =>
  buildApp(fixtures, { positionsStore: new PositionsStore(data) });
const get = (app: ReturnType<typeof buildApp>, url: string) =>
  app.inject({ method: "GET", url, headers });
function contract(
  body: unknown,
  path: "/user-positions/{userId}" | "/user-portfolio/{userId}",
) {
  assertSchema(
    body,
    spec.paths[path].get.responses["200"].content["application/json"].schema,
    path,
    spec,
  );
}

test("mint selection is native, deduplicated, alias-aware and request-ordered", async () => {
  const app = withApp();
  try {
    const res = await get(
      app,
      "/v1/user-positions/synthetic-wallet-a?mints=mint-c,missing,mint-a,mint-a&updatesLimit=0",
    );
    assert.equal(res.statusCode, 200);
    contract(res.json(), "/user-positions/{userId}");
    assert.deepEqual(
      res.json().positions.map((r: any) => r.coinMint),
      ["mint-c", "mint-a"],
    );
    assert.equal(res.headers["x-reconstruction-data-source"], "synthetic");
    assert.equal(res.headers["x-reconstruction-compatibility"], "unqualified");
    assert.equal(res.headers["x-reconstruction-observed-at"], now);
    const [closed, open] = res.json().positions;
    assert.equal(closed.amountBoughtUsd, 80);
    assert.equal(closed.amountSoldUsd, 75);
    assert.equal(open.tradeCount, 0);
    assert.equal(open.callout.updates.length, 0);
    for (const name of [
      "coin",
      "isNative",
      "potentialSpam",
      "userMarkedNonSpam",
      "dustFloorFiltered",
    ])
      assert.equal(name in open, false);
  } finally {
    await app.close();
  }
});
test("unknown financial knowledge stays null or absent, not fabricated", () => {
  const row = new PositionsStore(dataset()).positions("person-a", [
    "mint-unknown",
  ])!.positions[0];
  assert.equal(row.pnlUsd, null);
  assert.equal(row.tokenPriceUsd, null);
  for (const name of [
    "valueUsd",
    "amountSoldUsd",
    "tradeCount",
    "openedAt",
    "updatedAt",
    "realizedPnlUsd",
    "hasTransfers",
  ])
    assert.equal(name in row, false);
  const data = dataset();
  data.subjects[0].positions[0].facts.hasUntrustedUsdBasis = true;
  assert.equal(
    new PositionsStore(data).positions("person-a", ["mint-a"], 0)!.positions[0]
      .hasUntrustedUsdBasis,
    true,
  );
});
test("update join includes only live author replies, newest first, respecting 0/default/20", () => {
  const data = dataset();
  for (const [id, authorId, deleted, hidden] of [
    ["other-author", "other", false, false],
    ["deleted", "person-a", true, false],
    ["hidden", "person-a", false, true],
  ] as const)
    data.updates.push({
      calloutId: "callout-a",
      authorId,
      deleted,
      hidden,
      body: update(id, now),
    });
  data.updates.push({
    calloutId: "callout-a",
    authorId: "person-a",
    deleted: false,
    hidden: false,
    body: { ...update("wrong-parent", now), parentMessageId: "other" },
  });
  const store = new PositionsStore(data);
  assert.equal(
    store.positions("person-a", ["mint-a"], 0)!.positions[0].callout!.updates
      .length,
    0,
  );
  const defaults = store.positions("person-a", ["mint-a"])!.positions[0]
    .callout!;
  assert.deepEqual(
    defaults.updates.map((r) => r.id),
    ["update-24", "update-23", "update-22", "update-21", "update-20"],
  );
  assert.equal(defaults.updateCount, 25);
  assert.equal(
    store.positions("person-a", ["mint-a"], 20)!.positions[0].callout!.updates
      .length,
    20,
  );
});
test("public spam/chain filters happen before count and pagination, and metadata is joined", async () => {
  const app = withApp();
  try {
    const first = await get(
      app,
      "/v1/user-portfolio/person-a?filterSpam=true&pageSize=1",
    );
    contract(first.json(), "/user-portfolio/{userId}");
    assert.equal(first.json().summary.positionCount, 3);
    assert.equal(first.json().positions[0].coinMint, "evm-mint");
    const next = (
      await get(
        app,
        "/v1/user-portfolio/person-a?filterSpam=true&pageSize=1&page=1",
      )
    ).json().positions[0];
    assert.equal(next.coinMint, "mint-a");
    assert.equal(next.potentialSpam, false);
    assert.equal(next.userMarkedNonSpam, false);
    assert.equal(next.dustFloorFiltered, false);
    assert.equal(next.coin.name, "Synthetic A");
    const spam = (
      await get(app, "/v1/user-portfolio/person-a?spamOnly=1")
    ).json();
    assert.equal(spam.summary.positionCount, 1);
    assert.equal(spam.positions[0].coinMint, "mint-b");
    const chain = (
      await get(app, "/v1/user-portfolio/person-a?chainId=8453")
    ).json();
    assert.equal(chain.summary.positionCount, 1);
    assert.equal(chain.positions[0].coinMint, "evm-mint");
  } finally {
    await app.close();
  }
});
test("normalized filters, totalsOnly and distant safe-integer pages stay coherent", async () => {
  const app = withApp();
  try {
    assert.deepEqual(
      (
        await get(
          app,
          "/v1/user-portfolio/person-a?filter=%20all%20&totalsOnly=true",
        )
      ).json(),
      { positions: [], summary: { positionCount: 5 }, updatesApplied: true },
    );
    const closed = (
      await get(app, "/v1/user-portfolio/person-a?filter=CLOSED")
    ).json();
    assert.equal(closed.positions.length, 1);
    assert.equal(closed.positions[0].isExited, true);
    const distant = (
      await get(
        app,
        "/v1/user-portfolio/person-a?page=9007199254740991&pageSize=200",
      )
    ).json();
    assert.deepEqual(distant.positions, []);
    assert.equal(distant.summary.positionCount, 4);
    contract(distant, "/user-portfolio/{userId}");
  } finally {
    await app.close();
  }
});
test("local ordering uses PnL, known value or ledger recency; unknowns last", () => {
  const store = new PositionsStore(dataset());
  assert.deepEqual(
    store.portfolio("person-a")!.positions.map((r) => r.coinMint),
    ["mint-b", "evm-mint", "mint-a", "mint-unknown"],
  );
  for (const sortBy of ["POSITION_SIZE", "RECENCY"] as const)
    assert.deepEqual(
      store.portfolio("person-a", { sortBy })!.positions.map((r) => r.coinMint),
      ["mint-a", "mint-b", "evm-mint", "mint-unknown"],
    );
});
test("coin join cannot cross chains; native cash is portfolio-only and has no coin metadata", () => {
  const data = dataset();
  data.coins[0].chainId = 8453;
  data.coins[0].chain = "eip155:8453";
  data.subjects[0].positions.push({
    facts: facts("native", { isNative: true }),
  });
  const store = new PositionsStore(data),
    rows = store.portfolio("person-a")!.positions;
  assert.equal(rows.find((r) => r.coinMint === "mint-a")!.coin, null);
  assert.equal("coin" in rows.find((r) => r.isNative)!, false);
  assert.deepEqual(store.positions("person-a", ["native"]), { positions: [] });
});
test("unknown subjects are 404; explicitly empty subjects are 200; identities preserve case", async () => {
  const app = withApp();
  try {
    for (const id of ["missing", "PERSON-A", "__proto__"])
      assert.equal(
        (await get(app, `/v1/user-positions/${id}?mints=mint-a`)).statusCode,
        404,
      );
    assert.deepEqual(
      (await get(app, "/v1/user-positions/empty-person?mints=mint-a")).json(),
      { positions: [] },
    );
  } finally {
    await app.close();
  }
});
const invalid = [
  "/user-positions/person-a",
  "/user-positions/person-a?mints=a&mints=b",
  "/user-positions/person-a?mints=a&updatesLimit=-1",
  "/user-positions/person-a?mints=a&updatesLimit=21",
  "/user-positions/person-a?mints=a&updatesLimit=1.1",
  "/user-positions/person-a?mints=a&updatesLimit=",
  `/user-positions/person-a?mints=${Array(201).fill("a").join(",")}`,
  "/user-portfolio/person-a?page=-1",
  "/user-portfolio/person-a?page=9007199254740992",
  "/user-portfolio/person-a?page=1e2",
  "/user-portfolio/person-a?pageSize=0",
  "/user-portfolio/person-a?pageSize=201",
  "/user-portfolio/person-a?filter=bogus",
  "/user-portfolio/person-a?sortBy=bogus",
  "/user-portfolio/person-a?totalsOnly=yes",
  "/user-portfolio/person-a?spamOnly=true&filterSpam=true",
  "/user-portfolio/person-a?chainId=NaN",
  "/user-portfolio/person-a?page=1&page=2",
  "/user-portfolio/person-a?query=unbound",
];
for (const url of invalid)
  test(`reject invalid query: ${url.slice(0, 110)}`, async () => {
    const app = withApp();
    try {
      assert.equal((await get(app, `/v1${url}`)).statusCode, 400);
    } finally {
      await app.close();
    }
  });
test("200 mints allowed; empty CSV matches nothing under the declared string-array contract", async () => {
  const app = withApp();
  try {
    assert.equal(
      (
        await get(
          app,
          `/v1/user-positions/person-a?mints=${Array(200).fill("mint-a").join(",")}`,
        )
      ).statusCode,
      200,
    );
    assert.deepEqual(
      (await get(app, "/v1/user-positions/person-a?mints=")).json(),
      { positions: [] },
    );
  } finally {
    await app.close();
  }
});
test("API key gate remains before reads; perpetual mints remain explicitly deferred", async () => {
  const app = withApp();
  try {
    assert.equal(
      (await app.inject("/v1/user-positions/person-a?mints=mint-a")).statusCode,
      401,
    );
    const res = await get(
      app,
      "/v1/user-positions/person-a?mints=hlcore:mainnet:BTC",
    );
    assert.equal(res.statusCode, 501);
    assert.equal(res.json().reason, "PERPETUAL_POSITIONS_DEFERRED");
  } finally {
    await app.close();
  }
});
test("no store preserves 501/replay; configured native read does not serve a matching fixture", async () => {
  const fixture: Fixture = {
    method: "GET",
    path: "/v1/user-positions/person-a",
    query: { mints: "mint-a", updatesLimit: "0" },
    status: 200,
    body: { replayOnly: true },
    source: "synthetic:test",
  };
  const blank = buildApp(),
    replay = buildApp([fixture]),
    native = withApp(dataset(), [fixture]);
  try {
    const url = "/v1/user-positions/person-a?mints=mint-a&updatesLimit=0";
    assert.equal((await get(blank, url)).statusCode, 501);
    assert.deepEqual((await get(replay, url)).json(), fixture.body);
    assert.equal(
      (await get(native, url)).json().positions[0].coinMint,
      "mint-a",
    );
    assert.equal(
      (await get(native, "/v1/portfolio-summary?period=1d&user=person-a"))
        .statusCode,
      501,
    );
  } finally {
    await Promise.all([blank.close(), replay.close(), native.close()]);
  }
});
test("unknown update completeness is not known-empty", async () => {
  const data = dataset();
  data.callouts[0].updatesComplete = false;
  const app = withApp(data);
  try {
    assert.equal(
      (await get(app, "/v1/user-positions/person-a?mints=mint-a")).json()
        .reason,
      "CALLOUT_UPDATES_UNAVAILABLE",
    );
    assert.equal(
      (
        await get(
          app,
          "/v1/user-positions/person-a?mints=mint-a&updatesLimit=0",
        )
      ).statusCode,
      200,
    );
    const page = (await get(app, "/v1/user-portfolio/person-a")).json();
    assert.equal(page.updatesApplied, false);
    assert.equal(
      page.positions.find((r: any) => r.coinMint === "mint-a").callout.updates
        .length,
      0,
    );
    assert.equal(
      (await get(app, "/v1/user-portfolio/person-a?totalsOnly=true")).json()
        .updatesApplied,
      true,
    );
  } finally {
    await app.close();
  }
});
test("ambiguous mint fails closed, but portfolio retains both chain rows", async () => {
  const data = dataset();
  data.subjects[0].positions.push({
    facts: facts("mint-a", { chain: "eip155:8453", chainId: 8453 }),
  });
  const app = withApp(data);
  try {
    const res = await get(app, "/v1/user-positions/person-a?mints=mint-a");
    assert.equal(res.statusCode, 501);
    assert.equal(res.json().reason, "AMBIGUOUS_MINT_CHAIN");
    assert.equal(
      (await get(app, "/v1/user-portfolio/person-a")).json().summary
        .positionCount,
      5,
    );
  } finally {
    await app.close();
  }
});
test("input and output mutation cannot rewrite the retained snapshot", () => {
  const data = dataset(),
    store = new PositionsStore(data);
  data.subjects[0].positions[0].facts.amountHeld = 999;
  const row = store.positions("person-a", ["mint-a"])!.positions[0];
  row.amountHeld = 888;
  row.callout!.updates[0].content = "changed";
  assert.equal(
    store.positions("person-a", ["mint-a"])!.positions[0].amountHeld,
    5,
  );
  assert.notEqual(
    store.positions("person-a", ["mint-a"])!.positions[0].callout!.updates[0]
      .content,
    "changed",
  );
});
const mutations: Array<[string, (data: any) => void]> = [
  ["version", (d) => delete d.schemaVersion],
  ["data classification", (d) => (d.dataSource = "upstream")],
  ["timestamp", (d) => (d.observedAt = "today")],
  ["duplicate alias", (d) => d.subjects[1].aliases.push("person-a")],
  [
    "duplicate position",
    (d) => d.subjects[0].positions.push(d.subjects[0].positions[0]),
  ],
  ["group", (d) => (d.subjects[0].kind = "group")],
  ["NaN", (d) => (d.subjects[0].positions[0].facts.pnlUsd = NaN)],
  [
    "required price",
    (d) => delete d.subjects[0].positions[0].facts.tokenPriceUsd,
  ],
  [
    "fractional trade count",
    (d) => (d.subjects[0].positions[0].facts.tradeCount = 0.5),
  ],
  [
    "unsafe trade count",
    (d) => (d.subjects[0].positions[0].facts.tradeCount = 9007199254740992),
  ],
  [
    "ledger cursor",
    (d) => (d.subjects[0].positions[0].facts.lastSlotIndexId = "1"),
  ],
  ["exit openedAt", (d) => (d.subjects[0].positions[0].facts.isExited = true)],
  ["foreign callout", (d) => (d.callouts[0].authorId = "other")],
  ["missing callout", (d) => (d.callouts = [])],
  ["update completeness", (d) => delete d.callouts[0].updatesComplete],
  [
    "embedded updates",
    (d) => d.callouts[0].body.updates.push(d.updates[0].body),
  ],
  ["private likes", (d) => (d.callouts[0].body.hasLiked = true)],
  [
    "private rescue",
    (d) => (d.subjects[0].positions[0].facts.userMarkedNonSpam = true),
  ],
  [
    "private dust",
    (d) => (d.subjects[0].positions[0].facts.dustFloorFiltered = true),
  ],
  ["native mint", (d) => (d.subjects[0].positions[0].facts.isNative = true)],
  [
    "perpetual",
    (d) =>
      (d.subjects[0].positions[0].facts.assetClass = "ASSET_CLASS_PERPETUAL"),
  ],
  [
    "other chain",
    (d) => (d.subjects[0].positions[0].facts.chain = "near:mainnet"),
  ],
  ["duplicate update", (d) => d.updates.push(d.updates[0])],
  ["unbound update", (d) => (d.updates[0].calloutId = "unknown")],
  ["duplicate coin", (d) => d.coins.push(d.coins[0])],
  ["null coin", (d) => (d.coins[0].coin = null)],
];
for (const [name, mutate] of mutations)
  test(`materialization rejects ${name}`, () => {
    const data = dataset();
    mutate(data);
    assert.throws(() => new PositionsStore(data));
  });
test("all represented success bodies conform to official OpenAPI schema", () => {
  const store = new PositionsStore(dataset());
  for (const filter of ["OPEN", "CLOSED", "ALL"] as const)
    for (const sortBy of ["PNL", "POSITION_SIZE", "RECENCY"] as const)
      for (const totalsOnly of [false, true])
        for (const page of [0, 1, 10])
          contract(
            store.portfolio("person-a", {
              filter,
              sortBy,
              totalsOnly,
              page,
              pageSize: 1,
            }),
            "/user-portfolio/{userId}",
          );
  for (const limit of [0, 5, 20])
    contract(
      store.positions("person-a", ["mint-a", "mint-c", "mint-unknown"], limit),
      "/user-positions/{userId}",
    );
});

test("identical metrics and update timestamps use documented deterministic local tie-breaks", () => {
  const data = dataset();
  data.subjects[0].positions.push({ facts: facts("mint-aa", { pnlUsd: 20 }) });
  data.updates.push({
    calloutId: "callout-a",
    authorId: "person-a",
    deleted: false,
    hidden: false,
    body: update("update-24-a", "2026-10-25T00:00:00Z"),
  });
  const store = new PositionsStore(data);
  assert.deepEqual(
    store
      .positions("person-a", ["mint-a"], 2)!
      .positions[0].callout!.updates.map((u) => u.id),
    ["update-24", "update-24-a"],
  );
  const tied = store
    .portfolio("person-a")!
    .positions.filter((r) => r.pnlUsd === 20);
  assert.deepEqual(
    tied.map((r) => r.coinMint),
    ["mint-a", "mint-aa"],
  );
});
test("invalid calendar dates are rejected instead of normalized silently", () => {
  const data = dataset();
  data.observedAt = "2026-02-30T00:00:00Z";
  assert.throws(() => new PositionsStore(data), /calendar date/);
});
test("all-empty snapshots and local-materialized classification work without a synthetic seed", async () => {
  const data = dataset();
  data.dataSource = "local-materialized";
  data.subjects = [];
  data.coins = [];
  data.callouts = [];
  data.updates = [];
  const app = withApp(data);
  try {
    assert.equal(
      (await get(app, "/v1/user-portfolio/missing")).statusCode,
      404,
    );
  } finally {
    await app.close();
  }
});

const enrichmentAdmissionCases: Array<[string, (data: any) => void]> = [
  [
    "callout perp without asset class",
    (d) => {
      d.callouts[0].body.perp = {
        side: "long",
        leverageBps: 100,
        entryPx: null,
        closePx: null,
        closedAt: null,
      };
    },
  ],
  [
    "callout unsupported chain",
    (d) => {
      d.callouts[0].body.chain = "near:mainnet";
    },
  ],
  [
    "callout invalid calendar timestamp",
    (d) => {
      d.callouts[0].body.calloutTimestamp = "2026-02-30T00:00:00Z";
    },
  ],
  [
    "callout unsafe likes",
    (d) => {
      d.callouts[0].body.likes = Number.MAX_SAFE_INTEGER + 1;
    },
  ],
  [
    "callout fractional update count",
    (d) => {
      d.callouts[0].body.updateCount = -1.5;
    },
  ],
  [
    "update unsafe like count",
    (d) => {
      d.updates[0].body.likeCount = Number.MAX_SAFE_INTEGER + 1;
    },
  ],
  [
    "update negative view count",
    (d) => {
      d.updates[0].body.viewCount = -1;
    },
  ],
  [
    "empty row chain",
    (d) => {
      d.subjects[0].positions[0].facts.chain = "";
    },
  ],
];
for (const [name, mutate] of enrichmentAdmissionCases)
  test(`spot enrichment admission rejects ${name}`, () => {
    const data = dataset();
    mutate(data);
    assert.throws(() => new PositionsStore(data));
  });
test("safe-integer counter boundary and nullable callout fields are retained exactly", () => {
  const data = dataset();
  data.subjects[0].positions[0].facts.tradeCount = Number.MAX_SAFE_INTEGER;
  data.callouts[0].body.likes = Number.MAX_SAFE_INTEGER;
  data.callouts[0].body.chain = null;
  data.callouts[0].body.perp = null;
  data.updates[24].body.likeCount = Number.MAX_SAFE_INTEGER;
  const row = new PositionsStore(data).positions("person-a", ["mint-a"])!
    .positions[0];
  assert.equal(row.tradeCount, Number.MAX_SAFE_INTEGER);
  assert.equal(row.callout!.likes, Number.MAX_SAFE_INTEGER);
  assert.equal(row.callout!.chain, null);
  assert.equal(row.callout!.perp, null);
  assert.equal(row.callout!.updates[0].likeCount, Number.MAX_SAFE_INTEGER);
});
test("conflicting spam filters are invalid even for an unknown subject", async () => {
  const app = withApp();
  try {
    assert.equal(
      (
        await get(
          app,
          "/v1/user-portfolio/missing?filterSpam=true&spamOnly=true",
        )
      ).statusCode,
      400,
    );
  } finally {
    await app.close();
  }
});

function quoted(): NonNullable<Callout["quotedCallout"]> {
  return {
    coinMint: "quoted-mint",
    walletAddress: null,
    userId: null,
    userName: null,
    profileImage: null,
    isVerified: false,
    verifiedBadgeVisible: false,
    accountKind: "person",
    xUsername: null,
    xFollowerCount: 0,
    mediaUrl: null,
    callout: { ...callout(), calloutId: "quoted-callout" },
  };
}
const quotedAdmissionCases: Array<
  [string, (quote: NonNullable<Callout["quotedCallout"]>) => void]
> = [
  [
    "perp payload",
    (q) => {
      q.callout.perp = {
        side: "short",
        leverageBps: 100,
        entryPx: null,
        closePx: null,
        closedAt: null,
      };
    },
  ],
  [
    "unsupported parent chain",
    (q) => {
      q.chain = "near:mainnet";
    },
  ],
  [
    "unsupported child chain",
    (q) => {
      q.callout.chain = "ton:-239";
    },
  ],
  [
    "invalid timestamp",
    (q) => {
      q.callout.maxMultiplierAt = "2026-02-30T00:00:00Z";
    },
  ],
  [
    "unsafe social counter",
    (q) => {
      q.xFollowerCount = Number.MAX_SAFE_INTEGER + 1;
    },
  ],
  [
    "fractional nested reply count",
    (q) => {
      q.callout.replyCount = 1.25;
    },
  ],
  [
    "private nested liked state",
    (q) => {
      q.callout.hasLiked = true;
    },
  ],
  [
    "second expanded quote",
    (q) => {
      q.callout.quotedCallout = quoted();
    },
  ],
];
for (const [name, mutate] of quotedAdmissionCases)
  test(`nested quote admission rejects ${name}`, () => {
    const data = dataset(),
      quote = quoted();
    mutate(quote);
    data.callouts[0].body.quotedCallout = quote;
    assert.throws(() => new PositionsStore(data));
  });
test("quoted callout updates cannot bypass the separate update relation", () => {
  const data = dataset();
  const quote = quoted();
  quote.callout.updates = [
    {
      ...update("unjoined-quoted-update", now),
      parentMessageId: quote.callout.calloutId,
    },
  ];
  data.callouts[0].body.quotedCallout = quote;
  assertSchema(
    data.callouts[0].body,
    spec.components.schemas.Shared_fceda4efe6cd,
    "schema-valid quoted updates",
    spec,
  );
  // Embedded replies bypass author/visibility joins, even with updatesLimit=0.
  assert.throws(
    () => new PositionsStore(data),
    /updates must come from the separate update relation/,
  );
});

test("a valid one-level spot quote retains its nullable/unknown fields and zero counters", () => {
  const data = dataset();
  data.callouts[0].body.quotedCallout = quoted();
  const quote = new PositionsStore(data).positions("person-a", ["mint-a"], 0)!
    .positions[0].callout!.quotedCallout!;
  assert.equal(quote.callout.calloutId, "quoted-callout");
  assert.equal(quote.xFollowerCount, 0);
  assert.equal(quote.callout.quotedCallout, null);
});

function collectible(): NonNullable<Callout["collectible"]> {
  return {
    assetId: "synthetic-card",
    provider: null,
    status: null,
    name: null,
    imageUrl: null,
    grade: null,
    setName: null,
    markUsd: null,
    markSource: null,
    markAsOf: null,
    insuredValueUsd: null,
    insuredAsOf: null,
    buybackValueUsd: null,
    buybackExpiresAt: null,
    listing: null,
  };
}
for (const nested of [false, true])
  test(`non-null collectible payload cannot bypass spot admission (${nested ? "quoted" : "direct"})`, () => {
    const data = dataset();
    if (nested) {
      data.callouts[0].body.quotedCallout = quoted();
      data.callouts[0].body.quotedCallout.callout.collectible = collectible();
    } else data.callouts[0].body.collectible = collectible();
    assertSchema(
      data.callouts[0].body,
      spec.components.schemas.Shared_fceda4efe6cd,
      "schema-valid collectible callout",
      spec,
    );
    assert.throws(() => new PositionsStore(data), /non-spot enrichment/);
  });

test('direct portfolio query flags are booleans rather than truthy values',()=>{
  const store=new PositionsStore(dataset());
  for(const field of ['totalsOnly','filterSpam','spamOnly'])for(const value of ['false',0,null])assert.throws(()=>store.portfolio('person-a',{[field]:value} as any),/Invalid portfolio/);
  assert.doesNotThrow(()=>store.portfolio('person-a',{totalsOnly:false,filterSpam:false,spamOnly:false}));
});

test('position state timestamps cannot exceed their observation checkpoint',()=>{
  for(const field of ['updatedAt','openedAt'] as const){
    const data=dataset();(data.subjects[0].positions[0].facts as any)[field]='2026-10-29T00:00:00Z';
    assert.throws(()=>new PositionsStore(data),/observedAt/);
  }
  assert.doesNotThrow(()=>new PositionsStore(dataset()));
});

for (const field of ['calloutTimestamp', 'maxMultiplierAt'] as const) {
  for (const nested of [false, true]) test(`position ${nested ? 'quoted ' : ''}${field} cannot exceed observedAt`, () => {
    const data = dataset();
    const body = nested ? (data.callouts[0].body.quotedCallout = quoted()).callout : data.callouts[0].body;
    body[field] = '2026-10-29T00:00:00.000Z';
    assert.throws(() => new PositionsStore(data), /enrichment timestamp exceeds observedAt/);
  });
}

test('position update enrichment cannot contain facts after observedAt', () => {
  const data = dataset();
  data.updates[0].body.createdAt = '2026-10-29T00:00:00.000Z';
  assert.throws(() => new PositionsStore(data), /enrichment timestamp exceeds observedAt/);
});

test('checkpoint equality and unknown enrichment timestamps remain valid', () => {
  const data = dataset();
  data.callouts[0].body.maxMultiplierAt = now;
  data.callouts[0].body.quotedCallout = quoted();
  data.updates[0].body.createdAt = null;
  const store = new PositionsStore(data);
  assert.equal(store.positions('person-a', ['mint-a'])!.positions[0].callout!.maxMultiplierAt, now);
});
