import { defineConfig } from "@playwright/test";
import base from "./playwright.config";
const server = base.webServer;
if (!server || Array.isArray(server))
  throw new Error("Expected one isolated fixture server");
export default defineConfig({
  ...base,
  testMatch: [
    "global-incentive-record.spec.ts",
    "wallet-program-record.spec.ts",
  ],
  webServer: {
    ...server,
    stdout: "pipe",
    stderr: "pipe",
    gracefulShutdown: { signal: "SIGTERM", timeout: 10_000 },
    command:
      "node tests/with-global-record-fixture.mjs node node_modules/next/dist/bin/next dev --turbopack --hostname 127.0.0.1 --port 3010",
    env: { ...server.env, SOLANA_RPC_URL: "", GLOBAL_RECORD_FIXTURE_TEST: "1" },
  },
});
