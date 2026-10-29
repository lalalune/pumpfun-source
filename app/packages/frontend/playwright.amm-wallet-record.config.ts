import { defineConfig } from "@playwright/test";
import base from "./playwright.config";
const server = base.webServer;
if (!server || Array.isArray(server))
  throw new Error("Expected one controlled fixture server");
export default defineConfig({
  ...base,
  testMatch: ["amm-wallet-record.spec.ts", "wallet-program-record.spec.ts"],
  webServer: {
    ...server,
    command:
      "node tests/with-amm-record-fixture.mjs pnpm exec next dev --turbopack --hostname 127.0.0.1 --port 3010",
    env: {
      ...server.env,
      SOLANA_RPC_URL: "",
      AMM_RECORD_FIXTURE_TEST: "1",
    },
  },
});
