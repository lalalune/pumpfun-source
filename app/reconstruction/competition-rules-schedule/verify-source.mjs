import assert from "node:assert/strict";
import { readFile, realpath } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "@babel/parser";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  sha256,
  member,
} from "../../scripts/original-contracts/source.mjs";
const HERE = path.dirname(fileURLToPath(import.meta.url)),
  APP = path.resolve(HERE, "../..");
const evidence = JSON.parse(
    await readFile(path.join(HERE, "source-evidence.json"), "utf8"),
  ),
  corpus = await openCorpus(APP);
const original = await corpus.factory(590407, {
  source: evidence.source.source,
});
assert.deepEqual(original.provenance, evidence.source);
const helper = exactlyOne(
  findNodes(
    original.node,
    (n) => n.type === "VariableDeclarator" && n.id?.name === "tr",
  ),
  "actual schedule helper",
);
assert.deepEqual(
  original.witness(helper, evidence.helper.label),
  evidence.helper,
);
assert.equal(
  findNodes(
    helper,
    (n) => n.type === "StringLiteral" && n.value === evidence.sourceClass,
  ).length,
  1,
);
const calls = findNodes(
  original.node,
  (n) => n.type === "CallExpression" && n.arguments[0]?.name === "tr",
);
assert.deepEqual(
  calls.map((n) => original.witness(n, "actual schedule label/start/end call")),
  evidence.calls,
);
assert.equal(calls.length, 2);
async function retained(record) {
  assert.deepEqual(corpus.records.get(record.path), record);
  const file = path.join(APP, record.path);
  assert.equal(await realpath(file), file);
  const bytes = await readFile(file);
  assert.equal(bytes.length, record.bytes);
  assert.equal(sha256(bytes), record.sha256);
  return bytes;
}
const cssBytes = await retained(evidence.stylesheet.record),
  css = new TextDecoder("utf-8", { fatal: true }).decode(cssBytes);
const { utf16, utf8, rule } = evidence.stylesheet;
assert.equal(css.slice(...utf16), rule);
assert.equal(cssBytes.subarray(...utf8).toString("utf8"), rule);
assert.equal(sha256(rule), evidence.stylesheet.sha256);
assert.equal(rule, ".flex-1{flex:1}");
const html = (await retained(evidence.leaderboardHtml)).toString("utf8");
assert.ok(html.includes(new URL(evidence.stylesheet.record.url).pathname));
const native = await readFile(
    path.join(
      APP,
      "packages/frontend/src/app/leaderboard/competition-rules.tsx",
    ),
    "utf8",
  ),
  tree = parse(native, {
    sourceType: "module",
    plugins: ["typescript", "jsx"],
  });
const schedule = exactlyOne(
  findNodes(
    tree,
    (n) =>
      n.type === "JSXElement" &&
      n.openingElement.name?.name === "section" &&
      findNodes(
        n,
        (m) =>
          m.type === "JSXExpressionContainer" &&
          member(m.expression, "copy", "schedule"),
      ).length === 1,
  ),
  "actual Schedule section",
);
const dl = exactlyOne(
  findNodes(
    schedule,
    (n) => n.type === "JSXOpeningElement" && n.name?.name === "dl",
  ),
  "actual schedule dl",
);
const className = exactlyOne(
  dl.attributes.filter(
    (n) => n.type === "JSXAttribute" && n.name.name === "className",
  ),
  "schedule scope",
);
assert.ok(member(className.value.expression, "styles", "schedule"));
const nativeCss = await readFile(
  path.join(
    APP,
    "packages/frontend/src/app/leaderboard/competition-rules.module.css",
  ),
  "utf8",
);
assert.equal(
  (nativeCss.match(/\.schedule\s+\.row\s+dd\s*\{\s*flex:\s*1;\s*\}/g) ?? [])
    .length,
  1,
);
console.log(
  "Verified actual original schedule helper/callers, stylesheet/HTML linkage and native schedule-only value allocation; no full component/provider/pixel parity claim",
);
