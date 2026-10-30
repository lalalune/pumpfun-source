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
  "complete ordinary SearchDialog controller: real React rerenders, source query/result handoff, keys/focus, ordered submit/paste and cancellation",
  { timeout: 45000 },
  async () => {
    const temp = await mkdtemp(
        path.join(os.tmpdir(), "search-dialog-controller-"),
      ),
      output = process.env.PUMP_SEARCH_DIALOG_CONTROLLER_OUTPUT;
    const packet = {
      scope:
        "Synthetic original-source controller proof only. Actual React/compiler/DOM; all queries/data/readers/probes/recents/flags/analytics/navigation/renderers are supplied inert capabilities. No live request, credential, cookie, storage, session, provider or protected action.",
      observations: [],
      pageErrors: [],
      unexpected: [],
      hostRequests: [],
    };
    let server, browser, page;
    const state = () => page.evaluate(() => window.searchDialogHarness.state()),
      events = () => page.evaluate(() => window.searchDialogHarness.events());
    const wait = async (expected) => {
      await page.waitForFunction((e) => {
        const s = window.searchDialogHarness.state();
        return (
          s &&
          Object.entries(e).every(
            ([k, v]) => JSON.stringify(s[k]) === JSON.stringify(v),
          )
        );
      }, expected);
      return state();
    };
    const patch = async (p) => {
      const serial = await page.evaluate(() =>
        window.searchDialogHarness.serial(),
      );
      await page.evaluate((p) => window.searchDialogHarness.patch(p), p);
      await page.waitForFunction(
        (n) => window.searchDialogHarness.serial() > n,
        serial,
      );
    };
    const observe = async (name) =>
      packet.observations.push({
        name,
        state: await state(),
        events: await events(),
        resolverCalls: await page.evaluate(() =>
          window.searchDialogHarness.resolveCalls(),
        ),
      });
    const input = () =>
      page.getByRole("textbox", { name: "Synthetic search input" });
    const open = async () => {
      await page.keyboard.press("Control+k");
      await wait({ open: true });
      await input().waitFor({ state: "visible" });
    };
    try {
      const built = await build({
          absWorkingDir: app,
          entryPoints: ["tests/fixtures/search-dialog-controller-browser.mjs"],
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
        "reconstruction/search-dialog-controller/client.mjs",
        "reconstruction/search-dialog-controller/contract.json",
        "scripts/original-search-dialog-controller.mjs",
        "tests/fixtures/search-dialog-controller-browser.mjs",
        "tests/original_search_dialog_controller.browser.mjs",
        "tests/original_search_dialog_controller.test.mjs",
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
          window.searchDialogHarness &&
          window.searchDialogHarness.state().keyListeners === 1,
      );
      let s = await state();
      assert.equal(s.open, false);
      assert.equal(s.trending.enabled, false);
      assert.equal(s.pnl.enabled, false);
      assert.equal(s.group.enabled, false);
      assert.equal(s.group.initialPageParam, 0);
      assert.equal(s.group.staleTime, 30000);
      assert.equal(s.termsKey, "recently-searched-terms");
      await observe(
        "closed owner mounts once with supplied queries disabled and no provider requests",
      );
      await page.locator("#outside").click();
      await open();
      assert.equal(
        await input().evaluate((e) => e === document.activeElement),
        true,
      );
      s = await state();
      assert.equal(s.trending.enabled, true);
      assert.equal(s.pnl.enabled, true);
      assert.equal(s.trending.staleTime, 300000);
      assert.equal(s.trending.gcTime, 600000);
      assert.equal(s.pnl.refetchOnMount, false);
      assert.equal(s.trending.refetchOnWindowFocus, false);
      await observe(
        "trusted mounted shortcut opens and source ref focuses input; exact query defaults",
      );
      await patch({
        recentCoins: [
          { mint: "coin-a" },
          { mint: "coin-b" },
          { mint: "name.near", chain_id: "near:mainnet" },
        ],
        recentCards: [{ nftAddress: "card-a", viewedAt: 3 }],
        viewedAt: { "coin-a": 2, "coin-b": 5 },
        hydratedCoins: [{ mint: "coin-a", name: "hydrated" }],
        chainFlags: { near: true, hex: true },
        nearCoins: [{ mint: "name.near", name: "near hydrated" }],
        trending: [{ mint: "trend" }],
        leaders: { entries: [{ userId: "synthetic-leader" }] },
      });
      assert.deepEqual(
        await page
          .locator('[data-testid="search-recently-viewed"] button')
          .allTextContents(),
        [
          "common.clear",
          "Coin coin-b",
          "Card card-a",
          "Coin coin-a",
          "Coin name.near",
        ],
      );
      s = await state();
      assert.deepEqual(s.hydration, {
        mints: ["coin-a", "coin-b"],
        includeNsfw: true,
        disabled: false,
      });
      assert.deepEqual(s.near, [
        {
          queryKey: [
            "coin",
            {
              coinAddress: "name.near",
              includeDataLivestream: false,
              chainId: "near:mainnet",
            },
          ],
          retry: false,
          refetchOnWindowFocus: false,
        },
      ]);
      assert.deepEqual(s.coinUpdates, [
        "coin-a",
        "coin-b",
        "name.near",
        "trend",
      ]);
      await observe(
        "recent hydration branches, source-key lookup, card merge and descending view order",
      );
      const coins = Array.from({ length: 6 }, (_, i) => ({
          mint: "result-" + i,
          search_priority: true,
        })),
        users = Array.from({ length: 5 }, (_, i) => ({ userId: "user-" + i })),
        groups = [{ userId: "group-0" }, { userId: "group-1" }];
      await patch({ coins, users, groupRows: groups });
      await input().fill("alpha");
      await wait({ query: "alpha" });
      s = await state();
      assert.deepEqual(s.mixed.coins.rows, [
        "result-0",
        "result-1",
        "result-2",
        "result-3",
      ]);
      assert.equal(s.mixed.coins.hasMore, true);
      assert.equal(s.mixed.users.rows.length, 4);
      assert.equal(s.mixed.squads.rows.length, 2);
      assert.equal(s.group.queryKey[1], "alpha");
      assert.equal(s.group.enabled, true);
      assert.equal(s.debounce.ms, 500);
      await observe(
        "mixed sections use priority rows, four-row limits and actual query input",
      );
      await page.getByRole("button", { name: "users:5", exact: true }).click();
      await wait({ tab: "users" });
      assert.equal(await page.locator('[data-kind="user"]').count(), 5);
      await patch({ users: [] });
      await wait({ tab: "all" });
      await observe(
        "selected user tab falls back to all when provider results disappear",
      );
      await patch({ mixed: false, coins: [], users: [], groupRows: groups });
      await wait({ tab: "squads" });
      assert.equal(await page.locator('[data-kind="group"]').count(), 2);
      await observe(
        "nonmixed fallback chooses first populated category with projected group rows",
      );
      await patch({ debounced: "prior" });
      s = await state();
      assert.equal(s.group.queryKey[1], "prior");
      const request = await page.evaluate(() =>
        window.searchDialogHarness.groupRequest(20),
      );
      assert.deepEqual(request, {
        result: [{ userId: "synthetic-group" }],
        forwardedSignal: true,
        offset: 20,
        limit: 20,
        clientMatches: true,
      });
      const calls = await events();
      assert(
        calls.some(
          (e) =>
            e.type === "group-cache" &&
            e.key[1] === "synthetic-group" &&
            e.value.projected === true,
        ),
      );
      assert.equal(
        await page.evaluate(() =>
          window.searchDialogHarness.groupNext(Array(20).fill(0), [
            Array(250).fill(0),
            Array(250).fill(0),
          ]),
        ),
        500,
      );
      assert.equal(
        await page.evaluate(() =>
          window.searchDialogHarness.groupNext(Array(20).fill(0), [
            Array(260).fill(0),
            Array(260).fill(0),
          ]),
        ),
        undefined,
      );
      assert.equal(
        await page.evaluate(() =>
          window.searchDialogHarness.groupNext(Array(19).fill(0), [
            Array(19).fill(0),
          ]),
        ),
        undefined,
      );
      assert.deepEqual(
        await page.evaluate(() =>
          window.searchDialogHarness.groupSelect({ pages: [[1, 2], [3]] }),
        ),
        [1, 2, 3],
      );
      await page.evaluate(() =>
        Promise.all([
          window.searchDialogHarness.queryRead("trending"),
          window.searchDialogHarness.queryRead("pnl"),
        ]),
      );
      await observe(
        "group query forwards signal/client/offset, hydrates profile cache and retains strict greater-than500 cap",
      );
      await patch({
        debounced: "synthetic-reject",
        groupError: { synthetic: true },
      });
      assert.equal(
        await page.evaluate(async () => {
          try {
            await window.searchDialogHarness.groupRequest(0);
          } catch (e) {
            return e.message;
          }
        }),
        "Synthetic group reader failure",
      );
      await observe(
        "group reader rejection propagates; no invented retry/error UI or provider transport",
      );
      await patch({
        debounced: null,
        mixed: true,
        chainFlags: { near: false, hex: false },
        terms: Array.from({ length: 25 }, (_, i) => "term-" + i),
      });
      await input().fill("  alpha & beta=one  ");
      await page.getByRole("button", { name: "Submit supplied input" }).click();
      await wait({ open: false, query: "" });
      s = await state();
      assert.equal(s.terms.length, 20);
      assert.equal(s.terms[0], "alpha & beta=one");
      assert(
        (await events()).some(
          (e) =>
            e.type === "push" &&
            e.args[0] === "/explore?q=alpha%20%26%20beta%3Done",
        ),
      );
      await observe(
        "accepted ordered submit trims, closes/resets, caps recents and supplies encoded Explore navigation",
      );
      await open();
      await input().fill("11111111111111111111111111111111");
      await page.getByRole("button", { name: "Submit supplied input" }).click();
      await page.waitForFunction(
        () => window.searchDialogHarness.resolveCalls().length === 1,
      );
      await input().fill("new draft");
      await page.waitForFunction(
        () => window.searchDialogHarness.resolveCalls()[0].aborted,
      );
      await page.evaluate(() =>
        window.searchDialogHarness.release(1, {
          kind: "coin",
          mint: "stale-mint",
        }),
      );
      await wait({ open: true, query: "new draft" });
      assert(
        !(await events()).some(
          (e) => e.type === "push" && e.args[0] === "/coin/stale-mint",
        ),
      );
      await observe(
        "editing aborts supplied resolver and stale completion cannot close or navigate newer draft",
      );
      await input().fill("before OLD after");
      await input().evaluate((e) => e.setSelectionRange(7, 10));
      await page.evaluate(() =>
        window.searchDialogHarness.paste("11111111111111111111111111111111"),
      );
      await page.waitForFunction(
        () => window.searchDialogHarness.resolveCalls().length === 2,
      );
      assert.equal(
        await input().inputValue(),
        "before 11111111111111111111111111111111 after",
      );
      await page.evaluate(() =>
        window.searchDialogHarness.release(2, {
          kind: "coin",
          mint: "synthetic-pasted-mint",
        }),
      );
      await wait({ open: false, query: "" });
      const tail = (await events())
        .filter((e) =>
          ["mint-paste", "search", "last-click", "coin-click", "push"].includes(
            e.type,
          ),
        )
        .slice(-5);
      assert.deepEqual(
        tail.map((e) => e.type),
        ["mint-paste", "search", "last-click", "coin-click", "push"],
      );
      assert.equal(tail.at(-1).args[0], "/coin/synthetic-pasted-mint");
      await observe(
        "event-supplied paste preserves selection and exact analytics/click/navigation order without clipboard acquisition",
      );
      await open();
      await input().fill("0x" + "a".repeat(40));
      await page.getByRole("button", { name: "Submit supplied input" }).click();
      await page.waitForFunction(
        () => window.searchDialogHarness.resolveCalls().length === 3,
      );
      await page.evaluate(() =>
        window.searchDialogHarness.release(3, {
          kind: "coin",
          mint: "synthetic-evm-mint",
        }),
      );
      await wait({ open: false });
      assert(
        (await events()).some(
          (e) => e.type === "push" && e.args[0] === "/coin/synthetic-evm-mint",
        ),
      );
      await observe(
        "retained EVM readonly handler consumes supplied definitive coin result",
      );
      await patch({ chainFlags: { near: true, hex: true } });
      await open();
      await input().fill("synthetic.near");
      await page.getByRole("button", { name: "Submit supplied input" }).click();
      await page.waitForFunction(
        () => window.searchDialogHarness.resolveCalls().length === 4,
      );
      await page.evaluate(() =>
        window.searchDialogHarness.release(4, { kind: "external_wallet" }),
      );
      await wait({ open: false });
      assert(
        (await events()).some(
          (e) => e.type === "push" && e.args[0] === "/profile/synthetic.near",
        ),
      );
      await observe(
        "retained Near gate and definitive external-wallet navigation use supplied results only",
      );
      await open();
      await input().fill("0x" + "b".repeat(45));
      await page.getByRole("button", { name: "Submit supplied input" }).click();
      await page.waitForFunction(
        () => window.searchDialogHarness.resolveCalls().length === 5,
      );
      const hex = await page.evaluate(
        () => window.searchDialogHarness.resolveCalls()[4].term,
      );
      assert.equal(hex.length, 66);
      await page.evaluate(() =>
        window.searchDialogHarness.release(5, {
          kind: "coin",
          mint: "synthetic-hex-mint",
        }),
      );
      await wait({ open: false });
      await observe(
        "retained gated long-hex normalization and handler consume supplied definitive result",
      );
      await open();
      await patch({ mixed: true, coins, users, groupRows: groups });
      await input().fill("row selection");
      await wait({ tab: "all" });
      await page
        .getByRole("button", { name: "users user-0", exact: true })
        .click();
      await wait({ open: false });
      assert.notEqual((await state()).terms[0], "row selection");
      await observe(
        "ordinary result selection closes/resets without invented row navigation",
      );
      await open();
      await input().fill("11111111111111111111111111111111");
      await page.getByRole("button", { name: "Submit supplied input" }).click();
      await page.waitForFunction(
        () => window.searchDialogHarness.resolveCalls().length === 6,
      );
      await page.getByRole("button", { name: "Close supplied dialog" }).click();
      await wait({ open: false, query: "" });
      assert.equal(
        (
          await page.evaluate(() => window.searchDialogHarness.resolveCalls())
        )[5].aborted,
        true,
      );
      await page.evaluate(() =>
        window.searchDialogHarness.release(6, {
          kind: "coin",
          mint: "closed-stale",
        }),
      );
      await observe(
        "supplied Dialog close calls actual abort/reset/open-state callback",
      );
      await open();
      await input().fill("11111111111111111111111111111111");
      await page.getByRole("button", { name: "Submit supplied input" }).click();
      await page.waitForFunction(
        () => window.searchDialogHarness.resolveCalls().length === 7,
      );
      await page.evaluate(() => window.searchDialogHarness.unmount());
      assert.equal((await state()).keyListeners, 0);
      assert.equal(
        (
          await page.evaluate(() => window.searchDialogHarness.resolveCalls())
        )[6].aborted,
        false,
      );
      await observe(
        "unmount removes actual keyboard listener; no unsupported resolver-unmount cancellation is added",
      );
      assert.deepEqual(packet.pageErrors, []);
      assert.deepEqual(packet.unexpected, []);
      assert.equal(
        packet.hostRequests.filter((r) => r.path === "/fixture.js").length,
        1,
      );
      assert(packet.hostRequests.every((r) => r.method === "GET"));
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
