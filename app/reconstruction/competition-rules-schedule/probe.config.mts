import { defineConfig } from "../../packages/frontend/node_modules/@playwright/test/index.mjs";
import { acceptedClickwrapState } from "../../packages/frontend/tests/browser-state.ts";
const phase = process.env.PUMP_SCHEDULE_PHASE ?? "fixed";
const output =
  process.env.PUMP_SCHEDULE_OUTPUT ??
  new URL("../../artifacts/rules-schedule/" + phase + "/", import.meta.url)
    .pathname;
export default defineConfig({
  testDir: ".",
  testMatch: "probe.mts",
  outputDir: output + "/output",
  workers: 1,
  retries: 0,
  fullyParallel: false,
  forbidOnly: true,
  reporter: "line",
  use: {
    baseURL: "http://127.0.0.1:" + Number(process.env.PUMP_RULES_PORT ?? 3027),
    storageState: acceptedClickwrapState,
    browserName: "chromium",
    headless: true,
    launchOptions: {
      executablePath:
        process.env.PUMP_SCHEDULE_CHROMIUM ??
        "/home/agent/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome",
    },
    trace: "off",
    screenshot: "only-on-failure",
  },
});
