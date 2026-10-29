import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { parse } from "@babel/parser";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  member,
  propertyName,
  sha256,
} from "./original-contracts/source.mjs";
import { verifyMarketBoardBindings } from "./verify-market-board-bindings.mjs";

const ROOT = fileURLToPath(new URL("..", import.meta.url));
const TARGET = "reconstruction/market-board-response/contract.json";
const VARIANTS = [
  [
    "initial-board-chunk",
    "3740fc4e7a24596d",
    "609398a036a8f03009d8e18f6218b0db40076b5a728a62b1014447cd99fcc326",
  ],
  [
    "other-retained-board-chunk",
    "cf2bb278631744da",
    "dbed6512bf8d85a7a28e44bfd719c9b2b3370bd2ec239920c5a4c8c4f3e93acf",
  ],
];
function exported(factory, name) {
  const arrays = findNodes(
    factory.node,
    (n) =>
      n.type === "CallExpression" && member(n.callee, factory.runtime, "s"),
  );
  const matches = [];
  for (const call of arrays) {
    const entries = call.arguments[0]?.elements ?? [];
    for (let i = 0; i < entries.length; i += 3)
      if (entries[i]?.value === name) matches.push(entries[i + 2]);
  }
  return exactlyOne(matches, `export ${name}`);
}
function evidence(factory, node, label) {
  return { ...factory.witness(node, label), expression: factory.text(node) };
}
function directCall(node, alias, name) {
  if (node.type !== "CallExpression") return false;
  const callee =
    node.callee.type === "SequenceExpression"
      ? node.callee.expressions.at(-1)
      : node.callee;
  return member(callee, alias, name);
}
export async function buildMarketBoardResponse(root = ROOT) {
  const prior = await verifyMarketBoardBindings(root);
  const requestBytes = await readFile(
    path.join(root, "contracts/market-board-bindings.json"),
  );
  const request = JSON.parse(requestBytes);
  const corpus = await openCorpus(root);
  const variants = [];
  for (const [context, object, expected] of VARIANTS) {
    const factory = await corpus.factory(503774, {
      source: `evidence/web/objects/${object}.js`,
    });
    assert.equal(factory.provenance.sha256, expected);
    const mapper = exactlyOne(
      factory.node.body.body.filter(
        (n) => n.type === "FunctionDeclaration" && n.id.name === "d",
      ),
      "coin mapper",
    );
    const fields = exactlyOne(
      findNodes(
        mapper,
        (n) =>
          n.type === "ObjectExpression" &&
          n.properties.some((p) => propertyName(p.key) === "board_program"),
      ),
      "coin fields",
    );
    const cache = exactlyOne(
      findNodes(
        factory.node,
        (n) => n.type === "NewExpression" && n.callee.name === "Map",
      ),
      "timestamp cache",
    );
    const timestamp = exactlyOne(
      findNodes(
        mapper,
        (n) =>
          n.type === "CallExpression" &&
          n.callee.type === "ArrowFunctionExpression" &&
          n.callee.params.length === 2,
      ),
      "age conversion/cache",
    );
    const returned = exactlyOne(
      mapper.body.body.filter((n) => n.type === "ReturnStatement"),
      "coin mutations",
    );
    variants.push({
      context,
      factory: factory.provenance,
      query: evidence(
        factory,
        exported(factory, "q"),
        "response.entries to ordered coin list",
      ),
      mapper: evidence(factory, mapper, "complete coin projection"),
      timestamp: evidence(
        factory,
        timestamp,
        "clock evaluation and mint-keyed cache",
      ),
      cache: evidence(factory, cache, "module-lifetime timestamp map"),
      seed: evidence(
        factory,
        exported(factory, "$"),
        "seed timestamps from initial coins",
      ),
      fields: fields.properties.map((p) => ({
        name: propertyName(p.key),
        ...evidence(factory, p.value, `coin.${propertyName(p.key)}`),
      })),
      optionalAssignments: findNodes(
        returned,
        (n) =>
          n.type === "AssignmentExpression" &&
          member(n.left, "p", propertyName(n.left?.property)),
      ).map((n) => ({
        name: propertyName(n.left.property),
        ...evidence(factory, n, "optional coin field"),
      })),
    });
  }
  const expectedFields = variants[0].fields.map((p) => p.name);
  assert.deepEqual(
    variants[1].fields.map((p) => p.name),
    expectedFields,
  );
  const adapterBytes = await readFile(
    path.join(root, "reconstruction/market-board-response/response.mjs"),
  );
  const adapterAst = parse(adapterBytes.toString("utf8"), {
    sourceType: "module",
  });
  const adapterFields = exactlyOne(
    findNodes(
      adapterAst,
      (n) =>
        n.type === "ObjectExpression" &&
        n.properties.some((p) => propertyName(p.key) === "board_program"),
    ),
    "maintained fields",
  );
  assert.deepEqual(
    adapterFields.properties.map((p) => propertyName(p.key)),
    expectedFields,
  );
  const hook = await corpus.factory(379705, {
    source: "evidence/web/objects/dba17a249156c6ff.js",
  });
  assert.equal(hook.provenance.sha256, request.factories.exploreHook.sha256);
  const handoff = exactlyOne(
    findNodes(hook.node, (n) => directCall(n, "R", "$")),
    "hook board response handoff",
  );
  assert.equal(
    handoff.arguments.length,
    1,
    "actual hook supplies no served-rank offset",
  );
  const wrapper = await corpus.factory(583448, {
    source: "evidence/web/objects/3740fc4e7a24596d.js",
  });
  const wrapperImport = exactlyOne(
    findNodes(
      wrapper.node,
      (n) =>
        n.type === "VariableDeclarator" &&
        n.id.name === "c" &&
        member(n.init?.callee, wrapper.runtime, "i") &&
        n.init.arguments[0]?.value === 503774,
    ),
    "wrapper response import",
  );
  const seedCall = exactlyOne(
    findNodes(hook.node, (n) => directCall(n, "I", "$")),
    "initial-coin seed call",
  );
  const seedGate = exactlyOne(
    findNodes(
      hook.node,
      (n) => n.type === "LogicalExpression" && n.right === seedCall,
    ),
    "initial-coin seed gate",
  );
  const seedMode = exactlyOne(
    findNodes(
      hook.node,
      (n) => n.type === "VariableDeclarator" && n.id.name === "Q",
    ),
    "social-terminal mode gate",
  );
  const postprocess = exactlyOne(
    findNodes(hook.node, (n) => directCall(n, "O", "f")),
    "postprocess handoff",
  );
  const localSlice = exactlyOne(
    findNodes(
      hook.node,
      (n) => n.type === "CallExpression" && member(n.callee, "u", "slice"),
    ),
    "local displayed page",
  );
  const fetchCall = exactlyOne(
    findNodes(
      hook.node,
      (n) => n.type === "CallExpression" && n.callee.name === "fetch",
    ),
    "board/list fetch",
  );
  const post = await corpus.factory(493025, {
    source: "evidence/web/objects/fd402d4185b44ce9.js",
  });
  const clock = await corpus.factory(668487, {
    source: "evidence/web/objects/1e479323ffe53c14.js",
  });
  const evm = await corpus.factory(605587, {
    source: "evidence/web/objects/2c867fef5c76d400.js",
  });
  const chains = await corpus.factory(646908, {
    source: "evidence/web/objects/1e479323ffe53c14.js",
  });
  const exposure = await corpus.factory(541710, {
    source: "evidence/web/objects/3740fc4e7a24596d.js",
  });
  const exposureVariants = [];
  for (const object of [
    "3740fc4e7a24596d",
    "cf2bb278631744da",
    "27a1ee00eb5909ec",
  ]) {
    const factory = await corpus.factory(541710, {
      source: `evidence/web/objects/${object}.js`,
    });
    const imported = exactlyOne(
      findNodes(
        factory.node,
        (n) =>
          n.type === "VariableDeclarator" &&
          member(n.init?.callee, factory.runtime, "i") &&
          n.init.arguments[0]?.value === 646908,
      ),
      "retained chain namespace",
    );
    const predicate = exported(factory, "T");
    assert.equal(predicate.type, "ArrowFunctionExpression");
    const parameter = predicate.params[0].name;
    const body = predicate.body;
    assert.equal(body.type, "ConditionalExpression");
    assert.equal(body.test.operator, "||");
    for (const [test, field] of [
      [body.test.left, "d"],
      [body.test.right, "W"],
    ]) {
      assert.equal(test.operator, "===");
      assert.equal(test.left.name, parameter);
      assert.ok(member(test.right, imported.id.name, field));
    }
    assert.equal(body.consequent.name, parameter);
    assert.equal(body.alternate.operator, "void");
    assert.equal(body.alternate.argument.value, 0);
    exposureVariants.push({
      factory: factory.provenance,
      namespace: evidence(factory, imported, "actual646908 namespace import"),
      predicate: evidence(
        factory,
        predicate,
        "same Near/Starknet retention boundary; no active variant winner",
      ),
    });
  }
  return {
    version: 1,
    classification:
      "source-adapted response boundary; no acquired board data or native compatibility",
    requestAttribution: {
      existingWork: "merged PR695",
      contract: "contracts/market-board-bindings.json",
      sha256: sha256(requestBytes),
      verified: prior,
      operations: request.operations,
      origin: request.origin,
    },
    corpus: corpus.anchors,
    variants,
    handoff: {
      hook: hook.provenance,
      fetch: evidence(
        hook,
        fetchCall,
        "credentials include; JSON response parsed by branch",
      ),
      boardResponse: evidence(hook, handoff, "single-argument board wrapper"),
      wrapper: wrapper.provenance,
      wrapperImport: evidence(
        wrapper,
        wrapperImport,
        "wrapper imports503774 as c",
      ),
      wrapperExport: evidence(
        wrapper,
        exported(wrapper, "$"),
        "wrapper forwards e/t to c.q",
      ),
      initialSeedGate: evidence(
        hook,
        seedGate,
        "initial coins seed only when H and social-terminal Q are truthy",
      ),
      initialSeedMode: evidence(
        hook,
        seedMode.init,
        "source of social-terminal mode predicate",
      ),
      postprocess: evidence(
        hook,
        postprocess,
        "IPFS/alias postprocessing follows board projection",
      ),
      localPage: evidence(
        hook,
        localSlice,
        "normal featured/trending display slices locally",
      ),
      postprocessor: post.provenance,
      postprocessorExport: evidence(
        post,
        exported(post, "f"),
        "mutating image/metadata/alias postprocess; outside maintained adapter",
      ),
    },
    explicitPorts: {
      nowMs: {
        factory: clock.provenance,
        expression: evidence(
          clock,
          exported(clock, "t"),
          "Date.now plus existing clock offset; offset service not reconstructed",
        ),
      },
      isEvmRecord: {
        factory: evm.provenance,
        expression: evidence(
          evm,
          exported(evm, "N"),
          "mint/chain EVM classifier; chain registry lookup remains supplied",
        ),
        closure: ["s", "i", "t"].map((name) =>
          evidence(
            evm,
            exactlyOne(
              evm.node.body.body.filter(
                (n) => n.type === "FunctionDeclaration" && n.id.name === name,
              ),
              `classifier closure ${name}`,
            ),
            `classifier closure ${name}; registry implementation remains outside unit`,
          ),
        ),
      },
      retainChainId: {
        meaning:
          "605587.g(chain) OR646908.L(chain) OR541710.T(chain)!=null, preserving short circuit; registry-dependent predicate supplied by caller",
        parts: [
          evidence(evm, exported(evm, "g"), "EVM chain predicate"),
          evidence(chains, exported(chains, "L"), "TON chain predicate"),
          evidence(
            exposure,
            exported(exposure, "T"),
            "Near/Starknet retained identifiers",
          ),
        ],
        exposureVariants,
      },
    },
    adapterSha256: sha256(adapterBytes),
    limits: [
      "Both physical503774 variants are bound independently; no runtime cache winner or complete catalog claim.",
      "No anonymous board acquisition: observed credentials include and auth-ready hook prerequisites do not establish public access.",
      "No response DTO validation or server ranking/filter/auth/error/pagination proof; original defaults are presentation transformations.",
      "No mounted Explore, network service, image rewrite, hook cache/refetch lifecycle, native compatibility or feature credit.",
      "Direct semantic checks exercise new maintained code; captured JavaScript is parsed and hashed only, never evaluated.",
    ],
  };
}
export async function verifyMarketBoardResponse(root = ROOT) {
  const actual = await readFile(path.join(root, TARGET), "utf8");
  assert.equal(
    actual,
    JSON.stringify(await buildMarketBoardResponse(root), null, 2) + "\n",
    "market response contract stale",
  );
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const args = process.argv.slice(2);
  assert.ok(
    args.every((arg) => ["--check", "--write"].includes(arg)) &&
      args.length <= 1,
    "use --check or --write",
  );
  if (args[0] === "--write")
    await writeFile(
      path.join(ROOT, TARGET),
      JSON.stringify(await buildMarketBoardResponse(), null, 2) + "\n",
    );
  else await verifyMarketBoardResponse();
  console.log(
    "Both captured board-response variants and actual request/response handoff verified; no network or capture execution",
  );
}
