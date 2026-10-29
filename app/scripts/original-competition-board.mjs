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
export const DIRECTORY = "reconstruction/competition-board";
const OUT = "packages/frontend/src/components/leaderboard/board/";
const SHARED =
  "49b11417fd4d500d8821c94df6c215b77da2248875f943570f2b9df6c9b35213";
const PINS = {
  590407: ["3f494070c58a6d7f0f70279887ef648107935b765fe849de3e9ec100cec45dda"],
  706615: ["e606b2e7f5ab2bfd5da0abb70db2de0560f01d4d131d156719d8623614219e74"],
  139209: ["8d4ffb7afbfae1b99df53cf4d8421f1fb6f85c290468471f2e4f71f58358ed9b"],
  179537: [
    "44627d7c92a6d1701f6dfa39d0d6a883e49091468c77b5c53b59e287c60033c6",
    "9bf80842633385d9f509ffadb3aff4690be9592934d3679b017d690083f76992",
  ],
  359516: ["59b1004bf7c804e722ab718877cf19ecee28f5f157d184e14ffd65d89dcb228d"],
  961415: ["b3c4dc7eca967b4f9eaa67a43487bf6d8504bf5b4c58ccd582c2a4a3882c5d96"],
};
const vars = (f) =>
  f.node.body.body
    .filter((n) => n.type === "VariableDeclaration")
    .flatMap((n) => n.declarations);
const variable = (f, name) =>
  exactlyOne(
    vars(f).filter((n) => n.id.name === name),
    "variable " + name,
  );
const named = (f, name) =>
  exactlyOne(
    f.node.body.body.filter(
      (n) => n.type === "FunctionDeclaration" && n.id.name === name,
    ),
    "function " + name,
  );
