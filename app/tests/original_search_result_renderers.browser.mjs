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
  "complete ordinary shared-search result components with actual React: fields, memo/provider handoff, sections and source click order",
  { timeout: 45000 },
  async () => {
    const temp = await mkdtemp(
        path.join(os.tmpdir(), "search-result-renderers-"),
      ),
      output = process.env.PUMP_SEARCH_RESULT_RENDERERS_OUTPUT;
    const packet = {
      scope:
        "Synthetic supplied result/display ports only. Real React/compiler/DOM; no provider HTTP, auth, credentials, storage, clipboard, protected/menu action or Perps execution.",
      observations: [],
      pageErrors: [],
      unexpected: [],
      hostRequests: [],
    };
    let server, browser, page;
    const state = () => page.evaluate(() => window.searchResultHarness.state()),
      records = () => page.evaluate(() => window.searchResultHarness.records()),
      events = () => page.evaluate(() => window.searchResultHarness.events());
    const patch = async (p) => {
      const serial = await page.evaluate(() =>
        window.searchResultHarness.serial(),
      );
      await page.evaluate((p) => window.searchResultHarness.patch(p), p);
      await page.waitForFunction(
        (n) => window.searchResultHarness.serial() > n,
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
          entryPoints: ["tests/fixtures/search-result-renderers-browser.mjs"],
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
        "reconstruction/search-result-renderers/client.mjs",
        "reconstruction/search-result-renderers/contract.json",
        "scripts/original-search-result-renderers.mjs",
        "tests/fixtures/search-result-renderers-browser.mjs",
        "tests/original_search_result_renderers.browser.mjs",
        "tests/original_search_result_renderers.test.mjs",
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
          window.searchResultHarness &&
          document.querySelectorAll("[data-search-row]").length === 2,
      );
      let r = await records();
      assert.equal(
        await page.locator('[data-testid^="search-preview-"]').count(),
        3,
      );
      assert.equal(
        await page.getByTestId("search-coin-row-mcap").textContent(),
        "market:0",
      );
      assert.equal(r.impressions[0].metadata.marketCap, 12.35);
      assert.equal(r.impressions[0].metadata.sourceScreen, 9);
      assert.equal(r.impressions[0].metadata.sourceElement, 15);
      assert.equal(r.impressions[0].term, "term");
      assert.equal(r.menu[0].position, 1);
      assert(r.menu[0].hasAnalytics);
      await observe(
        "ordinary mixed family receives source section shapes and preserves snapshot-zero display versus rounded metadata",
      );
      assert.equal(
        await page
          .getByRole("link", { name: "Name", exact: true })
          .getAttribute("href"),
        "/profile/wallet%20one",
      );
      r = await records();
      assert.equal(r.profiles.at(-1).address, " wallet one ");
      assert.equal(r.profiles.at(-1).userId, "user-1");
      assert.equal(r.profiles.at(-1).description, "followers:7|compact:7");
      assert.equal(r.profiles.at(-1).verified, false);
      assert.equal(r.profiles.at(-1).link, false);
      assert.equal(r.profiles.at(-1).hoverCard, false);
      await observe(
        "user row preserves route trim/address priority, raw display address and userId verification subject",
      );
      r = await records();
      assert.equal(r.avatars.at(-1).address, "projected-group");
      assert.equal(r.avatars.at(-1).isAnonymous, false);
      assert.equal(r.avatars.at(-1).ipfsPrefix, "synthetic-image-prefix");
      assert.equal(r.avatars.at(-1).src, "supplied-image:local-image");
      assert.deepEqual(r.groupRoutes.at(-1), {
        groupId: "projected-group",
        username: "",
      });
      assert(
        (await page.getByTestId("search-squad-row").textContent()).includes(
          "profile.squads.profile.pill",
        ),
      );
      assert(
        (await page.getByTestId("search-squad-row").textContent()).includes(
          "members:9",
        ),
      );
      await observe(
        "group projection feeds route/avatar/label/member ports without image acquisition",
      );
      const metadataId = r.impressions.at(-1).metadataId;
      await patch({ marketCap: null });
      await page.waitForFunction(
        () =>
          document.querySelector('[data-testid="search-coin-row-mcap"]')
            .textContent === "market:12.345",
      );
      r = await records();
      assert.equal(r.impressions.at(-1).metadataId, metadataId);
      assert.equal(r.capFormats.at(-1), 12.345);
      await observe(
        "actual context rerender retains metadata memo identity while null snapshot falls back to raw coin market cap",
      );
      await page.locator('a[href="/coin/synthetic-coin"]').click();
      let e = await events();
      const click = e
        .filter((e) =>
          [
            "last-click",
            "coin-click",
            "selected-coin",
            "host-link",
            "overridden-hover-click",
          ].includes(e.type),
        )
        .slice(-4);
      assert.deepEqual(
        click.map((e) => e.type),
        ["last-click", "coin-click", "selected-coin", "host-link"],
      );
      assert.equal(click[0].args[3], click[1].args[3]);
      assert.equal(click[0].args[2], "term");
      assert.equal(click[2].args[1], (await state()).coinId);
      await observe(
        "trusted coin click preserves shared metadata, term and lastClick→coinClick→raw-row selection order; spread hover click is overridden",
      );
      await page.getByTestId("search-squad-row").click();
      e = await events();
      const selected = e.find((e) => e.type === "selected-group");
      assert.deepEqual(selected.args, [
        "source-group",
        (await state()).groupId,
      ]);
      await observe(
        "trusted group click returns original raw search row rather than projected display descriptor",
      );
      await page.getByRole("link", { name: "Name", exact: true }).click();
      assert(
        (await events()).some(
          (e) => e.type === "selected-user" && e.args[0] === "user-1",
        ),
      );
      await page
        .getByTestId("search-preview-users")
        .getByRole("button", { name: "common.see_all" })
        .click();
      assert.deepEqual(
        (await events()).filter((e) => e.type === "see-all").at(-1).args,
        ["users"],
      );
      await observe(
        "user selection and section SeeAll forward actual source identities/category",
      );
      await patch({ verified: true });
      await page.waitForFunction(
        () =>
          document.querySelector('[data-testid="profile-display"]').dataset
            .verified === "true",
      );
      await observe(
        "verified-provider context result updates retained profile presentation with no reader acquisition",
      );
      const projects = (await events()).filter(
        (e) => e.type === "project-group",
      ).length;
      await patch({
        squads: {
          rows: [{ userId: "unused-row" }],
          visible: false,
          loading: false,
          hasMore: true,
        },
      });
      assert.equal(await page.getByTestId("search-preview-squads").count(), 0);
      assert.equal(
        (await events()).filter((e) => e.type === "project-group").length,
        projects,
      );
      await observe(
        "invisible group section does not map/project or render its rows",
      );
      await patch({
        coins: {
          rows: [{ mint: "held-but-not-rendered" }],
          visible: true,
          loading: true,
          hasMore: true,
        },
      });
      assert.equal(
        await page
          .getByTestId("search-preview-coins")
          .locator('[data-testid="skeleton-part"]')
          .count(),
        10,
      );
      assert.equal(
        await page.locator('a[href="/coin/held-but-not-rendered"]').count(),
        0,
      );
      assert.equal(
        await page
          .getByTestId("search-preview-coins")
          .getByRole("button", { name: "common.see_all" })
          .count(),
        1,
      );
      await observe(
        "loading section renders exact two-row skeleton and retains source hasMore control without executing child rows",
      );
      await patch({
        coins: { rows: [], visible: true, loading: false, hasMore: false },
      });
      assert.equal(
        await page
          .getByTestId("search-preview-coins")
          .getByRole("button", { name: "common.see_all" })
          .count(),
        0,
      );
      await observe(
        "visible empty section has no invented rows or SeeAll when source hasMore is false",
      );
      await patch({
        mode: "coin",
        directCoin: {
          mint: "zero-coin",
          name: "Zero",
          symbol: "",
          usd_market_cap: 0,
          created_timestamp: 10,
        },
        sourceScreen: null,
        sourceElement: null,
      });
      await page.waitForFunction(
        () =>
          document.querySelector('[data-testid="search-coin-row-mcap"]')
            .textContent === "market:0",
      );
      r = await records();
      assert.equal(r.impressions.at(-1).metadata.sourceScreen, null);
      assert.equal(r.impressions.at(-1).metadata.sourceElement, null);
      assert.equal(r.impressions.at(-1).metadata.itemPosition, 2);
      assert.equal(r.impressions.at(-1).metadata.marketCap, 0);
      assert.deepEqual(r.age.at(-1), {
        timestamp: 10,
        density: "comfortable",
        suffix: false,
      });
      assert.equal(r.menu.at(-1).position, 3);
      await observe(
        "direct row null overrides remain null, zero metadata is retained, supplied age and menu descriptor use exact props",
      );
      await page.locator('a[href="/coin/zero-coin"]').click();
      assert.deepEqual(
        (await events())
          .filter((e) =>
            ["last-click", "coin-click", "row-close"].includes(e.type),
          )
          .slice(-3)
          .map((e) => e.type),
        ["last-click", "coin-click", "row-close"],
      );
      await observe(
        "direct ordinary row click invokes its supplied close after source metadata callbacks",
      );
      await patch({
        mode: "user",
        directUser: {
          address: "external-wallet",
          wallet_label: "Custom label",
          username: "Other",
          is_pump_user: false,
          followers: 99,
        },
      });
      await page.waitForFunction(
        () =>
          document.querySelector('[data-testid="profile-display"]').dataset
            .name === "Custom label",
      );
      r = await records();
      assert.equal(
        r.profiles.at(-1).description,
        "search.external_wallet.subtitle",
      );
      assert.equal(r.profiles.at(-1).outsideWallet, true);
      await observe(
        "labelled external wallet takes label/subtitle/outside precedence over username and follower data",
      );
      await patch({
        directUser: {
          address: "abcdefghi",
          wallet_label: "",
          username: "Fallback",
          is_pump_user: true,
          followers: 999,
        },
      });
      await page.waitForFunction(
        () =>
          document.querySelector('[data-testid="profile-display"]').dataset
            .name === "Fallback",
      );
      r = await records();
      assert.equal(r.profiles.at(-1).description, "abcdef");
      assert.equal(r.profiles.at(-1).outsideWallet, false);
      await observe(
        "defined empty wallet label falls back for name but still uses address subtitle rather than followers",
      );
      await patch({ directUser: {} });
      await page.waitForFunction(
        () =>
          document.querySelector('[data-testid="profile-display"]').dataset
            .name === "web.search.anonymous_fallback",
      );
      r = await records();
      assert.equal(r.profiles.at(-1).address, null);
      assert.equal(r.profiles.at(-1).description, "followers:0|compact:0");
      assert.equal(await page.locator("a").count(), 0);
      await observe(
        "missing identity preserves anonymous display and zero followers without inventing a profile link",
      );
      await patch({
        mode: "skeleton",
        skeletonRows: 3,
        skeletonVariant: "circle",
      });
      await page.waitForFunction(
        () =>
          document.querySelectorAll('[data-testid="skeleton-part"]').length ===
          15,
      );
      assert.equal(await page.locator('[data-variant="circle"]').count(), 3);
      await observe(
        "retained skeleton frame responds to row/variant changes with exact supplied part props",
      );
      await page.evaluate(() => window.searchResultHarness.unmount());
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
