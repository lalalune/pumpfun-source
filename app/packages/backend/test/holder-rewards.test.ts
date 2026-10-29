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
import { buildApp } from "../src/app.js";
import {
  HolderRewardsStore,
  loadHolderRewardsStore,
  type HolderRewardsCoin,
  type HolderRewardsDataset,
} from "../src/holder-rewards-store.js";
import { assertSchema } from "../src/schema-validator.js";

const now = "2026-10-29T00:00:00.000Z";
const path = "/services/frontend/fees/holder-rewards";
// Synthetic base58-shaped quote mints; no production record is used.
const QA = `QuoteA${"1".repeat(36)}`;
const QB = `QuoteB${"1".repeat(36)}`;
const contract = JSON.parse(
  readFileSync(
    new URL("../../../contracts/original-holder-rewards.json", import.meta.url),
    "utf8",
  ),
);
function conforms(body: unknown) {
  assertSchema(
    body,
    contract.declarations["x-holder-rewards-response"],
    "holder rewards page",
    contract.declarations,
  );
}
function coin(
  mint: string,
  quote: string,
  lastTradeAt: string | null,
): HolderRewardsCoin {
  return {
    mint,
    holderRewardsPda: `pda-${mint}`,
    name: null,
    symbol: null,
    imageUri: null,
    createdAt: "2026-10-01T00:00:00.000Z",
    lastTradeAt,
    marketCapUsd: null,
    athMarketCapUsd: null,
    isGraduated: false,
    isLive: false,
    isNsfw: false,
    quoteMintAddress: quote,
    socials: { twitter: null, telegram: null, website: null },
    accrued: null,
    payouts: null,
  };
}
function accrued(quote: string, usdAtTrade: string | null, numTrades: number) {
  return {
    quoteMintAddress: quote,
    quote: "12.5",
    usdAtTrade,
    usdNow: usdAtTrade === null ? null : "260",
    numTrades,
    firstTradeAt: "2026-10-02T00:00:00.000Z",
    lastTradeAt: "2026-10-28T12:00:00.000Z",
  };
}
function payouts(
  quote: string,
  usd: string | null,
  payoutCount: number,
  recipientCount: number,
  lastPayoutAt: string,
) {
  return {
    quoteMintAddress: quote,
    paidToHolders: "5000000",
    paidToHoldersQuote: usd === null ? null : "5",
    paidToHoldersUsd: usd,
    opsCharge: null,
    payoutCount,
    recipientCount,
    lastPayoutAt,
  };
}
function dataset(): HolderRewardsDataset {
  const a = {
    ...coin("coin-a", QA, "2026-10-28T12:00:00.000Z"),
    accrued: accrued(QA, "250.5", 40),
    payouts: payouts(QA, "100", 2, 3, "2026-10-28T10:00:00.000Z"),
  };
  const b = {
    ...coin("coin-b", QA, "2026-10-28T20:00:00.000Z"),
    accrued: accrued(QA, "1000", 5),
  };
  const c = {
    ...coin("coin-c", QB, null),
    accrued: accrued(QB, null, 7),
    payouts: payouts(QB, null, 1, 2, "2026-10-27T10:00:00.000Z"),
  };
  const d = coin("coin-d", QB, null);
  return {
    schemaVersion: 1,
    dataSource: "synthetic",
    observedAt: now,
    generatedAt: "2026-10-28T23:59:00.000Z",
    coins: [d, c, a, b],
    quotes: {
      [QA]: {
        mint: QA,
        decimals: 6,
        usdPrice: 20,
        symbol: "QA",
        name: null,
        imageUri: null,
      },
      [QB]: {
        mint: QB,
        decimals: null,
        usdPrice: null,
        symbol: null,
        name: null,
        imageUri: null,
      },
    },
    totals: {
      coinCount: 4,
      payingCount: 2,
      accruedUsdAtTrade: "1250.5",
      accruedUsdNow: "520",
      unpricedCoinCount: 2,
      walletsRewarded: 5,
      walletsRewardedDistinct: 4,
      payoutCount: 3,
    },
    byQuote: [
      {
        quoteMintAddress: QA,
        coinCount: 2,
        payingCount: 1,
        accrued: "25000000",
        accruedUsdAtTrade: "1250.5",
        paid: "5000000",
      },
      {
        quoteMintAddress: QB,
        coinCount: 2,
        payingCount: 1,
        accrued: "0",
        accruedUsdAtTrade: null,
        paid: "5000000",
      },
    ],
  };
}
async function withApp(
  run: (app: ReturnType<typeof buildApp>) => Promise<void>,
  data: HolderRewardsDataset | undefined = dataset(),
) {
  const app = buildApp(
    [],
    data ? { holderRewardsStore: new HolderRewardsStore(data) } : {},
  );
  try {
    await run(app);
  } finally {
    await app.close();
  }
}
async function mints(app: ReturnType<typeof buildApp>, query: string) {
  const res = await app.inject({ method: "GET", url: `${path}?${query}` });
  assert.equal(res.statusCode, 200, res.body);
  return res.json().coins.map((row: HolderRewardsCoin) => row.mint);
}

