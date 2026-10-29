import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
const { validateNativeFeedPage } = createRequire(import.meta.url)(
  "../../frontend/src/components/feed/native-feed-data.ts",
);
test("unknown feed kinds cannot masquerade as ranked responses", () => {
  for (const kind of ["other", null, 42])
    assert.throws(
      () => validateNativeFeedPage({ coins: [] }, kind as any),
      /kind/,
    );
  assert.equal(validateNativeFeedPage({ coins: [] }, "ranked").kind, "ranked");
});
