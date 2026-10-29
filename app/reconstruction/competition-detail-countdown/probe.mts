import {
  test,
  expect,
} from "../../packages/frontend/node_modules/@playwright/test/index.mjs";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { startRulesDismissHttp } from "../../tests/fixtures/rules-dismiss-http.mjs";
import { startRulesDismissNext } from "../../tests/fixtures/rules-dismiss-next.mjs";

const phase = process.env.PUMP_DETAIL_COUNTDOWN_PHASE ?? "fixed";
const output =
  process.env.PUMP_DETAIL_COUNTDOWN_OUTPUT ??
  new URL("../../artifacts/detail-countdown/" + phase + "/", import.meta.url)
    .pathname;
let http: Awaited<ReturnType<typeof startRulesDismissHttp>>;
let next: Awaited<ReturnType<typeof startRulesDismissNext>>;

test.beforeAll(async () => {
  test.setTimeout(90000);
  await mkdir(output, { recursive: true });
  http = await startRulesDismissHttp();
  try {
    next = await startRulesDismissNext({
      backendUrl: http.backendUrl,
      port: Number(process.env.PUMP_RULES_PORT ?? 3027),
      outputDir: output,
    });
  } catch (error) {
    await http.close();
    throw error;
  }
});
test.afterAll(async () => {
  if (http)
    await writeFile(
      path.join(output, "handler-ledger.json"),
      JSON.stringify(await http.snapshot(), null, 2) + "\n",
    );
  if (next)
    await writeFile(
      path.join(output, "next-exit.json"),
      JSON.stringify(await next.close()) + "\n",
    );
  if (http) await http.close();
});

for (const width of [390, 1280]) {
  test(`selected competition retains its countdown at ${width}px`, async ({
    page,
    context,
  }) => {
    test.setTimeout(60000);
    await page.setViewportSize({ width, height: 844 });
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await context.route("**/*", async (route) => {
      const request = route.request(),
        url = new URL(request.url());
      if (url.origin !== next.baseURL || request.method() !== "GET") {
        errors.push(request.method() + " " + url.origin + url.pathname);
        await route.abort();
      } else await route.continue();
    });
    const listResponse = page.waitForResponse(
      (r) => r.url().includes("/api/leaderboard?") && r.status() === 200,
    );
    await page.goto(
      next.baseURL + "/leaderboard?category=competitions&status=upcoming",
    );
    const list = await (await listResponse).json();
    expect(list.ok).toBe(true);
    expect(list.data.kind).toBe("competitions");
    const supplied = list.data.upcoming.find(
      (c: any) => c.slug === "solana-autumn-arena",
    );
    expect(supplied.phase).toBe("upcoming");
    expect(Date.parse(supplied.startsAt)).toBeGreaterThan(Date.now() + 60000);
    const card = page.locator(".competition-card").filter({
      has: page.getByRole("heading", { name: supplied.title, exact: true }),
    });
    await expect(card.getByTestId("cup-countdown")).toBeVisible();
    const detailResponse = page.waitForResponse(
      (r) =>
        r.url().includes("/api/leaderboard?") &&
        r.url().includes("id=solana-autumn-arena") &&
        r.status() === 200,
    );
    await card.getByRole("link", { name: "View ranked entries" }).click();
    const detail = await (await detailResponse).json();
    expect(detail.ok).toBe(true);
    expect(detail.data.kind).toBe("competition-detail");
    expect(detail.data.competition).toEqual(supplied);
    const heading = page.locator(".competition-detail-heading");
    await expect(
      heading.getByRole("heading", { name: supplied.title, exact: true }),
    ).toBeVisible();
    expect(
      (await http.snapshot()).ledger.some(
        (entry: any) =>
          entry.keyMatched &&
          entry.status === 200 &&
          entry.path.startsWith("/v1/competitions/solana-autumn-arena?"),
      ),
    ).toBe(true);
    const directory = path.join(output, String(width));
    await mkdir(directory, { recursive: true });
    const admission = { width, list: list.data, detail: detail.data };
    await writeFile(
      path.join(directory, "admission.json"),
      JSON.stringify(admission, null, 2) + "\n",
    );
    await page.screenshot({
      path: path.join(directory, "selected.png"),
      fullPage: true,
    });

    // The unchanged baseline reaches this assertion after actual native admission.
    const countdown = heading.getByTestId("cup-countdown");
    await expect(countdown).toBeVisible();
    await expect(countdown).toContainText("Starts in");
    await expect(page.getByTestId("cup-countdown")).toHaveCount(1);
    const observe = () =>
      countdown.evaluate((element) => {
        const boxes = [...element.querySelectorAll(":scope > div > div")];
        const values = boxes.map((box) =>
          Number(box.querySelector("span")?.textContent),
        );
        const labels = boxes.map(
          (box) => box.querySelectorAll("span")[1]?.textContent,
        );
        const rect = element.getBoundingClientRect();
        return {
          now: Date.now(),
          values,
          labels,
          totalSeconds:
            values[0] * 86400 + values[1] * 3600 + values[2] * 60 + values[3],
          width: rect.width,
          clientWidth: element.clientWidth,
          scrollWidth: element.scrollWidth,
        };
      });
    const beforeTick = await observe();
    expect(beforeTick.labels).toEqual(["Days", "Hours", "Minutes", "Seconds"]);
    expect(beforeTick.totalSeconds).toBeGreaterThan(0);
    expect(
      Math.abs(
        beforeTick.totalSeconds -
          Math.floor((Date.parse(supplied.startsAt) - beforeTick.now) / 1000),
      ),
    ).toBeLessThanOrEqual(2);
    await expect
      .poll(async () => (await observe()).totalSeconds, { timeout: 5000 })
      .toBeLessThan(beforeTick.totalSeconds);
    const afterTick = await observe();
    expect(afterTick.clientWidth).toBeGreaterThan(0);
    expect(afterTick.scrollWidth).toBeLessThanOrEqual(
      afterTick.clientWidth + 1,
    );
    await page.screenshot({
      path: path.join(directory, "countdown.png"),
      fullPage: true,
    });
    await heading.getByRole("button", { name: "Back to competitions" }).click();
    await expect(card.getByTestId("cup-countdown")).toBeVisible();
    await expect(page.locator(".competition-detail-heading")).toHaveCount(0);
    await expect(page.getByTestId("cup-countdown")).toHaveCount(1);
    await page.goto(next.baseURL + "/docs/fees");
    await expect(page.getByTestId("cup-countdown")).toHaveCount(0);
    expect(errors).toEqual([]);
    await writeFile(
      path.join(directory, "observed.json"),
      JSON.stringify(
        {
          ...admission,
          beforeTick,
          afterTick,
          errors,
          navigation:
            "Detail → existing list → fees: one visible countdown, then none. No timer-count or universal cleanup claim.",
        },
        null,
        2,
      ) + "\n",
    );
  });
}
