import { writeFile } from "node:fs/promises";
import { expect, test, type Page } from "@playwright/test";
import { openShellSearch } from "./shell-controls";

async function observe(page: Page) {
  const events: unknown[] = [];
  const errors: string[] = [];
  const unexpectedRequests: string[] = [];
  const origin = new URL(test.info().project.use.baseURL!).origin;
  page.context().on("request", (request) => {
    if (
      new URL(request.url()).origin !== origin ||
      !["GET", "HEAD"].includes(request.method())
    )
      unexpectedRequests.push(`${request.method()} ${request.url()}`);
  });
  page.context().on("response", (response) => {
    if (response.url().includes("/api/local-users/search?"))
      events.push({
        stage: "actual-local-search-response",
        url: response.url(),
        status: response.status(),
        dataSource: response.headers()["x-reconstruction-data-source"],
      });
  });
  page.context().on("page", (child) => {
    events.push({ stage: "actual-child-created", url: child.url() });
    child.on("pageerror", (error) => errors.push(error.message));
    child.on("console", (message) => {
      if (message.type() === "error") errors.push(message.text());
    });
  });
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
    if (message.text().startsWith("__profileNavigation:"))
      events.push(
        JSON.parse(message.text().slice("__profileNavigation:".length)),
      );
  });
  page.on("framenavigated", (frame) => {
    if (frame === page.mainFrame())
      events.push({ stage: "parent-navigation", url: frame.url() });
  });
  await page.addInitScript(() => {
    document.addEventListener(
      "click",
      (event) => {
        const link =
          event.target instanceof Element
            ? event.target.closest('a[href^="/profile/"]')
            : null;
        if (!link) return;
        console.debug(
          "__profileNavigation:" +
            JSON.stringify({
              stage: "actual-profile-click",
              trusted: event.isTrusted,
              ctrl: event.ctrlKey,
              meta: event.metaKey,
              shift: event.shiftKey,
              href: link.getAttribute("href"),
              parentUrl: location.href,
            }),
        );
      },
      true,
    );
    document.addEventListener(
      "close",
      (event) => {
        if (
          event.target instanceof HTMLDialogElement &&
          event.target.getAttribute("aria-label") ===
            "Search for coins and users"
        )
          console.debug(
            "__profileNavigation:" +
              JSON.stringify({
                stage: "native-dialog-close",
                parentUrl: location.href,
              }),
          );
      },
      true,
    );
  });
  return { events, errors, unexpectedRequests };
}

async function prepare(page: Page) {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("/");
  const input = await openShellSearch(page);
  await input.fill("alice");
  const dialog = page.getByRole("dialog", {
    name: "Search for coins and users",
  });
  const link = dialog.getByRole("link", { name: "alice_pump", exact: true });
  await expect(link).toBeVisible();
  return { input, dialog, link };
}

async function save(page: Page, data: unknown) {
  const state = await page.evaluate(() => {
    const dialog = document.querySelector<HTMLDialogElement>(
      'dialog[aria-label="Search for coins and users"]',
    );
    return {
      url: location.href,
      open: dialog?.open,
      query: dialog?.querySelector<HTMLInputElement>("input")?.value,
    };
  });
  await writeFile(
    test.info().outputPath("navigation-observations.json"),
    JSON.stringify({ state, data }, null, 2),
  );
  await page.screenshot({ path: test.info().outputPath("parent.png") });
}

for (const activation of ["pointer", "keyboard"] as const) {
  test(`ordinary ${activation} profile navigation closes search in its own tab`, async ({
    page,
  }) => {
    const observed = await observe(page);
    try {
      const { dialog, link } = await prepare(page);
      if (activation === "pointer") await link.click();
      else {
        await link.focus();
        await page.keyboard.press("Enter");
      }
      await expect(page).toHaveURL(/\/profile\/user-001$/);
      await expect(page.getByRole("heading", { level: 1 })).toHaveText(
        "alice_pump",
      );
      await expect(dialog).not.toBeVisible();
      expect(observed.errors).toEqual([]);
      expect(observed.unexpectedRequests).toEqual([]);
    } finally {
      await save(page, observed);
    }
  });
}

for (const modifier of ["Control", "Shift"] as const) {
  test(`${modifier}-click opens the local profile separately and keeps the parent search`, async ({
    page,
  }) => {
    const observed = await observe(page);
    let childUrl: string | undefined;
    let childHasOpener: boolean | undefined;
    let child: Page | undefined;
    try {
      const { input, dialog, link } = await prepare(page);
      const parentUrl = page.url();
      [child] = await Promise.all([
        page.context().waitForEvent("page", { timeout: 5000 }),
        link.click({ modifiers: [modifier] }),
      ]);
      await expect(child).toHaveURL(/\/profile\/user-001$/);
      await expect(child.getByRole("heading", { level: 1 })).toHaveText(
        "alice_pump",
      );
      childUrl = child.url();
      childHasOpener = (await child.opener()) !== null;
      await expect(page).toHaveURL(parentUrl);
      await expect(dialog).toBeVisible();
      await expect(input).toHaveValue("alice");
      await expect(link).toBeVisible();
      expect(observed.errors).toEqual([]);
      expect(observed.unexpectedRequests).toEqual([]);
    } finally {
      await save(page, { ...observed, childUrl, childHasOpener });
      await child?.close();
    }
  });
}
