import assert from "node:assert/strict";
import { test } from "node:test";
import { readFile, writeFile, mkdir, mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { parseExpression } from "@babel/parser";
import {
  exportDeclarations,
  inspectExportProviders,
  RUNTIME_SOURCE,
} from "../scripts/factory-graph/export-providers.mjs";
import {
  decodeSource,
  sha256,
  RANGE_ENCODING,
} from "../scripts/original-contracts/source.mjs";

const APP = path.resolve(import.meta.dirname, "..");
const REAL_SOURCE = "evidence/web/objects/0f4bad575370faed.js";

function decode(text, ids = [7]) {
  const { byteOffsets } = decodeSource(Buffer.from(text));
  const capture = {
    text,
    witness: ({ start, end }, label) => ({
      label,
      source: "synthetic.js",
      sourceSha256: sha256(text),
      utf16: [start, end],
      utf8: [byteOffsets[start], byteOffsets[end]],
      sha256: sha256(
        Buffer.from(text).subarray(byteOffsets[start], byteOffsets[end]),
      ),
    }),
  };
  return exportDeclarations({
    node: parseExpression(text),
    runtime: "e",
    ids,
    capture,
  });
}

test("captured S Root maps to DrawerRoot in physical439587; grouped target is not a literal factory", async () => {
  const result = await inspectExportProviders(APP, "396623", [REAL_SOURCE]);
  assert.equal(result.providers.length, 1);
  assert.equal(result.literalRegistrations.length, 0);
  const provider = result.providers[0];
  assert.equal(provider.method, "S");
  assert.equal(provider.target.value, 396623);
  assert.deepEqual(provider.physicalFactory.ids, [439587]);
  assert.equal(
    provider.physicalFactory.sha256,
    "556a5e98fc389f458883751f5ed829f9493c87444c6f5053b676b34a39f05fa9",
  );
  assert.deepEqual(provider.raw.utf16, [84773, 84944]);
  assert.equal(
    provider.raw.sha256,
    "d60bcd5c51aba99f17fa85b895396c96d63d0390cc4d66af6a9d9f65e3cfbf19",
  );
  assert.deepEqual(
    provider.descriptors.map((d) => [d.exportName, d.property.value]),
    [
      ["Backdrop", "DrawerBackdrop"],
      ["Popup", "DrawerPopup"],
      ["Portal", "DrawerPortal"],
      ["Root", "DrawerRoot"],
      ["Trigger", "DrawerTrigger"],
      ["Viewport", "DrawerViewport"],
    ],
  );
  const root = provider.descriptors.find((d) => d.exportName === "Root");
  assert.equal(root.namespace.raw.text, "f");
  assert.equal(root.namespace.importInitializerCandidates[0].moduleId, 524684);
  assert.equal(
    result.sourceContexts[0].sourceSha256,
    "feb10137dd786820010700c4292fc2c38647c79de5493e6e0689552055ec7cbc",
  );
  for (const entry of result.runtime) {
    const bytes = await readFile(path.join(APP, entry.source));
    assert.equal(sha256(bytes.subarray(...entry.utf8)), entry.sha256);
  }
  assert.match(
    result.runtime.find((entry) => entry.label === "runtime helper m").text,
    /Reflect.getOwnPropertyDescriptor\(r,n\)/,
  );
});

test("captured s targets660315 while its real literal aliases stay attached to one physical factory", async () => {
  const result = await inspectExportProviders(APP, "660315", [REAL_SOURCE]);
  assert.equal(result.providers.length, 1);
  assert.equal(result.literalRegistrations.length, 1);
  const provider = result.providers[0];
  assert.equal(provider.method, "s");
  assert.deepEqual(provider.physicalFactory.ids, [524684, 660315, 195636]);
  assert.equal(
    provider.physicalFactory.sha256,
    "4a95dd69ab776beb22fce660c865256c7cc7ddc091c08d949c92213f537a1f1d",
  );
  assert.deepEqual(provider.raw.utf16, [13739, 16546]);
  assert.deepEqual(
    provider.descriptors.map((d) => d.exportName),
    ["Backdrop", "Close", "Popup", "Portal", "Root", "Title"],
  );
  assert.ok(!provider.descriptors.some((d) => d.exportName === "DrawerRoot"));
});

test("actual CLI source-context lookup is deterministic and leaves selected reports unchanged", async () => {
  const files = [
    "recovered/modules.json",
    "research/turbopack-route-graph-20261028/MODULE-IDENTITIES.json.gz",
    "research/turbopack-route-graph-20261028/MANIFEST.json",
  ];
  const before = await Promise.all(
    files.map((file) => readFile(path.join(APP, file))),
  );
  const args = [
    "scripts/factory-graph/cli.mjs",
    "module",
    "396623",
    "--source",
    REAL_SOURCE,
  ];
  const first = spawnSync(process.execPath, args, {
    cwd: APP,
    encoding: "utf8",
  });
  const second = spawnSync(process.execPath, args, {
    cwd: APP,
    encoding: "utf8",
  });
  assert.equal(first.status, 0, first.stderr);
  assert.equal(second.stdout, first.stdout);
  assert.equal(JSON.parse(first.stdout).providers[0].method, "S");
  for (let i = 0; i < files.length; i++)
    assert.deepEqual(await readFile(path.join(APP, files[i])), before[i]);
  const legacy = spawnSync(
    process.execPath,
    ["scripts/factory-graph/cli.mjs", "module", "396623"],
    { cwd: APP, encoding: "utf8" },
  );
  assert.notEqual(legacy.status, 0);
  assert.match(legacy.stderr, /no selected identity for module 396623/);
});

test("lowercase descriptors retain target, constant/getter/setter and raw expressions without executing them", () => {
  const [entry] = decode(
    '(e)=>{e.s(["constant",0,(()=>{throw Error("never")})(),"getter",()=>value,v=>set(v)],99)}',
  );
  assert.equal(entry.target.value, 99);
  assert.equal(entry.status, "decoded");
  assert.deepEqual(
    entry.descriptors.map((d) => d.kind),
    ["constant", "accessor"],
  );
  assert.match(entry.descriptors[0].value.text, /throw Error/);
  assert.equal(entry.descriptors[1].setter.text, "v=>set(v)");
});

test("uppercase packed and expanded aliases preserve empty/missing fields without invented defaults", () => {
  const [entry] = decode(
    '(e)=>{e.S([123,"A,B,C,",0,namespace,"D","E","F",0,other,"G"],"target")}',
  );
  assert.equal(entry.target.valueType, "string");
  assert.deepEqual(
    entry.descriptors.map((d) => [d.exportName, d.property]),
    [
      ["A", { kind: "literal", value: "B", valueType: "string" }],
      ["C", { kind: "literal", value: "", valueType: "string" }],
      ["D", { kind: "literal", value: "E", valueType: "string" }],
      ["F", { kind: "undefined" }],
      ["G", { kind: "undefined" }],
    ],
  );
  assert.equal(entry.descriptors[0].namespace.moduleId, 123);
  assert.equal(entry.descriptors[2].namespace.kind, "expression");
});

test("implicit and null targets stay current-module; explicit numeric and string IDs stay distinct", () => {
  const entries = decode(
    '(e)=>{e.s(["a",0,1]);e.s(["b",0,2],null);e.s(["c",0,3],7);e.s(["d",0,4],"7");e.s(["x",0,5],computed)}',
    [7, 8],
  );
  assert.deepEqual(
    entries.slice(0, 2).map((d) => d.target.kind),
    ["current-module", "current-module"],
  );
  assert.deepEqual(entries[0].target.ids, [7, 8]);
  assert.deepEqual(
    entries.slice(2, 4).map((d) => d.target.valueType),
    ["number", "string"],
  );
  assert.equal(entries[4].target.kind, "dynamic");
});

test("direct comma declarations are retained; nested functions, blocks and lookalike receivers are excluded", () => {
  const entries = decode(
    '(e)=>{e.s(["a",0,1],9),e.S([ns,"B,C"],9);function inner(e){e.s(["fake",0,2],9)}if(ok){e.s(["conditional",0,3],9)}other.S([ns,"fake"],9)}',
  );
  assert.deepEqual(
    entries.map((d) => d.method),
    ["s", "S"],
  );
});

test("unsupported descriptor shapes make no partial declaration-name claim", () => {
  for (const expression of [
    'e.s(["ok",0,1,...rest],9)',
    'e.s(["ok",0,1,"bad",getter],9)',
    'e.s(["bad",1,value],9)',
    'e.s(["bad",0],9)',
    "e.s(dynamic,9)",
    'e.S([ns,"ok,X",0,other,...rest],9)',
    "e.S([ns,42],9)",
    'e.S([ns,"X",property],9)',
  ]) {
    const [entry] = decode(`(e)=>{${expression}}`);
    assert.equal(entry.status, "unsupported", expression);
    assert.deepEqual(entry.descriptors, [], expression);
  }
});

async function fixture(t) {
  const root = await mkdtemp(path.join(tmpdir(), "export-providers-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  await mkdir(path.join(root, "evidence/web/objects"), { recursive: true });
  await mkdir(path.join(root, "recovered"));
  const runtime = await readFile(path.join(APP, RUNTIME_SOURCE));
  const source = "evidence/web/objects/synthetic.js";
  const text =
    '\ufeff(globalThis.TURBOPACK||(globalThis.TURBOPACK=[])).push(["c",[1,e=>{const label="é😀";e.s(["A",0,1],9)}],2,e=>{e.S([ns,"B,C"],9);e.s(["X",0,1],dynamic)}]);';
  const records = [
    {
      path: source,
      url: "https://example.invalid/c.js",
      status: 200,
      bytes: Buffer.byteLength(text),
      sha256: sha256(text),
    },
    {
      path: RUNTIME_SOURCE,
      url: "https://example.invalid/runtime.js",
      status: 200,
      bytes: runtime.length,
      sha256: sha256(runtime),
    },
  ];
  const modules = [
    'e=>{const label="é😀";e.s(["A",0,1],9)}',
    'e=>{e.S([ns,"B,C"],9);e.s(["X",0,1],dynamic)}',
  ].map((raw, index) => {
    const start = text.indexOf(raw);
    return {
      ids: [index + 1],
      sha256: sha256(raw),
      origins: [
        { source, url: records[0].url, start, end: start + raw.length },
      ],
    };
  });
  await writeFile(path.join(root, source), text);
  await writeFile(path.join(root, RUNTIME_SOURCE), runtime);
  const save = async () => {
    await writeFile(
      path.join(root, "evidence/web/manifest.json"),
      JSON.stringify({ records }),
    );
    await writeFile(
      path.join(root, "recovered/modules.json"),
      JSON.stringify({ rangeEncoding: RANGE_ENCODING, modules }),
    );
  };
  await save();
  return { root, source, text, records, modules, save };
}

test("all physical providers and unresolved targets survive explicit context; Unicode ranges bind raw bytes", async (t) => {
  const f = await fixture(t);
  const result = await inspectExportProviders(f.root, "9", [
    f.source,
    f.source,
  ]);
  assert.equal(result.providers.length, 2);
  assert.equal(result.ambiguous, true);
  assert.deepEqual(
    result.providers.map((p) => p.physicalFactory.ids),
    [[1], [2]],
  );
  assert.equal(result.unresolvedTargets.length, 1);
  const raw = result.providers[0].raw;
  assert.ok(raw.utf8[0] > raw.utf16[0]);
  assert.equal(sha256(Buffer.from(f.text).subarray(...raw.utf8)), raw.sha256);
});

test("a hash/length change is rejected before provider attribution", async (t) => {
  const f = await fixture(t);
  await writeFile(path.join(f.root, f.source), f.text + " ");
  await assert.rejects(
    inspectExportProviders(f.root, "9", [f.source]),
    /authentication failed/,
  );
});

test("multiple explicit objects preserve real per-origin aliases and all provider occurrences", async (t) => {
  const f = await fixture(t);
  const secondSource = "evidence/web/objects/another.js";
  const raw = f.text.slice(
    f.modules[0].origins[0].start,
    f.modules[0].origins[0].end,
  );
  const text = `(globalThis.TURBOPACK||(globalThis.TURBOPACK=[])).push(["other",33,${raw}]);`;
  const start = text.indexOf(raw);
  const record = {
    path: secondSource,
    url: "https://example.invalid/another.js",
    status: 200,
    bytes: Buffer.byteLength(text),
    sha256: sha256(text),
  };
  f.records.push(record);
  f.modules[0].ids.push(33);
  f.modules[0].origins.push({
    source: secondSource,
    url: record.url,
    start,
    end: start + raw.length,
  });
  await writeFile(path.join(f.root, secondSource), text);
  await f.save();
  const result = await inspectExportProviders(f.root, "9", [
    f.source,
    secondSource,
  ]);
  assert.equal(result.providers.length, 3);
  assert.deepEqual(
    result.providers.map((p) => p.physicalFactory.ids),
    [[33], [1], [2]],
  );
  assert.equal(
    result.providers[0].physicalFactory.sha256,
    result.providers[1].physicalFactory.sha256,
  );
  assert.deepEqual(
    result,
    await inspectExportProviders(f.root, "9", [secondSource, f.source]),
  );
});

test("an authenticated but different runtime is rejected instead of assuming its decoder grammar", async (t) => {
  const f = await fixture(t);
  const bytes = Buffer.concat([
    await readFile(path.join(f.root, RUNTIME_SOURCE)),
    Buffer.from(" "),
  ]);
  f.records[1].bytes = bytes.length;
  f.records[1].sha256 = sha256(bytes);
  await writeFile(path.join(f.root, RUNTIME_SOURCE), bytes);
  await f.save();
  await assert.rejects(
    inspectExportProviders(f.root, "9", [f.source]),
    /unsupported export-provider runtime/,
  );
});

test("a forged inventory origin or content hash cannot authenticate the physical provider", async (t) => {
  const f = await fixture(t);
  f.modules[0].origins[0].start++;
  await f.save();
  await assert.rejects(
    inspectExportProviders(f.root, "9", [f.source]),
    /inventory binding failed/,
  );
});

test("inventory aggregate IDs cannot invent implicit providers or literal registrations", async (t) => {
  const f = await fixture(t);
  f.modules[0].ids.push(99);
  await f.save();
  const result = await inspectExportProviders(f.root, "99", [f.source]);
  assert.deepEqual(result.literalRegistrations, []);
  assert.deepEqual(result.providers, []);
});

test("source contexts cannot escape retained objects and malformed CLI arguments fail", async (t) => {
  const f = await fixture(t);
  await assert.rejects(
    inspectExportProviders(f.root, "9", ["../outside.js"]),
    /non-object capture path/,
  );
  const run = spawnSync(
    process.execPath,
    ["scripts/factory-graph/cli.mjs", "module", "9", "--source"],
    { cwd: APP, encoding: "utf8" },
  );
  assert.notEqual(run.status, 0);
  assert.match(run.stderr, /usage: graph:module/);
});
