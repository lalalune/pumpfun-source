import assert from "node:assert/strict";
import { resolve } from "node:path";
import test from "node:test";
import { analyzeFactory } from "../scripts/factory-graph/core.mjs";
import { openCorpus } from "../scripts/original-contracts/source.mjs";

test("captured factory 504554 does not import through a shadowing function parameter", async () => {
  const corpus = await openCorpus(resolve(import.meta.dirname, ".."));
  const factory = await corpus.factory(504554);
  assert.equal(
    factory.provenance.sha256,
    "3c91f814678cfb43fcdcb14d2c09b8cfb0c71d7464da81ae8a786a9e8c30dc7f",
  );
  const analysis = analyzeFactory(factory.text());
  assert.deepEqual(analysis.imports, []);
  assert.deepEqual(analysis.exports, []);
});

test("runtime calls follow lexical bindings, including closures and hoisted declarations", () => {
  const analysis = analyzeFactory(`(runtime) => {
    runtime.i(1);
    (() => runtime.A(2))();
    function parameter(runtime) { runtime.i(3); runtime.s(['wrong', 0, 3]); }
    function hoisted() { runtime.i(4); var runtime; }
    { let runtime; runtime.A(5); }
    try {} catch (runtime) { runtime.i(6); }
    const nested = function runtime() { runtime.i(7); };
    for (let runtime of []) { runtime.i(8); }
    function destructured({runtime}) { runtime.i(9); }
    runtime.s(['right', 0, 1]);
    function closure() { runtime.i(10); }
  }`);
  assert.deepEqual(
    analysis.imports.map(({ target }) => target),
    [1, 2, 10],
  );
  assert.deepEqual(analysis.exports, ["right"]);
});

test("ordinary nested locals do not hide the runtime parameter", () => {
  const analysis = analyzeFactory(`function(runtime) {
    function nested(other) { runtime.i('react'); }
    { let other; runtime.i(7); }
    runtime.s(['x', () => runtime.i(8)]);
  }`);
  assert.deepEqual(
    analysis.imports.map(({ target }) => target),
    ["react", 7, 8],
  );
  assert.deepEqual(analysis.exports, ["x"]);
});
