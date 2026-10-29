import { expect, test } from "@playwright/test";

for (const target of ["trigger", "link"] as const) {
  test(`desktop sidebar ${target} transfers focus to its mobile opener when hidden`, async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto("/?settings=notifications");
    await expect(
      page.getByRole("dialog", { name: "Settings", exact: true }),
    ).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(
      page.getByRole("button", { name: "Open settings", exact: true }),
    ).toBeFocused();
    const sidebar = page.getByRole("complementary", {
      name: "Application navigation",
    });
    const active =
      target === "trigger"
        ? page.locator("#app-sidebar-trigger")
        : sidebar.getByRole("link", { name: "Explore", exact: true });
    await active.focus();
    await expect(active).toBeFocused();
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(page.locator("#app-sidebar")).toHaveAttribute("inert", "");
    const opener = page.getByRole("button", {
      name: "Open navigation",
      exact: true,
    });
    await expect(opener).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(
      page.getByRole("button", { name: "Close navigation", exact: true }),
    ).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(opener).toBeFocused();
    await page.setViewportSize({ width: 1280, height: 900 });
    await expect(page.locator("#app-sidebar-trigger")).toBeFocused();
  });
}

test("the breakpoint does not steal focus from content outside the sidebar", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("/?settings=notifications");
  await expect(
    page.getByRole("dialog", { name: "Settings", exact: true }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "Open settings", exact: true }),
  ).toBeFocused();
  const tab = page.getByRole("tab", { name: "For you", exact: true });
  await tab.focus();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator("#app-sidebar")).toHaveAttribute("inert", "");
  await expect(tab).toBeFocused();
});
