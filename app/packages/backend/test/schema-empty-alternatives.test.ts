import test from "node:test";
import assert from "node:assert/strict";
import { validateAgainstSchema } from "../src/schema-validator.js";
test("an empty anyOf cannot silently disable an alternative constraint", () => {
  for (const value of [null, 0, "x", {}, []])
    assert.ok(validateAgainstSchema(value, { anyOf: [] }).length > 0);
  assert.deepEqual(
    validateAgainstSchema(0, { anyOf: [{ type: "number" }] }),
    [],
  );
  assert.ok(
    validateAgainstSchema("x", { anyOf: [{ type: "number" }] }).length > 0,
  );
});
