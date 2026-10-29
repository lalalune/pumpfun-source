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
test("named functions and hoisted local helper references alpha-compare", () => {
  for (const normalize of normalizers) {
    assert.deepEqual(
      normalize(parseExpression("function f(n){return n?f(n-1):0}"), {}),
      normalize(parseExpression("function g(x){return x?g(x-1):0}"), {}),
    );
    assert.deepEqual(
      normalize(
        parseExpression("()=>{function help(){return 1}return help()}"),
        {},
      ),
      normalize(
        parseExpression("()=>{function other(){return 1}return other()}"),
        {},
      ),
    );
  }
});
