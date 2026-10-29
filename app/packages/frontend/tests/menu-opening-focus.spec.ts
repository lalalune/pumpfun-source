import { expect, test } from "@playwright/test";

test("menu opening arrows choose their corresponding edge on every opening", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("/?settings=notifications");
  await expect(
    page.getByRole("dialog", { name: "Settings", exact: true }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  const trigger = page
    .getByRole("navigation", { name: "Footer", exact: true })
    .getByRole("button", { name: "Resources", exact: true });
  await trigger.scrollIntoViewIfNeeded();
  await trigger.focus();
  await page.evaluate(
    () =>
      new Promise<void>((resolve) => {
        // Drain scroll events from bringing the footer trigger into view before opening.
        requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
      }),
  );
  const menu = page.getByRole("menu", { name: "Resources", exact: true });
  const first = menu.getByRole("menuitem", { name: "PumpSwap", exact: true });
  const last = menu.getByRole("menuitem", {
    name: "Wallet sign-in changes",
    exact: true,
  });
  await page.keyboard.press("ArrowUp");
  await expect(last).toBeFocused();
  await page.keyboard.press("ArrowDown");
  await expect(first).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(trigger).toBeFocused();
  await page.keyboard.press("ArrowDown");
  await expect(first).toBeFocused();
  await page.keyboard.press("ArrowUp");
  await expect(last).toBeFocused();
  await page.keyboard.press("Escape");
  await trigger.click();
  await expect(first).toBeFocused();
});
