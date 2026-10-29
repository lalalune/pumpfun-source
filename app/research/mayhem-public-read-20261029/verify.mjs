import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { gunzipSync } from "node:zlib";
import { parse } from "@babel/parser";
import { parseFlightRecords } from "../../scripts/settings-client-contract.mjs";
import {
  openCorpus,
  findNodes,
  propertyName,
} from "../../scripts/original-contracts/source.mjs";
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");

function verifyMountedScreener(html) {
  const fragments = [];
  for (const match of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)) {
    if (!match[1].includes("__next_f")) continue;
    const ast = parse(match[1], { sourceType: "script" });
    for (const push of findNodes(
      ast,
      (node) =>
        node.type === "CallExpression" &&
        propertyName(node.callee?.property) === "push" &&
        node.arguments[0]?.type === "ArrayExpression" &&
        node.arguments[0].elements[0]?.value === 1 &&
        node.arguments[0].elements[1]?.type === "StringLiteral",
    )) {
      fragments.push(push.arguments[0].elements[1].value);
    }
  }
  const records = parseFlightRecords(fragments.join(""));
  const imported = records.get("103");
  assert.equal(imported?.kind, "import", "actual Flight import103");
  assert.equal(imported.value[0], 457065, "actual screener factory");
  assert.equal(imported.value[2], "MayhemScreener", "actual exported symbol");
  const uses = [];
  function visit(value, route) {
    if (!value || typeof value !== "object") return;
    if (Array.isArray(value) && value[0] === "$" && value[1] === "$L103")
      uses.push({ path: route, props: value[3] });
    for (const [key, child] of Object.entries(value))
      visit(child, [...route, key]);
  }
  for (const [id, record] of records) visit(record.value, [id]);
  assert.deepEqual(
    uses,
    [
      {
        path: ["7a", "1", "3", "children", "3", "3", "children", "1"],
        props: {},
      },
    ],
    "actual Flight element use",
  );
  return {
    importRecord: "103",
    factory: 457065,
    export: "MayhemScreener",
    uses,
  };
}

