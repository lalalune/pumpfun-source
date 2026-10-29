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
  literal,
  sha256,
} from "./original-contracts/source.mjs";

const defaultRoot = fileURLToPath(new URL("../", import.meta.url));
const packetDirectory = "reconstruction/home-feed-state";
const contexts = [
  "evidence/web/objects/3740fc4e7a24596d.js",
  "evidence/web/objects/cf2bb278631744da.js",
];
const stateSource = "evidence/web/objects/11be0c4b34eb27cb.js";
const expectedNormalizers = [
  "7fb1990b807291b37cfd559db80e1d428cea58bfa9007bd6e823f78785a43c7f",
  "960ab98a1f113c07b8a86ad009f505faaadc056a45f4a07d9ae86baf0aca0310",
  "70a717bf9bc6bf6a0f33a8d910030e7eb13df2348e96b805af3d43b58dab86ec",
  "c40d7f92b3999c9387da21f01eca0802a91204b49bddbe6fa41088133d5425c8",
  "45e56c6c56b6ebc80d4b1979b3ef6bd3c83ecf5aed7b773183e164311ae892dd",
  "b7754f3a78d17d64d1df27ef1649d16e623c6e16fc3e0b2b4edbe3386550aad4",
];

function exportsOf(factory) {
  const result = new Map();
  for (const call of findNodes(
    factory.node,
    (n) =>
      n.type === "CallExpression" &&
      n.callee.type === "MemberExpression" &&
      n.callee.object.name === factory.runtime &&
      propertyName(n.callee.property) === "s",
  )) {
    if (call.arguments[1] && call.arguments[1].value !== factory.id) continue;
    const values = call.arguments[0]?.elements;
    if (!values) continue;
    for (let i = 0; i < values.length; i += 3) {
      if (values[i]?.type === "StringLiteral" && values[i + 1]?.value === 0)
        result.set(values[i].value, values[i + 2]);
    }
  }
  return result;
}

function declaration(factory, name) {
  const candidates = [];
  for (const statement of factory.node.body.body) {
    if (statement.type === "VariableDeclaration")
      for (const value of statement.declarations) {
        if (value.id.name === name) candidates.push(value);
      }
    if (statement.type === "FunctionDeclaration" && statement.id?.name === name)
      candidates.push(statement);
  }
  return exactlyOne(candidates, `${factory.id} top-level ${name}`);
}

function exported(factory, key) {
  const value = exportsOf(factory).get(key);
  assert.ok(value, `${factory.id}.${key}`);
  return value.type === "Identifier"
    ? (declaration(factory, value.name).init ??
        declaration(factory, value.name))
    : value;
}

function imported(factory, id) {
  return exactlyOne(
    findNodes(
      factory.node,
      (n) =>
        n.type === "VariableDeclarator" &&
        n.init?.type === "CallExpression" &&
        n.init.callee.type === "MemberExpression" &&
        n.init.callee.object.name === factory.runtime &&
        ["i", "r"].includes(propertyName(n.init.callee.property)) &&
        n.init.arguments[0]?.value === id,
    ),
    `${factory.id} import ${id}`,
  ).id.name;
}

