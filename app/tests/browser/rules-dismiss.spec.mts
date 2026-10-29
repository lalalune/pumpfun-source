import {
  test,
  expect,
} from "../../packages/frontend/node_modules/@playwright/test/index.mjs";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { startRulesDismissHttp } from "../fixtures/rules-dismiss-http.mjs";
import { startRulesDismissNext } from "../fixtures/rules-dismiss-next.mjs";
const phase = process.env.PUMP_RULES_PHASE ?? "fixed";
const output =
  process.env.PUMP_RULES_OUTPUT ??
  new URL("../../artifacts/rules-dismiss/" + phase + "/", import.meta.url)
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
  test(`actual competition Rules light dismissal at ${width}px`, async ({
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
    const ledger = await http.snapshot();
    expect(
      ledger.ledger.some(
        (r: any) =>
          r.keyMatched &&
          r.status === 200 &&
          r.method === "GET" &&
          r.path.startsWith("/v1/competitions/solana-autumn-arena?"),
      ),
    ).toBe(true);
    const launcher = page.getByRole("button", {
        name: "Schedule, scoring, eligibility and rules",
      }),
      dialog = page.getByRole("dialog", { name: "Competition rules" });
    await expect(launcher).toBeEnabled();
    await launcher.focus();
    await launcher.press("Enter");
    await expect(dialog).toBeVisible();
    const close = dialog.getByRole("button", { name: "Close", exact: true });
    await expect(close).toBeFocused();
    await expect(dialog).toContainText("Solana Autumn Arena");
    const before = await page.evaluate(() => ({
      scrollY: window.scrollY,
      overflow: document.body.style.overflow,
    }));
    const box = await dialog.boundingBox();
    if (!box) throw Error("No native Rules dialog box");
    expect(box.x).toBeGreaterThan(2);
    expect(box.y).toBeGreaterThan(2);
    // A press starting inside and released on the backdrop must remain inside-owned.
    await page.mouse.move(box.x + box.width / 2, box.y + 20);
    await page.mouse.down();
    await page.mouse.move(2, 2);
    await page.mouse.up();
    await expect(dialog).toBeVisible();
    await page.mouse.click(2, 2, { button: "right" });
    await expect(dialog).toBeVisible();
    await page.mouse.move(2, 2);
    await page.mouse.wheel(0, 400);
    expect(await page.evaluate(() => window.scrollY)).toBe(before.scrollY);
    const readsBefore = (await http.snapshot()).ledger.filter((r: any) =>
      r.path.startsWith("/v1/competitions/"),
    ).length;
    await mkdir(path.join(output, String(width)), { recursive: true });
    await writeFile(
      path.join(output, String(width), "admitted-response.json"),
      JSON.stringify(body, null, 2) + "\n",
    );
    await page.screenshot({
      path: path.join(output, String(width), "before-outside.png"),
      fullPage: true,
    });
    await page.mouse.click(2, 2);
    // Same actual missing behavior assertion before and after the caller-only fix.
    await expect(dialog).not.toBeVisible();
    await expect(launcher).toBeFocused();
    expect(await page.evaluate(() => document.body.style.overflow)).toBe("");
    expect(await page.evaluate(() => window.scrollY)).toBe(before.scrollY);
    await page.screenshot({
      path: path.join(output, String(width), "after-outside.png"),
      fullPage: true,
    });
    await launcher.press("Enter");
    await expect(dialog).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(dialog).not.toBeVisible();
    await expect(launcher).toBeFocused();
    await launcher.click();
    await expect(dialog).toBeVisible();
    await close.click();
    await expect(dialog).not.toBeVisible();
    await expect(launcher).toBeFocused();
    expect(
      (await http.snapshot()).ledger.filter((r: any) =>
        r.path.startsWith("/v1/competitions/"),
      ).length,
    ).toBe(readsBefore);
    expect(errors).toEqual([]);
    await writeFile(
      path.join(output, String(width), "observed.json"),
      JSON.stringify(
        {
          before,
          after: {
            scrollY: await page.evaluate(() => window.scrollY),
            overflow: await page.evaluate(() => document.body.style.overflow),
          },
          errors,
          readsBefore,
        },
        null,
        2,
      ) + "\n",
    );
  });
