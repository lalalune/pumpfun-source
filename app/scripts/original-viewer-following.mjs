import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  member,
  objectProperty,
  propertyName,
  literal,
  sha256,
} from "./original-contracts/source.mjs";
import { createSchemaExtractor } from "./original-contracts/schema.mjs";
const source = (name) => `evidence/web/objects/${name}.js`;
function assert(ok, label) {
  if (!ok) throw Error(label);
}
function imported(f, id) {
  return exactlyOne(
    findNodes(
      f.node,
      (n) =>
        n.type === "VariableDeclarator" &&
        n.init?.type === "CallExpression" &&
        ["i", "r"].some((m) => member(n.init.callee, f.runtime, m)) &&
        n.init.arguments[0]?.value === id,
    ),
    `import ${id}`,
  );
}
function exportsOf(f, id) {
  const n = exactlyOne(
      findNodes(
        f.node,
        (n) =>
          n.type === "CallExpression" &&
          member(n.callee, f.runtime, "s") &&
          (n.arguments[1]?.value === id ||
            (n.arguments.length === 1 && f.ids.length === 1)),
      ),
      `registration ${id}`,
    ),
    values = n.arguments[0].elements,
    result = new Map();
  for (let i = 0; i < values.length; i += 3) {
    assert(
      values[i]?.type === "StringLiteral" &&
        values[i + 1]?.value === 0 &&
        !result.has(values[i].value),
      `unsupported exports ${id}`,
    );
    result.set(values[i].value, values[i + 2]);
  }
  return result;
}
function local(f, n) {
  if (n?.type !== "Identifier") return n;
  const d = exactlyOne(
    findNodes(
      f.node,
      (d, parents) =>
        ((d.type === "VariableDeclarator" && d.id.name === n.name) ||
          (d.type === "FunctionDeclaration" && d.id.name === n.name)) &&
        !parents.some((p) => p !== f.node && /Function|Method/.test(p.type)),
    ),
    `local ${n.name}`,
  );
  return d.type === "VariableDeclarator" ? d.init : d;
}
function calls(node, namespace, name) {
  return findNodes(
    node,
    (n) =>
      n.type === "CallExpression" &&
      member(
        n.callee.type === "SequenceExpression"
          ? n.callee.expressions.at(-1)
          : n.callee,
        namespace,
        name,
      ),
  );
}
export async function extractViewerFollowing(root) {
  const corpus = await openCorpus(root);
  assert(
    corpus.anchors.manifestSha256 ===
      "9e0fc00719eb8c919dd4205d3c118eb48c4927e056c77e8343e26d6f7189bbb5",
    "unreviewed manifest",
  );
  assert(
    corpus.anchors.inventorySha256 ===
      "1d268ae7f2eb0f61eaaffd222269bf29d9ce06e9946372861721b2f159d868e2",
    "unreviewed inventory",
  );
  const fragments = new Map(),
    factories = new Map();
  const get = async (id, selected) => {
    const f = await corpus.factory(id, selected ? { source: selected } : {});
    factories.set(
      `${id}:${f.provenance.source}:${f.provenance.sha256}`,
      f.provenance,
    );
    return f;
  };
  const add = (f, n, label) => {
    assert(n, `missing ${label}`);
    const x = f.witness(n, label),
      key = `${x.source}:${x.utf16.join(":")}`;
    fragments.set(key, { ...x, text: f.text(n) });
    return key;
  };
  const f = await get(303599, source("fd402d4185b44ce9")),
    ex = exportsOf(f, 303599),
    query = local(f, ex.get("Q")),
    policy = query.body;
  const callback = objectProperty(policy, "queryFn"),
    operation = "GET /following/v3/following/{userId}";
  const request = exactlyOne(
      findNodes(
        callback,
        (n) =>
          n.type === "CallExpression" && n.arguments[0]?.value === operation,
      ),
      "actual viewer-following request",
    ),
    opts = request.arguments[1];
  exactlyOne(
    calls(request.callee, imported(f, 759257).id.name, "j"),
    "viewer read actual website j",
  );
  assert(
    opts.properties.map((p) => propertyName(p.key)).join(",") ===
      "params,query,signal,throwHttpErrors,hooks,parseJson",
    "viewer request override fields changed",
  );
  assert(
    literal(objectProperty(objectProperty(opts, "query"), "limit")) === 1000 &&
      literal(objectProperty(opts, "throwHttpErrors")) === false,
    "viewer cap/error behavior changed",
  );
  assert(
    literal(objectProperty(policy, "staleTime")) === 60000 &&
      literal(objectProperty(policy, "gcTime")) === 300000,
    "viewer cache options changed",
  );
  const guard = objectProperty(objectProperty(opts, "hooks"), "afterResponse")
      .elements[0],
    parser = objectProperty(opts, "parseJson");
  assert(
    guard.async &&
      findNodes(
        guard,
        (n) => n.type === "CallExpression" && n.callee.name === "Error",
      ).length === 1,
    "non-OK viewer response no longer plain Error",
  );
  const active = ex.get("o"),
    passive = ex.get("G");
  const passiveOptions = exactlyOne(
    findNodes(
      passive,
      (n) =>
        n.type === "ObjectExpression" &&
        n.properties.some((p) => propertyName(p.key) === "enabled"),
    ),
    "passive query override",
  );
  assert(
    literal(objectProperty(passiveOptions, "enabled")) === false,
    "passive observer started automatic reads",
  );
  const builderCall = exactlyOne(
    findNodes(
      active,
      (n) =>
        n.type === "CallExpression" &&
        n.callee.type === "Identifier" &&
        n.arguments[0]?.type === "MemberExpression" &&
        propertyName(n.arguments[0].property) === "data",
    ),
    "actual following Set builder",
  );
  const builder = local(f, builderCall.callee);
  assert(
    findNodes(
      builder,
      (n) =>
        n.type === "CallExpression" &&
        propertyName(n.callee.property) === "toLowerCase",
    ).length === 2,
    "following identity folding changed",
  );
  assert(
    findNodes(
      builder,
      (n) =>
        n.type === "CallExpression" &&
        propertyName(n.callee.property) === "trim",
    ).length === 0,
    "following Set started trimming identifiers",
  );
  for (const body of [active, passive])
    assert(
      calls(body, imported(f, 779106).id.name, "f").length === 1,
      "viewer-key resolver boundary changed",
    );
  const ranges = {
    query: add(
      f,
      query,
      "303599.Q: raw-viewer key, capped read and query policy",
    ),
    request: add(f, request, "actual1000-row following GET with exact signal"),
    guard: add(f, guard, "non-OK plain error; successful cloned blank guard"),
    parser: add(f, parser, "strict array parser with typed JSON/shape errors"),
    key: add(
      f,
      local(f, ex.get("j")),
      "303599.j raw viewer-following cache key",
    ),
    set: add(
      f,
      builder,
      "legacy user_id priority and case folding without trim",
    ),
    active: add(
      f,
      active,
      "303599.o active readiness/error/set/membership projection",
    ),
    passive: add(
      f,
      passive,
      "303599.G enabled:false cache observer; unknown remains undefined",
    ),
  };
  const viewer = await get(779106, source("fd402d4185b44ce9")),
    selector = await get(92245, source("fd402d4185b44ce9"));
  add(
    viewer,
    viewer.node,
    "actual viewer-key resolver; identity store external",
  );
  add(
    selector,
    exportsOf(selector, 92245).get("$"),
    "trimmed userId/address selector is not auth proof",
  );
  const consumers = [];
  for (const [id, name, exportName] of [
    [400466, "13c13db9eb86191b", "Q"],
    [163807, "decc1b8a23be2e25", "o"],
    [949060, "eb0b23ee6feb7543", "G"],
  ]) {
    const consumer = await get(id, source(name)),
      scope =
        id === 949060
          ? local(consumer, exportsOf(consumer, id).get("f"))
          : consumer.node;
    const call = exactlyOne(
      calls(scope, imported(consumer, 303599).id.name, exportName),
      `actual${id} to303599.${exportName} caller`,
    );
    const result = {
      module: id,
      calledExport: exportName,
      factory: consumer.provenance,
      invocation: add(
        consumer,
        call,
        `actual${id} invokes303599.${exportName}`,
      ),
    };
    if (id === 949060) {
      const binding = exactlyOne(
        findNodes(
          scope,
          (n) => n.type === "VariableDeclarator" && n.init === call,
        ),
        "actual passive membership result",
      );
      const props = exactlyOne(
        findNodes(
          scope,
          (n) =>
            n.type === "ObjectExpression" &&
            n.properties.some(
              (p) => propertyName(p.key) === "initialIsFollowing",
            ),
        ),
        "actual follow-button props",
      );
      assert(
        objectProperty(props, "initialIsFollowing").name === binding.id.name &&
          literal(objectProperty(props, "hideUntilReady")) === true,
        "passive membership is not actual button initial state",
      );
      result.buttonProps = add(
        consumer,
        props,
        "actual passive value supplied as initialIsFollowing/hideUntilReady",
      );
    }
    consumers.push(result);
  }
  const client = await get(759257, source("1e479323ffe53c14"));
  add(
    client,
    exportsOf(client, 759257).get("j"),
    "existing website client/defaults credited686",
  );
  const origin = await get(503630, source("1e479323ffe53c14")),
    url = exportsOf(origin, 503630).get("R");
  assert(
    url.body.value === "https://frontend-api-v3.pump.fun",
    "viewer service origin changed",
  );
  exactlyOne(
    calls(
      exportsOf(client, 759257).get("j"),
      imported(client, 503630).id.name,
      "R",
    ),
    "actual j origin",
  );
  add(origin, url, "website service origin");
  const http = await get(30181, source("01ad4f413e529b60")),
    ctor = exportsOf(http, 30181).get("K");
  exactlyOne(
    calls(ctor, imported(http, 402030).id.name, "createContractClient"),
    "actual K contract constructor",
  );
  add(http, ctor, "existing K constructor");
  const barrel = await get(402030, source("2b47dd0b38a1608f"));
  add(
    barrel,
    exactlyOne(
      findNodes(
        barrel.node,
        (n) =>
          n.type === "SpreadElement" &&
          member(
            n.argument,
            imported(barrel, 972407).id.name,
            "followingRoutes",
          ),
      ),
      "following route catalog inclusion",
    ),
    "existing following catalog membership",
  );
  const transport = await get(898661, source("2b47dd0b38a1608f"));
  add(
    transport,
    transport.node,
    "existing raw JSON/error transport credited686/691",
  );
  const prerequisitePath = "reconstruction/profile-lookup/client.mjs",
    hash = sha256(await fs.readFile(path.join(root, prerequisitePath)));
  assert(
    hash === "e8039acc986f36dc614f976c348032644a7ed4d7115f75091142a091a8c98b52",
    "unreviewed870 shared error class",
  );
  const extractor = createSchemaExtractor(corpus, {
      sources: { 972407: source("2b47dd0b38a1608f") },
    }),
    declaration = await extractor.declaration(972407, "followingRoutes"),
    wrapped = objectProperty(declaration.node.arguments[0], operation),
    route = wrapped.arguments[1],
    fields = {};
  assert(
    literal(wrapped.arguments[0]) === "graph.read",
    "viewer declaration scope changed",
  );
  for (const name of ["params", "query", "response"])
    fields[name] = await extractor.compile(
      objectProperty(route, name),
      declaration.factory,
    );
  add(
    declaration.factory,
    wrapped,
    "existing graph.read declaration; not row validation by the raw client",
  );
  for (const x of extractor.witnesses()) {
    if (
      x.label.startsWith("factory ") ||
      x.label === "declaration 972407.followingRoutes"
    )
      continue;
    const c = await corpus.capture(x.source),
      key = `${x.source}:${x.utf16.join(":")}`;
    fragments.set(key, { ...x, text: c.text.slice(...x.utf16) });
  }
  return {
    schemaVersion: 1,
    authority: "Authenticated AST only; captured JS never evaluated",
    frozenInputs: corpus.anchors,
    implementation: {
      path: "reconstruction/viewer-following/client.mjs",
      sha256: sha256(
        await fs.readFile(
          path.join(root, "reconstruction/viewer-following/client.mjs"),
        ),
      ),
    },
    prerequisite: {
      pullRequest: 870,
      exactPublicHead: "e46c14ea3857da7ef6eecc9f7945622f5dbcfc39",
      path: prerequisitePath,
      sha256: hash,
      novelCredit: false,
    },
    operation,
    entry: {
      module: 303599,
      exports: ["Q", "j", "G", "o"],
      factory: f.provenance,
      ranges,
    },
    consumers,
    policy: {
      limit: 1000,
      pagination:
        "One capped read; no complete graph/continuation or total synthesized",
      response:
        "Strict array JSON parser, successful blank guard, non-OK plain Error, post-transport null guard",
      identity:
        "Case-fold address and user_id??userId strings without trim; no DTO normalization",
      active:
        "Default enabled plus viewer, ready=enabled&&query.isSuccess, isError preserved; unknown membership undefined",
      passive:
        "enabled:false cache observer; value only when viewer/target/isSuccess are truthy",
      credentials: "No override in callback; inherits website j GET defaults",
    },
    declarations: extractor.document({
      "x-viewer-following": { scope: "graph.read", ...fields },
    }),
    factories: [...factories.values()],
    fragments: [...fragments.values()],
    limits: [
      "Exact870 error class dependency unchanged, zero novel credit;767 list pager/882 reciprocal reads/854 mutual reads remain distinct",
      "Viewer key is an external request/cache input, not an authenticated principal",
      "1000-row source cap is not a complete graph guarantee; known false means absent from supplied successful set",
      "Strict outer-array parse does not validate or normalize individual profile rows",
      "Query/cache runtime/React memo/effect scheduling and browser cookies external; actual callers do not establish rendered UI parity",
      "No production request/server/auth/provider/mutation/UI mount/ledger/compatibility qualification",
    ],
  };
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const mode = process.argv[2];
  if (process.argv.length !== 3 || !["--write", "--check"].includes(mode))
    throw Error("usage: original-viewer-following.mjs --write|--check");
  const root = fileURLToPath(new URL("..", import.meta.url)),
    target = path.join(root, "reconstruction/viewer-following/contract.json"),
    value = JSON.stringify(await extractViewerFollowing(root), null, 2) + "\n";
  if (mode === "--check") {
    if ((await fs.readFile(target, "utf8")) !== value)
      throw Error("viewer-following artifact changed");
  } else await fs.writeFile(target, value);
  console.log(
    `${mode === "--check" ? "Verified" : "Wrote"} original viewer-following state`,
  );
}
