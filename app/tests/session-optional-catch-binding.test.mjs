import test from "node:test";
import assert from "node:assert/strict";
import { parseExpression } from "@babel/parser";
import { normalizeSession } from "../scripts/verify-search-session.mjs";
test("optional catch bindings preserve the handler body without crashing", () => {
  const ast = parseExpression("()=>{try {throw 1}catch {return 2}}");
  assert.doesNotThrow(() => normalizeSession(ast, {}));
  const a = normalizeSession(ast, {});
  assert.notDeepEqual(
    a,
    normalizeSession(
      parseExpression("()=>{try {throw 1}catch {return 3}}"),
      {},
    ),
  );
});
