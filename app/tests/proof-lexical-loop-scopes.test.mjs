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
test("loop locals alpha-compare without escaping their lexical scope", () => {
  for (const n of normalizers) {
    for (const [a, b] of [
      [
        "()=>{for(let i=0;i<2;i++){}return 0}",
        "()=>{for(let j=0;j<2;j++){}return 0}",
      ],
      [
        "(obj)=>{for(const key in obj){obj[key]}}",
        "(data)=>{for(const prop in data){data[prop]}}",
      ],
      ["(xs)=>{for(const x of xs){x}}", "(ys)=>{for(const y of ys){y}}"],
    ])
      assert.deepEqual(n(parseExpression(a), {}), n(parseExpression(b), {}));
    assert.throws(
      () => n(parseExpression("(xs)=>{for(const x of xs){}return x}"), {}),
      /unresolved/,
    );
  }
});
