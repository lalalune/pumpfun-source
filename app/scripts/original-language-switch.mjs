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
export const DIRECTORY = "reconstruction/language-switch";
const specs = [
  [
    447890,
    "babf5a6e1fea06e4.js",
    "3939f2a8bdd33c4ace6f89ae1d582c608df96c5ba4e7ab08a32bbd4ba5673346",
  ],
  [
    411657,
    "337439e6bd8e9380.js",
    "dbf10cf0f7f677ecaabca6d53825144562370403b391d78032475dd1aeba83d6",
  ],
  [
    644306,
    "a0ec47219f76f808.js",
    "f7b9c13e45242f55cfe960d7861c9c79f9cf520a7c77f5ce2eb02402b1916f70",
  ],
  [
    592209,
    "a0ec47219f76f808.js",
    "6b3fe2082dbaa30d9d803777d25ef02aa53ccc736b312980dec097206324c790",
  ],
  [
    187611,
    "a0ec47219f76f808.js",
    "bd62a3ae8bc3cb897b656e246f762a897468e49c9752cfbe9e82f51de8397c3b",
  ],
  [
    124884,
    "4490d02ba2117672.js",
    "dfcb487f79e63fa817cef92fd322e172c6d44fb2270bad175820a463b2e382ea",
  ],
  [
    956718,
    "11cf0bf8a734ea43.js",
    "00b703deb875b1517888552730f857a14e594ae5d6e0cf6948d55a23731b57e2",
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

export async function recover(root = APP) {
  const corpus = await openCorpus(root),
    modules = new Map(),
    entries = [];
  for (const [id, basename, hash] of specs) {
    const rows = corpus.index.modules.filter((entry) => entry.ids.includes(id));
    assert.equal(rows.length, 1, `review all variants ${id}`);
    assert.equal(rows[0].sha256, hash);
    assert.equal(rows[0].origins.length, 1);
    const factory = await corpus.factory(id, {
      source: "evidence/web/objects/" + basename,
    });
    assert.equal(factory.provenance.sha256, hash);
    modules.set(id, factory);
    entries.push(rows[0]);
  }
  const selector = modules.get(447890),
    client = modules.get(411657),
    cookie = modules.get(644306);
  const catalog = modules.get(592209),
    token = modules.get(187611),
    caller = modules.get(124884),
    definitions = modules.get(956718);
  for (const id of [411657, 592209, 187611]) imported(selector, id);
  imported(client, 644306);
  imported(cookie, 592209);
  const selectorImport = imported(caller, 447890);
  const field = exactlyOne(
    findNodes(
      caller.node,
      (node) =>
        node.type === "ObjectProperty" && propertyName(node.key) === "language",
    ),
    "actual custom language field",
  );
  const fieldCall = exactlyOne(
    findNodes(
      field.value,
      (node) =>
        node.type === "CallExpression" &&
        member(target(node.callee), "t", "jsx") &&
        member(node.arguments[0], selectorImport.id.name, "f"),
    ),
    "custom field renders actual language selector",
  );
  const definition = exactlyOne(
    findNodes(
      definitions.node,
      (node) =>
        node.type === "ObjectProperty" &&
        propertyName(node.key) === "display.language",
    ),
    "actual language descriptor",
  );
  assert.equal(
    objectProperty(
      objectProperty(definition.value.arguments[0], "control"),
      "component",
    ).value,
    "language",
  );
  const selected = exported(selector, 447890, "f");
  const clientCall = exactlyOne(
    findNodes(
      selected,
      (node) =>
        node.type === "CallExpression" && member(target(node.callee), "s", "C"),
    ),
    "selector invokes actual language client",
  );
  assert.equal(objectProperty(clientCall.arguments[0], "instance").name, "k");
  assert.equal(objectProperty(clientCall.arguments[0], "locale").name, "t");
  assert.equal(objectProperty(clientCall.arguments[0], "namespaces").name, "o");
  const kept = [];
  const copy = (factory, node, label) => {
    kept.push({
      label,
      source: factory.witness(node, label),
      astSha256: astHash(node),
    });
    return factory.text(node);
  };
  const catalogBody = declarations(catalog).map((node) =>
    copy(catalog, node, "complete locale metadata/order/alias declarations"),
  );
  const normalizer = copy(
    catalog,
    exported(catalog, 592209, "v"),
    "complete original locale normalizer; existing prize helper credited",
  );
  const defaultLocale = copy(
    catalog,
    exported(catalog, 592209, "T"),
    "actual fallback locale",
  );
  const cookieBody = declarations(cookie).map((node) =>
    copy(cookie, node, "complete cookie name/parser declarations"),
  );
  const readCookie = copy(
    cookie,
    exported(cookie, 644306, "I"),
    "complete explicit-document cookie reader",
  );
  const writeCookie = copy(
    cookie,
    exported(cookie, 644306, "E"),
    "complete explicit-document cookie writer",
  );
  const clientBody = declarations(client).map((node) =>
    copy(
      client,
      node,
      "complete namespace client/cache/error/transition declarations",
    ),
  );
  const namespaces = copy(
    selector,
    declaration(selector, "o"),
    "actual complete selector namespace list",
  );
  const option = copy(
    selector,
    exactlyOne(
      selector.node.body.body.filter(
        (node) => node.type === "FunctionDeclaration" && node.id.name === "u",
      ),
      "actual option renderer",
    ),
    "complete original language option renderer",
  );
  const identity = copy(
    token,
    exported(token, 187611, "T"),
    "actual language-value string marker",
  );
  const component = copy(
    selector,
    selected,
    "complete original language selector component",
  );
  const text = await prettier.format(
    `// Source-adapted original language workflow. All browser/provider capabilities are explicit.
export function createLocaleCatalog(){${catalogBody.join("\n")}return {metadata:t,locales:n,defaultLocale:${defaultLocale},normalizeLocale:${normalizer}};}
export function createLocaleCookie({document,location,normalizeLocale}){const t={v:normalizeLocale};${cookieBody.join("\n")}return {parseHeader:a,readCookie:${readCookie},writeCookie:${writeCookie}};}
export function createLanguageClient({fetch,logger,writeCookie}){const t={y:logger},n={E:writeCookie};${clientBody.join("\n")}return {namespace:a,seedNamespaces:o,prefetchCatalog:l,changeLanguage:c};}
export function createLanguageSelector({jsx,jsxs,useMemoCache,useState,useTransition,useTranslation,useRouter,select,catalog,changeLanguage}){const t={jsx,jsxs},i={c:useMemoCache},l={useRouter},n={useState,useTransition},a={f:useTranslation},r={d:select.Root,P:select.Trigger,U:select.Value,r:select.Content,T:select.Item},s={C:changeLanguage},c={L:catalog.metadata,O:catalog.locales,T:catalog.defaultLocale,v:catalog.normalizeLocale},d={T:${identity}};let ${namespaces};${option}return ${component};}
`,
    { parser: "babel" },
  );
  const ast = parse(text, { sourceType: "module" });
  for (const node of kept)
    assert.ok(
      findNodes(ast, (candidate) => astHash(candidate) === node.astSha256)
        .length > 0,
      `retained AST missing: ${node.label}`,
    );
  const contract = {
    schema: 1,
    reviewBase: "094a06f18df738d41e77070c1a009e135671ac1a",
    scope:
      "Complete selected Settings language component and namespace-read/cookie-write/i18n/refresh client flow, with explicit synthetic capability ports",
    selectedIndexEntries: entries,
    provenance: [...modules.values()].map((module) => module.provenance),
    retained: kept,
    callerWitnesses: [
      definitions.witness(
        definition,
        "actual language custom-control descriptor; metadata is not server persistence",
      ),
      caller.witness(selectorImport, "actual selector import"),
      caller.witness(field.value, "complete custom Settings field consumer"),
      caller.witness(fieldCall, "actual selector render"),
      selector.witness(
        clientCall,
        "actual instance/locale/namespaces/router client call",
      ),
    ],
    module: {
      path: DIRECTORY + "/client.mjs",
      sha256: sha256(Buffer.from(text)),
    },
    selectorNamespaces: declaration(selector, "o").init.elements.map((node) => {
      assert.equal(node.type, "StringLiteral");
      return node.value;
    }),
    capabilities: {
      cookie:
        "Supplied document/location only; no global defaults or actual-cookie access",
      client:
        "Supplied fetch/logger/cookie writer and i18n/router instance; same-origin relative GET source paths do not prove server implementation or anonymous access",
      component:
        "Supplied React/compiler/translation/router and Select components; private provider/control behavior unqualified",
    },
    credit:
      "Existing captured locale/copy work and original-prize-formats already retain 592209 normalization metadata; privacy/local-settings work maps preference boundaries. This unit adds the complete actual language selector/client workflow, not first locale-helper or whole Settings recovery.",
    limits: [
      "The actual custom language UI calls 411657 directly; do not invent a 547562/214100 dependency or import the unmerged local-settings runtime.",
      "Only the language export and used declarations are adapted from co-registered447890/749099; trading sibling749099 is excluded.",
      "No actual cookies/session/credentials, real app/tenant request, global translation UI or new locale backend is supplied. Tests use synthetic document/location/i18n/Select/router/fetch ports and owned loopback GETs only.",
      "Catalog-prefetch cache and error/fallback/order quirks are preserved; no stronger concurrency, cancellation or atomic cookie/provider guarantee is inferred.",
      "No original private provider/API/pixel equivalence, feature milestone or security assurance claim.",
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
    "Verified complete original language selector, namespace/cookie/i18n client and explicit source contexts; no real provider/backend parity claim",
  );
}
