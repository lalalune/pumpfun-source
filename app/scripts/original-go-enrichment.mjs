import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import prettier from "prettier";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  member,
  propertyName,
  sha256,
} from "./original-contracts/source.mjs";
import { normalizeUserSearch } from "./verify-user-search.mjs";
import { verifySession } from "./verify-search-session.mjs";

export const APP_ROOT = fileURLToPath(new URL("..", import.meta.url));
export const DIRECTORY = "reconstruction/go-enrichment";
// PINNED_COHORT
const PINS = {
  260095: [
    [
      "41216a65a59eaf37.js",
      "2649e2a42601c79c33fe729da749f22200532b620f25d7faec19721b59fa1a54",
    ],
  ],
  242663: [
    [
      "9e0ee9dcf9856205.js",
      "40d144ca6b6818d78daff874343e2df289def523fec0114c20de4f5c046bf86d",
    ],
    [
      "95be9180237024f4.js",
      "e5c6cda9020c5c610162d2de10f654c06af240ad7733cd0c6d213fb49b22ce22",
    ],
  ],
  609252: [
    [
      "11ee2a97b2772408.js",
      "912f6120ed5c5adada18e702e39e564e7331850bd43e70dba8e2a463322b1ac2",
    ],
    [
      "4a89a99471a66194.js",
      "fd62996aae4f9d46364558e32c54cf36a60ea45f9f179828d2401919d8a1e10f",
    ],
    [
      "dd1b7e2a0ecbaed0.js",
      "c438d25a94216ad8a89a14f0ce71124596a4a8b580ac1710ee533ea9a9c3f98a",
    ],
    [
      "8748d5c4832dda34.js",
      "8771ebc2df8dd955abc0b4ef42903f675d51316eabc1b6eb986aaf3d4d6fd5dd",
    ],
    [
      "95be9180237024f4.js",
      "7ef61705e1c15ac2dcf2d6153c2d6843ceb6f53c306560ee5165227139f9d873",
    ],
    [
      "767cc801e3f88f8b.js",
      "cb75f05f0e1d6b8bf78ad8cf9cd47f6286c1d74f17a31c65605c7bc928752801",
    ],
    [
      "97dc53c5c25c1fdc.js",
      "928189cf25fa929570eb47da831ac66ae42a85d448691959a830b3b633b497bc",
    ],
    [
      "7a7f27bff952614d.js",
      "c331cdee07265e37444c19db6f0e4ff9adc834ca3ef104127606f1ac2e1b894a",
    ],
    [
      "a6c540af7c959989.js",
      "3b7c5cf337dfbbf876d64310606abc6ca27b623d36e123fa582e1dc9514e6e0f",
    ],
  ],
  462024: [
    [
      "9e0ee9dcf9856205.js",
      "14f93c41eab3af5bfb33f7914ec9054dbacb3a9de910172b8dd3f63233fa4294",
    ],
    [
      "95be9180237024f4.js",
      "1a344374e15f73b1a2b26f0c264e7f40b8ec8ff8ebc5c93e9747443db04dbc30",
    ],
  ],
  456647: [
    [
      "9e0ee9dcf9856205.js",
      "d47a16d5e50647850134a857f9ec582a0cdd160e45a804bc59f5b220b7592b3f",
    ],
  ],
};
const IMPORTS = {
  445242: ["c"],
  574472: ["F"],
  576766: ["f"],
  456647: ["m"],
  462024: ["i", "u", "Q"],
  242663: ["f"],
  609252: ["f"],
  369091: ["useIpfsPrefix"],
  493025: ["f"],
  689943: ["V"],
};
const GLOBALS = Object.fromEntries(
  [
    "Date",
    "Number",
    "Symbol",
    "Array",
    "Map",
    "Set",
    "Boolean",
    "Error",
    "String",
  ].map((n) => [n, "global:" + n]),
);
function declarations(f) {
  return f.node.body.body.flatMap((n) =>
    n.type === "FunctionDeclaration"
      ? [n]
      : n.type === "VariableDeclaration"
        ? n.declarations
        : [],
  );
}
function local(f, name) {
  return exactlyOne(
    declarations(f).filter((n) => n.id?.name === name),
    "module binding " + name,
  );
}
function exportsOf(f, id) {
  const c = exactlyOne(
    findNodes(
      f.node,
      (n) =>
        n.type === "CallExpression" &&
        member(n.callee, f.runtime, "s") &&
        (n.arguments[1]?.value === id ||
          (!n.arguments[1] && f.ids.length === 1)),
    ),
    "actual export " + id,
  );
  const a = c.arguments[0].elements,
    out = new Map();
  assert.equal(a.length % 3, 0);
  for (let i = 0; i < a.length; i += 3) {
    assert.equal(a[i].type, "StringLiteral");
    assert.equal(a[i + 1].value, 0);
    let v = a[i + 2];
    if (v.type === "Identifier") {
      const d = local(f, v.name);
      v = d.type === "VariableDeclarator" ? d.init : d;
    }
    out.set(a[i].value, v);
  }
  return out;
}
function moduleImports(f) {
  return new Map(
    declarations(f)
      .filter(
        (d) =>
          d.type === "VariableDeclarator" &&
          d.init?.type === "CallExpression" &&
          member(d.init.callee, f.runtime, "i"),
      )
      .map((d) => [d.id.name, d.init.arguments[0].value]),
  );
}
function bindings(n) {
  if (!n) return [];
  if (n.type === "Identifier") return [n.name];
  if (n.type === "RestElement") return bindings(n.argument);
  if (n.type === "AssignmentPattern") return bindings(n.left);
  if (n.type === "ObjectPattern")
    return n.properties.flatMap((p) =>
      bindings(p.type === "RestElement" ? p.argument : p.value),
    );
  if (n.type === "ArrayPattern") return n.elements.flatMap(bindings);
  throw Error("Unsupported binding " + n.type);
}
function shadowed(name, parents) {
  return parents.some(
    (n) =>
      (/Function/.test(n.type) &&
        (n.params.flatMap(bindings).includes(name) || n.id?.name === name)) ||
      (n.type === "BlockStatement" &&
        n.body
          .filter((x) => x.type === "VariableDeclaration")
          .flatMap((x) => x.declarations)
          .flatMap((x) => bindings(x.id))
          .includes(name)) ||
      (n.type === "ForOfStatement" &&
        n.left.type === "VariableDeclaration" &&
        n.left.declarations.flatMap((x) => bindings(x.id)).includes(name)) ||
      (n.type === "CatchClause" && bindings(n.param).includes(name)),
  );
}
function context(f, fn, roles) {
  const im = moduleImports(f),
    qualified = {};
  for (const n of findNodes(fn, (n, parents) => {
    if (n.type !== "MemberExpression" || n.computed || !im.has(n.object?.name))
      return false;
    const prop = propertyName(n.property),
      id = im.get(n.object.name);
    if (!IMPORTS[id]?.includes(prop)) return false;
    assert.equal(
      shadowed(n.object.name, parents),
      false,
      "ambiguous namespace " + n.object.name + "." + prop,
    );
    return true;
  }))
    qualified[n.object.name + "." + propertyName(n.property)] =
      "operation:" + im.get(n.object.name) + "." + propertyName(n.property);
  return { roles: { ...GLOBALS, ...roles }, qualified };
}
// A lossless compatibility aid for the existing comparator's object-pattern
// binder: every original RestElement field/type remains, including .argument.
// The added .value duplicates that binding and is explicitly marked. This
// representation is never executed and never replaces a rest with a property.
function restBindings(n) {
  if (Array.isArray(n)) return n.map(restBindings);
  if (!n || typeof n !== "object") return n;
  const v = Object.fromEntries(
    Object.entries(n).map(([k, v]) => [k, restBindings(v)]),
  );
  if (v.type === "RestElement") {
    v.value = v.argument;
    v.restBindingAid = true;
  }
  return v;
}
function normalized(f, fn, roles) {
  const c = context(f, fn, roles);
  return {
    ...c,
    value: normalizeUserSearch(restBindings(fn), c.roles, c.qualified),
  };
}
function tokenRoles(f) {
  const roles = {};
  for (const n of f.node.body.body.filter(
    (n) => n.type === "FunctionDeclaration",
  )) {
    const ret = n.body.body[0]?.argument;
    if (ret?.type === "ArrayExpression")
      roles[n.id.name] = "operation:mint-pair";
    else if (ret?.type === "MemberExpression")
      roles[n.id.name] = "operation:mint-key";
    else if (ret?.type === "UnaryExpression")
      roles[n.id.name] = "operation:truthy";
    else throw Error("New token helper");
  }
  assert.deepEqual(Object.values(roles).sort(), [
    "operation:mint-key",
    "operation:mint-pair",
    "operation:truthy",
  ]);
  return roles;
}
const MAPPER_ROLES = {
  r: "constant:SOLmint",
  i: "constant:USDCmint",
  a: "operation:markdown",
  m: "operation:reward-display",
  c: "operation:reward-part",
  f: "operation:atomic-display",
  u: "operation:status",
  l: "operation:expiry",
  w: "operation:creator",
  p: "operation:token",
  o: "operation:winner-count",
  d: "operation:refund-status",
};
const SPECS = [
  [260095, ["E", "o"], () => ({ o: "operation:token-stubs" })],
  [242663, ["f"], tokenRoles],
  [609252, ["f"], () => ({})],
  [462024, ["u", "Q", "i"], () => ({ o: "operation:mutations" })],
  [456647, ["m"], () => MAPPER_ROLES],
];
function witness(f, n, label) {
  return { ...f.witness(n, label), text: f.text(n) };
}
function namespaceCode(f, ports) {
  return [...moduleImports(f)]
    .filter(([, id]) => ports[id])
    .map(([alias, id]) => "const " + alias + "=" + ports[id] + ";")
    .join("\n");
}
export async function recover(root = APP_ROOT) {
  const corpus = await openCorpus(root),
    groups = [],
    selected = new Map(),
    fragments = [];
  for (const [id, names, getRoles] of SPECS) {
    const cohort = corpus.index.modules.filter((m) => m.ids.includes(id));
    assert.deepEqual(
      cohort
        .flatMap((m) =>
          m.origins.map((o) => [o.source.split("/").at(-1), m.sha256]),
        )
        .sort(),
      PINS[id].slice().sort(),
      "physical cohort changed " + id,
    );
    const proofs = [];
    for (const [file, hash] of PINS[id]) {
      const f = await corpus.factory(id, {
        source: "evidence/web/objects/" + file,
      });
      assert.equal(f.provenance.sha256, hash);
      if (!selected.has(id)) selected.set(id, f);
      const exports = exportsOf(f, id),
        operations = names.map((name) => {
          const fn = exports.get(name),
            n = normalized(f, fn, getRoles(f));
          return {
            name,
            normalizedSha256: sha256(JSON.stringify(n.value)),
            source: witness(f, fn, id + "." + name),
            roles: n.roles,
            qualified: n.qualified,
          };
        });
      proofs.push({ factory: f.provenance, operations });
    }
    for (const name of names)
      assert.equal(
        new Set(
          proofs.map(
            (p) => p.operations.find((n) => n.name === name).normalizedSha256,
          ),
        ).size,
        1,
        "variants differ " + id + "." + name,
      );
    groups.push({ id, proofs });
  }
  const frame = selected.get(260095),
    token = selected.get(242663),
    coin = selected.get(609252),
    policy = selected.get(462024),
    mapper = selected.get(456647);
  const fx = (id) => exportsOf(selected.get(id), id);
  const moduleLocal = (f, name) => {
    const n = local(f, name);
    fragments.push(witness(f, n, "used local " + name));
    return n.type === "VariableDeclarator"
      ? "let " + f.text(n) + ";"
      : f.text(n);
  };
  const policyObject = local(policy, "i"),
    policyPredicate = fx(462024).get("Q");
  fragments.push(
    witness(policy, policyObject, "used token descriptors"),
    witness(policy, policyPredicate, "used mutation predicate"),
  );
  const policyCode = [
    "function createPolicy(nowMs){",
    "const Date={now:nowMs,parse:globalThis.Date.parse};",
    "let " + policy.text(policyObject) + ";",
    policy.text(policyPredicate),
    "return {i:i,Q:o,u:" + policy.text(fx(462024).get("u")) + "};",
    "}",
  ].join("\n");
  const mapperCode = [
    "function createDisplayMapper(policy){",
    namespaceCode(mapper, { 462024: "policy" }),
    ...["r", "i", "a", "m", "c", "f", "u", "l", "w", "p", "o", "d"].map((n) =>
      moduleLocal(mapper, n),
    ),
    "return " + mapper.text(fx(456647).get("m")) + ";",
    "}",
  ].join("\n");
  // Prove every selected helper is closed over the same explicit operations;
  // no unused32850 conversion helpers or other exports are pulled into scope.
  for (const name of Object.keys(MAPPER_ROLES)) {
    const d = local(mapper, name),
      n = d.type === "VariableDeclarator" ? d.init : d;
    normalized(mapper, n, MAPPER_ROLES);
  }
  const coinCode = [
    "function createCoinResultHook(ports){",
    namespaceCode(coin, {
      445242: "{c:ports.memoCache}",
      689943: "{V:ports.useCoinQuery}",
      369091: "{useIpfsPrefix:ports.useIpfsPrefix}",
      493025: "{f:normalizeSearchCoins}",
    }),
    "return " + coin.text(fx(609252).get("f")) + ";",
    "}",
  ].join("\n");
  const tokenCode = [
    "function createTokenHook(ports,useCoinResult){",
    namespaceCode(token, {
      445242: "{c:ports.memoCache}",
      609252: "{f:useCoinResult}",
    }),
    ...token.node.body.body
      .filter((n) => n.type === "FunctionDeclaration")
      .map((n) => {
        fragments.push(witness(token, n, "used projection helper"));
        return token.text(n);
      }),
    "return " + token.text(fx(242663).get("f")) + ";",
    "}",
  ].join("\n");
  const frameCode = [
    "function createEnrichmentHooks(ports,useTokens,mapBounty,policy){",
    namespaceCode(frame, {
      445242: "{c:ports.memoCache}",
      574472: "{F:ports.useViewerSnapshot}",
      576766: "{f:ports.useBatchProfiles}",
      456647: "{m:mapBounty}",
      462024: "policy",
      242663: "{f:useTokens}",
    }),
    moduleLocal(frame, "o"),
    "return {useEnrichedBounties:" +
      frame.text(fx(260095).get("E")) +
      ",useBountyTokens:" +
      frame.text(fx(260095).get("o")) +
      "};",
    "}",
  ].join("\n");
  const text = await prettier.format(
    [
      'import {normalizeSearchCoins} from "../search-session/session.mjs";',
      "// Complete selected GO enrichment operations, with explicit query/viewer ports.",
      policyCode,
      mapperCode,
      coinCode,
      tokenCode,
      frameCode,
      "export function createBountyEnrichment(ports){",
      'for(const name of ["memoCache","useViewerSnapshot","useBatchProfiles","useCoinQuery","useIpfsPrefix","nowMs"]) if(typeof ports?.[name]!=="function") throw new TypeError("Explicit enrichment capability required: "+name);',
      "const policy=createPolicy(ports.nowMs),mapBounty=createDisplayMapper(policy),useCoinResult=createCoinResultHook(ports),useTokens=createTokenHook(ports,useCoinResult);",
      "return {...createEnrichmentHooks(ports,useTokens,mapBounty,policy),mapBounty};",
      "}",
    ].join("\n"),
    { parser: "babel", singleQuote: false },
  );
  const consumer = await corpus.factory(851373, {
    source: "evidence/web/objects/1a7569c5c8d92a3d.js",
  });
  assert.equal(
    consumer.provenance.sha256,
    "bbcb560d600f357da96ef54da57bf0c90a856789b645c0022bf18238097e2815",
  );
  const consumerImport = exactlyOne(
    findNodes(
      consumer.node,
      (n) =>
        n.type === "VariableDeclarator" &&
        n.init?.arguments?.[0]?.value === 260095,
    ),
    "actual GO enrichment import",
  );
  const consumerCall = exactlyOne(
    findNodes(
      consumer.node,
      (n) =>
        n.type === "CallExpression" &&
        n.callee.type === "SequenceExpression" &&
        member(n.callee.expressions.at(-1), consumerImport.id.name, "E"),
    ),
    "actual GO enrichment call",
  );
  const query = await corpus.factory(689943, {
      source: "evidence/web/objects/020facfab961bf67.js",
    }),
    queryFn = exportsOf(query, 689943).get("V");
  assert.equal(
    query.provenance.sha256,
    "2f14d3455aeb9f4d16ae197ae4f9ca0ca62d74422f0c816b5776336c96644f6e",
  );
  const memo = await corpus.factory(445242, {
      source: "evidence/web/objects/01ad4f413e529b60.js",
    }),
    memoTarget = await corpus.factory(532815, {
      source: memo.provenance.source,
    });
  assert.equal(
    memo.provenance.sha256,
    "2d7f3e592645b5e2d997e444ee9b10be6dc8c357680552dccddafb63e4887576",
  );
  assert.equal(
    memoTarget.provenance.sha256,
    "30e0e70b96ec8bc14a84e8ebab1dc7a376f543667300fa43b118f00c3199ae9a",
  );
  const prior = await verifySession(root);
  const dependencies = [];
  for (const p of [
    "reconstruction/search-session/session.mjs",
    "reconstruction/batch-profile-query/client.mjs",
    "reconstruction/batch-profile-query/contract.json",
  ])
    dependencies.push({
      path: p,
      sha256: sha256(await readFile(path.join(root, p))),
    });
  const contract = {
    schemaVersion: 1,
    base: "094a06f18df738d41e77070c1a009e135671ac1a",
    scope:
      "Complete selected260095 E/o enrichment frame,242663 projection,609252 result wrapper,456647.m used display closure and462024 i/u/Q; external query/provider results only",
    groups,
    fragments,
    module: {
      path: DIRECTORY + "/client.mjs",
      sha256: sha256(Buffer.from(text)),
    },
    dependencies,
    priorNormalizer: prior.adapterSha256,
    caller: {
      factory: consumer.provenance,
      witnesses: [
        witness(consumer, consumerImport, "actual GO import"),
        witness(consumer, consumerCall, "actual enrichment invocation"),
      ],
      credit:
        "OPEN1854 recovers surrounding main-app screener/read/feed handoff; not imported/copied or re-credited here",
    },
    ports: {
      memoCache: {
        signature: "memoCache(size)",
        bridge: memo.provenance,
        target: memoTarget.provenance,
        text: memoTarget.text(),
        qualification:
          "Explicit React compiler memo-cache capability; original runtime initialization not executed",
      },
      useViewerSnapshot: {
        signature: "() => {address}",
        qualification:
          "Read-only external viewer-address snapshot; no wallet/session/auth acquisition or authorization guarantee",
      },
      useBatchProfiles: {
        signature: "({userAddresses}) => {data,isPending,...}",
        credit:
          "Existing576766 batch-profile query/read/error boundary unchanged; host owns actual hook/query scheduling",
      },
      useCoinQuery: {
        signature:
          "(mints,options) => {data,isLoading,error,refetch,isError,isLoadingError}",
        factory: query.provenance,
        operation: witness(query, queryFn, "actual689943.V query boundary"),
        qualification:
          "Opaque actual query-result port; request/cache/TanStack/identity/service semantics not implemented",
      },
      useIpfsPrefix: {
        signature: "() => {ipfsPrefix}",
        qualification:
          "Explicit read-only provider result, no provider acquisition",
      },
      nowMs: {
        signature: "() => epoch milliseconds",
        qualification:
          "Used only by source submission-admission display predicate; no invented timer/invalidation",
      },
    },
    credit: [
      "Existing493025 normalization from accepted search-session unchanged",
      "Existing576766 query+strict batch/profile clients unchanged",
      "OPEN1854 surrounding screener omitted;1812 prior609252 hydration attribution credited, no query/reader recovery claim",
    ],
    limits: [
      "No live request, credentials/cookies/storage/session/wallet acquisition or signing",
      "Display projections preserve source Number conversions and quirks; no backend ranking/reward/accounting/claim authorization",
      "Query/provider result ports are required; no hidden default destination or transport, TanStack or original provider winner",
      "Only selected used exports/helpers; no whole GO/detail/creation/moderation/refund/payout feature implementation",
      "No captured execution, product mount/native/API/security/visual equivalence or feature-completion count claim",
    ],
  };
  return { text, contract };
}
export async function verify(root = APP_ROOT) {
  const result = await recover(root);
  assert.equal(
    await readFile(path.join(root, DIRECTORY, "client.mjs"), "utf8"),
    result.text,
    "enrichment module differs",
  );
  assert.equal(
    await readFile(path.join(root, DIRECTORY, "contract.json"), "utf8"),
    JSON.stringify(result.contract, null, 2) + "\n",
    "enrichment contract bytes differ",
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
    const r = await recover();
    await mkdir(path.join(APP_ROOT, DIRECTORY), { recursive: true });
    await writeFile(path.join(APP_ROOT, DIRECTORY, "client.mjs"), r.text);
    await writeFile(
      path.join(APP_ROOT, DIRECTORY, "contract.json"),
      JSON.stringify(r.contract, null, 2) + "\n",
    );
  } else await verify();
  console.log(
    "PASS complete selected GO enrichment closure/all15physicalvariant occurrences; query/provider ports explicit",
  );
}
