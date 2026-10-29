// Immutable captures are parsed as data, never evaluated.
import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { parse } from "@babel/parser";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  member,
  propertyName,
  sha256,
} from "./original-contracts/source.mjs";
const APP = fileURLToPath(new URL("..", import.meta.url)),
  DIRECTORY = "reconstruction/settings-identifier-search";
function canonical(node) {
  if (Array.isArray(node)) return node.map(canonical);
  if (!node || typeof node !== "object") return node;
  return Object.fromEntries(
    Object.entries(node)
      .filter(
        ([key]) =>
          ![
            "start",
            "end",
            "loc",
            "extra",
            "comments",
            "leadingComments",
            "trailingComments",
            "innerComments",
          ].includes(key),
      )
      .map(([key, value]) => [key, canonical(value)]),
  );
}
export async function recover(root = APP) {
  const corpus = await openCorpus(root),
    rows = corpus.index.modules.filter((row) => row.ids.includes(124884));
  assert.equal(rows.length, 1);
  assert.equal(
    rows[0].sha256,
    "dfcb487f79e63fa817cef92fd322e172c6d44fb2270bad175820a463b2e382ea",
  );
  assert.equal(rows[0].origins.length, 1);
  const factory = await corpus.factory(124884, {
    source: "evidence/web/objects/4490d02ba2117672.js",
  });
  const operation = exactlyOne(
    findNodes(
      factory.node,
      (node) =>
        node.type === "CallExpression" &&
        node.callee.type === "MemberExpression" &&
        propertyName(node.callee.property) === "replace" &&
        member(node.callee.object, "e", "id"),
    ),
    "actual original identifier search operand",
  );
  const fields = exactlyOne(
    findNodes(
      factory.node,
      (node) =>
        node.type === "ArrayExpression" && node.elements.includes(operation),
    ),
    "actual original search document",
  );
  const filter = exactlyOne(
    findNodes(
      factory.node,
      (node) =>
        node.type === "CallExpression" &&
        node.callee.type === "MemberExpression" &&
        propertyName(node.callee.property) === "filter" &&
        node.arguments[0] &&
        findNodes(node.arguments[0], (child) => child === operation).length ===
          1,
    ),
    "actual original per-definition filter",
  );
  assert.equal(filter.arguments[0].params[0].name, "e");
  const caller = exactlyOne(
    factory.node.body.body.filter(
      (node) => node.type === "FunctionDeclaration" && node.id.name === "eb",
    ),
    "actual original results consumer",
  );
  const record = {
    schema: 1,
    reviewBase: "094a06f18df738d41e77070c1a009e135671ac1a",
    scope:
      "Restore only original identifier search text within already-mapped native Settings definitions",
    indexEntry: rows[0],
    factory: factory.provenance,
    witnesses: [
      factory.witness(
        operation,
        "actual identifier indexing with periods replaced by spaces",
      ),
      factory.witness(
        fields,
        "actual translated label/description/search terms/section/id search document",
      ),
      factory.witness(
        filter,
        "complete source token-AND definition filter and hidden guard",
      ),
      factory.witness(
        caller,
        "complete original query/results/grouping consumer",
      ),
    ],
    native: {
      file: "packages/frontend/src/components/settings/settings-model.ts",
      function: "findSettings",
      bindingAdaptation:
        "Original filter parameter e becomes existing native filter parameter setting; only its id.replace expression is restored.",
    },
    overlap: {
      pr: 1188,
      scope:
        "Open concurrent normalization-order fix remains distinct. This unit preserves current Unicode/locale/order policy; integration may touch the same file, without copying that patch.",
    },
    limits: [
      "Native search remains limited to existing static mapped definitions; no added setting or preference value/control.",
      "Only original ID indexing operand is restored. This is not whole original Settings/search/provider equivalence.",
      "No extra normalization of dotted query strings, new Unicode policy, ranking, server preferences, auth, mutation or completion claim.",
      "Captures and previous source/validation packages remain unchanged; no captured-code execution or tenant requests.",
    ],
  };
  return { record, operation };
}
export async function verify(root = APP) {
  const { record, operation } = await recover(root);
  assert.equal(
    await readFile(path.join(root, DIRECTORY, "SOURCE.json"), "utf8"),
    JSON.stringify(record, null, 2) + "\n",
  );
  const native = parse(
    await readFile(path.join(root, record.native.file), "utf8"),
    { sourceType: "module", plugins: ["typescript"] },
  );
  const fn = exactlyOne(
    findNodes(
      native,
      (node) =>
        node.type === "FunctionDeclaration" && node.id?.name === "findSettings",
    ),
    "actual native findSettings",
  );
  const filter = exactlyOne(
    findNodes(
      fn,
      (node) =>
        node.type === "CallExpression" &&
        member(node.callee, "SETTINGS_DEFINITIONS", "filter"),
    ),
    "used native definition filter",
  );
  assert.equal(filter.arguments[0].params[0].name, "setting");
  const actual = exactlyOne(
    findNodes(
      filter.arguments[0],
      (node) =>
        node.type === "CallExpression" &&
        node.callee.type === "MemberExpression" &&
        propertyName(node.callee.property) === "replace" &&
        member(node.callee.object, "setting", "id"),
    ),
    "used native identifier operand",
  );
  const fields = exactlyOne(
    findNodes(
      filter.arguments[0],
      (node) =>
        node.type === "ArrayExpression" && node.elements.includes(actual),
    ),
    "actual native search document",
  );
  assert.ok(
    findNodes(
      filter.arguments[0],
      (node) =>
        node.type === "CallExpression" &&
        node.callee.type === "MemberExpression" &&
        propertyName(node.callee.property) === "join" &&
        node.callee.object === fields,
    ).length === 1,
  );
  const adapted = structuredClone(operation);
  adapted.callee.object.object.name = "setting";
  assert.deepEqual(canonical(actual), canonical(adapted));
  return record;
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  if (process.argv.includes("--write")) {
    const { record } = await recover();
    await mkdir(path.join(APP, DIRECTORY), { recursive: true });
    await writeFile(
      path.join(APP, DIRECTORY, "SOURCE.json"),
      JSON.stringify(record, null, 2) + "\n",
    );
  } else await verify();
  console.log(
    process.argv.includes("--write")
      ? "Wrote original source provenance; native operand verification is the default command"
      : "Verified original Settings identifier-index operand and actual used native search document; no normalization/provider parity claim",
  );
}
