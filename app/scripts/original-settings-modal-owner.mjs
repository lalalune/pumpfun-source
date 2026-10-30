// Captures are authenticated/parsed as data; no captured factory is evaluated.
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
  sha256,
} from "./original-contracts/source.mjs";

export const APP = fileURLToPath(new URL("..", import.meta.url));
export const DIRECTORY = "reconstruction/settings-modal-owner";
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
  return exactlyOne(found, `${id}.${name} actual export`);
}
const declaration = (factory, name) =>
  exactlyOne(
    factory.node.body.body
      .filter((node) => node.type === "VariableDeclaration")
      .flatMap((node) => node.declarations)
      .filter((node) => node.id.name === name),
    `${name} module declaration`,
  );
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
    `${id} import`,
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
      .map(([key, child]) => [key, canonical(child)]),
  );
}
const astHash = (node) => sha256(Buffer.from(JSON.stringify(canonical(node))));

const fn = (factory, name) =>
  exactlyOne(
    factory.node.body.body.filter(
      (node) => node.type === "FunctionDeclaration" && node.id.name === name,
    ),
    name + " complete function",
  );
export async function recover(root = APP) {
  const corpus = await openCorpus(root),
    entries = corpus.index.modules.filter((r) => r.ids.includes(124884));
  assert.equal(entries.length, 1);
  assert.equal(entries[0].origins.length, 1);
  assert.equal(
    entries[0].sha256,
    "dfcb487f79e63fa817cef92fd322e172c6d44fb2270bad175820a463b2e382ea",
  );
  const f = await corpus.factory(124884, {
      source: "evidence/web/objects/4490d02ba2117672.js",
    }),
    original = exported(f, 124884, "SettingsModal"),
    retained = [];
  const bindings = {};
  for (const name of ["Y", "J"])
    bindings[name] = exactlyOne(
      findNodes(
        original,
        (n) => n.type === "VariableDeclarator" && n.id.name === name,
      ),
      name + " exact top-level derived hook binding",
    );
  for (const name of ["Y", "J"]) {
    assert.equal(bindings[name].init.type, "CallExpression");
    assert.equal(bindings[name].init.callee.type, "ArrowFunctionExpression");
    assert.equal(bindings[name].init.arguments.length, 0);
  }
  const declared = original.body.body[0].declarations;
  assert.ok(declared.includes(bindings.Y) && declared.includes(bindings.J));
  assert.equal(declared.indexOf(bindings.J), declared.indexOf(bindings.Y) + 1);
  assert.equal(
    declared[declared.indexOf(bindings.Y) - 1].id.type,
    "ObjectPattern",
  );
  assert.equal(declared[declared.indexOf(bindings.J) + 1].id.name, "ee");
  const replacements = [
    { binding: "Y", port: "useVisibleSections", node: bindings.Y.init },
    { binding: "J", port: "useSettingsResourceAttempt", node: bindings.J.init },
  ];
  let adapted = f.text(original);
  for (const { node, port } of [...replacements].sort(
    (a, b) => b.node.start - a.node.start,
  ))
    adapted =
      adapted.slice(0, node.start - original.start) +
      port +
      "()" +
      adapted.slice(node.end - original.start);
  const adaptedNode = parse("(" + adapted + ")", { sourceType: "module" })
    .program.body[0].expression;
  const normalized = canonical(original);
  for (const n of findNodes(
    normalized,
    (n) => n.type === "VariableDeclarator" && ["Y", "J"].includes(n.id.name),
  ))
    n.init = {
      type: "CallExpression",
      callee: {
        type: "Identifier",
        name:
          n.id.name === "Y"
            ? "useVisibleSections"
            : "useSettingsResourceAttempt",
      },
      arguments: [],
    };
  assert.equal(
    astHash(adaptedNode),
    astHash(normalized),
    "only two original hook IIFE init nodes changed",
  );
  const copy = (node, label) => {
    retained.push({
      label,
      source: f.witness(node, label),
      astSha256: astHash(node),
    });
    return f.text(node);
  };
  const resettable = copy(
      fn(f, "eU"),
      "complete actual resettable strict-false metadata predicate",
    ),
    sectionId = copy(
      fn(f, "eH"),
      "complete actual visible-section ID projection",
    );
  const text = await prettier.format(
    `// Full original Settings display/controller owner. Exactly2documented hook-port substitutions; no provider acquisition.
export function createSettingsModalOwner({jsx,jsxs,useMemoCache,useState,useEffect,useId,useRef,useTranslation,translateKey,useVisibleSections,useSettingsResourceAttempt,useTransientSettingId,FocusContextProvider,definitionsForSection,SearchResults,SectionContent,Loading,resetSection,DialogRoot,DialogContent,TabsRoot,TabsList,TabsTrigger,Button,CloseIcon,SearchIcon,ResetIcon,DeviceIcon}){const t={jsx,jsxs},i={c:useMemoCache},n={useState,useEffect,useId,useRef},l={f:useTranslation},K={f:translateKey},a={h:useTransientSettingId,_:{Provider:FocusContextProvider}},ep={n:definitionsForSection},eb=SearchResults,eF=SectionContent,eq=Loading,V={t:resetSection},s={v:DialogRoot,s:DialogContent,i:TabsRoot,R:TabsList,V:TabsTrigger,K:Button},r={x6:CloseIcon,L3:SearchIcon,B4:ResetIcon,mD:DeviceIcon};${resettable}${sectionId}return ${adapted};}`,
    { parser: "babel" },
  );
  const wrapper = exactlyOne(
    findNodes(
      parse(text, { sourceType: "module" }),
      (n) =>
        n.type === "FunctionDeclaration" &&
        n.id?.name === "createSettingsModalOwner",
    ),
    "actualusedconstructor",
  );
  for (const r of retained)
    assert.equal(
      findNodes(wrapper, (n) => astHash(n) === r.astSha256).length,
      1,
      "full retained helper exactly once in used owner",
    );
  assert.equal(
    findNodes(wrapper, (n) => astHash(n) === astHash(adaptedNode)).length,
    1,
    "complete two-substitution owner exactly once in usedconstructor",
  );
  const expression = (property, object) =>
    exactlyOne(
      findNodes(
        original,
        (n) =>
          n.type === "CallExpression" &&
          member(target(n.callee), object, property),
      ),
      object + "." + property + " actualcall",
    );
  const contract = {
    schema: 1,
    reviewBase: "094a06f18df738d41e77070c1a009e135671ac1a",
    scope:
      "Complete original Settings display/controller owner with exactly two source-signature hook-port substitutions; no protected/provider/permission/address acquisition or preferences persistence",
    indexEntry: entries[0],
    factory: f.provenance,
    retained,
    owner: {
      source: f.witness(
        original,
        "complete original SettingsModal owner before exactly two hook init substitutions",
      ),
      originalAstSha256: astHash(original),
      adaptedAstSha256: astHash(adaptedNode),
      memoSlots: 100,
      transformations: replacements.map((r) => ({
        binding: r.binding,
        original: f.witness(
          r.node,
          "complete original " +
            r.binding +
            " IIFE; external source-signature capability",
        ),
        replacement: r.port + "()",
        callPosition:
          r.binding === "Y"
            ? "After useTranslation, before J resource hook"
            : "After Y availability, before useTransientSettingId(H)",
        scope:
          r.binding === "Y"
            ? "Protected availability/address/permission/feature acquisition remains external; supplied visible metadata only"
            : "Exact hook API returned by1911; no copied standalone core or new acquisition",
      })),
    },
    witnesses: [
      f.witness(
        expression("h", "a"),
        "actual raw useTransientSettingId(H) call;1920hook not FocusProviderwrapper",
      ),
      f.witness(
        expression("t", "V"),
        "actual resetSection(eo) call precedes confirmationclear; callbackexternal",
      ),
      f.witness(
        exactlyOne(
          findNodes(
            original,
            (n) =>
              n.type === "CallExpression" &&
              member(target(n.callee), "t", "jsx") &&
              n.arguments[0]?.type === "MemberExpression" &&
              member(n.arguments[0].object, "a", "_"),
          ),
          "actual raw FocusContext.Provider caller",
        ),
        "actual raw FocusContext.Provider value=ee signature; no doubletimer",
      ),
      f.witness(imported(f, 165228), "actual focus namespace"),
      f.witness(
        imported(f, 439587),
        "actual modal/tabs/button facade; primitivesexternal",
      ),
      f.witness(
        imported(f, 138800),
        "actual reset service import; callbackonly no reset implementation",
      ),
      f.witness(
        imported(f, 272700),
        "actual section metadata reader import; definitionsonly",
      ),
      f.witness(
        fn(f, "eb"),
        "actual1898 SearchResults(query,visibleSections) target; rendererexternal",
      ),
      f.witness(
        fn(f, "eF"),
        "actual1952 SectionContent(section,onRequestClose) target; rendererexternal",
      ),
      f.witness(fn(f, "eq"), "actual1911 Loading target; rendererexternal"),
    ],
    module: {
      path: DIRECTORY + "/client.mjs",
      sha256: sha256(Buffer.from(text)),
    },
    credit:
      "1911 useSettingsResourceAttempt/Loading APIs and verbatim content-branch body already recovered; no new count for that region.1898SearchResults,1952SectionContent,1920useTransientSettingId+FocusContext.Provider exactports,1872fielddispatcher/1839state external. No standalone recovered cores copied or unmerged imports.",
    limits: [
      "OnlyY/J IIFE initializers replaced with requiredhooks at original unconditionalcallpositions. All other100-slot memo/state/scroll/search/tabs/reset-confirm/header/footer/dialog operations remain original. Internal hook-slot layout belongs to suppliedhooks, not claimed originalprovider parity.",
      "VisibleSections is a required complete metadata-list hook; originalY provider/address/permission/feature acquisition is not implemented. Tests supply safe feed/privacy metadata and inert denied/unknown selection, not actual auth/permission.",
      "ResetSection(section) is a required callback. Synthetic successful/throwing callback tests qualify confirmationordering only; no actual preference reset/storage/cookie/provider acquired.",
      "Dialog/tabs/buttons/icons/translation/resource/results/content/focus remain explicit actualsignatureports. No originalprimitive/focus-trap/Next/provider/wholeSettings/native/API/pixel/security/completion claim.",
    ],
  };
  return { text, contract };
}
export async function verify(root = APP) {
  const r = await recover(root);
  assert.equal(
    await readFile(path.join(root, DIRECTORY, "client.mjs"), "utf8"),
    r.text,
  );
  assert.equal(
    await readFile(path.join(root, DIRECTORY, "contract.json"), "utf8"),
    JSON.stringify(r.contract, null, 2) + "\n",
  );
  return r.contract;
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  if (process.argv.includes("--write")) {
    const r = await recover();
    await mkdir(path.join(APP, DIRECTORY), { recursive: true });
    await writeFile(path.join(APP, DIRECTORY, "client.mjs"), r.text);
    await writeFile(
      path.join(APP, DIRECTORY, "contract.json"),
      JSON.stringify(r.contract, null, 2) + "\n",
    );
  } else await verify();
  console.log(
    "Verified full original Settings full display/controller owner; exactly2source-signature hook-port substitutions preserved",
  );
}
