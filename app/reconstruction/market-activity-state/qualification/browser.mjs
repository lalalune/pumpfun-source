import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createHash } from "node:crypto";
import { readFile, writeFile, mkdir, stat } from "node:fs/promises";
import http from "node:http";
import { once } from "node:events";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";
import { queryVariants } from "../client.mjs";
const appRoot = fileURLToPath(new URL("../../../", import.meta.url));
assert.equal(
  process.argv.length,
  4,
  "usage: browser.mjs --output NEW_DIRECTORY",
);
assert.equal(process.argv[2], "--output");
const output = path.resolve(process.argv[3]);
await assert.rejects(stat(output), { code: "ENOENT" });
await mkdir(output, { recursive: true });
const frontend = createRequire(
  path.join(appRoot, "packages/frontend/package.json"),
);
const backend = createRequire(
  path.join(appRoot, "packages/backend/package.json"),
);
const esbuild = createRequire(backend.resolve("tsx"))("esbuild"),
  { chromium } = frontend("@playwright/test");
const sha = (b) => createHash("sha256").update(b).digest("hex");
const built = await esbuild.build({
  entryPoints: [fileURLToPath(new URL("./fixture.mjs", import.meta.url))],
  absWorkingDir: appRoot,
  bundle: true,
  write: false,
  platform: "browser",
  format: "iife",
  metafile: true,
  define: { "process.env.NODE_ENV": '"development"' },
  alias: {
    "react-dom/client": frontend.resolve("react-dom/client"),
    "react-dom": frontend.resolve("react-dom"),
    react: frontend.resolve("react"),
  },
});
const bundle = built.outputFiles[0].contents,
  inputs = [];
