import { expect, test } from "@playwright/test";
const origin = "http://127.0.0.1:3016";

test("hash-bound local Home renders the original standalone quote preview while preserving roots and excluding reposts", async ({
  page,
  context,
}, testInfo) => {
  const errors: string[] = [],
    forbidden: string[] = [];
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(m.text());
  });
  await context.route("**/*", (route) => {
    const request = route.request(),
      url = new URL(request.url());
    if (url.origin !== origin || !["GET", "HEAD"].includes(request.method())) {
      forbidden.push(`${request.method()} ${request.url()}`);
      return route.abort();
    }
    return route.continue();
  });
  await page.setViewportSize({ width: 1280, height: 800 });
  expect((await page.goto("/"))?.status()).toBe(200);
  await expect(
    page.getByText("Local example data — not live Pump activity", {
      exact: true,
    }),
  ).toBeVisible();
  const roots = page.locator('.feed-list > [data-testid="local-feed-item"]');
  await expect(roots).toHaveCount(3);
  await expect(roots.nth(0)).toContainText("chad_group");
  await expect(roots.nth(1)).toContainText("bob_degen");
  await expect(roots.nth(2)).toContainText("First post on synthetic pump!");
  await expect(
    roots.nth(2).getByText("Likes", { exact: true }).locator(".."),
  ).toContainText("5");
  await expect(page.getByText("Reply 1 to Alice", { exact: true })).toHaveCount(
    0,
  );
  await expect(page.getByText("Hidden post", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Deleted post", { exact: true })).toHaveCount(0);
  await expect(page.locator("main img,main iframe")).toHaveCount(0);
  const baseline = process.env.QUOTE_PREVIEW_EXPECT_BASELINE === "1";
  if (baseline) {
    await expect(page.getByTestId("local-feed-item")).toHaveCount(3);
    await expect(page.getByTestId("feed-quote-embed")).toHaveCount(0);
    await expect(
      page.getByText("Alice quoting her own post", { exact: true }),
    ).toHaveCount(0);
    await page.screenshot({
      path: testInfo.outputPath("quote-preview-before-1280.png"),
      fullPage: true,
    });
  } else {
    await expect(page.getByTestId("local-feed-item")).toHaveCount(6);
    const rows = page.getByRole("group", {
      name: "Recorded local quote",
      exact: true,
    });
    await expect(rows).toHaveCount(3);
    await expect(rows.nth(0)).toContainText("Alice quoting her own post");
    await expect(rows.nth(1)).toContainText("Another quote of Alice");
    await expect(rows.nth(2)).toContainText("Quoting Alice post 1");
    const embeds = page.getByTestId("feed-quote-embed");
    await expect(embeds).toHaveCount(3);
    for (const embed of await embeds.all()) {
      await expect(embed).toHaveJSProperty("tagName", "BLOCKQUOTE");
      await expect(embed).toContainText("alice_pump");
      await expect(embed).toContainText("First post on synthetic pump!");
      await expect(embed.locator("a,button,img,iframe")).toHaveCount(0);
    }
    await expect(
      page.getByText("Quoted local record", { exact: true }),
    ).toHaveCount(3);
    await expect(
      page.getByText("6 validated local posts from the", { exact: false }),
    ).toBeVisible();
    // Repost30 remains absent; it cannot become a seventh synthetic root.
    await expect(page.locator('[data-local-post-kind="repost"]')).toHaveCount(
      0,
    );
    for (const [width, height] of [
      [1280, 800],
      [375, 812],
    ] as const) {
      await page.setViewportSize({ width, height });
      expect(
        await page.evaluate(
          () =>
            document.documentElement.scrollWidth <=
            document.documentElement.clientWidth,
        ),
      ).toBe(true);
      expect(
        await embeds.evaluateAll((nodes) =>
          nodes.every((n) => n.scrollWidth <= n.clientWidth),
        ),
      ).toBe(true);
      await page.screenshot({
        path: testInfo.outputPath(`quote-preview-after-${width}.png`),
        fullPage: true,
      });
    }
  }
  // Existing root author still supports ordinary keyboard navigation. Quotes
  // have a source-faithful display-only author, with no invented target action.
  const alice = roots
    .nth(2)
    .getByRole("link", { name: "alice_pump", exact: true });
  await alice.focus();
  await expect(alice).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("heading", { level: 1, name: "alice_pump", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".profile-page")).toHaveAttribute(
    "data-profile-kind",
    "person",
  );
  await expect(page.getByTestId("feed-quote-embed")).toHaveCount(0);
  await page.goBack();
  await expect(page.getByTestId("local-feed-item")).toHaveCount(
    baseline ? 3 : 6,
  );
  expect(forbidden).toEqual([]);
  expect(errors).toEqual([]);
});
