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
export const DIRECTORY = "reconstruction/settings-search-results";
const specs = [
  [
    124884,
    "4490d02ba2117672.js",
    "dfcb487f79e63fa817cef92fd322e172c6d44fb2270bad175820a463b2e382ea",
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
    rows = corpus.index.modules.filter((row) => row.ids.includes(124884));
  assert.equal(rows.length, 1, "all current124884 variants must be reviewed");
  assert.equal(rows[0].sha256, specs[0][2]);
  assert.equal(rows[0].origins.length, 1);
  const factory = await corpus.factory(124884, {
    source: "evidence/web/objects/4490d02ba2117672.js",
  });
  const component = fn(factory, "eb"),
    forward = fn(factory, "eg"),
    normalizer = declaration(factory, "ef");
  const call = exactlyOne(
    findNodes(
      factory.node,
      (node) =>
        node.type === "CallExpression" &&
        member(target(node.callee), "t", "jsx") &&
        node.arguments[0]?.name === "eb",
    ),
    "actual Settings search/results render",
  );
  const callerGuard = exactlyOne(
    findNodes(
      factory.node,
      (node) =>
        node.type === "ConditionalExpression" && node.consequent === call,
    ),
    "actual nonblank-query results branch",
  );
  assert.equal(callerGuard.test.name, "ex");
  const callerFrame = exported(factory, 124884, "SettingsModal");
  const nonblank = exactlyOne(
    findNodes(
      callerFrame,
      (node) => node.type === "VariableDeclarator" && node.id.name === "ex",
    ),
    "actual nonblank guard alias",
  );
  assert.equal(nonblank.init.type, "BinaryExpression");
  assert.equal(nonblank.init.operator, ">");
  assert.ok(member(nonblank.init.left, "o", "length"));
  assert.equal(nonblank.init.right.value, 0);
  const trimmed = exactlyOne(
    findNodes(
      callerFrame,
      (node) =>
        node.type === "AssignmentExpression" &&
        node.left.name === "o" &&
        node.right.type === "CallExpression" &&
        member(node.right.callee, "et", "trim"),
    ),
    "actual memoized trim feeding guard alias",
  );
  const query = objectProperty(call.arguments[1], "query");
  assert.equal(query.type, "CallExpression");
  assert.ok(member(query.callee, "et", "trim"));
  assert.equal(objectProperty(call.arguments[1], "visibleSections").name, "ea");
  assert.ok(
    findNodes(
      forward,
      (node) =>
        node.type === "CallExpression" &&
        member(target(node.callee), "t", "jsx") &&
        node.arguments[0]?.name === "ed" &&
        objectProperty(node.arguments[1], "definition")?.name === "e" &&
        member(node.arguments[2], "e", "id"),
    ).length === 1,
  );
  const retained = [];
  const copy = (node, label) => {
    retained.push({
      label,
      source: factory.witness(node, label),
      astSha256: astHash(node),
    });
    return factory.text(node);
  };
  const normText = copy(
    normalizer,
    "complete original query/document normalizer; original case-before-NFKD retained",
  );
  const componentText = copy(
    component,
    "complete original Settings query/filter/grouped/empty results renderer",
  );
  const forwardText = copy(
    forward,
    "complete original keyed definition→field forwarder",
  );
  const text = await prettier.format(
    `// Source-adapted full original search/results component. Explicit module-lifetime ports only.
export function createSettingsSearchResults({jsx,jsxs,useMemoCache,useTranslation,translateKey,useHiddenSettingIds,registry,sections,Field,Section}){const t={jsx,jsxs},i={c:useMemoCache},l={f:useTranslation},K={f:translateKey},T={X:Section},ep={g:registry},ey={n:sections},ed=Field,eh=useHiddenSettingIds;let ${normText};${componentText}${forwardText}return eb;}
`,
    { parser: "babel" },
  );
  const generated = parse(text, { sourceType: "module" }),
    wrapper = exactlyOne(
      findNodes(
        generated,
        (node) =>
          node.type === "FunctionDeclaration" &&
          node.id?.name === "createSettingsSearchResults",
      ),
      "actual exported constructor",
    );
  for (const region of retained)
    assert.equal(
      findNodes(wrapper, (node) => astHash(node) === region.astSha256).length,
      1,
      "complete region exactly once inside returned used flow",
    );
  const contract = {
    schema: 1,
    reviewBase: "094a06f18df738d41e77070c1a009e135671ac1a",
    scope:
      "Complete captured Settings search/results component with explicit metadata/translation/visibility/field/React ports; no preference implementation or global mount",
    indexEntry: rows[0],
    factory: factory.provenance,
    retained,
    callerWitnesses: [
      factory.witness(
        call,
        "actual query.trim()/visibleSections Settings caller",
      ),
      factory.witness(
        trimmed,
        "actual memoized trim assignment feeding nonblank guard",
      ),
      factory.witness(nonblank, "actual trimmed length>0 guard alias"),
      factory.witness(
        callerGuard,
        "actual nonblank-query results branch; outer availability and other view remain external",
      ),
      factory.witness(
        imported(factory, 272700),
        "actual registry provider import; external module-lifetime capability",
      ),
      factory.witness(
        imported(factory, 532757),
        "actual section catalog provider import; existing settings mapping credited",
      ),
      factory.witness(
        declaration(factory, "eh"),
        "actual visibility helper context; feature provider behavior remains external",
      ),
      factory.witness(
        fn(factory, "ed"),
        "actual field-dispatch output target; existing1872 component credited, not copied",
      ),
    ],
    module: {
      path: DIRECTORY + "/client.mjs",
      sha256: sha256(Buffer.from(text)),
    },
    capabilities: {
      metadata:
        "Registry/catalog are module-lifetime references. No implicit subscriptions or mutation/reactivity policy added.",
      visibility:
        "Supplied hidden-ID hook preserves the original Set.has filtering contract; private flags/provider acquisition are not implemented.",
      ui: "Supplied React/compiler, translation, Field and Section components. Full keyed forwarder retained, without preference values, controls or private framework implementation.",
    },
    credit:
      "1885 is the separate native identifier-text correction;1872 recovers field/choice rendering and1839 setting state. Existing675/683 metadata/translation mapping is credited. None is copied, imported as an unmerged dependency, retallied or superseded.",
    limits: [
      "The actual Settings caller supplies trimmed query and visible sections. Whole modal routing/input/provider/outer-availability gate/global mounting is not reconstructed.",
      "Original locale-sensitive case-before-NFKD behavior is retained; no1188 normalization fix or native parity is imported.",
      "Compiler memo tracks query, visibility/translation and section-list identities; module-lifetime registry/catalog arrays are not newly reactive stores.",
      "Tests use safe synthetic read-only metadata and explicit host ports only; no preferences/account/trading controls, user cookies/sessions/credentials, service requests, auth, backend or native/pixel/completion/security claim.",
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
    "Verified complete original Settings query/filter/grouped/empty renderer; external capability boundaries preserved",
  );
}
