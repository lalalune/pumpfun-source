import assert from "node:assert/strict";
import { test } from "node:test";
import {
  readFile,
  writeFile,
  mkdir,
  mkdtemp,
  rm,
  link,
} from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import { parse } from "@babel/parser";
import React from "../packages/frontend/node_modules/react/index.js";
import { renderToStaticMarkup } from "../packages/frontend/node_modules/react-dom/server.node.js";
import {
  findNodes,
  exactlyOne,
} from "../scripts/original-contracts/source.mjs";
import {
  verifyCompetitionEntryPresentation,
  nativeRow,
} from "../scripts/verify-competition-entry-presentation.mjs";
import { parseLeaderboardResponse } from "../packages/frontend/src/app/leaderboard/types.ts";
const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), ".."),
  PAGE = "packages/frontend/src/app/leaderboard/leaderboard-client.tsx",
  DIR = "reconstruction/competition-entry-presentation";
const sdk = createRequire(path.join(APP, "packages/sdk/package.json")),
  { transform, build } = createRequire(sdk.resolve("tsup"))("esbuild");
const base = {
  entryId: "synthetic-zero",
  participantId: "synthetic-account",
  kind: "person",
  rank: 0,
  pnlUsd: 0,
  realizedPnlUsd: 0,
  unrealizedPnlUsd: 0,
  memberCount: 1,
  membersFresh: 1,
  struck: false,
  lastRefreshedAtMs: 0,
  walletAddress: null,
  username: "SyntheticUnranked",
  isVerified: false,
  verifiedBadgeVisible: false,
};
const entries = [
  base,
  { ...base, entryId: "ranked-zero", rank: 1, username: "SyntheticRankedZero" },
  {
    ...base,
    entryId: "positive",
    rank: 2,
    pnlUsd: 12.34,
    username: "SyntheticGain",
  },
  {
    ...base,
    entryId: "negative",
    rank: 3,
    pnlUsd: -12.34,
    username: "SyntheticLoss",
  },
  {
    ...base,
    entryId: "negative-zero",
    rank: 4,
    pnlUsd: -0,
    username: "SyntheticNegativeZero",
  },
  {
    ...base,
    entryId: "rounding",
    rank: 5,
    pnlUsd: Number.MIN_VALUE,
    username: "SyntheticSmallPositive",
  },
];
async function baselineRowComponent(t) {
  const text = await readFile(path.join(APP, PAGE), "utf8"),
    tree = parse(text, {
      sourceType: "module",
      plugins: ["jsx", "typescript"],
    }),
    parts = [];
  const usd = exactlyOne(
    findNodes(
      tree,
      (n) => n.type === "VariableDeclarator" && n.id?.name === "usd",
    ),
    "actual existing native formatter",
  );
  parts.push("const " + text.slice(usd.start, usd.end) + ";");
  for (const name of ["shortIdentity", "identityLabel", "VerifiedMark"]) {
    const n = exactlyOne(
      findNodes(
        tree,
        (n) => n.type === "FunctionDeclaration" && n.id?.name === name,
      ),
      "actual used " + name,
    );
    parts.push(text.slice(n.start, n.end));
  }
  const row = nativeRow(text);
  parts.push(
    await readFile(path.join(APP, DIR, "reference/native-row.tsx"), "utf8"),
  );
  const dir = await mkdtemp(
    path.join(APP, "packages/frontend/.entry-presentation-"),
  );
  t.after(() => rm(dir, { recursive: true, force: true }));
  const result = await transform(
      parts.join("\n") + "\nexport{CompetitionEntryRows};",
      { loader: "tsx", jsx: "automatic", format: "cjs", target: "node22" },
    ),
    out = path.join(dir, "actual-row.cjs");
  await writeFile(out, result.code);
  return createRequire(import.meta.url)(out).CompetitionEntryRows;
}
async function rowComponent(t, baseline = false) {
  if (baseline) return baselineRowComponent(t);
  const dir = await mkdtemp(
    path.join(APP, "packages/frontend/.entry-presentation-"),
  );
  t.after(() => rm(dir, { recursive: true, force: true }));
  const out = path.join(dir, "actual-native-module.cjs");
  await build({
    entryPoints: [path.join(APP, PAGE)],
    bundle: true,
    write: true,
    outfile: out,
    platform: "node",
    format: "cjs",
    jsx: "automatic",
    external: ["react", "react/*", "next/*"],
    plugins: [
      {
        name: "expose-existing-private-row-for-test",
        setup(builder) {
          builder.onLoad(
            { filter: /leaderboard-client\.tsx$/ },
            async (args) => {
              const text = await readFile(args.path, "utf8");
              assert.equal(
                text.split("export default function LeaderboardClient()")
                  .length,
                2,
              );
              return {
                contents:
                  text.replace(
                    "export default function LeaderboardClient()",
                    "function LeaderboardClient()",
                  ) + "\nexport{CompetitionEntryRows};",
                loader: "tsx",
              };
            },
          );
        },
      },
    ],
  });
  return createRequire(import.meta.url)(out).CompetitionEntryRows;
}

