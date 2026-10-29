import { defineConfig } from "../../packages/frontend/node_modules/@playwright/test/index.mjs";
import { acceptedClickwrapState } from "../../packages/frontend/tests/browser-state.ts";
const phase = process.env.PUMP_RULES_PHASE ?? "fixed";
const output =
  process.env.PUMP_RULES_OUTPUT ??
  new URL("../../artifacts/rules-dismiss/" + phase + "/", import.meta.url)
    .pathname;
export default defineConfig({
  testDir: ".",
  testMatch: "rules-dismiss.spec.mts",
  outputDir: output + "/output",
  workers: 1,
  retries: 0,
  forbidOnly: true,
  fullyParallel: false,
  reporter: "line",
  use: {
    baseURL: "http://127.0.0.1:" + Number(process.env.PUMP_RULES_PORT ?? 3027),
    storageState: acceptedClickwrapState,
    browserName: "chromium",
    headless: true,
    launchOptions: {
      executablePath:
        "/home/agent/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome",
    },
    trace: "off",
    screenshot: "only-on-failure",
  },
});
