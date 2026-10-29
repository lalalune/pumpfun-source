import { expect, test, type Page } from "@playwright/test";
import { PublicKey } from "@solana/web3.js";
import {
  PUMP_AMM_PROGRAM_ID,
  PUMP_PROGRAM_ID,
  userVolumeAccumulatorPda,
} from "@pump-fun/pump-sdk";
const USER = "So11111111111111111111111111111111111111112",
  OTHER = "11111111111111111111111111111111";
function portfolio(address = USER) {
  const group = (program: string, programId: string) => ({
    program,
    programId,
    contextSlot: 300,
    accounts: [],
    mints: [],
  });
  return {
    ok: true,
    address,
    cluster: "mainnet-beta",
    genesisHash: "5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d",
    commitment: "confirmed",
    observedAt: "2026-10-29T05:00:00.000Z",
    endpointHost: "public-rpc.example",
    sol: { lamports: "0", amount: "0.000000000", contextSlot: 300 },
    splToken: group("spl-token", "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"),
    token2022: group(
      "token-2022",
      "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
    ),
    snapshotAtomic: false,
  };
}
function payload(address = USER) {
  return {
    ok: true,
    address,
    programId: PUMP_AMM_PROGRAM_ID.toBase58(),
    recordPda: userVolumeAccumulatorPda(
      new PublicKey(address),
      PUMP_AMM_PROGRAM_ID,
    ).toBase58(),
    cluster: "mainnet-beta",
    commitment: "confirmed",
    contextSlot: 654,
    endpointHost: "public-rpc.example",
    observedAt: "2026-10-29T05:00:00.000Z",
    dataBytes: 90,
    record: {
      user: address,
      needsClaim: true,
      hasTotalClaimedTokens: false,
      totalUnclaimedTokens: "18446744073709551615",
      totalClaimedTokens: "9007199254740993",
      currentSolVolume: "7",
      lastUpdateTimestamp: "-9223372036854775808",
      cashbackEarned: "2",
      totalCashbackClaimed: "0",
    },
  };
}
async function load(page: Page) {
  await page.route("**/api/portfolio?*", (route) =>
    route.fulfill({
      json: portfolio(
        new URL(route.request().url()).searchParams.get("address")!,
      ),
    }),
  );
  await page.goto(`/portfolio?address=${USER}`);
  await expect(page.getByTestId("portfolio-result")).toBeVisible();
}
const panel = (page: Page) => page.getByTestId("public-amm-record"),
  result = (page: Page) => page.getByTestId("public-amm-record-result"),
  read = (page: Page) =>
    page.getByRole("button", {
      name: "Read public PumpSwap record",
      exact: true,
    });
