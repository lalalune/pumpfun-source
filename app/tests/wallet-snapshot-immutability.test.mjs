import test from "node:test";
import assert from "node:assert/strict";
import { PublicWalletController } from "../packages/frontend/src/app/auth/public-wallet/controller.ts";
function fixture() {
  const target = new EventTarget();
  const controller = new PublicWalletController(target, 1000);
  let connects = 0,
    disconnects = 0,
    ready = 0;
  const wallet = {
    version: "1.0.0",
    name: "Synthetic wallet",
    chains: ["solana:mainnet"],
    accounts: [
      {
        address: "11111111111111111111111111111111",
        chains: ["solana:mainnet"],
      },
    ],
    features: {
      "standard:connect": {
        version: "1.0.0",
        async connect() {
          connects++;
        },
      },
      "standard:events": {
        version: "1.0.0",
        on() {
          return () => {};
        },
      },
      "standard:disconnect": {
        version: "1.0.0",
        async disconnect() {
          disconnects++;
        },
      },
    },
  };
  target.addEventListener("wallet-standard:app-ready", (e) => {
    ready++;
    e.detail.register(wallet);
  });
  return {
    target,
    controller,
    counts: () => ({ connects, disconnects, ready }),
  };
}
test("snapshot consumers cannot rewrite wallet labels or selections", () => {
  const f = fixture();
  try {
    assert.ok(Object.isFrozen(f.controller.getSnapshot().wallets));
    f.controller.discover();
    const choices = f.controller.getSnapshot().wallets;
    assert.ok(Object.isFrozen(choices));
    assert.ok(Object.isFrozen(choices[0]));
    assert.throws(() => {
      choices[0].id = 99;
    });
    assert.equal(f.controller.getSnapshot().wallets[0].id, 0);
  } finally {
    f.controller.dispose();
  }
});
