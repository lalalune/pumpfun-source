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
test("static method keys cannot be alpha-renamed into capability roles", () => {
  for (const normalize of normalizers) {
    const first = normalize(parseExpression("()=>({first(){return 1}})"), {
      first: "port:shared",
    });
    const second = normalize(parseExpression("()=>({second(){return 1}})"), {
      second: "port:shared",
    });
    assert.notDeepEqual(first, second);
  }
});
test("method parameters bind locally while closures retain their outer inputs", () => {
  for (const normalize of normalizers) {
    const first = normalize(
      parseExpression("(input)=>({read(value){return input+value}})"),
      {},
    );
    const second = normalize(
      parseExpression("(base)=>({read(item){return base+item}})"),
      {},
    );
    assert.deepEqual(first, second);
    assert.notDeepEqual(
      first,
      normalize(
        parseExpression("(base)=>({read(item){return item+item}})"),
        {},
      ),
    );
  }
});