function exported(f, id, key) {
  const out = [];
  for (const call of findNodes(
    f.node,
    (n) =>
      n.type === "CallExpression" &&
      member(n.callee, f.runtime, "s") &&
      (n.arguments[1]?.value === id || (!n.arguments[1] && f.ids.length === 1)),
  )) {
    const a = call.arguments[0].elements;
    for (let i = 0; i < a.length; i += 3)
      if (a[i].value === key) out.push(a[i + 2]);
  }
  return exactlyOne(out, "actual export " + id + "." + key);
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
function replaceOnce(text, before, after) {
  assert.equal(
    text.split(before).length,
    2,
    "single annotation site " + before,
  );
  return text.replace(before, after);
}
export async function buildCompetitionBoard(appRoot = APP_ROOT) {
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
  for (const [id, pins] of Object.entries(PINS)) {
    const rows = corpus.index.modules.filter((r) => r.ids.includes(+id));
    assert.deepEqual(
      rows.map((r) => r.sha256).sort(),
      pins,
      "unreviewed variants " + id,
    );
    const fs = [];
    for (const row of rows)
      fs.push(await corpus.factory(+id, { source: row.origins[0].source }));
    factories.set(+id, fs);
  }
  const one = (id) => exactlyOne(factories.get(id), "single factory " + id),
    page = one(590407),
    utility = one(706615),
    add = (f, n, label) => {
      witnesses.push(f.witness(n, label));
      return f.text(n);
    };
  for (const [alias, id] of [
    ["a", 732486],
    ["s", 445242],
    ["i", 352386],
    ["l", 398902],
    ["U", 983737],
    ["A", 338319],
    ["n", 179537],
    ["$", 706615],
    ["td", 359516],
    ["ti", 961415],
  ]) {
    const v = variable(page, alias);
    assert.ok(member(v.init.callee, page.runtime, "i"));
    assert.equal(v.init.arguments[0].value, id);
    add(page, v, "actual board import " + alias + " -> " + id);
  }
  const original = named(page, "to");
  let board = add(
    page,
    original,
    "COMPLETE actual competition-board coordinator to",
  );
  board = replaceOnce(board, "function to(e)", "function to(e:BoardProps)");
  board = replaceOnce(board, 'e=e=>"final"', 'e=(e:string)=>"final"');
  board = replaceOnce(
    board,
    "competition:R}=",
    "competition:R}:{list:ListSnapshot;detail:DetailSnapshot;competition:Competition|null|undefined}=",
  );
  board = replaceOnce(
    board,
    "(({competition:e,detail:t})=>{let r=",
    "(({competition:e,detail:t}:{competition:Competition|null|undefined;detail:Detail|null|undefined}):BoardItem[]=>{let r:BoardItem[]=",
  );
  board = replaceOnce(
    board,
    "(e=>{switch(e.type)",
    "((e:BoardItem)=>{switch(e.type)",
  );
  const pieces = [];
  for (const [name, type] of [
    ["T", "{title:string;isCardTop:boolean}"],
    ["O", "{paidRanks:number}"],
    ["K", "{title:string;body:string;testId:string}"],
  ]) {
    const n = variable(page, name);
    pieces.push(
      "const " +
        name +
        ":ComponentType<" +
        type +
        ">=" +
        add(page, n.init, "COMPLETE original board display " + name) +
        ";",
    );
  }
  for (const name of ["tc", "tu", "tm"])
    pieces.push(
      add(
        page,
        named(page, name),
        "COMPLETE original board-item predicate " + name,
      ).replace(
        "function " + name + "(e)",
        "function " + name + "(e:BoardItem)",
      ),
    );
  const callers = findNodes(
    page.node,
    (n) =>
      n.type === "CallExpression" &&
      n.callee.type === "SequenceExpression" &&
      member(n.callee.expressions.at(-1), "a", "jsx") &&
      n.arguments[0]?.name === "to",
  );
  assert.equal(callers.length, 2);
  const callTexts = {};
  for (const call of callers) {
    const kind = exactlyOne(
      call.arguments[1].properties.filter((p) => p.key.name === "kind"),
      "actual kind",
    ).value.value;
    assert.ok(["person", "group"].includes(kind));
    callTexts[kind] = add(
      page,
      call,
      "actual " + kind + " board invocation and control placement",
    );
  }
  const select = add(
    utility,
    exported(utility, 706615, "y"),
    "reused complete accepted bucket selection",
  );
  const paid = add(
    utility,
    exported(utility, 706615, "V"),
    "COMPLETE used paid-rank boundary function",
  );
  add(
    utility,
    exported(utility, 706615, "J"),
    "reused accepted rank-prize lookup",
  );
  for (const id of [359516, 961415])
    add(
      one(id),
      exported(one(id), id, "f"),
      "accepted injected " +
        id +
        " query-hook boundary; no provider reconstruction",
    );
  for (const f of factories.get(179537))
    add(
      f,
      exported(f, 179537, "B"),
      "unreconstructed compatible motion-card port, explicit original context",
    );
  const dto = one(139209);
  for (const name of ["h", "m", "g"])
    add(dto, variable(dto, name), "actual board DTO " + name);
  const types =
    '"use client";import type{ComponentType,ReactNode}from"react";import type{ViewerEntry}from"../viewer/original-viewer-card";import type{Prize}from"../original-prizes";export type Competition={id:string;kind:"person"|"group";phase:string;title:string;startsAt:string|null;endsAt:string|null;prizes:Prize[];[key:string]:unknown};export type Buckets={live:Competition[];upcoming:Competition[];past:Competition[]};export type Detail={competition:Competition;leaderboard:{entries:ViewerEntry[]};viewer?:{entry:ViewerEntry|null}|null};export type Snapshot<T>={data?:T;isError:boolean;isLoading:boolean;refetch:()=>unknown};export type ListSnapshot=Snapshot<Buckets>;export type DetailSnapshot=Snapshot<Detail>;export type BoardClient={useList:(o:{isVisible:true})=>ListSnapshot;useDetail:(o:{idOrSlug:string|null;isVisible:true})=>DetailSnapshot;selectCompetition:(data:Buckets|undefined,kind:"person"|"group")=>Competition|null};export type BoardProps={kind:"person"|"group";periodControl?:ReactNode;periodControlTopPx?:number|null;periodControlLeadClassName?:string};export type ControlProps={periodControl?:ReactNode;periodControlTopPx?:number|null};type BoardItem={type:"hero"}|{type:"highlights";competitionId:string;entries:ViewerEntry[]}|{type:"pending"}|{type:"viewer";entry:ViewerEntry}|{type:"section";section:"final"|"standings"|"prizes";isCardTop:boolean}|{type:"row";entry:ViewerEntry;prize:Prize|null;isLast:boolean}|{type:"prize_line";paidRanks:number}|{type:"tier";prize:Prize;isLast:boolean};export type HeroProps={kind:"person"|"group";topControl?:ReactNode;topControlTopPx:number|null;className?:string;competition:Competition|null|undefined;isLoading:boolean;isError:boolean;onRetry:()=>void;onOpenRules:()=>void};export type HighlightProps={competitionId:string;entries:ViewerEntry[];window:{fromMs:number;toMs:number}|null};export type RulesProps={open:boolean;onOpenChange:(open:boolean)=>void;competition:Competition};export type CardProps={ariaLabel:string;testId?:string;children?:ReactNode};';
  const caps =
    'jsx:typeof import("react/jsx-runtime").jsx;jsxs:typeof import("react/jsx-runtime").jsxs;React:Pick<typeof import("react"),"useState">;useMemoCache:(size:number)=>any[];useTranslation:()=>{t:(key:string,values?:Record<string,string|number>)=>string};useReducedMotion:()=>boolean|null|undefined;classNames:(...parts:Array<string|undefined|false>)=>string;client:BoardClient;Hero:ComponentType<HeroProps>;Highlights:ComponentType<HighlightProps>;Rules:ComponentType<RulesProps>;Card:ComponentType<CardProps>;EntryRow:ComponentType<{entry:ViewerEntry;prize?:Prize|null}>;ViewerCard:ComponentType<{entry:ViewerEntry}>;PrizeTier:ComponentType<{prize:Prize}>;findPrize:(prizes:Prize[],rank:number)=>Prize|null';
  const text =
    types +
    "export function createCompetitionBoard({jsx,jsxs,React,useMemoCache,useTranslation,useReducedMotion,classNames,client,Hero,Highlights,Rules,Card,EntryRow,ViewerCard,PrizeTier,findPrize}:{" +
    caps +
    "}){const a={jsx,jsxs},s={c:useMemoCache},i={useState:React.useState},l={f:useTranslation},U={f:useReducedMotion},A={c:classNames},n={B:Card},td={f:client.useList},ti={f:client.useDetail},$={y:client.selectCompetition,V:" +
    paid.replace("e=>", "(e:Prize[])=>") +
    ",J:findPrize};const e$=Hero,e3=Highlights,tn=Rules,e9=ViewerCard,X=EntryRow,D=PrizeTier;" +
    pieces.join("") +
    board +
    "const PersonConsumer:ComponentType<ControlProps>=({periodControl:ef,periodControlTopPx:eh})=>" +
    callTexts.person +
    ";const GroupConsumer:ComponentType<ControlProps>=({periodControl:en,periodControlTopPx:el})=>" +
    callTexts.group +
    ";return{Board:to,PersonConsumer,GroupConsumer};}";
  const generated = await prettier.format(text, { parser: "babel-ts" }),
    ast = parse(generated, {
      sourceType: "module",
      plugins: ["typescript", "jsx"],
    });
  for (const name of ["to", "tc", "tu", "tm"]) {
    const n = exactlyOne(
      findNodes(
        ast,
        (n) => n.type === "FunctionDeclaration" && n.id?.name === name,
      ),
      "generated " + name,
    );
    assert.deepEqual(
      canonical(n.body),
      canonical(named(page, name).body),
      "actual body changed " + name,
    );
  }
  outputs.set(OUT + "original-board.tsx", generated);
  const selected = corpus.index.modules
    .filter((r) => r.ids.some((id) => Object.hasOwn(PINS, id)))
    .sort((a, b) => a.sha256.localeCompare(b.sha256));
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
      outputs: Object.fromEntries([...outputs].map(([p, t]) => [p, sha256(t)])),
      witnesses: witnesses.sort(
        (a, b) => a.source.localeCompare(b.source) || a.utf16[0] - b.utf16[0],
      ),
      prerequisites: {
        1296: "Entry row and explicit identity/image contexts",
        1315: "Viewer card and optional stats with injected price hook",
        937: "Prize tier, formatting and findPrize",
        850: "List/detail hooks and bucket selector; genuine query/viewer/contract providers stay injected",
      },
      limits: [
        "Original full coordinator and finite display/predicate bodies preserved; captured factories parsed only.",
        "Ordinary array mapping, not virtualized rendering. No rank/prize/eligibility policy invented.",
        "Hero/highlights/rules/motion-card/query/reduced-motion providers are explicit compatible ports; their full original implementations are not claimed.",
        "Supplied viewer entry is UI data, not identity or backend authorization. No auth/session/registration/terms mutation.",
        "No native page/API/projection/SDK/capture/dependency/global-style/ledger changes.",
        "Component factory created once in a legitimate client module; no guessed global source variant.",
      ],
    },
  };
}
export async function verifyCompetitionBoard(appRoot = APP_ROOT) {
  const { outputs, contract } = await buildCompetitionBoard(appRoot);
  for (const [name, expected] of outputs) {
    const actual = await readFile(path.join(appRoot, name), "utf8");
    assert.deepEqual(
      canonical(
        parse(actual, { sourceType: "module", plugins: ["typescript", "jsx"] }),
      ),
      canonical(
        parse(expected, {
          sourceType: "module",
          plugins: ["typescript", "jsx"],
        }),
      ),
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
      const { outputs, contract } = await buildCompetitionBoard();
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
    } else await verifyCompetitionBoard();
    console.log(
      "Complete original competition-board coordinator, actual callers and source boundaries verified.",
    );
  } catch (e) {
    console.error(e.message);
    process.exitCode = 1;
  }
}
