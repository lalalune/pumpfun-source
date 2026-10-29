import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { promisify } from 'node:util';
import { execFile } from 'node:child_process';

const root = '/workspace/pump-app-privacy-links';
const frontend = path.join(root, 'app/packages/frontend');
const args = process.argv.slice(2);
const option = (name) => {
  const at = args.indexOf(name);
  assert.ok(at >= 0 && args[at + 1], `Missing ${name}`);
  return args[at + 1];
};
const base = new URL(option('--base-url'));
assert.equal(base.protocol, 'http:');
assert.equal(base.hostname, '127.0.0.1');
assert.equal(base.username + base.password, '');
const output = path.resolve(option('--output'));
const baseline = args.includes('--baseline');
const config = path.join(frontend, `.settings-clear-focus-${process.pid}.config.ts`);
await mkdir(output, { recursive: true });
const declared = [
  'src/components/settings/settings-control.tsx',
  'src/components/settings/settings.module.css',
  'src/components/settings/settings-model.ts',
  'src/lib/body-scroll-lock.ts',
  'tests/settings-clear-focus.spec.ts',
  'tests/browser-state.ts',
  'playwright.config.ts',
];
const sha = (bytes) => createHash('sha256').update(bytes).digest('hex');
const inputs = {};
for (const relative of declared) inputs[relative] = sha(await readFile(path.join(frontend, relative)));
await writeFile(path.join(output, 'execution-inputs.json'), JSON.stringify({ inputs, baseURL: base.origin, browserRun: 'about-to-run', baseline }, null, 2) + '\n');
const configuration = `import { defineConfig } from '@playwright/test';
import base from './playwright.config';
export default defineConfig({ ...base, testMatch: 'settings-clear-focus.spec.ts', outputDir: ${JSON.stringify(path.join(output, 'artifacts'))}, use: { ...base.use, baseURL: ${JSON.stringify(base.origin)}, trace: 'off' }, webServer: undefined });\n`;
await writeFile(config, configuration);
await writeFile(path.join(output, 'execution-config.txt'), configuration);
let result;
try {
  result = await promisify(execFile)(process.execPath, [
    path.join(frontend, 'node_modules/@playwright/test/cli.js'), 'test', '--config', config,
    '--reporter=json', '--max-failures=2',
    ...(baseline ? ['--grep', '1280px by mouse|390px by keyboard'] : []),
  ], { cwd: frontend, maxBuffer: 8 * 1024 * 1024, timeout: 180_000 });
  result = { ...result, code: 0 };
} catch (error) {
  result = { stdout: error.stdout ?? '', stderr: error.stderr ?? '', code: error.code ?? null };
} finally {
  await rm(config, { force: true });
}
await writeFile(path.join(output, 'report.json'), result.stdout);
await writeFile(path.join(output, 'stderr.log'), result.stderr);
for (const relative of declared) assert.equal(sha(await readFile(path.join(frontend, relative))), inputs[relative], `Input changed during run: ${relative}`);
const report = JSON.parse(result.stdout);
const specs = [];
function walk(suite) {
  specs.push(...(suite.specs ?? []));
  for (const child of suite.suites ?? []) walk(child);
}
walk(report);
const observed = [];
for (const spec of specs) {
  const attempt = spec.tests[0].results.at(-1);
  const attachment = attempt.attachments.find((item) => item.name === 'settings-clear-focus-evidence');
  const payload = attachment ? JSON.parse(attachment.body ? Buffer.from(attachment.body, 'base64').toString() : await readFile(attachment.path, 'utf8')) : null;
  observed.push({ title: spec.title, status: attempt.status, error: attempt.error ?? null, payload });
}
const summary = { code: result.code, stats: report.stats, inputs, observed, baseline, productCompatibilityClaimed: false };
await writeFile(path.join(output, 'observed.json'), JSON.stringify(summary, null, 2) + '\n');
console.log(JSON.stringify({ code: result.code, stats: report.stats, outcomes: observed.map(({ title, status, error }) => ({ title, status, error: error?.message })), output }, null, 2));
process.exitCode = result.code === 0 ? 0 : 1;
