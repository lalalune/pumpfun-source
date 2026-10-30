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
} from "../scripts/original-search-idle-strip.mjs";
import { createSearchIdleStrip } from "../reconstruction/search-idle-strip/client.mjs";
test("complete Discover strip/tiles/scroll frames and MAIN/provider boundaries authenticate", async () => {
  const c = await verify();
  assert.equal(c.retained.length, 19);
  assert.equal(c.requiredFunctions.length, 16);
  assert.equal(c.requiredRenderers.length, 12);
  assert.equal(c.constants.SEARCH, 9);
  assert.equal(c.constants.WEB_AVATAR_DECORATIONS, "webAvatarDecorations");
  assert(
    c.proofs.some(
      (p) => p.label === "actual MAIN/#1925 idle-strip props handoff",
    ),
  );
  for (const id of [782067, 521368, 850175, 662093])
    assert(c.bindings.some((b) => b.id === id));
});
test("no default provider/presentation capability", () => {
  assert.throws(
    () => createSearchIdleStrip(),
    /Explicit idle strip capability/,
  );
  assert.throws(
    () =>
      createSearchIdleStrip(
        new Proxy(
          {},
          {
            get: () => () => {
              throw Error("must not acquire or execute");
            },
          },
        ),
      ),
    /Explicit idle strip renderer/,
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
      after = before.replace("o.scrollLeft <= 1", "o.scrollLeft <= 0");
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
