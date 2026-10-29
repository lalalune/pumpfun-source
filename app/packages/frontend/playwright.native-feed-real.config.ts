import { defineConfig } from "@playwright/test";
import { acceptedClickwrapState } from "./tests/browser-state";

export default defineConfig({
  testDir: "./tests",
  testMatch: "native-home-feed-real.spec.ts",
  outputDir: "../../artifacts/playwright-native-feed-real",
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  reporter: "line",
  use: {
    baseURL: "http://127.0.0.1:3012",
    browserName: "chromium",
    storageState: acceptedClickwrapState,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
});
