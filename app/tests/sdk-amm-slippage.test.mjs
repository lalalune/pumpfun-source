import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";

const require = createRequire(
  new URL("../packages/sdk/package.json", import.meta.url),
);
const BN = require("bn.js");
const { maxAfterSlippage, minAfterSlippage } = await import(
  new URL("../packages/sdk/src/swap/slippage.ts", import.meta.url).href
);

test("one percent moves the bound in the documented direction", () => {
  assert.equal(maxAfterSlippage(new BN(1000), 1).toString(), "1010");
  assert.equal(minAfterSlippage(new BN(1000), 1).toString(), "990");
  assert.equal(minAfterSlippage(new BN(1000), 100).toString(), "0");
});

test("negative slippage is rejected before it inverts the minimum", () => {
  assert.throws(
    () => minAfterSlippage(new BN(5000), -10),
    /between 0 and 100/,
  );
  assert.throws(
    () => maxAfterSlippage(new BN(5000), -10),
    /between 0 and 100/,
  );
});

test("non-finite slippage is rejected", () => {
  assert.throws(
    () => minAfterSlippage(new BN(5000), Number.NaN),
    /between 0 and 100/,
  );
});
