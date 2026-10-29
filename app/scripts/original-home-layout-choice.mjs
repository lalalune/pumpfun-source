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
  propertyName,
  sha256,
} from "./original-contracts/source.mjs";

export const APP = fileURLToPath(new URL("..", import.meta.url));
export const DIRECTORY = "reconstruction/home-layout-choice";
const specs = [
  [
    124884,
    "4490d02ba2117672.js",
    "dfcb487f79e63fa817cef92fd322e172c6d44fb2270bad175820a463b2e382ea",
  ],
  [
    807786,
    "11cf0bf8a734ea43.js",
    "ea9e6537f895a54672e11bbcca534c78936c75d556c6ff1766fbbd99b783efda",
  ],
  [
    810680,
    "11cf0bf8a734ea43.js",
    "82ef329784658b379b55ffc108d36dc83138d513674b9d6c3654ca7330ff1af0",
  ],
  [
    214100,
    "11cf0bf8a734ea43.js",
    "97378a2c68301894e867783bc0dcd8475c492bfa86d4d34bb0c6d4e119d213ef",
  ],
  [
    529281,
    "11cf0bf8a734ea43.js",
    "faac91fe220707cbde9c6287b6c7e2493b5e5f9bbe93e2a6079cc45a8ab0543d",
  ],
  [
    272700,
    "11cf0bf8a734ea43.js",
    "854b2b23846f367dbc1e84904d2954eaac355ef8c5412b32cd7cef39e7340110",
  ],
];
const target = (node) =>
  node?.type === "SequenceExpression" ? node.expressions.at(-1) : node;
