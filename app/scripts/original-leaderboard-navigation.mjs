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
export const DIRECTORY = "reconstruction/leaderboard-navigation";
const SHARED =
  "a7c04fdc74fb88a27d5cf24355396ee560d88ad4042abf3eb6a3c6874c5bacf2";
const PINS = {
  311282: ["3ccfe0dd0e060990f9e24ad766854850ce8d19b064b0c4a5e2c27bfa1310e44d"],
  747911: ["10a3a306908e746dbc1eebee6ec66a391c39c9c84de5a133f441e1149fa8e9ad"],
  869322: ["5ac06ec234a4bab033be3383901f80320a7490743d289beecebfb1938be675ef"],
  986071: ["b8b5c48b0e1698ae04d6450303338955af3430a18b062cf2f732dd51bf0e6e12"],
  590407: ["3f494070c58a6d7f0f70279887ef648107935b765fe849de3e9ec100cec45dda"],
  765115: ["05f6e5546025b75d3e4a2b6d9a0b2ec996044a9c29a407bad514483b11e0aba3"],
  706615: ["e606b2e7f5ab2bfd5da0abb70db2de0560f01d4d131d156719d8623614219e74"],
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
  const values = [];
  for (const call of findNodes(
    factory.node,
    (node) =>
      node.type === "CallExpression" &&
      member(node.callee, factory.runtime, "s") &&
      (node.arguments[1]?.value === id ||
        (!node.arguments[1] && factory.ids.length === 1)),
  )) {
    const entries = call.arguments[0].elements;
    for (let i = 0; i < entries.length; i += 3)
      if (entries[i].value === name) values.push(entries[i + 2]);
  }
  return exactlyOne(values, `actual export ${id}.${name}`);
}
const declarations = (factory) =>
  factory.node.body.body
    .filter((node) => node.type === "VariableDeclaration")
    .flatMap((node) => node.declarations);
