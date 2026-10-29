import { expect, test } from "@playwright/test";

type ImeKey = {
  type: string;
  isComposing: boolean;
  isTrusted: boolean;
  preventedAfterDispatch?: boolean;
};

declare global {
  interface Window {
    settingsImeKeys?: ImeKey[];
  }
}

for (const width of [390, 1280]) {
  test(`composing Escape preserves Settings at ${width}px, then ordinary Escape dismisses it`, async ({
    page,
  }, testInfo) => {
    await page.setViewportSize({ width, height: 844 });
    const mint = "7bS1mH6MXbw1GnEkKTU6w5YLTywPkQ1w3YVZXWFupump";
    const live = `/live?stream=${mint}&playback=paused`;
    await page.goto(
      `${live}${width < 768 ? "" : "&settings=notifications"}#keep`,
    );
    const sidebar = page.locator("[data-mobile-navigation]");
    if (width < 768) {
      await page.getByRole("button", { name: "Open navigation" }).click();
      await expect(sidebar).toHaveAttribute("data-mobile-navigation", "open");
      await page.getByRole("button", { name: "Open settings" }).click();
    }
    const dialog = page.getByRole("dialog", { name: "Settings", exact: true });
    const search = dialog.getByRole("searchbox", { name: "Search settings" });
    await search.fill("follow");
    // A controlled render establishes hydration before the native input sequence.
    await expect(
      dialog.getByRole("button", { name: "Clear settings search" }),
    ).toBeVisible();
    await page.evaluate(() => {
      window.settingsImeKeys = [];
      for (const type of ["keydown", "keyup"]) {
        document.addEventListener(
          type,
          (event) => {
            if (!(event instanceof KeyboardEvent) || event.key !== "Escape")
              return;
            const record: ImeKey = {
              type,
              isComposing: event.isComposing,
              isTrusted: event.isTrusted,
            };
            window.settingsImeKeys?.push(record);
            queueMicrotask(() => {
              record.preventedAfterDispatch = event.defaultPrevented;
            });
          },
          true,
        );
      }
    });
    const cdp = await page.context().newCDPSession(page);
    await cdp.send("Input.imeSetComposition", {
      text: "にほん",
      selectionStart: 3,
      selectionEnd: 3,
    });
    await page.keyboard.press("Escape");
    // The faulty handler starts a router transition. Let local requests finish
    // before asserting that the dialog and its URL really remained open.
    await page.waitForLoadState("networkidle");
    const events = await page.evaluate(() => window.settingsImeKeys);
    await testInfo.attach("trusted-composition-events", {
      body: JSON.stringify(events, null, 2),
      contentType: "application/json",
    });
    await page.screenshot({
      path: testInfo.outputPath(`settings-ime-${width}.png`),
    });
    expect(events?.find((event) => event.type === "keydown")).toMatchObject({
      isComposing: true,
      isTrusted: true,
    });
    await expect(dialog).toBeVisible();
    await expect(search).toBeFocused();
    expect(new URL(page.url()).searchParams.get("settings")).toBe(
      "notifications",
    );
    if (width < 768)
      await expect(sidebar).toHaveAttribute("data-mobile-navigation", "open");
    expect(events?.find((event) => event.type === "keydown")).toHaveProperty(
      "preventedAfterDispatch",
      false,
    );
    // Native composition has ended: the next Escape retains normal dismissal.
    await search.fill("follow");
    await page.keyboard.press("Escape");
    await expect(dialog).not.toBeVisible();
    const url = new URL(page.url());
    expect(url.searchParams.has("settings")).toBe(false);
    expect(url.searchParams.get("stream")).toBe(mint);
    expect(url.searchParams.get("playback")).toBe("paused");
    expect(url.hash).toBe("#keep");
    if (width < 768)
      await expect(sidebar).toHaveAttribute("data-mobile-navigation", "open");
    await expect(
      page.locator("#main-content").getByTestId("playback-unavailable"),
    ).toBeVisible();
  });
}
