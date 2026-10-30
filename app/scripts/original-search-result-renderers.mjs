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
export const DIRECTORY = "reconstruction/search-result-renderers";
const HASH = "9e5affafd605f47d6c9466659c4bc0a654fae027f4beff481337a1cdf1263828";
const retained = [
  "v",
  "Z",
  "Y",
  "ee",
  "et",
  "en",
  "ed",
  "eu",
  "K",
  "Q",
  "G",
  "J",
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
  O: { h: "useCoinMarketCap" },
  L: { f: "useCoinImpression" },
  M: { f: "useCoinClick" },
  B: { y: "useLastClick" },
  R: { W: "useCoinPrefetch" },
  z: { Op: "trackBookmark" },
  S: { W: "formatSymbol", e: "shortenAddress" },
  H: { c: "classNames" },
  P: { l: "formatMarketCap", O: "formatFollowers" },
  u: { s: "useVerifiedProfile" },
  es: { Z: "groupRoute" },
  _: { f: "normalizeImage" },
  eo: { h: "projectGroup" },
  D: { x: "isPerp" },
  U: { K: "perpDisplay" },
};
const rendererNamespaces = {
  y: { f: "BookmarkMenu" },
  N: { CoinAvatar: "CoinAvatar" },
  C: { f: "CoinName" },
  E: { f: "RelativeTime" },
  f: { default: "Link" },
  A: { S: "ProfileDisplay" },
  T: { l: "SkeletonPart" },
  w: { f: "Avatar" },
  b: { BQ: "GroupIcon" },
  er: { E: "Badge" },
  q: { _: "Heading" },
};
const required = [
  ...new Set(Object.values(namespaces).flatMap((v) => Object.values(v))),
  "memoCache",
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
    "new dialog variants require review",
  );
  const navigation = await verifyNavigation(root),
    proofs = [],
    bindings = [],
    frees = {};
  const imports = new Map(
    f.node.body.body
      .flatMap((n) => (n.type === "VariableDeclaration" ? n.declarations : []))
      .filter(
        (n) =>
          n.init?.type === "CallExpression" &&
          member(n.init.callee, f.runtime, "i"),
      )
      .map((n) => [n.id.name, n]),
  );
  const used = new Set();
  for (const name of retained) {
    const n = value(f, name);
    frees[name] = freeNames(n);
    frees[name].forEach((v) => used.add(v));
    proofs.push(
      cite(f, own(f, name), "complete used result component/constant " + name),
    );
  }
  for (const name of [...used].sort()) {
    const imported = imports.get(name);
    if (!imported) continue;
    const id = imported.init.arguments[0].value;
    bindings.push({
      name,
      id,
      import: cite(f, imported, "actual renderer import " + id),
      variants: corpus.index.modules
        .filter((m) => m.ids.includes(id))
        .map((m) => ({ ids: m.ids, sha256: m.sha256, origins: m.origins })),
    });
  }
  const roles = await corpus.factory(292686),
    constants = {};
  for (const name of ["SEARCH", "ACTIVE_SEARCH_COIN_SEARCH_FEED"]) {
    const p = exactlyOne(
      findNodes(
        roles.node,
        (n) => n.type === "ObjectProperty" && propertyName(n.key) === name,
      ),
      "source enum " + name,
    );
    assert.equal(p.value.type, "NumericLiteral");
    constants[name] = p.value.value;
    proofs.push(cite(roles, p, "source event enum " + name));
  }
  const lines = Object.entries({ ...namespaces, ...rendererNamespaces }).map(
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
    "// Full ordinary shared-search result components; all data/rendering providers are required capabilities.",
    'import {profileRoute} from "../search-navigation/navigation.mjs";',
    "export function createSearchResultRenderers(ports){",
    "for(const name of " +
      JSON.stringify(required) +
      ')if(typeof ports?.[name]!=="function")throw new TypeError("Explicit search result capability required: "+name);',
    "for(const name of " +
      JSON.stringify([
        ...Object.values(rendererNamespaces).flatMap((v) => Object.values(v)),
        "PerpRow",
      ]) +
      ')if(!ports.renderers?.[name])throw new TypeError("Explicit search result renderer required: "+name);',
    'if(!ports.jsxRuntime||!ports.theme||!ports.styles||!Object.hasOwn(ports,"avatarSize")||!Object.hasOwn(ports,"imagePrefix"))throw new TypeError("Explicit JSX/theme/style/avatar/image-prefix capabilities required");',
    "const t=ports.jsxRuntime,r={c:ports.memoCache},o={$:profileRoute},k=ports.theme,F=ports.styles.row,V=ports.styles.seeAll,$=ports.avatarSize,ea={f:ports.imagePrefix},X=ports.renderers.PerpRow;",
    "const n={Ae:{SEARCH:" +
      constants.SEARCH +
      "},k9:{ACTIVE_SEARCH_COIN_SEARCH_FEED:" +
      constants.ACTIVE_SEARCH_COIN_SEARCH_FEED +
      "}};",
    ...lines,
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
    "return {CoinRow:Z,OrdinaryCoinRow:Y,UserRow:ee,GroupRow:en,Skeleton:et,MixedResults:eu};",
    "}",
  ].join("\n");
  const client = await prettier.format(code, { parser: "babel" }),
    emitted = parse(client, { sourceType: "module" }),
    constructor = emitted.program.body.find(
      (n) => n.type === "ExportNamedDeclaration",
    ).declaration;
  const declarations = constructor.body.body.flatMap((n) =>
      n.type === "VariableDeclaration"
        ? n.declarations
        : n.type === "FunctionDeclaration"
          ? [n]
          : [],
    ),
    get = (name) =>
      exactlyOne(
        declarations.filter((n) => n.id?.name === name),
        "emitted result binding " + name,
      );
  const allowed = new Set([
    ...Object.keys(namespaces),
    ...Object.keys(rendererNamespaces),
    ...retained,
    "t",
    "r",
    "o",
    "k",
    "F",
    "V",
    "$",
    "ea",
    "X",
    "n",
    "Array",
    "Number",
    "Symbol",
  ]);
  for (const name of retained) {
    const source = own(f, name),
      out = get(name);
    assert.deepEqual(
      ast(out),
      ast(source),
      "complete strict result AST changed " + name,
    );
    assert.deepEqual(
      frees[name].filter((v) => !allowed.has(v)),
      [],
      "unbound result capability " + name,
    );
  }
  const owner = value(f, "tg");
  for (const name of ["Z", "ee", "en", "et", "eu"]) {
    const calls = findNodes(
      owner,
      (n) =>
        n.type === "CallExpression" &&
        n.arguments[0]?.type === "Identifier" &&
        n.arguments[0].name === name &&
        n.callee?.type === "SequenceExpression" &&
        member(n.callee.expressions[1], "t", "jsx"),
    );
    assert(calls.length > 0, "MAIN result consumer missing " + name);
    for (const c of calls)
      proofs.push(
        cite(f, c, "actual MAIN owning-controller result handoff " + name),
      );
  }
  for (const name of ["tK", "t$", "tF"]) {
    const n = exactlyOne(
      findNodes(
        owner,
        (n) => n.type === "VariableDeclarator" && n.id?.name === name,
      ),
      "actual selected-row callback " + name,
    );
    proofs.push(cite(f, n, "credited #1925 owning selection callback " + name));
  }
  for (const name of ["$", "F", "V"])
    proofs.push(
      cite(f, own(f, name), "external style/size provider expression " + name),
    );
  const files = [
    "reconstruction/search-navigation/navigation.mjs",
    "reconstruction/search-navigation/PROVENANCE.json",
    "scripts/verify-search-navigation.mjs",
    "scripts/verify-search-planner.mjs",
  ];
  const dependencies = await Promise.all(
    files.map(async (file) => ({
      file,
      sha256: sha256(await readFile(path.join(root, file))),
    })),
  );
  const contract = {
    schemaVersion: 1,
    scope:
      "Complete ordinary shared-search row and mixed-result rendering family; external providers and deferred Perps remain required unqualified ports.",
    factory: f.provenance,
    manifestSha256: corpus.anchors.manifestSha256,
    clientSha256: sha256(client),
    strictComparison:
      "All thirteen original component/helper/constant nodes compare exactly except parser positions/comments/raw metadata; no alpha/type/operation/branch masks.",
    retained,
    frees,
    requiredFunctions: required,
    requiredRenderers: [
      ...Object.values(rendererNamespaces).flatMap((v) => Object.values(v)),
      "PerpRow",
    ],
    namespaces,
    rendererNamespaces,
    constants,
    bindings,
    proofs,
    dependencies,
    credits: {
      parent:
        "#1925 full SearchDialog controller owns query/recents/filter/selection; not imported or copied here. Actual source handoffs are bound.",
      navigation: {
        unit: "existing accepted search-navigation profile route helper; verifier reused unchanged",
        adapterSha256: navigation.adapterSha256,
      },
      verifiedProfile:
        "OPEN #1841 complete179736 query/693124 verification consumer remains supplied, no hidden dependency",
      avatar:
        "OPEN #1916/#1927 Avatar/decorations and existing helper/readers remain required ports; no duplicate recovery",
      other:
        "Existing formatting/RelativeTime/coin cache/impression/readonly prefetch/rendering providers are supplied, not inferred implementations. Bounded free-binding audit is proof infrastructure reused from #1925.",
    },
    limits: [
      "Perps dispatch is preserved only through required classifier/display/component ports; finite scope is ordinary rows and no Perps implementation/provider compatibility is claimed.",
      "Menu receives original coin/position/analytics descriptor; no protected action implementation or actual menu action execution.",
      "Market-cap metadata rounding/fallback is the original UI computation, not accounting or real market data. Formatting, clock/relative-age and snapshot providers remain explicit.",
      "All values/rendering/navigation/analytics/read hooks are supplied; no acquisition, service/HTTP/auth/session/cookie/storage/credential action or captured-module execution.",
      "Not mounted product UI, backend/API/native/security/visual/whole-runtime equivalence or feature-completion progress. Excluded coin routes remain strings.",
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
    console.log("PASS complete ordinary shared-search result rendering family");
  } catch (e) {
    console.error(e);
    process.exitCode = 1;
  }
}
