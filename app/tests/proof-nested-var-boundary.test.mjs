import test from "node:test";
import assert from "node:assert/strict";
import { parseExpression } from "@babel/parser";
import { normalizeSession } from "../scripts/verify-search-session.mjs";
import { normalizeNavigation } from "../scripts/verify-search-navigation.mjs";
import { normalizeUserSearch } from "../scripts/verify-user-search.mjs";
const normalizers = [
  normalizeSession,
  normalizeNavigation,
  normalizeUserSearch,
];
test("nested var must not be misqualified as a block-local declaration", () => {
  for (const n of normalizers) {
    const misleading = parseExpression("()=>{{var x=1}return x}");
    assert.throws(
      () => n(misleading, { x: "port:external" }),
      /nested function-scoped var/,
    );
    assert.doesNotThrow(() => n(parseExpression("()=>{var x=1;return x}"), {}));
    assert.doesNotThrow(() =>
      n(parseExpression("()=>{{let x=1; x}return 2}"), {}),
    );
  }
});
