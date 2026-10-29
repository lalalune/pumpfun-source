import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "@babel/parser";
import prettier from "prettier";
import { openCorpus, findNodes, exactlyOne, member, propertyName, sha256 } from "./original-contracts/source.mjs";

export const APP_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const DIRECTORY = "reconstruction/pnl-leaderboard-client";
export const ADAPTER_PATH = `${DIRECTORY}/client.mjs`;
export const CONTRACT_PATH = `${DIRECTORY}/contract.json`;
const SHARED_SOURCE_SHA256 = "a7c04fdc74fb88a27d5cf24355396ee560d88ad4042abf3eb6a3c6874c5bacf2";
const CLIENT_SOURCE = "evidence/web/objects/4fd6e792e7a336d9.js";
const CLIENT_SHA256 = "cec3cfd574ec5ecefe30bc96c8d3c5242ccaa83d7fa2056a7708ac557e7220b9";
const IMPORT_CAPABILITIES = {
  445242: ["c", "useMemoCache"],
  574472: ["F", "useWallet"],
  690877: ["useQuery", "useQuery"],
  759257: ["j", "createClient"],
};
const CONSUMERS = [
  ["evidence/web/objects/dd1b7e2a0ecbaed0.js", "80bc5bd7bf784ff392040b5157b0b51fd1e9e038179c66ce67b205b7041137da"],
  ["evidence/web/objects/bbad3cca63bc2aa5.js", "ac3ebd5b7d6f1227ac2defe6bdab4d173314d04315052350a509c8934aa02cae"],
];
const TAIL = (node) => node.type === "SequenceExpression" ? node.expressions.at(-1) : node;

function exportsOf(factory) {
  const output = new Map();
  for (const call of findNodes(factory.node, (node) => node.type === "CallExpression" && member(node.callee, factory.runtime, "s"))) {
    assert.equal(call.arguments[0].type, "ArrayExpression");
    assert.ok(factory.ids.includes(call.arguments[1].value));
    const entries = call.arguments[0].elements;
    for (let i = 0; i < entries.length; i += 3) {
      assert.equal(entries[i].type, "StringLiteral");
      assert.equal(entries[i + 1].value, 0);
      const key = `${call.arguments[1].value}.${entries[i].value}`;
      assert.ok(!output.has(key));
      output.set(key, entries[i + 2]);
    }
  }
  assert.deepEqual([...output.keys()].sort(), ["416287.n", "416287.y", "864024.f"]);
  return output;
}

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(Object.entries(value).filter(([key]) => ![
    "start", "end", "loc", "extra", "comments", "leadingComments", "trailingComments", "innerComments",
  ].includes(key)).map(([key, entry]) => [key, canonical(entry)]));
}

async function physicalFactory(corpus, id, source, expectedHash) {
  const factory = await corpus.factory(id, { source });
  assert.equal(factory.provenance.sha256, expectedHash, `unreviewed physical factory ${id}`);
  assert.equal(factory.capture.factories.filter((entry) => entry.ids.includes(id)).length, 1, `ambiguous physical factory ${id}`);
  return factory;
}

function publicExport(factory, id, name) {
  const values = [];
  for (const call of findNodes(factory.node, (node) => node.type === "CallExpression" && member(node.callee, factory.runtime, "s") &&
    (node.arguments[1]?.value === id || (!node.arguments[1] && factory.ids.length === 1 && factory.id === id)))) {
    const entries = call.arguments[0].elements;
    for (let i = 0; i < entries.length; i += 3) {
      assert.equal(entries[i + 1].value, 0);
      if (entries[i].value === name) values.push(entries[i + 2]);
    }
  }
  return exactlyOne(values, `source export ${id}.${name}`);
}

