import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  propertyName,
  objectProperty,
  literal,
} from "./original-contracts/source.mjs";
const ROOT = fileURLToPath(new URL("..", import.meta.url));
export const OUTPUT = "reconstruction/create-utf8/contract.json";
export async function recover(root = ROOT) {
  const c = await openCorpus(root);
  const page = await c.factory(734638, {
    source: "evidence/web/objects/89ce7de3b9bad421.js",
  });
  const helper = await c.factory(807757, {
    source: "evidence/web/objects/6a1606765ef3e83e.js",
  });
  const limits = await c.factory(586090, {
    source: "evidence/web/objects/6a1606765ef3e83e.js",
  });
  assert.equal(
    page.provenance.sha256,
    "616b013f89f1cf3e446817865c602c16b9eb6f07e09fa05145c0191ce60f63bc",
  );
  assert.equal(
    helper.provenance.sha256,
    "7094dc3c2113698f06bc9cef420cd9c153d355911226020d467f49a0ad85bf68",
  );
  assert.equal(
    limits.provenance.sha256,
    "5ddcdce058dfb79522bc03a2ba9bf7d9cae7eccccaad65d80ea43b368f114fc4",
  );
  const html = await c.capture("evidence/web/objects/5e15667ed36cac85");
  for (const f of [page, helper, limits])
    assert.ok(html.text.includes(new URL(f.provenance.url).pathname));
  const exports = exactlyOne(
    findNodes(
      helper.node,
      (n) =>
        n.type === "CallExpression" &&
        n.callee?.object?.name === helper.runtime &&
        propertyName(n.callee.property) === "s",
    ),
    "helper exports",
  ).arguments[0].elements;
  const W = exports[exports.findIndex((n) => n?.value === "W") + 2];
  assert.equal(W.type, "ArrowFunctionExpression");
  assert.equal(helper.text(W), "e=>new Blob([e]).size");
  const imported = exactlyOne(
    page.node.body.body
      .flatMap((n) => n.declarations ?? [])
      .filter((n) => n.id?.name === "eY"),
    "actual eY import",
  );
  assert.equal(page.text(imported), "eY=e.i(807757)");
  const validator = exactlyOne(
    findNodes(
      page.node,
      (n) => n.type === "VariableDeclarator" && n.id?.name === "tn",
    ),
    "used Create validator",
  );
  const body = validator.init.body.body;
  const guards = [
    ["name", "t", "NAME_MAX_LENGTH", 32],
    ["ticker", "r", "TICKER_MAX_LENGTH", 10],
  ].map(([field, arg, constant, cap]) => {
    const guard = exactlyOne(
      body.filter(
        (n) =>
          n.type === "IfStatement" &&
          n.test.type === "BinaryExpression" &&
          n.test.operator === ">" &&
          n.test.left.type === "CallExpression" &&
          n.test.left.arguments[0]?.name === arg,
      ),
      `${field} byte guard`,
    );
    assert.equal(page.text(guard.test.left.callee), "0,eY.W");
    assert.equal(page.text(guard.test.right), `eX.f.${constant}`);
    return { field, cap, node: guard };
  });
  const le = exactlyOne(
    findNodes(
      limits.node,
      (n) =>
        n.type === "CallExpression" &&
        n.callee?.object?.name === limits.runtime &&
        propertyName(n.callee.property) === "s",
    ),
    "limits exports",
  ).arguments[0].elements;
  const fields = le[le.findIndex((n) => n?.value === "f") + 2];
  for (const g of guards)
    assert.equal(
      literal(
        objectProperty(
          fields,
          g.field === "name" ? "NAME_MAX_LENGTH" : "TICKER_MAX_LENGTH",
        ),
      ),
      g.cap,
    );
  const calls = findNodes(
    page.node,
    (n) => n.type === "CallExpression" && n.callee?.name === "tn",
  );
  assert.equal(calls.length, 2);
  for (const call of calls) {
    assert.equal(page.text(objectProperty(call.arguments[0], "name")), "e_");
    assert.equal(page.text(objectProperty(call.arguments[0], "ticker")), "ey");
  }
  const inputs = ["name", "ticker"].map((id) =>
    exactlyOne(
      findNodes(
        page.node,
        (n) =>
          n.type === "CallExpression" &&
          n.arguments[0]?.value === "input" &&
          n.arguments[1]?.type === "ObjectExpression" &&
          n.arguments[1].properties.some(
            (p) => propertyName(p.key) === "id" && p.value?.value === id,
          ),
      ),
      `${id} input`,
    ),
  );
  assert.ok(
    page
      .text(objectProperty(inputs[0].arguments[1], "onChange"))
      .includes("e.target.value.length<=32"),
  );
  assert.ok(
    page
      .text(objectProperty(inputs[1].arguments[1], "onChange"))
      .includes("e.target.value.length<=10"),
  );
  const description = exactlyOne(
    body.filter(
      (n) =>
        n.type === "IfStatement" &&
        page.text(n.test) === "a&&a.length>eX.f.DESCRIPTION_MAX_LENGTH",
    ),
    "description remains codeunits",
  );
  const w = (f, n, label) => ({ ...f.witness(n, label), code: f.text(n) });
  return {
    authority:
      "Static original Create client validation, not SDK/on-chain/server capacity. Captured code is never executed.",
    anchors: c.anchors,
    createHtml: { path: html.record.path, sha256: html.record.sha256 },
    factories: [page, helper, limits].map((f) => f.provenance),
    observed: {
      nameUtf8Bytes: 32,
      tickerUtf8Bytes: 10,
      descriptionCodeUnits: 2000,
      originalNativeInputCodeUnitCaps: [32, 10],
      actualValidatorConsumers: calls.length,
    },
    witnesses: [
      w(page, imported, "actual helper import"),
      w(helper, W, "actual native UTF8 byte measurement"),
      ...guards.map((g) => w(page, g.node, `${g.field} used byte guard`)),
      w(page, description, "description remains codeunits"),
      ...calls.map((n, i) => w(page, n, `actual consumer ${i + 1}`)),
      ...inputs.map((n, i) =>
        w(page, n, `native input ${i + 1} codeunit admission`),
      ),
    ],
    localDecisions: [
      "Use the actual Blob byte semantics in validation and local counter.",
      "Preserve native maxlengths, description count, whitespace-only rejection and existing URL policy.",
      "No Unicode normalization or additional character restrictions.",
      "Separate SDK unpaired-surrogate rejection in PR1259 remains independent; no SDK/upload/signing/mutation changes.",
    ],
  };
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const text = `${JSON.stringify(await recover(), null, 2)}\n`,
    out = path.join(ROOT, OUTPUT);
  if (process.argv.includes("--check"))
    assert.equal(await readFile(out, "utf8"), text);
  else {
    await mkdir(path.dirname(out), { recursive: true });
    await writeFile(out, text);
  }
  console.log("Create UTF8 captured validation contract: PASS");
}
