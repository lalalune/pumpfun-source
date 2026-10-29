import { expect, test, type Page, type Route } from "@playwright/test";

const fixture = {
  source: "synthetic-test",
  coins: [
    {
      mint: "MayhemMintAlpha111111111111111111111111111",
      name: "Alpha agent",
      symbol: "ALPHA",
      state: "active",
      mode: "auto",
      createdTimestamp: 100,
      marketCapUsd: 10,
      volumeUsd24h: 90,
    },
    {
      mint: "MayhemMintBeta2222222222222222222222222222",
      name: "Beta mode",
      symbol: "BETA",
      state: "paused",
      mode: "manual",
      createdTimestamp: 300,
      marketCapUsd: 80,
      volumeUsd24h: 20,
    },
    {
      mint: "MayhemMintGamma333333333333333333333333333",
      name: "Gamma",
      symbol: "GAMMA",
      state: "completed",
      mode: "auto",
      createdTimestamp: 200,
    },
  ],
};

async function fulfill(route: Route, data: unknown = fixture) {
  await route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify(data),
  });
}

async function useFixture(page: Page) {
  await page.route("**/api/mayhem-screener?*", (route) => fulfill(route));
}

test("renders four accessible filters and remains unavailable without qualified data", async ({
  page,
}) => {
  const response = await page.goto("/mayhem");
  expect(response?.status()).toBe(200);
  await expect(
    page.getByRole("heading", { level: 1, name: "Mayhem screener" }),
  ).toBeVisible();
  for (const label of ["All", "Active", "Paused", "Ended"]) {
    await expect(
      page.getByRole("link", { name: label, exact: true }),
    ).toBeVisible();
  }
  const active = page.getByRole("link", { name: "Active", exact: true });
  await active.focus();
  await expect(active).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/state=active/);
  await expect(page.getByTestId("mayhem-unavailable")).toBeVisible();
  await expect(page.getByText(/No qualified live dataset/)).toBeVisible();
});

test("maps state filters to the captured query contract and preserves history", async ({
  page,
}) => {
  const seen: string[] = [];
  await page.route("**/api/mayhem-screener?*", async (route) => {
    seen.push(route.request().url());
    await fulfill(route);
  });
  await page.goto("/mayhem");
  await expect(page.getByTestId("mayhem-coin-row")).toHaveCount(3);
  expect(new URL(seen.at(-1)!).searchParams.has("mayhemState")).toBe(false);

  for (const [label, state, api] of [
    ["Active", "active", "active"],
    ["Paused", "paused", "paused"],
    ["Ended", "ended", "completed"],
  ] as const) {
    await page.getByRole("link", { name: label, exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`state=${state}`));
    await expect(page.getByTestId("mayhem-coin-row")).toHaveCount(3);
    expect(new URL(seen.at(-1)!).searchParams.get("mayhemState")).toBe(api);
  }
  await page.goBack();
  await expect(
    page.getByRole("link", { name: "Paused", exact: true }),
  ).toHaveAttribute("aria-current", "page");
  await page.reload();
  await expect(page).toHaveURL(/state=paused/);
});

test("sort controls implement volume, market cap, newest and server-order modes", async ({
  page,
}) => {
  await useFixture(page);
  await page.goto("/mayhem");
  const names = () =>
    page.getByTestId("mayhem-coin-row").locator("h2").allTextContents();
  await expect.poll(names).toEqual(["Alpha agent", "Beta mode", "Gamma"]);
  for (const [sort, expected] of [
    ["24h volume", ["Alpha agent", "Beta mode", "Gamma"]],
    ["Market cap", ["Beta mode", "Alpha agent", "Gamma"]],
    ["Newest", ["Beta mode", "Gamma", "Alpha agent"]],
    ["Last traded", ["Alpha agent", "Beta mode", "Gamma"]],
  ] as const) {
    await page.getByLabel("Sort Mayhem coins").selectOption({ label: sort });
    await expect.poll(names).toEqual(expected);
  }
  await expect(page.getByText("—", { exact: true }).first()).toBeVisible();
});

test("distinguishes loading, empty and invalid responses", async ({ page }) => {
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/mayhem-screener?*", async (route) => {
    await gate;
    await fulfill(route);
  });
  await page.goto("/mayhem");
  await expect(page.getByTestId("mayhem-loading")).toBeVisible();
  release();
  await expect(page.getByTestId("mayhem-coin-row")).toHaveCount(3);

  await page.unroute("**/api/mayhem-screener?*");
  await page.route("**/api/mayhem-screener?*", (route) =>
    fulfill(route, { source: "synthetic-test", coins: [] }),
  );
  await page.getByRole("link", { name: "Active", exact: true }).click();
  await expect(page.getByTestId("mayhem-empty")).toBeVisible();

  await page.unroute("**/api/mayhem-screener?*");
  await page.route("**/api/mayhem-screener?*", (route) =>
    fulfill(route, { source: "synthetic-test", coins: [{ mint: "x" }] }),
  );
  await page.getByRole("link", { name: "Paused", exact: true }).click();
  await expect(page.getByTestId("mayhem-validation-error")).toBeVisible();
});

