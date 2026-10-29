import { expect, test, type Page } from "@playwright/test";

test.use({ viewport: { width: 1280, height: 900 } });

type Evidence = {
  pageErrors: string[];
  consoleErrors: string[];
  routedExternal: { url: string; method: string; action: "fulfilled" }[];
  nativeFallbacks: { kind: string; url: string }[];
  storageRefusals: number;
};
const evidence = new WeakMap<Page, Evidence>();
const key = "privacy.confirm-external-links";
const blog = "https://medium.com/@pumpdotfun_";
const prompt = (page: Page) => page.getByTestId("footer-link-confirmation");
const footer = (page: Page) => page.getByRole("contentinfo");
const blogLink = (page: Page) =>
  footer(page).getByRole("link", { name: "Blog", exact: true });

declare global {
  interface Window {
    footerOpenCalls?: string[][];
    footerOpenThrows?: boolean;
    footerOpenRefusals?: number;
    footerStorageRefusals?: number;
  }
}

test.beforeEach(async ({ page, context, baseURL }) => {
  const origin = new URL(baseURL!).origin;
  const data: Evidence = {
    pageErrors: [],
    consoleErrors: [],
    routedExternal: [],
    nativeFallbacks: [],
    storageRefusals: 0,
  };
  evidence.set(page, data);
  page.on("pageerror", (error) => data.pageErrors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") data.consoleErrors.push(message.text());
  });
  context.on("page", (popup) =>
    popup.on("pageerror", (error) => data.pageErrors.push(error.message)),
  );
  await context.route("**/*", (route) => {
    if (new URL(route.request().url()).origin === origin)
      return route.continue();
    data.routedExternal.push({
      url: route.request().url(),
      method: route.request().method(),
      action: "fulfilled",
    });
    // The native fallback is exercised against a controlled browser response,
    // never the original destination or an upstream compatibility oracle.
    return route.fulfill({
      contentType: "text/html",
      body: "<!doctype html><title>Controlled external destination</title>",
    });
  });
  await page.addInitScript(() => {
    window.footerOpenCalls = [];
    window.footerOpenThrows = false;
    window.footerOpenRefusals = 0;
    window.open = (url, target, features) => {
      window.footerOpenCalls?.push([String(url), target ?? "", features ?? ""]);
      if (window.footerOpenThrows) {
        window.footerOpenRefusals = (window.footerOpenRefusals ?? 0) + 1;
        throw new DOMException("Controlled refusal", "SecurityError");
      }
      // noopener can return null normally. It is not a delivery/failure oracle.
      return null;
    };
  });
});

test.afterEach(async ({ page, browser }, info) => {
  const data = evidence.get(page)!;
  const ports = await page.evaluate(() => ({
    calls: window.footerOpenCalls ?? [],
    openRefusals: window.footerOpenRefusals ?? 0,
  }));
  await info.attach("footer-workflow-evidence", {
    body: JSON.stringify({
      ...data,
      ...ports,
      browserVersion: browser.version(),
    }),
    contentType: "application/json",
  });
  if (info.status === "passed") {
    expect(data.pageErrors).toEqual([]);
    expect(data.consoleErrors).toEqual([]);
  }
});

async function privacy(page: Page, enabled?: boolean) {
  await page.goto(
    "/?entry=footer&settings=privacy&setting=privacy.confirmExternalLinks#keep",
  );
  const settings = page.getByRole("dialog", { name: "Settings", exact: true });
  const control = settings.getByRole("switch", {
    name: "Confirm before opening external links",
  });
  await expect(control).toBeEnabled();
  if (
    enabled !== undefined &&
    (await control.getAttribute("aria-checked")) !== String(enabled)
  )
    await control.click();
  return { settings, control };
}
async function closeSettings(page: Page, settings: ReturnType<Page["getByRole"]>) {
  await settings.getByRole("button", { name: "Done", exact: true }).click();
  await expect(settings).not.toBeVisible();
  await expect(page).toHaveURL((url) => !url.searchParams.has("settings"));
}
async function prepare(page: Page, enabled = true) {
  const { settings } = await privacy(page, enabled);
  await closeSettings(page, settings);
  await footerReady(page);
}
async function footerReady(page: Page) {
  // An actual controlled footer interaction establishes hydration; SSR anchor
  // visibility alone does not prove that client enhancement is ready.
  const viewport = page.viewportSize();
  if (viewport && viewport.width < 768)
    await page.setViewportSize({ width: 1280, height: viewport.height });
  const resources = footer(page).getByRole("button", {
    name: "Resources",
    exact: true,
  });
  // The existing menu dismisses on scroll. Finish Playwright's intentional
  // viewport movement before opening it, rather than racing that dismissal.
  await resources.scrollIntoViewIfNeeded();
  await page.evaluate(
    () => new Promise<void>((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))),
  );
  await resources.click();
  const menu = page.getByRole("menu", { name: "Resources", exact: true });
  await expect(menu).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(menu).not.toBeVisible();
  if (viewport && viewport.width < 768) await page.setViewportSize(viewport);
}
async function calls(page: Page) {
  return page.evaluate(() => window.footerOpenCalls);
}

