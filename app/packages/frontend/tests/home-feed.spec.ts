import { expect, test, type Page } from "@playwright/test";

function collectSafetyViolations(page: Page) {
  const requests: string[] = [];
  const consoleErrors: string[] = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (
      url.origin !== "http://127.0.0.1:3010" ||
      !["GET", "HEAD"].includes(request.method())
    ) {
      requests.push(`${request.method()} ${request.url()}`);
    }
  });
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  return { requests, consoleErrors };
}

test("renders validated root posts with explicit synthetic provenance", async ({
  page,
}) => {
  const safety = collectSafetyViolations(page);
  const response = await page.goto("/");
  expect(response?.status()).toBe(200);

  await expect(
    page.getByText("Local example data — not live Pump activity", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.getByTestId("local-feed-item")).toHaveCount(3);
  await expect(page.getByRole("tab", { name: "Local callouts" })).toHaveCount(
    0,
  );
  await expect(page.getByTestId("local-feed-item").nth(0)).toContainText(
    "chad_group",
  );
  await expect(page.getByTestId("local-feed-item").nth(1)).toContainText(
    "bob_degen",
  );
  await expect(page.getByTestId("local-feed-item").nth(2)).toContainText(
    "alice_pump",
  );
  await expect(page.getByText("Reply 1 to Alice")).toHaveCount(0);
  await expect(page.getByText("Hidden post")).toHaveCount(0);
  await expect(page.getByText("Deleted post")).toHaveCount(0);
  await expect(
    page.getByRole("img", { name: "External media withheld in offline mode" }),
  ).toBeVisible();
  await expect(page.locator("main img")).toHaveCount(0);
  await expect(page.locator('main a[href^="/profile"]')).toHaveCount(3);
  await expect(
    page.getByText("Synthetic example", { exact: true }),
  ).toHaveCount(3);
  expect(safety.requests).toEqual([]);
  expect(safety.consoleErrors).toEqual([]);
});

test("known feed authors open their local profiles and preserve history", async ({
  page,
}, testInfo) => {
  const safety = collectSafetyViolations(page);
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/");
  const alice = page
    .getByTestId("local-feed-item")
    .filter({ hasText: "alice_pump" })
    .getByRole("link", { name: "alice_pump", exact: true });
  await expect(alice).toHaveAttribute(
    "href",
    "/profile/7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
  );
  await alice.focus();
  await expect(alice).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(
    /\/profile\/7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU$/,
  );
  await expect(
    page.getByRole("heading", { level: 1, name: "alice_pump" }),
  ).toBeVisible();
  await expect(page.locator(".profile-page")).toHaveAttribute(
    "data-profile-kind",
    "person",
  );
  await page.goBack();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByTestId("local-feed-item")).toHaveCount(3);
  const group = page
    .getByTestId("local-feed-item")
    .filter({ hasText: "chad_group" })
    .getByRole("link", { name: "chad_group", exact: true });
  await group.click();
  await expect(page).toHaveURL(
    /\/profile\/HN7cABqLq46Es1jh92dQQisAq662SmxELLLsHHe4YWrH$/,
  );
  await expect(page.locator(".profile-page")).toHaveAttribute(
    "data-profile-kind",
    "group",
  );
  await expect(
    page.getByRole("heading", { level: 1, name: "chad_group" }),
  ).toBeVisible();
  await page.goBack();
  for (const [width, height] of [
    [1280, 800],
    [375, 812],
  ] as const) {
    await page.setViewportSize({ width, height });
    await expect(group).toBeVisible();
    await group.focus();
    await expect(group).toBeFocused();
    expect(
      await page.evaluate(
        () =>
          document.documentElement.scrollWidth <=
          document.documentElement.clientWidth,
      ),
    ).toBe(true);
    await page.screenshot({
      path: testInfo.outputPath(`feed-author-${width}.png`),
      fullPage: true,
    });
  }
  expect(safety.requests).toEqual([]);
  expect(safety.consoleErrors).toEqual([]);
});

test("Following remains selectable without fabricated personalization", async ({
  page,
}) => {
  await page.goto("/");
  const forYou = page.getByRole("tab", { name: "For you" });
  const following = page.getByRole("tab", { name: "Following" });
  await expect(forYou).toHaveAttribute("aria-selected", "true");
  await expect(following).toHaveAttribute("aria-selected", "false");

  await following.click();
  await expect(page).toHaveURL(/\/?\?tab=following$/);
  await expect(following).toHaveAttribute("aria-selected", "true");
  await expect(page.getByTestId("following-unavailable")).toContainText(
    "No followed users or posts are invented here.",
  );
  await expect(page.getByTestId("local-feed-item")).toHaveCount(0);

  await page.goBack();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByTestId("local-feed-item")).toHaveCount(3);
  await page.goForward();
  await expect(page.getByTestId("following-unavailable")).toBeVisible();
  await page.reload();
  await expect(following).toHaveAttribute("aria-selected", "true");
});

test("feed tabs support roving keyboard navigation", async ({ page }) => {
  await page.goto("/");
  const forYou = page.getByRole("tab", { name: "For you" });
  const following = page.getByRole("tab", { name: "Following" });
  await forYou.focus();
  await page.keyboard.press("ArrowRight");
  await expect(page).toHaveURL(/tab=following/);
  await expect(following).toBeFocused();
  await expect(following).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("Home");
  await expect(page).toHaveURL(/\/$/);
  await expect(forYou).toBeFocused();
});

test("normal feed interaction stays local, read-only and error-free", async ({
  page,
}) => {
  const safety = collectSafetyViolations(page);
  await page.goto("/");
  await page.getByRole("tab", { name: "Following" }).click();
  await page.getByRole("link", { name: "Return to local examples" }).click();
  await expect(page.getByTestId("local-feed-item")).toHaveCount(3);
  await page.getByRole("link", { name: "Explore", exact: true }).click();
  await expect(
    page.getByRole("heading", { level: 1, name: "Explore" }),
  ).toBeVisible();
  await page.goto("/create");
  await expect(page.getByRole("form")).toBeVisible();

  expect(safety.requests).toEqual([]);
  expect(safety.consoleErrors).toEqual([]);
});

test("all required viewports keep the feed readable without overflow", async ({
  page,
}) => {
  for (const [width, height] of [
    [320, 640],
    [375, 812],
    [390, 844],
    [768, 1024],
    [1280, 800],
    [1440, 900],
  ] as const) {
    await page.setViewportSize({ width, height });
    await page.goto("/");
    await expect(page.getByRole("tab", { name: "For you" })).toBeVisible();
    await expect(page.getByTestId("local-feed-item").first()).toBeVisible();
    const dimensions = await page.evaluate(() => ({
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
      clippedPosts: Array.from(
        document.querySelectorAll("[data-testid=local-feed-item]"),
      ).filter((element) => element.scrollWidth > element.clientWidth).length,
    }));
    expect(dimensions.scrollWidth, `${width}px document`).toBeLessThanOrEqual(
      dimensions.clientWidth,
    );
    expect(dimensions.clippedPosts, `${width}px posts`).toBe(0);
    const firstTabBox = await page
      .getByRole("tab", { name: "For you" })
      .boundingBox();
    expect(firstTabBox?.height, `${width}px tab target`).toBeGreaterThanOrEqual(
      44,
    );
  }
});

test("excluded detail routes remain unavailable", async ({ page }) => {
  for (const path of ["/coin/example", "/pump-token"]) {
    const response = await page.goto(path);
    expect(response?.status(), path).toBe(404);
  }
});
