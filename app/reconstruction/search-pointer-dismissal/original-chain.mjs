import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import {
  exactlyOne,
  findNodes,
  openCorpus,
  walk,
} from "../../scripts/original-contracts/source.mjs";

const corpus = await openCorpus(
  fileURLToPath(new URL("../../", import.meta.url)),
);
const specs = [
  [
    238128,
    "ccb10fa3de5597c4",
    "9e5affafd605f47d6c9466659c4bc0a654fae027f4beff481337a1cdf1263828",
  ],
  [
    167958,
    "337439e6bd8e9380",
    "8e3ad9678ffe969d7b3495045fdff943074fce05c79e8560241bb631ef0a2954",
  ],
  [
    439587,
    "0f4bad575370faed",
    "556a5e98fc389f458883751f5ed829f9493c87444c6f5053b676b34a39f05fa9",
  ],
  [
    524684,
    "0f4bad575370faed",
    "4a95dd69ab776beb22fce660c865256c7cc7ddc091c08d949c92213f537a1f1d",
  ],
  [
    385676,
    "eee6e838a0365a32",
    "d18763456faf1ae85d0d574aba879b0fe2f8515be76364d8d9687c11ff60ec6d",
  ],
  [
    617614,
    "4da7a3f4580c8707",
    "aa91929315118bd84634d7861362b94a7e77a2d0bc89b6ad89c82ce6c201be2b",
  ],
];
const factories = [];
for (const [id, object, expected] of specs) {
  const factory = await corpus.factory(id, {
    source: `evidence/web/objects/${object}.js`,
  });
  assert.equal(factory.provenance.sha256, expected);
  factories.push(factory);
}
const [search, modal, responsive, drawer, dismiss, store] = factories;
const pick = (factory, predicate, label, within = factory.node) =>
  exactlyOne(findNodes(within, predicate), label);
const record = (factory, node, label, text = true) => ({
  witness: factory.witness(node, label),
  ...(text ? { text: factory.text(node) } : {}),
});
function exportsCall(factory, id, method = "s") {
  return pick(
    factory,
    (node) =>
      node.type === "CallExpression" &&
      node.callee.object?.name === factory.runtime &&
      node.callee.property?.name === method &&
      (node.arguments[1]?.value === id ||
        (id === factory.id && node.arguments.length === 1)),
    `actual ${method} export call for ${id}`,
  );
}
function exported(factory, id, name) {
  const elements = exportsCall(factory, id).arguments[0].elements;
  const index = elements.findIndex(
    (node) => node?.type === "StringLiteral" && node.value === name,
  );
  assert.notEqual(index, -1);
  assert.equal(elements[index + 1].value, 0);
  return elements[index + 2];
}
function imported(factory, binding, id) {
  const declarations = factory.node.body.body
    .filter((node) => node.type === "VariableDeclaration")
    .flatMap((node) => node.declarations);
  return exactlyOne(
    declarations.filter(
      (node) =>
        node.id.name === binding &&
        node.init?.type === "CallExpression" &&
        node.init.callee.object?.name === factory.runtime &&
        node.init.callee.property?.name === "i" &&
        node.init.arguments[0]?.value === id,
    ),
    `actual ${binding} import ${id}`,
  );
}

const runtime = await corpus.javascript(
  "evidence/web/objects/f25d7686d048ae16.js",
);
assert.equal(
  runtime.record.sha256,
  "b5f9b5199b99ab6c141f4540f0b7d0fe803c4ecf6956849ecb6e59d3d439272e",
);
const runtimeS = exactlyOne(
  findNodes(
    runtime.ast,
    (node) =>
      node.type === "AssignmentExpression" &&
      node.left.object?.name === "u" &&
      node.left.property?.name === "S",
  ),
  "uppercase grouped export runtime",
);
const runtimeM = exactlyOne(
  findNodes(
    runtime.ast,
    (node) => node.type === "FunctionDeclaration" && node.id.name === "m",
  ),
  "grouped getter mapping",
);
const runtimeD = exactlyOne(
  findNodes(
    runtime.ast,
    (node) => node.type === "FunctionDeclaration" && node.id.name === "d",
  ),
  "export module selector",
);
const runtimeModules = ["f", "p", "F", "w", "h"].map((name) =>
  exactlyOne(
    findNodes(
      runtime.ast,
      (node) =>
        node.type ===
          (name === "F" ? "VariableDeclarator" : "FunctionDeclaration") &&
        node.id.name === name,
    ),
    `actual module-cache/import helper ${name}`,
  ),
);
const cacheBinding = exactlyOne(
  findNodes(
    runtime.ast,
    (node) =>
      node.type === "AssignmentExpression" &&
      node.left.object?.name === "u" &&
      node.left.property?.name === "c",
  ),
  "actual shared module cache",
);
assert.equal(cacheBinding.right.name, "D");
const importBinding = exactlyOne(
  findNodes(
    runtime.ast,
    (node) =>
      node.type === "AssignmentExpression" &&
      node.left.object?.name === "u" &&
      node.left.property?.name === "i",
  ),
  "actual namespace import method",
);
assert.equal(importBinding.right.name, "w");
const runtimeRecord = (node, label) => ({
  witness: runtime.witness(node, label),
  text: runtime.text.slice(node.start, node.end),
});

