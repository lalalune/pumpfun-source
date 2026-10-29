import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
const { parseNativeFeedNavigation, nativeFeedHref } = createRequire(
  import.meta.url,
)("../../frontend/src/components/feed/native-feed-navigation.ts");
test("every supplied breadcrumb must survive navigation serialization", () => {
  for (const trail of [new Array(1), [undefined]])
    assert.throws(
      () =>
        parseNativeFeedNavigation({
          nativeCursor: "a.b",
          nativeTrail: trail as any,
        }),
      /cursor/,
    );
  const parsed = parseNativeFeedNavigation({
    nativeCursor: "a.b",
    nativeTrail: ["c.d"],
  });
  assert.deepEqual(parsed.trail, ["c.d"]);
  assert.equal(
    new URL(
      nativeFeedHref(parsed.kind, parsed.cursor, parsed.trail),
      "https://local.invalid",
    ).searchParams.get("nativeTrail"),
    "c.d",
  );
});
