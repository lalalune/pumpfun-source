import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { parse } from "@babel/parser";
import prettier from "prettier";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  member,
  propertyName,
  sha256,
} from "./original-contracts/source.mjs";
import { verifyNavigation } from "./verify-search-navigation.mjs";
export const APP_ROOT = fileURLToPath(new URL("..", import.meta.url));
export const DIRECTORY = "reconstruction/recent-search-renderer";
const HASH = "9e5affafd605f47d6c9466659c4bc0a654fae027f4beff481337a1cdf1263828";
const retained = [
  "tu",
  "td",
  "tw",
  "t_",
  "tv",
  "tk",
  "tN",
  "tC",
  "K",
  "Q",
  "W",
];
const own = (f, name) =>
  exactlyOne(
    f.node.body.body
      .flatMap((n) =>
        n.type === "VariableDeclaration"
          ? n.declarations
          : n.type === "FunctionDeclaration"
            ? [n]
            : [],
      )
      .filter((n) => n.id?.name === name),
    "source declaration " + name,
  );
const value = (f, name) => {
  const n = own(f, name);
  return n.type === "VariableDeclarator" ? n.init : n;
};
const ignored = new Set([
  "start",
  "end",
  "loc",
  "extra",
  "leadingComments",
  "trailingComments",
  "innerComments",
]);
const ast = (v) =>
  Array.isArray(v)
    ? v.map(ast)
    : v && typeof v === "object"
      ? Object.fromEntries(
          Object.entries(v)
            .filter(([k]) => !ignored.has(k))
            .map(([k, v]) => [k, ast(v)]),
        )
      : v;
