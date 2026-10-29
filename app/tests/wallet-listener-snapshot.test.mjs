import test from "node:test";
import assert from "node:assert/strict";
import { PublicWalletController } from "../packages/frontend/src/app/auth/public-wallet/controller.ts";
test("listeners added during a wallet publication wait for its next event", () => {
  const c = new PublicWalletController(new EventTarget());
  const seen = [];
  const late = () => seen.push("late");
  c.subscribe(() => {
    seen.push("first");
    c.subscribe(late);
  });
  try {
    c.forget();
    assert.deepEqual(seen, ["first"]);
    c.forget();
    assert.deepEqual(seen, ["first", "first", "late"]);
  } finally {
    c.dispose();
  }
});
