import { expect, test, type Page, type Route } from "@playwright/test";

function monitorSafety(page: Page) {
  const unexpected: string[] = [];
  const consoleErrors: string[] = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (
      url.origin !== "http://127.0.0.1:3010" ||
      !["GET", "HEAD"].includes(request.method())
    )
      unexpected.push(`${request.method()} ${request.url()}`);
  });
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  return { unexpected, consoleErrors };
}

test("renders a dedicated authenticated archive instead of the generic scaffold", async ({
  page,
}) => {
  const safety = monitorSafety(page);
  const response = await page.goto("/go");
  expect(response?.status()).toBe(200);
  await expect(
    page.getByRole("heading", { level: 1, name: "GO bounties" }),
  ).toBeVisible();
  await expect(
    page.getByText("25 exact archived bounties", { exact: true }),
  ).toBeVisible();
  await expect(page.getByTestId("go-bounty-card")).toHaveCount(24);
  await expect(page.locator('[data-product-state="unavailable"]')).toHaveCount(
    0,
  );
  await expect(
    page.getByText("No wallet or payouts", { exact: true }),
  ).toBeVisible();
  await expect(
    page.locator("main img, main iframe, main video, main audio"),
  ).toHaveCount(0);
  expect(safety.unexpected).toEqual([]);
  expect(safety.consoleErrors).toEqual([]);
});

test("search is encoded, URL-backed, refresh-safe and history-aware", async ({
  page,
}) => {
  await page.goto("/go");
  const search = page.getByRole("searchbox", {
    name: "Search archived bounties",
  });
  await search.fill("alpha & beta=one");
  await search.press("Enter");
  await expect(page).toHaveURL(/\/go\?q=alpha\+%26\+beta%3Done$/);
  await expect(page.getByTestId("go-empty-results")).toBeVisible();
  await page.reload();
  await expect(search).toHaveValue("alpha & beta=one");
  await page.goBack();
  await expect(page).toHaveURL(/\/go$/);
  await expect(page.getByTestId("go-bounty-card")).toHaveCount(24);
  await page.goForward();
  await expect(search).toHaveValue("alpha & beta=one");
  await page.getByRole("button", { name: "Reset" }).click();
  await expect(page).toHaveURL(/\/go$/);
  await expect(search).toHaveValue("");
});

test("validated filters, sorting and cursor pagination remain deterministic", async ({
  page,
}) => {
  await page.goto("/go");
  const firstTitle = await page
    .getByTestId("go-bounty-card")
    .first()
    .getByRole("heading", { level: 3 })
    .textContent();
  await page.getByLabel("Direction").selectOption("asc");
  await expect(page).toHaveURL(/order=asc/);
  await expect(
    page
      .getByTestId("go-bounty-card")
      .first()
      .getByRole("heading", { level: 3 }),
  ).not.toHaveText(firstTitle ?? "");

  await page.getByLabel("Status at capture").selectOption("CLOSED");
  await expect(page).toHaveURL(/status=CLOSED/);
  await expect(
    page
      .getByTestId("go-bounty-card")
      .first()
      .getByText("Closed", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Reset" }).click();

  await page.getByRole("button", { name: "Next page" }).click();
  await expect(page).toHaveURL(/cursor=c24/);
  await expect(page.getByTestId("go-bounty-card")).toHaveCount(1);
  await expect(page.getByText("Page 2", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Previous page" }).click();
  await expect(page).toHaveURL(/\/go$/);
  await expect(page.getByTestId("go-bounty-card")).toHaveCount(24);
});

test("invalid URL and API parameters fail safely", async ({
  page,
  request,
}) => {
  await page.goto(
    "/go?status=LIVE&sort=unknown&remote=https%3A%2F%2Fevil.example",
  );
  await expect(
    page.getByText("Unsupported URL filters were ignored safely."),
  ).toBeVisible();
  await expect(page.getByLabel("Status at capture")).toHaveValue("ALL");
  await expect(page.getByTestId("go-bounty-card")).toHaveCount(24);
  const response = await request.get("/api/go-bounties?cursor=c1");
  expect(response.status()).toBe(400);
  expect(await response.json()).toMatchObject({ code: "INVALID_GO_QUERY" });
});

test("network and malformed archive responses expose retryable fail-closed states", async ({
  page,
}) => {
  let mode: "network" | "malformed" | "pass" = "network";
  await page.route("**/api/go-bounties?**", async (route) => {
    if (mode === "network") return route.abort("failed");
    if (mode === "malformed")
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [{ title: "bad" }] }),
      });
    return route.fallback();
  });
  await page.goto("/go");
  await page.getByLabel("Direction").selectOption("asc");
  await expect(page.getByTestId("go-request-error")).toContainText(
    "did not fall back",
  );
  mode = "malformed";
  await page.getByRole("button", { name: "Retry" }).click();
  await expect(page.getByTestId("go-request-error")).toContainText(
    "failed validation",
  );
  mode = "pass";
  await page.getByRole("button", { name: "Retry" }).click();
  await expect(page.getByTestId("go-bounty-card")).toHaveCount(24);
});