test("actual compiled shared handler and SDK decoder serve controlled90B data under Next", async ({
  page,
}) => {
  test.skip(
    process.env.AMM_RECORD_FIXTURE_TEST !== "1",
    "Explicit temporary loopback fixture runner only",
  );
  let completed!: (value: { status: number; body: unknown }) => void;
  const actual = new Promise<{ status: number; body: unknown }>((resolve) => {
    completed = resolve;
  });
  await page.route("**/api/portfolio/amm-record?*", async (route) => {
    const target = new URL("/amm-record-test-fixture", route.request().url());
    target.search = new URL(route.request().url()).search;
    const response = await route.fetch({ url: target.toString() });
    completed({ status: response.status(), body: await response.json() });
    await route.fulfill({ response });
  });
  await load(page);
  await read(page).click();
  const response = await actual;
  expect(response.status).toBe(200);
  expect(response.body).toMatchObject({
    ok: true,
    programId: PUMP_AMM_PROGRAM_ID.toBase58(),
    dataBytes: 90,
    contextSlot: 654,
    endpointHost: "controlled-fixture.example",
    record: {
      user: USER,
      lastUpdateTimestamp: "-9",
      totalUnclaimedTokens: ((1n << 64n) - 42n).toString(),
    },
  });
  expect(JSON.stringify(response.body)).not.toContain("stableCashback");
  await expect(result(page)).toContainText(((1n << 64n) - 42n).toString());
  await expect(result(page)).toContainText("controlled-fixture.example");
  await expect(result(page)).not.toContainText("stable-cashback");
});
test("explicit AMM read omits credentials and displays exact independent stored counters", async ({
  page,
  context,
}) => {
  await context.addCookies([
    {
      name: "private_test_session",
      value: "not-forwarded",
      domain: "127.0.0.1",
      path: "/",
    },
  ]);
  const requests: unknown[] = [];
  await page.route("**/api/portfolio/amm-record?*", (route) => {
    requests.push({
      method: route.request().method(),
      address: new URL(route.request().url()).searchParams.get("address"),
      cookie: route.request().headers().cookie,
    });
    return route.fulfill({ json: payload() });
  });
  await load(page);
  expect(requests).toEqual([]);
  const before = await page.evaluate(() => ({
    local: { ...localStorage },
    session: { ...sessionStorage },
    cookie: document.cookie,
  }));
  await read(page).click();
  await expect(result(page)).toContainText("18446744073709551615");
  await expect(result(page)).toContainText("9007199254740993");
  await expect(result(page)).toContainText("-9223372036854775808");
  await expect(result(page)).toContainText("Response slot 654");
  await expect(result(page)).toContainText("not calculated entitlements");
  await expect(result(page)).toContainText("No claim or signing action");
  await expect(result(page)).not.toContainText("stable-cashback");
  expect(requests).toEqual([
    { method: "GET", address: USER, cookie: undefined },
  ]);
  await expect(page.locator("html")).toHaveAttribute("data-pf-auth", "out");
  expect(
    await page.evaluate(() => ({
      local: { ...localStorage },
      session: { ...sessionStorage },
      cookie: document.cookie,
    })),
  ).toEqual(before);
});
test("Pump and AMM observations are independently requested and never combined", async ({
  page,
}) => {
  const seen: string[] = [];
  const pump = {
    ...payload(),
    programId: PUMP_PROGRAM_ID.toBase58(),
    recordPda: userVolumeAccumulatorPda(new PublicKey(USER)).toBase58(),
    contextSlot: 321,
    dataBytes: 106,
    record: {
      ...payload().record,
      stableCashbackEarned: "11",
      totalStableCashbackClaimed: "12",
    },
  };
  await page.route("**/api/portfolio/pump-record?*", (route) => {
    seen.push("pump");
    return route.fulfill({ json: pump });
  });
  await page.route("**/api/portfolio/amm-record?*", (route) => {
    seen.push("amm");
    return route.fulfill({ json: payload() });
  });
  await load(page);
  await page
    .getByRole("button", { name: "Read public Pump record", exact: true })
    .click();
  await expect(page.getByTestId("public-pump-record-result")).toBeVisible();
  expect(seen).toEqual(["pump"]);
  await read(page).click();
  await expect(result(page)).toContainText("Response slot 654");
  await expect(page.getByTestId("public-pump-record-result")).toContainText(
    "Response slot 321",
  );
  await expect(panel(page)).toContainText("not combined");
  await expect(result(page)).not.toContainText("stable-cashback");
  expect(seen).toEqual(["pump", "amm"]);
});
test("absent AMM record remains absent rather than zero or ineligibility", async ({
  page,
}) => {
  await page.route("**/api/portfolio/amm-record?*", (route) =>
    route.fulfill({ json: { ...payload(), record: null, dataBytes: null } }),
  );
  await load(page);
  await read(page).click();
  await expect(result(page)).toContainText("No PumpSwap record was returned");
  await expect(result(page)).toContainText("not a zero");
  await expect(result(page).locator("dl")).toHaveCount(0);
});
for (const kind of ["program", "pda", "user", "invented-stable"]) {
  test(`AMM view rejects ${kind} identity or schema substitution`, async ({
    page,
  }) => {
    const data = payload();
    if (kind === "program") data.programId = PUMP_PROGRAM_ID.toBase58();
    if (kind === "pda")
      data.recordPda = userVolumeAccumulatorPda(new PublicKey(USER)).toBase58();
    if (kind === "user") data.record.user = OTHER;
    if (kind === "invented-stable")
      Object.assign(data.record, { stableCashbackEarned: "0" });
    await page.route("**/api/portfolio/amm-record?*", (route) =>
      route.fulfill({ json: data }),
    );
    await load(page);
    await read(page).click();
    await expect(panel(page).getByRole("alert")).toBeVisible();
    await expect(result(page)).toHaveCount(0);
  });
}
test("refresh failure removes old observation and retry can recover", async ({
  page,
}) => {
  let n = 0;
  await page.route("**/api/portfolio/amm-record?*", (route) =>
    route.fulfill(
      ++n === 2
        ? { status: 429, json: { error: "private-provider-body" } }
        : { json: payload() },
    ),
  );
  await load(page);
  await read(page).click();
  await expect(result(page)).toBeVisible();
  await page
    .getByRole("button", {
      name: "Refresh public PumpSwap record",
      exact: true,
    })
    .click();
  await expect(panel(page).getByRole("alert")).toBeVisible();
  await expect(result(page)).toHaveCount(0);
  await expect(panel(page)).not.toContainText("private-provider-body");
  await read(page).click();
  await expect(result(page)).toBeVisible();
});
for (const action of ["wallet navigation", "balance refresh"]) {
  test(`${action} discards a pending AMM read`, async ({ page }) => {
    let release!: () => void, started!: () => void;
    const gate = new Promise<void>((r) => {
        release = r;
      }),
      pending = new Promise<void>((r) => {
        started = r;
      });
    await page.route("**/api/portfolio/amm-record?*", async (route) => {
      started();
      await gate;
      await route.fulfill({ json: payload() }).catch(() => {});
    });
    await load(page);
    await read(page).click();
    await pending;
    if (action === "wallet navigation")
      await page.goto(`/portfolio?address=${OTHER}`);
    else
      await page
        .getByRole("button", { name: "Refresh live balances", exact: true })
        .click();
    await expect(read(page)).toBeEnabled();
    release();
    await expect(result(page)).toHaveCount(0);
  });
}
test("finite deadline clears AMM spinner and rejects late result", async ({
  page,
}) => {
  await page.clock.install();
  let release!: () => void, started!: () => void;
  const gate = new Promise<void>((r) => {
      release = r;
    }),
    pending = new Promise<void>((r) => {
      started = r;
    });
  await page.route("**/api/portfolio/amm-record?*", async (route) => {
    started();
    await gate;
    await route.fulfill({ json: payload() }).catch(() => {});
  });
  await load(page);
  await read(page).click();
  await pending;
  await page.clock.fastForward(20_001);
  await expect(panel(page).getByRole("alert")).toBeVisible();
  await expect(read(page)).toBeEnabled();
  release();
  await expect(result(page)).toHaveCount(0);
});
for (const width of [320, 1440])
  test(`AMM counters and provenance fit ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: width === 320 ? 640 : 900 });
    await page.route("**/api/portfolio/amm-record?*", (route) =>
      route.fulfill({ json: payload() }),
    );
    await load(page);
    await read(page).click();
    await expect(result(page)).toBeVisible();
    await result(page).scrollIntoViewIfNeeded();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.screenshot({
      path: `../../artifacts/amm-wallet-record-${width}.png`,
    });
  });
test("actual compiled AMM route returns complete bounded configuration error", async ({
  page,
}) => {
  test.skip(
    process.env.AMM_RECORD_TEST_NO_RPC !== "1",
    "Requires isolated empty SOLANA_RPC_URL; flag selects tests only",
  );
  await load(page);
  const response = page.waitForResponse(
    (r) => new URL(r.url()).pathname === "/api/portfolio/amm-record",
  );
  await read(page).click();
  const actual = await response;
  expect(actual.status()).toBe(503);
  expect(actual.headers()["cache-control"]).toBe("no-store");
  await expect(panel(page).getByRole("alert")).toBeVisible();
  // The browser client deliberately discards non-OK bodies. Independently check
  // the HTTP body rather than asking CDP to retain a discarded browser response.
  const complete = await page.request.get(
    `/api/portfolio/amm-record?address=${USER}`,
    { timeout: 5000 },
  );
  expect(complete.status()).toBe(503);
  expect((await complete.json()).error.code).toBe("RPC_CONFIGURATION_INVALID");
  expect(complete.headers()["cache-control"]).toBe("no-store");
});
