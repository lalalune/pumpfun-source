import { spawn } from "node:child_process";
import { createWriteStream } from "node:fs";
import { mkdir, writeFile } from "node:fs/promises";
import { finished } from "node:stream/promises";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const FRONT = path.join(APP, "packages/frontend");
const require = createRequire(path.join(FRONT, "package.json"));
export async function startCompetitionRefreshNext({
  backendUrl,
  port,
  outputDir,
}) {
  if (!Number.isInteger(port) || port < 1024 || port > 65535)
    throw new Error("Explicit coordinated high port required");
  const backend = new URL(backendUrl);
  if (backend.hostname !== "127.0.0.1" || backend.protocol !== "http:")
    throw new Error("Owned loopback fixture required");
  await mkdir(outputDir, { recursive: true });
  const output = createWriteStream(path.join(outputDir, "next.log"));
  const argv = [
    require.resolve("next/dist/bin/next"),
    "dev",
    "--webpack",
    "--hostname",
    "127.0.0.1",
    "--port",
    String(port),
  ];
  const child = spawn(process.execPath, argv, {
    cwd: FRONT,
    env: {
      PATH: process.env.PATH ?? "/usr/bin",
      NODE_ENV: "development",
      CI: "1",
      NEXT_TELEMETRY_DISABLED: "1",
      BACKEND_URL: "http://127.0.0.1:3028",
      PUMPFUN_DEVELOPER_API_KEY: `pf_live_${"A".repeat(49)}`,
      PUMP_TEST_UPSTREAM_URL: backendUrl,
      NODE_OPTIONS:
        "--import=" +
        path.join(APP, "tests/fixtures/competition-refresh-next-fetch.mjs"),
    },
    stdio: ["pipe", "pipe", "pipe"],
  });
  let startupText = "",
    ownReady = false,
    spawnError;
  child.stdout.on("data", (data) => {
    startupText = (startupText + data).slice(-8000);
    if (startupText.includes("Ready in")) ownReady = true;
  });
  child.once("error", (error) => {
    spawnError = error;
  });
  child.stdout.pipe(output, { end: false });
  child.stderr.pipe(output, { end: false });
  let ended = false;
  let closeResult;
  const closed = new Promise((resolve) =>
    child.once("close", (code, signal) => {
      ended = true;
      closeResult = { code, signal };
      resolve(closeResult);
    }),
  );
  const onExit = () => {
    if (!ended) child.kill("SIGTERM");
  };
  process.once("exit", onExit);
  async function close() {
    if (!ended) {
      child.kill("SIGINT");
      const timer = setTimeout(() => {
        if (!ended) child.kill("SIGKILL");
      }, 5000);
      await closed;
      clearTimeout(timer);
    }
    process.removeListener("exit", onExit);
    output.end();
    await finished(output);
    return closeResult;
  }
  const baseURL = "http://127.0.0.1:" + port;
  try {
    const until = Date.now() + 15000;
    while (!ownReady) {
      if (spawnError) throw spawnError;
      if (ended) throw new Error("Owned Next exited during startup");
      if (Date.now() >= until)
        throw new Error("Owned Next did not announce readiness");
      await new Promise((resolve) => setTimeout(resolve, 200));
    }
    const response = await fetch(baseURL + "/leaderboard", {
      signal: AbortSignal.timeout(45000),
    });
    if (!response.ok || ended)
      throw new Error("Owned Next page startup failed: " + response.status);
    await writeFile(
      path.join(outputDir, "server.json"),
      JSON.stringify(
        {
          pid: child.pid,
          argv,
          cwd: FRONT,
          baseURL,
          backendUrl,
          testOnlyPreload: "tests/fixtures/competition-refresh-next-fetch.mjs",
          credentials:
            "explicit public synthetic test-key format, never read from parent environment",
        },
        null,
        2,
      ) + "\n",
    );
  } catch (error) {
    await close();
    throw error;
  }
  return { baseURL, pid: child.pid, close };
}
