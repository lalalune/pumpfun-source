import { createTestSymlink } from './helpers/test-symlink.mjs';
import assert from "node:assert/strict";
import test from "node:test";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  buildMarketBoardBindings,
  verifyMarketBoardBindings,
} from "../scripts/verify-market-board-bindings.mjs";
const root = fileURLToPath(new URL("..", import.meta.url));
const contract = JSON.parse(
  await fs.readFile(
    path.join(root, "contracts/market-board-bindings.json"),
    "utf8",
  ),
);
async function workspace(t) {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "market-bindings-"));
  t.after(() => fs.rm(dir, { force: true, recursive: true }));
  for (const relative of [
    ...Object.keys(contract.sources),
    "evidence/web/manifest.json",
    "recovered/modules.json",
    "contracts/market-board-bindings.json",
  ]) {
    await fs.mkdir(path.dirname(path.join(dir, relative)), { recursive: true });
    await fs.copyFile(path.join(root, relative), path.join(dir, relative));
  }
  return dir;
}
async function edit(dir, file, change) {
  const target = path.join(dir, file);
  const value = JSON.parse(await fs.readFile(target, "utf8"));
  change(value);
  await fs.writeFile(target, JSON.stringify(value));
}
test("four immutable objects bind ten exact factories, ten imports and fourteen exports", async () => {
  assert.deepEqual(await verifyMarketBoardBindings(root), {
    sources: 4,
    factories: 10,
    imports: 10,
  });
  const result = await buildMarketBoardBindings(root);
  assert.equal(result.exports.length, 14);
  assert.equal(result.origin.value, "https://advanced-indexer.pump.fun");
  assert.equal(result.request.limitUpperCap, 150);
  assert.equal(result.request.followedHoldersLimit, 5);
});
test("raw source tampering fails even when the manifest is rewritten", async (t) => {
  const dir = await workspace(t),
    source = contract.factories.board.source;
  await fs.appendFile(path.join(dir, source), "\n");
  await assert.rejects(verifyMarketBoardBindings(dir), /source bytes/);
  await edit(dir, "evidence/web/manifest.json", (manifest) => {
    manifest.records.find((r) => r.path === source).bytes++;
  });
  await assert.rejects(verifyMarketBoardBindings(dir), /manifest source/);
});
test("all selected raw sources are required, no formatted-module fallback", async (t) => {
  const dir = await workspace(t);
  await fs.unlink(path.join(dir, contract.factories.origins.source));
  await assert.rejects(verifyMarketBoardBindings(dir), /ENOENT/);
});
for (const [name, mutate] of [
  [
    "factory hash",
    (m) => {
      m.sha256 = "0".repeat(64);
    },
  ],
  [
    "IDs",
    (m) => {
      m.ids[0]++;
    },
  ],
  [
    "UTF-16 range",
    (m) => {
      m.origins[0].start++;
    },
  ],
  [
    "source URL",
    (m) => {
      m.origins[0].url += "?different";
    },
  ],
  [
    "source identity",
    (m) => {
      m.origins[0].source = "evidence/web/objects/other.js";
    },
  ],
])
  test(`rejects mutated index ${name}`, async (t) => {
    const dir = await workspace(t);
    await edit(dir, "recovered/modules.json", (inventory) =>
      mutate(
        inventory.modules.find(
          (m) => m.sha256 === contract.factories.board.sha256,
        ),
      ),
    );
    await assert.rejects(verifyMarketBoardBindings(dir), /inventory/);
  });
test("rejects duplicate manifest identities", async (t) => {
  const dir = await workspace(t);
  await edit(dir, "evidence/web/manifest.json", (manifest) => {
    manifest.records.push(
      manifest.records.find((r) => r.path === contract.factories.board.source),
    );
  });
  await assert.rejects(verifyMarketBoardBindings(dir), /manifest identity/);
});
test("rejects symlinks rather than following replacement source bytes", async (t) => {
  const dir = await workspace(t),
    source = path.join(dir, contract.factories.board.source);
  const actual = path.join(dir, "replacement.js");
  await fs.rename(source, actual);
  if (!await createTestSymlink(t, actual, source)) return;
  await assert.rejects(verifyMarketBoardBindings(dir), /symlink/);
});
for (const field of [
  "origin",
  "request",
  "responseBoundary",
  "imports",
  "exports",
  "limits",
])
  test(`rejects edited generated ${field}`, async (t) => {
    const dir = await workspace(t);
    await edit(dir, "contracts/market-board-bindings.json", (value) => {
      value[field] = null;
    });
    await assert.rejects(verifyMarketBoardBindings(dir), /generated contract/);
  });
