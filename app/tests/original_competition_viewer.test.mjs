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
import React from "../packages/frontend/node_modules/react/index.js";
import {
  jsx,
  jsxs,
} from "../packages/frontend/node_modules/react/jsx-runtime.js";
import { renderToStaticMarkup } from "../packages/frontend/node_modules/react-dom/server.node.js";
import { useMemoCache } from "../packages/frontend/src/components/leaderboard/original-prize-formats.mjs";
import {
  createEntryHelpers,
  squadVariants,
  imageVariants,
} from "../packages/frontend/src/components/leaderboard/entry/entry-helpers.mjs";
import { createVolumeFormatter } from "../packages/frontend/src/components/leaderboard/viewer/original-volume.mjs";
import { verifyCompetitionViewer } from "../scripts/original-competition-viewer.mjs";
import { validateAgainstSchema } from "../packages/backend/src/schema-validator.ts";
import {
  viewerEntry,
  translateViewer,
  wallet,
} from "./fixtures/competition-viewer-data.mjs";
const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), ".."),
  sdk = createRequire(path.join(APP, "packages/sdk/package.json")),
  { transform } = createRequire(sdk.resolve("tsup"))("esbuild");
const contexts = squadVariants.flatMap((s) =>
  imageVariants.map((i) => ({
    squadVariant: s.sha256,
    imageVariant: i.sha256,
    Intl,
  })),
);
async function compiled(t) {
  const dir = await mkdtemp(path.join(APP, "packages/frontend/.viewer-ssr-"));
  t.after(() => rm(dir, { recursive: true, force: true }));
  const input = await readFile(
    path.join(
      APP,
      "packages/frontend/src/components/leaderboard/viewer/original-viewer-card.tsx",
    ),
    "utf8",
  );
  const result = await transform(input, {
    loader: "tsx",
    format: "cjs",
    jsx: "automatic",
  });
  const f = path.join(dir, "viewer.cjs");
  await writeFile(f, result.code);
  return createRequire(import.meta.url)(f).createViewerCard;
}
const base = {
  jsx,
  jsxs,
  React,
  useMemoCache,
  useTranslation: () => ({ t: translateViewer }),
  classNames: (...p) => p.filter(Boolean).join(" "),
  formatVolume: createVolumeFormatter(Intl),
};
test("complete viewer/card stats, actual consumer/planner/DTO, formatter aliases and price boundary are source authenticated", async () => {
  const c = await verifyCompetitionViewer();
  assert.equal(c.source.selectedIndexEntries.length, 6);
  for (const label of [
    "COMPLETE original e9 viewer card",
    "COMPLETE original e7 expanded stats with conditional price hook",
    "actual competition-board viewer-card invocation",
    "actual documented viewer entry and eligibility DTO",
    "COMPLETE actually used compact-currency formatter",
  ])
    assert.ok(
      c.witnesses.some((w) => w.label === label),
      label,
    );
  assert.equal(c.prerequisite.pr, 1296);
  assert.ok(c.witnesses.every((w) => w.sha256 && w.utf16 && w.utf8));
});
test("source verification rejects card-state drift and independent receipt changes", async (t) => {
  const temp = await mkdtemp(path.join(APP, ".viewer-source-"));
  t.after(() => rm(temp, { recursive: true, force: true }));
  const contract = JSON.parse(
    await readFile(
      path.join(APP, "reconstruction/competition-viewer/contract.json"),
    ),
  );
  const names = new Set([
    "scripts/original-contracts/source.mjs",
    "evidence/web/manifest.json",
    "recovered/modules.json",
    ...contract.source.selectedIndexEntries.flatMap((r) =>
      r.origins.map((o) => o.source),
    ),
    ...Object.keys(contract.outputs),
    ...Object.keys(contract.prerequisite.files),
    "reconstruction/competition-viewer/contract.json",
  ]);
  for (const name of names) {
    const out = path.join(temp, name);
    await mkdir(path.dirname(out), { recursive: true });
    if (
      name ===
        "packages/frontend/src/components/leaderboard/viewer/original-viewer-card.tsx" ||
      name === "reconstruction/competition-viewer/contract.json"
    )
      await writeFile(out, await readFile(path.join(APP, name)));
    else await link(path.join(APP, name), out);
  }
  const f = path.join(
      temp,
      "packages/frontend/src/components/leaderboard/viewer/original-viewer-card.tsx",
    ),
    text = await readFile(f, "utf8");
  assert.ok(text.includes("Math.abs(t)"));
  await writeFile(f, text.replace("Math.abs(t)", "Math.abs(t + 1)"));
  await assert.rejects(verifyCompetitionViewer(temp), /maintained AST differs/);
  await writeFile(f, text);
  const doc = path.join(
    temp,
    "reconstruction/competition-viewer/contract.json",
  );
  await writeFile(
    doc,
    JSON.stringify({ ...contract, limits: [] }, null, 2) + "\n",
  );
  await assert.rejects(
    verifyCompetitionViewer(temp),
    /source contract differs/,
  );
});
test("used compact volume closure preserves missing/nonfinite, signed, precision and compact thresholds", () => {
  const f = createVolumeFormatter(Intl);
  assert.equal(f(NaN), "—");
  assert.equal(f(Infinity), "—");
  assert.equal(f("12"), "—");
  assert.equal(f(-0), "$0.00");
  assert.equal(f(0.1), "$0.10");
  assert.equal(f(1.5), "$2");
  assert.equal(f(999.4), "$999");
  assert.equal(f(999.5), "$1K");
  assert.equal(f(12000), "$12K");
  assert.equal(f(-12000), "−$12K");
});
test("synthetic viewer entry is admitted by retained public entry schema; wrong numeric type rejected", async () => {
  const spec = JSON.parse(
      await readFile(path.join(APP, "contracts/developer.openapi.json")),
    ),
    schema =
      spec.paths["/competitions/{idOrSlug}"].get.responses["200"].content[
        "application/json"
      ].schema.properties.leaderboard.properties.entries.items;
  assert.deepEqual(validateAgainstSchema(viewerEntry, schema, "$", spec), []);
  assert.ok(
    validateAgainstSchema(
      { ...viewerEntry, buySpendSol: "2" },
      schema,
      "$",
      spec,
    ).length,
  );
});
test("actual React SSR uses captured consumer, exact identity and initial collapsed state without calling price hook; all six inherited contexts", async (t) => {
  const make = await compiled(t);
  for (const context of contexts) {
    const avatars = [],
      links = [];
    let calls = 0;
    const { ViewerConsumer } = make({
      ...base,
      ...createEntryHelpers(context),
      Avatar: (p) => {
        avatars.push(p);
        return jsx("span", { "data-avatar": p.address });
      },
      Link: ({ children, prefetch, ...p }) => {
        links.push(p);
        return jsx("a", { ...p, children });
      },
      useSolPrice: () => {
        calls++;
        return { data: 100 };
      },
    });
    const before = JSON.stringify(viewerEntry),
      html = renderToStaticMarkup(
        jsx(ViewerConsumer, { row: { entry: viewerEntry } }),
      );
    assert.equal(calls, 0);
    assert.ok(html.includes('aria-expanded="false"'));
    assert.ok(html.includes("fixture-show-stats"));
    assert.ok(html.includes("$1,000.00"));
    assert.ok(html.includes("fixture-YOU"));
    assert.ok(!html.includes("Realized"));
    assert.equal(links[0].href, "/profile/" + wallet);
    assert.equal(avatars[0].src, "https://fixture.invalid/avatar.png");
    assert.equal(JSON.stringify(viewerEntry), before);
    const group = renderToStaticMarkup(
      jsx(ViewerConsumer, {
        row: {
          entry: {
            ...viewerEntry,
            kind: "group",
            rank: 0,
            walletAddress: null,
            username: null,
            participantId: "a/b",
          },
        },
      }),
    );
    assert.ok(group.includes("fixture-unnamed-squad"));
    assert.ok(group.includes("fixture-your-squad"));
    assert.ok(group.includes("#—"));
    assert.ok(!group.includes("fixture-YOU"));
    assert.equal(links.at(-1).href, "/squads/a%2Fb");
    const unsafe = renderToStaticMarkup(
      jsx(ViewerConsumer, {
        row: { entry: { ...viewerEntry, username: "<script>bad</script>" } },
      }),
    );
    assert.ok(unsafe.includes("&lt;script&gt;"));
    assert.ok(!unsafe.includes("<script>"));
  }
});
test("actual expanded-stats SSR preserves missing entry/price, zero-price truthiness, near-zero rounding and independent stat tone", async (t) => {
  const make = await compiled(t),
    h = createEntryHelpers(contexts[0]);
  for (const { entry, price, expect } of [
    { entry: null, price: 100, expect: ["—", "—", "—"] },
    { entry: viewerEntry, price: undefined, expect: ["$0.00", "-$25.50", "—"] },
    { entry: viewerEntry, price: 0, expect: ["$0.00", "-$25.50", "—"] },
    {
      entry: {
        ...viewerEntry,
        realizedPnlUsd: -0.004,
        unrealizedPnlUsd: 0.005,
      },
      price: 6000,
      expect: ["$0.00", "$0.01", "$12K"],
    },
  ]) {
    let calls = 0;
    const { Stats } = make({
      ...base,
      ...h,
      Avatar: () => null,
      Link: () => null,
      useSolPrice: (o) => {
        assert.deepEqual(o, {});
        calls++;
        return { data: price };
      },
    });
    const html = renderToStaticMarkup(jsx(Stats, { entry }));
    for (const value of expect)
      assert.ok(html.includes(value), value + " in " + html);
    assert.equal(calls, 1);
    assert.ok(html.includes("Volume"));
    if (entry === viewerEntry) assert.ok(html.includes("text-loss"));
  }
});