function htmlRows(component) {
  return renderToStaticMarkup(
    React.createElement(component, { entries, prizes: [] }),
  ).replaceAll("<!-- -->", "");
}
function finalDecisions(html) {
  assert.ok(html.includes('aria-label="Not ranked">–</span>'));
  const metrics = [
    ...html.matchAll(
      /class="ranking-metric"><strong(?: class="([^"]+)")?>(.*?)<\/strong>/g,
    ),
  ].map((m) => ({ tone: m[1], text: m[2] }));
  assert.deepEqual(metrics, [
    { tone: undefined, text: "$0.00" },
    { tone: undefined, text: "$0.00" },
    { tone: "positive", text: "+$12.34" },
    { tone: "negative", text: "-$12.34" },
    { tone: undefined, text: "-$0.00" },
    { tone: "positive", text: "+$0.00" },
  ]);
}
test("actual native three display decisions bind complete original X and original DTO without port-stack dependency", async () => {
  const c = await verifyCompetitionEntryPresentation();
  assert.equal(c.source.length, 6);
  assert.ok(c.origins.length > 0);
  assert.ok(c.source.every((w) => w.sha256 && w.utf8 && w.utf16));
  assert.equal(
    c.local.amount,
    "Existing usd.format(entry.pnlUsd), unchanged Intl/ranking/API behavior",
  );
});
test("source gate rejects rank-zero regression, zero-gain coloring and positive-prefix boundary change", async (t) => {
  const c = await verifyCompetitionEntryPresentation(),
    dir = await mkdtemp(path.join(APP, ".entry-presentation-source-"));
  t.after(() => rm(dir, { recursive: true, force: true }));
  for (const name of new Set([
    "evidence/web/manifest.json",
    "recovered/modules.json",
    DIR + "/reference/native-row.tsx",
    ...c.origins.map((o) => o.source),
  ])) {
    const dest = path.join(dir, name);
    await mkdir(path.dirname(dest), { recursive: true });
    await link(path.join(APP, name), dest);
  }
  const dest = path.join(dir, PAGE);
  await mkdir(path.dirname(dest), { recursive: true });
  const text = await readFile(path.join(APP, PAGE), "utf8");
  for (const [from, to, message] of [
    [
      'entry.rank > 0 ? entry.rank : "–"',
      "entry.rank",
      "rank decision changed",
    ],
    ["0 === entry.pnlUsd", "0 > entry.pnlUsd", "tone decision changed"],
    [
      'entry.pnlUsd > 0 ? "+" : ""',
      'entry.pnlUsd >= 0 ? "+" : ""',
      "positive prefix changed",
    ],
  ]) {
    assert.ok(text.includes(from));
    await writeFile(dest, text.replace(from, to));
    await assert.rejects(
      verifyCompetitionEntryPresentation(dir),
      new RegExp(message),
    );
  }
});
test("same real React row assertion fails on exact base excerpt then passes candidate, retaining amount/identity/facts/order", async (t) => {
  const before = htmlRows(await rowComponent(t, true));
  assert.ok(before.includes('aria-label="Rank 0">0</span>'));
  assert.ok(before.includes('class="positive">$0.00'));
  assert.throws(() => finalDecisions(before));
  const after = htmlRows(await rowComponent(t));
  finalDecisions(after);
  for (const text of [
    "SyntheticUnranked",
    "SyntheticGain",
    "SyntheticLoss",
    "Realized $0.00",
    "Unrealized $0.00",
  ])
    assert.ok(after.includes(text), text);
  assert.ok(after.indexOf("SyntheticGain") < after.indexOf("SyntheticLoss"));
});
test("current local response admission retains supplied rank-zero/finite PnL; nonfinite values still reject", () => {
  const competition = {
    id: "fixture",
    slug: "fixture",
    kind: "person",
    title: "Synthetic admitted fixture",
    description: "",
    prizeCopy: "",
    prizes: [],
    minMembers: 0,
    maxMembers: 0,
    registrationOpensAt: null,
    registrationClosesAt: null,
    startsAt: null,
    endsAt: null,
    maxEntries: 10,
    entriesCount: entries.length,
    participants: entries.length,
    joinable: false,
    phase: "upcoming",
    isFinal: false,
  };
  const response = {
    ok: true,
    source: {
      mode: "developer-api",
      label: "Pump developer API",
      fetchedAt: "2026-10-29T00:00:00Z",
    },
    data: {
      kind: "competition-detail",
      competition,
      entries,
      totalRanked: entries.length,
      builtAtMs: 0,
      isFinal: false,
    },
  };
  const admitted = parseLeaderboardResponse(response);
  assert.equal(admitted.data.entries[0].rank, 0);
  assert.ok(Object.is(admitted.data.entries[4].pnlUsd, -0));
  for (const number of [NaN, Infinity, -Infinity])
    assert.throws(() =>
      parseLeaderboardResponse({
        ...response,
        data: { ...response.data, entries: [{ ...base, pnlUsd: number }] },
      }),
    );
});
