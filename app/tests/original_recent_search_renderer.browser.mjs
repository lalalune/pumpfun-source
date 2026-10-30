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
  "complete RecentTerms actual React workflow: visible slice, expansion, supplied query join/pending/fallback/profile and clear callbacks",
  { timeout: 45000 },
  async () => {
    const temp = await mkdtemp(
        path.join(os.tmpdir(), "recent-search-renderer-"),
      ),
      output = process.env.PUMP_RECENT_SEARCH_RENDERER_OUTPUT;
    const packet = {
      scope:
        "Synthetic supplied ordinary terms and query/hydration/profile/renderer results only. Real React/compiler/DOM; no actual history storage, account query, service, credential/session/cookie/clipboard or navigation acquisition.",
      observations: [],
      pageErrors: [],
      unexpected: [],
      hostRequests: [],
    };
    let server, browser, page;
    const state = () => page.evaluate(() => window.recentSearchHarness.state()),
      records = () => page.evaluate(() => window.recentSearchHarness.records()),
      events = () => page.evaluate(() => window.recentSearchHarness.events());
    const patch = async (p) => {
      const serial = await page.evaluate(() =>
        window.recentSearchHarness.serial(),
      );
      await page.evaluate((p) => window.recentSearchHarness.patch(p), p);
      await page.waitForFunction(
        (n) => window.recentSearchHarness.serial() > n,
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
          entryPoints: ["tests/fixtures/recent-search-renderer-browser.mjs"],
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
        "reconstruction/recent-search-renderer/client.mjs",
        "reconstruction/recent-search-renderer/contract.json",
        "scripts/original-recent-search-renderer.mjs",
        "tests/fixtures/recent-search-renderer-browser.mjs",
        "tests/original_recent_search_renderer.browser.mjs",
        "tests/original_recent_search_renderer.test.mjs",
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
          window.recentSearchHarness &&
          document.querySelectorAll('[data-testid="recent-search-pending"]')
            .length === 2,
      );
      const values = await page.evaluate(
        () => window.recentSearchHarness.values,
      );
      let s = await state();
      assert.equal(s.termCount, 6);
      assert.deepEqual(s.hydration, {
        mints: [values.SOL],
        includeNsfw: true,
        disabled: false,
      });
      assert.deepEqual(s.near, { mints: [], enabled: false });
      assert.deepEqual(s.groupQueries, [
        {
          key: ["supplied-group", values.GROUP],
          enabled: true,
          staleTime: 30000,
        },
      ]);
      assert.equal(
        await page
          .getByRole("link", { name: "plain & text", exact: true })
          .getAttribute("href"),
        "/explore?q=plain%20%26%20text",
      );
      assert.equal(s.updates.arity, 1);
      await observe(
        "collapsed visible slice3 alone feeds group/coin candidates and source pending/text presentation",
      );
      await page
        .getByRole("button", { name: "common.see_all", exact: true })
        .click();
      await page.waitForFunction(
        () =>
          document.querySelectorAll('[data-testid="recent-search-pending"]')
            .length === 4,
      );
      s = await state();
      assert.deepEqual(s.hydration.mints, [values.SOL, values.EVM]);
      assert.deepEqual(s.near, { mints: [values.NEAR], enabled: true });
      assert.equal(
        await page
          .getByRole("button", { name: "common.show_less", exact: true })
          .count(),
        1,
      );
      assert.equal(
        await page
          .getByRole("link", { name: "spaced term", exact: true })
          .getAttribute("href"),
        "/explore?q=%20%20spaced%20term%20%20",
      );
      await observe(
        "trusted expansion joins all shown terms, preserves raw text URI spaces and exposes source Near boundary",
      );
      await patch({
        groupPending: false,
        groupData: { groupId: "synthetic-projected-group", username: "Group" },
        coinLoading: false,
        coins: [{ mint: values.EVM, name: "Evm" }],
        nearPending: false,
        nearData: [[values.NEAR, { mint: values.NEAR, name: "Near" }]],
      });
      await page.waitForFunction(
        () =>
          document.querySelectorAll('[data-testid="coin-row"]').length === 2 &&
          document.querySelectorAll('[data-testid="group-row"]').length === 1 &&
          document.querySelectorAll('[data-testid="profile-display"]')
            .length === 1,
      );
      s = await state();
      assert.deepEqual(s.updates.mints, [values.NEAR, values.EVM]);
      assert.equal(s.updates.arity, 1);
      let r = await records();
      assert(
        r.coinRows.some(
          (c) =>
            c.mint === values.EVM &&
            c.index === 4 &&
            c.sourceScreen === 9 &&
            c.sourceElement === 30 &&
            c.searchTerm === values.EVM &&
            c.callbackMatches,
        ),
      );
      assert(r.groupRows.at(-1).callbackMatches);
      assert.equal(
        r.groupRows.at(-1).squad.groupId,
        "synthetic-projected-group",
      );
      await observe(
        "group and coin data outrank pending, Solana-only user fallback and source row props/callback identities join correctly",
      );
      r = await records();
      assert.equal(r.profiles.at(-1).nameOverride, values.SOL.slice(0, 6));
      assert.equal(r.profiles.at(-1).address, values.SOL);
      assert.equal(r.profiles.at(-1).description, undefined);
      assert.deepEqual(r.profilesRequested.at(-1), { address: values.SOL });
      assert(
        (await events()).some(
          (e) => e.type === "verified-subject" && e.subject === values.SOL,
        ),
      );
      await observe(
        "address row starts with raw prefix and no invented profile description while supplied profile result is absent",
      );
      await patch({
        profile: {
          username: "Synthetic name",
          followers: 0,
          profile_image: "inert-image",
          resolved_avatar_decoration: { synthetic: true },
          x_username: "inert-name",
        },
        verified: true,
      });
      await page.waitForFunction(
        () =>
          document.querySelector('[data-testid="profile-display"]').dataset
            .name === "Synthetic name",
      );
      r = await records();
      assert.equal(r.profiles.at(-1).description, "followers:0|compact:0");
      assert.equal(r.profiles.at(-1).verified, true);
      assert.equal(r.profiles.at(-1).profileImage, "inert-image");
      assert.equal(r.profiles.at(-1).link, false);
      assert.equal(r.profiles.at(-1).hoverCard, false);
      await observe(
        "real context/profile result rerender delivers exact name/follower/avatar/verification fields with no account request",
      );
      await page
        .getByRole("link", { name: "Synthetic name", exact: true })
        .click();
      assert.equal(
        (await events()).filter((e) => e.type === "navigate").at(-1).label,
        "A",
      );
      await patch({ callbackB: true });
      await page
        .getByRole("button", { name: "Coin " + values.EVM, exact: true })
        .click();
      assert.equal(
        (await events()).filter((e) => e.type === "navigate").at(-1).label,
        "B",
      );
      assert((await records()).coinRows.at(-1).callbackMatches);
      await observe(
        "trusted row actions forward current supplied navigation callback after callback-prop replacement",
      );
      const request = await page.evaluate(() =>
        window.recentSearchHarness.groupRequest(),
      );
      assert.equal(request.result.groupId, "synthetic-projected-group");
      assert.deepEqual(
        (await events()).filter((e) => e.type === "group-reader-port").at(-1),
        {
          type: "group-reader-port",
          id: values.GROUP,
          apiMatches: true,
          hasSignal: true,
        },
      );
      await observe(
        "actual group query callback forwards supplied client/id/native signal to an inert reader port",
      );
      await patch({ rejectGroup: true });
      assert.deepEqual(
        await page.evaluate(() => window.recentSearchHarness.groupRequest()),
        { error: "Synthetic group port failure" },
      );
      await patch({
        groupData: undefined,
        groupPending: false,
        groupError: true,
      });
      assert.equal(await page.getByTestId("group-row").count(), 0);
      assert.equal(
        await page.locator('a[href="/explore?q=' + values.GROUP + '"]').count(),
        1,
      );
      await observe(
        "group reader rejection propagates; undefined nonpending query data falls back to text without invented retry/error UI",
      );
      await patch({ coinError: true });
      assert.equal(await page.getByTestId("profile-display").count(), 0);
      assert.equal(
        await page.locator('a[href="/explore?q=' + values.SOL + '"]').count(),
        1,
      );
      assert.equal(
        await page
          .getByRole("button", { name: "Coin " + values.EVM, exact: true })
          .count(),
        1,
      );
      await observe(
        "coin loading-error blocks Solana user fallback while existing coin data still wins",
      );
      await patch({ fallbackPending: true });
      assert.equal(await page.getByTestId("recent-search-pending").count(), 1);
      assert.equal(
        await page.locator('a[href="/explore?q=' + values.SOL + '"]').count(),
        0,
      );
      await observe(
        "fallback-pending outranks error/text for an unresolved candidate exactly as source orders it",
      );
      await patch({
        coinError: false,
        fallbackPending: false,
        coins: [],
        curve: false,
      });
      assert.equal(await page.getByTestId("profile-display").count(), 0);
      assert.equal(
        await page.locator('a[href="/explore?q=' + values.SOL + '"]').count(),
        1,
      );
      assert.equal(
        await page.locator('a[href="/explore?q=' + values.EVM + '"]').count(),
        1,
      );
      await observe(
        "provided false curve admission and unresolved EVM stay text with no invented identity/account result",
      );
      await patch({ nearData: [], nearPending: true });
      assert.equal(await page.getByTestId("recent-search-pending").count(), 1);
      await patch({ nearPending: false });
      assert.equal(await page.getByTestId("recent-search-pending").count(), 0);
      assert.equal(
        await page.locator('a[href="/explore?q=' + values.NEAR + '"]').count(),
        1,
      );
      await observe(
        "Near supplied cohort pending then resolved-missing results become source pending then text",
      );
      await patch({
        groupsEnabled: false,
        groupData: { groupId: "unused-group" },
        groupPending: true,
      });
      assert.equal((await state()).groupQueries[0].enabled, false);
      assert.equal(await page.getByTestId("group-row").count(), 0);
      assert.equal(
        await page.locator('a[href="/explore?q=' + values.GROUP + '"]').count(),
        1,
      );
      await observe(
        "disabled group feature keeps query enabledfalse and ignores supplied data/pending in its combiner",
      );
      await patch({ canExpand: false });
      assert.equal(
        await page
          .getByRole("button", { name: "common.show_less", exact: true })
          .count(),
        0,
      );
      assert.deepEqual((await state()).near, { mints: [], enabled: false });
      assert.equal(
        await page
          .getByRole("link", { name: "spaced term", exact: true })
          .count(),
        0,
      );
      await patch({ canExpand: true });
      assert.equal(
        await page
          .getByRole("button", { name: "common.show_less", exact: true })
          .count(),
        1,
      );
      assert.equal(
        await page
          .getByRole("link", { name: "spaced term", exact: true })
          .count(),
        1,
      );
      await observe(
        "canExpand temporarily collapses the slice while retained local expanded state resumes when admission returns",
      );
      await page
        .getByRole("button", { name: "common.show_less", exact: true })
        .click();
      assert.equal(
        await page
          .getByRole("link", { name: "spaced term", exact: true })
          .count(),
        0,
      );
      await page
        .getByRole("button", { name: "common.see_all", exact: true })
        .click();
      assert.equal(
        await page
          .getByRole("link", { name: "spaced term", exact: true })
          .count(),
        1,
      );
      await observe(
        "source functional state updater toggles show-less/see-all without history persistence",
      );
      const navigations = (await events()).filter(
        (e) => e.type === "navigate",
      ).length;
      await page
        .getByRole("button", { name: "common.clear", exact: true })
        .click();
      await page.waitForFunction(
        () => window.recentSearchHarness.state().termCount === 0,
      );
      assert.equal(
        await page
          .getByRole("button", { name: "common.clear", exact: true })
          .isDisabled(),
        true,
      );
      assert.equal(
        await page.getByTestId("empty").textContent(),
        "search.no_recent_searches",
      );
      assert.deepEqual((await state()).groupQueries, []);
      assert.equal((await state()).hydration.disabled, true);
      assert.equal(
        (await events()).filter((e) => e.type === "navigate").length,
        navigations,
      );
      await observe(
        "clear calls supplied parent once, empties read inputs and disables its own button without navigating or reading storage",
      );
      await patch({ terms: values.terms });
      assert.equal(
        await page
          .getByRole("button", { name: "common.show_less", exact: true })
          .count(),
        1,
      );
      assert.equal(
        await page
          .getByRole("link", { name: "spaced term", exact: true })
          .count(),
        1,
      );
      await observe(
        "expanded local state is not silently reset across supplied term removal/replacement",
      );
      await page.evaluate(() => window.recentSearchHarness.unmount());
      assert.equal(await page.locator("#root").textContent(), "");
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
