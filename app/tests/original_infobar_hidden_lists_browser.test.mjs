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
  "actual React complete hidden-InfoBar list/callback/coerce workflow with syntheticlocalports at two widths",
  { timeout: 60000 },
  async () => {
    const temp = await mkdtemp(
      path.join(os.tmpdir(), "synthetic-infobar-hidden-"),
    );
    let browser, server;
    const output = process.env.PUMP_INFOBAR_HIDDEN_OUTPUT,
      requests = [],
      results = [];
    try {
      await build({
        entryPoints: [
          path.join(app, "tests/fixtures/infobar-hidden-lists-browser.mjs"),
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
            '<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic InfoBar hidden lists</title><style>body{font:16px system-ui;margin:16px}main{max-width:640px}h1{font-size:22px}h2{font-size:18px}section{border:1px solid #aaa;padding:12px;margin-top:16px}button{font:inherit;max-width:100%;margin:4px;padding:6px}ul{list-style:none;margin:8px 0;padding:0;display:flex;gap:6px;flex-wrap:wrap}li{max-width:100%}p{overflow-wrap:anywhere}</style><div id="root"></div><script type="module" src="/fixture.js"></script></html>',
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
        const tokens = page.locator(
            '[data-setting-id="feed.infoBar.hiddenTokens"]',
          ),
          profiles = page.locator(
            '[data-setting-id="feed.infoBar.hiddenProfiles"]',
          ),
          snapshot = () =>
            page.evaluate(() => window.hiddenInfoBarFixture.snapshot()),
          names = async (list) =>
            list
              .getByRole("button")
              .evaluateAll((nodes) =>
                nodes
                  .filter((n) => n.hasAttribute("aria-label"))
                  .map((n) => n.getAttribute("aria-label")),
              );
        await tokens.getByRole("list", { name: "Hidden tokens" }).waitFor();
        assert.deepEqual(await names(tokens), [
          "Unhide BETA",
          "Unhide synthetic-abbreviation",
          "Unhide ALPHA",
        ]);
        assert.deepEqual(await names(profiles), [
          "Unhide @bob",
          "Unhide @alice",
        ]);
        const initial = await snapshot();
        assert.ok(
          initial.formats.some(
            (x) => x[0] === "truncate" && x[2] === 4 && x[3] === 4,
          ),
        );
        assert.ok(
          initial.formats.some(
            (x) => x[0] === "normalize" && x[2] === "coin-symbol",
          ),
        );
        assert.ok(
          initial.formats.some(
            (x) => x[0] === "normalize" && x[2] === "user-name",
          ),
        );
        if (output) {
          await mkdir(output, { recursive: true });
          await page.screenshot({
            path: path.join(output, `hidden-lists-${width}.png`),
            fullPage: true,
          });
        }
        await page.evaluate(() => window.hiddenInfoBarFixture.addToken());
        await tokens
          .getByRole("button", { name: "Unhide LATEST", exact: true })
          .waitFor();
        const added = await snapshot();
        assert.equal(Object.keys(added.tokens).length, 4);
        await page.evaluate(() => window.hiddenInfoBarFixture.fail(true));
        await tokens
          .getByRole("button", { name: "Unhide ALPHA", exact: true })
          .click();
        for (let n = 0; n < 20 && errors.length === 0; n++)
          await page.waitForTimeout(20);
        assert.deepEqual(errors, ["SYNTHETIC local setter denied"]);
        const denied = await snapshot();
        assert.deepEqual(denied.tokens, added.tokens);
        assert.equal(
          await tokens
            .getByRole("button", { name: "Unhide ALPHA", exact: true })
            .count(),
          1,
        );
        await page.evaluate(() => window.hiddenInfoBarFixture.fail(false));
        await tokens
          .getByRole("button", { name: "Unhide ALPHA", exact: true })
          .click();
        await page.waitForFunction(
          () => !("0xab" in window.hiddenInfoBarFixture.snapshot().tokens),
        );
        const unhidden = await snapshot();
        assert.ok(unhidden.tokens["synthetic-latest"]);
        assert.equal(Object.keys(unhidden.tokens).length, 3);
        assert.deepEqual(await names(tokens), [
          "Unhide LATEST",
          "Unhide BETA",
          "Unhide synthetic-abbreviation",
        ]);
        const functional = unhidden.events.filter(
          (x) => x[0] === "write-request",
        );
        assert.ok(
          functional.some(
            (x) => x[1] === "feed.infoBar.hiddenTokens" && x[2] === "function",
          ),
        );
        assert.ok(
          unhidden.events.some(
            (x) => x[0] === "latest-read" && x[2].includes("synthetic-latest"),
          ),
        );
        await profiles
          .getByRole("button", { name: "Unhide @bob", exact: true })
          .focus();
        await page.keyboard.press("Enter");
        await page.waitForFunction(
          () => !("0xbb" in window.hiddenInfoBarFixture.snapshot().profiles),
        );
        const profileRemoved = await snapshot();
        assert.deepEqual(Object.keys(profileRemoved.profiles), [
          "synthetic-alice",
        ]);
        assert.deepEqual(await names(profiles), ["Unhide @alice"]);
        await tokens
          .getByRole("button", { name: "Show all hidden", exact: true })
          .click();
        await page.waitForFunction(
          () =>
            Object.keys(window.hiddenInfoBarFixture.snapshot().tokens)
              .length === 0,
        );
        assert.equal(await tokens.getByRole("list").count(), 0);
        assert.equal(await tokens.locator("[data-description]").count(), 0);
        assert.equal(
          await tokens.locator("[data-note]").innerText(),
          "Synthetic note: positions are separate",
        );
        const tokensCleared = await snapshot();
        assert.equal(Object.keys(tokensCleared.profiles).length, 1);
        await profiles
          .getByRole("button", { name: "Show all hidden", exact: true })
          .click();
        await page.waitForFunction(
          () =>
            Object.keys(window.hiddenInfoBarFixture.snapshot().profiles)
              .length === 0,
        );
        await tokens.getByText("None hidden", { exact: true }).waitFor();
        assert.equal(await profiles.getByRole("list").count(), 0);
        assert.equal(
          await page
            .getByRole("button", { name: "Show all hidden", exact: true })
            .count(),
          0,
        );
        const allCleared = await snapshot();
        assert.deepEqual(allCleared.tokens, {});
        assert.deepEqual(allCleared.profiles, {});
        assert.ok(
          allCleared.events.filter(
            (x) => x[0] === "write-request" && x[2] === "object",
          ).length === 2,
        );
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth - innerWidth,
        );
        assert.ok(overflow <= 1);
        assert.deepEqual(errors, ["SYNTHETIC local setter denied"]);
        if (output)
          await page.screenshot({
            path: path.join(output, `cleared-lists-${width}.png`),
            fullPage: true,
          });
        await page.evaluate(() => window.hiddenInfoBarFixture.unmount());
        assert.equal(await page.locator("main").count(), 0);
        const unmounted = await snapshot();
        assert.deepEqual(errors, ["SYNTHETIC local setter denied"]);
        results.push({
          width,
          initial,
          added,
          denied,
          unhidden,
          profileRemoved,
          tokensCleared,
          allCleared,
          unmounted,
          overflow,
          expectedSyntheticSetterFailure: errors,
          unexpectedErrors: [],
          limits:
            "Source fields/descriptor/coerce/callbacks with actualReact/compiler and explicit synthetic in-memory local-setting/bucket/render/translation/format capabilities. No original private state/persistence/normalization/nativeInfoBar claim.",
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
                "GET-only ownedfixture; safe synthetic token/profile-shaped labels, not acquired data. No actualcookies/storage/sessions/credentials/userdata/profilelookups/tenantrequests/preferencemutation; no originalframework/storage/provider/native/API/pixel/security/completion claim.",
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
