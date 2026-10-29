import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createHash } from "node:crypto";
import { readFile, writeFile, mkdir, stat } from "node:fs/promises";
import http from "node:http";
import { once } from "node:events";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

const appRoot = fileURLToPath(new URL("../../../", import.meta.url));
const args = process.argv.slice(2);
assert.equal(args.length, 2, "usage: browser.mjs --output NEW_DIRECTORY");
assert.equal(args[0], "--output");
const output = path.resolve(args[1]);
await assert.rejects(stat(output), { code: "ENOENT" });
await mkdir(output, { recursive: true });
const frontend = createRequire(
  path.join(appRoot, "packages/frontend/package.json"),
);
const backend = createRequire(
  path.join(appRoot, "packages/backend/package.json"),
);
const esbuild = createRequire(backend.resolve("tsx"))("esbuild");
const { chromium } = frontend("@playwright/test");
const sha = (b) => createHash("sha256").update(b).digest("hex");
const fixture = fileURLToPath(new URL("./fixture.mjs", import.meta.url));
const built = await esbuild.build({
  entryPoints: [fixture],
  absWorkingDir: appRoot,
  bundle: true,
  write: false,
  platform: "browser",
  format: "iife",
  metafile: true,
  define: { "process.env.NODE_ENV": '"development"' },
  alias: {
    "react/compiler-runtime": frontend.resolve("react/compiler-runtime"),
    "react-dom/client": frontend.resolve("react-dom/client"),
    react: frontend.resolve("react"),
  },
});
const bundle = built.outputFiles[0].contents;
const inputs = [];
for (const name of Object.keys(built.metafile.inputs)) {
  const absolute = path.resolve(appRoot, name),
    bytes = await readFile(absolute);
  inputs.push({
    path: path.relative(appRoot, absolute),
    bytes: bytes.length,
    sha256: sha(bytes),
  });
}
const record = {
  scope:
    "Complete translated hook in real React/compiler runtime with explicit synthetic query/seed/codec ports. Five manual-timer scenarios plus one real2500ms control; not maintained/website UI or provider compatibility.",
  sourceHead: execFileSync("git", ["rev-parse", "HEAD"], {
    cwd: appRoot,
    env: { ...process.env, GIT_NO_LAZY_FETCH: "1" },
    encoding: "utf8",
  }).trim(),
  startedAt: new Date().toISOString(),
  inputs,
  bundleSha256: sha(bundle),
  requests: [],
  cases: [],
  errors: [],
};
await writeFile(
  path.join(output, "INPUTS.json"),
  JSON.stringify(record, null, 2) + "\n",
);
const server = http.createServer((request, response) => {
  record.requests.push({ method: request.method, path: request.url });
  response.setHeader("Cache-Control", "no-store");
  if (request.method !== "GET") {
    response.writeHead(405);
    response.end();
    return;
  }
  if (request.url === "/bundle.js") {
    response.setHeader("Content-Type", "text/javascript");
    response.end(bundle);
  } else if (request.url === "/") {
    response.setHeader("Content-Type", "text/html");
    response.end(
      '<!doctype html><meta charset="utf-8"><title>Synthetic source qualification</title><div id="root"></div><script src="/bundle.js"></script>',
    );
  } else {
    response.writeHead(404);
    response.end();
  }
});
let browser, context, page;
async function settled() {
  await page.waitForFunction(
    () =>
      window.harness?.observe().lastRevision ===
      window.harness?.observe().revision,
    {},
    { timeout: 5000 },
  );
}
async function observe() {
  await settled();
  return page.evaluate(() => window.harness.observe());
}
async function reset(expression) {
  await page.evaluate(expression);
  await settled();
}
async function run(name, body) {
  const item = { name, startedAt: new Date().toISOString() };
  record.cases.push(item);
  try {
    await body(item);
    item.status = "PASS";
  } catch (error) {
    item.status = "FAIL";
    item.error = String(error.stack ?? error);
    await page
      .screenshot({
        path: path.join(output, `failure-${record.cases.length}.png`),
      })
      .catch(() => {});
    throw error;
  } finally {
    item.endedAt = new Date().toISOString();
  }
}
try {
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  record.origin = `http://127.0.0.1:${server.address().port}`;
  browser = await chromium.launch({ headless: true });
  context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
  });
  await context.tracing.start({
    screenshots: true,
    snapshots: true,
    sources: true,
  });
  page = await context.newPage();
  page.on("pageerror", (error) =>
    record.errors.push(String(error.stack ?? error)),
  );
  await page.goto(record.origin);
  await page.waitForFunction(() => Boolean(window.harness));
  await run(
    "deduplication, first12, local append12 and matching query options",
    async (item) => {
      await reset(() => {
        const rows = window.harness.makeRows("old", 30);
        return window.harness.reset({
          query: {
            data: { coins: [...rows, rows[0], {}] },
            isPending: false,
            isError: false,
          },
        });
      });
      item.initial = await observe();
      assert.equal(item.initial.keys.length, 12);
      assert.equal(item.initial.symbols[0], "old-0");
      assert.deepEqual(item.initial.options, {
        queryKey: ["callouts", "home-feed", "all", 150, false, null],
        enabled: true,
        staleTime: 15000,
        retry: 3,
        refetchOnWindowFocus: true,
        refetchInterval: 15000,
        refetchIntervalInBackground: false,
        hasPlaceholder: false,
      });
      await page
        .getByRole("button", { name: "Fetch next", exact: true })
        .click();
      assert.equal((await observe()).keys.length, 24);
      await page
        .getByRole("button", { name: "Fetch next", exact: true })
        .click();
      item.final = await observe();
      assert.equal(item.final.keys.length, 30);
      assert.equal(item.final.hasNextPage, false);
    },
  );
  await run(
    "raw array identity and WeakMap object identity preserve cached rows",
    async (item) => {
      await reset(() =>
        window.harness.reset({
          query: {
            data: { coins: window.harness.makeRows("cache", 14) },
            isPending: false,
            isError: false,
          },
        }),
      );
      item.phases = [await observe()];
      for (const phase of [1, 2, 3]) {
        await page.evaluate((value) => window.harness.identity(value), phase);
        item.phases.push(await observe());
      }
      assert.deepEqual(
        item.phases.map((x) => x.symbols[0]),
        ["cache-0", "cache-0", "cache-0", "MUTATED"],
      );
      assert.ok(item.phases.every((x) => x.keys.length === 12));
    },
  );
  await run(
    "pending counts, cap25/preview3, show-new cap40 and retired fallback",
    async (item) => {
      await reset(() =>
        window.harness.reset({
          query: {
            data: { coins: window.harness.makeRows("old", 50) },
            isPending: false,
            isError: false,
          },
        }),
      );
      for (let i = 0; i < 4; i++)
        await page
          .getByRole("button", { name: "Fetch next", exact: true })
          .click();
      assert.equal((await observe()).keys.length, 50);
      await page.evaluate(() => {
        const old = window.harness.makeRows("old", 50);
        window.harness.update({
          query: {
            data: { coins: [...window.harness.makeRows("new", 60), ...old] },
            isPending: false,
            isError: false,
          },
        });
      });
      item.before = await observe();
      assert.equal(item.before.pending, 0);
      assert.equal(item.before.hasUnseen, true);
      await page.getByRole("button", { name: "Show new", exact: true }).click();
      let snapshot = await observe();
      assert.equal(snapshot.keys.length, 40);
      assert.equal(snapshot.keys[0], "cid:new-0");
      for (let i = 0; i < 3; i++) {
        await page
          .getByRole("button", {
            name: "Step 100 artificial timer callbacks",
            exact: true,
          })
          .click();
        snapshot = await observe();
        assert.ok(snapshot.pending <= 25);
        assert.ok(snapshot.preview.length <= 3);
        if (i === 0) {
          assert.equal(snapshot.pending, 25);
          assert.equal(snapshot.preview.length, 3);
          item.capped = snapshot;
        }
        await page
          .getByRole("button", { name: "Show new", exact: true })
          .click();
        snapshot = await observe();
        assert.equal(snapshot.keys.length, 40);
      }
      assert.equal(snapshot.hasUnseen, false);
      assert.equal(snapshot.hasNextPage, true);
      assert.equal(snapshot.pending, 0);
      assert.equal(snapshot.intervals.length, 0);
      await page
        .getByRole("button", { name: "Fetch next", exact: true })
        .click();
      item.final = await observe();
      assert.equal(item.final.keys.length, 52);
    },
  );
  await run(
    "seed chain/initial-viewer gate and actual viewer reset",
    async (item) => {
      await reset(() =>
        window.harness.reset({
          args: { viewerAddress: "A", chain: "all" },
          seed: {
            chain: "all",
            response: { coins: window.harness.makeRows("seed", 14) },
          },
          query: { data: undefined, isPending: true, isError: false },
        }),
      );
      item.seed = await observe();
      assert.equal(item.seed.keys.length, 12);
      assert.equal(item.seed.loading, false);
      assert.equal(item.seed.options.hasPlaceholder, true);
      await page.evaluate(() =>
        window.harness.update({ args: { viewerAddress: "B", chain: "all" } }),
      );
      item.otherViewer = await observe();
      assert.equal(item.otherViewer.keys.length, 0);
      assert.equal(item.otherViewer.loading, true);
      assert.equal(item.otherViewer.options.hasPlaceholder, false);
      await page.evaluate(() =>
        window.harness.update({ args: { viewerAddress: "A", chain: "all" } }),
      );
      assert.equal((await observe()).keys.length, 12);
      await page.evaluate(() =>
        window.harness.update({ args: { viewerAddress: "A", chain: "other" } }),
      );
      assert.equal((await observe()).keys.length, 0);
      await page.evaluate(() =>
        window.harness.update({
          args: { viewerAddress: "B", chain: "all" },
          query: {
            data: { coins: window.harness.makeRows("B", 20) },
            isPending: false,
            isError: false,
          },
        }),
      );
      item.final = await observe();
      assert.equal(item.final.keys.length, 12);
      assert.ok(item.final.keys.every((x) => x.startsWith("cid:B-")));
    },
  );
  await run(
    "loading/error/disabled output follows supplied query states",
    async (item) => {
      await reset(() =>
        window.harness.reset({
          args: { enabled: false },
          query: { data: undefined, isPending: true, isError: false },
        }),
      );
      assert.equal((await observe()).loading, false);
      await page.evaluate(() =>
        window.harness.update({ args: { enabled: true } }),
      );
      assert.equal((await observe()).loading, true);
      await page.evaluate(() =>
        window.harness.update({
          query: { data: undefined, isPending: false, isError: true },
        }),
      );
      assert.equal((await observe()).error, "Could not load the callouts feed");
      await page.evaluate(() =>
        window.harness.update({
          query: { data: { coins: [] }, isPending: false, isError: true },
        }),
      );
      assert.equal((await observe()).error, null);
      await page.evaluate(() =>
        window.harness.update({
          query: {
            data: { coins: window.harness.makeRows("stale", 4) },
            isPending: false,
            isError: true,
          },
        }),
      );
      item.final = await observe();
      assert.equal(item.final.error, null);
      assert.equal(item.final.keys.length, 4);
      assert.equal(item.final.fetching, false);
    },
  );
  await run(
    "one actual2500ms interval and real React unmount cleanup",
    async (item) => {
      await reset(() =>
        window.harness.reset({
          timerMode: "real",
          query: {
            data: { coins: window.harness.makeRows("old", 12) },
            isPending: false,
            isError: false,
          },
        }),
      );
      const start = Date.now();
      await page.evaluate(() =>
        window.harness.update({
          query: {
            data: {
              coins: [
                ...window.harness.makeRows("fresh", 1),
                ...window.harness.makeRows("old", 12),
              ],
            },
            isPending: false,
            isError: false,
          },
        }),
      );
      item.before = await observe();
      assert.equal(item.before.pending, 0);
      assert.deepEqual(item.before.intervals, [{ delay: 2500, mode: "real" }]);
      await page.waitForFunction(
        () => window.harness.observe().pending === 1,
        {},
        { timeout: 8000 },
      );
      item.elapsedMs = Date.now() - start;
      item.tick = await observe();
      assert.ok(item.elapsedMs >= 2000);
      assert.equal(item.tick.preview.length, 1);
      await page.evaluate(() => window.harness.unmount());
      await page.waitForFunction(
        () => window.harness.observe().intervals.length === 0,
        {},
        { timeout: 5000 },
      );
      item.final = await page.evaluate(() => window.harness.observe());
      assert.ok(item.final.cleared > item.before.cleared);
    },
  );
  assert.deepEqual(record.errors, []);
  record.status = "PASS";
} catch (error) {
  record.status = "FAIL";
  record.failure = String(error.stack ?? error);
  process.exitCode = 1;
} finally {
  if (context)
    await context.tracing
      .stop({ path: path.join(output, "trace.zip") })
      .catch((error) => record.errors.push(String(error)));
  if (browser) await browser.close();
  if (server.listening) await new Promise((resolve) => server.close(resolve));
  record.stoppedAt = new Date().toISOString();
  record.cleanup = { browserClosed: true, serverListening: server.listening };
  await writeFile(
    path.join(output, "RESULT.json"),
    JSON.stringify(record, null, 2) + "\n",
  );
  console.log(
    JSON.stringify({
      status: record.status,
      cases: record.cases.map((x) => ({ name: x.name, status: x.status })),
      output,
      cleanup: record.cleanup,
    }),
  );
}
