import { defineConfig } from "@playwright/test";
import base from "./playwright.config";
const server = base.webServer;
if (!server || Array.isArray(server))
  throw new Error("Expected one isolated server");
export default defineConfig({
  ...base,
  testMatch: ["portfolio-activity-independent.spec.ts"],
  use: { ...base.use, baseURL: "http://127.0.0.1:3027" },
  webServer: {
    ...server,
    command: "pnpm exec next dev --turbopack --hostname 127.0.0.1 --port 3027",
    url: "http://127.0.0.1:3027",
    env: { ...server.env, SOLANA_RPC_URL: "" },
  },
});
