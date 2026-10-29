import { expect, test } from "@playwright/test";

const competition = {
  id: "synthetic-row-presentation",
  slug: "synthetic-row-presentation",
  kind: "person",
  title: "Synthetic row presentation",
  description: "Local admitted display facts, not an upstream ranking claim",
  prizeCopy: "",
  prizes: [],
  minMembers: 0,
  maxMembers: 0,
  registrationOpensAt: null,
  registrationClosesAt: null,
  startsAt: null,
  endsAt: null,
  maxEntries: 100,
  entriesCount: 4,
  participants: 3,
  joinable: false,
  phase: "upcoming",
  isFinal: false,
};
const entries = [
  { entryId: "unranked", rank: 0, pnlUsd: 0, username: "SyntheticUnranked" },
  { entryId: "zero", rank: 1, pnlUsd: 0, username: "SyntheticZero" },
  { entryId: "gain", rank: 2, pnlUsd: 12.34, username: "SyntheticGain" },
  { entryId: "loss", rank: 3, pnlUsd: -12.34, username: "SyntheticLoss" },
].map((value) => ({
  ...value,
  participantId: "synthetic-" + value.entryId,
  kind: "person",
  realizedPnlUsd: 0,
  unrealizedPnlUsd: 0,
  memberCount: 1,
  membersFresh: 1,
  struck: false,
  lastRefreshedAtMs: 0,
  walletAddress: null,
  isVerified: false,
  verifiedBadgeVisible: false,
}));

for (const width of [390, 1280]) {
  test(`actual web row preserves supplied unranked and PnL display decisions at ${width}px`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: 844 });
    const baseURL = test.info().project.use.baseURL;
    if (!baseURL) throw new Error("Explicit local baseURL required");
    const origin = new URL(baseURL).origin;
    const unexpected: string[] = [],
      reads: string[] = [];
    await page.route("**/*", async (route) => {
      const request = route.request(),
        url = new URL(request.url());
      if (
        url.origin !== origin ||
        !["GET", "HEAD"].includes(request.method())
      ) {
        unexpected.push(request.method() + " " + request.url());
        await route.abort();
      } else if (url.pathname === "/api/leaderboard") {
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
              competition,
              entries,
              totalRanked: 3,
              builtAtMs: 0,
              isFinal: false,
            },
          }),
        });
      } else await route.continue();
    });
    await page.goto(
      "/leaderboard?category=competitions&competition=synthetic-row-presentation",
    );
    await expect(
      page.getByRole("heading", { name: competition.title, exact: true }),
    ).toBeVisible();
    const list = page.getByRole("list", { name: "Competition rankings" });
    const rows = list.getByRole("listitem");
    await expect(rows).toHaveCount(4);
    await list.screenshot({ path: info.outputPath("rows-before-assert.png") });
    const metric = (i: number) =>
      rows.nth(i).locator(".ranking-metric > strong");
    await expect(metric(1)).toHaveText("$0.00");
    await expect(metric(1)).not.toHaveClass(/positive|negative/);
    await expect(metric(2)).toHaveText("+$12.34");
    await expect(metric(2)).toHaveClass("positive");
    await expect(metric(3)).toHaveText("-$12.34");
    await expect(metric(3)).toHaveClass("negative");
    await expect(
      rows.nth(0).getByLabel("Not ranked", { exact: true }),
    ).toHaveText("–");
    await expect(rows.nth(1)).toContainText("SyntheticZero");
    await expect(rows.nth(2)).toContainText("SyntheticGain");
    await expect(rows.nth(3)).toContainText("SyntheticLoss");
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await list.screenshot({ path: info.outputPath("rows-after.png") });
    expect(reads.length).toBeGreaterThanOrEqual(1);
    expect(unexpected).toEqual([]);
  });
}
