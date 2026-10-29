import test from "node:test";
import assert from "node:assert/strict";
import { parseMayhemResponse } from "../packages/frontend/src/app/mayhem/mayhem-data.ts";
test("Mayhem epochs are exact integers while market metrics may be fractional", () => {
  for (const field of ["createdTimestamp", "lastTradeTimestamp"])
    for (const value of [1.5, Number.MAX_SAFE_INTEGER + 1])
      assert.throws(() =>
        parseMayhemResponse({
          source: "synthetic-test",
          coins: [{ mint: "m", name: "n", symbol: "s", [field]: value }],
        }),
      );
  assert.equal(
    parseMayhemResponse({
      source: "synthetic-test",
      coins: [
        {
          mint: "m",
          name: "n",
          symbol: "s",
          createdTimestamp: 0,
          marketCapUsd: 1.5,
        },
      ],
    }).coins[0].marketCapUsd,
    1.5,
  );
});
