import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "@babel/parser";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  member,
  objectProperty,
  sha256,
} from "./original-contracts/source.mjs";
import { buildPnlLeaderboardClient } from "./original-pnl-leaderboard-client.mjs";
const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const PAGE =
  "packages/frontend/src/app/leaderboard/leaderboard-client.tsx";
const DIR = "reconstruction/trader-selected-measure";
const ast = (s) =>
  parse(s, { sourceType: "module", plugins: ["typescript", "jsx"] });
function clean(n, ids = {}) {
  if (Array.isArray(n)) return n.map((x) => clean(x, ids));
  if (!n || typeof n !== "object") return n;
  return Object.fromEntries(
    Object.entries(n)
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
      .map(([k, v]) => [
        k,
        k === "name" && n.type === "Identifier" && ids[v]
          ? ids[v]
          : clean(v, ids),
      ]),
  );
}
const expr = (s) => ast("(" + s + ")").program.body[0].expression;
const tail = (n) =>
  n.type === "SequenceExpression" ? n.expressions.at(-1) : n;
const call = (n, o, p) =>
  n.type === "CallExpression" && member(tail(n.callee), o, p);
const jsx = (n, name) =>
  n.type === "JSXElement" &&
  n.openingElement.name.type === "JSXIdentifier" &&
  n.openingElement.name.name === name;
const attr = (n, name) =>
  exactlyOne(
    n.openingElement.attributes.filter(
      (a) => a.type === "JSXAttribute" && a.name.name === name,
    ),
    "actual " + name,
  ).value;
