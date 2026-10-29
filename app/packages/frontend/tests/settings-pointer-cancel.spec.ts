import { expect, test } from "@playwright/test";

test("cancelled trusted backdrop touch preserves Settings and permits a later outside click", async ({ page, context, baseURL }, info) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const errors: string[] = [];
  const blocked: string[] = [];
  const origin = new URL(baseURL!).origin;
  page.on("pageerror", (error) => errors.push(error.message));
  await context.route("**/*", (route) => {
    if (new URL(route.request().url()).origin === origin) return route.continue();
    blocked.push(route.request().url());
    return route.abort();
  });
  await page.goto("/?marker=cancel&settings=notifications#keep");
  const dialog = page.getByRole("dialog", { name: "Settings", exact: true });
  const search = dialog.getByRole("searchbox", { name: "Search settings" });
  await search.fill("group");
  await dialog.evaluate((node) => {
    const events: { type: string; trusted: boolean; pointerType: string }[] = [];
    node.setAttribute("data-cancel-events", "[]");
    for (const type of ["pointerdown", "pointercancel"]) {
      node.addEventListener(type, (event) => {
        if (!(event instanceof PointerEvent)) return;
        events.push({ type, trusted: event.isTrusted, pointerType: event.pointerType });
        node.setAttribute("data-cancel-events", JSON.stringify(events));
      });
    }
  });
  const box = await dialog.boundingBox();
  if (!box) throw new Error("Visible Settings required");
  const outside = { x: box.x / 2, y: box.y / 2 };
  const cdp = await context.newCDPSession(page);
  try {
    await cdp.send("Input.dispatchTouchEvent", {
      type: "touchStart",
      touchPoints: [{ x: outside.x, y: outside.y, id: 1 }],
    });
    await cdp.send("Input.dispatchTouchEvent", { type: "touchCancel", touchPoints: [] });
    await expect(dialog).toHaveAttribute("data-cancel-events", /pointercancel/);
    const events = JSON.parse(await dialog.getAttribute("data-cancel-events") ?? "[]");
    expect(events).toEqual([
      { type: "pointerdown", trusted: true, pointerType: "touch" },
      { type: "pointercancel", trusted: true, pointerType: "touch" },
    ]);
    await expect(dialog).toBeVisible();
    await expect(search).toHaveValue("group");
    await page.screenshot({ path: info.outputPath("settings-pointer-cancel.png") });
    await page.mouse.click(outside.x, outside.y);
    await expect(dialog).not.toBeVisible();
    await expect(page).toHaveURL((url) => url.search === "?marker=cancel" && url.hash === "#keep");
    await expect(page.locator("#main-content")).toBeFocused();
    expect(errors).toEqual([]);
    expect(blocked).toEqual([]);
    await info.attach("trusted-pointer-cancel", {
      body: JSON.stringify({ events, errors, blocked, finalURL: page.url(), scope: "Chromium CDP trusted touch cancellation and recovery; no operating-system touch compatibility claim" }),
      contentType: "application/json",
    });
  } finally {
    await cdp.detach();
  }
});
