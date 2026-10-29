import test from "node:test";
import assert from "node:assert/strict";
import { parseExpression } from "@babel/parser";
import { fileURLToPath } from "node:url";
import { openCorpus, sha256 } from "../scripts/original-contracts/source.mjs";
import { createSchemaExtractor } from "../scripts/original-contracts/schema.mjs";
import { validateDeclared } from "../scripts/original-contracts/validate.mjs";
const real = await openCorpus(fileURLToPath(new URL("..", import.meta.url)));
async function extract(body) {
  const text = `(e,t,n)=>{const a=e.i(876543);${body}}`;
  const node = parseExpression(text);
  const id = 999999999;
  const factory = {
    id,
    node,
    runtime: "e",
    text: (n = node) => text.slice(n.start, n.end),
    provenance: { sha256: sha256(Buffer.from(text)) },
    witness: (n, label) => ({
      source: "synthetic-input",
      utf16: [n.start, n.end],
      label,
      sha256: sha256(Buffer.from(text.slice(n.start, n.end))),
    }),
  };
  const x = createSchemaExtractor({
    factory: async (i, o) => (i === id ? factory : real.factory(i, o)),
  });
  const ref = await x.schema(id, "dto");
  const doc = x.document({ schema: ref });
  return {
    ref,
    doc,
    check: (value) => validateDeclared(doc, ref, value).success,
  };
}
test("a repeated supported integer refinement remains idempotent", async () => {
  const r = await extract("n.dto=a.z.number().int().int();");
  assert.equal(r.check(2), true);
  assert.equal(r.check(2.5), false);
  assert.equal(r.check(Number.MAX_SAFE_INTEGER + 1), false);
});
