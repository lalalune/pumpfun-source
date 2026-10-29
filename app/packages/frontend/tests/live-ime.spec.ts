import { expect, test, type Page } from "@playwright/test";
const MINT = "7bS1mH6MXbw1GnEkKTU6w5YLTywPkQ1w3YVZXWFupump";
type ImeKey = {
  type: string;
  key: string;
  composing: boolean;
  trusted: boolean;
  prevented: boolean;
};
declare global {
  interface Window {
    liveImeKeys?: ImeKey[];
  }
}
async function recordKeys(page: Page) {
  // Installed after readiness, so the window observer follows the Live listener.
  await page.evaluate(() => {
    window.liveImeKeys = [];
    for (const type of ["keydown", "keyup"])
      window.addEventListener(type, (event) => {
        if (!(event instanceof KeyboardEvent) || event.key !== "Escape") return;
        window.liveImeKeys?.push({
          type,
          key: event.key,
          composing: event.isComposing,
          trusted: event.isTrusted,
          prevented: event.defaultPrevented,
        });
      });
  });
}
async function composingEscape(page: Page) {
  const cdp = await page.context().newCDPSession(page);
  try {
    await cdp.send("Input.imeSetComposition", {
      text: "にほん",
      selectionStart: 3,
      selectionEnd: 3,
    });
    await page.keyboard.press("Escape");
    await page.waitForLoadState("networkidle");
  } finally {
    await cdp.detach();
  }
  return page.evaluate(() => window.liveImeKeys ?? []);
}
for (const width of [390, 1280]) {
  test(`composing Escape preserves archived Live details at ${width}px, then ordinary Escape closes them`, async ({
    page,
    baseURL,
  }, testInfo) => {
    await page.setViewportSize({ width, height: 844 });
    await page.route("**/*", async (route) => {
      const r = route.request(),
        u = new URL(r.url());
      if (!/^https?:$/.test(u.protocol)) return route.continue();
      if (
        u.origin !== new URL(baseURL!).origin ||
        !["GET", "HEAD"].includes(r.method())
      )
        throw Error(
          `Unexpected Live request ${r.method()} ${u.origin}${u.pathname}`,
        );
      return route.continue();
    });
    // Native platform control, not an original Pump playback or UI reference.
    await page.setContent(
      '<label>Native control</label><dialog aria-label="Native composition control"><input type="search" aria-label="Native archive search"></dialog>',
    );
    await page.evaluate(() => document.querySelector("dialog")!.showModal());
    const nativeDialog = page.getByRole("dialog", {
      name: "Native composition control",
    });
    const nativeInput = page.getByRole("searchbox", {
      name: "Native archive search",
    });
    await nativeInput.fill("draft");
    await recordKeys(page);
    const nativeEvents = await composingEscape(page);
    const nativeResult = {
      events: nativeEvents,
      open: await nativeDialog.isVisible(),
      focused: await nativeInput.evaluate(
        (el) => el === document.activeElement,
      ),
    };
    await testInfo.attach("native-control", {
      body: JSON.stringify(nativeResult, null, 2),
      contentType: "application/json",
    });
    expect(nativeEvents.find((e) => e.type === "keydown")).toMatchObject({
      composing: true,
      trusted: true,
      prevented: false,
    });
    await expect(nativeDialog).toBeVisible();
    await expect(nativeInput).toBeFocused();

    await page.goto(`/live?page=4&stream=${MINT}&playback=paused&keep=1#keep`);
    const detail = page
      .locator("#main-content")
      .getByTestId("playback-unavailable");
    const search = page.getByRole("searchbox", {
      name: "Search captured streams",
    });
    await expect(detail).toBeVisible();
    await search.fill("draft");
    // A controlled field render establishes hydration before the trusted key.
    await expect(
      page.getByRole("button", { name: "Clear", exact: true }),
    ).toBeVisible();
    await recordKeys(page);
    const originalUrl = page.url();
    const events = await composingEscape(page);
    const result = {
      events,
      url: page.url(),
      detailCount: await detail.count(),
      focused: await search.evaluate((el) => el === document.activeElement),
    };
    await testInfo.attach("archived-live", {
      body: JSON.stringify(result, null, 2),
      contentType: "application/json",
    });
    await page.screenshot({
      path: testInfo.outputPath(`live-ime-${width}.png`),
    });
    expect(events.find((e) => e.type === "keydown")).toMatchObject({
      composing: true,
      trusted: true,
      prevented: false,
    });
    await expect(detail).toBeVisible();
    await expect(search).toBeFocused();
    expect(page.url()).toBe(originalUrl);
    await expect(
      page.locator("#main-content").locator("video,audio,iframe"),
    ).toHaveCount(0);

    // End composition explicitly through ordinary input before testing dismissal.
    await search.fill("draft");
    await page.keyboard.press("Escape");
    await expect(detail).toHaveCount(0);
    const url = new URL(page.url());
    expect(url.searchParams.has("stream")).toBe(false);
    expect(url.searchParams.get("page")).toBe("4");
    expect(url.searchParams.get("playback")).toBe("paused");
    expect(url.searchParams.get("keep")).toBe("1");
    // Ordinary navigation keeps its existing fragment-clearing behavior.
    expect(url.hash).toBe("");
    await expect(search).toBeFocused();
    expect(
      (await page.evaluate(() => window.liveImeKeys ?? []))
        .filter((e) => e.type === "keydown")
        .at(-1),
    ).toMatchObject({ composing: false, trusted: true, prevented: true });
  });
}
