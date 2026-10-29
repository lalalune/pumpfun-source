import assert from "node:assert/strict";
import { readFile, writeFile, rm } from "node:fs/promises";
import { join } from "node:path";
import test from "node:test";
import {
  buildGraph,
  publishGraph,
  verifyGraph,
} from "../scripts/factory-graph/core.mjs";
import { fixture } from "./factory-graph-fixture.mjs";
const options = { routes: ["/"], targetLines: 4, maximumLines: 100 };
async function setup(t) {
  const root = await fixture();
  t.after(() => rm(root, { recursive: true, force: true }));
  const manifestPath = join(root, "evidence/web/manifest.json");
  const indexPath = join(root, "recovered/modules.json");
  const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
  const index = JSON.parse(await readFile(indexPath, "utf8"));
  const source = manifest.records.find((r) => r.path.endsWith("source.js"));
  return {
    root,
    manifest,
    index,
    source,
    save: async () => {
      await writeFile(manifestPath, JSON.stringify(manifest));
      await writeFile(indexPath, JSON.stringify(index));
    },
  };
}
test("source provenance URLs must agree with the captured record before publication", async (t) => {
  const f = await setup(t);
  const out = "research/provenance";
  await publishGraph(f.root, out, options);
  const before = await readFile(join(f.root, out, "MANIFEST.json"));
  const origin = f.index.modules[0].origins[0];
  const original = origin.url;
  for (const url of ["https://pump.fun/unrelated.js", undefined]) {
    origin.url = url;
    await f.save();
    await assert.rejects(publishGraph(f.root, out, options), /origin URL/);
    assert.deepEqual(
      await readFile(join(f.root, out, "MANIFEST.json")),
      before,
    );
  }
  origin.url = original;
  await f.save();
  await verifyGraph(f.root, out, options);
});
test("non-successful capture bodies cannot authenticate recovered graph source", async (t) => {
  const f = await setup(t);
  for (const status of [404, 500, undefined, true]) {
    f.source.status = status;
    await f.save();
    await assert.rejects(buildGraph(f.root, options), /successful capture/);
  }
});
test("duplicate capture paths cannot silently replace source identity", async (t) => {
  const f = await setup(t);
  f.manifest.records.push({ ...f.source });
  await f.save();
  await assert.rejects(buildGraph(f.root, options), /duplicate capture path/);
});
test("ambiguous requested and final capture URLs cannot silently select one record", async (t) => {
  for (const duplicateRequested of [true, false]) {
    const f = await setup(t);
    const copy = {
      ...f.source,
      path: "evidence/web/objects/alias.js",
      url: duplicateRequested ? f.source.url : "https://pump.fun/redirect.js",
      final_url: f.source.url,
    };
    await writeFile(
      join(f.root, copy.path),
      await readFile(join(f.root, f.source.path)),
    );
    f.manifest.records.push(copy);
    await f.save();
    await assert.rejects(buildGraph(f.root, options), /ambiguous capture URL/);
  }
});
test("factory source requires a valid JavaScript capture URL", async (t) => {
  const f = await setup(t);
  for (const url of ["https://pump.fun/source.txt", "not a URL"]) {
    f.source.url = url;
    f.source.final_url = url;
    for (const module of f.index.modules)
      for (const origin of module.origins)
        if (origin.source === f.source.path) origin.url = url;
    await f.save();
    await assert.rejects(buildGraph(f.root, options), /JavaScript capture URL/);
  }
});
test("valid captured redirects retain original provenance and verify normally", async (t) => {
  const f = await setup(t);
  f.source.final_url = "https://pump.fun/redirected/source.js";
  await f.save();
  await publishGraph(f.root, "research/redirect", options);
  await verifyGraph(f.root, "research/redirect", options);
});