export async function buildPnlLeaderboardClient(appRoot = APP_ROOT) {
  assert.equal(sha256(await readFile(path.join(appRoot, "scripts/original-contracts/source.mjs"))), SHARED_SOURCE_SHA256);
  const corpus = await openCorpus(appRoot);
  const factory = await physicalFactory(corpus, 864024, CLIENT_SOURCE, CLIENT_SHA256);
  assert.deepEqual(factory.node.body.body.map((node) => node.type), ["VariableDeclaration", "FunctionDeclaration", "ExpressionStatement"]);
  const imports = factory.node.body.body[0];
  assert.equal(imports.kind, "var");
  assert.equal(imports.declarations.length, 4);
  const capabilities = [];
  for (const declaration of imports.declarations) {
    assert.equal(declaration.id.type, "Identifier");
    assert.ok(member(declaration.init.callee, factory.runtime, "i"));
    const id = declaration.init.arguments[0].value;
    assert.ok(IMPORT_CAPABILITIES[id]);
    const [property, capability] = IMPORT_CAPABILITIES[id];
    capabilities.push({ id, binding: declaration.id.name, property, capability, witness: factory.witness(declaration, `original import ${id}`) });
  }
  assert.deepEqual(capabilities.map((entry) => entry.id).sort((a, b) => a - b), Object.keys(IMPORT_CAPABILITIES).map(Number).sort((a, b) => a - b));
  const originalExports = exportsOf(factory);
  const request = factory.node.body.body[1];
  assert.equal(request.async, true);
  assert.equal(originalExports.get("416287.y").name, request.id.name);
  const score = originalExports.get("416287.n");
  const hook = originalExports.get("864024.f");
  assert.equal(score.type, "ArrowFunctionExpression");
  assert.equal(hook.type, "ArrowFunctionExpression");
  const memo = exactlyOne(findNodes(hook, (node) => node.type === "CallExpression" && member(TAIL(node.callee), "t", "c")), "actual memo-cache call");
  assert.equal(memo.arguments[0].value, 19);
  const actualClient = exactlyOne(findNodes(request, (node) => node.type === "CallExpression" && node.arguments[0]?.value === "GET /pnl-leaderboard"), "actual leaderboard client request");
  const queryConsumer = exactlyOne(findNodes(hook, (node) => node.type === "CallExpression" && propertyName(TAIL(node.callee).property) === "useQuery"), "actual query consumer");
  const retained = [request, score, hook];
  const substitutions = capabilities.map(({ binding, property, capability }) => `${binding}={${JSON.stringify(property)}:${capability}}`).join(",");
  const adapter = await prettier.format(`// Source-derived maintained adapter. Captured runtime imports/exports are replaced by explicit capabilities.\nexport function createPnlLeaderboardClient({useMemoCache,useWallet,useQuery,createClient}){var ${substitutions};${factory.text(request)}return {request:${request.id.name},score:${factory.text(score)},useLeaderboard:${factory.text(hook)}};}`, { parser: "babel" });
  const witnesses = [
    factory.witness(request, "retained whole request function"), factory.witness(score, "retained whole raw-score selector"),
    factory.witness(hook, "retained whole memo/query/cache hook"), factory.witness(actualClient, "used client request and afterResponse error policy"),
    factory.witness(memo, "actual nineteen-slot memo capability"), factory.witness(queryConsumer, "actual useQuery options consumer"),
  ];
  const consumers = [];
  for (const [source, expectedHash] of CONSUMERS) {
    const consumer = await physicalFactory(corpus, 996005, source, expectedHash);
    const bindings = new Map();
    for (const node of findNodes(consumer.node, (node) => node.type === "VariableDeclarator" &&
      node.init?.type === "CallExpression" && member(node.init.callee, consumer.runtime, "i") && [864024, 416287].includes(node.init.arguments[0]?.value))) {
      bindings.set(node.init.arguments[0].value, node.id.name);
      witnesses.push(consumer.witness(node, `consumer ${consumer.provenance.sha256.slice(0, 12)} imports ${node.init.arguments[0].value}`));
    }
    for (const [id, name] of [[864024, "f"], [416287, "n"]]) {
      const calls = findNodes(consumer.node, (node) => node.type === "CallExpression" && member(TAIL(node.callee), bindings.get(id), name));
      assert.ok(calls.length > 0, `missing used consumer ${id}.${name}`);
      for (const call of calls) witnesses.push(consumer.witness(call, `used consumer call ${id}.${name}`));
    }
    consumers.push(consumer.provenance);
  }
  const transport = await physicalFactory(corpus, 759257, "evidence/web/objects/1e479323ffe53c14.js", "e1c207697339004b48f6baa9f81f34e7644686ee424616b553e55b23c659b855");
  const origin = await physicalFactory(corpus, 503630, "evidence/web/objects/1e479323ffe53c14.js", "df5a12d4b76158889dd38a02d0d9afc0d0405065772b589c9cadf9806422d0e7");
  const clientFactory = publicExport(transport, 759257, "j");
  const base = publicExport(origin, 503630, "R");
  assert.equal(base.body.type, "StringLiteral");
  const originBinding = exactlyOne(findNodes(transport.node, (node) => node.type === "VariableDeclarator" && node.init?.type === "CallExpression" && member(node.init.callee, transport.runtime, "i") && node.init.arguments[0]?.value === 503630), "transport origin import");
  assert.equal(findNodes(clientFactory, (node) => node.type === "CallExpression" && member(TAIL(node.callee), originBinding.id.name, "R")).length, 1);
  witnesses.push(transport.witness(clientFactory, "actual 759257.j client factory and origin configuration"), origin.witness(base, "captured website frontend-api origin"));
  const declaration = await physicalFactory(corpus, 154263, "evidence/web/objects/2b47dd0b38a1608f.js", "cd01bde47e65d8950932e98d4dc853a8e18e53e527de909f905b5caf1b4fc878");
  const route = exactlyOne(findNodes(declaration.node, (node) => node.type === "ObjectProperty" && node.key?.type === "StringLiteral" && node.key.value === "GET /pnl-leaderboard"), "declared leaderboard route");
  witnesses.push(declaration.witness(route, "declared query/response contract, not invoked by the retained client"));
  const selectedIds = [864024, 416287, 996005, 759257, 503630, 154263];
  const selected = corpus.index.modules.filter((module) => module.ids.some((id) => selectedIds.includes(id))).sort((a, b) => a.sha256.localeCompare(b.sha256));
  const expectedVariants = new Map([
    [864024, [CLIENT_SHA256]], [416287, [CLIENT_SHA256]],
    [996005, CONSUMERS.map(([, hash]) => hash)],
    [759257, [transport.provenance.sha256]],
    [503630, [origin.provenance.sha256]],
    [154263, [declaration.provenance.sha256]],
  ]);
  for (const [id, hashes] of expectedVariants) {
    assert.deepEqual(selected.filter((module) => module.ids.includes(id)).map((module) => module.sha256).sort(),
      [...hashes].sort(), `unreviewed captured variant set for ${id}`);
  }
  const contract = {
    schemaVersion: 1,
    source: { repository: "lalalune/pumpfun-source", reviewBase: "c571e162500ee6a72a3cc942eb9dca1f4c825931",
      manifestSha256: corpus.anchors.manifestSha256, selectedCompleteEntriesSha256: sha256(JSON.stringify(selected)),
      selectedIndexEntries: selected,
      sharedSource: { revision: "0a9a1f084", sha256: SHARED_SOURCE_SHA256 } },
    scope: "Original PnL request, raw-score selector and complete memo/query/cache hook through explicit capabilities; no server rankings or API qualification",
    factory: factory.provenance, consumers,
    dependencies: [transport.provenance, origin.provenance, declaration.provenance],
    adapter: { path: ADAPTER_PATH, sha256: sha256(adapter), rewrite: "replace only four runtime import bindings and export registration; retain complete request, score and hook ASTs",
      retainedAsts: retained.map((node) => ({ type: node.type, sha256: sha256(JSON.stringify(canonical(node))) })) },
    capabilities,
    behavior: { operation: "GET /pnl-leaderboard", capturedWebsiteOrigin: base.body.value, query: ["period", "sort", "limit"], credentials: "include",
      contentType: "application/json", nonOkResponse: "plain Error('Failed to fetch pnl leaderboard: '+response.status)",
      response: "injected contract client's result is returned unchanged; no response schema parser is added",
      memoSlots: 19, staleTimeMs: 60000, enabledDefault: "true when enabled is undefined; otherwise the supplied value is retained", refetchDefault: "false when refetchIntervalMs is null or undefined",
      viewerKey: "address?.toLowerCase() ?? null; a cache partition, not authenticated identity",
      queryKey: ["pnl-leaderboard", "board", "period", "sort", "limit", "viewerKey"],
      placeholder: "falsy prior data -> undefined; matching previous query-key tail -> original data; otherwise shallow copy with own viewer:undefined and entry copies deleting isViewer/viewerFollows",
      score: "realized -> realizedPnlUsd; unrealized -> unrealizedPnlUsd; otherwise pnlUsd; no coercion or sorting" },
    witnesses: witnesses.sort((a, b) => a.source.localeCompare(b.source) || a.utf16[0] - b.utf16[0]),
    limits: ["Captured JavaScript is parsed only, never evaluated.", "Consumer variants are retained explicitly without an active runtime winner claim.",
      "React/compiler cache and query scheduling, wallet authority and HTTP transport remain caller-provided capabilities.",
      "No PnL/rank calculation, backend endpoint, full response DTO recovery, native cookie/auth claim or feature credit."] };
  return { contract, adapter };
}

