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
import { verifySearchShortcuts } from "./verify-search-shortcuts.mjs";
export const APP_ROOT = fileURLToPath(new URL("..", import.meta.url));
export const DIRECTORY = "reconstruction/search-dialog-controller";
const SOURCE = "evidence/web/objects/ccb10fa3de5597c4.js";
const HASH = "9e5affafd605f47d6c9466659c4bc0a654fae027f4beff481337a1cdf1263828";
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
    "factory declaration " + name,
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

// Each key is the actual original import spelling; values are required, explicit
// source-signature capabilities. This is not an implementation of providers.
const namespaces = {
  p: { f: "useTranslation" },
  e8: { F: "useSearchOpen", Z: "useSetSearchOpen" },
  e9: { M: "useNsfw" },
  eM: { j: "useLocalTerms", r: "useDebouncedValue" },
  eP: { U: "useRecentCoins", A: "recentCoinViewedAt" },
  eZ: { l: "useChainFlags", M: "nearEnabled", k: "hexEnabled" },
  eQ: { f: "useCoinHydration" },
  te: { c: "canonicalCoinAddress", h: "isEvmAddress" },
  i: { k: "useFlag" },
  eL: { f: "useRecentCards" },
  x: { useRouter: "useRouter" },
  M: { f: "useCoinClick" },
  B: { y: "useLastClick" },
  tr: { f: "validSolanaAddress" },
  eA: { Q: "probeKnownMint" },
  e1: { isSolanaMintOnChain: "probeSolanaMint" },
  tt: { f: "walletProfile" },
  eI: { j: "getContractClient" },
  z: {
    pL: "trackMintPaste",
    Cv: "trackWalletPaste",
    iu: "trackSearch",
    P8: "trackOpen",
    bG: "trackClear",
    mM: "trackTab",
  },
  eS: { k: "readCoin" },
  eE: { useQuery: "useQuery" },
  eV: { f: "useCoinSearch" },
  D: { x: "isPerp" },
  U: { K: "perpDisplay" },
  eJ: { f: "useCoinUpdates" },
  eX: { N: "useUserSearch" },
  eH: { f: "useGroupsEnabled" },
  eO: { useClientServerContract: "useGroupClient" },
  ez: { useQueryClient: "useQueryClient" },
  eo: { h: "projectGroup" },
  eD: { useInfiniteQuery: "useInfiniteQuery" },
  h: { f: "useQueries" },
  e0: { D: "isNearIdentifier" },
  H: { c: "classNames" },
};
const rendererNamespaces = {
  ew: { N: "Dialog", K: "Body", c: "Footer" },
  ek: { o: "Input" },
  q: { _: "Heading" },
  e_: { L: "Empty" },
  ej: { p: "Tabs" },
  f: { default: "Link" },
  s: { kK: "ArrowIcon" },
};
const renderers = {
  tp: "Recommendations",
  tu: "RecentTerms",
  ec: "RecentCard",
  Z: "CoinRow",
  et: "Skeleton",
  eu: "MixedResults",
  en: "GroupRow",
  ee: "UserRow",
};
const retained = [
  "e$",
  "eF",
  "eW",
  "e2",
  "e3",
  "e5",
  "e6",
  "e7",
  "ti",
  "tc",
  "to",
  "tb",
  "ty",
  "tj",
  "K",
  "Q",
  "G",
  "J",
];
const required = [
  ...new Set([
    ...Object.values(namespaces).flatMap((v) => Object.values(v)),
    "memoCache",
    "readTrendingCoins",
    "readPnlLeaders",
    "resolveIdentifier",
    "searchGroups",
    "groupSearchKey",
    "groupProfileKey",
    "normalizeHexIdentifier",
    "isNearCoin",
    "isHexCoin",
  ]),
];
const literal = (n) =>
  n.type === "StringLiteral" || n.type === "NumericLiteral"
    ? n.value
    : n.type === "UnaryExpression" && n.operator === "-"
      ? -literal(n.argument)
      : assert.fail("nonliteral constant");
