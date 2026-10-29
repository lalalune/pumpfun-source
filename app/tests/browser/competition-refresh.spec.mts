import {
  test,
  expect,
} from "../../packages/frontend/node_modules/@playwright/test/index.mjs";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { startCompetitionRefreshHttp } from "../fixtures/competition-refresh-http.mjs";
import { startCompetitionRefreshNext } from "../fixtures/competition-refresh-next.mjs";

const output =
  process.env.PUMP_REFRESH_OUTPUT_DIR ??
  new URL(
    "../../artifacts/competition-refresh/" +
      (process.env.PUMP_REFRESH_PHASE ?? "fixed") +
      "/",
    import.meta.url,
  ).pathname;
let fixture: any, server: any;
test.beforeAll(async () => {
  test.setTimeout(90_000);
  fixture = await startCompetitionRefreshHttp();
  try {
    server = await startCompetitionRefreshNext({
      backendUrl: fixture.backendUrl,
      port: Number(process.env.PUMP_REFRESH_PORT ?? 3027),
      outputDir: output,
    });
  } catch (error) {
    await fixture.close();
    throw error;
  }
});
test.beforeEach(async () => {
  await fixture.command("reset");
});
test.afterAll(async () => {
  await mkdir(output, { recursive: true });
  if (fixture)
    await writeFile(
      path.join(output, "requests.json"),
      JSON.stringify(await fixture.command("snapshot"), null, 2) + "\n",
    );
  if (server)
    await writeFile(
      path.join(output, "server-exit.json"),
      JSON.stringify(await server.close()) + "\n",
    );
  if (fixture) await fixture.close();
});
async function observe(page: any, info: any) {
  const unexpected: string[] = [],
    responses: any[] = [],
    pending: Promise<unknown>[] = [];
  await page.route("**/*", async (route: any) => {
    const request = route.request(),
      url = new URL(request.url());
    if (
      url.origin !== server.baseURL ||
      !["GET", "HEAD"].includes(request.method())
    ) {
      unexpected.push(request.method() + " " + request.url());
      await route.abort();
      return;
    }
    if (url.pathname === "/api/leaderboard")
      expect(request.headers().authorization).toBeUndefined();
    await route.continue();
  });
  page.on("response", (response: any) => {
    if (new URL(response.url()).pathname === "/api/leaderboard") {
      pending.push(
        response
          .json()
          .then((body: any) =>
            responses.push({
              atMs: Date.now(),
              url: response.url(),
              status: response.status(),
              body,
            }),
          )
          .catch((error: Error) =>
            responses.push({
              atMs: Date.now(),
              status: response.status(),
              readError: error.message,
            }),
          ),
      );
    }
  });
  const startedAtMs = Date.now();
  return async () => {
    await Promise.allSettled(pending);
    await writeFile(
      info.outputPath("observed.json"),
      JSON.stringify(
        {
          realClock: true,
          startedAtMs,
          finishedAtMs: Date.now(),
          unexpected,
          responses,
          native: await fixture.command("snapshot"),
        },
        null,
        2,
      ) + "\n",
    );
    expect(unexpected).toEqual([]);
    expect(await page.content()).not.toContain(`pf_live_${"A".repeat(49)}`);
  };
}
async function foreground(page: any) {
  await page.bringToFront();
  await expect
    .poll(() =>
      page.evaluate(
        () => document.visibilityState === "visible" && document.hasFocus(),
      ),
    )
    .toBe(true);
}

test("real-clock detail rereads supplied data after15seconds at1280px", async ({
  page,
}, info) => {
  await page.setViewportSize({ width: 1280, height: 844 });
  const finish = await observe(page, info);
  try {
    await page.goto(
      "/leaderboard?category=competitions&competition=" + fixture.slug,
    );
    await foreground(page);
    const amount = page
      .getByRole("list", { name: "Competition rankings" })
      .locator(".ranking-metric > strong");
    await expect(amount).toHaveText("$100.00");
    await fixture.command("advance");
    const actual = await (
      await fetch(
        fixture.adapterUrl +
          "/api/leaderboard?category=competitions&id=" +
          fixture.slug,
      )
    ).json();
    expect(actual.ok).toBe(true);
    expect(actual.data.entries[0].pnlUsd).toBe(200);
    await writeFile(
      info.outputPath("changed-backend-response.json"),
      JSON.stringify(actual, null, 2) + "\n",
    );
    await page.screenshot({
      path: info.outputPath("before-refresh.png"),
      fullPage: true,
    });
    await expect(amount).toHaveText("$200.00", { timeout: 22_000 });
    await page.screenshot({
      path: info.outputPath("after-refresh.png"),
      fullPage: true,
    });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  } finally {
    await finish();
  }
});

