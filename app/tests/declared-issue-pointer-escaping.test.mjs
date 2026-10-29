import test from "node:test";
import assert from "node:assert/strict";
import { validateDeclared } from "../scripts/original-contracts/validate.mjs";
test("diagnostic paths distinguish slashes and tildes in own object keys", () => {
  const rule = { type: "object", properties: { "a/b~c": { type: "string" } } };
  const result = validateDeclared({}, rule, { "a/b~c": 3 });
  assert.equal(result.success, false);
  assert.equal(result.issues[0].path, "/a~1b~0c");
  assert.equal(validateDeclared({}, rule, { "a/b~c": "ok" }).success, true);
});
