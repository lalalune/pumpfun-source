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
const rootDefault = fileURLToPath(new URL("../", import.meta.url));
const packet = "reconstruction/lite-trade-listeners";
const enumSources = [
  "evidence/web/objects/e37dbbcf0dcb6051.js",
  "evidence/web/objects/a0ec47219f76f808.js",
];
const enumHashes = [
  "d07a60b6380a193ffe870306c705b0c8c289663dcb883d57e7605a296425dc27",
  "d2419cfba7861ae41660985a0fa4b586b8e48c353aa46ccb1c55d1011a4cd04d",
];
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
    for (let i = 0; i < a.length; ) {
      assert.equal(a[i]?.type, "StringLiteral");
      if (a[i + 1]?.value === 0) {
        out.set(a[i].value, a[i + 2]);
        i += 3;
      } else {
        assert.equal(a[i + 1]?.type, "ArrowFunctionExpression");
        out.set(a[i].value, a[i + 1]);
        i += 2;
      }
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
    declarations(f).filter((d) => d.id?.name === name),
    `${f.id} ${name}`,
  );
}
function exported(f, key, id = f.id) {
  const n = exportsOf(f, id).get(key);
  assert.ok(n, `${id}.${key}`);
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
  const enums = [],
    enumCode = [];
  assert.deepEqual(
    new Set(
      corpus.index.modules
        .filter((m) => m.ids.includes(985526))
        .map((m) => m.sha256),
    ),
    new Set(enumHashes),
  );
  for (let v = 0; v < enumSources.length; v++) {
    const f = await factory(985526, enumSources[v]);
    assert.equal(f.provenance.sha256, enumHashes[v]);
    assert.deepEqual([...exportsOf(f).keys()], ["m", "N"]);
    const getter = exported(f, "N");
    assert.equal(getter.params.length, 0);
    assert.equal(getter.body.type, "Identifier");
    const init = declaration(f, getter.body.name).init;
    const unified = exactlyOne(
      findNodes(
        init,
        (n) =>
          n.type === "AssignmentExpression" &&
          n.left.type === "MemberExpression" &&
          propertyName(n.left.property) === "Unified",
      ),
      "used Unified assignment",
    );
    assert.equal(literal(unified.right), "UNIFIED");
    witness(f, unified, "actual exported namespace Unified literal");
    enumCode.push(
      `function protocol${v}(){${privates(f)}return{get N(){return (${witness(f, getter, "actual N namespace getter")})()},get m(){return (${witness(f, exported(f, "m"), "actual m namespace getter")})()}};}`,
    );
    enums.push({
      source: enumSources[v],
      sha256: enumHashes[v],
      unified: "UNIFIED",
    });
  }
  const subjects = await factory(237237),
    subject = exported(subjects, "V");
  assert.equal(literal(subject), "unifiedTradeEvent.lite");
  const subjectCode = witness(subjects, subject, "used lite subject prefix");
  const f = await factory(915631);
  assert.equal(
    f.provenance.sha256,
    "32d1e326a1838d7745974be05b28302b1c54c4fcbe6e519c964a318ad7f9a4f9",
  );
  assert.equal(
    corpus.index.modules.filter(
      (m) => m.ids.includes(915631) || m.ids.includes(949629),
    ).length,
    1,
  );
  assert.deepEqual([...exportsOf(f, 949629).keys()], ["f"]);
  assert.deepEqual([...exportsOf(f, 915631).keys()], ["f"]);
  const protocol = {
    254667: "{y:logger}",
    352386: "React",
    985526: "protocol",
    237237: `{V:${subjectCode}}`,
    544514: "{f:useReady}",
    390065: "{N:useConnection}",
    653805: "{x:liveCoinStore}",
  };
  const bindings = Object.entries(protocol)
    .map(([id, value]) => {
      const imp = imported(f, Number(id));
      witness(f, imp, `used runtime import${id}`);
      return `const ${imp.id.name}=${value};`;
    })
    .join("\n");
  const provider = await factory(390065);
  witness(
    provider,
    exported(provider, "N"),
    "external connection hook; subscription API/active-instance signature only",
  );
  const readiness = await factory(544514);
  witness(
    readiness,
    readiness.node,
    "external one-shot boot/idle readiness; not auth or session readiness",
  );
  const consumers = [];
  for (const [id, target] of [
    [457065, 915631],
    [228998, 949629],
  ]) {
    const parent = await factory(id),
      imp = imported(parent, target),
      alias = imp.id.name;
    witness(parent, imp, `actual${id} import${target}`);
    const calls = findNodes(
      parent.node,
      (n) =>
        n.type === "CallExpression" &&
        n.callee.type === "SequenceExpression" &&
        n.callee.expressions.at(-1)?.type === "MemberExpression" &&
        n.callee.expressions.at(-1).object.name === alias &&
        propertyName(n.callee.expressions.at(-1).property) === "f",
    );
    assert.equal(calls.length, 1, `${id} actual selected call`);
    witness(parent, calls[0], `actual${id} call${target}.f`);
    const enclosing = exactlyOne(
      parent.node.body.body.filter(
        (n) => n.start <= calls[0].start && n.end >= calls[0].end,
      ),
      `${id} enclosing used caller`,
    );
    witness(
      parent,
      enclosing,
      `complete enclosing${id} caller; screen not implemented`,
    );
    consumers.push({
      id,
      target,
      source: parent.provenance,
      call: parent.witness(calls[0], `selected${target}.f call`),
    });
  }
  const code = await format(
    `// Source-bound editable translation; captured factories are parsed, never evaluated.
 export const protocolVariantHashes=${JSON.stringify(enumHashes)};
 ${enumCode.join("\n")}
 export function createLiteTradeHooks({protocolVariant,React,useConnection,useReady,liveCoinStore,logger,DatePort}){
  const protocol=protocolVariant===protocolVariantHashes[0]?protocol0():protocolVariant===protocolVariantHashes[1]?protocol1():null;
  if(!protocol)throw Error('explicit supported985526 variant hash required');
  const Date=DatePort;
  ${bindings}
  ${privates(f)}
  return {useSubscriptions:${witness(f, exportsOf(f, 949629).get("f"), "complete949629 subscription hook export")},useLiteTrades:${witness(f, exported(f, "f", 915631), "complete915631 event-to-local-state hook export")}};
 }`,
    { parser: "babel" },
  );
  const contract = {
    schemaVersion: 1,
    title:
      "Complete keyed lite-trade listener reconciliation and event-to-local-state boundary",
    anchors: corpus.anchors,
    sources,
    witnesses,
    protocolVariants: enums,
    subject: "unifiedTradeEvent.lite",
    consumers,
    sourceBoundary: {
      factory: 915631,
      sharedFactory: 949629,
      variants: 1,
      registry:
        "One Map per reconstructed module instance, shared by all hook calls from that instance. Keys trimmed in registry; original per-hook keys and sorted joined dependency retained.",
      coalescing:
        "Any listener requesting none wins; otherwise latest. Mode changes unsubscribe then resubscribe; last removal deletes registry entry even if unsubscribe throws.",
      lifecycle:
        "Stable forwarding callback reads latest callback ref after its effect; per-hook map reconciles mints when dependencies change; empty/disabled/not-ready/inactive and unmount cleanup retained.",
      readiness:
        "544514 is one-shot boot/idle readiness; it is neither auth nor proof of connection.",
      normalization:
        "Actual finite positive marketCap guard; truthy price/timestamp paths, Date constructor/now, exact buy type equality, truthy previous pending ATH and larger cap field; caught callback errors log. No extra validation or interpretation.",
    },
    externalPorts: [
      "React useEffect/useRef/useCallback/useMemo scheduling",
      "390065.N subscribe/unsubscribe/isInstanceActive provider; consistent shared provider assumed by source",
      "544514.f boot/idle readiness",
      "653805.x bound-store hook/getState/peekCoin/updateCoin, credited proposed1870; no runtime import",
      "Date constructor/Date.now and254667 logger",
    ],
    attribution: [
      {
        pr: 1812,
        scope:
          "Mayhem source consumers/join; subscription lifecycle remained external",
      },
      {
        pr: 1870,
        scope:
          "Qualified proposed queued store/frame-batch recovery; store stays injected, no copied implementation or absent-main import",
      },
    ],
    limits: [
      "No network/WS/NATS connection, provider service, original mount, auth/session/cookies, endpoint operation, history, financial/oracle/accounting qualification, native compatibility or feature milestones",
      "Provider operations in qualification are local injected calls, not service delivery. Callback errors/unsubscribe errors follow source handling, not a guarantee of transport cleanup.",
      "Both protocol namespace variants retained; no original active-loader winner inferred. Parent caller witnesses do not implement the screens or their state/query logic.",
      "Original captures, ledgers, previous packets and proposed1870 are unchanged",
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
    witnesses: actual.contract.witnesses.length,
    sourceEntries: actual.contract.sources.length,
    protocolVariants: 2,
    listenerFactoryVariants: 1,
    selectedConsumers: 2,
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
        "usage: original-lite-trade-listeners.mjs [--app-root PATH] --write|--check",
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
