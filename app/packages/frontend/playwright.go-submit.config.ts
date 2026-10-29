import { defineConfig } from "@playwright/test";
import { acceptedClickwrapState } from "./tests/browser-state";

export default defineConfig({
  testDir: "./tests",
  testMatch: ["go-pending-submit.flow.ts", "go-submit-controls.flow.ts", "go.spec.ts"],
  outputDir: "../../artifacts/playwright-go-submit",
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  reporter: "line",
  use: {
    baseURL: "http://127.0.0.1:3010",
    browserName: "chromium",
    storageState: acceptedClickwrapState,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: {
    command:
      "corepack pnpm exec next dev --turbopack --hostname 127.0.0.1 --port 3010",
    url: "http://127.0.0.1:3010",
    reuseExistingServer: false,
    timeout: 120000,
    env: { PUMPFUN_DEVELOPER_API_KEY: "" },
  },
});
