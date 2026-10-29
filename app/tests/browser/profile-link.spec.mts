import {
  test,
  expect,
} from "../../packages/frontend/node_modules/@playwright/test/index.mjs";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { startProfileLinkHttp } from "../fixtures/profile-link-http.mjs";
import { startProfileLinkNext } from "../fixtures/profile-link-next.mjs";
const phase = process.env.PUMP_PROFILE_PHASE ?? "fixed";
const output =
  process.env.PUMP_PROFILE_OUTPUT ??
  new URL("../../artifacts/profile-link/" + phase + "/", import.meta.url)
    .pathname;
const wallet = "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU";
let http: Awaited<ReturnType<typeof startProfileLinkHttp>>;
let next: Awaited<ReturnType<typeof startProfileLinkNext>>;
test.beforeAll(async () => {
  test.setTimeout(90000);
  await mkdir(output, { recursive: true });
  http = await startProfileLinkHttp();
  try {
    next = await startProfileLinkNext({
      backendUrl: http.backendUrl,
      port: Number(process.env.PUMP_PROFILE_PORT ?? 3027),
      outputDir: output,
    });
  } catch (error) {
    await http.close();
    throw error;
  }
});
test.afterAll(async () => {
  if (http) {
    const snapshot = await http.command("snapshot");
    await writeFile(
      path.join(output, "handler-ledger.json"),
      JSON.stringify(snapshot, null, 2) + "\n",
    );
  }
  if (next)
    await writeFile(
      path.join(output, "next-exit.json"),
      JSON.stringify(await next.close()) + "\n",
    );
  if (http) await http.close();
});
for (const width of [390, 1280])
  test(`known local profile navigation at ${width}px`, async ({
    page,
    context,
  }, testInfo) => {
    test.setTimeout(60000);
    await page.setViewportSize({ width, height: 900 });
    const errors: string[] = [],
      requests: Array<{ url: string; method: string; status?: number }> = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await context.route("**/*", async (route) => {
      const request = route.request(),
        u = new URL(request.url());
      if (u.origin !== next.baseURL) {
        await route.abort();
        return;
      }
      if (request.method() !== "GET") {
        errors.push(
          "Unexpected browser write " + request.method() + " " + u.pathname,
        );
        await route.abort();
        return;
      }
      await route.continue();
    });
    page.on("response", (response) => {
      if (response.url().includes("/api/leaderboard"))
        requests.push({
          url: response.url(),
          method: response.request().method(),
          status: response.status(),
        });
    });
    const bodyPromise = page.waitForResponse(
      (r) => r.url().includes("/api/leaderboard?") && r.status() === 200,
    );
    await page.goto(
      next.baseURL + "/leaderboard?category=traders&period=daily&sort=combined",
    );
    const response = await bodyPromise,
      body = await response.json();
    expect(body.ok).toBe(true);
    expect(body.data.entries).toHaveLength(3);
    expect(body.data.entries[0]).toMatchObject({
      walletAddress: wallet,
      userId: "user-001",
      username: "alice_pump",
      pnlUsd: 100,
    });
    const snapshot = await http.command("snapshot");
    expect(
      snapshot.ledger.some(
        (r: any) =>
          r.keyMatched &&
          r.status === 200 &&
          r.method === "GET" &&
          r.path.startsWith("/v1/pnl-leaderboard?"),
      ),
    ).toBe(true);
    const rows = page
      .getByRole("list", { name: "Trader rankings" })
      .locator("li");
    await expect(rows).toHaveCount(3);
    await expect(rows.nth(0).locator(".ranking-metric strong")).toHaveText(
      "$100.00",
    );
    await expect(rows.nth(1)).toContainText("@alice_pump");
    await expect(rows.nth(1).getByRole("link")).toHaveCount(0); // Known wallet, mismatched user/name tuple.
    await expect(rows.nth(2).getByRole("link")).toHaveCount(0); // Unresolved public identity.
    await mkdir(path.join(output, String(width)), { recursive: true });
    await writeFile(
      path.join(output, String(width), "admitted-response.json"),
      JSON.stringify(body, null, 2) + "\n",
    );
    await page.screenshot({
      path: path.join(output, String(width), "rankings.png"),
      fullPage: true,
    });
    const link = rows
      .nth(0)
      .getByRole("link", {
        name: "View local example profile for @alice_pump",
      });
    // Same causal assertion on baseline and candidate, after real HTTP admission.
    await expect(link).toHaveAttribute("href", "/profile/" + wallet);
    expect(
      await page.evaluate(
        () => document.querySelectorAll('link[rel="prefetch"]').length,
      ),
    ).toBe(0);
    await link.focus();
    await expect(link).toBeFocused();
    await link.press("Enter");
    await expect(page).toHaveURL(next.baseURL + "/profile/" + wallet);
    await expect(page.getByLabel("Profile data source")).toContainText(
      "Local synthetic example — not a real Pump.fun user",
    );
    await expect(page.locator(".profile-page")).toContainText("alice_pump");
    await page.screenshot({
      path: path.join(output, String(width), "profile.png"),
      fullPage: true,
    });
    await page.goBack();
    await expect(page).toHaveURL(
      /\/leaderboard\?category=traders&period=daily&sort=combined$/,
    );
    const returned = page.getByRole("link", {
      name: "View local example profile for @alice_pump",
    });
    await expect(returned).toBeVisible();
    await returned.click();
    await expect(page).toHaveURL(next.baseURL + "/profile/" + wallet);
    expect(errors).toEqual([]);
    await writeFile(
      path.join(output, String(width), "browser-observed.json"),
      JSON.stringify(
        { errors, requests, actualProfileURL: page.url() },
        null,
        2,
      ) + "\n",
    );
  });
