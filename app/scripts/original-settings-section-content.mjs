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
export const DIRECTORY = "reconstruction/settings-section-content";
const specs = [
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
    rows = corpus.index.modules.filter((r) => r.ids.includes(124884));
  assert.equal(rows.length, 1);
  assert.equal(rows[0].origins.length, 1);
  assert.equal(rows[0].sha256, specs[0][2]);
  const f = await corpus.factory(124884, {
      source: "evidence/web/objects/4490d02ba2117672.js",
    }),
    retained = [];
  const copy = (node, label) => {
    retained.push({
      label,
      source: f.witness(node, label),
      astSha256: astHash(node),
    });
    return f.text(node);
  };
  const ids = copy(
      declaration(f, "ez"),
      "complete original first-group ID set; inert grouping metadata only",
    ),
    groups = copy(
      declaration(f, "eD"),
      "complete original section grouping metadata/match predicates; no controls acquired",
    );
  const fallback = copy(
      fn(f, "eM"),
      "complete original fallback-all group predicate",
    ),
    forward = copy(
      fn(f, "eL"),
      "complete actual account metadata→readonly field forwarder",
    ),
    content = copy(
      fn(f, "eF"),
      "complete original section-content renderer/filter/group/key/empty/special-port branches",
    );
  const text = await prettier.format(
    `// Complete source-adapted original Settings section-content grouping/display owner.
export function createSettingsSectionContent({jsx,jsxs,useMemoCache,useTranslation,translateKey,useHiddenSettingIds,definitionsForSection,Section,Field,AccountHeader,NotificationSettingsSections,PrivacyFooter}){const t={jsx,jsxs},i={c:useMemoCache},l={f:useTranslation},K={f:translateKey},ep={n:definitionsForSection},T={X:Section},ed=Field,eT=AccountHeader,ej={NotificationSettingsSections},eW=PrivacyFooter,eh=useHiddenSettingIds;let ${ids},${groups};${fallback}${forward}${content}return eF;}`,
    { parser: "babel" },
  );
  const generated = parse(text, { sourceType: "module" }),
    wrapper = exactlyOne(
      findNodes(
        generated,
        (n) =>
          n.type === "FunctionDeclaration" &&
          n.id?.name === "createSettingsSectionContent",
      ),
      "used exported constructor",
    );
  for (const region of retained)
    assert.equal(
      findNodes(wrapper, (n) => astHash(n) === region.astSha256).length,
      1,
      "full original region exactly once in used constructor",
    );
  const modal = exported(f, 124884, "SettingsModal");
  const caller = exactlyOne(
    findNodes(
      modal,
      (n) =>
        n.type === "CallExpression" &&
        member(target(n.callee), "t", "jsx") &&
        n.arguments[0]?.name === "eF",
    ),
    "actual complete source section caller",
  );
  assert.equal(objectProperty(caller.arguments[1], "section").name, "eo");
  assert.equal(objectProperty(caller.arguments[1], "onRequestClose").name, "G");
  const callerBranch = exactlyOne(
    findNodes(
      modal,
      (n) =>
        n.type === "ConditionalExpression" &&
        n.test?.name === "ex" &&
        findNodes(n.alternate, (c) => c === caller).length === 1,
    ),
    "actual blank-query branch containing section owner",
  );
  const defs = exactlyOne(
    findNodes(
      fn(f, "eF"),
      (n) => n.type === "CallExpression" && member(target(n.callee), "ep", "n"),
    ),
    "actual section definition reader",
  );
  assert.equal(defs.arguments[0].name, "x");
  const keyed = exactlyOne(
    findNodes(
      callerBranch,
      (node) =>
        node.type === "CallExpression" &&
        member(target(node.callee), "t", "jsx") &&
        node.arguments[0]?.value === "div" &&
        node.arguments[2]?.name === "eo" &&
        findNodes(node, (child) => child === caller).length === 1,
    ),
    "actual section-keyed parent wrapper",
  );
  const contract = {
    schema: 1,
    reviewBase: "094a06f18df738d41e77070c1a009e135671ac1a",
    scope:
      "Complete ordinary Settings section-content grouping/display renderer with exactreadonly branch ports; no preference/protected/provider/cookie acquisition",
    indexEntry: rows[0],
    factory: f.provenance,
    retained,
    witnesses: [
      f.witness(
        keyed,
        "actual section-keyed caller wrapper; parentkey retained by finite host, fullprovider external",
      ),
      f.witness(
        caller,
        "actual1911-compatible section/onRequestClose caller shape",
      ),
      f.witness(
        callerBranch,
        "actual blank-query section branch; fulloutermodal external",
      ),
      f.witness(defs, "actual module-lifetime definitionsForSection reader"),
      f.witness(imported(f, 272700), "actual registry/section-reader import"),
      f.witness(
        declaration(f, "eh"),
        "actual hidden-ID provider context only; implementation not acquired",
      ),
      f.witness(
        fn(f, "ed"),
        "actual field output target;1872 dispatcher external",
      ),
      f.witness(
        imported(f, 379288),
        "actual Section frame import;1920implementation external",
      ),
      f.witness(
        fn(f, "eW"),
        "actual privacy footer target/context only; cookies/action not copied or invoked",
      ),
      f.witness(
        fn(f, "eT"),
        "actual account header target/context only; protected/acquisition behavior external",
      ),
    ],
    module: {
      path: DIRECTORY + "/client.mjs",
      sha256: sha256(Buffer.from(text)),
    },
    capabilities: {
      metadata:
        "Supplied module-lifetime definitionsForSection and hidden-ID Set hook. Original memo dependencies preserved, no subscriptions/dynamic registry policy added.",
      display:
        "Supplied React/compiler/translation/Section/Field ports. Trade/chart prefix literals are inert grouping metadata only; no controls/prices/values acquired.",
      special:
        "AccountHeader,NotificationSettingsSections andPrivacyFooter are explicitreadonly renderer ports with originalprops. They do not implement account/Hermes/permission/cookie/provider or request acquisition.",
    },
    credit:
      "1911already recovers the actual resource/content caller;1898results,1872fielddispatcher,1920frames,1839state and675/683metadata remainexternalcreditedports, withoutcopy/unmergedruntimeimport/retally.",
    limits: [
      "Groups take first matching IDs in originalregistry order, then leftovergroup; emptygroupsremoved, originalrun-index/labelkeyandfieldkeys retained. Inerttrade/chartmetadata is not an implemented financialcontrol.",
      "Unknown/empty ordinarysection stillreturns originalemptycontainer, notnewstatusmessage. PrivacyFooter occurs onlyonlast nonemptygroup; accountheader andnotification earlyreturn retainexactbranches via readonlyports.",
      "Memo observes hiddenSet/close/section/translation identities, not arbitrarymutation of suppliedregistry orSet; no staleness/refresh policy is invented.",
      "Onlysyntheticreadonly metadata/rendererports in tests. Noactualcookies/storage/sessions/credentials/user/accountdata/preferencesmutation/trading/wallet/admin/protectedacquisition, fullSettings/provider/CSS/native/API/pixel/security/completionclaim.",
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
    "Verified full original Settings section-content display/filter/group owner; readonlyexternalports preserved",
  );
}
