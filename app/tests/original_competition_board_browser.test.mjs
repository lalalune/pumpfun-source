import assert from "node:assert/strict";
import { test } from "node:test";
import { readFile, mkdir } from "node:fs/promises";
import { createServer } from "node:http";
import { once } from "node:events";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import { chromium } from "../packages/frontend/node_modules/@playwright/test/index.mjs";
import {
  squadVariants,
  imageVariants,
} from "../packages/frontend/src/components/leaderboard/entry/entry-helpers.mjs";
import { prizeNumberVariants } from "../packages/frontend/src/components/leaderboard/original-prize-formats.mjs";
import { foregroundVariants } from "../reconstruction/competition-client/client.mjs";
import {
  competition,
  entries,
  detail,
  buckets,
} from "./fixtures/competition-board-data.mjs";
const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), ".."),
  FRONTEND = path.join(APP, "packages/frontend"),
  sdk = createRequire(path.join(APP, "packages/sdk/package.json")),
  { build } = createRequire(sdk.resolve("tsup"))("esbuild"),
  frontend = createRequire(path.join(FRONTEND, "package.json"));
async function css() {
  let text = await readFile(path.join(FRONTEND, "src/app/globals.css"), "utf8");
  for (const name of [
    "recovered-tokens.css",
    "recovered-fonts.css",
    "captured-root.css",
  ])
    text = text.replace(
      '@import "./' + name + '";',
      await readFile(path.join(FRONTEND, "src/app", name), "utf8"),
    );
  const config = frontend("tailwindcss/loadConfig.js")(
    path.join(FRONTEND, "tailwind.config.ts"),
  );
  config.content = [];
  for (const n of [
    "board/original-board.tsx",
    "entry/original-entry-row.tsx",
    "viewer/original-viewer-card.tsx",
    "original-prizes.tsx",
  ])
    config.content.push({
      raw: await readFile(
        path.join(FRONTEND, "src/components/leaderboard", n),
        "utf8",
      ),
      extension: "tsx",
    });
  return (
    await frontend("postcss")([frontend("tailwindcss")(config)]).process(text, {
      from: undefined,
    })
  ).css;
}
test("real recovered hooks→local GET→selection→full board composition and actual callers; responsive, retry/pending/final/rules/cleanup without original-provider parity", async (t) => {
  const bundle = await build({
      entryPoints: [
        path.join(APP, "tests/fixtures/competition-board-browser.mjs"),
      ],
      bundle: true,
      write: false,
      format: "iife",
      platform: "browser",
      jsx: "automatic",
      nodePaths: [path.join(FRONTEND, "node_modules")],
      define: { "process.env.NODE_ENV": '"production"' },
    }),
    style = await css(),
    received = [],
    failures = new Map();
  let announceAbortRequest, announceAbortClose;
  const abortRequest = new Promise(
    (resolve) => (announceAbortRequest = resolve),
  );
  const abortClose = new Promise((resolve) => (announceAbortClose = resolve));
  const server = createServer(async (req, res) => {
    if (req.url.startsWith("/fixture/")) {
      received.push({
        url: req.url,
        method: req.method,
        source: req.headers["x-pump-source"],
        platform: req.headers["x-pump-platform"],
      });
      const parts = req.url.split("/"),
        scenario = parts[2],
        id = parts[4],
        group = {
          ...competition,
          id: "group-fixture",
          kind: "group",
          title: "Fixture squad competition",
        },
        current = id === "group-fixture" ? group : competition;
      res.setHeader("content-type", "application/json");
      if (scenario === "abort" && id) {
        // A real in-flight loopback response. Only the local query port owns
        // cancellation; this does not claim the original query runtime policy.
        res.once("close", announceAbortClose);
        announceAbortRequest();
        return;
      }
      if (!id) {
        if (scenario === "fail" && !failures.get(scenario)) {
          failures.set(scenario, 1);
          res.statusCode = 503;
          res.end(JSON.stringify({ error: "fixture temporary failure" }));
          return;
        }
        res.end(
          JSON.stringify(
            scenario === "empty"
              ? { live: [], upcoming: [], past: [] }
              : { ...buckets, live: [competition, group] },
          ),
        );
        return;
      }
      const final =
        scenario === "final" ? { ...current, phase: "ended" } : current;
      res.end(
        JSON.stringify({
          ...detail,
          competition: final,
          viewer: {
            entry: {
              ...detail.viewer.entry,
              kind: current.kind,
              walletAddress:
                current.kind === "group"
                  ? null
                  : detail.viewer.entry.walletAddress,
            },
          },
          leaderboard: {
            entries:
              scenario === "pending"
                ? []
                : entries.map((e) => ({ ...e, kind: current.kind })),
          },
        }),
      );
      return;
    }
    if (req.url === "/app.js") {
      res.setHeader("content-type", "text/javascript");
      res.end(bundle.outputFiles[0].contents);
      return;
    }
    if (req.url === "/style.css") {
      res.setHeader("content-type", "text/css");
      res.end(style);
      return;
    }
    if (req.url.startsWith("/fonts/")) {
      try {
        res.setHeader("content-type", "font/woff2");
        res.end(await readFile(path.join(FRONTEND, "public", req.url)));
      } catch {
        res.statusCode = 404;
        res.end();
      }
      return;
    }
    res.setHeader("content-type", "text/html");
    res.end(
      '<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/style.css"></head><body><div id="root"></div><script src="/app.js"></script></body></html>',
    );
  });
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  t.after(async () => {
    const closed = new Promise((r) => server.close(r));
    server.closeAllConnections();
    await closed;
  });
  const origin = "http://127.0.0.1:" + server.address().port,
    browser = await chromium.launch({
      headless: true,
      executablePath: chromium.executablePath(),
    });
  t.after(() => browser.close());
  const errors = [],
    requests = [];
  const contexts = squadVariants.flatMap((s) =>
    imageVariants.map((i) => ({ squad: s.sha256, image: i.sha256 })),
  );
  async function pageFor(viewport, context, index, scenario = "normal") {
    const page = await browser.newPage({ viewport });
    page.on("pageerror", (e) => errors.push(e.message));
    await page.route("**/*", (route) => {
      const r = route.request();
      requests.push({ url: r.url(), method: r.method() });
      return new URL(r.url()).origin === origin
        ? route.continue()
        : route.abort();
    });
    const q = new URLSearchParams({
      ...context,
      number: prizeNumberVariants[index % 2].sha256,
      foreground: foregroundVariants[index % 2],
      scenario,
    });
    await page.goto(origin + "/?" + q);
    await page.waitForSelector("#unmounted");
    return page;
  }
  for (const [name, viewport] of [
    ["desktop", { width: 1280, height: 900 }],
    ["mobile", { width: 375, height: 812 }],
  ])
    for (let index = 0; index < contexts.length; index++) {
      const page = await pageFor(viewport, contexts[index], index);
      let release;
      const held = new Promise((r) => (release = r));
      await page.route(
        "**/fixture/normal/competitions/person-fixture",
        async (route) => {
          await held;
          await route.continue();
        },
      );
      await page.click("#mount");
      await page.waitForSelector(
        '[data-testid="host-hero"] h2:text("Fixture competition")',
      );
      assert.equal(await page.getByTestId("cup-entry-row").count(), 0);
      await page.getByTestId("cup-tier-1").waitFor();
      release();
      await page.getByTestId("cup-entry-row").first().waitFor();
      assert.equal(await page.getByTestId("cup-entry-row").count(), 3);
      assert.equal(await page.getByTestId("cup-rank-card").count(), 1);
      assert.equal(await page.getByTestId("cup-entry-prize").count(), 2);
      assert.equal(
        await page.getByTestId("cup-payline").textContent(),
        "fixture-paid-ranks:2",
      );
      assert.ok(
        (await page.getByTestId("cup-board-card").textContent()).includes(
          "fixture-standings",
        ),
      );
      const order = await page
        .getByTestId("cup-board-card")
        .locator(":scope > div")
        .evaluateAll((nodes) => nodes.map((n) => n.textContent));
      assert.ok(order[0].includes("fixture-your-rank"));
      assert.equal(order[1], "fixture-standings");
      assert.ok(order[2].includes("Fixture trader 1"));
      assert.ok(order[3].includes("Fixture trader 2"));
      assert.ok(order[4].includes("fixture-paid-ranks:2"));
      assert.ok(order[5].includes("Fixture trader 3"));
      const opts = await page.evaluate(() => window.__board.queryOptions);
      assert.ok(opts.some((o) => o.key[1] === "list" && o.staleTime === 15000));
      assert.ok(
        opts.some((o) => o.key[1] === "detail" && o.staleTime === 5000),
      );
      assert.ok(
        opts.every((o) => o.key.at(-1) === "unverified-synthetic-ui-key"),
      );
      const highlight = await page.evaluate(() =>
        window.__board.highlights.at(-1),
      );
      assert.deepEqual(highlight.window, {
        fromMs: Date.parse(competition.startsAt),
        toMs: Date.parse(competition.endsAt),
      });
      await page.click("#open-rules");
      await page.getByRole("dialog", { name: "Fixture rules port" }).waitFor();
      await page.click("#close-rules");
      assert.equal(await page.getByRole("dialog").count(), 0);
      const bounds = await page
        .getByTestId("cup-board-card")
        .evaluate((e) => ({ w: e.clientWidth, s: e.scrollWidth }));
      assert.ok(bounds.s <= bounds.w + 1);
      assert.ok(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      );
      await page.evaluate(() => document.fonts.ready);
      if (process.env.BOARD_SCREENSHOTS_DIR && index === 0) {
        await mkdir(process.env.BOARD_SCREENSHOTS_DIR, { recursive: true });
        await page.screenshot({
          path: path.join(
            process.env.BOARD_SCREENSHOTS_DIR,
            "board-" + name + ".png",
          ),
          fullPage: true,
        });
      }
      await page.click("#kind");
      await page.locator('[data-cup-kind="group"]').waitFor();
      await page.waitForFunction(
        () => window.__board.hero.at(-1)?.competition?.id === "group-fixture",
      );
      await page.getByTestId("cup-entry-row").first().waitFor();
      assert.equal(await page.getByTestId("cup-entry-row").count(), 3);
      assert.ok(
        (
          await page.evaluate(() => window.__board.hero.at(-1))
        ).className.includes("[--cup-lead:8px]"),
      );
      await page.click("#mount");
      await page.waitForSelector("#unmounted");
      await page.waitForFunction(() => window.__board.foregroundActive === 0);
      assert.ok(await page.evaluate(() => window.__board.aborts >= 4));
      assert.deepEqual(await page.context().cookies(), []);
      assert.equal(await page.evaluate(() => localStorage.length), 0);
      await page.close();
    }
  for (const scenario of ["fail", "pending", "empty", "final"]) {
    const page = await pageFor(
      { width: 375, height: 812 },
      contexts[0],
      0,
      scenario,
    );
    await page.click("#mount");
    if (scenario === "fail") {
      await page.locator("#retry-list").waitFor();
      assert.equal(await page.getByTestId("cup-entry-row").count(), 0);
      await page.click("#retry-list");
      await page.getByTestId("cup-entry-row").first().waitFor();
    } else if (scenario === "pending") {
      await page.getByTestId("cup-pending").waitFor();
      await page.getByTestId("cup-tier-1").waitFor();
      assert.equal(await page.getByTestId("cup-entry-row").count(), 0);
      assert.equal(await page.getByTestId("cup-rank-card").count(), 1);
    } else if (scenario === "empty") {
      await page.waitForSelector(
        '[data-testid="host-hero"] h2:text("fixture-no-competition")',
      );
      assert.equal(await page.getByTestId("cup-board-below-hero").count(), 0);
    } else {
      await page.getByTestId("cup-entry-row").first().waitFor();
      assert.ok(
        (await page.getByTestId("cup-board-card").textContent()).includes(
          "fixture-final-results",
        ),
      );
    }
    await page.click("#mount");
    await page.waitForFunction(() => window.__board.foregroundActive === 0);
    await page.close();
  }
  const abortPage = await pageFor(
    { width: 375, height: 812 },
    contexts[0],
    0,
    "abort",
  );
  await abortPage.click("#mount");
  await abortRequest;
  await abortPage.getByTestId("cup-tier-1").waitFor();
  assert.equal(await abortPage.getByTestId("cup-entry-row").count(), 0);
  await abortPage.click("#mount");
  await abortPage.waitForSelector("#unmounted");
  let timeout;
  try {
    await Promise.race([
      abortClose,
      new Promise((_, reject) => {
        timeout = setTimeout(
          () => reject(Error("loopback request did not abort")),
          5000,
        );
      }),
    ]);
  } finally {
    clearTimeout(timeout);
  }
  await abortPage.waitForFunction(() => window.__board.foregroundActive === 0);
  assert.deepEqual(await abortPage.context().cookies(), []);
  await abortPage.close();
  assert.deepEqual(errors, []);
  assert.ok(
    received.every(
      (r) => r.method === "GET" && r.source === "WEB" && r.platform === "web",
    ),
  );
  assert.ok(
    !received.some((r) => r.url.startsWith("/fixture/empty/competitions/")),
  );
  assert.ok(
    requests.every(
      (r) => r.method === "GET" && new URL(r.url).origin === origin,
    ),
  );
});
