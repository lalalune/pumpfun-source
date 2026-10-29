import fs from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { parse } from "@babel/parser";
import prettier from "prettier";

const defaultRoot = fileURLToPath(new URL("..", import.meta.url));
const factoryBanner =
  "// Recovered Turbopack factory. Requires original runtime/import IDs; not a standalone source module.\n";
const publicationTargets = [
  "recovered/modules",
  "recovered/modules.json",
  "contracts/internal-operations.json",
  "evidence/web/dependency-paths.json",
];

function walk(node, fn) {
  if (!node || typeof node !== "object") return;
  fn(node);
  for (const [key, value] of Object.entries(node)) {
    if (["loc", "start", "end", "extra", "comments", "tokens"].includes(key))
      continue;
    if (Array.isArray(value)) value.forEach((child) => walk(child, fn));
    else if (value && typeof value === "object") walk(value, fn);
  }
}

function containedPath(root, relative) {
  if (typeof relative !== "string" || relative.length === 0) {
    throw new Error("Inventory source has a missing or invalid path");
  }
  const absoluteRoot = path.resolve(root);
  const absolute = path.resolve(absoluteRoot, relative);
  if (
    absolute !== absoluteRoot &&
    !absolute.startsWith(`${absoluteRoot}${path.sep}`)
  ) {
    throw new Error(`Inventory source path escapes the workspace: ${relative}`);
  }
  return absolute;
}

function errorSummary(error) {
  if (error && typeof error === "object" && "code" in error) {
    return String(error.code);
  }
  if (error instanceof Error) return error.message;
  return String(error);
}

function factoryFilename(module) {
  const id = String(module.ids[0] ?? "anonymous");
  if (id === "." || id === ".." || /[\\/\0]/.test(id)) {
    throw new Error(`Unsafe recovered factory identifier: ${id}`);
  }
  return `${id}-${module.sha256.slice(0, 12)}.js`;
}

function* registrationFactories(array, start = 1) {
  // The captured runtime's X(t) registers a leading nested array recursively
  // before the remaining entries. Two-element outer arrays carry metadata.
  if (start === 1 && array.elements.length === 2) return;
  const nested = start === 0;
  if (
    array.elements[start]?.type === "ArrayExpression" &&
    (start === 0 || array.elements.length > 2)
  ) {
    yield* registrationFactories(array.elements[start], 0);
    start++;
  }
  let ids = [];
  for (const item of array.elements.slice(start)) {
    if (item?.type === "NumericLiteral" || item?.type === "StringLiteral") {
      ids.push(item.value);
    } else if (
      item?.type === "ArrowFunctionExpression" ||
      item?.type === "FunctionExpression"
    ) {
      yield { item, ids, nested };
      ids = [];
    } else {
      ids = [];
    }
  }
}

