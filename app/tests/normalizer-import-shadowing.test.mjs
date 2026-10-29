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
test("a parameter receiver is not the same capability as an imported receiver", () => {
  for (const normalize of normalizers) {
    const map = { "client.read": "operation:read" };
    const local = normalize(
      parseExpression("(client)=>client.read()"),
      {},
      map,
    );
    const renamed = normalize(
      parseExpression("(input)=>input.read()"),
      {},
      map,
    );
    assert.deepEqual(local, renamed);
    const global = normalize(
      parseExpression("()=>client.read()"),
      { client: "import:client" },
      map,
    );
    assert.notDeepEqual(local.body, global.body);
  }
});