test("without an explicit book the route keeps the existing 501 fallback", async () => {
  const app = buildApp([], {});
  try {
    const res = await app.inject({ method: "GET", url: `${path}?page=1` });
    assert.equal(res.statusCode, 501);
    assert.equal(res.json().error, "COMPATIBILITY_NOT_IMPLEMENTED");
  } finally {
    await app.close();
  }
});

test("page mode serves the supplied book and satisfies the captured declaration", async () => {
  await withApp(async (app) => {
    const res = await app.inject({ method: "GET", url: `${path}?page=1` });
    assert.equal(res.statusCode, 200);
    const body = res.json();
    conforms(body);
    assert.deepEqual(Object.keys(body), [
      "generatedAt",
      "coins",
      "next",
      "quotes",
      "totals",
      "matchingCount",
      "offset",
      "byQuote",
    ]);
    assert.equal(body.generatedAt, "2026-10-28T23:59:00.000Z");
    assert.equal(body.next, null);
    assert.equal(body.matchingCount, 4);
    assert.equal(body.offset, 0);
    assert.deepEqual(body.totals, dataset().totals);
    assert.deepEqual(body.quotes, dataset().quotes);
    assert.equal(res.headers["x-reconstruction-data-source"], "synthetic");
    assert.equal(res.headers["x-reconstruction-observed-at"], now);
    assert.equal(
      res.headers["x-reconstruction-compatibility"],
      "local-unqualified",
    );
    // The declaration says the route sets no Cache-Control of its own.
    assert.equal(res.headers["cache-control"], undefined);
  });
});

test("sorts order non-null values by direction, keep nulls last and break ties by mint", async () => {
  await withApp(async (app) => {
    assert.deepEqual(await mints(app, "page=1"), [
      "coin-b",
      "coin-a",
      "coin-c",
      "coin-d",
    ]);
    assert.deepEqual(await mints(app, "sort=accrued&direction=asc"), [
      "coin-a",
      "coin-b",
      "coin-c",
      "coin-d",
    ]);
    assert.deepEqual(await mints(app, "sort=trades"), [
      "coin-a",
      "coin-c",
      "coin-b",
      "coin-d",
    ]);
    assert.deepEqual(await mints(app, "sort=trades&direction=asc"), [
      "coin-b",
      "coin-c",
      "coin-a",
      "coin-d",
    ]);
    assert.deepEqual(await mints(app, "sort=wallets"), [
      "coin-a",
      "coin-c",
      "coin-b",
      "coin-d",
    ]);
    assert.deepEqual(await mints(app, "sort=lastPayout"), [
      "coin-a",
      "coin-c",
      "coin-b",
      "coin-d",
    ]);
    assert.deepEqual(await mints(app, "sort=lastTrade"), [
      "coin-b",
      "coin-a",
      "coin-c",
      "coin-d",
    ]);
  });
  const tied = dataset();
  tied.coins[2].accrued!.usdAtTrade = "1000.00";
  await withApp(async (app) => {
    // Decimal comparison is numeric, so 1000.00 ties 1000 and mint order decides both ways.
    assert.deepEqual(await mints(app, "sort=accrued"), [
      "coin-a",
      "coin-b",
      "coin-c",
      "coin-d",
    ]);
    assert.deepEqual(await mints(app, "sort=accrued&direction=asc"), [
      "coin-a",
      "coin-b",
      "coin-c",
      "coin-d",
    ]);
  }, tied);
});