const cite = (f, n, label) => ({ ...f.witness(n, label), text: f.text(n) });
// Bounded source-scope audit reused, credited from #1925. No shared parser edits.
function freeNames(node) {
  const result = new Set();
  const bind = (p, s) => {
    if (!p) return;
    if (p.type === "Identifier") s.add(p.name);
    else if (p.type === "ObjectPattern")
      p.properties.forEach((v) =>
        bind(v.type === "RestElement" ? v.argument : v.value, s),
      );
    else if (p.type === "ArrayPattern") p.elements.forEach((v) => bind(v, s));
    else if (p.type === "AssignmentPattern") bind(p.left, s);
    else if (p.type === "RestElement") bind(p.argument, s);
    else assert.fail("unreviewed binding " + p.type);
  };
  const walk = (n, sc = [], parent, key) => {
    if (!n || typeof n !== "object") return;
    if (Array.isArray(n)) {
      n.forEach((v) => walk(v, sc, parent, key));
      return;
    }
    let next = sc;
    if (
      [
        "FunctionDeclaration",
        "FunctionExpression",
        "ArrowFunctionExpression",
      ].includes(n.type)
    ) {
      const s = new Set();
      bind(n.id, s);
      n.params.forEach((p) => bind(p, s));
      next = [...sc, s];
    }
    if (n.type === "BlockStatement") {
      const s = new Set();
      for (const b of n.body) {
        if (b.type === "VariableDeclaration")
          b.declarations.forEach((d) => bind(d.id, s));
        if (b.type === "FunctionDeclaration") bind(b.id, s);
      }
      next = [...sc, s];
    }
    if (n.type === "CatchClause") {
      const s = new Set();
      bind(n.param, s);
      next = [...sc, s];
    }
    if (
      ["ForOfStatement", "ForInStatement"].includes(n.type) &&
      n.left.type === "VariableDeclaration"
    ) {
      const s = new Set();
      n.left.declarations.forEach((d) => bind(d.id, s));
      next = [...sc, s];
    }
    if (n.type === "Identifier") {
      const field =
        (["MemberExpression", "OptionalMemberExpression"].includes(
          parent?.type,
        ) &&
          key === "property" &&
          !parent.computed) ||
        (["ObjectProperty", "ObjectMethod"].includes(parent?.type) &&
          key === "key" &&
          !parent.computed) ||
        (["LabeledStatement", "BreakStatement", "ContinueStatement"].includes(
          parent?.type,
        ) &&
          key === "label");
      if (!field && !next.some((s) => s.has(n.name))) result.add(n.name);
      return;
    }
    for (const [k, v] of Object.entries(n))
      if (!ignored.has(k)) walk(v, next, n, k);
  };
  walk(node);
  return [...result].sort();
}
const namespaces = {
  p: { f: "useTranslation" },
  eZ: { l: "useChainFlags", M: "nearEnabled" },
  tr: { f: "validSolanaAddress" },
  te: { h: "isEvmAddress", c: "canonicalCoinAddress" },
  c: { f: "isGroupIdentifier" },
  eO: { useClientServerContract: "useGroupClient" },
  eH: { f: "useGroupsEnabled" },
  eB: { N: "readGroup" },
  h: { f: "useQueries" },
  eQ: { f: "useCoinHydration" },
  tt: { f: "walletProfile" },
  eJ: { f: "useCoinUpdates" },
  H: { c: "classNames" },
  m: { T: "useProfile" },
  u: { s: "useVerifiedProfile" },
  P: { O: "formatFollowers" },
};
const rendererNamespaces = {
  q: { _: "Heading" },
  e_: { L: "Empty" },
  T: { l: "SkeletonPart" },
  f: { default: "Link" },
  s: { L3: "SearchIcon" },
  A: { S: "ProfileDisplay" },
};
const required = [
  ...new Set(Object.values(namespaces).flatMap((v) => Object.values(v))),
  "memoCache",
  "groupProfileKey",
  "useNearCoins",
  "normalizeNearInput",
];
export async function recover(root = APP_ROOT) {
  const corpus = await openCorpus(root),
    f = await corpus.factory(238128, {
      source: "evidence/web/objects/ccb10fa3de5597c4.js",
    });
  assert.equal(f.provenance.sha256, HASH);
  assert.equal(
    corpus.index.modules.filter((m) => m.ids.includes(238128)).length,
    1,
    "new RecentTerms context requires review",
  );
  const navigation = await verifyNavigation(root),
    proofs = [],
    bindings = [],
    frees = {},
    imports = new Map(
      f.node.body.body
        .flatMap((n) =>
          n.type === "VariableDeclaration" ? n.declarations : [],
        )
        .filter(
          (n) =>
            n.init?.type === "CallExpression" &&
            member(n.init.callee, f.runtime, "i"),
        )
        .map((n) => [n.id.name, n]),
    ),
    used = new Set();
  for (const name of retained) {
    frees[name] = freeNames(value(f, name));
    frees[name].forEach((n) => used.add(n));
    proofs.push(
      cite(
        f,
        own(f, name),
        "complete recent-term component/selector/context " + name,
      ),
    );
  }
  for (const name of [...used].sort()) {
    const n = imports.get(name);
    if (!n) continue;
    const id = n.init.arguments[0].value;
    bindings.push({
      name,
      id,
      import: cite(f, n, "actual recent-term import " + id),
      variants: corpus.index.modules
        .filter((m) => m.ids.includes(id))
        .map((m) => ({ ids: m.ids, sha256: m.sha256, origins: m.origins })),
    });
  }
  const roles = await corpus.factory(292686),
    constants = {};
  for (const name of ["SEARCH", "RECENT_LIST"]) {
    const p = exactlyOne(
      findNodes(
        roles.node,
        (n) => n.type === "ObjectProperty" && propertyName(n.key) === name,
      ),
      "source event enum " + name,
    );
    assert.equal(p.value.type, "NumericLiteral");
    constants[name] = p.value.value;
    proofs.push(cite(roles, p, "source event enum " + name));
  }
  const chainFactory = await corpus.factory(646908, {
      source: "evidence/web/objects/1e479323ffe53c14.js",
    }),
    chain = value(chainFactory, "d");
  assert.equal(chain.type, "StringLiteral");
  assert.equal(chain.value, "near:mainnet");
  const chainImport = own(f, "eY");
  assert.equal(chainImport.init.arguments[0].value, 646908);
  proofs.push(
    cite(f, chainImport, "credited Near helper chain namespace"),
    cite(chainFactory, chain, "credited Near result chain_id literal"),
  );
  const nearResult = {
    byAddress:
      "Map keyed by raw Near address; supplied records preserve other fields and carry chain_id",
    chainId: chain.value,
    pending: "cohort boolean from credited tc combine",
  };
  const ns = Object.entries({ ...namespaces, ...rendererNamespaces })

    .map(
      ([name, values]) =>
        "const " +
        name +
        "={" +
        Object.entries(values)
          .map(
            ([key, v]) =>
              JSON.stringify(key) +
              ":ports." +
              (rendererNamespaces[name] ? "renderers." : "") +
              v,
          )
          .join(",") +
        "};",
    );
  const code = [
    "// Complete original RecentTerms/read-state/address-row frames with explicit supplied capabilities.",
    'import {normalizeSolanaInput,profileRoute} from "../search-navigation/navigation.mjs";',
    "export function createRecentSearchRenderer(ports){",
    "for(const name of " +
      JSON.stringify(required) +
      ')if(typeof ports?.[name]!=="function")throw new TypeError("Explicit recent search capability required: "+name);',
    "for(const name of " +
      JSON.stringify([
        ...Object.values(rendererNamespaces).flatMap((v) => Object.values(v)),
        "CoinRow",
        "GroupRow",
      ]) +
      ')if(!ports.renderers?.[name])throw new TypeError("Explicit recent search renderer required: "+name);',
    'if(!ports.React||!ports.jsxRuntime||!ports.styles||!Object.hasOwn(ports,"avatarSize"))throw new TypeError("Explicit React/JSX/style/size capabilities required");',
    "const a=ports.React,t=ports.jsxRuntime,r={c:ports.memoCache},d={R:normalizeSolanaInput},o={$:profileRoute},to=ports.useNearCoins,ti=ports.normalizeNearInput,F=ports.styles.row,V=ports.styles.action,$=ports.avatarSize,Z=ports.renderers.CoinRow,en=ports.renderers.GroupRow,eK={f:{profile:ports.groupProfileKey}};",
    "const n={Ae:{SEARCH:" +
      constants.SEARCH +
      "},k9:{RECENT_LIST:" +
      constants.RECENT_LIST +
      "}};",
    ...ns,
    ...retained.map((name) => {
      const n = own(f, name);
      return n.type === "FunctionDeclaration"
        ? f.text(n)
        : f.node.body.body.find(
            (s) =>
              s.type === "VariableDeclaration" && s.declarations.includes(n),
          ).kind +
            " " +
            f.text(n) +
            ";";
    }),
    "return {RecentTerms:tu,AddressRow:td};",
    "}",
  ].join("\n");
  const client = await prettier.format(code, { parser: "babel" }),
    emitted = parse(client, { sourceType: "module" }),
    ctor = emitted.program.body.find(
      (n) => n.type === "ExportNamedDeclaration",
    ).declaration,
    decls = ctor.body.body.flatMap((n) =>
      n.type === "VariableDeclaration"
        ? n.declarations
        : n.type === "FunctionDeclaration"
          ? [n]
          : [],
    ),
    get = (name) =>
      exactlyOne(
        decls.filter((n) => n.id?.name === name),
        "emitted recent binding " + name,
      ),
    allowed = new Set([
      ...Object.keys(namespaces),
      ...Object.keys(rendererNamespaces),
      ...retained,
      "a",
      "t",
      "r",
      "d",
      "o",
      "to",
      "ti",
      "eK",
      "F",
      "V",
      "$",
      "Z",
      "en",
      "n",
      "Map",
      "Set",
      "Symbol",
      "encodeURIComponent",
    ]);
  for (const name of retained) {
    assert.deepEqual(
      ast(get(name)),
      ast(own(f, name)),
      "complete recent strict AST changed " + name,
    );
    assert.deepEqual(
      frees[name].filter((n) => !allowed.has(n)),
      [],
      "unbound recent capability " + name,
    );
  }
  const owner = value(f, "tg"),
    handoff = exactlyOne(
      findNodes(
        owner,
        (n) =>
          n.type === "CallExpression" &&
          n.arguments[0]?.type === "Identifier" &&
          n.arguments[0].name === "tu" &&
          n.callee?.type === "SequenceExpression" &&
          member(n.callee.expressions[1], "t", "jsx"),
      ),
      "actual MAIN RecentTerms consumer",
    );
  proofs.push(cite(f, handoff, "actual MAIN/#1925 RecentTerms props handoff"));
  for (const name of ["to", "tc", "tb", "ti", "F", "V", "$"])
    proofs.push(
      cite(f, own(f, name), "credited existing helper/style boundary " + name),
    );
  const near = value(f, "to"),
    nearReturn = exactlyOne(
      findNodes(
        near,
        (n) =>
          n.type === "CallExpression" &&
          n.callee?.type === "SequenceExpression" &&
          member(n.callee.expressions[1], "h", "f"),
      ),
      "original Near query consumer",
    );
  proofs.push(
    cite(f, nearReturn, "credited #1925 Near helper query runtime shape"),
  );
  const files = [
      "reconstruction/search-navigation/navigation.mjs",
      "reconstruction/search-navigation/PROVENANCE.json",
      "scripts/verify-search-navigation.mjs",
      "scripts/verify-search-planner.mjs",
    ],
    dependencies = await Promise.all(
      files.map(async (file) => ({
        file,
        sha256: sha256(await readFile(path.join(root, file))),
      })),
    );
  const contract = {
    schemaVersion: 1,
    scope:
      "Complete ordinary RecentTerms visible-candidate/query/data join and address-profile display boundary; explicit provider and renderer results only.",
    factory: f.provenance,
    manifestSha256: corpus.anchors.manifestSha256,
    clientSha256: sha256(client),
    retained,
    frees,
    requiredFunctions: required,
    requiredRenderers: [
      ...Object.values(rendererNamespaces).flatMap((v) => Object.values(v)),
      "CoinRow",
      "GroupRow",
    ],
    namespaces,
    queryKeyBinding: "eK.f.profile -> ports.groupProfileKey",
    rendererNamespaces,
    constants,
    nearResult,
    bindings,
    proofs,
    dependencies,
    comparison:
      "Complete selected declarations/functions compare strictly; only parser positions/comments/raw spelling ignored. No alpha/branch/type/operation masks or captured-code execution.",
    credits: {
      parent:
        "#1245 local history persistence and #1925 parent state/query/recents remain outside, unchanged. Actual MAIN props bound; no unmerged imports.",
      rows: "OPEN #1937 row implementations and other renderers remain required matching ports; not copied or combined-runtime qualified.",
      near: "useNearCoins(mints,enabled) matches original to helper alreadyrecovered #1925; required {byAddress:Map,pending} supplied result, no hidden import or new Near provider.",
      normalization:
        "Accepted search-navigation Solana normalization/profileRoute imported+verified unchanged; Near normalization/admission/canonical/curve ports keep actual source signatures.",
      profile:
        "Existing782067 coalescer/profile hook and179736 verified-profile/#1841 remain supplied; no profile/verification acquisition or duplicate reader.",
      proof:
        "Bounded free-binding audit reused from prior own source units; no shared source/parser edits or separate utility credit.",
    },
    limits: [
      "Props contain supplied ordinary history terms; no storage/history persistence, account/session/credential/cookie/provider acquisition or actual query/navigation/subscription.",
      "Query/debounce/store/hydration/feature/classification/ProfileDisplay ports stay external; no current variant winner or service/API/auth policy inference.",
      "Group query forwards client/id/signal and retains30s enabled/options/combine precedence; query lifecycle/retry/abort scheduling remains supplied.",
      "Near result Map/pending follows existing helper interface; no new Near/RPC/read provider. Group/coin/profile results are supplied, not acquired.",
      "Ordinary CoinRow/GroupRow rendering/selection remain matching external1937 ports; Perps/protected actions/excluded detail pages not implemented/executed.",
      "No mounted product/wholeSearchDialog/visual/security/native/API/backend/feature completion claim or progress change.",
    ],
  };
  return { client, contract: JSON.stringify(contract, null, 2) + "\n" };
}
export async function verify(root = APP_ROOT) {
  const g = await recover(root);
  for (const [file, text] of [
    ["client.mjs", g.client],
    ["contract.json", g.contract],
  ])
    assert.equal(
      await readFile(path.join(root, DIRECTORY, file), "utf8"),
      text,
      "canonical " + file + " changed",
    );
  return JSON.parse(g.contract);
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  try {
    assert(
      process.argv.length === 3 &&
        ["--write", "--check"].includes(process.argv[2]),
      "usage: --write|--check",
    );
    if (process.argv[2] === "--write") {
      const g = await recover();
      await mkdir(path.join(APP_ROOT, DIRECTORY), { recursive: true });
      for (const [file, text] of [
        ["client.mjs", g.client],
        ["contract.json", g.contract],
      ])
        await writeFile(path.join(APP_ROOT, DIRECTORY, file), text);
    } else await verify();
    console.log(
      "PASS complete RecentTerms candidate/read-state/address renderer source",
    );
  } catch (e) {
    console.error(e);
    process.exitCode = 1;
  }
}
