import test from "node:test";
import assert from "node:assert/strict";
import { openCorpus } from "../scripts/original-contracts/source.mjs";
import { fileURLToPath } from "node:url";
test("factory-scoped witnesses cannot attribute neighboring source ranges", async () => {
  const c = await openCorpus(fileURLToPath(new URL("..", import.meta.url)));
  const f = await c.factory(387665);
  assert.throws(
    () => f.witness({ start: 0, end: 1 }, "foreign"),
    /outside factory/,
  );
  assert.doesNotThrow(() => f.witness(f.node, "factory"));
});
