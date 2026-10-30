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
  "actual React original decimal draft input native focus typing blur controlled-value lifecycle at two widths",
  { timeout: 60000 },
  async () => {
    const temp = await mkdtemp(
      path.join(os.tmpdir(), "synthetic-settings-decimal-"),
    );
    let browser, server;
    const output = process.env.PUMP_SETTINGS_DECIMAL_OUTPUT,
      requests = [],
      results = [];
    try {
      await build({
        entryPoints: [
          path.join(app, "tests/fixtures/settings-decimal-input-browser.mjs"),
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
            '<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic Settings decimal input</title><style>body{font:16px system-ui;margin:16px}input{font:inherit;max-width:100%;box-sizing:border-box;width:112px}button{display:block;margin-top:16px}p{overflow-wrap:anywhere}main{max-width:640px}h1{font-size:22px}h2{font-size:16px;overflow-wrap:anywhere}section{margin-top:16px;border:1px solid #aaa;padding:10px}article{margin:6px 0;padding:6px;background:#eee;overflow-wrap:anywhere}article[data-compact=true]{padding:2px}p,aside{overflow-wrap:anywhere}</style><div id="root"></div><script type="module" src="/fixture.js"></script></html>',
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

        const input = page.getByRole("textbox", {
            name: "Synthetic decimal value",
          }),
          snapshot = () =>
            page.evaluate(() => window.settingsDecimalFixture.snapshot());
        await input.waitFor();
        await page.waitForFunction(
          () => window.settingsDecimalFixture.snapshot().mounts.length === 1,
        );
        const initial = await snapshot(),
          firstId = await page
            .locator("[data-instance]")
            .getAttribute("data-instance");
        assert.equal(await input.inputValue(), "5");
        assert.equal(await input.getAttribute("step"), "0.25");
        assert.equal(await input.getAttribute("type"), "text");
        await input.focus();
        await input.fill("1,5");
        assert.equal(await input.inputValue(), "1.5");
        await page.waitForFunction(
          () => window.settingsDecimalFixture.snapshot().state.value === 2.5,
        );
        const clampedDraft = await snapshot();
        assert.deepEqual(clampedDraft.commits.at(-1), {
          value: 2.5,
          accepted: true,
        });
        await page.locator("[data-action=blur]").click();
        assert.equal(await input.inputValue(), "2.5");
        await input.focus();
        await input.fill("3.25");
        assert.equal(await input.inputValue(), "3.25");
        await page.evaluate(() =>
          window.settingsDecimalFixture.patch({ value: 9 }),
        );
        await page.waitForFunction(
          () => window.settingsDecimalFixture.snapshot().state.value === 9,
        );
        assert.equal(await input.inputValue(), "3.25");
        const parentUpdated = await snapshot();
        assert.equal(
          await input.evaluate((n) => n === document.activeElement),
          true,
        );
        await page.locator("[data-action=blur]").click();
        assert.equal(await input.inputValue(), "9");
        await input.focus();
        let count = (await snapshot()).commits.length;
        for (const draft of ["0", "", "."]) {
          await input.fill(draft);
          assert.equal(await input.inputValue(), draft);
          assert.equal((await snapshot()).commits.length, count);
        }
        await input.fill("4");
        count = (await snapshot()).commits.length;
        for (const invalid of ["1e3", "-2", "1,2,3", "1234567890123"]) {
          await input.fill(invalid);
          assert.equal(await input.inputValue(), "4");
          assert.equal((await snapshot()).commits.length, count);
        }
        await input.fill("123456789012");
        assert.equal(await input.inputValue(), "123456789012");
        count = (await snapshot()).commits.length;
        await input.press("End");
        await input.press("9");
        assert.equal(await input.inputValue(), "123456789012");
        assert.equal((await snapshot()).commits.length, count);
        const maximumDraft = await snapshot();
        await page.locator("[data-action=blur]").click();
        await page.evaluate(() =>
          window.settingsDecimalFixture.patch({ value: 8, isDisabled: true }),
        );
        await input.waitFor();
        await page.waitForFunction(
          () => window.settingsDecimalFixture.snapshot().state.isDisabled,
        );
        assert.equal(await input.isDisabled(), true);
        assert.equal(await input.inputValue(), "8");
        await input.evaluate((n) => n.focus());
        assert.equal(
          await input.evaluate((n) => n === document.activeElement),
          false,
        );
        const disabled = await snapshot();
        await page.evaluate(() =>
          window.settingsDecimalFixture.patch({
            isDisabled: false,
            reject: true,
          }),
        );
        await page.waitForFunction(
          () => !window.settingsDecimalFixture.snapshot().state.isDisabled,
        );
        await input.focus();
        await input.fill("6.25");
        await page.waitForFunction(
          () =>
            window.settingsDecimalFixture.snapshot().commits.at(-1)
              ?.accepted === false,
        );
        assert.equal(await input.inputValue(), "6.25");
        const denied = await snapshot();
        assert.equal(denied.state.value, 8);
        await page.locator("[data-action=blur]").click();
        assert.equal(await input.inputValue(), "8");
        await page.evaluate(() =>
          window.settingsDecimalFixture.patch({ reject: false }),
        );
        await input.focus();
        await input.fill("7.75");
        await page.waitForFunction(
          () => window.settingsDecimalFixture.snapshot().state.value === 7.75,
        );
        assert.equal(await input.inputValue(), "7.75");
        assert.equal(
          await page.locator("[data-instance]").getAttribute("data-instance"),
          firstId,
        );
        const retried = await snapshot();
        if (output) {
          await mkdir(output, { recursive: true });
          await page.screenshot({
            path: path.join(output, `decimal-edit-${width}.png`),
            fullPage: true,
          });
        }
        await page.evaluate(() =>
          window.settingsDecimalFixture.patch({ present: false }),
        );
        await input.waitFor({ state: "detached" });
        await page.waitForFunction(
          () => window.settingsDecimalFixture.snapshot().unmounts.length === 1,
        );
        await page.evaluate(() =>
          window.settingsDecimalFixture.patch({ value: 18, present: true }),
        );
        await input.waitFor();
        await page.waitForFunction(
          () => window.settingsDecimalFixture.snapshot().mounts.length === 2,
        );
        assert.equal(await input.inputValue(), "18");
        assert.notEqual(
          await page.locator("[data-instance]").getAttribute("data-instance"),
          firstId,
        );
        const remounted = await snapshot();
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        );
        assert.equal(overflow, false);
        const expected = errors.filter(
            (e) => e === "SYNTHETIC numeric commit denial",
          ),
          unexpected = errors.filter(
            (e) => e !== "SYNTHETIC numeric commit denial",
          );
        assert.deepEqual(unexpected, []);
        assert.equal(expected.length, 1);
        if (output)
          await page.screenshot({
            path: path.join(output, `decimal-remount-${width}.png`),
            fullPage: true,
          });
        await page.evaluate(() => window.settingsDecimalFixture.unmount());
        const unmounted = await snapshot();
        assert.equal(unmounted.unmounts.length, 2);
        results.push({
          width,
          initial,
          clampedDraft,
          parentUpdated,
          maximumDraft,
          disabled,
          denied,
          retried,
          remounted,
          unmounted,
          expectedErrors: expected,
          unexpectedErrors: unexpected,
          overflow,
        });
        await context.close();
      }
      if (output) {
        await mkdir(output, { recursive: true });
        await writeFile(
          path.join(output, "observations.json"),
          JSON.stringify(
            {
              syntheticOnly: true,
              bundleSha256: createHash("sha256").update(bundle).digest("hex"),
              bundleBytes: bundle.length,
              requests,
              results,
            },
            null,
            2,
          ) + "\n",
        );
      }
    } finally {
      if (browser) await browser.close();
      if (server) await new Promise((resolve) => server.close(resolve));
      await rm(temp, { recursive: true, force: true });
    }
  },
);