export async function deriveTrace(root) {
  const corpus = await openCorpus(root);
  const ids = [457065, 759257, 503630, 30181, 402030, 898661, 997887, 985722];
  const factories = {};
  for (const id of ids) {
    const factory = await corpus.factory(id);
    factories[id] = { factory, provenance: factory.provenance };
  }

  const htmlPath = "evidence/web/objects/0c1c38e553b5ee46";
  const html = await readFile(path.join(root, htmlPath));
  const record = corpus.manifest.records.filter(
    (record) => record.path === htmlPath,
  );
  if (
    record.length !== 1 ||
    record[0].status !== 200 ||
    record[0].bytes !== html.length ||
    record[0].sha256 !== hash(html)
  )
    throw Error("HTML provenance");
  verifyMountedScreener(html.toString("utf8"));
  const refs = [];
  for (const [label, text] of [
    ["chunk", "/_next/static/immutable/chunks/2mx4v0o-d4lqt.js"],
    ["RSC factory", "103:I[457065,"],
    ["rendered RSC reference", "$L103"],
    ["SSR heading", "Mayhem screener"],
  ]) {
    const needle = Buffer.from(text);
    const starts = [];
    let offset = 0;
    while ((offset = html.indexOf(needle, offset)) !== -1) {
      starts.push(offset);
      offset += needle.length;
    }
    if (!starts.length) throw Error(label + " absent");
    refs.push({
      label,
      text,
      ranges: starts.map((start) => ({
        utf8: [start, start + needle.length],
        sha256: hash(needle),
      })),
    });
  }
  const witness = (id, label, predicate) => {
    const f = factories[id].factory;
    const nodes = findNodes(f.node, predicate);
    if (nodes.length !== 1)
      throw Error(label + ": " + nodes.length + " selections");
    return f.witness(nodes[0], label);
  };
  const bindings = [
    witness(
      457065,
      "actual screener request C",
      (n) => n.type === "FunctionDeclaration" && n.id?.name === "C",
    ),
    witness(
      457065,
      "literal state mapping M",
      (n) =>
        n.type === "VariableDeclarator" &&
        n.id?.name === "M" &&
        n.init?.type === "ObjectExpression" &&
        n.init.properties.some((p) => propertyName(p.key) === "ended"),
    ),
    witness(759257, "j client constructor and options", (n, parents) => {
      const parent = parents.at(-1);
      if (
        n.type !== "ArrowFunctionExpression" ||
        parent?.type !== "ArrayExpression"
      )
        return false;
      const index = parent.elements.indexOf(n);
      return (
        parent.elements[index - 2]?.value === "j" &&
        parent.elements[index - 1]?.value === 0
      );
    }),
    witness(
      759257,
      "same-origin credentials",
      (n) => n.type === "VariableDeclarator" && n.id?.name === "s",
    ),
    witness(
      759257,
      "uninitialized optional internal-key branch",
      (n) => n.type === "VariableDeclarator" && n.id?.name === "i",
    ),
    witness(
      503630,
      "actual frontend origin R",
      (n) =>
        n.type === "StringLiteral" &&
        n.value === "https://frontend-api-v3.pump.fun",
    ),
    witness(
      985722,
      "declared GET mayhem query and array response",
      (n) =>
        n.type === "ObjectProperty" &&
        propertyName(n.key) === "GET /coins/mayhem-mode",
    ),
    witness(
      997887,
      "identity list normalizer",
      (n) => n.type === "VariableDeclarator" && n.id?.name === "s",
    ),
  ];
  const output = {
    main: "094a06f18df738d41e77070c1a009e135671ac1a",
    anchors: corpus.anchors,
    factories: Object.fromEntries(
      Object.entries(factories).map(([id, v]) => [id, v.provenance]),
    ),
    html: { record: record[0], refs },
    bindings,
    usedChain: [
      "SSR RSC103 ->457065.MayhemScreener",
      "queryFn ->C({state}) (initial all; limit default60)",
      "C ->759257.j()",
      "j ->503630.R() plus credentials:same-origin ->30181.K",
      "K ->402030.createContractClient forwarding898661.createContractClient",
      "898661 ->get coins/mayhem-mode; omit undefined mayhemState; query limit; JSON result",
      "C ->997887.l identity normalization",
    ],
    authBoundary: {
      credentials:
        "same-origin overrides base include; absolute frontend-api-v3 is cross-origin from pump.fun",
      usedBeforeRequest:
        "I is an empty function; M adds fixed x-pump-source WEB and x-pump-platform web",
      internalKey:
        "local t in i is uninitialized; false branch returns input options unchanged",
      caller:
        "No supplied fetchOptions, login predicate or enabled guard in this screener query path",
      limits:
        "This attributes the captured client request, not a promise that the current server admits anonymous callers.",
    },
    plannedRead: {
      url: "https://frontend-api-v3.pump.fun/coins/mayhem-mode?limit=1",
      method: "GET",
      queryNote:
        "limit1 is an explicitly permitted builder/query value, reducing the response; actual mounted initial query uses default60.",
      cookie: false,
      authorization: false,
      redirects: false,
      retries: 0,
    },
    limits: [
      "Original bundles parsed only, never executed.",
      "One origin per selected literal ID in maintained inventory; logical grouped-provider runtime is not inferred.",
      "No response-schema parser runs in C/898661; declaration differs from client enforcement.",
      "No website API/developer API/native reconstruction equivalence claim.",
    ],
  };
  return output;
}

