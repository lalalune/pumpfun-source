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
test("closing during discovery cannot install a new registry lifetime", () => {
  const f = fixture();
  const stop = f.controller.subscribe(() => {
    if (f.controller.getSnapshot().status === "choosing")
      f.controller.dispose();
  });
  try {
    f.controller.discover();
    assert.equal(f.counts().ready, 0);
    assert.equal(f.controller.getSnapshot().status, "idle");
  } finally {
    stop();
    f.controller.dispose();
  }
});
test("closing during connect or disconnect publication stops provider dispatch", async () => {
  for (const phase of ["connecting", "disconnecting"]) {
    const f = fixture();
    f.controller.discover();
    if (phase === "disconnecting") await f.controller.connect(0);
    const stop = f.controller.subscribe(() => {
      if (f.controller.getSnapshot().status === phase) f.controller.dispose();
    });
    try {
      if (phase === "connecting") await f.controller.connect(0);
      else await f.controller.disconnect();
      assert.equal(
        f.counts()[phase === "connecting" ? "connects" : "disconnects"],
        0,
      );
      assert.equal(f.controller.getSnapshot().status, "idle");
    } finally {
      stop();
      f.controller.dispose();
    }
  }
});