function exported(f, name, id) {
  const call = exactlyOne(
      findNodes(
        f.node,
        (n) =>
          n.type === "CallExpression" &&
          member(n.callee, f.runtime, "s") &&
          (n.arguments[1]?.value === id ||
            (!n.arguments[1] && f.ids.length === 1)),
      ),
      "export registration " + id,
    ),
    a = call.arguments[0].elements;
  const i = a.findIndex((n) => n?.value === name);
  assert(i >= 0);
  assert.equal(a[i + 1].value, 0);
  return a[i + 2].type === "Identifier" ? value(f, a[i + 2].name) : a[i + 2];
}
function replace(code, f, replacements) {
  for (const [n, text] of [...replacements].sort(
    (a, b) => b[0].start - a[0].start,
  ))
    code =
      code.slice(0, n.start - f.start) + text + code.slice(n.end - f.start);
  return code;
}
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
export async function recover(root = APP_ROOT) {
  const corpus = await openCorpus(root),
    f = await corpus.factory(238128, { source: SOURCE });
  assert.equal(f.provenance.sha256, HASH);
  assert.equal(
    corpus.index.modules.filter((m) => m.ids.includes(238128)).length,
    1,
    "new dialog variant requires review",
  );
  const frame = own(f, "tg"),
    lazy = exported(f, "SearchDialogLazy", 238128),
    proofs = [];
  // Bridges are restricted to the complete functions already authenticated by
  // the maintained navigation and shortcut units. Their providers stay ports.
  const navigation = await verifyNavigation(root),
    shortcuts = await verifySearchShortcuts(root);
  const sol = exactlyOne(
    findNodes(
      frame,
      (n) => n.type === "VariableDeclarator" && n.id?.name === "ef",
    ),
    "Solana callback",
  ).init.arguments[0];
  const submit = exactlyOne(
    findNodes(
      frame,
      (n) => n.type === "VariableDeclarator" && n.id?.name === "tB",
    ),
    "form submit",
  ).init;
  const matcher = exactlyOne(
    findNodes(
      frame,
      (n) =>
        n.type === "ArrowFunctionExpression" &&
        findNodes(
          n,
          (x) =>
            x.type === "MemberExpression" &&
            propertyName(x.property) === "isContentEditable",
        ).length === 1 &&
        n.params.length === 1,
    ),
    "mounted key matcher",
  );
  const bridgeSol =
    "createSolanaSearchNavigator({controllerRef:Y,pasteRef:er,validAddress:tr.f,walletProfile:tt.f,resolveIdentifier:e4,getContractClient:eI.j,probeKnownMint:eA.Q,probeSolanaMint:e1.isSolanaMintOnChain,closeDialog:ea,rememberTerm:C,trackMintPaste:z.pL,trackWalletPaste:z.Cv,trackSearch:z.iu,setLastClick:X,handleCoinClick:W,push:F,AbortController})";
  const bridgeSubmit =
    "createSearchSubmit({searchTerm:w,navigateSolana:ef,navigateEvm:ex,navigateHex:ep,navigateNear:eg,closeDialog:ea,rememberTerm:C,push:F})";
  const replacements = [
    [sol, bridgeSol],
    [submit, bridgeSubmit],
    [matcher, "createSearchShortcutHandler(e)"],
  ];
  const bridged = replace(f.text(frame), frame, replacements);
  for (const [n] of replacements)
    proofs.push(cite(f, n, "credited complete body bridge"));
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
  const bindings = [];
  for (const name of new Set([
    ...freeNames(frame),
    ...retained.flatMap((name) => freeNames(value(f, name))),
  ])) {
    const n = imports.get(name) ?? (name === "tg" ? frame : undefined);
    if (n) {
      const id = n.init.arguments[0].value;
      bindings.push({
        name,
        id,
        import: cite(f, n, "actual controller import " + id),
        variants: corpus.index.modules
          .filter((m) => m.ids.includes(id))
          .map((m) => ({ ids: m.ids, sha256: m.sha256, origins: m.origins })),
      });
    }
  }
  // Every imported name's raw factory call is retained. External variants are
  // listed, not selected/authenticated as implementations by this unit.
  const flags = await corpus.factory(322315),
    flagNames = {};
  for (const name of ["WEB_PACKS", "WEB_SEARCH_MIXED_RESULTS", "WEB_PERPS"]) {
    const n = exactlyOne(
      findNodes(
        flags.node,
        (n) =>
          n.type === "AssignmentExpression" &&
          propertyName(n.left.property) === name,
      ),
      "flag " + name,
    );
    flagNames[name] = literal(n.right);
    proofs.push(cite(flags, n, "used flag literal"));
  }
  const chains = await corpus.factory(646908),
    near = exported(chains, "d", 646908),
    hex = exported(chains, "W", 646908);
  proofs.push(
    cite(chains, near, "Near chain identifier"),
    cite(chains, hex, "hex chain identifier"),
  );
  const groupLimits = [];
  for (const variant of corpus.index.modules.filter((m) =>
    m.ids.includes(560328),
  )) {
    for (const origin of variant.origins) {
      const provider = await corpus.factory(560328, { source: origin.source });
      const page = exported(provider, "V", 560328),
        cap = exported(provider, "J", 560328);
      groupLimits.push({
        factory: provider.provenance,
        pageSize: literal(page),
        maxOffset: literal(cap),
      });
      proofs.push(
        cite(provider, page, "group default page size"),
        cite(provider, cap, "group maximum offset"),
      );
    }
  }
  assert(groupLimits.length === 5);
  assert(
    groupLimits.every(
      (v) =>
        v.pageSize === groupLimits[0].pageSize &&
        v.maxOffset === groupLimits[0].maxOffset,
    ),
    "group limit variants differ",
  );
  const enums = await corpus.factory(292686),
    recent = exactlyOne(
      findNodes(
        enums.node,
        (n) =>
          n.type === "ObjectProperty" && propertyName(n.key) === "RECENT_LIST",
      ),
      "recent-list element",
    );
  assert.equal(literal(recent.value), 30);
  proofs.push(cite(enums, recent, "recent-list element literal"));
  const allNamespaces = { ...namespaces, ...rendererNamespaces },
    namespaceLines = Object.entries(allNamespaces).map(
      ([name, props]) =>
        "const " +
        name +
        "={" +
        Object.entries(props)
          .map(
            ([key, port]) =>
              JSON.stringify(key) +
              ":ports." +
              (rendererNamespaces[name] ? "renderers." : "") +
              port,
          )
          .join(",") +
        "};",
    );
  const code = [
    "// Complete captured SearchDialog owner and lazy child. Required capabilities never acquire data by default.",
    'import {createSolanaSearchNavigator,createSearchSubmit,normalizeSolanaInput,profileRoute,SEARCH_TYPE,SCREEN,ELEMENT} from "../search-navigation/navigation.mjs";',
    'import {createSearchShortcutHandler} from "../../packages/frontend/src/components/shell/search/search-shortcuts.mjs";',
    "export function createSearchDialogController(ports){",
    "for(const name of " +
      JSON.stringify(required) +
      ')if(typeof ports?.[name]!=="function")throw new TypeError("Explicit SearchDialog capability required: "+name);',
    "for(const name of " +
      JSON.stringify([
        ...Object.values(rendererNamespaces).flatMap((v) => Object.values(v)),
        ...Object.values(renderers),
      ]) +
      ')if(!ports.renderers?.[name])throw new TypeError("Explicit SearchDialog renderer required: "+name);',
    'if(!ports.React||!ports.jsxRuntime||!ports.browserWindow||!ports.browserDocument||!ports.queryKeys||!ports.styles||!ports.AbortController)throw new TypeError("Explicit framework, DOM, query-key and style capabilities required");',
    'if(!Object.hasOwn(ports,"keepPreviousData"))throw new TypeError("Explicit placeholder-data capability required");',
    ...namespaceLines,
    "const a=ports.React,t=ports.jsxRuntime,r={c:ports.memoCache},window=ports.browserWindow,document=ports.browserDocument,AbortController=ports.AbortController;",
    "const l={D:" +
      JSON.stringify(flagNames) +
      "},n={B8:SEARCH_TYPE,Ae:SCREEN,k9:{...ELEMENT,RECENT_LIST:30}},d={R:normalizeSolanaInput},o={$:profileRoute};",
    "const eY={d:" +
      JSON.stringify(literal(near)) +
      ",W:" +
      JSON.stringify(literal(hex)) +
      ",a:ports.isNearCoin,X:ports.isHexCoin,Y:ports.normalizeHexIdentifier};",
    "const eC={Q:ports.queryKeys},eK={f:{search:ports.groupSearchKey,profile:ports.groupProfileKey}},eU={y:ports.keepPreviousData},eB={B:ports.searchGroups,V:" +
      JSON.stringify(groupLimits[0].pageSize) +
      ",J:" +
      JSON.stringify(groupLimits[0].maxOffset) +
      "};",
    "const e4=ports.resolveIdentifier,eR=ports.readTrendingCoins,eT=ports.readPnlLeaders,tn=ports.styles.key,tl=ports.styles.viewAll,V=ports.styles.clear;",
    ...Object.entries(renderers).map(
      ([name, port]) => "const " + name + "=ports.renderers." + port + ";",
    ),
    ...retained.map((name) => {
      const n = own(f, name);
      return n.type === "FunctionDeclaration"
        ? f.text(n)
        : "let " + f.text(n) + ";";
    }),
    bridged,
    "const SearchDialogLazy=" + f.text(lazy) + ";",
    "return {SearchDialog:tg,SearchDialogLazy};",
    "}",
  ].join("\n");
  const client = await prettier.format(code, { parser: "babel" });
  const emitted = parse(client, { sourceType: "module" }),
    constructor = emitted.program.body.find(
      (n) => n.type === "ExportNamedDeclaration",
    ).declaration;
  const emittedOwn = (name) =>
    exactlyOne(
      constructor.body.body
        .flatMap((n) =>
          n.type === "VariableDeclaration"
            ? n.declarations
            : n.type === "FunctionDeclaration"
              ? [n]
              : [],
        )
        .filter((n) => n.id?.name === name),
      "emitted binding " + name,
    );
  assert.deepEqual(
    ast(emittedOwn("tg")),
    ast(parse(bridged, { sourceType: "module" }).program.body[0]),
    "complete bridged frame AST",
  );
  assert.deepEqual(
    ast(emittedOwn("SearchDialogLazy").init),
    ast(lazy),
    "complete lazy wrapper AST",
  );
  for (const name of retained) {
    const before = own(f, name),
      after = emittedOwn(name);
    assert.deepEqual(
      ast(after),
      ast(before),
      "complete retained helper " + name,
    );
    proofs.push(cite(f, before, "used complete controller helper " + name));
  }
  const allowed = new Set([
    ...Object.keys(allNamespaces),
    ...Object.keys(renderers),
    ...retained,
    "a",
    "t",
    "r",
    "l",
    "n",
    "d",
    "o",
    "eY",
    "eC",
    "eK",
    "eU",
    "eB",
    "e4",
    "eR",
    "eT",
    "tn",
    "tl",
    "V",
    "window",
    "document",
    "AbortController",
    "DOMException",
    "Symbol",
    "Map",
    "Set",
    "JSON",
    "encodeURIComponent",
    "createSolanaSearchNavigator",
    "createSearchSubmit",
    "createSearchShortcutHandler",
  ]);
  const free = freeNames(emittedOwn("tg"));
  assert.deepEqual(
    free.filter((n) => !allowed.has(n)),
    [],
    "unbound controller capability",
  );
  for (const name of retained)
    assert.deepEqual(
      freeNames(emittedOwn(name)).filter((n) => !allowed.has(n)),
      [],
      "unbound helper " + name,
    );
  for (const name of [
    "e4",
    "eR",
    "eq",
    "eT",
    "tp",
    "tu",
    "ec",
    "Z",
    "et",
    "eu",
    "en",
    "ee",
    "V",
    "tn",
    "tl",
  ])
    proofs.push(
      cite(
        f,
        own(f, name),
        "external existing provider or renderer boundary " + name,
      ),
    );
  proofs.push(
    cite(f, frame, "complete original owning controller"),
    cite(f, lazy, "actual complete exported lazy child"),
  );
  const parent = await corpus.factory(400466, {
    source: "evidence/web/objects/13c13db9eb86191b.js",
  });
  const mount = exactlyOne(
    findNodes(
      parent.node,
      (n) => n.type === "ObjectProperty" && propertyName(n.key) === "onMounted",
    ),
    "actual parent mounted handoff",
  );
  proofs.push(
    cite(parent, mount, "actual parent lazy-child onMounted handoff"),
  );
  const dependencies = [
    "reconstruction/search-navigation/navigation.mjs",
    "reconstruction/search-navigation/PROVENANCE.json",
    "scripts/verify-search-navigation.mjs",
    "packages/frontend/src/components/shell/search/search-shortcuts.mjs",
    "reconstruction/search-shortcuts/PROVENANCE.json",
    "scripts/verify-search-shortcuts.mjs",
  ];
  const dependencyHashes = await Promise.all(
    dependencies.map(async (file) => ({
      file,
      sha256: sha256(await readFile(path.join(root, file))),
    })),
  );
  const contract = {
    schemaVersion: 1,
    scope:
      "Complete ordinary SearchDialog owner/lazy child with three credited proven body bridges. Explicit source-signature provider/rendering ports; no original-provider/runtime winner or mounted application claim.",
    factory: f.provenance,
    manifestSha256: corpus.anchors.manifestSha256,
    clientSha256: sha256(client),
    completeOriginalFrameSha256: sha256(JSON.stringify(ast(frame))),
    completeBridgedFrameSha256: sha256(JSON.stringify(ast(emittedOwn("tg")))),
    freeControllerBindings: free,
    requiredFunctions: required,
    requiredRendererComponents: [
      ...Object.values(rendererNamespaces).flatMap((v) => Object.values(v)),
      ...Object.values(renderers),
    ],
    namespaces,
    rendererNamespaces,
    renderers,
    groupLimits,
    bindings,
    proofs,
    bridges: {
      navigation: {
        adapterSha256: navigation.adapterSha256,
        proofs: navigation.proofs.filter((p) =>
          [
            "complete Solana identifier navigation",
            "actual ordered form submit",
          ].some((n) => p.label?.includes(n)),
        ),
      },
      shortcuts: { normalizedMatcherSha256: shortcuts.normalizedMatcherSha256 },
      dependencies: dependencyHashes,
    },
    limits: [
      "Existing search-client/session/planner/user-search/navigation/shortcuts and query/cache/hydration providers are credited external capabilities, not duplicate reconstruction. Actual 379705 has four variants; no active provider winner is inferred.",
      "Group request/projection/keys and query runtimes are explicit ports. Inline group query options, callbacks, page cap, profile cache writes and frame are retained; external group schema/service is not implemented.",
      "DOM Dialog/Input/result renderers, translation/styles and original open/local-recents stores are external. The standalone host is synthetic and does not mount or alter the maintained product.",
      "Perps classification/display and card rendering stay external deferred boundaries. Finite proof admits ordinary rows only; excluded coin detail routes are navigation strings, not implemented pages.",
      "All resolver/coin/trending/PnL/group/probe/analytics/feature results are supplied. No auth/session/credential/cookie/storage/network acquisition, live request, protected action or provider/backend equivalence.",
      "onPaste reads only the event-supplied text payload; it is not the excluded QuickPaste action workflow. Native clipboard acquisition is not implemented.",
      "The original parent pre-mount lazy-loader/fallback lifecycle remains source evidence, not implemented by this constructor. SearchDialogLazy's actual onMounted effect and child memo frame are retained.",
    ],
  };
  return { client, contract: JSON.stringify(contract, null, 2) + "\n" };
}
export async function verify(root = APP_ROOT) {
  const generated = await recover(root);
  for (const [file, text] of [
    ["client.mjs", generated.client],
    ["contract.json", generated.contract],
  ])
    assert.equal(
      await readFile(path.join(root, DIRECTORY, file), "utf8"),
      text,
      "canonical " + file + " changed",
    );
  return JSON.parse(generated.contract);
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
    console.log("PASS complete ordinary SearchDialog controller source");
  } catch (e) {
    console.error(e);
    process.exitCode = 1;
  }
}
