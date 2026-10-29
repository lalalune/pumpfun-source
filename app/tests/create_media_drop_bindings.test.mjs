import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";

const root = new URL("../", import.meta.url);
const read = (path) => readFileSync(new URL(path, root));
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
const manifest = JSON.parse(read("evidence/web/manifest.json"));
const modules = JSON.parse(read("recovered/modules.json")).modules;
const objects = [
  [
    "5e15667ed36cac85",
    "6568b22a593755b49e02ccc9cb85fdc7655d50e09ccac6d9e0942783ff9f2b26",
  ],
  [
    "89ce7de3b9bad421.js",
    "d275ba753876846f4bf1e5a6923b88b9e8daac07d56fb1fdca785d35a9bb096e",
  ],
  [
    "01f240a1f9100e9d.js",
    "d342ebc4046f8be0723f9513e24649b615415b2923a09ea74a702145fda51bec",
  ],
  [
    "762f0784b7be61c0.js",
    "bcf44369e779ce7350d3208f3b954d45fb60de35e553f9e07fa3f058ddc4ee03",
  ],
];
function authenticate() {
  const captured = new Map();
  for (const [name, expected] of objects) {
    const path = `evidence/web/objects/${name}`;
    const record = manifest.records.find((value) => value.path === path);
    assert.equal(record.status, 200);
    assert.equal(record.sha256, expected);
    const bytes = read(path);
    assert.equal(bytes.length, record.bytes);
    assert.equal(sha(bytes), expected);
    captured.set(path, bytes.toString("utf8"));
  }
  const factories = new Map();
  for (const [id, digest, path, start, end] of [
    [
      734638,
      "616b013f89f1cf3e446817865c602c16b9eb6f07e09fa05145c0191ce60f63bc",
      "89ce7de3b9bad421.js",
      119,
      66825,
    ],
    [
      320853,
      "f11b9e82b5951d62d9717dad92358a120241bab0e6453ad8550cd8f2775975d9",
      "01f240a1f9100e9d.js",
      119,
      224,
    ],
    [
      658259,
      "691ff5f669927ccece0478631066f80ac94a832dd5fadae2a3a175f09372e6fa",
      "762f0784b7be61c0.js",
      138,
      5776,
    ],
  ]) {
    const source = `evidence/web/objects/${path}`;
    const matches = modules.filter(
      (value) => value.ids.includes(id) && value.sha256 === digest,
    );
    assert.equal(matches.length, 1);
    assert.ok(
      matches[0].origins.some(
        (value) =>
          value.source === source && value.start === start && value.end === end,
      ),
    );
    const text = captured.get(source).slice(start, end); // Declared UTF-16 offsets.
    assert.equal(sha(text), digest);
    factories.set(id, text);
  }
  return { captured, factories };
}

test("Create drop surface is bound through its actual lazy module edge, not a direct script claim", () => {
  const { captured, factories } = authenticate();
  const route = captured.get("evidence/web/objects/5e15667ed36cac85");
  assert.match(route, /1d42gkuet1_-2\.js/);
  assert.match(route, /13--g72v0ugku\.js/);
  assert.doesNotMatch(route, /3r6p9e97ury3w\.js/);
  assert.match(
    factories.get(734638),
    /e\.A\(320853\)\.then\(e=>\(\{default:e\.FileDropzoneInner\}\)\)/,
  );
  assert.match(
    factories.get(320853),
    /static\/immutable\/chunks\/3r6p9e97ury3w\.js/,
  );
  assert.match(factories.get(320853), /m\(658259\)/);
});

test("observed caller admits one media file and selector delegates accept/reject/drop behavior", () => {
  const { factories } = authenticate();
  assert.match(
    factories.get(734638),
    /onDrop:e=>er\(e\[0\]\),accept:eX\.v,maxFiles:1/,
  );
  const selector = factories.get(658259);
  for (const literal of [
    "onDrop:",
    "onDropRejected:",
    "maxFiles:",
    "isDragAccept:",
    "isDragReject:",
    "getInputProps:",
    "noDrag:",
    "OR_DRAG_AND_DROP",
  ])
    assert.ok(selector.includes(literal), literal);
  assert.match(selector, /C=void 0===y\?1:y/);
});
