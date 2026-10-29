import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { mkdtemp, rm, readFile, mkdir, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { once } from "node:events";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
const app = fileURLToPath(new URL("..", import.meta.url));
const frontend = createRequire(
  new URL("../packages/frontend/package.json", import.meta.url),
);
const backend = createRequire(
  new URL("../packages/backend/package.json", import.meta.url),
);
const { chromium } = frontend("@playwright/test");
const { build } = createRequire(backend.resolve("tsx"))("esbuild");
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");

test(
  "real React source switch → functional setters → synthetic storage/events → rerender and unmount",
  { timeout: 60000 },
  async () => {
    const directory = await mkdtemp(
      path.join(os.tmpdir(), "synthetic-local-setting-browser-"),
    );
    let browser, server;
    const output = process.env.PUMP_LOCAL_SETTINGS_OUTPUT;
    const results = [];
    try {
      await build({
        entryPoints: [
          path.join(app, "tests/fixtures/local-settings-browser.mjs"),
        ],
        bundle: true,
        platform: "browser",
        format: "esm",
        outfile: path.join(directory, "fixture.js"),
        define: { "process.env.NODE_ENV": '"development"' },
        logLevel: "silent",
      });
      const bundle = await readFile(path.join(directory, "fixture.js"));
      const requests = [];
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
            '<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic settings fixture</title><style>body{font:16px system-ui;margin:16px}main{max-width:600px}button{font:inherit;padding:8px;margin:8px}output{padding:8px}</style><div id="root"></div><script type="module" src="/fixture.js"></script></html>',
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
        });
        const page = await context.newPage(),
          errors = [];
        page.on("pageerror", (error) => errors.push(error.message));
        await page.route("**/*", (route) => {
          const request = route.request();
          if (
            new URL(request.url()).origin !== base ||
            request.method() !== "GET"
          ) {
            errors.push(
              "Unexpected request: " + request.method() + " " + request.url(),
            );
            return route.abort();
          }
          return route.continue();
        });
        await page.goto(base);
        const control = page.getByRole("switch", {
          name: "Synthetic animation preference",
        });
        await control.waitFor();
        assert.equal(await control.getAttribute("aria-checked"), "false");
        await control.click();
        await page.waitForFunction(
          () =>
            document
              .querySelector('[role="switch"]')
              .getAttribute("aria-checked") === "true",
        );
        assert.equal(
          await page.evaluate(
            () => window.localSettingsFixture.summary().pointerBubbles,
          ),
          0,
        );
        await control.focus();
        await control.press("Space");
        await page.waitForFunction(
          () => document.querySelector("output").textContent === "false",
        );
        await page.evaluate(() => {
          window.localSettingsFixture.clearCalls();
          window.localSettingsFixture.doubleUpdate();
        });
        await page.waitForFunction(
          () => document.querySelector("output").textContent === "false",
        );
        const functional = await page.evaluate(() =>
          window.localSettingsFixture.summary(),
        );
        assert.deepEqual(
          functional.calls
            .filter((entry) => entry[0] === "write")
            .map((entry) => entry[2]),
          ["true", "false"],
        );
        assert.equal(functional.setterChanged, false);
        await page.evaluate(() => window.localSettingsFixture.failWrites(true));
        await control.click();
        await page.waitForFunction(
          () => document.querySelector("output").textContent === "true",
        );
        const fallback = await page.evaluate(() => ({
          ...window.localSettingsFixture.summary(),
          freshRead: window.localSettingsFixture.freshRead(),
        }));
        assert.equal(fallback.values["home.show-animations"], "false");
        assert.equal(fallback.freshRead, false);
        await page.evaluate(() => window.localSettingsFixture.external(false));
        assert.equal(await control.getAttribute("aria-checked"), "true");
        await page.evaluate(() => {
          window.localSettingsFixture.failWrites(false);
          window.localSettingsFixture.write(false);
        });
        await page.waitForFunction(
          () => document.querySelector("output").textContent === "false",
        );
        await page.evaluate(() => window.localSettingsFixture.external(true));
        await page.waitForFunction(
          () => document.querySelector("output").textContent === "true",
        );
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth - innerWidth,
        );
        assert.ok(overflow <= 1);
        if (output) {
          await mkdir(output, { recursive: true });
          await page.screenshot({
            path: path.join(output, `switch-${width}.png`),
            fullPage: true,
          });
        }
        await page.evaluate(() => {
          window.localSettingsFixture.unmount();
          window.localSettingsFixture.clearCalls();
          window.localSettingsFixture.external(false);
        });
        const afterUnmount = await page.evaluate(() =>
          window.localSettingsFixture.summary(),
        );
        assert.equal(await page.getByRole("switch").count(), 0);
        assert.equal(
          afterUnmount.calls.filter((entry) => entry[0] === "read").length,
          0,
        );
        assert.deepEqual(errors, []);
        results.push({
          width,
          functional,
          fallback,
          overflow,
          afterUnmount,
          errors,
        });
        await context.close();
      }
      if (output)
        await writeFile(
          path.join(output, "observations.json"),
          JSON.stringify(
            {
              fixture:
                "actual source-adapted React components with explicit synthetic storage/control ports",
              bundleSha256: hash(bundle),
              requests,
              results,
              limits:
                "No real browser storage/cookies, original control/provider styling, mounted product Settings/Home effect, native API or server persistence claim.",
            },
            null,
            2,
          ) + "\n",
        );
    } finally {
      await browser?.close();
      if (server) await new Promise((resolve) => server.close(resolve));
      await rm(directory, { recursive: true, force: true });
    }
  },
);