test("filters set the paging denominator; book-wide totals, quotes and facets stay unfiltered", async () => {
  await withApp(async (app) => {
    const paying = (
      await app.inject({ method: "GET", url: `${path}?payingOnly=true` })
    ).json();
    assert.deepEqual(
      paying.coins.map((row: HolderRewardsCoin) => row.mint),
      ["coin-a", "coin-c"],
    );
    assert.equal(paying.matchingCount, 2);
    assert.equal(paying.totals.coinCount, 4);
    assert.equal(paying.byQuote.length, 2);
    assert.deepEqual(await mints(app, `quote=${QB}`), ["coin-c", "coin-d"]);
    assert.deepEqual(await mints(app, `quote=${QB}&payingOnly=true`), [
      "coin-c",
    ]);
    assert.deepEqual(await mints(app, "payingOnly=false"), [
      "coin-b",
      "coin-a",
      "coin-c",
      "coin-d",
    ]);
    const second = (
      await app.inject({ method: "GET", url: `${path}?limit=1&page=2` })
    ).json();
    assert.deepEqual(
      [second.coins[0].mint, second.offset, second.matchingCount],
      ["coin-a", 1, 4],
    );
    conforms(second);
    const distant = (
      await app.inject({ method: "GET", url: `${path}?limit=2000&page=99` })
    ).json();
    assert.deepEqual(
      [distant.coins, distant.offset, distant.matchingCount],
      [[], 196000, 4],
    );
    conforms(distant);
  });
});

test("cursor mode and current-mark sorts are explicit 501 boundaries, never a guessed page", async () => {
  await withApp(async (app) => {
    for (const [query, reason] of [
      ["", "CURSOR_MODE_UNAVAILABLE"],
      ["?cursor=abc", "CURSOR_MODE_UNAVAILABLE"],
      ["?sort=accruedNow", "CURRENT_MARK_SORT_UNAVAILABLE"],
      ["?sort=distributed&page=1", "CURRENT_MARK_SORT_UNAVAILABLE"],
    ]) {
      const res = await app.inject({ method: "GET", url: `${path}${query}` });
      assert.equal(res.statusCode, 501, query);
      assert.deepEqual(
        [res.json().error, res.json().reason],
        ["COMPATIBILITY_NOT_IMPLEMENTED", reason],
      );
    }
  });
});

test("malformed, duplicate, unknown and conflicting queries are local 400s", async () => {
  await withApp(async (app) => {
    for (const [query, error, field] of [
      ["cursor=abc&page=1", "PAGINATION_MODE_CONFLICT", "page"],
      ["page=1&page=2", "DUPLICATE_QUERY_PARAMETER", "page"],
      ["page=1&viewer=x", "UNKNOWN_QUERY_PARAMETER", "viewer"],
      ["sort=volume", "INVALID_QUERY_PARAMETER", "sort"],
      ["direction=up", "INVALID_QUERY_PARAMETER", "direction"],
      [`quote=0${"1".repeat(40)}`, "INVALID_QUERY_PARAMETER", "quote"],
      ["payingOnly=1", "INVALID_QUERY_PARAMETER", "payingOnly"],
      ["page=0", "INVALID_QUERY_PARAMETER", "page"],
      ["page=01", "INVALID_QUERY_PARAMETER", "page"],
      ["limit=2001", "INVALID_QUERY_PARAMETER", "limit"],
      ["limit=0", "INVALID_QUERY_PARAMETER", "limit"],
      [
        `limit=2&page=${Number.MAX_SAFE_INTEGER}`,
        "INVALID_QUERY_PARAMETER",
        "page",
      ],
      // A current-mark sort does not hide malformed parameters behind its 501.
      ["sort=accruedNow&limit=0", "INVALID_QUERY_PARAMETER", "limit"],
      ["sort=distributed&direction=up", "INVALID_QUERY_PARAMETER", "direction"],
    ]) {
      const res = await app.inject({ method: "GET", url: `${path}?${query}` });
      assert.equal(res.statusCode, 400, query);
      assert.deepEqual(res.json(), { statusCode: 400, error, field }, query);
    }
  });
});

