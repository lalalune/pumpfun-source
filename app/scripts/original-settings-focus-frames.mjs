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
export const DIRECTORY = "reconstruction/settings-focus-frames";
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
    rows = corpus.index.modules.filter((row) => row.ids.includes(165228));
  assert.equal(rows.length, 1, "all grouped focus/frame variants reviewed");
  assert.deepEqual(rows[0].ids, [379288, 165228]);
  assert.equal(rows[0].origins.length, 1);
  assert.equal(
    rows[0].sha256,
    "ab377b76367b582ab93f114fe047043fdf3289275a00fc3e878ed31da36aad2c",
  );
  const f = await corpus.factory(165228, {
    source: "evidence/web/objects/8401a8e00b4638cb.js",
  });
  for (const [id, name] of [
    [732486, "t"],
    [445242, "n"],
    [426091, "r"],
    [352386, "l"],
  ])
    assert.equal(
      imported(f, id).id.name,
      name,
      "actual explicit capability binding",
    );
  for (const [name, alias] of [
    ["_", "a"],
    ["A", "s"],
    ["h", "o"],
  ])
    assert.equal(
      exported(f, 165228, name).name,
      alias,
      "actual grouped focus export",
    );
  const retained = [];
  const copy = (node, label) => {
    retained.push({
      label,
      source: f.witness(node, label),
      astSha256: astHash(node),
    });
    return f.text(node);
  };
  const context = copy(
    declaration(f, "a"),
    "complete original focus context initialization",
  );
  const reader = copy(
    declaration(f, "s"),
    "complete original React.use focus-context reader",
  );
  const hook = copy(
    declaration(f, "o"),
    "complete2500ms transient-focus hook; original one-shot state/no-reset and cleanup",
  );
  const provider = copy(
    exported(f, 165228, "w"),
    "complete exported transient-focus provider component",
  );
  const header = copy(fn(f, "c"), "complete section header renderer");
  const row = copy(
    exported(f, 379288, "s"),
    "complete Settings row renderer including actual ref/scroll/highlight effect",
  );
  const section = copy(
    exported(f, 379288, "X"),
    "complete Settings section renderer and header/description/children branch",
  );
  const text = await prettier.format(
    `// Source-adapted complete original Settings focus, row and section frames.
export function createSettingsFocusFrames({jsx,jsxs,useMemoCache,createContext,use,useState,useEffect,useRef,classNames,window}){
 const t={jsx,jsxs},n={c:useMemoCache},r={c:classNames},l={createContext,use,useState,useEffect,useRef};
 let ${context},${reader},${hook};${header}
 const FocusProvider=${provider},Row=${row},Section=${section};
 return {FocusContext:a,useFocusSettingId:s,useTransientSettingId:o,FocusProvider,Row,Section};
}`,
    { parser: "babel" },
  );
  const generated = parse(text, { sourceType: "module" }),
    wrapper = exactlyOne(
      findNodes(
        generated,
        (node) =>
          node.type === "FunctionDeclaration" &&
          node.id?.name === "createSettingsFocusFrames",
      ),
      "used exported constructor",
    );
  for (const region of retained)
    assert.equal(
      findNodes(wrapper, (node) => astHash(node) === region.astSha256).length,
      1,
      "complete raw region exactly once in used constructor",
    );
  const cf = await corpus.factory(124884, {
    source: "evidence/web/objects/4490d02ba2117672.js",
  });
  assert.equal(cf.provenance.sha256, specs[0][2]);
  assert.equal(imported(cf, 165228).id.name, "a");
  assert.equal(imported(cf, 379288).id.name, "T");
  const modal = exported(cf, 124884, "SettingsModal"),
    focus = exactlyOne(
      findNodes(
        modal,
        (node) => node.type === "VariableDeclarator" && node.id.name === "ee",
      ),
      "actual caller focus value",
    );
  assert.ok(member(target(focus.init.callee), "a", "h"));
  assert.deepEqual(
    focus.init.arguments.map((n) => n.name),
    ["H"],
  );
  const providerCall = exactlyOne(
    findNodes(
      modal,
      (node) =>
        node.type === "CallExpression" &&
        member(target(node.callee), "t", "jsx") &&
        node.arguments[0]?.type === "MemberExpression" &&
        node.arguments[0].object?.type === "MemberExpression" &&
        member(node.arguments[0].object, "a", "_") &&
        node.arguments[0].property.name === "Provider",
    ),
    "actual focus provider caller",
  );
  assert.equal(objectProperty(providerCall.arguments[1], "value").name, "ee");
  const rowCalls = findNodes(
    cf.node,
    (node) =>
      node.type === "CallExpression" &&
      ["jsx", "jsxs"].some((key) => member(target(node.callee), "t", key)) &&
      member(node.arguments[0], "T", "s"),
  );
  const sectionCalls = findNodes(
    cf.node,
    (node) =>
      node.type === "CallExpression" &&
      ["jsx", "jsxs"].some((key) => member(target(node.callee), "t", key)) &&
      member(node.arguments[0], "T", "X"),
  );
  assert.ok(
    rowCalls.length > 0 && sectionCalls.length > 0,
    "actual used Row and Section call sites required",
  );
  const firstRow = exactlyOne(
    rowCalls.filter(
      (node) =>
        objectProperty(node.arguments[1], "settingId")?.name === "x" &&
        node.arguments[1].properties.some(
          (p) => p.key?.name === "control" && p.value?.name === "n",
        ),
    ),
    "actual language-row readonly wrapper output",
  );
  const firstSection = exactlyOne(
    findNodes(
      fn(cf, "eb"),
      (node) =>
        node.type === "CallExpression" &&
        member(target(node.callee), "t", "jsx") &&
        member(node.arguments[0], "T", "X"),
    ),
    "actual results component section call",
  );
  const contract = {
    schema: 1,
    reviewBase: "094a06f18df738d41e77070c1a009e135671ac1a",
    scope:
      "Complete original transient focus/context + row/section renderers, actual Settings caller bound; no preference or outer-modal acquisition",
    indexEntry: rows[0],
    factory: f.provenance,
    retained,
    witnesses: [
      f.witness(
        imported(f, 352386),
        "actual React createContext/use/state/effect/ref dependency",
      ),
      f.witness(imported(f, 445242), "actual compiler memo dependency"),
      f.witness(
        imported(f, 426091),
        "actual class combiner remains explicit port",
      ),
      cf.witness(imported(cf, 165228), "actual Settings focus import"),
      cf.witness(imported(cf, 379288), "actual Settings row/section import"),
      cf.witness(
        focus,
        "actual focusSettingId alias H passed into h; no provider state acquisition",
      ),
      cf.witness(
        providerCall,
        "actual focus value passed to same context.Provider around section content",
      ),
      cf.witness(
        firstRow,
        "actual definition row outputs settingId/title/description/control to379288.s; control implementation remains external",
      ),
      cf.witness(
        firstSection,
        "actual Settings results section uses379288.X; supplied row/result logic credited separately",
      ),
    ],
    module: {
      path: DIRECTORY + "/client.mjs",
      sha256: sha256(Buffer.from(text)),
    },
    capabilities: {
      react:
        "Actual JSX/compiler/hooks/createContext/React.use ports; no private provider acquisition.",
      timer:
        "Explicit window.setTimeout/clearTimeout capability, source delay2500ms retained. No global property overridden.",
      classNames:
        "Original426091 class combiner is an explicit port, no whole vendor/tailwind algorithm claim.",
      content:
        "Original Row/Section accept readonly React nodes for title/description/note/control/children; controls are not reconstructed or acquired here.",
    },
    credit:
      "Existing1839/1872/1898/1911 already retain actual callers with Row/Section/focus ports. This unit closes those distinct frame capabilities, without copying/importing unmerged implementations or retallying them. Generic shell/search/modal primitives and prior native Settings fixes remain unchanged.",
    limits: [
      "Initial hook state is true once; changing target before expiry clears/restarts timer, but after expiry a new target does not reset state totrue. Falsey target returnsnull. Remount starts fresh.",
      "Row scroll effect depends only on its focused boolean; same focus does not cause repeated scroll on unrelated props. Native scrollIntoView optional call uses center/smooth; it does not focus an input or implement parent focus trapping.",
      "Actual124884 calls h(H) then context.Provider; exported w is a complete alternative exported wrapper, not falsely attributed as this caller's literal component. Both consume the same hook/context.",
      "No preference state/control/mutation, actualcookies/storage/sessions/credentials/userdata/tenantrequest, protected availability/wallet/admin/trading path, full parentmodal/global mount/CSS/vendor/native/API/pixel/security/completion claim.",
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
    "Verified complete original Settings transient-focus/context and row/section renderer flow",
  );
}