test("a stale response cannot overwrite a newer search", async ({
  page,
  request,
}) => {
  const slow = await request.get("/api/go-bounties?q=Follow");
  const fast = await request.get("/api/go-bounties?q=Buy");
  const slowBody = await slow.text();
  const fastBody = await fast.text();
  await page.route("**/api/go-bounties?**", async (route) => {
    const query = new URL(route.request().url()).searchParams.get("q");
    if (query === "Follow") {
      await new Promise((resolve) => setTimeout(resolve, 350));
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: slowBody,
      });
    }
    if (query === "Buy")
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: fastBody,
      });
    return route.fallback();
  });
  await page.goto("/go");
  const search = page.getByRole("searchbox", {
    name: "Search archived bounties",
  });
  await search.fill("Follow");
  await search.press("Enter");
  await expect(page).toHaveURL(/q=Follow/);
  await expect(page.getByText("Updating archived results…")).toBeVisible();
  await search.fill("Buy");
  await search.press("Enter");
  await expect(page).toHaveURL(/q=Buy/);
  await expect(page.getByTestId("go-bounty-card").first()).toContainText("Buy");
  await page.waitForTimeout(450);
  await expect(page.getByTestId("go-bounty-card").first()).toContainText("Buy");
  await expect(
    page.getByTestId("go-bounty-card").filter({ hasText: "Follow me" }),
  ).toHaveCount(0);
});

test("detail is keyboard dismissible, restores focus and exposes no authenticated action", async ({
  page,
}) => {
  await page.goto("/go");
  const inspect = page
    .getByRole("button", { name: /^Inspect archived bounty / })
    .first();
  await inspect.focus();
  await inspect.click();
  await expect(page).toHaveURL(/task=/);
  await expect(page.getByTestId("go-bounty-detail")).toContainText(
    "Account actions unavailable",
  );
  await expect(
    page.getByText(/Funding, submissions, moderation and payouts/),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page).not.toHaveURL(/task=/);
  await expect(inspect).toBeFocused();
});

test("all required viewports avoid document overflow and preserve shell navigation", async ({
  page,
}) => {
  for (const [width, height] of [
    [320, 640],
    [375, 812],
    [768, 1024],
    [1440, 900],
  ] as const) {
    await page.setViewportSize({ width, height });
    await page.goto("/go");
    await expect(
      page.getByRole("searchbox", { name: "Search archived bounties" }),
    ).toBeVisible();
    await expect(page.getByTestId("go-bounty-card").first()).toBeVisible();
    const dimensions = await page.evaluate(() => ({
      client: document.documentElement.clientWidth,
      scroll: document.documentElement.scrollWidth,
    }));
    expect(dimensions.scroll, `${width}px document`).toBeLessThanOrEqual(
      dimensions.client,
    );
    if (width < 760) {
      await page.getByRole("button", { name: "Open navigation" }).click();
      await expect(
        page
          .getByRole("navigation", { name: "Primary", exact: true })
          .getByRole("link", { name: "GO", exact: true }),
      ).toHaveAttribute("aria-current", "page");
      await page.keyboard.press("Escape");
    }
  }
});

