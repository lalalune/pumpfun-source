import { expect, test, type Locator, type Page } from "@playwright/test";

type PointerRecord = {
  type: string;
  trusted: boolean;
  target: string;
  x: number;
  y: number;
  pointerType: string | null;
  pointerId: number | null;
  open: boolean;
  url: string;
};
declare global {
  interface Window {
    settingsBackdropTrace?: Record<string, PointerRecord[]>;
  }
}
const runtime = new WeakMap<Page, { pageErrors: string[]; consoleErrors: string[]; blockedExternal: string[] }>();

test.beforeEach(async ({ context, baseURL, page }) => {
  const origin = new URL(baseURL!).origin;
  const errors = { pageErrors: [] as string[], consoleErrors: [] as string[], blockedExternal: [] as string[] };
  runtime.set(page, errors);
  page.on("pageerror", (error) => errors.pageErrors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.consoleErrors.push(message.text());
  });
  await context.route("**/*", (route) => {
    if (new URL(route.request().url()).origin === origin) return route.continue();
    errors.blockedExternal.push(route.request().url());
    return route.abort();
  });
});

async function observe(dialog: Locator, name: string) {
  await dialog.evaluate((node, key) => {
    if (!(node instanceof HTMLDialogElement)) throw new Error("Native dialog required");
    window.settingsBackdropTrace ??= {};
    const records: PointerRecord[] = [];
    window.settingsBackdropTrace[key] = records;
    for (const type of ["pointerdown", "pointerup", "pointercancel", "click"]) {
      window.addEventListener(type, (event) => {
        if (!node.open || !(event instanceof MouseEvent) || !(event.target instanceof Node) || !node.contains(event.target)) return;
        records.push({
          type,
          trusted: event.isTrusted,
          target: event.target instanceof Element ? event.target.tagName : "other",
          x: event.clientX,
          y: event.clientY,
          pointerType: event instanceof PointerEvent ? event.pointerType : null,
          pointerId: event instanceof PointerEvent ? event.pointerId : null,
          open: node.open,
          url: location.href,
        });
      }, true);
    }
  }, name);
}

async function points(dialog: Locator, search: Locator) {
  const box = await dialog.boundingBox();
  const input = await search.boundingBox();
  if (!box || !input) throw new Error("Visible dialog and search required");
  return {
    inside: { x: input.x + 25, y: input.y + input.height / 2 },
    outside: { x: box.x / 2, y: box.y / 2 },
  };
}

async function drag(page: Page, start: { x: number; y: number }, end: { x: number; y: number }) {
  await page.mouse.move(start.x, start.y);
  await page.mouse.down();
  await page.mouse.move(end.x, end.y, { steps: 12 });
  await page.mouse.up();
}

async function openSettings(page: Page) {
  await page.goto("/?marker=backdrop&settings=notifications#keep");
  const dialog = page.getByRole("dialog", { name: "Settings", exact: true });
  const search = dialog.getByRole("searchbox", { name: "Search settings" });
  await expect(dialog).toBeVisible();
  await search.fill("group");
  await observe(dialog, "settings");
  return { dialog, search };
}

async function nativeReference(page: Page) {
  await page.evaluate(() => {
    const node = document.createElement("dialog");
    node.setAttribute("aria-label", "Native selection reference");
    node.setAttribute("closedby", "any");
    node.style.cssText = "box-sizing:border-box;width:min(400px,calc(100% - 24px));height:200px;padding:20px;margin:auto";
    const input = document.createElement("input");
    input.type = "search";
    input.setAttribute("aria-label", "Reference filter");
    input.value = "group";
    node.append(input);
    document.body.append(node);
    node.showModal();
  });
  const dialog = page.getByRole("dialog", { name: "Native selection reference", includeHidden: true });
  const search = dialog.getByRole("searchbox", { name: "Reference filter" });
  await observe(dialog, "native");
  const positions = await points(dialog, search);
  await drag(page, positions.inside, positions.outside);
  await expect(dialog).toBeVisible();
  await expect(search).toHaveValue("group");
  // Establish that this browser implements native light dismissal, rather than
  // treating an unsupported attribute as evidence that drags are preserved.
  await page.mouse.click(positions.outside.x, positions.outside.y);
  await expect(dialog).not.toBeVisible();
  await dialog.evaluate((node) => {
    if (!(node instanceof HTMLDialogElement)) throw new Error("Native dialog required");
    node.remove();
  });
}

test.afterEach(async ({ page }, info) => {
  await info.attach("trusted-settings-backdrop-events", {
    body: JSON.stringify({ ...runtime.get(page), ...await page.evaluate(() => ({
      events: window.settingsBackdropTrace ?? {},
      url: location.href,
      open: Array.from(document.querySelectorAll("dialog")).filter((node) => node.open).map((node) => node.getAttribute("aria-label") ?? node.getAttribute("aria-labelledby")),
    })) }),
    contentType: "application/json",
  });
  if (info.status === "passed") {
    expect(runtime.get(page)?.pageErrors).toEqual([]);
    expect(runtime.get(page)?.consoleErrors).toEqual([]);
    expect(runtime.get(page)?.blockedExternal).toEqual([]);
  }
});

for (const viewport of [{ width: 1280, height: 900 }, { width: 390, height: 844 }]) {
  test(`inside-to-backdrop selection keeps Settings open at ${viewport.width}px`, async ({ page }) => {
    await page.setViewportSize(viewport);
    const { dialog, search } = await openSettings(page);
    await nativeReference(page);
    const positions = await points(dialog, search);
    await drag(page, positions.inside, positions.outside);
    // Observe the existing URL transition when it happens; the bounded timeout
    // is an absence check, not a sleep used to establish hydration.
    await page.waitForURL((url) => !url.searchParams.has("settings"), { timeout: 1000 }).catch(() => {});
    await expect(dialog).toBeVisible();
    await expect(search).toHaveValue("group");
    expect(new URL(page.url()).searchParams.get("settings")).toBe("notifications");
    const traces = await page.evaluate(() => window.settingsBackdropTrace!);
    for (const key of ["native", "settings"]) {
      expect(traces[key].some((event) => event.type === "pointerdown" && event.target === "INPUT")).toBe(true);
      expect(traces[key].some((event) => event.type === "click" && event.target === "DIALOG")).toBe(true);
      expect(traces[key].every((event) => event.trusted)).toBe(true);
    }
  });

  test(`backdrop-to-inside selection keeps Settings open at ${viewport.width}px`, async ({ page }) => {
    await page.setViewportSize(viewport);
    const { dialog, search } = await openSettings(page);
    const positions = await points(dialog, search);
    await drag(page, positions.outside, positions.inside);
    await page.waitForURL((url) => !url.searchParams.has("settings"), { timeout: 1000 }).catch(() => {});
    await expect(dialog).toBeVisible();
    await expect(search).toHaveValue("group");
  });

  test(`an intentional backdrop click still dismisses Settings at ${viewport.width}px`, async ({ page }) => {
    await page.setViewportSize(viewport);
    const { dialog, search } = await openSettings(page);
    const positions = await points(dialog, search);
    await page.mouse.click(positions.outside.x, positions.outside.y);
    await expect(dialog).not.toBeVisible();
    await expect(page).toHaveURL((url) => url.search === "?marker=backdrop" && url.hash === "#keep");
    const target = viewport.width < 768 ? page.locator("#main-content") : page.getByRole("button", { name: "Open settings", exact: true });
    await expect(target).toBeFocused();
  });
}
