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
const defaultRoot = fileURLToPath(new URL("../", import.meta.url)),
  packet = "reconstruction/callout-replies-state";
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
  async function factory(id) {
    const f = await corpus.factory(id);
    sources.push(f.provenance);
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
  const owner = await factory(258182),
    reader = await factory(408750),
    caller = await factory(204478),
    main = await factory(163807),
    bridge = await factory(445242),
    runtime = await factory(532815);
  for (const f of [owner, reader])
    assert.equal(
      corpus.index.modules.filter((m) => m.ids.includes(f.id)).length,
      1,
    );
  const E = witness(
    owner,
    exported(owner, "E"),
    "complete26-slot replies query/result owner",
  );
  const L = witness(
    reader,
    exported(reader, "L"),
    "complete list request/404/response/row normalizer",
  );
  const contextInitializers = {
    o: "overlay.listeners",
    m: "overlay.pendingReplies",
    y: "overlay.likedByViewer",
  };
  const privateNames = ["n", "s", "o", "u", "d", "c", "m", "f", "y", "g"];
  const parts = privateNames.map((name) => {
    const d = declaration(owner, name);
    witness(owner, d, `complete used private declaration${name}`);
    return contextInitializers[name]
      ? `let ${name}=${contextInitializers[name]};`
      : `let ${owner.text(d)};`;
  });
  for (const name of ["h", "x", "I"])
    parts.push(
      witness(
        owner,
        declaration(owner, name),
        `complete used read/prune/dedup function${name}`,
      ),
    );
  const writerContext = [];
  for (const key of ["a", "k", "K", "j", "t", "w"]) {
    const n = exported(owner, key);
    witness(
      owner,
      n,
      `STATIC-ONLY writer${key}: context layout/version attribution; not executed or emitted`,
    );
    writerContext.push({
      export: key,
      ...owner.witness(n, `static writer${key}`),
    });
  }
  witness(
    owner,
    exported(owner, "L"),
    "actual source useSyncExternalStore export; read only",
  );
  const imp = imported(caller, 258182);
  witness(caller, imp, "actual grouped row wrapper import258182");
  const calls = findNodes(
    caller.node,
    (n) =>
      n.type === "CallExpression" &&
      n.callee.type === "SequenceExpression" &&
      n.callee.expressions.at(-1)?.type === "MemberExpression" &&
      n.callee.expressions.at(-1).object.name === imp.id.name &&
      propertyName(n.callee.expressions.at(-1).property) === "E",
  );
  assert.equal(calls.length, 2);
  for (const n of calls) witness(caller, n, "actual author/all reader call");
  for (const id of [481522, 627092]) {
    const n = exportsOf(caller, id).get("f");
    assert.equal(n.type, "Identifier");
    witness(
      caller,
      declaration(caller, n.name),
      `complete grouped${id} read-row consumer, static only`,
    );
  }
  const mainLinks = [];
  const lazy = exactlyOne(
    findNodes(
      main.node,
      (n) =>
        n.type === "CallExpression" &&
        n.callee.object?.name === main.runtime &&
        propertyName(n.callee.property) === "A" &&
        n.arguments[0]?.value === 505012,
    ),
    "HomeDeck lazy entry",
  );
  witness(main, lazy, "actual HomeDeck lazy import505012");
  for (const id of [505012, 590142]) {
    const f = await factory(id);
    witness(f, f.node, `complete static HomeDeck bootstrap${id}`);
    mainLinks.push(f.provenance);
  }
  const deck = await factory(897578),
    selector = await factory(347939),
    registry = await factory(117330),
    positions = await factory(150430);
  const deckImp = imported(deck, 347939);
  witness(deck, deckImp, "actual HomeDeck column selector import347939");
  const selectorCalls = findNodes(
    deck.node,
    (n) =>
      n.type === "CallExpression" &&
      n.arguments[0]?.type === "MemberExpression" &&
      n.arguments[0].object.name === deckImp.id.name &&
      propertyName(n.arguments[0].property) === "f",
  );
  assert.equal(selectorCalls.length, 1);
  witness(
    deck,
    selectorCalls[0],
    "actual HomeDeck pane renders column selector",
  );
  witness(
    selector,
    selector.node,
    "complete static column type→registry Component selector",
  );
  const positionsImp = imported(registry, 150430);
  witness(registry, positionsImp, "actual registry imports profile positions");
  const reg = declaration(registry, "lO").init;
  const entry = exactlyOne(
    reg.properties.filter((p) => propertyName(p.key) === "your-positions"),
    "Home your-positions registry branch",
  );
  witness(
    registry,
    entry,
    "complete static your-positions branch and its gates",
  );
  const positionCalls = findNodes(
    entry,
    (n) =>
      n.type === "CallExpression" &&
      n.arguments[0]?.type === "MemberExpression" &&
      n.arguments[0].object.name === positionsImp.id.name &&
      propertyName(n.arguments[0].property) === "ProfilePositionsCallouts",
  );
  assert.equal(positionCalls.length, 1);
  witness(
    registry,
    positionCalls[0],
    "actual Home positions component input handoff",
  );
  witness(
    positions,
    exported(positions, "ProfilePositionsCallouts"),
    "complete static positions list consumer",
  );
  const readImp = imported(positions, 481522);
  witness(positions, readImp, "actual positions row import481522");
  const readCalls = findNodes(
    positions.node,
    (n) =>
      n.type === "CallExpression" &&
      n.callee.type === "SequenceExpression" &&
      n.callee.expressions.at(-1)?.object?.name === readImp.id.name &&
      propertyName(n.callee.expressions.at(-1).property) === "f",
  );
  assert.equal(readCalls.length, 1);
  witness(
    positions,
    readCalls[0],
    "actual expanded positions row author-read call",
  );
  const marks = exported(caller, "k", 462570);
  witness(
    caller,
    marks,
    "complete static grouped462570 latest-read marks context",
  );
  const localReadCalls = findNodes(
    marks,
    (n) =>
      n.type === "CallExpression" &&
      n.callee.type === "Identifier" &&
      ["er", "en"].includes(n.callee.name),
  );
  assert.equal(localReadCalls.length, 2);
  for (const call of localReadCalls)
    witness(caller, call, "actual read marks owner invokes author/all wrapper");
  witness(bridge, bridge.node, "complete compiler bridge");
  witness(runtime, runtime.node, "complete native memo runtime bridge");
  const code = await format(
    `// Complete selected source read boundary; external context is deliberately explicit.
export function createCalloutRepliesReadState({React,useMemoCache,useQuery,getContractClient,clock,Response,overlay}){
 if(typeof useMemoCache!=='function'||typeof useQuery!=='function'||typeof getContractClient!=='function'||typeof clock?.now!=='function'||typeof clock?.parse!=='function'||typeof Response?.json!=='function'||typeof React?.useSyncExternalStore!=='function')throw TypeError('explicit React/compiler/query/client/clock/Response capabilities required');
 if(!(overlay?.pendingReplies instanceof Map)||!(overlay?.likedByViewer instanceof Map)||!(overlay?.listeners instanceof Set))throw TypeError('explicit owned Map/Map/Set overlay context required');
 const Date=clock;
 const readReplies=(()=>{${bindings(reader, { 759257: "{j:getContractClient}" })}return ${L};})();
 ${bindings(owner, { 445242: "{c:useMemoCache}", 690877: "{useQuery}", 352386: "React", 408750: "{L:readReplies}" })}
 ${parts.join("\n")}
 const useReplies=${E};
 return{useReplies,readReplies,notifyOverlayChange:u,getOverlayVersion:c,subscribeOverlay:d};
}
`,
    { parser: "babel" },
  );
  const contract = {
    schemaVersion: 1,
    title: "Complete callout replies read/query and explicit overlay context",
    mainChain:
      "163807 lazy505012→590142→897578 column selector347939→117330 your-positions conditional branch→150430.ProfilePositionsCallouts/expanded row→481522 er→258182.E→408750.L. All source/call witnesses only; no original mounted/active configuration claim.",
    anchors: corpus.anchors,
    sources,
    witnesses,
    writerContext,
    generatedSha256: sha256(code),
    ports: [
      "React.useSyncExternalStore/compiler useMemoCache",
      "useQuery observer/cache/scheduling",
      "759257.j exact factory/named operation; no default destination",
      "clock.now/clock.parse Date facade and native-compatible Response.json",
      "one module context: actual pendingRepliesMap/likedByViewerMap/listenersSet, synthetic priming only",
    ],
    contextAdaptation:
      "Only three captured allocation initializers (o=newSet,m=newMap,y=newMap) become required constructor-supplied actual containers. Full used read/dedup/prune/subscription/version bodies retained; local source version starts0. notifyOverlayChange is actual private version/notifier export for host notifications, not a like/reply action API.",
    semantics: {
      request:
        "GET /callout/{calloutId}/replies, limit200, author default/ALL only exact all; falsy parent omitted; include credentials/header/signal;404 replaced by Response.json empty list; other !ok throws status",
      normalization:
        "raw nullish list fallback; includeTombstones truthiness before map; trimmed wallet then raw ccId; finite Date.parse inclnegative; count/media/profile distinctions retained",
      query:
        "full26slots; enabled defaults with truthy mint/id; author default; key null fallbacks; stale15s/gc300s/window focusfalse/backgroundfalse/poll nullishfalse; forwards raw error/flags/refetch",
      overlays:
        "pending<=300000ms prunes map on read, exactparent/scope filtering; server reply IDs and pending userLowercase/contentTrim dedup, then like map patch identities",
      memo: "useSyncExternalStore tick is subscribed but not part of captured read projection dependencies: context-only notifications can rerender without recomputing rows until another dependency changes",
    },
    limits: [
      "Writer functions are static attribution only, never emitted/executed; no like/reply actions, mutation transport/auth or production data acquisition",
      "Main feed/row consumers are raw static witnesses, not mounted UI/provider winner claims",
      "Synthetic primed containers/notifications are explicit ports, not original store acquisition or current user state",
      "No default endpoint, current credentials/cookies, service, native/feature/finance qualification; ledgers/captures/earlier packages unchanged",
    ],
    mounted: false,
    productionOperationsQualified: 0,
  };
  return { code, contract };
}
export async function verify(appRoot = defaultRoot, supplied) {
  const d = await derive(appRoot),
    dir = path.join(appRoot, packet);
  assert.equal(
    supplied?.code ?? (await readFile(path.join(dir, "client.mjs"), "utf8")),
    d.code,
  );
  assert.deepEqual(
    supplied?.contract ??
      JSON.parse(await readFile(path.join(dir, "contract.json"), "utf8")),
    d.contract,
  );
  return {
    witnesses: d.contract.witnesses.length,
    sourceEntries: d.contract.sources.length,
    actualReadCalls: 2,
    actualMainRowCalls: 1,
    staticWriterContexts: 6,
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
        "usage: original-callout-replies-state.mjs [--app-root PATH] --write|--check",
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
