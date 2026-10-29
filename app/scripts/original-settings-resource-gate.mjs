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
export const DIRECTORY = "reconstruction/settings-resource-gate";
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
  const corpus = await openCorpus(root);
  const rows = corpus.index.modules.filter((row) => row.ids.includes(124884));
  assert.equal(
    rows.length,
    1,
    "all captured Settings factory variants reviewed",
  );
  assert.equal(rows[0].sha256, specs[0][2]);
  assert.equal(rows[0].origins.length, 1);
  const factory = await corpus.factory(124884, {
    source: "evidence/web/objects/4490d02ba2117672.js",
  });
  const frame = exported(factory, 124884, "SettingsModal");
  for (const [id, alias] of [
    [732486, "t"],
    [445242, "i"],
    [352386, "n"],
    [398902, "l"],
    [165228, "a"],
    [411657, "e$"],
    [592209, "eB"],
  ])
    assert.equal(
      imported(factory, id).id.name,
      alias,
      "actual module binding for explicit port",
    );

  const gate = exactlyOne(
    findNodes(
      frame,
      (node) => node.type === "VariableDeclarator" && node.id.name === "J",
    ),
    "actual resource-attempt IIFE",
  ).init;
  assert.equal(gate.type, "CallExpression");
  assert.equal(gate.callee.type, "ArrowFunctionExpression");
  assert.equal(gate.arguments.length, 0);
  const sentinel = exactlyOne(
    findNodes(
      gate,
      (node) =>
        node.type === "CallExpression" && member(node.callee, "a", "exists"),
    ),
    "translation sentinel check",
  );
  assert.equal(sentinel.arguments[0].value, "web.trade.max_slippage");
  const prefetch = exactlyOne(
    findNodes(
      gate,
      (node) =>
        node.type === "CallExpression" &&
        member(target(node.callee), "e$", "u"),
    ),
    "actual prefetch call",
  );
  assert.deepEqual(
    prefetch.arguments.map((n) => n.name),
    ["a", "t"],
  );
  const load = fn(factory, "eq"),
    row = fn(factory, "eX"),
    indices = declaration(factory, "eE");
  assert.deepEqual(
    indices.init.elements.map((n) => n.value),
    [0, 1, 2, 3, 4],
  );
  const output = exactlyOne(
    findNodes(
      frame,
      (node) =>
        node.type === "AssignmentExpression" &&
        node.left.name === "O" &&
        node.right.type === "ConditionalExpression" &&
        node.right.test.name === "J",
    ),
    "actual readiness/content assignment",
  );
  const memo = exactlyOne(
    findNodes(
      frame,
      (node) =>
        node.type === "SequenceExpression" &&
        node.expressions.length === 2 &&
        findNodes(node.expressions[0], (n) => n === output).length === 1 &&
        findNodes(
          node.expressions[1],
          (n) => n.type === "AssignmentExpression" && n.left.name === "W",
        ).length === 2,
    ),
    "complete actual content/scroll-wrapper memo sequence",
  );
  const busy = exactlyOne(
    findNodes(
      frame,
      (node) => node.type === "VariableDeclarator" && node.id.name === "ew",
    ),
    "actual aria-busy derivation",
  );
  const query = exactlyOne(
    findNodes(
      frame,
      (node) =>
        node.type === "ConditionalExpression" &&
        node.test.type === "BinaryExpression" &&
        node.test.left.type === "MemberExpression" &&
        node.test.left.object.name === "X" &&
        node.test.left.property.value === 0 &&
        findNodes(
          node,
          (n) => n.type === "CallExpression" && member(n.callee, "et", "trim"),
        ).length === 1,
    ),
    "actual query-trim memo",
  );
  const nonblank = exactlyOne(
    findNodes(
      frame,
      (node) => node.type === "VariableDeclarator" && node.id.name === "ex",
    ),
    "actual query-length alias",
  );
  assert.equal(nonblank.init.operator, ">");
  assert.ok(member(nonblank.init.left, "o", "length"));
  assert.equal(nonblank.init.right.value, 0);
  const retained = [];
  const copy = (node, label) => {
    retained.push({
      label,
      source: factory.witness(node, label),
      astSha256: astHash(node),
    });
    return factory.text(node);
  };
  const gateText = copy(
    gate,
    "complete original resource-attempt hook IIFE; finally completes attempt, cleanup suppresses state update",
  );
  const indicesText = copy(indices, "complete five loading row indices");
  const loadingText = copy(
    load,
    "complete aria-hidden Settings loading component",
  );
  const rowText = copy(row, "complete keyed three-block skeleton row");
  const queryText = copy(query, "actual memoized trimmed-query derivation");
  const nonblankText = copy(
    nonblank,
    "actual trimmed-query positive-length alias",
  );
  const busyText = copy(busy, "actual attempt-pending aria-busy expression");
  const memoText = copy(
    memo,
    "complete actual loading/results/section conditional and scroll-wrapper compiler memo sequence",
  );
  const text = await prettier.format(
    `// Source-adapted original Settings resource-attempt and complete content/loading branch.
// Browser/i18n/translation-provider/section capabilities are explicit. No global Settings mount.
export function createSettingsResourceContent({jsx,jsxs,useMemoCache,useState,useEffect,useTranslation,normalizeLocale,defaultLocale,prefetchCatalog,SearchResults,Section,FocusProvider}){
 const t={jsx,jsxs},i={c:useMemoCache},n={useState,useEffect},l={f:useTranslation},eB={v:normalizeLocale,T:defaultLocale},e$={u:prefetchCatalog},a={_:{Provider:FocusProvider}},eb=SearchResults,eF=Section;
 let ${indicesText};${loadingText}${rowText}
 function useSettingsResourceAttempt(){return (${gateText});}
 function SettingsResourceContent({query:et,visibleSections:ea,section:eo,focusValue:ee,onRequestClose:G,scrollRef:el}){
  let O,W,o,X=(0,i.c)(100),J=useSettingsResourceAttempt();${queryText};let ${nonblankText};let ${busyText};${memoText};return W;
 }
 return {SettingsResourceContent,Loading:eq,useSettingsResourceAttempt};
}`,
    { parser: "babel" },
  );
  const ast = parse(text, { sourceType: "module" });
  const wrapper = exactlyOne(
    findNodes(
      ast,
      (node) =>
        node.type === "FunctionDeclaration" &&
        node.id?.name === "createSettingsResourceContent",
    ),
    "actual used exported constructor",
  );
  for (const region of retained)
    assert.equal(
      findNodes(wrapper, (node) => astHash(node) === region.astSha256).length,
      1,
      "complete original region once in used constructor",
    );
  const locale = await corpus.factory(592209, {
    source: "evidence/web/objects/a0ec47219f76f808.js",
  });
  const language = await corpus.factory(411657, {
    source: "evidence/web/objects/337439e6bd8e9380.js",
  });
  const contract = {
    schema: 1,
    reviewBase: "094a06f18df738d41e77070c1a009e135671ac1a",
    scope:
      "Complete original Settings resource-attempt hook and actual content/loading/scroll-view branch with explicit capabilities, not resource-availability assertion or full modal",
    indexEntry: rows[0],
    factory: factory.provenance,
    retained,
    witnesses: [
      factory.witness(imported(factory, 732486), "actual JSX runtime import"),
      factory.witness(
        imported(factory, 445242),
        "actual compiler memo runtime import",
      ),
      factory.witness(
        imported(factory, 398902),
        "actual translation-hook import",
      ),
      factory.witness(
        imported(factory, 165228),
        "actual focus-provider context import; implementation remains external",
      ),
      factory.witness(
        fn(factory, "eb"),
        "actual results output target; separately recovered1898, not copied",
      ),
      factory.witness(
        fn(factory, "eF"),
        "actual section output target; private/account/other sections remain external",
      ),
      factory.witness(
        imported(factory, 411657),
        "actual prefetch client import; exact API recovered separately in1864",
      ),
      factory.witness(
        imported(factory, 592209),
        "actual locale normalization/default import; existing1864 metadata credited",
      ),
      factory.witness(
        imported(factory, 352386),
        "actual React hooks dependency context",
      ),
      factory.witness(
        output,
        "actual J controls loading vs query/section content",
      ),
      language.witness(
        language.node,
        "external language client complete context; original prefetch catches/logs individual namespace failures",
      ),
      locale.witness(
        locale.node,
        "external locale metadata/normalization/default context; no locale implementation retallied",
      ),
    ],
    module: {
      path: DIRECTORY + "/client.mjs",
      sha256: sha256(Buffer.from(text)),
    },
    credit:
      "1864 already recovers411657 prefetch and592209 locale metadata. They remain explicit ports here, without unmerged imports/copy/retally.1898 recovers the supplied results component,1872 field rendering,1839 setting state; all remain external. Existing675/683 metadata/context is credited.",
    capabilities: {
      react:
        "Actual React hooks/compiler/JSX ports; original hook and complete memo regions retained.",
      i18n: "useTranslation supplies synthetic i18n.exists/language; prefetchCatalog(i18n,locale) and normalizeLocale/defaultLocale are explicit1864-compatible ports. No live provider/network/cookie acquisition.",
      content:
        "SearchResults,Section and FocusProvider are explicit used components. Selected section/visible sections/focus value/close callback/scroll ref are supplied; private availability/account/feature discovery and parent dialog remain external.",
    },
    limits: [
      "Initial exists sentinel initializes hook state once. A completed prefetch attempt enables content even if the sentinel stays absent; this does not prove all resources loaded.",
      "Effect depends on i18n identity and attempt state, not language directly. Ready state is not reset when provider changes. Cleanup only suppresses setState; no request cancellation, retry, rollback or new policy is introduced.",
      "A rejecting synthetic prefetch port leaves the finally-chain rejection observable; original1864 normally catches/logs individual namespace failures. No unsupported promise-rejection handling added.",
      "Loading is original five-row aria-hidden output, not an accessible progress announcement; surrounding actual wrapper uses aria-busy. CSS utility names retained without original CSS/visual parity.",
      "No original outer modal, focus provider, global mount, preferences/wallet/admin/trading controls, actual cookies/storage/sessions/credentials or tenant requests. No native/API/pixel parity, completion or security acceptance.",
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
    "Verified complete original Settings resource-attempt/loading/content caller; resource/provider boundaries preserved",
  );
}
