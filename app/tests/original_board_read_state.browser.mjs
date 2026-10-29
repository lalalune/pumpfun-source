import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { once } from "node:events";
import { mkdtemp, readFile, mkdir, writeFile, rm } from "node:fs/promises";
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
const hash = (b) => createHash("sha256").update(b).digest("hex");

test(
  "real React board frame: source gates, local reads, cache boundaries, callbacks, abort and cleanup",
  { timeout: 60000 },
  async () => {
    const temp = await mkdtemp(
      path.join(os.tmpdir(), "synthetic-board-frame-"),
    );
    const output = process.env.PUMP_BOARD_STATE_OUTPUT;
    let server, browser, page;
    const plans = [],
      requests = [],
      responses = [],
      aborted = [],
      observations = [],
      pageErrors = [],
      unexpected = [],
      hostRequests = [];
    const packet = {
      domain:
        "Isolated synthetic React/read proof, not product UI/data/services, original normalizer/provider, auth, live discovery or ranking",
      requests,
      responses,
      aborted,
      observations,
      pageErrors,
      unexpected,
      hostRequests,
    };
    const rows = {
      A: ["synthetic-A1", "synthetic-A2", "synthetic-A3"],
      T: ["synthetic-T1", "synthetic-T2", "synthetic-T3"],
      B: ["synthetic-B1"],
    };
    const plan = (name, { status = 200, group = "A" } = {}) => {
      const value = {
        name,
        status,
        body:
          status === 200
            ? JSON.stringify({
                entries: rows[group].map((m) => ({ m, n: m })),
                serverTs: 1000,
              })
            : '{"synthetic":"unavailable"}',
        release: null,
      };
      plans.push(value);
      return value;
    };
    const waitRequests = async (n) => {
      while (requests.length < n) await once(server, "api-request");
    };
    const waitAbort = async (n) => {
      while (aborted.length < n) await once(server, "api-abort");
    };
    const state = () => page.evaluate(() => window.boardHarness.state());
    const waitState = async (expected) => {
      await page.waitForFunction((expected) => {
        const s = window.boardHarness.state();
        return (
          s &&
          Object.entries(expected).every(
            ([k, v]) => JSON.stringify(s[k]) === JSON.stringify(v),
          )
        );
      }, expected);
      return state();
    };
    const observe = async (name) => {
      const value = await state();
      observations.push({ name, state: value, requestCount: requests.length });
      return value;
    };
    const update = async (method, patch) => {
      const serial = await page.evaluate(() => window.boardHarness.serial());
      await page.evaluate(
        ({ method, patch }) => window.boardHarness[method](patch),
        { method, patch },
      );
      await page.waitForFunction(
        (serial) => window.boardHarness.serial() > serial,
        serial,
      );
    };
    try {
      const compilation = await build({
        absWorkingDir: app,
        entryPoints: [path.join(app, "tests/fixtures/board-read-state.mjs")],
        bundle: true,
        platform: "browser",
        format: "esm",
        outfile: path.join(temp, "fixture.js"),
        define: { "process.env.NODE_ENV": '"development"' },
        logLevel: "silent",
        metafile: true,
      });
      const bundle = await readFile(path.join(temp, "fixture.js"));
      packet.bundleSha256 = hash(bundle);
      packet.bundledInputs = [];
      for (const name of Object.keys(compilation.metafile.inputs).sort()) {
        const bytes = await readFile(path.resolve(app, name));
        packet.bundledInputs.push({
          path: name,
          sha256: hash(bytes),
          bytes: bytes.length,
        });
      }
      packet.nodeVersion = process.version;
      packet.esbuildVersion = createRequire(backend.resolve("tsx"))(
        "esbuild",
      ).version;
      const files = [
        "reconstruction/board-read-state/client.mjs",
        "reconstruction/board-read-state/contract.json",
        "scripts/original-board-read-state.mjs",
        "reconstruction/search-session/session.mjs",
        "reconstruction/search-planner/planner.mjs",
        "reconstruction/market-boards/request.mjs",
        "tests/fixtures/board-read-state.mjs",
        "tests/original_board_read_state.browser.mjs",
        "pnpm-lock.yaml",
      ];
      packet.inputs = [];
      for (const name of files) {
        const b = await readFile(path.join(app, name));
        packet.inputs.push({ path: name, sha256: hash(b), bytes: b.length });
      }
      packet.reactVersion = frontend("react/package.json").version;
      packet.reactDomVersion = frontend("react-dom/package.json").version;
      server = createServer((req, res) => {
        hostRequests.push({ method: req.method, pathAndQuery: req.url });
        if (req.method !== "GET") {
          res.writeHead(405).end();
          return;
        }
        if (req.url === "/") {
          res.setHeader("content-type", "text/html");
          res.end(
            '<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic board frame</title><div id="root"></div><script type="module" src="/fixture.js"></script></html>',
          );
          return;
        }
        if (req.url === "/fixture.js") {
          res.setHeader("content-type", "text/javascript");
          res.end(bundle);
          return;
        }
        if (!req.url.startsWith("/boards/")) {
          res.writeHead(404).end();
          return;
        }
        const next = plans.shift();
        if (!next) {
          unexpected.push({ reason: "unplanned GET", pathAndQuery: req.url });
          res.writeHead(503).end("{}");
          return;
        }
        const id = requests.length + 1;
        requests.push({
          id,
          case: next.name,
          method: req.method,
          pathAndQuery: req.url,
          headers: {
            contentType: req.headers["content-type"] ?? null,
            accept: req.headers.accept ?? null,
            pumpSource: req.headers["x-pump-source"] ?? null,
            pumpPlatform: req.headers["x-pump-platform"] ?? null,
          },
        });
        res.on("finish", () =>
          responses.push({
            id,
            case: next.name,
            status: res.statusCode,
            contentType: "application/json",
            body: next.body,
          }),
        );
        res.on("close", () => {
          if (!res.writableEnded) {
            aborted.push({
              id,
              case: next.name,
              completedResponse: false,
              headersSent: res.headersSent,
            });
            server.emit("api-abort");
          }
        });
        next.release = () => {
          if (res.destroyed) return;
          res.statusCode = next.status;
          res.setHeader("content-type", "application/json");
          res.end(next.body);
        };
        server.emit("api-request");
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
      page.on("pageerror", (e) => pageErrors.push(e.message));
      await page.addInitScript(() => {
        for (const name of ["localStorage", "sessionStorage"])
          Object.defineProperty(window, name, {
            get() {
              throw Error("Real browser storage is excluded");
            },
            configurable: true,
          });
        Object.defineProperty(document, "cookie", {
          get() {
            throw Error("Real cookie reads are excluded");
          },
          set() {
            throw Error("Cookie writes are excluded");
          },
          configurable: true,
        });
      });
      await page.route("**/*", (route) => {
        const r = route.request();
        if (new URL(r.url()).origin !== base || r.method() !== "GET") {
          unexpected.push({
            reason: "unexpected browser request",
            method: r.method(),
            url: r.url(),
          });
          return route.abort();
        }
        return route.continue();
      });
      await page.goto(base);
      await page.waitForFunction(
        () => window.boardHarness?.state() && window.boardHarness.serial() > 0,
      );
      assert.equal(requests.length, 0);
      assert.equal((await state()).loading, true);
      await observe("auth-not-ready suppresses initial board read");

      let p = plan("first movers read");
      await update("scope", {
        viewer: {
          address: "synthetic-viewer-A",
          userId: "synthetic-user-A",
          authReady: true,
        },
      });
      await waitRequests(1);
      assert.equal((await state()).loading, true);
      let url = new URL(requests[0].pathAndQuery, base);
      assert.equal(url.pathname, "/boards/movers");
      assert.equal(url.searchParams.get("limit"), "150");
      assert.equal(url.searchParams.get("chains"), "solana");
      assert.equal(url.searchParams.has("offset"), false);
      assert.equal(url.searchParams.get("userId"), "synthetic-viewer-A");
      assert.equal(url.searchParams.get("pumpUserId"), "synthetic-user-A");
      assert.equal(url.searchParams.get("session_start_timestamp_ms"), "0");
      assert.equal(url.searchParams.has("country"), false);
      p.release();
      await waitState({
        coins: rows.A.slice(0, 2),
        loading: false,
        error: false,
        hasMorePages: true,
        servedCoins: [],
      });
      await observe("default local slice and served mover order");

      p = plan("background failure", { status: 503 });
      let pending = page.evaluate(() =>
        window.boardHarness.refetch({ background: true }),
      );
      await waitRequests(2);
      assert.equal((await state()).loading, false);
      p.release();
      await pending;
      await observe("background failure preserves current rows");
      assert.deepEqual((await state()).coins, rows.A.slice(0, 2));
      assert.equal((await state()).error, false);
      p = plan("cache-hit foreground failure", { status: 503 });
      pending = page.evaluate(() =>
        window.boardHarness.fetchCoins(false, false),
      );
      await waitRequests(3);
      assert.equal((await state()).loading, false);
      p.release();
      await pending;
      assert.equal((await state()).error, false);
      await observe(
        "cache hit still refreshes but suppresses loading/error clear",
      );
      await page.evaluate(() => window.boardHarness.setClock(121000));
      p = plan("exact TTL boundary", { status: 503 });
      pending = page.evaluate(() =>
        window.boardHarness.fetchCoins(false, false),
      );
      await waitRequests(4);
      assert.equal((await state()).loading, false);
      p.release();
      await pending;
      await observe("age exactly120000 remains cached");
      await page.evaluate(() => window.boardHarness.setClock(121001));
      p = plan("expired foreground failure", { status: 503 });
      pending = page.evaluate(() =>
        window.boardHarness.fetchCoins(false, false),
      );
      await waitRequests(5);
      await waitState({ loading: true });
      p.release();
      await pending;
      await waitState({
        coins: [],
        loading: false,
        error: true,
        hasMorePages: false,
      });
      await observe(
        "age120001 expires then foreground failure publishes keyed error",
      );

      p = plan("trending recovery", { group: "T" });
      await update("render", { sort: "trending", chain: "base" });
      await waitRequests(6);
      url = new URL(requests[5].pathAndQuery, base);
      assert.equal(url.pathname, "/boards/trending");
      assert.equal(url.searchParams.get("ranking"), "social");
      assert.equal(url.searchParams.get("window"), "1h");
      assert.equal(url.searchParams.get("hot"), "label");
      assert.ok(url.searchParams.get("chains").includes("solana"));
      assert.notEqual(url.searchParams.get("chains"), "eip155:8453");
      p.release();
      await waitState({
        coins: rows.T.slice(0, 2),
        servedCoins: rows.T,
        error: false,
        loading: false,
        hasMorePages: true,
      });
      await observe(
        "trending ignores selected chain and retains full served rows",
      );
      const beforeAddressKey = (await state()).requestKey;
      p = plan("viewer address background refresh", { status: 503 });
      await update("scope", {
        viewer: {
          address: "synthetic-viewer-B",
          userId: "synthetic-user-A",
          authReady: true,
        },
      });
      await waitRequests(7);
      assert.equal((await state()).loading, false);
      p.release();
      await waitState({ loading: false, error: false });
      assert.equal((await state()).requestKey, beforeAddressKey);
      await observe(
        "address gate refreshes in background without inventing key ownership",
      );
      await page.evaluate(() => window.boardHarness.saveRefetch());
      await update("scope", {
        viewer: {
          address: "synthetic-viewer-B",
          userId: "synthetic-user-B",
          authReady: true,
        },
      });
      assert.equal(requests.length, 7);
      await observe(
        "userId-only change does not add an automatic source effect read",
      );
      p = plan("old callback retains captured user", { status: 503 });
      pending = page.evaluate(() =>
        window.boardHarness.callSavedRefetch({ background: true }),
      );
      await waitRequests(8);
      assert.equal(
        new URL(requests[7].pathAndQuery, base).searchParams.get("pumpUserId"),
        "synthetic-user-A",
      );
      p.release();
      await pending;
      p = plan("current callback uses latest user", { status: 503 });
      pending = page.evaluate(() =>
        window.boardHarness.refetch({ background: true }),
      );
      await waitRequests(9);
      assert.equal(
        new URL(requests[8].pathAndQuery, base).searchParams.get("pumpUserId"),
        "synthetic-user-B",
      );
      p.release();
      await pending;
      await observe("old/current callback capture boundary");

      p = plan("second local page", { group: "T" });
      await update("render", { offset: 2 });
      await waitRequests(10);
      assert.equal(
        new URL(requests[9].pathAndQuery, base).searchParams.has("offset"),
        false,
      );
      p.release();
      await waitState({
        coins: rows.T.slice(2),
        servedCoins: rows.T,
        loading: false,
        hasMorePages: false,
      });
      await observe("local page offset is absent from capped server request");
      p = plan("force-local-filter full handoff", { group: "T" });
      await update("render", { offset: 0, forceLocalFiltering: true });
      await waitRequests(11);
      p.release();
      await waitState({
        coins: rows.T,
        servedCoins: rows.T,
        loading: false,
        hasMorePages: true,
      });
      await observe(
        "forceLocalFiltering hands full normalized array to outer filter owner",
      );

      const old = plan("superseded request", { group: "A" });
      await update("render", { chain: "ethereum" });
      await waitRequests(12);
      const current = plan("current request", { group: "B" });
      await update("render", { chain: "solana" });
      await waitRequests(13);
      await waitAbort(1);
      assert.equal(aborted[0].case, old.name);
      current.release();
      await waitState({ coins: rows.B, servedCoins: rows.B, loading: false });
      await observe("native abort and current response commit");
      p = plan("unmount current read", { group: "A" });
      await update("render", { sort: "featured" });
      await waitRequests(14);
      await page.evaluate(() => window.boardHarness.unmount());
      await waitAbort(2);
      assert.equal(aborted[1].case, p.name);
      observations.push({
        name: "actual pending read aborted on cleanup",
        requestCount: requests.length,
      });

      const seed = [{ mint: "synthetic-T1", created_timestamp: 20 }];
      await page.evaluate(
        (seed) =>
          window.boardHarness.mount({ sort: "trending", initialCoins: seed }),
        seed,
      );
      await waitState({
        coins: ["synthetic-T1"],
        servedCoins: ["synthetic-T1"],
        loading: false,
      });
      assert.equal(requests.length, 14);
      await observe("real React seed initialization without ready auth");
      p = plan("seeded first read is background", { group: "T" });
      await update("scope", {
        viewer: {
          address: "synthetic-viewer-C",
          userId: "synthetic-user-C",
          authReady: true,
        },
      });
      await waitRequests(15);
      assert.equal((await state()).loading, false);
      assert.deepEqual((await state()).coins, ["synthetic-T1"]);
      p.release();
      await waitState({
        coins: rows.T.slice(0, 2),
        loading: false,
        hasMorePages: true,
      });
      await observe(
        "seeded first background read preserves prefill until response",
      );
      await page.evaluate(() => window.boardHarness.unmount());
      packet.events = await page.evaluate(() => window.boardHarness.events());
      assert.equal(
        packet.events.filter((e) => e.type === "seed-port").length,
        1,
      );
      assert.equal(
        packet.events.find((e) => e.type === "seed-port").argumentCount,
        1,
      );
      assert.ok(
        packet.events
          .filter((e) => e.type === "parse-port")
          .every((e) => e.argumentCount === 1),
      );
      assert.ok(
        packet.events
          .filter((e) => e.type === "poll-port")
          .every((e) => e.enabled === false),
      );
      assert.equal(
        packet.events.filter((e) => e.type === "unexpected-interval").length,
        0,
      );
      assert.equal(
        packet.events.filter((e) => e.type === "excluded-error").length,
        0,
      );
      assert.ok(
        requests.every(
          (r) =>
            r.method === "GET" &&
            r.headers.contentType === "application/json" &&
            r.headers.pumpSource === null &&
            r.headers.pumpPlatform === null,
        ),
      );
      assert.deepEqual(pageErrors, []);
      assert.deepEqual(unexpected, []);
      assert.equal(plans.length, 0);
      packet.completedResponses = responses.length;
      packet.abortedReads = aborted.length;
      packet.result = "PASS";
    } catch (error) {
      packet.result = "FAIL";
      packet.failure = { name: error.name, message: error.message };
      if (page)
        try {
          packet.events = await page.evaluate(() =>
            window.boardHarness?.events(),
          );
          packet.lastState = await state();
        } catch {}
      throw error;
    } finally {
      if (output) {
        await mkdir(output, { recursive: true });
        await writeFile(
          path.join(output, "browser-verification.json"),
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
