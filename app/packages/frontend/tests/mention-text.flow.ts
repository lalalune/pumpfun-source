import { expect, test } from "@playwright/test";
const origin = "http://127.0.0.1:3016";
const id = "12345678-1234-1234-1234-123456789abc";

test("actual Home Feed read renders original standalone content and keyboard profile navigation", async ({
  page,
  context,
}, testInfo) => {
  const consoleErrors: string[] = [],
    forbidden: string[] = [],
    requests: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  await context.route("**/*", (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.origin !== origin || !["GET", "HEAD"].includes(request.method())) {
      forbidden.push(`${request.method()} ${request.url()}`);
      return route.abort();
    }
    requests.push(url.pathname);
    return route.continue();
  });
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/?tab=local-callouts&nativeView=ranked");
  const article = page.getByTestId("native-callout-card");
  await expect(article).toHaveCount(1);
  await expect(
    page.getByText("Synthetic local callout data", { exact: true }),
  ).toBeVisible();
  if (process.env.MENTION_TEXT_EXPECT_BASELINE === "1") {
    await expect(article).toContainText(`@[Alice](${id})`);
    await expect(
      article.getByRole("link", { name: "@Alice", exact: true }),
    ).toHaveCount(0);
    await expect(article.getByTestId("callout-greentext")).toHaveCount(0);
    await expect(article.getByTestId("callout-tweet-chip")).toHaveCount(0);
    await page.screenshot({
      path: testInfo.outputPath("mention-text-baseline.png"),
      fullPage: true,
    });
    expect(consoleErrors).toEqual([]);
    expect(forbidden).toEqual([]);
    const calls = await (
      await fetch("http://127.0.0.1:3001/__requests")
    ).json();
    expect(calls.requests.length).toBeGreaterThanOrEqual(1);
    expect(
      calls.requests.every(
        (request: string) =>
          request === "GET /services/frontend/home-feed?pageSize=3",
      ),
    ).toBe(true);
    await testInfo.attach("backend-requests", {
      body: JSON.stringify(calls, null, 2),
      contentType: "application/json",
    });
    return;
  }
  const mention = article.getByRole("link", { name: "@Alice", exact: true });
  await expect(mention).toHaveAttribute("href", `/profile/${id}`);
  await expect(article).not.toContainText(`@[Alice](${id})`);
  await expect(article.getByTestId("callout-greentext")).toContainText(
    "> Hello @Alice. See",
  );
  await expect(article.getByTestId("callout-greentext")).toContainText(
    "!! Literal",
  );
  await expect(article.getByTestId("callout-greentext")).toHaveCSS(
    "color",
    "rgb(74, 222, 128)",
  );
  const tweet = article.getByRole("link", { name: "@reporter", exact: true });
  await expect(tweet).toHaveAttribute(
    "href",
    "https://x.com/reporter/status/12345?local=1",
  );
  await expect(tweet).toHaveAttribute("target", "_blank");
  await expect(tweet).toHaveAttribute("rel", "noopener noreferrer");
  await expect(article.getByTestId("callout-tweet-chip")).toHaveCount(2);
  await expect(article).toContainText(
    "https://evilx.com/a/status/9 stays text.",
  );
  await expect(article.locator('a[href*="evilx"]')).toHaveCount(0);
  await expect(article).toContainText(
    "<script>window.mentionInjected=true</script>",
  );
  await expect(article.locator("script,img,iframe,video")).toHaveCount(0);
  expect(await page.evaluate(() => "mentionInjected" in window)).toBe(false);
  expect(requests.some((p) => p.startsWith(`/profile/${id}`))).toBe(false);
  for (let index = 0; index < 60; index++) {
    if (await mention.evaluate((node) => node === document.activeElement))
      break;
    await page.keyboard.press("Tab");
  }
  await expect(mention).toBeFocused();
  for (const [width, height] of [
    [1280, 800],
    [375, 812],
  ] as const) {
    await page.setViewportSize({ width, height });
    await expect(mention).toBeVisible();
    expect(
      await page.evaluate(
        () =>
          document.documentElement.scrollWidth <=
          document.documentElement.clientWidth,
      ),
    ).toBe(true);
    await page.screenshot({
      path: testInfo.outputPath(`mention-text-${width}.png`),
      fullPage: true,
    });
  }
  expect(consoleErrors).toEqual([]);
  await expect(mention).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(new RegExp(`/profile/${id}$`));
  // The input is a synthetic, unresolved identity. A navigable link does not
  // fabricate a profile or an authenticated viewer.
  await expect(
    page.getByRole("heading", { name: "Page not reconstructed", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".profile-page")).toHaveCount(0);
  await page.goBack();
  await expect(page.getByTestId("native-callout-card")).toHaveCount(1);
  await page.goto("/");
  await expect(
    page.getByText("First post on synthetic pump!", { exact: true }),
  ).toBeVisible();
  expect(forbidden).toEqual([]);
  const calls = (await (
    await fetch("http://127.0.0.1:3001/__requests")
  ).json()) as { requests: string[] };
  expect(
    calls.requests.every(
      (request) => request === "GET /services/frontend/home-feed?pageSize=3",
    ),
  ).toBe(true);
  expect(calls.requests.length).toBeGreaterThanOrEqual(1);
  await testInfo.attach("backend-requests", {
    body: JSON.stringify(calls, null, 2),
    contentType: "application/json",
  });
});
