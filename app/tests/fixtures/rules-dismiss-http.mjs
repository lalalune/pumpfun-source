import { spawn } from "node:child_process";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
export async function startRulesDismissHttp() {
  const require = createRequire(
    path.join(APP, "packages/backend/package.json"),
  );
  const child = spawn(
    process.execPath,
    [
      "--import",
      require.resolve("tsx"),
      path.join(APP, "tests/fixtures/rules-dismiss-server.mts"),
    ],
    {
      cwd: APP,
      env: {
        PATH: process.env.PATH ?? "/usr/bin",
        NODE_ENV: "test",
        TZ: "UTC",
        PUMPFUN_DEVELOPER_API_KEY: `pf_live_${"A".repeat(49)}`,
      },
      stdio: ["ignore", "pipe", "pipe", "ipc"],
    },
  );
  let errors = "",
    next = 0,
    closed = false;
  const pending = new Map();
  child.stderr.on("data", (data) => (errors += data));
  let readyResolve, readyReject;
  const ready = new Promise((resolve, reject) => {
    readyResolve = resolve;
    readyReject = reject;
  });
  const timeout = setTimeout(() => {
    child.kill("SIGTERM");
    readyReject(Error("Fixture startup deadline: " + errors));
  }, 15000);
  child.on("message", (data) => {
    if (data.event === "ready") {
      clearTimeout(timeout);
      readyResolve(data);
    } else if (pending.has(data.id)) {
      pending.get(data.id).resolve(data);
      pending.delete(data.id);
    }
  });
  const exited = new Promise((resolve) =>
    child.once("exit", (code) => {
      closed = true;
      clearTimeout(timeout);
      readyReject(Error("Fixture exited " + code + ": " + errors));
      for (const item of pending.values()) item.reject(Error("Fixture exited"));
      pending.clear();
      resolve(code);
    }),
  );
  child.once("error", (error) => {
    clearTimeout(timeout);
    readyReject(error);
  });
  function snapshot() {
    return new Promise((resolve, reject) => {
      if (closed) return reject(Error("Fixture closed"));
      const id = ++next;
      const timer = setTimeout(() => {
        pending.delete(id);
        reject(Error("Fixture IPC deadline"));
        child.kill("SIGTERM");
      }, 5000);
      pending.set(id, {
        resolve: (data) => {
          clearTimeout(timer);
          resolve(data);
        },
        reject: (error) => {
          clearTimeout(timer);
          reject(error);
        },
      });
      child.send({ id, command: "snapshot" });
    });
  }
  const info = await ready;
  return {
    backendUrl: info.url,
    snapshot,
    async close() {
      if (!closed) child.send({ id: ++next, command: "close" });
      const code = await exited;
      if (code !== 0) throw Error("Fixture exit " + code);
    },
  };
}
