import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import {
  exactlyOne,
  findNodes,
  openCorpus,
  walk,
} from "../../scripts/original-contracts/source.mjs";

const root = fileURLToPath(new URL("../../", import.meta.url));
const corpus = await openCorpus(root);
const factory = await corpus.factory(400466, {
  source: "evidence/web/objects/13c13db9eb86191b.js",
});
assert.equal(
  factory.provenance.sha256,
  "b55e1d78341162edfc6c5ff1ba32c4b4faa3d0ade6de3a39f440fe39f2e9e5dd",
);

const component = exactlyOne(
  findNodes(factory.node, (node) =>
    node.type === "FunctionDeclaration" && node.id.name === "rD"),
  "captured Back component",
);
const guard = exactlyOne(
  findNodes(factory.node, (node) =>
    node.type === "VariableDeclarator" && node.id.name === "rM"),
  "captured hidden paths",
);
const header = exactlyOne(
  findNodes(factory.node, (node) =>
    node.type === "FunctionDeclaration" && node.id.name === "aW"),
  "captured header",
);
const calls = [];
walk(factory.node, (node, ancestors) => {
  if (node.type !== "CallExpression" || node.arguments[0]?.name !== "rD") return;
  assert.equal(
    ancestors.filter((parent) => parent.type === "FunctionDeclaration").at(-1),
    header,
    "Back must be used by the actual header",
  );
  calls.push(node);
});
assert.equal(calls.length, 2);
const record = (node, label) => ({
  witness: factory.witness(node, label),
  text: factory.text(node),
});
const result = {
  schemaVersion: 1,
  method: "Authenticated captured JavaScript parsed as AST; never executed",
  factory: factory.provenance,
  component: record(component, "actual Go-back component"),
  guard: record(guard, "actual hidden route set"),
  header: factory.witness(header, "actual header containing both Back calls"),
  actualHeaderCalls: calls.map((node) => record(node, "actual header Back consumer")),
};
const target = new URL("source.json", import.meta.url);
if (process.argv.includes("--write")) {
  await writeFile(target, JSON.stringify(result, null, 2) + "\n");
} else {
  assert.deepEqual(result, JSON.parse(await readFile(target, "utf8")));
  console.log("PASS: exact original Back component, hidden paths and both used header calls");
}
