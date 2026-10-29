import { expect, test, type Route } from "@playwright/test";

test("real unavailable Mayhem retry preserves keyboard focus through its local GET", async ({
  page,
  context,
}, testInfo) => {
  const forbidden: string[] = [];
  const reads: string[] = [];
  const focus = () =>
    page.evaluate(() => ({
      tag: document.activeElement?.tagName,
      id: document.activeElement?.id,
      label: document.activeElement?.getAttribute("aria-label"),
      text: document.activeElement?.textContent?.slice(0, 80),
    }));
  await context.route("**/*", (route) => {
    const r = route.request();
    if (
      new URL(r.url()).origin !== "http://127.0.0.1:3010" ||
      !["GET", "HEAD"].includes(r.method())
    ) {
      forbidden.push(`${r.method()} ${r.url()}`);
      return route.abort();
    }
    return route.continue();
  });
  page.on("request", (r) => {
    if (new URL(r.url()).pathname === "/api/mayhem-screener")
      reads.push(r.url());
  });
  await page.setViewportSize({ width: 1280, height: 800 });
  expect((await page.goto("/mayhem"))?.status()).toBe(200);
  const retry = page.getByRole("button", {
    name: "Retry local adapter",
    exact: true,
  });
  await expect(page.getByTestId("mayhem-unavailable")).toBeVisible();
  await expect(
    page.getByText("No qualified live dataset", { exact: true }),
  ).toBeVisible();
  const initialReadCount = reads.length;
  const held: Route[] = [];
  let hold = true;
  await page.route("**/api/mayhem-screener?*", async (route) => {
    if (
      new URL(route.request().url()).origin !== "http://127.0.0.1:3010" ||
      route.request().method() !== "GET"
    ) {
      forbidden.push(`${route.request().method()} ${route.request().url()}`);
      return route.abort();
    }
    if (hold) held.push(route);
    else await route.continue();
  });
  try {
    await page.getByLabel("Sort Mayhem coins").focus();
    await page.keyboard.press("Tab");
    await expect(retry).toBeFocused();
    const before = await focus();
    await page.keyboard.press("Enter");
    await expect.poll(() => held.length).toBe(1);
    await expect(page.getByTestId("mayhem-loading")).toBeVisible();
    const loading = await focus();
    // Continue the real local request; no synthetic response body/status is
    // substituted. The existing Next route still fails closed with503.
    const response = page.waitForResponse(
      (r) =>
        new URL(r.url()).pathname === "/api/mayhem-screener" &&
        r.request().method() === "GET",
    );
    hold = false;
    await Promise.all(held.map((route) => route.continue()));
    const actual = await response;
    expect(actual.status()).toBe(503);
    const body = await actual.json();
    expect(body.code).toBe("MAYHEM_DATA_UNAVAILABLE");
    await expect(page.getByTestId("mayhem-unavailable")).toBeVisible();
    await page.screenshot({
      path: testInfo.outputPath("after-retry.png"),
      fullPage: true,
    });
    await testInfo.attach("actual-retry-focus", {
      body: JSON.stringify(
        {
          initialReadCount,
          before,
          loading,
          after: await focus(),
          status: actual.status(),
          code: body.code,
          reads,
        },
        null,
        2,
      ),
      contentType: "application/json",
    });
    expect(reads.length - initialReadCount).toBe(1);
    await expect(retry).toBeFocused();
    expect(forbidden).toEqual([]);
    await expect(page.getByTestId("mayhem-coin-row")).toHaveCount(0);
  } finally {
    await page.unrouteAll({ behavior: "ignoreErrors" });
  }
});
