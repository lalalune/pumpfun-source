import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  propertyName,
  objectProperty,
} from "./original-contracts/source.mjs";

export const APP_ROOT = fileURLToPath(new URL("..", import.meta.url));
export const OUTPUT = "reconstruction/balance-summary/contract.json";
const EXPECTED = [
  [
    524711,
    "87a44458ebf665fe",
    "dadc0b38be490a453d40051fca0e0ccab736951a921d9a71b867802d36d8eaa9",
  ],
  [
    524711,
    "864111a9a40a97f0",
    "b6438cee42592063a7b39d4b7bc7e309f27eb68ed6e9d9e2919da8683437b97d",
  ],
  [
    524711,
    "d96bd90b2de3d9da",
    "9ee77e30c3477bf495a93c0e1a43c835eedaa60520f5693225596881cdac621a",
  ],
  [
    524711,
    "a8933cf5deeab5bd",
    "5bbfa5818419ab77ec3f23176573ccdbbc3b3effe7354231d2bc2712611aa86d",
  ],
  [
    524711,
    "5c900f5590ba04fe",
    "44abb461d255ba2a12e430255b7ce095be2d68e8f0b9f658d3d91e36c15a2fb8",
  ],
  [
    524711,
    "a6c540af7c959989",
    "12d13770ea05abbe3cfb7478c209096462fc962ecc9be8ef52e67284ab70f56c",
  ],
  [
    38279,
    "ad7136d0b3a7f323",
    "8d71db5a2d47da722166199f0a64e93e0295051da46086355f136b93a3f3b89a",
  ],
  [
    465363,
    "a8933cf5deeab5bd",
    "0457d6da501f92a1a4e47d297a28feb6fae5512889e4eff04a9087ef1d956556",
  ],
];
const callMember = (n, name) =>
  n.type === "CallExpression" &&
  n.callee?.type === "MemberExpression" &&
  propertyName(n.callee.property) === name;
function exportBinding(f, target, name) {
  const calls = findNodes(
    f.node,
    (n) =>
      callMember(n, "s") &&
      n.arguments[0]?.type === "ArrayExpression" &&
      (n.arguments[1]?.value === target ||
        (!n.arguments[1] && f.ids.includes(target))),
  );
  const values = [];
  for (const call of calls) {
    const entries = call.arguments[0].elements;
    for (let i = 0; i < entries.length; i += 3)
      if (entries[i]?.value === name) values.push(entries[i + 2]);
  }
  return exactlyOne(values, `${target}.${name} export`);
}
function declaration(f, value) {
  const declarations = f.node.body.body.flatMap((n) =>
    n.type === "VariableDeclaration" ? n.declarations : [n],
  );
  return exactlyOne(
    declarations.filter(
      (n) =>
        [
          "VariableDeclarator",
          "FunctionDeclaration",
          "ClassDeclaration",
        ].includes(n.type) && n.id?.name === value.name,
    ),
    `factory-local declaration${value.name}`,
  );
}
const resolve = (f, value) =>
  value.type === "Identifier"
    ? (declaration(f, value).init ?? declaration(f, value))
    : value;
const unsequence = (n) =>
  n?.type === "SequenceExpression" ? n.expressions.at(-1) : n;
function imported(f, id) {
  return exactlyOne(
    findNodes(
      f.node,
      (n) =>
        n.type === "VariableDeclarator" &&
        n.init?.type === "CallExpression" &&
        ["i", "r"].includes(propertyName(n.init.callee?.property)) &&
        n.init.arguments[0]?.value === id,
    ),
    `import${id}`,
  );
}
function cite(f, node, label) {
  return { ...f.witness(node, label), text: f.text(node) };
}