test("an older failed request cannot overwrite the latest successful filter", async ({
  page,
}) => {
  await page.route("**/api/mayhem-screener?*", async (route) => {
    const filter = new URL(route.request().url()).searchParams.get("filter");
    if (filter === "active")
      await new Promise((resolve) => setTimeout(resolve, 250));
    await fulfill(
      route,
      filter === "paused"
        ? { source: "synthetic-test", coins: [fixture.coins[1]] }
        : { source: "synthetic-test", coins: [fixture.coins[0]] },
    );
  });
  await page.goto("/mayhem");
  await expect(page.getByTestId("mayhem-coin-row")).toHaveCount(1);
  await page.getByRole("link", { name: "Active", exact: true }).click();
  await page.getByRole("link", { name: "Paused", exact: true }).click();
  await expect(page.getByText("Beta mode", { exact: true })).toBeVisible();
  await page.waitForTimeout(350);
  await expect(page.getByText("Beta mode", { exact: true })).toBeVisible();
  await expect(page.getByText("Alpha agent", { exact: true })).toHaveCount(0);
});

test("target viewports have no overflow and excluded coin routes remain unavailable", async ({
  page,
}) => {
  await useFixture(page);
  for (const [width, height] of [
    [320, 640],
    [375, 812],
    [768, 1024],
    [1440, 900],
  ] as const) {
    await page.setViewportSize({ width, height });
    await page.goto("/mayhem?state=active&sort=mcap");
    await expect(page.getByTestId("mayhem-coin-row").first()).toBeVisible();
    const size = await page.evaluate(() => ({
      client: document.documentElement.clientWidth,
      scroll: document.documentElement.scrollWidth,
    }));
    expect(size.scroll, `${width}px`).toBeLessThanOrEqual(size.client);
  }
  await expect(page.locator('a[href^="/coin/"]')).toHaveCount(0);
  expect((await page.goto("/coin/not-a-real-mint"))?.status()).toBe(404);
});

test("interaction issues no external, mutating, wallet or signing requests", async ({
  page,
}) => {
  await useFixture(page);
  const violations: string[] = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (
      url.origin !== "http://127.0.0.1:3010" ||
      !["GET", "HEAD"].includes(request.method()) ||
      /wallet|sign|transaction/i.test(url.pathname)
    ) {
      violations.push(`${request.method()} ${request.url()}`);
    }
  });
  await page.goto("/mayhem");
  await page.getByRole("link", { name: "Ended", exact: true }).click();
  await page.getByLabel("Sort Mayhem coins").selectOption("newest");
  expect(violations).toEqual([]);
  await expect(page.getByTestId("mayhem-test-disclosure")).toBeVisible();
});

for (const first of ["filter", "sort"] as const) {
  test(`pending ${first} navigation keeps the next Mayhem selection`, async ({
    page,
  }) => {
    await page.goto("/mayhem", { waitUntil: "networkidle" });
    const held: Route[] = [];
    let hold = true;
    await page.route("**/mayhem?**", async (route) => {
      if (hold && new URL(route.request().url()).searchParams.has("_rsc"))
        held.push(route);
      else await route.continue();
    });
    const filter = () =>
      page
        .getByRole("navigation", { name: "Mayhem state filter" })
        .getByRole("link", { name: "Active", exact: true })
        .click();
    const sort = () =>
      page.getByLabel("Sort Mayhem coins").selectOption("volume");
    try {
      await (first === "filter" ? filter() : sort());
      await expect.poll(() => held.length).toBeGreaterThan(0);
      await (first === "filter" ? sort() : filter());
      await expect.poll(() => held.length).toBeGreaterThan(1);
      hold = false;
      await Promise.all(held.map((route) => route.continue()));
      await expect(page).toHaveURL(/\/mayhem\?state=active&sort=volume$/);
      await expect(
        page.getByRole("link", { name: "Active", exact: true }),
      ).toHaveAttribute("aria-current", "page");
      await expect(page.getByLabel("Sort Mayhem coins")).toHaveValue("volume");
      await expect(page.getByTestId("mayhem-unavailable")).toBeVisible();
      await page.goBack();
      await expect(page).toHaveURL(/\/mayhem$/);
      await expect(page.getByLabel("Sort Mayhem coins")).toHaveValue(
        "lastTraded",
      );
      await page.goForward();
      await expect(page).toHaveURL(/state=active&sort=volume$/);
      await expect(
        page.getByRole("link", { name: "Active", exact: true }),
      ).toHaveAttribute("aria-current", "page");
    } finally {
      await page.unrouteAll({ behavior: "ignoreErrors" });
    }
  });
}