export function traderRows(text) {
  return exactlyOne(
    findNodes(
      ast(text),
      (n) => n.type === "FunctionDeclaration" && n.id?.name === "TraderRows",
    ),
    "complete actual native TraderRows",
  );
}
export async function verifyTraderSelectedMeasure(appRoot = APP) {
  const prerequisite = await buildPnlLeaderboardClient(appRoot),
    corpus = await openCorpus(appRoot);
  const client = await corpus.factory(416287, {
    source: prerequisite.contract.factory.source,
  });
  const registration = exactlyOne(
    findNodes(
      client.node,
      (n) =>
        n.type === "CallExpression" &&
        member(n.callee, client.runtime, "s") &&
        n.arguments[1]?.value === 416287,
    ),
    "actual selector registration",
  );
  const elements = registration.arguments[0].elements;
  let score;
  for (let i = 0; i < elements.length; i += 3)
    if (elements[i].value === "n") score = elements[i + 2];
  assert.equal(score.type, "ArrowFunctionExpression");
  const witnesses = [
    client.witness(
      score,
      "complete accepted raw selected-measure selector; reused not new recovery",
    ),
  ];
  const consumers = [];
  for (const origin of prerequisite.contract.consumers) {
    const f = await corpus.factory(996005, { source: origin.source });
    const imported = (id) =>
      exactlyOne(
        findNodes(
          f.node,
          (n) =>
            n.type === "VariableDeclarator" &&
            n.init?.type === "CallExpression" &&
            member(n.init.callee, f.runtime, "i") &&
            n.init.arguments[0]?.value === id,
        ),
        "actual import " + id,
      ).id.name;
    const scoreAlias = imported(416287),
      queryAlias = imported(864024),
      formatAlias = imported(540805);
    const selected = exactlyOne(
      findNodes(f.node, (n) => call(n, scoreAlias, "n")),
      "actual selected score call",
    );
    const row = exactlyOne(
      findNodes(
        f.node,
        (n) =>
          n.type === "VariableDeclarator" &&
          n.init?.type === "ArrowFunctionExpression" &&
          findNodes(n.init, (k) => k === selected).length === 1,
      ),
      "complete actual original row consumer",
    );
    const bindings = exactlyOne(
      findNodes(
        row,
        (n) =>
          n.type === "VariableDeclarator" &&
          n.id?.type === "ObjectPattern" &&
          n.id.properties.some((p) => p.key?.name === "entry") &&
          n.id.properties.some((p) => p.key?.name === "sort"),
      ),
      "actual entry/sort row binding",
    ).id;
    const prop = (name) =>
      bindings.properties.find((p) => p.key?.name === name).value.name;
    assert.deepEqual(
      selected.arguments.map((n) => n.name),
      [prop("entry"), prop("sort")],
    );
    const value = exactlyOne(
      findNodes(
        row,
        (n) => n.type === "VariableDeclarator" && n.init === selected,
      ),
      "used selected value",
    ).id.name;
    const formatted = exactlyOne(
      findNodes(
        row,
        (n) => call(n, formatAlias, "u") && n.arguments[0]?.name === value,
      ),
      "actual selected value formatter",
    );
    const colored = exactlyOne(
      findNodes(
        row,
        (n) => call(n, formatAlias, "k") && n.arguments[0]?.name === value,
      ),
      "actual selected value tone",
    );
    const query = exactlyOne(
      findNodes(f.node, (n) => call(n, queryAlias, "f")),
      "actual board query",
    );
    const options = exactlyOne(
      findNodes(
        f.node,
        (n) =>
          n.type === "AssignmentExpression" &&
          n.left?.name === query.arguments[0]?.name &&
          n.right?.type === "ObjectExpression" &&
          n.right.properties.some((p) => p.key?.name === "period") &&
          n.right.properties.some((p) => p.key?.name === "sort"),
      ),
      "actual board query options",
    ).right;
    const sort = objectProperty(options, "sort").name;
    const rowCall = exactlyOne(
      findNodes(
        f.node,
        (n) =>
          n.type === "CallExpression" &&
          n.arguments[0]?.type === "Identifier" &&
          n.arguments[0].name === row.id.name &&
          n.arguments[1]?.type === "ObjectExpression",
      ),
      "actual board row call",
    );
    assert.equal(
      objectProperty(rowCall.arguments[1], "sort").name,
      sort,
      "query and row must share selected sort",
    );
    const evidence = [
      f.witness(row, "complete original row consumer context"),
      f.witness(
        selected,
        "supplied row and selected sort choose displayed value",
      ),
      f.witness(formatted, "selected value reaches original formatter"),
      f.witness(colored, "selected value reaches original tone"),
      f.witness(query, "actual board query consumer"),
      f.witness(options, "selected query arguments"),
      f.witness(rowCall, "same selected sort reaches real row"),
    ];
    witnesses.push(...evidence);
    consumers.push(f.provenance);
  }
  const text = await readFile(path.join(appRoot, PAGE), "utf8"),
    native = ast(text),
    row = traderRows(text);
  const value = exactlyOne(
    findNodes(
      row,
      (n) => n.type === "VariableDeclarator" && n.id?.name === "value",
    ),
    "native used measure",
  );
  assert.deepEqual(
    clean(value.init),
    clean(score.body, {
      [score.params[0].name]: "entry",
      [score.params[1].name]: "sort",
    }),
    "native raw measure changed source selection",
  );
  const formatted = exactlyOne(
    findNodes(
      row,
      (n) => call(n, "usd", "format") && n.arguments[0]?.name === "value",
    ),
    "actual native selected currency call",
  );
  const metric = exactlyOne(
    findNodes(
      row,
      (n) =>
        jsx(n, "span") &&
        n.openingElement.attributes.some(
          (a) =>
            a.name?.name === "className" && a.value?.value === "ranking-metric",
        ),
    ),
    "native metric",
  );
  const strong = exactlyOne(
    metric.children.filter((n) => jsx(n, "strong")),
    "native metric value",
  );
  assert.deepEqual(
    clean(attr(strong, "className").expression),
    clean(expr('value >= 0 ? "positive" : "negative"')),
    "existing native tone must consume selected value",
  );
  assert.ok(
    findNodes(strong, (n) => n === formatted).length === 1,
    "selected formatter must render",
  );
  const caption = exactlyOne(
    metric.children.filter((n) => jsx(n, "small")),
    "native metric caption",
  );
  const captionExpr = exactlyOne(
    caption.children.filter((n) => n.type === "JSXExpressionContainer"),
    "native caption expression",
  ).expression;
  assert.deepEqual(
    clean(captionExpr),
    clean(
      expr(
        'sort === "combined" ? `${percent.format(entry.pnlPercent / 100)} combined PnL` : `${sort[0].toUpperCase()}${sort.slice(1)} PnL`',
      ),
    ),
    "caption must label selected measure without inventing partial percentage",
  );
  const usage = exactlyOne(
    findNodes(native, (n) => jsx(n, "TraderRows")),
    "actual native row consumer",
  );
  assert.equal(
    attr(usage, "sort").expression.name,
    "traderSort",
    "native row must receive selected request sort",
  );
  assert.equal(attr(usage, "entries").expression.name, "entries");
  const apiSort = exactlyOne(
    findNodes(
      native,
      (n) =>
        n.type === "CallExpression" &&
        member(n.callee, "parameters", "set") &&
        n.arguments[0]?.value === "sort",
    ),
    "actual request sort",
  );
  assert.equal(apiSort.arguments[1].name, "traderSort");
  const control = exactlyOne(
    findNodes(
      native,
      (n) =>
        jsx(n, "select") &&
        n.openingElement.attributes.some(
          (a) =>
            a.name?.name === "aria-label" && a.value?.value === "Trader sort",
        ),
    ),
    "actual sort control",
  );
  assert.equal(attr(control, "value").expression.name, "traderSort");
  const usd = exactlyOne(
    findNodes(
      native,
      (n) => n.type === "VariableDeclarator" && n.id?.name === "usd",
    ),
    "existing native Intl policy",
  );
  assert.equal(
    sha256(text.slice(usd.start, usd.end)),
    "1e741bc3b45320af763e6d402c5d811359c4cd1e4d398c128d6a55fb7f127fe2",
    "native Intl policy changed",
  );
  const reference = await readFile(
    path.join(appRoot, DIR, "reference/native-row.tsx"),
  );
  assert.equal(
    sha256(reference),
    "9a90936867e39164461dff9acec26359a1290fbda0c7e04b772d78c5861dd796",
    "exact native baseline excerpt changed",
  );
  const paths = [
    "packages/frontend/src/app/api/leaderboard/route.ts",
    "packages/frontend/src/app/api/leaderboard/upstream.ts",
    "packages/frontend/src/app/leaderboard/types.ts",
  ];
  const unchanged = {};
  for (const p of paths)
    unchanged[p] = sha256(await readFile(path.join(appRoot, p)));
  return {
    schemaVersion: 1,
    base: "2c8a7900f240c8a50cccc2b4d263bdbd32a68924",
    scope:
      "Actual native selected-sort request-to-displayed-value correction, retaining native formatter/tone policy; no backend ranking/auth changes",
    prerequisite: {
      accepted: "829",
      producer: "scripts/original-pnl-leaderboard-client.mjs",
      sha256: sha256(
        await readFile(
          path.join(appRoot, "scripts/original-pnl-leaderboard-client.mjs"),
        ),
      ),
      source: prerequisite.contract.source,
      credit:
        "Source request/query/selector discoveries reused without recovery-count claim",
    },
    witnesses,
    consumers,
    baseline: {
      gitCommit: "2c8a7900f240c8a50cccc2b4d263bdbd32a68924",
      file: PAGE,
      gitBlob: "e7dd4d0f92421d6869ad83d8322ba32328d9bd34",
      fileSha256:
        "02310d1e8050387ca314da56dc6d560a31c847d99ada6ac62d2def335f542c48",
      functionUtf16: [7157, 8556],
      functionSha256:
        "1506ff73a9a478e016c0cf792540d18a7e4b11a63056eb42808996c4cd47ff17",
    },
    native: {
      page: PAGE,
      rowSha256: sha256(text.slice(row.start, row.end)),
      sourceSortVariable: "traderSort",
      label:
        "Existing combined percentage only for combined; partial measures get existing native sort labels, no new percentage calculation",
      formatter:
        "Existing native USD Intl unchanged; original540805 formatter/neutral-band parity not claimed",
    },
    unchanged,
    limits: [
      "No original ReactQuery/cache/wallet/provider parity from local tests",
      "No native API compatibility/rank/PnL calculation/security claim; actual local backend is synthetic and unqualified",
      "Existing server/operator-key transport and backend rules remain outside this display correction",
    ],
  };
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const result = await verifyTraderSelectedMeasure(),
    file = path.join(APP, DIR, "contract.json"),
    text = JSON.stringify(result, null, 2) + "\n";
  if (process.argv.includes("--check"))
    assert.equal(await readFile(file, "utf8"), text);
  else await writeFile(file, text);
  console.log(
    "Verified complete original selected-measure closure and actual native request/control/row bindings; native format policy retained",
  );
}
