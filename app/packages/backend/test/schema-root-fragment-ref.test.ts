import test from "node:test";
import assert from "node:assert/strict";
import { validateAgainstSchema } from "../src/schema-validator.js";
test("a root fragment resolves without inventing an empty property segment", () => {
  const root = { type: "integer" };
  assert.deepEqual(validateAgainstSchema(7, { $ref: "#" }, "$", root), []);
  assert.ok(
    validateAgainstSchema("7", { $ref: "#" }, "$", root).some((i) =>
      i.message.includes("expected type"),
    ),
  );
  assert.ok(
    validateAgainstSchema(7, { $ref: "#/missing" }, "$", root).length > 0,
  );
});
