import test from "node:test";
import assert from "node:assert/strict";
import { validateDeclared } from "../scripts/original-contracts/validate.mjs";
test("a matching alternative does not discard constraints on the containing rule", () => {
  const rule = {
    anyOf: [{ type: "number" }, { type: "string" }],
    type: "number",
    minimum: 10,
  };
  assert.equal(validateDeclared({}, rule, 2).success, false);
  assert.equal(validateDeclared({}, rule, 12).success, true);
  assert.equal(validateDeclared({}, rule, "x").success, false);
});