test("the supplied book must satisfy the declared row shapes and invariants", () => {
  const breaks: [string, (data: HolderRewardsDataset) => void][] = [
    [
      "duplicate mint",
      (data) => {
        data.coins[1].mint = data.coins[0].mint;
      },
    ],
    [
      "extra row key",
      (data) => {
        (data.coins[0] as unknown as Record<string, unknown>).viewer = true;
      },
    ],
    [
      "missing quote",
      (data) => {
        delete data.quotes[QB];
      },
    ],
    [
      "unreferenced quote",
      (data) => {
        data.quotes.Other = { ...data.quotes[QA], mint: "Other" };
      },
    ],
    [
      "quote key/mint",
      (data) => {
        data.quotes[QA] = { ...data.quotes[QA], mint: QB };
      },
    ],
    [
      "coin count",
      (data) => {
        data.totals.coinCount = 5;
      },
    ],
    [
      "paying count",
      (data) => {
        data.totals.payingCount = 3;
      },
    ],
    [
      "payout sum",
      (data) => {
        data.totals.payoutCount = 4;
      },
    ],
    [
      "wallet sum",
      (data) => {
        data.totals.walletsRewarded = 6;
      },
    ],
    [
      "distinct above sum",
      (data) => {
        data.totals.walletsRewardedDistinct = 6;
      },
    ],
    [
      "distinct below widest coin",
      (data) => {
        data.totals.walletsRewardedDistinct = 2;
      },
    ],
    [
      "USD without price",
      (data) => {
        data.coins[1].payouts!.paidToHoldersUsd = "1";
      },
    ],
    [
      "future generatedAt",
      (data) => {
        data.generatedAt = "2026-10-29T00:00:01.000Z";
      },
    ],
    [
      "future payout",
      (data) => {
        data.coins[2].payouts!.lastPayoutAt = "2026-11-01T00:00:00.000Z";
      },
    ],
    [
      "non-canonical time",
      (data) => {
        data.coins[0].createdAt = "2026-10-01T00:00:00Z";
      },
    ],
    [
      "trade interval",
      (data) => {
        data.coins[2].accrued!.firstTradeAt = "2026-10-28T13:00:00.000Z";
      },
    ],
    [
      "leading-zero decimal",
      (data) => {
        data.coins[3].accrued!.usdAtTrade = "01";
      },
    ],
    [
      "fractional atomic",
      (data) => {
        data.byQuote[0].paid = "1.5";
      },
    ],
    [
      "negative count",
      (data) => {
        data.coins[2].accrued!.numTrades = -1;
      },
    ],
    [
      "byQuote paying above coins",
      (data) => {
        data.byQuote[0].payingCount = 3;
      },
    ],
  ];
  assert.doesNotThrow(() => new HolderRewardsStore(dataset()));
  const blankDisplay = dataset();
  blankDisplay.coins[0].name = "";
  blankDisplay.quotes[QA].symbol = "";
  // Declared z.string() display fields admit empty text; identifiers do not.
  assert.doesNotThrow(() => new HolderRewardsStore(blankDisplay));
  breaks.push([
    "empty mint",
    (data) => {
      data.coins[0].mint = "";
    },
  ]);
  for (const [label, mutate] of breaks) {
    const data = dataset();
    mutate(data);
    assert.throws(() => new HolderRewardsStore(data), TypeError, label);
  }
});

