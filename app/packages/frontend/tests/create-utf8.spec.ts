import { test, expect } from "@playwright/test";
const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
  "base64",
);
const fields = (page: import("@playwright/test").Page) => ({
  name: page.getByRole("textbox", { name: /^Coin name/ }),
  ticker: page.getByRole("textbox", { name: /^Ticker/ }),
  description: page.getByRole("textbox", { name: /^Description/ }),
});
test.beforeEach(async ({ page, baseURL }) => {
  await page.route("**/*", async (route) => {
    const r = route.request(),
      url = new URL(r.url());
    if (!/^https?:$/.test(url.protocol)) return route.continue();
    if (
      url.origin !== new URL(baseURL!).origin ||
      !["GET", "HEAD"].includes(r.method())
    )
      throw Error(
        `Unexpected Create request ${r.method()} ${url.origin}${url.pathname}`,
      );
    return route.continue();
  });
  await page.goto("/create");
  await page
    .getByLabel(/^Coin image/)
    .setInputFiles({ name: "coin.png", mimeType: "image/png", buffer: PNG });
  await expect(page.getByTestId("selected-image")).toContainText("coin.png");
  await expect
    .poll(() =>
      page
        .locator(".preview-image")
        .evaluate((img) => (img as HTMLImageElement).naturalWidth),
    )
    .toBe(1);
});
test("UTF8-byte-invalid multibyte name and ticker reject before a ready draft", async ({
  page,
}, testInfo) => {
  const f = fields(page);
  await f.name.fill("漢".repeat(11));
  await f.name.blur();
  await expect(f.name).toHaveValue("漢".repeat(11));
  await expect(f.name).toHaveAttribute("aria-invalid", "true");
  await expect(page.locator("#name-error")).toContainText("32 UTF-8 bytes");
  await expect(page.locator("#name-hint")).toContainText("33/32");
  await expect(page.locator("#name-hint")).toContainText("UTF-8 bytes");
  await f.ticker.fill("💚💚💚");
  await f.ticker.blur();
  await expect(f.ticker).toHaveValue("💚💚💚");
  await expect(f.ticker).toHaveAttribute("aria-invalid", "true");
  await expect(page.locator("#ticker-error")).toContainText("10 UTF-8 bytes");
  await expect(page.locator("#ticker-hint")).toContainText("12/10");
  await page
    .getByRole("button", { name: "Preview draft", exact: true })
    .click();
  await expect(page.locator(".form-status")).toContainText(
    "Correct the highlighted fields",
  );
  await expect(f.name).toBeFocused();
  await expect(
    page.getByRole("button", {
      name: "Launch unavailable in local reconstruction",
    }),
  ).toBeDisabled();
  await page.screenshot({
    path: testInfo.outputPath("after-utf8-validation.png"),
    fullPage: true,
  });
});
test("exact byte boundaries preserve Unicode and description remains a codeunit count", async ({
  page,
}) => {
  const f = fields(page),
    name = "漢".repeat(10) + "ab",
    ticker = "💚💚ab",
    description = "💚".repeat(1000);
  await f.name.fill(name);
  await f.ticker.fill(ticker);
  await f.description.fill(description);
  await f.description.blur();
  await expect(page.locator("#name-hint")).toContainText("32/32");
  await expect(page.locator("#ticker-hint")).toContainText("10/10");
  await expect(page.locator("#description-hint")).toContainText("2000/");
  await page
    .getByRole("button", { name: "Preview draft", exact: true })
    .click();
  await expect(page.locator(".form-status")).toContainText(
    "Local draft is ready",
  );
  await page.getByText("Inspect draft JSON", { exact: true }).click();
  const json = JSON.parse(await page.locator(".metadata-json pre").innerText());
  expect(json.name).toBe(name);
  expect(json.symbol).toBe(ticker);
  expect(json.description).toBe(description);
  expect(json.image.localFileName).toBe("coin.png");
  expect(json).not.toHaveProperty("metadataUri");
});
test("native maxlengths, mixed alphabets and editing/recovery keep their existing behavior", async ({
  page,
}) => {
  const f = fields(page);
  await f.name.fill("n".repeat(40));
  await expect(f.name).toHaveValue("n".repeat(32));
  await f.ticker.fill("💚".repeat(6));
  expect((await f.ticker.inputValue()).length).toBe(10);
  await f.ticker.blur();
  await expect(page.locator("#ticker-hint")).toContainText("20/10");
  await expect(f.ticker).toHaveAttribute("aria-invalid", "true");
  await f.ticker.fill("$? 混合");
  await f.ticker.blur();
  await expect(f.ticker).toHaveAttribute("aria-invalid", "false");
  await expect(page.locator("#ticker-hint")).toContainText("9/10");
  await page
    .getByRole("button", { name: "Preview draft", exact: true })
    .click();
  await expect(page.locator(".form-status")).toContainText(
    "Local draft is ready",
  );
  await page.getByRole("button", { name: "Reset draft", exact: true }).click();
  await expect(page.locator("#name-hint")).toContainText("0/32");
  await expect(page.locator("#ticker-hint")).toContainText("0/10");
});
