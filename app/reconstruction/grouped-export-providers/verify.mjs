import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { inspectExportProviders } from "../../scripts/factory-graph/export-providers.mjs";

const appRoot = path.resolve(import.meta.dirname, "../..");
const source = "evidence/web/objects/0f4bad575370faed.js";
for (const id of ["396623", "660315"]) {
  const bytes = JSON.stringify(await inspectExportProviders(appRoot, id, [source]), null, 2) + "\n";
  const target = path.join(import.meta.dirname, `providers-${id}.json`);
  if (process.argv.includes("--write")) await writeFile(target, bytes);
  else assert.equal(await readFile(target, "utf8"), bytes, `provider snapshot ${id}`);
}
const preserved = JSON.parse(await readFile(path.join(import.meta.dirname, "preserved-inputs.json"), "utf8"));
const { sha256 } = await import("../../scripts/original-contracts/source.mjs");
for (const entry of preserved.files) {
  const bytes = await readFile(path.resolve(appRoot, "..", entry.path));
  assert.equal(bytes.length, entry.bytes, entry.path);
  assert.equal(sha256(bytes), entry.sha256, entry.path);
}
console.log("PASS: two source-context provider snapshots and 15 preserved input/report files; no captured execution");
