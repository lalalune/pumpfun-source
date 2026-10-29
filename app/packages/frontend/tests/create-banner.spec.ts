import { test, expect } from "@playwright/test";
const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
  "base64",
);
const image = (name = "banner.png", buffer = PNG, mimeType = "image/png") => ({
  name,
  buffer,
  mimeType,
});

test.beforeEach(async ({ page, baseURL }) => {
  await page.route("**/*", async (route) => {
    const request = route.request(),
      url = new URL(request.url());
    if (!/^https?:$/.test(url.protocol)) return route.continue();
    if (
      url.origin !== new URL(baseURL!).origin ||
      !["GET", "HEAD"].includes(request.method())
    ) {
      throw new Error(
        `Forbidden create request ${request.method()} ${url.origin}${url.pathname}`,
      );
    }
    return route.continue();
  });
  await page.addInitScript(() => {
    const live = new Map<string, string>(),
      revoked: string[] = [];
    const create = URL.createObjectURL.bind(URL),
      revoke = URL.revokeObjectURL.bind(URL);
    URL.createObjectURL = (value) => {
      const url = create(value);
      if (value instanceof File && value.name.startsWith("banner"))
        live.set(url, value.name);
      return url;
    };
    URL.revokeObjectURL = (url) => {
      if (live.delete(url)) revoked.push(url);
      revoke(url);
    };
    Object.assign(window, { bannerUrls: { live, revoked } });
  });
});
const bannerInput = (page: import("@playwright/test").Page) =>
  page.getByLabel("Local banner image", { exact: true });
async function open(page: import("@playwright/test").Page) {
  await page.goto("/create");
  await page.getByText("Add banner", { exact: false }).first().click();
}
async function liveCount(page: import("@playwright/test").Page) {
  return page.evaluate(
    () =>
      (window as unknown as { bannerUrls: { live: Map<string, string> } })
        .bannerUrls.live.size,
  );
}

test("keyboard picker accepts a real decoded banner separately from the coin image and metadata", async ({
  page,
}) => {
  await page.goto("/create");
  const summary = page.locator("summary").filter({ hasText: "Add banner" });
  await expect(summary).toBeVisible();
  await summary.focus();
  await page.keyboard.press("Enter");
  const input = bannerInput(page);
  await input.focus();
  const chooser = page.waitForEvent("filechooser");
  await page.keyboard.press("Space");
  await (await chooser).setFiles(image());
  await expect(page.getByTestId("selected-banner")).toContainText(
    "1 × 1 pixels",
  );
  await expect(
    page.getByRole("img", { name: "Local draft banner preview" }),
  ).toBeVisible();
  await expect(page.getByTestId("selected-image")).toHaveCount(0);
  // The draft JSON is deliberately unchanged: banner is a separate offline preview.
  await page.getByLabel(/^Coin image/).setInputFiles(image("coin.png"));
  await page.getByLabel("Coin name", { exact: false }).fill("Draft");
  await page.getByLabel("Ticker", { exact: false }).fill("LOCAL");
  await page.getByText("Inspect draft JSON", { exact: true }).click();
  const json = JSON.parse(await page.locator(".metadata-json pre").innerText());
  expect(json.image.localFileName).toBe("coin.png");
  expect(json).not.toHaveProperty("banner");
  await page
    .getByRole("button", { name: "Preview draft", exact: true })
    .click();
  await expect(page.locator(".form-status")).toContainText(
    "Local draft is ready",
  );
  await expect(
    page.getByRole("button", {
      name: "Launch unavailable in local reconstruction",
    }),
  ).toBeDisabled();
  expect(await liveCount(page)).toBe(1);
});

test("bad MIME, empty and oversized selections preserve the current banner and show actionable errors", async ({
  page,
}) => {
  await open(page);
  const input = bannerInput(page);
  await input.setInputFiles(image());
  await expect(page.getByTestId("selected-banner")).toContainText("banner.png");
  for (const [file, error] of [
    [image("bad.svg", Buffer.from("<svg/>"), "image/svg+xml"), "Choose a JPEG"],
    [image("empty.png", Buffer.alloc(0)), "non-empty banner"],
    [image("large.png", Buffer.alloc(4_500_001)), "non-empty banner"],
  ] as const) {
    await input.setInputFiles(file);
    await expect(page.locator("#banner-error")).toContainText(error);
    await expect(page.getByTestId("selected-banner")).toContainText(
      "banner.png",
    );
    expect(await liveCount(page)).toBe(1);
  }
  await page
    .getByRole("button", { name: "Preview draft", exact: true })
    .click();
  await expect(page.locator(".form-status")).toContainText("Replace or remove");
  await expect(input).toBeFocused();
  await page
    .getByRole("button", { name: "Remove banner / cancel preparation" })
    .click();
  await expect(page.locator("#banner-error")).toHaveCount(0);
  expect(await liveCount(page)).toBe(0);
});

