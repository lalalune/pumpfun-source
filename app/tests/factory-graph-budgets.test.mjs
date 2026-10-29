import assert from "node:assert/strict";
import { mkdtemp, mkdir, readFile, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import {
  buildGraph,
  publishGraph,
  verifyGraph,
} from "../scripts/factory-graph/core.mjs";

async function retainedFixture(t) {
  const root = await mkdtemp(join(tmpdir(), "graph-budget-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  const app = fileURLToPath(new URL("../", import.meta.url));
  const index = JSON.parse(
    await readFile(join(app, "recovered/modules.json"), "utf8"),
  );
  const module = index.modules.find((m) => m.ids.includes(774101));
  assert.equal(
    module.sha256,
    "c69e3ff21e9162f1c81a5f8316bdf5b6ad131ecc0d3f8bced202a6b3339098ca",
  );
  const manifest = JSON.parse(
    await readFile(join(app, "evidence/web/manifest.json"), "utf8"),
  );
  const records = manifest.records.filter((r) =>
    module.origins.some((o) => o.source === r.path),
  );
  for (const path of [module.path, ...records.map((r) => r.path)]) {
    await mkdir(dirname(join(root, path)), { recursive: true });
    await writeFile(join(root, path), await readFile(join(app, path)));
  }
  await writeFile(
    join(root, "recovered/modules.json"),
    JSON.stringify({ ...index, modules: [module] }),
  );
  await writeFile(
    join(root, "evidence/web/manifest.json"),
    JSON.stringify({ records }),
  );
  await mkdir(join(root, "contracts"), { recursive: true });
  await writeFile(
    join(root, "contracts/internal-operations.json"),
    '{"operations":[]}',
  );
  await writeFile(
    join(root, "contracts/developer-bindings.json"),
    '{"bindings":[]}',
  );
  return root;
}
const options = { routes: [], targetLines: 1, maximumLines: 100 };
test("non-finite or malformed budgets cannot replace a verified retained-source graph", async (t) => {
  const root = await retainedFixture(t);
  await publishGraph(root, "research/graph", options);
  await verifyGraph(root, "research/graph", options);
  const before = await readFile(join(root, "research/graph/MANIFEST.json"));
  for (const [label, changed] of [
    ["NaN target", { targetLines: NaN }],
    ["NaN maximum", { maximumLines: NaN }],
    ["infinite maximum", { maximumLines: Infinity }],
    ["negative target", { targetLines: -1 }],
    ["fractional target", { targetLines: 0.5 }],
    ["string maximum", { maximumLines: "100" }],
    ["maximum below target", { targetLines: 5, maximumLines: 4 }],
    ["unsafe integer maximum", { maximumLines: Number.MAX_SAFE_INTEGER + 1 }],
  ])
    await t.test(label, async () => {
      await assert.rejects(
        publishGraph(root, "research/graph", { ...options, ...changed }),
        /invalid source-line budget/,
      );
      assert.deepEqual(
        await readFile(join(root, "research/graph/MANIFEST.json")),
        before,
      );
    });
});
test("a legitimate zero-line request and ordinary integer budgets stay valid", async (t) => {
  const root = await retainedFixture(t);
  const empty = await buildGraph(root, {
    ...options,
    targetLines: 0,
    maximumLines: 0,
  });
  assert.equal(empty["GRAPH-SUMMARY.json"].analyzedLines, 0);
  const selected = await buildGraph(root, options);
  assert.ok(selected["GRAPH-SUMMARY.json"].analyzedLines >= 1);
});