test("a full-size book sorts once per order, not once per request", () => {
  const data = dataset();
  data.coins = Array.from({ length: 100_000 }, (_, index) => ({
    ...coin(`coin-${String(index).padStart(6, "0")}`, QA, null),
    accrued: accrued(
      QA,
      `${(index * 7919) % 100_003}.${index % 100}`,
      index % 50,
    ),
  }));
  data.quotes = { [QA]: data.quotes[QA] };
  data.byQuote = [{ ...data.byQuote[0], coinCount: 100_000, payingCount: 0 }];
  data.totals = {
    ...data.totals,
    coinCount: 100_000,
    payingCount: 0,
    walletsRewarded: 0,
    walletsRewardedDistinct: 0,
    payoutCount: 0,
  };
  const store = new HolderRewardsStore(data);
  const started = performance.now();
  for (let request = 0; request < 20; request++)
    store.page({ page: request + 1 });
  // Sorting on every request blocked about 2.8 s each at this size.
  assert.ok(performance.now() - started < 10_000);
  // Independent reference: two-decimal values are exact as Numbers; the first maximum has the lowest mint.
  const top = data.coins.reduce((best, row) =>
    Number(row.accrued!.usdAtTrade) > Number(best.accrued!.usdAtTrade)
      ? row
      : best,
  );
  assert.equal(store.page({ limit: 1 }).coins[0].mint, top.mint);
});

test("the store owns an immutable copy of the book", () => {
  const data = dataset();
  const store = new HolderRewardsStore(data);
  data.coins[0].mint = "changed";
  data.quotes[QA].usdPrice = 0;
  const first = store.page();
  assert.deepEqual(
    first.coins.map((row) => row.mint),
    ["coin-b", "coin-a", "coin-c", "coin-d"],
  );
  assert.equal(first.quotes[QA].usdPrice, 20);
  assert.throws(() => {
    first.coins[0].mint = "x";
  }, TypeError);
  assert.throws(() => {
    first.totals.coinCount = 0;
  }, TypeError);
  first.coins.pop();
  first.byQuote.pop();
  assert.equal(store.page().coins.length, 4);
  assert.equal(store.page().byQuote.length, 2);
});

test("the file loader refuses a symlink when the account can create one", (t) => {
  const dir = mkdtempSync(join(tmpdir(), "holder-rewards-link-"));
  try {
    const file = join(dir, "book.json");
    writeFileSync(file, JSON.stringify(dataset()));
    const link = join(dir, "link.json");
    try {
      symlinkSync(file, link, "file");
    } catch (error) {
      if (
        process.platform === "win32" &&
        (error as NodeJS.ErrnoException).code === "EPERM"
      ) {
        t.skip(
          "Windows account cannot create file symlinks; requires Developer Mode or symlink privilege",
        );
        return;
      }
      throw error;
    }
    assert.throws(() => loadHolderRewardsStore(link), TypeError);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("the file loader reads one bounded regular UTF-8 file", () => {
  const dir = mkdtempSync(join(tmpdir(), "holder-rewards-"));
  try {
    assert.equal(loadHolderRewardsStore(undefined), undefined);
    const file = join(dir, "book.json");
    writeFileSync(file, JSON.stringify(dataset()));
    assert.equal(loadHolderRewardsStore(file)?.page().matchingCount, 4);
    const invalidUtf8 = join(dir, "bad.json");
    writeFileSync(invalidUtf8, Buffer.from([0x7b, 0xff, 0x7d]));
    assert.throws(() => loadHolderRewardsStore(invalidUtf8), TypeError);
    const large = join(dir, "large.json");
    writeFileSync(large, "");
    truncateSync(large, 64 * 1024 * 1024 + 1);
    assert.throws(() => loadHolderRewardsStore(large), TypeError);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
