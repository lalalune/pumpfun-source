import { expect, test, type Page, type Route } from "@playwright/test";

async function beginRealRetry(page: Page) {
  const reads: string[] = [],
    forbidden: string[] = [];
  await page.route("**/*", (route) => {
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
  await page.goto("/mayhem");
  await expect(page.getByTestId("mayhem-unavailable")).toBeVisible();
  const initial = reads.length,
    held: Route[] = [];
  let hold = true;
  await page.route("**/api/mayhem-screener?*", (route) => {
    if (
      new URL(route.request().url()).origin !== "http://127.0.0.1:3010" ||
      route.request().method() !== "GET"
    )
      return route.abort();
    if (hold) {
      held.push(route);
      return;
    }
    return route.continue();
  });
  const retry = page.getByRole("button", {
    name: "Retry local adapter",
    exact: true,
  });
  const sort = page.getByLabel("Sort Mayhem coins");
  await sort.focus();
  await page.keyboard.press("Tab");
  await expect(retry).toBeFocused();
  await page.keyboard.press("Enter");
  await expect.poll(() => held.length).toBe(1);
  await expect(page.getByTestId("mayhem-loading")).toBeVisible();
  return {
    retry,
    sort,
    held,
    reads,
    initial,
    forbidden,
    release: async () => {
      const response = page.waitForResponse(
        (r) =>
          new URL(r.url()).pathname === "/api/mayhem-screener" &&
          r.request().method() === "GET",
      );
      hold = false;
      await Promise.all(held.map((route) => route.continue()));
      const actual = await response;
      expect(actual.status()).toBe(503);
      expect((await actual.json()).code).toBe("MAYHEM_DATA_UNAVAILABLE");
      await expect(page.getByTestId("mayhem-unavailable")).toBeVisible();
    },
  };
}

test("busy retry remains keyboard focused and ignores repeated activation", async ({
  page,
}) => {
  const state = await beginRealRetry(page);
  try {
    await expect(state.retry).toBeFocused();
    await expect(state.retry).toHaveAttribute("aria-disabled", "true");
    expect(
      await state.retry.evaluate(
        (button: HTMLButtonElement) => button.disabled,
      ),
    ).toBe(false);
    await page.keyboard.press("Enter");
    await page.keyboard.press("Enter");
    await state.release();
    await expect(state.retry).toBeFocused();
    await expect(state.retry).not.toHaveAttribute("aria-disabled", "true");
    expect(state.reads.length - state.initial).toBe(1);
    expect(state.held.length).toBe(1);
    expect(state.forbidden).toEqual([]);
  } finally {
    await page.unrouteAll({ behavior: "ignoreErrors" });
  }
});

test("retry completion respects native focus moved to Sort while pending", async ({
  page,
}) => {
  const state = await beginRealRetry(page);
  try {
    await expect(state.retry).toBeFocused();
    await page.keyboard.press("Shift+Tab");
    await expect(state.sort).toBeFocused();
    await state.release();
    await expect(state.sort).toBeFocused();
    expect(state.reads.length - state.initial).toBe(1);
    expect(state.forbidden).toEqual([]);
  } finally {
    await page.unrouteAll({ behavior: "ignoreErrors" });
  }
});
