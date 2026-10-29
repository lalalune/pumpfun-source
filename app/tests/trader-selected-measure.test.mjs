import assert from "node:assert/strict";
import { test } from "node:test";
import {
  readFile,
  writeFile,
  mkdir,
  mkdtemp,
  link,
  rm,
} from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import { parse } from "@babel/parser";
import React from "../packages/frontend/node_modules/react/index.js";
import { renderToStaticMarkup } from "../packages/frontend/node_modules/react-dom/server.node.js";
import {
  findNodes,
  exactlyOne,
} from "../scripts/original-contracts/source.mjs";
import {
  verifyTraderSelectedMeasure,
  PAGE,
  traderRows,
} from "../scripts/verify-trader-selected-measure.mjs";
import { parseLeaderboardResponse } from "../packages/frontend/src/app/leaderboard/types.ts";
import { startTraderMeasureHttp } from "./fixtures/trader-measure-http.mjs";
const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sdk = createRequire(path.join(APP, "packages/sdk/package.json")),
  { build, transform } = createRequire(sdk.resolve("tsup"))("esbuild");
async function component(t, baseline = false) {
  const dir = await mkdtemp(
    path.join(APP, "packages/frontend/.trader-measure-"),
  );
  t.after(() => rm(dir, { recursive: true, force: true }));
  const out = path.join(dir, "actual-row.cjs");
  if (!baseline) {
    await build({
      entryPoints: [path.join(APP, PAGE)],
      bundle: true,
      write: true,
      outfile: out,
      platform: "node",
      format: "cjs",
      jsx: "automatic",
      external: ["react", "react/*", "next/*"],
      plugins: [
        {
          name: "expose-used-private-row",
          setup(b) {
            b.onLoad({ filter: /leaderboard-client\.tsx$/ }, async (args) => {
              const text = await readFile(args.path, "utf8");
              assert.equal(
                text.split("export default function LeaderboardClient()")
                  .length,
                2,
              );
              return {
                contents:
                  text.replace(
                    "export default function LeaderboardClient()",
                    "function LeaderboardClient()",
                  ) + "\nexport{TraderRows};",
                loader: "tsx",
              };
            });
          },
        },
      ],
    });
  } else {
    const text = await readFile(path.join(APP, PAGE), "utf8"),
      tree = parse(text, {
        sourceType: "module",
        plugins: ["typescript", "jsx"],
      }),
      parts = [];
    for (const name of ["usd", "percent"]) {
      const n = exactlyOne(
        findNodes(
          tree,
          (n) => n.type === "VariableDeclarator" && n.id?.name === name,
        ),
        name,
      );
      parts.push("const " + text.slice(n.start, n.end) + ";");
    }
    for (const name of ["identityLabel", "shortIdentity", "VerifiedMark"]) {
      const n = exactlyOne(
        findNodes(
          tree,
          (n) => n.type === "FunctionDeclaration" && n.id?.name === name,
        ),
        name,
      );
      parts.push(text.slice(n.start, n.end));
    }
    parts.push(
      await readFile(
        path.join(
          APP,
          "reconstruction/trader-selected-measure/reference/native-row.tsx",
        ),
        "utf8",
      ),
    );
    const result = await transform(parts.join("\n") + "\nexport{TraderRows};", {
      loader: "tsx",
      jsx: "automatic",
      format: "cjs",
    });
    await writeFile(out, result.code);
  }
  return createRequire(import.meta.url)(out).TraderRows;
}
const metrics = (html) =>
  [
    ...html
      .replaceAll("<!-- -->", "")
      .matchAll(
        /class="ranking-metric"><strong class="([^"]+)">(.*?)<\/strong><small>(.*?)<\/small>/g,
      ),
  ].map((m) => ({ tone: m[1], value: m[2], caption: m[3] }));
const render = (C, entries, sort) =>
  renderToStaticMarkup(React.createElement(C, { entries, sort }));
