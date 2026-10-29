import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "@babel/parser";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  member,
  sha256,
} from "./original-contracts/source.mjs";
import { verifyCompetitionPrizes } from "./original-competition-prizes.mjs";
const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DIR = "reconstruction/competition-prize-page";
const PAGE = "packages/frontend/src/app/leaderboard/leaderboard-client.tsx";
const BRIDGE = "packages/frontend/src/app/leaderboard/competition-prizes.tsx";
const MODEL =
  "packages/frontend/src/app/leaderboard/competition-rules-model.ts";
function canonical(x) {
  if (Array.isArray(x)) return x.map(canonical);
  if (!x || typeof x !== "object") return x;
  return Object.fromEntries(
    Object.entries(x)
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
      .map(([k, v]) => [k, canonical(v)]),
  );
}
const ast = (text) =>
  parse(text, { sourceType: "module", plugins: ["typescript", "jsx"] });
const jsx = (node, name) =>
  node.type === "JSXElement" &&
  node.openingElement.name.type === "JSXIdentifier" &&
  node.openingElement.name.name === name;
const attr = (node, key) =>
  exactlyOne(
    node.openingElement.attributes.filter(
      (a) => a.type === "JSXAttribute" && a.name.name === key,
    ),
    "actual prop " + key,
  ).value.expression;
const expr = (text) =>
  parse("(" + text + ")", { plugins: ["typescript", "jsx"] }).program.body[0]
    .expression;
