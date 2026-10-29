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
);
export const DIRECTORY = "reconstruction/competition-viewer";
const OUT = "packages/frontend/src/components/leaderboard/viewer/";
const SHARED =
  "49b11417fd4d500d8821c94df6c215b77da2248875f943570f2b9df6c9b35213";
const PINS = {
  590407: ["3f494070c58a6d7f0f70279887ef648107935b765fe849de3e9ec100cec45dda"],
  139209: ["8d4ffb7afbfae1b99df53cf4d8421f1fb6f85c290468471f2e4f71f58358ed9b"],
  90832: ["4338f013e20debf9abf08d64e2fd71df845208712ad7737a91216f3b9c48da90"],
  540805: ["058ef17f92b13d44c2ead869a78a52961abc88fd4814fa72514f5c11c1fc85be"],
  363250: ["e6fea22fefde82715cf2e611ea91240e636eda105ce2d4da95af63753d341e26"],
  745018: ["4cc46a6d51b6a9b0fe8ce9f64d77e130e7961309e881fe14f64efa16fb09f660"],
};
const variables = (f) =>
  f.node.body.body
    .filter((n) => n.type === "VariableDeclaration")
    .flatMap((n) => n.declarations);
const variable = (f, name) =>
  exactlyOne(
    variables(f).filter((n) => n.id.name === name),
    "variable " + name,
  );
const named = (f, name) =>
  exactlyOne(
    f.node.body.body.filter(
      (n) => n.type === "FunctionDeclaration" && n.id.name === name,
    ),
    "function " + name,
  );
