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
  sha256,
} from "./original-contracts/source.mjs";
export const APP_ROOT = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    "..",
  ),
  DIRECTORY = "reconstruction/competition-prizes",
  COMPONENT =
    "packages/frontend/src/components/leaderboard/original-prizes.tsx",
  FORMATS =
    "packages/frontend/src/components/leaderboard/original-prize-formats.mjs";
const SHARED =
    "ef7acaad8c20e23d6f9821dc683cfc0dc66cc3eb1b14642674a9007c9c064205",
  PINS = {
    590407: [
      "3f494070c58a6d7f0f70279887ef648107935b765fe849de3e9ec100cec45dda",
    ],
    706615: [
      "e606b2e7f5ab2bfd5da0abb70db2de0560f01d4d131d156719d8623614219e74",
    ],
    139209: [
      "8d4ffb7afbfae1b99df53cf4d8421f1fb6f85c290468471f2e4f71f58358ed9b",
    ],
    179537: [
      "44627d7c92a6d1701f6dfa39d0d6a883e49091468c77b5c53b59e287c60033c6",
      "9bf80842633385d9f509ffadb3aff4690be9592934d3679b017d690083f76992",
    ],
    36489: ["74dab3f8ec1cc9a308907b35744d1dd5da64e505faceb68dc65174634fa56126"],
    592209: [
      "6b3fe2082dbaa30d9d803777d25ef02aa53ccc736b312980dec097206324c790",
    ],
    890088: [
      "b6933f856a7fe6205483d9adca13b97117fed3fc3822f1383ed3ba99e512040b",
      "f29f27e66af25973af60575b0ffea4e03a9fc939855c0ff7d4a8f3c02d448e09",
    ],
  };
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
      .map(([key, item]) => [key, canonical(item)]),
  );
}
function exported(factory, id, name) {
  const result = [];
  for (const call of findNodes(
    factory.node,
    (node) =>
      node.type === "CallExpression" &&
      member(node.callee, factory.runtime, "s") &&
      (node.arguments[1]?.value === id ||
        (!node.arguments[1] && factory.ids.length === 1)),
  )) {
    const values = call.arguments[0].elements;
    for (let i = 0; i < values.length; i += 3)
      if (values[i].value === name) result.push(values[i + 2]);
  }
  return exactlyOne(result, `actual export ${id}.${name}`);
}
const declarations = (factory) =>
  factory.node.body.body
    .filter((node) => node.type === "VariableDeclaration")
    .flatMap((node) => node.declarations);