test("interaction performs no external, wallet or mutation requests and excluded routes stay excluded", async ({
  page,
}) => {
  const safety = monitorSafety(page);
  await page.goto("/go");
  await page.getByLabel("Sort by").selectOption("submissionCount");
  await page
    .getByRole("button", { name: /^Inspect archived bounty / })
    .first()
    .click();
  await page.keyboard.press("Escape");
  expect(safety.unexpected).toEqual([]);
  expect(safety.consoleErrors).toEqual([]);
  for (const route of [
    "/go/open",
    "/go/bounties",
    "/go/mine",
    "/go/submissions",
    "/pump-token",
    "/coin/example",
  ]) {
    const response = await page.goto(route);
    expect(response?.status(), route).toBe(404);
  }
});

test("filter changes compose while the previous navigation is pending", async ({
  page,
}) => {
  await page.goto("/go", { waitUntil: "networkidle" });
  const held: Route[] = [];
  let holdNavigation = true;
  await page.route("**/go?**", async (route) => {
    if (
      holdNavigation &&
      new URL(route.request().url()).searchParams.has("_rsc")
    ) {
      held.push(route);
    } else {
      await route.continue();
    }
  });
  try {
    await page.getByLabel("Status at capture").selectOption("CLOSED");
    await expect.poll(() => held.length).toBe(1);
    await page.getByLabel("Direction").selectOption("asc");
    await expect.poll(() => held.length).toBe(2);
    // Release the earlier response while the newer navigation is still held.
    await held[0].continue();
    await page.getByLabel("Sort by").selectOption("submissionCount");
    await expect.poll(() => held.length).toBe(3);
    holdNavigation = false;
    await Promise.all(held.slice(1).map((route) => route.continue()));
    await expect(page).toHaveURL(
      /\/go\?status=CLOSED&order=asc&sort=submissionCount$/,
    );
    await expect(page.getByLabel("Status at capture")).toHaveValue("CLOSED");
    await expect(page.getByLabel("Direction")).toHaveValue("asc");
    await expect(page.getByTestId("go-bounty-card").first()).toBeVisible();
    await expect(
      page.locator(".go-phase").filter({ hasNotText: "Closed" }),
    ).toHaveCount(0);
    await page.goBack();
    await expect(page).toHaveURL(/\/go$/);
    await page.goForward();
    await expect(page.getByLabel("Status at capture")).toHaveValue("CLOSED");
    await page.goBack();
    await expect(page).toHaveURL(/\/go$/);
    await page.getByLabel("Sort by").selectOption("submissionCount");
    await expect(page).toHaveURL(/\/go\?sort=submissionCount$/);
    await expect(page.getByLabel("Status at capture")).toHaveValue("ALL");
    await page.getByRole("button", { name: "Reset", exact: true }).click();
    await expect(page).toHaveURL(/\/go$/);
    await page.getByLabel("Direction").selectOption("asc");
    await expect(page).toHaveURL(/\/go\?order=asc$/);
  } finally {
    await page.unrouteAll({ behavior: "ignoreErrors" });
  }
});

test("delayed reset preserves the next archive search draft and URL history", async ({
  page,
}) => {
  await page.goto("/go?q=previous", { waitUntil: "networkidle" });
  const input = page.locator("#go-search");
  await expect(input).toHaveValue("previous");
  const held: Route[] = [];
  let hold = true;
  await page.route("**/go?**", async (route) => {
    if (hold && new URL(route.request().url()).searchParams.has("_rsc"))
      held.push(route);
    else await route.continue();
  });
  try {
    await page.getByRole("button", { name: "Reset", exact: true }).click();
    await expect.poll(() => held.length).toBeGreaterThan(0);
    await input.fill("new draft");
    hold = false;
    await Promise.all(held.map((route) => route.continue()));
    await expect(page).toHaveURL(/\/go$/);
    await expect(input).toHaveValue("new draft");
    await input.press("Enter");
    await expect(page).toHaveURL(/\/go\?q=new\+draft$/);
    await page.goBack();
    await expect(page).toHaveURL(/\/go$/);
    await expect(input).toHaveValue("");
    await page.goForward();
    await expect(input).toHaveValue("new draft");
  } finally {
    await page.unrouteAll({ behavior: "ignoreErrors" });
  }
});
