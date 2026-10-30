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
  "actual React original Settings URL/event/controller/conditional-mount workflow at two widths",
  { timeout: 60000 },
  async () => {
    const temp = await mkdtemp(
      path.join(os.tmpdir(), "synthetic-settings-entry-"),
    );
    let browser, server;
    const output = process.env.PUMP_SETTINGS_ENTRY_OUTPUT,
      requests = [],
      results = [];
    try {
      await build({
        entryPoints: [
          path.join(app, "tests/fixtures/settings-entry-flow-browser.mjs"),
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
        } else if (req.url?.startsWith("/?") || req.url === "/") {
          res.setHeader("Content-Type", "text/html");
          res.end(
            '<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic Settings entry workflow</title><style>body{font:16px system-ui;margin:16px}main{max-width:640px}h1{font-size:22px}h2{font-size:16px;overflow-wrap:anywhere}section{margin-top:16px;border:1px solid #aaa;padding:10px}button{display:block;margin:8px 0;max-width:100%}p{overflow-wrap:anywhere}article{margin:6px 0;padding:6px;background:#eee;overflow-wrap:anywhere}article[data-compact=true]{padding:2px}p,aside{overflow-wrap:anywhere}</style><div id="root"></div><script type="module" src="/fixture.js"></script></html>',
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
        await page.goto(base + "/?keep=one&keep=two#synthetic-fragment");

        const snapshot = () =>
          page.evaluate(() => window.settingsEntryFixture.snapshot());
        await page.waitForFunction(
          () => window.settingsEntryFixture?.snapshot().queryRead > 0,
        );
        const initial = await snapshot();
        assert.equal(initial.listeners, 0);
        assert.equal(initial.loadCount, 0);
        assert.deepEqual(initial.schema, { settings: true, setting: true });
        assert.deepEqual(initial.options, {
          history: "replace",
          clearOnDefault: true,
        });
        await page.evaluate(() => {
          history.replaceState(
            { synthetic: "history-state" },
            "",
            location.href,
          );
          window.settingsEntryFixture.open({
            section: "feed",
            settingId: "feed.synthetic",
          });
        });
        const disabledOpen = await snapshot();
        assert.equal(disabledOpen.listeners, 0);
        assert.equal(disabledOpen.loadCount, 0);
        assert.equal(await page.locator("[data-modal]").count(), 0);
        const dispatch = disabledOpen.events.find((e) => e.kind === "dispatch"),
          before = disabledOpen.events.find((e) => e.kind === "replace-before"),
          after = disabledOpen.events.find((e) => e.kind === "replace-after");
        assert.equal(dispatch.type, "pump:open-settings");
        assert.equal(dispatch.href, after.href);
        assert.notEqual(before.href, dispatch.href);
        assert.deepEqual(dispatch.detail, {
          section: "feed",
          settingId: "feed.synthetic",
        });
        const u = new URL(dispatch.href);
        assert.deepEqual(u.searchParams.getAll("keep"), ["one", "two"]);
        assert.equal(u.hash, "#synthetic-fragment");
        assert.deepEqual(disabledOpen.state, { synthetic: "history-state" });
        await page.evaluate(() => window.settingsEntryFixture.flag(true));
        await page.locator("[data-modal]").waitFor();
        await page.waitForFunction(
          () => window.settingsEntryFixture.snapshot().mounts.length === 1,
        );
        const opened = await snapshot();
        assert.equal(opened.listeners, 1);
        assert.equal(opened.loadCount, 1);
        assert.deepEqual(opened.props, {
          section: "feed",
          focusSettingId: "feed.synthetic",
        });
        const firstId = await page
          .locator("[data-modal]")
          .getAttribute("data-modal");
        await page.locator("[data-action=section]").click();
        await page.waitForFunction(
          () =>
            window.settingsEntryFixture.snapshot().props.section === "privacy",
        );
        const changed = await snapshot();
        assert.equal(
          await page.locator("[data-modal]").getAttribute("data-modal"),
          firstId,
        );
        assert.deepEqual(changed.changes.at(-1), {
          settings: "privacy",
          setting: "privacy.synthetic",
        });
        assert.equal(new URL(changed.href).searchParams.get("keep"), "one");
        await page.locator("[data-action=empty]").click();
        await page.waitForFunction(
          () =>
            window.settingsEntryFixture.snapshot().props.focusSettingId === "",
        );
        const emptyCallback = await snapshot();
        assert.deepEqual(emptyCallback.changes.at(-1), {
          settings: "feed",
          setting: "",
        });
        assert.equal(
          new URL(emptyCallback.href).searchParams.has("setting"),
          true,
        );
        await page.evaluate(() =>
          window.settingsEntryFixture.open({
            section: "privacy",
            settingId: "",
          }),
        );
        await page.waitForFunction(
          () =>
            window.settingsEntryFixture.snapshot().props.section === "privacy",
        );
        const emptyHelper = await snapshot();
        assert.equal(
          new URL(emptyHelper.href).searchParams.has("setting"),
          true,
        );
        assert.deepEqual(emptyHelper.changes.at(-1), {
          settings: "privacy",
          setting: "",
        });
        assert.equal(new URL(emptyHelper.href).searchParams.get("setting"), "");
        assert.equal(emptyHelper.props.focusSettingId, "");
        // The host callback's nullish behavior can re-add an empty string after the helper deleted it.
        assert.ok(
          emptyHelper.events.some(
            (e) =>
              e.kind === "dispatch" &&
              e.detail.settingId === "" &&
              !new URL(e.href).searchParams.has("setting"),
          ),
        );
        if (output) {
          await mkdir(output, { recursive: true });
          await page.screenshot({
            path: path.join(output, `entry-open-${width}.png`),
            fullPage: true,
          });
        }
        await page.locator("[data-action=close]").click();
        await page.locator("[data-modal]").waitFor({ state: "detached" });
        const closed = await snapshot();
        assert.deepEqual(closed.changes.at(-1), {
          settings: null,
          setting: null,
        });
        assert.equal(closed.unmounts.length, 1);
        assert.equal(new URL(closed.href).searchParams.has("settings"), false);
        assert.equal(new URL(closed.href).searchParams.has("setting"), false);
        assert.equal(closed.listeners, 1);
        await page.evaluate(() =>
          window.settingsEntryFixture.open({ section: "feed" }),
        );
        await page.locator("[data-modal]").waitFor();
        const reopened = await snapshot();
        assert.notEqual(
          await page.locator("[data-modal]").getAttribute("data-modal"),
          firstId,
        );
        assert.equal(reopened.loadCount, 1);
        assert.deepEqual(reopened.changes.at(-1), {
          settings: "feed",
          setting: null,
        });
        assert.equal(reopened.mounts.length, 2);
        await page.evaluate(() => window.settingsEntryFixture.flag(false));
        await page.locator("[data-modal]").waitFor({ state: "detached" });
        await page.waitForFunction(
          () => window.settingsEntryFixture.snapshot().listeners === 0,
        );
        const gated = await snapshot();
        assert.equal(gated.unmounts.length, 2);
        const count = gated.changes.length;
        await page.evaluate(() =>
          window.settingsEntryFixture.open({
            section: "privacy",
            settingId: "privacy.synthetic",
          }),
        );
        const noListener = await snapshot();
        assert.equal(noListener.changes.length, count);
        assert.equal(
          new URL(noListener.href).searchParams.get("settings"),
          "privacy",
        );
        assert.equal(noListener.listeners, 0);
        await page.evaluate(() => window.settingsEntryFixture.flag(true));
        await page.locator("[data-modal]").waitFor();
        await page.waitForFunction(
          () => window.settingsEntryFixture.snapshot().listeners === 1,
        );
        const flagRestored = await snapshot();
        assert.equal(flagRestored.mounts.length, 3);
        await page.evaluate(() => window.settingsEntryFixture.unmount());
        await page.waitForFunction(
          () =>
            window.settingsEntryFixture.snapshot().listeners === 0 &&
            window.settingsEntryFixture.snapshot().subscribers === 0,
        );
        const unmounted = await snapshot();
        assert.equal(unmounted.unmounts.length, 3);
        assert.equal(unmounted.flagSubscribers, 0);
        const changesBefore = unmounted.changes.length;
        await page.evaluate(() =>
          window.settingsEntryFixture.open({ section: "feed" }),
        );
        assert.equal((await snapshot()).changes.length, changesBefore);
        assert.equal(await page.locator("[data-modal]").count(), 0);
        await page.evaluate(() => window.settingsEntryFixture.remount());
        await page.locator("[data-modal]").waitFor();
        await page.waitForFunction(
          () => window.settingsEntryFixture.snapshot().listeners === 1,
        );
        const remounted = await snapshot();
        assert.equal(remounted.mounts.length, 4);
        assert.equal(remounted.loadCount, 1);
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth > innerWidth,
        );
        assert.equal(overflow, false);
        assert.deepEqual(errors, []);
        if (output)
          await page.screenshot({
            path: path.join(output, `entry-remount-${width}.png`),
            fullPage: true,
          });
        results.push({
          width,
          initial,
          disabledOpen,
          opened,
          changed,
          emptyCallback,
          emptyHelper,
          closed,
          reopened,
          gated,
          noListener,
          flagRestored,
          unmounted,
          remounted,
          errors,
          overflow,
        });
        await page.evaluate(() => window.settingsEntryFixture.unmount());
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
