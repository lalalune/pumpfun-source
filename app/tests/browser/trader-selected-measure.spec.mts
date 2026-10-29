import {
  expect,
  test,
} from "../../packages/frontend/node_modules/@playwright/test/index.mjs";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { startTraderMeasureHttp } from "../fixtures/trader-measure-http.mjs";
import { startTraderMeasureNext } from "../fixtures/trader-measure-next.mjs";
let fixture: any, server: any;
const phase = process.env.PUMP_MEASURE_PHASE ?? "fixed";
const output =
  process.env.PUMP_MEASURE_OUTPUT_DIR ??
  new URL("../../artifacts/trader-selected-measure/" + phase + "/", import.meta.url).pathname;
test.beforeAll(async () => {
  test.setTimeout(90_000);
  fixture = await startTraderMeasureHttp();
  try {
    server = await startTraderMeasureNext({
      backendUrl: fixture.backendUrl,
      port: Number(process.env.PUMP_MEASURE_PORT ?? 3027),
      outputDir: output,
    });
  } catch (error) {
    await fixture.close();
    throw error;
  }
});
test.afterAll(async () => {
  await mkdir(output, { recursive: true });
  if (fixture) {
    await writeFile(
      path.join(output, "requests.json"),
      JSON.stringify(await fixture.command("snapshot"), null, 2) + "\n",
    );
  }
  if (server) {
    const result = await server.close();
    await writeFile(
      path.join(output, "server-exit.json"),
      JSON.stringify(result) + "\n",
    );
  }
  if (fixture) await fixture.close();
});
async function isolate(page: any) {
  const origin = server.baseURL,
    unexpected: string[] = [],
    apiCalls: string[] = [];
  await page.route("**/*", async (route: any) => {
    const request = route.request(),
      url = new URL(request.url());
    if (url.origin !== origin || !["GET", "HEAD"].includes(request.method())) {
      unexpected.push(request.method() + " " + request.url());
      await route.abort();
      return;
    }
    if (url.pathname === "/api/leaderboard") {
      apiCalls.push(url.search);
      expect(request.headers().authorization).toBeUndefined();
    }
    await route.continue();
  });
  return { unexpected, apiCalls };
}
const rowFor = (page: any, wallet: string) =>
  page
    .getByRole("list", { name: "Trader rankings" })
    .getByRole("listitem")
    .filter({ has: page.locator('small[title="' + wallet + '"]') });
for (const width of [390, 1280])
  test(`sort controls render their selected backend measure at ${width}px`, async ({
    page,
  }, info) => {
    await page.setViewportSize({ width, height: 844 });
    const state = await isolate(page);
    await page.goto("/leaderboard?category=traders&period=daily&sort=combined");
    await expect(
      rowFor(page, fixture.wallets[0]).locator(".ranking-metric > strong"),
    ).toHaveText("$100.00");
    const response = page.waitForResponse((r) => {
      const u = new URL(r.url());
      return (
        u.pathname === "/api/leaderboard" &&
        u.searchParams.get("sort") === "realized" &&
        r.status() === 200
      );
    });
    await page
      .getByLabel("Trader sort", { exact: true })
      .selectOption("realized");
    const actual = await (await response).json();
    await writeFile(
      info.outputPath("realized-response.json"),
      JSON.stringify(actual, null, 2) + "\n",
    );
    expect(actual.data.kind).toBe("traders");
    expect(
      actual.data.entries.find(
        (row: any) => row.walletAddress === fixture.wallets[0],
      ).realizedPnlUsd,
    ).toBe(-20);
    expect(
      actual.data.entries.find(
        (row: any) => row.walletAddress === fixture.wallets[0],
      ).pnlUsd,
    ).toBe(100);
    const observed = (await fixture.command("snapshot")).ledger;
    expect(
      observed.some(
        (row: any) =>
          row.status === 200 &&
          row.keyMatched &&
          new URL(row.path, fixture.backendUrl).searchParams.get("sort") ===
            "realized",
      ),
    ).toBe(true);
    await expect(
      page
        .getByRole("list", { name: "Trader rankings" })
        .getByRole("listitem")
        .first(),
    ).toContainText("111111…11113");
    const alpha = rowFor(page, fixture.wallets[0]),
      beta = rowFor(page, fixture.wallets[1]);
    await page
      .getByRole("list", { name: "Trader rankings" })
      .screenshot({ path: info.outputPath("realized-before-assert.png") });
    await expect(alpha.locator(".ranking-metric > strong")).toHaveText(
      "-$20.00",
    );
    await expect(alpha.locator(".ranking-metric > strong")).toHaveClass(
      "negative",
    );
    await expect(beta.locator(".ranking-metric > strong")).toHaveText("$40.00");
    await expect(alpha.locator(".ranking-metric > small")).toHaveText(
      "Realized PnL",
    );
    await page
      .getByRole("list", { name: "Trader rankings" })
      .screenshot({ path: info.outputPath("realized-after.png") });
    await page
      .getByLabel("Trader sort", { exact: true })
      .selectOption("unrealized");
    await expect(alpha.locator(".ranking-metric > strong")).toHaveText(
      "$120.00",
    );
    await expect(beta.locator(".ranking-metric > strong")).toHaveText("$10.00");
    await expect(alpha.locator(".ranking-metric > small")).toHaveText(
      "Unrealized PnL",
    );
    await expect(alpha.locator(".ranking-metric > strong")).toHaveClass(
      "positive",
    );
    await page
      .getByLabel("Trader sort", { exact: true })
      .selectOption("combined");
    await expect(alpha.locator(".ranking-metric > strong")).toHaveText(
      "$100.00",
    );
    await expect(alpha.locator(".ranking-metric > small")).toHaveText(
      "10% combined PnL",
    );
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect(state.unexpected).toEqual([]);
    expect(
      state.apiCalls.some(
        (s) => new URLSearchParams(s).get("sort") === "realized",
      ),
    ).toBe(true);
    expect(await page.content()).not.toContain(`pf_live_${"A".repeat(49)}`);
  });
test("real upstream stop produces error without stale rows and Retry restores selected measure", async ({
  page,
}, info) => {
  const state = await isolate(page);
  await page.goto("/leaderboard?category=traders&period=daily&sort=realized");
  await expect(
    rowFor(page, fixture.wallets[0]).locator(".ranking-metric > strong"),
  ).toHaveText("-$20.00");
  await fixture.command("stop-backend");
  await page
    .getByLabel("Trader period", { exact: true })
    .selectOption("weekly");
  await expect(page.getByTestId("leaderboard-error")).toBeVisible();
  await expect(page.getByRole("list", { name: "Trader rankings" })).toHaveCount(
    0,
  );
  await page.screenshot({
    path: info.outputPath("upstream-error.png"),
    fullPage: true,
  });
  await fixture.command("start-backend");
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await expect(
    rowFor(page, fixture.wallets[0]).locator(".ranking-metric > strong"),
  ).toHaveText("-$20.00");
  await expect(page.getByLabel("Trader sort", { exact: true })).toHaveValue(
    "realized",
  );
  await expect(page.getByLabel("Trader period", { exact: true })).toHaveValue(
    "weekly",
  );
  await page
    .getByRole("list", { name: "Trader rankings" })
    .screenshot({ path: info.outputPath("retry-after.png") });
  expect(state.unexpected).toEqual([]);
});
