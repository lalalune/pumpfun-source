/** Test-only ownership/cleanup pattern derived from the earlier AMM reader PR #1488. */
/** Opt-in temporary test route. Never overwrite or delete an unrelated route. */
import { createHash } from "node:crypto";
import { spawn } from "node:child_process";
import {
  lstat,
  mkdir,
  readFile,
  realpath,
  rmdir,
  unlink,
  writeFile,
} from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

if (process.env.GLOBAL_RECORD_FIXTURE_TEST !== "1") {
  throw new Error(
    "Temporary Global fixture requires explicit GLOBAL_RECORD_FIXTURE_TEST=1 in an isolated test checkout",
  );
}
const [command, ...args] = process.argv.slice(2);
if (!command)
  throw new Error(
    "Pass the existing local test command after with-global-record-fixture.mjs",
  );
const frontend = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const app = join(frontend, "src/app");
if ((await realpath(app)) !== app)
  throw new Error("Test app directory cannot be symlinked");
const directory = join(app, "global-record-test-fixture");
const target = join(directory, "route.ts");
try {
  await lstat(directory);
  throw new Error(
    "Refusing to overwrite pre-existing global-record-test-fixture route",
  );
} catch (error) {
  if (error.code !== "ENOENT") throw error;
}
const bytes = await readFile(
  new URL("global-record-fixture/route.ts.in", import.meta.url),
);
const hash = (value) => createHash("sha256").update(value).digest("hex");
const expected = hash(bytes);
const artifacts = resolve(frontend, "../../artifacts");
await mkdir(artifacts, { recursive: true });
const lifecycle = join(artifacts, `global-record-fixture-${process.pid}.json`);
const receipt = {
  pid: process.pid,
  fixtureSha256: expected,
  target,
  phase: "preparing",
  installedAt: null,
  removedAt: null,
};
await mkdir(directory);
let wrote = false;
let recorded = false;
try {
  await writeFile(target, bytes, { flag: "wx" });
  wrote = true;
  if (hash(await readFile(target)) !== expected)
    throw new Error("Test fixture write verification failed");
  receipt.phase = "installed";
  receipt.installedAt = new Date().toISOString();
  await writeFile(lifecycle, JSON.stringify(receipt, null, 2) + "\n", {
    flag: "wx",
  });
  recorded = true;
  console.log(
    `Installed temporary Global test route; fixture SHA-256 ${expected}; lifecycle ${lifecycle}`,
  );
  const child = spawn(command, args, {
    cwd: frontend,
    stdio: "inherit",
    env: process.env,
  });
  const forward = (signal) => child.kill(signal);
  process.on("SIGINT", forward);
  process.on("SIGTERM", forward);
  try {
    process.exitCode = await new Promise((resolveStatus, reject) => {
      child.once("error", reject);
      child.once("exit", (code, signal) =>
        resolveStatus(code ?? (signal ? 1 : 0)),
      );
    });
  } finally {
    process.off("SIGINT", forward);
    process.off("SIGTERM", forward);
  }
} finally {
  if (wrote) {
    if (hash(await readFile(target)) !== expected) {
      throw new Error(
        "Test fixture changed during execution; refusing to delete changed bytes",
      );
    }
    await unlink(target);
  }
  await rmdir(directory);
  try {
    await lstat(directory);
    throw new Error("Temporary Global fixture cleanup failed");
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }
  if (recorded) {
    receipt.phase = "removed";
    receipt.removedAt = new Date().toISOString();
    await writeFile(lifecycle, JSON.stringify(receipt, null, 2) + "\n");
  }
  console.log(
    `Removed temporary Global test route; fixture SHA-256 ${expected}; lifecycle ${lifecycle}`,
  );
}
