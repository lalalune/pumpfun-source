import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { readFile } from "node:fs/promises";
import { createServer } from "node:http";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import { test } from "node:test";

const app = process.env.PUMP_VIDEO_SELECTION_APP ?? fileURLToPath(new URL("../", import.meta.url));
const require = createRequire(join(app, "packages/frontend/package.json"));
const { chromium } = require("@playwright/test");
const ts = require("typescript");

test("native video cover selection cannot reattach a cover released by its observer", async () => {
  const source = await readFile(join(app, "packages/frontend/src/app/create-video-preview.ts"), "utf8");
  const compiled = ts.transpileModule(source, { compilerOptions: {
    target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022,
  } }).outputText;
  const fixture = await readFile(new URL("./fixtures/cover-selection.webm", import.meta.url));
  const server = createServer((request, response) => {
    if (request.url === "/preview.mjs") {
      response.writeHead(200, { "content-type": "text/javascript" }); response.end(compiled);
    } else if (request.url === "/fixture.webm") {
      response.writeHead(200, { "content-type": "video/webm" }); response.end(fixture);
    } else {
      response.writeHead(200, { "content-type": "text/html" }); response.end("<!doctype html><title>Video lifecycle regression</title>");
    }
  });
  let browser;
  try {
    await new Promise((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
    const origin = `http://127.0.0.1:${server.address().port}`;
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    const remote = [];
    page.on("request", (request) => {
      if (/^https?:/.test(request.url()) && !request.url().startsWith(origin)) remote.push(request.url());
    });
    await page.goto(origin);
    const observations = await page.evaluate(async () => {
      const { prepareVideo, VideoDraftSession } = await import("/preview.mjs");
      const file = new File([await (await fetch("/fixture.webm")).blob()], "fixture.webm", { type: "video/webm" });
      const observations = [];
      for (const action of ["clear", "dispose"]) {
        const active = new Set(), revoked = [], selected = [];
        let session, released = false, created = 0;
        const platform = {
          video: () => document.createElement("video"), canvas: () => document.createElement("canvas"),
          url(blob) { const url = URL.createObjectURL(blob); active.add(url); created++; return url; },
          revoke(url) { URL.revokeObjectURL(url); active.delete(url); revoked.push(url); },
        };
        session = new VideoDraftSession((state) => {
          if (state.preview && state.selected === 1 && !released) { released = true; session[action](); }
        }, (value) => selected.push({ name: value.cover.name, released: active.size === 0 }), () => {},
        (file, signal) => prepareVideo(file, signal, platform));
        await session.choose(file);
        const prepared = { calls: selected.length, urls: active.size };
        session.select(1);
        observations.push({ action, prepared, created, selected, active: active.size, revoked: revoked.length });
        session.dispose();
      }
      return observations;
    });
    assert.deepEqual(remote, []);
    for (const row of observations) {
      assert.deepEqual(row.prepared, { calls: 1, urls: 4 });
      assert.equal(row.created, 4);
      assert.equal(row.revoked, 4);
      assert.equal(row.active, 0);
      assert.equal(row.selected.length, 1, row.action);
      assert.equal(row.selected[0].released, false, row.action);
    }
  } finally {
    await browser?.close();
    await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
  }
});
