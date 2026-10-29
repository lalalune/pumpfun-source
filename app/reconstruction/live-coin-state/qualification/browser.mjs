import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createHash } from "node:crypto";
import { readFile, writeFile, mkdir, stat } from "node:fs/promises";
import http from "node:http";
import { once } from "node:events";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";
import { batchVariantHashes } from "../client.mjs";
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
    "react/compiler-runtime": frontend.resolve("react/compiler-runtime"),
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
    "Standalone real React/compiler host; synthetic bound-store and manual scheduler ports, plus one native RAF scenario per physical variant. No app route/service/provider qualification.",
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
  for (const variant of batchVariantHashes) {
    await run(
      `${variant.slice(0, 12)} committed/pending rendering, multi-reference selector and unsubscribe`,
      async (c) => {
        await page.evaluate(
          (v) => window.harness.reset({ variant: v }),
          variant,
        );
        c.initial = await observed();
        await page
          .getByRole("button", { name: "Queue A", exact: true })
          .click();
        c.pending = await observed();
        assert.equal(c.pending.cap, null);
        assert.equal(c.pending.committed, null);
        assert.equal(c.pending.pending.usdMarketCap, 9);
        await page
          .getByRole("button", {
            name: "Advance artificial frame",
            exact: true,
          })
          .click();
        await page.getByTestId("cap").filter({ hasText: "9" }).waitFor();
        c.committed = await observed();
        assert.equal(c.committed.cap, 9);
        assert.deepEqual(c.committed.manyMints, ["a", null, "a"]);
        const count = c.committed.renders;
        await page
          .getByRole("button", { name: "Queue unrelated", exact: true })
          .click();
        await page
          .getByRole("button", {
            name: "Advance artificial frame",
            exact: true,
          })
          .click();
        c.unrelated = await observed();
        assert.equal(c.unrelated.renders, count);
        assert.equal(c.unrelated.handles.length, 0);
        c.unmounted = await page.evaluate(() => window.harness.unmount());
        assert.equal(c.unmounted.mounted, false);
        assert.equal(c.unmounted.handles.length, 0);
      },
    );
    await run(
      `${variant.slice(0, 12)} actual nested pause effects and cleanup reschedule`,
      async (c) => {
        await page.evaluate(
          (v) => window.harness.reset({ variant: v, pauses: 2 }),
          variant,
        );
        c.initial = await observed();
        assert.equal(c.initial.pauses, 2);
        await page
          .getByRole("button", { name: "Queue A", exact: true })
          .click();
        await page
          .getByRole("button", { name: "Release one pause", exact: true })
          .click();
        await page.getByTestId("pauses").filter({ hasText: "1" }).waitFor();
        c.onePause = await observed();
        assert.equal(c.onePause.committed, null);
        await page
          .getByRole("button", { name: "Release one pause", exact: true })
          .click();
        await page.getByTestId("pauses").filter({ hasText: "0" }).waitFor();
        c.released = await observed();
        assert.equal(c.released.committed, null);
        assert.equal(c.released.handles.length, 2);
        await page
          .getByRole("button", {
            name: "Advance artificial frame",
            exact: true,
          })
          .click();
        await page.getByTestId("cap").filter({ hasText: "9" }).waitFor();
        c.committed = await observed();
        assert.equal(c.committed.cap, 9);
        assert.equal(c.committed.handles.length, 0);
        c.unmounted = await page.evaluate(() => window.harness.unmount());
        assert.equal(c.unmounted.mounted, false);
      },
    );
    await run(
      `${variant.slice(0, 12)} actual native RAF commits and cancels fallback`,
      async (c) => {
        await page.evaluate(
          (v) => window.harness.reset({ variant: v, mode: "native" }),
          variant,
        );
        await observed();
        const began = Date.now();
        await page
          .getByRole("button", { name: "Queue A", exact: true })
          .click();
        await page.waitForFunction(
          () => window.harness.observe()?.cap === 9,
          {},
          { timeout: 2000 },
        );
        c.elapsedMs = Date.now() - began;
        c.committed = await observed();
        assert.ok(c.committed.rafCalls >= 1);
        assert.equal(c.committed.handles.length, 0);
        assert.equal(c.committed.errors, 0);
        c.unmounted = await page.evaluate(() => window.harness.unmount());
        assert.equal(c.unmounted.mounted, false);
        assert.equal(c.unmounted.handles.length, 0);
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
