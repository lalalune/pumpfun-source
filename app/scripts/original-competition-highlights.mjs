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
export const DIRECTORY = "reconstruction/competition-highlights";
const SHARED =
  "a7c04fdc74fb88a27d5cf24355396ee560d88ad4042abf3eb6a3c6874c5bacf2";
const PINS = {
  590407: ["3f494070c58a6d7f0f70279887ef648107935b765fe849de3e9ec100cec45dda"],
  639287: ["4ed887ef8ddc186c2058ae314de45a3a562884ca8f1579a9f5030dd2463d1f2b"],
  674801: ["3b0c8c5efdabd3970379bb077a54a2a63e66a3235f836d03535d77b5e51e65d9"],
  139209: ["8d4ffb7afbfae1b99df53cf4d8421f1fb6f85c290468471f2e4f71f58358ed9b"],
};
const HELPERS = ["eD", "eK", "eZ", "eB", "eQ", "eW", "eJ", "eG", "eH", "eX"];
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
function exported(factory, id, name) {
  const values = [];
  for (const call of findNodes(
    factory.node,
    (node) =>
      node.type === "CallExpression" &&
      member(node.callee, factory.runtime, "s") &&
      (node.arguments[1]?.value === id ||
        (!node.arguments[1] && factory.ids.length === 1)),
  )) {
    const entries = call.arguments[0].elements;
    for (let index = 0; index < entries.length; index += 3)
      if (entries[index].value === name) values.push(entries[index + 2]);
  }
  return exactlyOne(values, `actual export ${id}.${name}`);
}
export async function buildCompetitionHighlights(appRoot = APP_ROOT) {
  assert.equal(
    sha256(
      await readFile(
        path.join(appRoot, "scripts/original-contracts/source.mjs"),
      ),
    ),
    SHARED,
  );
  const corpus = await openCorpus(appRoot);
  const witnesses = [];
  for (const [id, hashes] of Object.entries(PINS))
    assert.deepEqual(
      corpus.index.modules
        .filter((row) => row.ids.includes(Number(id)))
        .map((row) => row.sha256)
        .sort(),
      hashes,
      `unreviewed variant set ${id}`,
    );
  async function factory(id) {
    const row = exactlyOne(
      corpus.index.modules.filter((row) => row.ids.includes(id)),
      `unique reviewed ${id}`,
    );
    return corpus.factory(id, { source: row.origins[0].source });
  }
  const source = await factory(590407);
  const declarations = source.node.body.body
    .filter((node) => node.type === "VariableDeclaration")
    .flatMap((node) => node.declarations);
  const retained = HELPERS.map((name) =>
    exactlyOne(
      declarations.filter((node) => node.id.name === name),
      `used helper ${name}`,
    ),
  );
  for (const node of retained)
    witnesses.push(
      source.witness(node, `actual used helper/state ${node.id.name}`),
    );
  const component = exactlyOne(
    declarations.filter((node) => node.id.name === "e3"),
    "actual Cup highlights component",
  );
  const workflow = exactlyOne(
    findNodes(
      component.init,
      (node) =>
        node.type === "ArrowFunctionExpression" &&
        node.params.length === 1 &&
        node.params[0].type === "ObjectPattern" &&
        node.params[0].properties.map((p) => p.key.name).join(",") ===
          "competitionId,entries",
    ),
    "complete used nested data workflow",
  );
  witnesses.push(
    source.witness(workflow, "complete actual carousel data workflow"),
  );
  const caller = exactlyOne(
    findNodes(
      component.init,
      (node) => node.type === "CallExpression" && node.callee === workflow,
    ),
    "actual workflow invocation",
  );
  witnesses.push(
    source.witness(
      caller,
      "actual e3 component invokes the retained data workflow",
    ),
  );
  for (const [name, id, property] of [
    ["eR", 944410, "useClientServerContract"],
    ["eT", 935258, "f"],
    ["eO", 674801, "S"],
    ["eV", 639287, "f"],
  ]) {
    const node = exactlyOne(
      declarations.filter((node) => node.id.name === name),
      `actual import ${id}`,
    );
    assert.ok(member(node.init?.callee, source.runtime, "i"));
    assert.equal(node.init.arguments[0].value, id);
    witnesses.push(source.witness(node, `used import ${id}.${property}`));
  }
  const chain = await factory(674801);
  const chainId = exported(chain, 674801, "S");
  assert.equal(chainId.type, "NumericLiteral");
  assert.equal(chainId.value, 0x536f6c4d);
  witnesses.push(
    chain.witness(
      chainId,
      "actual selected Solana chain ID; unrelated RPC functions not adapted",
    ),
  );
  const keys = await factory(639287);
  const object = exported(keys, 639287, "f");
  for (const name of ["highlights", "entry", "highlightMedia"]) {
    const node = exactlyOne(
      object.properties.filter((node) => node.key.name === name),
      `used key ${name}`,
    );
    witnesses.push(keys.witness(node, `injected original key ${name}`));
  }
  const routes = await factory(139209);
  for (const operation of [
    "GET /competitions/{id}/entries/{entryId}/highlights",
    "GET /competitions/{id}/entries/{entryId}",
  ])
    witnesses.push(
      routes.witness(
        exactlyOne(
          findNodes(
            routes.node,
            (node) =>
              node.type === "ObjectProperty" && node.key?.value === operation,
          ),
          operation,
        ),
        `separate declared ${operation}; not executed`,
      ),
    );
  const text = await prettier.format(
    `// Maintained source adaptation of the complete actual Cup highlight data flow.\n// No captured runtime, UI rendering, server scoring or media generation is executed.\nexport function createCompetitionHighlights({useClientServerContract,useQueries,keys,fetch,queueMicrotask}){const eR={useClientServerContract},eT={f:useQueries},eO={S:${chain.text(chainId)}},eV={f:keys};let ${retained.map((node) => source.text(node)).join(",")};const useHighlights=${source.text(workflow)};return {useHighlights};}`,
    { parser: "babel" },
  );
  const selected = corpus.index.modules
    .filter((row) => row.ids.some((id) => Object.hasOwn(PINS, id)))
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
    factory: source.provenance,
    dependencies: [chain.provenance, keys.provenance, routes.provenance],
    adapter: {
      path: "client.mjs",
      sha256: sha256(text),
      retainedAsts: [...retained, workflow].map((node) => ({
        type: node.type,
        sha256: sha256(JSON.stringify(canonical(node))),
      })),
    },
    witnesses: witnesses.sort(
      (a, b) => a.source.localeCompare(b.source) || a.utf16[0] - b.utf16[0],
    ),
    behavior: {
      reads: [
        "GET /competitions/{id}/entries/{entryId}/highlights",
        "GET /competitions/{id}/entries/{entryId}",
      ],
      highlightLimit: 10,
      personLimit: 10,
      groupLimit: 5,
      staleTimeMs: 60000,
      mediaPath: "/api/profiles/generated-media",
      mediaMethod: "POST",
      mediaBatchSize: 200,
      mediaStaleTimeMs: 1800000,
      mediaRetry: false,
      outputLimit: 10,
      pending:
        "isPending produces undefined; resolved missing/error data becomes null. Each person/group sequence stops before the first pending result.",
      projection:
        "Original client-only ranked-entry filtering, Solana/positive-PnL token choice,10-percent threshold, roster sort/member match, max2 per squad, thumbnail selection retained. Not server scoring.",
      media:
        "Deduplicate wallet queries, coalesce pending lookups in one module-local Map, reset before drain, chunk200, resolve missing keys null, reject only the failed batch and continue.",
      providerBoundary:
        "Contract/auth/query scheduling and relative fetch/microtask capabilities injected; no original backend/media renderer/visual compatibility.",
    },
    limits: [
      "Raw captured bundles and route declarations are parsed, never executed.",
      "Private original filenames/types and backend implementation are unknown.",
      "One constructed adapter represents one original module instance and its shared pending-media Map.",
      "No mounted component, registration/TOS, private auth, server ranking, media generation, production request or live financial operation.",
    ],
  };
  return { text, contract };
}
export async function verifyCompetitionHighlights(appRoot = APP_ROOT) {
  const { text, contract } = await buildCompetitionHighlights(appRoot);
  const actual = await readFile(
    path.join(appRoot, DIRECTORY, "client.mjs"),
    "utf8",
  );
  assert.deepEqual(
    canonical(parse(actual, { sourceType: "module" })),
    canonical(parse(text, { sourceType: "module" })),
    "maintained AST differs",
  );
  assert.equal(actual, text, "maintained canonical bytes differ");
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
      const { text, contract } = await buildCompetitionHighlights();
      await mkdir(path.join(APP_ROOT, DIRECTORY), { recursive: true });
      await writeFile(path.join(APP_ROOT, DIRECTORY, "client.mjs"), text);
      await writeFile(
        path.join(APP_ROOT, DIRECTORY, "contract.json"),
        JSON.stringify(contract, null, 2) + "\n",
      );
    } else await verifyCompetitionHighlights();
    console.log(
      "Original competition highlights workflow verified without captured runtime execution.",
    );
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
