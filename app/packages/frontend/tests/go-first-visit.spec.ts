import { expect, test } from "@playwright/test";

test.use({ storageState: { cookies: [], origins: [] } });

for (const width of [390, 1280]) {
  test(`first-visit Escape preserves the selected GO task at ${width}px`, async ({
    page,
    baseURL,
  }) => {
    await page.setViewportSize({ width, height: 844 });
    const unexpected: string[] = [];
    page.on("request", (request) => {
      if (
        new URL(request.url()).origin !== new URL(baseURL!).origin ||
        !["GET", "HEAD"].includes(request.method())
      )
        unexpected.push(`${request.method()} ${request.url()}`);
    });
    const task = "34d83521-afbd-4642-a77c-2a47f2fd9ce6";
    const detailURL = new URL(`/go?task=${task}`, baseURL!).href;
    await page.goto(detailURL);
    const welcome = page.getByRole("dialog", { name: "Welcome to Pump.fun!" });
    const detail = page.getByTestId("go-bounty-detail");
    await expect(welcome).toBeVisible();
    await expect(welcome.locator("[tabindex='-1']").last()).toBeFocused();
    await expect(detail).toBeAttached();

    await page.keyboard.press("Escape");
    await expect(welcome).toHaveCount(0);
    await expect(page).toHaveURL(detailURL);
    await expect(detail).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(page).toHaveURL(new URL("/go", baseURL!).href);
    await expect(detail).toHaveCount(0);
    await expect(
      page.locator('button[aria-label^="Inspect archived bounty "]:focus'),
    ).toHaveCount(1);
    expect(unexpected).toEqual([]);
  });
}
