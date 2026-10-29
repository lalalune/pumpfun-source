import test from "node:test";
import assert from "node:assert/strict";
import { parseExpression } from "@babel/parser";
import { literal } from "../scripts/original-contracts/source.mjs";
test("overflowing JS numeric literals cannot turn into JSON null", () => {
  for (const text of ["1e400", "-1e400"])
    assert.throws(() => literal(parseExpression(text)), /nonfinite/);
  assert.equal(literal(parseExpression("-1.5")), -1.5);
  assert.equal(literal(parseExpression("!1e400")), false);
  assert.equal(literal(parseExpression('"Infinity"')), "Infinity");
});
