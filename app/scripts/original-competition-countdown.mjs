import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "@babel/parser";
import prettier from "prettier";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  member,
  sha256,
} from "./original-contracts/source.mjs";
export const APP_ROOT = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
);
export const DIRECTORY = "reconstruction/competition-countdown";
export const COMPONENT =
  "packages/frontend/src/components/leaderboard/original-countdown.mjs";
const SHARED =
  "a7c04fdc74fb88a27d5cf24355396ee560d88ad4042abf3eb6a3c6874c5bacf2";
const PINS = {
  590407: ["3f494070c58a6d7f0f70279887ef648107935b765fe849de3e9ec100cec45dda"],
  706615: ["e606b2e7f5ab2bfd5da0abb70db2de0560f01d4d131d156719d8623614219e74"],
  139209: ["8d4ffb7afbfae1b99df53cf4d8421f1fb6f85c290468471f2e4f71f58358ed9b"],
};
const BASE_SHA =
  "a2e6021221e41abb6e603b04ddc4d8cb4211ac92262842013574f4857aeae262";
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(
    Object.entries(value)
      .filter(
        ([key]) =>
          ![
            "start",
            "end",
            "loc",
            "extra",
            "comments",
            "leadingComments",
            "trailingComments",
            "innerComments",
          ].includes(key),
      )
      .map(([key, item]) => [key, canonical(item)]),
  );
}
function exported(factory, id, name) {
  const result = [];
  for (const call of findNodes(
    factory.node,
    (node) =>
      node.type === "CallExpression" &&
      member(node.callee, factory.runtime, "s") &&
      (node.arguments[1]?.value === id ||
        (!node.arguments[1] && factory.ids.length === 1)),
  )) {
    const values = call.arguments[0].elements;
    for (let i = 0; i < values.length; i += 3)
      if (values[i].value === name) result.push(values[i + 2]);
  }
  return exactlyOne(result, `actual export ${id}.${name}`);
}
const declarations = (factory) =>
  factory.node.body.body
    .filter((node) => node.type === "VariableDeclaration")
    .flatMap((node) => node.declarations);