export async function derive(appRoot = defaultRoot) {
  const corpus = await openCorpus(appRoot);
  const sources = [],
    witnesses = [];
  async function factory(id, source) {
    const f = await corpus.factory(id, source ? { source } : {});
    sources.push(f.provenance);
    return f;
  }
  function witness(f, node, label) {
    witnesses.push({ ...f.witness(node, label), astType: node.type });
    return f.text(node);
  }
  const state = await factory(99859, stateSource);
  const constants = await factory(349879);
  const ttl = literal(exported(constants, "t"));
  const previewCap = literal(exported(constants, "I"));
  assert.equal(ttl, 15000);
  assert.equal(previewCap, 3);
  witness(constants, exported(constants, "t"), "query stale time");
  witness(constants, exported(constants, "I"), "pending preview cap");
  const caip = await factory(
    646908,
    "evidence/web/objects/1e479323ffe53c14.js",
  );
  const caipValues = {};
  for (const key of ["d", "W"]) {
    const node = exported(caip, key);
    caipValues[key] = literal(node);
    witness(caip, node, `used CAIP literal ${key}`);
  }
  const helperCode = [],
    helperBindings = [];
  for (const [index, context] of contexts.entries()) {
    const assets = await factory(917341, context);
    const followers = await factory(559015, context);
    const chain = await factory(541710, context);
    const mint = await factory(639374, context);
    const assetsFn = exported(assets, "E");
    const followersFn = exported(followers, "i");
    const filterName = followersFn.body.consequent.callee.name;
    const filter = declaration(followers, filterName).init;
    const chainFn = exported(chain, "T"),
      mintFn = exported(mint, "f");
    const chainAlias = imported(chain, 646908),
      mintAlias = imported(mint, 344048);
    helperCode.push(`function helpers${index}(decodeBase58){
      const assets=${witness(assets, assetsFn, "asset projection, existing helper")};
      const excludeAuthor=(()=>{const ${filterName}=${witness(followers, filter, "holder filter and count/reference behavior")};return ${witness(followers, followersFn, "exclude callout author from followed holders")};})();
      const chainFromId=(()=>{const ${chainAlias}=${JSON.stringify(caipValues)};return ${witness(chain, chainFn, "used CAIP pass-through only")};})();
      const isSolanaMint=(()=>{const ${mintAlias}={f:{decode:decodeBase58}};return ${witness(mint, mintFn, "32 decoded bytes; decoder errors return false")};})();
      return {assets,excludeAuthor,chainFromId,isSolanaMint};
    }`);
    helperBindings.push({
      context,
      assets: assets.provenance.sha256,
      followers: followers.provenance.sha256,
      chain: chain.provenance.sha256,
      mint: mint.provenance.sha256,
    });
  }
  const normalizerCode = [],
    normalizerBindings = [];
  const variants = corpus.index.modules.filter((m) => m.ids.includes(154703));
  assert.deepEqual(
    new Set(variants.map((m) => m.sha256)),
    new Set(expectedNormalizers),
  );
  for (const [index, variant] of variants.entries()) {
    assert.equal(variant.origins.length, 1);
    const f = await factory(154703, variant.origins[0].source);
    const metrics = await factory(621624, variant.origins[0].source);
    const aliases = {
      [imported(f, 621624)]:
        `{P:${witness(metrics, exported(metrics, "P"), "used engagement projection")}}`,
      [imported(f, 917341)]: "{E:helpers.assets}",
      [imported(f, 559015)]: "{i:helpers.excludeAuthor}",
      [imported(f, 639374)]: "{f:helpers.isSolanaMint}",
      [imported(f, 541710)]: "{T:helpers.chainFromId}",
    };
    const declarations = f.node.body.body.filter(
      (n) => n.type === "VariableDeclaration" && n.kind === "let",
    );
    const retained = declarations
      .map((n) => witness(f, n, "normalizer private declarations"))
      .join("\n");
    const row = witness(f, exported(f, "y"), "complete row normalizer");
    normalizerCode.push(`function normalizer${index}(helpers){
      const ${Object.entries(aliases)
        .map(([a, value]) => `${a}=${value}`)
        .join(",")};
      ${retained}
      return ${row};
    }`);
    normalizerBindings.push({
      sha256: variant.sha256,
      source: variant.origins[0].source,
      metrics: metrics.provenance.sha256,
    });
  }
  const coreDeclarations = state.node.body.body.filter(
    (n) =>
      (n.type === "VariableDeclaration" && n.kind === "let") ||
      n.type === "FunctionDeclaration",
  );
  const core = coreDeclarations
    .map((n) => witness(state, n, "complete query/state private declaration"))
    .join("\n");
  const hook = witness(
    state,
    exported(state, "r"),
    "complete memoized read-state hook",
  );
  const prefetch = witness(
    state,
    exported(state, "Z"),
    "complete matching prefetch boundary",
  );
  const aliases = {
    [imported(state, 445242)]: "{c:useMemoCache}",
    [imported(state, 690877)]: "{useQuery}",
    [imported(state, 352386)]: "React",
    [imported(state, 349879)]: JSON.stringify({ t: ttl, I: previewCap }),
    [imported(state, 735821)]: "{c:150,Z:fetchHomeFeed}",
    [imported(state, 154703)]: "{y:normalizeRow}",
    [imported(state, 894107)]: "{useHomeFeedSeed}",
  };
  const seed = await factory(894107);
  witness(
    seed,
    exported(seed, "useHomeFeedSeed"),
    "seed context accessor; provider remains external",
  );
  const codec = await factory(344048);
  const codecNamespace = exported(codec, "f");
  assert.equal(codecNamespace.type, "CallExpression");
  assert.equal(
    literal(codecNamespace.arguments[0]),
    "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz",
  );
  witness(
    codec,
    codecNamespace,
    "base58 namespace dependency; decoder remains an injected capability",
  );
  witness(
    codec,
    codecNamespace.arguments[0],
    "base58 alphabet used by the captured dependency",
  );
  const memoBridge = await factory(445242);
  witness(
    memoBridge,
    exactlyOne(
      findNodes(
        memoBridge.node,
        (n) =>
          n.type === "CallExpression" &&
          n.callee.type === "MemberExpression" &&
          propertyName(n.callee.property) === "r" &&
          n.arguments[0]?.value === 532815,
      ),
      "compiler memo bridge",
    ),
    "compiler wrapper delegates to captured runtime",
  );
  const memoRuntime = await factory(532815);
  witness(
    memoRuntime,
    exactlyOne(
      findNodes(
        memoRuntime.node,
        (n) =>
          n.type === "AssignmentExpression" &&
          n.left.type === "MemberExpression" &&
          propertyName(n.left.property) === "c" &&
          n.right.type === "FunctionExpression",
      ),
      "compiler cache function",
    ),
    "compiler cache delegates to React dispatcher useMemoCache",
  );
  // Close both actual callsites; this does not reconstruct their UI renderers.
  for (const [id, source, alias] of [
    [163807, "evidence/web/objects/c3601a995a6b7f37.js", "em"],
    [117330, "evidence/web/objects/6a1606765ef3e83e.js", "nA"],
  ]) {
    const candidates = corpus.index.modules
      .filter((m) => m.ids.includes(id))
      .flatMap((m) => m.origins);
    const f = await factory(
      id,
      candidates.length === 1 ? candidates[0].source : source,
    );
    const actualAlias = imported(f, 99859);
    assert.equal(actualAlias, alias);
    const calls = findNodes(
      f.node,
      (n) =>
        n.type === "CallExpression" &&
        n.callee.type === "SequenceExpression" &&
        n.callee.expressions.at(-1)?.type === "MemberExpression" &&
        n.callee.expressions.at(-1).object.name === actualAlias &&
        ["r", "Z"].includes(propertyName(n.callee.expressions.at(-1).property)),
    );
    assert.ok(calls.length > 0);
    for (const call of calls)
      witness(
        f,
        call,
        "actual hook/prefetch consumer; renderer outside boundary",
      );
    if (id === 117330) {
      const handoff = exactlyOne(
        findNodes(
          f.node,
          (n) =>
            n.type === "CallExpression" &&
            n.arguments[0]?.name === "nC" &&
            n.arguments[1]?.type === "ObjectExpression" &&
            n.arguments[1].properties.some(
              (p) => propertyName(p.key) === "feed" && p.value?.name === "g",
            ),
        ),
        "screener feed state handoff",
      );
      witness(
        f,
        handoff,
        "screener passes complete hook state to feed renderer",
      );
    } else {
      const handoff = exactlyOne(
        findNodes(
          f.node,
          (n) =>
            n.type === "ObjectProperty" &&
            propertyName(n.key) === "for-you" &&
            n.value.type === "ObjectExpression" &&
            n.value.properties.some(
              (p) => p.type === "SpreadElement" && p.argument.name === "J",
            ),
        ),
        "Home for-you read state handoff",
      );
      witness(
        f,
        handoff,
        "Home adapts callouts to rows; other feed branches/renderers excluded",
      );
    }
  }
  const transport = await readFile(
    path.join(corpus.root, "contracts/original-home-feed.json"),
  );
  const code = await format(
    `// Reconstructed source boundary. Captured factories are never imported or evaluated.
    // Callers must select reviewed physical variants and supply the external runtimes.
    ${helperCode.join("\n")}
    ${normalizerCode.join("\n")}
    const helpersByContext=new Map([${contexts.map((c, i) => `[${JSON.stringify(c)},helpers${i}]`).join(",")}]);
    const normalizers=new Map([${normalizerBindings.map((c, i) => `[${JSON.stringify(c.sha256)},normalizer${i}]`).join(",")}]);
    export const normalizerVariants=Object.freeze(${JSON.stringify(normalizerBindings)});
    export const helperContexts=Object.freeze(${JSON.stringify(contexts)});
    export function createHomeFeedRead({normalizerVariant,helperContext,React,useMemoCache,useQuery,useHomeFeedSeed,fetchHomeFeed,decodeBase58,timers=globalThis}){
      const createHelpers=helpersByContext.get(helperContext),createNormalizer=normalizers.get(normalizerVariant);
      if(!createHelpers||!createNormalizer)throw new TypeError('Explicit reviewed helper context and normalizer variant required');
      for(const capability of [useMemoCache,useQuery,useHomeFeedSeed,fetchHomeFeed,decodeBase58,timers.setInterval,timers.clearInterval])if(typeof capability!=='function')throw new TypeError('Missing explicit Home-feed runtime capability');
      const normalizeRow=createNormalizer(createHelpers(decodeBase58));
      const setInterval=timers.setInterval.bind(timers),clearInterval=timers.clearInterval.bind(timers);
      const ${Object.entries(aliases)
        .map(([a, value]) => `${a}=${value}`)
        .join(",")};
      ${core}
      return {normalizeRow,prefetchHomeFeed:${prefetch},useHomeFeed:${hook}};
    }
  `,
    { parser: "babel", singleQuote: true },
  );
  const contract = {
    formatVersion: 1,
    authority:
      "Captured source attribution and complete maintained function translation; no original factory execution",
    frozenInputs: corpus.anchors,
    sources,
    witnesses,
    implementation: {
      path: `${packetDirectory}/client.mjs`,
      sha256: sha256(code),
    },
    normalizationVariants: normalizerBindings,
    helperContexts: helperBindings,
    acceptedRequestBoundary: {
      path: "contracts/original-home-feed.json",
      sha256: sha256(transport),
      operation: "GET /home-feed",
      port: "fetchHomeFeed(options) implements accepted735821.Z; no transport or telemetry implementation is copied here",
    },
    state: {
      initialVisible: 12,
      appendVisible: 12,
      showNewVisibleCap: 40,
      pendingTickMs: 2500,
      pendingCountCap: 25,
      pendingPreviewCap: 3,
      queryStaleMs: 15000,
      queryRetry: 3,
      queryRefetchMs: 15000,
      refetchOnWindowFocus: true,
      refetchIntervalInBackground: false,
      weakIdentity:
        "WeakMap keyed by raw object; undefined results recompute, null results cache; memoized raw coins-array identity",
      duplicatePolicy: "First normalized key wins in raw response order",
      seed: "Matching chain and equality to initial viewer; current data falls back to seed",
      paging:
        "Local visible-key expansion of ranked snapshots, not HTTP cursor pagination",
      viewer:
        "Reset visible keys, retired set and pending counter when viewer changes",
      tick: "Enabled and unseen rows required; this effect itself has no document visibility guard",
    },
    runtimePorts: [
      "React useState/useRef/useEffect",
      "React compiler useMemoCache",
      "useQuery runtime/cache/observer",
      "seed context/provider",
      "accepted735821.Z request",
      "base58 decoder used by639374.f",
      "interval timer scheduler",
    ],
    adaptations: [
      "Explicit factory/variant/capability selection is an authored host boundary; no original active-variant winner is inferred",
      "Compiler memo-cache shape and complete hook body retained; no React scheduling/provider implementation recovered",
    ],
    limits: [
      "No original service request, auth/session, cookies, wallet/signing, mutation, server implementation, maintained-app UI mount, native API or feature-milestone qualification",
      "Synthetic qualification hosts may exercise the translated functions; they are not recovered website/provider implementations",
      "No new original home-feed operation count or copied1374/1472/1523/891 implementation",
      "Complete selected source functions are retained; injected runtimes remain external",
    ],
    mounted: false,
    productionOperationsQualified: 0,
  };
  return { code, contract };
}

