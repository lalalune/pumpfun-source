import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import {
  mkdtemp,
  mkdir,
  readFile,
  rm,
  symlink,
  writeFile,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import prettier from "prettier";
import {
  analyzeFactory,
  buildGraph,
  countSourceLines,
  publishGraph,
  verifyGraph,
} from "../scripts/factory-graph/core.mjs";

const hash = (value) => createHash("sha256").update(value).digest("hex");

export async function fixture({
  corruptHash = false,
  corruptRange = false,
  duplicateOrigin = false,
  reverse = false,
} = {}) {
  const root = await mkdtemp(join(tmpdir(), "factory-graph-"));
  for (const path of ["recovered/modules", "evidence/web/objects", "contracts"])
    await mkdir(join(root, path), { recursive: true });
  const factories = [
    {
      id: 1,
      raw: `(e)=>{var t=e.i(2);e.A(3);e.i(99);e.i("react");e.s(["answer",0,t],1)}`,
    },
    { id: 2, raw: `(e)=>{e.s(["value",0,42],2)}` },
    { id: 2, raw: `(e)=>{e.s(["value",0,43],2)}` },
    { id: 3, raw: `(e)=>{e.i(3);e.s(["cycle",0,true],3)}` },
  ];
  const source = `globalThis.TURBOPACK.push(["fixture",${factories.map((item) => `${item.id},${item.raw}`).join(",")}]);`;
  const jsPath = "evidence/web/objects/source.js";
  await writeFile(join(root, jsPath), source);
  const duplicateFactory = factories.at(-1);
  const otherSource = `globalThis.TURBOPACK.push(["other",${duplicateFactory.id},${duplicateFactory.raw}]);`;
  const otherPath = "evidence/web/objects/other.js";
  if (duplicateOrigin) await writeFile(join(root, otherPath), otherSource);
  const html = `<html><script src="/_next/static/chunks/source.js"></script></html>`;
  const htmlPath = "evidence/web/objects/home.html";
  await writeFile(join(root, htmlPath), html);
  const modules = [];
  for (const item of factories) {
    const start = source.indexOf(item.raw);
    const digest = hash(item.raw);
    const path = `recovered/modules/${item.id}-${digest.slice(0, 12)}.js`;
    await writeFile(
      join(root, path),
      "// Recovered Turbopack factory. Requires original runtime/import IDs; not a standalone source module.\n" +
        (await prettier.format(`(${item.raw});`, { parser: "babel" })),
    );
    modules.push({
      ids: [item.id],
      sha256: digest,
      origins: [
        {
          source: jsPath,
          url: "https://pump.fun/_next/static/chunks/source.js",
          start,
          end: start + item.raw.length,
        },
      ],
      path,
    });
  }
  if (duplicateOrigin) {
    const duplicateModule = modules.find(
      (module) => module.sha256 === hash(duplicateFactory.raw),
    );
    const start = otherSource.indexOf(duplicateFactory.raw);
    duplicateModule.origins.push({
      source: otherPath,
      url: "https://pump.fun/_next/static/chunks/other.js",
      start,
      end: start + duplicateFactory.raw.length,
    });
  }
  if (reverse) modules.reverse();
  if (corruptRange) modules[0].origins[0].end -= 1;
  const manifest = {
    records: [
      {
        url: "https://pump.fun/_next/static/chunks/source.js",
        final_url: "https://pump.fun/_next/static/chunks/source.js",
        status: 200,
        path: jsPath,
        bytes: Buffer.byteLength(source),
        sha256: corruptHash ? "0".repeat(64) : hash(source),
        headers: { "content-type": "application/javascript" },
      },
      ...(duplicateOrigin
        ? [
            {
              url: "https://pump.fun/_next/static/chunks/other.js",
              final_url: "https://pump.fun/_next/static/chunks/other.js",
              status: 200,
              path: otherPath,
              bytes: Buffer.byteLength(otherSource),
              sha256: hash(otherSource),
              headers: { "content-type": "application/javascript" },
            },
          ]
        : []),
      {
        url: "https://pump.fun/",
        final_url: "https://pump.fun/",
        status: 200,
        path: htmlPath,
        bytes: Buffer.byteLength(html),
        sha256: hash(html),
        headers: { "content-type": "text/html; charset=utf-8" },
      },
    ],
  };
  await writeFile(
    join(root, "recovered/modules.json"),
    JSON.stringify({
      rangeEncoding:
        "UTF-16 code-unit half-open offsets in UTF-8 decoded source",
      modules,
      failures: [],
    }),
  );
  await writeFile(
    join(root, "evidence/web/manifest.json"),
    JSON.stringify(manifest),
  );
  await writeFile(
    join(root, "contracts/internal-operations.json"),
    JSON.stringify({ operations: [] }),
  );
  await writeFile(
    join(root, "contracts/developer-bindings.json"),
    JSON.stringify({ bindings: [] }),
  );
  return root;
}
