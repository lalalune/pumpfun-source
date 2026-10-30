import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { createRequire } from "node:module";
import { join, dirname } from "node:path";
import { pathToFileURL, fileURLToPath } from "node:url";

const defaultApp = fileURLToPath(new URL("../../", import.meta.url));
export async function buildChainIdentity(app = process.env.PUMP_CHAIN_IDENTITY_APP ?? defaultApp) {
  const require = createRequire(join(app, "package.json"));
  const prettier = require("prettier");
  const { parse } = require("@babel/parser");
  const { openCorpus, findNodes, member, exactlyOne, sha256 } = await import(pathToFileURL(join(app, "scripts/original-contracts/source.mjs")));
  const corpus = await openCorpus(app);
  const hash = "719f637fc436bde35bcaa1da5eac3057212d49b84331e27068450218041eb6c0";
  const variants = corpus.index.modules.filter((entry) => entry.ids.includes(646908));
  assert.deepEqual(variants.map((entry) => entry.sha256), [hash], "complete reviewed identity variant set");
  assert.equal(variants[0].origins.length, 1);
  const factory = await corpus.factory(646908);
  assert.equal(factory.provenance.sha256, hash);
  assert.deepEqual(factory.ids, [646908]);
  assert.equal(factory.node.body.type, "BlockStatement");
  assert.equal(factory.node.body.body.length, 2, "whole factory has one declaration and one export registration");
  const [declaration, registration] = factory.node.body.body;
  assert.equal(declaration.type, "VariableDeclaration");
  assert.equal(registration.type, "ExpressionStatement");
  assert.ok(member(registration.expression.callee, factory.runtime, "s"));
  assert.equal(registration.expression.arguments.length, 1);
  assert.equal(registration.expression.arguments[0].type, "ArrayExpression");
  assert.equal(findNodes(factory.node, (node) => member(node, factory.runtime, "i")).length, 0, "self-contained captured application algorithm has no runtime imports");
  const elements = registration.expression.arguments[0].elements;
  const exports = [];
  for (let index = 0; index < elements.length; index += 3) {
    assert.equal(elements[index].type, "StringLiteral");
    assert.equal(elements[index + 1].value, 0);
    exports.push([elements[index].value, elements[index + 2]]);
  }
  assert.deepEqual(exports.map(([name]) => name), ["H", "c", "d", "Q", "W", "h", "J", "z", "l", "Y", "U", "C", "n", "B", "a", "R", "V", "_", "X", "M", "L", "e", "u", "f"]);
  const client = await prettier.format(`// Complete maintained adaptation of original application factory 646908.\n// Captured factories are parsed only; no original runtime or network is installed.\nexport function createChainIdentity() {\n${factory.text(declaration)}\nreturn {${exports.map(([name, value]) => `${JSON.stringify(name)}:${factory.text(value)}`).join(",")}};\n}\n`, { parser: "babel" });
  const canonical = (value) => Array.isArray(value) ? value.map(canonical) : value && typeof value === "object" ? Object.fromEntries(Object.entries(value).filter(([key]) => !["start", "end", "loc", "extra", "comments", "leadingComments", "trailingComments", "innerComments"].includes(key)).map(([key, item]) => [key, canonical(item)])) : value;
  const originalDeclarationAst = canonical(declaration);
  const adaptedBody = parse(client, { sourceType: "module" }).program.body[0].declaration.body.body;
  assert.deepEqual(canonical(adaptedBody[0]), originalDeclarationAst, "complete retained declaration AST");
  assert.equal(adaptedBody.length, 2);
  const adaptedExports = adaptedBody[1].argument.properties;
  for (let index = 0; index < exports.length; index++) assert.deepEqual(canonical(adaptedExports[index].value), canonical(exports[index][1]), `complete export ${exports[index][0]} AST`);
  const witnesses = [factory.witness(declaration, "complete identity declaration and all local algorithms"), ...exports.map(([name, node]) => factory.witness(node, `complete original export ${name}`))];
  const consumers = [];
  async function consumer(id, source, expectedHash, expectedCalls) {
    const selected = await corpus.factory(id, { source });
    assert.equal(selected.provenance.sha256, expectedHash, "reviewed physical consumer");
    const binding = exactlyOne(findNodes(selected.node, (node) => node.type === "VariableDeclarator" && node.init?.type === "CallExpression" && member(node.init.callee, selected.runtime, "i") && node.init.arguments[0]?.value === 646908), `actual ${id} identity import`);
    const calls = findNodes(selected.node, (node) => node.type === "CallExpression" && (() => { const callee = node.callee.type === "SequenceExpression" ? node.callee.expressions.at(-1) : node.callee; return callee?.type === "MemberExpression" && callee.object?.name === binding.id.name; })());
    const tail = (node) => node.type === "SequenceExpression" ? node.expressions.at(-1) : node;
    assert.deepEqual([...new Set(calls.map((call) => tail(call.callee).property.name))].sort(), [...expectedCalls].sort());
    consumers.push({ factory: selected.provenance, import: selected.witness(binding, `actual ordinary consumer ${id} imports 646908`), calls: calls.map((call) => selected.witness(call, `actual ordinary consumer calls 646908.${tail(call.callee).property.name}`)) });
  }
  await consumer(228998, "evidence/web/objects/ad258f9377db8376.js", "3417e48c11cff94d2efdafcfae6018010e97d1003122b734cd3e019f280a1134", ["a", "e", "X"]);
  const searchVariants = corpus.index.modules.filter((entry) => entry.ids.includes(379705));
  const expectedSearch = ["642cafc9d2b3c27f2d2d35ea8699a509ded856839fb3d33a8a132333d85c82d6", "629ccc425314ef1e01dd2476266052df9bcb407199598ebba7f8ce9f52adc2d6", "3c58de415e19118992ecc37931a72eaf74272cfab0b7c7dc68fd9f4f402abd4d", "350da5b767415ae168c12050d3627d71039bcc2c0a097572b5319ddbad04d8fe"];
  assert.deepEqual(searchVariants.map((entry) => entry.sha256).sort(), expectedSearch.sort(), "all four retained ordinary Search owner variants, no runtime winner invented");
  for (const variant of searchVariants) for (const origin of variant.origins) await consumer(379705, origin.source, variant.sha256, ["a"]);
  const contract = { schemaVersion: 1, classification: "Complete original application chain identity algorithms; no backend chain expansion, requests, account writes, product UI or token-detail implementation", anchors: corpus.anchors, source: factory.provenance, retainedDeclarationAstSha256: sha256(JSON.stringify(originalDeclarationAst)), exports: exports.map(([name]) => name), adapterSha256: sha256(client), witnesses, consumers, limits: ["Only the single retained 646908 factory is restored; original TS names and unseen variants are unknown.", "Whole consuming Explore/Search owners and their providers remain external; references establish actual static use, not an active runtime registration winner.", "Previously restored NEAR pattern and namespace predicate in notification-navigation/positions-by-mint are existing dependencies, not newly recovered behaviors."] };
  return { client, contract };
}
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const output = process.env.PUMP_CHAIN_IDENTITY_OUTPUT ?? dirname(fileURLToPath(import.meta.url));
  const { client, contract } = await buildChainIdentity();
  if (process.argv.includes("--write")) {
    await mkdir(output, { recursive: true });
    await writeFile(join(output, "client.mjs"), client);
    await writeFile(join(output, "contract.json"), JSON.stringify(contract, null, 2) + "\n");
  } else {
    assert.equal(await readFile(join(output, "client.mjs"), "utf8"), client);
    assert.deepEqual(JSON.parse(await readFile(join(output, "contract.json"), "utf8")), contract);
  }
  console.log(`Complete chain identity source and ${contract.consumers.length} physical ordinary consumer witnesses verified.`);
}
