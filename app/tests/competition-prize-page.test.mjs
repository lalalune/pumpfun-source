import assert from "node:assert/strict";
import { test } from "node:test";
import {
  readFile,
  writeFile,
  mkdir,
  mkdtemp,
  rm,
  link,
} from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { once } from "node:events";
import React from "../packages/frontend/node_modules/react/index.js";
import { jsx } from "../packages/frontend/node_modules/react/jsx-runtime.js";
import { renderToStaticMarkup } from "../packages/frontend/node_modules/react-dom/server.node.js";
import { verifyCompetitionPrizePage } from "../scripts/verify-competition-prize-page.mjs";
import {
  readBoundedJson,
  normalizeUpstreamResponse,
} from "../packages/frontend/src/app/api/leaderboard/upstream.ts";
import { parseLeaderboardResponse } from "../packages/frontend/src/app/leaderboard/types.ts";
import { validateAgainstSchema } from "../packages/backend/src/schema-validator.ts";
const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), ".."),
  sdk = createRequire(path.join(APP, "packages/sdk/package.json")),
  { build } = createRequire(sdk.resolve("tsup"))("esbuild");
async function components(t) {
  const dir = await mkdtemp(path.join(APP, "packages/frontend/.prize-page-"));
  t.after(() => rm(dir, { recursive: true, force: true }));
  const out = path.join(dir, "prizes.cjs");
  await build({
    entryPoints: [
      path.join(
        APP,
        "packages/frontend/src/app/leaderboard/competition-prizes.tsx",
      ),
    ],
    bundle: true,
    write: true,
    outfile: out,
    platform: "node",
    format: "cjs",
    jsx: "automatic",
    external: ["react", "react/jsx-runtime", "react/compiler-runtime"],
    nodePaths: [path.join(APP, "packages/frontend/node_modules")],
  });
  return createRequire(import.meta.url)(out);
}
test("actual web bindings preserve original selector, unfiltered empty guard and existing precise display policy", async () => {
  const c = await verifyCompetitionPrizePage();
  assert.equal(c.base, "ef400863f4e476b2eaaab0866c0b1187d8060abc");
  assert.equal(c.original.length, 2);
  assert.ok(c.original.every((w) => w.sha256 && w.utf8 && w.utf16));
});
test("integration gate rejects selector changes and a filtered-empty condition", async (t) => {
  const dir = await mkdtemp(path.join(APP, ".prize-page-source-"));
  t.after(() => rm(dir, { recursive: true, force: true }));
  const old = JSON.parse(
    await readFile(
      path.join(APP, "reconstruction/competition-prizes/contract.json"),
    ),
  );
  const bridge = "packages/frontend/src/app/leaderboard/competition-prizes.tsx",
    page = "packages/frontend/src/app/leaderboard/leaderboard-client.tsx";
  const names = new Set([
    "scripts/original-contracts/source.mjs",
    "evidence/web/manifest.json",
    "recovered/modules.json",
    "reconstruction/competition-prizes/contract.json",
    ...Object.keys(old.outputs),
    ...old.source.selectedIndexEntries.flatMap((r) =>
      r.origins.map((o) => o.source),
    ),
    bridge,
    page,
    "packages/frontend/src/app/leaderboard/competition-rules-model.ts",
    "reconstruction/competition-prize-page/reference/competition-rules-model.ts",
  ]);
  for (const name of names) {
    const target = path.join(dir, name);
    await mkdir(path.dirname(target), { recursive: true });
    if (name === bridge || name === page)
      await writeFile(target, await readFile(path.join(APP, name)));
    else await link(path.join(APP, name), target);
  }
  const b = path.join(dir, bridge),
    bt = await readFile(b, "utf8");
  await writeFile(b, bt.replace("t >= e.rankFrom", "t > e.rankFrom"));
  await assert.rejects(
    verifyCompetitionPrizePage(dir),
    /selector changed original decisions/,
  );
  await writeFile(b, bt);
  const p = path.join(dir, page),
    pt = await readFile(p, "utf8");
  assert.ok(pt.includes("data.entries.length === 0"));
  await writeFile(
    p,
    pt.replace("data.entries.length === 0", "filtered.length === 0"),
  );
  await assert.rejects(
    verifyCompetitionPrizePage(dir),
    /fallback must use raw standings/,
  );
});
test("real React original tiers use existing English labels and preserve large decimal precision/raw text and supplied order", async (t) => {
  const { CompetitionPrizeTiers } = await components(t),
    prizes = [
      { rankFrom: 1, rankTo: 1, amount: "999999999999999999.99" },
      { rankFrom: 3, rankTo: 5, amount: "10.5" },
      { rankFrom: 7, rankTo: 7, amount: "<b>2 SOL</b>" },
    ],
    before = JSON.stringify(prizes),
    html = renderToStaticMarkup(jsx(CompetitionPrizeTiers, { prizes }));
  for (const text of [
    "Prize breakdown",
    "#1",
    "#3 – #5",
    "$999,999,999,999,999,999.99",
    "$10.50 each",
    "&lt;b&gt;2 SOL&lt;/b&gt;",
  ])
    assert.ok(html.includes(text), text);
  assert.ok(!html.includes("$1,000,000,000,000,000,000"));
  assert.ok(!html.includes("<b>2 SOL"));
  assert.ok(html.indexOf("cup-tier-1") < html.indexOf("cup-tier-3"));
  assert.ok(html.indexOf("cup-tier-3") < html.indexOf("cup-tier-7"));
  assert.equal(JSON.stringify(prizes), before);
});
test("real React row badges preserve inclusive first-match source selection, rank-zero absence, raw supplied values and escaping", async (t) => {
  const { CompetitionRankPrize } = await components(t),
    prizes = [
      { rankFrom: 1, rankTo: 2, amount: "first" },
      { rankFrom: 2, rankTo: 5, amount: "second" },
      { rankFrom: 6, rankTo: 6, amount: "<img src=x>" },
    ];
  for (const [rank, expected] of [
    [1, "first"],
    [2, "first"],
    [5, "second"],
    [6, "&lt;img src=x&gt;"],
  ]) {
    const html = renderToStaticMarkup(
      jsx(CompetitionRankPrize, { prizes, rank }),
    );
    assert.ok(html.includes('data-testid="cup-entry-prize"'));
    assert.ok(html.includes(expected));
    assert.ok(!html.includes("<img"));
  }
  for (const rank of [0, -1, 7])
    assert.equal(
      renderToStaticMarkup(jsx(CompetitionRankPrize, { prizes, rank })),
      "",
    );
});
test("real loopback JSON read passes retained public schema, actual projection/client admission and original tier rendering without backend-policy inference", async (t) => {
  const raw = {
    competition: {
      id: "00000000-0000-4000-8000-000000000001",
      slug: "web-prize-fixture",
      kind: "person",
      title: "Synthetic web prize fixture",
      description: "Supplied scoring description",
      prizeCopy: "Supplied copy",
      imageUrl: null,
      prizes: [
        { rankFrom: 1, rankTo: 1, amount: "999999999999999999.99" },
        { rankFrom: 2, rankTo: 3, amount: "2 SOL" },
      ],
      minMembers: 0,
      maxMembers: 0,
      maxEntries: 100,
      entriesCount: 0,
      participants: 0,
      registrationOpensAt: null,
      registrationClosesAt: null,
      startsAt: null,
      endsAt: null,
      joinable: false,
      phase: "upcoming",
      isFinal: false,
      top: [],
      winners: [],
    },
    leaderboard: {
      builtAtMs: 0,
      startSec: 0,
      endSec: 0,
      totalRanked: 0,
      isFinal: false,
      entries: [],
    },
  };
  const spec = JSON.parse(
      await readFile(path.join(APP, "contracts/developer.openapi.json")),
    ),
    schema =
      spec.paths["/competitions/{idOrSlug}"].get.responses["200"].content[
        "application/json"
      ].schema;
  assert.deepEqual(validateAgainstSchema(raw, schema, "$", spec), []);
  const requests = [],
    server = createServer((req, res) => {
      requests.push({ url: req.url, method: req.method });
      res.setHeader("content-type", "application/json");
      res.end(JSON.stringify(raw));
    });
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  t.after(async () => {
    const p = new Promise((r) => server.close(r));
    server.closeAllConnections();
    await p;
  });
  const response = await fetch(
      "http://127.0.0.1:" +
        server.address().port +
        "/fixture/competitions/web-prize-fixture",
    ),
    wire = await readBoundedJson(response),
    data = normalizeUpstreamResponse("competitions", wire, {
      page: 1,
      competitionId: "web-prize-fixture",
    }),
    accepted = parseLeaderboardResponse({
      ok: true,
      data,
      source: {
        mode: "developer-api",
        label: "Pump developer API",
        fetchedAt: "2026-10-29T00:00:00Z",
      },
    });
  assert.equal(accepted.ok, true);
  assert.equal(data.kind, "competition-detail");
  assert.deepEqual(data.competition.prizes, raw.competition.prizes);
  assert.deepEqual(requests, [
    { url: "/fixture/competitions/web-prize-fixture", method: "GET" },
  ]);
  const { CompetitionPrizeTiers } = await components(t),
    html = renderToStaticMarkup(
      jsx(CompetitionPrizeTiers, { prizes: data.competition.prizes }),
    );
  assert.ok(html.includes("$999,999,999,999,999,999.99"));
  assert.ok(html.includes("2 SOL each"));
  assert.throws(() =>
    normalizeUpstreamResponse(
      "competitions",
      {
        ...raw,
        competition: {
          ...raw.competition,
          prizes: [{ rankFrom: 1, rankTo: 1, amount: 1000 }],
        },
      },
      { page: 1, competitionId: "web-prize-fixture" },
    ),
  );
});
