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
test("nested array, object rest and rest parameters alpha-compare", () => {
  for (const n of normalizers) {
    for (const [a, b] of [
      ["([first,,...tail])=>[first,tail]", "([head,,...rest])=>[head,rest]"],
      ["({a,...rest})=>rest", "({a:x,...other})=>other"],
      ["(...args)=>args", "(...items)=>items"],
    ])
      assert.deepEqual(n(parseExpression(a), {}), n(parseExpression(b), {}));
  }
});
