import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtemp, mkdir, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { generateInventory } from "../scripts/inventory.mjs";
import { openCorpus } from "../scripts/original-contracts/source.mjs";

async function recover(t, source) {
  const root = await mkdtemp(join(tmpdir(), "inventory-metadata-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  await mkdir(join(root, "evidence/web/objects"), { recursive: true });
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
  return { root, report: await generateInventory(root, { log: () => {} }) };
}
test("top-level two-element chunk metadata never produces an anonymous factory", async (t) => {
  for (const callback of [
    'e=>{e.s(["metadata",0,1])}',
    'function(e){e.s(["metadata",0,1])}',
  ]) {
    const { root, report } = await recover(
      t,
      `globalThis.TURBOPACK.push(["metadata",${callback}]);`,
    );
    assert.equal(report.modules.length, 0);
    const source = await (
      await openCorpus(root)
    ).javascript("evidence/web/objects/source.js");
    assert.equal(source.factories.length, 0);
  }
});
test("a leading nested two-element ID/factory registration remains supported", async (t) => {
  const { root, report } = await recover(
    t,
    'globalThis.TURBOPACK.push(["chunk",[7,e=>{e.s(["nested",0,7])}],8,e=>{e.s(["outer",0,8])}]);',
  );
  assert.deepEqual(
    report.modules.flatMap((m) => m.ids).sort((a, b) => a - b),
    [7, 8],
  );
  const corpus = await openCorpus(root);
  assert.equal((await corpus.factory(7)).id, 7);
  assert.equal((await corpus.factory(8)).id, 8);
});
