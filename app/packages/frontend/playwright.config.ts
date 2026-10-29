import { defineConfig } from "@playwright/test";
import { acceptedClickwrapState } from "./tests/browser-state";

export default defineConfig({
  testDir: "./tests",
  testIgnore: ["native-home-feed.spec.ts", "native-home-feed-real.spec.ts"],
  outputDir: "../../artifacts/playwright",
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  reporter: "line",
  use: {
    baseURL: "http://127.0.0.1:3010",
    browserName: "chromium",
    // Existing page cases explicitly exercise an already-closed local browser state.
    // clickwrap.spec.ts overrides this fixture with an empty first-visit state.
    storageState: acceptedClickwrapState,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "pnpm exec next dev --turbopack --hostname 127.0.0.1 --port 3010",
    url: "http://127.0.0.1:3010",
    reuseExistingServer: false,
    timeout: 120_000,
    env: {
      PUMPFUN_DEVELOPER_API_KEY: "",
    },
  },
});
