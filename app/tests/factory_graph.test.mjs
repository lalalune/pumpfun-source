import { createTestSymlink } from './helpers/test-symlink.mjs';
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import {
  mkdtemp,
  mkdir,
  readFile,
  rm,
  writeFile,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import prettier from "prettier";
import {
  analyzeFactory,
  buildGraph,
  countSourceLines,
  publishGraph,
  verifyGraph,
} from "../scripts/factory-graph/core.mjs";

const hash = (value) => createHash("sha256").update(value).digest("hex");

async function fixture({
  corruptHash = false,
  corruptRange = false,
  duplicateOrigin = false,
  reverse = false,
} = {}) {
  const root = await mkdtemp(join(tmpdir(), "factory-graph-"));
  for (const path of ["recovered/modules", "evidence/web/objects", "contracts"])
    await mkdir(join(root, path), { recursive: true });
  const factories = [
    {
      id: 1,
      raw: `(e)=>{var t=e.i(2);e.A(3);e.i(99);e.i("react");e.s(["answer",0,t],1)}`,
    },
    { id: 2, raw: `(e)=>{e.s(["value",0,42],2)}` },
    { id: 2, raw: `(e)=>{e.s(["value",0,43],2)}` },
    { id: 3, raw: `(e)=>{e.i(3);e.s(["cycle",0,true],3)}` },
  ];
  const source = `globalThis.TURBOPACK=[${factories.map((item) => item.raw).join(",")}];`;
  const jsPath = "evidence/web/objects/source.js";
  await writeFile(join(root, jsPath), source);
  const duplicateFactory = factories.at(-1);
  const otherSource = `globalThis.TURBOPACK=[${duplicateFactory.raw}];`;
  const otherPath = "evidence/web/objects/other.js";
  if (duplicateOrigin) await writeFile(join(root, otherPath), otherSource);
  const html = `<html><script src="/_next/static/chunks/source.js"></script></html>`;
  const htmlPath = "evidence/web/objects/home.html";
  await writeFile(join(root, htmlPath), html);
  const modules = [];
  for (const item of factories) {
    const start = source.indexOf(item.raw);
    const digest = hash(item.raw);
    const path = `recovered/modules/${item.id}-${digest.slice(0, 12)}.js`;
    await writeFile(
      join(root, path),
      "// Recovered Turbopack factory. Requires original runtime/import IDs; not a standalone source module.\n" +
        (await prettier.format(`(${item.raw});`, { parser: "babel" })),
    );
    modules.push({
      ids: [item.id],
      sha256: digest,
      origins: [
        {
          source: jsPath,
          url: "https://pump.fun/_next/static/chunks/source.js",
          start,
          end: start + item.raw.length,
        },
      ],
      path,
    });
  }
  if (duplicateOrigin) {
    const duplicateModule = modules.find(
      (module) => module.sha256 === hash(duplicateFactory.raw),
    );
    const start = otherSource.indexOf(duplicateFactory.raw);
    duplicateModule.origins.push({
      source: otherPath,
      url: "https://pump.fun/_next/static/chunks/other.js",
      start,
      end: start + duplicateFactory.raw.length,
    });
  }
  if (reverse) modules.reverse();
  if (corruptRange) modules[0].origins[0].end -= 1;
  const manifest = {
    records: [
      {
        url: "https://pump.fun/_next/static/chunks/source.js",
        final_url: "https://pump.fun/_next/static/chunks/source.js",
        status: 200,
        path: jsPath,
        bytes: Buffer.byteLength(source),
        sha256: corruptHash ? "0".repeat(64) : hash(source),
        headers: { "content-type": "application/javascript" },
      },
      ...(duplicateOrigin
        ? [
            {
              url: "https://pump.fun/_next/static/chunks/other.js",
              final_url: "https://pump.fun/_next/static/chunks/other.js",
              status: 200,
              path: otherPath,
              bytes: Buffer.byteLength(otherSource),
              sha256: hash(otherSource),
              headers: { "content-type": "application/javascript" },
            },
          ]
        : []),
      {
        url: "https://pump.fun/",
        final_url: "https://pump.fun/",
        status: 200,
        path: htmlPath,
        bytes: Buffer.byteLength(html),
        sha256: hash(html),
        headers: { "content-type": "text/html; charset=utf-8" },
      },
    ],
  };
  await writeFile(
    join(root, "recovered/modules.json"),
    JSON.stringify({
      rangeEncoding:
        "UTF-16 code-unit half-open offsets in UTF-8 decoded source",
      modules,
      failures: [],
    }),
  );
  await writeFile(
    join(root, "evidence/web/manifest.json"),
    JSON.stringify(manifest),
  );
  await writeFile(
    join(root, "contracts/internal-operations.json"),
    JSON.stringify({ operations: [] }),
  );
  await writeFile(
    join(root, "contracts/developer-bindings.json"),
    JSON.stringify({ bindings: [] }),
  );
  return root;
}

async function recoveredPath(root, id) {
  const index = JSON.parse(
    await readFile(join(root, "recovered/modules.json"), "utf8"),
  );
  return join(
    root,
    index.modules.find((module) => module.ids.includes(id)).path,
  );
}

async function completeFixtureOptions(root, routes = ["/"]) {
  const index = JSON.parse(
    await readFile(join(root, "recovered/modules.json"), "utf8"),
  );
  let targetLines = 0;
  for (const module of index.modules)
    targetLines += countSourceLines(
      await readFile(join(root, module.path), "utf8"),
    );
  return { routes, targetLines, maximumLines: 100 };
}

test("line census excludes recovery banners, blanks, and comment-only lines", () => {
  assert.equal(
    countSourceLines(
      "// Recovered Turbopack factory. banner\n// comment\n(e) => {\n  /* note */\n  e.i(1); // inline\n}\n",
    ),
    3,
  );
});

test("AST reader recognizes only calls through the factory runtime binding", () => {
  const result = analyzeFactory(
    `(e)=>{other.i(9);e.i(2);e.A(3);e.A(variable);e.s(["x",0,1],4)}`,
  );
  assert.deepEqual(result.exports, ["x"]);
  assert.deepEqual(
    result.imports.map(({ kind, target, static: isStatic }) => [
      kind,
      target,
      isStatic,
    ]),
    [
      ["direct", 2, true],
      ["dynamic", 3, true],
      ["dynamic", null, false],
    ],
  );
});

test("malformed source never produces a partial AST result", () => {
  assert.throws(() => analyzeFactory(`(e)=>{e.i(`), /malformed factory/);
  assert.throws(
    () => countSourceLines(`(e)=>{`),
    /cannot count malformed source/,
  );
});

test("exports distinguish constant triples from getter pairs and setters", () => {
  const result = analyzeFactory(`(runtime) => {
    runtime.s([
      "first", 0, "not_an_export",
      "second", 0, 42,
      "third", () => { throw new Error("getter must not execute"); },
      "mutable", () => current, (next) => { throw new Error("setter must not execute"); },
      "functionValue", 0, () => { throw new Error("value must not execute"); },
      "last", () => last
    ]);
  }`);
  assert.deepEqual(result.exports, [
    "first",
    "functionValue",
    "last",
    "mutable",
    "second",
    "third",
  ]);
});

test("export decoding supports empty arrays, repeated names and multiple registrations", () => {
  assert.deepEqual(analyzeFactory(`(e)=>{e.s([])}`).exports, []);
  assert.deepEqual(
    analyzeFactory(`(e)=>{
    e.s(["z", 0, "value", "a", () => 1]);
    e.s(["z", () => 2, "é😀", 0, undefined], 42);
  }`).exports,
    ["a", "é😀", "z"],
  );
});

test("unsupported or incomplete export arrays make no partial name claim", () => {
  for (const entries of [
    '["x"]',
    '["x", 0]',
    '["x", 1, "not_an_export"]',
    '["x", -1, "not_an_export"]',
    '["x", 0, , "y", () => y]',
    '["x", 0, ...values]',
    '["x", () => x, ...entries]',
    "[name, () => x]",
    '["x", getter]',
    '["x", false]',
    '["x", () => x, setter]',
    '["known", 0, 1, "dynamic", getter]',
    "entries",
  ]) {
    assert.deepEqual(
      analyzeFactory(`(e)=>{e.s(${entries})}`, "unsupported fixture").exports,
      [],
      entries,
    );
  }
});

test("unrelated non-array s calls do not become new analysis failures", () => {
  assert.deepEqual(
    analyzeFactory(`(e)=>{
      e.s(["real", 0, 1]);
      function unrelated(e) { e.s("ordinary-method-argument"); }
    }`).exports,
    ["real"],
  );
});

test("captured settings exports match authenticated mixed runtime descriptors", async () => {
  // Read and parse inert public source only; none of these factories is imported.
  const root = join(import.meta.dirname, "..");
  const runtime = await readFile(
    join(root, "evidence/web/objects/f25d7686d048ae16.js"),
  );
  assert.equal(
    hash(runtime),
    "b5f9b5199b99ab6c141f4540f0b7d0fe803c4ecf6956849ecb6e59d3d439272e",
  );
  const bytes = await readFile(
    join(root, "evidence/web/objects/11cf0bf8a734ea43.js"),
  );
  assert.equal(
    hash(bytes),
    "a859077ba48e8afb625cd917a674ace225a0959ad40932f02331402dd5365f83",
  );
  const source = new TextDecoder("utf-8", {
    fatal: true,
    ignoreBOM: true,
  }).decode(bytes);
  for (const { start, end, digest, names } of [
    {
      start: 47485,
      end: 48430,
      digest:
        "5adc58d562f652cfc69ab06c0735b0bc196440d952f1f2fc61eaaa8725dd3edf",
      names: ["C", "L", "M", "O", "q", "s", "u", "V", "W", "X"],
    },
    {
      start: 12934,
      end: 15396,
      digest:
        "00b703deb875b1517888552730f857a14e594ae5d6e0cf6948d55a23731b57e2",
      names: ["d", "f", "I", "n"],
    },
    {
      start: 32638,
      end: 40444,
      digest:
        "854b2b23846f367dbc1e84904d2954eaac355ef8c5412b32cd7cef39e7340110",
      names: ["g", "k", "n"],
    },
  ]) {
    const factory = source.slice(start, end);
    assert.equal(hash(factory), digest);
    assert.deepEqual(analyzeFactory(factory).exports, names);
  }
});

test("variant collisions remain ambiguous instead of resolving arbitrarily", async () => {
  const root = await fixture();
  const reports = await buildGraph(
    root,
    await completeFixtureOptions(root, ["/", "/missing"]),
  );
  const edges = reports["IMPORT-EDGES.json.gz"];
  const direct = edges.find((edge) => edge.requestedId === 2);
  assert.equal(direct.resolution, "AMBIGUOUS");
  assert.equal(direct.candidates.length, 2);
  assert.equal(
    edges.find((edge) => edge.requestedId === 3 && edge.kind === "dynamic")
      .resolution,
    "EXACT",
  );
  assert.equal(
    edges.find((edge) => edge.requestedId === 99).resolution,
    "UNRESOLVED",
  );
  assert.equal(
    edges.find((edge) => edge.requestedId === "react").resolution,
    "EXTERNAL",
  );
  assert.ok(edges.some((edge) => edge.source === edge.target));
  assert.equal(
    reports["ROUTE-ATTRIBUTION.json"]["/missing"].status,
    "NO_EXACT_CAPTURE",
  );
});

test("route seeds stay scoped to the linked origin of a deduplicated factory", async () => {
  const root = await fixture({ duplicateOrigin: true });
  const reports = await buildGraph(root, await completeFixtureOptions(root));
  const identities = reports["MODULE-IDENTITIES.json.gz"].filter(
    (identity) => identity.id === 3,
  );
  assert.equal(identities.length, 2);
  const linked = identities.find((identity) =>
    identity.origin.source.endsWith("source.js"),
  );
  const unlinked = identities.find((identity) =>
    identity.origin.source.endsWith("other.js"),
  );
  assert.deepEqual(linked.routeSeeds, ["/"]);
  assert.deepEqual(unlinked.routeSeeds, []);
  const route = reports["ROUTE-ATTRIBUTION.json"]["/"];
  assert.ok(route.seedNodes.includes(linked.key));
  assert.ok(!route.seedNodes.includes(unlinked.key));
  assert.ok(route.reachableNodes.includes(linked.key));
  assert.ok(!route.reachableNodes.includes(unlinked.key));
  assert.notEqual(linked.key, unlinked.key);
  assert.equal(linked.sha256, unlinked.sha256);
  assert.ok(
    reports["IMPORT-EDGES.json.gz"].some(
      (edge) => edge.source === linked.key && edge.target === linked.key,
    ),
  );
});

test("tampered formatted factories fail build, publish, and source verification", async () => {
  const root = await fixture();
  const options = { routes: ["/"], targetLines: 4, maximumLines: 100 };
  const valid = await buildGraph(root, options);
  assert.ok(
    valid["IMPORT-EDGES.json.gz"].some((edge) => edge.requestedId === 2),
  );
  await publishGraph(root, "research/graph", options);
  const manifestBefore = await readFile(
    join(root, "research/graph/MANIFEST.json"),
    "utf8",
  );
  const path = await recoveredPath(root, 1);
  const formatted = await readFile(path, "utf8");
  await writeFile(path, formatted.replace("e.i(2)", "e.i(777)"));
  await assert.rejects(
    buildGraph(root, options),
    /recovered factory authenticity mismatch/,
  );
  await assert.rejects(
    publishGraph(root, "research/graph", options),
    /recovered factory authenticity mismatch/,
  );
  await assert.rejects(
    verifyGraph(root, "research/graph", options),
    /recovered factory authenticity mismatch/,
  );
  assert.equal(
    await readFile(join(root, "research/graph/MANIFEST.json"), "utf8"),
    manifestBefore,
  );
  const publishedEdges = JSON.parse(
    (await import("node:zlib")).gunzipSync(
      await readFile(join(root, "research/graph/IMPORT-EDGES.json.gz")),
    ),
  );
  assert.ok(!publishedEdges.some((edge) => edge.requestedId === 777));
});

test("factory authenticity accepts AST-equivalent formatting and rejects semantic changes", async () => {
  const options = { routes: ["/"], targetLines: 4, maximumLines: 100 };
  const formattedRoot = await fixture();
  const formattedPath = await recoveredPath(formattedRoot, 2);
  const formatted = await readFile(formattedPath, "utf8");
  await writeFile(
    formattedPath,
    formatted.replace("(e) => {", "/* formatting only */\n(e) => {"),
  );
  await buildGraph(formattedRoot, options);

  const changedRoot = await fixture();
  const changedPath = await recoveredPath(changedRoot, 2);
  const changed = await readFile(changedPath, "utf8");
  await writeFile(changedPath, changed.replace("42", "44"));
  await assert.rejects(
    buildGraph(changedRoot, options),
    /recovered factory authenticity mismatch/,
  );
});

test("capture hash and UTF-16 source range mutations fail closed", async () => {
  await assert.rejects(
    buildGraph(await fixture({ corruptHash: true }), {
      routes: ["/"],
      targetLines: 1,
      maximumLines: 100,
    }),
    /capture hash mismatch/,
  );
  await assert.rejects(
    buildGraph(await fixture({ corruptRange: true }), {
      routes: ["/"],
      targetLines: 1,
      maximumLines: 100,
    }),
    /source range mismatch/,
  );
});

test("symlinked evidence is rejected", async (t) => {
  const root = await fixture();
  const manifestPath = join(root, "evidence/web/manifest.json");
  const realPath = join(root, "manifest-real.json");
  await writeFile(realPath, await readFile(manifestPath));
  await writeFile(manifestPath, "{}");
  await import("node:fs/promises").then(({ unlink }) => unlink(manifestPath));
  if (!await createTestSymlink(t, realPath, manifestPath)) return;
  await assert.rejects(
    buildGraph(root, { routes: ["/"], targetLines: 1, maximumLines: 100 }),
    /symlink rejected/,
  );
});

test("publication is deterministic and generated evidence rejects tampering", async () => {
  const first = await fixture();
  const second = await fixture({ reverse: true });
  const options = { routes: ["/"], targetLines: 4, maximumLines: 100 };
  await publishGraph(first, "research/graph", {
    routes: ["/"],
    targetLines: 4,
    maximumLines: 100,
  });
  await publishGraph(second, "research/graph", {
    routes: ["/"],
    targetLines: 4,
    maximumLines: 100,
  });
  const firstManifest = await readFile(
    join(first, "research/graph/MANIFEST.json"),
    "utf8",
  );
  const secondManifest = await readFile(
    join(second, "research/graph/MANIFEST.json"),
    "utf8",
  );
  assert.equal(firstManifest, secondManifest);
  await verifyGraph(first, "research/graph", options);
  await writeFile(join(first, "research/graph/unexpected.json"), "{}\n");
  await assert.rejects(
    verifyGraph(first, "research/graph", options),
    /unexpected generated evidence/,
  );
  await rm(join(first, "research/graph/unexpected.json"));
  await writeFile(join(first, "research/graph/GRAPH-SUMMARY.json"), "{}\n");
  await assert.rejects(
    verifyGraph(first, "research/graph", options),
    /generated evidence mismatch/,
  );
});

test("an interrupted replacement restores the last complete graph", async () => {
  const root = await fixture();
  const options = { routes: ["/"], targetLines: 4, maximumLines: 100 };
  await publishGraph(root, "research/graph", {
    routes: ["/"],
    targetLines: 4,
    maximumLines: 100,
  });
  const before = await readFile(
    join(root, "research/graph/MANIFEST.json"),
    "utf8",
  );
  await assert.rejects(
    publishGraph(root, "research/graph", {
      routes: ["/"],
      targetLines: 4,
      maximumLines: 100,
      onPublishStage: () => {
        throw new Error("simulated interruption");
      },
    }),
    /simulated interruption/,
  );
  assert.equal(
    await readFile(join(root, "research/graph/MANIFEST.json"), "utf8"),
    before,
  );
  await verifyGraph(root, "research/graph", options);
});

test(
  "checked-in corpus rebuild stays within the authenticated 200K-300K range",
  { timeout: 180_000 },
  async () => {
    const root = join(import.meta.dirname, "..");
    const reports = await buildGraph(root);
    const summary = reports["GRAPH-SUMMARY.json"];
    assert.ok(
      summary.analyzedLines >= 200_000 && summary.analyzedLines <= 300_000,
    );
    assert.ok(summary.uniqueFactories > 0);
    assert.equal(
      summary.edges,
      summary.resolutions.EXACT +
        summary.resolutions.AMBIGUOUS +
        summary.resolutions.UNRESOLVED +
        summary.resolutions.EXTERNAL,
    );
    const verification = reports["VERIFY-RESULTS.json"];
    assert.equal(verification.capturedCodeExecuted, false);
    assert.equal(
      verification.formattedFactoriesParsed,
      verification.formattedFactoriesAstAuthenticated +
        verification.formattedFactoriesDerivationAuthenticated,
    );
    assert.ok(
      summary.routeAttributedNodes < summary.identities,
      "unreferenced provenance identities must not inherit a route seed",
    );
  },
);
