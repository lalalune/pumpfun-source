import { expect, test, type Page, type Route } from "@playwright/test";
import { createViaShell, openShellSearch } from "./shell-controls";

const includedRoutes = [
  ["/", "Home", "Feed"],
  ["/explore", "Explore", "Explore"],
  ["/leaderboard", "Leaderboard", "Leaderboard"],
  ["/live", "Live", "Live"],
  ["/go", "GO", "GO"],
  ["/mayhem", "Mayhem", "Mayhem"],
  ["/holder-rewards", "Holder rewards", "Holder rewards"],
  ["/portfolio", "Portfolio", "Solana portfolio"],
  ["/create", "Create a coin", "Create a coin"],
] as const;

const viewports = [
  ["desktop", 1440, 900],
  ["laptop", 1280, 800],
  ["tablet", 768, 1024],
  ["mobile", 390, 844],
  ["small mobile", 375, 667],
] as const;

function activeNavigation(page: Page) {
  return page.locator('#app-sidebar [aria-current="page"]');
}

test("included routes load with one accurate active navigation item", async ({
  page,
}) => {
  for (const [path, navigationLabel, heading] of includedRoutes) {
    const response = await page.goto(path);
    expect(response?.status(), path).toBe(200);
    await expect(
      page.getByRole("heading", { level: 1, name: heading }),
    ).toBeVisible();
    await expect(activeNavigation(page)).toHaveCount(1);
    await expect(activeNavigation(page)).toHaveAttribute(
      "aria-label",
      navigationLabel,
    );
    if (path === "/") {
      await expect(
        page.locator('[data-product-state="unavailable"]'),
      ).toHaveCount(0);
      await expect(page.getByTestId("local-feed-item")).toHaveCount(3);
    } else if (path === "/leaderboard") {
      await expect(page.getByTestId("leaderboard-error")).toBeVisible();
    } else if (path === "/explore") {
      await expect(
        page.locator('[data-product-state="unavailable"]'),
      ).toHaveCount(0);
      await expect(page.getByTestId("historical-coin-card")).toBeVisible();
    } else if (path === "/live") {
      await expect(
        page.locator('[data-product-state="unavailable"]'),
      ).toHaveCount(0);
      await expect(
        page.getByTestId("archived-stream-card").first(),
      ).toBeVisible();
    } else if (path === "/go") {
      await expect(
        page.locator('[data-product-state="unavailable"]'),
      ).toHaveCount(0);
      await expect(page.getByTestId("go-bounty-card").first()).toBeVisible();
    } else if (path === "/create") {
      await expect(
        page.locator('[data-product-state="unavailable"]'),
      ).toHaveCount(0);
      await expect(page.getByRole("form")).toBeVisible();
    } else if (path === "/holder-rewards") {
      await expect(
        page.locator('[data-product-state="unavailable"]'),
      ).toHaveCount(0);
      await expect(page.getByTestId("holder-rewards-inspector")).toBeVisible();
    } else if (path === "/portfolio") {
      await expect(
        page.locator('[data-product-state="unavailable"]'),
      ).toHaveCount(0);
      await expect(
        page.getByRole("form", { name: "Load public Solana wallet" }),
      ).toBeVisible();
    } else if (path === "/mayhem") {
      await expect(
        page.locator('[data-product-state="unavailable"]'),
      ).toHaveCount(0);
      await expect(page.getByTestId("mayhem-unavailable")).toBeVisible();
    } else {
      await expect(
        page.locator('[data-product-state="unavailable"]'),
      ).toBeVisible();
    }
  }
});

test("desktop navigation reaches every included route and preserves the shell", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");
  await expect(
    page.getByRole("complementary", { name: "Application navigation" }),
  ).toBeVisible();
  for (const [path, navigationLabel, heading] of includedRoutes.slice(1)) {
    if (path === "/create") await createViaShell(page);
    else
      await page
        .getByRole("link", { name: navigationLabel, exact: true })
        .click();
    await expect(page).toHaveURL(new RegExp(`${path}$`));
    await expect(
      page.getByRole("heading", { level: 1, name: heading }),
    ).toBeVisible();
    await expect(activeNavigation(page)).toHaveAttribute(
      "aria-label",
      navigationLabel,
    );
  }
  await expect(page.getByRole("search")).toBeVisible();
});

