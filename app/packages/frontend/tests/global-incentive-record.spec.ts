import { expect, test, type Page } from "@playwright/test";
import contract from "../src/app/global-incentive-record/contract.json";
const ADDRESS = "So11111111111111111111111111111111111111112";
const OTHER = "11111111111111111111111111111111";
function portfolio(address: string) {
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
    endpointHost: "controlled.example",
    sol: { lamports: "0", amount: "0.000000000", contextSlot: 300 },
    splToken: group("spl-token", "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"),
    token2022: group(
      "token-2022",
      "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
    ),
    snapshotAtomic: false,
  };
}
function payload() {
  return {
    ok: true,
    programId: contract.programId,
    recordPda: contract.recordPda,
    cluster: "mainnet-beta",
    commitment: "confirmed",
    contextSlot: 400,
    endpointHost: "controlled.example",
    observedAt: "2026-10-29T05:00:00.000Z",
    dataBytes: 544,
    record: {
      startTime: "-9223372036854775808",
      endTime: "9223372036854775807",
      secondsInADay: "86400",
      mint: ADDRESS,
      totalTokenSupply: Array.from({ length: 30 }, (_, i) =>
        (18446744073709551615n - BigInt(i)).toString(),
      ),
      solVolumes: Array.from({ length: 30 }, (_, i) =>
        (18446744073709551585n - BigInt(i)).toString(),
      ),
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
  await page.goto(`/portfolio?address=${ADDRESS}`);
  await expect(page.getByTestId("portfolio-result")).toBeVisible();
}
const panel = (page: Page) => page.getByTestId("public-incentive-schedule");
const read = (page: Page) =>
  page.getByRole("button", {
    name: "Read public incentive schedule",
    exact: true,
  });
const result = (page: Page) =>
  page.getByTestId("public-incentive-schedule-result");
test("explicit action traverses the actual compiled handler and SDK decoder without loading user records or credentials", async ({
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
  const requests: { url: string; cookie: string | undefined }[] = [];
  let userReads = 0;
  await page.route("**/api/portfolio/pump-record?*", (route) => {
    userReads++;
    return route.abort();
  });
  await page.route("**/api/portfolio/incentive-record", async (route) => {
    requests.push({
      url: route.request().url(),
      cookie: route.request().headers().cookie,
    });
    const actual = await route.fetch({
      url: new URL("/global-record-test-fixture", route.request().url()).href,
    });
    expect(actual.status()).toBe(200);
    expect(actual.headers()["x-test-rpc-calls"]).toBe(
      "getGenesisHash,getAccountInfo",
    );
    await route.fulfill({ response: actual });
  });
  await load(page);
  expect(requests).toEqual([]);
  expect(userReads).toBe(0);
  await read(page).click();
  await expect(result(page)).toContainText("compiled-fixture.example");
  await expect(result(page)).toContainText("-9223372036854775808");
  await expect(result(page)).toContainText("9223372036854775807");
  await expect(result(page)).toContainText("18446744073709551615");
  await expect(result(page)).toContainText("18446744073709551556");
  await expect(result(page).locator("tbody tr")).toHaveCount(30);
  expect(requests).toEqual([
    {
      url: "http://127.0.0.1:3010/api/portfolio/incentive-record",
      cookie: undefined,
    },
  ]);
  expect(userReads).toBe(0);
  await expect(page.locator("html")).toHaveAttribute("data-pf-auth", "out");
  await expect(result(page)).toContainText(
    "Neither SDK incentive calculation is run",
  );
});
test("missing stays missing; a failed refresh clears old data and does not expose provider details", async ({
  page,
}) => {
  let count = 0;
  await page.route("**/api/portfolio/incentive-record", (route) => {
    count++;
    return route.fulfill(
      count === 2
        ? { status: 502, json: { secret: "private-provider-value" } }
        : {
            json:
              count === 1
                ? payload()
                : { ...payload(), record: null, dataBytes: null },
          },
    );
  });
  await load(page);
  await read(page).click();
  await expect(result(page)).toBeVisible();
  await page
    .getByRole("button", {
      name: "Refresh public incentive schedule",
      exact: true,
    })
    .click();
  await expect(panel(page).getByRole("alert")).toBeVisible();
  await expect(result(page)).toHaveCount(0);
  await expect(panel(page)).not.toContainText("private-provider-value");
  await read(page).click();
  await expect(result(page)).toContainText(
    "No Global incentive record was returned",
  );
  await expect(result(page).locator("table")).toHaveCount(0);
});
test("wrong fixed account or unsupported integer layout is unavailable instead of substituted", async ({
  page,
}) => {
  let count = 0;
  await page.route("**/api/portfolio/incentive-record", (route) => {
    count++;
    return route.fulfill({
      json:
        count === 1
          ? { ...payload(), recordPda: ADDRESS }
          : {
              ...payload(),
              record: {
                ...payload().record,
                solVolumes: Array(30).fill("18446744073709551616"),
              },
            },
    });
  });
  await load(page);
  for (let i = 0; i < 2; i++) {
    await read(page).click();
    await expect(panel(page).getByRole("alert")).toBeVisible();
    await expect(result(page)).toHaveCount(0);
  }
});
test("wallet navigation invalidates the pending separate Global snapshot", async ({
  page,
}) => {
  let release!: () => void, started!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  const pending = new Promise<void>((resolve) => {
    started = resolve;
  });
  await page.route("**/api/portfolio/incentive-record", async (route) => {
    started();
    await gate;
    await route.fulfill({ json: payload() }).catch(() => {});
  });
  await load(page);
  await read(page).click();
  await pending;
  await page
    .getByLabel("Solana public-key address", { exact: true })
    .fill(OTHER);
  await page.getByRole("button", { name: "Load wallet", exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`address=${OTHER}$`));
  await expect(read(page)).toBeVisible();
  release();
  await expect(result(page)).toHaveCount(0);
});
test("finite deadline clears loading and suppresses a late Global response", async ({
  page,
}) => {
  await page.clock.install();
  let release!: () => void, started!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  const pending = new Promise<void>((resolve) => {
    started = resolve;
  });
  await page.route("**/api/portfolio/incentive-record", async (route) => {
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
  test(`stored schedule and exact counters remain contained at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.route("**/api/portfolio/incentive-record", (route) =>
      route.fulfill({ json: payload() }),
    );
    await load(page);
    await read(page).click();
    await expect(result(page)).toBeVisible();
    await panel(page).scrollIntoViewIfNeeded();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await expect(result(page).locator("tbody tr")).toHaveCount(30);
    await page.screenshot({
      path: `../../artifacts/global-incentive-record-${width}.png`,
    });
  });
test("actual production route fails closed without RPC configuration and returns a finite no-store JSON body", async ({
  page,
  request,
}) => {
  await load(page);
  const pending = page.waitForResponse(
    (response) =>
      new URL(response.url()).pathname === "/api/portfolio/incentive-record",
  );
  await read(page).click();
  const response = await pending;
  expect(response.status()).toBe(503);
  expect(response.headers()["cache-control"]).toBe("no-store");
  await expect(panel(page).getByRole("alert")).toBeVisible();
  const body = await request.get("/api/portfolio/incentive-record", {
    timeout: 5000,
  });
  expect(body.status()).toBe(503);
  expect((await body.json()).error.code).toBe("RPC_CONFIGURATION_INVALID");
});
