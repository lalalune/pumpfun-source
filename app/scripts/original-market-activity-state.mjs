import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { format } from "prettier";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  propertyName,
  sha256,
} from "./original-contracts/source.mjs";
const rootDefault = fileURLToPath(new URL("../", import.meta.url));
const packet = "reconstruction/market-activity-state";
const variants = {
  201629: [
    {
      source: "evidence/web/objects/dba17a249156c6ff.js",
      sha256:
        "704bb073aaf4230b6cac309756c284803fe7d3cc4e2776a060d041af2341a786",
    },
    {
      source: "evidence/web/objects/ecf7ec803bfb3020.js",
      sha256:
        "dff1b5f10ee3af571bcc7fa3b0a7e8a0ec4b9eedc58a4cc3526600590f1529b4",
    },
    {
      source: "evidence/web/objects/9535b69d76e2a69b.js",
      sha256:
        "d9ab130a7e21782f4e8a294f011c25405d3690ef4aafcc5bcc5bdabd656a414b",
    },
  ],
  372743: [
    {
      source: "evidence/web/objects/dba17a249156c6ff.js",
      sha256:
        "c57dd65e642700694b2b65e1554a0d11ac5caca8b535bfa1062564366e344d61",
    },
    {
      source: "evidence/web/objects/ecf7ec803bfb3020.js",
      sha256:
        "4d8d931c538e4d5825c61fd3a88195ed022fb5aea372113ac4f31b594b2ada62",
    },
    {
      source: "evidence/web/objects/9535b69d76e2a69b.js",
      sha256:
        "8d033eb75f35cf9896bac25b3e151d4e7057dacd759e61c880aa24e1e52b1022",
    },
    {
      source: "evidence/web/objects/0e0a55c249b456d7.js",
      sha256:
        "7eeb7e121092f1cac917f25c0d222d0e79932ce86d62cb01a73e90cb541781e0",
    },
    {
      source: "evidence/web/objects/1681353d046eeca6.js",
      sha256:
        "90cc0b7b37585830da582b2f52fe2177074ed20f613713e894858b23a8d34a12",
    },
  ],
  680930: [
    {
      source: "evidence/web/objects/dba17a249156c6ff.js",
      sha256:
        "9e400e569d2f1be621405e2416b4822a026a7314017ea0e0a0786d1874f4940a",
    },
    {
      source: "evidence/web/objects/ecf7ec803bfb3020.js",
      sha256:
        "28b8bd958df7a2591b9f5137a9df1a7b0175c4a5ff974a6ea3e3221f4de90915",
    },
    {
      source: "evidence/web/objects/9535b69d76e2a69b.js",
      sha256:
        "e26d778b38c007ca2caba17ad41f9759b9e68e61d22eda234f84d9e085f6c1d6",
    },
    {
      source: "evidence/web/objects/0e0a55c249b456d7.js",
      sha256:
        "6c2fe9687dcd41b43a0e38b067688017f1d4bc9297f066e5f42f32c709f91d62",
    },
    {
      source: "evidence/web/objects/1681353d046eeca6.js",
      sha256:
        "52b35b47af7bdd2920bb1862537c626afc4bde9baac68d2d138215848051b8bf",
    },
    {
      source: "evidence/web/objects/7a7f27bff952614d.js",
      sha256:
        "64630965b09dd0b4e78b2d7f90cae707909b550ba9f5cd4400b666c7b43cb996",
    },
  ],
};
function exportsOf(f, id = f.id) {
  const out = new Map();
  for (const s of f.node.body.body) {
    const c = s.type === "ExpressionStatement" ? s.expression : null;
    if (
      c?.type !== "CallExpression" ||
      c.callee.type !== "MemberExpression" ||
      c.callee.object.name !== f.runtime ||
      propertyName(c.callee.property) !== "s" ||
      (c.arguments[1] && c.arguments[1].value !== id)
    )
      continue;
    const a = c.arguments[0]?.elements;
    if (!a) continue;
    for (let i = 0; i < a.length; i += 3) {
      assert.equal(a[i]?.type, "StringLiteral");
      assert.equal(a[i + 1]?.value, 0);
      out.set(a[i].value, a[i + 2]);
    }
  }
  return out;
}
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
function exported(f, key) {
  const n = exportsOf(f).get(key);
  assert.ok(n, `${f.id}.${key}`);
  return n.type === "Identifier"
    ? (declaration(f, n.name).init ?? declaration(f, n.name))
    : n;
}
function isImport(f, n) {
  return (
    n.type === "VariableDeclarator" &&
    n.init?.type === "CallExpression" &&
    n.init.callee.type === "MemberExpression" &&
    n.init.callee.object.name === f.runtime &&
    propertyName(n.init.callee.property) === "i"
  );
}
function imported(f, id) {
  return exactlyOne(
    declarations(f).filter(
      (n) => isImport(f, n) && n.init.arguments[0]?.value === id,
    ),
    `${f.id} import${id}`,
  );
}
export async function derive(appRoot = rootDefault) {
  const corpus = await openCorpus(appRoot),
    sources = [],
    witnesses = [];
  async function factory(id, source) {
    const f = await corpus.factory(id, source ? { source } : {});
    sources.push(f.provenance);
    return f;
  }
  function witness(f, n, label) {
    witnesses.push({ ...f.witness(n, label), astType: n.type });
    return f.text(n);
  }
  function privates(f) {
    return declarations(f)
      .filter((n) => !isImport(f, n))
      .map((n) =>
        n.type === "FunctionDeclaration"
          ? witness(f, n, `complete private function${n.id.name}`)
          : `let ${witness(f, n, `complete private declaration${n.id.name}`)};`,
      )
      .join("\n");
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
  for (const [id, rows] of Object.entries(variants))
    assert.deepEqual(
      new Set(
        corpus.index.modules
          .filter((m) => m.ids.includes(Number(id)))
          .map((m) => m.sha256),
      ),
      new Set(rows.map((r) => r.sha256)),
    );
  const microtask = await factory(998243),
    taskCode = witness(
      microtask,
      exported(microtask, "f"),
      "complete native queueMicrotask forwarding wrapper",
    );
  const storeCodes = [];
  for (let i = 0; i < variants[372743].length; i++) {
    const row = variants[372743][i],
      f = await factory(372743, row.source);
    assert.equal(f.provenance.sha256, row.sha256);
    assert.deepEqual([...exportsOf(f).keys()], ["u", "c", "f"]);
    storeCodes.push(
      `function store${i}({createBoundStore,subscribeWithSelector,createBatch}){${bindings(f, { 78436: "{$:createBoundStore}", 634103: "{u:subscribeWithSelector}", 811005: "{H:createBatch}" })}${privates(f)}return {setMarketActivity:${witness(f, exported(f, "u"), "complete local patch export")},seedMarketActivity:${witness(f, exported(f, "c"), "complete local missing-seed export")},store:${witness(f, exportsOf(f).get("f"), "complete bound-store export")}};}`,
    );
  }
  const queryCodes = [];
  for (let i = 0; i < variants[201629].length; i++) {
    const row = variants[201629][i],
      f = await factory(201629, row.source);
    assert.equal(f.provenance.sha256, row.sha256);
    assert.deepEqual([...exportsOf(f).keys()], ["f"]);
    queryCodes.push(
      `function query${i}({React,useQuery,useQueryClient,helpers,fetchBatch,clock,queueMicrotask,state}){const Date=clock;const microtask=${taskCode};${bindings(f, { 690877: "{useQuery}", 606933: "{useQueryClient}", 352386: "React", 998243: "{f:microtask}", 372743: "{f:state.store,u:state.setMarketActivity,c:state.seedMarketActivity}", 680930: "helpers", 849812: "{g:fetchBatch}" })}${privates(f)}return {useMarketActivity:${witness(f, exported(f, "f"), "complete cache/query/seed/readback owning hook")}};}`,
    );
  }
  // Existing1873 pure helper source is reused ONLY as a qualification capability.
  // The runtime client still receives this interface; reader/query frame are not copied.
  const fixtureCodes = [];
  for (let i = 0; i < variants[680930].length; i++) {
    const row = variants[680930][i],
      f = await factory(680930, row.source);
    assert.equal(f.provenance.sha256, row.sha256);
    fixtureCodes.push(
      `function helper${i}(){${privates(f)}return{t:${witness(f, exportsOf(f).get("t"), "qualified1873 constants reference")},$:${witness(f, exported(f, "$"), "qualified1873 batch capability; fixture only")},P:${witness(f, exported(f, "P"), "qualified1873 missing24h capability; fixture only")},c:${witness(f, exported(f, "c"), "qualified1873 selected-field equality capability; fixture only")}};}`,
    );
  }
  const callers = [];
  for (const id of [228998, 20149]) {
    const f = await factory(id),
      imp = imported(f, 201629),
      alias = imp.id.name;
    witness(f, imp, `actual${id} import201629`);
    const calls = findNodes(
      f.node,
      (n) =>
        n.type === "CallExpression" &&
        n.callee.type === "SequenceExpression" &&
        n.callee.expressions.at(-1)?.type === "MemberExpression" &&
        n.callee.expressions.at(-1).object.name === alias &&
        propertyName(n.callee.expressions.at(-1).property) === "f",
    );
    assert.equal(calls.length, id === 228998 ? 2 : 1);
    for (const call of calls) witness(f, call, `actual${id} owning-hook call`);
    const enclosing = f.node.body.body.filter((n) =>
      calls.some((c) => n.start <= c.start && n.end >= c.end),
    );
    for (const n of enclosing)
      witness(f, n, `complete enclosing${id} caller statement; UI external`);
    callers.push({
      id,
      source: f.provenance,
      calls: calls.map((c) => f.witness(c, "actual201629.f call")),
    });
  }
  const code = await format(
    `// Complete source-bound query/store translation. Runtime and existing helpers are injected ports.
 export const queryVariants=${JSON.stringify(variants[201629])};
 export const storeVariants=${JSON.stringify(variants[372743])};
 ${storeCodes.join("\n")}
 ${queryCodes.join("\n")}
 export function createMarketActivityState({queryVariant,storeVariant,...ports}){
  const storeFactories=({${variants[372743].map((r, i) => `${JSON.stringify(r.sha256)}:store${i}`).join(",")}});
  const storeFactory=typeof storeVariant==='string'&&Object.hasOwn(storeFactories,storeVariant)?storeFactories[storeVariant]:null;
  const queryFactories=({${variants[201629].map((r, i) => `${JSON.stringify(r.sha256)}:query${i}`).join(",")}});
  const queryFactory=typeof queryVariant==='string'&&Object.hasOwn(queryFactories,queryVariant)?queryFactories[queryVariant]:null;
  if(!storeFactory||!queryFactory)throw Error('explicit supported201629 and372743 variant hashes required');
  const state=storeFactory(ports),query=queryFactory({...ports,state});return{...state,...query};
 }`,
    { parser: "babel" },
  );
  const fixture = await format(
    `// Source-bound reuse of existing1873 helper capabilities for qualification ONLY.
 // This is not another reader/helper recovery or a runtime client dependency.
 export const helperVariants=${JSON.stringify(variants[680930])};
 ${fixtureCodes.join("\n")}
 export function createHelperPort(variant){const constructors=({${variants[680930].map((r, i) => `${JSON.stringify(r.sha256)}:helper${i}`).join(",")}});const constructor=typeof variant==='string'&&Object.hasOwn(constructors,variant)?constructors[variant]:null;if(!constructor)throw Error('explicit supported680930 fixture variant required');return constructor();}`,
    { parser: "babel" },
  );
  const contract = {
    schemaVersion: 1,
    title:
      "Complete activity query/cache-to-queued-store and stable readback boundary",
    anchors: corpus.anchors,
    sources,
    witnesses,
    variants,
    callers,
    runtimePorts: [
      "React hooks and useQuery/useQueryClient cache/observer",
      "78436 curried bound-store provider +634103.u subscription middleware, credited proposed1870",
      "811005.H batch API, credited proposed1870; no scheduler implementation copied",
      "849812.g activity reader, credited proposed1873; no network implementation copied",
      "680930 constants/batch/equality/missing capability, credited proposed1873; source-bound qualification-only helpers included",
      "Date.now clock and native queueMicrotask",
    ],
    stateSemantics: {
      patch:
        "When both previous and next window values are truthy, only non-null nested patch fields overwrite; otherwise the next window replaces it, including null. Queued and committed merge order preserved",
      seed: "Existing addresses fill only missing fields inside windows truthy in both current and seed, considering pending queue; absent windows are skipped. New addresses enqueue whole seed",
      clear:
        "Clear pending batch map and reset committed state immediately; no global scheduler disposal added",
    },
    querySemantics: {
      mints:
        "Set/filter(Boolean)/sort, joined key; option defaults and polling boolean retained",
      warm: "Only current query data undefined permits cross-query cache warm; fresh noninvalidated query and global mint freshness required; highest dataUpdatedAt wins, first equal timestamp retained",
      generation:
        "Every nonempty query increments per-hook counter; fetched freshness timestamps always recorded; only latest generation writes fetched patches to store; earlier response still returned",
      seed: "Truthy query data queues a missing-field seed microtask independently of fetch enablement; no auth/readiness gate",
      readback:
        "readBack=false selects shared empty object; helper equality intentionally compares only24h volumeUSD and priceChangePercent. On change a shallow copy is cached but the first projection is returned; subsequent equal reads return that cached copy",
      refetch:
        "Committed-store missing24h guard precedes awaited invalidation and refetch",
    },
    limits: [
      "No external service request, WS/RPC, original provider/loader winner, mounted UI, auth/session/cookies, endpoint/feature/milestone or native qualification",
      "No accounting, financial, oracle, freshness guarantee or original runtime timing claim",
      "Existing1873 reader/query and1870 frame/store implementations are not copied; reused helper bodies are qualification-only and credited",
      "Explicit variant choices describe supported captured translations, not original loader execution order. All captures and previous ledgers/packets unchanged",
    ],
    mounted: false,
    productionOperationsQualified: 0,
    generatedSha256: sha256(code),
    qualificationHelperSha256: sha256(fixture),
  };
  return { code, fixture, contract };
}
export async function verify(appRoot = rootDefault, supplied) {
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
    queryVariants: 3,
    storeVariants: 5,
    qualificationHelperVariants: 6,
    witnesses: d.contract.witnesses.length,
    sourceEntries: d.contract.sources.length,
    callerCalls: 3,
    mounted: false,
    productionOperationsQualified: 0,
  };
}
async function main() {
  let root = rootDefault,
    mode;
  const args = process.argv.slice(2);
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--app-root" && args[i + 1]) root = path.resolve(args[++i]);
    else if (["--write", "--check"].includes(args[i]) && !mode) mode = args[i];
    else
      throw Error(
        "usage: original-market-activity-state.mjs [--app-root PATH] --write|--check",
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