test("mobile navigation traps focus, restores it and closes after navigation", async ({
  page,
}) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/");
  const shell = page.locator("[data-app-shell]");
  const navigation = page.locator("#app-sidebar");
  const open = page.getByRole("button", { name: "Open navigation" });

  await expect(navigation).toHaveAttribute("inert", "");
  await expect(open).toHaveAttribute("aria-expanded", "false");
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Skip to main content" }),
  ).toBeFocused();
  // The captured shell reaches header controls before its bottom mobile navigation.
  for (
    let step = 0;
    step < 40 &&
    !(await open.evaluate((element) => element === document.activeElement));
    step++
  ) {
    await page.keyboard.press("Tab");
  }
  await expect(open).toBeFocused();
  expect(
    await open.evaluate((element) => ({
      focusVisible: element.matches(":focus-visible"),
      outlineStyle: getComputedStyle(element).outlineStyle,
      outlineWidth: getComputedStyle(element).outlineWidth,
    })),
  ).toEqual({
    focusVisible: true,
    outlineStyle: "solid",
    outlineWidth: "2px",
  });
  await page.keyboard.press("Enter");
  await expect(open).toHaveAttribute("aria-expanded", "true");
  await expect(shell).toHaveAttribute("data-mobile-navigation", "open");
  await expect(
    page.getByRole("complementary", { name: "Application navigation" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Close navigation", exact: true }),
  ).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(
    navigation.getByRole("link", { name: "Pump reconstruction home" }),
  ).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(
    navigation.getByRole("link", { name: "Terms", exact: true }),
  ).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(
    navigation.getByRole("link", { name: "Pump reconstruction home" }),
  ).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(shell).toHaveAttribute("data-mobile-navigation", "closed");
  await expect(open).toHaveAttribute("aria-expanded", "false");
  await expect(open).toBeFocused();
  await expect(navigation).toHaveAttribute("inert", "");

  await open.click();
  await navigation.getByRole("link", { name: "Explore", exact: true }).click();
  await expect(page).toHaveURL(/\/explore$/);
  await expect(shell).toHaveAttribute("data-mobile-navigation", "closed");

  await open.click();
  await page
    .getByRole("button", { name: "Close navigation", exact: true })
    .click();
  await expect(shell).toHaveAttribute("data-mobile-navigation", "closed");
  await expect(open).toBeFocused();
});

