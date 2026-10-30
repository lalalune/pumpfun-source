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
  "actual React complete Settings display controller safe sections search scroll reset denial and lifecycle at two widths",
  { timeout: 60000 },
  async () => {
    const temp = await mkdtemp(
      path.join(os.tmpdir(), "synthetic-settings-modal-"),
    );
    let browser, server;
    const output = process.env.PUMP_SETTINGS_MODAL_OUTPUT,
      requests = [],
      results = [];
    try {
      await build({
        entryPoints: [
          path.join(app, "tests/fixtures/settings-modal-owner-browser.mjs"),
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
            '<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic complete Settings owner</title><style>body{font:16px system-ui;margin:16px}button{margin:4px;max-width:100%;overflow-wrap:anywhere}input{max-width:75%;box-sizing:border-box}nav{display:flex;flex-wrap:wrap}p{overflow-wrap:anywhere}[data-testid=settings-modal]{max-width:700px;border:1px solid #777;padding:8px}div.custom-scrollbar{height:150px;overflow-y:auto}header,footer{display:block}footer>div{display:block}label{display:flex;gap:4px}main{max-width:640px}h1{font-size:22px}h2{font-size:16px;overflow-wrap:anywhere}section{margin-top:16px;border:1px solid #aaa;padding:10px}article{margin:6px 0;padding:6px;background:#eee;overflow-wrap:anywhere}article[data-compact=true]{padding:2px}p,aside{overflow-wrap:anywhere}</style><div id="root"></div><script type="module" src="/fixture.js"></script></html>',
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
            page.evaluate(() => window.settingsModalFixture.snapshot()),
          modal = page.getByTestId("settings-modal"),
          input = page.getByRole("searchbox", {
            name: "web.settings.search_aria",
          }),
          scroll = page.locator(".custom-scrollbar");
        await modal.waitFor();
        await page.locator("[data-loading]").waitFor();
        assert.equal(await scroll.getAttribute("aria-busy"), "true");
        const pending = await snapshot();
        assert.deepEqual(pending.queries, []);
        assert.deepEqual(pending.mounts, []);
        await page.evaluate(() =>
          window.settingsModalFixture.patch({ ready: true }),
        );
        await page.locator("[data-section=feed]").waitFor();
        await page.waitForFunction(
          () => window.settingsModalFixture.snapshot().mounts.length === 1,
        );
        assert.equal(await scroll.getAttribute("aria-busy"), null);
        assert.equal(
          await page.locator("[data-focus-value]").textContent(),
          "feed.synthetic",
        );
        const first = await snapshot(),
          firstId = await page
            .locator("[data-instance]")
            .getAttribute("data-instance");
        await scroll.evaluate((n) => (n.scrollTop = 80));
        assert.ok((await scroll.evaluate((n) => n.scrollTop)) > 0);
        await page
          .getByRole("tab", { name: "synthetic.privacy.tab", exact: true })
          .click();
        await page.locator("[data-section=privacy]").waitFor();
        await page.waitForFunction(
          () => document.querySelector(".custom-scrollbar").scrollTop === 0,
        );
        assert.equal(
          await page
            .getByRole("tab", { name: "synthetic.privacy.tab", exact: true })
            .getAttribute("aria-selected"),
          "true",
        );
        assert.notEqual(
          await page.locator("[data-instance]").getAttribute("data-instance"),
          firstId,
        );
        const selected = await snapshot();
        assert.deepEqual(selected.events.at(-1), {
          kind: "select",
          section: "privacy",
        });
        await page
          .getByRole("button", {
            name: "web.settings.reset_section",
            exact: true,
          })
          .click();
        await page
          .getByRole("button", { name: "common.cancel", exact: true })
          .waitFor();
        await page
          .getByRole("tab", { name: "synthetic.feed.tab", exact: true })
          .click();
        await page
          .getByRole("button", {
            name: "web.settings.reset_section",
            exact: true,
          })
          .waitFor();
        assert.equal(
          await page
            .getByRole("button", { name: "common.cancel", exact: true })
            .count(),
          0,
        );
        await scroll.evaluate((n) => (n.scrollTop = 80));
        await input.fill("  first  ");
        await page.locator("[data-results-query=first]").waitFor();
        assert.equal(await input.inputValue(), "  first  ");
        await page.waitForFunction(
          () => document.querySelector(".custom-scrollbar").scrollTop === 0,
        );
        const searching = await snapshot();
        assert.deepEqual(searching.queries.at(-1), {
          query: "first",
          visibleSections: ["feed", "privacy"],
        });
        assert.equal(
          await page
            .getByRole("button", {
              name: "web.settings.reset_section",
              exact: true,
            })
            .count(),
          0,
        );
        await scroll.evaluate((n) => (n.scrollTop = 70));
        await input.fill(" second ");
        await page.locator("[data-results-query=second]").waitFor();
        assert.equal(await scroll.evaluate((n) => n.scrollTop), 70);
        const sameSearchMode = await snapshot();
        await page
          .getByRole("button", {
            name: "web.settings.clear_search",
            exact: true,
          })
          .click();
        await page.locator("[data-section=feed]").waitFor();
        assert.equal(await input.inputValue(), "");
        await page.waitForFunction(
          () => document.querySelector(".custom-scrollbar").scrollTop === 0,
        );
        await page.evaluate(() =>
          window.settingsModalFixture.patch({ section: "account" }),
        );
        await page.waitForFunction(
          () =>
            window.settingsModalFixture.snapshot().state.section === "account",
        );
        assert.equal(
          await page
            .getByRole("tab", { name: "synthetic.feed.tab", exact: true })
            .getAttribute("aria-selected"),
          "true",
        );
        assert.equal(await page.locator("[data-section=account]").count(), 0);
        assert.equal(await page.locator("[data-section=feed]").count(), 1);
        const deniedSection = await snapshot();
        await page
          .getByRole("button", {
            name: "web.settings.reset_section",
            exact: true,
          })
          .click();
        await page
          .getByRole("button", { name: "common.cancel", exact: true })
          .click();
        assert.equal(
          await page
            .getByRole("button", {
              name: "web.settings.reset_confirm_action",
              exact: true,
            })
            .count(),
          0,
        );
        await page
          .getByRole("button", {
            name: "web.settings.reset_section",
            exact: true,
          })
          .click();
        await page.evaluate(() =>
          window.settingsModalFixture.patch({ denyReset: true }),
        );
        await page.waitForFunction(
          () => window.settingsModalFixture.snapshot().state.denyReset,
        );
        await page
          .getByRole("button", {
            name: "web.settings.reset_confirm_action",
            exact: true,
          })
          .click();
        await page.waitForFunction(
          () =>
            window.settingsModalFixture.snapshot().events.at(-1)?.accepted ===
            false,
        );
        assert.equal(
          await page
            .getByRole("button", {
              name: "web.settings.reset_confirm_action",
              exact: true,
            })
            .count(),
          1,
        );
        const resetDenied = await snapshot();
        assert.deepEqual(resetDenied.events.at(-1), {
          kind: "reset",
          section: "feed",
          accepted: false,
        });
        await page.evaluate(() =>
          window.settingsModalFixture.patch({ denyReset: false }),
        );
        await page.waitForFunction(
          () => !window.settingsModalFixture.snapshot().state.denyReset,
        );
        await page
          .getByRole("button", {
            name: "web.settings.reset_confirm_action",
            exact: true,
          })
          .click();
        await page
          .getByRole("button", {
            name: "web.settings.reset_section",
            exact: true,
          })
          .waitFor();
        const resetAccepted = await snapshot();
        assert.deepEqual(resetAccepted.events.at(-1), {
          kind: "reset",
          section: "feed",
          accepted: true,
        });
        await page.evaluate(() =>
          window.settingsModalFixture.patch({ resettable: false }),
        );
        await page.waitForFunction(
          () => !window.settingsModalFixture.snapshot().state.resettable,
        );
        assert.equal(
          await page
            .getByRole("button", {
              name: "web.settings.reset_section",
              exact: true,
            })
            .count(),
          0,
        );
        await page.evaluate(() => window.settingsModalFixture.dialog(true));
        assert.equal(await modal.count(), 1);
        const stillOpen = await snapshot();
        assert.equal(
          stillOpen.events.filter((e) => e.kind === "close").length,
          0,
        );
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        );
        assert.equal(overflow, false);
        if (output) {
          await mkdir(output, { recursive: true });
          await page.screenshot({
            path: path.join(output, `modal-controller-${width}.png`),
            fullPage: true,
          });
        }
        await page
          .getByRole("button", { name: "common.done", exact: true })
          .click();
        await modal.waitFor({ state: "detached" });
        const done = await snapshot();
        assert.equal(done.events.filter((e) => e.kind === "close").length, 1);
        await page.evaluate(() =>
          window.settingsModalFixture.patch({
            present: true,
            section: "privacy",
            focusSettingId: null,
          }),
        );
        await modal.waitFor();
        await page.locator("[data-section=privacy]").waitFor();
        assert.equal(await input.inputValue(), "");
        const remounted = await snapshot();
        assert.equal(remounted.state.focusSettingId, null);
        await page.evaluate(() => window.settingsModalFixture.dialog(false));
        await modal.waitFor({ state: "detached" });
        const closed = await snapshot();
        assert.equal(closed.events.filter((e) => e.kind === "close").length, 2);
        await page.evaluate(() => window.settingsModalFixture.unmount());
        const unmounted = await snapshot();
        assert.equal(unmounted.mounts.length, unmounted.unmounts.length);
        const expected = errors.filter(
            (e) => e === "SYNTHETIC reset callback denial",
          ),
          unexpected = errors.filter(
            (e) => e !== "SYNTHETIC reset callback denial",
          );
        assert.equal(expected.length, 1);
        assert.deepEqual(unexpected, []);
        results.push({
          width,
          pending,
          first,
          selected,
          searching,
          sameSearchMode,
          deniedSection,
          resetDenied,
          resetAccepted,
          stillOpen,
          done,
          remounted,
          closed,
          unmounted,
          overflow,
          expectedErrors: expected,
          unexpectedErrors: unexpected,
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
