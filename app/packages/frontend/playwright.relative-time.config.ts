import { defineConfig } from "@playwright/test";
import { acceptedClickwrapState } from "./tests/browser-state";
export default defineConfig({
  testDir: "./tests",
  testMatch: "relative-time.flow.ts",
  outputDir: "../../artifacts/playwright-relative-time",
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  reporter: "line",
  use: {
    baseURL: "http://127.0.0.1:3016",
    browserName: "chromium",
    storageState: acceptedClickwrapState,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "node tests/support/relative-time-server.mjs",
      url: "http://127.0.0.1:3001/__health",
      reuseExistingServer: false,
      timeout: 30000,
    },
    {
      command:
        "corepack pnpm exec next dev --turbopack --hostname 127.0.0.1 --port 3016",
      url: "http://127.0.0.1:3016",
      reuseExistingServer: false,
      timeout: 120000,
      env: { PUMPFUN_DEVELOPER_API_KEY: "", PUMP_LOCAL_HOME_FEED: "enabled" },
    },
  ],
});
