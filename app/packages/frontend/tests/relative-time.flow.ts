import { expect, test } from "@playwright/test";
const origin = "http://127.0.0.1:3016";
test("actual feed and anonymous server-time read correct clock drift, tick and share one sampler", async ({
  page,
  context,
  request,
}, info) => {
  const baseline = process.env.RELATIVE_TIME_EXPECT_BASELINE === "1";
  const errors: string[] = [],
    violations: string[] = [],
    clockReads: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  let release!: () => void, seen!: () => void;
  const held = new Promise<void>((resolve) => {
      release = resolve;
    }),
    requested = new Promise<void>((resolve) => {
      seen = resolve;
    });
  await context.route("**/*", async (route) => {
    const r = route.request(),
      u = new URL(r.url());
    if (u.origin !== origin || !["GET", "HEAD"].includes(r.method())) {
      violations.push(`${r.method()} ${r.url()}`);
      await route.abort();
      return;
    }
    if (u.pathname === "/api/server-time") {
      clockReads.push(`${r.method()} ${u.pathname}`);
      seen();
      await held;
    }
    await route.continue();
  });
  const browserNow = Date.now() + 120000;
  await page.clock.setFixedTime(new Date(browserNow));
  await page.goto("/?tab=local-callouts&nativeView=ranked");
  const card = page.getByTestId("native-callout-card"),
    time = card.locator("time");
  await expect(card).toHaveCount(1);
  const backend = (await (
    await fetch("http://127.0.0.1:3001/__requests")
  ).json()) as { requests: string[]; timestamp: string };
  await expect(time).toHaveAttribute("datetime", backend.timestamp);
  if (baseline) {
    await expect(time).not.toContainText("ago");
    await expect(time).toContainText(
      String(new Date(backend.timestamp).getUTCFullYear()),
    );
    expect(clockReads).toEqual([]);
    expect(violations).toEqual([]);
    expect(errors).toEqual([]);
    const response = await request.get(`${origin}/api/server-time`);
    expect(response.status()).toBe(404);
    await page.screenshot({
      path: info.outputPath("relative-time-baseline.png"),
      fullPage: true,
    });
    release();
    return;
  }
  await requested;
  await expect(time).toHaveText(/^\d+(s|m) ago$/);
  const displaySeconds = (text: string) => {
    const match = /^(\d+)(s|m) ago$/.exec(text);
    expect(match).not.toBeNull();
    return Number(match![1]) * (match![2] === "m" ? 60 : 1);
  };
  expect(await page.evaluate(() => Date.now())).toBe(browserNow);
  console.log(
    "clock-observation-before-transition",
    JSON.stringify({
      browserNow: await page.evaluate(() => Date.now()),
      datetime: await time.getAttribute("datetime"),
      fixtureTimestamp: backend.timestamp,
      text: await time.textContent(),
      clockReads,
    }),
  );
  // suppressHydrationWarning can retain the SSR text when the initial client
  // virtual text is unchanged by mounting. Force one genuine label transition
  // while held, then restore the initial Date so sampling keeps its midpoint.
  await page.clock.setFixedTime(new Date(browserNow + 60000));
  await expect
    .poll(async () => displaySeconds((await time.textContent())!), {
      timeout: 2000,
    })
    .toBeGreaterThanOrEqual(180);
  console.log(
    "clock-observation-after-transition",
    JSON.stringify({
      browserNow: await page.evaluate(() => Date.now()),
      text: await time.textContent(),
      clockReads,
    }),
  );
  await page.clock.setFixedTime(new Date(browserNow));
  const drifted = displaySeconds((await time.textContent())!);
  const responsePromise = page.waitForResponse(
    (response) => new URL(response.url()).pathname === "/api/server-time",
  );
  release();
  const response = await responsePromise;
  expect(response.status()).toBe(200);
  expect(response.headers()["cache-control"]).toBe("no-store");
  const sample = (await response.json()) as { nowMs: number };
  expect(Number.isFinite(sample.nowMs)).toBe(true);
  expect(Math.abs(sample.nowMs - Date.now())).toBeLessThan(5000);
  await expect
    .poll(async () => displaySeconds((await time.textContent())!))
    .toBeLessThan(drifted - 60);
  const correctedText = (await time.textContent())!;
  const corrected = displaySeconds(correctedText);
  const actualAge = (sample.nowMs - Date.parse(backend.timestamp)) / 1000;
  expect(corrected).toBeGreaterThanOrEqual(Math.max(1, actualAge - 60));
  expect(corrected).toBeLessThanOrEqual(Math.max(1, actualAge + 1));
  await expect(time).toHaveAttribute("title", /.+/);
  await page.clock.setFixedTime(new Date(browserNow + 60000));
  await expect(time).not.toHaveText(correctedText);
  expect(clockReads).toEqual(["GET /api/server-time"]);
  for (const [width, height] of [
    [1280, 800],
    [375, 812],
  ] as const) {
    await page.setViewportSize({ width, height });
    await expect(time).toBeVisible();
    expect(
      await page.evaluate(
        () =>
          document.documentElement.scrollWidth <=
          document.documentElement.clientWidth,
      ),
    ).toBe(true);
    await page.screenshot({
      path: info.outputPath(`relative-time-${width}.png`),
      fullPage: true,
    });
  }
  await page.getByRole("tab", { name: "Following", exact: true }).click();
  await expect(page.getByTestId("following-unavailable")).toBeVisible();
  await page.getByRole("link", { name: "Return to local examples" }).click();
  await expect(page.getByTestId("local-feed-item")).toHaveCount(3);
  for (const t of await page
    .getByTestId("local-feed-item")
    .locator("time")
    .all()) {
    await expect(t).toHaveText(/ago$/);
    await expect(t).toHaveAttribute("title", /.+/);
  }
  expect(clockReads).toEqual(["GET /api/server-time"]);
  expect(violations).toEqual([]);
  expect(errors).toEqual([]);
  const again = await request.get(`${origin}/api/server-time`);
  expect(again.status()).toBe(200);
  expect(again.headers()["cache-control"]).toBe("no-store");
  expect((await again.json()).nowMs).toBeGreaterThanOrEqual(sample.nowMs);
  expect((await request.post(`${origin}/api/server-time`)).status()).toBe(405);
  expect(backend.requests).toEqual([
    "GET /services/frontend/home-feed?pageSize=3",
  ]);
  await info.attach("clock-read-observation", {
    body: JSON.stringify(
      { browserRequests: clockReads, backend, firstSample: sample },
      null,
      2,
    ),
    contentType: "application/json",
  });
});
