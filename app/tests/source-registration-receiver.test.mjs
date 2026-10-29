import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, mkdir, writeFile, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import {
  openCorpus,
  sha256,
  RANGE_ENCODING,
} from "../scripts/original-contracts/source.mjs";
async function fixture(t, text) {
  const root = await mkdtemp(path.join(os.tmpdir(), "registration-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  await mkdir(path.join(root, "evidence/web/objects"), { recursive: true });
  await mkdir(path.join(root, "recovered"));
  const source = "evidence/web/objects/chunk.js",
    url = "https://example.invalid/chunk.js",
    start = text.indexOf("r=>{}"),
    end = start + 7;
  await writeFile(path.join(root, source), text);
  await writeFile(
    path.join(root, "evidence/web/manifest.json"),
    JSON.stringify({
      records: [
        {
          path: source,
          url,
          status: 200,
          bytes: Buffer.byteLength(text),
          sha256: sha256(text),
        },
      ],
    }),
  );
  await writeFile(
    path.join(root, "recovered/modules.json"),
    JSON.stringify({
      rangeEncoding: RANGE_ENCODING,
      modules: [
        {
          ids: [7],
          sha256: sha256("r=>{}"),
          origins: [{ source, url, start, end: start + 5 }],
        },
      ],
    }),
  );
  return openCorpus(root);
}
test("mentioning TURBOPACK inside another receiver does not register a factory", async (t) => {
  const bad = await fixture(
    t,
    'other(globalThis.TURBOPACK).push(["chunk",7,r=>{}]);',
  );
  await assert.rejects(bad.factory(7), /registration/);
  const good = await fixture(
    t,
    '(globalThis.TURBOPACK||(globalThis.TURBOPACK=[])).push(["chunk",7,r=>{}]);',
  );
  assert.equal((await good.factory(7)).id, 7);
});
