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
  recover,
  verify,
} from "../scripts/original-search-dialog-controller.mjs";
import { createSearchDialogController } from "../reconstruction/search-dialog-controller/client.mjs";
test("full original controller, actual lazy child, all group constants and credited bridges authenticate", async () => {
  const c = await verify();
  assert.equal(
    c.factory.sha256,
    "9e5affafd605f47d6c9466659c4bc0a654fae027f4beff481337a1cdf1263828",
  );
  assert.equal(c.groupLimits.length, 5);
  assert(c.groupLimits.every((r) => r.pageSize === 20 && r.maxOffset === 500));
  assert.equal(c.bindings.find((r) => r.id === 379705).variants.length, 4);
  assert.equal(c.bindings.find((r) => r.id === 600775).variants.length, 3);
  assert.equal(c.requiredRendererComponents.length, 17);
  assert(
    c.proofs.some(
      (p) => p.label === "actual parent lazy-child onMounted handoff",
    ),
  );
});
test("no default provider, renderer or browser acquisition", () => {
  assert.throws(
    () => createSearchDialogController(),
    /Explicit SearchDialog capability/,
  );
  const p = new Proxy(
    {},
    {
      get: () => () => {
        throw Error("Provider must not run during construction");
      },
    },
  );
  assert.throws(
    () => createSearchDialogController(p),
    /Explicit SearchDialog renderer/,
  );
});
test("public checker rejects edited source and semantically equal noncanonical metadata", async () => {
  const contract = JSON.parse(
      await readFile(path.join(APP_ROOT, DIRECTORY, "contract.json"), "utf8"),
    ),
    nav = JSON.parse(
      await readFile(
        path.join(APP_ROOT, "reconstruction/search-navigation/PROVENANCE.json"),
        "utf8",
      ),
    ),
    keys = JSON.parse(
      await readFile(
        path.join(APP_ROOT, "reconstruction/search-shortcuts/PROVENANCE.json"),
        "utf8",
      ),
    );
  const files = new Set([
    "evidence/web/manifest.json",
    "recovered/modules.json",
    ...contract.proofs.map((p) => p.source),
    ...nav.proofs.map((p) => p.source),
    ...keys.proofs.map((p) => p.source),
    ...nav.opaqueBoundaries
      .flatMap((b) => b.variants ?? [])
      .flatMap((b) => b.origins ?? [])
      .map((o) => o.source),
    ...contract.bridges.dependencies.map((p) => p.file),
    "packages/frontend/src/components/shell/search/SearchDialog.tsx",
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
  [contract, nav, keys].forEach(sources);
  const dir = await mkdtemp(path.join(APP_ROOT, ".search-dialog-negative-"));
  try {
    for (const file of files) {
      assert.equal(typeof file, "string");
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
    const cp = path.join(dir, DIRECTORY, "client.mjs"),
      before = await readFile(cp, "utf8");
    await writeFile(cp, before.replace('k("all")', 'k("users")'));
    assert.notEqual(await readFile(cp, "utf8"), before);
    await assert.rejects(verify(dir), /canonical client/);
    await writeFile(cp, before);
    await writeFile(
      path.join(dir, DIRECTORY, "contract.json"),
      JSON.stringify(contract),
    );
    await assert.rejects(verify(dir), /canonical contract/);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});
