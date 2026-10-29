import { expect, test, type Page } from "@playwright/test";

const BACKEND = "http://127.0.0.1:3001";

async function setMode(mode: string) {
  const response = await fetch(`${BACKEND}/__control`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ mode }),
  });
  expect(response.ok).toBe(true);
}

async function backendRequests(): Promise<string[]> {
  const response = await fetch(`${BACKEND}/__requests`);
  return ((await response.json()) as { requests: string[] }).requests;
}

function collectBrowserSafety(page: Page) {
  const violations: string[] = [];
  const consoleErrors: string[] = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (
      url.origin !== "http://127.0.0.1:3011" ||
      !["GET", "HEAD"].includes(request.method())
    ) {
      violations.push(`${request.method()} ${request.url()}`);
    }
  });
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  return { violations, consoleErrors };
}

test.beforeEach(async () => {
  await setMode("normal");
});

test("keeps the offline post feed as the default opt-in landing state", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByTestId("local-feed-item")).toHaveCount(3);
  await expect(page.getByTestId("native-callout-card")).toHaveCount(0);
  await expect(page.getByRole("tab", { name: "Local callouts" })).toBeVisible();
  expect(await backendRequests()).toEqual([]);
});

test("renders validated local callouts without browser-side backend traffic", async ({
  page,
}) => {
  const safety = collectBrowserSafety(page);
  await page.goto("/?tab=local-callouts&nativeView=ranked");
  await expect(
    page.getByText("Synthetic local callout data", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Not live Pump.fun activity.", { exact: false }),
  ).toBeVisible();
  await expect(page.getByTestId("native-callout-card")).toHaveCount(3);
  await expect(
    page.getByText("Local Example Alpha", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("No local image supplied", { exact: true }),
  ).toHaveCount(3);
  await expect(page.locator("main img")).toHaveCount(0);
  await expect(
    page
      .getByRole("tabpanel", { name: "Local callouts" })
      .getByRole("button", { name: /wallet|sign|trade|claim/iu }),
  ).toHaveCount(0);
  expect(safety.violations).toEqual([]);
  expect(safety.consoleErrors).toEqual([]);
  expect(await backendRequests()).toEqual([
    "GET /services/frontend/home-feed?pageSize=3",
  ]);
});

test("supports ranked pagination and browser history with opaque cursors", async ({
  page,
}) => {
  await page.goto("/?tab=local-callouts&nativeView=ranked");
  await page.getByRole("link", { name: "Next" }).click();
  await expect(page.getByText("Local page 2", { exact: true })).toBeVisible();
  await expect(page.getByTestId("native-callout-card")).toHaveCount(1);
  await expect(
    page.getByText("End of local list", { exact: true }),
  ).toBeVisible();

  await page.goBack();
  await expect(page.getByText("Local page 1", { exact: true })).toBeVisible();
  await expect(page.getByTestId("native-callout-card")).toHaveCount(3);
  await page.goForward();
  await expect(page.getByText("Local page 2", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Previous" }).click();
  await expect(page.getByText("Local page 1", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Local newest" }).click();
  await expect(page).toHaveURL(/nativeView=newest/u);
  expect(page.url()).not.toContain("nativeCursor");
  await expect(page.getByTestId("native-callout-card")).toHaveCount(3);
  await page.getByRole("link", { name: "Local ranked" }).click();
  await expect(page.getByText("Local page 1", { exact: true })).toBeVisible();
});

test("keeps newest pagination separate and binds count to the exact head token", async ({
  page,
}) => {
  await page.goto("/?tab=local-callouts&nativeView=newest");
  await expect(page.getByTestId("native-feed-count")).toHaveText(
    "0 newer local callouts relative to this local snapshot.",
  );
  expect(await backendRequests()).toEqual([
    "GET /services/frontend/home-feed/new?pageSize=3",
    expect.stringMatching(
      /^GET \/services\/frontend\/home-feed\/new\/count\?since=/u,
    ),
  ]);
  await page.getByRole("link", { name: "Next" }).click();
  await expect(page.getByText("Local page 2", { exact: true })).toBeVisible();
  await expect(page.getByTestId("native-feed-count")).toHaveCount(0);
  expect((await backendRequests()).at(-1)).toMatch(
    /^GET \/services\/frontend\/home-feed\/new\?pageSize=3&pageToken=/u,
  );
});

test("fails closed for unavailable, unproven and malformed local responses", async ({
  page,
}) => {
  for (const mode of [
    "unavailable",
    "wrong-source",
    "wrong-compatibility",
    "wrong-cache",
    "wrong-content-type",
    "malformed",
    "duplicate",
  ]) {
    await setMode(mode);
    await page.goto(`/?tab=local-callouts&nativeView=ranked&case=${mode}`);
    await expect(page.getByTestId("native-feed-error"), mode).toBeVisible();
    await expect(page.getByTestId("native-callout-card"), mode).toHaveCount(0);
  }
});

test("renders an explicit empty local result without inventing records", async ({
  page,
}) => {
  await setMode("empty");
  await page.goto("/?tab=local-callouts&nativeView=ranked");
  await expect(page.getByTestId("native-feed-empty")).toContainText(
    "This says nothing about current Pump.fun activity.",
  );
  await expect(page.getByTestId("native-callout-card")).toHaveCount(0);
});

test("rejects malformed and backend-invalid cursors without request loops", async ({
  page,
}) => {
  await page.goto(
    "/?tab=local-callouts&nativeView=ranked&nativeCursor=not-a-cursor",
  );
  await expect(page.getByTestId("native-feed-error")).toContainText(
    "Local page cursor rejected",
  );
  expect(await backendRequests()).toEqual([]);

  await page.goto("/?tab=local-callouts&nativeView=ranked&nativeView=newest");
  await expect(page.getByTestId("native-feed-error")).toBeVisible();
  expect(await backendRequests()).toEqual([]);

  await page.goto(
    "/?tab=local-callouts&nativeView=ranked&nativeCursor=YWJj.ZGVm",
  );
  await expect(page.getByTestId("native-feed-error")).toContainText(
    "Local page cursor rejected",
  );
  expect((await backendRequests()).length).toBe(1);
});

test("retains Following and keyboard-accessible local navigation", async ({
  page,
}) => {
  await page.goto("/");
  const forYou = page.getByRole("tab", { name: "For you" });
  await forYou.focus();
  await page.keyboard.press("End");
  const local = page.getByRole("tab", { name: "Local callouts" });
  await expect(local).toBeFocused();
  await expect(local).toHaveAttribute("aria-selected", "true");

  await page.getByRole("tab", { name: "Following" }).click();
  await expect(page.getByTestId("following-unavailable")).toBeVisible();
  await expect(page.getByTestId("native-callout-card")).toHaveCount(0);
});

test("keeps local callout cards responsive across required viewports", async ({
  page,
}) => {
  for (const [width, height] of [
    [320, 640],
    [375, 812],
    [390, 844],
    [768, 1024],
    [1280, 800],
    [1440, 900],
  ] as const) {
    await page.setViewportSize({ width, height });
    await page.goto("/?tab=local-callouts&nativeView=ranked");
    await expect(page.getByTestId("native-callout-card").first()).toBeVisible();
    const dimensions = await page.evaluate(() => ({
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
      clippedCards: Array.from(
        document.querySelectorAll("[data-testid=native-callout-card]"),
      ).filter((element) => element.scrollWidth > element.clientWidth).length,
    }));
    expect(dimensions.scrollWidth, `${width}px document`).toBeLessThanOrEqual(
      dimensions.clientWidth,
    );
    expect(dimensions.clippedCards, `${width}px cards`).toBe(0);
  }
});