export function verifyResponse(response, body, traceBytes, collectorBytes) {
  const url = "https://frontend-api-v3.pump.fun/coins/mayhem-mode?limit=1";
  assert.equal(response.requestedUrl, url, "request URL");
  assert.equal(response.responseUrl, url, "response URL/redirect boundary");
  assert.equal(response.method, "GET", "method");
  assert.deepEqual(
    response.requestHeaders,
    {
      Accept: "application/json",
      "X-Pump-Source": "WEB",
      "X-Pump-Platform": "web",
    },
    "fixed anonymous request headers",
  );
  assert.equal(response.redirectsAllowed, false, "redirect boundary");
  assert.equal(response.retries, 0, "retry boundary");
  assert.equal(response.cookiesSent, false, "cookie boundary");
  assert.equal(response.authorizationSent, false, "authorization boundary");
  assert.equal(response.status, 200, "observed HTTP status");
  assert.equal(response.truncated, false, "complete captured body");
  assert.equal(response.bodyPath, "body.bin", "body path");
  assert.equal(response.retainedBodyBytes, body.length, "body length");
  assert.equal(response.retainedBodySha256, hash(body), "body SHA-256");
  assert.equal(
    response.sourceTraceSha256,
    hash(traceBytes),
    "pre-request source trace SHA-256",
  );
  assert.equal(
    response.collectorSha256,
    hash(collectorBytes),
    "executed collector SHA-256",
  );
  assert.ok(
    Number.isFinite(Date.parse(response.startedAt)) &&
      Date.parse(response.finishedAt) >= Date.parse(response.startedAt),
    "acquisition time",
  );
  assert.ok(
    response.headers.every(
      ([name, value]) =>
        typeof name === "string" &&
        typeof value === "string" &&
        !/^set-cookie2?$/i.test(name),
    ),
    "cookie values stay omitted",
  );
  assert.ok(
    response.headers.some(
      ([name, value]) =>
        name.toLowerCase() === "content-type" &&
        value.toLowerCase().startsWith("application/json"),
    ),
    "observed JSON content type",
  );
  const data = JSON.parse(
    new TextDecoder("utf-8", { fatal: true }).decode(body),
  );
  assert.ok(
    Array.isArray(data) &&
      data.length === 1 &&
      data[0] &&
      typeof data[0] === "object" &&
      !Array.isArray(data[0]),
    "actual one-row response",
  );
  assert.deepEqual(
    response.jsonSummary,
    { type: "list", rows: 1, firstRowFields: Object.keys(data[0]).sort() },
    "observed fields",
  );
  return {
    bytes: body.length,
    sha256: hash(body),
    rows: data.length,
    fields: Object.keys(data[0]).sort(),
  };
}

export async function verifyPacket(
  appRoot,
  packet = new URL("./", import.meta.url),
) {
  const directory = packet instanceof URL ? fileURLToPath(packet) : packet;
  const load = async (name) => readFile(path.join(directory, name));
  const manifest = JSON.parse(await load("MANIFEST.json"));
  for (const entry of manifest.files) {
    assert.equal(path.basename(entry.path), entry.path, "packet-relative file");
    const bytes = await load(entry.path);
    assert.equal(bytes.length, entry.bytes, entry.path + " length");
    assert.equal(hash(bytes), entry.sha256, entry.path + " SHA-256");
    if (entry.rawSha256) {
      const raw = gunzipSync(bytes);
      assert.equal(raw.length, entry.rawBytes, entry.path + " raw length");
      assert.equal(hash(raw), entry.rawSha256, entry.path + " raw SHA-256");
    }
  }
  const [traceBytes, responseBytes, body, collector] = await Promise.all(
    ["SOURCE-TRACE.json", "RESPONSE.json", "body.bin", "capture.py"].map(load),
  );
  const trace = JSON.parse(traceBytes);
  assert.deepEqual(
    await deriveTrace(appRoot),
    trace,
    "actual source/dependency bindings",
  );
  const response = verifyResponse(
    JSON.parse(responseBytes),
    body,
    traceBytes,
    collector,
  );
  return {
    sourceFactories: Object.keys(trace.factories).length,
    sourceBindings: trace.bindings.length,
    response,
    networkRequests: 0,
  };
}

if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const args = process.argv.slice(2);
  assert.ok(
    args.length === 0 || (args.length === 2 && args[0] === "--app-root"),
    "Usage: node verify.mjs [--app-root <app directory>]",
  );
  const appRoot = args.length
    ? path.resolve(args[1])
    : fileURLToPath(new URL("../../", import.meta.url));
  console.log(JSON.stringify(await verifyPacket(appRoot), null, 2));
}
