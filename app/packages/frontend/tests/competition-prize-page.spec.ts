import { expect, test, type Page } from "@playwright/test";

// Synthetic read-only adapter envelopes. No production credential/backend claim.
const competition = {
  id: "web-prize-fixture",
  slug: "web-prize-fixture",
  kind: "person",
  title: "Synthetic web prize fixture",
  description: "Supplied web competition description",
  prizeCopy: "Supplied prize copy",
  prizes: [
    { rankFrom: 1, rankTo: 1, amount: "999999999999999999.99" },
    { rankFrom: 2, rankTo: 3, amount: "2 SOL" },
  ],
  minMembers: 0,
  maxMembers: 0,
  registrationOpensAt: null,
  registrationClosesAt: null,
  startsAt: null,
  endsAt: null,
  maxEntries: 100,
  entriesCount: 0,
  participants: 0,
  joinable: false,
  phase: "upcoming",
  isFinal: false,
};
const entries = [
  {
    entryId: "first",
    participantId: "fixture-first",
    kind: "person",
    rank: 1,
    pnlUsd: 1000,
    realizedPnlUsd: 600,
    unrealizedPnlUsd: 400,
    memberCount: 1,
    membersFresh: 1,
    struck: false,
    lastRefreshedAtMs: 1,
    walletAddress: "11111111111111111111111111111112",
    username: "FixtureFirst",
    isVerified: false,
    verifiedBadgeVisible: false,
  },
  {
    entryId: "second",
    participantId: "fixture-second",
    kind: "person",
    rank: 2,
    pnlUsd: 500,
    realizedPnlUsd: 300,
    unrealizedPnlUsd: 200,
    memberCount: 1,
    membersFresh: 1,
    struck: false,
    lastRefreshedAtMs: 1,
    walletAddress: "11111111111111111111111111111113",
    username: "FixtureSecond",
    isVerified: false,
    verifiedBadgeVisible: false,
  },
  {
    entryId: "third",
    participantId: "fixture-third",
    kind: "person",
    rank: 3,
    pnlUsd: 10,
    realizedPnlUsd: 5,
    unrealizedPnlUsd: 5,
    memberCount: 1,
    membersFresh: 1,
    struck: false,
    lastRefreshedAtMs: 1,
    walletAddress: "11111111111111111111111111111114",
    username: "FixtureThird",
    isVerified: false,
    verifiedBadgeVisible: false,
  },
  {
    entryId: "fourth",
    participantId: "fixture-fourth",
    kind: "person",
    rank: 4,
    pnlUsd: 0,
    realizedPnlUsd: 0,
    unrealizedPnlUsd: 0,
    memberCount: 1,
    membersFresh: 1,
    struck: false,
    lastRefreshedAtMs: 1,
    walletAddress: "11111111111111111111111111111115",
    username: "FixtureFourth",
    isVerified: false,
    verifiedBadgeVisible: false,
  },
];
async function install(
  page: Page,
  rows = entries,
  prizes = competition.prizes,
) {
  const unexpected: string[] = [],
    reads: string[] = [];
  const baseURL = test.info().project.use.baseURL;
  if (!baseURL) throw new Error("Explicit local browser baseURL required");
  const expectedOrigin = new URL(baseURL).origin;
  await page.route("**/*", async (route) => {
    const r = route.request(),
      url = new URL(r.url());
    if (
      url.origin !== expectedOrigin ||
      !["GET", "HEAD"].includes(r.method())
    ) {
      unexpected.push(r.method() + " " + r.url());
      await route.abort();
      return;
    }
    if (url.pathname === "/api/leaderboard") {
      reads.push(url.search);
      await route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          ok: true,
          source: {
            mode: "developer-api",
            label: "Pump developer API",
            fetchedAt: "2026-10-29T00:00:00Z",
          },
          data: {
            kind: "competition-detail",
            competition: {
              ...competition,
              prizes,
              phase: rows.length ? "live" : "upcoming",
              entriesCount: rows.length,
              participants: rows.length,
            },
            entries: rows,
            totalRanked: rows.length,
            builtAtMs: 1,
            isFinal: false,
          },
        }),
      });
      return;
    }
    await route.continue();
  });
  return { unexpected, reads };
}

