import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import {
  copyFile,
  mkdir,
  mkdtemp,
  readFile,
  rm,
  symlink,
  writeFile,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import prettier from "prettier";
import { publishGraph } from "../scripts/factory-graph/core.mjs";

const output = "research/turbopack-route-graph-20261028";
const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");

async function workspace(t) {
  const root = await mkdtemp(join(tmpdir(), "graph-summary-cli-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  for (const relative of [
    "scripts/factory-graph",
    "recovered/modules",
    "contracts",
    "evidence/web/objects",
  ])
    await mkdir(join(root, relative), { recursive: true });
  for (const name of ["cli.mjs", "core.mjs"])
    await copyFile(
      new URL(`../scripts/factory-graph/${name}`, import.meta.url),
      join(root, "scripts/factory-graph", name),
    );
  await symlink(
    fileURLToPath(new URL("../node_modules", import.meta.url)),
    join(root, "node_modules"),
    process.platform === "win32" ? "junction" : "dir",
  );

  // One inert multiline template satisfies the CLI's unchanged default source
  // budget without thousands of factories or a test-only analyzer/flag override.
  // It is synthetic input, never executed and never a recovered-source count.
  const raw = `(e)=>{const value=\`${"line\n".repeat(250_000)}\`;e.s(["value",0,value])}`;
  const source = `globalThis.TURBOPACK.push(["synthetic",1,${raw}]);`;
  const capturePath = "evidence/web/objects/source.js";
  const url = "https://example.invalid/source.js";
  const hash = digest(raw);
  const formattedPath = `recovered/modules/1-${hash.slice(0, 12)}.js`;
  await writeFile(join(root, capturePath), source);
  await writeFile(
    join(root, formattedPath),
    "// Recovered Turbopack factory. Requires original runtime/import IDs; not a standalone source module.\n" +
      (await prettier.format(`(${raw});`, { parser: "babel" })),
  );
  await writeFile(
    join(root, "recovered/modules.json"),
    JSON.stringify({
      rangeEncoding:
        "UTF-16 code-unit half-open offsets in UTF-8 decoded source",
      failures: [],
      modules: [
        {
          ids: [1],
          sha256: hash,
          path: formattedPath,
          origins: [
            {
              source: capturePath,
              url,
              start: source.indexOf(raw),
              end: source.indexOf(raw) + raw.length,
            },
          ],
        },
      ],
    }),
  );
  await writeFile(
    join(root, "evidence/web/manifest.json"),
    JSON.stringify({
      records: [
        {
          status: 200,
          path: capturePath,
          url,
          sha256: digest(source),
          bytes: Buffer.byteLength(source),
        },
      ],
    }),
  );
  await writeFile(
    join(root, "contracts/internal-operations.json"),
    JSON.stringify({ operations: [] }),
  );
  await writeFile(
    join(root, "contracts/developer-bindings.json"),
    JSON.stringify({ bindings: [] }),
  );
  return root;
}

function summary(root) {
  const result = spawnSync(
    process.execPath,
    [join(root, "scripts/factory-graph/cli.mjs"), "summary"],
    { encoding: "utf8", timeout: 40_000 },
  );
  assert.ifError(result.error);
  return result;
}

test("summary distinguishes a first-run graph from a broken existing packet", async (t) => {
  const root = await workspace(t);
  let expected;
  await t.test(
    "absent packet performs real default-budget analysis without publishing",
    async () => {
      const result = summary(root);
      assert.equal(result.status, 0, result.stderr);
      expected = JSON.parse(result.stdout);
      assert.equal(expected.uniqueFactories, 1);
      assert.ok(expected.analyzedLines >= 250_000);
      await assert.rejects(readFile(join(root, output, "GRAPH-SUMMARY.json")), {
        code: "ENOENT",
      });
    },
  );
  const packet = await publishGraph(root, output);
  const target = join(root, output, "GRAPH-SUMMARY.json");
  const original = await readFile(target);
  const manifest = await readFile(join(root, output, "MANIFEST.json"));
  await t.test("valid retained summary stays readable", () => {
    const result = summary(root);
    assert.equal(result.status, 0, result.stderr);
    assert.deepEqual(JSON.parse(result.stdout), expected);
    assert.deepEqual(packet.summary, expected);
  });
  await t.test(
    "malformed retained JSON reports its error instead of a fresh success",
    async () => {
      const malformed = "{ broken retained summary";
      await writeFile(target, malformed);
      try {
        const result = summary(root);
        assert.notEqual(result.status, 0, result.stdout);
        assert.match(result.stderr, /SyntaxError/);
        assert.equal(result.stdout, "");
        assert.equal(await readFile(target, "utf8"), malformed);
        assert.deepEqual(
          await readFile(join(root, output, "MANIFEST.json")),
          manifest,
        );
      } finally {
        await writeFile(target, original);
      }
    },
  );
  await t.test(
    "missing summary inside an existing packet is not a first run",
    async () => {
      await rm(target);
      try {
        const result = summary(root);
        assert.notEqual(result.status, 0, result.stdout);
        assert.match(result.stderr, /ENOENT[\s\S]*GRAPH-SUMMARY\.json/);
        assert.equal(result.stdout, "");
        await assert.rejects(readFile(target), { code: "ENOENT" });
        assert.deepEqual(
          await readFile(join(root, output, "MANIFEST.json")),
          manifest,
        );
      } finally {
        await writeFile(target, original);
      }
    },
  );
});
