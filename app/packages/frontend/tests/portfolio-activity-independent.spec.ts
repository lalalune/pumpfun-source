import { expect, test, type Page } from "@playwright/test";
import { PublicKey } from "@solana/web3.js";
import { PUMP_PROGRAM_ID, userVolumeAccumulatorPda } from "@pump-fun/pump-sdk";
const ADDRESS = "So11111111111111111111111111111111111111112";
const OTHER = "11111111111111111111111111111111";
const failure = {
  ok: false,
  error: {
    code: "RPC_RESPONSE_INVALID",
    message: "Token account response is unsupported.",
    retryable: true,
  },
};
// Existing public-record DTO. No new service/API/SDK behavior is introduced.
function record(address = ADDRESS) {
  return {
    ok: true,
    address,
    programId: PUMP_PROGRAM_ID.toBase58(),
    recordPda: userVolumeAccumulatorPda(new PublicKey(address)).toBase58(),
    cluster: "mainnet-beta",
    commitment: "confirmed",
    contextSlot: 321,
    endpointHost: "controlled-public.example",
    observedAt: "2026-10-29T05:00:00.000Z",
    dataBytes: 106,
    record: {
      user: address,
      needsClaim: false,
      hasTotalClaimedTokens: false,
      totalUnclaimedTokens: "7",
      totalClaimedTokens: "0",
      currentSolVolume: "2",
      lastUpdateTimestamp: "0",
      cashbackEarned: "0",
      totalCashbackClaimed: "0",
      stableCashbackEarned: "0",
      totalStableCashbackClaimed: "0",
    },
  };
}
const inspect = (page: Page) =>
  page.getByRole("button", {
    name: "Read public Pump record",
    exact: true,
  });
async function failedHoldings(page: Page) {
  await page.route("**/api/portfolio?*", (route) =>
    route.fulfill({ status: 502, json: failure }),
  );
}
test("valid wallet activity remains explicitly inspectable when the holdings read fails", async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 640 });
  let recordRequests = 0;
  await page.route("**/api/portfolio?*", (route) =>
    route.fulfill({
      status: 502,
      json: {
        ok: false,
        error: {
          code: "RPC_RESPONSE_INVALID",
          message: "Token account response is unsupported.",
          retryable: false,
        },
      },
    }),
  );
  await page.route("**/api/portfolio/pump-record?*", (route) => {
    recordRequests++;
    return route.fulfill({ json: record() });
  });
  await page.goto(`/portfolio?address=${ADDRESS}`);
  await expect(page.locator(".portfolio-error")).toContainText(
    "Token account response is unsupported.",
  );
  expect(recordRequests).toBe(0);
  await expect(inspect(page)).toBeVisible();
  await inspect(page).click();
  await expect(page.getByTestId("public-pump-record-result")).toContainText(
    "controlled-public.example",
  );
  expect(recordRequests).toBe(1);
  await expect(page.locator("html")).toHaveAttribute("data-pf-auth", "out");
  await expect(page.getByTestId("portfolio-activity")).toContainText(ADDRESS);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.getByTestId("portfolio-activity").scrollIntoViewIfNeeded();
  await page.screenshot({ path: "../../artifacts/portfolio-activity-320.png" });
});

test("a pending holdings read neither blocks nor later clears an explicitly read activity record", async ({
  page,
}) => {
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/portfolio?*", async (route) => {
    await gate;
    await route.fulfill({ status: 502, json: failure });
  });
  let requests = 0;
  await page.route("**/api/portfolio/pump-record?*", (route) => {
    requests++;
    return route.fulfill({ json: record() });
  });
  await page.goto(`/portfolio?address=${ADDRESS}`);
  await expect(page.locator(".portfolio-loading")).toBeVisible();
  expect(requests).toBe(0);
  await inspect(page).click();
  await expect(page.getByTestId("public-pump-record-result")).toBeVisible();
  release();
  await expect(page.locator(".portfolio-error")).toBeVisible();
  await expect(page.getByTestId("public-pump-record-result")).toContainText(
    "controlled-public.example",
  );
  expect(requests).toBe(1);
  await page.screenshot({
    path: "../../artifacts/portfolio-activity-1440.png",
  });
});

