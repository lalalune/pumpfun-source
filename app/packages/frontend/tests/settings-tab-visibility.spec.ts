import { expect, test, type Locator } from "@playwright/test";

async function selectedTabBounds(dialog: Locator) {
  return dialog.getByRole("tab", { selected: true }).evaluate((tab) => {
    const rail = tab.parentElement!;
    const tabBox = tab.getBoundingClientRect();
    const railBox = rail.getBoundingClientRect();
    return {
      label: tab.textContent,
      tabLeft: tabBox.left,
      tabRight: tabBox.right,
      railLeft: railBox.left + rail.clientLeft,
      railRight: railBox.left + rail.clientLeft + rail.clientWidth,
      scrollLeft: rail.scrollLeft,
      pageX: window.scrollX,
      pageY: window.scrollY,
      bodyOverflow: document.body.style.overflow,
    };
  });
}

async function expectSelectedTabInRail(dialog: Locator) {
  await expect
    .poll(
      async () => {
        const bounds = await selectedTabBounds(dialog);
        return (
          bounds.tabLeft >= bounds.railLeft - 1 &&
          bounds.tabRight <= bounds.railRight + 1
        );
      },
      {
        message:
          "The selected Settings tab must fit inside its own scroll rail",
      },
    )
    .toBe(true);
}

for (const width of [320, 390, 1440]) {
  test(`a Privacy deep link reveals its selected tab at ${width}px without moving focus`, async ({
    page,
  }, testInfo) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/?settings=privacy&setting=privacy.confirmExternalLinks");
    const dialog = page.getByRole("dialog", { name: "Settings", exact: true });
    const target = dialog.locator(
      '[data-setting-id="privacy.confirmExternalLinks"]',
    );
    // This focus is applied by the hydrated Settings effect, not the SSR HTML.
    await expect(target).toBeFocused();
    const bounds = await selectedTabBounds(dialog);
    await testInfo.attach("selected-tab-bounds", {
      body: JSON.stringify(bounds, null, 2),
      contentType: "application/json",
    });
    await page.screenshot({
      path: testInfo.outputPath(`settings-${width}.png`),
    });
    await expectSelectedTabInRail(dialog);
    await expect(target).toBeFocused();
    expect(bounds.pageX).toBe(0);
    expect(bounds.pageY).toBe(0);
    expect(bounds.bodyOverflow).toBe("hidden");
  });
}

test("an open Settings dialog reveals a URL-selected tab and preserves unrelated Live state", async ({
  page,
}) => {
  const mint = "7bS1mH6MXbw1GnEkKTU6w5YLTywPkQ1w3YVZXWFupump";
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(
    `/live?mint=${mint}&playback=paused&settings=notifications#keep`,
  );
  const dialog = page.getByRole("dialog", { name: "Settings", exact: true });
  const close = dialog.getByRole("button", { name: "Close settings" });
  await expect(close).toBeFocused();
  // Complete an actual controlled interaction before native-history updates;
  // the server-rendered autofocus button can precede router hydration.
  const search = dialog.getByRole("searchbox", { name: "Search settings" });
  await search.fill("external");
  await dialog.getByRole("button", { name: "Clear settings search" }).click();
  await expect(search).toHaveValue("");
  // Native history is an existing router integration; no Settings tab is clicked,
  // since clicking would let the browser reveal the offscreen button itself.
  await page.evaluate(() => {
    const url = new URL(location.href);
    url.searchParams.set("settings", "privacy");
    url.searchParams.set("setting", "privacy.confirmExternalLinks");
    history.replaceState(null, "", url);
  });
  const target = dialog.locator(
    '[data-setting-id="privacy.confirmExternalLinks"]',
  );
  await expect(target).toBeFocused();
  await expectSelectedTabInRail(dialog);
  const url = new URL(page.url());
  expect(url.searchParams.get("mint")).toBe(mint);
  expect(url.searchParams.get("playback")).toBe("paused");
  expect(url.hash).toBe("#keep");
});

test("narrowing an open Privacy dialog keeps its active tab in the rail without changing focus", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/?settings=privacy&setting=privacy.confirmExternalLinks");
  const dialog = page.getByRole("dialog", { name: "Settings", exact: true });
  const target = dialog.locator(
    '[data-setting-id="privacy.confirmExternalLinks"]',
  );
  await expect(target).toBeFocused();
  await expectSelectedTabInRail(dialog);
  await page.setViewportSize({ width: 320, height: 640 });
  await expectSelectedTabInRail(dialog);
  await expect(target).toBeFocused();
  // Returning to the left edge must also reveal the first selected tab.
  await page.evaluate(() => {
    const url = new URL(location.href);
    url.searchParams.set("settings", "trading");
    url.searchParams.delete("setting");
    history.replaceState(null, "", url);
  });
  await expect(
    dialog.getByRole("tab", { name: "Trading", exact: true }),
  ).toHaveAttribute("aria-selected", "true");
  await expectSelectedTabInRail(dialog);
});
