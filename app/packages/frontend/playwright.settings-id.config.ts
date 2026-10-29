import { defineConfig } from "@playwright/test";
import { acceptedClickwrapState } from "./tests/browser-state";
const baseURL = process.env.PUMP_SETTINGS_BASE ?? "http://127.0.0.1:3027";
export default defineConfig({
  testDir: "./tests",
  testMatch: "settings-identifier-search.spec.ts",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 30000,
  outputDir:
    process.env.PUMP_SETTINGS_OUTPUT ??
    "../../artifacts/settings-identifier-search",
  reporter: "line",
  use: {
    baseURL,
    browserName: "chromium",
    trace: "off",
    screenshot: "off",
    storageState: {
      cookies: [],
      origins: acceptedClickwrapState.origins.map((entry) => ({
        ...entry,
        origin: new URL(baseURL).origin,
      })),
    },
  },
});