test("footer Blog confirms and cancellation preserves its native anchor and page", async ({
  page,
}, info) => {
  await prepare(page);
  await expect(blogLink(page)).toHaveAttribute("href", blog);
  await expect(blogLink(page)).toHaveAttribute("target", "_blank");
  await blogLink(page).click();
  await expect(prompt(page)).toBeVisible();
  await expect(prompt(page)).toContainText(blog);
  expect(await calls(page)).toEqual([]);
  await page.screenshot({ path: info.outputPath("footer-desktop.png") });
  await prompt(page).getByRole("checkbox").check();
  await prompt(page)
    .getByRole("button", { name: "Cancel", exact: true })
    .click();
  await expect(prompt(page)).not.toBeVisible();
  await expect(blogLink(page)).toBeFocused();
  expect(
    await page.evaluate((key) => localStorage.getItem(key), key),
  ).toBeNull();
  await blogLink(page).click();
  await expect(prompt(page).getByRole("checkbox")).not.toBeChecked();
  await page.keyboard.press("Escape");
  await expect(prompt(page)).not.toBeVisible();
  expect(await calls(page)).toEqual([]);
  expect(new URL(page.url()).search).toBe("?entry=footer");
  expect(new URL(page.url()).hash).toBe("#keep");
});

test("remembered footer choice updates Settings and survives reload", async ({
  page,
}) => {
  await prepare(page);
  await blogLink(page).click();
  await prompt(page).getByRole("checkbox").check();
  await prompt(page)
    .getByRole("button", { name: "Open link", exact: true })
    .click();
  await expect(prompt(page)).not.toBeVisible();
  expect(await calls(page)).toEqual([[blog, "_blank", "noopener,noreferrer"]]);
  expect(await page.evaluate((key) => localStorage.getItem(key), key)).toBe(
    "false",
  );
  const off = await privacy(page);
  await expect(off.control).toHaveAttribute("aria-checked", "false");
  await closeSettings(page, off.settings);
  await page.reload();
  await blogLink(page).click();
  expect(await calls(page)).toEqual([[blog, "_blank", "noopener,noreferrer"]]);
  await expect(prompt(page)).not.toBeVisible();
  const on = await privacy(page, true);
  await expect(on.control).toHaveAttribute("aria-checked", "true");
  await closeSettings(page, on.settings);
  await blogLink(page).click();
  await expect(prompt(page)).toBeVisible();
});

test("footer portal menu can unmount while confirmation survives and returns focus", async ({
  page,
}) => {
  await prepare(page);
  const resources = footer(page).getByRole("button", {
    name: "Resources",
    exact: true,
  });
  await resources.click();
  const menu = page.getByRole("menu", { name: "Resources", exact: true });
  await menu.getByRole("menuitem", { name: "PumpSwap", exact: true }).click();
  await expect(menu).not.toBeVisible();
  await expect(prompt(page)).toBeVisible();
  await expect(prompt(page)).toContainText("https://swap.pump.fun/");
  await prompt(page)
    .getByRole("button", { name: "Cancel", exact: true })
    .click();
  await expect(resources).toBeFocused();
  await resources.click();
  await menu.getByRole("menuitem", { name: "Fees", exact: true }).click();
  await expect(page).toHaveURL(/\/docs\/fees$/);
  await expect(prompt(page)).not.toBeVisible();
  expect(await calls(page)).toEqual([]);
});

test("mobile footer Resources and SVG social links use the same preference", async ({
  page,
}, info) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await prepare(page);
  await footer(page)
    .getByRole("link", { name: "Tech updates", exact: true })
    .click();
  await expect(prompt(page)).toBeVisible();
  await expect(prompt(page)).toContainText("https://t.me/pump_tech_updates");
  const box = await prompt(page).boundingBox();
  expect(box!.width).toBeLessThanOrEqual(390);
  await page.screenshot({ path: info.outputPath("footer-mobile.png") });
  await prompt(page)
    .getByRole("button", { name: "Cancel", exact: true })
    .click();
  await footer(page)
    .getByRole("link", { name: "X", exact: true })
    .locator("svg")
    .click();
  await expect(prompt(page)).toContainText("https://twitter.com/pumpfun");
  expect(await calls(page)).toEqual([]);
});

