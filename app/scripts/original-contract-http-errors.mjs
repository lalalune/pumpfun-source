import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  member,
  propertyName,
  sha256,
} from "./original-contracts/source.mjs";

export const APP_ROOT = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
);
export const CONTRACT_PATH =
  "reconstruction/contract-http-errors/contract.json";
export const COMPATIBILITY_PATH =
  "reconstruction/contract-http-errors/inventory-compatibility.json";
const SHARED_SOURCE_SHA256 =
  "a7c04fdc74fb88a27d5cf24355396ee560d88ad4042abf3eb6a3c6874c5bacf2";
const SOURCE = "evidence/web/objects/2b47dd0b38a1608f.js";
const EXPECTED = {
  898661: [
    SOURCE,
    "9015e4bad4b1f0bb4b245e446689d9b7e939b3ba922044c82dcd9e8d5f3d9ed5",
  ],
  858694: [
    SOURCE,
    "56476450549b4d9af22752fd35511718268d35e138164681cb7cf074450daebd",
  ],
  525364: [
    SOURCE,
    "b1aa4e878a8f48acf01f6bfe2937cddd913661b13678800dbf4604440c6dce61",
  ],
  233815: [
    SOURCE,
    "2d021d5c19976c45e01f3f6ce8f5c700449b9888f22bfdeefa93d84e969f8453",
  ],
  4171: [
    SOURCE,
    "397c5cc81cd2521928a51795f93ac65fc8e8b0c9e71977503eeb7b1092c8336e",
  ],
  402030: [
    SOURCE,
    "26d7d7ced2e06fee3c9354e5ffd9626bcf4f953c8927d3a5ea43d5a45e7064c2",
  ],
  30181: [
    "evidence/web/objects/01ad4f413e529b60.js",
    "fbae4e508e6c986c68209d975d3eea247718d478272089a60504b776074e2413",
  ],
  864024: [
    "evidence/web/objects/4fd6e792e7a336d9.js",
    "cec3cfd574ec5ecefe30bc96c8d3c5242ccaa83d7fa2056a7708ac557e7220b9",
  ],
};
const IDS = Object.keys(EXPECTED).map(Number);
function selectedEntries(index) {
  return index.modules
    .filter((module) => module.ids.some((id) => IDS.includes(id)))
    .sort((a, b) => a.sha256.localeCompare(b.sha256));
}
function declaration(factory, name) {
  return exactlyOne(
    factory.node.body.body
      .flatMap((node) =>
        node.type === "VariableDeclaration" ? node.declarations : [],
      )
      .filter((node) => node.id?.name === name),
    `declaration ${factory.id}.${name}`,
  ).init;
}
function exportedAssignment(factory, name, predicate = () => true) {
  return exactlyOne(
    findNodes(
      factory.node,
      (node) =>
        node.type === "AssignmentExpression" &&
        node.left.type === "MemberExpression" &&
        node.left.object?.name === factory.node.params[2]?.name &&
        propertyName(node.left.property) === name &&
        predicate(node.right),
    ),
    `export ${factory.id}.${name}`,
  );
}
function calledProperty(node, name) {
  if (node.type !== "CallExpression") return false;
  const callee =
    node.callee.type === "SequenceExpression"
      ? node.callee.expressions.at(-1)
      : node.callee;
  return (
    callee.type === "MemberExpression" && propertyName(callee.property) === name
  );
}

