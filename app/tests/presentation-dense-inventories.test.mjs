import test from "node:test";
import assert from "node:assert/strict";
import { parseAuthPresentation } from "../packages/frontend/src/app/auth/auth-model.ts";
import { parseMayhemResponse } from "../packages/frontend/src/app/mayhem/mayhem-data.ts";
import { validateCoinDataset } from "../packages/frontend/src/app/explore/coin-data.ts";
test("presentation adapters cannot retain sparse unvalidated inventory slots", () => {
  assert.throws(() =>
    parseAuthPresentation(
      {
        source: "synthetic-test",
        session: "anonymous",
        wallets: new Array(1),
        recentWallet: null,
      },
      true,
    ),
  );
  assert.throws(() =>
    parseMayhemResponse({ source: "synthetic-test", coins: new Array(1) }),
  );
  assert.throws(() => validateCoinDataset(new Array(1)));
  assert.deepEqual(validateCoinDataset([]), []);
});