test("opening exceptions retain recovery, retry and a native browser fallback", async ({
  page,
  context,
}) => {
  await prepare(page);
  await blogLink(page).click();
  await page.evaluate(() => {
    window.footerOpenThrows = true;
  });
  await prompt(page)
    .getByRole("button", { name: "Open link", exact: true })
    .click();
  await expect(prompt(page).getByRole("alert")).toContainText("could not open");
  await page.evaluate(() => {
    window.footerOpenThrows = false;
  });
  await prompt(page)
    .getByRole("button", { name: "Retry new tab", exact: true })
    .click();
  await expect(prompt(page)).not.toBeVisible();
  expect(await calls(page)).toHaveLength(2);
  await blogLink(page).click();
  await page.evaluate(() => {
    window.footerOpenThrows = true;
  });
  await prompt(page)
    .getByRole("button", { name: "Open link", exact: true })
    .click();
  const popupPromise = context.waitForEvent("page");
  await prompt(page)
    .getByRole("link", { name: "Use browser link", exact: true })
    .click();
  const popup = await popupPromise;
  await popup.waitForLoadState("domcontentloaded");
  expect(popup.url()).toBe(blog);
  await expect(popup).toHaveTitle("Controlled external destination");
  evidence
    .get(page)!
    .nativeFallbacks.push({ kind: "opening-exception", url: popup.url() });
  await expect(prompt(page)).not.toBeVisible();
  expect(await calls(page)).toHaveLength(3);
  await popup.close();
});

test("failed remembered-choice storage warns and its page fallback resets on reload", async ({
  page,
}, info) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript((key) => {
    const original = Storage.prototype.setItem;
    Storage.prototype.setItem = function (name, value) {
      if (name === key) {
        window.footerStorageRefusals = (window.footerStorageRefusals ?? 0) + 1;
        throw new DOMException(
          "Controlled storage refusal",
          "QuotaExceededError",
        );
      }
      return original.call(this, name, value);
    };
  }, key);
  await prepare(page);
  await blogLink(page).click();
  await prompt(page).getByRole("checkbox").check();
  await prompt(page)
    .getByRole("button", { name: "Open link", exact: true })
    .click();
  await expect(prompt(page)).not.toBeVisible();
  await expect(
    page
      .getByRole("status")
      .filter({ hasText: "storage could not be confirmed" }),
  ).toBeVisible();
  expect(
    await page.evaluate((key) => localStorage.getItem(key), key),
  ).toBeNull();
  evidence.get(page)!.storageRefusals = await page.evaluate(
    () => window.footerStorageRefusals ?? 0,
  );
  expect(evidence.get(page)!.storageRefusals).toBeGreaterThan(0);
  await page.screenshot({
    path: info.outputPath("footer-storage-failure.png"),
  });
  await blogLink(page).click();
  expect(await calls(page)).toHaveLength(2);
  await expect(prompt(page)).not.toBeVisible();
  await page.reload();
  await blogLink(page).click();
  await expect(prompt(page)).toBeVisible();
});

test("footer choice is immediately shared with unchanged Create preview links", async ({
  page,
}) => {
  const website = "https://example.com/local-draft";
  await page.goto("/create");
  await page.getByLabel("Website", { exact: true }).fill(website);
  const preview = page
    .getByRole("list", { name: "Draft social links" })
    .getByRole("link", { name: "Website", exact: true });
  await expect(preview).toHaveAttribute("href", website);
  await footerReady(page);
  await blogLink(page).click();
  await prompt(page).getByRole("checkbox").check();
  await prompt(page)
    .getByRole("button", { name: "Open link", exact: true })
    .click();
  await preview.click();
  expect(await calls(page)).toEqual([
    [blog, "_blank", "noopener,noreferrer"],
    [website, "_blank", "noopener,noreferrer"],
  ]);
  await expect(
    page.getByRole("dialog", { name: "Open external link?", exact: true }),
  ).not.toBeVisible();
  await page
    .getByRole("button", { name: "Open settings", exact: true })
    .click();
  const settings = page.getByRole("dialog", { name: "Settings", exact: true });
  await settings.getByRole("tab", { name: "Privacy", exact: true }).click();
  const control = settings.getByRole("switch", {
    name: "Confirm before opening external links",
  });
  await expect(control).toHaveAttribute("aria-checked", "false");
  await control.click();
  await closeSettings(page, settings);
  await preview.click();
  const confirmation = page.getByRole("dialog", {
    name: "Open external link?",
    exact: true,
  });
  await expect(confirmation).toBeVisible();
  await expect(confirmation).toContainText(website);
  await expect(prompt(page)).not.toBeVisible();
  expect(await calls(page)).toHaveLength(2);
});

test("server-rendered footer preserves native anchors before enhancement", async ({
  browser,
  baseURL,
}) => {
  const origin = new URL(baseURL!).origin;
  const context = await browser.newContext({ javaScriptEnabled: false });
  try {
    await context.route("**/*", (route) =>
      new URL(route.request().url()).origin === origin
        ? route.continue()
        : route.abort(),
    );
    const page = await context.newPage();
    await page.goto("/");
    await expect(blogLink(page)).toHaveAttribute("href", blog);
    await expect(blogLink(page)).toHaveAttribute("target", "_blank");
    await expect(blogLink(page)).toHaveAttribute("rel", "noopener noreferrer");
    await expect(prompt(page)).toHaveCount(0);
    // The existing clickwrap requires JS to hide its SSR overlay. This checks
    // anchor preservation only; it does not claim a usable no-JS app workflow.
    await expect(page.locator("[data-clickwrap-overlay]")).toBeVisible();
  } finally {
    await context.close();
  }
});
