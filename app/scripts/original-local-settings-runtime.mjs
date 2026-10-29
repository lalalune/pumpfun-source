// Authenticate original source as data; never evaluate a captured factory.
import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "@babel/parser";
import prettier from "prettier";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  member,
  objectProperty,
  propertyName,
  sha256,
} from "./original-contracts/source.mjs";

export const APP = fileURLToPath(new URL("..", import.meta.url));
export const DIRECTORY = "reconstruction/local-settings-runtime";
const specs = [
  [
    547562,
    "11cf0bf8a734ea43.js",
    "b2126ccdeda94a6a3aa697a68d8734231a76a6dccd14ee40be90143aa4281d30",
  ],
  [
    671027,
    "11cf0bf8a734ea43.js",
    "b7f01190e0bf72df3763afbfe71b7a146edf4c9d1895b4eedb3e8f1a81e758a9",
  ],
  [
    654506,
    "11cf0bf8a734ea43.js",
    "faac91fe220707cbde9c6287b6c7e2493b5e5f9bbe93e2a6079cc45a8ab0543d",
  ],
  [
    807786,
    "11cf0bf8a734ea43.js",
    "ea9e6537f895a54672e11bbcca534c78936c75d556c6ff1766fbbd99b783efda",
  ],
  [
    272700,
    "11cf0bf8a734ea43.js",
    "854b2b23846f367dbc1e84904d2954eaac355ef8c5412b32cd7cef39e7340110",
  ],
  [
    416380,
    "8401a8e00b4638cb.js",
    "88517177e9727701eed5312e3590ae11106a1c4888579501ea1413d4484f1479",
  ],
  [
    124884,
    "4490d02ba2117672.js",
    "dfcb487f79e63fa817cef92fd322e172c6d44fb2270bad175820a463b2e382ea",
  ],
];
const target = (node) =>
  node?.type === "SequenceExpression" ? node.expressions.at(-1) : node;
function exported(factory, id, name) {
  const found = [];
  for (const node of findNodes(
    factory.node,
    (node) =>
      node.type === "CallExpression" &&
      member(node.callee, factory.runtime, "s"),
  )) {
    if (
      node.arguments[1]
        ? node.arguments[1].value !== id
        : factory.ids.length !== 1 || factory.id !== id
    )
      continue;
    const values = node.arguments[0].elements;
    for (let index = 0; index < values.length; index += 3)
      if (values[index].value === name) found.push(values[index + 2]);
  }
  return exactlyOne(found, `actual export ${id}.${name}`);
}
const imported = (factory, id) =>
  exactlyOne(
    findNodes(
      factory.node,
      (node) =>
        node.type === "VariableDeclarator" &&
        node.init?.type === "CallExpression" &&
        member(node.init.callee, factory.runtime, "i") &&
        node.init.arguments[0]?.value === id,
    ),
    `actual import ${id}`,
  );
const top = (factory) =>
  factory.node.body.body.filter(
    (node) =>
      node.type === "FunctionDeclaration" ||
      (node.type === "VariableDeclaration" &&
        !node.declarations.every(
          (entry) =>
            entry.init?.type === "CallExpression" &&
            member(entry.init.callee, factory.runtime, "i"),
        )),
  );
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(
    Object.entries(value)
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
      .map(([key, entry]) => [key, canonical(entry)]),
  );
}
const astHash = (node) => sha256(Buffer.from(JSON.stringify(canonical(node))));

