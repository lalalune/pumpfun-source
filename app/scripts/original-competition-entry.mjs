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
export const DIRECTORY = "reconstruction/competition-entry";
const OUT = "packages/frontend/src/components/leaderboard/entry/";
const SHARED =
  "49b11417fd4d500d8821c94df6c215b77da2248875f943570f2b9df6c9b35213";
const PINS = {
  590407: ["3f494070c58a6d7f0f70279887ef648107935b765fe849de3e9ec100cec45dda"],
  139209: ["8d4ffb7afbfae1b99df53cf4d8421f1fb6f85c290468471f2e4f71f58358ed9b"],
  179537: [
    "44627d7c92a6d1701f6dfa39d0d6a883e49091468c77b5c53b59e287c60033c6",
    "9bf80842633385d9f509ffadb3aff4690be9592934d3679b017d690083f76992",
  ],
  146695: ["bb995bc856796eb404e21763f5a72275af2b0efa06b46f0d12507e1c6a3d90a1"],
  365089: ["8957b61a69e89f0148cf9a43ca9bc4089cc0c2c892e476af960d1a02c966f4d1"],
  599432: ["27351c6a51494d8af0e554adea5a63e593e723beae394a6e8847feb9ede0daee"],
  69399: [
    "35ee9b42b2197b69c4f65475eaafa8097929e9e2e1f0657cce4fc2d79565d075",
    "4043938d1f3547190132378541afc93d48c24d0dc55898853f2b2b987071eeb1",
  ],
  741084: [
    "1877fed09a6363588057a816a53c9d14fa46d3a3cb285321349a29a6ce48812a",
    "64085dc31cc9ebbcde019719b8096cfd198d84216b08826b70461fdfa689dc55",
    "9fa49ca7090d955ed1650833d4a5adb620e11fd63ee88437701c50bd419832a2",
  ],
  426091: ["93b70fac45ba969c312e0f7ec965b181d06a8332f7e1a4bba6751a63fd5555a4"],
  98525: ["38b7b65f7e40c1463314e2e5d484a63675c6d48338435ee54a71a4c5593f046b"],
  897665: ["7f51ea2404b2095fdef86bb61090e6288dbd2c80030c5d8ed60de1366be33c7e"],
  90832: ["4338f013e20debf9abf08d64e2fd71df845208712ad7737a91216f3b9c48da90"],
  745018: ["4cc46a6d51b6a9b0fe8ce9f64d77e130e7961309e881fe14f64efa16fb09f660"],
};
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
          ].includes(k),
      )
      .map(([k, v]) => [k, canonical(v)]),
  );
}
function exported(f, id, name) {
  const result = [];
  for (const call of findNodes(
    f.node,
    (n) =>
      n.type === "CallExpression" &&
      member(n.callee, f.runtime, "s") &&
      (n.arguments[1]?.value === id || (!n.arguments[1] && f.ids.length === 1)),
  )) {
    const a = call.arguments[0].elements;
    for (let i = 0; i < a.length; i += 3)
      if (a[i].value === name) result.push(a[i + 2]);
  }
  return exactlyOne(result, "actual export " + id + "." + name);
}
const vars = (f) =>
  f.node.body.body
    .filter((n) => n.type === "VariableDeclaration")
    .flatMap((n) => n.declarations);
const variable = (f, name) =>
  exactlyOne(
    vars(f).filter((n) => n.id.name === name),
    "top-level " + name,
  );
const named = (f, name) =>
  exactlyOne(
    f.node.body.body.filter(
      (n) => n.type === "FunctionDeclaration" && n.id.name === name,
    ),
    "function " + name,
  );