export async function buildCompetitionPrizes(appRoot = APP_ROOT) {
  assert.equal(
    sha256(
      await readFile(
        path.join(appRoot, "scripts/original-contracts/source.mjs"),
      ),
    ),
    SHARED,
  );
  const corpus = await openCorpus(appRoot),
    factories = new Map(),
    witnesses = [],
    outputs = new Map();
  for (const [id, hashes] of Object.entries(PINS)) {
    const rows = corpus.index.modules.filter((row) =>
      row.ids.includes(Number(id)),
    );
    assert.deepEqual(
      rows.map((row) => row.sha256).sort(),
      hashes,
      `unreviewed variants ${id}`,
    );
    const found = [];
    for (const row of rows)
      found.push(
        await corpus.factory(Number(id), { source: row.origins[0].source }),
      );
    factories.set(Number(id), found);
  }
  const one = (id) =>
      exactlyOne(factories.get(id), `single source context ${id}`),
    get = (factory, name) =>
      exactlyOne(
        declarations(factory).filter((node) => node.id.name === name),
        `actual declarator ${name}`,
      ),
    add = (factory, node, label) => {
      witnesses.push(factory.witness(node, label));
      return node;
    };
  const page = one(590407),
    shared = one(706615),
    routes = one(139209),
    locale = one(592209),
    ranks = one(36489);
  const tier = add(
      page,
      get(page, "D").init,
      "complete original prize-tier DISPLAY component",
    ),
    heading = add(
      page,
      get(page, "T").init,
      "complete original section heading",
    );
  const row = exactlyOne(
    page.node.body.body.filter(
      (node) => node.type === "FunctionDeclaration" && node.id.name === "X",
    ),
    "actual ranked row",
  );
  const badge = add(
    page,
    exactlyOne(
      findNodes(
        row,
        (node) =>
          node.type === "ConditionalExpression" &&
          node.test?.name === "S" &&
          findNodes(
            node,
            (node) =>
              node.type === "StringLiteral" && node.value === "cup-entry-prize",
          ).length === 1,
      ),
      "actual optional rank-prize badge",
    ),
    "complete actual conditional rank-prize badge",
  );
  const match = add(
      shared,
      exported(shared, 706615, "J"),
      "complete original first-covering-rank selector",
    ),
    amount = add(
      shared,
      exported(shared, 706615, "k"),
      "complete original display-string currency formatter",
    ),
    numeric = add(
      shared,
      get(shared, "r"),
      "actual numeric display-string regex",
    );
  const colors = factories.get(179537).map((factory) => ({
    factory,
    node: add(
      factory,
      exported(factory, 179537, "S"),
      "actual rank palette; selected literal identical across physical variants",
    ),
  }));
  for (const entry of colors)
    assert.deepEqual(
      canonical(entry.node),
      canonical(colors[0].node),
      "rank palette variants diverge; no arbitrary winner permitted",
    );
  const numberVariants = [];
  for (const numbers of factories.get(890088)) {
    const value = exported(numbers, 890088, "R");
    add(numbers, value, "actual NumberFormat export");
    const format = get(numbers, value.name);
    const call = format.init.body;
    assert.equal(call.type, "CallExpression");
    const names = [
      call.arguments[0].name,
      call.arguments[1].callee.name,
      call.callee.name,
      value.name,
    ];
    assert.ok(names.every((name) => typeof name === "string"));
    const state = names.map((name) =>
      add(
        numbers,
        get(numbers, name),
        `complete used number-format state/helper ${name}`,
      ),
    );
    const name = `packages/frontend/src/components/leaderboard/prize-number-variants/${numbers.provenance.sha256.slice(0, 12)}.mjs`;
    outputs.set(
      name,
      await prettier.format(
        `// One explicitly selected original NumberFormat source context.\nexport function createNumberFormatter({Intl}){let ${state.map((node) => numbers.text(node)).join(",")};return ${value.name};}`,
        { parser: "babel" },
      ),
    );
    numberVariants.push({
      sha256: numbers.provenance.sha256,
      path: name,
      source: numbers.provenance.source,
    });
  }
  const rankFormat = add(
    ranks,
    exported(ranks, 36489, "Z"),
    "complete used locale rank-number formatter",
  );
  const localeState = ["t", "r"].map((name) =>
      add(locale, get(locale, name), `complete used locale state ${name}`),
    ),
    localeFn = add(
      locale,
      exported(locale, 592209, "v"),
      "complete original locale canonicalizer",
    );
  outputs.set(
    FORMATS,
    await prettier.format(
      `// Used source-bound formatter/locale helpers only; no captured runtime execution.\n${numberVariants.map((row, index) => `import {createNumberFormatter as v${index}} from './prize-number-variants/${row.sha256.slice(0, 12)}.mjs';`).join("\n")}\nexport {c as useMemoCache} from 'react/compiler-runtime';\nconst numberVariants=new Map([${numberVariants.map((row, index) => `[${JSON.stringify(row.sha256)},v${index}]`).join(",")}]);\nexport const prizeNumberVariants=Object.freeze(${JSON.stringify(numberVariants)});\nexport function createPrizeFormats({numberVariant,Intl}){const createNumberFormatter=numberVariants.get(numberVariant);if(!createNumberFormatter)throw new TypeError('Explicit reviewed prize NumberFormat source variant required');const numberFormatter=createNumberFormatter({Intl});const canonicalLocale=(()=>{let ${localeState.map((node) => locale.text(node)).join(",")};return ${locale.text(localeFn)};})();const formatRank=(()=>{const t={R:numberFormatter};return ${ranks.text(rankFormat)};})();const formatAmount=(()=>{const t={R:numberFormatter};let ${shared.text(numeric)};return ${shared.text(amount)};})();return {canonicalLocale,formatRank,formatAmount,findPrize:${shared.text(match)}};}`,
      { parser: "babel" },
    ),
  );
  // Type annotations are OUTSIDE the complete original component/expression bodies.
  outputs.set(
    COMPONENT,
    await prettier.format(
      `"use client";\nimport type {ComponentType} from 'react';\nexport type Prize={rankFrom:number;rankTo:number;amount:string};\nexport function createPrizeDisplay({jsx,jsxs,useMemoCache,useTranslation,classNames,canonicalLocale,formatRank,formatAmount}: {jsx:typeof import('react/jsx-runtime').jsx;jsxs:typeof import('react/jsx-runtime').jsxs;useMemoCache:(size:number)=>any[];useTranslation:()=>{t:(key:string,values?:Record<string,string|number>)=>string;i18n:{language:string}};classNames:(...parts:Array<string|undefined|false>)=>string;canonicalLocale:(language:string)=>string|null;formatRank:(value:number,locale:string)=>string;formatAmount:(options:{text:string;locale:string})=>string}){const a={jsx,jsxs},s={c:useMemoCache},l={f:useTranslation},A={c:classNames},R={v:canonicalLocale},E={Z:formatRank},$={k:formatAmount},n:{S:Record<number,string|undefined>}={S:${colors[0].factory.text(colors[0].node)}};const Tier:ComponentType<{prize:Prize}>=${page.text(tier)};const Heading:ComponentType<{title:string;isCardTop?:boolean}>=${page.text(heading)};const PrizeBadge:ComponentType<{prize:Prize|null}>=({prize:S})=>${page.text(badge)};return {Tier,Heading,PrizeBadge};}`,
      { parser: "babel-ts" },
    ),
  );
  const body = exactlyOne(
    findNodes(
      get(routes, "b").init,
      (node) => node.type === "ObjectProperty" && node.key.name === "prizes",
    ),
    "actual DTO prizes",
  );
  add(
    routes,
    body,
    "documented served display tiers; no payout/scoring calculation",
  );
  const pageFunction = exported(page, 590407, "LeaderboardPage");
  assert.ok(pageFunction);
  const tierCalls = findNodes(
    page.node,
    (node) =>
      node.type === "CallExpression" &&
      member(
        node.callee.type === "SequenceExpression"
          ? node.callee.expressions.at(-1)
          : node.callee,
        "a",
        "jsx",
      ) &&
      node.arguments[0]?.name === "D",
  );
  assert.ok(tierCalls.length);
  for (const node of tierCalls)
    add(page, node, "actual original tier-display caller");
  const originalPlan = exactlyOne(
    findNodes(
      page.node,
      (node) =>
        node.type === "ArrowFunctionExpression" &&
        node.params[0]?.type === "ObjectPattern" &&
        node.params[0].properties.map((p) => p.key.name).join(",") ===
          "competition,detail" &&
        findNodes(
          node,
          (node) =>
            node.type === "StringLiteral" && node.value === "prize_line",
        ).length === 1,
    ),
    "actual source row planner",
  );
  add(
    page,
    originalPlan,
    "actual caller chooses tier rows only without ranked entries; rank badge selector used with served rank",
  );
  const selected = corpus.index.modules
    .filter((row) => row.ids.some((id) => Object.hasOwn(PINS, id)))
    .sort((a, b) => a.sha256.localeCompare(b.sha256));
  const contract = {
    schemaVersion: 1,
    source: {
      reviewBase: "812a9a89efab0d85c6e6d47fef7f2429ec39783b",
      manifestSha256: corpus.anchors.manifestSha256,
      sharedSourceSha256: SHARED,
      selectedIndexEntries: selected,
      selectedCompleteEntriesSha256: sha256(JSON.stringify(selected)),
    },
    relatedWork: {
      pr: 864,
      head: "18689c86aa592b7a15819c90ae16225912c5ca46",
      scope:
        "Prior projection/rules/English-label work belongs to its accepted prior contribution; not shipped or qualified here. Earlier706615 tracing is credited, with no repeated factory-count claim.",
    },
    outputs: Object.fromEntries(
      [...outputs].map(([name, text]) => [name, sha256(text)]),
    ),
    witnesses: witnesses.sort(
      (a, b) => a.source.localeCompare(b.source) || a.utf16[0] - b.utf16[0],
    ),
    behavior: {
      tiers:
        "Original complete D component and heading; first-covering-rank J; exact original optional row badge.",
      projection:
        "Caller supplies already-validated captured-shaped Prize props. This unit adds no parser/projection or producer-guard qualification.",
      formatting:
        "Original numeric-string regex/currency formatting, locale canonicalization and bounded NumberFormat cache. Textual amounts remain text. Rank badge retains raw amount as original X.",
      palette:
        "Selected literal is identical in every reviewed179537 variant; no whole-factory equality or active-winner claim.",
      integration:
        "Actual captured caller chooses tier rows without ranked entries; this display-only unit does not wire or qualify the maintained page. RankPrize uses original J with caller-supplied rank.",
    },
    limits: [
      "All original captures/factories/schemas parsed, never executed.",
      "Translation remains an explicitly supplied provider, with synthetic labels only in tests. No English-label recovery or tenant identity claim. Class joining is a bounded local capability.",
      "No viewer selection, server rank/price/scoring/payout/auth semantics or production requests.",
      "Maintained page/API/projection files are unchanged. Future native wiring requires a separately qualified provider, such as PR864; no864 guard or rules/copy work is included.",
    ],
  };
  return { outputs, contract };
}
export async function verifyCompetitionPrizes(appRoot = APP_ROOT) {
  const { outputs, contract } = await buildCompetitionPrizes(appRoot);
  for (const [name, expected] of outputs) {
    const actual = await readFile(path.join(appRoot, name), "utf8"),
      plugins = name.endsWith(".tsx") ? ["typescript", "jsx"] : [];
    assert.deepEqual(
      canonical(parse(actual, { sourceType: "module", plugins })),
      canonical(parse(expected, { sourceType: "module", plugins })),
      `maintained AST differs ${name}`,
    );
    assert.equal(actual, expected, `maintained bytes differ ${name}`);
  }
  assert.equal(
    await readFile(path.join(appRoot, DIRECTORY, "contract.json"), "utf8"),
    JSON.stringify(contract, null, 2) + "\n",
    "source contract differs",
  );
  return contract;
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
    if (mode === "--write") {
      const { outputs, contract } = await buildCompetitionPrizes();
      for (const [name, text] of outputs) {
        const file = path.join(APP_ROOT, name);
        await mkdir(path.dirname(file), { recursive: true });
        await writeFile(file, text);
      }
      await writeFile(
        path.join(APP_ROOT, DIRECTORY, "contract.json"),
        JSON.stringify(contract, null, 2) + "\n",
      );
    } else await verifyCompetitionPrizes();
    console.log(
      "Complete original competition prize display/formatters verified without captured runtime execution.",
    );
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
