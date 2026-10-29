import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import {
  copyFile,
  mkdir,
  mkdtemp,
  readFile,
  rm,
  writeFile,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import test from "node:test";
import {
  buildGraph,
  factoryRegistrationIds,
  publishGraph,
  verifyGraph,
} from "../scripts/factory-graph/core.mjs";

const app = resolve(import.meta.dirname, "..");
const options = { routes: ["/"], targetLines: 1, maximumLines: 100 };
const sha = (value) => createHash("sha256").update(value).digest("hex");

async function retainedFixture(t, aliasControl = false) {
  const root = await mkdtemp(join(tmpdir(), "pump-graph-origin-ids-"));
  assert.equal(dirname(root), resolve(tmpdir()));
  assert.ok(root.startsWith(join(tmpdir(), "pump-graph-origin-ids-")));
  t.after(() => rm(root, { recursive: true, force: true }));
  const index = JSON.parse(
    await readFile(join(app, "recovered/modules.json"), "utf8"),
  );
  const original = index.modules.find(
    (item) =>
      item.sha256 ===
      (aliasControl
        ? "ac958e6c1ea5ae37647619da80cee73000e79667bdb7e1ac2f0c49a2b43c4c20"
        : "e7a13e86717bfab990fca9f995565810d802f430f480aa7f7d244241abc22d9e"),
  );
  assert.deepEqual(
    original.ids,
    aliasControl ? [335703, 309265, 985688, 186434] : [906032, 110823],
  );
  const module = { ...original, origins: original.origins.slice(0, 2) };
  const capture = JSON.parse(
    await readFile(join(app, "evidence/web/manifest.json"), "utf8"),
  );
  const sources = new Set(module.origins.map((origin) => origin.source));
  const html = capture.records.find(
    (record) => record.url === "https://pump.fun/" && record.status === 200,
  );
  sources.add(html.path);
  const records = capture.records.filter((record) => sources.has(record.path));
  for (const relative of [...sources, module.path]) {
    await mkdir(dirname(join(root, relative)), { recursive: true });
    await copyFile(join(app, relative), join(root, relative));
  }
  await mkdir(join(root, "contracts"));
  await writeFile(
    join(root, "recovered/modules.json"),
    JSON.stringify({ ...index, modules: [module] }),
  );
  await writeFile(
    join(root, "evidence/web/manifest.json"),
    JSON.stringify({ ...capture, records }),
  );
  await writeFile(
    join(root, "contracts/internal-operations.json"),
    '{"operations":[]}',
  );
  await writeFile(
    join(root, "contracts/developer-bindings.json"),
    '{"bindings":[]}',
  );
  return { root, module };
}

test("retained identical factories keep only the IDs registered at each origin", async (t) => {
  const { root, module } = await retainedFixture(t);
  const reports = await buildGraph(root, options);
  const identities = reports["MODULE-IDENTITIES.json.gz"];
  assert.equal(
    identities.length,
    2,
    "a union of IDs must not create a cross product with origins",
  );
  for (const [index, id] of [906032, 110823].entries()) {
    assert.deepEqual(
      identities
        .filter((item) => item.origin.source === module.origins[index].source)
        .map((item) => item.id),
      [id],
    );
  }
  assert.ok(
    identities.find((item) => item.id === 906032).routeSeeds.includes("/"),
  );
  await publishGraph(root, "packet", options);
  await verifyGraph(root, "packet", options);
});

test("multiple aliases registered together remain available at both retained origins", async (t) => {
  const { root, module } = await retainedFixture(t, true);
  const reports = await buildGraph(root, { ...options, maximumLines: 10_000 });
  const identities = reports["MODULE-IDENTITIES.json.gz"];
  assert.equal(identities.length, 8);
  for (const origin of module.origins) {
    assert.deepEqual(
      new Set(
        identities
          .filter((item) => item.origin.source === origin.source)
          .map((item) => item.id),
      ),
      new Set(module.ids),
    );
  }
});

test("an unregistered inventory ID is rejected before graph publication", async (t) => {
  const { root, module } = await retainedFixture(t);
  await publishGraph(root, "packet", options);
  const before = await readFile(join(root, "packet/GRAPH-SUMMARY.json"));
  const path = join(root, "recovered/modules.json");
  const index = JSON.parse(await readFile(path, "utf8"));
  index.modules[0].ids.push(999999);
  await writeFile(path, JSON.stringify(index));
  await assert.rejects(
    publishGraph(root, "packet", options),
    /registration.*ID|ID.*registration/i,
  );
  assert.deepEqual(
    await readFile(join(root, "packet/GRAPH-SUMMARY.json")),
    before,
  );
  index.modules[0] = module;
  await writeFile(path, JSON.stringify(index));
  await verifyGraph(root, "packet", options);
});

test(
  "retained corpus registration census authenticates each actual ID and origin",
  { timeout: 60_000 },
  async () => {
    const index = JSON.parse(
      await readFile(join(app, "recovered/modules.json"), "utf8"),
    );
    const capture = JSON.parse(
      await readFile(join(app, "evidence/web/manifest.json"), "utf8"),
    );
    const records = new Map(
      capture.records.map((record) => [record.path, record]),
    );
    const sources = new Map();
    let oldPairs = 0,
      registeredPairs = 0,
      origins = 0;
    for (const module of index.modules) {
      const observed = new Set();
      for (const origin of module.origins) {
        if (!sources.has(origin.source)) {
          const bytes = await readFile(join(app, origin.source));
          const record = records.get(origin.source);
          assert.equal(bytes.length, record.bytes);
          assert.equal(sha(bytes), record.sha256);
          const text = new TextDecoder("utf-8", {
            fatal: true,
            ignoreBOM: true,
          }).decode(bytes);
          sources.set(origin.source, {
            text,
            registrations: factoryRegistrationIds(text),
          });
        }
        const { text, registrations } = sources.get(origin.source);
        assert.equal(sha(text.slice(origin.start, origin.end)), module.sha256);
        const ids = registrations.get(`${origin.start}:${origin.end}`);
        assert.ok(ids?.length);
        for (const id of ids) {
          assert.ok(module.ids.map(String).includes(String(id)));
          observed.add(String(id));
        }
        oldPairs += module.ids.length;
        registeredPairs += ids.length;
        origins++;
      }
      assert.deepEqual(observed, new Set(module.ids.map(String)));
    }
    assert.ok(
      registeredPairs < oldPairs,
      "the actual corpus contains falsely multiplied ID/origin pairs",
    );
    console.log(
      JSON.stringify({
        modules: index.modules.length,
        origins,
        capturedSources: sources.size,
        oldPairs,
        registeredPairs,
        inventedPairs: oldPairs - registeredPairs,
      }),
    );
  },
);
