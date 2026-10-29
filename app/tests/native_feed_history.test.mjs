import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";
import test from "node:test";

const backend = createRequire(
  new URL("../packages/backend/package.json", import.meta.url),
);

test("local feed routes and actual server-rendered navigation respect the history bound", () => {
  // Use the existing ordinary loader, not the tsx CLI's IPC server. The actual
  // frontend tsconfig supplies its JSX transform; no dependency is installed.
  const env = {
    ...process.env,
    TSX_TSCONFIG_PATH: fileURLToPath(
      new URL("../packages/frontend/tsconfig.json", import.meta.url),
    ),
  };
  // A fresh node --test invocation must not inherit the parent runner's private
  // child transport context; otherwise Node can suppress this child's test run.
  delete env.NODE_TEST_CONTEXT;
  const result = spawnSync(
    process.execPath,
    [
      "--import",
      pathToFileURL(backend.resolve("tsx")).href,
      "--test",
      fileURLToPath(
        new URL("./support/native-feed-history.cjs", import.meta.url),
      ),
    ],
    {
      env,
      encoding: "utf8",
      timeout: 30_000,
      maxBuffer: 1_048_576,
    },
  );
  assert.ifError(result.error);
  assert.equal(result.signal, null, result.stderr);
  assert.equal(result.status, 0, `${result.stdout}\n${result.stderr}`);
  assert.match(result.stdout, /# pass 4|ℹ pass 4/u);
});
