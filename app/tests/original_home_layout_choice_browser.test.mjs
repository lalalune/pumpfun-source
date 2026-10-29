import { test } from "node:test";
import assert from "node:assert/strict";
import { createServer } from "node:http";
import { once } from "node:events";
import { createRequire } from "node:module";
import { mkdtemp, readFile, mkdir, writeFile, rm } from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
const app = fileURLToPath(new URL("..", import.meta.url));
const frontend = createRequire(
    new URL("../packages/frontend/package.json", import.meta.url),
  ),
  backend = createRequire(
    new URL("../packages/backend/package.json", import.meta.url),
  );
const { chromium } = frontend("@playwright/test"),
  { build } = createRequire(backend.resolve("tsx"))("esbuild");

test(
  "actual React choice/dispatcher → synthetic cookie write/notify, same-value writes, errors and lifetime cleanup",
  { timeout: 60000 },
  async () => {
    const temp = await mkdtemp(
      path.join(os.tmpdir(), "synthetic-home-layout-"),
    );
    let server, browser;
    const requests = [],
      results = [];
    const output = process.env.PUMP_LAYOUT_OUTPUT;
    try {
      await build({
        entryPoints: [
          path.join(app, "tests/fixtures/home-layout-choice-browser.mjs"),
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
            '<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic original layout choice</title><style>body{font:16px system-ui;margin:16px}main{max-width:640px}button{font:inherit;padding:8px;min-width:120px}button svg{display:block;width:120px;max-width:100%;height:auto}[role=radiogroup]{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}[aria-checked=true]{outline:2px solid green}</style><div id="root"></div><script type="module" src="/fixture.js"></script></html>',
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
        const grid = page.getByRole("radio", { name: "Grid", exact: true }),
          table = page.getByRole("radio", { name: "Table", exact: true });
        await table.waitFor();
        await page.waitForFunction(
          () => window.homeLayoutFixture.snapshot().listeners === 1,
        );
        assert.equal(await table.getAttribute("aria-checked"), "true");
        assert.equal(
          await page.locator('svg[viewBox="0 0 120 64"]').count(),
          2,
        );
        const initial = await page.evaluate(() =>
          window.homeLayoutFixture.snapshot(),
        );
        assert.equal(initial.cookieText, "");
        assert.equal(initial.listeners, 1);
        await grid.click();
        await page.waitForFunction(() =>
          document
            .querySelector("[role=radio][aria-checked=true]")
            ?.textContent.includes("Grid"),
        );
        const selected = await page.evaluate(() =>
          window.homeLayoutFixture.snapshot(),
        );
        assert.match(selected.cookieText, /^home_feed_layout=grid;/);
        const write = selected.calls.findIndex((x) => x[0] === "write:done"),
          notify = selected.calls.findIndex((x) => x[0] === "notify");
        assert.ok(write >= 0 && notify > write);
        await grid.click();
        const repeated = await page.evaluate(() =>
          window.homeLayoutFixture.snapshot(),
        );
        assert.equal(
          repeated.calls.filter((x) => x[0] === "write:done").length,
          selected.calls.filter((x) => x[0] === "write:done").length + 1,
        );
        assert.equal(
          repeated.calls.filter((x) => x[0] === "notify").length,
          selected.calls.filter((x) => x[0] === "notify").length + 1,
        );
        await page.evaluate(() => window.homeLayoutFixture.external("table"));
        await page.waitForFunction(() =>
          document
            .querySelector("[role=radio][aria-checked=true]")
            ?.textContent.includes("Table"),
        );
        const external = await page.evaluate(() =>
          window.homeLayoutFixture.snapshot(),
        );
        await page.evaluate(() => window.homeLayoutFixture.denyNext());
        const rejectedError = page.waitForEvent("pageerror");
        await grid.click();
        assert.equal(
          (await rejectedError).message,
          "synthetic layout cookie denied",
        );
        const rejected = await page.evaluate(() =>
          window.homeLayoutFixture.snapshot(),
        );
        assert.equal(await table.getAttribute("aria-checked"), "true");
        assert.equal(rejected.cookieText, external.cookieText);
        assert.equal(
          rejected.calls.filter((x) => x[0] === "notify").length,
          external.calls.filter((x) => x[0] === "notify").length,
        );
        assert.deepEqual(errors, ["synthetic layout cookie denied"]);
        await grid.click();
        await page.waitForFunction(() =>
          document
            .querySelector("[role=radio][aria-checked=true]")
            ?.textContent.includes("Grid"),
        );
        const retry = await page.evaluate(() =>
          window.homeLayoutFixture.snapshot(),
        );
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth - innerWidth,
        );
        assert.ok(overflow <= 1);
        if (output) {
          await mkdir(output, { recursive: true });
          await page.screenshot({
            path: path.join(output, `layout-${width}.png`),
            fullPage: true,
          });
        }
        await page.evaluate(() => window.homeLayoutFixture.unmount());
        const unmounted = await page.evaluate(() =>
          window.homeLayoutFixture.snapshot(),
        );
        assert.equal(unmounted.listeners, 0);
        assert.equal(await page.getByRole("radiogroup").count(), 0);
        await page.evaluate(() => window.homeLayoutFixture.external("table"));
        const afterUnmount = await page.evaluate(() =>
          window.homeLayoutFixture.snapshot(),
        );
        assert.equal(
          afterUnmount.calls.filter((x) => x[0] === "notify").length,
          unmounted.calls.filter((x) => x[0] === "notify").length,
        );
        assert.equal(
          afterUnmount.calls.filter((x) => x[0] === "read").length,
          unmounted.calls.filter((x) => x[0] === "read").length,
        );
        await page.evaluate(() => window.homeLayoutFixture.mount());
        await page.getByRole("radio", { name: "Table", exact: true }).waitFor();
        assert.equal(
          await page
            .getByRole("radio", { name: "Table", exact: true })
            .getAttribute("aria-checked"),
          "true",
        );
        await page.waitForFunction(
          () => window.homeLayoutFixture.snapshot().listeners === 1,
        );
        const remounted = await page.evaluate(() =>
          window.homeLayoutFixture.snapshot(),
        );
        assert.equal(remounted.listeners, 1);
        await page.evaluate(() => window.homeLayoutFixture.unmount());
        assert.equal(
          (await page.evaluate(() => window.homeLayoutFixture.snapshot()))
            .listeners,
          0,
        );
        assert.deepEqual(errors, ["synthetic layout cookie denied"]);
        results.push({
          width,
          initial,
          selected,
          repeated,
          external,
          rejected,
          retry,
          unmounted,
          afterUnmount,
          remounted,
          overflow,
          expectedErrors: errors,
          limit:
            "Authored API-compatible setting hooks only; not original547562/provider/Home mount. All cookie reads/writes use the injected synthetic object.",
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
                "Actual source choice/field/descriptor/cookie adapter with real React and synthetic host/settings/document/location/row ports; GET-only loopback host",
              limits:
                "One expected synthetic cookie-denied error per width; no actual cookies, global preference or private provider/Home compatibility.",
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