const declarations = (factory) =>
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
    modules = new Map(),
    entries = [];
  for (const [id, basename, hash] of specs) {
    const rows = corpus.index.modules.filter((entry) => entry.ids.includes(id));
    assert.equal(rows.length, 1, "review all variants " + id);
    assert.equal(rows[0].sha256, hash);
    assert.equal(rows[0].origins.length, 1);
    const factory = await corpus.factory(id, {
      source: "evidence/web/objects/" + basename,
    });
    assert.equal(factory.provenance.sha256, hash);
    modules.set(id, factory);
    entries.push(rows[0]);
  }
  const ui = modules.get(124884),
    definitions = modules.get(807786),
    cookie = modules.get(810680),
    adapter = modules.get(214100),
    identity = modules.get(529281),
    registry = modules.get(272700);
  const layoutImport = imported(definitions, 810680),
    adapterImport = imported(definitions, 214100),
    frameworkImport = imported(ui, 547562);
  const definition = exactlyOne(
    findNodes(
      definitions.node,
      (node) =>
        node.type === "ObjectProperty" &&
        propertyName(node.key) === "feed.homeLayout",
    ),
    "actual safe home layout definition",
  );
  assert.equal(
    objectProperty(
      objectProperty(definition.value.arguments[0], "control"),
      "kind",
    ).value,
    "pills",
  );
  const previewEntries = declaration(ui, "j").init.properties.filter((node) =>
    ["layout-grid", "layout-table"].includes(propertyName(node.key)),
  );
  assert.deepEqual(
    previewEntries.map((node) => propertyName(node.key)),
    ["layout-grid", "layout-table"],
  );
  const registrySpread = exactlyOne(
    findNodes(
      registry.node,
      (node) =>
        node.type === "SpreadElement" && member(node.argument, "s", "f"),
    ),
    "actual feed registry spread",
  );
  const retained = [];
  const copy = (factory, node, label, wrapper) => {
    retained.push({
      label,
      wrapper,
      source: factory.witness(node, label),
      astSha256: astHash(node),
    });
    return factory.text(node);
  };
  const cookieDeclarations = declarations(cookie).map((node) =>
    copy(
      cookie,
      node,
      "complete layout cookie declarations",
      "createHomeLayoutCookie",
    ),
  );
  const read = copy(
    cookie,
    exported(cookie, 810680, "i"),
    "complete synthetic-document reader",
    "createHomeLayoutCookie",
  );
  const readServer = copy(
    cookie,
    exported(cookie, 810680, "b"),
    "complete header parser; no server bootstrap claim",
    "createHomeLayoutCookie",
  );
  const write = copy(
    cookie,
    exported(cookie, 810680, "m"),
    "complete synthetic-document writer",
    "createHomeLayoutCookie",
  );
  const makeAdapter = copy(
    adapter,
    exported(adapter, 214100, "f"),
    "complete cookie adapter and Set subscriptions",
    "createCookieAdapter",
  );
  const define = copy(
    identity,
    exported(identity, 529281, "f"),
    "existing identity definition helper;1839 credited",
    "createHomeLayoutDefinition",
  );
  const selected = copy(
    definitions,
    definition.value,
    "complete actual safe layout descriptor construction",
    "createHomeLayoutDefinition",
  );
  const previewDeclarations = ["c", "d", "x"].map((name) =>
    copy(
      ui,
      declaration(ui, name),
      "complete used SVG " + name + " renderer",
      "createLayoutPreviews",
    ),
  );
  const previews = previewEntries.map((node) =>
    copy(
      ui,
      node,
      "complete actual " + propertyName(node.key) + " SVG projection",
      "createLayoutPreviews",
    ),
  );
  const isPreview = copy(
    ui,
    declaration(ui, "v"),
    "original preview membership predicate within selected map",
    "createLayoutPreviews",
  );
  const preview = copy(
    ui,
    fn(ui, "w"),
    "complete preview SVG wrapper",
    "createLayoutPreviews",
  );
  const pills = copy(
    ui,
    fn(ui, "k"),
    "complete plain radio/pills renderer",
    "createChoiceRenderer",
  );
  const label = copy(
    ui,
    declaration(ui, "S"),
    "complete option-label selector",
    "createChoiceRenderer",
  );
  const compact = copy(
    ui,
    declaration(ui, "P"),
    "complete compact-label threshold",
    "createChoiceRenderer",
  );
  const choice = copy(
    ui,
    fn(ui, "I"),
    "complete choice renderer including preview and plain branches",
    "createChoiceRenderer",
  );
  const hasPreview = copy(
    ui,
    fn(ui, "A"),
    "complete option preview test",
    "createChoiceRenderer",
  );
  const field = copy(
    ui,
    fn(ui, "ed"),
    "complete generic field dispatcher; unselected controls are ports",
    "createSettingsField",
  );
  const inline = copy(
    ui,
    fn(ui, "ex"),
    "complete dispatcher preview test",
    "createSettingsField",
  );
  const text = await prettier.format(
    `// Source-adapted original choice flow. Explicit ports only; importing reads no browser state.
export function createHomeLayoutCookie({document,location}){${cookieDeclarations.join("\n")}return {key:t,layouts:r,defaultLayout:i,coerce:n,read:${read},readServer:${readServer},write:${write}};}
export function createCookieAdapter(options){return (${makeAdapter})(options);}
export function createHomeLayoutDefinition({layout,cookieAdapter}){const r={x:layout.defaultLayout,E:layout.layouts,g:layout.coerce,i:layout.read,m:layout.write,b:layout.readServer},u={f:cookieAdapter},b={f:${define}};return ${selected};}
export function createLayoutPreviews({jsx,jsxs,useMemoCache}){const t={jsx,jsxs},i={c:useMemoCache};let ${previewDeclarations.join(",")};let j={${previews.join(",")}};let ${isPreview};${preview}return {isPreview:v,Preview:w};}
export function createChoiceRenderer({jsx,jsxs,useMemoCache,useTranslation,translateKey,markString,classNames,previews}){const t={jsx,jsxs},i={c:useMemoCache},l={f:useTranslation},K={f:translateKey},_={T:markString},o={c:classNames},v=previews.isPreview,w=previews.Preview;${pills}let ${label},${compact};${choice}${hasPreview}return {Choice:I,Pills:k,labelOption:S,isCompact:P};}
export function createSettingsField({jsx,jsxs,useMemoCache,useTranslation,translateKey,useHydrated,settings,Row,Switch,NumberInput,customControls,choice,previews}){const t={jsx,jsxs},i={c:useMemoCache},l={f:useTranslation},K={f:translateKey},el={f:useHydrated},W={o:settings.useSetting,Z:settings.useSetter},T={s:Row},ec={f:Switch},eo=NumberInput,en=customControls,I=choice.Choice,P=choice.isCompact,S=choice.labelOption,v=previews.isPreview;${field}${inline}return ed;}
`,
    { parser: "babel" },
  );
  const generated = parse(text, { sourceType: "module" });
  for (const entry of retained) {
    const wrapper = exactlyOne(
      findNodes(
        generated,
        (node) =>
          node.type === "FunctionDeclaration" &&
          node.id?.name === entry.wrapper,
      ),
      entry.wrapper,
    );
    assert.equal(
      findNodes(wrapper, (node) => astHash(node) === entry.astSha256).length,
      1,
      "retained AST exactly once in used wrapper: " + entry.label,
    );
  }
  const contract = {
    schema: 1,
    reviewBase: "094a06f18df738d41e77070c1a009e135671ac1a",
    scope:
      "Complete original choice/field renderer with actual home layout descriptor, selected pure SVG projections and cookie/read-write-notify flow; no Home/Settings product effect",
    selectedIndexEntries: entries,
    provenance: [...modules.values()].map((module) => module.provenance),
    retained,
    callerWitnesses: [
      definitions.witness(layoutImport, "actual layout helpers import"),
      definitions.witness(adapterImport, "actual cookie adapter import"),
      ui.witness(
        frameworkImport,
        "actual547562 framework API import; existing1839 external",
      ),
      registry.witness(
        registrySpread,
        "actual registry contains feed definitions",
      ),
    ],
    module: {
      path: DIRECTORY + "/client.mjs",
      sha256: sha256(Buffer.from(text)),
    },
    selectedPreviewKeys: ["layout-grid", "layout-table"],
    capabilities: {
      renderer:
        "Actual React/compiler/translation/class join/row and unselected Switch/Number/custom control ports; no private component/provider recovery claim",
      framework:
        "External547562 useSetting/useSetter APIs; existing1839 credited, not copied or retallied. Tests use labeled authored host hook, not original registry/provider parity.",
      storage:
        "Explicit synthetic document/location only; cookie access and writes are never acquired from actual browser state. Adapter Set notifications remain instance-local.",
    },
    credit:
      "Existing1839 recovers547562/671027 and actual switch, existingprivacy helper coversselectedlocalKey; this unit adds complete choice/dispatcher/local-cookie flow rather than recounting those frameworks.",
    limits: [
      "Only actual feed.homeLayout descriptor and its two pureSVG map entries are constructed. Other original preview-map keys and sensitive/custom/number/switch behavior remain explicit ports or unqualified.",
      "Header parser is retained; actual original SSR bootstrap/provider override and Home/Settings mounting/visual or downstream layout effects are not established.",
      "No real cookies/session/credentials, tenant requests, network mutations, trading/chart/account controls, new product preference page, original provider/API/pixel compatibility, security or completion claim.",
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
  assert.equal(
    await readFile(path.join(root, DIRECTORY, "contract.json"), "utf8"),
    JSON.stringify(result.contract, null, 2) + "\n",
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
    "Verified original choice/dispatcher, selected layout previews and cookie adapter; external framework/provider/Home boundaries retained",
  );
}