export async function verifyCompetitionPrizePage(appRoot = APP) {
  await verifyCompetitionPrizes(appRoot);
  const corpus = await openCorpus(appRoot),
    rows = corpus.index.modules.filter((r) => r.ids.includes(706615));
  assert.deepEqual(
    rows.map((r) => r.sha256),
    ["e606b2e7f5ab2bfd5da0abb70db2de0560f01d4d131d156719d8623614219e74"],
  );
  const utility = await corpus.factory(706615, {
      source: rows[0].origins[0].source,
    }),
    exported = [];
  for (const call of findNodes(
    utility.node,
    (n) =>
      n.type === "CallExpression" &&
      member(n.callee, utility.runtime, "s") &&
      (n.arguments[1]?.value === 706615 ||
        (!n.arguments[1] && utility.ids.length === 1)),
  )) {
    const a = call.arguments[0].elements;
    for (let i = 0; i < a.length; i += 3)
      if (a[i].value === "J") exported.push(a[i + 2]);
  }
  const original = exactlyOne(exported, "actual 706615.J"),
    bridgeText = await readFile(path.join(appRoot, BRIDGE), "utf8"),
    bridge = ast(bridgeText),
    nativeText = await readFile(path.join(appRoot, PAGE), "utf8"),
    native = ast(nativeText);
  const selector = exactlyOne(
    findNodes(
      bridge,
      (n) => n.type === "VariableDeclarator" && n.id.name === "findPrize",
    ),
    "used native prize selector",
  );
  assert.deepEqual(
    canonical(selector.init),
    canonical(original),
    "native rank-prize selector changed original decisions",
  );
  const use = exactlyOne(
    findNodes(
      bridge,
      (n) => n.type === "CallExpression" && n.callee.name === "findPrize",
    ),
    "actual selector use",
  );
  assert.deepEqual(
    use.arguments.map((a) => a.name),
    ["prizes", "rank"],
  );
  const rowCall = exactlyOne(
    findNodes(native, (n) => jsx(n, "CompetitionEntryRows")),
    "actual page ranked rows",
  );
  assert.deepEqual(
    canonical(attr(rowCall, "prizes")),
    canonical(expr("data.competition.prizes")),
  );
  assert.equal(attr(rowCall, "entries").name, "entries");
  const rowsFunction = exactlyOne(
      findNodes(
        native,
        (n) =>
          n.type === "FunctionDeclaration" &&
          n.id?.name === "CompetitionEntryRows",
      ),
      "ranked row function",
    ),
    badge = exactlyOne(
      findNodes(rowsFunction, (n) => jsx(n, "CompetitionRankPrize")),
      "actual ranked-row prize call",
    );
  assert.equal(attr(badge, "prizes").name, "prizes");
  assert.deepEqual(
    canonical(attr(badge, "rank")),
    canonical(expr("entry.rank")),
  );
  const fallback = exactlyOne(
    findNodes(
      native,
      (n) =>
        n.type === "ConditionalExpression" &&
        jsx(n.consequent, "CompetitionPrizeTiers"),
    ),
    "actual empty-standings prize fallback",
  );
  assert.deepEqual(
    canonical(fallback.test),
    canonical(
      expr("data.entries.length === 0 && data.competition.prizes.length > 0"),
    ),
    "fallback must use raw standings, not filtered results",
  );
  assert.deepEqual(
    canonical(attr(fallback.consequent, "prizes")),
    canonical(expr("data.competition.prizes")),
  );
  const model = ast(await readFile(path.join(appRoot, MODEL), "utf8")),
    baseModel = ast(
      await readFile(
        path.join(appRoot, DIR, "reference/competition-rules-model.ts"),
        "utf8",
      ),
    );
  for (const name of ["amount", "fill"]) {
    const fn = (a) =>
      exactlyOne(
        findNodes(
          a,
          (n) => n.type === "FunctionDeclaration" && n.id?.name === name,
        ),
        name,
      );
    assert.deepEqual(
      canonical(fn(model)),
      canonical(fn(baseModel)),
      "existing native display policy changed " + name,
    );
  }
  const sourceRows = corpus.index.modules.filter((r) => r.ids.includes(590407));
  assert.equal(sourceRows.length, 1);
  const page = await corpus.factory(590407, {
    source: sourceRows[0].origins[0].source,
  });
  const planner = exactlyOne(
    findNodes(
      page.node,
      (n) =>
        n.type === "ArrowFunctionExpression" &&
        n.params[0]?.type === "ObjectPattern" &&
        n.params[0].properties.map((p) => p.key.name).join(",") ===
          "competition,detail" &&
        findNodes(
          n,
          (x) => x.type === "StringLiteral" && x.value === "prize_line",
        ).length === 1,
    ),
    "actual original planner",
  );
  return {
    schemaVersion: 1,
    base: "ef400863f4e476b2eaaab0866c0b1187d8060abc",
    original: [
      utility.witness(original, "accepted complete J selected by actual rank"),
      page.witness(
        planner,
        "actual branch: empty unfiltered standings use supplied prize tiers",
      ),
    ],
    localBindings: {
      page: PAGE,
      bridge: BRIDGE,
      rankedRows: {
        entries: "entries after existing local filtering/paging",
        prizes: "data.competition.prizes",
        rank: "entry.rank",
      },
      emptyGuard:
        "data.entries.length === 0 && data.competition.prizes.length > 0",
    },
    unchangedPolicy: {
      amount: "existing native BigInt formatter",
      labels: "existing captured English prize-only labels",
      originalComponents:
        "accepted #937 D/T/badge bytes unchanged; formatter/translation are explicit native providers",
    },
    scope: [
      "Mounted web detail display, no app/mobile promotion or deep links",
      "No API/projection/ranking/payout/auth policy changes",
      "No original NumberFormat variant selection or full provider/native API parity claim",
    ],
    reference: {
      "leaderboard-client.tsx": sha256(
        await readFile(
          path.join(appRoot, DIR, "reference/leaderboard-client.tsx"),
        ),
      ),
      "competition-rules-model.ts": sha256(
        await readFile(
          path.join(appRoot, DIR, "reference/competition-rules-model.ts"),
        ),
      ),
    },
  };
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  try {
    const [mode, ...rest] = process.argv.slice(2);
    assert.ok(
      !rest.length && ["--write", "--check"].includes(mode),
      "usage: --write | --check",
    );
    const c = await verifyCompetitionPrizePage();
    const target = path.join(APP, DIR, "contract.json");
    if (mode === "--write") {
      await mkdir(path.dirname(target), { recursive: true });
      await writeFile(target, JSON.stringify(c, null, 2) + "\n");
    } else
      assert.equal(
        await readFile(target, "utf8"),
        JSON.stringify(c, null, 2) + "\n",
        "integration source contract differs",
      );
    console.log(
      "Web prize integration: original selector/components, actual page fields and unchanged native precision policy verified.",
    );
  } catch (e) {
    console.error(e.message);
    process.exitCode = 1;
  }
}
