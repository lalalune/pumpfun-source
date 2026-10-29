import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtemp, mkdir, readFile, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import { generateInventory } from "../scripts/inventory.mjs";
import {
  buildGraph,
  publishGraph,
  verifyGraph,
} from "../scripts/factory-graph/core.mjs";
const options = { routes: [], targetLines: 1, maximumLines: 10000 };
async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), "graph-api-literal-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  for (const path of ["contracts", "evidence/web/objects"])
    await mkdir(join(root, path), { recursive: true });
  const source =
    'globalThis.TURBOPACK.push(["chunk",1,e=>{e.s(["right",0,"GET /right"]);/* "GET /wrong" */}]);';
  const path = "evidence/web/objects/source.js";
  await writeFile(join(root, path), source);
  await writeFile(
    join(root, "evidence/web/manifest.json"),
    JSON.stringify({
      records: [
        {
          url: "https://pump.fun/source.js",
          path,
          status: 200,
          bytes: Buffer.byteLength(source),
          sha256: createHash("sha256").update(source).digest("hex"),
        },
      ],
    }),
  );
  await generateInventory(root, { log: () => {} });
  const start = source.indexOf('"GET /right"');
  const site = { source: path, start, end: start + '"GET /right"'.length };
  await writeFile(
    join(root, "contracts/developer-bindings.json"),
    JSON.stringify({
      bindings: [
        {
          operation: "GET /right",
          operationId: "get_right",
          evidence: { clientCallSites: [site] },
        },
      ],
    }),
  );
  return { root, source, site };
}
test("API attribution binds exact parsed literals and preserves the last packet on mismatches", async (t) => {
  for (const ledger of ["internal-operations", "developer-bindings"]) {
    const { root } = await fixture(t);
    await publishGraph(root, "research/graph", options);
    await verifyGraph(root, "research/graph", options);
    const before = await readFile(join(root, "research/graph/MANIFEST.json"));
    const path = join(root, "contracts", ledger + ".json");
    const data = JSON.parse(await readFile(path, "utf8"));
    (data.operations || data.bindings)[0].operation = "GET /wrong";
    await writeFile(path, JSON.stringify(data));
    await assert.rejects(
      publishGraph(root, "research/graph", options),
      /operation literal mismatch/,
    );
    assert.deepEqual(
      await readFile(join(root, "research/graph/MANIFEST.json")),
      before,
    );
  }
});
test("quoted text inside comments and coercible or partial ranges are not operation literals", async (t) => {
  for (const mutate of [
    (site, source) => ({
      ...site,
      operation: "GET /wrong",
      start: source.indexOf('"GET /wrong"'),
      end: source.indexOf('"GET /wrong"') + 12,
    }),
    (site) => ({ ...site, start: String(site.start) }),
    (site) => ({ ...site, start: site.start + 1, end: site.end - 1 }),
    (site) => ({ ...site, start: site.start + 0.5 }),
  ]) {
    const { root, source, site } = await fixture(t);
    await writeFile(
      join(root, "contracts/internal-operations.json"),
      JSON.stringify({
        operations: [{ operation: "GET /right", ...mutate(site, source) }],
      }),
    );
    await assert.rejects(
      buildGraph(root, options),
      /operation literal mismatch/,
    );
  }
});
test("a retained developer call site authenticates its operation before attribution", async (t) => {
  const { root } = await fixture(t);
  const app = fileURLToPath(new URL("../", import.meta.url));
  const bindings = JSON.parse(
    await readFile(join(app, "contracts/developer-bindings.json"), "utf8"),
  );
  const binding = bindings.bindings.find(
    (b) => b.operation === "GET /competitions",
  );
  const site = binding.evidence.clientCallSites[0];
  assert.deepEqual(
    [site.source, site.start, site.end],
    ["evidence/web/objects/13c13db9eb86191b.js", 40747, 40766],
  );
  const index = JSON.parse(
    await readFile(join(app, "recovered/modules.json"), "utf8"),
  );
  const module = index.modules.find((m) =>
    m.origins.some(
      (o) =>
        o.source === site.source && o.start <= site.start && o.end >= site.end,
    ),
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
  index.modules = [module];
  await writeFile(join(root, "recovered/modules.json"), JSON.stringify(index));
  await writeFile(
    join(root, "evidence/web/manifest.json"),
    JSON.stringify({ records }),
  );
  binding.evidence.clientCallSites = [site];
  await writeFile(
    join(root, "contracts/internal-operations.json"),
    JSON.stringify({ operations: [] }),
  );
  const path = join(root, "contracts/developer-bindings.json");
  await writeFile(path, JSON.stringify({ bindings: [binding] }));
  const reports = await buildGraph(root, options);
  assert.equal(reports["API-ATTRIBUTION.json"].developer.length, 1);
  binding.operation = "GET /wrong";
  await writeFile(path, JSON.stringify({ bindings: [binding] }));
  await assert.rejects(buildGraph(root, options), /operation literal mismatch/);
});
