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
  propertyName,
  sha256,
} from "./original-contracts/source.mjs";
import { normalizeSession, verifySession } from "./verify-search-session.mjs";
import { verifyPlanner } from "./verify-search-planner.mjs";
import { verifyMarketBoardBindings } from "./verify-market-board-bindings.mjs";

export const APP_ROOT = fileURLToPath(new URL("..", import.meta.url));
export const DIRECTORY = "reconstruction/board-read-state";
const HOOKS = [
  [
    "dba17a249156c6ff.js",
    "642cafc9d2b3c27f2d2d35ea8699a509ded856839fb3d33a8a132333d85c82d6",
  ],
  [
    "baaa37ea4eff7a5d.js",
    "629ccc425314ef1e01dd2476266052df9bcb407199598ebba7f8ce9f52adc2d6",
  ],
  [
    "31d5c1d669eab8ef.js",
    "3c58de415e19118992ecc37931a72eaf74272cfab0b7c7dc68fd9f4f402abd4d",
  ],
  [
    "767cc801e3f88f8b.js",
    "350da5b767415ae168c12050d3627d71039bcc2c0a097572b5319ddbad04d8fe",
  ],
];
const EXPORTS = {
  148269: ["E"],
  352386: ["useState", "useRef", "useCallback", "useEffect"],
  751275: ["y"],
  503774: ["$"],
  369091: ["useIpfsPrefix"],
  574472: ["F"],
  293205: ["useSession"],
  192: ["d"],
  541710: ["l", "M"],
  231824: ["f"],
  583448: ["f", "$"],
  759257: ["f"],
  997887: ["l"],
  493025: ["f"],
  930234: ["f"],
  646908: ["a"],
  569124: ["m", "K"],
  346431: ["W", "x"],
  402030: ["contract"],
  536925: ["t"],
  85324: ["q"],
  182303: ["i"],
};
const GLOBALS = Object.fromEntries(
  [
    "JSON",
    "Date",
    "Error",
    "fetch",
    "AbortController",
    "URLSearchParams",
    "setInterval",
    "clearInterval",
    "console",
    "String",
  ].map((n) => [n, "global:" + n]),
);
function bindings(n) {
  if (!n) return [];
  if (n.type === "Identifier") return [n.name];
  if (n.type === "AssignmentPattern") return bindings(n.left);
  if (n.type === "ObjectPattern")
    return n.properties.flatMap((p) => bindings(p.value));
  if (n.type === "ArrayPattern") return n.elements.flatMap(bindings);
  throw Error("Unsupported board binding " + n.type);
}
function shadowed(name, parents) {
  return parents.some(
    (p) =>
      ((p.type === "FunctionExpression" ||
        p.type === "ArrowFunctionExpression") &&
        p.params.flatMap(bindings).includes(name)) ||
      (p.type === "BlockStatement" &&
        p.body
          .filter((n) => n.type === "VariableDeclaration")
          .flatMap((n) => n.declarations)
          .flatMap((n) => bindings(n.id))
          .includes(name)) ||
      (p.type === "CatchClause" && bindings(p.param).includes(name)),
  );
}
// The reused alpha comparator supports object bindings. This lossless tuple
// representation retains position/arity and an explicit marker, not a mask.
function tuples(value) {
  if (Array.isArray(value)) return value.map(tuples);
  if (!value || typeof value !== "object") return value;
  if (value.type === "ArrayPattern") {
    assert.ok(value.elements.every((n) => n && n.type !== "RestElement"));
    return {
      type: "ObjectPattern",
      boardTuplePattern: true,
      properties: value.elements.map((n, i) => ({
        type: "ObjectProperty",
        key: { type: "NumericLiteral", value: i },
        value: tuples(n),
        computed: false,
        shorthand: false,
      })),
    };
  }
  return Object.fromEntries(
    Object.entries(value).map(([k, v]) => [k, tuples(v)]),
  );
}
const declarations = (f) =>
  f.node.body.body.flatMap((n) =>
    n.type === "VariableDeclaration" ? n.declarations : [],
  );