export async function buildContractHttpErrors(appRoot = APP_ROOT) {
  const helper = await readFile(
    path.join(appRoot, "scripts/original-contracts/source.mjs"),
  );
  assert.equal(
    sha256(helper),
    SHARED_SOURCE_SHA256,
    "shared source authenticator changed; review its revision",
  );
  const corpus = await openCorpus(appRoot);
  const factories = new Map();
  const witnesses = [];
  const imports = [];
  const witness = (factory, node, label) => {
    const value = factory.witness(node, label);
    witnesses.push(value);
    return value;
  };
  for (const id of IDS) {
    const [source, expected] = EXPECTED[id];
    const factory = await corpus.factory(id, { source });
    assert.equal(
      factory.provenance.sha256,
      expected,
      `unreviewed factory ${id}`,
    );
    // The physical capture is authoritative even if a contender is missing
    // from an earlier inventory. No global numeric-ID default is selected.
    assert.equal(
      factory.capture.factories.filter((entry) => entry.ids.includes(id))
        .length,
      1,
      `ambiguous physical context for ${id}`,
    );
    factories.set(id, factory);
    for (const call of findNodes(
      factory.node,
      (node) =>
        node.type === "CallExpression" &&
        ["i", "r"].some((kind) => member(node.callee, factory.runtime, kind)) &&
        node.arguments[0]?.type === "NumericLiteral",
    )) {
      if (IDS.includes(call.arguments[0].value))
        imports.push({
          from: id,
          to: call.arguments[0].value,
          kind: propertyName(call.callee.property),
          ...factory.witness(
            call,
            `actual import ${id} -> ${call.arguments[0].value}`,
          ),
        });
    }
  }
  const encoder = factories.get(898661);
  const normalizer = declaration(encoder, "c");
  assert.equal(normalizer.type, "ArrowFunctionExpression");
  assert.equal(normalizer.async, true);
  assert.equal(normalizer.params.length, 2);
  witness(
    encoder,
    normalizer,
    "HTTP-error shape/body/schema/construction normalizer",
  );
  const errorConstruction = exactlyOne(
    findNodes(
      normalizer,
      (node) =>
        node.type === "NewExpression" &&
        node.callee.type === "MemberExpression" &&
        propertyName(node.callee.property) === "ContractError",
    ),
    "actual ContractError construction",
  );
  assert.equal(errorConstruction.arguments.length, 6);
  const choice = errorConstruction.arguments[3];
  assert.equal(choice.type, "ConditionalExpression");
  assert.equal(choice.alternate.type, "ConditionalExpression");
  assert.equal(
    propertyName(choice.alternate.alternate.properties[0].key),
    "statusCode",
  );
  witness(
    encoder,
    errorConstruction,
    "declared -> generic -> status-only data precedence",
  );
  const client = exportedAssignment(
    encoder,
    "createContractClient",
    (node) => node.type === "ArrowFunctionExpression",
  );
  const catchNode = exactlyOne(
    findNodes(client, (node) => node.type === "CatchClause"),
    "request catch",
  );
  const thrown = catchNode.body.body[0].argument;
  assert.equal(thrown.type, "LogicalExpression");
  assert.equal(thrown.operator, "??");
  assert.equal(thrown.left.type, "AwaitExpression");
  assert.equal(thrown.left.argument.callee.name, "c");
  witness(
    encoder,
    catchNode,
    "actual request catch wraps HTTP errors and preserves other throws",
  );

  const errorClass = factories.get(858694);
  witness(
    errorClass,
    exactlyOne(
      findNodes(
        errorClass.node,
        (node) =>
          node.type === "ClassDeclaration" && node.superClass?.name === "Error",
      ),
      "ContractError class",
    ),
    "ContractError fields/message/cause/status predicate",
  );
  witness(
    errorClass,
    exportedAssignment(
      errorClass,
      "isContractError",
      (node) => node.type === "ArrowFunctionExpression",
    ),
    "instanceof and optional exact-route predicate",
  );
  const codes = factories.get(525364);
  const pattern = exportedAssignment(
    codes,
    "ERROR_CODE_PATTERN",
    (node) => node.type === "RegExpLiteral",
  );
  assert.equal(pattern.right.pattern, "^[A-Z][A-Z0-9_]+$");
  assert.equal(pattern.right.flags, "");
  witness(
    codes,
    pattern,
    "domain code pattern, independent of registry membership",
  );
  witness(
    codes,
    exportedAssignment(
      codes,
      "domainCode",
      (node) => node.type === "ArrowFunctionExpression",
    ),
    "domain code extraction from raw error field",
  );
  for (const [id, name] of [
    [233815, "routeErrorSchema"],
    [4171, "contractErrorBody"],
  ]) {
    const factory = factories.get(id);
    witness(
      factory,
      exportedAssignment(
        factory,
        name,
        (node) =>
          node.type !== "UnaryExpression" &&
          node.type !== "AssignmentExpression",
      ),
      `schema dependency ${name}; implementation remains injected`,
    );
  }
  const http = factories.get(30181);
  const constructor = exactlyOne(
    findNodes(http.node, (node) =>
      calledProperty(node, "createContractClient"),
    ),
    "HTTP client constructor",
  );
  witness(http, constructor, "used HTTP constructor invokes contract client");
  const bridge = factories.get(402030);
  witness(
    bridge,
    exactlyOne(
      findNodes(
        bridge.node,
        (node) =>
          node.type === "CallExpression" &&
          member(node.callee, "Object", "defineProperty") &&
          node.arguments[1]?.value === "createContractClient",
      ),
      "contract client reexport",
    ),
    "contract barrel reexports real encoder",
  );
  const pnl = factories.get(864024);
  witness(
    pnl,
    exactlyOne(
      findNodes(pnl.node, (node) => node.type === "ThrowStatement"),
      "plain afterResponse hook error",
    ),
    "plain PnL hook error has no response and bypasses normalizer",
  );

  return {
    schemaVersion: 1,
    source: {
      repository: "lalalune/pumpfun-source",
      reviewBase: "f77117ea8827f2ff4a497a2a5360deba8608aeca",
      manifestSha256: corpus.anchors.manifestSha256,
      selectedInventoryEntriesSha256: sha256(
        JSON.stringify(selectedEntries(corpus.index)),
      ),
      sharedSource: {
        revision: "0a9a1f084",
        sha256: SHARED_SOURCE_SHA256,
        attribution:
          "shared source authenticator from the original-search recovery",
      },
    },
    scope:
      "Captured HTTP-error normalizer and error object semantics; explicit schema dependencies; no endpoint or backend compatibility claim",
    factories: [...factories.values()]
      .map((factory) => factory.provenance)
      .sort((a, b) => a.id - b.id),
    imports: imports.sort((a, b) => a.from - b.from || a.to - b.to),
    behavior: {
      guard:
        "non-null object error.response with numeric status and callable text; otherwise undefined",
      body: "read response.text once; JSON.parse success retains any JSON value, parse failure retains text, read failure yields undefined",
      schemaOrder: [
        "known route's status schema when present and not true",
        "generic contractErrorBody, even after declared success",
      ],
      dataPrecedence: [
        "declared safeParse success data",
        "generic safeParse success data",
        "{statusCode:response.status}",
      ],
      serverMessage:
        "raw message string, or raw array filtered to strings and joined with '; '; otherwise undefined",
      domainCodePattern: {
        source: pattern.right.pattern,
        flags: pattern.right.flags,
      },
      domainCodeRegistryLookup: false,
      cause: "original thrown error, distinct from any body-read rejection",
      requestCatch: "throw (await normalize(route,error)) ?? error",
      schemaImplementations:
        "explicit injected contracts, routeErrorSchema and contractErrorBody; no Zod approximation",
    },
    witnesses: witnesses.sort(
      (a, b) => a.source.localeCompare(b.source) || a.utf16[0] - b.utf16[0],
    ),
    limits: [
      "Captured JavaScript is parsed only, never evaluated.",
      "Static imports show source edges, not a complete runtime loading context or active global-ID winner.",
      "Route-schema generation, Zod parsing/projection, Ky retries, headers, auth and endpoint behavior are not implemented here.",
      "The maintained adapter uses independently written code and native response.text/JSON semantics; stack traces/source names are not original.",
      "No completion or API qualification count changes.",
    ],
  };
}