const grouped = exportsCall(responsive, 396623, "S");
const elements = grouped.arguments[0].elements;
assert.equal(elements[9].name, "f");
assert.equal(elements[10].value, "Root,DrawerRoot");
assert.equal(elements[11].value, 0);
const namespaceImport = imported(responsive, "f", 524684);
const rootImport = imported(responsive, "h", 396623);
assert.ok(
  namespaceImport.start < grouped.start && grouped.end < rootImport.start,
);
const drawerRoot = exported(drawer, 524684, "DrawerRoot");
const baseRoot = exported(drawer, 660315, "Root");
const baseImport = imported(drawer, "Z", 660315);
assert.ok(exportsCall(drawer, 660315).end < baseImport.start);
const predicate = pick(
  drawer,
  (node) => node.type === "ObjectMethod" && node.key.name === "outsidePress",
  "actual used backdrop admission",
  baseRoot,
);
const stateClose = pick(
  drawer,
  (node) => node.type === "ClassProperty" && node.key.name === "setOpen",
  "actual store open-change callback bridge",
);
const close = pick(
  dismiss,
  (node) =>
    node.type === "CallExpression" &&
    node.callee.property?.name === "setOpen" &&
    dismiss.text(node).includes("outsidePress"),
  "actual outside close state call",
);
let outside;
walk(dismiss.node, (node, parents) => {
  if (node === close)
    outside = parents.findLast(
      (parent) => parent.type === "FunctionDeclaration",
    );
});
assert.equal(outside?.id.name, "m");
const component = pick(
  search,
  (node) => node.type === "FunctionDeclaration" && node.id.name === "tg",
  "actual SearchDialog component",
);
const change = pick(
  search,
  (node) => node.type === "VariableDeclarator" && node.id.name === "es",
  "actual onOpenChange callback",
  component,
);
const reset = pick(
  search,
  (node) => node.type === "VariableDeclarator" && node.id.name === "ea",
  "actual original close/reset callback",
  component,
);
const rootProperty = pick(
  search,
  (node) => node.type === "ObjectProperty" && node.key.name === "onOpenChange",
  "actual SearchDialog Root caller",
  component,
);

const result = {
  method:
    "Authenticated captured AST and actual export/import/value bindings only; no capture execution",
  factories: factories.map((factory) => factory.provenance),
  runtime: [
    runtimeRecord(runtimeS, "uppercase S names/aliases/module decoder"),
    runtimeRecord(
      runtimeM,
      "getter maps export name to original namespace property",
    ),
    runtimeRecord(runtimeD, "non-null module ID selects the grouped module"),
    ...runtimeModules.map((node) =>
      runtimeRecord(node, `actual module-cache/import helper ${node.id.name}`),
    ),
    runtimeRecord(
      cacheBinding,
      "export registration and namespace imports use the same cache",
    ),
    runtimeRecord(importBinding, "actual i method resolves through w and F"),
  ],
  groupedRoot: {
    logicalModuleId: 396623,
    physicalFactoryId: 439587,
    exportName: "Root",
    namespaceProperty: "DrawerRoot",
    namespaceFactoryId: 524684,
    statements: [
      record(responsive, namespaceImport, "actual DrawerRoot namespace"),
      record(responsive, grouped, "actual uppercase grouped Root export"),
      record(
        responsive,
        rootImport,
        "actual grouped Root import after registration",
      ),
    ],
  },
  responsive: [
    record(
      modal,
      exported(modal, 167958, "N"),
      "used modal wrapper forwards open callback",
    ),
    record(
      responsive,
      exported(responsive, 439587, "v"),
      "actual responsive Root caller",
    ),
    record(
      responsive,
      exported(responsive, 439587, "s"),
      "actual content/backdrop caller",
    ),
    record(
      responsive,
      pick(
        responsive,
        (node) => node.type === "FunctionDeclaration" && node.id.name === "ey",
        "actual backdrop component",
      ),
      "actual Backdrop rendering",
    ),
  ],
  drawer: [
    record(
      drawer,
      drawerRoot,
      "DrawerRoot defaults pointer dismissal false and passes it through",
    ),
    record(drawer, baseImport, "actual grouped base-Root import"),
    record(
      drawer,
      baseRoot,
      "actual base Root, callback store and interaction use",
    ),
    record(
      drawer,
      imported(drawer, "I", 385676),
      "actual outside handler dependency",
    ),
    record(
      drawer,
      predicate,
      "topmost primary/single-touch backdrop predicate",
    ),
    record(
      drawer,
      stateClose,
      "store forwards false to the actual onOpenChange callback",
    ),
  ],
  outsideClose: [
    record(
      dismiss,
      outside,
      "actual outside handler consumes predicate then closes",
    ),
    record(dismiss, close, "actual false outsidePress state call"),
  ],
  searchClose: [
    record(search, imported(search, "ew", 167958), "actual modal import"),
    record(search, rootProperty, "actual modal onOpenChange callback"),
    record(search, change, "false open change calls actual close callback"),
    record(
      search,
      reset,
      "original close clears draft/tab and sets open false",
    ),
    record(
      search,
      imported(search, "e8", 617614),
      "actual search state getter/setter import",
    ),
    record(store, store.node, "actual search-open store and boolean setter"),
  ],
  limits: [
    "Grouped logical IDs are not additional literal factories or new captured bytes.",
    "Static outside-close attribution, not original runtime or pixel parity.",
    "The native local adaptation preserves maintained draft/Escape semantics; original ea draft/tab reset equivalence is excluded.",
  ],
};
const target = new URL("original-chain.json", import.meta.url);
if (process.argv.includes("--write"))
  await writeFile(target, JSON.stringify(result, null, 2) + "\n");
else {
  assert.deepEqual(result, JSON.parse(await readFile(target, "utf8")));
  console.log(
    "PASS: captured grouped export, actual Root/predicate/close consumer and Search setter chain",
  );
}