function exported(f, id, name) {
  const found = [];
  for (const call of findNodes(
    f.node,
    (n) =>
      n.type === "CallExpression" &&
      member(n.callee, f.runtime, "s") &&
      (n.arguments[1]?.value === id || (!n.arguments[1] && f.ids.length === 1)),
  )) {
    const a = call.arguments[0].elements;
    for (let i = 0; i < a.length; i += 3)
      if (a[i].value === name) found.push(a[i + 2]);
  }
  return exactlyOne(found, "actual export " + id + "." + name);
}
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
export async function buildCompetitionViewer(appRoot = APP_ROOT) {
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
    const rows = corpus.index.modules.filter((r) => r.ids.includes(+id));
    assert.deepEqual(
      rows.map((r) => r.sha256).sort(),
      hashes,
      "unreviewed variants " + id,
    );
    factories.set(
      +id,
      await corpus.factory(+id, { source: rows[0].origins[0].source }),
    );
  }
  const add = (f, n, label) => {
      witnesses.push(f.witness(n, label));
      return f.text(n);
    },
    page = factories.get(590407),
    svg = factories.get(745018),
    dto = factories.get(139209),
    currency = factories.get(90832),
    compact = factories.get(540805),
    price = factories.get(363250);
  for (const [alias, id, meaning] of [
    ["a", 732486, "JSX runtime"],
    ["s", 445242, "compiler cache"],
    ["i", 352386, "React useState"],
    ["l", 398902, "translation hook"],
    ["e4", 363250, "injected SOL-price query hook"],
    ["H", 90832, "supplied currency display"],
    ["q", 745018, "expand/collapse SVGs"],
    ["A", 338319, "bounded class capability"],
    ["Z", 705313, "Avatar port"],
    ["Q", 458310, "Link port"],
    ["C", 146695, "profile href"],
    ["P", 365089, "short wallet"],
    ["G", 69399, "explicit squad variant"],
    ["V", 741084, "explicit image variant"],
    ["W", 897665, "IPFS constant"],
  ]) {
    const d = variable(page, alias);
    assert.ok(member(d.init.callee, page.runtime, "i"));
    assert.equal(d.init.arguments[0].value, id);
    add(
      page,
      d,
      "actual viewer import " + alias + " -> " + id + " (" + meaning + ")",
    );
  }
  const full = {};
  for (const name of ["e9", "e7", "e8", "te"])
    full[name] = add(
      page,
      named(page, name),
      "COMPLETE original " +
        name +
        " " +
        {
          e9: "viewer card",
          e7: "expanded stats with conditional price hook",
          e8: "stat cell",
          te: "toggle updater",
        }[name],
    );
  const stat = variable(page, "e5");
  const statText = add(
    page,
    stat,
    "COMPLETE original near-zero/null stat decision",
  );
  const toneText = add(
    page,
    variable(page, "e6").init,
    "original stat tone map",
  );
  const calls = findNodes(
    page.node,
    (n) =>
      n.type === "CallExpression" &&
      n.callee.type === "SequenceExpression" &&
      member(n.callee.expressions.at(-1), "a", "jsx") &&
      n.arguments[0]?.name === "e9",
  );
  const caller = exactlyOne(calls, "actual viewer-card consumer");
  add(page, caller, "actual competition-board viewer-card invocation");
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
    "complete competition row planner",
  );
  add(
    page,
    planner,
    "complete actual planner: viewer entry comes from detail.viewer.entry; no session inference",
  );
  for (const name of ["h", "m", "g"])
    add(
      dto,
      variable(dto, name),
      "actual documented " +
        {
          h: "shared profile fields",
          m: "complete competition entry DTO",
          g: "viewer entry and eligibility DTO",
        }[name],
    );
  const currencyAlias = exported(currency, 90832, "v");
  assert.equal(currencyAlias.name, "l");
  add(currency, currencyAlias, "actual volume export is alias l");
  add(currency, variable(currency, "l"), "actual volume alias l=t.l");
  assert.ok(member(variable(currency, "l").init, "t", "l"));
  const importCompact = variable(currency, "t");
  assert.ok(member(importCompact.init.callee, currency.runtime, "i"));
  assert.equal(importCompact.init.arguments[0].value, 540805);
  add(currency, importCompact, "actual volume formatter import 540805");
  const declarations = ["t", "n", "r", "i", "o"].map((name) =>
    add(
      compact,
      variable(compact, name),
      "complete used compact-currency closure " + name,
    ),
  );
  const format = add(
    compact,
    exported(compact, 540805, "l"),
    "COMPLETE actually used compact-currency formatter",
  );
  outputs.set(
    OUT + "original-volume.mjs",
    await prettier.format(
      "export function createVolumeFormatter(Intl){let " +
        declarations.join(",") +
        ";return " +
        format +
        ";}",
      { parser: "babel" },
    ),
  );
  add(
    price,
    named(price, "o"),
    "unreconstructed original SOL price query function: provider60326.f({})",
  );
  const priceHook = exported(price, 363250, "f");
  add(
    price,
    priceHook,
    "unreconstructed injected price-hook contract: query defaults and data; no synthetic native query",
  );
  for (const [alias, id] of [
    ["r", 690877],
    ["n", 38279],
    ["i", 60326],
  ]) {
    const v = variable(price, alias);
    assert.ok(member(v.init.callee, price.runtime, "i"));
    assert.equal(v.init.arguments[0].value, id);
    add(
      price,
      v,
      "unreconstructed original price-query dependency " + alias + " -> " + id,
    );
  }
  const wrapper = add(
    svg,
    variable(svg, "r").init,
    "used original SVG wrapper; prior entry-row prerequisite credited",
  );
  const icons = {};
  for (const name of ["cg", "J0"])
    icons[name] = add(
      svg,
      exported(svg, 745018, name),
      "COMPLETE used " + name + " chevron",
    ).replace("e=>", "(e:{className?:string})=>");
  const imports =
    '"use client";import type{ComponentType,ReactNode,CSSProperties}from"react";import type{Entry,AvatarProps}from"../entry/original-entry-row";export type ViewerEntry=Entry&{realizedPnlUsd:number;unrealizedPnlUsd:number;buySpendSol:number};export type ViewerLinkProps={href:string|null;prefetch:false;className:string;children?:ReactNode;"aria-label":string};export type Stat={label:string;value:string;tone:"gain"|"loss"|"neutral"};';
  const caps =
    'jsx:typeof import("react/jsx-runtime").jsx;jsxs:typeof import("react/jsx-runtime").jsxs;React:Pick<typeof import("react"),"createElement"|"useState">;useMemoCache:(size:number)=>any[];useTranslation:()=>{t:(key:string,values?:Record<string,string|number>)=>string};useSolPrice:(options:Record<string,never>)=>{data?:number|null};classNames:(...parts:Array<string|undefined|false>)=>string;Avatar:ComponentType<AvatarProps>;Link:ComponentType<ViewerLinkProps>;profileHref:(value:string)=>string|null;shortWallet:(value:string)=>string;formatPnl:(value:number)=>string;formatVolume:(value:number)=>string;squadHref:(value:{groupId:string;username:string|null})=>string;normalizeImage:(value:string|null)=>string|undefined;ipfsPrefix:string';
  const text =
    imports +
    "export function createViewerCard({jsx,jsxs,React,useMemoCache,useTranslation,useSolPrice,classNames,Avatar,Link,profileHref,shortWallet,formatPnl,formatVolume,squadHref,normalizeImage,ipfsPrefix}:{" +
    caps +
    "}){const a={jsx,jsxs},s={c:useMemoCache},i={useState:React.useState},l={f:useTranslation},A={c:classNames},G={Z:squadHref},C={$:profileHref},P={d:shortWallet},V={f:normalizeImage},Z={f:Avatar},W={f:ipfsPrefix},Q={default:Link},H={w:formatPnl,v:formatVolume},e4={f:useSolPrice};const q=(()=>{const t={default:React};const r:ComponentType<{children?:ReactNode;size?:number|string;ariaLabel?:string;color?:string;ariaHidden?:boolean;style?:CSSProperties;[key:string]:unknown}>=" +
    wrapper +
    ";return{cg:" +
    icons.cg +
    ",J0:" +
    icons.J0 +
    '};})();const e6:Record<Stat["tone"],string>=' +
    toneText +
    ";let " +
    statText.replace("(e,t)=>", "(e:string,t?:number|null):Stat=>") +
    ";" +
    full.e8.replace("function e8(e)", "function e8(e:Stat)") +
    full.e7
      .replace(
        "function e7(e)",
        "function e7(e:{entry?:ViewerEntry|null;className?:string})",
      )
      .replace("})=>[e5(", "}):Stat[]=>[e5(") +
    full.te.replace("function te(e)", "function te(e:boolean)") +
    full.e9.replace("function e9(e)", "function e9(e:{entry:ViewerEntry})") +
    "const Card:ComponentType<{entry:ViewerEntry}>=e9;const ViewerConsumer:ComponentType<{row:{entry:ViewerEntry}}>=({row:e})=>" +
    page.text(caller) +
    ";return{Card,Stats:e7,ViewerConsumer};}";
  const generated = await prettier.format(text, { parser: "babel-ts" });
  const generatedAst = parse(generated, {
    sourceType: "module",
    plugins: ["typescript", "jsx"],
  });
  for (const name of ["e9", "e7", "e8", "te"]) {
    const actual = exactlyOne(
      findNodes(
        generatedAst,
        (n) => n.type === "FunctionDeclaration" && n.id?.name === name,
      ),
      "generated " + name,
    );
    assert.deepEqual(
      canonical(actual.body),
      canonical(named(page, name).body),
      "original component body changed " + name,
    );
  }
  outputs.set(OUT + "original-viewer-card.tsx", generated);
  const selected = corpus.index.modules
    .filter((r) => r.ids.some((id) => Object.hasOwn(PINS, id)))
    .sort((a, b) => a.sha256.localeCompare(b.sha256));
  const prerequisiteNames = [
    "scripts/original-competition-entry.mjs",
    "reconstruction/competition-entry/contract.json",
    "packages/frontend/src/components/leaderboard/entry/entry-helpers.mjs",
    "packages/frontend/src/components/leaderboard/entry/entry-helpers.d.mts",
    "packages/frontend/src/components/leaderboard/entry/original-entry-row.tsx",
  ];
  const entryContract = JSON.parse(
    await readFile(
      path.join(appRoot, "reconstruction/competition-entry/contract.json"),
    ),
  );
  for (const name of Object.keys(entryContract.outputs))
    if (name.includes("/entry/variants/")) prerequisiteNames.push(name);
  const prerequisites = {};
  for (const name of prerequisiteNames)
    prerequisites[name] = sha256(await readFile(path.join(appRoot, name)));
  return {
    outputs,
    contract: {
      schemaVersion: 1,
      source: {
        reviewBase: "abd766d7a8c047f14af34851f64166b840c6728d",
        manifestSha256: corpus.anchors.manifestSha256,
        sharedSourceSha256: SHARED,
        selectedIndexEntries: selected,
        selectedCompleteEntriesSha256: sha256(JSON.stringify(selected)),
      },
      prerequisite: {
        pr: 1296,
        sourceHead: "a6c5d3792b88d47cdbf6f870ee59e47ec5e3698d",
        files: prerequisites,
        credit:
          "Reused identity/image helpers and original SVG wrapper attribution; no duplicate recovery claim.",
      },
      outputs: Object.fromEntries([...outputs].map(([p, t]) => [p, sha256(t)])),
      witnesses: witnesses.sort(
        (a, b) => a.source.localeCompare(b.source) || a.utf16[0] - b.utf16[0],
      ),
      limits: [
        "Captured source is parsed, never executed as a runtime factory. Original upstream authorship retained.",
        "Caller supplies a validated viewer entry: the component neither identifies nor authorizes an account.",
        "SOL price is an explicit injected hook. Its query/cache/transport and backend business logic are not reconstructed here.",
        "Only original UI display multiplies supplied buySpendSol by supplied price; no pricing, rank, PnL or eligibility calculation.",
        "Translation/Avatar/Link are explicit compatible capabilities; local fixture rendering is not original media/router/provider parity.",
        "No native page/API/projection/auth/session/SDK change. Component factory is created once in a legitimate client module.",
      ],
    },
  };
}
export async function verifyCompetitionViewer(appRoot = APP_ROOT) {
  const { outputs, contract } = await buildCompetitionViewer(appRoot);
  for (const [name, expected] of outputs) {
    const actual = await readFile(path.join(appRoot, name), "utf8"),
      plugins = name.endsWith(".tsx") ? ["typescript", "jsx"] : [];
    assert.deepEqual(
      canonical(parse(actual, { sourceType: "module", plugins })),
      canonical(parse(expected, { sourceType: "module", plugins })),
      "maintained AST differs " + name,
    );
    assert.equal(actual, expected, "maintained bytes differ " + name);
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
      const { outputs, contract } = await buildCompetitionViewer();
      for (const [name, text] of outputs) {
        const f = path.join(APP_ROOT, name);
        await mkdir(path.dirname(f), { recursive: true });
        await writeFile(f, text);
      }
      await mkdir(path.join(APP_ROOT, DIRECTORY), { recursive: true });
      await writeFile(
        path.join(APP_ROOT, DIRECTORY, "contract.json"),
        JSON.stringify(contract, null, 2) + "\n",
      );
    } else await verifyCompetitionViewer();
    console.log(
      "Complete original viewer card, actual invocation, stats and used source closures verified without captured runtime execution.",
    );
  } catch (e) {
    console.error(e.message);
    process.exitCode = 1;
  }
}
