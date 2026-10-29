import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";
const require = createRequire(
  new URL("../packages/sdk/package.json", import.meta.url),
);
const BN = require("bn.js");
const { lessSlippage } = await import(
  new URL("../packages/sdk/src/slippage.ts", import.meta.url).href
);

test("one percent reduces the amount and respects the floor", () => {
  assert.equal(lessSlippage(new BN(1000), 1).toString(), "990");
  assert.equal(lessSlippage(new BN(50), 50, 1).toString(), "25");
  assert.equal(lessSlippage(new BN(10), 100, 1).toString(), "1");
});

test("negative slippage is rejected instead of raising the minimum", () => {
  assert.throws(
    () => lessSlippage(new BN(1000), -10),
    /between 0 and 100/,
  );
});

test("slippage above 100 and non-finite values are rejected", () => {
  assert.throws(() => lessSlippage(new BN(1000), 100.1), /between 0 and 100/);
  assert.throws(() => lessSlippage(new BN(1000), Number.NaN), /between 0 and 100/);
});
