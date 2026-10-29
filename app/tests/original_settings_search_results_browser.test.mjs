import { test } from "node:test";
import assert from "node:assert/strict";
import { createServer } from "node:http";
import { once } from "node:events";
import { createRequire } from "node:module";
import { readFile, writeFile, mkdir, mkdtemp, rm } from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
const app = fileURLToPath(new URL("..", import.meta.url)),
  frontend = createRequire(
    new URL("../packages/frontend/package.json", import.meta.url),
  ),
  backend = createRequire(
    new URL("../packages/backend/package.json", import.meta.url),
  );
const { chromium } = frontend("@playwright/test"),
  { build } = createRequire(backend.resolve("tsx"))("esbuild");
test(
  "actual React query/filter/grouped results transitions with read-only metadata and explicit host lifecycle",
  { timeout: 60000 },
  async () => {
    const temp = await mkdtemp(
      path.join(os.tmpdir(), "synthetic-settings-results-"),
    );
    let browser, server;
    const results = [],
      requests = [],
      output = process.env.PUMP_SETTINGS_RESULTS_OUTPUT;
    try {
      await build({
        entryPoints: [
          path.join(app, "tests/fixtures/settings-search-results-browser.mjs"),
        ],
        bundle: true,
        platform: "browser",
        format: "esm",
        outfile: path.join(temp, "fixture.js"),
        define: { "process.env.NODE_ENV": '"development"' },
        logLevel: "silent",
      });
      const bundle = await readFile(path.join(temp, "fixture.js"));
      server = createServer((request, response) => {
        requests.push({ method: request.method, url: request.url });
        response.setHeader("Cache-Control", "no-store");
        if (request.method !== "GET") {
          response.writeHead(405).end();
          return;
        }
        if (request.url === "/fixture.js") {
          response.setHeader("Content-Type", "text/javascript");
          response.end(bundle);
        } else if (request.url === "/") {
          response.setHeader("Content-Type", "text/html");
          response.end(
            '<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic Settings results</title><style>body{font:16px system-ui;margin:16px}main{max-width:640px}input{font:inherit;max-width:100%;box-sizing:border-box}article{padding:8px;border:1px solid #ccc}section{margin:12px 0}h1{font-size:22px}</style><div id="root"></div><script type="module" src="/fixture.js"></script></html>',
          );
        } else response.writeHead(404).end();
      });
      server.listen(0, "127.0.0.1");
      await once(server, "listening");
      const base = "http://127.0.0.1:" + server.address().port;
      browser = await chromium.launch({
        headless: true,
        executablePath:
          process.env.PUMP_BROWSER_EXECUTABLE ?? chromium.executablePath(),
      });
      for (const width of [390, 1280]) {
        const context = await browser.newContext({
            viewport: { width, height: 844 },
            locale: "en-US",
          }),
          page = await context.newPage(),
          errors = [];
        page.on("pageerror", (error) => errors.push(error.message));
        await page.route("**/*", (route) => {
          const r = route.request();
          if (new URL(r.url()).origin !== base || r.method() !== "GET") {
            errors.push("Unexpected request: " + r.url());
            return route.abort();
          }
          return route.continue();
        });
        await page.goto(base);
        const input = page.getByRole("textbox", {
          name: "Synthetic settings query",
        });
        await input.waitFor();
        const snapshot = async () =>
          page.evaluate(() => ({
            ids: [...document.querySelectorAll("[data-setting-id]")].map((n) =>
              n.getAttribute("data-setting-id"),
            ),
            groups: [...document.querySelectorAll("[data-group]")].map((n) =>
              n.getAttribute("data-group"),
            ),
            host: window.settingsResultsFixture.snapshot(),
          }));
        await page.waitForFunction(
          () =>
            window.settingsResultsFixture.snapshot().mounted[
              "privacy.warning"
            ] &&
            Object.keys(window.settingsResultsFixture.snapshot().mounted)
              .length === 3,
        );
        const initial = await snapshot();
        assert.deepEqual(initial.ids, [
          "feed.blueCard",
          "feed.other",
          "privacy.warning",
        ]);
        assert.deepEqual(initial.groups, ["Feed", "Privacy"]);
        await input.fill("  CAFÉ motion  ");
        await page.waitForFunction(
          () =>
            Object.keys(window.settingsResultsFixture.snapshot().mounted)
              .length === 1 &&
            document.querySelectorAll("[data-setting-id]").length === 1,
        );
        const filtered = await snapshot();
        assert.deepEqual(filtered.ids, ["feed.blueCard"]);
        assert.equal(
          filtered.host.mounted["feed.blueCard"],
          initial.host.mounted["feed.blueCard"],
        );
        await page.evaluate(() =>
          window.settingsResultsFixture.setHidden([
            "feed.hidden",
            "feed.blueCard",
          ]),
        );
        await page.getByRole("status").waitFor();
        await page.waitForFunction(
          () =>
            Object.keys(window.settingsResultsFixture.snapshot().mounted)
              .length === 0,
        );
        const hidden = await snapshot();
        assert.deepEqual(hidden.ids, []);
        assert.match(
          await page.getByRole("status").innerText(),
          /No matches for CAFÉ motion/,
        );
        await page.evaluate(() =>
          window.settingsResultsFixture.setHidden(["feed.hidden"]),
        );
        await page.waitForFunction(
          () =>
            Object.keys(window.settingsResultsFixture.snapshot().mounted)
              .length === 1,
        );
        const restored = await snapshot();
        assert.deepEqual(restored.ids, ["feed.blueCard"]);
        assert.notEqual(
          restored.host.mounted["feed.blueCard"],
          initial.host.mounted["feed.blueCard"],
        );
        await page.evaluate(() =>
          window.settingsResultsFixture.setVisible(["privacy"]),
        );
        await input.fill("shared");
        await page.waitForFunction(
          () =>
            Object.keys(window.settingsResultsFixture.snapshot().mounted)
              .length === 1 &&
            Boolean(
              window.settingsResultsFixture.snapshot().mounted[
                "privacy.warning"
              ],
            ),
        );
        const privacy = await snapshot();
        assert.deepEqual(privacy.ids, ["privacy.warning"]);
        assert.deepEqual(privacy.groups, ["Privacy"]);
        await page.evaluate(() =>
          window.settingsResultsFixture.setVisible(["feed", "privacy"]),
        );
        await page.waitForFunction(
          () =>
            Object.keys(window.settingsResultsFixture.snapshot().mounted)
              .length === 3,
        );
        const allAgain = await snapshot();
        assert.deepEqual(allAgain.ids, initial.ids);
        assert.deepEqual(allAgain.groups, initial.groups);
        await input.fill("notfound");
        await page.getByRole("status").waitFor();
        await page.waitForFunction(
          () =>
            Object.keys(window.settingsResultsFixture.snapshot().mounted)
              .length === 0,
        );
        const empty = await snapshot();
        assert.deepEqual(empty.ids, []);
        assert.equal(
          await page.getByRole("status").innerText(),
          "No matches for notfound",
        );
        await input.fill("");
        await page.locator('[data-host-state="blank-query"]').waitFor();
        assert.equal(await page.getByRole("region").count(), 0);
        const blank = await snapshot();
        assert.deepEqual(blank.ids, []);
        await input.fill("feed blueCard");
        await page.waitForFunction(
          () =>
            Object.keys(window.settingsResultsFixture.snapshot().mounted)
              .length === 1,
        );
        const identifier = await snapshot();
        assert.deepEqual(identifier.ids, ["feed.blueCard"]);
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth - innerWidth,
        );
        assert.ok(overflow <= 1);
        assert.deepEqual(errors, []);
        if (output) {
          await mkdir(output, { recursive: true });
          await page.screenshot({
            path: path.join(output, `settings-results-${width}.png`),
            fullPage: true,
          });
        }
        await page.evaluate(() => window.settingsResultsFixture.unmount());
        const unmounted = await snapshot();
        assert.deepEqual(unmounted.ids, []);
        assert.deepEqual(unmounted.host.mounted, {});
        assert.equal(await page.getByRole("textbox").count(), 0);
        assert.deepEqual(errors, []);
        results.push({
          width,
          initial,
          filtered,
          hidden,
          restored,
          privacy,
          allAgain,
          empty,
          blank,
          identifier,
          unmounted,
          overflow,
          errors,
          limit:
            "Read-only authored input/visibility/Field/Section host. React useId/effects are diagnostic host lifecycle only, not original setting values, private provider or product Settings mount.",
        });
        await context.close();
      }
      if (output)
        await writeFile(
          path.join(output, "observations.json"),
          JSON.stringify(
            {
              bundleSha256: createHash("sha256").update(bundle).digest("hex"),
              requests,
              results,
              fixture:
                "Complete source-adapted Settings results component with real React/compiler and explicit safe synthetic read-only metadata/host ports",
              limits:
                "No actual cookies/storage/sessions/credentials or service requests, private preference/framework, global mount or pixel/native/API parity. Blank-query host placeholder is external, not the original other section view.",
            },
            null,
            2,
          ) + "\n",
        );
    } finally {
      await browser?.close();
      if (server) await new Promise((resolve) => server.close(resolve));
      await rm(temp, { recursive: true, force: true });
    }
  },
);