for (const width of [320, 375]) {
  test(`Create a coin remains reachable at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: width === 320 ? 640 : 812 });
    await page.goto("/");
    // This case tests the mounted drawer/menu, after the responsive effect.
    await expect(page.locator("#app-sidebar")).toHaveAttribute(
      "aria-hidden",
      "true",
    );
    await page.getByRole("button", { name: "Open navigation" }).click();
    await page
      .getByRole("complementary", { name: "Application navigation" })
      .getByRole("button", { name: "Create a coin", exact: true })
      .click();
    const create = page
      .getByRole("menu", { name: "Create", exact: true })
      .getByRole("menuitem", { name: "Create coin", exact: true });
    await expect(create).toBeVisible();
    const target = await create.getAttribute("href");
    expect(target).toBe("/create");
    await create.click();
    await expect(page).toHaveURL(/\/create$/);
    await expect(activeNavigation(page)).toHaveAttribute(
      "aria-label",
      "Create a coin",
    );
  });
}

test("search encodes queries, follows history and handles clearing and empties", async ({
  page,
}) => {
  await page.goto("/");
  const input = await openShellSearch(page);
  await input.fill("alpha & beta=one");
  await input.press("Enter");
  await expect(page).toHaveURL(/\/explore\?q=alpha\+%26\+beta%3Done$/);
  await expect(
    page.getByText("alpha & beta=one", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "No matching local record" }),
  ).toBeVisible();

  await page.goBack();
  await expect(page).toHaveURL(/\/$/);
  await openShellSearch(page);
  await expect(input).toHaveValue("");
  await page.goForward();
  await expect(page).toHaveURL(/\/explore\?q=/);
  await openShellSearch(page);
  await expect(input).toHaveValue("alpha & beta=one");

  await page.getByRole("button", { name: "Clear search" }).click();
  await expect(page).toHaveURL(/\/explore$/);
  await expect(input).toHaveValue("");
  await input.fill("   ");
  await input.press("Enter");
  await expect(page).toHaveURL(/\/explore$/);
});

test("keyboard traversal reaches shell navigation, search and actions", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");
  const focused: string[] = [];
  for (let index = 0; index < 18; index += 1) {
    await page.keyboard.press("Tab");
    focused.push(
      await page.evaluate(() => {
        const element = document.activeElement;
        return (
          element?.getAttribute("aria-label") ??
          element?.getAttribute("id") ??
          element?.textContent?.trim() ??
          ""
        );
      }),
    );
  }
  expect(focused).toContain("Home");
  expect(focused).toContain("Explore");
  expect(focused).toContain("Create a coin");
  expect(focused).toContain("Search for coins and users");
  const search = await openShellSearch(page);
  await expect(search).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("dialog", {
      name: "Search for coins and users",
      exact: true,
    }),
  ).not.toBeVisible();
});

test("requested viewports have usable controls and no horizontal overflow", async ({
  page,
}) => {
  for (const [name, width, height] of viewports) {
    await page.setViewportSize({ width, height });
    await page.goto("/");
    const dimensions = await page.evaluate(() => ({
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
    }));
    expect(dimensions.scrollWidth, name).toBeLessThanOrEqual(
      dimensions.clientWidth,
    );
    await expect(
      page.getByRole("button", {
        name: "Search for coins and users",
        exact: true,
      }),
    ).toBeVisible();
    if (width < 768) {
      const menuBox = await page
        .getByRole("button", { name: "Open navigation" })
        .boundingBox();
      expect(menuBox?.width, name).toBeGreaterThanOrEqual(44);
      expect(menuBox?.height, name).toBeGreaterThanOrEqual(44);
    } else {
      await expect(
        page
          .getByRole("complementary", { name: "Application navigation" })
          .getByRole("button", { name: "Create a coin", exact: true }),
      ).toBeVisible();
      await expect(
        page.getByRole("button", { name: "Open navigation" }),
      ).toBeHidden();
    }
  }
});

test("unknown and explicitly excluded routes return not found", async ({
  page,
}) => {
  for (const path of [
    "/unknown-route",
    "/coin/example",
    "/pump-token",
    "/support",
    "/perps",
  ]) {
    const response = await page.goto(path);
    expect(response?.status(), path).toBe(404);
    await expect(
      page.getByRole("heading", { name: "Page not reconstructed" }),
    ).toBeVisible();
  }
});

test("normal navigation emits no console errors or production mutations", async ({
  page,
}) => {
  const consoleErrors: string[] = [];
  const unexpectedRequests: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (url.origin !== "http://127.0.0.1:3010") {
      unexpectedRequests.push(
        `${request.method()} ${url.origin}${url.pathname}`,
      );
    }
    if (!["GET", "HEAD"].includes(request.method())) {
      unexpectedRequests.push(`${request.method()} ${url.pathname}`);
    }
  });

  await page.goto("/");
  await page.getByRole("link", { name: "Live", exact: true }).click();
  await (await openShellSearch(page)).fill("safe query");
  await page
    .getByRole("dialog", { name: "Search for coins and users", exact: true })
    .getByRole("button", { name: "Search", exact: true })
    .click();
  await expect(page).toHaveURL(/\/explore\?q=safe\+query$/);
  await expect(
    page.getByRole("heading", { name: "0 local matches" }),
  ).toBeVisible();
  await expect(
    page.getByText(/not a statement about live Pump market results/),
  ).toBeVisible();
  expect(consoleErrors).toEqual([]);
  expect(unexpectedRequests).toEqual([]);
});

test("a delayed search clear preserves a newly typed draft", async ({
  page,
}) => {
  await page.goto("/explore?q=previous", { waitUntil: "networkidle" });
  const input = await openShellSearch(page);
  await expect(input).toHaveValue("previous");
  const held: Route[] = [];
  let holdClear = true;
  await page.route("**/explore?**", async (route) => {
    if (holdClear && new URL(route.request().url()).searchParams.has("_rsc")) {
      held.push(route);
    } else {
      await route.continue();
    }
  });
  try {
    await page
      .getByRole("button", { name: "Clear search", exact: true })
      .click();
    await expect.poll(() => held.length).toBe(1);
    await input.fill("new draft");
    holdClear = false;
    await Promise.all(held.map((route) => route.continue()));
    await expect(page).toHaveURL(/\/explore$/);
    await expect(input).toHaveValue("new draft");
    await input.press("Enter");
    await expect(page).toHaveURL(/\/explore\?q=new\+draft$/);
    await openShellSearch(page);
    await page.goBack();
    await expect(page).toHaveURL(/\/explore$/);
    await expect(input).toHaveValue("");
    await page.goForward();
    await expect(input).toHaveValue("new draft");
  } finally {
    await page.unrouteAll({ behavior: "ignoreErrors" });
  }
});