export async function verifyContractHttpErrors(appRoot = APP_ROOT) {
  const expected =
    JSON.stringify(await buildContractHttpErrors(appRoot), null, 2) + "\n";
  assert.equal(
    await readFile(path.join(appRoot, CONTRACT_PATH), "utf8"),
    expected,
    "HTTP error contract differs from authenticated captured source",
  );
  const compatibility = JSON.parse(
    await readFile(path.join(appRoot, COMPATIBILITY_PATH), "utf8"),
  );
  assert.equal(compatibility.completeEntriesEqual, true);
  assert.deepEqual(compatibility.selectedIds, IDS);
  assert.equal(
    compatibility.selectedEntriesSha256,
    JSON.parse(expected).source.selectedInventoryEntriesSha256,
    "inventory compatibility witness no longer binds the selected complete entries",
  );
  return JSON.parse(expected);
}

export async function compareInventory(expandedPath, appRoot = APP_ROOT) {
  const currentBytes = await readFile(
    path.join(appRoot, "recovered/modules.json"),
  );
  const expandedBytes = await readFile(expandedPath);
  const current = JSON.parse(currentBytes);
  const expanded = JSON.parse(expandedBytes);
  assert.deepEqual(
    selectedEntries(current),
    selectedEntries(expanded),
    "selected complete inventory entries changed",
  );
  return {
    schemaVersion: 1,
    purpose:
      "selected complete-entry compatibility witness; no dependence on unrelated global inventory entries",
    selectedIds: IDS,
    selectedEntriesSha256: sha256(JSON.stringify(selectedEntries(current))),
    maintained: {
      variants: current.modules.length,
      sha256: sha256(currentBytes),
    },
    expanded: {
      variants: expanded.modules.length,
      sha256: sha256(expandedBytes),
      source:
        "PR679 source/index commit7b52e2cfb780e246fe98c656122d95be769e17a3",
    },
    completeEntriesEqual: true,
  };
}

if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  try {
    const [mode, ...args] = process.argv.slice(2);
    if (mode === "--compare-inventory" && args.length === 1) {
      await mkdir(path.dirname(path.join(APP_ROOT, COMPATIBILITY_PATH)), {
        recursive: true,
      });
      await writeFile(
        path.join(APP_ROOT, COMPATIBILITY_PATH),
        JSON.stringify(await compareInventory(args[0]), null, 2) + "\n",
      );
    } else if (mode === "--write" && !args.length) {
      await mkdir(path.dirname(path.join(APP_ROOT, CONTRACT_PATH)), {
        recursive: true,
      });
      await writeFile(
        path.join(APP_ROOT, CONTRACT_PATH),
        JSON.stringify(await buildContractHttpErrors(), null, 2) + "\n",
      );
    } else if (mode === "--check" && !args.length)
      await verifyContractHttpErrors();
    else
      throw new Error(
        "usage: --write | --check | --compare-inventory <expanded modules.json>",
      );
    console.log(
      "Original HTTP-error contract verified; captured JavaScript was not executed.",
    );
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
