import { writeFile } from "node:fs/promises";
import { expect, test, type Page } from "@playwright/test";
import { openShellSearch } from "./shell-controls";

async function observe(page: Page) {
  const errors: string[] = [];
  const events: unknown[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
    if (
      message.type() === "debug" &&
      message.text().startsWith("__headerBack:")
    )
      events.push(JSON.parse(message.text().slice("__headerBack:".length)));
  });
  page.on("framenavigated", (frame) => {
    if (frame === page.mainFrame())
      events.push({ stage: "actual-navigation", url: frame.url() });
  });
  await page.addInitScript(() => {
    document.addEventListener(
      "click",
      (event) => {
        if (
          !(event.target instanceof Element) ||
          !event.target.closest('button[aria-label="Go back"]')
        )
          return;
        console.debug(
          "__headerBack:" +
            JSON.stringify({
              stage: "actual-back-click",
              trusted: event.isTrusted,
              url: location.href,
              historyLength: history.length,
            }),
        );
      },
      true,
    );
  });
  return { errors, events };
}

async function mountedHeader(page: Page) {
  const input = await openShellSearch(page);
  await input.press("Escape");
}

async function save(page: Page, data: unknown) {
  const current = await page.evaluate(() => ({
    url: location.href,
    historyLength: history.length,
  }));
  await writeFile(
    test.info().outputPath("back-observations.json"),
    JSON.stringify({ current, data }, null, 2),
  );
  await page.screenshot({
    path: test.info().outputPath("back-state.png"),
    animations: "disabled",
  });
}

test("header Back follows a real prior entry and preserves the Explore query", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  const observed = await observe(page);
  try {
    await page.goto("/explore?q=retained");
    await mountedHeader(page);
    await page.getByTestId("topbar-create-button").click();
    await page
      .getByRole("menu", { name: "Create", exact: true })
      .getByRole("menuitem", { name: "Create coin", exact: true })
      .press("Enter");
    await expect(page).toHaveURL(/\/create$/);
    expect(await page.evaluate(() => history.length)).toBeGreaterThan(1);
    await page.getByRole("button", { name: "Go back", exact: true }).click();
    await expect(page).toHaveURL(/\/explore\?q=retained$/);
    await expect(
      page.getByRole("searchbox", {
        name: "Search captured coins",
        exact: true,
      }),
    ).toHaveValue("retained");
    expect(observed.errors).toEqual([]);
  } finally {
    await save(page, observed);
  }
});

test("a first-entry header Back falls home and uses push rather than replace", async ({
  page,
  context,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  const observed = await observe(page);
  let nativeHistory: unknown;
  try {
    await page.goto("/create");
    await mountedHeader(page);
    const cdp = await context.newCDPSession(page);
    // Model a direct visit with a genuinely empty native back list. No history
    // getter or app/router hook is mocked or replaced.
    await cdp.send("Page.resetNavigationHistory");
    nativeHistory = await cdp.send("Page.getNavigationHistory");
    expect(await page.evaluate(() => history.length)).toBe(1);
    await page.getByRole("button", { name: "Go back", exact: true }).click();
    await expect(page).toHaveURL(/:\d+\/$/);
    await page.goBack();
    await expect(page).toHaveURL(/\/create$/);
    expect(observed.errors).toEqual([]);
  } finally {
    await save(page, { ...observed, nativeHistory });
  }
});

test("header Back follows the original route visibility on desktop and tablet", async ({
  page,
}) => {
  const observed = await observe(page);
  const states: unknown[] = [];
  try {
    for (const width of [1440, 768]) {
      await page.setViewportSize({ width, height: 1000 });
      for (const path of ["/", "/go", "/live", "/explore", "/create"]) {
        await page.goto(path);
        await mountedHeader(page);
        const back = page.getByRole("button", { name: "Go back", exact: true });
        const count = await back.count();
        states.push({ width, path, count });
        await expect(back).toHaveCount(
          ["/", "/go", "/live"].includes(path) ? 0 : 1,
        );
      }
    }
    expect(observed.errors).toEqual([]);
  } finally {
    await save(page, { ...observed, states });
  }
});
