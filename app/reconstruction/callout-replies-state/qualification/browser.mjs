import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createHash } from "node:crypto";
import { readFile, writeFile, mkdir, stat } from "node:fs/promises";
import http from "node:http";
import { once } from "node:events";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";
assert.equal(
  process.argv.length,
  4,
  "usage: browser.mjs --output NEW_DIRECTORY",
);
assert.equal(process.argv[2], "--output");
const appRoot = fileURLToPath(new URL("../../../", import.meta.url)),
  output = path.resolve(process.argv[3]);
await assert.rejects(stat(output), { code: "ENOENT" });
await mkdir(output, { recursive: true });
const frontend = createRequire(
    path.join(appRoot, "packages/frontend/package.json"),
  ),
  backend = createRequire(path.join(appRoot, "packages/backend/package.json")),
  esbuild = createRequire(backend.resolve("tsx"))("esbuild"),
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
  const file = fileURLToPath(new URL(name, import.meta.url)),
    relative = path.relative(appRoot, file);
  if (!inputs.some((i) => i.path === relative)) {
    const b = await readFile(file);
    inputs.push({ path: relative, bytes: b.length, sha256: sha(b) });
  }
}
const record = {
  scope:
    "Standalone real React/compiler with synthetic query observer, primed realMap/Set overlay context and injected reader/Response capabilities. No Next, provider, current cookies, endpoint or original timing qualification.",
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
      '<!doctype html><meta charset="utf-8"><title>Injected replies read</title><div id="root"></div><script src="/bundle.js"></script>',
    );
  }
  res.writeHead(req.url === "/favicon.ico" ? 204 : 404);
  res.end();
});
let browser, context, page;
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
  await page.waitForFunction(() => !!window.repliesFixture);
  const names = await page.evaluate(() => window.repliesFixture.names);
  assert.equal(names.length, 6);
  for (const name of names) {
    const item = { name, startedAt: new Date().toISOString() };
    record.cases.push(item);
    try {
      item.observed = await page.evaluate(
        (name) => window.repliesFixture.run(name),
        name,
      );
      item.status = "PASS";
    } catch (e) {
      item.status = "FAIL";
      item.error = String(e.stack ?? e);
      await page
        .screenshot({
          path: path.join(output, `failure-${record.cases.length}.png`),
        })
        .catch(() => {});
      throw e;
    } finally {
      item.endedAt = new Date().toISOString();
    }
  }
  record.cleanup = await page.evaluate(() => window.repliesFixture.cleanup());
  assert.deepEqual(record.cleanup, {
    overlayListeners: 0,
    queryListeners: 0,
    rootChildren: 0,
  });
  assert.deepEqual(record.errors, []);
  assert.ok(
    record.requests.every(
      (r) =>
        r.method === "GET" &&
        ["/", "/bundle.js", "/favicon.ico"].includes(r.path),
    ),
  );
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
  record.afterInputs = [];
  for (const row of inputs) {
    const b = await readFile(path.resolve(appRoot, row.path));
    const after = { path: row.path, bytes: b.length, sha256: sha(b) };
    record.afterInputs.push(after);
    assert.deepEqual(after, row, "runtime input changed during producer");
  }
  await writeFile(
    path.join(output, "RESULT.json"),
    JSON.stringify(record, null, 2) + "\n",
  );
}
console.log(
  JSON.stringify({
    status: record.status,
    cases: record.cases.length,
    errors: record.errors.length,
    browserClosed: record.browserClosed,
    serverListening: record.serverListening,
  }),
);