export async function recover(root = APP) {
  const corpus = await openCorpus(root),
    modules = new Map(),
    entries = [];
  for (const [id, basename, hash] of specs) {
    const rows = corpus.index.modules.filter((entry) => entry.ids.includes(id));
    assert.equal(rows.length, 1, `review all variants of ${id}`);
    assert.equal(rows[0].sha256, hash);
    assert.equal(rows[0].origins.length, 1, `review all origins of ${id}`);
    const module = await corpus.factory(id, {
      source: "evidence/web/objects/" + basename,
    });
    assert.equal(module.provenance.sha256, hash);
    modules.set(id, module);
    entries.push(rows[0]);
  }
  const hook = modules.get(547562),
    legacy = modules.get(671027),
    storage = modules.get(654506);
  const definitions = modules.get(807786),
    registry = modules.get(272700);
  const renderer = modules.get(416380),
    dispatcher = modules.get(124884);
  for (const id of [671027, 272700]) imported(hook, id);
  imported(renderer, 547562);
  imported(definitions, 654506);
  imported(registry, 807786);
  const definition = exactlyOne(
    findNodes(
      definitions.node,
      (node) =>
        node.type === "ObjectProperty" &&
        propertyName(node.key) === "feed.showAnimations",
    ),
    "safe actual descriptor",
  );
  const object = definition.value.arguments[0];
  assert.equal(objectProperty(object, "scope").value, "device");
  assert.equal(objectProperty(object, "default").type, "UnaryExpression");
  assert.equal(definitions.text(objectProperty(object, "coerce")), "e=>!1!==e");
  const adapter = objectProperty(object, "adapter");
  assert.equal(propertyName(target(adapter.callee).property), "f");
  assert.equal(
    objectProperty(adapter.arguments[0], "key").value,
    "home.show-animations",
  );
  assert.equal(objectProperty(adapter.arguments[0], "codec").value, "json");
  const control = objectProperty(object, "control");
  assert.equal(objectProperty(control, "kind").value, "switch");
  assert.ok(
    !object.properties.some((node) =>
      ["legacy", "firstPaintSensitive"].includes(propertyName(node.key)),
    ),
  );
  const switchImport = imported(dispatcher, 416380);
  const renderCall = exactlyOne(
    findNodes(
      dispatcher.node,
      (node) =>
        node.type === "CallExpression" &&
        member(target(node.callee), "t", "jsx") &&
        member(node.arguments[0], switchImport.id.name, "f"),
    ),
    "actual switch dispatcher call",
  );
  assert.equal(objectProperty(renderCall.arguments[1], "definition").name, "x");
  const branch = exactlyOne(
    findNodes(
      dispatcher.node,
      (node) =>
        node.type === "IfStatement" &&
        node.test.type === "BinaryExpression" &&
        node.test.left.value === "switch" &&
        member(node.test.right, "g", "kind") &&
        findNodes(node.consequent, (child) => child === renderCall).length ===
          1,
    ),
    "actual switch dispatch branch",
  );
  const registrySpread = exactlyOne(
    findNodes(
      registry.node,
      (node) =>
        node.type === "SpreadElement" && member(node.argument, "s", "f"),
    ),
    "actual feed registry spread",
  );

  const kept = [];
  function copy(module, node, label) {
    kept.push({
      label,
      source: module.witness(node, label),
      astSha256: astHash(node),
    });
    return module.text(node);
  }
  const storageStatements = top(storage).map((node) =>
    copy(storage, node, "complete local-key module declaration"),
  );
  const legacyStatements = top(legacy).map((node) =>
    copy(legacy, node, "complete legacy-initialization declaration"),
  );
  const hookStatements = top(hook).map((node) =>
    copy(hook, node, "complete setting-hook module declaration"),
  );
  const rendererStatements = top(renderer).map((node) =>
    copy(renderer, node, "complete switch renderer helper"),
  );
  const localKey = copy(
    storage,
    exported(storage, 654506, "f"),
    "complete local-key adapter constructor; existing privacy helper credited",
  );
  const identity = copy(
    storage,
    exported(storage, 529281, "f"),
    "actual identity descriptor constructor",
  );
  const initialize = copy(
    legacy,
    exported(legacy, 671027, "f"),
    "complete once-per-definition legacy initializer",
  );
  const pair = copy(
    hook,
    exported(hook, 547562, "l"),
    "complete setting pair hook",
  );
  const switchComponent = copy(
    renderer,
    exported(renderer, 416380, "f"),
    "complete actual Settings switch renderer",
  );
  const selected = copy(
    definitions,
    definition.value,
    "complete safe feed animation definition construction",
  );
  const text = await prettier.format(
    `// Source-adapted original logic. Explicit ports only; importing reads no browser state.
export function createLocalKeyRuntime({window,StorageEvent}){${storageStatements.join("\n")}const localKey=${localKey};return {localKey};}
export function createLegacyInitializer({window}){${legacyStatements.join("\n")}return ${initialize};}
export function createSettingsRuntime({registry,initializeLegacy,useMemoCache,useSyncExternalStore}){const t={c:useMemoCache},r={useSyncExternalStore},i={f:initializeLegacy},s={k:registry};${hookStatements.join("\n")}const useSettingPair=${pair};return {readSetting:l,writeSetting:c,useSetting:d,useSetter:u,useSettingPair};}
export function createFeedAnimationsDefinition({localKey}){const m={f:localKey},b={f:${identity}};return ${selected};}
export function createSettingsSwitch({jsx,jsxs,Fragment,useMemoCache,useState,useTranslation,translateKey,Switch,Button,confirmation,useHydrated,settings}){const t={jsx,jsxs,Fragment},n={c:useMemoCache},i={Z:Switch,K:Button},r={useState},l={f:useTranslation},a={f:translateKey},s=confirmation,o={f:useHydrated},c={o:settings.useSetting,Z:settings.useSetter};${rendererStatements.join("\n")}return ${switchComponent};}
`,
    { parser: "babel" },
  );
  const generated = parse(text, { sourceType: "module" });
  for (const entry of kept)
    assert.ok(
      findNodes(generated, (node) => astHash(node) === entry.astSha256).length >
        0,
      "complete retained AST missing: " + entry.label,
    );
  const contract = {
    schema: 1,
    reviewBase: "094a06f18df738d41e77070c1a009e135671ac1a",
    scope:
      "Original setting framework, safe actual switch/definition and local JSON lifecycle; no new settings page or Home effect",
    selectedIndexEntries: entries,
    provenance: [...modules.values()].map((module) => module.provenance),
    retained: kept,
    callerWitnesses: [
      dispatcher.witness(switchImport, "actual switch component import"),
      dispatcher.witness(
        branch,
        "actual switch-kind branch passes the definition",
      ),
      registry.witness(
        registrySpread,
        "actual registry includes feed definitions",
      ),
    ],
    module: {
      path: DIRECTORY + "/client.mjs",
      sha256: sha256(Buffer.from(text)),
    },
    capabilities: {
      browser:
        "Explicit synthetic/integration window.localStorage + addEventListener/dispatchEvent and StorageEvent constructor; no global defaults",
      framework:
        "Injected registry, same-runtime legacy initializer and actual React/compiler useMemoCache/useSyncExternalStore",
      renderer:
        "Injected JSX/React, translation, hydration, switch/button/confirmation components; private component/provider behavior is not recovered",
    },
    credit:
      "Existing privacy-external-links unit already reconstructs selected654506 key/cache/fallback semantics. This unit adds complete547562 hooks/SSR/functional updates,671027 initialization and416380 selected UI closure; no first-helper or whole-registry recovery claim.",
    limits: [
      "Only safe feed.showAnimations descriptor is constructed; no generic preferences page, fabricated Home animation effect or server persistence.",
      "Legacy tests use synthetic keys, not trading/admin/account data. No current cookies, auth/session, support/Firebase, claims, signing, mutation or live requests.",
      "The captured confirmation branch is retained, but its private provider and unrelated sensitive setting policies are not supplied or qualified.",
      "LocalBucket/locale-cookie and full registry remain separate. Scope metadata is not ownership or server authorization.",
      "No feature milestone, production availability, original-provider/API/pixel equivalence or security clearance claim.",
    ],
  };
  return { text, contract };
}

export async function verify(root = APP) {
  const result = await recover(root);
  assert.equal(
    await readFile(path.join(root, DIRECTORY, "client.mjs"), "utf8"),
    result.text,
  );
  assert.deepEqual(
    JSON.parse(
      await readFile(path.join(root, DIRECTORY, "contract.json"), "utf8"),
    ),
    result.contract,
  );
  return result.contract;
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  if (process.argv.includes("--write")) {
    const result = await recover();
    await mkdir(path.join(APP, DIRECTORY), { recursive: true });
    await writeFile(path.join(APP, DIRECTORY, "client.mjs"), result.text);
    await writeFile(
      path.join(APP, DIRECTORY, "contract.json"),
      JSON.stringify(result.contract, null, 2) + "\n",
    );
  } else await verify();
  console.log(
    "Verified complete local setting framework, legacy initializer, safe descriptor and actual switch closure; no server/provider policy claim",
  );
}
