import test from "node:test";
import assert from "node:assert/strict";
import { isLocalUserSearchRows } from "../packages/frontend/src/lib/local-user-search-data.ts";
import { validateNativeFeedPage } from "../packages/frontend/src/components/feed/native-feed-data.ts";
test("client type guards cannot certify absent inventory rows", () => {
  assert.equal(isLocalUserSearchRows(new Array(1)), false);
  assert.throws(() =>
    validateNativeFeedPage({ coins: new Array(1) }, "ranked"),
  );
  assert.equal(isLocalUserSearchRows([]), true);
  assert.deepEqual(validateNativeFeedPage({ coins: [] }, "ranked").coins, []);
});