export async function recover(root = APP_ROOT) {
  const corpus = await openCorpus(root);
  const factories = [];
  for (const [id, basename, hash] of EXPECTED) {
    const f = await corpus.factory(id, {
      source: `evidence/web/objects/${basename}.js`,
    });
    assert.equal(
      f.provenance.sha256,
      hash,
      `review required: changed factory${id}`,
    );
    factories.push(f);
  }
  assert.deepEqual(
    corpus.index.modules
      .filter((m) => m.ids.includes(524711))
      .map((m) => m.sha256)
      .sort(),
    factories
      .slice(0, 6)
      .map((f) => f.provenance.sha256)
      .sort(),
    "all physical reader variants must remain explicit",
  );
  const readers = factories.slice(0, 6).map((f) => {
    const provider = imported(f, 38279);
    const read = resolve(f, exportBinding(f, 349572, "K"));
    const options = resolve(f, exportBinding(f, 524711, "g"));
    const hook = resolve(f, exportBinding(f, 524711, "_"));
    const status = resolve(f, exportBinding(f, 349572, "W"));
    const retryAfter = resolve(f, exportBinding(f, 349572, "P"));
    const finiteProperty = resolve(f, status.body.callee);
    const errorClass = exactlyOne(
      findNodes(f.node, (n) => n.type === "ClassDeclaration"),
      "error class",
    );
    const optionsObject = exactlyOne(
      findNodes(
        options,
        (n) =>
          n.type === "ObjectExpression" &&
          n.properties.some((p) => propertyName(p.key) === "queryFn"),
      ),
      "query options",
    );
    const retry = resolve(f, objectProperty(optionsObject, "retry"));
    const delay = resolve(f, objectProperty(optionsObject, "retryDelay"));
    const poll = resolve(
      f,
      exactlyOne(
        findNodes(
          hook,
          (n) =>
            n.type === "ObjectProperty" &&
            propertyName(n.key) === "refetchInterval",
        ),
        "poll interval",
      ).value,
    );
    const fetchCall = exactlyOne(
      findNodes(
        read,
        (n) => n.type === "CallExpression" && n.callee?.name === "fetch",
      ),
      "native fetch",
    );
    assert.equal(fetchCall.arguments.length, 2);
    const url = exactlyOne(
      findNodes(
        read,
        (n) => n.type === "NewExpression" && n.callee.name === "URL",
      ),
      "URL construction",
    );
    const originRef = url.arguments[0].expressions[0];
    assert.equal(originRef.object.object.name, provider.id.name);
    assert.equal(propertyName(originRef.object.property), "t");
    assert.equal(propertyName(originRef.property), "BALANCE_SUMMARY");
    const multiChain = exactlyOne(
      findNodes(
        read,
        (n) => callMember(n, "set") && n.arguments[0]?.value === "multi_chain",
      ),
      "multi-chain query",
    );
    assert.equal(multiChain.arguments[1]?.value, "true");
    assert.equal(findNodes(read, (n) => callMember(n, "json")).length, 1);
    assert.equal(
      findNodes(
        read,
        (n) => callMember(n, "get") && n.arguments[0]?.value === "retry-after",
      ).length,
      1,
    );
    return {
      factory: f.provenance,
      sourceNodes: [
        cite(f, provider, "literal source/cache-key provider import"),
        cite(f, read, "complete HTTP reader and error/Retry-After path"),
        cite(f, errorClass, "actual HTTP error constructor"),
        cite(
          f,
          finiteProperty,
          "finite property guard shared by status/retry-after",
        ),
        cite(f, status, "finite status extraction"),
        cite(f, retryAfter, "finite retry-after extraction"),
        cite(f, options, "query builder and closed-over request input"),
        cite(f, retry, "retry admission"),
        cite(f, delay, "retry delay"),
        cite(f, poll, "poll interval"),
        cite(f, hook, "complete query hook/memo and last-spread overrides"),
      ],
    };
  });
  const provider = factories[6];
  const urls = resolve(provider, exportBinding(provider, 38279, "C"));
  const endpoints = resolve(provider, exportBinding(provider, 38279, "t"));
  const keys = resolve(provider, exportBinding(provider, 38279, "Q"));
  const profile = objectProperty(urls, "PROFILE");
  assert.equal(profile.value, "https://profile-api.pump.fun");
  const endpoint = objectProperty(endpoints, "BALANCE_SUMMARY");
  assert.equal(endpoint.quasis[1].value.cooked, "/balance/summary");
  const queryKey = objectProperty(keys, "BALANCE_SUMMARY");
  assert.equal(queryKey.body.elements[0].value, "balanceSummary");
  const caller = factories[7],
    callerImport = imported(caller, 524711);
  const invocation = exactlyOne(
    findNodes(caller.node, (n) => {
      const callee = unsequence(n.callee);
      return (
        n.type === "CallExpression" &&
        callee?.object?.name === callerImport.id.name &&
        propertyName(callee.property) === "_"
      );
    }),
    "actual UI query invocation",
  );
  const argument = invocation.arguments[0];
  const queryInput = exactlyOne(
    findNodes(
      caller.node,
      (n) =>
        n.type === "AssignmentExpression" &&
        n.left.name === argument.name &&
        n.right.type === "ObjectExpression" &&
        n.right.properties.some((p) => propertyName(p.key) === "userAddress"),
    ),
    "actual UI query input",
  );
  const success = exactlyOne(
    findNodes(
      caller.node,
      (n) =>
        n.type === "VariableDeclarator" &&
        n.init?.type === "ConditionalExpression" &&
        n.init.test.type === "OptionalMemberExpression" &&
        propertyName(n.init.test.property) === "success" &&
        n.init.consequent.type === "MemberExpression" &&
        propertyName(n.init.consequent.property) === "data",
    ),
    "UI success/data handoff",
  );
  return {
    schemaVersion: 1,
    authority:
      "Authenticated shipped JavaScript parsed as inert AST; no captured execution or live request",
    anchors: corpus.anchors,
    readers,
    provider: {
      factory: provider.provenance,
      sourceNodes: [
        cite(provider, profile, "profile service origin"),
        cite(provider, endpoint, "balance summary endpoint"),
        cite(provider, queryKey, "query/cache key; not a credential"),
      ],
    },
    caller: {
      factory: caller.provenance,
      sourceNodes: [
        cite(caller, callerImport, "actual UI reader import"),
        cite(caller, queryInput, "UI query input fields"),
        cite(caller, invocation, "actual UI query call"),
        cite(caller, success, "raw successful response data handoff"),
      ],
    },
    behavior: {
      capturedBaseUrl: "https://profile-api.pump.fun/balance/summary",
      method:
        "Fetch default GET unless explicitly overridden by passed fetchOptions",
      subjectEncoding:
        "raw interpolation before URL parsing; no path-segment encoding or validation",
      multiChain:
        "truthy flag adds multi_chain=true; query builder always requests it",
      fetchOptions:
        "forwarded unchanged; query context AbortSignal is not read",
      success:
        "raw response.json(); no schema or success:true enforcement in reader",
      unauthorized:
        "status401 throws BalanceSummaryHttpError Unauthorized without reading body/header",
      otherErrors:
        "status plus Failed to fetch wallet summary; Retry-After header only on429",
      retry: "non401 and failureCount<2",
      retryDelay:
        "non429 exponential 1s capped30s; finite429 retryAfter capped60s, otherwise5s*(count+1)",
      polling:
        "60000 only for query state success AND data.success===true; otherwise15000",
      cache:
        "balanceSummary/subject; infinite staleTime, mount/focus/reconnect refetch; overrides spread LAST",
      uiHandoff:
        "actual caller passes subject only; raw response success truthiness controls data handoff",
    },
    limits: [
      "No active provider/variant, authenticated availability, server ownership or response/accounting schema is established.",
      "Original React/query scheduler is an explicit injected port; finite tests do not qualify its lifecycle/retry scheduling.",
      "HTTP provider is explicit and synthetic in tests. No default destination or request occurs on import.",
      "No RPC, financial/PnL calculation, live pricing/repricing, original UI/animation or native backend compatibility is implemented.",
    ],
  };
}

export async function verify(root = APP_ROOT) {
  const result = await recover(root);
  const actual = await readFile(path.join(root, OUTPUT));
  assert.ok(
    actual.equals(Buffer.from(JSON.stringify(result, null, 2) + "\n")),
    "balance-summary contract bytes differ from authenticated deterministic output",
  );
  return result;
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  if (
    process.argv.length !== 3 ||
    !["--write", "--check"].includes(process.argv[2])
  )
    throw new Error(
      "Usage: node app/scripts/original-balance-summary.mjs --check|--write",
    );
  if (process.argv[2] === "--write") {
    const result = await recover();
    await mkdir(path.dirname(path.join(APP_ROOT, OUTPUT)), { recursive: true });
    await writeFile(
      path.join(APP_ROOT, OUTPUT),
      JSON.stringify(result, null, 2) + "\n",
    );
  } else await verify();
  console.log(
    "PASS balance-summary: six physical readers, origin/query key and actual UI handoff",
  );
}
