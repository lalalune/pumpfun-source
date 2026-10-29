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
import { rows, wallet } from "./fixtures/competition-entry-data.mjs";
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
          "src/components/leaderboard/entry/original-entry-row.tsx",
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
test("actual captured row consumer in React/Chromium: six contexts, person/group links, SVGs, Avatar props, supplied updates, invalid/clear states and responsive fit", async (t) => {
  const spec = JSON.parse(
      await readFile(path.join(APP, "contracts/developer.openapi.json")),
    ),
    schema =
      spec.paths["/competitions/{idOrSlug}"].get.responses["200"].content[
        "application/json"
      ].schema.properties.leaderboard.properties.entries.items;
  const script = await build({
      entryPoints: [
        path.join(APP, "tests/fixtures/competition-entry-browser.mjs"),
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
            ? rows
            : [{ ...rows[0], entry: { ...rows[0].entry, pnlUsd: "bad" } }],
        errors = body.flatMap((row) =>
          validateAgainstSchema(row.entry, schema, "$", spec),
        );
      admissions.push({ path: req.url, valid: errors.length === 0 });
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
      '<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="/style.css"></head><body><div id="root"></div><script src="/app.js"></script></body></html>',
    );
  });
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  t.after(async () => {
    const closed = new Promise((resolve) => server.close(resolve));
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
        page.on("pageerror", (error) => errors.push(error.message));
        await page.route("**/*", (route) => {
          const request = route.request();
          requests.push({ url: request.url(), method: request.method() });
          return new URL(request.url()).origin === origin
            ? route.continue()
            : route.abort();
        });
        await page.goto(
          origin + "/?squad=" + squad.sha256 + "&image=" + image.sha256,
        );
        await page.waitForSelector("#empty");
        assert.equal(await page.getByTestId("cup-entry-row").count(), 0);
        await page.click("#load");
        await page.waitForSelector("#entries");
        assert.equal(await page.getByTestId("cup-entry-row").count(), 4);
        const entry = (id) => page.locator('[data-entry-id="' + id + '"]');
        assert.ok((await entry("person").textContent()).includes("+$1,000.00"));
        assert.ok((await entry("group").textContent()).includes("-$25.00"));
        assert.ok(
          (await entry("group").textContent()).includes("fixture-members:3"),
        );
        assert.ok(
          (await entry("anonymous").textContent()).includes(
            "fixture-anonymous",
          ),
        );
        assert.ok((await entry("unranked").textContent()).includes("–"));
        assert.equal(
          await entry("person").locator("a").getAttribute("href"),
          "/profile/" + wallet,
        );
        assert.equal(
          await entry("group").locator("a").getAttribute("href"),
          "/squads/group%2Ffixture",
        );
        assert.equal(
          await entry("group").locator("a").getAttribute("data-prefetch"),
          "false",
        );
        assert.equal(
          await page.locator('[aria-label="Verified account"]').count(),
          1,
        );
        assert.equal(await page.locator('svg[viewBox="0 0 24 24"]').count(), 3);
        assert.deepEqual(
          await page.getByTestId("cup-entry-prize").allTextContents(),
          ["1000", "2 SOL"],
        );
        const avatar = await page.evaluate(
          (address) => window.__avatarProps.find((p) => p.address === address),
          wallet,
        );
        assert.equal(avatar.src, "https://fixture.invalid/avatar.png");
        assert.equal(avatar.width, 40);
        assert.equal(avatar.height, 40);
        assert.equal(avatar.isAnonymous, false);
        assert.equal(avatar.ipfsPrefix, "https://pump.mypinata.cloud/ipfs/");
        const bounds = await page
          .getByTestId("cup-entry-row")
          .evaluateAll((elements) =>
            elements.map((e) => ({
              width: e.clientWidth,
              scroll: e.scrollWidth,
            })),
          );
        assert.ok(
          bounds.every((x) => x.scroll <= x.width + 1),
          JSON.stringify({ name, bounds }),
        );
        assert.ok(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth,
          ),
        );
        await page.evaluate(() => document.fonts.ready);
        if (process.env.ENTRY_SCREENSHOTS_DIR && image === imageVariants[0]) {
          await mkdir(process.env.ENTRY_SCREENSHOTS_DIR, { recursive: true });
          await page.screenshot({
            path: path.join(
              process.env.ENTRY_SCREENSHOTS_DIR,
              "entry-" + name + "-" + squad.sha256.slice(0, 12) + ".png",
            ),
            fullPage: true,
          });
        }
        await page.click("#update");
        await page.waitForFunction(() =>
          document
            .querySelector('[data-entry-id="person"]')
            .textContent.includes("UpdatedFixture"),
        );
        assert.ok((await entry("person").textContent()).includes("-$0.50"));
        assert.equal(
          await page.locator('[aria-label="Verified account"]').count(),
          0,
        );
        assert.equal(
          await entry("person").getByTestId("cup-entry-prize").textContent(),
          "1000",
        );
        const latest = await page.evaluate(
          (address) =>
            window.__avatarProps.filter((p) => p.address === address).at(-1),
          wallet,
        );
        assert.equal(latest.src, "https://fixture.invalid/updated.png");
        await page.click("#invalid");
        await page.waitForSelector('[role="alert"]');
        assert.equal(await page.getByTestId("cup-entry-row").count(), 0);
        await page.click("#clear");
        await page.waitForSelector("#empty");
        assert.equal(await page.locator('[role="alert"]').count(), 0);
        await page.close();
      }
  assert.deepEqual(errors, []);
  assert.equal(admissions.filter((x) => x.valid).length, 12);
  assert.equal(admissions.filter((x) => !x.valid).length, 12);
  assert.ok(
    requests.every(
      (r) => new URL(r.url).origin === origin && r.method === "GET",
    ),
  );
});