export async function verify(appRoot = defaultRoot, supplied) {
  const actual = await derive(appRoot);
  const location = path.join(appRoot, packetDirectory);
  assert.equal(
    supplied?.code ??
      (await readFile(path.join(location, "client.mjs"), "utf8")),
    actual.code,
  );
  assert.deepEqual(
    supplied?.contract ??
      JSON.parse(await readFile(path.join(location, "contract.json"), "utf8")),
    actual.contract,
  );
  return {
    normalizerVariants: actual.contract.normalizationVariants.length,
    witnesses: actual.contract.witnesses.length,
    mounted: false,
    productionOperationsQualified: 0,
  };
}
async function main() {
  const args = process.argv.slice(2);
  let root = defaultRoot,
    mode;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--app-root" && args[i + 1]) root = path.resolve(args[++i]);
    else if (["--write", "--check"].includes(args[i]) && !mode) mode = args[i];
    else
      throw Error(
        "usage: original-home-feed-state.mjs [--app-root PATH] --check|--write",
      );
  }
  if (!mode) throw Error("explicit --write or --check required");
  if (mode === "--write") {
    const actual = await derive(root);
    await mkdir(path.join(root, packetDirectory), { recursive: true });
    await writeFile(
      path.join(root, packetDirectory, "client.mjs"),
      actual.code,
    );
    await writeFile(
      path.join(root, packetDirectory, "contract.json"),
      JSON.stringify(actual.contract, null, 2) + "\n",
    );
  }
  console.log(JSON.stringify(await verify(root)));
}
if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
)
  await main();
