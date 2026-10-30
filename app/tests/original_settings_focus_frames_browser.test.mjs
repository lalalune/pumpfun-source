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
  "actual React original readonly frames with native smooth-scroll and one-shot2500ms focus lifecycle at two widths",
  { timeout: 60000 },
  async () => {
    const temp = await mkdtemp(
      path.join(os.tmpdir(), "synthetic-settings-focus-"),
    );
    let browser, server;
    const results = [],
      requests = [],
      output = process.env.PUMP_SETTINGS_FOCUS_OUTPUT;
    try {
      await build({
        entryPoints: [
          path.join(app, "tests/fixtures/settings-focus-frames-browser.mjs"),
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
            '<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic original Settings frames</title><style>body{font:16px system-ui;margin:16px}main{max-width:640px}h1{font-size:22px}h3{font-size:14px;margin:8px}h4{font-size:14px;margin:0}p{font-size:14px}input{font:inherit;max-width:100%;box-sizing:border-box;margin-bottom:12px}[data-scroll-host]{height:220px;overflow:auto;border:1px solid #999;scrollbar-gutter:stable}[data-setting-id]{padding:14px;border-block:1px solid #ccc;min-height:72px;box-sizing:border-box}[data-focused=true]{background:#e6f4ff;outline:1px solid #468bd0;outline-offset:-1px}[data-host-spacer]{height:340px}</style><div id="root"></div><script type="module" src="/fixture.js"></script></html>',
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
        const snapshot = () =>
          page.evaluate(() => ({
            host: window.settingsFocusFixture.snapshot(),
            focused: [...document.querySelectorAll("[data-focused=true]")].map(
              (n) => n.getAttribute("data-setting-id"),
            ),
            scrollTop:
              document.querySelector("[data-scroll-host]")?.scrollTop ?? null,
          }));
        const center = async (id) => {
          await page.waitForFunction(
            (id) => {
              const host = document.querySelector("[data-scroll-host]"),
                target = document.querySelector(`[data-setting-id="${id}"]`);
              if (!host || !target) return false;
              const a = host.getBoundingClientRect(),
                b = target.getBoundingClientRect();
              return Math.abs((a.top + a.bottom - b.top - b.bottom) / 2) < 6;
            },
            id,
            { timeout: 1800 },
          );
          return page.evaluate((id) => {
            const a = document
                .querySelector("[data-scroll-host]")
                .getBoundingClientRect(),
              b = document
                .querySelector(`[data-setting-id="${id}"]`)
                .getBoundingClientRect();
            return {
              offset: (a.top + a.bottom - b.top - b.bottom) / 2,
              scrollTop: document.querySelector("[data-scroll-host]").scrollTop,
            };
          }, id);
        };
        await page.goto(base);
        await page
          .locator('[data-setting-id="feed.beta"][data-focused=true]')
          .waitFor();
        await page.waitForFunction(
          () => window.settingsFocusFixture.snapshot().timers.length === 1,
        );
        const initialCenter = await center("feed.beta");
        assert.ok(initialCenter.scrollTop > 0);
        const initial = await snapshot();
        assert.deepEqual(initial.focused, ["feed.beta"]);
        assert.equal(initial.host.timers[0].delay, 2500);
        assert.equal(
          await page.getByText("Readonly slot", { exact: true }).count(),
          1,
        );
        assert.equal(
          await page.getByText("Readonly child", { exact: true }).count(),
          1,
        );
        await page
          .getByRole("textbox", { name: "Synthetic host focus control" })
          .fill("synthetic diagnostic");
        await page.evaluate(() => {
          document
            .querySelector("[data-scroll-host]")
            .scrollTo({ top: 0, behavior: "instant" });
          window.settingsFocusFixture.rerender();
        });
        await page.evaluate(() => new Promise(requestAnimationFrame));
        await page.evaluate(() => new Promise(requestAnimationFrame));
        const sameTarget = await snapshot();
        assert.equal(sameTarget.scrollTop, 0);
        assert.deepEqual(sameTarget.focused, ["feed.beta"]);
        assert.equal(sameTarget.host.timers.length, 1);
        await page.evaluate(() =>
          window.settingsFocusFixture.target("feed.alpha"),
        );
        await page
          .locator('[data-setting-id="feed.alpha"][data-focused=true]')
          .waitFor();
        await page.waitForFunction(
          () => window.settingsFocusFixture.snapshot().timers.length === 2,
        );
        const changedCenter = await center("feed.alpha");
        const changed = await snapshot();
        assert.deepEqual(changed.focused, ["feed.alpha"]);
        assert.ok(changed.host.timers[0].cleared.length === 1);
        assert.equal(changed.host.timers[1].delay, 2500);
        assert.equal(
          await page
            .getByRole("textbox", { name: "Synthetic host focus control" })
            .evaluate((n) => n === document.activeElement),
          true,
        );
        if (output) {
          await mkdir(output, { recursive: true });
          await page.screenshot({
            path: path.join(output, `focused-${width}.png`),
            fullPage: true,
          });
        }
        await page.waitForFunction(
          () => window.settingsFocusFixture.snapshot().timers[1].fired !== null,
        );
        await page
          .locator("[data-focused=true]")
          .waitFor({ state: "detached" });
        const expired = await snapshot();
        assert.deepEqual(expired.focused, []);
        const elapsed =
          expired.host.timers[1].fired - expired.host.timers[1].start;
        assert.ok(elapsed >= 2400);
        assert.equal(expired.host.timers[0].fired, null);
        await page.evaluate(() =>
          window.settingsFocusFixture.target("feed.beta"),
        );
        await page.waitForFunction(
          () => window.settingsFocusFixture.snapshot().timers.length === 3,
        );
        await page.evaluate(() => new Promise(requestAnimationFrame));
        const afterExpiry = await snapshot();
        assert.deepEqual(afterExpiry.focused, []);
        assert.equal(afterExpiry.host.timers[2].delay, 2500);
        await page.evaluate(() =>
          window.settingsFocusFixture.remount("feed.beta"),
        );
        await page
          .locator('[data-setting-id="feed.beta"][data-focused=true]')
          .waitFor();
        await page.waitForFunction(
          () => window.settingsFocusFixture.snapshot().timers.length === 4,
        );
        const remountCenter = await center("feed.beta");
        const remounted = await snapshot();
        assert.deepEqual(remounted.focused, ["feed.beta"]);
        assert.ok(remounted.host.timers[2].cleared.length === 1);
        await page.evaluate(() => window.settingsFocusFixture.hide());
        await page.locator("[data-host-unmounted]").waitFor();
        const hidden = await snapshot();
        assert.deepEqual(hidden.host.active, []);
        assert.ok(hidden.host.timers[3].cleared.length === 1);
        await page.waitForTimeout(2650);
        const afterUnmount = await snapshot();
        assert.deepEqual(afterUnmount.focused, []);
        assert.equal(
          afterUnmount.host.timers.filter((t) => t.fired !== null).length,
          1,
        );
        assert.deepEqual(afterUnmount.host.active, []);
        await page.evaluate(() => window.settingsFocusFixture.remount(null));
        await page.locator("[data-scroll-host]").waitFor();
        await page.evaluate(() => new Promise(requestAnimationFrame));
        const emptyTarget = await snapshot();
        assert.deepEqual(emptyTarget.focused, []);
        assert.equal(emptyTarget.host.timers.length, 4);
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth - innerWidth,
        );
        assert.ok(overflow <= 1);
        assert.deepEqual(errors, []);
        if (output)
          await page.screenshot({
            path: path.join(output, `inactive-${width}.png`),
            fullPage: true,
          });
        await page.evaluate(() => window.settingsFocusFixture.unmount());
        const final = await snapshot();
        assert.deepEqual(final.host.active, []);
        assert.equal(await page.locator("main").count(), 0);
        assert.deepEqual(errors, []);
        results.push({
          width,
          initial,
          initialCenter,
          sameTarget,
          changed,
          changedCenter,
          expired,
          elapsed,
          afterExpiry,
          remounted,
          remountCenter,
          hidden,
          afterUnmount,
          emptyTarget,
          final,
          overflow,
          errors,
          limit:
            "Actual React/compiler, native timer and native scrollIntoView with source frames; injected readonly nodes/class combiner/window timer port only. No original provider/global Settings/CSS/vendor parity.",
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
                "Owned GET-only fixture, synthetic identifiers/readonly views. Timer capability records and forwards actual native2500ms callbacks; no global overrides/fake clock/scroll spy, actualcookies/storage/userdata/credentials/service acquisition or preference mutation. Source scroll changes visual position, not keyboard focus.",
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