export async function buildLeaderboardNavigation(appRoot = APP_ROOT) {
  assert.equal(
    sha256(
      await readFile(
        path.join(appRoot, "scripts/original-contracts/source.mjs"),
      ),
    ),
    SHARED,
  );
  const corpus = await openCorpus(appRoot),
    witnesses = [],
    adapters = [],
    outputs = new Map(),
    factories = new Map();
  for (const [id, hashes] of Object.entries(PINS)) {
    const rows = corpus.index.modules.filter((row) =>
      row.ids.includes(Number(id)),
    );
    assert.deepEqual(
      rows.map((row) => row.sha256).sort(),
      hashes,
      `unreviewed ${id} variants`,
    );
    const row = exactlyOne(rows, `unique reviewed ${id}`);
    const factory = await corpus.factory(Number(id), {
      source: row.origins[0].source,
    });
    factories.set(Number(id), factory);
  }
  const witness = (factory, node, label) => {
    witnesses.push(factory.witness(node, label));
    return node;
  };
  async function output(name, source, factory, nodes) {
    const text = await prettier.format(source, { parser: "babel" });
    outputs.set(name, text);
    adapters.push({
      path: name,
      factory: factory.provenance,
      sha256: sha256(text),
      retainedAsts: nodes.map((node) => ({
        type: node.type,
        sha256: sha256(JSON.stringify(canonical(node))),
      })),
    });
    for (const node of nodes)
      witness(factory, node, `${name}: complete ${node.type}`);
  }
  const core = factories.get(311282),
    coreDeclarations = declarations(core);
  const functions = ["l", "c", "d", "f", "m"].map((name) =>
    exactlyOne(
      core.node.body.body.filter(
        (node) => node.type === "FunctionDeclaration" && node.id.name === name,
      ),
      `used core function ${name}`,
    ),
  );
  const values = ["n", "a", "i", "s", "u", "o", "v"].map((name) =>
    exactlyOne(
      coreDeclarations.filter((node) => node.id.name === name),
      `used core state ${name}`,
    ),
  );
  const enumParser = exported(core, 311282, "b"),
    queryState = exported(core, 311282, "o");
  await output(
    "query-state.mjs",
    `// Source-adapted USED enum/single-query/queue path, not the whole URL-state library.\nexport function createQueryState({useUrlAdapter,react,logDebug,logParseError,formatError,console,window,navigator,location,performance,setTimeout}){var t;const r={J:useUrlAdapter,h:logDebug,S:logParseError,C:formatError},p=react;${functions.map((node) => core.text(node)).join("\n")}var ${values.map((node) => core.text(node)).join(",")};return {parseEnum:${core.text(enumParser)},useQueryState:${core.text(queryState)}};}`,
    core,
    [...functions, ...values, enumParser, queryState],
  );
  const constants = factories.get(986071);
  const keyObject = exported(constants, 986071, "f");
  const leaderboardKeys = exactlyOne(
    keyObject.properties.filter((node) => node.key.name === "LEADERBOARD"),
    "actual LEADERBOARD keys",
  ).value;
  witness(constants, leaderboardKeys, "actual tab/period URL key names");
  const landing = factories.get(869322),
    landingHook = exported(landing, 869322, "b"),
    cup = exported(landing, 869322, "N");
  assert.equal(cup.value, "cup");
  await output(
    "landing.mjs",
    `// Complete original live-Cup landing/timeframe hook.\nexport function createLanding({useMemoCache,useState,useList,hasLiveCompetition}){const t={c:useMemoCache},l={useState},a={f:useList},n={g:hasLiveCompetition};return ${landing.text(landingHook)};}`,
    landing,
    [landingHook],
  );
  const period = factories.get(747911),
    periodDecl = declarations(period),
    allowed = exactlyOne(
      periodDecl.filter((node) => node.id.name === "a"),
      "actual period enum",
    );
  const periodHook = exported(period, 747911, "t"),
    href = exported(period, 747911, "O");
  await output(
    "period.mjs",
    `// Complete original period hook and link builder.\nexport function createPeriod({useMemoCache,parseEnum,useQueryState}){const t={c:useMemoCache},r={b:parseEnum,o:useQueryState},l={N:${landing.text(cup)}},i={f:{LEADERBOARD:${constants.text(leaderboardKeys)}}};let ${period.text(allowed)};return {usePeriod:${period.text(periodHook)},periodHref:${period.text(href)}};}`,
    period,
    [allowed, periodHook, href],
  );
  const page = factories.get(590407),
    pageExport = exported(page, 590407, "LeaderboardPage");
  const tab = exactlyOne(
    findNodes(
      pageExport,
      (node) =>
        node.type === "FunctionExpression" &&
        node.params.length === 0 &&
        findNodes(
          node.body,
          (node) =>
            node.type === "ObjectProperty" && node.key.name === "urlTab",
        ).length === 1,
    ),
    "actual complete inline tab hook",
  );
  const pageDecl = declarations(page),
    allowedTabs = exactlyOne(
      pageDecl.filter((node) => node.id.name === "rc"),
      "actual allowed tab names",
    ),
    defaultTab = exactlyOne(
      pageDecl.filter((node) => node.id.name === "ru"),
      "actual default tab",
    );
  const localDecl = pageExport.body.body
    .filter((node) => node.type === "VariableDeclaration")
    .flatMap((node) => node.declarations);
  const requested = exactlyOne(
      localDecl.filter((node) => node.id.name === "E"),
      "actual requested tab",
    ),
    resolved = exactlyOne(
      localDecl.filter((node) => node.id.name === "R"),
      "actual responsive/flag tab resolution",
    );
  await output(
    "tab.mjs",
    `// Complete original tab hook and actual page fallback expressions.\nexport function createTab({useMemoCache,parseEnum,useQueryState}){const s={c:useMemoCache},rd={b:parseEnum,o:useQueryState},ro={f:{LEADERBOARD:${constants.text(leaderboardKeys)}}};let ${page.text(allowedTabs)},${page.text(defaultTab)};return {useTab:${page.text(tab)},resolveTab:({urlTab:q,squadsEnabled:P,isDesktop:$})=>{let ${page.text(requested)},${page.text(resolved)};return R;}};}`,
    page,
    [allowedTabs, defaultTab, tab, requested, resolved],
  );
  // Bind actual provider/consumer/import edges without evaluating the page or vendor context.
  for (const [factory, id] of [
    [period, 311282],
    [period, 869322],
    [period, 986071],
    [landing, 359516],
    [landing, 706615],
    [page, 747911],
    [page, 311282],
    [page, 986071],
    [page, 869322],
    [core, 765115],
    [core, 352386],
  ]) {
    const node = exactlyOne(
      declarations(factory).filter(
        (node) =>
          node.init?.type === "CallExpression" &&
          member(node.init.callee, factory.runtime, "i") &&
          node.init.arguments[0]?.value === id,
      ),
      `${factory.id} used import ${id}`,
    );
    witness(factory, node, `actual ${factory.id} import ${id}`);
  }
  for (const id of [765115, 706615]) {
    const factory = factories.get(id);
    for (const name of id === 765115 ? ["J", "h", "S", "C"] : ["g"])
      witness(
        factory,
        exported(factory, id, name),
        `external original provider ${id}.${name}; explicit capability`,
      );
  }
  const calls = findNodes(
    pageExport,
    (node) =>
      node.type === "CallExpression" &&
      member(
        node.callee.type === "SequenceExpression"
          ? node.callee.expressions.at(-1)
          : node.callee,
        "ri",
        "t",
      ),
  );
  assert.equal(calls.length, 1);
  witness(page, calls[0], "actual LeaderboardPage period consumer");
  const trader = exactlyOne(
    page.node.body.body.filter(
      (node) => node.type === "FunctionDeclaration" && node.id.name === "tB",
    ),
    "actual trader board",
  );
  const landingCall = exactlyOne(
    findNodes(
      trader,
      (node) =>
        node.type === "CallExpression" &&
        member(
          node.callee.type === "SequenceExpression"
            ? node.callee.expressions.at(-1)
            : node.callee,
          "th",
          "b",
        ),
    ),
    "actual trader live-Cup landing call",
  );
  witness(
    page,
    landingCall,
    "actual trader board consumes live-Cup landing with daily/person/initialPeriod",
  );
  outputs.set(
    "client.mjs",
    await prettier.format(
      `import {createQueryState} from './query-state.mjs';import {createPeriod} from './period.mjs';import {createTab} from './tab.mjs';import {createLanding} from './landing.mjs';export function createLeaderboardNavigation(capabilities){const query=createQueryState(capabilities);const hooks={useMemoCache:capabilities.useMemoCache,...query};return {...query,...createPeriod(hooks),...createTab(hooks),useLanding:createLanding({useMemoCache:capabilities.useMemoCache,useState:capabilities.react.useState,useList:capabilities.useList,hasLiveCompetition:capabilities.hasLiveCompetition})};}`,
      { parser: "babel" },
    ),
  );
  const selected = corpus.index.modules
    .filter((row) => row.ids.some((id) => Object.hasOwn(PINS, id)))
    .sort((a, b) => a.sha256.localeCompare(b.sha256));
  const contract = {
    schemaVersion: 1,
    source: {
      reviewBase: "03bcf6a0b8162919a72b884869850abf342aa9d3",
      manifestSha256: corpus.anchors.manifestSha256,
      sharedSourceSha256: SHARED,
      selectedIndexEntries: selected,
      selectedCompleteEntriesSha256: sha256(JSON.stringify(selected)),
    },
    adapters,
    witnesses: witnesses.sort(
      (a, b) => a.source.localeCompare(b.source) || a.utf16[0] - b.utf16[0],
    ),
    scope:
      "Complete used original leaderboard URL/tab/period/live-Cup state workflow. Used enum/single-query/queue path only; no whole vendor library, router, auth or mounted-page claim.",
    capabilities: [
      "useUrlAdapter",
      "react.useRef/useState/useEffect/useCallback",
      "useMemoCache",
      "useList",
      "hasLiveCompetition",
      "logDebug/logParseError/formatError/console",
      "window/navigator/location/performance/setTimeout",
    ],
    limits: [
      "Captured bundles/factories are parsed, never executed.",
      "Unknown actual Next/router adapter and React scheduling remain explicit; tests inject synthetic capabilities.",
      "No browser/user storage, real profiles/cookies or production API is read.",
      "Existing independent local leaderboard UI/backend and feature ledger remain unchanged.",
    ],
  };
  return { outputs, contract };
}
export async function verifyLeaderboardNavigation(appRoot = APP_ROOT) {
  const { outputs, contract } = await buildLeaderboardNavigation(appRoot);
  for (const [name, expected] of outputs) {
    const actual = await readFile(path.join(appRoot, DIRECTORY, name), "utf8");
    assert.deepEqual(
      canonical(parse(actual, { sourceType: "module" })),
      canonical(parse(expected, { sourceType: "module" })),
      `maintained AST differs: ${name}`,
    );
    assert.equal(
      actual,
      expected,
      `maintained canonical bytes differ: ${name}`,
    );
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
      const { outputs, contract } = await buildLeaderboardNavigation();
      for (const [name, text] of outputs) {
        const file = path.join(APP_ROOT, DIRECTORY, name);
        await mkdir(path.dirname(file), { recursive: true });
        await writeFile(file, text);
      }
      await writeFile(
        path.join(APP_ROOT, DIRECTORY, "contract.json"),
        JSON.stringify(contract, null, 2) + "\n",
      );
    } else await verifyLeaderboardNavigation();
    console.log(
      "Original leaderboard navigation verified without captured runtime execution.",
    );
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
