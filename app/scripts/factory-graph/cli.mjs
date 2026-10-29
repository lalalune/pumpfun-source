#!/usr/bin/env node
import { resolve } from "node:path";
import { buildGraph, publishGraph, readReport, verifyGraph } from "./core.mjs";

const root = resolve(import.meta.dirname, "../..");
const output = "research/turbopack-route-graph-20261028";
const [command = "summary", ...rawArgs] = process.argv.slice(2);
const args = rawArgs[0] === "--" ? rawArgs.slice(1) : rawArgs;
const print = (value) =>
  process.stdout.write(`${JSON.stringify(value, null, 2)}\n`);

if (command === "build") {
  const result = await publishGraph(root, output);
  print(result.summary);
} else if (command === "verify") {
  print(await verifyGraph(root, output));
} else if (command === "summary") {
  try {
    print(await readReport(root, output, "GRAPH-SUMMARY.json"));
  } catch {
    print((await buildGraph(root))["GRAPH-SUMMARY.json"]);
  }
} else if (command === "route") {
  const route = args[0];
  const report = await readReport(root, output, "ROUTE-ATTRIBUTION.json");
  if (!route || !Object.hasOwn(report, route))
    throw new Error(
      `unknown route; choose one of: ${Object.keys(report).join(", ")}`,
    );
  print(report[route]);
} else if (command === "module") {
  const [id, hash] = args;
  if (!id)
    throw new Error("usage: graph:module -- <module-id> [sha256-prefix]");
  const nodes = await readReport(root, output, "MODULE-IDENTITIES.json.gz");
  const matches = nodes.filter(
    (node) => String(node.id) === id && (!hash || node.sha256.startsWith(hash)),
  );
  if (!matches.length) throw new Error(`no selected identity for module ${id}`);
  print({ ambiguous: matches.length > 1, matches });
} else if (command === "operations") {
  const query = args.join(" ").toLowerCase();
  const report = await readReport(root, output, "API-ATTRIBUTION.json");
  const matches = [...report.internal, ...report.developer].filter(
    (entry) => !query || JSON.stringify(entry).toLowerCase().includes(query),
  );
  print({ matches });
} else throw new Error(`unknown graph command: ${command}`);