test("real corrupt-image decode failure retains the accepted banner and releases the rejected URL", async ({
  page,
}) => {
  await open(page);
  const input = bannerInput(page);
  await input.setInputFiles(image());
  await expect(page.getByTestId("selected-banner")).toContainText("banner.png");
  await input.setInputFiles(
    image("banner-broken.png", Buffer.from("not a PNG")),
  );
  await expect(page.locator("#banner-error")).toContainText("could not decode");
  await expect(page.getByTestId("selected-banner")).toContainText("banner.png");
  expect(await liveCount(page)).toBe(1);
  await input.setInputFiles(image("banner-retry.png"));
  await expect(page.locator("#banner-error")).toHaveCount(0);
  await expect(page.getByTestId("selected-banner")).toContainText(
    "banner-retry.png",
  );
  expect(await liveCount(page)).toBe(1);
});

test("replacement, removal, reset and route unmount release their local banner URLs", async ({
  page,
}) => {
  await open(page);
  const input = bannerInput(page);
  await input.setInputFiles(image());
  await expect(page.getByTestId("selected-banner")).toBeVisible();
  await input.setInputFiles(image("banner-new.png"));
  await expect(page.getByTestId("selected-banner")).toContainText("banner-new");
  expect(await liveCount(page)).toBe(1);
  await page
    .getByRole("button", { name: "Remove banner / cancel preparation" })
    .click();
  expect(await liveCount(page)).toBe(0);
  await input.setInputFiles(image());
  await expect(page.getByTestId("selected-banner")).toBeVisible();
  await page.getByRole("button", { name: "Reset draft", exact: true }).click();
  await expect(page.getByTestId("selected-banner")).toHaveCount(0);
  await expect.poll(() => liveCount(page)).toBe(0);
  await page.locator("summary").filter({ hasText: "Add banner" }).click();
  await input.setInputFiles(image());
  await expect(page.getByTestId("selected-banner")).toBeVisible();
  // Next navigation keeps the same document so the URL ownership assertion remains meaningful.
  await page.getByRole("link", { name: "Home", exact: true }).first().click();
  await expect(page.getByTestId("selected-banner")).toHaveCount(0);
  await expect.poll(() => liveCount(page)).toBe(0);
});

test("pending decoder can be cancelled and cannot produce a ready draft", async ({
  page,
}) => {
  // Explicit synthetic stalled-image port for cancellation only; success cases use native decoding.
  await page.addInitScript(() => {
    const descriptor = Object.getOwnPropertyDescriptor(
      HTMLImageElement.prototype,
      "src",
    )!;
    Object.defineProperty(HTMLImageElement.prototype, "src", {
      ...descriptor,
      set(value: string) {
        if (value.startsWith("blob:")) return;
        descriptor.set!.call(this, value);
      },
    });
  });
  await open(page);
  await bannerInput(page).setInputFiles(image());
  await expect(
    page.getByText("Preparing local banner preview…", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Preview draft", exact: true })
    .click();
  await expect(page.locator(".form-status")).toContainText(
    "Wait for the local banner",
  );
  await page
    .getByRole("button", { name: "Remove banner / cancel preparation" })
    .click();
  await expect(
    page.getByText("Preparing local banner preview…", { exact: true }),
  ).toHaveCount(0);
  await expect.poll(() => liveCount(page)).toBe(0);
  await expect(page.getByTestId("selected-banner")).toHaveCount(0);
});

test("banner draft is ephemeral and is absent after reload", async ({
  page,
}) => {
  await open(page);
  await bannerInput(page).setInputFiles(image());
  await expect(page.getByTestId("selected-banner")).toBeVisible();
  await page.reload();
  await expect(page.getByTestId("selected-banner")).toHaveCount(0);
  await page.locator("summary").filter({ hasText: "Add banner" }).click();
  await expect(bannerInput(page)).toHaveValue("");
});

test("local banner preview fits desktop and mobile widths", async ({
  page,
}, testInfo) => {
  await open(page);
  await bannerInput(page).setInputFiles(image());
  await expect(page.getByTestId("selected-banner")).toBeVisible();
  for (const width of [1440, 375]) {
    await page.setViewportSize({ width, height: 950 });
    await page.getByTestId("selected-banner").scrollIntoViewIfNeeded();
    const box = await page
      .getByRole("img", { name: "Local draft banner preview" })
      .boundingBox();
    expect(box).not.toBeNull();
    expect(box!.x).toBeGreaterThanOrEqual(0);
    expect(box!.x + box!.width).toBeLessThanOrEqual(width);
    expect(Math.abs(box!.width / box!.height - 3)).toBeLessThan(0.05);
    await page.screenshot({
      path: testInfo.outputPath(`local-banner-${width}.png`),
      fullPage: true,
    });
  }
});
