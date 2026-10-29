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
  "actual React attempt/loading/content lifecycle with controlled synthetic provider promises at two widths",
  { timeout: 60000 },
  async () => {
    const temp = await mkdtemp(
      path.join(os.tmpdir(), "synthetic-settings-resource-"),
    );
    let browser, server;
    const results = [],
      requests = [],
      output = process.env.PUMP_SETTINGS_RESOURCE_OUTPUT;
    try {
      await build({
        entryPoints: [
          path.join(app, "tests/fixtures/settings-resource-gate-browser.mjs"),
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
            '<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic Settings resource attempt</title><style>body{font:16px system-ui;margin:16px}main{max-width:640px}h1{font-size:22px}button{font:inherit}article{padding:8px;border:1px solid #aaa}[aria-hidden=true]>div{display:flex;justify-content:space-between;gap:24px;padding:16px 0}[aria-hidden=true]>div>div:first-child{max-width:75%}.animate-pulse{background:#ddd;border-radius:4px;height:12px;width:80px;margin:8px 0}.w-40{width:160px}.w-64{width:256px;max-width:100%}.w-9{width:36px}</style><div id="root"></div><script type="module" src="/fixture.js"></script></html>',
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
          const req = route.request();
          if (new URL(req.url()).origin !== base || req.method() !== "GET") {
            errors.push("Unexpected request " + req.url());
            return route.abort();
          }
          return route.continue();
        });
        const snapshot = () =>
          page.evaluate(() => window.settingsResourceFixture.snapshot());
        const requestCount = async (count) =>
          page.waitForFunction(
            (n) =>
              window.settingsResourceFixture?.snapshot().requests.length === n,
            count,
          );
        const content = async () =>
          page.locator("[data-host-section]").waitFor();
        const busy = page.locator("[aria-busy=true]");
        await page.goto(base);
        await requestCount(1);
        await busy.waitFor();
        assert.equal(await page.locator("[aria-hidden=true]>div").count(), 5);
        assert.equal(await page.locator(".animate-pulse").count(), 15);
        assert.equal(
          await page.locator("[data-host-section],[data-host-results]").count(),
          0,
        );
        const initial = await snapshot();
        assert.equal(initial.sentinel, false);
        assert.equal(initial.requests[0].locale, "fr");
        assert.deepEqual(
          initial.events.filter((x) => x[0] === "exists"),
          [["exists", 1, "web.trade.max_slippage"]],
        );
        if (output) {
          await mkdir(output, { recursive: true });
          await page.screenshot({
            path: path.join(output, `loading-${width}.png`),
            fullPage: true,
          });
        }
        await page.evaluate(() => window.settingsResourceFixture.resolve(0));
        await content();
        assert.equal(await busy.count(), 0);
        assert.equal(await page.locator("[aria-hidden]").count(), 0);
        const completedAbsent = await snapshot();
        assert.equal(completedAbsent.sentinel, false);
        assert.equal(completedAbsent.requests.length, 1);
        const firstInstance = await page
          .locator("[data-host-section]")
          .getAttribute("data-host-instance");
        assert.equal(
          await page
            .locator("[data-host-section]")
            .getAttribute("data-host-focus"),
          "synthetic-focus",
        );
        await page
          .getByRole("button", { name: "Synthetic close callback" })
          .click();
        assert.equal((await snapshot()).closeCount, 1);
        await page.evaluate(() =>
          window.settingsResourceFixture.section("privacy"),
        );
        await page.locator("[data-host-section=privacy]").waitFor();
        const changedSection = await snapshot();
        const secondInstance = await page
          .locator("[data-host-section]")
          .getAttribute("data-host-instance");
        assert.notEqual(secondInstance, firstInstance);
        await page.evaluate(() =>
          window.settingsResourceFixture.query("  Café motion  "),
        );
        await page.locator("[data-host-results]").waitFor();
        assert.equal(
          await page.locator("[data-host-results]").innerText(),
          "Café motion",
        );
        assert.equal(
          await page
            .locator("[data-host-results]")
            .getAttribute("data-visible-identity"),
          "same",
        );
        await page.waitForFunction(
          () =>
            Object.keys(window.settingsResourceFixture.snapshot().mounted)
              .length === 0,
        );
        const searched = await snapshot();
        assert.equal(searched.requests.length, 1);
        await page.evaluate(() => {
          window.settingsResourceFixture.query(" \t ");
          window.settingsResourceFixture.provider("de-DE", false);
        });
        await content();
        const alreadyComplete = await snapshot();
        assert.equal(alreadyComplete.sentinel, false);
        assert.equal(alreadyComplete.requests.length, 1);
        assert.equal(
          alreadyComplete.events.filter((x) => x[0] === "exists").length,
          1,
        );
        await page.evaluate(() =>
          window.settingsResourceFixture.remount("unsupported", false),
        );
        await requestCount(2);
        await busy.waitFor();
        const fallback = await snapshot();
        assert.equal(fallback.requests[1].locale, "en");
        await page.evaluate(() =>
          window.settingsResourceFixture.language("fr-FR"),
        );
        await page.waitForFunction(
          () => window.settingsResourceFixture.snapshot().language === "fr-FR",
        );
        await page.evaluate(() => new Promise(requestAnimationFrame));
        const sameIdentity = await snapshot();
        assert.equal(sameIdentity.requests.length, 2);
        assert.equal(await busy.count(), 1);
        await page.evaluate(() =>
          window.settingsResourceFixture.provider("de-DE", false),
        );
        await requestCount(3);
        const changedProvider = await snapshot();
        assert.equal(changedProvider.requests[2].locale, "de");
        await page.evaluate(() => window.settingsResourceFixture.resolve(1));
        await page.evaluate(() => new Promise(requestAnimationFrame));
        assert.equal(await busy.count(), 1);
        assert.equal(await page.locator("[data-host-section]").count(), 0);
        const staleCompletion = await snapshot();
        await page.evaluate(() => window.settingsResourceFixture.resolve(2));
        await content();
        assert.equal(await busy.count(), 0);
        const currentCompletion = await snapshot();
        assert.equal(currentCompletion.sentinel, false);
        await page.evaluate(() =>
          window.settingsResourceFixture.remount("unsupported", false),
        );
        await requestCount(4);
        await busy.waitFor();
        await page.evaluate(() => window.settingsResourceFixture.hide());
        await page.locator("[data-host-unmounted]").waitFor();
        const hidden = await snapshot();
        await page.evaluate(() => window.settingsResourceFixture.resolve(3));
        await page.evaluate(() => new Promise(requestAnimationFrame));
        const settledAfterUnmount = await snapshot();
        assert.equal(settledAfterUnmount.contentRenders, hidden.contentRenders);
        assert.deepEqual(settledAfterUnmount.mounted, {});
        assert.equal(await page.locator("[aria-busy]").count(), 0);
        await page.evaluate(() =>
          window.settingsResourceFixture.remount("fr-FR", true),
        );
        await content();
        const initiallyReady = await snapshot();
        assert.equal(initiallyReady.requests.length, 4);
        assert.equal(initiallyReady.sentinel, true);
        assert.equal(await busy.count(), 0);
        await page.evaluate(() =>
          window.settingsResourceFixture.remount("unsupported", false),
        );
        await requestCount(5);
        await busy.waitFor();
        await page.evaluate(() => window.settingsResourceFixture.reject(4));
        await content();
        await page.waitForFunction(
          () => document.querySelector("[aria-busy]") === null,
        );
        for (let i = 0; i < 20 && errors.length === 0; i++)
          await page.waitForTimeout(20);
        assert.deepEqual(errors, ["SYNTHETIC prefetch capability rejection"]);
        const rejected = await snapshot();
        assert.equal(rejected.sentinel, false);
        assert.equal(rejected.requests.length, 5);
        assert.equal(await busy.count(), 0);
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth - innerWidth,
        );
        assert.ok(overflow <= 1);
        if (output)
          await page.screenshot({
            path: path.join(output, `attempt-complete-${width}.png`),
            fullPage: true,
          });
        await page.evaluate(() => window.settingsResourceFixture.unmount());
        const unmounted = await snapshot();
        assert.deepEqual(unmounted.mounted, {});
        assert.equal(await page.locator("main").count(), 0);
        assert.deepEqual(errors, ["SYNTHETIC prefetch capability rejection"]);
        results.push({
          width,
          initial,
          completedAbsent,
          changedSection,
          searched,
          alreadyComplete,
          fallback,
          sameIdentity,
          changedProvider,
          staleCompletion,
          currentCompletion,
          hidden,
          settledAfterUnmount,
          initiallyReady,
          rejected,
          unmounted,
          overflow,
          expectedSyntheticRejection: errors,
          unexpectedErrors: [],
          limit:
            "Source-adapted actual React hook/content branch; explicit synthetic i18n/prefetch/locale/FocusProvider/read-onlyResults/Section. Attempt-completed is not resource-ready; no global Settings/native/provider parity.",
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
                "GET-only owned fixture host, controlled in-memory provider promises and readonly views; no actual cookies/storage/sessions/credentials, live namespace or tenant request, preference control, original provider/global mount/CSS/API/native parity.",
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