test("complete source query/selector and both actual consumer variants bind native control/request/rendered value", async () => {
  const c = await verifyTraderSelectedMeasure();
  assert.equal(c.consumers.length, 2);
  assert.equal(c.witnesses.length, 15);
  assert.ok(c.witnesses.every((w) => w.sha256 && w.utf8 && w.utf16));
});
test("source gate rejects selecting combined for realized, disconnecting sort prop and formatting the wrong field", async (t) => {
  const c = await verifyTraderSelectedMeasure(),
    dir = await mkdtemp(path.join(APP, ".trader-source-"));
  t.after(() => rm(dir, { recursive: true, force: true }));
  const files = new Set([
    "reconstruction/trader-selected-measure/reference/native-row.tsx",
    "scripts/original-contracts/source.mjs",
    "scripts/original-pnl-leaderboard-client.mjs",
    "evidence/web/manifest.json",
    "recovered/modules.json",
    ...Object.keys(c.unchanged),
    ...c.prerequisite.source.selectedIndexEntries.flatMap((r) =>
      r.origins.map((o) => o.source),
    ),
  ]);
  for (const name of files) {
    const dest = path.join(dir, name);
    await mkdir(path.dirname(dest), { recursive: true });
    await link(path.join(APP, name), dest);
  }
  const dest = path.join(dir, PAGE);
  await mkdir(path.dirname(dest), { recursive: true });
  const text = await readFile(path.join(APP, PAGE), "utf8");
  await writeFile(dest, text);
  await verifyTraderSelectedMeasure(dir);
  for (const [from, to, pattern] of [
    ["? entry.realizedPnlUsd", "? entry.pnlUsd", "raw measure changed source"],
    [
      "sort={traderSort}",
      'sort={"combined"}',
      "native row must receive selected request sort",
    ],
    [
      "usd.format(value)",
      "usd.format(entry.pnlUsd)",
      "actual native selected currency call",
    ],
  ]) {
    assert.ok(text.includes(from));
    await writeFile(dest, text.replace(from, to));
    await assert.rejects(
      verifyTraderSelectedMeasure(dir),
      pattern ? new RegExp(pattern) : undefined,
    );
  }
});
test("actual native backend HTTP and exported adapter admit all sorts, retain key gate, reject bad filter and fail/recover without fallback", async (t) => {
  const fixture = await startTraderMeasureHttp();
  t.after(() => fixture.close());
  assert.equal(
    (await fetch(fixture.backendUrl + "/v1/pnl-leaderboard?period=daily"))
      .status,
    401,
  );
  for (const sort of ["combined", "realized", "unrealized"]) {
    const r = await fetch(
      fixture.adapterUrl +
        "/api/leaderboard?category=traders&period=daily&sort=" +
        sort,
    );
    assert.equal(r.status, 200);
    const body = await r.json();
    const admitted = parseLeaderboardResponse(body);
    assert.equal(admitted.ok, true);
    assert.equal(admitted.data.kind, "traders");
    assert.equal(
      admitted.data.entries[0].walletAddress,
      fixture.wallets[sort === "realized" ? 1 : 0],
    );
    assert.ok(!JSON.stringify(body).includes(`pf_live_${"A".repeat(49)}`));
  }
  const before = (await fixture.command("snapshot")).ledger.length;
  assert.equal(
    (
      await fetch(
        fixture.adapterUrl +
          "/api/leaderboard?category=traders&sort=unsupported",
      )
    ).status,
    400,
  );
  assert.equal((await fixture.command("snapshot")).ledger.length, before);
  await fixture.command("stop-backend");
  const failed = await fetch(
    fixture.adapterUrl +
      "/api/leaderboard?category=traders&period=daily&sort=realized",
  );
  assert.equal(failed.status, 502);
  assert.equal((await failed.json()).ok, false);
  await fixture.command("start-backend");
  assert.equal(
    (
      await fetch(
        fixture.adapterUrl +
          "/api/leaderboard?category=traders&period=daily&sort=realized",
      )
    ).status,
    200,
  );
  const ledger = (await fixture.command("snapshot")).ledger;
  assert.ok(ledger.every((r) => r.method === "GET"));
  assert.ok(ledger.filter((r) => r.keyMatched).every((r) => r.status === 200));
});
test("same actual backend/adapter data exposes base UI defect then actual native React module displays selected amount/tone/caption", async (t) => {
  const fixture = await startTraderMeasureHttp();
  t.after(() => fixture.close());
  const Current = await component(t),
    Before = await component(t, true);
  const expected = {
    combined: [
      ["positive", "$100.00", "10% combined PnL"],
      ["positive", "$50.00", "5% combined PnL"],
    ],
    realized: [
      ["positive", "$40.00", "Realized PnL"],
      ["negative", "-$20.00", "Realized PnL"],
    ],
    unrealized: [
      ["positive", "$120.00", "Unrealized PnL"],
      ["positive", "$10.00", "Unrealized PnL"],
    ],
  };
  for (const sort of Object.keys(expected)) {
    const r = await fetch(
      fixture.adapterUrl +
        "/api/leaderboard?category=traders&period=daily&sort=" +
        sort,
    );
    const body = parseLeaderboardResponse(await r.json()),
      entries = body.data.entries;
    const result = metrics(render(Current, entries, sort));
    assert.deepEqual(
      result,
      expected[sort].map(([tone, value, caption]) => ({
        tone,
        value,
        caption,
      })),
    );
    if (sort !== "combined")
      assert.notDeepEqual(metrics(render(Before, entries, sort)), result);
    const corrupted = structuredClone(body);
    corrupted.data.entries[0].realizedPnlUsd = null;
    assert.throws(() => parseLeaderboardResponse(corrupted));
  }
});