function exported(f, id, name) {
  const call = exactlyOne(
    findNodes(
      f.node,
      (n) =>
        n.type === "CallExpression" &&
        member(n.callee, f.runtime, "s") &&
        (n.arguments[1]?.value === id ||
          (!n.arguments[1] && f.ids.includes(id))) &&
        n.arguments[0]?.type === "ArrayExpression" &&
        n.arguments[0].elements.some((n) => n?.value === name),
    ),
    "actual export" + id + "." + name,
  );
  const values = call.arguments[0].elements,
    at = values.findIndex((n) => n?.value === name);
  const result = values[at + 2];
  return result.type === "Identifier"
    ? exactlyOne(
        declarations(f).filter((n) => n.id.name === result.name),
        "export binding",
      ).init
    : result;
}
function context(f, fn) {
  const ds = declarations(f);
  const imports = new Map(
    ds
      .filter(
        (n) =>
          n.init?.type === "CallExpression" &&
          member(n.init.callee, f.runtime, "i"),
      )
      .map((n) => [n.id.name, n.init.arguments[0].value]),
  );
  const qualified = {};
  for (const n of findNodes(fn, (n, parents) => {
    if (
      n.type !== "MemberExpression" ||
      n.computed ||
      !imports.has(n.object?.name)
    )
      return false;
    const id = imports.get(n.object.name),
      prop = propertyName(n.property);
    if (!EXPORTS[id]?.includes(prop)) return false;
    assert.equal(
      shadowed(n.object.name, parents),
      false,
      "namespace shadowing: " + n.object.name + "." + prop,
    );
    return true;
  }))
    qualified[n.object.name + "." + propertyName(n.property)] =
      "operation:" +
      imports.get(n.object.name) +
      "." +
      propertyName(n.property);
  const roles = { ...GLOBALS };
  for (const n of ds) {
    if (n.init?.type === "NewExpression" && n.init.callee.name === "Map")
      roles[n.id.name] = "module:query-cache";
    if (n.init?.type === "ArrayExpression" && n.init.elements.length === 0)
      roles[n.id.name] = "module:empty-coins";
    if (
      n.init?.type === "ArrowFunctionExpression" &&
      findNodes(
        n.init,
        (n) =>
          n.type === "ObjectProperty" && propertyName(n.key) === "storedAt",
      ).length
    )
      roles[n.id.name] = "module:cache-store";
    if (
      n.init?.type === "ArrowFunctionExpression" &&
      findNodes(
        n.init,
        (n) =>
          n.type === "MemberExpression" &&
          propertyName(n.property) === "FEATURED",
      ).length
    )
      roles[n.id.name] = "module:board-sort-predicate";
    if (
      n.init?.type === "SequenceExpression" &&
      findNodes(
        n.init,
        (n) =>
          n.type === "AssignmentExpression" &&
          propertyName(n.left?.property) === "ASC",
      ).length
    )
      roles[n.id.name] = "module:sort-order";
  }
  return { roles, qualified, imports };
}
function normalized(fn, ctx) {
  return normalizeSession(tuples(fn), ctx.roles, ctx.qualified);
}
function variable(fn, name) {
  return exactlyOne(
    findNodes(
      fn,
      (n) => n.type === "VariableDeclarator" && n.id?.name === name,
    ),
    "hook variable " + name,
  );
}
const cite = (f, n, label) => ({ ...f.witness(n, label), text: f.text(n) });

