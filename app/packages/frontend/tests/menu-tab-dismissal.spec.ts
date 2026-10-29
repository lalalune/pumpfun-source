import { expect, test } from "@playwright/test";

for (const width of [390, 1280]) {
  for (const reverse of [false, true]) {
    const direction = reverse ? "backward" : "forward";
    test(`Tab ${direction} exits Create menu at ${width}px`, async ({
      page,
      baseURL,
    }) => {
      await page.setViewportSize({ width, height: 844 });
      const unexpected: string[] = [];
      page.on("request", (request) => {
        if (
          new URL(request.url()).origin !== new URL(baseURL!).origin ||
          !["GET", "HEAD"].includes(request.method())
        )
          unexpected.push(`${request.method()} ${request.url()}`);
      });
      await page.goto("/", { waitUntil: "networkidle" });
      const mobile = width === 390;
      await page
        .getByTestId(mobile ? "create-button-mobile-nav" : "topbar-create-button")
        .click();
      const menu = page.getByRole("menu", { name: "Create", exact: true });
      await expect(
        menu.getByRole("menuitem", { name: "Create coin", exact: true }),
      ).toBeFocused();

      await page.keyboard.press(reverse ? "Shift+Tab" : "Tab");
      await expect(menu).toHaveCount(0);
      const target = mobile
        ? page
            .getByRole("navigation", { name: "Mobile", exact: true })
            .getByRole("link", { name: reverse ? "Explore" : "GO", exact: true })
        : page.getByRole("button", {
            name: reverse ? "Search for coins and users" : "Sign in",
            exact: true,
          });
      await expect(target).toBeFocused();
      expect(unexpected).toEqual([]);
    });
  }
}
