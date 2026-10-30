import assert from "node:assert/strict";
import { createServer } from "node:http";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";
import { test } from "node:test";

// Explicit test-only source root lets the same test run on an isolated base and
// candidate. When installed in app/tests it reads that repository's real modules.
const app = process.env.PUMP_LEADERBOARD_CONTEXT_APP ?? fileURLToPath(new URL("../", import.meta.url));
const ts = createRequire(pathToFileURL(join(app, "package.json")))("typescript");
const competition = {
  id: "returned-id", slug: "returned-slug", kind: "person", title: "Synthetic context fixture",
  description: "Test-only", prizeCopy: "Test-only", imageUrl: null, prizes: [],
  registrationOpensAt: null, registrationClosesAt: null, startsAt: null, endsAt: null,
  minMembers: 1, maxMembers: 1, maxEntries: 1, entriesCount: 0, participants: 0,
  joinable: false, phase: "upcoming", isFinal: false, top: [], winners: []
};
const payload = {
  competition,
  leaderboard: { startSec: 0, endSec: 1, entries: [], totalRanked: 0, builtAtMs: 0, isFinal: false }
};

const listen = async (server) => {
  await new Promise((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
  return `http://127.0.0.1:${server.address().port}`;
};
const close = (server) => new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));

test("real proxy HTTP rejects a different competition while accepting its id and slug", async () => {
  const temporary = await mkdtemp(join(tmpdir(), "pump-leaderboard-context-"));
  assert.equal(dirname(temporary), resolve(tmpdir()));
  let upstream, proxy;
  const paths = [];
  try {
    upstream = createServer((request, response) => {
      paths.push(new URL(request.url, "http://localhost").pathname);
      response.writeHead(200, { "content-type": "application/json" });
      response.end(JSON.stringify(payload));
    });
    const origin = await listen(upstream);
    for (const [name, relative] of [
      ["upstream", "packages/frontend/src/app/api/leaderboard/upstream.ts"],
      ["route", "packages/frontend/src/app/api/leaderboard/route.ts"],
      ["types", "packages/frontend/src/app/leaderboard/types.ts"]
    ]) {
      let source = await readFile(join(app, relative), "utf8");
      if (name === "upstream") {
        const original = 'export const DEVELOPER_API_ORIGIN = "https://api.pump.fun";';
        assert.equal(source.split(original).length, 2);
        source = source.replace(original, `export const DEVELOPER_API_ORIGIN = ${JSON.stringify(origin)};`);
      }
      if (name === "route") {
        const original = "const apiKey = process.env.PUMPFUN_DEVELOPER_API_KEY?.trim();";
        assert.equal(source.split(original).length, 2);
        source = source.replace(original, 'const apiKey = "synthetic-loopback-only";')
          .replace('"../../leaderboard/types"', '"./types.mjs"')
          .replace('"./upstream"', '"./upstream.mjs"');
      }
      const compiled = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022 } });
      await writeFile(join(temporary, `${name}.mjs`), compiled.outputText);
    }
    const { GET } = await import(pathToFileURL(join(temporary, "route.mjs")).href);
    proxy = createServer(async (request, response) => {
      try {
        const result = await GET(new Request(new URL(request.url, "http://localhost")));
        response.writeHead(result.status, Object.fromEntries(result.headers));
        response.end(await result.text());
      } catch { response.writeHead(500); response.end(); }
    });
    const proxyOrigin = await listen(proxy);
    for (const id of [competition.id, competition.slug, competition.slug.toUpperCase()]) {
      const response = await fetch(`${proxyOrigin}/api/leaderboard?category=competitions&id=${id}`);
      assert.equal(response.status, 200);
      assert.equal((await response.json()).data.competition.id, competition.id);
    }
    const response = await fetch(`${proxyOrigin}/api/leaderboard?category=competitions&id=requested-unrelated-id`);
    const result = await response.json();
    assert.equal(response.status, 502, JSON.stringify(result));
    assert.equal(result.error.code, "INVALID_UPSTREAM_RESPONSE");
    assert.equal(response.headers.get("cache-control"), "no-store");
    assert.deepEqual(paths, ["/v1/competitions/returned-id", "/v1/competitions/returned-slug", "/v1/competitions/RETURNED-SLUG", "/v1/competitions/requested-unrelated-id"]);
  } finally {
    if (proxy?.listening) await close(proxy);
    if (upstream?.listening) await close(upstream);
    await rm(temporary, { recursive: true, force: true });
  }
});