for (const address of ["", "not-a-public-key"]) {
  test(`an ${address ? "invalid" : "empty"} committed address offers no activity read`, async ({
    page,
  }) => {
    let requests = 0;
    await failedHoldings(page);
    await page.route("**/api/portfolio/pump-record?*", (route) => {
      requests++;
      return route.abort();
    });
    await page.goto(`/portfolio?${new URLSearchParams({ address })}`);
    await expect(
      page.getByLabel("Solana public-key address", { exact: true }),
    ).toHaveValue(address);
    await expect(page.getByTestId("portfolio-activity")).toHaveCount(0);
    expect(requests).toBe(0);
  });
}

test("editing a draft preserves the committed target; navigation clears the previous result", async ({
  page,
}) => {
  await failedHoldings(page);
  const requests: string[] = [];
  await page.route("**/api/portfolio/pump-record?*", (route) => {
    const address = new URL(route.request().url()).searchParams.get("address")!;
    requests.push(address);
    return route.fulfill({ json: record(address) });
  });
  await page.goto(`/portfolio?address=${ADDRESS}`);
  const input = page.getByLabel("Solana public-key address", { exact: true });
  await input.fill(OTHER);
  await expect(page.getByTestId("portfolio-activity")).toContainText(ADDRESS);
  await inspect(page).click();
  await expect(page.getByTestId("public-pump-record-result")).toBeVisible();
  expect(requests).toEqual([ADDRESS]);
  await page.getByRole("button", { name: "Load wallet", exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`address=${OTHER}$`));
  await expect(page.getByTestId("portfolio-activity")).toContainText(OTHER);
  await expect(page.getByTestId("public-pump-record-result")).toHaveCount(0);
  expect(requests).toEqual([ADDRESS]);
  await inspect(page).click();
  await expect(page.getByTestId("public-pump-record-result")).toBeVisible();
  expect(requests).toEqual([ADDRESS, OTHER]);
});

test("navigation invalidates a pending activity result while both wallets have holdings errors", async ({
  page,
}) => {
  await failedHoldings(page);
  let release!: () => void, started!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  const pending = new Promise<void>((resolve) => {
    started = resolve;
  });
  await page.route("**/api/portfolio/pump-record?*", async (route) => {
    const address = new URL(route.request().url()).searchParams.get("address")!;
    if (address === ADDRESS) {
      started();
      await gate;
    }
    await route.fulfill({ json: record(address) }).catch(() => {});
  });
  await page.goto(`/portfolio?address=${ADDRESS}`);
  await inspect(page).click();
  await pending;
  await page
    .getByLabel("Solana public-key address", { exact: true })
    .fill(OTHER);
  await page.getByRole("button", { name: "Load wallet", exact: true }).click();
  await expect(page.getByTestId("portfolio-activity")).toContainText(OTHER);
  release();
  await expect(inspect(page)).toBeVisible();
  await expect(page.getByTestId("public-pump-record-result")).toHaveCount(0);
  await inspect(page).click();
  await expect(page.getByTestId("public-pump-record-result")).toContainText(
    record(OTHER).recordPda,
  );
});

test("retrying holdings invalidates an activity snapshot without automatically reading it again", async ({
  page,
}) => {
  let balanceRequests = 0,
    recordRequests = 0;
  await page.route("**/api/portfolio?*", (route) => {
    balanceRequests++;
    return route.fulfill({ status: 502, json: failure });
  });
  await page.route("**/api/portfolio/pump-record?*", (route) => {
    recordRequests++;
    return route.fulfill({ json: record() });
  });
  await page.goto(`/portfolio?address=${ADDRESS}`);
  await inspect(page).click();
  await expect(page.getByTestId("public-pump-record-result")).toBeVisible();
  await page
    .locator(".portfolio-error")
    .getByRole("button", { name: "Try again", exact: true })
    .click();
  await expect(inspect(page)).toBeVisible();
  await expect(page.getByTestId("public-pump-record-result")).toHaveCount(0);
  expect(recordRequests).toBe(1);
  expect(balanceRequests).toBe(2);
  await inspect(page).click();
  await expect(page.getByTestId("public-pump-record-result")).toBeVisible();
  expect(recordRequests).toBe(2);
});
