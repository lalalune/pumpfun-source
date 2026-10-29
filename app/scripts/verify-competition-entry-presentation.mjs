import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "@babel/parser";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  sha256,
} from "./original-contracts/source.mjs";
const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const PAGE = "packages/frontend/src/app/leaderboard/leaderboard-client.tsx";
const PACKAGE = "reconstruction/competition-entry-presentation";
const parseNative = (text) =>
  parse(text, { sourceType: "module", plugins: ["jsx", "typescript"] });
function clean(node, identifiers = {}, strings = {}) {
  if (Array.isArray(node))
    return node.map((n) => clean(n, identifiers, strings));
  if (!node || typeof node !== "object") return node;
  if (node.type === "Identifier" && identifiers[node.name])
    return clean(identifiers[node.name]);
  if (node.type === "StringLiteral" && Object.hasOwn(strings, node.value))
    return clean(strings[node.value]);
  return Object.fromEntries(
    Object.entries(node)
      .filter(
        ([k]) =>
          ![
            "start",
            "end",
            "loc",
            "extra",
            "comments",
            "leadingComments",
            "trailingComments",
            "innerComments",
            "typeAnnotation",
            "returnType",
            "typeParameters",
          ].includes(k),
      )
      .map(([k, v]) => [k, clean(v, identifiers, strings)]),
  );
}
const expression = (s) => parseNative("(" + s + ")").program.body[0].expression;
const member = (n, o, p) =>
  n?.type === "MemberExpression" &&
  n.object?.name === o &&
  n.property?.name === p;
const jsx = (n, name) =>
  n.type === "JSXElement" &&
  n.openingElement.name.type === "JSXIdentifier" &&
  n.openingElement.name.name === name;
const attribute = (n, name) =>
  exactlyOne(
    n.openingElement.attributes.filter(
      (a) => a.type === "JSXAttribute" && a.name.name === name,
    ),
    "actual attribute " + name,
  ).value;
const exprChildren = (n) =>
  n.children
    .filter((c) => c.type === "JSXExpressionContainer")
    .map((c) => c.expression);