for (const name of Object.keys(built.metafile.inputs)) {
  const file = path.resolve(appRoot, name),
    bytes = await readFile(file);
  inputs.push({
    path: path.relative(appRoot, file),
    bytes: bytes.length,
    sha256: sha(bytes),
  });
}
for (const name of ["browser.mjs", "fixture.mjs", "ports.mjs"]) {
  const bytes = await readFile(new URL(name, import.meta.url));
  if (
    !inputs.some(
      (i) =>
        i.path ===
        path.relative(appRoot, fileURLToPath(new URL(name, import.meta.url))),
    )
  )
    inputs.push({
      path: path.relative(
        appRoot,
        fileURLToPath(new URL(name, import.meta.url)),
      ),
      bytes: bytes.length,
      sha256: sha(bytes),
    });
}
const record = {
  scope:
    "Standalone real React host; injected local query/provider/frame capabilities, source-bound qualification helper ports and native queueMicrotask. No app route/service/provider qualification.",
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
const server = http.createServer((req, res) => {
  record.requests.push({ method: req.method, path: req.url });
  res.setHeader("Cache-Control", "no-store");
  if (req.method !== "GET") {
    res.writeHead(405);
    return res.end();
  }
  if (req.url === "/bundle.js") {
    res.setHeader("Content-Type", "text/javascript");
    return res.end(bundle);
  }
  if (req.url === "/") {
    res.setHeader("Content-Type", "text/html");
    return res.end(
      '<!doctype html><meta charset="utf-8"><title>Synthetic live state</title><div id="root"></div><script src="/bundle.js"></script>',
    );
  }
  res.writeHead(404);
  res.end();
});
let browser, context, page;
async function observed() {
  await page.waitForFunction(() => window.harness.observe()?.mounted);
  return page.evaluate(() => window.harness.observe());
}
async function run(name, body) {
  const c = { name, startedAt: new Date().toISOString() };
  record.cases.push(c);
  try {
    await body(c);
    c.status = "PASS";
  } catch (e) {
    c.status = "FAIL";
    c.error = String(e.stack ?? e);
    await page
      .screenshot({
        path: path.join(output, `failure-${record.cases.length}.png`),
      })
      .catch(() => {});
    throw e;
  } finally {
    c.endedAt = new Date().toISOString();
  }
}
try {
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  record.origin = `http://127.0.0.1:${server.address().port}`;
  browser = await chromium.launch({ headless: true });
  context = await browser.newContext();
  await context.tracing.start({
    screenshots: true,
    snapshots: true,
    sources: true,
  });
  page = await context.newPage();
  page.on("pageerror", (e) => record.errors.push(String(e.stack ?? e)));
  await page.goto(record.origin);
  await page.waitForFunction(() => !!window.harness);
  for (const row of queryVariants) {
    const variant = row.sha256;
    await run(
      `${variant.slice(0, 12)} query callback, native microtask seed, frame and selected-field readback`,
      async (item) => {
        await page.evaluate(
          (v) => window.harness.reset({ queryVariant: v }),
          variant,
        );
        item.initial = await observed();
        assert.deepEqual(item.initial.committed, {});
        await page
          .getByRole("button", { name: "Run request capability", exact: true })
          .click();
        await page.waitForFunction(
          () =>
            window.harness.observe().responses.length === 1 &&
            window.harness.observe().microtasksExecuted === 1,
        );
        item.queued = await observed();
        assert.deepEqual(item.queued.committed, {});
        assert.equal(item.queued.pending, 1);
        assert.equal(item.queued.microtasksQueued, 1);
        assert.equal(item.queued.requests[0].hasSignal, true);
        assert.deepEqual(item.queued.requests[0].mints, ["a"]);
        await page
          .getByRole("button", { name: "Flush artificial frame", exact: true })
          .click();
        await page.getByTestId("volume").filter({ hasText: "10" }).waitFor();
        item.committed = await observed();
        assert.equal(item.committed.read.a["24h"].numTxs, 1);
        await page
          .getByRole("button", { name: "Patch unselected metric", exact: true })
          .click();
        await page
          .getByRole("button", { name: "Flush artificial frame", exact: true })
          .click();
        await page.waitForFunction(
          () => window.harness.observe().committed.a["24h"].numTxs === 2,
        );
        item.unselected = await observed();
        assert.equal(item.unselected.read.a["24h"].numTxs, 1);
        assert.notEqual(item.unselected.reference, item.committed.reference);
        await page
          .getByRole("button", { name: "Render again", exact: true })
          .click();
        item.stable = await observed();
        assert.equal(item.stable.reference, item.unselected.reference);
        await page
          .getByRole("button", { name: "Patch selected metric", exact: true })
          .click();
        await page
          .getByRole("button", { name: "Flush artificial frame", exact: true })
          .click();
        await page.getByTestId("volume").filter({ hasText: "3" }).waitFor();
        item.selected = await observed();
        assert.equal(item.selected.read.a["24h"].volumeUSD, 3);
        await page
          .getByRole("button", { name: "Refetch missing mint", exact: true })
          .click();
        await page.waitForFunction(
          () => window.harness.observe().sequence.length === 2,
        );
        item.refetched = await observed();
        assert.deepEqual(item.refetched.sequence, ["invalidate", "refetch"]);
        await page
          .getByRole("button", { name: "Readback off", exact: true })
          .click();
        await page
          .getByTestId("volume")
          .filter({ hasText: "missing" })
          .waitFor();
        item.off = await observed();
        assert.deepEqual(item.off.read, {});
        assert.equal(item.off.committed.a["24h"].volumeUSD, 3);
        item.unmounted = await page.evaluate(() => window.harness.unmount());
        assert.equal(item.unmounted.mounted, false);
        assert.equal(item.unmounted.listeners, 0);
        assert.equal(item.unmounted.pending, 0);
      },
    );
    await run(
      `${variant.slice(0, 12)} overlapping generations and stale-completion freshness cache`,
      async (item) => {
        await page.evaluate(
          (v) => window.harness.reset({ queryVariant: v }),
          variant,
        );
        await observed();
        await page
          .getByRole("button", { name: "Start deferred request", exact: true })
          .click();
        await page
          .getByRole("button", { name: "Start deferred request", exact: true })
          .click();
        item.started = await observed();
        assert.equal(item.started.requests.length, 2);
        await page
          .getByRole("button", { name: "Resolve second", exact: true })
          .click();
        await page.waitForFunction(
          () => window.harness.observe().responses.length === 1,
        );
        await page
          .getByRole("button", { name: "Flush artificial frame", exact: true })
          .click();
        await page.getByTestId("volume").filter({ hasText: "2" }).waitFor();
        item.second = await observed();
        assert.equal(item.second.committed.a["24h"].volumeUSD, 2);
        await page
          .getByRole("button", { name: "Resolve first", exact: true })
          .click();
        await page.waitForFunction(
          () => window.harness.observe().responses.length === 2,
        );
        item.first = await observed();
        assert.equal(item.first.responses[1].a["24h"].volumeUSD, 1);
        assert.equal(item.first.committed.a["24h"].volumeUSD, 2);
        assert.equal(item.first.pending, 0);
        await page
          .getByRole("button", { name: "Warm cache", exact: true })
          .click();
        await page.waitForFunction(
          () => window.harness.observe().responses.length === 3,
        );
        item.warm = await observed();
        assert.equal(item.warm.responses[2].a["24h"].volumeUSD, 7);
        assert.equal(item.warm.requests.length, 2);
        assert.equal(item.warm.committed.a["24h"].volumeUSD, 2);
        item.unmounted = await page.evaluate(() => window.harness.unmount());
        assert.equal(item.unmounted.mounted, false);
        assert.equal(item.unmounted.listeners, 0);
        assert.equal(item.unmounted.pending, 0);
      },
    );
  }
  assert.deepEqual(record.errors, []);
  assert.equal(record.cases.length, 6);
  record.status = "PASS";
} finally {
  if (context)
    await context.tracing
      .stop({ path: path.join(output, "trace.zip") })
      .catch(() => {});
  if (browser) await browser.close();
  record.browserClosed = browser ? !browser.isConnected() : true;
  if (server.listening) await new Promise((resolve) => server.close(resolve));
  record.serverListening = server.listening;
  record.endedAt = new Date().toISOString();
  await writeFile(
    path.join(output, "RESULT.json"),
    JSON.stringify(record, null, 2) + "\n",
  );
}
console.log(
  JSON.stringify({
    status: record.status,
    cases: record.cases.length,
    errors: record.errors,
    browserClosed: record.browserClosed,
    serverListening: record.serverListening,
  }),
);
