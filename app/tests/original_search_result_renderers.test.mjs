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
} from "../scripts/original-search-result-renderers.mjs";
import { createSearchResultRenderers } from "../reconstruction/search-result-renderers/client.mjs";
test("all complete result nodes, MAIN caller handoffs, provider variants and inherited route authenticate", async () => {
  const c = await verify();
  assert.equal(c.retained.length, 13);
  assert.equal(c.requiredRenderers.length, 12);
  assert.equal(c.requiredFunctions.length, 19);
  assert.equal(c.constants.ACTIVE_SEARCH_COIN_SEARCH_FEED, 15);
  for (const name of ["Z", "ee", "en", "et", "eu"])
    assert(
      c.proofs.some(
        (p) =>
          p.label === "actual MAIN owning-controller result handoff " + name,
      ),
    );
  assert(c.bindings.some((b) => b.id === 705313));
  assert(c.bindings.some((b) => b.id === 179736));
});
test("no default provider/presentation capability", () => {
  assert.throws(
    () => createSearchResultRenderers(),
    /Explicit search result capability/,
  );
  assert.throws(
    () =>
      createSearchResultRenderers(
        new Proxy(
          {},
          {
            get: () => () => {
              throw Error("must not acquire or execute");
            },
          },
        ),
      ),
    /Explicit search result renderer/,
  );
});
test("canonical client and metadata edits fail in a source-only synthetic root", async () => {
  const c = JSON.parse(
      await readFile(path.join(APP_ROOT, DIRECTORY, "contract.json"), "utf8"),
    ),
    nav = JSON.parse(
      await readFile(
        path.join(APP_ROOT, "reconstruction/search-navigation/PROVENANCE.json"),
        "utf8",
      ),
    ),
    files = new Set([
      "evidence/web/manifest.json",
      "recovered/modules.json",
      "scripts/verify-search-planner.mjs",
      DIRECTORY + "/client.mjs",
      DIRECTORY + "/contract.json",
      ...c.dependencies.map((x) => x.file),
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
  [c, nav].forEach(sources);
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
      after = before.replace("itemPosition: Z,", "itemPosition: Z + 1,");
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
