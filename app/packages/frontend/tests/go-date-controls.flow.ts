import { expect, test, type Page, type BrowserContext } from "@playwright/test";

async function observe(page: Page, context: BrowserContext) {
  const errors: string[] = [], forbidden: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("pageerror", (error) => errors.push(error.message));
  await context.route("**/*", (route) => {
    const request = route.request();
    if (new URL(request.url()).origin !== "http://127.0.0.1:3010" || !["GET", "HEAD"].includes(request.method())) {
      forbidden.push(`${request.method()} ${request.url()}`);
      return route.abort();
    }
    return route.continue();
  });
  return { errors, forbidden };
}

test("GO expiry retains local formatting on direct detail, soft navigation and reload", async ({ page, context }) => {
  const state = await observe(page, context);
  const id = "34d83521-afbd-4642-a77c-2a47f2fd9ce6";
  await page.goto(`/go?task=${id}`, { waitUntil: "networkidle" });
  const expiry = page.getByTestId("go-bounty-detail").locator('time[datetime="2026-11-11T06:57:47.120Z"]');
  const label = await page.evaluate(() => new Date("2026-11-11T06:57:47.120Z").toLocaleDateString("en-US"));
  await expect(expiry).toHaveText(label);
  await page.getByRole("button", { name: "Close bounty detail" }).click();
  await expect(page).toHaveURL(/\/go$/);
  await page.getByTestId("go-bounty-card").first().getByRole("button").click();
  await expect(page).toHaveURL(new RegExp(`/go\\?task=${id}$`));
  await expect(expiry).toHaveText(label);
  await page.reload({ waitUntil: "networkidle" });
  await expect(expiry).toHaveText(label);
  expect(state.errors.filter((message) => /hydration failed/i.test(message))).toEqual([]);
  expect(state.forbidden).toEqual([]);
});

test.describe("matching server/browser timezone", () => {
  test.use({ timezoneId: "UTC" });
  test("GO dates keep their existing UTC label without hydration errors", async ({ page, context }) => {
    const state = await observe(page, context);
    await page.goto("/go", { waitUntil: "networkidle" });
    const first = page.getByTestId("go-bounty-card").first().locator("time");
    await expect(first).toHaveAttribute("datetime", "2026-10-28T06:53:34.915Z");
    await expect(first).toHaveText("10/28/2026");
    expect(state.errors.filter((message) => /hydration failed/i.test(message))).toEqual([]);
    expect(state.forbidden).toEqual([]);
  });
});
