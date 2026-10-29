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
const packet = "reconstruction/live-coin-state";
const batchSources = [
  "evidence/web/objects/f4e16ef1b0b97d5e.js",
  "evidence/web/objects/27a1ee00eb5909ec.js",
];
const batchHashes = [
  "eaadb129bb56009d4029f5ad08f8a52fb30da20d64ab9218ff56359dfdead966",
  "c232e5e54526261f925817dc14fbf1a253b4e89e2515f7a8c5bf2c3b7d2de8d8",
];
function exportsOf(f, id = f.id) {
  const out = new Map();
  // Only the factory's own top-level registration statements are accepted.
  for (const statement of f.node.body.body) {
    if (statement.type !== "ExpressionStatement") continue;
    const call = statement.expression;
    if (
      call.type !== "CallExpression" ||
      call.callee.type !== "MemberExpression" ||
      call.callee.object.name !== f.runtime ||
      propertyName(call.callee.property) !== "s"
    )
      continue;
    if (call.arguments[1] && call.arguments[1].value !== id) continue;
    const a = call.arguments[0]?.elements;
    if (!a) continue;
    for (let i = 0; i < a.length; i += 3)
      if (a[i]?.type === "StringLiteral" && a[i + 1]?.value === 0)
        out.set(a[i].value, a[i + 2]);
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
    `${f.id} declaration ${name}`,
  );
}
function exported(f, key, id = f.id) {
  const n = exportsOf(f, id).get(key);
  assert.ok(n, `${id}.${key}`);
  return n.type === "Identifier"
    ? (declaration(f, n.name).init ?? declaration(f, n.name))
    : n;
}
function importDeclaration(f, id) {
  return exactlyOne(
    declarations(f).filter(
      (n) =>
        n.type === "VariableDeclarator" &&
        n.init?.type === "CallExpression" &&
        n.init.callee.type === "MemberExpression" &&
        n.init.callee.object.name === f.runtime &&
        propertyName(n.init.callee.property) === "i" &&
        n.init.arguments[0]?.value === id,
    ),
    `${f.id} import ${id}`,
  );
}
function privateDeclarations(f) {
  return declarations(f).filter(
    (n) =>
      !(
        n.type === "VariableDeclarator" &&
        n.init?.type === "CallExpression" &&
        n.init.callee.object?.name === f.runtime &&
        ["i", "r"].includes(propertyName(n.init.callee.property))
      ),
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
  function bindings(f, map) {
    return Object.entries(map)
      .map(
        ([id, value]) =>
          `const ${witness(
            f,
            importDeclaration(f, Number(id)),
            `used import ${id}`,
          )
            .split("=")[0]
            .trim()}=${value};`,
      )
      .join("\n");
  }
  function privates(f) {
    return privateDeclarations(f)
      .map((n) =>
        n.type === "FunctionDeclaration"
          ? witness(f, n, `complete private function ${n.id.name}`)
          : `let ${witness(f, n, `complete private state/declaration ${n.id.name}`)};`,
      )
      .join("\n");
  }
  const allBatches = corpus.index.modules.filter((m) => m.ids.includes(811005));
  assert.deepEqual(
    new Set(allBatches.map((m) => m.sha256)),
    new Set(batchHashes),
  );
  const batchCodes = [];
  for (let v = 0; v < batchSources.length; v++) {
    const f = await factory(811005, batchSources[v]);
    assert.equal(f.provenance.sha256, batchHashes[v]);
    assert.deepEqual([...exportsOf(f).keys()], ["H", "_", "J"]);
    batchCodes.push(`function frameVariant${v}({React,compiler,environment,logger}){
   const {window,document,setTimeout,clearTimeout}=environment;
   ${bindings(f, { 445242: "{c:compiler}", 254667: "{y:logger}", 352386: "React" })}
   ${privates(f)}
   return {createBatch:${witness(f, exported(f, "H"), "complete H batch constructor")},enqueue:${witness(f, exportsOf(f).get("_"), "shared callback enqueue export")},usePause:${witness(f, exported(f, "J"), "complete J effect/pause hook")}};
  }`);
  }
  const middleware = await factory(634103);
  const subscribe = witness(
    middleware,
    exported(middleware, "u"),
    "used subscribeWithSelector; persistence j/V excluded",
  );
  const state = await factory(653805);
  assert.equal(
    state.provenance.sha256,
    "f2496f3277c7f8750beafb209804155df0c69de4d2f5ce0a9b0213e6eeabc57e",
  );
  assert.equal(
    corpus.index.modules.filter((m) => m.ids.includes(653805)).length,
    1,
  );
  assert.deepEqual([...exportsOf(state).keys()], ["J", "F", "k", "x"]);
  const provider = await factory(78436);
  witness(
    provider,
    exported(provider, "$"),
    "external curried bound-store provider signature",
  );
  witness(
    provider,
    exported(provider, "f"),
    "external React useSyncExternalStore provider implementation",
  );
  const storeCode = `export function createLiveCoinState({React,compiler,createBoundStore,frameBatch,clock}){
  const Date=clock;
  ${bindings(state, { 445242: "{c:compiler}", 78436: "{$:createBoundStore}", 634103: "{u:subscribeWithSelector}", 352386: "{default:React}", 811005: "{H:frameBatch.createBatch}" })}
  ${privates(state)}
  return {store:${witness(state, exportsOf(state).get("x"), "complete bound-store export")},useMarketCap:${witness(state, exported(state, "J"), "complete J market-cap selector")},useCoin:${witness(state, exported(state, "F"), "complete F coin selector")},useCoins:${witness(state, exported(state, "k"), "complete k multi selector")},useShallow:${witness(state, exportsOf(state, 362324).get("f"), "same-factory362324 shallow-reference export")}};
 }`;
  // These are complete, selected source consumers, not a global minified-name or loader resolver.
  const consumers = [];
  for (const [id, key] of [
    [457065, "J"],
    [401134, "F"],
    [493870, "k"],
    [915631, "x"],
  ]) {
    const f = await factory(id),
      imp = importDeclaration(f, 653805),
      alias = imp.id.name;
    witness(f, imp, `actual ${id} import653805`);
    const refs = findNodes(
      f.node,
      (n) =>
        n.type === "MemberExpression" &&
        !n.computed &&
        n.object?.name === alias &&
        n.property.name === key,
    );
    assert.ok(refs.length > 0, `${id} used653805.${key}`);
    // Keep a full enclosing top-level function/declaration/registration witness. Exact
    // bytes expose lexical scopes; no identifier-name-only global resolution claim.
    const selected = exactlyOne(
      f.node.body.body.filter((s) =>
        refs.some((n) => s.start <= n.start && s.end >= n.end),
      ),
      `${id} enclosing used consumer`,
    );
    witness(
      f,
      selected,
      `complete enclosing ${id} consumer statement of653805.${key}`,
    );
    consumers.push({
      id,
      export: key,
      source: f.provenance,
      receiver: alias,
      uses: refs.map((n) => f.witness(n, `selected ${id} ${alias}.${key}`)),
    });
  }
  const code = await format(
    `// Source-bound editable translation. Captured factories are parsed, never evaluated.
 // Provider, React/compiler, clock, browser scheduler and logger are explicit ports.
 export const batchVariantHashes=${JSON.stringify(batchHashes)};
 ${batchCodes.join("\n")}
 export function createFrameBatchRuntime({variant,...ports}){
  if(variant===batchVariantHashes[0])return frameVariant0(ports);
  if(variant===batchVariantHashes[1])return frameVariant1(ports);
  throw new Error('explicit supported811005 variant hash required');
 }
 export const subscribeWithSelector=${subscribe};
 ${storeCode}`,
    { parser: "babel" },
  );
  const contract = {
    schemaVersion: 1,
    title:
      "653805 live-coin queued state and complete811005 frame-batch boundary",
    anchors: corpus.anchors,
    sources,
    witnesses,
    consumers,
    batchVariants: batchSources.map((source, i) => ({
      source,
      sha256: batchHashes[i],
    })),
    state: {
      factory: 653805,
      sharedShallowFactory: 362324,
      exports: {
        x: "bound store",
        J: "usdMarketCap selector",
        F: "coin selector",
        k: "shallow multi-coin selector",
      },
      methods: [
        "updateCoin",
        "setCoin",
        "removeCoin",
        "getCoin",
        "getCoins",
        "hasLiveData",
        "peekCoin",
      ],
      writes: "Local queued state operations, not API mutations",
      pending:
        "getCoin/getCoins/hasLiveData see committed state; peekCoin applies queued operations without committing",
      merge:
        "Latest base except committed retains prior base; updates shallow-merge; defined ATH fields use Math.max; queuedAt is latest enqueue Date.now, not a monotonicity check",
      identity:
        "Object/Map/iterable shallow equality and hook reference cache retained; one shared empty selection; no numeric/field admission added",
    },
    batching: {
      visible: "requestAnimationFrame plus100ms timeout fallback",
      hiddenOrNoRAF: "250ms timeout",
      visibility:
        "one retained visibilitychange listener; hidden transition flushes unless paused",
      pause:
        "effect increments shared pause count, cancels global handles; local RAF/250ms completion releases and flushes if last; cleanup releases/reschedules without direct flush",
      lifetime:
        "Batch registry and visibility listener have no source unregister/dispose; direct batch.flush bypasses global pause; callback snapshot clears before callbacks, exceptions logged independently",
    },
    externalPorts: [
      "78436 curried bound-store provider and React subscription scheduling",
      "React hooks/useEffect/useRef",
      "445242 compiler memo-cache",
      "Date.now clock",
      "window/document and RAF/timeout/visibility scheduler",
      "254667 logger",
    ],
    attribution: [
      {
        pr: 1812,
        scope:
          "Existing Mayhem mint/cap join remains external; its selected consumer uses653805.J with undefined-only fallback",
      },
      {
        pr: 1839,
        scope:
          "Existing settings framework; only634103.u used here; persistence/storage exports excluded",
      },
    ],
    limits: [
      "No WS/NATS/RPC or provider service reconstruction, history, network calls, original loader winner, price/oracle/accounting interpretation, auth/session/cookies, native compatibility or maintained app mount",
      "Actual selected consumers are source witnesses only; their request/provider/transport and full screens are not implemented here",
      "Qualification hosts inject state/timers; finite synthetic behavior is not original provider or production delivery qualification",
      "Two811005 physical variants explicit; no original active variant winner inferred; all captured source files unchanged",
    ],
    mounted: false,
    productionOperationsQualified: 0,
    generatedSha256: sha256(code),
  };
  return { code, contract };
}
export async function verify(appRoot = rootDefault, supplied) {
  const actual = await derive(appRoot),
    dir = path.join(appRoot, packet);
  assert.equal(
    supplied?.code ?? (await readFile(path.join(dir, "client.mjs"), "utf8")),
    actual.code,
  );
  assert.deepEqual(
    supplied?.contract ??
      JSON.parse(await readFile(path.join(dir, "contract.json"), "utf8")),
    actual.contract,
  );
  return {
    batchVariants: 2,
    witnesses: actual.contract.witnesses.length,
    sourceEntries: actual.contract.sources.length,
    selectedConsumers: actual.contract.consumers.length,
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
        "usage: original-live-coin-state.mjs [--app-root PATH] --write|--check",
      );
  }
  if (!mode) throw Error("explicit --write or --check required");
  if (mode === "--write") {
    const d = await derive(root);
    await mkdir(path.join(root, packet), { recursive: true });
    await writeFile(path.join(root, packet, "client.mjs"), d.code);
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
