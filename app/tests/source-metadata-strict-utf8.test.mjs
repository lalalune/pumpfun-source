import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, mkdir, writeFile, rm } from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";
import {
  openCorpus,
  RANGE_ENCODING,
  sha256,
} from "../scripts/original-contracts/source.mjs";
test("source metadata cannot silently replace malformed UTF-8 bytes", async (t) => {
  const root = await mkdtemp(path.join(os.tmpdir(), "source-metadata-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  await mkdir(path.join(root, "evidence/web"), { recursive: true });
  await mkdir(path.join(root, "recovered"));
  const files = {
    "evidence/web/manifest.json": { records: [], note: "MARKER" },
    "recovered/modules.json": {
      rangeEncoding: RANGE_ENCODING,
      modules: [],
      note: "MARKER",
    },
  };
  const save = async () => {
    for (const [file, value] of Object.entries(files))
      await writeFile(path.join(root, file), JSON.stringify(value));
  };
  for (const file of Object.keys(files)) {
    await save();
    const [before, after] = JSON.stringify(files[file]).split("MARKER");
    await writeFile(
      path.join(root, file),
      Buffer.concat([
        Buffer.from(before),
        Buffer.from([0xff]),
        Buffer.from(after),
      ]),
    );
    await assert.rejects(openCorpus(root), /encoded data/);
  }
  files["evidence/web/manifest.json"].note = "é😀";
  await save();
  const corpus = await openCorpus(root);
  assert.equal(corpus.manifest.note, "é😀");
  assert.equal(
    corpus.anchors.manifestSha256,
    sha256(Buffer.from(JSON.stringify(files["evidence/web/manifest.json"]))),
  );
  const retained = await openCorpus(
    fileURLToPath(new URL("..", import.meta.url)),
  );
  assert.ok(retained.index.modules.length > 0);
});
