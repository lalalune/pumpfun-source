import { defineConfig } from "../../packages/frontend/node_modules/@playwright/test/index.mjs";
import { acceptedClickwrapState } from "../../packages/frontend/tests/browser-state.ts";
const phase = process.env.PUMP_REFRESH_PHASE ?? "fixed";
const port = Number(process.env.PUMP_REFRESH_PORT ?? 3027);
const root =
  process.env.PUMP_REFRESH_OUTPUT_DIR ??
  new URL("../../artifacts/competition-refresh/" + phase + "/", import.meta.url)
    .pathname;
export default defineConfig({
  testDir: ".",
  testMatch: "competition-refresh.spec.mts",
  outputDir: root + "/output",
  timeout: 110_000,
  forbidOnly: true,
  workers: 1,
  retries: 0,
  fullyParallel: false,
  reporter: "line",
  use: {
    baseURL: "http://127.0.0.1:" + port,
    storageState: acceptedClickwrapState,
    browserName: "chromium",
    headless: true,
    launchOptions: {
      executablePath:
        process.env.PUMP_REFRESH_CHROMIUM ??
        "/home/agent/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome",
    },
    screenshot: "only-on-failure",
    video: "on",
    trace: "off",
  },
});
