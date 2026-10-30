import { test } from "node:test";
import assert from "node:assert/strict";
import {
  mkdtemp,
  readFile,
  writeFile,
  mkdir,
  link,
  copyFile,
  rm,
} from "node:fs/promises";
import path from "node:path";
import {
  APP_ROOT,
  DIRECTORY,
  verify,
} from "../scripts/original-group-search-read-model.mjs";
import { createGroupSearchReadModel } from "../reconstruction/group-search-read-model/client.mjs";
test("all five physical reader/model contexts and exact MAIN/Recent/SearchRows handoffs authenticate", async () => {
  const c = await verify();
  assert.equal(c.contexts.length, 5);
  for (const v of c.contexts) {
    assert.equal(v.imports.length, 3);
    assert(v.readerLocals.length >= 3);
    assert(v.schemaLocals.length >= 7);
  }
  assert(
    c.proofs.some(
      (p) => p.label === "actual MAIN/RecentTerms group reader call",
    ),
  );
  assert(
    c.proofs.some(
      (p) => p.label === "actual MAIN/SearchRows group projection handoff",
    ),
  );
});
test("no default API/schema/provider context", () => {
  assert.throws(() => createGroupSearchReadModel(), /Explicit group schema/);
  assert.throws(
    () =>
      createGroupSearchReadModel({
        z: { string() {} },
        contract: {
          "GET /groups/search": { response: {} },
          "GET /users/{id}": { response: {} },
        },
      }),
    /Explicit captured group source context/,
  );
});
test("canonical client and metadata edits fail in a source-only synthetic root", async () => {
  const c = JSON.parse(
      await readFile(path.join(APP_ROOT, DIRECTORY, "contract.json"), "utf8"),
    ),
    files = new Set([
      "evidence/web/manifest.json",
      "recovered/modules.json",
      "scripts/verify-search-planner.mjs",
      DIRECTORY + "/client.mjs",
      DIRECTORY + "/contract.json",
    ]);
  function sources(v) {
    if (Array.isArray(v)) v.forEach(sources);
    else if (v && typeof v === "object") Object.values(v).forEach(sources);
    else if (
      typeof v === "string" &&
      /^evidence\/web\/objects\/[^/]+\.js$/.test(v)
    )
      files.add(v);
  }
  sources(c);
  const dir = await mkdtemp(path.join(APP_ROOT, ".search-result-negative-"));
  try {
    for (const file of files) {
      await mkdir(path.dirname(path.join(dir, file)), { recursive: true });
      if (file.startsWith(DIRECTORY))
        await copyFile(path.join(APP_ROOT, file), path.join(dir, file));
      else
        try {
          await link(path.join(APP_ROOT, file), path.join(dir, file));
        } catch (e) {
          if (e.code !== "EXDEV") throw e;
          await copyFile(path.join(APP_ROOT, file), path.join(dir, file));
        }
    }
    await verify(dir);
    const p = path.join(dir, DIRECTORY, "client.mjs"),
      before = await readFile(p, "utf8"),
      after = before.replace('"GET /groups/search"', '"GET /groups/edited"');
    assert.notEqual(after, before);
    await writeFile(p, after);
    await assert.rejects(verify(dir), /canonical client/);
    await writeFile(p, before);
    await writeFile(
      path.join(dir, DIRECTORY, "contract.json"),
      JSON.stringify(c),
    );
    await assert.rejects(verify(dir), /canonical contract/);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});