test("real-clock list rereads supplied data after60seconds at390px", async ({
  page,
}, info) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const finish = await observe(page, info);
  try {
    await page.goto("/leaderboard?category=competitions&status=live");
    await foreground(page);
    const title = page
      .getByRole("list", { name: "Competitions", exact: true })
      .getByRole("heading", { level: 2 });
    await expect(title).toHaveText("Synthetic read snapshot 1");
    await fixture.command("advance");
    const actual = await (
      await fetch(
        fixture.adapterUrl +
          "/api/leaderboard?category=competitions&status=live",
      )
    ).json();
    expect(actual.ok).toBe(true);
    expect(actual.data.live[0].title).toBe("Synthetic read snapshot 2");
    await writeFile(
      info.outputPath("changed-backend-response.json"),
      JSON.stringify(actual, null, 2) + "\n",
    );
    await page.screenshot({
      path: info.outputPath("before-refresh.png"),
      fullPage: true,
    });
    await expect(title).toHaveText("Synthetic read snapshot 2", {
      timeout: 68_000,
    });
    await page.screenshot({
      path: info.outputPath("after-refresh.png"),
      fullPage: true,
    });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  } finally {
    await finish();
  }
});

test("actual foreground pause, error/Retry and unmount retain request ownership", async ({
  page,
  context,
}, info) => {
  const finish = await observe(page, info);
  // Playwright 1.64.1 enables CDP focus emulation for every main frame. Disable
  // that driver override so real tab switching reaches the unchanged DOM API.
  const focusSession = await context.newCDPSession(page);
  await focusSession.send("Emulation.setFocusEmulationEnabled", {
    enabled: false,
  });
  const focusStates: any[] = [];
  const recordFocus = async (label: string) =>
    focusStates.push({
      label,
      atMs: Date.now(),
      state: await page.evaluate(() => ({
        focused: document.hasFocus(),
        visibility: document.visibilityState,
      })),
      native: await fixture.command("snapshot"),
    });
  try {
    await page.goto(
      "/leaderboard?category=competitions&competition=" + fixture.slug,
    );
    await foreground(page);
    const amount = page
      .getByRole("list", { name: "Competition rankings" })
      .locator(".ranking-metric > strong");
    await expect(amount).toHaveText("$100.00");
    const before = (await fixture.command("snapshot")).ledger.length;
    const other = await context.newPage();
    const otherFocusSession = await context.newCDPSession(other);
    await otherFocusSession.send("Emulation.setFocusEmulationEnabled", {
      enabled: false,
    });
    await other.bringToFront();
    await expect
      .poll(() => page.evaluate(() => document.hasFocus()))
      .toBe(false);
    await recordFocus("other tab foreground; real source document blurred");
    await fixture.command("advance");
    await page.waitForTimeout(17_000); // Real elapsed time; no virtual clock or timer shim.
    expect((await fixture.command("snapshot")).ledger.length).toBe(before);
    await recordFocus("17 real seconds blurred; no recurring read");
    await expect(amount).toHaveText("$100.00");
    await other.close();
    await foreground(page);
    await recordFocus("source tab foreground again");
    await expect(amount).toHaveText("$200.00", { timeout: 22_000 });
    await fixture.command("stop-backend");
    await expect(page.getByTestId("leaderboard-error")).toBeVisible({
      timeout: 22_000,
    });
    await expect(
      page.getByRole("list", { name: "Competition rankings" }),
    ).toHaveCount(0);
    await page.screenshot({
      path: info.outputPath("upstream-error.png"),
      fullPage: true,
    });
    await fixture.command("start-backend");
    await page.getByRole("button", { name: "Retry", exact: true }).click();
    await expect(amount).toHaveText("$200.00");
    await page.goto("/docs/fees");
    await expect(
      page.getByRole("heading", { name: /Fees/i, level: 1 }),
    ).toBeVisible();
    const afterUnmount = (await fixture.command("snapshot")).ledger.length;
    await page.waitForTimeout(17_000);
    expect((await fixture.command("snapshot")).ledger.length).toBe(
      afterUnmount,
    );
  } finally {
    await writeFile(
      info.outputPath("focus-states.json"),
      JSON.stringify(focusStates, null, 2) + "\n",
    );
    await focusSession.detach();
    await finish();
  }
});
