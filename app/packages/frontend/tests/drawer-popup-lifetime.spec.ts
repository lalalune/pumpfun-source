import { writeFile } from "node:fs/promises";
import { expect, test, type Page } from "@playwright/test";
import { openShellSearch } from "./shell-controls";

async function observe(page: Page) {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  await page.addInitScript(() => {
    const trace: unknown[] = [];
    Reflect.set(window, "__drawerPopupTrace", trace);
    const record = (stage: string, event?: KeyboardEvent) => {
      if (trace.length >= 50) return;
      const menu = document.querySelector<HTMLElement>(
        '[role="menu"][aria-label="Create"]',
      );
      trace.push({
        stage,
        time: performance.now(),
        trusted: event?.isTrusted,
        prevented: event?.defaultPrevented,
        drawer: document
          .querySelector("[data-app-shell]")
          ?.getAttribute("data-mobile-navigation"),
        portalPresent: !!menu,
        portalRendered: !!menu?.getClientRects().length,
        focusedRole: document.activeElement?.getAttribute("role"),
        focusedLabel: document.activeElement?.getAttribute("aria-label"),
        focusedText: document.activeElement?.textContent?.slice(0, 80),
        url: location.href,
      });
    };
    document.addEventListener("keydown", (event) => {
      if (event.key === "b" && (event.ctrlKey || event.metaKey))
        record("actual-parent-shortcut", event);
    });
    document.addEventListener("focusin", () => record("native-focus-change"));
    let previous = "";
    new MutationObserver(() => {
      const menu = document.querySelector('[role="menu"][aria-label="Create"]');
      const state = [
        document
          .querySelector("[data-app-shell]")
          ?.getAttribute("data-mobile-navigation"),
        !!menu,
      ].join("|");
      if (state !== previous) {
        previous = state;
        record("drawer-portal-change");
      }
    }).observe(document, { childList: true, subtree: true, attributes: true });
  });
  return errors;
}

async function save(page: Page, errors: string[]) {
  const observation = await page.evaluate(() => ({
    trace: Reflect.get(window, "__drawerPopupTrace"),
    drawer: document
      .querySelector("[data-app-shell]")
      ?.getAttribute("data-mobile-navigation"),
    activePortal: !!document
      .querySelector('[role="menu"][aria-label="Create"]')
      ?.getClientRects().length,
    focusedRole: document.activeElement?.getAttribute("role"),
  }));
  await writeFile(
    test.info().outputPath("drawer-popup-observations.json"),
    JSON.stringify({ errors, ...observation }, null, 2),
  );
  await page.screenshot({
    path: test.info().outputPath("drawer-popup.png"),
    animations: "disabled",
  });
}

async function openMountedDrawerMenu(page: Page) {
  // Isolate already-mounted parent/child lifecycle from the separately
  // reconstructed first-offered More readiness boundary.
  await expect(page.locator("#app-sidebar")).toHaveAttribute(
    "aria-hidden",
    "true",
  );
  await page
    .getByRole("button", { name: "Open navigation", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Close navigation", exact: true }),
  ).toBeFocused();
  await page.getByTestId("create-button-sidebar").click();
  const menu = page.getByRole("menu", { name: "Create", exact: true });
  await expect(
    menu.getByRole("menuitem", { name: "Create coin", exact: true }),
  ).toBeFocused();
  return menu;
}

test("ordinary Create selection closes both menu and drawer", async ({
  page,
}) => {
  await page.setViewportSize({ width: 767, height: 900 });
  const errors = await observe(page);
  try {
    await page.goto("/explore");
    const menu = await openMountedDrawerMenu(page);
    await menu
      .getByRole("menuitem", { name: "Create coin", exact: true })
      .press("Enter");
    await expect(page).toHaveURL(/\/create$/);
    await expect(
      page.getByRole("heading", {
        level: 1,
        name: "Create a coin",
        exact: true,
      }),
    ).toBeVisible();
    await expect(page.locator("[data-app-shell]")).toHaveAttribute(
      "data-mobile-navigation",
      "closed",
    );
    await expect(menu).toHaveCount(0);
    // Closed navigation retains its route metadata, as the existing shell does.
    await expect(page.getByTestId("create-button-sidebar")).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(errors).toEqual([]);
  } finally {
    await save(page, errors);
  }
});

test("closing the drawer with its parent shortcut removes the active portal", async ({
  page,
}) => {
  await page.setViewportSize({ width: 767, height: 900 });
  const errors = await observe(page);
  try {
    await page.goto("/explore");
    const menu = await openMountedDrawerMenu(page);
    await page.keyboard.press("Control+b");
    await expect(page.locator("[data-app-shell]")).toHaveAttribute(
      "data-mobile-navigation",
      "closed",
    );
    await expect(page.locator("#app-sidebar")).toHaveAttribute("inert", "");
    await expect(menu).toHaveCount(0);
    await expect(page).toHaveURL(/\/explore$/);
    const more = page.getByRole("button", {
      name: "Open navigation",
      exact: true,
    });
    await expect(more).toBeFocused();
    await more.press("Enter");
    await expect(
      page.getByRole("button", { name: "Close navigation", exact: true }),
    ).toBeFocused();
    await page.getByTestId("create-button-sidebar").click();
    await expect(
      menu.getByRole("menuitem", { name: "Create coin", exact: true }),
    ).toBeFocused();
    await menu
      .getByRole("menuitem", { name: "Create coin", exact: true })
      .press("Enter");
    await expect(page).toHaveURL(/\/create$/);
    await expect(menu).toHaveCount(0);
    expect(errors).toEqual([]);
  } finally {
    await save(page, errors);
  }
});

test("desktop popup keeps identity and focus while its sidebar shortcut toggles the rail", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  const errors = await observe(page);
  try {
    await page.goto("/explore");
    const search = await openShellSearch(page);
    await search.press("Escape");
    const sidebar = page.locator("#app-sidebar");
    await expect(sidebar).toHaveAttribute("data-state", "collapsed");
    await page.keyboard.press("Control+b");
    await expect(sidebar).toHaveAttribute("data-state", "expanded");
    const create = page.getByTestId("create-button-sidebar");
    await create.click();
    const menu = page.getByRole("menu", { name: "Create", exact: true });
    await expect(
      menu.getByRole("menuitem", { name: "Create coin", exact: true }),
    ).toBeFocused();
    const menuId = await menu.getAttribute("id");
    await page.keyboard.press("Control+b");
    await expect(sidebar).toHaveAttribute("data-state", "collapsed");
    await expect(menu).toHaveAttribute("id", menuId!);
    await expect(
      menu.getByRole("menuitem", { name: "Create coin", exact: true }),
    ).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(menu).toHaveCount(0);
    await expect(create).toBeFocused();
    expect(errors).toEqual([]);
  } finally {
    await save(page, errors);
  }
});