export async function buildInventory(
  root,
  { formatFactory = prettier.format } = {},
) {
  const manifest = JSON.parse(
    await fs.readFile(path.join(root, "evidence/web/manifest.json"), "utf8"),
  );
  const modules = new Map();
  const nestedFactories = [];
  const failures = [];
  const routes = [];
  const dependencies = [];
  const records = manifest.records.filter(
    (record) =>
      record.status === 200 && new URL(record.url).pathname.endsWith(".js"),
  );

  for (const record of records) {
    let source;
    try {
      const bytes = await fs.readFile(containedPath(root, record.path));
      if (Object.hasOwn(record, "bytes") &&
          (!Number.isSafeInteger(record.bytes) || record.bytes < 0 || bytes.length !== record.bytes)) {
        throw new Error("Captured source byte count mismatch");
      }
      if (createHash("sha256").update(bytes).digest("hex") !== record.sha256) {
        throw new Error("Captured source SHA-256 mismatch");
      }
      source = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(bytes);
    } catch (error) {
      throw new Error(
        `Unable to read inventory source ${record.path ?? "<invalid path>"}: ${errorSummary(error)}`,
        { cause: error },
      );
    }

    try {
      const ast = parse(source, {
        sourceType: "unambiguous",
        errorRecovery: false,
      });
      walk(ast, (node) => {
        if (
          node.type === "StringLiteral" &&
          /^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS) \/\S+$/.test(node.value)
        ) {
          routes.push({
            operation: node.value,
            source: record.path,
            start: node.start,
            end: node.end,
            authority: "static-literal",
            service: "unresolved",
            implemented: false,
            qualified: false,
          });
        }
        if (
          node.type !== "CallExpression" ||
          node.callee?.type !== "MemberExpression" ||
          node.callee.property?.name !== "push" ||
          node.arguments[0]?.type !== "ArrayExpression"
        ) {
          return;
        }
        if (
          !source
            .slice(node.callee.start, node.callee.end)
            .includes("TURBOPACK")
        ) {
          return;
        }
        for (const { item, ids, nested } of registrationFactories(
          node.arguments[0],
        )) {
          const raw = source.slice(item.start, item.end);
          const hash = createHash("sha256").update(raw).digest("hex");
          const origin = {
            source: record.path,
            url: record.url,
            start: item.start,
            end: item.end,
          };
          if (nested) {
            nestedFactories.push({ raw, hash, ids, origin });
            continue;
          }
          const existing = modules.get(hash) ?? {
            ids: [],
            sha256: hash,
            sourceCode: raw,
            origins: [],
          };
          existing.ids = [...new Set([...existing.ids, ...ids])];
          existing.origins.push(origin);
          modules.set(hash, existing);
        }
      });
    } catch (error) {
      failures.push({ source: record.path, error: errorSummary(error) });
    }

    for (const match of source.matchAll(/node_modules\/\.pnpm\/([^/"\s]+)/g)) {
      dependencies.push({
        specifier: match[1],
        source: record.path,
        offset: match.index,
      });
    }
  }

  if (failures.length > 0) {
    const details = failures
      .map((failure) => `${failure.source}: ${failure.error}`)
      .join("; ");
    throw new Error(
      `Inventory extraction failed for ${failures.length} source(s): ${details}`,
    );
  }

  // Keep the original flat inventory's IDs, paths and origins in place. New
  // nested origins extend it deterministically, even when their capture came first.
  for (const { raw, hash, ids, origin } of nestedFactories) {
    const existing = modules.get(hash) ?? {
      ids: [],
      sha256: hash,
      sourceCode: raw,
      origins: [],
    };
    existing.ids = [...new Set([...existing.ids, ...ids])];
    existing.origins.push(origin);
    modules.set(hash, existing);
  }

  const factoryFiles = new Map();
  for (const module of modules.values()) {
    const filename = factoryFilename(module);
    if (factoryFiles.has(filename)) {
      throw new Error(`Recovered factory output collision: ${filename}`);
    }
    module.path = `recovered/modules/${filename}`;
    let text;
    try {
      text = await formatFactory(`(${module.sourceCode});`, {
        parser: "babel",
      });
    } catch (error) {
      throw new Error(
        `Unable to format recovered factory ${module.sha256}: ${errorSummary(error)}`,
        { cause: error },
      );
    }
    factoryFiles.set(filename, factoryBanner + text);
    delete module.sourceCode;
  }

  const report = {
    authority:
      "Shipped public JavaScript; factory boundaries via AST. Original filenames and TS types unavailable.",
    rangeEncoding: "UTF-16 code-unit half-open offsets in UTF-8 decoded source",
    modules: [...modules.values()],
    failures: [],
  };
  const operations = {
    notice:
      "Static candidate operations; includes shared/excluded/admin code. Never probe privileged routes automatically.",
    operations: [
      ...new Map(routes.map((route) => [route.operation, route])).values(),
    ].sort((a, b) => a.operation.localeCompare(b.operation)),
    occurrences: routes,
  };
  const reportFiles = new Map([
    ["recovered/modules.json", JSON.stringify(report, null, 2) + "\n"],
    [
      "contracts/internal-operations.json",
      JSON.stringify(operations, null, 2) + "\n",
    ],
    [
      "evidence/web/dependency-paths.json",
      JSON.stringify(dependencies, null, 2) + "\n",
    ],
  ]);

  return {
    factoryFiles,
    reportFiles,
    report,
    summary: {
      modules: modules.size,
      parseFailures: 0,
      uniqueOperations: new Set(routes.map((route) => route.operation)).size,
    },
  };
}

async function exists(target) {
  try {
    await fs.lstat(target);
    return true;
  } catch (error) {
    if (error?.code === "ENOENT") return false;
    throw error;
  }
}

async function isGeneratorOwnedFactory(entry, absolute) {
  if (!entry.isFile() || !/-[0-9a-f]{12}\.js$/.test(entry.name)) {
    return false;
  }
  const expected = Buffer.from(factoryBanner);
  const actual = Buffer.alloc(expected.length);
  const handle = await fs.open(absolute, "r");
  try {
    const { bytesRead } = await handle.read(actual, 0, actual.length, 0);
    return bytesRead === expected.length && actual.equals(expected);
  } finally {
    await handle.close();
  }
}

async function stageInventory(root, inventory) {
  const transaction = await fs.mkdtemp(path.join(root, ".inventory-stage-"));
  const nextRoot = path.join(transaction, "next");
  const nextModules = path.join(nextRoot, "recovered/modules");
  try {
    await fs.mkdir(nextModules, { recursive: true });
    for (const [filename, contents] of inventory.factoryFiles) {
      await fs.writeFile(path.join(nextModules, filename), contents, {
        flag: "wx",
      });
    }

    const currentModules = path.join(root, "recovered/modules");
    let entries = [];
    try {
      entries = await fs.readdir(currentModules, { withFileTypes: true });
    } catch (error) {
      if (error?.code !== "ENOENT") throw error;
    }
    for (const entry of entries) {
      const source = path.join(currentModules, entry.name);
      if (await isGeneratorOwnedFactory(entry, source)) continue;
      const destination = path.join(nextModules, entry.name);
      if (await exists(destination)) {
        throw new Error(
          `Recovered factory output collides with an unrelated file: ${entry.name}`,
        );
      }
      await fs.cp(source, destination, {
        recursive: true,
        errorOnExist: true,
        force: false,
        preserveTimestamps: true,
        verbatimSymlinks: true,
      });
    }

    for (const [relative, contents] of inventory.reportFiles) {
      const destination = path.join(nextRoot, relative);
      await fs.mkdir(path.dirname(destination), { recursive: true });
      await fs.writeFile(destination, contents, { flag: "wx" });
    }
    return transaction;
  } catch (error) {
    await fs.rm(transaction, { recursive: true, force: true });
    throw error;
  }
}

async function publishStagedInventory(
  root,
  transaction,
  { beforePublish } = {},
) {
  const states = [];
  try {
    for (const [index, relative] of publicationTargets.entries()) {
      await beforePublish?.({ index, relative });
      const target = path.join(root, relative);
      const staged = path.join(transaction, "next", relative);
      const backup = path.join(transaction, "previous", relative);
      const state = {
        relative,
        target,
        backup,
        oldMoved: false,
        newPublished: false,
      };
      states.push(state);
      await fs.mkdir(path.dirname(target), { recursive: true });
      if (await exists(target)) {
        await fs.mkdir(path.dirname(backup), { recursive: true });
        await fs.rename(target, backup);
        state.oldMoved = true;
      }
      await fs.rename(staged, target);
      state.newPublished = true;
    }
  } catch (error) {
    const rollbackErrors = [];
    for (const state of states.reverse()) {
      try {
        if (state.newPublished && (await exists(state.target))) {
          const failed = path.join(transaction, "failed", state.relative);
          await fs.mkdir(path.dirname(failed), { recursive: true });
          await fs.rename(state.target, failed);
        }
        if (state.oldMoved) await fs.rename(state.backup, state.target);
      } catch (rollbackError) {
        rollbackErrors.push(
          `${state.relative}: ${errorSummary(rollbackError)}`,
        );
      }
    }
    const rollbackComplete = rollbackErrors.length === 0;
    const message = rollbackComplete
      ? "previous outputs restored"
      : `rollback incomplete (${rollbackErrors.join("; ")})`;
    const publicationError = new Error(
      `Inventory publication failed; ${message}: ${errorSummary(error)}`,
      { cause: error },
    );
    publicationError.rollbackComplete = rollbackComplete;
    throw publicationError;
  }
}

export async function generateInventory(
  root = defaultRoot,
  { formatFactory, beforePublish, log = console.log } = {},
) {
  const inventory = await buildInventory(root, { formatFactory });
  const transaction = await stageInventory(root, inventory);
  try {
    await publishStagedInventory(root, transaction, { beforePublish });
  } catch (error) {
    if (error.rollbackComplete) {
      await fs.rm(transaction, { recursive: true, force: true });
    }
    throw error;
  }
  await fs.rm(transaction, { recursive: true, force: true });
  log(JSON.stringify(inventory.summary));
  return inventory.report;
}

export const inventory = generateInventory;

if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const args = process.argv.slice(2);
  if (args.length !== 0 && (args.length !== 2 || args[0] !== "--root")) {
    throw new Error("Usage: node scripts/inventory.mjs [--root <workspace>]");
  }
  await generateInventory(
    args.length === 0 ? defaultRoot : path.resolve(args[1]),
  );
}
