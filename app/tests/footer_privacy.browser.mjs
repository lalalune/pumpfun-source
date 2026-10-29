// Authored local UI qualification. Never executes captured code or contacts upstream.
import assert from "node:assert/strict";
import {
  readFile,
  writeFile,
  mkdir,
  rm,
  readdir,
  copyFile,
} from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import { promisify } from "node:util";
import { execFile } from "node:child_process";
import {
  verify,
  appBrowserInputs,
  appBrowserCaseTitles,
} from "../scripts/original-privacy-external-links.mjs";

const root = fileURLToPath(new URL("..", import.meta.url));
const args = process.argv.slice(2);
const option = (name) => {
  const i = args.indexOf(name);
  assert.ok(i >= 0 && args[i + 1], `Missing ${name}`);
  return args[i + 1];
};
const base = new URL(option("--base-url"));
assert.ok(
  base.protocol === "http:" &&
    base.hostname === "127.0.0.1" &&
    !base.username &&
    !base.password,
  "Explicit loopback HTTP app required",
);
const output = path.resolve(option("--output"));
const directory = path.dirname(output);
const frontend = path.join(root, "packages/frontend");
const artifacts = path.join(directory, "artifacts");
const config = path.join(frontend, `.footer-privacy-${process.pid}.config.ts`);
const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");
const inputs = {};
for (const relative of appBrowserInputs)
  inputs[relative] = digest(await readFile(path.join(root, relative)));
await mkdir(directory, { recursive: true });
await writeFile(
  path.join(directory, "execution-inputs.json"),
  JSON.stringify(
    {
      sourceInputs: inputs,
      baseURL: base.origin,
      scope:
        "Declared source/test files before actual execution; no pass claim",
    },
    null,
    2,
  ) + "\n",
);
await verify(root);
const configuration = `import { defineConfig } from '@playwright/test';
import base from './playwright.config';
export default defineConfig({ ...base, testMatch: 'footer-privacy.spec.ts', outputDir: ${JSON.stringify(artifacts)}, use: { ...base.use, baseURL: ${JSON.stringify(base.origin)} }, webServer: undefined });\n`;
await writeFile(config, configuration);
await writeFile(path.join(directory, "execution-config.txt"), configuration);
let result;
try {
  result = await promisify(execFile)(
    process.execPath,
    [
      path.join(frontend, "node_modules/@playwright/test/cli.js"),
      "test",
      "--config",
      config,
      "--reporter=json",
      "--max-failures=1",
    ],
    { cwd: frontend, maxBuffer: 20 * 1024 * 1024 },
  );
} catch (error) {
  await writeFile(
    path.join(directory, "playwright-report.json"),
    error.stdout ?? "",
  );
  await writeFile(
    path.join(directory, "playwright-stderr.log"),
    error.stderr ?? "",
  );
  throw error;
} finally {
  await rm(config, { force: true });
}
await writeFile(path.join(directory, "playwright-report.json"), result.stdout);
await writeFile(path.join(directory, "playwright-stderr.log"), result.stderr);
const report = JSON.parse(result.stdout);
const specs = [];
function walkSuites(suites) {
  for (const suite of suites ?? []) {
    specs.push(...(suite.specs ?? []));
    walkSuites(suite.suites);
  }
}
walkSuites(report.suites);
assert.deepEqual(
  specs.map((spec) => spec.title),
  appBrowserCaseTitles,
);
const data = [];
for (const spec of specs) {
  assert.equal(spec.tests.length, 1);
  const attempt = spec.tests[0].results.at(-1);
  assert.equal(attempt.status, "passed", spec.title);
  const attachment = attempt.attachments.find(
    (item) => item.name === "footer-workflow-evidence",
  );
  assert.ok(attachment, `Missing evidence: ${spec.title}`);
  const bytes = attachment.body
    ? Buffer.from(attachment.body, "base64")
    : await readFile(attachment.path);
  data.push(JSON.parse(bytes.toString("utf8")));
}
async function filesBelow(folder) {
  const files = [];
  for (const item of await readdir(folder, { withFileTypes: true })) {
    const file = path.join(folder, item.name);
    if (item.isDirectory()) files.push(...(await filesBelow(file)));
    else if (item.isFile()) files.push(file);
  }
  return files;
}
const files = await filesBelow(artifacts);
const screenshots = {};
for (const name of [
  "footer-desktop.png",
  "footer-mobile.png",
  "footer-storage-failure.png",
]) {
  const matches = files.filter((file) => path.basename(file) === name);
  assert.equal(matches.length, 1, name);
  const target = path.join(directory, name);
  await copyFile(matches[0], target);
  screenshots[name] = digest(await readFile(target));
}
for (const relative of appBrowserInputs)
  assert.equal(
    digest(await readFile(path.join(root, relative))),
    inputs[relative],
    `Input changed during execution: ${relative}`,
  );
const pageErrors = data.flatMap((item) => item.pageErrors);
const consoleErrors = data.flatMap((item) => item.consoleErrors);
assert.deepEqual(pageErrors, []);
assert.deepEqual(consoleErrors, []);
const nativeFallbacks = data.flatMap((item) => item.nativeFallbacks);
assert.equal(nativeFallbacks.length, 1);
const openRefusals = data.reduce((n, item) => n + item.openRefusals, 0);
assert.equal(openRefusals, 2);
const storageRefusals = data.reduce((n, item) => n + item.storageRefusals, 0);
assert.ok(storageRefusals >= 1);
const routedExternal = data.flatMap((item) => item.routedExternal);
assert.ok(
  routedExternal.every(
    (item) => item.action === "fulfilled" && item.method === "GET",
  ),
);
const receipt = {
  result: "PASS",
  sourceInputs: inputs,
  screenshots,
  passed: specs.length,
  failed: 0,
  skipped: 0,
  checks: appBrowserCaseTitles,
  browser: [...new Set(data.map((item) => item.browserVersion))],
  browserProcessRestarts: 0,
  reloadsExercised: true,
  pageErrors,
  consoleErrors,
  nativeFallbacks,
  openRefusals,
  storageRefusals,
  routedExternal,
  capturedCodeExecuted: false,
  outboundConsumersExercised: true,
  upstreamRequestsPerformed: false,
  upstreamFlagRolloutClaimed: false,
  serverCompatibilityClaimed: false,
  scope:
    "Local interactive footer clicks and shared device setting; explicit window ports and synthetically fulfilled native fallback pages, not original delivery or server compatibility",
};
await writeFile(output, JSON.stringify(receipt, null, 2) + "\n");
console.log(
  JSON.stringify(
    { result: receipt.result, checks: receipt.passed, output },
    null,
    2,
  ),
);