export async function recover(root = APP_ROOT) {
  const corpus = await openCorpus(root),
    factories = [],
    functions = [],
    contexts = [],
    proof = [];
  assert.deepEqual(
    corpus.index.modules
      .filter((m) => m.ids.includes(379705))
      .map((m) => m.sha256)
      .sort(),
    HOOKS.map((r) => r[1]).sort(),
    "all four hook variants must remain explicit",
  );
  let canonical;
  for (const [file, hash] of HOOKS) {
    const f = await corpus.factory(379705, {
      source: "evidence/web/objects/" + file,
    });
    assert.equal(f.provenance.sha256, hash, "review required for hook source");
    const fn = exported(f, 379705, "f"),
      ctx = context(f, fn),
      value = normalized(fn, ctx);
    if (canonical)
      assert.deepEqual(value, canonical, "complete hook variants differ");
    else canonical = value;
    factories.push(f);
    functions.push(fn);
    contexts.push(ctx);
    proof.push({
      factory: f.provenance,
      fullHook: f.witness(fn, "complete owning hook"),
      normalizedSha256: sha256(JSON.stringify(value)),
      roles: ctx.roles,
      qualifiedImports: ctx.qualified,
    });
  }
  const source = factories[0],
    fn = functions[0],
    ctx = contexts[0];
  const providerConstants = [];
  for (const f of factories) {
    const interval = await corpus.factory(182303, {
      source: f.provenance.source,
    });
    const intervalValue = exported(interval, 182303, "i");
    assert.equal(intervalValue.value, 60000);
    const calls = await corpus.factory(346431, { source: f.provenance.source });
    const callsValue = exported(calls, 346431, "W");
    assert.equal(callsValue.value, "1h");
    providerConstants.push({
      intervalFactory: interval.provenance,
      interval: cite(
        interval,
        intervalValue,
        "actual LIVE interval constant, disabled for board domain",
      ),
      callsFactory: calls.provenance,
      callsWindow: cite(
        calls,
        callsValue,
        "actual default request-key calls window",
      ),
    });
  }
  const pauseSources = [];
  for (const [file, hash] of [
    [
      "b7df9c4704b957ab.js",
      "67966a7a877f6aaeac36c545415ddfc2d534bcb892a9b11c56e45a5aa5560cfc",
    ],
    [
      "7128bd47b219d222.js",
      "0024317d4e63db1b1791329f7416024563bc11858041efaa1e185556e58baae1",
    ],
  ]) {
    const f = await corpus.factory(85324, {
      source: "evidence/web/objects/" + file,
    });
    assert.equal(f.provenance.sha256, hash);
    pauseSources.push({
      factory: f.provenance,
      gate: cite(
        f,
        exported(f, 85324, "q"),
        "actual enabled/foreground/number interval gate; board enabled input is false",
      ),
      qualification:
        "Provider hook is NOT supplied by this adapter; actual false result is required for disabled board input, no invented polling",
    });
  }
  const identitySources = [];
  for (const [file, hash] of [
    [
      "3740fc4e7a24596d.js",
      "9ca16f081716f491ff43aa662ac181e556e4ff2a28b77be4cbbf3a1431b9087f",
    ],
    [
      "cf2bb278631744da.js",
      "0596b668b2aca36cff2b18017d76bdc97bfb3b4fbb630528bef49e1bdd57869a",
    ],
  ]) {
    const f = await corpus.factory(231824, {
      source: "evidence/web/objects/" + file,
    });
    assert.equal(f.provenance.sha256, hash);
    identitySources.push({
      factory: f.provenance,
      selector: cite(
        f,
        exported(f, 231824, "f"),
        "actual identity helper call/result contract only; acquisition excluded",
      ),
      qualification:
        "Explicit port only: result carries deviceId/sessionId/sessionStartTimestampMs, not country. Original default getter/device acquisition is NOT imported, executed or implemented.",
    });
  }
  const executor = variable(fn, "eR").init.arguments[0],
    query = variable(fn, "eA").init.arguments[0];
  assert.equal(executor.async, true);
  assert.equal(query.type, "ArrowFunctionExpression");
  const execText = `createSearchExecutor({offset:c,limit:f,ipfsPrefix:ef,socialTerminal:Q},{entries:M,store:L,requestKeyRef:ea,loadedKeyRef:es,sequenceRef:ep,abortRef:ew,setCoins:B,setPageSize:ee,setHasNextPage:z,setLoadedKey:en,setErrorKey:ei,setLoading:J,setServedCoins:V,emptyCoins:N,getContractClient:excludedOperation,fetchResponse,parseBoard,now:nowMs,AbortController:Controller})`;
  const queryText = `args=>buildCoinSearchQuery(args,{limit:f,includeNsfw:h,creator:D,sessionId:em},requestIdentity)`;
  let body = source.text(fn);
  for (const [node, replacement] of [
    [executor, execText],
    [query, queryText],
  ].sort((a, b) => b[0].start - a[0].start))
    body =
      body.slice(0, node.start - fn.start) +
      replacement +
      body.slice(node.end - fn.start);
  const predicate = exactlyOne(
    declarations(source).filter(
      (n) => ctx.roles[n.id.name] === "module:board-sort-predicate",
    ),
    "original board predicate",
  ).init;
  const text = await prettier.format(
    `
import {buildBoardRequest} from '../market-boards/request.mjs';
import {createSearchExecutor} from '../search-session/session.mjs';
import {SEARCH_SORT,buildCoinSearchQuery} from '../search-planner/planner.mjs';
// No implicit fetch, destination, identity, session, response decoder or provider.
export function createBoardCoinHook({React,cache,baseUrl,fetchResponse,parseBoard,seedBoardCoins,nowMs,AbortController:Controller,useViewerSnapshot,useSessionSnapshot,usePrimarySessionIdSnapshot,useVariant,useExposure,useIpfsPrefix,requestIdentity,debounce,useLivePollInterval,timers,logger}){
  const capabilities={fetchResponse,parseBoard,seedBoardCoins,nowMs,Controller,useViewerSnapshot,useSessionSnapshot,usePrimarySessionIdSnapshot,useVariant,useExposure,useIpfsPrefix,requestIdentity,debounce,useLivePollInterval};
  for(const [name,value]of Object.entries(capabilities))if(typeof value!=='function')throw new TypeError('Explicit board capability required: '+name);
  if(!(cache?.entries instanceof Map)||typeof cache.store!=='function'||typeof baseUrl!=='string')throw new TypeError('Explicit shared cache and destination are required');
  if(!['useState','useRef','useCallback','useEffect'].every(name=>typeof React?.[name]==='function'))throw new TypeError('Explicit React hooks are required');
  if(typeof timers?.setInterval!=='function'||typeof timers?.clearInterval!=='function'||typeof logger?.error!=='function')throw new TypeError('Explicit timer/logger capabilities are required');
  const excludedOperation=()=>{throw new TypeError('Non-board request is outside this adapter domain');};
  const r={get contract(){return excludedOperation();}},n={F:useViewerSnapshot},l=React,i={t:debounce},u={y:useVariant},a={i:60000},s={E:SEARCH_SORT},d={ASC:'ASC',DESC:'DESC'},
    y={q:useLivePollInterval},S={W:'1h',x:excludedOperation},p={l:useExposure,M:excludedOperation},w={a:excludedOperation},k={f:requestIdentity},b={d:usePrimarySessionIdSnapshot},T={m:excludedOperation,K:excludedOperation},v={useIpfsPrefix},C={useSession:useSessionSnapshot},A={f:excludedOperation},R={f:options=>buildBoardRequest(options,{baseUrl}).url},I={$:seedBoardCoins},Date={now:nowMs},setInterval=timers.setInterval,clearInterval=timers.clearInterval,console=logger;
  const M=cache.entries,L=cache.store,N=[],j=${source.text(predicate)};
  const originalHook=${body};
  return function useBoardCoins(options){
    if(![SEARCH_SORT.FEATURED,SEARCH_SORT.TRENDING].includes(options?.sort)||options.isSearchMode)throw new TypeError('Only non-search featured/trending board inputs are admitted');
    const result=originalHook(options);
    return {coins:result.coins,loading:result.loading,error:result.error,hasMorePages:result.hasMorePages,fetchCoins:result.fetchCoins,refetch:result.refetch,requestKey:result.requestKey,rowsRequestKey:result.rowsRequestKey,servedCoins:result.servedCoins,setCoins:result.setCoins};
  };
}
`,
    { parser: "babel" },
  );
  const generated = parse(text, { sourceType: "module" }),
    adapted = exactlyOne(
      findNodes(
        generated,
        (n) => n.type === "VariableDeclarator" && n.id.name === "originalHook",
      ),
      "used hook frame",
    ).init;
  const restored = structuredClone(adapted);
  const emittedExecutor = variable(restored, "eR").init.arguments[0],
    emittedQuery = variable(restored, "eA").init.arguments[0];
  assert.equal(emittedExecutor.callee.name, "createSearchExecutor");
  assert.equal(emittedQuery.body.callee.name, "buildCoinSearchQuery");
  variable(restored, "eR").init.arguments[0] = executor;
  variable(restored, "eA").init.arguments[0] = query;
  assert.deepEqual(
    normalized(restored, ctx),
    canonical,
    "owning hook frame changed outside credited bridges",
  );
  // Independently retained accepted proofs authenticate the reused operations;
  // these do not regenerate or change any accepted source/artifact.
  const priorExecutor = await verifySession(root),
    priorPlanner = await verifyPlanner(root),
    priorRequest = await verifyMarketBoardBindings(root);
  const consumer = await corpus.factory(228998, {
    source: "evidence/web/objects/ad258f9377db8376.js",
  });
  assert.equal(
    consumer.provenance.sha256,
    "3417e48c11cff94d2efdafcfae6018010e97d1003122b734cd3e019f280a1134",
  );
  const consumerImport = exactlyOne(
    findNodes(
      consumer.node,
      (n) =>
        n.type === "VariableDeclarator" &&
        n.init?.arguments?.[0]?.value === 379705,
    ),
    "actual consumer hook import",
  );
  const consumerCall = exactlyOne(
    findNodes(
      consumer.node,
      (n) =>
        n.type === "CallExpression" &&
        n.callee.type === "SequenceExpression" &&
        member(n.callee.expressions.at(-1), consumerImport.id.name, "f"),
    ),
    "actual consumer hook call",
  );
  const initial = exactlyOne(
    findNodes(
      consumer.node,
      (n) =>
        n.type === "ArrowFunctionExpression" &&
        n.params[0]?.type === "ObjectPattern" &&
        n.params[0].properties.some(
          (p) => propertyName(p.key) === "initialCoins",
        ) &&
        n.body.type === "ObjectExpression",
    ),
    "actual initial-coin admission",
  );
  const force = exactlyOne(
    findNodes(
      consumer.node,
      (n) =>
        n.type === "ObjectProperty" &&
        propertyName(n.key) === "forceLocalFiltering",
    ),
    "actual local-filter flag handoff",
  );
  const seedPolicy = await corpus.factory(947427, {
    source: "evidence/web/objects/ee92e9e880aedbf0.js",
  });
  assert.equal(
    seedPolicy.provenance.sha256,
    "bb25e4e2aa798b336055bc2940a725e203ed39a392bbd1c03d181b882f49d520",
  );
  const deps = [];
  for (const file of [
    "reconstruction/search-session/session.mjs",
    "reconstruction/search-planner/planner.mjs",
    "reconstruction/market-boards/request.mjs",
  ])
    deps.push({
      path: file,
      sha256: sha256(await readFile(path.join(root, file))),
    });
  const contract = {
    schemaVersion: 1,
    base: "094a06f18df738d41e77070c1a009e135671ac1a",
    scope:
      "Full used owning-hook frame for non-search FEATURED/TRENDING board inputs; explicit read-only provider snapshots and response ports",
    sourceProofs: proof,
    frameNormalizedSha256: sha256(JSON.stringify(canonical)),
    module: {
      path: DIRECTORY + "/client.mjs",
      sha256: sha256(Buffer.from(text)),
    },
    bridges: [
      cite(source, executor, "credited accepted shared executor operation"),
      cite(source, query, "credited accepted query builder operation"),
    ],
    providerConstants,
    pauseSources,
    identitySources,
    dependencies: deps,
    priorProofs: {
      executorAdapter: priorExecutor.adapterSha256,
      plannerAdapter: priorPlanner.adapterSha256,
      requestBoundary: sha256(JSON.stringify(priorRequest)),
    },
    caller: {
      factory: consumer.provenance,
      witnesses: [
        cite(consumer, consumerImport, "actual Explore hook import"),
        cite(consumer, consumerCall, "actual hook invocation"),
        cite(consumer, initial, "actual initial seed admission"),
        cite(consumer, force, "actual local-filter flag handoff"),
      ],
      seedPolicyFactory: seedPolicy.provenance,
      seedPolicy: [
        cite(
          seedPolicy,
          exported(seedPolicy, 947427, "r"),
          "actual featured/trending board selection",
        ),
        cite(
          seedPolicy,
          exported(seedPolicy, 947427, "n"),
          "actual initial-coins board admission",
        ),
        cite(
          seedPolicy,
          exported(seedPolicy, 947427, "H"),
          "actual trending all-chain effective selection",
        ),
      ],
      qualification:
        "Source caller/admission/handoff witnesses only; downstream local/verified filters, page/provider/rendering behavior are not reconstructed",
    },
    responsePorts: {
      dependency:
        "OPEN PR1761, public07d93a198ff472ff11f278337d5481a3b4e21d51; not imported or copied",
      parseBoard:
        "Actual583448.$ calls503774.q with one payload argument; supply adapter.mapCoins, no rank offset/context invented",
      seedBoardCoins:
        "Actual503774.$ single normalized-coins argument; supply SAME adapter instance.seedTimestamps",
      qualification:
        "No new normalization/classification/cache recovery credit; source/data behavior remains supplied capability",
    },
    credit: [
      "Accepted695 request builder unchanged",
      "Accepted search-session executor/cache/493025 and search-planner query builder unchanged",
      "OPEN1761 response/seed implementation excluded; explicit actual-signature ports only",
    ],
    limits: [
      "Local API admits non-search featured/trending only and returns board-used methods; no complete379705 search/list compatibility",
      "No credential/cookie/session acquisition: viewer/session/identity/exposure/prefix values are externally supplied read-only snapshots",
      "LIVE-only85324.q is called with enabledfalse for boards; no automatic board timer or invented pause behavior",
      "Private other-sort/search branches remain retained in the original frame but are not exposed or qualified",
      "No backend ranking/accounting, server auth/provider winner, live acquisition, original React/provider lifecycle, UI/native/feature-completion claim",
    ],
  };
  return { text, contract };
}
export async function verify(root = APP_ROOT) {
  const result = await recover(root);
  assert.equal(
    await readFile(path.join(root, DIRECTORY, "client.mjs"), "utf8"),
    result.text,
    "board hook module differs from source adaptation",
  );
  assert.equal(
    await readFile(path.join(root, DIRECTORY, "contract.json"), "utf8"),
    JSON.stringify(result.contract, null, 2) + "\n",
    "board hook contract bytes differ",
  );
  return result.contract;
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  assert.ok(
    process.argv.length === 3 &&
      ["--write", "--check"].includes(process.argv[2]),
    "Use --write|--check",
  );
  if (process.argv[2] === "--write") {
    const result = await recover();
    await mkdir(path.join(APP_ROOT, DIRECTORY), { recursive: true });
    await writeFile(path.join(APP_ROOT, DIRECTORY, "client.mjs"), result.text);
    await writeFile(
      path.join(APP_ROOT, DIRECTORY, "contract.json"),
      JSON.stringify(result.contract, null, 2) + "\n",
    );
  } else await verify();
  console.log(
    "PASS all-four board owning-hook frames; accepted operations reused, normalization/provider ports explicit",
  );
}
