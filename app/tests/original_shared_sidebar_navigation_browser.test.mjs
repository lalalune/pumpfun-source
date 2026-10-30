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
  "actual React complete sharedSidebar responsive collapse route callback and controlled lifecycle at two widths",
  { timeout: 60000 },
  async () => {
    const temp = await mkdtemp(
      path.join(os.tmpdir(), "synthetic-shared-sidebar-"),
    );
    let browser, server;
    const output = process.env.PUMP_SIDEBAR_OUTPUT,
      requests = [],
      results = [];
    try {
      await build({
        entryPoints: [
          path.join(
            app,
            "tests/fixtures/shared-sidebar-navigation-browser.mjs",
          ),
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
            '<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic original sharedSidebar</title><style>body{font:16px system-ui;margin:16px}[hidden]{display:none!important}button,a{font:inherit;max-width:100%}p{overflow-wrap:anywhere}svg{width:16px;height:16px}ul{list-style:none;padding:0}li{margin:4px 0}a{display:flex;gap:8px;color:inherit}span{overflow-wrap:anywhere}button{margin:4px}output{display:block;font:12px monospace;overflow-wrap:anywhere}[data-state][data-collapsible]{width:var(--sidebar-width);max-width:100%}[data-state=collapsed][data-collapsible=icon]{width:var(--sidebar-width-icon)}[data-state][data-collapsible]>div:last-child{position:relative!important;top:auto!important;bottom:auto!important;width:100%;border:1px solid #aaa}[data-sidebar=sidebar]{width:100%;box-sizing:border-box}[data-diagnostic-drawer-root]{position:fixed;inset:0;z-index:10;background:#0004}[data-mobile=true]{width:var(--sidebar-width);max-width:90vw;height:100%;background:white;padding:8px;box-sizing:border-box}[data-diagnostic-tooltip]{display:block;font:11px system-ui}.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}@media(max-width:767px){[data-state][data-collapsible]{display:none}}@media(min-width:768px){[data-diagnostic-drawer-root]{display:none!important}}main{max-width:640px}h1{font-size:22px}h2{font-size:16px;overflow-wrap:anywhere}section{margin-top:16px;border:1px solid #aaa;padding:10px}article{margin:6px 0;padding:6px;background:#eee;overflow-wrap:anywhere}article[data-compact=true]{padding:2px}p,aside{overflow-wrap:anywhere}</style><div id="root"></div><script type="module" src="/fixture.js"></script></html>',
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
            page.evaluate(() => window.sharedSidebarFixture.snapshot()),
          trigger = page.getByTestId("outside-trigger");
        await trigger.waitFor();
        await page.waitForFunction(
          () => window.sharedSidebarFixture.snapshot().listeners === 1,
        );
        const initial = await snapshot();
        assert.deepEqual(initial.context, {
          open: false,
          openMobile: false,
          state: "collapsed",
        });
        // Actual same-batch sourceAPI: desktop captured-value updater differs from mobile Reactfunctional updater.
        await page.evaluate(() => window.sharedSidebarFixture.toggleTwice());
        await page.waitForFunction((w) => {
          const c = window.sharedSidebarFixture.snapshot().context;
          return c.open === w >= 768 && c.openMobile === false;
        }, width);
        const batched = await snapshot();
        assert.equal(batched.context.open, width >= 768);
        assert.equal(batched.context.openMobile, false);
        await trigger.click();
        await page.waitForFunction((w) => {
          const c = window.sharedSidebarFixture.snapshot().context;
          return w < 768 ? c.openMobile : !c.open;
        }, width);
        const firstToggle = await snapshot();
        assert.equal(
          firstToggle.events.at(-2)?.kind === "media" ||
            firstToggle.events.some((e) => e.kind === "media"),
          true,
        );
        assert.equal(
          firstToggle.events.filter((e) => e.kind === "media").at(-1).matches,
          width < 768,
        );
        const scope =
          width < 768
            ? page.locator("[data-mobile=true]")
            : page.locator("[data-state][data-collapsible]");
        assert.equal(await scope.isVisible(), true);
        const groupWidth = await scope.evaluate(
          (n) => n.getBoundingClientRect().width,
        );
        assert.equal(Math.round(groupWidth), width < 768 ? 288 : 56);
        // At desktop first toggle after batched expansion collapses; source still exposes original safe links.
        await scope.getByTestId("nav-explore").click();
        await page.waitForFunction(() => location.pathname === "/explore");
        assert.equal(
          await scope.getByTestId("nav-explore").getAttribute("aria-current"),
          "page",
        );
        assert.equal(
          await scope.getByTestId("nav-home").getAttribute("aria-current"),
          null,
        );
        const routed = await snapshot();
        assert.deepEqual(
          routed.events.filter((e) => e.kind === "navigate-callback").at(-1),
          { kind: "navigate-callback", key: "explore" },
        );
        assert.equal(routed.context.openMobile, width < 768);
        await scope.getByTestId("safe-action").click();
        assert.equal((await snapshot()).events.at(-1).kind, "safe-action");
        if (width < 768) {
          await scope.locator("[data-diagnostic-drawer-close]").click();
          await page.waitForFunction(
            () => !window.sharedSidebarFixture.snapshot().context.openMobile,
          );
        }
        // Native keyboard uses the source global effect and current mediaquery; no key/property override.
        await page.keyboard.press("Control+b");
        await page.waitForFunction((w) => {
          const c = window.sharedSidebarFixture.snapshot().context;
          return w < 768 ? c.openMobile : c.open;
        }, width);
        const keyboard = await snapshot();
        assert.equal(keyboard.listeners, 1);
        if (width < 768) {
          await page.setViewportSize({ width: 1280, height: 844 });
          assert.equal(
            await page.locator("[data-mobile=true]").isVisible(),
            false,
          );
          assert.equal((await snapshot()).context.openMobile, true);
          await page.keyboard.press("Control+b");
          await page.waitForFunction(
            () => window.sharedSidebarFixture.snapshot().context.open,
          );
          await page.setViewportSize({ width, height: 844 });
          assert.equal(
            await page.locator("[data-mobile=true]").isVisible(),
            true,
          );
          assert.equal((await snapshot()).context.openMobile, true);
          await page
            .locator("[data-mobile=true] [data-diagnostic-drawer-close]")
            .click();
          await page.waitForFunction(
            () => !window.sharedSidebarFixture.snapshot().context.openMobile,
          );
        }
        await page.evaluate(() => {
          window.sharedSidebarFixture.setDesktop(false);
          window.sharedSidebarFixture.setMobile(false);
          window.sharedSidebarFixture.patch({ preventTrigger: true });
        });
        await page.waitForFunction(
          () =>
            !window.sharedSidebarFixture.snapshot().context.open &&
            !window.sharedSidebarFixture.snapshot().context.openMobile,
        );
        await trigger.click();
        await page.waitForFunction((w) => {
          const c = window.sharedSidebarFixture.snapshot().context;
          return w < 768 ? c.openMobile : c.open;
        }, width);
        const prevented = await snapshot();
        assert.equal(
          prevented.events.filter((e) => e.kind === "trigger-callback").at(-1)
            .prevent,
          true,
        );
        if (width < 768) {
          await page
            .locator("[data-mobile=true] [data-diagnostic-drawer-close]")
            .click();
          await page.waitForFunction(
            () => !window.sharedSidebarFixture.snapshot().context.openMobile,
          );
        }
        await page.evaluate(() =>
          window.sharedSidebarFixture.patch({
            preventTrigger: false,
            denyTrigger: true,
          }),
        );
        await page.waitForFunction(
          () => window.sharedSidebarFixture.snapshot().state.denyTrigger,
        );
        const beforeDenial = await snapshot();
        await trigger.click();
        await page.waitForFunction(
          () =>
            window.sharedSidebarFixture
              .snapshot()
              .events.filter((e) => e.kind === "trigger-callback")
              .at(-1)?.deny,
        );
        const denied = await snapshot();
        assert.deepEqual(denied.context, beforeDenial.context);
        if (output) {
          await mkdir(output, { recursive: true });
          await page.screenshot({
            path: path.join(output, `sidebar-controller-${width}.png`),
            fullPage: true,
          });
        }
        await page.evaluate(() =>
          window.sharedSidebarFixture.patch({ present: false }),
        );
        await trigger.waitFor({ state: "detached" });
        await page.waitForFunction(
          () => window.sharedSidebarFixture.snapshot().listeners === 0,
        );
        const unmounted = await snapshot();
        await page.keyboard.press("Control+b");
        assert.equal((await snapshot()).events.length, unmounted.events.length);
        await page.evaluate(() =>
          window.sharedSidebarFixture.patch({
            present: true,
            controlled: true,
            controlledOpen: false,
            denyControlled: true,
            denyTrigger: false,
          }),
        );
        await trigger.waitFor();
        await page.waitForFunction(
          () => window.sharedSidebarFixture.snapshot().listeners === 1,
        );
        await page.evaluate(() =>
          window.sharedSidebarFixture.setDesktop((x) => !x),
        );
        await page.waitForFunction(
          () =>
            window.sharedSidebarFixture.snapshot().events.at(-1)?.kind ===
            "controlled-callback",
        );
        const controlledDenied = await snapshot();
        assert.equal(controlledDenied.context.open, false);
        assert.deepEqual(controlledDenied.events.at(-1), {
          kind: "controlled-callback",
          value: true,
          accepted: false,
        });
        await page.evaluate(() =>
          window.sharedSidebarFixture.patch({ denyControlled: false }),
        );
        await page.waitForFunction(
          () => !window.sharedSidebarFixture.snapshot().state.denyControlled,
        );
        await page.evaluate(() => window.sharedSidebarFixture.setDesktop(true));
        await page.waitForFunction(
          () => window.sharedSidebarFixture.snapshot().context.open,
        );
        const controlledAccepted = await snapshot();
        assert.equal(controlledAccepted.context.open, true);
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        );
        assert.equal(overflow, false);
        const expected = errors.filter(
            (e) => e === "SYNTHETIC trigger callback denial",
          ),
          unexpected = errors.filter(
            (e) => e !== "SYNTHETIC trigger callback denial",
          );
        assert.equal(expected.length, 1);
        assert.deepEqual(unexpected, []);
        await page.evaluate(() => window.sharedSidebarFixture.unmount());
        const cleanup = await snapshot();
        assert.equal(cleanup.listeners, 0);
        results.push({
          width,
          initial,
          batched,
          firstToggle,
          groupWidth,
          routed,
          keyboard,
          prevented,
          denied,
          unmounted,
          controlledDenied,
          controlledAccepted,
          cleanup,
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