export async function buildCompetitionCountdown(appRoot = APP_ROOT) {
  assert.equal(
    sha256(
      await readFile(
        path.join(appRoot, "scripts/original-contracts/source.mjs"),
      ),
    ),
    SHARED,
  );
  const corpus = await openCorpus(appRoot),
    factories = new Map(),
    witnesses = [];
  for (const [id, hashes] of Object.entries(PINS)) {
    const rows = corpus.index.modules.filter((row) =>
      row.ids.includes(Number(id)),
    );
    assert.deepEqual(
      rows.map((row) => row.sha256).sort(),
      hashes,
      `unreviewed source ${id}`,
    );
    const row = exactlyOne(rows, `unique source ${id}`);
    factories.set(
      Number(id),
      await corpus.factory(Number(id), { source: row.origins[0].source }),
    );
  }
  const page = factories.get(590407),
    helpers = factories.get(706615),
    routes = factories.get(139209);
  const get = (factory, name) =>
    exactlyOne(
      declarations(factory).filter((node) => node.id.name === name),
      `actual declarator ${name}`,
    );
  const digits = get(page, "Y"),
    countdown = get(page, "ee"),
    now = exactlyOne(
      page.node.body.body.filter(
        (node) => node.type === "FunctionDeclaration" && node.id.name === "et",
      ),
      "actual Date.now initializer",
    );
  const date = get(helpers, "l"),
    target = exported(helpers, 706615, "H"),
    parts = exported(helpers, 706615, "v");
  for (const [factory, node, label] of [
    [page, digits, "complete digit-box component"],
    [page, countdown, "complete countdown DISPLAY component"],
    [page, now, "actual Date.now initializer"],
    [helpers, date, "actual nullable date parser"],
    [helpers, target, "complete phase/time target selector"],
    [helpers, parts, "complete clamped countdown projection"],
  ])
    witnesses.push(factory.witness(node, label));
  const hero = get(page, "eL");
  for (const [binding, property] of [
    ["$", "H"],
    ["a", "jsx"],
  ]) {
    const calls = findNodes(
      hero.init,
      (node) =>
        node.type === "CallExpression" &&
        member(
          node.callee.type === "SequenceExpression"
            ? node.callee.expressions.at(-1)
            : node.callee,
          binding,
          property,
        ) &&
        (property === "H" || node.arguments[0]?.name === "ee"),
    );
    assert.equal(calls.length, 1);
    witnesses.push(
      page.witness(
        calls[0],
        `actual hero uses ${binding}.${property} ${property === "H" ? "on competition DTO" : "with selected target"}`,
      ),
    );
  }
  const definition = get(routes, "b");
  for (const name of ["phase", "startsAt", "endsAt"]) {
    const property = exactlyOne(
      findNodes(
        definition.init,
        (node) => node.type === "ObjectProperty" && node.key?.name === name,
      ),
      `declared DTO ${name}`,
    );
    witnesses.push(
      routes.witness(
        property,
        `actual competition DTO ${name}; no inferred clock/phase conversion`,
      ),
    );
  }
  const text = await prettier.format(
    `"use client";\nexport {c as useMemoCache} from 'react/compiler-runtime';\n// Complete source-adapted React display, digit component and used selectors.\n// Capability bindings are local; captured runtime factories are never executed.\nexport function createCountdownModule({jsx,jsxs,useMemoCache,useState,useEffect,useTranslation,Date,setInterval,clearInterval}){const a={jsx,jsxs},s={c:useMemoCache},i={useState,useEffect},l={f:useTranslation};const {selectTarget,countdown}=(()=>{let ${helpers.text(date)};return {selectTarget:${helpers.text(target)},countdown:${helpers.text(parts)}};})();const $={v:countdown};${page.text(now)}let ${page.text(digits)},${page.text(countdown)};return {Countdown:ee,selectTarget,countdown};}`,
    { parser: "babel" },
  );
  const base = await readFile(
    path.join(appRoot, DIRECTORY, "reference/leaderboard-client.base.tsx"),
    "utf8",
  );
  assert.equal(sha256(base), BASE_SHA, "maintained base reference drift");
  const ast = parse(base, {
    sourceType: "module",
    plugins: ["typescript", "jsx"],
  });
  const before = exactlyOne(
    findNodes(
      ast,
      (node) =>
        node.type === "FunctionDeclaration" &&
        node.id?.name === "CompetitionCards",
    ),
    "base product cards",
  );
  assert.equal(
    findNodes(
      before,
      (node) =>
        node.type === "JSXIdentifier" && node.name === "CompetitionCountdown",
    ).length,
    0,
  );
  const selected = corpus.index.modules
    .filter((row) => row.ids.some((id) => Object.hasOwn(PINS, id)))
    .sort((a, b) => a.sha256.localeCompare(b.sha256));
  const nodes = [digits, countdown, now, date, target, parts];
  const contract = {
    schemaVersion: 1,
    source: {
      reviewBase: "d3ed4863f8a52bb8dabdeea338aa11367297377c",
      manifestSha256: corpus.anchors.manifestSha256,
      sharedSourceSha256: SHARED,
      selectedIndexEntries: selected,
      selectedCompleteEntriesSha256: sha256(JSON.stringify(selected)),
    },
    component: {
      path: COMPONENT,
      sha256: sha256(text),
      retainedAsts: nodes.map((node) => ({
        type: node.type,
        sha256: sha256(JSON.stringify(canonical(node))),
      })),
    },
    witnesses: witnesses.sort(
      (a, b) => a.source.localeCompare(b.source) || a.utf16[0] - b.utf16[0],
    ),
    maintainedBefore: {
      path: DIRECTORY + "/reference/leaderboard-client.base.tsx",
      sha256: BASE_SHA,
      gitCommit: "d3ed4863f8a52bb8dabdeea338aa11367297377c",
      originalPath:
        "app/packages/frontend/src/app/leaderboard/leaderboard-client.tsx",
      cardsUtf16: [before.start, before.end],
      cardsSha256: sha256(base.slice(before.start, before.end)),
      qualification:
        "Maintained local product baseline, not a screenshot/source identity claim about upstream.",
    },
    behavior: {
      target:
        "live uses endsAt; upcoming/registration use startsAt; other phases or nonfinite Date.parse return null. No phase inference from clock.",
      clock:
        "Date.now initializer;1000ms interval; clearInterval cleanup; expired remaining time clamps to zero without changing phase.",
      display:
        "Complete original four digit boxes, start/end label decisions, memo behavior and captured utility classes retained.",
      integration:
        "Current CompetitionSummary phase/startsAt/endsAt pass unchanged into original selector. Missing/loading DTO renders nothing. Local adapter supplies explicit English labels and React/browser capabilities.",
    },
    limits: [
      "Original bundle/factory/route schema never executed.",
      "Local English labels are explicit adapter values, not recovered translation-tenant identity.",
      "Product baseline screenshots are before/after maintained app, not authenticated upstream visual parity.",
      "No rank/price/scoring/auth/backend/state/phase mutation or financial operation.",
    ],
  };
  return { text, contract };
}
export async function verifyCompetitionCountdown(appRoot = APP_ROOT) {
  const { text, contract } = await buildCompetitionCountdown(appRoot);
  const actual = await readFile(path.join(appRoot, COMPONENT), "utf8");
  assert.deepEqual(
    canonical(parse(actual, { sourceType: "module" })),
    canonical(parse(text, { sourceType: "module" })),
    "maintained component AST differs",
  );
  assert.equal(actual, text, "maintained component bytes differ");
  assert.equal(
    await readFile(path.join(appRoot, DIRECTORY, "contract.json"), "utf8"),
    JSON.stringify(contract, null, 2) + "\n",
    "source contract differs",
  );
  return contract;
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  try {
    const [mode, ...rest] = process.argv.slice(2);
    assert.ok(
      !rest.length && ["--write", "--check"].includes(mode),
      "usage: --write | --check",
    );
    if (mode === "--write") {
      const { text, contract } = await buildCompetitionCountdown();
      await mkdir(path.dirname(path.join(APP_ROOT, COMPONENT)), {
        recursive: true,
      });
      await writeFile(path.join(APP_ROOT, COMPONENT), text);
      await writeFile(
        path.join(APP_ROOT, DIRECTORY, "contract.json"),
        JSON.stringify(contract, null, 2) + "\n",
      );
    } else await verifyCompetitionCountdown();
    console.log(
      "Complete original competition countdown display verified without captured runtime execution.",
    );
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
