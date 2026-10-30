import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { format } from "prettier";
import { parse } from "@babel/parser";

import {
  openCorpus,
  findNodes,
  exactlyOne,
  propertyName,
  sha256,
} from "./original-contracts/source.mjs";
const defaultRoot = fileURLToPath(new URL("../", import.meta.url)),
  packet = "reconstruction/home-feed-coordination";
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
  async function factory(id, source, role = "runtime source") {
    const rows = corpus.index.modules.filter((m) => m.ids.includes(id));
    if (!source && rows.length === 1 && rows[0].origins.length > 1) {
      let first;
      for (const origin of rows[0].origins) {
        const f = await corpus.factory(id, { source: origin.source });
        sources.push({ ...f.provenance, role });
        if (first)
          assert.equal(
            f.text(),
            first.text(),
            "same-hash repeated physical helper body",
          );
        else first = f;
      }
      return first;
    }
    const f = await corpus.factory(id, source ? { source } : {});
    sources.push({ ...f.provenance, role });
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
  function privates(f, names, label) {
    return names
      .map((name) => {
        const n = declaration(f, name);
        assert.ok(
          !(
            n.init?.type === "CallExpression" &&
            n.init.callee.object?.name === f.runtime &&
            propertyName(n.init.callee.property) === "i"
          ),
          "private selection cannot include runtime import",
        );
        return n.type === "FunctionDeclaration"
          ? witness(f, n, label)
          : `let ${witness(f, n, label)};`;
      })
      .join("\n");
  }
  const main = await factory(163807);
  const badgeCall = exactlyOne(
    findNodes(
      main.node,
      (n) =>
        n.type === "CallExpression" &&
        n.callee.type === "FunctionExpression" &&
        main.text(n.callee).includes("classic-tab-badge"),
    ),
    "complete inactive badge IIFE",
  );
  const aheadCall = exactlyOne(
    findNodes(
      main.node,
      (n) =>
        n.type === "CallExpression" &&
        n.callee.type === "ArrowFunctionExpression" &&
        main.text(n.callee).includes("followingChain") &&
        main.text(n.callee).includes(".prefetchInfiniteQuery"),
    ),
    "complete read-ahead IIFE",
  );
  const badge = witness(
      main,
      badgeCall.callee,
      "complete15slot inactive badge owner",
    ),
    ahead = witness(
      main,
      aheadCall.callee,
      "complete8slot read-ahead effect owner",
    );
  witness(main, badgeCall, "actual MAIN badge call");
  witness(main, aheadCall, "actual MAIN read-ahead call");
  const badgeResult = exactlyOne(
    findNodes(
      main.node,
      (n) => n.type === "VariableDeclarator" && n.init === badgeCall,
    ),
    "actual badge result",
  );
  const members = findNodes(
    main.node,
    (n) =>
      n.type === "MemberExpression" &&
      n.object.name === badgeResult.id.name &&
      ["reset", "newCount"].includes(propertyName(n.property)),
  );
  assert.equal(
    members.filter((n) => propertyName(n.property) === "reset").length,
    1,
  );
  assert.ok(
    members.filter((n) => propertyName(n.property) === "newCount").length >= 2,
  );
  for (const n of members)
    witness(
      main,
      n,
      "actual used tab " + propertyName(n.property) + " consumer",
    );
  const resetCall = exactlyOne(
    findNodes(
      main.node,
      (n) =>
        n.type === "CallExpression" &&
        n.callee === members.find((x) => propertyName(x.property) === "reset"),
    ),
    "tab reset invocation",
  );
  witness(main, resetCall, "actual tab activation reset call");
  for (const call of [badgeCall, aheadCall]) {
    assert.equal(call.arguments[0].type, "Identifier");
    const alias = call.arguments[0].name,
      options = findNodes(
        main.node,
        (n) =>
          n.type === "AssignmentExpression" &&
          n.left.name === alias &&
          n.right.type === "ObjectExpression",
      );
    assert.ok(options.length >= 1);
    for (const n of options)
      witness(
        main,
        n,
        "actual MAIN " +
          (call === badgeCall ? "badge" : "read-ahead") +
          " input object",
      );
  }
  const updater = witness(
    main,
    declaration(main, "eu"),
    "complete cache first-page trim updater",
  );
  const keyPrefix = declaration(main, "et").init,
    keyChain = declaration(main, "el").init,
    query = declaration(main, "ec").init;
  witness(
    main,
    keyPrefix,
    "existing1966 exact prefix-key signature, not emittedruntime",
  );
  witness(
    main,
    keyChain,
    "existing1966 exact chain-key signature, not emittedruntime",
  );
  witness(
    main,
    query,
    "existing1966 queryOptions API signature/body, requiredport only",
  );
  const binding = bindings(main, {
    445242: "{c:useMemoCache}",
    352386: "React",
    606933: "{useQueryClient}",
    106009: "{f:useFollowingEvents}",
    735821: "{G:followingKinds}",
    637172: "followingChain",
    99859: "{Z:prefetchHome}",
    364468: "{H:prefetchTop}",
  });
  const code = await format(
    `// Complete inactive badge and read-ahead owners; prior read/query cores are required ports.
export function createHomeFeedCoordination({React,useMemoCache,useQueryClient,useFollowingEvents,prefetchHome,prefetchTop,followingQueryOptions,followingPrefixKey,followingChainKey,followingChain,followingKinds}){
 for(const fn of[React?.useEffect,React?.useState,useMemoCache,useQueryClient,useFollowingEvents,prefetchHome,prefetchTop,followingQueryOptions,followingPrefixKey,followingChainKey,followingChain?.m,followingChain?.R])if(typeof fn!=='function')throw TypeError('all explicit coordination/runtime/read/key/event capabilities required');
 if(typeof followingKinds!=='string')throw TypeError('original following kinds namespace required');
 ${binding}
 const ec=followingQueryOptions,et=followingPrefixKey,el=followingChainKey;
 ${updater}
 const useFollowingBadge=${badge},useHomeReadAhead=${ahead};
 return{useFollowingBadge,useHomeReadAhead,trimExtraPages:eu};
}
`,
    { parser: "babel" },
  );
  parse(code, { sourceType: "module" });
  const fixture = await format(
    `// Qualification-only reuse of1966 private key signatures; no read/query core copied.
const et=${main.text(keyPrefix)};
const el=${main.text(keyChain)};
export const followingPrefixKey=et,followingChainKey=el;
`,
    { parser: "babel" },
  );
  parse(fixture, { sourceType: "module" });
  const contract = {
    schemaVersion: 1,
    title:
      "Complete MAIN inactive FOLLOWING badge and Home read-ahead coordination",
    anchors: corpus.anchors,
    sources,
    witnesses,
    generatedSha256: sha256(code),
    qualificationKeySha256: sha256(fixture),
    priorQualifiedPorts: [
      {
        pr: 1966,
        roles: ["ec queryOptions", "et/el keys", "637172m/R", "735821G"],
        limit:
          "Exact original signatures are required; no standalone read/querycore imported/copied or new helper credit.",
      },
      {
        pr: 1846,
        roles: ["99859Z Home prefetch"],
        limit: "Required original signature; no read execution in this packet.",
      },
      {
        pr: 1973,
        roles: ["364468H Top prefetch"],
        limit: "Required original signature; no ranking/querycore copy.",
      },
    ],
    ports: [
      "445242c compiler cache andReact useState/useEffect",
      "606933useQueryClient setQueriesData/invalidateQueries/prefetchInfiniteQuery",
      "106009f exact eventhook with enabled/viewer/queryKey/kinds/surface/onNewContent, no presence/event acquisition",
      "All prior read/key/chain/kinds ports listed above",
    ],
    semantics: {
      badge:
        "15memo slots; null-onlyviewer readiness and inactive gate; rawid dedup; every event trims all matchingprefix pages>1 then invalidates prefix refetchType:none; active/viewer reset; chainchange preservesids; reset stablecallback; active hides count",
      trim: "returns only pages/pageParams sliced1 when pageslength>1, elseundefined (cache updater skip)",
      readAhead:
        "8memo slots; effect invokes Home thenTop thenFollowing withoutawait/catch; onlynullviewer skipsFollowing, nototherprefetches; followingChain defaults onlyundefined→all; following pageSize20; original querydescriptor passedunchanged",
      caller:
        "actual MAIN calls/inputobjects/reset/newCount tab consumption sourcebound; UI/display and provider acquisition external",
    },
    limits: [
      "Source evidence authenticates one physical163807 factory, no new original loader/provider winner claim",
      "No source read/query core copied or silently imported from open PRs; required API ports remain explicit",
      "Finite synthetic query/cache/event/prefetch capabilities do not qualify original scheduling/cacheTTL/presence/service/provider/auth/telemetry/native/UI/feature behavior",
      "Read-ahead discards promises and adds no cleanup/catch; no invented cancellation or error recovery",
      "Semantic JSON comparison, not canonical JSON byte validation",
    ],
    mounted: false,
    productionOperationsQualified: 0,
  };
  return { code, fixture, contract };
}
export async function verify(appRoot = defaultRoot, supplied) {
  const d = await derive(appRoot),
    dir = path.join(appRoot, packet);
  assert.equal(
    supplied?.code ?? (await readFile(path.join(dir, "client.mjs"), "utf8")),
    d.code,
  );
  assert.equal(
    supplied?.fixture ??
      (await readFile(path.join(dir, "qualification/key-ports.mjs"), "utf8")),
    d.fixture,
  );
  assert.deepEqual(
    supplied?.contract ??
      JSON.parse(await readFile(path.join(dir, "contract.json"), "utf8")),
    d.contract,
  );
  return {
    witnesses: d.contract.witnesses.length,
    sourceEntries: d.contract.sources.length,
    badgeMemoSlots: 15,
    readAheadMemoSlots: 8,
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
        "usage: original-home-feed-coordination.mjs [--app-root PATH] --write|--check",
      );
  }
  if (!mode) throw Error("explicit mode required");
  if (mode === "--write") {
    const d = await derive(root);
    await mkdir(path.join(root, packet, "qualification"), { recursive: true });
    await writeFile(path.join(root, packet, "client.mjs"), d.code);
    await writeFile(
      path.join(root, packet, "qualification/key-ports.mjs"),
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
