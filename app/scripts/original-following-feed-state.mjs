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
  packet = "reconstruction/following-feed-state";
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
  const main = await factory(163807),
    ns = await factory(646908),
    mint = await factory(605587),
    sol = await factory(639374),
    shape = await factory(975982),
    perps = await factory(21617),
    collectible = await factory(265129),
    entry = await factory(16503),
    cap = await factory(349879),
    decl = await factory(236187),
    protocol = await factory(390146);
  const frameCall = exactlyOne(
    findNodes(
      main.node,
      (n) =>
        n.type === "CallExpression" &&
        n.callee.type === "ArrowFunctionExpression" &&
        main.text(n.callee).includes("bufferNewCallouts") &&
        main.text(n.callee).includes("pendingNewCount:"),
    ),
    "complete following owner",
  );
  const frame = witness(
    main,
    frameCall.callee,
    "complete inlineFOLLOWING read-state owner",
  );
  witness(main, frameCall, "actual following owner input call");
  const queryPrivate = privates(
    main,
    ["et", "el", "ed", "ec"],
    "complete used following query/key/surface declaration",
  );
  const contextFiles = [
    "evidence/web/objects/3740fc4e7a24596d.js",
    "evidence/web/objects/cf2bb278631744da.js",
  ];
  const contexts = [],
    readerCode = [],
    chainCode = [];
  for (let i = 0; i < contextFiles.length; i++) {
    const source = contextFiles[i],
      r = await factory(735821, source),
      c = await factory(637172, source);
    contexts.push({
      source,
      reader: r.provenance.sha256,
      chain: c.provenance.sha256,
    });
    readerCode.push(
      `function reader${i}({getContractClient,kindsSchema}){${bindings(r, { 402030: '{contract:{"GET /following-positions/alerts":{query:{shape:{kinds:kindsSchema}}}}}', 759257: "{j:getContractClient}" })}return{read:${witness(r, exported(r, "r"), "complete following list reader")},kinds:${witness(r, exportsOf(r).get("G"), "actual classic following kind set")},assets:${witness(r, exported(r, "E", 917341), "credited existing asset field projection")}};}`,
    );
    chainCode.push(
      `function chain${i}({namespace,mint,isSolanaMint,perpsChain}){${bindings(c, { 646908: "namespace", 605587: "mint", 639374: "{f:isSolanaMint}", 21617: "{g:perpsChain}" })}${privates(c, [exportsOf(c).get("w").name, "u", "h", "f"], "complete used chain-filter private closure")}return{m:${witness(c, exported(c, "m"), "complete query chain filter")},R:${witness(c, exported(c, "R"), "complete filter key encoding")},N:${witness(c, exported(c, "N"), "complete row chain predicate")}};}`,
    );
  }
  assert.deepEqual(
    new Set(
      corpus.index.modules
        .filter((m) => m.ids.includes(735821))
        .map((m) => m.sha256),
    ),
    new Set(contexts.map((c) => c.reader)),
  );
  assert.deepEqual(
    new Set(
      corpus.index.modules
        .filter((m) => m.ids.includes(637172))
        .map((m) => m.sha256),
    ),
    new Set(contexts.map((c) => c.chain)),
  );
  const namespaceCode = `function namespace(){${privates(ns, ["r", "n", "i", "a", "d"], "used exact namespace literal")}return{${["C", "L", "B", "_", "h", "Q", "z", "J", "W", "d"].map((key) => `${JSON.stringify(key)}:${witness(ns, exported(ns, key), "used namespace predicate/literal " + key)}`).join(",")}};}`;
  const mintCode = `function mintNamespace(){return{h:${witness(mint, exported(mint, "h"), "used exact40hex predicate")},w:${witness(mint, exported(mint, "w"), "used chain-id prefix strip")}};}`;
  witness(
    sol,
    exported(sol, "f"),
    "accepted639374 decoded32 guard reused; no new predicate/codec",
  );
  witness(
    shape,
    exported(shape, "k"),
    "accepted975982 shape-only helper reused, distinct from decoded guard",
  );
  const navigationPath = "reconstruction/search-navigation/navigation.mjs",
    navigationBytes = await readFile(path.join(appRoot, navigationPath));
  assert.equal(
    sha256(navigationBytes),
    "3df06f823f7ad2fe9888a640a369c8e26f7566e28dcb6961ac7b89d7e6a7c6c5",
  );
  const navigationAST = parse(navigationBytes.toString("utf8"), {
    sourceType: "module",
  });
  const valid = exactlyOne(
    findNodes(
      navigationAST,
      (n) => n.type === "VariableDeclarator" && n.id.name === "validAddress",
    ),
    "accepted validAddress",
  ).init;
  const rawValid = exported(sol, "f");
  const codecAlias = imported(sol, 344048);
  witness(sol, codecAlias, "existing344048 codec API only");
  assert.deepEqual(
    normalizeNavigation(
      rawValid,
      {},
      { [`${codecAlias.id.name}.f`]: "value:base58" },
    ),
    normalizeNavigation(
      { ...rawValid, params: valid.params, body: valid.body },
      { base58: "value:base58" },
    ),
  );
  const perpsLiteral = witness(
    perps,
    exported(perps, "g"),
    "used perp namespace literal only",
  );
  const imageVariants = [],
    imageCode = [];
  for (const [i, m] of corpus.index.modules
    .filter((m) => m.ids.includes(549613))
    .entries()) {
    assert.equal(m.origins.length, 1);
    const f = await factory(549613, m.origins[0].source);
    imageVariants.push({ source: m.origins[0].source, sha256: m.sha256 });
    const names = declarations(f).map((n) => n.id.name);
    imageCode.push(
      `function image${i}(){${privates(f, names, "complete used pure image/provider-string closure")}return ${witness(f, exported(f, "G"), "complete pure image/provider normalization; no fetch")};}`,
    );
  }
  const classVariants = [],
    classCode = [];
  for (const [i, m] of corpus.index.modules
    .filter((m) => m.ids.includes(662986))
    .entries()) {
    assert.equal(m.origins.length, 1);
    const f = await factory(662986, m.origins[0].source);
    classVariants.push({ source: m.origins[0].source, sha256: m.sha256 });
    const base = exportsOf(f).get("I");
    assert.equal(base.type, "Identifier");
    classCode.push(
      `function classification${i}({mint,shape,perpsChain}){${bindings(f, { 605587: "mint", 975982: "{k:shape}", 21617: "{g:perpsChain}" })}${privates(f, ["c", "u", base.name, "x", "h"], "complete used entry classification closure")}return ${witness(f, exported(f, "l"), "complete row type classification; no perps service")};}`,
    );
  }
  const entryCode = `function entries({normalizerHelpers,assets,classify,namespace,collectibleImage}){const collectible=(()=>{${bindings(collectible, { 549613: "{G:collectibleImage}" })}${privates(collectible, ["n"], "used metadata trim closure")}return ${witness(collectible, exported(collectible, "q"), "complete collectible metadata projection")};})();${bindings(entry, { 265129: "{q:collectible}", 917341: "{E:assets}", 154703: "normalizerHelpers", 662986: "{l:classify}", 287129: "{j:mapUserReplyRow,m:mapReplyCallout}", 646908: "namespace" })}${privates(entry, ["o", "s", "u", "c"], "complete used entry mapping closure")}return{o:${witness(entry, exported(entry, "o"), "complete seven-kind entry mapping including null fallbacks")},D:${witness(entry, exported(entry, "D"), "complete mapped-entry chain input")}};}`;
  const kindsEnum = declaration(decl, "u");
  witness(
    decl,
    kindsEnum,
    "actual nine-kind declaration, Zod parse runtime external",
  );
  const getDecl = exactlyOne(
    findNodes(
      decl.node,
      (n) =>
        n.type === "ObjectProperty" &&
        propertyName(n.key) === "GET /following-positions/alerts",
    ),
    "actual following route declaration",
  );
  witness(
    decl,
    getDecl,
    "full declared GET operation, no server implementation",
  );
  const eventFn = exported(protocol, "f", 106009),
    observerFn = exported(protocol, "f", 390146),
    metricFn = exported(protocol, "Q", 572128);
  witness(
    protocol,
    eventFn,
    "complete original event hook as external API witness only; presence acquisition excluded",
  );
  witness(
    protocol,
    observerFn,
    "complete first-rows observation hook as external API witness only",
  );
  witness(
    protocol,
    metricFn,
    "complete telemetry normalization callback as external API witness only; delivery excluded",
  );
  const acceptedPath = "reconstruction/user-replies/client.mjs",
    acceptedBytes = await readFile(path.join(appRoot, acceptedPath));
  const memo = witness(cap, exported(cap, "I"), "actual pending preview cap");
  const code = await format(
    `// Full selected following read owner. Required runtimes/providers are explicit capabilities.
import{mapUserReplyRow,mapReplyCallout}from'../user-replies/client.mjs';
import{createSolanaGuards,isSolanaText}from'../search-navigation/navigation.mjs';
export const readContexts=${JSON.stringify(contexts)};
export const imageVariants=${JSON.stringify(imageVariants)};
export const classificationVariants=${JSON.stringify(classVariants)};
${namespaceCode}${mintCode}
${readerCode.join("\n")}${chainCode.join("\n")}${imageCode.join("\n")}${classCode.join("\n")}${entryCode}
function select(table,key,label){if(typeof key!=='string'||!Object.hasOwn(table,key))throw TypeError('explicit supported '+label+' hash required');return table[key];}
export function createFollowingFeedRead({readContext,imageVariant,classificationVariant,React,useInfiniteQuery,useQueryClient,getContractClient,kindsSchema,useFollowingEvents,useFirstRowsObserver,recordRefresh,normalizerHelpers,decodeBase58,clock}){
 for(const fn of[React?.useMemo,React?.useState,React?.useRef,React?.useCallback,useInfiniteQuery,useQueryClient,getContractClient,kindsSchema?.parse,useFollowingEvents,useFirstRowsObserver,recordRefresh,normalizerHelpers?.g,normalizerHelpers?.v,normalizerHelpers?.s,decodeBase58,clock?.now])if(typeof fn!=='function')throw TypeError('all explicit following read/runtime/schema/event/observer/helper capabilities required');
 const Date=clock,ns=namespace(),mint=mintNamespace(),perpsChain=${perpsLiteral};
 const reader=select({${contexts.map((r, i) => `${JSON.stringify(r.reader)}:reader${i}`).join(",")}},readContext,'read context')({getContractClient,kindsSchema});
 const chains=select({${contexts.map((r, i) => `${JSON.stringify(r.reader)}:chain${i}`).join(",")}},readContext,'chain context')({namespace:ns,mint,isSolanaMint:createSolanaGuards({base58:{decode:decodeBase58}}).validAddress,perpsChain});
 const image=select({${imageVariants.map((r, i) => `${JSON.stringify(r.sha256)}:image${i}`).join(",")}},imageVariant,'image')();
 const classify=select({${classVariants.map((r, i) => `${JSON.stringify(r.sha256)}:classification${i}`).join(",")}},classificationVariant,'classification')({mint,shape:isSolanaText,perpsChain});
 const rows=entries({normalizerHelpers,assets:reader.assets,classify,namespace:ns,collectibleImage:image});
 ${bindings(main, { 352386: "React", 761459: "{useInfiniteQuery}", 606933: "{useQueryClient}", 390146: "{f:useFirstRowsObserver}", 106009: "{f:useFollowingEvents}", 572128: "{Q:recordRefresh}", 735821: "{r:reader.read,G:reader.kinds}", 16503: "rows", 637172: "chains", 349879: `{I:${memo}}` })}
 ${queryPrivate}
 const useFollowingFeed=${frame};
 return{useFollowingFeed,readAlerts:reader.read,queryOptions:ec,normalizeEntry:rows.o,entryChain:rows.D};
}
`,
    { parser: "babel" },
  );
  const helperCodes = [],
    helperVariants = [];
  for (const [i, m] of corpus.index.modules
    .filter((m) => m.ids.includes(154703))
    .entries()) {
    assert.equal(m.origins.length, 1);
    const f = await factory(
      154703,
      m.origins[0].source,
      "qualification-only reuse of1846 helpers",
    );
    helperVariants.push({ source: m.origins[0].source, sha256: m.sha256 });
    const roots = ["g", "v", "s"].map((key) => {
      const n = exportsOf(f).get(key);
      assert.equal(n.type, "Identifier");
      return n.name;
    });
    const update = exported(f, "v");
    const predicate = exactlyOne(
      findNodes(
        update,
        (n) =>
          n.type === "CallExpression" &&
          n.callee.type === "MemberExpression" &&
          propertyName(n.callee.property) === "filter" &&
          n.arguments[0]?.type === "Identifier",
      ),
      "update root predicate",
    );
    const date = exactlyOne(
      findNodes(
        update,
        (n) =>
          n.type === "ObjectProperty" &&
          propertyName(n.key) === "createdAt" &&
          n.value.type === "CallExpression" &&
          n.value.callee.type === "Identifier",
      ),
      "update timestamp helper",
    );
    const selected = new Set([
      ...roots,
      predicate.arguments[0].name,
      date.value.callee.name,
    ]);
    const names = declarations(f)
      .filter((n) => selected.has(n.id.name))
      .map((n) => n.id.name);
    assert.equal(names.length, 5);
    helperCodes.push(
      `function helpers${i}(){${privates(f, names, "qualified1846 helper reuse only, not a new helper recovery")}return{${["g", "v", "s"].map((key) => `${key}:${witness(f, exported(f, key), "existing1846 original namespace export " + key + "; qualification only")}`).join(",")}};}`,
    );
  }
  const fixture = await format(
    `// Source-bound reuse of already-recovered1846 helpers ONLY for qualification. Runtime client requires the original namespace capability.
export const helperVariants=${JSON.stringify(helperVariants)};
${helperCodes.join("\n")}
export function createNormalizerHelpers(variant){const table={${helperVariants.map((r, i) => `${JSON.stringify(r.sha256)}:helpers${i}`).join(",")}};if(typeof variant!=='string'||!Object.hasOwn(table,variant))throw TypeError('explicit supported1846 helper hash required');return table[variant]();}
`,
    { parser: "babel" },
  );
  parse(code, { sourceType: "module" });
  parse(fixture, { sourceType: "module" });
  const contract = {
    schemaVersion: 1,
    title: "Complete following feed read/query and pending-event state",
    anchors: corpus.anchors,
    sources,
    witnesses,
    readContexts: contexts,
    imageVariants,
    classificationVariants: classVariants,
    qualificationHelperVariants: helperVariants,
    accepted: [
      {
        path: acceptedPath,
        bytes: acceptedBytes.length,
        sha256: sha256(acceptedBytes),
      },
      {
        path: navigationPath,
        bytes: navigationBytes.length,
        sha256: sha256(navigationBytes),
      },
    ],
    generatedSha256: sha256(code),
    qualificationHelperSha256: sha256(fixture),
    ports: [
      "React hooks +infinite query/cache/observer runtime",
      "759257.j exact namedoperation clientfactory; no destination",
      "actual catalog kindsSchema.parse; Zodruntime/errorformat external",
      "106009.f eventhook,390146.f observerhook,572128.Q telemetrycallback exact original APIs; no presence/provider/delivery implementation",
      "154703g/v/s original namespace required; existing1846 credited, qualification-only reuse included",
      "344048 base58 decode; injectedDate.now clock; all parsing keeps native hostDate.parse across emitted and accepted/reused helpers",
    ],
    scope: {
      owner:
        "entire inline163807 FOLLOWING read owner and ec/et/el/ed; outertab/provider/reset effects external",
      reader:
        "735821.r both physicalcontexts,classicG kind list; actual schema parse call retained",
      mapping:
        "16503.o/D complete all branches +usedpure chain/metadata/classification closure; accepted287129 maps reused unchanged",
    },
    semantics: {
      cursor:
        "nextCursor nullish→null, continue when not null and !== previouspageParam only",
      rows: "first mapped key dedup BEFORE chain filter, wire page order; mapper nulls omitted",
      events:
        "viewer null-only gate;5s throttle on empty cache or bufferingfalse; otherwise rawid dedup enqueue",
      pending:
        "viewer+chain identity resets pending duringrender; preview excludes only nullcoinMint and caps actual349879.I",
      reveal:
        "clearpending→firstpage cachetrim→invalidate.then telemetry; callback returnsundefined and adds no catch",
      results:
        "query-error shown only when no data; exact loading/hasNext/fetchNext guards",
    },
    limits: [
      "No originalactiveconfiguration/providerwinner/mountedUI/currentdata",
      "No networkacquisition/personalizedservice/currentcookies/auth/presence/mutation/telemetrydelivery",
      "Required schema/query/event/observer/helper ports are not default no-ops; qualification supplies explicit synthetic capabilities",
      "Acceptedsearch-navigation decoded32guard/shapehelper reused separately, credit existingproof +1943attribution; no newpredicate/codec/identityqualification. No financial/accounting/oracle/perpsservice/feature/native/securityqualification; captures/ledgers/priorpackets unchanged",
      "Sourcecontractgate comparesparsedJSONsemantic values, notcanonicalJSONformatting",
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
    readContexts: d.contract.readContexts.length,
    imageVariants: d.contract.imageVariants.length,
    classificationVariants: d.contract.classificationVariants.length,
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
        "usage: original-following-feed-state.mjs [--app-root PATH] --write|--check",
      );
  }
  if (!mode) throw Error("explicit --write or --check required");
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
