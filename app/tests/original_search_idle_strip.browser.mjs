import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { once } from "node:events";
import { mkdtemp, readFile, writeFile, mkdir, rm } from "node:fs/promises";
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
  { build, version: esbuildVersion } = createRequire(backend.resolve("tsx"))(
    "esbuild",
  ),
  hash = (b) => createHash("sha256").update(b).digest("hex");
test(
  "complete idle Discover strip: selection, native scroll lifecycle and supplied trader/coin display callbacks",
  { timeout: 45000 },
  async () => {
    const temp = await mkdtemp(path.join(os.tmpdir(), "search-idle-strip-")),
      output = process.env.PUMP_SEARCH_IDLE_STRIP_OUTPUT;
    const packet = {
      scope:
        "Synthetic supplied ordinary trader/coin rows and inert storage/provider capabilities only; real React/compiler/DOM scroll/observers. No actual storage/account/service/credential/session/cookie or navigation acquisition.",
      observations: [],
      pageErrors: [],
      unexpected: [],
      hostRequests: [],
    };
    let server, browser, page;
    const state = () => page.evaluate(() => window.idleStripHarness.state()),
      records = () => page.evaluate(() => window.idleStripHarness.records()),
      events = () => page.evaluate(() => window.idleStripHarness.events());
    const patch = async (p) => {
      const serial = await page.evaluate(() =>
        window.idleStripHarness.serial(),
      );
      await page.evaluate((p) => window.idleStripHarness.patch(p), p);
      await page.waitForFunction(
        (n) => window.idleStripHarness.serial() > n,
        serial,
      );
    };
    const observe = async (name) =>
      packet.observations.push({
        name,
        state: await state(),
        records: await records(),
        events: await events(),
      });
    try {
      const built = await build({
          absWorkingDir: app,
          entryPoints: ["tests/fixtures/search-idle-strip-browser.mjs"],
          bundle: true,
          platform: "browser",
          format: "esm",
          outfile: path.join(temp, "fixture.js"),
          define: { "process.env.NODE_ENV": '"development"' },
          metafile: true,
          logLevel: "silent",
        }),
        bundle = await readFile(path.join(temp, "fixture.js"));
      Object.assign(packet, {
        bundleSha256: hash(bundle),
        nodeVersion: process.version,
        reactVersion: frontend("react/package.json").version,
        reactDomVersion: frontend("react-dom/package.json").version,
        esbuildVersion,
      });
      packet.bundledInputs = [];
      for (const name of Object.keys(built.metafile.inputs).sort()) {
        const b = await readFile(path.resolve(app, name));
        packet.bundledInputs.push({
          path: name,
          bytes: b.length,
          sha256: hash(b),
        });
      }
      packet.inputs = [];
      for (const name of [
        "reconstruction/search-idle-strip/client.mjs",
        "reconstruction/search-idle-strip/contract.json",
        "scripts/original-search-idle-strip.mjs",
        "tests/fixtures/search-idle-strip-browser.mjs",
        "tests/original_search_idle_strip.browser.mjs",
        "tests/original_search_idle_strip.test.mjs",
        "pnpm-lock.yaml",
      ]) {
        const b = await readFile(path.join(app, name));
        packet.inputs.push({ path: name, bytes: b.length, sha256: hash(b) });
      }
      server = createServer((req, res) => {
        packet.hostRequests.push({ method: req.method, path: req.url });
        if (req.method !== "GET") {
          packet.unexpected.push("nonGET host request");
          res.writeHead(405).end();
        } else if (req.url === "/") {
          res.setHeader("content-type", "text/html");
          res.end(
            '<!doctype html><html><title>Inert original SearchDialog controller</title><button id="outside">Outside</button><div id="root"></div><script type="module" src="/fixture.js"></script></html>',
          );
        } else if (req.url === "/fixture.js") {
          res.setHeader("content-type", "text/javascript");
          res.end(bundle);
        } else {
          if (req.url !== "/favicon.ico")
            packet.unexpected.push("unknown host path");
          res.writeHead(404).end();
        }
      });
      server.listen(0, "127.0.0.1");
      await once(server, "listening");
      const base = "http://127.0.0.1:" + server.address().port;
      browser = await chromium.launch({
        headless: true,
        executablePath:
          process.env.PUMP_BROWSER_EXECUTABLE ?? chromium.executablePath(),
      });
      packet.chromiumVersion = browser.version();
      page = await browser.newPage();
      page.on("pageerror", (e) => packet.pageErrors.push(e.message));
      await page.addInitScript(() => {
        for (const name of [
          "localStorage",
          "sessionStorage",
          "Notification",
          "PushManager",
        ])
          Object.defineProperty(window, name, {
            get() {
              throw Error("Excluded real acquisition: " + name);
            },
            configurable: true,
          });
        Object.defineProperty(document, "cookie", {
          get() {
            throw Error("Excluded cookie read");
          },
          set() {
            throw Error("Excluded cookie write");
          },
          configurable: true,
        });
      });
      await page.route("**/*", (route) => {
        const u = new URL(route.request().url());
        if (
          u.origin === base &&
          ["/", "/fixture.js", "/favicon.ico"].includes(u.pathname) &&
          route.request().method() === "GET"
        )
          return route.continue();
        packet.unexpected.push(
          route.request().method() + " " + u.origin + u.pathname,
        );
        return route.abort();
      });
      await page.goto(base);
      await page.waitForFunction(
        () =>
          window.idleStripHarness &&
          document.querySelectorAll(".overflow-x-auto>div[aria-hidden=true]")
            .length === 5,
      );
      const strip = () => page.locator(".overflow-x-auto");
      const geometry = () =>
        strip().evaluate((n) => ({
          left: n.scrollLeft,
          width: n.clientWidth,
          total: n.scrollWidth,
        }));
      const tab = (name) => page.getByRole("tab", { name, exact: true });
      const previous = page.getByRole("button", {
        name: "web.pagination.previous_page",
        exact: true,
      });
      const next = page.getByRole("button", {
        name: "web.pagination.next_page",
        exact: true,
      });
      assert.equal(
        await tab("web.search.hot_coins").getAttribute("aria-selected"),
        "true",
      );
      assert.equal(await tab("web.search.top_traders").isDisabled(), true);
      assert.equal(
        (await events()).find((e) => e.type === "storage-get").key,
        "search.idle-strip",
      );
      await observe(
        "invalid supplied storage value defaults to hot-coins; source five loading skeletons and disabled unavailable trader tab",
      );
      await page.evaluate(() => window.idleStripHarness.load());
      await page.waitForFunction(
        () =>
          document.querySelectorAll("[data-testid=coin-avatar]").length === 6,
      );
      assert.equal(await previous.isDisabled(), true);
      assert.equal(await next.isEnabled(), true);
      const r = await records();
      assert.equal(r.liveCaps.at(-1).mint, "supplied-mint-5");
      assert.equal(r.charts.at(-1).length, 4);
      assert.equal(r.charts.at(-1)[2], undefined);
      assert.equal(r.charts[0][1], null);
      assert.equal(r.coinImpressions[0][1].sourceScreen, 9);
      assert.equal(r.coinImpressions[0][1].itemPosition, 0);
      assert.equal(r.coinImpressions[1][1].marketCap, 120.13);
      assert.equal(r.coinImpressions[0][2], undefined);
      assert.equal(
        r.coinImpressions[0][1].sourceElement,
        r.coinImpressions[0][3],
      );
      await observe(
        "loaded supplied coin rows pass exact live-cap, chart/default timestamp, prefetch and impression/index/rounded cap ports",
      );
      await next.click();
      await page.waitForFunction(
        () => document.querySelector(".overflow-x-auto").scrollLeft > 340,
      );
      const g = await geometry();
      assert.equal(g.width, 360);
      assert.equal(await previous.isEnabled(), true);
      await observe(
        "trusted next pages one native clientWidth with smooth motion; native scroll notification updates edge state",
      );
      await next.click();
      await page.waitForFunction(() => {
        const n = document.querySelector(".overflow-x-auto");
        return n.scrollLeft >= n.scrollWidth - n.clientWidth - 1;
      });
      await page.waitForFunction(
        () => document.querySelector("[data-search-strip-arrow=next]").disabled,
      );
      assert.equal(await next.isDisabled(), true);
      await observe(
        "native end threshold disables next at the actual scroll extent",
      );
      await patch({ reducedMotion: true });
      await previous.click();
      await page.waitForFunction(
        () => document.querySelector(".overflow-x-auto").scrollLeft < 400,
      );
      assert(
        (await events()).some(
          (e) =>
            e.type === "motion-query" &&
            e.query === "(prefers-reduced-motion: reduce)",
        ),
      );
      await previous.click();
      await page.waitForFunction(
        () =>
          document.querySelector("[data-search-strip-arrow=previous]").disabled,
      );
      await observe(
        "source reduced-motion port selects auto and trusted previous returns to native start",
      );
      await patch({ width: 2000 });
      await page.waitForFunction(
        () => document.querySelector("[data-search-strip-arrow=next]").disabled,
      );
      assert.equal(await previous.isDisabled(), true);
      await observe(
        "native ResizeObserver recomputes both edges when all supplied tiles fit",
      );
      await patch({ width: 360 });
      await page.waitForFunction(
        () =>
          !document.querySelector("[data-search-strip-arrow=next]").disabled,
      );
      const before = (await events()).length;
      await page.locator('a[href="/coin/supplied-mint-0"]').click();
      assert.deepEqual(
        (await events()).slice(before).map((e) => e.type),
        ["last-impression", "coin-click", "navigate", "host-link"],
      );
      await observe(
        "trusted coin selection retains last-impression then coin-click then current parent callback; host blocks actual navigation",
      );
      await patch({
        callbackB: true,
        liveCap: 0,
        chartLoading: true,
        chartError: "supplied-chart-error",
      });
      await page.waitForFunction(
        () =>
          document.querySelector("[data-testid=sparkline]")?.textContent ===
          "loading",
      );
      assert(
        (await records()).formats.some(
          (e) => e.kind === "cap" && e.value === 0,
        ),
      );
      const beforeB = (await events()).length;
      await page.locator('a[href="/coin/supplied-mint-1"]').click();
      assert.equal(
        (await events()).slice(beforeB).find((e) => e.type === "navigate")
          .label,
        "B",
      );
      await observe(
        "live-cap zero wins nullish fallback; supplied chart state and callback replacement flow without a service",
      );
      await tab("web.search.top_traders").click();
      await page.waitForFunction(
        () =>
          document.querySelectorAll("[data-testid=profile-display]").length ===
          6,
      );
      assert.equal((await state()).storageValue, "top-traders");
      const rr = await records();
      assert.equal(rr.profiles.at(-1).enabled, false);
      assert.equal(rr.profileDisplay[0].nameOverride, "supp...ess0");
      assert.equal(rr.profileDisplay[0].link, false);
      assert.equal(rr.profileDisplay[0].hoverCard, false);
      assert(rr.formats.some((e) => e.kind === "tone" && e.threshold === 0));
      await observe(
        "trusted tab selection writes only inert source key; full trader tile retains fallback name and supplied formatter/profile flags",
      );
      await patch({
        decorationEnabled: true,
        profileData: { resolved_avatar_decoration: "supplied-decoration" },
      });
      await page.waitForFunction(
        () =>
          document
            .querySelector("[data-testid=profile-display]")
            ?.getAttribute("data-decoration") === "supplied-decoration",
      );
      assert.equal((await records()).profiles.at(-1).enabled, true);
      assert(
        (await events()).some(
          (e) => e.type === "flag" && e.key === "webAvatarDecorations",
        ),
      );
      const tb = (await events()).length;
      await page.locator('a[href="/profile/suppliedWalletAddress0"]').click();
      assert.deepEqual(
        (await events()).slice(tb).map((e) => e.type),
        ["navigate", "host-link"],
      );
      await observe(
        "supplied decoration snapshot updates exact profile handoff; trader link invokes current callback without coin instrumentation",
      );
      await tab("web.search.hot_coins").click();
      await patch({ coins: [], coinLoading: false });
      await page.waitForFunction(() =>
        document.querySelector("[data-testid=search-top-traders]"),
      );
      assert.equal(
        await tab("web.search.hot_coins").getAttribute("aria-selected"),
        "false",
      );
      assert.equal((await state()).storageValue, "hot-coins");
      await observe(
        "availability fallback displays traders without overwriting picked hot-coins or synthetic persistence",
      );
      await patch({ traders: [], traderLoading: false });
      assert.equal(
        await page.getByTestId("empty").textContent(),
        "web.search.no_trending_coins",
      );
      assert.equal(await next.count(), 0);
      assert.equal(await tab("web.search.hot_coins").isDisabled(), true);
      await observe(
        "no available list preserves empty-message and disabled tabs with no arrow/strip",
      );
      await page.evaluate(() => window.idleStripHarness.load());
      await page.waitForFunction(() =>
        document.querySelector(
          "[data-testid=search-hot-coins] .overflow-x-auto",
        ),
      );
      assert.equal(
        await tab("web.search.hot_coins").getAttribute("aria-selected"),
        "true",
      );
      await observe(
        "retained user pick recovers when supplied availability returns",
      );
      await patch({ writeFails: true });
      await tab("web.search.top_traders").click();
      assert.equal(
        await tab("web.search.top_traders").getAttribute("aria-selected"),
        "true",
      );
      assert.equal((await state()).storageValue, "hot-coins");
      await observe(
        "synthetic storage write failure is caught after local selection update",
      );
      await patch({ readFails: true, writeFails: false, epoch: 1 });
      await page.waitForFunction(() =>
        document.querySelector(
          "[data-testid=search-hot-coins] .overflow-x-auto",
        ),
      );
      assert.equal(
        await tab("web.search.hot_coins").getAttribute("aria-selected"),
        "true",
      );
      await observe(
        "remounted source initializer catches synthetic storage read failure and uses default",
      );
      await page.evaluate(() =>
        window.idleStripHarness.resetStorage("top-traders"),
      );
      await patch({ readFails: false, epoch: 2, modeNoResize: true });
      await page.waitForFunction(() =>
        document.querySelector(
          "[data-testid=search-top-traders] .overflow-x-auto",
        ),
      );
      assert.equal(
        await tab("web.search.top_traders").getAttribute("aria-selected"),
        "true",
      );
      await observe(
        "valid synthetic persisted choice is read on remount with explicit unavailable ResizeObserver path",
      );
      await patch({ traders: [] });
      await page.waitForFunction(() =>
        document.querySelector(
          "[data-testid=search-hot-coins] .overflow-x-auto",
        ),
      );
      assert(
        (await events()).some(
          (e) => e.type === "mutation-observe" && e.options.childList === true,
        ),
      );
      await page.evaluate(() => window.idleStripHarness.unmount());
      assert.equal(await page.locator("#root").textContent(), "");
      const cleanup = await events();
      assert(cleanup.some((e) => e.type === "mutation-disconnect"));
      assert(cleanup.some((e) => e.type === "resize-disconnect"));
      await observe(
        "source store disconnects native observer subscriptions on replacement and unmount; missing ResizeObserver remains admitted",
      );
      assert.deepEqual(packet.pageErrors, []);
      assert.deepEqual(packet.unexpected, []);
      assert.deepEqual(packet.hostRequests, [
        { method: "GET", path: "/" },
        { method: "GET", path: "/fixture.js" },
      ]);
      packet.pass = true;
    } catch (e) {
      packet.failure = String(e.stack ?? e);
      throw e;
    } finally {
      if (page && !page.isClosed() && packet.failure)
        await page
          .screenshot({ path: path.join(temp, "failure.png") })
          .catch(() => {});
      await browser?.close();
      if (server) await new Promise((r) => server.close(r));
      if (output) {
        await mkdir(path.dirname(path.resolve(output)), { recursive: true });
        await writeFile(output, JSON.stringify(packet, null, 2) + "\n");
        if (packet.failure)
          try {
            await writeFile(
              output + ".png",
              await readFile(path.join(temp, "failure.png")),
            );
          } catch {}
      }
      await rm(temp, { recursive: true, force: true });
    }
  },
);
