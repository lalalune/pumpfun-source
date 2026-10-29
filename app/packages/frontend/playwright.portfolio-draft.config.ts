import { defineConfig } from "@playwright/test";
import base from "./playwright.config";

export default defineConfig({
  ...base,
  testMatch: ["portfolio-draft.spec.ts"],
  outputDir: "../../artifacts/playwright-portfolio-draft",
  use: { ...base.use, baseURL: "http://127.0.0.1:3065" },
  webServer: {
    command: "pnpm exec next dev --turbopack --hostname 127.0.0.1 --port 3065",
    url: "http://127.0.0.1:3065",
    reuseExistingServer: false,
    timeout: 120_000,
    env: { PUMPFUN_DEVELOPER_API_KEY: "", SOLANA_RPC_URL: "" },
  },
});
