import { defineConfig } from "../../packages/frontend/node_modules/@playwright/test/index.mjs";
import { acceptedClickwrapState } from "../../packages/frontend/tests/browser-state.ts";
const phase = process.env.PUMP_PROFILE_PHASE ?? "fixed";
const output =
  process.env.PUMP_PROFILE_OUTPUT ??
  new URL("../../artifacts/profile-link/" + phase + "/", import.meta.url)
    .pathname;
export default defineConfig({
  testDir: ".",
  testMatch: "profile-link.spec.mts",
  outputDir: output + "/output",
  workers: 1,
  retries: 0,
  fullyParallel: false,
  forbidOnly: true,
  reporter: "line",
  use: {
    baseURL:
      "http://127.0.0.1:" + Number(process.env.PUMP_PROFILE_PORT ?? 3027),
    storageState: acceptedClickwrapState,
    browserName: "chromium",
    headless: true,
    launchOptions: {
      executablePath:
        "/home/agent/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome",
    },
    screenshot: "only-on-failure",
    trace: "off",
  },
});
