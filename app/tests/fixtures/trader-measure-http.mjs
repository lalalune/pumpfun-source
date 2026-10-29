import { spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const backendRequire = createRequire(
  path.join(APP, "packages/backend/package.json"),
);
export async function startTraderMeasureHttp() {
  const child = spawn(
    process.execPath,
    [
      "--import",
      backendRequire.resolve("tsx"),
      path.join(APP, "tests/fixtures/trader-measure-server.mts"),
    ],
    {
      cwd: APP,
      env: {
        PATH: process.env.PATH ?? "/usr/bin",
        PUMPFUN_DEVELOPER_API_KEY: `pf_live_${"A".repeat(49)}`,
        NODE_ENV: "test",
        TZ: "UTC",
      },
      stdio: ["pipe", "pipe", "pipe"],
    },
  );
  let stderr = "",
    next = 0,
    closed = false;
  const pending = new Map();
  child.stderr.on("data", (b) => {
    stderr += b;
  });
  let resolveReady, rejectReady;
  const ready = new Promise((resolve, reject) => {
    resolveReady = resolve;
    rejectReady = reject;
  });
  let resolveExit;
  const exited = new Promise((resolve) => {
    resolveExit = resolve;
  });
  const timer = setTimeout(() => {
    child.kill("SIGTERM");
    rejectReady(new Error("Loopback fixture startup timeout: " + stderr));
  }, 20_000);
  createInterface({ input: child.stdout }).on("line", (line) => {
    let message;
    try {
      message = JSON.parse(line);
    } catch {
      return;
    }
    if (message.event === "ready") {
      clearTimeout(timer);
      resolveReady(message);
    } else if (message.event === "error") {
      for (const item of pending.values())
        item.reject(new Error("Fixture controller failed"));
      pending.clear();
      child.kill("SIGTERM");
    } else if (pending.has(message.id)) {
      pending.get(message.id).resolve(message);
      pending.delete(message.id);
    }
  });
  child.on("error", (error) => {
    clearTimeout(timer);
    rejectReady(error);
  });
  child.on("exit", (code) => {
    closed = true;
    clearTimeout(timer);
    resolveExit(code);
    rejectReady(new Error("Fixture exit " + code + ": " + stderr));
    for (const item of pending.values())
      item.reject(new Error("Fixture exited"));
    pending.clear();
  });
  const command = (command) =>
    new Promise((resolve, reject) => {
      if (closed) {
        reject(new Error("Fixture closed"));
        return;
      }
      const id = ++next;
      const deadline = setTimeout(() => {
        pending.delete(id);
        child.kill("SIGTERM");
        reject(new Error("Fixture command timeout"));
      }, 8_000);
      pending.set(id, {
        resolve: (value) => {
          clearTimeout(deadline);
          resolve(value);
        },
        reject: (error) => {
          clearTimeout(deadline);
          reject(error);
        },
      });
      child.stdin.write(JSON.stringify({ id, command }) + "\n");
    });
  const info = await ready;
  return {
    ...info,
    command,
    async close() {
      if (!closed) await command("close");
      const code = await exited;
      if (code !== 0) throw new Error("Fixture close exit " + code);
    },
    getStderr: () => stderr,
  };
}
