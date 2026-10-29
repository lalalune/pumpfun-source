import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { once } from "node:events";
import { mkdtemp, readFile, rm, mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
const app = fileURLToPath(new URL("..", import.meta.url));
const frontend = createRequire(
  new URL("../packages/frontend/package.json", import.meta.url),
);
const backend = createRequire(
  new URL("../packages/backend/package.json", import.meta.url),
);
const { chromium } = frontend("@playwright/test"),
  { build } = createRequire(backend.resolve("tsx"))("esbuild");
const deferred = () => {
  let resolve;
  const promise = new Promise((r) => {
    resolve = r;
  });
  return { promise, resolve };
};

test(
  "actual React selector → owned namespace GET → synthetic cookie/provider/refresh lifecycle",
  { timeout: 60000 },
  async () => {
    const temp = await mkdtemp(
      path.join(os.tmpdir(), "synthetic-language-switch-"),
    );
    const output = process.env.PUMP_LANGUAGE_OUTPUT;
    let server,
      browser,
      releaseCatalog = deferred(),
      reachedCatalog = deferred();
    const requests = [],
      results = [];
    try {
      const contract = JSON.parse(
        await readFile(
          path.join(app, "reconstruction/language-switch/contract.json"),
          "utf8",
        ),
      );
      const dictionary = Object.fromEntries(
        contract.selectorNamespaces.map((name) => [name, { synthetic: true }]),
      );
      await build({
        entryPoints: [
          path.join(app, "tests/fixtures/language-switch-browser.mjs"),
        ],
        bundle: true,
        platform: "browser",
        format: "esm",
        outfile: path.join(temp, "fixture.js"),
        define: { "process.env.NODE_ENV": '"development"' },
        logLevel: "silent",
      });
      const bundle = await readFile(path.join(temp, "fixture.js"));
      server = createServer(async (request, response) => {
        requests.push({ method: request.method, url: request.url });
        response.setHeader("Cache-Control", "no-store");
        if (request.method !== "GET") {
          response.writeHead(405).end();
          return;
        }
        const url = new URL(request.url, "http://owned.invalid");
        if (url.pathname === "/fixture.js") {
          response.setHeader("Content-Type", "text/javascript");
          response.end(bundle);
        } else if (url.pathname === "/") {
          response.setHeader("Content-Type", "text/html");
          response.end(
            '<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic language fixture</title><style>body{font:16px system-ui;margin:16px}main{max-width:640px}button{font:inherit;padding:8px}.options-port{max-height:480px;overflow:auto;display:grid;gap:4px}.select-port{max-width:100%}</style><div id="root"></div><script type="module" src="/fixture.js"></script></html>',
          );
        } else if (/^\/api\/i18n\/(fr|de|it)$/.test(url.pathname)) {
          if (url.pathname.endsWith("/fr")) {
            reachedCatalog.resolve();
            await releaseCatalog.promise;
          }
          response.setHeader("Content-Type", "application/json");
          response.end(JSON.stringify(dictionary));
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
        releaseCatalog = deferred();
        reachedCatalog = deferred();
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
            errors.push("Unexpected request: " + request.url());
            return route.abort();
          }
          return route.continue();
        });
        await page.goto(base);
        const trigger = page.getByTestId("language-select-trigger");
        await trigger.waitFor();
        assert.match(await trigger.innerText(), /English/);
        await trigger.click();
        await page.getByTestId("language-option-fr").click();
        await reachedCatalog.promise;
        await page.waitForFunction(
          () =>
            document.querySelector('[data-testid="language-select-trigger"]')
              .disabled,
        );
        assert.equal(await trigger.getAttribute("aria-busy"), "true");
        const fetching = await page.evaluate(() =>
          window.languageFixture.snapshot(),
        );
        assert.equal(fetching.cookieText, "");
        assert.equal(fetching.language, "en");
        releaseCatalog.resolve();
        await page.waitForFunction(() =>
          window.languageFixture
            .snapshot()
            .steps.some((entry) => entry[0] === "change:start"),
        );
        const pendingProvider = await page.evaluate(() =>
          window.languageFixture.snapshot(),
        );
        assert.match(pendingProvider.cookieText, /^pump_locale=fr;/);
        assert.equal(
          pendingProvider.steps.some((entry) => entry[0] === "refresh"),
          false,
        );
        assert.equal(await trigger.isDisabled(), true);
        await page.evaluate(() => window.languageFixture.finishProvider());
        await page.waitForFunction(
          () =>
            !document.querySelector('[data-testid="language-select-trigger"]')
              .disabled,
        );
        assert.match(await trigger.innerText(), /Français/);
        const success = await page.evaluate(() =>
          window.languageFixture.snapshot(),
        );
        assert.deepEqual(
          success.steps
            .filter((entry) =>
              ["cookie", "change:start", "change:end", "refresh"].includes(
                entry[0],
              ),
            )
            .map((entry) => entry[0]),
          ["cookie", "change:start", "change:end", "refresh"],
        );
        const apiReadCount = () =>
          requests.filter((entry) => entry.url.startsWith("/api/i18n/")).length;
        const readsBeforeSame = apiReadCount();
        await trigger.click();
        await page.getByTestId("language-option-fr").click();
        assert.equal(apiReadCount(), readsBeforeSame);
        await page.evaluate(() => window.languageFixture.rejectNext());
        const rejectionEvent = page.waitForEvent("pageerror");
        await trigger.click();
        await page.getByTestId("language-option-de").click();
        await page.waitForFunction(
          () =>
            !document.querySelector('[data-testid="language-select-trigger"]')
              .disabled,
        );
        await page.waitForFunction(() =>
          window.languageFixture
            .snapshot()
            .cookieText.startsWith("pump_locale=de;"),
        );
        const rejected = await page.evaluate(() =>
          window.languageFixture.snapshot(),
        );
        assert.equal(rejected.language, "fr");
        assert.equal(
          rejected.steps.filter((entry) => entry[0] === "refresh").length,
          1,
        );
        assert.equal(
          (await rejectionEvent).message,
          "synthetic provider rejection",
        );
        assert.deepEqual(errors, ["synthetic provider rejection"]);
        const readsBeforeRetry = apiReadCount();
        await trigger.click();
        await page.getByTestId("language-option-de").click();
        await page.waitForFunction(
          () => window.languageFixture.snapshot().language === "de",
        );
        await page.waitForFunction(
          () =>
            !document.querySelector('[data-testid="language-select-trigger"]')
              .disabled,
        );
        assert.equal(apiReadCount(), readsBeforeRetry); // Successful catalog cache is reused after provider failure.
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth - innerWidth,
        );
        assert.ok(overflow <= 1);
        if (output) {
          await mkdir(output, { recursive: true });
          await page.screenshot({
            path: path.join(output, `language-${width}.png`),
            fullPage: true,
          });
        }
        await page.evaluate(() => window.languageFixture.holdProvider());
        await trigger.click();
        await page.getByTestId("language-option-it").click();
        await page.waitForFunction(() =>
          window.languageFixture
            .snapshot()
            .steps.some(
              (entry) => entry[0] === "change:start" && entry[1] === "it",
            ),
        );
        await page.evaluate(() => window.languageFixture.unmount());
        assert.equal(
          await page.getByTestId("language-select-trigger").count(),
          0,
        );
        await page.evaluate(() => window.languageFixture.finishProvider());
        await page.waitForFunction(
          () => window.languageFixture.snapshot().language === "it",
        );
        await page.waitForFunction(
          () =>
            window.languageFixture
              .snapshot()
              .steps.filter((entry) => entry[0] === "refresh").length === 3,
        );
        const afterUnmount = await page.evaluate(() =>
          window.languageFixture.snapshot(),
        );
        assert.equal(
          afterUnmount.steps.filter((entry) => entry[0] === "refresh").length,
          3,
        );
        results.push({
          width,
          fetching,
          pendingProvider,
          success,
          rejected,
          afterUnmount,
          overflow,
          expectedErrors: errors,
          limit:
            "Source has no cancellation on unmount; supplied cookie/provider/refresh work still completes. No real cookie or provider implementation.",
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
                "Actual source-adapted selector/client; authored Select/i18n/document/location/router ports and synthetic loopback dictionaries",
              limits:
                "One expected uncaught synthetic provider rejection per width is preserved, not reported as zero errors. No real cookies, locale backend, original private provider or product/global translation parity.",
            },
            null,
            2,
          ) + "\n",
        );
    } finally {
      releaseCatalog.resolve();
      await browser?.close();
      if (server) await new Promise((resolve) => server.close(resolve));
      await rm(temp, { recursive: true, force: true });
    }
  },
);