export function nativeRow(text) {
  return exactlyOne(
    findNodes(
      parseNative(text),
      (n) =>
        n.type === "FunctionDeclaration" &&
        n.id?.name === "CompetitionEntryRows",
    ),
    "actual complete native row",
  );
}
export async function verifyCompetitionEntryPresentation(appRoot = APP) {
  const corpus = await openCorpus(appRoot),
    rows = corpus.index.modules.filter((r) => r.ids.includes(590407));
  assert.deepEqual(
    rows.map((r) => r.sha256),
    ["3f494070c58a6d7f0f70279887ef648107935b765fe849de3e9ec100cec45dda"],
  );
  const f = await corpus.factory(590407, { source: rows[0].origins[0].source });
  const original = exactlyOne(
    findNodes(
      f.node,
      (n) => n.type === "FunctionDeclaration" && n.id?.name === "X",
    ),
    "actual complete original row X",
  );
  const rank = exactlyOne(
    findNodes(
      original,
      (n) =>
        n.type === "ConditionalExpression" &&
        member(n.consequent, "U", "rank") &&
        n.alternate?.value === "–",
    ),
    "original rank expression",
  );
  const tone = exactlyOne(
    findNodes(
      original,
      (n) =>
        n.type === "ConditionalExpression" &&
        n.consequent?.value === "text-text-primary" &&
        n.alternate?.type === "ConditionalExpression",
    ),
    "original zero/positive/negative tone",
  );
  const sign = exactlyOne(
    findNodes(
      original,
      (n) =>
        n.type === "ConditionalExpression" &&
        n.consequent?.value === "+" &&
        n.alternate?.value === "",
    ),
    "original positive prefix",
  );
  assert.equal(
    findNodes(
      original,
      (n) =>
        n.type === "AssignmentExpression" &&
        n.left?.name === "e" &&
        member(n.right, "U", "pnlUsd"),
    ).length,
    1,
    "actual local prefix value derives from supplied pnlUsd",
  );
  const nativeText = await readFile(path.join(appRoot, PAGE), "utf8"),
    native = nativeRow(nativeText);
  const usd = exactlyOne(
    findNodes(
      parseNative(nativeText),
      (n) => n.type === "VariableDeclarator" && n.id?.name === "usd",
    ),
    "existing native formatter",
  );
  assert.equal(
    sha256(nativeText.slice(usd.start, usd.end)),
    "1e741bc3b45320af763e6d402c5d811359c4cd1e4d398c128d6a55fb7f127fe2",
    "existing native formatter changed",
  );
  const position = exactlyOne(
    findNodes(
      native,
      (n) =>
        jsx(n, "span") && attributeSafe(n, "className") === "ranking-position",
    ),
    "actual rank span",
  );
  assert.deepEqual(
    clean(exactlyOne(exprChildren(position), "rank child")),
    clean(rank, { U: expression("entry") }),
    "rank decision changed",
  );
  const metric = exactlyOne(
    findNodes(
      native,
      (n) =>
        jsx(n, "span") && attributeSafe(n, "className") === "ranking-metric",
    ),
    "actual PnL container",
  );
  const strong = exactlyOne(
    metric.children.filter((n) => jsx(n, "strong")),
    "actual PnL strong",
  );
  assert.deepEqual(
    clean(attribute(strong, "className").expression),
    clean(
      tone,
      { U: expression("entry") },
      {
        "text-text-primary": expression("undefined"),
        "text-gain": expression('"positive"'),
        "text-loss": expression('"negative"'),
      },
    ),
    "tone decision changed",
  );
  const children = exprChildren(strong);
  assert.equal(
    children.length,
    2,
    "only original sign and existing native amount",
  );
  assert.deepEqual(
    clean(children[0]),
    clean(sign, { e: expression("entry.pnlUsd") }),
    "positive prefix changed",
  );
  assert.deepEqual(
    clean(children[1]),
    clean(expression("usd.format(entry.pnlUsd)")),
    "native Intl policy changed",
  );
  assert.deepEqual(
    clean(attribute(position, "aria-label").expression),
    clean(expression('entry.rank > 0 ? `Rank ${entry.rank}` : "Not ranked"')),
    "accessible unranked label changed",
  );
  const baselineText = await readFile(
      path.join(appRoot, PACKAGE, "reference/native-row.tsx"),
      "utf8",
    ),
    baseline = nativeRow(baselineText);
  assert.equal(
    sha256(baselineText),
    "357fa51a7bb863c99d3cbbf64fade3c30dbcc6148ac3528162fc1c7def625176",
    "exact baseline excerpt changed",
  );
  // Bound the existing row facts used by this correction without freezing
  // independent additive UI (for example the separately qualified prize badge).
  for (const property of ["realizedPnlUsd", "unrealizedPnlUsd"]) {
    const matching = (node) =>
      findNodes(
        node,
        (n) =>
          n.type === "CallExpression" &&
          n.callee?.type === "MemberExpression" &&
          n.callee.object?.name === "usd" &&
          n.callee.property?.name === "format" &&
          member(n.arguments[0], "entry", property),
      );
    assert.deepEqual(
      clean(exactlyOne(matching(native), "actual " + property)),
      clean(exactlyOne(matching(baseline), "baseline " + property)),
      "existing fact formatting changed",
    );
  }
  const rowKey = exactlyOne(
    findNodes(native, (n) => jsx(n, "li")),
    "native keyed row",
  );
  assert.deepEqual(
    clean(attribute(rowKey, "key").expression),
    clean(expression("entry.entryId")),
    "row key changed",
  );
  const dtoRows = corpus.index.modules.filter((r) => r.ids.includes(139209));
  assert.deepEqual(
    dtoRows.map((r) => r.sha256),
    ["8d4ffb7afbfae1b99df53cf4d8421f1fb6f85c290468471f2e4f71f58358ed9b"],
  );
  const dto = await corpus.factory(139209, {
    source: dtoRows[0].origins[0].source,
  });
  const rankContract = exactlyOne(
    findNodes(
      dto.node,
      (n) =>
        n.type === "StringLiteral" &&
        n.value.startsWith("1-based ordinal rank"),
    ),
    "original rank contract",
  );
  const struck = exactlyOne(
    findNodes(
      dto.node,
      (n) =>
        n.type === "StringLiteral" &&
        n.value.startsWith("Disqualified for this competition"),
    ),
    "original struck boundary",
  );
  const origins = [];
  for (const [selected, id] of [
    ...rows.map((r) => [r, 590407]),
    ...dtoRows.map((r) => [r, 139209]),
  ]) {
    for (const origin of selected.origins) {
      const actual = await corpus.factory(id, { source: origin.source });
      origins.push(actual.provenance);
    }
  }
  return {
    schemaVersion: 1,
    base: "b08fd908203a76d84c8dd68b60310582aa2c4fba",
    anchors: corpus.anchors,
    source: [
      f.witness(
        original,
        "complete original X context; reused not re-recovered",
      ),
      f.witness(rank, "rank-positive value or unranked dash"),
      f.witness(tone, "zero-neutral / positive-gain / negative-loss"),
      f.witness(sign, "positive-only prefix bound to supplied pnlUsd"),
      dto.witness(rankContract, "rank0 means unranked"),
      dto.witness(
        struck,
        "struck entries excluded from ranked arrays; own/detail contexts remain",
      ),
    ],
    origins,
    baseline: {
      gitCommit: "b08fd908203a76d84c8dd68b60310582aa2c4fba",
      file: PAGE,
      gitBlob: "e7dd4d0f92421d6869ad83d8322ba32328d9bd34",
      fileSha256:
        "02310d1e8050387ca314da56dc6d560a31c847d99ada6ac62d2def335f542c48",
      functionUtf16: [11453, 12957],
      functionSha256:
        "c9f5a9fce9cf82b82bc8a42ba86f92f49bc08db8d4de87292b68645c69571e8d",
    },
    local: {
      page: PAGE,
      rowSha256: sha256(nativeText.slice(native.start, native.end)),
      baselineRowSha256: sha256(baselineText),
      accessibleLabel:
        "Native English Not ranked; no cause/eligibility inferred",
      colors: {
        "text-text-primary": "inherit existing native primary text",
        "text-gain": "existing positive class",
        "text-loss": "existing negative class",
      },
      amount:
        "Existing usd.format(entry.pnlUsd), unchanged Intl/ranking/API behavior",
    },
    limits: [
      "This adapts three proven display decisions, not the full original row/providers",
      "Rank0 fixture tests admission/display only, not a claim original ranked arrays include unranked/struck entries",
      "Negative-zero Intl amount remains unchanged; source equality makes its tone neutral",
      "No unaccepted1296/1315/1380 dependency, server ranking, payout, eligibility or private backend claim",
    ],
  };
}
function attributeSafe(n, name) {
  return n.openingElement.attributes.find(
    (a) => a.type === "JSXAttribute" && a.name.name === name,
  )?.value?.value;
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const contract = await verifyCompetitionEntryPresentation(),
    target = path.join(APP, PACKAGE, "contract.json");
  const text = JSON.stringify(contract, null, 2) + "\n";
  if (process.argv.includes("--check"))
    assert.equal(
      await readFile(target, "utf8"),
      text,
      "source receipt changed",
    );
  else await writeFile(target, text);
  console.log(
    "Verified original rank/PnL display decisions and actual native row; no ranking/Intl/provider equivalence claim",
  );
}
