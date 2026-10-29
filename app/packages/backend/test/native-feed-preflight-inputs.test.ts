import test from "node:test";
import assert from "node:assert/strict";
import Module, { createRequire } from "node:module";
import { mock } from "node:test";
const internals = Module as unknown as { _load: (...args: any[]) => any };
const original = internals._load;
const marker = mock.method(
  internals,
  "_load",
  function (this: unknown, name: string, ...rest: any[]) {
    if (name === "server-only") return {};
    return original.apply(this, [name, ...rest]);
  },
);
let loadNativeFeed: any;
try {
  ({ loadNativeFeed } = createRequire(import.meta.url)(
    "../../frontend/src/components/feed/native-feed-server.ts",
  ));
} finally {
  marker.mock.restore();
}
test("invalid direct feed state cannot dispatch a different local read", async () => {
  const before = process.env.PUMP_LOCAL_HOME_FEED;
  process.env.PUMP_LOCAL_HOME_FEED = "enabled";
  const fetchBefore = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => {
    calls++;
    throw Error("synthetic transport");
  };
  try {
    for (const [kind, cursor] of [
      ["other", undefined],
      ["ranked", ""],
      ["ranked", "bad cursor"],
    ]) {
      const r = await loadNativeFeed(kind, cursor);
      assert.equal(r.ok, false);
    }
    assert.equal(calls, 0);
    await loadNativeFeed("ranked");
    assert.equal(calls, 1);
  } finally {
    globalThis.fetch = fetchBefore;
    if (before === undefined) delete process.env.PUMP_LOCAL_HOME_FEED;
    else process.env.PUMP_LOCAL_HOME_FEED = before;
  }
});