export async function verifyPnlLeaderboardClient(appRoot = APP_ROOT) {
  const { contract, adapter } = await buildPnlLeaderboardClient(appRoot);
  const actual = await readFile(path.join(appRoot, ADAPTER_PATH), "utf8");
  assert.deepEqual(canonical(parse(actual, { sourceType: "module" })), canonical(parse(adapter, { sourceType: "module" })), "maintained whole-module AST differs from the captured-source adaptation");
  assert.equal(actual, adapter, "canonical adapter bytes differ");
  assert.equal(await readFile(path.join(appRoot, CONTRACT_PATH), "utf8"), JSON.stringify(contract, null, 2) + "\n", "source contract differs");
  return contract;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const [mode, ...args] = process.argv.slice(2);
    if (args.length || !["--write", "--check"].includes(mode)) throw new Error("usage: --write | --check");
    if (mode === "--write") {
      const { contract, adapter } = await buildPnlLeaderboardClient();
      await mkdir(path.join(APP_ROOT, DIRECTORY), { recursive: true });
      await writeFile(path.join(APP_ROOT, ADAPTER_PATH), adapter);
      await writeFile(path.join(APP_ROOT, CONTRACT_PATH), JSON.stringify(contract, null, 2) + "\n");
    } else await verifyPnlLeaderboardClient();
    console.log("Original PnL client source adaptation verified; captured runtime was not executed.");
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
