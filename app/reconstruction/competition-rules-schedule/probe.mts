import {
  test,
  expect,
} from "../../packages/frontend/node_modules/@playwright/test/index.mjs";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { startRulesDismissHttp } from "../../tests/fixtures/rules-dismiss-http.mjs";
import { startRulesDismissNext } from "../../tests/fixtures/rules-dismiss-next.mjs";
const phase = process.env.PUMP_SCHEDULE_PHASE ?? "fixed";
const output =
  process.env.PUMP_SCHEDULE_OUTPUT ??
  new URL("../../artifacts/rules-schedule/" + phase + "/", import.meta.url)
    .pathname;
let http: Awaited<ReturnType<typeof startRulesDismissHttp>>,
  next: Awaited<ReturnType<typeof startRulesDismissNext>>;
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
for (const width of [390, 1280])
  test(`actual Rules schedule columns at ${width}px`, async ({
    page,
    context,
  }) => {
    test.setTimeout(60000);
    await page.setViewportSize({ width, height: 844 });
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await context.route("**/*", async (route) => {
      const r = route.request(),
        u = new URL(r.url());
      if (u.origin !== next.baseURL || r.method() !== "GET") {
        errors.push(r.method() + " " + u.origin + u.pathname);
        await route.abort();
        return;
      }
      await route.continue();
    });
    const responsePromise = page.waitForResponse(
      (r) => r.url().includes("/api/leaderboard?") && r.status() === 200,
    );
    await page.goto(
      next.baseURL +
        "/leaderboard?category=competitions&competition=solana-autumn-arena",
    );
    const response = await responsePromise,
      body = await response.json();
    expect(body.ok).toBe(true);
    expect(body.data.kind).toBe("competition-detail");
    expect(body.data.competition.slug).toBe("solana-autumn-arena");
    expect(
      (await http.snapshot()).ledger.some(
        (r: any) =>
          r.keyMatched &&
          r.status === 200 &&
          r.path.startsWith("/v1/competitions/solana-autumn-arena?"),
      ),
    ).toBe(true);
    await page
      .getByRole("button", { name: "Schedule, scoring, eligibility and rules" })
      .click();
    const dialog = page.getByRole("dialog", { name: "Competition rules" });
    await expect(dialog).toBeVisible();
    await page.evaluate(() => document.fonts.ready);
    const schedule = dialog
      .locator("section")
      .filter({
        has: page.getByRole("heading", { name: "Schedule", exact: true }),
      })
      .locator("dl");
    const measured = await schedule.evaluate((dl) => {
      const box = (e: Element) => {
        const r = e.getBoundingClientRect();
        return {
          left: r.left,
          right: r.right,
          top: r.top,
          bottom: r.bottom,
          width: r.width,
          height: r.height,
        };
      };
      return {
        bounds: box(dl),
        clientWidth: dl.clientWidth,
        scrollWidth: dl.scrollWidth,
        rows: [...dl.children].map((row) => {
          const label = row.querySelector("dt")!,
            value = row.querySelector("dd")!,
            range = document.createRange();
          range.selectNodeContents(label);
          const labelRects = [...range.getClientRects()]
            .filter((r) => r.width > 0)
            .map((r) => ({
              left: r.left,
              right: r.right,
              top: r.top,
              bottom: r.bottom,
              width: r.width,
              height: r.height,
            }));
          range.selectNodeContents(value);
          const valueRects = [...range.getClientRects()]
            .filter((r) => r.width > 0)
            .map((r) => ({
              left: r.left,
              right: r.right,
              top: r.top,
              bottom: r.bottom,
              width: r.width,
              height: r.height,
            }));
          return {
            label: label.textContent,
            value: value.textContent,
            row: box(row),
            labelBounds: box(label),
            valueBounds: box(value),
            labelRects,
            valueRects,
            flex: getComputedStyle(value).flex,
          };
        }),
      };
    });
    const prize = dialog
      .locator("section")
      .filter({
        has: page.getByRole("heading", {
          name: "Prize breakdown",
          exact: true,
        }),
      });
    const prizeData = await prize.evaluate((section) => ({
      text: section.textContent,
      rows: [...section.querySelectorAll("dl>div")].map((row) => ({
        label: row.querySelector("dt")?.textContent,
        value: row.querySelector("dd")?.textContent,
        height: row.getBoundingClientRect().height,
      })),
    }));
    await mkdir(path.join(output, String(width)), { recursive: true });
    await writeFile(
      path.join(output, String(width), "observed.json"),
      JSON.stringify({ measured, prizeData, admitted: body, errors }, null, 2) +
        "\n",
    );
    await page.screenshot({
      path: path.join(output, String(width), "schedule.png"),
      fullPage: true,
    });
    expect(measured.rows.map((row) => row.label)).toEqual([
      "Registration",
      "Competition",
    ]);
    // Product assertion: the source's column allocation keeps each label word intact.
    for (const row of measured.rows) expect(row.labelRects).toHaveLength(1);
    expect(measured.scrollWidth).toBeLessThanOrEqual(measured.clientWidth + 1);
    for (const row of measured.rows) {
      expect(row.value?.length).toBeGreaterThan(0);
      for (const rect of row.valueRects) {
        expect(rect.left).toBeGreaterThanOrEqual(row.valueBounds.left - 0.5);
        expect(rect.right).toBeLessThanOrEqual(row.valueBounds.right + 0.5);
      }
    }
    expect(errors).toEqual([]);
    await dialog.getByRole("button", { name: "Close", exact: true }).click();
    await expect(dialog).not.toBeVisible();
  });
