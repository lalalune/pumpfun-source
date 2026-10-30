import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { format } from "prettier";
import { parse } from "@babel/parser";
import { normalizeNavigation } from "./verify-search-navigation.mjs";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  propertyName,
  sha256,
} from "./original-contracts/source.mjs";
const defaultRoot = fileURLToPath(new URL("../", import.meta.url)),
  packet = "reconstruction/top-feed-state";
function declarations(f) {
  return f.node.body.body.flatMap((s) =>
    s.type === "VariableDeclaration"
      ? s.declarations
      : s.type === "FunctionDeclaration"
        ? [s]
        : [],
  );
}
function declaration(f, name) {
  return exactlyOne(
    declarations(f).filter((n) => n.id?.name === name),
    `${f.id} ${name}`,
  );
}
function exportsOf(f, id = f.id) {
  const out = new Map();
  const calls = findNodes(
    f.node,
    (n, parents) =>
      n.type === "CallExpression" &&
      n.callee.type === "MemberExpression" &&
      n.callee.object.name === f.runtime &&
      propertyName(n.callee.property) === "s" &&
      !parents.some(
        (p) =>
          [
            "FunctionDeclaration",
            "FunctionExpression",
            "ArrowFunctionExpression",
          ].includes(p.type) && p !== f.node,
      ),
  );
  for (const c of calls) {
    if (c.arguments[1] && c.arguments[1].value !== id) continue;
    const a = c.arguments[0]?.elements;
    assert.ok(a);
    for (let i = 0; i < a.length; i += 3) {
      assert.equal(a[i + 1]?.value, 0);
      out.set(a[i].value, a[i + 2]);
    }
  }
  return out;
}
function exported(f, key, id = f.id) {
  const n = exportsOf(f, id).get(key);
  assert.ok(n, `${id}.${key}`);
  return n.type === "Identifier"
    ? (declaration(f, n.name).init ?? declaration(f, n.name))
    : n;
}
function imported(f, id) {
  return exactlyOne(
    declarations(f).filter(
      (n) =>
        n.init?.type === "CallExpression" &&
        n.init.callee.object?.name === f.runtime &&
        propertyName(n.init.callee.property) === "i" &&
        n.init.arguments[0]?.value === id,
    ),
    `${f.id} import${id}`,
  );
}
export async function derive(appRoot = defaultRoot) {
  const corpus = await openCorpus(appRoot),
    sources = [],
    witnesses = [];
  async function factory(id, source, role = "runtime source") {
    const rows = corpus.index.modules.filter((m) => m.ids.includes(id));
    if (!source && rows.length === 1 && rows[0].origins.length > 1) {
      let first;
      for (const origin of rows[0].origins) {
        const f = await corpus.factory(id, { source: origin.source });
        sources.push({ ...f.provenance, role });
        if (first)
          assert.equal(
            f.text(),
            first.text(),
            "same-hash repeated physical helper body",
          );
        else first = f;
      }
      return first;
    }
    const f = await corpus.factory(id, source ? { source } : {});
    sources.push({ ...f.provenance, role });
    return f;
  }
  function witness(f, n, label) {
    witnesses.push({ ...f.witness(n, label), astType: n.type });
    return f.text(n);
  }
  function bindings(f, map) {
    return Object.entries(map)
      .map(([id, value]) => {
        const d = imported(f, Number(id));
        witness(f, d, `used import${id}`);
        return `const ${d.id.name}=${value};`;
      })
      .join("\n");
  }
  function privates(f, names, label) {
    return names
      .map((name) => {
        const n = declaration(f, name);
        assert.ok(
          !(
            n.init?.type === "CallExpression" &&
            n.init.callee.object?.name === f.runtime &&
            propertyName(n.init.callee.property) === "i"
          ),
          "private selection cannot include runtime import",
        );
        return n.type === "FunctionDeclaration"
          ? witness(f, n, label)
          : `let ${witness(f, n, label)};`;
      })
      .join("\n");
  }
  const ownerVariants = [],
    ownerCode = [],
    readContexts = [],
    readerCode = [];
  for (const [i, m] of corpus.index.modules
    .filter((m) => m.ids.includes(735821))
    .entries()) {
    const source = m.origins[0].source,
      f = await factory(735821, source),
      holders = await factory(559015, source);
    const holderFn = exported(holders, "h"),
      holderPrivate = exactlyOne(
        findNodes(
          holderFn,
          (n) => n.type === "CallExpression" && n.callee.type === "Identifier",
        ),
        "holder exclusion callee",
      ).callee.name;
    const limit = witness(
      holders,
      exported(holders, "A"),
      "existing followed holders facepile limit",
    );
    readContexts.push({
      source,
      reader: f.provenance.sha256,
      holders: holders.provenance.sha256,
    });
    readerCode.push(`function reader${i}({getContractClient}){${bindings(f, { 759257: "{j:getContractClient}", 559015: `{A:${limit}}` })}return ${witness(f, exported(f, "F"), "complete used top positions GET reader")};}
function holders${i}(){${privates(holders, [holderPrivate], "used username exclusion helper")}return {h:${witness(holders, holderFn, "complete username author exclusion projection; no request or position math")}};}`);
  }
  for (const [i, m] of corpus.index.modules
    .filter((m) => m.ids.includes(364468))
    .entries()) {
    const f = await factory(364468, m.origins[0].source);
    ownerVariants.push({ source: m.origins[0].source, sha256: m.sha256 });
    // Derive the public builder from the actual prefetch and owning-hook calls.
    // Its private spelling differs between retained factories (u versus c).
    const prefetchCall = exactlyOne(
      findNodes(exported(f, "H"), (n) => n.type === "CallExpression" &&
        n.callee.type === "MemberExpression" &&
        propertyName(n.callee.property) === "prefetchQuery"),
      "actual prefetch query call",
    );
    const builderCall = prefetchCall.arguments[0];
    assert.equal(builderCall.type, "CallExpression");
    assert.equal(builderCall.callee.type, "Identifier");
    const queryBuilderName = builderCall.callee.name;
    const queryBuilder = declaration(f, queryBuilderName).init;
    assert.equal(queryBuilder.type, "ArrowFunctionExpression");
    assert.equal(findNodes(queryBuilder, (n) => n.type === "ObjectProperty" &&
      propertyName(n.key) === "queryKey").length, 1);
    assert.equal(findNodes(exported(f, "y"), (n) => n.type === "CallExpression" &&
      n.callee.type === "Identifier" && n.callee.name === queryBuilderName).length, 1);
    ownerCode.push(
      `function owner${i}({useMemoCache,useQuery,reader,normalizerHelpers,engagementHelpers,holderHelpers,isSolanaMint}){${bindings(f, { 445242: "{c:useMemoCache}", 690877: "{useQuery}", 735821: "{F:reader}", 621624: "engagementHelpers", 559015: "holderHelpers", 154703: "normalizerHelpers", 639374: "{f:isSolanaMint}" })}${privates(f, ["o", "d", "c", "u"], "complete used mapper/query/constant private closure")}return{useTopFeed:${witness(f, exported(f, "y"), "complete16-slot TOP feed query/read owner")},prefetchTopFeed:${witness(f, exported(f, "H"), "complete daily top prefetch")},mapEntry:o,queryOptions:${queryBuilderName}};}`,
    );
  }
  const main = await factory(163807),
    topAlias = imported(main, 364468);
  witness(main, topAlias, "actual MAIN top query/prefetch import");
  const calls = findNodes(
    main.node,
    (n) =>
      n.type === "CallExpression" &&
      n.callee.type === "SequenceExpression" &&
      n.callee.expressions.at(-1)?.type === "MemberExpression" &&
      n.callee.expressions.at(-1).object.name === topAlias.id.name,
  );
  assert.deepEqual(
    calls.map((n) => propertyName(n.callee.expressions.at(-1).property)).sort(),
    ["H", "y"],
  );
  for (const n of calls)
    witness(
      main,
      n,
      "actual MAIN used top " +
        propertyName(n.callee.expressions.at(-1).property) +
        " call",
    );
  const enabled = exactlyOne(
    findNodes(
      main.node,
      (n) =>
        n.type === "VariableDeclarator" &&
        n.init?.type === "BinaryExpression" &&
        n.init.operator === "===" &&
        n.init.left?.value === "top",
    ),
    "actual top-tab gate",
  );
  witness(main, enabled, "literal top-tab enable gate; no acquisition");
  const consumed = exactlyOne(
    findNodes(
      main.node,
      (n) =>
        n.type === "VariableDeclarator" &&
        n.init?.type === "CallExpression" &&
        calls.includes(n.init),
    ),
    "actual owner result",
  );
  const handoff = exactlyOne(
    findNodes(
      main.node,
      (n) =>
        n.type === "ObjectProperty" &&
        propertyName(n.key) === "top" &&
        n.value?.type === "ObjectExpression" &&
        findNodes(
          n.value,
          (x) =>
            x.type === "SpreadElement" && x.argument.name === consumed.id.name,
        ).length > 0,
    ),
    "actual top spread/result row handoff",
  );
  witness(main, handoff, "actual top result spread and row-wrapper call");
  const rowCall = exactlyOne(
    findNodes(
      handoff,
      (n) => n.type === "CallExpression" && n.callee.type === "Identifier",
    ),
    "actual shared row wrapper",
  );
  const rowWrapper = witness(
    main,
    declaration(main, rowCall.callee.name).init,
    "existing shared MAIN callout row wrapper, no new helper credit",
  );
  const declarationFactory = await factory(154263),
    route = exactlyOne(
      findNodes(
        declarationFactory.node,
        (n) =>
          n.type === "ObjectProperty" &&
          propertyName(n.key) === "GET /pnl-leaderboard/positions",
      ),
      "actual catalog declaration",
    );
  witness(
    declarationFactory,
    route,
    "captured route/query/response declaration only; no validator implementation",
  );
  const navigationPath = "reconstruction/search-navigation/navigation.mjs",
    navigationBytes = await readFile(path.join(appRoot, navigationPath));
  assert.equal(
    sha256(navigationBytes),
    "3df06f823f7ad2fe9888a640a369c8e26f7566e28dcb6961ac7b89d7e6a7c6c5",
  );
  const navAST = parse(navigationBytes.toString(), { sourceType: "module" }),
    valid = exactlyOne(
      findNodes(
        navAST,
        (n) => n.type === "VariableDeclarator" && n.id.name === "validAddress",
      ),
      "accepted validAddress",
    ).init;
  const sol = await factory(639374),
    rawValid = exported(sol, "f"),
    codec = imported(sol, 344048);
  witness(sol, codec, "accepted decoder namespace; no new codec");
  witness(sol, rawValid, "accepted decoded32 guard attribution only");
  assert.deepEqual(
    normalizeNavigation(
      rawValid,
      {},
      { [`${codec.id.name}.f`]: "value:base58" },
    ),
    normalizeNavigation(
      { ...rawValid, params: valid.params, body: valid.body },
      { base58: "value:base58" },
    ),
  );
  const helperVariants = [],
    helperCodes = [];
  for (const [i, m] of corpus.index.modules
    .filter((m) => m.ids.includes(154703))
    .entries()) {
    const source = m.origins[0].source,
      f = await factory(154703, source, "qualification-only prior1846 helpers"),
      metrics = await factory(
        621624,
        source,
        "qualification-only prior1846 engagement projection",
      );
    helperVariants.push({
      source,
      normalizer: m.sha256,
      engagement: metrics.provenance.sha256,
    });
    const roots = ["l", "v", "s"].map((k) => {
      const n = exportsOf(f).get(k);
      assert.equal(n.type, "Identifier");
      return n.name;
    });
    const predicate = exactlyOne(
      findNodes(
        exported(f, "v"),
        (n) =>
          n.type === "CallExpression" &&
          n.callee.type === "MemberExpression" &&
          propertyName(n.callee.property) === "filter" &&
          n.arguments[0]?.type === "Identifier",
      ),
      "update root predicate",
    );
    const selected = new Set([...roots, predicate.arguments[0].name]),
      names = declarations(f)
        .filter((n) => selected.has(n.id.name))
        .map((n) => n.id.name);
    assert.equal(names.length, 4);
    helperCodes.push(
      `function helpers${i}(){${privates(f, names, "existing1846 timestamp/update/count projection, qualification only")}return{normalizerHelpers:{${["l", "v", "s"].map((k) => `${k}:${witness(f, exported(f, k), "existing1846 namespace " + k + " qualification reuse")}`).join(",")}},engagementHelpers:{P:${witness(metrics, exported(metrics, "P"), "existing1846 engagement projection, qualification reuse only")}}};}`,
    );
  }
  const code = await format(
    `// Complete TOP feed owner/read boundary. Providers and prior helpers remain required capabilities.
import{createSolanaGuards}from'../search-navigation/navigation.mjs';
export const toFeedRows=${rowWrapper};
export const ownerVariants=${JSON.stringify(ownerVariants)};
export const readContexts=${JSON.stringify(readContexts)};
${readerCode.join("\n")}
${ownerCode.join("\n")}
function select(table,key,label){if(typeof key!=='string'||!Object.hasOwn(table,key))throw TypeError('explicit supported '+label+' hash required');return table[key];}
export function createTopFeedRead({ownerVariant,readContext,useMemoCache,useQuery,getContractClient,normalizerHelpers,engagementHelpers,decodeBase58}){
 for(const fn of[useMemoCache,useQuery,getContractClient,normalizerHelpers?.l,normalizerHelpers?.v,normalizerHelpers?.s,engagementHelpers?.P,decodeBase58])if(typeof fn!=='function')throw TypeError('all explicit top read/runtime/helper capabilities required');
 const reader=select({${readContexts.map((x, i) => `${JSON.stringify(x.reader)}:reader${i}`).join(",")}},readContext,'reader')({getContractClient});
 const holderHelpers=select({${readContexts.map((x, i) => `${JSON.stringify(x.reader)}:holders${i}`).join(",")}},readContext,'holder context')();
 const owner=select({${ownerVariants.map((x, i) => `${JSON.stringify(x.sha256)}:owner${i}`).join(",")}},ownerVariant,'owner')({useMemoCache,useQuery,reader,normalizerHelpers,engagementHelpers,holderHelpers,isSolanaMint:createSolanaGuards({base58:{decode:decodeBase58}}).validAddress});
 return{...owner,readPositions:reader};
}
`,
    { parser: "babel" },
  );
  const fixture = await format(
    `// Qualification-only source-bound reuse of prior1846 namespaces; no new helper credit.
export const helperVariants=${JSON.stringify(helperVariants)};
${helperCodes.join("\n")}
export function createHelperPorts(variant){const table={${helperVariants.map((x, i) => `${JSON.stringify(x.normalizer)}:helpers${i}`).join(",")}};if(typeof variant!=='string'||!Object.hasOwn(table,variant))throw TypeError('explicit supported1846 helper context required');return table[variant]();}
`,
    { parser: "babel" },
  );
  parse(code, { sourceType: "module" });
  parse(fixture, { sourceType: "module" });
  const contract = {
    schemaVersion: 1,
    title: "Complete original MAIN TOP feed read owner",
    anchors: corpus.anchors,
    sources,
    witnesses,
    ownerVariants,
    readContexts,
    qualificationHelperVariants: helperVariants,
    accepted: [
      {
        path: navigationPath,
        bytes: navigationBytes.length,
        sha256: sha256(navigationBytes),
      },
    ],
    generatedSha256: sha256(code),
    qualificationHelperSha256: sha256(fixture),
    ports: [
      "445242.c compiler memo cache",
      "690877.useQuery exact query/result/refetch API",
      "759257.j required namedoperationfactory; no default destination",
      "154703.l/v/s and621624.P prior1846 exact original namespaces; qualification reuse only",
      "344048 decode input to accepted639374 guard",
    ],
    semantics: {
      reader:
        "GET /pnl-leaderboard/positions; daily default; optional includeFollowedHolders adds true and limit5; credentials include/JSONheader/signal/nonOK plainError; success body unvalidated",
      owner:
        "Full16slots, option defaults, refetchOnWindowFocus true, stable raw entries reference memo, first mapped key dedup, empty-row error condition, refetch discards returned Promise",
      map: "Null callout/note/id and invalid decoded32 mint excluded; note trimmed; timestamp/update/count/engagement original ports; username-case holder author exclusion; optional media/metadata fields retained",
      prefetch:
        "Daily query descriptor, includeFollowedHolders false default; returns original queryclient prefetch result",
      result:
        "Pending0/preview singleton empty/sharednoops/no next page; queryloading gated enabled; error when isError and no mapped rows",
    },
    scope: {
      owner: "complete364468y/H/privateclosure both physicalvariants",
      caller:
        "actual163807top-tab owner call/result handoff +prefetch call; outer Home/UI/provider acquisition excluded",
      helpers:
        "Used559015h/l andA, reader735821F complete; prior1846 helpers/engagement remain credited ports",
    },
    limits: [
      "No original loader/providerwinner/mountedUI/personalizeddata/queryscheduler/browser-cookie/CORS/auth/service qualification",
      "No ranking/price/financial/accounting/oracle calculation or native/feature/security qualification",
      "No other735821 methods/559015reader or position aggregation/621624 optimistic-write arithmetic",
      "Captured bundles never executed; generated source is a maintained injected boundary",
      "Contract gate compares parsedJSON semantics, not canonicalJSON bytes",
    ],
    mounted: false,
    productionOperationsQualified: 0,
  };
  return { code, fixture, contract };
}
export async function verify(appRoot = defaultRoot, supplied) {
  const d = await derive(appRoot),
    dir = path.join(appRoot, packet);
  assert.equal(
    supplied?.code ?? (await readFile(path.join(dir, "client.mjs"), "utf8")),
    d.code,
  );
  assert.equal(
    supplied?.fixture ??
      (await readFile(
        path.join(dir, "qualification/helper-ports.mjs"),
        "utf8",
      )),
    d.fixture,
  );
  assert.deepEqual(
    supplied?.contract ??
      JSON.parse(await readFile(path.join(dir, "contract.json"), "utf8")),
    d.contract,
  );
  return {
    witnesses: d.contract.witnesses.length,
    sourceEntries: d.contract.sources.length,
    ownerVariants: d.contract.ownerVariants.length,
    readContexts: d.contract.readContexts.length,
    qualificationHelperVariants: d.contract.qualificationHelperVariants.length,
    mounted: false,
    productionOperationsQualified: 0,
  };
}
async function main() {
  let root = defaultRoot,
    mode;
  const args = process.argv.slice(2);
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--app-root" && args[i + 1]) root = path.resolve(args[++i]);
    else if (["--write", "--check"].includes(args[i]) && !mode) mode = args[i];
    else
      throw Error(
        "usage: original-top-feed-state.mjs [--app-root PATH] --write|--check",
      );
  }
  if (!mode) throw Error("explicit mode required");
  if (mode === "--write") {
    const d = await derive(root);
    await mkdir(path.join(root, packet, "qualification"), { recursive: true });
    await writeFile(path.join(root, packet, "client.mjs"), d.code);
    await writeFile(
      path.join(root, packet, "qualification/helper-ports.mjs"),
      d.fixture,
    );
    await writeFile(
      path.join(root, packet, "contract.json"),
      JSON.stringify(d.contract, null, 2) + "\n",
    );
  }
  console.log(JSON.stringify(await verify(root)));
}
if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
)
  await main();
