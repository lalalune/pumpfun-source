import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { parse } from "@babel/parser";
import { format } from "prettier";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  propertyName,
  sha256,
} from "./original-contracts/source.mjs";
const defaultRoot = fileURLToPath(new URL("../", import.meta.url));
const packet = "reconstruction/coin-query-cache";
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
function exportsOf(f) {
  const out = new Map();
  for (const s of f.node.body.body) {
    const c = s.type === "ExpressionStatement" ? s.expression : null;
    if (
      c?.type !== "CallExpression" ||
      c.callee.type !== "MemberExpression" ||
      c.callee.object.name !== f.runtime ||
      propertyName(c.callee.property) !== "s"
    )
      continue;
    const a = c.arguments[0]?.elements;
    assert.ok(a);
    for (let i = 0; i < a.length; i += 3) {
      assert.equal(a[i + 1]?.value, 0);
      out.set(a[i].value, a[i + 2]);
    }
  }
  return out;
}
function exported(f, key) {
  const n = exportsOf(f).get(key);
  assert.ok(n, `${f.id}.${key}`);
  return n.type === "Identifier"
    ? (declaration(f, n.name).init ?? declaration(f, n.name))
    : n;
}
function imported(f, id) {
  return exactlyOne(
    declarations(f).filter(
      (n) =>
        n.init?.type === "CallExpression" &&
        n.init.callee.type === "MemberExpression" &&
        n.init.callee.object.name === f.runtime &&
        propertyName(n.init.callee.property) === "i" &&
        n.init.arguments[0]?.value === id,
    ),
    `${f.id} import ${id}`,
  );
}
export async function derive(appRoot = defaultRoot) {
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
      .map(([id, value]) => {
        const d = imported(f, Number(id));
        witness(f, d, `used import ${id}`);
        return `const ${d.id.name}=${value};`;
      })
      .join("\n");
  }
  const owner = await factory(689943),
    mint = await factory(605587),
    chain = await factory(646908),
    identity = await factory(997887);
  assert.deepEqual(
    corpus.index.modules
      .filter((m) => m.ids.includes(689943))
      .map((m) => m.sha256),
    ["2f14d3455aeb9f4d16ae197ae4f9ca0ca62d74422f0c816b5776336c96644f6e"],
  );
  const V = witness(
    owner,
    exported(owner, "V"),
    "complete52-slot owning coin cache/query/result hook",
  );
  const D = witness(
    owner,
    declaration(owner, "D"),
    "complete batch reader, options, response hook and identity handoff",
  );
  const constants = ["T", "S"]
    .map(
      (n) =>
        `const ${witness(owner, declaration(owner, n), `complete ${n} TTL declaration`)};`,
    )
    .join("\n");
  const keyObject = declaration(owner, "M").init;
  const keys = ["coin", "coinsByMints"].map((key) =>
    witness(
      owner,
      exactlyOne(
        keyObject.properties.filter((p) => propertyName(p.key) === key),
        `M.${key}`,
      ),
      `complete used cache key M.${key}`,
    ),
  );
  const mintCode = witness(
    mint,
    exported(mint, "c"),
    "complete lowercase0x-only canonicalizer",
  );
  const literals = ["i", "a", "d"]
    .map(
      (n) =>
        `const ${witness(chain, declaration(chain, n), `used chain literal ${n}`)};`,
    )
    .join("\n");
  const predicates = ["L", "B", "_"].map(
    (key) =>
      `${JSON.stringify(key)}:${witness(chain, exported(chain, key), `complete used chain predicate ${key}`)}`,
  );
  const rawIdentity = exported(identity, "l");
  witness(
    identity,
    rawIdentity,
    "accepted997887 identity reused, not recovered again",
  );
  assert.equal(rawIdentity.type, "ArrowFunctionExpression");
  assert.equal(rawIdentity.params.length, 1);
  assert.equal(rawIdentity.body.name, rawIdentity.params[0].name);
  const accepted = [];
  for (const file of [
    "reconstruction/search-session/session.mjs",
    "reconstruction/search-client/request.mjs",
    "reconstruction/search-client/contract.json",
  ]) {
    const b = await readFile(path.join(appRoot, file));
    accepted.push({ path: file, bytes: b.length, sha256: sha256(b) });
  }
  const session = parse(
    await readFile(path.join(appRoot, accepted[0].path), "utf8"),
    { sourceType: "module" },
  );
  const maintained = exactlyOne(
    findNodes(
      session,
      (n) => n.type === "VariableDeclarator" && n.id.name === "readSearchCoins",
    ),
    "accepted readSearchCoins",
  );
  assert.equal(maintained.init.type, "ArrowFunctionExpression");
  assert.equal(maintained.init.params.length, 1);
  assert.equal(maintained.init.body.name, maintained.init.params[0].name);
  const bridge = await factory(445242),
    runtime = await factory(532815);
  witness(
    bridge,
    bridge.node,
    "complete compiler re-export bridge; side-effect runtime dependency external",
  );
  witness(
    runtime,
    runtime.node,
    "complete compiler memo bridge, actual useMemoCache port",
  );
  const callers = [];
  for (const row of corpus.index.modules.filter((m) =>
    m.ids.includes(609252),
  )) {
    assert.equal(row.origins.length, 1);
    const f = await factory(609252, row.origins[0].source),
      imp = imported(f, 689943);
    witness(f, imp, "actual609252 import689943");
    const calls = findNodes(
      f.node,
      (n) =>
        n.type === "CallExpression" &&
        n.callee.type === "SequenceExpression" &&
        n.callee.expressions.at(-1)?.type === "MemberExpression" &&
        n.callee.expressions.at(-1).object.name === imp.id.name &&
        propertyName(n.callee.expressions.at(-1).property) === "V",
    );
    assert.equal(calls.length, 1);
    witness(f, calls[0], "actual609252 two-argument V call");
    for (const s of f.node.body.body.filter(
      (s) => s.start <= calls[0].start && s.end >= calls[0].end,
    ))
      witness(
        f,
        s,
        "complete enclosing609252 caller, implementation credited1882/external",
      );
    callers.push({
      source: f.provenance,
      call: f.witness(calls[0], "actual V call"),
    });
  }
  const code = await format(
    `// Generated from selected captured ASTs; no bundle/runtime evaluation.
 import {readSearchCoins} from '../search-session/session.mjs';
 export function createCoinQuery({useMemoCache,useQuery,useQueryClient,getContractClient,clock}){
 for(const [name,value] of Object.entries({useMemoCache,useQuery,useQueryClient,getContractClient}))if(typeof value!=='function')throw TypeError(name+' capability required');
 if(typeof clock?.now!=='function')throw TypeError('clock.now capability required');
 const Date=clock;
 ${bindings(owner, { 445242: "{c:useMemoCache}", 690877: "{useQuery}", 606933: "{useQueryClient}", 759257: "{j:getContractClient}", 997887: "{l:readSearchCoins}", 605587: `{c:${mintCode}}`, 646908: `(()=>{${literals}return{${predicates.join(",")}};})()` })}
 ${constants}
 const M={${keys.join(",")}};
 const ${D};
 const useCoins=${V};
 return {useCoins,readCoins:D};
 }
 `,
    { parser: "babel" },
  );
  const contract = {
    schemaVersion: 1,
    title: "Complete captured689943.V coin query/cache and D read boundary",
    anchors: corpus.anchors,
    sources,
    witnesses,
    callers,
    accepted,
    generatedSha256: sha256(code),
    semantics: {
      request: {
        operation: "POST /coins-v2/mints",
        factory:
          "required759257.j() exact-signature port; no default destination",
        body: "{mints}; includeNsfw is read but omitted",
        credentials: "include (source option only; no cookies acquired)",
        afterResponse:
          "third argument !ok throws Failed to fetch coins: statusText; no signal added",
        response:
          "unchanged accepted997887.l identity; no response schema parsing",
      },
      keys: "coin key preserves requested spelling; coinsByMints sorts a copy, preserves duplicates and safe/nsfw distinction",
      cache:
        "identity-memoized inspection; strict >60000 stale test, exact TON/NEAR/Starknet chain exceptions; lowercase0x fallback scans coin-prefix queries, highest timestamp/first tie",
      merge:
        "stale then fresh then fetched, canonical mint last-wins; original requested order/duplicates, missing omitted",
      options:
        "limit/offset/sort/order destructured but unused; rest spreads last and can override key/fn/enabled/staleTime/gcTime",
      result:
        "loading depends on missing flag, row count and raw query loading; raw error/flags/refetch, success=!loading&&!error",
    },
    ports: [
      "compiler useMemoCache",
      "TanStack-compatible useQuery/useQueryClient (cache/observer/scheduling external)",
      "759257.j factory returning named-operation client",
      "clock.now",
    ],
    limits: [
      "No service/default destination, current cookies, authentication, provider acquisition or original loader winner",
      "No mounted application, accounting/oracle/price/freshness guarantee, original timing or native/feature qualification",
      "609252 full wrapper belongs to1882; witnesses only; other689943 exports/history and unselected M keys excluded",
      "Exact selected helpers credited; unchanged accepted997887 identity reused via search-session; captures and ledgers unchanged",
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
    callerCalls: d.contract.callers.length,
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
        "usage: original-coin-query-cache.mjs [--app-root PATH] --write|--check",
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
