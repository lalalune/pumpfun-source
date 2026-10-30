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
  ),
  { chromium } = frontend("@playwright/test"),
  { build } = createRequire(backend.resolve("tsx"))("esbuild");
test(
  "actual React complete Settings section-content order/filter/key/empty/readonly-port lifecycle at two widths",
  { timeout: 60000 },
  async () => {
    const temp = await mkdtemp(
      path.join(os.tmpdir(), "synthetic-settings-section-"),
    );
    let browser, server;
    const output = process.env.PUMP_SETTINGS_SECTION_OUTPUT,
      requests = [],
      results = [];
    try {
      await build({
        entryPoints: [
          path.join(app, "tests/fixtures/settings-section-content-browser.mjs"),
        ],
        bundle: true,
        platform: "browser",
        format: "esm",
        outfile: path.join(temp, "fixture.js"),
        define: { "process.env.NODE_ENV": '"development"' },
        logLevel: "silent",
      });
      const bundle = await readFile(path.join(temp, "fixture.js"));
      server = createServer((req, res) => {
        requests.push({ method: req.method, url: req.url });
        res.setHeader("Cache-Control", "no-store");
        if (req.method !== "GET") return res.writeHead(405).end();
        if (req.url === "/fixture.js") {
          res.setHeader("Content-Type", "text/javascript");
          res.end(bundle);
        } else if (req.url === "/") {
          res.setHeader("Content-Type", "text/html");
          res.end(
            '<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic Settings section content</title><style>body{font:16px system-ui;margin:16px}main{max-width:640px}h1{font-size:22px}h2{font-size:16px;overflow-wrap:anywhere}section{margin-top:16px;border:1px solid #aaa;padding:10px}article{margin:6px 0;padding:6px;background:#eee;overflow-wrap:anywhere}article[data-compact=true]{padding:2px}p,aside{overflow-wrap:anywhere}</style><div id="root"></div><script type="module" src="/fixture.js"></script></html>',
          );
        } else res.writeHead(404).end();
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
        page.on("pageerror", (e) => errors.push(e.message));
        await page.route("**/*", (route) => {
          const q = route.request();
          if (new URL(q.url()).origin !== base || q.method() !== "GET") {
            errors.push("Unexpected request " + q.url());
            return route.abort();
          }
          return route.continue();
        });
        await page.goto(base);
        const snapshot = () =>
          page.evaluate(() => ({
            host: window.settingsSectionFixture.snapshot(),
            ids: [...document.querySelectorAll("[data-field-id]")].map((n) =>
              n.getAttribute("data-field-id"),
            ),
            compact: [...document.querySelectorAll("[data-field-id]")].map(
              (n) => n.getAttribute("data-compact"),
            ),
            labels: [...document.querySelectorAll("[data-host-frame]")].map(
              (n) => n.getAttribute("data-label"),
            ),
          }));
        await page.waitForFunction(
          () =>
            Object.keys(window.settingsSectionFixture?.snapshot().mounted ?? {})
              .length === 3,
        );
        const initial = await snapshot();
        assert.deepEqual(initial.ids, [
          "chart.axis.synthetic",
          "chart.markers.b",
          "chart.markers.a",
        ]);
        assert.deepEqual(initial.compact, [null, "true", "true"]);
        assert.deepEqual(initial.labels, [
          "unlabelled",
          "Synthetic:web.settings.chart.bubbles",
        ]);
        if (output) {
          await mkdir(output, { recursive: true });
          await page.screenshot({
            path: path.join(output, `section-groups-${width}.png`),
            fullPage: true,
          });
        }
        await page.evaluate(() =>
          window.settingsSectionFixture.hidden(["chart.markers.a"]),
        );
        await page.waitForFunction(
          () =>
            Object.keys(window.settingsSectionFixture.snapshot().mounted)
              .length === 2,
        );
        const filtered = await snapshot();
        assert.deepEqual(filtered.ids, [
          "chart.axis.synthetic",
          "chart.markers.b",
        ]);
        for (const id of filtered.ids)
          assert.equal(filtered.host.mounted[id], initial.host.mounted[id]);
        await page.evaluate(() => window.settingsSectionFixture.hidden([]));
        await page.waitForFunction(
          () =>
            Object.keys(window.settingsSectionFixture.snapshot().mounted)
              .length === 3,
        );
        const restored = await snapshot();
        assert.notEqual(
          restored.host.mounted["chart.markers.a"],
          initial.host.mounted["chart.markers.a"],
        );
        assert.equal(
          restored.host.mounted["chart.markers.b"],
          initial.host.mounted["chart.markers.b"],
        );
        await page.evaluate(() =>
          window.settingsSectionFixture.hidden([
            "chart.markers.a",
            "chart.markers.b",
          ]),
        );
        await page.waitForFunction(
          () =>
            Object.keys(window.settingsSectionFixture.snapshot().mounted)
              .length === 1,
        );
        const emptyGroupRemoved = await snapshot();
        assert.deepEqual(emptyGroupRemoved.labels, ["unlabelled"]);
        assert.equal(
          Object.keys(emptyGroupRemoved.host.frames)[0],
          Object.keys(initial.host.frames)[0],
        );
        await page.evaluate(() => {
          window.settingsSectionFixture.hidden([]);
          window.settingsSectionFixture.section("feed");
        });
        await page.waitForFunction(
          () => window.settingsSectionFixture.snapshot().mounted["feed.first"],
        );
        const feed = await snapshot();
        assert.deepEqual(feed.ids, ["feed.second", "feed.first"]);
        assert.deepEqual(feed.labels, ["unlabelled"]);
        assert.ok(
          !Object.keys(initial.host.frames).includes(
            Object.keys(feed.host.frames)[0],
          ),
        );
        await page.evaluate(() =>
          window.settingsSectionFixture.section("privacy"),
        );
        await page.locator("[data-external-port=privacy]").waitFor();
        await page.waitForFunction(
          () =>
            window.settingsSectionFixture.snapshot().mounted[
              "privacy.synthetic"
            ],
        );
        const privacy = await snapshot();
        assert.deepEqual(privacy.ids, ["privacy.synthetic"]);
        assert.equal(
          await page
            .locator("[data-external-port=privacy]")
            .getAttribute("data-close-identity"),
          "same",
        );
        await page.evaluate(() =>
          window.settingsSectionFixture.hidden(["privacy.synthetic"]),
        );
        await page.waitForFunction(
          () =>
            Object.keys(window.settingsSectionFixture.snapshot().mounted)
              .length === 0,
        );
        assert.equal(
          await page.locator("[data-external-port=privacy]").count(),
          0,
        );
        const emptyPrivacy = await snapshot();
        assert.deepEqual(emptyPrivacy.labels, []);
        await page.evaluate(() =>
          window.settingsSectionFixture.section("account"),
        );
        await page.locator("[data-external-port=account]").waitFor();
        const account = await snapshot();
        assert.deepEqual(account.ids, []);
        assert.deepEqual(account.labels, []);
        await page.evaluate(() =>
          window.settingsSectionFixture.section("notifications"),
        );
        await page.locator("[data-external-port=notifications]").waitFor();
        assert.equal(
          await page
            .locator('[data-testid="settings-section-notifications"]')
            .count(),
          0,
        );
        const notifications = await snapshot();
        assert.deepEqual(notifications.ids, []);
        assert.deepEqual(notifications.labels, []);
        await page.evaluate(() =>
          window.settingsSectionFixture.section("unknown"),
        );
        await page
          .locator('[data-testid="settings-section-unknown"]')
          .waitFor({ state: "attached" });
        assert.equal(await page.getByRole("status").count(), 0);
        assert.equal(await page.locator("[data-external-port]").count(), 0);
        const unknown = await snapshot();
        assert.deepEqual(unknown.ids, []);
        assert.deepEqual(unknown.labels, []);
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth - innerWidth,
        );
        assert.ok(overflow <= 1);
        assert.deepEqual(errors, []);
        if (output)
          await page.screenshot({
            path: path.join(output, `section-empty-${width}.png`),
            fullPage: true,
          });
        await page.evaluate(() => window.settingsSectionFixture.unmount());
        const unmounted = await snapshot();
        assert.deepEqual(unmounted.host.mounted, {});
        assert.deepEqual(unmounted.host.frames, {});
        assert.equal(await page.locator("main").count(), 0);
        assert.deepEqual(errors, []);
        results.push({
          width,
          initial,
          filtered,
          restored,
          emptyGroupRemoved,
          feed,
          privacy,
          emptyPrivacy,
          account,
          notifications,
          unknown,
          unmounted,
          overflow,
          errors,
          limits:
            "Actual source section-owner withreadonlysyntheticmetadata/ports and actualReact/compiler. Host honors source section-keyed parent; useId/effects diagnosehostkeys, not preference/provider lifecycle.",
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
              limits:
                "Owned GET-onlyfixture; onlyreadonlysyntheticregistry/visibility/renderer/translationports. No protected/provider/account/Hermes/cookie/request acquisition, actualstorage/credentials/userdata/preferences/controlmutation or originalglobalSettings/CSS/native/API/pixel/security/completion claim.",
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
