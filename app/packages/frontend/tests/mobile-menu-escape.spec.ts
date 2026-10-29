import { writeFile } from "node:fs/promises";
import { expect, test, type Page } from "@playwright/test";

async function observeEscape(page: Page) {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  await page.addInitScript(() => {
    const events: unknown[] = [];
    Reflect.set(window, "__menuEscapeEvents", events);
    // Bubble observation follows the actual portal menu's React key handler
    // and precedes the mobile drawer's window key handler. No input is changed.
    document.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      const target = event.target instanceof Element ? event.target : null;
      events.push({
        key: event.key,
        preventedBeforeWindow: event.defaultPrevented,
        targetRole: target?.getAttribute("role"),
        targetText: target?.textContent,
        drawer: document
          .querySelector("[data-app-shell]")
          ?.getAttribute("data-mobile-navigation"),
      });
    });
  });
  return errors;
}

async function saveObservation(page: Page, errors: string[]) {
  const state = await page.evaluate(() => ({
    events: Reflect.get(window, "__menuEscapeEvents"),
    drawer: document
      .querySelector("[data-app-shell]")
      ?.getAttribute("data-mobile-navigation"),
    focused: document.activeElement?.getAttribute("aria-label"),
    url: location.href,
  }));
  await writeFile(
    test.info().outputPath("escape-observations.json"),
    JSON.stringify({ errors, ...state }, null, 2),
  );
  await page.screenshot({
    path: test.info().outputPath("navigation.png"),
    animations: "disabled",
  });
}

for (const width of [375, 767]) {
  test(`Escape closes the nested Create menu before the mobile drawer at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 812 });
    const errors = await observeEscape(page);
    try {
      await page.goto("/explore");
      // The provider initially renders desktop state; wait for its real
      // responsive effect before testing an already-mounted nested menu.
      await expect(page.locator("#app-sidebar")).toHaveAttribute(
        "aria-hidden",
        "true",
      );
      const more = page.getByRole("button", {
        name: "Open navigation",
        exact: true,
      });
      const drawer = page.getByRole("complementary", {
        name: "Application navigation",
      });
      const shell = page.locator("[data-app-shell]");
      await more.click();
      // This focus is installed by the same real effect as the Escape listener.
      await expect(
        page.getByRole("button", { name: "Close navigation", exact: true }),
      ).toBeFocused();
      const create = drawer.getByRole("button", {
        name: "Create a coin",
        exact: true,
      });
      await create.click();
      const menu = page.getByRole("menu", { name: "Create", exact: true });
      await expect(
        menu.getByRole("menuitem", { name: "Create coin", exact: true }),
      ).toBeFocused();
      await page.keyboard.press("Escape");
      await expect(menu).not.toBeVisible();
      await expect(shell).toHaveAttribute("data-mobile-navigation", "open");
      await expect(create).toBeFocused();
      await expect(page.locator("[data-shell-content]")).toHaveAttribute(
        "inert",
        "",
      );
      await expect(page).toHaveURL(/\/explore$/);
      await page.screenshot({
        path: test.info().outputPath("after-menu-escape.png"),
        animations: "disabled",
      });
      await page.keyboard.press("Escape");
      await expect(shell).toHaveAttribute("data-mobile-navigation", "closed");
      await expect(more).toBeFocused();
      await expect(page.locator("[data-shell-content]")).not.toHaveAttribute(
        "inert",
      );
      const events = await page.evaluate(() =>
        Reflect.get(window, "__menuEscapeEvents"),
      );
      expect(
        events.map(
          (event: { preventedBeforeWindow: boolean }) =>
            event.preventedBeforeWindow,
        ),
      ).toEqual([true, false]);
      expect(errors).toEqual([]);
    } finally {
      await saveObservation(page, errors);
    }
  });
}
