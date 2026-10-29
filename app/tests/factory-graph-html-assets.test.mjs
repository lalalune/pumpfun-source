import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile, writeFile, rm } from "node:fs/promises";
import { join } from "node:path";
import test from "node:test";
import { buildGraph } from "../scripts/factory-graph/core.mjs";
import { fixture } from "./factory-graph-fixture.mjs";

async function attributed(t, html, { query = "" } = {}) {
  const root = await fixture();
  t.after(() => rm(root, { recursive: true, force: true }));
  const manifestPath = join(root, "evidence/web/manifest.json");
  const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
  const document = manifest.records.find((r) => r.path.endsWith("home.html"));
  await writeFile(join(root, document.path), html);
  document.bytes = Buffer.byteLength(html);
  document.sha256 = createHash("sha256").update(html).digest("hex");
  const script = manifest.records.find((r) => r.path.endsWith("source.js"));
  script.url += query;
  script.final_url = script.url;
  await writeFile(manifestPath, JSON.stringify(manifest));
  const indexPath = join(root, "recovered/modules.json");
  const index = JSON.parse(await readFile(indexPath, "utf8"));
  for (const module of index.modules)
    for (const origin of module.origins)
      if (origin.source === script.path) origin.url = script.url;
  await writeFile(indexPath, JSON.stringify(index));
  const reports = await buildGraph(root, {
    routes: ["/"],
    targetLines: 4,
    maximumLines: 100,
  });
  return reports["MODULE-IDENTITIES.json.gz"].some((n) =>
    n.routeSeeds.includes("/"),
  );
}

test("HTML entity decoding and URL fragments preserve authenticated route seeds", async (t) => {
  for (const src of [
    "/_next/static/chunks/source.js?dpl=rev&amp;mode=x",
    "/_next/static/chunks/source.js?dpl=rev&#38;mode=x",
    "/_next/static/chunks/source.js?dpl=rev&mode=x#ignored",
  ]) {
    assert.equal(
      await attributed(t, `<script src="${src}"></script>`, {
        query: "?dpl=rev&mode=x",
      }),
      true,
      src,
    );
  }
});
test("comments, data attributes and ordinary text cannot create route script seeds", async (t) => {
  for (const html of [
    '<!-- <script src="/_next/static/chunks/source.js"></script> -->',
    '<script data-src="/_next/static/chunks/source.js"></script>',
    '<p>"/_next/static/chunks/source.js"</p>',
  ]) {
    assert.equal(await attributed(t, html), false, html);
  }
});
test("normal script attributes and inline recorded chunk strings keep their seeds", async (t) => {
  for (const html of [
    '<script src="/_next/static/chunks/source.js"></script>',
    '<script>self.__next_f.push([1,"/_next/static/chunks/source.js"])</script>',
    '<link rel="preload" as="script" href="/_next/static/chunks/source.js">',
    '<link rel="modulepreload" href="/_next/static/chunks/source.js">',
  ]) {
    assert.equal(await attributed(t, html), true, html);
  }
});
