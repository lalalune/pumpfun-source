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
export const DIRECTORY = "reconstruction/infobar-hidden-lists";
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
    specs = [
      [
        124884,
        "4490d02ba2117672.js",
        "dfcb487f79e63fa817cef92fd322e172c6d44fb2270bad175820a463b2e382ea",
      ],
      [
        551792,
        "11cf0bf8a734ea43.js",
        "16d67bea83a09ac1ad36eeac24f6511bb47c8c96ec543f3dae0b9ac1eb65df36",
      ],
      [
        605587,
        "2c867fef5c76d400.js",
        "bceabd6341b002dbe14334459e7470c27ca90281762d8c10db07ed3044f57ea1",
      ],
      [
        807786,
        "11cf0bf8a734ea43.js",
        "ea9e6537f895a54672e11bbcca534c78936c75d556c6ff1766fbbd99b783efda",
      ],
    ];
  const factories = [],
    indexEntries = [];
  for (const [id, file, hash] of specs) {
    const rows = corpus.index.modules.filter((r) => r.ids.includes(id));
    assert.equal(rows.length, 1, "all selected variants reviewed");
    assert.equal(rows[0].sha256, hash);
    assert.equal(rows[0].origins.length, 1);
    indexEntries.push(rows[0]);
    factories.push(
      await corpus.factory(id, { source: "evidence/web/objects/" + file }),
    );
  }
  const [ui, store, keys, defs] = factories,
    retained = [];
  const copy = (f, node, label) => {
    retained.push({
      label,
      source: f.witness(node, label),
      astSha256: astHash(node),
    });
    return f.text(node);
  };
  const canonical = copy(
    keys,
    exported(keys, 605587, "c"),
    "complete canonicalidentifier0xcase rule; no chain/account acquisition",
  );
  const helpers = ["c", "d", "u", "p", "f", "m"].map((name) =>
    copy(
      store,
      declaration(store, name),
      "complete hidden-list value helper " + name,
    ),
  );
  const definitions = [
    "feed.infoBar.hiddenTokens",
    "feed.infoBar.hiddenProfiles",
  ].map((id) =>
    exactlyOne(
      findNodes(
        defs.node,
        (node) =>
          node.type === "ObjectExpression" &&
          node.properties.some(
            (p) => p.key?.name === "id" && p.value?.value === id,
          ),
      ),
      id + " complete actual descriptor",
    ),
  );
  assert.equal(imported(defs, 551792).id.name, "l");
  assert.equal(imported(defs, 73383).id.name, "f");
  const fieldmap = declaration(ui, "en").init;
  const fields = ["info-bar-hidden-tokens", "info-bar-hidden-profiles"].map(
    (name) => objectProperty(fieldmap, name),
  );
  for (let i = 0; i < 2; i++) {
    assert.equal(objectProperty(definitions[i], "scope").value, "device");
    assert.equal(
      objectProperty(objectProperty(definitions[i], "control"), "component")
        .value,
      i ? "info-bar-hidden-profiles" : "info-bar-hidden-tokens",
    );
    assert.ok(
      member(objectProperty(definitions[i], "coerce"), "l", i ? "W" : "j"),
    );
  }
  const descriptorText = definitions.map((n, i) =>
    copy(
      defs,
      n,
      "complete actual device hidden-" +
        (i ? "profile" : "token") +
        " descriptor/coerce/localbucketsetter binding",
    ),
  );
  const chip = copy(
    ui,
    fn(ui, "L"),
    "complete accessible keyed unhide chip-list renderer",
  );
  const sorts = ["q", "$"].map((name) =>
    copy(ui, fn(ui, name), "complete newest-first UI sorter " + name),
  );
  const fieldText = fields.map((n, i) =>
    copy(
      ui,
      n,
      "complete original hidden-" +
        (i ? "profile" : "token") +
        " field renderer, local callback and empty/clear branches",
    ),
  );
  const text = await prettier.format(
    `// Complete source-adapted ordinary InfoBar hidden-list values, descriptors and fields.
export function createHiddenInfoBarValues(){const canonical=${canonical},i={c:canonical};let ${helpers.join(",")};return {tokenKey:canonical,profileKey:c,coerceTokens:f,coerceProfiles:m};}
export function createHiddenInfoBarDefinitions({values,store,makeBucketAdapter}){const l={j:values.coerceTokens,W:values.coerceProfiles,L:store},f={f:makeBucketAdapter};return [${descriptorText.join(",")}];}
export function createHiddenInfoBarFields({jsx,jsxs,useMemoCache,useTranslation,translateKey,useSetting,readSetting,Row,Action,CloseIcon,formatProfileLabel,truncateAddress,normalizeDisplayText,values}){const t={jsx,jsxs},i={c:useMemoCache},l={f:useTranslation},K={f:translateKey},W={l:useSetting,o:readSetting},T={s:Row,O:Action},r={x6:CloseIcon},M={f:formatProfileLabel},B={d:truncateAddress},_={T:normalizeDisplayText},R={M:values.profileKey},E={c:values.tokenKey};${chip}${sorts.join(";")};const HiddenTokens=${fieldText[0]},HiddenProfiles=${fieldText[1]};return {HiddenTokens,HiddenProfiles};}`,
    { parser: "babel" },
  );
  const generated = parse(text, { sourceType: "module" });
  const wrappers = findNodes(
    generated,
    (node) =>
      node.type === "FunctionDeclaration" &&
      [
        "createHiddenInfoBarValues",
        "createHiddenInfoBarDefinitions",
        "createHiddenInfoBarFields",
      ].includes(node.id?.name),
  );
  assert.equal(wrappers.length, 3);
  for (const region of retained)
    assert.equal(
      wrappers.flatMap((wrapper) =>
        findNodes(wrapper, (node) => astHash(node) === region.astSha256),
      ).length,
      1,
      "complete original region once inside actually used constructors",
    );
  const dispatcher = fn(ui, "ed"),
    lookup = exactlyOne(
      findNodes(
        dispatcher,
        (node) =>
          node.type === "MemberExpression" &&
          node.computed &&
          node.object?.name === "en" &&
          member(node.property, "g", "component"),
      ),
      "actual custom control renderer lookup",
    );
  const framework = await corpus.factory(547562, {
    source: "evidence/web/objects/11cf0bf8a734ea43.js",
  });
  const write = exactlyOne(
    findNodes(
      framework.node,
      (node) =>
        node.type === "CallExpression" &&
        node.callee?.type === "MemberExpression" &&
        node.callee.property.name === "write",
    ),
    "actual source framework coerce/write call",
  );
  const contract = {
    schema: 1,
    reviewBase: "094a06f18df738d41e77070c1a009e135671ac1a",
    scope:
      "Complete ordinary hidden-InfoBar token/profile list/coerce/descriptor/chip/setter display workflow with explicit synthetic local capabilities; no account/preference acquisition",
    selectedIndexEntries: indexEntries,
    factories: factories.map((f) => f.provenance),
    retained,
    witnesses: [
      defs.witness(
        imported(defs, 73383),
        "actual73383 localbucketadapter import; implementation external",
      ),
      ui.witness(
        lookup,
        "actual custom field dispatcher selects full en[control.component]",
      ),
      ui.witness(
        imported(ui, 547562),
        "actual local setting hook/setter import;1839 exactAPI creditedexternal",
      ),
      ui.witness(
        imported(ui, 551792),
        "actual local profile key normalization dependency",
      ),
      store.witness(
        declaration(store, "h"),
        "original device store context only; mode/watchlist/PnL/acquisition not copied or exposed",
      ),
      framework.witness(
        write,
        "actual framework applies definition.coerce then adapter.write;1839 implementation external",
      ),
      defs.witness(
        imported(defs, 551792),
        "actual descriptor coerce and local store import",
      ),
      ui.witness(
        imported(ui, 562322),
        "profile label formatter explicitport, not a profile lookup",
      ),
      ui.witness(
        imported(ui, 365089),
        "address truncation formatter explicitport",
      ),
      ui.witness(
        imported(ui, 187611),
        "display normalization category port; no normalization algorithm/nativeparity invented",
      ),
    ],
    module: {
      path: DIRECTORY + "/client.mjs",
      sha256: sha256(Buffer.from(text)),
    },
    capabilities: {
      settings:
        "useSetting(id) returns[value,setter]; readSetting(id) returnsvalue. Latest-functionalupdate/coerce/write framework and bucketadapter/store remain explicit1839-compatible syntheticports.",
      views:
        "Row/Action/CloseIcon and React/compiler/translation/display-formatters are supplied. No unmerged1920frames or priorhelperimplementation copied.",
      storage:
        "Descriptor targets supplied store.hiddenTokens/hiddenProfiles via setField. No628127storage persistence/hydration/acquisition/globalInfoBar/PnL/watchlist state exposed.",
    },
    credit:
      "1839localframework,1872fielddispatcher,1920frames,675/683metadata and prior InfoBar UI/shortcut work creditedexternal. No copied/unmergedruntimeimports or retally.",
    limits: [
      "Token coerce preserves mint text and case except canonical0xkey; profilekey trimsaddress then applies0xcase. FinitehiddenAt fallback0 and newest200before canonical-key collapse are preserved, not strict schemas or account validation.",
      "Token empty description also depends on whether local hiddenProfiles is empty, and profile labels still pass username||null to externalformatter. These original display quirks remain.",
      "Unhide requests pass a function to the supplied latest-value setter; clear passes an emptyobject. This tests local callback semantics with synthetic values, not real preference mutation or private state/persistence.",
      "Display label normalization/truncation/profileformatter, entire setting framework and storageadapter remain explicitcapabilities; compatiblefunction signatures are source-bound, unknown underlyingprovider behavior not inferred.",
      "No actualcookies/storage/sessions/credentials/profileuser oraccountdata/tenantservice requests, dustfloor/positions/financial/trading/wallet/admin controls, full Settings/InfoBar mount, native/API/CSS/pixel/security/completion claim.",
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
    "Verified complete ordinary InfoBar hidden-list fields/value/coerce/descriptor/local-callback flow",
  );
}
