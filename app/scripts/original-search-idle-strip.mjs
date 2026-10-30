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
export const DIRECTORY = "reconstruction/search-idle-strip";
const HASH = "9e5affafd605f47d6c9466659c4bc0a654fae027f4beff481337a1cdf1263828";
const retained = [
  "eh",
  "ef",
  "ex",
  "ep",
  "eg",
  "eb",
  "ta",
  "ts",
  "tm",
  "th",
  "tf",
  "tx",
  "tp",
  "tS",
  "tA",
  "K",
  "Q",
  "W",
  "$",
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
  i: { k: "useFlag" },
  m: { T: "useProfile" },
  P: {
    k: "pnlTone",
    u: "formatPnlUsd",
    c: "formatPnlPercent",
    l: "formatMarketCap",
  },
  H: { c: "classNames" },
  O: { h: "useLiveMarketCap" },
  L: { f: "useCoinImpression" },
  M: { f: "useCoinClickHandlers" },
  B: { y: "useImpressionContext" },
  eN: { f: "useCandlesticks" },
  S: { W: "cleanSymbol" },
  R: { W: "usePrefetch" },
};
const rendererNamespaces = {
  s: { S: "PreviousIcon", kK: "NextIcon" },
  em: { _: "ArrowButton" },
  q: { _: "Heading" },
  e_: { L: "Empty" },
  T: { l: "SkeletonPart" },
  f: { default: "Link" },
  A: { S: "ProfileDisplay" },
  ey: { X: "SegmentedControl" },
  N: { CoinAvatar: "CoinAvatar" },
  C: { f: "CoinName" },
  g: { f: "Sparkline" },
};
const required = [
  ...new Set(Object.values(namespaces).flatMap(Object.values)),
  "memoCache",
];
const renderers = Object.values(rendererNamespaces).flatMap(Object.values);
export async function recover(root = APP_ROOT) {
  const corpus = await openCorpus(root),
    f = await corpus.factory(238128, {
      source: "evidence/web/objects/ccb10fa3de5597c4.js",
    });
  assert.equal(f.provenance.sha256, HASH);
  assert.equal(
    corpus.index.modules.filter((m) => m.ids.includes(238128)).length,
    1,
    "new idle strip context requires review",
  );
  await verifyNavigation(root);
  const proofs = [],
    bindings = [],
    frees = {},
    used = new Set();
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
  for (const name of retained) {
    frees[name] = freeNames(value(f, name));
    frees[name].forEach((n) => used.add(n));
    proofs.push(
      cite(
        f,
        own(f, name),
        "complete idle-strip component/helper/context " + name,
      ),
    );
  }
  // k and l are used through retained size and supplied constant namespace.
  used.add("k");
  used.add("l");
  used.add("n");
  for (const name of [...used].sort()) {
    const n = imports.get(name);
    if (!n) continue;
    const id = n.init.arguments[0].value;
    bindings.push({
      name,
      id,
      import: cite(f, n, "actual idle-strip import " + id),
      variants: corpus.index.modules
        .filter((m) => m.ids.includes(id))
        .map((m) => ({ ids: m.ids, sha256: m.sha256, origins: m.origins })),
    });
  }
  const constants = {},
    roles = await corpus.factory(292686);
  for (const name of ["SEARCH", "ACTIVE_SEARCH_TRENDING_COIN_LIST"]) {
    const n = exactlyOne(
      findNodes(
        roles.node,
        (n) => n.type === "ObjectProperty" && propertyName(n.key) === name,
      ),
      "source event enum " + name,
    );
    assert.equal(n.value.type, "NumericLiteral");
    constants[name] = n.value.value;
    proofs.push(cite(roles, n, "source event enum " + name));
  }
  const flagFactory = await corpus.factory(322315),
    flag = exactlyOne(
      findNodes(
        flagFactory.node,
        (n) =>
          n.type === "AssignmentExpression" &&
          n.left.type === "MemberExpression" &&
          propertyName(n.left.property) === "WEB_AVATAR_DECORATIONS",
      ),
      "avatar decoration flag key",
    );
  assert.equal(flag.right.type, "StringLiteral");
  constants.WEB_AVATAR_DECORATIONS = flag.right.value;
  proofs.push(
    cite(
      flagFactory,
      flag,
      "existing avatar flag key; value supplied by useFlag",
    ),
  );
  const ns = Object.entries({ ...namespaces, ...rendererNamespaces }).map(
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
    "// Complete ordinary SearchDialog idle Discover strip and used tiles/scroll/skeleton frames.",
    'import {profileRoute} from "../search-navigation/navigation.mjs";',
    "export function createSearchIdleStrip(ports){",
    "for(const name of " +
      JSON.stringify(required) +
      ')if(typeof ports?.[name]!=="function")throw new TypeError("Explicit idle strip capability required: "+name);',
    "for(const name of " +
      JSON.stringify(renderers) +
      ')if(!ports.renderers?.[name])throw new TypeError("Explicit idle strip renderer required: "+name);',
    'if(!ports.React||!ports.jsxRuntime||!ports.browserWindow||typeof ports.MutationObserver!=="function"||!Object.hasOwn(ports,"ResizeObserver")||!Object.hasOwn(ports,"avatarSize"))throw new TypeError("Explicit React/JSX/browser/observer/size capabilities required");',
    "const a=ports.React,t=ports.jsxRuntime,r={c:ports.memoCache},o={$:profileRoute},k={s:{comfortable:ports.avatarSize}},window=ports.browserWindow,ResizeObserver=ports.ResizeObserver,MutationObserver=ports.MutationObserver;",
    "const n={Ae:{SEARCH:" +
      constants.SEARCH +
      "},k9:{ACTIVE_SEARCH_TRENDING_COIN_LIST:" +
      constants.ACTIVE_SEARCH_TRENDING_COIN_LIST +
      "}},l={D:{WEB_AVATAR_DECORATIONS:" +
      JSON.stringify(constants.WEB_AVATAR_DECORATIONS) +
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
    "return {DiscoverStrip:tp,TraderTile:tm,CoinTile:tf,TraderSkeleton:th,CoinSkeleton:tx,Arrows:ex};",
    "}",
  ].join("\n");
  const client = await prettier.format(code, { parser: "babel" }),
    emitted = parse(client, { sourceType: "module" }),
    ctor = emitted.program.body.find(
      (n) => n.type === "ExportNamedDeclaration",
    ).declaration;
  const decls = ctor.body.body.flatMap((n) =>
      n.type === "VariableDeclaration"
        ? n.declarations
        : n.type === "FunctionDeclaration"
          ? [n]
          : [],
    ),
    get = (name) =>
      exactlyOne(
        decls.filter((n) => n.id?.name === name),
        "emitted idle binding " + name,
      );
  const allowed = new Set([
    ...Object.keys(namespaces),
    ...Object.keys(rendererNamespaces),
    ...retained,
    "a",
    "t",
    "r",
    "o",
    "k",
    "n",
    "l",
    "window",
    "ResizeObserver",
    "MutationObserver",
    "Symbol",
    "Array",
    "Number",
  ]);
  for (const name of retained) {
    assert.deepEqual(
      ast(get(name)),
      ast(own(f, name)),
      "complete idle strict AST changed " + name,
    );
    assert.deepEqual(
      frees[name].filter((n) => !allowed.has(n)),
      [],
      "unbound idle capability " + name,
    );
  }
  const handoff = exactlyOne(
    findNodes(
      value(f, "tg"),
      (n) =>
        n.type === "CallExpression" &&
        n.arguments[0]?.type === "Identifier" &&
        n.arguments[0].name === "tp" &&
        n.callee.type === "SequenceExpression" &&
        member(n.callee.expressions[1], "t", "jsx"),
    ),
    "actual MAIN idle-strip consumer",
  );
  proofs.push(cite(f, handoff, "actual MAIN/#1925 idle-strip props handoff"));
  const descriptor = handoff.arguments[1];
  assert.deepEqual(
    descriptor.properties.map((p) => propertyName(p.key)),
    [
      "topTraders",
      "topTradersLoading",
      "trendingCoins",
      "trendingLoading",
      "onNavigate",
    ],
  );
  const tp = value(f, "tp"),
    subscribe = exactlyOne(
      findNodes(
        tp,
        (n) =>
          n.type === "CallExpression" &&
          n.callee.type === "SequenceExpression" &&
          member(n.callee.expressions[1], "a", "useSyncExternalStore"),
      ),
      "complete inline scroll store",
    );
  proofs.push(
    cite(f, subscribe, "actual native scroll external-store subscription"),
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
      "Complete ordinary SearchDialog idle Discover strip, scroll/selection state and trader/coin display handoff; existing service/renderer/browser capabilities supplied",
    factory: f.provenance,
    manifestSha256: corpus.anchors.manifestSha256,
    clientSha256: sha256(client),
    retained,
    frees,
    requiredFunctions: required,
    requiredRenderers: renderers,
    namespaces,
    rendererNamespaces,
    constants,
    bindings,
    proofs,
    dependencies,
    browserPorts: {
      browserWindow:
        "Required sessionStorage getItem/setItem and optional matchMedia exact source API; synthetic capability only, never real storage",
      MutationObserver:
        "Required constructor, observe(node,{childList:true}) and disconnect; source subscription cleanup",
      ResizeObserver:
        "Explicit constructor or undefined; source availability check/optional observe and disconnect",
      avatarSize:
        "Existing951425.s.comfortable value supplied exactly; retained $ declaration source-bound",
    },
    caller: {
      props: [
        "topTraders",
        "topTradersLoading",
        "trendingCoins",
        "trendingLoading",
        "onNavigate",
      ],
      guard:
        "Actual parent renders tp when raw draft w is falsy; parent1925 unchanged, no additional open/auth gate",
    },
    comparison:
      "Complete selected declarations/functions compare strictly; only parser positions/comments/raw spelling ignored. No alpha/type/branch/operation masks or captured execution.",
    credits: {
      parent:
        "OPEN1925 provides the exact source-bound data/loading/callback props and owns all acquisition/query/state. No hidden import, no new request or duplicate parent helper.",
      rows: "Ordinary result rows1937/recent terms1962 are separate and unchanged; these are the distinct complete idle tile/strip frames.",
      providers:
        "Chart/media/Avatar/profile/decoration/prefetch/metrics/formatter providers retain exact required call signatures; existing1916/1927/#1841 or other attributed work stays external, not duplicated.",
      navigation:
        "Accepted profileRoute imported and verified unchanged. Coin detail href is retained source metadata only; no detail-page or actual navigation implementation.",
      proof:
        "Bounded source-scope audit reused from own1925/1937/1962, not shared helper changes or separate utility credit.",
    },
    limits: [
      "No actual session/local storage/cookie/account/credential/config/flag/service/price/leaderboard query or provider acquisition; supplied synthetic rows/results only.",
      "PnlUsd/PnlPercent/market cap are supplied fields with exact display formatter ports, not inferred financial/accounting/ranking data.",
      "Coin click instrumentation/prefetch/links remain supplied callback/metadata ports; no original navigation, protected action, detail page or provider implementation/execution.",
      "Native scroll/DOM listener/observer/motion APIs retain source calls; synthetic browserWindow storage/motion may be injected. No production persistence or current original renderer/provider parity.",
      "No product mount/Next/full-app/visual/API/native/backend/security/accounting/feature-completion claim or progress change; no combined1925runtime qualification.",
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
    console.log("PASS complete SearchDialog idle Discover strip source");
  } catch (e) {
    console.error(e);
    process.exitCode = 1;
  }
}