for (const width of [390, 1280]) {
  test(`empty standings show supplied original prize tiers at ${width}px`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: 844 });
    const state = await install(page, []);
    await page.goto(
      "/leaderboard?category=competitions&competition=web-prize-fixture",
    );
    await expect(
      page.getByRole("heading", { name: competition.title, exact: true }),
    ).toBeVisible();
    await page.screenshot({
      path: info.outputPath("prizes-before-assert.png"),
      fullPage: true,
    });
    const region = page.getByRole("region", {
      name: "Prize breakdown",
      exact: true,
    });
    await expect(region).toBeVisible();
    await expect(region.getByTestId("cup-tier-1")).toContainText(
      "$999,999,999,999,999,999.99",
    );
    await expect(region.getByTestId("cup-tier-2")).toContainText("#2 – #3");
    await expect(region.getByTestId("cup-tier-2")).toContainText("2 SOL each");
    await expect(
      page.getByText("No ranked competition entry matches this local filter.", {
        exact: true,
      }),
    ).toHaveCount(0);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.screenshot({
      path: info.outputPath("empty-prizes-after.png"),
      fullPage: true,
    });
    await region.screenshot({ path: info.outputPath("empty-prize-widget.png") });
    expect(state.reads.length).toBeGreaterThanOrEqual(1);
    expect(state.unexpected).toEqual([]);
  });
  test(`ranked rows show source-selected raw prize badges and filtered results do not turn into prize fallback at ${width}px`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: 844 });
    const state = await install(page);
    await page.goto(
      "/leaderboard?category=competitions&competition=web-prize-fixture",
    );
    const rows = page
      .getByRole("list", { name: "Competition rankings" })
      .getByRole("listitem");
    await expect(rows).toHaveCount(4);
    await expect(rows.nth(0).getByTestId("cup-entry-prize")).toHaveText(
      competition.prizes[0].amount,
    );
    await expect(rows.nth(1).getByTestId("cup-entry-prize")).toHaveText(
      "2 SOL",
    );
    await expect(rows.nth(2).getByTestId("cup-entry-prize")).toHaveText(
      "2 SOL",
    );
    await expect(rows.nth(3).getByTestId("cup-entry-prize")).toHaveCount(0);
    await expect(page.getByTestId("competition-prize-tiers")).toHaveCount(0);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.screenshot({
      path: info.outputPath("ranked-prizes-after.png"),
      fullPage: true,
    });
    await page.getByRole("list", { name: "Competition rankings" }).screenshot({
      path: info.outputPath("ranked-prize-widget.png"),
    });
    const readsBeforeFilter = state.reads.length;
    await page.getByLabel("Filter loaded results").fill("FixtureFourth");
    await page.getByRole("button", { name: "Filter", exact: true }).click();
    await expect(rows).toHaveCount(1);
    await expect(page.getByTestId("cup-entry-prize")).toHaveCount(0);
    await page.getByLabel("Filter loaded results").fill("does-not-match");
    await page.getByRole("button", { name: "Filter", exact: true }).click();
    await expect(
      page.getByText("No ranked competition entry matches this local filter.", {
        exact: true,
      }),
    ).toBeVisible();
    await expect(page.getByTestId("competition-prize-tiers")).toHaveCount(0);
    await page.getByLabel("Filter loaded results").fill("");
    await page.getByRole("button", { name: "Filter", exact: true }).click();
    await expect(rows).toHaveCount(4);
    expect(state.reads).toHaveLength(readsBeforeFilter);
    expect(state.unexpected).toEqual([]);
  });
}
test("empty standings without supplied prizes retain the existing empty state", async ({
  page,
}) => {
  const state = await install(page, [], []);
  await page.goto(
    "/leaderboard?category=competitions&competition=web-prize-fixture",
  );
  await expect(
    page.getByText("No ranked competition entry matches this local filter.", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.getByTestId("competition-prize-tiers")).toHaveCount(0);
  expect(state.unexpected).toEqual([]);
});