export async function buildCompetitionEntry(appRoot = APP_ROOT) {
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
    const found = [];
    for (const row of rows)
      found.push({
        row,
        f: await corpus.factory(+id, { source: row.origins[0].source }),
      });
    factories.set(+id, found);
  }
  const one = (id) => exactlyOne(factories.get(id), "single context " + id).f;
  const add = (f, node, label) => {
    witnesses.push(f.witness(node, label));
    return f.text(node);
  };
  const page = one(590407),
    shared = one(426091),
    svg = one(745018),
    badge = one(98525),
    dt = one(139209);
  for (const [alias, id, boundary] of [
    ["n", 179537, "rank palette"],
    ["C", 146695, "profile href"],
    ["P", 365089, "short wallet"],
    ["J", 599432, "verification hint"],
    ["G", 69399, "squad href"],
    ["V", 741084, "image normalizer"],
    ["W", 897665, "IPFS constant"],
    ["B", 98525, "verified SVG"],
    ["q", 745018, "crown SVG"],
    ["H", 90832, "PnL display"],
    ["a", 732486, "injected JSX runtime"],
    ["s", 445242, "injected compiler runtime"],
    ["l", 398902, "injected translation provider"],
    ["A", 338319, "local bounded class capability"],
    ["Q", 458310, "injected Link provider"],
    ["Z", 705313, "injected Avatar provider"],
  ]) {
    const declaration = variable(page, alias);
    assert.ok(member(declaration.init.callee, page.runtime, "i"));
    assert.equal(declaration.init.arguments[0].value, id);
    add(
      page,
      declaration,
      "actual X import edge: " + alias + " -> " + id + " (" + boundary + ")",
    );
  }
  for (const [factory, alias, id] of [
    [badge, "t", 732486],
    [badge, "r", 445242],
    [badge, "n", 426091],
    [svg, "t", 352386],
  ]) {
    const declaration = variable(factory, alias);
    assert.ok(member(declaration.init.callee, factory.runtime, "i"));
    assert.equal(declaration.init.arguments[0].value, id);
    add(
      factory,
      declaration,
      "actual used SVG provider edge: " + alias + " -> " + id,
    );
  }
  const row = named(page, "X"),
    rowText = add(page, row, "COMPLETE actual competition entry row X");
  const caller = exactlyOne(
    findNodes(
      page.node,
      (n) =>
        n.type === "CallExpression" &&
        (member(n.callee, "a", "jsx") ||
          (n.callee.type === "SequenceExpression" &&
            member(n.callee.expressions.at(-1), "a", "jsx"))) &&
        n.arguments[0]?.name === "X",
    ),
    "actual X caller",
  );
  add(
    page,
    caller,
    "actual consumer: supplied entry and already selected prize",
  );
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
          (n) => n.type === "StringLiteral" && n.value === "prize_line",
        ).length === 1,
    ),
    "actual row planner",
  );
  add(
    page,
    planner,
    "complete actual row planner / served entry and prize decisions",
  );
  add(
    dt,
    variable(dt, "m"),
    "actual complete served competition entry DTO including shared profile fields",
  );
  const profileFields = variable(dt, "h");
  add(dt, profileFields, "actual shared profile fields spread into entry DTO");
  const palettes = factories.get(179537).map(({ f }) => {
    const value = exported(f, 179537, "S");
    assert.equal(value.type, "ObjectExpression");
    add(f, value, "used rank palette literal; no full-factory winner");
    return { f, value };
  });
  assert.deepEqual(
    canonical(palettes[0].value),
    canonical(palettes[1].value),
    "rank literal variants differ",
  );
  const placeholderName = exported(shared, 426091, "A");
  assert.equal(placeholderName.type, "Identifier");
  const placeholder = variable(shared, placeholderName.name).init;
  assert.equal(placeholder.type, "StringLiteral");
  add(shared, placeholder, "actual empty-image sentinel value only");
  const prefix = exported(one(897665), 897665, "f");
  assert.equal(prefix.type, "StringLiteral");
  add(one(897665), prefix, "actual passed IPFS prefix constant");
  const profile = one(146695),
    profileExport = exported(profile, 146695, "$");
  assert.equal(profileExport.type, "Identifier");
  const profileFn = named(profile, profileExport.name),
    profileText = add(
      profile,
      profileFn,
      "complete used profile href function",
    );
  const short = one(365089),
    shortExport = exported(short, 365089, "d");
  assert.equal(shortExport.type, "Identifier");
  const shortText = add(
    short,
    named(short, shortExport.name),
    "complete used wallet shortener",
  );
  const verified = one(599432),
    verifiedText = add(
      verified,
      exported(verified, 599432, "f"),
      "complete strict verification display predicate",
    );
  const pnl = one(90832),
    pnlText = add(
      pnl,
      exported(pnl, 90832, "w"),
      "complete supplied-PnL display formatter; no calculation",
    );
  const squadRows = [],
    imageRows = [],
    imports = [];
  for (const [id, kind, key] of [
    [69399, "squad", "Z"],
    [741084, "image", "f"],
  ]) {
    for (const { f, row } of factories.get(id)) {
      const e = exported(f, id, key),
        filename =
          OUT + "variants/" + kind + "-" + row.sha256.slice(0, 12) + ".mjs",
        local = "v" + imports.length;
      imports.push(
        "import{createHelper as " +
          local +
          "}from'./variants/" +
          kind +
          "-" +
          row.sha256.slice(0, 12) +
          ".mjs';",
      );
      let body;
      if (kind === "squad") {
        const declarations = f.node.body.body.filter(
          (n) => n.type === "VariableDeclaration",
        );
        assert.equal(declarations.length, 1);
        body =
          add(
            f,
            declarations[0],
            "complete used squad route closure declarations",
          ) +
          "return " +
          add(f, e, "actual squad href export") +
          ";";
      } else {
        const declaration = exactlyOne(
          f.node.body.body.filter((n) => n.type === "VariableDeclaration"),
          "actual image import",
        );
        const binding = declaration.declarations[0].id.name;
        assert.ok(
          member(declaration.declarations[0].init.callee, f.runtime, "i") &&
            declaration.declarations[0].init.arguments[0].value === 426091,
        );
        add(f, declaration, "actual image-sentinel import edge");
        body =
          "const " +
          binding +
          "={A:emptyImage};return " +
          add(f, e, "complete used image normalization export") +
          ";";
      }
      outputs.set(
        filename,
        await prettier.format(
          "// Explicit original source context; never a guessed runtime winner.\nexport function createHelper({emptyImage}={}){" +
            body +
            "}",
          { parser: "babel" },
        ),
      );
      (kind === "squad" ? squadRows : imageRows).push({
        sha256: row.sha256,
        path: filename,
        source: row.origins[0].source,
        local,
      });
    }
  }
  const badgeFn = exported(badge, 98525, "f"),
    badgePath = variable(badge, "a").init;
  const badgeText = add(
      badge,
      badgeFn,
      "COMPLETE original verified badge component",
    ),
    badgePathText = add(badge, badgePath, "actual verified SVG path");
  const crown = add(
    svg,
    exported(svg, 745018, "zN"),
    "COMPLETE used original crown icon",
  );
  const svgWrapper = add(
    svg,
    variable(svg, "r").init,
    "COMPLETE used original SVG wrapper",
  );
  const pubRows = (rows) => rows.map(({ local, ...r }) => r);
  const helperText =
    imports.join("\n") +
    "\nexport const squadVariants=Object.freeze(" +
    JSON.stringify(pubRows(squadRows)) +
    ");export const imageVariants=Object.freeze(" +
    JSON.stringify(pubRows(imageRows)) +
    ");\n" +
    "const squads=new Map([" +
    squadRows
      .map((r) => "[" + JSON.stringify(r.sha256) + "," + r.local + "]")
      .join(",") +
    "]),images=new Map([" +
    imageRows
      .map((r) => "[" + JSON.stringify(r.sha256) + "," + r.local + "]")
      .join(",") +
    "]);\n" +
    "export function createEntryHelpers({squadVariant,imageVariant,Intl}){const squad=squads.get(squadVariant),image=images.get(imageVariant);if(!squad||!image)throw new TypeError('Explicit reviewed squad and image source hashes required');" +
    profileText +
    shortText +
    "return{profileHref:" +
    profileExport.name +
    ",shortWallet:" +
    shortExport.name +
    ",isVerified:" +
    verifiedText +
    ",formatPnl:" +
    pnlText +
    ",squadHref:squad(),normalizeImage:image({emptyImage:" +
    JSON.stringify(placeholder.value) +
    "}),ipfsPrefix:" +
    JSON.stringify(prefix.value) +
    "};}";
  outputs.set(
    OUT + "entry-helpers.mjs",
    await prettier.format(helperText, { parser: "babel" }),
  );
  const types =
    "import type{ComponentType,ReactNode,CSSProperties}from'react';\nexport type Entry={entryId:string;participantId:string;kind:'group'|'person';rank:number;pnlUsd:number;memberCount:number;walletAddress:string|null;username:string|null;profileImageUrl:string|null;isVerified:boolean;verifiedBadgeVisible:boolean};\nexport type Prize={rankFrom:number;rankTo:number;amount:string};\nexport type AvatarProps={address:string;alt:string;className:string;height:number;ipfsPrefix:string;isAnonymous:false;src?:string;width:number};\nexport type LinkProps={href:string|null;prefetch:false;className:string;children?:ReactNode};\n";
  const caps =
    "jsx:typeof import('react/jsx-runtime').jsx;jsxs:typeof import('react/jsx-runtime').jsxs;React:Pick<typeof import('react'),'createElement'>;useMemoCache:(size:number)=>any[];useTranslation:()=>{t:(key:string,values?:Record<string,string|number>)=>string};classNames:(...parts:Array<string|undefined|false>)=>string;Avatar:ComponentType<AvatarProps>;Link:ComponentType<LinkProps>;profileHref:(value:string)=>string|null;shortWallet:(value:string)=>string;isVerified:(value:Entry)=>boolean;formatPnl:(value:number)=>string;squadHref:(value:{groupId:string;username:string|null})=>string;normalizeImage:(value:string|null)=>string|undefined;ipfsPrefix:string";
  const component =
    '"use client";\n' +
    types +
    "export function createEntryRow({jsx,jsxs,React,useMemoCache,useTranslation,classNames,Avatar,Link,profileHref,shortWallet,isVerified,formatPnl,squadHref,normalizeImage,ipfsPrefix}:{" +
    caps +
    "}){" +
    "const VerifiedBadge:ComponentType<{size:number;className?:string}>=(()=>{const t={jsx,jsxs},r={c:useMemoCache},n={c:classNames};let a=" +
    badgePathText +
    ";return " +
    badgeText +
    ";})();" +
    "const Crown:ComponentType<{className?:string;'aria-hidden'?:boolean}>=(()=>{const t={default:React};const r:ComponentType<{children?:ReactNode;size?:number|string;ariaLabel?:string;color?:string;ariaHidden?:boolean;style?:CSSProperties;[key:string]:unknown}>=" +
    svgWrapper +
    ";return " +
    crown +
    ";})();" +
    "const a={jsx,jsxs},s={c:useMemoCache},l={f:useTranslation},n:{S:Record<number,string|undefined>}={S:" +
    palettes[0].f.text(palettes[0].value) +
    "},A={c:classNames},G={Z:squadHref},C={$:profileHref},P={d:shortWallet},V={f:normalizeImage},Z={f:Avatar},W={f:ipfsPrefix},J={f:isVerified},B={f:VerifiedBadge},q={zN:Crown},Q={default:Link},H={w:formatPnl};const Row:ComponentType<{entry:Entry;prize?:Prize|null}>=" +
    rowText +
    ";const X=Row;const EntryConsumer:ComponentType<{row:{entry:Entry;prize?:Prize|null}}>=({row:e})=>" +
    page.text(caller) +
    ";return{Row,EntryConsumer};}";
  outputs.set(
    OUT + "original-entry-row.tsx",
    await prettier.format(component, { parser: "babel-ts" }),
  );
  const selected = corpus.index.modules
    .filter((r) => r.ids.some((id) => Object.hasOwn(PINS, id)))
    .sort((a, b) => a.sha256.localeCompare(b.sha256));
  return {
    outputs,
    contract: {
      schemaVersion: 1,
      source: {
        reviewBase: "c5f10b023f5f298f8e3633a2f333b454c78af206",
        manifestSha256: corpus.anchors.manifestSha256,
        sharedSourceSha256: SHARED,
        selectedIndexEntries: selected,
        selectedCompleteEntriesSha256: sha256(JSON.stringify(selected)),
      },
      outputs: Object.fromEntries([...outputs].map(([p, t]) => [p, sha256(t)])),
      witnesses: witnesses.sort(
        (a, b) => a.source.localeCompare(b.source) || a.utf16[0] - b.utf16[0],
      ),
      attribution: {
        pr937:
          "Accepted complete prize D/T/J and optional badge expression; this unit recovers full X with the same original badge in context. No duplicate prize-factory count claim.",
        otherHelpers:
          "Original upstream authorship retained; local adapter names/types are not recovered TS.",
      },
      limits: [
        "Captured source parsed as AST, never executed as runtime factories.",
        "Explicit squad/image source contexts; no guessed global winner.",
        "Host supplies legitimate translation, compatible Link and Avatar. Avatar internals, Next router/cache, media requests, auth and backend behavior remain outside this unit.",
        "Entry/prize values are supplied; no ranking, price, PnL, membership or payout calculation.",
        "Native page/API/types/projection unchanged: current projection omits profileImageUrl, so no speculative main-page binding.",
        "Finite class join is a local capability for this row's nonconflicting strings; complete captured class-merge library not claimed.",
      ],
    },
  };
}
export async function verifyCompetitionEntry(appRoot = APP_ROOT) {
  const { outputs, contract } = await buildCompetitionEntry(appRoot);
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
      const { outputs, contract } = await buildCompetitionEntry();
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
    } else await verifyCompetitionEntry();
    console.log(
      "Complete original competition entry row and used source contexts verified without captured runtime execution.",
    );
  } catch (e) {
    console.error(e.message);
    process.exitCode = 1;
  }
}
