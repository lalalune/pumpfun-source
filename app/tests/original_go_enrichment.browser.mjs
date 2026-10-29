import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { once } from "node:events";
import { mkdtemp, readFile, mkdir, writeFile, rm } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import os from "node:os";
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
  "actual React/compiler memo frames preserve enrichment data, identity, query handoffs and clock invalidation limits",
  { timeout: 30000 },
  async () => {
    const temp = await mkdtemp(
        path.join(os.tmpdir(), "synthetic-go-enrichment-"),
      ),
      output = process.env.PUMP_GO_ENRICHMENT_OUTPUT;
    const packet = {
      scope:
        "Isolated synthetic realReact composition only. Query/viewer/IPFS results are explicit ports; no HTTP data-provider, auth, live service, original query runtime, product UI, reward/accounting or native claim",
      observations: [],
      pageErrors: [],
      hostRequests: [],
      unexpected: [],
    };
    let server, browser, page;
    const state = () => page.evaluate(() => window.enrichmentHarness.state());
    const observe = async (name) => {
      const s = await state();
      packet.observations.push({ name, state: s });
      return s;
    };
    const update = async (method, arg) => {
      const before = await page.evaluate(() =>
        window.enrichmentHarness.serial(),
      );
      await page.evaluate(
        ({ method, arg }) => window.enrichmentHarness[method](arg),
        { method, arg },
      );
      await page.waitForFunction(
        (n) => window.enrichmentHarness.serial() > n,
        before,
      );
      return state();
    };
    try {
      const built = await build({
          absWorkingDir: app,
          entryPoints: ["tests/fixtures/go-enrichment-browser.mjs"],
          bundle: true,
          platform: "browser",
          format: "esm",
          outfile: path.join(temp, "fixture.js"),
          define: { "process.env.NODE_ENV": '"development"' },
          metafile: true,
          logLevel: "silent",
        }),
        bundle = await readFile(path.join(temp, "fixture.js"));
      packet.bundleSha256 = hash(bundle);
      packet.nodeVersion = process.version;
      packet.reactVersion = frontend("react/package.json").version;
      packet.reactDomVersion = frontend("react-dom/package.json").version;
      packet.esbuildVersion = esbuildVersion;
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
        "reconstruction/go-enrichment/client.mjs",
        "reconstruction/go-enrichment/contract.json",
        "scripts/original-go-enrichment.mjs",
        "tests/fixtures/go-enrichment-browser.mjs",
        "tests/original_go_enrichment.browser.mjs",
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
            '<!doctype html><html><title>Synthetic enrichment</title><div id="root"></div><script type="module" src="/fixture.js"></script></html>',
          );
        } else if (req.url === "/fixture.js") {
          res.setHeader("content-type", "text/javascript");
          res.end(bundle);
        } else {
          if (req.url !== "/favicon.ico")
            packet.unexpected.push("unknown host path " + req.url);
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
      const context = await browser.newContext();
      page = await context.newPage();
      page.on("pageerror", (e) => packet.pageErrors.push(e.message));
      await page.addInitScript(() => {
        for (const name of ["localStorage", "sessionStorage"])
          Object.defineProperty(window, name, {
            get() {
              throw Error("Browser storage excluded");
            },
            configurable: true,
          });
        Object.defineProperty(document, "cookie", {
          get() {
            throw Error("Cookie reads excluded");
          },
          set() {
            throw Error("Cookie writes excluded");
          },
          configurable: true,
        });
      });
      await page.route("**/*", (route) => {
        const r = route.request();
        if (new URL(r.url()).origin !== base || r.method() !== "GET") {
          packet.unexpected.push("unexpected browser request");
          return route.abort();
        }
        return route.continue();
      });
      await page.goto(base);
      await page.waitForFunction(() => window.enrichmentHarness?.serial() > 0);
      let s = await observe(
        "initial stubs/loading with explicit pending query results",
      );
      assert.equal(s.isEnriching, true);
      assert.equal(s.rows[0].acceptsSubmissions, true);
      assert.equal(s.rows[0].viewerIsCreator, false);
      assert.deepEqual(
        s.tokens.map((x) => x.mint),
        ["synthetic-coin", "reward-token"],
      );
      s = await update("tick");
      assert.equal(s.sameResult, true);
      let events = await page.evaluate(() => window.enrichmentHarness.events());
      let coins = events.filter((e) => e.type === "coin-port"),
        profiles = events.filter((e) => e.type === "profile-port");
      assert.equal(coins.at(-1).sameMints, true);
      assert.equal(coins.at(-1).sameOptions, true);
      assert.equal(profiles.at(-1).sameOptions, true);
      await observe(
        "stable render preserves frame/result and query argument identities",
      );
      const raw = {
        mint: "synthetic-coin",
        name: " LIVE ",
        symbol: " LIVE ",
        usd_market_cap: 12,
        total_supply: "1000000",
        base_decimals: 6,
        created_at: 10,
      };
      s = await update("scope", {
        coins: { data: [raw], isLoading: false, error: null },
        profiles: {
          data: [
            { address: "Creator", username: " first " },
            { address: "Creator", username: " last " },
          ],
          isPending: false,
        },
      });
      assert.equal(s.sameResult, false);
      assert.equal(s.isEnriching, false);
      assert.equal(s.rows[0].token.name, "LIVE");
      assert.equal(s.rows[0].creator.username, "last");
      assert.equal(s.tokens[0].price, 12);
      await observe(
        "query result arrival projects metadata and last matching profile",
      );
      const clockReads = (
        await page.evaluate(() => window.enrichmentHarness.events())
      ).filter((e) => e.type === "clock-port").length;
      await page.evaluate(() =>
        window.enrichmentHarness.setClock(
          Date.parse("2026-01-09T00:00:00.000Z"),
        ),
      );
      s = await update("tick");
      assert.equal(s.sameResult, true);
      assert.equal(s.rows[0].acceptsSubmissions, true);
      assert.equal(
        (await page.evaluate(() => window.enrichmentHarness.events())).filter(
          (e) => e.type === "clock-port",
        ).length,
        clockReads,
      );
      await observe(
        "clock alone does not invalidate original memo or create a timer",
      );
      s = await update("scope", {
        coins: { data: [raw], isLoading: false, error: null },
      });
      assert.equal(s.sameResult, false);
      assert.equal(s.rows[0].acceptsSubmissions, false);
      assert.equal(s.rows[0].allowsSubmissionMutations, true);
      await observe(
        "new data reference recomputes expiry admission with explicit clock",
      );
      s = await update("scope", { viewer: "cREATOR" });
      assert.equal(s.sameResult, false);
      assert.equal(s.rows[0].viewerIsCreator, true);
      assert.equal(s.rows[0].refundStatus, "claimed");
      await observe(
        "viewer address change recomputes only source display decisions",
      );
      s = await update("scope", {
        coins: { data: [raw], isLoading: false, error: "synthetic error" },
      });
      assert.equal(s.rows[0].token.name, "LIVE");
      assert.equal(s.isEnriching, false);
      await observe(
        "opaque query error does not invent enrichment error/loading policy",
      );
      await page.evaluate(() => {
        const first = window.enrichmentHarness.initialRow();
        window.enrichmentHarness.setRows([
          first,
          {
            ...first,
            taskId: "second",
            creatorAddress: "Second",
            coinAddress: "new-coin",
          },
        ]);
      });
      await page.waitForFunction(
        () => window.enrichmentHarness.state().rows.length === 2,
      );
      s = await observe(
        "new input rows update ordered token and unique creator handoffs",
      );
      assert.deepEqual(
        s.tokens.map((x) => x.mint),
        ["synthetic-coin", "reward-token", "new-coin"],
      );
      events = await page.evaluate(() => window.enrichmentHarness.events());
      assert.deepEqual(
        events.filter((e) => e.type === "profile-port").at(-1).addresses,
        ["Creator", "Second"],
      );
      s = await update("setRows", []);
      assert.deepEqual(s.rows, []);
      assert.deepEqual(s.tokens, []);
      assert.equal(s.isEnriching, false);
      events = await page.evaluate(() => window.enrichmentHarness.events());
      assert.deepEqual(
        events.filter((e) => e.type === "profile-port").at(-1).addresses,
        [],
      );
      assert.equal(
        events.filter((e) => e.type === "coin-port").at(-1).options.disabled,
        true,
      );
      await observe("empty inputs retain actual empty/disabled query calls");
      const viewerCalls = events.filter((e) => e.type === "viewer-port").length,
        profileCalls = events.filter((e) => e.type === "profile-port").length;
      s = await update("mountTokens");
      assert.equal(s.kind, "useBountyTokens");
      assert.deepEqual(s.rows, []);
      assert.deepEqual(
        s.tokens.map((x) => x.mint),
        ["synthetic-coin", "reward-token"],
      );
      packet.events = await page.evaluate(() =>
        window.enrichmentHarness.events(),
      );
      assert.equal(
        packet.events.filter((e) => e.type === "viewer-port").length,
        viewerCalls,
      );
      assert.equal(
        packet.events.filter((e) => e.type === "profile-port").length,
        profileCalls,
      );
      await observe(
        "separate actual token hook does not acquire viewer/profile data",
      );
      const sizes = new Set(
        packet.events.filter((e) => e.type === "memo").map((e) => e.size),
      );
      assert.deepEqual(
        [...sizes].sort((a, b) => a - b),
        [2, 13, 21, 32],
      );
      assert.deepEqual(packet.pageErrors, []);
      assert.deepEqual(packet.unexpected, []);
      assert.ok(
        packet.hostRequests.every((r) =>
          ["/", "/fixture.js", "/favicon.ico"].includes(r.path),
        ),
      );
      await page.evaluate(() => window.enrichmentHarness.unmount());
      packet.result = "PASS";
    } catch (error) {
      packet.result = "FAIL";
      packet.failure = { name: error.name, message: error.message };
      if (page)
        try {
          packet.events = await page.evaluate(() =>
            window.enrichmentHarness?.events(),
          );
          packet.lastState = await state();
        } catch {}
      throw error;
    } finally {
      if (output) {
        await mkdir(output, { recursive: true });
        await writeFile(
          path.join(output, "react-verification.json"),
          JSON.stringify(packet, null, 2) + "\n",
        );
      }
      if (browser) await browser.close();
      if (server) {
        server.closeAllConnections();
        server.close();
      }
      await rm(temp, { recursive: true, force: true });
    }
  },
);
