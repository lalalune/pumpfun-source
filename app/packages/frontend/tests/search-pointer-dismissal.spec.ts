import { writeFile } from "node:fs/promises";
import { expect, test, type Page } from "@playwright/test";

test.use({ viewport: { width: 1280, height: 900 } });

async function observe(page: Page) {
  const events: unknown[] = [];
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
    if (message.text().startsWith("__searchPointer:"))
      events.push(JSON.parse(message.text().slice("__searchPointer:".length)));
  });
  await page.addInitScript(() => {
    for (const type of [
      "pointerdown",
      "pointerup",
      "click",
      "cancel",
      "close",
      "focusin",
    ]) {
      document.addEventListener(
        type,
        (event) => {
          const dialog = document.querySelector<HTMLDialogElement>(
            'dialog[aria-label="Search for coins and users"]',
          );
          if (!dialog) return;
          const rect = dialog.getBoundingClientRect();
          const target = event.target instanceof Element ? event.target : null;
          console.debug(
            "__searchPointer:" +
              JSON.stringify({
                type,
                trusted: event.isTrusted,
                button: event instanceof MouseEvent ? event.button : undefined,
                pointerType:
                  event instanceof PointerEvent ? event.pointerType : undefined,
                insidePanel:
                  event instanceof MouseEvent
                    ? event.clientX >= rect.left &&
                      event.clientX <= rect.right &&
                      event.clientY >= rect.top &&
                      event.clientY <= rect.bottom
                    : undefined,
                open: dialog.open,
                target: target?.tagName,
                label: target?.getAttribute("aria-label"),
                url: location.href,
              }),
          );
        },
        true,
      );
    }
  });
  return { events, errors };
}

async function prepare(page: Page, touch = false) {
  await page.goto("/explore?q=retained");
  const trigger = page.getByRole("button", {
    name: "Search for coins and users",
    exact: true,
  });
  if (touch) await trigger.tap();
  else await trigger.click();
  const dialog = page.getByRole("dialog", {
    name: "Search for coins and users",
    exact: true,
  });
  await expect(dialog).toBeVisible();
  const input = dialog.getByRole("searchbox");
  await input.fill("pointer draft");
  const box = await dialog.boundingBox();
  if (!box) throw new Error("Search panel must have real bounds");
  const outside = { x: Math.max(4, box.x - 8), y: box.y + 10 };
  return { trigger, dialog, input, outside };
}

async function save(page: Page, data: unknown, name = "final") {
  const state = await page.evaluate(() => {
    const dialog = document.querySelector<HTMLDialogElement>(
      'dialog[aria-label="Search for coins and users"]',
    );
    return {
      url: location.href,
      open: dialog?.open,
      query: dialog?.querySelector<HTMLInputElement>("input")?.value,
      closedby: dialog?.getAttribute("closedby"),
      nativeClosedBy: dialog && Reflect.get(dialog, "closedBy"),
      supportsClosedBy: dialog && "closedBy" in dialog,
      focusedLabel: document.activeElement?.getAttribute("aria-label"),
    };
  });
  await writeFile(
    test.info().outputPath(`${name}.json`),
    JSON.stringify({ state, data }, null, 2),
  );
  await page.screenshot({ path: test.info().outputPath(`${name}.png`) });
}

test("inside clicks, an inside-to-outside drag and nonprimary outside press keep search open", async ({
  page,
}) => {
  const observed = await observe(page);
  try {
    const { dialog, input, outside } = await prepare(page);
    await input.click();
    await expect(dialog).toBeVisible();
    const box = await input.boundingBox();
    if (!box) throw new Error("Input must have real bounds");
    await page.mouse.move(box.x + 20, box.y + box.height / 2);
    await page.mouse.down();
    await page.mouse.move(outside.x, outside.y, { steps: 4 });
    await page.mouse.up();
    await expect(dialog).toBeVisible();
    await page.mouse.click(outside.x, outside.y, { button: "right" });
    await expect(dialog).toBeVisible();
    await expect(input).toHaveValue("pointer draft");
    await expect(page).toHaveURL(/\/explore\?q=retained$/);
    expect(observed.errors).toEqual([]);
  } finally {
    await save(page, observed);
  }
});

test("trusted backdrop click closes search and returns actual opener focus without changing the route", async ({
  page,
}) => {
  const observed = await observe(page);
  try {
    const { trigger, dialog, input, outside } = await prepare(page);
    await page.mouse.click(outside.x, outside.y);
    await expect(dialog).not.toBeVisible();
    await expect(page).toHaveURL(/\/explore\?q=retained$/);
    await expect(trigger).toBeFocused();
    await save(page, observed, "after-outside-close");
    await page.keyboard.press("Enter");
    await expect(dialog).toBeVisible();
    await expect(input).toHaveValue("pointer draft");
    await page.keyboard.press("Escape");
    await expect(dialog).not.toBeVisible();
    await expect(trigger).toBeFocused();
    expect(observed.errors).toEqual([]);
  } finally {
    await save(page, observed);
  }
});

test.describe("touch viewport", () => {
  test.use({
    viewport: { width: 390, height: 844 },
    hasTouch: true,
    isMobile: true,
  });
  test("trusted backdrop tap closes search and preserves its maintained draft", async ({
    page,
  }) => {
    const observed = await observe(page);
    try {
      const { trigger, dialog, input, outside } = await prepare(page, true);
      await page.touchscreen.tap(outside.x, outside.y);
      await expect(dialog).not.toBeVisible();
      await expect(page).toHaveURL(/\/explore\?q=retained$/);
      await save(page, observed, "after-outside-close");
      await trigger.tap();
      await expect(dialog).toBeVisible();
      await expect(input).toHaveValue("pointer draft");
      expect(observed.errors).toEqual([]);
    } finally {
      await save(page, observed);
    }
  });
});
