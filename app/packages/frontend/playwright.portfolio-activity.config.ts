import { defineConfig } from "@playwright/test";
import base from "./playwright.config";
const server = base.webServer;
if (!server || Array.isArray(server))
  throw new Error("Expected one isolated server");
export default defineConfig({
  ...base,
  testMatch: [
    "portfolio-activity-independent.spec.ts",
    "portfolio.spec.ts",
    "wallet-program-record.spec.ts",
  ],
  use: { ...base.use, baseURL: "http://127.0.0.1:3010" },
  webServer: {
    ...server,
    command: "pnpm exec next dev --turbopack --hostname 127.0.0.1 --port 3010",
    url: "http://127.0.0.1:3010",
    env: { ...server.env, SOLANA_RPC_URL: "" },
  },
});
