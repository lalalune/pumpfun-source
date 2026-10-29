import test from "node:test";
import assert from "node:assert/strict";
import { readFile, mkdtemp, mkdir, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { verifyPacket, verifyResponse, deriveTrace } from "./verify.mjs";

const packet = fileURLToPath(new URL("./", import.meta.url));
const appRoot = fileURLToPath(new URL("../../", import.meta.url));
const load = async (name) => readFile(path.join(packet, name));
const [responseBytes, body, traceBytes, collector] = await Promise.all(
  ["RESPONSE.json", "body.bin", "SOURCE-TRACE.json", "capture.py"].map(load),
);
const response = JSON.parse(responseBytes);
const trace = JSON.parse(traceBytes);
const check = (
  record = response,
  bytes = body,
  source = traceBytes,
  code = collector,
) => verifyResponse(record, bytes, source, code);

test("offline full closure authenticates the actual dated one-row response", async () => {
  const result = await verifyPacket(appRoot);
  assert.equal(result.sourceFactories, 8);
  assert.equal(result.response.rows, 1);
  assert.equal(result.networkRequests, 0);
});
test("a changed raw response byte cannot retain the captured digest", () => {
  const changed = Buffer.from(body);
  changed[changed.length - 2] ^= 1;
  assert.throws(() => check(response, changed), /body SHA-256/);
});
test("a different origin or redirected response cannot inherit this request binding", () => {
  for (const field of ["requestedUrl", "responseUrl"])
    assert.throws(
      () =>
        check({
          ...response,
          [field]: "https://example.invalid/coins/mayhem-mode?limit=1",
        }),
      /URL/,
    );
});
test("an authenticated or repeated request cannot inherit the anonymous single-read receipt", () => {
  for (const change of [
    { cookiesSent: true },
    { authorizationSent: true },
    { redirectsAllowed: true },
    { retries: 1 },
    { method: "POST" },
    {
      requestHeaders: { ...response.requestHeaders, Cookie: "synthetic=test" },
    },
  ])
    assert.throws(() => check({ ...response, ...change }));
});
test("the pre-request source trace and executed collector are both immutable inputs", () => {
  assert.throws(
    () => check(response, body, Buffer.concat([traceBytes, Buffer.from(" ")])),
    /source trace SHA-256/,
  );
  assert.throws(
    () =>
      check(
        response,
        body,
        traceBytes,
        Buffer.concat([collector, Buffer.from("\n")]),
      ),
    /collector SHA-256/,
  );
});
test("truncation and cookie-header value retention fail the declared evidence boundary", () => {
  assert.throws(
    () => check({ ...response, truncated: true }),
    /complete captured body/,
  );
  assert.throws(
    () =>
      check({
        ...response,
        headers: [...response.headers, ["set-cookie", "synthetic=test"]],
      }),
    /cookie values stay omitted/,
  );
});
test("actual captured transport corruption fails before source attribution", async (t) => {
  const root = await mkdtemp(path.join(tmpdir(), "mayhem-source-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  const paths = new Set([
    "evidence/web/manifest.json",
    "recovered/modules.json",
    trace.html.record.path,
    ...Object.values(trace.factories).map((value) => value.source),
  ]);
  for (const relative of paths) {
    await mkdir(path.dirname(path.join(root, relative)), { recursive: true });
    await writeFile(
      path.join(root, relative),
      await readFile(path.join(appRoot, relative)),
    );
  }
  const relative = trace.factories[759257].source;
  const original = await readFile(path.join(root, relative), "utf8");
  assert.ok(original.includes("same-origin"));
  await writeFile(
    path.join(root, relative),
    original.replace("same-origin", "include"),
  );
  await assert.rejects(
    deriveTrace(root),
    /hash|digest|SHA|length|bytes|capture/i,
  );
});
