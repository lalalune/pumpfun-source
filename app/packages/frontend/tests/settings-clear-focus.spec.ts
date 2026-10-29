import { expect, test, type Page } from "@playwright/test";

const records = new WeakMap<Page, { errors: string[]; blocked: string[] }>();

async function nativeSearchControl(page: Page, activation: "mouse" | "keyboard") {
  await page.evaluate(() => {
    const dialog = document.createElement("dialog");
    dialog.setAttribute("aria-label", "Native search reference");
    dialog.style.cssText = "box-sizing:border-box;width:min(340px,calc(100% - 24px));height:180px;margin:auto;padding:20px";
    const search = document.createElement("input");
    search.type = "search";
    search.setAttribute("aria-label", "Native search control");
    search.style.cssText = "box-sizing:border-box;width:100%;height:44px;font:16px sans-serif;appearance:auto";
    dialog.append(search);
    document.body.append(dialog);
    dialog.showModal();
  });
  const native = page.getByRole("dialog", { name: "Native search reference" });
  const search = native.getByRole("searchbox", { name: "Native search control" });
  await search.fill("not-a-mapped-setting");
  if (activation === "mouse") {
    const box = await search.boundingBox();
    if (!box) throw new Error("Visible native search required");
    await page.mouse.click(box.x + box.width - 8, box.y + box.height / 2);
  } else await search.press("Escape");
  await expect(search).toHaveValue("");
  await expect(search).toBeFocused();
  await page.keyboard.type("group");
  await expect(search).toHaveValue("group");
  await page.evaluate((mode) => document.documentElement.setAttribute("data-native-clear-reference", JSON.stringify({ activation: mode, cleared: true, continuedTyping: "group", inputFocused: true })), activation);
  await native.evaluate((node) => {
    if (!(node instanceof HTMLDialogElement)) throw new Error("Native dialog required");
    node.close();
    node.remove();
  });
}
test.beforeEach(async ({ page, context, baseURL }) => {
  const origin = new URL(baseURL!).origin;
  const row = { errors: [] as string[], blocked: [] as string[] };
  records.set(page, row);
  page.on("pageerror", (error) => row.errors.push(error.message));
  await context.route("**/*", (route) => {
    if (new URL(route.request().url()).origin === origin) return route.continue();
    row.blocked.push(route.request().url());
    return route.abort();
  });
});

test.afterEach(async ({ page }, info) => {
  const state = await page.evaluate(() => ({
    activeTag: document.activeElement?.tagName ?? null,
    activeId: document.activeElement?.id ?? null,
    settingsOpen: Array.from(document.querySelectorAll("dialog")).some((node) => node.open && node.querySelector("h2")?.textContent === "Settings"),
    trace: document.documentElement.getAttribute("data-settings-clear-trace"),
    nativeReference: document.documentElement.getAttribute("data-native-clear-reference"),
    url: location.href,
  }));
  await info.attach("settings-clear-focus-evidence", {
    body: JSON.stringify({ ...records.get(page), ...state }),
    contentType: "application/json",
  });
  if (info.status === "passed") {
    expect(records.get(page)?.errors).toEqual([]);
    expect(records.get(page)?.blocked).toEqual([]);
  }
});

for (const viewport of [{ width: 1280, height: 900 }, { width: 390, height: 844 }]) {
  for (const activation of ["mouse", "keyboard"] as const) {
    test(`clearing Settings allows immediate continued typing at ${viewport.width}px by ${activation}`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto("/?marker=clear&settings=notifications#keep");
      const dialog = page.getByRole("dialog", { name: "Settings", exact: true });
      const search = dialog.getByRole("searchbox", { name: "Search settings" });
      await search.fill("not-a-mapped-setting");
      await expect(dialog.getByRole("heading", { name: "No matching settings" })).toBeVisible();
      await nativeSearchControl(page, activation);
      const clear = dialog.getByRole("button", { name: "Clear settings search" });
      if (activation === "keyboard") {
        await search.press("Tab");
        await expect(clear).toBeFocused();
      }
      await page.evaluate(() => {
        const rows: unknown[] = [];
        window.addEventListener("keydown", (event) => {
          rows.push({ type: event.type, key: event.key, trusted: event.isTrusted, target: event.target instanceof Element ? event.target.tagName : null });
          document.documentElement.setAttribute("data-settings-clear-trace", JSON.stringify(rows));
        }, true);
      });
      if (activation === "mouse") await clear.click();
      else await page.keyboard.press("Enter");
      await expect(search).toHaveValue("");
      // Continue the actual keyboard workflow; fill() would refocus the input
      // and conceal the loss of focus caused by removing the Clear button.
      await page.keyboard.type("group");
      await expect(search).toHaveValue("group");
      await expect(search).toBeFocused();
      await expect(dialog.getByRole("heading", { name: "Group chats", exact: true })).toBeVisible();
      expect(new URL(page.url()).search).toBe("?marker=clear&settings=notifications");
      expect(new URL(page.url()).hash).toBe("#keep");
    });
  }
}
