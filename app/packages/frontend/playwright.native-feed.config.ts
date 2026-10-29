import { defineConfig } from "@playwright/test";
import { acceptedClickwrapState } from "./tests/browser-state";

export default defineConfig({
  testDir: "./tests",
  testMatch: "native-home-feed.spec.ts",
  outputDir: "../../artifacts/playwright-native-feed",
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  reporter: "line",
  use: {
    baseURL: "http://127.0.0.1:3011",
    browserName: "chromium",
    storageState: acceptedClickwrapState,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "node tests/support/native-feed-server.mjs",
      url: "http://127.0.0.1:3001/__health",
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command:
        "pnpm exec next dev --turbopack --hostname 127.0.0.1 --port 3011",
      url: "http://127.0.0.1:3011",
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        PUMPFUN_DEVELOPER_API_KEY: "",
        PUMP_LOCAL_HOME_FEED: "enabled",
      },
    },
  ],
});
