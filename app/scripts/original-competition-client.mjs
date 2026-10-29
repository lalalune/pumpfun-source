import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "@babel/parser";
import prettier from "prettier";
import {
  openCorpus,
  findNodes,
  member,
  exactlyOne,
  sha256,
} from "./original-contracts/source.mjs";

export const APP_ROOT = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
);
export const DIRECTORY = "reconstruction/competition-client";
const SHARED =
  "ef7acaad8c20e23d6f9821dc683cfc0dc66cc3eb1b14642674a9007c9c064205";
const REVIEWED = {
  359516: ["59b1004bf7c804e722ab718877cf19ecee28f5f157d184e14ffd65d89dcb228d"],
  961415: ["b3c4dc7eca967b4f9eaa67a43487bf6d8504bf5b4c58ccd582c2a4a3882c5d96"],
  85324: [
    "0024317d4e63db1b1791329f7416024563bc11858041efaa1e185556e58baae1",
    "67966a7a877f6aaeac36c545415ddfc2d534bcb892a9b11c56e45a5aa5560cfc",
  ],
  639287: ["4ed887ef8ddc186c2058ae314de45a3a562884ca8f1579a9f5030dd2463d1f2b"],
  706615: ["e606b2e7f5ab2bfd5da0abb70db2de0560f01d4d131d156719d8623614219e74"],
};
const PROVENANCE = {
  590407: ["3f494070c58a6d7f0f70279887ef648107935b765fe849de3e9ec100cec45dda"],
  869322: ["5ac06ec234a4bab033be3383901f80320a7490743d289beecebfb1938be675ef"],
  779106: ["e1e29868ec56b56bdbc68b58127f2c71583094d14645020b53c733a7be06423b"],
  92245: ["9b5bbc065d7b19bf7273c3fa6fcbddb2f61a6c183a2f512d6e2d2d81d5ea89e3"],
  944410: [
    "6e0b85a81829493018b501cb1137b5cf667eec841ea56b6921e6ad0875271b96",
    "eb97d758430643b5c14b01e535a4bc5490b13e7d5437d04b76fe7bb3525d1395",
  ],
  30181: ["fbae4e508e6c986c68209d975d3eea247718d478272089a60504b776074e2413"],
  96224: ["5a7aacd1e02cdcba6278e50454f2b919f6e5cfc1cc3006855c0be0d0f4344c4e"],
  139209: ["8d4ffb7afbfae1b99df53cf4d8421f1fb6f85c290468471f2e4f71f58358ed9b"],
};
const CAPS = {
  445242: ["c", "useMemoCache"],
  944410: ["useClientServerContract", "useClientServerContract"],
  690877: ["useQuery", "useQuery"],
  85324: ["q", "useForegroundInterval"],
  639287: ["f", "keys"],
  779106: ["f", "useViewerKey"],
};
const tail = (node) =>
  node.type === "SequenceExpression" ? node.expressions.at(-1) : node;
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(
    Object.entries(value)
      .filter(
        ([key]) =>
          ![
            "start",
            "end",
            "loc",
            "extra",
            "comments",
            "leadingComments",
            "trailingComments",
            "innerComments",
          ].includes(key),
      )
      .map(([key, item]) => [key, canonical(item)]),
  );
}
function sourceExport(factory, id, name) {
  const found = [];
  for (const call of findNodes(
    factory.node,
    (node) =>
      node.type === "CallExpression" &&
      member(node.callee, factory.runtime, "s") &&
      (node.arguments[1]?.value === id ||
        (!node.arguments[1] && factory.ids.length === 1 && factory.id === id)),
  )) {
    const entries = call.arguments[0].elements;
    for (let index = 0; index < entries.length; index += 3) {
      if (entries[index].value === name) found.push(entries[index + 2]);
    }
  }
  return exactlyOne(found, `actual export ${id}.${name}`);
}

