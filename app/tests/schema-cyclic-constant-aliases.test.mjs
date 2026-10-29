import test from "node:test";
import assert from "node:assert/strict";
import { parseExpression } from "@babel/parser";
import { fileURLToPath } from "node:url";
import { openCorpus } from "../scripts/original-contracts/source.mjs";
import { createSchemaExtractor } from "../scripts/original-contracts/schema.mjs";
const corpus = await openCorpus(fileURLToPath(new URL("..", import.meta.url)));
const factory = await corpus.factory(387665);
const extract = () => createSchemaExtractor(corpus);
test("cyclic aliases stop with a bounded declaration diagnostic; acyclic aliases remain usable", async () => {
  const { parse } = await import("@babel/parser");
  const node = parse("(r,m,e)=>{const a=b,b=a,ok=3;e.schema=a}").program.body[0]
    .expression;
  const fake = {
    id: 999999,
    runtime: "r",
    node,
    provenance: { sha256: "synthetic" },
    text: () => "",
    witness: () => ({ source: "synthetic", utf16: [0, 1] }),
  };
  const x = createSchemaExtractor({
    factory: async (id) => (id === 999999 ? fake : corpus.factory(id)),
  });
  await assert.rejects(
    x.constant(parseExpression("a"), fake),
    /cyclic constant declaration/,
  );
  assert.equal(await x.constant(parseExpression("ok"), fake), 3);
  assert.deepEqual(
    await Promise.all([
      x.constant(parseExpression("ok"), fake),
      x.constant(parseExpression("ok"), fake),
    ]),
    [3, 3],
  );
});
