import { defineConfig } from "@playwright/test";
import { acceptedClickwrapState } from "./tests/browser-state";
export default defineConfig({
  testDir: "./tests",
  testMatch: ["quote-preview.flow.ts", "home-feed.spec.ts"],
  outputDir: "../../artifacts/playwright-quote-preview",
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
  webServer: {
    command:
      "corepack pnpm exec next dev --turbopack --hostname 127.0.0.1 --port 3016",
    url: "http://127.0.0.1:3016",
    reuseExistingServer: false,
    timeout: 120000,
    env: { PUMPFUN_DEVELOPER_API_KEY: "", PUMP_LOCAL_HOME_FEED: "" },
  },
});
