import assert from "node:assert/strict";
import { readFile, writeFile, rm, mkdir } from "node:fs/promises";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import {
  buildGraph,
  publishGraph,
  verifyGraph,
} from "../scripts/factory-graph/core.mjs";
import { fixture } from "./factory-graph-fixture.mjs";
const options = { routes: ["/"], targetLines: 4, maximumLines: 100 };
test("a real retained factory is accepted once and rejected when its index row is duplicated", async (t) => {
  const root = await fixture();
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
    join(root, "evidence/web/manifest.json"),
    JSON.stringify({ records }),
  );
  index.modules = [module];
  const path = join(root, "recovered/modules.json");
  await writeFile(path, JSON.stringify(index));
  const realOptions = { routes: [], targetLines: 1, maximumLines: 100 };
  await publishGraph(root, "research/graph", realOptions);
  await verifyGraph(root, "research/graph", realOptions);
  index.modules.push(structuredClone(module));
  await writeFile(path, JSON.stringify(index));
  await assert.rejects(buildGraph(root, realOptions), /duplicate factory hash/);
});
test("duplicate factory rows cannot inflate a unique-content census or replace a valid packet", async (t) => {
  const root = await fixture();
  t.after(() => rm(root, { recursive: true, force: true }));
  await publishGraph(root, "research/graph", options);
  await verifyGraph(root, "research/graph", options);
  const before = await readFile(join(root, "research/graph/MANIFEST.json"));
  const path = join(root, "recovered/modules.json");
  const index = JSON.parse(await readFile(path, "utf8"));
  index.modules.push(structuredClone(index.modules[0]));
  await writeFile(path, JSON.stringify(index));
  await assert.rejects(
    publishGraph(root, "research/graph", options),
    /duplicate factory hash/,
  );
  assert.deepEqual(
    await readFile(join(root, "research/graph/MANIFEST.json")),
    before,
  );
});
test("duplicate IDs and identical origins cannot duplicate provenance-qualified nodes", async (t) => {
  for (const kind of ["id", "origin"]) {
    const root = await fixture();
    t.after(() => rm(root, { recursive: true, force: true }));
    const path = join(root, "recovered/modules.json");
    const index = JSON.parse(await readFile(path, "utf8"));
    const module = index.modules[0];
    if (kind === "id") module.ids.push(String(module.ids[0]));
    else module.origins.push(structuredClone(module.origins[0]));
    await writeFile(path, JSON.stringify(index));
    await assert.rejects(
      buildGraph(root, options),
      /duplicate factory (ID|origin)/,
    );
  }
});
test("different captured origins and conflicting variants remain independent evidence", async (t) => {
  const root = await fixture({ duplicateOrigin: true });
  t.after(() => rm(root, { recursive: true, force: true }));
  await publishGraph(root, "research/graph", options);
  await verifyGraph(root, "research/graph", options);
});
