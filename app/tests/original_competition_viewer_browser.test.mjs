import assert from "node:assert/strict";
import { test } from "node:test";
import { readFile, mkdir } from "node:fs/promises";
import { createServer } from "node:http";
import { once } from "node:events";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import { chromium } from "../packages/frontend/node_modules/@playwright/test/index.mjs";
import { validateAgainstSchema } from "../packages/backend/src/schema-validator.ts";
import {
  squadVariants,
  imageVariants,
} from "../packages/frontend/src/components/leaderboard/entry/entry-helpers.mjs";
import { viewerEntry, wallet } from "./fixtures/competition-viewer-data.mjs";
const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), ".."),
  FRONTEND = path.join(APP, "packages/frontend"),
  sdk = createRequire(path.join(APP, "packages/sdk/package.json")),
  { build } = createRequire(sdk.resolve("tsup"))("esbuild"),
  frontend = createRequire(path.join(FRONTEND, "package.json"));
async function css() {
  let text = await readFile(path.join(FRONTEND, "src/app/globals.css"), "utf8");
  for (const name of [
    "recovered-tokens.css",
    "recovered-fonts.css",
    "captured-root.css",
  ])
    text = text.replace(
      '@import "./' + name + '";',
      await readFile(path.join(FRONTEND, "src/app", name), "utf8"),
    );
  const config = frontend("tailwindcss/loadConfig.js")(
    path.join(FRONTEND, "tailwind.config.ts"),
  );
  config.content = [
    {
      raw: await readFile(
        path.join(
          FRONTEND,
          "src/components/leaderboard/viewer/original-viewer-card.tsx",
        ),
        "utf8",
      ),
      extension: "tsx",
    },
  ];
  return (
    await frontend("postcss")([frontend("tailwindcss")(config)]).process(text, {
      from: undefined,
    })
  ).css;
}
test("actual captured viewer consumer in React/Chromium: all six contexts × desktop/mobile, toggle/query lifetime, supplied updates, invalid/cleared props and responsive fit", async (t) => {
  const spec = JSON.parse(
      await readFile(path.join(APP, "contracts/developer.openapi.json")),
    ),
    schema =
      spec.paths["/competitions/{idOrSlug}"].get.responses["200"].content[
        "application/json"
      ].schema.properties.leaderboard.properties.entries.items;
  const script = await build({
      entryPoints: [
        path.join(APP, "tests/fixtures/competition-viewer-browser.mjs"),
      ],
      bundle: true,
      write: false,
      format: "iife",
      platform: "browser",
      jsx: "automatic",
      nodePaths: [path.join(FRONTEND, "node_modules")],
      define: { "process.env.NODE_ENV": '"production"' },
    }),
    style = await css(),
    admissions = [];
  const server = createServer(async (req, res) => {
    if (req.url.startsWith("/fixture/")) {
      const body =
          req.url === "/fixture/valid"
            ? viewerEntry
            : { ...viewerEntry, buySpendSol: "bad" },
        errors = validateAgainstSchema(body, schema, "$", spec);
      admissions.push({ path: req.url, valid: !errors.length });
      res.statusCode = errors.length ? 422 : 200;
      res.setHeader("content-type", "application/json");
      res.end(
        JSON.stringify(
          errors.length ? { error: "invalid fixture props" } : body,
        ),
      );
      return;
    }
    if (req.url === "/app.js") {
      res.setHeader("content-type", "text/javascript");
      res.end(script.outputFiles[0].contents);
      return;
    }
    if (req.url === "/style.css") {
      res.setHeader("content-type", "text/css");
      res.end(style);
      return;
    }
    if (req.url.startsWith("/fonts/")) {
      try {
        res.setHeader("content-type", "font/woff2");
        res.end(await readFile(path.join(FRONTEND, "public", req.url)));
      } catch {
        res.statusCode = 404;
        res.end();
      }
      return;
    }
    res.setHeader("content-type", "text/html");
    res.end(
      '<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/style.css"></head><body><div id="root"></div><script src="/app.js"></script></body></html>',
    );
  });
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  t.after(async () => {
    const closed = new Promise((r) => server.close(r));
    server.closeAllConnections();
    await closed;
  });
  const origin = "http://127.0.0.1:" + server.address().port,
    browser = await chromium.launch({
      headless: true,
      executablePath: chromium.executablePath(),
    });
  t.after(() => browser.close());
  const errors = [],
    requests = [];
  for (const [name, viewport] of [
    ["desktop", { width: 1280, height: 900 }],
    ["mobile", { width: 375, height: 812 }],
  ])
    for (const squad of squadVariants)
      for (const image of imageVariants) {
        const page = await browser.newPage({ viewport });
        page.on("pageerror", (e) => errors.push(e.message));
        await page.route("**/*", (route) => {
          const r = route.request();
          requests.push({ url: r.url(), method: r.method() });
          return new URL(r.url()).origin === origin
            ? route.continue()
            : route.abort();
        });
        await page.goto(
          origin + "/?squad=" + squad.sha256 + "&image=" + image.sha256,
        );
        await page.waitForSelector("#empty");
        assert.equal(await page.getByTestId("cup-rank-card").count(), 0);
        await page.click("#load");
        const card = page.getByTestId("cup-rank-card"),
          toggle = card.locator("button");
        await card.waitFor();
        assert.equal(await toggle.getAttribute("aria-expanded"), "false");
        assert.equal(
          await toggle.getAttribute("aria-label"),
          "fixture-show-stats",
        );
        assert.equal(
          await card.getByTestId("cup-rank-card-pnl").textContent(),
          "$1,000.00",
        );
        assert.equal(
          await card.locator("a").getAttribute("href"),
          "/profile/" + wallet,
        );
        assert.equal(
          await card.locator("a").getAttribute("data-prefetch"),
          "false",
        );
        assert.deepEqual(await page.evaluate(() => window.__price), {
          mounts: 0,
          unmounts: 0,
          active: 0,
        });
        assert.ok((await card.textContent()).includes("fixture-YOU"));
        await page.evaluate(() => document.fonts.ready);
        const save = async (phase) => {
          if (
            process.env.VIEWER_SCREENSHOTS_DIR &&
            squad === squadVariants[0] &&
            image === imageVariants[0]
          ) {
            await mkdir(process.env.VIEWER_SCREENSHOTS_DIR, {
              recursive: true,
            });
            await page.screenshot({
              path: path.join(
                process.env.VIEWER_SCREENSHOTS_DIR,
                "viewer-" + name + "-" + phase + ".png",
              ),
              fullPage: true,
            });
          }
        };
        await save("collapsed");
        await toggle.click();
        await page.waitForFunction(() => window.__price.active === 1);
        assert.equal(await toggle.getAttribute("aria-expanded"), "true");
        assert.equal(
          await toggle.getAttribute("aria-label"),
          "fixture-hide-stats",
        );
        assert.ok((await card.textContent()).includes("Realized"));
        assert.ok((await card.textContent()).includes("-$25.50"));
        assert.ok((await card.textContent()).includes("$0.00"));
        assert.ok((await card.textContent()).includes("—"));
        assert.equal(
          await card.locator("svg path").getAttribute("d"),
          "M4 15.0001L11.2929 7.7072C11.6834 7.31668 12.3166 7.31667 12.7071 7.7072L20 15.0001",
        );
        await page.click("#price");
        await page.waitForFunction(() =>
          document
            .querySelector('[data-testid="cup-rank-card"]')
            .textContent.includes("$12K"),
        );
        await save("expanded");
        await page.click("#zero");
        await page.waitForFunction(() =>
          document
            .querySelector('[data-testid="cup-rank-card"]')
            .textContent.includes("—"),
        );
        await page.click("#update");
        await page.waitForFunction(() =>
          document
            .querySelector('[data-testid="cup-rank-card"]')
            .textContent.includes("Updated viewer"),
        );
        assert.equal(await toggle.getAttribute("aria-expanded"), "true");
        assert.equal(
          await card.getByTestId("cup-rank-card-pnl").textContent(),
          "-$0.50",
        );
        assert.ok((await card.textContent()).includes("#—"));
        assert.ok((await card.textContent()).includes("$12.00"));
        const bounds = await card.evaluate((e) => ({
          width: e.clientWidth,
          scroll: e.scrollWidth,
        }));
        assert.ok(
          bounds.scroll <= bounds.width + 1,
          JSON.stringify({ name, bounds }),
        );
        assert.ok(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth,
          ),
        );
        await toggle.focus();
        await page.keyboard.press("Space");
        await page.waitForFunction(() => window.__price.active === 0);
        assert.equal(await toggle.getAttribute("aria-expanded"), "false");
        assert.ok(!(await card.textContent()).includes("Realized"));
        assert.equal(
          await card.locator("svg path").getAttribute("d"),
          "M20 9L12.7071 16.2929C12.3166 16.6834 11.6834 16.6834 11.2929 16.2929L4 9",
        );
        await toggle.click();
        await page.waitForFunction(() => window.__price.active === 1);
        await page.click("#group");
        await page.waitForFunction(() =>
          document
            .querySelector('[data-testid="cup-rank-card"]')
            .textContent.includes("fixture-your-squad"),
        );
        assert.equal(
          await card.locator("a").getAttribute("href"),
          "/squads/group%2Ffixture",
        );
        assert.ok(!(await card.textContent()).includes("fixture-YOU"));
        assert.equal(await toggle.getAttribute("aria-expanded"), "true");
        await page.click("#invalid");
        await page.waitForSelector('[role="alert"]');
        assert.equal(await card.count(), 0);
        await page.waitForFunction(() => window.__price.active === 0);
        assert.deepEqual(await page.evaluate(() => window.__price), {
          mounts: 2,
          unmounts: 2,
          active: 0,
        });
        await page.click("#load");
        await card.waitFor();
        assert.equal(await toggle.getAttribute("aria-expanded"), "false");
        await page.click("#clear");
        await page.waitForSelector("#empty");
        assert.equal(await card.count(), 0);
        assert.deepEqual(await page.context().cookies(), []);
        assert.equal(await page.evaluate(() => localStorage.length), 0);
        await page.close();
      }
  assert.deepEqual(errors, []);
  assert.equal(admissions.filter((x) => x.valid).length, 24);
  assert.equal(admissions.filter((x) => !x.valid).length, 12);
  assert.ok(
    requests.every(
      (r) => r.method === "GET" && new URL(r.url).origin === origin,
    ),
  );
});