export async function buildCompetitionClient(appRoot = APP_ROOT) {
  assert.equal(
    sha256(
      await readFile(
        path.join(appRoot, "scripts/original-contracts/source.mjs"),
      ),
    ),
    SHARED,
  );
  const corpus = await openCorpus(appRoot);
  const witnesses = [],
    adapters = [],
    dependencies = [];
  const outputs = new Map();
  async function physical(id, hash) {
    const row = exactlyOne(
      corpus.index.modules.filter(
        (entry) => entry.ids.includes(id) && (!hash || entry.sha256 === hash),
      ),
      `reviewed ${id}`,
    );
    const factory = await corpus.factory(id, { source: row.origins[0].source });
    assert.equal(factory.provenance.sha256, row.sha256);
    assert.equal(
      factory.capture.factories.filter((entry) => entry.ids.includes(id))
        .length,
      1,
    );
    return factory;
  }
  async function output(name, source, factory, nodes) {
    const text = await prettier.format(source, { parser: "babel" });
    outputs.set(name, text);
    adapters.push({
      path: name,
      factory: factory.provenance,
      adapterSha256: sha256(text),
      retainedAsts: nodes.map((node) => ({
        type: node.type,
        sha256: sha256(JSON.stringify(canonical(node))),
      })),
    });
    for (const node of nodes)
      witnesses.push(
        factory.witness(node, `${name} retained complete ${node.type}`),
      );
  }
  for (const [id, hashes] of Object.entries({ ...REVIEWED, ...PROVENANCE }))
    assert.deepEqual(
      corpus.index.modules
        .filter((row) => row.ids.includes(Number(id)))
        .map((row) => row.sha256)
        .sort(),
      hashes,
      `unreviewed variant set ${id}`,
    );
  for (const [id, name] of [
    [359516, "useList"],
    [961415, "useDetail"],
  ]) {
    const factory = await physical(id);
    const expression = sourceExport(factory, id, "f");
    assert.equal(expression.type, "ArrowFunctionExpression");
    const imports = factory.node.body.body[0];
    assert.equal(imports.type, "VariableDeclaration");
    assert.equal(imports.declarations.length, 6);
    const bindings = imports.declarations.map((declaration) => {
      assert.ok(member(declaration.init?.callee, factory.runtime, "i"));
      const moduleId = declaration.init.arguments[0].value;
      const [property, capability] = CAPS[moduleId];
      witnesses.push(
        factory.witness(declaration, `${id} actual import ${moduleId}`),
      );
      return `${declaration.id.name}={${JSON.stringify(property)}:${capability}}`;
    });
    assert.equal(
      findNodes(
        expression,
        (node) =>
          node.type === "MemberExpression" &&
          (member(node, factory.runtime, "i") ||
            member(node, factory.runtime, "s")),
      ).length,
      0,
    );
    await output(
      `${name}.mjs`,
      `// Source-adapted complete original hook. Providers remain explicit capabilities.\nexport function createHook({useMemoCache,useClientServerContract,useQuery,useForegroundInterval,keys,useViewerKey}){var ${bindings.join(",")};return ${factory.text(expression)};}`,
      factory,
      [expression],
    );
  }
  for (const hash of REVIEWED[85324]) {
    const factory = await physical(85324, hash);
    const imports = factory.node.body.body[0];
    assert.equal(imports.declarations.length, 1);
    assert.equal(imports.declarations[0].init.arguments[0].value, 352386);
    const binding = imports.declarations[0].id.name;
    const retained = factory.node.body.body.slice(1, -1);
    assert.ok(retained.every((node) => node.type === "VariableDeclaration"));
    const exports = {
      useFocused: sourceExport(factory, 85324, "W"),
      useVisible: sourceExport(factory, 85324, "p"),
      useForegroundInterval: sourceExport(factory, 85324, "q"),
      useVisibleInterval: sourceExport(factory, 85324, "S"),
    };
    await output(
      `foreground/${hash.slice(0, 12)}.mjs`,
      `// Source-adapted full foreground module, with injected browser and React capability.\nexport function createForegroundModule({document,window,useSyncExternalStore}){var ${binding}={useSyncExternalStore};${retained.map((node) => factory.text(node)).join("\n")}return {${Object.entries(
        exports,
      )
        .map(([key, node]) => `${key}:${factory.text(node)}`)
        .join(",")}};}`,
      factory,
      [
        ...retained,
        ...Object.values(exports).filter(
          (node) => node.type === "ArrowFunctionExpression",
        ),
      ],
    );
  }
  const keys = await physical(639287);
  const declaration = keys.node.body.body[0];
  const keyObject = sourceExport(keys, 639287, "f");
  await output(
    "keys.mjs",
    `// Complete original key object; a key does not implement any operation.\n${keys.text(declaration)}\nexport const keys=${keys.text(keyObject)};`,
    keys,
    [declaration, keyObject],
  );
  const selectors = await physical(706615);
  const select = sourceExport(selectors, 706615, "y"),
    live = sourceExport(selectors, 706615, "g");
  await output(
    "selection.mjs",
    `// Complete original bucket selection expressions; server ordering is retained.\nexport const selectCompetition=${selectors.text(select)};export const hasLiveCompetition=${selectors.text(live)};`,
    selectors,
    [select, live],
  );
  const consumers = [];
  for (const [id, wanted] of [
    [
      590407,
      [
        [359516, "f"],
        [961415, "f"],
        [706615, "y"],
      ],
    ],
    [
      869322,
      [
        [359516, "f"],
        [706615, "g"],
      ],
    ],
  ]) {
    const factory = await physical(id);
    for (const [moduleId, property] of wanted) {
      const imported = exactlyOne(
        findNodes(
          factory.node,
          (node) =>
            node.type === "VariableDeclarator" &&
            node.init?.type === "CallExpression" &&
            member(node.init.callee, factory.runtime, "i") &&
            node.init.arguments[0]?.value === moduleId,
        ),
        `${id} import ${moduleId}`,
      );
      witnesses.push(
        factory.witness(imported, `actual consumer ${id} import ${moduleId}`),
      );
      const calls = findNodes(
        factory.node,
        (node) =>
          node.type === "CallExpression" &&
          member(tail(node.callee), imported.id.name, property),
      );
      assert.ok(calls.length);
      for (const call of calls)
        witnesses.push(
          factory.witness(
            call,
            `actual consumer ${id} call ${moduleId}.${property}`,
          ),
        );
    }
    consumers.push(factory.provenance);
  }
  // These original providers are traced but not replaced with guessed auth or HTTP internals.
  for (const id of [779106, 92245, 944410, 30181, 96224, 139209]) {
    for (const row of corpus.index.modules.filter((entry) =>
      entry.ids.includes(id),
    )) {
      const factory = await physical(id, row.sha256);
      dependencies.push(factory.provenance);
      if (id === 139209) {
        for (const operation of [
          "GET /competitions",
          "GET /competitions/{idOrSlug}",
        ])
          witnesses.push(
            factory.witness(
              exactlyOne(
                findNodes(
                  factory.node,
                  (node) =>
                    node.type === "ObjectProperty" &&
                    node.key?.value === operation,
                ),
                operation,
              ),
              `separate declared ${operation}; not executed`,
            ),
          );
      } else {
        const names = {
          779106: ["f"],
          92245: ["$", "m"],
          944410: ["useClientServerContract"],
          30181: ["K", "d"],
          96224: ["useApiClientsConfig"],
        }[id];
        for (const name of names)
          witnesses.push(
            factory.witness(
              sourceExport(factory, id, name),
              `original provider ${id}.${name}; explicit boundary`,
            ),
          );
        if (id === 30181)
          for (const node of findNodes(
            factory.node,
            (node) =>
              node.type === "VariableDeclarator" &&
              ["$", "M", "_"].includes(node.id?.name),
          ))
            witnesses.push(
              factory.witness(
                node,
                "actual contract HTTP constructor: configured clientServerUrl, credentials include, WEB headers; not reimplemented",
              ),
            );
      }
    }
  }
  const table = REVIEWED[85324]
    .map((hash, index) => `[${JSON.stringify(hash)},v${index}]`)
    .join(",");
  outputs.set(
    "client.mjs",
    await prettier.format(
      `${REVIEWED[85324].map((hash, index) => `import {createForegroundModule as v${index}} from './foreground/${hash.slice(0, 12)}.mjs';`).join("\n")}
import {createHook as createList} from './useList.mjs';import {createHook as createDetail} from './useDetail.mjs';import {keys} from './keys.mjs';import {selectCompetition,hasLiveCompetition} from './selection.mjs';
const variants=new Map([${table}]);export const foregroundVariants=Object.freeze(${JSON.stringify(REVIEWED[85324])});
export function createCompetitionClient({foregroundVariant,document,window,useSyncExternalStore,...providers}){const create=variants.get(foregroundVariant);if(!create)throw new TypeError('Explicit reviewed foreground source variant required');const foreground=create({document,window,useSyncExternalStore});const caps={...providers,keys,useForegroundInterval:foreground.useForegroundInterval};return {useList:createList(caps),useDetail:createDetail(caps),keys,selectCompetition,hasLiveCompetition,foreground};}`,
      { parser: "babel" },
    ),
  );
  const ids = [
    ...Object.keys(REVIEWED).map(Number),
    590407,
    869322,
    779106,
    92245,
    944410,
    30181,
    96224,
    139209,
  ];
  const selected = corpus.index.modules
    .filter((row) => row.ids.some((id) => ids.includes(id)))
    .sort((a, b) => a.sha256.localeCompare(b.sha256));
  const contract = {
    schemaVersion: 1,
    source: {
      reviewBase: "03bcf6a0b8162919a72b884869850abf342aa9d3",
      manifestSha256: corpus.anchors.manifestSha256,
      sharedSourceSha256: SHARED,
      selectedIndexEntries: selected,
      selectedCompleteEntriesSha256: sha256(JSON.stringify(selected)),
    },
    scope:
      "Original competition list/detail hook, complete foreground polling variants, cache keys and actual bucket-selection expressions. No server ranking, auth, mutations or mounted UI.",
    adapters,
    consumers,
    dependencies,
    capabilities: CAPS,
    witnesses: witnesses.sort(
      (a, b) => a.source.localeCompare(b.source) || a.utf16[0] - b.utf16[0],
    ),
    behavior: {
      list: {
        operation: "GET /competitions",
        staleTimeMs: 15000,
        foregroundPollMs: 60000,
      },
      detail: {
        operation: "GET /competitions/{idOrSlug}",
        staleTimeMs: 5000,
        foregroundPollMs: 15000,
        enabled:
          "Only literal null disables; params use idOrSlug??empty string. Disabled projection hides data/loading but retains error/refetch fields.",
      },
      selection:
        "First matching kind in live, then upcoming, then past. No sorting or PnL calculation.",
      polling:
        "useSyncExternalStore subscriptions preserve visibilitychange/focus/blur and exact numeric/truthiness behavior; server snapshots false. No timers implemented by original helper.",
      viewerScope:
        "779106.f consumes545063.U and92245.$, logs source attribution via effect; injected useViewerKey is client display/cache identity only, never authorization.",
      http: "944410.useClientServerContract reads96224 config and30181.K; actual constructor uses configured clientServerUrl, credentials include and WEB headers. Real contract decoding/retry/error/auth remain external capabilities.",
    },
    limits: [
      "Captured bundles/factories/schemas are parsed, never executed.",
      "Both physical85324 variants require explicit full SHA selection; active deployment winner unknown.",
      "961415 shares a factory with626540; unrelated group-portfolio export is not adapted.",
      "No private backend, original auth, response normalization, ranking, visual or production compatibility claim.",
    ],
  };
  return { outputs, contract };
}
export async function verifyCompetitionClient(appRoot = APP_ROOT) {
  const { outputs, contract } = await buildCompetitionClient(appRoot);
  for (const [name, expected] of outputs) {
    const actual = await readFile(path.join(appRoot, DIRECTORY, name), "utf8");
    assert.deepEqual(
      canonical(parse(actual, { sourceType: "module" })),
      canonical(parse(expected, { sourceType: "module" })),
      `maintained AST differs: ${name}`,
    );
    assert.equal(
      actual,
      expected,
      `maintained canonical bytes differ: ${name}`,
    );
  }
  assert.equal(
    await readFile(path.join(appRoot, DIRECTORY, "contract.json"), "utf8"),
    JSON.stringify(contract, null, 2) + "\n",
    "source contract differs",
  );
  return contract;
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  try {
    const [mode, ...rest] = process.argv.slice(2);
    assert.ok(
      !rest.length && ["--write", "--check"].includes(mode),
      "usage: --write | --check",
    );
    if (mode === "--write") {
      const { outputs, contract } = await buildCompetitionClient();
      for (const [name, text] of outputs) {
        const file = path.join(APP_ROOT, DIRECTORY, name);
        await mkdir(path.dirname(file), { recursive: true });
        await writeFile(file, text);
      }
      await writeFile(
        path.join(APP_ROOT, DIRECTORY, "contract.json"),
        JSON.stringify(contract, null, 2) + "\n",
      );
    } else await verifyCompetitionClient();
    console.log(
      "Original competition workflow verified without captured runtime execution.",
    );
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
